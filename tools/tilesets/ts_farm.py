"""The 'farm' tileset: WILLOW ACRE (docs/EXPANSION.md 7.2, owner: FARM).

Legend (map characters, world/farm/data.h):

    .  grass (3 variants)          r / y  red / yellow flowers (animated)
    =  sandy path (autotiled)       ~      pond water (autotiled, animated)
    x  packed dirt yard            T / t  tree top / bottom (border trees)
    s  field soil (A_SOIL: till it with the HOE)
    o  orchard mound (A_SOIL: saplings only, no tilling needed)
    m  berry mound (solid; a wild berry patch OBJ_BERRY sits on it)
    -  fence, post + rails to the right (also the NW corner)
    ]  fence end post (rails come from the left; NE corner)
    |  fence, vertical run
    {  SW corner (post + rails right + joins the run above)
    }  SE corner (end post + joins the run above)

Soil states and crops are not map characters: farm.c draws them over A_SOIL
cells at run time through dyn_cell() with these metatiles (MT_FA_*):

    TILLED, TILLED_WET, TILLED_FERT, TILLED_WET_FERT   ground (BG0)
    SEEDED, SPROUT, <CROP>_GROW, <CROP>_RIPE, SAPLING  overlays (BG2)
    YOUNG_/FRUIT_/APPLE_/PEACH_ TOP + BOTTOM           fruit trees: the
        bottom stands on the orchard cell (BG2), the crown is drawn on the
        top layer (BG3) of the cell above
    SPRINKLER                                          placed sprinkler

Palette banks:
    0 grass, path, flowers      1 water and shore     2 border trees
    3 village props (decor)     4 soil (dry, wet, fertiliser specks)
    5 farmhouse (red roof, clapboard, wood)
    6 crops A (reds, oranges, yellows)   7 crops B (blues, purples, pinks, glow)
Every crop and decor is drawn on transparency (the art lint checks it).
"""

import math

from pixelart import Img, G, hash2, shade_clumps

USES_DECOR = ['SIGNPOST', 'BARREL', 'CRATE', 'SACKS', 'HAY_BALE', 'WATER_TROUGH', 'WHEELBARROW',
              'SCARECROW', 'BEEHIVE', 'WOODPILE', 'STUMP', 'ROCK', 'BUSH', 'LOG', 'PUMPKINS',
              'SMALL_FLOWERS', 'PEBBLES', 'CART', 'BENCH']

FARM_COLORS = {
    # soil: dry / wet / fertiliser specks
    'fm_so_hi': (212, 164, 112),
    'fm_so_lt': (184, 132, 84),
    'fm_so': (156, 106, 64),
    'fm_so_md': (126, 84, 52),
    'fm_so_dk': (96, 62, 40),
    'fm_we_lt': (136, 94, 62),
    'fm_we': (108, 72, 48),
    'fm_we_md': (86, 56, 38),
    'fm_we_dk': (62, 40, 30),
    'fm_we_gl': (168, 200, 216),
    'fm_fe_a': (236, 224, 184),
    'fm_fe_b': (70, 96, 52),
    # crops: shared
    'fm_out': (44, 40, 32),
    'fm_lf_hi': (170, 226, 104),
    'fm_lf': (100, 180, 72),
    'fm_lf_dk': (46, 124, 58),
    'fm_bk': (140, 94, 56),
    # crops A
    'fm_hl': (255, 250, 228),
    'fm_rd_hi': (255, 144, 120),
    'fm_rd': (224, 56, 48),
    'fm_rd_dk': (150, 30, 42),
    'fm_or_hi': (255, 204, 120),
    'fm_or': (240, 136, 40),
    'fm_or_dk': (180, 82, 24),
    'fm_ye_hi': (255, 246, 164),
    'fm_ye': (248, 208, 48),
    'fm_ye_dk': (198, 142, 24),
    # crops B
    'fm_bl_hi': (176, 216, 255),
    'fm_bl': (80, 136, 232),
    'fm_bl_dk': (46, 70, 168),
    'fm_pu_hi': (228, 180, 255),
    'fm_pu': (164, 98, 216),
    'fm_pu_dk': (98, 56, 150),
    'fm_pk_hi': (255, 214, 184),
    'fm_pk': (250, 152, 124),
    'fm_pk_dk': (200, 92, 92),
    'fm_gl': (214, 255, 196),
}

COMMON = ['fm_out', 'fm_lf_hi', 'fm_lf', 'fm_lf_dk', 'fm_bk']
BANK_SOIL = ['g_base', 'g_mid', 'g_dk', 'fm_so_hi', 'fm_so_lt', 'fm_so', 'fm_so_md', 'fm_so_dk',
             'fm_we_lt', 'fm_we', 'fm_we_md', 'fm_we_dk', 'fm_we_gl', 'fm_fe_a', 'fm_fe_b']
BANK_HOUSE = ['g_base', 'g_dk', 'b_out', 'rf_hi', 'rf_lt', 'rf_base', 'rf_dk', 'rf_dkr',
              'wl_hi', 'wl_base', 'wl_dk', 'wd_lt', 'wd_base', 'wd_dk', 'gl_base']
BANK_CROPS_A = COMMON + ['fm_hl', 'fm_rd_hi', 'fm_rd', 'fm_rd_dk', 'fm_or_hi', 'fm_or', 'fm_or_dk',
                         'fm_ye_hi', 'fm_ye', 'fm_ye_dk']
BANK_CROPS_B = COMMON + ['fm_bl_hi', 'fm_bl', 'fm_bl_dk', 'fm_pu_hi', 'fm_pu', 'fm_pu_dk',
                         'fm_pk_hi', 'fm_pk', 'fm_pk_dk', 'fm_gl']

# Crop order = CROP_* in src/game/farm.c (and the IK_PLANT params in items/farm.inc).
CROPS = ['GLOWBERRY', 'EMBERBERRY', 'TIDEBERRY', 'RADISH', 'CARROT', 'POTATO', 'PUMPKIN',
         'CHILI', 'TOMATO', 'CORN', 'SUNFLOWER', 'MOTEBLOOM']
TREES = ['YOUNG', 'FRUIT', 'APPLE', 'PEACH']

GROUND_TERRAIN = ['GRASS', 'GRASS2', 'GRASS3', 'FLOWER_RED', 'FLOWER_YELLOW', 'DIRT',
                  'SOIL', 'SOIL2', 'TILLED', 'TILLED_WET', 'TILLED_FERT', 'TILLED_WET_FERT',
                  'ORCHARD', 'BERRY_MOUND']
FENCES = ['FENCE_H', 'FENCE_V', 'FENCE_END', 'FENCE_SW', 'FENCE_SE']
OVERLAYS = (['TREE_TOP', 'TREE_BOTTOM'] + FENCES + ['SEEDED', 'SPROUT', 'SAPLING'] +
            [c + s for c in CROPS for s in ('_GROW', '_RIPE')] +
            [t + s for t in TREES for s in ('_TOP', '_BOTTOM')] + ['SPRINKLER'])
FARM_TERRAIN = GROUND_TERRAIN + OVERLAYS

DOC = {
    'SOIL': 'field soil (A_SOIL): the HOE tills it',
    'TILLED': 'tilled soil (farm.c draws it over A_SOIL cells); _WET watered, _FERT fertilised',
    'ORCHARD': 'orchard mound (A_SOIL): saplings grow here',
    'BERRY_MOUND': 'mound under a wild berry patch (solid)',
    'SEEDED': 'crop overlay: just planted',
    'SPROUT': 'crop overlay: sprout (every crop)',
    'YOUNG_TOP': 'fruit tree crown, drawn on the top layer of the cell above the orchard cell',
    'SPRINKLER': 'placed sprinkler (waters the 8 plots around it)',
}

# ---------------------------------------------------------------------------
# small drawing helpers
# ---------------------------------------------------------------------------


def outline(img, col='fm_out', skip=()):
    """1px outline (4-neighbour) around the opaque pixels."""
    o = img.copy()
    for y in range(img.h):
        for x in range(img.w):
            if img.p[y][x] is not None:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c = img.get(x + dx, y + dy)
                if c is not None and c not in skip:
                    o.p[y][x] = col
                    break
    return o


def ell(img, cx, cy, rx, ry, ramp, light=(-0.6, -0.8), dither=0):
    """Shaded ellipse; ramp = light .. dark."""
    n = len(ramp)
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            d = nx * nx + ny * ny
            if d > 1.0:
                continue
            b = (nx * light[0] + ny * light[1]) * 0.8 + (1 - d) * 0.35
            t = (0.55 - b) * (n - 1)
            if dither:
                t += ((hash2(x, y, dither) & 255) / 255.0 - 0.5) * 0.6
            img.set(x, y, ramp[max(0, min(n - 1, int(round(t))))])


def line(img, x0, y0, x1, y1, c):
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        img.set(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def leaf(img, bx, by, ang, length, width, cols=('fm_lf_hi', 'fm_lf', 'fm_lf_dk')):
    """A pointed leaf from (bx, by) toward angle ang (degrees, 0 = up)."""
    a = math.radians(ang)
    ux, uy = math.sin(a), -math.cos(a)
    for y in range(int(by - length - 2), int(by + length + 2)):
        for x in range(int(bx - length - 2), int(bx + length + 2)):
            px, py = x + 0.5 - bx, y + 0.5 - by
            u = px * ux + py * uy
            v = -px * uy + py * ux
            if u < 0 or u > length:
                continue
            w = width * math.sin(math.pi * min(1.0, u / length)) ** 0.8
            if abs(v) > w:
                continue
            c = cols[0] if v < -w * 0.25 else (cols[2] if v > w * 0.45 else cols[1])
            img.set(x, y, c)


def bush(w=16, h=16, big=True, seed=5):
    if big:
        clumps = [(8.0, 7.0, 4.6, 4.0), (4.8, 10.0, 3.8, 3.4), (11.2, 10.0, 3.8, 3.4),
                  (8.0, 11.4, 4.8, 2.8)]
    else:
        clumps = [(8.0, 9.5, 3.8, 3.2), (5.4, 11.6, 2.8, 2.2), (10.6, 11.6, 2.8, 2.2)]
    img, _ = shade_clumps(w, h, clumps, ['fm_lf_hi', 'fm_lf', 'fm_lf', 'fm_lf_dk'], 'fm_out',
                          seed=seed, clip=lambda x, y: 1 <= x <= 14 and y <= 14)
    return img


def dots(img, pts, ramp, big=False):
    """Round fruit: ramp = (hi, base, dark)."""
    for (x, y) in pts:
        if big:
            for (dx, dy, k) in ((0, 0, 1), (1, 0, 1), (0, 1, 2), (1, 1, 2), (-1, 0, 1), (0, -1, 1),
                                (-1, 1, 2), (1, -1, 1), (-1, -1, 0)):
                img.set(x + dx, y + dy, ramp[k])
            img.set(x - 1, y - 1, ramp[0])
        else:
            img.set(x, y, ramp[1])
            img.set(x + 1, y, ramp[1])
            img.set(x, y + 1, ramp[2])
            img.set(x + 1, y + 1, ramp[2])
            img.set(x, y, ramp[0])


# ---------------------------------------------------------------------------
# ground: soil states, mounds
# ---------------------------------------------------------------------------


def soil_img(seed=0):
    """Untilled field soil: flat, pebbly, with a few grass sprigs."""
    img = Img(16, 16, 'fm_so_lt')
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 91 + seed) & 63
            if h < 7:
                img.p[y][x] = 'fm_so'
            elif h < 9:
                img.p[y][x] = 'fm_so_md'
            elif h > 60:
                img.p[y][x] = 'fm_so_hi'
    for (x, y) in ((3, 4), (11, 11)) if not seed else ((9, 3), (4, 12)):
        img.set(x, y, 'fm_so_hi')
        img.set(x + 1, y, 'fm_so_lt')
        img.set(x, y + 1, 'fm_so_md')
        img.set(x + 1, y + 1, 'fm_so_dk')
    sprig = (12, 5) if not seed else (2, 7)
    x, y = sprig
    for (dx, dy, c) in ((0, 0, 'g_mid'), (1, -1, 'g_base'), (-1, -1, 'g_base'), (0, 1, 'g_dk'),
                        (1, 0, 'g_dk')):
        img.set(x + dx, y + dy, c)
    return img


def tilled_img(wet=False, fert=False):
    """Furrowed soil: two ridges per cell, lit from the top."""
    if wet:
        ridge = ['fm_we_lt', 'fm_we_lt', 'fm_we', 'fm_we', 'fm_we_md', 'fm_we_dk', 'fm_we_md', 'fm_we']
    else:
        ridge = ['fm_so_hi', 'fm_so_lt', 'fm_so_lt', 'fm_so', 'fm_so_md', 'fm_so_dk', 'fm_so_md', 'fm_so']
    img = Img(16, 16)
    for y in range(16):
        for x in range(16):
            c = ridge[y % 8]
            h = hash2(x, y, 17) & 31
            if y % 8 in (1, 2) and h < 5:
                c = ridge[3]
            if y % 8 == 3 and h < 4:
                c = ridge[0]
            if y % 8 == 5 and h > 28:
                c = ridge[4]
            img.p[y][x] = c
    if wet:
        for (x, y) in ((3, 1), (4, 1), (12, 9), (13, 9), (8, 2), (1, 10)):
            img.set(x, y, 'fm_we_gl')
    if fert:
        for (x, y) in ((2, 2), (6, 1), (10, 3), (13, 1), (4, 10), (8, 9), (12, 11), (15, 10),
                       (1, 13), (9, 12)):
            img.set(x, y, 'fm_fe_a')
        for (x, y) in ((7, 2), (3, 11), (14, 3), (11, 10)):
            img.set(x, y, 'fm_fe_b')
    return img


def mound_img():
    """A round soil mound in grass (orchard spots, berry patches)."""
    img = Img(16, 16, 'g_base')
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 23) & 63
            if h < 5:
                img.p[y][x] = 'g_mid'
            elif h > 61:
                img.p[y][x] = 'g_dk'
    cx, cy, rx, ry = 8.0, 9.0, 6.6, 5.4
    for y in range(16):
        for x in range(16):
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            d = nx * nx + ny * ny
            if d > 1.0:
                if d < 1.35 and ny > 0.2:
                    img.p[y][x] = 'g_dk'
                continue
            b = -(nx * 0.5 + ny * 0.8) + 0.2
            c = 'fm_so_hi' if b > 0.55 else 'fm_so_lt' if b > 0.05 else 'fm_so' if b > -0.45 else 'fm_so_md'
            if d > 0.78 and ny > 0.1:
                c = 'fm_so_dk'
            img.p[y][x] = c
    for (x, y) in ((6, 7), (10, 10), (8, 12)):
        img.set(x, y, 'fm_so_md')
    return img


# ---------------------------------------------------------------------------
# fences (overlays in the village FENCE style: O outline, A/B/K wood)
# ---------------------------------------------------------------------------

FL = {'.': None, 'O': 'b_out', 'A': 'wd_lt', 'B': 'wd_base', 'K': 'wd_dk'}

FENCE_H = G('''
................
................
................
.OOOO...........
.OABO...........
.OABOOOOOOOOOOOO
.OABOAAAAAAAAAAA
.OABOBBBBBBBBBBB
.OABOOOOOOOOOOOO
.OABO...........
.OABOOOOOOOOOOOO
.OABOAAAAAAAAAAA
.OABOKKKKKKKKKKK
.OABOOOOOOOOOOOO
.OABO...........
.OOOO...........
''', FL)

FENCE_END = G('''
................
................
................
.OOOO...........
.OABO...........
OOABO...........
AOABO...........
BOABO...........
OOABO...........
.OABO...........
OOABO...........
AOABO...........
KOABO...........
OOABO...........
.OABO...........
.OOOO...........
''', FL)

STUB = G('''
.OABO...........
.OABO...........
.OABO...........
''', FL)


def with_stub(img):
    o = img.copy()
    o.paste(STUB, 0, 0)
    return o


def fence_v():
    img = Img(16, 16)
    img.paste(G('''
................
................
................
.OOOO...........
.OABO...........
.OABO...........
.OABO...........
.OABO...........
.OABO...........
.OABO...........
.OABO...........
.OABO...........
.OABO...........
.OABO...........
.OABO...........
.OOOO...........
''', FL), 0, 0)
    return with_stub(img)


# ---------------------------------------------------------------------------
# crops (16x16 overlays on transparency)
# ---------------------------------------------------------------------------

RED = ('fm_rd_hi', 'fm_rd', 'fm_rd_dk')
ORANGE = ('fm_or_hi', 'fm_or', 'fm_or_dk')
YELLOW = ('fm_ye_hi', 'fm_ye', 'fm_ye_dk')
BLUE = ('fm_bl_hi', 'fm_bl', 'fm_bl_dk')
PURPLE = ('fm_pu_hi', 'fm_pu', 'fm_pu_dk')
PINK = ('fm_pk_hi', 'fm_pk', 'fm_pk_dk')
GLOW = ('fm_gl', 'fm_gl', 'fm_bl_hi')


def seeded():
    img = Img(16, 16)
    for (x, y) in ((4, 9), (8, 11), (11, 8)):
        img.set(x, y, 'fm_out')
        img.set(x + 1, y, 'fm_out')
        img.set(x, y - 1, 'fm_ye_hi')
        img.set(x + 1, y - 1, 'fm_ye_dk')
    return img


def sprout():
    img = Img(16, 16)
    line(img, 8, 13, 8, 9, 'fm_lf_dk')
    leaf(img, 8, 9, -60, 4.5, 1.8)
    leaf(img, 8.5, 9, 60, 4.5, 1.8)
    return outline(img)


def rosette(n=5, length=6.0, width=2.2, base=(8, 12), spread=110):
    img = Img(16, 16)
    for i in range(n):
        ang = -spread / 2 + spread * i / (n - 1)
        leaf(img, base[0] + 0.5, base[1], ang, length * (0.85 if i % 2 else 1.0), width)
    return img


def fronds(base=(8, 12)):
    img = Img(16, 16)
    for ang in (-40, -15, 12, 38):
        a = math.radians(ang)
        tip = (base[0] + 8 * math.sin(a), base[1] - 8 * math.cos(a))
        line(img, base[0], base[1], int(round(tip[0])), int(round(tip[1])), 'fm_lf_dk')
        for k in (0.45, 0.7, 0.95):
            px, py = base[0] + (tip[0] - base[0]) * k, base[1] + (tip[1] - base[1]) * k
            leaf(img, px, py, ang - 55, 2.6, 1.0)
            leaf(img, px, py, ang + 55, 2.6, 1.0)
    return img


def crop_img(name, ripe):
    img = Img(16, 16)
    if name in ('GLOWBERRY', 'EMBERBERRY', 'TIDEBERRY'):
        img = bush(big=ripe, seed=CROPS.index(name) + 3)
        if ripe:
            ramp = {'GLOWBERRY': GLOW, 'EMBERBERRY': ('fm_or_hi', 'fm_or', 'fm_rd'),
                    'TIDEBERRY': BLUE}[name]
            dots(img, [(4, 7), (9, 5), (11, 9), (6, 10), (8, 12), (12, 12), (3, 11)], ramp)
            if name == 'GLOWBERRY':
                for (x, y) in ((2, 5), (13, 6), (7, 2)):
                    img.set(x, y, 'fm_gl')
        return img
    if name == 'RADISH':
        img = rosette(5, 6.5 if ripe else 5.0, 2.2)
        if ripe:
            ell(img, 8.5, 12.8, 3.4, 2.4, list(RED))
            img.set(7, 12, 'fm_hl')
        return outline(img)
    if name == 'CARROT':
        img = fronds()
        if not ripe:
            img = Img(16, 16)
            small = fronds((8, 13))
            for y in range(16):
                for x in range(16):
                    if small.p[y][x] is not None and y >= 7:
                        img.p[y][x] = small.p[y][x]
        else:
            ell(img, 8.5, 13.0, 3.0, 2.0, list(ORANGE))
            img.set(7, 12, 'fm_or_hi')
        return outline(img)
    if name == 'POTATO':
        clumps = [(8.0, 8.5, 4.4, 3.6), (5.0, 11.0, 3.4, 3.0), (11.0, 11.0, 3.4, 3.0)]
        if not ripe:
            clumps = [(8.0, 10.0, 3.6, 3.0), (5.6, 12.0, 2.6, 2.0), (10.4, 12.0, 2.6, 2.0)]
        img, _ = shade_clumps(16, 16, clumps, ['fm_lf_hi', 'fm_lf', 'fm_lf_dk'], 'fm_out', seed=9,
                              clip=lambda x, y: 1 <= x <= 14 and y <= 14)
        if ripe:
            for (x, y) in ((6, 6), (10, 7), (8, 9)):
                img.set(x, y, 'fm_pu_hi')
                img.set(x + 1, y, 'fm_pu')
                img.set(x, y + 1, 'fm_pu')
                img.set(x + 1, y + 1, 'fm_gl')
            ell(img, 12.5, 13.5, 2.2, 1.6, ['fm_pk_hi', 'fm_bk', 'fm_bk'])
            img = outline(img, skip=('fm_out',))
        return img
    if name == 'PUMPKIN':
        if not ripe:
            leaf(img, 8, 12, -75, 6.5, 3.0)
            leaf(img, 8, 12, 70, 6.0, 3.0)
            leaf(img, 8, 12, -5, 5.0, 2.8)
            line(img, 3, 13, 13, 13, 'fm_lf_dk')
            img.set(13, 12, 'fm_lf_dk')
            img.set(14, 11, 'fm_lf_dk')
            return outline(img)
        leaf(img, 5, 10, -60, 5.0, 2.6)
        ell(img, 8.5, 10.5, 6.2, 4.6, list(ORANGE))
        for x in (6, 11):
            for y in range(8, 14):
                if img.get(x, y) in ORANGE:
                    img.set(x, y, 'fm_or_dk')
        for y in range(8, 12):
            if img.get(8, y) in ORANGE:
                img.set(8, y, 'fm_or_hi' if y < 10 else 'fm_or')
        line(img, 8, 5, 9, 6, 'fm_lf_dk')
        img.set(9, 4, 'fm_lf_dk')
        return outline(img)
    if name == 'CHILI':
        line(img, 8, 13, 8, 5 if ripe else 7, 'fm_lf_dk')
        for (y, ang) in ((10, -70), (9, 70), (7, -50), (6, 50)):
            if not ripe and y < 8:
                continue
            leaf(img, 8, y, ang, 4.5, 1.6)
        if ripe:
            for (x, y) in ((4, 9), (11, 8), (6, 11), (10, 11)):
                img.set(x, y, 'fm_lf_dk')
                img.set(x, y + 1, 'fm_rd')
                img.set(x, y + 2, 'fm_rd')
                img.set(x + (1 if x < 8 else -1), y + 3, 'fm_rd_dk')
                img.set(x + (1 if x < 8 else 0), y + 1, 'fm_rd_hi')
        return outline(img)
    if name == 'TOMATO':
        line(img, 8, 14, 8, 1, 'fm_bk')
        img.set(8, 0, 'fm_bk')
        for (y, ang) in ((12, -70), (11, 70), (8, -55), (7, 60), (4, -45), (3, 40)):
            if not ripe and y < 6:
                continue
            leaf(img, 8, y, ang, 4.2, 1.7)
        if ripe:
            dots(img, [(4, 8), (11, 6), (5, 12), (11, 11)], RED, big=True)
        return outline(img)
    if name == 'CORN':
        top = 2 if ripe else 5
        line(img, 8, 14, 8, top, 'fm_lf_dk')
        line(img, 7, 14, 7, top + 2, 'fm_lf')
        for (y, ang, ln) in ((12, -60, 6.5), (10, 65, 6.5), (7, -40, 5.5), (5, 40, 5.0)):
            if y < top + 2:
                continue
            leaf(img, 8, y, ang, ln, 1.4)
        if ripe:
            ell(img, 10.5, 8.0, 1.6, 3.2, list(YELLOW))
            leaf(img, 9.5, 11, 15, 5.0, 1.2)
            for (x, y) in ((7, 1), (8, 0), (9, 1), (6, 2), (10, 2)):
                img.set(x, y, 'fm_ye_dk')
        return outline(img)
    if name == 'SUNFLOWER':
        line(img, 8, 14, 8, 6, 'fm_lf_dk')
        leaf(img, 8, 11, -65, 4.5, 2.0)
        leaf(img, 8, 10, 65, 4.5, 2.0)
        if ripe:
            for k in range(10):
                a = k * math.pi / 5
                for r in (3.4, 4.4):
                    img.set(int(round(8 + r * math.cos(a))), int(round(5 + r * math.sin(a) * 0.9)),
                            'fm_ye' if r < 4 else 'fm_ye_hi')
            ell(img, 8.5, 5.3, 4.6, 4.0, ['fm_ye_hi', 'fm_ye', 'fm_ye', 'fm_ye_dk'])
            ell(img, 8.5, 5.5, 2.2, 2.0, ['fm_bk', 'fm_bk', 'fm_out'])
            img.set(7, 4, 'fm_ye_dk')
        else:
            ell(img, 8.5, 5.5, 1.8, 1.8, ['fm_lf_hi', 'fm_lf', 'fm_lf_dk'])
        return outline(img, skip=('fm_ye_hi',)) if ripe else outline(img)
    if name == 'MOTEBLOOM':
        line(img, 8, 14, 8, 6, 'fm_lf_dk')
        leaf(img, 8, 12, -60, 4.0, 1.5)
        leaf(img, 8, 11, 60, 4.0, 1.5)
        if ripe:
            for k in range(5):
                a = -math.pi / 2 + k * 2 * math.pi / 5
                ell(img, 8.5 + 2.6 * math.cos(a), 5.5 + 2.4 * math.sin(a), 1.9, 1.9, list(PURPLE))
            ell(img, 8.5, 5.5, 1.3, 1.3, ['fm_gl', 'fm_gl', 'fm_bl_hi'])
            img = outline(img)
            for (x, y) in ((2, 3), (14, 2), (3, 9), (13, 8), (11, 0)):
                img.set(x, y, 'fm_gl')
            return img
        ell(img, 8.5, 5.0, 1.8, 2.6, ['fm_pu_hi', 'fm_pu', 'fm_pu_dk'])
        return outline(img)
    raise KeyError(name)


def sapling():
    img = Img(16, 16)
    line(img, 8, 14, 8, 5, 'fm_bk')
    line(img, 8, 9, 11, 6, 'fm_bk')
    leaf(img, 8, 5, -20, 4.0, 1.8)
    leaf(img, 11, 6, 40, 3.5, 1.6)
    leaf(img, 8, 9, -70, 3.5, 1.5)
    return outline(img)


def tree_img(kind):
    """16x32 fruit tree: YOUNG, FRUIT (grown, resting), APPLE, PEACH."""
    img = Img(16, 32)
    young = kind == 'YOUNG'
    if young:
        for y in range(19, 31):
            img.set(7, y, 'fm_bk')
            img.set(8, y, 'fm_bk' if y % 3 else 'fm_out')
        clumps = [(8.0, 15.0, 5.2, 4.6), (5.4, 18.5, 3.4, 2.8), (10.6, 18.5, 3.4, 2.8)]
    else:
        for y in range(19, 31):
            for x in range(6, 10):
                img.set(x, y, 'fm_out' if x == 9 and y % 4 == 1 else 'fm_bk')
        for (x, y) in ((5, 30), (10, 30), (4, 31), (11, 31)):
            img.set(x, y, 'fm_bk')
        clumps = [(8.0, 8.0, 6.0, 5.4), (4.2, 12.5, 4.0, 4.0), (11.8, 12.5, 4.0, 4.0),
                  (8.0, 14.0, 5.6, 4.4), (4.8, 18.0, 3.8, 3.2), (11.2, 18.0, 3.8, 3.2),
                  (8.0, 19.5, 4.4, 2.8)]
    can, _ = shade_clumps(16, 32, clumps, ['fm_lf_hi', 'fm_lf', 'fm_lf', 'fm_lf_dk'], 'fm_out',
                          seed=11 + TREES.index(kind), clip=lambda x, y: 0 <= x <= 15)
    img.paste(can, 0, 0)
    img = outline(img, skip=('fm_out',))
    if kind == 'APPLE':
        dots(img, [(4, 7), (10, 5), (12, 11), (6, 13), (9, 16), (3, 17), (12, 19)], RED, big=True)
    if kind == 'PEACH':
        dots(img, [(5, 6), (11, 7), (8, 11), (3, 14), (12, 15), (7, 18)], PINK, big=True)
    return img


def sprinkler():
    img = Img(16, 16)
    L = {'.': None, 'O': 'b_out', 'l': 'st_lt', 'm': 'st_mid', 'd': 'st_dk', 'w': 'white',
         'u': 'w_lt', 'U': 'w_base'}
    img.paste(G('''
......u..u......
...u..........u.
.......OO.......
......OlmO......
......OldO......
....OOOlmOOO....
...OwllllmmmO...
..OlllmmmmmmdO..
..OmmmmmmmmddO..
...OddddddddO...
....OOOOOOOO....
''', L), 0, 3)
    return img


# ---------------------------------------------------------------------------
# the farmhouse stamp (96x80 = 6x5 cells, door at col 2 row 4), bank 5
# ---------------------------------------------------------------------------

HL = {'.': None, 'O': 'b_out', 'W': 'wl_hi', 'w': 'wl_base', 'v': 'wl_dk', 'A': 'wd_lt',
      'B': 'wd_base', 'K': 'wd_dk', 'g': 'gl_base', 'G': 'g_base', 's': 'g_dk',
      '1': 'rf_hi', '2': 'rf_lt', '3': 'rf_base', '4': 'rf_dk', '5': 'rf_dkr'}

WINDOW = G('''
OOOOOOOOOOOO
OAAAAAAAAAAO
OAggggAgggKO
OAgWggAggWKO
OAggggAgggKO
OAAAAAAAAAKO
OAggggAgggKO
OAgggWAgggKO
OAggggAgggKO
OKKKKKKKKKKO
OOOOOOOOOOOO
.O4444444O..
''', HL)

DOOR = G('''
..OOOOOOOOOOOO..
..OAAAAAAAAAAO..
..OAOOOOOOOOKO..
..OAOBBBBBBOKO..
..OAOBKKKKBOKO..
..OAOBKggKBOKO..
..OAOBKggKBOKO..
..OAOBKKKKBOKO..
..OAOBBBBBBOKO..
..OAOBBBBWBOKO..
..OAOBBBBKBOKO..
..OAOBBBBBBOKO..
..OAOBKKKKBOKO..
..OAOBBBBBBOKO..
..OAOKKKKKKOKO..
..OOOOOOOOOOOO..
.OAAAAAAAAAAAAO.
.OKKKKKKKKKKKKO.
..OOOOOOOOOOOO..
''', HL)


def farmhouse():
    W_, H_ = 96, 80
    img = Img(W_, H_, 'g_base')
    R = {'1': 'rf_hi', '2': 'rf_lt', '3': 'rf_base', '4': 'rf_dk', '5': 'rf_dkr'}
    # ground shadow
    for x in range(8, 94):
        img.set(x, 77, 'g_dk')
        if x < 92:
            img.set(x, 78, 'g_dk')
    # clapboard walls
    for y in range(38, 72):
        for x in range(5, 91):
            r = (y - 38) % 5
            img.set(x, y, 'wl_hi' if r == 0 else 'wl_dk' if r == 4 else 'wl_base')
        img.set(4, y, 'b_out')
        img.set(91, y, 'b_out')
        img.set(5, y, 'wd_lt')
        img.set(6, y, 'wd_base')
        img.set(89, y, 'wd_base')
        img.set(90, y, 'wd_dk')
    # corner trim + eave shadow
    for x in range(5, 91):
        img.set(x, 38, 'wl_dk')
        img.set(x, 39, 'wl_dk' if x % 2 else 'wl_base')
    # stone-less foundation: a dark wooden sill
    for x in range(4, 92):
        img.set(x, 72, 'b_out')
        img.set(x, 73, 'wd_dk' if x % 6 else 'b_out')
        img.set(x, 74, 'wd_base' if x % 6 else 'b_out')
        img.set(x, 75, 'b_out')
    # windows with flower-less sills (bank 5 only)
    for wx in (10, 58, 74):
        img.paste(WINDOW, wx, 44)
    # door (col 2 of the stamp: x 32..47, the door cell is row 4: y 64..79)
    img.paste(DOOR, 32, 57)
    # roof: a big red hip roof with a hay loft gable
    from_gf = _gf['draw_roof']
    from_gf(img, 1, 94, 4, 39, 6, R)
    # chimney (left) and loft door in the roof
    ch = G('''
OOOOOOOO
O111112O
O222233O
OOOOOOOO
.O3333O.
.O3443O.
.O3343O5
.O3443O5
.O3333O5
.OOOOOO5
..55555.
''', HL)
    img.paste(ch, 14, 0)
    loft = G('''
....OOOOOOOO....
...OAAAAAAAAO...
..OAKBBBBBBKAO..
.OAKBBKBBKBBKAO.
OAKBBBKBBKBBBKAO
OAKBBBKBBKBBBKAO
OAKKKKKKKKKKKKAO
OOOOOOOOOOOOOOOO
''', HL)
    img.paste(loft, 56, 22)
    return img


_gf = {}


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def terrain_images(gf):
    imgs = {
        'GRASS': gf.GRASS_A, 'GRASS2': gf.GRASS_B, 'GRASS3': gf.GRASS_C,
        'DIRT': gf.terrain_wild.dirt_img(),
        'SOIL': soil_img(0), 'SOIL2': soil_img(1),
        'TILLED': tilled_img(), 'TILLED_WET': tilled_img(wet=True),
        'TILLED_FERT': tilled_img(fert=True), 'TILLED_WET_FERT': tilled_img(wet=True, fert=True),
        'ORCHARD': mound_img(), 'BERRY_MOUND': mound_img(),
    }
    tree = gf.tree_img(overlay=True)
    over = {
        'TREE_TOP': tree.crop(0, 0, 16, 16), 'TREE_BOTTOM': tree.crop(0, 16, 16, 16),
        'FENCE_H': FENCE_H, 'FENCE_V': fence_v(), 'FENCE_END': FENCE_END,
        'FENCE_SW': with_stub(FENCE_H), 'FENCE_SE': with_stub(FENCE_END),
        'SEEDED': seeded(), 'SPROUT': sprout(), 'SAPLING': sapling(), 'SPRINKLER': sprinkler(),
    }
    for c in CROPS:
        over[c + '_GROW'] = crop_img(c, False)
        over[c + '_RIPE'] = crop_img(c, True)
    for t in TREES:
        im = tree_img(t)
        over[t + '_TOP'] = im.crop(0, 0, 16, 16)
        over[t + '_BOTTOM'] = im.crop(0, 16, 16, 16)
    return imgs, over


def build(gf, name):
    _gf['draw_roof'] = gf.draw_roof
    gf.register_colors(FARM_COLORS)
    banks = [
        gf.BANK_GROUND,
        ['g_base', 'g_lt', 'g_mid', 'w_hi', 'w_lt', 'w_base', 'w_mid', 'w_dk',
         'r_hi', 'r_base', 'r_dk', 's_hi', 's_base', 's_mid', 'c_dk'],
        gf.BANK_TREES,
        gf.decor_outdoor.TOWN_DECOR_BANK,
        BANK_SOIL, BANK_HOUSE, BANK_CROPS_A, BANK_CROPS_B,
    ]
    gf.check_banks(name, banks)
    ts = gf.TileSet(name, banks)
    out = {'ts': ts, 'meta_b': [], 'meta_t': [], 'terrain': FARM_TERRAIN}
    gf.add_water_anim(ts, out)
    flower_meta = gf.add_flower_anim(ts, out)
    imgs, over = terrain_images(gf)
    for tname in FARM_TERRAIN:
        if tname == 'FLOWER_RED':
            out['meta_b'].append(flower_meta[0])
            out['meta_t'].append([0, 0, 0, 0])
        elif tname == 'FLOWER_YELLOW':
            out['meta_b'].append(flower_meta[1])
            out['meta_t'].append([0, 0, 0, 0])
        elif tname in over:
            gf.add_overlay_terrain(ts, out, tname, over[tname], top=tname.endswith('_TOP'))
        else:
            out['meta_b'].append(ts.meta(imgs[tname], where='farm.' + tname))
            out['meta_t'].append([0, 0, 0, 0])
    gf.add_stamps(ts, out, [
        ('FARMHOUSE', farmhouse(), (5,), 'WILLOW ACRE farmhouse (red roof), door col 2 row 4'),
    ])
    gf.add_path(ts, out)
    attrs = {'SOIL': gf.A_SOIL, 'SOIL2': gf.A_SOIL, 'ORCHARD': gf.A_SOIL,
             'BERRY_MOUND': gf.A_SOLID}
    for t in ('TILLED', 'TILLED_WET', 'TILLED_FERT', 'TILLED_WET_FERT'):
        attrs[t] = gf.A_SOIL
    return gf.finish_tileset(
        out, name, 'FA', attrs=attrs,
        ground=['GRASS', 'GRASS2', 'GRASS3', 'DIRT'], overlay=list(OVERLAYS),
        legend={'.': gf.GRASS_VARIANTS, 'r': 'FLOWER_RED', 'y': 'FLOWER_YELLOW', '=': 'PATH',
                '~': 'WATER', 'T': 'TREE_TOP', 't': 'TREE_BOTTOM', 'x': 'DIRT',
                's': [('SOIL2', 5), ('SOIL', 11)], 'o': 'ORCHARD', 'm': 'BERRY_MOUND',
                '-': 'FENCE_H', ']': 'FENCE_END', '|': 'FENCE_V', '{': 'FENCE_SW',
                '}': 'FENCE_SE'},
        oob='TREE_TOP', default_ground='GRASS', backdrop='ground',
        doors=[('FARMHOUSE', 2, 4)])
