#!/usr/bin/env python3
"""Money report from the paper bot logs (no restart needed).

    python3 report.py                      # logs/brent and logs/wti
    python3 report.py --logs logs/brent --trades 20
"""
import argparse, json, os
from collections import defaultdict


def rows(path):
    if not os.path.exists(path):
        return []
    out = []
    for line in open(path):
        try: out.append(json.loads(line))
        except json.JSONDecodeError: pass
    return out


def report(log_dir, n_trades):
    fills = rows(os.path.join(log_dir, "fills.jsonl"))
    settled = {w["ticker"]: w for w in rows(os.path.join(log_dir, "windows.jsonl"))}
    by_win = defaultdict(list)
    for f in fills:
        by_win[f["ticker"]].append(f)

    print(f"\n===== {os.path.basename(os.path.normpath(log_dir)).upper()} =====")
    print(f"{'window':28s} {'side':>4s} {'contracts':>9s} {'put in':>9s} {'avg px':>7s} {'result':>6s} {'P&L':>9s}")
    invested = invested_settled = up = down = 0.0
    wins = losses = 0
    for tk in sorted(by_win, key=lambda t: by_win[t][0]["trade_time"]):
        fs = by_win[tk]
        qty = sum(f["qty"] for f in fs)
        cost = sum(f["qty"] * f["price"] for f in fs)
        sides = "/".join(sorted({f["side"].upper() for f in fs}))
        invested += cost
        w = settled.get(tk)
        if w:
            invested_settled += cost
            pnl = w["pnl"]
            if pnl > 0: wins += 1; up += pnl
            elif pnl < 0: losses += 1; down += pnl
            res, pl = w["result"].upper(), f"{'+' if pnl >= 0 else '-'}${abs(pnl):,.2f}"
        else:
            res, pl = "open", "pending"
        print(f"{tk:28s} {sides:>4s} {qty:9.0f} {'$'+format(cost,',.2f'):>9s} {cost/qty:7.3f} {res:>6s} {pl:>9s}")

    net = up + down
    print("-" * 78)
    print(f"Money put in (all trades):    ${invested:,.2f}   (settled ${invested_settled:,.2f})")
    print(f"Windows won / lost:           {wins} / {losses}")
    print(f"Total up (winning windows):   +${up:,.2f}")
    print(f"Total down (losing windows):  -${abs(down):,.2f}")
    print(f"Net made:                     {'+' if net >= 0 else '-'}${abs(net):,.2f}"
          + (f"   ({100*net/invested_settled:+.2f}% of money put in)" if invested_settled else ""))
    if n_trades:
        print(f"\nLast {n_trades} individual fills:")
        for f in fills[-n_trades:]:
            print(f"  {f['trade_time'][11:19]}  {f['ticker']}  {f['side'].upper():3s} {f['qty']:6.0f} @ {f['price']:.3f}  = ${f['qty']*f['price']:,.2f}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--logs", nargs="+", default=["logs/brent", "logs/wti"])
    p.add_argument("--trades", type=int, default=0, help="also list the last N individual fills")
    a = p.parse_args()
    for d in a.logs:
        report(d, a.trades)
