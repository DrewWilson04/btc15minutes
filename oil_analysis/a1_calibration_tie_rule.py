import pandas as pd, numpy as np, sys, statsmodels.api as sm
ser=sys.argv[1]
w=pd.read_pickle(f"data/{ser}_w2.pkl"); r=pd.read_pickle(f"data/{ser}_r.pkl")
w=w.sort_values("open").reset_index(drop=True)
w["et"]=w.open.dt.tz_convert("America/New_York")
feeT=lambda p: 0.07*p*(1-p)
d=r.merge(w[["t","yes","open","et","chg","sig","K"]+[f"b{k}" for k in range(16)]],on="t")
d["mid"]=(d.bid+d.ask)/2
print("=====",ser,"windows",len(w),"rows",len(d))
print("median spread by minute:",d.groupby("k").apply(lambda s:(s.ask-s.bid).median()).round(3).to_dict())
print("median vol/min by k:",d.groupby("k").v.median().round(0).to_dict())
# ---- 1. tie rule vs minute-1 price
m1=d[d.k==1].copy()
print("\n[tie rule] overall YES",w.yes.mean().round(4),"| mean mid@1",m1.mid.mean().round(4),"| ties",(w.chg==0).mean().round(4))
g=m1.groupby(m1.et.dt.hour).agg(n=("yes","size"),yes=("yes","mean"),mid1=("mid","mean"))
g["tie"]=w.groupby(w.et.dt.hour).chg.apply(lambda s:(s==0).mean()).values
print(g.round(3).T.to_string())
# buy YES at ask at minute 1 in every window
p=m1.yes-m1.ask-feeT(m1.ask); print("buy YES@ask min1 all windows: EV",p.mean().round(4),"t",(p.mean()/p.std()*np.sqrt(len(p))).round(2))
# ---- 2. calibration (favorite side) by minute groups
print("\n[calibration] favorite side bought at ask")
for kk in [(1,3),(4,8),(9,12),(13,14)]:
    s=d[(d.k>=kk[0])&(d.k<=kk[1])&(d.ask>0)&(d.ask<1)&d.bid.notna()].copy()
    fy=s.mid>=.5
    s["px"]=np.where(fy,s.ask,1-s.bid); s["win"]=np.where(fy,s.yes,1-s.yes)
    s["upx"]=np.where(fy,1-s.bid,s.ask); s["uwin"]=1-s["win"]
    g=s.groupby(pd.cut(s.px,[.5,.6,.7,.8,.9,.95,.98,1.0]),observed=True).agg(n=("win","size"),px=("px","mean"),win=("win","mean"))
    g["net"]=g.win-g.px-feeT(g.px)
    u=s.groupby(pd.cut(s.upx,[0,.02,.05,.1,.2,.3,.4,.5]),observed=True).agg(n=("uwin","size"),px=("upx","mean"),win=("uwin","mean"))
    u["net"]=u.win-u.px-feeT(u.px)
    print("min",kk,"FAV:",g.round(3).to_dict("index")); print("        DOG:",u.round(3).to_dict("index"))
