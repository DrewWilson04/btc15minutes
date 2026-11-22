#!/bin/bash
LA="$HOME/Library/LaunchAgents"
for l in com.oilbot.brent com.oilbot.wti com.oilbot.dashboard; do
  launchctl unload -w "$LA/$l.plist" 2>/dev/null; rm -f "$LA/$l.plist"; echo "removed $l"; done
