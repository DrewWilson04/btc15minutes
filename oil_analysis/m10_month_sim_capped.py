import json, pandas as pd, numpy as np, sys
D=json.load(open("data/day1120.json"))
def load(ser):
    T=pd.read_pickle(f"data/{ser}_T.pkl")[["t","ts","open","sec","tpx","taker","n","yes"]]
    d=pd.DataFrame(D[ser]["trades"],columns=["t","ts","p","n","taker"]); M=D[ser]["markets"]
    d["ts"]=pd.to_datetime(d.ts,format="ISO8601"); d["open"]=pd.to_datetime(d.t.map(lambda x:M[x]["open"]))
    d["yes"]=(d.t.map(lambda x:M[x]["result"])=="yes").astype(int); d["sec"]=(d.ts-d.open).dt.total_seconds()
    d["tpx"]=np.where(d.taker=="yes",d.p,1-d.p)
    T=pd.concat([T[~T.t.isin(d.t)],d[T.columns]])          # Friday from the full-day pull
    T=T[(T.sec>=0)&(T.sec<900)].sort_values(["t","ts"]).reset_index(drop=True)
    T["min"]=(T.sec//60).astype(int)+1; T["side"]=np.where(T.taker=="yes","no","yes"); T["px"]=1-T.tpx
    T["win"]=np.where(T.side=="yes",T.yes,1-T.yes); return T
def sim(T,maxmin,maxdog,Q,c1,c2,N=50):
    S=T[(T["min"]<=maxmin)&(T.tpx<maxdog)].copy()
    key=S.t+"|"+S.taker+"|"+S.tpx.round(4).astype(str); S["run"]=(key!=key.shift()).cumsum()
    S["cum"]=S.groupby("run").n.cumsum(); S["cum0"]=S.cum-S.n
    S["fill"]=np.clip(S.cum-Q,0,None)-np.clip(S.cum0-Q,0,None); S["fb"]=S.groupby("run").fill.cumsum()-S.fill
    S["fill"]=np.clip(np.minimum(S.fill,N-S.fb),0,None); S=S[S.fill>0].copy()
    first=S.groupby("t").side.transform("first"); cap=np.where(S.side==first,c1,c2)
    S["cost0"]=S.fill*S.px; S["cc"]=S.groupby(["t","side"]).cost0.cumsum(); S["prev"]=S.cc-S.cost0
    S["fill"]=S.fill*np.clip((cap-S.prev)/S.cost0,0,1)
    S["cost"]=S.fill*S.px; S["pnl"]=S.fill*(S.win-S.px)
    w=S.groupby("t").agg(put=("cost","sum"),pnl=("pnl","sum"),open=("open","first")); return w[w.put>0.5]
def report(name,w):
    d=w.groupby(w.open.dt.tz_convert("America/New_York").dt.date).agg(pnl=("pnl","sum"),put=("put","sum"),n=("pnl","size"))
    eq=d.pnl.cumsum(); wk=w.groupby(w.open.dt.tz_convert("America/New_York").dt.tz_localize(None).dt.to_period("W").astype(str)).pnl.sum()
    print(f"\n=== {name}: {len(d)} days, {len(w)} rounds, W/L {(w.pnl>0).sum()}/{(w.pnl<0).sum()}, put in ${w.put.sum():,.0f}")
    print(f"    NET ${w.pnl.sum():+,.0f}  ({100*w.pnl.sum()/w.put.sum():+.2f}% of money put in) | avg/day ${d.pnl.mean():+.0f} | up days {(d.pnl>0).sum()}/{len(d)} | best day ${d.pnl.max():+.0f} worst day ${d.pnl.min():+.0f} | max drawdown ${(eq-eq.cummax()).min():+.0f} | worst round ${w.pnl.min():+.0f}")
    print("    weekly: "+"  ".join(f"{k[:10]} ${v:+.0f}" for k,v in wk.items()))
    return d
res={}
for ser,maxmin,maxdog,Q,lab in [("KXBRENT15M",12,0.5,150,"BRENT (current rules)"),("KXBRENT15M",9,0.40,150,"BRENT with WTI rules (min 1-9, underdog<40c)"),("KXWTI15M",9,0.40,300,"WTI (current rules)")]:
    T=load(ser)
    for c2 in [130,175]:
        res[(lab,c2)]=report(f"{lab}, $100 first / ${c2} flip",sim(T,maxmin,maxdog,Q,100,c2))
