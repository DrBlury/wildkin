"""TIDE (the Tidal Temple, Current Hall, Drowned Bell) drawn from tiles2 `tide`."""

from core import Img
import terrain as T
import interiorart as IN
import sets.tide as S

from .load import kit, over
from . import common as CM

SET = 'tide'


def art(ctx):
    k = kit(SET)
    floor = k.cells('floor')
    face1 = k.img('cliff_face_single')
    wall = CM.cell_of(face1, 1, 0)
    port = wall.copy()
    for y in range(16):
        for x in range(16):
            d = ((x + 0.5 - 8) ** 2 + (y + 0.5 - 7) ** 2) ** 0.5
            if d < 4.2:
                port.p[y][x] = k.role('tw3') if (x + y) % 5 else k.role('tw5')
            elif d < 5.6:
                port.p[y][x] = k.role('br1') if y < 7 else k.role('br0')
    rocktop = k.paint(T.lump_texture(['ts0', 'ts1', 'ts2', 'ts3'], 16, 16, 7, rx=3.4, ry=2.8, sx=5.3, sy=4.0,
                                     bias=-0.1))
    mat = k.paint(IN.door_mat(['br0', 'br1', 'br2'], 'ts0'))
    pools, deep = k.frames('pool'), k.frames('deep_pool')
    terrain = {
        'HALL_FLOOR': floor, 'HALL_WALL_TOP': k.cells('wall_top'), 'HALL_WALL': wall,
        'HALL_PORTHOLE': ('fit', port), 'HALL_MAT': ('fit', over(floor, mat)),
        'HALL_POOL': ('anim', [CM.cell_of(p, 1, 2) for p in pools], 16),
        'CUR_DOWN': ('anim', k.frames('current_s'), 10), 'CUR_UP': ('anim', k.frames('current_n'), 10),
        'CUR_LEFT': ('anim', k.frames('current_w'), 10), 'CUR_RIGHT': ('anim', k.frames('current_e'), 10),
        'GROT_TOP': rocktop, 'GROT_WALL': CM.cell_of(k.img('cliff_face'), 1, 1),
        'GROT_FLOOR': k.cells('floor_kelp'), 'GROT_GLOW': ('fit', over(k.cells('floor_kelp'), k.img('glow_coral'))),
        'TEMPLE': k.cells('floor_barnacles'),
        'GLOW_POOL': ('anim', [CM.cell_of(p, 1, 2) for p in deep[:3]], 16),
        'GROT_MAT': ('fit', over(k.cells('floor_kelp'), mat)), 'VOID': Img(16, 16, k.role('v0')),
    }
    decor = CM.decor_table(k, ctx.decor, {
        'HALL_COLUMN': 'column@0,1', 'DROWNED_BELL': CM.at_bottom(k.img('drowned_bell'), 3, 3, 8),
        'GROT_PILLAR': 'coral_pillar@0,1', 'WHALE_CARVING': 'whale_carving@0,1',
    })
    return {'set': SET, 'terrain': terrain, 'stamps': {}, 'decor': decor}
