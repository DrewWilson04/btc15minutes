# Brent maker economics during vs after its liquidity-reward week, plus reward-share scenarios.
import pandas as pd, numpy as np
T=pd.read_pickle("data/KXBRENT15M_T.pkl").sort_values(["t","ts"]).reset_index(drop=True)
T["min"]=(T.sec//60).astype(int)+1; T["mp"]=-T.traw*T.n
LIP_END=pd.Timestamp("2026-10-28T04:00Z")
def touch(S,Q,N):
    S=S.copy(); key=S.t+"|"+S.taker+"|"+S.tpx.round(4).astype(str); S["run"]=(key!=key.shift()).cumsum()
    S["cum"]=S.groupby("run").n.cumsum(); S["cum0"]=S.cum-S.n
    S["fill"]=np.clip(S.cum-Q,0,None)-np.clip(S.cum0-Q,0,None); S["fb"]=S.groupby("run").fill.cumsum()-S.fill
    S["fill"]=np.clip(np.minimum(S.fill,N-S.fb),0,None); S["pnl"]=S.fill*(-S.traw)
    return S.groupby("t").agg(p=("pnl","sum"),f=("fill","sum"))
for nm,D in [("LIP week (Oct 21-28)",T[T.open<LIP_END]),("after LIP (Oct 28-Nov 20)",T[T.open>=LIP_END])]:
    D=D[D["min"]<=14]; g2=touch(D,150,300)
    print(f"{nm}: windows {D.t.nunique()} | tape maker all-flow {100*D.mp.sum()/D.n.sum():+.2f}c | two-sided touch-maker (Q=150, 300/level): {100*g2.p.sum()/g2.f.sum():+.2f}c/contract, ${g2.p.mean():+.1f}/window")
for Z in [300,900,2700]:
    sh=300/(300+Z); print(f"  reward share if others rest {Z}: {sh:.0%} -> ${50*sh:.1f}/window")
