"""DREAM - Mistfen, Moonveil, Dreamspire and the Dust Library.

Replaces the old `dream` tileset (Mistfen, Moonveil Path, Dreamspire, Dust
Library, Mirror Hall). Twilight grass dusted with stars, moonstone paths,
a lavender mist-lake that mirrors the sky, glowing moon lilies, crystal
trees, marble spires with gold bands, mirrors, moon orbs and drifting
pages.
"""

from core import Img
from sheet import Sheet, Scene
import paint as P
import terrain as T
import flora as F
import props as PR
import townprops as TP
import desertart as DS
import dreamart as DR
import extras as X
import buildings as B
import gothart as GO
import kit

PALETTE = {
    'dg0': '#101428', 'dg1': '#1c2844', 'dg2': '#2a4058', 'dg3': '#3a5c6c', 'dg4': '#528080', 'dg5': '#7cac9c',
    'mp0': '#3c3858', 'mp1': '#5c5880', 'mp2': '#8480a8', 'mp3': '#aca8cc', 'mp4': '#d4d0ec',
    'mw0': '#141434', 'mw1': '#242450', 'mw2': '#3a3872', 'mw3': '#5c5898', 'mw4': '#9490c8', 'mw5': '#dcd8ff',
    'ct0': '#1c3c5c', 'ct1': '#2c6484', 'ct2': '#48a0b4', 'ct3': '#80d4d8', 'ct4': '#d0fff8',
    'cp0': '#5c2c6c', 'cp1': '#9c4c9c', 'cp2': '#dc88d0', 'cp3': '#ffd8f4',
    'mb0': '#4c4c6c', 'mb1': '#8c8cac', 'mb2': '#c0c0d8', 'mb3': '#ececf8',
    'au0': '#8c6424', 'au1': '#d8a840', 'au2': '#fff0a0',
    'ml1': '#b8c8ff', 'ml2': '#f0f4ff', 'st': '#fff8c0',
    'bk1': '#2c2438', 'bk2': '#44385a', 'bk3': '#5c4c78',
}
# Waking hour: warmer, rosier light over the same dream.
DAWN = {'dg2': '#4c4458', 'dg3': '#6c5c6c', 'dg4': '#947880', 'dg5': '#c4a098',
        'mw2': '#6c4c78', 'mw3': '#9c6c94', 'mw4': '#d49cbc', 'mp2': '#a88ca8', 'mp3': '#ccb0c4'}

STYLE = {'out': 'mb0', 'roof': ['mw1', 'mw2', 'mw3', 'mw4', 'ml2'], 'wall': ['mb1', 'mb2', 'mb3'],
         'trim': ['au0', 'au1', 'au2'], 'glass': ['mw1', 'mw3', 'ml2'], 'found': ['mb0', 'mb1', 'mb2'],
         'chimney': ['mb0', 'mb1', 'mb2'], 'door': ['au0', 'mw2', 'mw3']}
ROSE = dict(STYLE, roof=['cp0', 'cp1', 'cp2', 'cp3', 'ml2'])

BANKS = [
    ['dg0', 'dg1', 'dg2', 'dg3', 'dg4', 'dg5', 'mp0', 'mp1', 'mp2', 'mp3', 'mp4', 'st', 'ml1', 'ml2'],
    ['mw0', 'mw1', 'mw2', 'mw3', 'mw4', 'mw5', 'dg0', 'dg1', 'dg2', 'dg3', 'dg4', 'dg5', 'st'],
    ['ct0', 'ct1', 'ct2', 'ct3', 'ct4', 'cp0', 'cp1', 'cp2', 'cp3', 'bk1', 'bk2', 'bk3', 'mp1', 'mp2', 'dg0'],
    ['mb0', 'mb1', 'mb2', 'mb3', 'au0', 'au1', 'au2', 'mw1', 'mw2', 'mw3', 'mw4', 'mp0', 'mp1', 'mp2', 'ml2'],
    ['mb0', 'mb1', 'mb2', 'mb3', 'mp0', 'mp1', 'mp2', 'mp3', 'mp4', 'dg1', 'dg2', 'dg3', 'dg4', 'dg5'],
    ['cp0', 'cp1', 'cp2', 'cp3', 'mb0', 'mb1', 'mb2', 'mb3', 'au0', 'au1', 'au2', 'mw1', 'mw2', 'mw3', 'ml2'],
]

GRASS = {'dk': 'dg1', 'mid': 'dg2', 'base': 'dg3', 'lt': 'dg4', 'hi': 'dg5', 'out': 'dg0'}
PATH = {'dk': 'mp0', 'mid': 'mp1', 'base': 'mp2', 'lt': 'mp3', 'hi': 'mp4'}
MIST = {'deep': 'mw1', 'base': 'mw2', 'lt': 'mw3', 'hi': 'mw4', 'foam': 'mw5', 'dark': 'mw0'}
MARBLE = ['mb0', 'mb1', 'mb2', 'mb3', 'mb3']
GOLD = ['au0', 'au1', 'au2']


def build():
    S = Sheet('dream', 'Dream - Mistfen, Moonveil, Dreamspire', PALETTE, variants={'dawn': DAWN}, banks=BANKS,
              doc=__doc__)
    S.section('ground')
    grass = kit.grass_family(S, 'grass', GRASS, doc='twilight grass')
    S.tile('grass_stars', DR.star_grass(GRASS, 'st', 5), group='grass', weight=2, doc='grass with star-dust')
    S.tile('grass_stars_b', DR.star_grass(GRASS, 'st', 6, n=1), group='grass', weight=2)
    flag = T.flagstones(['mp0', 'mp1', 'mp2', 'mp3'], seed=4)
    S.tile('moonstone', flag, doc='moonstone flags')
    S.tile('tallgrass', F.tallgrass(GRASS), attrs=['GRASS'], doc='mist reeds (encounters)')
    fr = [DR.moon_lily(grass, 'ml1', 'ml2', 'dg2', f) for f in range(3)]
    S.tile('moon_lilies', fr[0], frames=fr, period=24, doc='glowing moon lilies')

    S.section('autotiles')
    kit.path(S, 'path', flag, grass, 'mp0', 'dg1', 'mp4', 'grass', 'moonstone path over grass', seed=3, E=3.0,
             amp=0.5)
    kit.path(S, 'reeds_patch', F.tallgrass(GRASS), grass, None, 'dg1', None, 'grass', 'mist reeds', seed=4, E=3.0,
             attrs=['GRASS'])
    kit.water(S, MIST, grass, 'dg0', 'dg1', 'grass', name='mistlake', doc='star-reflecting mist lake over grass')
    kit.cliffs(S, ['mp0', 'mp1', 'mp2', 'mp3', 'mp4'], 'dg0', grass, grass, 'dg5', 'dg3', ['dg2', 'dg4'],
               ['dg5', 'dg4', 'mp2', 'mp1', 'dg0', 'dg1'], stairs_roles=('mb3', 'mb2', 'mb0', 'dg0', 'mb1'))

    S.section('flora')
    S.object('crystal_tree', DR.crystal_tree(['ct0', 'ct1', 'ct2', 'ct3', 'ct4'], 'ct0', ['bk1', 'bk2', 'bk3']),
             top='XX/XX/..', solid='../../XX', doc='crystal tree 2x3 (teal)')
    S.object('crystal_tree_rose', DR.crystal_tree(['cp0', 'cp1', 'cp2', 'cp3', 'cp3'], 'cp0', ['bk1', 'bk2', 'bk3'],
                                                  seed=4), top='XX/XX/..', solid='../../XX', doc='crystal tree 2x3 (rose)')
    S.object('dream_tree', F.round_tree('mid', ['ct0', 'ct1', 'ct2', 'ct3', 'ct4'], 'ct0', ['bk1', 'bk2', 'bk3'], 'bk1',
                                        seed=7), top='XX/..', solid='../XX', doc='mist willow 2x2')
    S.patch9('forest', F.forest_wall(['dg0', 'ct0', 'ct1', 'ct2', 'ct3'], 'dg0', ['bk1', 'bk2', 'bk3'], 'bk1', seed=5),
             layer='mid', attrs=['SOLID'], doc='dreamwood mass')
    S.object('shrub', F.bush(16, 16, ['cp0', 'cp1', 'cp2', 'cp3'], 'cp0', seed=2), doc='rose-crystal shrub')
    S.object('reeds', F.reeds(['dg1', 'dg2', 'dg4'], h=16, heads=('mp1', 'mp2', 'mp4')), solid='X', doc='mist reeds')

    S.section('architecture')
    S.object('spire', DR.spire(MARBLE, ['mw1', 'mw2', 'mw3'], GOLD, ['mw0', 'mw3', 'mw5'], 'mb0'),
             top='XXX/XXX/XXX/.../.../...', solid='.../.../.../XXX/XXX/XXX', doc='Dreamspire tower 3x6',
             extra={'door': [1, 5]})
    S.object('house', B.house(64, 64, STYLE, door_at=40, windows=[(8, 6)], roof_style='slate', siding='stone'),
             doc='marble house 4x4', extra={'door': [2, 3]})
    S.object('house_rose', B.house(64, 64, ROSE, door_at=24, windows=[(38, 6)], roof_style='tile', siding='stone'),
             doc='rose-roofed house 4x4', extra={'door': [1, 3]})
    kit.civic(S, STYLE, ('au2', 'au1', 'au0'), roof_style='slate', siding='stone', skip=('inn', 'hall'),
              chimney=False)
    S.object('spire_rose', DR.spire(MARBLE, ['cp1', 'cp2', 'cp3'], GOLD, ['mw1', 'mw3', 'ml2'], 'mb0'),
             top='XXX/XXX/XXX/.../.../...', solid='.../.../.../XXX/XXX/XXX', doc='rose spire 3x6',
             extra={'door': [1, 5]})
    S.object('mirror_hall', B.house(112, 80, STYLE, door_at=56, windows='auto', roof_style='slate', siding='stone',
                                    storeys=2, door_w=18), doc='Mirror Hall 7x5', extra={'door': [3, 4]})
    S.object('library', B.house(128, 96, ROSE, door_at=64, windows='auto', roof_style='tile', siding='stone',
                                storeys=2, door_w=20, beams=True), doc='Dust Library 8x6', extra={'door': [4, 5]})
    S.object('book_pile', X.book_pile([('au0', 'au1', 'au2'), ('mw1', 'mw2', 'mw3'), ('mb0', 'mb1', 'mb2'),
                                       ('mp0', 'mp1', 'mp2')], 'mb0'), doc='pile of books')
    S.object('reading_desk', X.reading_desk(['mb0', 'mb1', 'mb2'], ['mb2', 'mb3'],
                                            ['au0', 'au1', 'au2'], 'mb0'), top='XX/..', solid='../XX',
             doc='reading desk 2x2')
    S.object('bookcase', __import__('interiorart').bookshelf(['mb0', 'mb1', 'mb2'],
                                                             [('au0', 'au1', 'au2'), ('mw1', 'mw2', 'mw3'),
                                                              ('mp0', 'mp1', 'mp2')], 'mb0'), doc='bookcase 2x2')
    S.object('petals', X.petals(['cp2', 'cp3', 'ml2']), solid='.', doc='drifting petals (decor)')
    S.object('script_pedestal', X.script_pedestal(MARBLE, ['mb2', 'mb3'], 'au2', 'mb0'), top='X/.', solid='./X',
             doc='script pedestal 1x2')
    S.object('column', DS.pillar(MARBLE, 'mb0'), top='X/./.', solid='./X/X', doc='marble column 1x3')
    S.object('column_broken', DS.pillar(MARBLE, 'mb0', broken=True), top='X/./.', solid='./X/X',
             doc='fallen column 1x3')
    S.object('mirror', DR.mirror(GOLD, ['mw2', 'mw3', 'mw5'], 'mb0'), top='X/.', solid='./X', doc='standing mirror 1x2')
    orb = [DR.moon_orb(MARBLE, ['mw3', 'mw4', 'mw5'], 'mb0', f) for f in range(2)]
    S.object('moon_orb', orb[0], frames=orb, period=30, top='X/.', solid='./X', doc='moon orb pedestal 1x2')
    S.object('moon_lantern', TP.lamp_post(['mb0', 'mb1', 'mb2'], 'mb0', ['mw3', 'mw4', 'mw5']), top='X/.', solid='./X',
             doc='moon lantern 1x2')
    pg = [DR.floating_pages(['mb1', 'mb2', 'mb3'], 'mp0', f) for f in range(4)]
    S.object('pages', pg[0], frames=pg, period=14, solid='.', layer='top', doc='drifting pages (animated)')
    S.object('statue', TP.statue(MARBLE, 'mb0', ['mb0', 'mb1', 'mb2']), top='XX/../..', solid='../XX/XX',
             doc='dreamer statue 2x3')
    ws = [GO.wisp(['ml1', 'ml2'], 'mw4', f) for f in range(4)]
    S.object('mote', ws[0], frames=ws, period=14, solid='.', layer='top', doc='floating light mote')
    S.object('signpost', PR.signpost(MARBLE, 'mb0'), attrs=['SIGN'], doc='marble plaque')
    kit.rocks(S, ['mp0', 'mp1', 'mp2', 'mp3', 'mp4'], 'dg0')

    S.scene(moonveil_scene())
    return S


def moonveil_scene():
    sc = Scene('moonveil', 'Moonveil to Dreamspire (sample)', 36, 26, 'grass',
               doc='A moonstone path winding past the star-reflecting mist lake, moon lilies and '
                   'crystal trees, to the marble Dreamspire with its columns and orbs.')
    L = {'.': 'grass', '=': 'path', '~': 'mistlake', 'D': 'deep_mistlake', ',': 'reeds_patch', 'l': 'moon_lilies',
         'F': ('forest', 'over')}
    sc.rows('''
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
FFFFFFFFFFFFF...........FFFFFFFFFFFF
FFFFFFFF.................FFFFFFFFFFF
FFFF......................FFFFFFFFFF
FF.........................FFFFFFFFF
F...........======...........FFFFFFF
F...........=....=............FFFFFF
F...........=....=.............FFFFF
F...........======..............FFFF
F..............=.................FFF
F..............=..................FF
F...~~~~~......=...................F
F..~~~~~~~~....==..........lll.....F
F.~~~~DD~~~~....=.........lllll....F
F.~~~DDDD~~~~...==.........lll.....F
F..~~~DD~~~~.....=.................F
F...~~~~~~~......==................F
F....,,,~~........=................F
F...,,,,,..........==..............F
F....,,,............=====..........F
F.......................=..........F
F........................===.......F
FF.........................===....FF
FFF..........................==..FFF
FFFFFF........................=FFFFF
FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF=FFFFF
''', L)
    obj = [('spire', 13, 0), ('column', 10, 3), ('column', 19, 3), ('column_broken', 22, 6), ('moon_orb', 11, 8),
           ('moon_orb', 18, 8), ('mirror', 24, 3), ('statue', 7, 4), ('crystal_tree', 26, 8), ('crystal_tree_rose', 3, 18),
           ('crystal_tree', 30, 16), ('dream_tree', 21, 12), ('shrub', 25, 19), ('shrub', 9, 20), ('reeds', 11, 12),
           ('reeds', 12, 16), ('moon_lantern', 17, 12), ('moon_lantern', 23, 18), ('pages', 20, 9), ('pages', 14, 10),
           ('mote', 6, 10), ('mote', 28, 14), ('mote', 12, 21), ('signpost', 19, 20), ('rock', 32, 11)]
    for (n, x, y) in obj:
        sc.put(n, x, y)
    sc.sprinkle(['petals', 'pebbles', 'mote', 'petals'], 14, on={'grass'}, seed=5)
    return sc
