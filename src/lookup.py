"""How a consumer (e.g. the Cowork cloud task) reads the store for one horse.

Given a horse name, return a compact recent-form signal summary from the last N
starts — the fastest recent closing rating, whether the last run had an excuse,
any live health caution, and pending gear changes. This is the shape v5 (or a
v5-lite in the cloud task) would turn into features.

Locally:   python3 src/lookup.py "Friendzoned"
In cloud:  WebFetch  data/horses.json  then run this logic on the JSON.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import norm_name

ROOT = Path(__file__).resolve().parent.parent


def summarise(horse, n=3):
    runs = horse.get("runs", [])[:n]
    best_close = None
    last_excuse = 0
    health = False
    gear = False
    faded = False
    for i, r in enumerate(runs):
        s = r.get("sectional")
        if s and s.get("close_rating") is not None:
            best_close = s["close_rating"] if best_close is None else max(best_close, s["close_rating"])
        st = r.get("steward")
        if st:
            if i == 0:
                last_excuse = st.get("excuse_index", 0)
            health = health or st.get("health_flag", False)
            gear = gear or st.get("gear_change", False)
            faded = faded or ("faded" in st.get("flags", []))
    return {
        "name": horse.get("name"),
        "starts_seen": len(horse.get("runs", [])),
        "best_close_rating_recent": best_close,   # 100 = fastest closer in its race
        "last_start_excuse_index": last_excuse,   # >0 = forgive last run
        "health_caution": health,                 # True = needs/needed vet clearance
        "gear_change_flagged": gear,              # blinkers etc. coming
        "faded_recent": faded,
    }


def lookup(name, store_path=None):
    store_path = store_path or (ROOT / "data" / "horses.json")
    horses = json.load(open(store_path))
    key = norm_name(name)
    horse = horses.get(key)
    if not horse:
        return {"name": name, "found": False}
    out = summarise(horse)
    out["found"] = True
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('usage: python3 src/lookup.py "Horse Name"')
        sys.exit(0)
    print(json.dumps(lookup(" ".join(sys.argv[1:])), indent=1))
