"""The 'cave' tileset (owner: W-NORTH): Glimmer Caverns (two floors) and the
Starfall Grotto.

Map legend (documented again at the top of src/game/world/north/data.h):

  .  cave floor (+ pebbles, crystal grit)   ,  glowmoss (wild kin; top layer hides legs)
  =  trodden gravel path (autotiled)        ~  underground lake (autotiled, animated)
  X  rock mass (the cave roof, solid)       c  rock wall face (solid; below X)
  Q  crystal vein in the wall face (solid)  *  crystal outcrop on the floor (solid)
  L  rock ledge (hop down)   [ ]  ledge ends
  D  exit mat: daylight at the cave mouth (A_EXIT)
  7 8 9 / 4 5 6 / 1 2 3  the starlit pool of the Starfall Grotto (solid), numpad
     layout with a stone rim: 5 is open water, 7 = north-west corner ...
  ' ' void (outside the cave)

Stamps (STAMP(CV, NAME, x, y)), all 1x1 door cells entered from the south:
STAIRS_DOWN (a stair well going down), STAIRS_UP (wooden steps up into the
rock), CRACK (a narrow fissure glowing violet: the way to the grotto).

Palette banks come from tools/north_palette.py (CAVE_BANK_*); bank 3 is the
village props bank so bridges, signposts, crates and barrels work here too.
"""

import math
from pixelart import Img, G, hash2, shade_clumps
from terrain_common import autotile
from terrain_wild import rock_tex
import north_palette as NP
import decor_outdoor

USES_DECOR = ['SIGNPOST', 'SIGN_ARROW', 'BRIDGE_H', 'BRIDGE_V', 'CRATE', 'CRATE_STACK', 'BARREL',
              'SACKS', 'LOG', 'CAMPFIRE', 'PEBBLES', 'ROCK', 'BOULDER', 'LANTERN_POST',
              'RAILS_H', 'RAILS_V', 'ORE_CART', 'ORE_PILE']

TERRAIN = [
    'FLOOR', 'FLOOR2', 'FLOOR3', 'MOSS', 'ROCK', 'WALL', 'WALL_CRYSTAL', 'CRYSTAL',
    'LEDGE', 'LEDGE_L', 'LEDGE_R', 'MOUTH', 'VOID',
    'POOL', 'POOL_N', 'POOL_S', 'POOL_W', 'POOL_E', 'POOL_NW', 'POOL_NE', 'POOL_SW', 'POOL_SE',
]

DOC = {
    'FLOOR': 'cave floor (+ FLOOR2 crystal grit, FLOOR3 pebbles and a crack)',
    'MOSS': 'glowmoss carpet: wild kin roam here; top layer hides legs',
    'ROCK': 'rock mass, the cave roof seen from above (solid)',
    'WALL': 'rock wall face (solid); put it on the floor side below ROCK',
    'WALL_CRYSTAL': 'wall face with a glowing crystal vein (solid)',
    'CRYSTAL': 'crystal outcrop growing out of the floor (solid)',
    'LEDGE': 'rock ledge: walk DOWN onto it to hop over; tiles horizontally',
    'MOUTH': 'exit mat: daylight and blown-in snow at the cave mouth (A_EXIT)',
    'VOID': 'outside the cave',
    'POOL': 'the starlit pool of the Starfall Grotto (solid); POOL_* have a stone rim',
}

# floor colours: cv_lt .. cv_dkr (no cv_hi, so floor, walls and ledges share bank 2)
FL = {'.': 'cv_base', 'l': 'cv_lt', 'm': 'cv_mid', 'd': 'cv_dk', 'D': 'cv_dkr',
      'a': 'cr_hi', 'b': 'cr_lt', 'c': 'cr_base', 'p': 'am_lt', 'P': 'am_base'}

FLOOR_A = G('''
................
..........m.....
...............l
....mm..........
...m..m.........
..........l.....
.........ldm....
..........m.....
.m..............
................
......m.........
.....m.m.....m..
..............m.
..l.............
.ldm............
..m.......m.....
''', FL)

FLOOR_B = G('''
................
...b............
..bac...........
...c.......m....
..........m.....
................
.......m........
................
...........p....
..........pP....
....m.....P.....
................
.b..............
.c.......m......
.........mm.....
................
''', FL)

FLOOR_C = G('''
................
....ll..........
...lmmd.........
....dd..........
..........D.....
...........D....
...........dD...
............D...
.....m.......D..
..............d.
................
..ll............
.lmmd......l....
..dd......ldm...
...........m....
................
''', FL)


# ---------------------------------------------------------------------------
# glowmoss (wild kin roam here)
# ---------------------------------------------------------------------------

MT = {'.': None, 'O': 'cv_dkr', 'd': 'mo_dk', 'm': 'mo_base', 'h': 'mo_hi', 'g': 'cr_lt'}
MOSS_TUFT = G('''
..h...h.
.hmO.hmd
.hmmdhmm
hmmmdmmd
mmmddmmd
mmddmddd
dddddddO
OdOddOdO
''', MT)


def moss_layers():
    back = FLOOR_A.copy()
    for y in range(16):
        for x in range(16):
            if (hash2(x, y, 57) & 7) == 0:
                back.p[y][x] = 'mo_dk'
    for ox in (-4, 4, 12):
        back.paste(MOSS_TUFT, ox, 1)
    front = Img(16, 16)
    for ox in (0, 8):
        front.paste(MOSS_TUFT, ox, 8)
    bottom = back.copy()
    bottom.paste(front, 0, 0)
    # a few spores glowing between the tufts
    for (x, y) in ((3, 6), (11, 3), (14, 12)):
        bottom.p[y][x] = 'cr_lt'
    top = Img(16, 16)
    for y in range(9, 16):
        for x in range(16):
            ty = y - 8
            c = MOSS_TUFT.p[ty][x % 8]
            if c is None or (ty <= 3 and c in ('cv_dkr', 'mo_dk')):
                continue
            top.p[y][x] = c
    return bottom, top


# ---------------------------------------------------------------------------
# rock mass (the cave roof), wall faces, crystal
# ---------------------------------------------------------------------------

def rock_mass():
    """Rounded knuckles of dark rock (wraps seamlessly)."""
    clumps = []
    for (cx, cy, rx, ry) in ((4.0, 4.0, 5.0, 4.5), (12.0, 5.5, 5.5, 4.5), (7.0, 12.0, 6.0, 4.5),
                             (15.5, 14.0, 4.0, 3.5), (0.0, 12.5, 3.5, 3.5)):
        for ox in (-16, 0, 16):
            for oy in (-16, 0, 16):
                clumps.append((cx + ox, cy + oy, rx, ry))
    ramp = ['cw_lt', 'cw_base', 'cw_base', 'cw_dk', 'cw_dk']
    cl, own = shade_clumps(16, 16, clumps, ramp, 'cw_out', seed=31)
    img = Img(16, 16)
    for y in range(16):
        for x in range(16):
            img.p[y][x] = cl.p[y][x] or 'cw_out'
    return img


WALL_MAP = {'t_out': 'cw_out', 'k_lt': 'cw_lt', 'k_base': 'cw_base', 'k_dk': 'cw_dk'}


def wall_face():
    img = rock_tex([(3, 3), (11, 2), (7, 9), (14, 10), (2, 13)], seed=7).replace(WALL_MAP)
    for y in range(16):
        for x in range(16):
            if img.p[y][x] == 'cw_lt' and (hash2(x, y, 19) & 7) == 0:
                img.p[y][x] = 'cw_hi'
    # the lip of the roof above, and drips hanging off it
    for x in range(16):
        img.p[0][x] = 'cw_out'
        img.p[1][x] = 'cw_dk' if x % 5 else 'cw_out'
    for x in (3, 9, 13):
        img.p[2][x] = 'cw_dk'
        if x != 9:
            img.p[3][x] = 'cw_out'
    # Thin wet mineral trails stop above the contact shadow at the floor.
    for x, y0, length in ((4, 5, 5), (12, 6, 4)):
        for i in range(length):
            img.p[y0 + i][x] = 'cw_hi' if i % 3 == 0 else 'cw_lt'
        img.p[y0 + length][x] = 'cw_dk'
    # the foot of the wall: a shadow on the floor
    for x in range(16):
        img.p[15][x] = 'cv_dkr'
        if img.p[14][x] == 'cw_lt':
            img.p[14][x] = 'cw_base'
    return img


def wall_crystal():
    img = wall_face()
    vein = G('''
    .......O......
    ......Oab.....
    .....ObbcO....
    ..O..ObbcO..O.
    .OaO.Obbcd.OaO
    .ObcOObbcdOObc
    ..ObcObbcdObcO
    ..ObbbbbcdbcO.
    ...OObbbcdOO..
    ''', {'.': None, 'O': 'cw_out', 'a': 'cr_hi', 'b': 'cr_lt', 'c': 'cr_base', 'd': 'cr_dk'})
    img.paste(vein, 1, 5)
    return img


def crystal_outcrop():
    img = FLOOR_A.copy()
    # shadow on the floor to the lower right
    for (x, y) in ((11, 14), (12, 14), (13, 14), (13, 13), (14, 13), (10, 15), (11, 15), (12, 15)):
        img.p[y][x] = 'cv_dk'
    shard = G('''
    ........O.......
    .......OaO......
    .......ObO......
    ..O...OabcO.....
    .OaO..ObbcO..O..
    .ObcO.ObbcdOOaO.
    .ObbcOObbcdObcO.
    ..ObbcObbcdObcO.
    ..ObbcdObcdbcdO.
    ...ObbcObcdbcdO.
    ...ObpPObcdbcO..
    ....ObpPObcbdO..
    ...OOpPPObccdO..
    ...OOOOOOOOOO...
    ''', {'.': None, 'O': 'cw_out', 'a': 'cr_hi', 'b': 'cr_lt', 'c': 'cr_base', 'd': 'cr_dk',
          'p': 'am_lt', 'P': 'am_base'})
    img.paste(shard, 0, 1)
    return img


# ---------------------------------------------------------------------------
# rock ledge (drop to the south)
# ---------------------------------------------------------------------------

LIP_Y = 5
FACE = 4


def _ledge_column(x):
    col = {LIP_Y: 'cv_lt', LIP_Y + 1: 'cv_lt' if x % 3 else 'cv_base', LIP_Y + 2: 'cw_out'}
    for i in range(FACE):
        c = 'cw_base'
        if i == 0:
            c = 'cw_lt' if x % 4 != 2 else 'cw_base'
        elif x % 5 == 0:
            c = 'cw_dk'
        if i == FACE - 1:
            c = 'cw_dk'
        col[LIP_Y + 3 + i] = c
    col[LIP_Y + 3 + FACE] = 'cw_out'
    col[LIP_Y + 4 + FACE] = 'cv_dkr' if x % 2 else 'cv_dk'
    col[LIP_Y + 5 + FACE] = 'cv_dk' if x % 3 else 'cv_mid'
    return col


def ledge_img(ends=None):
    img = FLOOR_A.copy()
    for x in range(16):
        for y, c in _ledge_column(x).items():
            if y < 16:
                img.p[y][x] = c
    if ends:
        prof = {0: None, 1: None, 2: None, 3: 3, 4: 1, 5: 0}
        for u, cut in prof.items():
            x = u if ends == 'L' else 15 - u
            for y in range(LIP_Y, 16):
                img.p[y][x] = FLOOR_A.p[y][x]
            if cut is None:
                continue
            for y, c in _ledge_column(x).items():
                yy = y + cut
                if yy <= 15 and y <= LIP_Y + 3 + FACE:
                    img.p[yy][x] = c
            img.p[LIP_Y + cut][x] = 'cv_lt'
    return img


# ---------------------------------------------------------------------------
# the cave mouth (exit mat): daylight and a drift of blown-in snow
# ---------------------------------------------------------------------------

def mouth_img():
    img = Img(16, 16)
    for y in range(16):
        for x in range(16):
            c = FLOOR_A.p[y][x]
            # the light pool brightens toward the bottom (the way out)
            v = y + 0.5 + 2.0 * math.sin(x * 0.7)
            if v > 9.0:
                c = 'sn_mid' if c in ('cv_base', 'cv_lt') else 'cv_base'
            if v > 12.0:
                c = 'sn_base' if (hash2(x, y, 3) & 3) else 'sn_lt'
            if v > 14.5:
                c = 'sn_lt' if (hash2(x, y, 4) & 3) else 'sn_hi'
            img.p[y][x] = c
    for (x, y) in ((4, 4), (11, 6), (7, 8)):
        img.p[y][x] = 'sn_lt'
    return img


# ---------------------------------------------------------------------------
# the starlit pool (Starfall Grotto): night sky reflected in still water
# ---------------------------------------------------------------------------

STARS = [(2, 3, 'sy_hi'), (9, 1, 'white'), (13, 6, 'sy_base'), (5, 9, 'white'), (11, 12, 'sy_hi'),
         (1, 14, 'sy_base'), (7, 5, 'cr_lt'), (14, 14, 'white')]


def pool_tex():
    img = Img(16, 16, 'nv_base')
    for y in range(16):
        for x in range(16):
            u = (x * 3 + y * 5) % 16
            if u in (0, 7):
                img.p[y][x] = 'nv_lt' if (hash2(x, y, 23) & 1) else 'nv_base'
            elif (hash2(x, y, 27) & 15) == 0:
                img.p[y][x] = 'nv_dk'
    for (x, y, c) in STARS:
        img.p[y][x] = c
    img.p[5][8] = 'nv_lt'
    img.p[5][6] = 'nv_lt'
    return img


POOL_TEX = pool_tex()
RIM = ['cv_lt', 'cv_base', 'cv_dk', 'cv_dkr']


def pool_cell(n, s, w, e):
    """A 16x16 pool cell whose edges n/s/w/e border the stone floor."""
    img = Img(16, 16)
    E0, R = 3.0, 6.0
    for y in range(16):
        for x in range(16):
            dx, dy = 99.0, 99.0
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
            near_nw = (n and dy == y + 0.5 and dy <= dx) or (w and dx == x + 0.5 and dx < dy)
            if v < E0 - 1.0:
                c = FLOOR_A.p[y][x]
            elif v < E0:
                c = 'cv_lt' if not near_nw else 'cv_base'
            elif v < E0 + 1.0:
                c = 'cv_dkr' if near_nw else 'cv_dk'
            elif v < E0 + 2.0 and near_nw:
                c = 'nv_dk'
            else:
                c = POOL_TEX.p[y][x]
            img.p[y][x] = c
    return img


# ---------------------------------------------------------------------------
# gravel path (autotile) and the underground lake (autotile, 3 frames)
# ---------------------------------------------------------------------------

PATH_TEX = G('''
llllllllllllllll
llllmlllllllllll
lllm.mllllllllll
llllmllllllll.ll
llllllllllllllll
l.llllllllmlllll
lllllllllm.mllll
llllllllllmlllll
llllllmlllllllll
lllllm.mlllll.ll
llllllmlllllllll
llllllllllllllll
ll.llllllllmllll
llllllllllm.mlll
lllllllllllmllll
llllllllllllllll
''', FL)


def path_quads():
    def color_at(d, X, Y, c, v, lx, ly):
        if d < -1.0:
            return FLOOR_A.p[Y][X]
        if d < 0:
            return 'cv_mid'
        if d < 1.0:
            return 'cv_base'
        return PATH_TEX.p[Y][X]
    return autotile(color_at, E=2.0, R=5.0, Rn=2.0)


GLINTS = [(2, 2, 3), (10, 1, 2), (6, 6, 3), (13, 9, 2), (1, 11, 2), (8, 13, 3)]


def water_surface(f):
    img = Img(16, 16, 'uw_base')
    for y in range(16):
        for x in range(16):
            if (hash2(x, y, 37) & 31) == 0:
                img.p[y][x] = 'uw_mid'
    for (x, y, n) in GLINTS:
        x2 = x + (f if n == 2 else 0)
        for i in range(n):
            img.p[y % 16][(x2 + i) % 16] = 'uw_lt'
        img.p[y % 16][(x2 + (f % n)) % 16] = 'uw_hi' if (x + y) % 3 else 'cr_lt'
        for i in range(max(1, n - 1)):
            img.p[(y + 1) % 16][(x2 + 1 + i) % 16] = 'uw_mid'
    return img


def water_quads(f):
    surf = water_surface(f)

    def color_at(d, X, Y, c, v, lx, ly):
        if d < 0:
            return FLOOR_A.p[Y][X]
        if d < 1.0:
            return 'cv_lt'
        if d < 2.0:
            return 'cv_dk'
        if d < 3.0:
            return 'uw_dk'
        if d < 4.0:
            return 'uw_mid'
        return surf.p[Y][X]
    return autotile(color_at, E=1.0, R=6.0, Rn=2.5)


def add_water(gf, ts, out, bank=1):
    """Contiguous, never-shared block of animated water autotiles."""
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
# stamps: stairs down, steps up, the crack to the grotto (1x1 doors)
# ---------------------------------------------------------------------------

def stairs_down():
    """A stair well cut into the floor, going down to the north."""
    img = FLOOR_A.copy()
    for y in range(1, 16):
        for x in range(1, 15):
            img.p[y][x] = 'cw_out'
    for x in range(1, 15):
        img.p[1][x] = 'cw_dk'
        img.p[15][x] = 'cv_lt'
    for y in range(1, 16):
        img.p[y][1] = 'cw_dk'
        img.p[y][14] = 'cw_dk'
    # steps, getting darker and narrower as they go down
    for i, (y, c, hi) in enumerate(((12, 'cv_base', 'cv_lt'), (9, 'cv_mid', 'cv_base'),
                                    (6, 'cv_dk', 'cv_mid'), (3, 'cv_dkr', 'cv_dk'))):
        for x in range(2 + i, 14 - i):
            img.p[y][x] = hi
            img.p[y + 1][x] = c
    return img


def stairs_up():
    """Wooden steps climbing into the rock face (a WALL cell with steps)."""
    img = wall_face()
    for y in range(2, 16):
        for x in range(3, 13):
            img.p[y][x] = 'cw_out'
    for i, y in enumerate((13, 10, 7, 4)):
        x0, x1 = 3 + (i > 2), 12 - (i > 2)
        for x in range(x0, x1 + 1):
            img.p[y][x] = 'wd_lt'
            img.p[y + 1][x] = 'wd_base' if i < 3 else 'wd_dk'
            img.p[y + 2][x] = 'wd_dk' if y + 2 < 16 else img.p[y + 2][x]
        img.p[y][x0] = img.p[y][x1] = 'b_out'
    # rails
    for y in range(3, 16):
        img.p[y][2] = 'wd_dk'
        img.p[y][13] = 'wd_dk'
    img.p[2][2] = img.p[2][13] = 'lw_base'
    return img


def crack_img():
    """A tall fissure in the wall, lit violet from beyond."""
    img = wall_face()
    for y in range(2, 16):
        half = 1.5 + 2.2 * math.sin(math.pi * (y - 1) / 15.0)
        cx = 8.0 + 0.8 * math.sin(y * 0.9)
        for x in range(16):
            d = abs(x + 0.5 - cx)
            if d < half - 1.0:
                img.p[y][x] = 'am_lt' if d < 0.8 else 'am_base'
            elif d < half:
                img.p[y][x] = 'cw_out'
    for (x, y) in ((8, 6), (7, 11)):
        img.p[y][x] = 'white'
    for x in range(5, 12):
        img.p[15][x] = 'am_base' if x % 2 else 'cv_dk'
    return img


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def images():
    moss_b, moss_t = moss_layers()
    return {
        'FLOOR': (FLOOR_A.copy(), None), 'FLOOR2': (FLOOR_B.copy(), None),
        'FLOOR3': (FLOOR_C.copy(), None), 'MOSS': (moss_b, moss_t),
        'ROCK': (rock_mass(), None), 'WALL': (wall_face(), None),
        'WALL_CRYSTAL': (wall_crystal(), None), 'CRYSTAL': (crystal_outcrop(), None),
        'LEDGE': (ledge_img(), None), 'LEDGE_L': (ledge_img('L'), None),
        'LEDGE_R': (ledge_img('R'), None), 'MOUTH': (mouth_img(), None),
        'VOID': (Img(16, 16, 'cw_out'), None),
        'POOL': (POOL_TEX.copy(), None),
        'POOL_N': (pool_cell(1, 0, 0, 0), None), 'POOL_S': (pool_cell(0, 1, 0, 0), None),
        'POOL_W': (pool_cell(0, 0, 1, 0), None), 'POOL_E': (pool_cell(0, 0, 0, 1), None),
        'POOL_NW': (pool_cell(1, 0, 1, 0), None), 'POOL_NE': (pool_cell(1, 0, 0, 1), None),
        'POOL_SW': (pool_cell(0, 1, 1, 0), None), 'POOL_SE': (pool_cell(0, 1, 0, 1), None),
    }


BANKS = [
    NP.CAVE_BANK_FLOOR,            # 0 floor, glowmoss, crystal grit, outcrops
    NP.CAVE_BANK_WATER,            # 1 underground lake and its shore
    NP.CAVE_BANK_WALLS,            # 2 rock mass, wall faces, ledges
    decor_outdoor.TOWN_DECOR_BANK,  # 3 village props
    NP.CAVE_DECOR_BANK,            # 4 cave decor: crystals, stalagmites
    NP.CAVE_BANK_MOUTH,            # 5 daylight at the mouth, wooden steps, lamps
    NP.CAVE_BANK_SKY,              # 6 the starlit pool, moonlight
    NP.CAVE_BANK_CRYSTAL,          # 7 crystal veins in the walls
]

PREFER = {'FLOOR': (0,), 'FLOOR2': (0,), 'FLOOR3': (0,), 'MOSS': (0,), 'CRYSTAL': (0,),
          'ROCK': (2,), 'WALL': (2,), 'WALL_CRYSTAL': (7, 2), 'LEDGE': (2,), 'LEDGE_L': (2,),
          'LEDGE_R': (2,), 'MOUTH': (5,), 'VOID': (2,)}
POOLS = ['POOL', 'POOL_N', 'POOL_S', 'POOL_W', 'POOL_E', 'POOL_NW', 'POOL_NE', 'POOL_SW', 'POOL_SE']


def build(gf, name):
    gf.register_colors(NP.NORTH_COLORS)
    gf.check_banks(name, BANKS)
    ts = gf.TileSet(name, BANKS)
    out = {'ts': ts, 'meta_b': [], 'meta_t': [], 'terrain': TERRAIN}
    add_water(gf, ts, out, bank=1)
    imgs = images()
    for t in TERRAIN:
        bottom, top = imgs[t]
        pref = PREFER.get(t, (6,))
        out['meta_b'].append(ts.meta(bottom, prefer=pref, where='cave.' + t))
        out['meta_t'].append(ts.meta(top, prefer=(0,), where='cave.%s.top' % t, opaque=False)
                             if top else [0, 0, 0, 0])
    gf.add_stamps(ts, out, [
        ('STAIRS_DOWN', stairs_down(), (2,), 'stair well going down, door (walk north into it)'),
        ('STAIRS_UP', stairs_up(), (5, 2), 'wooden steps up into the rock, door (walk north)'),
        ('CRACK', crack_img(), (7, 2), 'violet-lit fissure to the grotto, door (walk north)'),
    ])
    out['path_q'] = [[ts.add(gf.img_pix(q), (0,), 'cave.path[%d][%d]' % (c, v))
                      for v, q in enumerate(row)] for c, row in enumerate(path_quads())]
    attrs = {'MOSS': gf.A_GRASS, 'ROCK': gf.A_SOLID, 'WALL': gf.A_SOLID,
             'WALL_CRYSTAL': gf.A_SOLID, 'CRYSTAL': gf.A_SOLID, 'LEDGE': gf.A_LEDGE,
             'LEDGE_L': gf.A_LEDGE, 'LEDGE_R': gf.A_LEDGE, 'MOUTH': gf.A_EXIT, 'VOID': gf.A_SOLID}
    for n in POOLS:
        attrs[n] = gf.A_SOLID
    out = gf.finish_tileset(
        out, name, 'CV', attrs=attrs,
        ground=['FLOOR', 'FLOOR2', 'FLOOR3'], overlay=[],
        legend={'.': [('FLOOR3', 2), ('FLOOR2', 3), ('FLOOR', 11)], ',': 'MOSS', '=': 'PATH',
                '~': 'WATER', 'X': 'ROCK', 'c': 'WALL', 'Q': 'WALL_CRYSTAL', '*': 'CRYSTAL',
                'L': 'LEDGE', '[': 'LEDGE_L', ']': 'LEDGE_R', 'D': 'MOUTH', ' ': 'VOID',
                '5': 'POOL', '8': 'POOL_N', '2': 'POOL_S', '4': 'POOL_W', '6': 'POOL_E',
                '7': 'POOL_NW', '9': 'POOL_NE', '1': 'POOL_SW', '3': 'POOL_SE'},
        oob='ROCK', default_ground='FLOOR', backdrop=(24, 20, 36),
        doors=[('STAIRS_DOWN', 0, 0), ('STAIRS_UP', 0, 0), ('CRACK', 0, 0)])
    out['docs'] = DOC
    return out
