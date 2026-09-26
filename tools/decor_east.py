#!/usr/bin/env python3
"""W-EAST decor catalog: LUMEN CITY, COPPERLINE ROAD, ELDERWOOD HEART and
the eastern interiors (owner: W-EAST, docs/EXPANSION.md 9 and 10.1).

Palette plan (every 8x8 tile fits one bank of its tileset):

  city  bank 5  teal/copper: b_out, rt_*, fx_org, sg_hi, sg_base, p_yel,
                white, st_lt, st_mid, st_dk, wd_dk   (lamps, coils, bikes)
  city  bank 4  terracotta: rf_*, wl_*, st_*       (cafe parasols)
  wild  bank 3  props (OL): stone, wood, fire, water, leaves (mine, carts)
  wild  bank 4  nature (WL): slate, storm glow, heartglass, reds, leaves
  wild  bank 2  trees (TL): the elder tree and ferns
  interior bank 4  metal, glass and science (pylons, vats, cabinets)
  interior bank 7  shop goods: metal, ceramic, red, blue, gold (bikes, gears)

Light comes from the top-left; every object has a 1px dark outline and no
ground shadow. Nothing here bakes in ground (the art lint checks).
"""

import math
from pixelart import Img, Decor
from decor_outdoor import SG, OL, WL, TL, outline, blob, in_ell
from decor_indoor import IL

C = ['city']
W = ['wild']
I = ['interior']

# city teal/copper bank (5)
CL = {'.': None, 'O': 'b_out', '1': 'rt_hi', '2': 'rt_lt', '3': 'rt_base', '4': 'rt_dk',
      '5': 'rt_dkr', 'o': 'fx_org', 'c': 'sg_hi', 'C': 'sg_base', 'y': 'p_yel', 'w': 'white',
      'l': 'st_lt', 'm': 'st_mid', 'd': 'st_dk', 'K': 'wd_dk'}

# city terracotta bank (4)
RL = {'.': None, 'O': 'b_out', '1': 'rf_hi', '2': 'rf_lt', '3': 'rf_base', '4': 'rf_dk',
      '5': 'rf_dkr', 'W': 'wl_hi', 'w': 'wl_base', 'v': 'wl_dk', 'h': 'st_hi', 'l': 'st_lt',
      'm': 'st_mid', 'd': 'st_dk', 'K': 'wd_dk'}


def line(img, x0, y0, x1, y1, c):
    """Bresenham line."""
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        img.set(x0, y0, c)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def dots(img, pts, c):
    for (x, y) in pts:
        img.set(x, y, c)


# ===========================================================================
# LUMEN CITY
# ===========================================================================

def city_lamp():
    post = ['......O45O......'] * 16
    return SG('\n'.join([
        '................',
        '................',
        '......OOOO......',
        '.....O3223O.....',
        '....O322333O....',
        '....OOOOOOOO....',
        '.....OwwccO.....',
        '.....OwcccO.....',
        '.....OccCCO.....',
        '.....OcCCCO.....',
        '.....OOOOOO.....',
    ] + post + [
        '.....OO45OO.....',
        '....O444455O....',
        '....O555555O....',
        '.....OOOOOO.....',
        '................',
    ]), CL)


def tesla_coil_frames():
    body = SG('''
................
................
................
................
................
....OOOOOOOO....
..OOllllllllOO..
.OlllmmmmmmmldO.
.OmmmmmmmmmmddO.
..OOddddddddOO..
.....OOOOOO.....
.....OyooKO.....
.....OKKKKO.....
.....OyooKO.....
.....OKKKKO.....
.....OyooKO.....
.....OKKKKO.....
.....OyooKO.....
.....OKKKKO.....
.....OyooKO.....
.....OKKKKO.....
.....OyooKO.....
.....OKKKKO.....
.....OyooKO.....
....OOOOOOOO....
...OllllllllmO..
...OmmmmmmmmdO..
...OmmmmmmmmdO..
...OdddddddddO..
...OOOOOOOOOOO..
................
................
''', CL)
    arcs = [
        [(1, 6), (0, 5), (1, 4), (0, 3), (14, 6), (15, 5), (14, 4), (15, 3), (14, 2),
         (6, 4), (7, 3), (6, 2), (7, 1), (6, 0)],
        [(1, 7), (0, 6), (0, 5), (1, 4), (2, 3), (14, 7), (15, 6), (15, 5), (14, 4),
         (9, 4), (8, 3), (9, 2), (10, 1), (9, 0)],
    ]
    frames = []
    for pts in arcs:
        f = body.copy()
        for i, (x, y) in enumerate(pts):
            f.set(x, y, 'sg_hi' if i % 3 else 'white')
        frames.append(f)
    return frames


def parked_bike():
    img = Img(16, 16)
    for (cx, cy) in ((4, 11), (12, 11)):
        for y in range(16):
            for x in range(16):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if 2.3 <= d < 3.4:
                    img.set(x, y, 'st_dk')
        img.set(cx, cy, 'st_lt')
        img.set(cx - 1, cy - 1, 'st_mid')
    # frame
    line(img, 4, 11, 7, 11, 'rt_dk')
    line(img, 4, 11, 6, 6, 'rt_base')
    line(img, 6, 6, 7, 11, 'rt_base')
    line(img, 6, 6, 10, 6, 'rt_lt')
    line(img, 7, 11, 10, 7, 'rt_base')
    line(img, 10, 6, 12, 11, 'rt_dk')
    dots(img, [(5, 5), (6, 5), (7, 5)], 'wd_dk')
    dots(img, [(10, 4), (11, 4), (10, 5)], 'st_mid')
    img.set(8, 11, 'fx_org')
    return outline(img)


def cafe_table():
    img = Img(16, 32)
    # parasol: a dome with red and white gores
    for y in range(2, 12):
        for x in range(16):
            if not in_ell(x, y, 8, 11, 7.6, 8.6) or y > 10:
                continue
            ang = math.atan2(y + 0.5 - 11, x + 0.5 - 8)
            gore = int((ang + math.pi) / (math.pi / 6)) % 2
            c = 'rf_base' if gore else 'wl_hi'
            if y >= 9:
                c = 'rf_dk' if gore else 'wl_dk'
            elif x < 6 and y < 7:
                c = 'rf_lt' if gore else 'wl_hi'
            img.set(x, y, c)
    img.set(8, 1, 'st_mid')
    # scalloped rim
    for x in range(1, 15):
        if x % 3 != 0:
            img.set(x, 11, 'rf_dk' if (x // 3) % 2 else 'wl_dk')
    # pole
    for y in range(12, 22):
        img.set(8, y, 'st_mid')
    # round table top and legs
    for y in range(21, 26):
        for x in range(2, 14):
            if in_ell(x, y, 8, 23, 6.2, 2.6):
                img.set(x, y, 'wl_hi' if y < 23 else 'wl_base')
    for x in range(3, 13):
        img.set(x, 26, 'wl_dk')
    dots(img, [(8, 27), (8, 28), (7, 29), (9, 29)], 'st_dk')
    # a cup
    dots(img, [(5, 22), (6, 22)], 'rf_lt')
    img.set(5, 21, 'st_hi')
    return outline(img)


def railing():
    return SG('''
................
................
................
................
................
................
OOOOOOOOOOOOOOOO
2222222222222222
4444444444444444
OOOOOOOOOOOOOOOO
.O4O....O4O.....
.O3O....O3O.....
.O4O....O4O.....
OOOOOOOOOOOOOOOO
3333333333333333
OOOOOOOOOOOOOOOO
''', CL)


def beacon_frames():
    """The LUMEN BEACON: a lattice tower of patina copper crowned with a
    glass globe of trapped lightning (2x3, plaza centrepiece)."""
    frames = []
    for f in range(2):
        img = Img(32, 48)
        # stone plinth
        for y in range(40, 47):
            for x in range(6, 26):
                c = 'st_lt' if y < 42 else ('st_mid' if y < 45 else 'st_dk')
                if x in (6, 25):
                    c = 'st_dk'
                img.set(x, y, c)
        # lattice legs (taper from the plinth to the globe)
        for y in range(16, 40):
            t = (y - 16) / 24.0
            half = int(3 + 7 * t)
            for side in (-1, 1):
                x = 16 + side * half - (1 if side > 0 else 0)
                img.set(x, y, 'rt_dk')
                img.set(x - side, y, 'rt_base')
            if y % 4 == 0:
                for x in range(16 - half, 16 + half):
                    img.set(x, y, 'rt_lt' if y % 8 == 0 else 'rt_dk')
            else:
                # cross bracing
                k = y % 4
                for s in (-1, 1):
                    xx = 16 + s * (half - 1 - k * (half - 1) // 3) - (1 if s > 0 else 0)
                    img.set(xx, y, 'rt_dkr')
        # copper collar under the globe
        for x in range(11, 21):
            img.set(x, 15, 'fx_org' if x < 16 else 'wd_dk')
            img.set(x, 14, 'p_yel' if x < 14 else 'fx_org')
        # the globe
        for y in range(1, 14):
            for x in range(8, 24):
                if in_ell(x, y, 16, 7.5, 7.2, 6.6):
                    c = 'sg_base'
                    if in_ell(x, y, 13.5, 5, 3, 2.6):
                        c = 'sg_hi'
                    img.set(x, y, c)
        # the lightning inside (flickers)
        bolt = [(16, 3), (15, 4), (16, 5), (17, 6), (16, 7), (15, 8), (14, 9), (15, 10), (16, 11)] if f == 0 \
            else [(15, 3), (16, 4), (17, 5), (16, 6), (15, 7), (16, 8), (17, 9), (18, 10), (17, 11)]
        for (x, y) in bolt:
            img.set(x, y, 'white')
            img.set(x + 1, y, 'p_yel')
        img.set(11, 4, 'white')
        frames.append(outline(img))
    return frames


# ===========================================================================
# COPPERLINE ROAD (route tileset)
# ===========================================================================

def mine_mouth():
    """A timbered adit into the old copper workings, boarded shut (3x2)."""
    img = Img(48, 32)
    # rock face around the opening
    for y in range(0, 32):
        for x in range(48):
            if in_ell(x, y, 24, 30, 24, 30):
                img.set(x, y, 'st_mid' if (x * 7 + y * 3) % 11 else 'st_dk')
    for y in range(2, 32):
        for x in range(2, 46):
            if in_ell(x, y, 24, 30, 22, 28) and (x + y) % 9 == 0:
                img.set(x, y, 'st_lt')
    # dark tunnel
    for y in range(9, 32):
        for x in range(14, 34):
            img.set(x, y, 'b_out')
    # timber frame: posts and a lintel
    for y in range(8, 32):
        for x in (12, 13, 34, 35):
            img.set(x, y, 'wd_base' if x in (12, 34) else 'wd_dk')
    for x in range(10, 38):
        img.set(x, 6, 'wd_lt')
        img.set(x, 7, 'wd_base')
        img.set(x, 8, 'wd_dk')
    # boards across
    for by in (13, 20, 26):
        for x in range(13, 35):
            img.set(x, by, 'wd_lt')
            img.set(x, by + 1, 'wd_base')
            img.set(x, by + 2, 'wd_dk')
        img.set(15, by + 1, 'st_lt')
        img.set(32, by + 1, 'st_lt')
    # a lantern hook and a warning plate
    dots(img, [(38, 10), (38, 11), (37, 12), (38, 12), (39, 12), (38, 13)], 'fx_org')
    return outline(img)


def rails_h():
    return SG('''
................
................
................
OOOOOOOOOOOOOOOO
mmmmmmmmmmmmmmmm
dddddddddddddddd
.BK..BK..BK..BK.
.BK..BK..BK..BK.
.BK..BK..BK..BK.
.BK..BK..BK..BK.
OOOOOOOOOOOOOOOO
mmmmmmmmmmmmmmmm
dddddddddddddddd
................
................
................
''', OL)


def rails_v():
    return SG('''
..OmdK.....OmdK.
..Omd......Omd..
BBOmdBBBBBBOmdBB
KKOmdKKKKKKOmdKK
..Omd......Omd..
..Omd......Omd..
..Omd......Omd..
BBOmdBBBBBBOmdBB
KKOmdKKKKKKOmdKK
..Omd......Omd..
..Omd......Omd..
..Omd......Omd..
BBOmdBBBBBBOmdBB
KKOmdKKKKKKOmdKK
..Omd......Omd..
..Omd......Omd..
''', OL)


def ore_cart():
    return SG('''
................
................
................
....OOO.OOO.....
...OoyoOoooOO...
..OoyooooKoooO..
.OOOOOOOOOOOOOO.
.OlllllllllllmO.
.OlmmmmmmmmmmdO.
.OlmdmmmmmmdmdO.
.OlmmmmmmmmmmdO.
.OmddddddddddddO
..OOOOOOOOOOOOO.
...OmdO....OmdO.
...OddO....OddO.
....OO......OO..
''', OL)


def ore_pile():
    img = blob(16, 16, [(8, 10.5, 6.8, 4.6), (5.5, 9, 3.5, 3.2), (10.5, 8.5, 3.6, 3.4)],
               ['st_lt', 'st_mid', 'st_mid', 'st_dk'], 'b_out', seed=5)
    for (x, y) in ((6, 8), (9, 7), (11, 10), (4, 11), (8, 12), (12, 12)):
        img.set(x, y, 'fx_org')
        img.set(x + 1, y, 'wd_dk')
    img.set(6, 7, 'p_yel')
    img.set(9, 6, 'p_yel')
    return img


def copper_rock():
    img = blob(16, 16, [(8, 9.5, 6.8, 5.6), (6, 7.5, 3.8, 3.4)],
               ['st_lt', 'st_mid', 'st_mid', 'st_dk'], 'b_out', seed=11)
    # a vein of native copper
    for (x, y) in ((4, 11), (5, 10), (6, 10), (7, 9), (8, 9), (9, 8), (10, 8), (11, 7)):
        img.set(x, y, 'fx_org')
        img.set(x, y + 1, 'wd_dk')
    img.set(7, 8, 'p_yel')
    return img


def headframe():
    """A timber winding headframe with a sheave wheel (2x3)."""
    img = Img(32, 48)
    # legs (an A-frame) and cross beams
    line(img, 6, 46, 13, 8, 'wd_base')
    line(img, 7, 46, 14, 8, 'wd_dk')
    line(img, 25, 46, 18, 8, 'wd_base')
    line(img, 26, 46, 19, 8, 'wd_dk')
    line(img, 20, 46, 16, 12, 'wd_lt')
    for y in (20, 31, 42):
        t = (46 - y) / 38.0
        x0 = int(6 + 7 * t)
        x1 = int(26 - 7 * t)
        for x in range(x0, x1 + 1):
            img.set(x, y, 'wd_lt')
            img.set(x, y + 1, 'wd_dk')
    line(img, 8, 42, 23, 21, 'wd_base')
    line(img, 23, 42, 9, 21, 'wd_base')
    # sheave wheel
    for y in range(0, 16):
        for x in range(8, 24):
            d = math.hypot(x + 0.5 - 16, y + 0.5 - 7.5)
            if 5.2 <= d < 7:
                img.set(x, y, 'st_dk' if y > 8 else 'st_mid')
            elif d < 1.6:
                img.set(x, y, 'st_lt')
    for k in range(6):
        a = k * math.pi / 3
        for r in range(2, 6):
            img.set(int(16 + r * math.cos(a)), int(7.5 + r * math.sin(a)), 'st_mid')
    # the cable down into the shaft
    for y in range(8, 44):
        img.set(22, y, 'st_dk')
    # a little platform at the foot
    for x in range(4, 28):
        img.set(x, 45, 'wd_lt')
        img.set(x, 46, 'wd_base')
    return outline(img)


# ===========================================================================
# ELDERWOOD HEART (route tileset)
# ===========================================================================

def elder_tree():
    """The Elder: a vast old oak, 3x3. The crown (top two rows) is drawn over
    people; the trunk and roots on the bottom row are solid."""
    img = Img(48, 48)
    # roots and trunk
    for y in range(24, 47):
        for x in range(10, 38):
            t = (y - 24) / 22.0
            half = 6 + 12 * t ** 3
            if abs(x + 0.5 - 24) <= half:
                dx = x + 0.5 - 24
                c = 'k_base'
                if dx < -half + 3:
                    c = 'k_lt'
                elif dx > half - 3:
                    c = 'k_dk'
                if (x * 3 + y) % 7 == 0:
                    c = 'k_dk'
                img.set(x, y, c)
    # a hollow at the foot
    for y in range(37, 44):
        for x in range(21, 28):
            if in_ell(x, y, 24.5, 42, 3.2, 5):
                img.set(x, y, 't_out')
    # moss on the roots
    for (x, y) in ((13, 45), (14, 44), (34, 45), (33, 44), (18, 40), (30, 39), (19, 30)):
        img.set(x, y, 't_lt')
        img.set(x + 1, y, 't_base')
    # the crown
    clumps = [(24, 13, 16, 11), (12, 17, 9, 8), (36, 17, 9, 8), (24, 6, 11, 6),
              (16, 9, 8, 6), (32, 9, 8, 6), (24, 21, 12, 5)]
    crown = blob(48, 30, clumps, ['t_hi', 't_lt', 't_base', 't_mid', 't_dk'], 't_out', seed=23,
                 dither=True)
    img.paste(crown, 0, 0)
    img = outline(img, 't_out')
    return img


def fern():
    img = Img(16, 16)
    for (x0, y0, x1, y1) in ((8, 14, 2, 6), (8, 14, 14, 6), (8, 14, 5, 3), (8, 14, 11, 3),
                             (8, 14, 8, 2)):
        line(img, x0, y0, x1, y1, 't_base')
    for (x0, y0, x1, y1) in ((8, 14, 2, 6), (8, 14, 14, 6), (8, 14, 5, 3), (8, 14, 11, 3),
                             (8, 14, 8, 2)):
        steps = max(abs(x1 - x0), abs(y1 - y0))
        for s in range(2, steps, 2):
            x = x0 + (x1 - x0) * s // steps
            y = y0 + (y1 - y0) * s // steps
            img.set(x - 1, y, 't_lt')
            img.set(x + 1, y - 1, 't_mid')
    return outline(img, 't_out')


def glowcap_frames():
    frames = []
    for f in range(2):
        img = Img(16, 16)
        caps = [(4, 9, 3.2, 2.2), (10, 7, 3.8, 2.6), (12, 12, 2.6, 1.8)]
        for (cx, cy, rx, ry) in caps:
            for y in range(16):
                for x in range(16):
                    if in_ell(x, y, cx, cy, rx, ry) and y <= cy:
                        c = 'hg_base' if f == 0 else 'hg_hi'
                        if y < cy - ry * 0.4 and x < cx:
                            c = 'hg_hi' if f == 0 else 'white'
                        img.set(x, y, c)
            for y in range(int(cy) + 1, int(cy) + 4):
                img.set(int(cx), y, 'white')
                img.set(int(cx) - 1, y, 'sl_hi')
        # spores drifting up
        sp = [(3, 3), (13, 2), (8, 1)] if f == 0 else [(4, 2), (12, 4), (7, 3)]
        for (x, y) in sp:
            img.set(x, y, 'hg_hi')
        frames.append(outline(img))
    return frames


def stag_altar():
    """A mossy stone altar carved with antlers: where SYLVARCH is met (2x2)."""
    img = Img(32, 32)
    # slab
    for y in range(14, 30):
        for x in range(3, 29):
            c = 'sl_base'
            if y < 17:
                c = 'sl_hi'
            elif y > 26:
                c = 'sl_dk'
            elif x < 5:
                c = 'sl_hi'
            elif x > 26:
                c = 'sl_dk'
            img.set(x, y, c)
    # antler carving glowing faintly
    ant = [(16, 26), (16, 25), (16, 24), (16, 23), (15, 22), (14, 21), (13, 20), (12, 19),
           (17, 22), (18, 21), (19, 20), (20, 19), (13, 22), (12, 22), (19, 22), (20, 22),
           (11, 20), (21, 20)]
    for (x, y) in ant:
        img.set(x, y, 'sg_base')
    img.set(16, 21, 'sg_hi')
    # moss and a few white flowers
    for x in range(3, 29):
        if (x * 5) % 7 < 4:
            img.set(x, 14, 't_lt')
        if (x * 3) % 5 < 2:
            img.set(x, 15, 't_base')
    for (x, y) in ((6, 13), (7, 12), (24, 13), (25, 12), (10, 13)):
        img.set(x, y, 't_lt')
    dots(img, [(7, 11), (25, 11), (10, 12)], 'white')
    # a standing antler crown on top
    for (x0, y0, x1, y1) in ((16, 13, 10, 4), (16, 13, 22, 4), (13, 9, 9, 8), (19, 9, 23, 8),
                             (11, 6, 8, 2), (21, 6, 24, 2)):
        line(img, x0, y0, x1, y1, 'sl_hi')
    return outline(img)


# ===========================================================================
# INTERIORS
# ===========================================================================

# interior bank 4: metal, glass and science
ML = {'.': None, 'O': 'i_out', 'A': 'bb_lt', 'B': 'bb_base', 'K': 'bb_dk', 'Z': 'white',
      'M': 'mt_hi', 'N': 'mt_base', 'E': 'mt_dk', 'a': 'gl_hi', 'b': 'gl_base', 'd': 'gl_dk',
      'S': 'sc_hi', 's': 'sc_base', 'z': 'sc_dk', 'r': 'rd_hi'}

# interior bank 7: shop goods
GL = {'.': None, 'O': 'i_out', 'M': 'mt_hi', 'N': 'mt_base', 'E': 'mt_dk', 'C': 'ck_hi',
      'c': 'ck_base', 'l': 'ck_line', 'L': 'ck_dk', 'R': 'rd_hi', 'r': 'rd_base', 'U': 'bl_hi',
      'u': 'bl_base', 'Y': 'gd_hi', 'y': 'gd_base', 'Z': 'white'}


def pylon_frames():
    """A Volt Hall pylon: a squat steel post with a glass insulator cap; the
    charge in the cap flickers. Solid (the hall's walls are made of them)."""
    base = SG('''
................
.....OOOOOO.....
....OaaaabbO....
....OaZabbdO....
....ObbbbddO....
.....OOOOOO.....
......ONEO......
.....OMNNEO.....
.....OMNNEO.....
.....OMNNEO.....
.....OMNNEO.....
....OMMNNNEO....
...OMMNNNNEEO...
...ONNNNNNEEO...
...OEEEEEEEEO...
....OOOOOOOO....
''', ML)
    frames = [base]
    f = base.copy()
    for (x, y) in ((6, 2), (7, 3), (8, 2), (9, 3)):
        f.set(x, y, 'white')
    frames.append(f)
    return frames


def resonance_coil():
    return SG('''
................
................
.....OOOOOO.....
...OOMMMMNNOO...
..OMMNNNNNNEEO..
..ONNNNNNNNEEO..
...OOEEEEEEOO...
......ONEO......
.....OYyyyO.....
.....OyyyEO.....
.....OYyyyO.....
.....OyyyEO.....
.....OYyyyO.....
.....OyyyEO.....
.....OYyyyO.....
.....OyyyEO.....
.....OYyyyO.....
.....OyyyEO.....
.....OYyyyO.....
.....OyyyEO.....
.....OYyyyO.....
.....OyyyEO.....
....OOOOOOOO....
...OMMMMMMNEO...
..OMNNNNNNNNEO..
..ONNNNNNNNNEO..
..OEEEEEEEEEEO..
...OOOOOOOOOO...
................
................
................
................
''', GL)


def energy_vat_frames():
    frames = []
    for f in range(2):
        img = SG('''
................
................
....OOOOOOOO....
...OMMMMMMNEO...
...ONNNNNNNEO...
...OOOOOOOOOO...
...OaaSSSSsdO...
...OaSSSSssdO...
...OaSSsSSsdO...
...OaSSSSSsdO...
...OaSsSSssdO...
...OasSSSSsdO...
...OaSSSSssdO...
...OaSSsSSsdO...
...OassSSssdO...
...OasssssszO...
...OaSSsSSsdO...
...OaSSSSssdO...
...OasSSSSsdO...
...OaSSSSssdO...
...OasSSsSsdO...
...OassssszzO...
...OOOOOOOOOO...
...OMMMMMMNEO...
..OMNNNNNNNNEO..
..ONNNrNNrNNEO..
..OEEEEEEEEEEO..
...OOOOOOOOOO...
................
................
................
................
''', ML)
        # rising bubbles
        bub = [(6, 18), (8, 13), (7, 9), (9, 16)] if f == 0 else [(7, 17), (6, 12), (9, 10), (8, 19)]
        for (x, y) in bub:
            img.set(x, y, 'white')
        frames.append(img)
    return frames


def dynamo():
    return SG('''
................................
................................
................................
................................
.....OOOOOOOOOOOOOO.............
....OMMMMMMMMMMMMNNO...OOOO.....
...OMNNNNNNNNNNNNNNEO.OMMNEO....
...OMNyYyYyYyYyYyNNEOOMNNNEEO...
...ONNyyyyyyyyyyyNNEOONNNNNEO...
...ONNyYyYyYyYyYyNNEONNNEENNEO..
...ONNyyyyyyyyyyyNNEOENNEENNEO..
...ONNNNNNNNNNNNNNNEOONNNNNNEO..
...OEEEEEEEEEEEEEEEEOOENNNNEEO..
....OOOOOOOOOOOOOOOO..OEEEEEO...
...OMMMMMMMMMMMMMMMMMMMMMMMNO...
...OEEEEEEEEEEEEEEEEEEEEEEEEO...
''', GL, w=32)


def bike_display():
    img = Img(32, 16)
    stand = SG('''
................................
................................
................................
................................
................................
................................
................................
................................
................................
................................
................................
................................
................................
..OOOOOOOOOOOOOOOOOOOOOOOOOOOO..
..ONNNNNNNNNNNNNNNNNNNNNNNNNNO..
..OOOOOOOOOOOOOOOOOOOOOOOOOOOO..
''', GL, w=32)
    img.paste(stand, 0, 0)
    for (ox, col) in ((0, 'rd_base'), (15, 'bl_base')):
        b = Img(16, 16)
        for (cx, cy) in ((4, 10), (12, 10)):
            for y in range(16):
                for x in range(16):
                    d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                    if 2.2 <= d < 3.3:
                        b.set(x, y, 'mt_dk')
            b.set(cx, cy, 'mt_hi')
        line(b, 4, 10, 7, 10, col)
        line(b, 4, 10, 6, 5, col)
        line(b, 6, 5, 7, 10, col)
        line(b, 6, 5, 10, 5, col)
        line(b, 7, 10, 10, 6, col)
        line(b, 10, 5, 12, 10, 'mt_base')
        dots(b, [(5, 4), (6, 4), (7, 4)], 'ck_dk')
        dots(b, [(10, 3), (11, 3)], 'mt_base')
        img.paste(outline(b, 'i_out'), ox, -1)
    return img


def gears():
    """Brass clockwork gears on the wall of the Clockwork Spire (2x2)."""
    img = Img(32, 32)

    def gear(cx, cy, r, teeth, c_lt, c_dk, phase=0.0):
        for y in range(32):
            for x in range(32):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                d = math.hypot(dx, dy)
                a = math.atan2(dy, dx) + phase
                tooth = (math.cos(a * teeth) > 0.2)
                if d < r - 1.5 or (d < r + 0.8 and tooth):
                    if d < 2.2:
                        img.set(x, y, 'mt_dk')
                    elif d < r * 0.45:
                        img.set(x, y, c_lt)
                    elif r * 0.45 <= d < r * 0.62:
                        img.set(x, y, 'mt_dk' if (int((a + math.pi) * 4 / math.pi)) % 2 else c_dk)
                    else:
                        img.set(x, y, c_lt if dx + dy < 0 else c_dk)
    gear(11, 12, 10, 10, 'gd_hi', 'gd_base')
    gear(24, 23, 7, 8, 'mt_hi', 'mt_base', 0.3)
    gear(25, 7, 5, 6, 'gd_hi', 'gd_base', 0.2)
    return outline(img, 'i_out')


def file_cabinet():
    return SG('''
................
................
................
................
................
................
................
..OOOOOOOOOOOO..
..OMMMMMMMMMNO..
..OMNNNNNNNNEO..
..OMNNNEENNNEO..
..OMNNNNNNNNEO..
..OMOOOOOOOOEO..
..OMOddddddOEO..
..OMOOOOOOOOEO..
..OMNNNNNNNNEO..
..OMNNNEENNNEO..
..OMNNNNNNNNEO..
..OMOOOOOOOOEO..
..OMOddddddOEO..
..OMOOOOOOOOEO..
..OMNNNNNNNNEO..
..OMNNNEENNNEO..
..OMNNNNNNNNEO..
..OMOOOOOOOOEO..
..OMOddddddOEO..
..OMOOOOOOOOEO..
..OEEEEEEEEEEO..
..OOOOOOOOOOOO..
................
................
................
''', ML)


def volt_banner():
    img = SG('''
................
................
..OOOOOOOOOOOO..
..OYyYyYyYyYyO..
..OUUUUUUUUUuO..
..OUUUUUYYUUuO..
..OUUUUUYUUUuO..
..OUUUUYYUUUuO..
..OUUUUYUUUUuO..
..OUUUYYYYYUuO..
..OUUUUUUYUUuO..
..OUUUUUYYUUuO..
..OUUUUUYUUUuO..
..OUUUUYYUUUuO..
..OUUUUYUUUUuO..
..OUUUUUUUUUuO..
..OUUUUUUUUUuO..
..OuUUUUUUUuuO..
..OOuUUUUUuuOO..
...OOuUUUuuOO...
....OOuUuuOO....
.....OOuuOO.....
......OOOO......
................
................
................
................
................
................
................
................
................
''', GL)
    return img


# ===========================================================================
# catalog
# ===========================================================================

EAST_DECOR = [
    # --- LUMEN CITY ---------------------------------------------------------
    Decor('CITY_LAMP', C, city_lamp(), top='X/.',
          doc='Lumen street lamp: patina post, glass globe of stored charge; globe over people',
          examine="A LUMEN street lamp. There's no flame inside, just a hum and a steady blue glow."),
    Decor('TESLA_COIL', C, frames=tesla_coil_frames(), period=8, top='X/.',
          doc='tesla coil on a stone plinth, arcs crackle (2 frames); top over people',
          examine='A TESLA COIL. It crackles softly. The hair on your arms stands up.'),
    Decor('PARKED_BIKE', C, parked_bike(), doc='a bicycle leaning on its stand',
          examine="Someone's BIKE. It's chained to nothing at all. Lumen is that kind of city."),
    Decor('CAFE_TABLE', C, cafe_table(), top='X/.',
          doc='cafe table under a red and white parasol; parasol over people',
          examine='A cafe table. Someone left half a cup of copper-leaf tea.'),
    Decor('RAILING', C, railing(), doc='iron canal railing, tiles horizontally'),
    Decor('BEACON', C, frames=beacon_frames(), period=6, top='XX/XX/..',
          doc='the LUMEN BEACON: copper lattice tower with a globe of lightning (2x3)',
          examine='The LUMEN BEACON. Its glass globe holds a storm that has never gone out.'),
    # --- COPPERLINE ROAD ----------------------------------------------------
    Decor('MINE_MOUTH', W, mine_mouth(), doc='timbered adit into the old copper mine, boarded shut (3x2)',
          examine='The old COPPERLINE shaft. Boarded shut since the vein ran dry.'),
    Decor('RAILS_H', W, rails_h(), solid='.', doc='mine-cart rails, left-right (walkable decal)'),
    Decor('RAILS_V', W, rails_v(), solid='.', doc='mine-cart rails, up-down (walkable decal)'),
    Decor('ORE_CART', W, ore_cart(), doc='a mine cart heaped with copper ore',
          examine='A cart of copper ore, green with patina. Nobody has pushed it in years.'),
    Decor('ORE_PILE', W, ore_pile(), doc='heap of ore and slag with copper glints',
          examine='Slag and ore. Something small and magnetic has been nibbling at it.'),
    Decor('COPPER_ROCK', W, copper_rock(), doc='rock with a vein of native copper'),
    Decor('HEADFRAME', W, headframe(), top='XX/XX/..',
          doc='timber winding headframe with a sheave wheel (2x3); upper rows over people',
          examine='A winding headframe. The cable still hangs down into the dark.'),
    # --- ELDERWOOD HEART ----------------------------------------------------
    Decor('ELDER_TREE', W, elder_tree(), top='XXX/XXX/...',
          doc='the Elder: a vast ancient oak (3x3); crown over people, trunk solid',
          examine='The ELDER. Its roots drink from springs no one has ever found.'),
    Decor('FERN', W, fern(), solid='.', doc='fern fronds (walkable decal)'),
    Decor('GLOWCAPS', W, frames=glowcap_frames(), period=24, doc='glowing pink mushrooms (pulse)',
          examine='GLOWCAPS. Their light is a cold pink, bright enough to read by.'),
    Decor('STAG_ALTAR', W, stag_altar(), top='XX/..',
          doc='mossy stone altar carved with antlers (2x2); antler crown over people',
          examine='An old altar. Someone keeps leaving fresh flowers on it.'),
    # --- INTERIORS -----------------------------------------------------------
    Decor('PYLON', I, frames=pylon_frames(), period=12,
          doc='Volt Hall pylon: steel post with a glass insulator (solid; walls the maze)'),
    Decor('RESONANCE_COIL', I, resonance_coil(), top='X/.',
          doc='brass resonance coil on a steel base (1x2); top over people',
          examine='A resonance coil. It sings one clear note when you walk past.'),
    Decor('ENERGY_VAT', I, frames=energy_vat_frames(), period=16, top='X/.',
          doc='glass vat of glowing energy, bubbles rise (1x2)',
          examine='A vat of raw energy, green as spring leaves. Do not tap the glass.'),
    Decor('DYNAMO', I, dynamo(), doc='a brass-wound dynamo with a flywheel (2x1)',
          examine='A DYNAMO. Turn the wheel and it pays you back in light.'),
    Decor('BIKE_DISPLAY', I, bike_display(), doc='two bikes on a display stand (2x1)',
          examine='Shiny new BIKES. The price tags have a lot of zeros.'),
    Decor('GEARS', I, gears(), doc='brass clockwork gears on the wall (2x2)',
          examine='The Spire\'s gears. They turn so slowly you only notice if you wait.'),
    Decor('FILE_CABINET', I, file_cabinet(), top='X/.', doc='steel filing cabinet (1x2)',
          examine='Deeds, surveys and boundary maps, all filed in perfect order.'),
    Decor('VOLT_BANNER', I, volt_banner(), doc='Volt Hall banner, gold bolt on blue (hang on WALL_TOP)'),
]

# The Elder's crown is so dense that its middle cells are solid leaf: that is
# foliage, not baked ground (its outer cells are drawn on transparency).
for _d in EAST_DECOR:
    if _d.name == 'ELDER_TREE':
        _d.ground_ok = True
