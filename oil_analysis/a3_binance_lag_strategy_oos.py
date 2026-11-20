import pandas as pd, numpy as np, sys, statsmodels.api as sm
ser=sys.argv[1]
d=pd.read_pickle(f"data/{ser}_panel.pkl").sort_values(["open","k"])
lg=lambda p: np.log(p/(1-p)); sg=lambda x: 1/(1+np.exp(-x))
feeT=lambda p: 0.07*p*(1-p)
d=d[(d.mid>.02)&(d.mid<.98)&d.ask.notna()&d.bid.notna()].copy()
# next-minute quotes (latency-robust execution)
d["ask_n"]=d.groupby("t").ask.shift(-1); d["bid_n"]=d.groupby("t").bid.shift(-1)
ts=d.open.sort_values().unique(); cut=ts[len(ts)//2]
tr=d[d.open<cut]; te=d[d.open>=cut]
def feats(s): return pd.DataFrame({"Lmid":lg(s.mid),"z":s.z,"zk":s.z*s.k/15,"Lk":lg(s.mid)*s.k/15}).assign(const=1.0)
res=sm.Logit(tr.yes,feats(tr)).fit(disp=0); print(res.params.round(3).to_dict())
for name,s in [("train",tr),("test",te)]:
    s=s.copy(); s["p"]=sg(feats(s)@res.params)
    for lag in ["now","next"]:
        a=s.ask if lag=="now" else s.ask_n; b=s.bid if lag=="now" else s.bid_n
        eY=s.p-a-feeT(a); eN=(1-s.p)-(1-b)-feeT(1-b)
        for th in [0.0,0.02,0.04,0.06]:
            rows=[]
            for side,e,px,win in [("Y",eY,a,s.yes),("N",eN,1-b,1-s.yes)]:
                m=(e>th)&(s.k>=2)&(s.k<=13)&px.notna()
                rows.append(pd.DataFrame({"t":s.t[m],"k":s.k[m],"pnl":(win-px-feeT(px))[m],"e":e[m]}))
            q=pd.concat(rows).sort_values(["t","k"]).groupby("t").head(1)   # first signal per window only
            if len(q)>20:
                print(f"{name:5s} exec={lag:4s} th={th:.2f}: trades={len(q):5d} winEV/contract={q.pnl.mean():+.4f} t={q.pnl.mean()/q.pnl.std()*np.sqrt(len(q)):+.2f} predicted edge={q.e.mean():.3f}")
