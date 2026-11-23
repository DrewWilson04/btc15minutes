#!/usr/bin/env python3
"""Paper market-maker for Kalshi 15-minute oil markets (default: KXBRENT15M).

Strategy (from oil_analysis/FINDINGS.md):
  * minutes 1..MAX_MINUTE of each window, the favourite = side with mid >= 0.50
  * keep ONE virtual resting buy order on the favourite at the current best bid
    (i.e. we offer the underdog); cancel/replace whenever the best bid moves
  * fills: we join the BACK of the queue at our price. Live taker trades that hit our
    level (or sweep through it) first consume the queue that was ahead of us, then fill us
  * hold every fill to settlement; maker fee = 0 on these series
  * optional risk caps (off by default): $ at risk per window, daily stop

No order is ever sent: only public, unauthenticated GET endpoints are used.
"""
import argparse, datetime as dt, json, math, os, sys, time
import httpx
try:
    from zoneinfo import ZoneInfo
    NY = ZoneInfo("America/New_York")
except Exception:                                    # no tz database: fall back to US Eastern standard time
    NY = dt.timezone(dt.timedelta(hours=-5))


def parse_hours(h):
    """'11-18' -> (11, 18): trade rounds that START from 11:00 up to 17:59 ET. Empty/None -> None (all hours)."""
    if not h:
        return None
    a, b = str(h).split("-")
    return int(a), int(b)

API = "https://api.elections.kalshi.com/trade-api/v2"
UTC = dt.timezone.utc


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def now():
    return dt.datetime.now(UTC)


class Client:
    def __init__(self):
        self.c = httpx.Client(timeout=15)

    def get(self, path, params=None):
        code = None
        for attempt in range(8):
            try:
                r = self.c.get(API + path, params=params)
                code = r.status_code
                if code in (429, 500, 502, 503, 504):
                    time.sleep(min(8, 0.7 * 2 ** attempt)); continue
                r.raise_for_status()
                return r.json()
            except httpx.HTTPError as e:
                code = str(e); time.sleep(min(8, 0.7 * 2 ** attempt))
        raise RuntimeError(f"GET {path} failed ({code})")


def levels(side):
    """orderbook side -> {price: size}"""
    return {round(float(p), 4): float(q) for p, q in (side or [])}


class PaperMaker:
    def __init__(self, a):
        self.a = a
        self.api = Client()
        os.makedirs(a.log_dir, exist_ok=True)
        self.f_fills = open(os.path.join(a.log_dir, "fills.jsonl"), "a")
        self.f_windows = open(os.path.join(a.log_dir, "windows.jsonl"), "a")
        self.f_events = open(os.path.join(a.log_dir, "events.jsonl"), "a")
        self.state_path = os.path.join(a.log_dir, "state.json")
        st = json.load(open(self.state_path)) if os.path.exists(self.state_path) else {}
        self.total = st.get("total", 0.0)
        self.day = st.get("day", str(now().astimezone(dt.timezone(dt.timedelta(hours=-5))).date()))
        self.day_pnl = st.get("day_pnl", 0.0)
        self.wins, self.losses = st.get("wins", 0), st.get("losses", 0)
        self.pending = st.get("pending", [])          # windows awaiting settlement
        self.market = None
        self.order = None                              # {side, price, queue_ahead, placed}
        self.win = None                                # current window bookkeeping
        self.seen = set()

    # ---------- persistence / logging ----------
    def save(self):
        json.dump({"total": self.total, "day": self.day, "day_pnl": self.day_pnl, "wins": self.wins,
                   "losses": self.losses, "pending": self.pending}, open(self.state_path, "w"), indent=1)

    def log(self, f, rec):
        rec["ts"] = now().isoformat(); f.write(json.dumps(rec) + "\n"); f.flush()

    # ---------- market discovery ----------
    def current_market(self):
        if self.market and now() < ts(self.market["close_time"]):
            return self.market
        if self.win:
            self.close_window()
        ms = self.api.get("/markets", {"series_ticker": self.a.series, "status": "open", "limit": 5})["markets"]
        ms = [m for m in ms if ts(m["open_time"]) <= now() < ts(m["close_time"])]
        if not ms:
            self.market = None; return None
        self.market = ms[0]; self.order = None
        self.win = {"ticker": self.market["ticker"], "open": self.market["open_time"],
                    "close": self.market["close_time"], "fills": [], "at_risk": 0.0, "side_risk": {"yes": 0.0, "no": 0.0}, "first_side": None}
        self.trade_cursor = ts(self.market["open_time"])
        print(f"[{now():%H:%M:%S}] new window {self.market['ticker']}", flush=True)
        return self.market

    def close_window(self):
        if self.win["fills"]:
            self.pending.append(self.win)
        print(f"[{now():%H:%M:%S}] window {self.win['ticker']} closed with "
              f"{sum(f['qty'] for f in self.win['fills']):.0f} contracts", flush=True)
        self.win = None; self.order = None; self.save()

    # ---------- settlement ----------
    def settle_pending(self):
        still = []
        for w in self.pending:
            m = self.api.get(f"/markets/{w['ticker']}")["market"]
            res = m.get("result")
            if res not in ("yes", "no"):
                still.append(w); continue
            pnl = sum(f["qty"] * ((1 - f["price"]) if f["side"] == res else -f["price"]) for f in w["fills"])
            qty = sum(f["qty"] for f in w["fills"])
            self.roll_day()
            self.total += pnl; self.day_pnl += pnl
            self.wins += pnl > 0; self.losses += pnl < 0
            self.log(self.f_windows, {"ticker": w["ticker"], "result": res, "contracts": qty, "pnl": round(pnl, 4),
                                      "total": round(self.total, 2), "day_pnl": round(self.day_pnl, 2)})
            print(f"[{now():%H:%M:%S}] SETTLED {w['ticker']} result={res} contracts={qty:.0f} "
                  f"pnl=${pnl:+.2f} | day ${self.day_pnl:+.2f} | total ${self.total:+.2f} "
                  f"({self.wins}W/{self.losses}L windows)", flush=True)
        self.pending = still; self.save()

    def roll_day(self):
        d = str(now().astimezone(dt.timezone(dt.timedelta(hours=-5))).date())
        if d != self.day:
            self.day, self.day_pnl = d, 0.0

    # ---------- risk ----------
    def open_risk(self):
        return sum(f["qty"] * f["price"] for w in self.pending for f in w["fills"]) + (self.win["at_risk"] if self.win else 0)

    def side_limit(self, side):
        first = self.win["first_side"]
        if first not in (None, side) and getattr(self.a, "no_flip", False):
            return 0.0                                  # flip turned off: never buy the other side
        return self.a.side_cap if first in (None, side) or not self.a.flip_cap else self.a.flip_cap

    def in_hours(self):
        hrs = parse_hours(getattr(self.a, "hours", None))
        if not hrs or not self.market:
            return True
        h = ts(self.market["open_time"]).astimezone(NY).hour       # by when the round STARTED (as in the backtest)
        a, b = hrs
        return a <= h < b if a < b else (h >= a or h < b)          # also allows windows that wrap past midnight

    def allowed(self, side=None):
        self.roll_day()
        if not self.in_hours():
            return False
        if self.a.day_stop and self.day_pnl - (self.open_risk() if self.a.count_open_risk else 0) <= -self.a.day_stop:
            return False
        if self.a.window_cap and self.win["at_risk"] >= self.a.window_cap:
            return False
        if side and (self.a.side_cap or getattr(self.a, "no_flip", False)) and self.win["side_risk"][side] >= self.side_limit(side):
            return False
        wait = float(getattr(self.a, "flip_wait", 0) or 0)
        first = self.win["first_side"] if self.win else None
        if side and wait and first and side != first:
            # flip safety: only buy the other side once the flip has lasted `wait` seconds (since it was first seen
            # inside the rules this round). A quick flip-and-flip-back never gets the flip side bought.
            seen = self.win.get("flip_seen")
            if not seen:
                self.win["flip_seen"] = seen = now().isoformat()
            if (now() - ts(seen)).total_seconds() < wait:
                return False
        return True

    # ---------- main step ----------
    def step(self):
        self.book = None
        self._step_failed = False
        try:
            self._step()
            if not self._step_failed:
                self.last_ok = now().isoformat()
        except Exception as e:
            self.last_error = {"at": now().isoformat(), "msg": str(e)[:300]}
            raise
        finally:
            self.write_live()

    def write_live(self):
        """Small status file for the local dashboard (logs/<name>/live.json)."""
        m, w = self.market, self.win
        live = {"ts": now().isoformat(), "series": self.a.series, "market": m["ticker"] if m else None,
                "open": m["open_time"] if m else None, "close": m["close_time"] if m else None,
                "book": self.book, "order": self.order,
                "window": {"at_risk": round(w["at_risk"], 2), "side_risk": w.get("side_risk"), "first_side": w.get("first_side"),
                           "contracts": round(sum(f["qty"] for f in w["fills"]), 2)} if w else None,
                "mode": "paper", "pid": os.getpid(), "last_ok": getattr(self, "last_ok", None),
                "last_error": getattr(self, "last_error", None),
                "rules": {"max_minute": self.a.max_minute, "max_dog": self.a.max_dog, "side_cap": self.a.side_cap,
                          "flip_cap": self.a.flip_cap, "per_level": self.a.per_level,
                          "no_flip": bool(getattr(self.a, "no_flip", False)),
                          "flip_wait": float(getattr(self.a, "flip_wait", 0) or 0),
                          "hours": getattr(self.a, "hours", None) or None, "in_hours": self.in_hours()}}
        tmp = os.path.join(self.a.log_dir, "live.json.tmp")
        with open(tmp, "w") as f: json.dump(live, f)
        os.replace(tmp, os.path.join(self.a.log_dir, "live.json"))

    def _step(self):
        m = self.current_market()
        if not m:
            return
        minute = int((now() - ts(m["open_time"])).total_seconds() // 60) + 1
        ob = self.api.get(f"/markets/{m['ticker']}/orderbook", {"depth": 10}).get("orderbook_fp", {})
        yes, no = levels(ob.get("yes_dollars")), levels(ob.get("no_dollars"))
        self.process_trades(m)                   # fills against the order that was resting
        if not yes or not no:
            self.order = None; return
        yb, nb = max(yes), max(no)
        mid = (yb + (1 - nb)) / 2
        self.book = {"yes_bid": yb, "yes_ask": round(1 - nb, 4), "minute": minute}
        fav = "yes" if mid >= 0.5 else "no"
        price = yb if fav == "yes" else nb
        depth = (yes if fav == "yes" else no)[price]
        dog_px = 1 - price
        ok = (1 <= minute <= self.a.max_minute and self.a.min_dog <= dog_px < self.a.max_dog and self.allowed(fav))
        if not ok:
            if self.order: self.log(self.f_events, {"ev": "cancel", "why": "filter", "minute": minute, **self.order})
            self.order = None; return
        if not self.order or self.order["side"] != fav or abs(self.order["price"] - price) > 1e-9:
            self.order = {"side": fav, "price": price, "queue_ahead": depth, "filled": 0.0,
                          "placed": now().isoformat(), "minute": minute}
            self.log(self.f_events, {"ev": "quote", "ticker": m["ticker"], **self.order})

    def process_trades(self, m):
        d = self.api.get("/markets/trades", {"ticker": m["ticker"], "limit": 1000,
                                              "min_ts": int(self.trade_cursor.timestamp()) - 2})
        trades = sorted(d.get("trades", []), key=lambda t: t["created_time"])
        for t in trades:
            if t["trade_id"] in self.seen: continue
            self.seen.add(t["trade_id"])
            tt = ts(t["created_time"]); self.trade_cursor = max(self.trade_cursor, tt)
            o = self.order
            if not o or tt <= ts(o["placed"]): continue
            yp = float(t.get("yes_price_dollars") or t.get("yes_price"))
            qty = float(t.get("count_fp") or t.get("count"))
            taker = t.get("taker_outcome_side") or t.get("taker_side")
            # our favourite bid is hit when a taker buys the OTHER side at our level or worse for them
            if o["side"] == "yes":
                hit = taker == "no" and yp <= o["price"] + 1e-9
            else:
                hit = taker == "yes" and (1 - yp) <= o["price"] + 1e-9
            if not hit: continue
            eat = min(qty, o["queue_ahead"]); o["queue_ahead"] -= eat; qty -= eat
            room = self.a.per_level - o["filled"]
            if self.a.window_cap:
                room = min(room, max(0.0, (self.a.window_cap - self.win["at_risk"]) / o["price"]))
            if self.a.side_cap:
                room = min(room, max(0.0, (self.side_limit(o["side"]) - self.win["side_risk"][o["side"]]) / o["price"]))
            f = min(qty, room)
            if f <= 0: continue
            o["filled"] += f; self.win["at_risk"] += f * o["price"]; self.win["side_risk"][o["side"]] += f * o["price"]
            self.win["first_side"] = self.win["first_side"] or o["side"]
            fill = {"ticker": m["ticker"], "side": o["side"], "price": o["price"], "qty": round(f, 2),
                    "minute": int((tt - ts(m["open_time"])).total_seconds() // 60) + 1, "trade_time": t["created_time"]}
            self.win["fills"].append(fill); self.log(self.f_fills, fill)
            print(f"[{now():%H:%M:%S}] FILL {m['ticker']} bought {o['side'].upper()} {f:.0f} @ {o['price']:.3f} "
                  f"(min {fill['minute']}, window at risk ${self.win['at_risk']:.0f})", flush=True)

    def run(self):
        print(f"paper maker on {self.a.series}: minutes 1-{self.a.max_minute}, {self.a.per_level:.0f}/level, "
              f"window cap {self.a.window_cap or 'off'}, side cap {self.a.side_cap or 'off'} (flip side {self.a.flip_cap or 'same'}), day stop {self.a.day_stop or 'off'}  "
              f"| total so far ${self.total:+.2f}", flush=True)
        last_settle = 0
        while True:
            try:
                self.step()
                if time.time() - last_settle > 10:
                    self.settle_pending(); last_settle = time.time()
            except Exception as e:
                print(f"[{now():%H:%M:%S}] error: {e}", flush=True)
            time.sleep(self.a.poll)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--series", default="KXBRENT15M")
    p.add_argument("--max-minute", type=int, default=12)
    p.add_argument("--per-level", type=float, default=50)
    p.add_argument("--min-dog", type=float, default=0.0, help="only quote when underdog price >= this")
    p.add_argument("--max-dog", type=float, default=0.5, help="only quote when underdog price < this")
    p.add_argument("--window-cap", type=float, default=0, help="max $ at risk per window (0 = off)")
    p.add_argument("--side-cap", type=float, default=0, help="max $ put in per side (YES / NO) per window (0 = off)")
    p.add_argument("--flip-cap", type=float, default=0, help="$ cap for the side bought AFTER the first side in a window (0 = same as --side-cap)")
    p.add_argument("--day-stop", type=float, default=0, help="stop for the day at this loss (0 = off)")
    p.add_argument("--count-open-risk", action="store_true", help="count unsettled positions as lost for the day stop")
    p.add_argument("--poll", type=float, default=1.5)
    p.add_argument("--log-dir", default="logs/paper")
    PaperMaker(p.parse_args()).run()
