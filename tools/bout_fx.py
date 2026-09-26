"""Move-effect particles for the expansion moves (HOLLOW, RELIC, METAL,
ASTRAL and the new moves of the old types), drawn with the helpers of
tools/gen_battle_gfx.py and appended after its own particles.

    fx(g)     -> [(NAME, Canvas16), ...]   becomes FX_NAME
    fx_big(g) -> [(NAME, Canvas32), ...]   becomes FXB_NAME

Same value ramp as every particle: 1 darkest/outline, 2 dark, 3 mid (the
move's main colour), 4 light, 5 highlight, 6 white-hot, 7/8/9 secondary
dark/mid/light. Light comes from the top-left.
"""

import math


def _shade(g, cv, mask, cx, cy, rx, ry, lv=(2, 3, 4, 5), th=(-0.1, 0.4, 0.8)):
    for (x, y) in mask:
        nx = max(-1.0, min(1.0, (x + 0.5 - cx) / rx))
        ny = max(-1.0, min(1.0, (y + 0.5 - cy) / ry))
        cv.set(x, y, lv[g.quant(g.sphere_b(nx, ny), th)])


def _clip(mask, w=16, h=16):
    return {(x, y) for (x, y) in mask if 0 <= x < w and 0 <= y < h}


def fx_bone(g):
    """A bone shard: a shaft with two knobbly ends, on the diagonal."""
    cv = g.Canvas(16, 16)
    ax, ay, bx, by = 4.2, 11.8, 11.8, 4.2
    L = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / L, (by - ay) / L
    nx, ny = -uy, ux

    def inside(px, py):
        d, t = g.seg_dist(px, py, ax, ay, bx, by)
        if d <= 1.45:
            return True
        for (ex, ey, s) in ((ax, ay, -1), (bx, by, 1)):
            for side in (-1, 1):
                kx = ex + ux * s * 0.9 + nx * side * 1.55
                ky = ey + uy * s * 0.9 + ny * side * 1.55
                if math.hypot(px - kx, py - ky) <= 1.9:
                    return True
        return False
    m = g.fn_mask(inside)
    dist = g.inner_dist(m)
    for (x, y), d in dist.items():
        # light side = toward the top-left of the shaft
        side = (x + 0.5 - 8.0) * nx + (y + 0.5 - 8.0) * ny
        cv.set(x, y, 5 if d >= 2 and side < 0.3 else 4 if d >= 2 else 3 if side < 0 else 2)
    for (x, y) in [(6, 8), (7, 7), (8, 6)]:
        cv.set(x, y, 6)
    g.fx_outline(cv, 1)
    return cv


def fx_skull(g):
    """A small, friendly skull with glowing eye sockets."""
    cv = g.Canvas(16, 16)
    head = g.ellipse_mask(7.5, 6.6, 5.6, 5.2) | g.rect_mask(4, 9, 11, 12, 1)
    head = _clip(head)
    _shade(g, cv, head, 7.5, 7.0, 6.2, 6.6, (3, 4, 5, 5), (-0.3, 0.2, 0.7))
    for (x, y) in head:
        if y >= 12 and x in (5, 7, 9):
            cv.set(x, y, 2)                      # teeth gaps
    for ex in (5.2, 9.9):
        for (x, y) in g.ellipse_mask(ex, 8.0, 1.5, 1.6):
            cv.set(x, y, 7)
        cv.set(int(ex), 8, 9)
    for (x, y) in [(7, 10), (8, 10)]:
        cv.set(x, y, 2)                          # nose
    for (x, y) in [(4, 3), (5, 2), (6, 2)]:
        cv.set(x, y, 6)
    g.fx_outline(cv, 1)
    return cv


def fx_rivet(g):
    """A glowing hot rivet: domed head and a short shank."""
    cv = g.Canvas(16, 16)
    headm = {(x, y) for (x, y) in g.ellipse_mask(7.5, 8.0, 6.4, 4.2) if y <= 8}
    _shade(g, cv, headm, 6.0, 8.0, 6.6, 4.4, (2, 3, 4, 5), (-0.2, 0.35, 0.78))
    for x in range(1, 15):
        if (x, 8) in headm:
            cv.set(x, 8, 2)
    for y in range(9, 15):
        for x in range(6, 10):
            cv.set(x, y, 7 if x == 9 else 9 if y >= 12 and x < 8 else 8)
    for (x, y) in [(7, 14), (8, 14)]:
        cv.set(x, y, 6)                              # white-hot tip
    for (x, y) in [(3, 5), (4, 5), (5, 4)]:
        cv.set(x, y, 6)
    g.fx_outline(cv, 1)
    return cv


def fx_gear(g):
    """A cog with eight teeth and an axle hole."""
    cv = g.Canvas(16, 16)
    cx = cy = 7.5
    m = set()
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(px, py)
            a = math.degrees(math.atan2(py, px)) + 11.25
            tooth = (a % 45.0) < 22.5
            if d <= (7.4 if tooth else 5.6) and d > 1.9:
                m.add((x, y))
    _shade(g, cv, m, cx, cy, 7.4, 7.4, (2, 3, 4, 5), (-0.25, 0.3, 0.75))
    for (x, y) in m:
        d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
        if 2.0 < d < 3.2:
            cv.set(x, y, 2 if x + y > 15 else 4)    # hub ring
    g.fx_outline(cv, 1)
    return cv


def fx_coin(g):
    """A gilt coin, a little tilted, with a star stamped on it."""
    cv = g.Canvas(16, 16)
    cx, cy, rx, ry = 7.5, 7.5, 5.4, 6.6
    m = g.ellipse_mask(cx, cy, rx, ry)
    for (x, y) in m:
        px, py = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
        r = math.hypot(px, py)
        if r > 0.78:
            cv.set(x, y, 3 if px + py > 0.2 else 4)
        else:
            cv.set(x, y, 4 if px + py > 0.35 else 5)
    for (x, y) in g.poly_mask(g.star_poly(7.5, 7.8, [3.3 if i % 2 == 0 else 1.4 for i in range(10)],
                                          rot=-math.pi / 2), 16, 16):
        if (x, y) in m:
            cv.set(x, y, 3)
    for (x, y) in [(4, 4), (4, 5), (5, 3)]:
        cv.set(x, y, 6)
    g.fx_outline(cv, 1)
    return cv


def fx_mote(g):
    """A star mote: a round glowing core with four long, thin rays."""
    cv = g.Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5 - 8.0, y + 0.5 - 8.0
            d = math.hypot(px, py)
            if d <= 1.6:
                cv.set(x, y, 6)
            elif d <= 2.6:
                cv.set(x, y, 5)
            elif (abs(px) < 0.6 and abs(py) < 7.6) or (abs(py) < 0.6 and abs(px) < 7.6):
                cv.set(x, y, 5 if max(abs(px), abs(py)) < 4.6 else 4)
    for (x, y) in [(5, 5), (10, 5), (5, 10), (10, 10)]:
        cv.set(x, y, 9)
    g.fx_outline(cv, 8)
    return cv


def fx_bell(g):
    """A bronze bell with a clapper."""
    cv = g.Canvas(16, 16)

    def inside(px, py):
        if py < 1.6 or py > 12.6:
            return False
        if py < 4.4:
            return math.hypot(px - 8.0, (py - 4.4) * 1.3) <= 3.4
        t = (py - 4.4) / 8.2
        hw = 3.4 + 3.2 * t ** 1.8
        return abs(px - 8.0) <= hw
    m = g.fn_mask(inside)
    for (x, y) in m:
        rel = (x + 0.5 - 8.0) / 6.6
        cv.set(x, y, 5 if rel < -0.35 else 4 if rel < 0.05 else 3 if rel < 0.45 else 2)
        if y >= 11:
            cv.set(x, y, 3 if rel < 0.3 else 2)      # the lip
    for (x, y) in [(7, 0), (8, 0), (7, 1), (8, 1)]:
        cv.set(x, y, 2)                              # hanger
    for (x, y) in [(7, 13), (8, 13), (7, 14), (8, 14)]:
        cv.set(x, y, 8 if y == 13 else 7)            # clapper
    for (x, y) in [(5, 5), (5, 6), (5, 7)]:
        cv.set(x, y, 6)
    g.fx_outline(cv, 1)
    return cv


def fx_cup(g):
    """A flying teacup with a handle and a painted band."""
    cv = g.Canvas(16, 16)

    def body(px, py):
        if not (4.2 <= py <= 12.4):
            return False
        t = (py - 4.2) / 8.2
        return abs(px - 7.0) <= 5.4 - 1.6 * t ** 2
    m = g.fn_mask(body)
    for (x, y) in m:
        rel = (x + 0.5 - 7.0) / 5.4
        cv.set(x, y, 6 if rel < -0.45 else 5 if rel < 0.1 else 4 if rel < 0.55 else 3)
        if y in (7, 8):
            cv.set(x, y, 8 if rel < 0.4 else 7)      # painted band
    for x in range(2, 13):
        if (x, 4) in m:
            cv.set(x, 4, 2)                          # tea inside the rim
    for (x, y) in [(13, 6), (14, 7), (14, 8), (13, 9), (12, 10)]:
        cv.set(x, y, 4)                              # handle
    for x in range(1, 14):
        cv.set(x, 13, 3 if x > 9 else 4)             # saucer
    for x in range(3, 12):
        cv.set(x, 14, 2)
    g.fx_outline(cv, 1)
    return cv


def fx_moon(g):
    """A crescent moon with a soft glow edge."""
    cv = g.Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5, y + 0.5
            a = math.hypot(px - 7.2, py - 8.0) <= 6.6
            b = math.hypot(px - 10.2, py - 6.2) <= 5.6
            if a and not b:
                d = math.hypot(px - 10.2, py - 6.2) - 5.6
                cv.set(x, y, 6 if d < 1.2 else 5 if d < 2.6 else 4)
    for (x, y) in [(4, 11), (6, 12)]:
        if cv.get(x, y) is not None:
            cv.set(x, y, 3)                          # a crater or two
    g.fx_outline(cv, 9)
    return cv


def fx_flake(g):
    """Rust flakes and metal shavings: three small tumbling chips."""
    cv = g.Canvas(16, 16)
    chips = [[(2.0, 3.0), (6.8, 1.6), (7.4, 5.0), (3.2, 6.2)],
             [(9.0, 6.0), (14.2, 7.8), (12.4, 11.0), (8.6, 9.4)],
             [(2.6, 10.6), (6.4, 10.0), (5.6, 14.2), (1.8, 13.4)]]
    for i, pts in enumerate(chips):
        m = g.poly_mask(pts, 16, 16)
        for (x, y) in m:
            top = y + 0.5 < sum(p[1] for p in pts) / 4
            cv.set(x, y, (4 if top else 3) if i != 1 else (8 if top else 7))
    for (x, y) in [(4, 3), (11, 7)]:
        cv.set(x, y, 6)
    g.fx_outline(cv, 1)
    return cv


def fx_trinket(g):
    """A trinket: an old key on a ring with a locket."""
    cv = g.Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + 0.5 - 4.8, y + 0.5 - 4.8)
            if 1.6 <= d <= 3.4:
                cv.set(x, y, 5 if x + y < 9 else 3)  # key bow (ring)
    for k in range(9):
        x, y = 6 + k, 6 + k
        if x < 16 and y < 16:
            cv.set(x, y, 4)
            cv.set(x, y - 1, 5) if y - 1 >= 0 else None
    for (x, y) in [(11, 12), (12, 12), (12, 13), (13, 10), (14, 10), (14, 11)]:
        cv.set(x, y, 3)                              # key bits
    for (x, y) in g.ellipse_mask(11.0, 4.0, 2.4, 2.8):
        cv.set(x, y, 8 if x + y < 15 else 7)         # a little locket
    cv.set(10, 3, 9)
    g.fx_outline(cv, 1)
    return cv


def fx_magnet(g):
    """A horseshoe magnet: painted body, bright steel poles."""
    cv = g.Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5 - 8.0, y + 0.5 - 7.0
            d = math.hypot(px, py)
            if py <= 0 and 2.4 <= d <= 6.4:
                cv.set(x, y, 5 if d > 5.3 and px < 0 else 4 if px < -1 else 3)
            elif py > 0 and (2.4 <= abs(px) <= 6.4) and py <= 7.2:
                pole = py > 3.6
                left = px < 0
                cv.set(x, y, (9 if left else 8) if pole else (4 if left else 3))
    for (x, y) in [(3, 4), (4, 3)]:
        cv.set(x, y, 6)
    g.fx_outline(cv, 1)
    return cv


def fx_streak(g):
    """A thin vertical streak of light (tiles vertically, like FX_BOLT)."""
    cv = g.Canvas(16, 16)
    for y in range(16):
        for x in (7, 8):
            cv.set(x, y, 6 if x == 7 else 5)
        if y % 5 != 2:
            cv.set(6, y, 4)
            cv.set(9, y, 3)
    for y in (3, 11):
        cv.set(5, y, 9)
        cv.set(10, y + 2, 9)
    return cv


def fx_candle(g):
    """A grave candle: wax stub, a drip and a small steady flame."""
    cv = g.Canvas(16, 16)
    for y in range(8, 15):
        for x in range(5, 11):
            cv.set(x, y, 5 if x == 6 else 3 if x == 10 else 4)
    for (x, y) in [(5, 8), (5, 9), (5, 10), (9, 8), (9, 9)]:
        cv.set(x, y, 6)                              # drips
    cv.set(8, 7, 2)                                  # wick
    for (x, y, c) in [(8, 1, 7), (7, 2, 8), (8, 2, 8), (7, 3, 8), (8, 3, 9), (9, 3, 7), (6, 4, 7),
                      (7, 4, 9), (8, 4, 9), (9, 4, 8), (7, 5, 9), (8, 5, 6), (8, 6, 8)]:
        cv.set(x, y, c)
    g.fx_outline(cv, 1)
    return cv


def fx_bug(g):
    """A buzzing beetle seen from above, wings a blur."""
    cv = g.Canvas(16, 16)
    body = g.ellipse_mask(8.0, 9.0, 3.4, 4.6)
    _shade(g, cv, body, 8.0, 9.0, 3.6, 4.8, (2, 3, 4, 5), (-0.2, 0.3, 0.75))
    for y in range(6, 14):
        if (8, y) in body:
            cv.set(8, y, 2)                          # wing-case seam
    for (x, y) in g.ellipse_mask(8.0, 4.0, 2.0, 1.6):
        cv.set(x, y, 2)                              # head
    for (x, y) in [(6, 2), (5, 1), (10, 2), (11, 1)]:
        cv.set(x, y, 1)                              # feelers
    for (x, y) in g.ellipse_mask(3.6, 6.8, 2.8, 2.0) | g.ellipse_mask(12.4, 6.8, 2.8, 2.0):
        if cv.get(x, y) is None:
            cv.set(x, y, 9 if (x + y) % 2 else 8)    # wing blur
    for (x, y) in [(6, 7), (7, 6)]:
        cv.set(x, y, 6)
    g.fx_outline(cv, 1)
    return cv


def fx_scale(g):
    """A wyrm scale: a pointed shield shape with a ridge."""
    cv = g.Canvas(16, 16)

    def inside(px, py):
        if py < 2.0 or py > 14.4:
            return False
        if py < 8.0:
            return abs(px - 8.0) <= 6.0 * math.sqrt(max(0.0, 1 - ((8.0 - py) / 6.2) ** 2))
        t = (py - 8.0) / 6.4
        return abs(px - 8.0) <= 6.0 * (1 - t) ** 0.9
    m = g.fn_mask(inside)
    for (x, y) in m:
        rel = x + 0.5 - 8.0
        cv.set(x, y, 5 if rel < -2.5 else 4 if rel < 0 else 3 if rel < 2.8 else 2)
    for y in range(4, 13):
        cv.set(8, y, 8 if y < 9 else 7)              # ridge
    for (x, y) in [(4, 5), (5, 4)]:
        cv.set(x, y, 6)
    g.fx_outline(cv, 1)
    return cv


def fx(g):
    return [
        ("BONE", fx_bone(g)), ("SKULL", fx_skull(g)), ("RIVET", fx_rivet(g)), ("GEAR", fx_gear(g)),
        ("COIN", fx_coin(g)), ("MOTE", fx_mote(g)), ("BELL", fx_bell(g)), ("CUP", fx_cup(g)),
        ("MOON", fx_moon(g)), ("FLAKE", fx_flake(g)), ("TRINKET", fx_trinket(g)), ("MAGNET", fx_magnet(g)),
        ("STREAK", fx_streak(g)), ("CANDLE", fx_candle(g)), ("BUG", fx_bug(g)), ("SCALE", fx_scale(g)),
    ]


# ---- big 32x32 particles ------------------------------------------------------

def fxb_anvil(g):
    """A blacksmith's anvil, drawn big: horn to the left, heel to the right."""
    cv = g.Canvas(32, 32)
    top = g.poly_mask([(2.0, 9.0), (8.0, 8.0), (30.0, 8.0), (30.0, 14.0), (22.0, 15.0),
                       (10.0, 15.0), (6.0, 13.0), (2.0, 10.6)], 32, 32)
    waist = g.poly_mask([(11.0, 15.0), (21.0, 15.0), (19.0, 21.0), (13.0, 21.0)], 32, 32)
    foot = g.poly_mask([(7.0, 25.0), (13.0, 21.0), (19.0, 21.0), (25.0, 25.0), (25.0, 28.0), (7.0, 28.0)], 32, 32)
    for (x, y) in top:
        cv.set(x, y, 5 if y <= 9 else 4 if y <= 11 else 3 if x < 24 else 2)
    for (x, y) in waist:
        cv.set(x, y, 3 if x < 15 else 2)
    for (x, y) in foot:
        cv.set(x, y, 4 if y <= 23 and x < 16 else 3 if x < 18 else 2)
    for x in range(8, 30):
        cv.set(x, 8, 6)                                  # the polished face
    for (x, y) in [(3, 9), (4, 9), (5, 8)]:
        cv.set(x, y, 6)
    for (x, y) in [(26, 10), (27, 10), (26, 11), (27, 11)]:
        cv.set(x, y, 2)                                  # hardy hole
    g.fx_outline(cv, 1)
    return cv


def fxb_chest(g):
    """A mimic's lid: a banded chest lid with a row of teeth along its lower
    edge. Drawn upright it is the upper jaw; flipped, the lower jaw."""
    cv = g.Canvas(32, 32)

    def lid(px, py):
        if not (4.0 <= px <= 28.0):
            return False
        arch = 6.0 + 5.0 * ((px - 16.0) / 12.0) ** 2
        return arch <= py <= 20.0
    m = g.fn_mask(lid, 32, 32)
    for (x, y) in m:
        band = x in (9, 10, 21, 22)
        if band:
            cv.set(x, y, 8 if x in (9, 21) else 7)
        else:
            cv.set(x, y, 5 if y < 10 and x < 20 else 4 if x < 22 else 3)
        if y >= 18:
            cv.set(x, y, 8 if band else 2)               # the rim
    for k in range(6):                                   # teeth
        x0 = 6 + k * 4
        for dy in range(4):
            for dx in range(3 - (dy + 1) // 2):
                cv.set(x0 + dx + (dy + 1) // 4, 21 + dy, 6 if dx == 0 else 4)
    for (x, y) in [(15, 14), (16, 14), (15, 15), (16, 15), (15, 16), (16, 16)]:
        cv.set(x, y, 9 if y == 14 else 8)                # lock plate
    g.fx_outline(cv, 1)
    return cv


def fx_big(g):
    return [("ANVIL", fxb_anvil(g)), ("CHEST", fxb_chest(g))]
