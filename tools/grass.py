#!/usr/bin/env python3
"""Tall grass for every tileset: procedural blades, wind, rustle and the
front-blade overlay drawn over people (tools/gen_field_gfx.py calls
install() from finish_tileset; the engine side is src/game/grass.c).

A grass *variety* (meadow grass, reeds, snowy tussocks, ember brush...) is
a STYLE: colours from the tileset's banks plus blade shape parameters.
Every variety gets

  * VARIANTS cell looks (NAME, NAME_B, NAME_C: different clumps, picked by
    cell hash through the legend so a field never looks tiled),
  * WIND wind poses per variant, swapped as a tile animation of the
    variant's own four BG tiles (each variant sways at its own phase),
  * RUSTLE frames of the whole cell and of its front blades, played as
    sprites when someone steps in (blades part, spring back),
  * the FRONT blades of every pose: a 16x16 sprite drawn over whoever
    stands in the cell, so only their lower part hides behind ragged
    blade tips (the cell above no longer cuts through heads),
  * two 8x8 particle frames (leaves, snow, ash, sparks, petals).

Nothing is drawn on the BG top layer for tall grass any more.

Standard library only. Colours are names (gen_field_gfx.C); a colour a
style asks for that is missing from the variety's bank is replaced by the
nearest colour of that bank.
"""

import math

from pixelart import Img, hash2

VARIANTS = 3
WIND = 4           # wind poses: rest, lean right, rest, lean left
RUSTLE = 4         # rustle frames (the engine shows each for GRASS_RUSTLE_STEP frames)
PARTS = [3, 2, -1, 1]  # how far the blades part in each rustle frame

# 4x4 ordered dither thresholds (0..15)
BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def bayer(x, y):
    return BAYER4[y & 3][x & 3]


# ---------------------------------------------------------------------------
# Styles. Ramps run light -> dark. 'ground' names a terrain whose texture
# shows between the back blade tips (it fades by ordered dither into 'gap',
# the shadow deep in the grass), so a patch sits naturally in its ground.
# ---------------------------------------------------------------------------

def style(**kw):
    s = dict(
        ramp=['g_hi', 'g_lt', 'g_base', 'g_mid', 'g_dk'],
        shade='g_dkr',                  # tuft outlines
        gap=['g_mid', 'g_dk', 'g_dkr'],  # deep-grass shadow, top -> bottom
        ground='GRASS',                 # terrain showing between the back tips
        ground_rows=2,                  # rows of ground above the shadow
        back=['tuft', 'fan', 'pair'],   # tuft shapes of the back row
        front=['tuft', 'fan', 'pair'],  # ... and of the front row
        back_n=3, front_n=3,            # tufts per row
        back_base=9,                    # base line of the back row
        sway=1.0,                       # wind lean at the tips (px)
        period=14,                      # frames per wind pose
        heads=None,                     # [(colour per wind pose, chance per tip, shape)]
        caps=None,                      # colour dusted on some tips (snow)
        cap_chance=0.0,
        particles=['g_hi', 'g_lt'],
        part_kind='leaf',
    )
    s.update(kw)
    return s


MEADOW = style()
FLOWER = style(heads=[(['f_red', 'f_red', 'f_redd', 'f_red'], 0.18, 'flower'),
                      (['f_yel', 'white', 'f_yel', 'f_yeld'], 0.14, 'flower'),
                      (['white', 'white', 'f_yel', 'white'], 0.12, 'dot')],
               particles=['f_red', 'white'], part_kind='petal')
GOLDEN = style(ramp=['s_hi', 's_base', 's_mid', 's_dk', 'g_dk'], shade='g_dkr',
               gap=['s_mid', 's_dk', 'g_dkr'], ground=None, period=12,
               heads=[(['s_hi', 's_hi', 'white', 's_hi'], 0.3, 'seed')],
               particles=['s_hi', 'f_yel'], part_kind='seed')
REEDS = style(ramp=['g_hi', 'g_lt', 'g_base', 't_base', 't_mid'], shade='t_dk',
              gap=['t_base', 't_mid', 't_dk'], back=['stalk', 'reed', 'stalk'], front=['reed', 'stalk', 'pair'],
              back_n=3, front_n=3, sway=1.0, period=18,
              heads=[(['k_base', 'k_base', 'k_dk', 'k_base'], 0.0, 'cattail')],
              particles=['k_lt', 'g_hi'], part_kind='fluff')
DUNE = style(shade='s_dk', gap=['s_mid', 's_dk', 'g_dk'], ground='SAND', ground_rows=3,
             back=['pair', 'reed', 'pair'], front=['pair', 'fan', 'reed'], period=16,
             heads=[(['s_hi', 's_base', 's_hi', 's_hi'], 0.35, 'seed')],
             particles=['s_hi', 's_base'], part_kind='sand')
SNOWY = style(ramp=['fg_hi', 'fg_hi', 'fg_base', 'fg_dk', 'fg_dkr'], shade='fg_dkr',
              gap=['sn_mid', 'sn_dk', 'fg_dkr'], ground='SNOW', ground_rows=2, period=16,
              caps='sn_hi', cap_chance=0.6, particles=['sn_hi', 'sn_lt'], part_kind='snow')
GLOWMOSS = style(ramp=['mo_hi', 'mo_hi', 'mo_base', 'mo_dk', 'cv_dk'], shade='cv_dkr',
                 gap=['cv_mid', 'cv_dk', 'cv_dkr'], ground='FLOOR',
                 rows=[('back', 5, ['moss'], 3), ('back', 10, ['moss', 'frond'], 3),
                       ('front', 15, ['moss'], 3)], ground_rows=0, period=20,
                 heads=[(['cr_lt', 'cr_hi', 'cr_lt', 'cr_base'], 0.45, 'dot')],
                 particles=['cr_hi', 'cr_lt'], part_kind='spark')
ASHGRASS = style(ramp=['grm_straw_hi', 'grm_straw_hi', 'grm_straw', 'grm_straw_dk', 'grm_ash_dk'],
                 shade='grm_soot', gap=['grm_ash_md', 'grm_ash_dk', 'grm_ash_dkr'], ground='ASH',
                 back=['pair', 'tuft', 'reed'], front=['pair', 'fan', 'tuft'], period=12,
                 heads=[(['grm_bone', 'grm_straw_hi', 'grm_bone', 'grm_bone'], 0.2, 'seed')],
                 particles=['grm_ash_hi', 'grm_ash_lt'], part_kind='ash')
BRACKEN = style(ramp=['grm_straw', 'grm_rust', 'grm_straw_dk', 'grm_ash_dk', 'grm_ash_dkr'],
                shade='grm_soot', gap=['grm_ash_dk', 'grm_ash_dkr', 'grm_soot'], ground='GRAVE_SOIL',
                back=['frond', 'frond', 'pair'], front=['frond', 'fan'], back_n=3, front_n=2, period=16,
                heads=[(['grm_rust', 'grm_emb_dk', 'grm_rust', 'grm_rust'], 0.3, 'dot')],
                particles=['grm_rust', 'grm_straw'], part_kind='leaf')
MIREREEDS = style(ramp=['grm_reed_hi', 'grm_reed_hi', 'grm_reed', 'grm_moss_dk', 'grm_mud_dk'],
                  shade='grm_peat', gap=['grm_mud', 'grm_mud_dk', 'grm_peat'], ground='MUD',
                  back=['reed', 'stalk', 'pair'], front=['reed', 'stalk', 'pair'], period=20,
                  heads=[(['grm_peat', 'grm_peat', 'grm_mud_dk', 'grm_peat'], 0.0, 'cattail'),
                         (['grm_wisp', 'grm_wisp_hi', 'grm_wisp', 'grm_moss_hi'], 0.12, 'dot')],
                  particles=['grm_wisp_hi', 'grm_wisp'], part_kind='spark')
EMBER = style(ramp=['va_lt', 'va_lt', 'va_mid', 'va_dk', 'vb_dk'], shade='vb_out',
              gap=['va_dk', 'vb_dk', 'vb_out'], ground='ASH',
              back=['pair', 'frond', 'tuft'], front=['pair', 'fan', 'frond'], period=10,
              heads=[(['eb_hi', 'su_y', 'eb_lt', 'eb_hi'], 0.35, 'dot'),
                     (['eb_lt', 'eb_base', 'eb_hi', 'eb_lt'], 0.25, 'seed')],
              particles=['eb_hi', 'su_y'], part_kind='spark')
EMBERMOSS = style(ramp=['eb_lt', 'eb_lt', 'eb_base', 'eb_dk', 'vb_dk'], shade='vb_out',
                  gap=['vb_base', 'vb_dk', 'vb_out'], ground='CAVE_FLOOR',
                  rows=[('back', 5, ['moss'], 3), ('back', 10, ['moss'], 3),
                        ('front', 15, ['moss', 'frond'], 3)], ground_rows=0, period=18,
                  heads=[(['su_y', 'eb_hi', 'su_y', 'eb_hi'], 0.45, 'dot')],
                  particles=['eb_hi', 'su_y'], part_kind='spark')
MOONPETAL = style(ramp=['dg_hi', 'dg_lt', 'dg_base', 'dg_mid', 'dg_dk'], shade='dg_dk',
                  gap=['dg_mid', 'dg_dk', 'ds_dk'], ground='GRASS', period=20,
                  heads=[(['dp_base', 'dp_hi', 'ds_hi', 'dp_hi'], 0.28, 'flower'),
                         (['vcr_base', 'ds_hi', 'vcr_base', 'dp_hi'], 0.15, 'dot')],
                  particles=['dp_hi', 'dp_base'], part_kind='petal')


# tileset -> [(terrain name, style, legend char or None, doc)]; an existing
# terrain is regenerated, a new one is added (legend char required).
REGISTRY = {
    'town': [('TALLGRASS', MEADOW, None, None)],
    'wild': [('TALLGRASS', MEADOW, None, None), ('REEDS', REEDS, None, None),
             ('FLOWERGRASS', FLOWER, 'w', 'tall grass in flower (wild kin roam; flowers shimmer)'),
             ('GOLDGRASS', GOLDEN, 'g', 'dry golden tall grass (wild kin roam)')],
    'city': [('TALLGRASS', MEADOW, None, None)],
    'coast': [('TALLGRASS', MEADOW, None, None), ('DUNEGRASS', DUNE, None, None)],
    'snow': [('DRIFT', SNOWY, None, None)],
    'cave': [('MOSS', GLOWMOSS, None, None)],
    'grim': [('ASH_GRASS', ASHGRASS, None, None), ('GRAVE_BRUSH', BRACKEN, None, None),
             ('MIRE_REEDS', MIREREEDS, None, None)],
    'volcanic': [('EMBERBRUSH', EMBER, None, None), ('EMBERMOSS', EMBERMOSS, None, None)],
    'dream': [('MOONPETAL', MOONPETAL, None, None)],
}


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

# Tuft templates: h l b m d = the style's ramp (light -> dark), O = its
# outline colour, H = a seed head / cattail (the style's head colour).
# Rows are top -> bottom; the bottom row stands on the tuft's base line.
TUFTS = {
    'tuft': """
..h...h.
.hlO.hlO
.hlmOhlm
hllmdllm
hlmmdlmd
lmmddmmd
mmdddmdd
ddddOddd
dOddddOd
""",
    'fan': """
....h...
.h..lO..
.lO.lm.h
hlmOlmOl
llmdlmdl
lmmdmmdm
lmddmddm
mmdddddd
mdddOddd
dddOdddO
""",
    'pair': """
.h....
.lh...
hlmO.h
llmOhl
lmmdlm
lmddlm
mmddmd
mdddmd
ddOddd
dOdddO
""",
    'stalk': """
..H..
..H..
..H..
..m..
..l..
.hl..
hlm..
lm.h.
m..lm
...lm
..hmd
..lmd
.lmdd
.mddd
""",
    'reed': """
.h...
.l...
.lh..
.lm..
hlm..
lm...
lm.h.
m..lm
..hmd
..lmd
.lmdd
.mddd
""",
    'frond': """
.hl.....
h..l.hl.
...lh..l
..hlm...
.hlmm.l.
.l.mdlm.
...mdm..
..mddd..
.mdddd..
""",
    'moss': """
.h..h...
hlOhlOh.
lmdlmdlO
mddmddmd
dddddddd
""",
}


def parse_tuft(text):
    rows = [r for r in text.strip('\n').split('\n') if r.strip()]
    pts = []
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != '.':
                pts.append((x, y, ch))
    return pts, len(rows), max(len(r) for r in rows)


TUFT_PTS = {k: parse_tuft(v) for k, v in TUFTS.items()}


class Tuft:
    __slots__ = ('shape', 'x', 'base', 'layer', 'flip', 'heads', 'caps', 'ph')


def make_blades(st, variant):
    """The tufts of one variant: a back row (bases at y 9) and a front row
    (bases at the cell bottom), jittered per variant; x wraps around."""
    seed = 17 + variant * 31
    rnd = lambda k, n: hash2(variant * 7 + k, n, seed) / 65536.0  # noqa: E731
    tufts = []
    rows = st.get('rows') or [('back', st['back_base'], st['back'], st['back_n']),
                              ('front', 15, st['front'], st['front_n'])]
    for li, (layer, base, shapes, count) in enumerate(rows):
        x0 = rnd(li, 1) * 16
        for c in range(count):
            t = Tuft()
            t.shape = shapes[int(rnd(li * 8 + c, 2) * len(shapes)) % len(shapes)]
            w = TUFT_PTS[t.shape][2]
            t.x = int(x0 + c * 16.0 / count + (rnd(li * 8 + c, 3) - 0.5) * 3) - w // 2
            j = rnd(li * 8 + c, 4)
            t.base = base + (1 if j < 0.3 else 0) - (1 if layer == 'front' and j > 0.8 else 0)
            t.layer = layer
            t.flip = rnd(li * 8 + c, 5) < 0.5
            t.ph = rnd(li * 8 + c, 6)
            t.heads = [rnd(li * 8 + c, 10 + k) for k in range(8)]
            t.caps = [rnd(li * 8 + c, 20 + k) for k in range(8)]
            tufts.append(t)
    tufts.sort(key=lambda t: (t.layer != 'back', t.base))
    return tufts


def tuft_pixels(t, wave, part):
    """Yield (x, y, letter, is_tip) for a tuft bent by the wind (wave, px
    at the tip) and parted by a rustle (part: pushed away from the centre,
    the top row squashed down when it is strong)."""
    pts, h, w = TUFT_PTS[t.shape]
    centre = (t.x + w / 2.0) % 16
    push = part * (1 if centre >= 8 else -1) * (1.0 if t.layer == 'front' else 0.6)
    squash = 1 if abs(part) >= 3 else 0
    top = t.base - h + 1
    tips = set()
    seen_cols = set()
    for (x, y, ch) in sorted(pts, key=lambda p: p[1]):
        if ch in 'hH' and x not in seen_cols:
            tips.add((x, y))
        seen_cols.add(x)
    for (x, y, ch) in pts:
        if squash and y == 0:
            continue
        r = y / float(h)                      # 0 at the top
        bend = max(0.0, 1.0 - r / 0.55)       # the upper half bends
        dx = (wave * (0.85 + 0.3 * t.ph) + push) * bend
        xx = (w - 1 - x) if t.flip else x
        px = int(math.floor(t.x + xx + dx + 0.5)) % 16
        py = top + y + (squash if y < h // 2 else 0)
        yield px, py, ch, (x, y) in tips


def ground_texture(st, ground_img):
    """16x16 of the ground colours (or the lightest gap colour)."""
    if ground_img is None:
        return Img(16, 16, st['gap'][0])
    return ground_img


def render_cell(st, tufts, ground_img, wave, part=0, pose=0):
    """-> (bottom opaque Img, front Img (transparent))."""
    img = Img(16, 16)
    g = ground_texture(st, ground_img)
    gap = st['gap']
    # background: the ground between the back tips, dithered down into the
    # shadow deep in the grass
    for y in range(16):
        for x in range(16):
            # a wavy edge: the shadow starts a row higher or lower per column
            wob = (hash2(x, 3, int(tufts[0].ph * 999)) % 3) - 1
            d = (y - st['ground_rows'] - wob) / 7.0
            lvl = max(0.0, d) * 3.0
            k = int(lvl)
            if bayer(x, y) < (lvl - k) * 16:
                k += 1
            k = min(k, 3)
            img.p[y][x] = g.p[y][x] if k == 0 else gap[k - 1]
    front = Img(16, 16)
    ramp, shade = st['ramp'], st['shade']
    tone = {'h': 0, 'l': 1, 'b': 2, 'm': 3, 'd': 4}
    for t in tufts:
        back = t.layer == 'back'
        ti = 0
        for (x, y, ch, tip) in tuft_pixels(t, wave, part):
            if not (0 <= y < 16):
                continue
            if ch == 'O':
                c = shade
            elif ch == 'H':
                c = st['heads'][0][0][pose % WIND] if st['heads'] else ramp[3]
            else:
                k = tone[ch] + (1 if back and ch != 'h' else 0)
                c = ramp[min(4, k)]
            extra = []
            if tip:
                if st['caps'] and t.caps[ti % 8] < st['cap_chance']:
                    c = st['caps']
                elif st['heads'] and ch == 'h':
                    r, acc = t.heads[ti % 8], 0.0
                    for (cols, chance, shape) in st['heads']:
                        acc += chance
                        if r < acc:
                            c = cols[pose % len(cols)]
                            if shape == 'flower':
                                c2 = cols[(pose + 1) % len(cols)]
                                extra = [((x - 1) % 16, y, c), ((x + 1) % 16, y, c), (x, y + 1, c2)]
                            elif shape == 'seed':
                                extra = [(x, y + 1, c)]
                            break
                ti += 1
            for (ex, ey, ec) in [(x, y, c)] + extra:
                if 0 <= ey < 16:
                    img.p[ey][ex] = ec
                    if not back:
                        front.p[ey][ex] = ec
    # the overlay: front tufts, and the bottom rows in full so feet hide
    for y in range(12, 16):
        for x in range(16):
            front.p[y][x] = img.p[y][x]
    # a ragged, dithered edge just above the solid rows
    for y in (10, 11):
        for x in range(16):
            if front.p[y][x] is None and bayer(x, y) < (5 if y == 10 else 10):
                front.p[y][x] = img.p[y][x]
    return img, front


def wave_of(st, pose):
    return [0, 1, 0, -1][pose % 4] * st['sway']


def particle_frames(st):
    """Two 8x8 frames of one particle (leaf, petal, snow, spark...)."""
    a, b = st['particles']
    k = st['part_kind']
    frames = []
    shapes = {
        'leaf': [[(3, 3), (4, 3), (4, 4), (2, 3)], [(3, 3), (3, 4), (4, 2)]],
        'petal': [[(3, 3), (4, 3), (3, 4)], [(3, 3), (4, 4)]],
        'seed': [[(3, 3), (3, 4)], [(3, 3), (4, 3)]],
        'fluff': [[(3, 3), (2, 3), (4, 3), (3, 2), (3, 4)], [(3, 3), (4, 4), (2, 2)]],
        'sand': [[(3, 3)], [(3, 3), (4, 4)]],
        'snow': [[(3, 3), (4, 3), (3, 4), (4, 4)], [(3, 3), (2, 3), (4, 3), (3, 2), (3, 4)]],
        'ash': [[(3, 3), (4, 3)], [(3, 3), (3, 4)]],
        'spark': [[(3, 3), (2, 3), (4, 3), (3, 2), (3, 4)], [(3, 3)]],
    }[k]
    for f in range(2):
        img = Img(8, 8)
        for i, (x, y) in enumerate(shapes[f]):
            img.p[y][x] = a if i == 0 else b
        frames.append(img)
    return frames


# ---------------------------------------------------------------------------
# Installation into a tileset build (called from gen_field_gfx.finish_tileset)
# ---------------------------------------------------------------------------

def rgb_dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def to_bank(img, bank, C):
    """Replace colours that are not in the bank by the nearest bank colour."""
    o = img.copy()
    for row in o.p:
        for i, c in enumerate(row):
            if c is not None and c not in bank:
                row[i] = min(bank, key=lambda n: rgb_dist(C[n], C[c]))
    return o


def decode_meta(ts, ents):
    img = Img(16, 16)
    for q, e in enumerate(ents):
        if not e:
            continue
        t, hf, vf, b = e & 1023, (e >> 10) & 1, (e >> 11) & 1, e >> 12
        idx = ts.tiles[t]
        for y in range(8):
            for x in range(8):
                k = idx[(7 - y if vf else y) * 8 + (7 - x if hf else x)]
                if k:
                    img.p[(q >> 1) * 8 + y][(q & 1) * 8 + x] = ts.banks[b][k - 1]
    return img


def pix(img, x0=0, y0=0):
    return [img.get(x0 + x, y0 + y) for y in range(8) for x in range(8)]


def quads(img):
    return [pix(img, dx, dy) for (dx, dy) in ((0, 0), (8, 0), (0, 8), (8, 8))]


def choose_bank(ts, st, C, ground_img):
    """The bank holding most of the style's colours (ties: the lowest)."""
    want = set(st['ramp'] + st['gap'] + [st['shade']])
    best, score = 0, -1
    for b, bank in enumerate(ts.banks):
        s = len(want & set(bank)) * 4
        if ground_img is not None:
            s += sum(1 for row in ground_img.p for c in row if c in bank) // 64
        if s > score:
            best, score = b, s
    return best


def variety(gf, ts, out, name, st, ground_img):
    """Build every image of one variety; returns the data for the header."""
    C = gf.C
    bank = choose_bank(ts, st, C, ground_img)
    pal = ts.banks[bank]
    if ground_img is not None:
        ground_img = to_bank(ground_img, pal, C)
    vs = []
    for v in range(VARIANTS):
        blades = make_blades(st, v)
        phase = [0, 1, 3][v % 3]
        poses, fronts = [], []
        for p in range(WIND):
            pose = (p + phase) % WIND
            b_img, f_img = render_cell(st, blades, ground_img, wave_of(st, pose), 0, pose)
            poses.append(to_bank(b_img, pal, C))
            fronts.append(to_bank(f_img, pal, C))
        rb, rf = [], []
        for r, part in enumerate(PARTS):
            b_img, f_img = render_cell(st, blades, ground_img, 0, part, r)
            rb.append(to_bank(b_img, pal, C))
            rf.append(to_bank(f_img, pal, C))
        vs.append(dict(phase=phase, poses=poses, fronts=fronts, rback=rb, rfront=rf))
    parts = [to_bank(i, pal, C) for i in particle_frames(st)]
    return dict(name=name, bank=bank, period=st['period'], variants=vs, particles=parts)


def install(gf, out, tsname, attrs, legend):
    """Regenerate / add this tileset's tall grass (see the module doc).
    Mutates out (metatiles, anims, stamps' ids), attrs and legend."""
    specs = REGISTRY.get(tsname)
    if not specs:
        return
    ts = out['ts']
    names = list(out['terrain'])   # (may be a shared module-level list)
    out['terrain'] = names
    grass = []
    old_tiles = set()
    new_meta = []   # (name, bottom ents) to insert before the stamps
    for (tname, st, ch, doc) in specs:
        ground_img = None
        if st['ground'] in names:
            gi = names.index(st['ground'])
            ground_img = decode_meta(ts, out['meta_b'][gi])
        vdata = variety(gf, ts, out, tname, st, ground_img)
        bank = vdata['bank']
        # BG tiles: one contiguous, unshared block of 4 tiles per variant;
        # frames[f] = every variant's tiles at wind frame f
        first = len(ts.tiles)
        frames = [[] for _ in range(WIND)]
        ents_of = []
        for v, vd in enumerate(vdata['variants']):
            ents = []
            for q in range(4):
                t = ts.add_raw(ts.indices(quads(vd['poses'][0])[q], bank))
                ents.append(t | (bank << 12))
            for f in range(WIND):
                for q in range(4):
                    frames[f].append(ts.indices(quads(vd['poses'][f])[q], bank))
            ents_of.append(ents)
        out.setdefault('anims', []).append((first, frames, vdata['period']))
        vdata['anim_first'] = first
        vnames = [tname] + ['%s_%s' % (tname, 'BCDEFG'[v - 1]) for v in range(1, VARIANTS)]
        if tname in names:
            i = names.index(tname)
            old_tiles.update(e & 1023 for e in list(out['meta_b'][i]) + list(out['meta_t'][i]))
            out['meta_b'][i] = ents_of[0]
            out['meta_t'][i] = [0, 0, 0, 0]
            new_meta.append((vnames[1:], ents_of[1:]))
        else:
            if ch is None:
                raise ValueError('%s: new grass %s needs a legend char' % (tsname, tname))
            if ch in legend:
                raise ValueError('%s: grass %s: legend char %r is taken' % (tsname, tname, ch))
            new_meta.append((vnames, ents_of))
            legend[ch] = tname
            if doc and isinstance(out.get('docs'), dict):
                out['docs'][tname] = doc
            vdata['doc'] = doc
        vdata['names'] = vnames
        grass.append(vdata)
        for vn in vnames:
            attrs[vn] = attrs.get(tname, 0) | gf.A_GRASS
    # insert the new metatiles after the terrain (before the stamps)
    at = len(names)
    add = [(n, e) for (ns, es) in new_meta for (n, e) in zip(ns, es)]
    for k, (n, e) in enumerate(add):
        names.append(n)
        out['meta_b'].insert(at + k, e)
        out['meta_t'].insert(at + k, [0, 0, 0, 0])
    out['stamps'] = [(sn, sid + len(add), cw, chh, d) for (sn, sid, cw, chh, d) in out.get('stamps', [])]
    # legend: every char that meant a grass variety now picks its variants
    for chx, spec in list(legend.items()):
        for vd in grass:
            if spec == vd['names'][0]:
                legend[chx] = [(vd['names'][0], 6), (vd['names'][1], 5), (vd['names'][2], 5)]
    ids = {n: i for i, n in enumerate(names)}
    for vd in grass:
        vd['ids'] = [ids[n] for n in vd['names']]
    out['grass'] = grass
    compact(out, old_tiles)


def compact(out, candidates):
    """Drop tiles of the replaced grass art that nothing refers to any more
    (the old hand-drawn tall grass), renumbering every tile reference."""
    ts = out['ts']
    used = set([0])

    def ents():
        for arr in (out['meta_b'], out['meta_t']):
            for e4 in arr:
                for e in e4:
                    yield e
        for key in ('path_q', 'water_q'):
            for row in out.get(key) or []:
                for e in row:
                    yield e
    for e in ents():
        used.add(e & 1023)
    for (first, frames, period) in out.get('anims', []):
        used.update(range(first, first + len(frames[0])))
    for key in ('water_first', 'flower_first'):
        if key in out:
            used.add(out[key])
    drop = sorted(t for t in candidates if t not in used and t != 0)
    if not drop:
        return
    remap, k = {}, 0
    dropset = set(drop)
    tiles = []
    for t, idx in enumerate(ts.tiles):
        if t in dropset:
            continue
        remap[t] = len(tiles)
        tiles.append(idx)
    ts.tiles = tiles
    ts.lookup = {idx: (remap[t], h, v) for idx, (t, h, v) in ts.lookup.items() if t in remap}

    def fix(e):
        return (e & ~1023) | remap[e & 1023] if e else e
    for arr in (out['meta_b'], out['meta_t']):
        for j, e4 in enumerate(arr):
            arr[j] = [fix(e) for e in e4]
    for key in ('path_q', 'water_q'):
        if out.get(key):
            out[key] = [[fix(e) for e in row] for row in out[key]]
    out['anims'] = [(remap[f], fr, p) for (f, fr, p) in out.get('anims', [])]
    for key in ('water_first', 'flower_first'):
        if key in out:
            out[key] = remap[out[key]]
    for vd in out.get('grass', []):
        vd['anim_first'] = remap[vd['anim_first']]


# ---------------------------------------------------------------------------
# Header (gfx_field.h): one GrassSet per tileset
# ---------------------------------------------------------------------------

def emit(o, sets, ts_names, pack4, fmt_u32):
    A = o.append
    A('/* ================================================================ */')
    A('/* Tall grass (tools/grass.py; engine: src/game/grass.c)             */')
    A('/* ================================================================ */')
    A('#define GRASS_VARIANTS %d' % VARIANTS)
    A('#define GRASS_WIND %d      /* wind poses (the variety\'s BG tile animation) */' % WIND)
    A('#define GRASS_RUSTLE %d    /* rustle frames */' % RUSTLE)
    A('/* A variety: its variants\' metatiles, the BG bank its tiles use and the')
    A(' * frames per wind pose. Sprite data is 4bpp in that bank\'s colours, 16x16')
    A(' * = 4 tiles (TL TR BL BR): front[variant][wind frame] (the front blades')
    A(' * drawn over whoever stands in the cell), rback / rfront[variant][rustle')
    A(' * frame] (the whole cell and its front blades while it rustles), part[2]')
    A(' * two 8x8 particle frames. */')
    A('typedef struct {')
    A('    u16 meta[GRASS_VARIANTS];')
    A('    u8 bank, period;')
    A('    const u32 *front, *rback, *rfront, *part;')
    A('} GrassDef;')
    A('typedef struct { const GrassDef *defs; u8 count; } GrassSet;')
    A('')

    def words(tiles):
        w = []
        for t in tiles:
            w.extend(pack4(t))
        return w
    rows = []
    for sn in ts_names:
        out = sets[sn]
        g = out.get('grass')
        if not g:
            rows.append('    [TS_%s] = { 0, 0 },' % sn.upper())
            continue
        ts = out['ts']
        entries = []
        for k, vd in enumerate(g):
            b = vd['bank']
            nm = '%s_grass%d' % (sn, k)
            for (field, key, n) in (('front', 'fronts', WIND), ('rback', 'rback', RUSTLE),
                                    ('rfront', 'rfront', RUSTLE)):
                tiles = []
                for v in vd['variants']:
                    for img in v[key]:
                        tiles += [ts.indices(q, b) for q in quads(img)]
                A('static const u32 %s_%s[%d * %d * 4 * 8] = {' % (nm, field, VARIANTS, n))
                A(fmt_u32(words(tiles)))
                A('};')
            tiles = [ts.indices(pix(img), b) for img in vd['particles']]
            A('static const u32 %s_part[2 * 8] = {' % nm)
            A(fmt_u32(words(tiles)))
            A('};')
            entries.append('    { { %s }, %d, %d, %s_front, %s_rback, %s_rfront, %s_part }, /* %s */' % (
                ', '.join(str(i) for i in vd['ids']), b, vd['period'], nm, nm, nm, nm, vd['name']))
        A('static const GrassDef %s_grass[%d] = {' % (sn, len(entries)))
        o.extend(entries)
        A('};')
        rows.append('    [TS_%s] = { %s_grass, %d },' % (sn.upper(), sn, len(entries)))
    A('static const GrassSet GRASS_SETS[TS_COUNT] = {')
    o.extend(rows)
    A('};')
    A('')


# ---------------------------------------------------------------------------
# Preview: python3 tools/grass.py OUT.png [scale] -- every variety: a 6x3
# field of its variants (wind pose 0), then per variant the wind poses, the
# rustle frames and the front overlay, and a person standing in it.
# ---------------------------------------------------------------------------

def preview(path, scale=3):
    import gen_field_gfx as gf
    from pixelart import write_png, c15_to_rgb, c15
    sets = gf.build_tilesets()
    chars = gf.char_gfx(gf.CHARACTERS[0])
    pl_frames, pl_pal = chars
    rows_out = []
    W = 16 * 30

    def rgb(n):
        return c15_to_rgb(c15(gf.C[n]))
    for sname, out in sets.items():
        for vd in out.get('grass', []):
            band = [[(20, 20, 30)] * W for _ in range(16 * 4 + 4)]

            def put(img, x0, y0, under=None):
                for y in range(img.h):
                    for x in range(img.w):
                        c = img.p[y][x]
                        if c is not None and 0 <= y0 + y < len(band) and 0 <= x0 + x < W:
                            band[y0 + y][x0 + x] = rgb(c)
            # field: 8x3 cells, variants by hash
            for cy in range(4):
                for cx in range(8):
                    v = [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2][hash2(cx, cy, 5) % 16]
                    put(vd['variants'][v]['poses'][0], cx * 16, cy * 16)
            # a person standing in cell (3, 2): sprite then the front overlay
            spr = pl_frames[3]
            for ty in range(4):
                for tx in range(2):
                    words = spr[ty * 2 + tx]
                    for y in range(8):
                        for x in range(8):
                            i = (words[y] >> (4 * x)) & 15
                            if i:
                                band[16 + ty * 8 + y][48 + tx * 8 + x] = c15_to_rgb(pl_pal[i])
            put(vd['variants'][0]['fronts'][0], 48, 32)
            x = 8 * 16 + 8
            for v, d in enumerate(vd['variants']):
                for p in range(WIND):
                    put(d['poses'][p], x + p * 17, v * 17)
                for r in range(RUSTLE):
                    put(d['rback'][r], x + (WIND + r) * 17 + 4, v * 17)
                for p in range(WIND):
                    put(d['fronts'][p], x + (WIND + RUSTLE + p) * 17 + 8, v * 17)
                for r in range(RUSTLE):
                    put(d['rfront'][r], x + (2 * WIND + RUSTLE + r) * 17 + 12, v * 17)
            for i, pimg in enumerate(vd['particles']):
                put(pimg, x + i * 10, 3 * 17 + 2)
            rows_out += band
    big = [[c for c in row for _ in range(scale)] for row in rows_out for _ in range(scale)]
    write_png(path, W * scale, len(rows_out) * scale, big)


if __name__ == '__main__':
    import sys
    preview(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 3)
