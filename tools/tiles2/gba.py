#!/usr/bin/env python3
"""Load a committed second-generation tile set (PNG + JSON manifest) and
encode it for the GBA, independent of the painters that drew it.

    python3 tools/tiles2/gba.py verdant            # summary
    python3 tools/tiles2/gba.py verdant --entry tree

API (for the integration into tools/gen_field_gfx.py or a new generator):

    ts = load('verdant')              # manifest + pixels
    enc = encode(ts)                  # tiles, palettes, per-entry refs
    enc['tiles']      list of 64-tuple colour indices (0 = transparent)
    enc['palettes']   8 x 16 BGR555 values (bank b, index 0 unused)
    enc['refs'][name] list, per frame, per cell (row-major), of 4 screen
                      entries (TL, TR, BL, BR) = tile | hflip<<10 |
                      vflip<<11 | bank<<12 (the GBA text-BG format;
                      tile 0 = transparent)

Variants: encode(ts, variant='autumn') swaps the palette only; tile data
and refs are identical, so a map can change season by reloading banks.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
ASSETS = os.path.join(ROOT, 'assets', 'tiles2')

from core import read_png_rgba, hex_rgb, c15, q15  # noqa: E402

QUADS = ((0, 0), (8, 0), (0, 8), (8, 8))


def load(name, root=ASSETS):
    d = os.path.join(root, name)
    with open(os.path.join(d, name + '.json')) as f:
        man = json.load(f)
    w, h, rows = read_png_rgba(os.path.join(d, name + '.png'))
    rgb2role = {}
    for role, hx in man['palette'].items():
        rgb = q15(hex_rgb(hx))
        rgb2role.setdefault(rgb, []).append(role)
    return {'name': name, 'manifest': man, 'w': w, 'h': h, 'rows': rows, 'rgb2role': rgb2role,
            'entries': {e['name']: e for e in man['entries']}}


def cell_pixels(ts, cx, cy):
    """16x16 list of roles (None = transparent) at sheet cell (cx, cy).
    A pixel whose colour several roles share resolves to all of them; the
    encoder picks whichever sits in the chosen bank."""
    out = []
    for y in range(16):
        row = []
        for x in range(16):
            r, g, b, a = ts['rows'][cy * 16 + y][cx * 16 + x]
            if a < 128:
                row.append(None)
            else:
                roles = ts['rgb2role'].get((r, g, b))
                if roles is None:
                    raise ValueError('%s: pixel (%d,%d) colour %s not in palette' %
                                     (ts['name'], cx * 16 + x, cy * 16 + y, (r, g, b)))
                row.append(tuple(roles))
        out.append(row)
    return out


def entry_cells(e):
    """[(frame, [(cx, cy) row-major])] for an entry."""
    frames = e.get('frames') or [[e['x'], e['y']]]
    out = []
    for (fx, fy) in frames:
        out.append([(fx + i, fy + j) for j in range(e['h']) for i in range(e['w'])])
    return out


def _flip(t, h, v):
    o = []
    for y in range(8):
        sy = 7 - y if v else y
        r = t[sy * 8:sy * 8 + 8]
        o.extend(r[::-1] if h else r)
    return tuple(o)


def encode(ts, variant=None):
    man = ts['manifest']
    banks = man['banks']
    pal = dict(man['palette'])
    if variant:
        pal.update(man['variants'][variant])
    bank_sets = [set(b) for b in banks]
    tiles = [tuple([0] * 64)]
    lookup = {tiles[0]: (0, 0, 0)}
    refs = {}
    for e in man['entries']:
        per = []
        for cells in entry_cells(e):
            fr = []
            for (cx, cy) in cells:
                px = cell_pixels(ts, cx, cy)
                q4 = []
                for (qx, qy) in QUADS:
                    quad = [px[qy + y][qx + x] for y in range(8) for x in range(8)]
                    opts = [set(p) for p in quad if p is not None]
                    if not opts:
                        q4.append(0)
                        continue
                    b = None
                    for i, bs in enumerate(bank_sets):
                        if all(o & bs for o in opts):
                            b = i
                            break
                    if b is None:
                        raise ValueError('%s.%s: 8x8 tile at cell (%d,%d) fits no bank' %
                                         (ts['name'], e['name'], cx, cy))
                    idx = tuple(0 if p is None else next(banks[b].index(r) + 1 for r in p if r in bank_sets[b])
                                for p in quad)
                    hit = None
                    for hf in (0, 1):
                        for vf in (0, 1):
                            f = _flip(idx, hf, vf)
                            if f in lookup:
                                t, fh, fv = lookup[f]
                                hit = t | ((hf ^ fh) << 10) | ((vf ^ fv) << 11)
                                break
                        if hit is not None:
                            break
                    if hit is None:
                        t = len(tiles)
                        tiles.append(idx)
                        lookup[idx] = (t, 0, 0)
                        hit = t
                    q4.append(hit | (b << 12))
                fr.append(q4)
            per.append(fr)
        refs[e['name']] = per
    palettes = []
    for b in range(8):
        row = [0] * 16
        if b < len(banks):
            for i, role in enumerate(banks[b]):
                row[i + 1] = c15(hex_rgb(pal[role]))
        palettes.append(row)
    return {'tiles': tiles, 'palettes': palettes, 'refs': refs}


def pack4(idx):
    """64 colour indices -> 8 u32 words (GBA 4bpp, low nibble = left)."""
    words = []
    for y in range(8):
        w = 0
        for x in range(8):
            w |= (idx[y * 8 + x] & 15) << (4 * x)
        words.append(w)
    return words


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    ts = load(argv[1])
    enc = encode(ts)
    man = ts['manifest']
    print('%s: %d entries, %d tiles (incl. blank), %d banks' % (argv[1], len(man['entries']), len(enc['tiles']),
                                                               len(man['banks'])))
    if '--entry' in argv:
        n = argv[argv.index('--entry') + 1]
        e = ts['entries'][n]
        print(json.dumps({k: v for k, v in e.items()}, indent=1))
        for fi, fr in enumerate(enc['refs'][n]):
            print('frame %d:' % fi, ' '.join('[%s]' % ','.join('%04x' % v for v in q) for q in fr))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
