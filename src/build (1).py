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

THREE SOURCES, ALL OPTIONAL. raw/sectionals/*.csv, raw/stewards/*, and now
raw/sectionals_pdf/*.pdf. The PDF is the long-form report behind the CSV and
carries the result -- finishing rank and margin -- plus barrier, jockey and
distance-to-rail per section. Coverage is partial by design: only some meetings
publish one. A run with no PDF looks exactly as it did before, so nothing
downstream may require run["pdf"].
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import norm_name
import parse_sectionals
import parse_sectionals_pdf
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
    # Same accounting for PDFs: one entry per file found, parsed or not, so a
    # PDF that silently fails is distinguishable from one never uploaded.
    #
    # TWO FOLDERS ON PURPOSE. raw/sectionals_pdf/ is the tidy home, but a PDF
    # dropped straight into raw/sectionals/ next to its own CSV is picked up
    # just the same -- 5191079_01.csv and 5191079_01.pdf sitting together is a
    # perfectly sensible way to file them, and it should not silently do
    # nothing. Each parser filters by extension, so neither trips over the
    # other's files.
    pdf_report = []
    pdf_recs = []
    for sub in ("sectionals_pdf", "sectionals"):
        pdf_recs += parse_sectionals_pdf.parse_dir(ROOT / "raw" / sub,
                                                   report=pdf_report)
    # A CSV is not a failed PDF. Drop those from the report so n_pdf_failed
    # counts real problems and does not read as 196 broken uploads.
    pdf_report = [r for r in pdf_report
                  if not (r["status"] == "skipped" and r["reason"] == "not a pdf")]
    # A browser that downloads the same report twice writes "x (1).pdf", and
    # both copies get uploaded. The merge itself is idempotent -- the second
    # copy overwrites the first with identical values -- but the counters would
    # report twice the races and twice the runners, which is a lie about
    # coverage. Keep the first copy of each (date, track, race).
    seen, uniq, n_dup = set(), [], 0
    for rec in pdf_recs:
        rk = (rec["date"], (rec["track"] or "").lower(), rec["race"])
        if rk in seen:
            n_dup += 1
            continue
        seen.add(rk)
        uniq.append(rec)
    pdf_recs = uniq

    # run map keyed by (norm_name, date) so both sources merge into one start
    runs = {}
    display = {}
    meetings = []

    def run_slot(key, date, track, distance, race):
        display.setdefault(key, None)
        rk = (key, date)
        if rk not in runs:
            runs[rk] = {"date": date, "track": track, "distance": distance,
                        "race": race, "sectional": None, "steward": None,
                        # keys always present so a consumer can read them
                        # without a .get() dance on every single run
                        "pdf": None, "scratched": False}
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
                # where the horse sat before the turn: 100 = led, 0 = last.
                # Display-only for now -- measure it before it gates anything.
                "early_pct": ru.get("early_pct"),
                "lens_off_600": ru.get("lens_off_600"),
                # False = the horse is IN the sectionals file but every section
                # came back speed 0 / time 0. That is a scratching or a tracker
                # failure, not a missing upload. The run is kept (nothing is
                # lost) but it must not be read as a completed start.
                "tracked": not ru.get("no_data"),
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

    # --- sectionals PDF: the result, plus where the horse actually ran -------
    n_pdf_runs = n_scratched = 0
    for rec in pdf_recs:
        meetings.append({"date": rec["date"], "track": rec["track"],
                         "type": "sectional_pdf", "source_file": rec["source_file"],
                         "count": len(rec["runners"]),
                         "condition": rec.get("track_rating") or ""})
        for ru in rec["runners"]:
            key = ru["key"]
            if not key:
                continue
            if not display.get(key):
                display[key] = ru["name"]
            slot = run_slot(key, rec["date"], rec["track"], rec["distance"], rec["race"])
            # The PDF names the race number; the CSV never does, so this fills a
            # gap for every meeting that has no stewards report.
            slot["race"] = slot["race"] or rec["race"]
            slot["distance"] = slot["distance"] or rec["distance"]
            slot["pdf"] = {
                # the result -- the one thing no other source in this store has
                "final_rank": ru["final_rank"], "won": ru["won"],
                "placed": ru["placed"], "margin_len": ru["margin_len"],
                "race_state": ru["race_state"],
                "barrier": ru["barrier"], "jockey": ru["jockey"],
                # ground lost/saved. dist_travelled is signed metres against the
                # winner's path and is blank for the winner itself. Measured on
                # one meeting it spans only -6..+3m and correlates 0.65 with
                # rail_max, 0.30 with rail_avg and ~0 with the finish -- real,
                # but small. Display and measure before it gates anything.
                "dist_travelled": ru["dist_travelled"],
                "rail_avg": ru["rail_avg"], "rail_max": ru["rail_max"],
                "rail_early": ru["rail_early"], "rail_late": ru["rail_late"],
                # position in running, published rather than derived
                "settled": ru["settled"], "rank_at_800": ru["rank_at_800"],
                "rank_at_600": ru["rank_at_600"],
                "stride_m": ru["stride_m"], "stride_hz": ru["stride_hz"],
                "avg_kmh": ru["avg_kmh"], "top_kmh": ru["top_kmh"],
                "fastest_section_t": ru["fastest_section_t"],
                "fastest_section": ru["fastest_section"],
                "track_rating": rec["track_rating"], "weather": rec["weather"],
                "rail_position": rec["rail_position"],
                "race_name": rec["race_name"],
                "sections": ru["sections"],
            }
            n_pdf_runs += 1

        # A scratching still appears in the sectionals CSV with an all-zero
        # trace, so the store banks it as a start. The PDF names them outright:
        # mark from evidence rather than inferring from missing data. The run
        # stays -- it is flagged, not deleted.
        for s in rec["scratched"]:
            rk = (s["key"], rec["date"])
            if rk in runs:
                runs[rk]["scratched"] = True
                runs[rk]["race"] = runs[rk]["race"] or rec["race"]
                n_scratched += 1

    horses = {}
    for (key, date), run in runs.items():
        horses.setdefault(key, {"name": display.get(key) or key, "runs": []})
        horses[key]["runs"].append(run)
    for h in horses.values():
        h["runs"].sort(key=lambda x: x["date"], reverse=True)

    n_runs = sum(len(h["runs"]) for h in horses.values())
    n_untracked = sum(1 for r in runs.values()
                      if r["sectional"] and not r["sectional"].get("tracked"))
    bad = [r for r in stewards_report if r["status"] != "ok"]
    bad_pdf = [r for r in pdf_report if r["status"] != "ok"]
    index = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "n_horses": len(horses), "n_runs": n_runs,
        "n_sectional_files": len(sec_recs), "n_stewards_files": len(stw_recs),
        # PDF coverage is deliberately partial -- these are for seeing how far
        # it reaches, not for alarm when they are low.
        "n_pdf_files": len(pdf_recs), "n_pdf_found": len(pdf_report),
        "n_pdf_failed": len(bad_pdf), "n_pdf_runs": n_pdf_runs,
        # same race uploaded twice, e.g. "5191079_01 (1).pdf" -- ignored, not
        # an error, but worth seeing so the folder can be tidied
        "n_pdf_duplicates": n_dup,
        "n_scratched_marked": n_scratched,
        # runs that exist but have no GPS trace at all (scratchings, tracker
        # failures). Kept in the store, flagged so they are not read as starts.
        "n_untracked": n_untracked,
        "pdf_problems": bad_pdf,
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
    (out / "pdf_report.json").write_text(json.dumps(pdf_report, indent=1))
    return index, horses


if __name__ == "__main__":
    index, horses = build()
    print("BUILT:", json.dumps({k: v for k, v in index.items()
                                if k not in ("stewards_problems", "pdf_problems")}))
    if index["n_stewards_failed"]:
        print("\n!! %d stewards file(s) found but NOT used:" % index["n_stewards_failed"])
        for r in index["stewards_problems"]:
            print("   %-8s %-55s %s" % (r["status"], r["file"], r["reason"]))
    if index["n_pdf_failed"]:
        print("\n!! %d sectionals PDF(s) found but NOT used:" % index["n_pdf_failed"])
        for r in index["pdf_problems"]:
            print("   %-8s %-55s %s" % (r["status"], r["file"], r["reason"]))
    print()
    print("\nSample horse records:")
    # Show the RICHEST runs, not each horse's latest. Sampling runs[0] hid the
    # PDF join entirely whenever a horse had raced again since its PDF meeting.
    every = [(h["name"], r) for h in horses.values() for r in h["runs"]]
    every.sort(key=lambda x: (-(bool(x[1]["sectional"]) + bool(x[1]["steward"])
                                + bool(x[1]["pdf"])), not x[1]["pdf"]))
    shown = 0
    for name, r in every:
        h = {"name": name}
        bits = []
        if r["sectional"]:
            bits.append("L600 %s / CR %s%s" % (
                r["sectional"]["last600_t"], r["sectional"]["close_rating"],
                "" if r["sectional"].get("tracked") else " (NO TRACE)"))
        if r["pdf"]:
            bits.append("fin %s by %sL / rail %s" % (
                r["pdf"]["final_rank"], r["pdf"]["margin_len"], r["pdf"]["rail_avg"]))
        if r["steward"]:
            bits.append("excuse %d %s" % (r["steward"]["excuse_index"], r["steward"]["flags"]))
        if r.get("scratched"):
            bits.append("SCRATCHED")
        print("  %-22s %s  %s" % (h["name"], r["date"], " | ".join(bits)))
        shown += 1
        if shown >= 5:
            break
