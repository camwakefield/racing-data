"""Parse a racing.com sectionals CSV into structured per-runner data.

Input format (semicolon-delimited), one file per race:

    <date> ; <meeting-slug> ; <race name>
    HORSE ; number ; m1 ; spd1 ; t1 ; m2 ; spd2 ; t2 ; ...    (one row per runner)

Each (m, spd, t) triple is: cumulative distance-from-start marker (m),
average ground speed over that 200m section (m/s), and the section split time.
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import norm_name, secs, r2, norm_date


def parse_file(path):
    rows = [r for r in csv.reader(open(path), delimiter=";") if any(c.strip() for c in r)]
    if not rows:
        return None
    date = norm_date(rows[0][0])
    meeting_slug = rows[0][1].strip() if len(rows[0]) > 1 else ""
    race_name = rows[0][2].strip() if len(rows[0]) > 2 else ""
    track = meeting_slug.split("-")[0] if meeting_slug else ""

    runners = []
    max_marker = 0
    for r in rows[1:]:
        name = r[0].strip()
        if not name:
            continue
        number = r[1].strip() if len(r) > 1 else ""
        trips = r[2:]
        segs = []
        for i in range(0, len(trips) - 2, 3):
            try:
                marker = int(float(trips[i]))
                spd = float(trips[i + 1])
                t = secs(trips[i + 2])
            except (ValueError, IndexError):
                continue
            segs.append({"m": marker, "spd": spd, "t": t})
        if not segs:
            continue
        segs.sort(key=lambda s: s["m"])
        max_marker = max(max_marker, segs[-1]["m"])
        runners.append({"name": name, "key": norm_name(name), "no": number, "segs": segs})

    distance = max_marker
    for ru in runners:
        valid = [s for s in ru["segs"] if s.get("spd") and s.get("t")]
        ru["no_data"] = len(valid) == 0
        if not valid:
            for k in ("overall_t", "last600_t", "last200_t", "early_t", "top_spd",
                      "close_ratio"):
                ru[k] = None
            continue
        ru["overall_t"] = r2(sum(s["t"] for s in valid))
        last3 = valid[-3:]
        ru["last600_t"] = r2(sum(s["t"] for s in last3))
        ru["last200_t"] = last3[-1]["t"]
        early = valid[:-3]
        ru["early_t"] = r2(sum(s["t"] for s in early)) if early else None
        ru["top_spd"] = r2(max(s["spd"] for s in valid))
        late_sp = [s["spd"] for s in last3]
        early_sp = [s["spd"] for s in early]
        early_mean = (sum(early_sp) / len(early_sp)) if early_sp else 0
        late_mean = (sum(late_sp) / len(late_sp)) if late_sp else 0
        ru["close_ratio"] = r2(late_mean / early_mean) if early_mean else None

    l600 = [ru["last600_t"] for ru in runners if ru["last600_t"]]
    best = min(l600) if l600 else None
    for ru in runners:
        if best and ru["last600_t"]:
            ru["close_rating"] = r2(100.0 * best / ru["last600_t"])
        else:
            ru["close_rating"] = None

    return {
        "date": date,
        "track": track,
        "meeting_slug": meeting_slug,
        "race_name": race_name,
        "distance": distance,
        "source_file": Path(path).name,
        "runners": runners,
    }


def parse_dir(folder):
    out = []
    for p in sorted(Path(folder).glob("*.csv")):
        rec = parse_file(p)
        if rec:
            out.append(rec)
    return out
