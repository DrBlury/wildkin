#!/usr/bin/env python3
"""Generate src/gfx_rune.h: the art of the ten RUNE battle moves (anim_rune.c).

The RUNESTONE's homeward spell (gen_travel_gfx) grown into an attack set.
Everything is drawn in ONE index layout so any element palette recolours
any piece (a KENAZ glyph burns, an ISA glyph frosts over):

    1 deep   2 dark   3 mid    4 light     halo ramp (dark .. light)
    5 rim-d  6 rim    7 pale   8 white     strokes and rims
    9 accent 10 gold  11-13 crystal (dark, mid, light)

Pieces (OBJ tiles in upload order, 1D mapping):

  * 12 runes, 16x16: bright core, rim, a dithered halo. Depth is shown by
    the palette bank (anim_rune.c fades the same tiles toward the dark in
    two steps), so there is no second "behind" set.
  * 6 hero runes, 32x32 (KENAZ, ISA, SOWILO, THURISAZ, ALGIZ, ANSUZ) with
    2-pixel strokes, for the moves' signature glyphs.
  * three 32x32 circles, drawn flat and squashed on the ground or stood up
    as gates with an affine matrix: the hexagram CIRCLE, the SEAL (double
    ring with rune notches and an eight-point star) and a thin RING with
    nodes for shockwaves and wards.
  * a 16x32 light BEAM that tiles, and a 16x32 crystal SPIKE (point up,
    base on the bottom row).
  * eight 8x8 sparks: star, small, lilac, dot, mote, shard, ember, glint.

The palettes: ARCANE (the set's violet and cyan, the RUNESTONE's) and one
per element. Deterministic, standard library only:

    python3 tools/gen_rune_gfx.py [--preview DIR]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixelart import c15, c15_to_rgb, write_png, scale_rows  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_H = os.path.join(ROOT, 'src', 'gfx_rune.h')

K = {'.': 0, 'i': 1, 'V': 2, 'v': 3, 'L': 4, 'C': 5, 'c': 6, 'P': 7, 'w': 8, 'm': 9, 'Y': 10,
     's': 11, 'S': 12, 'T': 13}

# name -> (i, V, v, L, C, c, P, w, m, Y, s, S, T) in 8-bit RGB
PALETTES = [
    ('ARCANE', [(36, 20, 84), (84, 44, 164), (144, 88, 236), (206, 168, 255), (32, 128, 200),
                (88, 212, 252), (196, 248, 255), (248, 248, 248), (236, 104, 224), (255, 228, 140),
                (60, 52, 120), (120, 110, 200), (200, 196, 255)]),
    ('KENAZ', [(72, 12, 8), (150, 36, 12), (224, 84, 20), (255, 184, 110), (208, 96, 16),
               (255, 168, 40), (255, 236, 150), (255, 255, 236), (255, 64, 48), (255, 220, 90),
               (96, 32, 16), (180, 72, 24), (255, 170, 90)]),
    ('ISA', [(16, 32, 72), (40, 84, 150), (90, 150, 220), (180, 220, 250), (60, 140, 200),
             (140, 220, 255), (220, 248, 255), (255, 255, 255), (160, 200, 255), (230, 250, 255),
             (56, 104, 168), (130, 190, 240), (224, 246, 255)]),
    ('SOWILO', [(80, 40, 8), (150, 90, 16), (232, 160, 32), (255, 220, 140), (216, 140, 24),
                (255, 208, 64), (255, 244, 180), (255, 255, 240), (255, 120, 40), (255, 236, 120),
                (120, 72, 16), (208, 150, 48), (255, 230, 150)]),
    ('THURS', [(40, 24, 16), (96, 56, 32), (168, 104, 56), (224, 184, 140), (150, 40, 40),
               (236, 96, 72), (255, 210, 180), (255, 248, 236), (200, 60, 90), (255, 200, 100),
               (72, 60, 56), (132, 116, 104), (196, 184, 168)]),
    ('ALGIZ', [(8, 48, 56), (20, 96, 104), (48, 168, 160), (160, 236, 220), (200, 150, 40),
               (255, 212, 96), (236, 255, 244), (255, 255, 255), (120, 255, 200), (255, 230, 140),
               (24, 88, 96), (72, 160, 150), (180, 240, 228)]),
    ('SIGIL', [(52, 12, 60), (110, 30, 120), (190, 70, 200), (240, 170, 250), (140, 40, 160),
               (250, 120, 230), (255, 220, 250), (255, 255, 255), (255, 80, 160), (255, 200, 240),
               (90, 30, 100), (170, 80, 190), (240, 190, 250)]),
    ('RAIDO', [(12, 40, 72), (24, 88, 140), (60, 160, 220), (180, 230, 255), (40, 120, 200),
               (120, 230, 255), (220, 250, 255), (255, 255, 255), (160, 120, 255), (255, 255, 200),
               (40, 80, 130), (100, 170, 230), (200, 240, 255)]),
    ('SIPHON', [(20, 40, 30), (40, 100, 70), (80, 190, 120), (190, 250, 210), (110, 60, 180),
                (180, 130, 255), (230, 255, 236), (255, 255, 255), (236, 104, 224), (240, 255, 160),
                (40, 90, 70), (90, 170, 130), (200, 250, 220)]),
]


def palette15(entries):
    return [0] + [c15(c) for c in entries] + [0] * (15 - len(entries))


# =====================================================================
# Images (index grids)
# =====================================================================

def blank(w, h):
    return [[0] * w for _ in range(h)]


def put(img, x, y, v):
    if 0 <= y < len(img) and 0 <= x < len(img[0]):
        img[y][x] = v


def get(img, x, y):
    if 0 <= y < len(img) and 0 <= x < len(img[0]):
        return img[y][x]
    return 0


def pack4(idx):
    words = []
    for y in range(8):
        w = 0
        for x in range(8):
            w |= (idx[y * 8 + x] & 15) << (4 * x)
        words.append(w)
    return words


def tiles_of(img):
    """Row-major 8x8 tiles (1D OBJ mapping) of an index image."""
    h, w = len(img), len(img[0])
    out = []
    for ty in range(h // 8):
        for tx in range(w // 8):
            out.append(pack4([img[ty * 8 + y][tx * 8 + x] for y in range(8) for x in range(8)]))
    return out


# =====================================================================
# Runes: strokes on a 7x9 grid (x 0..6, y 0..8)
# =====================================================================

RUNES = [
    ('FEHU', [[(1, 8), (1, 0)], [(1, 3), (5, 0)], [(1, 6), (5, 3)]]),
    ('THURISAZ', [[(1, 0), (1, 8)], [(1, 2), (5, 4), (1, 6)]]),
    ('ANSUZ', [[(1, 0), (1, 8)], [(1, 0), (5, 3)], [(1, 3), (5, 6)]]),
    ('RAIDO', [[(1, 8), (1, 0), (5, 2), (1, 4), (5, 8)]]),
    ('KENAZ', [[(5, 0), (1, 4), (5, 8)]]),
    ('ISA', [[(3, 0), (3, 8)]]),
    ('SOWILO', [[(5, 0), (1, 3), (5, 5), (1, 8)]]),
    ('ALGIZ', [[(3, 8), (3, 0)], [(3, 4), (0, 1)], [(3, 4), (6, 1)]]),
    ('OTHALA', [[(0, 8), (5, 3), (3, 0), (1, 3), (6, 8)]]),
    ('TIWAZ', [[(3, 8), (3, 0)], [(0, 3), (3, 0), (6, 3)]]),
    ('DAGAZ', [[(0, 1), (6, 7), (6, 1), (0, 7), (0, 1)]]),
    ('INGWAZ', [[(3, 0), (6, 4), (3, 8), (0, 4), (3, 0)]]),
]
HERO = ['KENAZ', 'ISA', 'SOWILO', 'THURISAZ', 'ALGIZ', 'ANSUZ']


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    qx, qy = ax + dx * t, ay + dy * t
    return math.hypot(px - qx, py - qy)


def stroke_core(strokes, size, unit, width):
    """Pixels within `width` of the strokes, the rune centred in size x size."""
    gw, gh = 6 * unit, 8 * unit
    ox, oy = (size - gw) / 2.0, (size - gh) / 2.0
    segs = []
    for poly in strokes:
        for (a, b) in zip(poly, poly[1:]):
            segs.append((ox + a[0] * unit, oy + a[1] * unit, ox + b[0] * unit, oy + b[1] * unit))
    core = set()
    for y in range(size):
        for x in range(size):
            if any(seg_dist(x, y, *s) <= width for s in segs):
                core.add((x, y))
    return core


def rune_image(strokes, size):
    """A glowing rune: white core, cyan rim, violet halo fading out."""
    img = blank(size, size)
    if size == 16:
        core = stroke_core(strokes, 16, 1, 0.5)
    else:
        core = stroke_core(strokes, 32, 3, 0.95)
    dist = {}
    for y in range(size):
        for x in range(size):
            if (x, y) in core:
                continue
            dist[(x, y)] = min(max(abs(x - cx), abs(y - cy)) + 0.5 * min(abs(x - cx), abs(y - cy))
                               for (cx, cy) in core)
    big = size == 32
    for (x, y) in core:
        img[y][x] = K['w']
    if big:   # a pale inner edge on the 2-px strokes
        for (x, y) in core:
            if any((x + dx, y + dy) not in core for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                img[y][x] = K['P']
    for (x, y), d in dist.items():
        if d <= 1.0:
            img[y][x] = K['c']
        elif d <= (1.6 if not big else 2.1):
            img[y][x] = K['C'] if big else K['v']
        elif d <= (2.2 if not big else 3.2):
            img[y][x] = K['v']
        elif d <= (3.2 if not big else 4.4) and (x + y) % 2 == 0:
            img[y][x] = K['V']
        elif big and d <= 5.4 and (x + y) % 4 == 0:
            img[y][x] = K['i']
    return img


# =====================================================================
# Circles
# =====================================================================

def circle_hexagram():
    """The RUNESTONE's circle: two rings, ticks, a six-point star."""
    img = blank(32, 32)
    for y in range(32):
        for x in range(32):
            r = math.hypot(x + 0.5 - 16, y + 0.5 - 16)
            a = math.atan2(y + 0.5 - 16, x + 0.5 - 16)
            if 14.2 <= r < 15.4:
                img[y][x] = K['c']
            elif 13.2 <= r < 14.2:
                img[y][x] = K['C']
            elif 10.4 <= r < 11.4:
                img[y][x] = K['v']
            elif 11.4 <= r < 13.2:
                k = (a + math.pi) / (2 * math.pi) * 24
                if abs(k - round(k)) < 0.12:
                    img[y][x] = K['P']
                elif (int(k) % 3 == 0) and abs(k - int(k) - 0.5) < 0.2 and 11.8 <= r < 12.8:
                    img[y][x] = K['L']
    for tri in range(2):
        pts = []
        for k in range(3):
            ang = math.radians(-90 + tri * 60 + k * 120)
            pts.append((16 + 10.2 * math.cos(ang), 16 + 10.2 * math.sin(ang)))
        for k in range(3):
            (x0, y0), (x1, y1) = pts[k], pts[(k + 1) % 3]
            for s in range(41):
                x = int(x0 + (x1 - x0) * s / 40)
                y = int(y0 + (y1 - y0) * s / 40)
                if img[y][x] == 0:
                    img[y][x] = K['V'] if tri else K['v']
    for y in range(32):
        for x in range(32):
            if math.hypot(x + 0.5 - 16, y + 0.5 - 16) < 2.0:
                img[y][x] = K['P']
    return img


def circle_seal():
    """A sealing circle: a double ring with eight rune notches, an
    eight-point star of two squares and a bright core."""
    img = blank(32, 32)
    for y in range(32):
        for x in range(32):
            r = math.hypot(x + 0.5 - 16, y + 0.5 - 16)
            a = math.atan2(y + 0.5 - 16, x + 0.5 - 16)
            k = (a + math.pi) / (2 * math.pi) * 8
            f = k - math.floor(k)
            if 14.4 <= r < 15.5:
                img[y][x] = K['c']
            elif 13.6 <= r < 14.4:
                img[y][x] = K['C']
            elif 9.6 <= r < 10.6:
                img[y][x] = K['c'] if (int(k * 2) % 2 == 0) else K['v']
            elif 10.6 <= r < 13.6:
                # a rune notch in the band every eighth of a turn
                if abs(f - 0.5) < 0.09 and 11.0 <= r < 13.3:
                    img[y][x] = K['w']
                elif abs(f - 0.5) < 0.2 and 11.9 <= r < 12.5:
                    img[y][x] = K['P']
                elif (x + y) % 2 == 0:
                    img[y][x] = K['i']
    # two squares (a star of eight points) inside the inner ring
    for rot in (0.0, math.pi / 4):
        pts = [(16 + 9.2 * math.cos(rot + q * math.pi / 2), 16 + 9.2 * math.sin(rot + q * math.pi / 2))
               for q in range(4)]
        for q in range(4):
            (x0, y0), (x1, y1) = pts[q], pts[(q + 1) % 4]
            for s in range(41):
                x = int(round(x0 + (x1 - x0) * s / 40 - 0.5))
                y = int(round(y0 + (y1 - y0) * s / 40 - 0.5))
                if get(img, x, y) in (0, K['i']):
                    put(img, x, y, K['L'] if rot else K['v'])
    for y in range(32):
        for x in range(32):
            r = math.hypot(x + 0.5 - 16, y + 0.5 - 16)
            if r < 1.6:
                img[y][x] = K['w']
            elif r < 2.8:
                img[y][x] = K['c']
            elif 4.0 <= r < 4.8:
                img[y][x] = K['V']
    return img


def circle_ring():
    """A thin bright ring with eight nodes and a faint inner glow."""
    img = blank(32, 32)
    for y in range(32):
        for x in range(32):
            r = math.hypot(x + 0.5 - 16, y + 0.5 - 16)
            a = math.atan2(y + 0.5 - 16, x + 0.5 - 16)
            k = (a + math.pi) / (2 * math.pi) * 8
            node = abs(k - round(k)) < 0.08
            if 13.8 <= r < 15.0:
                img[y][x] = K['w'] if node else K['c']
            elif 12.8 <= r < 13.8:
                img[y][x] = K['P'] if node else K['C']
            elif 15.0 <= r < 15.8 and node:
                img[y][x] = K['c']
            elif 11.4 <= r < 12.8 and (x + y) % 2 == 0:
                img[y][x] = K['v']
            elif 10.2 <= r < 11.4 and (x * 3 + y) % 4 == 0:
                img[y][x] = K['V']
    return img


# =====================================================================
# Beam, spike, sparks
# =====================================================================

def beam():
    """A 16x32 column of light that tiles vertically."""
    img = blank(16, 32)
    for y in range(32):
        for x in range(16):
            d = abs(x + 0.5 - 8)
            if d < 1.6:
                v = K['w']
            elif d < 3.0:
                v = K['P']
            elif d < 4.4:
                v = K['c']
            elif d < 5.8:
                v = K['v'] if (x + y) % 2 else K['c']
            elif d < 7.2:
                v = K['V'] if (x * 3 + y) % 4 == 0 else 0
            else:
                v = 0
            img[y][x] = v
    for k in range(6):
        put(img, 4 + (k * 5) % 8, (k * 11) % 32, K['w'])
    return img


def spike():
    """A 16x32 crystal thorn, point up, base on the bottom row: a lit left
    facet, a dark right facet and a glowing rune seam up the middle."""
    img = blank(16, 32)
    for y in range(32):
        half = 0.4 + 6.6 * (y / 31.0) ** 0.85      # tapers to a point at the top
        for x in range(16):
            dx = x + 0.5 - 8
            if abs(dx) > half:
                continue
            e = abs(dx) / half
            if e > 0.82:
                v = K['s']
            elif dx < -0.5:
                v = K['T'] if e < 0.45 else K['S']
            elif dx > 0.5:
                v = K['S'] if e < 0.4 else K['s']
            else:
                v = K['c']
            img[y][x] = v
    # the seam glows brighter toward the tip; notches like a thorn rune
    for y in range(2, 30):
        if y < 12:
            put(img, 8, y, K['w'])
        elif y % 7 == 3:
            put(img, 9, y, K['P'])
            put(img, 10, y - 1, K['c'])
    for x in range(16):   # dark outline
        for y in range(32):
            if img[y][x] == 0 and any(get(img, x + dx, y + dy) not in (0, K['i'])
                                      for dx, dy in ((1, 0), (-1, 0), (0, -1))):
                img[y][x] = K['i']
    return img


def grid(text):
    rows = [r.strip() for r in text.strip('\n').split('\n') if r.strip()]
    img = blank(8, 8)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            img[y][x] = K[ch]
    return img


SPARKS = [
    ('STAR', '''
        ...w....
        ...c....
        ..cPc...
        wcPwPcw.
        ..cPc...
        ...c....
        ...w....
        ........
    '''),
    ('SMALL', '''
        ........
        ...c....
        ..cwc...
        ...c....
        ........
        ........
        ........
        ........
    '''),
    ('LILAC', '''
        ........
        ...L....
        ..LmL...
        ...L....
        ........
        ........
        ........
        ........
    '''),
    ('DOT', '''
        ........
        ........
        ...v....
        ........
        ........
        ........
        ........
        ........
    '''),
    ('MOTE', '''
        ........
        ..vcv...
        .vPwPv..
        .cwwwc..
        .vPwPv..
        ..vcv...
        ........
        ........
    '''),
    ('SHARD', '''
        ...w....
        ..TwS...
        ..TPS...
        ..TcS...
        ..TcS...
        ...s....
        ........
        ........
    '''),
    ('EMBER', '''
        ........
        ...m....
        ..mYm...
        ..YwY...
        ...m....
        ........
        ........
        ........
    '''),
    ('GLINT', '''
        ........
        ....w...
        ...wP...
        ..wPc...
        .wPc....
        ..c.....
        ........
        ........
    '''),
]


# =====================================================================
# The sheet
# =====================================================================

def sheet():
    tiles, offs = [], {}
    offs['GLYPH'] = len(tiles)
    for (_, strokes) in RUNES:
        tiles += tiles_of(rune_image(strokes, 16))
    offs['HERO'] = len(tiles)
    strokes_of = dict(RUNES)
    for name in HERO:
        tiles += tiles_of(rune_image(strokes_of[name], 32))
    offs['CIRCLE'] = len(tiles)
    tiles += tiles_of(circle_hexagram())
    offs['SEAL'] = len(tiles)
    tiles += tiles_of(circle_seal())
    offs['RING'] = len(tiles)
    tiles += tiles_of(circle_ring())
    offs['BEAM'] = len(tiles)
    tiles += tiles_of(beam())
    offs['SPIKE'] = len(tiles)
    tiles += tiles_of(spike())
    offs['SPARK'] = len(tiles)
    for (_, s) in SPARKS:
        tiles += tiles_of(grid(s))
    return tiles, offs


def emit():
    tiles, offs = sheet()
    L = []
    A = L.append
    A('/* Generated by tools/gen_rune_gfx.py -- do not edit. */')
    A('#ifndef GFX_RUNE_H')
    A('#define GFX_RUNE_H')
    A('')
    A('/* The RUNE battle moves (anim_rune.c): one index layout for every piece,')
    A(' * recoloured by the palettes below (ARCANE is the set\'s own violet and')
    A(' * cyan, the rest one per element). */')
    A('enum { ' + ', '.join('RP_%s' % n for n, _ in PALETTES) + ', RP_COUNT };')
    A('static const u16 rune_palettes[RP_COUNT][16] = {')
    for name, entries in PALETTES:
        A('    { ' + ', '.join('0x%04X' % v for v in palette15(entries)) + ' }, /* %s */' % name)
    A('};')
    A('/* 16x16 runes (4 tiles each) */')
    A('enum { ' + ', '.join('RG_%s' % n for n, _ in RUNES) + ', RG_COUNT };')
    A('/* 32x32 hero runes (16 tiles each) */')
    A('enum { ' + ', '.join('RH_%s' % n for n in HERO) + ', RH_COUNT };')
    A('enum { ' + ', '.join('RS_%s' % n for n, _ in SPARKS) + ', RS_COUNT };')
    for k in ('GLYPH', 'HERO', 'CIRCLE', 'SEAL', 'RING', 'BEAM', 'SPIKE', 'SPARK'):
        A('#define RT_%s %d' % (k, offs[k]))
    A('#define RT_TILE_COUNT %d' % len(tiles))
    A('static const u32 rune_gfx[RT_TILE_COUNT][8] = {')
    for t in tiles:
        A('    { ' + ', '.join('0x%08X' % w for w in t) + ' },')
    A('};')
    A('')
    A('#endif')
    return '\n'.join(L) + '\n'


def preview(d):
    os.makedirs(d, exist_ok=True)
    strokes_of = dict(RUNES)
    pieces = [rune_image(s, 16) for _, s in RUNES] + [rune_image(strokes_of[n], 32) for n in HERO]
    pieces += [circle_hexagram(), circle_seal(), circle_ring(), beam(), spike()]
    pieces += [grid(s) for _, s in SPARKS]
    for pname, entries in PALETTES:
        pal = [(16, 12, 28)] + [c15_to_rgb(c15(c)) for c in entries] + [(0, 0, 0)] * 3
        W, H = 0, 36
        for p in pieces:
            W += len(p[0]) + 4
        rows = [[(16, 12, 28)] * W for _ in range(H)]
        x = 2
        for p in pieces:
            for y, r in enumerate(p):
                for xx, v in enumerate(r):
                    if v:
                        rows[2 + y][x + xx] = pal[v]
            x += len(p[0]) + 4
        s = scale_rows(rows, 3)
        write_png(os.path.join(d, 'rune_%s.png' % pname.lower()), W * 3, H * 3, s)


def main():
    out = emit()
    with open(OUT_H, 'w') as f:
        f.write(out)
    if '--preview' in sys.argv:
        preview(sys.argv[sys.argv.index('--preview') + 1])


if __name__ == '__main__':
    main()
