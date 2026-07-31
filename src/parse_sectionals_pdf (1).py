"""Parse a racing.com sectionals PDF -- the long-form report behind the CSV.

The CSV feed gives (marker, spd, split) triples and nothing else. The PDF that
accompanies the same race carries a great deal the CSV does not, and two things
in particular that this data store has never had at all:

  * THE RESULT. Final finishing rank and beaten margin. Every grade in the
    system today leans on close_rating precisely because no results were banked.
  * WHERE THE HORSE RAN. "Avg. Dist. to Rail [m]" per 200m section, and a
    signed "Distance Travelled [m]" figure. This is the raced-wide signal I
    previously said was unrecoverable -- true of the CSV, not true of the PDF.

Plus: barrier, jockey, per-section rank, per-section TRUE mean speed (km/h --
unlike the CSV's spd column, which is a peak), per-section top speed, stride
frequency and stride length, race state (Finished / DNF / DNT), the track
rating / weather / rail position, and the scratched list.

That last one matters more than it looks. The store currently banks scratched
horses as starts, because a scratching still appears in the CSV with an all-zero
trace. The PDF names them outright, so a run can be marked scratched from
evidence instead of inferred from missing data.

COVERAGE IS PARTIAL AND ALWAYS WILL BE. Not every meeting has a PDF. Every field
this module produces is therefore optional: a meeting with no PDF must look
exactly as it does today, and nothing downstream may require a PDF field.

LAYOUT. `pdftotext -layout` output, one form feed per page:

  pages 1..k   summary table, ~10 runners per page, two text lines each. The
               table is split ACROSS pages by section group, so the same runner
               appears on every summary page with different columns. One of
               those pages carries Margin; the last column is Distance Travelled.
  pages k+1..n one detail page per runner: a labelled header block, then a
               section table (Section Times / Average Speed / Top Speed /
               Avg. Dist. to Rail / Avg. Stride Freq. / Avg. Stride Length),
               then two charts.

The charts repeat the same numbers and reuse the same axis titles, so every
value row is matched on "label followed by two or more numbers on ONE line" and
only the FIRST match per page is taken -- the table always precedes its chart.

SECTION TIMES READ BACKWARDS FROM THE LINE. Under the "1200m" column, 1:11.16 is
the time from the 1200m-to-go mark to the finish, not the time to reach it. The
bracketed figure below is the split for the section just completed. Both are
kept: `to_finish` and `split`.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import norm_name, secs, r2, clean_track


LENGTH_M = 2.4

_MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}

# "Race 1: TAB We're On - 1420m"   (race names contain dashes, so anchor on the
# distance at the end rather than splitting on the first dash)
_RACE = re.compile(r"^\s*Race\s+(\d+)\s*:\s*(.+?)\s*[-\u2013]\s*(\d+)\s*m\s*$")
_DATE = re.compile(r"^\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\s*(?:-\s*(\d{1,2}:\d{2}))?\s*$")
_COND = re.compile(r"Track Rating:\s*(?P<rating>[^,]+?)\s*,\s*"
                   r"Weather:\s*(?P<weather>[^,]+?)\s*,\s*"
                   r"Rail Position:\s*(?P<rail>.+?)\s*$")
# "FlemingtonProfessional" -> venue + grade, glued together by the layout
_GRADE = re.compile(r"^(?P<track>.*[a-z\)])(?P<grade>Professional|Amateur|Country|"
                    r"Provincial|Metropolitan|Trial|Jumpout|Picnic)\s*$")
# Fallback for a grade word not on that list: any lower->upper join. On its own
# that would happily match stray body text, so it is only trusted for a short
# line that repeats on two or more pages -- which is what a page header is.
_GLUED = re.compile(r"^(?P<track>[A-Z][A-Za-z'\-\. ]*[a-z\)])(?P<grade>[A-Z][a-z]+)\s*$")

_SCRATCH = re.compile(r"([A-Za-z][A-Za-z'\-\. ]+?)\s*\(#(\d+)\)")

# summary line 1: rank, saddlecloth, horse, barrier, top speed, fastest section
_SUM1 = re.compile(r"^\s*(\d{1,2})\s+(\d{1,2})\s+"
                   r"(?P<horse>\S.*?)\s{2,}"
                   r"(?P<barrier>\d{1,2})\s+"
                   r"(?P<top>\d{2,3}\.\d)\s+"
                   r"(?P<fast>\d:\d{2}\.\d{2}|NA|-:--\.--)\s+"
                   r"(?P<rest>.*)$")
_SUM2 = re.compile(r"^\s{4,}(?P<jockey>[A-Za-z][A-Za-z'\-\.]*(?: [A-Za-z'\-\.]+)*)"
                   r"\s{2,}(?:Overall|\d+m|NA)\b")

_TRAVEL = re.compile(r"([+-]\d+)\s*$")
_MARGIN = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*L(?![A-Za-z])")

_TIMED = re.compile(r"(\d+:\d{2}\.\d{2}|-:--\.--|NA)\s*\[\s*(\d+|NA|-)\s*\]")
_PAREN = re.compile(r"\((\d+:\d{2}\.\d{2}|-:--\.--|NA)\)")
_NUM = re.compile(r"(?<![\w.])(-?\d+(?:\.\d+)?)(?![\w.])")

_LABEL = "Horse/Jockey Name"


def pdf_text(path):
    """pdftotext -layout, falling back to pdfplumber where poppler is absent."""
    try:
        return subprocess.run(["pdftotext", "-layout", str(path), "-"],
                              capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            return "\f".join((pg.extract_text() or "") for pg in pdf.pages)


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _rank(tok):
    return int(tok) if tok and tok.isdigit() else None


def _t(tok):
    """Split/section time, or None for the '-:--.--' / 'NA' no-data markers."""
    if not tok or tok in ("NA", "-:--.--"):
        return None
    return secs(tok)


def _labels(line):
    """The section header row -> ['overall','1200','1000',...].

    'Last 600m' is a summary, not a marker; it is dropped so the label list
    lines up with the value rows that follow.
    """
    rest = line.split("Section", 1)[1]
    rest = re.sub(r"Last\s+600m\s*$", "", rest)
    out = []
    for tok in rest.split():
        if tok.lower() == "overall":
            out.append("overall")
        elif re.fullmatch(r"\d+m", tok):
            out.append(tok[:-1])
    return out


def _row(lines, label, n):
    """First line whose text starts with `label` and carries >= 2 numbers.

    The charts under each detail table reuse these exact strings as axis
    titles, but always on a line of their own, so the numeric guard is what
    keeps a chart axis from being read as data. First match wins because the
    table is always printed above its chart.
    """
    pat = re.compile(r"^\s*" + re.escape(label) + r"\s{2,}(?P<v>.*\d.*)$")
    for ln in lines:
        m = pat.match(ln)
        if not m:
            continue
        vals = _NUM.findall(m.group("v"))
        if len(vals) < 2:
            continue
        vals = [_f(v) for v in vals]
        # A short row means the layout drifted; pad rather than mis-align, so a
        # value is never silently attributed to the wrong section.
        return (vals + [None] * n)[:n]
    return [None] * n


def _detail_page(page):
    """One runner's detail page -> a record, or None if this is not one."""
    lines = page.splitlines()
    name = None
    for ln in lines:
        if _LABEL in ln:
            name = ln.split(_LABEL, 1)[1].strip()
            break
    if not name:
        return None

    def grab(label, pat=r"(\S+)"):
        rx = re.compile(r"^\s*" + re.escape(label) + r"\s{2,}" + pat)
        for ln in lines:
            m = rx.match(ln)
            if m:
                return m.groups()
        return None

    rec = {"name": name, "key": norm_name(name)}

    g = grab("Final Rank", r"(\d+|NA|DNF|DNT|-)")
    rec["final_rank"] = _rank(g[0]) if g else None
    g = grab("Race State", r"([A-Za-z ]+?)\s{2,}|([A-Za-z]+)\s*$")
    rec["race_state"] = next((x.strip() for x in (g or ()) if x), None)
    g = grab("Fastest Section Time (Section)", r"(\S+)\s+\(([^)]+)\)")
    rec["fastest_section_t"] = _t(g[0]) if g else None
    rec["fastest_section"] = g[1] if g else None
    g = grab("Top Speed [km/h] (Section)", r"([\d.]+)\s+\(([^)]+)\)")
    rec["top_kmh"] = _f(g[0]) if g else None
    rec["top_kmh_section"] = g[1] if g else None

    hdr = next((ln for ln in lines
                if re.match(r"^\s*Section\s{2,}(Overall|\d+m)", ln)), None)
    if not hdr:
        rec["sections"] = {}
        return rec
    labs = _labels(hdr)
    n = len(labs)

    times, splits = [None] * n, [None] * n
    for i, ln in enumerate(lines):
        m = re.match(r"^\s*Section Times\s{2,}(.*)$", ln)
        if not m:
            continue
        pairs = _TIMED.findall(m.group(1))
        for j, (tt, rk) in enumerate(pairs[:n]):
            times[j] = (_t(tt), _rank(rk))
        for j, sp in enumerate(_PAREN.findall(lines[i + 1] if i + 1 < len(lines) else "")[:n]):
            splits[j] = _t(sp)
        break

    avg = _row(lines, "Average Speed [km/h]", n)
    top = _row(lines, "Top Speed [km/h]", n)
    rail = _row(lines, "Avg. Dist. to Rail [m]", n)
    freq = _row(lines, "Avg. Stride Freq. [Hz]", n)
    leng = _row(lines, "Avg. Stride Length [m]", n)

    sections = {}
    for i, lab in enumerate(labs):
        sections[lab] = {
            "to_finish": times[i][0] if times[i] else None,
            "rank": times[i][1] if times[i] else None,
            "split": splits[i],
            "avg_kmh": avg[i], "top_kmh": top[i],
            "rail_m": rail[i], "stride_hz": freq[i], "stride_m": leng[i],
        }
    rec["sections"] = sections
    return rec


def _summary_page(page, out):
    """Accumulate summary-table fields into `out`, keyed by saddlecloth number.

    Each runner appears on every summary page with a different slice of the
    columns, so this merges rather than overwrites: a field already found on an
    earlier page is not clobbered by a blank on a later one.
    """
    lines = page.splitlines()
    has_margin = any("Margin" in ln for ln in lines)
    for i, ln in enumerate(lines):
        m = _SUM1.match(ln)
        if not m:
            continue
        horse = m.group("horse").strip()
        if not horse or horse.lower().startswith("rank"):
            continue
        no = ln.split()[1]
        r = out.setdefault(no, {"no": no})
        r.setdefault("name", horse)
        r.setdefault("key", norm_name(horse))
        r.setdefault("rank", int(ln.split()[0]))
        r.setdefault("barrier", int(m.group("barrier")))
        r.setdefault("top_kmh", _f(m.group("top")))
        rest = m.group("rest")
        tm = _TRAVEL.search(rest)
        if tm and r.get("dist_travelled") is None:
            r["dist_travelled"] = int(tm.group(1))
        if has_margin and r.get("margin_len") is None:
            mm = _MARGIN.search(rest)
            if mm:
                r["margin_len"] = _f(mm.group(1))
            elif r.get("rank") == 1:
                r["margin_len"] = 0.0
        if i + 1 < len(lines):
            jm = _SUM2.match(lines[i + 1])
            if jm and not r.get("jockey"):
                r["jockey"] = jm.group("jockey").strip()
    return out


def parse_file(path):
    text = pdf_text(path)
    pages = text.split("\f")

    race = race_name = distance = date = start_time = None
    track = grade = rating = weather = rail = None
    scratched, field_times = [], {}
    seen_scratch = set()

    for page in pages:
        for ln in page.splitlines():
            s = ln.strip()
            if not s:
                continue
            if race is None:
                m = _RACE.match(s)
                if m:
                    race = int(m.group(1))
                    race_name = m.group(2).strip()
                    distance = int(m.group(3))
                    continue
            if date is None:
                m = _DATE.match(s)
                if m:
                    mon = _MONTHS.get(m.group(2).title())
                    if mon:
                        date = "%s-%02d-%02d" % (m.group(3), mon, int(m.group(1)))
                        start_time = m.group(4)
                        continue
            if rating is None:
                m = _COND.search(s)
                if m:
                    rating = m.group("rating")
                    weather = m.group("weather")
                    rail = m.group("rail")
                    continue
            if track is None:
                m = _GRADE.match(s)
                if m and len(s) < 60 and " " not in m.group("grade"):
                    track = clean_track(m.group("track"))
                    grade = m.group("grade")
                    continue
            if s.startswith("Scratched:"):
                for nm, num in _SCRATCH.findall(s[len("Scratched:"):]):
                    k = norm_name(nm)
                    if k and k not in seen_scratch:
                        seen_scratch.add(k)
                        scratched.append({"name": nm.strip(), "key": k, "no": num})

    if track is None:
        counts = {}
        for page in pages:
            for s in {ln.strip() for ln in page.splitlines() if ln.strip()}:
                if len(s) < 40 and _GLUED.match(s):
                    counts[s] = counts.get(s, 0) + 1
        best = max((s for s, n in counts.items() if n >= 2), key=len, default=None)
        if best:
            m = _GLUED.match(best)
            track, grade = clean_track(m.group("track")), m.group("grade")

    # The rail position wraps onto a second line ("Out 11m Entire / Circuit") on
    # the detail pages; the summary pages carry it whole, so prefer the longest.
    for page in pages:
        for ln in page.splitlines():
            m = _COND.search(ln)
            if m and len(m.group("rail")) > len(rail or ""):
                rating, weather, rail = (m.group("rating"), m.group("weather"),
                                         m.group("rail"))

    summary, runners = {}, []
    for page in pages:
        if _LABEL in page:
            rec = _detail_page(page)
            if rec:
                runners.append(rec)
        elif "Horse/Jockey" in page:
            _summary_page(page, summary)
            hdr = next((ln for ln in page.splitlines()
                        if re.match(r"^\s*Section\s{2,}(Overall|\d+m)", ln)), None)
            ft = next((ln for ln in page.splitlines()
                       if re.match(r"^\s*Field Times\s{2,}", ln)), None)
            if hdr and ft:
                labs = _labels(hdr)
                vals = re.findall(r"\d+:\d{2}\.\d{2}", ft)
                for lab, v in zip(labs, vals):
                    field_times.setdefault(lab, secs(v))

    # merge summary columns onto the detail records (join on saddlecloth, then
    # on the normalised name -- a PDF is one race, so both are unique)
    by_no = {r["no"]: r for r in summary.values()}
    by_key = {r["key"]: r for r in summary.values() if r.get("key")}
    for ru in runners:
        s = by_key.get(ru["key"])
        if s is None:
            s = next((v for v in by_no.values() if v.get("key") == ru["key"]), None)
        if s:
            for f in ("no", "barrier", "jockey", "margin_len", "dist_travelled"):
                ru.setdefault(f, s.get(f))
            if ru.get("final_rank") is None:
                ru["final_rank"] = s.get("rank")
            if ru.get("top_kmh") is None:
                ru["top_kmh"] = s.get("top_kmh")
        else:
            for f in ("no", "barrier", "jockey", "margin_len", "dist_travelled"):
                ru.setdefault(f, None)

    # Summary-only runners: a horse that has a row in the table but no detail
    # page (it happens when the tracker lost it). Keep it -- the rank and margin
    # are still real results.
    have = {ru["key"] for ru in runners}
    for s in summary.values():
        if s.get("key") and s["key"] not in have:
            runners.append({"name": s["name"], "key": s["key"], "no": s.get("no"),
                            "final_rank": s.get("rank"), "barrier": s.get("barrier"),
                            "jockey": s.get("jockey"), "margin_len": s.get("margin_len"),
                            "dist_travelled": s.get("dist_travelled"),
                            "top_kmh": s.get("top_kmh"), "race_state": None,
                            "fastest_section_t": None, "fastest_section": None,
                            "top_kmh_section": None, "sections": {}})

    for ru in runners:
        _derive(ru, distance)

    runners.sort(key=lambda r: (r.get("final_rank") is None, r.get("final_rank") or 0))
    return {
        "date": date, "start_time": start_time,
        "track": track, "grade": grade,
        "race": race, "race_name": race_name, "distance": distance,
        "track_rating": rating, "weather": weather, "rail_position": rail,
        "field_times": field_times,
        "scratched": scratched,
        "source_file": Path(path).name,
        "runners": runners,
    }


def _derive(ru, distance):
    """Per-runner figures worth having precomputed.

    rail_avg is taken from the Overall column (the report's own whole-race mean)
    and falls back to the mean of the per-section values. rail_early / rail_late
    split at the 600m so a horse that was wide early but saved ground late is
    distinguishable from one that came off the fence to make its run -- those are
    opposite stories and a single average hides both.
    """
    sec = ru.get("sections") or {}
    marks = {k: v for k, v in sec.items() if k != "overall"}
    ov = sec.get("overall") or {}

    rails = [(int(k), v["rail_m"]) for k, v in marks.items() if v.get("rail_m") is not None]
    rails.sort(key=lambda x: -x[0])
    ru["rail_avg"] = r2(ov.get("rail_m") if ov.get("rail_m") is not None
                        else (sum(v for _, v in rails) / len(rails) if rails else None))
    ru["rail_max"] = r2(max((v for _, v in rails), default=None) if rails else None)
    early = [v for m, v in rails if m > 600]
    late = [v for m, v in rails if m <= 600]
    ru["rail_early"] = r2(sum(early) / len(early)) if early else None
    ru["rail_late"] = r2(sum(late) / len(late)) if late else None

    ru["stride_m"] = r2(ov.get("stride_m"))
    ru["stride_hz"] = r2(ov.get("stride_hz"))
    ru["overall_t"] = ov.get("to_finish")
    ru["avg_kmh"] = r2(ov.get("avg_kmh"))

    # position in running, straight from the report's own per-section ranks
    ranks = [(int(k), v["rank"]) for k, v in marks.items() if v.get("rank")]
    ranks.sort(key=lambda x: -x[0])
    ru["rank_at_800"] = next((r for m, r in ranks if m == 800), None)
    ru["rank_at_600"] = next((r for m, r in ranks if m == 600), None)
    ru["settled"] = ranks[0][1] if ranks else None

    ru["margin_m"] = r2(ru["margin_len"] * LENGTH_M) if ru.get("margin_len") else (
        0.0 if ru.get("final_rank") == 1 else None)
    ru["won"] = (ru.get("final_rank") == 1) if ru.get("final_rank") else None
    ru["placed"] = (ru["final_rank"] <= 3) if ru.get("final_rank") else None


def parse_dir(folder, report=None):
    """Every *.pdf under `folder`, recursively. Anything skipped is printed.

    A PDF that fails to parse must never take the build down with it -- the
    whole point of this source is that it is optional.
    """
    out = []
    folder = Path(folder)
    if not folder.exists():
        return out
    for p in sorted(folder.rglob("*")):
        if p.is_dir() or p.name.startswith("."):
            continue
        if p.suffix.lower() != ".pdf":
            print("  SKIP  %-55s not a pdf" % p.name, file=sys.stderr)
            if report is not None:
                report.append({"file": p.name, "status": "skipped", "reason": "not a pdf"})
            continue
        try:
            rec = parse_file(p)
        except Exception as exc:
            print("  ERROR %-55s %s: %s" % (p.name, type(exc).__name__, exc),
                  file=sys.stderr)
            if report is not None:
                report.append({"file": p.name, "status": "error",
                               "reason": "%s: %s" % (type(exc).__name__, exc)})
            continue
        if rec and rec["runners"] and rec["date"]:
            out.append(rec)
            if report is not None:
                report.append({"file": p.name, "status": "ok",
                               "reason": "%s %s R%s, %d runners" %
                               (rec["date"], rec["track"], rec["race"], len(rec["runners"]))})
        else:
            why = "no runners" if not (rec and rec["runners"]) else "no date in header"
            print("  EMPTY %-55s %s" % (p.name, why), file=sys.stderr)
            if report is not None:
                report.append({"file": p.name, "status": "empty", "reason": why})
    return out


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "raw/sectionals_pdf"
    p = Path(target)
    recs = [parse_file(p)] if p.is_file() else parse_dir(p)
    for rec in recs:
        print("== %s  %s  R%s %s  (%sm)  %s / %s / rail %s" % (
            rec["date"], rec["track"], rec["race"], rec["race_name"],
            rec["distance"], rec["track_rating"], rec["weather"], rec["rail_position"]))
        if rec["scratched"]:
            print("   scratched: %s" % ", ".join(
                "%s (#%s)" % (s["name"], s["no"]) for s in rec["scratched"]))
        print("   %-3s %-20s %-16s %-3s %6s %7s %6s %6s %6s %5s"
              % ("fin", "horse", "jockey", "bar", "mgn L", "trav m",
                 "rail", "early", "late", "s800"))
        for r in rec["runners"]:
            print("   %-3s %-20s %-16s %-3s %6s %7s %6s %6s %6s %5s" % (
                r["final_rank"], r["name"][:20], (r["jockey"] or "")[:16],
                r["barrier"], r["margin_len"], r["dist_travelled"],
                r["rail_avg"], r["rail_early"], r["rail_late"], r["rank_at_800"]))
    print(json.dumps(recs)[:0])
