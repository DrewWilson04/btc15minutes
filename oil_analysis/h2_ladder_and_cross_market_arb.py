import pandas as pd, numpy as np
r=pd.read_pickle("data/KXWTIH_r.pkl"); r=r[r.bid.notna()&r.ask.notna()]
feeT=lambda p: 0.07*p*(1-p)
# (a) ladder monotonicity across adjacent strikes, same event & minute
r=r.sort_values(["ev","mb","K"])
r["ask_lo"]=r.groupby(["ev","mb"]).ask.shift(1)   # ask of next-lower strike
r["K_lo"]=r.groupby(["ev","mb"]).K.shift(1)
v=r[(r.ask_lo.notna())&((r.K-r.K_lo).round(2)==0.10)&(r.bid>0)&(r.ask_lo<1)]
v=v.assign(gross=v.bid-v.ask_lo); v["net"]=v.gross-feeT(v.ask_lo)-feeT(1-v.bid)
a=v[v.net>0]
print("(a) monotonic-violation (ask lower strike < bid higher strike) minute-snapshots:",len(a),"of",len(v),"| events",a.ev.nunique(),"| median net",a.net.median().round(3) if len(a) else None)
if len(a): print(a.groupby(pd.cut(a.mb,[-1,5,15,30,60,120])).agg(n=("net","size"),net=("net","median")).to_string())
# (b) 15m vs hourly bounds, for the 15m window ending at the hourly close
w=pd.read_pickle("data/KXWTI15M_w.pkl"); w["end"]=w.open+pd.Timedelta(minutes=15)
r15=pd.read_pickle("data/KXWTI15M_r.pkl")  # k=1..15 ; minutes-before-close = 15-k
r15=r15.merge(w[["t","end","K","yes"]],on="t"); r15["mb"]=15-r15.k
H=r[["ev","close","mb","K","bid","ask","yes"]]
out=[]
for (end,mb),g in r15.groupby(["end","mb"]):
    pass
m=r15.merge(H,left_on=["end","mb"],right_on=["close","mb"],suffixes=("15","H"))
# K_hi: smallest hourly strike >= K15 ; K_lo: largest hourly strike < K15
hi=m[m.KH>=m.K15-1e-9].sort_values("KH").groupby(["t","mb"]).head(1)
lo=m[m.KH<m.K15-1e-9].sort_values("KH").groupby(["t","mb"]).tail(1)
hi=hi.assign(net=hi.bidH-hi.ask15-feeT(hi.ask15)-feeT(1-hi.bidH))   # buy 15m YES + buy hourly NO(K_hi)
lo=lo.assign(net=lo.bid15-lo.askH-feeT(1-lo.bid15)-feeT(lo.askH))   # buy 15m NO + buy hourly YES(K_lo)
for nm,s in [("15m YES + hourly NO(K_hi)",hi),("15m NO + hourly YES(K_lo)",lo)]:
    s=s[(s.bidH>0)&(s.askH<1)&s.ask15.notna()]
    x=s[s.net>0]
    print(f"(b) {nm}: snapshots {len(s)}, arb>0 after fees: {len(x)} ({len(x)/max(len(s),1):.2%}), windows {x.t.nunique()}, median net {x.net.median() if len(x) else 0:.3f}, mean net {x.net.mean() if len(x) else 0:.3f}")
    if len(x): print(x.groupby("mb").agg(n=("net","size"),net=("net","median")).T.round(3).to_string())
m.to_pickle("data/cross_15_H.pkl")
