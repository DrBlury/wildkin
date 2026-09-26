#!/usr/bin/env python3
"""Generate src/gfx_fusion.h: the RESONANCE WORKS art used by src/game/fusion.c.

  - 18 type-energy glyphs (16x16, 2x2 tiles) in three 16-colour palettes that
    serve both the UI canvas (BG banks 0..2) and sprites
  - a four-step colour ramp per type (motes, bars and the flask liquid)
  - particle tiles (8x8): dots, soft motes, orbs and sparkles, in two index
    sets (ramp A = 1..4, ramp B = 5..8) so a dual-type kin sheds two colours
  - four full-screen machine scenes for the UI canvas (240x160):
        WORKS    the hall: extractor, fusion loom, energy tanks, wall scope
        EXTRACT  the extractor dome and the big energy flask (unbinding)
        LOOM     the fusion loom and its two reels
        TUNER    the mixer's oscilloscope console (energy tuning)
    Scenes are painted with named colours and quantised per 8x8 cell onto BG
    palette banks 3..7: banks 3..6 are shared (structure, brass, heartglass,
    glass), bank 7 is the scene's own (screens, the flask liquid, the scope).
  - a 256-step sine table

Deterministic, standard library only.

    python3 tools/gen_fusion_gfx.py                 # writes src/gfx_fusion.h
    python3 tools/gen_fusion_gfx.py --preview DIR   # also writes preview PNGs
"""

import math
import os
import struct
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_H = os.path.join(ROOT, "src", "gfx_fusion.h")
sys.path.insert(0, os.path.join(ROOT, "tools"))

from gen_ui_gfx import TYPES, TYPE_COLORS  # noqa: E402  (the badge colours)

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def c15(c):
    """5-bit (r, g, b) -> RGB15."""
    return c[0] | (c[1] << 5) | (c[2] << 10)


def to5(rgb8):
    return (rgb8[0] >> 3, rgb8[1] >> 3, rgb8[2] >> 3)


def to8(c):
    return tuple((v << 3) | (v >> 2) for v in c)


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


WHITE5 = (31, 31, 31)
INK5 = (3, 3, 5)
GREY5 = (26, 26, 25)          # the UI's ink shadow (text on white paper)

BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def bayer(x, y):
    return (BAYER4[y & 3][x & 3] + 0.5) / 16.0


def write_png(path, rows):
    h = len(rows)
    w = len(rows[0])
    raw = bytearray()
    for row in rows:
        raw.append(0)
        for px in row:
            raw.extend(px)

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)


def tiles_of(idx, tw, th):
    """2D palette-index image -> list of tiles (8 u32 rows each), row-major."""
    out = []
    for ty in range(th):
        for tx in range(tw):
            t = []
            for r in range(8):
                v = 0
                for c in range(8):
                    v |= (idx[ty * 8 + r][tx * 8 + c] & 15) << (4 * c)
                t.append(v)
            out.append(t)
    return out


def hexs(v):
    return "0x%X" % v


def rows_c(words, per=8, indent="    "):
    return "\n".join(indent + ",".join(hexs(v) for v in words[i:i + per]) + ","
                     for i in range(0, len(words), per))


# --------------------------------------------------------------------------
# 1. type colours and glyph palettes
# --------------------------------------------------------------------------

def type_ramp(t):
    """glow, light, fill, dark (5-bit) for type name t."""
    fill, dark = TYPE_COLORS[t]
    return [mix(fill, WHITE5, 0.72), mix(fill, WHITE5, 0.38), fill, dark]


RAMPS = [type_ramp(t) for t in TYPES]

# three palettes of six types: 0 transparent, 1 white, 2 ink, 3 light grey,
# then (fill, dark) pairs at 4 + 2k, 5 + 2k
GLYPH_PALS = []
for g in range(3):
    pal = [(0, 0, 0), WHITE5, INK5, GREY5]
    for k in range(6):
        fill, dark = TYPE_COLORS[TYPES[g * 6 + k]]
        pal += [fill, dark]
    GLYPH_PALS.append(pal)


def lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


# --------------------------------------------------------------------------
# 2. glyph symbols (drawn in a 16x16 frame, supersampled 4x4)
# --------------------------------------------------------------------------

def seg_d(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    wx, wy = px - ax, py - ay
    L = vx * vx + vy * vy
    t = 0.0 if L == 0 else max(0.0, min(1.0, (wx * vx + wy * vy) / L))
    return math.hypot(px - (ax + vx * t), py - (ay + vy * t))


def in_poly(px, py, pts):
    inside = False
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        if (y0 > py) != (y1 > py):
            xc = x0 + (py - y0) * (x1 - x0) / (y1 - y0)
            if px < xc:
                inside = not inside
    return inside


def ell(px, py, cx, cy, rx, ry):
    return ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 <= 1.0


def sym_beast(x, y):
    if ell(x, y, 8.0, 10.2, 3.3, 2.7):
        return True
    for (cx, cy) in ((4.3, 7.0), (6.6, 4.6), (9.4, 4.6), (11.7, 7.0)):
        if ell(x, y, cx, cy, 1.35, 1.7):
            return True
    return False


def sym_blaze(x, y):
    # teardrop flame leaning right, with a small inner tongue cut out
    cx, cy, r = 8.0, 10.0, 3.9
    tip = (9.2, 2.4)
    out = math.hypot(x - cx, y - cy) <= r
    if not out and y < cy:
        t = (y - tip[1]) / (cy - tip[1])
        if 0 <= t <= 1:
            axis = tip[0] + (cx - tip[0]) * t
            out = abs(x - axis) <= r * t ** 0.9
    if not out:
        return False
    # cut: a small flame inside, near the bottom
    if math.hypot(x - 8.0, y - 11.0) <= 1.5 or (8.0 - 0.9 * (11.0 - y) / 3.0 <= x <= 8.0 + 0.3 and 7.8 <= y <= 11.0
                                                   and abs(x - 8.1) <= 1.3 * (y - 7.8) / 3.2):
        return False
    return True


def sym_tide(x, y):
    # droplet
    cx, cy, r = 8.0, 10.0, 3.9
    if math.hypot(x - cx, y - cy) <= r:
        # a bright gap for the gleam
        return not (math.hypot(x - 6.6, y - 9.6) <= 1.0)
    if y < cy and y >= 2.5:
        t = (y - 2.5) / (cy - 2.5)
        return abs(x - cx) <= r * t ** 1.3
    return False


def sym_bloom(x, y):
    # a leaf tilted 45 degrees with a midrib cut, and a short stem
    u = (x - 8.5 + y - 7.5) / math.sqrt(2)
    v = (x - 8.5 - (y - 7.5)) / math.sqrt(2)
    leaf = (u / 5.6) ** 2 + (v / 3.0) ** 2 <= 1.0
    if leaf and abs(v) < 0.45 and u > -4.2:
        return False
    stem = seg_d(x, y, 4.2, 11.8, 2.6, 13.4) <= 0.8
    return leaf or stem


def sym_spark(x, y):
    pts = [(9.8, 1.8), (4.6, 8.6), (7.9, 8.6), (6.0, 14.2), (11.6, 6.8), (8.3, 6.8), (10.4, 1.8)]
    return in_poly(x, y, pts)


def sym_frost(x, y):
    cx, cy = 8.0, 8.0
    for k in range(3):
        a = k * math.pi / 3
        ax, ay = cx + 5.6 * math.cos(a), cy + 5.6 * math.sin(a)
        bx, by = cx - 5.6 * math.cos(a), cy - 5.6 * math.sin(a)
        if seg_d(x, y, ax, ay, bx, by) <= 0.75:
            return True
        # little branches near the tips
        for s in (1, -1):
            tx, ty = cx + s * 3.6 * math.cos(a), cy + s * 3.6 * math.sin(a)
            for b in (1, -1):
                ba = a + b * math.pi / 3
                ex, ey = tx + s * 1.9 * math.cos(ba), ty + s * 1.9 * math.sin(ba)
                if seg_d(x, y, tx, ty, ex, ey) <= 0.6:
                    return True
    return False


def sym_brawl(x, y):
    # an impact burst: an eight-point star
    cx, cy = 8.0, 8.0
    a = math.atan2(y - cy, x - cx)
    d = math.hypot(x - cx, y - cy)
    r = 3.3 + 2.6 * (0.5 + 0.5 * math.cos(8 * (a + 0.2)))
    return d <= r and not d <= 1.4


def sym_venom(x, y):
    for (cx, cy, r, w) in ((6.2, 9.6, 3.4, 1.2), (11.0, 6.4, 2.2, 1.0), (10.4, 12.2, 1.4, 1.4), (5.0, 3.6, 1.2, 1.2)):
        d = math.hypot(x - cx, y - cy)
        if r - w <= d <= r:
            return True
    return False


def sym_stone(x, y):
    pts = [(3.0, 11.6), (4.2, 5.8), (8.0, 3.2), (12.2, 5.2), (13.2, 10.8), (10.2, 13.0), (5.0, 13.0)]
    if not in_poly(x, y, pts):
        return False
    # facet lines
    if seg_d(x, y, 8.0, 3.2, 7.4, 8.4) <= 0.45 or seg_d(x, y, 7.4, 8.4, 3.2, 11.0) <= 0.45 \
            or seg_d(x, y, 7.4, 8.4, 12.8, 9.2) <= 0.45:
        return False
    return True


def sym_gale(x, y):
    # three wind strokes with curls at their ends
    for (y0, x0, x1, cr) in ((4.6, 2.4, 10.0, 1.9), (8.2, 3.6, 12.2, 0.0), (11.8, 2.4, 8.8, 1.7)):
        if seg_d(x, y, x0, y0, x1, y0) <= 0.8:
            return True
        if cr:
            d = math.hypot(x - x1, y - (y0 - cr))
            if abs(d - cr) <= 0.8 and (x >= x1 - 0.2 or y < y0 - cr):
                return True
    return False


def sym_dream(x, y):
    moon = math.hypot(x - 7.0, y - 8.6) <= 5.2 and not math.hypot(x - 9.4, y - 6.8) <= 4.4
    star = False
    cx, cy = 11.8, 4.2
    if abs(x - cx) + abs(y - cy) * 0.45 <= 1.1 or abs(y - cy) + abs(x - cx) * 0.45 <= 1.1:
        star = True
    return moon or star


def sym_swarm(x, y):
    def hexa(cx, cy, r):
        dx, dy = abs(x - cx), abs(y - cy)
        return dy <= r * 0.866 and dx * 0.866 + dy * 0.5 <= r * 0.866
    return hexa(5.4, 5.8, 2.9) or hexa(10.6, 5.8, 2.9) or hexa(8.0, 10.4, 2.9)


def sym_dusk(x, y):
    # two glowing eyes in the dark
    for cx in (5.0, 11.0):
        if ell(x, y, cx, 8.2, 2.5, 1.7):
            return not (abs(x - cx) < 0.6 and abs(y - 8.2) < 1.5)
    return False


def sym_wyrm(x, y):
    # a dragon's eye: an almond with a slit pupil
    if not (abs(y - 8.0) <= 4.6 * (1 - ((x - 8.0) / 6.4) ** 2) ** 0.8 if abs(x - 8.0) < 6.4 else False):
        return False
    if abs(x - 8.0) <= 0.8 and abs(y - 8.0) <= 3.6:
        return False
    return abs(y - 8.0) >= 0 and (abs(y - 8.0) > 3.4 * (1 - ((x - 8.0) / 5.0) ** 2) ** 0.8
                                  if abs(x - 8.0) < 5.0 else True) or abs(x - 8.0) <= 2.6


def sym_hollow(x, y):
    skull = ell(x, y, 8.0, 7.0, 4.8, 4.4) or (5.2 <= x <= 10.8 and 9.0 <= y <= 12.6)
    if not skull:
        return False
    if ell(x, y, 6.0, 7.6, 1.2, 1.4) or ell(x, y, 10.0, 7.6, 1.2, 1.4):
        return False
    if abs(x - 8.0) <= 0.5 and 9.4 <= y <= 10.4:
        return False
    if y >= 11.4 and (abs(x - 6.8) < 0.4 or abs(x - 9.2) < 0.4):
        return False
    return True


def sym_relic(x, y):
    # an old key: a ring bow, a shaft and two teeth
    d = math.hypot(x - 4.6, y - 5.0)
    if 1.2 <= d <= 3.2:
        return True
    if seg_d(x, y, 6.8, 7.2, 12.6, 13.0) <= 0.9:
        return True
    if seg_d(x, y, 10.2, 10.6, 8.6, 12.2) <= 0.7 or seg_d(x, y, 12.0, 12.4, 10.6, 13.9) <= 0.7:
        return True
    return False


def sym_metal(x, y):
    cx, cy = 8.0, 8.0
    d = math.hypot(x - cx, y - cy)
    a = math.atan2(y - cy, x - cx)
    tooth = (math.cos(8 * a) > 0.25)
    r = 5.9 if tooth else 4.6
    return d <= r and d >= 1.8


def sym_astral(x, y):
    cx, cy = 7.6, 8.4
    dx, dy = abs(x - cx), abs(y - cy)
    if (dx / 1.25) ** 0.6 + (dy / 5.8) ** 0.6 <= 1.0 or (dx / 5.8) ** 0.6 + (dy / 1.25) ** 0.6 <= 1.0:
        return True
    sx, sy = 12.4, 3.6
    return abs(x - sx) + abs(y - sy) <= 1.1


SYMBOLS = {
    "BEAST": sym_beast, "BLAZE": sym_blaze, "TIDE": sym_tide, "BLOOM": sym_bloom,
    "SPARK": sym_spark, "FROST": sym_frost, "BRAWL": sym_brawl, "VENOM": sym_venom,
    "STONE": sym_stone, "GALE": sym_gale, "DREAM": sym_dream, "SWARM": sym_swarm,
    "DUSK": sym_dusk, "WYRM": sym_wyrm, "HOLLOW": sym_hollow, "RELIC": sym_relic,
    "METAL": sym_metal, "ASTRAL": sym_astral,
}


def sample(fn, x, y, ss=4):
    n = 0
    for sy in range(ss):
        for sx in range(ss):
            if fn(x + (sx + 0.5) / ss, y + (sy + 0.5) / ss):
                n += 1
    return n / (ss * ss)


def make_glyph(ti):
    """16x16 index image for type ti: a disc in the type colour with a dark
    rim and the symbol in white (dark on the palest discs)."""
    t = TYPES[ti]
    k = ti % 6
    FILL, DARK = 4 + 2 * k, 5 + 2 * k
    fill = TYPE_COLORS[t][0]
    sym_col = DARK if lum(fill) > 22.5 else 1
    img = [[0] * 16 for _ in range(16)]
    cx = cy = 8.0
    for y in range(16):
        for x in range(16):
            cover = sample(lambda px, py: math.hypot(px - cx, py - cy) <= 7.9, x, y)
            if cover < 0.5:
                continue
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            img[y][x] = DARK if d > 6.7 else FILL
    fn = SYMBOLS[t]
    for y in range(16):
        for x in range(16):
            if img[y][x] == FILL and sample(fn, x, y) >= 0.5:
                img[y][x] = sym_col
    # a small gleam at the top-left of the rim on dark symbols
    if sym_col == 1:
        for (x, y) in ((4, 3), (3, 4)):
            if img[y][x] == DARK:
                img[y][x] = FILL
    return img


# --------------------------------------------------------------------------
# 3. particles (8x8): ramp A uses indices 1..4 (glow, light, fill, dark),
#    ramp B uses 5..8
# --------------------------------------------------------------------------

def particle(kind):
    img = [[0] * 8 for _ in range(8)]
    c = 3.5
    for y in range(8):
        for x in range(8):
            dx, dy = x - c, y - c
            d = math.hypot(dx, dy)
            v = 0
            if kind == 0:      # dot
                if abs(dx) < 1 and abs(dy) < 1:
                    v = 1
                elif (abs(dx) < 1 and abs(dy) < 2) or (abs(dy) < 1 and abs(dx) < 2):
                    v = 3
            elif kind == 1:    # soft mote
                if d < 1.0:
                    v = 1
                elif d < 1.9:
                    v = 2
                elif d < 2.6:
                    v = 3
            elif kind == 2:    # orb
                if d < 1.2:
                    v = 1
                elif d < 2.2:
                    v = 2
                elif d < 3.0:
                    v = 3
                elif d < 3.6:
                    v = 4 if (x + y) & 1 else 0
            else:              # sparkle
                ax, ay = abs(dx), abs(dy)
                if d < 1.0:
                    v = 1
                elif (ax < 1 and ay < 3.6) or (ay < 1 and ax < 3.6):
                    v = 2 if max(ax, ay) < 2.2 else 3
                elif ax < 1.8 and ay < 1.8:
                    v = 3
            img[y][x] = v
    return img


PARTICLES = [particle(k) for k in range(4)]


def corner_tile():
    """Cursor corner (top-left; flip for the others): white bracket, ink edge."""
    img = [[0] * 8 for _ in range(8)]
    for y in range(8):
        for x in range(8):
            if (y < 2 and x < 7) or (x < 2 and y < 7):
                img[y][x] = 1
            elif (y < 3 and x < 8) or (x < 3 and y < 8):
                img[y][x] = 2
    return img


# --------------------------------------------------------------------------
# 4. scenes
# --------------------------------------------------------------------------

COL = {
    'white': (248, 248, 248), 'ink': (14, 12, 22),
    'void': (10, 12, 24),
    'wall_d': (22, 28, 46), 'wall': (32, 42, 66), 'wall_m': (44, 56, 84), 'wall_l': (62, 78, 108),
    'wall_hl': (90, 108, 140),
    'floor_d': (20, 18, 28), 'floor': (36, 34, 48), 'floor_m': (50, 48, 64), 'floor_l': (70, 66, 86),
    'steel_d': (66, 72, 90), 'steel': (110, 118, 138), 'steel_l': (164, 172, 190),
    'glow_wall': (66, 48, 96), 'glow_wall2': (100, 64, 124),
    'br_d': (86, 50, 24), 'br': (146, 96, 38), 'br_m': (200, 146, 58), 'br_l': (236, 198, 106),
    'br_hl': (255, 238, 186),
    'cu_d': (92, 38, 26), 'cu': (164, 78, 42), 'cu_l': (216, 130, 82),
    'hg_d': (84, 34, 108), 'hg': (152, 64, 160), 'hg_m': (214, 106, 190), 'hg_l': (246, 170, 224),
    'hg_hl': (255, 226, 248),
    'gl_d': (34, 60, 88), 'gl': (74, 124, 168), 'gl_m': (128, 182, 216), 'gl_l': (196, 230, 246),
    'tl_d': (18, 84, 88), 'tl': (36, 150, 142), 'tl_l': (110, 222, 192),
    'am_d': (160, 84, 20), 'am': (236, 160, 44), 'am_l': (255, 222, 122),
    'scr_d': (8, 30, 24), 'scr': (22, 72, 50), 'scr_l': (96, 228, 144),
    'red': (224, 60, 52), 'red_d': (120, 26, 32),
    # the extractor flask (bank 7 of EXTRACT; liquid slots are loaded at run time)
    'fl_in': (22, 28, 48),
    'liqA_l': (255, 200, 150), 'liqA': (240, 120, 60), 'liqA_d': (150, 56, 24),
    'liqB_l': (200, 150, 255), 'liqB': (120, 80, 220), 'liqB_d': (60, 30, 120),
    # the tuner scope (bank 7 of TUNER)
    'crt_bg': (8, 26, 22), 'crt_grid': (18, 54, 42), 'crt_grid_l': (34, 86, 64),
    'wave_t': (250, 178, 60), 'wave_t_d': (122, 84, 32), 'wave_p': (126, 250, 164),
    'wave_p_d': (40, 122, 82), 'meter_bg': (30, 22, 44), 'meter': (214, 106, 190),
    'meter_l': (255, 200, 240),
}

BANK_STRUCT = ['white', 'ink', 'void', 'wall_d', 'wall', 'wall_m', 'wall_l', 'wall_hl', 'floor_d',
               'floor', 'floor_m', 'floor_l', 'steel_d', 'steel', 'steel_l']
BANK_BRASS = ['white', 'ink', 'br_d', 'br', 'br_m', 'br_l', 'br_hl', 'cu_d', 'cu', 'cu_l', 'wall_d',
              'wall', 'wall_m', 'floor_d', 'steel_d']
BANK_HEART = ['white', 'ink', 'hg_d', 'hg', 'hg_m', 'hg_l', 'hg_hl', 'br_d', 'br', 'br_m', 'br_l',
              'wall_d', 'wall', 'glow_wall', 'glow_wall2']
BANK_GLASS = ['white', 'ink', 'gl_d', 'gl', 'gl_m', 'gl_l', 'tl_d', 'tl', 'tl_l', 'am_d', 'am', 'am_l',
              'wall_d', 'wall', 'steel']
BANK7 = {
    'WORKS': ['white', 'ink', 'scr_d', 'scr', 'scr_l', 'red', 'red_d', 'steel_d', 'steel', 'steel_l',
              'wall_d', 'wall', 'floor_d', 'floor', 'cu'],
    # indices 10..15 = liquid A (light, fill, dark) and B, replaced at run time
    'EXTRACT': ['white', 'ink', 'fl_in', 'gl_d', 'gl', 'gl_l', 'br_d', 'br_m', 'wall_d',
                'liqA_l', 'liqA', 'liqA_d', 'liqB_l', 'liqB', 'liqB_d'],
    'LOOM': ['white', 'ink', 'scr_d', 'scr', 'scr_l', 'red', 'red_d', 'steel_d', 'steel', 'steel_l',
             'wall_d', 'wall', 'cu_d', 'cu', 'cu_l'],
    'TUNER': ['white', 'ink', 'crt_bg', 'crt_grid', 'crt_grid_l', 'wave_t', 'wave_t_d', 'wave_p',
              'wave_p_d', 'meter_bg', 'meter', 'meter_l', 'steel_d', 'steel', 'steel_l'],
}
SCENE_NAMES = ['WORKS', 'EXTRACT', 'LOOM', 'TUNER']


class Pic:
    """A 240x160 picture of colour names (None = transparent)."""

    def __init__(self, w=240, h=160, fill='void'):
        self.w, self.h = w, h
        self.p = [[fill] * w for _ in range(h)]
        self.force = {}           # (cx, cy) -> forced bank index 0..4

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.p[y][x]
        return None

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            for x in range(max(0, x0), min(self.w, x1 + 1)):
                self.p[y][x] = c

    def dith(self, x, y, c0, c1, t):
        """Ordered dither: t in 0..1 blends from c0 to c1."""
        self.set(x, y, c1 if bayer(x, y) < t else c0)

    def ramp_at(self, x, y, ramp, v):
        """v in 0..1 over a list of colours (dithered between steps)."""
        v = max(0.0, min(0.999, v)) * (len(ramp) - 1)
        i = int(v)
        f = v - i
        self.set(x, y, ramp[i + 1] if i + 1 < len(ramp) and bayer(x, y) < f else ramp[i])

    def fn(self, x0, y0, x1, y1, f):
        """f(x, y) -> colour or False (leave) for every pixel of a box."""
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            for x in range(max(0, x0), min(self.w, x1 + 1)):
                c = f(x, y)
                if c is not False:
                    self.p[y][x] = c

    def outline(self, x0, y0, x1, y1, inside, col='ink'):
        """Paint col on pixels outside `inside` that touch it (4-neighbours)."""
        pts = []
        for y in range(y0 - 1, y1 + 2):
            for x in range(x0 - 1, x1 + 2):
                if inside(x, y):
                    continue
                if inside(x + 1, y) or inside(x - 1, y) or inside(x, y + 1) or inside(x, y - 1):
                    pts.append((x, y))
        for (x, y) in pts:
            self.set(x, y, col)

    def force_bank(self, x0, y0, x1, y1, bank):
        for cy in range(y0 // 8, y1 // 8 + 1):
            for cx in range(x0 // 8, x1 // 8 + 1):
                self.force[(cx, cy)] = bank


def cyl_level(x, x0, x1, light=0.3):
    """Horizontal cylinder shading: 0 dark .. 1 bright, highlight left of centre."""
    u = (x + 0.5 - x0) / max(1.0, (x1 + 1 - x0))
    return max(0.0, 1.0 - abs(u - light) * 1.9)


BRASS = ['br_d', 'br', 'br_m', 'br_l', 'br_hl']
COPPER = ['cu_d', 'cu', 'cu_l']
HEART = ['hg_d', 'hg', 'hg_m', 'hg_l', 'hg_hl']
GLASS = ['gl_d', 'gl', 'gl_m', 'gl_l']
STEEL = ['steel_d', 'steel', 'steel_l']


def paint_wall(P, y0=0, y1=111, panel=48, off=0):
    """Riveted slate panels, darker toward the ceiling, with a title band."""
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, (y1 - y0))
        for x in range(P.w):
            P.ramp_at(x, y, ['wall_d', 'wall', 'wall_m'], 0.15 + 0.75 * t)
    for x0 in range(off, P.w, panel):
        for y in range(y0 + 16, y1 + 1):
            P.set(x0, y, 'wall_d')
            P.set(x0 + 1, y, 'wall_l')
        for y in range(y0 + 22, y1 - 2, 14):
            for (dx, c) in ((-4, None), (5, None)):
                rx = x0 + dx
                P.set(rx, y, 'wall_hl')
                P.set(rx + 1, y, 'wall_l')
                P.set(rx, y + 1, 'wall_l')
                P.set(rx + 1, y + 1, 'wall_d')
    # wainscot rail
    for x in range(P.w):
        P.set(x, y1 - 12, 'wall_l')
        P.set(x, y1 - 11, 'wall_d')
    # title band and its brass trim
    P.rect(0, 0, P.w - 1, 13, 'void')
    for x in range(P.w):
        P.set(x, 14, 'br_m' if x % 16 else 'br_l')
        P.set(x, 15, 'br_d')
        P.set(x, 16, 'ink')


def paint_floor(P, y0=112, y1=159):
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, (y1 - y0))
        for x in range(P.w):
            P.ramp_at(x, y, ['floor_d', 'floor', 'floor_m'], 0.25 + 0.6 * t)
    # skirting
    for x in range(P.w):
        P.set(x, y0, 'ink')
        P.set(x, y0 + 1, 'steel_d')
        P.set(x, y0 + 2, 'floor_d')
    # tile seams with perspective spacing
    ys = [y0 + 8, y0 + 18, y0 + 30, y0 + 44]
    for y in ys:
        if y <= y1:
            for x in range(P.w):
                P.set(x, y, 'floor_d')
                if y + 1 <= y1:
                    P.set(x, y + 1, 'floor_l' if x % 3 else 'floor_m')
    cx = P.w / 2
    for k in range(-8, 9):
        for y in range(y0 + 3, y1 + 1):
            t = (y - y0) / max(1, (y1 - y0))
            x = int(round(cx + k * (18 + 26 * t)))
            P.set(x, y, 'floor_d')


def paint_pipe_h(P, x0, x1, y0, h=6, flange_every=56, ramp=COPPER):
    for x in range(x0, x1 + 1):
        for y in range(y0, y0 + h):
            v = 1.0 - abs((y + 0.5 - y0) / h - 0.3) * 1.8
            P.ramp_at(x, y, ramp, v)
        P.set(x, y0 - 1, 'ink')
        P.set(x, y0 + h, 'ink')
    for fx in range(x0 + 10, x1, flange_every):
        for x in range(fx, fx + 4):
            for y in range(y0 - 2, y0 + h + 2):
                v = 1.0 - abs((y + 0.5 - y0 + 2) / (h + 4) - 0.3) * 1.8
                P.ramp_at(x, y, BRASS, v * 0.9)
            P.set(x, y0 - 3, 'ink')
            P.set(x, y0 + h + 2, 'ink')
        for y in range(y0 - 2, y0 + h + 2):
            P.set(fx - 1, y, 'ink')
            P.set(fx + 4, y, 'ink')


def paint_pipe_v(P, x0, y0, y1, w=6, ramp=COPPER):
    for y in range(y0, y1 + 1):
        for x in range(x0, x0 + w):
            P.ramp_at(x, y, ramp, cyl_level(x, x0, x0 + w - 1))
        P.set(x0 - 1, y, 'ink')
        P.set(x0 + w, y, 'ink')


def paint_rivet(P, x, y):
    P.set(x, y, 'br_hl')
    P.set(x + 1, y, 'br_m')
    P.set(x, y + 1, 'br_m')
    P.set(x + 1, y + 1, 'br_d')


def paint_brass_box(P, x0, y0, x1, y1, rivets=True):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            v = cyl_level(x, x0, x1, 0.35) * 0.85 + (0.12 if y == y0 + 1 else 0.0)
            P.ramp_at(x, y, BRASS[:4], v)
    for x in range(x0, x1 + 1):
        P.set(x, y0, 'br_l')
        P.set(x, y1, 'br_d')
    P.outline(x0, y0, x1, y1, lambda x, y: x0 <= x <= x1 and y0 <= y <= y1)
    if rivets:
        for x in range(x0 + 3, x1 - 2, 10):
            paint_rivet(P, x, y0 + 3)
            paint_rivet(P, x, y1 - 4)


def paint_glow(P, cx, cy, r, table):
    """Recolour wall pixels around (cx, cy) toward a glow (dithered)."""
    for y in range(max(0, cy - r), min(P.h, cy + r + 1)):
        for x in range(max(0, cx - r), min(P.w, cx + r + 1)):
            d = math.hypot(x - cx, (y - cy) * 1.1) / r
            if d >= 1:
                continue
            c = P.p[y][x]
            if c not in table:
                continue
            t = (1 - d) ** 1.3
            steps = table[c]
            k = t * len(steps)
            i = int(k)
            if i >= len(steps):
                i = len(steps) - 1
            if bayer(x, y) < k - int(k) and i + 1 < len(steps):
                i += 1
            if i > 0:
                P.p[y][x] = steps[i - 1] if i - 1 < len(steps) else steps[-1]


GLOW_TABLE = {
    'wall_d': ['wall', 'glow_wall', 'glow_wall2'],
    'wall': ['glow_wall', 'glow_wall', 'glow_wall2'],
    'wall_m': ['glow_wall', 'glow_wall2', 'glow_wall2'],
    'wall_l': ['glow_wall2', 'glow_wall2', 'hg'],
    'wall_hl': ['glow_wall2', 'hg', 'hg'],
}


def paint_loom(P, cx, cy, ro, ri, lens_r, sockets=True):
    """The FUSION LOOM ring: brass ring shaded from the top-left, rivets,
    socket mounts, and the heartglass lens with concentric mode rings."""
    L = (-0.6, -0.8)
    for y in range(cy - ro - 2, cy + ro + 3):
        for x in range(cx - ro - 2, cx + ro + 3):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if ri <= d <= ro:
                nx, ny = dx / max(d, 0.01), dy / max(d, 0.01)
                # a ring shaded like a torus: outer half faces out, inner half in
                m = (d - ri) / (ro - ri)
                facing = (nx * L[0] + ny * L[1]) * (1 if m > 0.5 else -1)
                v = 0.45 + 0.42 * facing + 0.18 * (1 - abs(m - 0.5) * 2)
                P.ramp_at(x, y, BRASS, v)
            elif lens_r < d < ri:
                P.set(x, y, 'ink' if d > ri - 1.2 else 'br_d')
            elif d <= lens_r:
                t = d / lens_r
                # radial heartglass: bright core, mode rings
                v = 1.0 - t ** 0.8
                ring = abs(math.sin(t * math.pi * 3.0))
                if ring < 0.18 and t > 0.2:
                    v -= 0.35
                spec = math.hypot(dx + lens_r * 0.42, dy + lens_r * 0.42) / lens_r
                if spec < 0.22:
                    v = 1.0
                P.ramp_at(x, y, HEART, max(0.0, v))
    P.outline(cx - ro - 1, cy - ro - 1, cx + ro + 1, cy + ro + 1,
              lambda x, y: math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= ro)
    # rivets around the ring
    for k in range(12):
        a = k * math.pi / 6 + math.pi / 12
        rr = (ro + ri) / 2
        x, y = int(round(cx + rr * math.cos(a) - 0.5)), int(round(cy + rr * math.sin(a) - 0.5))
        paint_rivet(P, x, y)
    if sockets:
        for a in SOCKET_ANGLES:
            sx = int(round(cx + (ro + 1) * math.cos(math.radians(a))))
            sy = int(round(cy + (ro + 1) * math.sin(math.radians(a))))
            for y in range(sy - 6, sy + 7):
                for x in range(sx - 6, sx + 7):
                    d = math.hypot(x + 0.5 - sx, y + 0.5 - sy)
                    if d <= 6.4:
                        P.ramp_at(x, y, BRASS, 0.2 + 0.6 * (1 - d / 6.4) - 0.2 * ((y - sy) / 6.0))
                    if d <= 3.8:
                        P.set(x, y, 'ink' if d > 3.0 else 'hg_d')
            P.outline(sx - 7, sy - 7, sx + 7, sy + 7, lambda x, y: math.hypot(x + 0.5 - sx, y + 0.5 - sy) <= 6.4)


SOCKET_ANGLES = (-90, 150, 30)


def paint_dome(P, cx, cy, r, base_y, hollow):
    """A glass bell jar. hollow: the inside stays transparent (a sprite behind
    the canvas shows through), else it is dark glass."""
    def inside(x, y):
        return math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r and y < base_y
    for y in range(cy - r, base_y):
        for x in range(cx - r, cx + r + 1):
            if not inside(x, y):
                continue
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            a = math.degrees(math.atan2(y + 0.5 - cy, x + 0.5 - cx))
            if d > r - 1.5:
                P.set(x, y, 'gl')
            elif d > r - 2.6 and (-170 < a < -95):
                P.set(x, y, 'gl_l')
            elif r * 0.72 < d < r * 0.82 and -160 < a < -120:
                P.set(x, y, 'white' if -150 < a < -130 else 'gl_l')
            elif r * 0.80 < d < r * 0.88 and 10 < a < 40:
                P.set(x, y, 'gl_m')
            elif hollow:
                P.set(x, y, None)
            else:
                v = 0.15 + 0.25 * (1 - d / r)
                P.ramp_at(x, y, ['wall_d', 'gl_d', 'gl'], v)
    P.outline(cx - r - 1, cy - r - 1, cx + r + 1, base_y, inside)


def paint_flask_shape(cx, neck_w, neck_y0, bulb_cy, bulb_r):
    def inside(x, y):
        px, py = x + 0.5, y + 0.5
        if math.hypot(px - cx, py - bulb_cy) <= bulb_r:
            return True
        return neck_y0 <= py <= bulb_cy and abs(px - cx) <= neck_w / 2
    return inside


def quantise(P, bank7, forced_note=''):
    """Pick one bank per 8x8 cell. Returns (idx image, bank per cell, pals, misses)."""
    banks = [BANK_STRUCT, BANK_BRASS, BANK_HEART, BANK_GLASS, BANK7[bank7]]
    for b in banks:
        assert len(b) <= 15 and b[0] == 'white' and b[1] == 'ink', b
    pal5 = [[to5(COL[n]) for n in b] for b in banks]
    idx = [[0] * P.w for _ in range(P.h)]
    cell_bank = [[0] * (P.w // 8) for _ in range(P.h // 8)]
    misses = 0
    for cy in range(P.h // 8):
        for cx in range(P.w // 8):
            names = set()
            for y in range(cy * 8, cy * 8 + 8):
                for x in range(cx * 8, cx * 8 + 8):
                    if P.p[y][x] is not None:
                        names.add(P.p[y][x])
            forced = P.force.get((cx, cy))
            choice = None
            if forced is not None:
                choice = forced
            else:
                for bi, b in enumerate(banks):
                    if names <= set(b):
                        choice = bi
                        break
            if choice is None:
                best, choice = None, 0
                for bi in range(len(banks)):
                    err = 0
                    for n in names:
                        c = to5(COL[n])
                        err += min(sum((c[i] - q[i]) ** 2 for i in range(3)) for q in pal5[bi])
                    if best is None or err < best:
                        best, choice = err, bi
            b = banks[choice]
            for y in range(cy * 8, cy * 8 + 8):
                for x in range(cx * 8, cx * 8 + 8):
                    n = P.p[y][x]
                    if n is None:
                        idx[y][x] = 0
                    elif n in b:
                        idx[y][x] = 1 + b.index(n)
                    else:
                        misses += 1
                        c = to5(COL[n])
                        k = min(range(len(b)), key=lambda i: sum((c[j] - pal5[choice][i][j]) ** 2 for j in range(3)))
                        idx[y][x] = 1 + k
            cell_bank[cy][cx] = choice
    pals = [[(0, 0, 0)] + p + [(0, 0, 0)] * (15 - len(p)) for p in pal5]
    return idx, cell_bank, pals, misses


def pack_scene(idx, cell_bank):
    tiles, lookup, mp = [], {}, []
    for cy in range(20):
        for cx in range(30):
            t = []
            for r in range(8):
                v = 0
                for c in range(8):
                    v |= (idx[cy * 8 + r][cx * 8 + c] & 15) << (4 * c)
                t.append(v)
            key = tuple(t)
            if key not in lookup:
                lookup[key] = len(tiles)
                tiles.append(t)
            mp.append(lookup[key] | ((3 + cell_bank[cy][cx]) << 12))
    return tiles, mp


# ---------------------------------------------------------------- the scenes

GEOM = {}


def scene_works():
    P = Pic()
    paint_wall(P, 0, 111, panel=48, off=20)
    paint_floor(P, 112, 159)
    paint_pipe_h(P, 0, 239, 20, h=5)
    # loom in the middle, glowing on the wall
    lcx, lcy = 100, 62
    paint_glow(P, lcx, lcy, 58, GLOW_TABLE)
    # supports and base
    for (ax, bx) in ((lcx - 20, lcx - 26), (lcx + 20, lcx + 26)):
        for y in range(lcy + 20, 104):
            t = (y - lcy - 20) / (104 - lcy - 20)
            x0 = int(round(ax + (bx - ax) * t)) - 3
            for x in range(x0, x0 + 6):
                P.ramp_at(x, y, BRASS[:4], cyl_level(x, x0, x0 + 5))
            P.set(x0 - 1, y, 'ink')
            P.set(x0 + 6, y, 'ink')
    paint_loom(P, lcx, lcy, 32, 24, 22)
    paint_brass_box(P, lcx - 34, 100, lcx + 34, 114)
    for x in range(lcx - 26, lcx + 27, 13):
        P.rect(x, 105, x + 5, 108, 'ink')
        P.rect(x + 1, 106, x + 4, 107, 'hg_m')
    GEOM['WORKS_LOOM'] = (lcx, lcy)
    # the extractor on the left
    ecx, ecy = 30, 70
    paint_pipe_v(P, ecx - 3, 26, 46)
    paint_dome(P, ecx, ecy, 20, 88, hollow=False)
    for y in range(44, 52):
        for x in range(ecx - 11, ecx + 12):
            if ((x + 0.5 - ecx) / 11.5) ** 2 + ((y + 0.5 - 52) / 8.0) ** 2 <= 1:
                P.ramp_at(x, y, BRASS, 0.3 + 0.6 * cyl_level(x, ecx - 11, ecx + 11))
    P.outline(ecx - 12, 43, ecx + 12, 52,
              lambda x, y: y < 52 and ((x + 0.5 - ecx) / 11.5) ** 2 + ((y + 0.5 - 52) / 8.0) ** 2 <= 1)
    paint_brass_box(P, ecx - 22, 88, ecx + 22, 114)
    P.rect(ecx - 4, 96, ecx + 3, 103, 'ink')
    P.rect(ecx - 3, 97, ecx + 2, 102, 'red_d')
    P.rect(ecx - 2, 98, ecx, 100, 'red')
    GEOM['WORKS_DOME'] = (ecx, ecy)
    # energy tanks on the right
    for (tx, liq, lvl) in ((140, ['tl_d', 'tl', 'tl_l'], 0.62), (156, ['am_d', 'am', 'am_l'], 0.8)):
        top, bot = 50, 104
        for y in range(top, bot + 1):
            for x in range(tx, tx + 12):
                fill_y = bot - int((bot - top) * lvl)
                if y >= fill_y:
                    P.ramp_at(x, y, liq, 0.2 + 0.8 * cyl_level(x, tx, tx + 11))
                    if y == fill_y:
                        P.set(x, y, liq[2])
                else:
                    P.ramp_at(x, y, ['wall_d', 'gl_d', 'gl'], 0.1 + 0.5 * cyl_level(x, tx, tx + 11))
            P.set(tx + 2, y, 'gl_l' if y % 9 else 'white')
        P.outline(tx, top, tx + 11, bot, lambda x, y: tx <= x <= tx + 11 and top <= y <= bot)
        paint_brass_box(P, tx - 2, top - 6, tx + 13, top - 1, rivets=False)
        paint_brass_box(P, tx - 2, bot + 1, tx + 13, 112, rivets=False)
        GEOM.setdefault('WORKS_TANKS', []).append((tx, top, bot, lvl))
    # a wall scope above the tanks (the mixer's little brother)
    sx0, sy0, sx1, sy1 = 136, 26, 171, 42
    P.rect(sx0 - 2, sy0 - 2, sx1 + 2, sy1 + 2, 'steel')
    P.rect(sx0 - 2, sy1 + 2, sx1 + 2, sy1 + 2, 'steel_d')
    P.outline(sx0 - 2, sy0 - 2, sx1 + 2, sy1 + 2, lambda x, y: sx0 - 2 <= x <= sx1 + 2 and sy0 - 2 <= y <= sy1 + 2)
    P.rect(sx0, sy0, sx1, sy1, 'scr_d')
    for x in range(sx0, sx1 + 1):
        for y in range(sy0, sy1 + 1):
            if (x - sx0) % 6 == 0 or (y - sy0) % 6 == 0:
                P.set(x, y, 'scr')
        yy = int(round((sy0 + sy1) / 2 + 5 * math.sin((x - sx0) / 5.0)))
        P.set(x, yy, 'scr_l')
    # a hanging lamp and cables
    for (lx, ly) in ((64, 30), (180, 30)):
        for y in range(26, ly):
            P.set(lx, y, 'ink')
        for y in range(ly, ly + 5):
            for x in range(lx - 4, lx + 5):
                if abs(x - lx) <= (y - ly) + 1:
                    P.ramp_at(x, y, BRASS, 0.5 + 0.1 * (lx - x) / 4)
        P.rect(lx - 2, ly + 5, lx + 2, ly + 6, 'br_hl')
    return P


def scene_extract():
    P = Pic()
    paint_wall(P, 0, 111, panel=56, off=8)
    paint_floor(P, 112, 159)
    # a dark niche for the flask
    nx0, ny0, nx1, ny1 = 142, 20, 226, 111
    P.rect(nx0, ny0, nx1, ny1, 'wall_d')
    for y in range(ny0, ny1 + 1):
        P.set(nx0 - 1, y, 'steel')
        P.set(nx0 - 2, y, 'steel_l')
        P.set(nx1 + 1, y, 'steel_d')
    for x in range(nx0 - 2, nx1 + 2):
        P.set(x, ny0 - 1, 'steel_l')
        P.set(x, ny0 - 2, 'steel')
    # the flask
    fcx, neck_w, neck_y0, bcy, br = 184, 16, 24, 76, 32
    inside = paint_flask_shape(fcx, neck_w, neck_y0, bcy, br)
    inner = paint_flask_shape(fcx, neck_w - 4, neck_y0 + 2, bcy, br - 2)
    for y in range(neck_y0 - 2, bcy + br + 2):
        for x in range(fcx - br - 2, fcx + br + 3):
            if inner(x, y):
                P.set(x, y, 'fl_in')
            elif inside(x, y):
                a = math.degrees(math.atan2(y + 0.5 - bcy, x + 0.5 - fcx))
                P.set(x, y, 'gl_l' if (-170 < a < -100 and y > neck_y0 + 10) else 'gl')
    P.outline(fcx - br - 2, neck_y0 - 2, fcx + br + 2, bcy + br + 2, inside)
    # lip
    for y in range(neck_y0 - 5, neck_y0):
        for x in range(fcx - neck_w // 2 - 3, fcx + neck_w // 2 + 3):
            P.set(x, y, 'gl_l' if y == neck_y0 - 5 else 'gl')
    P.outline(fcx - 12, neck_y0 - 6, fcx + 12, neck_y0,
              lambda x, y: neck_y0 - 5 <= y < neck_y0 and fcx - neck_w // 2 - 3 <= x < fcx + neck_w // 2 + 3)
    # flask interior spans (for the liquid)
    spans = []
    fy0 = None
    for y in range(neck_y0, bcy + br):
        xs = [x for x in range(fcx - br, fcx + br + 1) if inner(x, y)]
        if xs:
            if fy0 is None:
                fy0 = y
            spans.append((min(xs), max(xs)))
    GEOM['FLASK'] = (fy0, spans)
    for i, (a, b) in enumerate(spans):
        P.force_bank(a, fy0 + i, b, fy0 + i, 4)
    # the stand under the flask
    paint_brass_box(P, fcx - 26, 106, fcx + 26, 116)
    # the dome and its pedestal
    dcx, dcy, dr = 56, 60, 34
    paint_dome(P, dcx, dcy, dr, 90, hollow=True)
    for y in range(18, 30):
        for x in range(dcx - 16, dcx + 17):
            if ((x + 0.5 - dcx) / 16.5) ** 2 + ((y + 0.5 - 30) / 11.0) ** 2 <= 1:
                P.ramp_at(x, y, BRASS, 0.25 + 0.7 * cyl_level(x, dcx - 16, dcx + 16))
    P.outline(dcx - 17, 17, dcx + 17, 30,
              lambda x, y: y < 30 and ((x + 0.5 - dcx) / 16.5) ** 2 + ((y + 0.5 - 30) / 11.0) ** 2 <= 1)
    for (rx, ry) in ((dcx - 10, 24), (dcx + 8, 24), (dcx - 1, 21)):
        paint_rivet(P, rx, ry)
    # the pipe from the cap across to the flask mouth
    paint_pipe_v(P, dcx - 3, 7, 18)
    paint_pipe_h(P, dcx - 4, fcx + 4, 3, h=5, flange_every=48)
    paint_pipe_v(P, fcx - 3, 9, neck_y0 - 7, ramp=COPPER)
    for x in range(fcx - 5, fcx + 6):
        P.set(x, neck_y0 - 7, 'br_m')
        P.set(x, neck_y0 - 6, 'br_d')
    paint_brass_box(P, dcx - 40, 88, dcx + 40, 116)
    # gauge
    gx, gy = dcx + 22, 101
    for y in range(gy - 7, gy + 8):
        for x in range(gx - 7, gx + 8):
            d = math.hypot(x + 0.5 - gx, y + 0.5 - gy)
            if d <= 7:
                P.set(x, y, 'ink' if d > 6 else ('steel_l' if d < 5 else 'steel'))
    for k in range(5):
        a = math.radians(200 + k * 35)
        P.set(int(gx + 4.5 * math.cos(a)), int(gy + 4.5 * math.sin(a)), 'ink')
    for i in range(5):
        P.set(gx - 1 + i // 2, gy - i, 'red')
    P.rect(dcx - 30, 97, dcx - 22, 105, 'ink')
    P.rect(dcx - 29, 98, dcx - 23, 104, 'red_d')
    P.rect(dcx - 28, 99, dcx - 26, 101, 'red')
    GEOM['DOME'] = (dcx, dcy, dr)
    GEOM['FLASK_MOUTH'] = (fcx, neck_y0 - 4)
    return P


def scene_loom():
    P = Pic()
    paint_wall(P, 0, 111, panel=40, off=0)
    paint_floor(P, 112, 159)
    lcx, lcy = 120, 42
    paint_glow(P, lcx, lcy, 56, GLOW_TABLE)
    paint_pipe_h(P, 0, 239, 20, h=5)
    # arms to the base
    for (ax, bx) in ((lcx - 22, lcx - 30), (lcx + 22, lcx + 30)):
        for y in range(lcy + 18, 80):
            t = (y - lcy - 18) / (80 - lcy - 18)
            x0 = int(round(ax + (bx - ax) * t)) - 3
            for x in range(x0, x0 + 6):
                P.ramp_at(x, y, BRASS[:4], cyl_level(x, x0, x0 + 5))
            P.set(x0 - 1, y, 'ink')
            P.set(x0 + 6, y, 'ink')
    paint_loom(P, lcx, lcy, 34, 26, 24)
    # the base with the reel windows
    bx0, by0, bx1, by1 = lcx - 40, 76, lcx + 40, 104
    paint_brass_box(P, bx0, by0, bx1, by1, rivets=False)
    reels = []
    for rx in (lcx - 23, lcx + 3):
        x0, y0 = rx, 80
        P.rect(x0 - 2, y0 - 2, x0 + 21, y0 + 21, 'ink')
        P.rect(x0 - 1, y0 - 1, x0 + 20, y0 + 20, 'br_d')
        P.rect(x0, y0, x0 + 19, y0 + 19, None)
        reels.append((x0, y0))
    for (rx, ry) in ((bx0 + 4, by0 + 4), (bx1 - 5, by0 + 4), (bx0 + 4, by1 - 5), (bx1 - 5, by1 - 5)):
        paint_rivet(P, rx, ry)
    # lamps between the reels
    P.rect(lcx - 2, 86, lcx + 1, 93, 'ink')
    P.rect(lcx - 1, 87, lcx, 92, 'red')
    GEOM['LOOM'] = (lcx, lcy)
    GEOM['REELS'] = reels
    # cables
    for (x0, dirn) in ((bx0 - 2, -1), (bx1 + 2, 1)):
        for k in range(26):
            x = x0 + dirn * k
            y = 104 + int(round(4 * math.sin(k / 26.0 * math.pi)))
            P.set(x, y, 'ink')
            P.set(x, y + 1, 'cu_d')
    return P


def scene_tuner():
    P = Pic()
    paint_wall(P, 0, 111, panel=64, off=30)
    paint_floor(P, 112, 159)
    # console body
    cx0, cy0, cx1, cy1 = 4, 20, 235, 118
    for y in range(cy0, cy1 + 1):
        for x in range(cx0, cx1 + 1):
            v = 0.35 + 0.35 * (1 - (y - cy0) / (cy1 - cy0))
            P.ramp_at(x, y, STEEL, v)
    P.outline(cx0, cy0, cx1, cy1, lambda x, y: cx0 <= x <= cx1 and cy0 <= y <= cy1)
    for x in range(cx0, cx1 + 1):
        P.set(x, cy0, 'steel_l')
        P.set(x, cy1, 'steel_d')
    for (rx, ry) in ((cx0 + 3, cy0 + 3), (cx1 - 4, cy0 + 3), (cx0 + 3, cy1 - 4), (cx1 - 4, cy1 - 4)):
        P.set(rx, ry, 'white')
        P.set(rx + 1, ry + 1, 'steel_d')
    # the scope screen (drawn by the game)
    sx0, sy0, sx1, sy1 = 16, 32, 183, 95
    P.rect(sx0 - 4, sy0 - 4, sx1 + 4, sy1 + 4, 'ink')
    P.rect(sx0 - 3, sy0 - 3, sx1 + 3, sy1 + 3, 'steel_d')
    P.rect(sx0, sy0, sx1, sy1, 'crt_bg')
    P.force_bank(sx0, sy0, sx1, sy1, 4)
    GEOM['CRT'] = (sx0, sy0, sx1 - sx0 + 1, sy1 - sy0 + 1)
    # the timer bar above the screen
    tx0, ty0, tx1, ty1 = 16, 24, 183, 27
    P.rect(tx0 - 1, ty0 - 1, tx1 + 1, ty1 + 1, 'ink')
    P.rect(tx0, ty0, tx1, ty1, 'meter_bg')
    P.force_bank(tx0, ty0, tx1, ty1, 4)
    GEOM['TIMER'] = (tx0, ty0, tx1 - tx0 + 1, ty1 - ty0 + 1)
    # the resonance meter tube
    mx0, my0, mx1, my1 = 200, 32, 215, 95
    P.rect(mx0 - 3, my0 - 3, mx1 + 3, my1 + 3, 'ink')
    P.rect(mx0 - 2, my0 - 2, mx1 + 2, my1 + 2, 'steel_d')
    P.rect(mx0, my0, mx1, my1, 'meter_bg')
    P.force_bank(mx0, my0, mx1, my1, 4)
    GEOM['METER'] = (mx0, my0, mx1 - mx0 + 1, my1 - my0 + 1)
    for (y0, y1) in ((my0 - 8, my0 - 4), (my1 + 4, my1 + 8)):
        paint_brass_box(P, mx0 - 4, y0, mx1 + 4, y1, rivets=False)
    # knobs (FREQ, AMP) and a toggle row
    knobs = []
    for kx in (48, 136):
        ky = 108
        for y in range(ky - 10, ky + 11):
            for x in range(kx - 10, kx + 11):
                d = math.hypot(x + 0.5 - kx, y + 0.5 - ky)
                if d <= 10:
                    a = math.atan2(y + 0.5 - ky, x + 0.5 - kx)
                    ridge = d > 8.2 and int((a + math.pi) / (2 * math.pi) * 24) % 2 == 0
                    v = 0.55 - 0.35 * ((x - kx) + (y - ky)) / 14.0 - (0.25 if ridge else 0)
                    P.ramp_at(x, y, BRASS, v)
        P.outline(kx - 11, ky - 11, kx + 11, ky + 11, lambda x, y: math.hypot(x + 0.5 - kx, y + 0.5 - ky) <= 10)
        knobs.append((kx, ky))
    GEOM['KNOBS'] = knobs
    return P


# --------------------------------------------------------------------------
# 5. the header
# --------------------------------------------------------------------------

def main():
    preview = None
    if "--preview" in sys.argv:
        preview = sys.argv[sys.argv.index("--preview") + 1]
        os.makedirs(preview, exist_ok=True)
    out = []
    w = out.append
    w("/*")
    w(" * RESONANCE WORKS art (src/game/fusion.c). GENERATED by tools/gen_fusion_gfx.py")
    w(" * -- do not edit. GBA 4bpp tiles: 8 u32 per 8x8 tile, multi-tile images in")
    w(" * row-major tile order. Colours are RGB15.")
    w(" */")
    w("#ifndef GFX_FUSION_H")
    w("#define GFX_FUSION_H")
    w("#define GFX_FUSION_UNUSED __attribute__((unused))")
    w("")

    glyphs = [make_glyph(i) for i in range(len(TYPES))]
    w("/* Type-energy glyphs, 16x16 (2x2 tiles), one per type in data.h order.")
    w(" * Palette fz_glyph_pal[t / 6]: 0 transparent, 1 white, 2 ink, 3 light grey,")
    w(" * then the type's fill at 4 + 2 * (t % 6) and its dark at 5 + 2 * (t % 6). */")
    w("static const u32 fz_glyph_gfx[%d][4 * 8] GFX_FUSION_UNUSED = {" % len(TYPES))
    for t, img in zip(TYPES, glyphs):
        words = [v for tl in tiles_of(img, 2, 2) for v in tl]
        w("    { /* %s */" % t)
        w(rows_c(words, 8, "        "))
        w("    },")
    w("};")
    w("static const u16 fz_glyph_pal[3][16] GFX_FUSION_UNUSED = {")
    for p in GLYPH_PALS:
        w("    {" + ",".join(hexs(c15(c)) for c in p) + "},")
    w("};")
    w("/* Per type: glow, light, fill, dark. */")
    w("static const u16 fz_type_ramp[%d][4] GFX_FUSION_UNUSED = {" % len(TYPES))
    for t, r in zip(TYPES, RAMPS):
        w("    {" + ",".join(hexs(c15(c)) for c in r) + "}, /* %s */" % t)
    w("};")
    w("")
    w("/* Particles, 8x8: [0] uses indices 1..4 (ramp A: glow, light, fill, dark),")
    w(" * [1] the same shapes on 5..8 (ramp B). */")
    w("enum { FZP_DOT, FZP_SOFT, FZP_ORB, FZP_STAR, FZP_COUNT };")
    w("static const u32 fz_particle_gfx[2][FZP_COUNT][8] GFX_FUSION_UNUSED = {")
    for off in (0, 4):
        w("    {")
        for img in PARTICLES:
            img2 = [[(v + off if v else 0) for v in row] for row in img]
            w(rows_c(tiles_of(img2, 1, 1)[0], 8, "        { ")[:-1] + " },")
        w("    },")
    w("};")
    corner = corner_tile()
    w("/* Cursor corner (top-left; flip for the rest): 1 white, 2 ink. */")
    w("static const u32 fz_corner_gfx[8] GFX_FUSION_UNUSED = {")
    w(rows_c(tiles_of(corner, 1, 1)[0]))
    w("};")
    w("")
    w("/* sin(2 pi i / 256) * 256 */")
    sins = [int(round(math.sin(2 * math.pi * i / 256) * 256)) for i in range(256)]
    w("static const s16 fz_sin[256] GFX_FUSION_UNUSED = {")
    for i in range(0, 256, 16):
        w("    " + ",".join(str(v) for v in sins[i:i + 16]) + ",")
    w("};")
    w("")

    scenes = [scene_works(), scene_extract(), scene_loom(), scene_tuner()]
    w("/* Machine scenes for the UI canvas (240x160 = 30x20 cells). Map entries:")
    w(" * tile index | BG palette bank << 12 (banks 3..7, fz_scene_pal[scene][bank - 3]). */")
    w("enum { " + ", ".join("FZ_SCENE_" + n for n in SCENE_NAMES) + ", FZ_SCENE_COUNT };")
    packed = []
    for name, P in zip(SCENE_NAMES, scenes):
        idx, cb, pals, misses = quantise(P, name)
        tiles, mp = pack_scene(idx, cb)
        packed.append((name, idx, cb, pals, tiles, mp, misses))
        if misses:
            print("  scene %s: %d pixel(s) remapped to their cell's bank" % (name, misses))
        w("static const u32 fz_scene_%s_tiles[%d * 8] GFX_FUSION_UNUSED = {" % (name.lower(), len(tiles)))
        w(rows_c([v for t in tiles for v in t]))
        w("};")
        w("static const u16 fz_scene_%s_map[600] GFX_FUSION_UNUSED = {" % name.lower())
        w(rows_c(mp, 15))
        w("};")
    w("static const u32 *const fz_scene_tiles[FZ_SCENE_COUNT] GFX_FUSION_UNUSED = {")
    w("    " + ", ".join("fz_scene_%s_tiles" % n.lower() for n in SCENE_NAMES) + ",")
    w("};")
    w("static const u16 *const fz_scene_map[FZ_SCENE_COUNT] GFX_FUSION_UNUSED = {")
    w("    " + ", ".join("fz_scene_%s_map" % n.lower() for n in SCENE_NAMES) + ",")
    w("};")
    w("static const u16 fz_scene_pal[FZ_SCENE_COUNT][5][16] GFX_FUSION_UNUSED = {")
    for (name, idx, cb, pals, tiles, mp, misses) in packed:
        w("    { /* %s */" % name)
        for p in pals:
            w("        {" + ",".join(hexs(c15(c)) for c in p) + "},")
        w("    },")
    w("};")
    w("")
    # geometry the game needs
    fy0, spans = GEOM['FLASK']
    w("/* Geometry (pixels). EXTRACT: the dome (the kin's portrait sits behind the")
    w(" * canvas inside it), the flask mouth and the flask's inner spans; bank 7 of")
    w(" * EXTRACT holds the liquid at 10..12 (type A light, fill, dark) and 13..15 (B). */")
    dcx, dcy, dr = GEOM['DOME']
    w("#define FZ_DOME_CX %d" % dcx)
    w("#define FZ_DOME_CY %d" % dcy)
    w("#define FZ_DOME_R %d" % dr)
    w("#define FZ_FLASK_MOUTH_X %d" % GEOM['FLASK_MOUTH'][0])
    w("#define FZ_FLASK_MOUTH_Y %d" % GEOM['FLASK_MOUTH'][1])
    w("#define FZ_FLASK_Y0 %d" % fy0)
    w("#define FZ_FLASK_ROWS %d" % len(spans))
    w("static const u8 fz_flask_span[FZ_FLASK_ROWS][2] GFX_FUSION_UNUSED = {")
    for i in range(0, len(spans), 8):
        w("    " + " ".join("{%d,%d}," % s for s in spans[i:i + 8]))
    w("};")
    lcx, lcy = GEOM['WORKS_LOOM']
    w("#define FZ_WORKS_LOOM_X %d" % lcx)
    w("#define FZ_WORKS_LOOM_Y %d" % lcy)
    ex, ey = GEOM['WORKS_DOME']
    w("#define FZ_WORKS_DOME_X %d" % ex)
    w("#define FZ_WORKS_DOME_Y %d" % ey)
    tanks = GEOM['WORKS_TANKS']
    w("/* WORKS tanks: x, top, bottom, liquid top */")
    w("static const u8 fz_works_tank[%d][4] GFX_FUSION_UNUSED = {" % len(tanks))
    for (tx, top, bot, lvl) in tanks:
        w("    {%d,%d,%d,%d}," % (tx, top, bot, bot - int((bot - top) * lvl)))
    w("};")
    lx, ly = GEOM['LOOM']
    w("/* LOOM: ring centre, sockets (angles in 256ths of a turn), reel windows (20x20). */")
    w("#define FZ_LOOM_X %d" % lx)
    w("#define FZ_LOOM_Y %d" % ly)
    w("#define FZ_LOOM_RING_R %d" % 35)
    socks = []
    for a in SOCKET_ANGLES:
        socks.append((int(round(lx + 35 * math.cos(math.radians(a)))), int(round(ly + 35 * math.sin(math.radians(a))))))
    w("static const u8 fz_loom_socket[3][2] GFX_FUSION_UNUSED = { " + ", ".join("{%d,%d}" % s for s in socks) + " };")
    w("static const u8 fz_loom_reel[2][2] GFX_FUSION_UNUSED = { " + ", ".join("{%d,%d}" % r for r in GEOM['REELS']) + " };")
    cx, cy, cw, ch = GEOM['CRT']
    w("/* TUNER: scope screen, timer bar and meter (bank 7: 3 screen, 4 grid, 5 grid light,")
    w(" * 6 target wave, 7 its glow, 8 your wave, 9 its glow, 10 meter back, 11 meter,")
    w(" * 12 meter light, 13..15 steel), knob centres. */")
    w("#define FZ_CRT_X %d" % cx)
    w("#define FZ_CRT_Y %d" % cy)
    w("#define FZ_CRT_W %d" % cw)
    w("#define FZ_CRT_H %d" % ch)
    tx, ty, tw, th = GEOM['TIMER']
    w("#define FZ_TIMER_X %d" % tx)
    w("#define FZ_TIMER_Y %d" % ty)
    w("#define FZ_TIMER_W %d" % tw)
    w("#define FZ_TIMER_H %d" % th)
    mx, my, mw, mh = GEOM['METER']
    w("#define FZ_METER_X %d" % mx)
    w("#define FZ_METER_Y %d" % my)
    w("#define FZ_METER_W %d" % mw)
    w("#define FZ_METER_H %d" % mh)
    w("static const u8 fz_knob[2][2] GFX_FUSION_UNUSED = { " + ", ".join("{%d,%d}" % k for k in GEOM['KNOBS']) + " };")
    w("")
    w("#endif /* GFX_FUSION_H */")
    with open(OUT_H, "w") as f:
        f.write("\n".join(out) + "\n")
    print("wrote %s" % OUT_H)

    if preview:
        # glyph sheet (4x) on white and on dark
        S = 4
        rows = [[(255, 255, 255)] * (18 * 18 * S) for _ in range(40 * S)]
        for i, img in enumerate(glyphs):
            pal = GLYPH_PALS[i // 6]
            for y in range(16):
                for x in range(16):
                    v = img[y][x]
                    for bg, oy in (((255, 255, 255), 0), ((40, 44, 64), 20)):
                        col = to8(pal[v]) if v else bg
                        for sy in range(S):
                            for sx in range(S):
                                rows[(oy + y) * S + sy][(i * 18 + x) * S + sx] = col
            for y in range(20, 40):
                for x in range(18):
                    for sy in range(S):
                        for sx in range(S):
                            r = rows[y * S + sy][(i * 18 + x) * S + sx]
                            if r == (255, 255, 255):
                                rows[y * S + sy][(i * 18 + x) * S + sx] = (40, 44, 64)
        write_png(os.path.join(preview, "fz_glyphs.png"), rows)
        for (name, idx, cb, pals, tiles, mp, misses) in packed:
            S = 3
            rows = []
            for y in range(160):
                r = []
                for x in range(240):
                    v = idx[y][x]
                    b = cb[y // 8][x // 8]
                    col = (255, 0, 255) if v == 0 else to8(pals[b][v])
                    r.extend([col] * S)
                for _ in range(S):
                    rows.append(r)
            write_png(os.path.join(preview, "fz_scene_%s.png" % name.lower()), rows)
            print("  scene %s: %d tiles" % (name, len(tiles)))


if __name__ == "__main__":
    main()
