#!/usr/bin/env python3
"""Render every map in src/game/maps.h to a PNG, the way the game draws it.

Terrain, autotiled paths and water, building stamps, decor (mid and top
layers), people and wild-kin-free tall grass are all decoded from the same
generated tiles the game uses, so the pictures match the GBA exactly.

    python3 tools/render_maps.py OUTDIR [--maps src/game/maps.h] [--scale 2]
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_field_gfx as gf  # noqa: E402
from pixelart import Canvas  # noqa: E402

TOWN_KEY = {'.': 'GRASS', ',': 'TALLGRASS', 'r': 'FLOWER_RED', 'y': 'FLOWER_YELLOW',
            '=': 'PATH', '~': 'WATER', '#': 'STONE', 'T': 'TREE_TOP', 't': 'TREE_BOTTOM',
            'c': 'COURT', 'h': 'COURT_LINE_H', 'v': 'COURT_LINE_V'}
WILD_KEY = {'.': 'GRASS', ',': 'TALLGRASS', 'r': 'FLOWER_RED', 'y': 'FLOWER_YELLOW',
            '=': 'PATH', '~': 'WATER', '#': 'STONE', 'T': 'TREE_TOP', 't': 'TREE_BOTTOM',
            'P': 'PINE_TOP', 'p': 'PINE_BOTTOM', 'L': 'LEDGE', 's': 'SAND', 'f': 'FOREST',
            'R': 'REEDS', '[': 'LEDGE_L', ']': 'LEDGE_R', 'C': 'CLIFF', 'c': 'CLIFF_FACE', 'd': 'DIRT',
            'm': 'MEADOW'}
INT_KEY = {'W': 'WALL_TOP', 'w': 'WALL', 'n': 'WINDOW', 'k': 'WALL_CLOCK', 'p': 'PAINTING',
           '.': 'FLOOR', ':': 'FLOOR2', 'D': 'DOORMAT', '<': 'COUNTER_L', '=': 'COUNTER',
           '>': 'COUNTER_R'}
SET_OF_TS = {'TS_TOWN': 'town', 'TS_WILD': 'wild', 'TS_INTERIOR': 'interior'}
FACING = {'DOWN': 0, 'UP': 3, 'LEFT': 6, 'RIGHT': 6}


def cell_hash(x, y):
    """Same hash as field.c (32-bit unsigned arithmetic)."""
    m = 0xFFFFFFFF
    h = ((x * 73856093) & m) ^ ((y * 19349663) & m)
    h ^= h >> 13
    h = (h * 0x5bd1e995) & m
    h ^= h >> 15
    return h


def parse(path):
    src = open(path).read()
    rows = {}
    for m in re.finditer(r'static const char \*const (\w+)\[\] = \{(.*?)\};', src, re.S):
        rows[m.group(1)] = re.findall(r'"([^"]*)"', m.group(2))
    stamps = {}
    for m in re.finditer(r'static const Stamp (\w+)\[\] = \{(.*?)\};', src, re.S):
        stamps[m.group(1)] = [(t, n, int(x), int(y)) for (t, n, x, y) in
                              re.findall(r'STAMP\((\w), (\w+), (\d+), (\d+)\)', m.group(2))]
    decor = {}
    for m in re.finditer(r'static const DecorPlace (\w+)\[\] = \{(.*?)\};', src, re.S):
        decor[m.group(1)] = [(n, int(x), int(y), f == 'DPF') for (f, n, x, y) in
                             re.findall(r'(DPF?)\((\w+), (\d+), (\d+)\)', m.group(2))]
    maps = {}
    for m in re.finditer(r'\[(MAP_\w+)\]\s*=\s*\{\s*(\d+),\s*NROWS\((\w+)\),\s*(TS_\w+),\s*\w+,\s*\w+,\s*'
                         r'(\w+),\s*[^,]+,\s*(\w+),\s*[^,]+,\s*"([^"]*)"', src):
        mid, w, rname, ts, st, dec, name = m.groups()
        maps[mid] = dict(w=int(w), rows=rows[rname], ts=SET_OF_TS[ts],
                         stamps=stamps.get(st, []), decor=decor.get(dec, []), name=name)
    people = []
    for m in re.finditer(r'(PERSON|PERSON_KIN|WARDEN)\((MAP_\w+), (\d+), (\d+), (\w+), (\w+)', src):
        kind, mp, x, y, chr_, face = m.groups()
        people.append((mp, int(x), int(y), chr_, face))
    return maps, people


def render(maps, people, sets, dec, chars, outdir, scale):
    char_names = [c['name'] for c in gf.CHARACTERS]
    os.makedirs(outdir, exist_ok=True)
    for mid, mp in maps.items():
        s = mp['ts']
        tsout = sets[s]
        ts = tsout['ts']
        pals = ts.pal15()
        key = {'town': TOWN_KEY, 'wild': WILD_KEY, 'interior': INT_KEY}[s]
        grid = [list(r) for r in mp['rows']]
        H, W = len(grid), mp['w']
        ids = {n: i for i, n in enumerate(tsout['terrain'])}
        stamp_ids = {n: (sid, cw, chh) for (n, sid, cw, chh, doc) in tsout['stamps']}
        tiles = list(ts.tiles)
        bases = {}
        for (n, x, y, fl) in mp['decor']:
            if n in bases:
                continue
            dd = dec['defs'][(s, n)]
            words = dec['words'][dd['tile_first'] * 8:(dd['tile_first'] + dd['tile_count']) * 8]
            bases[n] = len(tiles)
            for t in range(dd['tile_count']):
                w8 = words[t * 8:t * 8 + 8]
                tiles.append(tuple((w8[yy] >> (4 * xx)) & 15 for yy in range(8) for xx in range(8)))
        # stamp cells (door cells count as path for autotiles)
        cells = [[None] * W for _ in range(H)]
        doors = set()
        for (t, n, sx, sy) in mp['stamps']:
            sid, cw, chh = stamp_ids[n]
            for yy in range(chh):
                for xx in range(cw):
                    cells[sy + yy][sx + xx] = sid + yy * cw + xx
            if n not in ('COURT_CIRCLE', 'RUG'):
                doors.add((sx + (3 if n == 'LAB' else 2), sy + chh - 1))

        def same(ch):
            def f(x, y):
                if not (0 <= y < H and 0 <= x < W):
                    return True
                if cells[y][x] is not None:
                    return ch == '=' and (x, y) in doors
                return grid[y][x] == ch
            return f
        cv = Canvas(W * 16, H * 16)
        tops = []
        for y in range(H):
            for x in range(W):
                if cells[y][x] is not None:
                    cv.meta(tiles, pals, tsout['meta_b'][cells[y][x]], x * 16, y * 16)
                    continue
                ch = grid[y][x]
                k = key.get(ch)
                if k is None:
                    k = 'VOID' if s == 'interior' else 'GRASS'
                if k in ('PATH', 'WATER'):
                    q = tsout['path_q'] if k == 'PATH' else tsout['water_q']
                    vs = gf.autotile_variants(same(ch), x, y)
                    for c in range(4):
                        cv.entry(tiles, pals, q[c][vs[c]], x * 16 + 8 * (c & 1), y * 16 + 8 * (c >> 1), False)
                    continue
                if k == 'GRASS' and s != 'interior':
                    h = cell_hash(x, y) % 16
                    k = 'GRASS3' if h == 0 else 'GRASS2' if h < 5 else 'GRASS'
                if k == 'FOREST' and not (cell_hash(x, y) & 3):
                    k = 'FOREST2'
                if k == 'SAND' and s == 'wild' and cell_hash(x, y) % 8 == 0:
                    k = 'SAND2'
                cv.meta(tiles, pals, tsout['meta_b'][ids[k]], x * 16, y * 16)
                if tsout['meta_t'][ids[k]] != [0, 0, 0, 0]:
                    tops.append((tsout['meta_t'][ids[k]], x * 16, y * 16))
        for (n, dx, dy, fl) in mp['decor']:
            dd = dec['defs'][(s, n)]
            for kk in range(dd['w'] * dd['h']):
                cx, cy = kk % dd['w'], kk // dd['w']
                src_i = cy * dd['w'] + (dd['w'] - 1 - cx if fl else cx)
                ents = [gf.decor_entry_abs(e, bases[n]) for e in dec['meta'][dd['meta_first'] + src_i]]
                if fl:
                    ents = [ents[1] ^ 1024 if ents[1] else 0, ents[0] ^ 1024 if ents[0] else 0,
                            ents[3] ^ 1024 if ents[3] else 0, ents[2] ^ 1024 if ents[2] else 0]
                if dd['top'] & (1 << src_i):
                    tops.append((ents, (dx + cx) * 16, (dy + cy) * 16))
                else:
                    cv.meta(tiles, pals, ents, (dx + cx) * 16, (dy + cy) * 16, transparent=True)
        for (pm, x, y, chr_, face) in sorted([p for p in people if p[0] == mid], key=lambda p: p[2]):
            ci = char_names.index(chr_)
            frames, pal = chars[ci]
            cv.sprite(frames[FACING[face]], pal, x * 16, y * 16 - 16, 2, 4, hflip=face == 'RIGHT')
        for (ents, px, py) in tops:
            cv.meta(tiles, pals, ents, px, py, transparent=True)
        out = os.path.join(outdir, '%s.png' % mid.lower())
        cv.save(out, scale)
        print('wrote', out)


def main(argv):
    outdir = argv[0] if argv else 'build/maps'
    path = os.path.join(gf.ROOT, 'src', 'game', 'maps.h')
    scale = 1
    if '--maps' in argv:
        path = argv[argv.index('--maps') + 1]
    if '--scale' in argv:
        scale = int(argv[argv.index('--scale') + 1])
    for extra in (gf.decor_outdoor.OUTDOOR_COLORS, gf.decor_indoor.INDOOR_COLORS):
        gf.C.update(extra)
    sets = {'town': gf.build_town(), 'wild': gf.build_wild(), 'interior': gf.build_interior()}
    dec = gf.build_decor(sets)
    chars = [gf.char_gfx(c) for c in gf.CHARACTERS]
    maps, people = parse(path)
    render(maps, people, sets, dec, chars, outdir, scale)


if __name__ == '__main__':
    main(sys.argv[1:])
