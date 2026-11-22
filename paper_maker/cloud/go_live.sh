#!/bin/bash
# Switch to LIVE trading (Kalshi demo or real money). Checks the key first; real money needs the typed phrase.
cd "$(dirname "$0")/.."
PY=./.venv/bin/python
CAPS=$($PY -c 'import json;c=json.load(open("config.json"));print("$%s first side / $%s flip side" % (c["first_side_cap"], c["flip_side_cap"]))')
echo "LIVE TRADING: real orders on Kalshi (post-only), at most $CAPS per round."
echo "The strategy is NOT proven. You can lose money."
echo
read -r -p "Type demo (fake money) or real: " CH
case "$CH" in
  demo) ENV=demo ;;
  real) ENV=prod ;;
  *) echo "Cancelled. Still in paper mode."; exit 0 ;;
esac
$PY mac/setmode.py env "$ENV" >/dev/null
RES=$($PY run_bot.py --check-keys 2>&1 | tail -1)
echo "$RES"
case "$RES" in
  OK*) ;;
  *) $PY mac/setmode.py paper >/dev/null; echo "Could not sign in. Still in paper mode. Run ./cloud/set_keys.sh"; exit 1 ;;
esac
if [ "$ENV" = prod ]; then
  read -r -p "Type exactly: I UNDERSTAND THIS IS REAL MONEY > " T
  if [ "$T" != "I UNDERSTAND THIS IS REAL MONEY" ]; then
    $PY mac/setmode.py paper >/dev/null; echo "Phrase did not match. Still in paper mode."; exit 1
  fi
  $PY mac/setmode.py live-prod "$T"
else
  $PY mac/setmode.py live-demo
fi
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
systemctl --user restart oilbot-brent oilbot-wti
echo "Bots restarted in LIVE mode ($ENV). Watch the dashboard."
