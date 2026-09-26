"""MAPLE VILLAGE: home. A whistled tune over a guitar and a walking bass;
the festival arrangement plays once the storm is calmed."""

from musiclib import arp, bass, ch, grid, pad, song

INTRO = "D | A7"
LOOP = """D | G | A | D | Bm | G | Em7 A7 | D |
          D | G | A | D | Bm | Em | A7 | D |
          G | A | F#m | Bm | Em | A | D/F# G | A7"""

MELODY = """
    r1 | r2 r4 o4 a4 |
    L
    ; A: the hook climbs through each chord
    o4 f+8 a8 >d4 <a8 f+8 d4 | o4 g8 b8 >d4 <b8 g8 d4 |
    o4 e8 a8 >c+4 <a8 >c+8 e4 | o5 d4. c+8 d2 |
    o5 d8 c+8 <b8 a8 b4 f+4 | o4 g8 f+8 g8 a8 b4 g4 |
    o4 e8 f+8 g8 e8 a8 b8 >c+8 <a8 | o5 d2 r4 <a4 |
    ; A': same start, a new answer
    o4 f+8 a8 >d4 <a8 f+8 d4 | o4 g8 b8 >d4 <b8 g8 d4 |
    o4 e8 a8 >c+4 <a8 >c+8 e4 | o5 d8 e8 f+8 e8 d4 r4 |
    o5 f+4 f+8 e8 d4 <b4 | o5 e4 e8 d8 <b4 g4 |
    o4 a8 b8 >c+8 d8 e4 c+4 | o5 d2. r4 |
    ; B: longer notes, a little wistful
    o5 d4. <b8 g4 b4 | o5 c+4. <a8 e4 a4 |
    o4 a4. f+8 c+4 f+4 | o4 f+2 d4 f+4 |
    o4 e4 g4 b4 >e4 | o5 c+4 <b4 a2 |
    o4 f+4 a4 g4 b4 | o4 a4 g4 e4 c+4 |
"""

HARMONY = """
    r1 | r1 |
    L
    ; thirds under the lead in the second half of each phrase
    r1 | r1 | r1 | o4 f+4. e8 f+2 |
    o4 f+8 e8 d8 c+8 d4 d4 | o4 d8 d8 e8 f+8 g4 d4 |
    o4 c+8 d8 e8 c+8 e8 g8 a8 e8 | o4 f+2 r2 |
    r1 | r1 | r1 | o4 f+8 g8 a8 g8 f+4 r4 |
    o4 d4 d8 c+8 < b4 f+4 | o4 g4 g8 f+8 d4 < b4 |
    o4 e8 f+8 g8 a8 c+4 e4 | o4 f+2. r4 |
    o4 b4. g8 d4 g4 | o4 a4. e8 c+4 e4 |
    o4 f+4. c+8 < a4 > c+4 | o4 d2 < b4 > d4 |
    o3 b4 >e4 g4 b4 | o4 a4 g4 e2 |
    o4 d4 f+4 d4 g4 | o4 e4 c+4 < a4 g4 |
"""

PAD_I = pad(INTRO, voices=2, center=62)
PAD_L = pad(LOOP, voices=2, center=62)

song("VILLAGE", "Maple Village", tempo=8, chords=LOOP, channels=[
    ch("lead", "whistle", MELODY, vol=104, gate=7, check=True),
    ch("harmony", "clarinet", HARMONY, vol=62, gate=7),
    ch("bass", "finger_bass", "o2 " + bass(INTRO, "rf4", low=38) + " L " + bass(LOOP, "rf4", low=38), vol=110, gate=6),
    ch("guitar", "guitar", arp(INTRO, "0212", step=24, center=60) + " L " + arp(LOOP, "0212", step=24, center=60),
       vol=70, gate=8),
    ch("pad", "strings", PAD_I[0] + " L " + PAD_L[0], vol=40, gate=8),
    ch("pad2", "strings", PAD_I[1] + " L " + PAD_L[1], vol=36, gate=8),
    ch("kick", "drums", grid(16, 2, J="x.......x.......") + " L " +
       grid(16, 24, J="x.......x.......", R="....x.......x..."), vol=96),
    ch("shaker", "drums", grid(16, 2, X="..x...x...x...x.") + " L " + grid(16, 24, X="o.x.o.x.o.x.o.x."), vol=90),
])
