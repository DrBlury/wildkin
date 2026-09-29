"""DESERT - dunes, sandstone mesas, oases and adobe villages.

Replaces the old `desert` tileset (Saffron Dunes, Sunwell, Sunwell Cistern
approach). Wind-rippled dunes, hard-pan, sandstone strata cliffs, a
turquoise oasis, palms, cacti, adobe homes with beam ends, market canopies,
water jars and sun-bleached ruins.
"""

from core import Img
from sheet import Sheet, Scene
import palettes as PL
import paint as P
import terrain as T
import flora as F
import props as PR
import townprops as TP
import coastart as C
import desertart as DS
import kit

PALETTE = PL.merge(PL.BARK, {
    'ds0': '#5c3420', 'ds1': '#9c6034', 'ds2': '#cc8c48', 'ds3': '#e4b064', 'ds4': '#f4cc84', 'ds5': '#fce8b4',
    'hp1': '#a07850', 'hp2': '#b89468',
    'st0': '#4c2418', 'st1': '#7c3c24', 'st2': '#a85c34', 'st3': '#cc8448', 'st4': '#e4a868', 'st5': '#f4cc94',
    'oa0': '#0c4c5c', 'oa1': '#107c88', 'oa2': '#20a8a8', 'oa3': '#50d0c4', 'oa4': '#a0f0e0', 'oa5': '#e8fff8',
    'cg0': '#1c3c24', 'cg1': '#2c6034', 'cg2': '#4c8c44', 'cg3': '#7cb45c',
    'pl0': '#1c4c30', 'pl1': '#2c7040', 'pl2': '#48a050', 'pl3': '#84cc6c',
    'ad0': '#6c3c28', 'ad1': '#a4643c', 'ad2': '#cc8c58', 'ad3': '#e8b07c',
    'cl0': '#6c1c1c', 'cl1': '#b43c2c', 'cl2': '#e87850',
    'cb0': '#1c3c6c', 'cb1': '#3464a4', 'cb2': '#6c9cd8',
    'bn1': '#c4bca8', 'bn2': '#f4ecd8',
    'fp': '#f070a0', 'fy': '#f8d030',
})
# Midday haze and a cooler dusk for the same dunes.
DUSK = {'ds2': '#a86c50', 'ds3': '#c08860', 'ds4': '#d4a47c', 'ds5': '#e8c49c',
        'st2': '#8c4c3c', 'st3': '#a8644c', 'st4': '#c48464', 'oa2': '#1c7c90', 'oa3': '#3ca0b0'}

BANKS = [
    ['ds0', 'ds1', 'ds2', 'ds3', 'ds4', 'ds5', 'hp1', 'hp2', 'cg0', 'cg1', 'cg2', 'cg3', 'bn1', 'bn2'],
    ['oa0', 'oa1', 'oa2', 'oa3', 'oa4', 'oa5', 'ds1', 'ds2', 'ds3', 'ds4', 'ds5', 'pl1', 'pl2', 'pl3'],
    ['st0', 'st1', 'st2', 'st3', 'st4', 'st5', 'ds1', 'ds2', 'ds3', 'ds4', 'ds5'],
    ['cg0', 'cg1', 'cg2', 'cg3', 'pl0', 'pl1', 'pl2', 'pl3', 'k0', 'k1', 'k2', 'k3', 'fp', 'fy', 'bn2'],
    ['ad0', 'ad1', 'ad2', 'ad3', 'k0', 'k1', 'k2', 'k3', 'cl0', 'cl1', 'cl2', 'cb0', 'cb1', 'cb2', 'oa1'],
    ['st0', 'st1', 'st2', 'st3', 'st4', 'st5', 'k0', 'k1', 'k2', 'k3', 'k4', 'bn1', 'bn2', 'oa2', 'oa3'],
]

SAND = {'dk': 'ds1', 'mid': 'ds2', 'base': 'ds3', 'lt': 'ds4', 'hi': 'ds5'}
PAN = {'dk': 'ds1', 'mid': 'hp1', 'base': 'hp2', 'lt': 'ds3', 'hi': 'ds4'}
SCRUB = {'dk': 'cg0', 'mid': 'cg1', 'base': 'ds3', 'lt': 'cg2', 'hi': 'ds4', 'out': 'ds1'}
OASIS = {'deep': 'oa1', 'base': 'oa2', 'lt': 'oa3', 'hi': 'oa4', 'foam': 'oa5', 'dark': 'oa0'}
STRATA = ['st1', 'st2', 'st3', 'st4', 'st5']
CACTUS = ['cg0', 'cg1', 'cg2', 'cg3']
WOOD = ['k1', 'k2', 'k3', 'k4']
ADOBE = ['ad0', 'ad1', 'ad2', 'ad3']


def build():
    S = Sheet('desert', 'Desert - dunes, mesas, oases', PALETTE, variants={'dusk': DUSK}, banks=BANKS, doc=__doc__)
    S.section('ground')
    sand = kit.speckle_family(S, 'sand', SAND, seeds=(3, 4, 5), doc='loose sand', dots=(8, 10, 6),
                              pebbles=(1, 1, 0), grain=0.2)
    dn = [DS.dunes(['ds1', 'ds2', 'ds3', 'ds4', 'ds5'], s) for s in (1, 2)]
    S.tile('dunes', dn[0], group='dunes', weight=2, doc='wind-rippled dune (walkable)')
    S.tile('dunes_b', dn[1], group='dunes', weight=1)
    pan = kit.speckle_family(S, 'hardpan', PAN, seeds=(11, 12), doc='cracked hard-pan', dots=(8, 6),
                             pebbles=(1, 0), cracks=(1, 2), weights=(3, 2))
    scrub = kit.grass_family(S, 'scrub', SCRUB, seeds=(21, 22, 23, 24), doc='dry sedge (encounters)',
                             attrs=['GRASS'], tufts=(3, 5, 2, 4))

    S.section('autotiles')
    kit.path(S, 'dune_field', dn[0], sand[0], 'ds2', 'ds2', 'ds4', 'sand', 'rippled dunes over sand', seed=3, amp=1.4)
    kit.path(S, 'hardpan_patch', pan[0], sand[0], 'ds1', 'ds2', 'ds4', 'sand', 'hard-pan over sand', seed=6,
             amp=1.0, inner_alt=pan[1])
    kit.path(S, 'scrub_patch', scrub, sand[0], 'ds2', 'ds2', 'cg2', 'sand', 'sedge over sand', seed=9, amp=1.4,
             attrs=['GRASS'])
    kit.water(S, OASIS, sand[0], 'ds1', 'ds2', 'sand', name='oasis', doc='turquoise oasis over sand')
    kit.cliffs(S, STRATA, 'st0', sand[0], sand[0], 'ds5', 'ds2', ['ds2', 'ds4'],
               ['ds5', 'ds4', 'st3', 'st2', 'st0', 'ds1'], stairs_roles=('st5', 'st4', 'st1', 'st0', 'st3'),
               lump=dict(rx=7.5, ry=2.6, sx=10, sy=4.2), doc_face='sandstone strata (>= 2 rows)')

    S.section('plants')
    S.object('palm', C.palm(['pl0', 'pl1', 'pl2', 'pl3'], 'pl0', ['k1', 'k2', 'k3'], 'k0', coconut=['k0', 'k1', 'k3']),
             top='XX/XX/..', solid='../../.X', doc='date palm 2x3')
    S.object('palm_small', C.palm(['pl0', 'pl1', 'pl2', 'pl3'], 'pl0', ['k1', 'k2', 'k3'], 'k0', w=16, h=32, lean=1),
             top='X/.', solid='./X', doc='young palm 1x2')
    S.object('saguaro', DS.saguaro(CACTUS, 'cg0', 'bn2'), top='X/.', solid='./X', doc='column cactus 1x2')
    S.object('saguaro_bloom', DS.saguaro(CACTUS, 'cg0', 'bn2', flower=('fp', 'fy')), top='X/.', solid='./X',
             doc='cactus in bloom 1x2')
    S.object('barrel_cactus', DS.barrel_cactus(CACTUS, 'cg0', 'bn2', flower=('fp', 'fy')), doc='barrel cactus')
    S.object('prickly_pear', DS.prickly_pear(CACTUS, 'cg0', 'fp'), doc='prickly pear')
    S.object('tumbleweed', DS.tumbleweed(['k1', 'k2', 'k3'], 'k0'), solid='.', doc='tumbleweed (decor)')
    S.object('dry_tuft', F.reeds(['ds1', 'ds2', 'ds4'], h=16, n=5), solid='.', doc='dry grass tuft')

    S.section('village')
    S.object('adobe_house', DS.adobe(64, 48, ADOBE, ['k1', 'k2'], ['k1', 'k2'], ['k0', 'cb1'], 'ad0', door_at=40,
                                     windows=[(8, 8)]), doc='adobe house 4x3', extra={'door': [2, 2]})
    S.object('adobe_large', DS.adobe(96, 64, ADOBE, ['k1', 'k2'], ['k1', 'k2'], ['k0', 'cb1'], 'ad0', door_at=48,
                                     windows=[(10, 8), (78, 8)], dome=True, awning=(34, 61, ['cl0', 'cl1', 'cl2'])),
             doc='domed adobe hall 6x4 (Cistern)', extra={'door': [3, 3]})
    S.object('adobe_hut', DS.adobe(48, 48, ADOBE, ['k1', 'k2'], ['k1', 'k2'], ['k0', 'cb1'], 'ad0', door_at=24),
             doc='adobe hut 3x3', extra={'door': [1, 2]})
    S.object('canopy_red', DS.canopy(['cl0', 'cl1', 'cl2'], WOOD, 'k0'), top='XXX/...', solid='.../X.X',
             doc='caravan canopy 3x2')
    S.object('canopy_blue', DS.canopy(['cb0', 'cb1', 'cb2'], WOOD, 'k0'), top='XXX/...', solid='.../X.X',
             doc='market canopy 3x2')
    S.object('jars', DS.jars(['ad0', 'ad1', 'ad2'], 'ad0', 'cl1'), doc='water jars')
    S.object('well', TP.well(['st1', 'st2', 'st3', 'st4'], WOOD, ['oa1', 'oa2'], 'k0', ['k1', 'k2', 'k3', 'k4']),
             top='XX/..', solid='../XX', doc='oasis well 2x2')
    S.object('crate', PR.crate(WOOD, 'k0'), doc='crate')
    S.object('sacks', TP.sacks(['ds1', 'ds3', 'ds4'], 'k0', 'k1'), doc='grain sacks')
    S.object('signpost', PR.signpost(WOOD, 'k0'), attrs=['SIGN'], doc='waypost')

    S.section('ruins')
    S.object('pillar', DS.pillar(STRATA, 'st0'), top='X/./.', solid='./X/X', doc='sandstone column 1x3')
    S.object('pillar_broken', DS.pillar(STRATA, 'st0', broken=True), top='X/./.', solid='./X/X',
             doc='broken column 1x3')
    S.object('obelisk', DS.obelisk(STRATA, 'st0', 'oa2'), top='X/X/.', solid='./X/X', doc='sun obelisk 1x3')
    S.object('skull', DS.skull(['ds1', 'bn1', 'bn2'], 'ds0'), solid='.', doc='bleached skull (decor)')
    S.object('mesa', PR.rock_column(STRATA, 'st0', w=48, h=48, seed=2, taper=0.15), top='XXX/XXX/...',
             solid='.../.../XXX', doc='mesa butte 3x3')
    kit.rocks(S, STRATA, 'st0')

    S.scene(sunwell_scene())
    return S


def sunwell_scene():
    sc = Scene('sunwell', 'Sunwell oasis (sample)', 36, 26, 'sand',
               doc='An oasis village: palms around the turquoise pool, adobe homes, canopies, '
                   'the domed Cistern, dunes, hard-pan and sandstone mesas with ruins.')
    L = {'.': 'sand', 'd': 'dune_field', 'h': 'hardpan_patch', ',': 'scrub_patch', '~': 'oasis', 'D': 'deep_oasis',
         '^': 'cliff_top', '#': 'cliff_face'}
    sc.rows('''
^^^^^^^^^^^^^^^^^^^^^dddddddddddddddd
^^^^^^^^^^^^^^^^^^^^ddddddddddddddddd
^^^^^^^^^^^^^^^^^^^ddddddddddddddddd.
##################..dddddddddddd.....
##################...ddddddd.........
.....................................
.....................................
...........hhhhhh....................
..........hhhhhhhh.........,,,.......
...........hhhhh..........,,,,,......
..........................,,,,.......
.................~~~~~...............
...............~~~~~~~~~.............
..............~~~~DDD~~~~............
..............~~~~DDD~~~~............
...............~~~~~~~~~.............
.................~~~~~...............
.....................................
..................................dd.
.......,,,......................dddd.
......,,,,,....................ddddd.
.......,,,....................dddddd.
.............................ddddddd.
dd..........................dddddddd.
ddd........................ddddddddd.
dddd......................dddddddddd.
''', L)
    obj = [('adobe_large', 3, 6), ('adobe_house', 26, 5), ('adobe_hut', 11, 19), ('adobe_house', 22, 18),
           ('canopy_red', 24, 11), ('canopy_blue', 8, 13), ('well', 27, 14), ('jars', 10, 16), ('jars', 30, 8),
           ('sacks', 12, 15), ('crate', 23, 13), ('palm', 13, 9), ('palm', 24, 15), ('palm_small', 19, 17),
           ('palm_small', 15, 16), ('saguaro', 33, 13), ('saguaro_bloom', 2, 17), ('barrel_cactus', 30, 20),
           ('prickly_pear', 5, 23), ('tumbleweed', 18, 22), ('pillar', 21, 0), ('pillar_broken', 23, 1),
           ('obelisk', 7, 0), ('skull', 33, 17), ('rock', 16, 5), ('mesa', 32, 0), ('signpost', 20, 6)]
    for (n, x, y) in obj:
        sc.put(n, x, y)
    sc.sprinkle(['dry_tuft', 'pebbles', 'tumbleweed', 'dry_tuft', 'barrel_cactus'], 18, on={'sand'}, seed=5)
    return sc
