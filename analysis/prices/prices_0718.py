"""Flemington, Saturday 18 July 2026 -- fixed-odds WIN prices.

Transcribed from the full-field fixed-odds tables (No / Runner (Barrier) /
FIXED ODDS Win, Place / TOTE Win, Place).  WIN column only.  Scratchings
excluded from P, recorded in SCR for audit.

"Last Updated" stamps, one per race and all close to the jump:
R1 12:08:14, R2 12:42:37, R3 13:18:19, R4 13:54:20, R5 14:28:48,
R6 15:10:41, R7 15:47:54, R8 16:24:02, R9 16:57:34.

P = {race_no: [(name, barrier, decimal_win_price), ...]}

PAPER TRADING ONLY.
"""

P = {
    1: [
        ("Ko Phangan", 1, 2.10),
        ("Notified", 5, 3.00),
        ("Achy Breaky Heart", 3, 8.00),
        ("Delahra", 2, 4.80),
        ("Stunning Kitty", 4, 71.00),
    ],
    2: [
        ("Hard Kick", 6, 2.00),
        ("Leopard Shark", 3, 26.00),
        ("The Troubleshooter", 1, 41.00),
        ("Almontego", 4, 101.00),
        ("Dark Matter", 7, 10.00),
        ("Riverina Lulu", 2, 8.00),
        ("Veneto Street", 5, 61.00),
        ("Panchenko", 8, 2.70),
    ],
    3: [
        ("Sweet Jasmine", 10, 14.00),
        ("Barbie'sdreamworld", 9, 12.00),
        ("Changing Colours", 3, 4.40),
        ("Madiyya", 8, 4.60),
        ("Storm Season", 7, 19.00),
        ("Lake Vostok", 1, 6.00),
        ("Impending Shadow", 11, 41.00),
        ("Cat Noir", 6, 6.50),
        ("Marine Empress", 4, 11.00),
        ("Street Lark", 5, 14.00),
        ("Ataegina", 2, 34.00),
    ],
    4: [
        ("Palm Angel", 12, 18.00),
        ("Cherish Me", 7, 10.00),
        ("Davida", 2, 5.50),
        ("Miss Maranda", 14, 26.00),
        ("Angel In Black", 4, 41.00),
        ("Duntulm Lass", 6, 101.00),
        ("Licentious", 1, 23.00),
        ("Missapprehend", 10, 4.20),
        ("Off Their Perch", 8, 8.50),
        ("Pravaha", 13, 21.00),
        ("Salizou", 11, 23.00),
        ("Sky Watcher", 5, 51.00),
        ("Zuppa Inglese", 3, 21.00),
        ("Laura Eliza", 9, 4.00),
    ],
    5: [
        ("Prestige Forever", 13, 12.00),
        ("Kaleo", 11, 12.00),
        ("Flying Done", 15, 8.00),
        ("Siriusly Hot", 5, 18.00),
        ("Chowdown", 10, 13.00),
        ("Emperor Tzu", 2, 34.00),
        ("Flying Khan", 1, 5.50),
        ("Lucky Lucky Boom", 3, 10.00),
        ("Mr Avery", 6, 7.00),
        ("Overpriced", 7, 61.00),
        ("Oyster Lane", 8, 23.00),
        ("Zebra Finch", 9, 7.50),
        ("The Mean Fiddler", 14, 8.00),
        ("Don't Doubt Dare", 4, 151.00),
        ("Watt On Earth", 12, 81.00),
    ],
    6: [
        ("Bold Soul", 4, 5.00),
        ("Tempesti", 7, 16.00),
        ("Black Run", 5, 7.00),
        ("Tajanis", 2, 11.00),
        ("Virtuous Circle", 8, 14.00),
        ("Highland Blaze", 9, 2.60),
        ("Parvati Party", 6, 9.00),
        ("Stern Idol", 3, 17.00),
        ("Samuel Langhorne", 10, 16.00),
        ("Urban Outlook", 1, 71.00),
    ],
    7: [
        ("Great Maximus", 1, 11.00),
        ("Home Rule", 10, 21.00),
        ("Royal Insignia", 13, 8.00),
        ("Moby Dick", 4, 7.50),
        ("Steel Move", 2, 18.00),
        ("Betwitchery", 11, 11.00),
        ("Bullets High", 3, 151.00),
        ("Flyer", 6, 15.00),
        ("Mr Verse", 12, 15.00),
        ("Sixteen Reasons", 9, 126.00),
        ("Barari", 5, 3.00),
        ("Piastri", 14, 11.00),
        ("Jugiong", 7, 16.00),
        ("Zethus", 8, 51.00),
    ],
    8: [
        ("Bankers Choice", 11, 11.00),
        ("Saint George", 9, 4.00),
        ("Smokin' Romans", 13, 17.00),
        ("Brayden Star", 1, 23.00),
        ("Freedom Rally", 12, 19.00),
        ("Glory Daze", 3, 10.00),
        ("Nellie Leylax", 4, 7.00),
        ("Star Of India", 6, 17.00),
        ("Thedoctoroflove", 2, 21.00),
        ("Smokin' Princess", 7, 23.00),
        ("Chief Little Rock", 10, 101.00),
        ("Think Giant", 8, 4.50),
        ("Flash Feeling", 5, 13.00),
    ],
    9: [
        ("Along The River", 8, 34.00),
        ("Nimbustwothousand", 12, 9.00),
        ("Harry Got Styles", 6, 41.00),
        ("Prima Bella", 4, 6.50),
        ("Charmed Run", 2, 23.00),
        ("Per Sempre", 3, 31.00),
        ("Landmark", 9, 12.00),
        ("One Hard Lady", 1, 15.00),
        ("Street Artist", 10, 2.90),
        ("El Pibe De Oro", 7, 18.00),
        ("Next Step Iowa", 11, 3.90),
        ("Bring Me Power", 5, 71.00),
    ],
}

SCR = {
    2: [("Pocketfullofcash", 9)],
    3: [("I Am Velvet", 5)],
    5: [("Censori", 1), ("Jimmy Beans", 9)],
    7: [("Wolfy", 1)],
    9: [("Martial Music", 7), ("Shining Smile", 10)],
}

# Spelling artifacts between the sectional feed and the betting screen.
# Key = normalised screen name, value = normalised store key.
ALIAS = {}
