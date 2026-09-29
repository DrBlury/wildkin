"""FARM - Willow Acre and the player's homestead.

Replaces the old `farm` tileset. Soil and crop art match the dynamic farm
cells in src/game/farm.c (tilled / watered soil, four growth stages per
crop); buildings and yard props give the homestead a lived-in look. Four
seasonal palette variants re-colour the same tiles (spring, summer = base,
autumn, winter).
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
import farmart as FA
import extras as X
import kit

PALETTE = PL.merge(PL.MEADOW, PL.DIRT, PL.FRESH_WATER, PL.STONE_GREY, PL.LEAF, PL.BARK, PL.FLOWERS,
                   PL.ROOF_RED, PL.WALL_CREAM, PL.GLASS, {
                       # tilled soil (dry) and watered soil
                       'so0': '#3a2420', 'so1': '#5c3a2a', 'so2': '#7c5236', 'so3': '#9c6c44',
                       'sw0': '#24161a', 'sw1': '#3a2622', 'sw2': '#4e3428', 'sw3': '#664430',
                       # crop greens (brighter than meadow grass)
                       'cg0': '#1c4428', 'cg1': '#2c7034', 'cg2': '#48a03c', 'cg3': '#84d050',
                       # harvest colours
                       'gd1': '#b8862c', 'gd2': '#e0b440', 'gd3': '#f8e070',
                       'po1': '#b85424', 'po2': '#e88030', 'po3': '#f8b060',
                       'pr1': '#6a2c5c', 'pr2': '#a44c88',
                       # barn
                       'bn0': '#6a1c24', 'bn1': '#9c2c2c', 'bn2': '#c44c3c',
                       'sl0': '#2c3444', 'sl1': '#48546a', 'sl2': '#6a788c', 'sl3': '#94a0b0',
                   })

SPRING = {'g3': '#74bc5c', 'g4': '#a0d874', 'g5': '#d4f0a0', 't3': '#48a050', 't4': '#74c460', 't5': '#b4e490'}
AUTUMN = {'g1': '#5a5a30', 'g2': '#8a8a40', 'g3': '#b0a650', 'g4': '#d0c068', 'g5': '#e8dc90',
          't1': '#6a2c24', 't2': '#9a3c28', 't3': '#c85c30', 't4': '#e88a3c', 't5': '#f8b85c',
          'cg1': '#6a6a30', 'cg2': '#a09040', 'cg3': '#d0b860'}
WINTER = {'g0': '#3c4c6c', 'g1': '#8494b4', 'g2': '#b0bcd4', 'g3': '#d4dcec', 'g4': '#ecf0f8', 'g5': '#ffffff',
          't1': '#4c5c6c', 't2': '#6c7c8c', 't3': '#98a8b8', 't4': '#c8d4e0', 't5': '#f0f4f8',
          'd1': '#6c6070', 'd2': '#8c8494', 'd3': '#b0a8b4', 'd4': '#ccc8d0', 'd5': '#e4e0e8',
          'so1': '#6c6474', 'so2': '#8c8494', 'so3': '#b8b4c4',
          'w1': '#5c7cb0', 'w2': '#8cacd8', 'w3': '#b8d0ec', 'w4': '#dce8f8', 'w5': '#ffffff'}

BANKS = [
    ['g0', 'g1', 'g2', 'g3', 'g4', 'g5', 'd0', 'd1', 'd2', 'd3', 'd4', 'd5', 'fr', 'fy', 'fw'],
    ['g1', 'g2', 'g3', 'g4', 'g5', 'so0', 'so1', 'so2', 'so3', 'sw0', 'sw1', 'sw2', 'sw3', 'd2', 'd3'],
    ['g0', 'g1', 'g2', 'g3', 'g4', 'g5', 'w0', 'w1', 'w2', 'w3', 'w4', 'w5', 's1', 's2', 's3'],
    ['cg0', 'cg1', 'cg2', 'cg3', 'gd1', 'gd2', 'gd3', 'po1', 'po2', 'po3', 'pr1', 'pr2', 'fr', 'k1', 'k2'],
    ['ra0', 'ra1', 'ra2', 'ra3', 'ra4', 'k0', 'wl0', 'wl1', 'wl2', 'k1', 'k2', 'k3', 'gl0', 'gl1', 'gl2'],
    ['bn0', 'bn1', 'bn2', 'wl1', 'wl2', 'sl0', 'sl1', 'sl2', 'sl3', 'k0', 'gl0', 'gl1', 'gl2', 'k1', 'k2'],
    ['t0', 't1', 't2', 't3', 't4', 't5', 'k0', 'k1', 'k2', 'k3', 'k4', 'fr', 'frd', 'fp', 'fw'],
    ['s0', 's1', 's2', 's3', 's4', 's5', 'k0', 'k1', 'k2', 'k3', 'k4', 'gd2', 'gd3', 'fy', 'fw'],
]

GRASS = {'dk': 'g1', 'mid': 'g2', 'base': 'g3', 'lt': 'g4', 'hi': 'g5', 'out': 'g0'}
DIRT = {'dk': 'd1', 'mid': 'd2', 'base': 'd3', 'lt': 'd4', 'hi': 'd5'}
WATER = {'deep': 'w1', 'base': 'w2', 'lt': 'w3', 'hi': 'w4', 'foam': 'w5', 'dark': 'w0'}
LEAF = ['t0', 't1', 't2', 't3', 't4', 't5']
BARK = ['k1', 'k2', 'k3']
WOOD = ['k1', 'k2', 'k3', 'k4']
TRIM = ['k1', 'k2', 'k3']
GLASS = ['gl0', 'gl1', 'gl2']
CROP = {'leaf': ['cg0', 'cg1', 'cg2', 'cg3'], 'out': 'cg0', 'gold': ['gd1', 'gd1', 'gd2', 'gd3'],
        'orange': ['po1', 'po1', 'po2', 'po3'], 'red': ['k1', 'fr', 'po3'], 'stake': ['k1', 'k2'],
        'glow': ['k2', 'pr1', 'pr2', 'po3'],
        'root': {'turnip': ['pr1', 'pr2', 'fr'], 'carrot': ['po1', 'po2', 'po3'], 'beet': ['pr1', 'pr1', 'pr2']}}

HOUSE = {'out': 'k0', 'roof': ['ra0', 'ra1', 'ra2', 'ra3', 'ra4'], 'wall': ['wl0', 'wl1', 'wl2'], 'trim': TRIM,
         'glass': GLASS, 'found': ['k1', 'wl0', 'wl1'], 'chimney': ['k1', 'wl0', 'wl1']}


def build():
    S = Sheet('farm', 'Farm - Willow Acre homestead', PALETTE,
              variants={'spring': SPRING, 'autumn': AUTUMN, 'winter': WINTER}, banks=BANKS, doc=__doc__)
    S.section('ground')
    grass = kit.grass_family(S, 'grass', GRASS, flowers={'n': 2, 'petals': ['fw', 'fy'], 'center': 'fy'},
                             doc='pasture')
    dirt = kit.speckle_family(S, 'dirt', DIRT, doc='yard earth')
    dry = FA.soil(['so0', 'so1', 'so2', 'so3'], seed=1)
    wet = FA.soil(['sw0', 'sw1', 'sw2', 'sw3'], seed=1)
    S.tile('soil', dry, attrs=['SOIL'], doc='tilled soil (dry)')
    S.tile('soil_wet', wet, attrs=['SOIL'], doc='tilled soil (watered)')

    S.section('autotiles')
    kit.path(S, 'path', dirt[0], grass, 'd2', 'g2', 'd4', 'grass', 'farm track over grass', inner_alt=dirt[1])
    kit.path(S, 'field', dry, grass, 'so1', 'g2', 'so3', 'grass', 'tilled field over grass (dry)',
             seed=4, E=3.0, amp=0.3, attrs=['SOIL'])
    kit.path(S, 'field_wet', wet, grass, 'sw1', 'g2', 'sw3', 'grass', 'tilled field over grass (watered)',
             seed=4, E=3.0, amp=0.3, attrs=['SOIL'])
    kit.water(S, WATER, grass, 'g0', 'g2', 'grass', deep=False, doc='farm pond')

    S.section('crops')
    for kind in ('turnip', 'carrot', 'wheat', 'corn', 'pumpkin', 'tomato', 'sunflower', 'glowcap'):
        for st in range(4):
            S.object('crop_%s_%d' % (kind, st), FA.crop(kind, st, CROP), solid='.',
                     doc=('%s, growth stage %d/3' % (kind, st)) if st == 0 else '',
                     extra={'crop': kind, 'stage': st})

    S.section('buildings')
    S.object('farmhouse', B.house(96, 80, HOUSE, door_at=36, windows=[(10, 6), (56, 6), (74, 6), (56, 22), (74, 22)],
                                  roof_style='shingle', storeys=2, chimney=72, beams=True, flower_box=('k2', 'ra3', 'wl2')),
             doc='farmhouse 6x5', extra={'door': [2, 4]})
    S.object('barn', FA.barn(96, 80, ['bn0', 'bn1', 'bn2'], ['wl1', 'wl2'], ['sl0', 'sl1', 'sl2', 'sl3'], 'k0',
                             ['k1'], ['gl0', 'gl1', 'gl2']),
             doc='gambrel barn 6x5 (big door in the bottom middle)', extra={'door': [2, 4]})
    S.object('silo', FA.silo(['sl0', 'sl1', 'sl2', 'sl3'], ['bn0', 'bn1', 'bn2'], 'k0'), top='XX/../../..',
             solid='../XX/XX/XX', doc='grain silo 2x4')
    mill = [FA.windmill(['wl0', 'wl1', 'wl2'], ['ra0', 'ra1', 'ra2'], ['k1', 'wl1', 'wl2'], 'k0', f)
            for f in range(4)]
    S.object('windmill', mill[0], frames=mill, period=10, top='XXX/XXX/.../...', solid='.../.../XXX/XXX',
             doc='windmill 3x4, turning sails')
    S.object('greenhouse', FA.greenhouse(['k1', 'k2', 'k3'], ['gl0', 'gl1', 'gl2'], [('k1', 'ra2', 'ra4'), ('k1', 'wl1', 'wl2')], 'k0'),
             doc='greenhouse 4x3', extra={'door': [2, 2]})
    S.object('coop', FA.coop(['bn0', 'bn1', 'bn2'], ['sl0', 'sl1', 'sl2'], 'k0', ['k1', 'wl2']),
             top='XX/..', solid='../XX', doc='chicken coop 2x2')
    S.object('shed', B.house(48, 48, dict(HOUSE, wall=['k1', 'k2', 'k3'], found=['k1', 'k1', 'k2']), door_at=24,
                             gable=True, siding='plank', roof_h=24, door_w=12),
             doc='tool shed 3x3', extra={'door': [1, 2]})

    S.section('yard')
    S.custom('fence', PR.fence_block(WOOD, 'k0'), 'fence', layer='mid', attrs=['SOLID'], doc='paddock rail fence')
    S.object('hay_round', FA.hay_round(['k2', 'gd2', 'gd3'], 'k0'),
             doc='round hay bale')
    S.object('hay_bale', FA.hay_bale(['k2', 'gd2', 'gd3'], 'k0', 'k1'), doc='square bales 2x1')
    S.object('scarecrow', FA.scarecrow(WOOD, ['k1', 'k2', 'k3'], ['k1', 'k2', 'k3'], 'gd3', 'gd2', 'k0'),
             top='X/.', solid='./X', doc='scarecrow 1x2')
    S.object('beehive', FA.beehive(['k2', 'k3', 'k4'], ['s1', 's2', 's3'], 'k0', 'fy'), doc='beehive')
    S.object('pump', FA.pump(['s1', 's2', 's3'], 's0', 's4'), doc='water pump')
    S.object('shipping_bin', FA.shipping_bin(WOOD, ['k1', 'k2', 'k3'], 'k0'), doc='shipping bin 2x1')
    S.object('trough', TP.trough(WOOD, ['s1', 's2', 's4'], 'k0'), doc='feed trough 2x1')
    S.object('woodpile', TP.woodpile(WOOD, ['k2', 'k3', 'k4'], 'k0'), doc='firewood 2x1')
    S.object('cart', TP.cart(WOOD, ['k0', 'k2'], 'k0', load=[('k2', 'gd2', 'gd3')]), doc='hay cart 2x1')
    S.object('barrel', PR.barrel(WOOD, 's1', 'k0'), doc='rain barrel')
    S.object('crate', PR.crate(WOOD, 'k0'), doc='produce crate')
    S.object('signpost', PR.signpost(WOOD, 'k0'), attrs=['SIGN'], doc='field sign')
    S.object('mailbox', TP.mailbox('s3', 's1', WOOD, 'k0', 'fy'), doc='farm mailbox')

    S.object('preserves', X.preserves('s4', ['gd2', 'k2', 'fy'], 'k1', 'k0'), doc='jars of preserves')
    S.object('cider_press', X.cider_press(['k1', 'k2', 'k3'], ['s1', 's2', 's3'], 'k0'), top='XX/..', solid='../XX',
             doc='fruit press 2x2')
    S.object('drying_rack', X.drying_rack(['k1', 'k2', 'k3'], ['gd2', 'k3', 'fy'], 'k0'), top='XX/..', solid='X./X.',
             doc='herb drying rack 2x2')
    S.object('for_sale', PR.signpost(WOOD, 'k0', face='fw'), attrs=['SIGN'], doc='"for sale" plot sign')
    S.object('farm_chest', X.chest(['k1', 'k2', 'k3'], ['s1', 's2', 's3'], 'k0'), doc='storage chest')

    S.section('orchard and wild')
    kit.broadleaf(S, LEAF, 't0', BARK, 'k0', fruit=('fr', 'frd', 8), big=True, prefix='')
    S.object('tree_peach', F.round_tree('mid', LEAF, 't0', BARK, 'k0', seed=11, fruit=('fp', 'frd', 8)),
             top='XX/..', solid='../XX', doc='peach tree 2x2')
    S.object('bush', F.bush(16, 16, LEAF, 't0', seed=1), doc='bush')
    S.object('bush_berry', F.bush(16, 16, LEAF, 't0', seed=2, berries=('fr', 'frd', 4)), doc='berry bush')
    S.object('stump', F.stump(['k1', 'k2', 'k3'], 'k0', 'k4', 'k2'), doc='stump (clear with an axe)')
    S.object('rock', PR.small_rock(['s1', 's2', 's3', 's4', 's5'], 's0', 1), doc='field stone (clear)')
    S.object('weeds', F.bush(16, 16, ['t0', 't1', 't2', 't3', 't4'], 't0', seed=21, n=6), solid='.',
             doc='weeds (clear)')

    S.scene(farm_scene())
    return S


def farm_scene():
    sc = Scene('homestead', 'Willow Acre homestead (sample)', 36, 26, 'grass',
               doc='Farmhouse and barn around a yard, fenced fields in several growth stages, '
                   'an orchard, pond, coop, beehives and the windmill.')
    L = {'.': 'grass', '=': 'path', '~': 'water', 's': 'field', 'w': 'field_wet', 'd': 'dirt',
         'F': ('forest', 'over')}
    sc.rows('''
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
FF................................FF
F..................................F
F..................................F
F..................................F
F.........==========...............F
F.........=........=...............F
F.........=........=...............F
F=========================.........F
F....=..........=..........=.......F
F....=..........=..........=.......F
F....=..ssssss..=..wwwwww..=.......F
F....=..ssssss..=..wwwwww..=..~~~..F
F....=..ssssss..=..wwwwww..=.~~~~~.F
F....=..ssssss..=..wwwwww..=.~~~~~.F
F....=..........=..........=..~~~..F
F....=====================.=.......F
F....=..........=..........=.......F
F....=..ssssss..=..ssssss..=.......F
F....=..ssssss..=..ssssss..=.......F
F....=..ssssss..=..ssssss..=.......F
F....=..........=..........=.......F
F....=.....................=.......F
FF...=.....................=......FF
FFFF.=FFFFFFFFFFFFFFFFFFFFF=FFFFFFFF
FFFFF=FFFFFFFFFFFFFFFFFFFFF=FFFFFFFF
''', L)
    # crops by field
    fields = [((8, 11), 'turnip', 3), ((19, 11), 'wheat', 2), ((8, 18), 'pumpkin', 3), ((19, 18), 'corn', 1)]
    for (x0, y0), kind, stg in fields:
        for y in range(y0, y0 + (4 if y0 == 11 else 3)):
            for x in range(x0, x0 + 6):
                sc.put('crop_%s_%d' % (kind, stg if (x + y) % 5 else max(0, stg - 1)), x, y)
    obj = [('farmhouse', 2, 2), ('barn', 20, 1), ('silo', 26, 1), ('windmill', 31, 3), ('coop', 13, 5),
           ('greenhouse', 29, 17), ('shipping_bin', 11, 7), ('scarecrow', 11, 12), ('scarecrow', 22, 19),
           ('beehive', 32, 21), ('beehive', 33, 21), ('pump', 17, 7), ('trough', 15, 3),
           ('hay_round', 24, 6), ('hay_round', 25, 7), ('hay_bale', 28, 8), ('woodpile', 8, 7),
           ('tree_fruit', 1, 10), ('tree_peach', 1, 14), ('tree_fruit', 1, 18),
           ('tree_small', 34, 13), ('bush_berry', 28, 22), ('stump', 25, 22),
           ('rock', 20, 23), ('weeds', 14, 22), ('weeds', 9, 23), ('mailbox', 6, 7), ('signpost', 26, 16),
           ('barrel', 7, 7), ('cart', 22, 7), ('crate', 18, 7)]
    for (n, x, y) in obj:
        sc.put(n, x, y)
    for x in range(7, 15):
        sc.put('fence:2,0', x, 10)
    sc.sprinkle(['weeds', 'rock', 'stump', 'weeds'], 14, on={'grass'}, seed=4)
    return sc
