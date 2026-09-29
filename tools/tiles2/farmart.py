"""Farm art: soil, crops (growth stages), barns, silos, windmills,
greenhouses, coops, beehives, hay, scarecrows."""

import math

from core import Img, hash32, rnd
from paint import stamp, scatter, clump_crown
import terrain as T


def soil(S, seed=0, wet=False, w=16, h=16):
    """Tilled soil: furrow ridges running east-west (lit tops, dark
    troughs). S: [dark, mid, base, light]."""
    img = Img(w, h, S[2])
    for y in range(h):
        k = y % 4
        for x in range(w):
            c = S[3] if k == 0 else (S[2] if k in (1, 2) else S[1])
            if k == 3 and (x + y // 4 * 3 + seed) % 7 == 0:
                c = S[0]
            if k == 0 and hash32(x, y // 4, seed) % 9 == 0:
                c = S[2]
            img.p[y][x] = c
    return img


def crop(kind, stage, P):
    """A 16x16 crop sprite (transparent) at growth stage 0..3.
    P: role dict with keys leaf (4 dark->light), and fruit ramps per kind."""
    img = Img(16, 16)
    L = P['leaf']
    if stage == 0:
        # seeds / tiny sprouts in the furrow
        for (x, y) in ((4, 7), (11, 7), (7, 11)):
            img.set(x, y, L[2])
            img.set(x + 1, y - 1, L[3])
            img.set(x - 1, y - 1, L[2])
        return img
    if kind == 'wheat':
        n = [0, 3, 5, 7][stage]
        top = [0, 9, 5, 2][stage]
        head = P['gold'] if stage == 3 else L
        for i in range(n):
            x = 2 + i * 12 // max(1, n - 1) if n > 1 else 8
            lean = (i % 3) - 1
            for y in range(top, 15):
                img.set(x + (lean if y < top + 3 else 0), y, L[1] if y > 11 else L[2])
            if stage >= 2:
                for y in range(top, top + 4):
                    img.set(x + lean, y, head[2] if y % 2 else head[3])
                    img.set(x + lean + 1, y + 1, head[1])
        return img.outline(P['out']) if stage == 3 else img
    if kind == 'corn':
        # 1x1 sprite; mature corn is tall and leafy
        top = [0, 8, 3, 0][stage]
        img.rect(7, top, 8, 15, L[1])
        img.vline(7, top, 15, L[2])
        for y in range(top + 2, 15, 3):
            img.line(8, y, 13, y - 3, L[2])
            img.line(7, y + 1, 2, y - 2, L[3])
        if stage == 3:
            img.rect(9, 5, 10, 9, P['gold'][2])
            img.set(9, 5, P['gold'][3])
            img.vline(10, 5, 9, P['gold'][1])
            img.set(9, 4, L[3])
        return img.outline(P['out'])
    if kind == 'pumpkin':
        cl = [(8, 9, 4.5), (5, 8, 3), (11, 8, 3)]
        if stage >= 1:
            leaves = clump_crown(16, 16, [(8, 9, 3 + stage), (5, 7, 2 + stage * 0.5), (11, 7, 2 + stage * 0.5)],
                                 L, None, speck=False, gdark=0.3)
            img.paste(leaves, 0, 0)
        if stage == 3:
            O = P['orange']
            img.ellipse(8, 10.5, 5.5, 4, O[1])
            img.ellipse(7.3, 10, 4, 3, O[2])
            img.vline(6, 7, 14, O[1])
            img.vline(10, 7, 14, O[1])
            img.set(5, 8, O[3])
            img.rect(7, 5, 8, 6, L[1])
        return img.outline(P['out'])
    if kind in ('turnip', 'carrot', 'beet'):
        R = P['root'][kind]
        h = [0, 5, 8, 10][stage]
        for i, dx in enumerate((-3, -1, 1, 3)):
            for t in range(h):
                x = 8 + int(dx * t / max(1, h))
                y = 10 - t
                img.set(x, y, L[2] if t < h - 1 else L[3])
                if t > 2 and i % 2:
                    img.set(x + 1, y, L[1])
        if stage == 3:
            img.ellipse(8, 12, 3.5, 2.8, R[1])
            img.ellipse(7.4, 11.5, 2.2, 1.6, R[2])
            img.set(8, 15, R[0])
        return img.outline(P['out'])
    if kind == 'tomato':
        # staked vine
        top = [0, 8, 4, 2][stage]
        img.vline(8, top, 15, P['stake'][1])
        img.vline(9, top, 15, P['stake'][0])
        cl = [(8, top + 3, 3.5), (6, top + 7, 3), (11, top + 8, 3)] if stage > 1 else [(8, 11, 3)]
        leaves = clump_crown(16, 16, cl, L, None, speck=False, gdark=0.3)
        img.paste(leaves, 0, 0)
        if stage == 3:
            Rr = P['red']
            for (x, y) in ((5, 8), (10, 6), (11, 11), (6, 12)):
                img.set(x, y, Rr[2])
                img.set(x + 1, y, Rr[1])
                img.set(x, y + 1, Rr[1])
                img.set(x + 1, y + 1, Rr[0])
        return img.outline(P['out'])
    if kind == 'glowcap':
        G = P['glow']
        n = [0, 1, 2, 3][stage]
        for i in range(n):
            x, y = [(8, 8), (4, 11), (12, 11)][i]
            s = 1 if (i == 0 and stage == 3) else 0
            img.rect(x, y + 1, x, y + 4, G[0])
            img.rect(x - 2 - s, y - 1, x + 2 + s, y, G[1])
            img.rect(x - 1 - s, y - 2, x + 1 + s, y - 2, G[2])
            img.set(x - 1, y - 1, G[3])
        return img.outline(P['out'])
    if kind == 'sunflower':
        top = [0, 9, 5, 1][stage]
        img.vline(8, top + 3, 15, L[1])
        img.set(7, top + 7, L[2])
        img.set(6, top + 7, L[3])
        img.set(9, top + 9, L[2])
        img.set(10, top + 9, L[3])
        if stage >= 2:
            Y = P['gold']
            r = 3 if stage == 3 else 2
            img.ellipse(8.5, top + 2.5, r + 1.3, r + 1.3, Y[2])
            img.ellipse(8.5, top + 2.5, r - 0.8, r - 0.8, P['stake'][0])
            img.set(9, top + 2, P['stake'][1])
        return img.outline(P['out'])
    raise ValueError(kind)


def barn(w, h, walls, trim, roof, out, door_wood, glass):
    """Big red barn: gambrel roof, white trim, X-braced double door."""
    img = Img(w, h)
    rh = int(h * 0.5)
    cx = w / 2
    # gambrel roof: steep lower slopes, shallow upper
    for y in range(0, rh + 1):
        if y < rh * 0.4:
            half = w * 0.18 + y * (w * 0.2) / (rh * 0.4)
        else:
            half = w * 0.38 + (y - rh * 0.4) * (w * 0.12) / (rh * 0.6)
        for x in range(int(cx - half), int(cx + half)):
            edge = min(x - (cx - half), (cx + half) - x)
            row = y % 4
            k = 3 if x < cx else 1
            if row == 3:
                k -= 1
            c = roof[k] if edge > 1 else roof[0]
            img.set(x, y, c)
    # walls with vertical boards
    for y in range(rh, h - 1):
        for x in range(2, w - 2):
            c = walls[1] if (x % 4) else walls[0]
            if x % 4 == 1:
                c = walls[2]
            img.set(x, y, c)
    img.hline(2, w - 3, rh, roof[0])
    img.hline(2, w - 3, rh + 1, walls[0])
    for x in (2, 3, w - 4, w - 3):
        img.vline(x, rh, h - 2, trim[1] if x in (2, w - 4) else trim[0])
    # hay loft door
    lx, ly = int(cx) - 5, 6
    img.rect(lx, ly, lx + 9, ly + 8, trim[1])
    img.rect(lx + 1, ly + 1, lx + 8, ly + 7, door_wood[0])
    img.line(lx + 1, ly + 1, lx + 8, ly + 7, trim[1])
    img.line(lx + 8, ly + 1, lx + 1, ly + 7, trim[1])
    # big door
    dw, dh = 24, 22
    dx, dy = int(cx - dw / 2), h - 1 - dh
    img.rect(dx - 1, dy - 1, dx + dw, h - 2, trim[1])
    for half in (0, 1):
        x0 = dx + half * dw // 2
        x1 = x0 + dw // 2 - 1
        img.rect(x0, dy, x1, h - 2, walls[1])
        for x in range(x0, x1 + 1, 3):
            img.vline(x, dy, h - 2, walls[0])
        img.rect(x0, dy, x1, dy, trim[1])
        img.rect(x0, h - 2, x1, h - 2, trim[1])
        img.vline(x0, dy, h - 2, trim[1])
        img.vline(x1, dy, h - 2, trim[1])
        img.line(x0, dy, x1, h - 2, trim[1])
        img.line(x1, dy, x0, h - 2, trim[1])
    # side windows
    for wx in (8, w - 18):
        img.rect(wx, rh + 6, wx + 9, rh + 13, trim[1])
        img.rect(wx + 1, rh + 7, wx + 8, rh + 12, glass[1])
        img.set(wx + 7, rh + 8, glass[2])
        img.vline(wx + 5, rh + 7, rh + 12, trim[1])
    return img.outline(out)


def silo(body, cap, out, w=32, h=64):
    img = Img(w, h)
    for y in range(8, h - 2):
        for x in range(3, w - 3):
            u = (x - 3) / (w - 7)
            k = 3 if u < 0.2 else (2 if u < 0.55 else (1 if u < 0.85 else 0))
            c = body[k]
            if (y - 8) % 8 == 7:
                c = body[max(0, k - 1)]
            img.set(x, y, c)
    img.ellipse(w / 2, 9, w / 2 - 3, 8, cap[1])
    img.ellipse(w / 2 - 2, 7, w / 2 - 7, 5, cap[2])
    img.rect(w / 2 - 1, 0, w / 2, 2, cap[0])
    img.vline(int(w / 2) + 2, 16, h - 4, body[0])
    for y in range(16, h - 4, 3):
        img.hline(int(w / 2) + 1, int(w / 2) + 3, y, body[0])
    return img.outline(out)


def windmill(body, roof, sail, out, frame, w=48, h=64):
    """Tower with rotating sails (4 frames)."""
    img = Img(w, h)
    cx = w / 2
    for y in range(20, h - 2):
        half = 9 + (y - 20) * 0.18
        for x in range(int(cx - half), int(cx + half)):
            u = (x - (cx - half)) / (2 * half)
            k = 2 if u < 0.3 else (1 if u < 0.75 else 0)
            img.set(x, y, body[k])
    for y in range(8, 22):
        half = 3 + (y - 8) * 0.55
        for x in range(int(cx - half), int(cx + half)):
            img.set(x, y, roof[2] if x < cx else roof[1])
    img.rect(cx - 3, h - 12, cx + 2, h - 3, body[0])
    img.rect(cx - 2, h - 11, cx + 1, h - 3, roof[0])
    img.rect(cx - 2, 32, cx + 1, 36, sail[0])
    hub = (cx, 18)
    a0 = frame * math.pi / 8
    for k in range(4):
        a = a0 + k * math.pi / 2
        for t in range(3, 21):
            x = hub[0] + math.cos(a) * t
            y = hub[1] + math.sin(a) * t
            img.set(int(x), int(y), sail[0])
            # the sail cloth on one side of each arm
            if t > 6:
                for s in range(1, 4):
                    xs = x + math.cos(a + math.pi / 2) * s
                    ys = y + math.sin(a + math.pi / 2) * s
                    img.set(int(round(xs)), int(round(ys)), sail[2] if (t + s) % 3 else sail[1])
    img.rect(int(hub[0]) - 1, int(hub[1]) - 1, int(hub[0]) + 1, int(hub[1]) + 1, sail[0])
    return img.outline(out)


def greenhouse(frame_c, glass, plants, out, w=64, h=48):
    img = Img(w, h)
    rh = 18
    for y in range(0, rh):
        half = w / 2 - 1 - (rh - y) * 0.2
        for x in range(int(w / 2 - half), int(w / 2 + half)):
            c = glass[2] if (x + y) % 9 < 2 else glass[1]
            if x % 8 == 0:
                c = frame_c[1]
            img.set(x, y, c)
    img.hline(2, w - 3, 0, frame_c[2])
    for y in range(rh, h - 1):
        for x in range(1, w - 1):
            c = glass[1] if (y - rh) < 10 else glass[0]
            if x % 8 == 0 or y == rh or y == h - 2:
                c = frame_c[1]
            img.set(x, y, c)
    # plants seen through the glass
    for i, x in enumerate(range(4, w - 4, 6)):
        P = plants[i % len(plants)]
        img.ellipse(x + 2, rh + 12, 2.5, 2.5, P[1])
        img.set(x + 1, rh + 11, P[2])
    img.rect(w / 2 - 5, h - 16, w / 2 + 4, h - 2, frame_c[0])
    img.rect(w / 2 - 4, h - 15, w / 2 + 3, h - 3, glass[0])
    img.vline(int(w / 2), h - 15, h - 3, frame_c[1])
    return img.outline(out)


def coop(wood, roof, out, straw):
    img = Img(32, 32)
    for y in range(0, 12):
        half = 5 + y * 0.9
        for x in range(int(16 - half), int(16 + half)):
            img.set(x, y, roof[2] if x < 16 else roof[1])
    img.hline(4, 27, 11, roof[0])
    for y in range(12, 27):
        for x in range(5, 27):
            img.set(x, y, wood[1] if (y % 3) else wood[0])
    img.rect(13, 17, 18, 26, wood[0])
    img.rect(14, 18, 17, 26, straw[0])
    # ramp and legs
    img.line(18, 27, 24, 30, wood[2])
    img.line(18, 28, 24, 31, wood[1])
    for x in (6, 25):
        img.rect(x, 27, x + 1, 30, wood[0])
    img.rect(7, 15, 10, 18, straw[1])
    return img.outline(out)


def beehive(wood, roof, out, bee):
    img = Img(16, 16)
    img.rect(3, 13, 12, 14, wood[0])
    for y in range(4, 13):
        for x in range(3, 13):
            img.set(x, y, wood[2] if (y % 3 == 0) else wood[1])
    img.hline(2, 13, 3, roof[1])
    img.hline(3, 12, 2, roof[2])
    img.rect(6, 11, 9, 12, wood[0])
    img.set(12, 6, bee)
    img.set(13, 5, bee)
    return img.outline(out)


def hay_round(hay, out):
    """Round bale lying on its side: a cylinder with the rolled face on the
    right. hay: [dark, base, light]."""
    img = Img(16, 16)
    img.rect(1, 4, 10, 14, hay[1])
    img.hline(1, 10, 4, hay[2])
    img.hline(1, 10, 5, hay[2])
    for x in range(2, 10, 3):
        img.vline(x, 7, 13, hay[0])
    img.ellipse(11, 9.5, 4, 5.5, hay[0])
    img.ellipse(11, 9.5, 3, 4.5, hay[1])
    img.ellipse(11, 9.5, 1.8, 2.8, hay[2])
    img.ellipse(11, 9.5, 0.8, 1.2, hay[0])
    img.hline(1, 10, 14, hay[0])
    return img.outline(out)


def hay_bale(hay, out, band):
    img = Img(32, 16)
    img.rect(2, 4, 29, 14, hay[1])
    img.rect(2, 4, 29, 6, hay[2])
    for x in range(3, 29, 2):
        img.set(x, 8 + (x % 3), hay[0])
    img.vline(10, 4, 14, band)
    img.vline(21, 4, 14, band)
    img.hline(2, 29, 14, hay[0])
    return img.outline(out)


def scarecrow(wood, cloth, hat, face, straw, out):
    img = Img(16, 32)
    img.vline(8, 8, 30, wood[1])
    img.vline(7, 8, 30, wood[2])
    img.hline(1, 14, 12, wood[1])
    img.rect(4, 11, 11, 20, cloth[1])
    img.vline(4, 11, 20, cloth[2])
    img.vline(11, 11, 20, cloth[0])
    img.set(2, 13, straw)
    img.set(13, 13, straw)
    img.set(1, 12, straw)
    img.set(14, 12, straw)
    img.ellipse(8, 7, 3.2, 3, face)
    img.set(7, 7, out)
    img.set(9, 7, out)
    img.rect(3, 3, 12, 4, hat[1])
    img.rect(5, 0, 10, 3, hat[1])
    img.hline(5, 10, 0, hat[2])
    return img.outline(out)


def pump(metal, out, water):
    img = Img(16, 16)
    img.rect(6, 4, 9, 14, metal[1])
    img.vline(6, 4, 14, metal[2])
    img.rect(9, 6, 12, 7, metal[1])
    img.set(12, 8, water)
    img.line(6, 3, 2, 1, metal[0])
    img.rect(4, 14, 11, 15, metal[0])
    return img.outline(out)


def shipping_bin(wood, lid, out):
    img = Img(32, 16)
    img.rect(2, 5, 29, 14, wood[1])
    img.rect(2, 3, 29, 6, lid[1])
    img.hline(2, 29, 3, lid[2])
    for x in range(6, 29, 6):
        img.vline(x, 7, 14, wood[0])
    img.hline(2, 29, 14, wood[0])
    return img.outline(out)
