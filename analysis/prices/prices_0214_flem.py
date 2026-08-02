"""Flemington, Saturday 14 February 2026 -- WIN prices.

Transcribed from eleven screenshots of the full-field betting tables
(No / Runner (Barrier) / FIXED ODDS Win, Place / TOTE Win, Place).
WIN column only.  Scratchings excluded from P, recorded in SCR for audit.

Every screen here carries fixed-odds columns, so unlike prices_0715.py there
is no tote impurity in this meeting -- all ten races are backable prices.

Race numbers are inferred from the "Last Updated" stamps, which run strictly
in order:
R1 12:07:48, R2 12:38:59, R3 13:13:22, R4 13:48:27, R5 14:23:51,
R6 14:59:14, R7 15:33:05, R8 16:15:11, R9 16:53:29, R10 17:32:52.
R2 spans two images (runners 1-15, then 8-16); the overlap agrees exactly.

Field sizes including scratchings are 7, 16, 7, 10, 10, 11, 9, 8, 13, 11 and
match the store's runner count for each race exactly, so the numbering above
is confirmed by more than the timestamps.

The one race that needs explaining is R5.  The screen shows nine rows and a
"Substitutes: 7. RUE DE ROYALE" banner; the store holds ten.  The tenth is
INDOLA, which was scratched early enough that RUE DE ROYALE substituted in
and INDOLA never rendered on the betting screen at all.  It carries
close_rating None in the store, i.e. it is an inert row.  It is recorded in
SCR below with a null barrier so the field-size check still balances.

Book percentages on the starters as listed:
R1 1.190, R2 1.201, R3 1.176, R4 1.173, R5 1.183, R6 1.192,
R7 1.180, R8 1.164, R9 1.182, R10 1.190.  R8 is the tightest book in the
priced sample at 1.164, marginally under the 1.17-1.22 band the other
meetings sit in; it is an eight-runner race with no scratchings and two
short-priced favourites (TENTYRIS 2.60, GIGA KICK 3.40), so the tight
book looks real rather than a mistyped price.

Reconciliation against the store: 102 screen rows against 102 store rows,
race by race, with every one of the 91 priced names resolving to a store
key and no ALIAS entries required.  All 91 also carry both a close_rating
and a full sections table, so this meeting contributes to the market test
and the tempo test alike.

P = {race_no: [(name, barrier, decimal_win_price), ...]}

PAPER TRADING ONLY.
"""

P = {
    1: [
        ("Zambales", 6, 2.20),
        ("Stellar Cipher", 7, 18.00),
        ("Diameter", 5, 13.00),
        ("Hard Kick", 4, 3.10),
        ("Shah Jahan", 3, 5.50),
        ("Autumn Lover", 1, 15.00),
        ("Grinzinger Heart", 2, 31.00),
    ],
    2: [
        ("Chasing Aphrodite", 6, 26.00),
        ("My Brothers Keeper", 10, 23.00),
        ("Flamin' Romans", 2, 15.00),
        ("Sunsets", 4, 8.00),
        ("Fiorenot", 9, 3.00),
        ("Taka Speed", 12, 4.80),
        ("Otago", 8, 23.00),
        ("Tarvue", 5, 14.00),
        ("Trapalanda", 3, 8.50),
        ("Unseen Ruler", 1, 51.00),
        ("Extreme Virtue", 13, 21.00),
        ("Georgie Get Mad", 11, 23.00),
        ("Seafall", 7, 26.00),
        ("Balinor", 14, 251.00),
    ],
    3: [
        ("Ole Dancer", 6, 2.70),
        ("Sass Appeal", 1, 2.00),
        ("Custom", 2, 5.00),
        ("Sky Watcher", 5, 26.00),
        ("Next Jen", 4, 21.00),
        ("Celibate", 3, 51.00),
    ],
    4: [
        ("Immortal Star", 1, 2.00),
        ("Perilous Fighter", 2, 8.00),
        ("Umgawa", 7, 31.00),
        ("Tango Jewel", 4, 3.90),
        ("Mystic Reign", 3, 9.00),
        ("Mr Magnus", 6, 15.00),
        ("Jakivy", 5, 13.00),
        ("Nostra Bella", 8, 201.00),
    ],
    5: [
        ("Pounding", 3, 71.00),
        ("Highlights", 6, 126.00),
        ("Extratwo", 1, 21.00),
        ("Ndola", 5, 4.40),
        ("Great Maximus", 8, 4.60),
        ("Modown", 9, 23.00),
        ("Rue De Royale", 2, 2.40),
        ("Fission", 4, 8.50),
        ("Behaviour", 7, 11.00),
    ],
    6: [
        ("Berkeley Square", 7, 11.00),
        ("Saint George", 6, 2.20),
        ("Newfoundland", 2, 9.00),
        ("Scary", 3, 6.50),
        ("Garachico", 1, 31.00),
        ("Jenni's Meadow", 4, 11.00),
        ("Paradise Storm", 10, 26.00),
        ("Stylish Secret", 9, 7.00),
        ("Dictionary", 5, 41.00),
        ("Steel Run", 8, 19.00),
    ],
    7: [
        ("Birdman", 2, 14.00),
        ("Cafe Millenium", 6, 4.40),
        ("Arran Bay", 5, 23.00),
        ("Aztec Ruler", 3, 12.00),
        ("Sabaj", 1, 2.90),
        ("Matcha Latte", 8, 4.40),
        ("Enxuto", 7, 9.50),
        ("Scheelite", 4, 13.00),
    ],
    8: [
        ("Giga Kick", 6, 3.40),
        ("Baraqiel", 5, 9.00),
        ("Benedetta", 1, 26.00),
        ("Tentyris", 7, 2.60),
        ("Beiwacht", 3, 8.50),
        ("Marhoona", 4, 18.00),
        ("My Gladiola", 8, 7.00),
        ("Military Tycoon", 2, 51.00),
    ],
    9: [
        ("West Of Swindon", 7, 8.00),
        ("Sixties", 9, 1.60),
        ("Bingi", 11, 101.00),
        ("Officiate", 4, 51.00),
        ("Romantic Encounter", 3, 15.00),
        ("Express Class", 8, 21.00),
        ("Asakura", 6, 5.50),
        ("Loud Charlie", 10, 31.00),
        ("Wetumpka", 1, 31.00),
        ("Beyond Question", 2, 34.00),
        ("Earthing", 5, 81.00),
    ],
    10: [
        ("Philia", 4, 5.00),
        ("Real Class", 1, 101.00),
        ("Wrote To Arataki", 2, 3.50),
        ("Too Darn Discreet", 3, 4.60),
        ("Samangu", 7, 19.00),
        ("Eternal Flame", 6, 23.00),
        ("Sea What I See", 5, 10.00),
        ("Miss Tarzy", 8, 26.00),
        ("Grid Girl", 9, 7.00),
        ("Paradise City", 10, 10.00),
    ],
}

# Scratchings, kept for audit against the store's field sizes.
# INDOLA (race 5) never appeared on the betting screen -- see the module
# docstring -- so it carries a null barrier.
SCR = {
    1: [],
    2: [("Night Endeavor", 13), ("Double Cherry", 10)],
    3: [("Privateer", 4)],
    4: [("Photograph", 8), ("Jennyanydots", 1)],
    5: [("Indola", None)],
    6: [("Ardakan", 11)],
    7: [("Justadeel", 5)],
    8: [],
    9: [("Space Rider", 2), ("Pictor", 7)],
    10: [("Princess Que", 3)],
}

# Spelling artifacts between the sectional feed and the betting screen.
# Key = normalised screen name, value = normalised store key.
# norm_name already strips apostrophes, so FLAMIN' ROMANS and JENNI'S MEADOW
# resolve without help.  Nothing else needed here.
ALIAS = {}
