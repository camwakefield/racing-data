"""Flemington, Saturday 20 June 2026 -- fixed-odds WIN prices.

Transcribed from the full-field fixed-odds tables (No / Runner (Barrier) /
FIXED ODDS Win, Place / TOTE Win, Place).  WIN column only.  Scratchings
excluded from P, recorded in SCR for audit.

RACE NUMBERING IS ANCHORED ABSOLUTELY, not merely ordered.  Three screens
carry a "Running Double (a,b)" line in the Pools footer, which names the race
outright:
    Running Double (1,2)  ->  race 1   (stamp Sat 20 Jun 11:58:26)
    Running Double (6,7)  ->  race 6   (stamp 14:47:58)
    Running Double (7,8)  ->  race 7   (stamp 15:27:49)
The remaining screens are placed by their "Last Updated" stamps, which run
strictly in order and at a ~34-minute cadence:
    R1 11:58:26, R2 12:28:29, R3 (no stamp), R4 13:39:22, R5 14:13:21,
    R6 14:47:58, R7 15:27:49, R8 16:03:28, R9 16:41:24.

CAVEAT ON R3.  Its screen carries no stamp, so its race number is INFERRED
from the anomalous 70-minute gap between 12:28:29 and 13:39:22 -- exactly one
race wide.  The screen is also cut off after runner 13, so completeness was
initially UNCONFIRMED.  It is now confirmed by the barrier argument below:
R3's thirteen visible runners carry barriers 1..13 with no gaps and no
repeats, which cannot happen if runners are missing.

BARRIERS.  Unlike 27 June, this meeting prints "(Barrier)" for EVERY runner,
so there are no Nones anywhere.  Barriers are the POST-SCRATCHING reassigned
ones for starters: in all nine races the starters' barriers form exactly
1..n with no gaps.  Scratched runners retain their pre-reassignment barrier,
which is why a scratching's barrier can duplicate a starter's (e.g. R1 #16
FRANKEL'S WORD (13) against #3 RUNNING RICH (13)).  SCR's second field is
therefore a BARRIER here, not a saddlecloth number as it was on 27 June.

P   = {race_no: [(name, barrier, decimal_win_price), ...]} in saddlecloth
      order.
SCR = {race_no: [(name, barrier_as_printed), ...]} in saddlecloth order.

Total priced starters: 113, which matches the store's 113 final_rank rows
for this meeting exactly.

PAPER TRADING ONLY.
"""

P = {
    1: [
        ("Fontein Jewel", 10, 7.50),
        ("Portarlington", 1, 6.50),
        ("Running Rich", 13, 12.00),
        ("Star Of Macedon", 14, 5.50),
        ("Baccano", 8, 31.00),
        ("Helvecchio", 4, 26.00),
        ("Ko Phangan", 5, 12.00),
        ("Make 'Em All", 9, 51.00),
        ("Satono's Shout", 3, 10.00),
        ("Youmzain Express", 6, 9.50),
        ("Gallantry", 11, 14.00),
        ("Insolence", 7, 6.50),
        ("South Yarra Miss", 12, 81.00),
        ("Shinsiena", 2, 41.00),
    ],
    2: [
        ("Decalogue", 7, 3.50),
        ("Arabian Prince", 10, 16.00),
        ("Our Chief", 15, 8.00),
        ("Harbour Town", 5, 16.00),
        ("Mahers Landing", 6, 17.00),
        ("Hard Evidence", 12, 23.00),
        ("Nihancan", 13, 71.00),
        ("Think Your Amazing", 3, 10.00),
        ("Colizzi", 2, 71.00),
        ("Kings Reflection", 14, 4.20),
        ("Noble Work", 9, 61.00),
        ("Salt Spray", 8, 23.00),
        ("She's Got The Cash", 1, 17.00),
        ("Set Me Free", 11, 18.00),
        ("Morisu Ojo", 4, 81.00),
    ],
    3: [
        ("Bold Soul", 7, 7.00),
        ("Tempesti", 9, 12.00),
        ("Virtuous Circle", 6, 10.00),
        ("Alder", 12, 10.00),
        ("The Western Front", 13, 5.00),
        ("Tajanis", 11, 18.00),
        ("Howlin' Rain", 8, 13.00),
        ("Kingofwallstreet", 10, 12.00),
        ("Mission Of Love", 1, 26.00),
        ("Mr Waterville", 5, 18.00),
        ("Vegas Jack", 4, 9.50),
        ("Highland Blaze", 2, 11.00),
        ("Samuel Langhorne", 3, 16.00),
    ],
    4: [
        ("Blethyn", 11, 7.50),
        ("La Astro Chat", 4, 16.00),
        ("Choir Point", 6, 4.20),
        ("Recuperato", 1, 16.00),
        ("Fehmarn", 7, 31.00),
        ("I'mateez", 5, 9.50),
        ("Jenni The Ninja", 10, 9.50),
        ("Prestar", 8, 4.40),
        ("Tatakai Uta", 2, 26.00),
        ("Ulfberht", 9, 21.00),
        ("Poker", 3, 7.50),
    ],
    5: [
        ("Madero", 2, 17.00),
        ("Wonder Kid", 3, 101.00),
        ("Outta Compton", 10, 41.00),
        ("Angland", 14, 41.00),
        ("Fridge Monster", 7, 61.00),
        ("Ten Commandments", 5, 2.10),
        ("Capper Thirtynine", 1, 14.00),
        ("Semillion", 11, 81.00),
        ("Sought After", 6, 14.00),
        ("Supernima", 9, 26.00),
        ("Thebelmontgangster", 4, 4.20),
        ("Ruakaka Raider", 12, 51.00),
        ("Rosa Aotearoa", 8, 12.00),
        ("Castle On High", 13, 26.00),
    ],
    6: [
        ("Duchess Zou", 13, 5.00),
        ("Miss Aria", 12, 10.00),
        ("It's A Knockout", 4, 9.00),
        ("Flyer", 6, 26.00),
        ("Stylish", 10, 7.00),
        ("Apache Song", 9, 81.00),
        ("First Chorus", 7, 4.60),
        ("Changing Colours", 3, 14.00),
        ("Husk", 5, 10.00),
        ("Silent Shares", 11, 15.00),
        ("Sweet Jasmine", 1, 14.00),
        ("Lake Vostok", 2, 26.00),
        ("This Time Girl", 8, 41.00),
    ],
    7: [
        ("Dragonstone", 7, 18.00),
        ("New York Lustre", 9, 5.00),
        ("Recommendation", 10, 15.00),
        ("Losesomewinmore", 11, 3.20),
        ("Taunting", 5, 151.00),
        ("De Bergerac", 2, 4.60),
        ("Samangu", 12, 41.00),
        ("Pisanello", 6, 101.00),
        ("Contemporary", 4, 71.00),
        ("Royal Insignia", 3, 14.00),
        ("Winnasedge", 8, 8.00),
        ("Moby Dick", 1, 11.00),
    ],
    8: [
        ("Jimmy The Bear", 1, 4.60),
        ("Saint George", 3, 8.00),
        ("Punch Lane", 4, 5.50),
        ("Al Duca", 11, 4.80),
        ("Buckets Ridge", 5, 34.00),
        ("Detonator Jack", 10, 16.00),
        ("Freedom Rally", 2, 51.00),
        ("Highlights", 8, 26.00),
        ("Rumbled Again", 7, 23.00),
        ("Seafall", 9, 6.00),
        ("Beach Pad", 6, 10.00),
    ],
    9: [
        ("Highvol", 5, 19.00),
        ("Kaleo", 7, 5.00),
        ("Flying Done", 4, 7.00),
        ("Dirnaseer", 10, 4.60),
        ("Shoma", 9, 34.00),
        ("Paddypie", 1, 3.00),
        ("Obvious", 6, 9.50),
        ("Palladium", 2, 41.00),
        ("Prestige Snitzel", 3, 81.00),
        ("Lucky Lucky Boom", 8, 15.00),
    ],
}

# Second field = BARRIER as printed on the screen (see docstring).  These are
# pre-reassignment barriers, so they may collide with a starter's barrier.
SCR = {
    1: [("From Yesterday", 17), ("Frankel's Word", 13),
        ("Tears Of Happiness", 15)],
    2: [("Soldier Boi", 3), ("Rainsun", 5), ("Blindato", 17),
        ("Madesian", 7)],
    3: [],
    4: [("Ice Kool", 2), ("Sauvitude", 3), ("Uyuni", 8)],
    5: [("The Pendragon", 9), ("Komachi", 8), ("Yam", 17),
        ("Make It Sweet", 10)],
    6: [("Lady Jones", 3), ("Mystic Wonder", 16), ("Zunna", 10)],
    7: [("Bustling", 8), ("Gin A Tonic", 13)],
    8: [("Just Folk", 10), ("St Lawrence", 13), ("See That Storm", 14),
        ("Farhh Flung", 11)],
    9: [("Maldini", 10), ("Golden Horizon", 12), ("Miss Revealing", 2)],
}

# Numbered field size per race, from the saddlecloth numbering on the screens.
FIELD = {1: 17, 2: 19, 3: 13, 4: 14, 5: 18, 6: 16, 7: 14, 8: 15, 9: 13}

# Substitutes (emergencies promoted into the field), noted on the screens:
# R3 5. THE WESTERN FRONT, R6 2. DUCHESS ZOU, R7 4. LOSESOMEWINMORE,
# R8 2. JIMMY THE BEAR.  All are priced above.

# Spelling artifacts between the sectional feed and the betting screen.
# Key = normalised screen name, value = normalised store key.
ALIAS = {}
