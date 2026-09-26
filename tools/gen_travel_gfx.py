#!/usr/bin/env python3
"""Generate src/gfx_travel.h: the traversal graphics (docs/EXPANSION.md 7.5).

Everything the TRAVERSAL system draws that is not a tileset or a kin:

  * map objects as OBJ sprites (boulder, pressure plate, gate, floor switch,
    crackling barrier, teleport pad, chest, ladder, ferry post),
  * field particles (snow, ash, dust, sparkles, bubbles, wakes, splashes,
    ground shadows, current chevrons),
  * the player riding the BIKE (32x32 frames in the player's own palette,
    composed from the overworld player's head and body in gen_field_gfx),
  * the boat for ferry rides and the scrolling sea of the voyage scene,
  * the six Hall crests for the CREST CASE,
  * the Vale as a painted town map (one BG, 240x160) and the pixel position
    of every place on it (WM_* spots; the FLY destination picker uses them).

OBJ palettes are shared with gen_field_gfx: the misc bank (OBJ 8) keeps the
satchel colours at their indices and adds seven of ours, the fx bank (OBJ
15) keeps the emote colours and adds nine (docs/EXPANSION.md 10.3). The bike
uses the player's palette (OBJ 0) unchanged.

Standard library only, deterministic. Run from anywhere:

    python3 tools/gen_travel_gfx.py [--preview DIR]
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_field_gfx as gf  # noqa: E402
from pixelart import c15, c15_to_rgb, write_png, scale_rows, hash2  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_H = os.path.join(ROOT, 'src', 'gfx_travel.h')


# =====================================================================
# Palettes
# =====================================================================

class Pal:
    """16-entry palette addressed by one-character keys ('.' = 0)."""

    def __init__(self, entries):
        self.key = {'.': 0}
        self.rgb = [(0, 0, 0)] * 16
        n = 1
        for k, v in entries:
            if k in self.key:
                raise ValueError('palette key %r twice' % k)
            if n > 15:
                raise ValueError('palette too big')
            self.key[k] = n
            self.rgb[n] = v
            n += 1
        self.count = n

    def c15s(self):
        return [c15(c) for c in self.rgb]

    def __getitem__(self, k):
        return self.key[k]


# OBJ bank 8: the satchel's colours first (gen_field_gfx.ITEM_PAL), then ours.
MISC_EXTRA = [('d', (80, 84, 104)), ('m', (132, 136, 156)), ('l', (188, 192, 208)),
              ('w', (248, 248, 248)), ('c', (112, 216, 248)), ('u', (56, 112, 208)),
              ('v', (176, 104, 232))]
MISC = Pal(list(gf.ITEM_PAL) + MISC_EXTRA)

# OBJ bank 15: the emote colours first (gen_field_gfx.EMOTE_PAL), then ours.
FX_EXTRA = [('a', (80, 152, 224)), ('A', (168, 216, 248)), ('e', (204, 204, 216)),
            ('E', (144, 140, 156)), ('n', (100, 92, 96)), ('k', (36, 36, 52)),
            ('Y', (248, 232, 120)), ('G', (120, 192, 88)), ('p', (240, 160, 200))]
FX = Pal(list(gf.EMOTE_PAL) + FX_EXTRA)

PLAYER = gf.CHARACTERS[0]
PLAYER_IDX, PLAYER_PAL15 = gf.char_palette(PLAYER)


# =====================================================================
# Index images
# =====================================================================

def blank(w, h):
    return [[0] * w for _ in range(h)]


def grid(text, pal):
    rows = [r.strip() for r in text.strip('\n').split('\n')]
    rows = [r for r in rows if r]
    w = max(len(r) for r in rows)
    img = blank(w, len(rows))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            img[y][x] = pal[ch]
    return img


def put(img, x, y, v):
    if 0 <= y < len(img) and 0 <= x < len(img[0]):
        img[y][x] = v


def get(img, x, y):
    if 0 <= y < len(img) and 0 <= x < len(img[0]):
        return img[y][x]
    return 0


def paste(dst, src, ox, oy):
    for y, row in enumerate(src):
        for x, v in enumerate(row):
            if v:
                put(dst, ox + x, oy + y, v)


def outline(img, v, diag=False):
    h, w = len(img), len(img[0])
    add = []
    for y in range(h):
        for x in range(w):
            if img[y][x]:
                continue
            nb = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            if diag:
                nb += [(1, 1), (-1, 1), (1, -1), (-1, -1)]
            if any(get(img, x + dx, y + dy) not in (0, v) for dx, dy in nb):
                add.append((x, y))
    for x, y in add:
        img[y][x] = v


def flip_h(img):
    return [row[::-1] for row in img]


def tiles_of(img):
    """Row-major 8x8 tiles (1D OBJ mapping) of an index image."""
    h, w = len(img), len(img[0])
    out = []
    for ty in range(h // 8):
        for tx in range(w // 8):
            idx = [img[ty * 8 + y][tx * 8 + x] for y in range(8) for x in range(8)]
            out.append(gf.pack4(idx))
    return out


def words_of(img):
    return [w for t in tiles_of(img) for w in t]


LIGHT = (-0.55, -0.7, 0.45)
_ll = math.sqrt(sum(v * v for v in LIGHT))
LIGHT = tuple(v / _ll for v in LIGHT)


def sphere(nx, ny):
    nz = math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny))
    return nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]


def shade_ellipse(img, cx, cy, rx, ry, ramp, th, clip=None, seed=0):
    """Fill an ellipse with sphere shading; ramp dark..light, th ascending."""
    for y in range(len(img)):
        for x in range(len(img[0])):
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            if nx * nx + ny * ny > 1.0 or (clip and not clip(x, y)):
                continue
            b = sphere(nx * 0.95, ny * 0.95) + ((hash2(x, y, seed) & 63) / 63.0 - 0.5) * 0.12
            lv = sum(1 for t in th if b >= t)
            img[y][x] = ramp[min(lv, len(ramp) - 1)]


# =====================================================================
# Map objects (OBJ bank 8)
# =====================================================================

def boulder():
    M = MISC
    img = blank(16, 16)
    shade_ellipse(img, 8.0, 8.8, 7.2, 6.6, [M['d'], M['m'], M['l'], M['w']], (-0.1, 0.35, 0.86),
                  clip=lambda x, y: y <= 14, seed=3)
    for (x, y) in [(5, 7), (6, 8), (6, 9), (10, 5), (11, 6), (11, 10), (12, 11), (9, 12)]:
        if img[y][x] in (M['m'], M['l']):
            img[y][x] = M['d']
    for (x, y) in [(4, 5), (5, 4), (6, 4)]:
        if img[y][x]:
            img[y][x] = M['w']
    outline(img, M['o'])
    for x in range(3, 13):   # contact shadow
        if img[15][x] == 0 and img[14][x]:
            img[15][x] = M['o']
    return img


def plate(pressed):
    M = MISC
    img = blank(16, 16)
    top = 4 if not pressed else 5
    for y in range(top, 15):
        for x in range(2, 14):
            img[y][x] = M['m']
    for x in range(2, 14):
        img[top][x] = M['l']
        img[14][x] = M['d']
    for y in range(top, 15):
        img[y][2] = M['l']
        img[y][13] = M['d']
    if not pressed:
        for y in range(top + 1, 13):
            for x in range(3, 13):
                img[y][x] = M['l'] if (x + y) % 5 else M['m']
        for x in range(3, 13):
            img[13][x] = M['m']
        rune = M['u']
    else:
        rune = M['c']
    # a ring rune in the middle (glows when pressed)
    for (x, y) in [(7, top + 3), (8, top + 3), (6, top + 4), (9, top + 4), (6, top + 5), (9, top + 5),
                   (7, top + 6), (8, top + 6)]:
        img[y][x] = rune
    if pressed:
        img[top + 4][7] = img[top + 4][8] = M['w']
        img[top + 5][7] = img[top + 5][8] = M['w']
    outline(img, M['o'])
    return img


def floor_switch(on):
    M = MISC
    img = blank(16, 16)
    for y in range(5, 15):
        for x in range(2, 14):
            img[y][x] = M['d']
    for x in range(3, 13):
        img[5][x] = M['m']
    for y in range(6, 14):
        img[y][3] = M['m']
    lift = 0 if on else -1
    ramp = [M['u'], M['c'], M['w']] if on else [M['o'], M['u'], M['c']]
    shade_ellipse(img, 8.0, 9.6 + lift + (0.6 if on else 0), 3.8, 3.0, ramp, (-0.2, 0.6))
    if on:
        for (x, y) in [(2, 3), (13, 3), (1, 9), (14, 9)]:
            img[y][x] = M['G']
    outline(img, M['o'])
    return img


def pad(frame):
    M = MISC
    img = blank(16, 16)
    for y in range(16):
        for x in range(16):
            dx, dy = (x + 0.5 - 8) / 7.5, (y + 0.5 - 9) / 5.8
            r = math.sqrt(dx * dx + dy * dy)
            if r > 1.0:
                continue
            if r > 0.78:
                v = M['d']
            elif r > 0.58:
                ang = (math.atan2(dy, dx) / (2 * math.pi) + 0.5 + frame / 4.0) % 1.0
                v = M['w'] if ang < 0.14 else (M['c'] if ang < 0.3 else M['v'])
            elif r > 0.4:
                v = M['u']
            else:
                v = M['c'] if (frame % 2) else M['v']
                if r < 0.2:
                    v = M['w']
            img[y][x] = v
    outline(img, M['o'])
    return img


def chest(opened):
    M = MISC
    if not opened:
        return grid('''
            ................
            ................
            ...oooooooooo...
            ..oyyyyGGyyyyo..
            .oyYyyyGgyyyYbo.
            .obbbbbGgbbbbbo.
            .oBBBBBGgBBBBBo.
            .ooooooGGoooooo.
            .obbbboGGobbbbo.
            .obbbbboobbbbbo.
            .oBbbbbbbbbbbBo.
            .obbbbbbbbbbbbo.
            .oBbbbbbbbbbbBo.
            .oBBBBBBBBBBBBo.
            ..oooooooooooo..
            ................
        ''', M)
    return grid('''
        ...oooooooooo...
        ..oYyyyyyyyyyo..
        ..oyyyyGGyyyyo..
        ..oBBBBGgBBBBo..
        .ooooooooooooo..
        .oogGYGggGYgGoo.
        .oGYgGGYGgGYGgo.
        .ooooooooooooo..
        .obbbbboobbbbbo.
        .obbbbbbbbbbbbo.
        .oBbbbbbbbbbbBo.
        .obbbbbbbbbbbbo.
        .oBbbbbbbbbbbBo.
        .oBBBBBBBBBBBBo.
        ..oooooooooooo..
        ................
    ''', MISC)


def ladder():
    return grid('''
        ................
        ..oooooooooooo..
        .oddddddddddddo.
        .odoBoooooBoodo.
        .odoboooooboodo.
        .odobyyyyyboodo.
        .odoBBBBBBBoodo.
        .odoboooooboodo.
        .odobyyyyyboodo.
        .odoBBBBBBBoodo.
        .odoboooooboodo.
        .odobyyyyyboodo.
        .odoBBBBBBBoodo.
        .ommmmmmmmmmmmo.
        ..oooooooooooo..
        ................
    ''', MISC)


def gate_slot():
    return grid('''
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
        .oooooooooooooo.
        .odmdmdmdmdmdmo.
        .oooooooooooooo.
        ................
        ................
    ''', MISC)


def gate(sink):
    """16x32 iron portcullis; `sink` pixels already lowered into the slot."""
    M = MISC
    full = blank(16, 32)
    for y in range(6, 30):
        for x in (1, 14):
            full[y][x] = M['d']
        full[y][2] = M['m']
        full[y][13] = M['m']
    for y in range(8, 30):
        for bx in (4, 7, 10):
            full[y][bx] = M['m']
            full[y][bx + 1] = M['l'] if y % 6 else M['m']
    for x in range(1, 15):
        for y in (6, 7):
            full[y][x] = M['m'] if y == 7 else M['l']
        full[16][x] = M['m']
        full[17][x] = M['d']
        full[26][x] = M['m']
        full[27][x] = M['d']
    for bx in (4, 7, 10):   # spikes
        full[5][bx] = full[5][bx + 1] = M['l']
        full[4][bx + 1] = M['w']
    for (x, y) in [(3, 16), (6, 16), (9, 16), (12, 16), (3, 26), (6, 26), (9, 26), (12, 26)]:
        full[y][x] = M['w']
    outline(full, M['o'])
    img = blank(16, 32)
    for y in range(32):
        sy = y - sink
        if 0 <= sy < 32 and y <= 29:
            img[y] = full[sy][:]
    if sink:
        for x in range(1, 15):
            img[29][x] = M['o']
            img[30][x] = M['d']
    return img


def barrier(frame):
    """16x32 barrier: two posts, arcs crackling between them (frame 4 = off)."""
    M = MISC
    img = blank(16, 32)
    for y in range(10, 31):
        for x in (0, 15):
            img[y][x] = M['o']
        img[y][1] = M['m']
        img[y][14] = M['d']
    on = frame < 4
    for x, cap in ((1, 0), (14, 1)):
        for y in (8, 9, 10):
            img[y][x] = (M['w'] if y == 8 else M['c']) if on else M['u']
    if on:
        rnd = frame * 97 + 11
        for base in (13, 19, 25):
            y = base
            for x in range(2, 14):
                rnd = (rnd * 1103515245 + 12345) & 0x7fffffff
                y += (rnd >> 8) % 3 - 1
                y = max(base - 2, min(base + 2, y))
                img[y][x] = M['w']
                if img[y + 1][x] == 0:
                    img[y + 1][x] = M['c']
                if (rnd >> 12) % 4 == 0 and img[y - 1][x] == 0:
                    img[y - 1][x] = M['u']
        for (x, y) in [(2, 9), (13, 9)]:
            img[y][x] = M['G']
    outline(img, M['o'])
    return img


def ferry_post():
    return grid('''
        ................
        ................
        ....oooooooo....
        ...oyyyyyyyyo...
        ...oBBBBBBBBo...
        ....ooboobbo....
        ......ob..o.....
        .....oGGo.Y.....
        ....oGYGGoY.....
        ....oGGGgoY.....
        ...oGGGggg.o....
        ...ooooooooo....
        .......o........
        ......obbo......
        ......obBo......
        ......obBo......
        .....oyybBo.....
        .....obbbBo.....
        .....oYYYYo.....
        .....obbbBo.....
        .....obbbBo.....
        .....obbbBo.....
        .....oYYYYo.....
        .....obbbBo.....
        .....obbbBo.....
        .....obbbBo.....
        .....obbbBo.....
        ....oobbbBoo....
        ...oBbbbbbBBo...
        ...oooooooooo...
        ................
        ................
    ''', MISC)


def boat(frame):
    """32x32 sailing boat facing right."""
    M = MISC
    img = blank(32, 32)
    # hull
    for y in range(20, 28):
        t = (y - 20) / 7.0
        x0 = int(3 + t * 4)
        x1 = int(29 - t * 3)
        for x in range(x0, x1 + 1):
            img[y][x] = M['b'] if y < 25 else M['B']
    for x in range(3, 30):
        img[20][x] = M['Y']
        img[21][x] = M['y']
    for x in range(5, 28):
        img[23][x] = M['G'] if (x // 2) % 2 else M['g']
    # mast
    for y in range(3, 20):
        img[y][14] = M['B']
        img[y][15] = M['b']
    # sail (billows with the frame)
    bulge = 1 + frame
    for y in range(4, 18):
        t = (y - 4) / 13.0
        w = int(2 + t * 11 + math.sin(t * math.pi) * bulge)
        for x in range(16, 16 + w):
            img[y][x] = M['w'] if (x - 16) < w - 2 else M['l']
        if w > 3:
            img[y][16 + w // 2] = M['l'] if y % 4 == 0 else img[y][16 + w // 2]
    # little flag
    for (x, y) in [(15, 1), (16, 1), (17, 1), (15, 2), (16, 2)]:
        img[y][x] = M['G']
    outline(img, M['o'])
    return img


# =====================================================================
# Particles and effects (OBJ bank 15)
# =====================================================================

def fx8(text):
    return grid(text, FX)


FX8 = {}
FX8['SNOW'] = fx8('''
    ........
    ...w....
    .w.A.w..
    ..AwA...
    .wAwAw..
    ..AwA...
    .w.A.w..
    ...w....
''')
FX8['SNOW_SMALL'] = fx8('''
    ........
    ........
    ...A....
    ..AwA...
    ...A....
    ........
    ........
    ........
''')
FX8['ASH'] = fx8('''
    ........
    ........
    ..nE....
    .nEEe...
    ..nEn...
    ...n....
    ........
    ........
''')
FX8['EMBER'] = fx8('''
    ........
    ........
    ...f....
    ..fYf...
    ...r....
    ........
    ........
    ........
''')
FX8['DUST0'] = fx8('''
    ........
    ..ee....
    .ewwe.e.
    .ewwee..
    ..eee...
    ........
    ........
    ........
''')
FX8['DUST1'] = fx8('''
    ........
    ........
    ..e.....
    .e..e...
    ....e...
    ..e.....
    ........
    ........
''')
FX8['SPARK'] = fx8('''
    ...Y....
    ...Y....
    ..YwY...
    YYwwwYY.
    ..YwY...
    ...Y....
    ...Y....
    ........
''')
FX8['SPARKLE0'] = fx8('''
    ........
    ...w....
    ...w....
    .wwAww..
    ...w....
    ...w....
    ........
    ........
''')
FX8['SPARKLE1'] = fx8('''
    ........
    ........
    ..A.A...
    ...w....
    ..A.A...
    ........
    ........
    ........
''')
FX8['BUBBLE'] = fx8('''
    ........
    ..AAA...
    .A.wwA..
    .A..wA..
    .A...A..
    ..AAA...
    ........
    ........
''')
FX8['STREAK'] = fx8('''
    ........
    ........
    ........
    .AAwwww.
    ........
    ........
    ........
    ........
''')
FX8['MARK_TOWN'] = fx8('''
    ...o....
    ..ofo...
    .ofYfo..
    ofYwYfo.
    .ofYfo..
    ..ofo...
    ...o....
    ........
''')
FX8['MARK_DIM'] = fx8('''
    ........
    ...o....
    ..oEo...
    .oEeEo..
    ..oEo...
    ...o....
    ........
    ........
''')
FX8['MARK_SKY'] = fx8('''
    ...o....
    ..oAo...
    .oAwAo..
    oAwwwAo.
    .oAwAo..
    ..oAo...
    ...o....
    ........
''')
FX8_NAMES = list(FX8.keys())


def fx16_wake(frame):
    F = FX
    img = blank(16, 16)
    spread = 5 + frame * 2
    for k in range(spread):
        y = 11 + k // 2
        for x in (7 - k, 8 + k):
            if 0 <= x < 16 and y < 16:
                img[y][x] = F['w'] if k < 2 else F['A']
    for x in range(3, 13):
        if img[10][x] == 0 and (x + frame) % 3 == 0:
            img[10][x] = F['A']
    return img


def fx16_splash(frame):
    F = FX
    img = blank(16, 16)
    pts = [(3, 9), (5, 6), (8, 4), (11, 6), (13, 9)] if frame == 0 else \
          [(1, 7), (4, 3), (8, 1), (12, 3), (14, 7), (2, 12), (13, 12)]
    for (x, y) in pts:
        img[y][x] = F['w']
        put(img, x, y + 1, F['A'])
        if frame == 0:
            put(img, x + 1, y, F['A'])
    for x in range(2, 14):
        img[14][x] = F['A'] if x % 2 else F['w']
    return img


def fx16_shadow(rx, ry):
    F = FX
    img = blank(16, 16)
    for y in range(16):
        for x in range(16):
            dx, dy = (x + 0.5 - 8) / rx, (y + 0.5 - 12) / ry
            if dx * dx + dy * dy <= 1.0 and (x + y) % 2 == 0:
                img[y][x] = F['k']
    return img


def fx16_flash():
    F = FX
    img = blank(16, 16)
    for y in range(16):
        for x in range(16):
            r = math.hypot(x + 0.5 - 8, y + 0.5 - 8)
            if 5.2 < r < 7.4:
                img[y][x] = F['w'] if r < 6.4 else F['Y']
            elif r < 2.2:
                img[y][x] = F['w']
    return img


def fx16_cursor(frame):
    F = FX
    img = blank(16, 16)
    i = 1 if frame else 0
    for (cx, cy, sx, sy) in [(i, i, 1, 1), (15 - i, i, -1, 1), (i, 15 - i, 1, -1), (15 - i, 15 - i, -1, -1)]:
        for k in range(4):
            put(img, cx + sx * k, cy, F['w'])
            put(img, cx, cy + sy * k, F['w'])
    outline(img, F['r'])
    return img


def fx16_pin():
    return fx8.__call__('''
        .....oooo.......
        ....orrrro......
        ...orrwwrro.....
        ...orwwwwro.....
        ...orwwwwro.....
        ...orrwwrro.....
        ....orrrro......
        .....orro.......
        .....orro.......
        ......oo........
        ................
        ................
        ................
        ................
        ................
        ................
    ''')


def fx16_gull(frame):
    if frame == 0:
        return fx8('''
            ................
            ................
            ................
            .oo.........oo..
            .oeoo.....ooeo..
            ..oeeo...oeeo...
            ...oeeoooeeo....
            ....oewwweo.....
            .....owwwofo....
            ......ooo.......
            ................
            ................
            ................
            ................
            ................
            ................
        ''')
    return fx8('''
        ................
        ................
        ................
        ................
        ................
        ................
        ....ooooooo.....
        ..ooeewwweeoo...
        .oeeoowwwoofo...
        .oo...ooo...oo..
        ................
        ................
        ................
        ................
        ................
        ................
    ''')


def fx16_chevron(vertical):
    F = FX
    img = blank(16, 16)
    for base in (3, 9):
        for k in range(4):
            for (x, y) in [(base + k, 4 + k), (base + k, 11 - k)]:
                if vertical:
                    x, y = y, x
                img[y][x] = F['w'] if k > 1 else F['A']
    return img


def fx16_ring():
    F = FX
    img = blank(16, 16)
    for y in range(16):
        for x in range(16):
            dx, dy = (x + 0.5 - 8) / 7.0, (y + 0.5 - 11) / 3.8
            r = math.sqrt(dx * dx + dy * dy)
            if 0.72 < r <= 1.0:
                img[y][x] = F['A'] if (x // 2 + y) % 3 else F['w']
    return img


FX16 = [
    ('WAKE0', fx16_wake(0)), ('WAKE1', fx16_wake(1)),
    ('SPLASH0', fx16_splash(0)), ('SPLASH1', fx16_splash(1)),
    ('SHADOW', fx16_shadow(6.5, 3.2)), ('SHADOW_SMALL', fx16_shadow(4.0, 2.2)),
    ('FLASH', fx16_flash()), ('CURSOR0', fx16_cursor(0)), ('CURSOR1', fx16_cursor(1)),
    ('PIN', fx16_pin()), ('GULL0', fx16_gull(0)), ('GULL1', fx16_gull(1)),
    ('CHEVRON_H', fx16_chevron(False)), ('CHEVRON_V', fx16_chevron(True)),
    ('RIPPLE', fx16_ring()),
]


# =====================================================================
# The player on a BIKE (OBJ bank 0, the player's palette)
# =====================================================================

def pl(ch):
    return PLAYER_IDX[ch]


def stamp_rows(img, rows, ox, oy):
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != '.':
                put(img, ox + x, oy + y, pl(ch))


def line(img, x0, y0, x1, y1, v):
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        put(img, x0, y0, v)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def wheel_side(img, cx, cy, r, spin):
    for y in range(cy - r - 1, cy + r + 2):
        for x in range(cx - r - 1, cx + r + 2):
            d = math.hypot(x - cx, y - cy)
            if r - 1.0 <= d <= r + 0.45:
                put(img, x, y, pl('o'))
            elif r - 2.0 <= d < r - 1.0:
                put(img, x, y, pl('P'))
    for k in range(4):
        a = (k * 0.25 + spin * 0.125) * 2 * math.pi
        for t in (1, 2):
            put(img, int(round(cx + math.cos(a) * t)), int(round(cy + math.sin(a) * t)), pl('p'))
    put(img, cx, cy, pl('W'))


def bike_frame(view, phase):
    P = gf.parse16
    img = blank(32, 32)
    if view == 'left':
        # bike: front wheel left, rear right
        wheel_side(img, 8, 26, 5, phase)
        wheel_side(img, 24, 26, 5, phase + 1)
        for (a, b) in [((8, 26), (10, 18)), ((24, 26), (19, 20)), ((19, 20), (11, 20)),
                       ((24, 26), (15, 26)), ((15, 26), (19, 20)), ((15, 26), (11, 20))]:
            line(img, a[0], a[1], b[0], b[1], pl('R'))
        line(img, 12, 21, 18, 21, pl('r'))
        for x in range(17, 22):
            put(img, x, 19, pl('Y'))
        put(img, 9, 17, pl('W'))
        put(img, 10, 17, pl('W'))
        put(img, 8, 17, pl('o'))
        stamp_rows(img, P(PLAYER['head_left']), 9, 1)
        stamp_rows(img, P(PLAYER['body_left']), 9, 13)
        # arm reaching to the bars
        for (x, y) in [(12, 16), (11, 17), (10, 17)]:
            put(img, x, y, pl('j'))
        put(img, 9, 18, pl('k'))
        # leg on the near pedal
        pedal = (15 + (3 if phase else -3), 26 + (-1 if phase else 1))
        knee = (14 if phase else 13, 21)
        line(img, 19, 19, knee[0], knee[1], pl('p'))
        line(img, 18, 19, knee[0] - 1, knee[1], pl('P'))
        line(img, knee[0], knee[1], pedal[0], pedal[1] - 1, pl('P'))
        put(img, pedal[0], pedal[1], pl('o'))
        put(img, pedal[0] - 1, pedal[1], pl('o'))
    else:
        down = view == 'down'
        wx = 14
        # wheel (seen end-on)
        for y in range(23, 32):
            put(img, wx, y, pl('o'))
            put(img, wx + 3, y, pl('o'))
            put(img, wx + 1, y, pl('P'))
            put(img, wx + 2, y, pl('p' if (y + phase) % 3 else 'P'))
        put(img, wx + 1, 31, pl('o'))
        put(img, wx + 2, 31, pl('o'))
        if down:
            stamp_rows(img, P(PLAYER['head_down']), 8, 2)
            stamp_rows(img, P(PLAYER['body_down']), 8, 14)
        else:
            stamp_rows(img, P(PLAYER['head_up']), 8, 2)
            stamp_rows(img, P(PLAYER['body_up']), 8, 14)
        # handlebar across (in front when facing down, hidden behind the back when up)
        bar_y = 20 if down else 15
        for x in range(6, 26):
            if not down and 8 <= x <= 23:
                continue
            put(img, x, bar_y, pl('W') if 8 <= x <= 23 else pl('P'))
        put(img, 5, bar_y, pl('o'))
        put(img, 26, bar_y, pl('o'))
        if down:
            put(img, 7, bar_y - 1, pl('k'))
            put(img, 24, bar_y - 1, pl('k'))
            for y in range(20, 24):
                put(img, 15, y, pl('R'))
                put(img, 16, y, pl('r'))
        # legs pedalling on both sides
        up_l = phase == 0
        for side, (lx, up) in enumerate(((11, up_l), (19, not up_l))):
            y0, y1 = 20, (23 if up else 26)
            for y in range(y0, y1):
                put(img, lx, y, pl('p'))
                put(img, lx + 1, y, pl('P'))
            put(img, lx, y1, pl('o'))
            put(img, lx + 1, y1, pl('o'))
        if not down:
            for x in range(13, 19):
                put(img, x, 20, pl('Y'))
    outline(img, pl('o'))
    return img


def bike_frames():
    frames = []
    for view in ('down', 'up', 'left'):
        for ph in (0, 1):
            frames.append(bike_frame(view, ph))
    return frames


# =====================================================================
# Crests (their own palette; the CREST CASE loads it into an OBJ bank)
# =====================================================================

CREST = Pal([('o', (32, 24, 48)), ('g', (176, 120, 32)), ('G', (240, 192, 64)), ('Y', (255, 240, 160)),
             ('u', (40, 88, 184)), ('U', (80, 152, 232)), ('i', (176, 224, 248)), ('w', (248, 248, 248)),
             ('n', (88, 88, 108)), ('N', (156, 156, 176)), ('r', (240, 120, 48)), ('v', (104, 56, 152)),
             ('V', (172, 116, 220)), ('p', (240, 150, 200)), ('b', (232, 220, 196))])


def crest_base(img, rim, rim_hi, face):
    for y in range(32):
        for x in range(32):
            d = math.hypot(x + 0.5 - 16, y + 0.5 - 16)
            if d <= 13.8:
                if d > 11.6:
                    img[y][x] = rim_hi if (x + 0.5 - 16) + (y + 0.5 - 16) < -4 else rim
                else:
                    img[y][x] = face


def emblem(img, pts, v):
    for (x, y) in pts:
        put(img, x, y, v)


def crest(kind):
    C = CREST
    img = blank(32, 32)
    if kind == 'VOLT':
        crest_base(img, C['g'], C['Y'], C['u'])
        bolt = [(18, 7), (17, 8), (16, 9), (15, 10), (14, 11), (13, 12), (12, 13), (12, 14), (13, 15),
                (14, 15), (15, 15), (16, 15), (15, 16), (14, 17), (13, 18), (12, 19), (11, 20), (10, 21),
                (10, 22), (11, 22)]
        for (x, y) in bolt:
            for dx in range(0, 4):
                if img[y][x + dx] == C['u']:
                    img[y][x + dx] = C['Y'] if dx < 2 else C['G']
        for (x, y) in [(18, 12), (19, 12), (20, 12), (19, 13), (18, 14), (17, 15)]:
            img[y][x] = C['G']
    elif kind == 'TIDE':
        crest_base(img, C['N'], C['w'], C['u'])
        for y in range(7, 26):
            for x in range(6, 26):
                if img[y][x] != C['u']:
                    continue
                cx, cy = 16, 17
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                a = math.atan2(y + 0.5 - cy, x + 0.5 - cx)
                curl = 6.5 - (a + math.pi) * 0.7
                if y > 18 and (x + y) % 3:
                    img[y][x] = C['U']
                if abs(d - curl) < 1.2 and a < 1.6:
                    img[y][x] = C['w'] if d < curl else C['i']
    elif kind == 'ANVIL':
        crest_base(img, C['n'], C['N'], C['o'])
        anvil = grid('''
            ..NNNNNNNNNNNNNNN.
            NNwwNNNNNNNNNNNNNN
            .NNNNNNNNNNNNNNNnn
            ..nnNNNNNNNNNnn...
            .....NNNNNNNn.....
            .....NNNNNNnn.....
            ....NNNNNNNNnn....
            ...nnnnnnnnnnnn...
        ''', C)
        paste(img, anvil, 7, 13)
        for (x, y) in [(12, 10), (15, 8), (19, 9), (13, 7), (17, 11), (21, 7)]:
            img[y][x] = C['r']
            put(img, x, y + 1, C['G'])
    elif kind == 'RIME':
        crest_base(img, C['i'], C['w'], C['U'])
        for k in range(6):
            a = k * math.pi / 3
            for t in range(1, 10):
                x, y = int(round(16 + math.cos(a) * t)), int(round(16 + math.sin(a) * t))
                img[y][x] = C['w']
                if t in (5, 7):
                    for s in (-1, 1):
                        b = a + s * 0.9
                        put(img, int(round(x + math.cos(b) * 2)), int(round(y + math.sin(b) * 2)), C['i'])
        img[16][16] = C['i']
    elif kind == 'LANTERN':
        crest_base(img, C['b'], C['w'], C['v'])
        lan = grid('''
            ....oo....
            ...o..o...
            ..oNNNNo..
            ..oYGGYo..
            ..oGYYGo..
            ..oGYYGo..
            ..oYGGYo..
            ..oNNNNo..
            ...oooo...
        ''', C)
        paste(img, lan, 11, 9)
        for (x, y) in [(10, 13), (21, 13), (9, 16), (22, 16), (10, 19), (21, 19)]:
            img[y][x] = C['V']
    elif kind == 'DREAM':
        crest_base(img, C['V'], C['p'], C['v'])
        for y in range(32):
            for x in range(32):
                d1 = math.hypot(x + 0.5 - 15, y + 0.5 - 16)
                d2 = math.hypot(x + 0.5 - 19, y + 0.5 - 13.5)
                if d1 <= 8.0 and d2 > 7.0 and img[y][x] == C['v']:
                    img[y][x] = C['Y'] if d1 < 6.5 else C['G']
        for (x, y) in [(21, 19), (20, 20), (22, 20), (21, 21), (21, 20), (23, 9), (24, 9), (23, 10)]:
            img[y][x] = C['w']
    else:   # empty slot
        for y in range(32):
            for x in range(32):
                d = math.hypot(x + 0.5 - 16, y + 0.5 - 16)
                if 11.8 < d <= 13.8 and (x + y) % 2 == 0:
                    img[y][x] = C['n']
        return img
    outline(img, C['o'])
    return img


CRESTS = ['VOLT', 'TIDE', 'ANVIL', 'RIME', 'LANTERN', 'DREAM', 'EMPTY']


# =====================================================================
# The town map of the Vale (BG, 240x160, one palette bank)
# =====================================================================

MAP_PAL = Pal([('K', (40, 32, 56)), ('D', (36, 70, 144)), ('S', (56, 104, 184)), ('s', (104, 160, 216)),
               ('W', (240, 244, 236)), ('Y', (224, 200, 136)), ('G', (116, 184, 88)), ('g', (72, 140, 76)),
               ('F', (40, 94, 64)), ('R', (148, 140, 150)), ('r', (96, 88, 104)), ('I', (184, 206, 230)),
               ('V', (178, 150, 214)), ('L', (206, 80, 50)), ('A', (128, 112, 104))])

# Every place on the town map: key, x, y, kind (town, route, lair, isle).
# Region owners: these are the pixels FLY markers are drawn at; set your
# FlyPoint map_x/map_y to the same numbers (Maple Village is 104,110).
SPOTS = [
    ('MAPLE', 104, 110, 'town'), ('MEADOW', 100, 92, 'route'), ('RISE', 94, 74, 'route'),
    ('WOOD', 128, 110, 'route'), ('LAKE', 78, 110, 'route'), ('WILLOW', 102, 130, 'town'),
    ('SALTWIND', 54, 112, 'route'), ('PORT_BRINE', 30, 108, 'town'), ('SEA_ROUTE', 26, 128, 'route'),
    ('GULL_ISLE', 22, 146, 'town'), ('DROWNED_BELL', 46, 146, 'lair'),
    ('FROSTPINE', 86, 56, 'route'), ('FROSTHOLLOW', 84, 38, 'town'), ('WHITECROWN', 76, 22, 'lair'),
    ('SKY_ISLE', 122, 12, 'isle'), ('GLIMMER', 114, 38, 'route'), ('STARFALL', 140, 30, 'lair'),
    ('COPPERLINE', 152, 110, 'route'), ('LUMEN', 156, 88, 'town'), ('ELDERWOOD', 126, 132, 'lair'),
    ('MOONVEIL', 160, 68, 'route'), ('DREAMSPIRE', 166, 48, 'town'), ('DUST_LIBRARY', 192, 40, 'lair'),
    ('CINDER_ROAD', 180, 88, 'route'), ('CINDERMOOR', 204, 88, 'town'), ('EMBER_TUNNEL', 220, 74, 'route'),
    ('CALDERA', 228, 58, 'lair'), ('CLOCKWORK', 206, 112, 'lair'),
    ('ASHEN', 156, 132, 'route'), ('GRAVEWOOD', 178, 134, 'route'), ('DUSKMERE', 198, 134, 'town'),
    ('OSSUARY', 216, 140, 'route'), ('BONE_THRONE', 232, 150, 'lair'),
]
SPOT = {k: (x, y) for (k, x, y, _) in SPOTS}

ROUTES = [
    ('MAPLE', 'MEADOW'), ('MEADOW', 'RISE'), ('RISE', 'FROSTPINE'), ('FROSTPINE', 'FROSTHOLLOW'),
    ('FROSTHOLLOW', 'WHITECROWN'), ('FROSTHOLLOW', 'GLIMMER'), ('GLIMMER', 'STARFALL'),
    ('MAPLE', 'LAKE'), ('LAKE', 'SALTWIND'), ('SALTWIND', 'PORT_BRINE'), ('MAPLE', 'WOOD'),
    ('MAPLE', 'WILLOW'), ('WOOD', 'COPPERLINE'), ('WOOD', 'ELDERWOOD'), ('COPPERLINE', 'LUMEN'),
    ('COPPERLINE', 'ASHEN'), ('LUMEN', 'MOONVEIL'), ('MOONVEIL', 'DREAMSPIRE'),
    ('DREAMSPIRE', 'DUST_LIBRARY'), ('LUMEN', 'CINDER_ROAD'), ('CINDER_ROAD', 'CINDERMOOR'),
    ('CINDERMOOR', 'EMBER_TUNNEL'), ('EMBER_TUNNEL', 'CALDERA'), ('CINDERMOOR', 'CLOCKWORK'),
    ('ASHEN', 'GRAVEWOOD'), ('GRAVEWOOD', 'DUSKMERE'), ('DUSKMERE', 'OSSUARY'), ('OSSUARY', 'BONE_THRONE'),
]
SEA_ROUTES = [('PORT_BRINE', 'SEA_ROUTE'), ('SEA_ROUTE', 'GULL_ISLE'), ('GULL_ISLE', 'DROWNED_BELL')]


def smooth_noise(x, y, scale, seed):
    """Value noise in [0, 1]."""
    gx, gy = x / scale, y / scale
    x0, y0 = int(math.floor(gx)), int(math.floor(gy))
    fx, fy = gx - x0, gy - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)

    def v(ix, iy):
        return (hash2(ix, iy, seed) & 1023) / 1023.0
    a = v(x0, y0) + (v(x0 + 1, y0) - v(x0, y0)) * fx
    b = v(x0, y0 + 1) + (v(x0 + 1, y0 + 1) - v(x0, y0 + 1)) * fx
    return a + (b - a) * fy


def is_land(x, y):
    """The Vale: one big land mass with a ragged west coast, the Sea Route
    bay in the south-west, Gull Isle and the sea all round."""
    n = smooth_noise(x, y, 11.0, 7) * 7 - 3.5
    if y < 16:
        return False
    west = 20 + n
    if y > 118:
        west = 64 + n + (y - 118) * 0.2
    if x < west or x > 236 + n * 0.4:
        return False
    if y > 153 + n * 0.5:
        return False
    if y < 22 + n and not (60 < x < 150):
        return False
    return True


def gull_isle(x, y):
    return ((x - 22) / 9.0) ** 2 + ((y - 147) / 6.5) ** 2 <= 1.0 + smooth_noise(x, y, 4, 3) * 0.25


def biome(x, y):
    if y < 62 and x < 148:
        return 'snow'
    if x >= 148 and y < 76:
        return 'dream'
    if x >= 190 and y < 104:
        return 'volcano'
    if y >= 120 and x >= 142:
        return 'grim'
    if 114 <= x <= 142 and 98 <= y <= 144:
        return 'forest'
    if 90 <= x <= 114 and 122 <= y <= 142:
        return 'farm'
    return 'meadow'


def paint_town_map():
    M = MAP_PAL
    W, H = 240, 160
    img = blank(W, H)
    land = [[is_land(x, y) or gull_isle(x, y) for x in range(W)] for y in range(H)]

    def coast_dist(x, y, r):
        for d in range(1, r + 1):
            for (dx, dy) in ((d, 0), (-d, 0), (0, d), (0, -d)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H and land[yy][xx]:
                    return d
        return r + 1

    # sea: deep far out, lighter near the shore, a surf line at the coast;
    # small waves on an 8x8 lattice so the tiles repeat
    for y in range(H):
        for x in range(W):
            if land[y][x]:
                continue
            d = coast_dist(x, y, 6)
            if d <= 1:
                img[y][x] = M['W'] if (x + y) % 3 else M['s']
            elif d <= 4:
                img[y][x] = M['s']
            else:
                img[y][x] = M['S']
                if y < 16:
                    img[y][x] = M['D'] if (x // 8 + y // 8) % 2 else M['S']
                if (x % 16, y % 8) in ((3, 2), (4, 2), (5, 3), (11, 6), (12, 6), (13, 5)):
                    img[y][x] = M['s']
    # land by biome, with lattice textures (8x8 periodic) and a few features
    for y in range(H):
        for x in range(W):
            if not land[y][x]:
                continue
            b = biome(x, y)
            lx, ly = x % 8, y % 8
            if gull_isle(x, y) and not is_land(x, y):
                b = 'meadow'
            if b == 'snow':
                v = M['W'] if (lx + ly * 3) % 7 else M['I']
            elif b == 'dream':
                v = M['V'] if (lx * 5 + ly) % 9 else M['W']
                if (lx, ly) in ((2, 5), (6, 1)):
                    v = M['G']
            elif b == 'volcano':
                v = M['r'] if (lx + ly) % 5 else M['A']
            elif b == 'grim':
                v = M['A'] if (lx * 3 + ly) % 7 else M['r']
            elif b == 'forest':
                v = M['g']
            elif b == 'farm':
                v = M['Y'] if (ly // 2) % 2 else M['G']
            else:
                v = M['G'] if (lx * 7 + ly * 3) % 11 else M['g']
            # sand beaches along the sea
            if b in ('meadow', 'farm') and coast_dist(x, y, 2) <= 2 and not (x > 60 and y < 60):
                v = M['Y']
            img[y][x] = v

    def blob(cx, cy, rx, ry, v, edge=None, seed=1):
        for y in range(int(cy - ry - 2), int(cy + ry + 3)):
            for x in range(int(cx - rx - 2), int(cx + rx + 3)):
                if not (0 <= x < W and 0 <= y < H):
                    continue
                n = smooth_noise(x, y, 3.0, seed) * 0.35
                d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
                if d <= 1.0 - n:
                    img[y][x] = v
                elif edge is not None and d <= 1.25 - n:
                    img[y][x] = edge

    # Mirror Lake and the river from the mountains
    for t in range(0, 101):
        f = t / 100.0
        x = int(round(88 + (72 - 88) * f + math.sin(f * 6) * 3))
        y = int(round(58 + (100 - 58) * f))
        for dx in (0, 1):
            put(img, x + dx, y, M['s'])
    blob(70, 102, 9, 6, M['S'], M['s'], seed=5)
    # mountains: peaks in the north (Frosthollow, Whitecrown) and the volcano
    def peak(px, py, h, snow=True, lava=False):
        for dy in range(h):
            half = dy * 0.9 + 1
            for x in range(int(px - half), int(px + half) + 1):
                y = py + dy
                if not (0 <= x < W and 0 <= y < H) or not land[y][x]:
                    continue
                left = x < px
                if lava and dy < 3:
                    v = M['L'] if abs(x - px) < 2 else M['r']
                elif snow and dy < h * 0.45:
                    v = M['W'] if left else M['I']
                else:
                    v = M['R'] if left else M['r']
                img[y][x] = v
        for dy in range(h):
            half = dy * 0.9 + 1
            put(img, int(px - half) - 1, py + dy, M['K'])
            put(img, int(px + half) + 1, py + dy, M['K'])
    for (px, py, h) in [(62, 30, 12), (72, 18, 14), (98, 24, 12), (130, 28, 11), (110, 48, 9), (66, 46, 10),
                        (140, 44, 8), (52, 58, 8)]:
        peak(px, py, h)
    peak(230, 48, 13, snow=False, lava=True)
    peak(214, 60, 8, snow=False)
    # lava streams off the caldera
    for t in range(40):
        put(img, 229 - t // 6, 61 + t // 2, M['L'])
    # the Stormstone Rise: a lone crag
    peak(92, 66, 7, snow=False)
    # forests: tree clumps
    for i in range(70):
        x = 114 + (hash2(i, 1, 9) % 30)
        y = 98 + (hash2(i, 2, 9) % 46)
        if biome(x, y) == 'forest' and land[y][x]:
            blob(x, y, 2.2, 1.8, M['F'], None, seed=i)
            put(img, x - 1, y - 1, M['G'])
    for i in range(24):   # scattered woods in the meadows
        x = 40 + (hash2(i, 3, 4) % 110)
        y = 70 + (hash2(i, 4, 4) % 50)
        if biome(x, y) == 'meadow' and land[y][x] and img[y][x] in (M['G'], M['g']):
            blob(x, y, 1.8, 1.4, M['F'], None, seed=i + 40)
    # grim: dead trees and graves
    for i in range(30):
        x = 144 + (hash2(i, 5, 2) % 92)
        y = 122 + (hash2(i, 6, 2) % 30)
        if land[y][x] and biome(x, y) == 'grim':
            for k in range(3):
                put(img, x, y - k, M['K'])
            put(img, x - 1, y - 2, M['K'])
            put(img, x + 1, y - 3, M['K'])
    # dream mist and the spire
    for i in range(20):
        x = 150 + (hash2(i, 7, 3) % 80)
        y = 30 + (hash2(i, 8, 3) % 40)
        if land[y][x] and biome(x, y) == 'dream':
            for k in range(4):
                put(img, x + k, y, M['W'])
    # routes: tan paths on land, dotted white lanes on water
    def path(a, b, sea=False):
        (x0, y0), (x1, y1) = SPOT[a], SPOT[b]
        n = max(abs(x1 - x0), abs(y1 - y0)) + 1
        for i in range(n + 1):
            f = i / float(n)
            # a gentle bend so roads don't look ruled
            bend = math.sin(f * math.pi) * (3 if (x0 + y1) % 2 else -3)
            x = int(round(x0 + (x1 - x0) * f + (bend if abs(y1 - y0) > abs(x1 - x0) else 0)))
            y = int(round(y0 + (y1 - y0) * f + (bend if abs(y1 - y0) <= abs(x1 - x0) else 0)))
            if sea:
                if i % 4 < 2:
                    put(img, x, y, M['W'])
                continue
            for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                if 0 <= x + dx < W and 0 <= y + dy < H and land[y + dy][x + dx]:
                    img[y + dy][x + dx] = M['Y']
            for (dx, dy) in ((-1, 0), (2, 0), (0, -1), (0, 2), (-1, 1), (2, 1), (1, -1), (1, 2)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H and land[yy][xx] and img[yy][xx] not in (M['Y'], M['K']):
                    if img[yy][xx] in (M['G'], M['W'], M['V'], M['I']):
                        img[yy][xx] = M['g'] if img[yy][xx] == M['G'] else M['R']
    for (a, b) in ROUTES:
        path(a, b)
    for (a, b) in SEA_ROUTES:
        path(a, b, sea=True)
    # towns: small clusters of roofs
    def town(key, roof):
        cx, cy = SPOT[key]
        for (dx, dy) in ((-5, -4), (2, -5), (-2, 1), (4, 1), (-7, 2)):
            x0, y0 = cx + dx, cy + dy
            for y in range(y0, y0 + 3):
                for x in range(x0, x0 + 4):
                    put(img, x, y, roof if y == y0 else M['W'])
            put(img, x0 + 1, y0 + 2, M['K'])
    for (key, x, y, kind) in SPOTS:
        if kind == 'town':
            town(key, M['L'] if key not in ('FROSTHOLLOW', 'DREAMSPIRE') else M['V'])
    # Lumen City: grey blocks
    cx, cy = SPOT['LUMEN']
    for y in range(cy - 7, cy + 6):
        for x in range(cx - 9, cx + 9):
            if (x - cx) % 5 != 0 and (y - cy) % 4 != 0:
                put(img, x, y, M['R'] if (x + y) % 7 else M['W'])
    # the Clockwork Spire and the Dream Spire: towers
    for (key, v) in (('CLOCKWORK', M['R']), ('DREAMSPIRE', M['V'])):
        cx, cy = SPOT[key]
        for y in range(cy - 12, cy + 1):
            w = 1 if y < cy - 8 else 2
            for x in range(cx - w, cx + w + 1):
                put(img, x, y, v if x <= cx else M['r'])
        put(img, cx, cy - 13, M['W'])
    # the Sky Isle: a floating island in a cloud bank
    blob(122, 11, 16, 5, M['W'], M['I'], seed=11)
    blob(104, 13, 8, 3, M['W'], M['I'], seed=12)
    blob(142, 12, 9, 3, M['W'], M['I'], seed=13)
    blob(122, 12, 7, 3, M['G'], M['g'], seed=14)
    for x in range(117, 128):
        put(img, x, 15, M['r'])
    for x in range(119, 126):
        put(img, x, 16, M['r'])
    # a compass rose in the south-east sea corner area (top right is land)
    return img


def compass(img):
    M = MAP_PAL
    cx, cy = 14, 24
    for k in range(-5, 6):
        put(img, cx, cy + k, M['W'])
        put(img, cx + k, cy, M['W'])
    put(img, cx, cy - 6, M['L'])
    put(img, cx, cy - 7, M['L'])
    for (dx, dy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        put(img, cx + dx, cy + dy, M['Y'])


def encode_bg(img, max_tiles, what):
    """Cut an index image into deduplicated 8x8 tiles (with flips).
    Returns (tiles, screen entries row-major)."""
    h, w = len(img), len(img[0])
    tiles, lookup, screen = [], {}, []
    for ty in range(h // 8):
        for tx in range(w // 8):
            t = tuple(img[ty * 8 + y][tx * 8 + x] for y in range(8) for x in range(8))
            ent = None
            for (hf, vf) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                v = tuple(t[(7 - y if vf else y) * 8 + (7 - x if hf else x)] for y in range(8) for x in range(8))
                if v in lookup:
                    ent = lookup[v] | (hf << 10) | (vf << 11)
                    break
            if ent is None:
                ent = len(tiles)
                lookup[t] = ent
                tiles.append(t)
            screen.append(ent)
    if len(tiles) > max_tiles:
        raise SystemExit('%s: %d unique tiles (budget %d)' % (what, len(tiles), max_tiles))
    return [gf.pack4(list(t)) for t in tiles], screen


# =====================================================================
# The sea for the ferry voyage (BG, 256 wide so it scrolls seamlessly)
# =====================================================================

SEA_PAL = Pal([('k', (40, 56, 88)), ('1', (192, 228, 248)), ('2', (144, 200, 240)), ('3', (104, 164, 232)),
               ('c', (248, 248, 248)), ('C', (208, 224, 240)), ('i', (72, 104, 112)), ('I', (104, 144, 112)),
               ('h', (168, 204, 228)), ('D', (32, 72, 152)), ('S', (52, 108, 192)), ('s', (96, 160, 224)),
               ('f', (224, 240, 248)), ('y', (255, 240, 176))])
SEA_H = 160


def paint_sea():
    S = SEA_PAL
    W, H = 256, SEA_H
    img = blank(W, H)
    horizon = 58
    for y in range(horizon):
        for x in range(W):
            # dithered sky gradient in 8px bands
            band = y / float(horizon)
            if band < 0.35:
                v = S['3'] if (band < 0.25 or (x + y) % 2) else S['2']
            elif band < 0.7:
                v = S['2'] if (band < 0.6 or (x + y) % 2) else S['1']
            else:
                v = S['1']
            img[y][x] = v
    # clouds (period 128 so the sky tiles repeat)
    for (cx, cy, rx, ry) in [(30, 18, 16, 5), (44, 14, 10, 5), (92, 30, 14, 4), (100, 26, 8, 4)]:
        for rep in (0, 128):
            for y in range(cy - ry - 1, cy + ry + 2):
                for x in range(cx - rx - 1 + rep, cx + rx + 2 + rep):
                    d = ((x - rep + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
                    if d <= 1.0 and 0 <= x < W:
                        img[y][x] = S['c'] if y < cy + ry * 0.3 else S['C']
    # a distant island with a lighthouse on the horizon
    for x in range(150, 214):
        top = horizon - int(7 * math.sin((x - 150) / 64.0 * math.pi) + smooth_noise(x, 0, 6, 2) * 3)
        for y in range(top, horizon):
            img[y][x] = S['I'] if y < top + 2 else S['i']
    for y in range(horizon - 14, horizon - 7):
        img[y][176] = S['c']
        img[y][177] = S['C']
    img[horizon - 15][176] = S['y']
    for x in range(W):
        img[horizon][x] = S['h']
        img[horizon + 1][x] = S['s']
    # sea: bands of waves that grow toward the viewer (period 32)
    for y in range(horizon + 2, H):
        depth = (y - horizon) / float(H - horizon)
        for x in range(W):
            v = S['S'] if depth > 0.25 else S['s']
            if depth > 0.6 and ((x // 4) + y // 3) % 5 == 0:
                v = S['D']
            period = 8 if depth < 0.3 else (16 if depth < 0.65 else 32)
            ph = (x + (y * 3 if depth > 0.3 else y)) % period
            crest_row = (y - horizon) % (3 if depth < 0.3 else (5 if depth < 0.65 else 8)) == 0
            if crest_row and ph < period // 4:
                v = S['f'] if ph < period // 8 + 1 else S['s']
            img[y][x] = v
    return img


# =====================================================================
# Output
# =====================================================================

def fmt_u32(words, per=8, indent='    '):
    return gf.fmt_u32(words, per, indent)


def fmt_u16(vals, per=8, indent='    '):
    return gf.fmt_u16(vals, per, indent)


def emit_frames(o, ctype, name, frames, per_frame_words, comment):
    o.append('/* %s */' % comment)
    o.append('static const u32 %s[%d][%d] = {' % (name, len(frames), per_frame_words))
    for f in frames:
        w = words_of(f)
        assert len(w) == per_frame_words, (name, len(w))
        o.append('    {')
        o.append(fmt_u32(w, 8, '        '))
        o.append('    },')
    o.append('};')
    o.append('')


def build():
    out = {}
    out['obj16'] = [
        ('BOULDER', boulder()), ('PLATE', plate(False)), ('PLATE_DOWN', plate(True)),
        ('SWITCH', floor_switch(False)), ('SWITCH_ON', floor_switch(True)),
        ('PAD0', pad(0)), ('PAD1', pad(1)), ('PAD2', pad(2)), ('PAD3', pad(3)),
        ('CHEST', chest(False)), ('CHEST_OPEN', chest(True)), ('LADDER', ladder()),
        ('GATE_SLOT', gate_slot()),
    ]
    out['obj32'] = [
        ('GATE', gate(0)), ('GATE_1', gate(6)), ('GATE_2', gate(12)), ('GATE_3', gate(18)),
        ('BARRIER0', barrier(0)), ('BARRIER1', barrier(1)), ('BARRIER2', barrier(2)), ('BARRIER3', barrier(3)),
        ('BARRIER_OFF', barrier(4)), ('FERRY', ferry_post()),
    ]
    out['fx8'] = [(n, FX8[n]) for n in FX8_NAMES]
    out['fx16'] = FX16
    out['bike'] = bike_frames()
    out['boat'] = [boat(0), boat(1)]
    out['crests'] = [crest(k) for k in CRESTS]
    tm = paint_town_map()
    compass(tm)
    out['map_img'] = tm
    out['map_tiles'], out['map_screen'] = encode_bg(tm, 512, 'town map')
    sea = paint_sea()
    out['sea_img'] = sea
    out['sea_tiles'], out['sea_screen'] = encode_bg(sea, 512, 'voyage sea')
    return out


def write_header(out, path):
    o = []
    A = o.append
    A('/* gfx_travel.h -- GENERATED by tools/gen_travel_gfx.py. Do not edit.')
    A(' *')
    A(' * Traversal graphics (docs/EXPANSION.md 7.5): map objects, particles, the')
    A(' * bike, the boat, crests, the town map of the Vale and the voyage sea.')
    A(' * OBJ tiles are 1D-mapped, row-major. BG screens: tile (bits 0-9) | hflip')
    A(' * (10) | vflip (11), palette bank 0.')
    A(' */')
    A('#ifndef GFX_TRAVEL_H')
    A('#define GFX_TRAVEL_H')
    A('')
    A('/* OBJ bank 8 (satchel colours kept at 1-%d) and OBJ bank 15 (emote colours' % len(gf.ITEM_PAL))
    A(' * kept at 1-%d): load these instead of item_ball_palette / emote_palette. */' % len(gf.EMOTE_PAL))
    A('static const u16 travel_misc_palette[16] = {')
    A(fmt_u16(MISC.c15s()))
    A('};')
    A('static const u16 travel_fx_palette[16] = {')
    A(fmt_u16(FX.c15s()))
    A('};')
    A('/* misc-palette ink for the location banner */')
    A('#define TPAL_INK    %d' % MISC['o'])
    A('#define TPAL_EDGE   %d' % MISC['B'])
    A('#define TPAL_SHADE  %d' % MISC['y'])
    A('#define TPAL_PAPER  %d' % MISC['Y'])
    A('#define TPAL_GOLD   %d' % MISC['G'])
    A('')
    A('enum { ' + ', '.join('TO_%s' % n for n, _ in out['obj16']) + ', TO_COUNT };')
    emit_frames(o, 'u32', 'travel_obj16', [f for _, f in out['obj16']], 32, '16x16 map objects (OBJ bank 8)')
    A('enum { ' + ', '.join('TT_%s' % n for n, _ in out['obj32']) + ', TT_COUNT };')
    emit_frames(o, 'u32', 'travel_obj32', [f for _, f in out['obj32']], 64,
                '16x32 map objects (OBJ bank 8), feet at the bottom row')
    A('enum { ' + ', '.join('TF_%s' % n for n, _ in out['fx8']) + ', TF_COUNT };')
    emit_frames(o, 'u32', 'travel_fx8', [f for _, f in out['fx8']], 8, '8x8 particles (OBJ bank 15)')
    A('enum { ' + ', '.join('TX_%s' % n for n, _ in out['fx16']) + ', TX_COUNT };')
    emit_frames(o, 'u32', 'travel_fx16', [f for _, f in out['fx16']], 32, '16x16 effects (OBJ bank 15)')
    emit_frames(o, 'u32', 'travel_bike_gfx', out['bike'], 128,
                'the player on the BIKE, 32x32 in the player palette: down 0/1, up 2/3, left 4/5')
    emit_frames(o, 'u32', 'travel_boat_gfx', out['boat'], 128, 'the ferry boat, 32x32 facing right (OBJ bank 8)')
    A('/* the CREST CASE: VOLT, TIDE, ANVIL, RIME, LANTERN, DREAM, then an empty slot */')
    A('static const u16 travel_crest_palette[16] = {')
    A(fmt_u16(CREST.c15s()))
    A('};')
    emit_frames(o, 'u32', 'travel_crest_gfx', out['crests'], 128, '32x32 crests')
    A('/* The town map of the Vale: 30x20 tiles for BG (bank 0). */')
    A('#define TRAVEL_MAP_TILE_COUNT %d' % len(out['map_tiles']))
    A('static const u16 travel_map_palette[16] = {')
    A(fmt_u16(MAP_PAL.c15s()))
    A('};')
    A('static const u32 travel_map_tiles[%d][8] = {' % len(out['map_tiles']))
    for t in out['map_tiles']:
        A('    { ' + ', '.join('0x%08X' % w for w in t) + ' },')
    A('};')
    A('static const u16 travel_map_screen[20 * 30] = {')
    A(fmt_u16(out['map_screen'], 15))
    A('};')
    A('/* Places on the town map (pixel centre, kind 0 town, 1 route, 2 lair, 3 isle). */')
    A('enum { ' + ', '.join('WM_%s' % k for (k, _, _, _) in SPOTS) + ', WM_COUNT };')
    kinds = {'town': 0, 'route': 1, 'lair': 2, 'isle': 3}
    A('static const u8 WM_SPOTS[WM_COUNT][3] = {')
    for (k, x, y, kind) in SPOTS:
        A('    { %d, %d, %d },  /* %s */' % (x, y, kinds[kind], k))
    A('};')
    A('')
    A('/* The voyage sea: 32x20 tiles (256 px wide, wraps), BG bank 0. */')
    A('#define TRAVEL_SEA_TILE_COUNT %d' % len(out['sea_tiles']))
    A('#define TRAVEL_SEA_HORIZON 58')
    A('static const u16 travel_sea_palette[16] = {')
    A(fmt_u16(SEA_PAL.c15s()))
    A('};')
    A('static const u32 travel_sea_tiles[%d][8] = {' % len(out['sea_tiles']))
    for t in out['sea_tiles']:
        A('    { ' + ', '.join('0x%08X' % w for w in t) + ' },')
    A('};')
    A('static const u16 travel_sea_screen[20 * 32] = {')
    A(fmt_u16(out['sea_screen'], 16))
    A('};')
    A('')
    A('#endif')
    with open(path, 'w') as f:
        f.write('\n'.join(o) + '\n')


# =====================================================================
# Previews
# =====================================================================

def render(img, pal_rgb, scale=4, bg=(96, 120, 96)):
    rows = []
    for row in img:
        rows.append([bg if v == 0 else pal_rgb[v] for v in row])
    return scale_rows(rows, scale)


def sheet(imgs, pal_rgb, path, scale=4, cols=8, bg=(96, 120, 96)):
    cw = max(len(i[0]) for i in imgs) + 2
    ch = max(len(i) for i in imgs) + 2
    rows_n = (len(imgs) + cols - 1) // cols
    canvas = [[bg] * (cw * cols) for _ in range(ch * rows_n)]
    for k, im in enumerate(imgs):
        ox, oy = (k % cols) * cw + 1, (k // cols) * ch + 1
        for y, row in enumerate(im):
            for x, v in enumerate(row):
                if v:
                    canvas[oy + y][ox + x] = pal_rgb[v]
    write_png(path, cw * cols * scale, ch * rows_n * scale, scale_rows(canvas, scale))


def q(pal):
    return [c15_to_rgb(c15(c)) for c in pal.rgb]


def previews(out, d):
    os.makedirs(d, exist_ok=True)
    sheet([f for _, f in out['obj16']], q(MISC), os.path.join(d, 'travel_obj16.png'))
    sheet([f for _, f in out['obj32']], q(MISC), os.path.join(d, 'travel_obj32.png'))
    sheet([f for _, f in out['fx8']] + [f for _, f in out['fx16']], q(FX), os.path.join(d, 'travel_fx.png'))
    pp = [c15_to_rgb(c) for c in PLAYER_PAL15]
    sheet(out['bike'], pp, os.path.join(d, 'travel_bike.png'), cols=6)
    sheet(out['boat'], q(MISC), os.path.join(d, 'travel_boat.png'), cols=2, bg=(80, 140, 210))
    sheet(out['crests'], q(CREST), os.path.join(d, 'travel_crests.png'), cols=7, bg=(200, 200, 200))
    rows = render(out['map_img'], q(MAP_PAL), 3)
    write_png(os.path.join(d, 'travel_townmap.png'), 240 * 3, 160 * 3, rows)
    rows = render(out['sea_img'], q(SEA_PAL), 2)
    write_png(os.path.join(d, 'travel_sea.png'), 256 * 2, SEA_H * 2, rows)


def main(argv):
    out = build()
    write_header(out, OUT_H)
    print('wrote %s (town map %d tiles, sea %d tiles)' % (OUT_H, len(out['map_tiles']), len(out['sea_tiles'])))
    if '--preview' in argv:
        d = argv[argv.index('--preview') + 1]
        previews(out, d)
        print('previews in %s' % d)


if __name__ == '__main__':
    main(sys.argv[1:])
