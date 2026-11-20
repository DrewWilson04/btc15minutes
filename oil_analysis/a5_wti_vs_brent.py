import pandas as pd, numpy as np, statsmodels.api as sm
feeT=lambda p: 0.07*p*(1-p); lg=lambda p: np.log(p/(1-p))
P={}
for s in ["KXWTI15M","KXBRENT15M"]:
    d=pd.read_pickle(f"data/{s}_panel.pkl")[["open","k","mid","bid","ask","yes","z"]]
    P[s]=d.set_index(["open","k"])
m=P["KXBRENT15M"].join(P["KXWTI15M"],lsuffix="_b",rsuffix="_w",how="inner").reset_index()
print("joint windows",m.open.nunique(),"rows",len(m))
w1=m[m.k==15]; print("outcome agreement WTI vs Brent:",(w1.yes_b==w1.yes_w).mean().round(3))
for tgt,oth in [("b","w"),("w","b")]:
    print(f"== predict {tgt} outcome: logit(yes_{tgt}) ~ Lmid_{tgt} + Lmid_{oth}")
    for k in [2,4,6,8,10,12,13]:
        s=m[(m.k==k)&m[f"mid_{tgt}"].between(.03,.97)&m[f"mid_{oth}"].between(.03,.97)]
        X=sm.add_constant(pd.DataFrame({"own":lg(s[f"mid_{tgt}"]),"other":lg(s[f"mid_{oth}"])}))
        res=sm.Logit(s[f"yes_{tgt}"],X).fit(disp=0)
        print(f"  k={k:2d} n={len(s)} own={res.params.own:+.2f}(t={res.tvalues.own:+.1f}) other={res.params.other:+.2f}(t={res.tvalues.other:+.1f})")
# simple OOS trade: buy Brent side when WTI mid strongly disagrees with Brent mid
ts=np.sort(m.open.unique()); cut=ts[len(ts)//2]
for nm,s in [("train",m[m.open<cut]),("test",m[m.open>=cut])]:
    for gap in [0.15,0.25,0.35]:
        s2=s[(s.k>=2)&(s.k<=13)]
        Y=s2[(s2.mid_w-s2.mid_b>gap)]; N=s2[(s2.mid_b-s2.mid_w>gap)]
        a=pd.DataFrame({"open":Y.open,"k":Y.k,"pnl":Y.yes_b-Y.ask_b-feeT(Y.ask_b)})
        b=pd.DataFrame({"open":N.open,"k":N.k,"pnl":(1-N.yes_b)-(1-N.bid_b)-feeT(1-N.bid_b)})
        q=pd.concat([a,b]).sort_values(["open","k"]).groupby("open").head(1)
        if len(q)>10: print(f"[{nm}] Brent-follows-WTI gap>{gap}: trades {len(q)} EV {q.pnl.mean():+.4f} t={q.pnl.mean()/q.pnl.std()*np.sqrt(len(q)):+.2f}")
