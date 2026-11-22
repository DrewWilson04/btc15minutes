#!/bin/bash
# Switch the bots to LIVE trading (Kalshi demo with fake money, or real money).
# Everything happens in this Terminal window, so any problem is shown here.
cd "$(dirname "$0")"; [ -f run_bot.py ] || cd ..
PY=./.venv/bin/python
echo "=============================================="
echo "  Oil Bot - GO LIVE"
echo "=============================================="
if [ ! -x "$PY" ]; then echo "Run 'Start Oil Bot' once first (it sets things up). Nothing changed."; exit 1; fi
"$PY" -c "import cryptography" 2>/dev/null || ./.venv/bin/pip install --quiet cryptography
echo
echo "The bot will place REAL orders on Kalshi:"
echo "  - buys the favourite at the best bid (post-only, never takes)"
echo "  - at most \$20 on the first side and \$50 on the flip side each round"
echo "  - both Brent and WTI"
echo "The strategy is NOT proven. You can lose money."
echo
echo "  1 = Real money"
echo "  2 = Kalshi DEMO (fake money, needs a separate demo account + demo key)"
echo "  anything else = cancel"
read -r -p "Choose 1 or 2: " CHOICE
case "$CHOICE" in 1) ENV=prod;; 2) ENV=demo;; *) echo "Cancelled. Still in paper mode."; exit 0;; esac
"$PY" mac/setmode.py env $ENV >/dev/null
echo
echo "Signing in to Kalshi ($ENV) read-only to check your key..."
RES=$("$PY" run_bot.py --check-keys 2>&1 | tail -1)
echo "  $RES"
case "$RES" in OK*) ;; *)
  "$PY" mac/setmode.py paper >/dev/null
  echo
  echo "Could not sign in. Still in PAPER mode."
  echo "Run 'Set Kalshi Keys' again (or send this message to Claude)."
  exit 1;; esac
if [ "$ENV" = "prod" ]; then
  echo
  echo "Type exactly:  I UNDERSTAND THIS IS REAL MONEY"
  read -r -p "> " TYPED
  if [ "$TYPED" != "I UNDERSTAND THIS IS REAL MONEY" ]; then
    "$PY" mac/setmode.py paper >/dev/null; echo "Phrase did not match. Still in paper mode."; exit 1
  fi
  "$PY" mac/setmode.py live-prod "$TYPED"
else
  "$PY" mac/setmode.py live-demo
fi
echo
./mac/restart_bots.sh
sleep 2
open "http://localhost:8790"
echo
echo "LIVE ($ENV). The dashboard should now show a red LIVE banner."
echo "To go back to fake money: double-click 'Go Paper'."
