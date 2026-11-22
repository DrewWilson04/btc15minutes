#!/bin/bash
# Double-click to start: sets up on first run, starts both paper bots + the live dashboard, opens it.
cd "$(dirname "$0")/.."
echo "=== Oil Bot (paper trading) ==="
if [ ! -x .venv/bin/python ]; then
  echo "First run: setting up (takes about a minute)..."
  ./mac/setup.sh || { osascript -e 'display alert "Oil Bot setup failed" message "Python 3.9 or newer is needed. Install it from python.org, then double-click Start Oil Bot again."'; exit 1; }
fi
# First run: bring in the saved history from the cloud session, if logs are empty
"./.venv/bin/python" -c "import cryptography, segno" 2>/dev/null || ./.venv/bin/pip install --quiet cryptography segno
for b in brent wti; do
  if [ ! -f logs/$b/windows.jsonl ] && [ -f results/$b/windows.jsonl ]; then mkdir -p logs/$b && cp results/$b/*.jsonl results/$b/state.json logs/$b/ 2>/dev/null; echo "Imported saved $b history"; fi
done
./mac/start.sh
sleep 2
open "http://localhost:8790"
echo
echo "Running. You can close this window; the bots keep going in the background."
echo "To stop them, double-click 'Stop Oil Bot'."
