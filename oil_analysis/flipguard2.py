exec(open("flipguard.py").read().split('T = load("KXWTI15M")')[0])
import pandas as pd
T = load("KXWTI15M")
mid = T.open.min() + (T.open.max() - T.open.min()) / 2
halves = {"1st half": T[T.open < mid], "2nd half": T[T.open >= mid]}
V = [("A. Flip as now", dict(c2=35)), ("B. No flip", dict(c2=0)),
     ("G. new underdog < 30c", dict(c2=35, flip_maxdog=0.30)), ("G2. new underdog < 32c", dict(c2=35, flip_maxdog=0.32)),
     ("G3. new underdog < 28c", dict(c2=35, flip_maxdog=0.28)),
     ("H. holds 30s", dict(c2=35, flip_wait=30)), ("H2. holds 45s", dict(c2=35, flip_wait=45)), ("H3. holds 20s", dict(c2=35, flip_wait=20)),
     ("G+H. <30c AND holds 30s", dict(c2=35, flip_maxdog=0.30, flip_wait=30)),
     ("G+H, flip cap $25", dict(c2=25, flip_maxdog=0.30, flip_wait=30)),
     ("H + flip cap $15", dict(c2=15, flip_wait=30))]
print(f"{'WTI, $15 first side':30s} {'WHOLE MONTH':>40s}   {'1st half':>9s} {'2nd half':>9s}")
for lab, kw in V:
    c2 = kw.pop("c2")
    w = sim2(T, 9, 0.40, 300, 15, c2, **kw)
    d = w.groupby(w.open.dt.tz_convert("America/New_York").dt.date).pnl.sum(); eq = d.cumsum()
    hs = [sim2(h, 9, 0.40, 300, 15, c2, **kw).pnl.sum() for h in halves.values()]
    print(f"{lab:30s} ${w.pnl.sum():+5,.0f}  worst day ${d.min():+5,.0f}  max drop ${(eq-eq.cummax()).min():+5,.0f}   ${hs[0]:+7,.0f}  ${hs[1]:+7,.0f}")
