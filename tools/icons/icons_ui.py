"""Bag icons owned by 'ui' (see tools/icons/__init__.py): the KEY items.

BIKE, WATERING CAN, HOE, FARM DEED, FERRY PASS, TOWN MAP, CREST CASE,
RECIPE BOOK and ENERGY FLASK (docs/EXPANSION.md 6). 24x24 each, painted
with the same helpers and top-left lighting as the core icons in
tools/gen_battle_gfx.py; index 1 of every palette is pure white.
"""

import math


def _put(cv, pts, col):
    for (x, y) in pts:
        cv.set(x, y, col)


def _thick_line(g, cv, x0, y0, x1, y1, col, w=1):
    for (x, y) in g.line_pts(x0, y0, x1, y1):
        for dx in range(w):
            for dy in range(w):
                cv.set(x + dx, y + dy, col)


def icon_bike(g):
    """A little teal step-through bike seen from the side."""
    C, W = g.C, g.WHITE
    tire = C(40, 40, 52)
    rim = g.ramp((120, 128, 144), (200, 208, 220))
    frame = g.ramp((16, 104, 112), (40, 160, 160), (112, 216, 208))
    seat = C(120, 72, 40)
    outc = C(24, 32, 40)
    cv = g.Canvas(24, 24)
    for cx in (5.5, 18.5):
        for y in range(24):
            for x in range(24):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - 16.5)
                if 3.6 <= d <= 5.2:
                    cv.set(x, y, tire)
                elif 2.6 <= d < 3.6:
                    cv.set(x, y, rim[1] if y < 16 else rim[0])
                elif d < 1.2:
                    cv.set(x, y, rim[0])
        # spokes
        for a in range(0, 180, 45):
            r = math.radians(a)
            for t in (-2.2, -1.2, 1.2, 2.2):
                cv.set(int(cx + t * math.cos(r)), int(16.5 + t * math.sin(r)), rim[0])
    # frame: rear hub -> pedal -> steering head, seat post, handlebar
    _thick_line(g, cv, 6, 16, 11, 17, frame[1], 2)
    _thick_line(g, cv, 11, 17, 16, 9, frame[1], 2)
    _thick_line(g, cv, 6, 16, 10, 9, frame[0], 1)
    _thick_line(g, cv, 16, 8, 18, 16, frame[0], 2)
    _thick_line(g, cv, 10, 9, 10, 7, frame[1], 1)
    _put(cv, [(8, 6), (9, 6), (10, 6), (11, 6)], seat)
    _put(cv, [(15, 6), (16, 6), (17, 6), (18, 5), (19, 5)], frame[2])
    _put(cv, [(11, 16), (12, 16)], frame[2])
    g.outline(cv, outc)
    cv.set(12, 12, W)
    return cv


def icon_watering_can(g):
    """A green tin watering can with a long spout and a few drops."""
    C, W = g.C, g.WHITE
    tin = g.ramp((32, 104, 56), (64, 160, 80), (128, 208, 120), (200, 240, 184))
    dark = C(24, 56, 32)
    water = C(96, 176, 248)
    cv = g.Canvas(24, 24)
    body = g.rect_mask(5, 10, 15, 20, r=2)
    g.paint_levels(cv, g.lathe_levels(body, th=(0.08, 0.45, 0.85)), tin)
    for x in range(5, 16):
        if cv.get(x, 12) is not None:
            cv.set(x, 12, tin[0])
    # handle loop over the top
    for a in range(200, 341, 10):
        r = math.radians(a)
        cv.set(int(10.5 + 5.5 * math.cos(r)), int(10.5 + 5.0 * math.sin(r)), tin[1])
    # spout and rose
    _thick_line(g, cv, 15, 17, 20, 9, tin[1], 2)
    _put(cv, [(20, 7), (21, 7), (21, 8), (22, 8), (20, 8)], tin[2])
    g.outline(cv, dark)
    _put(cv, [(7, 13), (7, 14)], W)
    for (x, y) in [(22, 11), (23, 13), (21, 13), (22, 15)]:
        if cv.get(x, y) is None:
            cv.set(x, y, water)
    return cv


def icon_hoe(g):
    """A hoe: an ash-wood handle and a steel blade."""
    C, W = g.C, g.WHITE
    wood = g.ramp((120, 72, 32), (176, 112, 56), (224, 168, 104))
    steel = g.ramp((88, 96, 112), (152, 160, 176), (216, 224, 236))
    outc = C(40, 32, 32)
    cv = g.Canvas(24, 24)
    for (x, y) in g.line_pts(3, 21, 15, 8):
        cv.set(x, y, wood[1])
        cv.set(x + 1, y, wood[2])
        cv.set(x, y + 1, wood[0])
    # the blade hangs across the end of the handle, like a garden hoe
    blade = g.poly_mask([(13.8, 6.2), (16.6, 3.4), (23.6, 11.4), (19.4, 14.6)], 24, 24)
    for (x, y) in blade:
        u = (x - 13.8) + (y - 6.2)
        cv.set(x, y, steel[2] if u < 4 else steel[1] if u < 10 else steel[0])
    _put(cv, [(15, 7), (16, 7), (15, 8)], C(80, 64, 48))
    g.outline(cv, outc)
    _put(cv, [(17, 5), (18, 6)], W)
    return cv


def icon_farm_deed(g):
    """A rolled deed with a field drawn on it and a red wax seal."""
    C, W = g.C, g.WHITE
    paper = g.ramp((200, 168, 112), (232, 208, 152), (248, 236, 200))
    ink = C(96, 64, 40)
    field = C(96, 168, 64)
    wax = g.ramp((152, 24, 32), (216, 56, 56))
    outc = C(80, 56, 32)
    cv = g.Canvas(24, 24)
    for (x, y) in g.rect_mask(4, 5, 19, 19):
        cv.set(x, y, paper[2] if y < 7 else paper[1])
    for y in range(4, 21):              # rolled ends
        cv.set(3, y, paper[0])
        cv.set(20, y, paper[0])
    for x in (4, 19):
        cv.set(x, 4, paper[0])
        cv.set(x, 20, paper[0])
    # the plot: a fenced field with furrows and a tiny house
    for x in range(6, 16):
        cv.set(x, 9, ink)
        cv.set(x, 15, ink)
    for y in range(9, 16):
        cv.set(6, y, ink)
        cv.set(15, y, ink)
    for y in (11, 13):
        for x in range(7, 15, 2):
            cv.set(x, y, field)
    _put(cv, [(11, 7), (10, 8), (12, 8)], ink)
    for (x, y) in g.ellipse_mask(16.5, 17.5, 2.6, 2.6):
        cv.set(x, y, wax[1] if x + y < 34 else wax[0])
    g.outline(cv, outc)
    cv.set(15, 16, W)
    return cv


def icon_ferry_pass(g):
    """A blue ferry ticket with a little boat and a punched hole."""
    C, W = g.C, g.WHITE
    card = g.ramp((32, 80, 160), (64, 128, 208), (136, 184, 240))
    boat = C(248, 232, 176)
    sail = C(232, 88, 64)
    outc = C(16, 32, 72)
    cv = g.Canvas(24, 24)
    body = g.rect_mask(2, 6, 21, 18, r=2)
    for (x, y) in body:
        cv.set(x, y, card[2] if y < 8 else card[1] if y < 16 else card[0])
    # notch and stub line
    for y in range(7, 18, 2):
        cv.set(16, y, card[2])
    for (x, y) in g.ellipse_mask(19.0, 12.0, 1.3, 1.3):
        cv.set(x, y, None)
    # the boat
    for x in range(5, 13):
        cv.set(x, 14, boat)
    for x in range(6, 12):
        cv.set(x, 15, boat)
    for y in range(9, 14):
        cv.set(9, y, C(96, 64, 40))
    _put(cv, [(10, 9), (10, 10), (11, 10), (10, 11), (11, 11), (12, 11), (10, 12), (11, 12), (12, 12), (13, 12)], sail)
    g.outline(cv, outc)
    _put(cv, [(4, 8), (5, 8)], W)
    return cv


def icon_town_map(g):
    """A folded map of the Vale: river, woods and a red you-are-here pin."""
    C, W = g.C, g.WHITE
    paper = g.ramp((200, 176, 120), (232, 212, 160), (248, 236, 196))
    river = C(88, 152, 232)
    wood = C(72, 144, 72)
    pin = g.ramp((168, 32, 32), (240, 80, 64))
    outc = C(88, 64, 40)
    cv = g.Canvas(24, 24)
    folds = [(2, 7), (8, 13), (14, 21)]
    for i, (x0, x1) in enumerate(folds):
        top = 5 if i % 2 == 0 else 3
        for y in range(top, top + 16):
            for x in range(x0, x1 + 1):
                shade = paper[1] if i != 1 else paper[2]
                if x == x0 and i:
                    shade = paper[0]
                cv.set(x, y, shade)
    # river winding across the folds
    for x in range(2, 22):
        y = int(12 + 3.2 * math.sin(x * 0.55))
        if cv.get(x, y) is not None:
            cv.set(x, y, river)
            if cv.get(x, y + 1) is not None:
                cv.set(x, y + 1, river)
    for (x, y) in [(4, 7), (5, 7), (4, 8), (15, 17), (16, 17), (17, 16), (10, 6), (11, 6)]:
        cv.set(x, y, wood)
    g.outline(cv, outc)
    # the pin, on top of the outline
    for (x, y) in g.ellipse_mask(17.5, 7.5, 2.4, 2.4):
        cv.set(x, y, pin[1] if x + y < 24 else pin[0])
    _put(cv, [(17, 10), (17, 11)], pin[0])
    cv.set(16, 6, W)
    return cv


def icon_crest_case(g):
    """An open velvet case with three crest medallions."""
    C, W = g.C, g.WHITE
    leather = g.ramp((72, 32, 88), (112, 56, 136), (160, 96, 184))
    velvet = C(56, 24, 48)
    gold = g.ramp((176, 120, 16), (240, 192, 48), (255, 240, 144))
    outc = C(32, 16, 40)
    cv = g.Canvas(24, 24)
    for (x, y) in g.rect_mask(2, 4, 21, 9, r=1):          # the lid, open
        cv.set(x, y, leather[2] if y < 6 else leather[1])
    for (x, y) in g.rect_mask(2, 10, 21, 20, r=1):        # the tray
        cv.set(x, y, leather[1] if y < 12 or y > 18 else velvet)
    for x in range(2, 22):
        cv.set(x, 20, leather[0])
    for cx, col in ((6.5, gold), (11.5, g.ramp((40, 96, 200), (104, 160, 240), (200, 224, 255))),
                    (16.5, g.ramp((200, 64, 120), (248, 120, 168), (255, 200, 224)))):
        for (x, y) in g.ellipse_mask(cx, 15.0, 2.2, 2.2):
            cv.set(x, y, col[2] if x + y < cx + 14 else col[1])
    _put(cv, [(11, 7), (12, 7)], gold[1])                 # clasp
    g.outline(cv, outc)
    cv.set(4, 5, W)
    return cv


def icon_recipe_book(g):
    """A red cookbook with a golden spoon on the cover."""
    C, W = g.C, g.WHITE
    cover = g.ramp((136, 32, 32), (192, 56, 48), (232, 104, 88))
    pages = C(248, 240, 216)
    gold = g.ramp((200, 144, 24), (255, 216, 96))
    outc = C(64, 16, 16)
    cv = g.Canvas(24, 24)
    for (x, y) in g.rect_mask(5, 3, 19, 20, r=1):
        cv.set(x, y, cover[1] if x > 7 else cover[0])
    for y in range(5, 21):
        cv.set(20, y, pages)
    for x in range(6, 20):
        cv.set(x, 21, pages)
    for y in range(3, 21):
        cv.set(7, y, cover[0])
    # spoon
    for (x, y) in g.ellipse_mask(13.5, 8.5, 2.2, 2.8):
        cv.set(x, y, gold[1] if x < 14 else gold[0])
    for y in range(11, 18):
        cv.set(13, y, gold[0])
        cv.set(14, y, gold[1] if y < 14 else gold[0])
    g.outline(cv, outc)
    _put(cv, [(9, 4), (9, 5)], cover[2])
    cv.set(12, 7, W)
    return cv


def icon_energy_flask(g):
    """A corked flask swirling with bands of typed energy."""
    C, W = g.C, g.WHITE
    glass = g.ramp((160, 184, 208), (216, 232, 244))
    bands = [C(248, 112, 48), C(72, 152, 248), C(96, 208, 96), C(248, 216, 64), C(184, 104, 232)]
    cork = g.ramp((136, 88, 48), (184, 128, 72))
    outc = C(32, 40, 64)
    cv = g.Canvas(24, 24)
    cx, cy, r = 11.5, 14.5, 7.0
    for (x, y) in g.ellipse_mask(cx, cy, r, r):
        ang = math.atan2(y + 0.5 - cy, x + 0.5 - cx)
        d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
        k = int(((ang + math.pi) / (2 * math.pi) * 5 + d * 0.35)) % 5
        cv.set(x, y, bands[k] if d < r - 1.2 else glass[0])
    for (x, y) in g.rect_mask(9, 3, 14, 8):
        cv.set(x, y, glass[1] if x < 11 else glass[0])
    for (x, y) in g.rect_mask(9, 1, 14, 3):
        cv.set(x, y, cork[1] if x < 12 else cork[0])
    g.outline(cv, outc)
    _put(cv, [(7, 10), (6, 11), (6, 12)], W)
    return cv


def icons(g):
    return [
        ('BIKE', icon_bike(g)),
        ('WATERING_CAN', icon_watering_can(g)),
        ('HOE', icon_hoe(g)),
        ('FARM_DEED', icon_farm_deed(g)),
        ('FERRY_PASS', icon_ferry_pass(g)),
        ('TOWN_MAP', icon_town_map(g)),
        ('CREST_CASE', icon_crest_case(g)),
        ('RECIPE_BOOK', icon_recipe_book(g)),
        ('ENERGY_FLASK', icon_energy_flask(g)),
    ]
