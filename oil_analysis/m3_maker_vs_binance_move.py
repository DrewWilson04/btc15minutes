import pandas as pd, numpy as np, sys
sys.path.insert(0,"."); from binload import load
ser,sym=sys.argv[1],sys.argv[2]
T=pd.read_pickle(f"data/{ser}_T.pkl"); B=load(sym).close
T["mpnl"]=-T.traw*T.n; T["min"]=(T.sec//60).astype(int)+1; T["dog"]=T.tpx<0.5
tm=T.ts.dt.floor("min")
T["bmove"]=(tm+pd.Timedelta(minutes=1)).map(B)-tm.map(B)          # binance move during the trade's minute
T["bprev"]=tm.map(B)-(tm-pd.Timedelta(minutes=1)).map(B)           # binance move in the prior minute
sgn=np.where(T.taker=="yes",1,-1)
T["mv_for_taker"]=T.bmove*sgn; T["prev_for_taker"]=T.bprev*sgn
S=T[T.dog&(T["min"]<=12)].dropna(subset=["mv_for_taker"])
f=lambda s: pd.Series({"trades":len(s),"contracts":int(s.n.sum()),"maker_c":round(100*s.mpnl.sum()/s.n.sum(),2)})
print("underdog flow min1-12: maker c/contract by Binance move DURING trade minute (in taker's favor, $):")
print(S.groupby(pd.cut(S.mv_for_taker,[-9,-.10,-.05,-.02,-.005,.005,.02,.05,.10,9])).apply(f).to_string())
print("\n... by Binance move in PRIOR minute (known before trading):")
print(S.groupby(pd.cut(S.prev_for_taker,[-9,-.10,-.05,-.02,-.005,.005,.02,.05,.10,9])).apply(f).to_string())
