"""SNOW (alpine passes, tundra, frozen villages, Rime Hall) drawn from tiles2 `snow`."""

from core import Img
import paint as P
import terrain as T
import flora as F
import props as PR
import townprops as TP
import buildings as B
import snowart as SN
import extras as X
import sets.snow as S

from .load import kit, over, rmxp_cell
from . import common as CM
from .art_wild import outdoor_decor
from .art_town import kin_statue

SET = 'snow'

ICE9 = {'ICE': (1, 2), 'ICE_N': (1, 1), 'ICE_S': (1, 3), 'ICE_W': (0, 2), 'ICE_E': (2, 2),
        'ICE_NW': (0, 1), 'ICE_NE': (2, 1), 'ICE_SW': (0, 3), 'ICE_SE': (2, 3)}


def art(ctx):
    k = kit(SET)
    snow = k.cells('snow')
    PINE = ['p0', 'p1', 'p2', 'p3', 'p4']
    pines = CM.forest_render(k, PINE, 'p0', ['k1', 'k2', 'k3'], 'k0', seed=2, r=4.8, snow=('sn5', 'sn3'))
    ice = k.img('ice_patch')
    face1 = k.img('cliff_face_single')
    face9 = k.img('cliff_face')
    icew = k.paint(T.lump_texture(['ic0', 'ic1', 'ic2', 'ic3', 'sn5'], 32, 32, 5, rx=5.5, ry=4.2, sx=8, sy=6.5))
    wall_top = Img(16, 16, k.role('sn0'))
    wall_top.hline(0, 15, 15, k.role('ic1'))
    wall_top.hline(0, 15, 14, k.role('cw1'))
    cloud = k.paint(F.bush(16, 16, ['sn1', 'sn2', 'sn3', 'sn4', 'sn5'], 'sn2', seed=6))
    hall_floor = k.paint(SN.ice_floor(['ic0', 'ic1', 'ic2', 'ic3'], seed=3))
    terrain = {
        'SNOW': snow, 'SNOW2': k.cells('snow_b'), 'SNOW3': k.cells('snow_c'), 'SNOW_D': k.cells('snow_d'),
        'DRIFT': k.cells('snow_b'),
        'PINE_TOP': ('mass', 'pines'), 'PINE_BOTTOM': ('mass', 'pines'),
        'LEDGE': k.cells('ledge', 1, 0), 'LEDGE_L': k.cells('ledge', 0, 0), 'LEDGE_R': k.cells('ledge', 2, 0),
        'CLIFF': CM.cell_of(face1, 1, 0), 'CLIFF_FACE': CM.cell_of(face9, 1, 1),
        'CRAG': ('fit', over(snow, k.img('boulder'))),
        'STONE': k.paint(T.flagstones(['b1', 'b2', 'b3', 'b4'], seed=6)),
        'ICE_ROCK': ('fit', over(k.cells('ice'), k.img('rock'))),
        'CLOUD': ('fit', over(Img(16, 16, k.role('sn3')), cloud)),
        'HALL_FLOOR': hall_floor, 'HALL_WALL_TOP': wall_top, 'HALL_WALL': icew.crop(0, 0, 16, 16),
        'HALL_MAT': ('fit', over(hall_floor, k.paint(__import__('interiorart').door_mat(['k1', 'k2', 'k3'], 'k0')))),
        'VOID': Img(16, 16, k.role('sn0')),
    }
    for n, (cx, cy) in ICE9.items():
        terrain[n] = ice.crop(cx * 16, cy * 16, 16, 16)
    LOG = S.LOG
    cave = k.img('cave_mouth')
    stamps = {
        'HOUSE': CM.house(k, LOG, 5, 4, 2, windows=[(8, 6), (58, 6)], chimney=12, roof_style='snow', siding='log'),
        'HEARTH': CM.hearth(k, LOG, 5, 4, 2, ('gw2', 'gw1', 'gw0'), windows=[(6, 6), (62, 6)], roof_style='snow',
                            siding='log'),
        'SHOP': CM.house(k, LOG, 5, 4, 2, windows=[(6, 8), (62, 8)], roof_style='snow', siding='log',
                         awning=(24, 55, ['k1', 'sn5', 'k3'])),
        'BATHS': CM.house(k, LOG, 5, 4, 2, windows=[(6, 6), (62, 6)], gable=True, siding='log', roof_style='snow',
                          door_w=12),
        'HALL': CM.house(k, LOG, 7, 5, 3, windows='auto', roof_style='snow', siding='log', storeys=2, chimney=90),
        'CAVE': cave.crop(0, 16, 48, 32),
    }
    bh = k.paint(PR.bridge_h(S.WOOD, 'k0'))
    bv = k.paint(PR.bridge_v(S.WOOD, 'k0'))
    dock = k.paint(PR.dock_block(S.WOOD, 'k0', 'k1'))
    ice_r = ['ic0', 'ic1', 'ic2', 'ic3', 'sn5']
    decor = CM.decor_table(k, ctx.decor, outdoor_decor(k, S, {
        'BENCH': k.paint(TP.bench(S.WOOD, ['b1', 'b2'], 'k0')), 'CRATE_STACK': k.paint(X.crate_stack(S.WOOD, 'k0')),
        'SACKS': k.paint(TP.sacks(['k2', 'k3', 'k4'], 'k0', 'k1')),
        'WELL': k.paint(TP.well(['b1', 'b2', 'b3', 'b4'], S.WOOD, ['b0', 'b1'], 'k0', ['sn2', 'sn3', 'sn4', 'sn5'])),
        'HAY_BALE': 'woodpile@0,0', 'WATER_TROUGH': 'woodpile', 'LANTERN_POST': 'lamp',
        'STONE_LANTERN': k.paint(X.stone_lantern(['b1', 'b2', 'b3', 'b4'], ('fo', 'sn5'), 'b0')),
        'CAMPFIRE': ([k.paint(PR.campfire(S.WOOD, 'k0', ('sn5', 'fo', 'fr'), f)) for f in range(3)], 10),
        'STUMP': k.paint(F.stump(['k1', 'k2', 'k3'], 'k0', 'sn5', 'k2')),
        'LOG': k.paint(F.log_h(['k1', 'k2', 'k3', 'k4'], 'k0', 'sn5', 'k2')), 'BOULDER': 'rock_big',
        'DOCK': dock.crop(16, 16, 16, 16), 'DOCK_EDGE': dock.crop(16, 32, 16, 16), 'DOCK_POST': 'barrel',
        'BRIDGE_H': CM.bridge_cell_h(bh), 'BRIDGE_V': CM.bridge_cell_v(bv),
        'PICNIC_TABLE': k.paint(X.picnic_table(S.WOOD, 'k0')),
        'NOTICE_BOARD': k.paint(PR.notice_board(S.WOOD, 'k0', 'sn5', 'b3', 'fr')),
        'CART': CM.at_bottom(k.img('sled'), 2, 2), 'KIN_STATUE': kin_statue(k, ('b0', 'b1', 'b2', 'b3', 'b4')),
        'SIGN_ARROW': k.paint(PR.arrow_sign(S.WOOD, 'k0')),
        'CLOTHESLINE': CM.pair(CM.cell_of(k.img('frost_banner'), 0, 1), CM.cell_of(k.img('frost_banner'), 0, 1)),
        'WEATHER_VANE': k.paint(TP.weather_vane(['b1', 'b2', 'b3'], 'b0', 'k3')),
        'TELESCOPE': k.paint(X.telescope(['b1', 'b2', 'b3'], S.WOOD, 'k0')),
        'ICE_CRYSTAL': ([k.paint(SN.ice_crystal(['ic0', 'ic1', 'ic2', 'ic3'], 'ic0', h=16, seed=s)) for s in (1, 2, 3)],
                        20),
        'HOT_SPRING': ([k.paint(SN.hot_spring(['hs0', 'hs1', 'hs2'], ['b0', 'b2', 'b3', 'b4'], 'sn5', 'b0', f,
                                              w=64, h=48)) for f in range(3)], 16),
        'STEAM': ([CM.cell_of(f, 0, 0) for f in k.frames('steam')], 12),
        'WOLF_STATUE': kin_statue(k, ('b0', 'b1', 'b2', 'b3', 'b4')),
        'ICE_STATUE': kin_statue(k, ('ic0', 'ic1', 'ic2', 'ic3', 'sn5')),
        'RIME_PILLAR': k.paint(X.rime_pillar(['ic0', 'ic1', 'ic2', 'ic3'], ['b1', 'b2', 'b3'], 'b0', h=32)),
        'SKY_ARCH': k.paint(X.sky_arch(['b1', 'b2', 'b3'], ['ic0', 'ic1', 'ic2', 'ic3'], 'b0', w=48, h=32)),
        'SLED': CM.cell_of(k.img('sled'), 0, 0),
        'SKI_RACK': CM.cell_of(k.img('ski_rack'), 0, 1),
        'FROZEN_TREE': k.paint(F.dead_tree(16, 32, ['k1', 'k2', 'k3'], 'k0', seed=5)),
        'SNOW_CAIRN': 'cairn',
        'SHRINE': k.paint(X.shrine(S.WOOD, ['k1', 'k2', 'k3'], S.ROCK, ('fo', 'sn5'), 'k0', w=16, h=32)),
    }))
    return {
        'set': SET,
        'terrain': terrain,
        'add_terrain': ['SNOW_D'], 'ground': ['SNOW_D'],
        'legend': {'.': [('SNOW', 9), ('SNOW2', 3), ('SNOW3', 2), ('SNOW_D', 2)]},
        'water': k.frames('lake'), 'water_period': 20,
        'path': k.img('trail'),
        'stamps': stamps,
        'masses': {'pines': CM.forest_mass(pines, 'PINE_TOP', 'PINE_BOTTOM')},
        'elev': CM.elev(k, snow, ('b5', 'b4', 'b2', 'b0', 'b3'), rock_out='b0', rock_dk='b1', deck_imgs=(bh, bv)),
        'grass_colors': {'fg_hi': 'sn5', 'fg_base': 'mo3', 'fg_dk': 'mo2', 'fg_dkr': 'mo1',
                         'sn_hi': 'sn5', 'sn_lt': 'sn4', 'sn_base': 'sn4', 'sn_mid': 'sn3', 'sn_dk': 'sn2'},
        'decor': decor,
    }
