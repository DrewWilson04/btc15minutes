#!/bin/bash
# Switch back to paper trading. The live bots cancel their resting orders as they stop.
cd "$(dirname "$0")/.."
./.venv/bin/python mac/setmode.py paper
./mac/restart_bots.sh
osascript -e 'display notification "Back to PAPER trading. Live orders were cancelled." with title "Oil Bot"' 2>/dev/null
