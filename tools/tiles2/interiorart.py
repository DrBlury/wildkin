"""Interior art: floors, wallpapered back walls, windows, doors, stairs,
counters and furniture. All furniture is lit from the upper left with a
darker front face (the GBA 3/4 look): top surface light, front darker."""

import math

from core import Img, hash32, rnd
from paint import stamp, scatter, clump_crown


# ---------------------------------------------------------------------------
# floors and walls
# ---------------------------------------------------------------------------

def wood_floor(W, w=16, h=16, seed=0):
    """Plank floor, boards running east-west, staggered joints. W = [gap, dk, base, lt]."""
    img = Img(w, h, W[2])
    for y in range(h):
        row = y // 4
        for x in range(w):
            k = y % 4
            c = W[2]
            if k == 3:
                c = W[0]
            elif k == 0:
                c = W[3]
            if (x + row * 5 + seed) % 16 == 0 and k != 3:
                c = W[0]
            if (x * 7 + row * 3) % 13 == 0 and k == 2:
                c = W[1]
            img.p[y][x] = c
    return img


def checker(A, B, line, w=16, h=16):
    img = Img(w, h)
    for y in range(h):
        for x in range(w):
            c = A if ((x // 8) + (y // 8)) % 2 == 0 else B
            if x % 8 == 7 or y % 8 == 7:
                c = line
            img.p[y][x] = c
    return img


def wall_face(paper, wains, base, pattern='stripe', w=32, h=32):
    """A 2-cell-tall back wall texture (32x32): wallpaper above a wooden
    wainscot and a dark baseboard. paper/wains: [dk, base, lt]."""
    img = Img(w, h)
    for y in range(h):
        for x in range(w):
            if y < 18:
                c = paper[1]
                if pattern == 'stripe' and x % 8 in (0, 1):
                    c = paper[2]
                elif pattern == 'dots' and (x % 8 == 3 and y % 8 == 3 or x % 8 == 7 and y % 8 == 7):
                    c = paper[2]
                elif pattern == 'diamond' and (abs((x % 8) - 4) + abs((y % 8) - 4)) == 3:
                    c = paper[2]
                elif pattern == 'panel' and (x % 16 in (0, 15) or y % 16 == 0):
                    c = paper[0]
                elif pattern == 'brick':
                    row = y // 4
                    if y % 4 == 3 or (x + (row % 2) * 4) % 8 == 0:
                        c = paper[0]
                if y == 0:
                    c = paper[2]
            elif y < 20:
                c = wains[2] if y == 18 else wains[0]
            elif y < 29:
                c = wains[1] if x % 8 else wains[0]
                if x % 8 == 1:
                    c = wains[2]
            else:
                c = base[1] if y < 31 else base[0]
            img.p[y][x] = c
    return img


def window(frame_c, glass, sky, out, curtain=None, w=32, h=32):
    """Window set into the back wall (2x2 over the wall face)."""
    img = Img(w, h)
    img.rect(4, 2, w - 5, 20, frame_c[1])
    img.rect(6, 4, w - 7, 18, sky[1])
    img.rect(6, 12, w - 7, 18, sky[0])
    img.vline(int(w / 2) - 1, 4, 18, frame_c[1])
    img.hline(6, w - 7, 11, frame_c[1])
    img.line(8, 9, 11, 6, glass)
    img.line(9, 10, 12, 7, glass)
    img.rect(3, 20, w - 4, 22, frame_c[2])
    img.hline(3, w - 4, 22, frame_c[0])
    if curtain:
        for x in (4, 5, 6, w - 7, w - 6, w - 5):
            img.vline(x, 2, 19, curtain[1] if x in (4, w - 5) else curtain[0])
        img.hline(3, w - 4, 1, curtain[2])
    return img.outline(out)


def door_mat(mat, out):
    img = Img(16, 16)
    img.rect(1, 5, 14, 14, mat[1])
    img.rect(2, 6, 13, 13, mat[2])
    for x in range(3, 13, 2):
        img.vline(x, 7, 12, mat[1])
    img.hline(1, 14, 14, mat[0])
    return img.outline(out)


def stairs_in(wood, out, down=False):
    img = Img(16, 32)
    for y in range(32):
        k = y % 4
        for x in range(1, 15):
            c = wood[2] if k == 0 else (wood[1] if k < 3 else wood[0])
            if x in (1, 14):
                c = wood[0]
            img.set(x, y, c)
    if down:
        for y in range(16, 32):
            for x in range(2, 14):
                if (y - 16) > (x - 2) * 1.3:
                    img.set(x, y, wood[0])
    return img.outline(out)


# ---------------------------------------------------------------------------
# furniture (box helper: top face + front face)
# ---------------------------------------------------------------------------

def box(img, x0, y0, x1, y1, front_h, top, front, edge=None):
    """A piece of furniture: lit top surface over a darker front face."""
    ty1 = y1 - front_h
    img.rect(x0, y0, x1, ty1, top[1])
    img.hline(x0, x1, y0, top[2])
    img.vline(x0, y0, ty1, top[2])
    img.rect(x0, ty1 + 1, x1, y1, front[1])
    img.hline(x0, x1, ty1 + 1, edge or front[2])
    img.vline(x1, ty1 + 1, y1, front[0])
    img.hline(x0, x1, y1, front[0])


def table(wood, out, w=32, h=32, cloth=None):
    img = Img(w, h)
    box(img, 2, 6, w - 3, h - 8, 4, wood if not cloth else cloth, wood)
    for x in (4, w - 6):
        img.rect(x, h - 8, x + 1, h - 3, wood[0])
    if cloth:
        for x in range(2, w - 2, 3):
            img.set(x, h - 11, cloth[0])
    return img.outline(out)


def round_table(wood, out, cloth=None):
    img = Img(32, 32)
    img.ellipse(16, 14, 12, 7, (cloth or wood)[1])
    img.ellipse(15, 13, 9, 5, (cloth or wood)[2])
    img.ellipse(16, 16, 12, 5, (cloth or wood)[0])
    img.ellipse(16, 14, 12, 6.5, (cloth or wood)[1])
    img.ellipse(15, 13, 9, 4.6, (cloth or wood)[2])
    img.rect(14, 20, 17, 27, wood[1])
    img.rect(10, 27, 21, 29, wood[0])
    return img.outline(out)


def chair(wood, out, facing='down', cushion=None):
    img = Img(16, 16)
    if facing == 'down':
        img.rect(3, 1, 12, 7, wood[1])
        img.hline(3, 12, 1, wood[2])
        for x in range(5, 12, 3):
            img.vline(x, 2, 6, wood[0])
        box(img, 3, 7, 12, 12, 2, cushion or wood, wood)
    else:
        box(img, 3, 5, 12, 12, 2, cushion or wood, wood)
        img.rect(3, 11, 12, 14, wood[1])
        img.hline(3, 12, 11, wood[2])
    img.rect(3, 13, 4, 15, wood[0])
    img.rect(11, 13, 12, 15, wood[0])
    return img.outline(out)


def stool(wood, out):
    img = Img(16, 16)
    img.ellipse(8, 7, 5, 2.6, wood[2])
    img.ellipse(8, 8, 5, 2.4, wood[1])
    img.ellipse(8, 7, 5, 2.2, wood[2])
    for x in (5, 10):
        img.rect(x, 9, x, 14, wood[0])
    return img.outline(out)


def bed(frame_c, sheet, pillow, out, w=16, h=32, double=False):
    W = 32 if double else w
    img = Img(W, h)
    img.rect(1, 1, W - 2, 8, frame_c[1])
    img.hline(1, W - 2, 1, frame_c[2])
    img.rect(2, 6, W - 3, h - 4, sheet[1])
    img.rect(2, 13, W - 3, 15, sheet[2])
    img.vline(W - 3, 6, h - 4, sheet[0])
    for px in ([3] if not double else [3, 17]):
        img.rect(px, 5, px + 9, 10, pillow[1])
        img.hline(px, px + 9, 5, pillow[2])
    img.rect(1, h - 4, W - 2, h - 2, frame_c[1])
    img.hline(1, W - 2, h - 2, frame_c[0])
    return img.outline(out)


def bookshelf(wood, books, out, w=32, h=32):
    img = Img(w, h)
    img.rect(1, 1, w - 2, h - 2, wood[1])
    img.hline(1, w - 2, 1, wood[2])
    for sy in (3, 12, 21):
        img.rect(3, sy, w - 4, sy + 7, wood[0])
        x = 3
        i = 0
        while x < w - 4:
            bw = 2 + hash32(x, sy) % 2
            c = books[i % len(books)]
            top = sy + (hash32(x, sy, 1) % 3)
            img.rect(x, top, min(w - 4, x + bw - 1), sy + 7, c[1])
            img.vline(x, top, sy + 7, c[2])
            x += bw
            i += 1
        img.hline(2, w - 3, sy + 8, wood[2])
    img.hline(1, w - 2, h - 2, wood[0])
    return img.outline(out)


def counter(top, front, out, part='mid'):
    """Shop counter piece (1x1): 'left', 'mid', 'right', 'end'."""
    img = Img(16, 16)
    x0 = 2 if part in ('left', 'end') else 0
    x1 = 13 if part in ('right', 'end') else 15
    box(img, x0, 2, x1, 14, 6, top, front)
    for x in range(x0 + 2, x1, 4):
        img.vline(x, 9, 13, front[0])
    return img.outline(out)


def stove(metal, fire, out, frame=0):
    img = Img(16, 32)
    box(img, 1, 8, 14, 29, 14, metal, metal)
    img.rect(4, 10, 11, 12, metal[0])
    img.ellipse(5, 11, 1.5, 1, metal[2])
    img.ellipse(10, 11, 1.5, 1, metal[2])
    img.rect(4, 19, 11, 25, metal[0])
    img.rect(5, 21, 10, 24, fire[frame % 2])
    img.rect(6, 0, 8, 8, metal[0])
    return img.outline(out)


def fireplace(stone, fire, out, frame=0, w=32, h=32):
    img = Img(w, h)
    img.rect(1, 2, w - 2, h - 2, stone[1])
    img.rect(1, 2, w - 2, 5, stone[2])
    img.hline(0, w - 1, 2, stone[2])
    img.rect(7, 10, w - 8, h - 3, stone[0])
    img.ellipse(w / 2, 10, (w - 14) / 2, 3, stone[0])
    fl = [(10, 0), (14, 1), (18, 2), (21, 1)]
    for i, (x, ph) in enumerate(fl):
        hgt = 7 + ((frame + ph) % 3) * 2
        for y in range(h - 3 - hgt, h - 3):
            t = (y - (h - 3 - hgt)) / hgt
            img.set(x, y, fire[2] if t > 0.6 else (fire[1] if t > 0.25 else fire[0]))
            img.set(x + 1, y, fire[1] if t > 0.4 else fire[0])
    img.hline(8, w - 9, h - 3, stone[2])
    for y in range(6, h - 2, 4):
        for x in range(2, w - 2):
            if (x + (y // 4) * 4) % 8 == 0:
                img.set(x, y, stone[0])
    return img.outline(out)


def plant(pot, leaf, out, h=16, big=False):
    img = Img(16, h)
    py = h - 6
    img.rect(4, py, 11, h - 2, pot[1])
    img.vline(4, py, h - 2, pot[2])
    img.hline(3, 12, py, pot[2])
    cl = [(8, py - 5, 5.5), (4, py - 3, 3.5), (12, py - 3, 3.5), (8, py - 8, 4)]
    if big:
        cl += [(8, py - 13, 5), (5, py - 10, 4), (11, py - 10, 4)]
    crown = clump_crown(16, h, cl, leaf, None, speck=True, gdark=0.35)
    img.paste(crown, 0, 0)
    return img.outline(out)


def rug(R, out, w=48, h=32, pattern='diamond'):
    img = Img(w, h)
    img.rect(0, 0, w - 1, h - 1, R[0])
    img.rect(1, 1, w - 2, h - 2, R[2])
    img.rect(3, 3, w - 4, h - 4, R[1])
    cx, cy = w / 2, h / 2
    for y in range(4, h - 4):
        for x in range(4, w - 4):
            d = abs(x + 0.5 - cx) / (w / 2 - 4) + abs(y + 0.5 - cy) / (h / 2 - 4)
            if pattern == 'diamond' and 0.5 < d < 0.62:
                img.set(x, y, R[3] if len(R) > 3 else R[2])
            if pattern == 'diamond' and d < 0.2:
                img.set(x, y, R[2])
    for x in range(1, w - 1, 2):
        img.set(x, 0, R[2])
        img.set(x, h - 1, R[2])
    return img


def clock(wood, face, out):
    img = Img(16, 32)
    box(img, 3, 1, 12, 30, 2, wood, wood)
    img.ellipse(7.5, 7, 3.6, 3.6, face[1])
    img.set(7, 5, face[0])
    img.set(7, 6, face[0])
    img.set(8, 7, face[0])
    img.rect(5, 13, 10, 26, wood[0])
    img.vline(7, 14, 22, face[2])
    img.ellipse(7.5, 23, 1.8, 1.8, face[2])
    return img.outline(out)


def wardrobe(wood, out, w=32, h=32):
    img = Img(w, h)
    box(img, 2, 1, w - 3, h - 2, 26, wood, wood)
    img.vline(int(w / 2) - 1, 5, h - 3, wood[0])
    img.set(int(w / 2) - 3, 16, wood[2])
    img.set(int(w / 2) + 1, 16, wood[2])
    for y in (8, 22):
        img.hline(5, int(w / 2) - 4, y, wood[0])
        img.hline(int(w / 2) + 2, w - 6, y, wood[0])
    return img.outline(out)


def dresser(wood, out, knob):
    img = Img(32, 16)
    box(img, 2, 1, 29, 14, 9, wood, wood)
    for y in (7, 11):
        img.hline(3, 28, y, wood[0])
        img.set(9, y + 1, knob)
        img.set(22, y + 1, knob)
    return img.outline(out)


def pc(case, screen, out, frame=0):
    """Storage terminal (the kin storage link)."""
    img = Img(16, 32)
    box(img, 1, 14, 14, 30, 8, case, case)
    img.rect(2, 2, 13, 13, case[1])
    img.hline(2, 13, 2, case[2])
    img.rect(4, 4, 11, 11, screen[0])
    img.rect(5, 5, 10, 10, screen[1 + frame % 2])
    img.hline(5, 8, 6, screen[2] if len(screen) > 2 else screen[1])
    img.rect(4, 16, 11, 17, case[0])
    return img.outline(out)


def hearth_heal(stone, fire, gold, out, frame=0, w=32, h=32):
    """The Hearth Hall healing brazier: a stone bowl with a living flame on
    a gold-trimmed plinth (2x2)."""
    img = Img(w, h)
    box(img, 3, 16, w - 4, h - 2, 7, stone, stone)
    img.hline(3, w - 4, h - 9, gold[1])
    img.ellipse(w / 2, 14, 11, 4, stone[0])
    img.ellipse(w / 2, 13, 10, 3.2, stone[2])
    img.ellipse(w / 2, 13.5, 7, 2.2, stone[0])
    shapes = [(0, 9), (-4, 6), (4, 7), (-2, 11), (2, 10)]
    for i, (dx, hg) in enumerate(shapes):
        hh = hg + ((frame + i) % 3)
        for y in range(13 - hh, 14):
            t = (y - (13 - hh)) / hh
            half = 1.5 * t + 0.5
            for x in range(int(w / 2 + dx - half), int(w / 2 + dx + half) + 1):
                img.set(x, y, fire[2] if t < 0.3 else (fire[1] if t < 0.7 else fire[0]))
    return img.outline(out)


def shop_shelf(wood, goods, out, w=32, h=32):
    img = Img(w, h)
    img.rect(1, 1, w - 2, h - 2, wood[1])
    img.hline(1, w - 2, 1, wood[2])
    for sy in (4, 13, 22):
        img.hline(2, w - 3, sy + 7, wood[2])
        img.rect(2, sy, w - 3, sy + 6, wood[0])
        for i, x in enumerate(range(3, w - 5, 5)):
            g = goods[(i + sy) % len(goods)]
            img.rect(x, sy + 2, x + 3, sy + 6, g[1])
            img.hline(x, x + 3, sy + 2, g[2])
            img.set(x + 3, sy + 6, g[0])
    return img.outline(out)


def picture(frame_c, art, out, w=16, h=16):
    img = Img(w, h)
    img.rect(1, 2, 14, 12, frame_c[1])
    img.hline(1, 14, 2, frame_c[2])
    img.rect(3, 4, 12, 10, art[2])
    img.rect(3, 8, 12, 10, art[1])
    img.ellipse(10, 6, 1.5, 1.5, art[0] if len(art) > 3 else art[1])
    img.line(3, 9, 7, 6, art[0])
    img.line(7, 6, 12, 9, art[0])
    return img.outline(out)


def vase(clay, flower, out):
    img = Img(16, 16)
    img.ellipse(8, 11.5, 4, 3.5, clay[1])
    img.ellipse(7, 11, 2.4, 2, clay[2])
    img.rect(6, 6, 9, 8, clay[1])
    for (x, y, c) in ((5, 3, 0), (8, 2, 1), (11, 3, 0), (7, 4, 1), (10, 5, 0)):
        img.set(x, y, flower[c])
        img.set(x, y + 1, flower[1 - c])
    img.line(8, 4, 8, 6, clay[0])
    return img.outline(out)


def lamp_floor(metal, shade, out):
    img = Img(16, 32)
    img.vline(8, 10, 29, metal[1])
    img.rect(5, 29, 11, 30, metal[0])
    for y in range(2, 11):
        half = 3 + (y - 2) * 0.5
        img.hline(int(8 - half), int(8 + half), y, shade[1] if y < 9 else shade[0])
    img.hline(5, 11, 2, shade[2])
    return img.outline(out)


def piano(wood, keys, out, w=32, h=32):
    img = Img(w, h)
    box(img, 2, 2, w - 3, h - 8, 12, wood, wood)
    img.rect(3, 14, w - 4, 17, keys[1])
    for x in range(4, w - 4, 3):
        img.rect(x, 14, x, 15, keys[0])
    for x in (4, w - 6):
        img.rect(x, h - 8, x + 1, h - 3, wood[0])
    return img.outline(out)


def barrel_in(wood, band, out):
    from props import barrel
    return barrel(wood, band, out)


def sink(counter_c, metal, water, out):
    img = Img(16, 16)
    box(img, 1, 3, 14, 14, 5, counter_c, counter_c)
    img.rect(4, 4, 11, 7, metal[0])
    img.rect(5, 5, 10, 6, water)
    img.vline(8, 1, 3, metal[1])
    img.set(9, 1, metal[1])
    return img.outline(out)


def icebox(body, out, handle):
    img = Img(16, 32)
    box(img, 2, 1, 13, 30, 24, body, body)
    img.hline(3, 12, 14, body[0])
    img.vline(11, 9, 12, handle)
    img.vline(11, 17, 22, handle)
    return img.outline(out)


def globe(wood, sea, land, out):
    img = Img(16, 16)
    img.ellipse(8, 6.5, 5, 5, sea[1])
    img.ellipse(7, 5.5, 2.5, 2, land[1])
    img.ellipse(10, 8.5, 1.8, 1.5, land[0])
    img.set(6, 4, sea[2])
    img.vline(8, 11, 13, wood[1])
    img.rect(5, 13, 11, 14, wood[0])
    return img.outline(out)


def aquarium(glass, water, fish, stand, out, w=32, h=32):
    img = Img(w, h)
    img.rect(2, 4, w - 3, 20, glass)
    img.rect(3, 6, w - 4, 19, water[1])
    img.hline(3, w - 4, 6, water[2])
    img.rect(3, 17, w - 4, 19, water[0])
    for (x, y) in ((8, 10), (18, 13), (23, 9)):
        img.rect(x, y, x + 2, y + 1, fish)
        img.set(x - 1, y, fish)
    box(img, 2, 21, w - 3, h - 2, 7, stand, stand)
    return img.outline(out)


def machine(metal, light, out, frame=0, w=32, h=32):
    """Workshop apparatus: coils, dials and a blinking light (2x2)."""
    img = Img(w, h)
    box(img, 2, 8, w - 3, h - 2, 12, metal, metal)
    for x in range(6, w - 6, 3):
        img.vline(x, 3, 8, metal[1])
        img.set(x, 2, metal[2])
    img.ellipse(10, 20, 3, 3, metal[0])
    img.ellipse(10, 20, 2, 2, metal[2])
    img.line(10, 20, 11, 18, metal[0])
    img.rect(18, 17, 26, 22, metal[0])
    img.rect(19, 18, 25, 21, light[frame % 2])
    return img.outline(out)
