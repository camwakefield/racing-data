"""Caulfield, Saturday 27 June 2026 -- fixed-odds WIN prices.

Transcribed from the full-field fixed-odds tables.  WIN column only.
Scratchings excluded from P, recorded in SCR for audit.

"Last Updated" stamps, which run strictly in order and recover the race number:
R1 11:51:32, R2 (none visible), R3 13:06:27, R4 13:40:04, R5 14:17:49,
R6 15:01:30, R7 15:34:34, R8 16:09:18, R9 16:43:23.
R4, R6, R7, R8 and R9 each span two images; every overlap agrees exactly.

CAVEAT ON BARRIERS.  This meeting renders "Runner (Barrier)" with the barrier
in parentheses for only SOME runners -- typically the higher saddlecloth
numbers.  Where the screen shows no parenthesis the barrier is recorded as
None rather than guessed.  (The obvious guess, barrier = saddlecloth number,
is contradicted by R6 #16 LOGAM (16) and R8 #19 BOLTSAVER (19), where the
parenthesis is printed even though it equals the number -- so the rule is not
"shown only when different" and the blanks cannot be safely filled in.)

R2's screen carries no stamp and is cut off after runner 13, but its header
reads "Scratchings 13", so the field is 1-13 with #13 scratched and all 12
starters are visible.  Completeness is therefore CONFIRMED, unlike the
equivalent gap on 11 July.

P   = {race_no: [(name, barrier_or_None, decimal_win_price), ...]}
      listed in saddlecloth order.
SCR = {race_no: [(name, SADDLECLOTH NUMBER), ...]}
      NOTE: the second field here is the saddlecloth number, not the barrier,
      because that is what the "Scratchings" header gives on these screens.
FIELD = {race_no: number of runners in the numbered field}
      With SCR and saddlecloth order, this makes every runner's number
      reconstructible.

PAPER TRADING ONLY.
"""

P = {
    1: [
        ("Invicto", None, 16.00),
        ("Profumo", None, 9.50),
        ("Aston", None, 6.50),
        ("Angelic Rise", None, 10.00),
        ("Neotropical", None, 23.00),
        ("Face The Wild", None, 5.00),
        ("Lucky Brook", None, 4.00),
        ("Lumineer", None, 51.00),
        ("Ole Affair", None, 34.00),
        ("Mirador", None, 19.00),
        ("Portinari", None, 8.00),
        ("Egyptian Dancer", None, 15.00),
    ],
    2: [
        ("Hi Dubai", None, 34.00),
        ("Sixteen Reasons", None, 41.00),
        ("Dreamzel", None, 16.00),
        ("Takeko", None, 7.50),
        ("Biancelli", None, 6.00),
        ("Charmed Run", None, 34.00),
        ("Per Sempre", None, 18.00),
        ("Delicate Lady", None, 7.50),
        ("Luna Cat", None, 8.50),
        ("Vain Champagne", None, 15.00),
        ("Claymore Mine", None, 31.00),
        ("Next Step Iowa", None, 2.90),
    ],
    3: [
        ("Custom", None, 5.00),
        ("Afterberna", None, 4.60),
        ("Biologics", None, 13.00),
        ("Sky Watcher", None, 41.00),
        ("Race For Rule", None, 2.70),
        ("Our Justify", None, 13.00),
        ("Written Glow", None, 7.50),
        ("Gliding Lightening", None, 41.00),
        ("Rosangela", None, 18.00),
    ],
    4: [
        ("Miracle Spin", None, 19.00),
        ("Savour The Dream", None, 5.50),
        ("Prince Eric", None, 17.00),
        ("Skippers Canyon", None, 4.60),
        ("Flash Feeling", None, 41.00),
        ("Gregolimo", None, 26.00),
        ("Amleto", None, 4.80),
        ("Haaland", None, 151.00),
        ("Promised Land", None, 18.00),
        ("The Cunning Fox", 6, 81.00),
        ("Belle Savoir", 2, 21.00),
        ("Foire De Trone", 4, 6.00),
        ("Nothingelsematters", 11, 71.00),
        ("Ant", 15, 9.50),
    ],
    5: [
        ("Bankers Choice", None, 6.00),
        ("Smokin' Romans", None, 6.50),
        ("Freedom Rally", None, 21.00),
        ("Gilded Water", None, 4.60),
        ("Star Of India", None, 8.50),
        ("Nellie Leylax", None, 6.00),
        ("Thedoctoroflove", None, 9.00),
        ("Raging Bull", None, 13.00),
        ("Cadmus", None, 8.50),
    ],
    6: [
        ("Shining Smile", None, 31.00),
        ("Cannyworth", None, 21.00),
        ("Farcited", None, 11.00),
        ("Street Artist", None, 6.00),
        ("Saluted", None, 26.00),
        ("Ground Control", None, 19.00),
        ("Gunz", None, 13.00),
        ("I'm Foxing", None, 23.00),
        ("Wintery", None, 18.00),
        ("Fly By Light", None, 12.00),
        ("Satin Diva", 14, 11.00),
        ("Set Me Loose", 2, 3.20),
        ("Mad About Magnus", 6, 10.00),
        ("Palazzo Dama", 12, 201.00),
    ],
    7: [
        ("Black Storm", None, 23.00),
        ("Brave Miss", None, 16.00),
        ("Think Giant", None, 10.00),
        ("A Samurai Mind", None, 21.00),
        ("Nation's Call", None, 15.00),
        ("Indispensable", None, 23.00),
        ("First Chorus", None, 6.50),
        ("Somewhere", None, 26.00),
        ("Mometz", None, 10.00),
        ("Stop The Rock", 12, 81.00),
        ("Mr Blunt", 14, 7.50),
        ("Madiyya", 10, 3.30),
        ("The Devil In Her", 4, 12.00),
        ("Tikemyson", 9, 151.00),
        ("Vellasmachine", 7, 41.00),
    ],
    8: [
        ("Just Folk", None, 26.00),
        ("Coeur Volante", None, 6.50),
        ("Dashing", None, 151.00),
        ("Magnaspin", None, 41.00),
        ("El Rocko", None, 11.00),
        ("Big Swinger", None, 2.40),
        ("St Lawrence", None, 34.00),
        ("Tuff Tu Mus", None, 26.00),
        ("The Pendragon", None, 81.00),
        ("El Soleado", 4, 81.00),
        ("Elouyou", 15, 9.00),
        ("Windstorm", 8, 41.00),
        ("Roadcone", 3, 7.00),
        ("He'll Rip", 1, 9.50),
    ],
    9: [
        ("Great Maximus", None, 19.00),
        ("Winnasedge", None, 4.40),
        ("Bazaball Rewarded", None, 4.60),
        ("Carbonados", None, 11.00),
        ("Steel Move", None, 14.00),
        ("Ka Ying Cheer", None, 9.00),
        ("Along The River", None, 31.00),
        ("Naval Academy", None, 12.00),
        ("Nimbustwothousand", 12, 9.50),
        ("Piastri", 1, 15.00),
        ("Landmark", 8, 9.50),
        ("Zethus", 3, 81.00),
    ],
}

# Second field = SADDLECLOTH NUMBER (see docstring).
SCR = {
    1: [("Rubare", 4), ("Stakes", 5), ("Eilish", 8), ("Orchid Sky", 13)],
    2: [("Grassmere Diamond", 13)],
    3: [("Miss Lola", 9), ("Pinot For Mike", 10), ("Cresta Crystal", 12)],
    4: [("Perfect Play", 3), ("Sacrify", 8), ("My Roca Fella", 11),
        ("Durban Harbour", 17)],
    5: [("Smokin' Princess", 9), ("Test The Law", 10)],
    6: [("La Astro Chat", 2), ("Star Trip", 14), ("Logam", 16),
        ("Lost The Plot", 18)],
    7: [("Yam", 9), ("Beach Pad", 10), ("Oriental Smoke", 13),
        ("Geffina", 18)],
    8: [("Run Harry Run", 6), ("Fancify", 10), ("Grid Girl", 14),
        ("Make It Sweet", 18), ("Boltsaver", 19), ("Atomic Gold", 20)],
    9: [("Gin A Tonic", 1), ("Press Down", 3), ("Salsa Fellow", 8),
        ("Behaviour", 15)],
}

FIELD = {1: 16, 2: 13, 3: 12, 4: 18, 5: 11, 6: 18, 7: 19, 8: 20, 9: 16}

# Substitutes (emergencies promoted into the field), noted on the screens:
# R2 12. NEXT STEP IOWA, R5 4. GILDED WATER, R7 15. MADIYYA,
# R8 7. BIG SWINGER, R9 4. WINNASEDGE.  All are priced above.

# Spelling artifacts between the sectional feed and the betting screen.
# Key = normalised screen name, value = normalised store key.
ALIAS = {}
