"""The 'snow' tileset (owner: W-NORTH): Frostpine Pass, Frosthollow, the
Rime Hall, the hot spring, Whitecrown Peak and the Sky Isle.

Map legend (documented again at the top of src/game/world/north/data.h):

  .  snow (+ footprints, kin tracks)     ,  snow drift with frosted grass (wild kin)
  =  trodden snow path (autotiled)      ~  icy water (autotiled, animated)
  P  snowy pine, top half (overlay)     p  snowy pine, bottom half (overlay)
  L  icy ledge (hop down)   [ ]  ledge ends
  C  cliff with a snow cap  c  cliff face  R  snowbank crag (solid)
  #  slate cobbles (plaza)
  i  ice (A_ICE: you slide)  7 8 9 / 4 6 / 1 2 3  ice with a snowy rim (numpad
     layout: 7 = north-west corner ... 3 = south-east corner), also A_ICE
  o  rock frozen into the ice (solid)
  K  sea of clouds (Sky Isle; solid)
  F  hall flagstones  W  hall wall (upper)  w  hall wall (lower)  D  exit mat
  ' ' void (outside a room)

Stamps (STAMP(SN, NAME, x, y)): HOUSE, HEARTH, SHOP, BATHS (5x4, door col 2
row 3), HALL (7x5, door col 3 row 4), CAVE (3x2, door col 1 row 1).

Palette banks come from tools/north_palette.py; bank 3 is the village props
bank so signposts, fences, benches and lantern posts work here too.
"""

import math
from pixelart import Img, G, tex_fill, hash2, shade_clumps
from terrain_common import autotile
from terrain_wild import rock_tex
import north_palette as NP
import decor_outdoor

USES_DECOR = ['SIGNPOST', 'SIGN_ARROW', 'FENCE', 'FENCE_END', 'GATE', 'BENCH', 'BARREL', 'CRATE',
              'CRATE_STACK', 'SACKS', 'WOODPILE', 'STUMP', 'LOG', 'CAMPFIRE', 'LANTERN_POST',
              'STONE_LANTERN', 'LAMP', 'WELL', 'PEBBLES', 'NOTICE_BOARD', 'SHRINE', 'PICNIC_TABLE',
              'WATER_TROUGH', 'HAY_BALE', 'BRIDGE_H', 'BRIDGE_V', 'ROCK', 'BOULDER', 'KIN_STATUE',
              'TELESCOPE', 'WEATHER_VANE', 'CART', 'CLOTHESLINE', 'DOCK', 'DOCK_EDGE', 'DOCK_POST']

TERRAIN = [
    'SNOW', 'SNOW2', 'SNOW3', 'DRIFT', 'PINE_TOP', 'PINE_BOTTOM',
    'LEDGE', 'LEDGE_L', 'LEDGE_R', 'CLIFF', 'CLIFF_FACE', 'CRAG', 'STONE',
    'ICE', 'ICE_N', 'ICE_S', 'ICE_W', 'ICE_E', 'ICE_NW', 'ICE_NE', 'ICE_SW', 'ICE_SE',
    'ICE_ROCK', 'CLOUD', 'HALL_FLOOR', 'HALL_WALL_TOP', 'HALL_WALL', 'HALL_MAT', 'VOID',
]
OVERLAY = ('PINE_TOP', 'PINE_BOTTOM')

DOC = {
    'SNOW': 'fresh snow (+ SNOW2 footprints, SNOW3 kin tracks and a twig)',
    'DRIFT': 'snow drift with frosted grass: wild kin roam here; top layer hides legs',
    'PINE_TOP': '16x32 snowy pine: TOP above BOTTOM (overlay, ground drawn beneath)',
    'LEDGE': 'icy ledge: walk DOWN onto it to hop over; tiles horizontally',
    'CLIFF': 'granite wall with a snow cap on top (solid); stack CLIFF_FACE below',
    'CRAG': 'wind-carved snowbank with rock showing (solid)',
    'STONE': 'slate cobbles with snow in the joints (Frosthollow plaza)',
    'ICE': 'frozen pond (A_ICE: you slide until blocked); ICE_* have a snowy rim',
    'ICE_ROCK': 'granite boulder frozen into the ice (solid)',
    'CLOUD': 'the sea of clouds around the Sky Isle (solid)',
    'HALL_FLOOR': 'Rime Hall flagstones',
    'HALL_WALL_TOP': 'upper hall wall of frosted ice bricks',
    'HALL_WALL': 'lower hall wall with a granite skirting',
    'HALL_MAT': 'exit mat (A_EXIT) on the flagstones',
    'VOID': 'outside a room',
}

SN = {'.': 'sn_base', 'l': 'sn_lt', 'm': 'sn_mid', 'h': 'sn_hi', 'd': 'sn_dk', 'D': 'sn_dkr'}

# ---------------------------------------------------------------------------
# snow ground (kept mostly flat sn_base so building stamps blend in)
# ---------------------------------------------------------------------------

SNOW_A = G('''
................
..........h.....
................
....ll..........
...lmmm.........
..........lll...
.........lmmmm..
................
.h..............
................
......ll........
.....lmmml.....h
................
..............l.
.............lmm
................
''', SN)

SNOW_B = G('''
................
..lm............
..mdm...........
...m.....h......
.........lm.....
.........mdm....
..........m.....
...lm...........
...mdm..........
....m.......lm..
............mdm.
.............m..
.....lm.........
.....mdm......h.
......m.........
................
''', SN)

SNOW_C = G('''
................
.............h..
..m.m...........
...m............
................
..........ll....
.....m.m.lmmm...
......m.........
.........D......
..........D.....
.h........dD....
..........d.D...
...ll......d....
..lmmm..........
................
................
''', SN)


def snow_tex():
    return SNOW_A


# ---------------------------------------------------------------------------
# drifts with frosted grass (wild kin roam here)
# ---------------------------------------------------------------------------

FT = {'.': None, 'O': 'fg_dkr', 'd': 'fg_dk', 'm': 'fg_base', 'l': 'fg_hi', 'h': 'sn_hi',
      's': 'sn_lt'}
FROST_TUFT = G('''
..h...h.
.hlO.hlO
.slmOhlm
hllmdllm
slmmdlmd
lmmddmmd
mmdddmdd
ddddOddd
dOddddOd
''', FT)


def drift_layers():
    back = Img(16, 16, 'sn_base')
    for y in range(16):
        for x in range(16):
            if (hash2(x, y, 41) & 15) == 0:
                back.p[y][x] = 'sn_lt'
    for ox in (-4, 4, 12):
        back.paste(FROST_TUFT, ox, 0)
    front = Img(16, 16)
    for ox in (0, 8):
        front.paste(FROST_TUFT, ox, 8)
    bottom = back.copy()
    bottom.paste(front, 0, 0)
    for y in range(16):
        for x in range(16):
            if bottom.p[y][x] is None:
                bottom.p[y][x] = 'sn_mid'
    # snow heaped against the tuft roots
    for x in range(16):
        if bottom.p[15][x] in ('fg_dk', 'fg_dkr'):
            bottom.p[15][x] = 'sn_mid' if x % 3 else 'sn_lt'
    top = Img(16, 16)
    for y in range(9, 16):
        for x in range(16):
            ty, tx = y - 8, x % 8
            c = FROST_TUFT.p[ty][tx]
            if c is None:
                continue
            if ty <= 3 and c in ('fg_dkr', 'fg_dk'):
                continue
            top.p[y][x] = c
    return bottom, top


# ---------------------------------------------------------------------------
# trodden path (autotile)
# ---------------------------------------------------------------------------

PATH_TEX = G('''
mmmmmmmmmmmmmmmm
mmmmdmmmmmmmmmmm
mmmdDdmmmmmmlmmm
mmmmdmmmmmmmmmmm
mmmmmmmmmmdmmmmm
mlmmmmmmmdDdmmmm
mmmmmmmmmmdmmmmm
mmmmmmmmmmmmmmmm
mmmmmmdmmmmmmmmm
mmmmmdDdmmmmmmmm
mmmmmmdmmmmmmdmm
mmmmmmmmmmmmdDdm
mmmmmmmmmlmmmdmm
mdmmmmmmmmmmmmmm
dDdmmmmmmmmmmmmm
mdmmmmmmmmmmmmmm
''', SN)


def path_quads():
    def color_at(d, X, Y, c, v, lx, ly):
        if d < -1.0:
            return SNOW_A.p[Y][X]
        if d < 0:
            return 'sn_hi'
        if d < 1.0:
            return 'sn_dk' if (c >> 1) == 0 or (c & 1) == 0 else 'sn_lt'
        if d < 2.0:
            return 'sn_mid'
        return PATH_TEX.p[Y][X]
    return autotile(color_at, E=2.0, R=5.0, Rn=2.0)


# ---------------------------------------------------------------------------
# icy water (autotile, 3 frames)
# ---------------------------------------------------------------------------

FLOES = [(1, 2, 3), (11, 1, 2), (6, 6, 4), (13, 9, 2), (2, 11, 2), (9, 13, 3)]


def water_surface(f):
    img = Img(16, 16, 'iw_base')
    for y in range(16):
        for x in range(16):
            if (hash2(x, y, 17) & 31) == 0:
                img.p[y][x] = 'iw_mid'
    for (x, y, n) in FLOES:
        x2 = x + (f if n <= 2 else 0)
        for i in range(n):
            img.p[y % 16][(x2 + i) % 16] = 'iw_lt'
        img.p[y % 16][(x2 + (f % n)) % 16] = 'iw_hi'
        for i in range(max(1, n - 1)):
            img.p[(y + 1) % 16][(x2 + 1 + i) % 16] = 'iw_mid'
    return img


def water_quads(f):
    surf = water_surface(f)

    def color_at(d, X, Y, c, v, lx, ly):
        if d < 0:
            return SNOW_A.p[Y][X]
        if d < 1.0:
            return 'sn_hi'
        if d < 2.0:
            return 'ic_lt'
        if d < 3.0:
            return 'ic_base' if (X + Y) % 5 else 'ic_hi'
        if d < 4.0:
            return 'iw_dk'
        if d < 5.0:
            return 'iw_mid'
        return surf.p[Y][X]
    return autotile(color_at, E=1.0, R=6.0, Rn=2.5)


def add_water(gf, ts, out, bank=1):
    """Contiguous, never-shared block of animated water autotiles
    (gen_field_gfx.add_water_anim with the icy shore)."""
    wq = [water_quads(f) for f in range(3)]
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
# snowy pine (overlay: transparent around the tree)
# ---------------------------------------------------------------------------

PINE_RAMP = ['pn_hi', 'pn_lt', 'pn_base', 'pn_dk', 'pn_dk']


def snowy_pine():
    tiers = [(13.0, 27.0, 8.2), (6.5, 20.0, 7.0), (1.0, 12.5, 5.2)]
    img = Img(16, 32)
    owner = [[-1] * 16 for _ in range(32)]
    for ti, (ay, by, hw) in enumerate(tiers):
        for y in range(32):
            for x in range(16):
                v = (y + 0.5 - ay) / (by - ay)
                if v < 0 or v > 1.08:
                    continue
                half = hw * min(1.0, v) + 0.35
                dx = x + 0.5 - 8.0
                if abs(dx) > half:
                    continue
                tooth = (x % 3 == 1)
                if v > 1.0 and not tooth:
                    continue
                if v > 0.93 and abs(dx) > half - 1.0 and not tooth:
                    continue
                owner[y][x] = ti
    for y in range(32):
        for x in range(16):
            ti = owner[y][x]
            if ti < 0:
                continue
            ay, by, hw = tiers[ti]
            v = (y + 0.5 - ay) / (by - ay)
            half = hw * min(1.0, max(v, 0.05)) + 0.35
            t = (x + 0.5 - 8.0) / half
            k = 1 if t < -0.5 else 2 if t < 0.2 else 3
            if v > 0.8:
                k = min(4, k + 1)
            h = hash2(x, y, 29) & 7
            if h == 0 and k < 4:
                k += 1
            elif h == 1 and k > 1:
                k -= 1
            if y > 0 and owner[y - 1][x] > ti:
                k = 4
            c = PINE_RAMP[k]
            # snow resting on the bough: the exposed upper surface
            depth = 0
            while y - depth - 1 >= 0 and owner[y - depth - 1][x] == ti:
                depth += 1
            above = owner[y - depth - 1][x] if y - depth - 1 >= 0 else -1
            if above == -1:
                if depth == 0:
                    c = 'sn_hi' if t < 0.3 else 'sn_lt'
                elif depth == 1:
                    c = 'sn_lt' if t < 0.0 else 'sn_mid' if t < 0.6 else c
                elif depth == 2 and t < -0.3 and v < 0.7:
                    c = 'sn_mid'
            # clumps of snow caught in the lit side of each tier
            if -0.9 < t < -0.1 and 0.35 < v < 0.8 and (hash2(x, y, 7 + ti) & 7) == 0:
                c = 'sn_lt'
            img.p[y][x] = c
    for y in range(32):
        for x in range(16):
            if owner[y][x] >= 0:
                continue
            for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < 16 and 0 <= yy < 32 and owner[yy][xx] >= 0:
                    img.p[y][x] = 'pn_out'
                    break
    trunk = G('''
    .TabcT.
    .TabcT.
    TTabcTT
    .TTTTT.
    ''', {'.': None, 'T': 'pn_out', 'a': 'k_lt', 'b': 'k_base', 'c': 'k_dk'})
    img.paste(trunk, 5, 26)
    return img


# ---------------------------------------------------------------------------
# icy ledge (drop to the south): snow lip, a face of ice with icicles
# ---------------------------------------------------------------------------

LIP_Y = 5
FACE = 4


def _ledge_column(x):
    col = {LIP_Y: 'sn_hi', LIP_Y + 1: 'sn_lt', LIP_Y + 2: 'sn_base' if x % 4 != 1 else 'sn_lt'}
    y = LIP_Y + 3
    col[y] = 'sn_dk'
    for i in range(FACE):
        c = 'ic_base'
        if i == 0:
            c = 'ic_hi' if x % 5 == 2 else 'ic_lt'
        elif x % 4 == 0:
            c = 'ic_lt'
        elif x % 4 == 3:
            c = 'ic_mid'
        if i == FACE - 1:
            c = 'ic_mid' if x % 3 else 'ic_dk'
        col[y + 1 + i] = c
    # icicles hanging off the face
    if x % 5 in (1, 3):
        col[y + 1 + FACE] = 'ic_lt' if x % 5 == 1 else 'ic_mid'
        col[y + 2 + FACE] = 'sn_dk'
    else:
        col[y + 1 + FACE] = 'sn_dk'
        col[y + 2 + FACE] = 'sn_mid' if x % 2 else 'sn_dk'
    col[y + 3 + FACE] = 'sn_mid'
    return col


def ledge_img(ends=None):
    img = Img(16, 16)
    tex_fill(img, SNOW_A)
    for x in range(16):
        for y, c in _ledge_column(x).items():
            if y < 16:
                img.p[y][x] = c
    if ends:
        prof = {0: None, 1: None, 2: None, 3: 3, 4: 1, 5: 0}
        for u, cut in prof.items():
            x = u if ends == 'L' else 15 - u
            for y in range(LIP_Y, 16):
                img.p[y][x] = SNOW_A.p[y][x]
            if cut is None:
                continue
            col = _ledge_column(x)
            for y, c in col.items():
                yy = y + cut
                if yy <= 15 - (1 if cut else 0) and y <= LIP_Y + 3 + FACE:
                    img.p[yy][x] = c
            img.p[LIP_Y + cut][x] = 'sn_hi' if cut < 3 else 'sn_lt'
            if cut >= 1:
                img.p[LIP_Y + cut - 1][x] = 'sn_lt'
            img.p[15][x] = 'sn_mid'
    return img


# ---------------------------------------------------------------------------
# granite cliffs and crags
# ---------------------------------------------------------------------------

ROCK_MAP = {'t_out': 'rk_out', 'k_lt': 'rk_lt', 'k_base': 'rk_base', 'k_dk': 'rk_dk'}


def cliff_face():
    img = rock_tex([(4, 2), (12, 3), (8, 9), (1, 10), (13, 13.5)], seed=3).replace(ROCK_MAP)
    # snow caught on the lit tops of the slabs
    for y in range(16):
        for x in range(16):
            if img.p[y][x] == 'rk_lt' and img.p[(y - 1) % 16][x] == 'rk_out' and hash2(x, y, 9) & 1:
                img.p[y][x] = 'sn_lt'
            elif img.p[y][x] == 'rk_lt' and (hash2(x, y, 11) & 7) == 0:
                img.p[y][x] = 'rk_hi'
    return img


CLIFF_FACE = cliff_face()


def cliff_img():
    img = CLIFF_FACE.copy()
    cap = G('''
    hhhlhhhhhhhlhhhh
    llllllllllllllll
    ....l.......l...
    m..mmm..mm.mmm.m
    dmmddmmmddmmddmd
    ''', dict(SN, **{'.': 'sn_base'}))
    img.paste(cap, 0, 0)
    for x in (2, 6, 11, 14):          # snow drips over the edge
        img.p[5][x] = 'sn_mid'
        if x % 2 == 0:
            img.p[6][x] = 'sn_dk'
    for x in range(16):
        if img.p[5][x] in ('rk_base', 'rk_dk'):
            img.p[5][x] = 'rk_out'
    return img


def crag_img():
    """A wind-carved snowbank: rounded mounds (solid), granite showing."""
    img = Img(16, 16)
    clumps = []
    for (cx, cy, rx, ry) in ((4.0, 5.0, 5.5, 4.5), (12.5, 6.5, 5.0, 4.0), (7.5, 12.5, 6.5, 4.0),
                             (15.0, 14.0, 4.0, 3.0), (-0.5, 13.0, 3.5, 3.0)):
        for ox in (-16, 0, 16):
            for oy in (-16, 0, 16):
                clumps.append((cx + ox, cy + oy, rx, ry))
    ramp = ['sn_hi', 'sn_lt', 'sn_base', 'sn_mid', 'sn_dk']
    cl, own = shade_clumps(16, 16, clumps, ramp, 'rk_dk', seed=5)
    for y in range(16):
        for x in range(16):
            img.p[y][x] = cl.p[y][x] or 'rk_dk'
    for (x, y, c) in ((9, 2, 'rk_base'), (10, 2, 'rk_dk'), (9, 3, 'rk_dk'), (2, 10, 'rk_lt'),
                      (3, 10, 'rk_base'), (3, 11, 'rk_dk'), (13, 11, 'rk_base')):
        img.p[y][x] = c
    return img


def stone_img():
    """Slate cobbles with snow packed into the joints."""
    img = Img(16, 16, 'rk_lt')
    stones = [(0, 0, 7, 5), (8, 0, 15, 4), (0, 6, 4, 10), (5, 6, 11, 11), (12, 5, 15, 10),
              (0, 11, 3, 15), (4, 12, 9, 15), (10, 12, 15, 15)]
    for y in range(16):
        for x in range(16):
            img.p[y][x] = 'sn_lt'
    for (x0, y0, x1, y1) in stones:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if y == y1 or x == x1:
                    c = 'sn_base' if (x + y) % 3 else 'sn_mid'
                elif y == y0 or x == x0:
                    c = 'rk_hi'
                elif y == y1 - 1 or x == x1 - 1:
                    c = 'rk_base'
                else:
                    c = 'rk_lt'
                    if (hash2(x, y, 13) & 15) == 0:
                        c = 'rk_base'
                img.p[y][x] = c
    return img


# ---------------------------------------------------------------------------
# ice (A_ICE) with a snowy rim, and rocks frozen into it
# ---------------------------------------------------------------------------

def ice_tex():
    img = Img(16, 16, 'ic_base')
    for y in range(16):
        for x in range(16):
            u = (x + y) % 16
            if u in (3, 4):
                img.p[y][x] = 'ic_lt'
            elif u == 11:
                img.p[y][x] = 'ic_lt' if (x % 4) else 'ic_base'
            if (x - y) % 16 == 9 and 2 < x < 13:
                img.p[y][x] = 'ic_hi' if u in (3, 4) else 'ic_lt'
    for (x, y) in ((2, 12), (3, 12), (4, 13), (5, 13), (6, 14), (12, 3), (13, 4), (13, 5)):
        img.p[y][x] = 'ic_mid'
    for (x, y) in ((4, 4), (10, 9)):
        img.p[y][x] = 'ic_hi'
    return img


ICE_TEX = ice_tex()


def ice_cell(n, s, w, e):
    """A 16x16 ice cell whose edges n/s/w/e border snow (rounded corners)."""
    img = Img(16, 16)
    E0, R = 3.0, 6.0
    for y in range(16):
        for x in range(16):
            dx, dy, lit = 99.0, 99.0, 0
            if w:
                dx = x + 0.5
            if e and 16 - (x + 0.5) < dx:
                dx = 16 - (x + 0.5)
            if n:
                dy = y + 0.5
            if s and 16 - (y + 0.5) < dy:
                dy = 16 - (y + 0.5)
            ax, ay = R - dx, R - dy
            if ax > 0 and ay > 0:
                v = R - math.hypot(ax, ay)
            else:
                v = min(dx, dy)
            # which side lights the rim: snow banks on the north/west cast
            # shade on the ice, south/east rims catch the light
            near_nw = (n and dy == y + 0.5 and dy <= dx) or (w and dx == x + 0.5 and dx < dy)
            if v < E0 - 1.0:
                c = SNOW_A.p[y][x]
            elif v < E0:
                c = 'sn_hi' if near_nw else 'sn_lt'
            elif v < E0 + 1.0:
                c = 'sn_dk' if near_nw else 'ic_hi'
            elif v < E0 + 2.0 and near_nw:
                c = 'ic_mid'
            else:
                c = ICE_TEX.p[y][x]
            img.p[y][x] = c
    return img


def ice_rock():
    img = ICE_TEX.copy()
    # shade on the ice to the lower right
    for (x, y) in ((12, 13), (13, 13), (13, 12), (11, 14), (12, 14), (13, 14), (14, 13), (14, 12)):
        img.p[y][x] = 'ic_mid'
    clumps = [(7.5, 8.5, 6.0, 5.0), (10.5, 10.5, 3.5, 3.0), (4.5, 10.5, 3.5, 3.0)]
    rock, own = shade_clumps(16, 16, clumps, ['rk_hi', 'rk_lt', 'rk_base', 'rk_dk'], 'rk_out',
                             seed=9, clip=lambda x, y: 1 <= x <= 14 and 2 <= y <= 14)
    img.paste(rock, 0, 0)
    cap = G('''
    ...hhhh...
    .hhllllh..
    hllllmm...
    .mm...m...
    ''', dict(SN, **{'.': None}))
    img.paste(cap, 3, 3)
    return img


# ---------------------------------------------------------------------------
# sea of clouds (Sky Isle)
# ---------------------------------------------------------------------------

def cloud_img():
    clumps = []
    for (cx, cy, rx, ry) in ((4.0, 4.0, 5.0, 4.0), (12.0, 7.0, 5.5, 4.5), (5.0, 12.0, 6.0, 4.5),
                             (14.0, 15.0, 4.5, 3.5)):
        for ox in (-16, 0, 16):
            for oy in (-16, 0, 16):
                clumps.append((cx + ox, cy + oy, rx, ry))
    ramp = ['sn_hi', 'sn_hi', 'sn_lt', 'sn_base', 'sn_mid']
    cl, own = shade_clumps(16, 16, clumps, ramp, 'sn_dk', seed=21, dither=False)
    img = Img(16, 16)
    for y in range(16):
        for x in range(16):
            img.p[y][x] = cl.p[y][x] or 'sn_dk'
    return img


# ---------------------------------------------------------------------------
# the Rime Hall inside
# ---------------------------------------------------------------------------

def hall_floor():
    img = Img(16, 16, 'rk_lt')
    for y in range(16):
        for x in range(16):
            if y == 15 or x == 15:
                c = 'rk_dk'
            elif y == 0 or x == 0:
                c = 'rk_hi'
            elif y == 14 or x == 14:
                c = 'rk_base'
            else:
                c = 'rk_lt'
                h = hash2(x, y, 3) & 31
                if h == 0:
                    c = 'rk_base'
                elif h == 1:
                    c = 'rk_hi'
            img.p[y][x] = c
    # a frost star cut into the middle of each flagstone
    for (x, y) in ((7, 5), (7, 6), (7, 8), (7, 9), (5, 7), (6, 7), (8, 7), (9, 7)):
        img.p[y][x] = 'ic_lt'
    img.p[7][7] = 'ic_hi'
    return img


def ice_bricks(y0=0, rows=16):
    img = Img(16, rows)
    for y in range(rows):
        for x in range(16):
            yy = y0 + y
            r = yy % 8
            off = 0 if (yy // 8) % 2 == 0 else 8
            bx = (x + off) % 16
            if r == 7 or bx == 15:
                c = 'rk_dk'
            elif r == 0 or bx == 0:
                c = 'ic_hi'
            elif r == 6 or bx == 14:
                c = 'ic_base'
            else:
                c = 'ic_lt'
                if (bx + r) % 7 == 3:
                    c = 'ic_hi'
            img.p[y][x] = c
    return img


def hall_wall_top():
    img = ice_bricks()
    for x in range(16):
        img.p[0][x] = 'rk_out'
        img.p[1][x] = 'rk_base'
    return img


def hall_wall():
    img = ice_bricks()
    for y in range(8, 16):
        for x in range(16):
            if y == 8:
                c = 'rk_hi'
            elif y == 9:
                c = 'rk_lt'
            elif y == 15:
                c = 'rk_out'
            elif y == 14:
                c = 'rk_dk'
            else:
                c = 'rk_base' if (x + y) % 6 else 'rk_lt'
                if x % 8 == 7:
                    c = 'rk_dk'
            img.p[y][x] = c
    return img


def hall_mat():
    img = hall_floor()
    mat = G('''
    OOOOOOOOOOOOOO
    OlllllllllllmO
    OlbbbbbbbbbbmO
    OlbbbbhbbbbbmO
    OlbbbhhhbbbbmO
    OlbbbbhbbbbbmO
    OlbbbbbbbbbbmO
    OmmmmmmmmmmmmO
    OOOOOOOOOOOOOO
    ''', {'O': 'rk_out', 'l': 'ic_lt', 'b': 'ic_mid', 'h': 'ic_hi', 'm': 'ic_dk'})
    img.paste(mat, 1, 4)
    return img


# ---------------------------------------------------------------------------
# buildings (stamps): log houses with snowy roofs and warm windows
# ---------------------------------------------------------------------------

BLD = {'.': None, 'O': 'b_out', 'A': 'wd_lt', 'B': 'wd_base', 'K': 'wd_dk', 'H': 'st_hi',
       'L': 'st_lt', 'M': 'st_mid', 'a': 'lw_hi', 'b': 'lw_base', 'c': 'lw_dk',
       's': 'sn_hi', 'S': 'sn_lt', 'g': 'sn_base', 'G': 'sn_mid'}

WINDOW = G('''
OOOOOOOOOOOOOO
OAAAAAAAAAAAAO
OAccccAAccccKO
OAcaabAAcbbbKO
OAcabbAAcbbbKO
OAcbbbAAcbabKO
OAAAAAAAAAAAKO
OAcbbbAAcbbbKO
OAcbbbAAcabbKO
OAcbbbAAcbbbKO
OAKKKKKKKKKKKO
OOOOOOOOOOOOOO
.sSSsSSSsSSSs.
''', BLD)

DOOR = G('''
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
''', BLD)

GLASS_DOOR = G('''
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
''', BLD)

STEP = G('''
OOOOOOOOOOOOOOOO
OHHHHHHHHHHHHHHO
OLLLLLLLLLLLLLLO
OOOOOOOOOOOOOOOO
.OHHHHHHHHHHHHO.
.OLLLLLLLLLLLLO.
.OMMMMMMMMMMMMO.
.OOOOOOOOOOOOOO.
''', BLD)

CURTAIN_DOOR = G('''
OOOOOOOOOOOOOO
OAAAAAAAAAAAAO
OAOOOOOOOOOOKO
OAObbbbObbbbKO
OAObbabObabbKO
OAObbbbObbbbKO
OAObcbbObbcbKO
OAObbbbObbbbKO
OAOcccOOOcccKO
OAOKKKKKKKKOKO
OAOKBBBBBBKOKO
OAOKBBBBBBKOKO
OAOKBBBBBBKOKO
OAOKBBBBBBKOKO
OAOKBBBBBBKOKO
OAOKBBBBBBKOKO
OAOKKKKKKKKOKO
OOOOOOOOOOOOOO
''', BLD)

ROOF_R = {'1': 'rf_hi', '2': 'rf_lt', '3': 'rf_base', '4': 'rf_dk', '5': 'rf_dkr'}


def draw_roof(img, xl0, xr0, y0, y1, inset, R, joint=8):
    """Hip roof seen from the front/top (gen_field_gfx.draw_roof)."""
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
            else:
                n, rr = r // 4, r % 4
                if rr == 0:
                    c = R['2']
                elif rr == 3:
                    c = R['4']
                else:
                    c = R['3']
                    if (x + 4 * (n % 2)) % joint == 0:
                        c = R['4']
            img.set(x, y, c)


def snow_on_roof(img, xl0, xr0, y0, y1, inset, depth):
    """Heap snow over the upper part of a roof: a soft wavy lower edge,
    lit from the top-left, with icicles along the eave."""
    H = y1 - y0
    for x in range(xl0, xr0 + 1):
        wave = 1.6 * math.sin(x * 0.55) + 1.1 * math.sin(x * 0.23 + 1.0)
        bottom = int(round(y0 + depth + wave))
        for y in range(y0, min(bottom, y1 - 3) + 1):
            k = int(round(inset * (y1 - y) / float(H)))
            xl, xr = xl0 + k, xr0 - k
            if x < xl or x > xr:
                continue
            if y == y0 or x == xl or x == xr:
                c = 'b_out'
            elif y == bottom:
                c = 'sn_dk'
            elif y == bottom - 1:
                c = 'sn_mid'
            elif y <= y0 + 2 or x <= xl + 2:
                c = 'sn_hi'
            elif x >= xr - 3:
                c = 'sn_base'
            else:
                c = 'sn_lt'
                if (hash2(x, y, 33) & 15) == 0:
                    c = 'sn_hi'
            img.set(x, y, c)
    # icicles under the eave
    for x in range(xl0 + 3, xr0 - 2):
        if x % 7 in (0, 3):
            img.set(x, y1 + 1, 'ic_lt')
            if x % 7 == 0:
                img.set(x, y1 + 2, 'ic_lt')


def log_wall(img, x0, x1, y0, y1):
    for y in range(y0, y1 + 1):
        r = (y - y0) % 4
        for x in range(x0, x1 + 1):
            c = 'wd_base'
            if r == 0:
                c = 'wd_lt'
            elif r == 3:
                c = 'wd_dk'
            elif (x * 7 + (y - y0) // 4 * 13) % 23 == 0:
                c = 'wd_dk'
            img.set(x, y, c)


def cabin_body(W_, H_):
    """Ground, log walls, stone foundation and the ground shadow of a
    W_ x H_ building; the roof covers rows 5..31 (tile aligned)."""
    img = Img(W_, H_, 'sn_base')
    for x in range(7, W_ - 2):
        img.set(x, H_ - 4, 'sn_mid')
        if 8 <= x <= W_ - 4:
            img.set(x, H_ - 3, 'sn_mid')
    log_wall(img, 5, W_ - 6, 32, H_ - 9)
    for y in range(32, H_ - 4):
        img.set(4, y, 'b_out')
        img.set(W_ - 5, y, 'b_out')
        img.set(5, y, 'wd_lt')
        img.set(6, y, 'wd_base')
        img.set(W_ - 7, y, 'wd_base')
        img.set(W_ - 6, y, 'wd_dk')
    for x in range(4, W_ - 4):
        img.set(x, H_ - 8, 'b_out')
        img.set(x, H_ - 5, 'b_out')
        for y in (H_ - 7, H_ - 6):
            c = 'st_lt' if y == H_ - 7 else 'st_mid'
            if (x + (4 if y == H_ - 6 else 0)) % 8 == 0:
                c = 'st_mid' if y == H_ - 7 else 'b_out'
            img.set(x, y, c)
    # eave shadow
    for x in range(5, W_ - 5):
        img.set(x, 32, 'wd_dk')
        img.set(x, 33, 'wd_dk' if x % 2 == 0 else 'wd_base')
    # snow piled against the foundation
    for x in range(4, W_ - 4):
        if hash2(x, 1, 3) & 1:
            img.set(x, H_ - 5, 'sn_lt')
    return img


def medallion(symbol):
    """A round stone plaque (roof bank) with a flame or a hot-spring mark."""
    base = G('''
    ....OOOOOOO....
    ..OOHHHHHHHOO..
    .OHHLLLLLLLLMO.
    .OHLLLLLLLLLMO.
    OHLLLLLLLLLLLMO
    OHLLLLLLLLLLLMO
    OHLLLLLLLLLLLMO
    OHLLLLLLLLLLLMO
    OHLLLLLLLLLLLMO
    OHLLLLLLLLLLLMO
    OHLLLLLLLLLLLMO
    .OHLLLLLLLLLMO.
    .OMLLLLLLLLMMO.
    ..OOMMMMMMMOO..
    ....OOOOOOO....
    ''', {'.': None, 'O': 'b_out', 'H': 'st_hi', 'L': 'st_lt', 'M': 'st_mid'})
    if symbol == 'flame':
        mark = G('''
        ...3....
        ..32....
        ..323.3.
        .32223..
        .321123.
        3211123.
        3211123.
        .32223..
        ..333...
        ''', {'.': None, '1': 'rf_hi', '2': 'rf_lt', '3': 'rf_base'})
        base.paste(mark, 4, 3)
    else:
        # the hot-spring mark: a basin with three rising curls of steam
        mark = G('''
        .3..3..3..
        3..3..3...
        .3..3..3..
        ..3..3..3.
        .3..3..3..
        ..........
        3........3
        33......33
        .33333333.
        ''', {'.': None, '3': 'rf_base'})
        base.paste(mark, 2, 3)
    return base


def plate(text, ink='b_out'):
    """A stone name plate (gen_field_gfx.sign_plate) in the roof bank."""
    FONT = {
        'C': ['.###', '#...', '#...', '#...', '.###'],
        'M': ['#..#', '####', '####', '#..#', '#..#'],
        'I': ['.##.', '.##.', '.##.', '.##.', '.##.'],
        'E': ['####', '#...', '###.', '#...', '####'],
        'R': ['###.', '#..#', '###.', '#.#.', '#..#'],
        'S': ['.###', '#...', '.##.', '...#', '###.'],
        'H': ['#..#', '#..#', '####', '#..#', '#..#'],
        'O': ['.##.', '#..#', '#..#', '#..#', '.##.'],
        'P': ['###.', '#..#', '###.', '#...', '#...'],
    }
    w = len(text) * 5 - 1 + 6
    img = Img(w, 9)
    for y in range(9):
        for x in range(w):
            if y in (0, 8) or x in (0, w - 1):
                c = 'b_out'
            elif y == 7 or x == w - 2:
                c = 'st_lt'
            else:
                c = 'st_hi'
            img.p[y][x] = c
    for i, ch in enumerate(text):
        for yy, row in enumerate(FONT[ch]):
            for xx, px in enumerate(row):
                if px == '#':
                    img.p[2 + yy][3 + i * 5 + xx] = ink
    return img


CHIMNEY = G('''
OOOOOOOOO
OssssssSO
OSSSSSSGO
OOOOOOOOO
.OHLLLMO.
.OLMLLMO.
.OLLLMLO.
.OLMLLMO.
.OLLMLLO.
.OOOOOOO.
''', dict(BLD, G='sn_mid'))


def snow_cottage(kind='house'):
    """80x64 stamp (5x4 metatiles)."""
    img = cabin_body(80, 64)
    for wx in (9, 57):
        img.paste(WINDOW, wx, 38)
    if kind in ('house',):
        img.paste(DOOR, 33, 38)
    elif kind == 'baths':
        img.paste(CURTAIN_DOOR, 33, 38)
    else:
        img.paste(GLASS_DOOR, 32, 42)
    img.paste(STEP, 32, 56)
    draw_roof(img, 1, 78, 5, 31, 5, ROOF_R)
    snow_on_roof(img, 1, 78, 5, 31, 5, 15)
    if kind == 'house':
        img.paste(CHIMNEY, 58, 0)
    elif kind == 'hearth':
        img.paste(medallion('flame'), 33, 11)
    elif kind == 'baths':
        img.paste(medallion('spring'), 33, 11)
    elif kind == 'shop':
        img.paste(plate('SHOP'), 28, 22)
    return img


# ---- the Rime Hall: granite and ice ----------------------------------------

HALL_L = {'.': None, 'O': 'rk_out', 'H': 'rk_hi', 'L': 'rk_lt', 'B': 'rk_base', 'D': 'rk_dk',
          'a': 'ic_hi', 'b': 'ic_lt', 'c': 'ic_base', 'd': 'ic_mid', 'e': 'ic_dk',
          's': 'sn_hi', 'S': 'sn_lt', 'g': 'sn_base', 'G': 'sn_mid'}

ICE_WINDOW = G('''
....OOOOOOOO....
..OOaabbbbccOO..
.OabbbbbcccccdO.
.OabbbObccOccdO.
OabbbbObccOcccdO
OOOOOOOOOOOOOOOO
ObbbbbObccOcccdO
ObbbbbObccOcccdO
ObbcbbObccOcccdO
OcbbbbObccOccddO
OOOOOOOOOOOOOOOO
OHHHHHHHHHHHHHHO
OOOOOOOOOOOOOOOO
''', HALL_L)

HALL_DOOR = G('''
.....OOOOOO.....
...OOaabbbcOO...
..ObbbbbccccdO..
.ObbbbbOcccccdO.
.ObbbbbOcccccdO.
ObbbbbbOccccccdO
ObbabbbOcccccddO
ObbbbbbOcccacddO
ObbbbbbOccccccdO
ObbbbbHOHcccccdO
ObbbbbbOccccccdO
ObbbbbbOccccccdO
ObbbcbbOcccccddO
ObbbbbbOccccccdO
ObbbbbbOccccdcdO
OddddddOddddddeO
OOOOOOOOOOOOOOOO
''', HALL_L)

CREST = G('''
.......OO.......
.....OOaaOO.....
...O..ObbO..O...
..OaO.ObbO.OaO..
..ObbOObbOObbO..
...ObbbbbbbbO...
OOOOObbaabbOOOOO
OaabbbaHHabbbaaO
OOOOObbaabbOOOOO
...ObbbbbbbbO...
..ObbOObbOObbO..
..OaO.ObbO.OaO..
...O..ObbO..O...
.....OOddOO.....
.......OO.......
''', HALL_L)


def granite_wall(img, x0, x1, y0, y1):
    for y in range(y0, y1 + 1):
        r = (y - y0) % 8
        row = (y - y0) // 8
        for x in range(x0, x1 + 1):
            bx = (x - x0 + (8 if row % 2 else 0)) % 16
            if r == 7 or bx == 15:
                c = 'rk_dk'
            elif r == 0 or bx == 0:
                c = 'rk_hi'
            elif r == 6:
                c = 'rk_base'
            else:
                c = 'rk_lt'
                if (x * 5 + y * 3) % 17 == 0:
                    c = 'rk_base'
            img.set(x, y, c)


def rime_hall():
    """112x80 stamp (7x5 metatiles): granite walls, ice windows and door,
    a snowed-under roof and the snowflake crest of the Rime Hall."""
    W_, H_ = 112, 80
    img = Img(W_, H_, 'sn_base')
    for x in range(7, W_ - 2):
        img.set(x, H_ - 4, 'sn_mid')
        if 8 <= x <= W_ - 4:
            img.set(x, H_ - 3, 'sn_mid')
    granite_wall(img, 5, W_ - 6, 32, H_ - 5)
    for y in range(32, H_ - 4):
        img.set(4, y, 'rk_out')
        img.set(W_ - 5, y, 'rk_out')
    for x in range(4, W_ - 4):
        img.set(x, H_ - 5, 'rk_out')
    for x in range(5, W_ - 5):
        img.set(x, 32, 'rk_dk')
        img.set(x, 33, 'rk_base' if x % 2 else 'rk_dk')
    for wx in (10, 86):
        img.paste(ICE_WINDOW, wx, 44)
    for wx in (30, 66):
        img.paste(ICE_WINDOW, wx, 44)
    img.paste(HALL_DOOR, 48, 59)
    img.paste(CREST, 48, 38)
    # snow heaped along the foundation
    for x in range(5, W_ - 5):
        if not (48 <= x < 64):
            img.set(x, H_ - 6, 'sn_lt' if hash2(x, 2, 5) & 1 else 'sn_base')
    # the roof: slate eaves under deep snow
    R = {'1': 'st_hi', '2': 'st_hi', '3': 'st_lt', '4': 'st_mid', '5': 'st_mid'}
    draw_roof(img, 1, W_ - 2, 5, 31, 5, R)
    snow_on_roof(img, 1, W_ - 2, 5, 31, 5, 16)
    img.paste(plate('RIME'), 43, 21)
    return img


def cave_mouth():
    """48x32 stamp (3x2): a cave opening in a snow-capped granite face.
    The top row matches CLIFF, the bottom row CLIFF_FACE."""
    img = Img(48, 32)
    tex_fill(img, CLIFF_FACE)
    cap = cliff_img()
    for x0 in (0, 16, 32):
        img.paste(cap.crop(0, 0, 16, 8), x0, 0)
    # the arch: dark inside, a lit rim, icicles along the top
    cx, top = 24.0, 11.0
    for y in range(8, 32):
        for x in range(48):
            dx = (x + 0.5 - cx) / 13.0
            dy = (y + 0.5 - 32.0) / (32.0 - top)
            d = dx * dx + dy * dy
            if d <= 1.0:
                if d > 0.78:
                    c = 'rk_dk'
                elif d > 0.62:
                    c = 'rk_out'
                else:
                    c = 'rk_out'
                img.p[y][x] = c
            elif d <= 1.18:
                img.p[y][x] = 'rk_hi' if x < cx else 'rk_base'
    for (x, n) in ((17, 3), (20, 2), (24, 4), (28, 2), (31, 3)):
        yy = int(top + 1 + abs(x - cx) * 0.35)
        for i in range(n):
            img.set(x, yy + i, 'ic_lt' if i < n - 1 else 'ic_hi')
    # a trodden floor spilling out of the mouth
    for y in range(28, 32):
        for x in range(18, 30):
            if img.p[y][x] == 'rk_out' and (x + y) % 3 == 0:
                img.p[y][x] = 'rk_dk'
    return img


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def images():
    drift_b, drift_t = drift_layers()
    pine = snowy_pine()
    return {
        'SNOW': (SNOW_A.copy(), None), 'SNOW2': (SNOW_B.copy(), None), 'SNOW3': (SNOW_C.copy(), None),
        'DRIFT': (drift_b, drift_t),
        'PINE_TOP': (pine.crop(0, 0, 16, 16), None), 'PINE_BOTTOM': (pine.crop(0, 16, 16, 16), None),
        'LEDGE': (ledge_img(), None), 'LEDGE_L': (ledge_img('L'), None), 'LEDGE_R': (ledge_img('R'), None),
        'CLIFF': (cliff_img(), None), 'CLIFF_FACE': (CLIFF_FACE.copy(), None), 'CRAG': (crag_img(), None),
        'STONE': (stone_img(), None),
        'ICE': (ICE_TEX.copy(), None),
        'ICE_N': (ice_cell(1, 0, 0, 0), None), 'ICE_S': (ice_cell(0, 1, 0, 0), None),
        'ICE_W': (ice_cell(0, 0, 1, 0), None), 'ICE_E': (ice_cell(0, 0, 0, 1), None),
        'ICE_NW': (ice_cell(1, 0, 1, 0), None), 'ICE_NE': (ice_cell(1, 0, 0, 1), None),
        'ICE_SW': (ice_cell(0, 1, 1, 0), None), 'ICE_SE': (ice_cell(0, 1, 0, 1), None),
        'ICE_ROCK': (ice_rock(), None), 'CLOUD': (cloud_img(), None),
        'HALL_FLOOR': (hall_floor(), None), 'HALL_WALL_TOP': (hall_wall_top(), None),
        'HALL_WALL': (hall_wall(), None), 'HALL_MAT': (hall_mat(), None),
        'VOID': (Img(16, 16, 'rk_out'), None),
    }


BANKS = [
    NP.SNOW_BANK_GROUND,           # 0 snow, drifts, path, ledges, ice
    NP.SNOW_BANK_WATER,            # 1 icy water and its shore
    NP.SNOW_BANK_PINES,            # 2 snowy pines
    decor_outdoor.TOWN_DECOR_BANK,  # 3 village props
    NP.NORTH_DECOR_BANK,           # 4 north decor
    NP.SNOW_BANK_ROOF,             # 5 snowy roofs, chimneys, plaques
    NP.SNOW_BANK_ROCK,             # 6 granite, cliffs, the Rime Hall
    NP.SNOW_BANK_WALLS,            # 7 log walls, warm windows, doors
]

PREFER = {'PINE_TOP': (2,), 'PINE_BOTTOM': (2,)}
ROCKY = ('CLIFF', 'CLIFF_FACE', 'CRAG', 'STONE', 'ICE_ROCK', 'HALL_FLOOR', 'HALL_WALL_TOP',
         'HALL_WALL', 'HALL_MAT', 'VOID')


def build(gf, name):
    gf.register_colors(NP.NORTH_COLORS)
    gf.check_banks(name, BANKS)
    ts = gf.TileSet(name, BANKS)
    out = {'ts': ts, 'meta_b': [], 'meta_t': [], 'terrain': TERRAIN}
    add_water(gf, ts, out, bank=1)
    imgs = images()
    for t in TERRAIN:
        bottom, top = imgs[t]
        if t in OVERLAY:
            gf.add_overlay_terrain(ts, out, t, bottom, top=t.endswith('_TOP'))
            continue
        pref = (6,) if t in ROCKY else (0,)
        out['meta_b'].append(ts.meta(bottom, prefer=pref, where='snow.' + t))
        out['meta_t'].append(ts.meta(top, prefer=(0,), where='snow.%s.top' % t, opaque=False)
                             if top else [0, 0, 0, 0])
    gf.add_stamps(ts, out, [
        ('HOUSE', snow_cottage('house'), (7, 5), 'log house with a snowy roof, door col 2 row 3'),
        ('HEARTH', snow_cottage('hearth'), (7, 5), 'HEARTH HALL (flame plaque), door col 2 row 3'),
        ('SHOP', snow_cottage('shop'), (7, 5), 'FROST SHOP, door col 2 row 3'),
        ('BATHS', snow_cottage('baths'), (7, 5), 'hot spring bathhouse gate, door col 2 row 3'),
        ('HALL', rime_hall(), (6, 5), 'RIME HALL, door col 3 row 4'),
        ('CAVE', cave_mouth(), (6,), 'cave mouth in a cliff (top row = CLIFF), door col 1 row 1'),
    ])
    out['path_q'] = [[ts.add(gf.img_pix(q), (0,), 'snow.path[%d][%d]' % (c, v))
                      for v, q in enumerate(row)] for c, row in enumerate(path_quads())]
    ice = ['ICE', 'ICE_N', 'ICE_S', 'ICE_W', 'ICE_E', 'ICE_NW', 'ICE_NE', 'ICE_SW', 'ICE_SE']
    attrs = {'DRIFT': gf.A_GRASS, 'LEDGE': gf.A_LEDGE, 'LEDGE_L': gf.A_LEDGE, 'LEDGE_R': gf.A_LEDGE,
             'CLIFF': gf.A_SOLID, 'CLIFF_FACE': gf.A_SOLID, 'CRAG': gf.A_SOLID,
             'ICE_ROCK': gf.A_SOLID, 'CLOUD': gf.A_SOLID, 'HALL_WALL_TOP': gf.A_SOLID,
             'HALL_WALL': gf.A_SOLID, 'VOID': gf.A_SOLID, 'HALL_MAT': gf.A_EXIT}
    for n in ice:
        attrs[n] = gf.A_ICE
    out = gf.finish_tileset(
        out, name, 'SN', attrs=attrs,
        ground=['SNOW', 'SNOW2', 'SNOW3'], overlay=list(OVERLAY),
        legend={'.': [('SNOW3', 2), ('SNOW2', 3), ('SNOW', 11)], ',': 'DRIFT', '=': 'PATH',
                '~': 'WATER', 'P': 'PINE_TOP', 'p': 'PINE_BOTTOM', 'L': 'LEDGE', '[': 'LEDGE_L',
                ']': 'LEDGE_R', 'C': 'CLIFF', 'c': 'CLIFF_FACE', 'R': 'CRAG', '#': 'STONE',
                'i': 'ICE', '8': 'ICE_N', '2': 'ICE_S', '4': 'ICE_W', '6': 'ICE_E',
                '7': 'ICE_NW', '9': 'ICE_NE', '1': 'ICE_SW', '3': 'ICE_SE', 'o': 'ICE_ROCK',
                'K': 'CLOUD', 'F': 'HALL_FLOOR', 'W': 'HALL_WALL_TOP', 'w': 'HALL_WALL',
                'D': 'HALL_MAT', ' ': 'VOID'},
        oob='PINE_TOP', default_ground='SNOW', backdrop='ground',
        doors=[('HOUSE', 2, 3), ('HEARTH', 2, 3), ('SHOP', 2, 3), ('BATHS', 2, 3), ('HALL', 3, 4),
               ('CAVE', 1, 1)])
    out['docs'] = DOC
    return out
