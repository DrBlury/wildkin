"""Hall Masters and legends: D minor, faster and heavier than a wild bout.
Trumpet over a horn line, a choir, a galloping bass and timpani."""

from musiclib import bass, ch, grid, pad, song

INTRO = "A | A"
LOOP = """Dm | Bb | C | Dm |
          Dm | Bb | Gm | A |
          Gm | Dm | Bb | A |
          Gm | A | Dm Bb | A7"""

MELODY = """
    r1 | r2 o4 a8 b-8 >c+8 e8 |
    L
    ; A: the challenge
    o5 d4 a4 f4. e8 | o5 d4 c8 <b-8 >d4 f4 | o5 e4. d8 c4 g4 | o5 a2. r4 |
    o5 d4 a4 >d4. c8 | o5 b-4 a8 g8 f4 d4 | o5 g4. f8 d4 b-4 | o5 a2 e4 c+4 |
    ; B: the answer, rising to the break
    o5 g8 a8 b-8 a8 g4 d4 | o5 f8 g8 a8 g8 f4 d4 | o5 d8 e8 f8 e8 d4 <b-4 | o4 a4 >c+4 e4 a4 |
    o5 b-4. a8 g4 d4 | o5 c+4. d8 e4 a4 | o5 f4 d4 d4 f4 | o5 e4 c+4 <a4 g4 |
"""

# horn: long notes under the trumpet
HORN = """
    o3 a1 | o3 a2 >c+2 |
    L
    o4 f2 a2 | o4 f2 d2 | o4 g2 e2 | o4 f1 |
    o4 f2 a2 | o4 f2 d2 | o4 d2 b-2 | o4 c+1 |
    o4 d2 b-2 | o4 a2 f2 | o4 f2 d2 | o4 e1 |
    o4 d2 g2 | o4 e2 c+2 | o4 a2 f2 | o4 g2 e2 |
"""

CHOIR_I = pad(INTRO, voices=2, center=60)
CHOIR_L = pad(LOOP, voices=2, center=60)

TIMP = "o2 [a16]16 | [a16]8 a4 a4 | L " + bass(LOOP, "half", low=38)

song("MASTER", "Hall Master", tempo=5, chords=LOOP, level=0.95, channels=[
    ch("lead", "trumpet", MELODY, vol=100, gate=7, check=True),
    ch("horn", "horn", HORN, vol=58, gate=8),
    ch("bass", "synth_bass", bass(INTRO, "drive16", low=33) + " L " + bass(LOOP, "gallop", low=33),
       vol=100, gate=5),
    ch("choir", "choir", CHOIR_I[0] + " L " + CHOIR_L[0], vol=46, gate=8),
    ch("choir2", "choir", CHOIR_I[1] + " L " + CHOIR_L[1], vol=42, gate=8),
    ch("timpani", "timpani", TIMP, vol=90, gate=8),
    ch("drums", "drums", grid(16, 1, S="x.x.x.x.x.x.x.x.") + grid(16, 1, S="xxxxxxxxXXXXXXXX") +
       " L " + grid(16, 7, K="x..x..x...x..x..", S="....x.......x...") +
       grid(16, 1, K="x..x..x...x.....", S="....x...x.x.xxxx") +
       grid(16, 7, K="x..x..x...x..x..", S="....x.......x...") +
       grid(16, 1, K="x.....x.....x...", S="....x...xxxxXXXX"), vol=100),
    ch("hats", "drums", grid(16, 2, H="................") + " L " +
       grid(16, 1, C="x...............", H="..x.x.x.x.x.x.x.") + grid(16, 7, H="x.x.x.x.x.x.x.x.") +
       grid(16, 1, C="x...............", H="..x.x.x.x.x.x.x.") + grid(16, 7, H="x.x.x.x.x.x.x.x."), vol=100),
])
