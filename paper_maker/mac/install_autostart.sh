#!/bin/bash
# Run the bots + dashboard as macOS services: start at login, restart if they crash, keep the Mac awake.
set -e
cd "$(dirname "$0")/.."
DIR="$(pwd)"; PY="$DIR/.venv/bin/python"; LA="$HOME/Library/LaunchAgents"
[ -x "$PY" ] || { echo "Run ./mac/setup.sh first."; exit 1; }
./mac/stop.sh >/dev/null 2>&1 || true
mkdir -p "$LA" logs
make() { label=$1; out=$2; shift 2
  args=""; for a in /usr/bin/caffeinate -i "$PY" -u "$@"; do args="$args<string>$a</string>"; done
  cat > "$LA/$label.plist" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>$label</string>
<key>ProgramArguments</key><array>$args</array>
<key>WorkingDirectory</key><string>$DIR</string>
<key>RunAtLoad</key><true/>
<key>KeepAlive</key><true/>
<key>ThrottleInterval</key><integer>15</integer>
<key>StandardOutPath</key><string>$DIR/logs/$out.out</string>
<key>StandardErrorPath</key><string>$DIR/logs/$out.out</string>
</dict></plist>
PL
  launchctl unload "$LA/$label.plist" 2>/dev/null || true
  launchctl load -w "$LA/$label.plist"
  echo "installed $label"; }
make com.oilbot.brent brent run_bot.py brent
make com.oilbot.wti wti run_bot.py wti
make com.oilbot.dashboard dashboard live_server.py
echo "Done. Dashboard: http://localhost:8790  (they now start automatically at login)"
