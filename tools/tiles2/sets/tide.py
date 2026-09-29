"""TIDE - the drowned Tidal Temple and its halls.

Replaces the old `tide` tileset (Tidal Temple shore/hall/dark, Current
Hall, Drowned Bell, Reed Tunnel). Wet blue-green masonry, barnacled floor
slabs, tide pools, current floors that carry you (animated chevrons in
four directions), coral pillars, kelp, the drowned bell, shell lamps and a
whale carving.
"""

from core import Img
from sheet import Sheet, Scene
import paint as P
import terrain as T
import flora as F
import props as PR
import caveart as CA
import coastart as C
import dungeonart as DG
import kit

PALETTE = {
    'ts0': '#08141c', 'ts1': '#142834', 'ts2': '#203c48', 'ts3': '#30545c', 'ts4': '#487070', 'ts5': '#6c9088',
    'tf0': '#0c1a20', 'tf1': '#1a2e34', 'tf2': '#284448', 'tf3': '#3a5a5a', 'tf4': '#527470',
    'tw0': '#0a2440', 'tw1': '#10406a', 'tw2': '#185c8c', 'tw3': '#2c84b0', 'tw4': '#64b8d8', 'tw5': '#c0ecf4',
    'co0': '#6c2440', 'co1': '#b44868', 'co2': '#ec8ca0', 'gc': '#8cf0e0',
    'kp0': '#1c3424', 'kp1': '#2c5434', 'kp2': '#467c44',
    'br0': '#5c4c2c', 'br1': '#9c7c40', 'br2': '#d4b064', 'br3': '#f4e0a0',
    'sh0': '#8c7c74', 'sh1': '#d4c4b4', 'sh2': '#fcf4e8',
    'v0': '#04080c',
}
BIOLUME = {'ts3': '#1c4c5c', 'ts4': '#246c78', 'ts5': '#34949c', 'tf3': '#1c4c54', 'tf4': '#2c6c70'}

BANKS = [
    ['tf0', 'tf1', 'tf2', 'tf3', 'tf4', 'ts0', 'ts1', 'ts2', 'kp0', 'kp1', 'kp2', 'sh0', 'sh1', 'sh2', 'v0'],
    ['ts0', 'ts1', 'ts2', 'ts3', 'ts4', 'ts5', 'tf1', 'tf2', 'tf3', 'tf4', 'kp1', 'kp2', 'v0'],
    ['tw0', 'tw1', 'tw2', 'tw3', 'tw4', 'tw5', 'tf0', 'tf1', 'tf2', 'tf3', 'tf4'],
    ['co0', 'co1', 'co2', 'gc', 'kp0', 'kp1', 'kp2', 'ts0', 'ts1', 'ts2', 'ts3', 'tw3', 'tw4', 'tw5'],
    ['br0', 'br1', 'br2', 'br3', 'sh0', 'sh1', 'sh2', 'ts0', 'ts1', 'ts2', 'ts3', 'ts4', 'gc', 'tw4', 'tw5'],
]

FLOOR = ['tf1', 'tf2', 'tf3', 'tf4']
MASON = ['ts1', 'ts2', 'ts3', 'ts4']
STONE = ['ts1', 'ts2', 'ts3', 'ts4', 'ts5']
WATER = {'deep': 'tw1', 'base': 'tw2', 'lt': 'tw3', 'hi': 'tw4', 'foam': 'tw5', 'dark': 'tw0'}


def barnacled(seed):
    img = DG.floor_slabs(FLOOR, seed=seed)
    for i, (x, y) in enumerate(P.scatter(14, 14, 4, seed + 5, margin=1, min_dist=4)):
        img.set(x, y, 'sh1')
        img.set(x + 1, y, 'sh0')
        if i % 2:
            img.set(x, y + 1, 'kp1')
    return img


def build():
    S = Sheet('tide', 'Tide - the drowned temple', PALETTE, variants={'biolume': BIOLUME}, banks=BANKS, doc=__doc__)
    S.section('floors')
    slabs = DG.floor_slabs(FLOOR)
    S.tile('floor', slabs, group='floor', weight=6, doc='wet slabs')
    S.tile('floor_barnacles', barnacled(2), group='floor', weight=2, doc='barnacled slabs')
    S.tile('floor_kelp', F.flower_patch(slabs, 'kp2', 'kp1', 'kp2', 'kp0', kind='star', seed=1), group='floor',
           weight=1, doc='kelp-grown slabs')
    top = T.lump_texture(['ts0', 'ts0', 'ts1', 'ts2'], 16, 16, 5, rx=3.5, ry=2.6, sx=5.3, sy=4, bias=-0.2)
    S.tile('wall_top', top, attrs=['SOLID'], doc='top of a wall mass')
    for d in 'NESW':
        fr = [DG.current_floor(['tw1', 'tw2', 'tw3', 'tw4'], f, d) for f in range(4)]
        S.tile('current_' + d.lower(), fr[0], frames=fr, period=6, attrs=['WATER', 'CURRENT'],
               doc='current carrying you %s' % {'N': 'north', 'E': 'east', 'S': 'south', 'W': 'west'}[d],
               extra={'dir': d})

    S.section('walls and water')
    kit.cliffs(S, STONE, 'ts0', top, slabs, 'ts2', None, None, ['ts3', 'tf4', 'ts3', 'ts2', 'ts0', 'tf1'],
               stairs_roles=('tf4', 'tf3', 'tf1', 'ts0', 'tf2'), face_tex=DG.masonry(MASON, seed=1),
               face_tex2=DG.masonry(MASON, seed=2), doc_face='temple wall face (>= 2 rows)')
    kit.water(S, WATER, slabs, 'tf0', 'tf1', 'floor', name='pool', doc='flooded channel over slabs')
    S.autotile('abyss', CA.chasm_autotile(slabs, 'v0', 'tf1', ['ts0', 'ts1', 'ts2', 'ts3']), over='floor',
               attrs=['SOLID'], doc='drop into the dark water below')

    S.section('temple')
    S.object('drowned_bell', DG.bell(['br0', 'br1', 'br2', 'br3'], 'ts0'), top='XX/..', solid='../XX',
             doc='the drowned bell 2x2')
    S.object('coral_pillar', PR.rock_column(['co0', 'co1', 'co1', 'co2', 'co2'], 'ts0', w=16, h=48, seed=3,
                                            taper=0.1), top='X/./.', solid='./X/X', doc='coral-crusted pillar 1x3')
    S.object('column', __import__('desertart').pillar(STONE, 'ts0'), top='X/./.', solid='./X/X', doc='temple column 1x3')
    S.object('shell_lamp', DG.shell_lamp(['sh0', 'sh1', 'sh2'], ['gc', 'tw4', 'tw5'], ['br0', 'br1', 'br2'], 'ts0'),
             top='X/.', solid='./X', doc='shell lamp 1x2')
    gc = [CA.crystal(['co0', 'co1', 'co2', 'gc'], 'ts0', f) for f in range(3)]
    S.object('glow_coral', gc[0], frames=gc, period=20, doc='glowing coral (animated)')
    S.object('coral_branch', C.coral(['co0', 'co1', 'co2'], 'ts0'), doc='branch coral')
    S.object('coral_brain', C.coral(['co0', 'co1', 'co2'], 'ts0', kind='brain'), doc='brain coral')
    kw = [C.seaweed(['kp0', 'kp1', 'kp2'], 'kp0', f) for f in range(3)]
    S.object('kelp', kw[0], frames=kw, period=24, solid='.', doc='swaying kelp')
    S.object('shells', C.shells(['sh0', 'sh1', 'sh2'], 'ts0', star=['co0', 'co1', 'co2']), solid='.', doc='shells')
    S.object('urn', DG.urn(['ts1', 'ts3', 'ts4'], 'ts0', band='br2'), doc='sunken urn')
    S.object('chains', DG.chains(['ts1', 'ts3', 'ts4'], 'ts0'), solid='./.', doc='anchor chains 1x2')
    S.object('whale_carving', C.whale_arch(['ts3', 'ts4', 'ts5'], 'ts0'), top='XXX/.../...', solid='.../X.X/X.X',
             doc='whale-bone gate 3x3')
    S.object('statue', __import__('townprops').statue(STONE, 'ts0', ['ts1', 'ts2', 'ts3']), top='XX/../..',
             solid='../XX/XX', doc='tide-warden statue 2x3')
    S.object('plaque', PR.signpost(['br0', 'br1', 'br2', 'br3'], 'ts0'), attrs=['SIGN'], doc='bronze plaque')
    kit.rocks(S, STONE, 'ts0', moss=('kp1', 'kp2'))

    S.scene(temple_scene())
    return S


def temple_scene():
    sc = Scene('current_hall', 'Current Hall (sample)', 30, 22, 'floor',
               doc='A flooded temple hall: channels, current floors that sweep you around the drowned '
                   'bell, coral pillars, glowing coral and shell lamps.')
    L = {'.': 'floor', '^': 'cliff_top', '#': 'cliff_face', '~': 'pool', 'a': 'abyss',
         'n': 'current_n', 'e': 'current_e', 's': 'current_s', 'w': 'current_w'}
    sc.rows('''
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
##############################
##############################
..............................
...eeeeeeeeeeeeeeeeeeeeeeee...
...n......................s...
...n.....~~~~~~~~~~~......s...
...n.....~~~~~~~~~~~......s...
...n.....~~~~~~~~~~~......s...
...n.....~~~~~~~~~~~......s...
...n......................s...
...wwwwwwwwwwwwwwwwwwwwwwwws...
..............................
^^^^^^^^.............^^^^^^^^^
########.............#########
########.............#########
.............aaaa.............
............aaaaaa............
.............aaaa.............
..............................
..............................
''', L)
    obj = [('drowned_bell', 14, 7), ('coral_pillar', 1, 4), ('coral_pillar', 28, 4), ('column', 8, 13),
           ('column', 21, 13), ('shell_lamp', 6, 18), ('shell_lamp', 23, 18), ('glow_coral', 2, 17),
           ('glow_coral', 27, 19), ('coral_branch', 4, 20), ('coral_brain', 25, 17), ('kelp', 9, 11), ('kelp', 20, 7),
           ('shells', 11, 20), ('urn', 18, 20), ('chains', 5, 2), ('chains', 24, 2), ('statue', 1, 18),
           ('plaque', 15, 13), ('whale_carving', 13, 1)]
    for (n, x, y) in obj:
        sc.put(n, x, y)
    sc.sprinkle(['shells', 'kelp', 'pebbles'], 8, on={'floor'}, seed=5)
    return sc
