"""CITY (Lumen) drawn from tiles2 `city`."""

from core import Img
import terrain as T
import flora as F
import props as PR
import townprops as TP
import extras as X
import cityart as CT
import sets.city as S

from .load import kit, over
from . import common as CM

SET = 'city'


def art(ctx):
    k = kit(SET)
    pave = k.cells('pavement')
    road = k.cells('road')
    lawn = k.cells('lawn')
    forest = CM.forest_render(k, ['t0', 't1', 't2', 't3', 't4', 't5'], 't0', ['k1', 'k2', 'k3'], 'k0', seed=2)
    # flower beds in the lawn bank's own colours (terracotta and white)
    flowers = lambda petal, dk, ce, seed: [k.paint(F.flower_patch(lawn, petal, dk, ce, 'g2', frame=f, seed=seed,
                                                                  kind='tulip')) for f in range(2)]
    wtop = Img(16, 16, k.role('sl1'))
    wtop.hline(0, 15, 15, k.role('sl0'))
    wtop.hline(0, 15, 0, k.role('sl2'))
    terrain = {
        'PAVE': pave, 'PAVE2': k.cells('pavement_b'),
        'COBBLE': k.paint(T.cobbles(['pv1', 'pv2', 'pv3', 'pv4'], 'pv0', seed=5)),
        'PLAZA': k.paint(T.flagstones(['pv0', 'pv2', 'pv3', 'pv4'], seed=9)),
        'GRASS': lawn, 'GRASS2': k.cells('lawn_b'), 'GRASS3': k.cells('lawn_c'), 'GRASS_C': k.cells('lawn_d'),
        'TALLGRASS': k.cells('lawn_b'),
        'FLOWER_RED': ('anim', flowers('rd3', 'rd2', 'pv4', 3), 32),
        'FLOWER_YELLOW': ('anim', flowers('pv4', 'pv3', 'rd3', 7), 32),
        'TREE_TOP': ('mass', 'forest'), 'TREE_BOTTOM': ('mass', 'forest'),
        'WALL_TOP': wtop, 'WALL': k.paint(T.bricks(['k0', 'bk0', 'bk1', 'bk2'])),
    }
    SL, CU, CL = S.SLATE, S.COPPER, S.CLAY
    row = CM.house(k, SL, 7, 4, 1, windows=[(40, 6), (72, 6), (8, 24), (40, 24)], roof_style='slate', chimney=60,
                   beams=True, door_w=14)
    row.paste(row.crop(16, 48, 16, 16), 80, 48)
    stamps = {
        'HEARTH': CM.hearth(k, CL, 6, 4, 3, ('ws2', 'ra4', 'ra2'), windows=[(6, 6), (78, 6)], roof_style='tile',
                            siding='stone'),
        'MARKET': CM.house(k, CU, 8, 4, 4, windows='auto', roof_style='shingle', siding='brick', door_w=16,
                           awning=(40, 55, ['cu1', 'bk2', 'cu3'])),
        'VOLT_HALL': CM.house(k, SL, 9, 5, 4, windows='auto', roof_style='slate', storeys=2, beams=True, door_w=16),
        'WORKS': CM.house(k, CL, 8, 4, 3, windows='auto', roof_style='tile', siding='stone', chimney=100),
        'BIKE_SHOP': CM.house(k, CU, 5, 4, 3, windows=[(6, 8), (24, 8)], roof_style='shingle', siding='brick',
                              awning=(40, 55, ['cu1', 'bk2', 'cu3'])),
        'INN': CM.house(k, CL, 6, 4, 3, windows='auto', roof_style='tile', siding='stone', beams=True, chimney=12),
        'HOUSE_A': CM.house(k, CL, 5, 4, 2, windows='auto', roof_style='tile', chimney=58),
        'HOUSE_B': CM.house(k, CU, 5, 4, 2, windows='auto', roof_style='shingle', siding='brick', chimney=12),
        'HOUSE_C': CM.house(k, SL, 4, 4, 1, windows=[(38, 6)], roof_style='slate', chimney=44),
        'ROW_HOUSES': row,
        'CLOCK_TOWER': k.img('clock_tower'),
    }
    bridge = k.img('bridge')
    bv = bridge.crop(16, 16, 16, 16)
    rail = k.img('railing')
    decor = CM.decor_table(k, ctx.decor, {
        'SIGNPOST': k.paint(PR.signpost(['k1', 'k2', 'k3', 'k4'], 'k0')), 'FENCE': 'railing@2,0',
        'FENCE_END': 'railing@0,0', 'RAILING': 'railing@2,0',
        'ROCK': k.paint(PR.small_rock(['pv1', 'pv2', 'pv3', 'pv4', 'pv4'], 'pv0', 1)), 'BUSH': 'hedge_bush',
        'CRATE_STACK': k.paint(X.crate_stack(['k1', 'k2', 'k3', 'k4'], 'k0')),
        'SACKS': k.paint(TP.sacks(['k2', 'k3', 'k4'], 'k0', 'k1')),
        'PLANTER': k.paint(TP.planter(['k1', 'k2', 'k3', 'k4'], 'k1', ['t1', 't2', 't3', 't4'], ['fr', 'fw', 'fp'], 'k0')),
        'MARKET_STALL': k.paint(TP.market_stall(['k1', 'k2', 'k3'], ['ra1', 'ws2', 'ra3'],
                                               [('ra0', 'ra2', 'ra4'), ('k1', 'k2', 'k3')], 'k0')),
        'LANTERN_POST': 'lamp', 'STONE_LANTERN': k.paint(X.stone_lantern(['pv1', 'pv2', 'pv3', 'pv3'], ('el0', 'el1'), 'm0')),
        'BIG_TREE': 'tree',
        'HEDGE': CM.hedge_piece(k, ['t0', 't1', 't2', 't3', 't4', 't5'], 't0', 3, 't1', {(-1, 0), (1, 0)}),
        'HEDGE_END': CM.hedge_piece(k, ['t0', 't1', 't2', 't3', 't4', 't5'], 't0', 3, 't1', {(-1, 0)}),
        'PEBBLES': k.paint(PR.pebbles(['pv1', 'pv2', 'pv3', 'pv4', 'pv4'], 'pv0', 5)),
        'FALLEN_LEAVES': k.paint(X.fallen_leaves(['t3', 't4', 'k3'])),
        'SMALL_FLOWERS': k.paint(X.small_flowers(['fr', 'fp', 'fw'], 't2')),
        'LILY_PADS': k.paint(F.lily_pad(['t1', 't2', 't4'], 't1', flower=('fw', 'fp'))),
        'BRIDGE_V': bv, 'BRIDGE_H': bv.rot90(),
        'FOUNTAIN': ([k.paint(TP.fountain(['pv1', 'pv1', 'pv2', 'pv3'], ['cw1', 'cw2', 'cw4', 'cw5'], 'pv0', f,
                                         w=32, h=32)) for f in range(4)], 8),
        'NOTICE_BOARD': k.paint(PR.notice_board(['k1', 'k2', 'k3', 'k4'], 'k0', 'fw', 'fy', 'fr')),
        'CART': CM.at_bottom(k.paint(TP.cart(['k1', 'k2', 'k3', 'k4'], ['k0', 'k2'], 'k0')), 2, 2),
        'SIGN_ARROW': k.paint(PR.arrow_sign(['k1', 'k2', 'k3', 'k4'], 'k0')), 'BEEHIVE': 'flower_pot',
        'CITY_LAMP': 'lamp', 'TESLA_COIL': 'beacon@0,1', 'PARKED_BIKE': 'bike@0,0',
        'CAFE_TABLE': 'cafe_table@0,0', 'BEACON': 'beacon',
    })
    return {
        'set': SET,
        'terrain': terrain,
        'add_terrain': ['GRASS_C'], 'ground': ['GRASS_C'],
        'legend': {'g': [('GRASS', 9), ('GRASS2', 3), ('GRASS_C', 3), ('GRASS3', 1)]},
        'water': k.frames('canal'), 'water_period': 20,
        'path': CM.blend_block(k, road, pave, rim_in='rd0', rim_out='pv4', seed=3, E=3.0, amp=0.3),
        'blends': {'GRASS': k.img('lawn_bed')},
        'stamps': stamps,
        'masses': {'forest': CM.forest_mass(forest)},
        'elev': CM.painted_elev(k, pave, ['pv0', 'pv1', 'pv2', 'pv3', 'pv4'], 'pv0',
                                ('pv4', 'pv3', 'pv1', 'pv0', 'pv2'),
                                (k.paint(PR.bridge_h(['k1', 'k2', 'k3', 'k4'], 'k0')),
                                 k.paint(PR.bridge_v(['k1', 'k2', 'k3', 'k4'], 'k0'))),
                                bevel='pv4', rock_dk='pv1'),
        'grass_colors': {'g_hi': 'g5', 'g_lt': 'g4', 'g_base': 'g3', 'g_mid': 'g2', 'g_dk': 'g1', 'g_dkr': 'g0'},
        'decor': decor,
        'ground_ok': ('BRIDGE_H', 'BRIDGE_V'),   # stone decks are paving by design
    }
