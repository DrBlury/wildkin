#!/usr/bin/env python3
"""Decor of the WEST region (owner: W-WEST): transparent props for the
'coast' tileset (Saltwind Trail, Port Brine, the Current Hall, the Sea
Route, Gull Isle and the Drowned Bell) and a few harbour-town props for
'interior'. Registered in gen_field_gfx.all_decor().

Palette plan (tools/tilesets/ts_coast.py):

  coast bank 3  village props: outline, white, stone, wood, yellow, orange,
                red, sea blue, leaf greens. Every harbour, beach, Hall and
                Gull Isle prop is drawn in these 15 colours only.
  coast bank 7  the grotto: blue-black rock, bioluminescent cyan,
                verdigris and bronze (the Drowned Bell's props).
  interior bank 2 (wood, white, gold, red, blue, leaf) and bank 4 (wood,
                white, metal, glass): the harbour interiors.

Light comes from the top-left, objects have a 1px dark outline and never a
baked-in ground (the art lint checks). Piers reuse the village BRIDGE_H /
BRIDGE_V planks (ts_coast.USES_DECOR).
"""

import math
from pixelart import Img, Decor
from decor_outdoor import SG, outline

COAST = ['coast']
TIDE = ['tide']            # the Current Hall and the Drowned Bell
BOTH = ['coast', 'tide']
INT = ['interior']

# coast bank 3 legend
OL = {'.': None, 'O': 'b_out', 'w': 'white', 'l': 'st_lt', 'm': 'st_mid', 'd': 'st_dk',
      'A': 'wd_lt', 'B': 'wd_base', 'K': 'wd_dk', 'y': 'p_yel', 'o': 'fx_org', 'r': 'p_red',
      'u': 'w_lt', 'U': 'w_base', 'g': 't_lt', 'G': 't_mid'}
# coast bank 7 legend (the grotto)
GL = {'.': None, 'O': 'gb_blk', 'k': 'gb_dk', 'm': 'gb_mid', 'l': 'gb_lt', 'h': 'gb_hi',
      'C': 'bio_hi', 'c': 'bio_base', 'e': 'bio_dk', 'V': 'vg_hi', 'v': 'vg_base', 'x': 'vg_dk',
      'Z': 'bz_hi', 'z': 'bz_base', 'n': 'dw_base', 'w': 'white'}
# interior bank 2 legend
IL = {'.': None, 'O': 'i_out', 'A': 'bb_lt', 'B': 'bb_base', 'K': 'bb_dk', 'w': 'white',
      'Y': 'gd_hi', 'y': 'gd_base', 'R': 'rd_hi', 'r': 'rd_base', 'q': 'rd_dk', 'U': 'bl_hi',
      'u': 'bl_base', 'n': 'bl_dk', 'g': 'lf_hi', 'G': 'lf_base'}
# interior bank 4 legend
IG = {'.': None, 'O': 'i_out', 'A': 'bb_lt', 'B': 'bb_base', 'K': 'bb_dk', 'w': 'white',
      'H': 'mt_hi', 'M': 'mt_base', 'D': 'mt_dk', 'h': 'gl_hi', 'b': 'gl_base', 'k': 'gl_dk',
      's': 'sc_hi', 'S': 'sc_base', 'T': 'sc_dk', 'R': 'rd_hi'}


# ---------------------------------------------------------------------------
# drawing kit
# ---------------------------------------------------------------------------

def ell(img, cx, cy, rx, ry, c):
    for y in range(img.h):
        for x in range(img.w):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                img.p[y][x] = c


def ring(img, cx, cy, r_out, r_in, fn):
    """Annulus; fn(x, y, angle) -> colour or None."""
    for y in range(img.h):
        for x in range(img.w):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if r_in <= d <= r_out:
                c = fn(x, y, math.atan2(y + 0.5 - cy, x + 0.5 - cx))
                if c:
                    img.p[y][x] = c


def line(img, x0, y0, x1, y1, c):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        img.set(int(round(x0 + (x1 - x0) * i / n)), int(round(y0 + (y1 - y0) * i / n)), c)


def post(img, x, y0, y1, w=4, lt='wd_lt', base='wd_base', dk='wd_dk'):
    """A vertical wooden post (x = left edge)."""
    for y in range(y0, y1 + 1):
        for i in range(w):
            img.set(x + i, y, lt if i == 0 else (dk if i == w - 1 else base))


def shade_body(img, fill, lt, dk, cx=None):
    """Top-left light on a filled shape: first column/row of each run light,
    last dark."""
    o = img.copy()
    for y in range(img.h):
        for x in range(img.w):
            if img.p[y][x] != fill:
                continue
            if img.get(x - 1, y) != fill or img.get(x, y - 1) != fill:
                o.p[y][x] = lt
            elif img.get(x + 1, y) != fill or img.get(x, y + 1) != fill:
                o.p[y][x] = dk
    return o


# ---------------------------------------------------------------------------
# harbour props (coast bank 3)
# ---------------------------------------------------------------------------

PIER_POST = SG('''
................
................
................
................
.....OOOOOO.....
....OAAABBKO....
....OABBBBKO....
....OOOOOOOO....
....OAKKKKKO....
....OABBBBKO....
....OABBBKKO....
....OABBBBKO....
....OABBBBKO....
...uOABKBBKOu...
..uuOABBBBKOuu..
...uwOOOOOOwu...
''', OL)

BOLLARD = SG('''
................
................
................
................
................
.....OOOOOO.....
....OlllmmdO....
....OOOOOOOO....
.....OlmmdO.....
....OAAAAAAKO...
...OAKOlmdOAKO..
....OKOlmmdOKO..
.....OlmmmdO....
....OlllmmmdO...
....OOOOOOOOO...
................
''', OL)

LOBSTER_POTS = SG('''
................
................
....OOOOOO......
...OAKAKAKO.....
..OAOAOAOAKO....
..OAKAKAKAKO....
..OAOAOAOAKOOO..
..OBBBBBBBKAKAO.
.OOOOOOOOOAOAOKO
OAKAKAKAKOKAKAKO
OAOAOAOAKOAOAOKO
OAKAKAKAKOKAKAKO
OAOAOAOAKOBBBBKO
OBBBBBBBKOOOOOOO
OOOOOOOOOO......
................
''', OL)

def anchor_img():
    """16x16: an old iron anchor stood upright as a monument."""
    img = Img(16, 16)
    ring(img, 8, 3, 2.6, 1.2, lambda x, y, a: 'st_lt' if a < 0.5 else 'st_mid')
    img.rect(4, 6, 12, 7, 'st_mid')
    img.rect(4, 6, 12, 6, 'st_lt')
    img.rect(7, 6, 8, 13, 'st_mid')
    img.rect(7, 6, 7, 13, 'st_lt')
    for t in range(0, 7):
        x = 2 + t
        y = 9 + int(round(math.sqrt(max(0.0, 36 - (t - 6) ** 2)) * 0.7))
        img.set(x, y, 'st_mid')
        img.set(15 - x, y, 'st_dk')
        img.set(x, y - 1, 'st_lt')
        img.set(15 - x, y - 1, 'st_mid')
    img.rect(1, 9, 2, 10, 'st_lt')
    img.rect(13, 9, 14, 10, 'st_mid')
    img.rect(6, 13, 9, 13, 'st_dk')
    return outline(img)


LIFEBUOY = SG('''
................
.....OOOOOO.....
....OwwrrwwO....
...OwwOOOOrrO...
..OrrO....OwwO..
..OrrO....OwwO..
..OwwO....OrrO..
..OwwO....OrrO..
...OrrOOOOwwO...
....OrrwwrrO....
.....OOOOOO.....
.......OO.......
......OABO......
......OABO......
......OABO......
.....OOOOOO.....
''', OL)

SEA_ROCK = SG('''
................
................
................
.....OOOO.......
....OllmmOO.....
...OllmmmmmO....
..OllmmmmmmdO...
..OlmmmmmmddOO..
.OllmmmmmdddmdO.
.OlmmmmmmdddddO.
uOmmmmmmdddddddO
uwOmmmmddddddOOu
.uwOOdddddOOOwu.
..uwwOOOOOwwwu..
...uuwwwwwuuu...
................
''', OL)

SALT_HEAP = SG('''
................
................
................
................
.......OO.......
......OwwO......
.....OwwwlO.....
....OwwwwwlO....
...OwwwwwwllO...
...OwwwwwlllO...
..OwwwwwwllllO..
..OwwwwwlllllO..
.OwwwwwwllllmlO.
.OllwwllllmmmmO.
..OOOOOOOOOOOO..
................
''', OL)

SHELLS = SG('''
................
................
..OO............
.OwlO...........
.OlmO.......O...
..OO.......OoO..
..........OyoO..
...........OO...
................
.....OOO........
....OwwlO.......
....OwlmO.....O.
.....OOO.....OrO
..............O.
................
................
''', OL)

STARFISH = SG('''
................
................
................
.......O........
......OoO.......
......OoO.......
..OO..OoO..OO...
..OyooooooooO...
...OOooyoooO....
.....OoooO......
....OooOooO.....
...OoOO.OOoO....
...OO.....OO....
................
................
................
''', OL)

SEAWEED = SG('''
................
................
................
......O.........
.....OgO....O...
.....OgO...OgO..
....OgGO...OgO..
....OgGO..OgGO..
.O..OgGO..OgGO..
OgO.OGgO.OgGO...
OgGOOGgGOOgGO...
.OgGOgGGOgGO....
..OGgGgGgGO.....
...OGGGGGO......
....OOOOO.......
................
''', OL)

def driftwood():
    img = Img(32, 16)
    for x in range(3, 29):
        t = 6 + int(round(math.sin(x * 0.35) * 1.0))
        for y in range(t, t + 5):
            c = 'wd_lt' if y == t else ('K' if y == t + 4 else 'wd_base')
            img.set(x, y, 'wd_dk' if c == 'K' else c)
        if x % 7 == 2:
            img.set(x, t + 2, 'wd_dk')
    # a branch stub
    line(img, 22, 6, 25, 2, 'wd_base')
    line(img, 23, 6, 26, 2, 'wd_lt')
    # bleached ends
    for y in range(5, 12):
        if img.get(3, y):
            img.set(3, y, 'st_lt')
    img = outline(img)
    # a tuft of kelp caught on it
    for (x, y) in ((10, 11), (11, 12), (12, 11), (13, 12)):
        img.set(x, y, 't_mid')
    return img


def fishing_boat():
    """32x32: a small fishing smack, hull right, mast and furled red sail."""
    img = Img(32, 32)
    # hull
    for y in range(18, 28):
        k = (y - 18)
        x0, x1 = 2 + k // 2 + (2 if y > 25 else 0), 29 - k // 3 - (2 if y > 25 else 0)
        for x in range(x0, x1 + 1):
            c = 'wd_base'
            if y == 18:
                c = 'wd_lt'
            elif y in (20, 21):
                c = 'p_red'
            elif y >= 26:
                c = 'wd_dk'
            elif (x + y) % 9 == 0:
                c = 'wd_dk'
            img.set(x, y, c)
    for x in range(4, 27):
        img.set(x, 19, 'white' if x % 4 else 'wd_lt')
    # mast
    post(img, 14, 2, 17, w=2)
    # furled sail along the boom
    for x in range(8, 24):
        img.set(x, 15, 'p_red')
        img.set(x, 16, 'fx_org' if x % 3 else 'p_red')
    # pennant
    for i, x in enumerate(range(16, 21)):
        for y in range(3, 6 - i // 2):
            img.set(x, y, 'p_yel')
    # a coil of rope and a crate on deck
    img.rect(20, 14, 23, 17, 'wd_lt')
    img.rect(21, 15, 23, 17, 'wd_base')
    img = outline(img)
    # waterline ripples (transparent-friendly: only foam colours)
    for x in range(3, 29):
        if x % 5 != 0:
            img.set(x, 29, 'w_lt')
        if x % 7 in (1, 2):
            img.set(x, 30, 'white')
    return img


def ferry_boat():
    """48x32: the Brine ferry, a white-sailed cutter with a blue hull."""
    img = Img(48, 32)
    for y in range(20, 29):
        k = y - 20
        x0 = 3 + k + (2 if y > 26 else 0)
        x1 = 44 - k // 2 - (2 if y > 26 else 0)
        for x in range(x0, x1 + 1):
            c = 'w_base'
            if y == 20:
                c = 'white'
            elif y == 21:
                c = 'wd_lt'
            elif y in (24,):
                c = 'white'
            elif y >= 27:
                c = 'st_dk'
            img.set(x, y, c)
    # portholes
    for x in (14, 22, 30):
        img.set(x, 22, 'p_yel')
        img.set(x + 1, 22, 'p_yel')
    # cabin
    img.rect(26, 14, 37, 19, 'white')
    img.rect(26, 14, 37, 14, 'p_red')
    for x in (28, 31, 34):
        img.rect(x, 16, x + 1, 17, 'w_lt')
    # mast and sail
    post(img, 18, 1, 19, w=2)
    for y in range(3, 18):
        w = int((y - 2) * 0.9)
        for x in range(20, 20 + w):
            img.set(x, y, 'white' if (x - 20) < w - 1 else 'st_lt')
        for x in range(17 - int(w * 0.55), 18):
            img.set(x, y, 'white' if x > 17 - int(w * 0.55) else 'st_lt')
    for y in range(3, 18):
        img.set(20, y, 'st_lt')
    # flag
    img.rect(20, 0, 24, 2, 'p_red')
    img.set(22, 1, 'white')
    img = outline(img)
    for x in range(4, 45):
        if x % 5:
            img.set(x, 30, 'w_lt')
        if x % 6 in (2, 3):
            img.set(x, 31, 'white')
    return img


def lighthouse_frames():
    """32x64: a red-and-white striped lighthouse; the lamp sweeps (2 frames)."""
    base = Img(32, 64)
    # tower (tapers)
    for y in range(18, 58):
        half = 7 + (y - 18) * 3 // 40
        for x in range(16 - half, 16 + half):
            band = ((y - 18) // 8) % 2
            c = 'p_red' if band else 'white'
            if x == 16 - half:
                c = 'fx_org' if band else 'white'
            elif x >= 16 + half - 2:
                c = 'wd_dk' if band else 'st_lt'
            base.set(x, y, c)
    # door
    base.rect(13, 50, 18, 57, 'wd_base')
    base.rect(13, 50, 13, 57, 'wd_lt')
    base.rect(15, 49, 16, 49, 'wd_base')
    # window
    base.rect(15, 30, 16, 32, 'w_base')
    # gallery
    base.rect(7, 15, 24, 17, 'st_dk')
    base.rect(7, 15, 24, 15, 'st_mid')
    for x in range(8, 24, 2):
        base.set(x, 13, 'st_dk')
        base.set(x, 14, 'st_dk')
    base.rect(8, 12, 23, 12, 'st_dk')
    # lantern room
    base.rect(10, 5, 21, 11, 'p_yel')
    for x in (10, 13, 18, 21):
        base.rect(x, 5, x, 11, 'st_dk')
    # roof
    for y in range(0, 5):
        for x in range(12 - y, 20 + y):
            base.set(x, y + 1, 'p_red' if x < 16 else 'wd_dk')
    base.set(15, 0, 'st_dk')
    base.set(16, 0, 'st_dk')
    # base plinth
    base.rect(6, 58, 25, 61, 'st_mid')
    base.rect(6, 58, 25, 58, 'st_lt')
    base.rect(6, 61, 25, 61, 'st_dk')
    base = outline(base)
    frames = []
    for f in range(2):
        img = base.copy()
        glow = 'white' if f == 0 else 'fx_org'
        img.rect(14 if f == 0 else 11, 6, 17 if f == 0 else 12, 10, glow)
        if f == 1:
            img.rect(19, 6, 20, 10, glow)
        frames.append(img)
    return frames


def nets():
    """32x16: a fishing net hung to dry between two poles, with floats."""
    img = Img(32, 16)
    post(img, 2, 1, 14, w=3)
    post(img, 27, 1, 14, w=3)
    for x in range(5, 27):
        sag = int(round(2 * math.sin((x - 5) * math.pi / 22)))
        img.set(x, 2 + sag, 'st_mid')
        for y in range(3 + sag, 12 - sag // 2):
            if (x + y) % 3 == 0 or (x - y) % 3 == 0:
                img.set(x, y, 'st_lt' if y < 7 else 'st_mid')
        if x % 6 == 2:
            img.set(x, 3 + sag, 'fx_org')
            img.set(x + 1, 3 + sag, 'p_red')
    img = outline(img)
    return img


def fish_stall():
    """32x32: a fishmonger's stall: striped awning, fish on crushed ice."""
    img = Img(32, 32)
    # awning (rows 2..10)
    for y in range(2, 11):
        for x in range(1, 31):
            stripe = (x // 4) % 2
            c = 'p_red' if stripe else 'white'
            if y == 10 and x % 4 == 1:
                c = None
            if c:
                img.set(x, y, c)
    for x in range(1, 31):
        img.set(x, 2, 'fx_org' if (x // 4) % 2 else 'st_lt')
    # poles
    post(img, 2, 11, 29, w=2)
    post(img, 28, 11, 29, w=2)
    # counter
    img.rect(3, 18, 28, 28, 'wd_base')
    img.rect(3, 18, 28, 18, 'wd_lt')
    img.rect(3, 28, 28, 28, 'wd_dk')
    for x in range(5, 28, 6):
        img.rect(x, 21, x, 27, 'wd_dk')
    # ice + fish
    img.rect(4, 15, 27, 17, 'white')
    for (fx, c1, c2) in ((5, 'w_base', 'w_lt'), (11, 'st_mid', 'st_lt'), (17, 'fx_org', 'p_yel'),
                         (22, 'w_base', 'w_lt')):
        img.rect(fx, 15, fx + 3, 16, c1)
        img.set(fx, 15, c2)
        img.set(fx + 4, 14, c1)
        img.set(fx + 4, 16, c1)
        img.set(fx + 1, 15, 'b_out')
    # price board
    img.rect(12, 12, 19, 13, 'st_dk')
    img.set(14, 12, 'white')
    img.set(17, 12, 'white')
    return outline(img)


def bell_buoy_frames():
    """16x16, 2 frames: a red bell buoy bobbing in the swell."""
    frames = []
    for f in range(2):
        img = Img(16, 16)
        dy = f
        # cage
        for y in range(1 + dy, 7 + dy):
            img.set(5, y, 'st_dk')
            img.set(10, y, 'st_dk')
        img.rect(5, 1 + dy, 10, 1 + dy, 'st_dk')
        # bell
        img.rect(7, 3 + dy, 8, 5 + dy, 'p_yel')
        img.set(7, 3 + dy, 'white')
        # float
        for y in range(7 + dy, 12 + dy):
            half = 5 - abs(y - (9 + dy))
            for x in range(8 - half, 8 + half):
                img.set(x, y, 'p_red' if x > 5 else 'fx_org')
        img.rect(3, 9 + dy, 12, 9 + dy, 'white')
        img = outline(img)
        for x in range(1, 15):
            if (x + f) % 3:
                img.set(x, 13 + (x + f) % 2, 'w_lt' if x % 4 else 'white')
        frames.append(img)
    return frames


def gull_post():
    """16x32: a mooring post with a gull perched on top."""
    img = Img(16, 32)
    post(img, 6, 12, 30, w=4)
    img.rect(5, 11, 10, 11, 'wd_lt')
    # the gull
    ell(img, 8, 8, 4, 2.5, 'white')
    img.rect(3, 6, 6, 7, 'st_lt')   # wing
    img.rect(10, 5, 12, 7, 'white')  # head
    img.set(11, 5, 'b_out')          # eye
    img.set(13, 6, 'p_yel')          # beak
    img.set(14, 6, 'fx_org')
    img.set(7, 10, 'p_yel')
    img.set(9, 10, 'p_yel')
    img.rect(2, 7, 3, 7, 'st_dk')    # wingtip
    return outline(img)


def whale_arch():
    """48x48: an arch of two whale ribs over the path, lashed at the top."""
    img = Img(48, 48)
    for side in (-1, 1):
        for t in range(0, 64):
            a = t / 63.0 * math.pi * 0.5
            x = 24 + side * (4 + 16 * math.cos(a) ** 0.8)
            y = 44 - 40 * math.sin(a)
            for w in range(-2, 3):
                xx = int(round(x + side * w * 0.9))
                c = 'white' if w <= -1 else ('st_lt' if w <= 1 else 'st_mid')
                if side > 0:
                    c = 'white' if w >= 1 else ('st_lt' if w >= -1 else 'st_mid')
                img.set(xx, int(round(y)), c)
                img.set(xx, int(round(y)) + 1, c)
    # rope lashing at the crown
    img.rect(20, 3, 27, 7, 'wd_base')
    for x in range(20, 28, 2):
        img.rect(x, 3, x, 7, 'wd_dk')
    img.rect(22, 8, 22, 12, 'wd_base')
    img.rect(25, 8, 25, 11, 'wd_base')
    return outline(img)


def shell_lamp():
    """16x32: a harbour lamp whose shade is a great scallop shell."""
    img = Img(16, 32)
    post(img, 7, 12, 29, w=2, lt='st_mid', base='st_dk', dk='st_dk')
    img.rect(5, 29, 10, 30, 'st_dk')
    img.rect(5, 29, 10, 29, 'st_mid')
    # scallop shade
    for y in range(2, 10):
        half = min(6, 2 + (y - 2))
        for x in range(8 - half, 8 + half):
            c = 'white' if (x - 8) % 3 else 'st_lt'
            img.set(x, y, c)
    # glow
    img.rect(6, 10, 9, 11, 'p_yel')
    img.set(7, 10, 'white')
    return outline(img)


def hall_column():
    """16x32: a white column with a blue wave band."""
    img = Img(16, 32)
    img.rect(3, 1, 12, 3, 'st_lt')
    img.rect(3, 1, 12, 1, 'white')
    for y in range(4, 28):
        for x in range(4, 12):
            c = 'white' if x < 6 else ('st_lt' if x < 10 else 'st_mid')
            if 12 <= y <= 14:
                c = 'w_lt' if x < 8 else 'w_base'
            img.set(x, y, c)
    img.rect(3, 28, 12, 30, 'st_mid')
    img.rect(3, 28, 12, 28, 'st_lt')
    return outline(img)


def tide_pool_crab():
    """16x16: a CRANICRAB-sized crab shell (empty) for the beaches."""
    img = Img(16, 16)
    ell(img, 8, 10, 5, 3.5, 'p_red')
    ell(img, 7, 9, 3, 2, 'fx_org')
    for (x, y) in ((3, 12), (2, 13), (13, 12), (14, 13), (4, 13), (12, 13)):
        img.set(x, y, 'p_red')
    img.rect(4, 6, 5, 7, 'p_red')
    img.rect(11, 6, 12, 7, 'p_red')
    return outline(img)


# ---------------------------------------------------------------------------
# the Drowned Bell (coast bank 7)
# ---------------------------------------------------------------------------

def drowned_bell():
    """48x48: the great bronze bell of the drowned chapel, half sunk in the
    grotto floor, crusted with verdigris; a star is cast on its waist."""
    img = Img(48, 48)
    # yoke
    img.rect(8, 2, 39, 6, 'gb_lt')
    img.rect(8, 2, 39, 2, 'gb_hi')
    img.rect(8, 6, 39, 6, 'gb_mid')
    img.rect(21, 7, 26, 9, 'bz_base')
    # bell body
    for y in range(10, 44):
        t = (y - 10) / 33.0
        half = 9.5 + 4.5 * t + 40 * max(0.0, t - 0.72) ** 2
        if y < 15:  # rounded shoulder
            half = 9.5 * math.sqrt(max(0.0, 1 - ((15 - y) / 5.5) ** 2)) + 0.5
        for x in range(int(round(24 - half)), int(round(24 + half)) + 1):
            rel = (x - (24 - half)) / (2 * half)
            if rel < 0.18:
                c = 'bz_hi'
            elif rel < 0.62:
                c = 'bz_base'
            else:
                c = 'vg_dk'
            # verdigris streaks and crust
            if (x * 5 + y * 3) % 13 == 0 or (y > 34 and (x + y) % 5 == 0):
                c = 'vg_base' if rel < 0.62 else 'vg_dk'
            if (x * 7 + y) % 29 == 0:
                c = 'vg_hi'
            img.set(x, y, c)
    # lip
    for x in range(3, 45):
        img.set(x, 42, 'bz_hi' if x < 14 else ('bz_base' if x < 34 else 'vg_dk'))
    # cast star
    cx, cy = 24, 27
    for (dx, dy) in ((0, -4), (0, -3), (0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
                     (-4, 0), (-3, 0), (-2, 0), (-1, 0), (1, 0), (2, 0), (3, 0), (4, 0),
                     (-2, -2), (2, -2), (-2, 2), (2, 2), (-1, -1), (1, -1), (-1, 1), (1, 1)):
        img.set(cx + dx, cy + dy, 'bio_hi' if (dx, dy) == (0, 0) else 'bio_base')
    # rim bands
    for x in range(10, 38):
        if img.get(x, 17):
            img.set(x, 17, 'vg_base')
        if img.get(x, 37):
            img.set(x, 37, 'vg_base')
    img = outline(img, 'gb_blk')
    # glowing algae at the lip
    for x in range(4, 44, 3):
        img.set(x, 44, 'bio_base')
        img.set(x + 1, 45, 'bio_dk')
    return img


def grot_pillar():
    """16x32: a fallen chapel's pillar, bearded with glowing weed."""
    img = Img(16, 32)
    img.rect(2, 1, 13, 4, 'gb_hi')
    img.rect(2, 4, 13, 4, 'gb_lt')
    for y in range(5, 28):
        for x in range(4, 12):
            c = 'gb_hi' if x < 6 else ('gb_lt' if x < 10 else 'gb_mid')
            if (x + y * 2) % 11 == 0:
                c = 'gb_mid'
            img.set(x, y, c)
    for (x, y0, n) in ((5, 5, 7), (9, 5, 11), (7, 5, 4)):
        for y in range(y0, y0 + n):
            img.set(x, y, 'vg_base' if y < y0 + n - 1 else 'bio_base')
    img.rect(2, 28, 13, 30, 'gb_lt')
    img.rect(2, 28, 13, 28, 'gb_hi')
    return outline(img, 'gb_blk')


def glow_coral_frames():
    frames = []
    for f in range(2):
        img = Img(16, 16)
        branches = [(8, 14, 8, 6), (8, 10, 4, 5), (8, 11, 12, 4), (5, 7, 3, 3), (11, 6, 13, 2)]
        for (x0, y0, x1, y1) in branches:
            line(img, x0, y0, x1, y1, 'bio_dk')
            line(img, x0 - 1, y0, x1 - 1, y1, 'bio_base')
        tips = [(8, 5), (3, 3), (13, 2), (4, 5), (12, 4)]
        for i, (x, y) in enumerate(tips):
            img.set(x, y, 'bio_hi' if (i + f) % 2 == 0 else 'bio_base')
        img.rect(5, 14, 11, 15, 'gb_lt')
        img = outline(img, 'gb_blk')
        frames.append(img)
    return frames


def whale_carving():
    """48x32: a star whale carved in relief on the grotto wall; its star
    eyes glow."""
    img = Img(48, 32)
    # stone slab
    for y in range(2, 30):
        for x in range(2, 46):
            img.set(x, y, 'gb_lt' if (x < 4 or y < 4) else ('gb_mid' if x < 44 and y < 28 else 'gb_dk'))
    # whale body relief
    for y in range(8, 24):
        for x in range(8, 38):
            if ((x - 22) / 14.0) ** 2 + ((y - 16) / 6.5) ** 2 <= 1.0:
                img.set(x, y, 'gb_hi' if y < 14 else 'gb_lt')
    # tail
    for (x, y) in ((38, 14), (39, 13), (40, 12), (41, 11), (38, 17), (39, 18), (40, 19), (41, 20),
                   (37, 15), (37, 16), (40, 11), (41, 21)):
        img.set(x, y, 'gb_hi')
    # belly grooves
    for x in range(12, 32, 3):
        img.set(x, 20, 'gb_mid')
        img.set(x + 1, 21, 'gb_mid')
    # star eye and a sprinkle of stars
    img.set(13, 14, 'bio_hi')
    for (x, y) in ((9, 5), (20, 6), (33, 5), (43, 8), (6, 25), (27, 26), (40, 25)):
        img.set(x, y, 'bio_base')
    return outline(img, 'gb_blk')


# ---------------------------------------------------------------------------
# interiors (interior banks 2 and 4)
# ---------------------------------------------------------------------------

def ship_wheel():
    img = Img(16, 16)
    ring(img, 8, 8, 6.2, 4.4, lambda x, y, a: 'bb_lt' if (a < -0.8 or a > 2.6) else 'bb_base')
    for k in range(8):
        a = k * math.pi / 4
        for r in range(1, 8):
            x, y = int(round(8 + math.cos(a) * r - 0.5)), int(round(8 + math.sin(a) * r - 0.5))
            img.set(x, y, 'bb_dk' if r < 7 else 'bb_base')
    img.rect(7, 7, 8, 8, 'gd_hi')
    return outline(img, 'i_out')


def fish_trophy():
    img = Img(16, 16)
    # plaque
    for y in range(3, 14):
        for x in range(1, 15):
            if abs(x - 7.5) + abs(y - 8) * 0.9 <= 9:
                img.set(x, y, 'bb_base' if x > 3 else 'bb_lt')
    # the fish
    for y in range(6, 11):
        for x in range(3, 12):
            if ((x - 7) / 4.5) ** 2 + ((y - 8) / 2.3) ** 2 <= 1.0:
                img.set(x, y, 'bl_hi' if y < 8 else 'bl_base')
    for (x, y) in ((12, 7), (13, 6), (12, 9), (13, 10), (12, 8)):
        img.set(x, y, 'bl_dk')
    img.set(4, 7, 'i_out')
    img.rect(6, 12, 9, 12, 'gd_base')
    return outline(img, 'i_out')


def ship_bottle():
    img = Img(16, 16)
    # bottle lying on a stand
    for y in range(4, 12):
        for x in range(2, 13):
            if ((x - 7) / 5.5) ** 2 + ((y - 8) / 4.0) ** 2 <= 1.0:
                img.set(x, y, 'gl_hi' if y < 6 else 'gl_base')
    img.rect(12, 7, 14, 8, 'gl_base')
    img.rect(14, 7, 14, 8, 'bb_base')
    # the ship inside
    img.rect(4, 9, 10, 9, 'bb_base')
    img.rect(5, 10, 9, 10, 'bb_dk')
    img.rect(7, 5, 7, 8, 'bb_dk')
    img.rect(5, 6, 6, 8, 'white')
    img.rect(8, 6, 9, 8, 'white')
    # stand
    img.rect(3, 12, 11, 13, 'bb_base')
    img.rect(3, 12, 11, 12, 'bb_lt')
    return outline(img, 'i_out')


def net_wall():
    """32x16: a fishing net hung on the wall with two glass floats."""
    img = Img(32, 16)
    for x in range(1, 31):
        sag = int(round(2 * math.sin((x - 1) * math.pi / 30)))
        for y in range(1 + sag, 13 - sag):
            if (x + y) % 3 == 0 or (x - y) % 3 == 0:
                img.set(x, y, 'bb_lt' if y < 7 else 'bb_base')
    ell(img, 9, 8, 2.5, 2.5, 'gl_base')
    img.set(8, 7, 'gl_hi')
    ell(img, 22, 9, 2.5, 2.5, 'gl_base')
    img.set(21, 8, 'gl_hi')
    return outline(img, 'i_out')


def heron_statue():
    """Carved heron keeping watch over the reed rookery (one cell wide, two high)."""
    img = Img(16, 32)
    img.rect(2, 27, 13, 30, 'st_dk')
    img.rect(3, 27, 12, 28, 'st_lt')
    ell(img, 8, 19, 4.5, 6, 'st_mid')
    ell(img, 7, 17, 3.5, 4.5, 'st_lt')
    img.rect(9, 9, 10, 19, 'st_mid')
    ell(img, 10, 8, 3, 2.5, 'st_lt')
    line(img, 12, 8, 15, 9, 'st_dk')
    line(img, 7, 23, 6, 27, 'st_dk')
    line(img, 9, 23, 10, 27, 'st_dk')
    return outline(img)


# ---------------------------------------------------------------------------
# the catalogue
# ---------------------------------------------------------------------------

WEST_DECOR = [
    # harbour
    Decor('PIER_POST', COAST, PIER_POST, doc='wooden mooring pile standing in the water',
          examine='A mooring pile, furred with barnacles below the tide line.'),
    Decor('BOLLARD', COAST, BOLLARD, doc='iron bollard with a rope wound round it',
          examine='An iron bollard. The rope around it is still wet.'),
    Decor('LOBSTER_POTS', COAST, LOBSTER_POTS, doc='stacked wicker lobster pots',
          examine='Wicker lobster pots. One of them clicks. Something inside is not a lobster.'),
    Decor('ANCHOR', COAST, anchor_img(), doc='old iron anchor set up as a monument',
          examine='An old anchor from the first Brine trawler. Kids climb it; nobody minds.'),
    Decor('LIFEBUOY', COAST, LIFEBUOY, doc='red and white lifebuoy on a post',
          examine='A lifebuoy. Painted on it: IF YOU CAN READ THIS, YOU ARE TOO CLOSE TO THE EDGE.'),
    Decor('FISHING_BOAT', COAST, fishing_boat(), doc='small fishing smack moored in the water (2x2)',
          examine='A fishing smack. Its nets smell of yesterday.'),
    Decor('FERRY_BOAT', COAST, ferry_boat(), doc='the white-sailed Brine ferry (3x2)',
          examine='The ferry to GULL ISLE. Ask the HARBOR OFFICE for a crossing.'),
    Decor('LIGHTHOUSE', COAST, frames=lighthouse_frames(), period=24, top='XX/XX/../..',
          doc='striped lighthouse, lamp sweeps; upper half over people (2x4)',
          examine='The Brine light. Its lamp is a single heartglass lens the size of a cartwheel.'),
    Decor('NETS', COAST, nets(), doc='fishing net drying between two poles (2x1)',
          examine='Nets drying in the wind, mended with bright orange twine.'),
    Decor('FISH_STALL', COAST, fish_stall(), top='XX/..', doc='fishmonger stall with striped awning (2x2)',
          examine='Today\'s catch on crushed ice: mackerel, sprats, and a very offended crab.'),
    Decor('SHELLS', COAST, SHELLS, floor='X', doc='shells scattered on the sand (walkable)'),
    Decor('STARFISH', COAST, STARFISH, floor='X', doc='a starfish on the sand (walkable)'),
    Decor('SEAWEED', COAST, SEAWEED, floor='X', doc='a tangle of wrack on the sand (walkable)'),
    Decor('DRIFTWOOD', COAST, driftwood(), doc='bleached driftwood log (2x1)',
          examine='Driftwood, bleached silver. It has travelled further than you have.'),
    Decor('SEA_ROCK', COAST, SEA_ROCK, doc='rock in the surf with foam around it',
          examine='A rock in the surf. Limpets hold on for dear life.'),
    Decor('SALT_HEAP', COAST, SALT_HEAP, doc='heap of raked sea salt',
          examine='Raked sea salt, drying in a white heap. It crunches.'),
    Decor('BELL_BUOY', COAST, frames=bell_buoy_frames(), period=30, doc='red bell buoy bobbing',
          examine='A bell buoy. Dong... dong... The fishers say it rings by itself at night.'),
    Decor('GULL_POST', COAST, gull_post(), top='X/.', doc='mooring post with a gull on top (1x2)',
          examine='The gull stares at you. You stare at the gull. The gull wins.'),
    Decor('WHALE_ARCH', COAST, whale_arch(), top='XXX/X.X/...', solid='.../.../X.X',
          doc='arch of two whale ribs over a path (3x3; walk through the middle)',
          examine='Two ribs of a whale that beached here a century ago. Its song, they say, did not end.'),
    Decor('SHELL_LAMP', BOTH, shell_lamp(), top='X/.', doc='harbour lamp with a scallop shade (1x2)',
          examine='A street lamp with a scallop-shell shade. A little JELLUME sleeps inside the glass.'),
    Decor('HALL_COLUMN', TIDE, hall_column(), top='X/.', doc='Current Hall column with a wave band (1x2)'),
    Decor('CRAB_SHELL', COAST, tide_pool_crab(), floor='X', doc='an empty crab shell (walkable)'),
    # the Drowned Bell grotto
    Decor('DROWNED_BELL', TIDE, drowned_bell(), top='XXX/.../...',
          doc='the Drowned Bell: great verdigris bronze bell half sunk in the grotto (3x3)'),
    Decor('GROT_PILLAR', TIDE, grot_pillar(), top='X/.', doc='fallen chapel pillar with glowing weed (1x2)',
          examine='A chapel pillar, far below any chapel. The weed on it glows when you breathe on it.'),
    Decor('GLOW_CORAL', TIDE, frames=glow_coral_frames(), period=28, doc='bioluminescent coral (pulses)',
          examine='Glow coral. It brightens in time with a slow, deep hum you feel in your teeth.'),
    Decor('WHALE_CARVING', TIDE, whale_carving(), doc='star whale carved on the grotto wall (3x2)',
          examine='A whale carved in the rock, with stars for eyes. Scratched beneath: SHE SINGS THE TIDE IN.'),
    Decor('HERON_STATUE', COAST, heron_statue(), top='X/.',
          doc='carved heron at the Fen rookery (1x2)',
          examine='The heron is carved from driftwood. Real herons watch from the reeds.'),
    # harbour interiors
    Decor('SHIP_WHEEL', INT, ship_wheel(), doc='ship\'s wheel hung on the wall',
          examine='A ship\'s wheel from a wreck on the SEA ROUTE. Someone polished the spokes.'),
    Decor('FISH_TROPHY', INT, fish_trophy(), doc='mounted fish trophy on a plaque',
          examine='A mounted fish. The plaque reads: "THE ONE THAT DIDN\'T GET AWAY."'),
    Decor('SHIP_BOTTLE', INT, ship_bottle(), doc='a ship in a bottle on a stand',
          examine='A ship in a bottle. Nobody in Brine will say how it got in there.'),
    Decor('NET_WALL', INT, net_wall(), doc='fishing net hung on the wall with glass floats (2x1)',
          examine='An old net with glass floats. Each float was blown in Lumen and sailed home.'),
]
