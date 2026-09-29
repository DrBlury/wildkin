"""CAVE - caverns, mines, grottoes and root tunnels.

Replaces the old `cave` tileset (Glimmer Caverns 1/2, Copper Mine, Storm
Cave, Starfall, Karst Chamber, Mill Cellar, Rootways, Sporelight Hollow,
Tidal Underflow). Walls are raised rock masses (cliff_top + cliff_face
over the floor), chasms drop into darkness, and crystals / glowcaps give
the dark levels points of light.
"""

from core import Img
from sheet import Sheet, Scene
import palettes as PL
import paint as P
import terrain as T
import flora as F
import props as PR
import caveart as CA
import extras as X
import kit

PALETTE = PL.merge(PL.BARK, {
    'cf0': '#1e1a24', 'cf1': '#3a3038', 'cf2': '#56484a', 'cf3': '#72605a', 'cf4': '#907a6c', 'cf5': '#b09a84',
    'cr0': '#141420', 'cr1': '#2a2838', 'cr2': '#443e52', 'cr3': '#5e5670', 'cr4': '#7c7490', 'cr5': '#a49cb4',
    'v0': '#08080c',
    'uw0': '#0c2434', 'uw1': '#14405a', 'uw2': '#1c6078', 'uw3': '#3a8ca0', 'uw4': '#80c8d0', 'uw5': '#d0f4f4',
    'cy0': '#2c2c7c', 'cy1': '#5454c8', 'cy2': '#8c8cf0', 'cy3': '#e0e0ff',
    'am0': '#4c1c5c', 'am1': '#8c3ca4', 'am2': '#c47ce0', 'am3': '#f4d4ff',
    'gc1': '#1c8c8c', 'gc2': '#4cd4c4', 'gc3': '#b8fff0',
    'co0': '#8c4424', 'co1': '#d07034', 'co2': '#f8b060',
    'rt0': '#3a2a20', 'rt1': '#5c4430', 'rt2': '#86684a',
    'ms1': '#2c5c4c', 'ms2': '#448c64',
    'bn0': '#8c8474', 'bn1': '#c4bca8', 'bn2': '#ece4d0',
    'fo': '#f09040', 'fy': '#f8d030',
})
# Deeper levels: colder, darker rock (Storm Cave, Starfall).
DEEP = {'cf2': '#403c50', 'cf3': '#56506a', 'cf4': '#6c6888', 'cf5': '#8c88a8',
        'cr2': '#343454', 'cr3': '#46466c', 'cr4': '#5c5c88', 'cr5': '#8080b0'}

BANKS = [
    ['cf0', 'cf1', 'cf2', 'cf3', 'cf4', 'cf5', 'cr0', 'cr1', 'cr2', 'ms1', 'ms2', 'bn0', 'bn1', 'bn2', 'v0'],
    ['cr0', 'cr1', 'cr2', 'cr3', 'cr4', 'cr5', 'cf1', 'cf2', 'cf3', 'cf4', 'cf5', 'v0'],
    ['uw0', 'uw1', 'uw2', 'uw3', 'uw4', 'uw5', 'cf1', 'cf2', 'cf3', 'cf4', 'cf5', 'cr0', 'cr1', 'cr2'],
    ['cy0', 'cy1', 'cy2', 'cy3', 'am0', 'am1', 'am2', 'am3', 'gc1', 'gc2', 'gc3', 'cr0', 'cr1', 'cr2', 'cr3'],
    ['k0', 'k1', 'k2', 'k3', 'k4', 'cr0', 'cr1', 'cr2', 'cr3', 'cr4', 'co0', 'co1', 'co2', 'fo', 'fy'],
    ['rt0', 'rt1', 'rt2', 'ms1', 'ms2', 'cf0', 'cf1', 'cf2', 'cf3', 'bn0', 'bn1', 'bn2', 'k0', 'k1', 'k2'],
]

FLOOR = {'dk': 'cf1', 'mid': 'cf2', 'base': 'cf3', 'lt': 'cf4', 'hi': 'cf5'}
ROCK = ['cr1', 'cr2', 'cr3', 'cr4', 'cr5']
WATER = {'deep': 'uw1', 'base': 'uw2', 'lt': 'uw3', 'hi': 'uw4', 'foam': 'uw5', 'dark': 'uw0'}
WOOD = ['k1', 'k2', 'k3', 'k4']


def build():
    S = Sheet('cave', 'Cave - caverns, mines, grottoes', PALETTE, variants={'deep': DEEP}, banks=BANKS, doc=__doc__)
    S.section('ground')
    floor = kit.speckle_family(S, 'floor', FLOOR, seeds=(3, 4, 5, 6), doc='cave floor', dots=(9, 12, 7, 10),
                               pebbles=(2, 3, 1, 2), cracks=(0, 1, 0, 1), weights=(6, 3, 2, 2))
    rocktop = T.lump_texture(['cr0', 'cr1', 'cr2', 'cr3'], 16, 16, 7, rx=3.4, ry=2.8, sx=5.3, sy=4.0, bias=-0.1)
    S.tile('rock_top', rocktop, attrs=['SOLID'], doc='top of a rock mass (unwalkable)')
    moss = P.speckle_ground({'dk': 'cf1', 'mid': 'ms1', 'base': 'cf2', 'lt': 'ms2', 'hi': 'ms2'}, 31, dots=14)
    S.tile('floor_moss', moss, doc='mossy floor (Sporelight / Rootways)')

    S.section('walls and pits')
    kit.cliffs(S, ROCK, 'cr0', rocktop, floor[0], 'cr3', None, None, ['cr4', 'cf4', 'cr3', 'cr2', 'cr0', 'cf1'],
               stairs_roles=('cf5', 'cf4', 'cf1', 'cr0', 'cf2'), lump=dict(rx=5.5, ry=4.0, sx=8, sy=6),
               doc_face='cave wall face (>= 2 rows)')
    S.autotile('chasm', CA.chasm_autotile(floor[0], 'v0', 'cf1', ['cr0', 'cr1', 'cr2', 'cr3']), over='floor',
               attrs=['SOLID'], doc='drop into darkness (the far wall shows on the north side)')
    kit.water(S, WATER, floor[0], 'cf0', 'cf2', 'floor', name='pool', doc='underground pool')
    kit.path(S, 'moss_patch', moss, floor[0], 'cf2', 'cf2', 'ms2', 'floor', 'moss creeping over rock', seed=6,
             amp=1.3)
    S.object('ladder_up', CA.ladder(WOOD, 'k0'), attrs=['EXIT'], layer='mid', solid='.',
             doc='ladder up (exit)')
    S.object('ladder_down', CA.ladder(WOOD, 'k0', hole=('v0', 'cf0'), down=True), attrs=['EXIT'], solid='.',
             doc='hole with ladder down (exit)')
    S.object('rope_bridge', CA.rope_bridge(WOOD, 'rt2', 'k0'), floor='XXX/XXX', solid='.../...',
             doc='rope bridge over a chasm 3x2')

    S.section('minerals and life')
    cr = [CA.crystal(['cy0', 'cy1', 'cy2', 'cy3'], 'cr0', f) for f in range(3)]
    S.object('crystal', cr[0], frames=cr, period=20, doc='glowing crystal cluster (animated glint)')
    am = [CA.crystal(['am0', 'am1', 'am2', 'am3'], 'cr0', f, seed=3) for f in range(3)]
    S.object('amethyst', am[0], frames=am, period=24, doc='amethyst cluster')
    import snowart as SN
    S.object('crystal_pillar', SN.ice_crystal(['cy0', 'cy1', 'cy2', 'cy3'], 'cr0'), top='X/.', solid='./X',
             doc='crystal pillar 1x2')
    gc = [CA.glowcaps(['gc1', 'gc1', 'gc2'], 'cr3', 'gc3', 'cr0', f) for f in range(2)]
    S.object('glowcaps', gc[0], frames=gc, period=30, solid='.', doc='glowcap mushrooms (pulse)')
    S.object('stalagmite', CA.stalagmite(['cr1', 'cr2', 'cr3', 'cr4'], 'cr0'), top='X/.', solid='./X',
             doc='stalagmite 1x2')
    S.object('ore_copper', CA.ore_rock(ROCK, ['co0', 'co1', 'co2'], 'cr0', 3), doc='copper ore (mine)')
    S.object('roots', CA.hanging_roots(['rt0', 'rt1', 'rt2'], 'k0'), solid='.', layer='top',
             doc='hanging roots (over a wall lip)')
    S.object('bones', CA.bones(['bn0', 'bn1', 'bn2'], 'cf0'), solid='.', doc='old bones (decor)')
    kit.rocks(S, ROCK, 'cr0')

    S.object('crack', X.crack(['cr0', 'cr1', 'cr3'], 'v0', 'cr0'), solid='./.', attrs=['EXIT'],
             doc='squeeze-through fissure 1x2 (set into a wall face)')
    S.object('stairs_down', __import__('interiorart').stairs_in(['cf1', 'cf3', 'cf4'], 'cr0', down=True),
             attrs=['EXIT'], solid='./.', doc='rock steps down 1x2 (exit)')
    S.object('stairs_up', __import__('interiorart').stairs_in(['cf1', 'cf3', 'cf4'], 'cr0'), attrs=['EXIT'],
             solid='./.', doc='rock steps up 1x2 (exit)')
    S.object('moonbeam', X.light_shaft(['cy2', 'cy3']), solid='./.', layer='top',
             doc='moonlight through a ceiling crack 1x2 (top layer)')
    S.object('moth_dais', X.moth_dais(['cr1', 'cr2', 'cr3'], ['cy2', 'cy3'], 'cr0'), solid='../..',
             doc='moth dais 2x2 (Starfall)')
    S.object('fungal_shelf', X.fungal_shelf(['gc1', 'gc1', 'gc2'], 'cr3', 'cr0'), solid='.',
             doc='bracket fungi on a wall')

    S.section('mine')
    S.custom('rails', CA.rails_block(['cr1', 'cr2', 'cr4'], WOOD, 'k0'), 'rails', layer='mid',
             doc='mine rails: row 0 [E-W][N-S][curve S-E][curve S-W], row 1 [curve N-E][curve N-W][buffer][cross]')
    S.object('mine_cart', CA.mine_cart(['cr1', 'cr2', 'cr4'], 'cr0', ore=['co0', 'co1', 'co2']), doc='ore cart')
    S.object('timber_frame', CA.timber_frame(WOOD, 'k0'), top='XXX/.../...', solid='.../X.X/X.X',
             doc='tunnel support 3x3 (walk under)')
    lt = [CA.lantern_hook(['cr1', 'cr2', 'cr4'], ['fo', 'fo', 'fy'], 'k0', f) for f in range(2)]
    S.object('lantern', lt[0], frames=lt, period=20, solid='.', doc='hanging lantern (flicker)')
    S.object('crate', PR.crate(WOOD, 'k0'), doc='supply crate')
    S.object('barrel', PR.barrel(WOOD, 'cr2', 'k0'), doc='barrel')
    S.object('signpost', PR.signpost(WOOD, 'k0'), attrs=['SIGN'], doc='mine sign')

    S.scene(cave_scene())
    return S


def cave_scene():
    sc = Scene('glimmer', 'Glimmer Caverns (sample)', 36, 26, 'floor',
               doc='Rock masses with lit faces, a chasm crossed by a rope bridge, an underground '
                   'pool, crystal and glowcap pockets and a mine gallery with rails.')
    L = {'.': 'floor', '^': 'cliff_top', '#': 'cliff_face', 'c': 'chasm', '~': 'pool', 'D': 'deep_pool',
         'm': 'moss_patch'}
    sc.rows('''
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^##########^^^^^^^^^^^^^^
^^^^^^^^^^^^##########^^^^^^^^^^^^^^
^^^###########........##########^^^^
^^^###########..................^^^^
^^^.............................####
^^^.....................mmmm....####
^^^^^^...........~~~~...mmmmm......^
^^^^^^^.........~~~~~~~..mmm.......^
######^.........~~DD~~~............^
######^..........~~~~~.............^
......^^^...........................
......###...........................
..........cccccccccccccc............
..........cccccccccccccc.......^^^^^
.............ccccccccc.........#####
...............................#####
^^^^...........................^^^^^
####...........................#####
####...........................#####
.........mmm........................
........mmmm........................
..........m.........................
....................................
''', L)
    obj = [('rope_bridge', 15, 15), ('crystal', 30, 9), ('crystal', 33, 12), ('amethyst', 26, 10),
           ('crystal_pillar', 31, 7), ('glowcaps', 25, 8), ('glowcaps', 27, 9), ('glowcaps', 9, 22),
           ('stalagmite', 4, 7), ('stalagmite', 14, 6), ('stalagmite', 22, 12), ('ladder_up', 18, 5),
           ('ladder_down', 34, 24), ('timber_frame', 2, 15), ('mine_cart', 6, 18), ('crate', 1, 17),
           ('barrel', 1, 18), ('lantern', 3, 14), ('ore_copper', 7, 16), ('ore_copper', 8, 17), ('bones', 20, 20),
           ('boulder', 12, 19), ('rock', 25, 22), ('rock_cracked', 28, 18), ('signpost', 12, 13),
           ('stairs', 32, 17), ('roots', 24, 5)]
    for i in range(0, 8):
        sc.put('rails:0,0', i, 18)
    sc.put('rails:2,0', 8, 18)
    for (n, x, y) in obj:
        sc.put(n, x, y)
    sc.sprinkle(['pebbles', 'bones', 'glowcaps', 'pebbles', 'rock'], 16, on={'floor'}, seed=5)
    return sc
