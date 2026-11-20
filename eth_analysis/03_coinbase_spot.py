import httpx, json, time, datetime as dt
c=httpx.Client(timeout=30); rows={}
t=dt.datetime(2026,9,12,23,0,tzinfo=dt.timezone.utc); end=dt.datetime(2026,11,20,17,30,tzinfo=dt.timezone.utc)
while t<end:
    t2=min(t+dt.timedelta(minutes=300),end)
    for a in range(6):
        r=c.get("https://api.exchange.coinbase.com/products/ETH-USD/candles",params={"granularity":60,"start":t.isoformat(),"end":t2.isoformat()})
        if r.status_code==429: time.sleep(1+a); continue
        r.raise_for_status(); break
    for x in r.json(): rows[x[0]]=x
    t=t2; time.sleep(0.12)
json.dump(sorted(rows.values()),open("data/spot.json","w")); print("spot",len(rows))
