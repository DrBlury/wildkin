"""The 'farm' tileset: WILLOW ACRE (docs/EXPANSION.md 7.2, owner: FARM).

Legend (map characters, world/farm/data.h):

    .  grass (3 variants)          r / y  red / yellow flowers (animated)
    =  sandy path (autotiled)       ~      pond water (autotiled, animated)
    x  packed dirt yard            T / t  tree top / bottom (border trees)
    s  field soil (A_SOIL: till it with the HOE)
    e  soil around the fields (not a plot): where the soil fades into grass
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
    SEEDED, SPROUT, <CROP>_YOUNG, <CROP>_GROW,         overlays (BG2): the
    <CROP>_RIPE, SAPLING, WITHERED                     growth stages in order,
                                                       and a crop killed by
                                                       the change of season
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
         'CHILI', 'TOMATO', 'CORN', 'SUNFLOWER', 'MOTEBLOOM',
         'STRAWBERRY', 'MELON', 'EGGPLANT', 'SNOWPEA']
TREES = ['YOUNG', 'FRUIT', 'APPLE', 'PEACH']

GROUND_TERRAIN = ['GRASS', 'GRASS2', 'GRASS3', 'FLOWER_RED', 'FLOWER_YELLOW', 'DIRT',
                  'SOIL', 'SOIL2', 'TILLED', 'TILLED_WET', 'TILLED_FERT', 'TILLED_WET_FERT',
                  'ORCHARD', 'BERRY_MOUND', 'SOIL_RIM']
FENCES = ['FENCE_H', 'FENCE_V', 'FENCE_END', 'FENCE_SW', 'FENCE_SE']
OVERLAYS = (['TREE_TOP', 'TREE_BOTTOM'] + FENCES + ['SEEDED', 'SPROUT', 'SAPLING', 'WITHERED'] +
            [c + s for c in CROPS for s in ('_YOUNG', '_GROW', '_RIPE')] +
            [c + s + '_TOP' for c in CROPS for s in ('_YOUNG', '_GROW', '_RIPE')] +
            [t + s for t in TREES for s in ('_TOP', '_BOTTOM')] + ['SPRINKLER'])
FARM_TERRAIN = GROUND_TERRAIN + OVERLAYS

DOC = {
    'SOIL': 'field soil (A_SOIL): the HOE tills it',
    'TILLED': 'tilled soil (farm.c draws it over A_SOIL cells); _WET watered, _FERT fertilised',
    'ORCHARD': 'orchard mound (A_SOIL): saplings grow here',
    'BERRY_MOUND': 'mound under a wild berry patch (solid)',
    'SEEDED': 'crop overlay: just planted',
    'SPROUT': 'crop overlay: sprout (every crop)',
    'WITHERED': 'crop overlay: a crop that withered when its season ended (any tool clears it)',
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
                nx, ny = x + dx, y + dy
                c = img.p[ny][nx] if 0 <= nx < img.w and 0 <= ny < img.h else None
                if c is not None and c not in skip:
                    o.p[y][x] = col
                    break
    return o


class TallImg(Img):
    """A crop drawn in its own cell's coordinates (0..15, ground at y 14)
    with room above: y -16..-1 is the cell above, whose half becomes the
    <CROP>_<STAGE>_TOP overlay drawn on the top layer (like a tree crown),
    so tall plants are never cut off at the top of their cell."""

    def __init__(self):
        Img.__init__(self, 16, 32)

    def get(self, x, y, default=None):
        return Img.get(self, x, y + 16, default)

    def set(self, x, y, c):
        Img.set(self, x, y + 16, c)

    def copy(self):
        o = TallImg()
        o.p = [row[:] for row in self.p]
        return o

    def halves(self):
        """-> (bottom, top): the plot's own cell, the cell above."""
        bottom, top = Img(16, 16), Img(16, 16)
        bottom.p = [row[:] for row in self.p[16:]]
        top.p = [row[:] for row in self.p[:16]]
        return bottom, top


def tall_clumps(clumps, seed, ramp=('fm_lf_hi', 'fm_lf', 'fm_lf', 'fm_lf_dk')):
    """shade_clumps on a TallImg (clump centres in cell coordinates). The
    clumps must fit x 1..14 themselves: nothing is clipped flat."""
    raw, _ = shade_clumps(16, 32, [(cx, cy + 16, rx, ry) for (cx, cy, rx, ry) in clumps], list(ramp),
                          'fm_out', seed=seed)
    img = TallImg()
    img.p = raw.p
    return img


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


def bush(big=True, seed=5):
    if big:
        clumps = [(8.0, 5.6, 4.4, 4.0), (4.9, 9.2, 3.5, 3.4), (11.1, 9.2, 3.5, 3.4),
                  (8.0, 11.2, 4.8, 2.9)]
    else:
        clumps = [(8.0, 9.2, 3.8, 3.2), (5.4, 11.4, 2.8, 2.3), (10.6, 11.4, 2.8, 2.3)]
    return tall_clumps(clumps, seed)


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
    img = TallImg()
    for i in range(n):
        ang = -spread / 2 + spread * i / (n - 1)
        leaf(img, base[0] + 0.5, base[1], ang, length * (0.85 if i % 2 else 1.0), width)
    return img


def fronds(base=(8, 12)):
    img = TallImg()
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
    """A crop at its growing or ripe stage, as a TallImg."""
    img = TallImg()
    if name in ('GLOWBERRY', 'EMBERBERRY', 'TIDEBERRY'):
        img = bush(big=ripe, seed=CROPS.index(name) + 3)
        if ripe:
            ramp = {'GLOWBERRY': GLOW, 'EMBERBERRY': ('fm_or_hi', 'fm_or', 'fm_rd'),
                    'TIDEBERRY': BLUE}[name]
            dots(img, [(4, 7), (9, 4), (11, 8), (6, 10), (8, 12), (12, 11), (3, 10), (7, 6)], ramp)
            if name == 'GLOWBERRY':
                for (x, y) in ((1, 5), (14, 6), (7, 0)):
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
            img = TallImg()
            small = fronds((8, 13))
            for y in range(16):
                for x in range(16):
                    if small.get(x, y) is not None and y >= 7:
                        img.set(x, y, small.get(x, y))
        else:
            ell(img, 8.5, 13.0, 3.0, 2.0, list(ORANGE))
            img.set(7, 12, 'fm_or_hi')
        return outline(img)
    if name == 'POTATO':
        clumps = [(8.0, 8.0, 4.4, 3.8), (5.0, 11.0, 3.4, 3.0), (11.0, 11.0, 3.4, 3.0)]
        if not ripe:
            clumps = [(8.0, 10.0, 3.6, 3.0), (5.6, 12.0, 2.6, 2.0), (10.4, 12.0, 2.6, 2.0)]
        img = tall_clumps(clumps, 9, ('fm_lf_hi', 'fm_lf', 'fm_lf_dk'))
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
        line(img, 8, 14, 8, -4 if ripe else 1, 'fm_bk')
        for (y, ang) in ((12, -70), (11, 70), (8, -55), (7, 60), (4, -45), (3, 40), (0, -40), (-1, 35)):
            if not ripe and y < 3:
                continue
            leaf(img, 8, y, ang, 4.2, 1.7)
        if ripe:
            dots(img, [(4, 8), (11, 5), (5, 12), (11, 11), (4, 1)], RED, big=True)
        return outline(img)
    if name == 'CORN':
        top = -6 if ripe else 1
        line(img, 8, 14, 8, top, 'fm_lf_dk')
        line(img, 7, 14, 7, top + 2, 'fm_lf')
        for (y, ang, ln) in ((12, -60, 6.0), (10, 65, 6.0), (7, -40, 5.5), (4, 40, 5.0), (1, -35, 4.5),
                             (-2, 35, 4.0)):
            if y < top + 2:
                continue
            leaf(img, 8, y, ang, ln, 1.4)
        if ripe:
            ell(img, 10.5, 5.0, 1.6, 3.2, list(YELLOW))
            leaf(img, 9.5, 8, 15, 5.0, 1.2)
            for (x, y) in ((7, -7), (8, -8), (9, -7), (6, -6), (10, -6), (8, -9)):
                img.set(x, y, 'fm_ye_dk')
        return outline(img)
    if name == 'SUNFLOWER':
        hy = -2 if ripe else 3
        line(img, 8, 14, 8, hy, 'fm_lf_dk')
        leaf(img, 8, 11, -65, 4.5, 2.0)
        leaf(img, 8, 10, 65, 4.5, 2.0)
        leaf(img, 8, 6, -55, 4.0, 1.8)
        leaf(img, 8, 5, 60, 4.0, 1.8)
        if ripe:
            for k in range(10):
                a = k * math.pi / 5
                for r in (3.4, 4.4):
                    img.set(int(round(8 + r * math.cos(a))), int(round(hy + r * math.sin(a) * 0.9)),
                            'fm_ye' if r < 4 else 'fm_ye_hi')
            ell(img, 8.5, hy + 0.3, 4.6, 4.0, ['fm_ye_hi', 'fm_ye', 'fm_ye', 'fm_ye_dk'])
            ell(img, 8.5, hy + 0.5, 2.2, 2.0, ['fm_bk', 'fm_bk', 'fm_out'])
            img.set(7, hy - 1, 'fm_ye_dk')
        else:
            ell(img, 8.5, hy + 0.5, 1.8, 1.8, ['fm_lf_hi', 'fm_lf', 'fm_lf_dk'])
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
            for (x, y) in ((2, 3), (14, 2), (3, 9), (13, 8), (11, -1)):
                img.set(x, y, 'fm_gl')
            return img
        ell(img, 8.5, 5.0, 1.8, 2.6, ['fm_pu_hi', 'fm_pu', 'fm_pu_dk'])
        return outline(img)
    return new_crop_img(name, ripe)


def young_img(grown):
    """The young stage of a crop: its growing plant drawn smaller, standing
    on the same spot."""
    k = 0.62
    img = TallImg()
    for y in range(-16, 16):
        for x in range(16):
            sx = int(8 + (x + 0.5 - 8) / k)
            sy = int(14 + (y + 0.5 - 14) / k)
            c = grown.get(sx, sy)
            if c is not None and c != 'fm_out':
                img.set(x, y, c)
    return outline(img)


def withered():
    img = Img(16, 16)
    line(img, 8, 14, 8, 9, 'fm_bk')
    line(img, 8, 9, 11, 7, 'fm_bk')
    line(img, 8, 11, 5, 9, 'fm_bk')
    leaf(img, 11, 7, 120, 3.8, 1.4, cols=('fm_or_hi', 'fm_or_dk', 'fm_bk'))
    leaf(img, 5, 9, -130, 3.6, 1.4, cols=('fm_or_hi', 'fm_or_dk', 'fm_bk'))
    leaf(img, 8, 12, 100, 3.4, 1.2, cols=('fm_ye_dk', 'fm_or_dk', 'fm_bk'))
    leaf(img, 8, 13, -95, 3.0, 1.2, cols=('fm_ye_dk', 'fm_or_dk', 'fm_bk'))
    return outline(img)


def new_crop_img(name, ripe):
    img = TallImg()
    if name == 'STRAWBERRY':
        img = rosette(6, 5.2 if ripe else 4.6, 2.2, base=(8, 13), spread=150)
        if ripe:
            for (x, y) in ((4, 11), (11, 12), (7, 13)):
                for (dx, dy, c) in ((0, 0, 'fm_rd_hi'), (1, 0, 'fm_rd'), (0, 1, 'fm_rd'), (1, 1, 'fm_rd_dk'),
                                    (0, 2, 'fm_rd_dk')):
                    img.set(x + dx, y + dy, c)
                img.set(x + 1, y - 1, 'fm_lf_dk')
        else:
            for (x, y) in ((5, 8), (11, 9)):
                for (dx, dy) in ((0, -1), (-1, 0), (1, 0), (0, 1)):
                    img.set(x + dx, y + dy, 'fm_hl')
                img.set(x, y, 'fm_ye')
        return outline(img)
    if name == 'MELON':
        for (ang, ln) in ((-80, 6.5), (75, 6.0), (-30, 4.5), (35, 4.5)):
            leaf(img, 8, 12, ang, ln, 2.6)
        line(img, 2, 13, 14, 13, 'fm_lf_dk')
        if ripe:
            mel = TallImg()
            ell(mel, 9.0, 10.5, 5.6, 4.4, ['fm_lf_hi', 'fm_lf', 'fm_lf', 'fm_lf_dk'])
            for y in range(16):
                for x in range(16):
                    if mel.get(x, y) and (x + (y - 10) * (y - 10) // 6) % 3 == 0:
                        mel.set(x, y, 'fm_out' if mel.get(x, y) == 'fm_lf_dk' else 'fm_lf_dk')
            mel = outline(mel)
            for y in range(-16, 16):
                for x in range(16):
                    if mel.get(x, y) is not None:
                        img.set(x, y, mel.get(x, y))
            for (x, y) in ((6, 8), (7, 7), (8, 7)):
                img.set(x, y, 'fm_ye_hi')
        else:
            ell(img, 10.5, 11.5, 2.2, 1.8, ['fm_lf_hi', 'fm_lf', 'fm_lf_dk'])
            img.set(4, 9, 'fm_ye')
            img.set(12, 7, 'fm_ye')
        return outline(img)
    if name == 'EGGPLANT':
        line(img, 8, 14, 8, 4, 'fm_lf_dk')
        for (y, ang) in ((12, -70), (11, 70), (8, -55), (7, 55), (5, -35), (4, 35)):
            leaf(img, 8, y, ang, 4.4, 1.9)
        if ripe:
            for (cx, cy) in ((4.5, 11.5), (11.5, 10.5), (8.0, 13.0)):
                ell(img, cx, cy, 1.8, 2.6, list(PURPLE))
                img.set(int(cx), int(cy - 3), 'fm_lf_dk')
        else:
            for (x, y) in ((5, 8), (11, 9)):
                img.set(x, y, 'fm_pu_hi')
                img.set(x + 1, y, 'fm_pu')
                img.set(x, y + 1, 'fm_pu')
        return outline(img)
    if name == 'SNOWPEA':
        line(img, 12, 14, 12, -3, 'fm_bk')
        img.set(11, -3, 'fm_bk')
        img.set(13, -3, 'fm_bk')
        for (y, ang, x) in ((12, -70, 9), (10, 60, 10), (7, -60, 9), (5, 55, 10), (3, -50, 10),
                            (0, 50, 11), (-2, -45, 11)):
            if not ripe and y < 4:
                continue
            leaf(img, x, y, ang, 4.0, 1.6)
        line(img, 9, 14, 11, -1 if ripe else 4, 'fm_lf_dk')
        if ripe:
            for (x, y) in ((4, 8), (6, 11), (13, 7), (13, 11)):
                for k in range(4):
                    img.set(x, y + k, 'fm_lf_hi' if k < 3 else 'fm_lf')
                img.set(x + 1, y + 1, 'fm_lf')
                img.set(x + 1, y + 2, 'fm_lf')
        img = outline(img)
        for (x, y) in ((2, 3), (5, 0), (14, 13), (1, 12)):
            if img.get(x, y) is None:
                img.set(x, y, 'fm_bl_hi')
        return img
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
        'ORCHARD': mound_img(), 'BERRY_MOUND': mound_img(), 'SOIL_RIM': soil_img(0),
    }
    tree = gf.tree_img(overlay=True)
    over = {
        'TREE_TOP': tree.crop(0, 0, 16, 16), 'TREE_BOTTOM': tree.crop(0, 16, 16, 16),
        'FENCE_H': FENCE_H, 'FENCE_V': fence_v(), 'FENCE_END': FENCE_END,
        'FENCE_SW': with_stub(FENCE_H), 'FENCE_SE': with_stub(FENCE_END),
        'SEEDED': seeded(), 'SPROUT': sprout(), 'SAPLING': sapling(), 'SPRINKLER': sprinkler(),
        'WITHERED': withered(),
    }
    for c in CROPS:
        grow, ripe = crop_img(c, False), crop_img(c, True)
        for (stage, im) in (('_YOUNG', young_img(grow)), ('_GROW', grow), ('_RIPE', ripe)):
            over[c + stage], over[c + stage + '_TOP'] = im.halves()
    for t in TREES:
        im = tree_img(t)
        over[t + '_TOP'] = im.crop(0, 0, 16, 16)
        over[t + '_BOTTOM'] = im.crop(0, 16, 16, 16)
    return imgs, over


# ---------------------------------------------------------------------------
# tilled and watered soil, autotiled per 8x8 quadrant (farm.c soil_quads)
# ---------------------------------------------------------------------------

SOIL_DRY = 5   # farm_soil_combo[tvar][SOIL_DRY]: a dry plot


def _variant(h, v, d):
    return (0 if d else 1) if (h and v) else (2 if v else (3 if h else 4))


def soil_combos():
    """Every (tilled variant, wet variant or SOIL_DRY) a quadrant can show:
    wet soil is always tilled, so a neighbour's state is one of none, dry,
    wet."""
    combos = []
    for t in range(5):
        combos.append((t, SOIL_DRY))
    for h in range(3):
        for v in range(3):
            for d in range(3):
                c = (_variant(h > 0, v > 0, d > 0), _variant(h == 2, v == 2, d == 2))
                if c not in combos:
                    combos.append(c)
    return combos


def soil_quad_pix(c, tvar, wvar, fert, imgs):
    """Quadrant c (0 top-left .. 3 bottom-right) of a tilled plot whose
    tilled neighbours give variant tvar and wet ones wvar (SOIL_DRY: dry)."""
    wet = wvar != SOIL_DRY
    tex = imgs[('TILLED_WET' if wet else 'TILLED') + ('_FERT' if fert else '')]
    wet_tex, dry_tex = imgs['TILLED_WET_FERT' if fert else 'TILLED_WET'], imgs['TILLED_FERT' if fert else 'TILLED']
    soil = imgs['SOIL']
    qx, qy = (c & 1) * 8, (c >> 1) * 8
    pix = []
    for y in range(8):
        for x in range(8):
            lx = x if not (c & 1) else 7 - x
            ly = y if not (c >> 1) else 7 - y
            X, Y = qx + x, qy + y
            nt = ((hash2(X, Y, 41) & 255) / 255.0 - 0.5) * 1.2
            dt = gf_blend_depth(tvar, lx, ly, 1.6, 0.4, amp=0.35) if tvar else 9.0
            if dt + nt <= 0:
                col = soil.get(X, Y)
                if dt + nt > -1.2 and hash2(X, Y, 43) % 3:
                    col = 'fm_so_md'   # the little lip the hoe throws up
                pix.append(col)
                continue
            if not wet:
                pix.append(tex.get(X, Y))
                continue
            nw = ((hash2(X, Y, 47) & 255) / 255.0 - 0.5) * 1.6
            dw = gf_blend_depth(wvar, lx, ly, 1.2, 2.7, amp=0.5) if wvar else 9.0
            pix.append((wet_tex if dw + nw > 0 else dry_tex).get(X, Y))
    return pix


gf_blend_depth = None


def add_soil_quads(gf, ts, out, imgs):
    global gf_blend_depth
    gf_blend_depth = gf.blend_depth
    combos = soil_combos()
    q = [[ts.add(soil_quad_pix(c, t, w, False, imgs), (4,), 'farm.soil[%d][%d,%d]' % (c, t, w))
          for (t, w) in combos] for c in range(4)]
    fert = [[ts.add(soil_quad_pix(c, 0, w, True, imgs), (4,), 'farm.soil_fert[%d][%d]' % (c, w))
             for w in (SOIL_DRY, 0, 1, 2, 3, 4)] for c in range(4)]
    table = [[combos.index((t, w)) if (t, w) in combos else 0 for w in range(6)] for t in range(5)]
    lines = ['/* Tilled / watered soil per 8x8 quadrant (farm.c soil_quads): */',
             '#define FARM_SOIL_COMBOS %d' % len(combos),
             '#define FARM_SOIL_DRY %d' % SOIL_DRY,
             '/* [tilled variant][wet variant, or FARM_SOIL_DRY] -> column of farm_soil_q */',
             'static const u8 farm_soil_combo[5][6] = {']
    lines += ['    {' + ', '.join(str(v) for v in row) + '},' for row in table]
    lines += ['};', 'static const u16 farm_soil_q[4][FARM_SOIL_COMBOS] = {']
    lines += ['    {' + ', '.join('0x%04X' % v for v in row) + '},' for row in q]
    lines += ['};', '/* fertilised, where every neighbour is tilled: [quadrant][dry, wet variant 0..4] */',
              'static const u16 farm_soil_fert_q[4][6] = {']
    lines += ['    {' + ', '.join('0x%04X' % v for v in row) + '},' for row in fert]
    lines += ['};']
    out.setdefault('c_extra', []).extend(lines)


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
    add_soil_quads(gf, ts, out, imgs)
    grassy = ['GRASS', 'GRASS2', 'GRASS3', 'FLOWER_RED', 'FLOWER_YELLOW']
    gf.add_blend(ts, out, ['SOIL', 'SOIL2', 'SOIL_RIM'], imgs['SOIL'], imgs['GRASS'], grassy, width=3.0, seed=1.3,
                 rim_out='g_dk')
    gf.add_blend(ts, out, ['DIRT'], imgs['DIRT'], imgs['GRASS'], grassy, width=2.5, seed=2.1)
    attrs = {'SOIL': gf.A_SOIL, 'SOIL2': gf.A_SOIL, 'ORCHARD': gf.A_SOIL,
             'BERRY_MOUND': gf.A_SOLID}
    for t in ('TILLED', 'TILLED_WET', 'TILLED_FERT', 'TILLED_WET_FERT'):
        attrs[t] = gf.A_SOIL
    return gf.finish_tileset(
        out, name, 'FA', attrs=attrs,
        ground=['GRASS', 'GRASS2', 'GRASS3', 'DIRT'], overlay=list(OVERLAYS),
        legend={'.': gf.GRASS_VARIANTS, 'r': 'FLOWER_RED', 'y': 'FLOWER_YELLOW', '=': 'PATH',
                '~': 'WATER', 'T': 'TREE_TOP', 't': 'TREE_BOTTOM', 'x': 'DIRT',
                's': [('SOIL2', 5), ('SOIL', 11)], 'e': 'SOIL_RIM', 'o': 'ORCHARD', 'm': 'BERRY_MOUND',
                '-': 'FENCE_H', ']': 'FENCE_END', '|': 'FENCE_V', '{': 'FENCE_SW',
                '}': 'FENCE_SE'},
        oob='TREE_TOP', default_ground='GRASS', backdrop='ground',
        doors=[('FARMHOUSE', 2, 4)])
