#!/usr/bin/env python3
"""python3 mac/setmode.py paper | live-demo | live-prod CONFIRM_PHRASE"""
import json, os, sys
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
cfg = json.load(open(p))
mode = sys.argv[1]
if mode == "paper":
    cfg.update(mode="paper", live_confirm="")
elif mode == "live-demo":
    cfg.update(mode="live", environment="demo", live_confirm="I UNDERSTAND THIS IS REAL MONEY")
elif mode == "live-prod":
    cfg.update(mode="live", environment="prod", live_confirm=sys.argv[2] if len(sys.argv) > 2 else "")
elif mode == "env":
    cfg.update(environment=sys.argv[2])
json.dump(cfg, open(p, "w"), indent=2)
print("config:", cfg["mode"], cfg.get("environment"))
