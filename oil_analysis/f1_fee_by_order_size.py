# Per-contract taker fee by order size (per-order rounding up to the cent), and what takers in the tape actually paid.
import sys, pandas as pd, numpy as np
from fees import per_contract
P=[0.03,0.05,0.10,0.25,0.50,0.75,0.90,0.95,0.97]; C=[1,2,5,10,25,50,100,1000]
t=pd.DataFrame({f"{p:.2f}":[round(100*per_contract(c,p),3) for c in C] for p in P},index=[f"{c} contracts" for c in C])
t.loc["exact formula"]=[round(100*0.07*p*(1-p),3) for p in P]; print("cents per contract:"); print(t.to_string())
for ser in sys.argv[1:]:
    T=pd.read_pickle(f"data/{ser}_T.pkl"); T["fx"]=0.07*T.n*T.tpx*(1-T.tpx)
    O=T.groupby(["t","ts","taker"]).agg(C=("n","sum"),fx=("fx","sum"))      # an "order" = same market, timestamp, taker side
    O["fr"]=np.ceil(np.round(O.fx*100,6))/100
    O["size"]=pd.cut(O.C,[0,1,5,10,25,100,1e9],labels=["<=1","1-5","5-10","10-25","25-100",">100"])
    g=O.groupby("size",observed=True).agg(orders=("C","size"),contracts=("C","sum"),fx=("fx","sum"),fr=("fr","sum"))
    g["share"]=(g.contracts/g.contracts.sum()).round(3); g["exact_c"]=(100*g.fx/g.contracts).round(3); g["paid_c"]=(100*g.fr/g.contracts).round(3)
    print("==",ser); print(g[["orders","share","exact_c","paid_c"]].to_string())
