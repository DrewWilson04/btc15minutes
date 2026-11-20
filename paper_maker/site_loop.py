#!/usr/bin/env python3
"""Rebuild the dashboard every --every seconds and (optionally) publish it.

    python3 site_loop.py --logs logs/brent logs/wti --out site \
        --publish-cmd 'rsync -az site/ me@drew.cx:/var/www/drew.cx/kalshi/'
"""
import argparse, subprocess, sys, time, os
p = argparse.ArgumentParser()
p.add_argument("--logs", nargs="+", default=["logs/brent"])
p.add_argument("--out", default="site")
p.add_argument("--every", type=int, default=300)
p.add_argument("--publish-cmd", default="", help="shell command run after each rebuild (rsync, git push, netlify deploy...)")
a = p.parse_args()
here = os.path.dirname(os.path.abspath(__file__))
while True:
    subprocess.run([sys.executable, os.path.join(here, "export_site.py"), "--logs", *a.logs, "--out", a.out])
    if a.publish_cmd:
        r = subprocess.run(a.publish_cmd, shell=True)
        print(f"publish exit {r.returncode}", flush=True)
    time.sleep(a.every)
