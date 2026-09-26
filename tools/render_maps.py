#!/usr/bin/env python3
"""Render maps to PNG exactly the way the game draws them (make maps).

Builds tools/render_maps.c (the host build of the game plus a PNG writer)
and runs it:

    python3 tools/render_maps.py OUTDIR [--scale N] [--levels] [NAME_OR_ID ...]

With no names every map is written to OUTDIR/<map_name>.png; names select
maps whose file name contains them (e.g. maple_village). --levels prints
each cell's elevation over the picture (docs/ELEVATION.md).
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    outdir = argv[0] if argv else os.path.join(ROOT, 'build', 'maps')
    os.makedirs(outdir, exist_ok=True)
    exe = os.path.join(ROOT, 'build', 'render_maps')
    os.makedirs(os.path.dirname(exe), exist_ok=True)
    cc = os.environ.get('HOSTCC', 'cc')
    subprocess.check_call([cc, '-std=c11', '-O2', '-Wall', '-Wextra', '-Wno-missing-field-initializers',
                           '-Wno-unused-function', '-o', exe,
                           os.path.join(ROOT, 'tools', 'render_maps.c'), '-lz'])
    subprocess.check_call([exe, outdir] + list(argv[1:]))


if __name__ == '__main__':
    main(sys.argv[1:])
