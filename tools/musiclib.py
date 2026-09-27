#!/usr/bin/env python3
"""Music toolkit for WILDKIN: waveforms, drum samples, instruments, an MML
compiler and accompaniment helpers.

tools/gen_music.py imports the songs in tools/music/*.py (each calls
song(...)) and writes src/music_data.h for the engine in src/game/music.c.

Everything here uses only + - * / on floats and integer maths (no libm), so
the generated header is byte-identical on every platform: CI regenerates it
and fails on any difference.

Timing: 48 ticks per quarter note. A song's tempo is given in frames per
16th note (7 -> 128.6 BPM, 8 -> 112.5 BPM, 6 -> 150 BPM); whole-frame values
keep every 16th exactly the same length.

MML dialect (one string per channel)
------------------------------------
  c d e f g a b     notes; + or # sharp, - flat:  c+ e- f#
  r                 rest
  4 8. 16 %36       length after a note/rest: 1/N note, dotted, or raw ticks
  ^8                tie more length onto the previous note/rest:  c4^16
  &                 legato into the next note (no re-attack):   c4&d4
  { c e g }4        tuplet: the notes share the length evenly (triplets)
  o4 > <            octave (o4 c = middle C, MIDI 60), up, down
  l8                default length
  k-2               transpose following notes by semitones
  v100              channel volume 0..127
  q6                gate: notes sound 6/8 of their length (q8 = full legato)
  @flute            instrument
  D+6               detune in 1/64 semitones
  P12               portamento speed (1/64 semitones per frame, 0 = off)
  A047 / A          arpeggio offsets in semitones (hex digits), cycling each frame / off
  [ ... ]3          repeat 3 times;  [ a / b ]3 plays  a b a b a
  |                 bar line: checked against the song's bar length
  L                 loop point (same tick in every channel)
  ; comment         to the end of the line

Drum channels (drum=True) use letters for the kit instead of notes:
  K kick   J soft kick   S snare   Z brush   P clap   H hat   O open hat
  X shaker C crash       R rim     L/M/T toms W woodblock  I triangle
  B tambourine  N thunder  U splash drop
"""

import itertools
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# output format
# ---------------------------------------------------------------------------

CYCLES_PER_FRAME = 280896
RATE_CYCLES = 1254                           # timer 0 period (CPU cycles)
MIX_LEN = CYCLES_PER_FRAME // RATE_CYCLES    # 224 samples per frame
RATE = 16777216.0 / RATE_CYCLES              # 13378.9 Hz
assert MIX_LEN * RATE_CYCLES == CYCLES_PER_FRAME and MIX_LEN % 16 == 0

PPQ = 48
WHOLE = PPQ * 4
MAX_CHANNELS = 8

# ---------------------------------------------------------------------------
# deterministic maths (basic IEEE operations only)
# ---------------------------------------------------------------------------

PI = 3.141592653589793
TWO_PI = 6.283185307179586
HALF_PI = 1.5707963267948966
LN2 = 0.6931471805599453


def dsin(x):
    x = x - TWO_PI * float(int(x / TWO_PI))
    if x > PI:
        x -= TWO_PI
    elif x < -PI:
        x += TWO_PI
    if x > HALF_PI:
        x = PI - x
    elif x < -HALF_PI:
        x = -PI - x
    x2 = x * x
    term = x
    s = x
    for k in range(1, 10):
        term *= -x2 / ((2 * k) * (2 * k + 1))
        s += term
    return s


def dcos(x):
    return dsin(x + HALF_PI)


def dexp(x):
    halvings = 0
    while x > 0.5 or x < -0.5:
        x *= 0.5
        halvings += 1
    s = 1.0
    term = 1.0
    for i in range(1, 22):
        term *= x / i
        s += term
    for _ in range(halvings):
        s *= s
    return s


def dexp2(x):
    return dexp(x * LN2)


def dln(x):
    """Natural log for x > 0 (atanh series after scaling into [0.5, 2])."""
    k = 0
    while x > 2.0:
        x *= 0.5
        k += 1
    while x < 0.5:
        x *= 2.0
        k -= 1
    y = (x - 1.0) / (x + 1.0)
    y2 = y * y
    term = y
    s = 0.0
    for n in range(0, 40):
        s += term / (2 * n + 1)
        term *= y2
    return 2.0 * s + k * LN2


def dpow(x, e):
    return dexp(e * dln(x))


def rnd(x):
    """Round half away from zero (deterministic)."""
    return int(x + 0.5) if x >= 0 else -int(-x + 0.5)


class Noise:
    """xorshift32: identical white noise everywhere."""

    def __init__(self, seed):
        self.s = seed & 0xFFFFFFFF or 1

    def next(self):
        s = self.s
        s ^= (s << 13) & 0xFFFFFFFF
        s ^= s >> 17
        s ^= (s << 5) & 0xFFFFFFFF
        self.s = s
        return s

    def white(self):
        """Uniform in [-1, 1)."""
        return (self.next() & 0xFFFF) / 32768.0 - 1.0


def normalize(vals, peak=118):
    m = max(abs(v) for v in vals) or 1.0
    return [max(-128, min(127, rnd(v * peak / m))) for v in vals]


# ---------------------------------------------------------------------------
# waveforms: 64 steps, signed 8-bit
# ---------------------------------------------------------------------------

WAVE_LEN = 64


def additive(partials, peak=118):
    """partials: (harmonic, amplitude[, phase]) tuples."""
    out = []
    for i in range(WAVE_LEN):
        x = TWO_PI * i / WAVE_LEN
        v = 0.0
        for p in partials:
            h, a = p[0], p[1]
            ph = p[2] if len(p) > 2 else 0.0
            v += a * dsin(h * x + ph)
        out.append(v)
    return normalize(out, peak)


def pulse(duty, peak=112):
    hi = rnd(WAVE_LEN * duty)
    return [peak if i < hi else -peak for i in range(WAVE_LEN)]


def quantize4(vals):
    """Game Boy wave-channel flavour: 16 levels."""
    return [max(-128, min(127, (rnd((v + 128) * 15 / 255) * 255 // 15) - 128)) for v in vals]


def saw_partials(n, tilt=1.0):
    return [(h, 1.0 / dpow(h, tilt)) for h in range(1, n + 1)]


def square_partials(n):
    return [(h, 1.0 / h) for h in range(1, n + 1, 2)]


WAVES = {}


def _waves():
    W = WAVES
    W["square"] = pulse(0.5)
    W["pulse25"] = pulse(0.25)
    W["pulse12"] = pulse(0.125)
    W["saw"] = normalize([112 - i * 224 / (WAVE_LEN - 1) for i in range(WAVE_LEN)], 112)
    W["tri"] = normalize([(i if i < 32 else 64 - i) - 16 for i in range(WAVE_LEN)], 118)
    W["sine"] = additive([(1, 1.0)])
    W["soft_square"] = additive(square_partials(9))
    W["soft_pulse"] = additive([(h, dsin(PI * h * 0.25) / h) for h in range(1, 11)])
    W["soft_saw"] = additive(saw_partials(10))
    W["flute"] = additive([(1, 1.0), (2, 0.22), (3, 0.08)])
    W["whistle"] = additive([(1, 1.0), (2, 0.06), (3, 0.03)])
    W["clarinet"] = additive([(1, 1.0), (3, 0.55), (5, 0.3), (7, 0.16), (9, 0.08)])
    W["oboe"] = additive([(1, 0.55), (2, 0.9), (3, 0.75), (4, 0.4), (5, 0.25), (6, 0.12)])
    W["brass"] = additive(saw_partials(8, 0.8))
    W["strings"] = additive([(h, 1.0 / h, 0.3 * h) for h in range(1, 13)])
    W["organ"] = additive([(1, 1.0), (2, 0.6), (3, 0.3), (4, 0.45), (6, 0.2), (8, 0.25)])
    W["vocal"] = additive([(1, 1.0), (2, 0.65), (3, 0.9), (4, 0.3), (5, 0.12)])
    W["choir"] = additive([(1, 1.0), (2, 0.35), (3, 0.45), (4, 0.1)])
    W["bell"] = additive([(1, 1.0), (4, 0.45), (7, 0.18), (10, 0.12)])
    W["marimba"] = additive([(1, 1.0), (4, 0.28), (10, 0.06)])
    W["piano"] = additive([(1, 1.0), (2, 0.5), (3, 0.3), (4, 0.2), (5, 0.14), (6, 0.08), (7, 0.05)])
    W["bass"] = additive([(1, 1.0), (2, 0.55), (3, 0.28), (4, 0.1)])
    W["harp"] = additive([(1, 1.0), (2, 0.3), (3, 0.12)])
    W["guitar"] = additive([(1, 1.0), (2, 0.7), (3, 0.45), (4, 0.3), (5, 0.25), (6, 0.12), (8, 0.05)])
    W["reed"] = additive([(1, 1.0), (2, 0.8), (3, 0.6), (4, 0.5), (5, 0.38), (6, 0.28), (7, 0.18)])
    W["gb_bass"] = quantize4(additive([(1, 1.0), (2, 0.45), (3, 0.2)]))
    W["gb_soft"] = quantize4(additive([(1, 1.0), (3, 0.12)]))


_waves()

# ---------------------------------------------------------------------------
# noise loops: 4096 steps (the engine steps them at a rate set by the note)
# ---------------------------------------------------------------------------

NOISE_LEN = 4096
NOISES = {}


def _noises():
    n = Noise(0xC0FFEE)
    white = [n.white() for _ in range(NOISE_LEN)]
    NOISES["white"] = normalize(white, 110)
    lp = []
    y = 0.0
    for _ in range(2):          # run twice so the loop point is seamless
        lp = []
        for v in white:
            y += (v - y) * 0.12
            lp.append(y)
    NOISES["wind"] = normalize(lp, 116)


_noises()

# ---------------------------------------------------------------------------
# drum samples (one-shots at the output rate)
# ---------------------------------------------------------------------------

SAMPLES = {}          # name -> (data, base MIDI note)


def _decay(tau_s):
    return dexp(-1.0 / (tau_s * RATE))


def _sweep_tone(f0, f1, ftau, atau, secs, click=0.0, partials=((1, 1.0),)):
    out = []
    ph = 0.0
    f = f0
    fk = _decay(ftau)
    a = 1.0
    ak = _decay(atau)
    for i in range(int(secs * RATE)):
        v = 0.0
        for h, amp in partials:
            v += amp * dsin(ph * h)
        if click and i < 40:
            v += click * (1.0 - i / 40.0)
        out.append(v * a)
        ph += TWO_PI * f / RATE
        f = f1 + (f - f1) * fk
        a *= ak
    return out


def _noise_hit(seed, secs, tau, hp=0.0, lp=1.0, attack=0.0):
    n = Noise(seed)
    out = []
    a = 1.0
    ak = _decay(tau)
    prev = 0.0
    y = 0.0
    att = int(attack * RATE)
    for i in range(int(secs * RATE)):
        w = n.white()
        x = w - prev * hp          # simple high-pass (difference)
        prev = w
        y += (x - y) * lp          # one-pole low-pass
        g = a * (i / att if att and i < att else 1.0)
        out.append(y * g)
        a *= ak
    return out


def _mix(*parts):
    n = max(len(p) for p, _ in parts)
    out = [0.0] * n
    for p, g in parts:
        for i, v in enumerate(p):
            out[i] += v * g
    return out


def _fade_tail(vals, secs=0.02):
    n = int(secs * RATE)
    for i in range(min(n, len(vals))):
        vals[len(vals) - 1 - i] *= i / n
    return vals


def _add_sample(name, vals, base=60, peak=120):
    SAMPLES[name] = (normalize(_fade_tail(list(vals)), peak), base)


def _samples():
    _add_sample("kick", _mix((_sweep_tone(170, 48, 0.035, 0.09, 0.26, click=0.6), 1.0),
                             (_noise_hit(11, 0.02, 0.004, lp=0.5), 0.25)))
    _add_sample("kick_soft", _sweep_tone(120, 50, 0.04, 0.08, 0.24), peak=90)
    _add_sample("snare", _mix((_noise_hit(21, 0.22, 0.055, hp=0.6, lp=0.7), 1.0),
                              (_sweep_tone(230, 170, 0.02, 0.04, 0.2), 0.6)))
    _add_sample("brush", _noise_hit(23, 0.2, 0.07, hp=0.8, lp=0.45, attack=0.012), peak=80)
    clap = []
    for k in range(3):
        clap += [v * (0.8 + 0.1 * k) for v in _noise_hit(31 + k, 0.011, 0.004, hp=0.7, lp=0.6)]
    clap += _noise_hit(34, 0.16, 0.045, hp=0.7, lp=0.55)
    _add_sample("clap", clap)
    _add_sample("hat", _noise_hit(41, 0.06, 0.013, hp=1.0, lp=0.9), peak=88)
    _add_sample("ohat", _noise_hit(42, 0.32, 0.09, hp=1.0, lp=0.9), peak=84)
    _add_sample("shaker", _noise_hit(43, 0.09, 0.025, hp=0.9, lp=0.5, attack=0.02), peak=70)
    _add_sample("crash", _noise_hit(51, 1.1, 0.33, hp=1.0, lp=0.8), peak=96)
    _add_sample("rim", _mix((_sweep_tone(900, 800, 0.01, 0.009, 0.05), 1.0),
                            (_noise_hit(61, 0.01, 0.003, hp=1.0), 0.5)), peak=100)
    _add_sample("tom", _sweep_tone(150, 100, 0.08, 0.12, 0.36, click=0.2), base=48)
    timp = _mix((_sweep_tone(116, 110, 0.05, 0.36, 0.95, partials=((1, 1.0), (1.5, 0.35), (2, 0.25))), 1.0),
                (_noise_hit(71, 0.08, 0.02, lp=0.25), 0.3))
    _add_sample("timpani", timp, base=45)
    thunder = []
    n = Noise(81)
    y1 = y2 = 0.0
    total = int(1.9 * RATE)
    for i in range(total):
        w = n.white()
        y1 += (w - y1) * 0.05
        y2 += (y1 - y2) * 0.08
        t = i / RATE
        env = (t / 0.12 if t < 0.12 else dexp(-(t - 0.12) / 0.55))
        rumble = 0.6 + 0.4 * dsin(TWO_PI * 3.1 * t) * dsin(TWO_PI * 1.3 * t + 1.0)
        crack = w * dexp(-t / 0.03) * 0.5
        thunder.append(y2 * env * rumble * 3.0 + crack)
    _add_sample("thunder", thunder, peak=118)
    _add_sample("wood", _sweep_tone(1050, 1000, 0.02, 0.022, 0.08, partials=((1, 1.0), (2.7, 0.3))), peak=100)
    _add_sample("triangle", _sweep_tone(2600, 2600, 1.0, 0.35, 0.7, partials=((1, 1.0), (2.76, 0.4), (5.4, 0.2))), peak=70)
    tamb = []
    for k in range(4):
        tamb += [v * (1.0 - 0.18 * k) for v in _noise_hit(91 + k, 0.022, 0.008, hp=1.0, lp=0.95)]
    tamb += _noise_hit(95, 0.14, 0.04, hp=1.0, lp=0.95)
    _add_sample("tamb", tamb, peak=80)
    _add_sample("drop", _sweep_tone(520, 1500, 0.025, 0.05, 0.12, partials=((1, 1.0),)), peak=90)


_samples()

# Drum kit: letter -> (sample, volume 0..255, semitone offset)
KIT = [
    ("K", "kick", 255, 0), ("J", "kick_soft", 230, 0), ("S", "snare", 220, 0),
    ("Z", "brush", 200, 0), ("P", "clap", 210, 0), ("H", "hat", 150, 0),
    ("O", "ohat", 150, 0), ("X", "shaker", 150, 0), ("C", "crash", 190, 0),
    ("R", "rim", 170, 0), ("L", "tom", 230, -5), ("M", "tom", 230, 0),
    ("T", "tom", 230, 5), ("W", "wood", 190, 0), ("I", "triangle", 150, 0),
    ("B", "tamb", 160, 0), ("N", "thunder", 255, 0), ("U", "drop", 170, 0),
]
KIT_SLOT = {k[0]: i + 1 for i, k in enumerate(KIT)}     # note byte = slot (1..)

# ---------------------------------------------------------------------------
# instruments
# ---------------------------------------------------------------------------

MK_WAVE, MK_NOISE, MK_PCM, MK_KIT = 1, 2, 3, 4

INSTRUMENTS = {}      # name -> dict
INSTR_ORDER = []


def instr(name, src, kind=MK_WAVE, vol=1.0, a=0, d=0, s=1.0, f=0, r=4, vib=None, sweep=0):
    """Envelope times are in frames (1/60 s): a = attack (linear), d = decay
    time constant toward sustain level s, f = slow fade time constant while
    held (0 = none), r = release time constant after the note ends.
    vib = (delay frames, depth cents, speed Hz). sweep = pitch slide per
    frame in 1/64 semitones."""
    INSTRUMENTS[name] = dict(name=name, src=src, kind=kind, vol=vol, a=a, d=d, s=s, f=f, r=r,
                             vib=vib, sweep=sweep)
    INSTR_ORDER.append(name)


def _instruments():
    # chip leads
    instr("square", "square", vol=0.62, a=0, d=10, s=0.8, r=3, vib=(22, 14, 6))
    instr("pulse", "pulse25", vol=0.62, a=0, d=10, s=0.78, r=3, vib=(22, 14, 6))
    instr("thin", "pulse12", vol=0.62, a=0, d=8, s=0.75, r=3, vib=(24, 12, 6))
    instr("chip_arp", "pulse12", vol=0.5, a=0, d=6, s=0.55, r=2)
    instr("blip", "square", vol=0.5, a=0, d=4, s=0.0, r=2)
    instr("saw_lead", "soft_saw", vol=0.6, a=1, d=14, s=0.8, r=4, vib=(20, 16, 6))
    # soft leads
    instr("flute", "flute", vol=0.95, a=4, d=20, s=0.85, r=6, vib=(18, 14, 5))
    instr("whistle", "whistle", vol=1.0, a=3, d=16, s=0.9, r=5, vib=(14, 18, 6))
    instr("ocarina", "gb_soft", vol=0.95, a=3, d=18, s=0.85, r=5, vib=(20, 12, 5))
    instr("clarinet", "clarinet", vol=0.8, a=3, d=20, s=0.85, r=5, vib=(24, 10, 5))
    instr("oboe", "oboe", vol=0.75, a=3, d=20, s=0.82, r=5, vib=(20, 12, 5))
    instr("violin", "strings", vol=0.75, a=5, d=30, s=0.85, r=8, vib=(16, 16, 6))
    instr("brass", "brass", vol=0.7, a=4, d=18, s=0.8, r=5, vib=(24, 10, 5))
    instr("trumpet", "brass", vol=0.72, a=2, d=12, s=0.85, r=4, vib=(20, 12, 6))
    instr("horn", "soft_saw", vol=0.72, a=7, d=30, s=0.9, r=8, vib=(30, 8, 5))
    instr("organ", "organ", vol=0.62, a=1, d=0, s=1.0, r=3)
    instr("accordion", "reed", vol=0.58, a=3, d=0, s=1.0, r=4, vib=(0, 8, 7))
    instr("vocal", "vocal", vol=0.7, a=8, d=0, s=1.0, r=10, vib=(20, 14, 5))
    # plucked / struck
    instr("pizz", "soft_saw", vol=0.8, a=0, d=0, s=1.0, f=7, r=3)
    instr("guitar", "guitar", vol=0.78, a=0, d=0, s=1.0, f=26, r=5)
    instr("harp", "harp", vol=0.95, a=0, d=0, s=1.0, f=40, r=12)
    instr("piano", "piano", vol=0.85, a=0, d=0, s=1.0, f=45, r=8)
    instr("epiano", "sine", vol=0.95, a=0, d=0, s=1.0, f=40, r=8, vib=(0, 6, 5))
    instr("marimba", "marimba", vol=0.95, a=0, d=0, s=1.0, f=11, r=4)
    instr("bell", "bell", vol=0.75, a=0, d=0, s=1.0, f=60, r=20)
    instr("glock", "bell", vol=0.7, a=0, d=0, s=1.0, f=22, r=8)
    instr("musicbox", "sine", vol=0.85, a=0, d=0, s=1.0, f=30, r=10)
    instr("celesta", "tri", vol=0.8, a=0, d=0, s=1.0, f=28, r=10)
    # basses
    instr("bass", "gb_bass", vol=0.95, a=0, d=0, s=1.0, r=3)
    instr("bass_pluck", "bass", vol=1.0, a=0, d=0, s=1.0, f=30, r=3)
    instr("finger_bass", "tri", vol=1.0, a=0, d=0, s=1.0, f=40, r=3)
    instr("synth_bass", "soft_square", vol=0.75, a=0, d=14, s=0.7, r=3)
    instr("chip_bass", "square", vol=0.55, a=0, d=0, s=1.0, r=2)
    instr("tuba", "brass", vol=0.8, a=3, d=20, s=0.85, r=5)
    instr("sub", "sine", vol=1.0, a=1, d=0, s=1.0, r=4)
    # pads
    instr("strings", "strings", vol=0.6, a=18, d=0, s=1.0, r=20, vib=(30, 10, 5))
    instr("pad", "soft_saw", vol=0.5, a=24, d=0, s=1.0, r=24, vib=(40, 8, 4))
    instr("warm", "tri", vol=0.8, a=20, d=0, s=1.0, r=20)
    instr("choir", "choir", vol=0.66, a=20, d=0, s=1.0, r=22, vib=(30, 12, 5))
    # noise and drums
    instr("wind", "wind", kind=MK_NOISE, vol=0.55, a=40, d=0, s=1.0, r=40)
    instr("rain", "white", kind=MK_NOISE, vol=0.22, a=20, d=0, s=1.0, r=30)
    instr("drums", "kit", kind=MK_KIT, vol=1.0, a=0, d=0, s=1.0, r=4)
    instr("timpani", "timpani", kind=MK_PCM, vol=1.0, a=0, d=0, s=1.0, r=10)


_instruments()


def instr_c_params(ins):
    def factor(frames):
        if frames <= 0:
            return 0
        return max(1, min(65535, rnd(65536.0 * (1.0 - dexp(-1.0 / frames)))))

    atk = 0 if ins["a"] <= 1 else max(1, rnd(65280.0 / ins["a"]))
    dec = factor(ins["d"])
    fade = factor(ins["f"])
    rel = 65535 if ins["r"] <= 0 else factor(ins["r"])
    sus = max(0, min(255, rnd(ins["s"] * 255)))
    vol = max(1, min(255, rnd(ins["vol"] * 255)))
    vd, vdepth, vspeed = ins["vib"] if ins["vib"] else (0, 0, 0)
    return dict(atk=atk, dec=dec, fade=fade, rel=rel, sus=sus, vol=vol,
                vib_delay=min(255, vd), vib_depth=min(255, rnd(vdepth * 0.64)),
                vib_speed=min(255, rnd(vspeed * 256.0 / 60.0)), sweep=ins["sweep"])

# ---------------------------------------------------------------------------
# MML compiler
# ---------------------------------------------------------------------------

NOTE_PC = {"c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11}

# byte-code
OP_END = 0x00
OP_REST, OP_INSTR, OP_VOL, OP_GATE, OP_DETUNE, OP_PORTA, OP_ARP, OP_LEGATO, OP_TEMPO, OP_VIB = range(0x80, 0x8A)


class MMLError(Exception):
    pass


def strip_comments(text):
    return "\n".join(line.split(";", 1)[0] for line in text.split("\n"))


def expand_repeats(text):
    pat = re.compile(r"\[([^\[\]]*)\](\d*)")
    while "[" in text:
        m = pat.search(text)
        if not m:
            raise MMLError("unbalanced [ ]")
        body, n = m.group(1), int(m.group(2) or 2)
        if "/" in body:
            head, tail = body.split("/", 1)
            rep = (head + " " + tail + " ") * (n - 1) + head
        else:
            rep = (body + " ") * n
        text = text[:m.start()] + " " + rep + " " + text[m.end():]
    if "]" in text:
        raise MMLError("unbalanced [ ]")
    return text


class Parser:
    def __init__(self, text, drum=False, bar=WHOLE, where=""):
        self.src = expand_repeats(strip_comments(text))
        self.i = 0
        self.drum = drum
        self.bar = bar
        self.where = where
        self.octave = 4
        self.length = PPQ
        self.transpose = 0
        self.tick = 0
        self.events = []           # (kind, ...)
        self.loop_tick = None
        self.legato_next = False

    def err(self, msg):
        ctx = self.src[max(0, self.i - 30):self.i + 10].replace("\n", " ")
        raise MMLError(f"{self.where}: {msg} (tick {self.tick}, bar {self.tick // self.bar + 1}) near '{ctx}'")

    def peek(self):
        return self.src[self.i] if self.i < len(self.src) else ""

    def number(self, signed=False):
        j = self.i
        if signed and self.peek() in "+-":
            self.i += 1
        while self.peek().isdigit():
            self.i += 1
        s = self.src[j:self.i]
        if s in ("", "+", "-"):
            return None
        return int(s)

    def length_spec(self, default):
        if self.peek() == "%":
            self.i += 1
            n = self.number()
            if n is None or n <= 0:
                self.err("bad %ticks length")
            base = n
        else:
            n = self.number()
            if n is None:
                base = default
            else:
                if n <= 0 or WHOLE % n:
                    self.err(f"length 1/{n} is not a whole number of ticks")
                base = WHOLE // n
        total = base
        add = base
        while self.peek() == ".":
            self.i += 1
            if add % 2:
                self.err("dotted length is not a whole number of ticks")
            add //= 2
            total += add
        return total

    def ties(self, dur):
        while True:
            self.skip_ws()
            if self.peek() != "^":
                return dur
            self.i += 1
            dur += self.length_spec(self.length)

    def skip_ws(self):
        while self.peek() and self.peek() in " \t\r\n":
            self.i += 1

    def add_note(self, midi, dur):
        legato = self.legato_next
        self.legato_next = False
        self.skip_ws()
        if self.peek() == "&":
            self.i += 1
            self.legato_next = True
        self.events.append(("note", midi, dur, legato, self.legato_next))
        self.tick += dur

    def parse_note_pitch(self, ch):
        pc = NOTE_PC[ch]
        while self.peek() in ("+", "#", "-"):
            pc += -1 if self.peek() == "-" else 1
            self.i += 1
        midi = 12 * (self.octave + 1) + pc + self.transpose
        if not 0 < midi < 128:
            self.err(f"note out of range ({midi})")
        return midi

    def parse(self):
        while True:
            self.skip_ws()
            c = self.peek()
            if not c:
                break
            self.i += 1
            if c == "|":
                if self.tick % self.bar:
                    self.err(f"bar line at {self.tick % self.bar} ticks into a bar")
            elif c == "L":
                if self.loop_tick is not None:
                    self.err("two loop points")
                self.loop_tick = self.tick
                self.events.append(("loop",))
            elif c == "o":
                n = self.number()
                if n is None:
                    self.err("o needs a number")
                self.octave = n
            elif c == ">":
                self.octave += 1
            elif c == "<":
                self.octave -= 1
            elif c == "l":
                self.length = self.length_spec(self.length)
            elif c == "k":
                n = self.number(signed=True)
                if n is None:
                    self.err("k needs a number")
                self.transpose = n
            elif c == "v":
                n = self.number()
                if n is None or not 0 <= n <= 127:
                    self.err("v needs 0..127")
                self.events.append(("vol", n))
            elif c == "q":
                n = self.number()
                if n is None or not 0 <= n <= 8:
                    self.err("q needs 0..8")
                self.events.append(("gate", n))
            elif c == "@":
                j = self.i
                while self.peek() and (self.peek().isalnum() or self.peek() == "_"):
                    self.i += 1
                name = self.src[j:self.i]
                if name not in INSTRUMENTS:
                    self.err(f"unknown instrument @{name}")
                self.events.append(("instr", name))
            elif c == "D":
                n = self.number(signed=True)
                if n is None:
                    self.err("D needs a number")
                self.events.append(("detune", n))
            elif c == "P":
                n = self.number()
                if n is None:
                    self.err("P needs a number")
                self.events.append(("porta", n))
            elif c == "A":
                offs = []
                while self.peek() and self.peek() in "0123456789abcdefABCDEF":
                    offs.append(int(self.peek(), 16))
                    self.i += 1
                if len(offs) > 4:
                    self.err("arpeggio has at most 4 steps")
                self.events.append(("arp", offs if len(offs) > 1 else []))
            elif c == "{":
                self.parse_tuplet()
            elif c == "r":
                dur = self.ties(self.length_spec(self.length))
                self.events.append(("rest", dur))
                self.tick += dur
                self.legato_next = False
            elif self.drum and c in KIT_SLOT:
                dur = self.ties(self.length_spec(self.length))
                self.add_note(KIT_SLOT[c], dur)
            elif not self.drum and c in NOTE_PC:
                midi = self.parse_note_pitch(c)
                dur = self.ties(self.length_spec(self.length))
                self.add_note(midi, dur)
            else:
                self.i -= 1
                self.err(f"unexpected '{c}'")
        return self

    def parse_tuplet(self):
        items = []          # ("note", midi) / ("rest",)
        while True:
            self.skip_ws()
            c = self.peek()
            if not c:
                self.err("unclosed {")
            self.i += 1
            if c == "}":
                break
            if c == "o":
                self.octave = self.number()
            elif c == ">":
                self.octave += 1
            elif c == "<":
                self.octave -= 1
            elif c == "r":
                items.append(("rest", 0))
            elif self.drum and c in KIT_SLOT:
                items.append(("note", KIT_SLOT[c]))
            elif not self.drum and c in NOTE_PC:
                items.append(("note", self.parse_note_pitch(c)))
            else:
                self.i -= 1
                self.err(f"unexpected '{c}' in tuplet")
        total = self.length_spec(self.length)
        if not items or total % len(items):
            self.err(f"tuplet of {len(items)} does not split {total} ticks evenly")
        each = total // len(items)
        for kind, v in items:
            if kind == "rest":
                self.events.append(("rest", each))
                self.tick += each
            else:
                self.events.append(("note", v, each, self.legato_next, False))
                self.legato_next = False
                self.tick += each


def dur_bytes(d):
    if d <= 0:
        raise MMLError("zero-length event")
    if d < 256:
        return [d]
    if d > 65535:
        raise MMLError("event too long")
    return [0, d & 0xFF, d >> 8]


def assemble(events, instr_index):
    """Events -> byte-code. A note that slurs into the next one (&) is sent
    with gate 8 so it never releases early; the channel's gate comes back
    for the last note of the slur."""
    out = []
    loop = None
    held = False
    gate = 8          # channel gate as written
    sent = 8          # gate the engine has
    for e in events:
        k = e[0]
        if k == "loop":
            loop = len(out)
        elif k == "note":
            _, midi, dur, legato, nxt = e
            want = 8 if nxt else gate
            if want != sent:
                out += [OP_GATE, want]
                sent = want
            if legato and held:
                out += [OP_LEGATO, midi] + dur_bytes(dur)
            else:
                out += [midi] + dur_bytes(dur)
            held = True
        elif k == "rest":
            out += [OP_REST] + dur_bytes(e[1])
            held = False
        elif k == "instr":
            out += [OP_INSTR, instr_index[e[1]]]
        elif k == "vol":
            out += [OP_VOL, e[1]]
        elif k == "gate":
            gate = sent = e[1]
            out += [OP_GATE, e[1]]
        elif k == "detune":
            out += [OP_DETUNE, e[1] & 0xFF]
        elif k == "porta":
            out += [OP_PORTA, min(255, e[1])]
        elif k == "arp":
            out += [OP_ARP, len(e[1])] + list(e[1])
        elif k == "tempo":
            out += [OP_TEMPO, e[1], e[2]]
        else:
            raise MMLError(f"unknown event {k}")
    out.append(OP_END)
    return out, loop

# ---------------------------------------------------------------------------
# songs
# ---------------------------------------------------------------------------

SONGS = []


def ch(name, instrument, mml, vol=100, gate=7, drum=None, check=False, detune=0):
    """One channel. `check` marks the melody: its strong-beat notes are
    compared against the song's chords."""
    if drum is None:
        drum = INSTRUMENTS[instrument]["kind"] == MK_KIT
    return dict(name=name, instrument=instrument, mml=mml, vol=vol, gate=gate, drum=drum,
                check=check, detune=detune)


def song(ident, title, tempo, channels, beats=4, chords=None, level=1.0, loop=True, desc=""):
    """tempo: frames per 16th note (may be fractional, e.g. 7.5).
    beats: quarter notes per bar (3 for waltzes; 6/8 = beats=3 with triplets).
    chords: optional progression checked against melody channels.
    loop=False makes a one-shot jingle (the song ends)."""
    SONGS.append(dict(ident=ident, title=title, tempo=tempo, channels=channels, beats=beats,
                      chords=chords, level=level, loop=loop, desc=desc))


def tempo_ratio(frames_per_16th):
    """ticks per frame = 12 / frames_per_16th as a small fraction num/den."""
    from fractions import Fraction
    fr = Fraction(12) / Fraction(frames_per_16th).limit_denominator(16)
    fr = fr.limit_denominator(255)
    if fr.numerator > 255 or fr.denominator > 255:
        raise MMLError("tempo out of range")
    return fr.numerator, fr.denominator


def bpm(frames_per_16th):
    return 900.0 / frames_per_16th

# ---------------------------------------------------------------------------
# harmony helpers
# ---------------------------------------------------------------------------

PC_NAMES = ["c", "c+", "d", "d+", "e", "f", "f+", "g", "g+", "a", "a+", "b"]
ROOT_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
QUALITY = {
    "": [0, 4, 7], "m": [0, 3, 7], "7": [0, 4, 7, 10], "maj7": [0, 4, 7, 11],
    "m7": [0, 3, 7, 10], "dim": [0, 3, 6], "dim7": [0, 3, 6, 9], "m7b5": [0, 3, 6, 10],
    "aug": [0, 4, 8], "sus2": [0, 2, 7], "sus4": [0, 5, 7], "add9": [0, 4, 7, 14],
    "madd9": [0, 3, 7, 14], "6": [0, 4, 7, 9], "m6": [0, 3, 7, 9], "9": [0, 4, 7, 10, 14],
    "maj9": [0, 4, 7, 11, 14], "m9": [0, 3, 7, 10, 14], "7sus4": [0, 5, 7, 10],
    "5": [0, 7],
}


class Chord:
    def __init__(self, sym):
        m = re.match(r"^([A-G])([#b]?)([a-z0-9]*)(?:/([A-G])([#b]?))?$", sym)
        if not m:
            raise MMLError(f"bad chord '{sym}'")
        root = ROOT_PC[m.group(1)] + (1 if m.group(2) == "#" else -1 if m.group(2) == "b" else 0)
        q = m.group(3)
        if q not in QUALITY:
            raise MMLError(f"unknown chord quality '{q}' in '{sym}'")
        self.sym = sym
        self.root = root % 12
        self.intervals = QUALITY[q]
        self.pcs = sorted({(self.root + i) % 12 for i in self.intervals})
        self.bass = self.root
        if m.group(4):
            self.bass = (ROOT_PC[m.group(4)] + (1 if m.group(5) == "#" else -1 if m.group(5) == "b" else 0)) % 12
        self.fifth = (self.root + (self.intervals[2] if len(self.intervals) > 2 else 7)) % 12

    def tones(self, lo, hi):
        """Chord tones (MIDI) within [lo, hi]."""
        return [n for n in range(lo, hi + 1) if n % 12 in self.pcs]


def parse_prog(prog, beats=4):
    """'C | G/B | Am . F . | G' -> [(start_tick, ticks, Chord)]. Each bar's
    tokens split it evenly; '.' extends the previous chord."""
    bar = PPQ * beats
    out = []
    t = 0
    for bar_txt in [b for b in prog.replace("\n", " ").split("|")]:
        toks = bar_txt.split()
        if not toks:
            continue
        step = bar // len(toks)
        if step * len(toks) != bar:
            raise MMLError(f"bar '{bar_txt}' does not split evenly")
        for tok in toks:
            if tok == ".":
                if not out:
                    raise MMLError("'.' before any chord")
                s, d, c = out[-1]
                out[-1] = (s, d + step, c)
            else:
                out.append((t, step, Chord(tok)))
            t += step
    return out


def prog_length(prog, beats=4):
    p = parse_prog(prog, beats)
    return p[-1][0] + p[-1][1] if p else 0


def n2mml(midi, ticks):
    """Absolute note as MML."""
    return f"o{midi // 12 - 1}{PC_NAMES[midi % 12]}%{ticks} "


def rest_mml(ticks):
    return f"r%{ticks} "


def nearest(pc, center):
    """MIDI note with pitch class pc nearest to center."""
    base = center - ((center - pc) % 12)
    return base if center - base <= 6 else base + 12


def bass(prog, style="root8", low=36, beats=4):
    """Bass line MML from a progression. Styles: whole, half, root4,
    root8, rf4 (root-fifth), oct8, walk, pulse, gallop, waltz, drive16."""
    items = parse_prog(prog, beats)
    out = []
    for idx, (start, dur, c) in enumerate(items):
        root = nearest(c.bass, low + 6)
        fifth = root + ((c.fifth - c.bass) % 12)
        if fifth - root < 5:
            fifth += 12
        nxt = items[idx + 1][2] if idx + 1 < len(items) else items[0][2]
        nroot = nearest(nxt.bass, root)

        def fill(pattern):
            """pattern: list of (ticks, midi or None); repeated to fill dur."""
            t = 0
            k = 0
            while t < dur:
                ln, n = pattern[k % len(pattern)]
                ln = min(ln, dur - t)
                out.append(rest_mml(ln) if n is None else n2mml(n, ln))
                t += ln
                k += 1

        if style == "whole":
            fill([(dur, root)])
        elif style == "half":
            fill([(PPQ * 2, root), (PPQ * 2, fifth)])
        elif style == "root4":
            fill([(PPQ, root)])
        elif style == "root8":
            fill([(PPQ // 2, root)])
        elif style == "drive16":
            fill([(PPQ // 4, root)])
        elif style == "rf4":
            fill([(PPQ, root), (PPQ, fifth - 12 if fifth - 12 >= low - 2 else fifth)])
        elif style == "oct8":
            fill([(PPQ // 2, root), (PPQ // 2, root + 12)])
        elif style == "pulse":
            fill([(PPQ * 3 // 2, root), (PPQ // 2, root), (PPQ, fifth), (PPQ, root + 12)])
        elif style == "gallop":
            fill([(PPQ // 2, root), (PPQ // 4, root), (PPQ // 4, root)])
        elif style == "waltz":
            fill([(PPQ, root), (PPQ, fifth), (PPQ, fifth)])
        elif style == "walk":
            beats_here = dur // PPQ
            third = root + ((c.pcs[1] - c.root) % 12 if len(c.pcs) > 1 else 4)
            tones = [root, third if third > root else third + 12, fifth]
            line = []
            for b in range(beats_here):
                if b == beats_here - 1 and beats_here > 1:
                    # approach the next root from a half step
                    line.append(nroot - 1 if nroot > root else nroot + 1)
                else:
                    line.append(tones[b % len(tones)])
            for n in line:
                out.append(n2mml(n, PPQ))
            rem = dur - beats_here * PPQ
            if rem:
                out.append(n2mml(root, rem))
        else:
            raise MMLError(f"unknown bass style {style}")
    return "".join(out)


def arp(prog, pattern="0121", step=12, center=64, beats=4, span=None):
    """Broken-chord accompaniment. pattern: digits index the chord tones
    stacked upward from the one nearest `center` (0 = lowest)."""
    items = parse_prog(prog, beats)
    out = []
    idx_list = [int(ch) for ch in pattern if ch.isdigit()]
    for start, dur, c in items:
        base = nearest(c.pcs[0], center - 5)
        tones = [n for n in range(base, base + 30) if n % 12 in c.pcs]
        t = 0
        k = 0
        while t < dur:
            ln = min(step, dur - t)
            out.append(n2mml(tones[idx_list[k % len(idx_list)]], ln))
            t += ln
            k += 1
    return "".join(out)


def pad(prog, voices=3, center=60, beats=4, rhythm=None):
    """Sustained chords with smooth voice leading; returns one MML string per
    voice (lowest first). rhythm: optional list of note lengths (ticks)
    repeated inside each chord, e.g. [PPQ] for quarter-note stabs."""
    items = parse_prog(prog, beats)
    prev = None
    lines = [[] for _ in range(voices)]
    for start, dur, c in items:
        cand = c.tones(center - 9, center + 12)
        best = None
        # choose `voices` distinct chord tones close to the previous voicing
        for combo in itertools.combinations(cand, voices):
            pcs = {n % 12 for n in combo}
            if len(pcs) < min(voices, len(c.pcs)):
                continue
            if combo[-1] - combo[0] > 14:
                continue
            if prev is None:
                cost = abs(sum(combo) / voices - center)
            else:
                cost = sum(abs(a - b) for a, b in zip(combo, prev))
            if best is None or cost < best[0]:
                best = (cost, combo)
        combo = best[1]
        prev = combo
        for v in range(voices):
            if rhythm:
                t = 0
                k = 0
                while t < dur:
                    ln = min(rhythm[k % len(rhythm)], dur - t)
                    lines[v].append(n2mml(combo[v], ln))
                    t += ln
                    k += 1
            else:
                lines[v].append(n2mml(combo[v], dur))
    return ["".join(l) for l in lines]


def grid(steps, bars=1, step=12, **parts):
    """Drum pattern from step grids: grid(16, K='x...x...', S='....x...').
    'x' hit, 'X' accent, 'o' ghost, '.' rest. Earlier parts win when two
    hit on the same step. Each grid string is repeated to fill `steps`."""
    order = list(parts.keys())
    out = []
    for _ in range(bars):
        cur_vol = None
        i = 0
        while i < steps:
            hit = None
            for letter in order:
                g = parts[letter].replace(" ", "")
                c = g[i % len(g)]
                if c in "xXo":
                    hit = (letter, c)
                    break
            # length: until the next step with any hit
            j = i + 1
            while j < steps and not any(parts[L].replace(" ", "")[j % len(parts[L].replace(" ", ""))] in "xXo"
                                        for L in order):
                j += 1
            ln = (j - i) * step
            if hit:
                v = {"x": 100, "X": 127, "o": 60}[hit[1]]
                if v != cur_vol:
                    out.append(f"v{v} ")
                    cur_vol = v
                out.append(f"{hit[0]}%{ln} ")
            else:
                out.append(f"r%{ln} ")
            i = j
    return "".join(out)

# ---------------------------------------------------------------------------
# compile a song
# ---------------------------------------------------------------------------


def compile_song(s, instr_index, warn):
    bar = PPQ * s["beats"]
    chans = []
    lengths = []
    loops = []
    for c in s["channels"]:
        where = f"{s['ident']}/{c['name']}"
        p = Parser(c["mml"], drum=c["drum"], bar=bar, where=where).parse()
        pre = [("instr", c["instrument"]), ("vol", c["vol"]), ("gate", c["gate"])]
        if c["detune"]:
            pre.append(("detune", c["detune"]))
        events = pre + p.events
        if s["loop"] and p.loop_tick is None:
            events = pre + [("loop",)] + p.events
            p.loop_tick = 0
        lengths.append(p.tick)
        loops.append(p.loop_tick)
        chans.append((c, events, p))
    if len(set(lengths)) != 1:
        detail = ", ".join(f"{c['name']}={n}" for (c, _, _), n in zip(chans, lengths))
        raise MMLError(f"{s['ident']}: channels differ in length ({detail}; bar = {bar})")
    if s["loop"] and len(set(loops)) != 1:
        detail = ", ".join(f"{c['name']}={n}" for (c, _, _), n in zip(chans, loops))
        raise MMLError(f"{s['ident']}: loop points differ ({detail})")
    if lengths[0] % bar:
        warn(f"{s['ident']}: length is not a whole number of bars")
    if len(chans) > MAX_CHANNELS:
        raise MMLError(f"{s['ident']}: more than {MAX_CHANNELS} channels")
    num, den = tempo_ratio(s["tempo"])
    streams = []
    for c, events, p in chans:
        code, loop = assemble(events, instr_index)
        if not s["loop"]:
            loop = None
        streams.append((c["name"], code, loop))
    # melody vs chords
    if s["chords"]:
        prog = parse_prog(s["chords"], s["beats"])
        plen = prog[-1][0] + prog[-1][1]
        intro = loops[0] or 0
        for c, events, p in chans:
            if not c["check"]:
                continue
            t = 0
            for e in p.events:
                if e[0] == "rest":
                    t += e[1]
                elif e[0] == "note":
                    strong = (t % bar == 0) or (s["beats"] == 4 and t % (bar // 2) == 0)
                    if strong and e[2] >= PPQ // 2 and t >= intro:
                        pt = (t - intro) % plen
                        chord = next(ch for st, d, ch in prog if st <= pt < st + d)
                        if e[1] % 12 not in chord.pcs:
                            warn(f"{s['ident']}/{c['name']}: bar {t // bar + 1} beat {t % bar // PPQ + 1}: "
                                 f"{PC_NAMES[e[1] % 12]} over {chord.sym}")
                    t += e[2]
    return dict(ident=s["ident"], title=s["title"], num=num, den=den, streams=streams,
                ticks=lengths[0], loop_tick=loops[0] if s["loop"] else None,
                level=max(1, min(255, rnd(s["level"] * 128))), loop=s["loop"], tempo=s["tempo"],
                beats=s["beats"])
