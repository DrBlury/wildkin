"""The 'grim' tileset (W-GRIM): the Ashen March outdoors -- ASHEN FIELDS,
GRAVEWOOD and the stilt town of DUSKMERE.

Legend (documented again at the top of src/game/world/grim/data.h):

  .  ASH (drifted ash; variants ASH2 cinders, ASH3 a bone chip)   ground
  ,  ASH_GRASS dead grass (wild kin roam)                         grass
  :  SCORCH burnt earth                                            ground
  e  EMBERS smouldering cracks (animated, walkable)
  #  COBBLE old cobbles
  =  PATH the ash road (autotiled)
  ~  WATER black mire water (autotiled, animated)
  g  GRAVE_SOIL dark leafy loam (+ GRAVE_SOIL2)                    ground
  b  GRAVE_BRUSH dead bracken (wild kin roam)                      grass
  m  MUD peat mud (+ MUD2 puddle and foxfire)                      ground
  M  MOSS moss carpet                                              ground
  r  MIRE_REEDS reeds in the mud (wild kin roam)                   grass
  d  DECK wooden planks (Duskmere platforms)
  T/t GNARL_TOP/BOTTOM dead oak        (overlay, solid)
  P/p SNAG_TOP/BOTTOM charred pine     (overlay, solid)
  Y/y CYPRESS_TOP/BOTTOM swamp cypress (overlay, solid)
  L [ ]  LEDGE / LEDGE_L / LEDGE_R one-way ash ledges (hop down)
  C  CRAG rock wall with an ash lip, c CRAG_FACE plain rock (solid)

Stamps: HOUSE, SHOP, APOTHECARY (4x4 stilt houses, door col 1 row 3),
HEARTH (5x4, door col 2 row 3), CRYPT_HALL (the LANTERN CRYPT, 5x4,
door col 2 row 3) and BONE_GATE (the sealed OSSUARY gate, 5x4, no door:
the gate warden lets crest-holders in).
"""

import math
import decor_grim as dg
from decor_grim import mask_img, seg_mask, ell_mask, shade_mask, outline_mask, wrap_noise
from pixelart import Img, G, hash2, shade_clumps, tex_fill
from terrain_common import autotile

USES_DECOR = []

TERRAIN = [
    'ASH', 'ASH2', 'ASH3', 'ASH_GRASS', 'SCORCH', 'EMBERS', 'COBBLE',
    'GRAVE_SOIL', 'GRAVE_SOIL2', 'GRAVE_BRUSH',
    'MUD', 'MUD2', 'MOSS', 'MIRE_REEDS', 'DECK',
    'GNARL_TOP', 'GNARL_BOTTOM', 'SNAG_TOP', 'SNAG_BOTTOM', 'CYPRESS_TOP', 'CYPRESS_BOTTOM',
    'LEDGE', 'LEDGE_L', 'LEDGE_R', 'CRAG', 'CRAG_FACE',
]

TERRAIN_DOC = {
    'ASH': 'drifted ash (+ ASH2 cinders, ASH3 a bone chip and an ember)',
    'ASH_GRASS': 'dead grass on ash; wild kin roam; top layer = front blades',
    'SCORCH': 'burnt earth with cracks',
    'EMBERS': 'smouldering cracks, animated (walkable)',
    'COBBLE': 'old cobbles of the ash road and the Duskmere square',
    'GRAVE_SOIL': 'dark loam with fallen leaves (Gravewood floor, + variant)',
    'GRAVE_BRUSH': 'dead bracken; wild kin roam; top layer = front fronds',
    'MUD': 'peat mud (+ MUD2 with a puddle and foxfire specks)',
    'MOSS': 'moss carpet on the mud',
    'MIRE_REEDS': 'reeds in the mud; wild kin roam; top layer = front stalks',
    'DECK': 'weathered planks (Duskmere platforms)',
    'GNARL_TOP': '16x32 dead oak: TOP above BOTTOM (overlay)',
    'SNAG_TOP': '16x32 charred pine with ember cracks (overlay; forest walls)',
    'CYPRESS_TOP': '16x32 swamp cypress with hanging moss (overlay)',
    'LEDGE': 'one-way ash ledge: walk DOWN onto it to hop over',
    'CRAG': 'rock wall with an ash lip (solid); CRAG_FACE stacks below',
}

OVERLAY = ('GNARL_TOP', 'GNARL_BOTTOM', 'SNAG_TOP', 'SNAG_BOTTOM', 'CYPRESS_TOP', 'CYPRESS_BOTTOM')
GROUND = ['ASH', 'ASH2', 'ASH3', 'SCORCH', 'GRAVE_SOIL', 'GRAVE_SOIL2', 'MUD', 'MUD2', 'MOSS']

TAU = math.pi * 2


# ---------------------------------------------------------------- ash

def ash_img(seed=0, extras=0):
    img = Img(16, 16, 'grm_ash')
    # soft drift ripples (short arcs: a light crest over a shadowed trough)
    ripples = [(1, 2, 5), (9, 4, 6), (4, 8, 4), (11, 11, 5), (0, 13, 4), (6, 14, 3)]
    if seed:
        ripples = [(3, 1, 4), (10, 3, 5), (1, 7, 5), (8, 9, 6), (13, 13, 4), (4, 12, 3)]
    for (x0, y0, n) in ripples:
        for i in range(n):
            x = (x0 + i) % 16
            y = (y0 + (1 if 0 < i < n - 1 else 0)) % 16
            img.p[y][x] = 'grm_ash_md'
            if 0 < i < n - 1:
                img.p[(y - 1) % 16][x] = 'grm_ash_lt' if i % 2 else 'grm_ash'
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 41 + seed) & 255
            if img.p[y][x] != 'grm_ash':
                continue
            if h < 9:
                img.p[y][x] = 'grm_ash_md'
            elif h < 12:
                img.p[y][x] = 'grm_ash_dk'
            elif h > 251:
                img.p[y][x] = 'grm_ash_hi'
            elif h > 243:
                img.p[y][x] = 'grm_ash_lt'
    if extras == 1:     # cinders
        for (x, y) in ((4, 5), (12, 9), (7, 12)):
            img.p[y][x] = 'grm_soot'
            img.p[y][x + 1] = 'grm_ash_dkr'
            img.p[y + 1][x] = 'grm_ash_dkr'
        img.p[5][5] = 'grm_emb_dk'
    elif extras == 2:   # a bone chip and a live ember
        chip = G('''
        .bB.
        bBBs
        .ss.
        ''', {'.': None, 'b': 'grm_bone', 'B': 'grm_bone', 's': 'grm_ash_md'})
        img.paste(chip, 3, 9)
        img.p[9][4] = 'grm_ash_hi'
        img.p[4][11] = 'grm_emb'
        img.p[4][12] = 'grm_emb_dk'
        img.p[3][11] = 'grm_emb_dk'
        img.p[5][11] = 'grm_ash_dkr'
    return img


ASH_A = ash_img()


def fill_ash(img):
    tex_fill(img, ASH_A, only_none=True)
    return img


# dead grass tuft (blades bend in the wind; dark gaps are soot)
DG = {'.': None, 'O': 'grm_soot', 'd': 'grm_straw_dk', 'm': 'grm_straw', 'l': 'grm_straw_hi',
      'a': 'grm_ash_dk', 'r': 'grm_rust'}
DEAD_TUFT = G('''
.l.....l
.ld...lm
lmd..lmO
lmdOlmdd
mddOmmdO
mdaOmdad
ddaaddaa
aOaaOaaO
''', DG)


def ash_grass_layers():
    back = Img(16, 16)
    tex_fill(back, ASH_A)
    for ox in (-4, 4, 12):
        back.paste(DEAD_TUFT, ox, 1)
    front = Img(16, 16)
    for ox in (0, 8):
        front.paste(DEAD_TUFT, ox, 8)
    bottom = back.copy()
    bottom.paste(front, 0, 0)
    bottom.p[6][3] = 'grm_rust'
    bottom.p[13][13] = 'grm_rust'
    top = Img(16, 16)
    for y in range(9, 16):
        for x in range(16):
            ty = y - 8
            c = DEAD_TUFT.p[ty][x % 8]
            if c is None or (ty <= 3 and c in ('grm_soot', 'grm_ash_dk')):
                continue
            top.p[y][x] = c
    return bottom, top


def scorch_img():
    img = Img(16, 16, 'grm_ash_dkr')
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 77) & 255
            if h < 40:
                img.p[y][x] = 'grm_soot'
            elif h < 60:
                img.p[y][x] = 'grm_ash_dk'
            elif h > 250:
                img.p[y][x] = 'grm_ash_md'
    # cracks
    for (pts) in (((0, 4), (3, 5), (6, 5), (8, 7)), ((8, 7), (11, 6), (15, 8)),
                  ((8, 7), (9, 10), (7, 13), (8, 15))):
        for i in range(len(pts) - 1):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            n = max(abs(x1 - x0), abs(y1 - y0))
            for k in range(n + 1):
                x = x0 + (x1 - x0) * k // max(1, n)
                y = y0 + (y1 - y0) * k // max(1, n)
                img.p[y % 16][x % 16] = 'grm_soot'
    img.p[12][3] = 'grm_emb_dk'
    img.p[2][12] = 'grm_ash_md'
    return img


CRACKS = [((0, 3), (4, 4), (7, 6)), ((7, 6), (10, 4), (15, 3)), ((7, 6), (8, 10), (5, 13), (4, 15)),
          ((8, 10), (12, 12), (15, 12))]


def embers_frames():
    frames = []
    for f in range(2):
        img = scorch_img()
        glow = ('grm_emb_dk', 'grm_emb') if f == 0 else ('grm_emb', 'grm_emb_hi')
        for pts in CRACKS:
            for i in range(len(pts) - 1):
                (x0, y0), (x1, y1) = pts[i], pts[i + 1]
                n = max(abs(x1 - x0), abs(y1 - y0))
                for k in range(n + 1):
                    x = x0 + (x1 - x0) * k // max(1, n)
                    y = y0 + (y1 - y0) * k // max(1, n)
                    hot = (x * 3 + y * 5 + f * 7) % 5 == 0
                    img.p[y % 16][x % 16] = glow[1] if hot else glow[0]
        for (x, y) in ((2, 10), (12, 8), (11, 1)):
            img.p[y][x] = glow[f % 2]
        frames.append(img)
    return frames


def cobble_img():
    img = Img(16, 16, 'grm_ash_dkr')
    stones = [(0, 0, 6, 4), (7, 0, 4, 4), (12, 0, 4, 4), (0, 5, 3, 5), (4, 5, 6, 5), (11, 5, 5, 5),
              (0, 11, 5, 5), (6, 11, 4, 5), (11, 11, 5, 5)]
    for i, (x0, y0, w, h) in enumerate(stones):
        for y in range(y0, y0 + h - 1):
            for x in range(x0, x0 + w - 1):
                c = 'grm_ash' if (i % 3) else 'grm_ash_lt'
                if y == y0 or x == x0:
                    c = 'grm_ash_hi' if (i % 3) == 0 else 'grm_ash_lt'
                if y == y0 + h - 2 or x == x0 + w - 2:
                    c = 'grm_ash_md'
                if (hash2(x, y, 5) & 15) == 0:
                    c = 'grm_ash_dk'
                img.p[y % 16][x % 16] = c
    img.p[7][7] = 'grm_ash_dk'
    img.p[13][2] = 'grm_straw_dk'
    return img


# ---------------------------------------------------------------- gravewood floor

def grave_soil_img(seed=0):
    img = Img(16, 16, 'grm_ash_dkr')
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 91 + seed) & 255
            if h < 30:
                img.p[y][x] = 'grm_soot'
            elif h < 64:
                img.p[y][x] = 'grm_ash_dk'
            elif h > 252:
                img.p[y][x] = 'grm_ash_md'
    leaf = G('''
    .r.
    rRr
    .s.
    ''', {'.': None, 'r': 'grm_rust', 'R': 'grm_straw_dk', 's': 'grm_soot'})
    leaf2 = G('''
    Rr
    rs
    ''', {'.': None, 'r': 'grm_rust', 'R': 'grm_straw_dk', 's': 'grm_soot'})
    if seed == 0:
        img.paste(leaf, 3, 2)
        img.paste(leaf2, 11, 9)
        img.paste(leaf2, 6, 12)
    else:
        img.paste(leaf, 10, 3)
        img.paste(leaf2, 2, 10)
        # a twig and pebbles
        for (x, y) in ((6, 6), (7, 6), (8, 7), (9, 7)):
            img.p[y][x] = 'grm_straw_dk'
        img.p[12][12] = 'grm_ash_md'
        img.p[12][13] = 'grm_ash_dk'
        img.p[11][12] = 'grm_ash_lt'
    return img


FROND = G('''
..r...r.
.rR..rRr
rRs.rRs.
Rsr.Rsr.
sRr.sRr.
.sRssRs.
..sRRs..
...ss...
''', {'.': None, 'r': 'grm_rust', 'R': 'grm_straw_dk', 's': 'grm_soot'})


def grave_brush_layers():
    back = grave_soil_img()
    for ox in (-4, 4, 12):
        back.paste(FROND, ox, 1)
    front = Img(16, 16)
    for ox in (0, 8):
        front.paste(FROND, ox, 8)
    bottom = back.copy()
    bottom.paste(front, 0, 0)
    bottom.p[4][2] = 'grm_straw'
    bottom.p[12][10] = 'grm_straw'
    top = Img(16, 16)
    for y in range(9, 16):
        for x in range(16):
            ty = y - 8
            c = FROND.p[ty][x % 8]
            if c is None or (ty <= 2 and c == 'grm_soot'):
                continue
            top.p[y][x] = c
    return bottom, top


# ---------------------------------------------------------------- the mire

def mud_img(seed=0):
    img = Img(16, 16, 'grm_mud')
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 61 + seed) & 255
            if h < 36:
                img.p[y][x] = 'grm_mud_dk'
            elif h < 44:
                img.p[y][x] = 'grm_peat'
            elif h > 248:
                img.p[y][x] = 'grm_mud_hi'
    # soft blotches
    for (cx, cy, r) in ((4, 4, 2.2), (12, 11, 2.6)):
        for y in range(16):
            for x in range(16):
                dx = (x + 0.5 - cx + 8) % 16 - 8
                dy = (y + 0.5 - cy + 8) % 16 - 8
                if dx * dx + dy * dy <= r * r and (hash2(x, y, 3) & 3):
                    img.p[y][x] = 'grm_mud_dk'
    if seed:
        pud = G('''
        .kkk.
        kwwlk
        kwwwk
        .kkk.
        ''', {'.': None, 'k': 'grm_peat', 'w': 'grm_wat_dk', 'l': 'grm_wat_lt'})
        img.paste(pud, 8, 3)
        img.p[12][3] = 'grm_wisp'
        img.p[13][4] = 'grm_wisp_hi'
        img.p[13][3] = 'grm_moss_dk'
    else:
        img.p[9][9] = 'grm_moss_dk'
        img.p[2][13] = 'grm_mud_hi'
    return img


MUD_A = mud_img()


def moss_img():
    img = Img(16, 16, 'grm_moss')
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 17) & 255
            if h < 50:
                img.p[y][x] = 'grm_moss_dk'
            elif h < 58:
                img.p[y][x] = 'grm_mud_dk'
            elif h > 236:
                img.p[y][x] = 'grm_moss_hi'
    for (x, y) in ((3, 3), (10, 7), (6, 12), (13, 13)):
        img.p[y][x] = 'grm_moss_hi'
        img.p[y + 1][x] = 'grm_moss_dk'
    return img


REED = G('''
.h.
Hmh
Hmh
Hmk
.k.
.r.
''', {'.': None, 'h': 'grm_reed_hi', 'H': 'grm_mud_hi', 'm': 'grm_mud', 'k': 'grm_mud_dk',
      'r': 'grm_reed'})


def mire_reeds_layers():
    bottom = Img(16, 16, 'grm_mud_dk')
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 23) & 15
            if h < 4:
                bottom.p[y][x] = 'grm_peat'
            elif h == 15:
                bottom.p[y][x] = 'grm_mud'
    stalks = [(2, 1, True), (5, 4, False), (8, 0, True), (12, 2, True), (14, 6, False)]
    for (x, ty, cat) in stalks:
        for y in range(ty, 16):
            bottom.p[y][x] = 'grm_reed'
            bottom.p[y][(x + 1) % 16] = 'grm_peat' if y > ty + 5 else 'grm_mud_dk'
        if cat:
            bottom.paste(REED, x - 1, ty)
        else:
            bottom.p[ty][x] = 'grm_reed_hi'
    top = Img(16, 16)
    blades = [(0, 8, 1), (4, 10, -1), (7, 9, 1), (11, 10, 1), (13, 8, -1)]
    for (x, ty, lean) in blades:
        for y in range(ty, 16):
            xx = x + (lean if y < ty + 2 else 0)
            top.p[y][xx % 16] = 'grm_reed_hi' if y < ty + 3 else 'grm_reed'
            if top.p[y][(xx + 1) % 16] is None:
                top.p[y][(xx + 1) % 16] = 'grm_mud_dk'
        top.p[ty][(x + lean) % 16] = 'grm_moss_hi'
    bottom.paste(top, 0, 0)
    return bottom, top


def deck_img():
    img = Img(16, 16, 'grm_wd')
    for y in range(16):
        row = y % 4
        for x in range(16):
            c = 'grm_wd'
            if row == 3:
                c = 'grm_char'
            elif row == 0:
                c = 'grm_wd_hi' if (hash2(x, y, 4) & 3) else 'grm_wd'
            elif (hash2(x // 3, y, 9) & 7) == 0:
                c = 'grm_wd_dk'
            img.p[y][x] = c
        seam = (y // 4 * 5 + 3) % 16
        if row != 3:
            img.p[y][seam] = 'grm_char'
    for (x, y) in ((1, 1), (6, 5), (12, 9), (9, 13)):
        img.p[y][x] = 'grm_pl_dk'
    return img


# ---------------------------------------------------------------- trees

BARK = ['grm_bark_hi', 'grm_bark_lt', 'grm_bark', 'grm_bark_dk']


def tree_from_limbs(limbs, seed, rim=True, ember=False):
    mask = mask_img(16, 32)
    for (pts, r0, r1) in limbs:
        seg_mask(mask, pts, r0, r1)
    img = shade_mask(mask, BARK, seed=seed, rim='grm_bruise_lt' if rim else None, streak=True)
    # knot holes
    for y in range(32):
        for x in range(16):
            if img.p[y][x] and (hash2(x, y, seed + 9) & 63) == 0 and 18 < y < 29:
                img.p[y][x] = 'grm_char'
    if ember:
        for y in range(20, 30):
            for x in range(6, 10):
                if mask[y][x] and mask[y][x - 1] and mask[y][x + 1] and (x * 5 + y * 3) % 7 == 0:
                    img.p[y][x] = 'grm_emb' if (y % 3) else 'grm_emb_dk'
    outline_mask(img, mask, 'grm_out')
    return img


def gnarl_img():
    limbs = [
        ([(7.5, 31.5), (7.2, 26), (7.8, 21), (7.3, 18)], 2.4, 1.7),      # trunk
        ([(7.5, 30.5), (4.0, 31.6)], 1.3, 0.8), ([(8.0, 30.5), (11.8, 31.6)], 1.3, 0.8),   # roots
        ([(7.0, 19), (4.8, 15), (2.6, 11.5), (0.8, 8.5)], 1.6, 0.6),    # left limb
        ([(8.0, 19), (10.4, 14.5), (13.0, 10.5), (15.4, 8.0)], 1.6, 0.6),  # right limb
        ([(7.6, 18), (8.1, 12), (7.0, 6.5), (8.2, 1.5)], 1.3, 0.5),     # leader
        ([(3.6, 13.0), (3.0, 7.0), (4.2, 3.0)], 0.9, 0.5),
        ([(11.6, 12.5), (12.4, 6.0), (11.2, 2.0)], 0.9, 0.5),
        ([(7.6, 9.0), (10.2, 5.0), (12.6, 3.6)], 0.8, 0.5),
        ([(7.3, 11.0), (5.0, 7.0), (5.6, 4.2)], 0.8, 0.5),
        ([(2.4, 11.0), (0.4, 12.6)], 0.6, 0.5),
        ([(13.2, 10.2), (15.4, 12.2)], 0.6, 0.5),
        ([(8.2, 3.0), (6.4, 0.4)], 0.6, 0.5),
    ]
    return tree_from_limbs(limbs, seed=3)


def snag_img():
    limbs = [
        ([(7.6, 31.5), (7.8, 20), (7.4, 8), (7.8, 2.2)], 2.3, 1.1),       # trunk
        ([(7.6, 30.6), (4.6, 31.6)], 1.2, 0.7), ([(8.0, 30.6), (11.2, 31.6)], 1.2, 0.7),
        ([(7.2, 24.5), (4.4, 22.0), (2.2, 22.6)], 0.9, 0.5),
        ([(8.2, 20.5), (11.4, 18.0), (13.6, 18.8)], 0.9, 0.5),
        ([(7.3, 15.0), (4.0, 12.6), (1.4, 13.2)], 0.8, 0.5),
        ([(8.2, 11.5), (11.6, 9.4), (14.4, 10.2)], 0.8, 0.5),
        ([(7.4, 7.0), (5.0, 5.2)], 0.7, 0.5),
        ([(8.1, 5.0), (10.4, 3.4)], 0.7, 0.5),
    ]
    img = tree_from_limbs(limbs, seed=11, rim=False, ember=True)
    # darker charred body
    for y in range(32):
        for x in range(16):
            c = img.p[y][x]
            if c == 'grm_bark':
                img.p[y][x] = 'grm_bark_dk'
            elif c == 'grm_bark_lt':
                img.p[y][x] = 'grm_bark'
            elif c == 'grm_bark_dk':
                img.p[y][x] = 'grm_char'
    # jagged broken top
    for (x, y, c) in ((7, 0, 'grm_out'), (7, 1, 'grm_bark'), (9, 1, 'grm_out'), (9, 2, 'grm_char'),
                      (6, 1, 'grm_out')):
        img.p[y][x] = c
    return img


def cypress_img():
    clumps = [
        (8.0, 4.0, 3.6, 4.2),
        (5.0, 9.0, 3.8, 3.8), (11.0, 9.0, 3.8, 3.8),
        (8.0, 11.5, 4.4, 4.0),
        (4.0, 15.5, 3.8, 3.6), (12.0, 15.5, 3.8, 3.6),
        (8.0, 17.5, 5.0, 3.4),
    ]
    ramp = ['grm_leaf_hi', 'grm_leaf', 'grm_leaf', 'grm_leaf_dk', 'grm_bark_dk']
    can, own = shade_clumps(16, 32, clumps, ramp, 'grm_out', seed=5,
                            clip=lambda x, y: 0 <= x <= 15 and y <= 21)
    img = Img(16, 32)
    # buttressed trunk with knees
    mask = mask_img(16, 32)
    for y in range(19, 32):
        t = (y - 19) / 12.0
        half = 1.6 + 3.8 * t ** 2.2
        for x in range(16):
            if abs(x + 0.5 - 8.0) <= half:
                mask[y][x] = 1
    seg_mask(mask, [(2.5, 31.6), (2.5, 29.4)], 0.9, 0.6)
    seg_mask(mask, [(13.5, 31.6), (13.5, 28.8)], 0.9, 0.6)
    trunk = shade_mask(mask, BARK, seed=21, rim='grm_bruise_lt', streak=True)
    outline_mask(trunk, mask, 'grm_out')
    img.paste(trunk, 0, 0)
    img.paste(can, 0, 0)
    # hanging moss dripping from the crown
    for (x, y0, n) in ((2, 17, 5), (5, 20, 4), (9, 21, 5), (12, 19, 4), (14, 16, 3), (7, 14, 3)):
        for k in range(n):
            y = y0 + k
            if y < 32 and (can.get(x, y) is None or k > 0):
                img.p[y][x] = 'grm_hang' if k < n - 1 else 'grm_leaf'
    # a few bruised leaves in the crown (dusk light)
    for y in range(22):
        for x in range(16):
            if img.p[y][x] == 'grm_leaf_hi' and (hash2(x, y, 7) & 7) == 0:
                img.p[y][x] = 'grm_bruise_lt'
    return img


# ---------------------------------------------------------------- ledges & crags

def ledge_img(ends=None):
    img = Img(16, 16)
    tex_fill(img, ASH_A)
    LIP = 5
    for x in range(16):
        col = {LIP: 'grm_ash_hi' if x % 5 else 'grm_ash_lt', LIP + 1: 'grm_ash_lt',
               LIP + 2: 'grm_ash' if x % 4 != 1 else 'grm_ash_lt', LIP + 3: 'grm_soot'}
        for i in range(4):
            c = 'grm_ash_dkr'
            if i == 0:
                c = 'grm_ash_dk' if x % 3 else 'grm_ash_md'
            elif i == 3:
                c = 'grm_soot' if x % 5 else 'grm_ash_dkr'
            if x % 7 == 4 and i == 1:
                c = 'grm_rust'
            col[LIP + 4 + i] = c
        col[LIP + 8] = 'grm_soot'
        col[LIP + 9] = 'grm_ash_md'
        col[LIP + 10] = 'grm_ash_md' if x % 2 else 'grm_ash'
        for y, c in col.items():
            if y < 16:
                img.p[y][x] = c
    if ends:
        for u in range(3):
            x = u if ends == 'L' else 15 - u
            for y in range(LIP, 16):
                img.p[y][x] = ASH_A.p[y][x]
        x = 3 if ends == 'L' else 12
        for y in range(LIP, 14):
            if img.p[y][x] not in ('grm_ash', 'grm_ash_md', 'grm_ash_lt', 'grm_ash_hi'):
                img.p[y][x] = 'grm_ash_dk'
    return img


def rock_tex(seeds, w=16, h=16, sy=1.7):
    def owner(x, y):
        best, bi = 1e9, -1
        for i, (px, py) in enumerate(seeds):
            dx = (x + 0.5 - px + w / 2) % w - w / 2
            dy = ((y + 0.5 - py + h / 2) % h - h / 2) * sy
            d = dx * dx + dy * dy
            if d < best:
                best, bi = d, i
        return bi
    o = [[owner(x, y) for x in range(w)] for y in range(h)]
    img = Img(w, h)
    for y in range(h):
        for x in range(w):
            me = o[y][x]
            if o[y][(x + 1) % w] != me or o[(y + 1) % h][x] != me:
                c = 'grm_soot'
            elif o[(y - 1) % h][x] != me or o[y][(x - 1) % w] != me:
                c = 'grm_ash_md'
            elif o[(y + 2) % h][x] != me:
                c = 'grm_ash_dkr'
            else:
                c = 'grm_ash_dk'
                hh = hash2(x, y, 13) & 15
                if hh == 0:
                    c = 'grm_ash_dkr'
                elif hh == 1:
                    c = 'grm_ash_md'
            img.p[y][x] = c
    return img


CRAG_FACE = rock_tex([(4, 2), (12, 3), (8, 9), (1, 10), (13, 13.5)])


def crag_img():
    img = CRAG_FACE.copy()
    lip = G('''
    lhllllllhlllllll
    aaaaaaaaaaaaaaaa
    aamaaaaaaamaaaaa
    maMmmamaMmmMamam
    ssssssssssssssss
    ''', {'l': 'grm_ash_lt', 'h': 'grm_ash_hi', 'a': 'grm_ash', 'm': 'grm_ash_md',
          'M': 'grm_ash_dk', 's': 'grm_soot'})
    img.paste(lip, 0, 0)
    for x in (2, 9, 13):
        img.p[5][x] = 'grm_ash_md'
    return img


# ---------------------------------------------------------------- autotiles

PATH_TEX = G('''
................
.........h......
..m.............
...........m....
......h.........
...........k....
.m..........h...
....k...........
.........m......
...h............
................
.............m..
.....m..........
..........h.....
.h..........k...
................
''', {'.': 'grm_ash_lt', 'h': 'grm_ash_hi', 'm': 'grm_ash', 'k': 'grm_bone'})


def path_quads():
    def color_at(d, X, Y, c, v, lx, ly):
        if d < -1.0:
            return ASH_A.p[Y][X]
        if d < 0:
            return 'grm_ash_md'
        if d < 1.0:
            return 'grm_ash'
        return PATH_TEX.p[Y][X]
    return autotile(color_at, E=2.0, R=5.0, Rn=2.0)


WAVES = [(1, 2, 3), (11, 3, 3), (6, 7, 2), (2, 10, 3), (12, 10, 3), (8, 13, 2)]


def water_surface(f):
    img = Img(16, 16, 'grm_wat')
    for y in range(16):
        for x in range(16):
            if (hash2(x, y, 33) & 31) == 0:
                img.p[y][x] = 'grm_wat_dk'
    for (x, y, n) in WAVES:
        x2 = x + (f if (y % 2) else -f)
        for i in range(n):
            img.p[y % 16][(x2 + i) % 16] = 'grm_wat_lt'
        if n >= 3 and f != 1:
            img.p[y % 16][(x2 + 1) % 16] = 'grm_wat_hi'
        img.p[(y + 1) % 16][(x2 + 1) % 16] = 'grm_wat_dk'
    # foxfire reflections drift
    img.p[(4 + f) % 16][9] = 'grm_wisp'
    img.p[(12 - f) % 16][4] = 'grm_moss_dk'
    return img


def water_quads(f):
    surf = water_surface(f)

    def color_at(d, X, Y, c, v, lx, ly):
        if d < 0:
            return MUD_A.p[Y][X]
        if d < 1.0:
            return 'grm_mud_dk'
        if d < 2.0:
            return 'grm_peat'
        if d < 3.0:
            return 'grm_wat_dk'
        if d < 4.0:
            return 'grm_wat' if (X + Y + f) % 3 else 'grm_wat_lt'
        return surf.p[Y][X]
    return autotile(color_at, E=1.0, R=6.0, Rn=2.5)


# ---------------------------------------------------------------- buildings

def roofs(img, x0, x1, y0, y1, ramp=('grm_rf_hi', 'grm_rf_lt', 'grm_rf', 'grm_rf_dk', 'grm_rf_dkr')):
    """A steep shingled roof seen from the front: rows of slates, a light
    ridge, the eave's dark underside at the bottom."""
    for y in range(y0, y1 + 1):
        inset = max(0, (y0 + 6 - y) // 2)
        for x in range(x0 + inset, x1 - inset + 1):
            row = (y - y0) // 3
            col = (x - x0 + (2 if row % 2 else 0)) // 4
            c = ramp[2]
            if (y - y0) % 3 == 0:
                c = ramp[3]
            elif (x - x0 + (2 if row % 2 else 0)) % 4 == 0:
                c = ramp[3]
            elif (y - y0) % 3 == 1 and (hash2(col, row, 3) & 3) == 0:
                c = ramp[1]
            if y <= y0 + 1:
                c = ramp[0] if y == y0 else ramp[1]
            if (hash2(x, y, 71) & 31) == 0 and c == ramp[2]:
                c = 'grm_moss'
            img.set(x, y, c)
        img.set(x0 + inset - 1, y, 'grm_out')
        img.set(x1 - inset + 1, y, 'grm_out')
    for x in range(x0 + 3, x1 - 2):
        img.set(x, y0 - 1, 'grm_out')
    for x in range(x0 - 1, x1 + 2):
        img.set(x, y1 + 1, 'grm_out')
        img.set(x, y1 + 2, ramp[4])


PLANK = {'.': None, 'O': 'grm_out', 'h': 'grm_wd_hi', 'w': 'grm_wd', 'k': 'grm_wd_dk', 'c': 'grm_char',
         'L': 'grm_lamp_hi', 'l': 'grm_lamp', 'd': 'grm_lamp_dk', 'g': 'grm_gl', 'p': 'grm_pl',
         'P': 'grm_pl_hi', 'q': 'grm_pl_dk', 'W': 'grm_wisp_hi', 'V': 'grm_wisp', 'C': 'grm_cloth'}

ROUND_WINDOW = G('''
..OOOO..
.OkkkkO.
OkdlldkO
OkLlLlkO
OklLkLkO
OkdlkdkO
.OkkkkO.
..OOOO..
''', PLANK)

ARCH_DOOR = G('''
...OOOOOO...
..OkkkkkkO..
.OkcwwkwcckO
.OcwwwkwwcO.
OcwwwwkwwwcO
OcwwwwkwwwcO
OcwwwwkwwwcO
OcwwwqkqwwcO
OcwwwwkwwwcO
OcwwwwkwwwcO
OcwwwwkwwwcO
OcwwwwkwwwcO
OcwwwwkwwwcO
OccccccccccO
''', PLANK)


def timber_wall(img, x0, x1, y0, y1):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            k = (x - x0) % 5
            c = 'grm_wd'
            if k == 0:
                c = 'grm_wd_dk'
            elif k == 1:
                c = 'grm_wd_hi' if (hash2(x, y // 4, 2) & 3) else 'grm_wd'
            elif (hash2(x, y, 19) & 15) == 0:
                c = 'grm_wd_dk'
            img.set(x, y, c)
    for x in range(x0, x1 + 1):
        img.set(x, y0, 'grm_char')
        img.set(x, y0 + 1, 'grm_wd_dk' if x % 2 else 'grm_char')
        img.set(x, y1, 'grm_char')
    for y in range(y0, y1 + 1):
        img.set(x0 - 1, y, 'grm_out')
        img.set(x1 + 1, y, 'grm_out')


def stilts_row(img, x0, x1, y0, y1, posts):
    """The underside: shadow, posts in the mud (bank 5 colours only)."""
    tex_fill(img, MUD_A, 0, y0, img.w - 1, y1)
    for y in range(y0, min(y1, y0 + 9) + 1):
        for x in range(x0, x1 + 1):
            img.set(x, y, 'grm_peat' if (y - y0) < 6 or (x + y) % 2 else 'grm_mud_dk')
    for x in range(x0 - 1, x1 + 2):
        img.set(x, y0, 'grm_out')
        img.set(x, y0 + 1, 'grm_wd_dk')
        img.set(x, y0 + 2, 'grm_out')
    for px in posts:
        for y in range(y0 + 3, y1 - 1):
            img.set(px, y, 'grm_out')
            img.set(px + 1, y, 'grm_wd')
            img.set(px + 2, y, 'grm_wd_dk')
            img.set(px + 3, y, 'grm_out')
        for x in range(px - 1, px + 5):
            img.set(x, y1 - 1, 'grm_mud_dk')
        img.set(px + 1, y1 - 2, 'grm_moss')


def stairs(img, x0, y0, w, n):
    for i in range(n):
        y = y0 + i * 3
        for x in range(x0 - i, x0 + w + i):
            img.set(x, y, 'grm_out')
            img.set(x, y + 1, 'grm_wd_hi')
            img.set(x, y + 2, 'grm_wd' if i < n - 1 else 'grm_wd_dk')
        img.set(x0 - i - 1, y + 1, 'grm_out')
        img.set(x0 + w + i, y + 1, 'grm_out')


def lantern_hang(img, x, y):
    L = G('''
    .O.
    .O.
    OOO
    OLO
    OlO
    OdO
    .O.
    ''', {'.': None, 'O': 'grm_out', 'L': 'grm_lamp_hi', 'l': 'grm_lamp', 'd': 'grm_wd_dk'})
    img.paste(L, x, y)


def plate(img, text, x, y, gf):
    """A small painted plate with the 4x5 sign font."""
    w = len(text) * 4 + 3
    for yy in range(y, y + 9):
        for xx in range(x, x + w):
            edge = yy in (y, y + 8) or xx in (x, x + w - 1)
            img.set(xx, yy, 'grm_out' if edge else 'grm_pl_hi')
    cx = x + 2
    for ch in text:
        glyph = gf.FONT.get(ch)
        if glyph:
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit in '#X1':
                        img.set(cx + gx, y + 2 + gy, 'grm_char')
        cx += 4


def stilt_house(gf, kind='house', w=4):
    W, H = w * 16, 64
    img = Img(W, H)
    tex_fill(img, MUD_A)
    stilts_row(img, 3, W - 4, 44, 63, posts=[6, W // 2 - 2, W - 10])
    timber_wall(img, 4, W - 5, 24, 44)
    roofs(img, 1, W - 2, 3, 21)
    # chimney with a curl of pale smoke
    for y in range(0, 8):
        for x in range(W - 18, W - 12):
            img.set(x, y, 'grm_out' if x in (W - 18, W - 13) or y == 0 else
                    ('grm_rf_dk' if (x + y) % 3 else 'grm_rf'))
    door_x = 18 if w == 4 else 34
    img.paste(ARCH_DOOR, door_x, 30)
    stairs(img, door_x + 1, 45, 10, 6)
    wins = [44] if w == 4 else [6, 60]
    if w == 4:
        wins = [42]
    for wx in wins:
        img.paste(ROUND_WINDOW, wx, 30)
    if kind == 'apothecary':
        for y in range(31, 37):
            for x in range(wins[0] + 1, wins[0] + 7):
                c = img.get(x, y)
                if c == 'grm_lamp_hi':
                    img.set(x, y, 'grm_wisp_hi')
                elif c in ('grm_lamp', 'grm_lamp_dk'):
                    img.set(x, y, 'grm_wisp')
        # a mortar-and-bottle sign on the wall
        sign = G('''
        ..OO..
        .OWWO.
        OWVVWO
        OVVVVO
        .OOOO.
        ''', PLANK)
        img.paste(sign, 5, 32)
        plate(img, 'APOTH', 4, 12, gf)
    elif kind == 'shop':
        lantern_hang(img, 8, 22)
        plate(img, 'SHOP', 20, 12, gf)
    elif kind == 'hearth':
        flame = G('''
        ....O....
        ...OLO...
        ...OlLO..
        ..OlLlO..
        .OdlLlLO.
        .OdlLLldO
        OdllLLldO
        OdlLLLldO
        .OddlddO.
        ..OOOOO..
        ''', PLANK)
        img.paste(flame, W // 2 - 4, 4)
        lantern_hang(img, 26, 22)
        lantern_hang(img, 51, 22)
        plate(img, 'HEARTH', 4, 12, gf)
    else:
        lantern_hang(img, 8, 22)
    return img


def crypt_hall(gf):
    """The LANTERN CRYPT: a stone mausoleum with a lantern frieze."""
    W, H = 80, 64
    img = Img(W, H)
    tex_fill(img, MUD_A)
    ST = {'.': None, 'O': 'grm_out', 'h': 'grm_st_hi', 'l': 'grm_st_lt', 's': 'grm_st', 'd': 'grm_st_dk',
          'L': 'grm_lamp_hi', 'm': 'grm_lamp', 'b': 'grm_bone', 'k': 'grm_peat', 'M': 'grm_moss'}
    # body
    for y in range(20, 56):
        for x in range(6, 74):
            course = (y - 20) // 5
            off = 6 if course % 2 else 0
            c = 'grm_st'
            if (y - 20) % 5 == 4:
                c = 'grm_st_dk'
            elif (x + off) % 12 == 0:
                c = 'grm_st_dk'
            elif (y - 20) % 5 == 0:
                c = 'grm_st_lt'
            if (hash2(x, y, 8) & 31) == 0:
                c = 'grm_moss'
            img.set(x, y, c)
    for y in range(20, 56):
        img.set(5, y, 'grm_out')
        img.set(74, y, 'grm_out')
    # pediment
    for y in range(2, 20):
        half = (y - 2) * 2.1 + 4
        for x in range(6, 74):
            if abs(x + 0.5 - 40) <= half:
                edge = abs(x + 0.5 - 40) > half - 1.2
                c = 'grm_out' if edge else ('grm_st_hi' if x < 40 and abs(x + 0.5 - 40) > half - 3 else
                                             ('grm_st_lt' if (y % 4) else 'grm_st'))
                img.set(x, y, c)
    for x in range(4, 76):
        img.set(x, 19, 'grm_out')
        img.set(x, 20, 'grm_st_hi')
        img.set(x, 21, 'grm_st_lt')
        img.set(x, 22, 'grm_st_dk')
    # lantern emblem in the pediment
    emb = G('''
    ...OO...
    ..O..O..
    .OOOOOO.
    .OLLLLO.
    OLmLLmLO
    OLmmmmLO
    OLLmmLLO
    .OOOOOO.
    ''', ST)
    img.paste(emb, 36, 8)
    # columns
    for cx in (12, 60):
        for y in range(23, 54):
            for x in range(cx, cx + 8):
                c = 'grm_st_lt' if x < cx + 3 else ('grm_st' if x < cx + 6 else 'grm_st_dk')
                if x in (cx, cx + 7):
                    c = 'grm_out'
                img.set(x, y, c)
        for x in range(cx - 1, cx + 9):
            img.set(x, 23, 'grm_out')
            img.set(x, 24, 'grm_st_hi')
            img.set(x, 53, 'grm_out')
    # dark arched doorway with a faint glow deep inside
    for y in range(28, 56):
        for x in range(30, 50):
            dx = abs(x + 0.5 - 40)
            top = 28 + (dx * dx) / 14.0
            if y >= top:
                edge = y < top + 1.5 or dx > 9
                c = 'grm_out' if edge else 'grm_peat'
                if not edge and 44 <= y <= 50 and dx < 3:
                    c = 'grm_lamp' if y > 46 and dx < 1.5 else 'grm_mud_dk'
                img.set(x, y, c)
    # wall lanterns
    for lx in (22, 54):
        g = G('''
        .OOO.
        OLLmO
        OLmmO
        OmmmO
        .OOO.
        ..O..
        ''', ST)
        img.paste(g, lx, 34)
    # steps
    for i, y in enumerate((56, 59, 62)):
        for x in range(26 - i * 2, 54 + i * 2):
            img.set(x, y, 'grm_out')
            if y + 1 < H:
                img.set(x, y + 1, 'grm_st_hi' if i < 2 else 'grm_st_lt')
            if y + 2 < H:
                img.set(x, y + 2, 'grm_st')
    return img


def bone_gate():
    """The sealed OSSUARY gate: a bone arch in a dark mound, a round stone
    door with six empty crest sockets."""
    W, H = 80, 64
    img = Img(W, H)
    tex_fill(img, MUD_A)
    # the mound of dark rock
    for y in range(0, 58):
        for x in range(W):
            dx = (x + 0.5 - 40) / 40.0
            top = 8 + 30 * dx * dx
            if y >= top:
                h = hash2(x // 3, y // 2, 4) & 15
                c = 'grm_st_dk' if h < 11 else ('grm_st' if h < 14 else 'grm_peat')
                if y < top + 1.5:
                    c = 'grm_out'
                elif y < top + 3:
                    c = 'grm_moss' if (x % 5) else 'grm_st'
                img.set(x, y, c)
    # the bone arch: stacked long bones with skull keystones (stylised)
    cx, cy = 40.0, 40.0
    for y in range(4, 58):
        for x in range(8, 72):
            r = math.hypot((x + 0.5 - cx) / 1.05, y + 0.5 - cy)
            if 24 <= r <= 31 and y <= 57:
                ang = math.atan2(y + 0.5 - cy, x + 0.5 - cx)
                band = int((ang + math.pi) / (math.pi / 14))
                c = 'grm_bone' if band % 2 else 'grm_bone_hi'
                if r < 25 or r > 30:
                    c = 'grm_out'
                elif abs(r - 27.5) < 0.6:
                    c = 'grm_bone_dk'
                img.set(x, y, c)
    skull = G('''
    .OOOO.
    OhhhhO
    OkhhkO
    OhhhhO
    .OddO.
    ''', {'.': None, 'O': 'grm_out', 'h': 'grm_bone_hi', 'k': 'grm_peat', 'd': 'grm_bone_dk'})
    for (sx, sy) in ((37, 8), (16, 20), (58, 20)):
        img.paste(skull, sx, sy)
    # the round sealed door
    for y in range(18, 58):
        for x in range(18, 62):
            r = math.hypot(x + 0.5 - 40, (y + 0.5 - 40) * 1.02)
            if r <= 22:
                c = 'grm_st' if r < 21 else 'grm_out'
                if r < 21:
                    if (x + 0.5 - 40) < -8 and r > 17:
                        c = 'grm_st_lt'
                    elif r > 18.5:
                        c = 'grm_st_dk'
                    if abs(x + 0.5 - 40) < 0.8 and y > 22:
                        c = 'grm_out'
                img.set(x, y, c)
    # six empty crest sockets around a centre boss
    for k in range(6):
        a = -math.pi / 2 + k * math.pi / 3
        sx, sy = 40 + 13 * math.cos(a), 40 + 13 * math.sin(a)
        for y in range(int(sy) - 3, int(sy) + 4):
            for x in range(int(sx) - 3, int(sx) + 4):
                d = math.hypot(x + 0.5 - sx, y + 0.5 - sy)
                if d <= 3.2:
                    img.set(x, y, 'grm_out' if d > 2.3 else ('grm_peat' if d > 1.0 else 'grm_wisp'))
    for y in range(35, 46):
        for x in range(35, 46):
            d = math.hypot(x + 0.5 - 40.5, y + 0.5 - 40.5)
            if d <= 4.5:
                img.set(x, y, 'grm_out' if d > 3.6 else ('grm_bone' if d > 2 else 'grm_bone_dk'))
    # threshold
    for x in range(20, 60):
        img.set(x, 58, 'grm_out')
        img.set(x, 59, 'grm_st_lt')
        img.set(x, 60, 'grm_st')
        img.set(x, 61, 'grm_out')
    return img


# ---------------------------------------------------------------- build

def add_anim_terrain(gf, ts, out, frames, bank, period):
    first = len(ts.tiles)
    anim = [[] for _ in frames]
    ents = []
    for (dx, dy) in gf.QUADS:
        fr = [ts.indices(gf.img_pix(f.crop(dx, dy, 8, 8)), bank) for f in frames]
        t = ts.add_raw(fr[0])
        for i in range(len(frames)):
            anim[i].append(fr[i])
        ents.append(t | (bank << 12))
    out['anims'].append((first, anim, period))
    return ents


def add_water(gf, ts, out, bank=1):
    wq = [water_quads(f) for f in range(3)]
    water_q = [[0] * 5 for _ in range(4)]
    anim = [[], [], []]
    first = len(ts.tiles)
    seen = {}
    for c in range(4):
        for v in range(5):
            frames = tuple(ts.indices(gf.img_pix(wq[f][c][v]), bank) for f in range(3))
            if frames not in seen:
                seen[frames] = ts.add_raw(frames[0])
                for f in range(3):
                    anim[f].append(frames[f])
            water_q[c][v] = seen[frames] | (bank << 12)
    out['anims'].append((first, anim, 24))
    out['water_q'] = water_q


def build(gf, name):
    gf.register_colors(dg.ALL_COLORS)
    gf.check_banks(name, dg.GRIM_BANKS)
    ts = gf.TileSet(name, dg.GRIM_BANKS)
    out = {'ts': ts, 'meta_b': [], 'meta_t': [], 'terrain': TERRAIN, 'anims': [], 'docs': TERRAIN_DOC}
    add_water(gf, ts, out)
    ember_ents = add_anim_terrain(gf, ts, out, embers_frames(), 0, 20)
    ag_b, ag_t = ash_grass_layers()
    gb_b, gb_t = grave_brush_layers()
    mr_b, mr_t = mire_reeds_layers()
    gn, sn, cy = gnarl_img(), snag_img(), cypress_img()
    imgs = {
        'ASH': (ASH_A, None), 'ASH2': (ash_img(1, 1), None), 'ASH3': (ash_img(0, 2), None),
        'ASH_GRASS': (ag_b, ag_t), 'SCORCH': (scorch_img(), None), 'COBBLE': (cobble_img(), None),
        'GRAVE_SOIL': (grave_soil_img(), None), 'GRAVE_SOIL2': (grave_soil_img(1), None),
        'GRAVE_BRUSH': (gb_b, gb_t),
        'MUD': (MUD_A, None), 'MUD2': (mud_img(1), None), 'MOSS': (moss_img(), None),
        'MIRE_REEDS': (mr_b, mr_t), 'DECK': (deck_img(), None),
        'GNARL_TOP': (gn.crop(0, 0, 16, 16), None), 'GNARL_BOTTOM': (gn.crop(0, 16, 16, 16), None),
        'SNAG_TOP': (sn.crop(0, 0, 16, 16), None), 'SNAG_BOTTOM': (sn.crop(0, 16, 16, 16), None),
        'CYPRESS_TOP': (cy.crop(0, 0, 16, 16), None), 'CYPRESS_BOTTOM': (cy.crop(0, 16, 16, 16), None),
        'LEDGE': (ledge_img(), None), 'LEDGE_L': (ledge_img('L'), None), 'LEDGE_R': (ledge_img('R'), None),
        'CRAG': (crag_img(), None), 'CRAG_FACE': (CRAG_FACE.copy(), None),
    }
    for tname in TERRAIN:
        if tname == 'EMBERS':
            out['meta_b'].append(ember_ents)
            out['meta_t'].append([0, 0, 0, 0])
            continue
        bottom, top = imgs[tname]
        if tname in OVERLAY:
            gf.add_overlay_terrain(ts, out, tname, bottom, top=tname.endswith('_TOP'))
            continue
        out['meta_b'].append(ts.meta(bottom, where='grim.' + tname))
        out['meta_t'].append(ts.meta(top, where='grim.%s.top' % tname, opaque=False) if top else [0, 0, 0, 0])
    gf.add_stamps(ts, out, [
        ('HOUSE', stilt_house(gf, 'house'), (5, 7), 'stilt house, door (stairs) col 1 row 3'),
        ('SHOP', stilt_house(gf, 'shop'), (5, 7), 'DUSK SHOP, hanging lantern sign, door col 1 row 3'),
        ('APOTHECARY', stilt_house(gf, 'apothecary'), (5, 7), 'apothecary, green window, door col 1 row 3'),
        ('HEARTH', stilt_house(gf, 'hearth', 5), (5, 7), 'DUSKMERE HEARTH HALL, flame, door col 2 row 3'),
        ('CRYPT_HALL', crypt_hall(gf), (6,), 'the LANTERN CRYPT mausoleum, door col 2 row 3'),
        ('BONE_GATE', bone_gate(), (6,), 'the sealed OSSUARY gate (no door: the gate warden opens it)'),
    ])
    pq = path_quads()
    out['path_q'] = [[ts.add(gf.img_pix(pq[c][v]), (0,), 'grim.path[%d][%d]' % (c, v))
                      for v in range(5)] for c in range(4)]
    attrs = {'ASH_GRASS': gf.A_GRASS, 'GRAVE_BRUSH': gf.A_GRASS, 'MIRE_REEDS': gf.A_GRASS,
             'LEDGE': gf.A_LEDGE, 'LEDGE_L': gf.A_LEDGE, 'LEDGE_R': gf.A_LEDGE,
             'CRAG': gf.A_SOLID, 'CRAG_FACE': gf.A_SOLID, 'BONE_GATE': gf.A_SOLID}
    return gf.finish_tileset(
        out, name, 'GR', attrs=attrs, ground=GROUND, overlay=list(OVERLAY),
        legend={'.': [('ASH3', 1), ('ASH2', 4), ('ASH', 11)], ',': 'ASH_GRASS', ':': 'SCORCH',
                'e': 'EMBERS', '#': 'COBBLE', '=': 'PATH', '~': 'WATER',
                'g': [('GRAVE_SOIL2', 5), ('GRAVE_SOIL', 11)], 'b': 'GRAVE_BRUSH',
                'm': [('MUD2', 3), ('MUD', 13)], 'M': 'MOSS', 'r': 'MIRE_REEDS', 'd': 'DECK',
                'T': 'GNARL_TOP', 't': 'GNARL_BOTTOM', 'P': 'SNAG_TOP', 'p': 'SNAG_BOTTOM',
                'Y': 'CYPRESS_TOP', 'y': 'CYPRESS_BOTTOM', 'L': 'LEDGE', '[': 'LEDGE_L',
                ']': 'LEDGE_R', 'C': 'CRAG', 'c': 'CRAG_FACE'},
        oob='GNARL_TOP', default_ground='ASH', backdrop=(32, 26, 42),
        doors=[('HOUSE', 1, 3), ('SHOP', 1, 3), ('APOTHECARY', 1, 3), ('HEARTH', 2, 3),
               ('CRYPT_HALL', 2, 3)])
