"""The 'city' tileset: LUMEN CITY, the lamp-lit city of the east (owner:
W-EAST, docs/EXPANSION.md 9).

Streets are cobbled and autotiled with kerbs ('='), the canal is a stone-
rimmed autotiled channel ('~'), pavements are warm flagstones, the market
square is sandstone herringbone, and the parks have lawns, flower beds,
trees and a patch of wild grass. Buildings are stamps composed from
modular 16x16 parts (roofs in terracotta, copper patina and slate; walls
in plaster, brick and dressed stone), so every building shares the same
tiles and only its sign and emblem are unique.

Legend (map characters, also documented in src/game/world/east/data.h):
  .  PAVE        flagstone pavement (+ PAVE2 drain grate, 1/16)
  =  STREET      cobbled street, autotiled kerbs against anything else
  ~  CANAL       canal water with a stone rim (autotiled, animated)
  c  COBBLE      plain cobbles (alleys and yards, no kerbs)
  p  PLAZA       sandstone herringbone (market square)
  g  GRASS       lawn (+ GRASS2 / GRASS3)
  ,  TALLGRASS   the park's wild grass (kin roam)
  r  FLOWER_RED  flower bed    y  FLOWER_YELLOW
  T  TREE_TOP    t  TREE_BOTTOM   (overlay trees on any ground)
  #  WALL_TOP    top of the old city wall (solid)
  w  WALL        face of the old city wall (solid)
Stamps (STAMP(CY, NAME, x, y)): see STAMPS below for sizes and doors.
"""

import math

USES_DECOR = ['SIGNPOST', 'BENCH', 'BARREL', 'CRATE', 'CRATE_STACK', 'SACKS', 'BUSH',
              'BIG_TREE', 'HEDGE', 'HEDGE_END', 'LANTERN_POST', 'STONE_LANTERN', 'FENCE',
              'FENCE_END', 'MARKET_STALL', 'MAILBOX', 'SIGN_ARROW', 'PEBBLES', 'SMALL_FLOWERS',
              'FALLEN_LEAVES', 'ROCK', 'LILY_PADS', 'CART', 'NOTICE_BOARD', 'BEEHIVE']

CITY_COLORS = {
    # flagstone pavement (warm grey)
    'pv_hi': (236, 230, 214),
    'pv_lt': (212, 204, 186),
    'pv_base': (190, 182, 166),
    'pv_dk': (150, 142, 132),
    # cobbled street / slate (cool blue-grey)
    'cb_hi': (180, 188, 204),
    'cb_lt': (150, 158, 180),
    'cb_base': (122, 130, 156),
    'cb_dk': (92, 98, 126),
    'cb_out': (60, 62, 88),
    # bricks (same values as the indoor catalog)
    'br_hi': (216, 124, 92),
    'br_base': (176, 84, 64),
    'br_dk': (122, 54, 50),
    # copper and electric glow (same values as the outdoor catalog)
    'fx_org': (240, 144, 48),
    'sg_hi': (200, 250, 255),
    'sg_base': (80, 200, 248),
    'p_yel': (248, 232, 128),
}

TERRAIN = ['PAVE', 'PAVE2', 'COBBLE', 'PLAZA', 'GRASS', 'GRASS2', 'GRASS3', 'TALLGRASS',
           'FLOWER_RED', 'FLOWER_YELLOW', 'TREE_TOP', 'TREE_BOTTOM', 'WALL_TOP', 'WALL']

TERRAIN_DOC = {
    'PAVE': 'flagstone pavement (+ PAVE2 with a drain grate)',
    'COBBLE': 'plain cobbles without kerbs (alleys, yards)',
    'PLAZA': 'sandstone herringbone (the market square)',
    'GRASS': 'park lawn + 2 variants',
    'TALLGRASS': 'wild grass in the park; kin roam here',
    'FLOWER_RED': 'animated flower beds (2 frames)',
    'TREE_TOP': '16x32 park tree: TOP above BOTTOM (overlay; any ground)',
    'WALL_TOP': 'top of the old city wall (solid); WALL is its face',
}

# ---------------------------------------------------------------------------
# palette banks
# ---------------------------------------------------------------------------

BANK_STREET = ['cb_hi', 'cb_lt', 'cb_base', 'cb_dk', 'cb_out', 'pv_hi', 'pv_lt', 'pv_base',
               'pv_dk', 'w_hi', 'w_lt', 'w_base', 'w_mid', 'w_dk', 'b_out']
BANK_RED = ['b_out', 'rf_hi', 'rf_lt', 'rf_base', 'rf_dk', 'rf_dkr', 'wl_hi', 'wl_base',
            'wl_dk', 'st_hi', 'st_lt', 'st_mid', 'gl_dk', 'st_dk', 'wd_dk']
BANK_TEAL = ['b_out', 'rt_hi', 'rt_lt', 'rt_base', 'rt_dk', 'rt_dkr', 'fx_org', 'sg_hi',
             'sg_base', 'p_yel', 'white', 'st_lt', 'st_mid', 'st_dk', 'wd_dk']
BANK_BRICK = ['b_out', 'br_hi', 'br_base', 'br_dk', 'st_hi', 'st_lt', 'st_mid', 'st_dk',
              'wd_lt', 'wd_base', 'wd_dk', 'gl_hi', 'gl_base', 'gl_dk', 'p_yel']
BANK_PLASTER = ['b_out', 'wl_hi', 'wl_base', 'wl_dk', 'st_hi', 'st_lt', 'st_mid', 'st_dk',
                'wd_lt', 'wd_base', 'wd_dk', 'gl_hi', 'gl_base', 'gl_dk', 'p_yel']


def banks(gf):
    import decor_outdoor
    return [
        gf.BANK_GROUND,                     # 0 grass, flowers, plaza sandstone
        BANK_STREET,                        # 1 pavement, streets, canal, slate roofs
        gf.BANK_TREES,                      # 2 trees, bushes, hedges
        decor_outdoor.TOWN_DECOR_BANK,      # 3 props
        BANK_RED,                           # 4 terracotta roofs, awnings, red props
        BANK_TEAL,                          # 5 copper patina roofs, copper, sparks
        BANK_BRICK,                         # 6 brick walls, windows, doors
        BANK_PLASTER,                       # 7 plaster and stone walls
    ]


# ---------------------------------------------------------------------------
# ground textures
# ---------------------------------------------------------------------------

def pave_img(Img, hash2, grate=False):
    """Flagstones: 16x8 slabs in a running bond, lit from the top-left."""
    img = Img(16, 16)
    for y in range(16):
        for x in range(16):
            off = 8 if (y // 8) % 2 else 0
            lx, ly = (x + off) % 16, y % 8
            if ly == 7 or lx == 15:
                c = 'pv_base'
            elif ly == 0 or lx == 0:
                c = 'pv_hi'
            else:
                c = 'pv_lt'
                h = hash2(x, y, 11) & 63
                if h < 3:
                    c = 'pv_base'
                elif h == 63:
                    c = 'pv_hi'
            if ly == 7 and lx == 15:
                c = 'pv_dk'
            img.p[y][x] = c
    if grate:
        for y in range(4, 12):
            for x in range(3, 13):
                if y in (4, 11) or x in (3, 12):
                    c = 'cb_out'
                elif y % 2 == 1:
                    c = 'cb_dk'
                else:
                    c = 'cb_out'
                img.p[y][x] = c
        for x in range(4, 13):
            img.p[12][x] = 'pv_hi'
    return img


def cobble_img(Img, hash2):
    """Rounded setts in offset rows, blue-grey."""
    img = Img(16, 16, 'cb_out')
    for row in range(4):
        y0 = row * 4
        off = 2 if row % 2 else 0
        for k in range(4):
            x0 = (k * 4 + off) % 16
            for dy in range(3):
                for dx in range(3):
                    x = (x0 + dx) % 16
                    y = y0 + dy
                    c = 'cb_base'
                    if dy == 0 and dx < 2:
                        c = 'cb_lt'
                    if dy == 0 and dx == 0:
                        c = 'cb_hi' if (hash2(k, row, 3) & 1) else 'cb_lt'
                    if dy == 2 or dx == 2:
                        c = 'cb_dk'
                    img.p[y][x] = c
    return img


def plaza_img(Img):
    """Sandstone herringbone (bank 0 sand colours)."""
    img = Img(16, 16)
    for y in range(16):
        for x in range(16):
            # herringbone of 2x6 bricks rotated by 90 degrees in a 8x8 period
            u = (x + y) % 8
            v = (x - y) % 8
            if ((x // 4) + (y // 4)) % 2 == 0:
                c = 's_base' if (y % 4) else 's_mid'
                if x % 4 == 0 and y % 4:
                    c = 's_hi'
            else:
                c = 's_base' if (x % 4) else 's_mid'
                if y % 4 == 0 and x % 4:
                    c = 's_hi'
            img.p[y][x] = c
            del u, v
    for y in range(16):
        for x in range(16):
            if (x % 4 == 3 and ((x // 4) + (y // 4)) % 2 == 0) or \
               (y % 4 == 3 and ((x // 4) + (y // 4)) % 2 == 1):
                img.p[y][x] = 's_dk'
    return img


def wall_top_img(Img, hash2):
    """The old city wall seen from above: dressed coping stones."""
    img = Img(16, 16)
    for y in range(16):
        for x in range(16):
            lx = (x + (8 if y >= 8 else 0)) % 16
            if y in (7, 15) or lx == 15:
                c = 'cb_out'
            elif y in (0, 8) or lx == 0:
                c = 'pv_hi'
            else:
                c = 'pv_lt' if (hash2(x, y, 5) & 7) else 'pv_base'
            img.p[y][x] = c
    return img


def wall_face_img(Img, hash2):
    """The wall's face: big weathered blocks, darker toward the base."""
    img = Img(16, 16)
    for y in range(16):
        for x in range(16):
            row = y // 5
            lx = (x + (8 if row % 2 else 0)) % 16
            ly = y % 5
            if ly == 4 or lx == 15:
                c = 'cb_out'
            elif ly == 0 or lx == 0:
                c = 'pv_base'
            else:
                c = 'pv_dk' if y < 12 else 'cb_dk'
                if (hash2(x, y, 9) & 15) == 0:
                    c = 'cb_base'
            img.p[y][x] = c
    for x in range(16):
        img.p[15][x] = 'cb_out'
    return img


# ---------------------------------------------------------------------------
# autotiles: kerbed streets and the stone-rimmed canal
# ---------------------------------------------------------------------------

def street_quads(gf, Img, hash2):
    cob = cobble_img(Img, hash2)
    pave = pave_img(Img, hash2)

    def color_at(d, X, Y, c, v, lx, ly):
        if d < -1.0:
            return pave.p[Y][X]
        if d < 0.0:
            return 'pv_hi'          # kerb top
        if d < 1.0:
            return 'cb_out'         # kerb face in shadow
        if d < 2.0:
            return 'cb_dk'          # gutter
        return cob.p[Y][X]
    return gf.autotile(color_at, E=2.0, R=4.0, Rn=2.0)


def canal_quads(gf, Img, hash2, f):
    surf = gf.water_surface(f)
    pave = pave_img(Img, hash2)

    def color_at(d, X, Y, c, v, lx, ly):
        if d < 0.0:
            return pave.p[Y][X]
        if d < 1.0:
            return 'pv_hi'          # rim coping
        if d < 2.0:
            return 'pv_dk'
        if d < 3.0:
            return 'cb_out'         # the drop to the water
        if d < 4.0:
            return 'w_dk'
        if d < 5.0:
            return 'w_mid'
        return surf.p[Y][X]
    return gf.autotile(color_at, E=0.0, R=5.0, Rn=2.0)


def add_canal_anim(gf, ts, out, Img, hash2, bank=1):
    """Like gen_field_gfx.add_water_anim, with the canal's stone rim."""
    wq = [canal_quads(gf, Img, hash2, f) for f in range(3)]
    water_q = [[0] * 5 for _ in range(4)]
    water_anim = [[], [], []]
    first = len(ts.tiles)
    seen = {}
    for c in range(4):
        for v in range(5):
            frames = tuple(ts.indices(gf.img_pix(wq[f][c][v]), bank) for f in range(3))
            if frames not in seen:
                seen[frames] = ts.add_raw(frames[0])
                for f in range(3):
                    water_anim[f].append(frames[f])
            water_q[c][v] = seen[frames] | (bank << 12)
    out['water_first'] = first
    out['water_anim'] = water_anim
    out['water_q'] = water_q


# ---------------------------------------------------------------------------
# modular buildings
# ---------------------------------------------------------------------------

ROOFS = {
    'red': ['rf_hi', 'rf_lt', 'rf_base', 'rf_dk', 'rf_dkr'],
    'teal': ['rt_hi', 'rt_lt', 'rt_base', 'rt_dk', 'rt_dkr'],
    'slate': ['cb_hi', 'cb_lt', 'cb_base', 'cb_dk', 'cb_out'],
}
ROOF_OUT = {'red': 'b_out', 'teal': 'b_out', 'slate': 'cb_out'}

# wall materials: fill, light, shadow, joint
WALLS = {
    'plaster': dict(base='wl_base', hi='wl_hi', dk='wl_dk', joint='wl_dk'),
    'brick': dict(base='br_base', hi='br_hi', dk='br_dk', joint='br_dk'),
    'stone': dict(base='st_lt', hi='st_hi', dk='st_mid', joint='st_mid'),
}


def roof_texture(roof, R, x, y):
    """Interior roof pixel (period 8 in x, 8 in y, so cells share tiles)."""
    if roof == 'teal':
        # copper standing-seam roof: vertical seams, faint horizontal laps
        k = x % 8
        if k == 0:
            return R[0]
        if k == 1:
            return R[1]
        if k == 7:
            return R[3]
        return R[3] if y % 8 == 7 and k in (3, 4) else R[2]
    if roof == 'slate':
        # small rectangular slates, offset every course of 4 px
        course, r = y // 4, y % 4
        if r == 3:
            return R[4]
        if (x + 4 * (course % 2)) % 8 == 7:
            return R[3]
        return R[1] if r == 0 else R[2]
    # terracotta: rounded pan tiles in courses
    course, r = y // 4, y % 4
    if r == 0:
        return R[1]
    if r == 3:
        return R[3]
    u = (x + 4 * (course % 2)) % 8
    if u == 0:
        return R[3]
    if u == 1 and r == 1:
        return R[0]
    return R[2]


def paint_roof(img, x0, y0, wc, rows, roof):
    R = ROOFS[roof]
    O = ROOF_OUT[roof]
    W, H = wc * 16, rows * 16
    for y in range(H):
        for x in range(W):
            if y == 0 or x == 0 or x == W - 1:
                c = O
            elif y == 1:
                c = R[0] if x % 2 else R[1]     # ridge cap
            elif y == 2:
                c = R[3]
            elif y >= H - 4:
                c = [R[3], R[4], O, R[1]][y - (H - 4)]
                if y == H - 1:
                    c = R[1] if x % 8 else R[3]  # fascia board with brackets
            else:
                c = roof_texture(roof, R, x, y)
                if x == 1:
                    c = R[0] if c != R[4] else R[1]
                elif x == W - 2:
                    c = R[4] if c in (R[3], R[4]) else R[3]
            img.set(x0 + x, y0 + y, c)


def wall_texture(mat, x, y):
    M = WALLS[mat]
    if mat == 'brick':
        course = y // 4
        if y % 4 == 3:
            return 'br_dk'
        if (x + (4 if course % 2 else 0)) % 8 == 7:
            return 'br_dk'
        return 'br_hi' if y % 4 == 0 else 'br_base'
    if mat == 'stone':
        course = y // 8
        if y % 8 == 7:
            return 'st_mid'
        if (x + (8 if course % 2 else 0)) % 16 == 15:
            return 'st_mid'
        return 'st_hi' if y % 8 == 0 else 'st_lt'
    # plaster: smooth with faint speckles (16-periodic, so cells share tiles)
    k = (x % 16) * 16 + (y % 16)
    if k in (37, 90, 141, 203, 250):
        return 'wl_dk'
    if k in (12, 71, 118, 180, 229):
        return 'wl_hi'
    return 'wl_base'


def window_art(G, mat, tall):
    """A sash window 10 px wide; tall=True for the upper storey."""
    frame = 'st_hi'
    fr_dk = 'st_mid'
    leg = {'.': None, 'O': 'b_out', 'H': frame, 'L': fr_dk, 'a': 'gl_hi', 'b': 'gl_base',
           'c': 'gl_dk', 'S': 'st_lt', 's': 'st_mid'}
    if tall:
        return G('''
        OOOOOOOOOOOO
        OHHHHHHHHHHO
        OHccccOcccLO
        OHabbbOabbLO
        OHbabbObabLO
        OHbbbbObbbLO
        OHOOOOOOOOLO
        OHcbbbOcbbLO
        OHbabbObabLO
        OHbbabObbaLO
        OLLLLLLLLLLO
        SSSSSSSSSSSS
        ssssssssssss
        ''', leg)
    return G('''
    OOOOOOOOOOOO
    OHHHHHHHHHHO
    OHccccOcccLO
    OHabbbOabbLO
    OHbabbObabLO
    OHbbabObbaLO
    OLLLLLLLLLLO
    SSSSSSSSSSSS
    ssssssssssss
    ''', leg)


def door_art(G, kind):
    leg = {'.': None, 'O': 'b_out', 'A': 'wd_lt', 'B': 'wd_base', 'K': 'wd_dk',
           'H': 'st_hi', 'L': 'st_lt', 'M': 'st_mid', 'a': 'gl_hi', 'b': 'gl_base',
           'c': 'gl_dk', 'y': 'p_yel'}
    if kind == 'glass':
        return G('''
        OOOOOOOOOOOOOO
        OHHHHHHHHHHHHO
        OHOOOOOOOOOOLO
        OHOaabcOabbcOLO
        OHOabbcObbbcOLO
        OHObbbcObabcOLO
        OHObbacOabbcOLO
        OHObabcObbacOLO
        OHOabbcObabcOLO
        OHObbbcObbbcOLO
        OHObbbcObbbcOLO
        OHOabbcOabbcOLO
        OHObbacObbbcOLO
        OHObbbcObbacOLO
        OHObbbcObbbcOLO
        OHOccccOccccOLO
        OHLLLLLLLLLLLLO
        OMMMMMMMMMMMMMO
        ''', leg)
    return G('''
    OOOOOOOOOOOO
    OAAAAAAAAAAO
    OAOOOOOOOOKO
    OAOBBBBBBOKO
    OAOBKKKKBOKO
    OAOBKaabBOKO
    OAOBKabbBOKO
    OAOBKKKKBOKO
    OAOBBBBBBOKO
    OAOBBBByBOKO
    OAOBBBBBBOKO
    OAOBKKKKBOKO
    OAOBKBBABOKO
    OAOBKBBABOKO
    OAOBKAAABOKO
    OAOBBBBBBOKO
    OAOKKKKKKOKO
    OOOOOOOOOOOO
    ''', leg)


def paint_walls(G, img, x0, y0, wc, rows, mat, fronts):
    """rows = storeys of 16 px. fronts: per storey a string of wc codes:
    '.' plain, 'w' window, 'd' wooden door, 'g' glass door, 's' shop window,
    'a' awning (over a shop window below)."""
    M = WALLS[mat]
    W, H = wc * 16, rows * 16
    for y in range(H):
        for x in range(W):
            c = wall_texture(mat, x, y)
            if y == 0:
                c = M['dk']
            elif y == 1 and x % 2 == 0:
                c = M['dk']
            if x == 0 or x == W - 1:
                c = 'b_out'
            elif x == 1:
                c = M['hi'] if y > 1 else c
            elif x == W - 2:
                c = M['dk']
            img.set(x0 + x, y0 + y, c)
    # foundation course along the bottom
    for x in range(W):
        img.set(x0 + x, y0 + H - 4, 'b_out')
        img.set(x0 + x, y0 + H - 3, 'st_hi' if x % 8 else 'st_mid')
        img.set(x0 + x, y0 + H - 2, 'st_mid' if (x + 4) % 8 else 'st_dk')
        img.set(x0 + x, y0 + H - 1, 'b_out')
    for r, front in enumerate(fronts):
        assert len(front) == wc, front
        last = r == rows - 1
        for i, code in enumerate(front):
            cx, cy = x0 + i * 16, y0 + r * 16
            if code == 'w':
                win = window_art(G, mat, tall=not last)
                img.paste(win, cx + 2, cy + (2 if not last else 1))
            elif code in ('d', 'g'):
                door = door_art(G, 'glass' if code == 'g' else 'wood')
                # the door stands on the ground line; its top reaches up into
                # the storey above
                dy = y0 + H - door.h - 1
                img.paste(door, cx + (16 - door.w) // 2, dy)
                for x in range(cx + 1, cx + 15):
                    img.set(x, y0 + H - 1, 'b_out')
            elif code == 's':
                shop_window(img, cx, cy, last)
            elif code == 'a':
                awning(img, cx, cy + 8)
            elif code == 'c':
                column(img, cx, cy, top=r == 0, bottom=last)
    return img


def column(img, cx, cy, top, bottom):
    """A fluted stone column filling one storey of a cell (portico)."""
    for y in range(16):
        for x in range(2, 14):
            if x in (2, 13):
                c = 'b_out'
            elif x == 3:
                c = 'st_hi'
            elif x == 12:
                c = 'st_dk'
            else:
                c = 'st_lt' if (x - 4) % 3 else 'st_mid'
                if x in (4, 5):
                    c = 'st_hi' if x == 4 else c
            img.set(cx + x, cy + y, c)
    if top:
        for y in range(0, 5):
            for x in range(1, 15):
                c = 'b_out' if y in (0, 4) or x in (1, 14) else ('st_hi' if y == 1 else 'st_lt')
                if y == 3 and x not in (1, 14):
                    c = 'st_mid'
                img.set(cx + x, cy + y, c)
    if bottom:
        for y in range(8, 12):
            for x in range(1, 15):
                c = 'b_out' if y in (8, 11) or x in (1, 14) else ('st_hi' if y == 9 else 'st_mid')
                img.set(cx + x, cy + y, c)


def shop_window(img, cx, cy, last):
    y1 = cy + (11 if last else 15)
    for y in range(cy + 1, y1 + 1):
        for x in range(cx, cx + 16):
            if y in (cy + 1, y1) or x in (cx, cx + 15):
                c = 'b_out'
            elif y == cy + 2 or x == cx + 1:
                c = 'st_hi'
            elif x == cx + 14:
                c = 'st_mid'
            else:
                t = (x - cx) + (y - cy)
                c = 'gl_hi' if t % 9 in (3, 4) and y < cy + 7 else 'gl_base'
                if y == cy + 3:
                    c = 'gl_dk'
                if y >= y1 - 3:
                    c = 'wd_base' if y == y1 - 3 else 'wd_dk'
                    if y == y1 - 4:
                        c = 'wd_lt'
                # goods on the display shelf
                if y in (y1 - 5, y1 - 4) and (x - cx) % 4 in (1, 2) and 2 < x - cx < 14:
                    c = 'p_yel' if (x - cx) % 8 < 4 else 'wd_lt'
            img.set(x, y, c)


def awning(img, cx, cy):
    """Striped awning, 8 px tall, fully covering its tile row."""
    for y in range(8):
        for x in range(16):
            stripe = (x // 4) % 2 == 0
            if y == 0 or y == 7:
                c = 'b_out'
            elif y == 6:
                c = 'rf_dkr' if stripe else 'wl_dk'
            elif y == 1:
                c = 'rf_hi' if stripe else 'wl_hi'
            else:
                c = 'rf_base' if stripe else 'wl_hi'
                if y == 5:
                    c = 'rf_dk' if stripe else 'wl_base'
            img.set(cx + x, cy + y, c)


# 4x5 sign font (every capital letter, digits we need, a few marks)
FONT = {
    'A': ['.##.', '#..#', '####', '#..#', '#..#'], 'B': ['###.', '#..#', '###.', '#..#', '###.'],
    'C': ['.###', '#...', '#...', '#...', '.###'], 'D': ['###.', '#..#', '#..#', '#..#', '###.'],
    'E': ['####', '#...', '###.', '#...', '####'], 'F': ['####', '#...', '###.', '#...', '#...'],
    'G': ['.###', '#...', '#.##', '#..#', '.###'], 'H': ['#..#', '#..#', '####', '#..#', '#..#'],
    'I': ['###.', '.#..', '.#..', '.#..', '###.'], 'J': ['..##', '...#', '...#', '#..#', '.##.'],
    'K': ['#..#', '#.#.', '##..', '#.#.', '#..#'], 'L': ['#...', '#...', '#...', '#...', '####'],
    'M': ['#...#', '##.##', '#.#.#', '#...#', '#...#'], 'N': ['#..#', '##.#', '#.##', '#..#', '#..#'],
    'O': ['.##.', '#..#', '#..#', '#..#', '.##.'], 'P': ['###.', '#..#', '###.', '#...', '#...'],
    'Q': ['.##.', '#..#', '#..#', '#.#.', '.#.#'], 'R': ['###.', '#..#', '###.', '#.#.', '#..#'],
    'S': ['.###', '#...', '.##.', '...#', '###.'], 'T': ['####', '.#..', '.#..', '.#..', '.#..'],
    'U': ['#..#', '#..#', '#..#', '#..#', '.##.'], 'V': ['#..#', '#..#', '#..#', '.##.', '.#..'],
    'W': ['#...#', '#...#', '#.#.#', '##.##', '#...#'], 'X': ['#..#', '.##.', '.##.', '.##.', '#..#'],
    'Y': ['#..#', '#..#', '.###', '...#', '###.'], 'Z': ['####', '..#.', '.#..', '#...', '####'],
    ' ': ['..', '..', '..', '..', '..'],
}


def sign_plate(Img, text, plate='st_hi', ink='b_out', edge='st_mid', out='b_out'):
    """An 8 px tall name plate (paste it at a y that is a multiple of 8 so
    it costs a single row of tiles). The font is variable width."""
    w = sum(len(FONT[ch][0]) + 1 for ch in text) - 1 + 5
    img = Img(w, 8)
    for y in range(8):
        for x in range(w):
            if y in (0, 7) or x in (0, w - 1):
                c = out
            elif y == 6 or x == w - 2:
                c = edge
            else:
                c = plate
            img.p[y][x] = c
    x0 = 2
    for ch in text:
        for yy, row in enumerate(FONT[ch]):
            for xx, px in enumerate(row):
                if px == '#':
                    img.p[1 + yy][x0 + xx] = ink
        x0 += len(FONT[ch][0]) + 1
    return img


def make_building(gf, wc, roof, nroof, mat, fronts):
    Img, G = gf.Img, gf.G
    img = Img(wc * 16, (nroof + len(fronts)) * 16)
    paint_roof(img, 0, 0, wc, nroof, roof)
    paint_walls(G, img, 0, nroof * 16, wc, len(fronts), mat, fronts)
    return img


# ---------------------------------------------------------------------------
# emblems (painted over roofs)
# ---------------------------------------------------------------------------

def flame_emblem(G):
    """The Hearth Hall flame on a stone roundel (red roof bank)."""
    return G('''
    ....OOOOOOOO....
    ..OOhhhhhhhhOO..
    .OhhhhhOhhhhhmO.
    .OhhhhOlOhhhhmO.
    Ohhhhh0llOhhhhmO
    OhhhhOll2OhhhhmO
    OhhhOl2l22OOhhmO
    OhhOll2112lOOhmO
    OhhOl21112l2OhmO
    OhhOl22112l2OhmO
    OhhhOll22llOhhmO
    .OhhhOOllOOhhmO.
    .OhhhhhOOhhhhmO.
    ..OOmmmmmmmmOO..
    ....OOOOOOOO....
    ''', {'.': None, 'O': 'b_out', 'h': 'st_hi', 'm': 'st_mid', 'l': 'rf_hi', '2': 'rf_lt',
          '1': 'wl_hi', '0': 'rf_base'})


def bolt_emblem(G):
    """The VOLT HALL lightning bolt on a copper roundel (teal bank)."""
    return G('''
    ......OOOOOOOO......
    ....OOoooooooOOO....
    ...OooooooOOoooOO...
    ..OooooooOyyOooooO..
    .OoooooooOyyOoooooO.
    .OooooooOyyOooooookO
    OooooooOyyOoooooookO
    OoooooOyyyOOOOooookO
    OooooOyyyyyyyyOoookO
    OoooOOOOOyyyyOooookO
    OoooooookOyyOoooookO
    OooooookOyyOooooookO
    .OoooooOyyOoooooookO
    .OoooooOyOoooooookO.
    ..OooooOOoooooookO..
    ...OOkkkkkkkkkkOO...
    .....OOOOOOOOOO.....
    ''', {'.': None, 'O': 'b_out', 'o': 'fx_org', 'k': 'wd_dk', 'y': 'p_yel'})


def gear_emblem(G):
    """A steel gear with a glowing core for the RESONANCE WORKS (slate bank)."""
    return G('''
    .....OO.OO.....
    ....OyyOyyO....
    ..OOOyyyyyOOO..
    .OyyyyyyyyyyyO.
    .OyyyOOOOOyyyO.
    OOyyOsgggsOyyOO
    OyyyOgsssgOyyyO
    .OyyOgsOsgOyyO.
    OyyyOgsssgOyyyO
    OOyyOsgggsOyyOO
    .OyyyOOOOOyyyO.
    .OyyyyyyyyyyyO.
    ..OOOyyyyyOOO..
    ....OyyOyyO....
    .....OO.OO.....
    ''', {'.': None, 'O': 'cb_out', 'y': 'pv_lt', 's': 'w_base', 'g': 'w_hi'})


def clock_face(G):
    """A 24 px clock face in a stone ring (the hands point to ten past ten)."""
    return G('''
    ........OOOOOOOO........
    ......OOmmmmmmmmOO......
    .....OmmhhhhhhhhmmO.....
    ....OmhhhhhhOhhhhhmO....
    ...OmhhOhhhhOhhhhOhmO...
    ..OmhhhhhhhhOhhhhhhhmO..
    ..OmhhhhhhhhOhhhhhhhmO..
    .OmhhhhhhhhhOhhhhhhhhmO.
    .OmhhhhOhhhhOhhhhhhhhmO.
    OmhhhhhhOOhhOhhhhhhhhhmO
    OmhOhhhhhhOOOhhhhhhOhhmO
    OmhhhhhhhhhOOOOOOhhhhhmO
    OmhhhhhhhhhhhhhhhhhhhhmO
    OmhhhhhhhhhhhhhhhhhhhhmO
    OmhhhhhhhhhhhhhhhhhhhhmO
    .OmhhhhhhhhhhhhhhhhhhmO.
    .OmhhhhhhhhhhhhhhhhhhmO.
    ..OmhhhhhhhhhhhhhhhhmO..
    ..OmhhOhhhhhhhhhhOhhmO..
    ...OmhhhhhhhhhhhhhhmO...
    ....OmhhhhhhOhhhhhmO....
    .....OmmhhhhhhhhmmO.....
    ......OOmmmmmmmmOO......
    ........OOOOOOOO........
    ''', {'.': None, 'O': 'b_out', 'h': 'st_hi', 'm': 'st_mid'})


# ---------------------------------------------------------------------------
# the buildings of Lumen City
# ---------------------------------------------------------------------------

def centered_sign(img, Img, text, y, **kw):
    sg = sign_plate(Img, text, **kw)
    img.paste(sg, (img.w - sg.w) // 2, y)


def city_stamps(gf):
    Img, G = gf.Img, gf.G
    S = []

    # HEARTH HALL: dressed stone, terracotta roof, flame roundel, glass doors
    im = make_building(gf, 6, 'red', 2, 'stone', ['ww..ww', 'ww.gww'])
    im.paste(flame_emblem(G), 40, 8)
    centered_sign(im, Img, 'HEARTH HALL', 32, plate='wl_hi', ink='rf_dk', edge='wl_dk')
    S.append(('HEARTH', im, (7, 4), 'HEARTH HALL (6x4), door col 3 row 3'))

    # LUMEN MARKET: brick, terracotta roof, striped awnings over shop windows
    im = make_building(gf, 8, 'red', 2, 'brick', ['aaa..aaa', 'sss.gsss'])
    centered_sign(im, Img, 'LUMEN MARKET', 32, plate='st_hi', ink='br_dk', edge='st_mid')
    S.append(('MARKET', im, (6, 4), 'LUMEN MARKET (8x4), door col 4 row 3'))

    # VOLT HALL: dressed stone, copper roof, lightning roundel, portico columns
    im = make_building(gf, 9, 'teal', 3, 'stone', ['w.wc.cw.w', 'wwwcgcwww'])
    im.paste(bolt_emblem(G), 62, 12)
    centered_sign(im, Img, 'VOLT HALL', 48, plate='st_hi', ink='gl_dk', edge='st_mid')
    S.append(('VOLT_HALL', im, (7, 5), 'VOLT HALL (9x5), door col 4 row 4'))

    # RESONANCE WORKS: brick, slate roof, steel gear
    im = make_building(gf, 8, 'slate', 2, 'brick', ['w......w', 'ww.gwwww'])
    im.paste(gear_emblem(G), 88, 8)
    centered_sign(im, Img, 'RESONANCE WORKS', 32, plate='st_hi', ink='br_dk', edge='st_mid')
    S.append(('WORKS', im, (6, 1), 'RESONANCE WORKS (8x4), door col 3 row 3'))

    # BIKE SHOP: plaster, copper roof, shop windows
    im = make_building(gf, 5, 'teal', 2, 'plaster', ['aa..w', 'ss.dw'])
    centered_sign(im, Img, 'BIKES', 32, plate='wl_hi', ink='gl_dk', edge='wl_dk')
    S.append(('BIKE_SHOP', im, (7, 5), 'BIKE SHOP (5x4), door col 3 row 3'))

    # COPPER KETTLE INN: brick, terracotta roof
    im = make_building(gf, 6, 'red', 2, 'brick', ['w....w', 'ww.dww'])
    centered_sign(im, Img, 'KETTLE INN', 32, plate='st_hi', ink='br_dk', edge='st_mid')
    S.append(('INN', im, (6, 4), 'COPPER KETTLE INN (6x4), door col 3 row 3'))

    # houses
    S.append(('HOUSE_A', make_building(gf, 5, 'red', 2, 'plaster', ['w.w.w', 'w.dww']), (7, 4),
              'townhouse, plaster + terracotta (5x4), door col 2 row 3'))
    S.append(('HOUSE_B', make_building(gf, 5, 'teal', 2, 'brick', ['w.w.w', 'wwd.w']), (6, 5),
              'townhouse, brick + copper (5x4), door col 2 row 3'))
    S.append(('HOUSE_C', make_building(gf, 4, 'slate', 2, 'plaster', ['w..w', 'wd.w']), (7, 1),
              'narrow townhouse, plaster + slate (4x4), door col 1 row 3'))
    S.append(('ROW_HOUSES', make_building(gf, 7, 'slate', 2, 'brick',
                                          ['www.www', 'wdw.wdw']), (6, 1),
              'terrace of two brick houses (7x4), doors col 1 and 5 row 3 (locked)'))

    # CLOCK TOWER (the foot of the CLOCKWORK SPIRE): stone, clock face, door
    im = make_building(gf, 3, 'teal', 1, 'stone', ['...', '...', '...', '...', '.g.'])
    im.paste(clock_face(G), 12, 18)
    centered_sign(im, Img, 'SPIRE', 72, plate='st_hi', ink='gl_dk', edge='st_mid')
    S.append(('CLOCK_TOWER', im, (7, 5), 'clock tower (3x6), door col 1 row 5 (CLOCKWORK SPIRE)'))
    return S


DOORS = [('HEARTH', 3, 3), ('MARKET', 4, 3), ('VOLT_HALL', 4, 4), ('WORKS', 3, 3),
         ('BIKE_SHOP', 3, 3), ('INN', 3, 3), ('HOUSE_A', 2, 3), ('HOUSE_B', 2, 3),
         ('HOUSE_C', 1, 3), ('ROW_HOUSES', 1, 3), ('ROW_HOUSES', 5, 3), ('CLOCK_TOWER', 1, 5)]


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def build(gf, name):
    from pixelart import Img, hash2
    gf.register_colors(CITY_COLORS)
    bk = banks(gf)
    gf.check_banks(name, bk)
    ts = gf.TileSet(name, bk)
    out = {'ts': ts, 'meta_b': [], 'meta_t': [], 'terrain': TERRAIN}
    add_canal_anim(gf, ts, out, Img, hash2)
    flower_meta = gf.add_flower_anim(ts, out)
    tall_b, tall_t = gf.tallgrass_layers()
    tree = gf.tree_img(overlay=True)
    imgs = {
        'PAVE': (pave_img(Img, hash2), 1), 'PAVE2': (pave_img(Img, hash2, grate=True), 1),
        'COBBLE': (cobble_img(Img, hash2), 1), 'PLAZA': (plaza_img(Img), 0),
        'GRASS': (gf.GRASS_A, 0), 'GRASS2': (gf.GRASS_B, 0), 'GRASS3': (gf.GRASS_C, 0),
        'TALLGRASS': (tall_b, 0), 'WALL_TOP': (wall_top_img(Img, hash2), 1),
        'WALL': (wall_face_img(Img, hash2), 1),
    }
    for tname in TERRAIN:
        if tname == 'FLOWER_RED':
            out['meta_b'].append(flower_meta[0])
        elif tname == 'FLOWER_YELLOW':
            out['meta_b'].append(flower_meta[1])
        elif tname in ('TREE_TOP', 'TREE_BOTTOM'):
            crop = tree.crop(0, 0 if tname == 'TREE_TOP' else 16, 16, 16)
            gf.add_overlay_terrain(ts, out, tname, crop, top=tname == 'TREE_TOP')
            continue
        else:
            im, bank = imgs[tname]
            out['meta_b'].append(ts.meta(im, prefer=(bank,), where='city.' + tname))
        if tname == 'TALLGRASS':
            out['meta_t'].append(ts.meta(tall_t, prefer=(0,), where='city.TALLGRASS.top',
                                         opaque=False))
        else:
            out['meta_t'].append([0, 0, 0, 0])
    stamps = city_stamps(gf)
    gf.add_stamps(ts, out, [(n, im, pref, doc) for (n, im, pref, doc) in stamps])
    sq = street_quads(gf, Img, hash2)
    out['path_q'] = [[ts.add(gf.img_pix(sq[c][v]), (1,), 'street[%d][%d]' % (c, v))
                      for v in range(5)] for c in range(4)]
    res = gf.finish_tileset(
        out, name, 'CY',
        attrs={'TALLGRASS': gf.A_GRASS, 'WALL_TOP': gf.A_SOLID, 'WALL': gf.A_SOLID},
        ground=['PAVE', 'PAVE2', 'COBBLE', 'PLAZA', 'GRASS', 'GRASS2', 'GRASS3'],
        overlay=['TREE_TOP', 'TREE_BOTTOM'],
        legend={'.': [('PAVE2', 1), ('PAVE', 15)], '=': 'PATH', '~': 'WATER', 'c': 'COBBLE',
                'p': 'PLAZA', 'g': gf.GRASS_VARIANTS, ',': 'TALLGRASS', 'r': 'FLOWER_RED',
                'y': 'FLOWER_YELLOW', 'T': 'TREE_TOP', 't': 'TREE_BOTTOM', '#': 'WALL_TOP',
                'w': 'WALL'},
        oob='WALL_TOP', default_ground='PAVE', backdrop='ground', doors=DOORS)
    res['docs'] = TERRAIN_DOC
    return res
