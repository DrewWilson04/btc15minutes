# Re-run the taker tests under three fee regimes: exact formula (large orders), 10-contract orders (rounded), zero fee.
import pandas as pd, numpy as np, statsmodels.api as sm, sys
sys.path.insert(0,"."); from fees import per_contract
REG={"exact (big orders)":lambda p: 0.07*p*(1-p), "10-contract orders":lambda p: per_contract(10,np.asarray(p,float)), "zero fee":lambda p: 0*p}
lg=lambda p: np.log(p/(1-p)); sg=lambda x: 1/(1+np.exp(-x))
tstat=lambda x: x.mean()/x.std()*np.sqrt(len(x)) if len(x)>2 else np.nan
rows=[]
def add(test,ser,half,fee,pnl,n=None):
    rows.append(dict(test=test,series=ser,half=half,fee=fee,trades=len(pnl),EV_c=round(100*pnl.mean(),2),t=round(tstat(pnl),2)))
for ser in ["KXWTI15M","KXBRENT15M"]:
    d=pd.read_pickle(f"data/{ser}_panel.pkl").sort_values(["open","k"])
    d=d[(d.mid>.02)&(d.mid<.98)&d.ask.notna()&d.bid.notna()].copy()
    ts=d.open.sort_values().unique(); cut=ts[len(ts)//2]; tr=d[d.open<cut]; te=d[d.open>=cut]
    # 1) Binance-lag fair value, trained on 1st half, traded on 2nd half (first signal per window, edge > 2c before fees)
    F=lambda s: pd.DataFrame({"Lmid":lg(s.mid),"z":s.z,"zk":s.z*s.k/15,"Lk":lg(s.mid)*s.k/15}).assign(const=1.0)
    res=sm.Logit(tr.yes,F(tr)).fit(disp=0); s=te.copy(); s["p"]=sg(F(s)@res.params)
    for fn,fee in REG.items():
        eY=s.p-s.ask-fee(s.ask); eN=(1-s.p)-(1-s.bid)-fee(1-s.bid)
        a=s[(eY>0.02)&s.k.between(2,13)].assign(pnl=lambda x: x.yes-x.ask-fee(x.ask),side="Y")
        b=s[(eN>0.02)&s.k.between(2,13)].assign(pnl=lambda x: (1-x.yes)-(1-x.bid)-fee(1-x.bid),side="N")
        q=pd.concat([a,b]).sort_values(["open","k"]).groupby("t").head(1)
        add("Binance-lag fair value (edge>2c)",ser,"test",fn,q.pnl)
    # 2) buy the underdog / buy the favourite at the ask (all minutes 2-13), whole sample, one per window per side-bucket
    for fn,fee in REG.items():
        s=d[d.k.between(2,13)]; fy=s.mid>=.5
        fav_px=np.where(fy,s.ask,1-s.bid); fav_win=np.where(fy,s.yes,1-s.yes)
        dog_px=np.where(fy,1-s.bid,s.ask); dog_win=1-fav_win
        g=pd.DataFrame({"t":s.t,"fav":fav_win-fav_px-fee(fav_px),"dog":dog_win-dog_px-fee(dog_px)}).groupby("t").mean()
        add("buy favourite at ask (every minute)",ser,"all",fn,g.fav); add("buy underdog at ask (every minute)",ser,"all",fn,g.dog)
# 3) WTI streak: after a down window buy YES at minute-1 ask
w=pd.read_pickle("data/KXWTI15M_w2.pkl").sort_values("open").reset_index(drop=True); r=pd.read_pickle("data/KXWTI15M_r.pkl")
m1=r[r.k==1].set_index("t"); w["ask1"]=w.t.map(m1.ask)
contig=w.open.diff()==pd.Timedelta(minutes=15); w["p1"]=w.yes.shift(1).where(contig)
s=w[(w.p1==0)&w.ask1.between(.02,.98)]
for fn,fee in REG.items(): add("WTI: after a down window buy YES @min1",'KXWTI15M',"all",fn,s.yes-s.ask1-fee(s.ask1))
# 4) Brent follows WTI (gap>0.25), test half
P={}
for sr in ["KXWTI15M","KXBRENT15M"]: P[sr]=pd.read_pickle(f"data/{sr}_panel.pkl")[["open","k","mid","bid","ask","yes"]].set_index(["open","k"])
m=P["KXBRENT15M"].join(P["KXWTI15M"],lsuffix="_b",rsuffix="_w",how="inner").reset_index()
tsx=np.sort(m.open.unique()); te=m[(m.open>=tsx[len(tsx)//2])&m.k.between(2,13)]
for fn,fee in REG.items():
    Y=te[te.mid_w-te.mid_b>0.25]; N=te[te.mid_b-te.mid_w>0.25]
    q=pd.concat([pd.DataFrame({"open":Y.open,"k":Y.k,"pnl":Y.yes_b-Y.ask_b-fee(Y.ask_b)}),pd.DataFrame({"open":N.open,"k":N.k,"pnl":(1-N.yes_b)-(1-N.bid_b)-fee(1-N.bid_b)})]).sort_values(["open","k"]).groupby("open").head(1)
    add("Brent follows WTI (gap>0.25)","KXBRENT15M","test",fn,q.pnl)
# 5) hourly fair-value pick-off (edge>6c), test half
h=pd.read_pickle("data/KXWTIH_fv.pkl"); evs=np.sort(h.close.unique()); cutH=evs[len(evs)//2]; trh=h[h.close<cutH]; teh=h[h.close>=cutH].copy()
X=lambda s: pd.DataFrame({"z":s.zc,"z3":s.zc**3/10,"c":1.0}); resH=sm.Logit(trh.yes,X(trh)).fit(disp=0); teh["p"]=sg(X(teh)@resH.params)
for fn,fee in REG.items():
    rr=[]
    for px,win,pp in [(teh.ask,teh.yes,teh.p),(1-teh.bid,1-teh.yes,1-teh.p)]:
        e=pp-px-fee(px); mm=(e>0.06)&(px>0.02)&(px<0.98)
        rr.append(pd.DataFrame({"t":teh.t[mm],"mb":teh.mb[mm],"ev":teh.ev[mm],"pnl":(win-px-fee(px))[mm]}))
    q=pd.concat(rr).sort_values(["t","mb"],ascending=[True,False]).groupby("t").head(1)
    pe=q.groupby("ev").pnl.mean()
    rows.append(dict(test="Hourly fair-value pick-off (edge>6c)",series="KXWTIH",half="test",fee=fn,trades=len(q),EV_c=round(100*q.pnl.mean(),2),t=round(tstat(pe),2)))
out=pd.DataFrame(rows)
print(out.pivot_table(index=["test","series","half"],columns="fee",values=["EV_c","t"],aggfunc="first").to_string())
out.to_csv("out_fee_sens.csv",index=False)
