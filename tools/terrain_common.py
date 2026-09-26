#!/usr/bin/env python3
"""Terrain art shared by the village and route tilesets: grass, tall grass,
flowers, paving, trees, the battle court and the path/water autotiles."""

import math
from pixelart import Img, G, tex_fill, hash2, shade_clumps

GL = {'.': 'g_base', 'l': 'g_lt', 'm': 'g_mid', 'h': 'g_hi', 'd': 'g_dk',
      'w': 'white', 'y': 'f_yel'}

GRASS_A = G('''
................
................
.........l......
...m..m.........
....mm..........
............l...
................
..........m..m..
...l.......mm...
................
................
................
....m..m........
.....mm......l..
................
................
''', GL)

GRASS_B = G('''
................
......l.........
................
..........m..m..
...........mm...
................
..l.............
................
................
...m..m.....l...
....mm..........
................
................
..........m..m..
.....l.....mm...
................
''', GL)

GRASS_C = G('''
................
................
...w............
..wyw.......m..m
...m.........mm.
................
................
.........w......
................
.........m......
................
..m..m..........
...mm.......w...
...........wyw..
............m...
................
''', GL)


def grass_img(w, h, tex=None):
    img = Img(w, h)
    tex_fill(img, tex or GRASS_A)
    return img


def fill_grass(img, tex=None):
    """Put grass (world-aligned) under every transparent pixel."""
    tex_fill(img, tex or GRASS_A, only_none=True)
    return img


# ---------------------------------------------------------------- tall grass

TALL_L = {'.': None, 'O': 'g_dkr', 'd': 'g_dk', 'm': 'g_mid', 'b': 'g_base',
          'l': 'g_lt', 'h': 'g_hi'}
TUFT = G('''
..h...h.
.hlO.hlO
.hlmOhlm
hllmdllm
hlmmdlmd
lmmddmmd
mmdddmdd
ddddOddd
dOddddOd
''', TALL_L)


def tallgrass_layers():
    """Returns (bottom 16x16 opaque, top 16x16 with transparency)."""
    back = Img(16, 16, 'g_base')
    for ox in (-4, 4, 12):
        back.paste(TUFT, ox, 0)
    front = Img(16, 16)
    for ox in (0, 8):
        front.paste(TUFT, ox, 8)
    bottom = back.copy()
    bottom.paste(front, 0, 0)
    for y in range(16):
        for x in range(16):
            if bottom.p[y][x] is None:
                bottom.p[y][x] = 'g_dk'
    # overlay: the front tufts from row 9 down, with the dark gaps between
    # blades left open so legs peek through
    top = Img(16, 16)
    for y in range(9, 16):
        for x in range(16):
            ty, tx = y - 8, x % 8
            c = TUFT.p[ty][tx]
            if c is None:
                continue
            if ty <= 3 and c in ('g_dkr', 'g_dk'):
                continue
            top.p[y][x] = c
    return bottom, top


# ---------------------------------------------------------------- flowers

def flower_frames(petal, shade, center, hilite):
    """Two 16x16 frames of a flower patch on grass (heads sway 1px)."""
    FL = {'.': None, 'P': petal, 'p': shade, 'c': center, 'w': hilite,
          'L': 'g_mid', 'D': 'g_dk'}
    head = G('''
    .wP.
    PccP
    PccP
    .pp.
    ''', FL)
    leaves = G('''
    .D..
    LDL.
    .LD.
    ''', FL)
    spots = [(1, 1), (9, 3), (4, 9), (11, 11)]
    frames = []
    for f in range(2):
        img = Img(16, 16)
        tex_fill(img, GRASS_B)
        # clear the grass tufts near the flowers so they read cleanly
        for (x, y) in spots:
            for yy in range(y, y + 7):
                for xx in range(x - 1, x + 5):
                    if 0 <= xx < 16 and 0 <= yy < 16:
                        img.p[yy][xx] = 'g_base'
        for i, (x, y) in enumerate(spots):
            img.paste(leaves, x, y + 3)
            dx = (1 if (i % 2 == 0) else -1) if f == 1 else 0
            dy = 1 if (f == 1 and i % 2 == 1) else 0
            img.paste(head, x + dx, y + dy)
        frames.append(img)
    return frames


# ---------------------------------------------------------------- paving

STONE_L = {'h': 'r_hi', 'l': 'r_base', 'm': 'r_dk', 'd': 'c_dk'}
STONE = G('''
hhhhhhhmhhhhhhhm
hlllllmmhlllllmm
hllllllmhllllllm
hllllllmhllllllm
hllllllmhllllllm
hlllllmmhlllllmm
hmllmmmmhmllmmmm
mmmmmmmdmmmmmmmd
hhhmhhhhhhhmhhhh
lllmmhlllllmmhll
lllmhllllllmhlll
lllmhllllllmhlll
lllmhllllllmhlll
llmmhlllllmmhlll
mmmmhmllmmmmhmll
mmmdmmmmmmmdmmmm
''', STONE_L)


# ---------------------------------------------------------------- trees

TREE_RAMP = ['t_hi', 't_lt', 't_base', 't_mid', 't_dk']


def tree_img(overlay=False):
    """16x32 tree on grass; overlay=True: on transparent ground (the engine
    draws whatever ground the tree stands on underneath)."""
    clumps = [
        (8.0, 8.0, 6.5, 6.5),
        (4.5, 13.0, 4.5, 4.6), (11.5, 13.0, 4.5, 4.6),
        (8.0, 15.5, 5.5, 5.0),
        (4.5, 19.5, 4.5, 4.0), (11.5, 19.5, 4.5, 4.0),
        (8.0, 21.5, 5.0, 3.2),
    ]
    can, own = shade_clumps(16, 32, clumps, TREE_RAMP, 't_out', seed=3,
                            clip=lambda x, y: 1 <= x <= 14)
    img = Img(16, 32)
    TK = {'.': None, 'O': 't_out', 'l': 'k_lt', 'b': 'k_base', 'd': 'k_dk',
          's': None if overlay else 'g_dk'}
    trunk = G('''
    .OlbbdO.
    .OlbbdO.
    .Olbbdo.
    OOlbbddO
    OlbbbbdO
    sOOOOOOs
    .ssssss.
    ''', dict(TK, o='t_out'))
    img.paste(trunk, 4, 24)
    img.paste(can, 0, 0)
    if not overlay:
        fill_grass(img)
    return img


def bush_img():
    clumps = [(8.0, 6.5, 5.5, 4.5), (4.8, 9.5, 3.8, 3.6), (11.2, 9.5, 3.8, 3.6),
              (8.0, 10.5, 4.6, 3.4)]
    can, own = shade_clumps(16, 16, clumps, TREE_RAMP, 't_out', seed=7,
                            clip=lambda x, y: 1 <= x <= 14 and y <= 13)
    img = Img(16, 16)
    for x in range(2, 15):
        img.set(x, 14, 'g_dk')
    for x in range(4, 13):
        img.set(x, 15, 'g_dk')
    img.paste(can, 0, 0)
    fill_grass(img)
    return img


# ---------------------------------------------------------------- props





# ---------------------------------------------------------------- court

COURT_L = {'.': 'c_base', 'l': 'c_lt', 'd': 'c_dk', 'W': 'w_hi'}
COURT = G('''
................
..........d.....
....l...........
...............l
..d.............
.........l......
................
.............d..
.l..............
......d.........
................
...........l....
...l............
................
........d......d
................
''', COURT_L)


def court_img(line=None):
    img = COURT.copy()
    if line == 'h':
        for x in range(16):
            img.p[7][x] = 'w_hi'
            img.p[8][x] = 'w_hi'
    elif line == 'v':
        for y in range(16):
            img.p[y][7] = 'w_hi'
            img.p[y][8] = 'w_hi'
    return img


def court_circle_img():
    img = Img(32, 32)
    tex_fill(img, COURT)
    for y in range(32):
        for x in range(32):
            d = math.hypot(x + 0.5 - 16, y + 0.5 - 16)
            if 11.0 <= d <= 13.0 or d <= 1.6:
                img.p[y][x] = 'w_hi'
    return img


# ---------------------------------------------------------------- autotiles
#
# Every quadrant is computed from a signed distance d (>0 inside the
# region) evaluated in *local* coordinates, mirrored so that lx=0 / ly=0 is
# the cell side that faces the tested neighbours.  Textures are sampled at
# absolute cell coordinates so the fill continues across quadrants/cells.

def quad_sdf(v, px, py, E, R, Rn, wob):
    if v == 0:
        return 99.0
    if v == 2:
        return px - E - wob(py)
    if v == 3:
        return py - E - wob(px)
    if v == 4:
        ax, ay = (E + R) - px, (E + R) - py
        if ax > 0 and ay > 0:
            return R - math.hypot(ax, ay)
        return min(px - E - wob(py), py - E - wob(px))
    if v == 1:
        ax, ay = px - (E - Rn), py - (E - Rn)
        if ax > 0 and ay > 0:
            return math.hypot(ax, ay) - Rn
        return max(ax, ay) - Rn
    raise ValueError(v)


def autotile(color_at, E, R, Rn, wob=lambda t: 0.0):
    """color_at(d, X, Y, c, v) -> color name. Returns quads[c][v] = Img 8x8."""
    quads = []
    for c in range(4):
        row = []
        for v in range(5):
            img = Img(8, 8)
            for y in range(8):
                for x in range(8):
                    X = x + 8 * (c & 1)
                    Y = y + 8 * (c >> 1)
                    lx = x if (c & 1) == 0 else 7 - x
                    ly = y if (c >> 1) == 0 else 7 - y
                    d = quad_sdf(v, lx + 0.5, ly + 0.5, E, R, Rn, wob)
                    img.p[y][x] = color_at(d, X, Y, c, v, lx, ly)
            row.append(img)
        quads.append(row)
    return quads


PATH_TEX = G('''
................
.........h......
..m.............
...........m....
......h.........
................
.m..........h...
................
.........m......
...h............
................
.............m..
.....m..........
..........h.....
.h..............
................
''', {'.': 's_base', 'h': 's_hi', 'm': 's_mid'})


def path_quads():
    def wob(t):
        return 0.0

    def color_at(d, X, Y, c, v, lx, ly):
        if d < -1.0:
            return GRASS_A.p[Y][X]
        if d < 0:
            return 'g_base'
        if d < 1.0:
            return 's_mid'
        if d < 2.0:
            return 's_base'
        return PATH_TEX.p[Y][X]
    return autotile(color_at, E=2.0, R=5.0, Rn=2.0, wob=wob)


WAVES = [(1, 1, 3), (12, 2, 3), (7, 5, 3), (3, 9, 2), (13, 9, 3), (10, 12, 3)]


def water_surface(f):
    img = Img(16, 16, 'w_base')
    for (x, y, n) in WAVES:
        n2 = n - (1 if f == 2 else 0)
        x2 = x + f
        for i in range(n2):
            img.p[y % 16][(x2 + i) % 16] = 'w_lt'
        if n2 >= 3:
            img.p[y % 16][(x2 + n2 // 2) % 16] = 'w_hi'
        for i in range(max(1, n2 - 1)):
            img.p[(y + 1) % 16][(x2 + 1 + i) % 16] = 'w_mid'
    return img


def water_quads(f):
    surf = water_surface(f)

    def color_at(d, X, Y, c, v, lx, ly):
        if d < 0:
            return GRASS_A.p[Y][X]
        if d < 1.0:
            return 'r_hi'
        if d < 2.0:
            return 'r_base'
        if d < 3.0:
            return 'r_dk'
        if d < 4.0:
            return 'w_dk'
        if d < 5.0:
            return 'w_mid'
        return surf.p[Y][X]
    return autotile(color_at, E=1.0, R=6.0, Rn=2.5)


