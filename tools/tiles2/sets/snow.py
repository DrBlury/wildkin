"""SNOW - alpine forests, frozen lakes, tundra and snowbound villages.

Replaces the old `snow` tileset (Frostpine Pass, Timberline, Frosthollow,
Aurora Ridge 1/2, Whitecrown, Rimewind Tundra, Hot Spring, Sky Isle, Rime
Hall, Karst Frost). Snow with wind ripples, ice floors (slide), a cold
lake, blue-grey rock, snow-laden pines, log cabins with warm windows,
hot springs with steam and aurora stones.
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
import snowart as SN
import extras as X
import kit

PALETTE = PL.merge(PL.PINE, PL.BARK, {
    'sn0': '#34406c', 'sn1': '#7888b8', 'sn2': '#a8b8dc', 'sn3': '#d0dcf0', 'sn4': '#eef4fc', 'sn5': '#ffffff',
    'ic0': '#3c7cb0', 'ic1': '#6cb0e0', 'ic2': '#a8dcf4', 'ic3': '#e0f8ff',
    'cw0': '#1c3c6c', 'cw1': '#2c5c98', 'cw2': '#3c7cbc', 'cw3': '#64a0d8', 'cw4': '#a0ccec',
    'b0': '#1c2230', 'b1': '#343e50', 'b2': '#4e5c70', 'b3': '#6c7c90', 'b4': '#94a4b4', 'b5': '#c4ccd4',
    'mo1': '#4c6c54', 'mo2': '#6c8c64', 'mo3': '#94ac7c',
    'gw0': '#8c4c1c', 'gw1': '#f0a838', 'gw2': '#fff0a0',
    'hs0': '#1c6c74', 'hs1': '#34a4a4', 'hs2': '#8cdcd0',
    'au1': '#5ce0a0', 'au2': '#b0ffd8', 'mg': '#c070e0',
    'fr': '#d83c3c', 'fo': '#f09040',
})
# Night on the ridge: deep blue snow, the aurora and windows glow.
NIGHT = {'sn1': '#2c3464', 'sn2': '#3c4880', 'sn3': '#52609c', 'sn4': '#6c7cb4', 'sn5': '#8c9cd0',
         'b3': '#3c4868', 'b4': '#50608a', 'b5': '#6c7ca4', 'p3': '#1c4c4c', 'p4': '#28604c',
         'ic2': '#6c9cd0', 'ic3': '#9cc4ec'}

BANKS = [
    ['sn0', 'sn1', 'sn2', 'sn3', 'sn4', 'sn5', 'ic0', 'ic1', 'ic2', 'ic3', 'mo1', 'mo2', 'mo3'],
    ['sn0', 'sn1', 'sn2', 'sn3', 'sn4', 'sn5', 'cw0', 'cw1', 'cw2', 'cw3', 'cw4', 'ic2', 'ic3'],
    ['b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'sn2', 'sn3', 'sn4', 'sn5', 'mo1', 'mo2', 'mo3'],
    ['p0', 'p1', 'p2', 'p3', 'p4', 'k0', 'k1', 'k2', 'k3', 'sn2', 'sn3', 'sn4', 'sn5'],
    ['sn0', 'sn1', 'sn2', 'sn3', 'sn4', 'sn5', 'k0', 'k1', 'k2', 'k3', 'k4', 'gw0', 'gw1', 'gw2', 'fr'],
    ['b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'k0', 'k1', 'k2', 'k3', 'k4', 'fr', 'fo', 'sn4', 'sn5'],
    ['hs0', 'hs1', 'hs2', 'b0', 'b1', 'b2', 'b3', 'b4', 'sn3', 'sn4', 'sn5'],
    ['ic0', 'ic1', 'ic2', 'ic3', 'au1', 'au2', 'mg', 'b0', 'b1', 'b2', 'b3', 'b4', 'sn4', 'sn5'],
]

SNOW = ['sn2', 'sn3', 'sn4', 'sn5', 'sn5']
GRS = {'dk': 'sn2', 'mid': 'sn3', 'base': 'sn4', 'lt': 'sn5', 'hi': 'sn5', 'out': 'sn1'}
MOSS = {'dk': 'mo1', 'mid': 'mo1', 'base': 'mo2', 'lt': 'mo3', 'hi': 'sn4', 'out': 'sn0'}
LAKE = {'deep': 'cw1', 'base': 'cw2', 'lt': 'cw3', 'hi': 'cw4', 'foam': 'ic3', 'dark': 'cw0'}
ROCK = ['b1', 'b2', 'b3', 'b4', 'b5']
WOOD = ['k1', 'k2', 'k3', 'k4']
LOG = {'out': 'k0', 'roof': ['sn1', 'sn2', 'sn3', 'sn4', 'sn5'], 'wall': ['k1', 'k2', 'k3'], 'trim': ['k0', 'k1', 'k2'],
       'glass': ['gw0', 'gw1', 'gw2'], 'found': ['k0', 'k1', 'k2'], 'chimney': ['k0', 'k1', 'k2'],
       'door': ['k0', 'k1', 'k2'], 'window': (10, 9)}


def build():
    S = Sheet('snow', 'Snow - alpine, tundra, frozen villages', PALETTE, variants={'night': NIGHT},
              banks=BANKS, doc=__doc__)
    S.section('ground')
    imgs = [SN.snow_ground(SNOW, s) for s in (1, 2, 3, 4)]
    for i, im in enumerate(imgs):
        S.tile('snow' if i == 0 else 'snow_' + 'bcd'[i - 1], im, group='snow', weight=(8, 4, 3, 2)[i],
               doc='wind-rippled snow' if i == 0 else '')
    S.tile('snow_deep', SN.snow_ground(['sn1', 'sn2', 'sn3', 'sn4', 'sn5'], 7, sparkle=1), attrs=['GRASS'],
           doc='deep powder (encounters, slow)')
    moss = kit.grass_family(S, 'tundra', MOSS, seeds=(21, 22, 23, 24), doc='tundra moss', tufts=(3, 4, 2, 3))
    ice = SN.ice_floor(['ic0', 'ic1', 'ic2', 'ic3'], 3)
    S.tile('ice', ice, attrs=['ICE'], doc='slippery ice (slide until stopped)')
    S.tile('ice_b', SN.ice_floor(['ic0', 'ic1', 'ic2', 'ic3'], 8), attrs=['ICE'])

    S.section('autotiles')
    kit.path(S, 'ice_patch', ice, imgs[0], 'ic1', 'sn2', 'ic3', 'snow', 'ice sheet over snow', seed=4, amp=1.0,
             attrs=['ICE'])
    kit.path(S, 'tundra_patch', moss, imgs[0], 'mo1', 'sn3', 'mo3', 'snow', 'moss showing through snow',
             seed=8, amp=1.4)
    kit.path(S, 'trail', SN.snow_ground(['sn1', 'sn2', 'sn3', 'sn4', 'sn4'], 11, sparkle=0), imgs[0], 'sn2', 'sn3',
             'sn4', 'snow', 'trodden trail through snow', seed=3)
    kit.water(S, LAKE, imgs[0], 'sn1', 'sn3', 'snow', name='lake', doc='cold lake over snow (ice-rimmed)')
    kit.water(S, LAKE, ice, 'ic0', 'ic1', 'ice_patch', name='ice_hole', deep=False, doc='open water in an ice sheet')
    kit.cliffs(S, ROCK, 'b0', imgs[0], imgs[0], 'sn5', 'sn4', ['sn3', 'sn5'], ['sn5', 'sn4', 'b3', 'b2', 'b0', 'sn2'],
               stairs_roles=('sn5', 'sn4', 'b2', 'b0', 'b3'), lump=dict(rx=5.5, ry=4.0, sx=8, sy=6))
    S.patch9('snowbank', SN.snowbank(['sn1', 'sn2', 'sn3', 'sn4', 'sn5'], 'sn0', seed=2), layer='mid',
             attrs=['SOLID'], doc='packed snowbank wall')

    S.section('trees')
    kit.conifers(S, ['p0', 'p1', 'p2', 'p3', 'p4'], 'p0', ['k1', 'k2', 'k3'], 'k0', snow=('sn5', 'sn3'),
                 doc='snowy pine')
    S.object('pine_bare', F.conifer(32, 48, ['p0', 'p1', 'p2', 'p3', 'p4'], 'p0', ['k1', 'k2', 'k3'], 'k0',
                                     seed=5, tiers=5), top='XX/XX/..', solid='../../XX', doc='pine without snow')
    S.object('dead_tree', F.dead_tree(32, 32, ['k1', 'k2', 'k3'], 'k0', seed=9), top='XX/..', solid='../XX',
             doc='frost-killed tree 2x2')
    S.object('shrub', F.bush(16, 16, ['p0', 'p1', 'p2', 'p3', 'p4'], 'p0', seed=4), doc='juniper shrub')

    S.section('village')
    S.object('cabin', B.house(64, 64, LOG, door_at=40, windows=[(8, 6)], chimney=12, roof_style='snow',
                              siding='log'), doc='log cabin 4x4, snow roof, lit window', extra={'door': [2, 3]})
    S.object('lodge', B.house(96, 80, LOG, door_at=48, windows='auto', chimney=74, roof_style='snow',
                              siding='log', storeys=2, door_w=14), doc='mountain lodge 6x5', extra={'door': [3, 4]})
    S.object('cabin_gable', B.house(64, 64, LOG, door_at=32, windows=[(4, 5), (48, 5)], gable=True, siding='log',
                                    roof_style='snow'), doc='gabled cabin 4x4', extra={'door': [2, 3]})
    S.object('icicles', SN.icicles(['ic0', 'ic1', 'ic2', 'ic3'], 'ic0'), solid='.', layer='top',
             doc='icicles (hang from eaves and lips)')
    S.object('woodpile', TP.woodpile(WOOD, ['k2', 'k3', 'k4'], 'k0'), doc='firewood 2x1')
    S.object('sled', SN.sled(WOOD, ['b1', 'b3'], 'k0'), doc='sled 2x1')
    S.object('lamp', TP.lamp_post(['b1', 'b2', 'b3'], 'b0', ['fo', 'fo', 'sn5']), top='X/.', solid='./X',
             doc='lantern post')
    S.object('signpost', PR.signpost(WOOD, 'k0'), attrs=['SIGN'], doc='trail sign')
    S.object('barrel', PR.barrel(WOOD, 'b1', 'k0'), doc='barrel')
    S.object('crate', PR.crate(WOOD, 'k0'), doc='crate')
    S.custom('fence', PR.fence_block(WOOD, 'k0', post_cap='sn5'), 'fence', layer='mid', attrs=['SOLID'],
             doc='snow-capped rail fence')

    kit.civic(S, LOG, ('gw2', 'gw1', 'gw0'), roof_style='snow', siding='log')
    S.object('bathhouse', B.house(80, 64, LOG, door_at=40, windows=[(6, 6), (62, 6)], gable=True, siding='log',
                                  roof_style='snow', door_w=12), doc='bathhouse 5x4 (by the hot spring)',
             extra={'door': [2, 3]})
    S.object('frost_banner', __import__('dungeonart').banner(['k0', 'fr', 'fr'], ['k1', 'k2', 'k3'], 'sn5', 'k0'),
             solid='./.', doc='frost banner 1x2 (on a wall or post)')

    S.section('wild')
    S.object('cave_mouth', X.cave_mouth(ROCK, 'b0', 'b0'), top='XXX/.../...', solid='.../XXX/X.X',
             doc='ice cave entrance 3x3', extra={'door': [1, 2]})
    S.object('ice_blocks', X.ice_blocks(['ic0', 'ic1', 'ic2', 'ic3'], 'ic0'), doc='ice blocks')
    S.object('wolf_statue', X.wolf_statue(['b1', 'b2', 'b3', 'b4'], 'b0', ['b1', 'b2', 'b3']), top='XX/../..',
             solid='../XX/XX', doc='wolf kin statue 2x3')
    S.object('ice_statue', X.ice_statue(['ic0', 'ic1', 'ic2', 'ic3'], 'ic0', ['b1', 'b2', 'b3']), top='XX/../..',
             solid='../XX/XX', doc='ice sculpture 2x3')
    S.object('rime_pillar', X.rime_pillar(['ic0', 'ic1', 'ic2', 'ic3'], ['b1', 'b2', 'b3'], 'b0'), top='X/./.',
             solid='./X/X', doc='rime-crusted pillar 1x3')
    S.object('sky_arch', X.sky_arch(['b1', 'b2', 'b3'], ['ic0', 'ic1', 'ic2', 'ic3'], 'b0'), top='XXX/.../...',
             solid='.../X.X/X.X', doc='sky arch 3x3 (Sky Isle)')
    S.object('ski_rack', X.ski_rack(['k1', 'k2', 'k3'], ['fr', 'k3', 'b3'], 'k0'), top='X/.', solid='./X',
             doc='ski rack 1x2')
    S.object('wash_bucket', X.wash_bucket(['k1', 'k2', 'k3'], 'b4', 'k0'), doc='wash bucket')
    S.object('snowman', SN.snowman(['sn1', 'sn2', 'sn3', 'sn4', 'sn5'], 'sn0', 'k0', 'gw1', ['fr', 'fr']),
             top='X/.', solid='./X', doc='snowman 1x2')
    S.object('cairn', SN.cairn(ROCK, 'b0', snow='sn5'), top='X/.', solid='./X', doc='trail cairn 1x2')
    S.object('ice_crystal', SN.ice_crystal(['ic0', 'ic1', 'ic2', 'ic3'], 'ic0'), top='X/.', solid='./X',
             doc='ice crystal 1x2')
    S.object('aurora_stone', PR.standing_stone(['b1', 'b2', 'b3', 'b4'], 'b0', seed=4, rune='au2'), top='X/.',
             solid='./X', doc='aurora stone 1x2 (glowing rune)')
    kit.rocks(S, ROCK, 'b0')
    stm = [SN.steam(['sn3', 'sn4', 'sn5'], f) for f in range(4)]
    S.object('steam', stm[0], frames=stm, period=12, solid='./.', layer='top', doc='rising steam 1x2 (animated)')
    hs = [SN.hot_spring(['hs0', 'hs1', 'hs2'], ['b0', 'b2', 'b3', 'b4'], 'sn5', 'b0', f) for f in range(3)]
    S.object('hot_spring', hs[0], frames=hs, period=16, solid='XXX/XXX', doc='hot spring pool 3x2')

    S.scene(frost_scene())
    return S


def frost_scene():
    sc = Scene('frosthollow', 'Frosthollow (sample)', 36, 26, 'snow',
               doc='A snowbound village: cabins with lit windows, a lodge, a frozen lake with an ice '
                   'sheet, a steaming hot spring under the cliffs, cairns and snowbanks.')
    L = {'.': 'snow', '=': 'trail', '~': 'ice_hole', 'D': 'ice_hole', 'i': 'ice_patch', 't': 'tundra_patch',
         '^': 'cliff_top', '#': 'cliff_face', 'P': ('pine_forest', 'over'), 'B': ('snowbank', 'over')}
    sc.rows('''
PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
PPPPPPPPPPPPP^^^^^^^^^^^^^PPPPPPPPPP
PP...........^^^^^^^^^^^^^......PPPP
PP...........^^^^^^^^^^^^^.......PPP
P............#############........PP
P............#############.........P
P..................................P
P...===========================....P
P...=............=............=....P
P...=............=............=....P
P...=............=............=....P
P...=..BBBB......=.............=...P
P...=............=.....iiiiii..=...P
P...=............=....iiii~~ii.=...P
P...=............=...iii~~~~~i.=...P
P.====================ii~~DD~~ii=..P
P...=........=.......iii~~~~~i..=..P
P...=........=........iii~~~iii.=..P
P...=........=.........iiiiii...=..P
P...=...tttt.=..................=..P
P...=...tttt.=..................=..P
PP..=........=....BBBBB.........=.PP
PPP.=........=..................=PPP
PPPP=PPPPPPPP=PPPPPPPPPPPPPPPPPP=PPP
PPPP=PPPPPPPP=PPPPPPPPPPPPPPPPPP=PPP
PPPP=PPPPPPPP=PPPPPPPPPPPPPPPPPP=PPP
''', L)
    obj = [('lodge', 6, 1), ('cabin', 27, 2), ('cabin_gable', 5, 11),
           ('cabin', 14, 16), ('hot_spring', 18, 5), ('steam', 19, 4), ('steam', 21, 4), ('stairs', 16, 4),
           ('woodpile', 11, 7), ('sled', 9, 15), ('lamp', 16, 8), ('lamp', 12, 14), ('signpost', 18, 14),
           ('snowman', 24, 9), ('cairn', 33, 11), ('cairn', 2, 19), ('ice_crystal', 29, 20), ('aurora_stone', 33, 17),
           ('pine', 2, 6), ('pine_small', 20, 19), ('pine_small', 32, 5),
           ('dead_tree', 8, 20), ('shrub', 30, 16), ('rock', 26, 20), ('boulder', 23, 21), ('barrel', 13, 7)]
    for (n, x, y) in obj:
        sc.put(n, x, y)
    sc.sprinkle(['pebbles', 'rock', 'shrub', 'pebbles'], 12, on={'snow'}, seed=5)
    return sc
