#!/bin/bash
# Switch the bots to LIVE trading (Kalshi demo with fake money, or real money). Asks first, checks keys first.
cd "$(dirname "$0")/.."
PY=./.venv/bin/python
ask() { osascript -e "$1" 2>/dev/null; }
[ -x "$PY" ] || { ask 'display alert "Run Start Oil Bot once first (it sets things up)."'; exit 1; }
"$PY" -c "import cryptography" 2>/dev/null || ./.venv/bin/pip install --quiet cryptography
CHOICE=$(ask 'button returned of (display dialog "Switch to LIVE trading?\n\nThe bot will place REAL orders on Kalshi:\n• buys the favourite at the best bid (post-only, never takes)\n• at most $20 on the first side and $50 on the flip side each round\n• both Brent and WTI\n\nThe strategy is NOT proven: paper results so far are mixed. You can lose money.\n\nTry Kalshi DEMO first (fake money, needs a separate demo account and demo key)." buttons {"Cancel","Demo (fake money)","Real money"} default button "Cancel" cancel button "Cancel" with icon caution with title "Oil Bot – go live")') || exit 0
[ -z "$CHOICE" ] && exit 0
if [ "$CHOICE" = "Demo (fake money)" ]; then ENV=demo; else ENV=prod; fi
"$PY" mac/setmode.py env $ENV >/dev/null
RES=$("$PY" run_bot.py --check-keys 2>&1 | tail -1)
case "$RES" in OK*) ;; *) "$PY" mac/setmode.py paper >/dev/null; ask "display alert \"Could not sign in to Kalshi ($ENV)\" message \"$RES\n\nStill in paper mode. Check your key with Set Kalshi Keys.\""; exit 1;; esac
if [ "$ENV" = "prod" ]; then
  TYPED=$(ask "text returned of (display dialog \"$RES\n\nType exactly:\nI UNDERSTAND THIS IS REAL MONEY\" default answer \"\" with icon caution with title \"Oil Bot – real money\")") || { "$PY" mac/setmode.py paper >/dev/null; exit 0; }
  [ "$TYPED" = "I UNDERSTAND THIS IS REAL MONEY" ] || { "$PY" mac/setmode.py paper >/dev/null; ask 'display alert "Phrase did not match. Still in paper mode."'; exit 1; }
  "$PY" mac/setmode.py live-prod "$TYPED"
else
  "$PY" mac/setmode.py live-demo
fi
./mac/restart_bots.sh
ask "display notification \"Bots restarted in LIVE mode ($ENV). Watch http://localhost:8790\" with title \"Oil Bot\""
open "http://localhost:8790"
