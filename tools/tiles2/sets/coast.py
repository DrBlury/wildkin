"""COAST - beaches, harbours, fens, reefs and fjords.

Replaces the old `coast` tileset (Sea Route, Saltwind, Port Brine, Gull
Isle, Heron Fen, Reedwick, Coralhook Reef, Greywater Fjord, Tidal Temple
shore). Sand, surf and sea; blue-grey fjord rock; marsh water and mud for
the fens; docks, boats, a lighthouse and harbour buildings.
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
import coastart as C
import extras as X
import kit

PALETTE = PL.merge(PL.MEADOW, PL.LEAF, PL.BARK, PL.ROOF_RED, PL.ROOF_BLUE, PL.WALL_CREAM, PL.GLASS, {
    'sa0': '#6a4c34', 'sa1': '#a07c50', 'sa2': '#cca870', 'sa3': '#e4c890', 'sa4': '#f4e0b0', 'sa5': '#fcf4d8',
    'swet': '#b89464',
    'e0': '#10306c', 'e1': '#1c52a0', 'e2': '#2878c8', 'e3': '#40a0dc', 'e4': '#80d0ec', 'e5': '#e0f8ff',
    'mw0': '#1c3024', 'mw1': '#2c4434', 'mw2': '#3c5c40', 'mw3': '#5a7a50',
    'md0': '#3a2c24', 'md1': '#5a4434', 'md2': '#7a5e44', 'md3': '#9a7a58',
    'b0': '#1c2230', 'b1': '#343e50', 'b2': '#4e5c70', 'b3': '#6c7c90', 'b4': '#94a4b4', 'b5': '#c4ccd4',
    'co0': '#7c2848', 'co1': '#c84c6c', 'co2': '#f090a0',
    'sg1': '#5a8c4c', 'sg2': '#8cb45c', 'sg3': '#c0d884',
})
# Storm: the same harbour under heavy grey skies (Greywater, bad weather).
STORM = {'e1': '#1c3a5c', 'e2': '#2c5470', 'e3': '#3c6c84', 'e4': '#6a90a0', 'e5': '#b8ccd4',
         'sa2': '#a89478', 'sa3': '#bcaa8c', 'sa4': '#d0c0a4', 'sa5': '#e0d4c0',
         'g3': '#4c8450', 'g4': '#6c9c64', 'g5': '#8cb07c'}

BANKS = [
    ['sa0', 'sa1', 'sa2', 'sa3', 'sa4', 'sa5', 'swet', 'sg1', 'sg2', 'sg3', 'g1', 'g2', 'g3', 'g4', 'g5'],
    ['e0', 'e1', 'e2', 'e3', 'e4', 'e5', 'sa1', 'sa2', 'sa3', 'sa4', 'sa5', 'swet', 'b1', 'b3', 'b5'],
    ['g0', 'g1', 'g2', 'g3', 'g4', 'g5', 'md0', 'md1', 'md2', 'md3', 'mw0', 'mw1', 'mw2', 'mw3'],
    ['b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'g0', 'g1', 'g2', 'g3', 'g4', 'g5', 'e1', 'e2', 'e4'],
    ['k0', 'k1', 'k2', 'k3', 'k4', 'b1', 'b2', 'b3', 'b4', 'b5', 'e2', 'e3', 'sa4', 'co1', 'wl2'],
    ['ra0', 'ra1', 'ra2', 'ra3', 'ra4', 'k0', 'wl0', 'wl1', 'wl2', 'k1', 'k2', 'k3', 'gl0', 'gl1', 'gl2'],
    ['rb0', 'rb1', 'rb2', 'rb3', 'rb4', 'k0', 'wl0', 'wl1', 'wl2', 'k1', 'k2', 'k3', 'gl0', 'gl1', 'gl2'],
    ['t0', 't1', 't2', 't3', 't4', 't5', 'k0', 'k1', 'k2', 'k3', 'k4', 'co0', 'co1', 'co2', 'sa4'],
]

SAND = {'dk': 'sa1', 'mid': 'sa2', 'base': 'sa3', 'lt': 'sa4', 'hi': 'sa5'}
GRASS = {'dk': 'g1', 'mid': 'g2', 'base': 'g3', 'lt': 'g4', 'hi': 'g5', 'out': 'g0'}
DUNE = {'dk': 'sg1', 'mid': 'sg2', 'base': 'sa3', 'lt': 'sg3', 'hi': 'sa5'}
MUD = {'dk': 'md0', 'mid': 'md1', 'base': 'md2', 'lt': 'md3', 'hi': 'md3'}
SEA = {'deep': 'e1', 'base': 'e2', 'lt': 'e3', 'hi': 'e4', 'foam': 'e5', 'dark': 'e0'}
MARSH = {'deep': 'mw0', 'base': 'mw1', 'lt': 'mw2', 'hi': 'mw3', 'foam': 'g4', 'dark': 'mw0'}
ROCK = ['b1', 'b2', 'b3', 'b4', 'b5']
LEAF = ['t0', 't1', 't2', 't3', 't4', 't5']
WOOD = ['k1', 'k2', 'k3', 'k4']
TRIM = ['k1', 'k2', 'k3']
GLASS = ['gl0', 'gl1', 'gl2']


def st(roof, wall=('wl0', 'wl1', 'wl2')):
    return {'out': 'k0', 'roof': roof, 'wall': list(wall), 'trim': TRIM, 'glass': GLASS,
            'found': ['k1', wall[0], wall[1]], 'chimney': ['k1', wall[0], wall[1]]}


RED = st(['ra0', 'ra1', 'ra2', 'ra3', 'ra4'])
BLUE = st(['rb0', 'rb1', 'rb2', 'rb3', 'rb4'])


def build():
    S = Sheet('coast', 'Coast - beaches, harbours, fens, reefs', PALETTE, variants={'storm': STORM},
              banks=BANKS, doc=__doc__)
    S.section('ground')
    sand = kit.speckle_family(S, 'sand', SAND, doc='beach sand', dots=(10, 12, 8), pebbles=(1, 2, 1),
                              cracks=(0, 0, 0), grain=0.25)
    S.tile('sand_wet', P.speckle_ground(dict(SAND, base='swet', lt='sa3', mid='sa1'), 21, dots=8, pebbles=0),
           doc='damp sand at the tide line')
    grass = kit.grass_family(S, 'grass', GRASS, doc='coastal meadow / fen grass')
    dune = kit.grass_family(S, 'dune', DUNE, seeds=(31, 32, 33, 34), doc='marram-grass dune', tufts=(4, 6, 3, 5))
    mud = kit.speckle_family(S, 'mud', MUD, seeds=(41, 42, 43), doc='fen mud', dots=(10, 8, 6))

    S.section('water')
    fr = [C.surf_autotile(SEA, sand[0], 'swet', f) for f in range(4)]
    S.autotile('sea', fr[0], frames=fr, over='sand', attrs=['WATER'], period=18,
               doc='sea over sand: shallows and a foam line that washes up and back')
    D = dict(SEA, base='e1', deep='e0', lt='e2', hi='e3')
    dr = [T.material_autotile(T.water_surface(D, f, seed=5), T.water_surface(SEA, f), rim_in='e0', rim_out='e3',
                              seed=7, E=3.0, amp=1.2, dither=0.0) for f in range(4)]
    S.autotile('deep_sea', dr[0], frames=dr, over='sea', attrs=['WATER', 'DEEP'], period=18,
               doc='open sea (surf) inside sea')
    kit.water(S, MARSH, grass, 'g0', 'md1', 'grass', name='marsh', deep=False, doc='fen water over grass')
    kit.path(S, 'sand_patch', sand[0], grass, 'sa2', 'g2', 'sa4', 'grass', 'sand drift over grass',
             inner_alt=sand[1], seed=5, amp=1.3)
    kit.path(S, 'mud_patch', mud[0], grass, 'md1', 'g2', 'md3', 'grass', 'mud over grass', seed=9, amp=1.2)
    kit.path(S, 'dune_edge', dune, sand[0], 'sg1', 'sa2', 'sg3', 'sand', 'dune grass over sand', seed=13, amp=1.4)

    S.section('cliffs')
    kit.cliffs(S, ROCK, 'b0', grass, grass, 'g4', 'g2', ['g2', 'g4'], ['g5', 'g4', 'b3', 'b2', 'b0', 'g1'],
               stairs_roles=('b5', 'b4', 'b2', 'b0', 'b3'), lump=dict(rx=6.5, ry=3.6, sx=9, sy=5.5))
    S.object('sea_rock', PR.rock(16, 16, ROCK, 'b0', 3, parts=[(8, 10, 6.5, 4.5), (6, 7, 3.5, 2.8)]),
             doc='rock in the surf')
    S.object('sea_stack', PR.rock_column(ROCK, 'b0', seed=5),
             top='XX/../..', solid='../XX/XX', doc='sea stack 2x3')
    S.object('tide_pool', C.coral(['co0', 'co1', 'co2'], 'k0', kind='brain') , solid='.', doc='anemone in a tide pool')

    S.section('harbour')
    S.patch9('dock', PR.dock_block(WOOD, 'k0', 'k1'), layer='ground', doc='pier decking over water (floor)')
    S.object('bollard', PR.barrel(['b1', 'b2', 'b3', 'b4'], 'b0', 'b0'), doc='mooring bollard')
    S.object('rowboat', C.rowboat(WOOD, 'k0', 'k1'), solid='..', doc='moored rowboat 2x1 (on water)')
    S.object('fishing_boat', C.fishing_boat('rb2', 'rb1', WOOD, ['wl0', 'wl1', 'wl2'], 'k0'),
             top='XXX/.../...', solid='.../XXX/XXX', doc='fishing boat 3x3 (on water)')
    S.object('lighthouse', C.lighthouse(['wl0', 'wl1', 'wl2'], ['ra0', 'ra2', 'ra3'], ['gl0', 'gl1', 'gl2'],
                                        ['k1', 'wl0', 'wl1'], 'k0'),
             top='XX/XX/../../..', solid='../../XX/XX/XX', doc='lighthouse 2x5', extra={'door': [0, 4]})
    S.object('warehouse', B.house(96, 64, st(['ra0', 'ra1', 'ra2', 'ra3', 'ra4']), door_at=48, windows=[(8, 6), (76, 6)],
                                  roof_style='tile', siding='plank', door_w=18),
             doc='harbour warehouse 6x4', extra={'door': [3, 3]})
    S.object('harbour_house', B.house(80, 64, BLUE, door_at=24, windows=[(40, 5), (58, 5)], roof_style='slate',
                                      shutters=('rb1', 'rb2')),
             doc='harbour office 5x4', extra={'door': [1, 3]})
    S.object('cottage', B.house(64, 64, BLUE, door_at=40, windows=[(8, 5)], chimney=12, roof_style='slate',
                                siding='plank'), doc='fisher cottage 4x4', extra={'door': [2, 3]})
    S.object('stilt_hut', C.stilt_hut(WOOD, ['k1', 'k3', 'k4'], 'k0',
                                      ['gl0', 'gl1', 'gl2']),
             top='XXX/.../.../...', solid='.../XXX/XXX/...', doc='reed-thatch hut on stilts 3x4 (fens)',
             extra={'door': [1, 2]})
    S.object('fish_stall', TP.market_stall(TRIM, ['rb1', 'wl2', 'rb3'], [('rb1', 'rb3', 'wl2'), ('k1', 'k2', 'k3')], 'k0'),
             top='XXX/...', solid='.../XXX', doc='fish stall 3x2')
    S.object('crate', PR.crate(WOOD, 'k0'), doc='crate')
    S.object('barrel', PR.barrel(WOOD, 'b2', 'k0'), doc='barrel')
    S.object('nets', C.net_rack(WOOD, 'b4', 'k0'), top='XX/..', solid='../XX', doc='drying nets 2x2')
    S.object('lobster_pots', C.lobster_pots(WOOD, 'b4', 'k0'), doc='lobster pots')
    S.object('anchor', C.anchor(['b1', 'b2', 'b3'], 'b0'), doc='old anchor')
    bu = [C.buoy(['k1', 'co1', 'sa4'], ['k1', 'wl2', 'wl2'], 'k0', f)
          for f in range(2)]
    S.object('buoy', bu[0], frames=bu, period=30, doc='bobbing buoy (on water)')
    gl = [C.gull('wl2', 'b3', 'k0', f) for f in range(2)]
    S.object('gull', gl[0], frames=gl, period=40, solid='.', layer='top', doc='gull (perch on posts / roofs)')

    kit.civic(S, RED, ('wl2', 'ra4', 'ra2'), roof_style='tile', siding='plank', skip=('shop', 'hall'))
    kit.civic(S, BLUE, ('wl2', 'ra4', 'ra2'), roof_style='slate', siding='plaster', skip=('hearth_hall', 'inn'))
    S.object('cave_mouth', X.cave_mouth(ROCK, 'b0', 'b0'), top='XXX/.../...', solid='.../XXX/X.X',
             doc='sea cave entrance 3x3 (door bottom middle)', extra={'door': [1, 2]})
    S.object('lifebuoy', X.lifebuoy('ra2', 'wl2', 'k0'), doc='lifebuoy on a post')
    S.object('ferry_boat', X.ferry_boat(['rb0', 'rb1', 'rb2'], ['k1', 'k2', 'k3'], ['wl0', 'wl1', 'wl2'], 'k0'),
             top='XXXX/..../....', solid='..../XXXX/XXXX', doc='ferry 4x3 (on water)')
    S.object('salt_heap', X.salt_heap(['sa3', 'sa4', 'sa5'], 'sa1'), doc='salt heap 2x1')
    bb = [X.bell_buoy(['k1', 'co1', 'co1'], ['b1', 'b3', 'b4'], 'k0', f) for f in range(2)]
    S.object('bell_buoy', bb[0], frames=bb, period=30, top='X/.', solid='./X', doc='bell buoy 1x2 (on water)')
    S.object('shell_lamp', __import__('dungeonart').shell_lamp(['sa4', 'sa4', 'wl2'], ['e2', 'e3', 'wl2'],
                                                                ['k1', 'k2', 'k3'], 'k0'), top='X/.', solid='./X',
             doc='shell lamp 1x2')
    S.object('crab_shell', X.crab_shell(['co0', 'co1', 'co2'], 'k0'), solid='.', doc='crab shell (decor)')
    S.object('heron_statue', X.heron_statue(['b1', 'b2', 'b3', 'b4'], 'b0', ['b1', 'b2', 'b3']), top='X/.',
             solid='./X', doc='heron statue 1x2 (Heron Fen)')

    S.custom('fence', PR.fence_block(WOOD, 'k0'), 'fence', layer='mid', attrs=['SOLID'],
             doc='rail fence: row 0 [post][W end][mid][E end], row 1 [N end][mid][S end][gate]')
    S.object('signpost', PR.signpost(WOOD, 'k0'), attrs=['SIGN'], doc='sign')
    S.object('arrow_sign', PR.arrow_sign(WOOD, 'k0'), attrs=['SIGN'], doc='direction arrow')
    S.object('notice_board', PR.notice_board(WOOD, 'k0', 'wl2', 'wl0', 'ra2'), top='XX/..', solid='../XX',
             attrs=['SIGN'], doc='harbour notice board 2x2')
    S.object('small_flowers', X.small_flowers(['co1', 'co2', 'sa4'], 'k1'), solid='.', doc='sea pinks (decor)')
    S.object('trough', TP.trough(WOOD, ['b1', 'b2', 'b4'], 'k0'), doc='water trough 2x1')

    S.section('shore life')
    S.object('shells', C.shells(['k1', 'co1', 'co2'], 'k0', star=['k1', 'co1', 'co2']),
             solid='.', doc='shells and a starfish (decor)')
    S.object('driftwood', C.driftwood(WOOD, 'k0'), doc='driftwood 2x1')
    sw = [C.seaweed(['t0', 't2', 't4'], 't0', f) for f in range(3)]
    S.object('seaweed', sw[0], frames=sw, period=24, solid='.', doc='swaying kelp (shallows)')
    S.object('coral_branch', C.coral(['co0', 'co1', 'co2'], 'k0'), doc='branching coral')
    S.object('coral_brain', C.coral(['co0', 'co1', 'co2'], 'k0', kind='brain'), doc='brain coral')
    S.object('whale_arch', C.whale_arch(['b3', 'b4', 'b5'], 'b0'), top='XXX/.../...', solid='.../X.X/X.X',
             doc='whale-bone arch 3x3')
    S.object('palm', C.palm(['t0', 't2', 't3', 't5'], 't0', ['k1', 'k2', 'k3'], 'k0', coconut=['k0', 'k1', 'k3']),
             top='XX/XX/..', solid='../../.X', doc='palm 2x3')
    S.object('reeds', F.reeds(['g1', 'g2', 'g4'], h=16, heads=('md0', 'md1', 'md2')), solid='X', doc='bulrushes')
    S.object('lily_pads', F.lily_pad(['g1', 'g2', 'g4'], 'g1'), solid='.', doc='lily pads (marsh)')
    S.object('bush', F.bush(16, 16, LEAF, 't0', seed=1), doc='salt bush')
    kit.broadleaf(S, LEAF, 't0', ['k1', 'k2', 'k3'], 'k0', big=False, forest=True, doc='alder')

    S.scene(port_scene())
    return S


def port_scene():
    sc = Scene('port', 'Port Brine (sample)', 40, 30, 'sand',
               doc='A harbour town above a beach: piers into the sea, boats, a lighthouse on the '
                   'fjord headland, dunes, tide pools and a whale-bone arch.')
    L = {'.': 'sand', 'g': 'grass', '~': 'sea', 'D': 'deep_sea', 'd': 'dune_edge', 'p': 'sand_patch',
         '^': 'cliff_top', '#': 'cliff_face', 'k': 'dock', 'm': 'marsh', 'F': ('forest', 'over')}
    sc.rows('''
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
FgggggggggggggggggggggggggggggggggggFFFF
Fggggggggggggggggggggggggggggggggggggg^^
gggggggggggggggggggggggggggggggggggg^^^^
gggggggggggggggggggggggggggggggggggg^^^^
ggggggggggggggggggggggggggggggggggg^^^^^
gggggggggggggggggggggggggggggggggg^^^^^^
ggggggggggggggggggggggggggggggggggg#####
ggggggggggggggggggggggggggggggggggg#####
gggggggggggggggggggggggggggggggggggg~~~~
ggppppppppppppppppppppppgggggggggggg~~~~
gpp....................ppppppppppp..~~~~
dd........................................
dd.........................................
d...........................~~~~~~~~~~~~
.............~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.......~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.....~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
....~~~~~~~~~~DDDDDDDDDDDDDDDDDDDDDDDDDD
...~~~~~~~~~DDDDDDDDDDDDDDDDDDDDDDDDDDDDD
...~~~~~~~~DDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
..~~~~~~~~DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
..~~~~~~~DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
.~~~~~~~~DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
.~~~~~~~DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
~~~~~~~~DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
~~~~~~~DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
~~~~~~DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
~~~~~~DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
~~~~~DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
''', L)
    sc.join['sea'] = ('deep_sea',)
    # piers
    # piers sit on the mass layer over sand and sea
    for (x, y0, y1) in ((16, 12, 22), (17, 12, 22), (26, 11, 20), (27, 11, 20)):
        for y in range(y0, y1 + 1):
            sc.set(x, y, 'dock', 'over')
    obj = [('warehouse', 2, 4), ('harbour_house', 9, 4), ('cottage', 15, 4), ('cottage', 20, 4),
           ('lighthouse', 37, 0), ('fishing_boat', 19, 18), ('rowboat', 13, 17), ('rowboat', 28, 16),
           ('fish_stall', 24, 9), ('nets', 30, 8), ('crate', 18, 12), ('barrel', 19, 12), ('barrel', 25, 11),
           ('lobster_pots', 29, 11), ('anchor', 11, 11), ('bollard', 15, 14), ('bollard', 18, 20),
           ('bollard', 25, 13), ('buoy', 23, 23), ('buoy', 33, 21), ('gull', 15, 13), ('gull', 38, 6),
           ('whale_arch', 3, 11), ('shells', 8, 14), ('driftwood', 10, 13), ('palm', 32, 10),
           ('sea_rock', 6, 19), ('sea_rock', 36, 13), ('sea_stack', 34, 16), ('tide_pool', 2, 16),
           ('tree', 26, 1), ('tree_small', 31, 2), ('bush', 7, 9), ('bush', 22, 9), ('seaweed', 4, 18)]
    for (n, x, y) in obj:
        sc.put(n, x, y)
    sc.sprinkle(['shells', 'driftwood', 'crab_shell', 'shells'], 10, on={'sand'}, seed=2)
    sc.sprinkle(['small_flowers', 'bush'], 8, on={'grass'}, seed=6)
    return sc
