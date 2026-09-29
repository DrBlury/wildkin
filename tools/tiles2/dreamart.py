"""Dream art: star-dusted grass, moon lilies, crystal trees, moon lanterns,
spire towers, mirrors, floating pages."""

import math

from core import Img, hash32, rnd
from paint import stamp, scatter, clump_crown, grass


def star_grass(R, star, seed=0, n=2):
    img = grass(R, seed, tufts=3, flecks=2)
    for i, (x, y) in enumerate(scatter(13, 13, n, seed + 50, margin=2, min_dist=6)):
        img.set(x, y, star)
        if i % 2 == 0:
            img.set(x - 1, y, R['lt'])
            img.set(x + 1, y, R['lt'])
            img.set(x, y - 1, R['lt'])
            img.set(x, y + 1, R['lt'])
    return img


def moon_lily(ground, petal, glow, stem, frame):
    """Glowing lilies on a ground tile, pulsing over 3 frames."""
    img = ground.copy()
    for i, (x, y) in enumerate(((3, 3), (10, 8), (4, 11))):
        img.set(x + 1, y + 4, stem)
        img.set(x + 1, y + 5, stem)
        c = glow if (i + frame) % 3 == 0 else petal
        stamp(img, x, y, '''
        p.p
        ppp
        .p.
        ''', {'p': c})
        if (i + frame) % 3 == 0:
            img.set(x - 1, y + 1, petal)
            img.set(x + 3, y + 1, petal)
    return img


def crystal_tree(C, out, trunk_c, w=32, h=48, seed=0):
    """A tree of glassy crystal: faceted crown with sparkles."""
    img = Img(w, h)
    img.rect(w / 2 - 1, h - 18, w / 2 + 1, h - 3, trunk_c[1])
    img.vline(int(w / 2) - 1, h - 18, h - 3, trunk_c[2])
    img.hline(int(w / 2) - 3, int(w / 2) + 3, h - 3, trunk_c[0])
    cl = [(16, 14, 9, 8), (9, 20, 6, 5.5), (23, 20, 6, 5.5), (16, 24, 8, 6), (16, 6, 6, 5.5)]
    crown = clump_crown(w, h, cl, C, None, speck=False, gdark=0.4, rim=1.0, dither=0.0)
    # facet lines
    for y in range(h):
        for x in range(w):
            if crown.p[y][x] is not None and (x + y * 2) % 7 == 0:
                crown.p[y][x] = C[max(0, C.index(crown.p[y][x]) - 1)]
    img.paste(crown, 0, 0)
    for (x, y) in ((11, 9), (20, 13), (14, 21), (22, 22)):
        img.set(x, y, C[-1])
    return img.outline(out)


def spire(stone, roof, trim, glass, out, w=48, h=96):
    """Dreamspire tower (3x6): tapering marble shaft, gold bands, cone roof."""
    img = Img(w, h)
    cx = w / 2
    top = 30
    for y in range(top, h - 2):
        t = (y - top) / (h - 2 - top)
        half = 9 + t * 11
        for x in range(int(cx - half), int(cx + half)):
            u = (x + 0.5 - (cx - half)) / (2 * half)
            c = stone[3] if u < 0.2 else (stone[2] if u < 0.6 else (stone[1] if u < 0.9 else stone[0]))
            if (y - top) % 16 == 0:
                c = trim[1]
            img.set(x, y, c)
    for y in range(4, top + 1):
        half = (y - 4) * 0.42 + 1
        for x in range(int(cx - half), int(cx + half) + 1):
            img.set(x, y, roof[2] if x < cx else roof[1])
    img.hline(int(cx - 12), int(cx + 12), top, trim[1])
    img.rect(cx - 1, 0, cx, 4, trim[1])
    img.set(int(cx) - 1, 0, trim[2])
    for (wy) in (44, 60):
        img.rect(cx - 3, wy, cx + 2, wy + 7, trim[0])
        img.rect(cx - 2, wy + 1, cx + 1, wy + 7, glass[1])
        img.ellipse(cx - 0.5, wy + 1, 2.5, 1.5, glass[1])
        img.set(int(cx) - 1, wy + 2, glass[2])
    img.rect(cx - 5, h - 16, cx + 4, h - 3, trim[0])
    img.rect(cx - 4, h - 15, cx + 3, h - 3, glass[0])
    img.ellipse(cx - 0.5, h - 15, 4.5, 2.5, glass[0])
    return img.outline(out)


def mirror(frame_c, glass, out, w=16, h=32):
    img = Img(w, h)
    img.ellipse(8, 11, 6, 9.5, frame_c[1])
    img.ellipse(8, 11, 4.6, 8, glass[1])
    img.line(5, 8, 8, 4, glass[2])
    img.line(6, 11, 10, 6, glass[2])
    img.rect(6, 20, 9, 27, frame_c[1])
    img.rect(3, 27, 12, 29, frame_c[0])
    img.hline(3, 12, 27, frame_c[2])
    return img.outline(out)


def floating_pages(paper, ink, frame, w=16, h=16):
    img = Img(w, h)
    for i, (x, y) in enumerate(((2, 6), (9, 3), (6, 10))):
        dy = [0, -1, -2, -1][(frame + i) % 4]
        img.rect(x, y + dy, x + 4, y + dy + 3, paper[1])
        img.hline(x, x + 4, y + dy, paper[2])
        img.set(x + 1, y + dy + 2, ink)
        img.set(x + 3, y + dy + 2, ink)
    return img


def moon_orb(stone, glow, out, frame):
    """Pedestal with a softly pulsing moon orb (1x2)."""
    img = Img(16, 32)
    img.rect(5, 16, 10, 29, stone[1])
    img.vline(5, 16, 29, stone[2])
    img.rect(3, 29, 12, 30, stone[0])
    img.rect(3, 14, 12, 16, stone[2])
    r = 4.5 + (frame % 2) * 0.5
    img.ellipse(8, 9, r, r, glow[0])
    img.ellipse(7.3, 8.3, r - 1.5, r - 1.5, glow[1])
    img.set(6, 7, glow[2])
    return img.outline(out)
