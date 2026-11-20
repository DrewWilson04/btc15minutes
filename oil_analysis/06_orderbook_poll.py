import httpx, json, time, datetime as dt
B="https://api.elections.kalshi.com/trade-api/v2"
c=httpx.Client(timeout=20); out=open("data/ob_snap.jsonl","a"); cur={}
end=time.time()+32*60
while time.time()<end:
    for ser in ["KXWTI15M","KXBRENT15M"]:
        try:
            if ser not in cur or time.time()>cur[ser][1]:
                m=c.get(B+"/markets",params={"series_ticker":ser,"status":"open","limit":1}).json()["markets"][0]
                cur[ser]=(m["ticker"],dt.datetime.fromisoformat(m["close_time"].replace("Z","+00:00")).timestamp(),m["open_time"])
            tk=cur[ser][0]
            ob=c.get(B+f"/markets/{tk}/orderbook",params={"depth":10}).json()
            out.write(json.dumps({"ts":time.time(),"ser":ser,"t":tk,"open":cur[ser][2],"ob":ob})+"\n"); out.flush()
        except Exception as e: print("err",e,flush=True)
    time.sleep(8)
print("done")
