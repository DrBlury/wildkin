#!/usr/bin/env python3
"""Terrain art of the FAR region (W-FAR): the 'volcanic' tileset (Cinder
Road, Cindermoor, Ember Tunnel, Caldera Heart, Anvil Hall) and the 'dream'
tileset (Moonveil Path, Dreamspire, Mirror Hall, Dust Library).

Everything here is authored in colour names (FAR_COLORS) like the rest of
the field art; tools/tilesets/ts_volcanic.py and ts_dream.py cut it into
banks and metatiles. Light comes from the top-left, objects carry a 1px
dark outline, overlay terrain (crags, charred trees, blossom trees) is
drawn on transparency so the engine can put any ground underneath.
"""

import math
from pixelart import Img, G, tex_fill, hash2, shade_clumps

FAR_COLORS = {
    # --- volcanic: ash (warm grey ground) -------------------------------
    'va_hi': (204, 192, 180), 'va_lt': (176, 164, 154), 'va_base': (150, 138, 130),
    'va_mid': (124, 114, 108), 'va_dk': (96, 88, 86),
    # --- basalt (cool dark stone) ----------------------------------------
    'vb_hi': (136, 136, 154), 'vb_lt': (104, 104, 122), 'vb_base': (80, 80, 98),
    'vb_dk': (58, 56, 74), 'vb_out': (36, 32, 46),
    # --- ember brush (scorched grass where wild kin roam) --------------
    'eb_hi': (252, 216, 112), 'eb_lt': (236, 164, 76), 'eb_base': (196, 110, 58),
    'eb_dk': (136, 66, 50),
    # --- lava -------------------------------------------------------------
    'lv_w': (255, 250, 214), 'lv_y': (255, 216, 84), 'lv_o': (250, 144, 42),
    'lv_r': (216, 64, 36), 'lv_dr': (144, 36, 38),
    # --- hot spring (mineral water) --------------------------------------
    'hs_hi': (214, 250, 242), 'hs_lt': (140, 226, 216), 'hs_base': (82, 186, 194),
    'hs_dk': (46, 132, 158),   # shared with north_palette.py
    # --- sulfur, obsidian -------------------------------------------------
    'su_y': (236, 226, 110),
    'ob_hi': (180, 168, 228), 'ob_base': (68, 58, 98), 'ob_dk': (38, 32, 60),
    # --- iron, rust, brick, charred wood ------------------------------
    'ir_hi': (192, 196, 208), 'ir_lt': (152, 156, 172), 'ir_base': (116, 118, 136),
    'ir_dk': (84, 84, 102), 'ir_dkr': (58, 56, 74),
    'ru_hi': (228, 146, 92), 'ru_base': (180, 96, 60), 'ru_dk': (124, 62, 46),
    'rr_hi': (236, 156, 108), 'rr_lt': (212, 116, 80), 'rr_base': (178, 82, 62),
    'rr_dk': (138, 58, 50), 'rr_dkr': (98, 42, 42),
    'bk_hi': (204, 124, 98), 'bk_base': (164, 88, 70), 'bk_dk': (114, 58, 54),
    'vcw_lt': (124, 100, 92), 'vcw_base': (88, 68, 64), 'vcw_dk': (60, 46, 48),
    # --- dream: pastel stone ground --------------------------------------
    'ds_hi': (250, 244, 250), 'ds_lt': (232, 222, 240), 'ds_base': (210, 198, 226),
    'ds_mid': (184, 170, 208), 'ds_dk': (148, 134, 180),
    # --- moon grass (mint) --------------------------------------------
    'dg_hi': (206, 238, 220), 'dg_lt': (170, 218, 200), 'dg_base': (138, 194, 184),
    'dg_mid': (108, 162, 166), 'dg_dk': (80, 126, 146),
    # --- moonpetals (pink / lilac flowers) --------------------------------
    'dp_hi': (255, 226, 244), 'dp_base': (242, 172, 212), 'dp_dk': (196, 122, 180),
    # --- blossom trees ---------------------------------------------------
    'bt_hi': (255, 232, 244), 'bt_lt': (250, 202, 228), 'bt_base': (236, 166, 208),
    'bt_mid': (206, 128, 184), 'bt_dk': (162, 94, 158), 'bt_out': (98, 58, 110),
    'tk_lt': (184, 160, 188), 'tk_base': (138, 112, 150), 'tk_dk': (96, 76, 116),
    # --- moon pond -------------------------------------------------------
    'dw_hi': (242, 248, 255), 'dw_lt': (180, 212, 250), 'dw_base': (140, 170, 234),
    'dw_mid': (116, 142, 218), 'dw_dk': (92, 110, 186),
    # --- lantern light, paper, moonstone ----------------------------------
    'lg_y': (255, 238, 164), 'lg_o': (250, 186, 100), 'lp_r': (232, 104, 120),
    'vcr_hi': (226, 236, 255), 'vcr_base': (160, 176, 240), 'vcr_dk': (108, 112, 196),
    # --- dream buildings: cream walls, indigo and rose roofs -------------
    'tw_hi': (252, 246, 232), 'tw_base': (238, 226, 204), 'tw_dk': (204, 184, 168),
    'ri_hi': (168, 170, 240), 'ri_lt': (128, 128, 220), 'ri_base': (100, 96, 196),
    'ri_dk': (74, 68, 156), 'ri_dkr': (52, 46, 112),
    'ro_hi': (252, 196, 212), 'ro_lt': (236, 150, 180), 'ro_base': (212, 112, 152),
    'ro_dk': (170, 80, 126), 'ro_dkr': (122, 56, 98),
    # --- dream interiors: mirror floor, plum wood, book spines -----------
    'mf_hi': (244, 244, 252), 'mf_lt': (214, 214, 236), 'mf_base': (184, 184, 216),
    'mf_dk': (140, 136, 184),
    'vlw_hi': (176, 120, 136), 'vlw_lt': (140, 90, 112), 'vlw_base': (108, 66, 92),
    'vlw_dk': (76, 46, 70), 'lw_out': (46, 28, 46),
    'bo_r': (200, 76, 84), 'bo_g': (88, 150, 110), 'bo_b': (84, 110, 186),
    'bo_y': (222, 184, 92), 'pg_hi': (252, 246, 226), 'pg_base': (230, 218, 188),
    'pg_dk': (184, 166, 136),
}


def rgb(name):
    return FAR_COLORS[name]


# =====================================================================
# small helpers
# =====================================================================

def speckle(img, seed, table):
    """Scatter colours over an image: table = [(threshold/256, colour), ...]
    applied to pixels hash-ordered; earlier entries win."""
    for y in range(img.h):
        for x in range(img.w):
            h = hash2(x, y, seed) & 255
            acc = 0
            for (n, c) in table:
                acc += n
                if h < acc:
                    img.p[y][x] = c
                    break
    return img


def put(img, pts, c):
    for (x, y) in pts:
        img.set(x % img.w, y % img.h, c)


def pebble(img, x, y, hi, base, dk, big=False):
    """A small lit pebble (2x2 or 3x2) with a shadow pixel."""
    if big:
        put(img, [(x, y), (x + 1, y)], hi)
        put(img, [(x, y + 1), (x + 1, y + 1), (x + 2, y)], base)
        put(img, [(x + 2, y + 1), (x + 1, y + 2), (x, y + 2)], dk)
    else:
        put(img, [(x, y)], hi)
        put(img, [(x + 1, y), (x, y + 1)], base)
        put(img, [(x + 1, y + 1)], dk)


# =====================================================================
# VOLCANIC: ground
# =====================================================================

def ash_img(seed=0):
    """Soft volcanic ash: warm grey with wind-combed streaks, grit and a few
    cinders. Tiles seamlessly (all features wrap)."""
    img = Img(16, 16, 'va_base')
    speckle(img, 11 + seed, [(18, 'va_mid'), (14, 'va_lt'), (3, 'va_dk'), (2, 'va_hi')])
    # wind-combed streaks: short light/dark pairs
    streaks = [(2, 3, 4), (10, 1, 3), (6, 8, 5), (13, 11, 3), (1, 13, 3)] if seed == 0 else \
              [(4, 2, 3), (11, 6, 4), (1, 9, 4), (8, 13, 5)]
    for (x0, y0, n) in streaks:
        for i in range(n):
            img.set((x0 + i) % 16, y0, 'va_lt')
            img.set((x0 + i + 1) % 16, (y0 + 1) % 16, 'va_mid')
    if seed == 0:
        pebble(img, 12, 5, 'va_hi', 'va_mid', 'va_dk')
        pebble(img, 4, 11, 'vb_lt', 'vb_base', 'vb_dk')
    elif seed == 1:
        pebble(img, 6, 4, 'vb_lt', 'vb_base', 'vb_dk', big=True)
        pebble(img, 13, 14, 'va_hi', 'va_mid', 'va_dk')
        img.set(2, 6, 'eb_base')   # a dying cinder
        img.set(3, 6, 'eb_dk')
    else:
        pebble(img, 9, 9, 'va_hi', 'va_mid', 'va_dk', big=True)
        pebble(img, 2, 2, 'vb_lt', 'vb_base', 'vb_dk')
        pebble(img, 13, 3, 'va_hi', 'va_mid', 'va_dk')
    return img


def hex_centres(w=16, h=16):
    """Centres of a wrapped hexagonal lattice that tiles a 16x16 cell."""
    return [(4, 2.7), (12, 2.7), (0, 8.0), (8, 8.0), (4, 13.3), (12, 13.3), (16, 8.0)]


def basalt_img(seed=0):
    """Columnar basalt seen from above: hexagonal column tops, each lit on
    its top-left rim and shaded on the bottom-right, dark joints between."""
    cs = hex_centres()
    img = Img(16, 16)

    def owner(x, y):
        best, bi, second = 1e9, -1, 1e9
        for i, (cx, cy) in enumerate(cs):
            for ox in (-16, 0, 16):
                for oy in (-16, 0, 16):
                    dx = x + 0.5 - (cx + ox)
                    dy = (y + 0.5 - (cy + oy)) * 1.15
                    d = dx * dx + dy * dy
                    if d < best:
                        second, best, bi = best, d, (i, ox, oy)
                    elif d < second:
                        second = d
        return bi, math.sqrt(second) - math.sqrt(best)
    grid = [[owner(x, y) for x in range(16)] for y in range(16)]
    for y in range(16):
        for x in range(16):
            (i, ox, oy), edge = grid[y][x]
            cx, cy = cs[i][0] + ox, cs[i][1] + oy
            if edge < 0.9:
                c = 'vb_out'
            else:
                nx, ny = x + 0.5 - cx, y + 0.5 - cy
                t = nx * 0.6 + ny * 0.8          # >0: away from the light
                if edge < 1.9 and t < -0.4:
                    c = 'vb_hi'
                elif edge < 1.9 and t > 0.8:
                    c = 'vb_dk'
                else:
                    c = 'vb_base' if (hash2(x, y, 41 + seed) & 7) else 'vb_lt'
                    if (i + seed) % 3 == 0 and c == 'vb_base':
                        c = 'vb_lt' if (x + y) % 5 == 0 else 'vb_base'
            img.p[y][x] = c
    if seed == 1:
        # a crack across one column and a little ash in a joint
        put(img, [(9, 7), (10, 8), (10, 9)], 'vb_out')
        put(img, [(3, 11), (4, 11)], 'va_mid')
    return img


def setts_img():
    """Cindermoor street paving: dressed hexagonal basalt setts, lighter and
    more regular than the wild columns, with ash in the joints."""
    img = basalt_img(0)
    for y in range(16):
        for x in range(16):
            c = img.p[y][x]
            img.p[y][x] = {'vb_out': 'va_dk', 'vb_dk': 'vb_base', 'vb_base': 'vb_lt',
                           'vb_lt': 'vb_lt', 'vb_hi': 'vb_hi'}[c]
    return img


def sulfur_img():
    """Ash crusted with yellow sulfur around a hairline fumarole crack."""
    img = ash_img(2)
    blobs = [(4, 5, 3.2, 2.2), (11, 10, 3.0, 2.4), (13, 3, 1.8, 1.4), (3, 13, 2.0, 1.5)]
    for y in range(16):
        for x in range(16):
            for (cx, cy, rx, ry) in blobs:
                for ox in (-16, 0, 16):
                    for oy in (-16, 0, 16):
                        d = ((x + 0.5 - cx - ox) / rx) ** 2 + ((y + 0.5 - cy - oy) / ry) ** 2
                        if d <= 1.0:
                            img.p[y][x] = 'su_y' if d < 0.55 or (hash2(x, y, 3) & 3) else 'eb_hi'
    put(img, [(6, 6), (7, 7), (8, 7), (9, 8), (10, 9)], 'va_dk')
    return img


# ---------------------------------------------------------------- ember brush

EB_L = {'.': None, 'O': 'eb_dk', 'd': 'eb_dk', 'm': 'eb_base', 'b': 'eb_base',
        'l': 'eb_lt', 'h': 'eb_hi', 'y': 'su_y'}
EB_TUFT = G('''
..h....h
.hlO..hl
.hlmO.lm
hllmdhlm
hlmmdlmd
lmmddmmd
mmdddmdd
ddddOddd
dOddddOd
''', EB_L)


def emberbrush_layers():
    """Scorched, fire-hardy brush with glowing seed tips (wild kin roam in
    it). Returns (bottom opaque, top with the front blades)."""
    back = ash_img(0).copy()
    for y in range(9, 16):
        for x in range(16):
            back.p[y][x] = 'va_mid' if (x + y) % 3 else 'va_dk'
    for ox in (-4, 4, 12):
        back.paste(EB_TUFT, ox, 0)
    front = Img(16, 16)
    for ox in (0, 8):
        front.paste(EB_TUFT, ox, 8)
    bottom = back.copy()
    bottom.paste(front, 0, 0)
    for (x, y) in ((2, 0), (10, 1), (6, 8), (14, 9)):
        bottom.set(x, y, 'su_y')      # glowing seed heads
    top = Img(16, 16)
    for y in range(9, 16):
        for x in range(16):
            ty, tx = y - 8, x % 8
            c = EB_TUFT.p[ty][tx]
            if c is None or (ty <= 3 and c == 'eb_dk'):
                continue
            top.p[y][x] = c
    top.set(6, 8, 'su_y')
    top.set(14, 9, 'su_y')
    return bottom, top


# ---------------------------------------------------------------- lava

def lava_surface(f, nframes=4):
    """Molten rock: bright channels between dark cooling rafts. The rafts
    drift one pixel right-and-down per frame (wrapping), the glow pulses."""
    img = Img(16, 16)
    rafts = [(3.0, 4.0, 3.4, 2.0), (11.5, 2.5, 2.6, 1.6), (9.0, 10.0, 3.8, 2.3),
             (1.5, 12.5, 2.3, 1.7), (14.0, 13.5, 1.9, 1.3)]
    sx = f * 16.0 / nframes
    sy = f * 4.0 / nframes
    for y in range(16):
        for x in range(16):
            best = 9.0
            for (cx, cy, rx, ry) in rafts:
                for ox in (-16, 0, 16):
                    for oy in (-16, 0, 16):
                        dx = (x + 0.5 - (cx + sx) % 16 - ox) / rx
                        dy = (y + 0.5 - (cy + sy) % 16 - oy) / ry
                        best = min(best, dx * dx + dy * dy)
            wob = 0.18 * math.sin((x * 0.9 + y * 0.6) + f * math.pi / 2)
            v = best + wob
            if v < 0.45:
                c = 'lv_dr'
            elif v < 0.85:
                c = 'lv_r'
            elif v < 1.6:
                c = 'lv_o'
            elif v < 3.2:
                c = 'lv_y'
            else:
                c = 'lv_w' if (hash2(x, y, 5 + f) & 3) == 0 else 'lv_y'
            img.p[y][x] = c
    return img


def lava_quads(f, nframes=4):
    """Autotile quadrants (4 corners x 5 variants, like water) for lava:
    a crust of basalt around the edge, glowing where it meets the melt. The
    outside is crust too (no ground), so lava sits on any ground."""
    from terrain_common import autotile
    surf = lava_surface(f, nframes)

    def wob(t):
        return 0.7 * math.sin(t * 1.3 + 0.8) + 0.4 * math.sin(t * 2.9)

    def color_at(d, X, Y, c, v, lx, ly):
        h = hash2(X, Y, 77) & 7
        if d < -0.6:
            return 'vb_out' if h == 0 else 'vb_dk'
        if d < 0.6:
            return 'vb_base' if h > 1 else 'vb_lt'
        if d < 1.5:
            return 'vb_out'
        if d < 2.4:
            return 'lv_dr'
        if d < 3.3:
            return 'lv_r' if (X + Y + f) % 3 else 'lv_o'
        return surf.p[Y][X]
    return autotile(color_at, E=2.0, R=5.5, Rn=2.0, wob=wob)


# The lava pieces a map can use (legend character -> which neighbours are
# lava). A piece is written as the 3x3 neighbourhood with 'L' = lava.
LAVA_PIECES = {
    'LAVA':      ('LLL', 'LLL', 'LLL'),
    'LAVA_N':    ('...', 'LLL', 'LLL'),
    'LAVA_S':    ('LLL', 'LLL', '...'),
    'LAVA_W':    ('.LL', '.LL', '.LL'),
    'LAVA_E':    ('LL.', 'LL.', 'LL.'),
    'LAVA_NW':   ('...', '.LL', '.LL'),
    'LAVA_NE':   ('...', 'LL.', 'LL.'),
    'LAVA_SW':   ('.LL', '.LL', '...'),
    'LAVA_SE':   ('LL.', 'LL.', '...'),
    'LAVA_INW':  ('.LL', 'LLL', 'LLL'),     # inner corners: ground only diagonally
    'LAVA_INE':  ('LL.', 'LLL', 'LLL'),
    'LAVA_ISW':  ('LLL', 'LLL', '.LL'),
    'LAVA_ISE':  ('LLL', 'LLL', 'LL.'),
    'LAVA_H':    ('...', 'LLL', '...'),     # one-cell-wide streams
    'LAVA_V':    ('.L.', '.L.', '.L.'),
    'LAVA_POOL': ('...', '.L.', '...'),
}


def piece_variants(rows):
    """Quadrant variants (0 inner .. 4 outer corner) of a lava piece."""
    def same(dx, dy):
        return rows[1 + dy][1 + dx] == 'L'
    out = []
    for c in range(4):
        sx = -1 if (c & 1) == 0 else 1
        sy = -1 if (c >> 1) == 0 else 1
        h, v, d = same(sx, 0), same(0, sy), same(sx, sy)
        if h and v:
            out.append(0 if d else 1)
        elif v:
            out.append(2)
        elif h:
            out.append(3)
        else:
            out.append(4)
    return out


# ---------------------------------------------------------------- hot spring

def spring_surface(f):
    img = Img(16, 16, 'hs_base')
    rip = [(1, 2, 3), (10, 1, 4), (6, 6, 3), (13, 8, 2), (2, 10, 4), (9, 13, 3)]
    for (x, y, n) in rip:
        x2 = x + f
        for i in range(n):
            img.set((x2 + i) % 16, y, 'hs_lt')
        img.set((x2 + n // 2) % 16, (y - 1) % 16, 'hs_hi')
        for i in range(max(1, n - 1)):
            img.set((x2 + 1 + i) % 16, (y + 1) % 16, 'hs_dk')
    # rising bubbles
    for (x, y) in ((4, 13), (12, 5)):
        yy = (y - f * 2) % 16
        img.set(x, yy, 'hs_hi')
    return img


def spring_quads(f):
    """Mineral hot spring autotiles: a white sinter rim (silica deposited by
    the hot water) inside a basalt kerb, so it sits on any ground."""
    from terrain_common import autotile
    surf = spring_surface(f)

    def color_at(d, X, Y, c, v, lx, ly):
        if d < -0.6:
            return 'vb_dk'
        if d < 0.6:
            return 'vb_base' if (hash2(X, Y, 9) & 3) else 'vb_lt'
        if d < 1.6:
            return 'va_hi'
        if d < 2.6:
            return 'va_lt'
        if d < 3.4:
            return 'hs_dk'
        return surf.p[Y][X]
    return autotile(color_at, E=2.0, R=6.0, Rn=2.5)


# ---------------------------------------------------------------- paths

CINDER_TEX = G('''
................
..h......m......
.......d.....h..
....m...........
..........h..m..
.d..............
......h.....d...
...m.......h....
.........m......
.h..d...........
.......h....m...
............d..h
..m..h..........
........d.......
.............m..
...h...m........
''', {'.': 'va_lt', 'h': 'va_hi', 'm': 'va_base', 'd': 'va_mid'})


def cinder_path_quads():
    """Raked cinder gravel paths on ash."""
    from terrain_common import autotile
    ash = ash_img(0)

    def color_at(d, X, Y, c, v, lx, ly):
        if d < -1.0:
            return ash.p[Y][X]
        if d < 0:
            return 'va_mid'
        if d < 1.0:
            return 'va_base'
        return CINDER_TEX.p[Y][X]
    return autotile(color_at, E=2.0, R=5.0, Rn=2.0)


# ---------------------------------------------------------------- cliffs

def column_face(seed=0, lip=None):
    """Basalt cliff face: vertical hexagonal columns seen from the side,
    each lit on its left facet, with horizontal joints. lip: 'ash' draws
    the ash-covered top edge (CLIFF), None = plain face (stacks)."""
    img = Img(16, 16)
    cols = [(0, 5), (5, 11), (11, 16)] if seed == 0 else [(0, 3), (3, 9), (9, 14), (14, 16)]
    joints = {0: (5, 12), 1: (2, 9), 2: (7, 14), 3: (4, 11)}
    for ci, (x0, x1) in enumerate(cols):
        jy = joints[(ci + seed) % 4]
        for x in range(x0, x1):
            for y in range(16):
                u = (x - x0) / max(1, x1 - x0 - 1)
                if x == x0:
                    c = 'vb_out'
                elif u < 0.3:
                    c = 'vb_hi' if x == x0 + 1 else 'vb_lt'
                elif u < 0.75:
                    c = 'vb_base'
                else:
                    c = 'vb_dk'
                if y in jy:
                    c = 'vb_out'
                elif y - 1 in jy and x > x0:
                    c = 'vb_lt' if u < 0.75 else 'vb_base'
                img.p[y][x] = c
    if lip == 'ash':
        top = G('''
        hhlhhhhhlhhhhlhh
        llbllllbllllbbll
        bbmbbbmbbbbmbbmb
        mmdmmddmmdmmdmmd
        dOddOddddOdddOdd
        ''', {'h': 'va_hi', 'l': 'va_lt', 'b': 'va_base', 'm': 'va_mid', 'd': 'va_dk',
              'O': 'vb_out'})
        img.paste(top, 0, 0)
        for x in (3, 8, 13):
            img.set(x, 5, 'va_dk')
    return img


# ---------------------------------------------------------------- overlays

def crag_img():
    """16x32 basalt spire (map borders, like trees): a cluster of broken
    columns, tallest at the back, outlined like every object. Transparent
    around it (the engine draws the ground beneath)."""
    img = Img(16, 32)
    spires = [  # (x0, x1, top_y, bottom_y)
        (1, 6, 10, 30), (5, 10, 1, 30), (9, 14, 6, 30),
    ]
    for (x0, x1, ty, by) in spires:
        w = x1 - x0
        for x in range(x0, x1 + 1):
            u = (x - x0) / w
            top = ty + int(round(abs(u - 0.35) * 5))
            for y in range(top, by + 1):
                if x in (x0, x1) or y == top or y == by:
                    c = 'b_out'
                elif y == top + 1:
                    c = 'vb_hi' if u < 0.55 else 'vb_lt'
                elif u < 0.34:
                    c = 'vb_lt'
                elif u < 0.7:
                    c = 'vb_base'
                else:
                    c = 'vb_dk'
                if c != 'b_out' and (y - ty) % 9 == 8:
                    c = 'b_out'
                    if x == x0 + 1:
                        img.p[y + 1][x] = 'vb_hi'
                img.p[y][x] = c
    for (x, y) in ((7, 5), (12, 11), (3, 15), (8, 20), (11, 24)):
        img.set(x, y, 'ob_hi')
        img.set(x, y + 1, 'ob_base')
    return img


def dead_tree_img():
    """16x32 charred tree: a black trunk and bare, twisted branches."""
    img = Img(16, 32)
    TK = {'.': None, 'O': 'b_out', 'l': 'vcw_lt', 'b': 'vcw_base', 'd': 'vcw_dk'}
    art = G('''
    ................
    ..O.......O.....
    .OlO..O..OlO....
    ..OlO.OO.Ol.O.O.
    ...OlOlO.OlOOlO.
    .O..OlbOOlbOlO..
    .OlO.OlblbdlO...
    ..OlOOlbbbdO..O.
    ...OllbbbdO..OlO
    ....OlbbbdOOOlO.
    .....Olbbbdlld..
    ..OOOOlbbdOOO...
    .OlllOlbbdO.....
    ..OOOOlbbdO.....
    ......Olbbd.....
    ......Olbbd.....
    ......Olbbd.....
    ......Olbdd.....
    .....Olbbdd.....
    .....Olbbdd.....
    .....Olbbdd.....
    ....OOlbbddO....
    ....Olbbbbd.O...
    ...OlbbObbddO...
    ..OlbO.ObbdOdO..
    ..OOO..OOOO.OO..
    ................
    ................
    ................
    ................
    ................
    ................
    ''', TK)
    img.paste(art, 0, 4)
    return img


def ledge_img_ash(ends=None):
    """One-way ash ledge (walk down to hop): a lip of ash over a short
    basalt step, like the route ledges."""
    img = ash_img(0).copy()
    for x in range(16):
        img.p[5][x] = 'va_hi' if x % 5 else 'va_lt'
        img.p[6][x] = 'va_lt'
        img.p[7][x] = 'va_base' if x % 4 != 1 else 'va_mid'
        img.p[8][x] = 'vb_out'
        for y in (9, 10, 11):
            img.p[y][x] = 'vb_lt' if y == 9 else ('vb_base' if y == 10 else 'vb_dk')
            if x % 6 == 0 and y > 9:
                img.p[y][x] = 'vb_out'
        img.p[12][x] = 'vb_out'
        img.p[13][x] = 'va_dk'
        img.p[14][x] = 'va_mid' if x % 2 else 'va_dk'
    if ends:
        a = ash_img(0)
        rng = range(0, 3) if ends == 'L' else range(13, 16)
        for x in rng:
            for y in range(5, 16):
                img.p[y][x] = a.p[y][x]
        edge = 3 if ends == 'L' else 12
        for y in range(6, 13):
            img.p[y][edge] = 'vb_out'
    return img


# ---------------------------------------------------------------- rails

def rail_img(vertical=False):
    """Mine-cart rails on dark cinder ballast (walkable)."""
    img = Img(16, 16, 'va_mid')
    speckle(img, 23, [(40, 'va_dk'), (26, 'va_base'), (6, 'vb_dk')])
    # sleepers
    for sy in (1, 6, 11):
        for y in (sy, sy + 1, sy + 2):
            for x in range(1, 15):
                img.p[y][x] = 'vcw_lt' if y == sy else ('vcw_base' if y == sy + 1 else 'vcw_dk')
        img.p[sy + 1][0] = 'b_out'
        img.p[sy + 1][15] = 'b_out'
    # rails
    for x in (3, 12):
        for y in range(16):
            img.p[y][x] = 'vb_hi'
            img.p[y][x + 1] = 'vb_base'
    if vertical:
        o = Img(16, 16)
        for y in range(16):
            for x in range(16):
                o.p[y][x] = img.p[x][y]
        # relight: rails lit on the left
        for y in range(16):
            for x in range(16):
                if o.p[y][x] == 'vb_hi' and x in (4, 13):
                    o.p[y][x] = 'vb_base'
                elif o.p[y][x] == 'vb_base' and x in (3, 12):
                    o.p[y][x] = 'vb_hi'
        return o
    return img


# ---------------------------------------------------------------- caves

def cave_floor_img(seed=0):
    """Ember Tunnel floor: dark basalt grit, warm-lit, with lava-glass
    flecks."""
    img = Img(16, 16, 'vb_base')
    speckle(img, 61 + seed, [(34, 'vb_dk'), (16, 'vb_lt'), (5, 'va_mid'), (2, 'eb_dk')])
    if seed == 0:
        pebble(img, 3, 4, 'vb_hi', 'vb_lt', 'vb_out')
        pebble(img, 11, 12, 'va_lt', 'va_mid', 'vb_out', big=True)
    else:
        pebble(img, 9, 3, 'vb_hi', 'vb_lt', 'vb_out', big=True)
        put(img, [(2, 11), (3, 12), (4, 12)], 'vb_out')
        img.set(13, 7, 'eb_base')
    return img


def cave_wall_top():
    """The rock mass above a cave wall: rough, dark and solid."""
    img = Img(16, 16, 'vb_dk')
    speckle(img, 83, [(40, 'vb_out'), (30, 'vb_base')])
    for (x, y) in ((3, 3), (10, 6), (6, 11), (13, 13)):
        put(img, [(x, y), (x + 1, y)], 'vb_lt')
        put(img, [(x, y + 1), (x + 1, y + 1)], 'vb_base')
        put(img, [(x + 2, y + 1), (x, y + 2), (x + 1, y + 2)], 'vb_out')
    return img


def cave_wall_face(glow=True):
    """A cave wall seen from the front, down to the floor: basalt columns
    with a lava-lit lower edge."""
    img = column_face(1)
    for x in range(16):
        img.p[0][x] = 'vb_out'
        if glow:
            img.p[14][x] = 'eb_dk' if x % 3 else 'vb_out'
        img.p[15][x] = 'vb_out'
    return img


def cave_exit_img():
    """Exit mat of a cave: the light of the way out spills over the grit."""
    img = cave_floor_img(0)
    for y in range(6, 16):
        for x in range(2, 14):
            d = abs(x - 7.5) / 6.0 + (15 - y) / 14.0
            if d < 0.55:
                img.p[y][x] = 'va_hi' if (x + y) % 2 else 'va_lt'
            elif d < 0.85:
                img.p[y][x] = 'va_lt' if (x + y) % 2 else 'va_base'
            elif d < 1.05 and (x + y) % 2:
                img.p[y][x] = 'va_base'
    return img


def embermoss_layers():
    """Glowing ember moss on the tunnel floor (wild kin roam in it)."""
    bottom = cave_floor_img(1)
    tuft = G('''
    ..y...
    .hlh..
    hlbld.
    lbbbdd
    ''', {'.': None, 'y': 'su_y', 'h': 'eb_hi', 'l': 'eb_lt', 'b': 'eb_base', 'd': 'eb_dk'})
    for (x, y) in ((1, 2), (8, 0), (4, 7), (11, 6), (0, 11), (7, 12), (13, 12)):
        bottom.paste(tuft, x, y)
    top = Img(16, 16)
    for (x, y) in ((4, 7), (11, 6), (0, 11), (7, 12), (13, 12)):
        top.paste(tuft, x, y)
    for y in range(0, 10):
        for x in range(16):
            if y < 9:
                top.p[y][x] = None
    return bottom, top


# ---------------------------------------------------------------- the Anvil Hall

def hall_floor_img(vent=False):
    """Riveted iron deck plates of the Anvil Hall."""
    img = Img(16, 16, 'ir_base')
    for y in range(16):
        for x in range(16):
            u, v = x % 8, y % 8
            if u == 7 or v == 7:
                c = 'ir_dkr'
            elif u == 0 or v == 0:
                c = 'ir_lt'
            elif u == 6 or v == 6:
                c = 'ir_dk'
            else:
                c = 'ir_base'
                if (hash2(x, y, 13) & 15) == 0:
                    c = 'ir_lt'
            img.p[y][x] = c
    for (x, y) in ((1, 1), (5, 1), (1, 5), (5, 5), (9, 9), (13, 9), (9, 13), (13, 13),
                   (9, 1), (13, 5), (1, 9), (5, 13)):
        img.set(x, y, 'ir_hi')
        img.set(x + 1, y + 1, 'ir_dk')
    if vent:
        for y in range(3, 13):
            for x in range(3, 13):
                if y in (3, 12) or x in (3, 12):
                    img.p[y][x] = 'ir_dkr'
                elif (y - 4) % 2 == 0:
                    img.p[y][x] = 'bk_dk' if (x + y) % 3 else 'bk_base'
                else:
                    img.p[y][x] = 'ir_dkr'
    return img


def brick_band(img, y0, y1, x0=0, x1=15, course=4, off=0):
    """Brick courses (lit top edge, dark mortar) in rows y0..y1."""
    for y in range(y0, y1 + 1):
        r = (y - y0) % course
        for x in range(x0, x1 + 1):
            shift = 4 if ((y - y0) // course) % 2 else 0
            if r == course - 1:
                c = 'bk_dk'
            elif (x + shift + off) % 8 == 7:
                c = 'bk_dk'
            elif r == 0:
                c = 'bk_hi'
            else:
                c = 'bk_base'
            img.set(x, y, c)


def hall_wall_top():
    img = Img(16, 16)
    for x in range(16):
        img.p[0][x] = 'b_out'
        img.p[1][x] = 'ir_dk'
        img.p[2][x] = 'ir_dkr'
    brick_band(img, 3, 15)
    return img


def hall_wall():
    """Lower hall wall: brick, an iron rail with rivets, dark footing."""
    img = Img(16, 16)
    brick_band(img, 0, 7)
    for x in range(16):
        img.p[8][x] = 'ir_hi'
        img.p[9][x] = 'ir_lt'
        img.p[10][x] = 'ir_base'
        img.p[11][x] = 'ir_base' if x % 4 else 'ir_hi'
        img.p[12][x] = 'ir_dk'
        img.p[13][x] = 'ir_dkr'
        img.p[14][x] = 'ir_dkr'
        img.p[15][x] = 'b_out'
    return img


def hall_mat():
    img = hall_floor_img()
    for y in range(3, 15):
        for x in range(1, 15):
            edge = y in (3, 14) or x in (1, 14)
            img.p[y][x] = 'b_out' if edge else ('bk_base' if (x + y) % 4 else 'bk_dk')
    for x in range(3, 13):
        img.p[8][x] = 'bk_hi' if x % 2 else 'bk_base'
    return img
