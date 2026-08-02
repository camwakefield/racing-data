"""Caulfield, Saturday 11 July 2026 -- fixed-odds WIN prices.

Transcribed from the full-field fixed-odds tables (No / Runner (Barrier) /
FIXED ODDS Win, Place / TOTE Win, Place).  WIN column only.  Scratchings
excluded from P, recorded in SCR for audit.

"Last Updated" stamps, used to recover the race numbers (they run strictly in
order across the eleven screenshots):
R1 12:07:43, R2 (none visible), R3 13:14:20, R4 13:47:50, R5 14:22:43,
R6 15:03:02, R7 15:44:09, R8 16:17:37, R9 16:52:31.
R1 and R9 each span two images.

TWO CAVEATS, stated rather than absorbed:
  * R2's screen carries NO "Last Updated" stamp and is cut off at runner 15,
    so its completeness is UNCONFIRMED.  Its race number is inferred purely
    from its position between R1 (12:07:43) and R3 (13:14:20).
  * R5's screen is a different render with NO barrier column and no TOTE
    columns, so barriers are None and the barrier cross-check is unavailable
    for that race.

P = {race_no: [(name, barrier_or_None, decimal_win_price), ...]}

PAPER TRADING ONLY.
"""

P = {
    1: [
        ("Angels Fury", 9, 1.70),
        ("Egyptian Dancer", 5, 12.00),
        ("Artrema", 1, 23.00),
        ("Eilish", 7, 10.00),
        ("Ms Port Melbourne", 4, 23.00),
        ("Ole Affair", 3, 34.00),
        ("Orchid Sky", 2, 41.00),
        ("Play It Now", 10, 26.00),
        ("Ruby Guild", 8, 101.00),
        ("Portinari", 6, 4.00),
    ],
    2: [
        ("Zouper Fund", 1, 4.20),
        ("Naval Academy", 10, 11.00),
        ("Markdel", 12, 5.50),
        ("Luna Cat", 3, 4.40),
        ("Stealth Of Night", 11, 6.50),
        ("Jennyanydots", 4, 34.00),
        ("Dancing Storm", 8, 15.00),
        ("Demojo", 6, 13.00),
        ("Behaviour", 2, 23.00),
        ("Dollar Shot", 7, 17.00),
        ("Zethus", 9, 151.00),
        ("Electric Star", 5, 34.00),
    ],
    3: [
        ("Like A Drifter", 7, 3.90),
        ("Davida", 11, 11.00),
        ("Celtics", 4, 8.00),
        ("Cruiserweight", 8, 2.90),
        ("Jenni Gone Bonkers", 9, 8.00),
        ("Lil Orlov", 1, 51.00),
        ("Loveyamore", 2, 34.00),
        ("Shares", 10, 61.00),
        ("Undisputable", 3, 9.50),
        ("Beechworth", 6, 14.00),
    ],
    4: [
        ("Cavalry Girl", 5, 6.50),
        ("Signature Scent", 2, 6.00),
        ("Jenni The Ninja", 8, 26.00),
        ("Wintery", 4, 10.00),
        ("Brilliant Horizon", 3, 5.50),
        ("Lady Verity", 7, 3.80),
        ("Restless Wind", 1, 14.00),
        ("Miss Lola", 6, 4.60),
    ],
    5: [
        # No barrier column on this render -- see caveat in the docstring.
        ("Sir Atlas", None, 6.50),
        ("Aftermath", None, 101.00),
        ("Howlin Rain", None, 23.00),
        ("Kingofwallstreet", None, 51.00),
        ("Stop The Rock", None, 9.50),
        ("Prince Eric", None, 8.00),
        ("Belle Savoir", None, 4.80),
        ("Flash Feeling", None, 34.00),
        ("Amleto", None, 2.50),
        ("Tazaral", None, 51.00),
        ("Stirrup Cup", None, 31.00),
        ("A Samurai Mind", None, 23.00),
    ],
    6: [
        ("Decalogue", 6, 2.30),
        ("Dirnaseer", 4, 9.50),
        ("Our Chief", 8, 5.50),
        ("Harbour Town", 2, 11.00),
        ("Hells Spirit", 3, 81.00),
        ("Orlova", 5, 26.00),
        ("Paddypie", 1, 7.50),
        ("Menthon", 7, 51.00),
        ("Ferrario", 9, 26.00),
        ("Ichnusa", 10, 6.00),
    ],
    7: [
        ("Recommendation", 11, 5.50),
        ("Bustling", 5, 10.00),
        ("Klabel", 1, 26.00),
        ("Beast Mode", 7, 21.00),
        ("Title Fighter", 2, 151.00),
        ("Watchme Win", 6, 5.00),
        ("Sir Now", 3, 11.00),
        ("Winnasedge", 9, 4.40),
        ("Bellatrix Star", 10, 11.00),
        ("Miraval Rose", 8, 11.00),
        ("Bazaball Rewarded", 4, 7.50),
    ],
    8: [
        ("Pinstriped", 10, 21.00),
        ("Rise At Dawn", 3, 11.00),
        ("Coeur Volante", 4, 4.00),
        ("Magnaspin", 8, 26.00),
        ("Dashing", 5, 201.00),
        ("Big Swinger", 9, 6.00),
        ("Tuff Tu Mus", 6, 126.00),
        ("St Lawrence", 11, 18.00),
        ("Roadcone", 7, 12.00),
        ("Ten Commandments", 1, 2.30),
        ("Angland", 2, 41.00),
    ],
    9: [
        ("Snoopy Now", 2, 12.00),
        ("Station One", 10, 71.00),
        ("Makdane", 11, 4.00),
        ("Test The Law", 4, 51.00),
        ("Wonder Kid", 7, 51.00),
        ("First Chorus", 3, 2.70),
        ("Beach Pad", 1, 15.00),
        ("Mometz", 5, 7.00),
        ("Fearless Freddy", 9, 13.00),
        ("Ruakaka Raider", 8, 34.00),
        ("Taka Speed", 6, 7.50),
    ],
}

# Scratchings seen on the screens, excluded from P above (audit trail only).
# (L)SCR and SCR are both recorded here -- the distinction is a late/early
# scratching and does not matter for the book, since neither started.
SCR = {
    1: [("Rubare", 14), ("Fontalicious", 15), ("Tag The Bride", 9),
        ("Andres Girl", 13), ("Contarini", 5), ("Vain Beauty", 16)],
    2: [("Along The River", 15), ("Apache Song", 3), ("Ravenclaw", 10)],
    3: [("Bold Secret", 12), ("Glam Award", 5), ("King Maywin", 11)],
    4: [("Our Wynd Chymes", 10), ("Satin Diva", 9)],
    5: [("Chief Little Rock", None)],
    8: [("Madero", 12)],
    9: [("Narbold", 11), ("Nation's Call", 5), ("Indispensable", 10),
        ("Yam", 9), ("Glenfinnan", 4)],
}

# Substitutes noted on the screens (emergency promoted into the field):
# R4 6. LADY VERITY, R6 1. DECALOGUE, R7 8. WINNASEDGE,
# R8 10. TEN COMMANDMENTS, R9 9. FIRST CHORUS.  All are priced above.

# Spelling artifacts between the sectional feed and the betting screen.
# Key = normalised screen name, value = normalised store key.
ALIAS = {}
