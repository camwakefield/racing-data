"""Parse a racing.com sectionals CSV into structured per-runner data.

Input format (semicolon-delimited), one file per race:

    <date> ; <meeting-slug> ; <race name>
    HORSE ; number ; m1 ; spd1 ; t1 ; m2 ; spd2 ; t2 ; ...    (one row per runner)

Each (m, spd, t) triple is: cumulative distance-from-start marker (m), a ground
speed reading for that section (m/s), and the section split time.

WHAT THE spd COLUMN IS -- AND IS NOT.  It is a PEAK (or terminal) reading inside
the section, not the section mean.  Measured across all 196 files: spd * t comes
out ~28% above the nominal section length over the first section from the
barriers, ~5% over the final 200m and ~2.5% mid-race.  A horse cannot cover 256m
inside the first 200m, so the product is not a path length -- that U-shape is
exactly what a peak reading produces (speed varies most at the start and at the
finish).  Two consequences:
  * There is NO distance-covered / raced-wide signal recoverable from this feed.
  * Any early-vs-late speed comparison must use section_length / t, not spd.
    The old close_ratio used spd and so was biased low for every runner: the
    first section's peak inflated the "early" side of the ratio.  spd is still
    the right source for top_spd, which genuinely wants a peak.

Derived per runner:
  - overall_t     : sum of all split times (the horse's running time)
  - last600_t     : sum of the final three 200m splits
  - last200_t     : the final 200m split
  - early_t       : sum of splits before the final 600m
  - top_spd       : peak section speed (from the spd column -- a peak is wanted)
  - close_ratio   : mean last-600 section speed / mean earlier section speed,
                    both computed as section_length / t.  >1 = quickened late.
                    Runs ~0.046 higher than the old spd-based version and
                    correlates +0.85 with it, so a consumer's gate has to move
                    with it: the old 0.95 cut sits at 1.00 on this scale.

Per race we add field-relative figures so a horse can be compared to the race it
actually ran in:
  - close_rating  : 100 * (race best last600_t) / (this horse's last600_t)
                    100 = fastest closer in the race; 95 = ~5% slower, etc.
  - early_pct     : where the horse sat at the last marker before the 600m, as a
                    percentile of the field. 100 = leading, 0 = last, 50 = midfield.
  - lens_off_600  : lengths behind the leader at that same point (2.4m/length).

early_pct / lens_off_600 are only valid because every runner in a race shares one
marker grid and one start gun, so cumulative split times are directly comparable
across the field -- i.e. position-in-running is reconstructible from the CSV with
no extra source.  Where the grid is NOT uniform, or the race is too short to have
a marker before the 600m, both fields are None rather than guessed.
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


LENGTH_M = 2.4          # one "length" in metres, the standard Australian figure
MIN_FIELD = 5           # below this a percentile of the field means very little


def _early_position(runners, distance):
    """Reconstruct where each runner sat before the turn for home.

    Every runner in a race is timed off the same start over the same marker
    grid, so cumulative split times ARE comparable across the field -- this is
    position-in-running, recovered from the CSV with no second source.

    The read point is the last marker at or before (distance - 600), i.e. the
    latest point that is still 'before the sprint home'. Sets, per runner:
      early_pct    100 = led the field there, 0 = last, 50 = midfield
      lens_off_600 lengths behind the leader at that point
    Both are None when the grid is not uniform across the field, when the race
    is too short to have such a marker, or when the field is too small.
    """
    for ru in runners:
        ru["early_pct"] = None
        ru["lens_off_600"] = None

    live = [ru for ru in runners if ru.get("_cum")]
    if len(live) < MIN_FIELD:
        return
    grids = set(ru["_grid"] for ru in live)
    if len(grids) != 1:
        # Mixed grids mean the markers are not the same physical points for
        # every runner, so cross-runner time comparison is meaningless. Say
        # nothing rather than emit a number that looks authoritative.
        print("  NOTE  mixed marker grids - no early position for this race",
              file=sys.stderr)
        return
    grid = sorted(grids.pop())
    before = [m for m in grid if m <= distance - 600]
    if not before:
        return
    sp = before[-1]

    tab = [(ru["_cum"][sp], ru) for ru in live if sp in ru["_cum"]]
    if len(tab) < MIN_FIELD:
        return
    tab.sort(key=lambda x: x[0])
    lead, n = tab[0][0], len(tab)
    for i, (t_sp, ru) in enumerate(tab):
        ru["early_pct"] = r2(100.0 * (1.0 - i / (n - 1)))
        # gap in lengths = time gap x the speed being run there / metres per length
        ru["lens_off_600"] = r2((t_sp - lead) * (sp / t_sp) / LENGTH_M)


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
        ru["_grid"] = tuple(s["m"] for s in valid)
        cum, acc = {}, 0.0
        for s in valid:
            acc += s["t"]
            cum[s["m"]] = acc
        ru["_cum"] = cum
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
        # quickened-vs-faded. Mean section speed = section_length / split time.
        # NOT the spd column: see the module docstring -- that is a peak, and
        # using it drags the early side up and every close_ratio down.
        prev_m, mean_sp = 0, []
        for s in valid:
            nominal = s["m"] - prev_m
            prev_m = s["m"]
            mean_sp.append((nominal / s["t"]) if (nominal > 0 and s["t"]) else None)
        early_sp = [x for x in mean_sp[:-3] if x]
        late_sp = [x for x in mean_sp[-3:] if x]
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

    _early_position(runners, distance)
    for ru in runners:                      # scratch fields, not part of the record
        ru.pop("_cum", None)
        ru.pop("_grid", None)

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
    """Every *.csv under `folder`, recursively and case-insensitively.

    The old version globbed "*.csv" in one directory only. Linux globs are
    case-sensitive, so a file saved as ".CSV" — or dropped in a subfolder —
    was skipped without a word. Anything ignored is now printed.
    """
    out = []
    folder = Path(folder)
    if not folder.exists():
        print("  SKIP  %s does not exist" % folder, file=sys.stderr)
        return out
    for p in sorted(folder.rglob("*")):
        if p.is_dir() or p.name.startswith("."):
            continue
        if p.suffix.lower() != ".csv":
            print("  SKIP  %-55s unrecognised extension %r"
                  % (p.relative_to(folder), p.suffix or "(none)"), file=sys.stderr)
            continue
        try:
            rec = parse_file(p)
        except Exception as exc:
            print("  ERROR %-55s %s: %s" % (p.name, type(exc).__name__, exc),
                  file=sys.stderr)
            continue
        if rec and rec["runners"]:
            out.append(rec)
        else:
            print("  EMPTY %-55s no runners parsed" % p.name, file=sys.stderr)
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
            pos = ("%3.0f%%  %4.1fL back" % (r["early_pct"], r["lens_off_600"])
                   if r["early_pct"] is not None else "   -            ")
            print("   %-20s no%-3s L600 %5.2f  L200 %5.2f  close_rating %5.1f  "
                  "close_ratio %-5s  early %s"
                  % (r["name"], r["no"], r["last600_t"], r["last200_t"] or 0,
                     r["close_rating"] or 0, r["close_ratio"], pos))
    print(json.dumps(recs)[:0])  # keep import side-effect free
