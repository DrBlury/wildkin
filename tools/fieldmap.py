#!/usr/bin/env python3
"""Decode and draw maps exactly the way src/game/field.c does.

Shared by tools/render_maps.py, the asset-viewer generator and the art
previews, so a map rendered on the host matches the GBA pixel for pixel:

  * each character goes through the tileset's legend (variants picked by
    the same cell hash as field.c),
  * '=' paths and '~' water are autotiled per 8x8 quadrant,
  * overlay terrain (trees) gets the ground of its nearest ground
    neighbour drawn underneath (field.c: map_infer_ground),
  * stamps, decor (mid / top layers) and people are layered like BG0, BG2,
    OBJ and BG3.
"""

import gen_field_gfx as gf
from pixelart import Canvas

GROUND_SEARCH = 8  # cells; must match field.c


def cell_hash(x, y):
    """Same hash as field.c (32-bit unsigned arithmetic)."""
    m = 0xFFFFFFFF
    h = ((x * 73856093) & m) ^ ((y * 19349663) & m)
    h ^= h >> 13
    h = (h * 0x5bd1e995) & m
    h ^= h >> 15
    return h


def legend_spec(out, ch):
    spec = out['legend'].get(ch)
    if spec is None:
        spec = out['legend'][out['legend_default']]
    return spec


def pick(out, spec, x, y):
    """Metatile id for a legend entry at (x, y); 'PATH' / 'WATER' pass through."""
    if spec in ('PATH', 'WATER'):
        return spec
    if len(spec) == 1:
        return out['ids'][spec[0][0]]
    h = cell_hash(x, y) % 16
    acc = 0
    for (name, w) in spec:
        acc += w
        if h < acc:
            return out['ids'][name]
    return out['ids'][spec[-1][0]]


def is_ground_spec(out, spec):
    if spec in ('PATH', 'WATER'):
        return False
    return all(out['mflags'][out['ids'][n]] & gf.MF_GROUND for (n, _) in spec)


def infer_ground(out, rows, x, y):
    h, w = len(rows), len(rows[0])
    for d in range(1, GROUND_SEARCH + 1):
        for (nx, ny) in ((x, y + d), (x, y - d), (x - d, y), (x + d, y)):
            if 0 <= nx < w and 0 <= ny < h:
                spec = legend_spec(out, rows[ny][nx])
                if is_ground_spec(out, spec):
                    return pick(out, spec, x, y)
    return out['ground_default']


def decode(out, rows):
    """-> (cells, ground): cells[y][x] is a metatile id or 'PATH' / 'WATER';
    ground[y][x] is the ground under an overlay cell (else None)."""
    h, w = len(rows), len(rows[0])
    cells = [[pick(out, legend_spec(out, rows[y][x]), x, y) for x in range(w)] for y in range(h)]
    ground = [[None] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            v = cells[y][x]
            if not isinstance(v, str) and out['mflags'][v] & gf.MF_OVERLAY:
                ground[y][x] = infer_ground(out, rows, x, y)
    return cells, ground


class Painter:
    """Draws cells, decor and sprites onto a Canvas with the tileset's tiles
    plus the decor kinds used (appended after the tileset, like the game)."""

    def __init__(self, out, dec, sname, w, h):
        self.out, self.dec, self.sname = out, dec, sname
        self.pals = out['ts'].pal15()
        self.tiles = list(out['ts'].tiles)
        self.bases = {}
        self.cv = Canvas(w * 16, h * 16)
        self.tops = []

    def decor_base(self, name):
        if name not in self.bases:
            dd = self.dec['defs'][(self.sname, name)]
            words = self.dec['words'][dd['tile_first'] * 8:(dd['tile_first'] + dd['tile_count']) * 8]
            self.bases[name] = len(self.tiles)
            for t in range(dd['tile_count']):
                w8 = words[t * 8:t * 8 + 8]
                self.tiles.append(tuple((w8[y] >> (4 * x)) & 15 for y in range(8) for x in range(8)))
        return self.bases[name]

    def cells(self, cells, ground):
        out = self.out
        H, W = len(cells), len(cells[0])

        def same(kind):
            def f(x, y):
                if not (0 <= y < H and 0 <= x < W):
                    return True
                v = cells[y][x]
                if v == kind:
                    return True
                return kind == 'PATH' and not isinstance(v, str) and out['attr'][v] & gf.A_DOOR
            return f
        for y in range(H):
            for x in range(W):
                v = cells[y][x]
                if isinstance(v, str):
                    q = out['path_q'] if v == 'PATH' else out['water_q']
                    vs = gf.autotile_variants(same(v), x, y)
                    for c in range(4):
                        self.cv.entry(self.tiles, self.pals, q[c][vs[c]],
                                      x * 16 + 8 * (c & 1), y * 16 + 8 * (c >> 1), False)
                    continue
                if ground[y][x] is not None:
                    self.cv.meta(self.tiles, self.pals, out['meta_b'][ground[y][x]], x * 16, y * 16)
                    self.cv.meta(self.tiles, self.pals, out['meta_b'][v], x * 16, y * 16,
                                 transparent=True)
                else:
                    self.cv.meta(self.tiles, self.pals, out['meta_b'][v], x * 16, y * 16)
                if out['meta_t'][v] != [0, 0, 0, 0]:
                    self.tops.append((out['meta_t'][v], x * 16, y * 16))

    def stamp(self, sid, cw, chh, sx, sy):
        for my in range(chh):
            for mx in range(cw):
                self.cv.meta(self.tiles, self.pals, self.out['meta_b'][sid + my * cw + mx],
                             (sx + mx) * 16, (sy + my) * 16)

    def decor(self, name, dx, dy, flip):
        dd = self.dec['defs'][(self.sname, name)]
        base = self.decor_base(name)
        for k in range(dd['w'] * dd['h']):
            cx, cy = k % dd['w'], k // dd['w']
            src = cy * dd['w'] + (dd['w'] - 1 - cx if flip else cx)
            ents = [gf.decor_entry_abs(e, base) for e in self.dec['meta'][dd['meta_first'] + src]]
            if flip:
                ents = [ents[1] ^ (1 << 10) if ents[1] else 0, ents[0] ^ (1 << 10) if ents[0] else 0,
                        ents[3] ^ (1 << 10) if ents[3] else 0, ents[2] ^ (1 << 10) if ents[2] else 0]
            if dd['top'] & (1 << src):
                self.tops.append((ents, (dx + cx) * 16, (dy + cy) * 16))
            else:
                self.cv.meta(self.tiles, self.pals, ents, (dx + cx) * 16, (dy + cy) * 16,
                             transparent=True)

    def sprite(self, gfx, pal, px, py, tw, th, flip=False):
        self.cv.sprite(gfx, pal, px, py, tw, th, hflip=flip)

    def finish(self):
        for (ents, px, py) in self.tops:
            self.cv.meta(self.tiles, self.pals, ents, px, py, transparent=True)
        self.tops = []
        return self.cv
