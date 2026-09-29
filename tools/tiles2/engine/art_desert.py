"""DESERT (Saffron Dunes, Sunwell) drawn from tiles2 `desert`."""

from core import Img
import terrain as T
import props as PR
import desertart as DS
import sets.desert as S

from .load import kit, over
from . import common as CM

SET = 'desert'


def art(ctx):
    k = kit(SET)
    sand = k.cells('sand')
    rock = k.paint(T.lump_texture(['st0', 'st1', 'st2', 'st3'], 16, 16, 7, rx=3.4, ry=2.8, sx=5.3, sy=4.0, bias=-0.1))
    rock2 = k.paint(T.lump_texture(['st0', 'st1', 'st2', 'st4'], 16, 16, 11, rx=3.4, ry=2.8, sx=5.3, sy=4.0, bias=-0.1))
    adobe = k.paint(T.bricks(['ad0', 'ad1', 'ad2', 'ad3'], bw=8, bh=4))
    hut = k.img('adobe_hut')
    terrain = {
        'SAND': sand, 'SAND2': k.cells('sand_b'), 'SAND3': k.cells('sand_c'),
        'SAND_T': ('fit', over(sand, k.img('dry_tuft'))), 'SAND_P': ('fit', over(k.cells('sand_b'), k.img('pebbles'))),
        'DUNE': k.cells('dunes'), 'DRY_WASH': k.cells('hardpan'),
        'SCRUB': k.cells('scrub'), 'GARDEN': k.cells('scrub_c'),
        'ROCK': rock, 'ROCK2': rock2, 'ADOBE_WALL': adobe,
        'DOOR': ('fit', over(adobe, CM.cell_of(hut, 1, 2))),
    }
    decor = CM.decor_table(k, ctx.decor, {
        'DESERT_WAYPOST': 'signpost', 'DESERT_CACTUS': 'saguaro', 'DESERT_CACTUS_BLOOM': 'saguaro_bloom',
        'DESERT_DUNE_TUFT': 'dry_tuft', 'DESERT_ADOBE_HUT': 'adobe_hut', 'DESERT_WELL': 'well',
        'DESERT_JAR': 'jars', 'DESERT_CARAVAN_CANOPY': 'canopy_red@0,0',
    })
    return {
        'set': SET,
        'terrain': terrain,
        'add_terrain': ['SAND3', 'SAND_T', 'SAND_P'],
        'variant_of': {'SAND3': 'SAND', 'SAND_T': 'SAND', 'SAND_P': 'SAND'},
        'legend': {'.': [('SAND', 9), ('SAND2', 3), ('SAND3', 2), ('SAND_T', 1), ('SAND_P', 1)]},
        'water': k.frames('oasis'), 'water_period': 20,
        'path': CM.blend_block(k, k.cells('hardpan'), sand, rim_out='ds2', seed=5),
        'stamps': {},
        'elev': CM.elev(k, sand, ('st5', 'st4', 'st1', 'st0', 'st3'), rock_out='st0', rock_dk='st1',
                        deck_imgs=(k.paint(PR.bridge_h(S.WOOD, 'k0')), k.paint(PR.bridge_v(S.WOOD, 'k0')))),
        'decor': decor,
    }
