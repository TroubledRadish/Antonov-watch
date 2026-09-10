#!/usr/bin/env python3
"""Watch one aircraft on adsb.fi and push a phone notification when its
transponder shows up in ADS-B coverage (i.e. it "turns on").

Standard library only - no pip install needed. Works the same when run
locally or inside GitHub Actions; everything is driven by env vars:

  ADSB_HEX     ICAO hex to watch            (default 50801b)
  NTFY_TOPIC   ntfy.sh topic to publish to  (required for notifications)
  NTFY_SERVER  ntfy server                  (default https://ntfy.sh)
  STATE_FILE   where to persist state       (default state.json)
  CLEAR_AFTER  consecutive misses before the alert re-arms (default 3)

Data: adsb.fi (https://adsb.fi) - personal, non-commercial use.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

HEX = os.environ.get("ADSB_HEX", "50801b").lower()
NTFY_SERVER = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "").strip()
STATE_FILE = os.environ.get("STATE_FILE", "state.json")
CLEAR_AFTER = int(os.environ.get("CLEAR_AFTER", "3"))

API = f"https://opendata.adsb.fi/api/v2/hex/{HEX}"
GLOBE = f"https://globe.adsb.fi/?icao={HEX}"
UA = "antonov-watch/1.0 (personal, non-commercial; data: adsb.fi)"


def log(*parts):
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(stamp, *parts, flush=True)


def fetch():
    req = urllib.request.Request(API, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"status": "off", "misses": 0, "last_change": None}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def notify(ac):
    if not NTFY_TOPIC:
        log("NTFY_TOPIC not set - would have sent a notification. Aircraft is UP.")
        return

    callsign = (ac.get("flight") or "").strip() or "(no callsign)"

    alt = ac.get("alt_baro")
    if alt == "ground":
        alt_s = "on ground"
    elif isinstance(alt, (int, float)):
        alt_s = f"{alt} ft"
    else:
        alt_s = "n/a"

    gs = ac.get("gs")
    gs_s = f"{gs} kt" if isinstance(gs, (int, float)) else "n/a"

    lat, lon = ac.get("lat"), ac.get("lon")
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
        pos_s = f"{lat:.3f}, {lon:.3f}"
    else:
        pos_s = "unknown"

    body = (
        f"Antonov {HEX.upper()} transponder is ON.\n"
        f"Callsign: {callsign}\n"
        f"Altitude: {alt_s}\n"
        f"Ground speed: {gs_s}\n"
        f"Position: {pos_s}"
    )

    req = urllib.request.Request(
        f"{NTFY_SERVER}/{NTFY_TOPIC}",
        data=body.encode("utf-8"),
        headers={
            "User-Agent": UA,
            "Title": f"Antonov {HEX.upper()} is transmitting",
            "Priority": "high",
            "Tags": "airplane",
            "Click": GLOBE,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        log("ntfy responded", resp.status)


def main():
    state = load_state()

    try:
        payload = fetch()
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
        log("fetch failed, leaving state unchanged:", err)
        return 0

    ac_list = payload.get("ac") or []
    seen = len(ac_list) > 0
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if seen:
        if state.get("status") != "on":
            log(f"{HEX} TURNED ON -> notifying")
            notify(ac_list[0])
            state = {"status": "on", "misses": 0, "last_change": now_iso}
        else:
            log(f"{HEX} still on")
            state["misses"] = 0
    else:
        if state.get("status") == "on":
            state["misses"] = state.get("misses", 0) + 1
            log(f"{HEX} not seen ({state['misses']}/{CLEAR_AFTER})")
            if state["misses"] >= CLEAR_AFTER:
                log(f"{HEX} treated as OFF again - alert re-armed")
                state = {"status": "off", "misses": 0, "last_change": now_iso}
        else:
            log(f"{HEX} still off")
            state["misses"] = 0

    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
