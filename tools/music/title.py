"""The title screen: WILDKIN's main theme in D major. A timpani roll and
string swell, then a trumpet anthem over horns, harp and a marching snare."""

from musiclib import arp, bass, ch, grid, pad, song

INTRO = "D | A"
LOOP = """D | A/C# | Bm | G |
          D | Em | G A | D |
          Bm | G | D | A |
          Bm | G | Em A | D"""

MELODY = """
    r1 | r2 o4 a8 b8 >c+8 e8 |
    L
    ; A: the call
    o5 d4. <a8 >d4 f+4 | o5 e4. c+8 <a4 >e4 | o5 f+4. e8 d4 <b4 | o5 d2 <b4 >d4 |
    o5 a4. f+8 a4 >d4 | o5 g4. f+8 e4 b4 | o5 b4 a8 g8 a4 e4 | o5 f+2. r4 |
    ; B: out into the wild
    o5 f+4 b8 a8 f+4 d4 | o5 g4 b4 d4 g4 | o5 f+4. e8 d4 a4 | o5 e2 c+4 e4 |
    o5 d4 f+4 b4 a4 | o5 b4. a8 g4 d4 | o5 e4 g4 a4 c+4 | o5 d2. r4 |
"""

# horns: half-note thirds and sixths under the tune
HORN = "o4 d1 | o4 c+1 | L " + " ".join(
    f"o4 {a}2 {b}2 |" for a, b in [
        ("a", "a"), ("a", "c+"), ("d", "d"), ("b", "g"),
        ("f+", "f+"), ("e", "g"), ("g", "e"), ("d", "a"),
        ("d", "d"), ("d", "b"), ("a", "f+"), ("c+", "e"),
        ("f+", "d"), ("g", "b"), ("b", "e"), ("f+", "a")])

PAD_I = pad(INTRO, voices=2, center=62)
PAD_L = pad(LOOP, voices=2, center=62)

TIMP = "o2 [d16]16 | a4 a4 a4 [a16]4 | L " + bass(LOOP, "half", low=38)

song("TITLE", "WILDKIN", tempo=8, chords=LOOP, channels=[
    ch("lead", "trumpet", MELODY, vol=100, gate=7, check=True),
    ch("horn", "horn", HORN, vol=54, gate=7),
    ch("bass", "tuba", bass(INTRO, "whole", low=38) + " L " + bass(LOOP, "rf4", low=38), vol=84, gate=6),
    ch("harp", "harp", "r1 | r1 | L " + arp(LOOP, "0123", step=12, center=67), vol=46, gate=8),
    ch("pad", "strings", PAD_I[0] + " L " + PAD_L[0], vol=44, gate=8),
    ch("pad2", "strings", PAD_I[1] + " L " + PAD_L[1], vol=40, gate=8),
    ch("timpani", "timpani", TIMP, vol=86, gate=8),
    ch("drums", "drums", grid(16, 1, C="................") + grid(16, 1, S="............xxXX") + " L " +
       grid(16, 1, C="x...............", S="....x.......x.o.") +
       grid(16, 15, K="x.......x.......", S="....x..o....x.oo"), vol=100),
])
