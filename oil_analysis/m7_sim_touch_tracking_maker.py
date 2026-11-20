# Touch-tracking maker: always quotes the underdog side at the current touch (i.e. rests a bid on the favorite
# at the best bid, re-quoting as the touch moves). At each new price level it joins the BACK of the queue behind
# Q contracts; it is filled only by underdog-taker volume at that level beyond Q, at most N contracts per level.
import pandas as pd, numpy as np, sys
ser=sys.argv[1]; N=float(sys.argv[2]); Q=float(sys.argv[3]); M0,M1=int(sys.argv[4]),int(sys.argv[5]); PMAX=float(sys.argv[6]) if len(sys.argv)>6 else 0.5; HOURS=sys.argv[7] if len(sys.argv)>7 else ""
T=pd.read_pickle(f"data/{ser}_T.pkl").sort_values(["t","ts"]).reset_index(drop=True)
T["min"]=(T.sec//60).astype(int)+1
T=T[(T["min"]>=M0)&(T["min"]<=M1)&(T.tpx<min(PMAX,0.5))]          # taker bought the underdog (priced below PMAX)
if HOURS:
    hs=set(int(x) for x in HOURS.split(",")); T=T[T.open.dt.tz_convert("America/New_York").dt.hour.isin(hs)]
# runs of consecutive trades at the same level (same market, same taker side, same price)
key=T.t+"|"+T.taker+"|"+T.tpx.round(4).astype(str)
T["run"]=(key!=key.shift()).cumsum()
T["cum"]=T.groupby("run").n.cumsum(); T["cum0"]=T.cum-T.n
T["fill"]=np.clip(T.cum-Q,0,None)-np.clip(T.cum0-Q,0,None)          # this trade's volume beyond the queue
T["filled_before"]=T.groupby("run").fill.cumsum()-T.fill
T["fill"]=np.clip(np.minimum(T.fill,N-T.filled_before),0,None)
T["pnl"]=T.fill*(-T.traw)
g=T.groupby("t").agg(pnl=("pnl","sum"),fill=("fill","sum"),open=("open","first"))
tt=lambda s: s.pnl.mean()/s.pnl.std()*np.sqrt(len(s))
h=g.open.sort_values().iloc[len(g)//2]
print(f"{ser} touch-maker N={N:.0f}/level Q={Q:.0f} min{M0}-{M1} dog<{PMAX} hrs[{HOURS or 'all'}]: contracts={g.fill.sum():.0f} c/contract={100*g.pnl.sum()/g.fill.sum():+.2f} $={g.pnl.sum():+.0f} $/window={g.pnl.mean():+.2f} t={tt(g):+.2f} | 1st half {100*g[g.open<h].pnl.sum()/g[g.open<h].fill.sum():+.2f}c (t={tt(g[g.open<h]):+.2f}) 2nd half {100*g[g.open>=h].pnl.sum()/g[g.open>=h].fill.sum():+.2f}c (t={tt(g[g.open>=h]):+.2f})")
