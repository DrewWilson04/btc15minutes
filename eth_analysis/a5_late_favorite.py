import pandas as pd, numpy as np
w=pd.read_parquet("data/w.parquet"); r=pd.read_parquet("data/r.parquet")
w=w.sort_values("open").reset_index(drop=True)
w["dt"]=pd.to_datetime(w.open,unit="s",utc=True).dt.tz_convert("America/New_York")
piv=lambda c: r.pivot(index="ticker",columns="k",values=c).reindex(w.ticker)
B,A=piv("bid"),piv("ask")
fee=lambda p: np.ceil(0.07*p*(1-p)*20*100)/100/20   # 20-contract-ish order rounding
S=w[[f"s{k}" for k in range(0,13)]].values
up=(S.max(1)-w.strike).clip(lower=0); dn=(w.strike-S.min(1)).clip(lower=0)
w["range_bps"]=(up+dn)/w.strike*1e4; w["up"]=up/w.strike*1e4; w["dn"]=dn/w.strike*1e4
def fav_sim(thr, ks=(13,14), cap=0.99):
    rows=[]
    for i in range(len(w)):
        for k in ks:
            a,b=A.iat[i,k-1],B.iat[i,k-1]
            if a>=thr and a<=cap: rows.append((i,"Y",a,w.yes.iat[i]));break
            if 1-b>=thr and 1-b<=cap: rows.append((i,"N",1-b,1-w.yes.iat[i]));break
    d=pd.DataFrame(rows,columns=["i","side","px","win"]); d["pnl"]=d.win-d.px-fee(d.px); return d
for thr in [.85,.90,.93,.95,.97]:
    d=fav_sim(thr); L=(d.win==0).sum()
    print(f"thr {thr}: n={len(d)} W/L={d.win.sum()}/{L} winrate={d.win.mean():.4f} avgpx={d.px.mean():.4f} EV/contract={d.pnl.mean():+.4f} t={d.pnl.mean()/d.pnl.std()*np.sqrt(len(d)):.2f}")
d=fav_sim(.93); d=d.join(w[["range_bps","up","dn","dt"]],on="i")
d["adverse"]=np.where(d.side=="Y",d.dn,d.up)
print(d.groupby(pd.qcut(d.range_bps,5),observed=True).agg(n=("win","size"),win=("win","mean"),px=("px","mean"),ev=("pnl","mean")).round(4))
print(d.groupby(pd.qcut(d.adverse,[0,.5,.8,.9,1.0],duplicates="drop"),observed=True).agg(n=("win","size"),win=("win","mean"),px=("px","mean"),ev=("pnl","mean")).round(4))
print(d.groupby(d.dt.dt.hour//3*3).agg(n=("win","size"),win=("win","mean"),ev=("pnl","mean")).round(4).T)
