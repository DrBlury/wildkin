"""Caves, crypts and lairs: a slow E minor ocarina over a sub bass, low
pads and wind, with glockenspiel drips and a soft heartbeat drum."""

from musiclib import arp, bass, ch, grid, pad, song

LOOP = """Em | Cmaj7 | Em | B |
          Em | Cmaj7 | Am | B7 |
          C | D | Em | Em |
          Am | C | B | B"""

MELODY = """
    L
    o4 b2. a8 g8 | o4 e2 g4 b4 | o4 b2. >c8 <b8 | o4 f+1 |
    o4 g2. f+8 e8 | o4 e2 g4 >c4 | o4 a2 >c4 e4 | o4 d+2 f+2 |
    o4 e2. g4 | o4 f+2 a2 | o4 b1 | r1 |
    o5 c2. <a4 | o4 g2 e2 | o4 f+2. d+4 | o4 b2 r2 |
"""

PAD_L = pad(LOOP, voices=2, center=55)

# two bars per gust; the pitch sets how fast the noise loop is read
WIND = "L o5 c1^1 | o5 d1^1 | o5 c1^1 | o4 a1^1 | o5 c1^1 | o5 e1^1 | o5 d1^1 | o5 c1^1 |"

song("CAVE", "Glimmer Caverns", tempo=10, chords=LOOP, level=0.8, channels=[
    ch("lead", "ocarina", MELODY, vol=84, gate=7, check=True),
    ch("drips", "glock", "L " + arp(LOOP, "0314", step=36 * 2, center=76), vol=34, gate=8),
    ch("bass", "sub", "L " + bass(LOOP, "whole", low=28), vol=96, gate=8),
    ch("pad", "pad", "L " + PAD_L[0], vol=40, gate=8),
    ch("pad2", "pad", "L " + PAD_L[1], vol=36, gate=8),
    ch("wind", "wind", WIND, vol=30, gate=8),
    ch("drums", "drums", "L " + grid(16, 16, J="x.....x.........", U="..........o....."), vol=100),
])
