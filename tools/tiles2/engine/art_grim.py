"""GRIM (Hollow Downs, Ashen Fields, Duskmere) drawn from tiles2 `grim`; the
shared builder gothic() also draws DUSK (Gravewood) from tiles2 `dusk`."""

from core import Img
import paint as P
import terrain as T
import flora as F
import props as PR
import townprops as TP
import extras as X
import gothart as GO
import interiorart as IN

from .load import kit, over
from . import common as CM

SET = 'grim'


def speckle(k, R, seed, **kw):
    return k.paint(P.speckle_ground(dict(zip(('dk', 'mid', 'base', 'lt', 'hi'), R)), seed, **kw))


def gothic(ctx, k, R):
    """R: the set's materials (see art() below and art_dusk.py)."""
    g0 = k.cells(R['grass'][0])
    soil = speckle(k, R['soil'], 5, dots=9, pebbles=1)
    soil2 = speckle(k, R['soil'], 6, dots=11, pebbles=2, cracks=1)
    mud = speckle(k, R['mud'], 8, dots=8, pebbles=0)
    mud2 = speckle(k, R['mud'], 9, dots=10, pebbles=1)
    moss = speckle(k, R['moss'], 12, dots=12, pebbles=0)
    scorch = speckle(k, R['scorch'], 14, dots=8, pebbles=1, cracks=1)
    embers = []
    for f in range(3):
        im = scorch.copy()
        for i, (x, y) in enumerate(P.scatter(14, 14, 5, 40, margin=1, min_dist=3)):
            c = R['glow'][(i + f) % len(R['glow'])]
            im.p[y][x] = k.role(c)
        embers.append(im)
    face1 = k.img('cliff_face_single')
    face9 = k.img('cliff_face')
    dock = k.paint(PR.dock_block(R['wood'], R['wood_out'], R['wood'][0]))
    gnarl = CM.forest_render(k, R['leaf'], R['leaf_out'], R['bark'], R['bark_out'], seed=R.get('seed', 6), r=6.8)
    snag = k.paint(F.dead_tree(16, 32, R['bark'], R['bark_out'], seed=7))
    cypress = k.paint(F.conifer(16, 32, R['cypress'], R['cypress'][0], R['bark'], R['bark_out'], seed=4, tiers=4))
    terrain = {
        'ASH': g0, 'ASH2': k.cells(R['grass'][1]), 'ASH3': k.cells(R['grass'][2]), 'ASH4': k.cells(R['grass'][3]),
        'ASH_GRASS': k.cells(R['grass'][1]), 'SCORCH': scorch, 'EMBERS': ('anim', embers, 20),
        'COBBLE': k.paint(T.cobbles(R['stone'][:4], R['stone_out'], seed=4)),
        'GRAVE_SOIL': soil, 'GRAVE_SOIL2': soil2, 'GRAVE_BRUSH': k.cells(R['grass'][2]),
        'MUD': mud, 'MUD2': mud2, 'MOSS': moss, 'MIRE_REEDS': k.cells(R['grass'][1]),
        'DECK': ('fit', over(mud, dock.crop(16, 16, 16, 16))),
        'GNARL_TOP': ('mass', 'gnarl'), 'GNARL_BOTTOM': ('mass', 'gnarl'),
        'SNAG_TOP': ('overlay', snag.crop(0, 0, 16, 16), True),
        'SNAG_BOTTOM': ('overlay', snag.crop(0, 16, 16, 16), False),
        'CYPRESS_TOP': ('overlay', cypress.crop(0, 0, 16, 16), True),
        'CYPRESS_BOTTOM': ('overlay', cypress.crop(0, 16, 16, 16), False),
        'LEDGE': k.cells('ledge', 1, 0), 'LEDGE_L': k.cells('ledge', 0, 0), 'LEDGE_R': k.cells('ledge', 2, 0),
        'CRAG': CM.cell_of(face1, 1, 0), 'CRAG_FACE': CM.cell_of(face9, 1, 1),
    }
    H = R['house']
    stamps = {
        'HOUSE': CM.house(k, H, 4, 4, 1, windows=[(38, 6)], chimney=44, roof_style='slate', siding='stone'),
        'SHOP': CM.house(k, H, 4, 4, 1, windows=[(38, 8)], roof_style='slate', siding='stone',
                         awning=(8, 55, [H['roof'][1], H['wall'][2], H['roof'][3]])),
        'APOTHECARY': CM.house(k, H, 4, 4, 1, windows=[(38, 6)], gable=True, siding='stone', roof_style='slate'),
        'HEARTH': CM.hearth(k, H, 5, 4, 2, R['flame'], windows=[(6, 6), (62, 6)], roof_style='slate', siding='stone'),
        'CRYPT_HALL': CM.house(k, H, 5, 4, 2, windows=None, gable=True, siding='stone', roof_style='slate',
                               door_w=14),
        'BONE_GATE': k.paint(X.bone_gate(R['bone'], R['void'], R['stone_out'], w=80, h=64)),
    }
    bell = k.paint(TP.bell_tower(R['stone'][:3], R['wood'][:3], H['roof'][:4], R['bell'], R['stone_out'],
                                 w=16, h=32))
    decor = CM.decor_table(k, ctx.decor, {
        'GR_SIGN': 'signpost', 'GR_GRAVE': 'grave_round', 'GR_CROSS': 'grave_cross',
        'GR_FENCE': 'iron_fence@2,0', 'GR_BONES': 'bones', 'GR_SHRUB': R.get('shrub', 'shrub'),
        'GR_STUMP': 'stump', 'GR_CART': 'cart', 'GR_LANTERN': R['lamp'], 'GR_WISP': 'wisp', 'GR_BELL': bell,
        'GR_MOORING': 'mooring', 'GR_PUMPKIN': R['pumpkin'], 'GR_MEMORIAL': 'memorial',
    })
    return {
        'set': k.name,
        'terrain': terrain,
        'add_terrain': ['ASH4'], 'ground': ['ASH4'],
        'legend': {'.': [('ASH', 9), ('ASH2', 3), ('ASH3', 2), ('ASH4', 2)]},
        'water': k.frames(R['water']), 'water_period': 20,
        'path': k.img(R['path']),
        'blends': {'SCORCH': CM.blend_block(k, scorch, g0, seed=3),
                   'MOSS': CM.blend_block(k, moss, g0, seed=5),
                   'GRAVE_SOIL': CM.blend_block(k, soil, g0, rim_out=R['grass_dk'], seed=7),
                   'MUD': CM.blend_block(k, mud, g0, rim_out=R['grass_dk'], seed=9)},
        'stamps': stamps,
        'masses': {'gnarl': CM.forest_mass(gnarl, 'GNARL_TOP', 'GNARL_BOTTOM')},
        'elev': CM.elev(k, g0, R['stairs'], rock_out=R['stone_out'], rock_dk=R['stone'][0],
                        deck_imgs=(k.paint(PR.bridge_h(R['wood'], R['wood_out'])),
                                   k.paint(PR.bridge_v(R['wood'], R['wood_out'])))),
        'grass_colors': R['grass_colors'],
        'decor': decor,
        'backdrop': R.get('backdrop'),
    }


def art(ctx):
    import sets.grim as S
    k = kit('grim')
    R = {
        'grass': ('grass', 'grass_b', 'grass_c', 'grass_d'), 'grass_dk': 'wg1',
        'soil': ('gp1', 'gp2', 'gp3', 'gp4', 'gp4'), 'mud': ('wd0', 'wd1', 'wd2', 'wd3', 'wd3'),
        'moss': ('wg1', 'dl1', 'dl2', 'dl3', 'wg3'), 'scorch': ('wg0', 'gp1', 'gp2', 'gp3', 'gp3'),
        'glow': ('pk1', 'pk2', 'pk0'), 'stone': S.STONE, 'stone_out': 'gs0', 'wood': S.WOOD, 'wood_out': 'wd0',
        'leaf': ['wd0', 'dl1', 'dl2', 'dl3', 'wg3'], 'leaf_out': 'wd0', 'bark': ['wd1', 'wd2', 'wd3'],
        'bark_out': 'wd0', 'cypress': ['wg0', 'wg1', 'wg2', 'wg3', 'wg4'], 'house': S.HOUSE,
        'flame': ('ln2', 'ln1', 'ln0'), 'bone': ['gs3', 'gs4', 'gs5'], 'void': 'gs0',
        'bell': ['wd1', 'ln0', 'ln1'], 'lamp': 'lamp', 'pumpkin': 'lantern_pumpkin', 'water': 'mere',
        'path': 'road', 'stairs': ('gs5', 'gs4', 'gs1', 'gs0', 'gs3'),
        'grass_colors': {'grm_straw_hi': 'wg5', 'grm_straw': 'wg4', 'grm_straw_dk': 'wg3', 'grm_ash_dk': 'wg1',
                         'grm_soot': 'wg0', 'grm_ash_md': 'wg2', 'grm_ash_dkr': 'wg0', 'grm_bone': 'gp4',
                         'grm_ash_hi': 'gp4', 'grm_ash_lt': 'gp3', 'grm_rust': 'dl3', 'grm_emb_dk': 'pk0',
                         'grm_reed_hi': 'dl3', 'grm_reed': 'dl2', 'grm_moss_dk': 'dl1', 'grm_mud_dk': 'wd1',
                         'grm_peat': 'wd0', 'grm_mud': 'wd2', 'grm_wisp': 'ws0', 'grm_wisp_hi': 'ws1',
                         'grm_moss_hi': 'dl3'},
    }
    return gothic(ctx, k, R)
