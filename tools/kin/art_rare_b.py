"""Art for kin 107-112 (KIN-R2).

One model function per species (the lowercase species name), called by
tools/gen_monsters.py as fn(g) with g = the gen_monsters module. Coordinates:
+Y up, +Z the way the kin faces, +X its left; the ground is y = 0.

The three rare lines each carry one glowing "soul" material: the ghost-teal
light inside the haunted armour, the candle / lantern fire, and the molten
heat in the meteor cracks.
"""

import math

DEG = math.pi / 180.0


# ---- small vector helpers (stdlib only; gen_monsters is passed in as g) ----
def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    ln = math.sqrt(dot(a, a))
    return (0.0, 0.0, 1.0) if ln < 1e-12 else (a[0] / ln, a[1] / ln, a[2] / ln)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def hover(g, m, px):
    """Mark a hovering kin: lifted on the front sprite and in the overworld."""
    m.float_lift = max(m.float_lift, 2)
    g.OW_FLOAT[m.name] = px


def side_yaw(g, m, yaw):
    """Overworld side view yaw."""
    g.OW_SIDE_YAW[m.name] = yaw


def paint_path(m, pts, r, mat, parts, steps=6):
    """A painted line (glowing seam, crack, stripe) through pts."""
    if isinstance(r, (int, float)):
        r = (r, r, r)
    for i in range(len(pts) - 1):
        for k in range(steps + 1):
            m.paint(lerp(pts[i], pts[i + 1], k / float(steps)), r, mat, parts)


def frustum_planes(base, rb, rt, h, sides, phase=0.0):
    x0, y0, z0 = base
    planes = [((0.0, 1.0, 0.0), y0 + h), ((0.0, -1.0, 0.0), -y0)]
    for k in range(sides):
        a = 2 * math.pi * k / sides + phase * DEG
        n = norm((math.cos(a) * h, rb - rt, math.sin(a) * h))
        p = (x0 + math.cos(a) * rb, y0, z0 + math.sin(a) * rb)
        planes.append((n, dot(n, p)))
    return planes


def frustum(m, base, rb, rt, h, sides, mat, part, phase=0.0):
    """Faceted vertical frustum (convex hull) standing on `base`."""
    planes = frustum_planes(base, rb, rt, h, sides, phase)
    c = (base[0], base[1] + h / 2.0, base[2])
    return m.hull(planes, c, math.sqrt(max(rb, rt) ** 2 + (h / 2.0) ** 2) + 0.6, mat, part)


def ring(m, c, r, axis, tube_r, mat, part, n=18, flat=1.0, up=None):
    """A closed ring (rim, band, collar) of radius r round `axis` through c."""
    ax = norm(axis)
    u = norm(cross(ax, (0.3, 0.9, 0.2) if abs(ax[1]) < 0.9 else (1, 0, 0)))
    v = cross(ax, u)
    pts = []
    for k in range(n + 1):
        a = 2 * math.pi * k / n
        pts.append(add(c, add(mul(u, math.cos(a) * r), mul(v, math.sin(a) * r))))
    m.tube(pts, tube_r, mat, part, flat=flat, up=up if up is not None else ax)


# ==========================================================================
# 107 GAUNTLING  RELIC/METAL  a gauntlet that walks on its fingers
# ==========================================================================
def gauntling(g):
    m = g.Model('GAUNTLING')
    m.outline = (22, 24, 34)
    m.mat('steel', ['#2e3444', '#4c566c', '#7a869c', '#b8c4d4'], spec=0.5)
    m.mat('brass', ['#7a4e14', '#c08a2a', '#f2d070'], spec=0.3)
    m.mat('soul', ['#2aa89c', '#8af4e0', '#e8fff8'], emissive=0.85)
    m.mat('void', ['#141420'])
    m.white = (232, 255, 248)
    m.eye_dark = (20, 20, 32)
    m.height = 32
    m.front_yaw = -28
    m.back_pitch = 8.0
    # the back of the hand reared up like a crab's shell, tilted to face us
    tilt = (-26, 0, 0)
    hand_c, hand_r = (0, 12.4, -0.8), (7.8, 6.8, 3.8)
    m.ell(hand_c, hand_r, 'steel', 'hand', rot=tilt)
    # articulated lames across the back of the hand
    for k, y in enumerate((15.6, 12.4)):
        p, n = g.on(hand_c, hand_r, (0, (y - 12.0) / 6.6, 0.8), rot=tilt)
        m.paint(p, (7.6, 0.55, 1.2), 'steel' if k else 'brass', ['hand'], rot=tilt)
    # riveted brass knuckle guard over the finger roots
    for i, x in enumerate((-4.8, -1.6, 1.6, 4.8)):
        m.ell((x, 7.4, 3.4), (1.9, 1.6, 1.8), 'steel', 'knuckle')
        m.sph((x, 8.0, 5.0), 0.7, 'brass', 'knuckle')
    m.tube([(-6.4, 8.6, 2.2), (0, 9.2, 3.6), (6.4, 8.6, 2.2)], 1.0, 'brass', 'knuckle')
    # four fingers arch forward and down as legs; each has three plates
    for i, x in enumerate((-4.8, -1.6, 1.6, 4.8)):
        sx = x * (1.55 if abs(x) > 3 else 1.15)
        pts = [(x, 7.2, 3.8), (x * 1.25, 7.4, 7.2), (sx, 4.4, 9.2), (sx * 1.05, 0.9, 9.4)]
        m.tube(pts, [1.5, 1.45, 1.35, 1.1], 'steel', 'finger%d' % i)
        for t, j in ((pts[1], 1.6), (pts[2], 1.5)):
            m.sph(t, j, 'steel', 'finger%d' % i)
            m.paint(t, (1.7, 0.45, 1.7), 'void', ['finger%d' % i])
        # little pointed brass fingertip
        m.crystal(add(pts[3], (0, 0.6, 0)), add(pts[3], (0, -0.9, 1.6)), 0.9, 'brass',
                  'finger%d' % i, sides=4, tip_frac=0.7)
    # thumb raised to the side like a waving arm
    m.tube([(7.0, 11.0, 0.6), (9.8, 12.8, 2.2), (11.2, 15.8, 3.2)], [1.9, 1.7, 1.5], 'steel',
           'thumb')
    m.sph((9.8, 12.8, 2.2), 1.9, 'steel', 'thumb')
    m.paint((9.8, 12.8, 2.2), (2.0, 0.45, 2.0), 'void', ['thumb'])
    m.crystal((11.2, 15.8, 3.2), (11.6, 17.8, 3.8), 0.9, 'brass', 'thumb', sides=4, tip_frac=0.7)
    # a short flared cuff low at the wrist, open to the sky, a wisp of ghost
    # light rising out of it
    ax = norm((0, 1, -0.7))
    cb = (0, 8.4, -4.4)
    m.ell(add(cb, mul(ax, 0.4)), (3.4, 2.0, 3.0), 'steel', 'cuff', rot=(-35, 0, 0))
    for k in range(2):
        c = add(cb, mul(ax, 1.0 + k * 1.2))
        ring(m, c, 3.0 + k * 0.5, ax, 0.95, 'steel' if k < 1 else 'brass', 'cuff', n=20)
    ic = add(cb, mul(ax, 2.0))
    m.ell(ic, (3.2, 0.5, 3.0), 'void', 'cuffin', rot=(-35, 0, 0))
    m.paint(add(ic, mul(ax, 0.4)), (1.6, 0.8, 1.6), 'soul', ['cuffin'], rot=(-35, 0, 0))
    g.flame(m, add(ic, mul(ax, 0.2)), 5.0, 2.0, 'wisp', mats=('soul', 'soul', 'soul'),
            up=(0, 1, -0.8), face=(0.8, 0.2, 0.3), tongues=2, seed=17, inner=False, core=False)
    # the palm side seen from behind: a brass-rimmed plate, rivets and a
    # glowing seam
    for yy, mat, w in ((1.1, 'brass', 8.0), (0.45, 'soul', 8.0)):
        p, n = g.on(hand_c, hand_r, (0, yy, -1), rot=tilt)
        m.paint(p, (w, 0.8, 2.0), mat, ['hand'], rot=tilt)
    for sx in (-0.75, 0.75):
        p, n = g.on(hand_c, hand_r, (sx, 0.5, -0.6), rot=tilt)
        m.sph(p, 0.9, 'brass', 'hand')
    # the face: a dark visor slit across the hand, two ghost-light eyes
    p, n = g.on(hand_c, hand_r, (0, 0.05, 1), rot=tilt)
    m.dot(add(p, (0, 0.2, 0)), n, w=11.0, h=4.2, color=('void', 0), minw=9, minh=4)
    for s in (-1, 1):
        q, nn = g.on(hand_c, hand_r, (s * 0.34, 0.08, 0.94), rot=tilt)
        m.eye(q, nn, 3.4, 2.8, style='glow', iris=('soul', 1), slant=-0.5, glint=False,
              center=(0, 12, 12), minw=3, minh=2)
    return m


# ==========================================================================
# 108 HOLLOWHELM  RELIC/METAL  an empty suit of plate armour, glowing gaps
# ==========================================================================
def hollowhelm(g):
    m = g.Model('HOLLOWHELM')
    m.outline = (18, 20, 30)
    m.mat('steel', ['#20263a', '#3a445c', '#687690', '#b0bed0'], spec=0.5)
    m.mat('brass', ['#74480e', '#bc8628', '#f0cc6a'], spec=0.3)
    m.mat('soul', ['#15968c', '#5ee8d2', '#b4fff0'], emissive=0.6)
    m.mat('void', ['#12121c'])
    m.mat('cloth', ['#4a1422', '#86263a'])
    m.white = (180, 255, 240)
    m.eye_dark = (18, 18, 28)
    m.height = 60
    m.max_w = 62
    m.front_yaw = -26
    m.back_scale = 1.15
    # ---- legs: sabatons, greaves, glowing knee gaps, cuisses
    for s in (-1, 1):
        x = s * 4.8
        m.ell((x * 1.05, 1.6, 2.2), (2.6, 1.7, 4.6), 'steel', 'foot%d' % s)
        m.crystal((x * 1.05, 1.4, 5.0), (x * 1.08, 0.9, 8.2), 1.5, 'steel', 'foot%d' % s,
                  sides=4, tip_frac=0.8)
        m.tube([(x, 3.0, 0.8), (x, 7.0, 1.0), (x, 10.2, 1.2)], [2.5, 2.9, 2.6], 'steel',
               'leg%d' % s)
        m.sph((x, 14.0, 1.4), 2.3, 'soul', 'kneeglow%d' % s)
        m.tube([(x, 18.4, 1.0), (x * 0.95, 21.0, 0.8), (x * 0.9, 24.0, 0.6)], [2.9, 3.3, 3.5],
               'steel', 'thigh%d' % s)
    # ---- waist: glowing gap, tassets, a torn tabard
    m.ell((0, 26.4, 0.2), (5.6, 2.6, 4.2), 'soul', 'waist')
    # flared tassets: two rows of plates skirting out over the hips
    for row, (y, rr, fl) in enumerate(((23.4, 7.4, 28), (20.2, 8.8, 40))):
        for a in (-110, -70, -30, 10, 50, 90) if row else (-95, -55, -15, 25, 65, 105):
            a2 = a if row else a - 5
            c = (math.sin(a2 * DEG) * rr, y, math.cos(a2 * DEG) * rr * 0.72)
            m.box(c, (2.8, 3.2, 0.55), 'steel', 'tasset', rot=(fl * 0.4, a2, 0),
                  bevel=0.3)
    m.tube([(math.sin(a * DEG) * 7.2, 25.6, math.cos(a * DEG) * 5.2) for a in range(-120, 121, 20)],
           0.8, 'brass', 'tasset')
    # ---- tattered cape behind
    m.poly([(-8.0, 44.0, -5.0), (8.0, 44.0, -5.0), (10.0, 16.0, -7.0), (6.0, 19.0, -7.2),
            (3.0, 13.0, -7.2), (-1.0, 18.0, -7.2), (-4.4, 12.0, -7.0), (-7.2, 17.4, -7.0),
            (-10.0, 15.0, -6.8)], 'cloth', 'cape', puff=0.25)
    # ---- breastplate with a brass ridge and a second glowing seam
    m.ell((0, 37.0, 0.4), (9.6, 8.2, 5.8), 'steel', 'body')
    m.ell((0, 31.2, 0.6), (7.0, 2.4, 4.8), 'steel', 'belly')
    m.paint((0, 33.2, 0.6), (9.6, 0.8, 6.2), 'soul', ['body'])
    # a cross-shaped slit over the heart: the light inside shows through
    m.paint((0, 37.6, 5.8), (1.3, 4.4, 1.6), 'void', ['body'])
    m.paint((0, 38.8, 5.8), (3.4, 1.2, 1.6), 'void', ['body'])
    m.paint((0, 37.6, 6.0), (0.8, 3.6, 1.8), 'soul', ['body'])
    m.paint((0, 38.8, 6.0), (2.6, 0.75, 1.8), 'soul', ['body'])
    for s in (-1, 1):
        m.paint((s * 5.6, 36.0, 3.8), (0.8, 5.0, 3.0), 'brass', ['body'], rot=(0, 0, s * 10))
    # ---- gorget, an empty neck full of light, the floating helm
    ring(m, (0, 44.4, 0.3), 3.8, (0, 1, 0), 1.3, 'steel', 'gorget', n=18)
    m.ell((0, 44.6, 0.3), (3.2, 1.0, 3.2), 'soul', 'gorget')
    g.flame(m, (0, 44.6, 0.8), 3.4, 2.4, 'neckfire', mats=('soul', 'soul', 'soul'),
            up=(0, 1, 0), tongues=2, seed=5, inner=False, core=False)
    head_c, head_r = (0, 53.4, 1.2), (6.4, 6.6, 6.2)
    m.ell(head_c, head_r, 'steel', 'head')
    m.ell((0, 50.4, 3.8), (4.6, 3.4, 3.4), 'steel', 'head')
    m.paint((0, 50.0, 7.0), (0.8, 3.0, 1.2), 'brass', ['head'])
    m.paint((0, 57.6, 1.2), (6.0, 0.7, 6.2), 'brass', ['head'])
    # ghost-flame plume streaming off the crest
    g.flame(m, (0, 58.4, -0.8), 7.0, 2.6, 'plume', mats=('soul', 'soul', 'soul'),
            up=(0, 1, -0.55), face=(0.8, 0.2, 0.3), tongues=2, seed=11, inner=False,
            core=False)
    # ---- pauldrons: big flared, stacked brass-rimmed plates with a ridge
    for s_ in (-1, 1):
        for k in range(3):
            c = (s_ * (11.0 + k * 1.3), 43.4 - k * 2.6, 0.2)
            m.ell(c, (6.4 - k * 0.5, 3.0, 5.8 - k * 0.4), 'steel', 'sh%d' % s_,
                  rot=(0, 0, -s_ * (16 + k * 9)))
        m.paint((s_ * 11.0, 43.4, 0.2), (6.6, 0.8, 6.0), 'brass', ['sh%d' % s_],
                rot=(0, 0, -s_ * 16))
        # a fin-like ridge standing up on each pauldron
        m.crystal((s_ * 10.6, 45.4, 0.2), (s_ * 12.4, 49.6, -0.4), 1.4, 'brass', 'sh%d' % s_,
                  sides=4, tip_frac=0.8)
    # ---- arms: glowing elbow gaps, vambraces, both gauntlets on the pommel
    for s in (-1, 1):
        sh = (s * 12.8, 37.6, 0.4)
        el = (s * 14.4, 29.6, 2.6)
        wr = (s * 5.0, 24.6, 8.2)
        m.sph((s * 10.6, 37.2, 0.6), 2.4, 'soul', 'arm%d' % s)
        m.tube([add(sh, (0, -1.6, 0)), lerp(sh, el, 0.62)], [2.7, 2.5], 'steel', 'arm%d' % s)
        m.sph(el, 2.3, 'soul', 'elbowglow%d' % s)
        m.tube([lerp(el, wr, 0.3), wr], [2.5, 2.9], 'steel', 'arm%d' % s)
        ring(m, lerp(el, wr, 0.9), 2.8, sub(wr, el), 0.8, 'brass', 'arm%d' % s, n=16)
        fc = (s * 2.4, 23.4, 9.4)
        m.ell(fc, (2.8, 3.0, 2.8), 'steel', 'fist%d' % s)
        for i in range(4):
            m.ell(add(fc, (-s * 0.4, 1.6 - i * 1.1, 2.2)), (1.6, 0.7, 1.2), 'steel',
                  'fist%d' % s)
        m.sph(add(fc, (s * 0.6, 1.4, 2.4)), 0.6, 'brass', 'fist%d' % s)
    # a broken greatsword planted point-down between the feet
    fr = (0, 23.6, 9.6)
    m.box(add(fr, (0, 1.6, 0)), (0.7, 3.4, 0.7), 'cloth', 'hilt', bevel=0.3)
    m.sph(add(fr, (0, 5.6, 0)), 1.5, 'brass', 'hilt')
    m.box(add(fr, (0, -3.8, 0)), (4.6, 0.8, 1.0), 'brass', 'hilt', bevel=0.4)
    m.box(add(fr, (0, -11.6, -0.4)), (1.9, 7.2, 0.5), 'steel', 'blade', bevel=0.2,
          rot=(20, 0, 0))
    m.crystal(add(fr, (0.4, -18.4, -0.4)), add(fr, (0.9, -22.4, -0.4)), 1.3, 'steel', 'blade',
              sides=4, tip_frac=0.9, twist=45)
    paint_path(m, [add(fr, (0, -5.4, 0.3)), add(fr, (0, -16.0, 0.3))], (0.55, 0.8, 0.8),
               'brass', ['blade'])
    # ---- the face: a tall visor slit full of dark, two big ghost-light eyes
    p, n = g.on(head_c, head_r, (0, 0.0, 1))
    m.dot(add(p, (0, 0.4, 0)), n, w=11.5, h=5.0, color=('void', 0), minw=10, minh=5)
    for s in (-1, 1):
        q, nn = g.on(head_c, head_r, (s * 0.34, 0.04, 0.94))
        m.eye(q, nn, 4.2, 4.2, style='glow', iris=('soul', 2), slant=-0.3, glint=False,
              center=(0, 53, 14), minw=3, minh=3)
    for k in range(3):
        m.dot(add(p, (-1.8 + k * 1.8, -3.6, 0.4)), n, w=1.0, h=1.4, color=('void', 0))
    return m


# ==========================================================================
# 109 WICKLET  RELIC/BLAZE  a candle stub that walks about in its brass dish
# ==========================================================================
def wicklet(g):
    m = g.Model('WICKLET')
    m.outline = (58, 30, 22)
    m.mat('wax', ['#b08a6a', '#dcc0a0', '#f4e4c8', '#fffaec'])
    m.mat('brass', ['#6e4212', '#b47e24', '#eec462'], spec=0.4)
    m.mat('flame', ['#e0501c', '#ff9a2a'], emissive=0.8)
    m.mat('fgold', ['#ffd040', '#fff4a0'], emissive=0.9)
    m.mat('wick', ['#2a1a18'])
    m.white = (255, 250, 236)
    m.eye_dark = (42, 26, 24)
    m.height = 34
    m.front_yaw = -24
    # the brass dish on three little claw feet, with a ring handle for a tail
    m.ell((0, 2.4, 0), (8.4, 1.3, 8.0), 'brass', 'dish')
    ring(m, (0, 3.3, 0), 8.0, (0, 1, 0), 0.8, 'brass', 'dish', n=26)
    for k, a in enumerate((35, 155, 275)):
        c = (math.sin(a * DEG) * 5.6, 0.9, math.cos(a * DEG) * 5.4)
        m.ell(c, (1.6, 1.1, 1.8), 'brass', 'foot%d' % k)
    ring(m, (0, 4.4, -10.8), 3.0, (1, 0, 0), 0.75, 'brass', 'handle', n=18)
    m.tube([(0, 3.2, -7.8), (0, 3.6, -8.6)], 0.9, 'brass', 'handle')
    # the candle stub: a squat wax body with a melted, lumpy top
    body_c, body_r = (0, 8.6, 0), (6.2, 6.0, 6.0)
    frustum(m, (0, 2.8, 0), 6.4, 6.0, 10.2, 16, 'wax', 'body', phase=11.25)
    m.ell((0, 13.0, 0), (5.8, 1.4, 5.8), 'wax', 'body')
    # wax drips running down the sides and pooling in the dish
    for k, (a, ln) in enumerate(((-40, 4.4), (15, 6.0), (70, 3.4), (130, 5.0), (200, 4.0),
                                 (250, 5.6))):
        d = (math.sin(a * DEG), 0, math.cos(a * DEG))
        top = (d[0] * 5.9, 13.4, d[2] * 5.9)
        bot = (d[0] * 6.4, 13.4 - ln, d[2] * 6.4)
        m.tube([top, lerp(top, bot, 0.5), bot], [0.9, 0.8, 1.0], 'wax', 'drip%d' % k)
    m.ell((3.4, 3.6, 3.6), (2.6, 0.7, 2.2), 'wax', 'dish')
    # stubby wax arms
    for s in (-1, 1):
        m.tube([(s * 5.8, 8.6, 0.8), (s * 7.8, 7.6, 1.8), (s * 8.4, 6.4, 2.4)], [1.4, 1.2, 1.2],
               'wax', 'arm%d' % s)
    # the wick and its flame: the kin's head-fire
    m.tube([(0, 13.4, 0), (0.2, 15.2, 0.1), (-0.3, 16.4, 0.3)], [0.6, 0.55, 0.45], 'wick',
           'wick')
    g.flame(m, (-0.2, 15.6, 0.3), 12.0, 3.6, 'flame', mats=('flame', 'fgold', 'fgold'),
            up=(0.05, 1, 0), tongues=2, seed=9)
    # face on the wax: big round eyes, a tiny smile and warm cheeks
    p, n = (0.0, 7.4, 6.3), (0, 0, 1)
    for s in (-1, 1):
        a = s * 24 * DEG
        q, nn = (math.sin(a) * 6.3, 9.2, math.cos(a) * 6.3), (math.sin(a), 0, math.cos(a))
        m.eye(q, nn, 2.8, 3.6, style='cute', iris=('flame', 0), center=(0, 9, 14), minw=2,
              minh=3)
        a = s * 42 * DEG
        q, nn = (math.sin(a) * 6.2, 6.8, math.cos(a) * 6.2), (math.sin(a), 0, math.cos(a))
        m.dot(q, nn, w=1.6, h=0.9, color=('flame', 1))
    m.mouth(p, n, 'smile', w=2.4, h=1.4)
    return m


# ==========================================================================
# 110 LAMPGHAST  RELIC/BLAZE  a grinning paper lantern ghost (chochin-obake)
# ==========================================================================
def lampghast(g):
    m = g.Model('LAMPGHAST')
    m.outline = (52, 20, 24)
    m.mat('paper', ['#c0602a', '#e8923e', '#f8c472', '#fff0c8'], emissive=0.3)
    m.mat('rib', ['#9a4a22'])
    m.mat('lac', ['#1c1418'])
    m.mat('maw', ['#5a1422'])
    m.mat('tooth', ['#fff0c8'])
    m.mat('gold', ['#a8741c', '#f0c250'], spec=0.3)
    m.mat('tongue', ['#b41e3a', '#f0607a'])
    m.mat('fire', ['#e8401c', '#ffa030'], emissive=0.8)
    m.mat('core', ['#fff0a0'], emissive=0.95)
    m.white = (255, 240, 200)
    m.eye_dark = (28, 20, 24)
    m.height = 56
    m.max_w = 60
    m.front_yaw = -22
    hover(g, m, 3)
    # the paper body: a tall round lantern stretched on bamboo ribs
    bc, br = (0, 23.0, 0), (10.0, 12.0, 9.6)
    m.ell(bc, br, 'paper', 'body')
    # bamboo ribs showing through the paper
    for k in range(-4, 5):
        y = bc[1] + k * 2.5
        t = 1 - ((y - bc[1]) / br[1]) ** 2
        if t > 0.05:
            rr = math.sqrt(t)
            m.paint((0, y, 0), (br[0] * rr + 0.6, 0.5, br[2] * rr + 0.6), 'rib', ['body'])
    # black lacquer caps top and bottom with gold rims, a wire hanging loop
    frustum(m, (0, 33.0, 0), 5.6, 4.8, 2.6, 14, 'lac', 'cap')
    ring(m, (0, 33.2, 0), 5.8, (0, 1, 0), 0.6, 'gold', 'cap', n=22)
    frustum(m, (0, 10.4, 0), 4.8, 5.6, 2.8, 14, 'lac', 'base')
    ring(m, (0, 13.0, 0), 5.8, (0, 1, 0), 0.6, 'gold', 'base', n=22)
    m.tube([(-3.6, 35.4, 0), (-3.4, 38.6, 0), (0, 40.6, 0), (3.4, 38.6, 0), (3.6, 35.4, 0)],
           0.55, 'lac', 'cap')
    # a red crest painted on its back
    m.paint((0, 24.0, -9.6), (3.6, 3.6, 1.4), 'tongue', ['body'])
    m.paint((0, 24.0, -9.9), (2.2, 2.2, 1.4), 'paper', ['body'])
    # a torn slit on one side, fire showing through
    paint_path(m, [(-8.0, 29.0, 5.4), (-9.2, 26.4, 3.8), (-8.8, 24.0, 4.4)], (0.9, 0.9, 1.6),
               'fire', ['body'])
    # ghost-fire tail streaming down from the base
    g.flame(m, (0, 10.6, 0), 10.0, 4.2, 'tail', mats=('fire', 'fire', 'core'),
            up=(0.15, -1, -0.35), face=(0.4, 0, 1), tongues=2, seed=21, inner=False)
    # two will-o'-wisps orbiting it
    for s, (x, y, z) in ((-1, (-14.4, 30.0, -1.0)), (1, (14.0, 14.0, 2.4))):
        m.sph((x, y, z), 2.0, 'fire', 'wisp%d' % s)
        m.sph((x + 0.4, y + 0.3, z + 1.2), 1.1, 'core', 'wisp%d' % s)
        m.tube([(x, y + 1.4, z), (x - s * 0.8, y + 3.6, z - 0.6), (x - s * 0.2, y + 5.4, z - 1.0)],
               [1.6, 1.0, 0.3], 'fire', 'wisp%d' % s)
    # the face: one huge eye, one squint, a wide grin torn in the paper
    q, nn = g.on(bc, br, (math.sin(26 * DEG), 0.30, math.cos(26 * DEG)))
    m.eye(q, nn, 5.8, 6.4, style='sharp', iris=('fire', 0), look=-1, center=(0, 25, 16), minw=5,
          minh=5)
    q, nn = g.on(bc, br, (math.sin(-24 * DEG), 0.28, math.cos(-24 * DEG)))
    m.eye(q, nn, 3.4, 2.6, style='cute', iris=('lac', 0), lid=1, slant=0.6,
          center=(0, 25, 16), minw=3, minh=2)
    # the grin: a wide jagged slash that wraps round the lantern's curve,
    # dark lips, a dark-red mouth inside, fangs top and bottom
    def grin_pt(a, dy=0.0):
        """Point on the paper at yaw a (deg) along the grin centreline."""
        t = a / 52.0
        y = 16.0 + 6.4 * t * t + dy
        d = (math.sin(a * DEG), (y - bc[1]) / br[1], math.cos(a * DEG))
        return g.on(bc, br, d)[0]

    def grin_h(a):
        t = abs(a) / 52.0
        return 3.8 * (1 - t ** 2.4) + 0.7

    angles = [-52 + k * 4 for k in range(27)]
    for a in angles:
        m.paint(grin_pt(a), (1.9, grin_h(a) + 0.9, 1.9), 'lac', ['body'])
    for a in angles[1:-1]:
        m.paint(grin_pt(a), (1.7, grin_h(a), 1.7), 'maw', ['body'])
    # fangs: a jagged row hanging from the upper lip, two jutting up
    def fang(a, sgn, big):
        h = grin_h(a)
        y0 = sgn * (h - 0.2)
        for k, (w, hh) in enumerate(((1.35, 0.8), (0.95, 0.7), (0.5, 0.6))[:3 if big else 2]):
            m.paint(grin_pt(a, y0 - sgn * k * 1.1), (w * (1 if big else 0.85), hh, 1.8), 'tooth',
                    ['body'])
    for a in (-36, -20, 16, 34):
        fang(a, 1, abs(a) < 30)
    for a in (-28, 26):
        fang(a, -1, False)
    # the long tongue lolling out of the grin and curling up at the tip
    t0 = add(grin_pt(-2, -1.6), (0, 0, -1.4))
    m.tube([t0, add(t0, (0.6, -1.2, 2.8)), add(t0, (1.4, -5.6, 4.0)), add(t0, (1.4, -9.8, 3.4)),
            add(t0, (0.0, -11.8, 2.0)), add(t0, (-1.0, -10.8, 1.4))],
           [2.3, 2.3, 2.1, 1.8, 1.4, 1.0], 'tongue', 'tongue', flat=0.5, up=(0, 0.2, 1))
    m.paint(add(t0, (1.0, -5.0, 4.6)), (0.35, 3.0, 1.0), 'maw', ['tongue'])
    return m


# ==========================================================================
# 111 METEORB  ASTRAL/STONE  a fallen meteorite on stubby legs
# ==========================================================================
def meteorb(g):
    m = g.Model('METEORB')
    m.outline = (22, 16, 30)
    m.mat('rock', ['#2a2434', '#463c54', '#6a5e7a', '#968aa4'])
    m.mat('magma', ['#c0280e', '#ff6418', '#ffc040'], emissive=0.7)
    m.mat('star', ['#7a5ce0', '#d8ccff'], emissive=0.4, spec=0.6)
    m.mat('socket', ['#16101c'])
    m.white = (255, 192, 64)
    m.eye_dark = (22, 16, 28)
    m.height = 30
    m.front_yaw = -26
    # four stubby rock legs
    for k, (x, z) in enumerate(((-4.6, 3.2), (4.6, 3.2), (-4.4, -3.6), (4.4, -3.6))):
        m.rock((x, 2.0, z), (2.4, 2.4, 2.4), 'rock', 'leg%d' % k, seed=70 + k, n=12)
    # the pitted, lumpy meteorite body
    bc, br = (0, 10.4, 0), (8.6, 7.8, 8.2)
    m.rock(bc, br, 'rock', 'body', seed=77, n=24, jitter=0.07)
    m.rock((3.0, 14.2, -3.4), (4.6, 3.6, 4.4), 'rock', 'body', seed=78, n=14)
    # glowing cracks from the heat of the fall
    paint_path(m, [(-7.6, 13.0, 4.0), (-5.4, 11.0, 6.4), (-5.8, 8.0, 7.0), (-3.8, 5.6, 7.0)],
               (0.8, 0.8, 2.2), 'magma', ['body'])
    paint_path(m, [(7.8, 12.0, 3.2), (6.2, 9.6, 6.0), (6.8, 6.4, 5.6)], (0.8, 0.8, 2.2), 'magma',
               ['body'])
    paint_path(m, [(-2.0, 17.8, 3.4), (0.6, 16.6, 5.0), (0.0, 18.4, 1.0), (2.4, 19.0, -1.6),
                   (5.0, 18.6, -1.8)], (0.8, 0.8, 2.0), 'magma', ['body'])
    paint_path(m, [(-7.0, 10.0, -4.6), (-3.0, 12.8, -7.6), (1.6, 10.4, -8.2), (5.2, 13.6, -6.0)],
               (0.8, 0.8, 2.0), 'magma', ['body'])
    # star shards stuck in its crust, jutting out of the flanks (not the
    # crown, where they read as ears)
    for (b, d, ln, r) in (((-7.4, 8.4, 2.4), (-1, -0.15, 0.35), 3.6, 1.2),
                          ((7.0, 7.2, -2.6), (1, 0.05, -0.2), 3.0, 1.0),
                          ((-2.0, 11.0, -7.4), (-0.3, 0.2, -1), 3.0, 1.0)):
        m.crystal(b, add(b, mul(norm(d), ln)), r, 'star', 'body', sides=5, tip_frac=0.45)
    # a comet trail still streaming low off its back
    g.flame(m, (1.6, 9.6, -7.0), 12.0, 4.8, 'tail', mats=('magma', 'magma', 'magma'),
            up=(0.5, 0.12, -1), face=(1, 0.35, 0.2), tongues=2, seed=3, inner=False,
            core=False)
    # the face: glowing eyes in dark sockets, a small frown of a mouth
    for s in (-1, 1):
        q, nn = g.on(bc, br, (s * 0.36, 0.14, 0.92))
        m.paint(q, (2.4, 2.2, 1.6), 'socket', ['body'])
        m.eye(add(q, mul(nn, 0.3)), nn, 3.2, 3.0, style='glow', iris=('magma', 1), glint=False,
              slant=0.3, center=(0, 11, 14), minw=3, minh=2)
    q, nn = g.on(bc, br, (0.02, -0.22, 0.97))
    m.mouth(q, nn, 'line', w=2.6)
    m.sparkle((-9.0, 19.0, 2.0), (0, 0, 1), size=2, color=('star', 1))
    return m


# ==========================================================================
# 112 BOLIDON  ASTRAL/STONE  a meteor rhino with a streaming comet mane
# ==========================================================================
def bolidon(g):
    m = g.Model('BOLIDON')
    m.outline = (20, 14, 28)
    m.mat('rock', ['#241e2e', '#403650', '#645876', '#9284a4'])
    m.mat('magma', ['#c0280e', '#ff6418', '#ffc040'], emissive=0.7)
    m.mat('fire', ['#a81c10', '#e84818', '#ff9a28'], emissive=0.45)
    m.mat('core', ['#fff4c0'], emissive=0.95)
    m.mat('star', ['#7a5ce0', '#d8ccff'], emissive=0.4, spec=0.6)
    m.mat('socket', ['#140e1a'])
    m.white = (255, 244, 192)
    m.eye_dark = (20, 14, 26)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -42
    m.back_scale = 1.1
    side_yaw(g, m, -70)
    g.OW_TURN[m.name] = -20.0
    # four pillar legs with broad stone feet
    for k, (x, z) in enumerate(((-6.0, 8.0), (6.0, 8.0), (-6.2, -9.0), (6.2, -9.0))):
        m.tube([(x, 14.0, z), (x * 1.05, 8.0, z + 0.4), (x * 1.08, 3.0, z + 0.6)],
               [4.2, 3.6, 3.4], 'rock', 'leg%d' % k)
        m.rock((x * 1.08, 1.8, z + 1.2), (3.8, 2.0, 4.2), 'rock', 'leg%d' % k, seed=90 + k, n=12)
    # massive boulder body, humped over the shoulders
    m.rock((0, 18.0, -2.0), (10.0, 9.0, 14.0), 'rock', 'body', seed=95, n=26, jitter=0.06)
    m.rock((0, 24.0, 5.4), (9.0, 7.0, 7.6), 'rock', 'body', seed=96, n=18, jitter=0.06)
    m.rock((0, 16.2, -12.4), (8.0, 7.0, 5.6), 'rock', 'body', seed=97, n=16)
    m.rock((0, 12.6, -1.0), (8.6, 5.0, 11.6), 'rock', 'body', seed=98, n=18)
    # molten cracks glowing through the hide
    for pts in ([(9.0, 23.0, 7.0), (9.4, 19.0, 3.0), (9.2, 16.0, 0.0), (9.0, 13.0, -4.0)],
                [(9.0, 22.0, -4.0), (9.4, 18.0, -8.0), (8.6, 14.6, -12.0)],
                [(-9.2, 21.0, 6.0), (-9.4, 17.0, 0.0), (-9.0, 14.0, -6.0)],
                [(7.0, 26.0, 8.0), (4.0, 29.0, 6.0)]):
        paint_path(m, pts, (2.2, 1.3, 1.3), 'magma', ['body'])
    # star shards along the spine
    for (b, d, ln, r) in (((2.0, 26.4, -6.0), (0.3, 1, -0.4), 5.0, 1.4),
                          ((-3.0, 26.0, -1.0), (-0.5, 1, -0.2), 4.2, 1.2),
                          ((4.4, 24.4, -12.0), (0.5, 0.8, -0.6), 3.6, 1.1)):
        m.crystal(b, add(b, mul(norm(d), ln)), r, 'star', 'body', sides=5, tip_frac=0.45)
    # the head: a heavy wedge carried low, stone brow, ears
    hc, hr = (0, 19.0, 17.4), (7.4, 6.8, 7.8)
    m.rock(hc, hr, 'rock', 'head', seed=101, n=20, jitter=0.05)
    m.rock((0, 14.8, 23.6), (4.6, 4.2, 4.6), 'rock', 'head', seed=102, n=16, jitter=0.05)
    for s in (-1, 1):
        m.rock((s * 5.0, 24.0, 12.8), (1.6, 2.6, 1.4), 'rock', 'ear%d' % s, seed=104 + s, n=10,
               rot=(0, 0, -s * 30))
    # the great nose horn and a smaller one behind it on the brow, both
    # white-hot at the tip
    m.tube([(0, 15.2, 26.0), (0, 19.6, 28.2), (0, 24.6, 28.6), (0, 28.6, 27.2)],
           [2.5, 1.6, 1.0, 0.3], 'star', 'horn', mats=[(0, 'star'), (0.72, 'magma')])
    m.tube([(0, 24.4, 16.4), (0, 27.4, 17.0), (0, 29.4, 16.2)], [1.9, 1.1, 0.3], 'star',
           'horn2')
    # the comet mane: fire streaming back from the brow along the spine
    for k, (b, h, w, up) in enumerate(((((0, 25.0, 11.0)), 30.0, 6.0, (0, 0.5, -1)),
                                       (((0, 27.4, 3.0)), 22.0, 5.0, (0, 0.55, -1)),
                                       (((0, 25.8, -5.0)), 14.0, 4.0, (0, 0.5, -1)))):
        g.flame(m, b, h, w, 'mane%d' % k, mats=('fire', 'magma', 'core'), up=up,
                face=(1, 0.2, 0.2), tongues=2, seed=40 + k)
    # a short flaming tail
    g.flame(m, (0, 18.0, -17.0), 9.0, 3.0, 'tail', mats=('fire', 'magma', 'core'),
            up=(0, 0.3, -1), face=(1, 0.2, 0), tongues=2, seed=48, inner=False)
    # the face: ember eyes set forward either side of the horn under a heavy
    # stone brow, so they read head-on; flared nostrils
    for s in (-1, 1):
        q, nn = g.on(hc, hr, (s * 0.72, 0.40, 0.68))
        nn = norm(add(nn, (0, 0, 0.7)))
        m.paint(q, (2.9, 2.6, 2.2), 'socket', ['head'])
        m.eye(add(q, mul(nn, 0.3)), nn, 4.6, 4.6, style='glow', iris=('magma', 2), glint=False,
              slant=0.25, center=(0, 20, 34), minw=3, minh=3)
        m.rock(add(q, (s * 0.4, 2.8, -1.0)), (3.0, 1.0, 1.6), 'rock', 'head', seed=110 + s, n=10,
               rot=(0, 0, s * 14))
        m.dot((s * 2.0, 14.0, 28.0), (s * 0.4, -0.2, 1), w=1.2, h=1.2, color=('magma', 0))
    return m


# ---- end of batch ----
