# Kalshi oil: WTI 15m, Brent 15m, WTI hourly (pattern hunt)

Markets studied: **KXWTI15M**, **KXBRENT15M**, **KXWTIH** (hourly WTI ladder).

## Data

| Source | Coverage |
|---|---|
| KXWTI15M | 7,896 settled windows (Jul 31 to Nov 20 2026) with outcomes. 1-min candles for 5,414 windows (Sep 13 to Nov 20). Every trade (price, size, taker side) for 1,923 windows, Oct 21 to Nov 20: 5.7M trades, 208M contracts. About 310 windows are missing because Kalshi throttled the download |
| KXBRENT15M | 2,152 settled windows (Oct 21 to Nov 20, the series' whole life). 1-min candles plus every trade (1.0M trades, 18.2M contracts) |
| KXWTIH | 1,128 hourly events with 1-min quotes on the ±$0.60 strikes (13.5k strike-markets), Sep 13 to Nov 20 |
| Underlying | Kalshi settles on Pyth (PYTHOIL / BRENT index), whose history API now needs a key. Binance **CLUSDT / BZUSDT** perps were used instead (1-min klines plus tick aggTrades). Their 15-min changes correlate **0.99** with the Pyth settlement prints, peaking at zero lag |
| Live order books | ~115 snapshots over 30 min, 2 windows each (Nov 20): median best-bid depth on the favourite is WTI 232 and Brent 141 contracts. Median spread is 1¢ (WTI) and 2–3¢ (Brent) |

Fees: all three series are fee type `quadratic` per the API, not `quadratic_with_maker_fees`.
**Takers pay 0.07·p·(1−p) and resting (maker) orders pay nothing.**

## How these markets work

* **Ties resolve YES.** 15m YES pays if the close is at least the open. Ties happen in 2.7% of WTI windows and 2.5% of Brent. Fair YES is about 0.51, and **the market already prices it**. WTI's mean minute-1 mid is 0.5068 against a realized 0.5068; Brent's is 0.5065 against 0.5084.
* The 15m strike equals the previous window's settle in 99.9% of cases, so the series chains together.
* **The hourly ladder and the 15m window ending on the hour settle on the identical print** (1,128 of 1,128).
* Kalshi lags the perps by about a minute. Minute-ahead Kalshi mid changes follow the current Binance move (t = 4.1 WTI, 6.7 Brent).

## Things that do NOT make money (taking liquidity)

| Idea | Result |
|---|---|
| Calibration (any price, any minute) | Accurate to about 1¢. Cheap sides are overpriced, and buying underdogs loses 2–4¢ (WTI) and 2–8¢ (Brent) after fees |
| Binance-informed fair value vs the Kalshi ask, trained on one half and tested on the other | WTI test half −4.5 to +0.7¢ across thresholds (|t| ≤ 0.8). Brent test half −1.8 to −8.1¢. The information is real but smaller than spread plus fee |
| Streaks / mean reversion | WTI: after a down window P(up) is 0.527 while the price says 0.506. That 2¢ gap is less than taker cost. Brent: none |
| Time slots (EIA Wed 10:30, API Tue 16:30, CME open/settle, Sunday open, the 17:00 halt) | Too few observations, or no gap the market misses. Gaps per slot are within multiple-testing noise |
| Brent follows WTI (thin market lags the liquid one) | WTI's price does add information about Brent (t up to 4.6), but trading it loses out of sample |
| Hourly ladder arbitrage (monotonicity) | 2 violations in 523k minute-snapshots |
| 15m vs hourly arbitrage (same settlement print) | Positive after fees in 0.1–0.2% of snapshots, about 17 windows in 2 months. Not repeatable |
| Hourly pick-offs against fair value | Unstable: train +1.8¢ (t = 0.4), test +6.0¢ (t = 2.7) at a 10¢ threshold. Realized edge is far below predicted. Spreads are 6–8¢ |

## The one pattern that repeats: the maker side against underdog buyers

Takers pay the spread **and** overpay for underdogs. With no maker fee, the resting side collects both.
This is a market-making edge for a bot. It is **not** a trade you can take with a click.

### Brent, all trades Oct 21 to Nov 20 (t-stats clustered by window)

| Flow | Maker ¢/contract | Window-clustered t | Positive windows |
|---|---|---|---|
| All flow | **+1.29** | 7.6 | 61% |
| Taker bought the underdog | **+2.22** | 4.5 | 73% |
| Taker bought the favourite | +0.50 | 1.0 | 30% |
| Underdog flow, minutes 1–3 | **+3.86** | 3.0 | |
| Underdog flow, priced 0.10–0.20 | +3.58 | 3.5 | |

Every week was positive (underdog flow, minutes 1–12): +4.4, +1.2, +3.1, +2.7, +2.6 ¢/contract.
This is the only finding that held in every week of the series' life.

Exploratory, and true for Brent only: the edge was largest after calm hours (lowest prior-hour volatility quartile +5.8 ¢, t = 5.0) and after busy hours (highest prior-hour volume quartile +5.0 ¢, t = 4.7). WTI shows neither pattern.

### WTI: real in November, failed the holdout

| WTI underdog flow, minutes 1–12 | Maker ¢/contract |
|---|---|
| Week of Oct 19 | −1.87 |
| Week of Oct 26 | +0.04 |
| Week of Nov 2 | +2.27 |
| Week of Nov 9 | +1.32 |
| Week of Nov 16 | +1.27 |

The WTI rule (minutes 1–9, underdog < 0.40) was chosen on Oct 30 to Nov 20, where it made +2.9 ¢ (t = 3.3).
On the **465 untouched windows of Oct 21–30 it lost −1.2 ¢** (tape) and −1.5 ¢ in the queue simulation, about −$390/day with 40% of days positive.
The "late minutes are bad for makers" sub-pattern also flipped in the holdout (+0.9 ¢).
**Treat WTI as unproven.** It is far more liquid and competitive: maker P&L on all flow is only +0.3 ¢.

The London-morning skip (03:00–08:59 ET) looked good in-sample on both oils but made Oct 21–30 **worse** for both. Don't use it.

### It only works if your quote stays at the best price

* **A stale resting order loses.** Leaving a bid at the previous minute's price fills mainly when the market moves through it: −1.2 to −5.6 ¢/contract (Brent, queue 0–300).
* **A maker that tracks the best bid wins on Brent.** It always quotes at the current best bid, joins the back of the queue behind Q contracts, and takes up to N per price level.
  * Brent, Q = 150 (median live depth 141), N = 50, minutes 1–12: **+2.40 ¢/contract, t = 3.1**. That is ≈ +$120/day over 27 days, 70% of days positive, worst day −$340, max drawdown −$340. Q from 0 to 600 gives +2.0 to +3.3 ¢.
  * But by period: Oct 21–30 **+1.0 ¢ (t = 0.6, ≈ +$40/day)**, against Oct 31 to Nov 20 +2.8 ¢ (t = 3.4, ≈ +$155/day). The edge is regime-dependent.
* **Pulling quotes after Binance moves barely matters** when tested causally: only moves already visible 0.25–1 s before the fill count. Brent kept fills go from +2.57 to +2.5–2.9 ¢, and WTI underdog flow is unchanged.
  The losses are not snipes you can dodge. They are the outcome moving after the fill. A Binance move in the *same* minute does separate fills (−6 to −13 ¢ when oil runs > $0.05 toward the underdog), but you can't know it before the fill.
* Queue position (underdog flow): front-of-queue +2.2 ¢, same-level +1.6 ¢ and swept levels +4.0 ¢ on Brent. On WTI +1.2, +1.4 and +2.0 ¢.

## What I would actually do

1. Pilot **Brent 15m only**, at small size: ≤ 50 contracts per level and ≤ 300 per window.
2. Each window, minutes 1–12. The favourite is the side with mid ≥ 0.50. **Rest a buy on the favourite at the current best bid**, which means offering the underdog. Cancel and replace on every best-bid change. Never quote the favourite's offer side.
3. Hold fills to settlement.
4. Log every fill and compare it with the `m2`/`m7` numbers. Stop if two weeks of real fills are not positive. One month of tape cannot rule out that this was a November effect.
5. Leave WTI until a new month of tape shows the edge again (re-run `05` → `m1` → `m2` → `m7`).

## Caveats

* Short history: one month for Brent (the series' whole life) and three weeks of WTI tape plus a 10-day holdout.
* The simulation assumes you can always join the best bid instantly, and that your presence doesn't change other makers or takers.
* Fee policy can change. Check that the series' `fee_type` is still `quadratic`.
* $/day figures are simulations, not a promise.
* The hourly ladder was not tested as a maker (no tick data pulled). It is thin, about 3M contracts a month against 240M for WTI 15m, and its 6–8 ¢ spreads make taking it a loser.
* This needs order placement, which the current bot in this repo does not have by design.

## Files

Run everything from this folder (`mkdir data` first). `data/` is not committed: about 1.5 GB, re-downloadable.

| Step | Script |
|---|---|
| Market lists | `01_list_markets_live.py SERIES`, `02_list_markets_historical.py SERIES` |
| Kalshi 1-min candles | `03_candles_15m.py SERIES`, `04_candles_hourly_ladder.py 0.6` (needs 07 and 08 first) |
| Kalshi tick trades | `SHARD=i/3 START=2026-10-21 05_trades_15m.py SERIES` |
| Holdout | `m9_holdout_wti.py` (WTI rule on windows before Oct 30 23:45 UTC) |
| Live order books | `06_orderbook_poll.py` |
| Build | `07_build_windows.py`, `08_build_hourly_markets.py`, `09_binance_download.sh`, `10_build_15m_panel.py SERIES CLUSDT|BZUSDT`, `11_build_hourly_panel.py` |
| Taker tests | `a1` calibration and tie rule · `a2` Binance lag (also writes the panel) · `a3` lag strategy out of sample · `a4` streaks and time slots · `a5` WTI vs Brent |
| Hourly | `h1` calibration · `h2` ladder and 15m-vs-hourly arbitrage · `h3` fair-value pick-off |
| Maker | `m1` maker vs taker tape (writes `*_T.pkl`) · `m2` clustered segments and weekly · `m3` vs Binance move · `m4` causal quote-pull · `m5` queue position · `m6` stale-quote simulation · `m7` touch-tracking simulation `SERIES N Q M0 M1 PMAX [HOURS]` · `m8` daily P&L and drawdown |
