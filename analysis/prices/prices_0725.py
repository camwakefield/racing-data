"""Caulfield, Saturday 25 July 2026 -- fixed-odds WIN prices.

Transcribed from the full-field fixed-odds tables (No / Runner (Barrier) /
FIXED ODDS Win, Place / TOTE Win, Place).  WIN column only.  Scratchings
excluded from P, recorded in SCR for audit.

Race numbers are inferred from the "Last Updated" stamps, which run strictly
in order across the ten screenshots:
R1 12:12:54, R2 12:56:24, R3 13:22:45, R4 13:57:57, R5 14:33:06,
R6 15:13:47, R7 15:52:59, R8 16:28:58, R9 ~16:5x (stamp clipped).
R8 spans two images (runners 1-14, then 3-15); the overlap agrees exactly.

P = {race_no: [(name, barrier, decimal_win_price), ...]}

PAPER TRADING ONLY.
"""

P = {
    1: [
        ("Takeko", 4, 5.50),
        ("Glasgow Lass", 8, 26.00),
        ("Custom", 7, 2.30),
        ("Divine Thoughts", 6, 23.00),
        ("Recuperato", 2, 7.00),
        ("Royal Lass", 3, 41.00),
        ("Mystery 'N' Drama", 10, 13.00),
        ("Sun Setting", 5, 8.00),
        ("Vain Champagne", 9, 15.00),
        ("Happy Link", 1, 17.00),
    ],
    2: [
        ("Ghana's Akan", 11, 3.90),
        ("Milsons Point", 10, 14.00),
        ("Torture", 4, 14.00),
        ("Brazen Dechambeau", 7, 11.00),
        ("Stakes", 8, 5.00),
        ("Resolutely", 5, 3.40),
        ("Orchid Sky", 1, 101.00),
        ("Brazen Panda", 9, 13.00),
        ("Doubt Time", 6, 9.00),
    ],
    3: [
        ("Salsa Fellow", 3, 17.00),
        ("Tennessee Bound", 1, 1.50),
        ("Apache Song", 2, 71.00),
        ("Luna Cat", 6, 5.50),
        ("Butternut Princess", 5, 13.00),
        ("Dancing Storm", 4, 12.00),
        ("Behaviour", 7, 11.00),
    ],
    4: [
        ("Snow Mercy", 11, 23.00),
        ("Prince Tycoon", 9, 5.00),
        ("Signature Scent", 6, 3.90),
        ("Afterberna", 4, 7.00),
        ("Express Class", 12, 7.50),
        ("Farcited", 2, 8.00),
        ("Jenni The Ninja", 13, 19.00),
        ("Nightime Star", 1, 34.00),
        ("The Benchmark", 7, 19.00),
        ("Final Moment", 3, 26.00),
        ("Talladega Girl", 8, 31.00),
        ("Beautiful Bevy", 5, 12.00),
        ("Pacific Glamour", 10, 201.00),
    ],
    5: [
        ("Jimmy The Bear", 3, 9.00),
        ("Detonator Jack", 7, 9.50),
        ("Magnaspin", 8, 11.00),
        ("Unlimited", 5, 17.00),
        ("Seafall", 1, 8.00),
        ("Tuff Tu Mus", 4, 16.00),
        ("St Lawrence", 9, 4.80),
        ("Rumbled Again", 2, 61.00),
        ("First Chorus", 6, 2.45),
    ],
    6: [
        ("Decalogue", 3, 4.00),
        ("Dirnaseer", 6, 10.00),
        ("Brillantezza", 10, 4.60),
        ("Engine Of War", 1, 19.00),
        ("Our Chief", 7, 7.50),
        ("Harbour Town", 8, 11.00),
        ("Kings Reflection", 2, 3.80),
        ("Menthon", 9, 101.00),
        ("Pressurised", 5, 101.00),
        ("Ferrario", 4, 17.00),
    ],
    7: [
        ("Cosmic Crusader", 1, 3.70),
        ("Recommendation", 9, 7.00),
        ("Zou Sensation", 8, 6.50),
        ("Aztec Ruler", 3, 31.00),
        ("Title Fighter", 7, 71.00),
        ("Watchme Win", 6, 7.50),
        ("Winnasedge", 5, 4.00),
        ("Miraval Rose", 2, 6.50),
        ("Samangu", 4, 31.00),
    ],
    8: [
        ("Diwali", 1, 151.00),
        ("Makdane", 12, 4.20),
        ("Prince Eric", 3, 10.00),
        ("Station One", 8, 151.00),
        ("Aftermath", 11, 126.00),
        ("Stop The Rock", 4, 6.00),
        ("Savour The Dream", 9, 16.00),
        ("Test The Law", 13, 126.00),
        ("Crimson Vine", 6, 41.00),
        ("Beach Pad", 7, 13.00),
        ("Amleto", 14, 5.00),
        ("Belle Savoir", 10, 13.00),
        ("Leonchroi", 5, 71.00),
        ("Aeolian", 2, 4.60),
    ],
    9: [
        ("Just Too Fly", 7, 151.00),
        ("Cruiserweight", 6, 1.85),
        ("Jenni Gone Bonkers", 4, 13.00),
        ("Celtics", 2, 9.50),
        ("Mahershala", 1, 4.60),
        ("Lauberhorn", 9, 34.00),
        ("Blankfield", 10, 17.00),
        ("Ludlum", 3, 19.00),
        ("Falset Star", 11, 23.00),
        ("Hotei Senshi", 8, 16.00),
        ("Shares", 5, 101.00),
    ],
}

# Scratchings seen on the screens, excluded from P above (audit trail only).
# (L)SCR and SCR are both recorded here -- the distinction is a late/early
# scratching and does not matter for the book, since neither started.
SCR = {
    2: [("Rebel Tuesday", 2), ("Jacaranda", 12), ("No Confetti", 3)],
    3: [("Vestas", 6)],
    4: [("Logam", 13)],
    6: [("Don't Doubt Dare", 3)],
    8: [("Oraqua", 11)],
    9: [("Itazura", 12), ("Barking Mad", 9), ("Centu Cavaddi", 13),
        ("Magnetic Chess", 10)],
}

# Spelling artifacts between the sectional feed and the betting screen.
# Key = normalised screen name, value = normalised store key.
ALIAS = {}
