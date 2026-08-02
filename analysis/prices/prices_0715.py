"""Sandown Hillside, Wednesday 15 July 2026 -- WIN prices.

Transcribed from nine screenshots of the full-field betting tables
(No / Runner (Barrier) / FIXED ODDS Win, Place / TOTE Win, Place).
WIN column only.  Scratchings excluded from P, recorded in SCR for audit.

Race numbers are inferred from the "Last Updated" stamps, which run strictly
in order:
R1 12:28:25, R2 13:03:41, R3 13:37:59, R4 14:13:41, R5 14:48:49,
R6 (stamp clipped), R7 15:59:31, R8 16:32:50.
R8 spans two images (runners 1-15, then 13-20); the overlap agrees exactly.

Field sizes read off the screens are 13, 11, 9, 11, 12, 15, 14, 20 and match
the store's runner count for each race exactly, so the race numbering above is
confirmed by more than the timestamps.

*** RACE 3 IS TOTE, NOT FIXED ODDS. ***  That screen carried no fixed-odds
columns at all -- only TOTE Win / Place -- so race 3's prices are final tote
dividends.  They book to 1.180, which is in the same band as the fixed-odds
races here, but they are a different quantity: a pool dividend struck after
the jump rather than a price that was available to back.  TOTE3 below is the
switch; set it False to drop race 3 from the priced sample entirely.

Book percentages on the starters as listed:
R1 1.192, R2 1.196, R3 1.180 (tote), R4 1.199, R5 1.220, R6 1.216,
R7 1.205, R8 1.212.  R5 sits high because LONGREACH DROVER was a late
scratching ((L)SCR) and its deduction is not applied here; pred3 renormalises
on the actual starters, so this does not propagate.

P = {race_no: [(name, barrier, decimal_win_price), ...]}

PAPER TRADING ONLY.
"""

TOTE3 = True

P = {
    1: [
        ("Commit", 8, 5.00),
        ("Judas Tree", 6, 2.90),
        ("American Eagle", 3, 3.30),
        ("Civic Square", 2, 9.50),
        ("Corretto", 4, 23.00),
        ("Perfectly Fine", 7, 31.00),
        ("Crown Of Fire", 1, 7.50),
        ("Anastasia's Flame", 5, 34.00),
    ],
    2: [
        ("De Ascot", 1, 8.00),
        ("Everymomentcounts", 6, 71.00),
        ("Gold Chariot", 8, 2.20),
        ("The Quiet Immortal", 4, 4.20),
        ("Chateau Dancer", 5, 6.50),
        ("Next Tuesday", 2, 5.00),
        ("Tornado Anwa", 3, 251.00),
        ("Zareenee", 7, 151.00),
    ],
    3: [
        # TOTE dividends -- see TOTE3 above.
        ("Silent Shares", 6, 3.10),
        ("Delicate Lady", 7, 7.70),
        ("Brutalina", 4, 9.90),
        ("Sea Poem", 2, 3.90),
        ("Meh Keffi", 3, 18.20),
        ("Tempranillo", 9, 8.20),
        ("Second Time", 5, 8.40),
        ("Dobkins", 1, 14.70),
        ("Everett", 8, 154.80),
    ],
    4: [
        ("Ravenclaw", 6, 13.00),
        ("Dreamzel", 7, 3.80),
        ("Misty Legend", 5, 15.00),
        ("Weapon Clear", 3, 3.80),
        ("Faraway Dream", 4, 3.50),
        ("Bella Cinque", 2, 12.00),
        ("Walter Spur", 8, 12.00),
        ("Legacy Bel", 1, 13.00),
    ],
    5: [
        ("Saluted", 2, 9.00),
        ("Nordic Strike", 6, 6.00),
        ("Blue Humma", 3, 5.00),
        ("Logam", 8, 17.00),
        ("Satin Diva", 12, 5.00),
        ("Bold Suitor", 10, 16.00),
        ("Obucci", 5, 21.00),
        ("Our Wynd Chymes", 1, 8.00),
        ("Bliss Bomb", 11, 10.00),
        ("Tan Tat Art", 7, 14.00),
        ("Final Moment", 9, 13.00),
    ],
    6: [
        ("Princeofnottingham", 2, 14.00),
        ("Natural Ruler", 4, 9.50),
        ("Saveadateforme", 6, 51.00),
        ("Dubai Watch", 12, 10.00),
        ("Almairac", 9, 10.00),
        ("Giggenbach", 11, 19.00),
        ("Holmes", 1, 31.00),
        ("Icaro", 5, 23.00),
        ("Komito", 3, 4.20),
        ("Big Sister Ava", 8, 10.00),
        ("Blue Willow", 10, 3.40),
        ("Imponderable", 7, 17.00),
    ],
    7: [
        ("Nearco Frod", 9, 2.90),
        ("Bluestone", 1, 7.00),
        ("Sing For Peace", 8, 31.00),
        ("Jaykayann", 6, 21.00),
        ("Customer Service", 2, 12.00),
        ("Empress Of The Sun", 3, 2.50),
        ("Shultzy", 10, 7.50),
        ("Miss Niagara", 5, 81.00),
        ("Zedwilldo", 7, 151.00),
        ("Flying Witness", 4, 251.00),
    ],
    8: [
        ("He'll Rip", 4, 7.00),
        ("Madero", 2, 81.00),
        ("Reset The Jazz", 1, 41.00),
        ("Angry Skies", 3, 81.00),
        ("Currawood", 9, 23.00),
        ("Outta Compton", 13, 81.00),
        ("Touchdown", 12, 3.80),
        ("Supernima", 5, 8.50),
        ("Fridge Monster", 10, 71.00),
        ("Keane Enuff", 14, 10.00),
        ("Shiny New Deel", 6, 18.00),
        ("Fear No Evil", 11, 21.00),
        ("Kahhof", 8, 5.00),
        ("Botanical Boy", 7, 6.00),
    ],
}

if not TOTE3:
    del P[3]

# Scratchings, kept for audit against the store's field sizes.
SCR = {
    1: [("Invicto", 8), ("Avengers", 3), ("Whimsy Smile", 12),
        ("Mareenya", 1), ("Exploit", 10)],
    2: [("A Long Story Short", 5), ("Bellabama", 2), ("Luminaza", 8)],
    3: [],
    4: [("Foxenberg", 1), ("Bring Me Power", 7), ("Soju", 10)],
    5: [("Longreach Drover", 4)],          # late scratching, (L)SCR
    6: [("Nishino Crescent", 2), ("Haaland", 1), ("Red On Red", 15)],
    7: [("Lightening Mann", 5), ("All So Clear", 2), ("Urban Outlook", 13),
        ("Omamori", 7)],
    8: [("Flying Valley", 18), ("Mr Verse", 13), ("Sought After", 5),
        ("Impending Link", 4), ("Glasgow Lass", 20), ("Stay Silent", 1)],
}

# Spelling artifacts between the sectional feed and the betting screen.
# Key = normalised screen name, value = normalised store key.
ALIAS = {}
