"""Props: rocks, signs, fences, bridges, docks, camp gear and other small
objects shared by several areas. Ramps are dark -> light role lists."""

import math

from core import Img, G, rnd, hash32, bayer, Height, shade
from paint import blob, faceted, clump_crown, scatter, stamp, CELL


# ---------------------------------------------------------------------------
# stone
# ---------------------------------------------------------------------------

def rock(w, h, ramp, out, seed=0, parts=None, cracks=None, moss=None):
    """Rounded boulder(s). parts: ellipsoids (cx, cy, rx, ry)."""
    if parts is None:
        parts = [(w / 2, h * 0.58, w / 2 - 1.5, h * 0.4 - 0.5)]
    cl = [(p[0], p[1], p[2], p[3]) for p in parts]
    img = clump_crown(w, h, cl, ramp, out, seed=seed, gdark=0.5, rim=1.1, speck=False,
                      dither=0.35)
    if cracks:
        for (x0, y0, x1, y1) in cracks:
            img.line(x0, y0, x1, y1, ramp[0])
    if moss:
        for x in range(w):
            for y in range(h):
                c = img.get(x, y)
                if c in ramp[-2:] and img.get(x, y - 1) in (None, out) and (x + seed) % 3 != 0:
                    img.set(x, y, moss[1])
                    if img.get(x, y + 1) in ramp[-2:]:
                        img.set(x, y + 1, moss[0])
    return img


def small_rock(ramp, out, seed=0):
    return rock(16, 16, ramp, out, seed, parts=[(8, 10, 6, 4.5), (5, 8.5, 3.2, 2.6)])


def boulder(ramp, out, seed=0):
    """Strength boulder: round, heavy, fills its cell."""
    return rock(16, 16, ramp, out, seed, parts=[(8, 9, 7, 6.2)])


def cracked_rock(ramp, out, seed=0):
    """Breakable rock: angular with a clear crack."""
    img = rock(16, 16, ramp, out, seed, parts=[(8, 9.5, 6.5, 5.2), (6, 7, 3.5, 2.5), (10.5, 7.5, 3, 2.4)])
    for (x, y) in ((8, 4), (8, 5), (7, 6), (8, 7), (9, 8), (8, 9), (7, 10), (7, 11)):
        if img.get(x, y) not in (None,):
            img.set(x, y, ramp[0])
    img.set(9, 6, ramp[-1])
    return img


def big_rock(ramp, out, seed=0, moss=None):
    return rock(32, 32, ramp, out, seed, parts=[(16, 19, 13.5, 10.5), (10, 13, 7, 6), (21, 12, 7.5, 6.5),
                                                (15, 9, 6, 5)], moss=moss)


def pebbles(ramp, out, seed=0):
    img = Img(16, 16)
    for i, (x, y) in enumerate(scatter(13, 13, 5, seed, margin=2, min_dist=4)):
        big = i % 2
        img.set(x, y, ramp[-1])
        img.set(x + 1, y, ramp[-2])
        img.set(x, y + 1, ramp[-2])
        img.set(x + 1, y + 1, ramp[1])
        if big:
            img.set(x + 2, y, ramp[-2])
            img.set(x + 2, y + 1, ramp[1])
    return img.outline(out)


def standing_stone(ramp, out, w=16, h=32, seed=0, rune=None, moss=None):
    """Menhir: stacked rounded blocks, a little lean."""
    parts = [(w / 2, h - 9, w / 2 - 2, 7.5), (w / 2 - 0.5, h - 17, w / 2 - 2.6, 7),
             (w / 2 - 1, h - 24, w / 2 - 3.4, 5)]
    img = rock(w, h, ramp, out, seed, parts=parts, moss=moss)
    if rune:
        cx = w // 2 - 1
        for (x, y) in ((0, 0), (0, 1), (0, 2), (-1, 3), (1, 3), (0, 4), (-2, 6), (2, 6), (0, 7), (0, 8)):
            img.set(cx + x, h - 22 + y, rune)
    return img


# ---------------------------------------------------------------------------
# wood
# ---------------------------------------------------------------------------

def plank_fill(img, x0, y0, x1, y1, wood, horizontal=True, seam=None, seed=0):
    """Planks with seams and light upper edges. wood: dark -> light."""
    n = len(wood)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if horizontal:
                k = (y - y0) % 4
                c = wood[-1] if k == 0 else (wood[n - 2] if k in (1, 2) else wood[max(0, n - 4)])
                if k == 3 or (seam and (x + ((y - y0) // 4) * 5 + seed) % 11 == 0):
                    c = seam or wood[0]
            else:
                k = (x - x0) % 4
                c = wood[-1] if k == 0 else (wood[n - 2] if k in (1, 2) else wood[max(0, n - 4)])
                if k == 3 or (seam and (y + ((x - x0) // 4) * 5 + seed) % 11 == 0):
                    c = seam or wood[0]
            img.set(x, y, c)


def signpost(wood, out, face=None, text=None):
    """Route sign on a post (1x1)."""
    img = Img(16, 16)
    img.rect(7, 9, 8, 15, wood[1])
    img.set(7, 9, wood[2])
    img.rect(2, 2, 13, 9, wood[2])
    img.rect(3, 3, 12, 8, face or wood[3])
    img.hline(3, 12, 3, wood[-1])
    for x in range(4, 12, 2):
        img.set(x, 5, wood[1])
        img.set(x + 1, 6, wood[1])
    img.hline(3, 12, 9, wood[0])
    return img.outline(out)


def arrow_sign(wood, out, face=None):
    img = Img(16, 16)
    img.rect(3, 9, 4, 15, wood[1])
    img.draw('''
    ..............
    .xxxxxxxxxx...
    .xyyyyyyyyyx..
    .xyzzzzzzzyyx.
    .xyyyyyyyyyx..
    .xxxxxxxxxx...
    ''', {'x': wood[1], 'y': face or wood[3], 'z': wood[0]}, 0, 2)
    return img.outline(out)


def notice_board(wood, out, paper, paper_dk, pin):
    img = Img(32, 32)
    img.rect(3, 10, 4, 30, wood[1])
    img.rect(27, 10, 28, 30, wood[1])
    img.rect(1, 6, 30, 22, wood[1])
    img.rect(2, 7, 29, 21, wood[2])
    img.rect(1, 3, 30, 5, wood[0])
    img.hline(0, 31, 3, wood[1])
    img.hline(1, 30, 2, wood[-1])
    for (x, y, w, h) in ((4, 9, 7, 8), (13, 8, 6, 6), (21, 10, 7, 9), (13, 15, 6, 5)):
        img.rect(x, y, x + w - 1, y + h - 1, paper)
        img.hline(x + 1, x + w - 2, y + 2, paper_dk)
        img.hline(x + 1, x + w - 3, y + 4, paper_dk)
        img.set(x + w // 2, y, pin)
    return img.outline(out)


def fence_block(wood, out, post_cap=None):
    """Wooden rail fence as a 64x32 custom block (transparent):
    row 0: [post][rail W end][rail middle][rail E end]
    row 1: [vertical top][vertical middle][vertical bottom][gate]"""
    img = Img(64, 32)
    cap = post_cap or wood[-1]

    def post(ox, oy, x=6):
        img.rect(ox + x, oy + 4, ox + x + 3, oy + 14, wood[1])
        img.vline(ox + x, oy + 4, oy + 14, wood[2])
        img.vline(ox + x + 3, oy + 4, oy + 14, wood[0])
        img.hline(ox + x, ox + x + 3, oy + 3, cap)

    def rails(ox, oy, x0, x1):
        for ry in (6, 11):
            img.hline(ox + x0, ox + x1, oy + ry, wood[2])
            img.hline(ox + x0, ox + x1, oy + ry + 1, wood[1])
            img.hline(ox + x0, ox + x1, oy + ry - 1, wood[-1])
    post(0, 0)
    rails(16, 0, 6, 15)
    post(16, 0)
    rails(32, 0, 0, 15)
    rails(48, 0, 0, 9)
    post(48, 0)
    # vertical run: posts stacked, rails seen end-on as a narrow beam
    for k, (y0, y1) in enumerate(((6, 15), (0, 15), (0, 10))):
        ox = k * 16
        img.rect(ox + 6, y0 + 16, ox + 9, y1 + 16, wood[1])
        img.vline(ox + 6, y0 + 16, y1 + 16, wood[2])
        img.vline(ox + 9, y0 + 16, y1 + 16, wood[0])
        if k == 0:
            img.hline(ox + 6, ox + 9, y0 + 15, cap)
        for y in range(y0 + 16, y1 + 17, 4):
            img.hline(ox + 6, ox + 9, y, wood[-1])
    # gate: two half rails with a latch
    rails(48, 16, 0, 15)
    img.rect(48 + 6, 16 + 4, 48 + 9, 16 + 13, wood[2])
    img.set(48 + 8, 16 + 8, wood[0])
    return img.outline(out)


def picket_block(paint_, paint_dk, out):
    """White picket fence (town): same layout as fence_block."""
    img = Img(64, 32)

    def pickets(ox, oy, x0, x1):
        for x in range(x0, x1 + 1):
            if (x - x0) % 4 in (0, 1, 2):
                img.vline(ox + x, oy + 4, oy + 14, paint_ if (x - x0) % 4 < 2 else paint_dk)
                if (x - x0) % 4 == 1:
                    img.set(ox + x, oy + 3, paint_)
        img.hline(ox + x0, ox + x1, oy + 7, paint_dk)
        img.hline(ox + x0, ox + x1, oy + 11, paint_dk)
    pickets(0, 0, 5, 10)
    pickets(16, 0, 5, 15)
    pickets(32, 0, 0, 15)
    pickets(48, 0, 0, 11)
    for k, (y0, y1) in enumerate(((5, 15), (0, 15), (0, 11))):
        ox = k * 16
        img.rect(ox + 6, y0 + 16, ox + 9, y1 + 16, paint_)
        img.vline(ox + 9, y0 + 16, y1 + 16, paint_dk)
        for y in range(y0 + 16, y1 + 17, 3):
            img.hline(ox + 6, ox + 9, y, paint_dk)
    pickets(48, 16, 1, 14)
    return img.outline(out)


def bridge_h(wood, out, rope=None, w=3):
    """East-west plank bridge, w cells long x 2 cells (railings N and S).
    Walkable (floor) over water."""
    img = Img(w * 16, 32)
    W = img.w
    plank_fill(img, 0, 6, W - 1, 25, wood, horizontal=False, seam=wood[0])
    for x in range(W):
        img.set(x, 6, wood[0])
        img.set(x, 25, wood[0])
        img.set(x, 26, out)
        img.set(x, 27, wood[0] if x % 8 in (2, 3) else None)
    # rails
    for y in (2, 3):
        img.hline(0, W - 1, y, wood[-1] if y == 2 else wood[1])
    img.hline(0, W - 1, 21, wood[-1])
    img.hline(0, W - 1, 22, wood[1])
    for x in range(1, W, 8):
        img.rect(x, 2, x + 1, 6, wood[1])
        img.rect(x, 20, x + 1, 25, wood[1])
        img.set(x, 2, wood[-1])
        img.set(x, 20, wood[-1])
        # support posts dipping into the water
        img.rect(x, 26, x + 1, 30, wood[0])
    return img.outline(out)


def bridge_v(wood, out, h=3):
    img = Img(32, h * 16)
    H = img.h
    plank_fill(img, 5, 0, 26, H - 1, wood, horizontal=True, seam=wood[0])
    for y in range(H):
        img.set(4, y, wood[0])
        img.set(27, y, wood[0])
        img.set(3, y, wood[1] if y % 8 else wood[-1])
        img.set(28, y, wood[1] if y % 8 else wood[-1])
        img.set(2, y, out)
        img.set(29, y, out)
    return img


def dock_block(wood, out, post):
    """Pier planks as a patch9 (80x48): planks run north-south; the south
    edge shows the front beam and pilings."""
    img = Img(80, 48)
    for by in range(3):
        for bx in range(5):
            ox, oy = bx * 16, by * 16
            plank_fill(img, ox, oy, ox + 15, oy + 15, wood, horizontal=False, seam=wood[0], seed=bx)
            west = bx == 0
            east = bx == 2
            north = by == 0
            south = by == 2
            if bx >= 3:
                west = east = north = south = False
            if north:
                img.hline(ox, ox + 15, oy, wood[-1])
            if west:
                img.vline(ox, oy, oy + 15, out)
                img.vline(ox + 1, oy, oy + 15, wood[-1])
            if east:
                img.vline(ox + 15, oy, oy + 15, out)
                img.vline(ox + 14, oy, oy + 15, wood[0])
            if south:
                img.rect(ox, oy + 11, ox + 15, oy + 12, wood[1])
                img.hline(ox, ox + 15, oy + 11, wood[2])
                img.hline(ox, ox + 15, oy + 13, out)
                for x in (3, 11):
                    img.rect(ox + x, oy + 14, ox + x + 1, oy + 15, post)
    # extras (row 2 col 3-4): mooring post, plank end
    return img


def campfire(wood, out, flame, frame):
    """flame: (hot, mid, dark) roles."""
    img = Img(16, 16)
    img.draw('''
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ................
    ....12....21....
    .....1221211....
    ...21122112212..
    ...o21211221o...
    ....oo....oo....
    ''', {'1': wood[2], '2': wood[1], 'o': wood[0]})
    hot, mid, dk = flame
    shapes = [
        ['......d.........', '.....dmd.d......', '....dmhmdmd.....', '....dmhhmhmd....', '.....mhhhhm.....'],
        ['.........d......', '......d.dmd.....', '.....dmdmhmd....', '....dmhmhhmd....', '.....mhhhhm.....'],
        ['.......d........', '......dmd.......', '.....dmhmd.d....', '....dmhhhmdmd...', '.....mhhhhm.....'],
    ]
    rows = shapes[frame % 3]
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            if ch != '.':
                img.set(i, 5 + j, {'h': hot, 'm': mid, 'd': dk}[ch])
    return img.outline(out)


def tent(cloth, cloth_dk, out, pole, w=32, h=32):
    img = Img(w, h)
    for y in range(4, 28):
        half = int((y - 4) * 0.62) + 1
        for x in range(16 - half, 16 + half):
            c = cloth if x < 16 else cloth_dk
            img.set(x, y, c)
    for y in range(14, 28):
        half = int((y - 14) * 0.35)
        img.hline(16 - half, 16 + half - 1, y, out)
    img.vline(16, 1, 4, pole)
    img.hline(2, 29, 28, None)
    return img.outline(out)


def barrel(wood, band, out):
    img = Img(16, 16)
    for y in range(3, 15):
        for x in range(3, 13):
            u = (x - 3) / 9
            k = 3 if u < 0.2 else (2 if u < 0.55 else (1 if u < 0.85 else 0))
            img.set(x, y, wood[min(k, len(wood) - 1)])
    for y in (5, 11):
        img.hline(3, 12, y, band)
    img.ellipse(8, 3.5, 5, 1.6, wood[-1])
    img.hline(5, 10, 3, wood[1])
    return img.outline(out)


def crate(wood, out, w=16, h=16):
    img = Img(w, h)
    img.rect(1, 3, w - 2, h - 2, wood[2])
    img.rect(1, 3, w - 2, 5, wood[-1])
    img.rect(2, 6, w - 3, h - 3, wood[1])
    for x in range(3, w - 3, 3):
        img.vline(x, 6, h - 3, wood[2])
    img.line(2, 6, w - 3, h - 3, wood[-1])
    img.rect(1, 6, 1, h - 2, wood[2])
    img.rect(w - 2, 6, w - 2, h - 2, wood[0])
    img.hline(1, w - 2, h - 2, wood[0])
    return img.outline(out)


def rock_column(ramp, out, w=32, h=48, seed=0, taper=0.2):
    """Tall stratified rock (sea stack, spire, mesa pillar): lump texture in
    a tapering column, lit cap on top. ramp: dark -> light (5)."""
    import terrain as T
    tex = T.lump_texture(ramp, 32, 32, seed, rx=6.5, ry=3.2, sx=9, sy=5.0, bias=-0.1)
    img = Img(w, h)
    for y in range(2, h - 1):
        t = (y - 2) / (h - 3)
        half = (w / 2 - 2) * (1 - taper + taper * t) + math.sin(y * 0.7 + seed) * 0.8
        for x in range(w):
            if abs(x + 0.5 - w / 2) <= half:
                img.p[y][x] = tex.p[y % 32][x % 32]
    for y in range(2, 7):
        for x in range(w):
            if img.p[y][x] is not None:
                img.p[y][x] = ramp[-1] if y < 4 else ramp[-2]
    return img.outline(out)
