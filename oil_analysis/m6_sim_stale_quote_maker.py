# Single small maker: each minute m (1..MAXM), rest a bid of N contracts on the FAVORITE side at the
# prior minute's best bid; filled only after queue-ahead Q is consumed by underdog-taker flow at our level or deeper.
import pandas as pd, numpy as np, sys
sys.path.insert(0,"."); from binload import load
ser,sym=sys.argv[1],sys.argv[2]; N=float(sys.argv[3]); Q=float(sys.argv[4]); MAXM=int(sys.argv[5]) if len(sys.argv)>5 else 12
CUT=float(sys.argv[6]) if len(sys.argv)>6 else 99.0   # cancel if Binance moves > CUT toward underdog during the minute
T=pd.read_pickle(f"data/{ser}_T.pkl"); r=pd.read_pickle(f"data/{ser}_r.pkl"); w=pd.read_pickle(f"data/{ser}_w.pkl")
B=load(sym).close
T["min"]=(T.sec//60).astype(int)+1
r=r.merge(w[["t","open","yes"]],on="t")
r=r[r.t.isin(set(T.t))]
# quote at end of minute m-1 (k=m-1); for m=1 skip (book empty at open)
q=r[["t","k","bid","ask","open","yes"]].copy(); q["m"]=q.k+1
q=q[(q.m>=2)&(q.m<=MAXM)&q.bid.between(0.01,0.99)&q.ask.between(0.01,0.99)]
q["mid"]=(q.bid+q.ask)/2
q["fav_yes"]=q.mid>=0.5
q["pf"]=np.where(q.fav_yes,q.bid,1-q.ask)          # our bid on the favorite: YES bid, or NO bid = 1-YES ask
q["win"]=np.where(q.fav_yes,q.yes,1-q.yes)
# binance move during minute m toward the underdog
st=q.open+pd.to_timedelta(q.m-1,unit="m"); q["bm"]=(st+pd.Timedelta(minutes=1)).map(B)-st.map(B)
q["mv_dog"]=np.where(q.fav_yes,-q.bm,q.bm)
# underdog-taker volume in minute m at price >= 1-pf
T["dog_side_yes"]=T.taker=="yes"
agg=[]
Tm=T.set_index(["t","min"]).sort_index()
vols=[]
for t,m,fy,pf in zip(q.t,q.m,q.fav_yes,q.pf):
    try: s=Tm.loc[(t,m)]
    except KeyError: vols.append(0.0); continue
    dogtaker=(s.taker=="no") if fy else (s.taker=="yes")
    v=s.n[dogtaker & (s.tpx>=1-pf-1e-9)].sum()
    vols.append(float(v))
q["V"]=vols
q["fill"]=np.clip(q.V-Q,0,N)
q.loc[q.mv_dog>CUT,"fill"]=0.0
q["pnl"]=q.fill*(q.win-q.pf)
g=q.groupby("t").agg(pnl=("pnl","sum"),fill=("fill","sum"),open=("open","first"))
f=g[g.fill>0]
print(f"{ser} N={N} Q={Q} minutes 2-{MAXM} cancel>{CUT}: windows={len(g)} filled_windows={len(f)} contracts={g.fill.sum():.0f} "
      f"c/contract={100*g.pnl.sum()/max(g.fill.sum(),1):+.2f}  $total={g.pnl.sum():+.0f}  $/window={g.pnl.mean():+.2f}  t={g.pnl.mean()/g.pnl.std()*np.sqrt(len(g)):+.2f}")
h=g.open.sort_values().iloc[len(g)//2]
for nm,s in [("1st half",g[g.open<h]),("2nd half",g[g.open>=h])]:
    print(f"   {nm}: c/contract={100*s.pnl.sum()/max(s.fill.sum(),1):+.2f} $={s.pnl.sum():+.0f} t={s.pnl.mean()/s.pnl.std()*np.sqrt(len(s)):+.2f}")
