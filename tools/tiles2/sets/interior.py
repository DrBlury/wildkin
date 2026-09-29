"""INTERIOR - homes, shops, Hearth Halls, inns, workshops and studies.

Replaces the old `interior` tileset (every house, shop, hall and lodge).
Plank, checker and stone floors; back walls in four wallpapers over a
wainscot (two rows: wall_*_top and wall_*_low); windows, doors, stairs,
counters; furniture drawn with a lit top and a darker front, the Hearth
Hall flame, the storage terminal, shelves of goods and workshop machines.
"""

from core import Img
from sheet import Sheet, Scene
import paint as P
import terrain as T
import props as PR
import townprops as TP
import interiorart as IN
import dungeonart as DG
import extras as X
import kit

PALETTE = {
    'v0': '#08080c', 'wt0': '#1c1418', 'wt1': '#2c2026',
    'fw0': '#4c3020', 'fw1': '#7c5234', 'fw2': '#a47448', 'fw3': '#c8966a',
    'ck0': '#8c8478', 'ck1': '#d8d0c0', 'ck2': '#f4ece0',
    'sf0': '#4c4848', 'sf1': '#6c6664', 'sf2': '#8c8680', 'sf3': '#aca69c',
    'pc0': '#b09c7c', 'pc1': '#e8dcb8', 'pc2': '#fcf4dc',
    'pb0': '#3c4c7c', 'pb1': '#5c74b0', 'pb2': '#8ca4d8',
    'pg0': '#3c5c44', 'pg1': '#5c845c', 'pg2': '#8cb484',
    'pr0': '#7c3c34', 'pr1': '#a45c48', 'pr2': '#c88468',
    'k0': '#2c1a1c', 'k1': '#553428', 'k2': '#7e5236', 'k3': '#a8764a', 'k4': '#c89a64',
    'rd0': '#5c1424', 'rd1': '#9c2c34', 'rd2': '#d0504c', 'rd3': '#f0a060',
    'bl0': '#1c2c5c', 'bl1': '#34509c', 'bl2': '#6c8cd8',
    'lf0': '#1c4430', 'lf1': '#2c6c3c', 'lf2': '#4c9848', 'lf3': '#84c460',
    'm0': '#2c2c38', 'm1': '#545868', 'm2': '#8c90a0',
    'sk0': '#6ca0d8', 'sk1': '#b8dcf8', 'gl': '#f0fcff',
    'fo': '#e86c24', 'fy': '#f8c040', 'fw': '#fff4c0',
    'sc0': '#1c3c2c', 'sc1': '#3cb468', 'sc2': '#9cf0b0',
}
# Evening: lamplight and fire warm the rooms.
EVENING = {'pc1': '#d8bc94', 'pc2': '#ecd4ac', 'ck1': '#c8b498', 'ck2': '#e0ccb0', 'fw2': '#946044', 'fw3': '#b47e58',
           'sk0': '#3c4c7c', 'sk1': '#6c7cb0'}

BANKS = [
    ['v0', 'wt0', 'wt1', 'fw0', 'fw1', 'fw2', 'fw3', 'ck0', 'ck1', 'ck2', 'sf0', 'sf1', 'sf2', 'sf3', 'k0'],
    ['pc0', 'pc1', 'pc2', 'pb0', 'pb1', 'pb2', 'k0', 'k1', 'k2', 'k3', 'wt0', 'wt1', 'sk0', 'sk1', 'gl'],
    ['pg0', 'pg1', 'pg2', 'pr0', 'pr1', 'pr2', 'k0', 'k1', 'k2', 'k3', 'wt0', 'wt1', 'sk0', 'sk1', 'gl'],
    ['k0', 'k1', 'k2', 'k3', 'k4', 'rd0', 'rd1', 'rd2', 'rd3', 'bl0', 'bl1', 'bl2', 'pc1', 'pc2', 'fy'],
    ['k0', 'k1', 'k2', 'k3', 'lf0', 'lf1', 'lf2', 'lf3', 'rd1', 'rd2', 'bl1', 'pc0', 'pc1', 'pc2', 'fy'],
    ['m0', 'm1', 'm2', 'sc0', 'sc1', 'sc2', 'fo', 'fy', 'fw', 'sf0', 'sf1', 'sf2', 'sf3', 'rd1', 'k0'],
    ['fw0', 'fw1', 'fw2', 'fw3', 'rd0', 'rd1', 'rd2', 'rd3', 'bl0', 'bl1', 'bl2', 'fy', 'k0', 'ck2'],
    ['bl0', 'bl1', 'bl2', 'ck0', 'ck1', 'ck2', 'fy', 'k0', 'k1', 'k2', 'k3', 'k4', 'fw2', 'fw3', 'm1'],
]

WOOD = ['k1', 'k2', 'k3']
DARK = ['k0', 'k1', 'k2']
FABRIC_R = ['rd0', 'rd1', 'rd2']
FABRIC_B = ['bl0', 'bl1', 'bl2']
METAL = ['m0', 'm1', 'm2']
BOOKS = [('rd0', 'rd1', 'rd2'), ('bl0', 'bl1', 'bl2'), ('k1', 'k2', 'k3'), ('rd1', 'rd2', 'rd3'), ('k1', 'fy', 'pc2')]


def add_wall(S, name, paper, pattern, doc):
    tex = IN.wall_face(paper, ['k1', 'k2', 'k3'], ['k0', 'k1'], pattern=pattern)
    S.tile(name + '_top', tex.crop(0, 0, 16, 16), attrs=['SOLID'], doc=doc + ' (upper row)',
           extra={'pair': name + '_low'})
    S.tile(name + '_low', tex.crop(0, 16, 16, 16), attrs=['SOLID'], doc=doc + ' (lower row, wainscot)')


def build():
    S = Sheet('interior', 'Interior - homes, shops, halls', PALETTE, variants={'evening': EVENING}, banks=BANKS,
              doc=__doc__)
    S.section('floors')
    S.tile('void', Img(16, 16, 'v0'), attrs=['SOLID'], doc='outside the room')
    wt = Img(16, 16, 'wt1')
    wt.hline(0, 15, 15, 'wt0')
    S.tile('wall_top', wt, attrs=['SOLID'], doc='top of a wall seen from above')
    S.tile('floor_wood', IN.wood_floor(['fw0', 'fw1', 'fw2', 'fw3']), group='floor_wood', weight=3, doc='plank floor')
    S.tile('floor_wood_b', IN.wood_floor(['fw0', 'fw1', 'fw2', 'fw3'], seed=7), group='floor_wood', weight=2)
    S.tile('floor_checker', IN.checker('ck1', 'ck2', 'ck0'), doc='checker tiles (halls, kitchens)')
    S.tile('floor_stone', DG.floor_slabs(['sf0', 'sf1', 'sf2', 'sf3']), doc='flagstone floor (cellars, forges)')
    S.autotile('carpet', DG.carpet_autotile(['rd0', 'rd1', 'rd2'], IN.wood_floor(['fw0', 'fw1', 'fw2', 'fw3']),
                                            ['fy', 'rd3']), over='floor_wood', doc='carpet over planks')
    S.autotile('carpet_blue', DG.carpet_autotile(['bl0', 'bl1', 'bl2'], IN.checker('ck1', 'ck2', 'ck0'),
                                                 ['fy', 'bl2']), over='floor_checker', doc='blue carpet over tiles')

    S.section('walls')
    add_wall(S, 'wall_cream', ['pc0', 'pc1', 'pc2'], 'stripe', 'cream striped wallpaper')
    add_wall(S, 'wall_blue', ['pb0', 'pb1', 'pb2'], 'dots', 'blue dotted wallpaper')
    add_wall(S, 'wall_green', ['pg0', 'pg1', 'pg2'], 'diamond', 'green diamond wallpaper')
    add_wall(S, 'wall_brick', ['pr0', 'pr1', 'pr2'], 'brick', 'exposed brick')
    S.object('window', IN.window(WOOD, 'gl', ['sk0', 'sk1'], 'k0', curtain=['pc0', 'pc1', 'pc2']), solid='XX/XX',
             doc='curtained window 2x2 (on the back wall)')
    S.object('window_small', IN.window(WOOD, 'gl', ['sk0', 'sk1'], 'k0', w=16, h=32), solid='X/X',
             doc='narrow window 1x2')
    S.object('door_mat', IN.door_mat(['k1', 'k2', 'k3'], 'k0'), attrs=['EXIT'], solid='.', doc='exit mat')
    S.object('stairs_up', IN.stairs_in(['k1', 'k2', 'k3'], 'k0'), attrs=['EXIT'], solid='./.', doc='stairs up 1x2')
    S.object('stairs_down', IN.stairs_in(['k1', 'k2', 'k3'], 'k0', down=True), attrs=['EXIT'], solid='./.',
             doc='stairs down 1x2')
    for part in ('left', 'mid', 'right', 'end'):
        S.object('counter_' + part, IN.counter(['fw2', 'fw2', 'fw3'], ['k0', 'k1', 'k2'], 'k0', part),
                 attrs=['COUNTER'], doc='shop counter (%s)' % part if part == 'left' else '')
    S.object('picture', IN.picture(['k1', 'k2', 'k3'], ['lf1', 'lf2', 'fy'],
                                   'k0'), solid='.', doc='framed painting (wall)')
    S.object('clock_wall', IN.globe(['k1', 'k2'], ['pc0', 'pc1', 'pc2'], ['k0', 'k2'], 'k0'), solid='.',
             doc='wall clock (wall)')
    S.object('shelf_wall', IN.dresser(['k1', 'k2', 'k3'], 'k0', 'fy'), solid='..', doc='wall shelf 2x1')

    S.section('home')
    S.object('bed', IN.bed(['k1', 'k2', 'k3'], FABRIC_B, ['pc0', 'pc1', 'pc2'], 'k0'), doc='bed 1x2')
    S.object('bed_double', IN.bed(['k1', 'k2', 'k3'], FABRIC_R, ['pc0', 'pc1', 'pc2'], 'k0', double=True),
             doc='double bed 2x2')
    S.object('table', IN.table(WOOD, 'k0'), top='XX/..', solid='../XX', doc='table 2x2')
    S.object('table_long', IN.table(WOOD, 'k0', w=48), top='XXX/...', solid='.../XXX', doc='long table 3x2')
    S.object('table_round', IN.round_table(WOOD, 'k0', cloth=['pc0', 'pc1', 'pc2']), top='XX/..', solid='../XX',
             doc='round table with cloth 2x2')
    S.object('chair', IN.chair(WOOD, 'k0', cushion=FABRIC_R), solid='.', doc='chair (facing down)')
    S.object('chair_up', IN.chair(WOOD, 'k0', facing='up', cushion=FABRIC_R), solid='.', doc='chair (facing up)')
    S.object('stool', IN.stool(WOOD, 'k0'), solid='.', doc='stool')
    S.object('bookshelf', IN.bookshelf(['k0', 'k1', 'k2'], BOOKS, 'k0'), doc='bookshelf 2x2')
    S.object('wardrobe', IN.wardrobe(WOOD, 'k0'), doc='wardrobe 2x2')
    S.object('dresser', IN.dresser(WOOD, 'k0', 'fy'), doc='dresser 2x1')
    S.object('clock', IN.clock(WOOD, ['k0', 'pc2', 'fy'], 'k0'), top='X/.', solid='./X', doc='grandfather clock 1x2')
    fp = [IN.fireplace(['sf0', 'sf1', 'sf2'], ['fo', 'fy', 'fw'], 'k0', f) for f in range(3)]
    S.object('fireplace', fp[0], frames=fp, period=8, doc='fireplace 2x2 (animated)')
    st = [IN.stove(METAL, ['fo', 'fy'], 'k0', f) for f in range(2)]
    S.object('stove', st[0], frames=st, period=12, top='X/.', solid='./X', doc='iron stove 1x2')
    S.object('sink', IN.sink(['fw2', 'fw2', 'fw3'], ['m1', 'm1'], 'bl2', 'k0'), doc='sink counter')
    S.object('icebox', IN.icebox(['sf1', 'sf2', 'sf3'], 'k0', 'm2'), top='X/.', solid='./X', doc='icebox 1x2')
    S.object('plant', IN.plant(['k1', 'k2', 'k3'], ['lf0', 'lf1', 'lf2', 'lf3'], 'k0'), doc='potted plant')
    S.object('plant_tall', IN.plant(['k1', 'k2', 'k3'], ['lf0', 'lf1', 'lf2', 'lf3'], 'k0', h=32, big=True),
             top='X/.', solid='./X', doc='tall plant 1x2')
    S.object('vase', IN.vase(['k1', 'k2', 'k3'], ['rd2', 'fy'], 'k0'), doc='flower vase')
    S.object('lamp', IN.lamp_floor(METAL, ['fo', 'fy', 'fw'], 'k0'), top='X/.',
             solid='./X', doc='floor lamp 1x2')
    S.object('piano', IN.piano(['k0', 'k1', 'k2'], ['k0', 'ck2'], 'k0'), doc='upright piano 2x2')
    S.object('rug', IN.rug(['rd0', 'rd1', 'rd2', 'rd3'], 'k0'), layer='ground', solid='.../...', doc='rug 3x2')
    S.object('rug_blue', IN.rug(['bl0', 'bl1', 'bl2', 'fy'], 'k0', w=32, h=32), layer='ground', solid='../..',
             doc='round-cornered rug 2x2')
    S.object('barrel', PR.barrel(['k1', 'k2', 'k3', 'k4'], 'm1', 'k0'), doc='barrel')
    S.object('crate', PR.crate(['k1', 'k2', 'k3', 'k4'], 'k0'), doc='crate')
    S.object('sacks', TP.sacks(['k2', 'k3', 'k4'], 'k0', 'k1'), doc='sacks')

    S.section('halls, shops, studies')
    hh = [IN.hearth_heal(['sf0', 'sf1', 'sf2'], ['fo', 'fy', 'fw'], ['fy', 'fy'], 'k0', f) for f in range(3)]
    S.object('hearth_flame', hh[0], frames=hh, period=8, doc='Hearth Hall healing flame 2x2 (animated)')
    pcf = [IN.pc(METAL, ['sc0', 'sc1', 'sc2'], 'k0', f) for f in range(2)]
    S.object('terminal', pcf[0], frames=pcf, period=40, top='X/.', solid='./X', doc='kin storage terminal 1x2')
    S.object('shop_shelf', IN.shop_shelf(['k0', 'k1', 'k2'], BOOKS, 'k0'), doc='shelf of goods 2x2')
    S.object('globe', IN.globe(['k1', 'k2'], FABRIC_B, ['lf1', 'lf2'], 'k0'), doc='globe')
    S.object('aquarium', IN.aquarium('ck2', ['bl0', 'bl1', 'bl2'], 'fy', ['k0', 'k1', 'k2'], 'k0'), doc='aquarium 2x2')
    mc = [IN.machine(METAL, ['sc1', 'sc2'], 'k0', f) for f in range(2)]
    S.object('machine', mc[0], frames=mc, period=20, doc='workshop apparatus 2x2 (blinking)')
    S.object('display_case', IN.aquarium('ck2', ['ck0', 'ck1', 'ck2'], 'fy', ['k0', 'k1', 'k2'], 'k0'),
             doc='display case 2x2')

    S.section('study and workshop')
    MT = ['m0', 'm1', 'm2']
    GLOW = ['sc1', 'sc2']
    for k in ('extractor', 'mixer', 'loom', 'tanks'):
        fr = [X.fusion_machine(k, MT, GLOW, ['sf1', 'sf2', 'sf3'], 'k0', f) for f in range(2)]
        S.object('fusion_' + k, fr[0], frames=fr, period=20, doc='fusion lab %s 2x2' % k)
    py = [X.pylon(MT, GLOW, 'k0', f) for f in range(2)]
    S.object('pylon', py[0], frames=py, period=24, top='X/.', solid='./X', doc='resonance pylon 1x2')
    co = [X.coil(MT, ['rd1', 'fo', 'fy'], 'sc2', 'k0', f) for f in range(2)]
    S.object('resonance_coil', co[0], frames=co, period=10, top='X/.', solid='./X', doc='resonance coil 1x2')
    vt = [X.vat(MT, ['sc0', 'sc1', 'sc2'], 'k0', f) for f in range(3)]
    S.object('energy_vat', vt[0], frames=vt, period=16, top='X/.', solid='./X', doc='energy vat 1x2')
    dy = [X.dynamo(MT, ['rd1', 'fo', 'fy'], 'k0', f) for f in range(4)]
    S.object('dynamo', dy[0], frames=dy, period=6, doc='dynamo 2x1 (spinning)')
    S.object('bike_display', X.bike_display(['m0', 'm2'], 'm0', ['sf0', 'sf1', 'sf2'], 'k0'), doc='bike on a stand 2x2')
    S.object('gears', X.gears(MT, 'k0'), doc='gear set')
    S.object('file_cabinet', X.file_cabinet(MT, 'k0'), top='X/.', solid='./X', doc='file cabinet 1x2')
    S.object('volt_banner', DG.banner(['bl0', 'bl1', 'bl2'], ['k1', 'k2', 'k3'], 'fy', 'k0'), solid='./.',
             doc='hall banner 1x2 (wall)')
    S.object('work_board', X.work_board(['k1', 'k2', 'k3'], ['pc1', 'pc2'], 'rd2', 'k0'), solid='..',
             doc='job board 2x1 (wall)')
    S.object('chest', X.chest(['k1', 'k2', 'k3'], ['k0', 'k2', 'k4'], 'k0'), doc='storage chest')
    S.object('radio', X.radio(['k1', 'k2', 'k3'], 'rd1', 'fy', 'k0'), doc='wireless set')
    S.object('desk', X.desk(['k1', 'k2', 'k3'], 'pc2', 'k0'), doc='writing desk 2x1')
    S.object('telescope', X.telescope(['k0', 'm1', 'ck2'], ['k1', 'k2', 'k3'], 'k0'), top='X/.', solid='./X',
             doc='telescope 1x2')
    S.object('specimen_shelf', IN.shop_shelf(['k0', 'k1', 'k2'], [('lf0', 'lf1', 'lf2'), ('k1', 'fy', 'pc2')], 'k0'),
             doc='specimen shelf 2x2')
    S.object('microscope', X.microscope(MT, 'k0'), doc='microscope')
    S.object('telegraph', X.telegraph(['k1', 'k2', 'k3'], ['k0', 'm1', 'ck2'], 'k0'), doc='telegraph key')
    S.object('chalkboard', X.chalkboard(['k1', 'k2', 'k3'], 'lf0', 'pc2', 'k0'), solid='..', doc='chalkboard 2x1 (wall)')
    S.object('map_poster', X.poster(['pc0', 'pc1', 'pc2'], ['k2', 'lf1'], 'k0', 'map'), solid='.', doc='map (wall)')
    S.object('calendar', X.poster(['pc0', 'pc1', 'pc2'], ['k1', 'rd1'], 'k0', 'calendar'), solid='.',
             doc='calendar (wall)')
    S.object('pennant', X.pennant(['rd0', 'rd1', 'rd2'], 'k2', 'k0'), solid='.', doc='pennant (wall)')
    S.object('cooktop', X.cooktop(MT, ['fo', 'fy'], 'k0'), doc='cooktop')
    cd = [X.cauldron(MT, ['sc0', 'sc2'], 'fo', 'k0', f) for f in range(3)]
    S.object('cauldron', cd[0], frames=cd, period=14, doc='bubbling cauldron')
    S.object('anvil', X.anvil_in(MT, ['sf0', 'sf1', 'sf2'], 'k0'), doc='anvil')
    ov = [X.brick_oven(['sf0', 'sf1'], ['fo', 'fy'], 'k0', f) for f in range(3)]
    S.object('brick_oven', ov[0], frames=ov, period=10, doc='bread oven 2x2 (animated)')
    S.object('bread_display', X.bread_display(['k1', 'k2', 'k3'], ['k2', 'k3', 'k4'], 'k0'), doc='bread counter 2x1')
    S.object('lantern_rack', X.lantern_rack(['k1', 'k2', 'k3'], 'fy', 'k0'), solid='..', doc='lantern rack 2x1')

    S.section('keepsakes')
    S.object('tea_set', X.tea_set(['pc0', 'pc1', 'pc2'], 'k2', 'k0'), solid='.', doc='tea set (on tables)')
    S.object('cushion', X.cushion(FABRIC_R, 'k0'), solid='.', doc='floor cushion')
    S.object('kin_basket', X.kin_basket(['k1', 'k2', 'k3'], FABRIC_B, 'k0'), doc='kin bed basket')
    S.object('bookshelf_small', X.small_bookshelf(['k0', 'k1', 'k2'], BOOKS, 'k0'), top='X/.', solid='./X',
             doc='narrow bookshelf 1x2')
    S.object('toy_box', X.toy_box(['k1', 'k2', 'k3'], ['rd2', 'bl1'], 'k0'), doc='toy box')
    S.object('coat_rack', X.coat_rack(['k1', 'k2', 'k3'], ['rd1', 'bl1'], 'k0'), top='X/.', solid='./X',
             doc='coat rack 1x2')
    S.object('mirror', __import__('dreamart').mirror(['k1', 'k2', 'k3'], ['bl1', 'bl2', 'pc2'], 'k0'), top='X/.',
             solid='./X', doc='standing mirror 1x2')
    S.object('cactus', X.cactus_pot(['k1', 'k2', 'k3'], ['lf1', 'lf2', 'lf3'], 'k0'), doc='potted cactus')
    S.object('kin_plush', X.kin_plush(['k1', 'k2', 'k3', 'k4'], 'k0'), solid='.', doc='kin plush toy')
    S.object('ship_wheel', X.ship_wheel(['k1', 'k2', 'k3'], 'k0'), solid='.', doc='ship wheel (wall)')
    S.object('fish_trophy', X.fish_trophy(['k1', 'k2', 'k3'], ['bl0', 'bl1', 'bl2'], 'k0'), solid='.',
             doc='fish trophy (wall)')
    S.object('ship_bottle', X.ship_bottle('ck2', ['k1', 'fw3'], 'k0'), solid='.', doc='ship in a bottle')
    S.object('net_wall', X.net_wall('k3', 'rd2', 'k0'), solid='..', doc='fishing net (wall) 2x1')

    S.scene(hall_scene())
    S.scene(home_scene())
    return S


def room(sc, x0, y0, x1, y1, wall, floor):
    """Void around, a 2-row back wall, the floor below."""
    sc.rect(0, 0, sc.w - 1, sc.h - 1, 'void')
    sc.rect(x0, y0, x1, y0, wall + '_top')
    sc.rect(x0, y0 + 1, x1, y0 + 1, wall + '_low')
    sc.rect(x0, y0 + 2, x1, y1, floor)


def hall_scene():
    sc = Scene('hearth_hall', 'Hearth Hall (sample)', 17, 13, 'void',
               doc='The Hearth Hall: checker floor and blue carpet to the flame counter, the storage '
                   'terminal, a hearth, plants and benches.')
    room(sc, 1, 0, 15, 12, 'wall_cream', 'floor_checker')
    sc.rect(7, 5, 9, 11, 'carpet_blue')
    obj = [('window', 2, 0), ('window', 12, 0), ('counter_left', 5, 3), ('counter_mid', 6, 3), ('counter_mid', 7, 3),
           ('counter_mid', 8, 3), ('counter_mid', 9, 3), ('counter_mid', 10, 3), ('counter_right', 11, 3),
           ('hearth_flame', 7, 1), ('terminal', 13, 2), ('fireplace', 2, 2), ('plant_tall', 1, 9),
           ('plant_tall', 15, 9), ('table_round', 2, 6), ('chair', 4, 6), ('bookshelf', 13, 5), ('clock', 15, 2),
           ('door_mat', 8, 12), ('picture', 5, 0), ('picture', 10, 0)]
    for (n, x, y) in obj:
        sc.put(n, x, y)
    return sc


def home_scene():
    sc = Scene('cottage', 'Cottage interior (sample)', 14, 11, 'void',
               doc='A cozy home: plank floor, rug, bed, bookshelf, stove and table, window light.')
    room(sc, 1, 0, 12, 10, 'wall_green', 'floor_wood')
    obj = [('window', 3, 0), ('window_small', 9, 0), ('bed', 1, 2), ('wardrobe', 2, 2), ('bookshelf', 7, 1),
           ('stove', 11, 1), ('sink', 10, 2), ('table', 5, 5), ('chair', 4, 5), ('chair_up', 7, 7), ('rug', 4, 8),
           ('plant', 1, 9), ('lamp', 12, 7), ('clock', 12, 3), ('barrel', 1, 5), ('stairs_up', 12, 8),
           ('door_mat', 6, 10), ('picture', 6, 0)]
    for (n, x, y) in obj:
        sc.put(n, x, y)
    return sc
