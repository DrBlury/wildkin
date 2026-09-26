#!/usr/bin/env python3
"""Buildings (stamps) of the FAR region and a helper for animated autotile
blocks. Used by tools/tilesets/ts_volcanic.py and ts_dream.py (owner: W-FAR).

Buildings are drawn once in semantic colours and recoloured per tileset:
  GND / GSH       flat ground around the building / its ground shadow
  WHI / WBA / WDK the wall material (brick in Cindermoor, plaster in Dreamspire)
Roofs use a 5-step ramp R = {'1'..'5': colour}. Roof banks share one layout,
so a building recoloured with another roof bank reuses the same tiles.
"""

import math
from pixelart import Img, G

# ---------------------------------------------------------------------------
# animated autotile blocks (lava, hot spring)
# ---------------------------------------------------------------------------


def add_quads_anim(gf, ts, out, quads_fn, nframes, bank, period):
    """Encode quads_fn(f, ...) (4 corners x 5 variants of 8x8 Imgs) for every
    frame as one contiguous, never-shared block of animated tiles.
    Returns q[c][v] = map entry (tile | bank << 12)."""
    try:
        frames_q = [quads_fn(f, nframes) for f in range(nframes)]
    except TypeError:
        frames_q = [quads_fn(f) for f in range(nframes)]
    q = [[0] * 5 for _ in range(4)]
    anim = [[] for _ in range(nframes)]
    first = len(ts.tiles)
    seen = {}
    for c in range(4):
        for v in range(5):
            frames = tuple(ts.indices(gf.img_pix(frames_q[f][c][v]), bank) for f in range(nframes))
            if frames not in seen:
                seen[frames] = ts.add_raw(frames[0])
                for f in range(nframes):
                    anim[f].append(frames[f])
            q[c][v] = seen[frames] | (bank << 12)
    out['anims'] = out.get('anims', []) + [(first, anim, period)]
    return q


# ---------------------------------------------------------------------------
# lettering (a few more letters than the village sign font)
# ---------------------------------------------------------------------------

FONT = {
    'A': ['.##.', '#..#', '####', '#..#', '#..#'],
    'B': ['###.', '#..#', '###.', '#..#', '###.'],
    'C': ['.###', '#...', '#...', '#...', '.###'],
    'D': ['###.', '#..#', '#..#', '#..#', '###.'],
    'E': ['####', '#...', '###.', '#...', '####'],
    'F': ['####', '#...', '###.', '#...', '#...'],
    'G': ['.###', '#...', '#.##', '#..#', '.###'],
    'H': ['#..#', '#..#', '####', '#..#', '#..#'],
    'I': ['.##.', '.##.', '.##.', '.##.', '.##.'],
    'L': ['#...', '#...', '#...', '#...', '####'],
    'M': ['#..#', '####', '####', '#..#', '#..#'],
    'N': ['#..#', '##.#', '#.##', '#..#', '#..#'],
    'O': ['.##.', '#..#', '#..#', '#..#', '.##.'],
    'P': ['###.', '#..#', '###.', '#...', '#...'],
    'R': ['###.', '#..#', '###.', '#.#.', '#..#'],
    'S': ['.###', '#...', '.##.', '...#', '###.'],
    'T': ['####', '.##.', '.##.', '.##.', '.##.'],
    'U': ['#..#', '#..#', '#..#', '#..#', '.##.'],
    'V': ['#..#', '#..#', '#..#', '.##.', '.##.'],
    'Y': ['#..#', '#..#', '.##.', '.##.', '.##.'],
    ' ': ['..', '..', '..', '..', '..'],
}


def sign_plate(text, plate='st_hi', ink='gl_dk', edge='st_lt'):
    widths = [len(FONT[ch][0]) + 1 for ch in text]
    w = sum(widths) - 1 + 6
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
    x0 = 3
    for ch in text:
        for yy, row in enumerate(FONT[ch]):
            for xx, px in enumerate(row):
                if px == '#':
                    img.p[2 + yy][x0 + xx] = ink
        x0 += len(FONT[ch][0]) + 1
    return img


# ---------------------------------------------------------------------------
# walls
# ---------------------------------------------------------------------------

def brick_wall(img, x0, x1, y0, y1):
    """Brick courses aligned to the 8px tile grid (repeat every 8x8)."""
    for y in range(y0, y1 + 1):
        r = y % 4
        for x in range(x0, x1 + 1):
            shift = 4 if (y // 4) % 2 else 0
            if r == 3:
                c = 'WDK'
            elif (x + shift) % 8 == 7:
                c = 'WDK'
            elif r == 0:
                c = 'WHI'
            else:
                c = 'WBA'
            img.set(x, y, c)


def plaster_wall(img, x0, x1, y0, y1):
    """Smooth lime plaster with faint trowel marks (repeats every 8x8)."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            u, v = x % 8, y % 8
            c = 'WBA'
            if (u, v) in ((1, 2), (2, 2), (5, 6), (6, 6)):
                c = 'WHI'
            elif (u, v) in ((3, 3), (7, 7)):
                c = 'WDK'
            img.set(x, y, c)


def ground_fill(img):
    for y in range(img.h):
        for x in range(img.w):
            if img.p[y][x] is None:
                img.p[y][x] = 'GND'


def ground_shadow(img, x0, x1, y):
    for x in range(x0, x1 + 1):
        img.set(x, y, 'GSH')
        if x0 + 1 <= x <= x1 - 1:
            img.set(x, y + 1, 'GSH')


def foundation(img, x0, x1, y):
    for x in range(x0, x1 + 1):
        img.set(x, y, 'b_out')
        img.set(x, y + 3, 'b_out')
        for yy in (y + 1, y + 2):
            c = 'st_lt' if yy == y + 1 else 'st_mid'
            if (x + (4 if yy == y + 2 else 0)) % 8 == 0:
                c = 'st_mid' if yy == y + 1 else 'b_out'
            img.set(x, yy, c)


def wall_block(img, x0, x1, y0, y1, style):
    (brick_wall if style == 'brick' else plaster_wall)(img, x0 + 1, x1 - 1, y0, y1)
    for y in range(y0, y1 + 4):
        img.set(x0 - 1, y, 'b_out')
        img.set(x1 + 1, y, 'b_out')
        img.set(x0, y, 'WHI')
        img.set(x1, y, 'WDK')
    # eave shadow
    for x in range(x0, x1 + 1):
        img.set(x, y0 + 2, 'WDK')
        img.set(x, y0 + 3, 'WDK' if x % 2 == 0 else 'WBA')


# ---------------------------------------------------------------------------
# roofs, chimneys, emblems
# ---------------------------------------------------------------------------

def chimney(img, x, y, h, R, glow=None):
    """A stone chimney standing on the roof, casting a roof shadow."""
    w = 9
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if xx in (x, x + w - 1) or yy == y + h - 1:
                c = 'b_out'
            elif yy in (y, y + 1):
                c = 'b_out' if yy == y else 'st_hi'
            elif yy == y + 2:
                c = 'st_lt'
            else:
                c = 'st_lt' if (xx - x) < 3 else 'st_mid'
                if (yy - y) % 4 == 0:
                    c = 'st_mid'
            img.set(xx, yy, c)
    for xx in range(x + 2, x + w - 2):
        img.set(xx, y + 1, glow or 'st_hi')
    for yy in range(y + 3, y + h):
        img.set(x + w, yy, R['5'])
    for xx in range(x + 1, x + w + 1):
        img.set(xx, y + h, R['5'])


def emblem_anvil():
    """An iron anvil on a plate (Anvil Hall)."""
    return G('''
    OOOOOOOOOOOOOOOOOOOO
    OHHHHHHHHHHHHHHHHHLO
    OHOOOOOOOOOOOOOOOHLO
    OHO1111111111111OHLO
    OO11222222222222OOLO
    O.O1222222222223O.LO
    ...OO22222222223O.O.
    .....OO22222223OO...
    .......O233333O.....
    ......O22233333O....
    .....O2222333333O...
    ....OOOOOOOOOOOOOO..
    ''', {'.': None, 'O': 'b_out', 'H': 'st_hi', 'L': 'st_lt', '1': 'R1', '2': 'R3', '3': 'R4'})


def emblem_mirror():
    """A round silver mirror in a frame (Mirror Hall)."""
    img = Img(18, 18)
    for y in range(18):
        for x in range(18):
            d = math.hypot(x + 0.5 - 9, y + 0.5 - 9)
            if d <= 8.6:
                if d > 7.6:
                    c = 'b_out'
                elif d > 6.2:
                    c = 'R1' if (x + y) < 16 else 'R3'
                elif d > 5.4:
                    c = 'b_out'
                else:
                    t = (x - 9) + (y - 9)
                    c = 'st_hi' if -5 < t < -1 else ('st_lt' if t < 3 else 'st_mid')
                img.p[y][x] = c
    return img


def emblem_book():
    """An open book (the Dust Library)."""
    return G('''
    .OOOOOO..OOOOOO.
    OHHHHHHOOHHHHHLO
    OHLLLLHOOHLLLHLO
    OHHHHHHOOHHHHHLO
    OHLLLHHOOHLLLHLO
    OHHHHHHOOHHHHHLO
    OHLLLLHOOHLLHHLO
    OHHHHHHOOHHHHHLO
    OO33333OO33333OO
    .OOOOOOOOOOOOOO.
    ''', {'.': None, 'O': 'b_out', 'H': 'st_hi', 'L': 'st_lt', '3': 'R3'})


def recolor(img, R, gnd, wall):
    """Semantic colours -> real ones."""
    m = {'GND': gnd[0], 'GSH': gnd[1], 'WHI': wall[0], 'WBA': wall[1], 'WDK': wall[2]}
    for k in '12345':
        m['R' + k] = R[k]
    return img.replace(m)


# ---------------------------------------------------------------------------
# a cottage-sized building (80x64, 5x4 cells): door at col 2 row 3
# ---------------------------------------------------------------------------

def cottage(gf, kind, R, style, gnd, wall, sign=None, glow=None):
    img = Img(80, 64)
    ground_shadow(img, 7, 77, 60)
    wall_block(img, 5, 74, 30, 55, style)
    foundation(img, 4, 75, 56)
    for wx in (9, 57):
        if kind == 'shop':
            img.paste(gf.SHOP_WINDOW, wx, 40)
            aw = gf.AWNING.replace({'rt_hi': R['1'], 'rt_lt': R['2'], 'rt_base': R['3'],
                                    'rt_dk': R['4'], 'rt_dkr': R['5']})
            img.paste(aw, wx - 2, 34)
        else:
            img.paste(gf.WINDOW, wx, 38)
    if kind in ('house', 'forge'):
        img.paste(gf.DOOR, 33, 38)
    else:
        img.paste(gf.GLASS_DOOR, 32, 42)
    img.paste(gf.STEP, 32, 56)
    gf.draw_roof(img, 1, 78, 5, 31, 5, R)
    if kind == 'house':
        chimney(img, 58, 1, 10, R)
    if kind == 'forge':
        chimney(img, 56, 0, 13, R, glow=glow)
        chimney(img, 14, 3, 9, R)
    if kind == 'heal':
        img.paste(gf.BIG_FLAME.replace({'rf_lt': R['2'], 'rf_hi': R['1']}), 30, 6)
    if sign:
        pl = sign_plate(sign)
        img.paste(pl, 40 - pl.w // 2, 26 if kind != 'heal' else 26)
    ground_fill(img)
    return recolor(img, R, gnd, wall)


# ---------------------------------------------------------------------------
# a hall (112x80, 7x5 cells): door at col 3 row 4
# ---------------------------------------------------------------------------

def hall(gf, R, style, gnd, wall, sign, emblem, spire=False):
    img = Img(112, 80)
    ground_shadow(img, 7, 109, 76)
    wall_block(img, 5, 106, 34, 71, style)
    foundation(img, 4, 107, 72)
    # tall windows either side, two pairs
    tall = G('''
    OOOOOOOOOOOO
    OHHHHHHHHHLO
    OHccccccccLO
    OHcaabbbbcLO
    OHcabbbbbcLO
    OHcbbbbbbcLO
    OHHHHHHHHHLO
    OHcbbbbbbcLO
    OHcbbbbabcLO
    OHcbbbbbbcLO
    OHcbbbbbbcLO
    OHcbbbbbbcLO
    OHLLLLLLLLLO
    OOOOOOOOOOOO
    ''', {'O': 'b_out', 'H': 'st_hi', 'L': 'st_lt', 'a': 'gl_hi', 'b': 'gl_base', 'c': 'gl_dk'})
    for wx in (10, 26, 74, 90):
        img.paste(tall, wx, 44)
    img.paste(gf.GLASS_DOOR, 48, 58)
    img.paste(gf.STEP, 48, 72)
    gf.draw_roof(img, 1, 110, 8, 35, 5, R)
    if spire:
        # a slim spire with a finial over the centre
        for y in range(0, 14):
            half = max(0, int((y - 1) * 0.45))
            for x in range(56 - half - 1, 56 + half + 2):
                if x in (56 - half - 1, 56 + half + 1) or y == 0:
                    c = 'b_out'
                else:
                    c = 'R1' if x < 56 else ('R3' if x < 56 + half else 'R4')
                img.set(x, y, c)
    pl = sign_plate(sign)
    img.paste(pl, 56 - pl.w // 2, 26)
    em = emblem
    img.paste(em, 56 - em.w // 2, 12 if not spire else 13)
    ground_fill(img)
    return recolor(img, R, gnd, wall)


# ---------------------------------------------------------------------------
# rock arches: cave mouths (48x32, 3x2 cells): door at col 1 row 1
# ---------------------------------------------------------------------------

def rock_arch(face, floor):
    """A dark opening in a basalt wall. face: 16x16 wall art for the row
    above and beside the opening; floor: 16x16 ground art at its foot."""
    img = Img(48, 32)
    for cx in range(3):
        img.paste(face, cx * 16, 0)
    for cx in (0, 2):
        img.paste(face, cx * 16, 16)
    img.paste(floor, 16, 16)
    # the opening: a rounded arch, dark inside, lit rim
    for y in range(4, 32):
        for x in range(12, 36):
            dx = (x + 0.5 - 24) / 11.0
            top = 4 + 9 * (1 - math.sqrt(max(0.0, 1 - dx * dx)))
            if y < top:
                continue
            if y < top + 1 or abs(dx) > 0.93:
                c = 'vb_out'
            else:
                depth = (y - top) / 28.0 + abs(dx) * 0.4
                c = 'vb_out' if depth < 0.55 else 'vb_dk'
                if y >= 29:
                    c = 'vb_dk' if (x + y) % 2 else 'vb_base'
            img.set(x, y, c)
    # lit stones framing the arch
    for x in range(11, 37):
        dx = (x + 0.5 - 24) / 12.0
        if abs(dx) <= 1:
            y = int(4 + 9 * (1 - math.sqrt(max(0.0, 1 - dx * dx)))) - 1
            img.set(x, y, 'vb_hi' if x < 24 else 'vb_lt')
            img.set(x, y - 1, 'vb_out')
    for y in range(12, 32):
        img.set(11, y, 'vb_hi')
        img.set(10, y, 'vb_out')
        img.set(36, y, 'vb_dk')
        img.set(37, y, 'vb_out')
    return img


# ---------------------------------------------------------------------------
# Dreamspire towers (48x80, 3x5 cells): door at col 1 row 4
# ---------------------------------------------------------------------------

def cone_roof(img, cx, y0, y1, half0, half1, R):
    """A tiered roof seen from the front: a trapezoid with an upturned eave."""
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, y1 - y0)
        half = half0 + (half1 - half0) * t
        xl, xr = int(round(cx - half)), int(round(cx + half))
        for x in range(xl, xr + 1):
            if x in (xl, xr) or y == y0:
                c = 'b_out'
            elif y == y1:
                c = 'b_out'
            elif y == y1 - 1:
                c = R['5']
            elif y == y1 - 2:
                c = R['2']
            else:
                u = (x - xl) / max(1, xr - xl)
                c = R['1'] if u < 0.22 else (R['2'] if u < 0.45 else (R['3'] if u < 0.8 else R['4']))
                if (y - y0) % 4 == 3 and 0.1 < u < 0.9:
                    c = R['4'] if u > 0.5 else R['3']
            img.set(x, y, c)
    # upturned eave tips
    img.set(int(round(cx - half1)) - 1, y1 - 2, 'b_out')
    img.set(int(round(cx + half1)) + 1, y1 - 2, 'b_out')
    img.set(int(round(cx - half1)) - 1, y1 - 3, R['2'])
    img.set(int(round(cx + half1)) + 1, y1 - 3, R['4'])


def round_window(img, x, y):
    win = G('''
    ..OOOO..
    .OHHHHO.
    OHcaabLO
    OHabbbLO
    OHbbbbLO
    OHcbbcLO
    OLLLLLLO
    OOOOOOOO
    ''', {'.': None, 'O': 'b_out', 'H': 'st_hi', 'L': 'st_lt', 'a': 'gl_hi', 'b': 'gl_base',
          'c': 'gl_dk'})
    img.paste(win, x, y)


def lantern_hanging(img, x, y):
    """A paper lantern hanging from a bracket (drawn in roof colours)."""
    lan = G('''
    OOOO..
    ...O..
    ..OOO.
    .O121O
    .O232O
    .O232O
    .O121O
    ..OOO.
    ...O..
    ''', {'.': None, 'O': 'b_out', '1': 'R1', '2': 'R2', '3': 'R3'})
    img.paste(lan, x, y)


def tower(gf, R, gnd, wall):
    img = Img(48, 80)
    ground_shadow(img, 8, 45, 76)
    # lower storey
    wall_block(img, 5, 42, 50, 71, 'plaster')
    foundation(img, 4, 43, 72)
    img.paste(gf.DOOR, 17, 54)
    img.paste(gf.STEP, 16, 72)
    round_window(img, 7, 56)
    round_window(img, 33, 56)
    # first roof tier
    cone_roof(img, 23.5, 38, 51, 12, 22, R)
    # upper storey
    wall_block(img, 12, 35, 24, 38, 'plaster')
    round_window(img, 20, 27)
    # top roof and finial
    cone_roof(img, 23.5, 6, 25, 3, 16, R)
    for y in range(0, 7):
        img.set(23, y, 'b_out' if y in (0, 6) else 'st_hi')
        img.set(24, y, 'b_out' if y in (0, 6) else 'st_lt')
    lantern_hanging(img, 1, 50)
    lantern_hanging(img, 41, 50)
    ground_fill(img)
    return recolor(img, R, gnd, wall)


# ---------------------------------------------------------------------------
# the stamp lists
# ---------------------------------------------------------------------------

IRON_R = {'1': 'ir_hi', '2': 'ir_lt', '3': 'ir_base', '4': 'ir_dk', '5': 'ir_dkr'}
RUST_R = {'1': 'rr_hi', '2': 'rr_lt', '3': 'rr_base', '4': 'rr_dk', '5': 'rr_dkr'}
VO_GND = ('va_base', 'va_dk')
VO_WALL = ('bk_hi', 'bk_base', 'bk_dk')

VOLCANIC_DOORS = [('HEARTH', 2, 3), ('SHOP', 2, 3), ('FORGE', 2, 3), ('HOUSE', 2, 3),
                  ('HOUSE_RUST', 2, 3), ('ANVIL_HALL', 3, 4), ('CAVE_MOUTH', 1, 1),
                  ('TUNNEL_ARCH', 1, 1)]


def volcanic_stamps(gf):
    import terrain_far as tf
    st = []
    st.append(('HEARTH', cottage(gf, 'heal', RUST_R, 'brick', VO_GND, VO_WALL), (6, 7),
               'CINDER HEARTH HALL (flame), door col 2 row 3'))
    st.append(('SHOP', cottage(gf, 'shop', IRON_R, 'brick', VO_GND, VO_WALL, sign='SHOP'), (5, 7),
               'CINDER SHOP, door col 2 row 3'))
    st.append(('FORGE', cottage(gf, 'forge', RUST_R, 'brick', VO_GND, VO_WALL, sign='FORGE',
                                glow='bk_hi'), (6, 7), 'THE FORGE (two chimneys), door col 2 row 3'))
    st.append(('HOUSE', cottage(gf, 'house', IRON_R, 'brick', VO_GND, VO_WALL), (5, 7),
               'brick house, iron roof, door col 2 row 3'))
    st.append(('HOUSE_RUST', cottage(gf, 'house', RUST_R, 'brick', VO_GND, VO_WALL), (6, 7),
               'brick house, rust roof, door col 2 row 3'))
    st.append(('ANVIL_HALL', hall(gf, IRON_R, 'brick', VO_GND, VO_WALL, 'ANVIL HALL', emblem_anvil()),
               (5, 7), 'ANVIL HALL, door col 3 row 4'))
    floor = tf.ash_img(0)
    st.append(('CAVE_MOUTH', rock_arch(tf.column_face(0), floor), (0,),
               'cave mouth in a basalt cliff (EMBER TUNNEL), door col 1 row 1'))
    st.append(('TUNNEL_ARCH', rock_arch(tf.cave_wall_face(), tf.cave_floor_img(0)), (0,),
               'arch in a cave wall (to CALDERA HEART), door col 1 row 1'))
    return st
