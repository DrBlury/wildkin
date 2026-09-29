"""Shared colour ramps (hex) for the second-generation sets.

Ramps run dark -> light and are hue-shifted: shadows lean cool/blue,
highlights lean warm/yellow. Values are authored at 8 bits and quantised to
the GBA's 5 bits per channel when a sheet is written.
"""

MEADOW = {
    'g0': '#183c30', 'g1': '#2c6838', 'g2': '#4a9444', 'g3': '#6cb454', 'g4': '#94d068', 'g5': '#c4e890',
}
DIRT = {
    'd0': '#4c3024', 'd1': '#7c5234', 'd2': '#a8784c', 'd3': '#cca068', 'd4': '#e4c088', 'd5': '#f4dcac',
}
FRESH_WATER = {
    'w0': '#203c7c', 'w1': '#3060b0', 'w2': '#4884d8', 'w3': '#70acf0', 'w4': '#a8d4f8', 'w5': '#e8f8ff',
}
CLIFF_BROWN = {
    'r0': '#3a2426', 'r1': '#62392e', 'r2': '#8a5838', 'r3': '#b27c4c', 'r4': '#d2a266', 'r5': '#eac68c',
}
STONE_GREY = {
    's0': '#26283a', 's1': '#474c5c', 's2': '#686f7e', 's3': '#8e96a0', 's4': '#b6bcc0', 's5': '#dcdedc',
}
LEAF = {
    't0': '#123028', 't1': '#1c4c34', 't2': '#28683c', 't3': '#3c8a44', 't4': '#5eac4c', 't5': '#8ccc60',
}
PINE = {
    'p0': '#0e2a2c', 'p1': '#16443c', 'p2': '#205e48', 'p3': '#2e7c52', 'p4': '#48a060',
}
BARK = {
    'k0': '#2c1a1c', 'k1': '#553428', 'k2': '#7e5236', 'k3': '#a8764a', 'k4': '#c89a64',
}
FLOWERS = {
    'fr': '#e04040', 'frd': '#a02840', 'fy': '#f8d030', 'fyd': '#c89020', 'fw': '#f8f8f0',
    'fp': '#f088b0', 'fpd': '#b85080', 'fb': '#6c8cf0', 'fbd': '#4058b0', 'fo': '#f09040',
}
# buildings
ROOF_RED = {'ra0': '#5c1a28', 'ra1': '#8c2a34', 'ra2': '#bc443e', 'ra3': '#e06a4c', 'ra4': '#f49a6c'}
ROOF_BLUE = {'rb0': '#1a2654', 'rb1': '#28407c', 'rb2': '#3a5eac', 'rb3': '#5a86d0', 'rb4': '#8cb4ec'}
ROOF_GREEN = {'rg0': '#143c3c', 'rg1': '#1f5c50', 'rg2': '#2e7c60', 'rg3': '#4ca070', 'rg4': '#80c88c'}
WALL_CREAM = {'wl0': '#b49c7c', 'wl1': '#e8d8b4', 'wl2': '#fcf4dc'}
GLASS = {'gl0': '#2c4474', 'gl1': '#6494cc', 'gl2': '#dcf0ff'}
COBBLE = {'c0': '#5a5048', 'c1': '#8a8078', 'c2': '#aca098', 'c3': '#cac0b4', 'c4': '#e8e0d4'}
BRICK = {'bk0': '#6a2c2c', 'bk1': '#a44a3c', 'bk2': '#c87058'}
OUTLINE = {'o': '#2a1c24'}


def merge(*ds):
    out = {}
    for d in ds:
        for k, v in d.items():
            if k in out and out[k] != v:
                raise ValueError('palette role %s defined twice' % k)
            out[k] = v
    return out


def ramp(prefix, n, start=0):
    return ['%s%d' % (prefix, i) for i in range(start, start + n)]
