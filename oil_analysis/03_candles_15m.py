# usage: candlesS.py SERIES  -> data/{S}_candles.json  (1-min candles, live batch + historical per-ticker)
import httpx, json, time, sys, datetime as dt, os
B="https://api.elections.kalshi.com/trade-api/v2"
ser=sys.argv[1]; group=int(sys.argv[2]) if len(sys.argv)>2 else 20
ts=lambda s: int(dt.datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
live=[m for m in json.load(open(f"data/{ser}_markets.json")) if m["status"]=="finalized"]
hist=json.load(open(f"data/{ser}_hist.json")) if os.path.exists(f"data/{ser}_hist.json") else []
livet={m["ticker"] for m in live}
hist=[m for m in hist if m["ticker"] not in livet]
c=httpx.Client(timeout=60)
def get(url,params):
    for a in range(10):
        try: r=c.get(url,params=params)
        except Exception as e: time.sleep(2*(a+1)); continue
        if r.status_code in (429,500,502,503,504): time.sleep(1.0*(a+1)); continue
        r.raise_for_status(); return r.json()
    raise RuntimeError("failed "+url)
out={}
fn=f"data/{ser}_candles.json"
if os.path.exists(fn): out=json.load(open(fn))
live.sort(key=lambda m:m["open_time"])
todo=[m for m in live if m["ticker"] not in out]
groups=[];g=[]
for m in todo:
    if g and (ts(m["close_time"])-ts(g[0]["open_time"])>group*900 or len(g)>=group): groups.append(g); g=[]
    g.append(m)
if g: groups.append(g)
for i,g in enumerate(groups):
    d=get(B+"/markets/candlesticks",{"market_tickers":",".join(m["ticker"] for m in g),"start_ts":min(ts(m["open_time"]) for m in g),"end_ts":max(ts(m["close_time"]) for m in g),"period_interval":1})
    for mk in d["markets"]: out[mk["market_ticker"]]=mk["candlesticks"]
    for m in g: out.setdefault(m["ticker"],[])
    if i%50==0: print("live",i,len(groups),flush=True)
    time.sleep(0.12)
json.dump(out,open(fn,"w"))
todo=[m for m in hist if m["ticker"] not in out]
for j,m in enumerate(todo):
    d=get(B+f"/historical/markets/{m['ticker']}/candlesticks",{"start_ts":ts(m["open_time"]),"end_ts":ts(m["close_time"]),"period_interval":1})
    out[m["ticker"]]=d.get("candlesticks",[])
    if j%500==0: print("hist",j,len(todo),flush=True); json.dump(out,open(fn,"w"))
    time.sleep(0.1)
json.dump(out,open(fn,"w")); print("done",ser,len(out))
