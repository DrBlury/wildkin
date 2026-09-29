"""JUNGLE (Rootcoil Jungle, Canopy Hearth) drawn from tiles2 `jungle`."""

from core import Img
import flora as F
import props as PR
import extras as X
import jungleart as J
import sets.jungle as S

from .load import kit, over
from . import common as CM

SET = 'jungle'


def art(ctx):
    k = kit(SET)
    loam = k.cells('loam')
    canopy = CM.forest_render(k, S.LEAF, 'jl0', S.BARK, 'k0', seed=3, r=7.4)
    face1 = k.img('cliff_face_single')
    hut = k.img('stilt_hut')
    plank = k.paint(PR.dock_block(S.WOOD, 'k0', 'k1')).crop(16, 16, 16, 16)
    crowns = F.lattice_render(lambda cx, cy: 0 <= cx < 3 and 0 <= cy < 2, 48, 32, S.LEAF, 'jl0', 9, r=7.4)
    terrain = {
        'LOAM': loam, 'LOAM2': k.cells('loam_b'), 'LOAM3': k.cells('loam_c'), 'LOAM4': k.cells('loam_d'),
        'LOAM_F': ('fit', over(loam, k.img('fern'))), 'LOAM_O': ('fit', over(k.cells('loam_b'), k.img('orchid'))),
        'ROOTS': k.cells('mud_c'), 'THICKET': k.cells('thicket'),
        'BOULDER': ('mass', 'canopy'), 'CANOPY': ('mass', 'canopy'),
        'VINE_WALL': ('fit', over(CM.cell_of(face1, 1, 0), CM.cell_of(k.img('vines'), 0, 0))),
        'PLATFORM': ('fit', over(k.cells('mud'), plank)),
        'DOOR': ('fit', over(plank, CM.cell_of(hut, 1, 2))),
    }
    decor = CM.decor_table(k, ctx.decor, {
        'JUNGLE_WAYPOST': 'waypost',
        'JUNGLE_BUTTRESS': k.paint(J.buttress_tree(S.LEAF, 'jl0', S.BARK, 'k0', w=32, h=48, seed=2)),
        'JUNGLE_VINES': 'vines', 'JUNGLE_CANOPY': k.paint(crowns), 'JUNGLE_WOVEN_HUT': 'stilt_hut',
        'JUNGLE_ORCHID': 'orchid',
        'JUNGLE_ROOT_BRIDGE': k.paint(X.root_bridge(S.WOOD, 'jl3', 'k0', w=32, h=16)),
    })
    return {
        'set': SET,
        'terrain': terrain,
        'add_terrain': ['LOAM3', 'LOAM4', 'LOAM_F', 'LOAM_O'],
        'variant_of': {'LOAM3': 'LOAM', 'LOAM4': 'LOAM', 'LOAM_F': 'LOAM', 'LOAM_O': 'LOAM'},
        'overlay': ['BOULDER', 'CANOPY'],
        'legend': {'.': [('LOAM', 7), ('LOAM2', 3), ('LOAM3', 2), ('LOAM4', 2), ('LOAM_F', 1), ('LOAM_O', 1)]},
        'water': k.frames('river'), 'water_period': 20,
        'path': k.img('mud_path'),
        'stamps': {},
        'masses': {'canopy': {'render': canopy, 'layer': {'BOULDER': 'mid', 'CANOPY': 'mid'}}},
        'elev': CM.elev(k, loam, ('ms3', 'ms2', 'ms0', 'jg0', 'ms1'), rock_out='jg0', rock_dk='ms0',
                        deck_imgs=(k.img('rope_bridge'), k.img('rope_bridge').rot90())),
        'decor': decor,
    }
