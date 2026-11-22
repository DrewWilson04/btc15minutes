#!/bin/bash
cd "$(dirname "$0")/.."
for n in brent wti dashboard; do
  if [ -f run/$n.pid ] && kill -0 "$(cat run/$n.pid)" 2>/dev/null; then echo "$n: running"; else echo "$n: not running (manual start)"; fi
done
launchctl list 2>/dev/null | grep -q com.oilbot && { echo "autostart services:"; launchctl list | grep com.oilbot; }
[ -x .venv/bin/python ] && ./.venv/bin/python report.py
