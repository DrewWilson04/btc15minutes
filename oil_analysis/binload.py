import pandas as pd, glob
def load(sym):
    fs=sorted(glob.glob(f"data/binance/{sym}-1m-*.csv"))
    d=pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("open_time").sort_values("open_time")
    d["t"]=pd.to_datetime(d.open_time,unit="ms",utc=True)+pd.Timedelta(minutes=1)  # timestamp = candle END (price at t)
    return d.set_index("t")[["open","high","low","close","volume","count","taker_buy_volume"]]
