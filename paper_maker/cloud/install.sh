#!/bin/bash
# One-time install on a Debian/Ubuntu cloud server (e.g. Google Cloud e2-micro, Debian 12).
# Runs both bots + the dashboard as user services that restart on crash and start at boot.
set -e
cd "$(dirname "$0")/.."
DIR="$(pwd)"
echo "== Installing system packages (needs sudo) =="
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-venv python3-pip unzip >/dev/null
echo "== Python environment =="
python3 -m venv .venv
./.venv/bin/pip install --quiet --upgrade pip
./.venv/bin/pip install --quiet httpx cryptography segno
mkdir -p logs
for b in brent wti; do
  if [ ! -f "logs/$b/windows.jsonl" ] && [ -f "results/$b/windows.jsonl" ]; then
    mkdir -p "logs/$b" && cp results/$b/*.jsonl results/$b/state.json "logs/$b/" 2>/dev/null
    echo "imported saved $b history"
  fi
done
echo "== Services =="
UD="$HOME/.config/systemd/user"
mkdir -p "$UD"
write_unit() {
  name=$1; shift
  {
    echo "[Unit]"
    echo "Description=Oil bot: $name"
    echo "After=network-online.target"
    echo
    echo "[Service]"
    echo "WorkingDirectory=$DIR"
    echo "ExecStart=$DIR/.venv/bin/python -u $*"
    echo "Restart=always"
    echo "RestartSec=15"
    echo "StandardOutput=append:$DIR/logs/$name.out"
    echo "StandardError=append:$DIR/logs/$name.out"
    echo
    echo "[Install]"
    echo "WantedBy=default.target"
  } > "$UD/oilbot-$name.service"
}
write_unit brent run_bot.py brent
write_unit wti run_bot.py wti
write_unit dashboard live_server.py --host 127.0.0.1
sudo loginctl enable-linger "$(whoami)"   # keeps services running when you log out, and starts them at boot
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
systemctl --user daemon-reload
systemctl --user enable --now oilbot-brent oilbot-wti oilbot-dashboard
sleep 3
systemctl --user --no-pager --lines=0 status oilbot-brent oilbot-wti oilbot-dashboard | grep -E "oilbot-|Active:" || true
echo
echo "Installed. Mode: $(./.venv/bin/python -c 'import json;print(json.load(open("config.json"))["mode"])')"
echo "On your Mac, open the SSH tunnel (see CLOUD_SETUP.md), then go to http://localhost:8790"
