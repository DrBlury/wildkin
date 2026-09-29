"""CITY - Lumen, the lamp-lit canal city.

Replaces the old `city` tileset (Lumen City and its views). Brick streets
with tram rails, slab pavements with curbs, lawns, a stone-banked canal
with an arch bridge, townhouses in three roof/wall pairings, the clock
tower, station, works hall, shops with awnings, electric lamps, a tesla
beacon, parked bikes, cafe tables and planter trees.
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
import cityart as CT
import gothart as GO
import kit

PALETTE = PL.merge(PL.MEADOW, PL.LEAF, PL.BARK, PL.ROOF_RED, PL.WALL_CREAM, PL.GLASS, PL.BRICK, {
    'pv0': '#3a3844', 'pv1': '#5c5a66', 'pv2': '#7e7c86', 'pv3': '#a09ea6', 'pv4': '#c4c2c8',
    'rd0': '#3c2a2a', 'rd1': '#6c4440', 'rd2': '#8c5c52', 'rd3': '#ac7a68',
    'cw0': '#102c44', 'cw1': '#1c486c', 'cw2': '#2c6890', 'cw3': '#4c90b4', 'cw4': '#88c0d8', 'cw5': '#d4f0f8',
    'sl0': '#1c2034', 'sl1': '#2c3450', 'sl2': '#40506c', 'sl3': '#5c708c', 'sl4': '#8498b0',
    'cu0': '#1c3c3c', 'cu1': '#2c6058', 'cu2': '#3c8474', 'cu3': '#5caa8c', 'cu4': '#94d0a8',
    'ws0': '#6c6c78', 'ws1': '#9c9ca8', 'ws2': '#c8c8d0',
    'm0': '#1c1c28', 'm1': '#3c3c4c', 'm2': '#6c6c80',
    'el0': '#f0b040', 'el1': '#fff0a0', 'el2': '#80e0ff', 'el3': '#e0ffff',
    'fr': '#e04040', 'fy': '#f8d030', 'fw': '#f8f8f0', 'fp': '#f088b0',
})
# Lamplight: the city after dark, windows and lamps lit.
NIGHT = {'pv1': '#34324a', 'pv2': '#4a4862', 'pv3': '#62607c', 'pv4': '#7c7a96', 'rd2': '#5c3c44', 'rd3': '#7c5058',
         'g3': '#2c5448', 'g4': '#3c6c58', 'g5': '#548468', 'wl1': '#8c8494', 'wl2': '#aca4b4',
         'gl0': '#a86828', 'gl1': '#f0b040', 'gl2': '#fff0a0', 'ws1': '#6c6c84', 'ws2': '#8c8ca4'}

BANKS = [
    ['pv0', 'pv1', 'pv2', 'pv3', 'pv4', 'rd0', 'rd1', 'rd2', 'rd3', 'g1', 'g2', 'g3', 'g4', 'g5', 'm2'],
    ['cw0', 'cw1', 'cw2', 'cw3', 'cw4', 'cw5', 'pv0', 'pv1', 'pv2', 'pv3', 'pv4', 'g0', 'g1', 'g2', 'g3'],
    ['sl0', 'sl1', 'sl2', 'sl3', 'sl4', 'k0', 'wl0', 'wl1', 'wl2', 'k1', 'k2', 'k3', 'gl0', 'gl1', 'gl2'],
    ['cu0', 'cu1', 'cu2', 'cu3', 'cu4', 'k0', 'bk0', 'bk1', 'bk2', 'k1', 'k2', 'k3', 'gl0', 'gl1', 'gl2'],
    ['ra0', 'ra1', 'ra2', 'ra3', 'ra4', 'k0', 'ws0', 'ws1', 'ws2', 'k1', 'k2', 'k3', 'gl0', 'gl1', 'gl2'],
    ['t0', 't1', 't2', 't3', 't4', 't5', 'k0', 'k1', 'k2', 'k3', 'k4', 'fr', 'fp', 'fw', 'fy'],
    ['m0', 'm1', 'm2', 'el0', 'el1', 'el2', 'el3', 'pv1', 'pv2', 'pv3', 'k0', 'k1', 'k2', 'fr', 'fw'],
]

GRASS = {'dk': 'g1', 'mid': 'g2', 'base': 'g3', 'lt': 'g4', 'hi': 'g5', 'out': 'g0'}
CANAL = {'deep': 'cw1', 'base': 'cw2', 'lt': 'cw3', 'hi': 'cw4', 'foam': 'cw5', 'dark': 'cw0'}
TRIM = ['k1', 'k2', 'k3']
GLASS = ['gl0', 'gl1', 'gl2']
METAL = ['m0', 'm1', 'm2']


def style(roof, wall):
    return {'out': 'k0', 'roof': roof, 'wall': list(wall), 'trim': TRIM, 'glass': GLASS,
            'found': ['k1', wall[0], wall[1]], 'chimney': ['k1', wall[0], wall[1]]}


SLATE = style(['sl0', 'sl1', 'sl2', 'sl3', 'sl4'], ('wl0', 'wl1', 'wl2'))
COPPER = style(['cu0', 'cu1', 'cu2', 'cu3', 'cu4'], ('bk0', 'bk1', 'bk2'))
CLAY = style(['ra0', 'ra1', 'ra2', 'ra3', 'ra4'], ('ws0', 'ws1', 'ws2'))


def build():
    S = Sheet('city', 'City - Lumen', PALETTE, variants={'night': NIGHT}, banks=BANKS, doc=__doc__)
    S.section('ground')
    road = T.bricks(['rd0', 'rd1', 'rd2', 'rd3'], bw=8, bh=4)
    S.tile('road', road, doc='brick street')
    pave = T.bricks(['pv2', 'pv2', 'pv3', 'pv4'], bw=16, bh=8)
    S.tile('pavement', pave, group='pavement', weight=4, doc='slab pavement')
    S.tile('pavement_b', T.flagstones(['pv1', 'pv2', 'pv3', 'pv4'], seed=2), group='pavement', weight=1,
           doc='flagged plaza')
    grass = kit.grass_family(S, 'lawn', GRASS, doc='park lawn')

    S.section('autotiles')
    kit.path(S, 'sidewalk', pave, road, 'pv4', 'pv0', 'pv1', 'road', 'pavement over the street (curb edge)',
             seed=1, E=3.0, amp=0.0, R=1.0)
    kit.path(S, 'lawn_bed', grass, pave, 'g1', 'pv0', 'g4', 'pavement', 'lawn inset in the pavement', seed=2,
             E=3.0, amp=0.0, R=2.0)
    kit.water(S, CANAL, pave, 'pv0', 'pv1', 'pavement', name='canal', deep=False,
              doc='canal with a stone embankment')
    S.custom('tram', CT.tram_track(road, METAL, 'k0'), 'tram', doc='tram rails in the street: [E-W][N-S][cross][stop]')

    S.section('buildings')
    S.object('townhouse_slate', B.house(64, 80, SLATE, door_at=40, windows=[(6, 6), (6, 24), (42, 6)],
                                        roof_style='slate', storeys=2, chimney=12, beams=True),
             doc='townhouse 4x5, slate over cream', extra={'door': [2, 4]})
    S.object('townhouse_copper', B.house(64, 80, COPPER, door_at=24, windows=[(38, 6), (38, 24), (6, 6)],
                                         roof_style='shingle', storeys=2, siding='brick', chimney=48),
             doc='townhouse 4x5, copper over brick', extra={'door': [1, 4]})
    S.object('townhouse_clay', B.house(80, 80, CLAY, door_at=40, windows='auto', roof_style='tile', storeys=2,
                                       siding='stone'), doc='townhouse 5x5, clay over grey stone', extra={'door': [2, 4]})
    S.object('shop', B.house(80, 64, SLATE, door_at=40, windows=[(6, 8), (62, 8)], roof_style='slate',
                             awning=(22, 57, ['sl1', 'wl2', 'sl3'])), doc='shop 5x4 with awning', extra={'door': [2, 3]})
    S.object('cafe', B.house(80, 64, CLAY, door_at=24, windows=[(40, 8), (58, 8)], roof_style='tile',
                             awning=(34, 76, ['ra1', 'ws2', 'ra3'])), doc='cafe 5x4', extra={'door': [1, 3]})
    S.object('station', B.house(128, 80, COPPER, door_at=64, windows='auto', roof_style='shingle', siding='brick',
                                storeys=2, door_w=20, beams=True), doc='tram station 8x5', extra={'door': [4, 4]})
    S.object('works', B.house(112, 80, CLAY, door_at=32, windows='auto', roof_style='tile', siding='stone', storeys=2,
                              chimney=88, door_w=16), doc='Resonance Works 7x5', extra={'door': [2, 4]})
    S.object('clock_tower', CT.clock_tower(['ws0', 'ws1', 'ws2', 'ws2'], ['ra0', 'ra1', 'ra2', 'ra3'],
                                           ['k0', 'ws1', 'ws2'], ['k1', 'k3'], 'k0'),
             top='XXX/XXX/XXX/.../.../...', solid='.../.../.../XXX/XXX/XXX', doc='clock tower 3x6',
             extra={'door': [1, 5]})
    kit.civic(S, CLAY, ('gl2', 'ra4', 'ra2'), roof_style='tile', siding='stone', skip=('shop', 'hall'))
    S.object('market_hall', B.house(128, 80, COPPER, door_at=64, windows='auto', roof_style='shingle', siding='brick',
                                    door_w=24, awning=(40, 87, ['cu1', 'bk2', 'cu3'])),
             doc='market hall 8x5', extra={'door': [4, 4]})
    S.object('volt_hall', B.house(112, 96, SLATE, door_at=56, windows='auto', roof_style='slate', storeys=2,
                                  door_w=20, beams=True), doc='Volt Hall 7x6', extra={'door': [3, 5]})
    S.object('bike_shop', B.house(80, 64, COPPER, door_at=24, windows=[(40, 8), (58, 8)], roof_style='shingle',
                                  siding='brick', awning=(34, 76, ['cu1', 'bk2', 'cu3'])),
             doc='bike shop 5x4', extra={'door': [1, 3]})
    S.object('row_houses', B.house(128, 80, SLATE, door_at=24, windows=[(40, 6), (72, 6), (104, 6), (8, 24), (40, 24),
                                                                        (72, 24), (104, 24)], roof_style='slate',
                                   storeys=2, chimney=60, beams=True), doc='terraced row 8x5', extra={'door': [1, 4]})
    S.object('kiosk', CT.kiosk(['wl0', 'wl1', 'wl2'], ['sl0', 'sl1', 'sl2'], GLASS, 'k2', 'k0'), top='XX/../..',
             solid='../XX/XX', doc='news kiosk 2x3')

    S.section('street')
    lp = [CT.electric_lamp(METAL, ['el0', 'el0', 'el1'], 'm0', f) for f in range(2)]
    S.object('lamp', lp[0], frames=lp, period=40, top='X/.', solid='./X', doc='electric street lamp 1x2')
    tb = [CT.tesla_beacon(METAL, ['k1', 'el0', 'el1'], ['el2', 'el3'], 'm0', f) for f in range(2)]
    S.object('beacon', tb[0], frames=tb, period=6, top='X/X/.', solid='./X/X', doc='tesla beacon 1x3 (sparks)')
    S.object('bike', CT.parked_bike(['m0', 'm2'], 'm0', 'm0'), doc='parked bike 2x1')
    S.object('cafe_table', CT.cafe_table(['pv2', 'fw', 'fw'], METAL, ['fr', 'fr', 'fw'], 'm0'), top='XX/..',
             solid='../XX', doc='cafe table and parasol 2x2')
    S.object('bench', TP.bench(['k1', 'k2', 'k3', 'k4'], ['k0', 'k1'], 'k0'), doc='bench 2x1')
    S.object('planter_tree', CT.planter_tree(['t0', 't1', 't2', 't3', 't4', 't5'], ['k1', 'k2', 'k3'], ['k1', 'k2', 'k3'],
                                             'k0'), top='X/.', solid='./X', doc='street tree in a planter 1x2')
    S.object('flower_pot', TP.flower_pot(['k1', 'k2', 'k3'], 'k0', ['t1', 't2', 't3', 't4', 't5'], 'fp', 'fw'),
             doc='flower pot')
    S.custom('railing', GO.iron_fence(['m1', 'm2', 'pv3'], 'm0'), 'fence', layer='mid', attrs=['SOLID'],
             doc='canal railing (fence layout)')
    S.object('bridge', CT.arch_bridge(['pv1', 'pv2', 'pv3'], ['pv1', 'pv2', 'pv3'], 'pv0'), floor='XXX/XXX/XXX',
             solid='.../.../...', doc='arch bridge 3x3 (north-south, over the canal)')
    fnt = [TP.fountain(['pv1', 'pv1', 'pv2', 'pv3'], ['cw1', 'cw2', 'cw4', 'cw5'], 'pv0', f) for f in range(4)]
    S.object('fountain', fnt[0], frames=fnt, period=8, top='.X./.../...', solid='.../XXX/XXX', doc='plaza fountain 3x3')
    S.object('mailbox', TP.mailbox('fr', 'k2', ['k1', 'k2', 'k3'], 'm0', 'fw'), doc='post box')
    S.object('street_sign', TP.street_sign(METAL, ['pv1', 'pv2', 'pv3'], 'm0', 'm0'), top='X/.', solid='./X',
             attrs=['SIGN'], doc='street sign 1x2')
    S.object('crate', PR.crate(['k1', 'k2', 'k3', 'k4'], 'k0'), doc='crate')
    S.object('barrel', PR.barrel(['k1', 'k2', 'k3', 'k4'], 'k0', 'k0'), doc='barrel')
    S.object('tree', F.round_tree('mid', ['t0', 't1', 't2', 't3', 't4', 't5'], 't0', ['k1', 'k2', 'k3'], 'k0', seed=3),
             top='XX/..', solid='../XX', doc='park tree 2x2')
    S.object('hedge_bush', F.bush(16, 16, ['t0', 't1', 't2', 't3', 't4'], 't0', seed=4), doc='clipped bush')

    S.scene(lumen_scene())
    return S


def lumen_scene():
    sc = Scene('lumen', 'Lumen canal district (sample)', 40, 28, 'pavement',
               doc='Brick streets with a tram line, pavements with curbs, the canal with an arch bridge '
                   'and railings, the clock-tower plaza with its fountain, townhouses, shops, the '
                   'station and the works.')
    L = {'.': 'pavement', 'r': 'road', 's': 'sidewalk', '~': 'canal', 'g': 'lawn_bed'}
    sc.rows('''
........................................
........................................
........................................
........................................
........................................
........................................
rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
........................................
..........gggg.............gggg.........
..........gggg.............gggg.........
........................................
........................................
........................................
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
........................................
........................................
........................................
........................................
rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr
........................................
........................................
........................................
........................................
........................................
''', L)
    for x in range(40):
        sc.put('tram:0,0', x, 7)
    obj = [('station', 0, 1), ('townhouse_slate', 9, 1), ('townhouse_copper', 13, 1), ('shop', 17, 2),
           ('clock_tower', 23, 0), ('townhouse_clay', 27, 1), ('cafe', 32, 2), ('fountain', 18, 10),
           ('lamp', 8, 8), ('lamp', 16, 8), ('lamp', 25, 8), ('lamp', 33, 8), ('beacon', 22, 9), ('bench', 14, 12),
           ('bench', 24, 12), ('planter_tree', 2, 11), ('planter_tree', 36, 11), ('cafe_table', 33, 10),
           ('bike', 5, 12), ('kiosk', 29, 10), ('bridge', 12, 14), ('bridge', 28, 14), ('works', 1, 17),
           ('townhouse_slate', 9, 16), ('townhouse_copper', 16, 16), ('shop', 21, 17), ('townhouse_clay', 27, 16),
           ('townhouse_slate', 33, 16), ('lamp', 8, 23), ('lamp', 20, 23), ('lamp', 32, 23), ('tree', 3, 24),
           ('tree', 35, 24), ('street_sign', 11, 23), ('mailbox', 26, 24), ('crate', 5, 23), ('barrel', 6, 23),
           ('flower_pot', 15, 24), ('flower_pot', 24, 24), ('hedge_bush', 17, 25), ('hedge_bush', 18, 25)]
    for x in list(range(0, 12)) + list(range(15, 28)) + list(range(31, 40)):
        sc.put('railing:2,0', x, 13)
    for (n, x, y) in obj:
        sc.put(n, x, y)
    return sc
