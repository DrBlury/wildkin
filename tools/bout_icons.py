"""Bag icons for the bout supplies (src/game/items/core.inc), drawn with the
helpers of tools/gen_battle_gfx.py.

    icons(g) -> [('NAME', canvas_24x24), ...]   # g = the gen_battle_gfx module

Each NAME becomes ICON_NAME in gfx_battle.h, right after the 17 original
icons and before the other owners' registry icons (tools/icons/).

Same house style as the originals: light from the top-left, quantised
shading, a 1px dark outline in a tint of the icon's main colour, at most 15
colours (index 1 is pure white, forced by g.index_image).
"""

import math


def _paint(cv, x0, y0, rows, cols):
    """Stamp character art: rows of strings, '.' = leave, else cols[ch]."""
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != '.':
                cv.set(x0 + dx, y0 + dy, cols[ch])


def _art(x0, y0, rows, cols):
    """Character art -> [(x, y, colour)] (for icon_coil emblems)."""
    return [(x0 + dx, y0 + dy, cols[ch])
            for dy, row in enumerate(rows) for dx, ch in enumerate(row) if ch != '.']


# --------------------------------------------------------------------------
# brewed potions
# --------------------------------------------------------------------------

def vigor_draught(g):
    """Round-bottomed flask on a long neck, ruby liquid glowing orange at the
    heart, a herb sprig tied to the neck with twine."""
    C, ramp = g.C, g.ramp
    LIQ = ramp((128, 16, 40), (192, 32, 48), (240, 88, 56), (255, 160, 88), (255, 224, 168))
    glass = ramp((200, 184, 200), (240, 232, 240))
    cork = ramp((136, 88, 48), (192, 136, 80))
    leaf = ramp((32, 120, 48), (96, 184, 64))
    twine = C(224, 184, 112)
    outc = C(72, 12, 24)
    cv = g.Canvas(24, 24)
    cx, cy, rx, ry = 12.0, 16.0, 7.4, 6.2
    body = g.ellipse_mask(cx, cy, rx, ry)
    for (x, y) in body:
        nx, ny = (x + 0.5 - cx) / (rx + 0.4), (y + 0.5 - cy) / (ry + 0.4)
        if y >= 13:
            # lit from inside, the hot spot a little up and left
            b = 1.0 - math.hypot(nx * 1.05 + 0.12, ny * 1.15 + 0.05)
            cv.set(x, y, LIQ[g.quant(b, (0.1, 0.36, 0.6, 0.8))])
        else:
            cv.set(x, y, glass[1] if nx < 0.05 else glass[0])
    for (x, y) in body:
        if y == 13:
            cv.set(x, y, LIQ[3] if x < 15 else LIQ[2])
    # neck with a lip, cork
    g.paint_levels(cv, g.lathe_levels(g.rect_mask(10, 5, 13, 10), th=(0.2, 0.7, 5)), glass)
    g.paint_levels(cv, g.lathe_levels(g.rect_mask(9, 5, 14, 6, r=0), th=(0.2, 0.7, 5)), glass)
    g.paint_levels(cv, g.lathe_levels(g.rect_mask(10, 1, 13, 4, r=1), th=(0.1, 0.6, 5)), cork)
    for x in range(10, 14):
        cv.set(x, 8, twine)
    # glass glints and a rising bubble
    for (x, y) in [(7, 11), (6, 12), (5, 14), (5, 15), (10, 6)]:
        cv.set(x, y, g.WHITE)
    cv.set(14, 17, LIQ[4])
    cv.set(16, 15, LIQ[3])
    # herb sprig tucked under the twine
    _paint(cv, 14, 3, [
        "...ab",
        "..aab",
        ".aab.",
        "aab..",
        "b....",
    ], {'a': leaf[1], 'b': leaf[0]})
    g.outline(cv, outc)
    return cv


def clarity_brew(g):
    """Tall slender vial of clear mint tonic, bubbles, a violet wax seal."""
    C, ramp = g.C, g.ramp
    LIQ = ramp((8, 112, 128), (24, 168, 164), (80, 216, 192), (168, 248, 224))
    glass = ramp((176, 200, 216), (232, 242, 248))
    wax = ramp((80, 32, 128), (136, 72, 192), (192, 136, 240))
    outc = C(8, 48, 64)
    cv = g.Canvas(24, 24)
    cx = 12.0

    def vial(px, py):
        if 8.0 <= py <= 18.5:
            return abs(px - cx) <= 4.0
        if 18.5 < py <= 22.5:
            return math.hypot(px - cx, (py - 18.5) * 1.0) <= 4.0
        if 6.5 <= py < 8.0:
            return abs(px - cx) <= 2.6 + (py - 6.5) * 0.9
        if 3.0 <= py < 6.5:
            return abs(px - cx) <= 2.0
        return False
    m = g.fn_mask(vial, 24, 24)
    lv = g.lathe_levels(m, th=(0.2, 0.6, 0.92))
    for (x, y), l in lv.items():
        if y >= 10:
            cv.set(x, y, LIQ[l])
        else:
            cv.set(x, y, glass[1] if l >= 2 else glass[0])
    for x in range(8, 16):
        if cv.get(x, 10) is not None:
            cv.set(x, 10, LIQ[3] if x < 13 else LIQ[2])
    # a violet wax seal dripping over the lip
    _paint(cv, 9, 0, [
        "..cb..",
        ".ccbb.",
        "cbbbba",
        "bbbbaa",
        "ab.ba.",
        ".a..a.",
    ], {'a': wax[0], 'b': wax[1], 'c': wax[2]})
    # the glass streak and rising bubbles
    for y in range(11, 18):
        cv.set(9, y, g.WHITE if y < 15 else LIQ[3])
    for (x, y) in [(12, 19), (13, 18), (14, 19), (13, 20), (12, 14), (13, 13), (12, 12), (14, 16)]:
        cv.set(x, y, LIQ[3])
    for (x, y) in [(13, 19), (13, 12)]:
        cv.set(x, y, LIQ[0] if y > 15 else LIQ[1])
    cv.set(11, 7, g.WHITE)
    g.outline(cv, outc)
    return cv


def revival_brew(g):
    """Heart-shaped golden flask with a sunrise core and little phoenix
    wings, a flame finial on the stopper."""
    C, ramp = g.C, g.ramp
    LIQ = ramp((200, 48, 24), (240, 112, 32), (255, 184, 56), (255, 232, 144))
    gold = ramp((168, 96, 16), (232, 168, 40), (255, 224, 112))
    outc = C(88, 32, 8)
    cv = g.Canvas(24, 24)
    cx, cy, sx, sy = 12.0, 15.2, 6.1, 5.6

    def heart(px, py):
        u = (px - cx) / sx
        v = -(py - cy) / sy
        return (u * u + v * v - 1) ** 3 - u * u * v ** 3 <= 0
    m = g.fn_mask(heart, 24, 24)
    for (x, y) in m:
        edge = any((x + dx, y + dy) not in m for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if edge:
            # the golden frame, lit from the top-left
            t = (x + 0.5 - cx) + (y + 0.5 - cy) * 1.1
            cv.set(x, y, gold[2] if t < -2 else gold[1] if t < 4.5 else gold[0])
        else:
            d = math.hypot((x + 0.5 - cx + 0.5) / sx, (y + 0.5 - cy + 0.2) / sy)
            cv.set(x, y, LIQ[3 - g.quant(d, (0.28, 0.5, 0.72))])
    for (x, y) in [(8, 11), (7, 12), (11, 14)]:
        cv.set(x, y, g.WHITE)
    # neck, collar and a round stopper with a flame finial
    g.paint_levels(cv, g.lathe_levels(g.rect_mask(10, 6, 13, 9), th=(0.2, 0.7, 5)), gold)
    for x in range(9, 15):
        cv.set(x, 8, gold[2] if x < 11 else gold[1] if x < 14 else gold[0])
    _paint(cv, 10, 0, [
        ".a..",
        ".ab.",
        "abbc",
        "cbcd",
        "ccdd",
        ".dd.",
    ], {'a': LIQ[3], 'b': LIQ[2], 'c': gold[2], 'd': gold[1]})
    # little phoenix wings on the collar, feather tips notched by the outline
    wing = [
        "aa......",
        "abaa....",
        ".bbbaaa.",
        "..bbbbba",
        "...b.bb.",
    ]
    _paint(cv, 1, 2, wing, {'a': gold[2], 'b': gold[1]})
    _paint(cv, 15, 2, [r[::-1] for r in wing], {'a': gold[2], 'b': gold[0]})
    g.outline(cv, outc)
    return cv


# --------------------------------------------------------------------------
# battle coils (g.icon_coil, emblem in the top-right corner)
# --------------------------------------------------------------------------

def swift_coil(g):
    C, ramp = g.C, g.ramp
    wire = ramp((16, 104, 80), (32, 160, 104), (88, 216, 136), (184, 248, 176))
    clip = ramp((200, 152, 16), (248, 216, 64))
    d, l = C(16, 120, 72), C(120, 232, 96)
    em = _art(16, 0, [
        "dl.dl..",
        ".dl.dl.",
        "..dl.dl",
        ".dl.dl.",
        "dl.dl..",
    ], {'d': d, 'l': l})
    return g.icon_coil(wire, C(8, 56, 40), clip, em)


def focus_coil(g):
    C, ramp = g.C, g.ramp
    wire = ramp((104, 24, 128), (160, 48, 176), (216, 104, 216), (248, 184, 248))
    clip = ramp((56, 40, 120), (96, 80, 176))
    o, i, p = C(72, 16, 96), C(224, 64, 176), C(40, 8, 56)
    em = _art(16, 0, [
        "..ooo..",
        ".oWiWo.",
        "oWipiWo",
        ".oWiWo.",
        "..ooo..",
    ], {'o': o, 'i': i, 'p': p, 'W': g.WHITE})
    return g.icon_coil(wire, C(56, 16, 72), clip, em)


def will_coil(g):
    C, ramp = g.C, g.ramp
    wire = ramp((112, 128, 168), (160, 176, 208), (208, 220, 240), (248, 252, 255))
    clip = ramp((184, 64, 104), (240, 120, 152))
    d, m, l = C(176, 32, 80), C(232, 72, 112), C(255, 168, 192)
    em = _art(17, 0, [
        ".m.m.",
        "mlmmm",
        "mmmmd",
        ".mmd.",
        "..d..",
    ], {'d': d, 'm': m, 'l': l})
    return g.icon_coil(wire, C(48, 56, 96), clip, em)


# --------------------------------------------------------------------------
# field supplies
# --------------------------------------------------------------------------

def lure_incense(g):
    """A small brass censer (domed, pierced lid on a footed bowl) and a wisp
    of sweet pink smoke with a heart drifting off it."""
    C, ramp = g.C, g.ramp
    brass = ramp((120, 64, 16), (184, 112, 32), (232, 168, 56), (255, 224, 136))
    smoke = ramp((208, 64, 136), (248, 136, 192), (255, 200, 228))
    outc = C(64, 28, 8)
    cv = g.Canvas(24, 24)
    # bowl (lower half ellipse), stem and foot
    bowl = {(x, y) for (x, y) in g.ellipse_mask(12.0, 13.0, 7.0, 6.0) if 14 <= y <= 18}
    g.paint_levels(cv, g.lathe_levels(bowl, th=(0.15, 0.55, 0.9)), brass)
    for (x, y) in [(7, 15), (7, 16), (8, 17)]:
        cv.set(x, y, brass[3])
    for x in range(10, 14):
        cv.set(x, 19, brass[2] if x < 12 else brass[0])
    for x in range(8, 16):
        cv.set(x, 20, brass[3] if x < 10 else brass[2] if x < 14 else brass[1])
    for x in range(7, 17):
        cv.set(x, 21, brass[1] if x < 14 else brass[0])
    # domed, pierced lid and knob
    lid = {(x, y) for (x, y) in g.ellipse_mask(12.0, 13.0, 5.2, 4.6) if y < 13}
    g.paint_levels(cv, g.lathe_levels(lid, th=(0.15, 0.55, 0.9)), brass)
    for (x, y) in [(9, 11), (12, 11), (15, 11), (10, 9), (13, 9)]:
        cv.set(x, y, brass[0])
    for (x, y, c) in [(11, 7, 3), (12, 7, 2), (11, 8, 2), (12, 8, 1)]:
        cv.set(x, y, brass[c])
    # the rim between them, a little proud of the bowl
    for x in range(4, 20):
        cv.set(x, 13, brass[3] if x < 9 else brass[2] if x < 16 else brass[1])
    for x in range(6, 18):
        cv.set(x, 14, brass[0])
    g.outline(cv, outc)
    # a wisp of sweet smoke rising from the knob, lit edge on the left
    _paint(cv, 9, 0, [
        "..lr..",
        ".lr...",
        ".lr...",
        "..lr..",
        "...lr.",
        "...lr.",
        "..lr..",
    ], {'l': smoke[1], 'r': smoke[0]})
    for (x, y) in [(11, 0), (10, 1)]:
        cv.set(x, y, smoke[2])
    # and a heart drifting off it
    _paint(cv, 16, 2, [
        "ab.bb",
        "abbbb",
        ".abb.",
        "..a..",
    ], {'a': smoke[0], 'b': smoke[1]})
    cv.set(16, 2, smoke[2])
    cv.set(17, 3, smoke[2])
    return cv


def waystone(g):
    """A rough-cut rune stone, one of a tuned pair: flat facets round a broad
    front face carved with a glowing hearth flame."""
    C, ramp = g.C, g.ramp
    stone = ramp((64, 72, 104), (104, 112, 144), (152, 160, 184), (200, 208, 224))
    glow = ramp((224, 88, 16), (255, 160, 40), (255, 232, 144))
    outc = C(32, 32, 56)
    cv = g.Canvas(24, 24)
    outer = [(10.5, 2.0), (15.5, 3.0), (18.8, 8.0), (19.2, 15.5), (16.0, 21.5),
             (8.0, 22.0), (4.6, 16.0), (4.8, 7.5)]
    face = [(10.2, 5.4), (15.0, 6.0), (16.4, 10.0), (16.2, 16.5), (13.8, 19.2),
            (8.6, 19.4), (7.0, 15.4), (7.4, 8.4)]
    om = g.poly_mask(outer, 24, 24)
    fm = g.poly_mask(face, 24, 24)
    cx, cy = 11.8, 12.2
    lx, ly = -0.6, -0.8
    for (x, y) in om:
        if (x, y) in fm:
            cv.set(x, y, stone[2])
            continue
        # which facet: the outer edge nearest to the pixel
        best, bi = 1e9, 0
        for i in range(len(outer)):
            (ax, ay), (bx, by) = outer[i], outer[(i + 1) % len(outer)]
            d, _ = g.seg_dist(x + 0.5, y + 0.5, ax, ay, bx, by)
            if d < best:
                best, bi = d, i
        (ax, ay), (bx, by) = outer[bi], outer[(bi + 1) % len(outer)]
        nx, ny = (ax + bx) / 2 - cx, (ay + by) / 2 - cy
        n = math.hypot(nx, ny) or 1
        b = (nx * lx + ny * ly) / n
        cv.set(x, y, stone[3] if b > 0.3 else stone[1] if b > -0.45 else stone[0])
    # chips and flecks
    for (x, y, c) in [(9, 9, 1), (15, 15, 1), (10, 17, 1), (17, 11, 0), (6, 11, 2), (12, 3, 2)]:
        if cv.get(x, y) is not None:
            cv.set(x, y, stone[c])
    # the hearth rune: a glowing flame over a hearth line
    _paint(cv, 8, 8, [
        "...o...",
        "..oy...",
        "..oyo..",
        ".oyWyo.",
        ".oyWyo.",
        "..ooo..",
        ".......",
        "ooooooo",
    ], {'o': glow[0], 'y': glow[1], 'W': glow[2]})
    g.outline(cv, outc)
    # warm light around it
    for (x, y, c) in [(2, 5, 0), (1, 6, 0), (2, 6, 1), (3, 6, 0), (2, 7, 0),
                      (21, 18, 0), (20, 2, 1), (21, 12, 0), (2, 19, 0)]:
        if cv.get(x, y) is None:
            cv.set(x, y, glow[c])
    return cv


# --------------------------------------------------------------------------
# growth shards (g.icon_shard + a telling detail each)
# --------------------------------------------------------------------------

def hollow_shard(g):
    C, ramp = g.C, g.ramp
    base = ramp((120, 104, 144), (176, 164, 192), (228, 220, 212), (255, 250, 236))
    cv = g.icon_shard(base, C(64, 48, 88))
    # old bone: a crack running down the lit face of the big sliver
    for (x, y) in [(10, 8), (11, 9), (11, 10), (10, 11), (10, 12), (11, 13), (11, 14), (10, 15)]:
        cv.set(x, y, C(96, 80, 120))
    return cv


def relic_shard(g):
    C, ramp = g.C, g.ramp
    base = ramp((128, 64, 24), (184, 108, 40), (228, 160, 72), (252, 216, 152))
    cv = g.icon_shard(base, C(72, 32, 8))
    # verdigris patina creeping up from the foot
    pat = ramp((40, 128, 112), (96, 192, 160))
    for (x, y, c) in [(5, 19, 1), (5, 20, 1), (6, 20, 0), (7, 20, 0), (6, 19, 1),
                      (9, 20, 1), (10, 21, 1), (11, 21, 0), (10, 20, 1), (13, 21, 0), (14, 20, 0),
                      (16, 20, 1), (17, 19, 0), (17, 20, 0), (18, 20, 0)]:
        if cv.get(x, y) not in (None, C(72, 32, 8)):
            cv.set(x, y, pat[c])
    return cv


def metal_shard(g):
    C, ramp = g.C, g.ramp
    base = ramp((72, 92, 128), (120, 140, 176), (176, 192, 224), (232, 238, 252))
    cv = g.icon_shard(base, C(24, 28, 48))
    # the big sliver is the magnetite core: gunmetal dark, steel-sheened
    core = ramp((32, 34, 50), (56, 60, 84), (100, 106, 136), (168, 176, 204))
    cx, yb, yt, hw, lean = 11.8, 21.5, 2.0, 3.4, 0.4     # icon_shard's centre sliver
    pts = [(cx - hw, yb), (cx - hw + lean * 0.7, yt + 3.2), (cx + lean, yt),
           (cx + hw + lean * 0.7, yt + 3.2), (cx + hw, yb)]
    for (x, y) in g.poly_mask(pts, 24, 24):
        v = cv.get(x, y)
        if v in base:
            cv.set(x, y, core[base.index(v)])
    return cv


def astral_shard(g):
    C, ramp = g.C, g.ramp
    base = ramp((32, 32, 96), (56, 64, 160), (104, 120, 224), (184, 196, 255))
    cv = g.icon_shard(base, C(16, 12, 48))
    star = ramp((232, 176, 32), (255, 240, 144))
    # specks of starlight inside, and a star glint
    for (x, y) in [(14, 16), (10, 18), (17, 12), (7, 17)]:
        cv.set(x, y, star[1])
    for (x, y, c) in [(20, 1, 0), (20, 2, 1), (19, 3, 0), (20, 3, 2), (21, 3, 0), (20, 4, 1), (20, 5, 0),
                      (18, 3, 0), (22, 3, 0)]:
        cv.set(x, y, [star[0], star[1], g.WHITE][c])
    return cv


def icons(g):
    return [
        ('VIGOR_DRAUGHT', vigor_draught(g)),
        ('CLARITY_BREW', clarity_brew(g)),
        ('REVIVAL_BREW', revival_brew(g)),
        ('SWIFT_COIL', swift_coil(g)),
        ('FOCUS_COIL', focus_coil(g)),
        ('WILL_COIL', will_coil(g)),
        ('LURE_INCENSE', lure_incense(g)),
        ('WAYSTONE', waystone(g)),
        ('HOLLOW_SHARD', hollow_shard(g)),
        ('RELIC_SHARD', relic_shard(g)),
        ('METAL_SHARD', metal_shard(g)),
        ('ASTRAL_SHARD', astral_shard(g)),
    ]
