import pandas as pd, numpy as np, sys
ser=sys.argv[1]; N=float(sys.argv[2]); Q=float(sys.argv[3]); M1=int(sys.argv[4]); PMAX=float(sys.argv[5]); SKIP=sys.argv[6]=="skip"
T=pd.read_pickle(f"data/{ser}_T.pkl").sort_values(["t","ts"]).reset_index(drop=True)
T["min"]=(T.sec//60).astype(int)+1
T=T[(T["min"]<=M1)&(T.tpx<PMAX)]
et=T.open.dt.tz_convert("America/New_York")
if SKIP: T=T[~et.dt.hour.between(3,8)]
key=T.t+"|"+T.taker+"|"+T.tpx.round(4).astype(str); T["run"]=(key!=key.shift()).cumsum()
T["cum"]=T.groupby("run").n.cumsum(); T["cum0"]=T.cum-T.n
T["fill"]=np.clip(T.cum-Q,0,None)-np.clip(T.cum0-Q,0,None)
T["fb"]=T.groupby("run").fill.cumsum()-T.fill; T["fill"]=np.clip(np.minimum(T.fill,N-T.fb),0,None)
T["pnl"]=T.fill*(-T.traw)
w=T.groupby("t").agg(pnl=("pnl","sum"),fill=("fill","sum"),open=("open","first"))
d=w.groupby(w.open.dt.tz_convert("America/New_York").dt.date).agg(pnl=("pnl","sum"),fill=("fill","sum"),windows=("pnl","size"))
eq=d.pnl.cumsum(); dd=(eq-eq.cummax()).min()
print(f"{ser} N={N:.0f} Q={Q:.0f} min1-{M1} dog<{PMAX} skipLondonAM={SKIP}: days={len(d)} total=${d.pnl.sum():+.0f} contracts={d.fill.sum():.0f} c/contract={100*d.pnl.sum()/d.fill.sum():+.2f}")
print(f"   avg/day ${d.pnl.mean():+.0f}  median/day ${d.pnl.median():+.0f}  worst day ${d.pnl.min():+.0f}  best day ${d.pnl.max():+.0f}  positive days {(d.pnl>0).mean():.0%}  max drawdown ${dd:+.0f}")
print(f"   worst window ${w.pnl.min():+.0f}  avg contracts/window {w.fill.mean():.0f}  max contracts/window {w.fill.max():.0f}")
