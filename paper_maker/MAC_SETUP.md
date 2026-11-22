# Running the oil paper bot on a MacBook Air

This gives you the two paper bots (Brent and WTI) running 24/7, plus a live dashboard at
**http://localhost:8790** that refreshes every 3 seconds. Paper trading only: nothing here can place a real order,
and no Kalshi account or API key is needed.

Time needed: about 15 minutes.

## 1. Get the code onto the Mac

Easiest, with no extra tools: open the repo on GitHub, switch to branch **`claude/wonderful-wright-wo44ow`**,
click **Code**, then **Download ZIP**. Unzip it and move the folder somewhere permanent, for example your home folder.
Don't use Desktop or Documents if iCloud Drive syncs them, because macOS can move "cold" files to the cloud.

Or with git, in Terminal:

```
cd ~
git clone -b claude/wonderful-wright-wo44ow https://github.com/DrewWilson04/btc15minutes.git
```

## 2. Install (one time)

Open **Terminal** (press Cmd+Space and type Terminal), then:

```
cd ~/btc15minutes/paper_maker
./mac/setup.sh
```

If it says Python 3.9+ isn't found, install Python from https://www.python.org/downloads/macos/ and run it again.
If macOS asks to install "command line developer tools", click Install, wait, then run it again.

**Optional: keep the history from the cloud session.** Before starting, copy its saved results in:

```
mkdir -p logs && cp -r results/brent results/wti logs/
```

## 3. Start it

To try it out (stops if you log out or restart):

```
./mac/start.sh
open http://localhost:8790
```

For 24/7 running (starts by itself at login and restarts itself if it crashes):

```
./mac/stop.sh
./mac/install_autostart.sh
open http://localhost:8790
```

## 4. Keep the Mac awake

The services hold off idle sleep on their own, but also:

* **Keep it plugged in** and **leave the lid open**. Closing the lid puts a MacBook to sleep no matter what, and the bots stop.
* System Settings → **Battery** (or Energy Saver) → **Options**: turn on *Prevent automatic sleeping on power adapter when the display is off*.
* Optional, for restarts after a power cut: System Settings → Users & Groups → **Automatically log in as** your user.
  This only works with FileVault turned off, so decide whether that trade-off is worth it.

## 5. Everyday use

| What | Command (from `paper_maker`) |
|---|---|
| See the dashboard | open http://localhost:8790 |
| See it on your phone (same Wi-Fi) | start the dashboard with `python3 live_server.py --host 0.0.0.0`, then open `http://<Mac's IP>:8790`. The IP is in System Settings → Wi-Fi → Details |
| Money summary in Terminal | `./mac/status.sh` |
| Stop (manual mode) | `./mac/stop.sh` |
| Remove 24/7 services | `./mac/uninstall_autostart.sh` |
| Logs if something looks wrong | `tail -f logs/brent.out` |

The bots trade whenever Kalshi has an oil round open: Sunday 6 pm to Friday midnight ET.
Over the weekend the dashboard shows "Running · markets closed".

## Settings in use

* Brent: buys the favourite (price above 50¢) at the best bid in minutes 1–12. WTI: minutes 1–9, only when the underdog is under 40¢.
* Per round: at most $100 on the first side bought, and $130 on the other side if the price flips.
* At most 50 contracts per price level. Held to settlement, never sold early.

To change a setting, edit the matching line in `mac/start.sh` and `mac/install_autostart.sh`. For example, to run Brent on WTI's
rules, add `--max-minute 9 --max-dog 0.40` to the Brent line. Then rerun the start or install script.

## Live trading (real money)

Off by default. `config.json` holds the mode and caps; the double-click files change it for you.

1. **Set Kalshi Keys**: paste the API Key ID (it goes into Keychain) and pick the private key file
   (copied to `~/.oilbot/`, readable only by you).
2. **Go Live**: signs in read-only to check the key and show your balance. Then pick:
   * *Demo (fake money)*: Kalshi's demo exchange. Needs a separate demo account and key from demo.kalshi.co.
   * *Real money*: you must type `I UNDERSTAND THIS IS REAL MONEY`.
3. **Go Paper** switches back. The bots cancel their resting orders as they stop.

Live rules: post-only buys of the favourite at the best bid. At most **$20 on the first side and $50 on the
flip side** per round. Cancel and replace whenever the bid moves, held to settlement. Live logs go to `logs/live/<bot>`.
Safety: the bot cancels its orders at start-up, at stop and at a halt. It halts after 5 API errors in a row, or when a
file named `STOP` exists in `logs/live/`.
