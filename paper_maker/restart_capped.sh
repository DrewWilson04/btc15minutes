#!/bin/sh
# wait for the next quarter-hour boundary (+3s so the bots park the closing round as pending), then restart with a $100 cap
while :; do m=$(date -u +%M); s=$(date -u +%S); case $m in 00|15|30|45) [ "$s" -ge 3 ] && [ "$s" -le 20 ] && break;; esac; sleep 1; done
pkill -f paper_maker.py; sleep 2
nohup python3 -u paper_maker.py --series KXBRENT15M --log-dir logs/brent --side-cap 100 --flip-cap 130 >> brent.out 2>&1 &
nohup python3 -u paper_maker.py --series KXWTI15M --max-minute 9 --max-dog 0.40 --log-dir logs/wti --side-cap 100 --flip-cap 130 >> wti.out 2>&1 &
sleep 3; date -u; pgrep -fa paper_maker.py
