#!/usr/bin/env python3
"""Generate src/gfx_field.h: overworld graphics in the style of GBA-era
creature-collecting games (town + interior tilesets, overworld people).

Everything is authored here, in Python 3 standard library only:
  * procedural textures (grass, sand, water, clay) sampled on a 16px grid so
    neighbouring metatiles line up exactly,
  * hand-authored pixel grids for structured objects (houses, props,
    furniture, characters),
  * an encoder that cuts images into 8x8 4bpp tiles, picks a palette bank
    per tile, and de-duplicates tiles including flipped variants.

Run from anywhere:

    python3 tools/gen_field_gfx.py [--preview DIR]

With --preview, PNG previews (rendered back from the encoded data, so they
show exactly what the GBA will show) are written to DIR.
"""

import math
import os
import struct
import sys
import zlib

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tiles2'))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_H = os.path.join(ROOT, 'src', 'gfx_field.h')


# =====================================================================
# Colors (8-bit RGB, quantised to RGB15 on output)
# =====================================================================

C = {
    # --- short grass / tall grass ---------------------------------
    'g_hi':   (176, 232, 136),
    'g_lt':   (148, 218, 112),
    'g_base': (120, 200, 96),
    'g_mid':  (88, 168, 80),
    'g_dk':   (64, 136, 72),
    'g_dkr':  (40, 100, 64),
    # --- sandy path ------------------------------------------------
    's_hi':   (248, 232, 184),
    's_base': (232, 208, 144),
    's_mid':  (208, 176, 112),
    's_dk':   (168, 136, 88),
    # --- flowers ------------------------------------------------------
    'white':  (248, 248, 248),
    'f_yel':  (248, 216, 56),
    'f_yeld': (216, 144, 32),
    'f_red':  (240, 72, 64),
    'f_redd': (168, 40, 56),
    # --- water / shore / court ---------------------------------------
    'w_hi':   (232, 248, 248),
    'w_lt':   (144, 208, 248),
    'w_base': (96, 168, 240),
    'w_mid':  (72, 136, 224),
    'w_dk':   (56, 104, 192),
    'r_hi':   (240, 232, 200),
    'r_base': (208, 196, 160),
    'r_dk':   (152, 140, 112),
    'c_lt':   (232, 196, 144),
    'c_base': (216, 172, 120),
    'c_dk':   (184, 140, 96),
    # --- trees -------------------------------------------------------
    't_hi':   (128, 200, 96),
    't_lt':   (88, 168, 80),
    't_base': (56, 136, 72),
    't_mid':  (40, 108, 64),
    't_dk':   (32, 80, 56),
    't_out':  (24, 56, 48),
    'k_lt':   (200, 144, 88),
    'k_base': (152, 96, 56),
    'k_dk':   (96, 60, 40),
    # --- props: stone, wood, metal ----------------------------------
    'st_hi':  (240, 240, 232),
    'st_lt':  (200, 200, 192),
    'st_mid': (160, 160, 152),
    'st_dk':  (112, 112, 112),
    'wd_lt':  (224, 176, 112),
    'wd_base': (184, 128, 72),
    'wd_dk':  (120, 80, 48),
    'p_out':  (64, 48, 48),
    'p_red':  (224, 64, 56),
    'p_yel':  (248, 232, 128),
    # --- buildings ---------------------------------------------------
    'b_out':  (64, 44, 52),
    'rf_hi':  (248, 160, 120),
    'rf_lt':  (232, 112, 80),
    'rf_base': (208, 76, 60),
    'rf_dk':  (168, 52, 52),
    'rf_dkr': (120, 36, 44),
    'rb_hi':  (168, 200, 248),
    'rb_lt':  (120, 160, 232),
    'rb_base': (88, 120, 208),
    'rb_dk':  (64, 88, 168),
    'rb_dkr': (44, 60, 120),
    'rt_hi':  (152, 232, 216),
    'rt_lt':  (96, 204, 192),
    'rt_base': (56, 164, 168),
    'rt_dk':  (40, 124, 136),
    'rt_dkr': (28, 84, 100),
    'wl_hi':  (248, 244, 224),
    'wl_base': (240, 224, 184),
    'wl_dk':  (208, 184, 144),
    'gl_hi':  (216, 240, 248),
    'gl_base': (120, 184, 232),
    'gl_dk':  (72, 120, 192),
    # --- interiors ---------------------------------------------------
    'void':   (0, 0, 0),
    'i_out':  (64, 44, 44),
    'wp_hi':  (248, 244, 224),
    'wp_base': (236, 224, 192),
    'wp_pat': (220, 204, 168),
    'wp_dk':  (184, 160, 124),
    'bb_lt':  (208, 152, 96),
    'bb_base': (168, 108, 64),
    'bb_dk':  (116, 72, 48),
    'fl_hi':  (240, 200, 140),
    'fl_base': (224, 176, 116),
    'fl_mid': (200, 148, 92),
    'fl_dk':  (164, 112, 68),
    'ck_hi':  (248, 248, 240),
    'ck_base': (224, 224, 216),
    'ck_line': (196, 200, 196),
    'ck_dk':  (152, 156, 164),
    'rd_hi':  (240, 116, 100),
    'rd_base': (208, 68, 64),
    'rd_dk':  (144, 40, 52),
    'gd_hi':  (248, 224, 120),
    'gd_base': (216, 164, 64),
    'bl_hi':  (144, 184, 240),
    'bl_base': (88, 128, 216),
    'bl_dk':  (56, 84, 156),
    'lf_hi':  (136, 208, 96),
    'lf_base': (80, 160, 72),
    'lf_dk':  (48, 108, 64),
    'pt_base': (212, 116, 76),
    'pt_dk':  (152, 76, 52),
    'mt_hi':  (228, 232, 236),
    'mt_base': (180, 184, 196),
    'mt_dk':  (120, 124, 144),
    'sc_hi':  (184, 244, 208),
    'sc_base': (72, 184, 152),
    'sc_dk':  (40, 100, 100),
    'pk_hi':  (248, 196, 212),
    'pk_base': (232, 132, 164),
}


from pixelart import (c15, c15_to_rgb, Img, G, tex_fill, hash2, write_png, SETS,
                      scale_rows, Canvas, shade_clumps)

# =====================================================================
# Tile encoder
# =====================================================================

def flip_idx(t, h, v):
    out = []
    for y in range(8):
        sy = 7 - y if v else y
        row = t[sy * 8:sy * 8 + 8]
        out.extend(row[::-1] if h else row)
    return tuple(out)


class TileSet:
    def __init__(self, name, banks, limit=600):
        self.name = name
        self.banks = banks          # list of 8 lists of color names (idx 1..)
        self.limit = limit
        self.tiles = [tuple([0] * 64)]
        self.lookup = {self.tiles[0]: (0, 0, 0)}
        self.opaque = True
        self.palette_colors = None  # optional per-set RGB overrides without remapping tile indices

    def bank_for(self, colors, prefer):
        order = list(prefer) + [b for b in range(len(self.banks)) if b not in prefer]
        for b in order:
            if colors <= set(self.banks[b]):
                return b
        return None

    def indices(self, pix, bank):
        pal = self.banks[bank]
        return tuple(0 if c is None else pal.index(c) + 1 for c in pix)

    def add(self, pix, prefer=(), where='?', share=True, opaque=True):
        colors = set(c for c in pix if c is not None)
        if opaque and None in pix:
            raise ValueError('%s: transparent pixel in opaque tile %s' % (self.name, where))
        if not colors:
            return 0
        b = self.bank_for(colors, prefer)
        if b is None:
            raise ValueError('%s: tile %s colors %s fit no bank' %
                             (self.name, where, sorted(colors)))
        idx = self.indices(pix, b)
        if share:
            for h in (0, 1):
                for v in (0, 1):
                    f = flip_idx(idx, h, v)
                    if f in self.lookup:
                        t, fh, fv = self.lookup[f]
                        return t | ((h ^ fh) << 10) | ((v ^ fv) << 11) | (b << 12)
        t = len(self.tiles)
        self.tiles.append(idx)
        if share:
            self.lookup[idx] = (t, 0, 0)
        return t | (b << 12)

    def add_raw(self, idx):
        """Append an unshared tile given as bank indices."""
        t = len(self.tiles)
        self.tiles.append(tuple(idx))
        return t

    def tile_pix(self, img, x0, y0):
        return [img.get(x0 + x, y0 + y) for y in range(8) for x in range(8)]

    def meta(self, img, x0=0, y0=0, prefer=(), where='?', opaque=True):
        ents = []
        for (dx, dy) in ((0, 0), (8, 0), (0, 8), (8, 8)):
            pix = self.tile_pix(img, x0 + dx, y0 + dy)
            ents.append(self.add(pix, prefer, '%s@%d,%d' % (where, x0 + dx, y0 + dy),
                                 opaque=opaque))
        return ents

    def pal15(self):
        out = []
        for b in range(8):
            row = [0] * 16
            if b < len(self.banks):
                for i, cn in enumerate(self.banks[b]):
                    row[i + 1] = c15(self.palette_colors.get(cn, C[cn]) if self.palette_colors else C[cn])
            out.append(row)
        return out


def pack4(idx):
    words = []
    for y in range(8):
        w = 0
        for x in range(8):
            w |= (idx[y * 8 + x] & 15) << (4 * x)
        words.append(w)
    return words


def check_banks(name, banks):
    for i, b in enumerate(banks):
        if len(b) > 15:
            raise ValueError('%s bank %d has %d colors' % (name, i, len(b)))
        if len(set(b)) != len(b):
            raise ValueError('%s bank %d has duplicate colors' % (name, i))
        for cn in b:
            if cn not in C:
                raise KeyError('%s bank %d: unknown color %s' % (name, i, cn))


# =====================================================================
# TOWN ART
# =====================================================================

from terrain_common import *  # noqa: F401,F403  (grass, trees, autotiles...)
from terrain_common import (GRASS_A, GRASS_B, GRASS_C, TREE_RAMP, tallgrass_layers,
                            flower_frames, STONE, tree_img, bush_img, court_img,
                            court_circle_img, path_quads, water_quads, fill_grass,
                            autotile)

# =====================================================================
# BUILDINGS
# =====================================================================

ROOF_RED = {'1': 'rf_hi', '2': 'rf_lt', '3': 'rf_base', '4': 'rf_dk', '5': 'rf_dkr'}
ROOF_BLUE = {'1': 'rb_hi', '2': 'rb_lt', '3': 'rb_base', '4': 'rb_dk', '5': 'rb_dkr'}
ROOF_TEAL = {'1': 'rt_hi', '2': 'rt_lt', '3': 'rt_base', '4': 'rt_dk', '5': 'rt_dkr'}
RED_TO_BLUE = {ROOF_RED[k]: ROOF_BLUE[k] for k in ROOF_RED}

BL = {'.': None, 'O': 'b_out', 'W': 'wl_hi', 'w': 'wl_base', 'v': 'wl_dk',
      'H': 'st_hi', 'L': 'st_lt', 'M': 'st_mid', 'A': 'wd_lt', 'B': 'wd_base',
      'K': 'wd_dk', 'a': 'gl_hi', 'b': 'gl_base', 'c': 'gl_dk', 'g': 'g_base',
      's': 'g_dk'}


def BG_(text, roof=ROOF_RED):
    return G(text, dict(BL, **roof))


def draw_roof(img, xl0, xr0, y0, y1, inset, R, joint=8):
    """Hip roof seen from the front/top. Slanted sides, shingle courses."""
    H = y1 - y0
    for y in range(y0, y1 + 1):
        k = int(round(inset * (y1 - y) / float(H)))
        xl, xr = xl0 + k, xr0 - k
        for x in range(xl, xr + 1):
            r = y - (y0 + 3)
            if y == y0 or y == y1 or x == xl or x == xr:
                c = 'b_out'
            elif y == y1 - 1:
                c = R['5']
            elif y == y1 - 2:
                c = R['4']
            elif y == y1 - 3:
                c = R['2']
            elif y == y0 + 1:
                c = R['1']
            elif y == y0 + 2:
                c = R['2']
            else:
                n, rr = r // 4, r % 4
                top = n <= 1          # upper courses catch more light
                if rr == 0:
                    c = R['1'] if top else R['2']
                elif rr == 3:
                    c = R['4']
                else:
                    c = R['2'] if (top and rr == 1) else R['3']
                    if (x + 4 * (n % 2)) % joint == 0:
                        c = R['4']
                if x == xl + 1:
                    c = R['1'] if rr != 3 else R['2']
                elif x == xr - 1:
                    c = R['4'] if rr != 3 else R['5']
            img.set(x, y, c)


def draw_clapboard(img, x0, x1, y0, y1):
    for y in range(y0, y1 + 1):
        r = (y - y0) % 5
        for x in range(x0, x1 + 1):
            c = 'wl_base'
            if r == 4:
                c = 'wl_dk'
            elif r == 0:
                c = 'wl_hi'
            img.set(x, y, c)


WINDOW = BG_('''
OOOOOOOOOOOOOO
OHHHHHHHHHHHHO
OHccccHHccccLO
OHcaabHHcbbbLO
OHcabbHHcbbbLO
OHcbbbHHcbabLO
OHHHHHHHHHHHLO
OHcbbbHHcbbbLO
OHcbbbHHcabbLO
OHcbbbHHcbbbLO
OHLLLLLLLLLLLO
OOOOOOOOOOOOOO
''')

FLOWERBOX = G('''
.23.s32.23s32.
s3223s2323s32s
OOOOOOOOOOOOOO
O44444444444vO
.OOOOOOOOOOOO.
''', dict(BL, **ROOF_RED))

DOOR = BG_('''
OOOOOOOOOOOOOO
OAAAAAAAAAAAAO
OAOOOOOOOOOOKO
OAOBBBBBBBBOKO
OAOBKKKKKKBOKO
OAOBKBBBBABOKO
OAOBKBBBBABOKO
OAOBKAAAAABOKO
OAOBBBBBBBBOKO
OAOBBBBBBHBOKO
OAOBBBBBBMBOKO
OAOBKKKKKKBOKO
OAOBKBBBBABOKO
OAOBKBBBBABOKO
OAOBKAAAAABOKO
OAOBBBBBBBBOKO
OAOKKKKKKKKOKO
OOOOOOOOOOOOOO
''')

STEP = BG_('''
OOOOOOOOOOOOOOOO
OHHHHHHHHHHHHHHO
OLLLLLLLLLLLLLLO
OOOOOOOOOOOOOOOO
.OHHHHHHHHHHHHO.
.OLLLLLLLLLLLLO.
.OMMMMMMMMMMMMO.
.OOOOOOOOOOOOOO.
''')

GLASS_DOOR = BG_('''
OOOOOOOOOOOOOOOO
OLLLLLLLLLLLLLLO
OLOOOOOOOOOOOOLO
OLOaabcOOaabcOLO
OLOabbcOOabbcOLO
OLObbbcOObbbcOLO
OLObbacOObbacOLO
OLObabcOObabcOLO
OLOabbcOOabbcOLO
OLObbbcOObbbcOLO
OLObbbcOObbbcOLO
OLOccccOOccccOLO
OLLLLLLLLLLLLLLO
OMMMMMMMMMMMMMMO
''')

# 4x5 pixel font for signs
FONT = {
    'C': ['.###', '#...', '#...', '#...', '.###'],
    'M': ['#..#', '####', '####', '#..#', '#..#'],
    'N': ['#..#', '##.#', '#.##', '#..#', '#..#'],
    'T': ['####', '.##.', '.##.', '.##.', '.##.'],
    'I': ['.##.', '.##.', '.##.', '.##.', '.##.'],
    'E': ['####', '#...', '###.', '#...', '####'],
    'R': ['###.', '#..#', '###.', '#.#.', '#..#'],
    'S': ['.###', '#...', '.##.', '...#', '###.'],
    'H': ['#..#', '#..#', '####', '#..#', '#..#'],
    'O': ['.##.', '#..#', '#..#', '#..#', '.##.'],
    'P': ['###.', '#..#', '###.', '#...', '#...'],
    'L': ['#...', '#...', '#...', '#...', '####'],
    'A': ['.##.', '#..#', '####', '#..#', '#..#'],
    'B': ['###.', '#..#', '###.', '#..#', '###.'],
}


def sign_plate(text, plate='st_hi', ink='gl_dk', edge='st_lt'):
    w = len(text) * 5 - 1 + 6
    img = Img(w, 9)
    for y in range(9):
        for x in range(w):
            if y in (0, 8) or x in (0, w - 1):
                c = 'b_out'
            elif y == 7 or x == w - 2:
                c = edge
            else:
                c = plate
            img.p[y][x] = c
    for i, ch in enumerate(text):
        for yy, row in enumerate(FONT[ch]):
            for xx, px in enumerate(row):
                if px == '#':
                    img.p[2 + yy][3 + i * 5 + xx] = ink
    return img


AWNING = G('''
OOOOOOOOOOOOOOOOOO
O1H1H1H1H1H1H1H1HO
O3L3L3L3L3L3L3L3LO
O3L3L3L3L3L3L3L3LO
.OOOOOOOOOOOOOOOO.
.3L..3L..3L..3L...
''', dict(BL, **ROOF_TEAL))

HEART = G('''
..OOO...OOO..
.OHHHO.OHHHO.
OHHHHHOHHHHLO
OHHHHHHHHHHLO
OHHHHHHHHHHLO
.OHHHHHHHHLO.
..OHHHHHHLO..
...OHHHHLO...
....OHHLO....
.....OLO.....
......O......
''', BL)

BIG_HEART = G('''
...OOOO.....OOOO...
..OHHHHO...OHHHHO..
.OHHHHHHO.OHHHHHLO.
OHHHHHHHHOHHHHHHHLO
OHHHHHHHHHHHHHHHHLO
OHHHHHHHHHHHHHHHHLO
OHHHHHHHHHHHHHHHLLO
.OHHHHHHHHHHHHHHLO.
..OHHHHHHHHHHHHLO..
...OHHHHHHHHHHLO...
....OHHHHHHHHLO....
.....OHHHHHHLO.....
......OHHHHLO......
.......OHLLO.......
........OLO........
.........O.........
''', BL)

BIG_FLAME = BG_('''
........O.........
.......OHO........
......OHHO........
.....OHHHO...O....
....OHHHHHO.OHO...
....OHHHHHHOHHO...
...OHHH2HHHHHHO...
...OHH22HHHHHHLO..
..OHH2222HHHHHLO..
..OHH22112HHHHLO..
..OHH21112HHHLO...
...OH222222HHLO...
...OHH2222HHLLO...
....OHHHHHHLLO....
.....OOLLLLOO.....
.......OOOO.......
''')


SHOP_WINDOW = BG_('''
OOOOOOOOOOOOOO
OHHHHHHHHHHHHO
OHccccccccccLO
OHcaabbbbbabLO
OHcabHbLcbbbLO
OHMMMMMMMMMMLO
OHcbKbAbcbKbLO
OHcBBKBBBAKbLO
OHMMMMMMMMMMLO
OHLLLLLLLLLLLO
OOOOOOOOOOOOOO
''')


def cottage(kind='house'):
    """80x64 stamp (5x4 metatiles) with a red roof (recolor for others)."""
    W_, H_ = 80, 64
    img = Img(W_, H_, 'g_base')
    # ground shadow (light from the top-left)
    for x in range(7, 78):
        img.set(x, 60, 'g_dk')
        if 8 <= x <= 76:
            img.set(x, 61, 'g_dk')
    # wall block
    draw_clapboard(img, 5, 74, 30, 55)
    for y in range(30, 60):
        img.set(4, y, 'b_out')
        img.set(75, y, 'b_out')
        img.set(5, y, 'wd_lt')
        img.set(6, y, 'wd_base')
        img.set(73, y, 'wd_base')
        img.set(74, y, 'wd_dk')
    # foundation
    for x in range(4, 76):
        img.set(x, 56, 'b_out')
        img.set(x, 59, 'b_out')
        for y in (57, 58):
            c = 'st_lt' if y == 57 else 'st_mid'
            if (x + (4 if y == 58 else 0)) % 8 == 0:
                c = 'st_mid' if y == 57 else 'b_out'
            img.set(x, y, c)
    # eave shadow on the wall
    for x in range(5, 75):
        img.set(x, 32, 'wl_dk')
        img.set(x, 33, 'wl_dk' if x % 2 == 0 else 'wl_base')
    # windows + flower boxes
    for wx in (9, 57):
        if kind == 'shop':
            img.paste(SHOP_WINDOW, wx, 40)
            img.paste(AWNING, wx - 2, 34)
        else:
            img.paste(WINDOW, wx, 38)
        if kind in ('house', 'heal'):
            img.paste(FLOWERBOX, wx, 48)
    # door
    if kind == 'house':
        img.paste(DOOR, 33, 38)
        img.paste(STEP, 32, 56)
    else:
        img.paste(GLASS_DOOR, 32, 42)
        img.paste(STEP, 32, 56)
    roof = ROOF_TEAL if kind in ('shop', 'station') else ROOF_RED
    draw_roof(img, 1, 78, 5, 31, 5, roof)
    if kind == 'house':
        ch = BG_('''
        OOOOOOOOO
        OHHHHHHLO
        OLLLLLLMO
        OOOOOOOOO
        .OHLLLMO.
        .OLMLLMO.
        .OLLLMLO5
        .OLMLLMO5
        .OLLMLLO5
        .OOOOOOO5
        ..555555.
        ''')
        img.paste(ch, 58, 1)
    if kind == 'heal':
        img.paste(BIG_FLAME, 30, 6)
    if kind == 'shop':
        img.paste(sign_plate('SHOP'), 27, 26)
    if kind == 'station':
        img.paste(sign_plate('STATION'), 20, 26)
    return img


def lab():
    """112x80 stamp (7x5 metatiles): research lab."""
    W_, H_ = 112, 80
    img = Img(W_, H_, 'g_base')
    for x in range(7, 110):
        img.set(x, 76, 'g_dk')
        if 8 <= x <= 108:
            img.set(x, 77, 'g_dk')
    # walls: white upper, grey lower band, blue stripe
    for y in range(34, 72):
        for x in range(5, 107):
            if y < 40:
                c = 'st_hi'
            elif y == 40:
                c = 'gl_dk'
            elif y == 41:
                c = 'gl_base'
            elif y < 62:
                c = 'st_hi'
            else:
                c = 'st_lt' if y < 70 else 'st_mid'
            if (x - 5) % 16 == 0 and y >= 42:
                c = 'st_lt'
            img.set(x, y, c)
        img.set(4, y, 'b_out')
        img.set(107, y, 'b_out')
    for x in range(4, 108):
        img.set(x, 72, 'b_out')
        img.set(x, 73, 'st_mid' if x % 8 else 'b_out')
        img.set(x, 74, 'b_out')
    for x in range(5, 107):
        img.set(x, 34, 'st_mid')
        img.set(x, 35, 'st_lt')
    # wide windows
    for (wx, ww) in ((9, 36), (67, 36)):
        for y in range(44, 58):
            for x in range(wx, wx + ww):
                if y in (44, 57) or x in (wx, wx + ww - 1):
                    c = 'b_out'
                elif y == 45 or x == wx + 1:
                    c = 'st_lt'
                elif y == 56:
                    c = 'st_mid'
                elif (x - wx) % 8 == 0:
                    c = 'st_lt'
                elif y == 46:
                    c = 'gl_dk'
                else:
                    t = (x - wx) + (y - 46)
                    c = 'gl_hi' if t % 8 in (2, 3) and y < 52 else 'gl_base'
                    if (x - wx) % 8 == 7:
                        c = 'gl_dk'
                img.set(x, y, c)
        for x in range(wx - 1, wx + ww + 1):
            img.set(x, 58, 'st_mid' if x not in (wx - 1, wx + ww) else 'b_out')
            img.set(x, 59, 'b_out')
    # door (glass double door) in column 3
    img.paste(GLASS_DOOR, 48, 58)
    img.paste(STEP, 48, 72)
    # roof
    draw_roof(img, 1, 110, 8, 35, 5, ROOF_BLUE)
    # roof vents
    vent = BG_('''
    OOOOOOOOOO
    OHHHHHHHLO
    OLOLOLOLMO
    OLOLOLOLMO
    OMMMMMMMMO
    OOOOOOOOOO
    .55555555.
    ''', ROOF_BLUE)
    img.paste(vent, 18, 16)
    img.paste(vent, 40, 16)
    # antenna mast + dish
    ant = BG_('''
    ...OOO...
    ..OHHLO..
    .OHLLLMO.
    OHLLLLLMO
    .OOOLOOO.
    ....L....
    ...OLO...
    ...OLO...
    ...OLO...
    ...OLO...
    ...OMO...
    ...OMO...
    ...OMO...
    ..OOMOO..
    ..OLLMO..
    ..OOOOO..
    ..55555..
    ''', ROOF_BLUE)
    img.paste(ant, 84, 0)
    img.paste(sign_plate('ALMANAC'), 36, 25)
    return img


# =====================================================================
# TILESETS
# =====================================================================
#
# Three tilesets: TOWN (the village), WILD (routes) and INTERIOR. Each has
# 8 palette banks, opaque terrain metatiles (bottom layer), optional top
# layer metatiles (tall grass blades) and stamps (buildings). Decor from
# the catalogs is encoded against each tileset's banks separately and
# loaded per map at runtime, after the terrain tiles.

import decor_outdoor
import decor_indoor
import terrain_wild
import grass


def register_colors(extra):
    """Add a module's colours to C (a name may not change its value)."""
    for k, v in extra.items():
        if k in C and C[k] != v:
            raise ValueError('colour %s redefined' % k)
        C[k] = v


register_colors(decor_outdoor.OUTDOOR_COLORS)
register_colors(decor_indoor.INDOOR_COLORS)
from decor_indoor import (I_FLOOR, I_FLOOR2, I_WALL_TOP, I_WALL, I_WINDOW, I_CLOCK, I_PAINTING,
                          I_DOORMAT, I_COUNTER, I_COUNTER_L, i_rug, on, shadowize)

TOWN_TERRAIN = [
    'GRASS', 'GRASS2', 'GRASS3', 'TALLGRASS', 'FLOWER_RED', 'FLOWER_YELLOW',
    'STONE', 'TREE_TOP', 'TREE_BOTTOM', 'COURT', 'COURT_LINE_H', 'COURT_LINE_V',
]
TOWN_TERRAIN_DOC = {
    'GRASS': 'short grass + 2 subtle variants (GRASS3 has tiny flower specks)',
    'TALLGRASS': 'tall grass; top layer = front blades over the legs',
    'FLOWER_RED': 'animated flower patches (2 frames)',
    'STONE': 'plaza paving stones',
    'TREE_TOP': '16x32 tree: TOP above BOTTOM; tiles side by side and stacked',
    'COURT': 'bout ring floor, plain / white line horizontal / vertical',
}

ROOF_BANK = ['g_base', 'g_dk', 'b_out', None, None, None, None, None,
             'wl_hi', 'wl_base', 'wl_dk', 'st_hi', 'st_lt', 'st_mid', 'gl_dk']


def roof_bank(R):
    b = list(ROOF_BANK)
    for i, k in enumerate('12345'):
        b[3 + i] = R[k]
    return b


BANK_GROUND = ['g_base', 'g_lt', 'g_mid', 'g_hi', 'g_dk', 'g_dkr', 's_hi', 's_base',
               's_mid', 's_dk', 'white', 'f_yel', 'f_yeld', 'f_red', 'f_redd']
BANK_WALLS = ['g_base', 'g_dk', 'b_out', 'wl_hi', 'wl_base', 'wl_dk', 'st_hi', 'st_lt',
              'st_mid', 'wd_lt', 'wd_base', 'wd_dk', 'gl_hi', 'gl_base', 'gl_dk']
BANK_TREES = ['g_base', 'g_lt', 'g_mid', 'g_dk', 't_hi', 't_lt', 't_base', 't_mid',
              't_dk', 't_out', 'k_lt', 'k_base', 'k_dk', 'g_dkr', 'g_hi']

TOWN_BANKS = [
    BANK_GROUND,                                    # 0 grass, tall grass, path, flowers
    ['g_base', 'g_lt', 'g_mid', 'w_hi', 'w_lt', 'w_base', 'w_mid', 'w_dk',
     'r_hi', 'r_base', 'r_dk', 'c_lt', 'c_base', 'c_dk'],   # 1 water, shore, court
    BANK_TREES,                                     # 2 trees
    decor_outdoor.TOWN_DECOR_BANK,                  # 3 decor
    roof_bank(ROOF_RED), roof_bank(ROOF_BLUE), roof_bank(ROOF_TEAL),  # 4-6 roofs
    BANK_WALLS,                                     # 7 walls, windows, doors
]

WILD_BANKS = [
    BANK_GROUND,                                    # 0 grass, tall grass, path, flowers, ledges
    ['g_base', 'g_lt', 'g_mid', 'w_hi', 'w_lt', 'w_base', 'w_mid', 'w_dk',
     'r_hi', 'r_base', 'r_dk', 's_hi', 's_base', 's_mid', 'c_dk'],   # 1 water, shore, sand, paving
    BANK_TREES,                                     # 2 trees, pines
    decor_outdoor.TOWN_DECOR_BANK,                  # 3 decor (same as the village)
    decor_outdoor.WILD_DECOR_BANK,                  # 4 nature decor
    roof_bank(ROOF_TEAL),                           # 5 station roof
    roof_bank(ROOF_BLUE),                           # 6 cabin roof
    BANK_WALLS,                                     # 7 walls, windows, doors
]

INTERIOR_TERRAIN = ['VOID', 'FLOOR', 'FLOOR2', 'WALL_TOP', 'WALL', 'WINDOW',
                    'WALL_CLOCK', 'PAINTING', 'DOORMAT', 'COUNTER', 'COUNTER_L',
                    'COUNTER_R']

INTERIOR_TERRAIN_DOC = {
    'VOID': 'black outside the room', 'FLOOR': 'warm wooden planks',
    'FLOOR2': 'light tile floor (shop, hearth hall, almanac house)',
    'WALL_TOP': 'upper back wall (wallpaper, dark top trim)',
    'WALL': 'lower back wall with wainscot/baseboard, directly above the floor',
    'WINDOW': 'window in the upper wall row', 'WALL_CLOCK': 'upper wall with clock',
    'PAINTING': 'upper wall with framed picture',
    'DOORMAT': 'exit mat (on FLOOR) at the bottom edge',
    'COUNTER': 'counter middle (seamless), on FLOOR2',
    'COUNTER_L': 'counter left end', 'COUNTER_R': 'counter right end',
}

INTERIOR_BANKS = [
    # 0 room: void, walls, wood floor, window glass
    ['void', 'i_out', 'wp_hi', 'wp_base', 'wp_pat', 'wp_dk', 'bb_lt', 'bb_base',
     'bb_dk', 'fl_hi', 'fl_base', 'fl_mid', 'fl_dk', 'gl_hi', 'gl_base'],
    # 1 tile floor, counter, clock
    ['i_out', 'ck_hi', 'ck_base', 'ck_line', 'ck_dk', 'wp_hi', 'wp_base',
     'wp_pat', 'wp_dk', 'bb_lt', 'bb_base', 'bb_dk', 'gd_hi', 'gd_base', 'white'],
    decor_indoor.INDOOR_DECOR_BANKS[2],
    # 3 rugs, doormat, plants
    ['i_out', 'fl_hi', 'fl_base', 'fl_mid', 'fl_dk', 'rd_hi', 'rd_base', 'rd_dk',
     'gd_hi', 'gd_base', 'lf_hi', 'lf_base', 'lf_dk', 'pt_base', 'pt_dk'],
    decor_indoor.INDOOR_DECOR_BANKS[4],
    decor_indoor.INDOOR_DECOR_BANKS[5],
    decor_indoor.INDOOR_DECOR_BANKS[6],
    decor_indoor.INDOOR_DECOR_BANKS[7],
]

TS_NAMES = list(SETS)
TS_TAGS = {'town': 'T', 'wild': 'W', 'interior': 'I', 'city': 'CY', 'coast': 'CO', 'snow': 'SN',
           'cave': 'CV', 'grim': 'GR', 'crypt': 'CR', 'volcanic': 'VO', 'dream': 'DR', 'farm': 'FA',
           'tide': 'TD', 'dusk': 'DU', 'desert': 'DE', 'jungle': 'JU'}
QUADS = ((0, 0), (8, 0), (0, 8), (8, 8))


def img_pix(img):
    return [img.p[y][x] for y in range(img.h) for x in range(img.w)]


def add_water_anim(ts, out, bank=1):
    """Contiguous, never-shared block of animated water autotiles."""
    wq = [water_quads(f) for f in range(3)]
    water_q = [[0] * 5 for _ in range(4)]
    water_anim = [[], [], []]
    first = len(ts.tiles)
    seen = {}
    for c in range(4):
        for v in range(5):
            frames = tuple(ts.indices(img_pix(wq[f][c][v]), bank) for f in range(3))
            if frames not in seen:
                seen[frames] = ts.add_raw(frames[0])
                for f in range(3):
                    water_anim[f].append(frames[f])
            water_q[c][v] = seen[frames] | (bank << 12)
    out['water_first'] = first
    out['water_anim'] = water_anim
    out['water_q'] = water_q


def add_flower_anim(ts, out):
    flower_first = len(ts.tiles)
    flower_anim = [[], []]
    flower_meta = []
    for (pc, sc, cc, hc) in (('f_red', 'f_redd', 'f_yel', 'white'),
                             ('f_yel', 'f_yeld', 'f_yeld', 'white')):
        fr = flower_frames(pc, sc, cc, hc)
        ents = []
        for (dx, dy) in QUADS:
            frames = [ts.indices(img_pix(fr[f].crop(dx, dy, 8, 8)), 0) for f in range(2)]
            t = ts.add_raw(frames[0])
            for f in range(2):
                flower_anim[f].append(frames[f])
            ents.append(t)
        flower_meta.append(ents)
    out['flower_first'] = flower_first
    out['flower_anim'] = flower_anim
    return flower_meta


def add_stamps(ts, out, stamps):
    stamp_ids = []
    for (name, im, pref, doc) in stamps:
        sid = len(out['meta_b'])
        cw, chh = im.w // 16, im.h // 16
        for my in range(chh):
            for mx in range(cw):
                out['meta_b'].append(ts.meta(im, mx * 16, my * 16, prefer=pref,
                                             where='%s[%d,%d]' % (name, mx, my)))
                out['meta_t'].append([0, 0, 0, 0])
        stamp_ids.append((name, sid, cw, chh, doc))
    out['stamps'] = stamp_ids


def add_path(ts, out):
    pq = path_quads()
    out['path_q'] = [[ts.add(img_pix(pq[c][v]), (0,), 'path[%d][%d]' % (c, v))
                      for v in range(5)] for c in range(4)]


# ---------------------------------------------------------------------
# Ground blends: a ground laid over another (soil or sand on grass, mud on
# ash...) fades into it instead of changing at a hard 16px edge.
#
# Like paths, a blend is autotiled per 8x8 quadrant from the four
# neighbours (field.c blend_quads), with the same five variants:
#   0 inside (the cell's own tile: its texture variants stay),
#   1 inner corner, 2 edge on the left, 3 edge on top, 4 outer corner.
# Only the top-left quadrant of each variant is drawn; the other quadrants
# use it mirrored, which also makes every seam line up: across quadrants
# and cells the edge is always the same wobble mirrored. The edge wobbles,
# is rounded at the corners and dithered over one pixel.
# ---------------------------------------------------------------------

def _blend_wob(u, seed, alt=0):
    """The edge's wobble along a quadrant (u = 0..8). Mirrored copies make
    it a wave a cell long, so it must be smooth at u = 0 and u = 8; the two
    sets (alt) share those ends, so any mix of them still joins up."""
    k = 0.8 + 0.4 * math.sin(seed * 3.1)
    mid = math.sin(u * math.pi / 8) ** 2
    return (k * 1.7 * math.cos(u * math.pi / 8) + 0.7 * math.cos(u * math.pi / 4 + seed) * math.sin(u * math.pi / 8)
            + (1.3 if alt else -0.5) * mid * math.sin(u * 0.9 + seed * 2.0 + alt))


def _sdf_corner(a, b, r):
    """Signed distance to the rounded region {a < 0, b < 0} (> 0 outside)."""
    qa, qb = a + r, b + r
    return math.hypot(max(qa, 0.0), max(qb, 0.0)) + min(max(qa, qb), 0.0) - r


def blend_depth(variant, x, y, width, seed, alt=0, amp=1.0):
    """How far pixel (x, y) of a top-left quadrant is inside the blended
    ground (> 0 inside, < 0 the ground around it). amp scales the wobble."""
    px, py = x + 0.5, y + 0.5
    dx = px - (width + amp * _blend_wob(py, seed, alt))
    dy = py - (width + amp * _blend_wob(px, seed, alt))
    if variant == 2:
        return dx
    if variant == 3:
        return dy
    if variant == 4:
        return -_sdf_corner(-dx, -dy, 2.5)
    return _sdf_corner(dx, dy, 1.5)   # 1: inner corner


def fit_bank_pix(ts, pix, prefer=()):
    """Pixels whose colours fit no bank take the nearest colours of the bank
    they fit best (edge tiles mix two grounds' textures)."""
    cols = set(c for c in pix if c is not None)
    if ts.bank_for(cols, prefer) is not None:
        return pix
    best, best_n = 0, -1
    for b, bank in enumerate(ts.banks):
        n = sum(1 for c in pix if c in bank)
        if n > best_n:
            best, best_n = b, n
    bank = ts.banks[best]

    def near(c):
        if c is None or c in bank:
            return c
        r, g, bl = C[c]
        return min(bank, key=lambda k: (C[k][0] - r) ** 2 + (C[k][1] - g) ** 2 + (C[k][2] - bl) ** 2)
    return [near(c) for c in pix]


def blend_quads(ts, inner, outer, width=3.0, seed=0.0, rim_in=None, rim_out=None, where='blend', alt=0):
    """-> q[4][5] tile entries for a blend of image `inner` into `outer`
    (16x16 each); q[c][0] is 0 (the cell's own tile is used there)."""
    q = [[0] * 5 for _ in range(4)]
    for v in range(1, 5):
        pix = []
        for y in range(8):
            for x in range(8):
                d = blend_depth(v, x, y, width, seed, alt)
                # a ragged, dithered edge about two pixels wide
                n = ((hash2(x, y, int(seed * 97) + v * 13 + alt * 7) & 255) / 255.0 - 0.5) * 1.8
                inside = d + n > 0
                c = inner.get(x, y) if inside else outer.get(x, y)
                if rim_in and inside and d + n < 1.0:
                    c = rim_in
                if rim_out and not inside and d + n > -1.0 and hash2(x, y, 73) % 3 == 0:
                    c = rim_out
                pix.append(c)
        e = ts.add(fit_bank_pix(ts, pix), where='%s[%d]' % (where, v))
        for c in range(4):
            q[c][v] = e ^ ((c & 1) << 10) ^ ((c >> 1) << 11)
    return q


def add_blend(ts, out, inner_names, inner_img, outer_img, outer_names, **kw):
    """Make the terrains inner_names one blend group that fades into the
    terrains outer_names where it meets them (outer_img is how they look;
    against anything else, like water or other grounds, it keeps its edge).
    Images may be Img or (bottom, top) pairs as the builders keep them."""
    if isinstance(inner_img, tuple):
        inner_img = inner_img[0]
    if isinstance(outer_img, tuple):
        outer_img = outer_img[0]
    where = '%s.blend.%s' % (ts.name, inner_names[0])
    q = [blend_quads(ts, inner_img, outer_img, where=where, alt=a, **kw) for a in (0, 1)]
    out.setdefault('blends', []).append({'inner': list(inner_names), 'outer': list(outer_names), 'q': q})


BLEND_MAX = 8   # blends per tileset (blend_outer[] is a bit mask)


# ---------------------------------------------------------------------
# Tile attributes (u16, docs/EXPANSION.md 10.2) and metatile flags
# ---------------------------------------------------------------------
A_SOLID, A_GRASS, A_DOOR, A_WATER, A_COUNTER, A_EXIT, A_SIGN, A_LEDGE = (1 << i for i in range(8))
A_ICE, A_SOIL, A_CURRENT, A_DIR_LO, A_DIR_HI, A_PAD, A_SWITCH, A_DEEP = (1 << i for i in range(8, 16))
MF_GROUND = 1    # plain ground: may be drawn under overlays (trees)
MF_OVERLAY = 2   # transparent object terrain (trees): ground drawn beneath
ATTR_NAMES = ['SOLID', 'GRASS', 'DOOR', 'WATER', 'COUNTER', 'EXIT', 'SIGN', 'LEDGE',
              'ICE', 'SOIL', 'CURRENT', 'DIR_LO', 'DIR_HI', 'PAD', 'SWITCH', 'DEEP']

# Grass variants: GRASS3 1/16, GRASS2 4/16, GRASS 11/16 (by cell hash).
GRASS_VARIANTS = [('GRASS3', 1), ('GRASS2', 4), ('GRASS', 11)]


def add_overlay_terrain(ts, out, name, img, top):
    """An overlay cell: transparent art on BG2 (bottom) or BG3 (top)."""
    ents = ts.meta(img, where=name, opaque=False)
    if top:
        out['meta_b'].append([0, 0, 0, 0])
        out['meta_t'].append(ents)
    else:
        out['meta_b'].append(ents)
        out['meta_t'].append([0, 0, 0, 0])


def finish_tileset(out, name, tag, attrs, ground, overlay, legend, oob, default_ground,
                   backdrop, doors=(), legend_default='.', elev=None):
    """Attach attributes, flags, the map legend and misc info to a build.

    attrs:   {terrain or stamp name: A_* bits} (stamps default to A_SOLID)
    ground:  terrain names that are plain ground (drawn under overlays)
    overlay: terrain names that are transparent objects (trees)
    legend:  {char: 'NAME' | [('NAME', weight/16), ...] | 'PATH' | 'WATER'}
    doors:   [(stamp name, col, row)] cells that are doors
    backdrop: 'ground' (bank 0 colour 1) or an (r, g, b) triple
    elev:    None (no elevation art) or a colour-role mapping for
             tools/elevation.py ({} = the town colour names; docs/ELEVATION.md)
    """
    grass.install(sys.modules[__name__], out, name, attrs, legend)  # tall grass (tools/grass.py)
    ids = {n: i for i, n in enumerate(out['terrain'])}
    for (sname, sid, cw, chh, doc) in out['stamps']:
        ids[sname] = sid
    n = len(out['meta_b'])
    attr, mflags = [0] * n, [0] * n
    for i, t in enumerate(out['terrain']):
        attr[i] = attrs.get(t, A_SOLID if t in overlay else 0)
        if t in ground:
            mflags[i] |= MF_GROUND
        if t in overlay:
            mflags[i] |= MF_OVERLAY
    for (sname, sid, cw, chh, doc) in out['stamps']:
        for k in range(cw * chh):
            attr[sid + k] = attrs.get(sname, A_SOLID)
    for (sname, col, row) in doors:
        st = [x for x in out['stamps'] if x[0] == sname][0]
        attr[st[1] + row * st[2] + col] = A_SOLID | A_DOOR
    for t in list(ground) + list(overlay) + list(attrs):
        if t not in ids:
            raise KeyError('%s: unknown terrain %s' % (name, t))
    leg = {}
    for ch, spec in legend.items():
        if spec in ('PATH', 'WATER'):
            if 'path_q' not in out:
                raise ValueError('%s: legend %r needs path/water autotiles' % (name, ch))
            leg[ch] = spec
        elif isinstance(spec, str):
            leg[ch] = [(spec, 16)]
        else:
            if sum(w for (_, w) in spec) != 16:
                raise ValueError('%s: legend %r weights must sum to 16' % (name, ch))
            if len(spec) > 8:
                raise ValueError('%s: legend %r has more than 8 variants' % (name, ch))
            leg[ch] = list(spec)
        if isinstance(leg[ch], list):
            for (t, w) in leg[ch]:
                if t not in ids:
                    raise KeyError('%s: legend %r: unknown terrain %s' % (name, ch, t))
    if legend_default not in leg:
        raise ValueError('%s: legend default %r missing' % (name, legend_default))
    blend_of, blend_outer = [0] * n, [0] * n
    if len(out.get('blends', [])) > BLEND_MAX:
        raise ValueError('%s: more than %d blends' % (name, BLEND_MAX))
    for bi, bl in enumerate(out.get('blends', [])):
        for t in bl['inner'] + bl['outer']:
            if t not in ids:
                raise KeyError('%s: blend of unknown terrain %s' % (name, t))
        for t in bl['inner']:
            blend_of[ids[t]] = bi + 1
        for t in bl['outer']:
            blend_outer[ids[t]] |= 1 << bi
    out['blend_of'], out['blend_outer'] = blend_of, blend_outer
    out.setdefault('blends', [])
    out.update(name=name, tag=tag, attr=attr, mflags=mflags, legend=leg,
               legend_default=legend_default, oob=ids[oob], ground_default=ids[default_ground],
               backdrop=backdrop, ids=ids)
    anims = []
    if 'water_first' in out:
        anims.append((out['water_first'], out['water_anim'], 20))
    if 'flower_first' in out:
        anims.append((out['flower_first'], out['flower_anim'], 32))
    out['anims'] = out.get('anims', []) + anims
    import elevation
    if elev is None:
        elev = elevation.ROLES.get(name)
    if elev is not None:
        out['elev'] = elevation.elevation_art(out['ts'], elev, where=name)
    if len(out['ts'].tiles) > out['ts'].limit:
        raise ValueError('%s: %d tiles > %d' % (name, len(out['ts'].tiles), out['ts'].limit))
    return out


def build_town(name='town'):
    check_banks(name, TOWN_BANKS)
    ts = TileSet(name, TOWN_BANKS)
    out = {'ts': ts, 'meta_b': [], 'meta_t': [], 'terrain': TOWN_TERRAIN}
    add_water_anim(ts, out)
    flower_meta = add_flower_anim(ts, out)
    tall_b, tall_t = tallgrass_layers()
    tree = tree_img(overlay=True)
    imgs = {
        'GRASS': (GRASS_A, 0), 'GRASS2': (GRASS_B, 0), 'GRASS3': (GRASS_C, 0),
        'TALLGRASS': (tall_b, 0), 'STONE': (STONE, 1),
        'COURT': (court_img(), 1), 'COURT_LINE_H': (court_img('h'), 1),
        'COURT_LINE_V': (court_img('v'), 1),
    }
    for tname in TOWN_TERRAIN:
        if tname == 'FLOWER_RED':
            out['meta_b'].append(flower_meta[0])
        elif tname == 'FLOWER_YELLOW':
            out['meta_b'].append(flower_meta[1])
        elif tname == 'TREE_TOP':
            add_overlay_terrain(ts, out, tname, tree.crop(0, 0, 16, 16), top=True)
            continue
        elif tname == 'TREE_BOTTOM':
            add_overlay_terrain(ts, out, tname, tree.crop(0, 16, 16, 16), top=False)
            continue
        else:
            im, bank = imgs[tname]
            out['meta_b'].append(ts.meta(im, prefer=(bank,), where=tname))
        if tname == 'TALLGRASS':
            out['meta_t'].append(ts.meta(tall_t, prefer=(0,), where='TALLGRASS.top',
                                         opaque=False))
        else:
            out['meta_t'].append([0, 0, 0, 0])
    house = cottage('house')
    add_stamps(ts, out, [
        ('HOUSE_RED', house, (7, 4), 'red/terracotta roof cottage, door col 2 row 3'),
        ('HOUSE_BLUE', house.replace(RED_TO_BLUE), (7, 5), 'blue roof cottage, door col 2 row 3'),
        ('LAB', lab(), (7, 5), 'ALMANAC HOUSE, door col 3 row 4'),
        ('SHOP', cottage('shop'), (7, 6), 'shop, SHOP sign, door col 2 row 3'),
        ('HEAL', cottage('heal'), (7, 4), 'HEARTH HALL, flame emblem, door col 2 row 3'),
        ('COURT_CIRCLE', court_circle_img(), (1,), 'center circle on the ring floor (walkable)'),
    ])
    add_path(ts, out)
    return finish_tileset(
        out, name, 'T',
        attrs={'TALLGRASS': A_GRASS, 'COURT_CIRCLE': 0},
        ground=['GRASS', 'GRASS2', 'GRASS3'], overlay=['TREE_TOP', 'TREE_BOTTOM'],
        legend={'.': GRASS_VARIANTS, ',': 'TALLGRASS', 'r': 'FLOWER_RED', 'y': 'FLOWER_YELLOW',
                '=': 'PATH', '~': 'WATER', '#': 'STONE', 'T': 'TREE_TOP', 't': 'TREE_BOTTOM',
                'c': 'COURT', 'h': 'COURT_LINE_H', 'v': 'COURT_LINE_V'},
        oob='TREE_TOP', default_ground='GRASS', backdrop='ground',
        doors=[('HOUSE_RED', 2, 3), ('HOUSE_BLUE', 2, 3), ('SHOP', 2, 3), ('HEAL', 2, 3),
               ('LAB', 3, 4)], elev={})


WILD_OVERLAY = ('TREE_TOP', 'TREE_BOTTOM', 'PINE_TOP', 'PINE_BOTTOM')


def build_wild(name='wild'):
    check_banks(name, WILD_BANKS)
    ts = TileSet(name, WILD_BANKS)
    out = {'ts': ts, 'meta_b': [], 'meta_t': [], 'terrain': terrain_wild.WILD_TERRAIN}
    add_water_anim(ts, out)
    flower_meta = add_flower_anim(ts, out)
    imgs = terrain_wild.wild_images()
    for tname in terrain_wild.WILD_TERRAIN:
        if tname == 'FLOWER_RED':
            out['meta_b'].append(flower_meta[0])
            out['meta_t'].append([0, 0, 0, 0])
            continue
        if tname == 'FLOWER_YELLOW':
            out['meta_b'].append(flower_meta[1])
            out['meta_t'].append([0, 0, 0, 0])
            continue
        bottom, top = imgs[tname]
        if tname in WILD_OVERLAY:
            add_overlay_terrain(ts, out, tname, bottom, top=tname.endswith('_TOP'))
            continue
        out['meta_b'].append(ts.meta(bottom, where='wild.' + tname))
        out['meta_t'].append(ts.meta(top, where='wild.%s.top' % tname, opaque=False)
                             if top else [0, 0, 0, 0])
    cabin = cottage('house').replace(RED_TO_BLUE)
    add_stamps(ts, out, [
        ('CABIN', cabin, (7, 6), 'blue roof cabin, door col 2 row 3'),
        ('STATION', cottage('station'), (7, 5),
         'lake field station (teal roof), door col 2 row 3'),
    ])
    add_path(ts, out)
    GRASSY = ['GRASS', 'GRASS2', 'GRASS3', 'FLOWER_RED', 'FLOWER_YELLOW', 'TALLGRASS']
    for (inner, width, seed) in ((['SAND', 'SAND2'], 3.0, 0.7), (['DIRT'], 2.5, 1.9),
                                 (['MEADOW'], 2.0, 2.6), (['FOREST', 'FOREST2'], 2.5, 3.3)):
        add_blend(ts, out, inner, imgs[inner[0]], imgs['GRASS'], GRASSY, width=width, seed=seed)
    return finish_tileset(
        out, name, 'W',
        attrs={'TALLGRASS': A_GRASS, 'REEDS': A_GRASS, 'CLIFF': A_SOLID, 'CLIFF_FACE': A_SOLID,
               'LEDGE': A_LEDGE, 'LEDGE_L': A_LEDGE, 'LEDGE_R': A_LEDGE},
        ground=['GRASS', 'GRASS2', 'GRASS3', 'SAND', 'SAND2', 'FOREST', 'FOREST2', 'DIRT',
                'MEADOW'],
        overlay=list(WILD_OVERLAY),
        legend={'.': GRASS_VARIANTS, ',': 'TALLGRASS', 'r': 'FLOWER_RED', 'y': 'FLOWER_YELLOW',
                '=': 'PATH', '~': 'WATER', '#': 'STONE', 'T': 'TREE_TOP', 't': 'TREE_BOTTOM',
                'P': 'PINE_TOP', 'p': 'PINE_BOTTOM', 'L': 'LEDGE', '[': 'LEDGE_L',
                ']': 'LEDGE_R', 'C': 'CLIFF', 'c': 'CLIFF_FACE', 'd': 'DIRT', 'm': 'MEADOW',
                's': [('SAND2', 2), ('SAND', 14)], 'f': [('FOREST2', 4), ('FOREST', 12)],
                'R': 'REEDS'},
        oob='TREE_TOP', default_ground='GRASS', backdrop='ground',
        doors=[('CABIN', 2, 3), ('STATION', 2, 3)], elev={})


def build_interior(name='interior'):
    check_banks(name, INTERIOR_BANKS)
    ts = TileSet(name, INTERIOR_BANKS)
    out = {'ts': ts, 'meta_b': [], 'meta_t': [], 'terrain': INTERIOR_TERRAIN}
    solid = Img(16, 16, 'void')
    counter = shadowize(I_COUNTER, 'ck_dk', (14,))
    counter_l = shadowize(I_COUNTER_L, 'ck_dk', (14,))
    counter_r = counter_l.flip_h()
    terr = {
        'VOID': solid, 'FLOOR': I_FLOOR, 'FLOOR2': I_FLOOR2,
        'WALL_TOP': I_WALL_TOP, 'WALL': I_WALL,
        'WINDOW': on(I_WALL_TOP, I_WINDOW), 'WALL_CLOCK': on(I_WALL_TOP, I_CLOCK),
        'PAINTING': on(I_WALL_TOP, I_PAINTING), 'DOORMAT': on(I_FLOOR, I_DOORMAT),
        'COUNTER': on(I_FLOOR2, counter), 'COUNTER_L': on(I_FLOOR2, counter_l),
        'COUNTER_R': on(I_FLOOR2, counter_r),
    }
    for n in INTERIOR_TERRAIN:
        out['meta_b'].append(ts.meta(terr[n], where=n))
        out['meta_t'].append([0, 0, 0, 0])
    add_stamps(ts, out, [
        ('RUG', i_rug(), (), 'decorative rug on FLOOR (walkable; baked into the floor)'),
    ])
    solid_names = ['VOID', 'WALL_TOP', 'WALL', 'WINDOW', 'WALL_CLOCK', 'PAINTING']
    attrs = {n: A_SOLID for n in solid_names}
    attrs.update({'DOORMAT': A_EXIT, 'COUNTER': A_SOLID | A_COUNTER,
                  'COUNTER_L': A_SOLID | A_COUNTER, 'COUNTER_R': A_SOLID | A_COUNTER, 'RUG': 0})
    return finish_tileset(
        out, name, 'I', attrs=attrs, ground=['FLOOR', 'FLOOR2'], overlay=[],
        legend={'W': 'WALL_TOP', 'w': 'WALL', 'n': 'WINDOW', 'k': 'WALL_CLOCK', 'p': 'PAINTING',
                '.': 'FLOOR', ':': 'FLOOR2', 'D': 'DOORMAT', '<': 'COUNTER_L', '=': 'COUNTER',
                '>': 'COUNTER_R', ' ': 'VOID'},
        oob='VOID', default_ground='FLOOR', backdrop=(0, 0, 0), legend_default=' ')


def build_tilesets():
    """Every tileset in registry order (pixelart.SETS); new ones come from
    tools/tilesets/ts_<name>.py (build(gf, name) -> finished tileset)."""
    import importlib
    import tilesets  # noqa: F401  (tools/tilesets/__init__.py)
    from engine import assemble   # tools/tiles2/engine: the tiles2 art (docs/TILES2.md 8)
    sets = {}
    with assemble.Recorder(sys.modules[__name__]) as rec:
        for name in SETS:
            rec.current = name
            if name == 'town':
                sets[name] = build_town()
            elif name == 'wild':
                sets[name] = build_wild()
            elif name == 'interior':
                sets[name] = build_interior()
            else:
                mod = importlib.import_module('tilesets.ts_%s' % name)
                sets[name] = mod.build(sys.modules[__name__], name)
                sets[name]['uses_decor'] = list(getattr(mod, 'USES_DECOR', []))
    for name in SETS:
        if name in assemble.PORTED:
            sets[name] = assemble.build(sys.modules[__name__], name, rec.rec[name], sets[name])
        sets[name]['tag'] = TS_TAGS[name]
        sets[name]['name'] = name
    return sets


# =====================================================================
# DECOR ENCODING
# =====================================================================

def all_decor():
    items = decor_outdoor.OUTDOOR_DECOR + decor_indoor.INDOOR_DECOR + __import__('decor_farm').FARM_DECOR
    items = items + __import__('decor_north').NORTH_DECOR  # W-NORTH (snow, cave)
    items = items + __import__('decor_fusion').FUSION_DECOR  # FUSION (Resonance Works machines)
    items = items + __import__('decor_craft').CRAFT_DECOR  # CRAFT (stations)
    items = items + __import__('decor_grim').DECOR  # W-GRIM (grim, crypt)
    items = items + __import__('decor_east').EAST_DECOR  # W-EAST (city, Copperline, Elderwood)
    items = items + __import__('decor_west').WEST_DECOR  # W-WEST (coast, harbour interiors)
    items = items + __import__('decor_far').FAR_DECOR  # W-FAR (volcanic, dream)
    items = items + __import__('decor_biomes').DECOR  # biome-native landmarks and wayfinding
    seen = set()
    for d in items:
        if d.name in seen:
            raise ValueError('decor %s defined twice' % d.name)
        seen.add(d.name)
    return items


def encode_decor(ts, d):
    """Encode one decor kind against a tileset's banks.

    Returns (tiles, cells): tiles = list of per-frame tuples of bank
    indices (one tile slot each); cells = [4 entries] per cell, row-major,
    each entry (local_tile + 1) | hflip << 10 | vflip << 11 | bank << 12,
    or 0 for a fully transparent quadrant."""
    frames = d.frames
    animated = len(frames) > 1
    tiles, lookup, cells = [], {}, []
    for cy in range(d.h):
        for cx in range(d.w):
            ents = []
            for (qx, qy) in QUADS:
                pixf = [[f.get(cx * 16 + qx + x, cy * 16 + qy + y) for y in range(8) for x in range(8)]
                        for f in frames]
                colors = set(c for pix in pixf for c in pix if c is not None)
                if not colors:
                    ents.append(0)
                    continue
                b = ts.bank_for(colors, ())
                if b is None:
                    raise ValueError('decor %s (%s): cell %d,%d quadrant %d,%d colours %s fit '
                                     'no bank' % (d.name, ts.name, cx, cy, qx, qy, sorted(colors)))
                idxf = tuple(ts.indices(pix, b) for pix in pixf)
                hh = vv = 0
                if animated:
                    t = len(tiles)
                    tiles.append(idxf)
                else:
                    found = None
                    for h in (0, 1):
                        for v in (0, 1):
                            f = flip_idx(idxf[0], h, v)
                            if (f, b) in lookup:
                                found = (lookup[(f, b)], h, v)
                                break
                        if found:
                            break
                    if found:
                        t, hh, vv = found
                    else:
                        t = len(tiles)
                        tiles.append(idxf)
                        lookup[(idxf[0], b)] = t
                ents.append((t + 1) | (hh << 10) | (vv << 11) | (b << 12))
            cells.append(ents)
    return tiles, cells


def decor_in_set(d, sname, tilesets):
    return sname in d.sets or d.name in tilesets[sname].get('uses_decor', ())


def build_decor(tilesets):
    """tilesets: {'town': out, ...}. Returns the global decor tables."""
    kinds = all_decor()
    names = set(d.name for d in kinds)
    for sname in TS_NAMES:
        for n in tilesets[sname].get('uses_decor', ()):
            if n not in names:
                raise KeyError('%s: USES_DECOR names unknown decor %s' % (sname, n))
    words, meta, defs, art = [], [], {}, {}
    tile_total = 0
    for sname in TS_NAMES:
        ts = tilesets[sname]['ts']
        for d in kinds:
            if not decor_in_set(d, sname, tilesets):
                continue
            if 'art2' in tilesets[sname]:
                # tiles2 art in the kind's own footprint and masks (tools/tiles2/engine)
                from engine import assemble
                import copy as _copy
                frames, period = assemble.decor_frames(sname, tilesets[sname], d)
                d = _copy.copy(d)
                d.frames, d.period = frames, period
            art[(sname, d.name)] = d
            tiles, cells = encode_decor(ts, d)
            first = tile_total
            nf = len(d.frames)
            for f in range(nf):
                for t in tiles:
                    words.extend(pack4(t[f]))
            tile_total += len(tiles) * nf
            defs[(sname, d.name)] = dict(w=d.w, h=d.h, frames=nf, period=d.period,
                                         tile_first=first, tile_count=len(tiles),
                                         meta_first=len(meta), solid=d.solid, top=d.top,
                                         floor=d.floor)
            meta.extend(cells)
    return {'kinds': kinds, 'words': words, 'meta': meta, 'defs': defs, 'tiles': tile_total, 'art': art}


def decor_entry_abs(e, base):
    """Resolve a decor meta entry to an absolute tile entry (like the game)."""
    if not e:
        return 0
    return (e & 0xFC00) | (base + (e & 1023) - 1)


# =====================================================================
# CHARACTERS (16x32 OBJ, 9 frames)
# =====================================================================
#
# Each character = head grids (down/up/left), body grids (down/up/left) and
# a leg style. Frames are assembled bottom-up (feet on rows 29-31); walking
# frames bob the head+body down 1px and swap the legs. Grid chars are
# semantic and mapped per character to its own 15-color OBJ palette.

LEGS = {
    'pants': {
        'down': ['''
            ...oppppppppo...
            ...opppoopPpo...
            ...opPo..opPo...
            ...offo..offo...
            ...oFFo..oFFo...
            ....oo....oo....
            ''', '''
            ...opppoopPpo...
            ...opPo..opPo...
            ...offo..oFFo...
            ...oFFo...oo....
            ....oo..........
            '''],
        'up': ['''
            ...oppppppppo...
            ...opppoopPpo...
            ...opPo..opPo...
            ...offo..offo...
            ...oFFo..oFFo...
            ....oo....oo....
            ''', '''
            ...opppoopPpo...
            ...opPo..opPo...
            ...offo..oFFo...
            ...oFFo...oo....
            ....oo..........
            '''],
        'left': ['''
            .....opppPo.....
            .....opppPo.....
            .....oppPPo.....
            ....offfoFo.....
            ....oFFFFFo.....
            .....ooooo......
            ''', '''
            ....oppppPPo....
            ...oppPo.oPPo...
            ..offfo...oFFo..
            ..oFFFo...oFFo..
            ...ooo.....oo...
            ''', '''
            .....oppPPo.....
            .....opPPPo.....
            ....offfPPo.....
            ....oFFFoFo.....
            .....ooo.o......
            '''],
    },
    'bare': {
        'down': ['''
            ....okKo.okKo...
            ....okKo.okKo...
            ...offo..offo...
            ...oFFo..oFFo...
            ....oo....oo....
            ''', '''
            ....okKo.okKo...
            ...offo..okKo...
            ...offo..oFFo...
            ....oo....oo....
            '''],
        'up': ['''
            ....okKo.okKo...
            ....okKo.okKo...
            ...offo..offo...
            ...oFFo..oFFo...
            ....oo....oo....
            ''', '''
            ....okKo.okKo...
            ...offo..okKo...
            ...offo..oFFo...
            ....oo....oo....
            '''],
        'left': ['''
            ......okKo......
            ......okKo......
            .....offfo......
            .....oFFFo......
            ......ooo.......
            ''', '''
            .....okoKo......
            ....okoooKo.....
            ...offo..oFo....
            ...ooo...oFo....
            ..........o.....
            ''', '''
            ......okKo......
            ......oKko......
            .....offKo......
            .....oFFFo......
            ......ooo.......
            '''],
    },
}


def parse16(text):
    rows = [r.strip() for r in text.strip('\n').split('\n')]
    rows = [r for r in rows if r]
    for r in rows:
        if len(r) != 16:
            raise ValueError('sprite row not 16 wide: %r' % r)
    return rows


def frame_rows(head, body, legs, stand_rows, bob, mirror_legs=False, coat=0):
    """Compose a 16x32 frame (list of 32 strings). Head directly above body,
    body directly above the standing legs; walking frames bob 1px down."""
    canvas = [['.'] * 16 for _ in range(32)]
    leg_rows = parse16(legs)
    if mirror_legs:
        leg_rows = [r[::-1] for r in leg_rows]
    body_rows = parse16(body)
    head_rows = parse16(head)

    def stamp(rows, y0):
        for i, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch != '.' and 0 <= y0 + i < 32:
                    canvas[y0 + i][x] = ch
    stamp(leg_rows, 32 - len(leg_rows))
    yb = 32 - stand_rows - len(body_rows) + coat + (1 if bob else 0)
    stamp(body_rows, yb)
    stamp(head_rows, yb - len(head_rows))
    return [''.join(r) for r in canvas]


def char_frames(ch):
    """9 frames of 32 strings for a character definition dict."""
    legs = LEGS[ch.get('legs', 'pants')]
    frames = []
    for d in ('down', 'up', 'left'):
        head, body = ch['head_' + d], ch['body_' + d]
        L = legs[d]
        n = len(parse16(L[0]))
        bw = ch.get('body_%s_walk' % d, body)
        cz = ch.get('coat', 0)
        frames.append(frame_rows(head, body, L[0], n, False, coat=cz))
        if d == 'left':
            frames.append(frame_rows(head, bw, L[1], n, True, coat=cz))
            frames.append(frame_rows(head, bw, L[2], n, True, coat=cz))
        else:
            frames.append(frame_rows(head, bw, L[1], n, True, coat=cz))
            frames.append(frame_rows(head, bw, L[1], n, True, mirror_legs=True,
                                     coat=cz))
    return frames


CHARACTERS = []

CHARACTERS.append({
    'name': 'PLAYER',
    'pal': [('o', (48, 40, 56)), ('k', (248, 212, 172)), ('K', (216, 160, 120)),
            ('h', (72, 56, 60)), ('H', (120, 96, 96)), ('r', (88, 160, 120)),
            ('R', (48, 104, 88)), ('w', (240, 224, 168)), ('W', (200, 176, 112)),
            ('j', (232, 128, 64)), ('J', (168, 80, 48)), ('p', (72, 76, 104)),
            ('P', (44, 46, 68)), ('y', (176, 124, 76)), ('Y', (128, 84, 52)),
            ('f', 'R'), ('F', 'o')],
    'head_down': '''
        .....oooooo.....
        ....orrwwrRo....
        ...orrwwwwrRo...
        ..orrrwwwwrrRo..
        ..orrrrrrrrrRo..
        .oRRRRRRRRRRRRo.
        .ohhhhhhhhhhhho.
        .ohkhkkkkkkhkho.
        .ohkkokkkkokKho.
        .ohkkokkkkokKho.
        ..oKkkkkkkkKKo..
        ...ooKKKKKKoo...
    ''',
    'body_down': '''
        ..oojjjwWjjjoo..
        .ojjJjjwWjjJjJo.
        .ojjJjjwWjjJjJo.
        .ojjJjjwWjjJJJo.
        .okKoJjwWjJokKo.
        ..oooJJJJJJooo..
    ''',
    'head_up': '''
        .....oooooo.....
        ....orrrrrRo....
        ...orrrrrrrRo...
        ..orrrrrrrrrRo..
        ..orrrrrrrrrRo..
        .oRRRRRwwRRRRRo.
        .ohhhhhhhhhhhho.
        .ohHhhhhhhhhhho.
        .ohHhhhhhhhhhho.
        .ohhhhhhhhhhhho.
        ..ohhhhhhhhhho..
        ...ooKkkkkKoo...
    ''',
    'body_up': '''
        ..ooyyyyyyyyoo..
        .ojoyyyyyyyyoJo.
        .ojoyYyyyyYyoJo.
        .ojoyyyyyyyyoJo.
        .okoYYYYYYYYoKo.
        ..ooJJJJJJJJoo..
    ''',
    'head_left': '''
        ......ooooo.....
        .....orrrrRo....
        ....owwrrrrRo...
        ...owwwrrrrrRo..
        ...owwrrrrrrRo..
        .ooRRRRRRRRRRo..
        oRRRooooohhhhho.
        .oookkkkkhhhhho.
        ...okkkkkkhhhho.
        ...okokkkkhhho..
        ..okkkkkkkKhho..
        ...ooKKkkKKoo...
    ''',
    'body_left': '''
        ....oojjjjooo...
        ...ojjjjjjoyYo..
        ...ojjjJjjoyYo..
        ...ojjjJjjoyYo..
        ...ojjkKjJoYYo..
        ....ooJJJJooo...
    ''',
})


OUT_ = (48, 40, 56)
SKIN = [('k', (248, 212, 172)), ('K', (216, 160, 120))]

CHARACTERS.append({
    'name': 'PROFESSOR', 'coat': 2,
    'pal': [('o', OUT_)] + SKIN + [
        ('h', (200, 200, 208)), ('H', (136, 136, 152)), ('w', (248, 248, 248)),
        ('W', (184, 192, 216)), ('s', (104, 168, 104)), ('S', (64, 120, 72)),
        ('p', (160, 108, 68)), ('P', (112, 72, 48)), ('f', (88, 60, 52)),
        ('F', (60, 40, 40))],
    'head_down': '''
        .....oooooo.....
        ...oohhhhhhoo...
        ..ohhhhhhhhhHo..
        ..ohhhhhhhhhHo..
        .ohhhhhhhhhhhHo.
        .ohHhkkkkkkhHHo.
        .ohkkkkkkkkkkHo.
        .ohkkokkkkokkHo.
        ..okkokkkkokKo..
        ..oKkkkkkkkKKo..
        ...ooKKKKKKoo...
    ''',
    'body_down': '''
        ..oowwwsswwwoo..
        .owwWwwsSwwWwWo.
        .owwWwwsSwwWwWo.
        .owwWwwsSwwWWWo.
        .okKWwwwwwwWkKo.
        ..owwwwowwwWWo..
        ..owwwwowwwWWo..
        ..oooooooooooo..
    ''',
    'head_up': '''
        .....oooooo.....
        ...oohhhhhhoo...
        ..ohhhhhhhhhHo..
        ..ohhhhhhhhhHo..
        .ohhhhhhhhhhhHo.
        .ohhhhhhhhhhhHo.
        .ohhhhhhhhhhHHo.
        .ohhhhhhhhhhHHo.
        ..ohhhhhhhhHHo..
        ..oKhhhhhhhHKo..
        ...ooKKKKKKoo...
    ''',
    'body_up': '''
        ..oowwwwwwwwoo..
        .owwwwwwwwwwWWo.
        .owWwwwwwwwwWWo.
        .owWwwwwwwwwWWo.
        .okWwwwwwwwwWKo.
        ..owwwwWwwwwWo..
        ..owwwwWwwwwWo..
        ..oooooooooooo..
    ''',
    'head_left': '''
        ......ooooo.....
        ....oohhhhhoo...
        ...ohhhhhhhhHo..
        ...ohhhhhhhhHo..
        ..ohhhhhhhhhhHo.
        ..okkkkhhhhhhHo.
        ..okkkkkhhhhhHo.
        ..okokkkkhhhHo..
        .okkkkkkkkhHHo..
        ..oKkkkkkKKHo...
        ...ooKKKKKoo....
    ''',
    'body_left': '''
        ....oowwwwoo....
        ...owwwwwwwWo...
        ...owwWwwwwWo...
        ...owwWwwwwWo...
        ...owWkKwwwWo...
        ...owwwwwwwWo...
        ...owwwwwwWWo...
        ....oooooooo....
    ''',
})

CHARACTERS.append({
    'name': 'BAKER', 'legs': 'bare', 'coat': 2,
    'pal': [('o', OUT_)] + SKIN + [
        ('h', (192, 92, 52)), ('H', (132, 56, 40)), ('w', (248, 248, 248)),
        ('W', (192, 196, 216)), ('d', (248, 152, 176)), ('D', (208, 100, 136)),
        ('f', (152, 88, 64)), ('F', (104, 56, 48))],
    'head_down': '''
        ......oooo......
        .....ohhhHo.....
        .....ohhHHo.....
        ...ooohhhhooo...
        ..ohhhhhhhhhHo..
        .ohhhhhhhhhhhHo.
        .ohhhhhhhhhhhHo.
        .ohhkkkkkkkkhHo.
        .ohkkkkkkkkkkho.
        .ohkkokkkkokkho.
        ..okkokkkkokKo..
        ..oKkkkkkkkKKo..
        ...ooKKKKKKoo...
    ''',
    'body_down': '''
        ..oodwwwwwwdoo..
        .oddowwwwwwoddo.
        .oddowwwwwwoDDo.
        .okKowwwwwwokKo.
        ..odwwwwwwwwDo..
        ..odwwwWwwwwDo..
        ..oddddddddDDo..
        ...oooooooooo...
    ''',
    'head_up': '''
        ......oooo......
        .....ohhhHo.....
        .....ohhHHo.....
        ...ooohhhhooo...
        ..ohhhhhhhhhHo..
        .ohhhhHhhhhhhHo.
        .ohhhhhHhhhhhHo.
        .ohhhhhhhhhhhHo.
        .ohhhhhhhhhhHHo.
        .ohhhhhhhhhhHHo.
        ..ohhhhhhhhhHo..
        ..oKhhhhhhhhKo..
        ...ooKKKKKKoo...
    ''',
    'body_up': '''
        ..ooddddddddoo..
        .odddddddddddDo.
        .odddddddddddDo.
        .okKddwwwwddkKo.
        ..oddwddwdddDo..
        ..odddddddddDo..
        ..oddddddddDDo..
        ...oooooooooo...
    ''',
    'head_left': '''
        .........oooo...
        ........ohhhHo..
        ........ohhHHo..
        .....ooooohhoo..
        ....ohhhhhhhho..
        ...ohhhhhhhhhHo.
        ..ohkkhhhhhhhHo.
        ..okkkkkhhhhhHo.
        ..okokkkkhhhhHo.
        .okkkkkkkkhhHo..
        ..oKkkkkkKKHo...
        ...ooKKKKKoo....
    ''',
    'body_left': '''
        ....ooddddoo....
        ...oddddddddo...
        ...owwwddddDo...
        ...owwkKdddDo...
        ...owwwwdddDo...
        ...owwwwddDDo...
        ...oddddddDDo...
        ....oooooooo....
    ''',
})

CHARACTERS.append({
    'name': 'GARDENER',
    'pal': [('o', OUT_)] + SKIN + [
        ('t', (240, 212, 120)), ('T', (192, 152, 72)), ('b', (200, 76, 60)),
        ('w', (240, 240, 240)), ('W', (184, 188, 200)), ('g', (104, 176, 88)),
        ('G', (60, 116, 64)), ('s', (232, 196, 136)), ('S', (192, 148, 96)),
        ('f', (120, 80, 56)), ('p', 'g'), ('P', 'G'), ('F', 'o')],
    'head_down': '''
        .....oooooo.....
        ....otttttTo....
        ...otttttttTo...
        ...obbbbbbbbo...
        .ootttttttttTTo.
        otttttttttttttTo
        .ooookkkkkkoooo.
        ..owkkkkkkkkwo..
        ..owkokkkkokwo..
        ..owwKkkkkKwwo..
        ..owwwwwwwwwWo..
        ...owwwwwwwWo...
        ....oowwwWoo....
    ''',
    'body_down': '''
        ..oossgssgssoo..
        .ossSoggggoSsSo.
        .ossSggggggSsSo.
        .okKoggggggoKko.
        ..oggggggggGGo..
        ..oggggggggGGo..
    ''',
    'head_up': '''
        .....oooooo.....
        ....otttttTo....
        ...otttttttTo...
        ...obbbbbbbbo...
        .ootttttttttTTo.
        otttttttttttttTo
        .oooowwwwwwoooo.
        ..owwwwwwwwwWo..
        ..owwwwwwwwwWo..
        ..oWwwwwwwwWWo..
        ...oKwwwwwWKo...
        ....ooKKKKoo....
    ''',
    'body_up': '''
        ..oossgssgssoo..
        .ossSoggggoSsSo.
        .ossSoggggoSsSo.
        .okKggggggggKko.
        ..oggggggggGGo..
        ..oggggggggGGo..
    ''',
    'head_left': '''
        ......ooooo.....
        .....otttttTo...
        ....ottttttTTo..
        ....obbbbbbbbo..
        ..oottttttttTTo.
        ottttttttttttTTo
        .oooookkkwwoooo.
        ...okkkkkwwwo...
        ...okokkkwwwo...
        ..okkkkkwwwWo...
        ...owwwwwwWo....
        ....oowwwWo.....
    ''',
    'body_left': '''
        ....oossssoo....
        ...ossssssSSo...
        ...ogssSSsgGo...
        ...oggskKggGo...
        ...ogggggggGo...
        ...ogggggggGo...
    ''',
})

CHARACTERS.append({
    'name': 'GUIDE',
    'pal': [('o', OUT_)] + SKIN + [
        ('h', (96, 60, 44)), ('H', (148, 100, 68)), ('r', (232, 56, 48)),
        ('R', (160, 32, 40)), ('v', (248, 148, 48)), ('V', (208, 96, 40)),
        ('w', (248, 248, 248)), ('W', (192, 196, 212)), ('p', (64, 72, 104)),
        ('P', (40, 44, 68)), ('f', 'w'), ('F', 'W')],
    'head_down': '''
        ...o..o..o..o...
        ...ohoohoohoo...
        ..ohhhhhhhhhho..
        .ohhHhhhhhHhhho.
        .ohhhhhhhhhhhho.
        .orrrrrrrrrrrRo.
        .ohkkkkkkkkkkho.
        .ohkkokkkkokKho.
        .ohkkokkkkokKho.
        ..oKkkkkkkkKKo..
        ...ooKKKKKKoo...
    ''',
    'body_down': '''
        ..oovvwwwwvvoo..
        .okovvvwwvvvoKo.
        .okKvvvwwvvVokKo
        .okKovvvvvvVokKo
        ..oovVVVVVVVoo..
        ...owwwwwwwWo...
    ''',
    'head_up': '''
        ...o..o..o..o...
        ...ohoohoohoo...
        ..ohhhhhhhhhho..
        .ohhHhhhhhHhhho.
        .ohhhhhhhhhhhho.
        .orrrrrrrrrrrRo.
        .ohhhhhhhhhhhho.
        .ohhhhhhhhhhHho.
        .ohhhhhhhhhhHho.
        ..oKhhhhhhhhKo..
        ...ooKKKKKKoo...
    ''',
    'body_up': '''
        ..oovvvvvvvvoo..
        .okovvvvvvvvoKo.
        .okKvvVvvVvvokKo
        .okKovvvvvvVokKo
        ..oovVVVVVVVoo..
        ...owwwwwwwWo...
    ''',
    'head_left': '''
        ....o..o..o.....
        ....oho.oho.o...
        ...ohhhohhhoho..
        ..ohhhhhhhhhhho.
        ..ohhhhhhhhhhho.
        .orrrrrrrrrrRRo.
        ..okkkkkhhhhhho.
        ..okkkkkkhhhhho.
        ..okokkkkhhhho..
        .okkkkkkkkhhHo..
        ..oKkkkkkKKho...
        ...ooKKKKKoo....
    ''',
    'body_left': '''
        ....oovvvvoo....
        ...ovvvvvvvVo...
        ...ovvkKvvvVo...
        ...ovvkKvvvVo...
        ...oVVkKVVVVo...
        ....owwwwwWo....
    ''',
})

CHARACTERS.append({
    'name': 'SHOPKEEPER',
    'pal': [('o', OUT_)] + SKIN + [
        ('h', (120, 76, 48)), ('H', (80, 52, 40)), ('c', (72, 128, 224)),
        ('C', (40, 80, 168)), ('w', (248, 248, 248)), ('W', (192, 196, 216)),
        ('b', (120, 176, 240)), ('B', (56, 104, 200)), ('p', (72, 72, 88)),
        ('P', (48, 48, 60)), ('f', (104, 64, 48)), ('F', (72, 44, 40))],
    'head_down': '''
        .....oooooo.....
        ....occcccCo....
        ...occwwccccCo..
        ..occcwwcccccCo.
        ..occcccccccCo..
        .oCCCCCCCCCCCCo.
        .ohhhhhhhhhhhho.
        .ohkkkkkkkkkkho.
        .ohkkokkkkokKho.
        ..okkokkkkokKo..
        ..oKkkkkkkkKKo..
        ...ooKKKKKKoo...
    ''',
    'body_down': '''
        ..oowwwwwwwwoo..
        .owwobBbBbBowWo.
        .owWobBbBbBoWWo.
        .okKobBbBbBokKo.
        ..obBbBbBbBbBo..
        ..obBbBbBbBbBo..
        ..oooooooooooo..
    ''',
    'head_up': '''
        .....oooooo.....
        ....occcccCo....
        ...occcccccCo...
        ..occcccccccCo..
        ..occcccccccCo..
        .oCCCCCCCCCCCCo.
        .ohhhhhhhhhhhho.
        .ohhhhhhhhhhHho.
        .ohhhhhhhhhhHho.
        ..ohhhhhhhhhHo..
        ..oKhhhhhhhhKo..
        ...ooKKKKKKoo...
    ''',
    'body_up': '''
        ..oowwwwwwwwoo..
        .owwwBwwwwBwwWo.
        .owWwwBwwBwwWWo.
        .okKwwwBBwwwkKo.
        ..owwwwBBwwwWo..
        ..owwwwwwwwwWo..
        ..oooooooooooo..
    ''',
    'head_left': '''
        ......ooooo.....
        .....occcccCo...
        ....owwcccccCo..
        ...owwcccccccCo.
        ...occcccccccCo.
        .ooCCCCCCCCCCo..
        oCCCohhhhhhhhho.
        .oookkkkhhhhhho.
        ...okokkkhhhho..
        ..okkkkkkkhhHo..
        ...oKkkkkKKHo...
        ....ooKKKKoo....
    ''',
    'body_left': '''
        ....oowwwwoo....
        ...obbbwwwwWo...
        ...oBbbwwwwWo...
        ...obbkKwwwWo...
        ...oBbbbwwwWo...
        ...obbbbwwWWo...
        ....oooooooo....
    ''',
})

CHARACTERS.append({
    'name': 'HEALER', 'legs': 'bare', 'coat': 2,
    'pal': [('o', OUT_)] + SKIN + [
        ('h', (208, 204, 196)), ('H', (148, 142, 138)), ('w', (240, 232, 208)),
        ('W', (192, 176, 144)), ('r', (240, 148, 48)), ('R', (184, 88, 32)),
        ('f', (120, 84, 60)), ('F', (84, 56, 44))],
    'head_down': '''
        .....oooooo.....
        ....owwrrwWo....
        ...oowwwwwWoo...
        ..ohhhhhhhhhHo..
        .ohhhhhhhhhhhHo.
        ohhohkkkkkkhHoHo
        ohhokkkkkkkkoHHo
        ohhokokkkkokoHHo
        .ohokokkkkokoHo.
        .oHooKkkkkKooHo.
        ..oo.ooKKoo.oo..
    ''',
    'body_down': '''
        ..oowwwwwwwwoo..
        .owwWwrrwrrWwWo.
        .owwWwrrrrRWwWo.
        .okKWwwrrRwWkKo.
        ..owwwwwrwwwWo..
        ..owwwwwwwwWWo..
        ..oWWWWWWWWWWo..
        ...oooooooooo...
    ''',
    'head_up': '''
        .....oooooo.....
        ....owwwwwWo....
        ...oowwwwwWoo...
        ..ohhhhhhhhhHo..
        .ohhhhhhhhhhhHo.
        ohhohhhhhhhhHoHo
        ohhohhhhhhhhHoHo
        ohhohhhhhhhhHoHo
        .ohohhhhhhhhHoo.
        .oHooKhhhhhKoHo.
        ..oo.ooKKoo.oo..
    ''',
    'body_up': '''
        ..oowwwwwwwwoo..
        .owwwwwwwwwwWWo.
        .owWwwwrrwwwWWo.
        .okKwwwwwwwwWKo.
        ..owwwwwwwwwWo..
        ..owwwwwwwwWWo..
        ..oWWWWWWWWWWo..
        ...oooooooooo...
    ''',
    'head_left': '''
        ......ooooo.....
        .....owrrwWo....
        ....oowwwwWoo...
        ...ohhhhhhhhHo..
        ..ohhhhhhhhhhHo.
        ..okkkhhhhhooHo.
        ..okkkkkhhohhHo.
        ..okokkkhhohhHo.
        .okkkkkkkhoHHo..
        ..oKkkkkKKHooo..
        ...ooKKKKoo.....
    ''',
    'body_left': '''
        ....oowwwwoo....
        ...owrrwwwwWo...
        ...owrRwwwwWo...
        ...owwkKwwwWo...
        ...owwwwwwwWo...
        ...owwwwwwWWo...
        ...oWWWWWWWWo...
        ....oooooooo....
    ''',
})

KID_LEGS = {
    'down': ['''
        .....okoko......
        ....offoffo.....
        ....oFFoFFo.....
        .....oo.oo......
        ''', '''
        .....okoko......
        ....offokfo.....
        ....oFFooo......
        .....oo.........
        '''],
    'left': ['''
        ......okko......
        .....offfo......
        .....oFFFo......
        ......ooo.......
        ''', '''
        .....okookko....
        ....offo.ofFo...
        ....ooo...oo....
        ................
        ''', '''
        ......okKo......
        ......ofKo......
        .....oFFFo......
        ......ooo.......
        '''],
}
KID_LEGS['up'] = KID_LEGS['down']
LEGS['kid'] = KID_LEGS

CHARACTERS.append({
    'name': 'KID', 'legs': 'kid',
    'pal': [('o', OUT_)] + SKIN + [
        ('h', (160, 96, 52)), ('H', (112, 64, 40)), ('y', (248, 216, 64)),
        ('Y', (216, 160, 40)), ('s', (80, 120, 208)), ('S', (48, 80, 160)),
        ('f', (232, 72, 64)), ('F', (160, 44, 48))],
    'head_down': '''
        ....o.oo.o......
        ...ohohhohoo....
        ..ohhhhhhhhHo...
        ..ohhhhhhhhhHo..
        ..ohhkhhkhhhHo..
        ..ohkkkkkkkkho..
        ..ohkokkkokKHo..
        ..ookokkkokKoo..
        ...oKkkkkkKKo...
        ....ooKKKKoo....
    ''',
    'body_down': '''
        ...ooyyyyyoo....
        ..okoyyyyyYoko..
        ..okoyyyyYYoKo..
        ...osssssSSo....
        ...ossSossSo....
    ''',
    'head_up': '''
        ....o.oo.o......
        ...ohohhohoo....
        ..ohhhhhhhhHo...
        ..ohhhhhhhhhHo..
        ..ohhhhhhhhhHo..
        ..ohhhhhhhhhHo..
        ..ohhhhhhhhHHo..
        ..oohhhhhhhHoo..
        ...oKhhhhhhKo...
        ....ooKKKKoo....
    ''',
    'body_up': '''
        ...ooyyyyyoo....
        ..okoyyyyyYoko..
        ..okoyyyyYYoKo..
        ...osssssSSo....
        ...ossSossSo....
    ''',
    'head_left': '''
        .....o.o.oo.....
        ....ohohohhoo...
        ...ohhhhhhhhHo..
        ...ohhhhhhhhhHo.
        ...okkhhhhhhhHo.
        ...okkkkkhhhhHo.
        ...okokkkhhhHo..
        ..okkkkkkkhHHo..
        ...oKkkkkKKHo...
        ....ooKKKKoo....
    ''',
    'body_left': '''
        .....ooyyyo.....
        ....oyyyyyYo....
        ....oyykKyYo....
        ....ossssSSo....
        .....osssSo.....
    ''',
})


def char_variant(base_name, name, **pal):
    """A recoloured copy of an existing character (palette keys replaced)."""
    base = [c for c in CHARACTERS if c['name'] == base_name][0]
    d = dict(base)
    d['name'] = name
    d['pal'] = [(k, pal.get(k, v)) for (k, v) in base['pal']]
    CHARACTERS.append(d)


char_variant('HEALER', 'GRAN', h=(236, 236, 240), H=(176, 176, 188), w=(176, 152, 208),
             W=(128, 104, 168), r=(248, 216, 120), R=(200, 160, 72))
char_variant('PROFESSOR', 'ELDER', s=(152, 104, 64), S=(104, 68, 44), p=(96, 88, 80),
             P=(64, 60, 56))
char_variant('PROFESSOR', 'SCIENTIST', h=(64, 48, 56), H=(40, 32, 40), s=(96, 144, 216),
             S=(56, 96, 168))
char_variant('GUIDE', 'WARDEN_A', r=(64, 144, 200), R=(40, 96, 152), v=(248, 216, 96),
             V=(200, 160, 56), h=(40, 36, 44), H=(80, 72, 84))
char_variant('GUIDE', 'WARDEN_B', r=(152, 88, 200), R=(104, 56, 152), v=(120, 200, 120),
             V=(72, 144, 88), h=(216, 168, 88), H=(160, 112, 56))
char_variant('GARDENER', 'FISHER', t=(96, 136, 200), T=(56, 88, 152), g=(208, 176, 96),
             G=(152, 120, 64))
char_variant('GARDENER', 'HERMIT', t=(120, 112, 96), T=(84, 76, 64), g=(88, 104, 88),
             G=(56, 68, 60), b=(96, 88, 120))
char_variant('BAKER', 'VILLAGER', h=(56, 44, 40), H=(32, 28, 28), d=(120, 176, 128),
             D=(72, 128, 88))
char_variant('KID', 'KID_B', h=(232, 196, 96), H=(184, 140, 56), y=(232, 104, 136),
             Y=(176, 64, 96), s=(96, 176, 112), S=(56, 128, 80))


def char_palette(ch):
    """Returns (char->index map, 16-entry RGB15 list)."""
    idx, pal = {}, [0] * 16
    n = 1
    for (k, v) in ch['pal']:
        if isinstance(v, str):
            idx[k] = idx[v]
            continue
        idx[k] = n
        pal[n] = c15(v)
        n += 1
    if n > 16:
        raise ValueError('%s: too many colors' % ch['name'])
    return idx, pal


def char_gfx(ch):
    """Returns (frames: 9 x 8 tiles x 8 u32, palette)."""
    idx, pal = char_palette(ch)
    frames = []
    for rows in char_frames(ch):
        tiles = []
        for ty in range(4):
            for tx in range(2):
                t = []
                for y in range(8):
                    for x in range(8):
                        c = rows[ty * 8 + y][tx * 8 + x]
                        if c != '.' and c not in idx:
                            raise KeyError('%s: color %r' % (ch['name'], c))
                        t.append(0 if c == '.' else idx[c])
                tiles.append(pack4(t))
        frames.append(tiles)
    return frames, pal


def render_characters(path, chars, item=None):
    S = 4
    cw, chh = 20, 36
    extra = 20 if item else 0
    cv = Canvas(9 * cw + 4, len(chars) * chh + 4 + extra, c15_to_rgb(c15(C['g_base'])))
    for r, (frames, pal) in enumerate(chars):
        for f in range(9):
            cv.sprite(frames[f], pal, 4 + f * cw, 4 + r * chh, 2, 4)
    if item:
        cv.sprite(item[0], item[1], 4, 4 + len(chars) * chh, 2, 2)
    cv.save(path, S)


# =====================================================================
# PREVIEW RENDERING (decodes the encoded data)
# =====================================================================

def autotile_variants(same, x, y):
    """Quadrant variants for cell (x, y); same(x, y) tests the region."""
    out = []
    for c in range(4):
        sx = -1 if (c & 1) == 0 else 1
        sy = -1 if (c >> 1) == 0 else 1
        h, v, d = same(x + sx, y), same(x, y + sy), same(x + sx, y + sy)
        if h and v:
            out.append(0 if d else 1)
        elif v:
            out.append(2)
        elif h:
            out.append(3)
        else:
            out.append(4)
    return out


# 3x5 label font for preview sheets
LABEL_FONT = {
    'A': '010101111101101', 'B': '110101110101110', 'C': '011100100100011',
    'D': '110101101101110', 'E': '111100110100111', 'F': '111100110100100',
    'G': '011100101101011', 'H': '101101111101101', 'I': '111010010010111',
    'J': '001001001101010', 'K': '101101110101101', 'L': '100100100100111',
    'M': '101111111101101', 'N': '110101101101101', 'O': '010101101101010',
    'P': '110101110100100', 'Q': '010101101110011', 'R': '110101110101101',
    'S': '011100010001110', 'T': '111010010010010', 'U': '101101101101111',
    'V': '101101101101010', 'W': '101101111111101', 'X': '101101010101101',
    'Y': '101101010010010', 'Z': '111001010100111', '_': '000000000000111',
    '0': '111101101101111', '1': '010110010010111', '2': '110001010100111',
    '3': '110001010001110', '4': '101101111001001', '5': '111100110001110',
    '6': '011100110101010', '7': '111001010010010', '8': '010101010101010',
    '9': '010101011001110', ' ': '000000000000000', '.': '000000000000010',
}


def draw_label(cv, x, y, text, rgb=(255, 255, 255)):
    for i, ch in enumerate(text.upper()):
        bits = LABEL_FONT.get(ch, LABEL_FONT[' '])
        for k, b in enumerate(bits):
            if b == '1':
                cv.put(x + i * 4 + k % 3, y + k // 3, rgb)


def ground_names(tsout):
    return [n for i, n in enumerate(tsout['terrain']) if tsout['mflags'][i] & MF_GROUND]


# ---------------------------------------------------------------------
# Art lint: objects must never carry baked-in ground (docs/EXPANSION.md
# 10.1). An object (overlay terrain or decor) whose outer border is mostly
# covered by the tileset's ground colours has a background painted in: it
# would show as a box on any other ground.
# ---------------------------------------------------------------------

def tile_colors(ts, ents_list):
    cols = set()
    pal = ts.banks
    for ents in ents_list:
        for e in ents:
            if not e:
                continue
            t, b = e & 1023, e >> 12
            for i in ts.tiles[t]:
                if i:
                    cols.add(pal[b][i - 1])
    return cols


def lint_image(img, ground_cols, what):
    """img: Img of one object (frame 0). Raise if its border is ground."""
    border = [(x, 0) for x in range(img.w)] + [(x, img.h - 1) for x in range(img.w)] + \
             [(0, y) for y in range(1, img.h - 1)] + [(img.w - 1, y) for y in range(1, img.h - 1)]
    ground = sum(1 for (x, y) in border if img.p[y][x] in ground_cols)
    if ground * 100 >= 55 * len(border):
        raise ValueError('art lint: %s has ground baked into its background (%d of %d border '
                         'pixels are ground colours). Draw it on transparency; the engine puts '
                         'the real ground underneath.' % (what, ground, len(border)))
    for cy in range(img.h // 16):
        for cx in range(img.w // 16):
            pix = [img.p[cy * 16 + y][cx * 16 + x] for y in range(16) for x in range(16)]
            if None not in pix and sum(1 for c in pix if c in ground_cols) * 2 >= len(pix):
                raise ValueError('art lint: %s cell %d,%d is a solid square of ground colours '
                                 '(baked background).' % (what, cx, cy))


def lint_objects(sets, dec):
    for sname in TS_NAMES:
        out = sets[sname]
        ts = out['ts']
        gids = [i for i, f in enumerate(out['mflags']) if f & MF_GROUND]
        if 'art2' in out:
            # tiles2 sets share material ramps between floors and props (a
            # plank floor and a crate): lint against the default ground only
            gids = [out['ground_default']]
        ground_cols = tile_colors(ts, [out['meta_b'][i] for i in gids])
        for i, n in enumerate(out['terrain']):
            if not (out['mflags'][i] & MF_OVERLAY):
                continue
            img = Img(16, 16)
            for ents in (out['meta_b'][i], out['meta_t'][i]):
                for q, e in enumerate(ents):
                    if not e:
                        continue
                    t, hf, vf, b = e & 1023, (e >> 10) & 1, (e >> 11) & 1, e >> 12
                    idx = ts.tiles[t]
                    for y in range(8):
                        for x in range(8):
                            k = idx[(7 - y if vf else y) * 8 + (7 - x if hf else x)]
                            if k:
                                img.p[(q >> 1) * 8 + y][(q & 1) * 8 + x] = ts.banks[b][k - 1]
            lint_image(img, ground_cols, '%s overlay terrain %s' % (sname, n))
        for d in dec['kinds']:
            if (sname, d.name) in dec['defs'] and not getattr(d, 'ground_ok', False) and \
                    d.name not in out.get('art2', {}).get('ground_ok', ()):
                lint_image(dec['art'][(sname, d.name)].frames[0], ground_cols, '%s decor %s' % (sname, d.name))


def ground_meta(tsout, name):
    return tsout['meta_b'][tsout['terrain'].index(name)]


def render_decor_sheet(tsout, sname, dec, path):
    """Every decor kind of one tileset over its ground, labelled."""
    ts = tsout['ts']
    pals = ts.pal15()
    items = [d for d in dec['kinds'] if (sname, d.name) in dec['defs']]
    grounds = ground_names(tsout)[:2] * 2
    # a tile block after the terrain tiles, like the game does
    tiles = list(ts.tiles)
    col_w = 6 * 16
    cols = 6
    rows_h = []
    cells = []
    for i, d in enumerate(items):
        cells.append(d)
    nrows = (len(cells) + cols - 1) // cols
    cell_h = 5 * 16
    cv = Canvas(cols * col_w, nrows * cell_h, bg=(24, 24, 32))
    for i, d in enumerate(cells):
        cx0, cy0 = (i % cols) * col_w, (i // cols) * cell_h
        dd = dec['defs'][(sname, d.name)]
        base = len(tiles)
        # append this kind's frame-0 tiles
        words = dec['words'][dd['tile_first'] * 8:(dd['tile_first'] + dd['tile_count']) * 8]
        loc = []
        for t in range(dd['tile_count']):
            w8 = words[t * 8:t * 8 + 8]
            loc.append(tuple((w8[y] >> (4 * x)) & 15 for y in range(8) for x in range(8)))
        alltiles = tiles + loc
        g = grounds[i % 2]
        for my in range(4):
            for mx in range(6):
                cv.meta(alltiles, pals, ground_meta(tsout, g), cx0 + mx * 16, cy0 + 8 + my * 16)
        ox = cx0 + (6 - d.w) * 8
        oy = cy0 + 8 + (4 - d.h) * 8 + 4
        for k in range(d.w * d.h):
            ents = [decor_entry_abs(e, base) for e in dec['meta'][dd['meta_first'] + k]]
            cx, cy = k % d.w, k // d.w
            cv.meta(alltiles, pals, ents, ox + cx * 16, oy + cy * 16, transparent=True)
        draw_label(cv, cx0 + 2, cy0 + 1, d.name[:23])
    cv.save(path, 2)


def render_map_sample(tsout, dec, sname, rows, key, stamps, decor, path, sprites=()):
    """A little map: rows of terrain chars (key: char -> terrain name or
    'PATH'/'WATER'), stamps [(name, x, y)], decor [(name, x, y, hflip)]."""
    ts = tsout['ts']
    pals = ts.pal15()
    H, W = len(rows), len(rows[0])
    grid = [list(r) for r in rows]
    tiles = list(ts.tiles)
    bases = {}
    for (name, x, y, fl) in decor:
        if name in bases:
            continue
        dd = dec['defs'][(sname, name)]
        words = dec['words'][dd['tile_first'] * 8:(dd['tile_first'] + dd['tile_count']) * 8]
        bases[name] = len(tiles)
        for t in range(dd['tile_count']):
            w8 = words[t * 8:t * 8 + 8]
            tiles.append(tuple((w8[y] >> (4 * x)) & 15 for y in range(8) for x in range(8)))
    cv = Canvas(W * 16, H * 16)
    ids = {n: i for i, n in enumerate(tsout['terrain'])}
    for (name, sid, cw, chh, doc) in tsout['stamps']:
        ids[name] = sid

    def same(ch):
        def f(x, y):
            if not (0 <= y < H and 0 <= x < W):
                return True
            return grid[y][x] == ch
        return f
    for y in range(H):
        for x in range(W):
            ch = grid[y][x]
            k = key.get(ch)
            if k in ('PATH', 'WATER'):
                q = tsout['path_q'] if k == 'PATH' else tsout['water_q']
                vs = autotile_variants(same(ch), x, y)
                for c in range(4):
                    cv.entry(tiles, pals, q[c][vs[c]], x * 16 + 8 * (c & 1), y * 16 + 8 * (c >> 1), False)
            elif k:
                cv.meta(tiles, pals, tsout['meta_b'][ids[k]], x * 16, y * 16)
    for (name, sx, sy) in stamps:
        st = [s for s in tsout['stamps'] if s[0] == name][0]
        _, sid, cw, chh, _ = st
        for my in range(chh):
            for mx in range(cw):
                cv.meta(tiles, pals, tsout['meta_b'][sid + my * cw + mx], (sx + mx) * 16, (sy + my) * 16)
    tops = []
    for (name, dx, dy, fl) in decor:
        dd = dec['defs'][(sname, name)]
        for k in range(dd['w'] * dd['h']):
            cx, cy = k % dd['w'], k // dd['w']
            src = cy * dd['w'] + (dd['w'] - 1 - cx if fl else cx)
            ents = [decor_entry_abs(e, bases[name]) for e in dec['meta'][dd['meta_first'] + src]]
            if fl:
                ents = [ents[1] ^ (1 << 10) if ents[1] else 0, ents[0] ^ (1 << 10) if ents[0] else 0,
                        ents[3] ^ (1 << 10) if ents[3] else 0, ents[2] ^ (1 << 10) if ents[2] else 0]
            if dd['top'] & (1 << src):
                tops.append((ents, (dx + cx) * 16, (dy + cy) * 16))
            else:
                cv.meta(tiles, pals, ents, (dx + cx) * 16, (dy + cy) * 16, transparent=True)
    for (gfx, pal, px, py, fl) in sprites:
        cv.sprite(gfx, pal, px, py, 2, 4, hflip=fl)
    for y in range(H):
        for x in range(W):
            k = key.get(grid[y][x])
            if k and k not in ('PATH', 'WATER') and k in ids and tsout['meta_t'][ids[k]] != [0, 0, 0, 0]:
                cv.meta(tiles, pals, tsout['meta_t'][ids[k]], x * 16, y * 16, transparent=True)
    for (ents, px, py) in tops:
        cv.meta(tiles, pals, ents, px, py, transparent=True)
    cv.save(path, 2)


TOWN_SAMPLE = [
    'TTTTTTTTTTTTTTTTTTTTTTTTT',
    'bbbbbbbbbbbbbbbbbbbbbbbbb',
    '.........................',
    '.........................',
    '.........................',
    '.........................',
    '.r.......,.............y.',
    '..rr.....................',
    '...PPPPPPPPPPPPPPPPPPPP..',
    '.........PP..............',
    '.........PP...cccccc.....',
    '...SSSS..PP...vc..cv.....',
    '...SSSS..PP...vc..cv.....',
    '...SSSS..PP...cccccc.....',
    '.WWW.....PP.....GGGG.....',
    'WWWWW....PP.....GGGGG....',
    'TTTTTTTTTPPTTTTTTTTTTTTTT',
    'bbbbbbbbbPPbbbbbbbbbbbbbb',
]
TOWN_SAMPLE_KEY = {
    'T': 'TREE_TOP', 'b': 'TREE_BOTTOM', '.': 'GRASS', ',': 'GRASS2',
    'G': 'TALLGRASS', 'r': 'FLOWER_RED', 'y': 'FLOWER_YELLOW', 'S': 'STONE',
    'c': 'COURT', 'v': 'COURT_LINE_V', 'P': 'PATH', 'W': 'WATER',
}
TOWN_SAMPLE_STAMPS = [('HOUSE_RED', 1, 2), ('LAB', 7, 1), ('HEAL', 15, 3), ('COURT_CIRCLE', 16, 11)]
TOWN_SAMPLE_DECOR = [('LAMP', 8, 8, 0), ('SIGNPOST', 12, 9, 0), ('ROCK', 22, 12, 0),
                     ('BUSH', 21, 6, 0), ('MAILBOX', 6, 6, 0), ('FENCE', 14, 9, 0),
                     ('FENCE', 15, 9, 0), ('FENCE_END', 16, 9, 0)]

WILD_SAMPLE = [
    'ppppppppppppppppppppppppp',
    'qqqqqqqqqqqqqqqqqqqqqqqqq',
    'ffffffff...,,,,,,....GGGG',
    'ffFfffff...,,,,,,....GGGG',
    'fffffff....PPPPPPP...GGGG',
    'LLLLLLL....P.....P.......',
    '...........P..r..P..ssss.',
    '..,,,,.....P.....P..sWWs.',
    '..,,,,.....PPPPPPP..sWWs.',
    '..........y.........RRRR.',
    'TTTTTTTTTTTTTTTTTTTTTTTTT',
    'bbbbbbbbbbbbbbbbbbbbbbbbb',
]
WILD_SAMPLE_KEY = {
    'T': 'TREE_TOP', 'b': 'TREE_BOTTOM', 'p': 'PINE_TOP', 'q': 'PINE_BOTTOM',
    '.': 'GRASS', ',': 'TALLGRASS', 'f': 'FOREST', 'F': 'FOREST2', 'L': 'LEDGE',
    's': 'SAND', 'W': 'WATER', 'R': 'REEDS', 'P': 'PATH', 'r': 'FLOWER_RED',
    'y': 'FLOWER_YELLOW', 'G': 'TALLGRASS',
}

INTERIOR_SAMPLE = [
    '#WWnWWkWWWnWWpWW#',
    '#wwwwwwwwwwwwwww#',
    '#.......::::::::#',
    '#.......::<==>::#',
    '#.......::::::::#',
    '#.......::::::::#',
    '#.......::::::::#',
    '#.......::::::::#',
    '#.......::::::::#',
    '#.......D:::::::#',
]
INTERIOR_SAMPLE_KEY = {
    '#': 'VOID', 'W': 'WALL_TOP', 'w': 'WALL', 'n': 'WINDOW', 'k': 'WALL_CLOCK',
    'p': 'PAINTING', '.': 'FLOOR', ':': 'FLOOR2', 'D': 'DOORMAT', '<': 'COUNTER_L',
    '=': 'COUNTER', '>': 'COUNTER_R',
}
INTERIOR_SAMPLE_DECOR = [('BOOKSHELF', 1, 1, 0), ('STOVE', 4, 1, 0), ('TV', 6, 2, 0),
                         ('BED', 1, 5, 0), ('TABLE', 3, 5, 0), ('CHAIR', 3, 4, 0),
                         ('CHAIR', 4, 4, 0), ('PLANT', 7, 6, 0), ('SHOP_SHELF', 9, 1, 0),
                         ('HEAL_MACHINE', 12, 1, 0), ('LAB_MACHINE', 14, 1, 0), ('PC', 15, 6, 0)]


# =====================================================================
# HEADER OUTPUT
# =====================================================================

def fmt_u32(words, per=8, indent='    '):
    lines = []
    for i in range(0, len(words), per):
        lines.append(indent + ', '.join('0x%08X' % w for w in words[i:i + per]) + ',')
    return '\n'.join(lines)


def fmt_u16(vals, per=8, indent='    '):
    lines = []
    for i in range(0, len(vals), per):
        lines.append(indent + ', '.join('0x%04X' % v for v in vals[i:i + per]) + ',')
    return '\n'.join(lines)


def meta_names(terrain, stamps, tag):
    names = ['MT_%s_%s' % (tag, n) for n in terrain]
    for (name, sid, cw, chh, doc) in stamps:
        for my in range(chh):
            for mx in range(cw):
                names.append('%s (%d,%d)' % (name, mx, my))
    return names


LG_NONE, LG_SIMPLE, LG_VARIANT, LG_PATH, LG_WATER = range(5)


def emit_tileset(o, out, docs):
    prefix, PREFIX, tag = out['name'], out['name'].upper(), out['tag']
    ts = out['ts']
    o.append('enum {')
    for n in out['terrain']:
        doc = docs.get(n)
        o.append('  MT_%s_%s,%s' % (tag, n, ('  /* %s */' % doc) if doc else ''))
    o.append('  MT_%s_TERRAIN_COUNT' % tag)
    o.append('};')
    last = len(out['terrain'])
    for (name, sid, cw, chh, doc) in out['stamps']:
        o.append('#define MT_%s_%-14s %3d  /* %dx%d %s */' % (tag, name, sid, cw, chh, doc))
        o.append('#define MT_%s_%s_W %d' % (tag, name, cw))
        o.append('#define MT_%s_%s_H %d' % (tag, name, chh))
        last = sid + cw * chh
    o.append('#define MT_%s_COUNT %d' % (PREFIX, last))
    o.append('')
    words = []
    for t in ts.tiles:
        words.extend(pack4(t))
    o.append('#define %s_TILE_COUNT %d' % (PREFIX, len(ts.tiles)))
    o.append('static const u32 %s_tiles[%s_TILE_COUNT * 8] = {' % (prefix, PREFIX))
    o.append(fmt_u32(words))
    o.append('};')
    o.append('static const u16 %s_palettes[8][16] = {' % prefix)
    for row in ts.pal15():
        o.append('    {' + ', '.join('0x%04X' % v for v in row) + '},')
    o.append('};')
    names = meta_names(out['terrain'], out['stamps'], tag)
    for (arr, label) in ((out['meta_b'], 'bottom'), (out['meta_t'], 'top')):
        o.append('static const u16 %s_meta_%s[MT_%s_COUNT][4] = {' % (prefix, label, PREFIX))
        for i, e in enumerate(arr):
            o.append('    {0x%04X, 0x%04X, 0x%04X, 0x%04X}, /* %s */' %
                     (e[0], e[1], e[2], e[3], names[i]))
        o.append('};')
    o.append('static const u16 %s_attr[MT_%s_COUNT] = {' % (prefix, PREFIX))
    for i, a in enumerate(out['attr']):
        flags = '|'.join('A_' + ATTR_NAMES[b] for b in range(16) if a & (1 << b)) or '0'
        o.append('    %s, /* %s */' % (flags, names[i]))
    o.append('};')
    o.append('static const u8 %s_mflags[MT_%s_COUNT] = {' % (prefix, PREFIX))
    o.append('    ' + ', '.join(str(f) for f in out['mflags']) + ',')
    o.append('};')
    if 'path_q' in out:
        for (nm, q) in (('path', out['path_q']), ('water', out['water_q'])):
            o.append('static const u16 %s_%s_quads[4][5] = {' % (prefix, nm))
            for c in range(4):
                o.append('    {' + ', '.join('0x%04X' % v for v in q[c]) + '},')
            o.append('};')
    if out['blends']:
        o.append('static const u8 %s_blend_of[MT_%s_COUNT] = {' % (prefix, PREFIX))
        o.append('    ' + ', '.join(str(b) for b in out['blend_of']) + ',')
        o.append('};')
        o.append('static const u8 %s_blend_outer[MT_%s_COUNT] = {' % (prefix, PREFIX))
        o.append('    ' + ', '.join(str(b) for b in out['blend_outer']) + ',')
        o.append('};')
        o.append('static const u16 %s_blend_quads[%d][2][4][5] = {' % (prefix, len(out['blends'])))
        for bl in out['blends']:
            o.append('    { /* %s into %s */' % ('/'.join(bl['inner']), '/'.join(bl['outer'])))
            for q in bl['q']:
                o.append('        {')
                for c in range(4):
                    o.append('            {' + ', '.join('0x%04X' % v for v in q[c]) + '},')
                o.append('        },')
            o.append('    },')
        o.append('};')
    if out.get('masses'):
        ids = {nm: i for i, nm in enumerate(out['terrain'])}
        mass_of = [0] * len(out['meta_b'])
        pieces, picks = [], []
        for gi, m in enumerate(out['masses']):
            for nm in m['members']:
                mass_of[ids[nm]] = gi + 1
            base = len(pieces)
            pieces.extend(m['pieces'])
            picks.append([base + p for p in m['pick']])
        o.append('static const u8 %s_mass_of[MT_%s_COUNT] = {' % (prefix, PREFIX))
        o.append('    ' + ', '.join(str(b) for b in mass_of) + ',')
        o.append('};')
        o.append('static const u16 %s_mass_pick[%d][256] = {' % (prefix, len(picks)))
        for gi, pk in enumerate(picks):
            o.append('    { /* %s */' % out['masses'][gi]['group'])
            for r in range(0, 256, 16):
                o.append('        ' + ', '.join(str(v) for v in pk[r:r + 16]) + ',')
            o.append('    },')
        o.append('};')
        o.append('static const u16 %s_mass_meta[%d][4] = {' % (prefix, len(pieces)))
        for e in pieces:
            o.append('    {0x%04X, 0x%04X, 0x%04X, 0x%04X},' % tuple(e))
        o.append('};')
    if out.get('path_alt_q'):
        o.append('static const u16 %s_path_alt_quads[4][5] = {' % prefix)
        for c in range(4):
            o.append('    {' + ', '.join('0x%04X' % v for v in out['path_alt_q'][c]) + '},')
        o.append('};')
        ids = {nm: i for i, nm in enumerate(out['terrain'])}
        alt_of = [0] * len(out['meta_b'])
        for nm in out['path_alt_names']:
            alt_of[ids[nm]] = 1
        o.append('static const u8 %s_path_alt_of[MT_%s_COUNT] = {' % (prefix, PREFIX))
        o.append('    ' + ', '.join(str(b) for b in alt_of) + ',')
        o.append('};')
    # tile animations: one flat block of frames x count tiles each
    anim_rows = []
    for k, (first, frames, period) in enumerate(out['anims']):
        o.append('static const u32 %s_anim%d[%d * %d * 8] = {' % (prefix, k, len(frames), len(frames[0])))
        for f in frames:
            o.append(fmt_u32([w for t in f for w in pack4(t)]))
        o.append('};')
        anim_rows.append('{ %d, %d, %d, %d, %s_anim%d }' % (first, len(frames[0]), len(frames),
                                                           period, prefix, k))
    o.append('static const TileAnim %s_anims[%d] = { %s };' %
             (prefix, max(1, len(anim_rows)), ', '.join(anim_rows) or '{ 0, 0, 0, 0, 0 }'))
    ids = out['ids']
    for line in out.get('c_extra', []):
        o.append(line)
    o.append('static const LegendEntry %s_legend[96] = {' % prefix)
    for ch in range(32, 128):
        spec = out['legend'].get(chr(ch))
        if spec is None:
            continue
        cname = "'\\\\'" if chr(ch) == '\\' else ("'\\''" if chr(ch) == "'" else "'%s'" % chr(ch))
        if spec == 'PATH':
            o.append('    [%s - 32] = { LG_PATH, 0, {0}, {0} },' % cname)
        elif spec == 'WATER':
            o.append('    [%s - 32] = { LG_WATER, 0, {0}, {0} },' % cname)
        else:
            kind = 'LG_SIMPLE' if len(spec) == 1 else 'LG_VARIANT'
            ws = ', '.join(str(w) for (_, w) in spec)
            vs = ', '.join('MT_%s_%s' % (tag, t) for (t, _) in spec)
            o.append('    [%s - 32] = { %s, %d, { %s }, { %s } },' % (cname, kind, len(spec), ws, vs))
    o.append('};')
    if 'elev' in out:
        ea = out['elev']

        def arr(v):
            if isinstance(v, list):
                return '{' + ', '.join(arr(x) for x in v) + '}'
            return '0x%04X' % v
        o.append('static const ElevArt %s_elev = {' % prefix)
        for k in ('face', 'rim', 'shadow', 'stairs', 'deck_h', 'deck_v', 'mouth', 'ledge'):
            o.append('    %s, /* %s */' % (arr(ea[k]), k))
        o.append('};')
    o.append('')


def emit_tileset_table(o, sets):
    o.append('static const TilesetDef TILESETS[TS_COUNT] = {')
    for n in TS_NAMES:
        out = sets[n]
        P = n.upper()
        bd = out['backdrop']
        if bd == 'ground':
            bdc = out['ts'].pal15()[0][1]
        else:
            bdc = c15(bd)
        has_q = 'path_q' in out
        o.append('    [TS_%s] = { "%s", %s_tiles, %s_TILE_COUNT, MT_%s_COUNT, %s_palettes,' % (
            P, n, n, P, P, n))
        o.append('        %s_meta_bottom, %s_meta_top, %s_attr, %s_mflags,' % (n, n, n, n))
        o.append('        %s, %s, %s_anims, %d, %s_legend, \'%s\', %d, %d, 0x%04X, %s,' % (
            ('%s_path_quads' % n) if has_q else '0', ('%s_water_quads' % n) if has_q else '0',
            n, len(out['anims']), n, out['legend_default'], out['oob'], out['ground_default'], bdc,
            ('&%s_elev' % n) if 'elev' in out else '0'))
        if out['blends']:
            o.append('        %s_blend_of, %s_blend_outer, %s_blend_quads,' % (n, n, n))
        else:
            o.append('        0, 0, 0,')
        if out.get('masses'):
            o.append('        %s_mass_of, %s_mass_pick, %s_mass_meta,' % (n, n, n))
        else:
            o.append('        0, 0, 0,')
        if out.get('path_alt_q'):
            o.append('        %s_path_alt_quads, %s_path_alt_of },' % (n, n))
        else:
            o.append('        0, 0 },')
    o.append('};')
    o.append('')


# =====================================================================
# ASSET VIEWER MAPS (docs/EXPANSION.md 10.1): generated for every tileset,
# so every terrain tile, overlay, building and decor kind can be walked
# around in the game (DEBUG menu on the title screen: hold SELECT, press
# START). Objects stand on a checkerboard of the tileset's grounds, so a
# baked-in background shows at once. Written to src/game/world/debug/.
# =====================================================================

VIEW_W = 40
VIEW_PEN_H = 6


def viewer_pages(sname, out, dec):
    """-> list of pages: dict(w, h, cells, ground, decor[(kind, x, y)], name)."""
    ids = out['ids']
    grounds = [i for i, f in enumerate(out['mflags']) if f & MF_GROUND][:3] or [out['ground_default']]
    overlay = [i for i, f in enumerate(out['mflags']) if f & MF_OVERLAY and i < len(out['terrain'])]
    plain = [i for i, n in enumerate(out['terrain'])
             if not (out['mflags'][i] & MF_OVERLAY)]
    kinds = [d for d in dec['kinds'] if (sname, d.name) in dec['defs']]
    budget = 768 - min(len(out['ts'].tiles), 512)
    # split decor into pages that fit the scene tile budget
    decor_pages, cur, used = [], [], 0
    for d in kinds:
        tc = dec['defs'][(sname, d.name)]['tile_count']
        if cur and used + tc > budget:
            decor_pages.append(cur)
            cur, used = [], 0
        cur.append(d)
        used += tc
    decor_pages.append(cur)
    pages = []
    for pi, dpage in enumerate(decor_pages):
        items = []   # (kind, w, h, payload)
        if pi == 0:
            for i in plain:
                items.append(('cell', 1, 1, i))
            # overlays: tops above bottoms, each over every ground
            names = out['terrain']
            pairs = []
            for i in overlay:
                n = names[i]
                if n.endswith('_TOP') and n[:-4] + '_BOTTOM' in ids:
                    pairs.append((i, ids[n[:-4] + '_BOTTOM']))
                elif not n.endswith('_BOTTOM'):
                    pairs.append((i, None))
            for (top, bot) in pairs:
                for g in grounds:
                    items.append(('tree', 1, 2 if bot is not None else 1, (top, bot, g)))
            for (nm, sid, cw, chh, doc) in out['stamps']:
                items.append(('stamp', cw, chh, (sid, cw, chh)))
            if 'path_q' in out:
                items.append(('path', 4, 3, None))
                items.append(('water', 4, 3, None))
        for d in dpage:
            items.append(('decor', d.w, d.h, d))
        # shelf packing with one-cell gaps
        x, y, row_h = 1, 1, 0
        placed = []
        for it in items:
            kind, w, h, pay = it
            if x + w + 1 > VIEW_W:
                x, y, row_h = 1, y + row_h + 1, 0
            placed.append((it, x, y))
            x += w + 1
            row_h = max(row_h, h)
        H = min(64, y + row_h + 2 + VIEW_PEN_H)
        cells = [[None] * VIEW_W for _ in range(H)]
        ground = [[0] * VIEW_W for _ in range(H)]
        for yy in range(H):
            for xx in range(VIEW_W):
                g = grounds[((xx // 4) + (yy // 4)) % len(grounds)]
                cells[yy][xx] = g
        decor = []
        for (it, px, py) in placed:
            kind, w, h, pay = it
            if kind == 'cell':
                cells[py][px] = pay
            elif kind == 'tree':
                top, bot, g = pay
                cells[py][px] = top
                ground[py][px] = g
                if bot is not None:
                    cells[py + 1][px] = bot
                    ground[py + 1][px] = g
            elif kind == 'stamp':
                sid, cw, chh = pay
                for yy in range(chh):
                    for xx in range(cw):
                        cells[py + yy][px + xx] = sid + yy * cw + xx
            elif kind in ('path', 'water'):
                v = 0xFFF0 if kind == 'path' else 0xFFF1
                for yy in range(h):
                    for xx in range(w):
                        if kind == 'path' and yy == 1 or kind == 'water':
                            cells[py + yy][px + xx] = v
            else:
                decor.append((pay.name, px, py))
        pages.append(dict(w=VIEW_W, h=H, cells=cells, ground=ground, decor=decor,
                          name='VIEW %s %d/%d' % (sname.upper(), pi + 1, len(decor_pages))))
    return pages


def write_viewer_maps(sets, dec, root):
    d = os.path.join(root, 'src', 'game', 'world', 'debug')
    ids, maps, data = [], [], []
    head = '/* GENERATED by tools/gen_field_gfx.py (asset viewer maps). Do not edit. */\n'
    for sname in TS_NAMES:
        out = sets[sname]
        for k, pg in enumerate(viewer_pages(sname, out, dec)):
            tag = 'VIEW_%s_%d' % (sname.upper(), k + 1)
            ids.append('    MAP_%s,\n' % tag)
            flat = [v for row in pg['cells'] for v in row]
            gflat = [v for row in pg['ground'] for v in row]
            data.append('static const u16 %s_CELLS[%d] = {\n%s\n};\n' % (tag, len(flat), fmt_u16(flat)))
            data.append('static const u16 %s_GROUND[%d] = {\n%s\n};\n' % (tag, len(gflat), fmt_u16(gflat)))
            if pg['decor']:
                data.append('static const DecorPlace %s_DECOR[] = {\n%s\n};\n' % (
                    tag, '\n'.join('    DP(%s, %d, %d),' % (n, x, y) for (n, x, y) in pg['decor'])))
                dref = '%s_DECOR, NDEC(%s_DECOR)' % (tag, tag)
            else:
                dref = '0, 0'
            flags = 'MF_DEBUG | MF_NIGHTLESS' + (' | MF_OUTDOOR' if out['backdrop'] == 'ground' else '')
            maps.append('    [MAP_%s] = { %d, %d, TS_%s, SC_MEADOW, 0, 0, 0, %s, "%s", ZONE_NONE, %s,\n'
                        '        NO_LINKS, 0, 0, 0, %s_CELLS, %s_GROUND },\n' % (
                            tag, pg['w'], pg['h'], sname.upper(), dref, pg['name'], flags, tag, tag))
    open(os.path.join(d, 'ids.inc'), 'w').write(head + ''.join(ids))
    open(os.path.join(d, 'maps.inc'), 'w').write(head + ''.join(maps))
    open(os.path.join(d, 'data.h'), 'w').write(head + '\n'.join(data))
    return len(ids)


def c_string(text):
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'


def write_header(sets, dec, chars, item, emotes, path):
    o = []
    A = o.append
    A('/* gfx_field.h -- GENERATED by tools/gen_field_gfx.py. Do not edit.')
    A(' *')
    A(' * Overworld graphics: village, route and interior tilesets, the decor')
    A(' * catalog, overworld people, satchels and emote bubbles.')
    A(' * Map entries: tile (bits 0-9) | hflip (10) | vflip (11) | palbank (12-15).')
    A(' * Metatiles are 16x16 = {TL, TR, BL, BR} entries. Stamps are row-major')
    A(' * runs of consecutive metatile IDs (id = STAMP + row * width + col).')
    A(' * Include after the u8/u16/u32 typedefs.')
    A(' */')
    A('#ifndef GFX_FIELD_H')
    A('#define GFX_FIELD_H')
    A('')
    A('enum { ' + ', '.join('TS_%s' % n.upper() for n in TS_NAMES) + ', TS_COUNT };')
    A('')
    A('/* Tile attributes (u16) and metatile flags; docs/EXPANSION.md 10.2. */')
    for b, an in enumerate(ATTR_NAMES):
        A('#define A_%-8s 0x%04X' % (an, 1 << b))
    A('#define MTF_GROUND  %d  /* plain ground: may be drawn under overlays */' % MF_GROUND)
    A('#define MTF_OVERLAY %d  /* transparent object terrain (trees): ground drawn beneath */' % MF_OVERLAY)
    A('enum { LG_NONE, LG_SIMPLE, LG_VARIANT, LG_PATH, LG_WATER };')
    A('typedef struct { u16 tile, count; u8 frames, period; const u32 *data; } TileAnim;')
    A('/* Map character -> metatile: SIMPLE id[0]; VARIANT picks by cell hash % 16')
    A(' * through cumulative weights w[]; PATH / WATER are autotiled. */')
    A('typedef struct { u8 kind, n; u8 w[8]; u16 id[8]; } LegendEntry;')
    A('/* Elevation art (tools/elevation.py, docs/ELEVATION.md): map entries per')
    A(' * 8x8 quadrant (TL, TR, BL, BR), autotiled by src/game/elev.c. */')
    A('typedef struct ElevArt {')
    A('    u16 face[4][4];     /* cliff face: variant = continues down/up | sideways << 1 */')
    A('    u16 rim[4][5];      /* plateau edges, path-autotile variants (0 = none) */')
    A('    u16 shadow[4];      /* cast shadow on low ground east of a rise */')
    A('    u16 stairs[4][4];   /* per climbing direction N, S, W, E */')
    A('    u16 deck_h[4][4];   /* bridge walked E-W: variant = railing | end << 1 */')
    A('    u16 deck_v[4][4];   /* bridge walked N-S: variant = railing | end << 1 */')
    A('    u16 mouth[4];       /* tunnel mouth in a cliff face */')
    A('    u16 ledge[4][2];    /* ledge (hop down): variant = continues sideways */')
    A('} ElevArt;')
    A('typedef struct {')
    A('    const char *name;')
    A('    const u32 *tiles;')
    A('    u16 tile_count, meta_count;')
    A('    const u16 (*palettes)[16];')
    A('    const u16 (*meta_bottom)[4];')
    A('    const u16 (*meta_top)[4];')
    A('    const u16 *attr;')
    A('    const u8 *mflags;')
    A('    const u16 (*path_q)[5];            /* 0 when the tileset has no autotiled paths */')
    A('    const u16 (*water_q)[5];')
    A('    const TileAnim *anims;')
    A('    u8 anim_count;')
    A('    const LegendEntry *legend;         /* chars 32..127 */')
    A('    char legend_default;               /* used for unknown characters */')
    A('    u16 oob, ground;                   /* out-of-bounds cell, default ground */')
    A('    u16 backdrop;                      /* colour behind everything */')
    A('    const struct ElevArt *elev;        /* elevation art (tools/elevation.py) or 0 */')
    A('    /* ground blends (field.c blend_quads), 0 when the tileset has none:')
    A('     * blend_of = group + 1 of each metatile (0: none); blend_outer = a bit per')
    A('     * group the metatile is the surrounding ground of (edges fade into it) */')
    A('    const u8 *blend_of, *blend_outer;')
    A('    const u16 (*blend_q)[2][4][5];     /* [group][edge set][quadrant][variant], variant 0 unused */')
    A('    /* masses (field.c mass_piece), 0 when the tileset has none: overlay')
    A('     * cells of one group (a forest of TREE_TOP / TREE_BOTTOM) are drawn')
    A('     * as one canopy: mass_of = group + 1 of each metatile; the piece of')
    A('     * a cell comes from its eight neighbours (bits N NE E SE S SW W NW,')
    A('     * set = same group or beyond the map) */')
    A('    const u8 *mass_of;')
    A('    const u16 (*mass_pick)[256];       /* [group][neighbour mask] -> piece */')
    A('    const u16 (*mass_meta)[4];         /* piece -> overlay entries (TL, TR, BL, BR) */')
    A('    /* a second path drawing for paths through one other ground (sand,')
    A('     * cobbles): a path quadrant whose edge faces a cell of that ground')
    A('     * (path_alt_of) takes path_alt_q (field.c autotile_quads); 0 = none */')
    A('    const u16 (*path_alt_q)[5];')
    A('    const u8 *path_alt_of;')
    A('} TilesetDef;')
    A('')
    DOCS = {'town': TOWN_TERRAIN_DOC, 'wild': terrain_wild.WILD_TERRAIN_DOC,
            'interior': INTERIOR_TERRAIN_DOC}
    for sname in TS_NAMES:
        A('/* ================================================================ */')
        A('/* %-64s */' % ('%s tileset' % sname.upper()))
        A('/* ================================================================ */')
        emit_tileset(o, sets[sname], sets[sname].get('docs', DOCS.get(sname, {})))
    emit_tileset_table(o, sets)
    grass.emit(o, sets, TS_NAMES, pack4, fmt_u32)
    # ---------------- decor
    kinds = dec['kinds']
    A('/* ================================================================ */')
    A('/* Decor: transparent objects placed over any ground (BG2 = below   */')
    A('/* people, BG3 = "top" cells above people). Loaded per map: a kind\'s */')
    A('/* tiles are copied after the tileset and its entries hold          */')
    A('/* (local tile + 1); 0 = transparent quadrant. Masks: bit per cell, */')
    A('/* row-major (bit = dy * w + dx).                                   */')
    A('/* ================================================================ */')
    A('enum {')
    for d in kinds:
        A('  DK_%s,  /* %dx%d %s: %s */' % (d.name, d.w, d.h, '/'.join(d.sets), d.doc))
    A('  DK_COUNT')
    A('};')
    A('typedef struct {')
    A('    u8 w, h, frames, period;         /* w == 0: not available in this tileset */')
    A('    u16 tile_first, tile_count;      /* into decor_tiles; count per frame */')
    A('    u16 meta_first;                  /* into decor_meta, w*h cells */')
    A('    u16 solid, top, floor;           /* per-cell masks */')
    A('} DecorDef;')
    A('#define DECOR_TILE_TOTAL %d' % dec['tiles'])
    A('static const u32 decor_tiles[DECOR_TILE_TOTAL * 8] = {')
    A(fmt_u32(dec['words']))
    A('};')
    A('static const u16 decor_meta[%d][4] = {' % len(dec['meta']))
    for e in dec['meta']:
        A('    {0x%04X, 0x%04X, 0x%04X, 0x%04X},' % tuple(e))
    A('};')
    A('static const DecorDef DECOR_DEFS[TS_COUNT][DK_COUNT] = {')
    for sname in TS_NAMES:
        A('  { /* %s */' % sname)
        for d in kinds:
            dd = dec['defs'].get((sname, d.name))
            if not dd:
                A('    {0}, /* %s */' % d.name)
                continue
            A('    { %d, %d, %d, %d, %d, %d, %d, 0x%04X, 0x%04X, 0x%04X }, /* %s */' % (
                dd['w'], dd['h'], dd['frames'], dd['period'], dd['tile_first'],
                dd['tile_count'], dd['meta_first'], dd['solid'], dd['top'], dd['floor'], d.name))
        A('  },')
    A('};')
    A('static const char *const DECOR_NAMES[DK_COUNT] = {')
    for d in kinds:
        A('    "%s",' % d.name)
    A('};')
    A('/* What examining a decor kind says (0 = nothing; scripts may override). */')
    A('static const char *const DECOR_EXAMINE[DK_COUNT] = {')
    for d in kinds:
        A('    %s, /* %s */' % (c_string(d.examine) if d.examine else '0', d.name))
    A('};')
    A('')
    # ---------------- characters
    A('/* ================================================================ */')
    A('/* Overworld people: 16x32 OBJ, 9 frames x 8 tiles (2x4, row-major).  */')
    A('/* Frames: 0 down, 1-2 down walk, 3 up, 4-5 up walk, 6 left, 7-8 left */')
    A('/* walk. Right = h-flipped left frames. Cycle: stand, a, stand, b.    */')
    A('/* ================================================================ */')
    A('#define CHAR_COUNT %d' % len(chars))
    A('enum { ' + ', '.join('CHR_%s' % c['name'] for c in CHARACTERS) + ' };')
    A('static const u32 char_gfx[CHAR_COUNT][9][8 * 8] = {')
    for ci, (frames, pal) in enumerate(chars):
        A('  { /* %s */' % CHARACTERS[ci]['name'])
        for f in frames:
            A('    {')
            A(fmt_u32([w for t in f for w in t], indent='      '))
            A('    },')
        A('  },')
    A('};')
    A('static const u16 char_palettes[CHAR_COUNT][16] = {')
    for ci, (frames, pal) in enumerate(chars):
        A('    {' + ', '.join('0x%04X' % v for v in pal) + '}, /* %s */' % CHARACTERS[ci]['name'])
    A('};')
    A('')
    igfx, ipal = item
    A('/* 16x16 satchel lying on the ground: 2x2 tiles, row-major. */')
    A('static const u32 item_ball_gfx[4 * 8] = {')
    A(fmt_u32([w for t in igfx for w in t]))
    A('};')
    A('static const u16 item_ball_palette[16] = {')
    A(fmt_u16(ipal))
    A('};')
    egfx, epal, enames = emotes
    A('/* 16x16 emote bubbles (2x2 tiles each), drawn above heads. */')
    A('enum { ' + ', '.join('EMOTE_%s' % n for n in enames) + ', EMOTE_COUNT };')
    A('static const u32 emote_gfx[EMOTE_COUNT][4 * 8] = {')
    for e in egfx:
        A('  {')
        A(fmt_u32([w for t in e for w in t]))
        A('  },')
    A('};')
    A('static const u16 emote_palette[16] = {')
    A(fmt_u16(epal))
    A('};')
    A('')
    A('#endif /* GFX_FIELD_H */')
    with open(path, 'w') as f:
        f.write('\n'.join(o) + '\n')


# =====================================================================
# SATCHEL (items on the ground) & EMOTES
# =====================================================================

ITEM_BALL = [
    '................',
    '................',
    '......oooo......',
    '.....oYyyYo.....',
    '....ooyooyoo....',
    '...obbbbbbbbo...',
    '..obBBBBBBBBbo..',
    '..oBbbbbbbbbBo..',
    '..oBbbGGGbbbBo..',
    '..oBbbGgGbbbBo..',
    '..oBbbbbbbbbBo..',
    '..oBBbbbbbbBBo..',
    '...oBBBBBBBBo...',
    '....oooooooo....',
    '....ssssssss....',
    '................',
]
ITEM_PAL = [('o', (56, 40, 40)), ('b', (184, 128, 72)), ('B', (136, 88, 48)),
            ('y', (224, 176, 112)), ('Y', (248, 216, 152)), ('G', (248, 224, 96)),
            ('g', (200, 152, 40)), ('s', (72, 128, 64))]

EMOTES = {
    'EXCLAIM': [
        '..oooooooooooo..',
        '.owwwwwwwwwwwwo.',
        'owwwwwrrrwwwwwwo',
        'owwwwwrrrwwwwwwo',
        'owwwwwrrrwwwwwwo',
        'owwwwwrrrwwwwwwo',
        'owwwwwwrwwwwwwwo',
        'owwwwwwrwwwwwwwo',
        'owwwwwwwwwwwwwwo',
        'owwwwwwrrwwwwwwo',
        'owwwwwwrrwwwwwwo',
        '.owwwwwwwwwwwwo.',
        '..oooooowwoooo..',
        '.......owo......',
        '........o.......',
        '................',
    ],
    'HAPPY': [
        '..oooooooooooo..',
        '.owwwwwwwwwwwwo.',
        'owwwwwwwwwwwwwwo',
        'owwwffwwwwffwwwo',
        'owwffffwwffffwwo',
        'owwfffffffffffwo',
        'owwfffffffffffwo',
        'owwwfffffffffwwo',
        'owwwwfffffffwwwo',
        'owwwwwfffffwwwwo',
        'owwwwwwfffwwwwwo',
        '.owwwwwwfwwwwwo.',
        '..oooooowwoooo..',
        '.......owo......',
        '........o.......',
        '................',
    ],
    'NOTE': [
        '..oooooooooooo..',
        '.owwwwwwwwwwwwo.',
        'owwwwwwwbbbbwwwo',
        'owwwwwwwbwwbwwwo',
        'owwwwwwwbwwbwwwo',
        'owwwwwwwbwwbwwwo',
        'owwwwwwwbwwbwwwo',
        'owwwwbbbbwwbwwwo',
        'owwwbbbbbbbbwwwo',
        'owwwbbbbbbbbwwwo',
        'owwwwbbwwbbwwwwo',
        '.owwwwwwwwwwwwo.',
        '..oooooowwoooo..',
        '.......owo......',
        '........o.......',
        '................',
    ],
    'DOTS': [
        '..oooooooooooo..',
        '.owwwwwwwwwwwwo.',
        'owwwwwwwwwwwwwwo',
        'owwwwwwwwwwwwwwo',
        'owwwwwwwwwwwwwwo',
        'owwwwwwwwwwwwwwo',
        'owwbbwwbbwwbbwwo',
        'owwbbwwbbwwbbwwo',
        'owwwwwwwwwwwwwwo',
        'owwwwwwwwwwwwwwo',
        'owwwwwwwwwwwwwwo',
        '.owwwwwwwwwwwwo.',
        '..oooooowwoooo..',
        '.......owo......',
        '........o.......',
        '................',
    ],
    'RAIN': [
        '................',
        '..........l.....',
        '.........l......',
        '........l.......',
        '.......l........',
        '................',
        '................',
        '................',
        '...l............',
        '..l.............',
        '.l..............',
        '................',
        '............l...',
        '...........l....',
        '..........l.....',
        '................',
    ],
}
EMOTE_PAL = [('o', (48, 40, 56)), ('w', (248, 248, 240)), ('r', (224, 56, 48)),
             ('f', (240, 120, 64)), ('b', (72, 88, 136)), ('l', (176, 200, 232))]


def grid16_gfx(rows, pal_list):
    idx = {}
    pal = [0] * 16
    for i, (k, v) in enumerate(pal_list):
        idx[k] = i + 1
        pal[i + 1] = c15(v)
    tiles = []
    for ty in range(2):
        for tx in range(2):
            t = []
            for y in range(8):
                for x in range(8):
                    ch = rows[ty * 8 + y][tx * 8 + x]
                    t.append(0 if ch == '.' else idx[ch])
            tiles.append(pack4(t))
    return tiles, pal


def item_gfx():
    return grid16_gfx(ITEM_BALL, ITEM_PAL)


def emote_gfx():
    names = list(EMOTES.keys())
    gfx = []
    pal = None
    for n in names:
        tiles, pal = grid16_gfx(EMOTES[n], EMOTE_PAL)
        gfx.append(tiles)
    return gfx, pal, names


# =====================================================================
# MAIN
# =====================================================================

def main(argv):
    preview = None
    out_h = OUT_H
    if '--preview' in argv:
        preview = argv[argv.index('--preview') + 1]
        os.makedirs(preview, exist_ok=True)
    if '--out' in argv:
        out_h = argv[argv.index('--out') + 1]
    sets = build_tilesets()
    dec = build_decor(sets)
    lint_objects(sets, dec)
    chars = [char_gfx(c) for c in CHARACTERS]
    item = item_gfx()
    emotes = emote_gfx()
    if not ('--no-header' in argv):
        write_header(sets, dec, chars, item, emotes, out_h)
        print('wrote %s' % out_h)
        if out_h == OUT_H:
            n = write_viewer_maps(sets, dec, ROOT)
            print('wrote %d asset viewer maps (src/game/world/debug/)' % n)
    for s in TS_NAMES:
        print('%s: %d tiles, %d metatiles' % (s, len(sets[s]['ts'].tiles), len(sets[s]['meta_b'])))
    print('decor: %d kinds, %d tiles' % (len(dec['kinds']), dec['tiles']))
    if preview:
        pl_frames, pl_pal = chars[0]
        for s in TS_NAMES:
            if any((s, d.name) in dec['defs'] for d in dec['kinds']):
                render_decor_sheet(sets[s], s, dec, os.path.join(preview, 'decor_%s.png' % s))
        render_map_sample(sets['town'], dec, 'town', TOWN_SAMPLE, TOWN_SAMPLE_KEY,
                          TOWN_SAMPLE_STAMPS, TOWN_SAMPLE_DECOR,
                          os.path.join(preview, 'town_sample.png'),
                          sprites=[(pl_frames[0], pl_pal, 10 * 16, 8 * 16, False)])
        render_map_sample(sets['wild'], dec, 'wild', WILD_SAMPLE, WILD_SAMPLE_KEY,
                          [], [('ROCK', 9, 6, 0), ('BUSH', 19, 3, 0)],
                          os.path.join(preview, 'wild_sample.png'),
                          sprites=[(pl_frames[0], pl_pal, 3 * 16, 6 * 16, False)])
        render_map_sample(sets['interior'], dec, 'interior', INTERIOR_SAMPLE, INTERIOR_SAMPLE_KEY,
                          [], INTERIOR_SAMPLE_DECOR, os.path.join(preview, 'interior_sample.png'))
        render_characters(os.path.join(preview, 'characters.png'), chars, item)
        print('previews in %s' % preview)


if __name__ == '__main__':
    main(sys.argv[1:])
