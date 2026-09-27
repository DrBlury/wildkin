#!/usr/bin/env python3
"""Colours and palette banks of the NORTH region (owner: W-NORTH): the
'snow' tileset (Frostpine Pass, Frosthollow, Whitecrown Peak, the Rime
Hall, the hot spring, the Sky Isle) and the 'cave' tileset (Glimmer
Caverns, Starfall Grotto). tools/tilesets/ts_snow.py, ts_cave.py and
tools/decor_north.py all share these, so decor fits the tileset banks.

Light comes from the top-left like the rest of the Vale's art. Snow is
never pure white: it is a cold blue-white ramp so white highlights,
sparkles and ice still read on it.
"""

NORTH_COLORS = {
    # --- snow (ground) ------------------------------------------------
    'sn_hi':   (252, 254, 255),
    'sn_lt':   (232, 242, 252),
    'sn_base': (212, 226, 246),
    'sn_mid':  (184, 202, 236),
    'sn_dk':   (148, 168, 216),
    'sn_dkr':  (110, 126, 184),
    # --- ice ----------------------------------------------------------
    'ic_hi':   (228, 250, 255),
    'ic_lt':   (172, 226, 248),
    'ic_base': (126, 198, 240),
    'ic_mid':  (92, 160, 224),
    'ic_dk':   (62, 114, 192),
    # --- frosted grass in the drifts ------------------------------------
    'fg_hi':   (206, 236, 214),
    'fg_base': (138, 188, 164),
    'fg_dk':   (86, 138, 126),
    'fg_dkr':  (54, 92, 98),
    # --- icy water ------------------------------------------------------
    'iw_hi':   (212, 238, 250),
    'iw_lt':   (120, 180, 226),
    'iw_base': (72, 134, 200),
    'iw_mid':  (54, 104, 176),
    'iw_dk':   (38, 74, 140),
    # --- snowy pines ----------------------------------------------------
    'pn_out':  (20, 42, 52),
    'pn_hi':   (92, 158, 124),
    'pn_lt':   (62, 128, 104),
    'pn_base': (42, 100, 88),
    'pn_dk':   (30, 72, 72),
    # --- granite (cliffs, hall, rocks) -----------------------------------
    'rk_hi':   (182, 186, 208),
    'rk_lt':   (140, 144, 170),
    'rk_base': (106, 110, 140),
    'rk_dk':   (74, 78, 108),
    'rk_out':  (38, 42, 62),
    # --- warm windows (lit from inside) ------------------------------------
    'lw_hi':   (255, 244, 188),
    'lw_base': (248, 204, 104),
    'lw_dk':   (206, 136, 64),
    # --- hot spring water -------------------------------------------------
    'hs_hi':   (214, 250, 242),
    'hs_lt':   (140, 226, 216),
    'hs_base': (82, 186, 194),
    'hs_dk':   (46, 132, 158),
    # --- the Rime crest / aurora / moon moth --------------------------------
    'au_gr':   (120, 240, 184),
    'au_vi':   (184, 140, 248),
    # --- caves ------------------------------------------------------------
    'cv_hi':   (176, 164, 172),
    'cv_lt':   (138, 126, 140),
    'cv_base': (106, 96, 114),
    'cv_mid':  (82, 74, 94),
    'cv_dk':   (58, 52, 72),
    'cv_dkr':  (36, 32, 50),
    'cw_hi':   (150, 140, 170),
    'cw_lt':   (112, 102, 136),
    'cw_base': (84, 76, 110),
    'cw_dk':   (58, 52, 84),
    'cw_out':  (24, 20, 36),
    'mo_hi':   (178, 250, 212),
    'mo_base': (88, 200, 160),
    'mo_dk':   (44, 128, 120),
    'cr_hi':   (236, 248, 255),
    'cr_lt':   (150, 232, 252),
    'cr_base': (84, 190, 240),
    'cr_dk':   (58, 116, 206),
    'am_lt':   (228, 170, 252),
    'am_base': (170, 108, 232),
    'am_dk':   (108, 64, 172),
    'uw_hi':   (200, 236, 255),
    'uw_lt':   (92, 150, 208),
    'uw_base': (50, 92, 160),
    'uw_mid':  (38, 68, 130),
    'uw_dk':   (28, 46, 96),
    'nv_dk':   (14, 16, 40),
    'nv_base': (26, 30, 70),
    'nv_lt':   (46, 52, 110),
    'sy_hi':   (255, 250, 200),
    'sy_base': (248, 222, 120),
}

# Shared ramps
SNOW5 = ['sn_hi', 'sn_lt', 'sn_base', 'sn_mid', 'sn_dk']
ICE5 = ['ic_hi', 'ic_lt', 'ic_base', 'ic_mid', 'ic_dk']
ROCK5 = ['rk_hi', 'rk_lt', 'rk_base', 'rk_dk', 'rk_out']

# ---------------------------------------------------------------------------
# 'snow' tileset banks (8 x 15 colours)
# ---------------------------------------------------------------------------
SNOW_BANK_GROUND = SNOW5 + ['sn_dkr'] + ['fg_hi', 'fg_base', 'fg_dk', 'fg_dkr'] + ICE5
SNOW_BANK_WATER = ['iw_hi', 'iw_lt', 'iw_base', 'iw_mid', 'iw_dk'] + SNOW5 + ICE5
SNOW_BANK_PINES = ['pn_out', 'pn_hi', 'pn_lt', 'pn_base', 'pn_dk', 'k_lt', 'k_base', 'k_dk'] + \
    SNOW5 + ['sn_dkr', 'ic_lt']
# bank 3: the village props bank (decor_outdoor.TOWN_DECOR_BANK), so signposts,
# fences, benches, barrels, lantern posts... can be used in the snow too.
# bank 4: the north decor bank (decor_north.py)
NORTH_DECOR_BANK = ['b_out', 'white', 'rk_hi', 'rk_lt', 'rk_base', 'rk_dk',
                    'hs_hi', 'hs_lt', 'hs_base', 'hs_dk', 'ic_lt', 'ic_base', 'ic_dk',
                    'au_gr', 'au_vi']
SNOW_BANK_ROOF = ['b_out'] + SNOW5 + ['rf_hi', 'rf_lt', 'rf_base', 'rf_dk', 'rf_dkr',
                                      'st_hi', 'st_lt', 'st_mid', 'ic_lt']
SNOW_BANK_ROCK = ROCK5 + SNOW5 + ICE5
SNOW_BANK_WALLS = ['sn_base', 'sn_mid', 'b_out', 'wd_lt', 'wd_base', 'wd_dk', 'st_hi', 'st_lt',
                   'st_mid', 'lw_hi', 'lw_base', 'lw_dk', 'ic_lt', 'sn_hi', 'sn_lt']

# ---------------------------------------------------------------------------
# 'cave' tileset banks (tools/tilesets/ts_cave.py)
# ---------------------------------------------------------------------------
CAVE_BANK_FLOOR = ['cv_lt', 'cv_base', 'cv_mid', 'cv_dk', 'cv_dkr', 'mo_hi', 'mo_base', 'mo_dk',
                   'cr_hi', 'cr_lt', 'cr_base', 'cr_dk', 'am_lt', 'am_base', 'cw_out']
CAVE_BANK_WATER = ['uw_hi', 'uw_lt', 'uw_base', 'uw_mid', 'uw_dk', 'cv_hi', 'cv_lt', 'cv_base',
                   'cv_mid', 'cv_dk', 'cv_dkr', 'cr_lt', 'cr_base', 'cr_hi', 'nv_dk']
CAVE_BANK_WALLS = ['cw_hi', 'cw_lt', 'cw_base', 'cw_dk', 'cw_out', 'cv_lt', 'cv_base', 'cv_mid',
                   'cv_dk', 'cv_dkr', 'am_lt', 'am_base', 'white', 'cr_lt', 'cr_base']
CAVE_DECOR_BANK = ['b_out', 'white', 'cr_hi', 'cr_lt', 'cr_base', 'cr_dk', 'am_lt', 'am_base',
                   'am_dk', 'cw_hi', 'cw_lt', 'cw_base', 'cw_dk', 'mo_hi', 'mo_base']
CAVE_BANK_MOUTH = ['cv_lt', 'cv_base', 'cv_mid', 'cv_dk', 'cv_dkr', 'sn_hi', 'sn_lt', 'sn_base',
                   'sn_mid', 'sn_dk', 'mo_base', 'mo_dk', 'lw_hi', 'lw_base', 'lw_dk']
CAVE_BANK_SKY = ['nv_dk', 'nv_base', 'nv_lt', 'white', 'sy_hi', 'sy_base', 'cr_lt', 'cv_lt',
                 'cv_base', 'cv_mid', 'cv_dk', 'cv_dkr', 'am_lt', 'am_base', 'cr_hi']
CAVE_BANK_CRYSTAL = ['cw_hi', 'cw_lt', 'cw_base', 'cw_dk', 'cw_out', 'cv_dkr', 'cr_hi', 'cr_lt',
                     'cr_base', 'cr_dk', 'wd_lt', 'wd_base', 'wd_dk', 'b_out', 'lw_base']
