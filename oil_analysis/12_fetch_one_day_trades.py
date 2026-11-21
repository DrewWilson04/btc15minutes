import httpx, json, time, sys, datetime as dt
B="https://api.elections.kalshi.com/trade-api/v2"; c=httpx.Client(timeout=30)
def get(p,params):
    for a in range(10):
        r=c.get(B+p,params=params)
        if r.status_code==429: time.sleep(1+a); continue
        r.raise_for_status(); return r.json()
out={}
for ser in ["KXBRENT15M","KXWTI15M"]:
    rows=[]; mk={}
    for h in range(24):
        for m in (0,15,30,45):
            end=dt.datetime(2026,11,20,h,m)+dt.timedelta(minutes=15)   # ET close time
            tk=f"{ser}-26NOV{end:%d%H%M}-{end:%M}" if end.day==20 else f"{ser}-26NOV{end:%d%H%M}-{end:%M}"
            try: M=get(f"/markets/{tk}",{})["market"]
            except Exception as e: print("miss",tk); continue
            mk[tk]={"open":M["open_time"],"result":M.get("result")}
            cur=None
            while True:
                p={"ticker":tk,"limit":1000}
                if cur:p["cursor"]=cur
                d=get("/markets/trades",p); rows+= [[tk,t["created_time"],float(t["yes_price_dollars"]),float(t["count_fp"]),t["taker_side"]] for t in d["trades"]]
                cur=d.get("cursor")
                if not cur or not d["trades"]: break
                time.sleep(0.1)
            time.sleep(0.1)
    out[ser]={"markets":mk,"trades":rows}; print(ser,len(mk),"markets",len(rows),"trades",flush=True)
json.dump(out,open("data/day1120.json","w"))
