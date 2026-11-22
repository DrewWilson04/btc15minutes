#!/usr/bin/env python3
"""Local live dashboard for the paper bots.

    python3 live_server.py                      # http://localhost:8790
    python3 live_server.py --host 127.0.0.1     # this Mac only (default 0.0.0.0: phones on your Wi-Fi can view; only this Mac can press buttons)

Reads the bots' log folders (default logs/brent and logs/wti) on every request. Standard library only.
"""
import argparse, csv, datetime as dt, io, json, os, shutil, signal, socket, subprocess, sys
from urllib.parse import parse_qs, urlparse
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
UTC = dt.timezone.utc
ET = dt.timezone(dt.timedelta(hours=-5))   # display only (EST)


def rows(path, tail=None):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        lines = f.readlines()
    if tail:
        lines = lines[-tail:]
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def bot_state(log_dir, frm=None):
    name = os.path.basename(os.path.normpath(log_dir))
    fills = rows(os.path.join(log_dir, "fills.jsonl"))
    wins = rows(os.path.join(log_dir, "windows.jsonl"))
    live = read_json(os.path.join(log_dir, "live.json"))
    state = read_json(os.path.join(log_dir, "state.json")) or {}
    cost, qty = defaultdict(float), defaultdict(float)
    for f in fills:
        cost[f["ticker"]] += f["qty"] * f["price"]
        qty[f["ticker"]] += f["qty"]
    today = dt.datetime.now(ET).date().isoformat()
    settled = []
    for w in wins:
        settled.append({"ticker": w["ticker"], "result": w["result"], "pnl": w["pnl"], "ts": w["ts"],
                        "date": dt.datetime.fromisoformat(w["ts"]).astimezone(ET).date().isoformat(),
                        "put_in": round(cost[w["ticker"]], 2), "contracts": round(qty[w["ticker"]], 1)})
    ranged = [x for x in settled if not frm or x["date"] >= frm]

    def summary(items):
        return {"rounds": len(items), "won": sum(x["pnl"] > 0 for x in items), "lost": sum(x["pnl"] < 0 for x in items),
                "net": round(sum(x["pnl"] for x in items), 2), "put_in": round(sum(x["put_in"] for x in items), 2),
                "up": round(sum(x["pnl"] for x in items if x["pnl"] > 0), 2),
                "down": round(sum(x["pnl"] for x in items if x["pnl"] < 0), 2)}

    today_items = [x for x in settled if dt.datetime.fromisoformat(x["ts"]).astimezone(ET).date().isoformat() == today]
    cur = live.get("market") if live else None
    cur_fills = [f for f in fills if f["ticker"] == cur] if cur else []
    age = None
    if live:
        age = (dt.datetime.now(UTC) - dt.datetime.fromisoformat(live["ts"])).total_seconds()
    equity, run = [], 0.0
    for x in ranged:
        run += x["pnl"]
        equity.append({"t": x["ts"], "y": round(run, 2), "step": x["pnl"]})
    return {
        "name": name, "live": live, "heartbeat_age_s": age,
        "pending": [p["ticker"] for p in state.get("pending", [])],
        "current_fills": cur_fills[-40:],
        "recent_fills": fills[-25:][::-1],
        "recent_rounds": ranged[-60:][::-1],
        "all": summary(settled), "today": summary(today_items), "range": summary(ranged),
        "first_date": settled[0]["date"] if settled else None, "_ranged": ranged,
        "equity": equity,
    }


def lan_ip():
    """This Mac's address on the local network (no traffic is sent)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1)); return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


# ---- bot control (Start / Stop buttons) ----
# Same commands as mac/start.sh. If the 24/7 macOS services are installed, they are loaded/unloaded instead,
# because launchd would otherwise restart a bot we stop.
sys.path.insert(0, HERE)
import run_bot                                       # config.json: mode, caps, which bots


def bot_names():
    return [n for n, b in run_bot.load_config()["bots"].items() if b.get("enabled", True)]


RUN = os.path.join(HERE, "run")


def plist(name):
    return os.path.expanduser(f"~/Library/LaunchAgents/com.oilbot.{name}.plist")


def pid_alive(name):
    try:
        with open(os.path.join(RUN, f"{name}.pid")) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None


def launchd_loaded(name):
    if not os.path.exists(plist(name)) or not shutil.which("launchctl"):
        return False
    return subprocess.run(["launchctl", "list", f"com.oilbot.{name}"], capture_output=True).returncode == 0


def systemd_unit(name):
    """Linux cloud server: per-user systemd service installed by cloud/install.sh."""
    unit = f"oilbot-{name}.service"
    if shutil.which("systemctl") and os.path.exists(os.path.expanduser(f"~/.config/systemd/user/{unit}")):
        return unit
    return None


def systemd_active(name):
    unit = systemd_unit(name)
    return bool(unit) and subprocess.run(["systemctl", "--user", "is-active", "--quiet", unit]).returncode == 0


def bot_running(name):
    return bool(pid_alive(name) or launchd_loaded(name) or systemd_active(name))


def start_bot(name):
    if bot_running(name):
        return "already running"
    if os.path.exists(plist(name)) and shutil.which("launchctl"):
        subprocess.run(["launchctl", "load", "-w", plist(name)], capture_output=True)
        return "started (service)"
    if systemd_unit(name):
        subprocess.run(["systemctl", "--user", "start", systemd_unit(name)], capture_output=True)
        return "started (service)"
    os.makedirs(RUN, exist_ok=True); os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    out = open(os.path.join(HERE, "logs", f"{name}.out"), "a")
    proc = subprocess.Popen([sys.executable, "-u", "run_bot.py", name], cwd=HERE, stdout=out, stderr=out, start_new_session=True)
    with open(os.path.join(RUN, f"{name}.pid"), "w") as f:
        f.write(str(proc.pid))
    if shutil.which("caffeinate"):                  # keep the Mac awake for as long as this bot runs
        subprocess.Popen(["caffeinate", "-i", "-w", str(proc.pid)], start_new_session=True)
    return "started"


def stop_bot(name):
    msg = "not running"
    if launchd_loaded(name):
        subprocess.run(["launchctl", "unload", "-w", plist(name)], capture_output=True)
        msg = "stopped (service)"
    if systemd_active(name):
        subprocess.run(["systemctl", "--user", "stop", systemd_unit(name)], capture_output=True)
        msg = "stopped (service)"
    pid = pid_alive(name)
    if pid:
        os.kill(pid, signal.SIGTERM)                # the bot process only, never the dashboard
        msg = "stopped"
    try:
        os.remove(os.path.join(RUN, f"{name}.pid"))
    except OSError:
        pass
    return msg


class Handler(BaseHTTPRequestHandler):
    allow_remote = False

    def _send(self, code, body, ctype):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        frm = (q.get("from") or [None])[0]
        if frm and not (len(frm) == 10 and frm[4] == "-" and frm[7] == "-"):
            frm = None
        if self.path.startswith("/api/lanip"):
            return self._send(200, json.dumps({"ip": lan_ip(), "port": self.server.server_address[1],
                                               "listening_on_network": self.server.server_address[0] != "127.0.0.1"}), "application/json")
        if self.path.startswith("/api/qr.svg"):
            text = (q.get("text") or [""])[0][:500]
            try:
                import segno
            except ImportError:
                return self._send(501, "QR maker not installed (pip install segno)", "text/plain")
            buf = io.BytesIO(); segno.make(text, error="m").save(buf, kind="svg", scale=6, border=2)
            return self._send(200, buf.getvalue(), "image/svg+xml")
        if self.path.startswith("/export.csv"):
            cfg = run_bot.load_config(); out = io.StringIO(); wr = csv.writer(out)
            wr.writerow(["bot", "round_end_et", "settled_utc", "result", "contracts", "put_in", "pnl", "running_total"])
            for n in bot_names():
                st = bot_state(run_bot.log_dir(cfg, n), frm); run = 0.0
                for r in st["_ranged"]:
                    run += r["pnl"]
                    wr.writerow([n, r["ticker"], r["ts"], r["result"], r["contracts"], r["put_in"], round(r["pnl"], 2), round(run, 2)])
            data = out.getvalue().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", f'attachment; filename="oilbot_rounds_{frm or "all"}.csv"')
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data); return
        if self.path.startswith("/api/state"):
            cfg = run_bot.load_config()
            names = bot_names()
            body = {"now": dt.datetime.now(UTC).isoformat(), "mode": cfg.get("mode", "paper"), "env": cfg.get("environment", "prod"),
                    "caps": {"first": cfg.get("first_side_cap"), "flip": cfg.get("flip_side_cap")},
                    "from": frm, "bots": [bot_state(run_bot.log_dir(cfg, n), frm) for n in names]}
            for b in body["bots"]:
                b["process_running"] = bot_running(b["name"]); b.pop("_ranged", None)
            return self._send(200, json.dumps(body), "application/json")
        if urlparse(self.path).path in ("/", "/index.html"):
            with open(os.path.join(HERE, "live.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        self._send(404, "not found", "text/plain")

    def do_POST(self):
        # Buttons send a custom header; a cross-site page can't, so other websites can't press them.
        if self.headers.get("X-OilBot") != "1":
            return self._send(403, "forbidden", "text/plain")
        if not self.allow_remote and self.client_address[0] not in ("127.0.0.1", "::1"):
            return self._send(403, "control only from this Mac", "text/plain")
        parts = self.path.strip("/").split("/")          # api/start/brent | api/stop/all
        if len(parts) != 3 or parts[0] != "api" or parts[1] not in ("start", "stop") or parts[2] not in bot_names() + ["all"]:
            return self._send(404, "not found", "text/plain")
        names = bot_names() if parts[2] == "all" else [parts[2]]
        fn = start_bot if parts[1] == "start" else stop_bot
        result = {n: fn(n) for n in names}
        self._send(200, json.dumps(result), "application/json")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="0.0.0.0", help="0.0.0.0 = viewable from your phone on the same Wi-Fi (buttons still work only on this Mac); 127.0.0.1 = this Mac only")
    p.add_argument("--port", type=int, default=8790)
    p.add_argument("--allow-remote-control", action="store_true", help="let other devices on your network press Start/Stop")
    a = p.parse_args()
    Handler.allow_remote = a.allow_remote_control
    print(f"live dashboard on http://localhost:{a.port}  (mode: {run_bot.load_config().get('mode')})", flush=True)
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()
