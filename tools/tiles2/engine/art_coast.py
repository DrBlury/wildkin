"""COAST (beaches, harbours, fens, fjords) drawn from tiles2 `coast`."""

from core import Img
import paint as P
import terrain as T
import flora as F
import props as PR
import townprops as TP
import coastart as C
import extras as X
import sets.coast as S

from .load import kit, over
from . import common as CM
from .art_wild import outdoor_decor

SET = 'coast'

HUT = {'out': 'k0', 'roof': ['k0', 'k1', 'k2', 'k3', 'k4'], 'wall': ['k1', 'k2', 'k3'],
       'trim': ['k0', 'k1', 'k2'], 'glass': ['gl0', 'gl1', 'gl2'], 'found': ['k0', 'k1', 'k2'],
       'chimney': ['k0', 'k1', 'k2'], 'door': ['k0', 'k1', 'k2']}


def gull_post(k):
    img = Img(16, 32)
    img.paste(k.img('bollard'), 0, 16)
    img.paste(k.img('gull', 0), 0, 4)
    return img


def art(ctx):
    k = kit(SET)
    grass = k.cells('grass')
    sand = k.cells('sand')
    forest = CM.forest_render(k, S.LEAF, 't0', ['k1', 'k2', 'k3'], 'k0', seed=4)
    palm = k.paint(C.palm(['t0', 't2', 't3', 't5'], 't0', ['k1', 'k2', 'k3'], 'k0', coconut=['k0', 'k1', 'k3'],
                          w=16, h=32, lean=1))
    flowers = lambda petal, dk, ce, seed: [k.paint(F.flower_patch(grass, petal, dk, ce, 'g2', frame=f, seed=seed,
                                                                  kind='daisy')) for f in range(2)]
    rock9 = k.img('cliff_face')
    bh = k.paint(PR.bridge_h(S.WOOD, 'k0'))
    bv = k.paint(PR.bridge_v(S.WOOD, 'k0'))
    terrain = {
        'GRASS': grass, 'GRASS2': k.cells('grass_b'), 'GRASS3': k.cells('grass_c'), 'GRASS_C': k.cells('grass_d'),
        'TALLGRASS': k.cells('grass_b'), 'DUNEGRASS': k.cells('dune'),
        'FLOWER_RED': ('anim', flowers('sa5', 'sa3', 'sa2', 5), 32),
        'FLOWER_YELLOW': ('anim', flowers('sg3', 'sg2', 'sa5', 9), 32),
        'SAND': sand, 'SAND2': k.cells('sand_b'), 'SAND3': k.cells('sand_c'),
        'SAND_S': ('fit', over(sand, k.img('shells'))), 'SAND_W': ('fit', over(k.cells('sand_b'), k.img('seaweed'))),
        'GRASS_F': ('fit', over(k.cells('grass_c'), k.img('small_flowers'))),
        'STONE': k.paint(T.flagstones(['b1', 'b2', 'b3', 'b4'], seed=4)),
        'QUAY': k.paint(T.cobbles(['b1', 'b2', 'b3', 'b4'], 'b0', seed=3)),
        'SHELF': CM.cell_of(rock9, 1, 1),
        'TIDEPOOL': ('fit', over(CM.cell_of(rock9, 1, 1), k.paint(C.coral(['co0', 'co1', 'co2'], 'k0', kind='brain')))),
        'SALTPAN': k.paint(P.speckle_ground({'dk': 'sa2', 'mid': 'sa3', 'base': 'sa5', 'lt': 'sa5', 'hi': 'sa5'},
                                            7, dots=4, pebbles=0, cracks=1)),
        'DUNE_LEDGE': ('fit', over(sand, CM.cell_of(k.cells('ledge', 0, 0, 4, 1), 1, 0))),
        'PINE_TOP': ('mass', 'forest'), 'PINE_BOTTOM': ('mass', 'forest'),
        'PALM_TOP': ('overlay', palm.crop(0, 0, 16, 16), True),
        'PALM_BOTTOM': ('overlay', palm.crop(0, 16, 16, 16), False),
        'VOID': Img(16, 16, k.role('e0')),
    }
    RED, BLUE = S.RED, S.BLUE
    stamps = {
        'HEAL': CM.hearth(k, RED, 5, 4, 2, ('wl2', 'ra4', 'ra2'), windows=[(6, 6), (62, 6)], roof_style='tile',
                          siding='plank'),
        'SHOP': CM.house(k, BLUE, 5, 4, 2, windows=[(6, 8), (62, 8)], roof_style='slate',
                         awning=(24, 55, ['rb1', 'wl2', 'rb3'])),
        'HOUSE_RED': CM.house(k, RED, 5, 4, 2, windows='auto', roof_style='tile', chimney=58, siding='plank'),
        'HOUSE_BLUE': CM.house(k, BLUE, 5, 4, 2, windows='auto', roof_style='slate', shutters=('rb1', 'rb2')),
        'HARBOR': CM.house(k, BLUE, 5, 4, 2, windows=[(6, 6), (62, 6)], roof_style='slate', siding='plank',
                           gable=True),
        'INN': CM.house(k, RED, 5, 4, 2, windows='auto', roof_style='tile', siding='plank', beams=True, chimney=10),
        'HALL': CM.house(k, BLUE, 7, 5, 3, windows='auto', roof_style='slate', storeys=2, beams=True, door_w=16),
        'HUT': CM.house(k, HUT, 3, 3, 1, windows=None, gable=True, siding='plank', roof_style='thatch',
                        roof_h=24, door_w=12),
        'CAVE': CM.cell_of(k.img('cave_mouth'), 1, 2),
    }
    decor = CM.decor_table(k, ctx.decor, outdoor_decor(k, S, {
        'MAILBOX': 'bollard', 'ROCK': 'sea_rock', 'BENCH': k.paint(TP.bench(S.WOOD, ['b1', 'b2'], 'k0')),
        'CRATE_STACK': k.paint(X.crate_stack(S.WOOD, 'k0')), 'SACKS': k.paint(TP.sacks(['k2', 'k3', 'k4'], 'k0', 'k1')),
        'FLOWER_POT': 'bush', 'PLANTER': 'driftwood', 'MARKET_STALL': 'fish_stall',
        'LANTERN_POST': 'shell_lamp', 'CAMPFIRE': ([k.paint(PR.campfire(S.WOOD, 'k0', ('sa4', 'co1', 'co0'), f))
                                                    for f in range(3)], 10),
        'WOODPILE': 'driftwood', 'STUMP': 'driftwood@0,0', 'LOG': 'driftwood',
        'BOULDER': k.paint(PR.big_rock(S.ROCK, 'b0', 4)), 'PEBBLES': 'shells', 'SMALL_FLOWERS': 'small_flowers',
        'BRIDGE_H': CM.bridge_cell_h(bh), 'BRIDGE_V': CM.bridge_cell_v(bv),
        'PICNIC_TABLE': k.paint(X.picnic_table(S.WOOD, 'k0')), 'CLOTHESLINE': 'nets@0,1',
        'WEATHER_VANE': k.paint(TP.weather_vane(['b1', 'b2', 'b3'], 'k0', 'k3')),
        'PIER_POST': 'bollard',
        'FISHING_BOAT': k.paint(C.fishing_boat('rb2', 'rb1', S.WOOD, ['wl0', 'wl1', 'wl2'], 'k0', w=32, h=32)),
        'FERRY_BOAT': k.paint(X.ferry_boat(['rb0', 'rb1', 'rb2'], ['k1', 'k2', 'k3'], ['wl0', 'wl1', 'wl2'], 'k0',
                                           w=48, h=32)),
        'LIGHTHOUSE': ([k.paint(C.lighthouse(['wl0', 'wl1', 'wl2'], ['ra0', 'ra2', 'ra3'], g, ['k1', 'wl0', 'wl1'],
                                             'k0', w=32, h=64))
                        for g in (['gl0', 'gl1', 'gl2'], ['gl1', 'gl2', 'wl2'])], 24),
        'NETS': 'nets@0,1', 'FISH_STALL': 'fish_stall@0,0', 'STARFISH': 'shells', 'SEAWEED': 'seaweed',
        'SALT_HEAP': 'salt_heap@0,0', 'BELL_BUOY': 'bell_buoy@0,1', 'GULL_POST': gull_post(k),
        'SHRINE': 'heron_statue', 'COAST_CORAL_CLUSTER': CM.at_bottom(k.img('coral_branch'), 2, 2, 8),
        'HAY_BALE': 'salt_heap@0,0',
    }))
    return {
        'set': SET,
        'terrain': terrain,
        'add_terrain': ['GRASS_C', 'GRASS_F', 'SAND_S', 'SAND_W'],
        'variant_of': {'GRASS_C': 'GRASS', 'GRASS_F': 'GRASS', 'SAND_S': 'SAND', 'SAND_W': 'SAND'},
        'legend': {'.': [('GRASS', 8), ('GRASS2', 3), ('GRASS_C', 3), ('GRASS3', 1), ('GRASS_F', 1)],
                   's': [('SAND', 10), ('SAND2', 2), ('SAND3', 2), ('SAND_S', 1), ('SAND_W', 1)]},
        'water': k.frames('sea'), 'water_period': 18,
        'path': CM.blend_block(k, k.cells('sand_c'), grass, rim_in='sa2', rim_out='g2', lip='sa4', seed=11),
        'path_alt': (CM.blend_block(k, k.cells('sand_wet'), sand, seed=13, amp=1.1),
                     ['SAND', 'SAND2', 'SAND3', 'SAND_S', 'SAND_W', 'SALTPAN', 'DUNEGRASS']),
        'blends': {'SAND': k.img('sand_patch')},
        'stamps': stamps,
        'masses': {'forest': CM.forest_mass(forest, 'PINE_TOP', 'PINE_BOTTOM')},
        'elev': CM.elev(k, grass, ('b5', 'b4', 'b2', 'b0', 'b3'), rock_out='b0', rock_dk='b1', deck_imgs=(bh, bv)),
        'grass_colors': {'g_hi': 'g5', 'g_lt': 'g4', 'g_base': 'g3', 'g_mid': 'g2', 'g_dk': 'g1', 'g_dkr': 'g0',
                         's_hi': 'sa5', 's_base': 'sa4', 's_mid': 'sa3', 's_dk': 'sa2'},
        'decor': decor,
    }
