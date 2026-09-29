"""Sandstone terraces, wind-combed dunes and turquoise oasis (Sunwell)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import biome_art as art

# 0 sand/path; 1 water; 2 strata/elevation; 3 succulent; 4 adobe;
# 5 awning; 6 trim/props; 7 sparse oasis vegetation.
BANKS = [
    ['bio_desert_hi', 'bio_desert_lt', 'bio_desert_mid', 'bio_desert_dk', 'bio_desert_out', 'bio_desert_rust'],
    ['bio_desert_foam', 'w_hi', 'bio_desert_water', 'bio_desert_water_dk', 'bio_desert_out'],
    ['bio_desert_out', 'bio_desert_hi', 'bio_desert_lt', 'bio_desert_mid', 'bio_desert_dk', 'bio_desert_rust'],
    ['bio_desert_out', 'bio_jungle_hi', 'bio_jungle_lt', 'bio_jungle_mid', 'bio_jungle_dk', 'bio_desert_hi', 'bio_desert_rust'],
    ['bio_desert_out', 'bio_desert_adobe_lt', 'bio_desert_adobe', 'bio_desert_adobe_dk', 'bio_desert_roof', 'bio_desert_hi', 'bio_desert_water'],
    ['bio_desert_out', 'bio_desert_hi', 'bio_desert_lt', 'bio_desert_roof', 'bio_desert_rust', 'bio_desert_adobe_dk'],
    ['bio_desert_out', 'bio_desert_hi', 'bio_desert_lt', 'bio_desert_mid', 'bio_desert_adobe_dk', 'bio_desert_roof', 'bio_jungle_mid'],
    ['bio_desert_out', 'bio_jungle_hi', 'bio_jungle_lt', 'bio_jungle_mid', 'bio_jungle_dk', 'bio_desert_lt', 'bio_desert_mid'],
]
USES_DECOR = ['DESERT_CACTUS', 'DESERT_CACTUS_BLOOM', 'DESERT_DUNE_TUFT',
              'DESERT_ADOBE_HUT', 'DESERT_WELL', 'DESERT_JAR', 'DESERT_CARAVAN_CANOPY']
ELEV = {'t_out': 'bio_desert_out', 'k_lt': 'bio_desert_hi', 'k_base': 'bio_desert_mid', 'k_dk': 'bio_desert_dk',
        'g_hi': 'bio_desert_hi', 'g_lt': 'bio_desert_lt', 'g_base': 'bio_desert_mid', 'g_mid': 'bio_desert_mid',
        'g_dk': 'bio_desert_dk', 'g_dkr': 'bio_desert_out',
        'deck': 'stone', 'deck_roles': {'d_out': 'bio_desert_out', 'd_hi': 'bio_desert_hi', 'd_lt': 'bio_desert_lt',
                                     'd_base': 'bio_desert_mid', 'd_dk': 'bio_desert_dk', 'd_dkr': 'bio_desert_out'}}


def build(gf, name):
    gf.register_colors(art.COLORS)
    gf.check_banks(name, BANKS)
    ts = gf.TileSet(name, BANKS, limit=768)
    out = dict(ts=ts, terrain=[], meta_b=[], meta_t=[], stamps=[],
               docs={'SAND': 'wind-combed sand', 'DUNE': 'crescent ridge, walkable',
                     'ROCK': 'solid broken sandstone', 'SCRUB': 'encounter brush',
                     'DOOR': 'adobe doorway (exit)'})
    art.animated_water(gf, ts, out, ('bio_desert_foam', 'w_hi', 'bio_desert_water', 'bio_desert_water_dk'))

    def add(n, im, bank=0):
        out['terrain'].append(n)
        out['meta_b'].append(ts.meta(im, prefer=(bank,), where=name + '.' + n))
        out['meta_t'].append([0, 0, 0, 0])

    add('SAND', art.ground('bio_desert_lt', 'bio_desert_hi', 'bio_desert_mid', 1))
    add('SAND2', art.ground('bio_desert_lt', 'bio_desert_hi', 'bio_desert_dk', 6))
    add('DUNE', art.dune('bio_desert_mid', 'bio_desert_hi', 'bio_desert_dk', 2))
    add('DRY_WASH', art.ground('bio_desert_mid', 'bio_desert_lt', 'bio_desert_dk', 7))
    add('SCRUB', art.brush('bio_desert_mid', 'bio_desert_dk', 'bio_desert_rust', 'bio_desert_hi', 1))
    add('GARDEN', art.brush('bio_desert_mid', 'bio_jungle_dk', 'bio_jungle_mid', 'bio_jungle_hi', 3), 7)
    add('ROCK', art.rock('bio_desert_lt', 'bio_desert_hi', 'bio_desert_mid', 'bio_desert_out', 3), 2)
    add('ROCK2', art.rock('bio_desert_lt', 'bio_desert_hi', 'bio_desert_rust', 'bio_desert_out', 8), 2)
    add('ADOBE_WALL', art.rock('bio_desert_adobe', 'bio_desert_adobe_lt', 'bio_desert_adobe', 'bio_desert_adobe_dk', 5), 4)
    add('DOOR', art.door('bio_desert_mid', 'bio_desert_out', 'bio_desert_roof', 'bio_desert_hi'), 5)
    art.add_path(gf, ts, out, ('bio_desert_mid', 'bio_desert_dk', 'bio_desert_hi', 'bio_desert_lt'))
    return gf.finish_tileset(out, name, 'DE',
        attrs={'SCRUB': gf.A_GRASS, 'ROCK': gf.A_SOLID, 'ROCK2': gf.A_SOLID,
               'ADOBE_WALL': gf.A_SOLID, 'DOOR': gf.A_EXIT},
        ground=['SAND', 'SAND2', 'DUNE', 'DRY_WASH', 'GARDEN'], overlay=[],
        legend={'.': [('SAND', 12), ('SAND2', 4)], '=': 'PATH', '~': 'WATER',
                ',': 'SCRUB', '#': [('ROCK', 12), ('ROCK2', 4)], 'D': 'DOOR',
                'd': 'DUNE', 'w': 'DRY_WASH', 'A': 'ADOBE_WALL', 'h': 'GARDEN'},
        oob='ROCK', default_ground='SAND', backdrop='ground', elev=ELEV)
