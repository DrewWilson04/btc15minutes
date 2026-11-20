# Kalshi KXETH15M: minute-level pattern scan

Data: 6,517 settled KXETH15M markets (2026-09-12 to 2026-11-20, about 69 days), with
1-minute Kalshi candles (yes bid/ask/last/volume) and Coinbase ETH-USD 1-minute spot.
Run from this folder: `mkdir data`, then the scripts 01 to 04, then a1 to a5. The data is
about 70 MB and is not committed.

EV figures are per $1 contract, after the 7% quadratic taker fee, and assume you buy at the ask.

## Results
1. Overall YES rate is 49.4%. ETH fell from about $2,520 to $1,640 over the sample.
2. **Outcomes tend to reverse from one window to the next.** P(up) is 46.5% after two up
   windows and 53.1% after two down windows (n of about 1,600 each, roughly 3.7 sigma).
   The minute-1 price already moves about two-thirds of the way toward this. Fading the
   streak at the minute-1 ask: EV is -0.002 (t = -0.2). No edge left to trade.
3. **The market is well calibrated at every minute.** Realized win rates match prices to
   within about 1 cent in every bucket. Underdogs are overpriced by 0.5 to 3 cents, a mild
   longshot bias. Mid-to-late in the window, buying an underdog priced 0.20 to 0.50 loses
   3 to 6 cents.
4. **Spot moves add nothing beyond the Kalshi price.** In a logistic regression, Coinbase's
   last 1-minute and 3-minute moves and the distance to the strike are all insignificant
   (|t| < 1.7) once the market's price is included, at minutes 3, 5, 8, 10, 12 and 13.
5. **The late-favorite rule (the bot's run C) breaks even at best on ETH.** Buying 0.93+ in
   minutes 13 to 14 gives 2,297W/70L (97.0%) at an average price of 0.9705. EV is -0.002
   (t = -0.7). Thresholds from 0.85 to 0.97 all come out between -0.003 and 0.000. The
   "travelled range" and "adverse move" filters do not separate winners from losers.
6. **Volatility and volume have clear daily patterns.** 15-minute moves are about twice
   as large from 9 to 11 ET (17 to 20 bps median) as overnight (about 9 to 10 bps).
   Weekends are 7.4 bps and weekdays 12.8 bps. Volume is lowest from 4 to 8 ET.
7. Windows starting on the hour were up only 42% of the time in the second half of the
   sample but 50% in the first half. This is not stable. It is probably noise plus the
   downtrend.

Bottom line: no tradable after-fee edge appears at 1-minute resolution. Anything left is
likely sub-minute (the RTI settlement average versus live venue prices) or comes from
earning the spread as a maker rather than paying it as a taker.
