"""Bag icons owned by 'fusion' (see tools/icons/__init__.py).

MOTE DUST: the glittering dust a failed weave leaves on the Fusion Loom,
heaped in a little glass dish. 24x24, top-left light, index 1 pure white.
(The ENERGY FLASK key item's icon is drawn by icons_ui.py.)
"""


def icon_mote_dust(g):
    C, W = g.C, g.WHITE
    dust = g.ramp((120, 56, 150), (190, 96, 200), (236, 150, 224), (255, 214, 246))
    dish = g.ramp((96, 132, 168), (150, 190, 220), (206, 230, 244))
    outc = C(40, 28, 64)
    cv = g.Canvas(24, 24)
    # the dish: a shallow ellipse
    for (x, y) in g.ellipse_mask(11.5, 17.5, 10.0, 4.0):
        cv.set(x, y, dish[2] if y < 16 else dish[1] if x < 14 else dish[0])
    # the heap of dust on it
    for y in range(24):
        for x in range(24):
            dx = (x + 0.5 - 11.5) / 7.5
            top = 16.5 - 8.0 * max(0.0, 1.0 - dx * dx) ** 0.8
            if abs(dx) <= 1.0 and top <= y + 0.5 <= 17.0:
                h = (16.5 - (y + 0.5)) / 8.0
                k = 3 if (x * 7 + y * 13) % 11 == 0 else (2 if h > 0.55 or dx < -0.3 else 1 if dx < 0.4 else 0)
                cv.set(x, y, dust[k])
    g.outline(cv, outc)
    # sparkles drifting up
    for (sx, sy) in ((5, 4), (17, 3), (19, 8)):
        for (dx, dy) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            cv.set(sx + dx, sy + dy, W if (dx, dy) == (0, 0) else dust[3])
    cv.set(9, 6, dust[2])
    cv.set(14, 2, dust[2])
    return cv


def icons(g):
    return [('MOTE_DUST', icon_mote_dust(g))]
