import pandas as pd, numpy as np, sys
ser=sys.argv[1]
import glob
T=pd.concat([pd.read_csv(f,names=["t","ts","p","n","taker"]) for f in sorted(glob.glob(f"data/{ser}_trades[0-9]*.csv"))]).drop_duplicates()
w=pd.read_pickle(f"data/{ser}_w.pkl")
T=T.merge(w[["t","open","yes"]],on="t")
T["ts"]=pd.to_datetime(T.ts,format="ISO8601"); T["sec"]=(T.ts-T.open).dt.total_seconds()
T=T[(T.sec>=0)&(T.sec<=900)]
T["p"]=T.p.astype(float); T["n"]=T.n.astype(float)
# taker's side price & outcome
ty=T.taker=="yes"
T["tpx"]=np.where(ty,T.p,1-T.p); T["twin"]=np.where(ty,T.yes,1-T.yes)
T["traw"]=T.twin-T.tpx                    # taker gross pnl/contract (maker = -traw)
fT=0.07*T.tpx*(1-T.tpx); fM=0.0175*T.tpx*(1-T.tpx)
T["taker_net"]=T.traw-fT; T["maker_net"]=-T.traw-fM; T["maker_net0"]=-T.traw
print(ser,"trades",len(T),"markets",T.t.nunique(),"contracts",T.n.sum().round(0))
wm=lambda s,c: (s[c]*s.n).sum()/s.n.sum()
def tab(g):
    return pd.DataFrame({"trades":g.size(),"contracts":g.n.sum().round(0),"taker_px":g.apply(lambda s:wm(s,"tpx")),
        "taker_gross":g.apply(lambda s:wm(s,"traw")),"maker_net(0.25x fee)":g.apply(lambda s:wm(s,"maker_net")),"maker_net(no fee)":g.apply(lambda s:wm(s,"maker_net0"))}).round(4)
print("\nALL:", tab(T.groupby(lambda i:0)).to_dict("records"))
print("\nby taker price bucket (price taker paid for its side):"); print(tab(T.groupby(pd.cut(T.tpx,[0,.05,.1,.2,.3,.4,.5,.6,.7,.8,.9,.95,1]),observed=True)).to_string())
print("\nby minute of window:"); print(tab(T.groupby((T.sec//60).astype(int)+1)).to_string())
print("\nby trade size:"); print(tab(T.groupby(pd.cut(T.n,[0,1,5,20,100,500,1e9]),observed=True)).to_string())
T.to_pickle(f"data/{ser}_T.pkl")
