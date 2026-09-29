"""Cave art: rock floors, chasms, ladders, crystals, glowcaps, stalagmites,
mine rails and carts, timber supports, ore, hanging roots, rope bridges."""

import math

from core import Img, hash32, rnd, bayer
from paint import stamp, scatter, clump_crown, autotile_block
import terrain as T


def chasm_autotile(floor, void, lip, rock, seed=0):
    """A drop into darkness cut into the floor: the north edge shows the
    far wall of the pit falling away (rock bands into void), other edges a
    crumbly lip. rock: dark -> light."""
    wob = T.wobble(seed, 0.7, 1.1)

    def color_at(d, X, Y, side, v, alt):
        if d < -0.8:
            return floor.p[Y][X]
        if d < 0.3:
            return lip
        if 'N' in side and v != 1:
            # the far wall visible below the north lip
            if d < 2.0:
                return rock[2]
            if d < 3.5:
                return rock[1] if (X + Y) % 2 else rock[0]
            if d < 5.0:
                return rock[0] if (X * 3 + Y) % 4 else void
            return void
        if d < 1.2:
            return rock[0]
        return void
    return autotile_block(color_at, E=4.0, R=4.0, Rn=2.0, wob=wob, dither=0.0)


def ladder(wood, out, hole=None, down=False):
    img = Img(16, 16)
    if hole:
        img.ellipse(8, 8.5, 7, 6, hole[0])
        img.ellipse(8, 8, 6, 5, hole[1])
    for x in (4, 11):
        img.rect(x, 1 if not down else 4, x + 1, 15 if not down else 14, wood[1])
        img.vline(x, 1 if not down else 4, 15 if not down else 14, wood[2])
    for y in range(3 if not down else 6, 15, 3):
        img.hline(5, 10, y, wood[2])
        img.hline(5, 10, y + 1, wood[0])
    return img.outline(out)


def crystal(C, out, frame=0, w=16, h=16, seed=0):
    """Glowing crystal cluster: C = [dark, base, light, glint]; the glint
    wanders between facets over 3 frames."""
    img = Img(w, h)
    spikes = [(8, 2, 2.8), (4, 6, 2.2), (12, 5, 2.2), (6, 9, 1.8), (11, 9, 1.8)]
    for i, (cx, top, hw) in enumerate(spikes):
        for y in range(top, h - 2):
            t = min(1.0, (y - top) / 3.0)
            half = hw * t
            for x in range(int(round(cx - half)), int(round(cx + half)) + 1):
                u = (x + 0.5 - (cx - half)) / max(1.0, 2 * half)
                img.set(x, y, C[2] if u < 0.35 else (C[1] if u < 0.7 else C[0]))
        if (i + frame) % 3 == 0:
            img.set(int(cx) - 1, top + 2, C[3])
            img.set(int(cx) - 1, top + 3, C[3])
    return img.outline(out)


def glowcaps(cap, stem, glow, out, frame=0):
    img = Img(16, 16)
    pts = [(4, 8, 1), (9, 5, 2), (12, 10, 1)]
    for i, (x, y, s) in enumerate(pts):
        img.rect(x, y + 1, x, y + 5, stem)
        img.rect(x - s - 1, y - 1, x + s + 1, y, cap[1])
        img.hline(x - s, x + s, y - 2, cap[2])
        img.set(x - s, y - 1, cap[2])
        if (i + frame) % 2 == 0:
            img.set(x, y - 1, glow)
            img.set(x + 1, y - 2, glow)
    return img.outline(out)


def stalagmite(R, out, w=16, h=32, seed=0):
    img = Img(w, h)
    for (cx, top, hw) in ((7, 3, 4.5), (12, 14, 2.5)):
        for y in range(top, h - 2):
            t = (y - top) / (h - 2 - top)
            half = 0.8 + hw * t ** 0.7
            for x in range(int(cx - half), int(cx + half) + 1):
                u = (x + 0.5 - (cx - half)) / max(1.0, 2 * half)
                k = 3 if u < 0.25 else (2 if u < 0.55 else (1 if u < 0.85 else 0))
                if (y + x) % 5 == 0:
                    k = max(0, k - 1)
                img.set(x, y, R[k])
    return img.outline(out)


def rails_block(metal, wood, out):
    """Mine rails as a 64x32 custom block (transparent, over floor):
    row 0: [east-west][north-south][corner S-E][corner S-W]
    row 1: [corner N-E][corner N-W][buffer stop][crossing]"""
    img = Img(64, 32)

    def ties_h(ox, oy):
        for x in range(1, 16, 4):
            img.rect(ox + x, oy + 3, ox + x + 1, oy + 12, wood[1])
            img.vline(ox + x, oy + 3, oy + 12, wood[2])

    def ties_v(ox, oy):
        for y in range(1, 16, 4):
            img.rect(ox + 3, oy + y, ox + 12, oy + y + 1, wood[1])
            img.hline(ox + 3, ox + 12, oy + y, wood[2])

    def rail_h(ox, oy, x0=0, x1=15):
        for ry in (5, 10):
            img.hline(ox + x0, ox + x1, oy + ry, metal[2])
            img.hline(ox + x0, ox + x1, oy + ry + 1, metal[0])

    def rail_v(ox, oy, y0=0, y1=15):
        for rx in (5, 10):
            img.vline(ox + rx, oy + y0, oy + y1, metal[2])
            img.vline(ox + rx + 1, oy + y0, oy + y1, metal[0])
    ties_h(0, 0)
    rail_h(0, 0)
    ties_v(16, 0)
    rail_v(16, 0)

    def curve(ox, oy, cx, cy):
        for r, c in ((5.5, metal[2]), (10.5, metal[2])):
            for a in range(0, 91, 3):
                ar = math.radians(a)
                x = cx + (r * math.cos(ar) if cx == 0 else -r * math.cos(ar))
                y = cy + (r * math.sin(ar) if cy == 0 else -r * math.sin(ar))
                img.set(ox + int(x), oy + int(y), c)
                img.set(ox + int(x) + 1, oy + int(y), metal[0])
    curve(32, 0, 15, 15)
    curve(48, 0, 0, 15)
    curve(0, 16, 15, 0)
    curve(16, 16, 0, 0)
    ties_h(32, 16)
    rail_h(32, 16, 0, 9)
    img.rect(32 + 9, 16 + 3, 32 + 12, 16 + 12, wood[1])
    img.vline(32 + 9, 16 + 3, 16 + 12, wood[2])
    ties_h(48, 16)
    rail_h(48, 16)
    rail_v(48, 16)
    return img.outline(out)


def mine_cart(metal, out, ore=None):
    img = Img(16, 16)
    for y in range(4, 12):
        inset = (y - 4) // 3
        img.hline(1 + inset, 14 - inset, y, metal[1])
    img.hline(1, 14, 4, metal[2])
    img.hline(2, 13, 11, metal[0])
    img.vline(4, 5, 10, metal[0])
    img.vline(11, 5, 10, metal[0])
    for cx in (4, 11):
        img.rect(cx - 1, 12, cx + 1, 14, metal[0])
        img.set(cx, 13, metal[2])
    if ore:
        for (x, y) in ((4, 2), (7, 1), (10, 2), (6, 3), (9, 3)):
            img.rect(x, y, x + 1, y + 1, ore[1])
            img.set(x, y, ore[2])
    return img.outline(out)


def timber_frame(wood, out, w=48, h=48):
    """Mine entrance / tunnel support: two posts and a lintel (3x3,
    walk under the middle)."""
    img = Img(w, h)
    for x in (4, w - 9):
        img.rect(x, 8, x + 4, h - 2, wood[1])
        img.vline(x, 8, h - 2, wood[2])
        img.vline(x + 4, 8, h - 2, wood[0])
    img.rect(1, 4, w - 2, 10, wood[1])
    img.hline(1, w - 2, 4, wood[2])
    img.hline(1, w - 2, 10, wood[0])
    for x in range(6, w - 6, 8):
        img.set(x, 7, wood[0])
    img.line(9, 11, 14, 17, wood[1])
    img.line(w - 10, 11, w - 15, 17, wood[1])
    return img.outline(out)


def ore_rock(R, ore, out, seed=0):
    from props import rock
    img = rock(16, 16, R, out, seed, parts=[(8, 9.5, 6.5, 5), (5.5, 7.5, 3.5, 2.8)])
    for (x, y) in ((5, 8), (9, 7), (10, 11), (6, 12)):
        if img.get(x, y) not in (None, out):
            img.set(x, y, ore[1])
            img.set(x + 1, y, ore[0])
            img.set(x, y - 1, ore[2])
    return img


def hanging_roots(R, out, w=16, h=16, seed=0):
    img = Img(w, h)
    for i in range(5):
        x = 1 + i * 3 + hash32(i, seed) % 2
        ln = 5 + hash32(i, seed, 1) % 10
        for y in range(ln):
            xx = x + int(round(math.sin((y + i) / 3.0)))
            img.set(xx, y, R[1] if y % 3 else R[2])
            img.set(xx + 1, y, R[0])
    return img.outline(out)


def rope_bridge(wood, rope, out, w=3):
    """East-west rope bridge over a chasm (w x 2 cells, floor)."""
    img = Img(w * 16, 32)
    W = img.w
    for x in range(W):
        sag = int(2 * math.sin(x / (W - 1) * math.pi))
        for y in range(8 + sag, 24 + sag):
            if x % 4 == 3:
                img.set(x, y, wood[0])
            else:
                img.set(x, y, wood[2] if y == 8 + sag else wood[1])
        img.set(x, 5 + sag, rope)
        img.set(x, 26 + sag, rope)
        if x % 8 == 0:
            img.vline(x, 5 + sag, 8 + sag, rope)
            img.vline(x, 24 + sag, 26 + sag, rope)
    return img.outline(out)


def lantern_hook(metal, glass, out, frame=0):
    img = Img(16, 16)
    img.vline(8, 0, 3, metal[0])
    img.rect(6, 4, 10, 10, metal[1])
    img.rect(7, 5, 9, 9, glass[1 + frame % 2] if len(glass) > 2 else glass[1])
    img.hline(5, 11, 4, metal[2])
    img.hline(6, 10, 11, metal[0])
    return img.outline(out)


def bones(bone, out):
    img = Img(16, 16)
    img.line(3, 11, 11, 7, bone[1])
    img.line(3, 12, 11, 8, bone[0])
    for (x, y) in ((2, 10), (2, 12), (12, 6), (12, 8)):
        img.rect(x, y, x + 1, y + 1, bone[2])
    img.ellipse(11, 12, 2.5, 2, bone[1])
    img.set(10, 12, bone[0])
    img.set(12, 12, bone[0])
    return img.outline(out)
