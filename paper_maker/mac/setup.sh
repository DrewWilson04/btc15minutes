#!/bin/bash
# One-time setup on the Mac: finds Python 3.9+, makes a private environment, installs the one library the bot needs.
set -e
cd "$(dirname "$0")/.."
PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3.9 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)' 2>/dev/null; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "Python 3.9 or newer not found."
  echo "Install it from https://www.python.org/downloads/macos/ (pick the macOS installer), then run this again."
  exit 1
fi
echo "Using $($PY --version) at $(command -v $PY)"
$PY -m venv .venv
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet httpx cryptography
mkdir -p logs
echo
echo "Setup done. Next:"
echo "  ./mac/start.sh          start the bots + live dashboard"
echo "  open http://localhost:8790"
