"""Snow and ice art: snow ground, ice floors, snowbanks, cairns, snowmen,
ice crystals, steam, sleds, icicles, hot springs."""

import math

from core import Img, hash32, rnd, bayer, value_noise
from paint import stamp, scatter, clump_crown
from flora import lattice_render, shape_patch9


def snow_ground(S, seed=0, sparkle=3, drifts=True, w=16, h=16):
    """Snow: soft blue-grey wind ripples, a few sparkles.
    S = [shadow, dk, base, lt, hi]."""
    img = Img(w, h, S[2])
    if drifts:
        for i in range(1 + seed % 2):
            y0 = 2 + (hash32(i, seed) % 12)
            x0 = 1 + hash32(i, seed, 1) % 9
            ln = 3 + hash32(i, seed, 2) % 5
            for k in range(ln):
                x = x0 + k
                if 1 <= x < w - 1:
                    img.set(x, y0, S[1])
                    if 0 < k < ln - 1:
                        img.set(x, y0 - 1, S[3])
    for i, (x, y) in enumerate(scatter(w - 2, h - 2, sparkle, seed + 9, margin=1, min_dist=4)):
        img.set(x, y, S[4])
    return img


def ice_floor(I, seed=0, w=16, h=16):
    """Slippery ice: glossy streaks and a few cracks. I = [dk, base, lt, hi]."""
    img = Img(w, h, I[1])
    for y in range(h):
        for x in range(w):
            if (x - y + 32) % 11 < 2:
                img.p[y][x] = I[2]
            if (x - y + 32) % 11 == 0 and (x + y) % 3 == 0:
                img.p[y][x] = I[3]
    x, y = 3 + seed % 5, 9 + seed % 4
    for k in range(6):
        img.set(x, y, I[0])
        x += 1
        y += (hash32(k, seed) % 3) - 1
    return img


def snowbank(S, out, seed=0):
    """Wind-packed snow walls as a patch9 (like hedges, but pillowy)."""
    def render(mask, W, H):
        return lattice_render(mask, W, H, S, out, seed, period=16, r=6.2, ry=5.4,
                              centers=((8, 6), (0, 12.5)), lobes=3)
    return shape_patch9(render)


def cairn(stone, out, snow=None):
    img = Img(16, 32)
    stones = [(8, 27, 6, 3.4), (7.5, 21.5, 5, 3), (8.5, 16.5, 4.2, 2.6), (8, 12, 3.2, 2.2), (8, 8, 2.2, 1.8)]
    body = clump_crown(16, 32, stones, stone, None, speck=False, gdark=0.3, rim=0.9)
    img.paste(body, 0, 0)
    if snow:
        for (x, y, rx, ry) in stones:
            for xx in range(int(x - rx + 1), int(x + rx - 1)):
                img.set(xx, int(y - ry + 0.5), snow)
    return img.outline(out)


def snowman(S, out, coal, carrot, scarf):
    img = Img(16, 32)
    parts = [(8, 25, 6.5, 5.5), (8, 16, 4.8, 4.2), (8, 9, 3.6, 3.3)]
    body = clump_crown(16, 32, parts, S, None, speck=False, gdark=0.35, rim=0.8)
    img.paste(body, 0, 0)
    img.set(7, 8, coal)
    img.set(9, 8, coal)
    img.set(10, 10, carrot)
    img.set(11, 10, carrot)
    img.hline(5, 11, 12, scarf[1])
    img.rect(10, 13, 11, 16, scarf[0])
    for y in (15, 18, 21):
        img.set(8, y, coal)
    img.line(4, 16, 0, 12, coal)
    img.line(12, 16, 15, 12, coal)
    return img.outline(out)


def ice_crystal(I, out, w=16, h=32, seed=0):
    """Clustered hexagonal ice spikes, glossy left faces."""
    img = Img(w, h)
    spikes = [(8, 4, 3.2), (4, 12, 2.4), (12, 10, 2.6), (6, 18, 2.2)]
    for (cx, top, hw) in spikes:
        for y in range(top, h - 2):
            t = min(1.0, (y - top) / 4.0)
            half = hw * t
            for x in range(int(cx - half), int(cx + half) + 1):
                u = (x - (cx - half)) / max(1.0, 2 * half)
                img.set(x, y, I[3] if u < 0.25 else (I[2] if u < 0.55 else I[1]))
    img.hline(2, w - 3, h - 2, I[0])
    return img.outline(out)


def steam(S, frame, w=16, h=32):
    """Rising steam puffs (transparent, top layer), 4 frames."""
    from fireart import puff
    img = Img(w, h)
    for i in range(3):
        y = (h - 4) - ((frame * 5 + i * 11) % (h - 4))
        x = 8 + int(3 * math.sin((y + i * 7) / 5.0))
        puff(img, x, y, 1.8 + (h - y) / 12.0, S[2], S[1])
    return img


def sled(wood, metal, out):
    img = Img(32, 16)
    img.rect(3, 5, 26, 9, wood[1])
    img.hline(3, 26, 5, wood[2])
    for x in range(6, 26, 5):
        img.vline(x, 6, 9, wood[0])
    img.hline(2, 28, 12, metal[1])
    img.line(28, 12, 30, 9, metal[1])
    for x in (6, 22):
        img.vline(x, 10, 11, metal[0])
    return img.outline(out)


def icicles(I, out, w=16):
    """A strip of icicles hanging from an eave or cliff lip (top layer)."""
    img = Img(w, 16)
    for x in range(0, w):
        ln = 2 + (hash32(x, 3) % 6)
        for y in range(ln):
            img.set(x, y, I[3] if x % 2 == 0 else I[2])
        if ln > 4:
            img.set(x, ln - 1, I[1])
    return img


def hot_spring(water, rock, steam_c, out, frame, w=48, h=32):
    """Rock-rimmed pool (3x2), animated shimmer."""
    img = Img(w, h)
    img.ellipse(w / 2, h / 2 + 1, w / 2 - 1, h / 2 - 2, rock[0])
    img.ellipse(w / 2, h / 2, w / 2 - 1, h / 2 - 2, rock[2])
    for (x, y) in ((6, 8), (14, 4), (26, 3), (38, 6), (43, 14), (38, 24), (22, 27), (8, 22)):
        img.ellipse(x, y, 3.5, 2.5, rock[1])
        img.ellipse(x - 0.8, y - 0.8, 2, 1.4, rock[3])
    img.ellipse(w / 2, h / 2 + 0.5, w / 2 - 6, h / 2 - 7, water[0])
    img.ellipse(w / 2, h / 2 + 1, w / 2 - 7, h / 2 - 8, water[1])
    for i in range(6):
        x = 12 + (i * 5 + frame * 3) % 24
        y = 12 + (i * 3) % 8
        img.hline(x, x + 2, y, water[2])
    img.set(18 + frame % 3, 14, steam_c)
    return img.outline(out)


def frozen_pond_rim(S):
    return None
