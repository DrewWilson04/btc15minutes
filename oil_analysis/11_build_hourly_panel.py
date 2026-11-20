import json, pandas as pd, numpy as np
sel=pd.read_pickle("data/KXWTIH_sel.pkl")
C=json.load(open("data/KXWTIH_candles.json"))
sel=sel[sel.t.isin(C.keys())].copy()
def fv(d,k="close_dollars"):
    if not d or d.get(k) in (None,""): return np.nan
    return float(d[k])
R=[]
for tk,cl in zip(sel.t,sel.close):
    cl=int(cl.timestamp())
    for c in C[tk]:
        mb=(cl-c["end_period_ts"])//60   # minutes before close at candle end
        R.append((tk,mb,fv(c.get("yes_bid")),fv(c.get("yes_ask")),float(c.get("volume_fp") or 0)))
r=pd.DataFrame(R,columns=["t","mb","bid","ask","v"])
r=r[(r.mb>=0)&(r.mb<=120)]
# full grid per market (minutes before close 120..0), ffill forward in time (i.e. decreasing mb)
out=[]
for tk,g in r.groupby("t"):
    g=g.drop_duplicates("mb",keep="last").set_index("mb").sort_index(ascending=False)
    idx=pd.Index(range(int(g.index.max()),-1,-1),name="mb")
    g=g.reindex(idx); g["v"]=g.v.fillna(0); g[["bid","ask"]]=g[["bid","ask"]].ffill()
    g["t"]=tk; out.append(g.reset_index())
r=pd.concat(out)
r=r.merge(sel[["t","ev","K","X","res","close","vol"]],on="t")
r["yes"]=(r.res=="yes").astype(int)
r.to_pickle("data/KXWTIH_r.pkl")
print(r.shape, r.ev.nunique(), r.t.nunique())
# settlement identity vs 15m
w=pd.read_pickle("data/KXWTI15M_w.pkl"); w["end"]=w.open+pd.Timedelta(minutes=15)
e=sel.groupby("close").X.first()
m=w.set_index("end").X.reindex(e.index)
ok=m.notna()
print("hourly X vs 15m X at same instant: n",ok.sum(),"identical share",(np.round(m[ok],2)==np.round(e[ok],2)).mean().round(4),"max abs diff",(m[ok]-e[ok]).abs().max())
