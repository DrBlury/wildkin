"""FARM (Willow Acre and the homestead) drawn from tiles2 `farm`."""

from core import Img
import paint as P
import flora as F
import props as PR
import townprops as TP
import extras as X
import farmart as FA
import sets.farm as S

from .load import kit, over
from . import common as CM
from .art_wild import outdoor_decor

SET = 'farm'
# old crop -> tiles2 crop drawing (stages YOUNG, GROW, RIPE = 1, 2, 3)
T2CROP = {'RADISH': 'turnip', 'CARROT': 'carrot', 'PUMPKIN': 'pumpkin', 'TOMATO': 'tomato'}  # tall crops keep two cells
CROP_BANK = 3


class FitTS:
    """A TileSet whose add() first fits each tile into the best bank."""
    def __init__(self, gf, ts):
        self.gf, self.ts = gf, ts

    def add(self, pix, prefer=(), where='?', **kw):
        return self.ts.add(self.gf.fit_bank_pix(self.ts, pix), prefer, where, **kw)

    def __getattr__(self, n):
        return getattr(self.ts, n)


def art(ctx):
    gf = ctx.gf
    import tilesets.ts_farm as OF
    k = kit(SET)
    grass = k.cells('grass')
    soil, wet = k.cells('soil'), k.cells('soil_wet')

    def fert(img, c1, c2):
        im = img.copy()
        for i, (x, y) in enumerate(P.scatter(14, 14, 6, 71, margin=1, min_dist=3)):
            im.p[y][x] = k.role((c1, c2)[i % 2])
        return im
    tilled_fert, wet_fert = fert(soil, 'g4', 'd3'), fert(wet, 'g3', 'so3')
    old = lambda img: CM.recolor_old(gf, k, img, [CROP_BANK])
    oldg = lambda img: CM.recolor_old(gf, k, img, [1])
    flowers = lambda petal, dk, ce, seed: [k.paint(F.flower_patch(grass, petal, dk, ce, 'g2', frame=f, seed=seed,
                                                                  kind='tulip')) for f in range(2)]
    forest = CM.forest_render(k, S.LEAF, 't0', S.BARK, 'k0', seed=1)
    fence = k.img('fence')
    H, V, END = fence.crop(32, 0, 16, 16), fence.crop(16, 16, 16, 16), fence.crop(48, 0, 16, 16)
    terrain = {
        'GRASS': grass, 'GRASS2': k.cells('grass_b'), 'GRASS3': k.cells('grass_flowers'),
        'GRASS_C': k.cells('grass_c'), 'GRASS_D': k.cells('grass_d'),
        'FLOWER_RED': ('anim', flowers('fr', 'fr', 'fy', 3), 32),
        'FLOWER_YELLOW': ('anim', flowers('fy', 'fy', 'fw', 7), 32),
        'DIRT': k.cells('dirt'), 'SOIL': k.cells('dirt_b'), 'SOIL2': k.cells('dirt_c'), 'SOIL_RIM': k.cells('dirt_b'),
        'TILLED': soil, 'TILLED_WET': wet, 'TILLED_FERT': tilled_fert, 'TILLED_WET_FERT': wet_fert,
        'ORCHARD': k.cells('dirt_c'), 'BERRY_MOUND': ('fit', oldg(OF.mound_img())),
        'TREE_TOP': ('mass', 'forest'), 'TREE_BOTTOM': ('mass', 'forest'),
        'FENCE_H': ('overlay', H, False), 'FENCE_V': ('overlay', V, False), 'FENCE_END': ('overlay', END, False),
        'FENCE_SW': ('overlay', over(H, V), False), 'FENCE_SE': ('overlay', over(END, V), False),
        'SEEDED': ('overlay', k.img('crop_wheat_0'), False),
        'SPROUT': ('overlay', k.img('crop_turnip_1'), False),
        'SAPLING': ('overlay', old(OF.sapling()), False), 'WITHERED': ('overlay', old(OF.withered()), False),
        'SPRINKLER': ('overlay', CM.recolor_old(gf, k, OF.sprinkler(), [7]), False),
    }
    for c in OF.CROPS:
        grow, ripe = OF.crop_img(c, False), OF.crop_img(c, True)
        stages = (('_YOUNG', OF.young_img(grow)), ('_GROW', grow), ('_RIPE', ripe))
        for si, (stage, im) in enumerate(stages):
            if c in T2CROP:
                bottom, top = k.img('crop_%s_%d' % (T2CROP[c], si + 1)), Img(16, 16)
            else:
                full = old(im)
                bottom, top = full.crop(0, 16, 16, 16), full.crop(0, 0, 16, 16)
            terrain[c + stage] = ('overlay', bottom, False)
            terrain[c + stage + '_TOP'] = ('overlay', top, True)
    young = k.img('tree_small')
    trees = {'YOUNG': young}
    for t, fruit in (('FRUIT', ('fp', 'frd', 5)), ('APPLE', ('fr', 'frd', 6)), ('PEACH', ('fp', 'fr', 6))):
        trees[t] = k.paint(F.round_tree('small', S.LEAF, 't0', S.BARK, 'k0', seed=4, fruit=fruit))
    for t, im in trees.items():
        terrain[t + '_TOP'] = ('overlay', im.crop(0, 0, 16, 16), True)
        terrain[t + '_BOTTOM'] = ('overlay', im.crop(0, 16, 16, 16), False)

    def extra(gf_, ts, out, art_):
        imgs = {'TILLED': soil, 'TILLED_WET': wet, 'TILLED_FERT': tilled_fert, 'TILLED_WET_FERT': wet_fert,
                'SOIL': k.cells('dirt_b')}
        OF.add_soil_quads(gf_, FitTS(gf_, ts), out, imgs)

    decor = CM.decor_table(k, ctx.decor, outdoor_decor(k, S, {
        'ROCK': 'rock', 'BENCH': k.paint(TP.bench(S.WOOD, ['s1', 's2'], 'k0')),
        'SACKS': k.paint(TP.sacks(['k2', 'k3', 'k4'], 'k0', 'k1')), 'HAY_BALE': 'hay_round',
        'LOG': k.paint(F.log_h(['k1', 'k2', 'k3', 'k4'], 'k0', 'k4', 'k2')),
        'PEBBLES': k.paint(PR.pebbles(['s1', 's2', 's3', 's4', 's5'], 's0', 5)),
        'SMALL_FLOWERS': k.paint(X.small_flowers(['fr', 'fp', 'fw'], 'k1')),
        'CART': CM.at_bottom(k.img('cart'), 2, 2), 'WHEELBARROW': k.paint(X.wheelbarrow(S.WOOD, ['s1', 's2', 's3'], 'k0')),
        'PUMPKINS': 'crop_pumpkin_3', 'PRESERVES_JAR': 'preserves',
        'PRESS': k.paint(X.cider_press(['k1', 'k2', 'k3'], ['s1', 's2', 's3'], 'k0')).crop(0, 0, 16, 32),
        'DRIER': 'drying_rack@0,1', 'FARM_GATE': fence.crop(48, 16, 16, 16),
    }))
    return {
        'set': SET,
        'terrain': terrain,
        'add_terrain': ['GRASS_C', 'GRASS_D'],
        'variant_of': {'GRASS_C': 'GRASS', 'GRASS_D': 'GRASS'},
        'legend': {'.': [('GRASS', 7), ('GRASS2', 3), ('GRASS_C', 3), ('GRASS_D', 2), ('GRASS3', 1)]},
        'water': k.frames('water'), 'water_period': 16,
        'path': k.img('path'),
        'blends': {'SOIL': CM.blend_block(k, k.cells('dirt_b'), grass, rim_out='g2', seed=3),
                   'DIRT': CM.blend_block(k, k.cells('dirt'), grass, rim_out='g2', seed=5)},
        'stamps': {'FARMHOUSE': k.img('farmhouse')},
        'masses': {'forest': CM.forest_mass(forest)},
        'extra': extra,
        'decor': decor,
    }
