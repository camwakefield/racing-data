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
]}


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
    while len(name) > 1 and name[-1].lower().strip("()'’.") in CONNECTORS:
        name.pop()
    return " ".join(name).strip(" -—–"), " ".join(toks[idx:]).strip(" -—–\t")


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


def parse_file(path):
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        text = pdf_text(path)
    else:
        text = open(path, encoding="utf-8", errors="replace").read()
    text = unwrap(text)
    header = parse_header(text)
    club = header.get("club", "")
    if ":" in club:
        track = club.split(":")[0].strip()
    else:
        track = re.sub(r"\s+(Jockey|Turf|Racing)\s+Club$", "", club).strip()
    track = re.sub(r"^(Sportsbet|TAB|Ladbrokes|Neds|BetEasy)\s+", "", track, flags=re.I).strip()

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
                "name": name, "key": norm_name(name), "race": rno,
                "flags": sorted(flags.keys()), "excuse_index": excuse_index,
                "health_flag": "vet_health" in flags, "gear_change": "gear_change" in flags,
                "underperf": "underperf" in flags, "comment": comment,
            })
        races.append({"race": rno, "distance": dist, "name": hdr_line, "horses": horses})

    return {"track": track, "date": header.get("date", ""), "header": header,
            "source_file": Path(path).name, "races": races}


def parse_dir(folder):
    out = []
    paths = sorted(list(Path(folder).glob("*.txt")) + list(Path(folder).glob("*.pdf")))
    for p in paths:
        out.append(parse_file(p))
    return out
