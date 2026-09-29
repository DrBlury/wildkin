"""VERDANT - temperate meadows, woods, lakes and hills.

Replaces the old `wild` tileset (Whisper Meadow, Bramblewood, Mirror Lake,
Stormstone Rise, Brookmill Trail, Copperline Road, Elderwood, Foothills,
Mistfall Gorge, Rootwood Path). `hamlet` (villages) and `farm` reuse its
ground, water and cliff palette so their maps join seamlessly.
"""

from core import Img
from sheet import Sheet, Scene
import paint as P
import terrain as T
import flora as F
import props as PR
import caveart as CA
import extras as X
import buildings as B
import kit

# ---------------------------------------------------------------------------
# palette: hue-shifted ramps (shadows cooler, highlights warmer)
# ---------------------------------------------------------------------------

PALETTE = {
    # meadow grass
    'g0': '#183c30', 'g1': '#2c6838', 'g2': '#4a9444', 'g3': '#6cb454', 'g4': '#94d068', 'g5': '#c4e890',
    # dirt / path
    'd0': '#4c3024', 'd1': '#7c5234', 'd2': '#a8784c', 'd3': '#cca068', 'd4': '#e4c088', 'd5': '#f4dcac',
    # fresh water
    'w0': '#203c7c', 'w1': '#3060b0', 'w2': '#4884d8', 'w3': '#70acf0', 'w4': '#a8d4f8', 'w5': '#e8f8ff',
    # cliff rock (warm brown)
    'r0': '#3a2426', 'r1': '#62392e', 'r2': '#8a5838', 'r3': '#b27c4c', 'r4': '#d2a266', 'r5': '#eac68c',
    # grey stone (boulders, steps, standing stones)
    's0': '#26283a', 's1': '#474c5c', 's2': '#686f7e', 's3': '#8e96a0', 's4': '#b6bcc0', 's5': '#dcdedc',
    # broadleaf foliage (bluer and deeper than grass so trees stand out)
    't0': '#123028', 't1': '#1c4c34', 't2': '#28683c', 't3': '#3c8a44', 't4': '#5eac4c', 't5': '#8ccc60',
    # conifer needles
    'p0': '#0e2a2c', 'p1': '#16443c', 'p2': '#205e48', 'p3': '#2e7c52', 'p4': '#48a060',
    # bark / wood
    'k0': '#2c1a1c', 'k1': '#553428', 'k2': '#7e5236', 'k3': '#a8764a', 'k4': '#c89a64',
    # roofs and glass for cabins and the lift/tram station
    'ra0': '#5c1a28', 'ra1': '#8c2a34', 'ra2': '#bc443e', 'ra3': '#e06a4c', 'ra4': '#f49a6c',
    'gl0': '#2c4474', 'gl1': '#6494cc', 'gl2': '#dcf0ff',
    # copper ore (Copperline Road)
    'co0': '#8c4424', 'co1': '#d07034', 'co2': '#f8b060',
    # flowers, fruit, cloth
    'fr': '#e04040', 'frd': '#a02840', 'fy': '#f8d030', 'fyd': '#c89020', 'fw': '#f8f8f0',
    'fp': '#f088b0', 'fpd': '#b85080', 'fb': '#6c8cf0', 'fbd': '#4058b0', 'fo': '#f09040',
}

# Autumn: the same tiles, warmer grass and foliage (swap palette at run time).
AUTUMN = {
    'g1': '#5a5a30', 'g2': '#8a8a40', 'g3': '#b0a650', 'g4': '#d0c068', 'g5': '#e8dc90',
    't1': '#6a2c24', 't2': '#9a3c28', 't3': '#c85c30', 't4': '#e88a3c', 't5': '#f8b85c',
    'p2': '#3a5a40', 'p3': '#4a7048',
}
SPRING = {
    'g3': '#74bc5c', 'g4': '#a0d874', 'g5': '#d4f0a0',
    't3': '#48a050', 't4': '#74c460', 't5': '#b4e490',
}

GRASS = {'dk': 'g1', 'mid': 'g2', 'base': 'g3', 'lt': 'g4', 'hi': 'g5', 'out': 'g0'}
TALL = {'out': 'g0', 'dk': 'g1', 'mid': 'g2', 'base': 'g3', 'lt': 'g4', 'hi': 'g5'}
DIRT = {'dk': 'd1', 'mid': 'd2', 'base': 'd3', 'lt': 'd4', 'hi': 'd5'}
WATER = {'deep': 'w1', 'base': 'w2', 'lt': 'w3', 'hi': 'w4', 'foam': 'w5', 'dark': 'w0'}
ROCK = ['r1', 'r2', 'r3', 'r4', 'r5']
STONE = ['s1', 's2', 's3', 's4', 's5']
LEAF = ['t0', 't1', 't2', 't3', 't4', 't5']
PINE = ['p0', 'p1', 'p2', 'p3', 'p4']
BARK = ['k1', 'k2', 'k3']
WOOD = ['k0', 'k1', 'k2', 'k3', 'k4']


# GBA palette banks by material (15 colours each; index 0 = transparent).
BANKS = [
    ['g0', 'g1', 'g2', 'g3', 'g4', 'g5', 'd0', 'd1', 'd2', 'd3', 'd4', 'd5', 's1', 's3', 's5'],   # ground
    ['g0', 'g1', 'g2', 'g3', 'g4', 'g5', 'w0', 'w1', 'w2', 'w3', 'w4', 'w5'],                     # water
    ['g0', 'g1', 'g2', 'g3', 'g4', 'g5', 'r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'co0', 'co1', 'co2'],  # cliffs, ore
    ['g1', 'g2', 'g3', 'g4', 'g5', 'fr', 'frd', 'fy', 'fyd', 'fw', 'fp', 'fpd', 'fb', 'fbd', 'fo'],  # flowers
    ['t0', 't1', 't2', 't3', 't4', 't5', 'k0', 'k1', 'k2', 'k3', 'k4', 'fr', 'frd', 'fp', 'fw'],  # foliage
    ['p0', 'p1', 'p2', 'p3', 'p4', 'k0', 'k1', 'k2', 'k3'],                                     # conifers
    ['s0', 's1', 's2', 's3', 's4', 's5', 'k0', 'k1', 'k2', 'k3', 'k4', 'fr', 'fy', 'fo', 'fw'],  # props
    ['ra0', 'ra1', 'ra2', 'ra3', 'ra4', 'k0', 'k1', 'k2', 'k3', 'gl0', 'gl1', 'gl2'],  # huts
]


def grounds():
    base = P.grass(GRASS, 1, tufts=3, flecks=3)
    return {
        'grass': base,
        'grass_b': P.grass(GRASS, 2, tufts=5, flecks=4),
        'grass_c': P.grass(GRASS, 3, tufts=2, flecks=5),
        'grass_d': P.grass(GRASS, 4, tufts=4, flecks=2),
        'grass_flowers': P.grass(GRASS, 5, tufts=2, flecks=2,
                                 flowers={'n': 2, 'petals': ['fw', 'fy'], 'center': 'fy'}),
        'grass_pebbles': P.grass(dict(GRASS, peb='s3', peb_hi='s5', peb_dk='s1'), 6, tufts=2, flecks=2,
                                 pebbles=2),
        'dirt': P.speckle_ground(DIRT, 5, dots=8, pebbles=1),
        'dirt_b': P.speckle_ground(DIRT, 8, dots=10, pebbles=2),
        'dirt_c': P.speckle_ground(DIRT, 9, dots=6, pebbles=0, cracks=1),
    }


def build():
    S = Sheet('verdant', 'Verdant - meadows, woods, lakes', PALETTE,
              variants={'autumn': AUTUMN, 'spring': SPRING}, banks=BANKS, doc=__doc__)
    g = grounds()
    grass = g['grass']

    # -- ground -----------------------------------------------------------
    S.section('ground')
    S.tile('grass', grass, group='grass', weight=9, doc='meadow grass (main variant)')
    S.tile('grass_b', g['grass_b'], group='grass', weight=4, doc='grass, more tufts')
    S.tile('grass_c', g['grass_c'], group='grass', weight=3, doc='grass, sunny flecks')
    S.tile('grass_d', g['grass_d'], group='grass', weight=3, doc='grass variant')
    S.tile('grass_flowers', g['grass_flowers'], group='grass', weight=1, doc='grass with two tiny flowers')
    S.tile('grass_pebbles', g['grass_pebbles'], group='grass', weight=1, doc='grass with pebbles')
    S.tile('dirt', g['dirt'], group='dirt', weight=6, doc='bare earth')
    S.tile('dirt_b', g['dirt_b'], group='dirt', weight=3)
    S.tile('dirt_c', g['dirt_c'], group='dirt', weight=1, doc='dry crack')
    # tall grass: encounter habitat + blade tips drawn above people
    tg = F.tallgrass(TALL)
    S.tile('tallgrass', tg, frames=[tg, F.tallgrass(TALL, sway=1), tg, F.tallgrass(TALL, sway=-1)],
           attrs=['GRASS'], period=24, doc='encounter grass (gentle sway)')
    S.object('tallgrass_top', F.tallgrass_top(TALL), top='X', solid='.', layer='top',
             doc='blade tips over a person standing in tall grass')

    # -- autotiles ----------------------------------------------------------
    S.section('autotiles')
    S.autotile('path', T.material_autotile(g['dirt'], grass, rim_in='d2', rim_out='g2', lip='d4',
                                           seed=2, inner_alt=g['dirt_b']),
               over='grass', doc='dirt path over grass (engine path_q)')
    S.autotile('tallgrass_patch', T.material_autotile(tg, grass, rim_out='g2', seed=4, E=3.0, R=3.5),
               over='grass', attrs=['GRASS'], doc='tall grass with soft edges')
    wf = [T.water_autotile(WATER, grass, f, edge='g0', wet='g2') for f in range(4)]
    S.autotile('water', wf[0], frames=wf, over='grass', attrs=['WATER'], period=20,
               doc='pond / lake over grass, 4-frame ripples (engine water_q)')
    deep = [T.material_autotile(T.water_surface(dict(WATER, base='w1', deep='w0', lt='w2', hi='w3'), f, seed=5),
                                T.water_surface(WATER, f), rim_in='w0', rim_out='w3', seed=7, E=3.0,
                                amp=1.2, dither=0.0)
            for f in range(4)]
    S.autotile('deep_water', deep[0], frames=deep, over='water', attrs=['WATER', 'DEEP'], period=20,
               doc='deep water (dive / darker channel) inside water')
    S.autotile('dirt_patch', T.material_autotile(g['dirt'], grass, rim_out='g2', seed=11, amp=1.3,
                                                 inner_alt=g['dirt_c']),
               over='grass', doc='worn earth patch (blend)')

    # -- flowers --------------------------------------------------------------
    S.section('flowers')
    for name, (pt, pd, ce, kind) in {
            'flowers_red': ('fr', 'frd', 'fy', 'tulip'),
            'flowers_yellow': ('fy', 'fyd', 'fo', 'daisy'),
            'flowers_white': ('fw', 's3', 'fy', 'daisy'),
            'flowers_pink': ('fp', 'fpd', 'fw', 'tulip'),
            'flowers_blue': ('fb', 'fbd', 'fw', 'bell')}.items():
        fr = [F.flower_patch(grass, pt, pd, ce, 'g2', frame=f, seed=sum(map(ord, name)) % 97, kind=kind)
              for f in range(2)]
        S.tile(name, fr[0], frames=fr, period=32, group='flowers', doc='flower patch (sways)')

    # -- elevation ------------------------------------------------------------
    S.section('elevation')
    face = T.lump_texture(ROCK, 32, 32, 1, rx=5.5, ry=4.2, sx=8, sy=6.5)
    S.autotile('cliff_top', T.cliff_rim(grass, grass, ROCK, 'r0', face_tex=face, bevel='g4', drip='g2'),
               over='grass', attrs=[], doc='upper level of a plateau: rims on every side; the south '
               'side continues into cliff_face below it')
    S.patch9('cliff_face', T.cliff_face(ROCK, 'r0', grass, tufts=['g2', 'g4'], tex=face,
                                        tex2=T.lump_texture(ROCK, 32, 32, 9, rx=5.5, ry=4.2, sx=8, sy=6.5)),
             attrs=['SOLID'], doc='cliff face under a plateau (>= 2 rows: top row, repeat middle, foot)')
    S.custom('cliff_face_single', T.cliff_face_single(ROCK, 'r0', grass, face, tufts=['g2', 'g4']), 'strip4',
             attrs=['SOLID'], doc='one-row face (a single level of drop): [W end][mid][E end][lone]')
    S.custom('ledge', T.ledge_block(grass, ['g5', 'g4', 'r3', 'r2', 'r0', 'g1']), 'ledge',
             attrs=['LEDGE'], doc='one-way hop-down ledges: row 0 south (W end, mid, E end, single), '
             'row 1 east-facing (N end, mid, S end, SE corner), row 2 west-facing')
    S.object('stairs', T.stairs('s4', 's3', 's1', 's0', 's2', 1, 2), solid='./.', layer='ground',
             doc='stone steps cut into a 2-row cliff face')
    S.object('stairs_wide', T.stairs('s4', 's3', 's1', 's0', 's2', 2, 2), solid='../..',
             layer='ground', doc='wide stone steps')
    S.object('stairs_wood', T.stairs('k4', 'k3', 'k1', 'k0', 'k2', 1, 2), solid='./.', layer='ground',
             doc='wooden steps')

    # -- water features ---------------------------------------------------------
    S.section('water features')
    fall = [T.waterfall(WATER, ROCK, f) for f in range(4)]
    S.object('waterfall', fall[0], frames=fall, period=8, solid='XX/XX/XX', layer='ground',
             attrs=['WATER'], doc='2x3 falls; the bottom row foams into the pool')
    S.object('lily_pads', F.lily_pad(['g1', 'g2', 'g4'], 'g1'), solid='.', floor=None,
             doc='lily pads (decor on water)')
    S.object('lily_flower', F.lily_pad(['g1', 'g2', 'g4'], 'g1', flower=('fp', 'fw')), solid='.')
    S.object('reeds', F.reeds(['g1', 'g2', 'g4'], h=16, heads=('k1', 'k2', 'k3')), solid='X',
             doc='cattails at the water edge')
    stones = Img(16, 16)
    stones.paste(PR.rock(16, 16, STONE, 's0', 3, parts=[(8, 9, 6, 4.5)]), 0, 0)
    S.object('stepping_stone', stones, solid='.', floor='X', doc='walkable stone in shallow water')
    S.object('water_rock', PR.rock(16, 16, STONE, 's0', 5, parts=[(8, 9, 6.5, 5), (5, 7, 3, 2.5)]),
             doc='rock jutting out of water')

    # -- trees ---------------------------------------------------------------------
    S.section('trees')
    kit.broadleaf(S, LEAF, 't0', BARK, 'k0', fruit=('fr', 'frd', 7), big=True, forest=False)
    S.object('pine', F.conifer(32, 48, PINE, 'p0', BARK, 'k0', seed=2, tiers=5), top='XX/XX/..',
             solid='../../XX', doc='tall pine 2x3')
    S.object('pine_small', F.conifer(16, 32, PINE, 'p0', BARK, 'k0', seed=3, tiers=4), top='X/.',
             solid='./X', doc='young pine 1x2')
    S.object('dead_tree', F.dead_tree(32, 32, ['k1', 'k2', 'k3'], 'k0', seed=4), top='XX/..', solid='../XX',
             doc='bare tree 2x2')
    S.patch9('forest', F.forest_wall(LEAF, 't0', BARK, 'k0', seed=1), layer='mid', attrs=['SOLID'],
             doc='dense broadleaf woods (mass layer over any ground; trunks on the south edge)')
    S.patch9('pine_forest', F.forest_wall(PINE, 'p0', BARK, 'k0', seed=2, r=4.8), layer='mid',
             attrs=['SOLID'], doc='dense pine woods')

    # -- shrubs ------------------------------------------------------------------------
    S.section('shrubs')
    S.object('bush', F.bush(16, 16, LEAF, 't0', seed=1), doc='round bush (cuttable)')
    S.object('bush_berry', F.bush(16, 16, LEAF, 't0', seed=2, berries=('fr', 'frd', 4)), doc='berry bush')
    S.object('bush_flower', F.bush(16, 16, LEAF, 't0', seed=3, flowers=('fp', 'fw', 4)), doc='flowering shrub')
    S.object('bush_wide', F.bush(32, 16, LEAF, 't0', seed=4), doc='long shrub 2x1')
    S.patch9('hedge', F.hedge_wall(LEAF, 't0', seed=3, base='t1'), layer='mid', attrs=['SOLID'],
             doc='clipped hedge / maze wall')
    S.object('stump', F.stump(['k1', 'k2', 'k3'], 'k0', 'k4', 'k2'), doc='tree stump')
    S.object('log', F.log_h(['k1', 'k2', 'k3', 'k4'], 'k0', 'k4', 'k2', moss=('t3', 't4')), doc='fallen log 2x1')
    S.object('mushrooms', F.mushrooms('fr', 'frd', 'fw', 'k4', 'k0'), solid='.', doc='toadstools (decor)')
    S.object('fern', F.bush(16, 16, ['t0', 't1', 't2', 't3', 't4'], 't0', seed=9, n=7), solid='.',
             doc='fern clump (walkable decor)')

    # -- rocks ------------------------------------------------------------------------
    S.section('rocks')
    S.object('rock', PR.small_rock(STONE, 's0', 1), doc='small rock')
    S.object('boulder', PR.boulder(STONE, 's0', 2), doc='push boulder (strength)')
    S.object('rock_cracked', PR.cracked_rock(STONE, 's0', 3), doc='breakable rock')
    S.object('rock_big', PR.big_rock(STONE, 's0', 4), doc='crag 2x2')
    S.object('pebbles', PR.pebbles(STONE, 's0', 5), solid='.', doc='pebbles (decor)')
    S.object('standing_stone', PR.standing_stone(STONE, 's0', seed=6), top='X/.', solid='./X',
             doc='menhir 1x2')
    S.object('stormstone', PR.standing_stone(STONE, 's0', seed=7, rune='fy'), top='X/.', solid='./X',
             doc='rune stone 1x2 (Stormstone Rise)')

    # -- man-made -----------------------------------------------------------------------
    S.section('camp and trail')
    S.object('signpost', PR.signpost(WOOD[1:], 'k0'), attrs=['SIGN'], doc='route sign')
    S.object('arrow_sign', PR.arrow_sign(WOOD[1:], 'k0'), attrs=['SIGN'], doc='direction arrow')
    S.object('notice_board', PR.notice_board(WOOD[1:], 'k0', 'fw', 's3', 'fr'), top='XX/..',
             solid='../XX', attrs=['SIGN'], doc='notice board 2x2')
    S.custom('fence', PR.fence_block(WOOD[1:], 'k0'), 'fence', layer='mid', attrs=['SOLID'],
             doc='rail fence: row 0 [post][W end][mid][E end], row 1 [N end][mid][S end][gate]')
    S.object('bridge_h', PR.bridge_h(WOOD[1:], 'k0'), floor='XXX/XXX', solid='.../...',
             doc='plank bridge east-west 3x2 (extend by repeating the middle column)')
    S.object('bridge_v', PR.bridge_v(WOOD[1:], 'k0'), floor='XX/XX/XX', solid='../../..',
             doc='plank bridge north-south 2x3')
    S.patch9('dock', PR.dock_block(WOOD[1:], 'k0', 'k1'), layer='ground', attrs=[],
             doc='pier decking over water (floor)')
    cf = [PR.campfire(WOOD[1:], 'k0', ('fy', 'fo', 'fr'), f) for f in range(3)]
    S.object('campfire', cf[0], frames=cf, period=10, doc='campfire (animated)')
    S.object('tent', PR.tent('fo', 'fr', 'k0', 'k2'), top='XX/..', solid='../XX', doc='camp tent 2x2')
    S.object('barrel', PR.barrel(WOOD[1:], 's1', 'k0'), doc='barrel')
    S.object('crate', PR.crate(WOOD[1:], 'k0'), doc='crate')


    S.section('outdoor furniture')
    kit.outdoor(S, {'wood': WOOD, 'out': 'k0', 'stone': STONE, 'stone_out': 's0', 'metal': ['s1', 's2', 's3'],
                    'red': 'fr', 'yellow': 'fy', 'orange': 'fo', 'white': 'fw', 'cloth': ['k1', 'fr', 'fo'],
                    'roof': ['k1', 'k2', 'k3'], 'hay': ['k2', 'fy', 'fw'], 'glow': ['fo', 'fy'],
                    'leaf': ['g1', 'g2', 'g3', 'g4']})
    S.object('crystal_cluster', CA.crystal(['s1', 's3', 's4', 's5'], 's0'), doc='quartz cluster')
    gc = [CA.glowcaps(['fo', 'fo', 'fy'], 'k3', 'fw', 'k0', f) for f in range(2)]
    S.object('glowcaps', gc[0], frames=gc, period=30, solid='.', doc='glowcap mushrooms (pulse)')
    bu = [__import__('coastart').buoy(['k1', 'fr', 'fr'], ['k1', 'fw', 'fw'], 'k0', f) for f in range(2)]
    S.object('buoy', bu[0], frames=bu, period=30, doc='lake buoy (on water)')
    rf = [X.river_foam(['w5', 'w4'], f) for f in range(3)]
    S.object('river_foam', rf[0], frames=rf, period=10, solid='.', doc='white water foam over a river (anim)')

    S.object('bench', __import__('townprops').bench(WOOD, ['s1', 's2'], 'k0'), doc='bench 2x1')
    S.object('sacks', __import__('townprops').sacks(['k2', 'k3', 'k4'], 'k0', 'k1'), doc='sacks')
    S.object('trough', __import__('townprops').trough(WOOD, ['s1', 's2', 's4'], 'k0'), doc='water trough 2x1')
    S.object('weather_vane', __import__('townprops').weather_vane(['s1', 's2', 's3'], 's0', 'k3'), top='X/.',
             solid='./X', doc='weather vane 1x2')
    S.object('well', __import__('townprops').well(['s1', 's2', 's3', 's4'], WOOD, ['s0', 's1'], 'k0',
                                                  ['k1', 'k2', 'k3', 'k4']), top='XX/..', solid='../XX', doc='well 2x2')
    S.object('bollard', PR.barrel(['k1', 'k2', 'k3', 'k4'], 'k0', 'k0'), doc='mooring post')
    import farmart as FA
    CROPV = {'leaf': ['t1', 't2', 't3', 't4'], 'out': 't0', 'gold': ['k2', 'k2', 'k4', 'fw'],
             'orange': ['k1', 'k1', 'fr', 'k4'], 'red': ['k1', 'fr', 'fo'], 'stake': ['k1', 'k2'],
             'glow': ['k2', 'fr', 'fr', 'fy'], 'root': {}}
    for kind in ('wheat', 'pumpkin', 'sunflower'):
        S.object('crop_%s_3' % kind, FA.crop(kind, 3, CROPV), solid='.', doc='%s (grown, decor)' % kind)

    S.section('mine and huts')
    S.object('mine_mouth', X.mine_mouth(ROCK, ['r1', 'r3', 'r4'], 'r0', 'r0'), solid='XXX/X.X', doc='adit entrance 3x2 (door '
             'in the bottom middle)', extra={'door': [1, 1]})
    S.object('headframe', X.headframe(WOOD, ['s1', 's2', 's3'], 'k0'), top='XXX/XXX/.../...',
             solid='.../.../XXX/XXX', doc='mine headframe 3x4')
    S.custom('rails', CA.rails_block(['s1', 's2', 's4'], WOOD, 'k0'), 'rails', layer='mid',
             doc='mine rails: row 0 [E-W][N-S][curve S-E][curve S-W], row 1 [curve N-E][curve N-W][buffer][cross]')
    S.object('ore_cart', CA.mine_cart(['r1', 'r2', 'r4'], 'r0', ore=['co0', 'co1', 'co2']), doc='ore cart')
    S.object('ore_pile', X.ore_pile(ROCK, ['co0', 'co1', 'co2'], 'r0'), doc='ore heap 2x1')
    S.object('copper_rock', CA.ore_rock(ROCK, ['co0', 'co1', 'co2'], 'r0', 3), doc='copper-veined rock')
    LOGH = {'out': 'k0', 'roof': ['ra0', 'ra1', 'ra2', 'ra3', 'ra4'], 'wall': ['k1', 'k2', 'k3'],
            'trim': ['k0', 'k1', 'k2'], 'glass': ['gl0', 'gl1', 'gl2'], 'found': ['k0', 'k1', 'k2'],
            'chimney': ['k0', 'k1', 'k2'], 'door': ['k0', 'k1', 'k2']}
    S.object('cabin', B.house(64, 64, LOGH, door_at=40, windows=[(8, 6)], chimney=12, siding='log'),
             doc='log cabin 4x4', extra={'door': [2, 3]})
    S.object('station', B.house(96, 64, LOGH, door_at=48, windows=[(8, 6), (74, 6)], siding='plank', roof_style='tile',
                                door_w=18), doc='lift / tram station 6x4', extra={'door': [3, 3]})

    S.scene(meadow_scene())
    return S


def meadow_scene():
    """Whisper-Meadow-like route: woods frame it, a river falls from the
    pine hills and is bridged by the trail, a raised hill with stairs and
    standing stones, a lily pond with a jetty, a camp, a fenced cabin."""
    sc = Scene('route', 'Verdant route (sample)', 40, 30, 'grass',
               doc='A redesigned Whisper Meadow: woods frame the route, a waterfall feeds a river '
                   'the trail bridges, a hill with stairs and menhirs, a lily pond with a jetty, '
                   'a camp and a fenced cabin, tall-grass habitats and flower meadows.')
    L = {
        '.': 'grass', ',': 'tallgrass_patch', '=': 'path', '~': 'water', 'D': 'deep_water',
        '^': 'cliff_top', '#': 'cliff_face', ':': 'dirt_patch', 'f': 'flowers',
        'F': ('forest', 'over'), 'P': ('pine_forest', 'over'),
    }
    sc.rows('''
FFFFFFFFFFFFFFFFF===FFFFFFFFF^^^^^^^PPPP
FFFFFFFFFFFFFFF....===FFFFFF^^^^^^^^^PPP
FFFF^^^^^^^^^.......===.FFF.^^^^^^^^^PPP
FFF.^^^^^^^^^..,,,...===....#########.PP
FF..^^^^^^^^^.,,,,,...===...#########..P
FF..^^^^^^^^^..,,,.....===....~~~~.....P
F...#########...........===..~~~~~......
F...#########...ff.......==..~~DD~~.....
F..............fff.......===.~~DD~~.....
F.....ff........f.........==~~~DD~~.....
F....fff..................=======~====..
F.........,,,,............===~~~~~~~===.
F........,,,,,,..........===.~~~~~~..===
FF........,,,,..........===...~~~~~...==
FF.....................===.....~~~~.....
F.....::::............===.......~~~~....
F....::::::..........===.........~~~~...
F.....::::..........===...........~~~~..
F..................===.....,,,,....~~~~.
F.................===.....,,,,,,....~~~~
FF...............===.......,,,,......~~~
FF..~~~~~.......===...................~~
F..~~~~~~~.....===...........fff......~~
F..~~DDD~~~...===...........fffff......~
F...~~DD~~....===............fff........
F....~~~~....===......................FF
FF..........===....................FFFFF
FFF........===...FFFFFFFFF......FFFFFFFF
FFFFFFFFF..==.FFFFFFFFFFFFFFFFFFFFFFFFFF
FFFFFFFFF..==FFFFFFFFFFFFFFFFFFFFFFFFFFF
''', L)
    obj = [
        # the hill: stairs through its face, menhirs on top
        ('stairs', 8, 6), ('standing_stone', 6, 2), ('stormstone', 9, 2), ('standing_stone', 11, 3),
        # waterfall off the pine ridge into the river
        ('waterfall', 30, 3), ('water_rock', 29, 5), ('reeds', 28, 6),
        # the trail bridge
        ('bridge_h', 29, 9),
        # camp on the worn earth
        ('tent', 5, 14), ('campfire', 8, 16), ('log', 9, 17), ('crate', 4, 16), ('woodpile', 10, 14),
        # pond with a jetty and boat
        ('lily_pads', 5, 22), ('lily_flower', 7, 21), ('reeds', 3, 21), ('reeds', 9, 24), ('rowboat', 5, 25),
        # a fenced cabin in the south-east
        ('cabin', 30, 20), ('well', 27, 20),
        # trees in clusters
        ('tree_big', 14, 12), ('tree', 18, 3), ('tree_b', 13, 22), ('tree_small', 17, 22), ('tree', 34, 12),
        ('tree_fruit', 36, 15), ('tree_small', 22, 16), ('pine', 36, 5), ('pine_small', 38, 8), ('dead_tree', 1, 18),
        # route furniture
        ('signpost', 17, 1), ('arrow_sign', 27, 11), ('notice_board', 20, 5), ('bench', 11, 20),
        ('lantern_post', 24, 13), ('boulder', 21, 8), ('rock_cracked', 33, 16), ('rock_big', 2, 11),
        ('stump', 12, 9), ('mushrooms', 13, 9), ('bush_berry', 19, 9), ('bush', 3, 8), ('bush_flower', 16, 18),
        ('shrine', 34, 24), ('picnic_table', 21, 22),
    ]
    for (n, x, y) in obj:
        sc.put(n, x, y)
    for x in range(26, 34):
        sc.put('fence:2,0', x, 19)
    sc.put('fence:0,0', 25, 19)
    sc.put('fence:0,0', 34, 19)
    sc.sprinkle(['small_flowers', 'pebbles', 'fern', 'small_flowers', 'mushrooms'], 34, on={'grass'}, seed=3)
    sc.sprinkle(['fallen_leaves'], 4, on={'grass'}, seed=9)
    return sc
