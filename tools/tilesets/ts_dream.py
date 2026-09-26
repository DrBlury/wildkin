"""The 'dream' tileset (owner: W-FAR): MOONVEIL PATH, DREAMSPIRE, the MIRROR
HALL and the DUST LIBRARY.

Banks
  0 ground   moon grass, moonstone, moonpetals, cliffs, ledges, paths
  1 pond     the animated moon pond (the tileset's WATER) and its grass bank
  2 blossom  blossom trees + the Mirror Hall's glass floor and moonstone
  3 props    the shared village prop bank (signposts, benches, lamps...)
  4 library  plum wood, book spines, paper, lantern light (Dust Library;
             far decor)
  5 indigo   indigo roofs and the Mirror Hall's walls over plaster
  6 rose     rose roofs over plaster
  7 walls    windows, doors, wood and glass on plaster

The map legend is documented at the top of src/game/world/far/data.h.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import terrain_far as tf  # noqa: E402
import far_buildings as fb  # noqa: E402

USES_DECOR = ['SIGNPOST', 'BENCH', 'LANTERN_POST', 'FENCE', 'FENCE_END', 'BARREL', 'CRATE']

GROUND = ['ds_hi', 'ds_lt', 'ds_base', 'ds_mid', 'ds_dk', 'dg_hi', 'dg_lt', 'dg_base', 'dg_mid',
          'dg_dk', 'dp_hi', 'dp_base', 'dp_dk', 'b_out', 'vcr_base']
POND = ['vdw_hi', 'vdw_lt', 'vdw_base', 'vdw_mid', 'vdw_dk', 'dg_hi', 'dg_lt', 'dg_base', 'dg_mid',
        'dg_dk', 'ds_lt', 'ds_base', 'ds_dk', 'white', 'vcr_hi']
BLOSSOM = ['bt_hi', 'bt_lt', 'bt_base', 'bt_dk', 'bt_out', 'tk_lt', 'tk_base', 'tk_dk',
           'mf_hi', 'mf_lt', 'mf_base', 'mf_dk', 'vcr_hi', 'vcr_base', 'vcr_dk']
LIBRARY = ['vlw_hi', 'vlw_lt', 'vlw_base', 'vlw_dk', 'lw_out', 'bo_r', 'bo_g', 'bo_b', 'bo_y',
           'pg_hi', 'pg_base', 'pg_dk', 'lg_y', 'lg_o', 'lp_r']
_ROOF_REST = ['tw_hi', 'tw_base', 'tw_dk', 'b_out', 'st_hi', 'st_lt', 'st_mid', 'gl_dk', 'dg_base',
              'dg_mid']
INDIGO = ['ri_hi', 'ri_lt', 'ri_base', 'ri_dk', 'ri_dkr'] + _ROOF_REST
ROSE = ['ro_hi', 'ro_lt', 'ro_base', 'ro_dk', 'ro_dkr'] + _ROOF_REST
WALLS = ['dg_base', 'dg_mid', 'b_out', 'tw_hi', 'tw_base', 'tw_dk', 'st_hi', 'st_lt', 'st_mid',
         'wd_lt', 'wd_base', 'wd_dk', 'gl_hi', 'gl_base', 'gl_dk']

TERRAIN_DOC = {
    'GRASS': 'mint moon grass (+ GRASS2 dew, GRASS3 fallen petals)',
    'STONE': 'pale lilac moonstone flagstones (+ STONE2 cracked)',
    'MOONPETAL': 'tall moonpetal grass; wild kin roam here (top = front blades)',
    'MOONFLOWER': 'grass with little lilac moonflowers (walkable)',
    'BLOSSOM_TOP': '16x32 moon-blossom tree: TOP above BOTTOM; overlay',
    'CLIFF': 'pastel stone cliff with a grass lip (solid)',
    'CLIFF_FACE': 'plain pastel strata; stack under CLIFF (solid)',
    'LEDGE': 'one-way grass ledge: walk DOWN onto it to hop (+ _L/_R ends)',
    'MIRROR_FLOOR': 'the Mirror Hall floor: polished glass checker (+ MIRROR_STAR inlay)',
    'MIRROR_WALL_TOP': 'upper Mirror Hall wall (solid)',
    'MIRROR_WALL': 'lower Mirror Hall wall: a tall mirror panel (solid)',
    'MIRROR_MAT': 'Mirror Hall exit mat',
    'LIB_FLOOR': 'Dust Library plum floorboards',
    'LIB_SHELF_TOP': 'top of a wall of bookshelves (solid)',
    'LIB_SHELF': 'lower wall of bookshelves (solid)',
    'LIB_DUST': 'drifts of paper dust and fallen pages; wild kin roam here',
    'LIB_MAT': 'Dust Library exit mat',
}


def build(gf, name):
    gf.register_colors(tf.FAR_COLORS)
    banks = [GROUND, POND, BLOSSOM, list(gf.decor_outdoor.TOWN_DECOR_BANK), LIBRARY, INDIGO, ROSE,
             WALLS]
    gf.check_banks(name, banks)
    ts = gf.TileSet(name, banks)
    out = {'ts': ts, 'meta_b': [], 'meta_t': [], 'terrain': [], 'docs': TERRAIN_DOC}

    water_q = fb.add_quads_anim(gf, ts, out, tf.pond_quads, 3, 1, period=24)
    out['water_q'] = water_q

    def T(nm, img, prefer=(0,), top=None):
        out['terrain'].append(nm)
        out['meta_b'].append(ts.meta(img, prefer=prefer, where='%s.%s' % (name, nm)))
        out['meta_t'].append(ts.meta(top, prefer=prefer, where='%s.%s.top' % (name, nm), opaque=False)
                             if top else [0, 0, 0, 0])

    def O(nm, img, top_layer):
        out['terrain'].append(nm)
        gf.add_overlay_terrain(ts, out, nm, img, top=top_layer)

    T('GRASS', tf.moongrass_img(0))
    T('GRASS2', tf.moongrass_img(1))
    T('GRASS3', tf.moongrass_img(2))
    T('STONE', tf.moonstone_img(0))
    T('STONE2', tf.moonstone_img(1))
    mp_b, mp_t = tf.moonpetal_layers()
    T('MOONPETAL', mp_b, top=mp_t)
    T('MOONFLOWER', tf.moonflower_img())
    T('CLIFF', tf.dream_cliff(True))
    T('CLIFF_FACE', tf.dream_cliff(False, 1))
    T('LEDGE', tf.dream_ledge())
    T('LEDGE_L', tf.dream_ledge('L'))
    T('LEDGE_R', tf.dream_ledge('R'))
    tree = tf.blossom_tree_img()
    O('BLOSSOM_TOP', tree.crop(0, 0, 16, 16), True)
    O('BLOSSOM_BOTTOM', tree.crop(0, 16, 16, 16), False)
    # the Mirror Hall
    T('MIRROR_FLOOR', tf.mirror_floor_img(0), prefer=(2,))
    T('MIRROR_STAR', tf.mirror_floor_img(1), prefer=(2,))
    T('MIRROR_WALL_TOP', tf.mirror_wall_top(), prefer=(5,))
    T('MIRROR_WALL', tf.mirror_wall(), prefer=(5,))
    T('MIRROR_MAT', tf.mirror_mat(), prefer=(2,))
    # the Dust Library
    T('LIB_FLOOR', tf.lib_floor_img(0), prefer=(4,))
    T('LIB_SHELF_TOP', tf.lib_shelf_top(), prefer=(4,))
    T('LIB_SHELF', tf.lib_shelf(), prefer=(4,))
    ld_b, ld_t = tf.lib_dust_layers()
    T('LIB_DUST', ld_b, prefer=(4,), top=ld_t)
    T('LIB_MAT', tf.lib_mat(), prefer=(4,))

    gf.add_stamps(ts, out, fb.dream_stamps(gf))
    pq = tf.moon_path_quads()
    out['path_q'] = [[ts.add(gf.img_pix(pq[c][v]), (0,), 'path[%d][%d]' % (c, v))
                      for v in range(5)] for c in range(4)]

    grass = tf.moongrass_img(0)
    grassy = ['GRASS', 'GRASS2', 'GRASS3', 'MOONPETAL']
    gf.add_blend(ts, out, ['STONE', 'STONE2'], tf.moonstone_img(0), grass, grassy, width=2.5, seed=1.4)
    gf.add_blend(ts, out, ['MOONFLOWER'], tf.moonflower_img(), grass, grassy, width=2.5, seed=2.8)

    S = gf.A_SOLID
    attrs = {'MOONPETAL': gf.A_GRASS, 'LIB_DUST': gf.A_GRASS, 'CLIFF': S, 'CLIFF_FACE': S,
             'LEDGE': gf.A_LEDGE, 'LEDGE_L': gf.A_LEDGE, 'LEDGE_R': gf.A_LEDGE,
             'MIRROR_WALL_TOP': S, 'MIRROR_WALL': S, 'MIRROR_MAT': gf.A_EXIT,
             'LIB_SHELF_TOP': S, 'LIB_SHELF': S, 'LIB_MAT': gf.A_EXIT}
    legend = {
        '.': [('GRASS3', 1), ('GRASS2', 4), ('GRASS', 11)],
        ',': 'MOONPETAL', 'f': 'MOONFLOWER', '#': [('STONE2', 3), ('STONE', 13)],
        '=': 'PATH', '~': 'WATER',
        'C': 'CLIFF', 'c': 'CLIFF_FACE', 'L': 'LEDGE', '[': 'LEDGE_L', ']': 'LEDGE_R',
        'T': 'BLOSSOM_TOP', 't': 'BLOSSOM_BOTTOM',
        '+': 'MIRROR_FLOOR', '*': 'MIRROR_STAR', 'M': 'MIRROR_WALL_TOP', 'm': 'MIRROR_WALL',
        'X': 'MIRROR_MAT',
        '_': 'LIB_FLOOR', 'B': 'LIB_SHELF_TOP', 'b': 'LIB_SHELF', ';': 'LIB_DUST', 'x': 'LIB_MAT',
    }
    return gf.finish_tileset(
        out, name, 'DR', attrs=attrs,
        ground=['GRASS', 'GRASS2', 'GRASS3', 'STONE', 'STONE2', 'MOONFLOWER', 'MIRROR_FLOOR',
                'LIB_FLOOR'],
        overlay=['BLOSSOM_TOP', 'BLOSSOM_BOTTOM'],
        legend=legend, oob='BLOSSOM_TOP', default_ground='GRASS', backdrop='ground',
        doors=fb.DREAM_DOORS)
