#!/usr/bin/env python3
"""Decor of the NORTH region (owner: W-NORTH): transparent objects for the
'snow' and 'cave' tilesets. Registered in gen_field_gfx.all_decor().

Palette plan (tools/north_palette.py):

  snow bank 4  NORTH_DECOR_BANK  granite, hot-spring water, ice, aurora
  snow bank 5  roof bank         snow ramp + reds + stone (snowman, sled)
  snow bank 3  village props     wood, red, amber (ski rack, sled)
  cave bank 4  CAVE_DECOR_BANK   crystals (cyan and amethyst), cave rock, moss
  cave bank 6  the sky bank      starlight, moonbeams (Starfall Grotto)

Light comes from the top-left; objects have a 1px dark outline and never a
baked-in ground (the art lint checks).
"""

import math
from pixelart import Img, G, hash2, shade_clumps, Decor
from decor_outdoor import SG, outline, blob

# ---------------------------------------------------------------------------
# legends
# ---------------------------------------------------------------------------

# snow bank 4
NL = {'.': None, 'O': 'b_out', 'w': 'white', 'H': 'rk_hi', 'L': 'rk_lt', 'B': 'rk_base',
      'D': 'rk_dk', 'h': 'hs_hi', 'l': 'hs_lt', 'b': 'hs_base', 'd': 'hs_dk',
      'i': 'ic_lt', 'c': 'ic_base', 'e': 'ic_dk', 'g': 'au_gr', 'v': 'au_vi'}
# snow bank 5 (roof bank): snow ramp, reds, stone
RL = {'.': None, 'O': 'b_out', '1': 'sn_hi', '2': 'sn_lt', '3': 'sn_base', '4': 'sn_mid',
      '5': 'sn_dk', 'r': 'rf_hi', 'R': 'rf_lt', 'x': 'rf_base', 'X': 'rf_dk', 'Z': 'rf_dkr',
      'H': 'st_hi', 'L': 'st_lt', 'M': 'st_mid', 'i': 'ic_lt'}
# village props bank (bank 3 in both tilesets)
OL = {'.': None, 'O': 'b_out', 'w': 'white', 'l': 'st_lt', 'm': 'st_mid', 'd': 'st_dk',
      'A': 'wd_lt', 'B': 'wd_base', 'K': 'wd_dk', 'y': 'p_yel', 'o': 'fx_org', 'r': 'p_red',
      'u': 'w_lt', 'U': 'w_base', 'g': 't_lt', 'G': 't_mid'}
# cave bank 4
CL = {'.': None, 'O': 'b_out', 'w': 'white', 'a': 'cr_hi', 'b': 'cr_lt', 'c': 'cr_base',
      'd': 'cr_dk', 'p': 'am_lt', 'P': 'am_base', 'Q': 'am_dk', 'H': 'cw_hi', 'L': 'cw_lt',
      'B': 'cw_base', 'D': 'cw_dk', 'm': 'mo_hi', 'M': 'mo_base'}
# cave bank 6 (sky)
SL = {'.': None, 'k': 'nv_dk', 'n': 'nv_base', 'N': 'nv_lt', 'w': 'white', 'y': 'sy_hi',
      'Y': 'sy_base', 'p': 'am_lt', 'P': 'am_base', 'Q': 'am_dk', 'a': 'cr_hi', 'b': 'cr_lt',
      'c': 'cv_base', 'm': 'cv_mid', 'd': 'cv_dk', 'D': 'cv_dkr'}

SNOW = ['snow']
CAVE = ['cave']


def _glint(frames_base, spots, bright='white', halo=None):
    """Animated glints: one frame per spot (a 1px star with a halo)."""
    frames = []
    for (sx, sy) in spots:
        fr = frames_base.copy()
        for (dx, dy) in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            if fr.get(sx + dx, sy + dy) not in (None, 'b_out'):
                if (dx, dy) == (0, 0):
                    fr.set(sx, sy, bright)
                elif halo:
                    fr.set(sx + dx, sy + dy, halo)
        frames.append(fr)
    return frames


# ===========================================================================
#  SNOW decor
# ===========================================================================

SNOWMAN = SG('''
................
................
................
................
.....OOOOOO.....
....OxxxxxxO....
....OXXXXXXO....
...OOOOOOOOOO...
....O111122O....
...O12O22O34O...
...O1222rr234O..
...O12222R234O..
....O2222334O...
..OOxxxxxxxxXO..
.O.OXXXXxXXXO.O.
O...O22OXO34O..O
...O1222xX2334O.
..O1222222223344
..O122222223334O
..O222222223334O
..O222222233344O
..O2222222333445
...O223333334440
...OO4444444450.
....OOOOOOOOOO..
................
................
................
................
................
................
................
''', dict(RL, **{'0': 'b_out'}))


def snowman():
    img = SNOWMAN.copy()
    # stick arms
    for (x, y) in ((1, 14), (0, 15), (14, 14), (15, 15)):
        img.set(x, y, 'rf_dkr')
    return img


def ice_crystal_frames():
    base = SG('''
    ................
    .......O........
    ......Oi........
    ......OiO....O..
    ..O...OicO..OiO.
    .OiO..OicO..OicO
    .OicO.OicO.OiceO
    .OiceOOiceOOiceO
    ..OiceOicecOiceO
    ..OiceOiccOiceO.
    ...OicOiccOiceO.
    ...OiccOiceiceO.
    ....OicciceeeO..
    .....OccceeeO...
    ......OOOOOO....
    ................
    ''', NL)
    return _glint(base, [(7, 3), (13, 6), (2, 7)], bright='white', halo='ic_lt')


def ice_blocks():
    return SG('''
    ................
    ................
    ................
    ...OOOOOOOOO....
    ..OiiiiiiiicO...
    ..OiwiiiiiiceO..
    ..OiiiiiiicceO..
    ..OccccccceeeOO.
    .OOOOOOOOOOOOiO.
    OiiiiiiOiiiiicO.
    OiwiiicOiwiiceO.
    OiiiiccOiiiiceO.
    OiiicccOiiicceO.
    OcccceeOcccceeO.
    OOOOOOOOOOOOOOO.
    ................
    ''', NL)


def hot_spring_frames():
    """A 4x3 stone-rimmed pool of steaming blue-green water (solid)."""
    W_, H_ = 64, 48
    frames = []
    for f in range(3):
        img = Img(W_, H_)
        cx, cy, rx, ry = 32.0, 25.0, 30.0, 20.5
        for y in range(H_):
            for x in range(W_):
                d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
                if d > 1.0:
                    continue
                if d > 0.66:
                    # stones of the rim
                    ang = math.atan2(y + 0.5 - cy, x + 0.5 - cx)
                    k = int((ang + math.pi) / (2 * math.pi) * 22)
                    edge = abs(((ang + math.pi) / (2 * math.pi) * 22) - k - 0.5) > 0.40
                    if edge or d > 0.97 or abs(d - 0.66) < 0.035:
                        c = 'b_out'
                    elif y + 0.5 < cy - ry * 0.35 or x + 0.5 < cx - rx * 0.6:
                        c = 'rk_hi' if d < 0.8 else 'rk_lt'
                    else:
                        c = 'rk_lt' if d < 0.8 else 'rk_base'
                    if (hash2(x, y, 5) & 15) == 0 and c != 'b_out':
                        c = 'rk_dk'
                else:
                    c = 'hs_base'
                    if d > 0.56 and y + 0.5 < cy:
                        c = 'hs_dk'           # shade under the north rim
                    elif d > 0.5 and y + 0.5 > cy:
                        c = 'hs_lt'
                    else:
                        # slow ripples
                        rr = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)
                        if abs(((rr * 9.0 - f * 0.33) % 1.0) - 0.5) < 0.07:
                            c = 'hs_lt'
                        if (hash2(x + f * 3, y, 11) & 63) == 0:
                            c = 'hs_hi'
                img.p[y][x] = c
        frames.append(img)
    return frames


def steam_frames():
    """Wisps of steam drifting up (top layer, over people)."""
    frames = []
    for f in range(4):
        img = Img(16, 16)
        for (x0, phase) in ((3, 0.0), (8, 2.1), (12, 4.0)):
            for y in range(16):
                t = (y + f * 4) % 16
                x = x0 + int(round(1.6 * math.sin(t * 0.55 + phase)))
                if 1 <= t <= 13 and (t + x0) % 4 != 0:
                    c = 'white' if t > 8 else 'hs_hi'
                    if 0 <= x < 16:
                        img.p[y][x] = c
                    if t > 10 and 0 <= x + 1 < 16 and (t % 2):
                        img.p[y][x + 1] = 'hs_hi'
        frames.append(img)
    return frames


WOLF_STATUE = SG('''
................
................
................
........OO......
.......OLO......
......OLHLO.....
......OLHLLO....
.....OLHLLLLO...
....OLHHLLBBO...
...OOLHLLBBDO...
..OLLHLLBBBDO...
..OOOLLLBBDO....
.....OLLBBDO....
.....OLLBBDO....
....OLHLLBBDO...
....OLHLLBBBDO..
...OLHLLLBBBDO..
...OLHLLLBBBBDO.
..OLHLLLBBBBBDO.
..OLHLLOBBOBBDO.
..OLHLLOBBOBBDO.
..OLLLDOBDOBDDO.
.OHHHHHHHHHHHHLO
.OLLLLLLLLLLLLBO
.OLLLLLLLLLLLLBO
.OBBBBBBBBBBBBDO
.OOOOOOOOOOOOOOO
................
................
................
................
................
''', NL)


def wolf_statue():
    img = WOLF_STATUE.copy()
    # frost on the stone and an old aurora rune on the plinth
    for (x, y) in ((6, 5), (7, 4), (5, 8), (4, 16), (4, 17)):
        img.set(x, y, 'white')
    for (x, y) in ((6, 23), (7, 23), (8, 24), (9, 23), (10, 23)):
        img.set(x, y, 'ic_base')
    return img


def aurora_stone_frames():
    base = SG('''
    ................
    ................
    ......OOOO......
    ....OOHHLLOO....
    ...OHHLLLLBDO...
    ...OHLLLLLBDO...
    ...OHLLLLBBDO...
    ...OHLLLLLBDDO..
    ..OHLLLLLLBBDO..
    ..OHLLLLLLLBDO..
    ..OHLLLLLLLBDO..
    ..OHLLLLLLBBDO..
    ..OHLLLLLLLBDO..
    ..OHLLLLLLLBDDO.
    ..OHLLLLLLLBDDO.
    ..OHLLLLLLLLBDO.
    ..OHLLLLLLLLBDO.
    ..OHLLLLLLLLBDO.
    ..OHLLLLLLLLBDO.
    ..OHLLLLLLLLBDO.
    ..OHLLLLLLLLBDO.
    ..OHLLLLLLLBBDO.
    .OHLLLLLLLLLBDO.
    .OHLLLLLLLLLBDDO
    .OHHLLLLLLLLBBDO
    .OOOOOOOOOOOOOOO
    ................
    ................
    ................
    ................
    ................
    ................
    ''', NL)
    rune = [(7, 7), (7, 8), (6, 9), (8, 9), (7, 10), (7, 11), (5, 13), (6, 14), (7, 15), (8, 14),
            (9, 13), (7, 16), (7, 17), (6, 19), (7, 19), (8, 19)]
    frames = []
    for f in range(4):
        fr = base.copy()
        for i, (x, y) in enumerate(rune):
            k = (i + f * 2) % 6
            fr.set(x, y, 'au_gr' if k < 2 else 'au_vi' if k < 4 else 'ic_lt')
        frames.append(fr)
    return frames


def frost_banner():
    return SG('''
    ................
    .OOOOOOOOOOOOOO.
    .OHLLLLLLLLLLBO.
    .OOOOOOOOOOOOOO.
    ..OeeeeeeeeeeO..
    ..OeccccccccdO..
    ..Oecc.w..ccdO..
    ..Oecw.w.wccdO..
    ..Oec.www.ccdO..
    ..Oewwwwwwwcd...
    ..Oec.www.ccdO..
    ..Oecw.w.wccdO..
    ..Oecc.w..ccdO..
    ..OeccccccccdO..
    ..OeeeeeeeeeeO..
    ..OeccccccccdO..
    ..OecccccccddO..
    ..OeeeeeeeeeeO..
    ...OeO....OeO...
    ....O......O....
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ''', dict(NL, d='ic_dk', **{'.': None})).replace({None: None})


def _fix_banner(img):
    # '.' inside the cloth is the cloth colour, not a hole
    for y in range(5, 14):
        for x in range(4, 12):
            if img.p[y][x] is None:
                img.p[y][x] = 'ic_base'
    img.p[9][13] = 'b_out'
    return img


def ice_statue_frames():
    """An ice sculpture of a FROSTOAT on a granite plinth (1x2)."""
    base = SG('''
    ................
    ................
    ................
    ................
    ................
    ......OO........
    .....OiiO.OO....
    ....OiwiiOiiO...
    ...OiiiiiiicO...
    ...OiOiiiiicO...
    ..OiiiiiiiccO...
    ...OOiiiicccO...
    .....OiiiccO....
    ....OiiiiiccO...
    ...OiiiiicccO...
    ..OiiiwiiicccO..
    ..OiiiiiiicccO..
    ..OiiiiiicccceO.
    ..OiiiiiccccceO.
    ...OiiicccceeiiO
    ...OOiicceeOOicO
    .....OOOOOO..OO.
    .OOOOOOOOOOOOOO.
    .OHHHHHHHHHHHHLO
    .OLLLLLLLLLLLLBO
    .OLLLLLLLLLLLLBO
    .OBBBBBBBBBBBBDO
    .OOOOOOOOOOOOOOO
    ................
    ................
    ................
    ................
    ''', NL)
    return _glint(base, [(6, 7), (10, 16), (4, 14)], bright='white', halo='ic_lt')


def sky_arch_frames():
    """A wind-worn stone arch on the Sky Isle hung with aurora ribbons (3x2)."""
    base = SG('''
    ................................................
    ................................................
    ..........OOOOOOOOOOOOOOOOOOOOOOOOOOOO..........
    ........OOHHHHHHHHHHHHHHHHHHHHHHHHHHHLOO........
    .......OHHLLLLLLLLLLLLLLLLLLLLLLLLLLLLBBO.......
    .......OHLLLLLLLLLLLLLLLLLLLLLLLLLLLLLBDO.......
    .......OHLLBBOOOOOOOOOOOOOOOOOOOOOOLLBBDO.......
    .......OHLBO......................OLLBDO........
    .......OHLBO......................OHLBDO........
    .......OHLBO......................OHLBDO........
    .......OHLBO......................OHLBDO........
    .......OHLBO......................OHLBDO........
    .......OHLBO......................OHLBDO........
    .......OHLBO......................OHLBDO........
    .......OHLBO......................OHLBDO........
    .......OHLBO......................OHLBDO........
    .......OHLBO......................OHLBDO........
    .......OHLBO......................OHLBDO........
    .......OHLBO......................OHLBDO........
    .......OHLBO......................OHLBDO........
    .......OHLBO......................OHLBDO........
    .......OHLBO......................OHLBDO........
    .......OHLBO......................OHLBDO........
    .......OHLBO......................OHLBDO........
    ......OHHLBBO....................OHHLBDDO.......
    ......OHLLBBO....................OHLLBBDO.......
    .....OHHLLBBDO..................OHHLLBBDO.......
    .....OOOOOOOOO..................OOOOOOOOO.......
    ................................................
    ................................................
    ................................................
    ................................................
    ''', NL, w=48)
    frames = []
    for f in range(4):
        fr = base.copy()
        for (x0, col) in ((16, 'au_gr'), (22, 'au_vi'), (27, 'au_gr'), (32, 'au_vi')):
            for y in range(7, 7 + 9 + (x0 % 3)):
                x = x0 + int(round(1.2 * math.sin(y * 0.6 + f * 1.4 + x0)))
                fr.set(x, y, col)
                if y % 3 == 0:
                    fr.set(x + 1, y, 'white' if col == 'au_gr' else 'ic_lt')
        frames.append(fr)
    return frames


def sled():
    return SG('''
    ................
    ................
    ................
    ................
    ................
    ................
    ..OOOOOOOOOOOO..
    .OrrrrrrrrrrroO.
    .OrrrrrrrrrrroO.
    ..OOOOOOOOOOOOO.
    ...OKO....OKO...
    OO.OKO....OKO...
    OAOOOOOOOOOOOOO.
    .OAAAAAAAAAAAAAO
    ..OOOOOOOOOOOOO.
    ................
    ''', OL)


def ski_rack():
    return SG('''
    ................
    ....OO...OO.....
    ...OrO..OuO.....
    ...OrO..OuO..OO.
    ...OrO..OuO.OyO.
    ...OrO..OuO.OyO.
    ...OrO..OuO.OyO.
    .OOOOOOOOOOOOOOO
    .OAAAAAAAAAAAAAO
    .OBBBBBBBBBBBBKO
    .OOOOOOOOOOOOOOO
    ...OrO..OuO.OyO.
    ...OrO..OuO.OyO.
    ..OOOOOOOOOOOOO.
    ..OBKO....OBKO..
    ..OOOO....OOOO..
    ''', OL)


def frozen_tree():
    """A bare birch rimed with frost (1x2, crown over people)."""
    img = Img(16, 32)
    def put(x, y, c):
        if 0 <= x < 16 and 0 <= y < 32:
            img.p[y][x] = c
    # trunk
    for y in range(12, 30):
        put(7, y, 'white')
        put(8, y, 'rk_hi' if y % 5 else 'b_out')
        put(9, y, 'rk_lt')
    # branches (lightning-like, frosted tips)
    branches = [(8, 14, -1, 6), (8, 12, 1, 5), (8, 18, -1, 4), (8, 20, 1, 5), (8, 9, -1, 4),
                (8, 8, 1, 4), (8, 5, 0, 5)]
    for (x0, y0, dx, n) in branches:
        x, y = x0, y0
        for i in range(n):
            x += dx if i % 2 == 0 or dx == 0 else 0
            y -= 1
            put(x, y, 'rk_lt' if i < n - 2 else 'white')
            if i == n - 1:
                put(x - 1, y, 'ic_lt')
                put(x + 1, y, 'ic_lt')
                put(x, y - 1, 'white')
    img = outline(img, 'b_out')
    return img


def rime_pillar():
    """An ice pillar of the Rime Hall (1x2; capital over people)."""
    return SG('''
    ................
    ..OOOOOOOOOOOO..
    .OHHHHHHHHHHHLO.
    .OBBBBBBBBBBBDO.
    ..OOOOOOOOOOOO..
    ...OiiicccceO...
    ...OiwicccceO...
    ...OiiicccceO...
    ...OiiicccceO...
    ...OiwicccceO...
    ...OiiicccceO...
    ...OiiicccceO...
    ...OiiicccceO...
    ...OiiicccceO...
    ...OiiicccceO...
    ...OiiicccceO...
    ...OiiicccceO...
    ...OiwicccceO...
    ...OiiicccceO...
    ...OiiicccceO...
    ...OiiicccceO...
    ...OiiicccceO...
    ...OiiicccceO...
    ...OiiicccceO...
    ..OOOOOOOOOOOO..
    .OHHHHHHHHHHHLO.
    .OLLLLLLLLLLLBO.
    .OBBBBBBBBBBBDO.
    .OOOOOOOOOOOOOO.
    ................
    ................
    ................
    ''', NL)


def wash_bucket():
    return SG('''
    ................
    ................
    ................
    ................
    ................
    .....OOOOOO.....
    ....OAAAAAAO....
    ...OhhhhhhhhO...
    ...OAlllllbKO...
    ...OAAAAAAAKO...
    ...OKKKKKKKKO...
    ...OABBBBBBKO...
    ...OAAAAAAAKO...
    ....OKKKKKKO....
    .....OOOOOO.....
    ................
    ''', dict(NL, A='rk_hi', B='rk_lt', K='rk_base'))


# ===========================================================================
#  CAVE decor
# ===========================================================================

def cave_crystal_frames():
    base = SG('''
    .......OO.......
    ......OabO......
    ......OabcO.....
    ..OO..ObbcO.OO..
    .OabO.ObbcdOacO.
    .ObbcOObbcdObcO.
    ..ObbcObbcdObcO.
    ..ObbcdObcdbcdO.
    ...ObcdObcdbcdO.
    ...ObbcObcdbcO..
    ....ObcdObcbdO..
    ..OOOccdObccdOO.
    .OLLBOOOOOOOOBDO
    .OLBBBBBBBBBBDDO
    ..OOOOOOOOOOOOO.
    ................
    ''', CL)
    return _glint(base, [(7, 2), (2, 5), (13, 5)], bright='white', halo='cr_hi')


def amethyst_frames():
    base = SG('''
    ................
    ........OO......
    .......OpPO.....
    ..OO...OpPQO....
    .OpPO..OpPQO.OO.
    .OpPQO.OpPQOOpO.
    ..OpPQOOpPQOpPO.
    ..OpPQOOpPQOpQO.
    ...OpQOOpPQpPQO.
    ...OpPQOpPQpQO..
    ....OpPOpPQpQO..
    ..OOOPPQOPPQOOO.
    .OLLBOOOOOOOOBDO
    .OLBBBBBBBBBBDDO
    ..OOOOOOOOOOOOO.
    ................
    ''', CL)
    return _glint(base, [(8, 3), (2, 5), (13, 6)], bright='white', halo='am_lt')


def crystal_pillar_frames():
    """A tall crystal spire (1x2) that lights the grotto."""
    base = SG('''
    ........O.......
    .......OaO......
    .......ObO......
    ......OabO......
    ......ObbcO.....
    ......ObbcO.....
    .....OabbcO.....
    .....ObbbcdO....
    .....ObbbcdO....
    ....OabbbcdO....
    ....ObbbbcdO....
    ....ObbbccdO..O.
    ....ObbbccdO.ObO
    ...OabbbccdO.ObO
    ...ObbbbccddOacO
    ...ObbbbcccdObcO
    ...ObbbbcccdObcO
    ..OabbbbcccdObcO
    ..ObbbbbcccddObO
    ..ObbbbbccccdObO
    ..ObbbbbccccdOcO
    .OO.ObbbccccdOcO
    OaO.ObbbccccddcO
    ObcOObbbcccccdO.
    ObcdObbbbccccdO.
    .ObcObbbbbccddO.
    OOOOOOOOOOOOOOOO
    OLLLLBBBBBBBBBDO
    OLBBBBBBBBBBBDDO
    .OOOOOOOOOOOOOO.
    ................
    ................
    ''', CL)
    return _glint(base, [(7, 3), (6, 12), (13, 14), (2, 23)], bright='white', halo='cr_hi')


def stalagmite():
    return SG('''
    ................
    .......OO.......
    .......OLO......
    ......OHLO......
    ......OHLBO.....
    ......OHLBO.....
    .....OHLLBO.....
    .....OHLLBDO....
    .....OHLLBDO....
    ....OHLLLBDO....
    ....OHLLLBBDO...
    ...OHLLLLBBDO...
    ..OOHLLLLBBDDO..
    .OHHLLLLLLBBDO..
    .OOOOOOOOOOOOOO.
    ................
    ''', CL)


def glowcap_frames():
    base = SG('''
    ................
    ................
    ................
    ................
    ....OOOO........
    ...OmmmMO.......
    ..OmmMMMMO..OO..
    ..OMMMMMMO.OmMO.
    ...OOLLOO.OmMMMO
    ....OLHO...OOOO.
    ....OLHO....OLO.
    ...OOLHO....OLO.
    ..OmMOHOO..OOLO.
    ..OMMOHO..OmMOO.
    ...OOOOO..OOO...
    ................
    ''', CL)
    frames = [base]
    alt = base.replace({'mo_hi': 'mo_base', 'mo_base': 'mo_hi'})
    frames.append(alt)
    return frames


def mine_cart():
    return SG('''
    ................
    ................
    ................
    ................
    ..OOOOOOOOOOOO..
    .OlllllllllllmO.
    .OldOOOOOOOOdmO.
    .OldBBAABBBBdmO.
    .OlmmmmmmmmmmmO.
    .OlKKKKKKKKKKdO.
    .OmmmmmmmmmmmdO.
    ..OOOOOOOOOOOO..
    ..OdO......OdO..
    .OdmdO....OdmdO.
    ..OdO......OdO..
    ................
    ''', OL)


def ore_rocks():
    return SG('''
    ................
    ................
    ................
    ................
    ................
    ......OOOO......
    ....OOHLLBOO....
    ...OHLLLbLBDO...
    ..OHLLbcLLBDDO..
    ..OHLLLLLpBBDO..
    .OHLLpPLLLLBDO..
    .OHLLLLLLLBBDDO.
    .OLLLLLLLBBBDDO.
    ..OOOOOOOOOOOO..
    ................
    ................
    ''', CL)


def moonbeam_frames():
    """A shaft of moonlight from the open roof of the grotto (1x2, top
    layer: drawn over people, dithered so the floor shows through)."""
    frames = []
    for f in range(4):
        img = Img(16, 32)
        for y in range(32):
            for x in range(16):
                edge = 3 + y * 0.12
                if not (edge <= x + 0.5 <= 16 - edge + 1.0):
                    continue
                k = (x + y + f) % 4
                if (x + y) % 2 == 0 and k != 0:
                    continue
                c = 'cr_hi' if abs(x + 0.5 - 8.5) < 2.2 else 'cr_lt'
                if y > 24 and (x + y) % 3:
                    continue
                img.p[y][x] = c
        for (x, y0) in ((6, 3), (10, 11), (7, 19), (9, 26)):
            y = (y0 + f * 2) % 32
            img.p[y][x] = 'white'
        frames.append(img)
    return frames


def moth_dais_frames():
    """SELENOTH's resting stone: a round moonstone dais (2x2)."""
    frames = []
    for f in range(3):
        img = Img(32, 32)
        cx, cy = 16.0, 18.0
        for y in range(32):
            for x in range(32):
                d = math.hypot((x + 0.5 - cx) / 14.5, (y + 0.5 - cy) / 11.0)
                if d > 1.0:
                    continue
                if d > 0.93:
                    c = 'b_out'
                elif y + 0.5 > cy + 6.5:
                    c = 'cw_dk' if d > 0.8 else 'cw_base'
                elif d > 0.8:
                    c = 'cw_hi' if x < cx else 'cw_lt'
                else:
                    r = (d * 5.0 + f * 0.33) % 1.0
                    c = 'am_lt' if r < 0.18 else 'cr_lt' if d < 0.3 else 'cw_hi'
                    if d < 0.14:
                        c = 'white'
                img.p[y][x] = c
        # the rim of the dais face
        for x in range(32):
            for y in range(int(cy + 5), 32):
                if img.p[y][x] not in (None, 'b_out') and img.p[y - 1][x] in ('cw_hi', 'cw_lt', 'am_lt',
                                                                               'cr_lt', 'white'):
                    img.p[y][x] = 'b_out'
        frames.append(img)
    return frames


# ===========================================================================
#  Catalogue
# ===========================================================================

_ALL_NORTH_DECOR = [
    # --- snow ---------------------------------------------------------------
    Decor('SNOWMAN', SNOW, snowman(), top='X/.', doc='snowman with a red scarf; head over people',
          examine='A snowman in a red scarf. Someone gave it a very serious expression.'),
    Decor('ICE_CRYSTAL', SNOW, frames=ice_crystal_frames(), period=16,
          doc='jagged ice crystals (glinting)',
          examine='Rime crystals, grown needle by needle out of the freezing air.'),
    Decor('ICE_BLOCKS', SNOW, ice_blocks(), doc='blocks of cut lake ice',
          examine='Blocks of clear lake ice, cut and stacked for the icehouse.'),
    Decor('HOT_SPRING', SNOW, frames=hot_spring_frames(), period=14,
          doc='4x3 steaming hot spring pool in a ring of stones (solid)',
          examine='The hot spring. The water is warm as a bath, and it smells faintly of stone.'),
    Decor('STEAM', SNOW, frames=steam_frames(), period=8, top='X', solid='.',
          doc='drifting steam (top layer, walkable)'),
    Decor('WOLF_STATUE', SNOW, wolf_statue(), top='X/.',
          doc='stone wolf howling on a plinth (Whitecrown); head over people',
          examine='A stone wolf, howling at the sky. Frost has never once melted off its muzzle.'),
    Decor('AURORA_STONE', SNOW, frames=aurora_stone_frames(), period=12, top='X/.',
          doc='standing stone with glowing aurora runes',
          examine='The runes shimmer green and violet, like the lights over the peak at midwinter.'),
    Decor('FROST_BANNER', SNOW, _fix_banner(frost_banner()), top='X/.', solid='./.',
          doc='Rime Hall banner with a snowflake (on a wall, over people)'),
    Decor('ICE_STATUE', SNOW, frames=ice_statue_frames(), period=18, top='X/.',
          doc='ice sculpture of a FROSTOAT on a granite plinth',
          examine='An ice FROSTOAT, carved by the Hall Master. It never melts, even in summer.'),
    Decor('RIME_PILLAR', SNOW, rime_pillar(), top='X/.', doc='ice pillar of the Rime Hall',
          examine='A pillar of clear blue ice. Your breath fogs on it.'),
    Decor('SKY_ARCH', SNOW, frames=sky_arch_frames(), period=10, top='XXX/...', solid='X.X/X.X',
          doc='3x2 wind-worn stone arch hung with aurora ribbons (Sky Isle)',
          examine='An arch older than the Vale. Ribbons of light hang in it with no wind to move them.'),
    Decor('SLED', SNOW, sled(), doc='red wooden sled',
          examine='A red sled. The runners are waxed to a shine.'),
    Decor('SKI_RACK', SNOW, ski_rack(), doc='rack of skis',
          examine='Skis and poles for the pass. One pair is child-sized.'),
    Decor('FROZEN_TREE', SNOW, frozen_tree(), top='X/.', doc='bare birch rimed with frost',
          examine='A birch so thick with rime it rings when the wind blows.'),
    Decor('WASH_BUCKET', SNOW, wash_bucket(), doc='stone wash basin at the hot spring',
          examine='A basin for rinsing off before the spring. House rules!'),
    # --- cave ---------------------------------------------------------------
    Decor('CAVE_CRYSTAL', CAVE, frames=cave_crystal_frames(), period=16,
          doc='cluster of glowing cyan crystals',
          examine='Glimmer crystal. It stores light by day and gives it back all night.'),
    Decor('AMETHYST', CAVE, frames=amethyst_frames(), period=18, doc='cluster of violet crystals',
          examine='Violet crystal, humming very faintly. A kin kernel sings like this.'),
    Decor('CRYSTAL_PILLAR', CAVE, frames=crystal_pillar_frames(), period=14, top='X/.',
          doc='tall crystal spire (1x2)', examine='A spire of crystal taller than a house, lit from within.'),
    Decor('STALAGMITE', CAVE, stalagmite(), doc='stalagmite',
          examine='A stalagmite. It grows about as fast as your fingernails... per century.'),
    Decor('GLOWCAP', CAVE, frames=glowcap_frames(), period=30, doc='glowing cave mushrooms',
          examine='Glowcaps. Their cold light is chemistry, just like a glow tonic.'),
    Decor('MINE_CART', CAVE, mine_cart(), doc='old mine cart', solid='X',
          examine='An old ore cart, left behind by the crystal miners.'),
    Decor('ORE_ROCKS', CAVE, ore_rocks(), doc='rock with crystal ore',
          examine='Rock threaded with crystal ore. Best left where it is.'),
    Decor('MOONBEAM', CAVE, frames=moonbeam_frames(), period=10, top='X/X', solid='./.',
          doc='shaft of moonlight (top layer, walkable)'),
    Decor('MOTH_DAIS', CAVE, frames=moth_dais_frames(), period=20,
          doc='2x2 moonstone dais (Starfall Grotto)',
          examine='A moonstone dais, dusted with pale wing-scales.'),
]

NORTH_DECOR = _ALL_NORTH_DECOR
