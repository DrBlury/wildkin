"""Rootcoil: exposed buttress roots, deep canopy and braided jade water."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import biome_art as art

# 0 leaf litter/path; 1 river; 2 stone/elevation; 3 canopy; 4 roots/vines;
# 5 woven hut; 6 wooden deck; 7 orchids/moss.
BANKS = [
    ['bio_jungle_hi', 'bio_jungle_lt', 'bio_jungle_mid', 'bio_jungle_dk', 'bio_jungle_out', 'bio_jungle_moss', 'bio_jungle_bark'],
    ['bio_jungle_foam', 'w_hi', 'bio_jungle_water', 'bio_jungle_water_dk', 'bio_jungle_out'],
    ['bio_jungle_out', 'bio_jungle_moss', 'bio_jungle_hi', 'bio_jungle_lt', 'bio_jungle_mid', 'bio_jungle_dk', 'bio_jungle_bark'],
    ['bio_jungle_out', 'bio_jungle_moss', 'bio_jungle_hi', 'bio_jungle_lt', 'bio_jungle_mid', 'bio_jungle_dk', 'bio_jungle_bloom'],
    ['bio_jungle_out', 'bio_jungle_bark', 'bio_jungle_bark_dk', 'bio_jungle_moss', 'bio_jungle_lt', 'bio_jungle_mid'],
    ['bio_jungle_out', 'bio_jungle_roof_lt', 'bio_jungle_roof', 'bio_jungle_bark', 'bio_jungle_bark_dk', 'bio_jungle_hi',
     'bio_jungle_thatch_lt', 'bio_jungle_wicker'],
    ['bio_jungle_out', 'bio_jungle_bark', 'bio_jungle_bark_dk', 'bio_jungle_roof_lt', 'bio_jungle_roof', 'bio_jungle_moss'],
    ['bio_jungle_out', 'bio_jungle_hi', 'bio_jungle_lt', 'bio_jungle_mid', 'bio_jungle_dk', 'bio_jungle_moss', 'bio_jungle_bloom', 'bio_jungle_pink'],
]
USES_DECOR = ['JUNGLE_BUTTRESS', 'JUNGLE_VINES', 'JUNGLE_CANOPY',
              'JUNGLE_WOVEN_HUT', 'JUNGLE_ORCHID', 'JUNGLE_ROOT_BRIDGE']
ELEV = {'t_out': 'bio_jungle_out', 'k_lt': 'bio_jungle_moss', 'k_base': 'bio_jungle_mid', 'k_dk': 'bio_jungle_dk',
        'g_hi': 'bio_jungle_moss', 'g_lt': 'bio_jungle_hi', 'g_base': 'bio_jungle_lt', 'g_mid': 'bio_jungle_mid',
        'g_dk': 'bio_jungle_dk', 'g_dkr': 'bio_jungle_out',
        'b_out': 'bio_jungle_out', 'wd_lt': 'bio_jungle_roof_lt', 'wd_base': 'bio_jungle_bark', 'wd_dk': 'bio_jungle_bark_dk'}


def build(gf, name):
    gf.register_colors(art.COLORS)
    gf.check_banks(name, BANKS)
    ts = gf.TileSet(name, BANKS, limit=768)
    out = dict(ts=ts, terrain=[], meta_b=[], meta_t=[], stamps=[],
               docs={'LOAM': 'dappled jungle floor', 'ROOTS': 'walkable exposed roots',
                     'THICKET': 'encounter fronds', 'BOULDER': 'solid mossy stone',
                     'CANOPY': 'solid layered broadleaf roof', 'DOOR': 'woven threshold (exit)'})
    art.animated_water(gf, ts, out, ('bio_jungle_foam', 'w_hi', 'bio_jungle_water', 'bio_jungle_water_dk'))

    def add(n, im, bank=0):
        out['terrain'].append(n)
        out['meta_b'].append(ts.meta(im, prefer=(bank,), where=name + '.' + n))
        out['meta_t'].append([0, 0, 0, 0])

    add('LOAM', art.ground('bio_jungle_mid', 'bio_jungle_lt', 'bio_jungle_dk', 2, 'leaf'))
    add('LOAM2', art.ground('bio_jungle_mid', 'bio_jungle_moss', 'bio_jungle_out', 8, 'leaf'))
    add('ROOTS', art.dune('bio_jungle_bark', 'bio_jungle_moss', 'bio_jungle_bark_dk', 1), 4)
    add('THICKET', art.brush('bio_jungle_mid', 'bio_jungle_out', 'bio_jungle_lt', 'bio_jungle_moss', 5), 3)
    add('BOULDER', art.rock('bio_jungle_mid', 'bio_jungle_moss', 'bio_jungle_lt', 'bio_jungle_out', 9, 'bio_jungle_hi'), 2)
    add('CANOPY', art.rock('bio_jungle_dk', 'bio_jungle_moss', 'bio_jungle_lt', 'bio_jungle_out', 4, 'bio_jungle_bloom'), 3)
    add('VINE_WALL', art.brush('bio_jungle_dk', 'bio_jungle_out', 'bio_jungle_bark', 'bio_jungle_lt', 4), 4)
    add('PLATFORM', art.ground('bio_jungle_bark', 'bio_jungle_roof_lt', 'bio_jungle_bark_dk', 1, 'leaf'), 6)
    add('DOOR', art.door('bio_jungle_bark', 'bio_jungle_out', 'bio_jungle_roof', 'bio_jungle_roof_lt'), 5)
    art.add_path(gf, ts, out, ('bio_jungle_bark', 'bio_jungle_dk', 'bio_jungle_moss', 'bio_jungle_mid'))
    return gf.finish_tileset(out, name, 'JU',
        attrs={'THICKET': gf.A_GRASS, 'BOULDER': gf.A_SOLID, 'CANOPY': gf.A_SOLID,
               'VINE_WALL': gf.A_SOLID, 'DOOR': gf.A_EXIT},
        ground=['LOAM', 'LOAM2', 'ROOTS', 'PLATFORM'], overlay=[],
        legend={'.': [('LOAM', 12), ('LOAM2', 4)], '=': 'PATH', '~': 'WATER',
                ',': 'THICKET', '#': [('BOULDER', 5), ('CANOPY', 11)],
                'D': 'DOOR', 'r': 'ROOTS', 'P': 'PLATFORM', 'V': 'VINE_WALL'},
        oob='CANOPY', default_ground='LOAM', backdrop='ground', elev=ELEV)
