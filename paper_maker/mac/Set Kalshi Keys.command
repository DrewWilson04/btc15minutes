#!/bin/bash
# Pop-up to store a Kalshi API key for later live trading. The paper bot does NOT use it.
# Key ID -> macOS Keychain (service "oilbot-kalshi-key-id").
# Private key file -> ~/.oilbot/kalshi_private_key.pem, readable only by you (chmod 600). Never put it in the project folder.
set -e
ask() { osascript -e "$1" 2>/dev/null; }
ask 'display dialog "Store your Kalshi API key on this Mac?\n\nThe paper bot does not use it. It is saved for live trading later:\n• Key ID → your macOS Keychain\n• Private key file → a private folder only your user can read\n\nCreate a key at kalshi.com → Account → API Keys." buttons {"Cancel","Continue"} default button "Continue" with title "Oil Bot – Kalshi keys"' >/dev/null || exit 0
KEYID=$(ask 'text returned of (display dialog "Paste your Kalshi API Key ID:" default answer "" with title "Oil Bot – Kalshi keys")') || exit 0
KEYID=$(echo "$KEYID" | tr -d '[:space:]')
[ -n "$KEYID" ] || { ask 'display alert "No Key ID entered. Nothing was saved."'; exit 0; }
PEM=$(ask 'POSIX path of (choose file with prompt "Choose the private key file Kalshi gave you (ends in .pem or .key):")') || exit 0
grep -q "PRIVATE KEY" "$PEM" || { ask 'display alert "That file does not look like a private key." message "Pick the .pem/.key file you downloaded when you created the API key. Nothing was saved."'; exit 1; }
mkdir -p "$HOME/.oilbot" && chmod 700 "$HOME/.oilbot"
cp "$PEM" "$HOME/.oilbot/kalshi_private_key.pem" && chmod 600 "$HOME/.oilbot/kalshi_private_key.pem"
security add-generic-password -U -a "$USER" -s oilbot-kalshi-key-id -w "$KEYID"
ask "display dialog \"Saved.\n\nKey ID: in Keychain (oilbot-kalshi-key-id)\nPrivate key: ~/.oilbot/kalshi_private_key.pem\n\nYou can delete the downloaded key file now if you like. The bot is still paper trading only.\" buttons {\"OK\"} default button \"OK\" with title \"Oil Bot – Kalshi keys\"" >/dev/null
