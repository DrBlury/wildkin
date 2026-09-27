"""Bag icons owned by 'travel' (see tools/icons/__init__.py): the RUNESTONE."""

import math

# the OTHALA rune (home), 7x9, carved into the stone
OTHALA = [
    '...#...',
    '..#.#..',
    '.#...#.',
    '..#.#..',
    '...#...',
    '..#.#..',
    '.#...#.',
    '#.....#',
]


def icon_runestone(g):
    """A smooth slate river stone with a glowing OTHALA (home) rune."""
    C, W = g.C, g.WHITE
    stone = g.ramp((40, 44, 72), (66, 72, 108), (100, 106, 146), (146, 154, 190))
    glow = g.ramp((120, 72, 216), (96, 208, 252), (200, 248, 255))
    outc = C(24, 20, 44)
    cv = g.Canvas(24, 24)
    cx, cy, rx, ry = 11.5, 12.5, 9.2, 10.2
    for (x, y) in g.ellipse_mask(cx, cy, rx, ry):
        nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        lit = -0.6 * nx - 0.75 * ny + 0.35 * math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
        k = 0 if lit < -0.25 else 1 if lit < 0.15 else 2 if lit < 0.5 else 3
        cv.set(x, y, stone[k])
    ox, oy = 9, 8
    carved = set()
    for y, row in enumerate(OTHALA):
        for x, ch in enumerate(row):
            if ch == '#':
                carved.add((ox + x, oy + y))
    groove = C(36, 32, 64)
    for (x, y) in carved:                      # the cut, shadowed down-right
        if (x + 1, y + 1) not in carved:
            cv.set(x + 1, y + 1, groove)
    for (x, y) in carved:                      # a violet glow beside the strokes
        for dx, dy in ((-1, 0), (1, 0)):
            p = (x + dx, y + dy)
            if p not in carved and cv.get(*p) not in (groove,):
                cv.set(p[0], p[1], glow[0])
    for (x, y) in carved:
        cv.set(x, y, glow[1])
    for (x, y) in ((ox + 3, oy), (ox + 3, oy + 4), (ox, oy + 7), (ox + 6, oy + 7)):
        cv.set(x, y, glow[2])
    g.outline(cv, outc)
    for (x, y) in ((6, 5), (7, 4), (8, 4)):
        cv.set(x, y, W)
    return cv


def icons(g):
    return [
        ('RUNESTONE', icon_runestone(g)),
    ]
