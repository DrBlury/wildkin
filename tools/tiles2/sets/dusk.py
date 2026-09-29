"""DUSK - Gravewood, the haunted forest.

Replaces the old `dusk` tileset (Gravewood and its views). A purple-tinged
forest floor with fallen leaves, bog pools, gnarled trees and a dense
twisted-wood mass, glowing toadstools, drifting fog and wisps, old graves,
iron fences and a mausoleum.
"""

from core import Img
from sheet import Sheet, Scene
import paint as P
import terrain as T
import flora as F
import props as PR
import townprops as TP
import gothart as GO
import extras as X
import buildings as B
import caveart as CA
import kit

PALETTE = {
    'fl0': '#140e1a', 'fl1': '#241a2a', 'fl2': '#34283a', 'fl3': '#48384a', 'fl4': '#5e4c5a', 'fl5': '#7a6670',
    'lf1': '#6c3024', 'lf2': '#9c4c2c', 'lf3': '#c47438',
    'bg0': '#0a100c', 'bg1': '#142018', 'bg2': '#1e3024', 'bg3': '#2c4430', 'bg4': '#46603e', 'bg5': '#7c9064',
    'tv0': '#0c0a14', 'tv1': '#1c1628', 'tv2': '#2c223c', 'tv3': '#3e3252', 'tv4': '#54466c', 'tv5': '#72628c',
    'bk0': '#120c10', 'bk1': '#2a1e20', 'bk2': '#44302c', 'bk3': '#604638',
    'gs0': '#141420', 'gs1': '#2c2c3a', 'gs2': '#464656', 'gs3': '#646474', 'gs4': '#8a8a9a',
    'tc0': '#4c1c6c', 'tc1': '#8c3cb4', 'tc2': '#d488f0', 'tc3': '#f8e0ff',
    'ws0': '#3cb4a0', 'ws1': '#c0fff0', 'ws2': '#6ce0c8',
    'fg0': '#6c6a84', 'fg1': '#9c9ab4',
    'ln0': '#c87028', 'ln1': '#f8c050',
}
MOON = {'fl3': '#3c4058', 'fl4': '#4e5470', 'fl5': '#6a7090', 'tv4': '#444c74', 'tv5': '#5c6890'}

STYLE = {'out': 'gs0', 'roof': ['tv1', 'tv2', 'tv3', 'tv4', 'tv5'], 'wall': ['gs1', 'gs2', 'gs3'],
         'trim': ['bk0', 'bk1', 'bk2'], 'glass': ['bk0', 'ln0', 'ln1'], 'found': ['gs0', 'gs1', 'gs2'],
         'chimney': ['gs0', 'gs1', 'gs2'], 'door': ['bk0', 'bk1', 'bk2']}

BANKS = [
    ['fl0', 'fl1', 'fl2', 'fl3', 'fl4', 'fl5', 'lf1', 'lf2', 'lf3', 'tc0', 'tc1', 'tc2', 'tc3', 'bg3', 'bg4'],
    ['bg0', 'bg1', 'bg2', 'bg3', 'bg4', 'bg5', 'fl0', 'fl1', 'fl2', 'fl3', 'fl4', 'fl5', 'ws0', 'ws1', 'ws2'],
    ['tv0', 'tv1', 'tv2', 'tv3', 'tv4', 'tv5', 'bk0', 'bk1', 'bk2', 'bk3', 'tc1', 'tc2', 'fg0', 'fg1'],
    ['gs0', 'gs1', 'gs2', 'gs3', 'gs4', 'fl1', 'fl2', 'fl3', 'fl4', 'fl5', 'bk0', 'bk1', 'bk2', 'ln0', 'ln1'],
    ['ws0', 'ws1', 'ws2', 'fg0', 'fg1', 'tc0', 'tc1', 'tc2', 'tc3', 'gs0', 'gs1', 'gs2', 'bk1', 'bk2', 'bk3'],
    ['tv1', 'tv2', 'tv3', 'tv4', 'tv5', 'gs0', 'gs1', 'gs2', 'gs3', 'bk0', 'bk1', 'bk2', 'ln0', 'ln1'],
]

FLOOR = {'dk': 'fl1', 'mid': 'fl2', 'base': 'fl3', 'lt': 'fl4', 'hi': 'fl5', 'out': 'fl0'}
BOG = {'deep': 'bg1', 'base': 'bg2', 'lt': 'bg3', 'hi': 'bg4', 'foam': 'bg5', 'dark': 'bg0'}
LEAF = ['tv0', 'tv1', 'tv2', 'tv3', 'tv4', 'tv5']
BARK = ['bk1', 'bk2', 'bk3']
STONE = ['gs1', 'gs2', 'gs3', 'gs4', 'gs4']


def leafy(R, seed):
    img = P.grass(R, seed, tufts=3, flecks=2)
    for i, (x, y) in enumerate(P.scatter(14, 14, 4, seed + 3, margin=1, min_dist=4)):
        c = ('lf1', 'lf2', 'lf3')[i % 3]
        img.set(x, y, c)
        img.set(x + 1, y, c)
        img.set(x + 1, y + 1, 'lf1')
    return img


def build():
    S = Sheet('dusk', 'Dusk - Gravewood haunted forest', PALETTE, variants={'moonlit': MOON}, banks=BANKS, doc=__doc__)
    S.section('ground')
    floor = kit.grass_family(S, 'floor', FLOOR, seeds=(1, 2, 3, 4), doc='dark forest floor')
    S.tile('leaves', leafy(FLOOR, 7), group='floor', weight=3, doc='fallen leaves')
    S.tile('leaves_b', leafy(FLOOR, 8), group='floor', weight=2)
    tg = F.tallgrass({'out': 'fl0', 'dk': 'fl1', 'mid': 'fl2', 'base': 'fl3', 'lt': 'fl4', 'hi': 'fl5'})
    S.tile('bramble', tg, attrs=['GRASS'], doc='brambles (encounters)')

    S.section('autotiles')
    kit.path(S, 'trail', P.speckle_ground({'dk': 'fl1', 'mid': 'fl3', 'base': 'fl4', 'lt': 'fl5', 'hi': 'fl5'}, 11),
             floor, 'fl2', 'fl1', 'fl5', 'floor', 'worn trail over the floor')
    kit.path(S, 'bramble_patch', tg, floor, None, 'fl1', None, 'floor', 'bramble thicket', seed=4, E=3.0,
             attrs=['GRASS'])
    kit.water(S, BOG, floor, 'fl0', 'fl1', 'floor', name='bog', doc='bog pool over the floor')
    kit.cliffs(S, STONE, 'gs0', floor, floor, 'fl5', 'fl3', ['fl2', 'fl4'], ['fl5', 'fl4', 'gs3', 'gs2', 'gs0', 'fl1'],
               stairs_roles=('gs4', 'gs3', 'gs1', 'gs0', 'gs2'))
    S.patch9('forest', F.forest_wall(LEAF, 'tv0', BARK, 'bk0', seed=6, r=7.0), layer='mid', attrs=['SOLID'],
             doc='gnarled wood mass (trunks on the south edge)')

    S.section('trees')
    S.object('twisted_tree', GO.twisted_tree(BARK, 'bk0', leaf=['tv2', 'tv3', 'tv4'], seed=3), top='XX/XX/..',
             solid='../../XX', doc='gnarled tree 2x3')
    S.object('twisted_tree_b', GO.twisted_tree(BARK, 'bk0', leaf=['tv2', 'tv3', 'tv4'], seed=8), top='XX/XX/..',
             solid='../../XX')
    S.object('dead_tree', F.dead_tree(32, 32, BARK, 'bk0', seed=4), top='XX/..', solid='../XX', doc='dead tree 2x2')
    S.object('tree', F.round_tree('mid', LEAF, 'tv0', BARK, 'bk0', seed=3), top='XX/..', solid='../XX',
             doc='dark oak 2x2')
    S.object('stump', F.stump(BARK, 'bk0', 'bk3', 'bk1'), doc='stump')
    S.object('log', F.log_h(['bk1', 'bk2', 'bk3', 'bk3'], 'bk0', 'bk3', 'bk1', moss=('bg3', 'bg4')), doc='rotting log 2x1')
    S.object('shrub', F.bush(16, 16, LEAF, 'tv0', seed=5), doc='dark shrub')

    S.section('eerie')
    tc = [__import__('caveart').glowcaps(['tc0', 'tc1', 'tc2'], 'fl4', 'tc3', 'fl0', f) for f in range(2)]
    S.object('toadstools', tc[0], frames=tc, period=30, solid='.', doc='glowing toadstools (pulse)')
    S.object('toadstool_ring', F.mushrooms('tc1', 'tc0', 'tc3', 'fl5', 'fl0'), solid='.', doc='toadstool ring')
    ws = [GO.wisp(['ws0', 'ws1'], 'ws2', f) for f in range(4)]
    S.object('wisp', ws[0], frames=ws, period=12, solid='.', layer='top', doc='wisp (animated)')
    fg = [GO.fog(['fg0', 'fg1'], f) for f in range(4)]
    S.object('fog', fg[0], frames=fg, period=16, solid='.', layer='top', doc='drifting fog overlay (tile it)')
    for k in ('round', 'cross', 'slab'):
        S.object('grave_' + k, GO.gravestone(['gs1', 'gs2', 'gs3'], 'gs0', k, moss='bg3'), doc='old grave (%s)' % k)
    S.custom('iron_fence', GO.iron_fence(['gs0', 'gs1', 'gs3'], 'gs0'), 'fence', layer='mid', attrs=['SOLID'],
             doc='wrought-iron fence')
    S.object('mausoleum', GO.mausoleum(['gs1', 'gs2', 'gs3', 'gs4'], ['gs1', 'gs2', 'gs3'], ['bk0', 'bk1'], 'gs0'),
             top='XXX/.../...', solid='.../XXX/XXX', doc='mausoleum 3x3', extra={'door': [1, 2]})
    S.section('buildings')
    S.object('house', B.house(64, 64, STYLE, door_at=40, windows=[(8, 6)], chimney=12, roof_style='slate',
                              siding='stone'), doc='stone house 4x4', extra={'door': [2, 3]})
    kit.civic(S, STYLE, ('ln1', 'ln0', 'bk2'), roof_style='slate', siding='stone', skip=('hall',))
    S.object('apothecary', B.house(64, 80, STYLE, door_at=24, windows=[(38, 8), (38, 26)], gable=True,
                                   siding='stone', roof_style='slate', roof_h=40, door_w=12), doc='apothecary 4x5',
             extra={'door': [1, 4]})
    S.object('crypt_hall', B.house(96, 96, STYLE, door_at=48, windows=[(8, 12), (76, 12)], gable=True,
                                   siding='stone', roof_style='slate', roof_h=52, door_w=16), doc='crypt hall 6x6',
             extra={'door': [3, 5]})
    S.object('bone_gate', X.bone_gate(['fl4', 'fl5', 'gs4'], 'fl0', 'fl0'), top='XXX/.../...', solid='.../X.X/X.X',
             doc='bone gate 3x3', extra={'door': [1, 2]})
    S.object('lantern', TP.lamp_post(['gs1', 'gs2', 'gs3'], 'gs0', ['ln0', 'ln0', 'ln1']), top='X/.', solid='./X',
             doc='lantern post')
    S.object('bell', TP.bell_tower(['gs1', 'gs2', 'gs3'], ['bk0', 'bk1', 'bk2'], ['tv1', 'tv2', 'tv3', 'tv4'],
                                   ['gs2', 'gs3', 'gs4'], 'gs0'), top='XX/../../..', solid='../XX/XX/XX',
             doc='bell tower 2x4')
    S.object('cart', TP.cart(['bk0', 'bk1', 'bk2', 'bk3'], ['bk0', 'bk2'], 'bk0', load=[('lf1', 'lf2', 'lf3')]),
             doc='old cart 2x1')
    S.object('memorial', GO.memorial(['gs1', 'gs2', 'gs3'], ['ln0', 'ln1'], 'gs0'), top='X/.', solid='./X',
             doc='memorial lantern 1x2')
    S.object('mooring', PR.barrel(['bk0', 'bk1', 'bk2', 'bk3'], 'gs2', 'bk0'), doc='mooring post')
    S.object('pumpkin', GO.pumpkin(['lf1', 'lf2', 'lf3'], 'bg3', 'fl0', face='ln1'), doc='carved pumpkin')
    S.object('bones', CA.bones(['fl4', 'fl5', 'gs4'], 'fl0'), solid='.', doc='bones')
    S.object('signpost', PR.signpost(['bk0', 'bk1', 'bk2', 'bk3'], 'bk0'), attrs=['SIGN'], doc='crooked sign')
    kit.rocks(S, STONE, 'gs0', moss=('bg3', 'bg4'))

    S.scene(gravewood_scene())
    return S


def gravewood_scene():
    sc = Scene('gravewood', 'Gravewood (sample)', 36, 26, 'floor',
               doc='A winding trail through gnarled woods to a fenced graveyard and mausoleum; bog '
                   'pools, glowing toadstools, wisps and fog.')
    L = {'.': 'floor', '=': 'trail', '~': 'bog', 'D': 'deep_bog', ',': 'bramble_patch',
         'F': ('forest', 'over')}
    sc.rows('''
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
FFFFFFFFFFFFFFF==FFFFFFFFFFFFFFFFFFF
FFFFFFFF.......==.......FFFFFFFFFFFF
FFFFF..........==..........FFFFFFFFF
FFF.....,,,,....==............FFFFFF
FF.....,,,,,,....==.............FFFF
FF......,,,,......==.............FFF
F..................==.............FF
F...~~~~............==.............F
F..~~~~~~............==............F
F..~~DD~~~............===..........F
F...~~~~~...............==.........F
F....~~~.................==........F
F..........................==......F
F...........................==.....F
F............................==....F
F.......,,,,..................==...F
F......,,,,,,..................=...F
FF......,,,,...................=..FF
FFF............................=.FFF
FFFFF..........................=FFFF
FFFFFFFF.......................FFFFF
FFFFFFFFFFFF..................FFFFFF
FFFFFFFFFFFFFFFFFF.........FFFFFFFFF
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
''', L)
    obj = [('mausoleum', 20, 13), ('grave_round', 17, 15), ('grave_cross', 18, 17), ('grave_slab', 24, 17),
           ('grave_round', 25, 15), ('grave_cross', 16, 18), ('lantern', 22, 11), ('wisp', 14, 12), ('wisp', 27, 8),
           ('wisp', 6, 14), ('toadstools', 11, 7), ('toadstools', 29, 19), ('toadstool_ring', 9, 20),
           ('twisted_tree', 12, 3), ('twisted_tree_b', 26, 3), ('dead_tree', 4, 16), ('tree', 30, 11),
           ('stump', 9, 12), ('log', 13, 19), ('shrub', 7, 5), ('bones', 21, 20), ('signpost', 18, 5),
           ('rock', 3, 12), ('rock_big', 31, 15)]
    for x in range(15, 27):
        if x not in (19, 22):
            sc.put('iron_fence:2,0', x, 12)
    for y in range(13, 20):
        sc.put('iron_fence:1,1', 14, y)
        sc.put('iron_fence:1,1', 27, y)
    for (n, x, y) in obj:
        sc.put(n, x, y)
    for (x, y) in ((5, 8), (6, 8), (7, 9), (10, 21), (11, 21), (20, 6), (21, 6)):
        sc.put('fog', x, y)
    sc.sprinkle(['toadstools', 'stump', 'bones', 'shrub', 'toadstool_ring'], 14, on={'floor'},
                seed=5)
    return sc
