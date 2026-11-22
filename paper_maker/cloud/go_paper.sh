#!/bin/bash
cd "$(dirname "$0")/.."
./.venv/bin/python mac/setmode.py paper
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
systemctl --user restart oilbot-brent oilbot-wti
echo "Back to PAPER trading. Live orders were cancelled as the bots stopped."
