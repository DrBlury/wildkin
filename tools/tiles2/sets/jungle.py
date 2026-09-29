"""JUNGLE - rainforest, river gorges, root villages and overgrown ruins.

Replaces the old `jungle` tileset (Rootcoil Jungle, Canopy Hearth, Canopy
Lodge approach) and serves Elderwood's deep groves. Deep green loam, mud,
a teal river, buttress giants, broad-leaf understorey, bamboo, hanging
vines, orchids, woven stilt homes and mossy temple ruins.
"""

from core import Img
from sheet import Sheet, Scene
import palettes as PL
import paint as P
import terrain as T
import flora as F
import props as PR
import townprops as TP
import caveart as CA
import jungleart as J
import kit

PALETTE = PL.merge(PL.BARK, {
    'jg0': '#0c2418', 'jg1': '#163c20', 'jg2': '#22582a', 'jg3': '#327434', 'jg4': '#4c9440', 'jg5': '#7cbc54',
    'jl0': '#082018', 'jl1': '#103828', 'jl2': '#1c5434', 'jl3': '#2c7440', 'jl4': '#48984c', 'jl5': '#80c460',
    'md0': '#2a1c14', 'md1': '#46301c', 'md2': '#624428', 'md3': '#7e5c38',
    'jr0': '#0c3434', 'jr1': '#145454', 'jr2': '#207470', 'jr3': '#3c9c8c', 'jr4': '#7cccb4', 'jr5': '#d0f4e4',
    'ms0': '#3c4c3c', 'ms1': '#5c6c54', 'ms2': '#7c8c6c', 'ms3': '#a4ac8c',
    'wv0': '#5c3c1c', 'wv1': '#8c6430', 'wv2': '#b88c48', 'wv3': '#dcb46c',
    'hb': '#e83c64', 'hbd': '#a01c44', 'or': '#d070e0', 'fy': '#f8d030',
})
DUSK = {'jg3': '#284c3c', 'jg4': '#3a644c', 'jg5': '#548060', 'jl3': '#205044', 'jl4': '#306c54', 'jl5': '#4c8c68',
        'jr2': '#1c5c6c', 'jr3': '#2c7c84'}

BANKS = [
    ['jg0', 'jg1', 'jg2', 'jg3', 'jg4', 'jg5', 'md0', 'md1', 'md2', 'md3', 'hb', 'hbd', 'or', 'fy'],
    ['jr0', 'jr1', 'jr2', 'jr3', 'jr4', 'jr5', 'jg0', 'jg1', 'jg2', 'jg3', 'jg4', 'jg5', 'md1', 'md2'],
    ['ms0', 'ms1', 'ms2', 'ms3', 'jg0', 'jg1', 'jg2', 'jg3', 'jg4', 'jg5', 'md0', 'md1', 'md2'],
    ['jl0', 'jl1', 'jl2', 'jl3', 'jl4', 'jl5', 'k0', 'k1', 'k2', 'k3', 'k4', 'hb', 'hbd', 'or', 'fy'],
    ['wv0', 'wv1', 'wv2', 'wv3', 'k0', 'k1', 'k2', 'k3', 'k4', 'jr0', 'jr2', 'md0', 'md1', 'md2'],
    ['ms0', 'ms1', 'ms2', 'ms3', 'jl0', 'jl1', 'jl2', 'jl3', 'k0', 'k1', 'jr3', 'jr4', 'fy'],
]

LOAM = {'dk': 'jg1', 'mid': 'jg2', 'base': 'jg3', 'lt': 'jg4', 'hi': 'jg5', 'out': 'jg0'}
MUD = {'dk': 'md0', 'mid': 'md1', 'base': 'md2', 'lt': 'md3', 'hi': 'md3'}
RIVER = {'deep': 'jr1', 'base': 'jr2', 'lt': 'jr3', 'hi': 'jr4', 'foam': 'jr5', 'dark': 'jr0'}
LEAF = ['jl0', 'jl1', 'jl2', 'jl3', 'jl4', 'jl5']
STONE = ['ms0', 'ms1', 'ms2', 'ms3', 'ms3']
BARK = ['k1', 'k2', 'k3']
WOOD = ['k1', 'k2', 'k3', 'k4']


def build():
    S = Sheet('jungle', 'Jungle - rainforest, river, root villages', PALETTE, variants={'dusk': DUSK},
              banks=BANKS, doc=__doc__)
    S.section('ground')
    loam = kit.grass_family(S, 'loam', LOAM, seeds=(1, 2, 3, 4), doc='jungle loam', tufts=(5, 7, 4, 6))
    mud = kit.speckle_family(S, 'mud', MUD, seeds=(5, 6, 7), doc='wet mud', dots=(10, 8, 12))
    S.tile('thicket', F.tallgrass({'out': 'jg0', 'dk': 'jg1', 'mid': 'jg2', 'base': 'jg3', 'lt': 'jg4', 'hi': 'jg5'}),
           attrs=['GRASS'], doc='dense undergrowth (encounters)')
    for name, (pt, pd, ce) in {'flowers_hibiscus': ('hb', 'hbd', 'fy'), 'flowers_orchid': ('or', 'hbd', 'fy')}.items():
        fr = [F.flower_patch(loam, pt, pd, ce, 'jg2', frame=f, seed=sum(map(ord, name)), kind='star') for f in range(2)]
        S.tile(name, fr[0], frames=fr, period=32, group='flowers', doc='jungle blossoms')

    S.section('autotiles')
    kit.path(S, 'mud_path', mud[0], loam, 'md1', 'jg1', 'md3', 'loam', 'muddy trail over loam', inner_alt=mud[1])
    kit.path(S, 'thicket_patch', F.tallgrass({'out': 'jg0', 'dk': 'jg1', 'mid': 'jg2', 'base': 'jg3', 'lt': 'jg4',
                                              'hi': 'jg5'}), loam, None, 'jg1', None, 'loam',
             'undergrowth with soft edges', seed=4, E=3.0, attrs=['GRASS'])
    kit.water(S, RIVER, loam, 'jg0', 'md1', 'loam', name='river', doc='jungle river over loam')
    kit.cliffs(S, STONE[:4] + ['ms3'], 'ms0', loam, loam, 'jg5', 'jg3', ['jg3', 'jg5'],
               ['jg5', 'jg4', 'ms2', 'ms1', 'ms0', 'jg1'], stairs_roles=('ms3', 'ms2', 'ms0', 'jg0', 'ms1'),
               lump=dict(rx=5, ry=4.5, sx=7.5, sy=7), doc_face='mossy rock face (>= 2 rows)')
    kit.waterfall(S, RIVER, STONE)

    S.section('trees')
    S.object('buttress_tree', J.buttress_tree(LEAF, 'jl0', BARK, 'k0'), top='XXX/XXX/.../...',
             solid='.../.../XXX/XXX', doc='buttress giant 3x4')
    kit.broadleaf(S, LEAF, 'jl0', BARK, 'k0', big=True, forest=True, forest_seed=4, doc='rainforest')
    S.object('big_leaf', J.big_leaf_plant(['jl1', 'jl2', 'jl4', 'jl5'], 'jl0'), doc='broad-leaf plant')
    S.object('fern', F.bush(16, 16, ['jl0', 'jl1', 'jl2', 'jl3', 'jl4'], 'jl0', seed=9, n=7), solid='.',
             doc='fern (walkable decor)')
    S.object('bamboo', J.bamboo(['jl1', 'jl3', 'jl4', 'jl5'], 'jl0'), top='X/.', solid='./X', doc='bamboo 1x2')
    S.object('vines', J.vines(['jl1', 'jl2', 'jl4'], flower='hb'), solid='./.', layer='top',
             doc='hanging vines 1x2 (top layer)')
    S.object('orchid', J.orchid('or', 'fy', ['jl1', 'jl2', 'jl4'], 'jl0'), solid='.', doc='orchid (decor)')
    S.object('bush_flower', F.bush(16, 16, LEAF, 'jl0', seed=3, flowers=('hb', 'fy', 4)), doc='hibiscus bush')
    S.object('lily_pads', F.lily_pad(['jg1', 'jg2', 'jg4'], 'jg1', flower=('hb', 'fy')), solid='.',
             doc='lily pads (river)')
    S.object('log', F.log_h(['k1', 'k2', 'k3', 'k4'], 'k0', 'k4', 'k2', moss=('jl3', 'jl4')), doc='mossy log 2x1')

    S.section('village')
    S.object('woven_hut', J.woven_hut(['wv0', 'wv1', 'wv2', 'wv3'], ['wv0', 'wv1', 'wv2', 'wv3'], ['k1', 'k2', 'k3'],
                                      'k0', ['k0', 'jr2']),
             top='XXXX/..../..../....', solid='..../XXXX/XXXX/....', doc='woven stilt home 4x4 on a root deck',
             extra={'door': [2, 2]})
    S.object('stilt_hut', J.woven_hut(['wv0', 'wv1', 'wv2', 'wv3'], ['wv0', 'wv1', 'wv2', 'wv3'], ['k1', 'k2', 'k3'],
                                      'k0', ['k0', 'jr2'], w=48, h=48),
             top='XXX/.../...', solid='.../XXX/...', doc='small stilt hut 3x3', extra={'door': [1, 1]})
    S.object('rope_bridge', CA.rope_bridge(WOOD, 'wv2', 'k0'), floor='XXX/XXX', solid='.../...',
             doc='rope bridge 3x2 (over river / gorge)')
    S.object('root_bridge', __import__('extras').root_bridge(['k1', 'k2', 'k3'], 'jl3', 'k0'), floor='XXX/XXX',
             solid='.../...', doc='living root bridge 3x2')
    S.object('waypost', PR.signpost(['wv0', 'wv1', 'wv2', 'wv3'], 'k0'), attrs=['SIGN'], doc='leaf-pattern waypost')
    S.object('jars', PR.barrel(['wv0', 'wv1', 'wv2', 'wv3'], 'k1', 'k0'), doc='woven basket')
    S.object('crate', PR.crate(WOOD, 'k0'), doc='crate')

    S.section('ruins')
    S.object('ruin_block', J.ruin_block(STONE, ['jl2', 'jl3'], 'ms0'), doc='carved temple block 2x2')
    S.object('idol', J.idol(STONE, 'ms0', 'jr4'), top='XX/../..', solid='../XX/XX', doc='jungle idol 2x3')
    S.patch9('ruin_wall', TP.stone_wall(['ms0', 'ms1', 'ms2', 'ms3', 'ms3'], 'ms0', cap='jl3'), layer='mid',
             attrs=['SOLID'], doc='mossy ruin wall')
    kit.rocks(S, STONE, 'ms0', moss=('jl3', 'jl4'))

    S.scene(jungle_scene())
    return S


def jungle_scene():
    sc = Scene('rootcoil', 'Rootcoil Jungle and Canopy Hearth (sample)', 36, 26, 'loam',
               doc='A root village on a clearing beside the river: woven stilt homes, a rope bridge, '
                   'buttress giants, bamboo, vines, mossy cliffs, a waterfall and temple ruins.')
    L = {'.': 'loam', '=': 'mud_path', '~': 'river', 'D': 'deep_river', ',': 'thicket_patch',
         '^': 'cliff_top', '#': 'cliff_face', 'F': ('forest', 'over'), 'W': ('ruin_wall', 'over')}
    sc.rows('''
FFFFFFFFFFFFFFFFFFFF^^^^^^^^FFFFFFFF
FFFFFFFFFFFFFFFFFFFF^^^^^^^^FFFFFFFF
FFFFFF..............^^^^^^^^....FFFF
FFFF................####~~##......FF
FF..................####~~##.......F
F.......,,,,.........~~~~~~~.......F
F......,,,,,,.......~~~~~~~~~......F
F.......,,,,.........~~DD~~~.......F
F====================~~DD~~==......F
F....................~~DD~~..=.....F
F....................~~DD~~..=.....F
F....................~~~~~~..=.....F
F.....................~~~~...=.....F
F.....................~~~~...=.....F
F....................~~~~....=.....F
F...................~~~~.....====..F
F..................~~~~.........=..F
F.................~~~~..........=..F
F....,,,,........~~~~...WWWWWW..=..F
F...,,,,,,......~~~~....W....W..=..F
F....,,,,......~~~~.....W....W..=..F
FF............~~~~..............=.FF
FFF..........~~~~...............=FFF
FFFFF.......~~~~..............FF=FFF
FFFFFFF....~~~~~....FFFFFFFFFFFF=FFF
FFFFFFFFFF~~~~~FFFFFFFFFFFFFFFFF=FFF
''', L)
    obj = [('waterfall', 23, 2), ('rope_bridge', 20, 8), ('woven_hut', 6, 9), ('woven_hut', 12, 11),
           ('stilt_hut', 29, 10), ('buttress_tree', 1, 13), ('tree_big', 9, 18), ('tree', 30, 2), ('tree_b', 17, 3),
           ('bamboo', 3, 4), ('bamboo', 4, 4), ('bamboo', 33, 16), ('vines', 26, 3), ('vines', 19, 0),
           ('big_leaf', 18, 12), ('big_leaf', 27, 14), ('fern', 10, 16), ('fern', 21, 21), ('orchid', 7, 17),
           ('bush_flower', 15, 15), ('lily_pads', 18, 16), ('log', 24, 22), ('idol', 26, 18), ('ruin_block', 28, 20),
           ('waypost', 19, 9), ('jars', 11, 13), ('crate', 5, 13), ('rock', 31, 7)]
    for (n, x, y) in obj:
        sc.put(n, x, y)
    sc.sprinkle(['fern', 'big_leaf', 'orchid', 'fern', 'bush_flower'], 22, on={'loam'}, seed=5)
    return sc
