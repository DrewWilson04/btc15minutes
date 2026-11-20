import pandas as pd, numpy as np, sys, statsmodels.api as sm
sys.path.insert(0,"."); from binload import load
r=pd.read_pickle("data/KXWTIH_r.pkl"); r=r[r.bid.notna()&r.ask.notna()&(r.mb<=59)&(r.mb>=1)]
feeT=lambda p: 0.07*p*(1-p)
B=load("CLUSDT").close; dif=B.diff(); vol60=dif.rolling(60,min_periods=30).std()
w=pd.read_pickle("data/KXWTI15M_w.pkl"); Kq=dict(zip(w.open,w.K))   # exact Pyth at quarter-hour boundaries
r["now"]=r.close-pd.to_timedelta(r.mb,unit="m")
r["q"]=r.now.dt.floor("15min")
r["Kq"]=r.q.map(Kq); r["bq"]=r.q.map(B); r["bn"]=r.now.map(B); r["sig"]=r.now.map(vol60)
r["S"]=r.Kq+(r.bn-r.bq)
r=r.dropna(subset=["S","sig"])
r["z"]=(r.S-r.K)/(r.sig*np.sqrt(r.mb+0.5))
r["zc"]=r.z.clip(-6,6)
evs=np.sort(r.close.unique()); cut=evs[len(evs)//2]
tr=r[r.close<cut]; te=r[r.close>=cut]
X=lambda s: pd.DataFrame({"z":s.zc,"z3":s.zc**3/10,"c":1.0})
res=sm.Logit(tr.yes,X(tr)).fit(disp=0); print(res.params.round(3).to_dict())
for nm,s in [("train",tr),("test",te)]:
    s=s.copy(); s["p"]=1/(1+np.exp(-(X(s)@res.params)))
    print(f"[{nm}] model calibration (deciles):",s.groupby(pd.qcut(s.p,10,duplicates='drop')).apply(lambda g:(g.yes.mean()-g.p.mean())).round(3).values)
    for th in [0.0,0.03,0.06,0.10]:
        rows=[]
        for side,px,win,pp in [("Y",s.ask,s.yes,s.p),("N",1-s.bid,1-s.yes,1-s.p)]:
            e=pp-px-feeT(px); m=(e>th)&(px>0.02)&(px<0.98)
            rows.append(pd.DataFrame({"t":s.t[m],"ev":s.ev[m],"mb":s.mb[m],"pnl":(win-px-feeT(px))[m],"e":e[m]}))
        q=pd.concat(rows).sort_values(["t","mb"],ascending=[True,False]).groupby("t").head(1)   # first signal per strike-market
        pe=q.groupby("ev").pnl.mean()   # cluster by event
        print(f"   th={th:.2f}: trades={len(q):5d} events={len(pe):4d} EV/contract={q.pnl.mean():+.4f} (event-clustered t={pe.mean()/pe.std()*np.sqrt(len(pe)):+.2f}) pred edge={q.e.mean():.3f}")
r.to_pickle("data/KXWTIH_fv.pkl")
