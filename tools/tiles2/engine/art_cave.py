"""CAVE (caverns, mines, grottoes, root tunnels) drawn from tiles2 `cave`."""

from core import Img
import props as PR
import caveart as CA
import extras as X
import sets.cave as S

from .load import kit, over
from . import common as CM

SET = 'cave'
POOL9 = {'POOL': (1, 2), 'POOL_N': (1, 1), 'POOL_S': (1, 3), 'POOL_W': (0, 2), 'POOL_E': (2, 2),
         'POOL_NW': (0, 1), 'POOL_NE': (2, 1), 'POOL_SW': (0, 3), 'POOL_SE': (2, 3)}


def art(ctx):
    k = kit(SET)
    floor = k.cells('floor')
    rock = k.cells('rock_top')
    face1 = k.img('cliff_face_single')
    wall = CM.cell_of(face1, 1, 0)
    crystal = k.img('crystal')
    pools = k.frames('pool')
    terrain = {
        'FLOOR': floor, 'FLOOR2': k.cells('floor_b'), 'FLOOR3': k.cells('floor_c'), 'FLOOR_D': k.cells('floor_d'),
        'FLOOR_P': ('fit', over(floor, k.img('pebbles'))), 'FLOOR_B': ('fit', over(k.cells('floor_b'), k.img('bones'))),
        'MOSS': k.cells('floor_moss'), 'ROCK': rock, 'WALL': wall,
        'WALL_CRYSTAL': ('fit', over(wall, crystal)), 'CRYSTAL': ('fit', over(floor, crystal)),
        'LEDGE': k.cells('ledge', 1, 0), 'LEDGE_L': k.cells('ledge', 0, 0), 'LEDGE_R': k.cells('ledge', 2, 0),
        'MOUTH': CM.mouth(wall, k.role('v0'), k.role('cr0')), 'VOID': Img(16, 16, k.role('v0')),
    }
    for n, (cx, cy) in POOL9.items():
        terrain[n] = ('anim', [p.crop(cx * 16, cy * 16, 16, 16) for p in pools], 20)
    bh = k.img('rope_bridge')
    bv = bh.rot90()
    decor = CM.decor_table(k, ctx.decor, {
        'ROCK': 'rock', 'CRATE_STACK': k.paint(X.crate_stack(S.WOOD, 'k0')),
        'SACKS': k.paint(__import__('townprops').sacks(['k2', 'k3', 'k4'], 'k0', 'k1')),
        'LANTERN_POST': CM.at_bottom(k.img('lantern'), 1, 2),
        'CAMPFIRE': ([k.paint(PR.campfire(S.WOOD, 'k0', ('fy', 'fo', 'co1'), f)) for f in range(3)], 10),
        'LOG': k.paint(__import__('flora').log_h(['k1', 'k2', 'k3', 'k4'], 'k0', 'k4', 'k2')),
        'BOULDER': 'rock_big', 'BRIDGE_H': CM.bridge_cell_h(bh), 'BRIDGE_V': CM.bridge_cell_v(bv),
        'SIGN_ARROW': k.paint(PR.arrow_sign(S.WOOD, 'k0')), 'CAVE_CRYSTAL': 'crystal',
        'STALAGMITE': 'stalagmite@0,1', 'GLOWCAP': 'glowcaps', 'ORE_ROCKS': 'ore_copper',
        'RAILS_H': 'rails@0,0', 'RAILS_V': 'rails@1,0', 'ORE_CART': 'mine_cart', 'ORE_PILE': 'ore_copper',
        'CAVE_FUNGAL_SHELF': CM.at_bottom(k.img('fungal_shelf'), 2, 2, 8),
    })
    return {
        'set': SET,
        'terrain': terrain,
        'add_terrain': ['FLOOR_D', 'FLOOR_P', 'FLOOR_B'],
        'variant_of': {'FLOOR_D': 'FLOOR', 'FLOOR_P': 'FLOOR', 'FLOOR_B': 'FLOOR'},
        'legend': {'.': [('FLOOR', 8), ('FLOOR2', 3), ('FLOOR3', 2), ('FLOOR_D', 2), ('FLOOR_P', 1)]},
        'water': k.frames('pool'), 'water_period': 20,
        'path': CM.blend_block(k, k.paint(__import__('paint').speckle_ground(
            {'dk': 'cf1', 'mid': 'cf2', 'base': 'cf2', 'lt': 'cf3', 'hi': 'cf4'}, 17, dots=6, pebbles=1)),
            floor, seed=13, amp=1.2),
        'stamps': {'STAIRS_DOWN': CM.cell_of(k.img('stairs_down'), 0, 1),
                   'STAIRS_UP': CM.cell_of(k.img('stairs_up'), 0, 1),
                   'CRACK': CM.cell_of(k.img('crack'), 0, 1)},
        'elev': CM.elev(k, rock, ('cf5', 'cf4', 'cf2', 'cr0', 'cf3'), rock_out='cr0', rock_dk='cr1',
                        deck_imgs=(bh, bv)),
        'grass_colors': {'mo_hi': 'ms2', 'mo_base': 'ms1', 'mo_dk': 'cf3', 'cv_mid': 'cf2', 'cv_dk': 'cf1',
                         'cv_dkr': 'cf0', 'cr_lt': 'bn1', 'cr_hi': 'bn2', 'cr_base': 'bn0'},
        'decor': decor,
    }
