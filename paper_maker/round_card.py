#!/usr/bin/env python3
"""Compact card: last 15-minute round + all rounds combined, per bot."""
import json, os, sys
from collections import defaultdict


def rows(p):
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else []


def money(v):
    return f"{'+' if v >= 0 else '−'}${abs(v):,.2f}"


def card(log_dirs):
    out = ["| | Put in | Contracts | Won / Lost | P&L |", "|---|---|---|---|---|"]
    for d in log_dirs:
        fills, wins = rows(os.path.join(d, "fills.jsonl")), rows(os.path.join(d, "windows.jsonl"))
        if not wins:
            continue
        cost, qty = defaultdict(float), defaultdict(float)
        for f in fills:
            cost[f["ticker"]] += f["qty"] * f["price"]; qty[f["ticker"]] += f["qty"]
        name = os.path.basename(os.path.normpath(d)).capitalize()
        w = wins[-1]; t = w["ticker"].split("-")[1][-4:]
        h = int(t[:2]); ampm = f"{(h - 1) % 12 + 1}:{t[2:]} {'pm' if h >= 12 else 'am'}"
        out.append(f"| **{name}** last round ({ampm}, {w['result'].upper()}) | ${cost[w['ticker']]:,.2f} | {qty[w['ticker']]:,.0f} | "
                   f"{'1 / 0' if w['pnl'] > 0 else '0 / 1' if w['pnl'] < 0 else '0 / 0'} | {'🟩' if w['pnl'] > 0 else '🟥' if w['pnl'] < 0 else '⬜'} {money(w['pnl'])} |")
        tot = sum(x["pnl"] for x in wins)
        out.append(f"| **{name}** all {len(wins)} rounds | ${sum(cost[x['ticker']] for x in wins):,.2f} | "
                   f"{sum(qty[x['ticker']] for x in wins):,.0f} | {sum(x['pnl'] > 0 for x in wins)} / {sum(x['pnl'] < 0 for x in wins)} | "
                   f"**{money(tot)}** |")
    return "\n".join(out)


if __name__ == "__main__":
    print(card(sys.argv[1:] or ["logs/brent", "logs/wti"]))
