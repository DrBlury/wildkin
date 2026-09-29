"""Volcanic art: lava, crust, vents, smoke, obsidian, embers, rail track,
forges, water towers, coal, braziers, salamander statues."""

import math

from core import Img, hash32, rnd, bayer, value_noise
from paint import stamp, scatter, clump_crown, autotile_block
import terrain as T


def lava_surface(L, frame, seed=0, w=16, h=16):
    """Molten rock: a warm base crossed by slow bright seams that drift east,
    one dark crust plate per tile riding the flow, rare white-hot sparks.
    L = [crust dark, crust, base, bright, white-hot]. 4 frames, tiles at 16."""
    img = Img(w, h, L[2])
    # bright seams: gentle sine ribbons
    for k, (y0, amp, ph) in enumerate(((3, 1.5, 0.0), (10, 2.0, 2.1))):
        for x in range(w):
            y = int(round(y0 + amp * math.sin((x + frame * 2 + seed) * math.tau / w + ph)))
            img.p[y % h][x] = L[3]
            if (x + frame + k) % 5 == 0:
                img.p[(y + 1) % h][x] = L[3]
    # crust plate
    cx = (4 + frame * 2 + seed * 3) % w
    for (dx, dy) in ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (3, 1), (1, 2), (2, 2)):
        img.p[(6 + dy) % h][(cx + dx) % w] = L[1]
    img.p[6][(cx + 1) % w] = L[0]
    img.p[7][(cx + 2) % w] = L[0]
    # sparks
    sx = (11 + frame * 5) % w
    img.p[(13 + frame) % h][sx] = L[4]
    return img


def lava_autotile(L, ground, crust, frame, seed=0):
    """Lava over ash/rock: a dark crust rim, a glowing edge, then the flow."""
    surf = lava_surface(L, frame, seed)
    wob = T.wobble(seed, 0.9)

    def color_at(d, X, Y, side, v, alt):
        if d < -1.4:
            return ground.p[Y][X]
        if d < -0.4:
            return crust[1]
        if d < 0.4:
            return crust[0]
        if d < 1.4:
            return L[3] if (X + Y + frame) % 4 else L[4]
        return surf.p[Y][X]
    return autotile_block(color_at, E=4.0, R=4.5, Rn=2.5, wob=wob, dither=0.4)


def puff(img, x, y, r, inner, outer):
    """A soft cloud puff: solid core, dithered rim (reads as translucent)."""
    for yy in range(int(y - r - 1), int(y + r + 2)):
        for xx in range(int(x - r - 1), int(x + r + 2)):
            d = math.hypot((xx + 0.5 - x), (yy + 0.5 - y) * 1.15) / r
            if d < 0.55:
                img.set(xx, yy, inner)
            elif d < 1.0 and (xx + yy) % 2 == 0:
                img.set(xx, yy, outer)


def vent(R, steam, out, frame):
    """Fumarole: a crater with drifting steam (1x2, top cell is the plume)."""
    img = Img(16, 32)
    img.ellipse(8, 26, 7, 4.5, R[1])
    img.ellipse(8, 25.5, 5.5, 3, R[2])
    img.ellipse(8, 26, 3.5, 2, R[0])
    img = img.outline(out)
    for i in range(3):
        y = 22 - ((frame * 6 + i * 8) % 22)
        x = 8 + int(2 * math.sin((y + i * 5) / 4.0))
        puff(img, x, y, 1.6 + (22 - y) / 9.0, steam[1], steam[0])
    return img


def smoke(S, frame, w=16, h=32):
    img = Img(w, h)
    for i in range(3):
        y = (h - 3) - ((frame * 5 + i * 10) % (h - 3))
        x = 7 + int(3 * math.sin((y + i * 9) / 5.0)) + (h - y) // 10
        puff(img, x, y, 1.8 + (h - y) / 11.0, S[1], S[0])
    return img


def ember_rock(R, glow, out, frame=0, seed=0):
    """Basalt block with glowing cracks that pulse."""
    from props import rock
    img = rock(16, 16, R, out, seed, parts=[(8, 9.5, 6.5, 5), (5, 7.5, 3.5, 2.8)])
    cracks = [(5, 7), (6, 8), (7, 8), (8, 9), (9, 9), (10, 10), (8, 10), (8, 11)]
    for i, (x, y) in enumerate(cracks):
        if img.get(x, y) not in (None, out):
            img.set(x, y, glow[1] if (i + frame) % 3 else glow[2])
    return img


def railway_block(bal, tie, metal, out):
    """Railway on a ballast bed as a 64x32 custom block (opaque ballast):
    row 0: [E-W][N-S][E-W west end][E-W east end]
    row 1: [N-S north end][N-S south end][crossing][buffer stop E-W]"""
    img = Img(64, 32)
    for y in range(32):
        for x in range(64):
            n = hash32(x, y, 3) % 7
            img.p[y][x] = bal[2] if n < 3 else (bal[1] if n < 6 else bal[0])

    def ew(ox, oy, x0=0, x1=15):
        for x in range(x0, x1 + 1, 4):
            img.rect(ox + x, oy + 2, ox + x + 1, oy + 13, tie[1])
            img.vline(ox + x, oy + 2, oy + 13, tie[2])
        for ry in (4, 11):
            img.hline(ox + x0, ox + x1, oy + ry, metal[2])
            img.hline(ox + x0, ox + x1, oy + ry + 1, metal[0])

    def ns(ox, oy, y0=0, y1=15):
        for y in range(y0, y1 + 1, 4):
            img.rect(ox + 2, oy + y, ox + 13, oy + y + 1, tie[1])
            img.hline(ox + 2, ox + 13, oy + y, tie[2])
        for rx in (4, 11):
            img.vline(ox + rx, oy + y0, oy + y1, metal[2])
            img.vline(ox + rx + 1, oy + y0, oy + y1, metal[0])
    ew(0, 0)
    ns(16, 0)
    ew(32, 0, 3, 15)
    ew(48, 0, 0, 12)
    ns(0, 16, 3, 15)
    ns(16, 16, 0, 12)
    ew(32, 16)
    ns(32, 16)
    ew(48, 16, 0, 10)
    img.rect(48 + 11, 16 + 2, 48 + 14, 16 + 13, tie[0])
    img.vline(48 + 11, 16 + 2, 16 + 13, tie[2])
    return img


def water_tower(wood, metal, water, out, w=32, h=64):
    img = Img(w, h)
    for x in (4, 12, 19, 27):
        img.line(x, 30, x + (2 if x < 16 else -2), h - 2, wood[1])
    img.line(5, 40, 26, 40, wood[0])
    img.line(5, 50, 26, 50, wood[0])
    img.line(6, 32, 25, 52, wood[0])
    img.rect(2, 8, w - 3, 30, wood[1])
    for x in range(3, w - 3, 3):
        img.vline(x, 9, 29, wood[2] if x % 2 else wood[1])
    for y in (12, 20, 27):
        img.hline(2, w - 3, y, metal[0])
    for y in range(0, 9):
        half = 4 + y * 1.6
        img.hline(int(w / 2 - half), int(w / 2 + half), y, metal[1] if y % 3 else metal[2])
    img.line(w - 4, 24, w - 1, 34, metal[1])
    return img.outline(out)


def coal_pile(coal, out):
    img = Img(32, 16)
    img.ellipse(16, 11, 14, 5, coal[0])
    img.ellipse(15, 9.5, 11, 4, coal[1])
    for (x, y) in scatter(28, 10, 14, 5, margin=2, min_dist=3):
        if img.get(x + 2, y + 4) is not None:
            img.set(x + 2, y + 4, coal[2])
    return img.outline(out)


def brazier(metal, fire, out, frame):
    img = Img(16, 32)
    img.rect(5, 18, 10, 29, metal[1])
    img.vline(5, 18, 29, metal[2])
    img.rect(3, 29, 12, 30, metal[0])
    img.rect(2, 14, 13, 18, metal[1])
    img.hline(2, 13, 14, metal[2])
    img.hline(3, 12, 18, metal[0])
    shapes = [
        ['...d..d...', '..dmd.dm..', '.dmhmdmhd.', '.dmhhhhmd.', '..mhhhhm..'],
        ['....d.....', '..d.dmd...', '.dmdmhmd..', '.dmhhhhmd.', '..mhhhhm..'],
        ['..d....d..', '.dmd..dmd.', '.dmhddhmd.', '.dmhhhhmd.', '..mhhhhm..'],
    ]
    for j, r in enumerate(shapes[frame % 3]):
        for i, ch in enumerate(r):
            if ch != '.':
                img.set(3 + i, 8 + j, {'h': fire[2], 'm': fire[1], 'd': fire[0]}[ch])
    return img.outline(out)


def anvil(metal, block, out):
    img = Img(16, 16)
    img.rect(4, 10, 11, 14, block[1])
    img.hline(4, 11, 10, block[2])
    img.rect(2, 5, 13, 7, metal[1])
    img.hline(2, 13, 5, metal[2])
    img.rect(0, 5, 2, 6, metal[1])
    img.rect(6, 8, 9, 9, metal[0])
    return img.outline(out)


def salamander_statue(stone, out, eye, plinth, h=48):
    """An original fire-lizard kin carved in basalt (2x3)."""
    from props import rock
    img = Img(32, h)
    img.rect(4, h - 12, 27, h - 3, plinth[1])
    img.hline(4, 27, h - 12, plinth[2])
    img.hline(3, 28, h - 3, plinth[0])
    parts = [(16, h - 19, 9, 5), (9, h - 24, 5, 4.2), (24, h - 21, 5, 3), (28, h - 26, 2.5, 4)]
    body = rock(32, h, stone, out, 5, parts=parts)
    img.paste(body, 0, 0)
    img.set(8, h - 26, eye)
    img.set(7, h - 26, eye)
    for x in (12, 20):
        img.rect(x, h - 15, x + 2, h - 13, stone[0])
    for (x, y) in ((13, h - 25), (17, h - 25), (21, h - 24)):
        img.set(x, y, stone[3])
        img.set(x, y - 1, stone[3])
    return img.outline(out)


def smokestack(brick, metal, out, w=16, h=48):
    img = Img(w, h)
    for y in range(4, h - 1):
        for x in range(3, w - 3):
            row = y // 3
            c = brick[1]
            if y % 3 == 2 or (x + (row % 2) * 2) % 4 == 0:
                c = brick[0]
            if x == 3:
                c = brick[2]
            img.set(x, y, c)
    img.rect(2, 2, w - 3, 5, metal[1])
    img.hline(2, w - 3, 2, metal[2])
    return img.outline(out)


def cinder_cone(R, crater, out, w=32, h=32):
    """Small volcanic cone with a glowing crater (2x2)."""
    img = Img(w, h)
    for y in range(6, h - 2):
        t = (y - 6) / (h - 8)
        half = 5 + t * (w / 2 - 6)
        for x in range(int(w / 2 - half), int(w / 2 + half)):
            u = (x + 0.5 - (w / 2 - half)) / (2 * half)
            k = 3 if u < 0.28 else (2 if u < 0.55 else (1 if u < 0.82 else 0))
            if (x * 3 + y * 5) % 11 == 0:
                k = max(0, k - 1)
            img.set(x, y, R[k])
    img.ellipse(w / 2, 7, 5.5, 2.4, R[0])
    img.ellipse(w / 2, 7.3, 3.8, 1.4, crater[0])
    img.hline(int(w / 2) - 2, int(w / 2) + 1, 7, crater[1])
    return img.outline(out)
