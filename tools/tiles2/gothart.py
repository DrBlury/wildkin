"""Gothic art for the grim downs and haunted woods: gravestones, iron
fences, wisps, mausoleums, pumpkins, barrows, twisted trees, fog."""

import math

from core import Img, hash32, rnd, bayer
from paint import stamp, scatter, clump_crown
from flora import dead_tree, trunk


def gravestone(stone, out, kind='round', moss=None):
    img = Img(16, 16)
    if kind == 'round':
        img.rect(4, 5, 11, 14, stone[1])
        img.ellipse(7.5, 5, 4, 3, stone[1])
        img.vline(4, 4, 14, stone[2])
        img.hline(5, 10, 3, stone[2])
        img.vline(11, 5, 14, stone[0])
        img.hline(6, 9, 7, stone[0])
        img.hline(6, 9, 9, stone[0])
    elif kind == 'cross':
        img.rect(7, 2, 8, 14, stone[1])
        img.rect(4, 5, 11, 6, stone[1])
        img.vline(7, 2, 14, stone[2])
        img.hline(4, 11, 5, stone[2])
    else:                             # slab
        img.rect(3, 7, 12, 14, stone[1])
        img.hline(3, 12, 7, stone[2])
        img.vline(12, 7, 14, stone[0])
        img.set(5, 9, stone[0])
        img.set(10, 11, stone[0])
    img.hline(2, 13, 15, stone[0])
    if moss:
        for x in range(4, 12, 2):
            img.set(x, 14, moss)
    return img.outline(out)


def iron_fence(metal, out, tip=None):
    """Wrought-iron fence, same layout as props.fence_block:
    row 0 [post][W end][mid][E end], row 1 [N end][mid][S end][gate]."""
    img = Img(64, 32)
    tp = tip or metal[2]

    def bars(ox, oy, x0, x1):
        for x in range(x0, x1 + 1, 3):
            img.vline(ox + x, oy + 4, oy + 14, metal[1])
            img.set(ox + x, oy + 3, tp)
            img.set(ox + x, oy + 2, tp)
        img.hline(ox + x0, ox + x1, oy + 6, metal[0])
        img.hline(ox + x0, ox + x1, oy + 12, metal[0])

    def post(ox, oy):
        img.rect(ox + 6, oy + 2, ox + 9, oy + 15, metal[0])
        img.vline(ox + 6, oy + 2, oy + 15, metal[2])
        img.rect(ox + 5, oy + 1, ox + 10, oy + 2, metal[1])
    post(0, 0)
    bars(16, 0, 8, 15)
    post(16, 0)
    bars(32, 0, 0, 15)
    bars(48, 0, 0, 7)
    post(48, 0)
    for k, (y0, y1) in enumerate(((4, 15), (0, 15), (0, 11))):
        ox = k * 16
        img.rect(ox + 7, y0 + 16, ox + 8, y1 + 16, metal[1])
        for y in range(y0 + 16, y1 + 17, 3):
            img.set(ox + 6, y, tp)
            img.set(ox + 9, y, metal[0])
    bars(48, 16, 1, 14)
    img.ellipse(48 + 8, 16 + 4, 4, 2, metal[1])
    return img.outline(out)


def wisp(core_c, glow, frame, w=16, h=16):
    """Will-o'-wisp: a bobbing flame with a dithered halo (4 frames)."""
    img = Img(w, h)
    bob = [0, -1, -2, -1][frame % 4]
    cx, cy = 8, 8 + bob
    for y in range(h):
        for x in range(w):
            d = math.hypot(x + 0.5 - cx, (y + 0.5 - cy) * 1.2)
            if d < 1.6:
                img.p[y][x] = core_c[1]
            elif d < 2.8:
                img.p[y][x] = core_c[0]
            elif d < 5.0 and (x + y + frame) % 2 == 0:
                img.p[y][x] = glow
    img.set(cx, cy - 3, core_c[0])
    img.set(cx + (frame % 2), cy - 4, glow)
    return img


def mausoleum(stone, roof, door, out, w=48, h=48):
    img = Img(w, h)
    # pediment roof
    for y in range(2, 14):
        half = 4 + (y - 2) * 1.75
        for x in range(int(w / 2 - half), int(w / 2 + half)):
            img.set(x, y, roof[2] if x < w / 2 else roof[1])
    img.hline(1, w - 2, 14, roof[0])
    img.hline(2, w - 3, 13, roof[2])
    # columns and walls
    for y in range(15, h - 4):
        for x in range(3, w - 3):
            c = stone[1]
            if (y - 15) % 5 == 4:
                c = stone[0]
            img.set(x, y, c)
    for x in (5, 12, w - 16, w - 9):
        img.rect(x, 15, x + 3, h - 5, stone[2])
        img.vline(x, 15, h - 5, stone[3] if len(stone) > 3 else stone[2])
        img.vline(x + 3, 15, h - 5, stone[0])
    img.rect(w / 2 - 6, 24, w / 2 + 5, h - 5, door[0])
    img.rect(w / 2 - 5, 25, w / 2 + 4, h - 5, door[1])
    img.vline(int(w / 2), 25, h - 5, door[0])
    img.ellipse(w / 2, 24, 6, 3, door[0])
    img.rect(1, h - 4, w - 2, h - 2, stone[2])
    img.hline(1, w - 2, h - 4, stone[3] if len(stone) > 3 else stone[2])
    img.hline(1, w - 2, h - 2, stone[0])
    return img.outline(out)


def pumpkin(P, stem, out, face=None):
    img = Img(16, 16)
    img.ellipse(8, 10, 6, 4.5, P[1])
    img.ellipse(7, 9.5, 4.2, 3.2, P[2])
    for x in (5, 8, 11):
        img.vline(x, 7, 14, P[0])
    img.rect(7, 4, 8, 6, stem)
    if face:
        img.set(5, 9, face)
        img.set(10, 9, face)
        img.hline(6, 10, 12, face)
    return img.outline(out)


def barrow(G, out, door=None, w=48, h=32):
    """Grassy burial mound with a stone-framed entrance (3x2)."""
    img = Img(w, h)
    cl = [(24, 20, 21, 11), (13, 21, 10, 8), (35, 21, 10, 8)]
    body = clump_crown(w, h, cl, G, None, speck=True, gdark=0.4, rim=0.8, dither=0.4)
    img.paste(body, 0, 0)
    if door:
        img.rect(19, 18, 28, h - 2, door[0])
        img.rect(20, 20, 27, h - 2, door[1])
        img.hline(18, 29, 17, door[2])
        img.vline(18, 17, h - 2, door[2])
        img.vline(29, 17, h - 2, door[2])
    return img.outline(out)


def twisted_tree(bark, out, leaf=None, w=32, h=48, seed=0):
    """A gnarled tree leaning over, with sparse ragged foliage."""
    img = dead_tree(w, h, bark, out, seed=seed, spread=1.25)
    if leaf:
        cl = []
        for i in range(6):
            x = 6 + rnd(i, seed) * (w - 12)
            y = 4 + rnd(i, seed, 1) * h * 0.35
            cl.append((x, y, 3.5 + rnd(i, seed, 2) * 2))
        crown = clump_crown(w, h, cl, leaf, None, speck=False, gdark=0.3)
        for y in range(h):
            for x in range(w):
                if crown.p[y][x] is not None and (x * 7 + y * 3 + seed) % 5:
                    img.p[y][x] = crown.p[y][x]
        img = img.outline(out)
    return img


def fog(F, frame, w=16, h=16):
    """Drifting fog wisp (transparent, top layer): sparse dithered band."""
    img = Img(w, h)
    for y in range(h):
        for x in range(w):
            v = math.sin((x + frame * 2) * math.tau / w + y * 0.6) + math.sin(y * math.tau / h * 2)
            if v > 0.9 and (x + y) % 2 == 0:
                img.p[y][x] = F[1]
            elif v > 0.4 and (x + y) % 4 == 0:
                img.p[y][x] = F[0]
    return img


def memorial(stone, flame, out, w=16, h=32):
    """Memorial lantern pillar (Duskmere custom)."""
    img = Img(w, h)
    img.rect(5, 12, 10, h - 3, stone[1])
    img.vline(5, 12, h - 3, stone[2])
    img.vline(10, 12, h - 3, stone[0])
    img.rect(3, h - 3, 12, h - 2, stone[0])
    img.rect(3, 9, 12, 11, stone[2])
    img.rect(4, 3, 11, 8, stone[1])
    img.rect(6, 4, 9, 7, flame[0])
    img.rect(7, 5, 8, 6, flame[1])
    for y in range(0, 3):
        img.hline(5 + y // 2, 10 - y // 2, 2 - y, stone[2])
    return img.outline(out)


def ruined_windmill(stone, wood, out, w=48, h=64):
    img = Img(w, h)
    cx = w / 2
    for y in range(18, h - 2):
        half = 10 + (y - 18) * 0.15
        for x in range(int(cx - half), int(cx + half)):
            c = stone[2] if x < cx - 3 else stone[1]
            if (y % 5 == 0) or (x + (y // 5) * 3) % 7 == 0:
                c = stone[0]
            img.set(x, y, c)
    # broken top
    for x in range(int(cx - 10), int(cx + 10)):
        cut = 18 + hash32(x, 7) % 5
        for y in range(18, cut):
            img.set(x, y, None)
    # a single broken sail
    img.line(int(cx), 24, int(cx) - 16, 6, wood[1])
    img.line(int(cx) + 1, 24, int(cx) - 15, 6, wood[0])
    for t in range(6, 16):
        x = int(cx) - t
        y = 24 - int(t * 1.1)
        img.set(x - 1, y - 2, wood[2])
        img.set(x - 2, y - 1, wood[1])
    img.rect(cx - 4, h - 14, cx + 3, h - 3, wood[0])
    return img.outline(out)
