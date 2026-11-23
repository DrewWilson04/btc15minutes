exec(open("flipguard.py").read().split('T = load("KXWTI15M")')[0])
T = load("KXWTI15M")
mid = T.open.min() + (T.open.max() - T.open.min()) / 2
H = [T[T.open < mid], T[T.open >= mid]]
print("WTI last month, $20 first / $35 flip, 30s flip hold\n")
for mm in (5, 6, 7, 8, 9, 10, 11, 12, 13):
    w = sim2(T, mm, 0.40, 300, 20, 35, flip_wait=30)
    d = w.groupby(w.open.dt.tz_convert("America/New_York").dt.date).pnl.sum(); eq = d.cumsum()
    hs = [sim2(h, mm, 0.40, 300, 20, 35, flip_wait=30).pnl.sum() for h in H]
    tag = "  <- now" if mm == 9 else ""
    print(f"stop buying after minute {mm:2d}{tag:8s} ${w.pnl.sum():+6,.0f}  W/L {(w.pnl>0).sum()}/{(w.pnl<0).sum()}  up days {(d>0).sum()}/{len(d)}  worst day ${d.min():+5,.0f}  max drop ${(eq-eq.cummax()).min():+5,.0f}  halves ${hs[0]:+5,.0f} / ${hs[1]:+5,.0f}")
