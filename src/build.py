"""Join raw sectionals + stewards into the published, per-horse data store.

Reads everything under raw/sectionals/*.csv and raw/stewards/*.txt, normalises
horse names, and writes derived JSON to data/ that both your friends and the
Cowork cloud task can read over a plain GitHub raw URL:

  data/horses.json    { "<NORM NAME>": {"name","runs":[ ...one per start... ]} }
  data/meetings.json  [ {date,track,type,source_file,count} ...]  (ingest log)
  data/index.json     { generated_utc, n_horses, n_runs, n_sectional, n_stewards }

A "run" is one horse in one race on one date; when a sectionals file and a
stewards report cover the SAME meeting, that horse's run carries both the
closing-speed figures and the trouble/excuse flags. Runs are newest-first, so a
consumer just reads horses[name]["runs"][0] for the most recent start.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import norm_name
import parse_sectionals
import parse_stewards

ROOT = Path(__file__).resolve().parent.parent


def _track_key(track):
    return (track or "").strip().lower()


def build():
    sec_recs = parse_sectionals.parse_dir(ROOT / "raw" / "sectionals")
    # stewards_report gets one entry per FILE FOUND, including the ones that
    # were skipped or produced nothing. Without it a file that silently fails
    # to parse is indistinguishable from a file that was never uploaded.
    stewards_report = []
    stw_recs = parse_stewards.parse_dir(ROOT / "raw" / "stewards",
                                        report=stewards_report)

    # run map keyed by (norm_name, date) so both sources merge into one start
    runs = {}
    display = {}
    meetings = []

    def run_slot(key, date, track, distance, race):
        display.setdefault(key, None)
        rk = (key, date)
        if rk not in runs:
            runs[rk] = {"date": date, "track": track, "distance": distance,
                        "race": race, "sectional": None, "steward": None}
        return runs[rk]

    for rec in sec_recs:
        meetings.append({"date": rec["date"], "track": rec["track"], "type": "sectional",
                         "source_file": rec["source_file"], "count": len(rec["runners"])})
        for ru in rec["runners"]:
            key = ru["key"]
            if not key:
                continue
            if not display.get(key):
                display[key] = ru["name"].title() if ru["name"].isupper() else ru["name"]
            slot = run_slot(key, rec["date"], rec["track"], rec["distance"], None)
            slot["distance"] = slot["distance"] or rec["distance"]
            slot["sectional"] = {
                "last600_t": ru["last600_t"], "last200_t": ru["last200_t"],
                "overall_t": ru["overall_t"], "close_rating": ru["close_rating"],
                "close_ratio": ru["close_ratio"], "top_spd": ru["top_spd"],
                "race_name": rec["race_name"],
            }

    for rec in stw_recs:
        n = sum(len(r["horses"]) for r in rec["races"])
        meetings.append({"date": rec["date"], "track": rec["track"], "type": "stewards",
                         "source_file": rec["source_file"], "count": n,
                         "condition": rec["header"].get("condition", "")})
        for r in rec["races"]:
            for hh in r["horses"]:
                key = hh["key"]
                if not key:
                    continue
                if not display.get(key):
                    display[key] = hh["name"]
                slot = run_slot(key, rec["date"], rec["track"], r["distance"], r["race"])
                slot["race"] = slot["race"] or hh["race"]
                slot["distance"] = slot["distance"] or r["distance"]
                slot["steward"] = {
                    "flags": hh["flags"], "excuse_index": hh["excuse_index"],
                    "health_flag": hh["health_flag"], "gear_change": hh["gear_change"],
                    "underperf": hh["underperf"], "condition": rec["header"].get("condition", ""),
                    "comment": hh["comment"],
                }

    horses = {}
    for (key, date), run in runs.items():
        horses.setdefault(key, {"name": display.get(key) or key, "runs": []})
        horses[key]["runs"].append(run)
    for h in horses.values():
        h["runs"].sort(key=lambda x: x["date"], reverse=True)

    n_runs = sum(len(h["runs"]) for h in horses.values())
    bad = [r for r in stewards_report if r["status"] != "ok"]
    index = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_horses": len(horses), "n_runs": n_runs,
        "n_sectional_files": len(sec_recs), "n_stewards_files": len(stw_recs),
        # discovery accounting — n_stewards_files counts only what PARSED, so
        # compare it against n_stewards_found to spot silently-ignored uploads
        "n_stewards_found": len(stewards_report),
        "n_stewards_failed": len(bad),
        "stewards_problems": bad,
    }

    out = ROOT / "data"
    out.mkdir(exist_ok=True)
    (out / "horses.json").write_text(json.dumps(horses, indent=1, sort_keys=True))
    (out / "meetings.json").write_text(json.dumps(
        sorted(meetings, key=lambda m: (m["date"], m["type"])), indent=1))
    (out / "index.json").write_text(json.dumps(index, indent=1))
    (out / "stewards_report.json").write_text(json.dumps(stewards_report, indent=1))
    return index, horses


if __name__ == "__main__":
    index, horses = build()
    print("BUILT:", json.dumps({k: v for k, v in index.items()
                                if k != "stewards_problems"}))
    if index["n_stewards_failed"]:
        print("\n!! %d stewards file(s) found but NOT used:" % index["n_stewards_failed"])
        for r in index["stewards_problems"]:
            print("   %-8s %-55s %s" % (r["status"], r["file"], r["reason"]))
    print()
    print("\nSample horse records:")
    for key in list(horses)[:4]:
        h = horses[key]
        r = h["runs"][0]
        bits = []
        if r["sectional"]:
            bits.append("L600 %s / close_rating %s" % (r["sectional"]["last600_t"], r["sectional"]["close_rating"]))
        if r["steward"]:
            bits.append("excuse %d %s" % (r["steward"]["excuse_index"], r["steward"]["flags"]))
        print("  %-22s %s  %s" % (h["name"], r["date"], " | ".join(bits)))
