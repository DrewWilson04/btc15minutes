#!/bin/bash
# Store a Kalshi API key on this server, readable only by you:
#   ~/.oilbot/key_id   and   ~/.oilbot/kalshi_private_key.pem
cd "$(dirname "$0")/.."
mkdir -p ~/.oilbot && chmod 700 ~/.oilbot
read -r -p "Paste your Kalshi API Key ID, then press Enter: " KEYID
KEYID=$(echo "$KEYID" | tr -d '[:space:]')
if [ -z "$KEYID" ]; then echo "No Key ID entered. Nothing saved."; exit 1; fi
echo
echo "Now paste your PRIVATE KEY: everything from the -----BEGIN line to the -----END line."
echo "Then press Enter, then Ctrl+D."
PEM=$(cat)
if ! echo "$PEM" | grep -q "BEGIN .*PRIVATE KEY" || ! echo "$PEM" | grep -q "END .*PRIVATE KEY"; then
  echo "That doesn't look like a private key. Nothing saved."; exit 1
fi
umask 077
printf '%s' "$KEYID" > ~/.oilbot/key_id
printf '%s\n' "$PEM" > ~/.oilbot/kalshi_private_key.pem
chmod 600 ~/.oilbot/key_id ~/.oilbot/kalshi_private_key.pem
echo "Saved. Checking it (read-only sign-in, places nothing)..."
./.venv/bin/python run_bot.py --check-keys
