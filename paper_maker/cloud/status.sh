#!/bin/bash
cd "$(dirname "$0")/.."
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
systemctl --user --no-pager --lines=0 status oilbot-brent oilbot-wti oilbot-dashboard | grep -E "oilbot-|Active:"
echo "Mode: $(./.venv/bin/python -c 'import json;c=json.load(open("config.json"));print(c["mode"], c.get("environment"))')"
echo
echo "Last log lines:"
tail -n 3 logs/brent.out logs/wti.out 2>/dev/null
