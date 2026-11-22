#!/bin/bash
# Store a Kalshi API key on this Mac for live trading. Everything happens in this Terminal window.
# Key ID -> macOS Keychain (service "oilbot-kalshi-key-id").
# Private key file -> ~/.oilbot/kalshi_private_key.pem, readable only by you (chmod 600). Never in the project folder.
cd "$(dirname "$0")"; [ -f run_bot.py ] || cd ..
echo "=============================================="
echo "  Oil Bot - SET KALSHI KEYS"
echo "=============================================="
echo "Create a key at kalshi.com -> Account & security -> API Keys -> Create key."
echo "Kalshi shows a Key ID and downloads a private key file."
echo
read -r -p "Paste your Key ID here, then press Enter: " KEYID
KEYID=$(printf "%s" "$KEYID" | tr -d '[:space:]')
[ -n "$KEYID" ] || { echo "No Key ID entered. Nothing saved."; exit 1; }
echo
echo "Now DRAG the private key file (from Downloads) into this window, then press Enter:"
read -r PEM
PEM=$(printf "%s" "$PEM" | sed -e "s/^[[:space:]]*//" -e "s/[[:space:]]*$//" -e "s/^'//" -e "s/'$//" -e 's/\\ / /g')
[ -f "$PEM" ] || { echo "Can't find that file: $PEM"; echo "Nothing saved."; exit 1; }
grep -q "PRIVATE KEY" "$PEM" || { echo "That file doesn't look like a private key (.pem / .key / .txt from Kalshi). Nothing saved."; exit 1; }
mkdir -p "$HOME/.oilbot" && chmod 700 "$HOME/.oilbot"
cp "$PEM" "$HOME/.oilbot/kalshi_private_key.pem" && chmod 600 "$HOME/.oilbot/kalshi_private_key.pem"
security add-generic-password -U -a "$USER" -s oilbot-kalshi-key-id -w "$KEYID" 2>/dev/null \
  || { printf "%s" "$KEYID" > "$HOME/.oilbot/key_id"; chmod 600 "$HOME/.oilbot/key_id"; }
echo
echo "Saved. Checking the key with a read-only sign-in..."
if [ -x ./.venv/bin/python ]; then
  ./.venv/bin/python -c "import cryptography" 2>/dev/null || ./.venv/bin/pip install --quiet cryptography
  ./.venv/bin/python run_bot.py --check-keys 2>&1 | tail -1
else
  echo "(Run 'Start Oil Bot' once to set up, then this check works.)"
fi
echo
echo "The bot is still in paper mode. Next: double-click 'Go Live'."
