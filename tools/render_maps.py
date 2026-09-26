#!/usr/bin/env python3
"""Render every map to OUTDIR/<id>_<name>.png the way the game draws it
(make maps). The work is done by tools/render_maps.c, a host build of the
whole game: each map and its tileset are loaded and the field renderer's
own layers are decoded, so the pictures match the GBA exactly (first
animation frame, people standing, no wild kin).

    python3 tools/render_maps.py OUTDIR [--scale 2]
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    outdir = argv[0] if argv and not argv[0].startswith('--') else os.path.join('build', 'maps')
    scale = argv[argv.index('--scale') + 1] if '--scale' in argv else '1'
    os.makedirs(outdir, exist_ok=True)
    exe = os.path.join(ROOT, 'build', 'render_maps')
    os.makedirs(os.path.dirname(exe), exist_ok=True)
    subprocess.check_call([os.environ.get('HOSTCC', 'cc'), '-std=c11', '-O1', '-Wno-unused-function', '-o', exe,
                           os.path.join(ROOT, 'tools', 'render_maps.c'), '-lz'])
    subprocess.check_call([exe, outdir, scale])


if __name__ == '__main__':
    main(sys.argv[1:])
