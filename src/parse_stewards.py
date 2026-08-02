"""Parse an RV-style stewards report into structured per-horse signals."""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import norm_name

RACE_HDR = re.compile(r"^Race\s+(\d+)\b(.*?)(\d{3,4})\s*met", re.I)
RACE_ANY = re.compile(r"^Race\s+(\d+)\b", re.I)

RULES = {
    "slow_begin": ["slow to begin", "slow into stride", "began awkwardly",
                   "commenced awkwardly", "missed the start", "slowly away"],
    "trouble":    ["hampered", "crowded", "bumped", "made contact", "checked",
                   "steadied", "carried out", "carried wider", "shifted out onto",
                   "crowded out", "tightened", "awkwardly placed", "clipped heels",
                   "severely hampered", "eased when", "restrained when crowded"],
    "wide":       ["wide without cover", "three wide", "four wide", "raced wide",
                   "travel wider", "four deep", "three deep", "without cover"],
    "held_up":    ["held up", "unable to obtain clear running", "no clear running",
                   "disappointed for", "unable to be fully tested",
                   "unable to be ridden out", "awaiting a run", "held up for clear"],
    "keen":       ["raced keenly", "over-raced", "overraced", "raced fiercely",
                   "pulled hard"],
    "faded":      ["weakened", "failed to run on", "eased down", "raced flat",
                   "failed to respond", "laid inwards", "laid in ", "laid outwards",
                   "laid out", "hung out", "hung in", "did not run on"],
    "gear_change":["blinkers", "add the", "addition of", "winkers", "tongue tie",
                   "gear change", "to its gear"],
    "tactics":    ["change of tactics", "ridden more positively", "further forward",
                   "further back", "settle further"],
    "condition":  ["firmer tracks", "firmer going", "better on top", "softer",
                   "did not appreciate", "may appreciate racing", "wet track",
                   "heavy track", "suited on firmer", "soft 6 track conditions",
                   "did not travel comfortably on the soft"],
    "vet_health": ["bled", "blood in", "blood at", "nostril", "haemorrhage",
                   "hemorrhage", "eiph", "pulmonary", "throat", "endoscopy",
                   "veterinary clearance", "lame", "cardiac", "jump-out",
                   "abnormality was detected", "returning from", "tendon",
                   "surgery", "suspended"],
    "underperf":  ["below market expectations", "performed below market",
                   "disappointing"],
}
FORGIVE = ("trouble", "slow_begin", "wide", "held_up")

CONNECTORS = {"of", "the", "a", "an", "and", "'n'", "n", "al", "my", "no", "that",
              "de", "du", "da", "la", "le", "van", "von", "el", "to", "on", "in", "for"}

STOP = {w.lower() for w in [
    "Slow", "Began", "Commenced", "Missed", "Jumped", "Stumbled", "Blundered",
    "Knuckled", "Reared", "Fractious", "Raced", "Restrained", "Settled", "Held",
    "Hampered", "Crowded", "Bumped", "Checked", "Steadied", "Carried", "Contacted",
    "Shifted", "Laid", "Hung", "Wandered", "Weakened", "Eased", "Improved",
    "Travelled", "Overraced", "Continued", "Approaching", "Rounding", "Near",
    "Over", "Under", "Shortly", "After", "Before", "During", "When", "Which",
    "Where", "As", "On", "At", "Underwent", "Performed", "Lost", "Made", "Was",
    "Had", "Got", "Failed", "Pulled", "Inclined", "Rider", "Trainer", "Apprentice",
    "Co-Trainer", "Connections", "Post-race", "Post-Race", "Re-plated", "Change",
    "Was", "Stewards", "Would", "Underneath", "Threw", "Refused",
    "Would", "Struck", "Racing", "Hanging", "Laying", "Ran", "Attempted",
    # Added to stop prose bleeding into horse-name keys. Every one of these was
    # observed heading, or sitting inside, a phantom key in the built store:
    # ORCHID SKY BROKE, THINK GIANT RESADDLED, THE MEAN FIDDLER DESPITE,
    # TEMPESTI BETWEEN THE 400M AND THE 250M, CORRECT, PRIOR.
    "Broke", "Resaddled", "Re-saddled", "Despite", "Between", "Prior",
    "Correct", "Following", "Whilst", "However", "Subsequently", "Subsequent",
    "Notwithstanding", "Unable", "Returned", "Throughout", "Upon", "Although",
    "Though", "Since", "Because", "Therefore", "Accordingly", "Meanwhile",
    "Thereafter", "Whereupon", "Owner", "Owners", "Jockey", "Stipendiary",
    "Veterinarian", "Veterinary", "Licensed", "Deputy", "Chairman", "Handler",
    "Strapper", "Foreman", "Steward",
]}

# Source misspellings in the stewards feed. Each of these created a second,
# empty store row alongside the correctly-spelled horse -- one run, no rating,
# no result. Mapped at key time so the comment lands on the real horse.
MISSPELL = {
    "DECALOUGE": "DECALOGUE",
    "TUFF TU MISS": "TUFF TU MUS",
}

_MEASURE = re.compile(r"^\d+(?:M|m)?$")


def _plausible_name(name):
    """Reject prose fragments that survived token-walking as a 'horse name'.

    A horse name has to carry at least one alphabetic run of three or more
    characters that is not a connector, and cannot be made only of connectors
    or of distance markers. This is what kills THE, AS, II and 200M.
    """
    toks = [t for t in name.split() if t]
    if not toks:
        return False
    real = [t for t in toks
            if t.lower().strip("()'’.") not in CONNECTORS
            and not _MEASURE.match(t)
            and len(re.sub(r"[^A-Za-z]", "", t)) >= 3]
    return bool(real)


def _extract_name(line):
    toks = line.split()
    if not toks:
        return None, ""
    name = []
    idx = 0
    for i, tok in enumerate(toks):
        core = tok.strip(" -—–,").strip()
        if not core:
            if name:
                break
            continue
        low = core.lower().strip("()'’.")
        is_country = bool(re.fullmatch(r"\(?[A-Za-z]{2,3}\)?", core)) and core.strip("()").isupper()
        # STOP is checked at EVERY position including the first. The old code
        # exempted token 0, which let role words through and produced keys like
        # APPRENTICE JACKSON RADLEY and RIDER JETT STANLEY.
        if low in STOP:
            break
        if i == 0:
            name.append(core); idx = i + 1; continue
        if is_country:
            name.append(core); idx = i + 1; continue
        if low in STOP:
            break
        if low in CONNECTORS:
            name.append(core); idx = i + 1; continue
        if core[:1].isupper() or core[:1].isdigit():
            name.append(core); idx = i + 1; continue
        break
    # Trailing connectors and distance markers are prose, not part of the name.
    while len(name) > 1 and (name[-1].lower().strip("()'’.") in CONNECTORS
                             or _MEASURE.match(name[-1])):
        name.pop()
        idx -= 1
    out = " ".join(name).strip(" -—–")
    if not _plausible_name(out):
        return None, line.strip()
    return out, " ".join(toks[idx:]).strip(" -—–\t")


def _split_horse_blocks(text):
    blocks = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        name, comment = _extract_name(line)
        if not name:
            if blocks:
                blocks[-1] = (blocks[-1][0], (blocks[-1][1] + " " + line).strip())
            continue
        blocks.append((name, comment))
    return blocks


def pdf_text(path):
    try:
        out = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                             capture_output=True, text=True, check=True).stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        import pdfplumber
        with pdfplumber.open(str(path)) as pdf:
            out = "\n".join((pg.extract_text() or "") for pg in pdf.pages)
    return out


def unwrap(text):
    out = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            out.append("")
            continue
        if s[:1].islower() and out:
            k = len(out) - 1
            while k >= 0 and out[k] == "":
                k -= 1
            if k >= 0:
                out[k] = out[k].rstrip() + " " + s
                continue
        out.append(s)
    return "\n".join(out)


def parse_header(text):
    h = {"track": "", "condition": "", "going_stick": "", "weather": "", "rail": "",
         "date": "", "club": ""}
    lines = [l.strip() for l in text.splitlines()]
    for l in lines:
        if re.search(r"\b(Racing|Turf|Jockey)\s+Club\b", l):
            h["club"] = l.strip()
            break
    if not h["club"] and lines:
        h["club"] = lines[0].strip()

    def field(label):
        pat = re.compile(r"^\s*" + label + r"\b[^:]*:\s*(.*)$", re.I)
        for i, l in enumerate(lines):
            m = pat.match(l)
            if m:
                if m.group(1).strip():
                    return m.group(1).strip()
                for j in range(i + 1, min(i + 3, len(lines))):
                    if lines[j]:
                        return lines[j]
        return ""
    h["condition"] = field("Track")
    h["going_stick"] = field("Going")
    h["weather"] = field("Weather")
    h["rail"] = field("Rail")
    raw_date = field("Date")
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", raw_date)
    if m:
        months = {mn.lower(): i for i, mn in enumerate(
            ["", "January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December"])}
        mo = months.get(m.group(2).lower(), 0)
        if mo:
            h["date"] = "%s-%02d-%02d" % (m.group(3), mo, int(m.group(1)))
    return h


def _horse_record(name, comment, rno):
    """Flag/score one horse comment. Shared by the text and HTML paths."""
    low = comment.lower()
    flags = {}
    for bucket, kws in RULES.items():
        hit = [kw for kw in kws if kw in low]
        if hit:
            flags[bucket] = hit
    forg = sum(1 for b in FORGIVE if b in flags)
    excuse_index = forg - (1 if ("faded" in flags and forg == 0) else 0)
    return {
        "name": name, "key": MISSPELL.get(norm_name(name), norm_name(name)),
        "race": rno,
        "flags": sorted(flags.keys()), "excuse_index": excuse_index,
        "health_flag": "vet_health" in flags, "gear_change": "gear_change" in flags,
        "underperf": "underperf" in flags, "comment": comment,
    }


# ------------------------------------------------------- racing.com HTML
#
# A saved racing.com stewards page is ~1.5 MB, of which the report is ~30 KB
# inside <div class="stewards-report">. The old path flattened the WHOLE
# document to text, so:
#
#   * parse_header read line 0 of the page chrome and returned the Racing.com
#     copyright notice as the track name, and found no date at all;
#   * the report body is a Word export where a horse name is wrapped in <b>
#     and hard-wrapped mid-name -- "<b><span>Flying\nKhan </span></b>" -- so
#     after tag-stripping the name arrived as two lines, "Flying" then
#     "Khan Slow to begin.". unwrap() only rejoins lines starting lowercase,
#     so most horses were lost and a few survived by luck. That is the
#     2-and-3-horse meetings.
#   * a single-race page (".../Race 9/...") carries no <h1> and no header
#     table, so there was no "Race N" line to anchor on and the file
#     extracted nothing at all.
#
# So: cut out the report div, walk its <p> elements, and use the <b>
# boundary that the document already provides instead of guessing where the
# name stops. Take the date and track from the header table when present and
# from the filename when it is not.

_SR_START = re.compile(r"<div\b[^>]*class=\"[^\"]*stewards-report[^\"]*\"[^>]*>", re.I)
_DIV_TOK = re.compile(r"<div\b|</div\s*>", re.I)
_P_BLOCK = re.compile(r"<p\b[^>]*>(.*?)</p\s*>", re.I | re.S)
_LEAD_BOLD = re.compile(r"\A\s*(?:<(b|strong)\b[^>]*>.*?</\1\s*>\s*)+", re.I | re.S)
_NUM_ENT = re.compile(r"&#(\d+);")
_MONTHS = {m.lower(): i for i, m in enumerate(
    ["", "January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}


# The <h1> is written a different way almost every meeting -- "Caulfield",
# "Caulfield: Melbourne Racing Club", "Victoria Racing Club @ Flemington",
# "Sportsbet-Ballarat Synthetic: Ballarat Turf Club", "Southside Racing
# Cranbourne". The sectionals side of the store uses the bare venue, so
# anything else forks meetings.json into near-duplicates. Longest first:
# Sandown Hillside must win over Sandown, Ballarat Synthetic over Ballarat,
# Morphettville Parks over Morphettville.
CANON_TRACKS = [
    "Sandown Hillside", "Sandown Lakeside", "Ballarat Synthetic",
    "Morphettville Parks", "Moonee Valley", "Flemington", "Caulfield",
    "Cranbourne", "Morphettville", "Ballarat", "Bendigo", "Geelong",
    "Pakenham", "Werribee", "Mornington", "Warrnambool", "Traralgon",
    "Bairnsdale", "Wangaratta", "Swan Hill", "Kyneton", "Seymour", "Kilmore",
    "Horsham", "Benalla", "Echuca", "Wodonga", "Tatura", "Ararat", "Colac",
    "Terang", "Hamilton", "Sale", "Moe", "Gawler", "Murray Bridge",
    "Strathalbyn", "Naracoorte", "Port Lincoln", "Mount Gambier",
]
_SPONSOR = re.compile(
    r"^(sportsbet|tab|tabcorp|ladbrokes|neds|beteasy|bet365|southside racing|"
    r"southside|racing\.com|the valley)[\s\-]+", re.I)


def normalise_track(s):
    """'Sportsbet-Ballarat Synthetic: Ballarat Turf Club' -> 'Ballarat Synthetic'."""
    s = (s or "").strip()
    if not s:
        return ""
    s = s.split(":")[0].strip()
    if "@" in s:                                  # 'Victoria Racing Club @ Flemington'
        s = s.split("@")[-1].strip()
    for canon in CANON_TRACKS:                    # trust the known venue over the prose
        if re.search(r"\b" + re.escape(canon) + r"\b", s, re.I):
            return canon
    prev = None
    while prev != s:                              # 'Sportsbet-Ballarat', 'TAB Bendigo'
        prev = s
        s = _SPONSOR.sub("", s).strip()
    s = re.sub(r"\s+(Jockey|Turf|Racing)\s+Club$", "", s, flags=re.I).strip()
    return s


def _plain(fragment):
    """Tags out, entities in, all whitespace (including hard wraps) to single spaces."""
    s = re.sub(r"<[^>]+>", " ", fragment)
    for k, v in _ENTITY.items():
        s = s.replace(k, v)
    s = _NUM_ENT.sub(lambda m: chr(int(m.group(1))) if int(m.group(1)) != 160 else " ", s)
    s = re.sub(r"&[a-zA-Z]+;", " ", s)
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()


def _report_div(raw):
    """The inner HTML of <div class="stewards-report">, or None."""
    m = _SR_START.search(raw)
    if not m:
        return None
    depth, start = 1, m.end()
    for tok in _DIV_TOK.finditer(raw, start):
        depth += 1 if tok.group(0).lower().startswith("<div") else -1
        if depth == 0:
            return raw[start:tok.start()]
    return raw[start:]


def _iso_date(s):
    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", s or "")
    if not m:
        return ""
    mo = _MONTHS.get(m.group(2).lower(), 0)
    return "%s-%02d-%02d" % (m.group(3), mo, int(m.group(1))) if mo else ""


def _from_filename(name):
    """'Form _ Stewards' Report _ Flemington _ Race 9 _ Saturday _ 4 July 2026 _ VIC _ ...'

    The single-race pages carry no header table, so the filename is the only
    place the date and track exist. It is a weaker source than the document,
    so it is only ever used to fill a gap.
    """
    stem = re.sub(r"\.(html?|xhtml)$", "", name, flags=re.I)
    parts = [p.strip() for p in re.split(r"\s+_\s+|_", stem) if p.strip()]
    out = {"date": _iso_date(stem), "track": "", "race": None}
    for i, p in enumerate(parts):
        m = re.fullmatch(r"Race\s*(\d+)", p, re.I)
        if m:
            out["race"] = int(m.group(1))
        if re.search(r"Stewards.{0,3}\s*Report", p, re.I) and i + 1 < len(parts):
            cand = parts[i + 1]
            if not re.fullmatch(r"Race\s*\d+", cand, re.I):
                out["track"] = cand
    return out


def parse_racingcom_html(path, body):
    """Structured parse of the report div. Returns the same record parse_file does."""
    fn = _from_filename(Path(path).name)

    # --- header: <h1>Flemington: Victoria Racing Club</h1> + a label/value table
    header = {"track": "", "condition": "", "going_stick": "", "weather": "",
              "rail": "", "date": "", "club": ""}
    mh1 = re.search(r"<h1\b[^>]*>(.*?)</h1\s*>", body, re.I | re.S)
    if mh1:
        header["club"] = _plain(mh1.group(1))
    cells = [_plain(c) for c in re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]\s*>", body, re.I | re.S)]
    for i, c in enumerate(cells[:-1]):
        lab = c.rstrip(":").strip().lower()
        val = cells[i + 1]
        if lab == "date":
            header["date"] = _iso_date(val)
        elif lab == "track":
            header["condition"] = val
        elif lab.startswith("going"):
            header["going_stick"] = val
        elif lab == "weather":
            header["weather"] = val
        elif lab == "rail":
            header["rail"] = val
    if not header["date"]:
        header["date"] = fn["date"]

    track = normalise_track(header["club"]) or normalise_track(fn["track"])

    # --- body: one <p> per horse, the name in the leading <b>
    races, cur, seen = [], None, set()

    def open_race(rno, dist, label):
        nonlocal cur
        if cur is not None:
            races.append(cur)
        cur = {"race": rno, "distance": dist, "name": label, "horses": []}

    for frag in _P_BLOCK.findall(body):
        mb = _LEAD_BOLD.match(frag)
        head = _plain(mb.group(0)) if mb else ""
        rest = _plain(frag[mb.end():]) if mb else ""
        if not head:
            continue                                   # penalty notices, notes
        mr = re.match(r"Race\s+(\d+)\b(.*)$", head, re.I)
        if mr:
            md = re.search(r"(\d{3,4})\s*met", mr.group(2), re.I)
            open_race(int(mr.group(1)), int(md.group(1)) if md else None, head)
            continue
        if not rest or head.endswith(":") or len(head) < 2:
            continue                                   # section heading, e.g.
        if re.match(r"^(Rider|Trainer|Apprentice|Stewards|Co-trainer)\b", head, re.I):
            continue                                   # bolded person, not a horse
        if cur is None:                                # pre-Race-1 or single-race page
            open_race(fn["race"] or 0, None, "Race %s" % (fn["race"] or "?"))
        name = head.strip(" -–—,")
        if not name:
            continue
        k = (cur["race"], norm_name(name))
        if k in seen:
            continue
        seen.add(k)
        cur["horses"].append(_horse_record(name, rest, cur["race"]))
    if cur is not None:
        races.append(cur)

    return {"track": track, "date": header["date"], "header": header,
            "source_file": Path(path).name, "races": races}


def parse_file(path):
    path = Path(path)
    ext = path.suffix.lower()
    if ext in PDF_EXTS:
        text = pdf_text(path)
    elif ext in HTML_EXTS:
        raw = open(path, encoding="utf-8", errors="replace").read()
        body = _report_div(raw)
        if body is not None:
            return parse_racingcom_html(path, body)
        text = html_text(path)
    else:
        text = open(path, encoding="utf-8", errors="replace").read()
    text = unwrap(text)
    header = parse_header(text)
    track = normalise_track(header.get("club", "")) or normalise_track(path.name)

    lines = text.splitlines()
    idxs = [i for i, l in enumerate(lines) if RACE_ANY.match(l.strip())]
    stop = len(lines)
    for i, l in enumerate(lines):
        if re.match(r"^(SWAB SAMPLES|Raceday Summary|SUMMARY)\b", l.strip(), re.I):
            stop = i
            break
    idxs = [i for i in idxs if i < stop]

    races = []
    for k, start in enumerate(idxs):
        end = idxs[k + 1] if k + 1 < len(idxs) else stop
        hdr_line = lines[start].strip()
        mh = RACE_HDR.match(hdr_line)
        rno = int((mh or RACE_ANY.match(hdr_line)).group(1))
        dist = int(mh.group(3)) if mh else None
        body = "\n".join(lines[start + 1:end])
        horses = []
        for name, comment in _split_horse_blocks(body):
            if not comment or len(name) < 2:
                continue
            low = comment.lower()
            flags = {}
            for bucket, kws in RULES.items():
                hit = [kw for kw in kws if kw in low]
                if hit:
                    flags[bucket] = hit
            forg = sum(1 for b in FORGIVE if b in flags)
            excuse_index = forg - (1 if ("faded" in flags and forg == 0) else 0)
            horses.append({
                "name": name,
                "key": MISSPELL.get(norm_name(name), norm_name(name)),
                "race": rno,
                "flags": sorted(flags.keys()), "excuse_index": excuse_index,
                "health_flag": "vet_health" in flags, "gear_change": "gear_change" in flags,
                "underperf": "underperf" in flags, "comment": comment,
            })
        races.append({"race": rno, "distance": dist, "name": hdr_line, "horses": horses})

    return {"track": track, "date": header.get("date", ""), "header": header,
            "source_file": Path(path).name, "races": races}


# --------------------------------------------------------------- discovery
#
# The old parse_dir globbed exactly "*.txt" and "*.pdf" in one directory.
# GitHub Actions runs on Linux, where globs are CASE-SENSITIVE, so a report
# saved as ".PDF" (Safari and macOS Preview both do this) was silently
# skipped, as was anything in a subfolder, anything saved as HTML from
# racing.com, and anything with a ".text" or ".md" extension. Nothing was
# logged, so the build looked successful while ignoring most of the input.
#
# This version walks the tree, matches extensions case-insensitively, never
# lets one unreadable file kill the build, and RECORDS what it skipped.

TEXT_EXTS = {".txt", ".text", ".md", ".log"}
PDF_EXTS = {".pdf"}
HTML_EXTS = {".html", ".htm", ".xhtml"}
KNOWN_EXTS = TEXT_EXTS | PDF_EXTS | HTML_EXTS

_TAG = re.compile(r"<[^>]+>")
_SCRIPT = re.compile(r"<(script|style)\b.*?</\1>", re.I | re.S)
_ENTITY = {"&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
           "&quot;": '"', "&#39;": "'", "&rsquo;": "'", "&ldquo;": '"',
           "&rdquo;": '"', "&mdash;": "-", "&ndash;": "-"}


def html_text(path):
    """Crude but adequate HTML-to-text for a saved racing.com report page."""
    raw = open(path, encoding="utf-8", errors="replace").read()
    raw = _SCRIPT.sub(" ", raw)
    raw = re.sub(r"<(br|/p|/div|/tr|/li|/h\d)\s*/?>", "\n", raw, flags=re.I)
    raw = _TAG.sub(" ", raw)
    for k, v in _ENTITY.items():
        raw = raw.replace(k, v)
    raw = re.sub(r"&#\d+;", " ", raw)
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in raw.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def discover(folder):
    """Every candidate stewards file under `folder`, plus the ones we ignored.

    Returns (paths, skipped) where skipped is a list of (name, reason).
    """
    folder = Path(folder)
    paths, skipped = [], []
    if not folder.exists():
        return paths, [(str(folder), "folder does not exist")]
    for p in sorted(folder.rglob("*")):
        if p.is_dir() or p.name.startswith("."):
            continue
        ext = p.suffix.lower()
        if ext in KNOWN_EXTS:
            paths.append(p)
        else:
            rel = p.relative_to(folder)
            skipped.append((str(rel), "unrecognised extension %r" % (p.suffix or "(none)")))
    return paths, skipped


def parse_dir(folder, report=None):
    """Parse every stewards file under `folder`, recursively.

    Pass a list as `report` to receive per-file diagnostics:
      {"file", "status", "races", "horses", "date", "track", "reason"}
    status is "ok", "empty" (parsed but no horse comments found) or "error".
    """
    paths, skipped = discover(folder)
    out = []
    for name, reason in skipped:
        if report is not None:
            report.append({"file": name, "status": "skipped", "races": 0,
                           "horses": 0, "date": "", "track": "", "reason": reason})
        print("  SKIP  %-60s %s" % (name, reason), file=sys.stderr)
    for p in paths:
        try:
            rec = parse_file(p)
        except Exception as exc:                      # never kill the whole build
            if report is not None:
                report.append({"file": p.name, "status": "error", "races": 0,
                               "horses": 0, "date": "", "track": "",
                               "reason": "%s: %s" % (type(exc).__name__, exc)})
            print("  ERROR %-60s %s: %s" % (p.name, type(exc).__name__, exc),
                  file=sys.stderr)
            continue
        n_horses = sum(len(r["horses"]) for r in rec["races"])
        status = "ok" if n_horses else "empty"
        reason = ""
        if not n_horses:
            reason = ("no horse comments extracted — check the report layout, "
                      "or that the PDF has a text layer (a scanned image will "
                      "produce nothing)")
        elif not rec.get("date"):
            status, reason = "empty", "no date parsed from the header, so runs cannot join"
        if report is not None:
            report.append({"file": p.name, "status": status, "races": len(rec["races"]),
                           "horses": n_horses, "date": rec.get("date", ""),
                           "track": rec.get("track", ""), "reason": reason})
        print("  %-5s %-60s %s %-20s %d races %d horses"
              % (status.upper(), p.name, rec.get("date", "????-??-??"),
                 rec.get("track", "")[:20], len(rec["races"]), n_horses),
              file=sys.stderr)
        if status == "ok":
            out.append(rec)
    return out
