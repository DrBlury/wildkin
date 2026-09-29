"""INTERIOR (every house, shop, hall and lodge) drawn from tiles2 `interior`."""

import interiorart as IN
import extras as X
import sets.interior as I

from .load import kit, over
from . import common as CM

SET = 'interior'


def art(ctx):
    k = kit(SET)
    floor = k.cells('floor_wood')
    checker = k.cells('floor_checker')
    top = k.cells('wall_cream_top')
    win = k.paint(IN.window(I.WOOD, 'gl', ['sk0', 'sk1'], 'k0', w=16, h=16))
    terrain = {
        'VOID': k.cells('void'), 'FLOOR': floor, 'FLOOR2': checker,
        'WALL_TOP': top, 'WALL': k.cells('wall_cream_low'),
        'WINDOW': ('fit', over(top, win)),
        'WALL_CLOCK': ('fit', over(top, k.img('clock_wall'))), 'PAINTING': ('fit', over(top, k.img('picture'))),
        'DOORMAT': ('fit', over(floor, k.img('door_mat'))),
        'COUNTER': ('fit', over(checker, k.img('counter_mid'))),
        'COUNTER_L': ('fit', over(checker, k.img('counter_left'))),
        'COUNTER_R': ('fit', over(checker, k.img('counter_right'))),
        # extra wallpapers and floors for the map redesign (legend below)
        'WALL_BLUE_TOP': k.cells('wall_blue_top'), 'WALL_BLUE': k.cells('wall_blue_low'),
        'WALL_GREEN_TOP': k.cells('wall_green_top'), 'WALL_GREEN': k.cells('wall_green_low'),
        'WALL_BRICK_TOP': k.cells('wall_brick_top'), 'WALL_BRICK': k.cells('wall_brick_low'),
        'FLOOR_B': k.cells('floor_wood_b'), 'FLOOR_STONE': k.cells('floor_stone'),
        'WINDOW_BLUE': ('fit', over(k.cells('wall_blue_top'), win)),
        'WINDOW_GREEN': ('fit', over(k.cells('wall_green_top'), win)),
        'WINDOW_BRICK': ('fit', over(k.cells('wall_brick_top'), win)),
    }
    for paper in ('blue', 'green', 'brick'):
        wall = k.cells('wall_%s_top' % paper)
        terrain['WALL_%s_CLOCK' % paper.upper()] = ('fit', over(wall, k.img('clock_wall')))
        terrain['WALL_%s_PICTURE' % paper.upper()] = ('fit', over(wall, k.img('picture')))
    add = ['WALL_BLUE_TOP', 'WALL_BLUE', 'WALL_GREEN_TOP', 'WALL_GREEN', 'WALL_BRICK_TOP', 'WALL_BRICK',
           'FLOOR_B', 'FLOOR_STONE', 'WINDOW_BLUE', 'WINDOW_GREEN', 'WINDOW_BRICK',
           'WALL_BLUE_CLOCK', 'WALL_BLUE_PICTURE', 'WALL_GREEN_CLOCK', 'WALL_GREEN_PICTURE',
           'WALL_BRICK_CLOCK', 'WALL_BRICK_PICTURE']
    rug_img = CM.over_tiled(k.img('rug'), floor)
    MT = I.METAL
    decor = CM.decor_table(k, ctx.decor, {
        'TV': 'radio', 'PLANT': 'plant_tall', 'PC': 'terminal', 'HEAL_MACHINE': 'hearth_flame',
        'LAB_MACHINE': 'machine', 'CHAIR_SIDE': 'chair', 'LONG_TABLE': 'table_long',
        'SMALL_RUG': k.paint(IN.rug(['bl0', 'bl1', 'bl2', 'fy'], 'k0', w=32, h=16)),
        'DOUBLE_BED': 'bed_double', 'WARDROBE': k.paint(IN.wardrobe(I.WOOD, 'k0', w=16, h=32)),
        'DRESSER': 'chest', 'BARREL_IN': 'barrel', 'SACKS_IN': 'sacks',
        'SINK_COUNTER': CM.at_bottom(k.img('sink'), 1, 2), 'SMALL_PLANT': 'plant', 'FLOWER_VASE': 'vase',
        'VASE': k.paint(IN.vase(['bl0', 'bl1', 'bl2'], ['ck2', 'bl2'], 'k0')),
        'GRANDFATHER_CLOCK': 'clock', 'FLOOR_LAMP': 'lamp',
        'LANTERN_RACK': CM.at_bottom(k.img('lantern_rack'), 2, 2),
        'BREAD_DISPLAY': CM.at_bottom(k.img('bread_display'), 2, 2), 'TELESCOPE_IN': 'telescope',
        'SPECIMEN_SHELF': k.paint(IN.shop_shelf(['k0', 'k1', 'k2'], [('lf0', 'lf1', 'lf2'), ('k1', 'fy', 'pc2')],
                                                'k0', w=16, h=32)),
        'DISPLAY_CASE': k.paint(IN.aquarium('ck2', ['ck0', 'ck1', 'ck2'], 'fy', ['k0', 'k1', 'k2'], 'k0', w=32, h=16)),
        'AQUARIUM': k.paint(IN.aquarium('ck2', ['bl0', 'bl1', 'bl2'], 'fy', ['k0', 'k1', 'k2'], 'k0', w=32, h=16)),
        'WORK_BOARD': CM.at_bottom(k.img('work_board'), 2, 2), 'FARM_CHEST': 'chest',
        'FZ_EXTRACTOR': 'fusion_extractor', 'FZ_MIXER': 'fusion_mixer', 'FZ_LOOM': 'fusion_loom',
        'FZ_TANKS': 'fusion_tanks',
        'PYLON': ([k.paint(X.pylon(MT, ['sc1', 'sc2'], 'k0', f, h=16)) for f in range(2)], 24),
        'BIKE_DISPLAY': 'bike_display@0,1', 'VOLT_BANNER': 'volt_banner',
    })
    return {
        'set': SET,
        'terrain': terrain,
        'add_terrain': add, 'ground': ['FLOOR_B', 'FLOOR_STONE'],
        'attrs': {n: 1 for n in add if n.startswith('WALL') or n.startswith('WINDOW')},
        'legend': {'.': [('FLOOR', 12), ('FLOOR_B', 4)], 'B': 'WALL_BLUE_TOP', 'b': 'WALL_BLUE',
                   'G': 'WALL_GREEN_TOP', 'g': 'WALL_GREEN', 'R': 'WALL_BRICK_TOP', 'r': 'WALL_BRICK',
                   '_': 'FLOOR_STONE', 'N': 'WINDOW_BLUE', 'M': 'WINDOW_GREEN', 'O': 'WINDOW_BRICK',
                   # clocks and pictures on the other wallpapers (k / p are on cream)
                   'K': 'WALL_BLUE_CLOCK', 'P': 'WALL_BLUE_PICTURE', 'C': 'WALL_GREEN_CLOCK',
                   'Y': 'WALL_GREEN_PICTURE', 'Q': 'WALL_BRICK_CLOCK', 'Z': 'WALL_BRICK_PICTURE'},
        'stamps': {'RUG': rug_img},
        'decor': decor,
    }
