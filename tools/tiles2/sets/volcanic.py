"""VOLCANIC - calderas, ash fields, forges and the railway.

Replaces the old `volcanic` tileset (Caldera, Cindermoor, Cinder Crossing,
Cinder Road, Ember Tunnel/Span, Railhead + shaft, Scorchwaste 1, Forge,
Anvil Hall, Cooling Chamber). Ash ground, basalt cliffs, flowing lava
with a crust rim, fumaroles, obsidian, charred trees, a ballast railway,
brick forge buildings with smoking stacks.
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
import caveart as CA
import fireart as FI
import extras as X
import kit

PALETTE = PL.merge(PL.BARK, PL.BRICK, {
    'a0': '#2a2226', 'a1': '#4a3c3c', 'a2': '#6a5850', 'a3': '#8a7466', 'a4': '#a8927e', 'a5': '#c8b29a',
    'bs0': '#141018', 'bs1': '#28202a', 'bs2': '#3e3240', 'bs3': '#584858', 'bs4': '#766474', 'bs5': '#9a8898',
    'lv0': '#6c1414', 'lv1': '#b42c14', 'lv2': '#e85c1c', 'lv3': '#f8a030', 'lv4': '#fff080',
    'ob0': '#1c1428', 'ob1': '#3c2c5c', 'ob2': '#7c64b4',
    'su1': '#c8b030', 'su2': '#f0e070',
    'sm0': '#5c5460', 'sm1': '#8c8490', 'sm2': '#bcb4bc',
    'sl0': '#2c3444', 'sl1': '#48546a', 'sl2': '#6a788c', 'sl3': '#94a0b0',
    'gw0': '#8c4c1c', 'gw1': '#f0a838', 'gw2': '#fff0a0',
    'sc1': '#5a5a3c', 'sc2': '#7c7c4c',
})
# Eruption: everything glows redder, ash darker (event maps).
ERUPT = {'a2': '#5a3c38', 'a3': '#744c40', 'a4': '#945c48', 'a5': '#b47458',
         'bs3': '#5c3040', 'bs4': '#7c4050', 'sm1': '#8c5c50', 'sm2': '#c08870'}

BANKS = [
    ['a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'bs0', 'bs1', 'bs2', 'sc1', 'sc2', 'su1', 'su2', 'lv2', 'lv3'],
    ['lv0', 'lv1', 'lv2', 'lv3', 'lv4', 'bs0', 'bs1', 'bs2', 'a1', 'a2', 'a3', 'a4', 'a5'],
    ['bs0', 'bs1', 'bs2', 'bs3', 'bs4', 'bs5', 'a1', 'a2', 'a3', 'a4', 'a5', 'lv2', 'lv3', 'lv4'],
    ['ob0', 'ob1', 'ob2', 'bs0', 'bs1', 'bs2', 'bs3', 'bs4', 'sm0', 'sm1', 'sm2', 'lv1', 'lv2', 'lv3', 'lv4'],
    ['bk0', 'bk1', 'bk2', 'sl0', 'sl1', 'sl2', 'sl3', 'k0', 'k1', 'k2', 'k3', 'gw0', 'gw1', 'gw2', 'bs0'],
    ['k0', 'k1', 'k2', 'k3', 'k4', 'sl0', 'sl1', 'sl2', 'sl3', 'a2', 'a3', 'a4', 'lv2', 'lv3', 'lv4'],
]

ASH = {'dk': 'a1', 'mid': 'a2', 'base': 'a3', 'lt': 'a4', 'hi': 'a5'}
BASALT = ['bs1', 'bs2', 'bs3', 'bs4', 'bs5']
LAVA = ['lv0', 'lv1', 'lv2', 'lv3', 'lv4']
WOOD = ['k1', 'k2', 'k3', 'k4']
METAL = ['sl0', 'sl1', 'sl3']
FORGE = {'out': 'bs0', 'roof': ['sl0', 'sl1', 'sl2', 'sl3', 'sl3'], 'wall': ['bk0', 'bk1', 'bk2'],
         'trim': ['k0', 'k1', 'k2'], 'glass': ['gw0', 'gw1', 'gw2'], 'found': ['bs0', 'bk0', 'bk1'],
         'chimney': ['bk0', 'bk1', 'bk2'], 'door': ['k0', 'k1', 'k2']}


def build():
    S = Sheet('volcanic', 'Volcanic - calderas, forges, railway', PALETTE, variants={'eruption': ERUPT},
              banks=BANKS, doc=__doc__)
    S.section('ground')
    ash = kit.speckle_family(S, 'ash', ASH, seeds=(3, 4, 5), doc='ash', dots=(10, 12, 8), pebbles=(2, 2, 1),
                             grain=0.2)
    scorch = kit.grass_family(S, 'scorch', {'dk': 'a1', 'mid': 'sc1', 'base': 'a3', 'lt': 'sc2', 'hi': 'a4',
                                            'out': 'a0'}, seeds=(11, 12, 13, 14), doc='scorched scrub (encounters)',
                              attrs=['GRASS'], tufts=(4, 6, 3, 5))
    S.tile('sulfur', P.speckle_ground({'dk': 'a2', 'mid': 'su1', 'base': 'a4', 'lt': 'su2', 'hi': 'su2'}, 17,
                                      dots=14, pebbles=0), doc='sulfur crust')
    crust = FI.lava_surface(['bs0', 'bs1', 'bs2', 'lv1', 'lv2'], 0, seed=4)
    S.tile('crust', crust, doc='cooling crust (walkable, hot)')

    S.section('lava and rock')
    fr = [FI.lava_autotile(LAVA, ash[0], ['bs0', 'bs1'], f) for f in range(4)]
    S.autotile('lava', fr[0], frames=fr, over='ash', attrs=['SOLID'], period=14,
               doc='flowing lava over ash (animated)')
    kit.path(S, 'crust_patch', crust, ash[0], 'bs1', 'a2', 'bs2', 'ash', 'cooled flow over ash', seed=5, amp=1.2)
    kit.path(S, 'scorch_patch', scorch, ash[0], 'a2', 'a2', 'sc2', 'ash', 'scrub over ash', seed=8, amp=1.3,
             attrs=['GRASS'])
    kit.cliffs(S, BASALT, 'bs0', ash[0], ash[0], 'a5', 'a2', ['a2', 'a4'], ['a5', 'a4', 'bs3', 'bs2', 'bs0', 'a1'],
               stairs_roles=('a5', 'a4', 'bs1', 'bs0', 'a3'), lump=dict(rx=4.5, ry=5.5, sx=7, sy=8))
    vt = [FI.vent(['bs0', 'bs1', 'bs3'], ['sm1', 'sm2'], 'bs0', f) for f in range(4)]
    S.object('vent', vt[0], frames=vt, period=10, top='X/.', solid='./X', doc='steam vent 1x2 (animated)')
    er = [FI.ember_rock(BASALT, ['lv1', 'lv2', 'lv4'], 'bs0', f) for f in range(3)]
    S.object('ember_rock', er[0], frames=er, period=18, doc='basalt with glowing cracks')
    S.object('obsidian', PR.rock(16, 16, ['ob0', 'ob1', 'ob2', 'bs4'], 'bs0', 7,
                                 parts=[(8, 10, 6, 4.5), (6, 7, 3.2, 3)]), doc='obsidian shard')
    S.object('cinder_cone', FI.cinder_cone(BASALT, ['lv1', 'lv3'], 'bs0'), top='XX/..',
             solid='../XX', doc='cinder cone 2x2')
    kit.rocks(S, BASALT, 'bs0')
    S.object('charred_tree', F.dead_tree(32, 48, ['bs1', 'bs2', 'bs3'], 'bs0', seed=2), top='XX/XX/..',
             solid='../../XX', doc='charred tree 2x3')
    S.object('charred_small', F.dead_tree(16, 32, ['bs1', 'bs2', 'bs3'], 'bs0', seed=5), top='X/.', solid='./X',
             doc='charred sapling 1x2')

    S.section('railway')
    S.custom('railway', FI.railway_block(['a1', 'a2', 'a3'], WOOD, METAL, 'k0'), 'railway',
             doc='ballast track: row 0 [E-W][N-S][W end][E end], row 1 [N end][S end][cross][buffer]')
    S.object('water_tower', FI.water_tower(WOOD, METAL, None, 'k0'), top='XX/XX/../..', solid='../../XX/XX',
             doc='locomotive water tower 2x4')
    S.object('coal_pile', FI.coal_pile(['bs0', 'bs1', 'bs3'], 'bs0'), doc='coal heap 2x1')
    S.object('mine_cart', CA.mine_cart(METAL, 'k0', ore=['bs0', 'bs1', 'bs3']), doc='coal tub')
    S.object('signal', TP.lamp_post(METAL, 'k0', ['lv1', 'lv2', 'lv4']), top='X/.', solid='./X',
             doc='rail signal lamp 1x2')

    S.section('forge town')
    S.object('forge', B.house(96, 80, FORGE, door_at=48, windows=[(8, 6), (76, 6)], siding='brick', roof_style='slate',
                              storeys=2, door_w=18, chimney=12), doc='forge hall 6x5', extra={'door': [3, 4]})
    S.object('depot', B.house(80, 64, FORGE, door_at=24, windows=[(40, 5), (58, 5)], siding='brick',
                              roof_style='slate'), doc='rail depot 5x4', extra={'door': [1, 3]})
    S.object('bunkhouse', B.house(64, 64, dict(FORGE, wall=['k1', 'k2', 'k3']), door_at=40, windows=[(8, 6)],
                                  siding='plank', roof_style='slate', chimney=12), doc='bunkhouse 4x4',
             extra={'door': [2, 3]})
    S.object('smokestack', FI.smokestack(['bk0', 'bk1', 'bk2'], METAL, 'bs0'), top='X/X/.', solid='./X/X',
             doc='smokestack 1x3 (pair with smoke)')
    sm = [FI.smoke(['sm1', 'sm2'], f) for f in range(4)]
    S.object('smoke', sm[0], frames=sm, period=10, solid='./.', layer='top', doc='drifting smoke 1x2 (animated)')
    bz = [FI.brazier(METAL, ['lv1', 'lv3', 'lv4'], 'bs0', f) for f in range(3)]
    S.object('brazier', bz[0], frames=bz, period=8, top='X/.', solid='./X', doc='brazier 1x2 (animated)')
    S.object('anvil', FI.anvil(METAL, ['bs1', 'bs2', 'bs3'], 'bs0'), doc='anvil')
    S.object('salamander_statue', FI.salamander_statue(BASALT, 'bs0', 'lv3', ['bs1', 'bs2', 'bs3']),
             top='XX/../..', solid='../XX/XX', doc='salamander kin statue 2x3')
    kit.civic(S, FORGE, ('gw2', 'gw1', 'gw0'), roof_style='slate', siding='brick')
    S.object('house_rust', B.house(64, 64, dict(FORGE, roof=['bs0', 'bk0', 'bk1', 'bk2', 'bk2']), door_at=40,
                                   windows=[(8, 6)], siding='plank', roof_style='tile'),
             doc='rust-roofed house 4x4', extra={'door': [2, 3]})
    S.object('anvil_hall', B.house(112, 80, FORGE, door_at=56, windows='auto', siding='stone', roof_style='slate',
                                   storeys=2, door_w=20, chimney=90), doc='Anvil Hall 7x5', extra={'door': [3, 4]})
    S.object('cave_mouth', X.cave_mouth(BASALT, 'bs0', 'bs0'), top='XXX/.../...', solid='.../XXX/X.X',
             doc='cave mouth 3x3', extra={'door': [1, 2]})
    S.object('tunnel_arch', X.tunnel_arch(['bk0', 'bk1', 'bk2'], 'bs0', 'bs0'), top='XXX/.../...',
             solid='.../XXX/X.X', doc='brick tunnel arch 3x3 (railway / Ember Tunnel)', extra={'door': [1, 2]})
    fu = [X.furnace(['bk0', 'bk1'], ['lv1', 'lv3', 'lv4'], METAL, 'bs0', f) for f in range(3)]
    S.object('furnace', fu[0], frames=fu, period=8, top='XX/..', solid='../XX', doc='furnace 2x2 (animated)')
    S.object('big_bell', X.big_bell(['sl0', 'sl1', 'sl2', 'sl3'], ['k0', 'k1', 'k2'], 'bs0'), top='XX/XX/..', solid='../../XX',
             doc='great bell 2x3')
    S.object('tool_rack', X.tool_rack(['k1', 'k2', 'k3'], METAL, 'k0'), top='XX/..', solid='../XX', doc='tool rack 2x2')
    S.object('hall_banner', __import__('dungeonart').banner(['lv0', 'lv1', 'lv2'], ['k1', 'k2', 'k3'], 'lv4', 'bs0'),
             solid='./.', doc='hall banner 1x2')
    S.object('crate', PR.crate(WOOD, 'k0'), doc='crate')
    S.object('barrel', PR.barrel(WOOD, 'sl1', 'k0'), doc='barrel')
    S.object('signpost', PR.signpost(WOOD, 'k0'), attrs=['SIGN'], doc='sign')
    S.custom('fence', PR.fence_block(WOOD, 'k0'), 'fence', layer='mid', attrs=['SOLID'], doc='rail fence')

    S.scene(caldera_scene())
    return S


def caldera_scene():
    sc = Scene('caldera', 'Cinder Road and Caldera rim (sample)', 38, 26, 'ash',
               doc='A railway town on the ash plain beside a lava river crossed by a stone causeway; '
                   'basalt cliffs, fumaroles, charred trees and obsidian.')
    L = {'.': 'ash', 'L': 'lava', 'c': 'crust_patch', 's': 'scorch_patch', '^': 'cliff_top', '#': 'cliff_face'}
    sc.rows('''
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
######################^^^^^^^^^^^^^^^^
######################################
......................################
.......................................
.......................................
.............ccc.......................
........LLLLLLLLLL.....................
.......LLLLLLLLLLLLL.......ssss........
......LLLLLLLLLLLLLLL.....ssssss.......
.......LLLLLLL.LLLLLL......ssss........
.........LLLL...LLLL...................
..........LL.....LLLccc................
..........LL......LLLLc................
..........LL.......LLLLLL..............
.........LLL........LLLLLLL............
........LLLL.........LLLLLLL...........
.......LLLL...........LLLLLLL..........
......LLLL.............LLLLLLL.........
.....LLLLc..............LLLLLL.........
....LLLLcc...............LLLL..........
....LLLL...........ss.....LL...........
...LLLL...........ssss....LL...........
...LLL.............ss.....LL...........
''', L)
    # the causeway: crust over the river
    for y in range(12, 14):
        sc.set(14, y, 'crust')
    for x in range(0, 38):
        sc.put('railway:0,0', x, 7)
    obj = [('forge', 26, 0), ('depot', 3, 1), ('bunkhouse', 10, 1), ('smokestack', 24, 0), ('smoke', 24, -1),
           ('water_tower', 33, 2), ('coal_pile', 18, 5), ('mine_cart', 21, 6), ('signal', 16, 5),
           ('brazier', 22, 3), ('anvil', 31, 5), ('salamander_statue', 29, 8), ('vent', 4, 15), ('vent', 30, 18),
           ('ember_rock', 20, 20), ('obsidian', 12, 21), ('obsidian', 33, 13), ('cinder_cone', 34, 21),
           ('charred_tree', 1, 5), ('charred_small', 22, 11), ('charred_tree', 17, 20), ('rock_big', 29, 13),
           ('boulder', 7, 20), ('signpost', 14, 11), ('crate', 20, 5), ('barrel', 19, 6)]
    for (n, x, y) in obj:
        sc.put(n, x, y)
    sc.sprinkle(['pebbles', 'obsidian', 'ember_rock', 'pebbles', 'rock'], 16, on={'ash'}, seed=5)
    return sc
