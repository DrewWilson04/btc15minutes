#!/usr/bin/env python3
"""Local live dashboard for the paper bots.

    python3 live_server.py                      # http://localhost:8790
    python3 live_server.py --host 0.0.0.0       # also reachable from your phone on the same Wi-Fi

Reads the bots' log folders (default logs/brent and logs/wti) on every request. Standard library only.
"""
import argparse, datetime as dt, json, os, shutil, signal, subprocess, sys
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


def bot_state(log_dir):
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
                        "put_in": round(cost[w["ticker"]], 2), "contracts": round(qty[w["ticker"]], 1)})

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
    for x in settled[-300:]:
        run += x["pnl"]
        equity.append(round(run, 2))
    return {
        "name": name, "live": live, "heartbeat_age_s": age,
        "pending": [p["ticker"] for p in state.get("pending", [])],
        "current_fills": cur_fills[-40:],
        "recent_fills": fills[-25:][::-1],
        "recent_rounds": settled[-20:][::-1],
        "all": summary(settled), "today": summary(today_items),
        "equity": equity,
    }


# ---- bot control (Start / Stop buttons) ----
# Same commands as mac/start.sh. If the 24/7 macOS services are installed, they are loaded/unloaded instead,
# because launchd would otherwise restart a bot we stop.
BOTS = {
    "brent": ["paper_maker.py", "--series", "KXBRENT15M", "--log-dir", "logs/brent", "--side-cap", "100", "--flip-cap", "130"],
    "wti": ["paper_maker.py", "--series", "KXWTI15M", "--max-minute", "9", "--max-dog", "0.40", "--log-dir", "logs/wti",
            "--side-cap", "100", "--flip-cap", "130"],
}
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


def bot_running(name):
    return bool(pid_alive(name) or launchd_loaded(name))


def start_bot(name):
    if bot_running(name):
        return "already running"
    if os.path.exists(plist(name)) and shutil.which("launchctl"):
        subprocess.run(["launchctl", "load", "-w", plist(name)], capture_output=True)
        return "started (service)"
    os.makedirs(RUN, exist_ok=True); os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    out = open(os.path.join(HERE, "logs", f"{name}.out"), "a")
    proc = subprocess.Popen([sys.executable, "-u"] + BOTS[name], cwd=HERE, stdout=out, stderr=out, start_new_session=True)
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
    logs = []
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
        if self.path.startswith("/api/state"):
            body = {"now": dt.datetime.now(UTC).isoformat(), "bots": [bot_state(d) for d in self.logs]}
            for b in body["bots"]:
                b["process_running"] = bot_running(b["name"]) if b["name"] in BOTS else None
            return self._send(200, json.dumps(body), "application/json")
        if self.path in ("/", "/index.html"):
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
        if len(parts) != 3 or parts[0] != "api" or parts[1] not in ("start", "stop") or parts[2] not in list(BOTS) + ["all"]:
            return self._send(404, "not found", "text/plain")
        names = list(BOTS) if parts[2] == "all" else [parts[2]]
        fn = start_bot if parts[1] == "start" else stop_bot
        result = {n: fn(n) for n in names}
        self._send(200, json.dumps(result), "application/json")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--logs", nargs="+", default=[os.path.join(HERE, "logs/brent"), os.path.join(HERE, "logs/wti")])
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8790)
    p.add_argument("--allow-remote-control", action="store_true", help="let other devices on your network press Start/Stop")
    a = p.parse_args()
    Handler.logs = a.logs; Handler.allow_remote = a.allow_remote_control
    print(f"live dashboard on http://localhost:{a.port}  (logs: {', '.join(a.logs)})", flush=True)
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()
