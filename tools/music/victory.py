"""After a won bout: a two-bar trumpet fanfare, then a relaxed loop on a
flute that plays until the bout screen closes."""

from musiclib import arp, bass, ch, grid, pad, song

INTRO = "C | G"
LOOP = """C | Am | F | G |
          C | Am | Dm G | C"""

MELODY = """
    @trumpet o4 { g g g }8 >c4 r8 < { g g g }8 >c4 e8 | o5 g2. r4 |
    L @flute
    o5 e4 g4 e8 d8 c4 | o5 c4 e4 a4 g8 e8 | o5 f4 a4 c4 f4 | o5 d2 <b4 g4 |
    o5 e4 g4 >c4 <g4 | o5 a4. g8 e4 c4 | o5 d4 f4 d4 <b4 | o5 c2 r2 |
"""

PAD_I = pad(INTRO, voices=2, center=62)
PAD_L = pad(LOOP, voices=2, center=62)

song("VICTORY", "Victory", tempo=7, chords=LOOP, channels=[
    ch("lead", "trumpet", MELODY, vol=100, gate=7, check=True),
    ch("bass", "bass_pluck", bass(INTRO, "root4", low=36) + " L " + bass(LOOP, "rf4", low=36), vol=100, gate=6),
    ch("harp", "harp", "r1 | r1 | L " + arp(LOOP, "0121", step=24, center=64), vol=62, gate=8),
    ch("pad", "strings", PAD_I[0] + " L " + PAD_L[0], vol=40, gate=8),
    ch("pad2", "strings", PAD_I[1] + " L " + PAD_L[1], vol=36, gate=8),
    ch("drums", "drums", grid(16, 1, S="x.x.x.x.x...x...") + grid(16, 1, K="x...............", C="x...............") +
       " L " + grid(16, 8, J="x.......x.......", Z="....x.......x..."), vol=100),
    ch("shaker", "drums", "r1 | r1 | L " + grid(16, 8, X="..x...x...x...x."), vol=100),
])
