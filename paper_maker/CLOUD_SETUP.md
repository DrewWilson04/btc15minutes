# Running Oil Bot on Google Cloud (free e2-micro)

You'll end up with the bots running 24/7 on Google's free server, and the dashboard on your Mac at
**http://localhost:8790** through a private, encrypted tunnel. The dashboard is never open to the internet.

Time: about 20–30 minutes. Cost: $0 within Google's Always Free tier (see step 2). Google's terms change, so check
the free-tier page when you sign up.

## 1. Google Cloud account

1. Go to **console.cloud.google.com** and sign in with a Google account.
2. Accept the terms. Create a **project** (top bar → project picker → *New project*), for example `oilbot`.
3. Set up **Billing** (left menu → Billing). A card is required even for the free tier.

## 2. Create the free server

Left menu → **Compute Engine → VM instances**. Click *Enable* if asked, then **Create instance**:

| Setting | Choose |
|---|---|
| Name | `oilbot` |
| Region | **us-central1 (Iowa)**, **us-west1 (Oregon)** or **us-east1 (South Carolina)**. Only these are free. |
| Machine type | **e2-micro** (under *General purpose → E2 → Shared-core*) |
| Boot disk | Change → **Debian 12**, disk type **Standard persistent disk**, size **30 GB** |
| Firewall | Leave *Allow HTTP* and *Allow HTTPS* **unchecked** |

Click **Create**. Note the **zone** it shows (for example `us-central1-a`); you'll need it in step 6.

> Free-tier rules: one e2-micro per account in those three US regions, 30 GB standard disk, and 1 GB of outbound
> traffic a month to most places. The bot sends many small requests and may go slightly over 1 GB, which costs cents.
> Keep it in the US: Kalshi is a US exchange.

## 3. Put Oil Bot on the server

1. On the VM list, click **SSH** next to `oilbot`. A terminal opens in your browser.
2. In that window click **Upload file** (the ⬆ icon at the top) and choose **OilBot.zip**.
3. Type:

```
unzip OilBot.zip
cd OilBot
./cloud/install.sh
```

The install takes 1–3 minutes. When it ends, all three services should show **active (running)**. It starts in **paper**
mode with your saved history.

## 4. Kalshi keys (only for live trading)

Still in the SSH window, in the `OilBot` folder:

```
./cloud/set_keys.sh
```

Paste the **Key ID** and press Enter. Then paste the **private key**, the whole thing from `-----BEGIN` to `-----END`,
press Enter, then **Ctrl+D**. It saves both readable only by you, then does a read-only sign-in that shows your balance.

## 5. Go live (optional, real money)

```
./cloud/go_live.sh       # type demo or real; real needs: I UNDERSTAND THIS IS REAL MONEY
./cloud/go_paper.sh      # back to paper; live orders are cancelled as the bots stop
```

## 6. See the dashboard on your Mac

You need Google's command-line tool on your Mac, one time:

1. Install the **Google Cloud CLI** for macOS from cloud.google.com/sdk/docs/install. Download it, unpack it,
   run `./google-cloud-sdk/install.sh`, then open a new Terminal window.
2. Run `gcloud init`, sign in, and pick your `oilbot` project.

Then, whenever you want to look:

```
gcloud compute ssh oilbot --zone us-central1-a -- -N -L 8790:localhost:8790
```

(Use your zone from step 2.) Leave that Terminal window open and go to **http://localhost:8790**. The Start/Stop buttons
work through this tunnel. Closing the Terminal window closes the dashboard, but the **bots keep running** on Google.

**On your phone:** the QR button won't work for the cloud copy, because the dashboard is only reachable through your Mac's tunnel.
Use **Download rounds (CSV)** or **Save chart (PNG)** and send them to yourself. Or, to let phones on your home Wi-Fi view it through your Mac,
start the tunnel with `-L 0.0.0.0:8790:localhost:8790` and open `http://<your Mac's IP>:8790` on the phone.

## Everyday commands (in the SSH window, inside `OilBot`)

| What | Command |
|---|---|
| Status and last log lines | `./cloud/status.sh` |
| Watch the Brent log live | `tail -f logs/brent.out` (Ctrl+C to stop watching) |
| Update to a new OilBot.zip | upload it to your home folder, then `./cloud/update.sh` (keeps logs, keys and settings) |
| Change caps or minutes | edit `config.json` (`nano config.json`), then restart the bots with the dashboard buttons |

If the server restarts (Google maintenance), the bots start again by themselves.
