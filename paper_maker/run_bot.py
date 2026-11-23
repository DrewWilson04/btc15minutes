#!/usr/bin/env python3
"""Start one bot using config.json:  python3 run_bot.py brent   |   python3 run_bot.py --check-keys

mode "paper": simulated fills (paper_maker.py), logs in logs/<name>
mode "live":  REAL orders and money (live_maker.py), logs in logs/live/<name>
             (or logs/demo/<name> on Kalshi's demo exchange). Needs live_confirm set to the confirmation phrase.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load_config():
    with open(os.path.join(HERE, "config.json")) as f:
        return json.load(f)


def log_dir(cfg, name):
    if cfg.get("mode") == "live":
        return os.path.join(HERE, "logs", "demo" if cfg.get("environment") == "demo" else "live", name)
    return os.path.join(HERE, "logs", name)


def bot_args(cfg, name):
    b = cfg["bots"][name]
    return argparse.Namespace(series=b["series"], max_minute=int(b["max_minute"]), per_level=float(cfg.get("per_level", 50)),
                              min_dog=0.0, max_dog=float(b["max_dog"]), window_cap=0.0,
                              side_cap=float(cfg["first_side_cap"]), flip_cap=float(cfg["flip_side_cap"]),
                              day_stop=0.0, count_open_risk=False, poll=1.5, log_dir=log_dir(cfg, name),
                              env=cfg.get("environment", "prod"), confirm=cfg.get("live_confirm", ""),
                              no_flip=not b.get("flip", True), flip_wait=float(b.get("flip_wait", 0)))


if __name__ == "__main__":
    os.chdir(HERE); sys.path.insert(0, HERE)
    cfg = load_config()
    if len(sys.argv) > 1 and sys.argv[1] == "--check-keys":
        from live_maker import check_keys, shard_report
        try:
            bal, raw = check_keys(cfg.get("environment", "prod"))
            print(f"OK: signed in to Kalshi ({cfg.get('environment', 'prod')}). Balance ${bal:,.2f}" + shard_report(raw))
        except SystemExit as e:
            print(f"FAILED: {e}"); sys.exit(1)
        except Exception as e:
            print(f"FAILED: {e}"); sys.exit(1)
        sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] == "--test-order":
        from live_maker import test_order
        try:
            print("OK: " + test_order(cfg.get("environment", "prod")))
        except BaseException as e:
            print(f"FAILED: {e}"); sys.exit(1)
        sys.exit(0)
    name = sys.argv[1]
    if not cfg["bots"].get(name, {}).get("enabled", True):
        print(f"{name} is disabled in config.json"); sys.exit(0)
    a = bot_args(cfg, name)
    if cfg.get("mode") == "live":
        from live_maker import LiveMaker
        LiveMaker(a).run()
    else:
        from paper_maker import PaperMaker
        PaperMaker(a).run()
