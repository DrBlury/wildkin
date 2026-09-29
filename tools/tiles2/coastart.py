"""Coast art: surf, palms, boats, lighthouse, stilt huts, coral, shells,
buoys, nets, anchors, lobster pots, driftwood, whale bones."""

import math

from core import Img, hash32, rnd
from paint import stamp, scatter, clump_crown
import terrain as T
from flora import trunk


def surf_autotile(W, sand, wet, frame, seed=0):
    """Sea over sand: shallow turquoise band, animated foam line that runs
    up the beach and back over 4 frames, damp sand band above it."""
    surf = T.water_surface(W, frame, seed)
    wob = T.wobble(seed + 2, 0.9)
    push = [0.0, 0.8, 1.4, 0.8][frame % 4]

    def color_at(d, X, Y, side, v, alt):
        if d < -2.2 - push * 0.5:
            return sand.p[Y][X]
        if d < -0.8 - push:
            return wet
        if d < 0.3 - push:
            # foam lace, broken
            return W['foam'] if (X * 3 + Y + frame) % 5 else W['hi']
        if d < 1.6:
            return W['hi'] if (X + Y * 2 + frame) % 4 == 0 else W['lt']
        if d < 3.2:
            return W['lt'] if ((X + Y) & 1) and d < 2.4 else surf.p[Y][X]
        return surf.p[Y][X]
    return T.autotile_block(color_at, E=4.0, R=5.0, Rn=2.5, wob=wob, dither=0.5)


def palm(leaf, leaf_out, bark, bark_out, coconut=None, w=32, h=48, lean=3, seed=0):
    img = Img(w, h)
    # segmented curving trunk
    cx0, cy0 = w / 2 + lean, 12
    for y in range(cy0, h - 2):
        t = (y - cy0) / (h - 2 - cy0)
        x = w / 2 + lean * (1 - t) ** 2
        for dx in range(-1, 2):
            c = bark[2] if dx < 0 else (bark[1] if dx == 0 else bark[0])
            if y % 3 == 0:
                c = bark[0] if dx >= 0 else bark[1]
            img.set(int(x + dx), y, c)
        img.set(int(x - 2), y, bark_out)
        img.set(int(x + 2), y, bark_out)
    # fronds: thick drooping arcs from the crown, lit on top
    fronds = [(-1.0, 0.6), (-0.55, 0.15), (0.55, 0.15), (1.0, 0.6), (-0.85, 1.2), (0.85, 1.2),
              (-0.2, -0.05), (0.25, -0.1)]
    fx, fy = cx0, cy0
    scale = w / 32.0
    order = sorted(range(len(fronds)), key=lambda i: -fronds[i][1])
    for i in order:
        dx, droop = fronds[i]
        L = int((14 if abs(dx) > 0.7 else 11) * scale) + 2
        for t in range(L):
            u = t / L
            x = fx + dx * t
            y = fy - 4 * scale * math.sin(u * math.pi * 0.9) + droop * t * u * 1.3 + (0 if abs(dx) > 0.3 else -t * 0.45)
            X, Y = int(round(x)), int(round(y))
            thick = 2 if u < 0.75 else 1
            img.set(X, Y - 1, leaf[3])
            for k in range(thick):
                img.set(X, Y + k, leaf[2] if k == 0 else leaf[1])
            # leaflets hanging from the frond
            if t % 2 == 0 and 1 < t < L - 1:
                img.set(X, Y + thick, leaf[1])
                img.set(X, Y + thick + 1, leaf[0])
    if coconut:
        for (x, y) in ((fx - 2, fy + 1), (fx + 1, fy + 2), (fx - 1, fy + 3)):
            img.rect(int(x), int(y), int(x) + 1, int(y) + 1, coconut[1])
            img.set(int(x), int(y), coconut[2])
    return img.outline(leaf_out)


def rowboat(wood, out, inner, w=32, h=16):
    img = Img(w, h)
    for y in range(3, 13):
        t = (y - 3) / 9
        half = (w / 2 - 1) * math.sqrt(max(0.0, 1 - (2 * t - 1) ** 2 * 0.15))
        inset = abs(y - 8) * 0.9
        for x in range(int(2 + inset), int(w - 2 - inset)):
            img.set(x, y, wood[1])
    for x in range(3, w - 3):
        img.set(x, 4, wood[2])
    for y in range(5, 11):
        for x in range(int(5 + abs(y - 8) * 0.9), int(w - 5 - abs(y - 8) * 0.9)):
            img.set(x, y, inner)
    img.hline(10, 11, 5, wood[0])
    img.rect(10, 5, 11, 11, wood[2])
    img.rect(20, 5, 21, 11, wood[2])
    img.hline(4, w - 5, 12, wood[0])
    return img.outline(out)


def fishing_boat(hull, hull_dk, wood, sail, out, w=48, h=48):
    img = Img(w, h)
    # hull
    for y in range(30, 44):
        inset = (y - 30) * 0.6
        for x in range(int(3 + inset), int(w - 3 - inset * 0.4)):
            img.set(x, y, hull if y < 38 else hull_dk)
    img.hline(3, w - 4, 30, wood[2])
    img.hline(4, w - 5, 31, wood[1])
    # cabin
    img.rect(26, 20, 38, 30, wood[1])
    img.rect(27, 21, 37, 22, wood[2])
    img.rect(29, 24, 32, 27, sail[0])
    img.rect(34, 24, 36, 27, sail[0])
    img.hline(25, 39, 19, wood[0])
    # mast + furled sail
    img.vline(16, 2, 30, wood[0])
    img.vline(15, 2, 30, wood[2])
    for y in range(6, 26):
        half = (y - 6) * 0.45
        for x in range(17, int(17 + half) + 1):
            img.set(x, y, sail[2] if x < 19 else sail[1])
    img.line(16, 2, 3, 30, wood[0])
    return img.outline(out)


def lighthouse(white, red, glass, stone, out, w=32, h=80):
    img = Img(w, h)
    top = 18
    for y in range(top, h - 6):
        t = (y - top) / (h - 6 - top)
        half = 6 + t * 5
        for x in range(int(w / 2 - half), int(w / 2 + half)):
            u = (x - (w / 2 - half)) / (2 * half)
            band = ((y - top) // 10) % 2
            R = red if band else white
            img.set(x, y, R[2] if u < 0.3 else (R[1] if u < 0.78 else R[0]))
    # base
    img.rect(4, h - 6, w - 5, h - 2, stone[1])
    img.hline(4, w - 5, h - 6, stone[2])
    img.rect(13, h - 14, 18, h - 6, stone[0])
    # gallery + lantern room
    img.rect(6, top - 3, w - 7, top - 1, stone[0])
    img.hline(6, w - 7, top - 3, stone[2])
    img.rect(10, 6, w - 11, top - 4, glass[1])
    img.rect(11, 7, 13, top - 5, glass[2])
    img.vline(16, 6, top - 4, stone[0])
    for y in range(0, 7):
        half = 1 + y * 0.9
        img.hline(int(w / 2 - half), int(w / 2 + half), y, red[1] if y else red[2])
    img.rect(14, top + 10, 17, top + 14, glass[0])
    return img.outline(out)


def stilt_hut(wood, roof, out, glass, w=48, h=64):
    img = Img(w, h)
    # stilts
    for x in (6, 20, 34):
        img.rect(x, 44, x + 2, h - 2, wood[0])
        img.vline(x, 44, h - 2, wood[1])
    # deck
    img.rect(1, 40, w - 2, 44, wood[1])
    img.hline(1, w - 2, 40, wood[2])
    for x in range(2, w - 2, 4):
        img.vline(x, 41, 44, wood[0])
    # walls
    for y in range(20, 40):
        for x in range(5, w - 5):
            img.set(x, y, wood[2] if (x % 4) == 0 else wood[1])
    img.rect(18, 26, 29, 39, wood[0])
    img.rect(19, 27, 28, 39, wood[0])
    img.rect(8, 25, 14, 31, glass[1])
    img.set(13, 26, glass[2])
    # thatch roof
    for y in range(2, 22):
        half = 6 + (y - 2) * 1.05
        for x in range(int(w / 2 - half), int(w / 2 + half)):
            n = hash32(x, y // 2, 3) % 5
            c = roof[2] if n < 2 else (roof[1] if n < 4 else roof[0])
            if (y % 4) == 3:
                c = roof[0] if (x % 3) else roof[1]
            img.set(x, y, c)
    img.hline(int(w / 2 - 26), int(w / 2 + 26), 21, roof[0])
    return img.outline(out)


def coral(pink, out, seed=0, w=16, h=16, kind='branch'):
    img = Img(w, h)
    if kind == 'branch':
        def br(x, y, a, ln, d):
            for t in range(ln):
                xx = x + math.cos(a) * t
                yy = y + math.sin(a) * t
                img.set(int(xx), int(yy), pink[1] if t % 3 else pink[2])
                img.set(int(xx) + 1, int(yy), pink[0])
            if d > 0:
                for k in (-1, 1):
                    br(int(x + math.cos(a) * ln), int(y + math.sin(a) * ln), a + k * 0.5, int(ln * 0.7), d - 1)
            else:
                img.set(int(x + math.cos(a) * ln), int(y + math.sin(a) * ln), pink[2])
        br(w // 2, h - 2, -math.pi / 2, 5, 2)
    else:
        # brain / fan coral
        img.ellipse(w / 2, h * 0.62, w / 2 - 2, h * 0.35, pink[1])
        for y in range(h):
            for x in range(w):
                if img.get(x, y) and (x + y * 2) % 4 == 0:
                    img.set(x, y, pink[2])
                if img.get(x, y) and (x - y) % 5 == 0:
                    img.set(x, y, pink[0])
    return img.outline(out)


def shells(shell, out, star=None):
    img = Img(16, 16)
    stamp(img, 3, 4, '''
    .ab.
    abba
    abba
    .aa.
    ''', {'a': shell[1], 'b': shell[2]})
    stamp(img, 10, 9, '''
    .a.
    aba
    ''', {'a': shell[1], 'b': shell[2]})
    if star:
        stamp(img, 5, 9, '''
        ..a..
        aabaa
        .aba.
        .a.a.
        ''', {'a': star[1], 'b': star[2]})
    return img.outline(out)


def buoy(red, white, out, frame):
    img = Img(16, 16)
    bob = frame % 2
    img.ellipse(8, 11 + bob, 5, 3.5, red[1])
    img.ellipse(7, 10 + bob, 3.5, 2.2, red[2])
    img.rect(7, 3 + bob, 8, 9 + bob, white[1])
    img.set(7, 3 + bob, white[2])
    img.rect(6, 1 + bob, 9, 2 + bob, red[1])
    img.hline(3, 12, 13 + bob, white[0])
    return img.outline(out)


def net_rack(wood, rope, out, w=32, h=32):
    img = Img(w, h)
    for x in (2, w - 4):
        img.rect(x, 3, x + 1, h - 2, wood[1])
        img.set(x, 3, wood[2])
    img.hline(2, w - 3, 4, wood[1])
    for y in range(5, h - 6):
        for x in range(4, w - 4):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                img.set(x, y + int(1.5 * math.sin((x - 4) / (w - 8) * math.pi)), rope)
    return img.outline(out)


def anchor(metal, out):
    img = Img(16, 16)
    img.vline(8, 2, 13, metal[1])
    img.vline(7, 2, 13, metal[2])
    img.hline(5, 10, 4, metal[1])
    img.ellipse(7.5, 1.5, 1.6, 1.4, metal[1])
    for x in range(3, 13):
        y = 13 - int(3 * (1 - ((x - 7.5) / 5) ** 2))
        img.set(x, y, metal[1])
        img.set(x, y + 1, metal[0])
    img.set(2, 10, metal[1])
    img.set(13, 10, metal[1])
    return img.outline(out)


def lobster_pots(wood, rope, out):
    img = Img(16, 16)
    for (x0, y0) in ((1, 6), (8, 8)):
        img.rect(x0, y0, x0 + 6, y0 + 6, wood[1])
        for x in range(x0, x0 + 7, 2):
            img.vline(x, y0, y0 + 6, wood[0])
        img.hline(x0, x0 + 6, y0, wood[2])
    img.line(4, 5, 11, 2, rope)
    return img.outline(out)


def driftwood(wood, out):
    img = Img(32, 16)
    for x in range(2, 29):
        y = 8 + int(2 * math.sin(x / 5.0))
        img.set(x, y, wood[2])
        img.set(x, y + 1, wood[1])
        img.set(x, y + 2, wood[0])
    img.line(8, 8, 5, 3, wood[1])
    img.line(20, 10, 24, 5, wood[2])
    return img.outline(out)


def whale_arch(bone, out, w=48, h=48):
    """Jaw-bone arch (3x3), walk through the middle."""
    img = Img(w, h)
    for side in (-1, 1):
        for t in range(40):
            u = t / 39
            x = w / 2 + side * (w / 2 - 5) * math.sin(u * math.pi * 0.5 + 0.2) ** 0.8
            y = h - 3 - u * (h - 8)
            if u > 0.85:
                x = w / 2 + side * (w / 2 - 5) * (1 - (u - 0.85) * 4)
            for d in range(-2, 2):
                img.set(int(x + d * side * 0), int(y), bone[1])
                img.set(int(x) + d, int(y), bone[2] if d < 0 else bone[1])
            img.set(int(x) + (2 if side > 0 else -3), int(y), bone[0])
    return img.outline(out)


def seaweed(G, out, frame=0):
    img = Img(16, 16)
    for i, x in enumerate((4, 8, 11)):
        for y in range(4 + i * 2, 15):
            sw = int(round(math.sin((y + frame * 2 + i) / 2.5)))
            img.set(x + sw, y, G[1] if y % 2 else G[2])
    return img.outline(out)


def gull(white, grey, out, frame):
    """A gull on a post-top perch, flapping on frame 1."""
    img = Img(16, 16)
    if frame % 2 == 0:
        stamp(img, 3, 6, '''
        ...ww.....
        ..wwwww...
        .ggwwwwwo.
        ....ww....
        ''', {'w': white, 'g': grey, 'o': out})
    else:
        stamp(img, 2, 3, '''
        g........g
        .gg....gg.
        ..gwwwwg..
        ...wwwwwo.
        ....ww....
        ''', {'w': white, 'g': grey, 'o': out})
    return img
