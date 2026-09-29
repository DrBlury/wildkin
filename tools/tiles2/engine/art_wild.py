"""WILD (routes, woods, lakes, hills, the copper mine) drawn from tiles2 `verdant`."""

import paint as P
import props as PR
import extras as X
import farmart as FA
import buildings as B
import terrain as T
import sets.verdant as V

from .load import kit, over
from . import common as CM
from .art_town import kin_statue, sunflowers, small_wheel

SET = 'verdant'

LOGH = {'out': 'k0', 'roof': ['ra0', 'ra1', 'ra2', 'ra3', 'ra4'], 'wall': ['k1', 'k2', 'k3'],
        'trim': ['k0', 'k1', 'k2'], 'glass': ['gl0', 'gl1', 'gl2'], 'found': ['k0', 'k1', 'k2'],
        'chimney': ['k0', 'k1', 'k2'], 'door': ['k0', 'k1', 'k2']}
SAND = {'dk': 'd2', 'mid': 'd3', 'base': 'd4', 'lt': 'd5', 'hi': 'd5'}
SHADE = {'dk': 'g0', 'mid': 'g1', 'base': 'g2', 'lt': 'g3', 'hi': 'g4', 'out': 'g0'}


def outdoor_decor(k, M, extra):
    """Decor shared by the temperate sets (town / wild / farm / coast...):
    M is the tiles2 set module (role ramps); extra overrides. Pieces whose
    entries a set lacks are left out (the decor table then reports them)."""
    wood = getattr(M, 'WOOD', ['k1', 'k2', 'k3', 'k4'])
    items = {
        'FENCE': lambda: 'fence@2,0', 'FENCE_END': lambda: 'fence@0,0', 'GATE': lambda: 'fence@3,1',
        'HAY_BALE': lambda: k.paint(FA.hay_round(['k3', 'fy', 'fw'], 'k1')), 'WATER_TROUGH': lambda: 'trough',
        'BIG_TREE': lambda: 'tree_b',
        'HEDGE': lambda: CM.hedge_piece(k, M.LEAF, 't0', 3, 't1', {(-1, 0), (1, 0)}),
        'HEDGE_END': lambda: CM.hedge_piece(k, M.LEAF, 't0', 3, 't1', {(-1, 0)}),
        'BOULDER': lambda: 'rock_big', 'BRIDGE_H': lambda: CM.bridge_cell_h(k.img('bridge_h')),
        'BRIDGE_V': lambda: CM.bridge_cell_v(k.img('bridge_v')), 'CART': lambda: CM.at_bottom(k.img('cart'), 2, 2),
        'KIN_STATUE': lambda: kin_statue(k),
        'SHRINE': lambda: k.paint(X.shrine(wood[-4:], ['k1', 'k2', 'k3'], M.STONE, ('fo', 'fy'), 'k0', w=16, h=32)),
        'SIGN_ARROW': lambda: 'arrow_sign', 'PUMPKINS': lambda: 'crop_pumpkin_3',
        'SUNFLOWERS': lambda: sunflowers(k), 'CROPS': lambda: 'crop_wheat_3', 'BERRY_BUSH': lambda: 'bush_berry',
        'WATERWHEEL': lambda: ([small_wheel(k, f) for f in range(2)], 8),
    }
    t = {}
    for name, fn in items.items():
        if name in extra:
            continue
        try:
            t[name] = fn()
        except (KeyError, ValueError, AttributeError):
            pass
    t.update(extra)
    return t


def art(ctx):
    k = kit(SET)
    grass = k.cells('grass')
    forest = CM.forest_render(k, V.LEAF, 't0', V.BARK, 'k0', seed=1)
    pines = CM.forest_render(k, V.PINE, 'p0', V.BARK, 'k0', seed=2, r=4.8)
    sand = k.paint(P.speckle_ground(SAND, 3, dots=7, pebbles=0))
    sand2 = k.paint(P.speckle_ground(dict(SAND, peb='s3', peb_hi='s5', peb_dk='s1'), 4, dots=6, pebbles=2))
    floor = k.paint(P.grass(SHADE, 11, tufts=2, flecks=4))
    floor2 = k.paint(P.grass(SHADE, 12, tufts=3, flecks=2))
    meadow = k.paint(P.grass(V.GRASS, 13, tufts=2, flecks=2,
                             flowers={'n': 4, 'petals': ['fw', 'fy'], 'center': 'fy'}))
    face1 = k.img('cliff_face_single')
    face9 = k.img('cliff_face')
    terrain = {
        'GRASS': grass, 'GRASS2': k.cells('grass_b'), 'GRASS3': k.cells('grass_flowers'),
        'GRASS_C': k.cells('grass_c'), 'GRASS_D': k.cells('grass_d'), 'GRASS_P': k.cells('grass_pebbles'),
        'GRASS_F': over(k.cells('grass_c'), k.img('small_flowers')),
        'TALLGRASS': k.cells('grass_b'), 'REEDS': k.cells('grass_b'),
        'FLOWER_RED': ('anim', k.frames('flowers_red'), 32),
        'FLOWER_YELLOW': ('anim', k.frames('flowers_yellow'), 32),
        'TREE_TOP': ('mass', 'forest'), 'TREE_BOTTOM': ('mass', 'forest'),
        'PINE_TOP': ('mass', 'pines'), 'PINE_BOTTOM': ('mass', 'pines'),
        'LEDGE': k.cells('ledge', 1, 0), 'LEDGE_L': k.cells('ledge', 0, 0), 'LEDGE_R': k.cells('ledge', 2, 0),
        'SAND': sand, 'SAND2': sand2, 'FOREST': floor, 'FOREST2': floor2,
        'STONE': k.paint(T.flagstones(['s0', 's1', 's2', 's3'], seed=3)),
        'CLIFF': CM.cell_of(face1, 1, 0), 'CLIFF_FACE': CM.cell_of(face9, 1, 1),
        'DIRT': k.cells('dirt'), 'MEADOW': meadow,
        'MEADOW2': k.paint(P.grass(V.GRASS, 17, tufts=3, flecks=2,
                                   flowers={'n': 3, 'petals': ['fw', 'fy'], 'center': 'fy'})),
        'MEADOW3': k.paint(P.grass(V.GRASS, 19, tufts=2, flecks=3,
                                   flowers={'n': 2, 'petals': ['fw', 'fp'], 'center': 'fy'})),
    }
    stamps = {
        'CABIN': k.paint(B.house(80, 64, LOGH, door_at=40, windows=[(8, 6), (58, 6)], chimney=12, siding='log')),
        'STATION': k.paint(B.house(80, 64, LOGH, door_at=40, windows=[(8, 6), (58, 6)], siding='plank',
                                   roof_style='tile', door_w=16)),
    }
    storm = [k.paint(PR.standing_stone(V.STONE, 's0', w=32, h=48, seed=7, rune=r)) for r in ('fy', 'fo', 'fw', 'fo')]
    fall = k.frames('waterfall')
    foam = k.frames('river_foam')
    decor = CM.decor_table(k, ctx.decor, outdoor_decor(k, V, {
        'DOCK': 'dock@1,1', 'DOCK_EDGE': 'dock@1,2', 'DOCK_POST': 'bollard',
        'STORMSTONE': (storm, 20), 'ORE_PILE': 'copper_rock',
        'RAILS_H': 'rails@0,0', 'RAILS_V': 'rails@1,0',
        'HEADFRAME': k.paint(X.headframe(V.WOOD, ['s1', 's2', 's3'], 'k0', w=32, h=48)),
        'ELDER_TREE': 'tree_big', 'SUNFLOWERS': sunflowers(k, 'frd'),
        'WILD_WATERFALL': ([f.crop(0, 0, 32, 32) for f in fall], 8),
        'WILD_RIVER_FOAM': ([CM.pair(f, f.flip_h()) for f in foam], 10),
    }))
    return {
        'set': SET,
        'terrain': terrain,
        'add_terrain': ['GRASS_C', 'GRASS_D', 'GRASS_P', 'GRASS_F', 'MEADOW2', 'MEADOW3'],
        'variant_of': {'GRASS_C': 'GRASS', 'GRASS_D': 'GRASS', 'GRASS_P': 'GRASS', 'GRASS_F': 'GRASS',
                       'MEADOW2': 'MEADOW', 'MEADOW3': 'MEADOW'},
        'legend': {'.': [('GRASS', 6), ('GRASS2', 3), ('GRASS_C', 2), ('GRASS_D', 2), ('GRASS3', 1),
                         ('GRASS_P', 1), ('GRASS_F', 1)],
                   'm': [('MEADOW', 7), ('MEADOW2', 5), ('MEADOW3', 4)]},
        'water': k.frames('water'), 'water_period': 16,
        'path': k.img('path'),
        'blends': {
            'SAND': CM.blend_block(k, sand, grass, rim_in='d2', rim_out='g2', seed=3),
            'DIRT': k.img('dirt_patch'),
            'MEADOW': CM.blend_block(k, meadow, grass, seed=5, E=3.0, amp=1.0),
            'FOREST': CM.blend_block(k, floor, grass, rim_out='g2', seed=7),
        },
        'stamps': stamps,
        'masses': {'forest': CM.forest_mass(forest), 'pines': CM.forest_mass(pines, 'PINE_TOP', 'PINE_BOTTOM')},
        'elev': CM.elev(k, grass, ('s4', 's3', 's1', 's0', 's2')),
        'grass_colors': {'g_hi': 'g5', 'g_lt': 'g4', 'g_base': 'g3', 'g_mid': 'g2', 'g_dk': 'g1', 'g_dkr': 'g0',
                         't_base': 't3', 't_mid': 't2', 't_dk': 't1', 'k_base': 'k2', 'k_dk': 'k1', 'k_lt': 'k3',
                         'f_red': 'fr', 'f_redd': 'frd', 'f_yel': 'fy', 'f_yeld': 'fyd', 'white': 'fw',
                         's_hi': 'd5', 's_base': 'd4', 's_mid': 'd3', 's_dk': 'd2'},
        'decor': decor,
    }
