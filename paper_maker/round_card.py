#!/usr/bin/env python3
"""Markdown card: per-15-minute-round results + running totals, for each bot log."""
import json, os, sys
from collections import defaultdict


def rows(p):
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else []


def card(log_dir, last=8):
    fills = rows(os.path.join(log_dir, "fills.jsonl"))
    wins = rows(os.path.join(log_dir, "windows.jsonl"))
    cost = defaultdict(float); qty = defaultdict(float)
    for f in fills:
        cost[f["ticker"]] += f["qty"] * f["price"]; qty[f["ticker"]] += f["qty"]
    name = os.path.basename(os.path.normpath(log_dir)).upper()
    out = [f"**{name}**", "", "| Round ends (ET) | Put in | Contracts | Result | P&L | Running total |", "|---|---|---|---|---|---|"]
    run = 0.0; lines = []
    for w in wins:
        run += w["pnl"]
        t = w["ticker"].split("-")[1][-4:]           # e.g. 1345
        bar = ("🟩" if w["pnl"] > 0 else "🟥" if w["pnl"] < 0 else "⬜")
        lines.append(f"| {t[:2]}:{t[2:]} | ${cost[w['ticker']]:,.2f} | {qty[w['ticker']]:,.0f} | {w['result'].upper()} | {bar} {'+' if w['pnl']>=0 else '−'}${abs(w['pnl']):,.2f} | {'+' if run>=0 else '−'}${abs(run):,.2f} |")
    out += lines[-last:]
    up = sum(w["pnl"] for w in wins if w["pnl"] > 0); dn = sum(w["pnl"] for w in wins if w["pnl"] < 0)
    put = sum(cost[w["ticker"]] for w in wins); ct = sum(qty[w["ticker"]] for w in wins)
    nw = sum(w["pnl"] > 0 for w in wins); nl = sum(w["pnl"] < 0 for w in wins)
    out += ["", f"Totals: **{len(wins)} rounds** ({nw} won / {nl} lost) · put in **${put:,.2f}** · {ct:,.0f} contracts · "
                f"up +${up:,.2f} · down −${abs(dn):,.2f} · **net {'+' if up+dn>=0 else '−'}${abs(up+dn):,.2f}**"]
    return "\n".join(out)


if __name__ == "__main__":
    print("\n\n".join(card(d) for d in (sys.argv[1:] or ["logs/brent", "logs/wti"])))
