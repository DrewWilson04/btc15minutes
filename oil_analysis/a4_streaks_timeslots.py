import pandas as pd, numpy as np, sys
ser=sys.argv[1]
w=pd.read_pickle(f"data/{ser}_w.pkl").sort_values("open").reset_index(drop=True)
w["et"]=w.open.dt.tz_convert("America/New_York")
try:
    r=pd.read_pickle(f"data/{ser}_r.pkl"); m1=r[r.k==1].set_index("t"); w["mid1"]=w.t.map((m1.bid+m1.ask)/2); w["ask1"]=w.t.map(m1.ask); w["bid1"]=w.t.map(m1.bid)
except Exception as e: print(e)
feeT=lambda p: 0.07*p*(1-p)
contig=w.open.diff()==pd.Timedelta(minutes=15)
w["p1"]=w.yes.shift(1).where(contig); c2=contig&contig.shift(1,fill_value=False); w["p2"]=w.yes.shift(2).where(c2)
w["pchg"]=w.chg.shift(1).where(contig)
print("== streaks (all windows)", len(w))
for lab,m in [("prev Y",w.p1==1),("prev N",w.p1==0),("YY",(w.p1==1)&(w.p2==1)),("NN",(w.p1==0)&(w.p2==0))]:
    s=w[m]; print(f"  {lab:6s} n={len(s):5d} P(yes)={s.yes.mean():.3f}  mid1={s.mid1.mean():.3f}  se={np.sqrt(.25/len(s)):.3f}")
q=pd.qcut(w.pchg.rank(method="first"),5,labels=False)
print(w.groupby(q).agg(n=("yes","size"),prevchg=("pchg","mean"),yes=("yes","mean"),mid1=("mid1","mean")).round(3).to_string())
print("autocorr 15m change:", w.chg.autocorr(1).round(4))
# halt hour / session transitions
w["hm"]=w.et.dt.strftime("%H:%M")
g=w.groupby("hm").agg(n=("yes","size"),yes=("yes","mean"),tie=("chg",lambda s:(s==0).mean()),absmv=("chg",lambda s:s.abs().mean()),mid1=("mid1","mean"))
g["gap"]=g.yes-g.mid1
print("\n== by window start (ET) -- top |yes-mid1| gaps"); print(g.reindex(g.gap.abs().sort_values(ascending=False).index).head(12).round(3).to_string())
print("\n== halt/thin hours detail"); print(g.loc[[x for x in g.index if x[:2] in ("16","17","18")]].round(3).to_string())
# weekday x hour: Wed 10:30 (EIA), Tue 16:30 (API)
w["dow"]=w.et.dt.dayofweek
for lab,m in [("Wed 10:30 EIA",(w.dow==2)&(w.hm=="10:30")),("Wed 10:15",(w.dow==2)&(w.hm=="10:15")),("Tue 16:30 API",(w.dow==1)&(w.hm=="16:30")),("09:00 CME open",w.hm=="09:00"),("14:30 settle",w.hm=="14:30"),("14:15",w.hm=="14:15"),("Sun 18:00 open",(w.dow==6)&(w.hm=="18:00"))]:
    s=w[m]; print(f"{lab:16s} n={len(s):4d} yes={s.yes.mean():.3f} mean|chg|={s.chg.abs().mean():.3f} tie={(s.chg==0).mean():.3f} mid1={s.mid1.mean():.3f}")
print("overall mean|chg|",w.chg.abs().mean().round(3))
