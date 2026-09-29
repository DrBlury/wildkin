"""TOWN (Maple Village, Brookmill, Mistbell) drawn from tiles2 `hamlet`."""

from core import Img, G
import flora as F
import props as PR
import townprops as TP
import buildings as B
import extras as X
import farmart as FA
import sets.hamlet as H

from .load import kit, over
from . import common as CM

SET = 'hamlet'


def court(k, line=None):
    """Bout ring floor: packed sand with chalk lines."""
    img = k.cells('dirt_c').copy()
    chalk = k.role('fw')
    if line == 'h':
        for x in range(16):
            img.p[7][x] = chalk
            img.p[8][x] = chalk
    elif line == 'v':
        for y in range(16):
            img.p[y][7] = chalk
            img.p[y][8] = chalk
    return img


def court_circle(k):
    img = Img(32, 32)
    base = k.cells('dirt_c')
    for y in range(32):
        for x in range(32):
            img.p[y][x] = base.p[y % 16][x % 16]
            d = ((x + 0.5 - 16) ** 2 + (y + 0.5 - 16) ** 2) ** 0.5
            if 9.0 <= d < 11.0:
                img.p[y][x] = k.role('fw')
    return img


def hearth_hall_5x4(k):
    hall = B.house(80, 64, H.style(['ra0', 'ra1', 'ra2', 'ra3', 'ra4']), door_at=40,
                   windows=[(6, 6), (62, 6)], roof_style='tile', beams=True, door_w=16, roof_h=30,
                   sign=(32, 6, 16, 8), emblem=None)
    B.flame_emblem('wl2', 'ra4', 'ra2')(hall, 40, 51)
    return k.paint(hall)


KIN_STATUE = '''
....o......o....
...oho....omo...
...ohlo..olmdo..
...ohllooolmdo..
...olllllllmdo..
..ollhllllllmdo.
..olhooldloomdo.
..ollllhlllllmdo
..olllllllllmdo.
...ollllllllmdo.
....olllllmmdo..
....oollllmdoo..
...olhllllllmdo.
..olhllllllllmdo
..ollllllllllmdo
..olllllllllmmdo
..olllllllllmmdo
..ollllllllmmmdo
..ooommmmmmmoooo
..ohhhhhhhhhhmdo
..ohllllllllllmo
..ommmmmmmmmmmmo
..oooooooooooooo
'''


def kin_statue(k, ramp=('s0', 's1', 's2', 's3', 's4')):
    body = G(KIN_STATUE, dict(zip('odmlh', ramp)))
    img = Img(16, 32)
    img.paste(body, 0, 32 - body.h - 1)
    return k.paint(img)


def sunflowers(k, centre='d1', stem=('g1', 'g2', 'g3'), petal='fy', tip='fw'):
    img = Img(16, 32)
    for (x, top) in ((3, 6), (8, 2), (12, 8)):
        for y in range(top + 4, 31):
            img.p[y][x] = k.role(stem[0]) if y % 5 else k.role(stem[1])
        for (lx, ly) in ((x - 1, top + 12), (x + 1, top + 16)):
            img.p[ly][lx] = k.role(stem[2])
            img.p[ly][lx + (1 if lx > x else -1)] = k.role(stem[1])
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                if dx * dx + dy * dy <= 10:
                    img.p[top + 2 + dy][x + dx] = k.role(petal) if dx * dx + dy * dy > 2 else k.role(centre)
        img.p[top][x - 1] = k.role(tip)
    return img


def small_wheel(k, frame, wood=('k1', 'k2', 'k3'), foam='fw', out='k0'):
    import math
    img = Img(16, 16)
    wood = [k.role(r) for r in wood]
    cx, cy = 8, 8
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if 6.0 <= d < 7.5:
                img.p[y][x] = wood[1] if y < 8 else wood[0]
    for i in range(4):
        a = (i / 4.0 + frame / 8.0) * math.pi
        for t in range(1, 7):
            x, y = int(cx + math.cos(a) * t), int(cy + math.sin(a) * t)
            img.p[y][x] = wood[2]
            x, y = int(cx - math.cos(a) * t), int(cy - math.sin(a) * t)
            img.p[y][x] = wood[2]
    for x in range(1, 15):
        if (x + frame) % 3 == 0:
            img.p[15][x] = k.role(foam)
    return img.outline(k.role(out))


def art(ctx):
    k = kit(SET)
    grass = k.cells('grass')
    forest = CM.forest_render(k, H.LEAF, 't0', H.BARK, 'k0', seed=1)
    bridge_h = k.img('bridge_h')
    bridge_v = k.img('bridge_v')
    hedge = lambda cells: CM.hedge_piece(k, H.LEAF, 't0', 3, 't1', cells)

    terrain = {
        'GRASS': grass, 'GRASS2': k.cells('grass_b'), 'GRASS3': k.cells('grass_flowers'),
        'GRASS_C': k.cells('grass_c'), 'GRASS_D': k.cells('grass_d'), 'GRASS_P': k.cells('grass_pebbles'),
        'GRASS_F': over(k.cells('grass_c'), k.img('small_flowers')),
        'TALLGRASS': k.cells('grass_b'),
        'FLOWER_RED': ('anim', k.frames('flowers_red'), 32),
        'FLOWER_YELLOW': ('anim', k.frames('flowers_yellow'), 32),
        'STONE': k.cells('cobble'),
        'TREE_TOP': ('mass', 'forest'), 'TREE_BOTTOM': ('mass', 'forest'),
        'COURT': court(k), 'COURT_LINE_H': court(k, 'h'), 'COURT_LINE_V': court(k, 'v'),
    }
    stamps = {
        'HOUSE_RED': k.img('house_red'),
        'HOUSE_BLUE': k.img('house_blue'),
        'LAB': k.img('workshop'),
        'SHOP': k.img('shop'),
        'HEAL': hearth_hall_5x4(k),
        'COURT_CIRCLE': court_circle(k),
    }
    wood = H.WOOD
    fountain = [k.paint(TP.fountain(['c1', 'c1', 'c2', 'c3'], ['w1', 'w2', 'w4', 'w5'], 'g0', f, w=32, h=32))
                for f in range(4)]
    cart = CM.at_bottom(k.img('cart'), 2, 2)
    shrine = k.paint(X.shrine(wood, ['k1', 'k2', 'k3'], H.STONE, ('fo', 'fy'), 'k0', w=16, h=32))
    line = k.img('clothesline')
    clothes = Img(32, 16)
    clothes.paste(line.crop(0, 8, 16, 16), 0, 0)
    clothes.paste(line.crop(32, 8, 16, 16), 16, 0)
    bell = k.paint(TP.bell_tower(['wl0', 'wl1', 'wl2'], H.TRIM, ['ra0', 'ra1', 'ra2', 'ra3'],
                                 ['ra1', 'ra3', 'ra4'], 'k0', w=16, h=32))
    decor = {
        'SIGNPOST': k.img('signpost'), 'MAILBOX': k.img('mailbox'),
        'FENCE': k.cells('fence', 2, 0), 'FENCE_END': k.cells('fence', 0, 0), 'GATE': k.cells('fence', 3, 1),
        'LAMP': k.img('lamp'), 'ROCK': k.img('rock'), 'BUSH': k.img('bush'), 'BENCH': k.img('bench'),
        'BARREL': k.img('barrel'), 'CRATE': k.img('crate'), 'CRATE_STACK': k.img('crate_stack'),
        'SACKS': k.img('sacks'), 'FLOWER_POT': k.img('flower_pot'), 'PLANTER': k.img('planter'),
        'WELL': k.img('well'),
        'HAY_BALE': k.paint(FA.hay_round(['k3', 'fy', 'fw'], 'k1')),
        'WATER_TROUGH': k.img('trough'), 'MARKET_STALL': k.img('market_stall'),
        'OLD_HEARTH': k.img('old_hearth'), 'LANTERN_POST': k.img('lantern_post'),
        'STONE_LANTERN': k.img('stone_lantern'), 'CAMPFIRE': (k.frames('campfire'), 10),
        'FLAG': (k.frames('flag'), 12), 'TENT': k.img('tent'), 'WOODPILE': k.img('woodpile'),
        'STUMP': k.img('stump'), 'LOG': k.img('log'), 'BIG_TREE': k.img('tree_b'),
        'HEDGE': hedge({(-1, 0), (1, 0)}), 'HEDGE_END': hedge({(-1, 0)}),
        'BOULDER': k.img('rock_big'), 'PEBBLES': k.img('pebbles'), 'FALLEN_LEAVES': k.img('fallen_leaves'),
        'SMALL_FLOWERS': k.img('small_flowers'), 'LILY_PADS': k.img('lily_pads'),
        'BRIDGE_H': CM.bridge_cell_h(bridge_h), 'BRIDGE_V': CM.bridge_cell_v(bridge_v),
        'FOUNTAIN': (fountain, 8), 'PICNIC_TABLE': k.img('picnic_table'),
        'NOTICE_BOARD': k.img('notice_board'), 'CART': cart, 'WHEELBARROW': k.img('wheelbarrow'),
        'SCARECROW': k.img('scarecrow'), 'KIN_STATUE': kin_statue(k), 'SHRINE': shrine,
        'SIGN_ARROW': k.img('arrow_sign'), 'CLOTHESLINE': clothes, 'BEEHIVE': k.img('beehive'),
        'WEATHER_VANE': k.img('weather_vane'), 'RAIN_GAUGE': k.img('rain_gauge'),
        'PUMPKINS': k.img('crop_pumpkin_3'), 'SUNFLOWERS': sunflowers(k),
        'BUNTING': k.cells('bunting', 1, 0), 'CROPS': k.img('crop_wheat_3'),
        'WATERWHEEL': ([small_wheel(k, f) for f in range(2)], 8),
        'TOWN_CLIFF_HUT': k.img('storehouse'), 'TOWN_SIGNAL_BELL': bell,
    }
    return {
        'set': SET,
        'terrain': terrain,
        'add_terrain': ['GRASS_C', 'GRASS_D', 'GRASS_P', 'GRASS_F'],
        'variant_of': {'GRASS_C': 'GRASS', 'GRASS_D': 'GRASS', 'GRASS_P': 'GRASS', 'GRASS_F': 'GRASS'},
        'legend': {'.': [('GRASS', 6), ('GRASS2', 3), ('GRASS_C', 2), ('GRASS_D', 2), ('GRASS3', 1),
                         ('GRASS_P', 1), ('GRASS_F', 1)]},
        'water': k.frames('water'), 'water_period': 16,
        'path': k.img('path'),
        'path_alt': (CM.blend_block(k, k.cells('dirt'), k.cells('cobble'), rim_in='d2', rim_out='c1', seed=9,
                                    E=3.0, amp=0.5), ['STONE']),
        'stamps': stamps,
        'masses': {'forest': CM.forest_mass(forest)},
        'elev': CM.elev(k, grass, ('c4', 'c3', 'c1', 'c0', 'c2')),
        'grass_colors': {'g_hi': 'g5', 'g_lt': 'g4', 'g_base': 'g3', 'g_mid': 'g2', 'g_dk': 'g1', 'g_dkr': 'g0'},
        'decor': decor,
    }
