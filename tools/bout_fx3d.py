"""Particles for the pseudo-3D battle animations (src/game/anim3d.c): shapes
meant to be spun, tumbled and laid flat on the ground by OBJ affine
matrices. Drawn with the helpers of tools/gen_battle_gfx.py and appended
after tools/bout_fx.py's particles.

    fx(g)     -> [(NAME, Canvas16), ...]   becomes FX_NAME
    fx_big(g) -> [(NAME, Canvas32), ...]   becomes FXB_NAME

Same value ramp as every particle: 1 darkest/outline, 2 dark, 3 mid (the
move's main colour), 4 light, 5 highlight, 6 white-hot, 7/8/9 secondary
dark/mid/light. Light comes from the top-left. Shapes that get rotated are
drawn centred on (8, 8) / (16, 16) so they spin in place.
"""

import math


def _ring_mask(cx, cy, r0, r1, w=16, h=16):
    return {(x, y) for y in range(h) for x in range(w)
            if r0 <= math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r1}


def fx_shadow(g):
    """A soft round shadow (drawn flat and semi-transparent under things in
    the air): a solid core with a dithered rim."""
    cv = g.Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + 0.5 - 8.0, y + 0.5 - 8.0)
            if d <= 5.2 or (d <= 7.2 and (x + y) & 1 == 0):
                cv.set(x, y, 1)
    return cv


def fx_ember(g):
    """A small hot ember: white core, bright body, a dithered glow."""
    cv = g.Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + 0.5 - 8.0, y + 0.5 - 8.0)
            if d <= 1.5:
                cv.set(x, y, 6)
            elif d <= 2.7:
                cv.set(x, y, 5)
            elif d <= 3.7:
                cv.set(x, y, 4)
            elif d <= 5.0 and (x + y) & 1 == 0:
                cv.set(x, y, 3)
            elif d <= 6.2 and (x & 1) == 0 and (y & 1) == 0:
                cv.set(x, y, 8)
    return cv


def fx_petal(g):
    """A petal, pointing up-right, with a pale vein: tumbles well."""
    cv = g.Canvas(16, 16)
    ang = -math.pi / 4

    def inside(px, py):
        u, v = g.rot_uv(px, py, 8.0, 8.0, ang)
        # teardrop along u: round at -u, pointed at +u
        t = (u + 6.0) / 12.0
        if not 0.0 <= t <= 1.0:
            return False
        half = 3.6 * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.8 * (1.0 - 0.35 * t)
        return abs(v) <= half
    m = g.fn_mask(inside)
    for (x, y) in m:
        u, v = g.rot_uv(x + 0.5, y + 0.5, 8.0, 8.0, ang)
        b = -v * 0.25 - u * 0.05
        cv.set(x, y, 5 if b > 0.55 else 4 if b > -0.1 else 3 if b > -0.6 else 2)
    for i in range(-4, 5):
        u = i * 1.0
        x = int(8.0 + u * math.cos(ang) + 0.2)
        y = int(8.0 + u * math.sin(ang) + 0.2)
        if (x, y) in m:
            cv.set(x, y, 9 if i < 2 else 6)
    g.fx_outline(cv, 1)
    return cv


def fx_crescent(g):
    """A crescent blade of light, opening to the right: spun, it is a slash
    that turns as it sweeps."""
    cv = g.Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5, y + 0.5
            outer = math.hypot(px - 7.0, py - 8.0) <= 6.8
            inner = math.hypot(px - 9.6, py - 8.0) <= 6.0
            if outer and not inner:
                e = math.hypot(px - 9.6, py - 8.0) - 6.0      # depth from the inner edge
                tip = abs(py - 8.0) / 6.8
                cv.set(x, y, 6 if e < 0.9 and tip < 0.7 else 5 if e < 1.8 else 4 if tip < 0.8 else 3)
    g.fx_outline(cv, 2)
    return cv


def fx_swirl(g):
    """One arm of a vortex: a comma-shaped stroke curling round the centre.
    Several copies turned about the middle make a whirlpool."""
    cv = g.Canvas(16, 16)
    pts = []
    for i in range(25):
        t = i / 24.0
        a = 0.3 + t * 3.6
        r = 1.6 + t * 5.4
        pts.append((8.0 + r * math.cos(a), 8.0 + r * math.sin(a)))
    g.stroke(cv, pts, lambda s: 0.9 + 2.6 * g.sinp(min(1.0, s * 1.25)), [(0.4, 6), (0.75, 5), (1.0, 4)])
    g.fx_outline(cv, 3)
    return cv


def fx_splash(g):
    """A crown of spray thrown up where something lands."""
    cv = g.Canvas(16, 16)
    # the basin
    for y in range(11, 15):
        for x in range(2, 14):
            if ((x + 0.5 - 8.0) / 6.0) ** 2 + ((y + 0.5 - 12.5) / 2.0) ** 2 <= 1.0:
                cv.set(x, y, 4 if y == 11 else 3 if y < 14 else 2)
    # jets and drops
    for (x0, lean, h) in [(3, -1, 5), (6, -0.4, 8), (9, 0.4, 8), (12, 1, 5)]:
        for k in range(h):
            x = int(round(x0 + lean * k * 0.5))
            y = 11 - k
            cv.set(x, y, 5 if k < h - 2 else 6)
    for (x, y) in [(2, 3), (7, 1), (13, 2), (10, 0), (4, 6)]:
        cv.set(x, y, 9)
    g.fx_outline(cv, 1)
    return cv


def fx_glow(g):
    """A soft round glow (16px): white core, dithered falloff; light cores,
    flares at the tips of beams and charges."""
    cv = g.Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + 0.5 - 8.0, y + 0.5 - 8.0)
            dither = (x + y) & 1 == 0
            if d <= 2.4:
                cv.set(x, y, 6)
            elif d <= 3.6:
                cv.set(x, y, 5 if d > 3.1 and dither else 6)
            elif d <= 5.0:
                cv.set(x, y, 5 if d <= 4.4 or dither else 4)
            elif d <= 6.4:
                cv.set(x, y, 4 if d <= 5.8 or dither else 3)
            elif d <= 7.6 and dither:
                cv.set(x, y, 3)
    return cv


def fx_hex(g):
    """A bevelled hexagonal plate: the tiles of a shield dome."""
    cv = g.Canvas(16, 16)
    pts = [(8.0 + 6.9 * math.cos(math.pi / 3 * k + math.pi / 6),
            8.0 + 6.9 * math.sin(math.pi / 3 * k + math.pi / 6)) for k in range(6)]
    m = g.poly_mask(pts, 16, 16)
    dist = g.inner_dist(m)
    for (x, y), d in dist.items():
        px, py = x + 0.5 - 8.0, y + 0.5 - 8.0
        if d <= 1:
            cv.set(x, y, 5 if px + py < -1 else 2 if px + py > 2 else 4)
        elif d == 2:
            cv.set(x, y, 4 if px + py < 0 else 3)
        else:
            cv.set(x, y, 8 if px - py > 2 else 9 if px + py < -3 else 3)
    for (x, y) in [(5, 6), (6, 5), (6, 6)]:
        cv.set(x, y, 6)
    g.fx_outline(cv, 1)
    return cv


def fx_chunk(g):
    """An angular chip of debris (stone, ice, metal): faceted, reads at any
    angle while it tumbles."""
    cv = g.Canvas(16, 16)
    pts = [(3.2, 6.0), (7.4, 2.6), (12.8, 4.4), (13.0, 9.6), (9.2, 13.2), (4.0, 11.4)]
    m = g.poly_mask(pts, 16, 16)
    for (x, y) in m:
        px, py = x + 0.5, y + 0.5
        if px + py < 12.5:
            v = 5 if px + py < 10.0 else 4
        elif px - py > 3.5:
            v = 3
        elif py > 9.5:
            v = 2
        else:
            v = 3 if px > 8.5 else 4
        cv.set(x, y, v)
    for (x, y) in [(7, 4), (8, 4), (6, 5)]:
        cv.set(x, y, 6)
    for (x, y) in [(9, 8), (10, 9), (10, 10)]:
        cv.set(x, y, 8)
    g.fx_outline(cv, 1)
    return cv


def fx_prism(g):
    """A glass prism (triangle) with coloured facets: it splits light."""
    cv = g.Canvas(16, 16)
    pts = [(8.0, 1.2), (14.6, 13.6), (1.4, 13.6)]
    m = g.poly_mask(pts, 16, 16)
    dist = g.inner_dist(m)
    for (x, y), d in dist.items():
        px = x + 0.5
        if d <= 1:
            cv.set(x, y, 6 if px < 8 else 5)
        else:
            cv.set(x, y, 9 if px < 6.5 else 4 if px < 9.5 else 8)
    for (x, y) in [(7, 5), (7, 6), (6, 8)]:
        cv.set(x, y, 6)
    g.fx_outline(cv, 2)
    return cv


def fx(g):
    return [
        ("SHADOW", fx_shadow(g)), ("EMBER", fx_ember(g)), ("PETAL", fx_petal(g)),
        ("CRESCENT", fx_crescent(g)), ("SWIRL", fx_swirl(g)), ("SPLASH", fx_splash(g)),
        ("GLOW", fx_glow(g)), ("HEX", fx_hex(g)), ("CHUNK", fx_chunk(g)), ("PRISM", fx_prism(g)),
    ]


# ---- big 32x32 particles ------------------------------------------------------

def fxb_wave(g):
    """A shockwave: a bright leading ring with a dithered wake inside it.
    Laid flat on the ground it races outward."""
    cv = g.Canvas(32, 32)
    for y in range(32):
        for x in range(32):
            d = math.hypot(x + 0.5 - 16.0, y + 0.5 - 16.0)
            dither = (x + y) & 1 == 0
            if 13.2 <= d <= 15.4:
                cv.set(x, y, 6 if 13.8 <= d <= 14.8 else 5)
            elif 11.6 <= d < 13.2:
                cv.set(x, y, 4)
            elif 9.4 <= d < 11.6 and dither:
                cv.set(x, y, 3)
            elif 7.0 <= d < 9.4 and (x & 1) == 0 and (y & 1) == 0:
                cv.set(x, y, 2)
    return cv


def fxb_vortex(g):
    """A three-armed whirlpool seen from above; spun and squashed it lies
    on the ground and turns."""
    cv = g.Canvas(32, 32)
    for arm in range(3):
        pts = []
        for i in range(33):
            t = i / 32.0
            a = arm * 2 * math.pi / 3 + t * 4.2
            r = 2.0 + t * 13.4
            pts.append((16.0 + r * math.cos(a), 16.0 + r * math.sin(a)))
        g.stroke(cv, pts, lambda s: 1.0 + 3.6 * g.sinp(min(1.0, 0.15 + s)), [(0.35, 6), (0.7, 5), (1.0, 4)],
                 only_empty=True)
    for y in range(32):
        for x in range(32):
            d = math.hypot(x + 0.5 - 16.0, y + 0.5 - 16.0)
            if d <= 2.4:
                cv.set(x, y, 2)
            elif cv.get(x, y) is None and d <= 14.5 and (x + y) % 4 == 0:
                cv.set(x, y, 8)
    g.fx_outline(cv, 3, skip=(8,))
    return cv


def fxb_flare(g):
    """A four-pointed flare with a round glow: the flash of a big hit or a
    released charge (spun slowly)."""
    cv = g.Canvas(32, 32)

    def ray(u, v, length, width):
        """Inside a tapered ray along u (both ways), width at the root."""
        au = abs(u)
        return au <= length and abs(v) <= width * (1.0 - au / length) ** 1.15

    r2 = math.sqrt(0.5)
    for y in range(32):
        for x in range(32):
            px, py = x + 0.5 - 16.0, y + 0.5 - 16.0
            d = math.hypot(px, py)
            du, dv = (px + py) * r2, (px - py) * r2
            main = ray(px, py, 15.8, 3.6) or ray(py, px, 15.8, 3.6)
            diag = ray(du, dv, 10.5, 2.4) or ray(dv, du, 10.5, 2.4)
            if d <= 3.2:
                cv.set(x, y, 6)
            elif main:
                cv.set(x, y, 6 if d < 7.0 else 5 if d < 11.0 else 4)
            elif diag:
                cv.set(x, y, 5 if d < 5.5 else 4)
            elif d <= 6.2:
                cv.set(x, y, 5 if d < 4.6 else 4 if (x + y) & 1 == 0 else 3)
            elif d <= 8.0 and (x + y) & 1 == 0:
                cv.set(x, y, 3)
    return cv


def fx_big(g):
    return [("WAVE", fxb_wave(g)), ("VORTEX", fxb_vortex(g)), ("FLARE", fxb_flare(g))]
