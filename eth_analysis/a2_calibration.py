import pandas as pd, numpy as np
w=pd.read_parquet("data/w.parquet"); r=pd.read_parquet("data/r.parquet")
d=r.merge(w[["ticker","yes","open"]],on="ticker")
fee=lambda p: np.ceil(0.07*p*(1-p)*100)/100  # per contract, single-contract rounding (worst case)
feeR=lambda p: 0.07*p*(1-p)  # large-order approx
d["mid"]=(d.bid+d.ask)/2
# Calibration: buying YES at ask, buying NO at (1-bid)
bins=[0,.05,.1,.2,.3,.4,.5,.6,.7,.8,.9,.95,.97,.99,1.001]
print("=== Calibration by ask bucket (all minutes): buy YES at ask ===")
for kk in [(1,3),(4,8),(9,12),(13,14)]:
    s=d[(d.k>=kk[0])&(d.k<=kk[1])&(d.ask>0)&(d.ask<1)]
    # treat both sides symmetrically: favorite price = max side ask
    s=s.assign(fav_yes=s.mid>=.5)
    s=s.assign(px=np.where(s.fav_yes,s.ask,1-s.bid), win=np.where(s.fav_yes,s.yes,1-s.yes))
    g=s.groupby(pd.cut(s.px,[.5,.6,.7,.8,.85,.9,.93,.95,.97,.98,.99,1.0]),observed=True).agg(n=("win","size"),px=("px","mean"),win=("win","mean"))
    g["edge"]=g.win-g.px; g["edge_net"]=g.edge-feeR(g.px)
    print("minutes",kk); print(g.round(4).to_string())
    # underdog
    s2=s.assign(px=np.where(s.fav_yes,1-s.bid,s.ask), win=np.where(s.fav_yes,1-s.yes,s.yes))
    g=s2.groupby(pd.cut(s2.px,[0,.01,.02,.03,.05,.07,.1,.15,.2,.3,.4,.5]),observed=True).agg(n=("win","size"),px=("px","mean"),win=("win","mean"))
    g["edge"]=g.win-g.px; g["edge_net"]=g.edge-feeR(g.px); print(" underdog:"); print(g.round(4).to_string())
