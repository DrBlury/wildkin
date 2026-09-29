"""Gravewood dusk: GRIM glyphs, metatile IDs, collision and decor with living
canopies and an authored blue-green/violet evening palette.
"""

from tilesets import ts_grim
import decor_grim

USES_DECOR = [decor.name for decor in decor_grim.DECOR if 'grim' in decor.sets]

# Palette entries retain their GRIM bank/index, including animated water and
# all existing decor. Unlisted lantern and ember accents stay warm.
DUSK_COLORS = {
    'grm_ash_hi': (196, 169, 202), 'grm_ash_lt': (160, 133, 177),
    'grm_ash': (125, 99, 153), 'grm_ash_md': (102, 76, 132),
    'grm_ash_dk': (76, 54, 105), 'grm_ash_dkr': (54, 38, 78),
    'grm_soot': (29, 25, 52), 'grm_rust': (183, 120, 115),
    'grm_straw_hi': (175, 190, 136), 'grm_straw': (128, 159, 108),
    'grm_straw_dk': (85, 116, 83),
    'grm_wat_hi': (164, 214, 207), 'grm_wat_lt': (91, 153, 163),
    'grm_wat': (49, 94, 120), 'grm_wat_dk': (28, 53, 81),
    'grm_mud_hi': (149, 116, 153), 'grm_mud': (112, 82, 126),
    'grm_mud_dk': (76, 56, 98), 'grm_peat': (45, 36, 69),
    'grm_moss_hi': (187, 212, 135), 'grm_moss': (108, 165, 115),
    'grm_moss_dk': (52, 105, 94),
    'grm_reed_hi': (183, 204, 150), 'grm_reed': (103, 147, 125),
    'grm_out': (22, 30, 52), 'grm_bark_hi': (170, 143, 153),
    'grm_bark_lt': (123, 100, 127), 'grm_bark': (84, 67, 106),
    'grm_bark_dk': (53, 48, 77), 'grm_char': (34, 39, 66),
    'grm_leaf_hi': (150, 218, 188), 'grm_leaf': (75, 166, 151),
    'grm_leaf_dk': (43, 105, 114), 'grm_hang': (158, 203, 166),
    'grm_bruise_lt': (183, 128, 190), 'grm_bruise': (119, 80, 143),
    'grm_st_hi': (187, 182, 207), 'grm_st_lt': (147, 145, 177),
    'grm_st': (107, 106, 147), 'grm_st_dk': (72, 71, 110),
    'grm_rf_hi': (172, 135, 191), 'grm_rf_lt': (139, 106, 163),
    'grm_rf': (105, 78, 135), 'grm_rf_dk': (72, 55, 104),
    'grm_rf_dkr': (46, 39, 75),
}


def build(gf, name):
    # Build under GRIM's style key: grass variants, elevation roles and all
    # metatile positions must be identical for region maps authored in GRIM.
    out = ts_grim.build(gf, 'grim', leafy=True)
    out['ts'].name = name
    out['ts'].palette_colors = DUSK_COLORS
    out['docs'] = dict(out['docs'], GNARL_TOP='living blue-green oak canopy over solid roots',
                       SNAG_TOP='clustered twilight foliage over charred roots')
    out['backdrop'] = (29, 25, 52)
    return out
