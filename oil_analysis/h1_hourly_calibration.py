import pandas as pd, numpy as np
r=pd.read_pickle("data/KXWTIH_r.pkl")
feeT=lambda p: 0.07*p*(1-p)
r=r[r.bid.notna()&r.ask.notna()]
r["mid"]=(r.bid+r.ask)/2; r["spr"]=r.ask-r.bid
q=r[(r.ask<1)&(r.bid>0)]
print("two-sided quotes share:",len(q)/len(r))
print("median spread by minutes-before-close:",q.groupby(pd.cut(q.mb,[-1,2,5,10,15,30,60,90,120])).spr.median().round(3).to_dict())
print("\n== calibration: buy YES at ask / buy NO at (1-bid), by price paid, by time-before-close")
for lo,hi in [(60,120),(30,59),(15,29),(5,14),(1,4)]:
    s=q[(q.mb>=lo)&(q.mb<=hi)]
    A=pd.DataFrame({"px":np.r_[s.ask.values,1-s.bid.values],"win":np.r_[s.yes.values,1-s.yes.values],"ev":np.r_[s.ev.values,s.ev.values]})
    g=A.groupby(pd.cut(A.px,[0,.03,.06,.1,.2,.35,.5,.65,.8,.9,.94,.97,1]),observed=True).agg(n=("win","size"),evs=("ev","nunique"),px=("px","mean"),win=("win","mean"))
    g["net"]=g.win-g.px-feeT(g.px)
    print(f"--- {lo}-{hi} min before close"); print(g.round(4).to_string())
