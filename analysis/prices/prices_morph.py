"""Morphettville Parks, Saturday 1 August 2026 -- fixed-odds WIN prices.

Transcribed from the full-field fixed-odds tables (columns No / Runner
(Barrier) / FIXED ODDS Win, Place / TOTE Win, Place).  WIN column only.
Scratchings are excluded entirely -- they are listed in SCR below only so the
transcription can be audited against the screenshots.

"Last Updated" stamps on the screens: R1 12:32:34, R2 13:05:48, R4 14:15:04,
R5 14:55:21, R6 15:29:09, R7 16:05:35, R8 16:40:33 -- i.e. close to each race's
jump, so comparable in snapshot timing to the 4 July Flemington set.

P = {race_no: [(name, barrier, decimal_win_price), ...]}

PAPER TRADING ONLY.
"""

P = {
    1: [
        ("Elrond", 9, 41.00),
        ("Street Legal", 3, 2.70),
        ("Torpedoes", 5, 13.00),
        ("Vasilias", 8, 151.00),
        ("Amalfi Dreamer", 6, 3.10),
        ("Bold Starlet", 10, 51.00),
        ("Clux Star", 1, 26.00),
        ("Grand Millesime", 7, 9.00),
        ("My Cherie Amor", 2, 81.00),
        ("She's Iconic", 4, 4.60),
    ],
    2: [
        ("Up The Den", 3, 7.00),
        ("Intellectual", 7, 2.10),
        ("Stand Alone", 6, 4.20),
        ("So Polite", 9, 11.00),
        ("Madam Jeanette", 2, 15.00),
        ("Sassy Little Miss", 8, 19.00),
        ("Scooped", 4, 21.00),
        ("Zoutrail", 1, 14.00),
        ("Oriedos", 10, 201.00),
        ("Valabing", 5, 201.00),
    ],
    3: [
        ("Longer Route", 6, 3.20),
        ("Exalted Fire", 5, 8.50),
        ("Theodor", 8, 34.00),
        ("Moussaka", 11, 13.00),
        ("Petit Eagle", 9, 6.50),
        ("Eight On The Dot", 2, 12.00),
        ("Holmes", 10, 12.00),
        ("Moana's Fortune", 4, 26.00),
        ("Oh Lovey No", 12, 61.00),
        ("High Society Girl", 3, 6.50),
        ("Rikki Rikkardo", 7, 9.00),
        ("Back Me Up Benny", 1, 34.00),
    ],
    4: [
        ("Breakfast", 10, 13.00),
        ("Hot Strut", 12, 12.00),
        ("Indian Jewel", 9, 31.00),
        ("Porsha Crystal", 8, 4.20),
        ("Tahnee Territory", 4, 9.00),
        ("Brimarvi Rosemarie", 1, 5.50),
        ("Mrs Penny Cracker", 3, 17.00),
        ("Chillcuz", 6, 6.00),
        ("Hell's On Fire", 5, 19.00),
        ("Hysterical Lady", 11, 15.00),
        ("Trantoro", 7, 16.00),
        ("Tully Hart", 2, 12.00),
    ],
    5: [
        ("Nicish", 3, 10.00),
        ("Big Sue", 4, 15.00),
        ("Flaming Navy", 8, 14.00),
        ("Phineas", 2, 7.00),
        ("Everything Counts", 10, 23.00),
        ("Fast Tempo", 7, 3.00),
        ("Maxildo", 1, 4.80),
        ("Capulet", 6, 41.00),
        ("Tyusix", 5, 7.00),
        ("Callistemon", 9, 14.00),
    ],
    6: [
        ("Demojo", 3, 10.00),
        ("Nextonixs", 4, 4.20),
        ("Real Deluxe", 10, 5.00),
        ("Zanthron", 1, 6.50),
        ("Bristler", 5, 19.00),
        ("Halliwell", 2, 8.00),
        ("Vintage Star", 7, 16.00),
        ("Daisydoo", 6, 4.80),
        ("Sioux Warrior", 9, 41.00),
        ("Grand Host", 8, 23.00),
    ],
    7: [
        ("Sav On Ice", 6, 34.00),
        ("Snow Patrol", 5, 51.00),
        ("Snoopy Now", 9, 4.40),
        ("Angry Skies", 4, 18.00),
        ("The Stalker", 1, 5.00),
        ("Guru Warrior", 7, 9.50),
        ("Sought After", 3, 5.00),
        ("Tosen Water", 8, 11.00),
        ("Cielao", 2, 6.00),
        ("Miso", 10, 9.00),
    ],
    8: [
        ("Mellifluent", 8, 10.00),
        ("Bold Secret", 6, 2.60),
        ("Power Dancer", 7, 14.00),
        ("Annihilate", 2, 19.00),
        ("Attain", 11, 23.00),
        ("Orthie's Boys", 5, 7.00),
        ("Kikorangi", 10, 26.00),
        ("Australia Forever", 3, 7.50),
        ("Extra Hot", 9, 11.00),
        ("Impact Storm", 1, 23.00),
        ("New York Scandal", 4, 9.00),
        ("Flight Deck", 12, 251.00),
    ],
    9: [
        ("Superset", 1, 9.50),
        ("Prevailed", 6, 4.60),
        ("Grande Terre", 7, 9.50),
        ("Tapinforpar", 10, 13.00),
        ("The Cosmic One", 2, 11.00),
        ("Naralinga", 9, 5.50),
        ("Steel Tsunami", 3, 18.00),
        ("Thermodynamic", 4, 11.00),
        ("Top Of The Ridge", 5, 6.50),
        ("Polunin", 8, 8.00),
    ],
}

# Spelling artifacts: the sectional PDF and the betting screen disagree on a
# name.  Key = normalised screen name, value = normalised store key.  R1's
# "She's Iconic" is rendered "Shes Iconnic" (double N) in the tripleSdata PDF.
ALIAS = {
    "SHES ICONIC": "SHES ICONNIC",
}

# Scratchings seen on the screens, excluded from P above (audit trail only).
SCR = {
    3: [("Like A Tiger", 10), ("Lafont", 9)],
    5: [("Extinguish", 11)],
    6: [("Pure Bliss", 11)],
    7: [("Carbonados", 9)],
    9: [("Cork Harbour", 14), ("Dampen", 12), ("Outpost", 11)],
}
