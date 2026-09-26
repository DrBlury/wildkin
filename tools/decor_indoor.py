#!/usr/bin/env python3
"""Interior art: floors and walls (used by the interior tileset) and the
indoor decor catalog (furniture on a transparent background)."""

import math
from pixelart import Img, G, tex_fill, hash2

IL = {'.': None, 'O': 'i_out', '#': 'void',
      'W': 'wp_hi', 'w': 'wp_base', 'p': 'wp_pat', 'q': 'wp_dk',
      'A': 'bb_lt', 'B': 'bb_base', 'K': 'bb_dk',
      'F': 'fl_hi', 'f': 'fl_base', 'm': 'fl_mid', 'n': 'fl_dk',
      'C': 'ck_hi', 'c': 'ck_base', 'l': 'ck_line', 'L': 'ck_dk',
      'a': 'gl_hi', 'b': 'gl_base', 'd': 'gl_dk',
      'R': 'rd_hi', 'r': 'rd_base', 'x': 'rd_dk',
      'Y': 'gd_hi', 'y': 'gd_base',
      'U': 'bl_hi', 'u': 'bl_base', 'v': 'bl_dk',
      'Z': 'white',
      'G': 'lf_hi', 'g': 'lf_base', 'h': 'lf_dk',
      'T': 'pt_base', 't': 'pt_dk',
      'M': 'mt_hi', 'N': 'mt_base', 'E': 'mt_dk',
      'S': 'sc_hi', 's': 'sc_base', 'z': 'sc_dk',
      'P': 'pk_hi', 'k': 'pk_base'}


def IG(text):
    return G(text, IL)


I_FLOOR = IG('''
fffffffFffnFffff
ffffffffffnfffff
fFffffffffnffFff
mmmmmmmmmmmmmmmm
ffnFffffffffffff
ffnfffffFfffffff
ffnffffffffffffF
mmmmmmmmmmmmmmmm
fffffffnFfffffff
fFfffffnffffffff
fffffffnfffffFff
mmmmmmmmmmmmmmmm
ffffFfffffffffnF
ffffffffffffffnf
ffffffffffFfffnf
mmmmmmmmmmmmmmmm
''')

I_FLOOR2 = IG('''
CCCCCCClcccccccl
CCCCCCClcccccccl
CCCCCCClcccccccl
CCCCCCClcccccccl
CCCCCCClcccccccl
CCCCCCClcccccccl
CCCCCCClcccccccl
llllllllllllllll
ccccccclCCCCCCCl
ccccccclCCCCCCCl
ccccccclCCCCCCCl
ccccccclCCCCCCCl
ccccccclCCCCCCCl
ccccccclCCCCCCCl
ccccccclCCCCCCCl
llllllllllllllll
''')

I_WALL_TOP = IG('''
OOOOOOOOOOOOOOOO
KKKKKKKKKKKKKKKK
qqqqqqqqqqqqqqqq
wwwpwwwwwwwpwwww
wwpWpwwwwwpWpwww
wwwpwwwwwwwpwwww
wwwwwwwwwwwwwwww
wwwwwwwwwwwwwwww
wwwwwwwpwwwwwwwp
wwwwwwpWpwwwwwpW
wwwwwwwpwwwwwwwp
wwwwwwwwwwwwwwww
wwwwwwwwwwwwwwww
wwwpwwwwwwwpwwww
wwpWpwwwwwpWpwww
wwwpwwwwwwwpwwww
''')

I_WALL = IG('''
wwwwwwwwwwwwwwww
wwwwwwwwwwwwwwww
wwwwwwwpwwwwwwwp
wwwwwwpWpwwwwwpW
wwwwwwwpwwwwwwwp
wwwwwwwwwwwwwwww
AAAAAAAAAAAAAAAA
BBBBBBBBBBBBBBBB
KKKKKKKKKKKKKKKK
BABBBBBKBABBBBBK
BABBBBBKBABBBBBK
BABBBBBKBABBBBBK
BABBBBBKBABBBBBK
KKKKKKKKKKKKKKKK
KKKKKKKKKKKKKKKK
OOOOOOOOOOOOOOOO
''')


def floor_shadow(bg):
    """Color that furniture shadows take on a given floor texture."""
    return 'ck_dk' if bg is I_FLOOR2 else 'fl_dk'


def shadowize(grid, color, rows):
    """Mark the given color in the given rows as a floor shadow ('SHADOW'):
    baked versions paint it in the floor's shadow color, the transparent
    (mid-layer) versions drop it."""
    img = grid.copy()
    for y in rows:
        if 0 <= y < img.h:
            for x in range(img.w):
                if img.p[y][x] == color:
                    img.p[y][x] = 'SHADOW'
    return img


def mid(grid):
    """Transparent-background version for the interior mid BG layer."""
    return grid.replace({'SHADOW': None})


def on(bg, grid, ox=0, oy=0):
    """Composite a grid (transparent '.') over a copy of a background
    texture tiled to the grid's size."""
    img = Img(grid.w, grid.h)
    tex_fill(img, bg)
    img.paste(grid.replace({'SHADOW': floor_shadow(bg)}), ox, oy)
    return img


def on_wallfloor(grid, wall_rows=16, floor=None):
    """Background: WALL (lower wall) for the first metatile row, floor below."""
    floor = floor or I_FLOOR
    img = Img(grid.w, grid.h)
    for y in range(grid.h):
        for x in range(grid.w):
            if y < wall_rows:
                img.p[y][x] = I_WALL.p[y % 16][x % 16]
            else:
                img.p[y][x] = floor.p[y % 16][x % 16]
    img.paste(grid.replace({'SHADOW': floor_shadow(floor)}), 0, 0)
    return img


I_WINDOW = IG('''
................
................
................
.OOOOOOOOOOOOOO.
.OAAAAAAAAAAAAO.
.OAaaabbAaabbKO.
.OAaabbbAabbbKO.
.OAabbbbAbbbbKO.
.OAAAAAAAAAAAKO.
.OAbbbbbAbbbbKO.
.OAbbbbbAbbbbKO.
.OAbbbbbAbbbbKO.
.OKKKKKKKKKKKKO.
OOOOOOOOOOOOOOOO
OAAAAAAAAAAAAAAO
qOOOOOOOOOOOOOOq
''')

I_CLOCK = IG('''
................
................
................
.....OOOOOO.....
....OyYYYYyO....
...OyZZZZZZyO...
..OyZZZOZZZZyO..
..OYZZZOZZZZyO..
..OYZZZOOOZZyO..
..OYZZZZZZZZyO..
..OyZZZZZZZZyO..
...OyZZZZZZyOq..
....OyyyyyyOq...
.....OOOOOOq....
......qqqq......
................
''')

I_PAINTING = IG('''
................
................
................
.OOOOOOOOOOOOOO.
.OAAAAAAAAAAABO.
.OAaaaaaaaaaaKO.
.OAaaaWWWaaabKO.
.OAaaaaaaabbbKO.
.OAbbAAbbbbbbKO.
.OAbABBAbbbAAKO.
.OAABBBBAAABBKO.
.OABBKBBBBBBKKO.
.OAKKKKKKKKKKKO.
.OOOOOOOOOOOOOOq
..qqqqqqqqqqqqq.
................
''')

I_DOORMAT = IG('''
................
................
.OOOOOOOOOOOOOO.
OxRRRRRRRRRRRRxO
OrrrrrrrrrrrrrrO
OrYYYYYYYYYYYYrO
OrrrrrrrrrrrrrrO
OrYyYyYyYyYyYyrO
OrrrrrrrrrrrrrrO
OrYYYYYYYYYYYYrO
OrrrrrrrrrrrrrrO
OxxxxxxxxxxxxxxO
.OOOOOOOOOOOOOO.
..nnnnnnnnnnnnn.
................
................
''')

I_TV = IG('''
................
.OOOOOOOOOOOOOO.
.OMMMMMMMMMMMNO.
.OMOOOOOOOOOONO.
.OMOaabbbbbONEO.
.OMObabbbbbONEO.
.OMObbbbbbdONEO.
.OMObbbbbddONEO.
.OMOOOOOOOOONEO.
.ONNNNNNNNREOEO.
.OEEEEEEEEEEEEO.
.OOOOOOOOOOOOOO.
..OABBBBBBBBKOn.
..OKKKKKKKKKKOn.
..OOnnnnnnnnOOn.
...nnnnnnnnnnnn.
''')

I_COUNTER = IG('''
................
OOOOOOOOOOOOOOOO
WWWWWWWWWWWWWWWW
wwwwwwwwwwwwwwww
wwwwwwwwwwwwwwww
pppppppppppppppp
OOOOOOOOOOOOOOOO
AAAAAAAAAAAAAAAA
BBBBBBBKBBBBBBBK
BBBBBBBKBBBBBBBK
BBBBBBBKBBBBBBBK
BBBBBBBKBBBBBBBK
KKKKKKKKKKKKKKKK
OOOOOOOOOOOOOOOO
LLLLLLLLLLLLLLLL
................
''')

I_COUNTER_L = IG('''
................
..OOOOOOOOOOOOOO
.OWWWWWWWWWWWWWW
.OWwwwwwwwwwwwww
.OWwwwwwwwwwwwww
.Oqppppppppppppp
.OOOOOOOOOOOOOOO
.OAAAAAAAAAAAAAA
.OABBBBBBBBBBBBK
.OABBBBBBBBBBBBK
.OABBBBBBBBBBBBK
.OABBBBBBBBBBBBK
.OKKKKKKKKKKKKKK
.OOOOOOOOOOOOOOO
..LLLLLLLLLLLLLL
................
''')


I_BED = IG('''
.OOOOOOOOOOOOOO.
.OAAAAAAAAAAABO.
.OABBBBBBBBBBKO.
.OKKKKKKKKKKKKO.
.OZZZZZZZZZZZMO.
.OZOOOOOOOOOOMO.
.OZOZZZZZZZZOMO.
.OZOZZZZZZZMOMO.
.OZOMMMMMMMMOMO.
.OZOOOOOOOOOOMO.
.OUUUUUUUUUUUUO.
.OZZZZZZZZZZZZO.
.OuUUUUUUUUUUuO.
.OuuuuuuuuuuuvO.
.OuuuuuuuuuuuvO.
.OuUuuuuuuuUuvO.
.OuuuuuuuuuuuvO.
.OuuuuuuuuuuuvO.
.OuuuuuuuuuuuvO.
.OuUuuuuuuuUuvO.
.OuuuuuuuuuuuvO.
.OuuuuuuuuuuuvO.
.OuuuuuuuuuuuvO.
.OvvvvvvvvvvvvO.
.OOOOOOOOOOOOOO.
.OAAAAAAAAAAABO.
.OKKKKKKKKKKKKO.
.OOOOOOOOOOOOOOn
..OKO......OKOn.
..OOOnnnnnnOOOn.
...nnnnnnnnnnnn.
................
''')


I_PLANT = IG('''
................
.....OOOOO......
...OOGGgGgOO....
..OGGgGgggghO...
.OGgGggGgghggO..
.OgGgggggGhghO..
OGgggGhggggghhO.
OgGggggggGgghhO.
OggGhgggggghghO.
.OggggGgghgghO..
.OhgggggggghhO..
OGgghgGgghghhhO.
OgghgggghgghhhO.
.OhhgghghhhhhO..
..OOhhhhhhhOO...
...OOOOOOOOO....
...OTTTTTTTtO...
....OTTTTTtO....
....OTTTTTtO....
....OTTTTTtO....
....OTTTTttOn...
.....OOOOOOnn...
......nnnnnn....
................
''')


def i_rug():
    img = Img(48, 32)
    for y in range(2, 30):
        for x in range(1, 47):
            if y in (2, 29) or x in (1, 46):
                c = 'i_out'
            elif y in (3, 28) or x in (2, 45):
                c = 'rd_dk'
            elif y in (4, 27) or x in (3, 44):
                c = 'gd_base'
            elif y in (5, 26) or x in (4, 43):
                c = 'rd_dk'
            else:
                c = 'rd_base'
                cx, cy = x - 23.5, y - 15.5
                dd = abs(cx) / 2.0 + abs(cy)
                if 7.0 <= dd < 8.0 or 3.0 <= dd < 3.9:
                    c = 'gd_hi'
                elif dd < 2.0:
                    c = 'gd_base'
                elif (x + y) % 6 == 0 and dd > 9.5 and 7 < x < 40 and 8 < y < 24:
                    c = 'rd_hi'
            img.p[y][x] = c
    return on(I_FLOOR, img)


def i_shop_shelf():
    img = Img(32, 32)
    for y in range(0, 30):
        for x in range(0, 32):
            if y == 0 or y == 29 or x == 0 or x == 31:
                c = 'i_out'
            elif y == 1:
                c = 'mt_hi'
            elif y == 2:
                c = 'mt_base'
            elif x in (1, 30):
                c = 'mt_base' if x == 1 else 'mt_dk'
            elif y in (10, 19, 27):
                c = 'mt_hi'
            elif y in (11, 20, 28):
                c = 'mt_dk'
            elif y == 3:
                c = 'i_out'
            else:
                c = 'mt_dk' if y in (12, 21, 4) else 'ck_line'
            img.p[y][x] = c
    goods = [
        # (x, width, height, body, hi, cap)
        ('bottle', 'rd_base', 'rd_hi'), ('bottle', 'bl_base', 'bl_hi'),
        ('box', 'gd_base', 'gd_hi'), ('bottle', 'bl_base', 'bl_hi'),
        ('box', 'rd_base', 'rd_hi'), ('bottle', 'gd_base', 'gd_hi'),
        ('box', 'bl_base', 'bl_hi'), ('bottle', 'rd_base', 'rd_hi'),
    ]
    k = 0
    for (sy0, sy1) in ((5, 9), (13, 18), (22, 26)):
        x = 3
        while x < 28:
            kind, body, hi = goods[k % len(goods)]
            k += 1
            if kind == 'bottle':
                w = 3
                for yy in range(sy0, sy1 + 1):
                    for xx in range(x, x + w):
                        if yy == sy0:
                            c = 'i_out' if xx != x + 1 else 'mt_hi'
                        elif yy == sy0 + 1 and xx != x + 1:
                            c = None
                        else:
                            c = hi if xx == x else body
                            if xx == x + w - 1:
                                c = 'i_out'
                        if c:
                            img.p[yy][xx] = c
                x += w + 1
            else:
                w = 4
                for yy in range(sy0 + 1, sy1 + 1):
                    for xx in range(x, x + w):
                        c = hi if yy == sy0 + 1 else body
                        if xx == x + w - 1 or yy == sy0 + 1 and xx == x:
                            c = 'i_out' if xx == x + w - 1 else c
                        if yy == sy0 + 3 and x < xx < x + w - 1:
                            c = 'white'
                        img.p[yy][xx] = c
                x += w + 1
    for x in range(1, 32):
        img.p[30][x] = 'SHADOW'
    img.p[30][0] = None
    return img


I_LAB = IG('''
OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
OMMMMMMMMMMMMMMMMMMMMMMMMMMMMMNO
OMNNNNNNNNNNNNNNNNNNNNNNNNNNNNEO
OMNOOOOOOOOOONNNNOOOOOOOOOOONNEO
OMNOSSsssssOONNNNOSSssssssszONEO
OMNOSsszssOSONOONOSsssssssszONEO
OMNOsszzssOsONRONOsssssSssszONEO
OMNOszsszzOsONOONOssssSsssszONEO
OMNOzzzzzzOzONOONOssssssssszONEO
OMNOOOOOOOOOONPONOzzzzzzzzzzONEO
OMNNNNNNNNNNNNOONOOOOOOOOOOONNEO
OMNNNNNNNNNNNNNNNNNNNNNNNNNNNNEO
OMEEEEEEEEEEEEEEEEEEEEEEEEEEEEEO
OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
OMMMMMMMMMMMMMMMMMMMMMMMMMMMMMNO
OMNNNNNNNNNNNNNNNNNNNNNNNNNNNNEO
OMNOONOONOONNNNNNNOOOOOOOOONNNEO
OMNOROOSOOPONEEENNOSSSSSSSONNNEO
OMNOONOONOONNNNNNNOszszszsONNNEO
OMNNNNNNNNNNNEEENNOOOOOOOOONNNEO
OMNEEEEEEEEENNNNNNNNNNNNNNNNNNEO
OMNEMMMMMMMENEEENNNEEENNNEEENNEO
OMNEMEEEEEMENNNNNNNEMENNNEMENNEO
OMNEMMMMMMMENEEENNNEEENNNEEENNEO
OMNEEEEEEEEENNNNNNNNNNNNNNNNNNEO
OMNNNNNNNNNNNNNNNNNNNNNNNNNNNNEO
OEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEO
OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
.OEEO....................OEEO...
.OOOOLLLLLLLLLLLLLLLLLLLLOOOOLL.
..LLLLLLLLLLLLLLLLLLLLLLLLLLLLL.
................................
''')


I_STOVE = IG('''
OOOOOOOOOOOOOOOO
OMMMMMMMMMMMMMNO
OMNRNNRNNRNNRNEO
ONNNNNNNNNNNNNEO
OOOOOOOOOOOOOOOO
OMMMMMMMMMMMMMNO
OMMOOOMMMMOOOMNO
OMOEEEOMMOEEEONO
OMMOOOMMMMOOOMNO
OMMMMMMMMMMMMMNO
OMMOOOMMMMOOOMNO
OMOEEEOMMOEEEONO
OMMOOOMMMMOOOMNO
OMMMMMMMMMMMMMNO
ONNNNNNNNNNNNNEO
OOOOOOOOOOOOOOOO
OMMMMMMMMMMMMMNO
OMOOOOOOOOOOOMNO
OMONNNNNNNNNOMNO
OMOOOOOOOOOOOMNO
OMOdddddddddOMNO
OMOdbbaabbbdOMNO
OMOdbabbbbbdOMNO
OMOdbbbbbbbdOMNO
OMOdddddddddOMNO
OMOOOOOOOOOOOMNO
OMMMMMMMMMMMMMNO
OEEEEEEEEEEEEEEO
OOOOOOOOOOOOOOOO
.OEO........OEO.
.nnnnnnnnnnnnnn.
................
''')


def pad_top(grid, h):
    img = Img(grid.w, h)
    img.paste(grid, 0, h - grid.h)
    return img


# =====================================================================
# Indoor decor catalog
# =====================================================================
#
# Furniture is drawn on a transparent background and placed over any floor
# (or over the lower wall row, for tall pieces standing against the wall).
# No floor shadows (no alpha on GBA): a dark bottom outline grounds each
# piece. Each 8x8 tile must fit one palette bank of the interior tileset:
# banks 0, 1 and 3 are fixed by the floors/walls/rugs, banks 2 and 4-7 below
# are the furniture banks (15 colours each).
#
# Wall pieces (CHALKBOARD, MAP_POSTER, CALENDAR, PENNANT) are drawn to hang
# on the upper wall row (WALL_TOP): they sit below its dark top trim.
# Tall pieces (1x2, 2x2) stand with their upper row over the lower wall
# (WALL) row; their upper cells are `top` so they also work in open floor.

from pixelart import Decor  # noqa: E402
from decor_outdoor import SG, outline, in_ell, ell_d, flames, blob  # noqa: E402

# Extra colours used only by indoor decor (name -> (r, g, b)). The heartglass
# colours are shared with the outdoor catalog (same values).
INDOOR_COLORS = {
    'if_org': (240, 136, 56),     # fire, lantern glow
    'br_hi': (216, 124, 92),      # bricks
    'br_base': (176, 84, 64),
    'br_dk': (122, 54, 50),
    'hg_hi': (255, 212, 240),     # heartglass (same values as the outdoor catalog)
    'hg_base': (232, 128, 200),
    'hg_dk': (150, 72, 168),
}

L2 = dict(IL)
L2.update({'o': 'if_org', '1': 'br_hi', '2': 'br_base', '3': 'br_dk', '8': 'hg_hi',
           '9': 'hg_base', '0': 'hg_dk', 'D': 'gd_base'})


def I2(text, w=16, h=None):
    return SG(text, L2, w=w, h=h)


FIRE_COLS = ('white', 'gd_hi', 'if_org', 'rd_base')


def no_floor_shadow(img):
    """Old grids baked a floor shadow in fl_dk; decor must be transparent."""
    return img.replace({'fl_dk': None, 'SHADOW': None})


# ------------------------------------------------------------------ seating

CHAIR = I2('''
................
................
....OOOOOOOO....
....OAAAAAAO....
....OBBBBBBO....
....OKKKKKKO....
....OAO..OBO....
....OAO..OBO....
...OOOOOOOOOO...
...OAAAAAAAAO...
...OBBBBBBBKO...
...OKKKKKKKKO...
...OOOOOOOOOO...
...OKO....OKO...
...OKO....OKO...
...OOO....OOO...
''')

CHAIR_UP = I2('''
................
................
....OOOOOOOO....
....OAAAAAAO....
....OBBBBBBO....
....OKKKKKKO....
....OAOBBOKO....
...OOAOBBOKOO...
...OAAOBBOKAO...
...OBBOKKOKBO...
...OKKKKKKKKO...
...OOOOOOOOOO...
...OKO....OKO...
...OKO....OKO...
...OOO....OOO...
................
''')

CHAIR_SIDE = I2('''
................
................
.....OOO........
.....OAO........
.....OAKO.......
.....OAKO.......
.....OAKO.......
.....OAKOOOOOO..
.....OAAAAAAAAO.
.....OBBBBBBBKO.
.....OKKKKKKKKO.
.....OOOOOOOOOO.
.....OKO....OKO.
.....OKO....OKO.
.....OOO....OOO.
................
''')

STOOL = I2('''
................
................
................
................
................
.....OOOOOO.....
....OAAAAAAO....
....OABBBBKO....
....OKKKKKKO....
.....OOOOOO.....
.....OKOOKO.....
....OKO..OKO....
....OKO..OKO....
....OOO..OOO....
................
................
''')

CUSHION = I2('''
................
................
................
....O......O....
...OYOOOOOOYO...
....ORRRRRrO....
...ORRrrrrrrO...
...ORrrRrrrrO...
...OrrrrrrrxO...
...OrrrrrrxxO...
....OrxxxxxO....
...OYOOOOOOYO...
....O......O....
................
................
................
''')


# ------------------------------------------------------------------ tables

def table_img(w, h, top_rows=15, runner=None):
    """Rectangular wooden table (like the 2x2 TABLE), w x h pixels."""
    img = Img(w, h)
    y0, y1 = 3, 3 + top_rows - 1
    for y in range(y0, y1 + 1):
        for x in range(1, w - 1):
            if y in (y0, y1) or x in (1, w - 2):
                c = 'i_out'
            elif y == y0 + 1:
                c = 'bb_lt'
            elif y >= y1 - 2:
                c = 'bb_dk'
            elif x == 2:
                c = 'bb_lt'
            elif x == w - 3:
                c = 'bb_dk'
            else:
                c = 'bb_base'
                if y in (y0 + 4, y0 + 8) and (x * 7 + y) % 9 < 5:
                    c = 'bb_lt'
            img.p[y][x] = c
    if runner:
        for y in range(y0 + 2, y1 - 2):
            for x in range(w // 2 - 5, w // 2 + 5):
                c = runner[1]
                if x in (w // 2 - 5, w // 2 + 4):
                    c = runner[0]
                elif (y - y0) % 4 == 0:
                    c = runner[2]
                img.p[y][x] = c
        for x in range(w // 2 - 5, w // 2 + 5):
            img.p[y1 - 2][x] = runner[3]
            img.p[y1 - 1][x] = runner[3] if x % 2 else runner[0]
    legs = [3, w - 6]
    if w > 40:
        legs.append(w // 2 - 1)
    for lx in legs:
        for y in range(y1 + 1, y1 + 10):
            for x in range(lx, lx + 3):
                img.p[y][x] = 'i_out' if x in (lx, lx + 2) or y == y1 + 9 else 'bb_dk'
    return img


TABLE = table_img(32, 32)
LONG_TABLE = table_img(48, 32, runner=('gd_base', 'rd_base', 'rd_hi', 'rd_dk'))


def round_table():
    img = Img(32, 32)
    cx, cy, rx, ry = 16.0, 11.0, 14.5, 7.5
    for y in range(32):
        for x in range(32):
            if in_ell(x, y, cx, cy, rx, ry):
                c = 'bb_base'
                d = ell_d(x, y, cx - 3, cy - 2, rx, ry)
                if d < 0.55:
                    c = 'bb_lt' if (x + y) % 5 else 'bb_base'
                if ell_d(x, y, cx, cy, rx, ry) > 0.86 and y + 0.5 > cy:
                    c = 'bb_lt' if y + 0.5 < cy + 3 else 'bb_base'
                if in_ell(x, y, cx, cy - 0.6, 5.5, 2.8):
                    c = 'white' if not in_ell(x, y, cx, cy - 0.6, 3.5, 1.6) else 'wp_hi'
                    if (x + y) % 3 == 0 and not in_ell(x, y, cx, cy - 0.6, 4.5, 2.2):
                        c = 'wp_base'
                img.set(x, y, c)
            elif in_ell(x, y, cx, cy + 2.0, rx, ry) and y + 0.5 > cy:
                img.set(x, y, 'bb_dk')
    for y in range(19, 27):
        for x in range(14, 18):
            img.set(x, y, 'bb_base' if x < 16 else 'bb_dk')
    for y in range(26, 31):
        for x in range(32):
            if in_ell(x, y, 16, 28.2, 6.5, 2.2):
                img.set(x, y, 'bb_base' if x < 17 else 'bb_dk')
    return outline(img, 'i_out')


DESK = I2('''
................................
...................OO...........
....OOOOOO........OZZO...OOO....
...OZZZZZZO.......OZO...OvuvO...
...OCClClCO......OZO....OuuuO...
.OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
.OAAAAAAAAAAAAAAAAAAAAAAAAAAAAO.
.OBBBBBBBBBBBBBBBBBBBBBBBBBBBKO.
.OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
.OAOAAAAAAOKKKKKKKKKKOAAAAAAOKO.
.OAOBBBYBBOKKKKKKKKKKOBBBYBBOKO.
.OAOOOOOOOOKKKKKKKKKKOOOOOOOOKO.
.OAOBBBYBBOKKKKKKKKKKOBBBYBBOKO.
.OKOOOOOOOOOOOOOOOOOOOOOOOOOOKO.
.OKO........................OKO.
.OOO........................OOO.
''', w=32)


def tea_set():
    img = I2('''
    ................
    ................
    ....OOO.........
    ...OZZZOO.......
    ..OZZuZZZO..OO..
    .OOZuuuZZOOOZZO.
    .OZOZZZZOZOOuZO.
    ..OOCZZCOO..OOO.
    .OOOOOOOOOOOOOO.
    OAAAAAAAAAAAAAAO
    OBBBBBBBBBBBBBKO
    .OOOOOOOOOOOOOO.
    ...OKO....OKO...
    ...OKO....OKO...
    ...OKO....OKO...
    ...OOO....OOO...
    ''')
    return img


# ------------------------------------------------------------------ beds

BED = no_floor_shadow(I_BED).replace({'mt_hi': 'bl_hi'})


def double_bed():
    img = Img(32, 32)
    head = I2('''
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    .OAAAAAAAAAAAAAAAAAAAAAAAAAAAAO.
    .OABBBBBBBBBBBBBBBBBBBBBBBBBBKO.
    .OKKKKKKKKKKKKKKKKKKKKKKKKKKKKO.
    .OZZZZZZZZZZZZZZZZZZZZZZZZZZZUO.
    .OZOOOOOOOOOOOZZOOOOOOOOOOOOZUO.
    .OZOZZZZZZZZZOZZOZZZZZZZZZZOZUO.
    .OZOZZZZZZZZUOZZOZZZZZZZZZUOZUO.
    .OZOUUUUUUUUUOZZOUUUUUUUUUUOZUO.
    .OZOOOOOOOOOOOZZOOOOOOOOOOOOZUO.
    ''', w=32)
    img.paste(head, 0, 0)
    for y in range(10, 27):
        for x in range(1, 31):
            if x in (1, 30):
                c = 'i_out'
            elif y == 10:
                c = 'bl_hi'
            elif y == 11:
                c = 'white'
            else:
                c = 'bl_base'
                u, v = (x - 2) % 7, (y - 12) % 5
                if u == 0 or v == 0:
                    c = 'bl_hi'
                if u == 3 and v == 2:
                    c = 'white'
                if x >= 28 or y >= 25:
                    c = 'bl_dk' if c == 'bl_base' else 'bl_base'
            img.set(x, y, c)
    foot = I2('''
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    .OAAAAAAAAAAAAAAAAAAAAAAAAAAAAO.
    .OKKKKKKKKKKKKKKKKKKKKKKKKKKKKO.
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    ..OKO......................OKO..
    ..OOO......................OOO..
    ''', w=32)
    img.paste(foot, 0, 26)
    return img


KIN_BASKET = I2('''
................
................
................
................
................
....OOOOOOOO....
..OOfFfFfFfFOO..
.OfFOOOOOOOOfnO.
.OFORRRRRRrrOmO.
.OfORrRRrrrxOnO.
.OFOOrrrrrxOOmO.
.OfFfmfmfmfmfnO.
.OmnmnmnmnmnmnO.
..OOOOOOOOOOOO..
................
................
''')


# ------------------------------------------------------------------ storage

def bookshelf(w, h, seed=0):
    img = Img(w, h)
    book_cols = ['rd_base', 'bl_base', 'lf_base', 'bl_base', 'rd_base', 'lf_base', 'gd_base']
    hi = {'rd_base': 'rd_hi', 'bl_base': 'bl_hi', 'lf_base': 'lf_hi', 'gd_base': 'gd_hi'}
    nshelf = 3 if h >= 30 else 2
    for y in range(0, h - 2):
        for x in range(0, w):
            if y == 0 or y == h - 3 or x == 0 or x == w - 1:
                c = 'i_out'
            elif y in (1, 2):
                c = 'bb_lt' if y == 1 else 'bb_base'
            elif x in (1, 2):
                c = 'bb_base' if x == 1 else 'bb_dk'
            elif x in (w - 3, w - 2):
                c = 'bb_base' if x == w - 3 else 'bb_dk'
            else:
                c = 'bb_dk'
            img.p[y][x] = c
    step = (h - 6) // nshelf
    shelves = []
    for i in range(nshelf):
        top = 3 + i * step
        img_row = top
        for x in range(1, w - 1):
            img.p[top][x] = 'i_out'
            img.p[top + step - 1][x] = 'bb_lt'
        shelves.append((top + 1, top + step - 2))
    k = seed
    for si, (y0, y1) in enumerate(shelves):
        x = 3
        while x < w - 4:
            k += 1
            bw = 2 + (hash2(k, si, 5) % 2)
            if x + bw > w - 3:
                break
            col = book_cols[(k * 3 + si) % len(book_cols)]
            top = y0 + (hash2(k, si, 9) % 3)
            if hash2(k, si, 11) % 7 == 0:
                x += 2
                continue
            for yy in range(top, y1 + 1):
                for xx in range(x, x + bw):
                    c = col
                    if xx == x + bw - 1:
                        c = 'i_out'
                    elif yy == top:
                        c = hi[col]
                    elif yy == top + 2 and bw > 2:
                        c = 'gd_hi'
                    img.p[yy][xx] = c
            x += bw
    return img


BOOKSHELF = bookshelf(32, 32)
BOOKSHELF_SMALL = bookshelf(16, 32, seed=40)

WARDROBE = I2('''
.OOOOOOOOOOOOOO.
OAAAAAAAAAAAAAAO
OBBBBBBBBBBBBBKO
OOOOOOOOOOOOOOOO
.OAAAAAAOAAAAKO.
.OABBBBBOABBBKO.
.OABOOOBOAOOOKO.
.OABOBKBOAOBKKO.
.OABOBKBOAOBKKO.
.OABOBKBOAOBKKO.
.OABOBKBOAOBKKO.
.OABOOOBOAOOOKO.
.OABBBBYOYBBBKO.
.OABBBBYOYBBBKO.
.OABOOOBOAOOOKO.
.OABOBKBOAOBKKO.
.OABOBKBOAOBKKO.
.OABOBKBOAOBKKO.
.OABOOOBOAOOOKO.
.OABBBBBOABBBKO.
.OKKKKKKOKKKKKO.
.OOOOOOOOOOOOOO.
.OAAAAAAAAAAAKO.
.OABBBBYYBBBBKO.
.OKKKKKKKKKKKKO.
.OOOOOOOOOOOOOO.
.OAAAAAAAAAAAKO.
.OABBBBYYBBBBKO.
.OKKKKKKKKKKKKO.
.OOOOOOOOOOOOOO.
.OKO........OKO.
.OOO........OOO.
''')

DRESSER = I2('''
................
.......OOO......
......OZuZO.....
......OuuvO.....
.OOOOOOOOOOOOOO.
OAAAAAAAAAAAAAAO
OBBBBBBBBBBBBBKO
OOOOOOOOOOOOOOOO
OAOAAAAYYAAAAOKO
OAOBBBBYYBBBBOKO
OAOOOOOOOOOOOOKO
OAOAAAAYYAAAAOKO
OAOBBBBYYBBBBOKO
OKOOOOOOOOOOOOKO
OKO..........OKO
OOO..........OOO
''')


def barrel_in():
    return I2('''
    ................
    ....OOOOOOOO....
    ..OOBBBBBBBBOO..
    .OBAAAAAAAAAABO.
    .OBAAKAAAAKAABO.
    .OKBAKAAAAKABKO.
    .OOKKKKKKKKKKOO.
    .OMNNNNNNNNNEO..
    OABBBKBBBBKBBKKO
    OABBBKBBBBKBBKKO
    OABBBKBBBBKBBKKO
    OMNNNNNNNNEEEEEO
    .OABBKBBBBKBBKO.
    .OABBKBBBBKBKKO.
    ..OOOOOOOOOOOO..
    ................
    ''')


SACKS_IN = SG('''
................
................
....OOO.........
...OFffO........
....OnO...OOO...
...OFFfOOOZZCO..
..OFFFfffOOlO...
.OFFfFFfffOZOO..
.OFFFFfffOZZZCO.
.OFFFffffOZZZCCO
.OFfFffmfOZZrCLO
.OFFfffmOZZrrCLO
.OFfffmmOZZZCCLO
..OmmmmmOCCCCLO.
...OOOOOOOOOOO..
................
''', {'.': None, 'O': 'i_out', 'F': 'wp_hi', 'f': 'wp_base', 'm': 'wp_dk',
       'n': 'bb_dk', 'Z': 'white', 'C': 'ck_hi', 'l': 'ck_line', 'L': 'ck_dk', 'r': 'gd_base'})

TOY_BOX = I2('''
................
.......OO.......
......OUuO..OO..
...OOOOOOOOOYyO.
..OAAAAAAAAAAOO.
..OKKKKKKKKKKKO.
.OOOOOOOOOOOOOO.
.ORRRRRRRRRRRxO.
.ORrrrrYrrrrrxO.
.ORrrrYYYrrrrxO.
.ORrrrrYrrrrrxO.
.ORrrrrrrrrrrxO.
.OxxxxxxxxxxxxO.
.OOOOOOOOOOOOOO.
..OKO......OKO..
..OOO......OOO..
''')


def icebox():
    return SG('''
    ................
    .OOOOOOOOOOOOOO.
    OAAAAAAAAAAAAAAO
    OBBBBBBBBBBBBBKO
    OOOOOOOOOOOOOOOO
    OAOAAAAAAAAAAOKO
    OAOCCCCCCCCCCOKO
    OAOCccccccccLOKO
    OAOCccccccccLOKO
    OAOCccccMNccLOKO
    OAOCccccEEccLOKO
    OAOCccccccccLOKO
    OAOCccccccccLOKO
    OAOLLLLLLLLLLOKO
    OAOOOOOOOOOOOOKO
    OAOAAAAAAAAAAOKO
    OAOCCCCCCCCCCOKO
    OAOCccccccccLOKO
    OAOCccccMNccLOKO
    OAOCccccEEccLOKO
    OAOCccccccccLOKO
    OAOCccccccccLOKO
    OAOCccccccccLOKO
    OAOLLLLLLLLLLOKO
    OAOOOOOOOOOOOOKO
    OKKKKKKKKKKKKKKO
    OOOOOOOOOOOOOOOO
    .OKO........OKO.
    .OOO........OOO.
    ''', dict(L2, C='bb_lt', c='bb_base', L='bb_dk'), h=32)


def sink_counter():
    return I2('''
    ................
    ................
    ....OOOOOOOO....
    ...OCCCCCCCCO...
    ...OCZCCZCCLO...
    ...OClllllllO...
    ...OCZuCZUCLO...
    ...OClllllllO...
    ...OCCCCCCCCO...
    ...OOOOOOOOOO...
    ................
    ......OOOO......
    ......OMNEO.....
    .......OO.OO....
    .......OMO......
    .......OMO......
    OOOOOOOOOOOOOOOO
    OMMMMMMMMMMMMMNO
    OMOOOOOOOOOOOONO
    OMOabbbbbbbbdONO
    OMOOOOOOOOOOOONO
    OEEEEEEEEEEEEEEO
    OOOOOOOOOOOOOOOO
    OAOAAAAAOAAAAOKO
    OAOBBBBBOBBBBOKO
    OAOBBBBYOYBBBOKO
    OAOBBBBBOBBBBOKO
    OAOBBBBBOBBBBOKO
    OAOKKKKKOKKKKOKO
    OKOOOOOOOOOOOOKO
    OKKKKKKKKKKKKKKO
    OOOOOOOOOOOOOOOO
    ''')


COAT_RACK = I2('''
................
................
......OOOO......
.....OAAAKO.....
...OOOOAKOOOO...
..OBO.OAKO.OBO..
...O.OOAKO..O...
....ORRAKxO.....
...ORRROKRxO....
...ORRrOKrxO....
...ORrrOKrxO....
...ORrrOKrxO....
...ORrrOKrxO....
...OxrrOKrxO....
....OxxOKxO.....
.....OOAKOO.....
......OAKO......
......OAKOSO....
......OAKOsO....
......OAKOsO....
......OAKOSO....
......OAKOzO....
......OAKO.O....
......OAKO......
......OAKO......
......OAKO......
......OAKO......
....OOOAKOOO....
...OAAAAAAAKO...
...OKKKKKKKKO...
...OOOOOOOOOO...
................
''')


def mirror():
    img = Img(16, 32)
    for y in range(1, 24):
        for x in range(16):
            if in_ell(x, y, 8.0, 12.0, 6.5, 11.0):
                inner = in_ell(x, y, 8.0, 12.0, 4.6, 9.2)
                if inner:
                    c = 'bl_base'
                    if ell_d(x, y, 6.0, 8.0, 3.0, 6.0) < 0.7:
                        c = 'bl_hi'
                    if (x - y) % 7 == 0 and ell_d(x, y, 8.0, 12.0, 4.6, 9.2) < 0.8:
                        c = 'white'
                    if x > 9 and y > 13:
                        c = 'bl_dk' if (x + y) % 3 == 0 else 'bl_base'
                else:
                    c = 'gd_hi' if x < 8 and y < 14 else 'gd_base' if x < 11 else 'bb_base'
                img.set(x, y, c)
    stand = I2('''
    .......OO.......
    .......OO.......
    ......OAKO......
    ......OAKO......
    ......OAKO......
    .....OOAKOO.....
    ...OOAAAAKKOO...
    ..OKKKKKKKKKKO..
    ..OOO......OOO..
    ''')
    img = outline(img, 'i_out')
    img.paste(stand, 0, 23)
    return img


# ------------------------------------------------------------------ plants & vases

def pot_plant(clumps, pot_y, seed=3):
    img = blob(16, 16, clumps, ['lf_hi', 'lf_base', 'lf_base', 'lf_dk'], 'i_out', seed=seed,
               dither=True, clip=lambda x, y: y < pot_y + 1)
    pot = I2('''
    ..OOOOOOOOOO..
    ..OTTTTTTTtO..
    ...OOOOOOOO...
    ...OTTTTTtO...
    ...OTTTTTtO...
    ....OTTTtO....
    ....OOOOOO....
    ''', w=14)
    img.paste(pot, 1, pot_y)
    return img


SMALL_PLANT = pot_plant([(8, 5.5, 4.5, 3.8), (5, 7.5, 3.0, 2.4), (11, 7.5, 3.0, 2.4)], 9)

CACTUS = I2('''
................
.......OO.......
......OPkO......
......OGgO......
.....OGgZhO.....
..OO.OGgghO.....
.OGgOOZgghO.OO..
.OGghOGgZhOOghO.
.OGgghGgghOgGhO.
..OGgghgghghhO..
...OOOGgghOOO...
.....OGGghO.....
..OOOOOOOOOOOO..
..OTTTTTTTTTtO..
...OTTTTTTTtO...
...OOOOOOOOOO...
''')

VASE = I2('''
................
......OOOO......
.....OZZZUO.....
......OZUO......
.....OZZZUO.....
....OZZuZZUO....
...OZZuuuZUvO...
...OZuZuZuUvO...
...OZZuuuZUvO...
...OZZZuZZUvO...
....OZZZZUvO....
.....OZZUvO.....
....OUUUUvvO....
....OOOOOOOO....
................
................
''')

FLOWER_VASE = SG('''
................
....OO..OO......
...ORRO.OYYO.OO.
..ORrRROYyYOOPkO
..OORrOGOYOGOkPO
.OPPOOGgOOGgOOO.
.OPkkOgOZZOgGO..
..OOOGOZYZZOGgO.
....OgOOZZOOgO..
.....OOZZZUOO...
.....OZZuZUO....
....OZZuuuZUO...
....OZZZuZZUO...
.....OZZZZUO....
.....OOOOOOO....
................
''', dict(L2, R='if_org', r='gd_base'))


# ------------------------------------------------------------------ clocks & lamps

CLOCK_BASE = '''
................
.....OOOOOO.....
....OAAAAAAO....
...OOOOOOOOOO...
...OAYYYYYYKO...
...OYZZZZZZDO...
...OYZZOZZZDO...
...OYZZOOOZDO...
...OYZZZZZZDO...
...OADDDDDDKO...
...OOOOOOOOOO...
....OAOOOOKO....
....OAOddOKO....
....OAOddOKO....
....OAOddOKO....
....OAOddOKO....
....OAOddOKO....
....OAOddOKO....
....OAOddOKO....
....OAOddOKO....
....OAOddOKO....
....OAOddOKO....
....OAOOOOKO....
...OOOOOOOOOO...
...OABBBBBBKO...
...OABBYYBBKO...
...OABBBBBBKO...
...OKKKKKKKKO...
...OOOOOOOOOO...
...OKO....OKO...
...OOO....OOO...
................
'''


def clock_frames():
    base = I2(CLOCK_BASE)
    # widen the pendulum window: columns 6..9, rows 12..21
    for y in range(12, 22):
        for x in range(6, 10):
            base.set(x, y, 'bb_dk')
    frames = []
    for sw in (0, -1, 0, 1):
        img = base.copy()
        for y in range(12, 19):
            xo = 7.5 + sw * (y - 12) / 7.0 * 1.0
            img.set(int(round(xo - 0.5)), y, 'gd_base')
        bx = int(round(7.5 + sw * 1.2 - 0.5))
        for (dx, dy, c) in ((0, 0, 'gd_hi'), (1, 0, 'gd_base'), (0, 1, 'gd_base'), (1, 1, 'bb_base')):
            if 6 <= bx + dx <= 9:
                img.set(bx + dx, 19 + dy, c)
        frames.append(img)
    return frames


FLOOR_LAMP = I2('''
................
................
.....OOOOOO.....
....OWWWWWwO....
...OWWYWWWwpO...
...OWYYWWwwpO...
..OWWWWWWwwppO..
..OWWWWWwwwppO..
.OOOOOOOOOOOOOO.
....OOYYYYOO....
......OYYO......
.......OO.......
.......OMO......
.......ONO......
.......OMO......
.......ONO......
.......OMO......
.......ONO......
.......OMO......
.......ONO......
.......OMO......
.......ONO......
.......OMO......
.......ONO......
.......OMO......
.......ONO......
.......OMO......
.....OOOMOOO....
....OMMMMNNEO...
....ONNNNEEEO...
....OOOOOOOOO...
................
''')


# ------------------------------------------------------------------ bakery & kitchen

def bread_display():
    img = I2('''
    ................................
    ................................
    ................................
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    .OFFFFFFFFFFFFFFFFFFFFFFFFFFFFO.
    .OFfffffffffffffffffffffffffffO.
    .OFfffffffffffffffffffffffffffO.
    .OFfffffffffffffffffffffffffffO.
    .OFfffffffffffffffffffffffffffO.
    .OFfffffffffffffffffffffffffffO.
    .OFfffffffffffffffffffffffffffO.
    .OFfffffffffffffffffffffffffffO.
    .OFfffffffffffffffffffffffffffO.
    .OmmmmmmmmmmmmmmmmmmmmmmmmmmmmO.
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    .OAAAAAAAAAAAAAAAAAAAAAAAAAAAKO.
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    .OAOaaaaaaaaaaaaaaaaaaaaaaaaOKO.
    .OAOabbbbbbbbbbbbbbbbbbbbbbbOKO.
    .OAOabbbbbbbbbbbbbbbbbbbbbbbOKO.
    .OAOabbbbbbbbbbbbbbbbbbbbbbbOKO.
    .OAOabbbbbbbbbbbbbbbbbbbbbbbOKO.
    .OAOaaaaaaaaaaaaaaaaaaaaaaaaOKO.
    .OAOabbbbbbbbbbbbbbbbbbbbbbbOKO.
    .OAOabbbbbbbbbbbbbbbbbbbbbbbOKO.
    .OAOabbbbbbbbbbbbbbbbbbbbbbbOKO.
    .OAOOOOOOOOOOOOOOOOOOOOOOOOOOKO.
    .OAAAAAAAAAAAAAAAAAAAAAAAAAAAKO.
    .OBBBBBBBBFFBBBBBBBBBBFFBBBBBKO.
    .OKKKKKKKKKKKKKKKKKKKKKKKKKKKKO.
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    ..OKO......................OKO..
    ''', w=32)
    goods = Img(32, 32)
    # a basket of round loaves (left) and baguettes (right) on the counter
    basket = I2('''
    .OOOOOOOOOOO.
    OfFfFfFfFfFfO
    OmfmfmfmfmfnO
    .OnnnnnnnnnO.
    ''', w=13)
    goods.paste(basket, 3, 9)
    goods.paste(basket, 16, 9)
    loaf = G('''
    .OOOO.
    OFFFfO
    OFfffmO
    OmmmmnO
    ''', L2)
    for (x, y) in ((3, 6), (8, 5), (10, 7)):
        goods.paste(loaf, x, y)
    bag = G('''
    ....OOO
    ..OOFfO
    OOFfmO.
    OFmmO..
    OOOO...
    ''', L2)
    for x in (16, 19, 22, 24):
        goods.paste(bag, x, 5)
    img.paste(goods, 0, 0)
    # pastries behind the glass: rolls, berry tarts, honey buns
    for i, x in enumerate(range(6, 27, 4)):
        y = 19
        c = [('fl_hi', 'fl_base', 'fl_mid'), ('fl_base', 'fl_mid', 'fl_dk'),
             ('fl_hi', 'fl_mid', 'fl_dk')][i % 3]
        img.set(x, y, c[0]); img.set(x + 1, y, c[1]); img.set(x + 2, y, c[1])
        img.set(x, y + 1, c[1]); img.set(x + 1, y + 1, c[1]); img.set(x + 2, y + 1, c[2])
        y = 24
        c = [('fl_base', 'fl_mid', 'fl_dk'), ('fl_hi', 'fl_base', 'fl_mid'),
             ('fl_hi', 'fl_mid', 'fl_dk')][i % 3]
        img.set(x, y, c[0]); img.set(x + 1, y, c[1]); img.set(x + 2, y, c[1])
        img.set(x, y + 1, c[1]); img.set(x + 1, y + 1, c[1]); img.set(x + 2, y + 1, c[2])
    return img


def brick_oven_frames():
    base = Img(32, 32)
    for y in range(0, 28):
        for x in range(1, 31):
            dome = in_ell(x, y, 16, 16, 14.5, 14.5) if y < 16 else True
            if not dome:
                continue
            course = y // 3
            off = 0 if course % 2 else 3
            if y % 3 == 0 or (x + off) % 6 == 0:
                c = 'ck_line'
            else:
                t = x / 31.0
                c = 'br_hi' if t < 0.3 else 'br_base' if t < 0.75 else 'br_dk'
                if (hash2(x // 6, course, 3) & 3) == 0:
                    c = 'br_base' if c == 'br_hi' else 'br_dk' if c == 'br_base' else c
            base.set(x, y, c)
    # chimney
    for y in range(0, 5):
        for x in range(13, 19):
            base.set(x, y, 'br_base' if x < 17 else 'br_dk')
    base = outline(base, 'i_out')
    for x in range(12, 20):
        base.set(x, 0, 'i_out')
    # stone sill + base
    for y in range(24, 32):
        for x in range(1, 31):
            if y == 24 or y == 31 or x in (1, 30):
                c = 'i_out'
            elif y == 25:
                c = 'ck_hi'
            elif y == 26:
                c = 'ck_base'
            elif y == 27:
                c = 'i_out'
            else:
                c = 'ck_line' if x < 22 else 'ck_dk'
                if y == 30:
                    c = 'ck_dk'
            base.set(x, y, c)
    # mouth (arch) and logs
    mouth = set()
    for y in range(11, 24):
        for x in range(8, 24):
            if y >= 17 or in_ell(x, y, 16, 17, 7.5, 6.5):
                mouth.add((x, y))
    frames = []
    for f in range(4):
        img = base.copy()
        for (x, y) in mouth:
            img.set(x, y, 'br_dk' if y < 15 else 'i_out')
        for (x, y) in mouth:
            if (x - 1, y) not in mouth or (x, y - 1) not in mouth:
                img.set(x, y, 'i_out')
        fl = flames(32, 32, [(16, 23, 9, 4.0, 0.0), (12.5, 23, 6, 2.6, 2.0), (19.5, 23, 6.5, 2.6, 4.0)],
                    f * math.pi / 2, cols=FIRE_COLS)
        for (x, y) in mouth:
            if fl.p[y][x] and img.p[y][x] != 'i_out' or fl.p[y][x] and y > 14 and (x - 1, y) in mouth:
                img.set(x, y, fl.p[y][x])
        for x in range(10, 23):
            img.set(x, 22, 'bb_base' if x % 3 else 'bb_dk')
            img.set(x, 23, 'bb_dk')
        frames.append(img)
    return frames


# ------------------------------------------------------------------ music & fire

def piano():
    """Upright piano, built row by row: lid, carved upper panel with sheet
    music, keyboard, lower panel with brass trim, pedals."""
    R = []
    R += ['.' * 32] * 2
    R.append('.' + 'O' * 30 + '.')
    R.append('.O' + '6' * 28 + 'O.')
    R.append('.O' + '7' * 28 + 'O.')
    R.append('.' + 'O' * 30 + '.')
    for y in range(6, 13):
        row = list('.O' + '7' * 28 + 'O.')
        for (x0, x1) in ((3, 8), (23, 28)):
            for x in range(x0, x1 + 1):
                if y in (6, 12) or x in (x0, x1):
                    row[x] = 'O'
                else:
                    row[x] = '6' if x == x0 + 1 or y == 7 else '7'
        for x in range(10, 22):
            if y in (6, 12) or x in (10, 21):
                row[x] = 'O'
            else:
                row[x] = 'Z'
                if y in (8, 10) and x % 2 == 0:
                    row[x] = 'l'
                if (x, y) in ((13, 8), (16, 10), (19, 8), (14, 9), (17, 9)):
                    row[x] = 'O'
        R.append(''.join(row))
    R.append('.O' + '7' * 28 + 'O.')
    R.append('.' + 'O' * 30 + '.')
    R.append('O' + '6' * 30 + 'O')
    R.append('O' * 32)
    black = set()
    for k in range(15):
        if k % 7 in (0, 1, 3, 4, 5) and k < 14:
            xb = 1 + 2 * (k + 1)
            black.update((xb - 1, xb))
    for y in (17, 18, 19, 20):
        row = ['O'] + ['Z'] * 30 + ['O']
        for x in range(1, 31):
            if y in (17, 18) and x in black:
                row[x] = 'O'
            elif y == 19 and (x - 1) % 2 == 1:
                row[x] = 'l'
            elif y == 20:
                row[x] = 'L'
        R.append(''.join(row))
    R.append('O' * 32)
    R.append('.O6' + '7' * 27 + 'O.')
    for y in range(23, 28):
        row = list('.O7' + '7' * 27 + 'O.')
        for x in range(4, 28):
            if y in (23, 27) or x in (4, 27):
                row[x] = 'O'
            elif y == 25 and 13 <= x <= 18:
                row[x] = 'Y'
            elif y == 24:
                row[x] = '6'
        R.append(''.join(row))
    R.append('.O' + '7' * 28 + 'O.')
    R.append('.' + 'O' * 30 + '.')
    R.append('.O7O' + '.' * 9 + 'OYOYO' + '.' * 10 + 'O7O.')
    R.append('.OOO' + '.' * 9 + 'OOOOO' + '.' * 10 + 'OOO.')
    return SG('\n'.join(R), dict(L2, **{'6': 'bb_base', '7': 'bb_dk'}), w=32)


PIANO = piano()


def fireplace_frames():
    base = I2('''
    ................................
    ....OOOOOOOOOOOOOOOOOOOOOOOO....
    ....OCCCCCCCCCCCCCCCCCCCCCLO....
    ....OCccccccccccccccccccccLO....
    ....OCcccccccOOOOOcccccccLLO....
    ....OCccccccOYYYYDOccccccLLO....
    ....OCcccccOYYoYYYDOcccccLLO....
    ....OCccccOYYoooYYYDOccccLLO....
    ....OCcccccOYYoYYYDOcccccLLO....
    ....OCccccccOYYYYDOccccccLLO....
    ....OCcccccccOOOOOcccccccLLO....
    ....OCcccccccccccccccccccLLO....
    OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
    OBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBO
    OKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKO
    OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
    .OCCCCCCOOOOOOOOOOOOOOOOCCCCCLO.
    .OCcccclO33333333333333OccccLLO.
    .OCcccclO33333333333333OccccLLO.
    .OCccccO3333333333333333OcccLLO.
    .OClllcO3333333333333333OlllLLO.
    .OCccccO3333333333333333OcccLLO.
    .OCccccO3333333333333333OcccLLO.
    .OCccccO3333333333333333OcccLLO.
    .OClllcO3333333333333333OlllLLO.
    .OCccccO3333333333333333OcccLLO.
    .OCccccO3333333333333333OcccLLO.
    .OCccccOOOOOOOOOOOOOOOOOOcccLLO.
    OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
    OCCCCCCCCCCCCCCCCCCCCCCCCCCCCCLO
    OLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLO
    OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
    ''', w=32)
    base = base.replace({'gd_base': 'if_org'})
    # candles on the mantel
    for cx in (6, 25):
        base.set(cx, 9, 'gd_hi'); base.set(cx, 10, 'white'); base.set(cx, 11, 'white')
    frames = []
    inside = [(x, y) for y in range(17, 27) for x in range(8, 24) if base.get(x, y) == 'br_dk']
    for f in range(4):
        img = base.copy()
        fl = flames(32, 32, [(16, 26, 9.5, 4.2, 0.0), (12, 26, 7, 2.8, 2.0), (20, 26, 7.5, 2.8, 4.0)],
                    f * math.pi / 2, cols=FIRE_COLS)
        for (x, y) in inside:
            if fl.p[y][x]:
                img.set(x, y, fl.p[y][x])
        logs = G('''
        ..OOOOOOOOOOOO..
        .OBBBBBBBBBBBKO.
        OOOOOOOOOOOOOOOO
        OBBBBKOOOBBBBBKO
        ''', L2)
        img.paste(logs, 8, 23)
        frames.append(img)
    return frames


def lantern_rack_frames():
    """Open wooden rack (three shelves) of small heartglass lanterns whose
    glow drifts from lantern to lantern."""
    rack = Img(32, 32)
    for y in range(0, 30):
        for x in range(32):
            if y in (0, 29) or x in (0, 31):
                c = 'i_out'
            elif y in (1, 2):
                c = 'bb_base' if y == 1 else 'bb_dk'
            elif x in (1, 30):
                c = 'bb_base' if x == 1 else 'bb_dk'
            elif (y - 3) % 9 == 0:
                c = 'i_out'
            elif (y - 3) % 9 == 8:
                c = 'bb_base'
            else:
                c = 'bb_dk'
            rack.p[y][x] = c
    lantern = '''
    ..O..
    .OOO.
    OcYcO
    OYwYO
    OcYcO
    .OOO.
    '''
    glows = [('hg_hi', 'gd_hi', 'white'), ('gd_hi', 'if_org', 'white'), ('hg_hi', 'white', 'gd_hi')]
    frames = []
    for f in range(3):
        img = rack.copy()
        k = 0
        for sy in (3, 12, 21):
            for lx in (3, 10, 17, 24):
                g = glows[(k + f) % 3]
                img.paste(G(lantern, {'.': None, 'O': 'i_out', 'c': g[0], 'Y': g[1], 'w': g[2]}),
                          lx, sy + 2)
                k += 1
        frames.append(img)
    return frames


# ------------------------------------------------------------------ study & lab

def globe():
    img = Img(16, 16)
    for y in range(16):
        for x in range(16):
            if in_ell(x, y, 7.5, 6.5, 5.2, 5.2):
                d = ell_d(x, y, 5.8, 4.8, 5.2, 5.2)
                c = 'bl_hi' if d < 0.45 else 'bl_base' if d < 1.05 else 'bl_dk'
                land = ((x - 3) * 3 + (y - 2) * 5) % 11 < 4 and 3 <= x <= 11 and 3 <= y <= 10
                if land:
                    c = 'lf_hi' if d < 0.6 else 'lf_base'
                img.set(x, y, c)
    img = outline(img, 'i_out')
    for y in range(1, 13):
        x = int(round(7.5 + 6.2 * math.sqrt(max(0.0, 1 - ((y + 0.5 - 6.5) / 6.2) ** 2))))
        img.set(x, y, 'gd_base')
    stand = I2('''
    .......OO.......
    ......OYDO......
    .....OOYDOO.....
    ...OOYYYDDDOO...
    ...OOOOOOOOOO...
    ''')
    img.paste(stand, 0, 11)
    return img


def telescope_in():
    from decor_outdoor import TELESCOPE
    return TELESCOPE.replace({'p_yel': 'gd_hi', 'wd_lt': 'gd_base', 'wd_base': 'bb_base',
                              'wd_dk': 'bb_dk', 'st_dk': 'bb_dk', 'st_mid': 'bb_base',
                              'w_lt': 'bl_hi', 'w_base': 'bl_base', 'b_out': 'i_out'})


CHALKBOARD = SG('''
................................
................................
................................
.OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
.OAAAAAAAAAAAAAAAAAAAAAAAAAAAAO.
.OA44444444444444444444444444KO.
.OA4Z4444Z44444ZZZ444ZZ4Z4ZZ4KO.
.OA4Z4ll4Z4444Z444Z4444444444KO.
.OA4Zl44lZ44l4Z4Z4Z4l4ZZZ4ZZ4KO.
.OA4Z4ll4Z4444Z444Z4444444444KO.
.OA4Z4444Z44444ZZZ444Z4ZZ4Z44KO.
.OA4444444444444444444444444KKO.
.OKKKKKKKKKKKKKKKKKKKKKKKKKKKKO.
.OAAAZZAAAAPPAAAAAAAAAAAAAAAAKO.
.OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
................................
''', dict(L2, l='gl_hi', P='rd_hi', **{'4': 'sc_dk'}), w=32)

def map_poster():
    """Map of the Vale on a pinned sheet: Mirror Lake (left), Bramblewood
    (right), Whisper Meadow and the Stormstone (top), Maple Village and its
    roads in the middle."""
    img = Img(32, 16)
    for y in range(4, 15):
        for x in range(1, 31):
            if y in (4, 14) or x in (1, 30):
                c = 'i_out'
            elif y == 13 or x in (2, 29) or y == 5:
                c = 'white'
            else:
                c = 'lf_hi'
                if in_ell(x, y, 6.5, 9.5, 4.5, 3.2):
                    c = 'bl_hi' if not in_ell(x, y, 6.5, 9.8, 3.4, 2.2) else 'bl_base'
                elif in_ell(x, y, 25.5, 9.5, 4.0, 3.4):
                    c = 'lf_dk' if (x + y) % 3 else 'lf_base'
                elif y == 9 and 10 <= x <= 22 or x == 16 and 6 <= y <= 12:
                    c = 'gd_base'
            img.set(x, y, c)
    for (x, y, c) in ((15, 9, 'if_org'), (17, 9, 'if_org'), (16, 10, 'if_org'), (16, 9, 'gd_hi'),
                      (16, 6, 'hg_dk'), (15, 6, 'hg_dk'), (16, 7, 'hg_dk'),
                      (11, 7, 'white'), (20, 7, 'white'), (13, 11, 'white'), (21, 11, 'white')):
        img.set(x, y, c)
    for (x, y) in ((2, 4), (29, 4)):
        img.set(x, y, 'gd_hi')
    return img


MAP_POSTER = map_poster()

CALENDAR = I2('''
................
................
................
.......OO.......
...OOOOOOOOOO...
...ORRRRRRRRO...
...ORrRRRRrRO...
...OZZZZZZZZO...
...OZlZlZlZlO...
...OZZZZZZZZO...
...OZlZRRZlZO...
...OZZRZlRZZO...
...OZlZRRZlCO...
...OCCCCCCCLO...
...OOOOOOOOOO...
................
''')

PENNANT = I2('''
................
................
................
................
.OO..........OO.
OAOOOOOOOOOOOOAO
.OSSSSSSSSSSSzO.
..OSSSSZSSSSzO..
..OSSSZZsSSSzO..
...OSSZssSSzO...
...OSSSZZSSzO...
....OSSSSSzO....
.....OSSSzO.....
......OSzO......
.......OO.......
................
''')

KIN_PLUSH = SG('''
................
................
...OO......OO...
..OoTO....OToO..
..OoPTO..OTPoO..
..OoooOOOOoooO..
.OooooooooooooO.
.OooOooooooOotO.
.OoWWWWOOWWWWtO.
..OWWWkWWkWWtO..
...OOWWWWWWOO.OO
...OooWWWWooOOYO
..OoooWWWWoooOZO
..OooooooootOOYO
..OoWWOOOOWWoOO.
...OOO....OOO...
''', dict(L2, o='pt_base', t='pt_dk', T='rd_dk', P='rd_hi', W='fl_hi', k='rd_hi',
                  Y='gd_hi', Z='fl_hi'))

def small_rug():
    img = Img(32, 16)
    for y in range(16):
        for x in range(32):
            if in_ell(x, y, 16, 8, 15.2, 6.8):
                d = ell_d(x, y, 16, 8, 15.2, 6.8)
                rings = ['rd_base', 'gd_hi', 'bl_base', 'rd_hi', 'gd_base', 'rd_dk']
                k = min(5, int(d * 6.2))
                c = rings[k]
                if (x + y) % 4 == 0 and k in (1, 3):
                    c = 'white'
                img.set(x, y, c)
    return outline(img, 'i_out')


def aquarium_frames():
    frames = []
    for f in range(3):
        img = Img(32, 16)
        for y in range(16):
            for x in range(32):
                c = None
                if x in (1, 30) and y <= 11 or y in (0, 2, 11) and 1 <= x <= 30:
                    c = 'i_out'
                elif y == 1 and 1 < x < 30:
                    c = 'mt_hi' if x < 26 else 'mt_base'
                elif 3 <= y <= 10 and 1 < x < 30:
                    c = 'gl_base'
                    if x == 2 or (x + y) % 11 == 0 and y < 7:
                        c = 'gl_hi'
                    if y == 3:
                        c = 'gl_hi'
                    if x == 29:
                        c = 'gl_dk'
                    if y == 10:
                        c = 'bb_lt' if x % 3 else 'bb_base'
                elif 12 <= y <= 13 and 1 <= x <= 30:
                    c = 'i_out' if x in (1, 30) else ('bb_lt' if y == 12 else 'bb_dk')
                elif y == 14 and (1 <= x <= 3 or 28 <= x <= 30):
                    c = 'i_out'
                elif y == 14 and 1 <= x <= 30:
                    c = 'i_out'
                if c:
                    img.set(x, y, c)
        for (px, h) in ((5, 4), (8, 3), (22, 5), (25, 3)):
            for y in range(10 - h, 10):
                img.set(px + ((y + f) % 2 if y < 8 else 0), y, 'sc_base' if y % 2 else 'sc_hi')
        fx = [9 + f * 3, 20 - f * 2]
        for i, x in enumerate(fx):
            y = 5 + i * 2
            d = 1 if i == 0 else -1
            img.set(x, y, 'rd_hi'); img.set(x + d, y, 'rd_hi'); img.set(x - d, y, 'white')
            img.set(x + 2 * d, y, 'i_out')
        for (bx, by) in ((14, 8), (15, 6), (14, 4)):
            yy = by - f
            if yy >= 3:
                img.set(bx, yy, 'white')
        frames.append(img)
    return frames


def specimen_shelf():
    img = bookshelf(16, 32, seed=7)
    for y in range(32):
        for x in range(16):
            if img.p[y][x] in ('rd_base', 'rd_hi', 'bl_base', 'bl_hi', 'lf_base', 'lf_hi',
                               'gd_base', 'gd_hi'):
                img.p[y][x] = 'bb_dk'
    jar = '''
    OOOO
    OaMO
    OccO
    OcdO
    OZZO
    OOOO
    '''
    fills = [('sc_base', 'sc_dk'), ('rd_hi', 'bb_base'), ('gl_base', 'gl_dk'),
             ('sc_hi', 'sc_base'), ('gl_hi', 'gl_base'), ('sc_base', 'gl_dk')]
    k = 0
    for sy in (4, 13, 22):
        for jx in (3, 8):
            if sy == 22 and jx == 8:
                continue
            c1, c2 = fills[k % len(fills)]
            k += 1
            img.paste(G(jar, {'.': None, 'O': 'i_out', 'a': 'gl_hi', 'M': 'mt_base',
                              'c': c1, 'd': c2, 'Z': 'white'}), jx, sy + 2)
    # a rolled chart on the bottom shelf
    for x in range(9, 13):
        img.set(x, 26, 'white'); img.set(x, 27, 'mt_base')
    return img


MICROSCOPE = I2('''
................
.......OO.......
......OMNO......
......OENO......
......OOEO......
.....OMNOO......
....OMNNEO......
....OMOONO......
...OOOEEOOO.....
...OMMMMMNO.....
...OOOONOOO.....
..OOOOMNEOOOOO..
.OAAAAAAAAAAAKO.
.OKKKKKKKKKKKKO.
.OKO........OKO.
.OOO........OOO.
''')


def display_case_frames():
    base = I2('''
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    .OUUUUUUUUUUUUUUUUUUUUUUUUUUUUO.
    .OUuuuuuuuuuuuuuuuuuuuuuuuuuuuO.
    .OUuuuuuuuuuuuuuuuuuuuuuuuuuuuO.
    .OUuuuuuuuuuuuuuuuuuuuuuuuuuuuO.
    .OUuuuuuuuuuuuuuuuuuuuuuuuuuuuO.
    .OUuuuuuuuuuuuuuuuuuuuuuuuuuuuO.
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    .OAAAAAAAAAAAAAAAAAAAAAAAAAAAKO.
    .OBBBBBBBBBBBBBBBBBBBBBBBBBBBKO.
    .OKKKKKKKKKKKKKKKKKKKKKKKKKKKKO.
    .OABBBBBBBBBBYYBBBBBBBBBBBBBBKO.
    .OKKKKKKKKKKKKKKKKKKKKKKKKKKKKO.
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    .OKO........................OKO.
    .OOO........................OOO.
    ''', w=32)
    shard = '''
    ..O..
    .OhO.
    OhbdO
    OhbdO
    .OdO.
    '''
    kinds = [('lf_hi', 'lf_base', 'lf_dk'), ('gd_hi', 'gd_base', 'if_org'),
             ('hg_hi', 'hg_base', 'hg_dk'), ('white', 'bl_hi', 'bl_hi')]
    for i, (h, b, d) in enumerate(kinds):
        base.paste(G(shard, {'.': None, 'O': 'i_out', 'h': h, 'b': b, 'd': d}), 5 + i * 6, 2)
    # glass glints
    for (x, y) in ((3, 2), (4, 3), (27, 2), (28, 3)):
        base.set(x, y, 'white')
    frames = []
    for f in range(4):
        img = base.copy()
        sx = 7 + f * 6
        img.set(sx, 2, 'white')
        img.set(sx + 1, 1, 'white')
        frames.append(img)
    return frames


TELEGRAPH = I2('''
................
................
.OOOO......OOO..
OMNNEO....OZZCO.
OMNEEO....OZZCO.
.OOOO.....OOOO..
OOOOOOOOOOOOOOOO
OAAAAAAAAAAAAAKO
OAOOOOOOOOAAAAKO
OAOYYYYYDOAZZZKO
OAOOODOOOOAAAAKO
OKKKKKKKKKKKKKKO
OOOOOOOOOOOOOOOO
OKO..........OKO
OKO..........OKO
OOO..........OOO
''')


def pc_frames():
    """Lantern Shelf terminal: a twin crystal glowing in a glass dome on a
    steel cradle with a dial, over a desk with a telegraph key."""
    base = I2('''
    ................
    ......OOOO......
    .....OaaabO.....
    ....OaaSabdO....
    ....OaSSsbdO....
    ....ObSsszdO....
    ....ObbszbdO....
    ...OOOOOOOOOO...
    ...OMMMMMMMNO...
    ...ONNNNNNNEO...
    .OOOOOOOOOOOOOO.
    .OAAAAAAAAAAAKO.
    .OAOOOOOOOOOAKO.
    .OAOZZOZMOROAKO.
    .OAOZOZOMOSOAKO.
    .OAOOOOOOOOOAKO.
    OOOOOOOOOOOOOOOO
    OAAAAAAAAAAAAAKO
    OABBOOOBBBBZZBKO
    OABOMNNOBBZZMBKO
    OABOOOOMOBBMBBKO
    OABBBBOOOBBBBBKO
    OKKKKKKKKKKKKKKO
    OOOOOOOOOOOOOOOO
    OAOAAAAAAAAAAOKO
    OAOBBBBMMBBBBOKO
    OAOBBBBBBBBBBOKO
    OKOOOOOOOOOOOOKO
    OKO..........OKO
    OKO..........OKO
    OOO..........OOO
    ................
    ''')
    frames = []
    for (a, b) in (('sc_hi', 'gl_hi'), ('white', 'sc_hi'), ('sc_hi', 'gl_hi')):
        img = base.copy()
        img.set(7, 4, a)
        img.set(6, 3, b)
        frames.append(img)
    return frames


def heal_frames():
    """Hearth resonator: warm stone and brick around a round heartglass
    window with a steady fire; lanterns rest in cradles on the ledge."""
    base = SG('''
    ................................
    ...OOOOOOOOOOOOOOOOOOOOOOOOOO...
    ..OWWWWWWWWWWWWWWWWWWWWWWWWWWO..
    .OWwwwwwwwwwwwwwwwwwwwwwwwwwwqO.
    .OWww1111OOOOOOOOOOOO1111wwwqqO.
    .OWw1222OO8888888888OO2223wwqqO.
    .OWw122O88999999999988O223wwqqO.
    .OWw12O8990333333330998O23wwqqO.
    .OWw12O8930333333330398O23wwqqO.
    .OWw12O8930333333330398O23wwqqO.
    .OWw12O8990333333330998O23wwqqO.
    .OWw122O88999999999988O223wwqqO.
    .OWw1222OO8888888888OO2223wwqqO.
    .OWww2333OOOOOOOOOOOO3333wwwqqO.
    .OWwwwwwwwwwwwwwwwwwwwwwwwwwqqO.
    .OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.
    OYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYO
    ODDDDDDDDDDDDDDDDDDDDDDDDDDDDDDO
    OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
    OWwOOOOOwwOOOOOwwOOOOOwwOOOOOwqO
    OWwODYDOwwODYDOwwODYDOwwODYDOwqO
    OWwOOOOOwwOOOOOwwOOOOOwwOOOOOwqO
    OWwwwwwwwwwwwwwwwwwwwwwwwwwwwwqO
    OW1111111111111111111111111111qO
    OW2222322222232222232222222322qO
    OW2322222322222232222222322222qO
    OW3333333333333333333333333333qO
    OqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqO
    OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
    .OqqO....................OqqO...
    .OOOO....................OOOO...
    ................................
    ''', dict(L2, W='ck_hi', w='ck_base', q='ck_dk', D='br_hi', **{'9': 'white', '0': 'br_dk'}), w=32)
    window = [(x, y) for y in range(6, 12) for x in range(10, 22) if base.get(x, y) == 'br_dk']
    frames = []
    for f in range(3):
        img = base.copy()
        fl = flames(32, 32, [(16, 12.5, 7, 3.4, 0.0), (13, 12.5, 4.5, 2.0, 2.0),
                             (19, 12.5, 5, 2.0, 4.0)], f * 2.1, cols=FIRE_COLS)
        for (x, y) in window:
            if fl.p[y][x]:
                img.set(x, y, fl.p[y][x])
        # lanterns resting in the cradles glow in turn
        for i, lx in enumerate((4, 11, 18, 25)):
            c = 'hg_hi' if (i + f) % 3 else 'white'
            img.set(lx, 19, c)
            img.set(lx - 1, 19, 'gd_hi')
            img.set(lx + 1, 19, 'gd_hi')
        frames.append(img)
    return frames


# ------------------------------------------------------------------ catalog

# Free banks, one colour family each (banks 0, 1, 3 are fixed: 0 = wood +
# wallpaper + floor + window glass, 1 = ceramic + paper + gold + wood,
# 3 = floor wood + red + gold + leaf + terracotta). Every 8x8 tile of a piece
# is drawn from one of these families.
INDOOR_DECOR_BANKS = {
    # textiles & books: beds, rugs, cushions, toy box, mirror, globe
    2: ['i_out', 'bb_lt', 'bb_base', 'bb_dk', 'white', 'gd_hi', 'gd_base', 'rd_hi', 'rd_base',
        'rd_dk', 'bl_hi', 'bl_base', 'bl_dk', 'lf_hi', 'lf_base'],
    # metal, glass & science: TV, stove, lab, terminal, aquarium, chalkboard
    4: ['i_out', 'bb_lt', 'bb_base', 'bb_dk', 'white', 'mt_hi', 'mt_base', 'mt_dk', 'gl_hi',
        'gl_base', 'gl_dk', 'sc_hi', 'sc_base', 'sc_dk', 'rd_hi'],
    # fire, brick & stone: fireplace, oven, hearth resonator, lanterns
    5: ['i_out', 'bb_base', 'bb_dk', 'white', 'gd_hi', 'if_org', 'rd_base', 'br_hi', 'br_base',
        'br_dk', 'ck_hi', 'ck_base', 'ck_line', 'ck_dk', 'hg_hi'],
    # flowers, crystals & maps
    6: ['i_out', 'white', 'gd_hi', 'gd_base', 'lf_hi', 'lf_base', 'lf_dk', 'pk_hi', 'pk_base',
        'hg_hi', 'hg_base', 'hg_dk', 'bl_hi', 'bl_base', 'if_org'],
    # shop goods: metal shelves, ceramic, red/blue/gold labels
    7: ['i_out', 'mt_hi', 'mt_base', 'mt_dk', 'ck_hi', 'ck_base', 'ck_line', 'ck_dk', 'rd_hi',
        'rd_base', 'bl_hi', 'bl_base', 'gd_hi', 'gd_base', 'white'],
}

I = ['interior']

INDOOR_DECOR = [
    # --- existing kinds (names kept) --------------------------------------
    Decor('CHAIR', I, CHAIR, doc='wooden chair facing down (place above a table)'),
    Decor('TV', I, no_floor_shadow(I_TV), doc='small TV on a stand'),
    Decor('TABLE', I, TABLE, doc='wooden table 2x2'),
    Decor('BED', I, BED, doc='single bed, pillow at the top'),
    Decor('BOOKSHELF', I, BOOKSHELF, top='XX/..',
          doc='bookshelf 2x2; upper row stands in front of the lower wall'),
    Decor('PLANT', I, no_floor_shadow(pad_top(I_PLANT, 32)), top='X/.',
          doc='tall potted plant 1x2; leaves over people'),
    Decor('PC', I, frames=pc_frames(), period=16, top='X/.',
          doc='LANTERN SHELF terminal: twin crystal in a glass dome over a desk with a '
              'telegraph key'),
    Decor('HEAL_MACHINE', I, frames=heal_frames(), period=10,
          doc='hearth resonator (heals): heartglass window with fire, lantern cradles; '
              'against the wall'),
    Decor('SHOP_SHELF', I, no_floor_shadow(i_shop_shelf()), doc='stocked shop shelves, against the wall'),
    Decor('LAB_MACHINE', I, no_floor_shadow(I_LAB).replace({'pk_hi': 'sc_hi'}), doc='research machine, against the wall'),
    Decor('STOVE', I, no_floor_shadow(I_STOVE), doc='stove and oven, against the wall'),
    # --- seating & tables --------------------------------------------------
    Decor('CHAIR_UP', I, CHAIR_UP, doc='chair seen from behind (place below a table)'),
    Decor('CHAIR_SIDE', I, CHAIR_SIDE, doc='chair facing right (mirror for facing left)'),
    Decor('STOOL', I, STOOL, doc='round wooden stool'),
    Decor('TABLE_ROUND', I, round_table(), doc='round table with a lace doily 2x2'),
    Decor('LONG_TABLE', I, LONG_TABLE, doc='long dining table 3x2 with a runner'),
    Decor('DESK', I, DESK, doc='writing desk with papers, quill and inkwell'),
    Decor('TEA_SET', I, tea_set(), doc='side table with a teapot and cups'),
    Decor('CUSHION', I, CUSHION, solid='.', doc='floor cushion (walkable)'),
    Decor('SMALL_RUG', I, small_rug(), solid='..', doc='oval braided rug (walkable)'),
    # --- beds & storage ---------------------------------------------------------
    Decor('DOUBLE_BED', I, double_bed(), doc='double bed with a patchwork quilt'),
    Decor('KIN_BASKET', I, KIN_BASKET, doc='wicker basket bed for a kin'),
    Decor('BOOKSHELF_SMALL', I, BOOKSHELF_SMALL, top='X/.', doc='narrow bookshelf 1x2'),
    Decor('WARDROBE', I, WARDROBE, top='X/.', doc='tall wardrobe 1x2'),
    Decor('DRESSER', I, DRESSER, doc='chest of drawers with a little vase'),
    Decor('BARREL_IN', I, barrel_in(), doc='wooden barrel (indoor palette)'),
    Decor('SACKS_IN', I, SACKS_IN, doc='flour and grain sacks'),
    Decor('TOY_BOX', I, TOY_BOX, doc='red toy chest with a star'),
    Decor('ICEBOX', I, icebox(), top='X/.', doc='wooden icebox 1x2'),
    Decor('SINK_COUNTER', I, sink_counter(), top='X/.',
          doc='kitchen sink with a tiled splashback 1x2 (pairs with STOVE)'),
    Decor('COAT_RACK', I, COAT_RACK, top='X/.', doc='coat rack with a red coat and a teal scarf'),
    Decor('MIRROR', I, mirror(), top='X/.', doc='standing oval mirror'),
    # --- plants & ornaments ------------------------------------------------
    Decor('SMALL_PLANT', I, SMALL_PLANT, doc='small potted plant'),
    Decor('CACTUS', I, CACTUS, doc='potted cactus with a pink flower'),
    Decor('VASE', I, VASE, doc='blue and white vase'),
    Decor('FLOWER_VASE', I, FLOWER_VASE, doc='vase of flowers'),
    Decor('KIN_PLUSH', I, KIN_PLUSH, doc='plush FLARIX with its ember tail'),
    Decor('GLOBE', I, globe(), doc='globe on a brass stand'),
    # --- clocks, lamps, fire ------------------------------------------------
    Decor('GRANDFATHER_CLOCK', I, frames=clock_frames(), period=20, top='X/.',
          doc='grandfather clock 1x2, pendulum swings'),
    Decor('FLOOR_LAMP', I, FLOOR_LAMP, top='X/.', doc='floor lamp; shade over people'),
    Decor('FIREPLACE', I, frames=fireplace_frames(), period=8,
          doc='stone fireplace with mantel and a burning fire; upper row over the lower wall'),
    Decor('BRICK_OVEN', I, frames=brick_oven_frames(), period=8,
          doc='bakery brick oven, fire glowing in the mouth; upper row over the lower wall'),
    Decor('LANTERN_RACK', I, frames=lantern_rack_frames(), period=14,
          doc='rack of softly glowing heartglass lanterns (hearth hall); against the wall'),
    Decor('PIANO', I, PIANO, doc='upright piano; upper row over the lower wall'),
    # --- bakery & kitchen --------------------------------------------------
    Decor('BREAD_DISPLAY', I, bread_display(), doc='bakery counter: bread baskets on top, '
          'pastries behind glass'),
    # --- study & lab ---------------------------------------------------------
    Decor('TELESCOPE_IN', I, telescope_in(), top='X/.', doc='brass telescope on a tripod'),
    Decor('SPECIMEN_SHELF', I, specimen_shelf(), top='X/.', doc='shelf of specimen jars 1x2'),
    Decor('MICROSCOPE', I, MICROSCOPE, doc='microscope on a small lab table'),
    Decor('DISPLAY_CASE', I, frames=display_case_frames(), period=12,
          doc='glass case of shards (BLOOM, SPARK, DUSK, FROST) that twinkle'),
    Decor('AQUARIUM', I, frames=aquarium_frames(), period=12,
          doc='aquarium on a stand: fish and bubbles'),
    Decor('TELEGRAPH', I, TELEGRAPH, doc='telegraph key and sounder on a small desk'),
    # --- wall hangings (upper wall row) ------------------------------------
    Decor('CHALKBOARD', I, CHALKBOARD, doc='wall chalkboard: two mirrors, a standing wave and '
          'a kernel (hang on WALL_TOP)'),
    Decor('MAP_POSTER', I, MAP_POSTER, doc='map of the Vale (hang on WALL_TOP)'),
    Decor('CALENDAR', I, CALENDAR, doc='wall calendar (hang on WALL_TOP)'),
    Decor('PENNANT', I, PENNANT, doc='teal pennant with the hearth flame (hang on WALL_TOP)'),
]
