# usage: tradesS.py SERIES -> data/{S}_trades.csv  columns: ticker,ts,yes_price,count,taker
import httpx, json, time, sys, os, datetime as dt, csv
B="https://api.elections.kalshi.com/trade-api/v2"
ser=sys.argv[1]
live=[m for m in json.load(open(f"data/{ser}_markets.json")) if m["status"]=="finalized"]
hist=json.load(open(f"data/{ser}_hist.json")) if os.path.exists(f"data/{ser}_hist.json") else []
livet={m["ticker"] for m in live}
START=os.environ.get("START","2026-10-21")
live=[m for m in live if m["open_time"]>=START]; hist=[m for m in hist if m["open_time"]>=START]
jobs=[(m["ticker"],"/markets/trades") for m in live]+[(m["ticker"],"/historical/trades") for m in hist if m["ticker"] not in livet]
SH=os.environ.get("SHARD","0/1"); si,sn=map(int,SH.split("/"))
jobs=[j for j in jobs if (sum(map(ord,j[0]))%sn)==si]
fn=f"data/{ser}_trades{si}.csv"; donef=f"data/{ser}_trades{si}.done"
done=set(open(donef).read().split()) if os.path.exists(donef) else set()
c=httpx.Client(timeout=60)
def get(url,params):
    for a in range(12):
        try: r=c.get(url,params=params)
        except Exception: time.sleep(2*(a+1)); continue
        if r.status_code in (429,500,502,503,504): time.sleep(0.8*(a+1)); continue
        r.raise_for_status(); return r.json()
    raise RuntimeError("failed "+url)
f=open(fn,"a",newline=""); w=csv.writer(f); df=open(donef,"a")
P=lambda t,k1,k2: t.get(k1) if t.get(k1) is not None else t.get(k2)
for j,(tk,ep) in enumerate(jobs):
    if tk in done: continue
    cur=None; rows=[]
    while True:
        p={"ticker":tk,"limit":1000}
        if cur: p["cursor"]=cur
        d=get(B+ep,p)
        for t in d.get("trades",[]):
            rows.append((tk,t["created_time"],P(t,"yes_price_dollars","yes_price"),P(t,"count_fp","count"),t.get("taker_side")))
        cur=d.get("cursor")
        time.sleep(0.12)
        if not cur or not d.get("trades"): break
    w.writerows(rows); f.flush(); df.write(tk+"\n"); df.flush()
    if j%250==0: print(ser,j,len(jobs),len(rows),flush=True)
print("done",ser)
