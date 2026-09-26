#!/usr/bin/env python3
"""Elevation art for a tileset (docs/ELEVATION.md): cliff faces, plateau
rims, cast shadows, stairs, bridge decks and tunnel mouths.

The engine (src/game/elev.c) autotiles these per 8x8 quadrant from a map's
elevation layer, so maps only give heights and a few features. Everything
is drawn with the town colour names below; a tileset whose banks use other
colours passes a `roles` mapping (town name -> its own colour name).

    art = elevation_art(ts, roles)      # -> dict of map entries (u16)

Entry tables (the ElevArt struct in gfx_field.h, same order):
  face[4][4]    cliff face quadrant c, variant = (continues vertically) |
                (continues sideways) << 1; the top quads without a face
                above carry the grass lip, the bottom quads without a face
                below the dark base and a dithered contact shadow
  rim[4][5]     plateau top edges over the ground layer, variants as the
                path autotiles (0 interior, 1 inner corner, 2 side edge,
                3 top/bottom edge, 4 outer corner); 0 = nothing drawn
  shadow[4]     low ground just east of something higher (left quads only)
  stairs[4][4]  per climbing direction (up = N, S, W, E), 4 quadrants
  deck_h[4][4]  bridge walked east-west: variant = railing | end << 1
                (TL/TR: north railing, BL/BR: south railing + fascia;
                 TL/BL: west end, TR/BR: east end)
  deck_v[4][4]  bridge walked north-south: variant = railing | end << 1
                (TL/BL: west railing, TR/BR: east railing;
                 TL/TR: north end, BL/BR: south end + fascia)
  mouth[4]      tunnel mouth cut into a cliff face
"""

from pixelart import Img, hash2
from terrain_wild import rock_tex

QUADS = ((0, 0), (8, 0), (0, 8), (8, 8))

# Town colour names the art is drawn with (every one must be mapped by
# `roles` for a tileset that lacks it).
ROCK_COLORS = ('t_out', 'k_lt', 'k_base', 'k_dk', 'g_hi', 'g_lt', 'g_base', 'g_mid', 'g_dk',
               'g_dkr')
WOOD_COLORS = ('b_out', 'wd_lt', 'wd_base', 'wd_dk')

FACE_SEEDS = [(2, 3), (7, 1), (12, 4), (4, 10), (9, 8), (14, 12), (1, 15)]


def face_tex():
    """Seamless cliff rock: tall slabs (vertical strata), lit on the left."""
    return rock_tex(FACE_SEEDS, sy=0.55, seed=3)


LIP_ROWS = 4          # grass lip rows at the top of an uncovered face
TUFTS = (2, 6, 11, 14)
DARKER = {'k_lt': 'k_base', 'k_base': 'k_dk'}
LIGHTER = {'k_base': 'k_lt', 'k_dk': 'k_base'}


def face_img(lip, base, left_cap, right_cap):
    img = face_tex()
    # light from above: the top of the rock is lighter, the foot darker
    for x in range(16):
        for y in range(16):
            c = img.p[y][x]
            if y in (4, 5) and c in LIGHTER and hash2(x, y, 9) % 3:
                img.p[y][x] = LIGHTER[c]
            if y >= 11 and c in DARKER and (y >= 13 or hash2(x, y, 9) % 2):
                img.p[y][x] = DARKER[c]
    if lip:
        for x in range(16):
            img.p[0][x] = 'g_hi' if x % 5 == 1 else 'g_lt'
            img.p[1][x] = 'g_base' if hash2(x, 1, 7) % 3 else 'g_lt'
            img.p[2][x] = 'g_mid' if hash2(x, 2, 7) & 1 else 'g_base'
            img.p[3][x] = 't_out'
            if x in TUFTS:            # grass tufts hanging over the rim
                img.p[3][x] = 'g_mid'
                img.p[4][x] = 't_out'
            elif img.p[4][x] in ('k_base', 'k_dk', 't_out'):
                img.p[4][x] = 'k_lt'
    if base:
        for x in range(16):
            img.p[14][x] = 't_out'
            img.p[15][x] = 't_out' if x % 2 == 0 else None   # contact shadow
    for side, cap in ((0, left_cap), (1, right_cap)):
        if not cap:
            continue
        for y in range(16):
            inset = 0
            if lip and y == 0:
                inset = 2
            elif lip and y == 1:
                inset = 1
            if base and y == 14:
                inset = 1
            if base and y == 15:
                inset = 16  # the shadow row stops short of the rounded foot
            for u in range(min(inset, 16)):
                x = u if side == 0 else 15 - u
                img.p[y][x] = None
            if inset >= 16:
                continue
            # the rock band of the plateau's side continues down the face
            x = inset if side == 0 else 15 - inset
            img.p[y][x] = 't_out'
            if y < LIP_ROWS and lip:
                x2 = x + 1 if side == 0 else x - 1
                img.p[y][x2] = 'g_lt' if side == 0 else 'g_mid'
                continue
            band = SIDE_L if side == 0 else SIDE_R
            for i, c in enumerate(band[1:-1]):
                xx = x + 1 + i if side == 0 else x - 1 - i
                if base and y >= 14:
                    c = 't_out'
                img.p[y][xx] = _side_px(c, y, side, i + 1)
        if base:   # finish the rounded foot's shadow
            for u in range(1, 6):
                x = u if side == 0 else 15 - u
                img.p[15][x] = 't_out' if u % 2 == 0 else None
    return img


# the rock band down a plateau's west / east side (outside -> inside)
SIDE_L = ('t_out', 'k_lt', 'k_lt', 'k_base', 'k_dk', 't_out')
SIDE_R = ('t_out', 'k_dk', 'k_base', 'k_base', 'k_dk', 't_out')


def _side_px(c, y, side, i=0):
    """Rock band texture: rounded stones with dark joints every few rows."""
    joint = (y + (2 if side else 0) + (i // 3) * 3) % 6
    if c != 't_out' and joint == 5:
        return 't_out' if i in (2, 3) else 'k_dk'
    if c == 'k_lt' and joint == 0:
        return 'k_lt'
    if c == 'k_base' and joint == 4:
        return 'k_dk'
    if c == 'k_lt' and joint == 4:
        return 'k_base'
    return c


def rim_img(n, s, w, e, inner):
    """Top-cell overlay: edges toward lower neighbours. inner: set of
    'nw', 'ne', 'sw', 'se' diagonal-only drops (inner corners)."""
    img = Img(16, 16)
    if n:
        for x in range(16):
            img.p[0][x] = 't_out'
            img.p[1][x] = 'g_hi' if x % 3 else 'g_lt'
    for (flag, band, side) in ((w, SIDE_L, 0), (e, SIDE_R, 1)):
        if not flag:
            continue
        for y in range(16):
            for i, c in enumerate(band):
                x = i if side == 0 else 15 - i
                img.p[y][x] = _side_px(c, y, side, i)
            x = len(band) if side == 0 else 15 - len(band)
            img.p[y][x] = 'g_dkr' if side else 'g_hi'
    if n and w:     # rounded outer corner
        for (x, y) in ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (0, 2)):
            img.p[y][x] = None
        for (x, y) in ((3, 0), (2, 1), (1, 2), (0, 3)):
            img.p[y][x] = 't_out'
        img.p[2][2] = 'k_lt'
        img.p[1][3] = 'g_hi'
    if n and e:
        for (x, y) in ((15, 0), (14, 0), (13, 0), (15, 1), (14, 1), (15, 2)):
            img.p[y][x] = None
        for (x, y) in ((12, 0), (13, 1), (14, 2), (15, 3)):
            img.p[y][x] = 't_out'
        img.p[2][13] = 'k_dk'
        img.p[1][12] = 'g_hi'
    if 'nw' in inner:
        img.p[0][0] = img.p[1][0] = img.p[0][1] = 't_out'
        img.p[1][1] = 'k_lt'
    if 'ne' in inner:
        img.p[0][15] = img.p[1][15] = img.p[0][14] = 't_out'
        img.p[1][14] = 'k_dk'
    if 'sw' in inner:
        img.p[15][0] = img.p[14][0] = 't_out'
        img.p[15][1] = 'k_lt'
    if 'se' in inner:
        img.p[15][15] = img.p[14][15] = 't_out'
        img.p[15][14] = 'k_dk'
    return img


def shadow_img():
    img = Img(16, 16)
    for y in range(16):
        img.p[y][0] = 't_out' if y % 2 == 0 else None
        img.p[y][1] = 't_out' if y % 4 == 1 else None
    return img


def stairs_up():
    """Stairs climbing north (the high end at the top)."""
    img = Img(16, 16)
    pattern = ['k_lt', 'k_lt', 'k_base', 'k_dk']
    for y in range(16):
        for x in range(16):
            if x == 0 or x == 15:
                c = 't_out'
            elif x == 1:
                c = 'k_base'
            elif x == 14:
                c = 'k_dk'
            elif x == 2 or x == 13:
                c = 't_out' if y % 4 == 3 else 'k_dk'
            else:
                c = pattern[y % 4]
                if y % 4 == 0 and hash2(x, y, 11) % 5 == 0:
                    c = 'k_base'
            img.p[y][x] = c
    for x in range(1, 15):     # the grass edge of the plateau above
        img.p[0][x] = 'g_mid' if x in (1, 14) else img.p[0][x]
    return img


def stairs_side(up_west):
    """Side stairs along a cliff: seen from the south, the steps climb toward
    the high end (west for up_west) and their stepped front face shows."""
    img = Img(16, 16)
    for u in range(16):             # u: 0 at the high end
        x = u if up_west else 15 - u
        step = u // 4
        face_top = 7 + step         # higher steps show a taller front face
        for y in range(16):
            if y == 0:
                c = 't_out'
            elif y < face_top:
                c = 'k_lt' if (y + u) % 7 else 'k_base'
                if u % 4 == 0 and step:        # the riser of the step above
                    c = 'k_dk'
                elif u % 4 == 1 and step:
                    c = 'k_base'
            elif y == face_top:
                c = 't_out'
            elif y == 15:
                c = 't_out'
            else:
                c = 'k_base' if y < 13 else 'k_dk'
                if u % 4 == 0:
                    c = 'k_dk'
            img.p[y][x] = c
        if u == 0:
            for y in range(16):
                img.p[y][x] = 't_out'
    return img


def stairs_img(d):
    """d: 0 up = north, 1 up = south, 2 up = west, 3 up = east."""
    if d >= 2:
        return stairs_side(d == 2)
    up = stairs_up()
    img = Img(16, 16)
    for y in range(16):
        for x in range(16):
            img.p[y][x] = up.p[y][x] if d == 0 else up.p[15 - y][x]
    return img


def deck_img(vertical, rail_lo, rail_hi, end_lo, end_hi):
    """Bridge deck. Horizontal (walked E-W): rail_lo = north railing,
    rail_hi = south railing + fascia, end_lo = west end, end_hi = east end.
    Vertical (walked N-S): rail_lo = west, rail_hi = east, end_lo = north,
    end_hi = south end + fascia."""
    img = Img(16, 16)
    for y in range(16):
        for x in range(16):
            a = y if vertical else x          # position along the planks' run
            k = a % 4
            c = 'wd_dk' if k == 3 else ('wd_lt' if k == 0 else 'wd_base')
            b = x if vertical else y
            if k in (1, 2) and hash2(b, a // 4, 21) % 7 == 0:
                c = 'wd_lt'
            img.p[y][x] = c

    def put(u, v, c):       # u across the walk, v along it (0..15)
        if vertical:
            img.p[v][u] = c
        else:
            img.p[u][v] = c
    # railings along the walking direction
    if rail_lo:
        for v in range(16):
            put(0, v, 'b_out')
            put(1, v, 'wd_lt')
            put(2, v, 'wd_base')
            put(3, v, 'wd_dk')
        for v in (2, 3, 10, 11):
            for u in range(0, 5):
                put(u, v, 'wd_dk' if v in (3, 11) else 'wd_base')
            put(0, v, 'b_out')
            put(5, v, 'b_out' if v in (3, 11) else 'wd_dk')
    if rail_hi:
        for v in range(16):
            put(10, v, 'b_out')
            put(11, v, 'wd_lt')
            put(12, v, 'wd_base')
            put(13, v, 'wd_dk')
            put(14, v, 'wd_dk')
            put(15, v, 'b_out')
        for v in (2, 3, 10, 11):
            for u in range(8, 14):
                put(u, v, 'wd_dk' if v in (3, 11) else 'wd_base')
            put(8, v, 'b_out')
    # ends: a dark beam where the deck meets the ground
    for (flag, v0, dv) in ((end_lo, 0, 1), (end_hi, 15, -1)):
        if not flag:
            continue
        for u in range(16):
            put(u, v0, 'wd_dk')
            put(u, v0 + dv, 'wd_base' if u % 4 else 'wd_dk')
        if rail_lo:
            for v in range(3):
                vv = v0 + dv * v
                for u in range(0, 5):
                    put(u, vv, 'b_out' if u in (0, 4) or v == 0 else 'wd_lt' if u == 1 else 'wd_base')
        if rail_hi:
            for v in range(3):
                vv = v0 + dv * v
                for u in range(10, 16):
                    put(u, vv, 'b_out' if u in (10, 15) or v == 0 else 'wd_base' if u < 13 else 'wd_dk')
    if vertical and end_hi:        # the front beam of a bridge walked N-S
        for u in range(16):
            put(u, 13, 'wd_dk')
            put(u, 14, 'wd_dk' if u % 5 else 'b_out')
            put(u, 15, 'b_out')
    return img


def mouth_img():
    img = face_img(True, True, False, False)
    for x in range(2, 14):
        top = 6
        if x in (2, 13):
            top = 10
        elif x in (3, 12):
            top = 8
        elif x in (4, 11):
            top = 7
        img.p[top - 1][x] = 'k_dk' if 4 <= x <= 11 else 't_out'
        for y in range(top, 16):
            c = 't_out'
            if y >= 13 and (x + y) % 2 == 0:
                c = 'k_dk'
            img.p[y][x] = c
    for y in range(6, 16):         # the lit left jamb, the dark right one
        if img.p[y][1] not in (None, 't_out'):
            img.p[y][1] = 'k_lt'
        if img.p[y][14] not in (None, 't_out'):
            img.p[y][14] = 'k_dk'
    return img


# ---------------------------------------------------------------- encoding

def _quad(img, c):
    dx, dy = QUADS[c]
    return [img.get(dx + x, dy + y) for y in range(8) for x in range(8)]


def elevation_art(ts, roles=None, where='elev'):
    """Encode every elevation tile into `ts` (gen_field_gfx.TileSet)."""
    roles = roles or {}

    def enc(img, c, what):
        if roles:
            img = img.replace(roles)
        return ts.add(_quad(img, c), where='%s.%s[%d]' % (where, what, c), opaque=False)

    art = {}
    art['face'] = [[enc(face_img(lip=not (v & 1) and c < 2, base=not (v & 1) and c >= 2,
                                 left_cap=not (v & 2) and c % 2 == 0,
                                 right_cap=not (v & 2) and c % 2 == 1), c, 'face%d' % v)
                    for v in range(4)] for c in range(4)]
    rim = []
    for c in range(4):
        row = [0]
        vert = 'n' if c < 2 else 's'
        horz = 'w' if c % 2 == 0 else 'e'
        for v in range(1, 5):
            f = {'n': False, 's': False, 'w': False, 'e': False}
            inner = set()
            if v == 1:
                inner.add(vert + horz)
            if v in (2, 4):
                f[horz] = True
            if v in (3, 4):
                f[vert] = True
            row.append(enc(rim_img(f['n'], f['s'], f['w'], f['e'], inner), c, 'rim%d' % v))
        rim.append(row)
    art['rim'] = rim
    sh = shadow_img()
    art['shadow'] = [enc(sh, 0, 'shadow'), 0, enc(sh, 2, 'shadow'), 0]
    art['stairs'] = [[enc(stairs_img(d), c, 'stairs%d' % d) for c in range(4)] for d in range(4)]
    for (key, vert) in (('deck_h', False), ('deck_v', True)):
        tab = []
        for c in range(4):
            row = []
            for v in range(4):
                rail, end = bool(v & 1), bool(v & 2)
                if vert:
                    rl, rh = rail and c % 2 == 0, rail and c % 2 == 1
                    el, eh = end and c < 2, end and c >= 2
                else:
                    rl, rh = rail and c < 2, rail and c >= 2
                    el, eh = end and c % 2 == 0, end and c % 2 == 1
                row.append(enc(deck_img(vert, rl, rh, el, eh), c, '%s%d' % (key, v)))
            tab.append(row)
        art[key] = tab
    mo = mouth_img()
    art['mouth'] = [enc(mo, c, 'mouth') for c in range(4)]
    return art


def preview(art_imgs_path=None):
    """Debug sheet of every elevation cell image (town colours)."""
    import gen_field_gfx as gf
    from pixelart import write_png
    cells = []
    for v in range(4):
        cells.append(face_img(not (v & 1), not (v & 1), not (v & 2), not (v & 2)))
    cells.append(rim_img(True, True, True, True, set()))
    cells.append(shadow_img())
    cells += [stairs_img(d) for d in range(4)]
    cells += [deck_img(False, True, True, True, True), deck_img(True, True, True, True, True)]
    cells.append(mouth_img())
    W = len(cells) * 18
    rows = [[(40, 40, 60)] * W for _ in range(18)]
    for i, im in enumerate(cells):
        for y in range(16):
            for x in range(16):
                c = im.p[y][x]
                if c:
                    rows[1 + y][i * 18 + 1 + x] = gf.C[c]
    write_png(art_imgs_path or 'elev_preview.png', W, 18, rows)
