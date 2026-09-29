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
  ledge[4][2]   a ledge (a low face you hop down): variant = continues
                sideways; only the top of the cell is drawn
"""

from pixelart import Img, hash2
from terrain_wild import rock_tex

QUADS = ((0, 0), (8, 0), (0, 8), (8, 8))

# Colour roles per tileset (town name -> the tileset's own colour); used by
# gen_field_gfx.finish_tileset for every tileset listed here (a module can
# also pass elev={...} itself). Each piece of art must fit one bank: the
# rock + lip colours together, and the four wood colours together.
ROLES = {
    'town': {}, 'wild': {}, 'coast': {}, 'farm': {},
    # pale sandstone bridges (the street bank, 1)
    'city': {'deck': 'stone',
             'deck_roles': {'d_out': 'cb_out', 'd_hi': 'pv_hi', 'd_lt': 'pv_lt', 'd_base': 'pv_base',
                            'd_dk': 'pv_dk', 'd_dkr': 'cb_dk'}},
    # light frost-capped granite under a snow lip (bank 6); frosted stone
    # bridges in the same bank
    'snow': {'t_out': 'rk_dk', 'k_lt': 'rk_hi', 'k_base': 'sn_dk', 'k_dk': 'rk_lt',
             'g_hi': 'sn_hi', 'g_lt': 'sn_lt', 'g_base': 'sn_base', 'g_mid': 'sn_mid',
             'g_dk': 'sn_dk', 'g_dkr': 'rk_base', 'frost': True,
             'deck': 'stone',
             'deck_roles': {'d_out': 'rk_out', 'd_hi': 'sn_hi', 'd_lt': 'rk_hi', 'd_base': 'rk_lt',
                            'd_dk': 'rk_base', 'd_dkr': 'rk_dk'}},
    # cave walls over the cave floor (bank 2)
    'cave': {'t_out': 'cw_out', 'k_lt': 'cw_lt', 'k_base': 'cw_base', 'k_dk': 'cw_dk',
             'g_hi': 'cv_lt', 'g_lt': 'cv_lt', 'g_base': 'cv_base', 'g_mid': 'cv_mid',
             'g_dk': 'cv_dk', 'g_dkr': 'cv_dkr'},
    # basalt under an ash lip (bank 2); riveted iron bridges (the iron bank, 5)
    'volcanic': {'t_out': 'b_out', 'k_lt': 'vb_lt', 'k_base': 'vb_base', 'k_dk': 'vb_dk',
                 'g_hi': 'va_lt', 'g_lt': 'va_lt', 'g_base': 'va_base', 'g_mid': 'va_mid',
                 'g_dk': 'va_dk', 'g_dkr': 'vb_dk',
                 'deck': 'iron',
                 'deck_roles': {'d_out': 'b_out', 'd_hi': 'ir_hi', 'd_lt': 'ir_lt', 'd_base': 'ir_base',
                                'd_dk': 'ir_dk', 'd_dkr': 'ir_dkr'}},
    # dream stone under a dream-grass lip (bank 0); moonstone bridges
    'dream': {'t_out': 'b_out', 'k_lt': 'ds_lt', 'k_base': 'ds_base', 'k_dk': 'ds_dk',
              'g_hi': 'dg_hi', 'g_lt': 'dg_lt', 'g_base': 'dg_base', 'g_mid': 'dg_mid',
              'g_dk': 'dg_dk', 'g_dkr': 'ds_mid',
              'deck': 'stone',
              'deck_roles': {'d_out': 'b_out', 'd_hi': 'ds_hi', 'd_lt': 'ds_lt', 'd_base': 'ds_base',
                             'd_dk': 'ds_mid', 'd_dkr': 'ds_dk'}},
    # grave stone under a mud-and-moss lip (bank 6), grim planks (bank 4)
    'grim': {'t_out': 'grm_out', 'k_lt': 'grm_st_lt', 'k_base': 'grm_st', 'k_dk': 'grm_st_dk',
             'g_hi': 'grm_moss', 'g_lt': 'grm_moss', 'g_base': 'grm_mud', 'g_mid': 'grm_mud_dk',
             'g_dk': 'grm_peat', 'g_dkr': 'grm_peat',
             'b_out': 'grm_out', 'wd_lt': 'grm_wd_hi', 'wd_base': 'grm_wd', 'wd_dk': 'grm_wd_dk'},
}
# Options inside a ROLES entry (not colours):
#   'deck'        bridge deck style: 'wood' (default, the WOOD_COLORS),
#                 'iron' (riveted plates between lattice girders) or
#                 'stone' (flagstones between parapets)
#   'deck_roles'  DECK_COLORS -> the tileset's colours (one bank) for iron/stone
#   'frost'       snow settled on the lit edges of the cliff faces

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


def face_img(lip, base, left_cap, right_cap, frost=False):
    img = face_tex()
    # light from above: the top of the rock is lighter, the foot darker
    for x in range(16):
        for y in range(16):
            c = img.p[y][x]
            if y in (4, 5) and c in LIGHTER and hash2(x, y, 9) % 3:
                img.p[y][x] = LIGHTER[c]
            if y >= 11 and c in DARKER and (y >= 13 or hash2(x, y, 9) % 2):
                img.p[y][x] = DARKER[c]
    if frost:
        _frost(img, 12)
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


def _frost(img, rows):
    """Snow settled on the rock: the lit top edge of every slab down to
    `rows` gets a cap of the lip colours (the frost look of the snow cliffs)."""
    src = img.copy()
    for y in range(1, rows):
        for x in range(16):
            c, up = src.p[y][x], src.p[y - 1][x]
            if c == 'k_lt' and up in ('t_out', 'k_dk'):
                img.p[y][x] = 'g_hi' if hash2(x, y, 31) % 3 == 0 else 'g_lt'
            elif c == 'k_lt' and up == 'k_lt' and src.p[y - 2][x] in ('t_out', 'k_dk') \
                    and y < rows - 4 and hash2(x, y, 37) % 2:
                img.p[y][x] = 'g_base'


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


# Deck styles besides wood. Drawn with the deck colour names below, which a
# ROLES entry maps with 'deck_roles' (all six into one palette bank).
DECK_COLORS = ('d_out', 'd_hi', 'd_lt', 'd_base', 'd_dk', 'd_dkr')


def deck_styled(style, vertical, rail_lo, rail_hi, end_lo, end_hi):
    """A bridge deck in 'iron' (riveted plates between lattice girders) or
    'stone' (flagstones between parapets with a coping). Same layout and
    arguments as deck_img: u runs across the walk (0 = rail_lo side),
    v along it (0 = end_lo side)."""
    img = Img(16, 16)

    def put(u, v, c):
        if vertical:
            img.p[v][u] = c
        else:
            img.p[u][v] = c

    iron = style == 'iron'
    # the walking surface
    for u in range(16):
        for v in range(16):
            if iron:
                # plates 8 long with a dark seam, a lit edge after it, rivets
                # at the corners and a raised diamond tread
                k = v % 8
                c = 'd_base'
                if k == 7:
                    c = 'd_dkr'
                elif k == 0:
                    c = 'd_lt'
                elif k in (1, 6) and u % 8 == 2:
                    c = 'd_hi'
                elif k in (1, 6) and u % 8 == 3:
                    c = 'd_dk'
                elif k == 6:
                    c = 'd_dk'
                elif (u + k) % 4 == 0 and u % 2 == 0 and 2 <= k <= 5:
                    c = 'd_lt'          # a sparse raised tread
            else:
                # flagstones: rows 4 wide across the walk, 8 long, in a
                # running bond, lit on their top-left edges
                row = u // 4
                k = (v + (4 if row % 2 else 0)) % 8
                c = 'd_base'
                if u % 4 == 3 or k == 7:
                    c = 'd_dk'
                elif u % 4 == 0 or k == 0:
                    c = 'd_lt'
                elif hash2(row, (v + (4 if row % 2 else 0)) // 8, 23) % 3 == 0:
                    c = 'd_lt' if (u + v) % 3 else 'd_base'
                if c == 'd_lt' and u % 4 == 0 and k == 0:
                    c = 'd_hi'
            put(u, v, c)
    # railings / parapets along the walk
    def lo_rail(v):
        """The rail_lo side's pixels at v, from u = 0 inward."""
        if iron:
            return ['d_out', 'd_hi', 'd_hi' if v % 4 == 1 else 'd_lt', 'd_out',
                    'd_dkr' if v % 2 else 'd_dk']
        return ['d_out', 'd_hi', 'd_lt', 'd_base' if v % 8 != 5 else 'd_dk', 'd_out',
                'd_dkr' if v % 2 else 'd_dk']
    for (on, mirror) in ((rail_lo, False), (rail_hi and vertical, True)):
        if not on:
            continue
        for v in range(16):
            for u, c in enumerate(lo_rail(v)):
                put(15 - u if mirror else u, v, c)
    front = rail_hi and not vertical       # the front railing of a bridge walked E-W
    if front:
        for v in range(16):
            if iron:
                # the girder's side: a lit top flange over a riveted web
                put(9, v, 'd_out')
                put(10, v, 'd_hi')
                put(11, v, 'd_lt')
                put(12, v, 'd_out')
                put(13, v, 'd_hi' if v % 4 == 1 else 'd_base')
                put(14, v, 'd_dk' if v % 4 != 1 else 'd_base')
                if v % 8 in (3, 4):
                    put(13, v, 'd_dk')  # diagonal web brace below the lit flange
                put(15, v, 'd_out')
            else:
                put(9, v, 'd_out')
                put(10, v, 'd_hi')
                put(11, v, 'd_lt')
                # the parapet's outer face: blocks with staggered joints
                for u in (12, 13, 14):
                    j = (v + (4 if u == 13 else 0)) % 8 == 0
                    put(u, v, 'd_dk' if j or u == 14 else 'd_base')
                put(15, v, 'd_out')
    # ends: where the deck meets the ground
    for (flag, v0, dv) in ((end_lo, 0, 1), (end_hi, 15, -1)):
        if not flag:
            continue
        for u in range(16):
            put(u, v0, 'd_out' if iron else 'd_dk')
            put(u, v0 + dv, 'd_dk' if iron else 'd_base')
            if iron and u % 4 == 2:
                put(u, v0 + dv, 'd_hi')             # rivets along the end beam
        for (on, u0, u1) in ((rail_lo, 0, 5), (rail_hi, 11 if vertical else 9, 16)):
            if not on:
                continue
            for w in range(3):                       # a squat end post / pier
                vv = v0 + dv * w
                for u in range(u0, u1):
                    edge = u in (u0, u1 - 1) or w == 0
                    put(u, vv, 'd_out' if edge else ('d_hi' if w == 1 and u == u0 + 1 else 'd_lt'))
    if vertical and end_hi:        # the front beam of a bridge walked N-S
        for u in range(16):
            if iron:
                put(u, 12, 'd_out')
                put(u, 13, 'd_lt' if u % 4 else 'd_hi')
                put(u, 14, 'd_dk')
                put(u, 15, 'd_out')
            else:
                put(u, 12, 'd_dk')
                put(u, 13, 'd_base' if u % 8 else 'd_dk')
                put(u, 14, 'd_dk' if (u + 4) % 8 else 'd_dkr')
                put(u, 15, 'd_out')
    return img


def ledge_img(left_cap, right_cap):
    """A low step: a bulging grass lip over a short earth face; the ground
    below shows under it."""
    img = Img(16, 16)
    tex = face_tex()
    for x in range(16):
        img.p[0][x] = 'g_hi' if x % 5 == 2 else 'g_lt'
        img.p[1][x] = 'g_base' if hash2(x, 1, 13) % 3 else 'g_lt'
        img.p[2][x] = 'g_base'
        img.p[3][x] = 'g_mid' if hash2(x, 3, 13) & 1 else 'g_base'
        img.p[4][x] = 'g_dkr' if x % 4 == 1 else 't_out'
        for y in range(5, 9):
            c = tex.p[y][x]
            img.p[y][x] = LIGHTER.get(c, c) if y == 5 else c
        img.p[9][x] = 't_out'
        img.p[10][x] = 't_out' if x % 2 == 0 else None
    for side, cap in ((0, left_cap), (1, right_cap)):
        if not cap:
            continue
        prof = {0: 2, 1: 1, 8: 1, 9: 2, 10: 16}
        for y in range(11):
            inset = prof.get(y, 0)
            for u in range(min(inset, 16)):
                x = u if side == 0 else 15 - u
                img.p[y][x] = None
            if inset >= 16:
                continue
            x = inset if side == 0 else 15 - inset
            img.p[y][x] = 't_out'
        for u in range(1, 5):
            x = u if side == 0 else 15 - u
            img.p[10][x] = 't_out' if u % 2 == 0 else None
    return img


def mouth_img(frost=False):
    img = face_img(True, True, False, False, frost)
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
    roles = dict(roles or {})
    deck = roles.pop('deck', 'wood')          # 'wood', 'iron' or 'stone'
    deck_roles = roles.pop('deck_roles', {})  # DECK_COLORS -> the tileset's colours
    frost = roles.pop('frost', False)         # snow settled on the cliff faces

    def enc(img, c, what):
        if roles:
            img = img.replace(roles)
        if deck_roles:
            img = img.replace(deck_roles)
        return ts.add(_quad(img, c), where='%s.%s[%d]' % (where, what, c), opaque=False)

    def deck_art(vert, rl, rh, el, eh):
        if deck == 'wood':
            return deck_img(vert, rl, rh, el, eh)
        return deck_styled(deck, vert, rl, rh, el, eh)

    art = {}
    art['face'] = [[enc(face_img(lip=not (v & 1) and c < 2, base=not (v & 1) and c >= 2,
                                 left_cap=not (v & 2) and c % 2 == 0,
                                 right_cap=not (v & 2) and c % 2 == 1, frost=frost), c, 'face%d' % v)
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
                row.append(enc(deck_art(vert, rl, rh, el, eh), c, '%s%d' % (key, v)))
            tab.append(row)
        art[key] = tab
    mo = mouth_img(frost)
    art['mouth'] = [enc(mo, c, 'mouth') for c in range(4)]
    art['ledge'] = [[enc(ledge_img(not v and c % 2 == 0, not v and c % 2 == 1), c, 'ledge%d' % v)
                     for v in range(2)] for c in range(4)]
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
    cells.append(ledge_img(True, True))
    W = len(cells) * 18
    rows = [[(40, 40, 60)] * W for _ in range(18)]
    for i, im in enumerate(cells):
        for y in range(16):
            for x in range(16):
                c = im.p[y][x]
                if c:
                    rows[1 + y][i * 18 + 1 + x] = gf.C[c]
    write_png(art_imgs_path or 'elev_preview.png', W, 18, rows)
