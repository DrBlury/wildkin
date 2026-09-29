"""GRIM - withered downs, ash fields and the lakeside town of Duskmere.

Replaces the old `grim` tileset (Hollow Downs, Ashen Fields, Duskmere,
Scorchwaste 2). Olive-grey withered grass, cold stone, slate roofs with
lamplit windows, the dark mere with mooring posts, barrows, standing
stones, gravestones and iron fences, wisps, pumpkins, a ruined windmill.
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
import gothart as GO
import extras as X
import kit

PALETTE = {
    'wg0': '#1c2020', 'wg1': '#343c30', 'wg2': '#4c5a3c', 'wg3': '#687448', 'wg4': '#88905c', 'wg5': '#aeac7c',
    'gp1': '#4c443c', 'gp2': '#6c6054', 'gp3': '#8c7e6c', 'gp4': '#aa9c88',
    'dm0': '#101826', 'dm1': '#1c2a3c', 'dm2': '#2c4054', 'dm3': '#48607a', 'dm4': '#7c94a8', 'dm5': '#b8c8d4',
    'gs0': '#1c1c24', 'gs1': '#34343e', 'gs2': '#4e4e5a', 'gs3': '#6c6c78', 'gs4': '#8e8e98', 'gs5': '#b4b4bc',
    'sl0': '#1c1a2c', 'sl1': '#2e2c44', 'sl2': '#44405c', 'sl3': '#5e5a78', 'sl4': '#7c7896',
    'wd0': '#241a18', 'wd1': '#443428', 'wd2': '#645038', 'wd3': '#846c4c',
    'ln0': '#c87028', 'ln1': '#f8c050', 'ln2': '#fff4b0',
    'pk0': '#8c3c14', 'pk1': '#d06420', 'pk2': '#f09848',
    'ws0': '#3c8cc8', 'ws1': '#b8f0ff', 'ws2': '#6cc8e8',
    'dl1': '#4c4a2c', 'dl2': '#6c6838', 'dl3': '#8c8448',
}
# Night: the same town after dark (windows and wisps carry the light).
NIGHT = {'wg2': '#2c3444', 'wg3': '#3c4454', 'wg4': '#4c5464', 'wg5': '#646c7c',
         'gp2': '#44404c', 'gp3': '#585460', 'gp4': '#6c6874', 'gs3': '#4c4c60', 'gs4': '#62627a', 'gs5': '#80809a'}

BANKS = [
    ['wg0', 'wg1', 'wg2', 'wg3', 'wg4', 'wg5', 'gp1', 'gp2', 'gp3', 'gp4', 'pk0', 'pk1', 'pk2', 'dl2', 'dl3'],
    ['dm0', 'dm1', 'dm2', 'dm3', 'dm4', 'dm5', 'wg0', 'wg1', 'wg2', 'wg3', 'wg4', 'wg5', 'ws0', 'ws1', 'ws2'],
    ['gs0', 'gs1', 'gs2', 'gs3', 'gs4', 'gs5', 'wg1', 'wg2', 'wg3', 'wg4', 'wg5', 'gp2', 'gp3'],
    ['sl0', 'sl1', 'sl2', 'sl3', 'sl4', 'gs0', 'gs1', 'gs2', 'gs3', 'wd0', 'wd1', 'wd2', 'ln0', 'ln1', 'ln2'],
    ['gs0', 'gs1', 'gs2', 'gs3', 'gs4', 'gs5', 'wd0', 'wd1', 'wd2', 'wd3', 'ln0', 'ln1', 'ln2', 'pk1', 'pk2'],
    ['wd0', 'wd1', 'wd2', 'wd3', 'dl1', 'dl2', 'dl3', 'wg0', 'wg1', 'wg2', 'wg3', 'ws0', 'ws1', 'ws2', 'gs3'],
]

GRASS = {'dk': 'wg1', 'mid': 'wg2', 'base': 'wg3', 'lt': 'wg4', 'hi': 'wg5', 'out': 'wg0'}
PATH = {'dk': 'gp1', 'mid': 'gp2', 'base': 'gp3', 'lt': 'gp4', 'hi': 'gp4'}
MERE = {'deep': 'dm1', 'base': 'dm2', 'lt': 'dm3', 'hi': 'dm4', 'foam': 'dm5', 'dark': 'dm0'}
STONE = ['gs1', 'gs2', 'gs3', 'gs4', 'gs5']
WOOD = ['wd0', 'wd1', 'wd2', 'wd3']
HOUSE = {'out': 'gs0', 'roof': ['sl0', 'sl1', 'sl2', 'sl3', 'sl4'], 'wall': ['gs1', 'gs2', 'gs3'],
         'trim': ['wd0', 'wd1', 'wd2'], 'glass': ['ln0', 'ln1', 'ln2'], 'found': ['gs0', 'gs1', 'gs2'],
         'chimney': ['gs0', 'gs1', 'gs2'], 'door': ['wd0', 'wd1', 'wd2']}


def build():
    S = Sheet('grim', 'Grim - withered downs, Duskmere', PALETTE, variants={'night': NIGHT}, banks=BANKS, doc=__doc__)
    S.section('ground')
    grass = kit.grass_family(S, 'grass', GRASS, doc='withered grass')
    path = kit.speckle_family(S, 'path', PATH, seeds=(5, 6, 7), doc='ashen path', dots=(9, 11, 7))
    S.tile('tallgrass', F.tallgrass(GRASS), attrs=['GRASS'], doc='dry tall grass (encounters)')
    S.object('tallgrass_top', F.tallgrass_top(GRASS), top='X', solid='.', layer='top', doc='blade tips over people')

    S.section('autotiles')
    kit.path(S, 'road', path[0], grass, 'gp1', 'wg1', 'gp4', 'grass', 'ashen road over grass', inner_alt=path[1])
    kit.path(S, 'tallgrass_patch', F.tallgrass(GRASS), grass, None, 'wg1', None, 'grass', 'dry tall grass patch',
             seed=4, E=3.0, attrs=['GRASS'])
    kit.water(S, MERE, grass, 'wg0', 'wg1', 'grass', name='mere', doc='the dark mere over grass')
    kit.cliffs(S, STONE, 'gs0', grass, grass, 'wg4', 'wg2', ['wg2', 'wg4'], ['wg5', 'wg4', 'gs3', 'gs2', 'gs0', 'wg1'],
               stairs_roles=('gs5', 'gs4', 'gs1', 'gs0', 'gs3'), lump=dict(rx=5.5, ry=4, sx=8, sy=6))

    S.section('town')
    S.object('cottage', B.house(64, 64, HOUSE, door_at=40, windows=[(8, 6)], chimney=12, roof_style='slate',
                                siding='stone'), doc='stone cottage 4x4', extra={'door': [2, 3]})
    S.object('house', B.house(80, 64, HOUSE, door_at=24, windows=[(40, 5), (58, 5)], roof_style='slate',
                              siding='stone', chimney=60), doc='stone house 5x4', extra={'door': [1, 3]})
    S.object('chapel', B.house(64, 80, HOUSE, door_at=32, windows=[(6, 10), (46, 10)], gable=True, siding='stone',
                               roof_style='slate', roof_h=44, door_w=12), doc='memorial chapel 4x5',
             extra={'door': [2, 4]})
    S.object('tall_house', B.house(96, 80, HOUSE, door_at=48, windows='auto', roof_style='slate', siding='stone',
                                   storeys=2, beams=True, chimney=72), doc='tall town house 6x5', extra={'door': [3, 4]})
    kit.civic(S, HOUSE, ('ln2', 'ln1', 'ln0'), roof_style='slate', siding='stone', skip=('hall',))
    S.object('apothecary', B.house(64, 80, HOUSE, door_at=24, windows=[(38, 8), (38, 26)], gable=True, siding='stone',
                                   roof_style='slate', roof_h=40, door_w=12), doc='apothecary 4x5',
             extra={'door': [1, 4]})
    S.object('crypt_hall', B.house(96, 96, HOUSE, door_at=48, windows=[(8, 12), (76, 12)], gable=True, siding='stone',
                                   roof_style='slate', roof_h=52, door_w=16), doc='crypt hall 6x6',
             extra={'door': [3, 5]})
    S.object('bone_gate', X.bone_gate(['gp2', 'gp4', 'wg5'], 'dm0', 'wg0'), top='XXX/.../...', solid='.../X.X/X.X',
             doc='bone gate 3x3 (walk through the middle)', extra={'door': [1, 2]})
    S.object('lamp', TP.lamp_post(['gs1', 'gs2', 'gs3'], 'gs0', ['ln0', 'ln1', 'ln2']), top='X/.', solid='./X',
             doc='street lamp 1x2')
    S.object('memorial', GO.memorial(['gs1', 'gs2', 'gs3'], ['ln1', 'ln2'], 'gs0'), top='X/.', solid='./X',
             doc='memorial lantern 1x2 (Duskmere custom)')
    S.object('bell', TP.bell_tower(['gs1', 'gs2', 'gs3'], ['wd0', 'wd1', 'wd2'], ['sl0', 'sl1', 'sl2', 'sl3'],
                                   ['gs2', 'gs4', 'gs5'], 'gs0'), top='XX/../../..', solid='../XX/XX/XX',
             doc='bell tower 2x4')
    S.object('mooring', PR.barrel(['wd0', 'wd1', 'wd2', 'wd3'], 'gs2', 'wd0'), doc='mooring post')
    S.patch9('dock', PR.dock_block(WOOD, 'wd0', 'wd0'), layer='ground', doc='jetty decking (floor)')
    S.object('rowboat', __import__('coastart').rowboat(WOOD, 'wd0', 'wd1'), solid='..', doc='rowboat 2x1')
    S.object('cart', TP.cart(WOOD, ['wd0', 'wd2'], 'wd0', load=[('pk0', 'pk1', 'pk2')]), doc='pumpkin cart 2x1')
    S.object('barrel', PR.barrel(WOOD, 'gs1', 'wd0'), doc='barrel')
    S.object('crate', PR.crate(WOOD, 'wd0'), doc='crate')
    S.object('signpost', PR.signpost(WOOD, 'wd0'), attrs=['SIGN'], doc='sign')

    S.section('graveyard')
    for k in ('round', 'cross', 'slab'):
        S.object('grave_' + k, GO.gravestone(['gs1', 'gs2', 'gs3'], 'gs0', k, moss='wg2'), doc='gravestone (%s)' % k)
    S.custom('iron_fence', GO.iron_fence(['gs0', 'gs1', 'gs3'], 'gs0'), 'fence', layer='mid', attrs=['SOLID'],
             doc='wrought-iron fence: row 0 [post][W end][mid][E end], row 1 [N end][mid][S end][gate]')
    ws = [GO.wisp(['ws0', 'ws1'], 'ws2', f) for f in range(4)]
    S.object('wisp', ws[0], frames=ws, period=12, solid='.', layer='top', doc='will-o\'-wisp (animated)')
    S.object('pumpkin', GO.pumpkin(['pk0', 'pk1', 'pk2'], 'wg2', 'wg0'), doc='pumpkin')
    S.object('lantern_pumpkin', GO.pumpkin(['pk0', 'pk1', 'pk2'], 'wg2', 'wg0', face='ln2'), doc='carved lantern')
    S.object('bones', __import__('caveart').bones(['gp2', 'gp4', 'wg5'], 'wg0'), solid='.', doc='bones (decor)')

    S.section('downs')
    S.object('barrow', GO.barrow(['wg1', 'wg2', 'wg3', 'wg4', 'wg5'], 'wg0', door=('gs0', 'dm0', 'gs3')),
             top='XXX/...', solid='.../X.X', doc='barrow mound 3x2 (door in the middle)', extra={'door': [1, 1]})
    S.object('ruined_windmill', GO.ruined_windmill(['gs1', 'gs2', 'gs3'], WOOD, 'gs0'), top='XXX/XXX/.../...',
             solid='.../.../XXX/XXX', doc='ruined windmill 3x4')
    S.object('twisted_tree', GO.twisted_tree(['wd1', 'wd2', 'wd3'], 'wd0', leaf=['dl1', 'dl2', 'dl3'], seed=3),
             top='XX/XX/..', solid='../../XX', doc='gnarled tree 2x3')
    S.object('dead_tree', F.dead_tree(32, 32, ['wd1', 'wd2', 'wd3'], 'wd0', seed=4), top='XX/..', solid='../XX',
             doc='bare tree 2x2')
    S.object('stump', F.stump(['wd1', 'wd2', 'wd3'], 'wd0', 'wd3', 'wd1'), doc='stump')
    S.object('shrub', F.bush(16, 16, ['wd0', 'dl1', 'dl2', 'dl3', 'wg4'], 'wd0', seed=5), doc='withered shrub')
    kit.rocks(S, STONE, 'gs0', moss=('wg2', 'wg3'))
    S.patch9('stone_wall', TP.stone_wall(['gs0', 'gs1', 'gs2', 'gs3', 'gs4'], 'gs0'), layer='mid', attrs=['SOLID'],
             doc='field wall')

    S.scene(duskmere_scene())
    return S


def duskmere_scene():
    sc = Scene('duskmere', 'Duskmere (sample)', 36, 26, 'grass',
               doc='A slate-roofed town on the dark mere: jetties and moored boats, memorial lanterns '
                   'along the shore, the chapel yard with graves and wisps, barrows and a ruined mill '
                   'on the downs.')
    L = {'.': 'grass', '=': 'road', '~': 'mere', 'D': 'deep_mere', ',': 'tallgrass_patch',
         '^': 'cliff_top', '#': 'cliff_face', 'W': ('stone_wall', 'over')}
    sc.rows('''
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
####################################
####################################
....................................
.......,,,,,..............,,,,......
......,,,,,,,............,,,,,,.....
...==================================
...=..........=..........=..........
...=..........=..........=..........
...=..........=..........=..........
...=..........=..........=..........
...=====================================
...=.........................=......
...=..WWWWWWWW...............=......
...=..W......W...............=......
...=..W......W...............=......
...=..WWW..WWW...............=......
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~=~~~~~~
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
~~~~~~~~DDDDDDDDDDDDDDDDDDDDDDDDDD~~
~~~~~~DDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
~~~~~DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
~~~~DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
~~~~DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD
''', L)
    for y in range(19, 23):
        sc.set(29, y, 'dock', 'over')
        sc.set(30, y, 'dock', 'over')
    obj = [('barrow', 2, 1), ('barrow', 12, 0), ('ruined_windmill', 29, 0), ('standing_stone', 22, 1),
           ('tall_house', 4, 3), ('chapel', 16, 4), ('house', 26, 5), ('cottage', 31, 8),
           ('lamp', 13, 12), ('lamp', 24, 12), ('memorial', 2, 17), ('memorial', 11, 17), ('memorial', 20, 17),
           ('memorial', 26, 17), ('grave_round', 7, 15), ('grave_cross', 9, 15), ('grave_slab', 11, 16),
           ('grave_round', 8, 17), ('wisp', 10, 16), ('wisp', 33, 14), ('pumpkin', 15, 15), ('lantern_pumpkin', 16, 16),
           ('cart', 21, 14), ('twisted_tree', 33, 15), ('dead_tree', 0, 9), ('stump', 22, 10), ('shrub', 18, 10),
           ('mooring', 28, 18), ('rowboat', 31, 20), ('rowboat', 26, 21), ('barrel', 27, 14), ('crate', 28, 14),
           ('signpost', 4, 13), ('rock', 1, 6)]
    for (n, x, y) in obj:
        sc.put(n, x, y)
    sc.sprinkle(['shrub', 'pebbles', 'stump', 'pebbles'], 14, on={'grass'}, seed=5)
    return sc
