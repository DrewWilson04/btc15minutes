# One row per KXWTIH strike-market (live + historical), used to select near-the-money strikes.
import json, pandas as pd, numpy as np
L=[m for m in json.load(open("data/KXWTIH_markets.json")) if m["status"]=="finalized"]
H=json.load(open("data/KXWTIH_hist.json"))
d={m["ticker"]:m for m in H}; d.update({m["ticker"]:m for m in L})
df=pd.DataFrame([dict(t=m["ticker"],ev=m["event_ticker"],open=m["open_time"],close=m["close_time"],K=m.get("floor_strike"),
    st=m.get("strike_type"),X=float(m["expiration_value"]) if m.get("expiration_value") not in (None,"") else np.nan,res=m["result"],
    vol=float(m.get("volume_fp") or m.get("volume") or 0)) for m in d.values()])
df["open"]=pd.to_datetime(df.open); df["close"]=pd.to_datetime(df.close)
df.to_pickle("data/KXWTIH_all.pkl"); print(len(df),"markets",df.ev.nunique(),"events")
