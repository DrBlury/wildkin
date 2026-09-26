"""The 'volcanic' tileset (owner: W-FAR): CINDER ROAD, CINDERMOOR, the EMBER
TUNNEL, CALDERA HEART and the ANVIL HALL.

Banks
  0 ground   ash, basalt, ember brush, sulfur, cave floor, ledges, paths
  1 lava     animated lava pieces + the hot spring (the tileset's WATER)
  2 rock     crags, charred trees, rails, obsidian
  3 props    the shared village prop bank (signposts, barrels, crates...)
  4 decor    far decor: steam, iron, rust, fire, obsidian (tools/decor_far.py)
  5 iron     iron roofs, brick walls, the Anvil Hall's plates and walls
  6 rust     rust-red roofs over the same walls
  7 walls    windows, doors, wood and glass on brick

The map legend is documented at the top of src/game/world/far/data.h.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import terrain_far as tf  # noqa: E402
import far_buildings as fb  # noqa: E402

USES_DECOR = ['SIGNPOST', 'BARREL', 'CRATE', 'CRATE_STACK', 'SACKS', 'CAMPFIRE', 'LANTERN_POST',
              'WOODPILE', 'BENCH', 'WATER_TROUGH', 'FENCE', 'FENCE_END']

GROUND = ['va_hi', 'va_lt', 'va_base', 'va_mid', 'va_dk',
          'vb_hi', 'vb_lt', 'vb_base', 'vb_dk', 'vb_out', 'eb_hi', 'eb_lt', 'eb_base', 'eb_dk', 'su_y']
LAVA = ['vb_lt', 'vb_base', 'vb_dk', 'vb_out', 'lv_w', 'lv_y', 'lv_o', 'lv_r', 'lv_dr',
        'hs_hi', 'hs_lt', 'hs_base', 'hs_dk', 'va_hi', 'va_lt']
ROCK = ['vb_hi', 'vb_lt', 'vb_base', 'vb_dk', 'b_out', 'va_lt', 'va_base', 'va_mid', 'va_dk',
        'ob_hi', 'ob_base', 'ob_dk', 'cw_lt', 'cw_base', 'cw_dk']
DECOR = ['b_out', 'white', 'st_lt', 'st_mid', 'st_dk', 'ru_hi', 'ru_base', 'ru_dk',
         'lv_y', 'lv_o', 'lv_r', 'ob_hi', 'ob_base', 'su_y', 'ir_dk']
IRON = ['va_base', 'va_dk', 'b_out', 'ir_hi', 'ir_lt', 'ir_base', 'ir_dk', 'ir_dkr',
        'bk_hi', 'bk_base', 'bk_dk', 'st_hi', 'st_lt', 'st_mid', 'gl_dk']
RUST = ['va_base', 'va_dk', 'b_out', 'rr_hi', 'rr_lt', 'rr_base', 'rr_dk', 'rr_dkr',
        'bk_hi', 'bk_base', 'bk_dk', 'st_hi', 'st_lt', 'st_mid', 'gl_dk']
WALLS = ['va_base', 'va_dk', 'b_out', 'bk_hi', 'bk_base', 'bk_dk', 'st_hi', 'st_lt', 'st_mid',
         'wd_lt', 'wd_base', 'wd_dk', 'gl_hi', 'gl_base', 'gl_dk']

TERRAIN_DOC = {
    'ASH': 'soft volcanic ash (+ ASH2, ASH3 variants)',
    'BASALT': 'columnar basalt seen from above: hexagonal column tops (+ BASALT2)',
    'SETTS': 'dressed hexagonal basalt street paving (Cindermoor)',
    'SULFUR': 'ash crusted with yellow sulfur',
    'EMBERBRUSH': 'scorched brush with glowing seed heads; wild kin roam here (top = front blades)',
    'CLIFF': 'basalt column cliff with an ash lip (solid); tiles horizontally',
    'CLIFF_FACE': 'plain basalt columns; stack under CLIFF (solid)',
    'CRAG_TOP': '16x32 basalt spire (map borders): TOP above BOTTOM; overlay',
    'DEADTREE_TOP': '16x32 charred tree: TOP above BOTTOM; overlay',
    'LEDGE': 'one-way ash ledge: walk DOWN onto it to hop (+ _L/_R ends)',
    'RAIL_H': 'mine-cart rails on cinder ballast, running east-west (walkable)',
    'RAIL_V': 'mine-cart rails running north-south (walkable)',
    'CAVE_FLOOR': 'Ember Tunnel grit floor (+ CAVE_FLOOR2)',
    'CAVE_WALL': 'rock mass above a cave wall (solid)',
    'CAVE_FACE': 'cave wall face down to the floor, lava-lit foot (solid)',
    'CAVE_EXIT': 'exit mat of a cave (walk DOWN to leave)',
    'EMBERMOSS': 'glowing ember moss on the cave floor; wild kin roam here',
    'HALL_FLOOR': 'riveted iron deck plates (Anvil Hall) (+ HALL_VENT grate)',
    'HALL_WALL_TOP': 'upper brick hall wall (solid)',
    'HALL_WALL': 'lower hall wall: brick over an iron rail (solid)',
    'HALL_MAT': 'Anvil Hall exit mat',
    'LAVA': 'animated lava (solid): LAVA_N/S/W/E edges, _NW/_NE/_SW/_SE outer corners, '
            '_INW/_INE/_ISW/_ISE inner corners, _H/_V one-cell streams, _POOL a single cell',
}


def build(gf, name):
    gf.register_colors(tf.FAR_COLORS)
    banks = [GROUND, LAVA, ROCK, list(gf.decor_outdoor.TOWN_DECOR_BANK), DECOR, IRON, RUST, WALLS]
    gf.check_banks(name, banks)
    ts = gf.TileSet(name, banks)
    out = {'ts': ts, 'meta_b': [], 'meta_t': [], 'terrain': [], 'docs': TERRAIN_DOC}

    # animated blocks first (each one contiguous)
    lava_q = fb.add_quads_anim(gf, ts, out, tf.lava_quads, 4, 1, period=14)
    water_q = fb.add_quads_anim(gf, ts, out, tf.spring_quads, 3, 1, period=22)
    out['water_q'] = water_q

    def T(nm, img, prefer=(0,), top=None):
        out['terrain'].append(nm)
        out['meta_b'].append(ts.meta(img, prefer=prefer, where='%s.%s' % (name, nm)))
        out['meta_t'].append(ts.meta(top, prefer=prefer, where='%s.%s.top' % (name, nm), opaque=False)
                             if top else [0, 0, 0, 0])

    def O(nm, img, top_layer):
        out['terrain'].append(nm)
        gf.add_overlay_terrain(ts, out, nm, img, top=top_layer)

    T('ASH', tf.ash_img(0))
    T('ASH2', tf.ash_img(1))
    T('ASH3', tf.ash_img(2))
    T('BASALT', tf.basalt_img(0))
    T('BASALT2', tf.basalt_img(1))
    T('SETTS', tf.setts_img())
    T('SULFUR', tf.sulfur_img())
    eb_b, eb_t = tf.emberbrush_layers()
    T('EMBERBRUSH', eb_b, top=eb_t)
    T('CLIFF', tf.column_face(0, lip='ash'))
    T('CLIFF_FACE', tf.column_face(0))
    T('LEDGE', tf.ledge_img_ash())
    T('LEDGE_L', tf.ledge_img_ash('L'))
    T('LEDGE_R', tf.ledge_img_ash('R'))
    T('RAIL_H', tf.rail_img(False), prefer=(2,))
    T('RAIL_V', tf.rail_img(True), prefer=(2,))
    crag = tf.crag_img()
    O('CRAG_TOP', crag.crop(0, 0, 16, 16), True)
    O('CRAG_BOTTOM', crag.crop(0, 16, 16, 16), False)
    dead = tf.dead_tree_img()
    O('DEADTREE_TOP', dead.crop(0, 0, 16, 16), True)
    O('DEADTREE_BOTTOM', dead.crop(0, 16, 16, 16), False)
    # the Ember Tunnel
    T('CAVE_FLOOR', tf.cave_floor_img(0))
    T('CAVE_FLOOR2', tf.cave_floor_img(1))
    T('CAVE_WALL', tf.cave_wall_top())
    T('CAVE_FACE', tf.cave_wall_face())
    T('CAVE_EXIT', tf.cave_exit_img())
    em_b, em_t = tf.embermoss_layers()
    T('EMBERMOSS', em_b, top=em_t)
    # the Anvil Hall
    T('HALL_FLOOR', tf.hall_floor_img(), prefer=(5,))
    T('HALL_VENT', tf.hall_floor_img(vent=True), prefer=(5,))
    T('HALL_WALL_TOP', tf.hall_wall_top(), prefer=(5,))
    T('HALL_WALL', tf.hall_wall(), prefer=(5,))
    T('HALL_MAT', tf.hall_mat(), prefer=(5,))
    # lava pieces (animated tiles)
    for nm, rows in tf.LAVA_PIECES.items():
        vs = tf.piece_variants(rows)
        out['terrain'].append(nm)
        out['meta_b'].append([lava_q[c][vs[c]] for c in range(4)])
        out['meta_t'].append([0, 0, 0, 0])

    # buildings
    gf.add_stamps(ts, out, fb.volcanic_stamps(gf))
    # cinder paths (autotiled '=')
    pq = tf.cinder_path_quads()
    out['path_q'] = [[ts.add(gf.img_pix(pq[c][v]), (0,), 'path[%d][%d]' % (c, v))
                      for v in range(5)] for c in range(4)]

    lava_names = list(tf.LAVA_PIECES)
    attrs = {n: gf.A_SOLID for n in lava_names}
    attrs.update({'EMBERBRUSH': gf.A_GRASS, 'EMBERMOSS': gf.A_GRASS, 'CLIFF': gf.A_SOLID,
                  'CLIFF_FACE': gf.A_SOLID, 'LEDGE': gf.A_LEDGE, 'LEDGE_L': gf.A_LEDGE,
                  'LEDGE_R': gf.A_LEDGE, 'CAVE_WALL': gf.A_SOLID, 'CAVE_FACE': gf.A_SOLID,
                  'CAVE_EXIT': gf.A_EXIT, 'HALL_WALL_TOP': gf.A_SOLID, 'HALL_WALL': gf.A_SOLID,
                  'HALL_MAT': gf.A_EXIT})
    legend = {
        '.': [('ASH3', 1), ('ASH2', 4), ('ASH', 11)],
        ',': 'EMBERBRUSH', ':': [('BASALT2', 4), ('BASALT', 12)], '#': 'SETTS',
        'y': 'SULFUR', '=': 'PATH', '~': 'WATER',
        'C': 'CLIFF', 'c': 'CLIFF_FACE', 'L': 'LEDGE', '[': 'LEDGE_L', ']': 'LEDGE_R',
        'T': 'CRAG_TOP', 't': 'CRAG_BOTTOM', 'D': 'DEADTREE_TOP', 'd': 'DEADTREE_BOTTOM',
        'r': 'RAIL_H', 'j': 'RAIL_V',
        '_': [('CAVE_FLOOR2', 5), ('CAVE_FLOOR', 11)], 'M': 'CAVE_WALL', 'm': 'CAVE_FACE',
        'x': 'CAVE_EXIT', ';': 'EMBERMOSS',
        '+': 'HALL_FLOOR', 'v': 'HALL_VENT', 'H': 'HALL_WALL_TOP', 'h': 'HALL_WALL', 'X': 'HALL_MAT',
        # lava: a numpad around the melt, then the inner corners and streams
        '5': 'LAVA', '8': 'LAVA_N', '2': 'LAVA_S', '4': 'LAVA_W', '6': 'LAVA_E',
        '7': 'LAVA_NW', '9': 'LAVA_NE', '1': 'LAVA_SW', '3': 'LAVA_SE',
        'q': 'LAVA_INW', 'p': 'LAVA_INE', 'b': 'LAVA_ISW', 'n': 'LAVA_ISE',
        '-': 'LAVA_H', '|': 'LAVA_V', 'o': 'LAVA_POOL',
    }
    return gf.finish_tileset(
        out, name, 'VO', attrs=attrs,
        ground=['ASH', 'ASH2', 'ASH3', 'BASALT', 'BASALT2', 'SETTS', 'SULFUR', 'CAVE_FLOOR',
                'CAVE_FLOOR2', 'HALL_FLOOR'],
        overlay=['CRAG_TOP', 'CRAG_BOTTOM', 'DEADTREE_TOP', 'DEADTREE_BOTTOM'],
        legend=legend, oob='CRAG_TOP', default_ground='ASH', backdrop='ground',
        doors=fb.VOLCANIC_DOORS)
