#!/usr/bin/env python3
"""Report kin sprites whose art touches the frame edge (i.e. is cut off).

    python3 tools/check_kin_clip.py            # every kin
    python3 tools/check_kin_clip.py 52,53,54   # only these ids

Checks the 64x64 front (all four edges), the 64x64 back (top, left and
right; the bottom is cropped on purpose), the 32x32 icon (all edges) and the
six 32x32 overworld frames (all edges). Exits 1 if anything touches.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_monsters as g  # noqa: E402


def touches(img, w, h, edges):
    hit = []
    if 'top' in edges and any(img[x] for x in range(w)):
        hit.append('top')
    if 'bottom' in edges and any(img[(h - 1) * w + x] for x in range(w)):
        hit.append('bottom')
    if 'left' in edges and any(img[y * w] for y in range(h)):
        hit.append('left')
    if 'right' in edges and any(img[y * w + w - 1] for y in range(h)):
        hit.append('right')
    return hit


def check(i):
    _, (front, back, icon, pal, ow, ow_h) = g.build_one(i)
    all4 = ('top', 'bottom', 'left', 'right')
    out = []
    for kind, img, w, edges in (('front', front, 64, all4),
                                ('back', back, 64, ('top', 'left', 'right')),
                                ('icon', icon, 32, all4)):
        hit = touches(img, w, w, edges)
        if hit:
            out.append('%s:%s' % (kind, '/'.join(hit)))
    for f, img in enumerate(ow):
        hit = touches(img, 32, 32, all4)
        if hit:
            out.append('ow%d:%s' % (f, '/'.join(hit)))
    return i, out


def main():
    if len(sys.argv) > 1:
        ids = [int(x) for x in sys.argv[1].split(',')]
    else:
        ids = list(range(len(g.SPECIES)))
    from multiprocessing import Pool
    with Pool(os.cpu_count() or 1) as pool:
        res = sorted(pool.map(check, ids))
    bad = 0
    for i, out in res:
        if out:
            bad += 1
            print('%3d %-10s %s' % (i, g.SPECIES[i][0], ' '.join(out)))
    print('%d of %d kin touch a frame edge' % (bad, len(ids)))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
