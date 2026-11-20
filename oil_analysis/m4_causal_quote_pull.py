# Causal quote-pull test: drop maker fills where Binance had ALREADY moved > c toward the taker's side
# in the W seconds ending L seconds before the fill (a bot watching Binance would have pulled its quote).
import pandas as pd, numpy as np, glob, sys
ser,sym=sys.argv[1],sys.argv[2]
fs=sorted(glob.glob(f"data/binance_agg/{sym}-aggTrades-*.csv"))
A=pd.concat([pd.read_csv(f,usecols=["price","transact_time"]) for f in fs]).sort_values("transact_time")
bt=A.transact_time.values.astype(np.int64); bp=A.price.values
def px_at(ms):
    i=np.searchsorted(bt,ms,side="right")-1
    out=np.where(i>=0,bp[np.clip(i,0,None)],np.nan)
    return out
T=pd.read_pickle(f"data/{ser}_T.pkl")
T=T[(T.ts>=pd.Timestamp(bt[0],unit="ms",tz="UTC"))&(T.ts<=pd.Timestamp(bt[-1],unit="ms",tz="UTC"))].copy()
T["ms"]=T.ts.astype("int64")//10**6 if T.ts.dtype!="int64" else T.ts
T["ms"]=(T.ts - pd.Timestamp("1970-01-01",tz="UTC"))//pd.Timedelta(milliseconds=1)
T["min"]=(T.sec//60).astype(int)+1; T["dog"]=T.tpx<0.5; T["mp"]=-T.traw*T.n
sgn=np.where(T.taker=="yes",1.0,-1.0)
print(ser,"trades in range",len(T),"windows",T.t.nunique())
base=lambda s: 100*s.mp.sum()/s.n.sum()
def win_t(s):
    g=s.groupby("t").mp.sum(); return g.mean()/g.std()*np.sqrt(len(g))
for seg,S in [("underdog flow min1-12",T[T.dog&(T["min"]<=12)]),("all flow min1-14",T[T["min"]<=14])]:
    print(f"\n== {seg}: baseline maker c/contract {base(S):+.2f} (t={win_t(S):+.2f}) contracts {S.n.sum():.0f}")
    for L in [0.25,1.0]:
        for W in [2,5,15,30]:
            mv=(px_at(S.ms.values-int(L*1000))-px_at(S.ms.values-int((L+W)*1000)))*sgn[S.index.map(T.index.get_loc)] if False else None
            p1=px_at(S.ms.values-int(L*1000)); p0=px_at(S.ms.values-int((L+W)*1000))
            sg=np.where(S.taker.values=="yes",1.0,-1.0)
            mvt=(p1-p0)*sg
            for c in [0.02,0.03,0.05]:
                keep=~(mvt>c)
                K=S[keep]; X=S[~keep]
                print(f"  latency {L:>4}s lookback {W:>2}s pull if >${c:.2f}: kept {K.n.sum()/S.n.sum():5.1%} of contracts -> kept c/contract {base(K):+.2f} (t={win_t(K):+.2f}) | pulled fills would have made {base(X):+.2f}")
