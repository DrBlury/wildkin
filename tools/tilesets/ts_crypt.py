"""The 'crypt' tileset (W-GRIM): the LANTERN CRYPT, THE OSSUARY (two
floors) and the BONE THRONE. Cold violet flagstones, stone walls with skull
niches, bone walls, a red runner and green foxfire cracks.

Legend (documented again at the top of src/game/world/grim/data.h):

  (space) VOID       black outside the rooms                 solid
  W  WALL_TOP        top of a wall                            solid
  w  WALL            wall face (bricks)                       solid
  n  NICHE           wall face with a skull niche and candle  solid
  o  BONE_WALL       wall face of stacked skulls (ossuary)    solid
  v  WISP_WALL       wall face with a green foxfire crack     solid
  .  FLOOR           flagstones (+ FLOOR2 dusty variant 3/16)  ground
  :  FLOOR2          cracked flagstones with bone dust        ground
  #  BLOCK           a maze block (top + front face)           solid
  %  FAKE_BLOCK      looks exactly like BLOCK, but walkable   (Lantern Crypt)
  _  GHOST_FLOOR     looks exactly like FLOOR, but solid      (Lantern Crypt)
  D  DOORMAT         worn threshold slab                      exit mat
  |  CARPET          red runner with gold edges (walkable)
  U  STAIRS_UP       steps up, set into a wall                door
  S  STAIRS_DOWN     steps down into the dark, in a wall      door
  A  ARCH            a dark archway in a wall                 door
  I/i PILLAR_TOP / PILLAR  a two-cell column                  solid

The FAKE_BLOCK and GHOST_FLOOR pair is the Lantern Crypt's puzzle: in the
dark, the walls lie. Doors are terrain here (no stamps): every door cell
needs a walkable cell right below it.
"""

import decor_grim as dg
from pixelart import Img, hash2

USES_DECOR = []

TERRAIN = ['VOID', 'WALL_TOP', 'WALL', 'NICHE', 'BONE_WALL', 'WISP_WALL', 'FLOOR', 'FLOOR2',
           'BLOCK', 'FAKE_BLOCK', 'GHOST_FLOOR', 'DOORMAT', 'CARPET', 'STAIRS_UP',
           'STAIRS_DOWN', 'ARCH', 'PILLAR_TOP', 'PILLAR']

TERRAIN_DOC = {
    'VOID': 'black outside the rooms',
    'WALL_TOP': 'top of a crypt wall (dark stone)',
    'WALL': 'wall face: violet bricks above a shadowed footing',
    'NICHE': 'wall face with a skull niche and a candle',
    'BONE_WALL': 'wall face of stacked skulls and long bones (the Ossuary)',
    'WISP_WALL': 'wall face split by a glowing green foxfire crack',
    'FLOOR': 'cold violet flagstones',
    'FLOOR2': 'cracked flagstones with bone dust',
    'BLOCK': 'a maze block seen from above: top face and a brick front',
    'FAKE_BLOCK': 'identical to BLOCK but walkable (a false wall)',
    'GHOST_FLOOR': 'identical to FLOOR but solid (an unseen wall)',
    'DOORMAT': 'worn threshold slab (exit mat)',
    'CARPET': 'red runner with gold edges',
    'STAIRS_UP': 'stone steps rising into the wall (door)',
    'STAIRS_DOWN': 'steps falling away into the dark (door)',
    'ARCH': 'a dark archway (door)',
    'PILLAR_TOP': 'column capital (upper cell)',
    'PILLAR': 'column shaft (lower cell)',
}


def flag_img(dusty=False):
    """Flagstones: two staggered rows of slabs, mortar in fl_dk."""
    img = Img(16, 16, 'cry_fl')
    joints_x = {0: (0, 9), 1: (4, 13)}   # vertical joints per slab row
    for y in range(16):
        row = 0 if y < 8 else 1
        yy = y % 8
        for x in range(16):
            c = 'cry_fl'
            if yy == 7:
                c = 'cry_fl_dk'
            elif x in joints_x[row]:
                c = 'cry_fl_dk'
            elif yy == 0 or (x - 1) in joints_x[row]:
                c = 'cry_fl_hi' if (hash2(x, y, 3) & 3) else 'cry_fl'
            elif yy == 6 or (x + 1) in joints_x[row]:
                c = 'cry_fl_md'
            else:
                h = hash2(x, y, 11) & 31
                if h < 3:
                    c = 'cry_fl_md'
                elif h == 31:
                    c = 'cry_fl_hi'
            img.p[y][x] = c
    if dusty:
        for (x, y, c) in ((3, 3, 'cry_bone_dk'), (4, 3, 'cry_bone'), (5, 4, 'cry_bone_dk'),
                          (11, 10, 'cry_bone'), (12, 11, 'cry_bone_dk'), (2, 12, 'cry_bone_dk')):
            img.p[y][x] = c
        # a hairline crack across a slab
        for (x, y) in ((7, 1), (8, 2), (8, 3), (9, 4), (10, 4), (11, 5)):
            img.p[y][x] = 'cry_fl_dk'
        img.p[3][8] = 'cry_wisp_dk'
    return img


def brick_face(img, y0, y1, seed=0):
    """Bricks in wl / wl_md with wl_dk mortar, rows of 4 px."""
    for y in range(y0, y1):
        r = (y - y0) // 4
        yy = (y - y0) % 4
        off = 4 if r % 2 else 0
        for x in range(16):
            if yy == 3:
                c = 'cry_wl_dk'
            elif (x + off) % 8 == 7:
                c = 'cry_wl_dk'
            elif yy == 0:
                c = 'cry_wl_hi' if (x + off) % 8 < 5 else 'cry_wl'
            else:
                h = hash2(x, y, 5 + seed) & 15
                c = 'cry_wl_md' if h < 3 else 'cry_wl'
            img.p[y][x] = c


def wall_top_img():
    img = Img(16, 16, 'cry_wl_dkr')
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 7) & 31
            if h < 3:
                img.p[y][x] = 'cry_wl_dk'
            elif h == 31:
                img.p[y][x] = 'cry_void'
    for x in range(16):
        img.p[15][x] = 'cry_wl_dk'
    return img


def wall_img():
    img = Img(16, 16)
    brick_face(img, 0, 13)
    for x in range(16):
        img.p[13][x] = 'cry_wl_md'
        img.p[14][x] = 'cry_wl_dk'
        img.p[15][x] = 'cry_wl_dkr'
    return img


def niche_img():
    img = wall_img()
    # the niche: a dark round-topped hole with a skull and a candle
    for y in range(2, 13):
        for x in range(3, 13):
            top = y < 5 and abs(x - 7.5) > (y - 1) * 1.6 + 1
            if top:
                continue
            img.p[y][x] = 'cry_out' if (x in (3, 12) or y == 12) else 'cry_void'
    for x in range(4, 12):
        img.p[12][x] = 'cry_wl_hi'
    skull = ['.WWB.', 'WOBOb', 'WBbBb', '.BbB.']
    for dy, row in enumerate(skull):
        for dx, ch in enumerate(row):
            c = {'W': 'cry_bone_hi', 'B': 'cry_bone', 'b': 'cry_bone_dk', 'O': 'cry_out'}.get(ch)
            if c:
                img.p[8 + dy][5 + dx] = c
    img.p[9][10] = 'cry_wax'
    img.p[10][10] = 'cry_wax'
    img.p[11][10] = 'cry_wax'
    img.p[8][10] = 'cry_flame'
    img.p[7][10] = 'cry_flame_hi'
    return img


def bone_wall_img():
    img = Img(16, 16, 'cry_void')
    # rows of skulls with long bones between them
    for band, y0 in enumerate((0, 8)):
        for x in range(16):
            img.p[y0 + 6][x] = 'cry_bone_dk'
            img.p[y0 + 7][x] = 'cry_bone' if x % 3 else 'cry_bone_hi'
        for k in range(2):
            sx = k * 8 + (4 if band else 0)
            skull = ['.BBB.', 'BWBBb', 'BObOb', 'bBBBb', '.bbb.']
            for dy, row in enumerate(skull):
                for dx, ch in enumerate(row):
                    c = {'W': 'cry_bone_hi', 'B': 'cry_bone', 'b': 'cry_bone_dk',
                         'O': 'cry_out'}.get(ch)
                    if c:
                        img.p[y0 + dy][(sx + 1 + dx) % 16] = c
    for x in range(16):
        img.p[15][x] = 'cry_wl_dkr'
    return img


def wisp_wall_img():
    img = wall_img()
    crack = [(9, 0), (9, 1), (8, 2), (8, 3), (7, 4), (7, 5), (8, 6), (8, 7), (9, 8), (8, 9),
             (7, 10), (7, 11), (6, 12)]
    for (x, y) in crack:
        img.p[y][x] = 'cry_wisp'
        if x + 1 < 16:
            img.p[y][x + 1] = 'cry_wisp_dk'
    for (x, y) in ((8, 3), (7, 5), (8, 7), (7, 11)):
        img.p[y][x] = 'cry_bone'   # the brightest glints (bank 0 has no wisp_hi)
    return img


def block_img():
    img = Img(16, 16)
    # top face (rows 0-9): dark stone slab with a lit rim
    for y in range(10):
        for x in range(16):
            if y == 0 or x == 0:
                c = 'cry_wl_md'
            elif x == 15:
                c = 'cry_wl_dkr'
            else:
                h = hash2(x, y, 23) & 15
                c = 'cry_wl_dk' if h else 'cry_wl_md'
            img.p[y][x] = c
    img.p[0][0] = 'cry_wl'
    # front face (rows 10-15): bricks and a dark footing
    for y in range(10, 16):
        for x in range(16):
            yy = y - 10
            if yy == 0:
                c = 'cry_wl_hi'
            elif yy == 5:
                c = 'cry_wl_dkr'
            elif yy == 3 or (x + (4 if yy > 3 else 0)) % 8 == 7:
                c = 'cry_wl_dk'
            else:
                c = 'cry_wl' if x > 1 else 'cry_wl_hi'
            img.p[y][x] = c
    return img


def doormat_img():
    img = flag_img()
    for y in range(3, 16):
        for x in range(2, 14):
            if y == 3:
                c = 'cry_fl_hi'
            elif x in (2, 13) or y == 15:
                c = 'cry_fl_dk'
            else:
                c = 'cry_fl_md' if (x + y) % 5 else 'cry_fl'
            img.p[y][x] = c
    return img


def carpet_img():
    img = Img(16, 16, 'cry_rug')
    for y in range(16):
        img.p[y][0] = 'cry_fl_md'
        img.p[y][15] = 'cry_fl_md'
        img.p[y][1] = 'cry_gold_dk'
        img.p[y][14] = 'cry_gold_dk'
        img.p[y][2] = 'cry_gold'
        img.p[y][13] = 'cry_gold'
        img.p[y][3] = 'cry_rug_dk'
        img.p[y][12] = 'cry_rug_dk'
        if y % 8 in (3, 4):
            img.p[y][7] = 'cry_gold_hi' if y % 8 == 3 else 'cry_gold'
            img.p[y][8] = 'cry_gold' if y % 8 == 3 else 'cry_gold_dk'
        elif (y % 8 in (2, 5)) and True:
            img.p[y][7] = 'cry_rug_hi'
            img.p[y][8] = 'cry_rug_hi'
        if y % 4 == 0:
            img.p[y][2] = 'cry_gold_hi'
            img.p[y][13] = 'cry_gold_hi'
    return img


def stairs_img(down):
    img = Img(16, 16, 'cry_void')
    # the opening in the wall: side jambs in wall stone
    for y in range(16):
        for x in (0, 1, 14, 15):
            img.p[y][x] = 'cry_wl_md' if x in (1, 14) else 'cry_wl_dk'
    for x in range(16):
        img.p[0][x] = 'cry_wl_dk'
    if down:
        # steps falling away: lit lips fading into the dark
        for k, y in enumerate((13, 10, 7, 5)):
            lip = ['cry_fl_hi', 'cry_fl', 'cry_fl_md', 'cry_fl_dk'][k]
            face = ['cry_fl_md', 'cry_fl_dk', 'cry_wl_dkr', 'cry_void'][k]
            for x in range(2 + k, 14 - k):
                img.p[y][x] = lip
                if y + 1 < 16:
                    img.p[y + 1][x] = face
    else:
        # steps rising into the wall: bright treads, shadowed risers
        for k, y in enumerate((12, 9, 6, 3)):
            for x in range(2, 14):
                img.p[y][x] = 'cry_fl_hi'
                img.p[y + 1][x] = 'cry_fl'
                img.p[y + 2][x] = 'cry_fl_dk'
        for x in range(2, 14):
            img.p[15][x] = 'cry_fl'
    return img


def arch_img():
    img = wall_img()
    for y in range(1, 16):
        for x in range(3, 13):
            if y < 5 and abs(x - 7.5) > (y + 0.5) * 1.5:
                continue
            edge = x in (3, 12) or (y < 5 and abs(x - 7.5) > (y - 0.5) * 1.5)
            img.p[y][x] = 'cry_out' if edge else 'cry_void'
    for x in range(3, 13):
        img.p[15][x] = 'cry_fl_dk'
    return img


def pillar_imgs():
    top = Img(16, 16)
    bot = Img(16, 16)
    ramp = ['cry_wl_dkr', 'cry_wl_hi', 'cry_wl', 'cry_wl', 'cry_wl', 'cry_wl_md', 'cry_wl_md',
            'cry_wl_dk']
    for y in range(16):
        for x in range(16):
            # capital: wide slab rows 2-6, then the shaft
            if 2 <= y <= 6:
                if x < 1 or x > 14:
                    c = None
                elif y == 2:
                    c = 'cry_wl_hi'
                elif y == 6:
                    c = 'cry_wl_dkr'
                else:
                    c = 'cry_wl' if x < 12 else 'cry_wl_md'
            elif y > 6 and 3 <= x <= 12:
                c = ramp[min(7, (x - 3) * 8 // 10)] if x > 3 else 'cry_wl_dkr'
                if x == 12:
                    c = 'cry_wl_dkr'
            else:
                c = None
            top.p[y][x] = c
            if 3 <= x <= 12:
                c2 = ramp[min(7, (x - 3) * 8 // 10)] if x > 3 else 'cry_wl_dkr'
                if x == 12:
                    c2 = 'cry_wl_dkr'
                if y >= 12:
                    c2 = 'cry_wl_md' if y == 12 else ('cry_wl_dk' if y < 15 else 'cry_wl_dkr')
                bot.p[y][x] = c2
            elif y >= 12 and 1 <= x <= 14:
                bot.p[y][x] = 'cry_wl_md' if y == 12 else ('cry_wl_dk' if y < 15 else 'cry_wl_dkr')
    # fill the transparent corners with floor so the cells are opaque
    fl = flag_img()
    for img in (top, bot):
        for y in range(16):
            for x in range(16):
                if img.p[y][x] is None:
                    img.p[y][x] = fl.p[y][x]
    return top, bot


def build(gf, name):
    gf.register_colors(dg.ALL_COLORS)
    gf.check_banks(name, dg.CRYPT_BANKS)
    ts = gf.TileSet(name, dg.CRYPT_BANKS)
    out = {'ts': ts, 'meta_b': [], 'meta_t': [], 'terrain': TERRAIN, 'docs': TERRAIN_DOC}
    floor, block = flag_img(), block_img()
    ptop, pbot = pillar_imgs()
    imgs = {
        'VOID': Img(16, 16, 'cry_void'), 'WALL_TOP': wall_top_img(), 'WALL': wall_img(),
        'NICHE': niche_img(), 'BONE_WALL': bone_wall_img(), 'WISP_WALL': wisp_wall_img(),
        'FLOOR': floor, 'FLOOR2': flag_img(True), 'BLOCK': block, 'FAKE_BLOCK': block.copy(),
        'GHOST_FLOOR': floor.copy(), 'DOORMAT': doormat_img(), 'CARPET': carpet_img(),
        'STAIRS_UP': stairs_img(False), 'STAIRS_DOWN': stairs_img(True), 'ARCH': arch_img(),
        'PILLAR_TOP': ptop, 'PILLAR': pbot,
    }
    prefer = {'NICHE': (1,), 'BONE_WALL': (1,), 'CARPET': (2,)}
    for tname in TERRAIN:
        out['meta_b'].append(ts.meta(imgs[tname], prefer=prefer.get(tname, (0,)),
                                     where='crypt.' + tname))
        out['meta_t'].append([0, 0, 0, 0])
    out['stamps'] = []
    S, D = gf.A_SOLID, gf.A_DOOR
    attrs = {'VOID': S, 'WALL_TOP': S, 'WALL': S, 'NICHE': S, 'BONE_WALL': S, 'WISP_WALL': S,
             'BLOCK': S, 'GHOST_FLOOR': S, 'PILLAR_TOP': S, 'PILLAR': S,
             'DOORMAT': gf.A_EXIT, 'STAIRS_UP': S | D, 'STAIRS_DOWN': S | D, 'ARCH': S | D}
    return gf.finish_tileset(
        out, name, 'CR', attrs=attrs, ground=['FLOOR', 'FLOOR2'], overlay=[],
        legend={' ': 'VOID', 'W': 'WALL_TOP', 'w': 'WALL', 'n': 'NICHE', 'o': 'BONE_WALL',
                'v': 'WISP_WALL', '.': [('FLOOR2', 3), ('FLOOR', 13)], ':': 'FLOOR2',
                '#': 'BLOCK', '%': 'FAKE_BLOCK', '_': 'GHOST_FLOOR', 'D': 'DOORMAT',
                '|': 'CARPET', 'U': 'STAIRS_UP', 'S': 'STAIRS_DOWN', 'A': 'ARCH',
                'I': 'PILLAR_TOP', 'i': 'PILLAR'},
        oob='VOID', default_ground='FLOOR', backdrop=(8, 6, 14), legend_default=' ')
