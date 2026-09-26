"""HEARTH HALL: a slow music-box waltz by the fire, with a harp and warm
pads. Every Hearth Hall plays it."""

from musiclib import arp, bass, ch, grid, pad, song

INTRO = "F | C7"
LOOP = """F | C/E | Dm | Bb |
          F | Gm | C7 | C7 |
          F | A7 | Dm | Bb |
          F/C | C7 | F | F"""

MELODY = """
    r2. | r2 o5 c4 |
    L
    o5 c4 a4 f4 | o5 e4. d8 c4 | o5 d4 f4 a4 | o5 b-2 a4 |
    o5 a4 g4 f4 | o5 g4 b-4 d4 | o5 e4 g4 b-4 | o5 c2. |
    o5 c4 f4 a4 | o5 c+4. e8 g4 | o5 f4 e4 d4 | o5 d2 <b-4 |
    o5 c4 a4 g4 | o5 g4 e4 b-4 | o5 a2 g4 | o5 f2. |
"""

# a second music box a sixth below, on the second half of each phrase
ECHO = """
    r2. | r2. |
    L
    r2. | r2. | r2. | o4 d2 c4 |
    r2. | r2. | r2. | o4 e2. |
    r2. | r2. | r2. | o4 f2 d4 |
    r2. | r2. | o4 c2 e4 | o4 a2. |
"""

PAD_I = pad(INTRO, voices=2, center=60, beats=3)
PAD_L = pad(LOOP, voices=2, center=60, beats=3)

song("HEARTH", "Hearth Hall", tempo=9, beats=3, chords=LOOP, channels=[
    ch("lead", "musicbox", MELODY, vol=110, gate=7, check=True),
    ch("echo", "celesta", ECHO, vol=56, gate=7),
    ch("bass", "finger_bass", bass(INTRO, "waltz", low=36, beats=3) + " L " + bass(LOOP, "waltz", low=36, beats=3),
       vol=92, gate=6),
    ch("harp", "harp", arp(INTRO, "012321", step=24, center=60, beats=3) + " L " +
       arp(LOOP, "012321", step=24, center=60, beats=3), vol=54, gate=8),
    ch("pad", "warm", PAD_I[0] + " L " + PAD_L[0], vol=40, gate=8),
    ch("pad2", "warm", PAD_I[1] + " L " + PAD_L[1], vol=36, gate=8),
    ch("bells", "drums", grid(12, 2, I="............") + " L " + grid(12, 16, I="x...........", X="....o...o..."),
       vol=100),
])
