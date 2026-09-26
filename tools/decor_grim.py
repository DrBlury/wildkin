#!/usr/bin/env python3
"""The Ashen March (W-GRIM): palettes, drawing helpers and the decor
catalogue for the 'grim' (ASHEN FIELDS, GRAVEWOOD, DUSKMERE) and 'crypt'
(LANTERN CRYPT, THE OSSUARY, BONE THRONE) tilesets, plus a few Duskmere
interior pieces for the shared 'interior' tileset.

Mood: ash greys that lean violet, bruised purples, ember-orange accents,
sickly green wisp light, bone ivory. Light comes from the top-left; objects
have a 1px dark outline (grm_out / cry_out) and never carry baked ground
(the art lint in gen_field_gfx.py checks it).

Palette plan (every 8x8 quadrant must fit one bank of its tileset):

  grim  0 ash ground: ash ramp, soot, embers, dead straw, bone, rust
        1 mire: black water, mud, peat, moss, reeds, foxfire green
        2 trees: bark ramp, charcoal, cypress leaves, hanging moss, embers
        3 decor A: stone, bone, iron, ember, wisp, moss (graves, fences)
        4 decor B: wood, lantern light, bruised cloth, straw, iron
        5 roofs: bruised slate + timber + mud
        6 stone and bone buildings (crypt, gate) + mud + light
        7 walls: timber, plaster, lit windows, planks
  crypt 0 room: void, flagstones, wall stone, bone dust, wisp crack
        1 niches: wall stone, bone, candle wax and flame
        2 carpet: bruised red runner, gold trim, floor stone
        3 decor A: bone, stone, candle light, wisp (skulls, sarcophagi)
        4 decor B: wood, iron, gold, cloth (coffins, chests, banners)
        5 decor C: flame, ember, green fire (braziers, candles)
        6 decor D: bruised stone, wisp glow, bone (statues, the throne)
        7 decor E: dark stone, iron chains, bone
"""

import math
from pixelart import Img, G, hash2, shade_clumps, Decor
from decor_outdoor import SG, outline

# ---------------------------------------------------------------------------
# colours (8-bit RGB, quantised to RGB15 on output)
# ---------------------------------------------------------------------------

GRIM_COLORS = {
    # ash ground
    'grm_ash_hi': (184, 178, 186), 'grm_ash_lt': (150, 144, 156), 'grm_ash': (122, 116, 132),
    'grm_ash_md': (98, 92, 110), 'grm_ash_dk': (74, 68, 88), 'grm_ash_dkr': (52, 46, 66),
    'grm_soot': (32, 26, 42),
    'grm_emb_hi': (255, 216, 120), 'grm_emb': (240, 128, 48), 'grm_emb_dk': (178, 62, 46),
    'grm_straw_hi': (186, 170, 132), 'grm_straw': (142, 126, 100), 'grm_straw_dk': (100, 88, 78),
    'grm_bone': (216, 206, 184), 'grm_rust': (128, 74, 66),
    # the mire
    'grm_wat_hi': (156, 176, 184), 'grm_wat_lt': (86, 98, 124), 'grm_wat': (48, 52, 78),
    'grm_wat_dk': (28, 30, 50),
    'grm_mud_hi': (116, 104, 98), 'grm_mud': (86, 76, 76), 'grm_mud_dk': (60, 52, 58),
    'grm_peat': (38, 32, 40),
    'grm_moss_hi': (164, 188, 104), 'grm_moss': (112, 140, 80), 'grm_moss_dk': (70, 94, 66),
    'grm_reed_hi': (176, 164, 120), 'grm_reed': (128, 114, 90),
    'grm_wisp_hi': (216, 255, 180), 'grm_wisp': (144, 224, 104),
    # trees
    'grm_out': (26, 18, 32),
    'grm_bark_hi': (152, 136, 136), 'grm_bark_lt': (118, 102, 110), 'grm_bark': (90, 76, 90),
    'grm_bark_dk': (62, 50, 66), 'grm_char': (42, 34, 48),
    'grm_leaf_hi': (142, 152, 110), 'grm_leaf': (100, 114, 88), 'grm_leaf_dk': (66, 80, 68),
    'grm_hang': (172, 178, 144),
    'grm_bruise_lt': (144, 112, 162), 'grm_bruise': (102, 74, 122),
    # decor
    'grm_st_hi': (200, 196, 206), 'grm_st_lt': (160, 156, 172), 'grm_st': (120, 116, 136),
    'grm_st_dk': (84, 80, 100),
    'grm_bone_hi': (246, 238, 218), 'grm_bone_dk': (164, 148, 132),
    'grm_iron_hi': (128, 132, 152), 'grm_iron': (72, 76, 96),
    'grm_wd_hi': (172, 134, 98), 'grm_wd': (126, 92, 72), 'grm_wd_dk': (84, 60, 56),
    'grm_lamp_hi': (255, 242, 178), 'grm_lamp': (252, 192, 82), 'grm_lamp_dk': (208, 118, 54),
    'grm_cloth_hi': (166, 126, 182), 'grm_cloth': (116, 82, 138), 'grm_cloth_dk': (76, 52, 98),
    # buildings
    'grm_rf_hi': (150, 126, 170), 'grm_rf_lt': (118, 96, 142), 'grm_rf': (92, 72, 116),
    'grm_rf_dk': (66, 50, 88), 'grm_rf_dkr': (44, 34, 62),
    'grm_pl_hi': (188, 182, 166), 'grm_pl': (150, 142, 132), 'grm_pl_dk': (110, 102, 100),
    'grm_gl': (50, 46, 74),
}

CRYPT_COLORS = {
    'cry_void': (8, 6, 14),
    'cry_out': (20, 14, 26),
    # flagstones (cold violet-grey)
    'cry_fl_hi': (118, 112, 136), 'cry_fl': (92, 86, 110), 'cry_fl_md': (72, 66, 90),
    'cry_fl_dk': (52, 46, 68),
    # wall stone
    'cry_wl_hi': (140, 132, 156), 'cry_wl': (108, 100, 126), 'cry_wl_md': (82, 76, 102),
    'cry_wl_dk': (58, 52, 78), 'cry_wl_dkr': (38, 32, 54),
    # bone
    'cry_bone_hi': (240, 232, 210), 'cry_bone': (204, 192, 168), 'cry_bone_dk': (150, 136, 120),
    # candle
    'cry_wax': (226, 216, 192), 'cry_flame_hi': (255, 244, 176), 'cry_flame': (252, 186, 76),
    'cry_flame_dk': (212, 104, 48),
    # wisp green
    'cry_wisp_hi': (212, 255, 176), 'cry_wisp': (132, 216, 104), 'cry_wisp_dk': (64, 140, 84),
    # carpet
    'cry_rug_hi': (160, 74, 104), 'cry_rug': (118, 46, 80), 'cry_rug_dk': (78, 30, 58),
    'cry_gold_hi': (246, 214, 120), 'cry_gold': (196, 150, 70), 'cry_gold_dk': (130, 92, 50),
    # wood and iron
    'cry_wd_hi': (156, 116, 88), 'cry_wd': (112, 80, 66), 'cry_wd_dk': (74, 52, 50),
    'cry_iron_hi': (136, 140, 160), 'cry_iron': (84, 88, 108), 'cry_iron_dk': (50, 52, 70),
    # cloth
    'cry_cloth_hi': (156, 120, 176), 'cry_cloth': (108, 78, 132), 'cry_cloth_dk': (70, 48, 94),
    # green fire
    'cry_gfire_hi': (232, 255, 200), 'cry_gfire': (120, 232, 120),
}

GRIM_BANKS = [
    # 0 ash ground, path, embers, dead grass, ledges, crags, cobbles
    ['grm_ash_hi', 'grm_ash_lt', 'grm_ash', 'grm_ash_md', 'grm_ash_dk', 'grm_ash_dkr', 'grm_soot',
     'grm_emb_hi', 'grm_emb', 'grm_emb_dk', 'grm_straw_hi', 'grm_straw', 'grm_straw_dk', 'grm_bone',
     'grm_rust'],
    # 1 mire: black water, mud, moss, reeds, foxfire
    ['grm_wat_hi', 'grm_wat_lt', 'grm_wat', 'grm_wat_dk', 'grm_mud_hi', 'grm_mud', 'grm_mud_dk',
     'grm_peat', 'grm_moss_hi', 'grm_moss', 'grm_moss_dk', 'grm_reed_hi', 'grm_reed', 'grm_wisp_hi',
     'grm_wisp'],
    # 2 trees
    ['grm_out', 'grm_bark_hi', 'grm_bark_lt', 'grm_bark', 'grm_bark_dk', 'grm_char', 'grm_leaf_hi',
     'grm_leaf', 'grm_leaf_dk', 'grm_hang', 'grm_emb', 'grm_emb_dk', 'grm_bruise_lt', 'grm_bruise',
     'grm_moss'],
    # 3 decor A: stone, bone, iron, ember, wisp, moss
    ['grm_out', 'grm_st_hi', 'grm_st_lt', 'grm_st', 'grm_st_dk', 'grm_bone_hi', 'grm_bone',
     'grm_bone_dk', 'grm_iron_hi', 'grm_iron', 'grm_emb', 'grm_emb_hi', 'grm_wisp_hi', 'grm_wisp',
     'grm_moss'],
    # 4 decor B: wood, lantern light, bruised cloth, straw, iron
    ['grm_out', 'grm_wd_hi', 'grm_wd', 'grm_wd_dk', 'grm_lamp_hi', 'grm_lamp', 'grm_lamp_dk',
     'grm_cloth_hi', 'grm_cloth', 'grm_cloth_dk', 'grm_straw_hi', 'grm_straw', 'grm_iron_hi',
     'grm_iron', 'grm_char'],
    # 5 roofs: bruised slate, timber, mud
    ['grm_out', 'grm_rf_hi', 'grm_rf_lt', 'grm_rf', 'grm_rf_dk', 'grm_rf_dkr', 'grm_wd_hi', 'grm_wd',
     'grm_wd_dk', 'grm_mud', 'grm_mud_dk', 'grm_peat', 'grm_moss', 'grm_lamp', 'grm_lamp_hi'],
    # 6 stone and bone buildings, mud, light
    ['grm_out', 'grm_st_hi', 'grm_st_lt', 'grm_st', 'grm_st_dk', 'grm_bone_hi', 'grm_bone',
     'grm_bone_dk', 'grm_mud', 'grm_mud_dk', 'grm_peat', 'grm_moss', 'grm_lamp', 'grm_lamp_hi',
     'grm_wisp'],
    # 7 walls: timber, plaster, lit windows, planks
    ['grm_out', 'grm_wd_hi', 'grm_wd', 'grm_wd_dk', 'grm_pl_hi', 'grm_pl', 'grm_pl_dk', 'grm_lamp_hi',
     'grm_lamp', 'grm_lamp_dk', 'grm_gl', 'grm_mud', 'grm_mud_dk', 'grm_peat', 'grm_char'],
]

CRYPT_BANKS = [
    # 0 room: void, flagstones, wall stone, bone dust, wisp crack
    ['cry_void', 'cry_out', 'cry_fl_hi', 'cry_fl', 'cry_fl_md', 'cry_fl_dk', 'cry_wl_hi', 'cry_wl',
     'cry_wl_md', 'cry_wl_dk', 'cry_wl_dkr', 'cry_bone', 'cry_bone_dk', 'cry_wisp', 'cry_wisp_dk'],
    # 1 niches: wall stone, bone, candle
    ['cry_void', 'cry_out', 'cry_wl_hi', 'cry_wl', 'cry_wl_md', 'cry_wl_dk', 'cry_wl_dkr',
     'cry_bone_hi', 'cry_bone', 'cry_bone_dk', 'cry_wax', 'cry_flame_hi', 'cry_flame', 'cry_flame_dk',
     'cry_fl_dk'],
    # 2 carpet: runner, gold trim, floor stone
    ['cry_out', 'cry_rug_hi', 'cry_rug', 'cry_rug_dk', 'cry_gold_hi', 'cry_gold', 'cry_gold_dk',
     'cry_fl_hi', 'cry_fl', 'cry_fl_md', 'cry_fl_dk', 'cry_bone', 'cry_bone_dk', 'cry_wl_dk',
     'cry_void'],
    # 3 decor A: bone, stone, candle light, wisp
    ['cry_out', 'cry_bone_hi', 'cry_bone', 'cry_bone_dk', 'cry_wl_hi', 'cry_wl', 'cry_wl_md',
     'cry_wl_dk', 'cry_wax', 'cry_flame_hi', 'cry_flame', 'cry_flame_dk', 'cry_wisp_hi', 'cry_wisp',
     'cry_void'],
    # 4 decor B: wood, iron, gold, cloth
    ['cry_out', 'cry_wd_hi', 'cry_wd', 'cry_wd_dk', 'cry_iron_hi', 'cry_iron', 'cry_iron_dk',
     'cry_gold_hi', 'cry_gold', 'cry_gold_dk', 'cry_cloth_hi', 'cry_cloth', 'cry_cloth_dk',
     'cry_bone', 'cry_flame'],
    # 5 decor C: fire and green fire, iron
    ['cry_out', 'cry_flame_hi', 'cry_flame', 'cry_flame_dk', 'cry_gfire_hi', 'cry_gfire',
     'cry_wisp_dk', 'cry_iron_hi', 'cry_iron', 'cry_iron_dk', 'cry_wl_hi', 'cry_wl', 'cry_wl_md',
     'cry_wl_dk', 'cry_wax'],
    # 6 decor D: statue stone, wisp glow, bone, cloth
    ['cry_out', 'cry_wl_hi', 'cry_wl', 'cry_wl_md', 'cry_wl_dk', 'cry_wl_dkr', 'cry_wisp_hi',
     'cry_wisp', 'cry_wisp_dk', 'cry_bone_hi', 'cry_bone', 'cry_bone_dk', 'cry_cloth', 'cry_cloth_dk',
     'cry_void'],
    # 7 decor E: bone and gold (the throne, treasure)
    ['cry_out', 'cry_bone_hi', 'cry_bone', 'cry_bone_dk', 'cry_gold_hi', 'cry_gold', 'cry_gold_dk',
     'cry_rug_hi', 'cry_rug', 'cry_rug_dk', 'cry_wl_md', 'cry_wl_dk', 'cry_flame', 'cry_wisp',
     'cry_void'],
]

ALL_COLORS = dict(GRIM_COLORS)
ALL_COLORS.update(CRYPT_COLORS)

# ---------------------------------------------------------------------------
# drawing helpers
# ---------------------------------------------------------------------------


def blank(w, h, fill=None):
    return Img(w, h, fill)


def mask_img(w, h):
    return [[0] * w for _ in range(h)]


def seg_mask(mask, pts, r0, r1, val=1):
    """Stamp a thick polyline into a boolean mask; radius r0 -> r1."""
    h, w = len(mask), len(mask[0])
    total = 0.0
    lens = []
    for i in range(len(pts) - 1):
        d = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        lens.append(d)
        total += d
    acc = 0.0
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        n = max(1, int(lens[i] * 4))
        for k in range(n + 1):
            t = k / n
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            f = (acc + lens[i] * t) / total if total else 0
            r = r0 + (r1 - r0) * f
            if r < 0.72:
                xi, yi = int(math.floor(x)), int(math.floor(y))
                if 0 <= xi < w and 0 <= yi < h:
                    mask[yi][xi] = val
                continue
            for yy in range(int(y - r - 1), int(y + r + 2)):
                for xx in range(int(x - r - 1), int(x + r + 2)):
                    if 0 <= xx < w and 0 <= yy < h and \
                            (xx + 0.5 - x) ** 2 + (yy + 0.5 - y) ** 2 <= r * r:
                        mask[yy][xx] = val
        acc += lens[i]


def ell_mask(mask, cx, cy, rx, ry, val=1):
    h, w = len(mask), len(mask[0])
    for y in range(h):
        for x in range(w):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                mask[y][x] = val


def shade_mask(mask, ramp, seed=0, rim=None, streak=False):
    """Colour a mask lit from the top-left: ramp = [hi, lt, base, dk];
    rim: optional rim-light colour for some left edges."""
    h, w = len(mask), len(mask[0])
    img = Img(w, h)

    def m(x, y):
        return 0 <= x < w and 0 <= y < h and mask[y][x]
    for y in range(h):
        for x in range(w):
            if not mask[y][x]:
                continue
            left, right, up = m(x - 1, y), m(x + 1, y), m(x, y - 1)
            n = hash2(x, y, seed) & 15
            if not left and not right:
                c = ramp[1] if n < 10 else ramp[2]
            elif not left:
                c = ramp[0]
                if rim and n < 5:
                    c = rim
            elif not right:
                c = ramp[3]
            elif not m(x - 2, y):
                c = ramp[1]
            elif not m(x + 2, y):
                c = ramp[3] if n < 9 else ramp[2]
            else:
                c = ramp[2]
                if streak and (x * 7 + (y // 3) * 3 + seed) % 5 == 0:
                    c = ramp[3]
                elif n == 0:
                    c = ramp[1]
            if not up and c == ramp[2]:
                c = ramp[1]
            img.p[y][x] = c
    return img


def outline_mask(img, mask, col):
    h, w = len(mask), len(mask[0])
    for y in range(h):
        for x in range(w):
            if mask[y][x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and mask[yy][xx]:
                    img.p[y][x] = col
                    break
    return img


def wrap_noise(x, y, seed, period=16):
    return hash2(x % period, y % period, seed)


def tex(w, h, fn):
    img = Img(w, h)
    for y in range(h):
        for x in range(w):
            img.p[y][x] = fn(x, y)
    return img


def sprinkle(img, pts, c):
    for (x, y) in pts:
        img.set(x, y, c)


def grid(text, legend, w=None, h=None):
    """Pixel grid with an explicit width (rows padded on the right)."""
    rows = [r.strip() for r in text.strip('\n').split('\n')]
    rows = [r for r in rows if r]
    W = w or max(len(r) for r in rows)
    img = Img(W, h or len(rows))
    oy = (h - len(rows)) if h else 0
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch not in legend:
                raise KeyError('grid char %r not in legend (row %d: %s)' % (ch, y, r))
            if legend[ch] is not None:
                img.p[oy + y][x] = legend[ch]
    return img




# ===========================================================================
# the decor catalogue
# ===========================================================================
#
# Every object is drawn inside one palette bank of its tileset (see the plan
# above), on transparency, lit from the top-left, with a dark outline.

GRIM = ['grim']
CRYPT = ['crypt']


def SG(text, legend, w=16):
    """Strict grid: every row must be exactly w wide."""
    rows = [r.strip() for r in text.strip('\n').split('\n')]
    rows = [r for r in rows if r]
    for i, r in enumerate(rows):
        if len(r) != w:
            raise ValueError('grid row %d is %d wide, expected %d: %r' % (i, len(r), w, r))
    return G('\n'.join(rows), legend)


# grim bank 3: stone, bone, iron, ember, wisp, moss
GA = {'.': None, 'O': 'grm_out', 'H': 'grm_st_hi', 'L': 'grm_st_lt', 'S': 'grm_st',
      'D': 'grm_st_dk', 'W': 'grm_bone_hi', 'B': 'grm_bone', 'b': 'grm_bone_dk',
      'I': 'grm_iron_hi', 'i': 'grm_iron', 'e': 'grm_emb', 'E': 'grm_emb_hi',
      'G': 'grm_wisp_hi', 'g': 'grm_wisp', 'm': 'grm_moss'}
# grim bank 4: wood, lantern light, bruised cloth, straw, iron
GB = {'.': None, 'O': 'grm_out', 'h': 'grm_wd_hi', 'w': 'grm_wd', 'k': 'grm_wd_dk',
      'Y': 'grm_lamp_hi', 'y': 'grm_lamp', 'o': 'grm_lamp_dk', 'C': 'grm_cloth_hi',
      'c': 'grm_cloth', 'x': 'grm_cloth_dk', 'T': 'grm_straw_hi', 't': 'grm_straw',
      'I': 'grm_iron_hi', 'i': 'grm_iron', 'z': 'grm_char'}
# grim bank 2: bark, charcoal, leaves, embers
GT = {'.': None, 'O': 'grm_out', 'H': 'grm_bark_hi', 'L': 'grm_bark_lt', 'B': 'grm_bark',
      'D': 'grm_bark_dk', 'c': 'grm_char', 'l': 'grm_leaf_hi', 'f': 'grm_leaf',
      'F': 'grm_leaf_dk', 'e': 'grm_emb', 'E': 'grm_emb_dk', 'm': 'grm_moss'}

# crypt bank 3: bone, stone, candle, wisp
CA = {'.': None, 'O': 'cry_out', 'W': 'cry_bone_hi', 'B': 'cry_bone', 'b': 'cry_bone_dk',
      'H': 'cry_wl_hi', 'L': 'cry_wl', 'M': 'cry_wl_md', 'D': 'cry_wl_dk', 'x': 'cry_wax',
      'F': 'cry_flame_hi', 'f': 'cry_flame', 'r': 'cry_flame_dk', 'G': 'cry_wisp_hi',
      'g': 'cry_wisp', 'V': 'cry_void'}
# crypt bank 4: wood, iron, gold, cloth
CB = {'.': None, 'O': 'cry_out', 'h': 'cry_wd_hi', 'w': 'cry_wd', 'k': 'cry_wd_dk',
      'I': 'cry_iron_hi', 'i': 'cry_iron', 'j': 'cry_iron_dk', 'Y': 'cry_gold_hi',
      'y': 'cry_gold', 'o': 'cry_gold_dk', 'C': 'cry_cloth_hi', 'c': 'cry_cloth',
      'x': 'cry_cloth_dk', 'B': 'cry_bone', 'f': 'cry_flame'}
# crypt bank 5: fire, green fire, iron, stone
CF = {'.': None, 'O': 'cry_out', 'F': 'cry_flame_hi', 'f': 'cry_flame', 'r': 'cry_flame_dk',
      'G': 'cry_gfire_hi', 'g': 'cry_gfire', 'd': 'cry_wisp_dk', 'I': 'cry_iron_hi',
      'i': 'cry_iron', 'j': 'cry_iron_dk', 'H': 'cry_wl_hi', 'L': 'cry_wl', 'M': 'cry_wl_md',
      'D': 'cry_wl_dk', 'x': 'cry_wax'}
# crypt bank 6: statue stone, wisp glow, bone, cloth
CS = {'.': None, 'O': 'cry_out', 'H': 'cry_wl_hi', 'L': 'cry_wl', 'M': 'cry_wl_md',
      'D': 'cry_wl_dk', 'K': 'cry_wl_dkr', 'G': 'cry_wisp_hi', 'g': 'cry_wisp',
      'd': 'cry_wisp_dk', 'W': 'cry_bone_hi', 'B': 'cry_bone', 'b': 'cry_bone_dk',
      'c': 'cry_cloth', 'x': 'cry_cloth_dk', 'V': 'cry_void'}
# crypt bank 7: bone and gold, red cloth
CT = {'.': None, 'O': 'cry_out', 'W': 'cry_bone_hi', 'B': 'cry_bone', 'b': 'cry_bone_dk',
      'Y': 'cry_gold_hi', 'y': 'cry_gold', 'o': 'cry_gold_dk', 'R': 'cry_rug_hi',
      'r': 'cry_rug', 'q': 'cry_rug_dk', 'M': 'cry_wl_md', 'D': 'cry_wl_dk', 'f': 'cry_flame',
      'g': 'cry_wisp', 'V': 'cry_void'}


def stack(*imgs):
    """Stack equally wide images vertically."""
    out = Img(imgs[0].w, sum(i.h for i in imgs))
    y = 0
    for i in imgs:
        out.paste(i, 0, y)
        y += i.h
    return out


# ---------------------------------------------------------------- grim

GR_SIGN = SG('''
................
................
..OOOOOOOOOOOO..
.OhhhhhhhhhhhwO.
.OhwwwwwwwwwwkO.
.OhwkkwkkkwwwkO.
.OhwwwwwwwwwwkO.
.OhwkwkkwkkkwkO.
.OhwwwwwwwwwwkO.
.OkkkkkkkkkkkkO.
..OOOOOhkOOOOO..
......OhkO......
......OhkO......
......OhkO......
.....OzhkzO.....
......OOOO......
''', GB)

GR_GRAVE = SG('''
................
................
.....OOOOOO.....
....OHHLLLSO....
...OHLLLLLSDO...
...OHLDDDLSDO...
...OHLLLLLSDO...
...OHLDDDDSDO...
...OHLLLLLSDO...
...OHLLmLLSDO...
...OHLmmLSSDO...
...OmmLLLSSDO...
..OOmmmSSSDDOO..
..ODDDDDDDDDDO..
...OOOOOOOOOO...
................
''', GA)

GR_CROSS = SG('''
................
.......OO.......
......OHLO......
......OHSO......
...OOOOHSOOOO...
..OHHHHLLSSSDO..
..ODDDDLSDDDDO..
...OOOOHSOOOO...
......OHSO......
......OHSO......
......OHSO......
......OHmO......
.....OmHSmO.....
....ODDDDDDO....
.....OOOOOO.....
................
''', GA)

GR_FENCE = SG('''
................
..I...I...I...I.
.OIO.OIO.OIO.OIO
.OiO.OiO.OiO.OiO
OOIOOOIOOOIOOOIO
IIIIIIIIIIIIIIII
iiiiiiiiiiiiiiii
OOiOOOiOOOiOOOiO
.OiO.OiO.OiO.OiO
.OiO.OiO.OiO.OiO
.OiO.OiO.OiO.OiO
OOiOOOiOOOiOOOiO
IIIIIIIIIIIIIIII
iiiiiiiiiiiiiiii
OOOOOOOOOOOOOOOO
................
''', GA)

GR_BONES = SG('''
................
................
................
.....OOOOO......
....OWWWBBO.....
...OWWOWBOBO....
...OWBOBBObO....
...OBWWBBBbO.OO.
..OOObOObbOOOWBO
.OWBBOBObOBWWBbO
OWWBbOWWWBOBbbO.
OBbbObBBBbbOOO..
.OOOOObbbbO.....
.....OOOOO......
................
................
''', GA)

GR_SHRUB = SG('''
................
................
....O.....O.....
...OHO...OLO.O..
....OLO.OLO.OBO.
.O...OLOLBOOBO..
OHO...OBLBOBO...
.OLO.OBLBDBO..O.
..OLOBLBDBO..OLO
...OBLBDDO..OLO.
..OBLBBDBOOOBO..
.OLBBDDBDBBDO...
.OBDDcDDcDDcO...
..OOcccccccO....
....OOOOOOO.....
................
''', GT)

GR_STUMP = SG('''
................
................
................
................
....OOOOOOOO....
...OLLHHHLLBO...
..OLHBBBBBHLBO..
..OBLHBDDBHLDO..
..OBBLLHHLLBDO..
..OHBBBBBBBBDO..
..OHLBBDBBDBDO..
..OHLBDBBDBDDO..
.OmHLBDBBDBDDmO.
.OmmcBDccDcDmmO.
..OOOOOOOOOOOO..
................
''', GT)

GR_CART = SG('''
................................
................................
................................
........................OO......
..OOOOOOOOOOOOOOOOOOOOOOhwO.....
.OhhhhhhzhhhhhhzhhhhhhhhwkO.....
.OhwwwwwzwwwwwwzwwwwwwwwkO......
.OwkkkkzzkkkkkzzkkkkkkkkO.......
.OhwwzwwwwwwzwwwwwwzwwwwkO......
.OkkkkkkkkkkkkkkkkkkkkkkkO......
..OOOOOOOOOOOOOOOOOOOOOOOhO.....
.....OOOO..........OOOO..OkhO...
....OhwwkO........OzwwzO..OkkhO.
....OwOOwO........OwOOkO...OOkO.
....OkwwkO........OzkkzO.....OO.
.....OOOO..........OOOO.........
''', GB, w=32)

LANTERN_HEAD = '''
................
................
.......OO.......
......OkkO......
.....OOOOOO.....
....OiIIIIiO....
....OiYYYYiO....
....OiYYYyiO....
....OiYyyoiO....
....OiyyooiO....
....OiIIIIiO....
.....OOOOOO.....
......OhkO......
......OhkO......
......OhkO......
......OhkO......
'''
LANTERN_POST = '''
......OhkO......
......OhkO......
......OhkO......
......OhkO......
......OhkO......
......OhkO......
......OhkO......
......OhkO......
......OhkO......
......OhkO......
......OhkO......
.....OhhkkO.....
....OhwwwwkO....
....OkkkkkkO....
.....OOOOOO.....
................
'''


def lantern_post_frames():
    dim = LANTERN_HEAD.replace('OiYYYyiO', 'OiYYyyiO').replace('OiYyyoiO', 'OiyyyoiO')
    return [stack(SG(LANTERN_HEAD, GB), SG(LANTERN_POST, GB)),
            stack(SG(dim, GB), SG(LANTERN_POST, GB))]


def wisp_frames():
    frames = []
    for (dy, big) in ((0, 1), (1, 0), (2, 1), (1, 0)):
        img = Img(16, 16)
        cy = 6 + dy
        for y in range(16):
            for x in range(16):
                d = ((x + 0.5 - 8) ** 2 + ((y + 0.5 - cy) * 1.2) ** 2) ** 0.5
                if d < 1.6 + big * 0.4:
                    img.p[y][x] = 'grm_wisp_hi'
                elif d < 3.0 + big * 0.5:
                    img.p[y][x] = 'grm_wisp'
        for (tx, ty) in ((8, cy + 3), (7 + big, cy + 4), (8, cy + 5)):
            if 0 <= ty < 16:
                img.p[ty][tx] = 'grm_wisp'
        frames.append(img)
    return frames


GR_BELL = stack(SG('''
................
..OOOOOOOOOOOO..
.OhhhhhhhhhhhhO.
.OkkkkkkkkkkkkO.
..OhkOOOOOOhkO..
..OhkO.OO.OhkO..
..OhkOOiiOOhkO..
..OhkOiIIiOhkO..
..OhkOIIiiOhkO..
..OhkOIiiiOhkO..
..OhkIiiiiiOkO..
..OhkIiiiiiiOO..
..OhkOOOOOOOhkO.
..OhkO.OiO.OhkO.
..OhkO..O..OhkO.
..OhkO.....OhkO.
''', GB), SG('''
..OhkO.....OhkO.
..OhkO.....OhkO.
..OhkO.....OhkO.
..OhkO.....OhkO.
..OhkO.....OhkO.
..OhkO.....OhkO.
..OhkO.....OhkO.
..OhkO.....OhkO.
..OhkO.....OhkO.
..OhkO.....OhkO.
.OhwwkO...OhwwkO
.OkkkkO...OkkkkO
..OOOO.....OOOO.
................
................
................
''', GB))

GR_MOORING = SG('''
................
................
................
................
.....OOOOOO.....
....OhhhhwkO....
....OhwwwwkO....
....OkkkkkkO....
....OtTTttkO....
....OTttTtkO....
....OhwwwwkO....
....OhwwwwkO....
....OhwwwwkO....
....OkwwwkkO....
.....OOOOOO.....
................
''', GB)

GR_PUMPKIN = SG('''
................
................
................
................
.......Ok.......
......OkO.......
...OOOOkOOOO....
..OoyyoyyoyyoO..
.OoyYyoyYyoyyoO.
.OoyOOyyyOOyyoO.
.OoyyyyYyyyyyoO.
.OoyOyOyOyOyyoO.
.OooyOOOOOyyooO.
..OoooyooyoooO..
...OOOOOOOOOO...
................
''', GB)

MEMORIAL_TOP = '''
................................
...............OO...............
..............OHLO..............
.............OHLLSO.............
.............OHLLSO.............
............OHLLLSDO............
............OHLLLSDO............
............OHLeLSDO............
............OHLeESDO............
............OHLeLSDO............
............OHLLLSDO............
...........OHLLLLSSDO...........
...........OHLDDDDSDO...........
...........OHLLLLLSDO...........
...........OHLDDDLSDO...........
...........OHLLLLLSDO...........
'''
MEMORIAL_BOTTOM = '''
...........OHLDDDDSDO...........
...........OHLLLLLSDO...........
...........OHLLmLLSDO...........
.........OOOHLmmLSSDOOO.........
........OHHHHLLLLSSSSDDO........
........OHLLLLLLLLSSSSDO........
........ODDDDDDDDDDDDDDO........
.......OHHHHLLLLLSSSSSDDO.......
......OHLLLLLLLLLLSSSSSSDO......
......OmmLLLLLLLLLLSSSSmmO......
......ODDDDDDDDDDDDDDDDDDO......
.......OOOOOOOOOOOOOOOOOO.......
................................
................................
................................
................................
'''


def memorial():
    return stack(SG(MEMORIAL_TOP, GA, 32), SG(MEMORIAL_BOTTOM, GA, 32))


# ---------------------------------------------------------------- crypt

CR_SKULLS = SG('''
................
................
................
................
......OOOO......
.....OWWBBO.....
....OWOWBObO....
....OWBOBObO....
.OOOOBWBBbOOOO..
OWWBbOObbOOWBBO.
OWOBObOOOOWOBObO
OWBOBbObBOWBOBbO
OBWBBbOBbOBWBbbO
.OObbOObbOObbbO.
...OOO.OO.OOOO..
................
''', CA)

CANDLE_BASE = '''
................
................
................
................
................
..........OO....
...OO....OxxO...
..OxxO...OxxO...
..OxxO...OxxO...
..OxxO.OOOxxO...
..OxxOOxxOxxO...
..OxxOOxxOxxO...
.OOxxOOxxOxxOO..
OMMMMMMMMMMMMMO.
ODDDDDDDDDDDDDO.
.OOOOOOOOOOOOO..
'''


def candle_frames():
    frames = []
    for f in range(3):
        img = SG(CANDLE_BASE, CA)
        for (fx, fy) in ((3, 6), (7, 9), (10, 5)):
            tall = (f + fx) % 3 != 0
            img.set(fx, fy - 1, 'cry_flame')
            img.set(fx + 1, fy - 1, 'cry_flame_dk')
            img.set(fx + (f + fx) % 2, fy - 2, 'cry_flame_hi')
            if tall:
                img.set(fx + (f + 1) % 2, fy - 3, 'cry_flame')
        frames.append(img)
    return frames


CR_SARCOPHAGUS = stack(SG('''
................
...OOOOOOOOOO...
..OHHHHHHHHLMO..
.OHLLLLLLLLLMDO.
.OHLMMMMMMMLMDO.
.OHLMWWWWWMLMDO.
.OHLMWBWWBMLMDO.
.OHLMWWbWWMLMDO.
.OHLMMWWWMMLMDO.
.OHLLMMMMMLLMDO.
.OHLLLLLLLLLMDO.
.OHLMLLLLLMLMDO.
.OHLMLLLLLMLMDO.
.OHLLMLLLMLLMDO.
.OHLLLMLMLLLMDO.
.OHLLLLMLLLLMDO.
''', CS), SG('''
.OHLLLLMLLLLMDO.
.OHLLLMLMLLLMDO.
.OHLLMLLLMLLMDO.
.OHLLLLLLLLLMDO.
.OHLLLLLLLLLMDO.
.ODDDDDDDDDDDDO.
.OHHHHHHHHHHHMO.
.OMMMMMMMMMMMDO.
.ODDDDDDDDDDDDO.
..OOOOOOOOOOOO..
................
................
................
................
................
................
''', CS))

CR_COFFIN = stack(SG('''
................
................
.....OOOOOO.....
....OhhhhhkO....
...OhwwwwwwkO...
...OhwwIIwwkO...
..OhwwwIIwwwkO..
..OhwIIIIIIwkO..
..OhwIIIIIIwkO..
..OhwwwIIwwwkO..
..OhwwwIIwwwkO..
..OhwwwIIwwwkO..
..OhwwwiiwwwkO..
..OhwwwwwwwwkO..
..OhwwwwwwwwkO..
...OhwwwwwwkO...
''', CB), SG('''
...OhwwwwwwkO...
....OhwwwwkO....
....OkkkkkkO....
.....OOOOOO.....
................
................
................
................
................
................
................
................
................
................
................
................
''', CB))

BRAZIER_BOWL = '''
.OOOOOOOOOOOOOO.
OIIIIIIIIIIIIIIO
OijjjjjjjjjjjjiO
.OiiiiiiiiiiiiO.
..OjjjjjjjjjjO..
...OOOiijOOOO...
.....OIijO......
.....OIijO......
.....OIijO......
.....OIijO......
....OIIijjO.....
...OIiiijjjO....
..OMMMMMMMMMMO..
..ODDDDDDDDDDO..
...OOOOOOOOOO...
................
'''


def brazier_frames():
    frames = []
    for f in range(3):
        fire = Img(16, 16)
        for y in range(16):
            for x in range(16):
                cx = 8 + (1 if (f == 1 and y < 10) else (-1 if f == 2 and y < 9 else 0))
                wdt = max(0.0, (y - 3 - f % 2) * 0.55)
                d = abs(x + 0.5 - cx)
                if y >= 3 and d < wdt:
                    c = 'cry_gfire_hi' if d < wdt * 0.45 and y > 7 else 'cry_gfire'
                    if d > wdt - 1.0:
                        c = 'cry_wisp_dk'
                    fire.p[y][x] = c
        for (x, y) in ((5, 2 + f), (11, 4 - f), (9, 1 + f % 2)):
            fire.set(x, y, 'cry_gfire')
        frames.append(stack(fire, SG(BRAZIER_BOWL, CF)))
    return frames


CR_URN = SG('''
................
................
.....OOOOOO.....
....OYyyyyoO....
.....OyyyoO.....
....OYyyyyyoO...
...OYyyyyyyyoO..
..OYyYyyyyyyyoO.
..OYYyyooyyyyoO.
..OYyyoOOoyyyoO.
..OYyyyooyyyyoO.
...OYyyyyyyyoO..
....OoyyyyyooO..
.....OooooooO...
....OYyyyyyyoO..
....OOOOOOOOOO..
''', CB)

CR_STATUE = stack(SG('''
................
......OOOO......
.....OHLLMO.....
....OHLDDMMO....
....OHDKKDMO....
....OHDGgDMO....
....OHDKKDMO....
...OHLDDDDMDO...
...OHLLMMMMDO...
..OHLLLMMMMMDO..
..OHLLMLMMMMDO..
..OHLMLLMMMDDO..
..OHLMLLMMMDDO..
..OHLMLLMMMDDO..
..OHLMLLLMMDDO..
..OHLMLLLMMDDO..
''', CS), SG('''
..OHLMLLLMMDDO..
..OHLMLLLMMDDO..
..OHLMLLLLMDDO..
..OHLLMLLLMDDO..
..OHLLMLLLMDDO..
.OHHLLMMLLMMDDO.
.OHLLLLLLLLLLDO.
.ODDDDDDDDDDDDO.
.OHHHHHHHHHHHMO.
.OMMMMMMMMMMMDO.
.ODDDDDDDDDDDDO.
..OOOOOOOOOOOO..
................
................
................
................
''', CS))

CR_BANNER = stack(SG('''
.OOOOOOOOOOOOOO.
OYyyyyyyyyyyyyoO
.OOOOOOOOOOOOOO.
..OCcccccccccO..
..OCccccccccxO..
..OCcYyyyyycxO..
..OCcyOOOOocxO..
..OCcyOCCOocxO..
..OCcyOccOocxO..
..OCcyOOOOocxO..
..OCcYyyyyocxO..
..OCccccccccxO..
..OCccccccccxO..
..OCccccccccxO..
..OCcccccccxxO..
..OCcccccccxxO..
''', CB), SG('''
..OCcccccccxxO..
..OCccccccxxxO..
..OCcccxxccxxO..
..OCccxOOxcxxO..
..OCcxO..OxxxO..
..OCxO....OxxO..
..OOO......OOO..
................
................
................
................
................
................
................
................
................
''', CB))

CR_CHAINS = SG('''
..OO......OO....
.OIiO....OIiO...
.OiO......OiO...
.OIiO....OIiO...
..OjO.....OjO...
.OIiO....OIiO...
.OiO......OiO...
.OIiO....OIiO...
..OjO.....OjO...
.OIiO....OIiO...
.OiO......OiO...
.OIiO....OIiO...
..OO.....OIIO...
........OIjjIO..
.........OjjO...
..........OO....
''', CB)

THRONE = '''
................................................
...................OOOOOOOOOO...................
..................OWWWBBBBBbbO..................
.......OO........OWBOBWBBObBbO........OO........
......OWbO.......OWBOBWBBObBbO.......ObbO.......
......OWBbO......OWWBBOOBBBbbO......ObbbO.......
.......OWBbO.....OOWBBBbbbbbOO.....ObbbO........
........OWBbO...OWBOOBbbbbOOBbO...ObBbO.........
.........OWBbOOOWBBBBOOOOOOBBbbOOObBbO..........
..........OWBBWBBbbObOYYyObBbbBBBbBbO...........
...........OWBBBbbObOYyyyoObbbBBBbbO............
...........OWBbObbOqOyYyyoOqObbObbbO............
...........OWBbOObOqRRRRrrrqOObObbbO............
...........OWBbObbOqRrrrrrrqObbObbbO............
...........OWBbObbOqRrrrrrrqObbObbbO............
...........OWBbObbOqRrrrrrrqObbObbbO............
..........OWBBbObbOqRrrrrrrqObbObbbbO...........
..........OWBBbObbOqRrrrrrrqObbObbbbO...........
..........OWBbbObbOqRrrrrrrqObbObbbbO...........
.........OWWBBOOOOOOOOOOOOOOOOOOOObbbO..........
.........OWBBBWWWWBBBBBBBBBBbbbbbbbbO...........
.........OWBbbbbbbbbbbbbbbbbbbbbbbbbO...........
.........OWBbOOOOOOOOOOOOOOOOOOOOObbO...........
.........OWBbO.OWBbO.OWBbO.OWBbO.ObbO...........
.........OWBbO.OWBbO.OWBbO.OWBbO.ObbO...........
........OWWBBbOWWBbbOWWBbbOWWBbbObbbbO..........
........OWBBBBBBBBBBBBBBBBBBBBBBBBBbbO..........
........OMMMMMMMMMMMMMMMMMMMMMMMMMMMDO..........
........ODDDDDDDDDDDDDDDDDDDDDDDDDDDDO..........
.........OOOOOOOOOOOOOOOOOOOOOOOOOOOO...........
................................................
................................................
'''


def throne():
    img = SG(THRONE, CT, 48)
    out = Img(48, 48)
    out.paste(img, 0, 14)
    return out


PEDESTAL = '''
................
................
................
................
................
................
....OOOOOOOO....
...OHHHHHHHLO...
...OLMMMMMMDO...
....OLMMMMDO....
....OLMMMMDO....
....OLMMMMDO....
....OLMMMMDO....
...OHLLLLLLDO...
...ODDDDDDDDO...
....OOOOOOOO....
'''


def pedestal_frames():
    frames = []
    for f in range(2):
        img = SG(PEDESTAL, CF)
        for (x, y, c) in ((7, 3, 'cry_flame_hi'), (8, 3, 'cry_flame'), (7, 4, 'cry_flame'),
                          (8, 4, 'cry_flame_dk'), (7, 5, 'cry_flame_dk'), (8, 5, 'cry_flame')):
            img.set(x, y - f, c)
        img.set(8 - f, 2 - f, 'cry_flame')
        frames.append(img)
    return frames


CR_PLAQUE = SG('''
................
................
................
..OOOOOOOOOOOO..
.OHHHHHHHHHHHLO.
.OHLLLLLLLLLLMO.
.OHLMMLMLMMLLMO.
.OHLLLLLLLLLLMO.
.OHLMLMMMLMLLMO.
.OHLLLLLLLLLLMO.
.OHLMMLMMLMLLMO.
.OLMMMMMMMMMMDO.
.ODDDDDDDDDDDDO.
..OOOOOOOOOOOO..
................
................
''', CA)


DECOR = [
    # ---- grim (ASHEN FIELDS, GRAVEWOOD, DUSKMERE)
    Decor('GR_SIGN', GRIM, GR_SIGN, doc='weathered wooden signboard'),
    Decor('GR_GRAVE', GRIM, GR_GRAVE, doc='mossy headstone',
          examine='An old headstone. The name has worn away, but someone left a clean pebble on top.'),
    Decor('GR_CROSS', GRIM, GR_CROSS, doc='stone grave cross',
          examine='A stone cross. Ash has settled in every carved letter.'),
    Decor('GR_FENCE', GRIM, GR_FENCE, doc='iron graveyard railing (tiles left-right)'),
    Decor('GR_BONES', GRIM, GR_BONES, doc='bleached bones in the ash',
          examine='Old bones, bleached white. HOLLOW kin shed them when they rebuild.'),
    Decor('GR_SHRUB', GRIM, GR_SHRUB, doc='dead thornbush'),
    Decor('GR_STUMP', GRIM, GR_STUMP, doc='charred stump',
          examine='A stump, burnt hollow a century ago. New shoots are trying anyway.'),
    Decor('GR_CART', GRIM, GR_CART, doc='burnt farm cart, one wheel gone',
          examine='A farm cart, charred black. It has sat here since the Burning.'),
    Decor('GR_LANTERN', GRIM, frames=lantern_post_frames(), period=24, top='X/.',
          doc='Duskmere lantern post (flickers)',
          examine='A lantern post. Duskmere keeps a light burning on every corner, day and night.'),
    Decor('GR_WISP', GRIM, frames=wisp_frames(), period=12, top='X', solid='.',
          doc='drifting foxfire wisp (walk-through)'),
    Decor('GR_BELL', GRIM, GR_BELL, top='X/.', doc="Duskmere's mire bell",
          examine='The mire bell. It rang every night of the Burning, and has hung silent for a hundred years.'),
    Decor('GR_MOORING', GRIM, GR_MOORING, doc='mooring post with rope'),
    Decor('GR_PUMPKIN', GRIM, GR_PUMPKIN, doc='carved pumpkin',
          examine='A carved pumpkin. Duskmere folk set them out to show HOLLOW kin the way home.'),
    Decor('GR_MEMORIAL', GRIM, memorial(), top='XX/..', doc='the Burning memorial obelisk',
          examine='THE BURNING. For the fields, the farms and the folk of the Ashen March. May the ash grow green.'),
    # ---- crypt (LANTERN CRYPT, THE OSSUARY, BONE THRONE)
    Decor('CR_SKULLS', CRYPT, CR_SKULLS, doc='heap of skulls',
          examine='Skulls, heaped with care. Each has a date scratched above the eyes.'),
    Decor('CR_CANDLES', CRYPT, frames=candle_frames(), period=10, doc='vigil candles',
          examine='Vigil candles. Someone keeps them lit, even down here.'),
    Decor('CR_SARCOPHAGUS', CRYPT, CR_SARCOPHAGUS, doc='stone sarcophagus (1x2)',
          examine='A stone sarcophagus. The lid shows a warden with a lantern on her chest.'),
    Decor('CR_COFFIN', CRYPT, CR_COFFIN, doc='iron-bound coffin (1x2)',
          examine='An iron-bound coffin, nailed shut. Something inside rattles, politely.'),
    Decor('CR_BRAZIER', CRYPT, frames=brazier_frames(), period=8, top='X/.',
          doc='brazier of green foxfire',
          examine='Green fire, cold to the touch: foxfire fed on bone dust.'),
    Decor('CR_URN', CRYPT, CR_URN, doc='gilded burial urn',
          examine='A gilded urn. The ash inside is still faintly warm.'),
    Decor('CR_STATUE', CRYPT, CR_STATUE, top='X/.', doc='hooded warden statue with wisp eyes',
          examine='A hooded warden of stone. Its eyes glow the same green as the foxfire.'),
    Decor('CR_BANNER', CRYPT, CR_BANNER, doc='Lantern Crypt banner (hangs on walls)'),
    Decor('CR_CHAINS', CRYPT, CR_CHAINS, doc='hanging chains'),
    Decor('CR_THRONE', CRYPT, throne(), top='XXX/.../...', solid='.../XXX/XXX',
          doc='the BONE THRONE (3x3)'),
    Decor('CR_PEDESTAL', CRYPT, frames=pedestal_frames(), period=14,
          doc='lantern pedestal (Hall crest)',
          examine='A pedestal holding a single flame. It never flickers, however hard you breathe.'),
    Decor('CR_PLAQUE', CRYPT, CR_PLAQUE, doc='engraved stone plaque'),
]
