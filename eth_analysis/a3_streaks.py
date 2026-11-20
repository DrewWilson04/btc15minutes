import pandas as pd, numpy as np
w=pd.read_parquet("data/w.parquet"); r=pd.read_parquet("data/r.parquet")
w=w.sort_values("open").reset_index(drop=True)
contig=(w.open.diff()==900)
w["p1"]=w.yes.shift(1).where(contig); w["p2"]=w.yes.shift(2).where(contig&contig.shift(1,fill_value=False))
w["p3"]=w.yes.shift(3).where(contig&contig.shift(1,fill_value=False)&contig.shift(2,fill_value=False))
m1=r[r.k==1].set_index("ticker"); w["ask1"]=w.ticker.map(m1.ask); w["bid1"]=w.ticker.map(m1.bid)
w["mid1"]=(w.ask1+w.bid1)/2
h=len(w)//2
for name,sub in [("all",w),("1st half",w.iloc[:h]),("2nd half",w.iloc[h:])]:
    print("==",name)
    for lab,mask in [("prev Y",sub.p1==1),("prev N",sub.p1==0),("YY",(sub.p1==1)&(sub.p2==1)),("NN",(sub.p1==0)&(sub.p2==0)),
                     ("YYY",(sub.p1==1)&(sub.p2==1)&(sub.p3==1)),("NNN",(sub.p1==0)&(sub.p2==0)&(sub.p3==0))]:
        s=sub[mask]; print(f"  {lab:4s} n={len(s):4d} P(yes)={s.yes.mean():.3f}  mkt mid@min1={s.mid1.mean():.3f}  se={np.sqrt(.25/len(s)):.3f}")
# strategy: fade the streak at minute-1 ask; after YY buy NO at 1-bid1; after NN buy YES at ask1
fee=lambda p: 0.07*p*(1-p)
for name,sub in [("all",w),("1st half",w.iloc[:h]),("2nd half",w.iloc[h:])]:
    a=sub[(sub.p1==0)&(sub.p2==0)].dropna(subset=["ask1"]); pnlA=a.yes-a.ask1-fee(a.ask1)
    b=sub[(sub.p1==1)&(sub.p2==1)].dropna(subset=["bid1"]); pnlB=(1-b.yes)-(1-b.bid1)-fee(1-b.bid1)
    p=pd.concat([pnlA,pnlB]); print(name,"fade-2-streak at min1 ask: n",len(p),"EV/contract",round(p.mean(),4),"t",round(p.mean()/p.std()*np.sqrt(len(p)),2))
# fade single prev
for name,sub in [("all",w),("1st half",w.iloc[:h]),("2nd half",w.iloc[h:])]:
    a=sub[(sub.p1==0)].dropna(subset=["ask1"]); pnlA=a.yes-a.ask1-fee(a.ask1)
    b=sub[(sub.p1==1)].dropna(subset=["bid1"]); pnlB=(1-b.yes)-(1-b.bid1)-fee(1-b.bid1)
    p=pd.concat([pnlA,pnlB]); print(name,"fade-1 at min1: n",len(p),"EV",round(p.mean(),4),"t",round(p.mean()/p.std()*np.sqrt(len(p)),2))
# spread at minute 1
print("spread min1 median",(w.ask1-w.bid1).median(), "mean", (w.ask1-w.bid1).mean().round(4))
# spot-level autocorrelation of 15m returns
ret=np.log(w.final/w.strike); print("lag1 autocorr of 15m settle returns", ret.autocorr(1).round(4), "lag2",ret.autocorr(2).round(4))
