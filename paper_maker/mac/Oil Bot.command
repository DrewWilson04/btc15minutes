#!/bin/bash
# Oil Bot: the one file to double-click. Everything (start, stop, keys, go live, go paper) is a menu here.
cd "$(dirname "$0")"; [ -f run_bot.py ] || cd ..
PY=./.venv/bin/python
CONFIRM="I UNDERSTAND THIS IS REAL MONEY"

mode_text() {
  [ -x "$PY" ] || { echo "not set up yet"; return; }
  "$PY" -c 'import json;c=json.load(open("config.json"));m=c.get("mode");e=c.get("environment");print("PAPER (fake money)" if m!="live" else ("LIVE on Kalshi DEMO (fake money)" if e=="demo" else "LIVE - REAL MONEY"))'
}
running_text() {
  n=0; for b in brent wti; do [ -f run/$b.pid ] && kill -0 "$(cat run/$b.pid)" 2>/dev/null && n=$((n+1)); done
  launchctl list 2>/dev/null | grep -q com.oilbot.brent && n=2
  echo "$n of 2 bots running"
}

setup() {
  if [ ! -x "$PY" ]; then
    echo "First run: setting up (takes about a minute)..."
    ./mac/setup.sh || { echo; echo "Setup failed. Python 3.9 or newer is needed: install it from python.org, then try again."; return 1; }
  fi
  "$PY" -c "import cryptography, segno" 2>/dev/null || ./.venv/bin/pip install --quiet cryptography segno
  for b in brent wti; do
    if [ ! -f logs/$b/windows.jsonl ] && [ -f results/$b/windows.jsonl ]; then
      mkdir -p logs/$b && cp results/$b/*.jsonl results/$b/state.json logs/$b/ 2>/dev/null; echo "Imported saved $b history"
    fi
  done
}

do_start() {
  setup || return
  ./mac/start.sh
  sleep 2; open "http://localhost:8790"
  echo; echo "Running. The dashboard is open at http://localhost:8790"
  echo "You can close this window; the bots keep going in the background."
}

do_stop() {
  ./mac/stop.sh
  echo "Both bots and the dashboard are stopped. (Live orders are cancelled as the bots stop.)"
}

do_keys() {
  echo "Create a key at kalshi.com -> Account & security -> API Keys -> Create key."
  echo "Kalshi shows a Key ID and downloads a private key file."
  echo
  read -r -p "Paste your Key ID here, then press Enter: " KEYID
  KEYID=$(printf "%s" "$KEYID" | tr -d '[:space:]')
  [ -n "$KEYID" ] || { echo "No Key ID entered. Nothing saved."; return; }
  echo
  echo "Now DRAG the private key file (from Downloads) into this window, then press Enter:"
  read -r PEM
  PEM=$(printf "%s" "$PEM" | sed -e "s/^[[:space:]]*//" -e "s/[[:space:]]*$//" -e "s/^'//" -e "s/'$//" -e 's/\\ / /g')
  [ -f "$PEM" ] || { echo "Can't find that file: $PEM"; echo "Nothing saved."; return; }
  grep -q "PRIVATE KEY" "$PEM" || { echo "That file doesn't look like a private key. Nothing saved."; return; }
  mkdir -p "$HOME/.oilbot" && chmod 700 "$HOME/.oilbot"
  cp "$PEM" "$HOME/.oilbot/kalshi_private_key.pem" && chmod 600 "$HOME/.oilbot/kalshi_private_key.pem"
  security add-generic-password -U -a "$USER" -s oilbot-kalshi-key-id -w "$KEYID" 2>/dev/null \
    || { printf "%s" "$KEYID" > "$HOME/.oilbot/key_id"; chmod 600 "$HOME/.oilbot/key_id"; }
  echo; echo "Saved. Checking the key with a read-only sign-in (places no orders)..."
  setup >/dev/null || return
  "$PY" run_bot.py --check-keys 2>&1 | tail -1
  echo "Still in the same mode as before. Choose 'Go LIVE' when you're ready."
}

do_live() {
  setup >/dev/null || return
  echo "The bot will place REAL orders on Kalshi:"
  echo "  - buys the favourite at the best bid (post-only, never takes)"
  echo "  - at most \$20 on the first side and \$50 on the flip side each round"
  echo "  - both Brent and WTI. The strategy is NOT proven. You can lose money."
  echo
  echo "  1 = Real money"
  echo "  2 = Kalshi DEMO (fake money, needs a separate demo account + demo key)"
  echo "  anything else = cancel"
  read -r -p "Choose 1 or 2: " C
  case "$C" in 1) ENV=prod;; 2) ENV=demo;; *) echo "Cancelled. Nothing changed."; return;; esac
  OLD=$(cat config.json)
  "$PY" mac/setmode.py env $ENV >/dev/null
  echo; echo "Signing in to Kalshi ($ENV) read-only to check your key..."
  RES=$("$PY" run_bot.py --check-keys 2>&1 | tail -1)
  echo "  $RES"
  case "$RES" in OK*) ;; *) printf "%s" "$OLD" > config.json; echo; echo "Could not sign in. Nothing changed. Use 'Set Kalshi keys' first."; return;; esac
  if [ "$ENV" = "prod" ]; then
    echo; echo "Type exactly:  $CONFIRM"
    read -r -p "> " TYPED
    [ "$TYPED" = "$CONFIRM" ] || { printf "%s" "$OLD" > config.json; echo "Phrase did not match. Nothing changed."; return; }
    "$PY" mac/setmode.py live-prod "$TYPED" >/dev/null
  else
    "$PY" mac/setmode.py live-demo >/dev/null
  fi
  ./mac/restart_bots.sh
  sleep 2; open "http://localhost:8790"
  echo; echo "Now: $(mode_text). The dashboard shows a red LIVE banner and a status box."
}

do_paper() {
  setup >/dev/null || return
  "$PY" mac/setmode.py paper >/dev/null
  ./mac/restart_bots.sh
  echo "Back to PAPER (fake money). Live orders were cancelled as the bots restarted."
}

while true; do
  echo
  echo "=============================================="
  echo "  OIL BOT    mode: $(mode_text)"
  echo "             $(running_text)"
  echo "=============================================="
  echo "  1  Start bots + open dashboard"
  echo "  2  Stop everything"
  echo "  3  Open dashboard"
  echo "  4  Set Kalshi keys"
  echo "  5  Go LIVE (real money or demo)"
  echo "  6  Go back to PAPER"
  echo "  Q  Quit this menu (bots keep running)"
  read -r -p "Choose: " CH
  echo
  case "$CH" in
    1) do_start;; 2) do_stop;; 3) open "http://localhost:8790";;
    4) do_keys;; 5) do_live;; 6) do_paper;;
    q|Q|"") exit 0;;
    *) echo "Type a number from the list.";;
  esac
done
