#!/bin/sh
# Binance USD-M perps CLUSDT (WTI) and BZUSDT (Brent): 1m klines + tick aggTrades from data.binance.vision.
mkdir -p data/binance data/binance_agg
for s in CLUSDT BZUSDT; do
  for m in 2026-07 2026-08 2026-09 2026-10; do (cd data/binance && curl -s -O "https://data.binance.vision/data/futures/um/monthly/klines/$s/1m/$s-1m-$m.zip"); done
  for d in $(seq -w 1 19); do (cd data/binance && curl -s -O "https://data.binance.vision/data/futures/um/daily/klines/$s/1m/$s-1m-2026-11-$d.zip"); done
  for d in $(seq 0 30); do day=$(date -d "2026-10-20 +$d day" +%F); (cd data/binance_agg && curl -s -O "https://data.binance.vision/data/futures/um/daily/aggTrades/$s/$s-aggTrades-$day.zip"); done
done
(cd data/binance && for f in *.zip; do unzip -o -q "$f"; done)
(cd data/binance_agg && for f in *.zip; do unzip -o -q "$f"; done)
