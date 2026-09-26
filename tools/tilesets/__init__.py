"""Tileset modules for tools/gen_field_gfx.py.

The registry order is pixelart.SETS (it fixes the TS_* ids). town, wild and
interior are built inside gen_field_gfx.py; every other tileset lives in
ts_<name>.py here and exposes

    build(gf, name) -> tileset dict (see gen_field_gfx.finish_tileset)

gf is the gen_field_gfx module (TileSet, helpers, colours, A_* bits). A
module may also define USES_DECOR = ['SIGNPOST', ...]: existing decor kinds
that should also be encoded for this tileset (their colours must fit the
tileset's banks). New decor for a tileset goes in its own decor module
registered in gen_field_gfx.all_decor().
"""
