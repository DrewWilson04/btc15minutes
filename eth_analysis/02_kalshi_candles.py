import httpx, json, time, datetime as dt
B="https://api.elections.kalshi.com/trade-api/v2"
ms=[m for m in json.load(open("data/markets.json")) if m["status"]=="finalized"]
ts=lambda s: int(dt.datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
ms.sort(key=lambda m: m["open_time"])
c=httpx.Client(timeout=60); res={}
N=20
for i in range(0,len(ms),N):
    g=ms[i:i+N]
    p={"market_tickers":",".join(m["ticker"] for m in g),"start_ts":ts(g[0]["open_time"]),"end_ts":ts(g[-1]["close_time"]),"period_interval":1}
    for a in range(5):
        r=c.get(B+"/markets/candlesticks",params=p)
        if r.status_code==429: time.sleep(2*(a+1)); continue
        r.raise_for_status(); break
    for mk in r.json()["markets"]:
        res[mk["market_ticker"]]=mk["candlesticks"]
    if i%400==0: print(i,len(res),flush=True)
    time.sleep(0.15)
json.dump(res,open("data/candles.json","w"))
print("done",len(res))
