"""Dungeon art (crypts, drowned temples): masonry faces, floor slabs,
carpets, candles, sarcophagi, urns, banners, chains, webs, thrones,
skull niches, iron gates, current floors, bells, shell lamps."""

import math

from core import Img, hash32, rnd, bayer
from paint import stamp, scatter, clump_crown, autotile_block
import terrain as T


def masonry(M, w=32, h=32, bw=16, bh=8, seed=0):
    """Large dressed stone blocks, lit top edges, dark joints.
    M = [joint, dark, base, light]."""
    img = Img(w, h, M[2])
    for y in range(h):
        row = y // bh
        off = (row % 2) * (bw // 2)
        for x in range(w):
            k = y % bh
            j = (x + off) % bw
            c = M[2]
            if k == bh - 1 or j == bw - 1:
                c = M[0]
            elif k == 0 or j == 0:
                c = M[3]
            elif k == bh - 2 or j == bw - 2:
                c = M[1]
            if c == M[2] and hash32((x + off) // bw, row, seed) % 4 == 0 and (x + y) % 5 == 0:
                c = M[1]
            img.p[y][x] = c
    return img


def floor_slabs(M, w=16, h=16, seed=0, cracked=False):
    img = Img(w, h, M[2])
    for y in range(h):
        for x in range(w):
            if x % 8 == 7 or y % 8 == 7:
                img.p[y][x] = M[0]
            elif x % 8 == 0 or y % 8 == 0:
                img.p[y][x] = M[3]
            elif (x % 8 == 6 or y % 8 == 6):
                img.p[y][x] = M[1]
    if cracked:
        x, y = 3 + seed % 4, 2
        for k in range(10):
            img.set(x, y, M[0])
            x += (hash32(k, seed) % 3) - 1
            y += 1
    return img


def carpet_autotile(C, floor, trim):
    """Carpet runner over a floor: border band in trim, pattern inside.
    C = [dark, base, light]."""
    def color_at(d, X, Y, side, v, alt):
        if d < 0:
            return floor.p[Y][X]
        if d < 1.0:
            return trim[0]
        if d < 2.0:
            return trim[1]
        if d < 3.0:
            return C[0]
        if (X + Y) % 8 == 0 or (X - Y) % 8 == 0:
            return C[2]
        return C[1]
    return autotile_block(color_at, E=3.0, R=1.0, Rn=1.0, dither=0.0)


def candles(wax, flame, out, frame):
    img = Img(16, 16)
    for i, (x, h) in enumerate(((4, 6), (8, 9), (12, 5))):
        top = 15 - h
        img.rect(x - 1, top, x, 14, wax[1])
        img.vline(x - 1, top, 14, wax[2])
        fy = top - 2 - ((frame + i) % 2)
        img.set(x - 1, fy, flame[1])
        img.set(x - 1, fy + 1, flame[0])
        img.set(x, fy + 1, flame[0] if (frame + i) % 2 else flame[1])
    img.hline(2, 13, 15, wax[0])
    return img.outline(out)


def sarcophagus(stone, out, trim=None, w=32, h=32):
    """Lidded stone coffin seen from above (2x2)."""
    img = Img(w, h)
    img.rect(3, 4, w - 4, h - 3, stone[1])
    img.rect(4, 5, w - 5, h - 5, stone[2])
    img.hline(4, w - 5, 5, stone[3])
    img.vline(4, 5, h - 5, stone[3])
    img.hline(3, w - 4, h - 3, stone[0])
    # carved figure
    img.ellipse(w / 2, 10, 3, 3, stone[1])
    img.rect(w / 2 - 4, 13, w / 2 + 3, h - 8, stone[1])
    img.vline(int(w / 2) - 1, 14, h - 9, stone[0])
    if trim:
        img.hline(4, w - 5, h - 6, trim)
        img.set(int(w / 2), 10, trim)
    return img.outline(out)


def coffin(wood, out):
    img = Img(16, 32)
    pts = [(5, 2), (10, 2), (13, 8), (11, 29), (4, 29), (2, 8)]
    for y in range(2, 30):
        if y < 8:
            t = (y - 2) / 6
            xl, xr = 5 - 3 * t, 10 + 3 * t
        else:
            t = (y - 8) / 21
            xl, xr = 2 + 2 * t, 13 - 2 * t
        for x in range(int(xl), int(xr) + 1):
            img.set(x, y, wood[2] if x < (xl + xr) / 2 - 2 else wood[1])
    img.vline(7, 6, 24, wood[0])
    img.hline(5, 9, 10, wood[0])
    return img.outline(out)


def urn(clay, out, band=None):
    img = Img(16, 16)
    img.ellipse(8, 9.5, 5, 5, clay[1])
    img.ellipse(7, 8.5, 3.2, 3.2, clay[2])
    img.rect(6, 2, 9, 5, clay[1])
    img.hline(5, 10, 2, clay[2])
    img.hline(5, 10, 14, clay[0])
    if band:
        img.hline(4, 12, 10, band)
    return img.outline(out)


def banner(cloth, rod, emblem, out, w=16, h=32):
    img = Img(w, h)
    img.hline(1, 14, 1, rod[1])
    img.set(0, 1, rod[2])
    img.set(15, 1, rod[2])
    for y in range(2, h - 4):
        for x in range(3, 13):
            img.set(x, y, cloth[1] if x < 11 else cloth[0])
        img.set(3, y, cloth[2])
    for x in range(3, 13):
        if x % 3 != 1:
            img.vline(x, h - 4, h - 2 - (x % 2), cloth[1])
    img.rect(6, 9, 9, 14, emblem)
    img.set(7, 8, emblem)
    return img.outline(out)


def chains(metal, out, w=16, h=32):
    img = Img(w, h)
    for x0 in (4, 11):
        for y in range(0, h - 4, 3):
            if (y // 3) % 2:
                img.vline(x0, y, y + 2, metal[1])
            else:
                img.rect(x0 - 1, y, x0 + 1, y + 2, metal[1])
                img.set(x0, y + 1, None)
    img.rect(8, h - 5, 14, h - 3, metal[0])
    return img.outline(out)


def web(silk, w=16, h=16):
    img = Img(w, h)
    for a in range(0, 91, 15):
        r = 15
        img.line(0, 0, int(math.cos(math.radians(a)) * r), int(math.sin(math.radians(a)) * r), silk)
    for r in (4, 8, 12):
        for a in range(0, 91, 6):
            img.set(int(math.cos(math.radians(a)) * r), int(math.sin(math.radians(a)) * r), silk)
    return img


def throne(stone, cloth, gold, out, w=32, h=48):
    img = Img(w, h)
    img.rect(6, 2, w - 7, 30, stone[1])
    img.rect(8, 4, w - 9, 28, cloth[1])
    img.vline(8, 4, 28, cloth[2])
    for y in range(0, 4):
        img.hline(6 + y, w - 7 - y, y, stone[2])
    img.rect(3, 26, w - 4, 36, stone[2])
    img.rect(8, 28, w - 9, 34, cloth[1])
    img.rect(3, 22, 7, 36, stone[1])
    img.rect(w - 8, 22, w - 4, 36, stone[1])
    img.rect(2, 37, w - 3, h - 3, stone[1])
    img.hline(2, w - 3, 37, stone[3])
    img.set(int(w / 2), 2, gold[1])
    img.set(int(w / 2) - 1, 3, gold[1])
    img.set(int(w / 2) + 1, 3, gold[1])
    img.hline(8, w - 9, 12, gold[0])
    return img.outline(out)


def skull_niche(stone, bone, out, w=16, h=16):
    """Alcove in a wall face holding a skull (placed on wall faces)."""
    img = Img(w, h)
    img.rect(2, 3, 13, 14, stone[0])
    img.ellipse(7.5, 3, 6, 3, stone[0])
    img.rect(4, 7, 11, 13, stone[1])
    img.draw('''
    .bbbb.
    bhhhhb
    bdhhdb
    .bhhb.
    ..bb..
    ''', {'b': bone[1], 'h': bone[2], 'd': bone[0]}, 5, 8)
    return img.outline(out)


def iron_gate(metal, out, w=32, h=32):
    img = Img(w, h)
    img.rect(0, 0, 3, h - 1, metal[0])
    img.rect(w - 4, 0, w - 1, h - 1, metal[0])
    for x in range(5, w - 5, 4):
        img.vline(x, 3, h - 2, metal[1])
        img.set(x, 2, metal[2])
    img.hline(4, w - 5, 8, metal[0])
    img.hline(4, w - 5, 22, metal[0])
    img.ellipse(w / 2, 4, 12, 3, metal[1])
    return img.outline(out)


def current_floor(W, frame, dir='S', w=16, h=16):
    """Flowing water that carries people: chevrons marching along dir."""
    img = Img(w, h, W[1])
    for y in range(h):
        for x in range(w):
            if dir in 'NS':
                t = (y - frame * 2) if dir == 'S' else (y + frame * 2)
                k = (t - abs(x - 7.5) * 0.8) % 8
            else:
                t = (x - frame * 2) if dir == 'E' else (x + frame * 2)
                k = (t - abs(y - 7.5) * 0.8) % 8
            if k < 1.5:
                img.p[y][x] = W[3]
            elif k < 3:
                img.p[y][x] = W[2]
            elif k > 7:
                img.p[y][x] = W[0]
    return img


def bell(metal, out, w=32, h=32):
    img = Img(w, h)
    for y in range(4, 26):
        t = (y - 4) / 22
        half = 5 + t ** 1.6 * 9
        for x in range(int(w / 2 - half), int(w / 2 + half)):
            u = (x + 0.5 - (w / 2 - half)) / (2 * half)
            img.set(x, y, metal[3] if u < 0.2 else (metal[2] if u < 0.5 else (metal[1] if u < 0.85 else metal[0])))
    img.rect(w / 2 - 2, 1, w / 2 + 1, 4, metal[1])
    img.hline(int(w / 2) - 14, int(w / 2) + 13, 26, metal[0])
    img.ellipse(w / 2, 28, 2.5, 2, metal[1])
    return img.outline(out)


def shell_lamp(shell, glow, stand, out, h=32):
    img = Img(16, h)
    img.rect(7, 12, 8, h - 3, stand[1])
    img.vline(7, 12, h - 3, stand[2])
    img.rect(4, h - 3, 11, h - 2, stand[0])
    img.ellipse(8, 8, 6, 5, shell[1])
    for x in range(3, 14, 2):
        img.line(8, 12, x, 3, shell[0])
    img.ellipse(8, 9, 2.5, 2, glow[1])
    img.set(7, 8, glow[2])
    return img.outline(out)
