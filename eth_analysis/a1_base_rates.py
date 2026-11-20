import pandas as pd, numpy as np
w=pd.read_parquet("data/w.parquet"); r=pd.read_parquet("data/r.parquet")
w["dt"]=pd.to_datetime(w.open,unit="s",utc=True).dt.tz_convert("America/New_York")
print("N",len(w),"yes rate",w.yes.mean().round(4))
# streaks
w["prev"]=w.yes.shift(1); w["prev2"]=w.yes.shift(2)
print("P(yes|prev yes)",w[w.prev==1].yes.mean().round(4),"P(yes|prev no)",w[w.prev==0].yes.mean().round(4))
print("P(yes|2 yes)",w[(w.prev==1)&(w.prev2==1)].yes.mean().round(4),"P(yes|2 no)",w[(w.prev==0)&(w.prev2==0)].yes.mean().round(4))
# prev window magnitude
w["prevret"]=(w.final-w.strike).shift(1)
q=pd.qcut(w.prevret,5); print(w.groupby(q,observed=True).yes.agg(["mean","count"]))
# hour of day ET
print(w.groupby(w.dt.dt.hour).yes.agg(["mean","count"]).T.round(3).to_string())
print(w.groupby(w.dt.dt.dayofweek).yes.agg(["mean","count"]).T.round(3))
# abs move by hour
w["absmv"]=(w.final-w.strike).abs()/w.strike*1e4
print("abs move bps by hour",w.groupby(w.dt.dt.hour).absmv.median().round(1).to_dict())
print("abs move bps by min-of-hour", w.groupby(w.dt.dt.minute).absmv.median().round(1).to_dict(), w.groupby(w.dt.dt.minute).yes.mean().round(3).to_dict())
# strike vs spot at open check
print("strike - s0 median",(w.strike-w.s0).describe().round(2).to_dict())
