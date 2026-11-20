import pandas as pd, numpy as np, sys
ser=sys.argv[1]
T=pd.read_pickle(f"data/{ser}_T.pkl").sort_values(["t","ts"]).reset_index(drop=True)
T["min"]=(T.sec//60).astype(int)+1; T["dog"]=T.tpx<0.5; T["mp"]=-T.traw*T.n
T["prev_same"]=T.groupby(["t","taker"]).tpx.shift(1)
T["gap_s"]=(T.ts-T.groupby(["t","taker"]).ts.shift(1)).dt.total_seconds()
T["cls"]=np.select([T.prev_same.isna(),T.tpx<T.prev_same-1e-9,(T.tpx-T.prev_same).abs()<=1e-9],["first","new better level (front of queue)","same level"],"swept into worse level")
f=lambda s: pd.Series({"trades":len(s),"contracts":int(s.n.sum()),"share":0,"maker_c":round(100*s.mp.sum()/s.n.sum(),2),
    "t":round((lambda g: g.mean()/g.std()*np.sqrt(len(g)))(s.groupby("t").mp.sum()),2)})
for nm,S in [("underdog flow min1-12",T[T.dog&(T["min"]<=12)]),("favorite flow min1-12",T[(~T.dog)&(T["min"]<=12)])]:
    g=S.groupby("cls").apply(f); g["share"]=(g.contracts/g.contracts.sum()).round(3)
    print("==",ser,nm); print(g.to_string())
