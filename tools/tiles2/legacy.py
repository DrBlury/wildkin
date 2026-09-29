#!/usr/bin/env python3
"""Old-to-new name map for switching the maps to the second-generation sets.

For every old tileset (TS_*), the set that replaces it and, for every old
decor kind (DK_*) and building stamp (MT_*) its maps use, the new entry
to place instead. Resolution: an explicit alias below, otherwise the old
name in lower case (SIGNPOST -> signpost). Block pieces are written
'entry:col,row' (a single cell of a fence / rails / ledge block).

    python3 tools/tiles2/legacy.py            # check every used kind resolves
    python3 tools/tiles2/legacy.py --json     # write assets/tiles2/legacy_map.json

The check parses src/game/world/**/ (map -> tileset, map -> decor list) so
it follows the live map data; kinds with no counterpart are listed.
"""

import collections
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ASSETS = os.path.join(ROOT, 'assets', 'tiles2')

NEW_SET = {
    'WILD': 'verdant', 'TOWN': 'hamlet', 'FARM': 'farm', 'COAST': 'coast', 'SNOW': 'snow', 'CAVE': 'cave',
    'VOLCANIC': 'volcanic', 'DESERT': 'desert', 'JUNGLE': 'jungle', 'GRIM': 'grim', 'DUSK': 'dusk',
    'DREAM': 'dream', 'CRYPT': 'crypt', 'TIDE': 'tide', 'CITY': 'city', 'INTERIOR': 'interior',
}

# Aliases that hold in every set (old kind -> new entry).
COMMON = {
    'FENCE': 'fence:2,0', 'FENCE_END': 'fence:0,0', 'GATE': 'fence:3,1', 'FARM_GATE': 'fence:3,1',
    'HEDGE': 'hedge', 'HEDGE_END': 'hedge', 'BIG_TREE': 'tree_big', 'ELDER_TREE': 'tree_big',
    'SIGN_ARROW': 'arrow_sign', 'LAMP': 'lamp', 'CITY_LAMP': 'lamp', 'DOCK_EDGE': 'dock', 'DOCK_POST': 'bollard',
    'PIER_POST': 'bollard', 'RAILS_H': 'rails:0,0', 'RAILS_V': 'rails:1,0', 'ORE_ROCKS': 'ore_copper',
    'KIN_STATUE': 'statue', 'WILD_WATERFALL': 'waterfall', 'WILD_RIVER_FOAM': 'river_foam',
    'CROPS': 'crop_wheat_3', 'SUNFLOWERS': 'crop_sunflower_3', 'PUMPKINS': 'crop_pumpkin_3',
    'STARFISH': 'shells', 'MOONSTONE': 'moon_orb', 'STEAM_VENT': 'vent', 'FORGE_ANVIL': 'anvil',
    'LAVA_ORE_CART': 'mine_cart', 'SMALL_FLOWERS': 'small_flowers', 'TESLA_COIL': 'beacon', 'PARKED_BIKE': 'bike',
    'RAILING': 'railing:2,0', 'GULL_POST': 'gull', 'COAST_CORAL_CLUSTER': 'coral_branch',
    'FROZEN_TREE': 'pine', 'SNOW_CAIRN': 'cairn', 'CAVE_CRYSTAL': 'crystal', 'GLOWCAP': 'glowcaps',
    'CAVE_FUNGAL_SHELF': 'fungal_shelf', 'HALL_COLUMN': 'column', 'GROT_PILLAR': 'coral_pillar',
    'STANDING_MIRROR': 'mirror', 'FLOAT_PAGES': 'pages', 'DREAM_STATUE': 'statue', 'MOON_LANTERN': 'moon_lantern',
    'BOOKCASE': 'bookcase', 'LANTERN_POST': 'lantern_post', 'DESERT_WAYPOST': 'signpost',
    'DESERT_CACTUS': 'saguaro', 'DESERT_CACTUS_BLOOM': 'saguaro_bloom', 'DESERT_DUNE_TUFT': 'dry_tuft',
    'DESERT_ADOBE_HUT': 'adobe_hut', 'DESERT_WELL': 'well', 'DESERT_JAR': 'jars', 'DESERT_CARAVAN_CANOPY': 'canopy_red',
    'JUNGLE_WAYPOST': 'waypost', 'JUNGLE_BUTTRESS': 'buttress_tree', 'JUNGLE_VINES': 'vines',
    'JUNGLE_CANOPY': 'forest', 'JUNGLE_WOVEN_HUT': 'woven_hut', 'JUNGLE_ORCHID': 'orchid',
    'JUNGLE_ROOT_BRIDGE': 'root_bridge', 'TOWN_CLIFF_HUT': 'storehouse', 'TOWN_SIGNAL_BELL': 'bell_tower',
    'WATER_TROUGH': 'trough', 'BUNTING': 'bunting', 'BERRY_BUSH': 'bush_berry',
    # grim / dusk
    'GR_SIGN': 'signpost', 'GR_GRAVE': 'grave_round', 'GR_CROSS': 'grave_cross', 'GR_FENCE': 'iron_fence:2,0',
    'GR_BONES': 'bones', 'GR_SHRUB': 'shrub', 'GR_STUMP': 'stump', 'GR_CART': 'cart', 'GR_LANTERN': 'lamp',
    'GR_WISP': 'wisp', 'GR_BELL': 'bell', 'GR_MOORING': 'mooring', 'GR_PUMPKIN': 'pumpkin', 'GR_MEMORIAL': 'memorial',
    # crypt
    'CR_SKULLS': 'skulls', 'CR_CANDLES': 'candles', 'CR_SARCOPHAGUS': 'sarcophagus', 'CR_COFFIN': 'coffin',
    'CR_BRAZIER': 'brazier', 'CR_URN': 'urn', 'CR_STATUE': 'statue', 'CR_BANNER': 'banner', 'CR_CHAINS': 'chains',
    'CR_THRONE': 'throne', 'CR_PEDESTAL': 'pedestal', 'CR_PLAQUE': 'signpost',
    # interior
    'BARREL_IN': 'barrel', 'SACKS_IN': 'sacks', 'SMALL_PLANT': 'plant', 'PLANT': 'plant_tall', 'SMALL_RUG': 'rug_blue',
    'FLOWER_VASE': 'vase', 'GRANDFATHER_CLOCK': 'clock', 'FLOOR_LAMP': 'lamp', 'HEAL_MACHINE': 'hearth_flame',
    'PC': 'terminal', 'LAB_MACHINE': 'machine', 'TELESCOPE_IN': 'telescope', 'TV': 'radio', 'CHAIR_SIDE': 'chair',
    'SINK_COUNTER': 'sink', 'FARM_CHEST': 'chest', 'FZ_EXTRACTOR': 'fusion_extractor', 'FZ_MIXER': 'fusion_mixer',
    'FZ_LOOM': 'fusion_loom', 'FZ_TANKS': 'fusion_tanks', 'PRESERVES_JAR': 'preserves', 'PRESS': 'cider_press',
    'DRIER': 'drying_rack', 'LONG_TABLE': 'table_long', 'DOUBLE_BED': 'bed_double',
}

# Per-set exceptions (new set -> old kind -> entry).
PER_SET = {
    'city': {'BIG_TREE': 'tree', 'HEDGE': 'hedge_bush', 'HEDGE_END': 'hedge_bush', 'BRIDGE_H': 'bridge',
             'BRIDGE_V': 'bridge', 'BEEHIVE': 'flower_pot', 'CART': 'crate', 'FENCE': 'railing:2,0',
             'FENCE_END': 'railing:0,0', 'FOUNTAIN': 'fountain', 'LILY_PADS': 'flower_pot', 'MARKET_STALL': 'kiosk',
             'NOTICE_BOARD': 'street_sign', 'PLANTER': 'planter_tree', 'ROCK': 'flower_pot', 'SACKS': 'crate',
             'SIGNPOST': 'street_sign', 'SIGN_ARROW': 'street_sign', 'CRATE_STACK': 'crate', 'PEBBLES': 'flower_pot',
             'FALLEN_LEAVES': 'hedge_bush', 'STONE_LANTERN': 'lamp', 'LANTERN_POST': 'lamp',
             'SMALL_FLOWERS': 'flower_pot', 'BUSH': 'hedge_bush'},
    'cave': {'BRIDGE_H': 'rope_bridge', 'BRIDGE_V': 'rope_bridge', 'LANTERN_POST': 'lantern', 'LOG': 'crate',
             'CAMPFIRE': 'lantern', 'SACKS': 'crate', 'CRATE_STACK': 'crate', 'SIGN_ARROW': 'signpost',
             'ORE_CART': 'mine_cart', 'ORE_PILE': 'ore_copper'},
    'coast': {'FENCE': 'fence:2,0', 'LANTERN_POST': 'shell_lamp', 'STUMP': 'driftwood', 'LOG': 'driftwood',
              'MARKET_STALL': 'fish_stall', 'FLOWER_POT': 'bush', 'PLANTER': 'bush', 'BENCH': 'crate',
              'CAMPFIRE': 'lobster_pots', 'CLOTHESLINE': 'nets', 'CRATE_STACK': 'crate', 'SACKS': 'crate',
              'MAILBOX': 'bollard', 'NOTICE_BOARD': 'signpost', 'PEBBLES': 'shells', 'PICNIC_TABLE': 'crate',
              'SHRINE': 'heron_statue', 'SIGN_ARROW': 'signpost', 'WEATHER_VANE': 'gull', 'WOODPILE': 'driftwood',
              'BRIDGE_H': 'dock', 'BRIDGE_V': 'dock', 'BOULDER': 'sea_rock', 'ROCK': 'sea_rock', 'NETS': 'nets'},
    'snow': {'DOCK': 'crate', 'DOCK_EDGE': 'crate', 'DOCK_POST': 'barrel', 'BRIDGE_H': 'fence:2,0',
             'BRIDGE_V': 'fence:1,1', 'CAMPFIRE': 'lamp', 'CART': 'sled', 'CLOTHESLINE': 'frost_banner',
             'CRATE_STACK': 'crate', 'GATE': 'fence:3,1', 'HAY_BALE': 'woodpile', 'KIN_STATUE': 'wolf_statue',
             'LANTERN_POST': 'lamp', 'LOG': 'woodpile', 'NOTICE_BOARD': 'signpost', 'PICNIC_TABLE': 'sled',
             'SACKS': 'crate', 'SHRINE': 'aurora_stone', 'SIGN_ARROW': 'signpost', 'STONE_LANTERN': 'lamp',
             'STUMP': 'rock', 'TELESCOPE': 'cairn', 'WATER_TROUGH': 'wash_bucket', 'WEATHER_VANE': 'lamp',
             'WELL': 'hot_spring', 'BENCH': 'sled'},
    'volcanic': {'BENCH': 'crate', 'CAMPFIRE': 'brazier', 'CRATE_STACK': 'crate', 'LANTERN_POST': 'signal',
                 'SACKS': 'crate', 'WATER_TROUGH': 'barrel', 'WOODPILE': 'coal_pile', 'FENCE_END': 'fence:0,0'},
    'dream': {'BARREL': 'rock', 'BENCH': 'column_broken', 'CRATE': 'rock', 'FENCE': 'column_broken',
              'FENCE_END': 'column', 'LANTERN_POST': 'moon_lantern', 'SIGNPOST': 'signpost', 'BOOKCASE': 'bookcase'},
    'farm': {'LOG': 'stump', 'PEBBLES': 'rock', 'SMALL_FLOWERS': 'weeds', 'HAY_BALE': 'hay_bale',
             'WHEELBARROW': 'cart', 'BENCH': 'crate', 'SACKS': 'crate'},
    'hamlet': {'BOULDER': 'boulder'},
    'verdant': {},
    'dusk': {'GR_LANTERN': 'lantern', 'GR_SIGN': 'signpost'},
}


# Old building stamps (MT_*) -> (new set, entry).
STAMPS = {
    'T_HOUSE_RED': ('hamlet', 'house_red'), 'T_HOUSE_BLUE': ('hamlet', 'house_blue'), 'T_LAB': ('hamlet', 'workshop'),
    'T_SHOP': ('hamlet', 'shop'), 'T_HEAL': ('hamlet', 'hearth_hall'), 'T_COURT_CIRCLE': ('hamlet', 'plaza'),
    'W_CABIN': ('verdant', 'cabin'), 'W_STATION': ('verdant', 'station'), 'I_RUG': ('interior', 'rug'),
    'CY_HEARTH': ('city', 'hearth_hall'), 'CY_MARKET': ('city', 'market_hall'), 'CY_VOLT_HALL': ('city', 'volt_hall'),
    'CY_WORKS': ('city', 'works'), 'CY_BIKE_SHOP': ('city', 'bike_shop'), 'CY_INN': ('city', 'inn'),
    'CY_HOUSE_A': ('city', 'townhouse_slate'), 'CY_HOUSE_B': ('city', 'townhouse_copper'),
    'CY_HOUSE_C': ('city', 'townhouse_clay'), 'CY_ROW_HOUSES': ('city', 'row_houses'),
    'CY_CLOCK_TOWER': ('city', 'clock_tower'),
    'CO_HEAL': ('coast', 'hearth_hall'), 'CO_SHOP': ('coast', 'shop'), 'CO_HOUSE_RED': ('coast', 'warehouse'),
    'CO_HOUSE_BLUE': ('coast', 'cottage'), 'CO_HARBOR': ('coast', 'harbour_house'), 'CO_INN': ('coast', 'inn'),
    'CO_HALL': ('coast', 'hall'), 'CO_HUT': ('coast', 'stilt_hut'), 'CO_CAVE': ('coast', 'cave_mouth'),
    'SN_HOUSE': ('snow', 'cabin'), 'SN_HEARTH': ('snow', 'hearth_hall'), 'SN_SHOP': ('snow', 'shop'),
    'SN_BATHS': ('snow', 'bathhouse'), 'SN_HALL': ('snow', 'hall'), 'SN_CAVE': ('snow', 'cave_mouth'),
    'CV_STAIRS_DOWN': ('cave', 'stairs_down'), 'CV_STAIRS_UP': ('cave', 'stairs_up'), 'CV_CRACK': ('cave', 'crack'),
    'GR_HOUSE': ('grim', 'house'), 'GR_SHOP': ('grim', 'shop'), 'GR_APOTHECARY': ('grim', 'apothecary'),
    'GR_HEARTH': ('grim', 'hearth_hall'), 'GR_CRYPT_HALL': ('grim', 'crypt_hall'), 'GR_BONE_GATE': ('grim', 'bone_gate'),
    'VO_HEARTH': ('volcanic', 'hearth_hall'), 'VO_SHOP': ('volcanic', 'shop'), 'VO_FORGE': ('volcanic', 'forge'),
    'VO_HOUSE': ('volcanic', 'bunkhouse'), 'VO_HOUSE_RUST': ('volcanic', 'house_rust'),
    'VO_ANVIL_HALL': ('volcanic', 'anvil_hall'), 'VO_CAVE_MOUTH': ('volcanic', 'cave_mouth'),
    'VO_TUNNEL_ARCH': ('volcanic', 'tunnel_arch'),
    'DR_HEARTH': ('dream', 'hearth_hall'), 'DR_SHOP': ('dream', 'shop'), 'DR_HOUSE': ('dream', 'house'),
    'DR_HOUSE_ROSE': ('dream', 'house_rose'), 'DR_TOWER': ('dream', 'spire'), 'DR_TOWER_ROSE': ('dream', 'spire_rose'),
    'DR_MIRROR_HALL': ('dream', 'mirror_hall'), 'DR_LIBRARY': ('dream', 'library'),
    'FA_FARMHOUSE': ('farm', 'farmhouse'),
    'DU_HOUSE': ('dusk', 'house'), 'DU_SHOP': ('dusk', 'shop'), 'DU_APOTHECARY': ('dusk', 'apothecary'),
    'DU_HEARTH': ('dusk', 'hearth_hall'), 'DU_CRYPT_HALL': ('dusk', 'crypt_hall'), 'DU_BONE_GATE': ('dusk', 'bone_gate'),
}

# Old terrain legend names -> new ground kinds (per replaced tileset the
# same idea holds: grass family, tall grass, path/water autotiles...).
TERRAIN = {
    'GRASS': 'grass (group)', 'GRASS2': 'grass (group)', 'GRASS3': 'grass (group)', 'TALLGRASS': 'tallgrass / tallgrass_patch',
    'FLOWER_RED': 'flowers_red', 'FLOWER_YELLOW': 'flowers_yellow', 'STONE': 'plaza / cobble',
    'TREE_TOP': 'tree (object, 2x2) or forest (mass layer)', 'TREE_BOTTOM': 'tree (object, 2x2) or forest (mass layer)',
    'PINE_TOP': 'pine', 'PINE_BOTTOM': 'pine', 'COURT': 'plaza', 'PATH': 'path (autotile)', 'WATER': 'water (autotile)',
    'VOID': 'void', 'FLOOR': 'floor_wood / floor_checker', 'WALL_TOP': 'wall_top', 'WALL': 'wall_*_top + wall_*_low',
    'WINDOW': 'window', 'DOORMAT': 'door_mat', 'COUNTER': 'counter_*', 'LEDGE': 'ledge:*',
}


def resolve(set_name, kind, entries):
    """New entry for an old kind in a set, or None if nothing fits."""
    for table in (PER_SET.get(set_name, {}), COMMON):
        if kind in table:
            tgt = table[kind]
            if tgt.split(':')[0] in entries:
                return tgt
    low = kind.lower()
    if low in entries:
        return low
    return None


def map_usage(root=ROOT):
    """{old tileset: {old decor kinds used by its maps}}"""
    maps = {}
    base = os.path.join(root, 'src', 'game', 'world')
    files = [f for f in glob.glob(os.path.join(base, '**', '*'), recursive=True) if f.endswith(('.h', '.inc', '.c'))]
    arrays = {}
    for f in files:
        s = open(f).read()
        for m in re.finditer(r'\[MAP_(\w+)\]\s*=\s*\{\s*[^,]+,\s*[^,]+,\s*TS_(\w+)\s*,([^}]*)', s):
            dec = re.findall(r'(\w+_DECOR)\b', m.group(3))
            maps[m.group(1)] = (m.group(2), dec[0] if dec else None)
        for m in re.finditer(r'DecorPlace\s+(\w+)\[\]\s*=\s*\{(.*?)\};', s, re.S):
            arrays[m.group(1)] = set(re.findall(r'DP\w*\(\s*(\w+)', m.group(2)))
    use = collections.defaultdict(set)
    for name, (ts, dec) in maps.items():
        if dec and dec in arrays:
            use[ts] |= arrays[dec]
    return use, maps


def entries_of(set_name):
    with open(os.path.join(ASSETS, set_name, set_name + '.json')) as f:
        return {e['name'] for e in json.load(f)['entries']}


def build_map():
    use, maps = map_usage()
    out = {'tilesets': {}, 'missing': {}}
    for ts, kinds in sorted(use.items()):
        new = NEW_SET.get(ts)
        if new is None:
            continue
        ents = entries_of(new)
        table = {}
        missing = []
        for k in sorted(kinds):
            r = resolve(new, k, ents)
            if r is None:
                missing.append(k)
            else:
                table[k] = r
        out['tilesets'][ts] = {'set': new, 'maps': sorted(m for m, (t, _) in maps.items() if t == ts),
                               'decor': table}
        if missing:
            out['missing'][ts] = missing
    stamps = {}
    for old, (st, ent) in STAMPS.items():
        stamps[old] = '%s.%s' % (st, ent)
        if ent not in entries_of(st):
            out['missing'].setdefault('STAMPS', []).append(old)
    out['stamps'] = stamps
    out['terrain'] = TERRAIN
    return out


def main(argv):
    m = build_map()
    for ts, miss in m['missing'].items():
        print('%-9s -> %-9s missing: %s' % (ts, NEW_SET.get(ts, '-'), ' '.join(miss)))
    n = sum(len(v['decor']) for v in m['tilesets'].values())
    print('%d old decor kinds resolved across %d tilesets, %d building stamps; %d unresolved' % (
        n, len(m['tilesets']), len(m['stamps']), sum(len(v) for v in m['missing'].values())))
    if '--json' in argv:
        with open(os.path.join(ASSETS, 'legacy_map.json'), 'w') as f:
            json.dump(m, f, indent=1)
            f.write('\n')
    return 1 if m['missing'] else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
