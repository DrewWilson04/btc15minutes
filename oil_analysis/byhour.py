exec(open("flipguard.py").read().split('T = load("KXWTI15M")')[0])
import pandas as pd
T = load("KXWTI15M")
w = sim2(T, 6, 0.40, 300, 20, 35, flip_wait=30)
et = w.open.dt.tz_convert("America/New_York")
w["hour"] = et.dt.hour; w["dow"] = et.dt.day_name().str[:3]; w["date"] = et.dt.date
mid = w.open.min() + (w.open.max() - w.open.min()) / 2
w["half"] = (w.open >= mid).map({False: "h1", True: "h2"})
print(f"WTI last month, min 1-6, $20/$35, 30s hold: total ${w.pnl.sum():+,.0f} over {len(w)} rounds\n")
g = w.groupby("hour").agg(n=("pnl", "size"), pnl=("pnl", "sum"), won=("pnl", lambda s: (s > 0).mean()))
h = w.pivot_table(index="hour", columns="half", values="pnl", aggfunc="sum").fillna(0)
d = w.groupby(["hour", "date"]).pnl.sum().reset_index()
upd = d.groupby("hour").pnl.apply(lambda s: f"{(s>0).sum()}/{len(s)}")
print("Hour (ET)  rounds   profit   won%   1st half / 2nd half   days up")
for hr, r in g.iterrows():
    flag = "  <-- lost in BOTH halves" if h.loc[hr, "h1"] < 0 and h.loc[hr, "h2"] < 0 else ""
    print(f"  {hr:02d}:00   {int(r.n):5d}  ${r.pnl:+7.0f}   {r.won*100:3.0f}%   ${h.loc[hr,'h1']:+6.0f} / ${h.loc[hr,'h2']:+6.0f}      {upd[hr]:>6s}{flag}")
print()
g2 = w.groupby("dow").agg(n=("pnl", "size"), pnl=("pnl", "sum"))
h2 = w.pivot_table(index="dow", columns="half", values="pnl", aggfunc="sum").fillna(0)
for dw in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]:
    if dw in g2.index:
        r = g2.loc[dw]; print(f"  {dw}  {int(r.n):5d} rounds  ${r.pnl:+7.0f}   halves ${h2.loc[dw].get('h1',0):+6.0f} / ${h2.loc[dw].get('h2',0):+6.0f}")
# what if we skipped hours that lost in both halves?
bad = [hr for hr in h.index if h.loc[hr, "h1"] < 0 and h.loc[hr, "h2"] < 0]
print(f"\nhours that lost in both halves: {bad}")
print(f"skipping them: ${w[~w.hour.isin(bad)].pnl.sum():+,.0f}  (vs ${w.pnl.sum():+,.0f})")
print()
def stats(lab, x):
    d = x.groupby("date").pnl.sum(); eq = d.cumsum()
    print(f"{lab:34s} ${x.pnl.sum():+6,.0f}  rounds {len(x):5d}  up days {(d>0).sum()}/{len(d)}  worst day ${d.min():+5,.0f}  max drop ${(eq-eq.cummax()).min():+5,.0f}  halves ${x[x.half=='h1'].pnl.sum():+5,.0f} / ${x[x.half=='h2'].pnl.sum():+5,.0f}")
stats("All hours (now)", w)
stats("Only 11am-6pm ET", w[w.hour.between(11, 17)])
stats("Only 11am-midnight ET", w[w.hour >= 11])
stats("Skip midnight-11am ET (same)", w[w.hour >= 11])
stats("Only midnight-11am ET", w[w.hour < 11])
stats("Only 6pm-midnight ET", w[w.hour >= 18])
