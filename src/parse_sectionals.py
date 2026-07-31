"""Parse a racing.com sectionals CSV into structured per-runner data.

Input format (semicolon-delimited), one file per race:

    <date> ; <meeting-slug> ; <race name>
    HORSE ; number ; m1 ; spd1 ; t1 ; m2 ; spd2 ; t2 ; ...    (one row per runner)

Each (m, spd, t) triple is: cumulative distance-from-start marker (m),
average ground speed over that 200m section (m/s), and the section split time.

Derived per runner:
  - overall_t     : sum of all split times (the horse's running time)
  - last600_t     : sum of the final three 200m splits
  - last200_t     : the final 200m split
  - early_t       : sum of splits before the final 600m
  - top_spd       : peak section speed
  - close_ratio   : last600 speed / early speed  (>1 = quickened late; <1 = faded)

Per race we add a field-relative closing rating so a horse can be compared to
the pace it actually ran against:
  - close_rating  : 100 * (race best last600_t) / (this horse's last600_t)
                    100 = fastest closer in the race; 95 = ~5% slower, etc.
"""
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import norm_name, secs, r2, norm_date, clean_track


# "Sportsbet-Ballarat Synthetic-Professional-2026-07-14" ->
#   track slug "Sportsbet-Ballarat Synthetic", date "2026-07-14"
_SLUG = re.compile(r"^(?P<track>.+)-(?P<grade>[A-Za-z ]+)-(?P<date>\d{4}-\d{2}-\d{2})$")


def parse_file(path):
    rows = [r for r in csv.reader(open(path), delimiter=";") if any(c.strip() for c in r)]
    if not rows:
        return None
    meeting_slug = rows[0][1].strip() if len(rows[0]) > 1 else ""
    race_name = rows[0][2].strip() if len(rows[0]) > 2 else ""

    # The meeting slug carries an unambiguous ISO date and the full track name.
    # Column 0 does not: older exports write it in US M/D/YYYY order, so
    # "6/13/2026" would otherwise be read as month 13. Trust the slug; fall back
    # to column 0 only if the slug is missing or malformed.
    m = _SLUG.match(meeting_slug)
    if m:
        date = m.group("date")
        track = clean_track(m.group("track"))
    else:
        date = norm_date(rows[0][0])
        track = clean_track(meeting_slug.split("-")[0]) if meeting_slug else ""

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

    # distance = furthest marker reached in the field
    distance = max_marker
    for ru in runners:
        # A GPS-less runner has every section as speed 0 / time 0:00.00 — drop
        # those sections so it just gets null sectional metrics (it still exists
        # as a run, we just have no speed data for it).
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
        # quickened-vs-faded: mean section speed over final 600 vs earlier
        late_sp = [s["spd"] for s in last3]
        early_sp = [s["spd"] for s in early]
        early_mean = (sum(early_sp) / len(early_sp)) if early_sp else 0
        late_mean = (sum(late_sp) / len(late_sp)) if late_sp else 0
        ru["close_ratio"] = r2(late_mean / early_mean) if early_mean else None

    # field-relative closing rating
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


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "raw/sectionals"
    p = Path(target)
    recs = [parse_file(p)] if p.is_file() else parse_dir(p)
    for rec in recs:
        print("== %s  %s  %s  (%dm, %d runners)" % (
            rec["date"], rec["track"], rec["race_name"], rec["distance"], len(rec["runners"])))
        ranked = sorted([r for r in rec["runners"] if r["last600_t"]], key=lambda r: r["last600_t"])
        for r in ranked:
            print("   %-20s no%-3s L600 %5.2f  L200 %5.2f  close_rating %5.1f  close_ratio %s"
                  % (r["name"], r["no"], r["last600_t"], r["last200_t"] or 0,
                     r["close_rating"] or 0, r["close_ratio"]))
    print(json.dumps(recs)[:0])  # keep import side-effect free
