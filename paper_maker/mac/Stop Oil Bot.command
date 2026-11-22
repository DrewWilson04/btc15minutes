#!/bin/bash
cd "$(dirname "$0")/.."
./mac/stop.sh
osascript -e 'display notification "Both bots and the dashboard are stopped." with title "Oil Bot"'
