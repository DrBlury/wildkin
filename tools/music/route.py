"""WHISPER MEADOW and the roads between towns: a bright walking tune on a
chip lead over broken-chord guitar, an octave bass and a slow flute
counterline."""

from musiclib import arp, bass, ch, grid, pad, song

INTRO = "C | D"
LOOP = """G | D/F# | Em | C D |
          G | D/F# | C | D |
          Em | C | G | D |
          C | D | G C | D7"""

MELODY = """
    r1 | r2 r4 o4 a8 b8 |
    L
    ; A: up the hill and back
    o5 d4 <b8 >d8 g4 f+8 e8 | o5 d4. e8 f+4 a4 | o5 g4. f+8 e4 <b4 | o5 c8 d8 e8 c8 <a4 >d4 |
    o5 d4 <b8 >d8 g4 f+8 e8 | o5 d4. e8 f+4 a4 | o5 g4. e8 c4 e4 | o5 d2. r4 |
    ; B: running eighths, then home
    o5 e8 f+8 g8 e8 b4 g4 | o5 c8 d8 e8 c8 g4 e4 | o5 d8 e8 d8 <b8 g4 b4 | o4 a4. b8 a4 f+4 |
    o4 g8 a8 >c8 e8 g4 e4 | o5 f+8 e8 d8 e8 f+4 a4 | o5 g4 d4 e4 c4 | o5 d4 c8 <b8 a4 >c4 |
"""

# half notes a sixth or so under the tune
COUNTER = "r1 | r1 | L " + " ".join(
    f"o4 {a}2 {b}2 |" for a, b in [
        ("b", "g"), ("a", "f+"), ("g", "b"), ("g", "f+"),
        ("b", "g"), ("a", "d"), ("e", "g"), ("f+", "a"),
        ("g", "b"), ("e", "g"), ("d", "g"), ("f+", "d"),
        ("e", "c"), ("f+", "a"), ("b", "c"), ("a", "f+")])

PAD_I = pad(INTRO, voices=2, center=64)
PAD_L = pad(LOOP, voices=2, center=64)

song("ROUTE", "Whisper Road", tempo=7, chords=LOOP, channels=[
    ch("lead", "square", MELODY, vol=92, gate=6, check=True),
    ch("bass", "bass", bass(INTRO, "oct8", low=36) + " L " + bass(LOOP, "oct8", low=36), vol=88, gate=5),
    ch("guitar", "guitar", arp(INTRO, "0121", step=24, center=60) + " L " + arp(LOOP, "0121", step=24, center=60),
       vol=64, gate=8),
    ch("pad", "strings", PAD_I[0] + " L " + PAD_L[0], vol=36, gate=8),
    ch("pad2", "strings", PAD_I[1] + " L " + PAD_L[1], vol=32, gate=8),
    ch("counter", "flute", COUNTER, vol=42, gate=7),
    ch("drums", "drums", grid(16, 1, K="x.......x.......") + grid(16, 1, K="x.......x.......", S="............x.x.") +
       " L " + grid(16, 16, K="x.......x.x.....", S="....x.......x..."), vol=100),
    ch("hats", "drums", grid(16, 2, H="..x...x...x...x.") + " L " + grid(16, 16, H="x.o.x.o.x.o.x.o."), vol=100),
])
