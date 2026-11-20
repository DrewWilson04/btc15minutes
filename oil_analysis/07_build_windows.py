# Merge live + historical market metadata into one row per 15m window (strike K = Pyth at open, X = Pyth at close).
import json, pandas as pd, numpy as np, sys
for ser in sys.argv[1:] or ["KXWTI15M","KXBRENT15M"]:
    L=[m for m in json.load(open(f"data/{ser}_markets.json")) if m["status"]=="finalized"]
    try: H=json.load(open(f"data/{ser}_hist.json"))
    except FileNotFoundError: H=[]
    d={m["ticker"]:m for m in H}; d.update({m["ticker"]:m for m in L})
    df=pd.DataFrame([dict(t=m["ticker"],open=m["open_time"],close=m["close_time"],K=m.get("floor_strike"),
        X=float(m["expiration_value"]) if m.get("expiration_value") not in (None,"") else np.nan,res=m["result"],
        vol=float(m.get("volume_fp") or m.get("volume") or 0)) for m in d.values()])
    df["open"]=pd.to_datetime(df.open); df=df.sort_values("open").reset_index(drop=True)
    df["yes"]=(df.res=="yes").astype(int); df["chg"]=(df.X-df.K).round(2)
    df.to_pickle(f"data/{ser}_w.pkl"); print(ser,len(df),"yes",df.yes.mean().round(4),"ties",(df.chg==0).mean().round(4))
