"""DREAM (Mistfen, Moonveil, Dreamspire, Dust Library, Mirror Hall) drawn from tiles2 `dream`."""

from core import Img
import paint as P
import terrain as T
import props as PR
import townprops as TP
import interiorart as IN
import caveart as CA
import gothart as GO
import dreamart as DR
import sets.dream as S

from .load import kit, over
from . import common as CM
from .art_town import kin_statue

SET = 'dream'


def art(ctx):
    k = kit(SET)
    grass = k.cells('grass')
    lily = k.frames('moon_lilies')
    blossom = CM.forest_render(k, ['dg0', 'cp0', 'cp1', 'cp2', 'cp3'], 'dg0', ['bk1', 'bk2', 'bk3'], 'bk1', seed=5)
    face1 = k.img('cliff_face_single')
    face9 = k.img('cliff_face')
    mfloor = k.paint(IN.checker('mw2', 'mw3', 'mw1'))
    mstar = mfloor.copy()
    for (x, y) in ((4, 5), (11, 10), (7, 13)):
        mstar.p[y][x] = k.role('st')
    for (x, y) in ((4, 4), (3, 5), (5, 5), (4, 6)):
        mstar.p[y][x] = k.role('mw5') if (x, y) != (4, 5) else k.role('st')
    wall = k.paint(IN.wall_face(['mb1', 'mb2', 'mb3'], ['au0', 'au1', 'au2'], ['mb0', 'mb1'], pattern='stripe'))
    wtop = Img(16, 16, k.role('mw1'))
    wtop.hline(0, 15, 15, k.role('mb0'))
    lfloor = k.paint(IN.wood_floor(['bk1', 'bk2', 'bk3', 'mp1']))
    ldust = lfloor.copy()
    for i, (x, y) in enumerate(P.scatter(14, 14, 6, 61, margin=1, min_dist=3)):
        ldust.p[y][x] = k.role(('mp2', 'mp1')[i % 2])
    books = [('cp0', 'cp1', 'cp2'), ('ct0', 'ct1', 'ct2'), ('mp1', 'mp2', 'bk3')]
    shelf = k.paint(IN.bookshelf(['bk1', 'bk2', 'bk3'], books, 'dg0', w=16, h=32))
    mat = k.paint(IN.door_mat(['bk1', 'bk2', 'bk3'], 'dg0'))
    terrain = {
        'GRASS': grass, 'GRASS2': k.cells('grass_b'), 'GRASS3': k.cells('grass_stars'),
        'GRASS_C': k.cells('grass_c'), 'STONE': k.cells('moonstone'),
        'STONE2': k.paint(T.flagstones(['mp0', 'mp1', 'mp2', 'mp3'], seed=7)),
        'MOONPETAL': k.cells('grass_b'), 'MOONFLOWER': ('anim', lily, 24),
        'CLIFF': CM.cell_of(face1, 1, 0), 'CLIFF_FACE': CM.cell_of(face9, 1, 1),
        'LEDGE': k.cells('ledge', 1, 0), 'LEDGE_L': k.cells('ledge', 0, 0), 'LEDGE_R': k.cells('ledge', 2, 0),
        'BLOSSOM_TOP': ('mass', 'blossom'), 'BLOSSOM_BOTTOM': ('mass', 'blossom'),
        'MIRROR_FLOOR': mfloor, 'MIRROR_STAR': mstar, 'MIRROR_WALL_TOP': wtop,
        'MIRROR_WALL': wall.crop(0, 16, 16, 16), 'MIRROR_MAT': ('fit', over(mfloor, mat)),
        'LIB_FLOOR': lfloor, 'LIB_SHELF_TOP': ('fit', over(wtop, shelf.crop(0, 0, 16, 16))),
        'LIB_SHELF': ('fit', over(lfloor, shelf.crop(0, 16, 16, 16))), 'LIB_DUST': ldust,
        'LIB_MAT': ('fit', over(lfloor, mat)),
    }
    ST, ROSE = S.STYLE, S.ROSE
    stamps = {
        'HEARTH': CM.hearth(k, ROSE, 5, 4, 2, ('au2', 'au1', 'au0'), windows=[(6, 6), (62, 6)], roof_style='slate',
                            siding='plaster'),
        'SHOP': CM.house(k, ST, 5, 4, 2, windows=[(6, 8), (62, 8)], roof_style='slate',
                         awning=(24, 55, ['mw2', 'mb3', 'mw4'])),
        'HOUSE': CM.house(k, ST, 5, 4, 2, windows='auto', roof_style='slate', chimney=58),
        'HOUSE_ROSE': CM.house(k, ROSE, 5, 4, 2, windows='auto', roof_style='tile', chimney=12),
        'TOWER': k.img('spire').crop(0, 16, 48, 80), 'TOWER_ROSE': k.img('spire_rose').crop(0, 16, 48, 80),
        'MIRROR_HALL': k.img('mirror_hall'),
        'LIBRARY': CM.house(k, ST, 7, 5, 3, windows='auto', roof_style='slate', siding='stone', storeys=2,
                            beams=True, door_w=16),
    }
    fence = k.paint(GO.iron_fence(['mb0', 'mb1', 'mb2'], 'mb0', tip='au1'))
    wood = ['bk1', 'bk2', 'bk3', 'mp1']
    decor = CM.decor_table(k, ctx.decor, {
        'FENCE': fence.crop(32, 0, 16, 16), 'FENCE_END': fence.crop(0, 0, 16, 16),
        'BENCH': k.paint(TP.bench(wood, ['mp1', 'mp2'], 'dg0')),
        'BARREL': k.paint(PR.barrel(wood, 'mp2', 'dg0')), 'CRATE': k.paint(PR.crate(wood, 'dg0')),
        'LANTERN_POST': 'moon_lantern', 'FLOAT_PAGES': 'pages', 'READING_DESK': 'reading_desk@0,1',
        'BOOKCASE': shelf,
        'MOONSTONE': ([k.paint(CA.crystal(['mw1', 'mw3', 'mw4', 'mw5'], 'mw0', f, seed=3)) for f in range(3)], 24),
        'STANDING_MIRROR': 'mirror', 'DREAM_STATUE': kin_statue(k, ('mb0', 'mb1', 'mb2', 'mb3', 'ml2')),
        'SCRIPT_PEDESTAL': 'script_pedestal@0,1',
    })
    return {
        'set': SET,
        'terrain': terrain,
        'add_terrain': ['GRASS_C'], 'ground': ['GRASS_C'],
        'legend': {'.': [('GRASS', 9), ('GRASS2', 3), ('GRASS_C', 2), ('GRASS3', 2)]},
        'water': k.frames('mistlake'), 'water_period': 20,
        'path': k.img('path'),
        'blends': {'STONE': CM.blend_block(k, k.cells('moonstone'), grass, rim_out='dg1', seed=3),
                   'MOONFLOWER': CM.blend_block(k, lily[0], grass, seed=5, E=3.0)},
        'stamps': stamps,
        'masses': {'blossom': CM.forest_mass(blossom, 'BLOSSOM_TOP', 'BLOSSOM_BOTTOM')},
        'elev': CM.elev(k, grass, ('mb3', 'mb2', 'mb0', 'mb0', 'mb1'), rock_out='mb0', rock_dk='mb1',
                        deck_imgs=(k.paint(PR.bridge_h(wood, 'dg0')), k.paint(PR.bridge_v(wood, 'dg0')))),
        'grass_colors': {'dg_hi': 'dg5', 'dg_lt': 'dg4', 'dg_base': 'dg3', 'dg_mid': 'dg2', 'dg_dk': 'dg1',
                         'ds_dk': 'dg0', 'dp_base': 'mp2', 'dp_hi': 'mp4', 'ds_hi': 'st', 'vcr_base': 'ml1'},
        'decor': decor,
    }
