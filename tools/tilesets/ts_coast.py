"""The 'coast' tileset (W-WEST: Saltwind Trail, Port Brine, the Sea Route,
Gull Isle) and the 'tide' tileset (the Current Hall and the Drowned Bell,
build_tide; tools/tilesets/ts_tide.py registers it).

'coast' holds the outdoor ground (grass, dunes, beach, rock shelves, salt
pans, harbour paving) and the elevation art (cliffs, stairs and bridges are
the maps' height layers, docs/ELEVATION.md); 'tide' holds the CURRENT HALL's
floor, walls and flowing channels and the DROWNED BELL's glowing grotto.
They were one tileset until the elevation art pushed it to 478 tiles, which
left Port Brine 34 tiles for its props (the rest were skipped and drawn as
garbage). Both share the palette banks, so the west props fit either.
Buildings are stamps; props live in tools/decor_west.py. The CAVE stamp is a
1x1 door cell to put on a TUNNEL mouth (Gull Isle's sea cave).

Palette banks (8 x 15 colours):

  0 ground   grass, tall grass, marram dunes, flowers, paths, grass ledges
  1 sea      water autotile (sand shore, foam), sand, shelf rock, tide
             pools, salt pans, plaza slabs, the Hall's currents and pools
  2 green    pines, palms
  3 props    the village decor bank (reused props), thatch, lighthouse
  4 red roof roof_bank(ROOF_RED): Hearth Hall, Harbor Office, houses
  5 blue roof roof_bank(ROOF_BLUE): shop, inn, Current Hall, houses
  6 walls    BANK_WALLS: walls, windows, doors; the Hall floor and walls
  7 grotto   blue-black rock, bioluminescent cyan, verdigris and bronze

Map legend (documented again in src/game/world/west/data.h):

  outdoor  . grass   , tall grass (kin)   ; marram dune grass (kin)
           s sand    = path   ~ sea (surfable, autotiled sand shore)
           # plaza slabs   q quay setts   k rock shelf   o tide pool
           % salt pan   l dune ledge (sand, hop south)
           r y flowers   P/p pine top/bottom   A/a palm top/bottom
  ('tide') the Hall and the grotto:
  hall     H wall top   h wall   n porthole   _ floor   M exit mat
           v ^ < > currents (A_CURRENT, see below)   O still pool (deep)
  grotto   G rock top   g rock wall   : wet floor   ' glowing floor
           t temple slabs   * glowing pool (deep)   m exit steps

CURRENTS (A_CURRENT + A_DIR_HI/A_DIR_LO): the direction is
(DIR_HI << 1 | DIR_LO) = 0 down, 1 up, 2 left, 3 right, the same order as
field.c's DIR_DOWN/UP/LEFT/RIGHT. Current cells are walkable water; a
player who steps onto one is carried one cell per step in the direction of
the cell they stand on, until they reach a cell that is not a current (or
the way ahead is blocked). tools/tests/test_west.c simulates exactly this.
"""

import math
from pixelart import Img, G, tex_fill, hash2, shade_clumps

USES_DECOR = [
    'SIGNPOST', 'BARREL', 'CRATE', 'CRATE_STACK', 'SACKS', 'ROCK', 'BENCH', 'LANTERN_POST',
    'CAMPFIRE', 'FENCE', 'FENCE_END', 'BUSH', 'BOULDER', 'PEBBLES', 'SMALL_FLOWERS',
    'NOTICE_BOARD', 'SHRINE', 'SIGN_ARROW', 'WOODPILE', 'STUMP', 'LOG', 'WEATHER_VANE',
    'MARKET_STALL', 'MAILBOX', 'FLOWER_POT', 'PLANTER', 'WATER_TROUGH', 'PICNIC_TABLE',
    'CLOTHESLINE', 'BRIDGE_H', 'BRIDGE_V', 'ROWBOAT',
]

COAST_COLORS = {
    'sw_lt': (216, 196, 148),    # wet sand at the tide line
    'sw_dk': (180, 160, 116),
    # the Drowned Bell grotto (bank 7)
    'gb_blk': (10, 14, 30),
    'gb_dk': (22, 30, 56),
    'gb_mid': (38, 50, 86),
    'gb_lt': (60, 78, 120),
    'gb_hi': (92, 114, 160),
    'bio_hi': (208, 255, 246),
    'bio_base': (96, 232, 214),
    'bio_dk': (36, 148, 158),
    'vg_hi': (150, 212, 182),
    'vg_base': (76, 160, 138),
    'vg_dk': (38, 98, 98),
    'bz_hi': (224, 176, 96),
    'bz_base': (164, 106, 56),
    'dw_base': (18, 42, 76),
}

TERRAIN = [
    # outdoor ground
    'GRASS', 'GRASS2', 'GRASS3', 'TALLGRASS', 'DUNEGRASS', 'FLOWER_RED', 'FLOWER_YELLOW',
    'SAND', 'SAND2', 'SAND3', 'STONE', 'QUAY', 'SHELF', 'TIDEPOOL', 'SALTPAN',
    'DUNE_LEDGE',
    'PINE_TOP', 'PINE_BOTTOM', 'PALM_TOP', 'PALM_BOTTOM',
    # the Current Hall
    'HALL_FLOOR', 'HALL_WALL_TOP', 'HALL_WALL', 'HALL_PORTHOLE', 'HALL_MAT', 'HALL_POOL',
    'CUR_DOWN', 'CUR_UP', 'CUR_LEFT', 'CUR_RIGHT',
    # the Drowned Bell
    'GROT_TOP', 'GROT_WALL', 'GROT_FLOOR', 'GROT_GLOW', 'TEMPLE', 'GLOW_POOL', 'GROT_MAT',
    'VOID',
]

TERRAIN_DOC = {
    'TALLGRASS': 'coastal tall grass; wild kin roam here; top layer hides legs',
    'DUNEGRASS': 'marram grass on sand; wild kin roam here; front blades over legs',
    'SAND': 'beach sand (+ SAND2 shells, SAND3 wrack line)',
    'STONE': 'pale plaza slabs (town square)',
    'QUAY': 'granite harbour setts (quays, streets)',
    'SHELF': 'wave-cut rock shelf (walkable)',
    'TIDEPOOL': 'rock pool in the shelf (solid)',
    'SALTPAN': 'shallow salt pan with a clay rim; tiles as a grid (solid)',
    'DUNE_LEDGE': 'one-way sand ledge on the dunes (hop south)',
    'PALM_TOP': '16x32 palm: TOP above BOTTOM',
    'HALL_FLOOR': 'Current Hall floor tiles (walkable platforms)',
    'HALL_POOL': 'still deep pool in the Hall (solid, no surf)',
    'CUR_DOWN': 'flowing channel: A_CURRENT, direction down (animated)',
    'GROT_TOP': 'grotto rock ceiling (solid)',
    'GROT_GLOW': 'grotto floor with glowing moss',
    'TEMPLE': 'sunken temple flagstones',
    'GLOW_POOL': 'bioluminescent pool (solid, deep; animated)',
    'VOID': 'black outside the rooms',
}

# ---------------------------------------------------------------- banks

BANK_SEA = ['w_hi', 'w_lt', 'w_base', 'w_mid', 'w_dk', 's_hi', 's_base', 's_mid', 's_dk',
            'sw_lt', 'sw_dk', 'r_hi', 'r_base', 'r_dk', 'white']
BANK_GROTTO = ['gb_blk', 'gb_dk', 'gb_mid', 'gb_lt', 'gb_hi', 'bio_hi', 'bio_base', 'bio_dk',
               'vg_hi', 'vg_base', 'vg_dk', 'bz_hi', 'bz_base', 'dw_base', 'white']


def banks(gf):
    import decor_outdoor
    return [
        gf.BANK_GROUND,
        BANK_SEA,
        gf.BANK_TREES,
        decor_outdoor.TOWN_DECOR_BANK,
        gf.roof_bank(gf.ROOF_RED),
        gf.roof_bank(gf.ROOF_BLUE),
        gf.BANK_WALLS,
        BANK_GROTTO,
    ]


B_GROUND, B_SEA, B_GREEN, B_PROPS, B_RED, B_BLUE, B_WALLS, B_GROTTO = range(8)

# ---------------------------------------------------------------- helpers


def solid(w, h, c):
    return Img(w, h, c)


def sand_tex(seed=0):
    """Beach sand: soft wind ripples and a few grains (s_* only)."""
    img = Img(16, 16, 's_base')
    for (x0, y0, n) in ((1, 2, 5), (9, 5, 6), (3, 9, 4), (10, 12, 5), (0, 14, 3)):
        for i in range(n):
            x = (x0 + i + seed * 5) % 16
            y = y0 + (1 if 0 < i < n - 1 else 0)
            img.p[y % 16][x] = 's_mid'
            if 0 < i < n - 1:
                img.p[(y - 1) % 16][x] = 's_hi' if i % 2 else 's_base'
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 31 + seed) & 255
            if h < 8 and img.p[y][x] == 's_base':
                img.p[y][x] = 's_mid'
            elif h > 250 and img.p[y][x] == 's_base':
                img.p[y][x] = 's_hi'
    return img


SAND_TEX = sand_tex()


def sand2_img():
    """Sand with a cockle shell and a couple of pebbles."""
    img = SAND_TEX.copy()
    shell = G('''
    .hh.
    hwwh
    rhhr
    .rr.
    ''', {'.': None, 'h': 'r_hi', 'w': 'white', 'r': 'r_base'})
    img.paste(shell, 5, 6)
    for (x, y) in ((12, 2), (2, 12), (13, 11)):
        img.p[y][x] = 'r_base'
        img.p[y][x + 1] = 'r_dk'
        img.p[y - 1][x] = 'r_hi'
    return img


def sand3_img():
    """Sand with a strand of dried wrack (the high-tide line)."""
    img = SAND_TEX.copy()
    pts = [(1, 9), (3, 8), (5, 9), (7, 10), (9, 9), (11, 8), (13, 9), (15, 10)]
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        for t in range(0, 9):
            x = int(round(x0 + (x1 - x0) * t / 8.0))
            y = int(round(y0 + (y1 - y0) * t / 8.0))
            img.set(x, y, 's_dk')
            if (x + y) % 3 == 0:
                img.set(x, y - 1, 'sw_dk')
    for (x, y) in ((4, 11), (10, 7), (14, 11)):
        img.set(x, y, 'r_dk')
    img.set(8, 6, 'white')
    img.set(9, 6, 'r_hi')
    return img


def stone_img():
    """terrain_common STONE (pale slabs), recoloured into the sea bank."""
    from terrain_common import STONE
    return STONE.replace({'c_dk': 's_dk'})


def quay_img():
    """Granite setts in running bond: long blocks lit from the top-left."""
    img = Img(16, 16, 'r_base')
    rows = [(0, 0), (4, 6), (8, 3), (12, 9)]   # (y, brick offset)
    for (y0, off) in rows:
        for x in range(16):
            img.p[y0 + 3][x] = 'r_dk'        # joint under the course
        for bx in (off, off + 8):
            bx %= 16
            for y in range(y0, y0 + 3):
                img.p[y][bx] = 'r_dk'         # vertical joint
            # highlight along the top-left of each block
            for x in range(1, 7):
                img.p[y0][(bx + x) % 16] = 'r_hi'
            img.p[y0 + 1][(bx + 1) % 16] = 'r_hi'
            # a darker lower edge
            for x in range(2, 8):
                if img.p[y0 + 2][(bx + x) % 16] == 'r_base' and (x + y0) % 3 == 0:
                    img.p[y0 + 2][(bx + x) % 16] = 'sw_dk'
    for y in range(16):
        for x in range(16):
            if img.p[y][x] == 'r_base' and (hash2(x, y, 77) & 31) == 0:
                img.p[y][x] = 'sw_lt'
    return img


def shelf_img():
    """Wave-cut rock shelf: pale sandstone beds, cracks and barnacle dots."""
    img = Img(16, 16, 'r_base')
    for y in range(16):
        band = (y + (1 if (y // 4) % 2 else 0)) % 5
        for x in range(16):
            if band == 0:
                img.p[y][x] = 'r_hi' if (x + y) % 7 else 'r_base'
            elif band == 4:
                img.p[y][x] = 'r_dk' if (hash2(x, y, 5) & 3) else 'sw_dk'
    # cracks
    for (x, y, n, dx) in ((3, 1, 4, 1), (11, 6, 5, -1), (6, 10, 4, 1)):
        for i in range(n):
            img.set((x + i * dx) % 16, y + i, 's_dk')
    for (x, y) in ((1, 7), (9, 3), (13, 12), (4, 14)):
        img.set(x, y, 'white')
        img.set(x + 1, y, 'r_dk')
    return img


def tidepool_img():
    img = shelf_img()
    cx, cy, rx, ry = 8.0, 8.5, 6.2, 5.2
    for y in range(16):
        for x in range(16):
            d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
            if d <= 1.0:
                if d > 0.72:
                    c = 'r_dk' if y < cy else 'w_lt'
                elif y < cy - ry * 0.35:
                    c = 'w_dk'
                elif d > 0.45 and x > cx:
                    c = 'w_base'
                else:
                    c = 'w_mid'
                img.p[y][x] = c
            elif d <= 1.28 and y > cy:
                img.p[y][x] = 'r_hi'
    # glints and a pebble on the bottom
    for (x, y, c) in ((5, 7, 'w_hi'), (6, 7, 'w_lt'), (10, 10, 'w_lt'), (9, 11, 's_mid'),
                      (10, 11, 's_dk'), (4, 10, 'r_base')):
        img.set(x, y, c)
    return img


def saltpan_img():
    """A square evaporation pan: clay rim, pale brine and salt crust."""
    img = Img(16, 16, 'w_lt')
    for y in range(16):
        for x in range(16):
            if x == 0 or y == 0:
                img.p[y][x] = 'r_hi'
            elif x == 15 or y == 15:
                img.p[y][x] = 'r_dk'
            elif x == 1 or y == 1:
                img.p[y][x] = 's_dk'
            else:
                h = hash2(x, y, 13) & 15
                if (x + 2 * y) % 9 == 0 or h == 0:
                    img.p[y][x] = 'w_hi'
                elif h < 3:
                    img.p[y][x] = 'white'
    # crust creeping in from the corners
    for (x, y) in ((2, 2), (3, 2), (2, 3), (13, 13), (12, 13), (13, 12), (13, 2), (2, 13)):
        img.p[y][x] = 'white'
    for (x, y) in ((4, 2), (2, 4), (11, 13), (13, 11)):
        img.p[y][x] = 'w_hi'
    return img


# ---------------------------------------------------------------- dune grass

def _blade(img, x0, y0, lean, length, ramp, tip):
    """A grass blade from its root (x0, y0) upward, leaning `lean` pixels."""
    pts = []
    for i in range(length):
        t = i / max(1, length - 1)
        x = x0 + lean * (t ** 1.6)
        pts.append((int(round(x)), y0 - i))
    for i, (x, y) in enumerate(pts):
        k = min(len(ramp) - 1, (len(pts) - 1 - i) * len(ramp) // len(pts))
        c = tip if i == len(pts) - 1 else ramp[len(ramp) - 1 - k]
        img.set(x, y, c)
        if i < len(pts) // 3:
            img.set(x + 1, y, ramp[-1])


def dune_tuft(w=8, h=11, seed=0):
    img = Img(w, h)
    ramp = ['g_lt', 'g_base', 'g_mid', 'g_dk']
    blades = [(3, -3, 9), (4, -1, 10), (4, 2, 9), (2, -4, 7), (5, 3, 7), (3, 0, 8)]
    for i, (bx, lean, ln) in enumerate(blades):
        tip = 's_hi' if (i + seed) % 3 else 'g_hi'
        _blade(img, bx, h - 1, lean * 0.8, ln, ramp, tip)
    for x in range(1, 7):
        if img.p[h - 1][x] is None:
            img.p[h - 1][x] = 's_dk' if x % 2 else 's_mid'
    return img


def dunegrass_layers():
    bottom = SAND_TEX.copy()
    back = Img(16, 16)
    for (ox, oy, s) in ((-3, -3, 0), (5, -4, 1), (12, -2, 2)):
        back.paste(dune_tuft(seed=s), ox, oy + 5)
    front = Img(16, 16)
    for (ox, s) in ((0, 1), (8, 2)):
        front.paste(dune_tuft(seed=s), ox, 5)
    bottom.paste(back, 0, 0)
    bottom.paste(front, 0, 0)
    top = Img(16, 16)
    for y in range(9, 16):
        for x in range(16):
            c = front.p[y][x]
            if c is not None and c not in ('s_dk', 's_mid'):
                top.p[y][x] = c
    return bottom, top


# ---------------------------------------------------------------- dune ledge

def dune_ledge_img():
    """Sand plateau with a soft lip and a short sand face (drop south)."""
    img = SAND_TEX.copy()
    for x in range(16):
        img.p[5][x] = 's_hi'
        img.p[6][x] = 's_hi' if x % 5 else 's_base'
        img.p[7][x] = 's_base'
        img.p[8][x] = 's_dk'
        for y in (9, 10, 11):
            img.p[y][x] = 's_mid' if (x + y) % 6 else 's_dk'
        img.p[12][x] = 's_dk'
        img.p[13][x] = 's_mid' if x % 2 else 's_dk'
        img.p[14][x] = SAND_TEX.p[14][x]
    for x in (2, 9, 13):
        img.p[8][x] = 'g_mid'
        img.p[7][x] = 'g_lt'
        img.p[6][x] = 'g_lt'
    return img


# ---------------------------------------------------------------- palm

def palm_img():
    """16x32 palm (transparent ground): a leaning ringed trunk and a crown
    of drooping fronds, lit from the top-left, outlined in t_out."""
    img = Img(16, 32)
    own = [[None] * 16 for _ in range(32)]
    # trunk: from (7.5, 31) curving to (9, 9)
    for y in range(9, 31):
        t = (31 - y) / 22.0
        cx = 7.0 + 2.2 * t * t
        half = 1.9 - 0.5 * t
        for x in range(16):
            dx = x + 0.5 - cx
            if abs(dx) <= half:
                ring = (y % 3 == 0)
                if dx < -half + 0.9:
                    c = 'k_lt'
                elif dx > half - 0.9:
                    c = 'k_dk'
                else:
                    c = 'k_base'
                if ring:
                    c = 'k_dk' if c != 'k_lt' else 'k_base'
                img.p[y][x] = c
                own[y][x] = 't'
    # fronds
    fronds = [(-160, 8.5, 0.55), (-120, 7.5, 0.35), (-60, 7.5, 0.35), (-20, 8.5, 0.6),
              (160, 6.5, 0.9), (20, 6.5, 0.9), (-95, 5.5, 0.1)]
    ramp = ['t_hi', 't_lt', 't_base', 't_mid', 't_dk']
    cx0, cy0 = 9.0, 9.0
    for (ang, ln, droop) in fronds:
        a = math.radians(ang)
        steps = 40
        for i in range(steps + 1):
            s = i / float(steps)
            px = cx0 + math.cos(a) * ln * s
            py = cy0 + math.sin(a) * ln * s + droop * (ln * s) ** 2 / 4.0
            width = 1.6 * (1.0 - s) + 0.5
            for yy in range(int(py - 2), int(py + 3)):
                for xx in range(int(px - 2), int(px + 3)):
                    if not (0 <= xx < 16 and 0 <= yy < 32):
                        continue
                    d = math.hypot(xx + 0.5 - px, yy + 0.5 - py)
                    if d <= width:
                        # lighting: upper side of the frond is lit
                        k = 1 if (yy + 0.5) < py else 2
                        if s > 0.7:
                            k += 1
                        if ang in (160, 20) and (yy + 0.5) > py:
                            k = 3
                        if (xx * 3 + yy) % 5 == 0 and s > 0.3:
                            k = min(4, k + 1)
                        if xx < 6 and (yy + 0.5) < py and s < 0.6:
                            k = 0
                        img.p[yy][xx] = ramp[k]
                        own[yy][xx] = 'f'
    # coconuts under the crown
    for (x, y) in ((8, 10), (10, 11)):
        for (dx, dy, c) in ((0, 0, 'k_base'), (1, 0, 'k_dk'), (0, 1, 'k_dk'), (1, 1, 'k_dk')):
            img.p[y + dy][x + dx] = c
            own[y + dy][x + dx] = 'c'
        img.p[y][x] = 'k_lt'
    # outline
    out = img.copy()
    for y in range(32):
        for x in range(16):
            if img.p[y][x] is not None:
                continue
            for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < 16 and 0 <= yy < 32 and img.p[yy][xx] is not None:
                    out.p[y][x] = 't_out'
                    break
    # roots
    for (x, c) in ((4, 't_out'), (5, 'k_dk'), (6, 'k_base'), (9, 'k_dk'), (10, 't_out')):
        out.p[31][x] = c
    return out


# ---------------------------------------------------------------- sea water

def coast_water_quads(gf, f):
    """Water autotile with a beach edge: sand outside, a wet-sand line, a
    band of foam that laps in and out over the 3 frames, then the sea."""
    surf = gf.water_surface(f)
    lap = (0.0, 0.7, 1.2)[f]

    def color_at(d, X, Y, c, v, lx, ly):
        if d < 0:
            return SAND_TEX.p[Y][X]
        if d < 0.9 + lap * 0.6:
            return 'sw_lt'
        if d < 1.9 + lap:
            h = hash2(X, Y, 3 + f) & 7
            return 'white' if h else 'w_hi'
        if d < 2.8 + lap:
            return 'w_hi' if (X + Y + f) % 3 == 0 else 'w_lt'
        if d < 4.2:
            return 'w_lt'
        if d < 5.0:
            return 'w_base' if (X + Y) % 2 else 'w_lt'
        return surf.p[Y][X]
    return gf.autotile(color_at, E=1.0, R=6.0, Rn=2.5)


def add_coast_water(gf, ts, out, bank=B_SEA):
    wq = [coast_water_quads(gf, f) for f in range(3)]
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


# ---------------------------------------------------------------- the Current Hall

def hall_floor_img():
    """Big square glazed-stone tiles with a blue diamond at the corners."""
    img = Img(16, 16, 'st_hi')
    for y in range(16):
        for x in range(16):
            if x == 15 or y == 15:
                img.p[y][x] = 'st_mid'
            elif x == 0 or y == 0:
                img.p[y][x] = 'wl_hi'
            elif x == 14 or y == 14:
                img.p[y][x] = 'st_lt'
            elif (x + y) % 11 == 0 and 3 < x < 12:
                img.p[y][x] = 'wl_hi'
    # blue inlays where four tiles meet (drawn as quarter diamonds)
    for (cx, cy) in ((0, 0), (15, 0), (0, 15), (15, 15)):
        for y in range(16):
            for x in range(16):
                if abs(x - cx) + abs(y - cy) <= 2:
                    img.p[y][x] = 'gl_base' if abs(x - cx) + abs(y - cy) <= 1 else 'gl_dk'
    img.p[0][0] = img.p[0][15] = img.p[15][0] = img.p[15][15] = 'gl_hi'
    return img


def hall_wall_top_img():
    img = Img(16, 16, 'wl_hi')
    for x in range(16):
        img.p[0][x] = 'b_out'
        img.p[1][x] = 'gl_dk'
        img.p[2][x] = 'gl_base'
        img.p[3][x] = 'gl_dk'
        # a wave frieze
        wy = 7 + int(round(1.6 * math.sin((x + 0.5) * math.pi / 4.0)))
        for y in range(5, 11):
            if y == wy:
                img.p[y][x] = 'gl_base'
            elif y == wy + 1:
                img.p[y][x] = 'gl_dk'
            elif y > wy + 1:
                img.p[y][x] = 'wl_base'
        img.p[12][x] = 'st_lt'
        img.p[13][x] = 'wl_hi'
        img.p[14][x] = 'wl_base'
        img.p[15][x] = 'wl_base'
    return img


def hall_wall_img():
    """Lower wall: glazed blue tiles above a stone skirting."""
    img = Img(16, 16, 'gl_base')
    for y in range(16):
        for x in range(16):
            if y < 9:
                if x % 8 == 7 or y % 4 == 3:
                    img.p[y][x] = 'gl_dk'
                elif (x % 8 == 0 or y % 4 == 0):
                    img.p[y][x] = 'gl_hi' if (x + y) % 2 else 'gl_base'
            elif y == 9:
                img.p[y][x] = 'b_out'
            elif y < 13:
                img.p[y][x] = 'st_lt' if y == 10 else 'st_mid'
                if x % 8 == 3 and y > 10:
                    img.p[y][x] = 'b_out'
            elif y == 13:
                img.p[y][x] = 'b_out'
            else:
                img.p[y][x] = 'st_mid'
    return img


def hall_porthole_img():
    img = hall_wall_top_img()
    cx, cy = 7.5, 7.5
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + 0.5 - 8, y + 0.5 - 8)
            if d <= 6.5:
                if d > 5.4:
                    img.p[y][x] = 'b_out'
                elif d > 4.2:
                    img.p[y][x] = 'wd_lt' if (x + y) < 16 else 'wd_dk'
                elif d > 3.6:
                    img.p[y][x] = 'b_out'
                else:
                    t = (x - y)
                    img.p[y][x] = 'gl_hi' if -2 <= t <= 1 and y < 9 else 'gl_base'
                    if y > 9:
                        img.p[y][x] = 'gl_dk'
    return img


def hall_mat_img():
    img = hall_floor_img()
    for y in range(3, 15):
        for x in range(2, 14):
            if y in (3, 14) or x in (2, 13):
                img.p[y][x] = 'b_out'
            elif y in (4, 13) or x in (3, 12):
                img.p[y][x] = 'gl_dk'
            else:
                img.p[y][x] = 'gl_base' if (x + y) % 4 else 'gl_hi'
    for x in range(5, 11):
        img.p[8][x] = 'wl_hi'
        img.p[9][x] = 'st_lt'
    return img


def hall_pool_img():
    img = Img(16, 16, 'w_mid')
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 41) & 31
            if h == 0:
                img.p[y][x] = 'w_base'
            elif h == 1:
                img.p[y][x] = 'w_dk'
    for (x, y, n) in ((2, 3, 3), (10, 6, 2), (5, 11, 3), (12, 13, 2)):
        for i in range(n):
            img.p[y][x + i] = 'w_base'
        img.p[y][x + n // 2] = 'w_lt'
    return tile8(img)


def current_frames(horizontal):
    """Four frames of a channel flowing right (horizontal) or down: bright
    streaks sliding 4px per frame over the water and a fixed chevron."""
    frames = []
    streaks = [(1, 1, 5), (4, 9, 4), (7, 4, 6), (10, 12, 3), (13, 7, 5), (15, 2, 3)]
    for f in range(4):
        img = Img(16, 16, 'w_base')
        for y in range(16):
            for x in range(16):
                if (hash2(x, y, 17) & 15) == 0:
                    img.p[y][x] = 'w_mid'
        for (row, start, n) in streaks:
            for i in range(n):
                p = (start + i + f * 4) % 16
                c = 'w_hi' if i == n - 1 else 'w_lt'
                if horizontal:
                    img.p[row][p] = c
                else:
                    img.p[p][row] = c
        # the chevron, pointing downstream
        chev = [(5, 4), (6, 5), (7, 6), (8, 7), (8, 8), (7, 9), (6, 10), (5, 11)]
        for (a, b) in chev:
            for (da, col) in ((0, 'white'), (1, 'white'), (-1, 'w_dk')):
                aa = a + da
                if horizontal:
                    img.set(aa, b, col)
                else:
                    img.set(b, aa, col)
        frames.append(img)
    return frames


def add_currents(gf, ts, out, bank=B_SEA):
    """CUR_RIGHT and CUR_DOWN get animated raw tiles; LEFT and UP reuse them
    flipped, so every channel animates in its own direction."""
    ents = {}
    anims = out.setdefault('anims', [])
    for (name, horizontal) in (('CUR_RIGHT', True), ('CUR_DOWN', False)):
        frames = current_frames(horizontal)
        first = len(ts.tiles)
        tiles = []
        per_frame = [[] for _ in frames]
        for (dx, dy) in gf.QUADS:
            fr = [ts.indices(gf.img_pix(frames[f].crop(dx, dy, 8, 8)), bank) for f in range(4)]
            t = ts.add_raw(fr[0])
            tiles.append(t)
            for f in range(4):
                per_frame[f].append(fr[f])
        anims.append((first, per_frame, 10))
        ents[name] = [t | (bank << 12) for t in tiles]
    r = ents['CUR_RIGHT']
    d = ents['CUR_DOWN']
    H, V = 1 << 10, 1 << 11
    ents['CUR_LEFT'] = [r[1] | H, r[0] | H, r[3] | H, r[2] | H]
    ents['CUR_UP'] = [d[2] | V, d[3] | V, d[0] | V, d[1] | V]
    return ents


# ---------------------------------------------------------------- the grotto

def grot_rock(seed=0):
    """Blue-black cave rock (wrapped Voronoi slabs, lit top-left)."""
    seeds = [(3, 3), (11, 2), (7, 8), (14, 10), (2, 12), (9, 14)]
    seeds = [((x + seed * 5) % 16, (y + seed * 3) % 16) for (x, y) in seeds]

    def owner(x, y):
        best, bi = 1e9, -1
        for i, (px, py) in enumerate(seeds):
            dx = (x + 0.5 - px + 8) % 16 - 8
            dy = ((y + 0.5 - py + 8) % 16 - 8) * 1.4
            d = dx * dx + dy * dy
            if d < best:
                best, bi = d, i
        return bi
    o = [[owner(x, y) for x in range(16)] for y in range(16)]
    img = Img(16, 16)
    for y in range(16):
        for x in range(16):
            me = o[y][x]
            if o[y][(x + 1) % 16] != me or o[(y + 1) % 16][x] != me:
                c = 'gb_blk'
            elif o[(y - 1) % 16][x] != me or o[y][(x - 1) % 16] != me:
                c = 'gb_lt'
            elif o[(y + 2) % 16][x] != me:
                c = 'gb_dk'
            else:
                c = 'gb_mid'
            img.p[y][x] = c
    return img


def tile8(img, ox=0, oy=0):
    """A 16x16 cell repeating one 8x8 block of `img` (costs a single tile)."""
    out = Img(16, 16)
    for y in range(16):
        for x in range(16):
            out.p[y][x] = img.p[oy + y % 8][ox + x % 8]
    return out


def grot_top_img():
    img = tile8(grot_rock(1), 4, 4)
    return img.replace({'gb_lt': 'gb_mid', 'gb_mid': 'gb_dk'})


def grot_wall_img():
    img = grot_rock(0)
    # glowing lichen streaks
    for (x, y) in ((3, 5), (4, 5), (4, 6), (11, 9), (12, 9), (12, 10), (7, 13)):
        img.set(x, y, 'bio_dk')
    img.set(4, 5, 'bio_base')
    img.set(12, 9, 'bio_base')
    for x in range(16):
        img.p[15][x] = 'gb_blk'
        img.p[14][x] = 'gb_dk' if x % 3 else 'gb_blk'
    return img


def grot_floor_img(glow=False):
    img = Img(16, 16, 'gb_dk')
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 88) & 63
            if h < 6:
                img.p[y][x] = 'gb_mid'
            elif h < 9:
                img.p[y][x] = 'gb_blk'
            elif h == 63:
                img.p[y][x] = 'gb_lt'
    # wet glints
    for (x, y) in ((4, 3), (12, 8), (7, 13)):
        img.p[y][x] = 'gb_hi'
        img.p[y][x + 1] = 'gb_lt'
    if glow:
        moss = G('''
        .dd.
        dbbd
        bhbd
        .dd.
        ''', {'.': None, 'd': 'bio_dk', 'b': 'bio_base', 'h': 'bio_hi'})
        img.paste(moss, 2, 8)
        img.paste(moss, 10, 2)
        img.set(9, 12, 'bio_dk')
        img.set(13, 13, 'bio_base')
    return img


def temple_img():
    """Sunken temple flagstones: dark slabs with verdigris-stained joints."""
    img = Img(16, 16, 'gb_mid')
    for y in range(16):
        for x in range(16):
            if y in (7, 15) or (x == 15 and y < 7) or (x == 7 and y > 7):
                img.p[y][x] = 'vg_dk'
            elif y in (0, 8) or (x == 0 and y < 7) or (x == 8 and y > 8):
                img.p[y][x] = 'gb_lt'
            elif (hash2(x, y, 9) & 15) == 0:
                img.p[y][x] = 'gb_dk'
    for (x, y) in ((3, 3), (12, 11)):
        img.p[y][x] = 'vg_base'
    return img


def glow_pool_frames():
    frames = []
    specks = [(2, 2), (6, 5), (11, 3), (14, 7), (3, 9), (8, 11), (12, 13), (5, 14), (9, 8)]
    for f in range(3):
        img = Img(16, 16, 'dw_base')
        for y in range(16):
            for x in range(16):
                if (hash2(x, y, 51) & 15) == 0:
                    img.p[y][x] = 'gb_dk'
        for i, (x, y) in enumerate(specks):
            phase = (i + f) % 3
            if phase == 0:
                img.p[y][x] = 'bio_hi'
                img.set(x + 1, y, 'bio_base')
                img.set(x, y + 1, 'bio_dk')
            elif phase == 1:
                img.p[y][x] = 'bio_base'
            else:
                img.p[y][x] = 'bio_dk'
        frames.append(img)
    return frames


def grot_mat_img():
    """Worn steps leading up and out."""
    img = Img(16, 16, 'gb_mid')
    for y in range(16):
        for x in range(16):
            step = y // 5
            if y % 5 == 0:
                img.p[y][x] = 'gb_hi' if step < 2 else 'gb_lt'
            elif y % 5 == 4:
                img.p[y][x] = 'gb_blk'
            else:
                img.p[y][x] = ('gb_lt', 'gb_mid', 'gb_dk')[min(2, step)]
    for x in range(16):
        img.p[15][x] = 'gb_dk'
    return img


# ---------------------------------------------------------------- buildings

FONT_EXTRA = {
    'U': ['#..#', '#..#', '#..#', '#..#', '.##.'],
    'G': ['.###', '#...', '#.##', '#..#', '.###'],
    'D': ['###.', '#..#', '#..#', '#..#', '###.'],
    'W': ['#..#', '#..#', '####', '####', '#..#'],
    'Y': ['#..#', '#..#', '.##.', '.##.', '.##.'],
    'F': ['####', '#...', '###.', '#...', '#...'],
    'K': ['#..#', '#.#.', '##..', '#.#.', '#..#'],
}


def sign(gf, text, plate='st_hi', ink='gl_dk', edge='st_lt'):
    font = dict(gf.FONT)
    font.update(FONT_EXTRA)
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
        if ch == ' ':
            continue
        for yy, row in enumerate(font[ch]):
            for xx, px in enumerate(row):
                if px == '#':
                    img.p[2 + yy][3 + i * 5 + xx] = ink
    return img


ROOF_TEAL_TO_BLUE = {'rt_hi': 'rb_hi', 'rt_lt': 'rb_lt', 'rt_base': 'rb_base',
                     'rt_dk': 'rb_dk', 'rt_dkr': 'rb_dkr'}


def anchor_emblem():
    return G('''
    ...OOO...
    ..OHLLO..
    ..OLOMO..
    ..OOMOO..
    OOOOHOOOO
    OHHHLMMMO
    OOOOLOOOO
    ...OLO...
    O..OLO..O
    OHOOLOOMO
    .OHHLMMO.
    ..OOOOO..
    ''', {'.': None, 'O': 'b_out', 'H': 'st_hi', 'L': 'st_lt', 'M': 'st_mid'})


def harbor_office(gf):
    img = gf.cottage('house')
    # replace the chimney with a flag mast and put an anchor in the gable
    img.paste(anchor_emblem(), 36, 12)
    img.paste(sign(gf, 'HARBOR'), 23, 26)
    return img


def inn(gf):
    img = gf.cottage('house').replace(gf.RED_TO_BLUE)
    img.paste(sign(gf, 'GULL INN', plate='wl_hi', ink='gl_dk', edge='wl_dk'), 18, 26)
    # a hanging board with a fish on it beside the door
    board = G('''
    OOOOOOOOOO
    .O......O.
    OOOOOOOOOO
    OAAAAAAAAO
    OAHHHHHHKO
    OAHMMMHHKO
    OAMMMMMLKO
    OAHMMMHHKO
    OAHHHHHHKO
    OKKKKKKKKO
    OOOOOOOOOO
    ''', {'.': None, 'O': 'b_out', 'A': 'wd_lt', 'K': 'wd_dk', 'H': 'wl_hi', 'M': 'gl_base',
          'L': 'gl_dk'})
    img.paste(board, 50, 36)
    return img


def shop(gf):
    return gf.cottage('shop').replace(ROOF_TEAL_TO_BLUE)


def current_hall(gf):
    """112x80 stamp (7x5 metatiles): the Current Hall, a white bathhouse
    temple with a blue roof, a wave crest in the gable and an arched door."""
    W_, H_ = 112, 80
    img = Img(W_, H_, 'g_base')
    for x in range(7, 110):
        img.set(x, 76, 'g_dk')
        if 8 <= x <= 108:
            img.set(x, 77, 'g_dk')
    # walls: white stone with a blue tile band and pilasters
    for y in range(34, 72):
        for x in range(5, 107):
            if y < 38:
                c = 'wl_hi'
            elif y == 38:
                c = 'gl_dk'
            elif y < 41:
                c = 'gl_base' if (x // 4 + y) % 2 else 'gl_hi'
            elif y == 41:
                c = 'gl_dk'
            elif y < 66:
                # ashlar courses (8px joints, so wall tiles repeat)
                c = 'st_hi' if y % 4 else 'st_lt'
                if (x + (4 if (y // 4) % 2 else 0)) % 8 == 0 and y % 4:
                    c = 'st_lt'
            else:
                c = 'st_lt' if y < 70 else 'st_mid'
            img.set(x, y, c)
        img.set(4, y, 'b_out')
        img.set(107, y, 'b_out')
    for px in (6, 30, 78, 102):     # pilasters (x % 8 == 6: their tiles repeat)
        for y in range(42, 70):
            for x in range(px, px + 6):
                c = 'wl_hi' if x == px else ('st_lt' if x < px + 4 else 'st_mid')
                if x == px + 5:
                    c = 'b_out'
                img.set(x, y, c)
        for x in range(px - 1, px + 7):
            img.set(x, 42, 'b_out')
            img.set(x, 43, 'wl_hi')
            img.set(x, 68, 'b_out')
    for x in range(4, 108):
        img.set(x, 72, 'b_out')
        img.set(x, 73, 'st_mid' if x % 8 else 'b_out')
        img.set(x, 74, 'b_out')
    # round windows
    for (wx, wy) in ((18, 50), (90, 50)):
        for y in range(wy - 7, wy + 8):
            for x in range(wx - 7, wx + 8):
                d = math.hypot(x + 0.5 - wx, y + 0.5 - wy)
                if d <= 6.8:
                    if d > 5.6:
                        c = 'b_out'
                    elif d > 4.5:
                        c = 'wd_lt' if (x - wx) + (y - wy) < 0 else 'wd_dk'
                    elif d > 3.7:
                        c = 'b_out'
                    else:
                        c = 'gl_hi' if -2 <= (x - wx) - (y - wy) <= 1 and y < wy else 'gl_base'
                        if y > wy + 1:
                            c = 'gl_dk'
                    img.set(x, y, c)
    # the arched double door (door cell: column 3, row 4)
    for y in range(52, 72):
        for x in range(44, 68):
            dx = x + 0.5 - 56
            top = 58 - math.sqrt(max(0.0, 144 - dx * dx)) * 0.55
            if y < top:
                continue
            edge = abs(dx) > 10.5 or y < top + 1.2
            if edge:
                c = 'b_out'
            elif abs(dx) > 9.0 or y < top + 2.2:
                c = 'st_lt'
            elif abs(dx) < 0.8:
                c = 'b_out'
            else:
                c = 'gl_dk' if y < 62 else 'wd_base'
                if y < 62 and (x + y) % 5 == 0:
                    c = 'gl_base'
                if y >= 62 and (x % 4 == 0):
                    c = 'wd_dk'
                if y >= 62 and y % 5 == 0:
                    c = 'wd_lt'
            img.set(x, y, c)
    img.paste(gf.STEP, 48, 72)
    # roof with a gable crest
    gf.draw_roof(img, 1, 110, 8, 35, 5, gf.ROOF_BLUE)
    crest = Img(26, 22)
    for y in range(22):
        for x in range(26):
            d = math.hypot(x + 0.5 - 13, y + 0.5 - 11)
            if d <= 10.5:
                if d > 9.3:
                    c = 'b_out'
                elif d > 8.3:
                    c = 'st_lt'
                else:
                    c = 'wl_hi'
                    wy = 12 + 2.5 * math.sin((x + 0.5) * math.pi / 5.0)
                    if y > wy + 1:
                        c = 'gl_dk'
                    elif y > wy - 0.5:
                        c = 'gl_base'
                    elif y > wy - 1.5 and (x % 3):
                        c = 'st_hi'
                crest.p[y][x] = c
    img.paste(crest, 43, 6)
    img.paste(sign(gf, 'CURRENT HALL'), 24, 27)
    # the eave row shares 8x8 tiles with the roof: the blue-roof bank has no
    # gl_hi, so the glass highlight there becomes the wall's white
    for y in range(32, 40):
        for x in range(img.w):
            if img.p[y][x] in ('gl_hi', 'gl_base'):
                img.p[y][x] = 'wl_hi'
    return img


def thatch_hut(gf, door=True):
    """48x48 stamp (3x3 metatiles): a Gull Isle fisher's hut: whitewashed
    walls, a thatched roof and a round window. Door cell: column 1, row 2."""
    img = Img(48, 48, 'g_base')
    for x in range(6, 46):
        img.set(x, 45, 'g_dk')
        if 7 <= x <= 44:
            img.set(x, 46, 'g_dk')
    # walls (x 4..59, y 24..43)
    for y in range(24, 44):
        for x in range(4, 44):
            if x in (4, 43):
                c = 'b_out'
            elif y >= 40:
                c = 'st_mid' if (x + (4 if y % 2 else 0)) % 8 else 'st_lt'
                if y == 40:
                    c = 'b_out'
            else:
                c = 'wl_hi'
                if x == 5:
                    c = 'wl_base'
                if x == 42:
                    c = 'wl_dk'
            img.set(x, y, c)
    for x in range(4, 44):
        img.set(x, 43, 'b_out')
    # door (x 18..29, y 28..43)
    if door:
        for y in range(28, 44):
            for x in range(18, 30):
                if x in (18, 29) or y == 28:
                    c = 'b_out'
                elif x in (19, 28) or y == 29:
                    c = 'wd_lt' if x == 19 or y == 29 else 'wd_dk'
                else:
                    c = 'wd_base' if (x - 20) % 3 else 'wd_dk'
                    if y == 36 and x == 26:
                        c = 'st_hi'
                img.set(x, y, c)
    else:
        for y in range(30, 38):
            for x in range(18, 30):
                img.set(x, y, 'b_out' if x in (18, 29) or y in (30, 37) else
                        ('gl_base' if (x + y) % 4 else 'gl_hi'))
    # round window
    for y in range(28, 40):
        for x in range(30, 42):
            d = math.hypot(x + 0.5 - 36, y + 0.5 - 34)
            if d <= 5.5:
                c = 'b_out' if d > 4.4 else ('wd_lt' if d > 3.4 else 'gl_base')
                if d <= 3.4 and x - 36 < y - 34 - 1:
                    c = 'gl_dk'
                if d <= 3.4 and -1 <= (x - 36) - (y - 34) <= 0 and y < 34:
                    c = 'gl_hi'
                img.set(x, y, c)
    # thatched roof (x 1..46, y 2..27), bank 3 colours
    for y in range(2, 28):
        k = int(round(8 * (27 - y) / 25.0))
        xl, xr = 1 + k, 46 - k
        for x in range(xl, xr + 1):
            if y == 2 or y == 27 or x == xl or x == xr:
                c = 'b_out'
            else:
                r = (y - 3) % 5
                s = ((y // 5) * 3) & 7   # periodic in x: roof tiles repeat
                if r == 4 or y == 26:
                    c = 'wd_dk'
                elif r == 3:
                    c = 'wd_base' if (x + s) % 4 else 'wd_dk'
                elif r == 0:
                    c = 'wl_base' if (x + s) % 4 else 'wd_lt'
                else:
                    c = 'wd_lt' if (x + s + 3 * r) % 8 else 'wl_base'
                if y == 25 and (x % 4 == 0):
                    c = 'wd_base'
            img.set(x, y, c)
    # ridge
    for x in range(11, 37):
        img.set(x, 3, 'wd_dk')
        img.set(x, 4, 'wd_base' if x % 2 else 'wd_dk')
    return img


def cave_door():
    """1x1 stamp: a sea cave's door cell. It goes on a TUNNEL mouth in an
    elevation cliff (docs/ELEVATION.md): the mouth art is drawn over it, the
    stamp gives the cell its A_DOOR and a dark inside (the same tile as
    VOID, so it costs nothing)."""
    return solid(16, 16, 'gb_blk')


# ---------------------------------------------------------------- build

TERRAIN_TIDE = [
    # the Current Hall
    'HALL_FLOOR', 'HALL_WALL_TOP', 'HALL_WALL', 'HALL_PORTHOLE', 'HALL_MAT', 'HALL_POOL',
    'CUR_DOWN', 'CUR_UP', 'CUR_LEFT', 'CUR_RIGHT',
    # the Drowned Bell
    'GROT_TOP', 'GROT_WALL', 'GROT_FLOOR', 'GROT_GLOW', 'TEMPLE', 'GLOW_POOL', 'GROT_MAT',
    'VOID',
]
TERRAIN_OUT = [t for t in TERRAIN if t not in TERRAIN_TIDE] + ['VOID']


def _setup(gf, name, terrain):
    gf.register_colors(COAST_COLORS)
    BANKS = banks(gf)
    gf.check_banks(name, BANKS)
    ts = gf.TileSet(name, BANKS)
    return ts, {'ts': ts, 'meta_b': [], 'meta_t': [], 'terrain': list(terrain)}


def _plain(gf, ts, out, name, imgs, tname):
    im, top, bank = imgs[tname]
    out['meta_b'].append(ts.meta(im, prefer=(bank,), where='%s.%s' % (name, tname)))
    out['meta_t'].append(ts.meta(top, prefer=(bank,), where='%s.%s.top' % (name, tname),
                                 opaque=False) if top else [0, 0, 0, 0])


def build(gf, name):
    """'coast': the outdoor maps (Saltwind, Port Brine, the Sea Route, Gull
    Isle). The Current Hall and the Drowned Bell are the 'tide' tileset
    (build_tide), so the towns keep room for their props in the 512-tile
    scene charblock (tileset + the map's decor)."""
    if name != 'coast':
        return build_tide(gf, name)
    import terrain_wild
    from terrain_common import GRASS_A, GRASS_B, GRASS_C, tallgrass_layers
    ts, out = _setup(gf, name, TERRAIN_OUT)
    add_coast_water(gf, ts, out)
    flower_meta = gf.add_flower_anim(ts, out)
    tall_b, tall_t = tallgrass_layers()
    dune_b, dune_t = dunegrass_layers()
    pine = terrain_wild.pine_img(overlay=True)
    palm = palm_img()
    imgs = {
        'GRASS': (GRASS_A, None, B_GROUND), 'GRASS2': (GRASS_B, None, B_GROUND),
        'GRASS3': (GRASS_C, None, B_GROUND),
        'TALLGRASS': (tall_b, tall_t, B_GROUND), 'DUNEGRASS': (dune_b, dune_t, B_GROUND),
        'SAND': (SAND_TEX, None, B_SEA), 'SAND2': (sand2_img(), None, B_SEA),
        'SAND3': (sand3_img(), None, B_SEA), 'STONE': (stone_img(), None, B_SEA),
        'QUAY': (quay_img(), None, B_SEA), 'SHELF': (shelf_img(), None, B_SEA),
        'TIDEPOOL': (tidepool_img(), None, B_SEA), 'SALTPAN': (saltpan_img(), None, B_SEA),
        'DUNE_LEDGE': (dune_ledge_img(), None, B_GROUND),
        'VOID': (solid(16, 16, 'gb_blk'), None, B_GROTTO),
    }
    for tname in TERRAIN_OUT:
        if tname == 'FLOWER_RED':
            out['meta_b'].append(flower_meta[0])
        elif tname == 'FLOWER_YELLOW':
            out['meta_b'].append(flower_meta[1])
        elif tname in ('PINE_TOP', 'PINE_BOTTOM', 'PALM_TOP', 'PALM_BOTTOM'):
            src = pine if tname.startswith('PINE') else palm
            part = src.crop(0, 0, 16, 16) if tname.endswith('_TOP') else src.crop(0, 16, 16, 16)
            gf.add_overlay_terrain(ts, out, tname, part, top=tname.endswith('_TOP'))
            continue
        else:
            _plain(gf, ts, out, name, imgs, tname)
            continue
        out['meta_t'].append([0, 0, 0, 0])
    gf.add_stamps(ts, out, [
        ('HEAL', gf.cottage('heal'), (B_WALLS, B_RED), 'BRINE HEARTH HALL, flame emblem, door col 2 row 3'),
        ('SHOP', shop(gf), (B_WALLS, B_BLUE), 'BRINE SHOP (blue roof), door col 2 row 3'),
        ('HOUSE_RED', gf.cottage('house'), (B_WALLS, B_RED), 'red roof house, door col 2 row 3'),
        ('HOUSE_BLUE', gf.cottage('house').replace(gf.RED_TO_BLUE), (B_WALLS, B_BLUE),
         'blue roof house, door col 2 row 3'),
        ('HARBOR', harbor_office(gf), (B_WALLS, B_RED), 'HARBOR OFFICE, anchor gable, door col 2 row 3'),
        ('INN', inn(gf), (B_WALLS, B_BLUE), 'GULL INN, fish board, door col 2 row 3'),
        ('HALL', current_hall(gf), (B_WALLS, B_BLUE), 'CURRENT HALL, wave crest, door col 3 row 4'),
        ('HUT', thatch_hut(gf), (B_WALLS, B_PROPS), 'Gull Isle thatched hut (3x3), door col 1 row 2'),
        ('CAVE', cave_door(), (B_GROTTO,),
         'sea cave door (1x1): put it on a TUNNEL mouth in an elevation cliff'),
    ])
    gf.add_path(ts, out)
    A = gf
    attrs = {
        'TALLGRASS': A.A_GRASS, 'DUNEGRASS': A.A_GRASS,
        'TIDEPOOL': A.A_SOLID | A.A_WATER | A.A_DEEP, 'SALTPAN': A.A_SOLID, 'DUNE_LEDGE': A.A_LEDGE, 'VOID': A.A_SOLID,
    }
    gf.add_blend(ts, out, ['SAND', 'SAND2', 'SAND3'], imgs['SAND'][0], imgs['GRASS'][0],
                 ['GRASS', 'GRASS2', 'GRASS3', 'TALLGRASS', 'FLOWER_RED', 'FLOWER_YELLOW'], width=3.0, seed=0.7)
    return gf.finish_tileset(
        out, name, 'CO', attrs=attrs,
        ground=['GRASS', 'GRASS2', 'GRASS3', 'SAND', 'SAND2', 'SAND3', 'STONE', 'QUAY', 'SHELF'],
        overlay=['PINE_TOP', 'PINE_BOTTOM', 'PALM_TOP', 'PALM_BOTTOM'],
        legend={'.': gf.GRASS_VARIANTS, ',': 'TALLGRASS', ';': 'DUNEGRASS',
                's': [('SAND2', 2), ('SAND3', 1), ('SAND', 13)], '=': 'PATH', '~': 'WATER',
                '#': 'STONE', 'q': 'QUAY', 'k': 'SHELF', 'o': 'TIDEPOOL', '%': 'SALTPAN',
                'l': 'DUNE_LEDGE', 'r': 'FLOWER_RED', 'y': 'FLOWER_YELLOW',
                'P': 'PINE_TOP', 'T': 'PINE_TOP', 'p': 'PINE_BOTTOM', 'A': 'PALM_TOP', 'a': 'PALM_BOTTOM',
                ' ': 'VOID'},
        oob='VOID', default_ground='SAND', backdrop=(10, 14, 30),
        doors=[('HEAL', 2, 3), ('SHOP', 2, 3), ('HOUSE_RED', 2, 3), ('HOUSE_BLUE', 2, 3),
               ('HARBOR', 2, 3), ('INN', 2, 3), ('HALL', 3, 4), ('HUT', 1, 2), ('CAVE', 0, 0)])


def build_tide(gf, name):
    """'tide': the CURRENT HALL (floor, walls, pools, flowing channels) and
    the DROWNED BELL grotto. Same palette banks as 'coast' (the west props
    are drawn in them)."""
    ts, out = _setup(gf, name, TERRAIN_TIDE)
    out['anims'] = []
    cur = add_currents(gf, ts, out)
    # glowing pool: animated raw tiles
    gp = glow_pool_frames()
    first = len(ts.tiles)
    gp_tiles, gp_frames = [], [[] for _ in gp]
    for (dx, dy) in gf.QUADS:
        fr = [ts.indices(gf.img_pix(gp[f].crop(dx, dy, 8, 8)), B_GROTTO) for f in range(len(gp))]
        gp_tiles.append(ts.add_raw(fr[0]))
        for f in range(len(gp)):
            gp_frames[f].append(fr[f])
    out['anims'].append((first, gp_frames, 16))
    gp_ents = [t | (B_GROTTO << 12) for t in gp_tiles]
    imgs = {
        'HALL_FLOOR': (hall_floor_img(), None, B_WALLS),
        'HALL_WALL_TOP': (hall_wall_top_img(), None, B_WALLS),
        'HALL_WALL': (hall_wall_img(), None, B_WALLS),
        'HALL_PORTHOLE': (hall_porthole_img(), None, B_WALLS),
        'HALL_MAT': (hall_mat_img(), None, B_WALLS),
        'HALL_POOL': (hall_pool_img(), None, B_SEA),
        'GROT_TOP': (grot_top_img(), None, B_GROTTO), 'GROT_WALL': (grot_wall_img(), None, B_GROTTO),
        'GROT_FLOOR': (grot_floor_img(), None, B_GROTTO),
        'GROT_GLOW': (grot_floor_img(True), None, B_GROTTO),
        'TEMPLE': (temple_img(), None, B_GROTTO), 'GROT_MAT': (grot_mat_img(), None, B_GROTTO),
        'VOID': (solid(16, 16, 'gb_blk'), None, B_GROTTO),
    }
    for tname in TERRAIN_TIDE:
        if tname in cur:
            out['meta_b'].append(cur[tname])
        elif tname == 'GLOW_POOL':
            out['meta_b'].append(gp_ents)
        else:
            _plain(gf, ts, out, name, imgs, tname)
            continue
        out['meta_t'].append([0, 0, 0, 0])
    out['stamps'] = []
    A = gf
    cur_attr = lambda d: A.A_CURRENT | (A.A_DIR_LO if d & 1 else 0) | (A.A_DIR_HI if d & 2 else 0)
    attrs = {
        'HALL_WALL_TOP': A.A_SOLID, 'HALL_WALL': A.A_SOLID, 'HALL_PORTHOLE': A.A_SOLID,
        'HALL_MAT': A.A_EXIT, 'HALL_POOL': A.A_SOLID | A.A_WATER | A.A_DEEP,
        'CUR_DOWN': cur_attr(0), 'CUR_UP': cur_attr(1), 'CUR_LEFT': cur_attr(2),
        'CUR_RIGHT': cur_attr(3),
        'GROT_TOP': A.A_SOLID, 'GROT_WALL': A.A_SOLID,
        'GLOW_POOL': A.A_SOLID | A.A_WATER | A.A_DEEP, 'GROT_MAT': A.A_EXIT, 'VOID': A.A_SOLID,
    }
    return gf.finish_tileset(
        out, name, 'TD', attrs=attrs,
        ground=['HALL_FLOOR', 'GROT_FLOOR', 'GROT_GLOW', 'TEMPLE'],
        overlay=[],
        legend={'H': 'HALL_WALL_TOP', 'h': 'HALL_WALL', 'n': 'HALL_PORTHOLE', '_': 'HALL_FLOOR',
                'M': 'HALL_MAT', 'O': 'HALL_POOL', 'v': 'CUR_DOWN', '^': 'CUR_UP',
                '<': 'CUR_LEFT', '>': 'CUR_RIGHT',
                'G': 'GROT_TOP', 'g': 'GROT_WALL', ':': 'GROT_FLOOR', "'": 'GROT_GLOW',
                't': 'TEMPLE', '*': 'GLOW_POOL', 'm': 'GROT_MAT', ' ': 'VOID'},
        oob='VOID', default_ground='HALL_FLOOR', backdrop=(10, 14, 30), legend_default=' ')
