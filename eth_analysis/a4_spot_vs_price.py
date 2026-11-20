import pandas as pd, numpy as np, statsmodels.api as sm
w=pd.read_parquet("data/w.parquet"); r=pd.read_parquet("data/r.parquet")
w=w.sort_values("open").reset_index(drop=True)
piv=lambda c: r.pivot(index="ticker",columns="k",values=c)
B,A=piv("bid"),piv("ask"); M=((B+A)/2).reindex(w.ticker)
lg=lambda p: np.log(p/(1-p))
h=len(w)//2
for k in [3,5,8,10,12,13]:
    mid=M[k].values.clip(.02,.98)
    d=pd.DataFrame({"y":w.yes,"L":lg(mid),
        "mv1":(w[f"s{k}"]-w[f"s{k-1}"])/w.strike*1e4,        # last-minute spot move bps
        "mv3":(w[f"s{k}"]-w[f"s{k-3}"])/w.strike*1e4,
        "dist":(w[f"s{k}"]-w.strike)/w.strike*1e4,
        "dmid":lg(mid)-lg(M[k-1].values.clip(.02,.98))})
    d=d.dropna(); d=d[(M[k].reindex(w.ticker).values[d.index]>.05)&(M[k].values[d.index]<.95)]
    X=sm.add_constant(d[["L","mv1","mv3","dist","dmid"]]); res=sm.Logit(d.y,X).fit(disp=0)
    print(f"k={k} n={len(d)}"); print(pd.DataFrame({"coef":res.params,"t":res.tvalues}).round(3).T.to_string())
