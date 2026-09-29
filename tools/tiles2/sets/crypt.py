"""CRYPT - barrows, ossuaries, vaults and the Bone Throne.

Replaces the old `crypt` tileset (Barrow A/B, Lantern Crypt, Ossuary 1/2,
Dusk Vault, Root Gallery, Waychapel, Bone Throne). Dressed-stone walls
with a dark top, slab floors, a red carpet runner, candles and braziers,
sarcophagi, coffins, urns, skull niches, banners, chains, webs, iron gates
and the throne.
"""

from core import Img
from sheet import Sheet, Scene
import paint as P
import terrain as T
import flora as F
import props as PR
import caveart as CA
import fireart as FI
import dungeonart as DG
import gothart as GO
import kit

PALETTE = {
    'cs0': '#100e14', 'cs1': '#26222c', 'cs2': '#3c3642', 'cs3': '#564e58', 'cs4': '#746a72', 'cs5': '#968a90',
    'cf0': '#1a1618', 'cf1': '#2e282a', 'cf2': '#443c3c', 'cf3': '#5c5250', 'cf4': '#766a66',
    'v0': '#060508',
    'rd0': '#3c0c14', 'rd1': '#6c1824', 'rd2': '#9c2c34',
    'au0': '#7c5c1c', 'au1': '#c8a038', 'au2': '#f4dc80',
    'bn0': '#8c8474', 'bn1': '#c4bca8', 'bn2': '#ece4d0',
    'wx1': '#b8a888', 'wx2': '#e4d8bc',
    'fl0': '#c85c1c', 'fl1': '#f8c040', 'fl2': '#fff4b0',
    'wd0': '#241a18', 'wd1': '#443428', 'wd2': '#645038',
    'rt0': '#2a1e16', 'rt1': '#4a3624', 'rt2': '#6c5236',
    'ws0': '#3c8cc8', 'ws1': '#b8f0ff', 'ws2': '#6cc8e8',
    'sk': '#b4b0b8',
}
# Lit: when the braziers are lit, the halls warm up.
LIT = {'cs2': '#4c3c38', 'cs3': '#6c5448', 'cs4': '#8c7058', 'cs5': '#b09070', 'cf2': '#54423a', 'cf3': '#6e5a4a',
       'cf4': '#8c7460'}

BANKS = [
    ['cf0', 'cf1', 'cf2', 'cf3', 'cf4', 'cs0', 'cs1', 'cs2', 'v0', 'bn0', 'bn1', 'bn2', 'sk'],
    ['cs0', 'cs1', 'cs2', 'cs3', 'cs4', 'cs5', 'cf1', 'cf2', 'cf3', 'cf4', 'v0', 'rt0', 'rt1', 'rt2'],
    ['rd0', 'rd1', 'rd2', 'au0', 'au1', 'au2', 'cf0', 'cf1', 'cf2', 'cf3', 'cf4', 'cs0'],
    ['cs0', 'cs1', 'cs2', 'cs3', 'cs4', 'cs5', 'au0', 'au1', 'au2', 'rd0', 'rd1', 'rd2', 'bn1', 'bn2'],
    ['wx1', 'wx2', 'fl0', 'fl1', 'fl2', 'wd0', 'wd1', 'wd2', 'cs0', 'cs1', 'cs2', 'cs3', 'ws0', 'ws1', 'ws2'],
]

FLOOR = ['cf0', 'cf1', 'cf2', 'cf3']
MASON = ['cs1', 'cs2', 'cs3', 'cs4']
STONE = ['cs1', 'cs2', 'cs3', 'cs4', 'cs5']


def build():
    S = Sheet('crypt', 'Crypt - barrows, ossuaries, vaults', PALETTE, variants={'lit': LIT}, banks=BANKS, doc=__doc__)
    S.section('floors')
    slabs = DG.floor_slabs(['cf1', 'cf2', 'cf3', 'cf4'])
    S.tile('floor', slabs, group='floor', weight=6, doc='stone slabs')
    S.tile('floor_cracked', DG.floor_slabs(['cf1', 'cf2', 'cf3', 'cf4'], seed=3, cracked=True), group='floor',
           weight=2, doc='cracked slabs')
    S.tile('floor_bones', PR.pebbles(['bn0', 'bn1', 'bn2', 'bn2'], 'cf0', 3).under(slabs), group='floor', weight=1,
           doc='bone-strewn slabs')
    dirt = kit.speckle_family(S, 'earth', {'dk': 'cf0', 'mid': 'cf1', 'base': 'cf2', 'lt': 'cf3', 'hi': 'cf4'},
                              seeds=(7, 8), doc='barrow earth', weights=(3, 2))
    top = T.lump_texture(['cs0', 'cs0', 'cs1', 'cs2'], 16, 16, 5, rx=3.5, ry=2.6, sx=5.3, sy=4, bias=-0.2)
    S.tile('wall_top', top, attrs=['SOLID'], doc='top of a wall mass')

    S.section('walls')
    face = DG.masonry(MASON, seed=1)
    kit.cliffs(S, STONE, 'cs0', top, slabs, 'cs2', None, None, ['cs3', 'cf4', 'cs3', 'cs2', 'cs0', 'cf1'],
               stairs_roles=('cf4', 'cf3', 'cf1', 'cs0', 'cf2'), face_tex=face, face_tex2=DG.masonry(MASON, seed=2),
               doc_face='dressed-stone wall face (>= 2 rows)')
    S.autotile('carpet', DG.carpet_autotile(['rd0', 'rd1', 'rd2'], slabs, ['au0', 'au1']), over='floor',
               doc='red carpet runner with gold border')
    S.autotile('pit', CA.chasm_autotile(slabs, 'v0', 'cf1', ['cs0', 'cs1', 'cs2', 'cs3']), over='floor',
               attrs=['SOLID'], doc='open pit / collapsed floor')
    S.object('skull_niche', DG.skull_niche(['cs0', 'cs1'], ['bn0', 'bn1', 'bn2'], 'cs0'), solid='X',
             doc='skull alcove (set into a wall face)')
    S.object('banner', DG.banner(['rd0', 'rd1', 'rd2'], ['au0', 'au1', 'au2'], 'au1', 'cs0'), solid='./.',
             doc='hanging banner 1x2 (on a wall face)')
    S.object('chains', DG.chains(['cs1', 'cs3', 'cs4'], 'cs0'), solid='./.', doc='wall chains 1x2')
    S.object('web', DG.web('sk'), solid='.', layer='top', doc='cobweb (corner)')
    S.object('roots', CA.hanging_roots(['rt0', 'rt1', 'rt2'], 'cs0'), solid='.', layer='top',
             doc='roots through the ceiling (Root Gallery)')
    S.object('iron_gate', DG.iron_gate(['cs0', 'cs2', 'cs4'], 'cs0'), solid='XX/XX', doc='iron gate 2x2 (locked)')

    S.section('furnishings')
    cd = [DG.candles(['wx1', 'wx1', 'wx2'], ['fl1', 'fl2'], 'cs0', f) for f in range(2)]
    S.object('candles', cd[0], frames=cd, period=16, doc='candle cluster (flicker)')
    bz = [FI.brazier(['cs1', 'cs2', 'cs4'], ['fl0', 'fl1', 'fl2'], 'cs0', f) for f in range(3)]
    S.object('brazier', bz[0], frames=bz, period=8, top='X/.', solid='./X', doc='brazier 1x2 (animated)')
    S.object('sarcophagus', DG.sarcophagus(STONE, 'cs0', trim='au1'), doc='sarcophagus 2x2')
    S.object('coffin', DG.coffin(['wd0', 'wd1', 'wd2'], 'cs0'), doc='coffin 1x2')
    S.object('urn', DG.urn(['cs1', 'cs3', 'cs4'], 'cs0', band='au1'), doc='funeral urn')
    S.object('bone_pile', CA.bones(['bn0', 'bn1', 'bn2'], 'cf0'), solid='.', doc='bones')
    S.object('skulls', GO.gravestone(['bn0', 'bn1', 'bn2'], 'cs0', 'round'), doc='skull cairn')
    S.object('statue', __import__('townprops').statue(STONE, 'cs0', ['cs1', 'cs2', 'cs3']), top='XX/../..',
             solid='../XX/XX', doc='guardian statue 2x3')
    S.object('throne', DG.throne(STONE, ['rd0', 'rd1', 'rd2'], ['au0', 'au1', 'au2'], 'cs0'), top='XX/../..',
             solid='../XX/XX', doc='the Bone Throne 2x3')
    S.object('pedestal', __import__('dreamart').moon_orb(STONE, ['au0', 'au1', 'au2'], 'cs0', 0), top='X/.',
             solid='./X', doc='relic pedestal 1x2')
    ws = [GO.wisp(['ws0', 'ws1'], 'ws2', f) for f in range(4)]
    S.object('wisp', ws[0], frames=ws, period=12, solid='.', layer='top', doc='restless wisp')
    S.object('signpost', PR.signpost(['wd0', 'wd1', 'wd2', 'wd2'], 'cs0'), attrs=['SIGN'], doc='plaque')

    S.scene(crypt_scene())
    return S


def crypt_scene():
    sc = Scene('ossuary', 'Ossuary and Bone Throne (sample)', 30, 22, 'floor',
               doc='Dressed-stone halls: a carpeted nave between sarcophagi and braziers leads to the '
                   'throne; side crypts with coffins, niches and a collapsed pit.')
    L = {'.': 'floor', '^': 'cliff_top', '#': 'cliff_face', 'c': 'carpet', 'p': 'pit', 'e': 'earth'}
    sc.rows('''
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
^^^^^^^^^^############^^^^^^^^
^^^^^^^^^^############^^^^^^^^
^^^^^^^^^^....cccc....^^^^^^^^
^^^^^^^^^^....cccc....^^^^^^^^
##########....cccc....########
##########....cccc....########
..............cccc............
..............cccc............
..............cccc............
..............cccc............
^^^^^^^.......cccc.......^^^^^
#######.......cccc.......#####
#######.......cccc.......#####
..............cccc............
...ppp........cccc.......eeee.
..pppp........cccc......eeeeee
...pp.........cccc.......eeee.
..............cccc............
..............cccc............
''', L)
    obj = [('throne', 15, 3), ('brazier', 11, 5), ('brazier', 20, 5), ('banner', 12, 3), ('banner', 19, 3),
           ('sarcophagus', 10, 10), ('sarcophagus', 20, 10), ('candles', 12, 9), ('candles', 19, 9),
           ('skull_niche', 2, 8), ('skull_niche', 5, 8), ('skull_niche', 24, 8), ('skull_niche', 27, 8),
           ('chains', 8, 14), ('coffin', 2, 15), ('coffin', 4, 15), ('urn', 27, 15), ('urn', 28, 16),
           ('statue', 7, 9), ('statue', 23, 9), ('bone_pile', 7, 18), ('skulls', 26, 20), ('web', 0, 9),
           ('wisp', 3, 19), ('pedestal', 27, 11), ('iron_gate', 14, 20)]
    for (n, x, y) in obj:
        sc.put(n, x, y)
    sc.sprinkle(['bone_pile', 'candles', 'urn'], 6, on={'floor'}, seed=5)
    return sc
