"""Jungle art: buttress trees, broad-leaf plants, bamboo, vines, orchids,
woven huts, mossy ruin blocks and an idol."""

import math

from core import Img, hash32, rnd
from paint import stamp, scatter, clump_crown
from flora import tree, trunk


def buttress_tree(leaf, out, bark, bark_out, w=48, h=64, seed=0):
    """Giant with a wide, flaring root base (3x4)."""
    img = Img(w, h)
    cx = w / 2
    gy = h - 3
    # buttress roots: fins spreading from the trunk
    for side in (-1, 1):
        for k, spread in enumerate((9, 15, 21)):
            for t in range(0, 18):
                u = t / 17
                x = cx + side * (2 + spread * u ** 1.6)
                y = gy - 16 + t
                for dx in range(0, 3 - k // 2):
                    img.set(int(x + side * dx), int(y), bark[2] if side < 0 else bark[0])
                img.set(int(x - side), int(y), bark[1])
    trunk(img, cx, 30, gy, 8, bark, bark_out, roots=2, seed=seed)
    cl = [(24, 16, 12), (12, 20, 9), (36, 20, 9), (16, 10, 9), (32, 10, 9), (24, 6, 8), (8, 28, 7), (40, 28, 7),
          (18, 27, 9), (30, 27, 9)]
    crown = clump_crown(w, h, cl, leaf, out, seed=seed, gdark=0.45)
    img.paste(crown, 0, 0)
    return img.outline(bark_out)


def big_leaf_plant(leaf, out, w=16, h=16, seed=0):
    """Monstera-like clump: a few broad split leaves."""
    img = Img(w, h)
    leaves = [(5, 9, 5, 3.5, -0.5), (11, 8, 5, 3.5, 0.5), (8, 5, 4.5, 3.2, 0.0), (8, 12, 5, 3, 0.1)]
    for (cx, cy, rx, ry, rot) in leaves:
        for y in range(h):
            for x in range(w):
                dx, dy = x + 0.5 - cx, y + 0.5 - cy
                ca, sa = math.cos(rot), math.sin(rot)
                u = (dx * ca + dy * sa) / rx
                v = (-dx * sa + dy * ca) / ry
                if u * u + v * v <= 1:
                    c = leaf[2] if v < -0.2 else (leaf[1] if v < 0.4 else leaf[0])
                    if abs(v) < 0.12:
                        c = leaf[3]          # midrib
                    if (int((u + 1) * 4) % 2 == 0) and abs(v) > 0.55:
                        c = None             # splits
                    if c is not None:
                        img.set(x, y, c)
    return img.outline(out)


def bamboo(G, out, w=16, h=32, seed=0):
    img = Img(w, h)
    for i, x in enumerate((3, 7, 11)):
        top = 1 + (hash32(i, seed) % 6)
        for y in range(top, h - 1):
            img.set(x, y, G[2])
            img.set(x + 1, y, G[1])
            if (y - top) % 6 == 5:
                img.set(x, y, G[0])
                img.set(x + 1, y, G[0])
        for y in range(top + 3, h - 8, 7):
            img.line(x + 2, y, x + 5, y - 2, G[3])
            img.set(x + 5, y - 1, G[2])
    return img.outline(out)


def vines(G, flower=None, w=16, h=32, seed=0):
    """Hanging vines (top layer)."""
    img = Img(w, h)
    for i in range(4):
        x = 2 + i * 4 + hash32(i, seed) % 2
        ln = 12 + hash32(i, seed, 2) % (h - 12)
        for y in range(ln):
            xx = x + int(round(math.sin((y + i * 3) / 4.0)))
            img.set(xx, y, G[1])
            if y % 4 == 2:
                img.set(xx + 1, y, G[2])
                img.set(xx - 1, y + 1, G[2])
        if flower and i % 2 == 0:
            img.set(x, ln, flower)
    return img


def orchid(petal, center, leaf, out):
    img = Img(16, 16)
    img.line(8, 14, 8, 7, leaf[1])
    img.line(8, 13, 4, 10, leaf[2])
    img.line(8, 12, 12, 9, leaf[2])
    for (x, y) in ((6, 4), (10, 5)):
        stamp(img, x - 2, y - 2, '''
        .p.p.
        ppcpp
        .ppp.
        ..p..
        ''', {'p': petal, 'c': center})
    return img.outline(out)


def woven_hut(wall, roof, trim, out, glass, w=64, h=64):
    """Canopy Hearth home: woven reed walls, deep thatch, on a root deck."""
    img = Img(w, h)
    # deck + stilts
    for x in (6, w // 2 - 1, w - 9):
        img.rect(x, h - 12, x + 2, h - 2, trim[0])
        img.vline(x, h - 12, h - 2, trim[1])
    img.rect(1, h - 16, w - 2, h - 12, trim[1])
    img.hline(1, w - 2, h - 16, trim[2])
    for x in range(2, w - 2, 5):
        img.vline(x, h - 15, h - 12, trim[0])
    # woven wall
    for y in range(26, h - 16):
        for x in range(6, w - 6):
            k = ((x // 3) + (y // 3)) % 2
            c = wall[2] if k else wall[1]
            if (x % 3 == 0) or (y % 3 == 0):
                c = wall[0]
            img.set(x, y, c)
    img.rect(w // 2 - 6, h - 32, w // 2 + 5, h - 17, trim[0])
    img.rect(w // 2 - 5, h - 31, w // 2 + 4, h - 17, glass[0])
    img.rect(10, 32, 17, 38, glass[0])
    img.set(16, 33, glass[1])
    # thatch: steep, deep eaves
    for y in range(0, 28):
        half = 4 + y * 1.15
        for x in range(int(w / 2 - half), int(w / 2 + half)):
            n = hash32(x % 16, (y // 2) % 8, 3) % 5
            c = roof[2] if n < 2 else (roof[1] if n < 4 else roof[3] if len(roof) > 3 else roof[2])
            if y % 4 == 3:
                c = roof[0] if (x % 3) else roof[1]
            img.set(x, y, c)
    img.hline(int(w / 2 - 36), int(w / 2 + 36), 27, roof[0])
    return img.outline(out)


def ruin_block(stone, moss, out, w=32, h=32, seed=0):
    """Carved temple block with moss (2x2)."""
    img = Img(w, h)
    for y in range(4, h - 1):
        for x in range(1, w - 1):
            c = stone[2]
            if y < 7:
                c = stone[3]
            if (y - 7) % 8 == 7 or (x + ((y - 7) // 8) * 8) % 16 == 0:
                c = stone[0]
            img.set(x, y, c)
    # carved spiral
    for a in range(0, 540, 20):
        r = a / 540 * 6
        x = 16 + math.cos(math.radians(a)) * r
        y = 18 + math.sin(math.radians(a)) * r
        img.set(int(x), int(y), stone[1])
    for x in range(1, w - 1):
        if hash32(x, seed) % 3:
            img.set(x, 4, moss[1])
            img.set(x, 5, moss[0] if x % 2 else moss[1])
        if hash32(x, seed, 2) % 5 == 0:
            for y in range(6, 6 + hash32(x, seed, 3) % 8):
                img.set(x, y, moss[0])
    return img.outline(out)


def idol(stone, out, eye, h=48):
    img = Img(32, h)
    for y in range(6, h - 2):
        half = 9 if y > 14 else 7
        for x in range(16 - half, 16 + half):
            u = (x - (16 - half)) / (2 * half)
            img.set(x, y, stone[3] if u < 0.25 else (stone[2] if u < 0.7 else stone[1]))
    for y in range(2, 8):
        img.hline(9, 22, y, stone[3] if y < 4 else stone[2])
    img.rect(10, 16, 13, 18, stone[0])
    img.rect(18, 16, 21, 18, stone[0])
    img.set(11, 17, eye)
    img.set(19, 17, eye)
    img.rect(12, 24, 19, 27, stone[0])
    for x in range(12, 20, 2):
        img.set(x, 25, stone[3])
    img.hline(7, 24, h - 3, stone[0])
    return img.outline(out)
