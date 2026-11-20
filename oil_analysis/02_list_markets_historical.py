import httpx, json, time, sys, collections
B="https://api.elections.kalshi.com/trade-api/v2"
ser=sys.argv[1]; out=[]; cur=None
c=httpx.Client(timeout=60); pages=0
while True:
    p={"series_ticker":ser,"limit":1000}
    if cur: p["cursor"]=cur
    for a in range(8):
        r=c.get(B+"/historical/markets",params=p)
        if r.status_code in (429,500,502,503): time.sleep(1.5*(a+1)); continue
        r.raise_for_status(); break
    d=r.json(); out+=d.get("markets",[]); cur=d.get("cursor"); pages+=1
    if pages%20==0: print(ser,len(out),out[-1]["open_time"],flush=True)
    if not cur or not d.get("markets"): break
    time.sleep(0.2)
json.dump(out,open(f"data/{ser}_hist.json","w"))
print(ser,len(out),collections.Counter(m["status"] for m in out), min((m["open_time"] for m in out),default=None), max((m["close_time"] for m in out),default=None))
