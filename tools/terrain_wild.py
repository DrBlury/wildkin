#!/usr/bin/env python3
"""Route (wild) terrain: meadow, forest and lakeshore ground tiles.

wild_images() returns {name: (bottom, top_or_None)} 16x16 (or 16x32 split
into *_TOP/*_BOTTOM) images in colour names. Everything is opaque on the
bottom layer; `top` images are drawn above people (tall grass blades).
The palette banks they must fit are defined in gen_field_gfx.py
(WILD_BANKS); bank 0 = ground, 1 = water/sand, 2 = trees.

  bank 0: grass, ledges (grass lip + earth face), DIRT, MEADOW
  bank 1: SAND (sand + pebbles/shells)
  bank 2: pines, FOREST floor (moss, roots), REEDS (stalks + cattails), CLIFF
"""

import math
from pixelart import Img, G, tex_fill, hash2, shade_clumps
from terrain_common import (GRASS_A, GRASS_B, GRASS_C, TREE_RAMP, tallgrass_layers,
                            STONE, tree_img, fill_grass)

WILD_TERRAIN = [
    'GRASS', 'GRASS2', 'GRASS3', 'TALLGRASS', 'FLOWER_RED', 'FLOWER_YELLOW',
    'TREE_TOP', 'TREE_BOTTOM', 'PINE_TOP', 'PINE_BOTTOM', 'LEDGE', 'SAND',
    'FOREST', 'FOREST2', 'REEDS', 'STONE',
    # additions
    'LEDGE_L', 'LEDGE_R', 'CLIFF', 'CLIFF_FACE', 'DIRT', 'MEADOW', 'SAND2',
]

WILD_TERRAIN_DOC = {
    'GRASS': 'short grass + 2 variants',
    'TALLGRASS': 'wild kin roam here; top layer = front blades over the legs',
    'FLOWER_RED': 'animated flower patches (2 frames)',
    'TREE_TOP': '16x32 broadleaf tree: TOP above BOTTOM',
    'PINE_TOP': '16x32 pine tree: TOP above BOTTOM (forests; tiles side by side and stacked)',
    'LEDGE': 'one-way ledge: walk DOWN onto it to hop over (grass lip above, earth face and drop '
             'below); tiles horizontally',
    'LEDGE_L': 'left end of a LEDGE run (the drop tapers into the grass)',
    'LEDGE_R': 'right end of a LEDGE run',
    'SAND': 'lakeshore sand (+ SAND2 with a shell and pebbles)',
    'FOREST': 'shady forest floor with moss and roots (+ variant)',
    'REEDS': 'lakeshore cattails; wild kin roam here like tall grass (top layer hides legs)',
    'STONE': 'paving stones',
    'CLIFF': 'rock wall with a grass lip on top; tiles horizontally (solid)',
    'CLIFF_FACE': 'plain rock wall; stack under CLIFF for taller walls (solid)',
    'DIRT': 'worn earth (camps, farm yards, trodden spots)',
    'MEADOW': 'grass with clover and tiny white flowers (Whisper Meadow)',
}

PINE_RAMP = ['t_hi', 't_lt', 't_base', 't_mid', 't_dk']


# ---------------------------------------------------------------- pines

def pine_img():
    """16x32 conifer on grass: three drooping tiers, lit from the top-left."""
    tiers = [  # (apex_y, bottom_y, half width at the bottom)
        (13.0, 27.0, 8.2),
        (6.5, 20.0, 7.0),
        (1.0, 12.5, 5.2),
    ]
    img = Img(16, 32)
    owner = [[-1] * 16 for _ in range(32)]
    for ti, (ay, by, hw) in enumerate(tiers):
        for y in range(32):
            for x in range(16):
                v = (y + 0.5 - ay) / (by - ay)
                if v < 0 or v > 1.08:
                    continue
                half = hw * min(1.0, v) + 0.35
                dx = x + 0.5 - 8.0
                if abs(dx) > half:
                    continue
                # drooping, saw-toothed lower edge
                tooth = (x % 3 == 1)
                if v > 1.0 and not tooth:
                    continue
                if v > 0.93 and abs(dx) > half - 1.0 and not tooth:
                    continue
                owner[y][x] = ti
    for y in range(32):
        for x in range(16):
            ti = owner[y][x]
            if ti < 0:
                continue
            ay, by, hw = tiers[ti]
            v = (y + 0.5 - ay) / (by - ay)
            half = hw * min(1.0, max(v, 0.05)) + 0.35
            t = (x + 0.5 - 8.0) / half
            k = 2
            if t < -0.5:
                k = 1
            elif t < 0.1:
                k = 2
            elif t < 0.6:
                k = 3
            else:
                k = 4
            if v > 0.78:
                k = min(4, k + 1)
            if v < 0.35 and t < -0.2:
                k = max(0, k - 1)
            h = hash2(x, y, 23) & 7
            if h == 0 and k < 4:
                k += 1
            elif h == 1 and k > 1:
                k -= 1
            # shadow cast by the tier above
            if y > 0 and owner[y - 1][x] > ti:
                k = 4
            elif y > 1 and owner[y - 2][x] > ti:
                k = max(k, 3)
            img.p[y][x] = PINE_RAMP[k]
    for y in range(32):
        for x in range(16):
            if owner[y][x] >= 0:
                continue
            for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < 16 and 0 <= yy < 32 and owner[yy][xx] >= 0:
                    img.p[y][x] = 't_out'
                    break
    trunk = G('''
    .TabcT.
    .TabcT.
    TTabcTT
    .TTTTT.
    ''', {'.': None, 'T': 't_out', 'a': 'k_lt', 'b': 'k_base', 'c': 'k_dk'})
    img.paste(trunk, 5, 26)
    for x in range(4, 12):
        if img.p[30][x] is None:
            img.p[30][x] = 'g_dk'
    fill_grass(img)
    return img


# ---------------------------------------------------------------- ledges
#
# Rows (top to bottom): grass plateau, a rounded grass lip (light rim,
# hanging tufts), a dark rim line, a 4px earth face and a shadow line where
# the face meets the lower ground. Tiles horizontally; LEDGE_L/R round the
# lip off at the ends.

LIP_Y = 5        # first lip row
FACE = 4         # earth face rows


def _ledge_column(x):
    col = {}
    col[LIP_Y] = 'g_lt' if x % 6 else 'g_hi'
    col[LIP_Y + 1] = 'g_base'
    col[LIP_Y + 2] = 'g_mid' if x % 4 != 1 else 'g_base'
    y = LIP_Y + 3
    col[y] = 'g_dkr'
    for i in range(FACE):
        c = 's_dk'
        if i == 0:
            c = 's_mid' if x % 3 else 's_base'
        elif i == FACE - 1:
            c = 'g_dkr' if x % 5 else 's_dk'
        if x % 7 == 4 and i == 1:
            c = 's_mid'
        col[y + 1 + i] = c
    # grass tufts hanging over the rim
    if x % 4 == 1:
        col[y] = 'g_mid'
        col[y + 1] = 'g_dkr'
    col[y + 1 + FACE] = 'g_dkr'
    # shadow cast on the lower ground
    col[y + 2 + FACE] = 'g_dk'
    col[y + 3 + FACE] = 'g_mid' if x % 2 else 'g_dk'
    return col


def ledge_img(ends=None):
    """Grass plateau with a lip and an earth face along the bottom edge
    (drop to the south). ends: 'L' or 'R' to round off one end."""
    img = Img(16, 16)
    tex_fill(img, GRASS_A)
    for x in range(16):
        for y, c in _ledge_column(x).items():
            img.p[y][x] = c
    if ends:
        # columns before the start are grass; the first columns curve down
        # like the end of a rounded kerb
        prof = {0: None, 1: None, 2: None, 3: 3, 4: 1, 5: 0}
        for u, cut in prof.items():
            x = u if ends == 'L' else 15 - u
            for y in range(LIP_Y, 16):
                if cut is None:
                    img.p[y][x] = GRASS_A.p[y][x]
            if cut is None:
                continue
            # lower the lip by `cut` rows: shift this column down
            col = _ledge_column(x)
            for y in range(LIP_Y, 16):
                img.p[y][x] = GRASS_A.p[y][x]
            for y, c in col.items():
                yy = y + cut
                if yy <= 15 - (1 if cut else 0) and y <= LIP_Y + 3 + FACE:
                    img.p[yy][x] = c
            img.p[LIP_Y + cut][x] = 'g_lt' if cut < 3 else 'g_base'
            # side rim of the curve
            if cut >= 1:
                img.p[LIP_Y + cut - 1][x] = 'g_base'
            if u == 3:
                for y in range(LIP_Y + cut, 16):
                    if img.p[y][x] in ('s_base', 's_mid', 's_hi'):
                        img.p[y][x] = 's_dk'
                    if img.p[y][x] in ('g_lt', 'g_hi'):
                        img.p[y][x] = 'g_base'
            img.p[15][x] = 'g_dkr' if u > 3 else 'g_dk'
    return img


# ---------------------------------------------------------------- cliffs

ROCK = {'.': None, 'T': 't_out', 'a': 'k_lt', 'b': 'k_base', 'c': 'k_dk',
        'g': 'g_base', 'l': 'g_lt', 'h': 'g_hi', 'm': 'g_mid', 'd': 'g_dk', 'D': 'g_dkr'}


def rock_tex(seeds, w=16, h=16, sy=1.7, seed=0):
    """Seamless rock face: wrapped Voronoi slabs (wider than tall), each lit
    on its top/left edge, shaded bottom/right, with dark crevices."""
    def owner(x, y):
        best, bi = 1e9, -1
        for i, (px, py) in enumerate(seeds):
            dx = (x + 0.5 - px + w / 2) % w - w / 2
            dy = ((y + 0.5 - py + h / 2) % h - h / 2) * sy
            d = dx * dx + dy * dy
            if d < best:
                best, bi = d, i
        return bi
    o = [[owner(x, y) for x in range(w)] for y in range(h)]
    img = Img(w, h)
    for y in range(h):
        for x in range(w):
            me = o[y][x]
            right = o[y][(x + 1) % w]
            down = o[(y + 1) % h][x]
            up = o[(y - 1) % h][x]
            left = o[y][(x - 1) % w]
            down2 = o[(y + 2) % h][x]
            if right != me or down != me:
                c = 't_out'
            elif up != me or left != me:
                c = 'k_lt'
            elif down2 != me:
                c = 'k_dk'
            else:
                c = 'k_base'
                hh = hash2(x, y, 5 + seed) & 15
                if hh == 0:
                    c = 'k_dk'
                elif hh == 1:
                    c = 'k_lt'
            img.p[y][x] = c
    return img


CLIFF_SEEDS = [(4, 2), (12, 3), (8, 9), (1, 10), (13, 13.5)]
CLIFF_FACE = rock_tex(CLIFF_SEEDS)


def cliff_img():
    img = CLIFF_FACE.copy()
    top = G('''
    lhllllllhlllllll
    gggggggggggggggg
    ggmgggggggmggggg
    mgmmgmgmmgmmgmgm
    DmDDmDDDDmDDDmDD
    ''', ROCK)
    img.paste(top, 0, 0)
    for x in range(16):
        if img.p[5][x] in ('k_base', 'k_dk'):
            img.p[5][x] = 'k_lt'
    for x in (2, 9, 13):
        img.p[5][x] = 'g_mid'
        img.p[6][x] = 'g_dkr'
    return img


# ---------------------------------------------------------------- ground

def sand_img(seed=0, extras=False):
    img = Img(16, 16, 's_base')
    # wind ripples: short soft arcs
    for (x0, y0, n) in ((1, 2, 5), (9, 5, 6), (3, 9, 4), (10, 12, 5), (0, 14, 3)):
        for i in range(n):
            x = (x0 + i) % 16
            y = y0 + (1 if 0 < i < n - 1 else 0)
            img.p[y % 16][x] = 's_mid'
            if 0 < i < n - 1:
                img.p[(y - 1) % 16][x] = 's_hi' if i % 2 else 's_base'
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 31 + seed) & 255
            if h < 8 and img.p[y][x] == 's_base':
                img.p[y][x] = 's_mid'
            elif h > 250 and img.p[y][x] == 's_base':
                img.p[y][x] = 's_hi'
    if extras:
        shell = G('''
        .hh.
        hwwh
        rhhr
        ''', {'.': None, 'h': 'r_hi', 'w': 'w_hi', 'r': 'r_base'})
        img.paste(shell, 5, 6)
        for (x, y) in ((12, 2), (2, 12), (13, 10)):
            img.p[y][x] = 'r_base'
            img.p[y][x + 1] = 'r_dk'
            img.p[y - 1][x] = 'r_hi'
    return img


def dirt_img():
    img = Img(16, 16, 's_mid')
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 71) & 63
            if h < 6:
                img.p[y][x] = 's_dk'
            elif h < 11:
                img.p[y][x] = 's_base'
            elif h == 63:
                img.p[y][x] = 's_hi'
    for (x, y) in ((3, 4), (11, 9), (6, 13)):
        img.p[y][x] = 's_hi'
        img.p[y][x + 1] = 's_base'
        img.p[y + 1][x] = 's_dk'
        img.p[y + 1][x + 1] = 's_dk'
    return img


def meadow_img():
    img = GRASS_B.copy()
    clover = G('''
    .l.
    lml
    .d.
    ''', {'.': None, 'l': 'g_lt', 'm': 'g_mid', 'd': 'g_dk'})
    for (x, y) in ((2, 1), (9, 3), (5, 8), (12, 10), (1, 12), (8, 13)):
        img.paste(clover, x, y)
    flower = G('''
    .w.
    wyw
    .m.
    ''', {'.': None, 'w': 'white', 'y': 'f_yel', 'm': 'g_mid'})
    for (x, y) in ((13, 1), (4, 4), (10, 8), (4, 12)):
        img.paste(flower, x, y)
    return img


def forest_img(seed=0):
    """Shady forest floor: dark grass with a moss cushion and a root/twig.
    Features are kept small and low-contrast so the 16px repeat is hidden."""
    img = Img(16, 16, 'g_mid')
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 57 + seed) & 255
            if h < 46:
                img.p[y][x] = 'g_dk'
            elif h < 52:
                img.p[y][x] = 'g_base'
            elif h > 249:
                img.p[y][x] = 'g_dkr'
    moss = G('''
    .tl.
    tlhl
    .tt.
    ''', {'.': None, 'l': 't_lt', 'h': 't_hi', 't': 't_base'})
    root = G('''
    cc..
    .ccc
    ''', {'.': None, 'c': 'k_dk'})
    if seed == 0:
        img.paste(moss, 2, 3)
        img.paste(root, 9, 11)
        img.p[8][12] = 't_base'
    else:
        img.paste(moss, 10, 9)
        img.p[3][4] = 'k_dk'
        img.p[3][5] = 'k_base'
        img.p[4][6] = 'k_dk'
        for (x, y) in ((12, 2), (1, 13)):
            img.p[y][x] = 'g_dkr'
    return img


# ---------------------------------------------------------------- reeds

def reeds_layers():
    """Cattails at the lakeshore: tall stalks with brown heads over marshy
    ground; the top layer holds the front stalks (legs peek through)."""
    bottom = Img(16, 16, 'g_dk')
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 91) & 15
            if h < 4:
                bottom.p[y][x] = 'g_dkr'
            elif h == 15:
                bottom.p[y][x] = 'g_mid'
    head = G('''
    .l.
    Tab
    Tab
    Tbc
    Tbc
    .t.
    ''', {'.': None, 'T': 't_out', 'a': 'k_lt', 'b': 'k_base', 'c': 'k_dk', 'l': 't_lt',
         't': 't_base'})
    # back stalks: (x, top_y, cattail?)
    stalks = [(2, 1, True), (5, 4, False), (8, 0, True), (12, 2, True), (14, 6, False)]
    for (x, ty, cat) in stalks:
        for y in range(ty, 16):
            bottom.p[y][x] = 't_base'
            bottom.p[y][(x + 1) % 16] = 't_mid'
        if cat:
            bottom.paste(head, x - 1, ty)
        else:
            bottom.p[ty][x] = 't_lt'
    top = Img(16, 16)
    blades = [(0, 8, 1), (4, 10, -1), (7, 9, 1), (11, 10, 1), (13, 8, -1)]
    for (x, ty, lean) in blades:
        for y in range(ty, 16):
            xx = x + (lean if y < ty + 2 else 0)
            top.p[y][xx % 16] = 't_lt' if y < ty + 3 else 't_base'
            if top.p[y][(xx + 1) % 16] is None:
                top.p[y][(xx + 1) % 16] = 't_mid'
        top.p[ty][(x + lean) % 16] = 't_hi'
    bottom.paste(top, 0, 0)
    return bottom, top


def wild_images():
    tall_b, tall_t = tallgrass_layers()
    reeds_b, reeds_t = reeds_layers()
    tree = tree_img()
    pine = pine_img()
    return {
        'GRASS': (GRASS_A.copy(), None), 'GRASS2': (GRASS_B.copy(), None),
        'GRASS3': (GRASS_C.copy(), None),
        'TALLGRASS': (tall_b, tall_t),
        'TREE_TOP': (tree.crop(0, 0, 16, 16), None), 'TREE_BOTTOM': (tree.crop(0, 16, 16, 16), None),
        'PINE_TOP': (pine.crop(0, 0, 16, 16), None), 'PINE_BOTTOM': (pine.crop(0, 16, 16, 16), None),
        'LEDGE': (ledge_img(), None), 'SAND': (sand_img(), None),
        'FOREST': (forest_img(), None), 'FOREST2': (forest_img(1), None),
        'REEDS': (reeds_b, reeds_t), 'STONE': (STONE.copy(), None),
        'LEDGE_L': (ledge_img('L'), None), 'LEDGE_R': (ledge_img('R'), None),
        'CLIFF': (cliff_img(), None), 'CLIFF_FACE': (CLIFF_FACE.copy(), None),
        'DIRT': (dirt_img(), None), 'MEADOW': (meadow_img(), None),
        'SAND2': (sand_img(1, extras=True), None),
    }

