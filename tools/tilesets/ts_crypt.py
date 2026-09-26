"""The 'crypt' tileset.

PLACEHOLDER: a copy of the interior tileset until its owner (see
docs/EXPANSION.md, section 9) draws the real one. Keep the legend
characters documented at the top of the region's maps.
"""

USES_DECOR = []


def build(gf, name):
    return gf.build_interior(name)
