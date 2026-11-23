import pandas as pd, numpy as np
src = open("simmonth.py").read().split("res={}")[0]
exec(src)

def sim2(T, maxmin, maxdog, Q, c1, c2, N=50, flip_min=0, flip_maxdog=None, flip_wait=0, flip_maxmin=None, hedge=False):
    S = T[(T["min"] <= maxmin) & (T.tpx < maxdog)].copy()
    key = S.t + "|" + S.taker + "|" + S.tpx.round(4).astype(str); S["run"] = (key != key.shift()).cumsum()
    S["cum"] = S.groupby("run").n.cumsum(); S["cum0"] = S.cum - S.n
    S["fill"] = np.clip(S.cum - Q, 0, None) - np.clip(S.cum0 - Q, 0, None); S["fb"] = S.groupby("run").fill.cumsum() - S.fill
    S["fill"] = np.clip(np.minimum(S.fill, N - S.fb), 0, None); S = S[S.fill > 0].copy()
    first = S.groupby("t").side.transform("first"); flip = S.side != first
    # --- flip safeties (only affect buys on the flip side) ---
    keep = ~flip
    ok = flip.copy()
    if flip_min: ok &= S["min"] >= flip_min
    if flip_maxmin: ok &= S["min"] <= flip_maxmin
    if flip_maxdog is not None: ok &= S.tpx < flip_maxdog          # flip side must be a stronger favourite
    if flip_wait:                                                    # flip must have lasted this many seconds
        fs = S[flip].groupby("t").sec.transform("min")
        S.loc[flip, "fstart"] = fs
        ok &= (S.sec - S.fstart.fillna(0)) >= flip_wait
    S = S[keep | ok].copy()
    first = S.groupby("t").side.transform("first"); cap = np.where(S.side == first, c1, c2)
    S["cost0"] = S.fill * S.px; S["cc"] = S.groupby(["t", "side"]).cost0.cumsum(); S["prev"] = S.cc - S.cost0
    S["fill"] = S.fill * np.clip((cap - S.prev) / S.cost0, 0, 1)
    if hedge:
        # flip side only buys enough that the round can't lose more than it would have without the flip:
        # cap flip spend at the first-side contracts' payout cushion -> spend <= first-side cost
        fc = S[S.side == first].groupby("t").apply(lambda g: (g.fill * g.px).sum())
        S["fcost"] = S.t.map(fc).fillna(0)
        isf = S.side != first
        S["cc2"] = (S.fill * S.px).where(isf, 0).groupby(S.t).cumsum(); S["prev2"] = S.cc2 - (S.fill * S.px).where(isf, 0)
        lim = np.clip((S.fcost - S.prev2) / (S.fill * S.px).replace(0, np.nan), 0, 1).fillna(1)
        S["fill"] = np.where(isf, S.fill * lim, S.fill)
    S["cost"] = S.fill * S.px; S["pnl"] = S.fill * (S.win - S.px)
    w = S.groupby("t").agg(put=("cost", "sum"), pnl=("pnl", "sum"), open=("open", "first"),
                           sides=("side", "nunique")); return w[w.put > 0.5]

def line(lab, w):
    d = w.groupby(w.open.dt.tz_convert("America/New_York").dt.date).pnl.sum(); eq = d.cumsum()
    flips = w[w.sides > 1]
    print(f"{lab:46s} ${w.pnl.sum():+6,.0f} | up days {(d>0).sum():2d}/{len(d)} | worst day ${d.min():+5,.0f} | max drop ${(eq-eq.cummax()).min():+5,.0f} "
          f"| worst round ${w.pnl.min():+4,.0f} | flip rounds {len(flips):3d}, their total ${flips.pnl.sum():+5,.0f}")

T = load("KXWTI15M")
print("WTI, last month, $15 first side / $35 flip (except where noted)\n")
line("A. Flip as now", sim2(T, 9, 0.40, 300, 15, 35))
line("B. No flip", sim2(T, 9, 0.40, 300, 15, 0))
line("C. Flip cap only $15 (same as first)", sim2(T, 9, 0.40, 300, 15, 15))
line("D. Flip cap $25", sim2(T, 9, 0.40, 300, 15, 25))
for m in (3, 4, 5, 6):
    line(f"E. Flip only from minute {m} on", sim2(T, 9, 0.40, 300, 15, 35, flip_min=m))
for m in (4, 5, 6):
    line(f"F. Flip only up to minute {m}", sim2(T, 9, 0.40, 300, 15, 35, flip_maxmin=m))
for dg in (0.35, 0.30, 0.25):
    line(f"G. Flip only if new underdog < {int(dg*100)}c", sim2(T, 9, 0.40, 300, 15, 35, flip_maxdog=dg))
for s in (30, 60, 120):
    line(f"H. Flip only after it holds {s}s", sim2(T, 9, 0.40, 300, 15, 35, flip_wait=s))
line("I. Hedge: flip spend <= first-side spend", sim2(T, 9, 0.40, 300, 15, 35, hedge=True))
