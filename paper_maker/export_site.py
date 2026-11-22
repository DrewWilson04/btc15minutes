#!/usr/bin/env python3
"""Build a static dashboard (index.html + stats.json) from the paper bot's logs.

    python3 export_site.py --logs logs/brent logs/wti --out site
Upload/copy the `site/` folder anywhere (e.g. drew.cx/kalshi/). The page re-reads stats.json every 60 s.
"""
import argparse, datetime as dt, json, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def read_jsonl(p):
    if not os.path.exists(p):
        return []
    out = []
    for line in open(p):
        try: out.append(json.loads(line))
        except json.JSONDecodeError: pass
    return out


def summarize(log_dir):
    W = read_jsonl(os.path.join(log_dir, "windows.jsonl"))
    F = read_jsonl(os.path.join(log_dir, "fills.jsonl"))
    st = json.load(open(os.path.join(log_dir, "state.json"))) if os.path.exists(os.path.join(log_dir, "state.json")) else {}
    days = {}
    for w in W:
        d = w["ts"][:10]
        days.setdefault(d, {"day": d, "pnl": 0.0, "windows": 0, "contracts": 0.0})
        days[d]["pnl"] += w["pnl"]; days[d]["windows"] += 1; days[d]["contracts"] += w["contracts"]
    eq, run = [], 0.0
    for w in W:
        run += w["pnl"]; eq.append({"t": w["ts"], "total": round(run, 2)})
    contracts = sum(w["contracts"] for w in W)
    total = sum(w["pnl"] for w in W)
    peak, dd = 0.0, 0.0
    for e in eq:
        peak = max(peak, e["total"]); dd = min(dd, e["total"] - peak)
    return {
        "name": os.path.basename(os.path.normpath(log_dir)),
        "total": round(total, 2),
        "windows": len(W),
        "wins": sum(w["pnl"] > 0 for w in W), "losses": sum(w["pnl"] < 0 for w in W),
        "contracts": round(contracts),
        "cents_per_contract": round(100 * total / contracts, 2) if contracts else None,
        "max_drawdown": round(dd, 2),
        "open_windows": len(st.get("pending", [])),
        "days": [{**v, "pnl": round(v["pnl"], 2), "contracts": round(v["contracts"])} for v in sorted(days.values(), key=lambda x: x["day"])],
        "equity": eq[-500:],
        "recent_windows": W[-15:][::-1],
        "recent_fills": F[-15:][::-1],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--logs", nargs="+", default=["logs/brent"])
    p.add_argument("--out", default="site")
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    data = {"updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "bots": [summarize(d) for d in a.logs]}
    tmp = os.path.join(a.out, "stats.json.tmp")
    json.dump(data, open(tmp, "w"), indent=1); os.replace(tmp, os.path.join(a.out, "stats.json"))
    shutil.copy(os.path.join(HERE, "dashboard.html"), os.path.join(a.out, "index.html"))
    totals = ", ".join("%s $%+.2f" % (b["name"], b["total"]) for b in data["bots"])
    print("wrote %s/index.html + stats.json (%s)" % (a.out, totals))


if __name__ == "__main__":
    main()
