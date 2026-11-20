#!/bin/sh
# Every 2 newly settled rounds (Brent), copy logs + summary into results/ and push to GitHub.
cd "$(dirname "$0")"
BR=$(git rev-parse --abbrev-ref HEAD)
last=$(cat .last_pushed 2>/dev/null || echo 0)
while :; do
  n=$(wc -l < logs/brent/windows.jsonl 2>/dev/null || echo 0)
  if [ "$n" -ge $((last + 2)) ]; then
    mkdir -p results/brent results/wti
    for b in brent wti; do cp logs/$b/fills.jsonl logs/$b/windows.jsonl logs/$b/state.json results/$b/ 2>/dev/null; done
    { echo "# Paper bot results"; echo; echo "Updated $(date -u '+%Y-%m-%d %H:%M UTC')"; echo; python3 round_card.py; echo; echo '```'; python3 report.py; echo '```'; } > results/RESULTS.md
    git add results && git commit -q -m "Paper bot results: $n Brent rounds settled" && \
      for i in 1 2 3 4; do git push -q origin "$BR" && break; sleep $((i*5)); done
    last=$n; echo $last > .last_pushed
    echo "$(date -u +%H:%M) pushed at $n rounds"
  fi
  sleep 60
done
