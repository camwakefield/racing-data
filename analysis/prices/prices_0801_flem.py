"""Flemington, Saturday 1 August 2026 -- fixed-odds WIN prices.

Extracted from flem/rows.json, the working file the 1 August run was scored
from.  That file carried a whole store snapshot per row; only race, saddlecloth
number, name and price are durable, so this is the same data in the shape every
other price module uses.  Regenerated and checked against the original: the
priced-runner set and every price agree exactly.

The middle element is the SADDLECLOTH NUMBER here, not the barrier.  Nothing
downstream reads it -- pred3 and tempo2 both bind it to _barrier and discard
it -- but it is not a barrier and should not be treated as one.

P = {race_no: [(name, saddlecloth_no, decimal_win_price), ...]}

PAPER TRADING ONLY.
"""

P = {
    1: [
        ('Nearco Frod', 5, 3.40),
        ('Our Chief', 6, 3.00),
        ('Black Run', 2, 10.00),
        ('Tempesti', 1, 17.00),
        ('Stop The Rock', 4, 6.50),
        ('Go Daddy', 3, 13.00),
        ('Bluestone', 9, 7.00),
        ('Samuel Langhorne', 7, 21.00),
        ('Urban Outlook', 10, 26.00),
    ],
    2: [
        ('Rubare', 3, 4.40),
        ('The Troubleshooter', 5, 11.00),
        ('Hearts Affair', 8, 8.50),
        ('Santa Barbara', 11, 12.00),
        ('Covert Action', 4, 6.00),
        ('Superbec', 10, 7.00),
        ('Relinquishing', 9, 14.00),
        ('Almontego', 7, 14.00),
        ('Eurocanto', 1, 7.50),
        ('Rebel Tuesday', 2, 7.00),
    ],
    3: [
        ("Smokin' Romans", 1, 4.20),
        ('Glory Daze', 2, 5.50),
        ('See That Storm', 5, 4.80),
        ('Star Of India', 4, 5.00),
        ('Brayden Star', 3, 9.00),
        ('Chief Little Rock', 8, 23.00),
        ("Smokin' Princess", 6, 7.50),
        ('Farag', 7, 34.00),
        ('Flash Feeling', 9, 12.00),
    ],
    4: [
        ('Kahhof', 1, 4.40),
        ('El Tercero', 18, 6.50),
        ('Fear No Evil', 11, 7.50),
        ('Darkbonee', 4, 4.80),
        ('Surreal I Am', 10, 14.00),
        ('Dramaticus', 12, 12.00),
        ('Raf Attack', 6, 71.00),
        ('Reset The Jazz', 2, 34.00),
        ('Impending Link', 8, 31.00),
        ('Keane Enuff', 9, 21.00),
        ('Flying Mikki', 16, 10.00),
        ('Itazura', 19, 19.00),
        ('Zourain', 15, 31.00),
        ('Flag Flyer', 13, 31.00),
        ('Politely Dun', 17, 41.00),
        ('I Am Velvet', 14, 15.00),
    ],
    5: [
        ("Enna's Dream", 5, 23.00),
        ('Cherish Me', 7, 6.50),
        ('Stealth Of Night', 2, 4.40),
        ("Stage 'n' Screen", 8, 18.00),
        ('Takeko', 6, 13.00),
        ('Proven Soul', 16, 12.00),
        ('Lovelycut', 3, 13.00),
        ('Silent Shares', 1, 10.00),
        ('Meh Keffi', 12, 23.00),
        ('Recuperato', 9, 8.00),
        ('Salizou', 10, 7.50),
        ('Brilliant Horizon', 14, 7.00),
        ('Sixteen Reasons', 4, 61.00),
        ('Claymore Mine', 15, 51.00),
        ("She's Pretty Rich", 13, 61.00),
        ('Illyivy', 11, 34.00),
    ],
    6: [
        ('Touchdown', 10, 2.00),
        ('Kaleo', 9, 6.50),
        ('Boltsaver', 14, 12.00),
        ('Farhh Flung', 5, 19.00),
        ('Madero', 6, 31.00),
        ('Hurry Curry', 8, 51.00),
        ('Shockletz', 1, 7.00),
        ('Indispensable', 13, 21.00),
        ('New York Hurricane', 2, 81.00),
        ('Castle On High', 17, 13.00),
        ('Unbelievable', 3, 21.00),
        ("Nation's Call", 7, 21.00),
        ('Angland', 11, 23.00),
        ('Dictionary', 12, 101.00),
    ],
    7: [
        ('Arkansaw Kid', 2, 7.50),
        ('Ndola', 5, 5.00),
        ('Fancify', 7, 11.00),
        ('War Machine', 1, 3.30),
        ('Royal Insignia', 8, 15.00),
        ('Cote Atlantique', 4, 7.50),
        ('Boomtown Boss', 6, 9.00),
        ('Star Patrol', 3, 5.50),
        ('Windstorm', 9, 126.00),
    ],
    8: [
        ('Duchess Zou', 7, 3.90),
        ('Coeur Volante', 1, 10.00),
        ('Sass Appeal', 10, 1.95),
        ('Rise At Dawn', 2, 7.50),
        ('Craig', 3, 16.00),
        ('Ten Commandments', 11, 8.00),
        ('Asva', 6, 71.00),
        ('Star Vega', 8, 101.00),
        ('Furious', 12, 51.00),
    ],
    9: [
        ('El Pibe De Oro', 10, 8.50),
        ('Nimbustwothousand', 4, 8.00),
        ('Jennyanydots', 7, 21.00),
        ('Big Day Out', 6, 41.00),
        ('Naval Academy', 3, 5.50),
        ('Along The River', 1, 17.00),
        ('Per Sempre', 9, 12.00),
        ('Just Like Gaby', 11, 2.70),
        ('Electric Star', 12, 16.00),
        ('Rhapsody Chic', 5, 34.00),
        ('Moby Dick', 2, 11.00),
        ('Charmed Run', 8, 18.00),
    ],
}
