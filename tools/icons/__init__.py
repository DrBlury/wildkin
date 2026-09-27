"""Bag icon registry for tools/gen_battle_gfx.py.

The 17 original icons are drawn in gen_battle_gfx.build_items(). Every owner
adds more in its own module here, icons_<owner>.py, exposing

    def icons(g):  # g = the gen_battle_gfx module (Canvas helpers, ramp, C...)
        return [('NAME', canvas_24x24), ...]

Each becomes ICON_NAME in gfx_battle.h (ids after the core ones, in module
order below, then list order). Items point at icons with Item.icon.
Icons are 24x24 with at most 15 colours, index 1 pure white (the UI draws
white text over the icon slot's frame).
"""

MODULES = ['icons_core', 'icons_farm', 'icons_craft', 'icons_fusion', 'icons_travel', 'icons_ui',
           'icons_kin']


def collect(g):
    import importlib
    out, seen = [], set()
    for m in MODULES:
        try:
            mod = importlib.import_module('icons.' + m)
        except ModuleNotFoundError:
            continue
        for (name, cv) in mod.icons(g):
            if name in seen:
                raise ValueError('icon %s defined twice' % name)
            seen.add(name)
            out.append((name, cv))
    return out
