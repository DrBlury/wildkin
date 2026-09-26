"""Bag icons owned by 'farm' (see tools/icons/__init__.py).

The 18 crops, a seed packet for each of the 16 field crops (the crop drawn
small on a paper packet), the sapling, the three fertilisers, the
sprinkler and the processed goods (jam, pickles, dried chili, dried fruit,
toasted sun seeds). 24x24 each, top-left lighting like the core icons;
index 1 of every palette is pure white (gen_battle_gfx.index_image).
"""

import math


def _put(cv, pts, col):
    for (x, y) in pts:
        cv.set(x, y, col)


def _ball(g, cv, cx, cy, rx, ry, ramp, th=(0.15, 0.5, 0.8)):
    """A shaded ellipse (sphere lighting from the top left)."""
    for (x, y) in g.ellipse_mask(cx, cy, rx, ry):
        nx = (x + 0.5 - cx) / rx
        ny = (y + 0.5 - cy) / ry
        if nx * nx + ny * ny > 1.0:
            continue
        b = g.sphere_b(nx * 0.95, ny * 0.95)
        cv.set(x, y, ramp[min(g.quant(b, th), len(ramp) - 1)])


def _leaf(g, cv, x0, y0, x1, y1, width, ramp):
    """A pointed leaf from (x0, y0) to (x1, y1)."""
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        w = width * math.sin(math.pi * t)
        px, py = -(y1 - y0) / n, (x1 - x0) / n
        ln = math.hypot(px, py) or 1
        px, py = px / ln, py / ln
        k = -w
        while k <= w:
            cv.set(int(round(x + px * k)), int(round(y + py * k)), ramp[1] if k < 0 else ramp[0])
            k += 0.5
        cv.set(int(round(x)), int(round(y)), ramp[min(2, len(ramp) - 1)])


GREEN = ((40, 104, 48), (72, 160, 64), (136, 208, 96))


def _greens(g):
    return g.ramp(*GREEN)


# ---------------------------------------------------------------------------
# crops
# ---------------------------------------------------------------------------

def berries(g, cols, glow=False):
    C, W = g.C, g.WHITE
    rp = g.ramp(*cols)
    lf = _greens(g)
    cv = g.Canvas(24, 24)
    _leaf(g, cv, 12, 8, 19, 2, 2.2, lf)
    _leaf(g, cv, 11, 8, 5, 3, 1.8, lf)
    outc = C(32, 32, 40)
    for (cx, cy) in ((8.5, 12.5), (15.5, 12.5), (12, 17.5)):
        for (x, y) in g.ellipse_mask(cx, cy, 5.1, 5.1):
            cv.set(x, y, outc)
        _ball(g, cv, cx, cy, 4.2, 4.2, rp)
    g.outline(cv, outc)
    for (x, y) in ((7, 10), (14, 10), (10, 15)):
        cv.set(x, y, W)
    if glow:
        for (x, y) in ((2, 13), (21, 9), (20, 20), (3, 20)):
            if cv.get(x, y) is None:
                cv.set(x, y, rp[-1])
    return cv


def icon_glowberry(g):
    return berries(g, ((56, 160, 136), (104, 216, 176), (176, 248, 208), (224, 255, 232)), glow=True)


def icon_emberberry(g):
    return berries(g, ((152, 32, 32), (224, 72, 40), (248, 144, 64), (255, 208, 128)))


def icon_tideberry(g):
    return berries(g, ((40, 64, 160), (72, 120, 224), (128, 176, 248), (192, 224, 255)))


def icon_radish(g):
    C, W = g.C, g.WHITE
    root = g.ramp((152, 24, 72), (216, 56, 104), (248, 120, 152), (255, 192, 208))
    tip = C(240, 232, 216)
    cv = g.Canvas(24, 24)
    lf = _greens(g)
    _leaf(g, cv, 12, 11, 7, 2, 2.4, lf)
    _leaf(g, cv, 12, 11, 17, 2, 2.4, lf)
    _leaf(g, cv, 12, 11, 12, 2, 1.8, lf)
    _ball(g, cv, 12, 15, 5.5, 5.0, root)
    _put(cv, [(12, 20), (12, 21), (13, 22)], tip)
    g.outline(cv, C(48, 24, 32))
    _put(cv, [(10, 13), (9, 14)], W)
    return cv


def icon_carrot(g):
    C, W = g.C, g.WHITE
    body = g.ramp((184, 80, 16), (240, 128, 32), (255, 184, 88))
    cv = g.Canvas(24, 24)
    lf = _greens(g)
    _leaf(g, cv, 15, 8, 20, 1, 2.0, lf)
    _leaf(g, cv, 15, 8, 14, 1, 1.8, lf)
    _leaf(g, cv, 15, 8, 21, 6, 1.6, lf)
    cone = g.poly_mask([(10.0, 7.5), (18.5, 11.0), (4.0, 21.5)], 24, 24)
    for (x, y) in cone:
        d = (x - 4) * 0.55 - (y - 21) * 0.8
        cv.set(x, y, body[2] if (x + y) % 7 == 0 else body[1] if d > 6 else body[0])
    for (x, y) in cone:
        if (x * 3 + y * 2) % 9 == 0:
            cv.set(x, y, body[0])
    g.outline(cv, C(80, 32, 16))
    _put(cv, [(11, 10), (10, 11)], W)
    return cv


def icon_potato(g):
    C, W = g.C, g.WHITE
    skin = g.ramp((120, 80, 40), (176, 128, 72), (216, 176, 112), (240, 212, 156))
    cv = g.Canvas(24, 24)
    _ball(g, cv, 12, 13, 8.5, 6.0, skin)
    for (x, y) in ((8, 12), (14, 10), (16, 15), (10, 16)):
        cv.set(x, y, skin[0])
    g.outline(cv, C(64, 40, 24))
    _put(cv, [(8, 9), (9, 9)], W)
    return cv


def icon_pumpkin(g):
    C, W = g.C, g.WHITE
    rp = g.ramp((176, 72, 16), (232, 120, 32), (248, 168, 64), (255, 208, 120))
    cv = g.Canvas(24, 24)
    for cx in (7.5, 16.5, 12):
        _ball(g, cv, cx, 14.5, 6.0 if cx != 12 else 6.5, 7.0, rp)
    for y in range(9, 21):
        for x in (9, 15):
            if cv.get(x, y) is not None:
                cv.set(x, y, rp[0])
    stem = g.ramp((64, 88, 32), (104, 136, 56))
    _put(cv, [(12, 5), (12, 6), (13, 5), (13, 6), (12, 7), (13, 4), (14, 4)], stem[1])
    _put(cv, [(11, 7)], stem[0])
    g.outline(cv, C(80, 32, 16))
    _put(cv, [(5, 11), (5, 12)], W)
    return cv


def icon_chili(g):
    C, W = g.C, g.WHITE
    rp = g.ramp((144, 16, 24), (216, 40, 40), (248, 104, 88))
    cv = g.Canvas(24, 24)
    pts = []
    for i in range(40):
        t = i / 39
        x = 7 + 12 * t
        y = 6 + 12 * t + 4 * math.sin(t * math.pi)
        w = 3.2 * (1 - t) + 0.6
        pts.append((x, y, w))
    for (x, y, w) in pts:
        for (px, py) in g.ellipse_mask(x, y, w, w):
            ny = (py + 0.5 - y) / w
            cv.set(px, py, rp[2] if ny < -0.45 else rp[1] if ny < 0.4 else rp[0])
    stem = g.ramp((48, 104, 40), (96, 168, 64))
    _put(cv, [(5, 4), (6, 5), (4, 3), (6, 4), (7, 5)], stem[1])
    _put(cv, [(5, 5), (7, 6)], stem[0])
    g.outline(cv, C(64, 16, 24))
    _put(cv, [(8, 5), (9, 5)], W)
    return cv


def icon_tomato(g):
    C, W = g.C, g.WHITE
    rp = g.ramp((160, 24, 24), (224, 56, 40), (248, 112, 88), (255, 176, 152))
    cv = g.Canvas(24, 24)
    _ball(g, cv, 12, 13.5, 8.0, 7.0, rp)
    lf = _greens(g)
    for (dx, dy) in ((-4, -1), (4, -1), (-2, -3), (2, -3), (0, -1)):
        _leaf(g, cv, 12, 7, 12 + dx, 7 + dy + 2, 1.0, lf)
    _put(cv, [(12, 4), (12, 5), (12, 6)], lf[0])
    g.outline(cv, C(72, 16, 24))
    _put(cv, [(7, 11), (7, 12), (8, 10)], W)
    return cv


def icon_corn(g):
    C, W = g.C, g.WHITE
    kern = g.ramp((200, 144, 24), (248, 200, 48), (255, 236, 128))
    husk = _greens(g)
    cv = g.Canvas(24, 24)
    cob = g.ellipse_mask(12, 11, 4.2, 9.0)
    for (x, y) in cob:
        k = kern[2] if (x + (y // 2)) % 2 == 0 and y % 2 == 0 else kern[1]
        if x >= 14:
            k = kern[0] if y % 2 else kern[1]
        cv.set(x, y, k)
    for side in (-1, 1):
        for y in range(10, 23):
            t = (y - 10) / 12
            x = 12 + side * (5.5 - 3.5 * t)
            for dx in range(3):
                cv.set(int(x) - side * dx, y, husk[0] if dx == 0 else husk[1])
    g.outline(cv, C(64, 56, 16))
    _put(cv, [(10, 4), (10, 5)], W)
    return cv


def icon_sunflower(g):
    C, W = g.C, g.WHITE
    pet = g.ramp((208, 136, 16), (248, 200, 40), (255, 240, 128))
    seed = g.ramp((72, 40, 24), (120, 72, 40))
    cv = g.Canvas(24, 24)
    for k in range(12):
        a = k * math.pi / 6
        _ball(g, cv, 12 + 7 * math.cos(a), 11 + 7 * math.sin(a), 2.6, 2.6, pet, th=(0.2, 0.6))
    for (x, y) in g.ellipse_mask(12, 11, 5.0, 5.0):
        cv.set(x, y, seed[(x + y) % 2])
    stem = _greens(g)
    for y in range(18, 24):
        cv.set(12, y, stem[0])
        cv.set(13, y, stem[1])
    g.outline(cv, C(80, 56, 16))
    _put(cv, [(10, 9)], W)
    return cv


def icon_motebloom(g):
    C, W = g.C, g.WHITE
    pet = g.ramp((120, 64, 184), (176, 112, 232), (228, 184, 255))
    core = C(255, 236, 160)
    cv = g.Canvas(24, 24)
    for k in range(5):
        a = k * 2 * math.pi / 5 - math.pi / 2
        _ball(g, cv, 12 + 5 * math.cos(a), 11 + 5 * math.sin(a), 3.6, 3.6, pet, th=(0.2, 0.6))
    for (x, y) in g.ellipse_mask(12, 11, 2.2, 2.2):
        cv.set(x, y, core)
    stem = _greens(g)
    for y in range(17, 24):
        cv.set(12, y, stem[0])
    _leaf(g, cv, 12, 21, 17, 18, 1.4, stem)
    g.outline(cv, C(56, 32, 88))
    mote = C(200, 255, 232)
    for (x, y) in ((3, 4), (20, 3), (21, 14), (2, 16), (6, 22)):
        cv.set(x, y, mote)
    _put(cv, [(9, 7)], W)
    return cv


def icon_fruit(g, rp, crease=False):
    C, W = g.C, g.WHITE
    cv = g.Canvas(24, 24)
    _ball(g, cv, 12, 14, 8.0, 7.5, rp)
    if crease:
        for y in range(8, 20):
            x = 13 + int(1.2 * math.sin((y - 8) / 12 * math.pi))
            if cv.get(x, y) is not None:
                cv.set(x, y, rp[0])
    else:
        _put(cv, [(11, 7), (12, 7), (13, 7), (12, 8)], rp[0])
    stem = C(96, 64, 32)
    _put(cv, [(12, 3), (12, 4), (12, 5), (12, 6)], stem)
    _leaf(g, cv, 13, 5, 19, 3, 1.8, _greens(g))
    g.outline(cv, C(64, 24, 24))
    _put(cv, [(7, 11), (7, 12), (8, 10)], W)
    return cv


def icon_apple(g):
    return icon_fruit(g, g.ramp((144, 16, 32), (208, 40, 48), (240, 96, 80), (255, 168, 144)))


def icon_peach(g):
    return icon_fruit(g, g.ramp((208, 96, 88), (248, 144, 112), (255, 192, 152), (255, 228, 200)),
                      crease=True)


def icon_strawberry(g):
    C, W = g.C, g.WHITE
    rp = g.ramp((152, 16, 40), (224, 48, 56), (248, 112, 104), (255, 176, 160))
    cv = g.Canvas(24, 24)
    for (x, y) in g.ellipse_mask(12, 13, 8.0, 8.0):
        # a rounded heart: wide at the top, pointed at the bottom
        dy = (y + 0.5 - 9.0) / 12.0
        if abs(x + 0.5 - 12) > 8.0 * (1.0 - max(dy, 0.0) ** 1.4):
            continue
        nx, ny = (x + 0.5 - 12) / 8.0, (y + 0.5 - 12) / 9.0
        b = g.sphere_b(nx * 0.95, ny * 0.95)
        cv.set(x, y, rp[min(g.quant(b, (0.15, 0.5, 0.8)), 3)])
    seed = C(255, 232, 128)
    for (x, y) in ((9, 10), (13, 9), (16, 11), (11, 13), (15, 14), (8, 14), (12, 17), (10, 16), (14, 18)):
        if cv.get(x, y) is not None:
            cv.set(x, y, seed)
    lf = _greens(g)
    for (dx, dy) in ((-5, 0), (5, 0), (-2, -2), (2, -2), (0, -3)):
        _leaf(g, cv, 12, 6, 12 + dx, 6 + dy, 1.2, lf)
    g.outline(cv, C(72, 16, 32))
    _put(cv, [(7, 9), (7, 10)], W)
    return cv


def icon_melon(g):
    C, W = g.C, g.WHITE
    rind = g.ramp((32, 96, 40), (64, 144, 56), (120, 196, 88), (176, 228, 136))
    cv = g.Canvas(24, 24)
    _ball(g, cv, 12, 13, 9.5, 8.5, rind)
    for y in range(24):
        for x in range(24):
            v = cv.get(x, y)
            if v is None:
                continue
            band = int(round((x - 12) * 0.9 + 0.3 * (y - 13) ** 2 / 9.0)) % 5
            if band == 0:
                cv.set(x, y, rind[0] if v != rind[3] else rind[1])
    stem = C(96, 72, 32)
    _put(cv, [(12, 3), (12, 4), (13, 4)], stem)
    _leaf(g, cv, 13, 4, 19, 2, 1.6, _greens(g))
    g.outline(cv, C(24, 56, 24))
    _put(cv, [(6, 9), (7, 8)], W)
    return cv


def icon_eggplant(g):
    C, W = g.C, g.WHITE
    rp = g.ramp((56, 24, 88), (104, 48, 144), (160, 96, 200), (208, 160, 240))
    cv = g.Canvas(24, 24)
    _ball(g, cv, 11, 11, 4.5, 4.5, rp)
    _ball(g, cv, 13.5, 16, 6.5, 6.0, rp)
    cap = _greens(g)
    for (dx, dy) in ((-4, 2), (3, 1), (0, 3), (-2, -1)):
        _leaf(g, cv, 9, 6, 9 + dx, 6 + dy, 1.3, cap)
    _put(cv, [(7, 3), (8, 4), (8, 5)], cap[0])
    g.outline(cv, C(40, 16, 56))
    _put(cv, [(9, 9), (10, 9), (10, 13)], W)
    return cv


def icon_snowpea(g):
    C, W = g.C, g.WHITE
    pod = g.ramp((48, 120, 56), (96, 176, 72), (160, 220, 120), (212, 244, 180))
    pea = g.ramp((72, 152, 64), (136, 208, 96), (200, 240, 160))
    cv = g.Canvas(24, 24)
    for i in range(48):
        t = i / 47
        x = 4 + 16 * t
        y = 16 - 9 * t + 3 * math.sin(t * math.pi)
        w = 3.4 * math.sin(math.pi * (0.08 + 0.84 * t)) + 0.4
        for (px, py) in g.ellipse_mask(x, y, w, w):
            ny = (py + 0.5 - y) / max(w, 0.5)
            cv.set(px, py, pod[3] if ny < -0.6 else pod[2] if ny < -0.1 else pod[1] if ny < 0.5 else pod[0])
    for k, t in enumerate((0.25, 0.45, 0.65)):
        x = 4 + 16 * t
        y = 16 - 9 * t + 3 * math.sin(t * math.pi)
        _ball(g, cv, x, y, 1.9, 1.9, pea)
    stem = _greens(g)
    _put(cv, [(20, 6), (21, 5), (21, 4), (22, 3)], stem[0])
    g.outline(cv, C(24, 64, 32))
    frost = C(236, 248, 255)
    for (x, y) in ((3, 4), (7, 2), (18, 19), (21, 14)):
        if cv.get(x, y) is None:
            cv.set(x, y, frost)
    _put(cv, [(6, 14)], W)
    return cv


CROP_ICONS = [
    ('GLOWBERRY', icon_glowberry), ('EMBERBERRY', icon_emberberry), ('TIDEBERRY', icon_tideberry),
    ('RADISH', icon_radish), ('CARROT', icon_carrot), ('POTATO', icon_potato),
    ('PUMPKIN', icon_pumpkin), ('CHILI', icon_chili), ('TOMATO', icon_tomato),
    ('CORN', icon_corn), ('SUNFLOWER', icon_sunflower), ('MOTEBLOOM', icon_motebloom),
    ('APPLE', icon_apple), ('PEACH', icon_peach),
    ('STRAWBERRY', icon_strawberry), ('MELON', icon_melon), ('EGGPLANT', icon_eggplant),
    ('SNOWPEA', icon_snowpea),
]

# ---------------------------------------------------------------------------
# seed packets, sapling, fertilisers, sprinkler
# ---------------------------------------------------------------------------


def _shrink(cv):
    """Half-size copy: the most common opaque colour of each 2x2 block."""
    out = cv.__class__(12, 12)
    for y in range(12):
        for x in range(12):
            cnt = {}
            for dy in range(2):
                for dx in range(2):
                    v = cv.get(x * 2 + dx, y * 2 + dy)
                    if v is not None:
                        cnt[v] = cnt.get(v, 0) + 1
            if sum(cnt.values()) >= 2:
                out.p[y][x] = max(cnt, key=lambda k: cnt[k])
    return out


def _cap_colors(g, cv, keep, limit):
    """Merge the least-used colours into their nearest neighbour until at
    most `limit` remain (colours in `keep` always stay)."""
    while True:
        cnt = {}
        for row in cv.p:
            for v in row:
                if v is not None:
                    cnt[v] = cnt.get(v, 0) + 1
        if len(cnt) <= limit:
            return cv
        cands = [c for c in cnt if c not in keep]
        worst = min(cands, key=lambda c: cnt[c])
        others = [c for c in cnt if c != worst]
        near = min(others, key=lambda c: sum((c[i] - worst[i]) ** 2 for i in range(3)))
        for row in cv.p:
            for i, v in enumerate(row):
                if v == worst:
                    row[i] = near


def icon_packet(g, crop_cv, band):
    C, W = g.C, g.WHITE
    paper = g.ramp((200, 176, 136), (232, 216, 176), (248, 240, 216))
    outc = C(72, 56, 40)
    bd = C(*band)
    cv = g.Canvas(24, 24)
    for (x, y) in g.rect_mask(4, 2, 19, 22, r=1):
        cv.set(x, y, paper[2] if x < 8 else paper[1])
    for x in range(4, 20):
        cv.set(x, 3, paper[0])
        cv.set(x, 19, bd)
        cv.set(x, 20, bd)
    for x in range(5, 19, 2):
        cv.set(x, 2, paper[0])
    small = _shrink(crop_cv)
    for y in range(12):
        for x in range(12):
            v = small.p[y][x]
            if v is not None:
                cv.set(6 + x, 6 + y, v)
    g.outline(cv, outc)
    cv.set(5, 5, W)
    return _cap_colors(g, cv, (W, outc, bd), 14)


PACKET_BANDS = {
    'GLOWBERRY': (104, 216, 176), 'EMBERBERRY': (224, 72, 40), 'TIDEBERRY': (72, 120, 224),
    'RADISH': (216, 56, 104), 'CARROT': (240, 128, 32), 'POTATO': (176, 128, 72),
    'PUMPKIN': (232, 120, 32), 'CHILI': (216, 40, 40), 'TOMATO': (224, 56, 40),
    'CORN': (248, 200, 48), 'SUNFLOWER': (248, 200, 40), 'MOTEBLOOM': (176, 112, 232),
    'STRAWBERRY': (224, 48, 72), 'MELON': (64, 152, 64), 'EGGPLANT': (120, 64, 176),
    'SNOWPEA': (144, 208, 232),
}


def icon_sapling(g):
    C, W = g.C, g.WHITE
    burlap = g.ramp((120, 88, 48), (168, 128, 80), (208, 176, 120))
    bark = C(104, 72, 40)
    cv = g.Canvas(24, 24)
    _ball(g, cv, 12, 18, 6.0, 4.5, burlap)
    for x in range(7, 18):
        if cv.get(x, 16) is not None:
            cv.set(x, 16, burlap[0])
    for y in range(8, 15):
        cv.set(12, y, bark)
    lf = _greens(g)
    _leaf(g, cv, 12, 10, 6, 5, 2.2, lf)
    _leaf(g, cv, 12, 9, 18, 4, 2.2, lf)
    _leaf(g, cv, 12, 8, 12, 1, 1.8, lf)
    g.outline(cv, C(48, 40, 24))
    _put(cv, [(9, 17)], W)
    return cv


def _sack(g, body, label, label_fn):
    C, W = g.C, g.WHITE
    rp = g.ramp(*body)
    cv = g.Canvas(24, 24)
    sack = g.poly_mask([(6, 6), (18, 6), (20, 21), (4, 21)], 24, 24)
    g.paint_levels(cv, g.lathe_levels(sack), rp)
    for x in range(7, 18):
        cv.set(x, 5, rp[0])
    _put(cv, [(8, 4), (10, 3), (12, 4), (14, 3), (16, 4)], rp[1])
    for (x, y) in g.rect_mask(8, 11, 16, 17, r=1):
        cv.set(x, y, C(*label))
    label_fn(cv)
    g.outline(cv, C(48, 36, 24))
    _put(cv, [(7, 8), (7, 9)], W)
    return cv


def icon_fertilizer(g):
    lf = _greens(g)

    def mark(cv):
        _leaf(g, cv, 10, 16, 14, 12, 1.4, lf)
    return _sack(g, ((120, 96, 64), (176, 148, 100), (216, 196, 148)), (240, 232, 200), mark)


def icon_rich_compost(g):
    C = g.C

    def mark(cv):
        for (x, y) in ((10, 13), (12, 15), (14, 13), (11, 16), (13, 12)):
            cv.set(x, y, C(56, 40, 32))
    return _sack(g, ((56, 44, 36), (96, 76, 56), (136, 112, 84)), (200, 168, 96), mark)


def icon_grow_mulch(g):
    C = g.C

    def mark(cv):
        for x in range(9, 16):
            cv.set(x, 12 + (x % 3), C(120, 176, 232))
    return _sack(g, ((168, 136, 56), (216, 184, 88), (240, 220, 140)), (232, 240, 216), mark)


def icon_sprinkler(g):
    C, W = g.C, g.WHITE
    brass = g.ramp((136, 96, 32), (200, 152, 56), (240, 208, 120))
    metal = g.ramp((72, 80, 96), (136, 144, 160))
    water = g.ramp((56, 120, 224), (136, 192, 255))
    cv = g.Canvas(24, 24)
    for y in range(13, 23):
        cv.set(11, y, metal[1])
        cv.set(12, y, metal[0])
    _ball(g, cv, 11.5, 11.5, 5.0, 3.5, brass)
    for (x, y) in g.rect_mask(10, 6, 13, 8):
        cv.set(x, y, brass[2] if x < 12 else brass[1])
    g.outline(cv, C(48, 40, 24))
    for side in (-1, 1):
        for i in range(9):
            t = i / 8
            x = 11.5 + side * (4 + 7 * t)
            y = 6 - 4 * math.sin(t * math.pi * 0.9) + 6 * t * t
            cv.set(int(round(x)), int(round(y)), water[1] if i % 2 else water[0])
    for (x, y) in ((4, 17), (19, 17), (2, 13), (21, 13)):
        cv.set(x, y, water[0])
    _put(cv, [(9, 10)], W)
    return cv

# ---------------------------------------------------------------------------
# processed goods
# ---------------------------------------------------------------------------


def _jar(g, fill, lid):
    C, W = g.C, g.WHITE
    glass = g.ramp((152, 176, 192), (208, 224, 232))
    rp = g.ramp(*fill)
    lr = g.ramp(*lid)
    cv = g.Canvas(24, 24)
    body = g.rect_mask(5, 7, 18, 21, r=3)
    g.paint_levels(cv, g.lathe_levels(body), rp)
    for (x, y) in g.rect_mask(6, 3, 17, 7, r=1):
        cv.set(x, y, lr[1] if y < 5 else lr[0])
    for (x, y) in g.rect_mask(7, 12, 16, 16):
        cv.set(x, y, C(248, 236, 208))
    _put(cv, [(9, 14), (10, 14), (11, 14), (12, 14), (13, 14), (14, 14)], C(120, 88, 56))
    for y in range(9, 20):
        cv.set(6, y, glass[1])
    g.outline(cv, C(40, 40, 48))
    _put(cv, [(7, 9), (7, 10)], W)
    return cv


def icon_fruit_jam(g):
    return _jar(g, ((128, 16, 48), (192, 40, 72), (232, 88, 112)), ((176, 48, 48), (224, 104, 96)))


def icon_pickles(g):
    return _jar(g, ((56, 96, 32), (96, 144, 56), (160, 192, 96)), ((200, 168, 64), (240, 212, 112)))


def icon_dried_chili(g):
    C, W = g.C, g.WHITE
    rp = g.ramp((112, 16, 24), (168, 32, 32), (216, 80, 56))
    cord = C(200, 176, 128)
    cv = g.Canvas(24, 24)
    for x in range(2, 22):
        cv.set(x, 3 + (1 if 6 < x < 17 else 0), cord)
    for (x0, bend) in ((5, 1), (12, -1), (18, 1)):
        for i in range(30):
            t = i / 29
            x = x0 + bend * 2.5 * math.sin(t * math.pi * 0.8)
            y = 5 + 15 * t
            w = 2.4 * (1 - t) + 0.5
            for (px, py) in g.ellipse_mask(x, y, w, w):
                nx = (px + 0.5 - x) / w
                cv.set(px, py, rp[2] if nx < -0.4 else rp[1] if nx < 0.4 else rp[0])
        cv.set(x0, 4, C(96, 120, 48))
    g.outline(cv, C(56, 16, 16))
    _put(cv, [(4, 7), (11, 7), (17, 7)], W)
    return cv


def icon_dried_fruit(g):
    C, W = g.C, g.WHITE
    rp = g.ramp((136, 72, 32), (192, 120, 56), (232, 176, 96))
    cv = g.Canvas(24, 24)
    for (cx, cy) in ((8.5, 9.5), (15.5, 11.5), (10.5, 16.5)):
        for (x, y) in g.ellipse_mask(cx, cy, 5.0, 4.0):
            d = math.hypot((x + 0.5 - cx) / 5.0, (y + 0.5 - cy) / 4.0)
            cv.set(x, y, rp[2] if d < 0.35 else rp[0] if d > 0.8 else rp[1])
    g.outline(cv, C(64, 32, 16))
    _put(cv, [(6, 7)], W)
    return cv


def icon_sun_seeds(g):
    C, W = g.C, g.WHITE
    wood = g.ramp((104, 64, 32), (152, 104, 56), (192, 144, 88))
    shell = C(56, 52, 56)
    stripe = C(232, 224, 208)
    outc = C(24, 20, 24)
    cv = g.Canvas(24, 24)
    bowl = set((x, y) for (x, y) in g.ellipse_mask(12, 14, 10.0, 7.0) if y >= 14)
    g.paint_levels(cv, g.lathe_levels(bowl), wood)
    for x in range(2, 23):
        cv.set(x, 14, wood[0])
    for (cx, cy, lean) in ((6, 11, -1), (10, 9, 0), (14, 10, 1), (18, 11, 0), (8, 13, 1), (16, 13, -1), (12, 12, 0)):
        for dy in range(-3, 4):
            for dx in (-1, 0, 1):
                x = cx + dx + (lean if dy < 0 else 0)
                y = cy + dy
                if abs(dy) == 3 and dx:
                    continue
                cv.set(x, y, stripe if dx == 0 and abs(dy) < 2 else shell)
    g.outline(cv, outc)
    _put(cv, [(4, 16)], W)
    return cv


def icons(g):
    out = []
    crops = {}
    for (name, fn) in CROP_ICONS:
        crops[name] = fn(g)
        out.append(('CROP_' + name, crops[name]))
    for (name, _) in CROP_ICONS:
        if name in ('APPLE', 'PEACH'):
            continue
        out.append(('SEED_' + name, icon_packet(g, crops[name], PACKET_BANDS[name])))
    out += [
        ('SAPLING', icon_sapling(g)),
        ('FERTILIZER', icon_fertilizer(g)),
        ('RICH_COMPOST', icon_rich_compost(g)),
        ('GROW_MULCH', icon_grow_mulch(g)),
        ('SPRINKLER', icon_sprinkler(g)),
        ('FRUIT_JAM', icon_fruit_jam(g)),
        ('PICKLES', icon_pickles(g)),
        ('DRIED_CHILI', icon_dried_chili(g)),
        ('DRIED_FRUIT', icon_dried_fruit(g)),
        ('SUN_SEEDS', icon_sun_seeds(g)),
    ]
    return out
