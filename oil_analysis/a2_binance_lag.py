import pandas as pd, numpy as np, sys, statsmodels.api as sm
ser=sys.argv[1]
w=pd.read_pickle(f"data/{ser}_w2.pkl"); r=pd.read_pickle(f"data/{ser}_r.pkl")
w=w.sort_values("open").reset_index(drop=True)
bk=w[[f"b{k}" for k in range(16)]].values
d=r.merge(w[["t","yes","open","sig"]].assign(i=np.arange(len(w))),on="t")
d["mid"]=(d.bid+d.ask)/2
d["D"]=bk[d.i,d.k]-bk[d.i,0]                     # binance move since window open
d["D1"]=bk[d.i,d.k]-bk[d.i,(d.k-1).clip(0)]      # last-minute binance move
d["z"]=d.D/(d.sig*np.sqrt(15-d.k+0.5))
lg=lambda p: np.log(p/(1-p))
d=d.dropna(subset=["z","mid","D1"])
print("== does Binance add info beyond Kalshi mid? logit(yes) ~ logit(mid) + z + D1/sig")
for k in [2,4,6,8,10,12,13,14]:
    s=d[(d.k==k)&(d.mid>.03)&(d.mid<.97)]
    X=sm.add_constant(pd.DataFrame({"Lmid":lg(s.mid),"z":s.z,"d1":s.D1/s.sig}))
    res=sm.Logit(s.yes,X).fit(disp=0)
    print(f"k={k:2d} n={len(s):5d}  "+"  ".join(f"{c}:{res.params[c]:+.3f}(t={res.tvalues[c]:+.1f})" for c in X.columns))
print("\n== lead-lag: next-minute Kalshi mid change ~ this-minute Binance move")
d=d.sort_values(["t","k"]); d["dmid_next"]=d.groupby("t").mid.shift(-1)-d.mid; d["dmid"]=d.groupby("t").mid.diff()
s=d[(d.k>=2)&(d.k<=13)&(d.mid>.05)&(d.mid<.95)].dropna(subset=["dmid_next","dmid"])
X=sm.add_constant(pd.DataFrame({"D1n":s.D1/s.sig,"dmid":s.dmid}))
res=sm.OLS(s.dmid_next,X).fit(cov_type="cluster",cov_kwds={"groups":s.t.astype("category").cat.codes})
print(res.params.round(4).to_dict(), res.tvalues.round(1).to_dict())
d.to_pickle(f"data/{ser}_panel.pkl")
