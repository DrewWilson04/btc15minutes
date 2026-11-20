import httpx, json, time
B="https://api.elections.kalshi.com/trade-api/v2"
out=[]; cur=None
c=httpx.Client(timeout=30)
while True:
    p={"series_ticker":"KXETH15M","limit":1000}
    if cur: p["cursor"]=cur
    r=c.get(B+"/markets",params=p); r.raise_for_status(); d=r.json()
    out+=d["markets"]; cur=d.get("cursor")
    print(len(out), out[-1]["ticker"] if out else None, flush=True)
    if not cur or not d["markets"]: break
    time.sleep(0.2)
json.dump(out,open("data/markets.json","w"))
