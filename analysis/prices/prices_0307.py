"""Flemington, Saturday 7 March 2026 (Super Saturday) -- fixed-odds WIN prices.

Transcribed from ten full-field fixed-odds screens (No / Runner (Barrier) /
FIXED ODDS Win, Place / TOTE Win, Place).  WIN column only.  Scratchings
excluded from P, recorded in SCR for audit.

RACE NUMBERING IS ANCHORED BY FIELD COMPOSITION, which is stronger here than
either the "Last Updated" stamps or a Running Double line.  Every screen's set
of runners matches exactly one race in the store's 7 March Flemington results,
with no ambiguity: R1 Legacy Bound, R2 She's An Artist, R3 Medicinal,
R4 Scheelite, R5 Sass Appeal, R6 Grinzinger Heart, R7 Tom Kitten, R8 Ahha Ahha,
R9 Caballus, R10 Arcora.  The stamps agree with that ordering and run at a
~35-minute cadence:

    R1 12:18:04, R2 12:47:59, R3 13:23:06, R4 13:57:41, R5 14:34:07,
    R6 15:10:11, R7 15:43:43, R8 16:20:53, R9 (no stamp), R10 17:38:02

R9's screen is cropped above the header and carries no stamp.  It is placed at
race 9 by field composition (its fourteen starters are exactly the store's
fourteen for race 9) and independently by ordering -- it sits between the
16:20:53 and 17:38:02 screens.

THREE SCREENS ARE CUT OFF at the bottom: R1 after runner 8, R5 after runner 9,
R9 after runner 15.  In each case the PRICED set is nevertheless provably
complete, on two independent grounds:

  * Store agreement.  Priced starters per race are 7, 8, 8, 9, 8, 10, 9, 11,
    14, 9 = 93, which equals the store's 93 final_rank rows for this meeting
    exactly, race by race.
  * Barrier contiguity.  On R1 the seven starters carry barriers 1..7 with no
    gaps; on R9 the fourteen starters carry 1..14 with no gaps.  A runner
    hidden below the crop would have to hold a barrier already taken.

R1's header declares 6 scratchings and R5's declares 4, but only one SCR row is
visible on each -- the rest sit below the crop.  SCR is therefore INCOMPLETE for
R1 and R5, and FIELD (the numbered field size) is unknown for R1, R5 and R9.
Neither affects P: no scratching carries a price.

BARRIERS are as printed.  They are NOT uniformly reassigned post-scratching at
this meeting -- e.g. R2 starters run 1,2,3,4,5,6,8,9 (7 held by the scratched
Castellar), and R10 starters run 1..8 and 10 (9 held by the scratched Saganti).
A scratching's barrier can also duplicate a starter's (R2 Fission (1) against
Codigo (1); R7 Buckaroo (6) against Tom Kitten (6); R10 Tarvue (6) against
Litzdeel (6)).  SCR's second field is a BARRIER here, not a saddlecloth number.

P   = {race_no: [(name, barrier, decimal_win_price), ...]} in saddlecloth order.
SCR = {race_no: [(name, barrier_as_printed), ...]} in saddlecloth order.

Total priced starters: 93, matching the store exactly.

PAPER TRADING ONLY.
"""

P = {
    1: [
        ("Legacy Bound", 7, 2.40),
        ("Shining Smile", 5, 10.00),
        ("Burma Star", 3, 7.50),
        ("Military Tycoon", 1, 4.40),
        ("Go Left", 4, 51.00),
        ("Vangogh Bankcheque", 6, 3.50),
        ("Petit Artiste", 2, 81.00),
    ],
    2: [
        ("Press Down", 3, 61.00),
        ("Nervous Witness", 5, 26.00),
        ("She's An Artist", 8, 1.70),
        ("Wiggum", 9, 31.00),
        ("Codigo", 1, 11.00),
        ("Hezdarnhottoo", 4, 6.00),
        ("Verdoux", 6, 4.40),
        ("Nation State", 2, 61.00),
    ],
    3: [
        ("Rebel Tuesday", 7, 7.50),
        ("Medicinal", 8, 1.85),
        ("Simply Steffi", 1, 9.50),
        ("Scintillation", 3, 15.00),
        ("Better Off Alone", 4, 12.00),
        ("Chapados", 6, 61.00),
        ("Jadzia", 5, 9.50),
        ("Sanctuary", 2, 8.00),
    ],
    4: [
        ("Here To Shock", 4, 8.00),
        ("Cafe Millenium", 8, 3.70),
        ("Persian Spirit", 7, 3.60),
        ("On Display", 6, 4.60),
        ("Precious Charm", 2, 26.00),
        ("Pounding", 9, 61.00),
        ("Welcometotheshow", 1, 9.50),
        ("Wonder Boy", 5, 16.00),
        ("Scheelite", 3, 14.00),
    ],
    5: [
        ("Salty Pearl", 6, 2.60),
        ("Sass Appeal", 8, 2.40),
        ("After Summer", 1, 15.00),
        ("Pillow Fight", 3, 13.00),
        ("Exit", 2, 19.00),
        ("Lathlain", 4, 6.50),
        ("Seychelles", 7, 51.00),
        ("Naraghi", 5, 101.00),
    ],
    6: [
        ("Zambales", 2, 1.65),
        ("Eurocanto", 6, 15.00),
        ("Diameter", 9, 17.00),
        ("Hydrobomb", 5, 11.00),
        ("Dr Hook", 1, 11.00),
        ("Inner Gold", 7, 21.00),
        ("Leopard Shark", 10, 12.00),
        ("Expensive Taste", 3, 34.00),
        ("Grinzinger Heart", 4, 41.00),
        ("Refuse To Curtsy", 8, 11.00),
    ],
    7: [
        ("Tom Kitten", 6, 3.90),
        ("Antino", 1, 16.00),
        ("Evaporate", 7, 12.00),
        ("Steparty", 9, 23.00),
        ("Watch Me Rock", 5, 34.00),
        ("Sabaj", 3, 23.00),
        ("Pride Of Jenni", 2, 2.30),
        ("Stefi Magnetica", 4, 7.00),
        ("Leica Lucy", 8, 14.00),
    ],
    8: [
        ("Benagil", 1, 7.50),
        ("Machine Gun Gracie", 7, 23.00),
        ("Philia", 4, 15.00),
        ("Jennilala", 8, 23.00),
        ("Damask Rose", 11, 6.00),
        ("Too Darn Discreet", 3, 9.50),
        ("Sea What I See", 2, 2.90),
        ("Until Valhalla", 9, 41.00),
        ("Miss Tarzy", 10, 41.00),
        ("Ahha Ahha", 5, 6.50),
        ("Butternut Princess", 6, 11.00),
    ],
    9: [
        ("Tentyris", 11, 2.15),
        ("War Machine", 10, 13.00),
        ("Angel Capital", 2, 12.00),
        ("Sepals", 3, 21.00),
        ("Caballus", 1, 21.00),
        ("Benedetta", 12, 13.00),
        ("De Bergerac", 13, 101.00),
        ("Disneck", 7, 101.00),
        ("Gallant Son", 9, 71.00),
        ("Geegees Mistruth", 4, 34.00),
        ("Sghirripa", 8, 151.00),
        ("My Gladiola", 6, 4.80),
        ("Wodeton", 14, 16.00),
        ("Pallaton", 5, 34.00),
    ],
    10: [
        ("Augustus", 3, 3.20),
        ("Whisky On The Hill", 2, 5.50),
        ("Magnaspin", 1, 9.50),
        ("Immediacy", 8, 4.80),
        ("Desert Hero", 4, 15.00),
        ("Point King", 7, 12.00),
        ("Litzdeel", 6, 12.00),
        ("Jenni's Meadow", 5, 13.00),
        ("Arcora", 10, 13.00),
    ],
}

# Second field = BARRIER as printed (see docstring).  INCOMPLETE for races 1
# and 5, whose headers declare 6 and 4 scratchings respectively but whose
# screens are cut off after the first one.  "(L)" marks a late scratching.
SCR = {
    1: [("Pure Passion", 3)],                       # 5 more below the crop
    2: [("Fission", 1), ("Castellar", 7)],          # Castellar (L)
    3: [("Diamond Dawn", 8), ("Money Honey", 5)],
    4: [],
    5: [("Mystery 'N' Drama", 2)],                  # 3 more below the crop
    6: [("Almost An Angel", 11), ("Regal Ambition", 8)],
    7: [("Buckaroo", 6), ("Treasurethe Moment", 9)],
    8: [("Miss Aria", 8)],
    9: [("Baraqiel", 3)],
    10: [("Saganti", 9), ("Tarvue", 6)],            # Saganti (L)
}

# Numbered field size per race, from the saddlecloth numbering on the screens.
# None where the screen is cut off and the true field size cannot be read.
FIELD = {1: None, 2: 10, 3: 10, 4: 9, 5: None, 6: 12, 7: 11, 8: 12,
         9: None, 10: 11}

# Substitutes (emergencies promoted into the field), noted on the screens:
# R1 1. LEGACY BOUND, R2 3. SHE'S AN ARTIST, R3 2. MEDICINAL,
# R4 3. PERSIAN SPIRIT, R5 2. SASS APPEAL, R6 1. ZAMBALES,
# R8 8. SEA WHAT I SEE.  All are priced above.  R7, R9 and R10 show none
# (R9's header is above the crop).

# Spelling artifacts between the sectional feed and the betting screen.
# Key = normalised screen name, value = normalised store key.
ALIAS = {}
