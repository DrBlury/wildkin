"""DUSK (Gravewood) drawn from tiles2 `dusk` with the grim structure."""

from .load import kit
from .art_grim import gothic


def art(ctx):
    import sets.dusk as S
    k = kit('dusk')
    R = {
        'grass': ('floor', 'floor_b', 'floor_c', 'leaves'), 'grass_dk': 'fl1',
        'soil': ('fl1', 'fl3', 'fl4', 'fl5', 'fl5'), 'mud': ('bg0', 'bg1', 'bg2', 'bg3', 'bg3'),
        'moss': ('fl1', 'bg2', 'bg3', 'bg4', 'bg5'), 'scorch': ('fl0', 'fl1', 'fl2', 'fl3', 'fl3'),
        'glow': ('tc1', 'tc2', 'tc3'), 'stone': S.STONE, 'stone_out': 'gs0', 'wood': ['bk0', 'bk1', 'bk2', 'bk3'],
        'wood_out': 'bk0', 'leaf': S.LEAF, 'leaf_out': 'tv0', 'bark': S.BARK, 'bark_out': 'bk0',
        'cypress': ['tv0', 'tv1', 'tv2', 'tv3', 'tv4'], 'house': S.STYLE, 'flame': ('ln1', 'ln0', 'bk2'),
        'bone': ['gs2', 'gs3', 'gs4'], 'void': 'gs0', 'bell': ['bk1', 'ln0', 'ln1'], 'lamp': 'lantern',
        'pumpkin': 'pumpkin', 'water': 'bog', 'path': 'trail', 'stairs': ('gs4', 'gs3', 'gs1', 'gs0', 'gs2'),
        'backdrop': (29, 25, 52), 'seed': 6,
        'grass_colors': {'grm_straw_hi': 'fl5', 'grm_straw': 'fl4', 'grm_straw_dk': 'fl3', 'grm_ash_dk': 'fl1',
                         'grm_soot': 'fl0', 'grm_ash_md': 'fl2', 'grm_ash_dkr': 'fl0', 'grm_bone': 'fl5',
                         'grm_ash_hi': 'fl5', 'grm_ash_lt': 'fl4', 'grm_rust': 'lf2', 'grm_emb_dk': 'lf1',
                         'grm_reed_hi': 'bg5', 'grm_reed': 'bg4', 'grm_moss_dk': 'bg3', 'grm_mud_dk': 'bg1',
                         'grm_peat': 'bg0', 'grm_mud': 'bg2', 'grm_wisp': 'ws0', 'grm_wisp_hi': 'ws1',
                         'grm_moss_hi': 'bg5'},
    }
    return gothic(ctx, k, R)
