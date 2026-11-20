# Out-of-sample check of the WTI maker rule on windows NOT used to choose it (opened before CUT).
import pandas as pd, numpy as np, sys
CUT=pd.Timestamp(sys.argv[1] if len(sys.argv)>1 else "2026-10-30T23:45Z")
T=pd.read_pickle("data/KXWTI15M_T.pkl").sort_values(["t","ts"]).reset_index(drop=True)
T["min"]=(T.sec//60).astype(int)+1; T["mp"]=-T.traw*T.n
H=T[T.open<CUT]; I=T[T.open>=CUT]
print("holdout windows",H.t.nunique(),H.open.min(),"->",H.open.max(),"| in-sample windows",I.t.nunique())
def tape(S,lab):
    g=S.groupby("t").mp.sum(); t=g.mean()/g.std()*np.sqrt(len(g))
    print(f"  tape {lab}: contracts {S.n.sum()/1e6:.1f}M maker {100*S.mp.sum()/S.n.sum():+.2f}c/contract t={t:+.2f}")
def touch(S,Q=300,N=50):
    S=S.copy(); key=S.t+"|"+S.taker+"|"+S.tpx.round(4).astype(str); S["run"]=(key!=key.shift()).cumsum()
    S["cum"]=S.groupby("run").n.cumsum(); S["cum0"]=S.cum-S.n
    S["fill"]=np.clip(S.cum-Q,0,None)-np.clip(S.cum0-Q,0,None); S["fb"]=S.groupby("run").fill.cumsum()-S.fill
    S["fill"]=np.clip(np.minimum(S.fill,N-S.fb),0,None); S["pnl"]=S.fill*(-S.traw)
    g=S.groupby("t").agg(p=("pnl","sum"),f=("fill","sum"),o=("open","first"))
    d=g.groupby(g.o.dt.tz_convert("America/New_York").dt.date).p.sum()
    return f"c/contract={100*g.p.sum()/g.f.sum():+.2f} t={g.p.mean()/g.p.std()*np.sqrt(len(g)):+.2f} $={g.p.sum():+.0f} days={len(d)} $/day={d.mean():+.0f} pos_days={(d>0).mean():.0%}"
for nm,D in [("HOLDOUT",H),("in-sample",I)]:
    print("==",nm)
    et=D.open.dt.tz_convert("America/New_York").dt.hour
    rule=D[(D["min"]<=9)&(D.tpx<0.40)]
    rule_s=rule[~et[rule.index].between(3,8)]
    tape(D[D.tpx<0.5],"all underdog flow"); tape(rule,"rule: min1-9 dog<0.40"); tape(rule_s,"rule + skip 03-08 ET")
    print("  touch-maker Q=300 N=50 rule          :",touch(rule))
    print("  touch-maker Q=300 N=50 rule+skip     :",touch(rule_s))
    late=D[(D["min"].between(13,14))&(D.tpx<0.5)]; tape(late,"late underdog flow min13-14 (predicted negative)")
