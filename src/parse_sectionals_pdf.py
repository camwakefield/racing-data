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

TWO PROVIDERS, ONE ENTRY POINT. racing.com changed sectional supplier between
20 June and 1 August 2026. Everything above describes the OLD report (Developer
Express, "<Track>Professional" masthead). The new one is a Chromium-rendered
"tripleSdata GPS Sectionals" sheet with an unrelated layout, and the old reader
returns "no runners" on it -- so the result silently never lands. Both are read
here: parse_file() sniffs the producer and delegates. See the tripleSdata
section at the foot of this file. Old PDFs already in raw/ keep parsing exactly
as before; the record contract is identical either way.

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
_DATE = re.compile(r"^\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\s*(?:-\s*(\d{1,2}:\d{2})\s*(?:[AaPp]\.?[Mm]\.?)?)?\s*$")
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


def _parse_dxperience(path):
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


# ---------------------------------------------------------------------------
# tripleSdata GPS Sectionals -- the format racing.com switched to in July 2026
# ---------------------------------------------------------------------------
"""
WHAT THE NEW FORMAT GIVES THAT THE OLD ONE DID NOT
  * position in running at EVERY section, published, in [brackets] beside each
    split -- the old report gave only settled / 800 / 600. This is the running
    line itself, not a derived proxy.
  * distance travelled as an absolute (2537m) as well as signed against the
    winner (-7).
WHAT IT LOSES
  * per-section average speed, stride length/rate and distance-from-rail appear
    on the per-runner detail pages as CHART labels only -- doubled, unlabelled,
    and not safely readable. rail_avg / rail_max / stride_* therefore come back
    None on these meetings. That is allowed: every PDF field is optional by
    contract, and a None is honest where a guess would not be.

LAYOUT. Summary pages first (the table is split HORIZONTALLY across pages: same
runners each time, different L-columns), then one detail page per runner. Every
runner occupies THREE stacked text rows inside one visual band:

      top     TAB   horse    margin    1st400   top km/h   cumulative to-finish
      middle  RANK                     TIME
      bottom  BAR   jockey   dist run  last600  fastest s  (split)[position]

so a word's meaning is (x band, above/below the RANK row). Read by geometry
from `pdftotext -bbox-layout`, never by line regex: the columns are stable to a
tenth of a point and the letter-spaced headings are not.
"""

_XH = "{http://www.w3.org/1999/xhtml}"

# x boundaries of the summary table, in points, taken from the column headings.
# The page is 841.9pt wide (A4 landscape) and the layout is fixed-width.
_TS_BANDS = [(0, 45, "rank"), (45, 82, "tab"), (82, 205, "name"),
             (205, 262, "time"), (262, 313, "margin"), (313, 350, "first400"),
             (350, 450, "kmh")]
_TS_SECT_X = 450        # anything right of this is a section column
_TS_ROW_EPS = 1.6       # y tolerance for "same sub-row as RANK"
_TS_BLOCK_GAP = 10.0    # y gap that separates one runner band from the next

_TS_TIME = re.compile(r"^\d+:\d\d\.\d\d$")
_TS_MGN = re.compile(r"^(\d+(?:\.\d+)?)L$")
_TS_SPLIT = re.compile(r"^\((\d+\.\d+)\)(?:\[(\d+)\])?$")
_TS_DTW = re.compile(r"^\(([-+]?\d+)\)$")
_TS_SCR = re.compile(r"([A-Za-z][A-Za-z'\-\. ]*?)\s*\(#(\d+)\)")

# this provider abbreviates the month ("Sat 01 Aug 2026"); the old one spells it
_TS_MON = {m[:3].lower(): n for m, n in _MONTHS.items()}


def _ts_words(path):
    """(x0, x1, ycentre, text) for every word, page by page, plus the title."""
    import xml.etree.ElementTree as ET
    xml = subprocess.run(["pdftotext", "-bbox-layout", str(path), "-"],
                         capture_output=True, text=True).stdout
    root = ET.fromstring(xml)
    t = root.find(".//%stitle" % _XH)
    title = t.text if (t is not None and t.text) else ""
    pages = []
    for pg in root.iter(_XH + "page"):
        ws = []
        for w in pg.iter(_XH + "word"):
            ws.append((float(w.get("xMin")), float(w.get("xMax")),
                       (float(w.get("yMin")) + float(w.get("yMax"))) / 2,
                       (w.text or "").strip()))
        pages.append(_ts_merge_pos([w for w in ws if w[3]]))
    return title, pages


_TS_POS = re.compile(r"^\[(\d+)\]$")


def _ts_merge_pos(ws, ygap=1.5, xgap=3.0):
    """Re-attach a position-in-running marker that pdftotext split off.

    The position at each section is printed as a superscript inside the split:
    '(12.72)[2]'.  On the later layout pdftotext emits that as one word.  On the
    transitional layout used through July 2026 it emits '[2]' as its OWN word,
    baseline-shifted about 0.6pt and starting within a point of the split's
    right edge -- so _TS_SPLIT never saw it and every per-section rank came back
    None for those meetings.  Glue the pair back together here, before any
    parsing, so both layouts present the parser with one token.

    Matching is SPATIAL, not by emission order: pdftotext lists the page column
    by column, so the token emitted before a '[2]' is usually the last split of
    the row above it, not the split it belongs to.  Each marker is therefore
    paired with the nearest word on its own baseline (within ygap, since the
    superscript sits about 0.6pt high) whose right edge it starts against.
    Word order is otherwise preserved -- downstream row and block grouping
    relies on the emission order it already had.
    """
    pos = [i for i, w in enumerate(ws) if _TS_POS.match(w[3])]
    if not pos:
        return ws
    cand = [i for i, w in enumerate(ws) if w[3].endswith(")")]
    drop = set()
    for i in pos:
        _x0, _x1, y, t = ws[i]
        best, bestgap = None, None
        for j in cand:
            q = ws[j]
            gap = _x0 - q[1]
            if abs(q[2] - y) > ygap or gap < -0.5 or gap > xgap:
                continue
            if bestgap is None or gap < bestgap:
                best, bestgap = j, gap
        if best is not None:
            q = ws[best]
            ws[best] = (q[0], _x1, q[2], q[3] + t)
            drop.add(i)
    return [w for i, w in enumerate(ws) if i not in drop]


def _ts_rows(ws, eps=2.6):
    """Group words into visual rows by y, each row sorted left to right."""
    out = []
    for w in sorted(ws, key=lambda w: (w[2], w[0])):
        if out and abs(out[-1][0] - w[2]) <= eps:
            out[-1][1].append(w)
        else:
            out.append([w[2], [w]])
    return [(y, sorted(g, key=lambda w: w[0])) for y, g in out]


def _ts_glue(row, gap=2.4):
    """'T RACK - G O O D 4' -> 'TRACK-GOOD 4'.

    The small-caps subheads are set with wide letter-spacing, so pdftotext
    emits them one glyph at a time. Glyphs closer together than a real space
    belong to the same token. Used ONLY on those subheads: the masthead and the
    scratched strip are set at full size with genuine word spaces, and gluing
    them would produce "TABWe'reOn".
    """
    out, cur, prev = [], "", None
    for x0, x1, _y, t in row:
        if prev is not None and x0 - prev < gap:
            cur += t
        else:
            if cur:
                out.append(cur)
            cur = t
        prev = x1
    if cur:
        out.append(cur)
    return " ".join(out)


def _ts_band(x):
    for lo, hi, nm in _TS_BANDS:
        if lo <= x < hi:
            return nm
    return "sect" if x >= _TS_SECT_X else None


def _ts_header(pages, title):
    """Track, date, race number/name/distance, going, and the scratched list."""
    h = {"track": "", "date": "", "race": None, "race_name": "",
         "distance": None, "track_rating": "", "weather": "",
         "rail_position": "", "scratched": []}
    # "Flemington \u00b7 tripleSdata GPS Sectionals \u2014 Sat 01 Aug 2026"
    m = re.match(r"\s*(.+?)\s*[\u00b7\u2022]", title or "")
    if m:
        h["track"] = clean_track(m.group(1).strip())
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3})[a-z]*\s+(\d{4})", title or "")
    if m and m.group(2).lower() in _TS_MON:
        h["date"] = "%s-%02d-%02d" % (m.group(3), _TS_MON[m.group(2).lower()],
                                      int(m.group(1)))
    for pg in pages[:2]:
        # The masthead is large display type whose baselines wander by several
        # points across one visual line, so it is read on its own with a loose
        # y window anchored on the word RACE rather than by row.
        if h["race"] is None:
            for w in pg:
                if w[3] != "RACE" or w[0] > 45:
                    continue
                band = sorted([v for v in pg if abs(v[2] - w[2]) < 8],
                              key=lambda v: v[0])
                line = " ".join(v[3] for v in band)
                m = re.match(r"^RACE\s+(\d+)\s+(.+?)\s*(\d{3,4})\s*m\s*$", line)
                if m:
                    h["race"] = int(m.group(1))
                    h["race_name"] = m.group(2).strip()
                    h["distance"] = int(m.group(3))
                break
        for _y, row in _ts_rows(pg):
            line = _ts_glue(row)
            if not h["track_rating"] and "TRACK-" in line.replace(" ", ""):
                flat = line.replace(" - ", "-")
                mm = re.search(r"TRACK-\s*([A-Za-z]+)\s*(\d*)", flat)
                if mm:
                    # the subhead is letter-spaced, so the space in "Good 4" is
                    # lost in the glue; put it back -- the old provider wrote
                    # "Heavy 8" and the two must be one vocabulary downstream
                    h["track_rating"] = (mm.group(1).title() + " "
                                         + mm.group(2)).strip()
                mm = re.search(r"WEATHER-\s*([A-Za-z ]+?)(?:\s{2,}|$|RAIL)", flat)
                if mm:
                    h["weather"] = mm.group(1).strip().title()
                mm = re.search(r"RAIL-\s*(.+?)(?:TELEMETRY|$)", flat)
                if mm:
                    h["rail_position"] = mm.group(1).strip().title()
            plain = " ".join(w[3] for w in row)
            if "(#" in plain:
                for nm, no in _TS_SCR.findall(plain):
                    nm = nm.strip(" \u00b7")
                    if nm and nm.lower() not in ("tab", "bar"):
                        h["scratched"].append({"name": nm, "no": int(no)})
    seen, uniq = set(), []          # the scratched strip repeats on every page
    for sc in h["scratched"]:
        if sc["no"] not in seen:
            seen.add(sc["no"])
            uniq.append(sc)
    h["scratched"] = uniq
    return h


def _ts_blocks(pg):
    """Split one summary page into per-runner bands of three sub-rows.

    Anchored on the RANK column rather than chained on y-gaps. The finishing
    position is the only word in the leftmost band, so its y fixes the centre of
    a runner's band and every other word is assigned to the nearest centre. A
    dead heat or a missing sub-row then costs one field rather than the whole
    runner, which gap-chaining could not promise.
    """
    tbl = [w for w in pg if 245 < w[2] < 515]     # between headings and legend
    anchors = sorted(w[2] for w in tbl
                     if _ts_band(w[0]) == "rank" and w[3].isdigit())
    if not anchors:
        return []
    blocks = [(a, []) for a in anchors]
    for w in tbl:
        i = min(range(len(anchors)), key=lambda i: abs(anchors[i] - w[2]))
        if abs(anchors[i] - w[2]) <= _TS_BLOCK_GAP:
            blocks[i][1].append(w)
    return [(a, _ts_rows(ws, eps=1.2)) for a, ws in blocks if ws]


def _ts_summary_page(pg, runners):
    """Merge one summary page's columns into `runners`, keyed on saddlecloth."""
    # the section columns this page carries, read off the heading row so a page
    # can be merged without knowing the race distance
    labels = {}
    for _y, row in _ts_rows([w for w in pg if 225 < w[2] < 246]):
        for x0, _x1, _y2, t in row:
            m = re.match(r"^L(\d+)$", t)
            if m and x0 >= _TS_SECT_X:
                labels[round(x0)] = int(m.group(1))
    for ranky, blk in _ts_blocks(pg):
        cur = {"rank": None, "tab": None, "bar": None, "name": [],
               "jockey": [], "time": None, "margin": None, "dist_run": None,
               "dtw": None, "first400": None, "last600": None, "kmh": None,
               "fastest": None, "cum": {}, "split": {}, "pos": {}}
        for y, row in blk:
            where = "mid" if abs(y - ranky) <= _TS_ROW_EPS else (
                "top" if y < ranky else "bot")
            for x0, _x1, _y, t in row:
                b = _ts_band(x0)
                if b == "rank":
                    if t.isdigit():
                        cur["rank"] = int(t)
                elif b == "tab":
                    if t.isdigit():
                        cur["tab" if where == "top" else "bar"] = int(t)
                elif b == "name":
                    cur["name" if where == "top" else "jockey"].append(t)
                elif b == "time":
                    if _TS_TIME.match(t):
                        cur["time"] = t
                elif b == "margin":
                    if where == "top":
                        if t in ("\u2014", "-", "\u2013"):
                            cur["margin"] = 0.0
                        else:
                            m = _TS_MGN.match(t)
                            if m:
                                cur["margin"] = float(m.group(1))
                    elif t.isdigit():
                        cur["dist_run"] = int(t)
                    else:
                        m = _TS_DTW.match(t)
                        if m:
                            cur["dtw"] = int(m.group(1))
                elif b == "first400":
                    v = _f(t)
                    if v is not None:
                        cur["first400" if where == "top" else "last600"] = v
                elif b == "kmh":
                    if re.match(r"^\d+-\d+$", t):
                        cur["fastest"] = t
                    else:
                        v = _f(t)
                        if v is not None:
                            cur["kmh"] = v
                elif b == "sect":
                    col = min(labels, key=lambda k: abs(k - x0)) if labels else None
                    lab = labels.get(col) if (col is not None
                                              and abs(col - x0) < 30) else None
                    if _TS_TIME.match(t) and where == "top":
                        if lab:
                            cur["cum"][lab] = t
                    else:
                        m = _TS_SPLIT.match(t)
                        if m and lab:
                            cur["split"][lab] = float(m.group(1))
                            if m.group(2):
                                cur["pos"][lab] = int(m.group(2))
        no = cur["tab"]
        if no is None:
            continue
        r = runners.setdefault(no, {})
        for k, v in cur.items():
            if k in ("cum", "split", "pos"):
                r.setdefault(k, {}).update(v)
            elif k in ("name", "jockey"):
                if v and not r.get(k):
                    r[k] = " ".join(v)
            elif v is not None and r.get(k) is None:
                r[k] = v


def _ts_sections(cur):
    """The three per-section dicts -> the same `sections` shape the old report
    produces, so nothing downstream can tell the two providers apart.

    Speed, stride and rail come back None here -- see the note at the head of
    this section. The keys are the marker in metres as a string, matching the
    old parser, plus 'overall'.
    """
    sections = {}
    for lab in sorted(set(cur["cum"]) | set(cur["split"]) | set(cur["pos"]),
                      reverse=True):
        sections[str(lab)] = {
            "to_finish": secs(cur["cum"].get(lab)) if cur["cum"].get(lab) else None,
            "rank": cur["pos"].get(lab),
            "split": cur["split"].get(lab),
            "avg_kmh": None, "top_kmh": None,
            "rail_m": None, "stride_hz": None, "stride_m": None,
        }
    sections["overall"] = {
        "to_finish": secs(cur["time"]) if cur.get("time") else None,
        "rank": cur.get("rank"), "split": None,
        "avg_kmh": None, "top_kmh": cur.get("kmh"),
        "rail_m": None, "stride_hz": None, "stride_m": None,
    }
    return sections


def _parse_triplesdata(path):
    title, pages = _ts_words(path)
    h = _ts_header(pages, title)
    runners = {}
    for pg in pages:
        # a summary page is the one carrying the RANK column heading; the
        # per-runner detail pages that follow have no table at all
        if not any(_ts_band(w[0]) == "rank" and w[3] == "RANK" for w in pg):
            continue
        _ts_summary_page(pg, runners)

    scr_nos = {s["no"] for s in h["scratched"]}
    out = []
    for no, r in sorted(runners.items()):
        if r.get("rank") is None or not r.get("name") or no in scr_nos:
            continue
        ru = {
            "name": r["name"], "key": norm_name(r["name"]), "no": str(no),
            "final_rank": r["rank"], "barrier": r.get("bar"),
            "jockey": r.get("jockey"), "margin_len": r.get("margin"),
            "dist_travelled": r.get("dtw"),
            # this provider reports no DNF/DNT state at all; a runner absent
            # from the table is simply absent. None, not a guess.
            "race_state": None,
            "top_kmh": r.get("kmh"), "top_kmh_section": None,
            "fastest_section": r.get("fastest"), "fastest_section_t": None,
            "sections": _ts_sections(r),
        }
        # the report prints the fastest section as a range ("600-400"); its time
        # is the split already banked against the section's own upper marker
        if ru["fastest_section"]:
            mk = ru["fastest_section"].split("-")[0]
            ru["fastest_section_t"] = (r.get("split") or {}).get(_int(mk))
        _derive(ru, h["distance"])
        out.append(ru)
    out.sort(key=lambda r: (r.get("final_rank") is None, r.get("final_rank") or 0))

    for s in h["scratched"]:
        s["key"] = norm_name(s["name"])
    return {
        "date": h["date"], "start_time": None,
        "track": h["track"], "grade": None,
        "race": h["race"], "race_name": h["race_name"],
        "distance": h["distance"],
        "track_rating": h["track_rating"], "weather": h["weather"],
        "rail_position": h["rail_position"],
        "field_times": {},
        "scratched": h["scratched"],
        "source_file": Path(path).name,
        "runners": out,
    }


# ---------------------------------------------------------------------------
# Racing SA / WeasyPrint -- the third layout, used for the SA meetings
# ---------------------------------------------------------------------------
"""
A THIRD REPORT, not a variant of either of the other two. Produced by
WeasyPrint rather than Developer Express or Chromium, and carried by the SA
meetings (Morphettville, Morphettville Parks) that the Victorian suppliers
never covered.

WHAT IT SHARES WITH THE DXPERIENCE REPORT
  * a summary table split horizontally across one or two pages, then one detail
    page per runner with the full Section Times / Average Speed / Top Speed /
    Avg. Dist. to Rail / Avg. Stride Freq. / Avg. Stride Length block. The
    detail page carries EVERY column even when the summary spilled, so sections
    are read from the detail pages and the summary is used only for the
    identity fields.

WHAT DIFFERS, AND WHY EACH DIFFERENCE NEEDED CODE
  * masthead is "Morphettville Parks SA -", which matches neither the
    "<Track><Grade>" glue of the old report nor the all-caps tripleSdata block.
    Read as "<track> <state> [-]" instead. There is no grade word at all, so
    `grade` comes back None -- honest, and nothing downstream requires it.
  * the section columns are labelled L1568 / L1400 / ... rather than
    Overall / 1400m / ..., and the L-number of the leading column is the RACE
    DISTANCE. Which column means "overall" therefore depends on the race, and
    on a spilled continuation page the leading column is NOT overall. Labels
    are resolved against the distance from the "Race N: ... - 1568m" line.
  * "Finish Rank", not "Final Rank".
  * the detail page names the runner as "Horse/Jockey" in one cell, with the
    right-hand header block on the same physical text line. Split on the first
    run of two-or-more spaces, then on "/".
  * the "Section Times" caption sits BETWEEN its two value rows rather than on
    the first of them, so the rows are found by shape (a row of times, then a
    row of parenthesised splits) rather than by the caption.
  * the barrier is on the continuation line as "(2)", not on the summary line,
    and margin and distance-travelled travel with it as "0.6L (-9)".
  * a position-in-running rank is published at EVERY section, as the old report
    did, so settled / rank_at_800 / rank_at_600 are all real rather than
    derived.
"""

# "Morphettville Parks SA -"  ->  track, state
_SA_TRACK = re.compile(r"^(?P<track>[A-Z][A-Za-z'\-\.]*(?:\s+[A-Za-z'\-\.]+)*?)"
                       r"\s+(?:SA|VIC|NSW|QLD|WA|TAS|NT|ACT)\s*-?\s*$")

# column headings: L1568 L1400 L1200 ...
_SA_COL = re.compile(r"\bL(\d{3,4})\b")

# summary line 1: rank, saddlecloth, horse, overall, first 400m, top speed
_SA_SUM1 = re.compile(r"^\s*(?P<rank>\d{1,2})\s+(?P<no>\d{1,2})\s+"
                      r"(?P<horse>[A-Za-z]\S*(?: \S+)*?)\s{2,}"
                      r"(?P<overall>\d:\d{2}\.\d{2}|-:--\.--|NA)\s+"
                      r"(?P<first400>\d:\d{2}\.\d{2}|-:--\.--|NA)\s+"
                      r"(?P<kmh>\d{2,3}\.\d|NA)\s*\((?P<kmh_sec>[^)]*)\)\s+"
                      r"(?P<rest>.*)$")
# summary line 2: (barrier), jockey, [margin (dt-w)], last 600m, fastest section
_SA_SUM2 = re.compile(r"^\s*\((?P<bar>\d{1,2})\)\s+"
                      r"(?P<jockey>[A-Za-z][A-Za-z'\-\.]*(?: [A-Za-z'\-\.]+)*)\s{2,}"
                      r"(?:(?P<margin>\d+(?:\.\d+)?)L\s*\((?P<dtw>[-+]?\d+)\)\s+)?"
                      r"(?P<last600>\d:\d{2}\.\d{2}|-:--\.--|NA)\s+"
                      r"(?P<fast_sec>\d{3,4}\s*-\s*\d{3,4})\s*"
                      r"\((?P<fast_t>[^)]*)\)\s*(?P<rest>.*)$")

# a cumulative time, optionally carrying its position-in-running in brackets
_SA_TIMED = re.compile(r"(\d+:\d{2}\.\d{2}|-:--\.--|NA)(?:\s*\[\s*(\d+|NA|-)\s*\])?")

_SA_FINISH = "Finish Rank"


def _sa_labels(line, distance):
    """'... L1568 L1400 L1200' -> ['overall', '1400', '1200'].

    The leading column is the race distance, i.e. the whole-race figure, but
    only on the FIRST summary page -- a spilled continuation page starts
    mid-table. Matching on the distance rather than on position is what keeps
    the two cases apart.
    """
    return ["overall" if int(x) == distance else x
            for x in _SA_COL.findall(line)]


def _sa_sections(labs, times_line, splits_line):
    """The two value rows under a section header -> {label: {...}}."""
    n = len(labs)
    times = [(None, None)] * n
    for i, (tt, rk) in enumerate(_SA_TIMED.findall(times_line or "")[:n]):
        times[i] = (_t(tt), _rank(rk))
    splits = [None] * n
    for i, sp in enumerate(_PAREN.findall(splits_line or "")[:n]):
        splits[i] = _t(sp)
    return {lab: {"to_finish": times[i][0], "rank": times[i][1],
                  "split": splits[i]} for i, lab in enumerate(labs)}


def _sa_overall(ru, distance):
    """Whole-race figures for a report whose leading column is a SECTION.

    L<race distance> is a hybrid: its cumulative time is the race time, but its
    average speed, rail distance and stride figures describe the opening
    segment only -- start to the first published mark, ~170m. Verified
    numerically rather than assumed: Canny Defense's L1568 average speed is
    48.1 km/h against a 57.4 km/h race average and a 46.6 km/h opening segment,
    and Stirrup Cup's L1973 reads 46.9 against 56.4 and 47.0. Letting `_derive`
    take those as the whole-race figures would put a standing-start number in
    the column every other meeting fills with a race average.

    So the whole-race figures are rebuilt from the report's own numbers: each
    section's split time weights its own average speed / rail distance /
    stride, summed across EVERY section including the opening one. For speed
    that is exactly the race average; for the rest it is a time-weighted mean,
    which is what "average distance from the rail" ought to mean in any case.
    `_derive` has already run, so this overwrites rather than fills.
    """
    sec = ru.get("sections") or {}
    cols = [v for v in sec.values() if v.get("split")]

    def wmean(field):
        num = den = 0.0
        for v in cols:
            x, t = v.get(field), v.get("split")
            if x is None or not t:
                continue
            num, den = num + x * t, den + t
        return r2(num / den) if den else None

    ru["avg_kmh"] = wmean("avg_kmh")
    ru["rail_avg"] = wmean("rail_m")
    ru["stride_hz"] = wmean("stride_hz")
    ru["stride_m"] = wmean("stride_m")

    marks = [(distance if k == "overall" else int(k), v["rail_m"])
             for k, v in sec.items() if v.get("rail_m") is not None]
    ru["rail_max"] = r2(max((v for _, v in marks), default=None)) if marks else None
    early = [v for m, v in marks if m > 600]
    late = [v for m, v in marks if m <= 600]
    ru["rail_early"] = r2(sum(early) / len(early)) if early else None
    ru["rail_late"] = r2(sum(late) / len(late)) if late else None


def _sa_detail_page(page, distance):
    """One runner's detail page -> a record, or None if this is not one."""
    lines = page.splitlines()
    cell = None
    for ln in lines:
        if _LABEL in ln:
            # the right-hand header block shares this physical line; the first
            # two-or-more-space run ends the name cell
            cell = re.split(r"\s{2,}", ln.split(_LABEL, 1)[1].strip())[0].strip()
            break
    if not cell:
        return None
    horse, _, jockey = cell.partition("/")
    horse, jockey = horse.strip(), jockey.strip()
    if not horse:
        return None

    def grab(label, pat=r"(\S+)"):
        rx = re.compile(r"^\s*" + re.escape(label) + r"\s{2,}" + pat)
        for ln in lines:
            m = rx.match(ln)
            if m:
                return m.groups()
        return None

    rec = {"name": horse, "key": norm_name(horse), "jockey": jockey or None}

    g = grab(_SA_FINISH, r"(\d+|NA|DNF|DNT|-)")
    rec["final_rank"] = _rank(g[0]) if g else None
    g = grab("Race State", r"([A-Za-z ]+?)\s{2,}|([A-Za-z]+)\s*$")
    rec["race_state"] = next((x.strip() for x in (g or ()) if x), None)
    g = grab("Fastest Section Time (Section)", r"(\S+)\s+\(([^)]+)\)")
    rec["fastest_section_t"] = _t(g[0]) if g else None
    rec["fastest_section"] = g[1] if g else None
    g = grab("Top Speed [km/h] (Section)", r"([\d.]+)\s+\(([^)]+)\)")
    rec["top_kmh"] = _f(g[0]) if g else None
    rec["top_kmh_section"] = g[1] if g else None

    hdr_i = next((i for i, ln in enumerate(lines)
                  if re.match(r"^\s*Section\s{2,}L\d{3,4}\b", ln)), None)
    if hdr_i is None:
        rec["sections"] = {}
        return rec
    labs = _sa_labels(lines[hdr_i], distance)
    n = len(labs)

    # The "Section Times" caption sits between the two value rows, so the rows
    # are located by shape: the first row of >=2 bare times, then the first row
    # of >=2 parenthesised times below it.
    t_i = next((i for i in range(hdr_i + 1, len(lines))
                if len(_SA_TIMED.findall(lines[i])) >= 2
                and not _PAREN.search(lines[i])), None)
    s_i = next((i for i in range(t_i + 1, len(lines))
                if len(_PAREN.findall(lines[i])) >= 2), None) if t_i else None
    sections = _sa_sections(labs, lines[t_i] if t_i else "",
                            lines[s_i] if s_i else "")

    avg = _row(lines, "Average Speed [km/h]", n)
    top = _row(lines, "Top Speed [km/h]", n)
    rail = _row(lines, "Avg. Dist. to Rail [m]", n)
    freq = _row(lines, "Avg. Stride Freq. [Hz]", n)
    leng = _row(lines, "Avg. Stride Length [m]", n)
    for i, lab in enumerate(labs):
        sections[lab].update({"avg_kmh": avg[i], "top_kmh": top[i],
                              "rail_m": rail[i], "stride_hz": freq[i],
                              "stride_m": leng[i]})
    rec["sections"] = sections
    return rec


def _sa_summary_page(page, out, distance):
    """Accumulate summary-table fields into `out`, keyed by saddlecloth number.

    Merges rather than overwrites: on a spilled table the same runner appears on
    both summary pages, and only one of them carries any given column.
    """
    lines = page.splitlines()
    for i, ln in enumerate(lines):
        m = _SA_SUM1.match(ln)
        if not m:
            continue
        horse = m.group("horse").strip()
        if not horse or horse.lower().startswith("rank"):
            continue
        r = out.setdefault(m.group("no"), {"no": m.group("no")})
        r.setdefault("name", horse)
        r.setdefault("key", norm_name(horse))
        r.setdefault("rank", int(m.group("rank")))
        if r.get("top_kmh") is None:
            r["top_kmh"] = _f(m.group("kmh"))
        m2 = _SA_SUM2.match(lines[i + 1]) if i + 1 < len(lines) else None
        if not m2:
            continue
        r.setdefault("barrier", int(m2.group("bar")))
        r.setdefault("jockey", m2.group("jockey").strip())
        if m2.group("margin") is not None:
            r.setdefault("margin_len", _f(m2.group("margin")))
            r.setdefault("dist_travelled", _int(m2.group("dtw")))
        elif r.get("rank") == 1:
            r.setdefault("margin_len", 0.0)
            r.setdefault("dist_travelled", 0)
    return out


def _parse_racingsa(path):
    text = pdf_text(path)
    pages = text.split("\f")

    race = race_name = distance = date = start_time = None
    track = rating = weather = rail = None
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
                    rating, weather = m.group("rating"), m.group("weather")
                    rail = m.group("rail")
                    continue
            if s.startswith("Scratched:"):
                for nm, num in _SCRATCH.findall(s[len("Scratched:"):]):
                    k = norm_name(nm)
                    if k and k not in seen_scratch:
                        seen_scratch.add(k)
                        scratched.append({"name": nm.strip(), "key": k, "no": num})

    # Masthead. It repeats on every page, so a short line that both matches the
    # "<track> <state>" shape and appears more than once is the venue and not
    # body text that happens to end in a state abbreviation.
    counts = {}
    for page in pages:
        for s in {ln.strip() for ln in page.splitlines() if ln.strip()}:
            if len(s) < 45 and _SA_TRACK.match(s):
                counts[s] = counts.get(s, 0) + 1
    best = max((s for s, n in counts.items() if n >= 2), key=len, default=None)
    if best is None and counts:
        best = max(counts, key=len)
    if best:
        track = clean_track(_SA_TRACK.match(best).group("track"))

    # The rail position wraps onto a second line on the detail pages; the
    # summary page carries it whole, so prefer the longest seen.
    for page in pages:
        for ln in page.splitlines():
            m = _COND.search(ln)
            if m and len(m.group("rail")) > len(rail or ""):
                rating, weather, rail = (m.group("rating"), m.group("weather"),
                                         m.group("rail"))

    summary, runners = {}, []
    for page in pages:
        if _LABEL in page:
            rec = _sa_detail_page(page, distance)
            if rec:
                runners.append(rec)
            continue
        if "TAB#" not in page:
            continue
        _sa_summary_page(page, summary, distance)
        lines = page.splitlines()
        hdr = next((ln for ln in lines if _SA_COL.search(ln) and "TAB#" in ln), None)
        ft = next((ln for ln in lines if re.match(r"^\s*Field Times\s{2,}", ln)), None)
        if hdr and ft:
            for lab, v in zip(_sa_labels(hdr, distance),
                              re.findall(r"\d+:\d{2}\.\d{2}", ft)):
                field_times.setdefault(lab, secs(v))

    # merge the summary columns onto the detail records
    by_key = {r["key"]: r for r in summary.values() if r.get("key")}
    for ru in runners:
        s = by_key.get(ru["key"])
        for f in ("no", "barrier", "margin_len", "dist_travelled"):
            ru.setdefault(f, s.get(f) if s else None)
        if not ru.get("jockey"):
            ru["jockey"] = s.get("jockey") if s else None
        if ru.get("final_rank") is None and s:
            ru["final_rank"] = s.get("rank")
        if ru.get("top_kmh") is None and s:
            ru["top_kmh"] = s.get("top_kmh")

    # Summary-only runners: a row in the table with no detail page behind it.
    # The rank and margin are still real results, so the row is kept.
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
        _sa_overall(ru, distance)

    runners.sort(key=lambda r: (r.get("final_rank") is None, r.get("final_rank") or 0))
    return {
        "date": date, "start_time": start_time,
        "track": track, "grade": None,
        "race": race, "race_name": race_name, "distance": distance,
        "track_rating": rating, "weather": weather, "rail_position": rail,
        "field_times": field_times,
        "scratched": scratched,
        "source_file": Path(path).name,
        "runners": runners,
    }


def _int(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def _is_racingsa(path):
    """'(BAR#)' in the first page's column headings.

    A content marker rather than a metadata one: the WeasyPrint producer string
    would do today, but it is the kind of thing a re-save destroys, whereas the
    heading is the table itself. Checked only AFTER the tripleSdata sniff --
    both layouts carry a 'TAB#' heading, only this one puts the barrier under
    the horse in parentheses.
    """
    try:
        txt = subprocess.run(["pdftotext", "-layout", "-f", "1", "-l", "1",
                              str(path), "-"], capture_output=True,
                             text=True).stdout
    except FileNotFoundError:
        return False
    return "(BAR#)" in txt


def _is_triplesdata(path):
    """Cheap sniff on the document metadata, then on page 1's words.

    Metadata first because it costs one pdfinfo and is what the generator
    actually stamps; the text scan is the fallback for a file that has been
    re-saved and lost its title.
    """
    try:
        info = subprocess.run(["pdfinfo", str(path)], capture_output=True,
                              text=True).stdout
    except FileNotFoundError:
        info = ""
    if "triplesdata" in info.lower():
        return True
    try:
        txt = subprocess.run(["pdftotext", "-f", "1", "-l", "1", str(path), "-"],
                             capture_output=True, text=True).stdout
    except FileNotFoundError:
        return False
    return "triplesdata" in txt.lower().replace(" ", "")


def parse_file(path):
    """One sectionals PDF -> one race record, whichever provider produced it."""
    if _is_triplesdata(path):
        return _parse_triplesdata(path)
    if _is_racingsa(path):
        return _parse_racingsa(path)
    return _parse_dxperience(path)



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
