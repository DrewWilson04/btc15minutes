import httpx, json, time, collections
B="https://api.elections.kalshi.com/trade-api/v2"; c=httpx.Client(timeout=30)
out=[]
for st in ["all","active","upcoming","closed","paid_out",None]:
    cur=None; n0=len(out)
    for page in range(400):
        p={"limit":10000}
        if st: p["status"]=st
        if cur: p["cursor"]=cur
        r=c.get(B+"/incentive_programs",params=p)
        if r.status_code==429: time.sleep(1); continue
        if r.status_code!=200: print(st,r.status_code,r.text[:200]); break
        d=r.json(); out+=d.get("incentive_programs",[]); cur=d.get("next_cursor") or d.get("cursor")
        if not cur or not d.get("incentive_programs"): break
    print("status",st,"->",len(out)-n0)
u={x["id"]:x for x in out}; L=list(u.values())
json.dump(L,open("data/incentives.json","w"))
print("unique programs",len(L))
print(collections.Counter((x.get("incentive_type"),x.get("incentive_description")) for x in L).most_common())
oil=[x for x in L if any(k in (x.get("series_ticker") or "") for k in ["WTI","BRENT","OIL"])]
print("oil programs",len(oil)); 
for x in oil[:20]: print({k:x.get(k) for k in ["series_ticker","market_ticker","incentive_type","incentive_description","period_reward","start_date","end_date","target_size_fp","discount_factor_bps","paid_out"]})
s15=[x for x in L if (x.get("series_ticker") or "").endswith("15M")]
print("15M-series programs",len(s15), collections.Counter(x["series_ticker"] for x in s15).most_common(10))
vol=[x for x in L if x.get("incentive_type")!="liquidity"]
print("non-liquidity programs",len(vol))
for x in vol[:10]: print({k:x.get(k) for k in ["series_ticker","market_ticker","incentive_type","incentive_description","period_reward","start_date","end_date"]})
print("date range",min(x["start_date"] for x in L),max(x["end_date"] for x in L))
