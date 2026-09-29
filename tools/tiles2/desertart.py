"""Desert art: dune ripples, cacti, tumbleweed, skulls, adobe houses,
canopies, jars, sandstone ruins and obelisks."""

import math

from core import Img, hash32, rnd
from paint import stamp, scatter, clump_crown


def dunes(S, seed=0, w=16, h=16):
    """Wind ripples: curved light crests with shadowed troughs.
    S = [dark, mid, base, light, hi]."""
    img = Img(w, h, S[2])
    for k in range(3):
        y0 = 2 + k * 5 + (seed % 2)
        for x in range(w):
            y = int(round(y0 + 1.2 * math.sin((x + seed * 3 + k * 5) * math.tau / w)))
            img.p[y % h][x] = S[3]
            img.p[(y + 1) % h][x] = S[1]
            if (x + k) % 6 == 0:
                img.p[(y - 1) % h][x] = S[4]
    return img


def saguaro(G, out, spines, flower=None, w=16, h=32):
    """Column cactus with two arms (1x2)."""
    img = Img(w, h)

    def col(x0, x1, y0, y1):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                u = (x - x0) / max(1, x1 - x0)
                img.set(x, y, G[3] if u < 0.25 else (G[2] if u < 0.6 else (G[1] if u < 0.9 else G[0])))
        for x in range(x0, x1 + 1):
            img.set(x, y0, G[3] if x < (x0 + x1) / 2 + 1 else G[2])
    col(6, 10, 3, h - 2)
    col(1, 3, 10, 18)
    img.rect(3, 17, 6, 19, G[2])
    col(13, 15, 7, 15)
    img.rect(10, 14, 13, 16, G[2])
    for y in range(6, h - 3, 3):
        img.set(8, y, G[0])
        img.set(5 if y % 2 else 11, y, spines)
    if flower:
        img.set(8, 2, flower[0])
        img.set(7, 2, flower[1])
        img.set(9, 2, flower[1])
    return img.outline(out)


def barrel_cactus(G, out, spines, flower=None):
    img = Img(16, 16)
    img.ellipse(8, 10, 5.5, 5, G[1])
    img.ellipse(7, 9, 4, 3.5, G[2])
    for x in (5, 8, 11):
        img.vline(x, 6, 14, G[0])
    img.set(6, 7, G[3])
    for (x, y) in ((4, 8), (12, 9), (8, 5), (6, 12)):
        img.set(x, y, spines)
    if flower:
        img.rect(7, 4, 9, 5, flower[0])
        img.set(8, 4, flower[1])
    return img.outline(out)


def prickly_pear(G, out, fruit):
    img = Img(16, 16)
    pads = [(8, 11, 4, 3.4), (5, 6, 3, 2.6), (11, 5, 2.8, 2.4)]
    body = clump_crown(16, 16, pads, G, None, speck=False, gdark=0.3, rim=0.9)
    img.paste(body, 0, 0)
    for (x, y) in ((4, 3), (11, 2), (13, 4)):
        img.set(x, y, fruit)
    return img.outline(out)


def tumbleweed(C, out):
    img = Img(16, 16)
    for a in range(0, 360, 20):
        for r in (3, 5):
            x = 8 + math.cos(math.radians(a + r * 7)) * r
            y = 9 + math.sin(math.radians(a + r * 7)) * r * 0.85
            img.set(int(x), int(y), C[1] if r == 5 else C[2])
    for i in range(10):
        a = i * 0.9
        img.line(8, 9, int(8 + math.cos(a) * 5), int(9 + math.sin(a) * 4), C[0])
    return img.outline(out)


def skull(B, out):
    img = Img(16, 16)
    img.draw('''
    ....bbbbb.......
    ...bhhhhbb......
    ..bhhhhhhbb.....
    ..bhddhddhb.....
    ..bhddhddhb.....
    ...bhhdhhb......
    ....bhbhb.......
    ................
    ''', {'b': B[1], 'h': B[2], 'd': B[0]}, 2, 4)
    img.line(9, 12, 13, 14, B[1])
    return img.outline(out)


def adobe(w, h, wall, beam, trim, glass, out, door_at=None, windows=(), dome=False, parapet=True, awning=None):
    """Flat-roofed mud-brick house: rounded corners, parapet, protruding
    roof beams, deep-set windows, arched door."""
    img = Img(w, h)
    roof_h = 10 if not dome else 14
    top = 2
    # body
    for y in range(roof_h, h - 1):
        for x in range(1, w - 1):
            c = wall[2]
            if x < 3:
                c = wall[3] if len(wall) > 3 else wall[2]
            if x > w - 4:
                c = wall[1]
            if hash32(x % 16, y % 16, 5) % 17 == 0:
                c = wall[1]
            img.set(x, y, c)
    for (x, y) in ((1, h - 2), (w - 2, h - 2)):
        img.set(x, y, None)
    # roof slab seen from above
    for y in range(top, roof_h):
        for x in range(1, w - 1):
            c = wall[3] if len(wall) > 3 else wall[2]
            if parapet and (y == top or x in (1, 2, w - 2, w - 3)):
                c = wall[2]
            if parapet and y == top + 1 and 2 < x < w - 3:
                c = wall[1]
            img.set(x, y, c)
    img.hline(1, w - 2, roof_h, wall[0])
    img.hline(1, w - 2, roof_h + 1, wall[1])
    if dome:
        cx = w / 2
        img.ellipse(cx, roof_h - 2, w * 0.28, 7, wall[2])
        img.ellipse(cx - 2, roof_h - 4, w * 0.16, 4, wall[3] if len(wall) > 3 else wall[2])
    # vigas (beam ends)
    for x in range(6, w - 5, 8):
        img.rect(x, roof_h + 1, x + 1, roof_h + 2, beam[1])
        img.set(x, roof_h + 3, beam[0])
    # windows: deep-set, dark
    for (wx, wy) in windows:
        img.rect(wx, roof_h + wy, wx + 7, roof_h + wy + 6, wall[0])
        img.rect(wx + 1, roof_h + wy + 1, wx + 6, roof_h + wy + 6, glass[0])
        img.hline(wx + 1, wx + 6, roof_h + wy + 1, glass[1])
        img.hline(wx, wx + 7, roof_h + wy + 7, wall[3] if len(wall) > 3 else wall[2])
    if awning:
        ax0, ax1, A = awning
        ay = roof_h + 3
        for x in range(ax0, ax1 + 1):
            for y in range(ay, ay + 4):
                img.set(x, y, A[1] if ((x - ax0) // 3) % 2 else A[2])
            img.set(x, ay + 4, A[0])
    if door_at is not None:
        dw, dh = 10, 15
        dx, dy = int(door_at - dw / 2), h - 1 - dh
        img.rect(dx - 1, dy - 1, dx + dw, h - 2, wall[0])
        img.rect(dx, dy + 2, dx + dw - 1, h - 2, trim[1])
        img.hline(dx + 2, dx + dw - 3, dy, trim[1])
        img.hline(dx + 1, dx + dw - 2, dy + 1, trim[1])
        for x in range(dx + 1, dx + dw - 1, 3):
            img.vline(x, dy + 2, h - 2, trim[0])
        img.hline(dx - 1, dx + dw, h - 1, wall[1])
    return img.outline(out)


def canopy(cloth, pole, out, w=48, h=32):
    img = Img(w, h)
    for x in (2, w - 4):
        img.rect(x, 8, x + 1, h - 2, pole[1])
        img.vline(x, 8, h - 2, pole[2])
    for y in range(4, 12):
        sag = 0
        for x in range(1, w - 1):
            sag = int(2 * math.sin((x - 1) / (w - 2) * math.pi))
            stripe = (x // 6) % 2
            c = cloth[2] if stripe else cloth[1]
            if y == 11:
                c = cloth[0]
            img.set(x, y + sag - 2, c)
    for x in range(1, w - 1, 6):
        img.set(x + 2, 11 + int(2 * math.sin((x - 1) / (w - 2) * math.pi)), cloth[1])
    return img.outline(out)


def jars(clay, out, band):
    img = Img(16, 16)
    for (cx, cy, rx, ry) in ((5, 10, 3.6, 4.2), (11, 11, 3.2, 3.6)):
        img.ellipse(cx, cy, rx, ry, clay[1])
        img.ellipse(cx - 1, cy - 1, rx - 1.5, ry - 1.5, clay[2])
        img.rect(int(cx) - 1, int(cy - ry) - 1, int(cx) + 1, int(cy - ry), clay[1])
        img.hline(int(cx - rx) + 1, int(cx + rx) - 1, int(cy), band)
    return img.outline(out)


def pillar(stone, out, w=16, h=48, broken=False):
    img = Img(w, h)
    top = 8 if broken else 3
    for y in range(top, h - 5):
        for x in range(4, 12):
            u = (x - 4) / 7
            c = stone[3] if u < 0.25 else (stone[2] if u < 0.6 else (stone[1] if u < 0.9 else stone[0]))
            if x in (6, 9) and not u < 0.25:
                c = stone[1]
            img.set(x, y, c)
    img.rect(2, h - 5, 13, h - 2, stone[2])
    img.hline(2, 13, h - 5, stone[3])
    img.hline(2, 13, h - 2, stone[0])
    if broken:
        for x in range(4, 12):
            img.set(x, top + (hash32(x, 3) % 3), None)
    else:
        img.rect(2, 1, 13, 3, stone[2])
        img.hline(2, 13, 1, stone[3])
    return img.outline(out)


def obelisk(stone, out, glyph, w=16, h=48):
    img = Img(w, h)
    for y in range(3, h - 2):
        t = (y - 3) / (h - 5)
        half = 2 + t * 3.5
        for x in range(int(8 - half), int(8 + half) + 1):
            img.set(x, y, stone[3] if x < 8 else stone[1])
    for y in range(0, 4):
        img.hline(8 - y // 2, 8 + y // 2, y, stone[3])
    for y in range(12, h - 8, 5):
        img.set(7, y, glyph)
        img.set(8, y + 1, glyph)
        img.set(7, y + 2, glyph)
    img.rect(3, h - 3, 12, h - 2, stone[0])
    return img.outline(out)
