# hourly WTI ladder candles for strikes within +-BAND of reference price at event open (ex-ante)
import httpx, json, time, sys, os, pandas as pd, numpy as np
B="https://api.elections.kalshi.com/trade-api/v2"
BAND=float(sys.argv[1]) if len(sys.argv)>1 else 0.6
df=pd.read_pickle("data/KXWTIH_all.pkl")
df=df[df.close>=pd.Timestamp("2026-07-31T00:00Z")]
w=pd.read_pickle("data/KXWTI15M_w.pkl")   # 15m chain: K at window open time = Pyth price at that instant
ref=dict(zip(w.open,w.K))
evX=df.groupby("close").X.first().to_dict()
live={m["ticker"] for m in json.load(open("data/KXWTIH_markets.json"))}
E=df.groupby("ev").agg(open=("open","min"),close=("close","max")).reset_index()
def refprice(o):
    o2=o.floor("15min")
    if o2 in ref: return ref[o2]
    if o.floor("h") in evX: return evX[o.floor("h")]
    return np.nan
E["ref"]=E.open.map(refprice)
print("events",len(E),"no ref",E.ref.isna().sum())
sel=df.merge(E[["ev","ref"]],on="ev")
sel=sel[(sel.K-sel.ref).abs()<=BAND+1e-9]
print("selected markets",len(sel), "live",sel.t.isin(live).sum())
sel.to_pickle("data/KXWTIH_sel.pkl")
fn="data/KXWTIH_candles.json"
out=json.load(open(fn)) if os.path.exists(fn) else {}
c=httpx.Client(timeout=60)
def get(url,params):
    for a in range(12):
        try: r=c.get(url,params=params)
        except Exception: time.sleep(2*(a+1)); continue
        if r.status_code in (429,500,502,503,504): time.sleep(0.8*(a+1)); continue
        if r.status_code==400: print("400",r.text[:200]); return None
        r.raise_for_status(); return r.json()
    raise RuntimeError("failed")
n=0
for ev,g in sel[sel.t.isin(live)].groupby("ev"):
    g=g[~g.t.isin(out)]
    if g.empty: continue
    d=get(B+"/markets/candlesticks",{"market_tickers":",".join(g.t),"start_ts":int(g.open.min().timestamp()),"end_ts":int(g.close.max().timestamp()),"period_interval":1})
    if d:
        for mk in d["markets"]: out[mk["market_ticker"]]=mk["candlesticks"]
    for t in g.t: out.setdefault(t,[])
    n+=1
    if n%100==0: print("live ev",n,flush=True); json.dump(out,open(fn,"w"))
    time.sleep(0.12)
json.dump(out,open(fn,"w"))
H=sel[~sel.t.isin(live)]
for j,(i,m) in enumerate(H.iterrows()):
    if m.t in out: continue
    d=get(B+f"/historical/markets/{m.t}/candlesticks",{"start_ts":int(m.open.timestamp()),"end_ts":int(m.close.timestamp()),"period_interval":1})
    out[m.t]=(d or {}).get("candlesticks",[])
    if j%500==0: print("hist",j,len(H),flush=True); json.dump(out,open(fn,"w"))
    time.sleep(0.1)
json.dump(out,open(fn,"w")); print("done",len(out))
