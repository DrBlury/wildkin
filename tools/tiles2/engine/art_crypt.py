"""CRYPT (barrows, ossuaries, vaults, the Bone Throne) drawn from tiles2 `crypt`."""

from core import Img
import terrain as T
import props as PR
import interiorart as IN
import dungeonart as DG
import sets.crypt as S

from .load import kit, over
from . import common as CM
from .art_town import kin_statue

SET = 'crypt'


def block(k, ramp, out):
    img = Img(16, 16)
    img.rect(1, 1, 14, 14, k.role(ramp[1]))
    img.rect(1, 1, 14, 4, k.role(ramp[3]))
    img.hline(1, 14, 1, k.role(ramp[4]))
    img.vline(14, 5, 14, k.role(ramp[0]))
    img.hline(2, 13, 9, k.role(ramp[0]))
    img.vline(7, 5, 9, k.role(ramp[0]))
    return img.outline(k.role(out))


def plaque(k):
    img = Img(16, 16)
    img.rect(3, 4, 12, 11, k.role('cs3'))
    img.hline(3, 12, 4, k.role('cs4'))
    for x in range(5, 11, 2):
        img.set(x, 7, k.role('au1'))
        img.set(x, 9, k.role('au1'))
    return img.outline(k.role('cs0'))


def art(ctx):
    k = kit(SET)
    floor = k.cells('floor')
    face1 = k.img('cliff_face_single')
    wall = CM.cell_of(face1, 1, 0)
    carpet = k.img('carpet')
    col = k.paint(PR.standing_stone(S.STONE, 'cs0', seed=3))
    terrain = {
        'VOID': Img(16, 16, k.role('v0')), 'WALL_TOP': k.cells('wall_top'), 'WALL': wall,
        'NICHE': ('fit', over(wall, k.img('skull_niche'))), 'BONE_WALL': ('fit', over(wall, k.img('bone_pile'))),
        'WISP_WALL': ('fit', over(wall, k.img('wisp'))),
        'FLOOR': floor, 'FLOOR2': k.cells('floor_cracked'),
        'BLOCK': ('fit', over(floor, block(k, S.STONE, 'cs0'))),
        'FAKE_BLOCK': ('fit', over(floor, block(k, S.STONE, 'cs0'))),
        'GHOST_FLOOR': floor,   # the puzzle: it must look like the floor (test_grim)
        'DOORMAT': ('fit', over(floor, k.paint(IN.door_mat(['rd0', 'rd1', 'rd2'], 'cf0')))),
        'CARPET': CM.cell_of(carpet, 1, 2),
        'STAIRS_UP': ('fit', over(floor, CM.cell_of(k.img('stairs'), 0, 1))),
        'STAIRS_DOWN': ('fit', over(floor, k.paint(IN.stairs_in(['cf1', 'cf3', 'cf4'], 'cs0', down=True)).crop(0, 16, 16, 16))),
        'ARCH': CM.mouth(wall, k.role('v0'), k.role('cs0')),
        'PILLAR_TOP': ('fit', over(k.cells('wall_top'), col.crop(0, 0, 16, 16))),
        'PILLAR': ('fit', over(floor, col.crop(0, 16, 16, 16))),
        'BONEDUST': k.cells('floor_bones'),
    }
    decor = CM.decor_table(k, ctx.decor, {
        'CR_SKULLS': 'skulls', 'CR_CANDLES': 'candles',
        'CR_SARCOPHAGUS': k.paint(DG.sarcophagus(S.STONE, 'cs0', trim='au1', w=16, h=32)),
        'CR_COFFIN': 'coffin', 'CR_BRAZIER': 'brazier', 'CR_URN': 'urn',
        'CR_STATUE': kin_statue(k, ('cs0', 'cs1', 'cs2', 'cs3', 'cs4')), 'CR_BANNER': 'banner',
        'CR_CHAINS': k.paint(DG.chains(['cs1', 'cs2', 'cs4'], 'cs0', w=16, h=16)),
        'CR_THRONE': k.paint(DG.throne(S.STONE, ['rd0', 'rd1', 'rd2'], ['au0', 'au1', 'au2'], 'cs0', w=48, h=48)),
        'CR_PEDESTAL': 'pedestal@0,1', 'CR_PLAQUE': plaque(k),
    })
    return {'set': SET, 'terrain': terrain, 'stamps': {}, 'decor': decor,
            'legend': {'.': [('FLOOR2', 3), ('FLOOR', 13)]}}
