# Build per-minute panel for a 15m oil series: Kalshi quotes (ffilled) + Binance perp path + outcome
import json, pandas as pd, numpy as np, sys
sys.path.insert(0,".")
from binload import load
ser,sym=sys.argv[1],sys.argv[2]
w=pd.read_pickle(f"data/{ser}_w.pkl")
C=json.load(open(f"data/{ser}_candles.json"))
def fv(d,*ks):
    if not d: return np.nan
    for k in ks:
        if d.get(k) not in (None,""): return float(d[k])
    return np.nan
R=[]
for tk,o in zip(w.t,w.open):
    o=int(o.timestamp())
    for c in C.get(tk,[]):
        k=(c["end_period_ts"]-o)//60
        if 1<=k<=15:
            R.append((tk,k,fv(c.get("yes_bid"),"close_dollars","close"),fv(c.get("yes_ask"),"close_dollars","close"),
                      fv(c.get("price"),"close_dollars","close"),fv(c,"volume_fp","volume"),fv(c,"open_interest_fp","open_interest")))
r=pd.DataFrame(R,columns=["t","k","bid","ask","last","v","oi"])
# full grid & forward fill quotes within market (candles only emitted on change)
grid=pd.MultiIndex.from_product([w.t,range(1,16)],names=["t","k"])
r=r.set_index(["t","k"]).reindex(grid)
r["v"]=r.v.fillna(0)
r[["bid","ask","last","oi"]]=r.groupby(level=0)[["bid","ask","last","oi"]].ffill()
r=r.reset_index()
print("rows",len(r),"missing quotes after ffill",r.ask.isna().mean().round(3))
B=load(sym)
w["b0"]=w.open.map(B.close)
for k in range(0,16): w[f"b{k}"]=(w.open+pd.Timedelta(minutes=k)).map(B.close)
# realized 1-min vol over trailing 60 minutes (std of 1m diffs, in $)
dif=B.close.diff()
vol60=dif.rolling(60,min_periods=30).std()
w["sig"]=w.open.map(vol60)
w.to_pickle(f"data/{ser}_w2.pkl"); r.to_pickle(f"data/{ser}_r.pkl")
print(w[["K","X","b0","b15","sig"]].describe().round(3))
