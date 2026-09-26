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


# the decor catalogue is appended at the end of this file (DECOR)
DECOR = []
