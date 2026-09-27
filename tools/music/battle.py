"""Wild and warden bouts: A minor at a gallop. A saw lead with a pulse
shadow an octave down, 16th-note arpeggios, brass stabs and a driving
octave bass."""

from musiclib import arp, bass, ch, grid, pad, song, PPQ

INTRO = "E | E7"
LOOP = """Am | Am | F | G |
          Am | Am | F | E |
          Dm | Am | Dm | E |
          F | G | Am | E7"""

MELODY = """
    o4 e16 f16 e16 d+16 e16 f16 e16 d+16 e16 g+16 b16 >d16 e8 r8 | o5 e2 r4 <b8 >d8 |
    L
    ; A
    o5 e4. d8 c8 <b8 a8 >c8 | o4 a8 b8 >c8 d8 e4 a4 | o5 c4. <a8 f8 a8 >c4 | o5 d4. c8 <b4 g4 |
    o5 e4. d8 c8 <b8 a8 >c8 | o5 e8 f8 e8 d8 c4 e4 | o5 c4. <a8 f8 a8 >c4 | o4 b2 g+4 e4 |
    ; B: climbing to the top
    o5 d4 f4 a4. g8 | o5 e4 c4 <a4 >c4 | o5 d4 f4 a4 >d4 | o5 b2 g+4 e4 |
    o5 a4. g8 f8 e8 f8 a8 | o5 g4. f8 d8 e8 f8 g8 | o5 a4 e4 c4 e4 | o5 d4 <b4 g+4 b4 |
"""

STAB = [PPQ * 3 // 2, PPQ * 3 // 2, PPQ]
PAD_I = pad(INTRO, voices=2, center=62, rhythm=STAB)
PAD_L = pad(LOOP, voices=2, center=62, rhythm=STAB)

song("BATTLE", "Wild Bout", tempo=5.5, chords=LOOP, level=0.95, channels=[
    ch("lead", "saw_lead", MELODY, vol=96, gate=7, check=True),
    ch("shadow", "pulse", "k-12 " + MELODY, vol=40, gate=6, detune=6),
    ch("bass", "synth_bass", bass(INTRO, "drive16", low=33) + " L " + bass(LOOP, "oct8", low=33),
       vol=100, gate=5),
    ch("arp", "chip_arp", arp(INTRO, "0123", step=12, center=69) + " L " + arp(LOOP, "0121", step=12, center=69),
       vol=40, gate=6),
    ch("brass", "brass", PAD_I[0] + " L " + PAD_L[0], vol=46, gate=5),
    ch("brass2", "brass", PAD_I[1] + " L " + PAD_L[1], vol=42, gate=5),
    ch("drums", "drums", grid(16, 1, K="x...x...x...x...") + grid(16, 1, S="x.x.x.x.xxxxXXXX") +
       " L " + grid(16, 15, K="x.....x...x.....", S="....x.......x..x") +
       grid(16, 1, K="x.....x...x.....", S="....x...x.x.xxxx"), vol=100),
    ch("hats", "drums", grid(16, 1, C="x...............") + grid(16, 1, H="................") + " L " +
       grid(16, 1, C="x...............", H="..x.x.x.x.x.x.x.") + grid(16, 15, H="x.x.x.x.x.x.x.x."), vol=100),
])
