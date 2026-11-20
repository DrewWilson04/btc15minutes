import json, pandas as pd, numpy as np, datetime as dt
ts=lambda s: int(dt.datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
ms={m["ticker"]:m for m in json.load(open("data/markets.json")) if m["status"]=="finalized"}
C=json.load(open("data/candles.json"))
spot=pd.DataFrame(json.load(open("data/spot.json")),columns=["t","lo","hi","op","cl","vol"]).set_index("t")
f=lambda d,k: float(d[k]) if d and d.get(k) is not None else np.nan
W=[];R=[]
for tk,m in ms.items():
    o=ts(m["open_time"]); cl=ts(m["close_time"])
    W.append(dict(ticker=tk,open=o,strike=m.get("floor_strike"),final=float(m["expiration_value"]) if m.get("expiration_value") else np.nan,
                  yes=1 if m["result"]=="yes" else 0, vol=float(m.get("volume_fp") or 0)))
    for c in C.get(tk,[]):
        k=(c["end_period_ts"]-o)//60  # minute index 1..15 (end of minute k)
        if k<1 or k>15: continue
        R.append(dict(ticker=tk,k=k,bid=f(c["yes_bid"],"close_dollars"),ask=f(c["yes_ask"],"close_dollars"),
                      last=f(c["price"],"close_dollars"),v=float(c.get("volume_fp") or 0)))
w=pd.DataFrame(W).sort_values("open").reset_index(drop=True)
r=pd.DataFrame(R)
# spot: coinbase close at end of minute k => candle starting at open+60*(k-1)
sc=spot["cl"]
for k in range(0,16):
    w[f"s{k}"]=w["open"].map(lambda o: sc.get(o+60*k-60, np.nan))
w.to_parquet("data/w.parquet"); r.to_parquet("data/r.parquet")
print(w.shape,r.shape); print(w.head(3).T.head(12)); print(r.describe())
