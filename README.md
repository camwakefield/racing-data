# racing-data

A small, shared store of **PF-independent** Australian racing signals — sectional
times (racing.com) and stewards-report trouble/excuse flags (Racing Victoria) —
normalised into per-horse JSON that your friends and the Cowork cloud task can
read over a plain GitHub raw URL.

Everything here is for private form study among a few people. It is **paper /
research only** — nothing in it is a betting instruction. If you ever make it
public, read the racing.com and Racing Victoria terms of use first: sharing your
own *derived figures* among friends is a very different footprint from
redistributing their raw data to the world.

## Why this exists

Punting Form's `pfai` is one model's opinion. To build a genuinely independent
second judge ("v5") we need raw, non-PF signals. Two of the best:

- **Sectionals** — who actually finished fastest (closing speed), which raw
  finishing positions hide.
- **Stewards reports** — the *excuses*: interference, held up, wide without
  cover, slow to begin, plus forward tells (blinkers coming, wants firmer going)
  and health cautions (bled, throat, suspended pending vet clearance).

Both describe a race that has **already finished**, so they are used
*backward-looking*: a runner's past sectionals + past trouble-notes inform its
**next** start. A horse that ran the fastest last-600 **and** was held up for
clear running is the classic next-start overlay — invisible to both PF and the
market.

## Layout

```
raw/
  sectionals/   drop racing.com CSVs here      (one file per race)
  stewards/     drop stewards reports here      (.txt, one file per meeting)
src/
  common.py            name normalisation + helpers
  parse_sectionals.py  CSV -> per-runner closing-speed figures
  parse_stewards.py    report text -> per-horse trouble/excuse flags
  build.py             joins both into data/*.json (run this after adding files)
  lookup.py            how a consumer reads one horse's recent signals
data/                  PUBLISHED output — commit this; the cloud task reads it
  horses.json          { "<NORM NAME>": {name, runs:[ newest-first ]} }
  meetings.json        ingest log (what's been added)
  index.json           counts + generated timestamp
```

## Daily workflow

1. Download the day's sectional CSVs into `raw/sectionals/` and the stewards
   reports into `raw/stewards/`.
2. `python3 src/build.py`
3. `git add -A && git commit -m "add <date>" && git push`

The store grows every day you do this; the more history, the richer each horse's
recent-form summary.

## How the cloud task reads it

The Cowork sandbox can't reach racing.com or Punting Form directly, but it can
`WebFetch` a public GitHub raw URL. Point it at:

```
https://raw.githubusercontent.com/<you>/racing-data/main/data/horses.json
```

then, for each of today's runners, apply the `lookup.py` logic:

```
python3 src/lookup.py "Friendzoned"
# -> {"last_start_excuse_index": 2, "best_close_rating_recent": ..., "health_caution": false, ...}
```

That summary is the shape v5 (or a v5-lite in the cloud task) turns into features
alongside the existing form data.

## Data dictionary

**Sectional (per run)** — `close_rating` is field-relative: `100 * (race best
last-600 time) / (this horse's last-600 time)`; 100 = fastest closer in that
race, lower = slower. `close_ratio` = late vs early section-speed (relative fade
measure within the field). `last600_t` / `last200_t` / `overall_t` are seconds.

**Steward (per run)** — `flags` from: `slow_begin, trouble, wide, held_up, keen,
faded, gear_change, tactics, condition, vet_health, underperf`. `excuse_index` =
count of forgive-flags (`trouble/slow_begin/wide/held_up`), minus 1 if it only
faded with no trouble; **higher = finishing position likely understates the
horse**. `health_flag` = a hard caution (needs vet clearance before racing).

## Known limits

- **Name matching** is by normalised name + date (country tags and punctuation
  stripped). Rare horses whose name literally starts with a comment-word could be
  clipped; when a companion runner list is available, validate names against it.
- The stewards extractor is **keyword-based**, so it's high-recall but not
  perfect — treat `excuse_index` as a screen, not gospel; the raw `comment` is
  kept on every record so you can always eyeball it.
- One `horses.json` is fine for a while; if it gets large, shard by month.
