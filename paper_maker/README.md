# Paper maker: Kalshi oil 15-minute

Paper-trades the strategy in `../oil_analysis/FINDINGS.md` on live data. **It never places an order.** It only reads public Kalshi endpoints, so it needs no API key.

What it does, every 1.5 s:
1. Finds the open window of the series (default KXBRENT15M).
2. In minutes 1–12, picks the favourite (mid ≥ 0.50) and keeps one *virtual* buy order on it at the current best bid. It re-quotes whenever the best bid moves.
3. On placing that order, records how much was already resting at that price (the queue ahead of us).
4. Reads live trades. A taker buying the underdog at our level, or sweeping through it, first eats the queue ahead and then fills us, up to `--per-level` contracts per price.
5. Holds every fill to settlement, then books P&L (maker fee is 0 on these series).

```
python3 paper_maker.py                                   # Brent, uncapped (the backtest's best total)
python3 paper_maker.py --window-cap 75 --day-stop 75 --count-open-risk   # hard ~$150/day loss ceiling
python3 paper_maker.py --series KXWTI15M --max-minute 9 --max-dog 0.40 --log-dir logs/wti
```

Logs go to `logs/<name>/`: `fills.jsonl` (every simulated fill), `windows.jsonl` (settled P&L per window),
`events.jsonl` (quotes and cancels) and `state.json` (running totals; survives restarts).

Limits of the simulation:
* It assumes nobody behind us cancels ahead of us, and that our order doesn't change anyone's behaviour.
* It polls every 1.5 s, so in that gap it can be filled at a just-stale price. That is realistic for a REST bot.
* The book is read through REST snapshots, not the websocket. A real bot should use the authenticated websocket.

## Showing results on a website (e.g. drew.cx)

`export_site.py` writes a self-contained `site/index.html` plus `site/stats.json`: totals, ¢/contract, drawdown, an equity curve, daily P&L and recent windows.
The page re-reads `stats.json` every minute. `site_loop.py` rebuilds it every 5 minutes and runs whatever publish command fits your host:

```
# your own server (bot runs elsewhere):
python3 site_loop.py --logs logs/brent logs/wti --publish-cmd 'rsync -az site/ you@drew.cx:/var/www/drew.cx/kalshi/'
# bot runs ON the web server: just write straight into the web root
python3 site_loop.py --logs logs/brent logs/wti --out /var/www/drew.cx/kalshi
# GitHub Pages repo checked out at ~/site-repo:
python3 site_loop.py --out ~/site-repo/kalshi --publish-cmd 'cd ~/site-repo && git add kalshi && git commit -qm stats && git push -q'
# Netlify:
python3 site_loop.py --publish-cmd 'netlify deploy --prod --dir site'
```
Run the bots and `site_loop.py` side by side (e.g. in `tmux` or as services).
