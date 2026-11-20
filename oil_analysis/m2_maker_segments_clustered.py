import pandas as pd, numpy as np, sys
ser=sys.argv[1]
T=pd.read_pickle(f"data/{ser}_T.pkl")
T["et"]=T.open.dt.tz_convert("America/New_York")
T["mpnl"]=-T.traw*T.n            # maker $ pnl (no maker fee on this series)
T["min"]=(T.sec//60).astype(int)+1
T["dog"]=T.tpx<0.5                 # taker bought the underdog side
def clus(s,label):
    g=s.groupby("t").agg(p=("mpnl","sum"),c=("n","sum"))
    t=g.p.mean()/g.p.std()*np.sqrt(len(g)) if len(g)>2 else np.nan
    return dict(seg=label,windows=len(g),contracts=int(g.c.sum()),maker_c_per_contract=round(100*g.p.sum()/g.c.sum(),2),dollars=round(g.p.sum()),win_t=round(t,2),pos_windows=round((g.p>0).mean(),3))
rows=[clus(T,"ALL"),clus(T[T.dog],"taker bought underdog"),clus(T[~T.dog],"taker bought favorite")]
for lo,hi in [(1,3),(4,6),(7,9),(10,12),(13,14),(15,15)]:
    s=T[(T["min"]>=lo)&(T["min"]<=hi)]
    rows.append(clus(s[s.dog],f"min {lo}-{hi} underdog")); rows.append(clus(s[~s.dog],f"min {lo}-{hi} favorite"))
for lo,hi in [(0,.1),(.1,.2),(.2,.3),(.3,.4),(.4,.5)]:
    rows.append(clus(T[(T.tpx>lo)&(T.tpx<=hi)&(T["min"]<=12)],f"dog px {lo}-{hi} (min1-12)"))
print(pd.DataFrame(rows).to_string(index=False))
# stability: weekly, underdog flow minutes 1-12
S=T[T.dog&(T["min"]<=12)].copy(); S["wk"]=S.open.dt.tz_convert("America/New_York").dt.to_period("W").astype(str)
print("\nweekly (taker-bought-underdog, min 1-12): maker cents/contract and $")
wk=S.groupby("wk").apply(lambda s:pd.Series({"windows":s.t.nunique(),"contracts":int(s.n.sum()),"c_per":round(100*s.mpnl.sum()/s.n.sum(),2),"$":round(s.mpnl.sum())}))
print(wk.to_string())
print("\nby ET hour (underdog flow, min 1-12): c/contract")
print(S.groupby(S.et.dt.hour).apply(lambda s:round(100*s.mpnl.sum()/s.n.sum(),2)).to_dict())
