#!/bin/bash
# Restart just the two bots (dashboard keeps running), in whichever way they were started.
cd "$(dirname "$0")/.."
LA="$HOME/Library/LaunchAgents"
for n in brent wti; do
  if [ -f "$LA/com.oilbot.$n.plist" ]; then
    launchctl unload "$LA/com.oilbot.$n.plist" 2>/dev/null; launchctl load -w "$LA/com.oilbot.$n.plist"; echo "restarted $n (service)"
  else
    if [ -f run/$n.pid ]; then kill "$(cat run/$n.pid)" 2>/dev/null; rm -f run/$n.pid; sleep 3; fi
  fi
done
[ -f "$LA/com.oilbot.brent.plist" ] || ./mac/start.sh
