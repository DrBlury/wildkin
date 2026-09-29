"""HAMLET - villages of the temperate lowlands.

Replaces the old `town` tileset (Maple Village, Brookmill, Mistbell and the
elevation test map). Shares verdant's grass, dirt, water and cliff colours,
so a route can hand over to a village without a seam, and adds buildings,
paving and village furniture.
"""

from core import Img
from sheet import Sheet, Scene
import palettes as PL
import paint as P
import terrain as T
import flora as F
import props as PR
import townprops as TP
import buildings as B
import kit

PALETTE = PL.merge(PL.MEADOW, PL.DIRT, PL.FRESH_WATER, PL.CLIFF_BROWN, PL.STONE_GREY, PL.LEAF, PL.BARK,
                   PL.FLOWERS, PL.ROOF_RED, PL.ROOF_BLUE, PL.ROOF_GREEN, PL.WALL_CREAM, PL.GLASS,
                   PL.COBBLE, PL.BRICK)

AUTUMN = {'g1': '#5a5a30', 'g2': '#8a8a40', 'g3': '#b0a650', 'g4': '#d0c068', 'g5': '#e8dc90',
          't1': '#6a2c24', 't2': '#9a3c28', 't3': '#c85c30', 't4': '#e88a3c', 't5': '#f8b85c'}
# Evening: the whole village under a warm dusk (window glass lit).
DUSK = {'g0': '#10243a', 'g1': '#1c3c48', 'g2': '#2c5a54', 'g3': '#3e7460', 'g4': '#5a8c6c', 'g5': '#7ca47c',
        'd1': '#4a3440', 'd2': '#6a4c50', 'd3': '#8a6860', 'd4': '#a88470', 'd5': '#c0a080',
        'gl0': '#a86828', 'gl1': '#f0b040', 'gl2': '#fff0a0',
        'wl0': '#6c5c68', 'wl1': '#9c8c90', 'wl2': '#b8acac',
        'c1': '#4c4658', 'c2': '#5e5868', 'c3': '#746c7c', 'c4': '#8c8494'}

BANKS = [
    ['g0', 'g1', 'g2', 'g3', 'g4', 'g5', 'd0', 'd1', 'd2', 'd3', 'd4', 'd5', 'fr', 'fy', 'fw'],
    ['g0', 'g1', 'g2', 'g3', 'g4', 'g5', 'w0', 'w1', 'w2', 'w3', 'w4', 'w5', 'c1', 'c2', 'c3'],
    ['g1', 'g2', 'g3', 'g4', 'g5', 'c0', 'c1', 'c2', 'c3', 'c4', 'r0', 'r1', 'r2', 'r3', 'r4'],
    ['ra0', 'ra1', 'ra2', 'ra3', 'ra4', 'k0', 'wl0', 'wl1', 'wl2', 'k1', 'k2', 'k3', 'gl0', 'gl1', 'gl2'],
    ['rb0', 'rb1', 'rb2', 'rb3', 'rb4', 'k0', 'wl0', 'wl1', 'wl2', 'k1', 'k2', 'k3', 'gl0', 'gl1', 'gl2'],
    ['rg0', 'rg1', 'rg2', 'rg3', 'rg4', 'k0', 'bk0', 'bk1', 'bk2', 'k1', 'k2', 'k3', 'gl0', 'gl1', 'gl2'],
    ['t0', 't1', 't2', 't3', 't4', 't5', 'k0', 'k1', 'k2', 'k3', 'k4', 'fr', 'frd', 'fp', 'fw'],
    ['s0', 's1', 's2', 's3', 's4', 's5', 'k0', 'k1', 'k2', 'k3', 'k4', 'fr', 'fy', 'fo', 'fw'],
]

GRASS = {'dk': 'g1', 'mid': 'g2', 'base': 'g3', 'lt': 'g4', 'hi': 'g5', 'out': 'g0'}
DIRT = {'dk': 'd1', 'mid': 'd2', 'base': 'd3', 'lt': 'd4', 'hi': 'd5'}
WATER = {'deep': 'w1', 'base': 'w2', 'lt': 'w3', 'hi': 'w4', 'foam': 'w5', 'dark': 'w0'}
ROCK = ['r1', 'r2', 'r3', 'r4', 'c4']   # c4 doubles as rock highlight (bank space)
STONE = ['s1', 's2', 's3', 's4', 's5']
LEAF = ['t0', 't1', 't2', 't3', 't4', 't5']
BARK = ['k1', 'k2', 'k3']
WOOD = ['k1', 'k2', 'k3', 'k4']
TRIM = ['k1', 'k2', 'k3']
GLASS = ['gl0', 'gl1', 'gl2']
FOUND = ['c1', 'c2', 'c3']


def style(roof, wall=('wl0', 'wl1', 'wl2'), **kw):
    # foundation and chimney reuse the wall/trim colours: each building's
    # tiles then need only its roof bank (GBA: 15 colours per 8x8 tile)
    st = {'out': 'k0', 'roof': roof, 'wall': list(wall), 'trim': TRIM, 'glass': GLASS,
          'found': ['k1', wall[0], wall[1]], 'chimney': ['k1', wall[0], wall[1]]}
    st.update(kw)
    return st


RED = style(['ra0', 'ra1', 'ra2', 'ra3', 'ra4'])
BLUE = style(['rb0', 'rb1', 'rb2', 'rb3', 'rb4'])
GREEN = style(['rg0', 'rg1', 'rg2', 'rg3', 'rg4'], wall=('bk0', 'bk1', 'bk2'))   # green roofs pair with red-brown walls (bank plan)
GREEN_BRICK = style(['rg0', 'rg1', 'rg2', 'rg3', 'rg4'], wall=('bk0', 'bk1', 'bk2'))


def add_building(S, name, img, door=None, doc='', top_rows=0):
    w, h = img.w // 16, img.h // 16
    solid = '/'.join(['X' * w] * h)
    extra = {}
    if door is not None:
        extra['door'] = list(door)
    top = '/'.join((['X' * w] * top_rows) + (['.' * w] * (h - top_rows))) if top_rows else None
    if top:
        solid = '/'.join((['.' * w] * top_rows) + (['X' * w] * (h - top_rows)))
    S.object(name, img, solid=solid, top=top, doc=doc, extra=extra)


def build():
    S = Sheet('hamlet', 'Hamlet - villages', PALETTE, variants={'autumn': AUTUMN, 'dusk': DUSK},
              banks=BANKS, doc=__doc__)

    # -- ground ----------------------------------------------------------------
    S.section('ground')
    grass = kit.grass_family(S, 'grass', GRASS, flowers={'n': 2, 'petals': ['fw', 'fy'], 'center': 'fy'},
                             pebbles={'peb': 'd3', 'peb_hi': 'd5', 'peb_dk': 'd1'}, doc='village green')
    dirt = kit.speckle_family(S, 'dirt', DIRT, doc='packed earth')
    cob = T.cobbles(['c1', 'c2', 'c3', 'c4'], 'c0', seed=2)
    S.tile('cobble', cob, group='cobble', weight=3, doc='cobblestones')
    S.tile('cobble_b', T.cobbles(['c1', 'c2', 'c3', 'c4'], 'c0', seed=5), group='cobble', weight=2)
    S.tile('brick_road', T.bricks(['c0', 'c1', 'c2', 'c3']), doc='brick paving')
    S.tile('flagstone', T.flagstones(['c0', 'c1', 'c2', 'c3'], seed=3), doc='square flagstones')
    for name, (pt, pd, ce, kind) in {'flowers_red': ('fr', 'fr', 'fy', 'tulip'),
                                     'flowers_yellow': ('fy', 'fy', 'fw', 'daisy'),
                                     'flowers_white': ('fw', 'fw', 'fy', 'star')}.items():
        fr = [F.flower_patch(grass, pt, pd, ce, 'g2', frame=f, seed=sum(map(ord, name)), kind=kind)
              for f in range(2)]
        S.tile(name, fr[0], frames=fr, period=32, group='flowers', doc='flower bed (sways)')

    # -- autotiles ------------------------------------------------------------------
    S.section('autotiles')
    kit.path(S, 'path', dirt[0], grass, 'd2', 'g2', 'd4', 'grass', 'dirt lane over grass', inner_alt=dirt[1])
    kit.path(S, 'plaza', cob, grass, 'c1', 'g2', 'c4', 'grass', 'cobbled square over grass',
             seed=5, E=3.0, amp=0.4)
    kit.water(S, WATER, grass, 'g0', 'g2', 'grass', deep=False, doc='village pond / mill race')
    kit.cliffs(S, ROCK, 'r0', grass, grass, 'g4', 'g2', ['g2', 'g4'], ['g5', 'g4', 'r3', 'r2', 'r0', 'g1'],
               stairs_roles=('c4', 'c3', 'c1', 'c0', 'c2'))

    # -- homes -------------------------------------------------------------------------
    S.section('homes')
    add_building(S, 'cottage_red', B.house(64, 64, RED, door_at=42, windows=[(8, 5)], chimney=44,
                                           flower_box=('k2', 'ra3', 'wl2')),
                 door=(2, 3), doc='cottage 4x4, red roof')
    add_building(S, 'cottage_blue', B.house(64, 64, BLUE, door_at=22, windows=[(36, 5)], chimney=12,
                                            roof_style='slate', shutters=('k1', 'k2')),
                 door=(1, 3), doc='cottage 4x4, blue slate')
    add_building(S, 'cottage_gable', B.house(64, 64, GREEN, door_at=32, windows=[(6, 5), (46, 5)],
                                             gable=True, siding='plank', roof_style='shingle'),
                 door=(2, 3), doc='gabled cottage 4x4, green roof, plank walls')
    add_building(S, 'house_red', B.house(80, 64, RED, door_at=40, windows='auto', roof_style='tile',
                                         chimney=58, beams=True),
                 door=(2, 3), doc='house 5x4, clay tiles, timber frame')
    add_building(S, 'house_blue', B.house(80, 64, BLUE, door_at=24, windows=[(40, 5), (58, 5)],
                                          roof_style='slate', flower_box=('k2', 'rb4', 'wl2')),
                 door=(1, 3), doc='house 5x4, slate roof')
    add_building(S, 'house_big', B.house(96, 80, GREEN_BRICK, door_at=48, windows='auto', siding='brick',
                                         roof_style='shingle', storeys=2, chimney=70, beams=True),
                 door=(3, 4), doc='two-storey brick house 6x5')

    # -- civic ---------------------------------------------------------------------------
    S.section('civic')
    hall = B.house(96, 80, style(['ra0', 'ra1', 'ra2', 'ra3', 'ra4']), door_at=48, windows=[(10, 6), (74, 6),
                                                                                          (10, 22), (74, 22)],
                   roof_style='tile', beams=True, storeys=2, door_w=14, roof_h=40,
                   sign=(40, 8, 16, 8), emblem=None)
    # the flame plate covers whole 8x8 tiles, so its colours live in the props bank
    B.flame_emblem('fy', 'fo', 'fr')(hall, 48, 52)
    add_building(S, 'hearth_hall', hall, door=(3, 4), doc='Hearth Hall 6x5: rest and healing (flame sign)')
    shop = B.house(80, 64, BLUE, door_at=40, windows=[(8, 8), (60, 8)], roof_style='slate',
                   awning=(24, 55, ['rb1', 'wl2', 'rb3']))
    add_building(S, 'shop', shop, door=(2, 3), doc='provisions shop 5x4 (awning, sign)')
    add_building(S, 'workshop', B.house(112, 80, BLUE, door_at=56, windows='auto', roof_style='slate',
                                        storeys=2, beams=True, chimney=88, door_w=14),
                 door=(3, 4), doc='workshop / study hall 7x5')
    add_building(S, 'mill',
                 B.house(80, 80, RED,
                         door_at=26, windows=[(44, 6), (44, 24)], siding='stone', roof_style='tile',
                         storeys=2),
                 door=(1, 4), doc='stone mill 5x5 (pair with waterwheel on its east side)')
    add_building(S, 'storehouse', B.house(48, 48, GREEN, door_at=24, windows=None, gable=True,
                                          siding='plank', door_w=12, roof_h=24),
                 door=(1, 2), doc='plank storehouse 3x3')
    S.object('bell_tower', TP.bell_tower(['wl0', 'wl1', 'wl2'], TRIM, ['ra0', 'ra1', 'ra2', 'ra3'],
                                         ['ra1', 'ra3', 'ra4'], 'k0'), top='XX/../../..',
             solid='../XX/XX/XX', doc='signal bell tower 2x4 (Mistbell)')
    wheel = [TP.waterwheel(WOOD, ['s3', 's4', 's5'], 'k0', f) for f in range(4)]
    S.object('waterwheel', wheel[0], frames=wheel, period=6, doc='turning mill wheel 2x3 (animated)')

    # -- trees and hedges --------------------------------------------------------------------
    S.section('trees')
    kit.broadleaf(S, LEAF, 't0', BARK, 'k0', fruit=('fr', 'frd', 7), big=True)
    S.object('bush', F.bush(16, 16, LEAF, 't0', seed=1), doc='round bush')
    S.object('bush_flower', F.bush(16, 16, LEAF, 't0', seed=3, flowers=('fp', 'fw', 4)), doc='rose bush')
    S.patch9('hedge', F.hedge_wall(LEAF, 't0', seed=3, base='t1'), layer='mid', attrs=['SOLID'],
             doc='clipped garden hedge')
    S.object('garden_arch', TP.garden_arch(WOOD, LEAF[1:], ('fp', 'fw'), 'k0'), top='XX/..',
             solid='../X.', doc='rose arch 2x2 (walk under the middle)')

    # -- fences and walls -------------------------------------------------------------------------
    S.section('fences and walls')
    S.patch9('stone_wall', TP.stone_wall(['c0', 'c1', 'c2', 'c3', 'c4'], 'r0'), layer='mid',
             attrs=['SOLID'], doc='dry-stone wall (mass layer)')
    S.custom('fence_picket', PR.picket_block('wl2', 'wl0', 'k0'), 'fence', layer='mid', attrs=['SOLID'],
             doc='white picket fence: row 0 [post][W end][mid][E end], row 1 [N end][mid][S end][gate]')
    S.custom('fence', PR.fence_block(WOOD, 'k0'), 'fence', layer='mid', attrs=['SOLID'], doc='rail fence')

    # -- furniture ------------------------------------------------------------------------------------
    S.section('street furniture')
    S.object('lamp', TP.lamp_post(['s1', 's2', 's3'], 's0', ['fo', 'fy', 'fw']), top='X/.', solid='./X',
             doc='street lamp 1x2; lantern above people')
    S.object('bench', TP.bench(WOOD, ['s1', 's2'], 'k0'), doc='park bench 2x1')
    S.object('mailbox', TP.mailbox('fr', 'k2', WOOD, 'k0', 'fy'), doc='mailbox')
    S.object('flower_pot', TP.flower_pot(['k1', 'k2', 'k3'], 'k0', LEAF[1:], 'fp', 'fw'), doc='potted flowers')
    S.object('planter', TP.planter(WOOD, 'k1', LEAF[1:], ['fr', 'fw', 'fp'], 'k0'), doc='planter box 2x1')
    S.object('barrel_planter', TP.barrel_planter(WOOD, 's1', 'k1', LEAF[1:], 'k0'), doc='half-barrel planter')
    fnt = [TP.fountain(['c1', 'c1', 'c2', 'c3'], ['w1', 'w2', 'w4', 'w5'], 'g0', f) for f in range(4)]
    S.object('fountain', fnt[0], frames=fnt, period=8, top='.X./.../...', solid='.../XXX/XXX',
             doc='plaza fountain 3x3 (animated)')
    S.object('well', TP.well(['s1', 's2', 's3', 's4'], WOOD, ['s0', 's1'], 'k0', ['ra0', 'ra1', 'ra2', 'ra3']),
             top='XX/..', solid='../XX', doc='village well 2x2')
    S.object('statue', TP.statue(STONE, 's0', ['s1', 's2', 's3']), top='XX/../..', solid='../XX/XX',
             doc='founders\' kin statue 2x3')
    S.object('signpost', PR.signpost(WOOD, 'k0'), attrs=['SIGN'], doc='house / town sign')
    S.object('notice_board', PR.notice_board(WOOD, 'k0', 'fw', 's3', 'fr'), top='XX/..', solid='../XX',
             attrs=['SIGN'], doc='village notice board 2x2')
    S.object('street_sign', TP.street_sign(['s1', 's2', 's3'], ['k1', 'k3', 'k4'], 'k0', 's0'), top='X/.',
             solid='./X', attrs=['SIGN'], doc='street name plate 1x2')
    S.object('weather_vane', TP.weather_vane(['s1', 's2', 's3'], 's0', 'k3'), top='X/.',
             solid='./X', doc='weather vane 1x2')
    S.object('bunting', TP.bunting('k0', ['fr', 'fy', 'fo', 'fw'], 'k0'), solid='...', layer='top',
             doc='festival bunting 3x1 (draw above people)')

    # -- trade and household -------------------------------------------------------------------
    S.section('trade and household')
    S.object('market_stall', TP.market_stall(TRIM, ['ra1', 'wl2', 'ra3'], [('ra0', 'ra2', 'ra4'), ('wl0', 'wl1', 'wl2'),
                                                                         ('k1', 'k2', 'k3')], 'k0'),
             top='XXX/...', solid='.../XXX', doc='market stall 3x2, red awning')
    S.object('market_stall_blue', TP.market_stall(TRIM, ['rb1', 'wl2', 'rb3'], [('k1', 'k2', 'k3'), ('gl0', 'gl1', 'gl2')],
                                                  'k0'),
             top='XXX/...', solid='.../XXX', doc='market stall 3x2, blue awning')
    S.object('barrel', PR.barrel(WOOD, 's1', 'k0'), doc='barrel')
    S.object('crate', PR.crate(WOOD, 'k0'), doc='crate')
    S.object('sacks', TP.sacks(['k2', 'k3', 'k4'], 'k0', 'k1'), doc='grain sacks')
    S.object('woodpile', TP.woodpile(WOOD, ['k2', 'k3', 'k4'], 'k0'), doc='stacked firewood 2x1')
    S.object('clothesline', TP.clothesline(WOOD, 'k0', [('ra1', 'ra2', 'ra3'), ('wl0', 'wl1', 'wl2'),
                                                        ('rb1', 'rb2', 'rb3')], 'k0'),
             top='XXX/...', solid='X.X/X.X', doc='drying laundry 3x2')
    S.object('cart', TP.cart(WOOD, ['k0', 'k2'], 'k0', load=[('k1', 'fr', 'fo'), ('fo', 'fy', 'fw')]),
             doc='hand cart 2x1')
    S.object('trough', TP.trough(['c1', 'c2', 'c3'], ['w1', 'w2', 'w4'], 'g0'), doc='water trough 2x1')

    S.object('bridge_h', PR.bridge_h(WOOD, 'k0'), floor='XXX/XXX', solid='.../...', doc='plank bridge E-W 3x2')
    S.object('bridge_v', PR.bridge_v(WOOD, 'k0'), floor='XX/XX/XX', solid='../../..', doc='plank bridge N-S 2x3')
    S.object('lily_pads', F.lily_pad(['g1', 'g2', 'g4'], 'g1', flower=('fw', 'fy')), solid='.', doc='lily pads')
    import farmart as FA
    CROPV = {'leaf': ['t1', 't2', 't3', 't4'], 'out': 't0', 'gold': ['k2', 'k2', 'k4', 'fw'],
             'orange': ['k1', 'k1', 'fr', 'k4'], 'red': ['k1', 'fr', 'k4'], 'stake': ['k1', 'k2'],
             'glow': ['k2', 'fr', 'fr', 'fw'], 'root': {}}
    for kind in ('wheat', 'pumpkin', 'sunflower'):
        S.object('crop_%s_3' % kind, FA.crop(kind, 3, CROPV), solid='.', doc='%s (grown, decor)' % kind)

    S.section('outdoor furniture')
    kit.outdoor(S, {'wood': WOOD, 'out': 'k0', 'stone': STONE, 'stone_out': 's0', 'metal': ['s1', 's2', 's3'],
                    'red': 'fr', 'yellow': 'fy', 'orange': 'fo', 'white': 'fw', 'cloth': ['k1', 'fr', 'fo'],
                    'roof': ['k1', 'k2', 'k3'], 'hay': ['k2', 'fy', 'fw'], 'glow': ['fo', 'fy'],
                    'leaf': ['g1', 'g2', 'g3', 'g4']}, skip=('woodpile', 'cart'))
    S.object('campfire', PR.campfire(WOOD, 'k0', ('fy', 'fo', 'fr'), 0),
             frames=[PR.campfire(WOOD, 'k0', ('fy', 'fo', 'fr'), f) for f in range(3)], period=10,
             doc='campfire (animated)')
    S.object('tent', PR.tent('fo', 'fr', 'k0', 'k2'), top='XX/..', solid='../XX', doc='festival tent 2x2')
    S.object('stump', F.stump(['k1', 'k2', 'k3'], 'k0', 'k4', 'k2'), doc='stump')
    S.object('log', F.log_h(['k1', 'k2', 'k3', 'k4'], 'k0', 'k4', 'k2'), doc='log 2x1')
    S.object('arrow_sign', PR.arrow_sign(WOOD, 'k0'), attrs=['SIGN'], doc='direction arrow')
    kit.rocks(S, STONE, 's0')

    S.scene(village_scene())
    return S


def village_scene():
    sc = Scene('village', 'Maple Village (sample)', 36, 28, 'grass',
               doc='A denser Maple Village: a cobbled square with fountain, statue and market around the '
                   'Hearth Hall, lanes to every door, hedged gardens and flower beds, the mill on its '
                   'stream, an orchard and the bell tower.')
    L = {'.': 'grass', '=': 'path', '#': 'plaza', '~': 'water', 'f': 'flowers', 'd': 'dirt',
         'F': ('forest', 'over'), 'H': ('hedge', 'over'), 'W': ('stone_wall', 'over')}
    sc.rows('''
FFFFFFFFFFFFFFFFF==FFFFFFFFFFFFFFFFF
FFF.............==..............FFFF
F...............==..................
F...............==..................
F...............==..................
F...............==..................
F.....=.........==.............=....
====================================
====================================
F.....=......############....=.....F
F.....=......############....=.....F
F.....=......############=====.....F
F.....=......############..........F
F............############..........F
F............############..........F
F.......~~.......==................F
F.......~~.......==..fff....fff....F
F......~~~.......==..fff....fff....F
F......~~........==................F
F......~~........==................F
F......~~........==.....=.......=..F
F.....~~~........=========......=..F
F.....~~.........==.......========.F
F.....~~.........==................F
F....~~~.........==................F
FF...~~..........==...............FF
FFFF~~~FFFFFFFFFF==FFFFFFFFFFFFFFFFF
FFFF~~FFFFFFFFFFF==FFFFFFFFFFFFFFFFF
''', L)
    obj = [
        ('house_big', 1, 1), ('hearth_hall', 18, 1), ('house_red', 28, 2),
        ('cottage_red', 4, 9), ('shop', 26, 8), ('house_blue', 2, 16), ('mill', 10, 15), ('waterwheel', 8, 16),
        ('cottage_blue', 22, 17), ('cottage_gable', 30, 18), ('bell_tower', 33, 9),
        ('fountain', 17, 10), ('statue', 14, 9), ('market_stall', 21, 12),
        ('lamp', 13, 8), ('lamp', 24, 8), ('lamp', 13, 14), ('lamp', 24, 14), ('bench', 21, 9),
        ('notice_board', 11, 5), ('well', 7, 11), ('mailbox', 7, 13), ('mailbox', 26, 12), ('mailbox', 21, 21),
        ('flower_pot', 25, 5), ('planter', 21, 6), ('barrel_planter', 17, 6), ('signpost', 15, 6),
        ('tree_fruit', 23, 23), ('tree_fruit', 27, 23), ('tree_fruit', 31, 23), ('tree', 1, 23), ('tree_b', 11, 22),
        ('tree_small', 2, 13), ('bush_flower', 31, 16), ('bush', 20, 20), ('clothesline', 2, 21),
        ('woodpile', 14, 21), ('barrel', 16, 20), ('sacks', 15, 20), ('crate', 25, 10), ('cart', 29, 13),
        ('garden_arch', 28, 15), ('trough', 11, 11), ('weather_vane', 26, 6),
    ]
    for (n, x, y) in obj:
        sc.put(n, x, y)
    for x in range(22, 34):
        if x not in (28, 29):
            sc.put('fence_picket:2,0', x, 15)
    sc.sprinkle(['small_flowers', 'pebbles', 'small_flowers'], 22, on={'grass'}, seed=5)
    return sc
