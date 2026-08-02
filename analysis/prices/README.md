# Hand-transcribed market prices

**PAPER TRADING ONLY.**

Every file here was typed off a screenshot of a betting screen. Nothing in this
folder can be regenerated from `raw/` — if it is lost it has to be transcribed
again from images. That is the whole reason it lives in the repo rather than in
a scratch workspace.

Nothing under `analysis/` is read by `src/build.py`, and this path is outside
the workflow's `paths:` filter, so committing here does **not** trigger a
rebuild. That is deliberate.

## Format

Each module exposes:

```python
P = {race_no: [(name, barrier, decimal_win_price), ...]}
```

WIN prices only, scratchings excluded. Some modules also carry `SCR` (the
scratchings, for auditing field sizes against the store) and `ALIAS` (a map
from normalised screen name to normalised store key, where the sectional feed
and the betting screen spell a horse differently).

Two exceptions to the middle element:

- `prices_0801_flem.py` holds the **saddlecloth number**, not the barrier. It
  was extracted from a working file that never recorded barriers.
- `prices_0715.py` race 3 is **tote**, not fixed odds — see below.

Consumers bind that element to `_barrier` and discard it, so the distinction
does not affect any result, but it should not be relied on as a barrier.

## The meetings

| date | track | module | notes |
|---|---|---|---|
| 2026-03-07 | Flemington | `prices_0307.py` | backfilled screens |
| 2026-06-20 | Flemington | `prices_0620.py` | backfilled screens |
| 2026-06-27 | Caulfield | `prices_0627.py` | backfilled screens |
| 2026-07-04 | Flemington | `prices_0704.py` | screens near the jump |
| 2026-07-11 | Caulfield | `prices_0711.py` | backfilled screens |
| 2026-07-15 | Sandown Hillside | `prices_0715.py` | race 3 is tote — see below |
| 2026-07-18 | Flemington | `prices_0718.py` | backfilled screens |
| 2026-07-25 | Caulfield | `prices_0725.py` | backfilled screens |
| 2026-08-01 | Flemington | `prices_0801_flem.py` | saddlecloth numbers, not barriers |
| 2026-08-01 | Morphettville Parks | `prices_morph.py` | carries `ALIAS` |

Ten meetings, 90 races, all of which price with no runner dropped.

## The one impurity

`prices_0715.py` race 3 came off a screen that carried no fixed-odds columns at
all — only tote. Those nine numbers are final pool dividends struck after the
jump, not prices that were available to back. They book to 1.180, which sits
inside the same band as the fixed-odds races, so they behave; but they are a
different quantity and should not be quietly treated as backable. The module
has a `TOTE3` flag at the top: set it `False` and race 3 drops out.

## Checking a new module

Before trusting a transcription, reconcile it against the store:

1. **Field size.** `len(P[r]) + len(SCR[r])` must equal the store's runner count
   for that race. This is what pins the race numbering, which is otherwise
   inferred from the "Last Updated" stamps running in order across the images.
2. **Names.** Every `norm_name(name)` in `P` must resolve to a store key for
   that race. Anything left over is either a typo or a genuine spelling
   difference that belongs in `ALIAS`.
3. **Book.** The sum of `1/price` over the starters should land around
   1.17–1.22. Materially below that usually means a price was mistyped;
   materially above usually means a late scratching whose deduction is not in
   the screen, which is harmless because the consumers renormalise on the
   runners that actually started.

15 July passed all three with nothing left over: field sizes 13, 11, 9, 11, 12,
15, 14, 20 matching the store exactly, all 91 priced names resolving, and books
of 1.192, 1.196, 1.180, 1.199, 1.220, 1.216, 1.207, 1.212.

**PAPER TRADING ONLY.**
