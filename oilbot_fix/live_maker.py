#!/usr/bin/env python3
"""LIVE market-maker: same strategy as paper_maker.py, but with REAL Kalshi orders and REAL money.

Differences from paper:
  * one real resting order at a time, sent as post_only (it can only rest on the book, never take liquidity)
  * the order is cancelled and replaced whenever the best bid moves, or when it leaves the rules (minute, price, cap)
  * caps count REAL fills from /portfolio/fills; each order is sized so that, even if it fills completely,
    the side stays within its cap
  * on start: cancels any resting orders it finds for this series; on stop (SIGTERM / Ctrl-C) or a halt: cancels its order
  * halts itself (cancels and stops quoting until restarted) after repeated API errors, or when a STOP file exists

Order format (Kalshi V2, POST /portfolio/events/orders, prices on the YES side; the old /portfolio/orders writes return 410):
  buy YES at p  ->  side "bid", price p
  buy NO  at q  ->  side "ask", price 1 - q

Exchange shards: Kalshi splits accounts into shards; oil (Commodities) is on shard 2. Website orders move money between
shards automatically, API orders do NOT, so the oil shard must hold the money (kalshi.com/account/exchange-indexes).
Orders auto-route by ticker; cancels must send market_ticker or they go to shard 0 and miss the order.
"""
OIL_SHARD = 2
import base64, datetime as dt, json, math, os, signal, subprocess, sys, time, uuid
import httpx
import paper_maker as pm
from paper_maker import PaperMaker, now, ts, levels

HOSTS = {"prod": "https://api.elections.kalshi.com/trade-api/v2", "demo": "https://demo-api.kalshi.co/trade-api/v2"}
CONFIRM = "I UNDERSTAND THIS IS REAL MONEY"
MIN_CONTRACTS = 1.0


# ---------------- keys ----------------
def load_keys():
    """Key ID: env OILBOT_KEY_ID or macOS Keychain (oilbot-kalshi-key-id). Private key: env OILBOT_KEY_FILE or ~/.oilbot/kalshi_private_key.pem"""
    key_id = os.environ.get("OILBOT_KEY_ID")
    if not key_id:
        try:
            key_id = subprocess.run(["security", "find-generic-password", "-s", "oilbot-kalshi-key-id", "-w"],
                                    capture_output=True, text=True, timeout=10).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            key_id = ""
    if not key_id:                                  # Linux / cloud: ~/.oilbot/key_id (chmod 600)
        try:
            with open(os.path.expanduser("~/.oilbot/key_id")) as f:
                key_id = f.read().strip()
        except OSError:
            key_id = ""
    path = os.environ.get("OILBOT_KEY_FILE") or os.path.expanduser("~/.oilbot/kalshi_private_key.pem")
    if not key_id or not os.path.exists(path):
        raise SystemExit("Kalshi keys not found. On a Mac open Oil Bot and choose 4 (Set Kalshi keys); on the cloud server run ./cloud/set_keys.sh")
    with open(path, "rb") as f:
        pem = f.read()
    return key_id, pem


class Signer:
    def __init__(self, key_id, pem):
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        self.key_id, self._h, self._p, self._ed = key_id, hashes, padding, Ed25519PrivateKey
        self.key = serialization.load_pem_private_key(pem, password=None)

    def headers(self, method, path):
        stamp = str(int(time.time() * 1000))
        msg = (stamp + method.upper() + path.split("?")[0]).encode()
        if isinstance(self.key, self._ed):
            sig = self.key.sign(msg)
        else:
            sig = self.key.sign(msg, self._p.PSS(mgf=self._p.MGF1(self._h.SHA256()), salt_length=self._p.PSS.DIGEST_LENGTH),
                                self._h.SHA256())
        return {"KALSHI-ACCESS-KEY": self.key_id, "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode(),
                "KALSHI-ACCESS-TIMESTAMP": stamp}


class ApiError(Exception):
    def __init__(self, status, text):
        super().__init__(f"HTTP {status}: {text[:300]}")
        self.status = status


class AuthClient:
    """Authenticated calls (orders, fills, balance). Public market data still goes through paper_maker.Client."""
    def __init__(self, base, signer):
        self.base, self.signer = base, signer
        self.prefix = httpx.URL(base).path            # "/trade-api/v2", part of what gets signed
        self.c = httpx.Client(timeout=15)

    def call(self, method, path, params=None, body=None):
        for attempt in range(3):
            h = self.signer.headers(method, self.prefix + path)
            h["Content-Type"] = "application/json"
            try:
                r = self.c.request(method, self.base + path, params=params, json=body, headers=h)
            except httpx.HTTPError as e:
                if attempt == 2:
                    raise ApiError(0, str(e))
                time.sleep(1 + attempt); continue
            if r.status_code == 429 or r.status_code >= 500:
                if attempt == 2:
                    raise ApiError(r.status_code, r.text)
                time.sleep(1 + attempt); continue
            if r.status_code >= 400:
                raise ApiError(r.status_code, r.text)
            return r.json() if r.content else {}


def shard_dollars(b, shard):
    """Available balance on one exchange shard, from GET /portfolio/balance's balance_breakdown (None if not given)."""
    for x in b.get("balance_breakdown") or []:
        if int(x.get("exchange_index", -1)) == shard:
            v = x.get("balance_dollars", x.get("balance"))   # documented as a fixed-point dollar string, e.g. "12.3400"
            return float(v) if v is not None else None
    return None


def balance_dollars(b):
    if "balance_dollars" in b:
        return float(b["balance_dollars"])
    if "balance" in b:
        return float(b["balance"]) / 100.0          # cents
    return None


# ---------------- live maker ----------------
class LiveMaker(PaperMaker):
    def __init__(self, a):
        if a.confirm != CONFIRM:
            raise SystemExit(f'Live trading needs the confirmation phrase: "{CONFIRM}"')
        base = HOSTS[a.env]
        pm.API = base                                   # public market data from the same environment
        super().__init__(a)
        key_id, pem = load_keys()
        self.auth = AuthClient(base, Signer(key_id, pem))
        self.my_orders = set()                          # order ids this process placed
        self.live_order = None                          # {"id", "side", "price", "count", "minute", "placed"}
        self.errors = 0
        self.halted = None
        self.balance = None
        self.shard, self.shard_balance = OIL_SHARD, None
        self.last_balance = 0
        self.stop_file = os.path.join(os.path.dirname(os.path.abspath(a.log_dir)), "STOP")
        self.fill_cursor = int(time.time()) - 60
        self.seen_fills = set(st for st in self._load_seen())

    def _load_seen(self):
        p = os.path.join(self.a.log_dir, "fills.jsonl")
        if not os.path.exists(p):
            return []
        out = []
        for line in open(p):
            try:
                out.append(json.loads(line).get("fill_id"))
            except json.JSONDecodeError:
                pass
        return [x for x in out if x]

    # ----- orders -----
    def place(self, side, price, count):
        n = int(math.floor(count + 1e-9))               # whole contracts: works on every market
        body = {"ticker": self.market["ticker"], "client_order_id": str(uuid.uuid4()),
                "side": "bid" if side == "yes" else "ask",
                "price": f"{(price if side == 'yes' else 1 - price):.4f}",
                "count": f"{n}", "time_in_force": "good_till_canceled", "post_only": True,
                "self_trade_prevention_type": "maker", "cancel_order_on_pause": True}
        r = self.auth.call("POST", "/portfolio/events/orders", body=body)
        count = n
        oid = r.get("order_id") or (r.get("order") or {}).get("order_id")
        self.my_orders.add(oid)
        self.live_order = {"id": oid, "ticker": self.market["ticker"], "side": side, "price": price, "count": count,
                           "placed": now().isoformat()}
        self.log(self.f_events, {"ev": "place", "ticker": self.market["ticker"], **self.live_order, "resp": r})
        print(f"[{now():%H:%M:%S}] ORDER buy {side.upper()} {count:.2f} @ {price:.3f}  ({oid})", flush=True)

    def cancel(self, why):
        o = self.live_order
        if not o:
            return
        try:
            self.auth.call("DELETE", f"/portfolio/events/orders/{o['id']}", params={"market_ticker": o["ticker"]})
        except ApiError as e:
            if e.status not in (404, 400):              # already filled / already gone is fine
                raise
        self.log(self.f_events, {"ev": "cancel", "why": why, **o})
        self.live_order = None

    def refresh_balance(self):
        """Total balance, plus the balance on the shard the oil markets trade on (that is what orders draw from)."""
        b = self.auth.call("GET", "/portfolio/balance")
        self.balance = balance_dollars(b)
        if self.market and self.market.get("exchange_index") is not None:
            self.shard = int(self.market["exchange_index"])
        self.shard_balance = shard_dollars(b, self.shard)

    def cancel_all_resting(self, why):
        """Cancel every resting order on this series (start-up clean-up and halts)."""
        try:
            d = self.auth.call("GET", "/portfolio/orders", params={"status": "resting", "limit": 200})
        except ApiError as e:
            print(f"[{now():%H:%M:%S}] could not list resting orders: {e}", flush=True); return
        for o in d.get("orders", []):
            if o.get("ticker", "").startswith(self.a.series + "-"):
                try:
                    self.auth.call("DELETE", f"/portfolio/events/orders/{o['order_id']}", params={"market_ticker": o["ticker"]})
                    self.log(self.f_events, {"ev": "cancel", "why": why, "id": o["order_id"], "ticker": o["ticker"]})
                    print(f"[{now():%H:%M:%S}] cancelled leftover order {o['order_id']} on {o['ticker']}", flush=True)
                except ApiError as e:
                    print(f"[{now():%H:%M:%S}] cancel failed {o['order_id']}: {e}", flush=True)
        self.live_order = None

    def halt(self, reason):
        if not self.halted:
            print(f"[{now():%H:%M:%S}] HALTED: {reason}", flush=True)
            self.log(self.f_events, {"ev": "halt", "why": reason})
        self.halted = reason
        try:
            self.cancel("halt")
        except ApiError:
            pass
        self.cancel_all_resting("halt")

    # ----- fills -----
    def process_trades(self, m):                        # replaces paper fill simulation with REAL fills
        if not self.my_orders and not self.win["fills"]:
            return
        d = self.auth.call("GET", "/portfolio/fills", params={"ticker": m["ticker"], "min_ts": self.fill_cursor - 5, "limit": 200})
        for f in sorted(d.get("fills", []), key=lambda x: x.get("created_time") or ""):
            fid = f.get("fill_id") or f.get("trade_id")
            if fid in self.seen_fills or f.get("order_id") not in self.my_orders:
                continue
            self.seen_fills.add(fid)
            side = f.get("outcome_side") or f.get("side")
            qty = float(f.get("count_fp") or f.get("count"))
            if f.get(f"{side}_price_dollars") is not None:
                price = float(f[f"{side}_price_dollars"])
            else:
                price = float(f.get(f"{side}_price")) / 100.0      # cents
            fee = float(f.get("fee_cost") or 0)
            tt = ts(f["created_time"]) if f.get("created_time") else now()
            self.fill_cursor = max(self.fill_cursor, int(tt.timestamp()))
            self.win["at_risk"] += qty * price + fee
            self.win["side_risk"][side] += qty * price + fee
            self.win["first_side"] = self.win["first_side"] or side
            fill = {"ticker": m["ticker"], "side": side, "price": price, "qty": round(qty, 2), "fee": round(fee, 4),
                    "minute": int((tt - ts(m["open_time"])).total_seconds() // 60) + 1, "trade_time": tt.isoformat(),
                    "fill_id": fid, "order_id": f.get("order_id"), "taker": f.get("is_taker")}
            self.win["fills"].append(fill); self.log(self.f_fills, fill)
            print(f"[{now():%H:%M:%S}] REAL FILL {m['ticker']} bought {side.upper()} {qty:.2f} @ {price:.3f} fee ${fee:.2f} "
                  f"(side {side.upper()} ${self.win['side_risk'][side]:.2f}/{self.side_limit(side):.0f})", flush=True)

    def settle_pending(self):                           # fees are a cost: subtract them from the round's P&L
        for w in self.pending:
            for f in w["fills"]:
                if f.get("fee") and not f.get("_fee_in_price"):
                    f["price"] = f["price"] + f["fee"] / f["qty"] if f["qty"] else f["price"]
                    f["_fee_in_price"] = True
        super().settle_pending()

    # ----- the loop step -----
    def current_market(self):
        if self.market and now() >= ts(self.market["close_time"]) and self.live_order:
            self.live_order = None                      # the market closed; its orders are gone with it
        before = self.win["ticker"] if self.win else None
        m = super().current_market()
        if m and self.win and self.win["ticker"] != before:
            self.restore_window_fills()
        return m

    def restore_window_fills(self):
        """After a restart mid-round, count the real fills already logged for this round toward its caps."""
        p = os.path.join(self.a.log_dir, "fills.jsonl")
        if not os.path.exists(p):
            return
        for line in open(p):
            try:
                f = json.loads(line)
            except json.JSONDecodeError:
                continue
            if f.get("ticker") != self.win["ticker"]:
                continue
            cost = f["qty"] * f["price"] + f.get("fee", 0)
            self.win["fills"].append(f); self.win["at_risk"] += cost; self.win["side_risk"][f["side"]] += cost
            self.win["first_side"] = self.win["first_side"] or f["side"]
            if f.get("order_id"):
                self.my_orders.add(f["order_id"])
        if self.win["fills"]:
            print(f"[{now():%H:%M:%S}] restored {len(self.win['fills'])} earlier fills for {self.win['ticker']} "
                  f"(YES ${self.win['side_risk']['yes']:.2f}, NO ${self.win['side_risk']['no']:.2f})", flush=True)

    def _step(self):
        if os.path.exists(self.stop_file):
            self.halt("STOP file present"); return
        if self.halted:
            return
        if time.time() - self.last_balance > 60:
            try:
                self.refresh_balance()
            except ApiError:
                pass
            self.last_balance = time.time()
        try:
            self._live_step()
            self.errors = 0
        except ApiError as e:
            self.errors += 0 if e.status in (400, 409) else 1
            self.last_error = {"at": now().isoformat(), "msg": str(e)[:300]}
            if e.status not in (400, 409):
                self._step_failed = True
            print(f"[{now():%H:%M:%S}] api error ({self.errors}): {e}", flush=True)
            self.log(self.f_events, {"ev": "error", "msg": str(e)})
            if self.errors >= 5:
                self.halt(f"5 API errors in a row (last: {e})")

    def _live_step(self):
        m = self.current_market()
        if not m:
            return
        minute = int((now() - ts(m["open_time"])).total_seconds() // 60) + 1
        ob = self.api.get(f"/markets/{m['ticker']}/orderbook", {"depth": 10}).get("orderbook_fp", {})
        yes, no = levels(ob.get("yes_dollars")), levels(ob.get("no_dollars"))
        self.process_trades(m)
        want = None
        if yes and no:
            yb, nb = max(yes), max(no)
            mid = (yb + (1 - nb)) / 2
            self.book = {"yes_bid": yb, "yes_ask": round(1 - nb, 4), "minute": minute}
            fav = "yes" if mid >= 0.5 else "no"
            price = yb if fav == "yes" else nb
            # our own resting order is part of the best bid: don't count it as "ahead of us"
            depth = (yes if fav == "yes" else no)[price]
            if self.live_order and self.live_order["side"] == fav and abs(self.live_order["price"] - price) < 1e-9:
                depth = max(0.0, depth - self.live_order["count"])
            if 1 <= minute <= self.a.max_minute and self.a.min_dog <= 1 - price < self.a.max_dog and self.allowed(fav):
                room = self.side_limit(fav) - self.win["side_risk"][fav]
                count = math.floor(min(self.a.per_level, room / price))
                if count >= MIN_CONTRACTS:
                    want = (fav, price, count, depth)
        o = self.live_order
        if o and (not want or o["side"] != want[0] or abs(o["price"] - want[1]) > 1e-9):
            self.cancel("requote" if want else "rules")
            self.process_trades(m)                      # catch anything that filled before the cancel landed
            if want:                                    # re-size with the latest fills
                room = self.side_limit(want[0]) - self.win["side_risk"][want[0]]
                count = math.floor(min(self.a.per_level, room / want[1]))
                want = (want[0], want[1], count, want[3]) if count >= MIN_CONTRACTS else None
        if want and not self.live_order:
            self.place(want[0], want[1], want[2])
        self.order = ({"side": self.live_order["side"], "price": self.live_order["price"], "queue_ahead": want[3] if want else 0,
                       "filled": 0.0, "count": self.live_order["count"], "id": self.live_order["id"]} if self.live_order else None)

    def write_live(self):
        super().write_live()
        p = os.path.join(self.a.log_dir, "live.json")
        try:
            d = json.load(open(p))
        except (OSError, json.JSONDecodeError):
            return
        d.update({"mode": "live", "env": self.a.env, "balance": self.balance, "halted": self.halted,
                  "shard": self.shard, "shard_balance": self.shard_balance, "need": self.a.side_cap})
        tmp = p + ".tmp"
        with open(tmp, "w") as f: json.dump(d, f)
        os.replace(tmp, p)

    def run(self):
        flip = "flip side OFF" if getattr(self.a, "no_flip", False) else f"${(self.a.flip_cap or self.a.side_cap):.0f} flip side"
        if not getattr(self.a, "no_flip", False) and getattr(self.a, "flip_wait", 0):
            flip += f" (only after the flip holds {self.a.flip_wait:.0f}s)"
        print(f"LIVE ({self.a.env}) maker on {self.a.series}: caps ${self.a.side_cap:.0f} first side / "
              f"{flip}, minutes 1-{self.a.max_minute}, max underdog {self.a.max_dog}", flush=True)
        self.refresh_balance()
        print(f"[{now():%H:%M:%S}] account balance ${self.balance} (oil shard {self.shard}: ${self.shard_balance})", flush=True)
        if self.shard_balance is not None and self.shard_balance < self.a.side_cap:
            print(f"[{now():%H:%M:%S}] WARNING: only ${self.shard_balance:.2f} on the oil shard. Orders will be rejected "
                  f"(insufficient_balance) until you move money to it at kalshi.com/account/exchange-indexes", flush=True)
        self.cancel_all_resting("startup")

        def shutdown(*_):
            print(f"[{now():%H:%M:%S}] stopping: cancelling resting order", flush=True)
            try:
                self.cancel("shutdown")
            except Exception:
                pass
            self.cancel_all_resting("shutdown")
            self.save()
            sys.exit(0)
        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGINT, shutdown)
        last_settle = 0
        while True:
            try:
                self.step()
                if time.time() - last_settle > 10:
                    self.settle_pending(); last_settle = time.time()
            except Exception as e:
                print(f"[{now():%H:%M:%S}] error: {e}", flush=True)
            time.sleep(self.a.poll)


def check_keys(env):
    """Read-only test: sign in and read the balance. Places nothing."""
    key_id, pem = load_keys()
    c = AuthClient(HOSTS[env], Signer(key_id, pem))
    b = c.call("GET", "/portfolio/balance")
    return balance_dollars(b), b


def shard_report(b):
    sb = shard_dollars(b, OIL_SHARD)
    if sb is None:
        return ""
    msg = f" (oil markets use shard {OIL_SHARD}: ${sb:,.2f} there)"
    if sb < 15:
        msg += (f". NOT ENOUGH on the oil shard: move money to shard {OIL_SHARD} (Commodities) at "
                f"kalshi.com/account/exchange-indexes or orders will be rejected")
    return msg


def test_order(env, series="KXBRENT15M"):
    """Places ONE tiny real order (buy 1 NO at 1 cent, post-only, so it rests and almost surely never fills),
    then cancels it straight away. Proves Kalshi accepts the bot's orders. Worst case cost: $0.01."""
    key_id, pem = load_keys()
    c = AuthClient(HOSTS[env], Signer(key_id, pem))
    pub = pm.Client()
    ms = pub.get("/markets", {"series_ticker": series, "status": "open", "limit": 5}).get("markets", [])
    if not ms:
        return "no open market right now (oil rounds run Sunday 6 pm to Friday midnight ET), try again then"
    t = ms[0]["ticker"]
    # buy 1 NO at 1 cent == sell 1 YES at 99 cents (post-only, so it rests far from the market)
    body = {"ticker": t, "client_order_id": str(uuid.uuid4()), "side": "ask", "price": "0.9900", "count": "1",
            "time_in_force": "good_till_canceled", "post_only": True, "self_trade_prevention_type": "maker",
            "cancel_order_on_pause": True}
    r = c.call("POST", "/portfolio/events/orders", body=body)
    oid = r.get("order_id")
    c.call("DELETE", f"/portfolio/events/orders/{oid}", params={"market_ticker": t})
    return f"placed and cancelled a 1-contract test order on {t} (remaining {r.get('remaining_count')}, filled {r.get('fill_count')})"
