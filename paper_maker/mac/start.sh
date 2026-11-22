#!/bin/bash
# Start both paper bots and the live dashboard in the background (use install_autostart.sh instead for 24/7).
cd "$(dirname "$0")/.."
PY=./.venv/bin/python
[ -x "$PY" ] || { echo "Run ./mac/setup.sh first."; exit 1; }
mkdir -p logs run
start() { name=$1; shift
  if [ -f run/$name.pid ] && kill -0 "$(cat run/$name.pid)" 2>/dev/null; then echo "$name already running"; return; fi
  nohup "$PY" -u "$@" >> logs/$name.out 2>&1 &
  pid=$!; echo $pid > run/$name.pid
  command -v caffeinate >/dev/null && (nohup caffeinate -i -w $pid >/dev/null 2>&1 &)
  echo "started $name"; }
start brent run_bot.py brent
start wti   run_bot.py wti
start dashboard live_server.py
echo "Dashboard: http://localhost:8790"
