"""Parse an RV-style stewards report (plain text) into structured per-horse signals.

We pull the meeting header (track condition, going stick, rail, weather), split
the body into races ("Race N ... NNNN metres:"), split each race into per-horse
comment blocks, then keyword-flag each block into buckets that matter for form:

  trouble      : the horse met interference/hard luck (forgive the run)
  slow_begin   : lost ground at the start
  wide         : raced wide / without cover (did it tough)
  held_up      : couldn't get clear running (unlucky, untested)
  keen         : over-raced / wasted energy early
  faded        : weakened / eased down / failed to run on
  gear_change  : blinkers or gear flagged for next time
  tactics      : change-of-tactics noted
  condition    : rider/trainer says it wants firmer/softer going
  vet_health   : bled / throat / lame / suspended pending clearance  (caution)
  underperf    : "performed below market expectations"

`excuse_index` = count of the *forgive* buckets (trouble/slow_begin/wide/held_up)
minus a small penalty if it merely faded with no trouble. Higher = the finishing
position likely understates the horse -> next-start improver / overlay candidate.
`health_flag` is a hard caution: something needs a vet clearance before it runs.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import norm_name

RACE_HDR = re.compile(r"^Race\s+(\d+)\b(.*?)(\d{3,4})\s*met", re.I)
RACE_ANY = re.compile(r"^Race\s+(\d+)\b", re.I)

# keyword -> bucket. Matched case-insensitively as substrings.
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


# Lowercase connectors that can appear *inside* a horse name.
CONNECTORS = {"of", "the", "a", "an", "and", "'n'", "n", "al", "my", "no", "that",
              "de", "du", "da", "la", "le", "van", "von", "el", "to", "on", "in", "for"}

# Capitalised words that BEGIN a stewards comment (never a name's 2nd+ token).
# If we hit one after the first token, the name has ended.
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
    """Return (name, comment) from one stewards line, cutting the name at the
    first comment-starter word. Country tags like (NZ) stay attached."""
    toks = line.split()
    if not toks:
        return None, ""
    name = []
    idx = 0
    for i, tok in enumerate(toks):
        raw = tok
        core = raw.strip(" -—–,").strip()
        if not core:
            if name:
                break
            continue
        low = core.lower().strip("()'’.")
        is_country = bool(re.fullmatch(r"\(?[A-Za-z]{2,3}\)?", core)) and core.strip("()").isupper()
        if i == 0:
            name.append(core)
            idx = i + 1
            continue
        if is_country:                       # (NZ) / (IRE) — part of the name
            name.append(core); idx = i + 1; continue
        if low in STOP:                       # comment begins here
            break
        if low in CONNECTORS:                 # internal connector, keep going
            name.append(core); idx = i + 1; continue
        if core[:1].isupper() or core[:1].isdigit():
            name.append(core); idx = i + 1; continue
        break                                 # lowercase, non-connector -> comment
    # A name never ends in a connector — if we swept one up because the comment
    # began "A post-race…" / "The mare…", drop it (fixes "Divine Thoughts A").
    while len(name) > 1 and name[-1].lower().strip("()'’.") in CONNECTORS:
        name.pop()
    name_str = " ".join(name).strip(" -—–")
    comment = " ".join(toks[idx:]).strip(" -—–\t")
    return name_str, comment


def _split_horse_blocks(text):
    """Within one race section, yield (horse_name, comment) blocks (one per line)."""
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


def parse_header(text):
    h = {"track": "", "condition": "", "going_stick": "", "weather": "", "rail": "",
         "date": "", "club": ""}
    lines = [l.strip() for l in text.splitlines()]
    if lines:
        h["club"] = lines[0].strip()

    def after(label):
        for i, l in enumerate(lines):
            if l.rstrip(":").lower() == label:
                for j in range(i + 1, min(i + 3, len(lines))):
                    if lines[j]:
                        return lines[j]
        return ""
    h["condition"] = after("track")
    h["going_stick"] = after("going stick")
    h["weather"] = after("weather")
    h["rail"] = after("rail")
    raw_date = after("date")
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
    text = open(path, encoding="utf-8", errors="replace").read()
    header = parse_header(text)
    track = header.get("club", "").replace(" Jockey Club", "").replace(" Turf Club", "").strip()

    # slice the body into race sections
    lines = text.splitlines()
    idxs = [i for i, l in enumerate(lines) if RACE_ANY.match(l.strip())]
    # stop the last race at the first "SWAB"/"Raceday Summary" marker
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
                "key": norm_name(name),
                "race": rno,
                "flags": sorted(flags.keys()),
                "excuse_index": excuse_index,
                "health_flag": "vet_health" in flags,
                "gear_change": "gear_change" in flags,
                "underperf": "underperf" in flags,
                "comment": comment,
            })
        races.append({"race": rno, "distance": dist, "name": hdr_line, "horses": horses})

    return {"track": track, "date": header.get("date", ""), "header": header,
            "source_file": Path(path).name, "races": races}


def parse_dir(folder):
    out = []
    for p in sorted(Path(folder).glob("*.txt")):
        out.append(parse_file(p))
    return out


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "raw/stewards"
    p = Path(target)
    recs = [parse_file(p)] if p.is_file() else parse_dir(p)
    for rec in recs:
        h = rec["header"]
        print("== %s  %s  | %s | rail %s | %s" % (
            rec["date"], rec["track"], h["condition"], h["rail"], h["weather"]))
        allh = [hh for r in rec["races"] for hh in r["horses"]]
        forgive = sorted([hh for hh in allh if hh["excuse_index"] > 0],
                         key=lambda x: -x["excuse_index"])
        print("  -- FORGIVE (excuse_index>0):")
        for hh in forgive:
            print("     R%d %-18s idx %d  %s" % (hh["race"], hh["name"], hh["excuse_index"], ",".join(hh["flags"])))
        health = [hh for hh in allh if hh["health_flag"]]
        print("  -- HEALTH CAUTION:", ", ".join("R%d %s" % (h["race"], h["name"]) for h in health))
        gear = [hh for hh in allh if hh["gear_change"]]
        print("  -- GEAR/BLINKERS FLAGGED:", ", ".join("R%d %s" % (h["race"], h["name"]) for h in gear))
