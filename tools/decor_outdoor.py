#!/usr/bin/env python3
"""Outdoor decor catalog (village and routes): transparent objects placed
over any ground. See tools/gen_field_gfx.py for how they are encoded.

Palette plan (every 8x8 tile must fit one bank of each tileset it is used in):

  town+wild bank 3  TOWN_DECOR_BANK  outline, stone, crafted wood, fire, water,
                                     two leaf greens  (most props)
  wild bank 4       WILD_DECOR_BANK  ancient slate, storm glow, heartglass,
                                     mushroom reds, leaves (route nature)
  bank 0 (ground)   decals without outlines (fallen leaves, small flowers)
  bank 2 (trees)    foliage / bark with the dark-green tree outline t_out
                    (BUSH, BIG_TREE, HEDGE)
  roof banks        teal/blue exist in both tilesets (TENT, FLAG); red only in
                    the village (MARKET_STALL awning, MAILBOX)

Light comes from the top-left; objects have a 1px dark outline (b_out, or
t_out for foliage) and no ground shadow (no alpha on the GBA).
"""

import math
from pixelart import Img, G, shade_clumps, hash2, Decor

# ---------------------------------------------------------------------------
# palette banks
# ---------------------------------------------------------------------------

TOWN_DECOR_BANK = ['b_out', 'white', 'st_lt', 'st_mid', 'st_dk', 'wd_lt', 'wd_base', 'wd_dk',
                   'p_yel', 'fx_org', 'p_red', 'w_lt', 'w_base', 't_lt', 't_mid']

# Bank 4 of the route tileset: nature decor.
WILD_DECOR_BANK = ['b_out', 'white', 'f_red', 'f_redd', 't_lt', 't_base', 't_mid',
                   'sl_hi', 'sl_base', 'sl_dk', 'sg_hi', 'sg_base', 'hg_hi', 'hg_base', 'hg_dk']

# Extra colours used only by outdoor decor (name -> (r, g, b)).
OUTDOOR_COLORS = {
    'fx_org': (240, 144, 48),     # fire / amber glow / pumpkins
    'sl_hi': (168, 176, 204),     # ancient slate (standing stones, Stormstone)
    'sl_base': (116, 122, 158),
    'sl_dk': (72, 76, 110),
    'sg_hi': (200, 250, 255),     # storm glow (Stormstone runes)
    'sg_base': (80, 200, 248),
    'hg_hi': (255, 212, 240),     # heartglass crystal
    'hg_base': (232, 128, 200),
    'hg_dk': (150, 72, 168),
}

TREE_RAMP = ['t_hi', 't_lt', 't_base', 't_mid', 't_dk']

# ---------------------------------------------------------------------------
# legends
# ---------------------------------------------------------------------------

# bank 3 family (town + wild props)
OL = {'.': None, 'O': 'b_out', 'w': 'white', 'l': 'st_lt', 'm': 'st_mid', 'd': 'st_dk',
      'A': 'wd_lt', 'B': 'wd_base', 'K': 'wd_dk', 'y': 'p_yel', 'o': 'fx_org', 'r': 'p_red',
      'u': 'w_lt', 'U': 'w_base', 'g': 't_lt', 'G': 't_mid'}

# bank 4 family (wild nature)
WL = {'.': None, 'O': 'b_out', 'w': 'white', 'R': 'f_red', 'x': 'f_redd',
      'g': 't_lt', 'n': 't_base', 'G': 't_mid', 's': 'sl_hi', 'S': 'sl_base', 'D': 'sl_dk',
      'c': 'sg_hi', 'C': 'sg_base', 'p': 'hg_hi', 'P': 'hg_base', 'Q': 'hg_dk'}

# bank 2 family (trees, hedges)
TL = {'.': None, 'T': 't_out', '1': 't_hi', '2': 't_lt', '3': 't_base', '4': 't_mid',
      '5': 't_dk', 'a': 'k_lt', 'b': 'k_base', 'c': 'k_dk'}


def roof_legend(prefix):
    return {'.': None, 'O': 'b_out', '1': prefix + '_hi', '2': prefix + '_lt',
            '3': prefix + '_base', '4': prefix + '_dk', '5': prefix + '_dkr',
            'E': 'wl_hi', 'e': 'wl_base', 'f': 'wl_dk', 'h': 'st_hi', 'l': 'st_lt',
            'm': 'st_mid', 'z': 'gl_dk'}


TEAL = roof_legend('rt')      # teal roof bank: town 6, wild 5
RED = roof_legend('rf')       # red roof bank: town only


# ---------------------------------------------------------------------------
# helpers (also used by decor_indoor)
# ---------------------------------------------------------------------------

def SG(text, legend, w=16, h=None):
    """Strict grid: every row must be exactly w wide; pads on top to h rows."""
    rows = [r.strip() for r in text.strip('\n').split('\n')]
    rows = [r for r in rows if r]
    for i, r in enumerate(rows):
        if len(r) != w:
            raise ValueError('grid row %d is %d wide, expected %d: %r' % (i, len(r), w, r))
    img = G('\n'.join(rows), legend)
    if h is not None and h != img.h:
        if h < img.h:
            raise ValueError('grid has %d rows > %d' % (img.h, h))
        out = Img(w, h)
        out.paste(img, 0, h - img.h)
        return out
    return img


def outline(img, col='b_out', diag=False):
    """1px outline on the transparent pixels around the shape."""
    o = img.copy()
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if diag:
        nb += [(1, 1), (-1, 1), (1, -1), (-1, -1)]
    for y in range(img.h):
        for x in range(img.w):
            if img.p[y][x] is not None:
                continue
            for dx, dy in nb:
                if img.get(x + dx, y + dy) is not None:
                    o.p[y][x] = col
                    break
    return o


def in_ell(x, y, cx, cy, rx, ry):
    return ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0


def ell_d(x, y, cx, cy, rx, ry):
    return math.sqrt(((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2)


def flames(w, h, tongues, t, levels=(0.84, 0.56, 0.28),
           cols=('white', 'p_yel', 'fx_org', 'p_red')):
    """Procedural flame tongues. tongues: (cx, base_y, height, half_width,
    phase). t: animation phase in radians. Returns an Img (None = empty)."""
    img = Img(w, h)
    for y in range(h):
        for x in range(w):
            heat = 0.0
            for (cx, base, height, width, ph) in tongues:
                hh = height * (1.0 + 0.18 * math.sin(t * 2.2 + ph * 1.7))
                v = (base - (y + 0.5)) / hh
                if v < 0 or v > 1:
                    continue
                sway = 1.1 * math.sin(v * 3.2 - t * 2.3 + ph) * v
                hw = width * ((1 - v) ** 0.75) * min(1.0, 0.45 + v * 3.0)
                d = abs(x + 0.5 - (cx + sway)) / max(hw, 0.05)
                if d < 1:
                    heat = max(heat, (1 - d) ** 0.8 * (1.0 - 0.55 * v) + 0.15 * (1 - v))
            if heat <= 0:
                continue
            if heat > levels[0]:
                c = cols[0]
            elif heat > levels[1]:
                c = cols[1]
            elif heat > levels[2]:
                c = cols[2]
            else:
                c = cols[3]
            img.p[y][x] = c
    return img


def blob(w, h, clumps, ramp, line='b_out', seed=0, dither=False, clip=None, shadow_edge=True):
    img, _ = shade_clumps(w, h, clumps, ramp, line, shadow_edge=shadow_edge, seed=seed,
                          dither=dither, clip=clip)
    return img


# ---------------------------------------------------------------------------
# village props (bank 3)
# ---------------------------------------------------------------------------

SIGN = SG('''
................
................
.OOOOOOOOOOOOOO.
OAAAAAAAAAAAAAAO
OBBBBBBBBBBBBBBO
OBAAAAAAAAAAAAKO
OBAKKKKAKKKKAAKO
OBAAAAAAAAAAAAKO
OBAKKKAKKKKKAAKO
OBAAAAAAAAAAAAKO
OKKKKKKKKKKKKKKO
.OOOOOOABOOOOOO.
......OABKO.....
......OABKO.....
......OABKO.....
......OOOOO.....
''', OL)

MAILBOX = SG('''
................
................
.....OOOOOO.....
....O122223O.OO.
...O12222334OEO.
...O22223334OEO.
...O22223334OeO.
...OO2OOOO34OOO.
...O2OhhhO344O..
...O2OlmmO344O..
...O33OOO3344O..
...OOOOOOOOOOO..
.......OlmO.....
.......OlmO.....
.......OlmO.....
.......OOOO.....
''', RED)

FENCE = SG('''
................
................
................
.OOOO...........
.OABO...........
OOABOOOOOOOOOOOO
AOABOAAAAAAAAAAA
BOABOBBBBBBBBBBB
OOABOOOOOOOOOOOO
.OABO...........
OOABOOOOOOOOOOOO
AOABOAAAAAAAAAAA
KOABOKKKKKKKKKKK
OOABOOOOOOOOOOOO
.OABO...........
.OOOO...........
''', OL)

FENCE_POST = SG('''
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
''', OL)

GATE = SG('''
................
................
................
.OOOO.O..O..O...
.OABOOAOOAOOAO..
OOABOOAOOAOOAOOO
AOABOAAAAAAAAAAA
BOABOBBKBBBBBBBB
OOABOOAOKAOOAOOO
.OABOOAOOKOOAO..
OOABOOAOOAKOAOOO
AOABOAAAAAAKAAAd
KOABOKKKKKKKKKKd
OOABOOAOOAOOAOOO
.OABOOBOOBOOBO..
.OOOOOOOOOOOOO..
''', OL)

LAMP = SG('''
................
................
......OOOO......
....OOddddOO....
...OdmmmmmmdO...
...OOOOOOOOOO...
....OwwyyyKO....
....OwyyyyKO....
....OyyyyyKO....
....OyyyyAKO....
....OOOOOOOO....
.....OdmmdO.....
......OmdO......
......OmdO......
......OmdO......
......OmdO......
......OmdO......
......OmdO......
......OmdO......
......OmdO......
......OmdO......
......OmdO......
......OmdO......
......OmdO......
......OmdO......
.....OOmdOO.....
....OmmmmddO....
....OdddddOO....
.....OOOOOO.....
................
................
................
''', OL)

ROCK = SG('''
................
................
................
.....OOOOOO.....
...OOwwwlllOO...
..OwwwlllllmmO..
..OwlllllllmmO..
.OwlllllllmmmmO.
.OwllllllmmmmdO.
.OlllllmmdmmmdOO
.OlllmmmdmmmddO.
.OlmmmmmmmmdddO.
..OmmmmmmmdddO..
...OOOOOOOOOO...
................
................
''', OL)


def _bush():
    clumps = [(8.0, 6.5, 5.5, 4.5), (4.8, 9.5, 3.8, 3.6), (11.2, 9.5, 3.8, 3.6),
              (8.0, 10.5, 4.6, 3.4)]
    return blob(16, 16, clumps, TREE_RAMP, 't_out', seed=7, dither=True,
                clip=lambda x, y: 1 <= x <= 14 and y <= 13)


BENCH = SG('''
................................
..OOOOOOOOOOOOOOOOOOOOOOOOOOOO..
..OAAAAAAAAAAAAAAAAAAAAAAAAAAO..
..OBBBBBBKBBBBBBBBBBKBBBBBBBKO..
..OOOOOOOOOOOOOOOOOOOOOOOOOOOO..
..OAAAAAAAAAAAAAAAAAAAAAAAAAAO..
..OBBBBBBBBBBBBKBBBBBBBBBKBBKO..
..OOOOOOOOOOOOOOOOOOOOOOOOOOOO..
....OdO..................OdO....
.OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
.OwAAAAAAAAAAAAAAAAAAAAAAAAAAAO.
.OBBBBBBKBBBBBBBBBBBKBBBBBBBBKO.
.OKKKKKKKKKKKKKKKKKKKKKKKKKKKKO.
.OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
..OmdO....................OmdO..
..OOOO....................OOOO..
''', OL, w=32)

BARREL = SG('''
................
....OOOOOOOO....
..OOBBBBBBBBOO..
.OBAAAAAAAAAABO.
.OBAAKAAAAKAABO.
.OKBAKAAAAKABKO.
.OOKKKKKKKKKKOO.
.OwlllllllmmdO..
OABBBKBBBBKBBKKO
OABBBKBBBBKBBKKO
OABBBKBBBBKBBKKO
OlllllllmmmmdddO
.OABBKBBBBKBBKO.
.OABBKBBBBKBKKO.
..OOOOOOOOOOOO..
................
''', OL)

CRATE = SG('''
................
................
.OOOOOOOOOOOOOO.
.OwAAAAAAAAAAAO.
.OABBBBBBBBBBKO.
.OAAAAAAAAAAAAO.
.OKKKKKKKKKKKKO.
.OOOOOOOOOOOOOO.
.OAAAAAAAAAAAKO.
.OABKBBBBBBKBKO.
.OABBKBBBBKBBKO.
.OABBBKKKKBBBKO.
.OABBKBBBBKBBKO.
.OAKKKKKKKKKKKO.
.OOOOOOOOOOOOOO.
................
''', OL)


def crate_stack():
    img = Img(16, 32)
    img.paste(CRATE.crop(0, 2, 16, 13), 0, 19)
    small = SG('''
    OOOOOOOOOOOO
    OwAAAAAAAAAO
    OABBBBBBBBKO
    OKKKKKKKKKKO
    OOOOOOOOOOOO
    OAAAAAAAAAKO
    OABKBBBBKBKO
    OABBKKKKBBKO
    OABKBBBBKBKO
    OAKKKKKKKKKO
    OOOOOOOOOOOO
    ''', OL, w=12)
    img.paste(small, 3, 9)
    return img


def sack_layer(spans, ramp, neck_x, neck_y, tie='wd_dk', speck=None, seed=0):
    """Sack body from row spans {y: (x0, x1)}, lit from the top-left, plus a
    gathered neck with a tie. Returns an outlined layer."""
    img = Img(16, 16)
    ys = sorted(spans)
    for y in ys:
        x0, x1 = spans[y]
        for x in range(x0, x1 + 1):
            t = (x - x0) / max(1, x1 - x0)
            c = ramp[1]
            if t < 0.3 or y == ys[0]:
                c = ramp[0]
            elif t > 0.72 or y == ys[-1]:
                c = ramp[2]
            if speck and c == ramp[1] and (hash2(x, y, seed) & 7) == 0:
                c = speck
            img.set(x, y, c)
    neck = G('''
    ABB
    .K.
    ''', {'.': None, 'A': ramp[0], 'B': ramp[1], 'K': tie})
    img.paste(neck, neck_x, neck_y)
    return outline(img)


def sacks():
    burlap = sack_layer({5: (3, 6), 6: (2, 7), 7: (1, 8), 8: (1, 9), 9: (1, 9), 10: (1, 9),
                         11: (1, 9), 12: (1, 9), 13: (2, 8)},
                        ['wd_lt', 'wd_base', 'wd_dk'], 3, 3, speck='wd_lt', seed=3)
    flour = sack_layer({8: (9, 12), 9: (8, 13), 10: (7, 14), 11: (7, 14), 12: (7, 14),
                        13: (7, 14), 14: (8, 13)},
                       ['white', 'st_lt', 'st_mid'], 9, 6, tie='wd_base')
    img = Img(16, 16)
    img.paste(burlap, 0, 0)
    img.paste(flour, 0, 0)
    for (x, y, c) in ((10, 11, 'p_red'), (11, 11, 'p_red'), (10, 12, 'p_red'), (11, 12, 'wd_dk')):
        img.set(x, y, c)
    return img


POT = SG('''
..OOOOOOOOOOOO..
..OooooooooooO..
..OKBBBBBBBBKO..
...OoBBBBBBKO...
...OoBBBBBBKO...
....OoBBBBKO....
....OOOOOOOO....
''', OL)


def leafy(w, h, clumps, seed=1):
    return blob(w, h, clumps, ['t_lt', 't_lt', 't_mid', 't_mid'], 'b_out', seed=seed, dither=True)


def blossom(img, x, y, petal, centre='p_yel'):
    for (dx, dy) in ((0, -1), (-1, 0), (1, 0), (0, 1)):
        img.set(x + dx, y + dy, petal)
    img.set(x, y, centre)


def flower_pot():
    img = Img(16, 16)
    img.paste(leafy(16, 16, [(8, 5.5, 5.4, 4.2), (5, 7.5, 3.2, 2.6), (11, 7.5, 3.2, 2.6)], seed=4), 0, 0)
    blossom(img, 6, 4, 'p_red')
    blossom(img, 10, 3, 'p_red')
    blossom(img, 9, 7, 'white')
    blossom(img, 4, 7, 'white')
    img.paste(POT, 0, 9)
    return img


def planter():
    img = Img(32, 16)
    img.paste(leafy(32, 16, [(6, 6, 5, 3.6), (16, 5.5, 6, 4), (26, 6, 5, 3.6),
                             (11, 7.5, 4, 2.5), (21, 7.5, 4, 2.5)], seed=9), 0, 0)
    cols = ['p_red', 'p_yel', 'white', 'p_red', 'white', 'p_yel', 'p_red']
    for i, (x, y) in enumerate(((4, 5), (8, 3), (12, 6), (16, 3), (20, 6), (24, 3), (28, 5))):
        blossom(img, x, y, cols[i], 'fx_org' if cols[i] == 'p_yel' else 'p_yel')
    box = SG('''
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    .OwAAAAAAAAAAAAAAAAAAAAAAAAAAAO.
    .OKKKKKKKKKKKKKKKKKKKKKKKKKKKKO.
    .OABBBBBBBOABBBBBBBOABBBBBBBBKO.
    .OABBBKBBBOABBBBBKBOABBBKBBBBKO.
    .OABBBBBBBOABBBBBBBOABBBBBBBBKO.
    .OKKKKKKKKOKKKKKKKKOKKKKKKKKKKO.
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    ''', OL, w=32)
    img.paste(box, 0, 8)
    return img


HAY_BALE = SG('''
................
................
..OOOOOOOOOOOO..
.OyyyKyyyyyKyyO.
.OywyKyAyyyKyAO.
.OAyyKyyyAyKAAO.
.OAAAKAAAAAKAAO.
.OOOOKOOOOOKOOO.
.OABAKABAABKBKO.
.OAABKBAABAKBKO.
.OABAKAABABKBKO.
.OAABKBABAAKBKO.
.OBABKABBABKBKO.
.OBBBKBBBBBKKKO.
..OOOOOOOOOOOO..
................
''', OL)


def ring_well(img, cx, cy, rx, ry, irx, iry, wall, rim_cols, wall_cols, joint='st_mid',
              hole=None, seed=0):
    """Round stone ring seen from above at an angle (rim + front wall).
    hole(x, y) paints the inside. Returns the shape mask."""
    def front(x):
        dx = (x + 0.5 - cx) / rx
        if abs(dx) >= 1:
            return None
        return cy + ry * math.sqrt(1 - dx * dx)
    for y in range(img.h):
        for x in range(img.w):
            if in_ell(x, y, cx, cy, rx, ry):
                if in_ell(x, y, cx, cy - 0.4, irx, iry):
                    if hole:
                        hole(x, y)
                    continue
                # rim stones: radial joints
                ang = math.atan2((y + 0.5 - cy) / ry, (x + 0.5 - cx) / rx)
                k = int((ang + math.pi) / (2 * math.pi) * 14)
                frac = ((ang + math.pi) / (2 * math.pi) * 14) % 1.0
                c = rim_cols[0] if (y + 0.5 - cy) < 0 else rim_cols[1]
                if (x + 0.5 - cx) > rx * 0.55:
                    c = rim_cols[1] if (y + 0.5 - cy) < 0 else rim_cols[2]
                if frac < 0.12:
                    c = joint
                img.set(x, y, c)
            else:
                fy = front(x)
                if fy is not None and cy <= y + 0.5 <= fy + wall:
                    t = (x + 0.5 - (cx - rx)) / (2 * rx)
                    course = int((y + 0.5 - fy) // 3 + 10)
                    yy = (y + 0.5 - fy) % 3
                    off = (course % 2) * 3
                    if yy < 1.0 and y + 0.5 > fy:
                        c = wall_cols[3]
                    elif (x + off) % 6 == 0:
                        c = wall_cols[3]
                    else:
                        base = 0 if t < 0.28 else 1 if t < 0.72 else 2
                        if (hash2(x // 6, course, seed) & 3) == 0:
                            base = min(2, base + 1)
                        c = wall_cols[base]
                    img.set(x, y, c)
    return img


def well():
    img = Img(32, 32)

    def hole(x, y):
        c = 'b_out'
        if y <= 18:
            c = 'st_dk'
        if (x, y) in ((13, 20), (14, 20), (19, 21)):
            c = 'w_base'
        img.set(x, y, c)
    ring_well(img, 16.0, 21.0, 14.0, 4.6, 10.0, 2.8, 7,
              ['white', 'st_lt', 'st_mid'], ['st_lt', 'st_mid', 'st_dk', 'st_dk'], seed=2,
              hole=hole)
    img = outline(img)
    top = SG('''
    ................................
    ......OOOOOOOOOOOOOOOOOOOO......
    .....OAAAAAAAAAAAAAAAAAAAAO.....
    ....OBKBBKBBKBBKBBKBBKBBKBBO....
    ...OAAAAAAAAAAAAAAAAAAAAAAAAO...
    ..OBBKBBKBBKBBKBBKBBKBBKBBKBBO..
    .OAAAAAAAAAAAAAAAAAAAAAAAAAAAAO.
    OBBKBBKBBKBBKBBKBBKBBKBBKBBKBBKO
    OKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKO
    OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
    ...OABO..................OABO...
    ...OABOOOOOOOOOOOOOOOOOOOOABOOO.
    ...OABOKKKKKKKKKKKKKKKKKKOABOdO.
    ...OABOOOOOOOOdOOOOOOOOOOOABOdO.
    ...OABO.......dO.........OABOOO.
    ...OABO.......dO.........OABO...
    ...OABO.....OOOOOO.......OABO...
    ...OABO.....OABBKO.......OABO...
    ...OABO.....OlmmdO.......OABO...
    ...OABO.....OABBKO.......OABO...
    ...OABO.....OOOOOO.......OABO...
    ...OABO..................OABO...
    ...OOOO..................OOOO...
    ''', OL, w=32)
    img.paste(top, 0, 0)
    return img


def trough():
    return SG('''
    ................................
    ................................
    ................................
    ..OOOOOOOOOOOOOOOOOOOOOOOOOOOO..
    .OAAAAAAAAAAAAAAAAAAAAAAAAAAAAO.
    .OAOOOOOOOOOOOOOOOOOOOOOOOOOOBO.
    .OAOUUUUUUUUUUUUUUUUUUUUUUUUOBO.
    .OAOuuwuuuuuuuuuwwuuuuuuuuuuOBO.
    .OAOuuuuuuuuuuuuuuuuuuuuuwuuOBO.
    .OBOOOOOOOOOOOOOOOOOOOOOOOOOOKO.
    .OKKKKKKKKKKKKKKKKKKKKKKKKKKKKO.
    .OABBBBBBBBBBBBBBBBBBBBBBBBBBKO.
    .OABBBBBBKBBBBBBBBBBBKBBBBBBBKO.
    .OKKKKKKKKKKKKKKKKKKKKKKKKKKKKO.
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    ..OKKO....................OKKO..
    ''', OL, w=32)


def fruit_pile(img, x0, y0, n_bottom, base, hi, dk, r=1.6):
    """A mound of round fruit (n_bottom in the lower row, one fewer above),
    each ~3px, outlined as one pile. x0,y0 = lower-left fruit centre."""
    pile = Img(img.w, img.h)
    centres = [(x0 + i * 3, y0) for i in range(n_bottom)]
    centres += [(x0 + 1.5 + i * 3, y0 - 2.5) for i in range(n_bottom - 1)]
    for (cx, cy) in centres:
        for y in range(int(cy - 2), int(cy + 3)):
            for x in range(int(cx - 2), int(cx + 3)):
                d = math.hypot(x + 0.5 - (cx + 0.5), y + 0.5 - (cy + 0.5))
                if d <= r:
                    c = base
                    if x + 0.5 - (cx + 0.5) < -0.4 and y + 0.5 - (cy + 0.5) < -0.4:
                        c = hi
                    elif x + 0.5 - (cx + 0.5) > 0.4 and y + 0.5 - (cy + 0.5) > 0.4:
                        c = dk
                    pile.set(x, y, c)
    pile = outline(pile)
    img.paste(pile, 0, 0)
    return img


def market_stall():
    img = Img(48, 32)
    # awning (red roof bank): stripes 6px, slanted top, scalloped valance
    for y in range(1, 15):
        for x in range(1, 47):
            stripe = (x - 1) // 6
            red = stripe % 2 == 0
            xs = (x - 1) % 6
            if y <= 9:
                if y <= 3:
                    c = 'rf_hi' if red else 'wl_hi'
                elif y <= 7:
                    c = 'rf_lt' if red else 'wl_hi'
                else:
                    c = 'rf_base' if red else 'wl_base'
                if xs == 5 and y > 2:
                    c = 'rf_dk' if red else 'wl_dk'
            else:
                yy = y - 10
                if yy == 4 and xs in (0, 5):
                    continue
                if yy == 4:
                    c = 'b_out'
                elif yy == 3 and xs in (0, 5):
                    c = 'b_out'
                else:
                    c = ('rf_base' if yy < 2 else 'rf_dk') if red else ('wl_base' if yy < 2 else 'wl_dk')
                    if yy == 0:
                        c = 'rf_dkr' if red else 'wl_dk'
            img.set(x, y, c)
    for x in range(1, 47):
        img.set(x, 0, 'b_out')
    for y in range(0, 14):
        img.set(0, y, 'b_out')
        img.set(47, y, 'b_out')
    # stall body (bank 3): poles, counter with goods, front panel
    body = SG('''
    ..OOOOO..................................OOOOO..
    ..OABKO..................................OABKO..
    ..OABKO..................................OABKO..
    ..OABKO..................................OABKO..
    ..OABKO..................................OABKO..
    OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
    OwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAO
    OKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKO
    OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
    .OABBBKOABBBBBBKOABBBBBBKOABBBBBBKOABBBBBBKOABO.
    .OABBBKOABBBBBBKOABBBBBBKOABBBBBBKOABBBBBBKOABO.
    .OABBBKOABBBBBBKOABBBBBBKOABBBBBBKOABBBBBBKOABO.
    .OKKKKKOKKKKKKKKOKKKKKKKKOKKKKKKKKOKKKKKKKKOKKO.
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    ..OKKO..................................OKKO....
    ..OOOO..................................OOOO....
    ''', OL, w=48)
    img.paste(body, 0, 16)
    goods = Img(48, 32)
    fruit_pile(goods, 7, 21, 3, 'p_red', 'white', 'wd_dk')
    fruit_pile(goods, 17, 21, 3, 'fx_org', 'p_yel', 'wd_base')
    fruit_pile(goods, 27, 21, 3, 't_lt', 'white', 't_mid')
    fruit_pile(goods, 37, 21, 3, 'p_yel', 'white', 'fx_org')
    img.paste(goods, 0, 0)
    return img


# ---------------------------------------------------------------------------
# lights, fire and the Old Hearth
# ---------------------------------------------------------------------------

HEARTH_BASE = '''
.....OwlllllllllllllllmmmdO.....
.....OwlyllollyllollylmomdO.....
......OlmmmmmmmmmmmmmmmmdO......
.......OwllllllllllmmmddO.......
.........OlllllllmmmddO.........
.........OOOwllllmmdOOO.........
...........OwlllmmddO...........
.........OwwllllllmmmdO.........
.........OmmmmmmmmmdddO.........
...OOOOOOOOOOOOOOOOOOOOOOOOOO...
...OwwwwwwwlllllllllllllllmmO...
...OwllllllllllllllllllllmmdO...
...OlllllmmmmmmmmmmmmmmmmdddO...
...OlmmmmmmmmmmoommmmmmmmdddO...
...OlmmmmmmmmmmmmmmmmmmmmdddO...
.OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
.OwwwwwwwwwlllllllllllllllllmmO.
.OlmmmmdmmmmmmdmmmmmmdmmmmmmddO.
.OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
'''


def hearth_frames():
    base = SG(HEARTH_BASE, OL, w=32, h=32)
    cx, cy, rx, ry = 16.0, 11.5, 11.5, 3.2
    back, front, coals = Img(32, 32), Img(32, 32), Img(32, 32)
    for y in range(6, 16):
        for x in range(32):
            if not in_ell(x, y, cx, cy, rx, ry):
                continue
            if in_ell(x, y, cx, cy - 0.3, rx - 2.2, ry - 1.2):
                h = hash2(x, y, 5) & 7
                coals.set(x, y, 'p_red' if h < 3 else 'fx_org' if h < 5 else
                          'p_yel' if h < 6 else 'wd_dk')
            elif y + 0.5 < cy:
                back.set(x, y, 'st_mid' if x > 21 else 'st_lt')
            else:
                front.set(x, y, 'white' if x < 11 else 'st_lt' if x < 23 else 'st_mid')
    stone = Img(32, 32)
    stone.paste(base, 0, 0)
    stone.paste(back, 0, 0)
    stone.paste(front, 0, 0)
    shell = outline(stone)
    tongues = [(16, 11.8, 15.5, 4.2, 0.0), (12.3, 11.8, 10.5, 2.8, 2.1),
               (19.7, 11.8, 11.0, 2.8, 4.2), (9.0, 11.8, 5.5, 2.0, 1.3), (23.0, 11.8, 6.0, 2.0, 3.3)]
    frames = []
    for f in range(4):
        img = shell.copy()
        img.paste(coals, 0, 0)
        fl = flames(32, 32, tongues, f * math.pi / 2)
        for y in range(32):
            for x in range(32):
                c = fl.p[y][x]
                if not c:
                    continue
                cur = img.p[y][x]
                if cur is None or back.p[y][x] or (cur == 'b_out' and y < 10) or \
                        (coals.p[y][x] and y + 0.5 < cy):
                    img.p[y][x] = c
        img.paste(front, 0, 0)
        frames.append(img)
    return frames


def lantern_post_frames():
    base = SG('''
    ................
    ................
    ..OOOOOOOOOOO...
    ..OddddddddddO..
    ..OOOOOOOOOdOO..
    ..OABO....OdO...
    ..OABO...OOOOO..
    ..OABO..OdmmmdO.
    ..OABO..OOOOOOO.
    ..OABO..OdYYYdO.
    ..OABO..OdYYYdO.
    ..OABO..OdYYYdO.
    ..OABO..OdYYYdO.
    ..OABO..OOOOOOO.
    ..OABO...OdmdO..
    ..OABO....OOO...
    ..OABO..........
    ..OABO..........
    ..OABO..........
    ..OABO..........
    ..OABO..........
    ..OABO..........
    ..OABO..........
    ..OABO..........
    ..OABO..........
    ..OABO..........
    ..OABO..........
    .OOABOO.........
    OABBBBKO........
    OBKKKKKO........
    OOOOOOOO........
    ................
    ''', dict(OL, Y='p_yel'))
    glows = [
        ['wyy', 'wyy', 'yyo', 'yoo'],
        ['ywy', 'wwy', 'yyo', 'ooo'],
        ['yyy', 'ywy', 'wyo', 'yoo'],
    ]
    cmap = {'w': 'white', 'y': 'p_yel', 'o': 'fx_org'}
    frames = []
    for g in glows:
        img = base.copy()
        for yy, row in enumerate(g):
            for xx, ch in enumerate(row):
                img.set(10 + xx, 9 + yy, cmap[ch])
        frames.append(img)
    return frames


STONE_LANTERN = '''
................
.......OO.......
......OwlO......
.....OOllOO.....
..OOOwwlllmOOO..
.OwwwlllllmmmdO.
OOOOOOOOOOOOOOOO
..OlOOOOOOOOdO..
..OlOYYYYYYOdO..
..OlOYWWYYoOdO..
..OlOYYYYooOdO..
..OlOOOOOOOOdO..
.OOOOOOOOOOOOOO.
.OwwlllllllmmdO.
.OOOOOOOOOOOOOO.
....OwllmmdO....
.....OlmmdO.....
.....OlmmdO.....
.....OlmmdO.....
.....OlmmdO.....
.....OlmmdO.....
.....OlmmdO.....
.....OlmmdO.....
....OOOOOOOO....
...OwllllmmdO...
..OOOOOOOOOOOO..
..OwwllllllmdO..
..OlllllmmmmdO..
..OmmmmmmmdddO..
..OOOOOOOOOOOO..
................
................
'''


def stone_lantern_frames():
    frames = []
    for glow in (('p_yel', 'white', 'fx_org'), ('p_yel', 'p_yel', 'fx_org')):
        leg = dict(OL, Y=glow[0], W=glow[1])
        leg['o'] = glow[2]
        frames.append(SG(STONE_LANTERN, leg))
    return frames


def campfire_frames():
    base = Img(16, 16)
    logs = SG('''
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ..OOO......OOO..
    .OAyKOO..OOKyAO.
    ..OOBBKOOKBBOO..
    ....OOBKKBOO....
    ...OOKBOOBKOO...
    ..OAKOO..OOKAO..
    ...OO......OO...
    ''', OL)
    stones = Img(16, 16)
    for (x, y) in ((1, 13), (4, 14), (8, 15), (12, 14), (14, 12), (0, 11)):
        pass
    frames = []
    tongues = [(8, 13, 11, 3.4, 0.0), (5.5, 13, 7, 2.2, 2.0), (10.5, 13, 7.5, 2.2, 4.0)]
    ring = SG('''
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
    .OO..........OO.
    OwlO........OlmO
    OlmdOO....OOlmdO
    .OOOwlOOOOwlOOO.
    ....OOOmmOOO....
    ''', OL)
    for f in range(4):
        img = Img(16, 16)
        img.paste(ring, 0, 0)
        img.paste(logs, 0, 0)
        fl = flames(16, 16, tongues, f * math.pi / 2)
        for y in range(16):
            for x in range(16):
                if fl.p[y][x] and (y < 11 or img.p[y][x] in (None, 'b_out') and y < 13):
                    img.p[y][x] = fl.p[y][x]
        frames.append(img)
    return frames


def flag_frames():
    frames = []
    for f in range(3):
        img = Img(16, 32)
        # pole + finial + stone foot
        for y in range(3, 29):
            img.set(2, y, 'st_hi')
            img.set(3, y, 'st_mid')
        for y in range(2, 30):
            img.set(1, y, 'b_out')
            img.set(4, y, 'b_out') if img.get(4, y) is None else None
        img.set(2, 0, 'b_out'); img.set(3, 0, 'b_out')
        img.set(1, 1, 'b_out'); img.set(2, 1, 'wl_hi'); img.set(3, 1, 'wl_base'); img.set(4, 1, 'b_out')
        img.set(2, 2, 'wl_base'); img.set(3, 2, 'wl_dk')
        foot = SG('''
        .OOOOOO.
        OhhllmO.
        OlllmmO.
        OOOOOOO.
        ''', TEAL, w=8)
        img.paste(foot, 0, 28)
        # cloth
        cloth = Img(16, 32)
        for x in range(4, 16):
            u = (x - 4) / 11.0
            ph = u * 5.0 - f * 2.1
            dy = int(round(1.2 * math.sin(ph) * u))
            slope = math.cos(ph)
            y0, y1 = 3 + dy, 12 + dy - (1 if x >= 13 else 0)
            for y in range(y0, y1 + 1):
                if x == 15 and (y - y0) % 3 == 1:
                    continue
                c = 'rt_base'
                if slope > 0.45:
                    c = 'rt_lt'
                elif slope < -0.45:
                    c = 'rt_dk'
                if y == y0:
                    c = 'rt_hi' if slope > -0.2 else 'rt_lt'
                if y == y1:
                    c = 'rt_dk' if slope > -0.2 else 'rt_dkr'
                cloth.set(x, y, c)
        # emblem: little cream flame
        em = G('''
        ..E.
        .EE.
        EEeE
        EeeE
        .EE.
        ''', {'.': None, 'E': 'wl_hi', 'e': 'wl_base'})
        emy = 5 + int(round(1.2 * math.sin(0.45 * 5.0 - f * 2.1) * 0.45))
        cloth.paste(em, 8, emy)
        cloth = outline(cloth)
        for y in range(32):
            for x in range(16):
                if cloth.p[y][x] and (img.p[y][x] is None or cloth.p[y][x] != 'b_out'):
                    if x >= 4:
                        img.p[y][x] = cloth.p[y][x]
        frames.append(img)
    return frames


def tent():
    img = Img(32, 32)
    ax, ay = 15.5, 2.0
    for y in range(3, 30):
        half = (y - ay) * 13.5 / 27.0
        for x in range(32):
            dx = x + 0.5 - ax
            if abs(dx) <= half:
                c = 'rt_base'
                if dx < -half + 2.2:
                    c = 'rt_lt'
                elif dx > half - 2.2:
                    c = 'rt_dk'
                if y >= 28:
                    c = 'rt_dk'
                # centre seam
                if abs(dx) < 0.6 and y < 10:
                    c = 'rt_dk'
                # door
                dh = (y - 10.0) * 6.2 / 18.0
                if y >= 10 and abs(dx) <= dh:
                    c = 'rt_dkr'
                    if abs(dx) > dh - 2.0 and y > 12:
                        c = 'wl_base' if dx < 0 else 'wl_dk'
                    if abs(dx) > dh - 1.0 and y > 12:
                        c = 'wl_hi' if dx < 0 else 'wl_base'
                    if y > 26 and abs(dx) < dh - 2:
                        c = 'b_out'
                img.set(x, y, c)
    # stitched highlight lines on the canvas
    for y in range(6, 28, 4):
        half = (y - ay) * 13.5 / 27.0
        for x in range(32):
            dx = x + 0.5 - ax
            if -half + 3 < dx < -3 and img.p[y][x] == 'rt_base' and (x + y) % 2 == 0:
                img.set(x, y, 'rt_lt')
    # ties on the rolled flaps
    img.set(10, 19, 'wl_dk'); img.set(21, 19, 'wl_dk')
    img = outline(img)
    # ridge pole tip and guy ropes with pegs
    img.set(15, 0, 'b_out'); img.set(16, 0, 'b_out')
    img.set(15, 1, 'st_lt'); img.set(16, 1, 'st_mid')
    for (x, y) in ((1, 29), (0, 30), (30, 29), (31, 30)):
        img.set(x, y, 'wl_dk')
    for (x, y) in ((0, 31), (31, 31)):
        img.set(x, y, 'b_out')
    return img


# ---------------------------------------------------------------------------
# wood, trees, stones
# ---------------------------------------------------------------------------

def log_end(img, cx, cy, r=2.8):
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= r:
                if d > r - 1.0:
                    c = 'wd_dk' if (x + 0.5 - cx) + (y + 0.5 - cy) > 0 else 'wd_base'
                elif d > r - 1.9:
                    c = 'wd_lt'
                elif d > 0.9:
                    c = 'p_yel'
                else:
                    c = 'wd_lt'
                img.set(x, y, c)


def woodpile():
    img = Img(32, 16)
    rows = [(12.5, [4.5, 10.5, 16.5, 22.5, 28.5]), (7.5, [7.5, 13.5, 19.5, 25.5]),
            (2.8, [10.5, 16.5, 22.5])]
    for (cy, xs) in rows:
        layer = Img(32, 16)
        for cx in xs:
            log_end(layer, cx, cy)
        img.paste(layer, 0, 0)
    img = outline(img)
    return img


def stump():
    img = SG('''
    ................
    ................
    ................
    ....OOOOOOO.....
    ..OOAyyyyyAOO...
    .OAyyAAAAAyyAO..
    .OAyAyyyyyAyBO..
    .OKAyAAAAAyBKO..
    .OgBAyyyyyBKKO..
    .OGgBBBBBBBKKO..
    .OBgGBKBBBKBKO..
    .OBBBBKBBBKBKO..
    OOABBKBBBBKBKOO.
    OAOBBKBBBBBKOKO.
    OOOOOOOOOOOOOOO.
    ................
    ''', OL)
    return img


def fallen_log():
    return SG('''
    ................................
    ................................
    ................................
    ...OOOOO..........OO............
    ..OAAAAAO.OOOOOOOOgGOOOOOOOOOO..
    .OAyyyyyAOgGgBBBBGgBBBBBBBBBBBO.
    .OAyAAAyAOGgBBBBBBBBBBBKBBBBBBO.
    OAyAyyyAyAOBBKBBBBBBBBBBBBBKBBBO
    OAyAyAyAyAOBBBBBBBBBKBBBBBBBBBBO
    OAyAyyyAyAOBBBBBKBBBBBBBBKBBBBBO
    .OAyAAAyAOKBBBBBBBBBBBBBBBBBBBKO
    .OAyyyyyAOKKKKBKKKKKKBKKKKKKKKKO
    ..OAAAAAOKKKKKKKKKKKKKKKKKKKKKO.
    ...OOOOOOOOOOOOOOOOOOOOOOOOOOO..
    ................................
    ................................
    ''', OL, w=32)


def big_tree():
    clumps = [
        (16.0, 7.5, 9.5, 7.0),
        (8.5, 11.0, 7.0, 6.0), (23.5, 11.0, 7.0, 6.0),
        (16.0, 13.5, 9.0, 6.5),
        (6.5, 17.0, 6.0, 4.6), (25.5, 17.0, 6.0, 4.6),
        (12.0, 19.0, 6.5, 4.4), (20.0, 19.0, 6.5, 4.4),
    ]
    can = blob(32, 32, clumps, TREE_RAMP, 't_out', seed=21, dither=True,
               clip=lambda x, y: y <= 23)
    img = Img(32, 32)
    trunk = SG('''
    .......TabbbbcT.......
    .......TabbbbcT.......
    .......TabbbbcT.......
    ......TTabbbbccT......
    .....TabbabbbbbcT.....
    ...TTabbbTabbTbbcTT...
    ..TabbTTTTTTTTTTTbbcT.
    ..TTTT..........TTTT..
    ''', TL, w=22)
    img.paste(trunk, 5, 24)
    img.paste(can, 0, 0)
    return img


def hedge():
    img = Img(16, 16)
    for y in range(2, 15):
        for x in range(16):
            h = hash2(x, y, 41) & 15
            if y <= 6:
                c = 't_hi' if h < 5 else 't_lt'
                if y == 6:
                    c = 't_lt' if h < 8 else 't_base'
            else:
                c = 't_base' if h < 9 else 't_mid'
                if y >= 12:
                    c = 't_mid' if h < 10 else 't_dk'
                if (x + (y // 3) * 3) % 6 == 0 and y < 12:
                    c = 't_lt'
            img.set(x, y, c)
    # bumpy top edge + outline
    for x in range(16):
        top = 2 if (x % 5) in (1, 2, 3) else 3
        for y in range(2, top):
            img.set(x, y, None)
        img.set(x, top - 1, 't_out')
        img.set(x, 15, 't_out')
        img.set(x, 14, 't_dk')
    return img


def hedge_end():
    img = hedge()
    # round off the right end: an elliptical cap
    for y in range(16):
        for x in range(8, 16):
            if not in_ell(x, y, 7.5, 8.6, 7.0, 6.6):
                img.set(x, y, None)
    for y in range(16):
        for x in range(8, 16):
            if img.p[y][x] in ('t_out',):
                img.set(x, y, None)
    for x in range(8, 16):
        for y in range(16):
            c = img.p[y][x]
            if c is None:
                continue
            if x >= 12 and c in ('t_hi', 't_lt', 't_base') and y > 6:
                img.set(x, y, 't_mid')
            elif x >= 13 and c == 't_hi':
                img.set(x, y, 't_lt')
    img = outline(img, 't_out')
    return img


def boulder():
    clumps = [(14.0, 17.5, 11.0, 9.0), (22.0, 21.0, 8.0, 7.0), (9.0, 23.0, 7.5, 5.8)]
    img = blob(32, 32, clumps, ['white', 'st_lt', 'st_lt', 'st_mid', 'st_mid', 'st_dk'], 'b_out',
               seed=13, dither=True, clip=lambda x, y: y <= 30)
    for (x, y) in ((12, 14), (13, 15), (13, 16), (14, 17), (14, 18), (24, 19), (23, 20), (23, 21),
                   (22, 22), (7, 24), (8, 25)):
        if img.get(x, y) not in (None, 'b_out'):
            img.set(x, y, 'st_dk')
    for (x, y, c) in ((8, 11, 't_lt'), (9, 11, 't_lt'), (10, 11, 't_mid'), (7, 12, 't_lt'),
                      (8, 12, 't_mid'), (9, 12, 't_mid'), (12, 9, 't_lt'), (13, 9, 't_lt'),
                      (14, 9, 't_mid'), (11, 10, 't_mid')):
        if img.get(x, y) not in (None, 'b_out'):
            img.set(x, y, c)
    return img


def pebbles():
    img = Img(16, 16)
    peb = [(2, 3, 3, 2), (10, 1, 2, 2), (6, 8, 3, 2), (12, 10, 3, 2), (3, 12, 2, 2),
           (9, 13, 2, 1)]
    for (x, y, w, h) in peb:
        for yy in range(h + 1):
            for xx in range(w):
                c = 'st_mid'
                if yy == 0:
                    c = 'white' if xx == 0 else 'st_lt'
                if yy == h:
                    c = 'st_dk'
                img.set(x + xx, y + yy, c)
    return img


def fallen_leaves():
    img = Img(16, 16)
    leaf = {'.': None, 'a': 'f_yel', 'b': 'f_yeld', 'c': 'f_red', 'd': 'f_redd', 's': 's_dk'}
    shapes = [
        ('.ab\nab.\ns..', (1, 2)), ('cd.\n.cd\n..s', (9, 1)), ('.a.\naab\n.b.', (5, 7)),
        ('..c\n.cd\nsd.', (12, 7)), ('ab.\n.bs', (2, 12)), ('.cc\ncd.', (9, 12)),
        ('a.\nbs', (13, 3)),
    ]
    for (s, (x, y)) in shapes:
        img.paste(G(s, leaf), x, y)
    return img


def small_flowers():
    img = Img(16, 16)
    for (x, y, p, c) in ((3, 3, 'white', 'f_yel'), (11, 2, 'f_red', 'f_yel'),
                         (7, 8, 'white', 'f_yel'), (13, 10, 'f_yel', 'f_yeld'),
                         (3, 12, 'f_red', 'f_yel'), (10, 13, 'white', 'f_yel')):
        img.set(x, y + 2, 'g_dk')
        img.set(x + 1, y + 2, 'g_mid')
        blossom(img, x, y, p, c)
    return img


def lily_pads():
    img = Img(16, 16)
    for (cx, cy, r, notch) in ((5.0, 5.0, 3.6, 0.6), (11.5, 10.5, 3.2, 2.5), (4.0, 12.0, 2.4, 4.0)):
        for y in range(16):
            for x in range(16):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy * 1.0
                d = math.hypot(dx, dy * 1.25)
                if d <= r:
                    ang = math.atan2(dy, dx)
                    if abs(((ang - notch + math.pi) % (2 * math.pi)) - math.pi) < 0.35:
                        continue
                    c = 't_lt'
                    if d > r - 1.0 and (dx + dy > -0.5):
                        c = 't_mid'
                    img.set(x, y, c)
    img = outline(img, 't_mid')
    # lotus flower
    fl = G('''
    ..O.O..
    .OwOwO.
    OwwlwwO
    OlwywlO
    .OlllO.
    ..OOO..
    ''', OL)
    img.paste(fl, 8, 0)
    img.set(4, 3, 'white')
    return img


# ---------------------------------------------------------------------------
# lake: dock, bridge, boat
# ---------------------------------------------------------------------------

DOCK = SG('''
AAAAAAAAAAAOAAAA
BBBdBBBBBBBOBdBB
BBBBBBBBBBBOBBBB
KKKKKKKKKKKKKKKK
AAAAOAAAAAAAAAAA
BdBBOBBBBBBBBdBB
BBBBOBBBBBBBBBBB
KKKKKKKKKKKKKKKK
AAAAAAAAAAOAAAAA
BBBBBBdBBBOBBBBd
BBBBBBBBBBOBBBBB
KKKKKKKKKKKKKKKK
AAOAAAAAAAAAAAAA
BBOBBBBdBBBBBBdB
BBOBBBBBBBBBBBBB
KKKKKKKKKKKKKKKK
''', OL)

DOCK_EDGE = SG('''
AAAAAAAAAAAOAAAA
BBBdBBBBBBBOBdBB
BBBBBBBBBBBOBBBB
KKKKKKKKKKKKKKKK
AAAAOAAAAAAAAAAA
BdBBOBBBBBBBBdBB
KKKKKKKKKKKKKKKK
OOOOOOOOOOOOOOOO
ABBBBBBBBBBBBBBK
BKKKKKKKKKKKKKKK
OOOOOOOOOOOOOOOO
.OABKO....OABKO.
.OABKO....OABKO.
.OuuuO....OuuuO.
.uwuuu....uuwuu.
................
''', OL)

DOCK_POST = SG('''
................
................
................
.....OOOOOO.....
....OAyyyyAO....
....OAAAAAKO....
....OBAAAKKO....
....OABBBBKO....
....OyyyyyAO....
....OAoooooO....
....OABBBBKO....
....OABBBBKO....
...uOABBBBKOu...
..uwuOOOOOOuwu..
...uuwuuuuwuu...
................
''', OL)

BRIDGE_H = SG('''
OOOOOOOOOOOOOOOO
AAAAAAAAAAAAAAAA
KKKKKKKKKKKKKKKK
OOOOOOOOOOOOOOOO
AABKAABKAABKAABK
ABBKABBKABBKABBK
ABBKABBKABdKABBK
ABBKABBKABBKABBK
AdBKABBKABBKABBK
ABBKABBKABBKABBK
ABBKABdKABBKABBK
ABBKABBKABBKABBK
OOOOOOOOOOOOOOOO
AAAAAAAAAAAAAAAA
BBBBBBBBBBBBBBBB
OOOOOOOOOOOOOOOO
''', OL)

BRIDGE_V = SG('''
OAKOAAAAAAAAOAKO
OAKOBBBBBBBBOAKO
OAKOBBBBdBBBOAKO
OAKOKKKKKKKKOAKO
OAKOAAAAAAAAOAKO
OAKOBBdBBBBBOAKO
OAKOBBBBBBBBOAKO
OAKOKKKKKKKKOAKO
OAKOAAAAAAAAOAKO
OAKOBBBBBBdBOAKO
OAKOBBBBBBBBOAKO
OAKOKKKKKKKKOAKO
OAKOAAAAAAAAOAKO
OAKOBdBBBBBBOAKO
OAKOBBBBBBBBOAKO
OAKOKKKKKKKKOAKO
''', OL)

ROWBOAT = SG('''
................................
................................
.....OOOOOOOOOOOOOOOOOOOO.......
...OOAAAAAAAAAAAAAAAAAAAAOOO....
..OAAAOOOOOOOOOOOOOOOOOOOAAAOO..
.OAAOOKKKKOAAOKKKKKKOAAOKKOAAAO.
.OAOKKBKKKOABOKKKKKKOABOKKKOOAAO
.OAOKKKKKKOABOKKBKKKOABOKKKKKOAO
.OAOKKKKKKOABOKKKKKKOABOKKKKOOAO
.OBOOKKKKKOABOKKKKKKOABOKKOOBBO.
.OBBBOOOOOOOOOOOOOOOOOOOOOBBBO..
..OUUUUUUUUUUUUUUUUUUUUUUUUUO...
...OBBBBBBBBBBBBBBBBBBBBBBOO....
....OOOOOOOOOOOOOOOOOOOOOO......
................................
................................
''', OL, w=32)

# ---------------------------------------------------------------------------
# Whisper Meadow / Stormstone Rise (bank 4)
# ---------------------------------------------------------------------------

STANDING_STONE = SG('''
................
................
......OOOO......
....OOssSSOO....
...OssSSSSSDO...
...OsSSSSSSDO...
...OsSSSSDSDO...
...OsSSSSDSDDO..
...OsSSSSSSSDO..
..OssSSSSSSSDO..
..OsSSSSSSSSDO..
..OsSSDSSSSSDO..
..OsSSSDSSSSDO..
..OsSSSSDSSSDDO.
..OsSSSSSSSSDDO.
..OsSSSSSSSSSDO.
..OssSSSSSSSSDO.
..OsSSSSSSSSSDO.
..OsSSSSSDSSSDO.
..OsSSSSSSDSSDO.
..OgSSSSSSSSSDO.
..OngSSSSSSSDDO.
..OsnSSSSSSSDDO.
..OsSSSSSSSSSDO.
.OssSSSSSSSSSDO.
.OsSSSSSSSSSSDDO
.OgnSSSSSSSSSDDO
.OGngSSSSSSnSGDO
..OOOOOOOOOOOOO.
................
................
................
''', WL)


RUNES = [
    '......XX......',
    '.....X..X.....',
    '....X....X....',
    '....X.XX.X....',
    '....X.X..X....',
    '.....X..X.....',
    '......XX......',
    '..............',
    '.......X......',
    '......XX......',
    '.....XX.......',
    '....XXXXX.....',
    '.......XX.....',
    '......XX......',
    '.....XX.......',
    '.....X........',
    '..............',
    '...X......X...',
    '...XX....XX...',
    '....XX..XX....',
    '.....XXXX.....',
    '......XX......',
    '..............',
    '..X..X..X..X..',
]


def stormstone_frames():
    shape = Img(32, 48)
    # monolith: tapering slab with a slanted, chipped top (higher on the left)
    for y in range(2, 45):
        u = (y - 2) / 42.0
        xl = 6.5 - 2.5 * u
        xr = 25.5 + 1.5 * u
        for x in range(32):
            if xl <= x + 0.5 <= xr and y >= 3 + (x - 6) * 0.22 + (2 if x > 21 else 0):
                shape.set(x, y, 'X')
    img = Img(32, 48)
    for y in range(48):
        for x in range(32):
            if shape.p[y][x] is None:
                continue
            left = shape.get(x - 1, y) is None or shape.get(x - 2, y) is None
            right = any(shape.get(x + k, y) is None for k in (1, 2, 3))
            top = shape.get(x, y - 1) is None
            c = 'sl_base'
            if left or top:
                c = 'sl_hi'
            elif right:
                c = 'sl_dk'
            h = hash2(x, y, 77) & 31
            if c == 'sl_base' and h == 0:
                c = 'sl_dk'
            img.set(x, y, c)
    for (x, y) in ((9, 12), (10, 13), (10, 14), (11, 15), (22, 30), (21, 31), (21, 32),
                   (20, 33), (8, 36), (9, 37)):
        img.set(x, y, 'sl_dk')
    # moss at the foot and lichen
    for x in range(4, 29):
        for y in range(40, 45):
            if img.get(x, y) and (hash2(x, y, 9) & 7) < (y - 38):
                img.set(x, y, 't_mid' if (x + y) % 3 else 't_base')
    for (x, y) in ((8, 6), (9, 6), (8, 7), (24, 18), (24, 19)):
        img.set(x, y, 't_lt')
    img = outline(img)
    rub = SG('''
    ..OOO......................OOO..
    .OsSSO.OOO..............OO.OsSSO
    OsSSDDOsSDO............OsSOOSSDO
    OOOOOOOOOOO............OOOOOOOOO
    ''', WL, w=32)
    img.paste(rub, 0, 44)
    rune = set()
    for ry, row in enumerate(RUNES):
        for rx, ch in enumerate(row):
            if ch == 'X':
                rune.add((9 + rx, 10 + ry))
    frames = []
    levels = [('sl_dk', 'sg_base'), ('sg_base', 'sg_hi'), ('sg_hi', 'white'), ('sg_base', 'sg_hi')]
    for (edge, core) in levels:
        fr = img.copy()
        for (x, y) in rune:
            fr.set(x, y, core)
        # carved groove shadow on the lower-right side of each stroke
        for (x, y) in rune:
            for (dx, dy) in ((1, 0), (0, 1), (1, 1)):
                q = (x + dx, y + dy)
                if q not in rune and fr.get(*q) in ('sl_base', 'sl_hi', 'sl_dk'):
                    fr.set(q[0], q[1], edge)
        if core == 'white':
            for (x, y) in ((4, 5), (28, 9), (2, 20), (29, 26)):
                fr.set(x, y, 'sg_hi')
                fr.set(x, y - 1, 'sg_base')
                fr.set(x, y + 1, 'sg_base')
        frames.append(fr)
    return frames


def crystal_frames():
    base = Img(16, 16)
    rock = SG('''
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
    ...OOOO....OOO..
    ..OsSSSOOOOsSSO.
    .OsSSSSSSSSSSDO.
    .OSSSDSSSSSDDDO.
    ..OOOOOOOOOOOO..
    ''', WL)
    crystals = SG('''
    .......OO.......
    ......OwpO......
    ......OppPO.....
    ..OO..OppPO.OO..
    .OwpO.OppPQOpQO.
    .OppPOOppPQOpPO.
    ..OppPOppPQOpPO.
    ..OppPQOpPQpPQO.
    ...OpPQOpPQpPQO.
    ...OppPOpPQpPO..
    ....OpPQOpPpQO..
    ....OOPQOpPPQO..
    ......OOOOOOO...
    ................
    ................
    ................
    ''', WL)
    base.paste(rock, 0, 0)
    base.paste(crystals, 0, 0)
    frames = []
    for (sx, sy) in ((8, 2), (3, 5), (12, 5)):
        fr = base.copy()
        for (dx, dy) in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            if fr.get(sx + dx, sy + dy) not in (None, 'b_out'):
                fr.set(sx + dx, sy + dy, 'white' if (dx, dy) == (0, 0) else 'hg_hi')
        frames.append(fr)
    return frames


def mushrooms():
    return SG('''
    ................
    ................
    ....OOOOOO......
    ..OORwRRRROO....
    .ORwwRRRwwRRO...
    .ORRRRRRRRwRO...
    OxRRRwRRRRRxxO..
    OxxxxRRRRxxxxO..
    .OOssOOOOssOO...
    ...OwwssO.OOOO..
    ...OwwsO.ORwRRO.
    .OOOwwsOOxRRxxO.
    ORwROwsOOOsssOO.
    OxxxOwsO.OwsO...
    .OwsOOOgnOwsOg..
    ..OOgGngGGOOOGn.
    ''', WL)


def berry_bush():
    clumps = [(8.0, 6.5, 5.5, 4.6), (4.8, 9.5, 3.8, 3.6), (11.2, 9.5, 3.8, 3.6),
              (8.0, 10.5, 4.6, 3.4)]
    img = blob(16, 16, clumps, ['t_lt', 't_lt', 't_base', 't_mid'], 'b_out', seed=17, dither=True,
               clip=lambda x, y: 1 <= x <= 14 and y <= 13)
    for (x, y) in ((5, 5), (9, 4), (11, 8), (4, 9), (8, 9), (12, 11), (6, 12)):
        img.set(x, y, 'f_red')
        img.set(x + 1, y, 'f_red')
        img.set(x, y + 1, 'f_red')
        img.set(x + 1, y + 1, 'f_redd')
        img.set(x, y, 'white') if (x + y) % 3 == 0 else img.set(x, y, 'f_red')
    return img


# ---------------------------------------------------------------------------
# more village props
# ---------------------------------------------------------------------------

def fountain_frames():
    frames = []
    cx, cy = 16.0, 21.5
    for f in range(3):
        img = Img(32, 32)

        def hole(x, y):
            d = ell_d(x, y, cx, cy - 0.4, 12.0, 4.6)
            c = 'w_base'
            ring = (d * 3.0 - f * 0.33) % 1.0
            if 0.25 < d < 0.95 and ring < 0.22:
                c = 'w_lt'
            if y + 0.5 < cy - 3.2:
                c = 'st_dk'
            elif y + 0.5 < cy - 2.4 and d > 0.7:
                c = 'st_mid'
            if (hash2(x, y, 11 + f) & 31) == 0 and c == 'w_base':
                c = 'white'
            img.set(x, y, c)
        ring_well(img, cx, cy, 15.0, 6.6, 12.0, 4.6, 4,
                  ['white', 'st_lt', 'st_mid'], ['st_lt', 'st_mid', 'st_dk', 'st_dk'],
                  seed=4, hole=hole)
        # central pedestal and upper bowl
        ped = SG('''
        ......OOOOOOOOOOOO......
        ....OOwwwwllllllmmOO....
        ...OwwuuuuuuuuuuuulmO...
        ...OlluuuuuuuuuuuumdO...
        ....OOllllllllmmmdOO....
        ......OOlllmmmddOO......
        ........OwlmmdO.........
        ........OwlmmdO.........
        ........OwlmmdO.........
        ........OwlmmdO.........
        .......OwllmmddO........
        .......OOOOOOOOO........
        ''', OL, w=24)
        img = outline(img)
        img.paste(ped, 4, 8)
        # water jet and falling drops (animated)
        for y in range(2, 9):
            for x in (15, 16):
                img.set(x, y, 'white' if (y + f) % 3 else 'w_lt')
        crown = [((14, 1), (17, 1), (13, 2), (18, 2)), ((14, 0), (17, 0), (12, 1), (19, 1)),
                 ((15, 1), (16, 1), (13, 1), (18, 1))][f]
        for (x, y) in crown:
            img.set(x, y, 'w_lt')
        for side in (-1, 1):
            for k in range(3):
                t = ((k + f / 3.0) / 3.0)
                x = int(round(16 + side * (8.5 + t * 2.5))) - (1 if side < 0 else 0)
                y = int(round(11 + t * 8))
                img.set(x, y, 'w_lt')
                img.set(x, y - 1, 'white')
        frames.append(img)
    return frames


def picnic_table():
    img = Img(32, 32)
    top = SG('''
    ................................
    ................................
    ...OOOOOOOOOOOOOOOOOOOOOOOOOO...
    ...OwAAAAAAAAAAAAAAAAAAAAAAAO...
    ...OBBBBBBBBBBBBBBBBBBBBBBBKO...
    ...OOOOOOOOOOOOOOOOOOOOOOOOOO...
    ....OKO..................OKO....
    ''', OL, w=32)
    img.paste(top, 0, 0)
    # table top with a checked cloth
    for y in range(7, 20):
        for x in range(1, 31):
            if y == 7 or x in (1, 30) or y == 19:
                c = 'b_out'
            else:
                cx_, cy_ = (x - 2) // 4, (y - 8) // 3
                red = (cx_ + cy_) % 2 == 0
                if y >= 16:
                    red = (cx_ % 2) == 0
                    c = 'p_red' if red else 'st_lt'
                    if y == 18:
                        c = 'wd_dk' if red else 'st_mid'
                else:
                    c = 'p_red' if red else 'white'
            img.set(x, y, c)
    basket = SG('''
    ...OOOOO...
    ..OO...OO..
    .OOOOOOOOO.
    OyAAAAAAAKO
    OAKAKAKAKBO
    OBAKAKAKBKO
    .OOOOOOOOO.
    ''', OL, w=11)
    img.paste(basket, 10, 6)
    for (x, c) in ((12, 'p_red'), (13, 'p_red'), (14, 'white'), (15, 'p_red')):
        img.set(x, 8, c)
    legs = SG('''
    ...OKO..................OKO.....
    ...OKO..................OKO.....
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    .OwAAAAAAAAAAAAAAAAAAAAAAAAAAAO.
    .OBBBBBBBBBBBBBBBBBBBBBBBBBBBKO.
    .OKKKKKKKKKKKKKKKKKKKKKKKKKKKKO.
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    ...OKO..................OKO.....
    ...OKO..................OKO.....
    ...OOO..................OOO.....
    ''', OL, w=32)
    img.paste(legs, 0, 20)
    return img


def notice_board():
    return SG('''
    ................................
    ..OOOOOOOOOOOOOOOOOOOOOOOOOOOO..
    .OAAAAAAAAAAAAAAAAAAAAAAAAAAAAO.
    OBBKBBKBBKBBKBBKBBKBBKBBKBBKBBKO
    OKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKO
    OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
    ..OAAAAAAAAAAAAAAAAAAAAAAAAAAO..
    ..OAOOOOOOOOOOOOOOOOOOOOOOOOKO..
    ..OAOBBBBBBBBBBBBBBBBBBBBBBOKO..
    ..OAOBOOOOOOBBBKBBBOOOOOOOBOKO..
    ..OAOBOwrwlOBOOOOOBOwwwulOBOKO..
    ..OAOBOwmmlOBOwrwOBOwmmmlOBOKO..
    ..OAOBOwllmOBOwmlOBOwllllOBOKO..
    ..OAOBOwmmlOBOwmlOBOwmmmlOBOKO..
    ..OAOBOwllmOBOwllOBOlllllOBOKO..
    ..OAOBOllllOBOlmmOBOOOOOOOBOKO..
    ..OAOBOOOOOOBOOOOOBBBBKBBBBOKO..
    ..OAOBBBKBBBBBBBBBOOOOOOBBBOKO..
    ..OAOBBBBBBBBOOOOOOwwrwOBBBOKO..
    ..OAOBBBBKBBBOwwwylmmmmOBBBOKO..
    ..OAOBBBBBBBBOwmmmmllllOBKBOKO..
    ..OAOBKBBBBBBOllllllmmlOBBBOKO..
    ..OAOBBBBBBBBOOOOOOOOOOOBBBOKO..
    ..OAOOOOOOOOOOOOOOOOOOOOOOOOKO..
    ..OKKKKKKKKKKKKKKKKKKKKKKKKKKO..
    ..OOOOOOOOOOOOOOOOOOOOOOOOOOOO..
    ....OABO..............OABO......
    ....OABO..............OABO......
    ....OABO..............OABO......
    ....OABO..............OABO......
    ....OABO..............OABO......
    ....OOOO..............OOOO......
    ''', OL, w=32)


def wheel(img, cx, cy, r, rim='wd_dk', spoke='wd_dk', hub='st_mid'):
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= r:
                c = None
                if d > r - 1.0:
                    c = 'b_out'
                elif d > r - 2.2:
                    c = 'wd_lt' if (y + 0.5 - cy) < -1 and (x + 0.5 - cx) < 1 else \
                        'wd_base' if (y + 0.5 - cy) < 1.5 else rim
                elif d < 1.3:
                    c = hub
                else:
                    ang = math.degrees(math.atan2(y + 0.5 - cy, x + 0.5 - cx)) % 60
                    if ang < 13 or ang > 47:
                        c = spoke
                if c:
                    img.set(x, y, c)
    return img


def cart():
    img = Img(32, 32)
    load = Img(32, 32)
    hay = blob(32, 32, [(13.0, 15.0, 9.0, 5.0)], ['p_yel', 'p_yel', 'wd_lt', 'wd_base'],
               'b_out', seed=31, dither=True, clip=lambda x, y: y <= 16)
    load.paste(hay, 0, 0)
    for (px, py) in ((20.5, 13.5), (25.0, 14.5)):
        pk = blob(32, 32, [(px, py, 3.2, 2.6)], ['p_yel', 'fx_org', 'fx_org', 'wd_base'],
                  'b_out', seed=5)
        load.paste(pk, 0, 0)
        load.set(int(px), int(py - 3), 't_mid')
        load.set(int(px), int(py - 2), 'wd_dk')
    img.paste(load, 0, 0)
    bed = SG('''
    ..OOOOOOOOOOOOOOOOOOOOOOOOOOOO..
    ..OwAAAAAAAAAAAAAAAAAAAAAAAAAO..
    ..OBBBBBBBKBBBBBBBBBKBBBBBBBKO..
    ..OKKKKKKKKKKKKKKKKKKKKKKKKKKO..
    ..OAAAAAAAAAAAAAAAAAAAAAAAAAAO..
    ..OBBBBBBKBBBBBBBBBBBBBKBBBBKO..
    ..OKKKKKKKKKKKKKKKKKKKKKKKKKKO..
    ..OOOOOOOOOOOOOOOOOOOOOOOOOOOO..
    ''', OL, w=32)
    img.paste(bed, 0, 16)
    for x in range(0, 3):
        img.set(x, 21, 'b_out')
        img.set(x, 22, 'wd_base')
        img.set(x, 23, 'b_out')
    for y in range(24, 30):
        img.set(5, y, 'b_out')
        img.set(6, y, 'wd_base')
        img.set(7, y, 'b_out')
    for x in (5, 6, 7):
        img.set(x, 30, 'b_out')
    wheel(img, 20.0, 24.5, 7.0)
    return img


def wheelbarrow():
    """Side view, facing right: steel tray of soil, wooden handles running
    back to the left, a prop leg and the front wheel."""
    img = Img(16, 16)
    for (y, x0, x1) in ((6, 2, 13), (7, 3, 13), (8, 4, 12), (9, 5, 11)):
        for x in range(x0, x1 + 1):
            t = (x - x0) / max(1, x1 - x0)
            c = 'st_lt' if t < 0.7 else 'st_mid'
            if y == 6:
                c = 'white' if t < 0.5 else 'st_lt'
            if y == 9:
                c = 'st_mid' if t < 0.6 else 'st_dk'
            img.set(x, y, c)
    for x in range(0, 12):
        y = 9 + int(round((x) * 3.0 / 11.0))
        img.set(x, y, 'wd_base' if x > 1 else 'wd_lt')
    for y in range(10, 14):
        img.set(5, y, 'wd_dk')
    img = outline(img)
    wheel(img, 12.0, 12.0, 3.6, hub='st_dk')
    soil = G('''
    ...OOOO...
    .OOKBBgOO.
    OKBBBBBBKO
    ''', OL)
    img.paste(soil, 2, 3)
    img.set(8, 3, 't_mid')
    img.set(8, 2, 'b_out')
    img.set(9, 3, 'b_out')
    img.set(7, 3, 'b_out')
    return img


SCARECROW = SG('''
................
......OOOO......
.....OyyyAO.....
.....OyAAAO.....
....OrrrrrrO....
..OOyyyyyAAAOO..
.OyyyyyyAAAAABO.
..OOOOOOOOOOOO..
....OAAAAAABO...
....OAKAAAKBO...
....OAAAAAABO...
....OAKKKKKBO...
.....OAAAABO....
......OOOOO.....
.......OKO......
OOOOOOOOOOOOOOO.
OyOuuuUUUUUUOyO.
OAOuUUUUUUUUOAO.
.OOOuUUUUUUOOO..
...OuUrrUUUO....
...OuUrrUUUO....
...OuUUUUUUO....
...OyUyUUyUyO...
...OOOOKBOOOO...
.......OKBO.....
.......OKBO.....
.......OKBO.....
.......OKBO.....
.......OKBO.....
......OOKBOO....
......OKKKKO....
......OOOOOO....
''', OL)

KIN_STATUE = SG('''
................
................
.....O.O........
....OwOlO.......
....OwllO.......
...OwlllmO......
..OwllOllmO.....
OOwwlllllmO.....
OwwwwlllllO.....
.OOOwwlllmO..OO.
....OwwllmO.OdyO
....OwwlllO.OyoO
...OwwlllllOOdO.
...OwwllllllOmO.
..OwwlllllllmdO.
..OwlllllllllmO.
..OwllOllllllmO.
..OwlOOOllllmmO.
..OwlO.OlllmmdO.
.OOwlOOOllmmmdO.
.OwwwOwwwlmmmdO.
.OOOOOOOOOOOOOO.
.OwwwwwwlllllmO.
OOOOOOOOOOOOOOOO
.OlllllllllmmdO.
.OlmdddddddmmdO.
.OlmdyoyoyommdO.
.OlmdddddddmmdO.
.OlllllllllmmdO.
OOOOOOOOOOOOOOOO
OwwwllllllmmmmdO
OOOOOOOOOOOOOOOO
''', OL)

SHRINE = SG('''
................
................
.......OO.......
.....OOroOO.....
...OOrroorrOO...
.OOrrooorrrrrOO.
OrrooorrrrrrrrrO
OKKKKKKKKKKKKKKO
OOOOOOOOOOOOOOOO
..OAOOOOOOOOAO..
..OAOdddddOOKO..
..OAOdOyyOdOKO..
..OAOdywyyOdKO..
..OAOdOyoOddKO..
..OAOdddddddKO..
.OOOOOOOOOOOOOO.
.OwAAAAAAAAAABO.
.OKKKKKKKKKKKKO.
.OOOOOOOOOOOOOO.
...OAO....OBO...
...OAO....OBO...
..OOOOOOOOOOOO..
..OwwllllllmmO..
..OlllllllmmdO..
..OlmmmmmmmmdO..
..OOOOOOOOOOOO..
''', OL, h=32)

SIGN_ARROW = SG('''
................
.OOOOOOOOOOOO...
.OwAAAAAAAAAAO..
.OBBBKBBBBKBBBO.
.OKKKKKKKKKKKKKO
.OOOOOOOOOOOOOO.
.....OABKO......
..OOOOOOOOOOOOO.
.OAAAAAAAAAAAAO.
OBBBKBBBBBKBBBO.
OKKKKKKKKKKKKKO.
.OOOOOOOOOOOOO..
.....OABKO......
.....OABKO......
.....OABKO......
.....OOOOO......
''', OL)


def clothesline():
    img = Img(32, 16)
    posts = SG('''
    OOOOO......................OOOOO
    OAABO......................OAABO
    OOOOO......................OOOOO
    .OAO........................OBO.
    .OAO........................OBO.
    .OAO........................OBO.
    .OAO........................OBO.
    .OAO........................OBO.
    .OAO........................OBO.
    .OAO........................OBO.
    .OAO........................OBO.
    .OAO........................OBO.
    .OAO........................OBO.
    .OAO........................OBO.
    .OAO........................OBO.
    .OOO........................OOO.
    ''', OL, w=32)
    img.paste(posts, 0, 0)
    for x in range(4, 28):
        sag = int(round(2.2 * math.sin(math.pi * (x - 3) / 25.0)))
        img.set(x, 2 + sag, 'st_dk')
    laundry = SG('''
    ....OOOOOOO...OOOOO.............
    ...OwwwwwwwO..OuuuO...OOO.OOO...
    ..OwwOwwwOwwO.OuUuO...OrO.OrO...
    ..OwOOwwwOOwO.OuuuO...OrO.OrO...
    ..OO.OwwwO.OO.OUuUO...OrO.OrO...
    .....OwlwO....OuuuO...OroOOro...
    .....OwllO....OUuUO...OOOOOOO...
    .....OOOOO....OOOOO.............
    ''', OL, w=32)
    img.paste(laundry, 1, 3)
    for (x, y) in ((8, 3), (13, 3), (16, 4), (19, 4), (24, 4), (27, 3)):
        img.set(x, y, 'wd_base')
    return img


def beehive_frames():
    base = SG('''
    ................
    ................
    ......OOOO......
    ....OOyyyAOO....
    ...OyyyyyAABO...
    ...OKKKKKKKKO...
    ..OyyyyyAAAABO..
    ..OKKKKKKKKKKO..
    ..OyywyyAAAABO..
    .OKKKKKKKKKKKKO.
    .OyyyyyAOOABBBO.
    .OyyyyAOOOOBBKO.
    OOOOOOOOOOOOOOOO
    OwAAAAAAAAAAAABO
    OKKKKKKKKKKKKKKO
    .OO..........OO.
    ''', OL)
    paths = [[(3, 3), (13, 5), (11, 1)], [(2, 6), (14, 2), (8, 0)], [(4, 1), (12, 4), (14, 8)]]
    frames = []
    for f, pts in enumerate(paths):
        img = base.copy()
        for (x, y) in pts:
            if img.get(x, y) is None:
                img.set(x, y, 'white')
                for (dx, dy) in ((1, 0), (-1, 0)):
                    if img.get(x + dx, y + dy) is None:
                        img.set(x + dx, y + dy, 'p_yel')
        img.set(9, 12, 'fx_org' if f != 1 else 'p_yel')
        frames.append(img)
    return frames


def weather_vane():
    img = Img(16, 32)
    # arrow: fletched tail (left), shaft, broad head (right)
    for x in range(2, 13):
        img.set(x, 7, 'st_dk')
    for (x, y) in ((12, 5), (12, 6), (13, 6), (12, 8), (13, 8), (12, 9), (13, 7), (14, 7),
                   (12, 7)):
        img.set(x, y, 'st_dk')
    for (x, y) in ((0, 5), (1, 6), (2, 6), (0, 9), (1, 8), (2, 8), (1, 5), (1, 9), (3, 6), (3, 8)):
        img.set(x, y, 'st_mid')
    # pole, finial, compass arms
    for y in range(8, 27):
        img.set(7, y, 'st_mid')
        img.set(8, y, 'st_dk')
    for x in range(3, 13):
        img.set(x, 14, 'st_dk')
    img = outline(img)
    for (x, y) in ((7, 3), (8, 3), (7, 4), (8, 4)):
        img.set(x, y, 'p_yel' if (x, y) != (8, 4) else 'fx_org')
    for (x, y) in ((6, 3), (9, 3), (6, 4), (9, 4), (7, 2), (8, 2), (7, 5), (8, 5)):
        img.set(x, y, 'b_out')
    for (bx, by) in ((2, 14), (13, 14)):
        img.set(bx, by, 'p_yel')
        for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if img.get(bx + dx, by + dy) is None:
                img.set(bx + dx, by + dy, 'b_out')
    base = SG('''
    .....OOOOOO.....
    ....OwllmmdO....
    ....OlmmmddO....
    ....OOOOOOOO....
    ''', OL)
    img.paste(base, 0, 26)
    return img


WEATHER_VANE = weather_vane()

TELESCOPE = SG('''
................
................
................
...........OOO..
..........OwuUO.
.........OyAuUO.
........OyAABKO.
.......OyAABKO..
......OyAABKO...
.....OyAABKO....
....OdAABKO.....
...OddABKO......
..OdmOOKO.......
..OOOOOOO.......
.....OddO.......
.....OmdO.......
.....OddO.......
....OKOOKO......
....OKOOBKO.....
...OKOOOOBO.....
...OKO.OKOBO....
..OKO..OKO.BO...
..OKO..OKO.OBO..
.OKO...OKO..OBO.
.OKO...OKO..OBO.
.OKO...OKO...OBO
OKO....OKO...OBO
OOO....OOO...OOO
''', OL, h=32)

RAIN_GAUGE = SG('''
................
....OOOOOOO.....
....OwlllmO.....
.....OlmdO......
.....OwlmOO.....
.....OwldOd.....
.....OwllO......
.....OwldOd.....
.....OuuUO......
.....OuUUOd.....
.....OuUUO......
.....OOOOO......
......OBKO......
......OBKO......
......OBKO......
......OOOO......
''', OL)


def pumpkins():
    img = Img(16, 16)
    for (px, py, rx, ry) in ((5.0, 10.0, 4.2, 3.2), (11.5, 11.5, 3.4, 2.8)):
        pk = blob(16, 16, [(px, py, rx, ry)], ['p_yel', 'fx_org', 'fx_org', 'wd_base'],
                  'b_out', seed=7)
        for y in range(16):
            for x in (int(px - rx * 0.45), int(px + rx * 0.4)):
                if pk.p[y][x] not in (None, 'b_out'):
                    pk.p[y][x] = 'wd_base' if pk.p[y][x] != 'p_yel' else 'fx_org'
        img.paste(pk, 0, 0)
    for (x, y, c) in ((5, 5, 'b_out'), (6, 5, 'b_out'), (4, 6, 'b_out'), (5, 6, 'wd_dk'),
                      (6, 6, 'b_out'), (11, 7, 'b_out'), (10, 8, 'b_out'), (11, 8, 'wd_dk'),
                      (12, 8, 'b_out'), (7, 6, 't_lt'), (8, 6, 't_mid'), (8, 5, 't_lt'),
                      (2, 6, 't_mid'), (3, 5, 't_lt')):
        img.set(x, y, c)
    return img


def sunflowers():
    img = Img(16, 32)
    stems = SG('''
    ....OGO...OGO...
    ....OGO...OGO...
    ...OgGO..OGgO...
    ..OggGO..OGggO..
    ..OOgGO.OgGOOO..
    ....OGOOggGO....
    ....OGOOggOGO...
    ....OGO.OOOGO...
    ...OgGO...OGO...
    ..OggGO...OGgO..
    ..OOOGO...OGggO.
    ....OGO...OGOOO.
    ....OGO...OGO...
    ....OOO...OOO...
    ''', OL)
    img.paste(stems, 0, 18)
    head = SG('''
    ..OOOOO..
    .OyyOyyO.
    OyyoooyyO
    OyoKKKoyO
    OOoKBKoOO
    OyoKKKoyO
    OyyoooyyO
    .OyyOyyO.
    ..OOOOO..
    ''', OL, w=9)
    for (hx, hy) in ((1, 10), (7, 12)):
        img.paste(head, hx, hy)
    return img


BUOY = SG('''
................
................
................
.......OO.......
......OddO......
.......OO.......
.....OOOOOO.....
....OwwrrrrO....
....OwrrrrrO....
....OwwwwwlO....
....OrrrrrrO....
...uOOOOOOOOu...
..uwuuuuuuuuwu..
...uuwuuuuwuu...
................
................
''', OL)


def bunting():
    img = Img(16, 16)
    for x in range(16):
        sag = int(round(1.6 * math.sin(math.pi * x / 16.0)))
        img.set(x, 1 + sag, 'wd_dk')
    for (fx, c) in ((1, 'p_red'), (6, 'p_yel'), (11, 'w_lt')):
        sag = int(round(1.6 * math.sin(math.pi * (fx + 2) / 16.0)))
        tri = G('''
        OOOOO
        OcccO
        .OcO.
        .OcO.
        ..O..
        ''', {'.': None, 'O': 'b_out', 'c': c})
        img.paste(tri, fx, 2 + sag)
    return img


def crops():
    img = Img(16, 16)
    for y in range(16):
        for x in range(16):
            r = y % 8
            if r in (0, 1):
                c = 'wd_base' if r == 0 else 'wd_lt'
            elif r in (2, 3, 4, 5):
                c = 'wd_base' if (hash2(x, y, 3) & 7) else 'wd_lt'
            else:
                c = 'wd_dk'
            img.set(x, y, c)
    leaf = SG('''
    .gOg.
    gGgGg
    OgwgO
    gGgGG
    .OGO.
    ''', OL, w=5)
    for (cx, cy) in ((4, 4), (12, 4), (4, 12), (12, 12)):
        img.paste(leaf, cx - 2, cy - 3)
    return img


# ---------------------------------------------------------------------------
# catalog
# ---------------------------------------------------------------------------

TW = ['town', 'wild']

OUTDOOR_DECOR = [
    # --- existing kinds (names kept) --------------------------------------
    Decor('SIGNPOST', TW, SIGN, doc='wooden signpost (read with A)'),
    Decor('MAILBOX', ['town'], MAILBOX, doc='red mailbox on a post'),
    Decor('FENCE', TW, FENCE, doc='fence: post left, rails to the right edge'),
    Decor('FENCE_END', TW, FENCE_POST, doc='closing fence post'),
    Decor('LAMP', ['town'], LAMP, top='X/.', doc='street lamp; head drawn above people'),
    Decor('ROCK', TW, ROCK, doc='boulder'),
    Decor('BUSH', TW, _bush(), doc='round bush'),
    # --- village props ----------------------------------------------------
    Decor('BENCH', TW, BENCH, doc='wooden park bench'),
    Decor('BARREL', TW, BARREL, doc='wooden barrel'),
    Decor('CRATE', TW, CRATE, doc='wooden crate'),
    Decor('CRATE_STACK', TW, crate_stack(), top='X/.', doc='stacked crates; upper crate over people'),
    Decor('SACKS', TW, sacks(), doc='grain and flour sacks'),
    Decor('FLOWER_POT', ['town'], flower_pot(), doc='terracotta pot with flowers'),
    Decor('PLANTER', ['town'], planter(), doc='wooden flower box'),
    Decor('WELL', TW, well(), top='XX/..', doc='stone well with roof; roof row over people'),
    Decor('HAY_BALE', TW, HAY_BALE, doc='bale of straw'),
    Decor('WATER_TROUGH', TW, trough(), doc='wooden water trough'),
    Decor('MARKET_STALL', ['town'], market_stall(), top='XXX/...',
          doc='market stall; striped awning row over people (vendor stands under it)'),
    Decor('OLD_HEARTH', ['town'], frames=hearth_frames(), period=8,
          doc='the Old Hearth: ancient stone brazier, burning (plaza centrepiece)'),
    Decor('LANTERN_POST', TW, frames=lantern_post_frames(), period=10, top='X/.',
          doc='post with a hanging lantern (flickers); lantern over people'),
    Decor('STONE_LANTERN', TW, frames=stone_lantern_frames(), period=20, top='X/.',
          doc='stone lantern with a warm window; cap over people'),
    Decor('CAMPFIRE', TW, frames=campfire_frames(), period=8, doc='campfire in a stone ring'),
    Decor('FLAG', TW, frames=flag_frames(), period=10, top='X/.',
          doc='teal village flag with the hearth flame, waving'),
    Decor('TENT', TW, tent(), top='XX/..', doc='teal canvas tent (hermit / camp)'),
    # --- wood, trees, stones --------------------------------------------
    Decor('WOODPILE', TW, woodpile(), doc='stacked firewood'),
    Decor('STUMP', TW, stump(), doc='tree stump'),
    Decor('LOG', TW, fallen_log(), doc='fallen mossy log'),
    Decor('BIG_TREE', TW, big_tree(), top='XX/..', doc='big oak; canopy row over people'),
    Decor('HEDGE', TW, hedge(), doc='trimmed hedge, tiles horizontally'),
    Decor('HEDGE_END', TW, hedge_end(), doc='hedge end cap (right; mirror for the left)'),
    Decor('BOULDER', TW, boulder(), doc='big mossy boulder'),
    Decor('PEBBLES', TW, pebbles(), solid='.', doc='scattered pebbles (walkable decal)'),
    Decor('FALLEN_LEAVES', TW, fallen_leaves(), solid='.', doc='autumn leaves (walkable decal)'),
    Decor('SMALL_FLOWERS', TW, small_flowers(), solid='.', doc='tiny flowers (walkable decal)'),
    # --- lake --------------------------------------------------------------
    Decor('LILY_PADS', TW, lily_pads(), doc='lily pads with a lotus, on water'),
    Decor('DOCK', ['wild'], DOCK, floor='X', doc='dock planks over water (walkable, tiles both ways)'),
    Decor('DOCK_EDGE', ['wild'], DOCK_EDGE, floor='X', doc='dock front edge with posts (south side)'),
    Decor('DOCK_POST', ['wild'], DOCK_POST, doc='mooring post in the water'),
    Decor('BRIDGE_H', TW, BRIDGE_H, floor='X', doc='plank bridge over water, walk left-right'),
    Decor('BRIDGE_V', TW, BRIDGE_V, floor='X', doc='plank bridge over water, walk up-down'),
    Decor('ROWBOAT', ['wild'], ROWBOAT, doc='rowboat on the water'),
    # --- meadow / stormstone ----------------------------------------------
    Decor('STANDING_STONE', ['wild'], STANDING_STONE, top='X/.',
          doc='ancient standing stone; top over people'),
    Decor('STORMSTONE', ['wild'], frames=stormstone_frames(), period=12, top='XX/XX/..',
          doc='the Stormstone: monolith with glowing storm runes (pulses)'),
    Decor('CRYSTAL_CLUSTER', ['wild'], frames=crystal_frames(), period=14,
          doc='heartglass crystals growing from rock (twinkle)'),
    Decor('MUSHROOMS', ['wild'], mushrooms(), doc='cluster of red toadstools'),
    Decor('BERRY_BUSH', ['wild'], berry_bush(), doc='bush with red berries'),
    # --- more village / route props ---------------------------------------
    Decor('FOUNTAIN', ['town'], frames=fountain_frames(), period=10,
          doc='stone fountain with a splashing jet'),
    Decor('PICNIC_TABLE', TW, picnic_table(), doc='picnic table with a checked cloth and basket'),
    Decor('NOTICE_BOARD', TW, notice_board(), top='XX/..',
          doc='notice board with pinned papers; roof row over people'),
    Decor('CART', TW, cart(), top='XX/..', doc='farm cart with hay and pumpkins'),
    Decor('WHEELBARROW', TW, wheelbarrow(), doc='wheelbarrow with soil'),
    Decor('SCARECROW', TW, SCARECROW, top='X/.', doc='scarecrow; hat and head over people'),
    Decor('KIN_STATUE', ['town'], KIN_STATUE, top='X/.',
          doc='stone statue of FLARIX with its lantern tail, on a plinth'),
    Decor('SHRINE', TW, SHRINE, top='X/.', doc='wayside shrine with a small lantern'),
    Decor('SIGN_ARROW', TW, SIGN_ARROW, doc='direction sign (mirror to swap arrows)'),
    Decor('GATE', TW, GATE, doc='closed fence gate (continues a FENCE line)'),
    Decor('CLOTHESLINE', ['town'], clothesline(), doc='clothesline with laundry'),
    Decor('BEEHIVE', TW, frames=beehive_frames(), period=9,
          doc='straw skep of glow-bees (bees glimmer around it)'),
    Decor('WEATHER_VANE', TW, WEATHER_VANE, top='X/.',
          doc='iron weather vane with a little storm dragon'),
    Decor('TELESCOPE', ['wild'], TELESCOPE, top='X/.', doc='brass telescope on a tripod (lake station)'),
    Decor('RAIN_GAUGE', TW, RAIN_GAUGE, doc='rain gauge on a stake'),
    Decor('PUMPKINS', TW, pumpkins(), doc='pumpkins on the ground'),
    Decor('SUNFLOWERS', TW, sunflowers(), top='X/.', doc='tall sunflowers; heads over people'),
    Decor('BUOY', ['wild'], BUOY, doc='red and white buoy on the water'),
    Decor('BUNTING', ['town'], bunting(), top='X', doc='festival bunting overhead (walk under; tiles)'),
    Decor('CROPS', TW, crops(), doc='vegetable bed: tilled rows with cabbages (tiles)'),
]
