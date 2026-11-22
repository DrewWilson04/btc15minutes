#!/bin/bash
# After uploading a new OilBot.zip to your home folder: unpack it over this folder
# (keeps your logs, keys and config.json), then restart everything.
cd "$(dirname "$0")/.."
if [ ! -f ~/OilBot.zip ]; then echo "Upload the new OilBot.zip to your home folder first."; exit 1; fi
cp config.json /tmp/oilbot_config.json
unzip -o -q ~/OilBot.zip -d ~
cp /tmp/oilbot_config.json config.json
./.venv/bin/pip install --quiet httpx cryptography segno
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
systemctl --user restart oilbot-brent oilbot-wti oilbot-dashboard
echo "Updated and restarted (your config.json was kept)."
