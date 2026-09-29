"""Village and city furniture. Ramps are dark -> light role lists."""

import math

from core import Img, hash32, rnd
from paint import stamp, scatter, clump_crown
import terrain as T
from props import plank_fill, rock


def lamp_post(metal, out, glass, glow=None, h=32, lit=True):
    """Street lamp 1x2: head drawn above people (top cell)."""
    img = Img(16, h)
    img.rect(7, 10, 8, h - 3, metal[1])
    img.vline(7, 10, h - 3, metal[2])
    img.rect(5, h - 3, 10, h - 2, metal[1])
    img.hline(5, 10, h - 3, metal[2])
    # lantern head
    img.rect(4, 1, 11, 2, metal[1])
    img.hline(5, 10, 0, metal[2])
    img.rect(5, 3, 10, 8, glass[1] if lit else metal[0])
    img.vline(5, 3, 8, metal[1])
    img.vline(10, 3, 8, metal[1])
    img.vline(7, 3, 8, metal[0])
    if lit:
        img.set(6, 4, glass[2])
        img.set(6, 5, glass[2])
        img.set(8, 4, glass[2])
    img.rect(4, 9, 11, 9, metal[1])
    return img.outline(out)


def bench(wood, metal, out, w=32):
    img = Img(w, 16)
    for y in (4, 5):
        img.hline(2, w - 3, y, wood[2] if y == 4 else wood[1])
    for y in (8, 9, 10):
        img.hline(1, w - 2, y, wood[2] if y == 8 else wood[1])
    img.hline(1, w - 2, 11, wood[0])
    for x in (3, w - 4):
        img.rect(x, 3, x + 1, 14, metal[0])
        img.set(x, 3, metal[1])
    img.hline(2, w - 3, 6, metal[0])
    return img.outline(out)


def mailbox(box, box_dk, post, out, flag):
    img = Img(16, 16)
    img.rect(7, 9, 8, 15, post[1])
    img.vline(7, 9, 15, post[2])
    img.rect(3, 3, 12, 9, box)
    img.hline(4, 11, 2, box)
    img.rect(3, 8, 12, 9, box_dk)
    img.vline(12, 3, 9, box_dk)
    img.rect(5, 5, 9, 6, box_dk)
    img.rect(13, 2, 13, 6, flag)
    img.set(14, 2, flag)
    return img.outline(out)


def flower_pot(pot, out, leaf, petal, center, w=16):
    img = Img(16, 16)
    for y in range(9, 15):
        half = 5 - (y - 9) // 3
        for x in range(8 - half, 8 + half):
            u = (x - (8 - half)) / (2 * half)
            img.set(x, y, pot[2] if u < 0.3 else (pot[1] if u < 0.75 else pot[0]))
    img.hline(2, 13, 8, pot[2])
    img.hline(2, 13, 9, pot[0])
    cl = [(8, 6, 4), (5, 6, 3), (11, 6, 3), (8, 3, 3)]
    crown = clump_crown(16, 10, cl, leaf, None, speck=False, gdark=0.3)
    img.paste(crown, 0, 0)
    for (x, y) in ((6, 3), (10, 4), (8, 6), (4, 6)):
        img.set(x, y, petal)
        img.set(x + 1, y, petal)
        img.set(x, y + 1, petal)
        img.set(x + 1, y + 1, center)
    return img.outline(out)


def planter(wood, soil, leaf, petals, out, w=32):
    """Long wooden planter box with flowers (2x1)."""
    img = Img(w, 16)
    img.rect(1, 8, w - 2, 14, wood[1])
    img.hline(1, w - 2, 8, wood[2])
    img.hline(1, w - 2, 14, wood[0])
    for x in range(4, w - 3, 6):
        img.vline(x, 9, 13, wood[0])
    img.hline(2, w - 3, 7, soil)
    for i, x in enumerate(range(3, w - 3, 4)):
        p = petals[i % len(petals)]
        y = 3 + (i % 2)
        img.set(x, y + 2, leaf[1])
        img.set(x + 1, y + 3, leaf[0])
        img.set(x - 1, y + 3, leaf[1])
        img.set(x, y, p)
        img.set(x + 1, y, p)
        img.set(x, y + 1, p)
        img.set(x + 1, y + 1, leaf[2])
    return img.outline(out)


def fountain(stone, water, out, frame, w=48, h=48):
    """3x3 fountain: round basin, central pillar, animated jets."""
    img = Img(w, h)
    cx, cy = w / 2, h * 0.6
    img.ellipse(cx, cy + 2, w / 2 - 1, h * 0.32, stone[0])
    img.ellipse(cx, cy, w / 2 - 1, h * 0.3, stone[2])
    img.ellipse(cx, cy - 1, w / 2 - 2, h * 0.28 - 1, stone[3])
    img.ellipse(cx, cy, w / 2 - 5, h * 0.22, water[0])
    img.ellipse(cx, cy + 0.6, w / 2 - 6, h * 0.2, water[1])
    # ripples
    for i in range(3):
        r = 5 + ((frame * 2 + i * 5) % 14)
        for a in range(0, 360, 12):
            x = cx + math.cos(math.radians(a)) * r
            y = cy + math.sin(math.radians(a)) * r * 0.62
            if img.get(int(x), int(y)) == water[1]:
                img.set(int(x), int(y), water[2])
    # pillar
    img.rect(int(cx) - 3, int(cy) - 14, int(cx) + 2, int(cy) + 2, stone[2])
    img.vline(int(cx) - 3, int(cy) - 14, int(cy) + 2, stone[3])
    img.vline(int(cx) + 2, int(cy) - 14, int(cy) + 2, stone[1])
    img.ellipse(cx, cy - 15, 6, 2.2, stone[3])
    img.ellipse(cx, cy - 15, 4, 1.2, water[1])
    # jets
    for side in (-1, 1):
        for t in range(10):
            x = cx + side * (1 + t * 0.9)
            y = cy - 17 - 3 * math.sin(t / 9 * math.pi) + t * 1.2
            if (t + frame) % 3 != 0:
                img.set(int(x), int(y), water[2] if t % 2 else water[3])
    img.set(int(cx), int(cy) - 19 + (frame % 2), water[3])
    img.set(int(cx) - 1, int(cy) - 18, water[3])
    return img.outline(out)


def well(stone, wood, water, out, roof):
    img = Img(32, 32)
    img.ellipse(16, 23, 12, 6.5, stone[0])
    img.ellipse(16, 22, 12, 6, stone[2])
    img.ellipse(16, 21.5, 9, 4, stone[0])
    img.ellipse(16, 22, 8, 3.2, water[1])
    for x in range(4, 29):
        if (x // 3) % 2 == 0:
            img.set(x, 25, stone[1])
    for x in (5, 26):
        img.rect(x, 6, x + 1, 22, wood[1])
        img.vline(x, 6, 22, wood[2])
    img.hline(6, 25, 10, wood[0])
    img.rect(14, 10, 17, 14, wood[1])
    img.set(15, 15, stone[1])
    # small roof
    for y in range(0, 7):
        half = 6 + y * 1.7
        for x in range(int(16 - half), int(16 + half)):
            img.set(x, y, roof[3] if x < 16 else roof[1])
    img.hline(3, 28, 6, roof[0])
    return img.outline(out)


def market_stall(wood, cloth, goods, out, w=48, h=32):
    """Stall with striped awning and produce crates (3x2)."""
    img = Img(w, h)
    # awning
    for y in range(2, 10):
        for x in range(1, w - 1):
            stripe = (x // 4) % 2
            c = cloth[2] if stripe else cloth[1]
            if y >= 8:
                c = cloth[0] if stripe else cloth[1]
            img.set(x, y, c)
    for x in range(1, w - 1, 4):
        img.set(x + 1, 10, cloth[1])
        img.set(x + 2, 10, cloth[1])
    img.hline(1, w - 2, 1, cloth[2])
    # posts
    for x in (3, w - 5):
        img.rect(x, 10, x + 1, h - 2, wood[1])
    # counter
    img.rect(2, 18, w - 3, h - 3, wood[1])
    img.hline(2, w - 3, 18, wood[2])
    img.hline(2, w - 3, h - 3, wood[0])
    for x in range(6, w - 4, 8):
        img.vline(x, 19, h - 4, wood[0])
    # goods on the counter
    for i, x in enumerate(range(5, w - 6, 5)):
        g = goods[i % len(goods)]
        img.rect(x, 15, x + 3, 17, g[1])
        img.hline(x, x + 3, 15, g[2])
        img.set(x + 1, 16, g[2])
        img.set(x + 3, 17, g[0])
    return img.outline(out)


def sacks(cloth, out, tie):
    img = Img(16, 16)
    for (x, y, rx, ry) in ((5, 10, 4, 4.5), (11, 11, 4, 4)):
        img.ellipse(x, y, rx, ry, cloth[1])
        img.ellipse(x - 1, y - 1, rx - 1.5, ry - 1.5, cloth[2])
        img.set(int(x), int(y - ry), tie)
        img.set(int(x), int(y - ry) + 1, tie)
    return img.outline(out)


def woodpile(wood, cut, out):
    img = Img(32, 16)
    for row in range(3):
        for i in range(6 - row):
            x = 3 + i * 5 + row * 2.5
            y = 12 - row * 4
            img.ellipse(x, y, 2.6, 2.3, wood[1])
            img.ellipse(x - 0.4, y - 0.3, 1.6, 1.4, cut[1])
            img.set(int(x) - 1, int(y) - 1, cut[2])
    return img.outline(out)


def clothesline(pole, rope, cloths, out, w=48):
    img = Img(w, 32)
    for x in (2, w - 3):
        img.rect(x, 4, x + 1, 30, pole[1])
        img.set(x, 4, pole[2])
    for x in range(3, w - 3):
        sag = int(2 * math.sin((x - 3) / (w - 6) * math.pi))
        img.set(x, 7 + sag, rope)
    items = [(7, 10, 8), (19, 9, 10), (32, 8, 8)]
    for i, (x, ww, hh) in enumerate(items):
        c = cloths[i % len(cloths)]
        sag = int(2 * math.sin((x + ww / 2 - 3) / (w - 6) * math.pi))
        y0 = 8 + sag
        img.rect(x, y0, x + ww - 1, y0 + hh, c[1])
        img.hline(x, x + ww - 1, y0, c[2])
        img.vline(x + ww - 1, y0, y0 + hh, c[0])
        img.hline(x, x + ww - 1, y0 + hh, c[0])
    return img.outline(out)


def waterwheel(wood, water, out, frame, size=32):
    img = Img(size, size + 16)
    cx, cy, R = size / 2, size / 2 + 2, size / 2 - 2
    img.ellipse(cx, cy, R, R, wood[0])
    img.ellipse(cx, cy, R - 2, R - 2, None)
    for y in range(size + 16):
        for x in range(size):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if R - 2.2 < d <= R:
                img.set(x, y, wood[1] if x < cx else wood[0])
    ang0 = frame * math.pi / 16
    for k in range(8):
        a = ang0 + k * math.pi / 4
        for t in range(2, int(R)):
            img.set(int(cx + math.cos(a) * t), int(cy + math.sin(a) * t), wood[2] if k % 2 else wood[1])
        px, py = cx + math.cos(a) * (R + 1), cy + math.sin(a) * (R + 1)
        img.rect(int(px) - 1, int(py) - 1, int(px) + 1, int(py) + 1, wood[2])
    img.ellipse(cx, cy, 2.5, 2.5, wood[0])
    # splash at the bottom
    for x in range(4, size - 4):
        if (x + frame) % 3:
            img.set(x, size + 6 + (x + frame) % 2, water[2])
            img.set(x, size + 7, water[1])
    return img.outline(out)


KIN_STATUE = """
.....o..........o.......
....oho........odo......
....ohlo......olmdo.....
....ohllo....ollmdo.....
....olllooooollmmdo.....
.....olllllllllmmdo.....
....ollhhllllllmmmdo....
....olhlllllllllmmdo....
....ollodlllllodmmdo....
....ollllllhllllmmdo....
.....olllllllllmmdo.....
......ollloollmmdo......
.......ollllllmdo.......
......olllllllmmdo......
.....ollhlllllmmmdo.....
....ollhllllllmmmmdo....
....olhlllllllmmmmdo.ooo
...ollhllllllllmmmmdolmdo
...olllllllllllmmmmdolmdo
...ollllllllllllmmmmolldo
...olllllooolllmmmmmdlmo.
...ollllo...ollmmmmdlmdo.
....ooooo...oooooooooodo.
....................ooo..
"""


def statue(stone, out, plinth, kind='fox', h=48):
    """Creature statue on a plinth (2x3): an original fox-eared kin sitting
    with its tail curled round (hand-drawn, shaded with the stone ramp)."""
    from core import G
    img = Img(32, h)
    img.rect(3, h - 13, 28, h - 3, plinth[1])
    img.hline(3, 28, h - 13, plinth[2])
    img.hline(3, 28, h - 12, plinth[2])
    img.rect(3, h - 4, 28, h - 3, plinth[0])
    img.vline(28, h - 13, h - 4, plinth[0])
    img.rect(10, h - 9, 21, h - 7, plinth[0])
    img.hline(11, 20, h - 8, plinth[1])
    body = G(KIN_STATUE, {'o': out, 'd': stone[0], 'm': stone[1], 'l': stone[2], 'h': stone[3]})
    img.paste(body, 4, h - 13 - body.h + 1)
    return img.outline(out)


def bell_tower(stone, wood, roof, bell, out, w=32, h=64):
    """Mistbell's signal bell tower (2x4)."""
    img = Img(w, h)
    for y in range(20, h - 2):
        for x in range(4, w - 4):
            row = (y - 20) // 4
            c = stone[1]
            if (y - 20) % 4 == 3 or (x + (row % 2) * 3) % 6 == 0:
                c = stone[0]
            elif (y - 20) % 4 == 0:
                c = stone[2]
            img.set(x, y, c)
    # bell opening
    img.rect(9, 22, w - 10, 36, wood[0])
    img.ellipse(w / 2, 24, (w - 20) / 2, 3, wood[0])
    img.rect(w / 2 - 4, 27, w / 2 + 3, 33, bell[1])
    img.ellipse(w / 2, 27, 4, 3, bell[1])
    img.hline(int(w / 2) - 5, int(w / 2) + 4, 34, bell[0])
    img.vline(int(w / 2) - 3, 25, 32, bell[2])
    # roof
    for y in range(0, 20):
        half = 3 + y * 0.72
        for x in range(int(w / 2 - half), int(w / 2 + half)):
            img.set(x, y, roof[3] if x < w / 2 else roof[1])
    img.hline(1, w - 2, 19, roof[0])
    img.hline(2, w - 3, 18, roof[1])
    img.rect(int(w / 2) - 1, 0, int(w / 2), 2, roof[3])
    # door
    img.rect(12, h - 14, w - 13, h - 3, wood[1])
    img.vline(12, h - 14, h - 3, wood[2])
    return img.outline(out)


def stone_wall(stone, out, cap=None, moss=None):
    """Dry-stone wall as a patch9 block (80x48): chunky stones, capstones
    lit on top, dark base; transparent where the wall ends."""
    def cell(mask, W, H):
        img = Img(W, H)
        tex = T.lump_texture(stone, 16, 16, 3, rx=3.8, ry=2.8, sx=5.3, sy=4, bias=-0.05)
        for y in range(H):
            for x in range(W):
                cx, cy = x // 16, y // 16
                if not mask(cx, cy):
                    continue
                lx, ly = x % 16, y % 16
                # walls are narrower than a cell on the open sides
                if not mask(cx, cy - 1) and ly < 3:
                    continue
                if not mask(cx - 1, cy) and lx < 2:
                    continue
                if not mask(cx + 1, cy) and lx > 13:
                    continue
                img.p[y][x] = tex.p[ly][lx]
                if not mask(cx, cy - 1) and ly == 3:
                    img.p[y][x] = cap or stone[-1]
                if not mask(cx, cy + 1) and ly >= 14:
                    img.p[y][x] = stone[0]
        return img.outline(out)
    from flora import shape_patch9
    return shape_patch9(cell)


def barrel_planter(wood, band, soil, leaf, out):
    img = Img(16, 16)
    for y in range(7, 15):
        for x in range(3, 13):
            u = (x - 3) / 9
            img.set(x, y, wood[2] if u < 0.3 else (wood[1] if u < 0.8 else wood[0]))
    img.hline(3, 12, 9, band)
    img.hline(3, 12, 13, band)
    img.ellipse(8, 6.5, 5, 1.8, soil)
    crown = clump_crown(16, 9, [(8, 4, 4), (5, 5, 3), (11, 5, 3)], leaf, None, speck=False, gdark=0.3)
    img.paste(crown, 0, 0)
    return img.outline(out)


def cart(wood, wheel, out, load=None):
    img = Img(32, 16)
    img.rect(3, 3, 26, 9, wood[1])
    img.hline(3, 26, 3, wood[2])
    img.hline(3, 26, 9, wood[0])
    for x in range(7, 26, 5):
        img.vline(x, 4, 8, wood[0])
    img.hline(26, 31, 7, wood[1])
    for cx in (8, 21):
        img.ellipse(cx, 11.5, 3.6, 3.6, wheel[0])
        img.ellipse(cx, 11.5, 2.2, 2.2, wheel[1])
        img.set(cx, 11, wheel[0])
    if load:
        for i, x in enumerate(range(5, 25, 4)):
            c = load[i % len(load)]
            img.ellipse(x + 1.5, 2.5, 2.2, 2, c[1])
            img.set(x + 1, 1, c[2])
    return img.outline(out)


def trough(wood, water, out):
    img = Img(32, 16)
    img.rect(2, 5, 29, 12, wood[1])
    img.hline(2, 29, 5, wood[2])
    img.rect(4, 6, 27, 8, water[1])
    img.hline(4, 27, 6, water[2])
    img.hline(2, 29, 12, wood[0])
    for x in (4, 27):
        img.rect(x, 13, x + 1, 14, wood[0])
    return img.outline(out)


def bunting(rope, flags, out, w=48):
    img = Img(w, 16)
    for x in range(w):
        y = 2 + int(3 * math.sin(x / (w - 1) * math.pi))
        img.set(x, y, rope)
        if x % 6 == 2:
            c = flags[(x // 6) % len(flags)]
            img.set(x, y + 1, c)
            img.set(x + 1, y + 1, c)
            img.set(x + 2, y + 1, c)
            img.set(x + 1, y + 2, c)
            img.set(x + 1, y + 3, c)
    return img


def street_sign(metal, plate, ink, out):
    img = Img(16, 32)
    img.rect(7, 8, 8, 30, metal[1])
    img.vline(7, 8, 30, metal[2])
    img.rect(1, 3, 14, 9, plate[1])
    img.hline(1, 14, 3, plate[2])
    img.hline(1, 14, 9, plate[0])
    for x in range(3, 13, 2):
        img.set(x, 6, ink)
    return img.outline(out)


def weather_vane(metal, out, accent):
    img = Img(16, 32)
    img.vline(8, 4, 30, metal[1])
    img.hline(3, 13, 8, metal[1])
    img.draw('''
    .aaa....
    aaaaaaa.
    .aaa..a.
    ''', {'a': accent}, 4, 3)
    img.set(3, 8, metal[2])
    img.set(13, 8, metal[2])
    img.rect(6, 29, 10, 30, metal[0])
    return img.outline(out)


def garden_arch(wood, leaf, flower, out):
    img = Img(32, 32)
    for x in (3, 27):
        img.rect(x, 6, x + 1, 30, wood[1])
        img.vline(x, 6, 30, wood[2])
    for x in range(3, 29):
        y = 6 - int(4 * math.sin((x - 3) / 25 * math.pi))
        img.rect(x, y, x, y + 1, wood[1])
    cl = []
    for i in range(9):
        t = i / 8
        x = 3 + t * 25
        y = 6 - 4 * math.sin(t * math.pi)
        cl.append((x + 1, y + 1, 3.2))
    for y in (12, 18, 24):
        cl.append((4, y, 2.8))
        cl.append((28, y + 2, 2.8))
    crown = clump_crown(32, 32, cl, leaf, None, speck=False, gdark=0.2)
    img.paste(crown, 0, 0)
    for (x, y) in ((6, 3), (14, 1), (22, 2), (27, 9), (3, 15), (28, 21)):
        img.set(x, y, flower[0])
        img.set(x + 1, y, flower[1])
        img.set(x, y + 1, flower[1])
    return img.outline(out)
