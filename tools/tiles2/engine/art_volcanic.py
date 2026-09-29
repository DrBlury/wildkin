"""VOLCANIC (calderas, ash fields, forges, the railway) drawn from tiles2 `volcanic`."""

from core import Img
import paint as P
import terrain as T
import flora as F
import props as PR
import townprops as TP
import extras as X
import fireart as FI
import sets.volcanic as S

from .load import kit, over
from . import common as CM
from .art_town import kin_statue

SET = 'volcanic'
LAVA9 = ['', 'N', 'S', 'W', 'E', 'NW', 'NE', 'SW', 'SE']


def art(ctx):
    k = kit(SET)
    ash = k.cells('ash')
    lava = k.frames('lava')
    basalt = k.paint(P.speckle_ground({'dk': 'bs1', 'mid': 'bs2', 'base': 'bs3', 'lt': 'bs4', 'hi': 'bs5'}, 21,
                                      dots=9, pebbles=1, cracks=1))
    basalt2 = k.paint(P.speckle_ground({'dk': 'bs1', 'mid': 'bs2', 'base': 'bs3', 'lt': 'bs4', 'hi': 'bs5'}, 22,
                                       dots=7, pebbles=2))
    cfloor = k.paint(P.speckle_ground({'dk': 'bs0', 'mid': 'bs1', 'base': 'bs2', 'lt': 'bs3', 'hi': 'bs4'}, 23,
                                      dots=9, pebbles=1))
    cfloor2 = k.paint(P.speckle_ground({'dk': 'bs0', 'mid': 'bs1', 'base': 'bs2', 'lt': 'bs3', 'hi': 'bs4'}, 24,
                                       dots=7, pebbles=2, cracks=1))
    face1 = k.img('cliff_face_single')
    face9 = k.img('cliff_face')
    cwall = k.paint(T.lump_texture(['bs0', 'bs1', 'bs2', 'bs3'], 16, 16, 9, rx=3.4, ry=2.8, sx=5.3, sy=4.0, bias=-0.1))
    hall = k.paint(T.flagstones(['k0', 'sl0', 'sl1', 'sl2'], seed=5))
    vent = hall.copy()
    for y in range(4, 12):
        for x in range(3, 13):
            vent.p[y][x] = k.role('sl0') if (x % 2 == 0 or y in (4, 11)) else k.role('lv2')
    wtop = Img(16, 16, k.role('bs0'))
    wtop.hline(0, 15, 15, k.role('bk0'))
    brick = k.paint(T.bricks(['bs0', 'bk0', 'bk1', 'bk2']))
    rail = k.img('railway')
    crag = CM.rock_mass(k, S.BASALT, 'bs0', seed=5)
    dead = k.img('charred_small')
    terrain = {
        'ASH': ash, 'ASH2': k.cells('ash_b'), 'ASH3': k.cells('ash_c'),
        'ASH_P': ('fit', over(ash, k.img('pebbles'))), 'ASH_O': ('fit', over(k.cells('ash_b'), k.img('obsidian'))),
        'BASALT': basalt, 'BASALT2': basalt2,
        'SETTS': k.paint(T.cobbles(['sl0', 'sl1', 'sl2', 'sl3'], 'bs0', seed=7)),
        'SULFUR': k.cells('sulfur'), 'EMBERBRUSH': k.cells('scorch'),
        'CLIFF': CM.cell_of(face1, 1, 0), 'CLIFF_FACE': CM.cell_of(face9, 1, 1),
        'LEDGE': k.cells('ledge', 1, 0), 'LEDGE_L': k.cells('ledge', 0, 0), 'LEDGE_R': k.cells('ledge', 2, 0),
        'RAIL_H': ('fit', over(ash, CM.cell_of(rail, 0, 0))), 'RAIL_V': ('fit', over(ash, CM.cell_of(rail, 1, 0))),
        'CRAG_TOP': ('mass', 'crag'), 'CRAG_BOTTOM': ('mass', 'crag'),
        'DEADTREE_TOP': ('overlay', CM.cell_of(dead, 0, 0), True),
        'DEADTREE_BOTTOM': ('overlay', CM.cell_of(dead, 0, 1), False),
        'CAVE_FLOOR': cfloor, 'CAVE_FLOOR2': cfloor2, 'CAVE_WALL': cwall, 'CAVE_FACE': CM.cell_of(face9, 1, 1),
        'CAVE_EXIT': CM.mouth(CM.cell_of(face1, 1, 0), k.role('bs0'), k.role('bs1')),
        'EMBERMOSS': cfloor2,
        'HALL_FLOOR': hall, 'HALL_VENT': vent, 'HALL_WALL_TOP': wtop, 'HALL_WALL': brick,
        'HALL_MAT': ('fit', over(hall, k.paint(__import__('interiorart').door_mat(['k1', 'k2', 'k3'], 'k0')))),
    }
    names = {'': 'LAVA', 'N': 'LAVA_N', 'S': 'LAVA_S', 'W': 'LAVA_W', 'E': 'LAVA_E', 'NW': 'LAVA_NW',
             'NE': 'LAVA_NE', 'SW': 'LAVA_SW', 'SE': 'LAVA_SE', 'INW': 'LAVA_INW', 'INE': 'LAVA_INE',
             'ISW': 'LAVA_ISW', 'ISE': 'LAVA_ISE', 'H': 'LAVA_H', 'V': 'LAVA_V', 'LONE': 'LAVA_POOL'}
    for kind, n in names.items():
        terrain[n] = ('anim', [CM.rmxp_piece(b, kind) for b in lava], 10)
    F_ = S.FORGE
    RUST = dict(F_, roof=['bs0', 'bk0', 'bk1', 'bk2', 'bk2'])
    cave = k.img('cave_mouth')
    arch = k.img('tunnel_arch')
    stamps = {
        'HEARTH': CM.hearth(k, F_, 5, 4, 2, ('gw2', 'gw1', 'gw0'), windows=[(6, 6), (62, 6)], roof_style='slate',
                            siding='brick'),
        'SHOP': CM.house(k, F_, 5, 4, 2, windows=[(6, 8), (62, 8)], roof_style='slate', siding='brick',
                         awning=(24, 55, ['bk0', 'gw2', 'bk2'])),
        'FORGE': CM.house(k, F_, 5, 4, 2, windows=[(6, 6), (62, 6)], roof_style='slate', siding='brick',
                          chimney=10),
        'HOUSE': CM.house(k, F_, 5, 4, 2, windows='auto', roof_style='slate', siding='brick', chimney=58),
        'HOUSE_RUST': CM.house(k, RUST, 5, 4, 2, windows='auto', roof_style='tile', siding='brick', chimney=12),
        'ANVIL_HALL': CM.house(k, F_, 7, 5, 3, windows='auto', roof_style='slate', siding='brick', storeys=2,
                               beams=True, door_w=16),
        'CAVE_MOUTH': cave.crop(0, 16, 48, 32), 'TUNNEL_ARCH': arch.crop(0, 16, 48, 32),
    }
    decor = CM.decor_table(k, ctx.decor, {
        'FENCE': 'fence@2,0', 'FENCE_END': 'fence@0,0',
        'BENCH': k.paint(TP.bench(S.WOOD, ['sl0', 'sl1'], 'k0')),
        'CRATE_STACK': k.paint(X.crate_stack(S.WOOD, 'k0')),
        'SACKS': k.paint(TP.sacks(['k2', 'k3', 'k4'], 'k0', 'k1')),
        'WATER_TROUGH': k.paint(TP.trough(S.WOOD, ['sl0', 'sl1', 'sl3'], 'k0')),
        'LANTERN_POST': k.paint(TP.lamp_post(['sl0', 'sl1', 'sl3'], 'k0', ['lv2', 'lv3', 'lv4'])),
        'CAMPFIRE': ([CM.cell_of(f, 0, 1) for f in k.frames('brazier')], 10),
        'WOODPILE': k.paint(TP.woodpile(S.WOOD, ['k2', 'k3', 'k4'], 'k0')),
        'STEAM_VENT': 'vent', 'LAVA_ORE_CART': 'mine_cart', 'FORGE_ANVIL': 'anvil',
        'BIG_BELL': 'big_bell@0,1', 'BRAZIER': 'brazier@0,1', 'COAL_PILE': 'coal_pile@0,0',
        'TOOL_RACK': 'tool_rack@0,1', 'SALAMANDER_STATUE': kin_statue(k, ('bs0', 'bs1', 'bs2', 'bs3', 'bs4')),
        'SMOKE': 'smoke@0,0',
    })
    return {
        'set': SET,
        'terrain': terrain,
        'add_terrain': ['ASH_P', 'ASH_O'], 'variant_of': {'ASH_P': 'ASH', 'ASH_O': 'ASH'},
        'legend': {'.': [('ASH', 10), ('ASH2', 3), ('ASH3', 2), ('ASH_P', 1)]},
        'water': k.frames('lava'), 'water_period': 10,
        'path': CM.blend_block(k, k.paint(P.speckle_ground({'dk': 'a1', 'mid': 'a2', 'base': 'a2', 'lt': 'a3',
                                                            'hi': 'a4'}, 31, dots=6, pebbles=1)), ash, seed=17),
        'blends': {'BASALT': CM.blend_block(k, basalt, ash, rim_out='a1', seed=19),
                   'SULFUR': CM.blend_block(k, k.cells('sulfur'), ash, seed=23)},
        'stamps': stamps,
        'masses': {'crag': CM.forest_mass(crag, 'CRAG_TOP', 'CRAG_BOTTOM')},
        'elev': CM.elev(k, ash, ('a5', 'a4', 'a2', 'bs0', 'a3'), rock_out='bs0', rock_dk='bs1',
                        deck_imgs=(k.paint(PR.bridge_h(S.WOOD, 'k0')), k.paint(PR.bridge_v(S.WOOD, 'k0')))),
        'grass_colors': {'eb_hi': 'lv4', 'eb_lt': 'lv3', 'eb_base': 'lv2', 'eb_dk': 'lv1', 'vb_dk': 'bs1',
                         'vb_out': 'bs0', 'va_dk': 'a1', 'su_y': 'su2', 'vb_base': 'bs2'},
        'decor': decor,
    }
