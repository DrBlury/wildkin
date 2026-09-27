"""Art for kin 92-100 (KIN-B3).

One model function per species (the lowercase species name), called by
tools/gen_monsters.py as fn(g) with g = the gen_monsters module. Coordinates:
+Y up, +Z the way the kin faces, +X its left; the ground is y = 0.
"""

import math

DEG = math.pi / 180.0

# Shared ramps
WASHI = ['#d8c49a', '#f6ecd0']
BAMBOO = ['#5e3e26', '#a0763e', '#d8b474']
TONGUE = ['#a8304e', '#e86a86']
IRON = ['#1e1a26', '#342e3c', '#524a5a', '#7c7282']
TANUKI = ['#4a3024', '#7e5a3a', '#b88c5c']
CHAR = ['#1c1420', '#342432', '#4e3848', '#6e5260']
BRONZE = ['#4a2626', '#8a4e34', '#c8864c', '#f2c682']
PLATE = ['#2c3244', '#4c5670', '#7a88a4', '#bcc8da']
HIDE = ['#7a4a48', '#b87c6a', '#e4b09a']
BRASS = ['#a8802e', '#f0d068']
EMBER = ['#ff7a1c', '#ffc43a', '#fff4b8']


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def sdir(az, el):
    """Unit direction: az degrees toward +X from +Z, el degrees up."""
    a, e = az * DEG, el * DEG
    return (math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e))


def rgb(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def ow(g, m, lift=None, side=None):
    """Overworld tweaks the renderer keys by name: hover lift, profile yaw."""
    if lift:
        m.float_lift = max(m.float_lift, 2)
        g.OW_FLOAT[m.name] = lift
    if side is not None:
        g.OW_SIDE_YAW[m.name] = side


def frustum(g, m, base, rb, rt, h, sides, mat, part, phase=0.0):
    """Faceted vertical frustum (convex hull) standing on `base`; with
    phase=0 one flat face looks along +Z."""
    x0, y0, z0 = base
    planes = [((0.0, 1.0, 0.0), y0 + h), ((0.0, -1.0, 0.0), -y0)]
    for k in range(sides):
        a = 2 * math.pi * k / sides + phase * DEG
        n = g.norm((math.cos(a) * h, rb - rt, math.sin(a) * h))
        p = (x0 + math.cos(a) * rb, y0, z0 + math.sin(a) * rb)
        planes.append((n, g.dot(n, p)))
    c = (x0, y0 + h / 2.0, z0)
    return m.hull(planes, c, math.sqrt(max(rb, rt) ** 2 + (h / 2.0) ** 2) + 0.6, mat, part)


def paint_path(g, m, pts, r, mat, parts, steps=6):
    """A painted line (glowing seam, stitch, stripe) through pts."""
    if isinstance(r, (int, float)):
        r = (r, r, r)
    for i in range(len(pts) - 1):
        for k in range(steps + 1):
            m.paint(g.lerp(pts[i], pts[i + 1], k / float(steps)), r, mat, parts)


# ==========================================================================
# RELIC: tsukumogami
# ==========================================================================
def parasole(g):
    m = g.Model('PARASOLE')
    m.outline = (46, 20, 34)
    m.mat('paper', ['#5a1a30', '#9c2a38', '#d44a42', '#f4865e'])
    m.mat('pleat', ['#5a1a30', '#9c2a38'])
    m.mat('washi', WASHI)
    m.mat('sclera', ['#fdf8ec'])
    m.mat('bamboo', BAMBOO)
    m.mat('tongue', TONGUE)
    m.eye_dark = (46, 20, 34)
    m.white = rgb(WASHI[1])
    m.height = 39
    m.front_yaw = -24
    # the folded paper canopy: a pleated eight-sided cone, flaring at the hem
    frustum(g, m, (0, 7.6, 0), 8.6, 7.4, 1.6, 8, 'paper', 'canopy')
    frustum(g, m, (0, 9.0, 0), 7.4, 0.9, 17.0, 8, 'paper', 'canopy')
    # a washi band (the janome ring) and a dark tie near the top
    # alternating dark pleats between the lit panels
    for k in (1, 3, 5, 7):
        a = k * 45 * DEG
        for i in range(22):
            y = 9.2 + 15.0 * i / 21.0
            r = 7.4 - 6.5 * (y - 9.0) / 17.0
            m.paint((math.cos(a) * r, y, math.sin(a) * r), (0.34 * r + 0.2, 0.9, 0.34 * r + 0.2), 'pleat',
                    ['canopy'])
    for y, t in ((11.0, 0.9),):
        m.paint((0, y, 0), (9.0, t, 9.0), 'washi', ['canopy'])
    m.paint((0, 22.4, 0), (4.0, 0.8, 4.0), 'bamboo', ['canopy'])
    # tip ferrule
    m.tube([(0, 25.6, 0), (0.3, 28.0, -0.2), (0.8, 30.0, -0.6)], [0.9, 0.6, 0.3], 'bamboo', 'tip')
    # two spoke tips poking out like little arms
    for s in (-1, 1):
        m.tube([(s * 5.6, 12.4, 0.8), (s * 8.6, 13.4, 1.6), (s * 10.2, 15.4, 2.0)], [0.75, 0.6, 0.5],
               'bamboo', 'arm%d' % s)
        m.sph((s * 10.2, 15.4, 2.0), 0.9, 'bamboo', 'arm%d' % s)
    # the shaft and its crook handle as a single hopping foot
    m.tube([(0, 8.0, 0), (0, 4.0, 0.2), (0, 2.2, 0.6)], [1.2, 1.1, 1.1], 'bamboo', 'foot')
    m.tube([(0, 2.2, 0.6), (0, 1.1, 2.2), (0, 1.3, 4.2), (0, 2.6, 5.2), (0, 3.8, 4.8)], [1.1, 1.1, 1.1, 1.0, 0.9],
           'bamboo', 'foot')
    # one big eye, a long lolling tongue
    # (big and low on the cone, with a dark rim, so it reads in the overworld)
    ec, en = (0, 16.8, 4.75), g.norm((0, 6.5, 17.0))
    m.paint(ec, (4.5, 4.8, 1.6), 'pleat', ['canopy'])
    m.paint(g.add(ec, (0, 0, 0.15)), (3.9, 4.2, 1.6), 'sclera', ['canopy'])
    m.eye(g.add(ec, (0, -0.2, 0.2)), en, 3.6, 4.2, style='cute', center=(0, 17, 12))
    m.mouth((0, 11.8, 6.4), g.norm((0, 6.5, 17.0)), 'open', w=4.6, h=2.6, inner=('paper', 0))
    m.tube([(0.4, 11.4, 6.2), (1.0, 10.2, 8.2), (1.8, 7.6, 8.8), (1.4, 5.8, 8.2)], [1.2, 1.3, 1.2, 0.9],
           'tongue', 'tongue', flat=0.5, up=(0, 0.2, 1))
    return m


def stormbrela(g):
    m = g.Model('STORMBRELA')
    m.outline = (22, 22, 36)
    m.mat('canopy', ['#22263a', '#3a425c', '#5e6c8a', '#94a4ba'])
    m.mat('inner', ['#22263a', '#3a425c'])
    m.mat('bamboo', BAMBOO)
    m.mat('spark', ['#e8a020', '#fff070', '#fdfff0'], emissive=0.45)
    m.mat('tongue', TONGUE)
    m.eye_dark = (22, 22, 36)
    m.white = (253, 255, 240)
    m.height = 50
    m.max_w = 62
    m.front_yaw = -22
    # the canopy blown inside out: a bowl opening upward, dark inside
    frustum(g, m, (0, 19.0, 0), 2.0, 12.0, 12.0, 8, 'canopy', 'canopy')
    m.ell((0, 31.0, 0), (10.8, 0.7, 10.8), 'inner', 'canopy')
    m.paint((0, 20.0, 0), (3.0, 1.2, 3.0), 'bamboo', ['canopy'])
    # torn flaps hanging from the rim between the ribs
    for k in range(8):
        a = (360.0 * k / 8 + 5.0 + (k % 3) * 8) * DEG
        c, s = math.cos(a), math.sin(a)
        m.tube([(c * 11.0, 30.2, s * 11.0), (c * 12.4, 28.4, s * 12.4), (c * 12.8, 26.6, s * 12.8)],
               [1.4, 1.0, 0.25], 'canopy', 'canopy', flat=0.4, up=(c, 0.2, s))
    # a lightning stripe across the front panel
    paint_path(g, m, [(-9.5, 29.4, 9.6), (-6.0, 26.0, 7.0), (-7.6, 25.0, 6.4), (-4.0, 21.6, 4.2)],
               0.8, 'spark', ['canopy'])
    # the ribs, bent past the rim, each crackling at its tip
    rnd = g.Rand(93)
    for k in range(8):
        a = (360.0 * k / 8 + 22.5) * DEG
        c, s = math.cos(a), math.sin(a)
        r2 = 15.4 + 1.6 * rnd.f()
        y2 = 34.6 + 2.0 * rnd.f()
        pts = [(c * 2.4, 19.8, s * 2.4), (c * 7.6, 26.0, s * 7.6), (c * 12.6, 31.2, s * 12.6), (c * r2, y2, s * r2)]
        m.tube(pts, [0.6, 0.6, 0.6, 0.5], 'bamboo', 'rib%d' % k)
        tip = (c * r2, y2, s * r2)
        m.sph(tip, 0.7, 'spark', 'rib%d' % k)
        zz = [tip, g.add(tip, (c * 1.4 - s * 1.0, 1.2, s * 1.4 + c * 1.0)),
              g.add(tip, (c * 1.6 + s * 0.8, 2.4, s * 1.6 - c * 0.8)), g.add(tip, (c * 2.6, 3.8, s * 2.6))]
        for a0, a1 in zip(zz, zz[1:]):
            m.tube([a0, a1], [0.5, 0.4], 'spark', 'rib%d' % k)
    # shaft and a crook handle trailing below like a tail
    m.tube([(0, 19.0, 0), (0, 14.0, 0), (0.2, 8.0, -0.4)], [1.3, 1.2, 1.2], 'bamboo', 'shaft')
    m.tube([(0.2, 8.0, -0.4), (0.3, 5.4, -1.0), (0.4, 4.2, 1.2), (0.4, 5.4, 3.2), (0.3, 7.0, 3.2)],
           [1.2, 1.2, 1.2, 1.1, 1.0], 'bamboo', 'shaft')
    # one big eye on the underside of the canopy, a grin and a tongue in the wind
    en = g.norm((0, -10.0, 12.0))
    ec = (1.2, 26.4, 8.1)
    m.paint(ec, (3.4, 3.4, 1.6), 'canopy', ['canopy'])
    m.eye(ec, g.norm(g.add(en, (0, 0.6, 0.3))), 8, 8, style='iris', iris=('spark', 1), center=(0, 25, 16))
    m.mouth((1.2, 21.6, 4.3), en, 'open', w=5, h=2.4, inner=('canopy', 0), fang=1)
    m.tube([(2.6, 21.2, 4.4), (5.0, 20.4, 6.6), (8.0, 21.6, 7.8), (10.4, 20.4, 7.4)], [1.1, 1.2, 1.1, 0.7],
           'tongue', 'tongue', flat=0.5, up=(0, 1, 0.3))
    ow(g, m, lift=4)
    return m


def kettlekin(g):
    m = g.Model('KETTLEKIN')
    m.outline = (26, 20, 32)
    m.mat('iron', IRON)
    m.mat('stud', IRON[3:])
    m.mat('fur', TANUKI)
    m.mat('cream', ['#e8d4a8'])
    m.mat('steam', ['#8cc8d0', '#eef8f8'])
    m.eye_dark = rgb(IRON[0])
    m.white = rgb('#eef8f8')
    m.height = 28
    m.front_yaw = -28
    body_c, body_r = (0, 6.4, 0), (6.6, 5.4, 6.4)
    # the round iron pot, studded with hobnails
    m.ell(body_c, body_r, 'iron', 'body')
    m.ell((0, 10.8, 0), (4.6, 1.2, 4.6), 'iron', 'body')
    for k in range(10):
        a = (k * 36 + 18) * DEG
        for y, rr in ((7.8, 6.2),):
            if abs(math.sin(a) - 0.0) < 0.2 and math.cos(a) > 0:
                continue
            m.paint((math.sin(a) * rr, y, math.cos(a) * rr), 0.8, 'stud', ['body'])
    # the bail handle, folded back behind the ears
    m.tube([(-6.0, 8.6, 0), (-6.2, 12.0, -2.4), (-3.4, 14.6, -5.4), (0, 15.4, -6.2), (3.4, 14.6, -5.4),
            (6.2, 12.0, -2.4), (6.0, 8.6, 0)], [0.7] * 7, 'iron', 'handle')
    for s in (-1, 1):
        m.sph((s * 6.0, 8.6, 0), 1.0, 'iron', 'body')
    # a lid with a knob and two round tanuki ears
    m.ell((0, 12.0, 0), (4.0, 1.0, 4.0), 'iron', 'lid')
    m.sph((0, 13.2, 0), 1.2, 'iron', 'lid')
    for s in (-1, 1):
        m.tube([(s * 2.6, 12.2, -0.4), (s * 3.6, 14.0, -0.6), (s * 3.9, 15.2, -0.7)], [1.8, 1.5, 0.6], 'fur',
               'ear%d' % s, flat=0.45, up=(0, 0.1, 1))
        m.paint((s * 3.3, 13.6, 0.1), (0.9, 1.0, 0.6), 'iron', ['ear%d' % s])
    # a spout on its side, steam curling from it
    m.tube([(4.8, 5.6, 2.4), (8.0, 7.6, 3.6), (9.8, 10.2, 4.0)], [1.8, 1.2, 1.0], 'iron', 'spout')
    for p, r in (((10.4, 12.0, 4.0), 1.1), ((11.4, 13.6, 3.2), 1.3), ((10.6, 15.4, 2.8), 0.9)):
        m.sph(p, r, 'steam', 'steam')
    # stubby paws and a ringed tanuki tail
    for s in (-1, 1):
        m.ell((s * 3.6, 1.1, 3.4), (1.6, 1.1, 1.8), 'fur', 'legF%d' % s)
        m.ell((s * 3.8, 1.1, -3.0), (1.6, 1.1, 1.8), 'fur', 'legB%d' % s)
    m.tube([(-1.0, 4.6, -5.8), (-3.2, 3.8, -9.0), (-5.0, 5.0, -11.0), (-5.6, 7.4, -11.4)], [1.6, 2.2, 2.1, 1.4],
           'fur', 'tail')
    for p in ((-3.2, 3.8, -9.0), (-5.2, 5.6, -11.1)):
        m.paint(p, (2.6, 0.7, 2.6), 'iron', ['tail'], rot=(0, 0, 30))
    # face: a cream muzzle patch, bright round eyes
    p, n = g.on(body_c, body_r, sdir(8, -8))
    m.paint(p, (2.8, 1.9, 1.4), 'cream', ['body'])
    g.eye_pair(m, body_c, body_r, 26, 14, 3.6, 4.4, style='cute', center=(0, 7, 12), turn=6)
    p, n = g.on(body_c, body_r, sdir(8, -2))
    m.dot(p, n, w=1.6, h=1.0, minw=2)
    p, n = g.on(body_c, body_r, sdir(8, -14))
    m.mouth(p, n, 'w', w=3.0)
    return m


def tanukettle(g):
    m = g.Model('TANUKETTLE')
    m.outline = (26, 20, 32)
    m.mat('iron', IRON)
    m.mat('stud', IRON[3:])
    m.mat('fur', TANUKI)
    m.mat('mask', ['#2e2230', '#4a3228'])
    m.mat('cream', ['#d8bc8c', '#f4e4c0'])
    m.mat('leaf', ['#3e7a34', '#7cba48'])
    m.eye_dark = rgb(IRON[0])
    m.height = 52
    m.max_w = 62
    m.front_yaw = -28
    # the iron chagama: round belly, a wide flange, a shoulder and a rim
    m.ell((0, 11.0, 0), (11.4, 10.0, 11.4), 'iron', 'pot')
    m.ell((0, 12.0, 0), (13.6, 1.4, 13.6), 'iron', 'brim')
    m.ell((0, 18.4, 0), (8.8, 3.0, 8.8), 'iron', 'pot')
    m.ell((0, 20.6, 0), (7.4, 1.3, 7.4), 'iron', 'pot')
    for s in (-1, 1):
        m.ell((s * 8.8, 18.0, 0), (1.0, 1.8, 1.8), 'iron', 'pot')
    # hobnail studs round the belly
    # (the upper row sits on the shoulder above the flange, proud of the pot)
    for row, (y, rr, sr) in enumerate(((15.0, 10.6, 1.25), (8.4, 11.1, 1.0))):
        for k in range(14):
            a = (k * 360.0 / 14 + row * 12) * DEG
            m.sph((math.sin(a) * rr, y, math.cos(a) * rr), sr, 'stud', 'stud')
    # the tanuki: head out of the rim, paws on the edge
    head_c, head_r = (0, 26.6, 1.4), (7.6, 6.6, 6.8)
    m.ell((0, 21.6, 0.6), (6.4, 3.0, 6.0), 'fur', 'body')
    m.ell(head_c, head_r, 'fur', 'head')
    for s in (-1, 1):
        m.paint(g.on(head_c, head_r, sdir(s * 30, 10))[0], (3.4, 2.6, 2.2), 'mask', ['head'], rot=(0, 0, s * 20))
        m.paint(g.on(head_c, head_r, sdir(s * 55, -18))[0], (2.6, 2.0, 2.4), 'cream', ['head'])
        m.ell((s * 5.2, 32.2, -0.4), (2.4, 2.4, 1.4), 'fur', 'ear%d' % s)
        m.paint((s * 5.2, 32.2, 0.6), (1.2, 1.3, 0.8), 'mask', ['ear%d' % s])
        m.tube([(s * 6.2, 22.0, 1.4), (s * 6.6, 21.6, 4.6), (s * 5.4, 21.6, 7.2)], [2.0, 1.9, 1.8], 'fur',
               'arm%d' % s)
        m.ell((s * 5.2, 21.4, 7.6), (1.9, 1.3, 1.8), 'mask', 'arm%d' % s)
    mz_c, mz_r = (0, 24.8, 7.2), (3.2, 2.4, 2.4)
    m.ell(mz_c, mz_r, 'cream', 'head')
    m.ell((0, 25.8, 9.4), (1.1, 0.8, 0.7), 'mask', 'head')
    # a leaf on its head
    m.tube([(0.4, 33.0, 1.0), (1.6, 34.6, 0.0), (1.8, 36.8, -1.4), (0.8, 38.6, -2.0)], [0.4, 2.0, 1.8, 0.2], 'leaf',
           'leaf', flat=0.3, up=(0.3, 0.2, 1))
    m.paint((1.6, 35.2, -0.6), (0.3, 1.8, 1.4), 'leaf', ['leaf'])
    # feet out under the belly and a bushy ringed tail
    for s in (-1, 1):
        m.ell((s * 6.0, 1.8, 7.6), (2.4, 1.8, 2.8), 'fur', 'legF%d' % s)
        m.ell((s * 6.0, 1.3, 9.2), (1.8, 1.1, 1.2), 'mask', 'legF%d' % s)
    m.tube([(-3.0, 8.0, -9.4), (-7.0, 6.4, -14.0), (-10.2, 8.4, -16.8), (-11.0, 12.4, -17.2)], [2.4, 3.8, 3.6, 2.0],
           'fur', 'tail')
    for p in ((-7.0, 6.4, -14.0), (-10.4, 9.8, -17.0)):
        m.paint(p, (4.4, 1.0, 4.4), 'mask', ['tail'], rot=(0, 0, 40))
    # face
    g.eye_pair(m, head_c, head_r, 30, 12, 3.2, 3.8, style='cute', center=(0, 25, 12))
    m.mouth(g.on(mz_c, mz_r, (0, -0.4, 1))[0], (0, -0.2, 1), 'w', w=3.4)
    return m


def strawspect(g):
    m = g.Model('STRAWSPECT')
    m.outline = (28, 22, 34)
    m.mat('sack', ['#8a6a44', '#c0a070', '#ead6a8'])
    m.mat('straw', ['#9c7424', '#dcb44a', '#fbe88c'])
    m.mat('coat', ['#2c3a5a', '#4a6290'])
    m.mat('patch', ['#a83a30'])
    m.mat('glow', ['#8adc3c', '#e8ff9c'], emissive=0.85)
    m.mat('crow', ['#1c1826', '#383450'])
    m.eye_dark = (28, 24, 38)
    m.white = rgb('#fbe88c')
    m.height = 58
    m.max_w = 62
    m.icon_h = 27
    m.icon_w = 29
    m.front_yaw = -20
    # the post it has stood on for a hundred summers, and its crossbar
    m.tube([(0, 0.2, -0.8), (0, 12.0, -0.8), (0, 24.0, -0.8)], [1.1, 1.0, 1.0], 'sack', 'post')
    m.ell((0, 0.6, -0.8), (2.4, 0.8, 2.2), 'sack', 'post')
    # patched coat with a rope belt and straw poking out of the hem
    m.ell((0, 17.2, 0), (5.2, 6.6, 3.8), 'coat', 'body')
    m.ell((0, 12.4, 0), (5.6, 2.6, 4.0), 'coat', 'body')
    m.paint((0, 14.2, 0), (6.0, 0.8, 4.4), 'sack', ['body'])
    m.paint((-2.2, 18.2, 3.4), (1.6, 1.8, 1.2), 'patch', ['body'])
    rnd = g.Rand(96)
    for k in range(9):
        a = (-160 + 320.0 * k / 8) * DEG
        b = (math.sin(a) * 4.2, 11.0, math.cos(a) * 3.0)
        d = g.norm((math.sin(a) * 0.35, -1.0, math.cos(a) * 0.25))
        ln = 3.6 + 1.8 * rnd.f()
        m.tube([b, g.add(b, g.mul(d, ln))], [1.0, 0.3], 'straw', 'hem')
    # arms stretched along the crossbar, straw bursting from the cuffs
    for s in (-1, 1):
        m.tube([(s * 4.4, 21.0, 0), (s * 8.4, 21.4, 0.2), (s * 12.0, 21.0, 0.4)], [2.4, 2.1, 2.0], 'coat',
               'arm%d' % s)
        for k in range(5):
            a = (-60 + 30 * k) * DEG
            d = g.norm((s * math.cos(a), math.sin(a) * 0.8, 0.25 * rnd.f()))
            b = (s * 12.6, 21.0, 0.4)
            m.tube([b, g.add(b, g.mul(d, 2.6 + 1.2 * rnd.f()))], [1.0, 0.3], 'straw', 'arm%d' % s)
    m.paint((6.6, 21.8, 2.0), (1.2, 1.2, 1.0), 'patch', ['arm1'])
    # sack head tied at the neck with a straw collar
    m.ell((0, 23.4, 0.2), (2.6, 1.4, 2.4), 'sack', 'neck')
    for k in range(8):
        a = (k * 45 + 10) * DEG
        b = (math.sin(a) * 2.2, 23.2, math.cos(a) * 2.0 + 0.2)
        d = g.norm((math.sin(a), -0.6, math.cos(a)))
        m.tube([b, g.add(b, g.mul(d, 2.6))], [0.9, 0.3], 'straw', 'neck')
    head_c, head_r = (0, 29.4, 0.8), (6.6, 6.2, 5.6)
    m.ell(head_c, head_r, 'sack', 'head')
    # a battered straw hat, pushed back so the face shows
    m.ell((0, 35.0, -0.4), (9.6, 1.2, 8.4), 'straw', 'hat', rot=(0, -14, -8))
    m.ell((-0.4, 36.8, -1.2), (5.2, 2.6, 4.8), 'straw', 'hat', rot=(0, -14, -8))
    m.paint((-0.3, 35.7, -1.0), (5.6, 0.8, 5.3), 'patch', ['hat'], rot=(0, -14, -8))
    # stitched face: dark hollows with glowing eyes, a sewn-shut grin
    for s in (-1, 1):
        p, n = g.on(head_c, head_r, sdir(s * 27 + 6, 8))
        m.paint(p, (2.9, 2.8, 1.8), 'crow', ['head'])
    g.eye_pair(m, head_c, head_r, 27, 8, 3.6, 3.6, style='glow', iris=('glow', 1), center=(0, 29, 12), turn=6)
    p, n = g.on(head_c, head_r, sdir(6, -30))
    m.mouth(p, n, 'line', w=5.0, h=1.0)
    for dx in (-1.6, 0.0, 1.6):
        q, nq = g.on(head_c, head_r, g.norm((dx / 5.4 + 0.1, -0.5, 0.86)))
        m.dot(q, nq, w=0.5, h=1.6, minh=2)
    # a crow perched on its arm, bringing a gift
    cx = 11.2
    m.ell((cx, 25.0, 0.8), (1.9, 2.0, 2.5), 'crow', 'crow')
    m.sph((cx, 27.4, 2.2), 1.5, 'crow', 'crow')
    m.crystal((cx, 27.2, 3.4), (cx, 26.8, 5.8), 0.6, 'straw', 'crow', sides=4, tip_frac=0.8)
    m.tube([(cx, 24.6, -1.4), (cx, 23.8, -4.0)], [1.3, 0.6], 'crow', 'crow', flat=0.4, up=(0, 1, 0))
    m.eye((cx + 1.1, 27.9, 2.9), (0.6, 0.2, 0.8), 1, 1, style='solid', iris=('glow', 1), minw=1, minh=1)
    return m


# ==========================================================================
# METAL: armadillos
# ==========================================================================
def band_shell(g, m, c, r, zs, rise, mat, part, rivet='brass', n_riv=5, spread=62):
    """Riveted armour bands: slightly proud ellipse slices across the shell
    at each z in zs, with a row of rivets over the top."""
    for z in zs:
        f = math.sqrt(max(0.0, 1 - ((z - c[2]) / r[2]) ** 2))
        rx, ry = r[0] * f + rise, r[1] * f + rise
        m.ell((c[0], c[1], z), (rx, ry, 1.0 + rise * 0.3), mat, part)
        for k in range(n_riv):
            a = (-spread + 2 * spread * k / max(1, n_riv - 1)) * DEG
            m.sph((c[0] + math.sin(a) * rx, c[1] + math.cos(a) * ry, z + 0.3), 0.55 + rise * 0.12, rivet, part)


def shell_slice(g, m, c, r, z0, z1, ybot, mat, part, n=60):
    """One crisp armour band: the slice z0..z1 of the ellipsoid (c, r),
    cut flat underneath at ybot, as a convex hull."""
    planes = [((0.0, 0.0, 1.0), z1), ((0.0, 0.0, -1.0), -z0), ((0.0, -1.0, 0.0), -ybot)]
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        rad = math.sqrt(max(0.0, 1 - y * y))
        d = (math.cos(ga * i) * rad, y, math.sin(ga * i) * rad)
        sup = math.sqrt((r[0] * d[0]) ** 2 + (r[1] * d[1]) ** 2 + (r[2] * d[2]) ** 2)
        planes.append((d, sup + g.dot(d, c)))
    return m.hull(planes, (c[0], (c[1] + r[1] + ybot) / 2.0, (z0 + z1) / 2.0), max(r) + 1.0, mat, part)


def rivetillo(g):
    m = g.Model('RIVETILLO')
    m.outline = (26, 24, 36)
    m.mat('plate', PLATE)
    m.mat('gap', PLATE[:1])
    m.mat('skin', HIDE)
    m.mat('ear', ['#c86a6a', '#f0a0a0'])
    m.mat('brass', BRASS)
    m.eye_dark = rgb(PLATE[0])
    m.height = 30
    m.front_yaw = -52
    # a round little dome of armour: dark core showing in the gaps between
    # a front shield, three riveted bands and a rear shield
    sc, sr = (0, 4.4, -0.8), (5.4, 5.6, 6.6)
    m.ell((0, 3.8, -0.8), (4.4, 2.8, 5.6), 'skin', 'body')
    m.ell(sc, (4.4, 4.6, 5.8), 'gap', 'shell')
    cuts = [(3.2, 6.0), (0.9, 2.3), (-1.5, -0.1), (-3.9, -2.5), (-8.0, -4.9)]
    for k, (z0, z1) in enumerate(cuts):
        shell_slice(g, m, sc, sr, z0, z1, 2.6, 'plate', 'shell%d' % k)
    # neat rivets: one row across the top of each band
    for z0, z1 in cuts[1:4]:
        zc = (z0 + z1) / 2.0
        f = math.sqrt(max(0.0, 1 - ((zc - sc[2]) / sr[2]) ** 2))
        for a in (-50, 0, 50):
            ar = a * DEG
            m.sph((math.sin(ar) * sr[0] * f, sc[1] + math.cos(ar) * sr[1] * f, zc), 0.62, 'brass', 'shell')
    # stubby legs with pale claws peeking out under the rim
    for s in (-1, 1):
        for z, lg in ((3.2, 'legF%d' % s), (-4.0, 'legB%d' % s)):
            m.tube([(s * 3.4, 2.8, z), (s * 3.7, 0.9, z + 0.3)], [1.5, 1.4], 'skin', lg)
            for t in (-1, 1):
                m.sph((s * 3.7 + t * 0.6, 0.5, z + 1.4), 0.5, 'brass', lg)
    # a short tail with a ring and a round tip
    m.tube([(0, 3.6, -7.2), (0, 2.6, -9.0), (0.4, 1.6, -10.4)], [1.5, 1.1, 0.7], 'plate', 'tail')
    m.paint((0, 2.9, -8.5), (1.8, 1.8, 0.45), 'gap', ['tail'])
    # a big round head (little brother of FORTADILLO): helmet cap with one
    # rivet, a short snout with a dark nose, tall rounded ears
    head_c, head_r = (0, 6.0, 7.4), (3.2, 3.0, 3.0)
    m.ell(head_c, head_r, 'skin', 'head')
    shell_slice(g, m, (0, 6.1, 7.2), (3.4, 3.3, 3.2), 4.2, 8.0, 8.2, 'plate', 'cap')
    m.sph((0, 9.4, 6.8), 0.6, 'brass', 'cap')
    m.tube([(0, 5.2, 9.6), (0, 4.8, 11.2), (0, 4.6, 12.4)], [1.7, 1.3, 1.1], 'skin', 'head')
    m.ell((0, 4.7, 12.8), (1.0, 0.9, 0.7), 'gap', 'head')
    for s in (-1, 1):
        m.tube([(s * 2.0, 8.4, 6.0), (s * 3.2, 10.8, 5.6), (s * 3.6, 12.2, 5.4)], [1.5, 1.4, 0.5], 'skin',
               'ear%d' % s, flat=0.4, up=(0, 0.1, 1))
        m.paint((s * 3.0, 10.4, 6.2), (0.8, 1.2, 0.5), 'ear', ['ear%d' % s])
        m.paint(g.on(head_c, head_r, sdir(s * 58 + 10, -26))[0], (0.9, 0.6, 0.6), 'ear', ['head'])
    g.eye_pair(m, head_c, head_r, 36, 8, 3.2, 3.6, style='cute', center=(0, 6, 14), turn=18)
    p, n = g.on((0, 4.8, 11.2), (1.3, 1.3, 1.3), sdir(0, -60))
    m.mouth(p, n, 'smile', w=1.8)
    return m


def fortadillo(g):
    m = g.Model('FORTADILLO')
    m.outline = (26, 24, 36)
    m.mat('plate', PLATE)
    m.mat('band', PLATE[:3])
    m.mat('stone', ['#5e5a62', '#8e8a8c', '#c4bfb4'])
    m.mat('skin', HIDE)
    m.mat('brass', BRASS)
    m.mat('flag', ['#b43a34'])
    m.mat('grate', PLATE[:1])
    m.eye_dark = rgb(PLATE[0])
    m.height = 56
    m.max_w = 62
    m.front_yaw = -34
    # the fortress shell: stone walls, riveted steel bands, arrow slits
    m.ell((0, 8.0, 0), (8.4, 4.6, 12.0), 'skin', 'body')
    sc, sr = (0, 11.6, -0.6), (11.0, 9.0, 14.0)
    m.ell(sc, sr, 'plate', 'shell')
    band_shell(g, m, sc, sr, (6.0, 2.4, -1.2, -4.8, -8.4), 0.5, 'band', 'shell', n_riv=6, spread=64)
    for a in (58, 100, 142, -58):
        p, n = g.on(sc, sr, sdir(a, 0))
        m.paint(p, (0.8, 1.9, 0.8), 'grate', ['shell'])
    # a flat parapet with battlements round its rim
    m.ell((0, 19.2, -0.6), (8.4, 2.4, 10.6), 'stone', 'keep')
    for k in range(14):
        a = 2 * math.pi * k / 14
        m.box((math.sin(a) * 7.6, 21.8, -0.6 + math.cos(a) * 9.8), (1.3, 1.5, 1.3), 'stone', 'keep',
              rot=(a / DEG, 0, 0), bevel=0.3)
    # a little watchtower with a pennant
    m.box((0, 25.0, -3.4), (2.8, 4.0, 2.8), 'stone', 'tower', bevel=0.4)
    for (x, z) in ((-2.0, -1.4), (2.0, -1.4), (-2.0, -5.4), (2.0, -5.4)):
        m.box((x, 29.8, z), (0.9, 1.0, 0.9), 'stone', 'tower', bevel=0.25)
    m.paint((0, 26.0, -0.6), (0.7, 1.4, 0.6), 'plate', ['tower'])
    m.tube([(0.4, 28.6, -3.4), (0.4, 35.6, -3.4)], [0.45, 0.4], 'plate', 'flag')
    m.tube([(0.4, 35.0, -3.4), (2.6, 34.4, -3.6), (5.0, 33.6, -3.2)], [1.3, 1.0, 0.3], 'flag', 'flag', flat=0.3,
           up=(0, 0, 1))
    # sturdy legs with digging claws
    for s in (-1, 1):
        for z, lg in ((7.4, 'legF%d' % s), (-7.4, 'legB%d' % s)):
            m.ell((s * 6.4, 8.4, z), (2.8, 3.6, 3.2), 'skin', lg)
            m.tube([(s * 6.6, 6.0, z), (s * 6.8, 1.8, z + 0.4)], [2.6, 2.4], 'skin', lg)
            for t in (-1, 0, 1):
                m.crystal((s * 6.8 + t * 1.3, 1.0, z + 1.8), (s * 6.8 + t * 1.6, 0.3, z + 3.8), 0.6, 'plate', lg,
                          sides=4, tip_frac=0.8)
    # ringed tail
    m.tube([(0, 9.8, -13.4), (0, 6.2, -17.0), (1.6, 3.0, -20.0)], [3.0, 2.0, 0.8], 'plate', 'tail')
    for z, y in ((-15.0, 8.4), (-17.4, 5.6)):
        m.paint((0, y, z), (3.6, 3.6, 0.5), 'brass', ['tail'])
    # a heavy helmeted head with a long snout
    head_c, head_r = (0, 10.0, 13.6), (4.6, 4.2, 4.6)
    m.ell(head_c, head_r, 'skin', 'head')
    m.ell((0, 12.4, 13.2), (4.6, 2.6, 4.8), 'plate', 'head')
    for x in (-2.4, 0, 2.4):
        m.sph((x, 14.6, 13.6 + (0.6 if x == 0 else 0)), 0.65, 'brass', 'head')
    m.tube([(0, 9.4, 16.6), (0, 8.2, 19.6), (0, 7.2, 21.6)], [2.8, 1.9, 1.2], 'skin', 'head')
    m.ell((0, 9.0, 18.8), (2.2, 1.0, 2.4), 'plate', 'head')
    m.sph((0, 7.3, 22.3), 1.0, 'plate', 'head')
    for s in (-1, 1):
        m.tube([(s * 2.8, 14.0, 11.8), (s * 3.8, 17.4, 10.8), (s * 4.2, 19.2, 10.2)], [1.8, 1.4, 0.4], 'skin',
               'ear%d' % s, flat=0.4, up=(0, 0.1, 1))
    g.eye_pair(m, head_c, head_r, 44, 6, 3.0, 3.0, style='cute', center=(0, 9, 20), turn=8)
    p, n = g.on(head_c, head_r, sdir(8, -28))
    m.mouth(p, n, 'line', w=3.0)
    return m


# ==========================================================================
# BLAZE: ember newt and foundry drake
# ==========================================================================
def salamber(g):
    m = g.Model('SALAMBER')
    m.outline = (36, 16, 26)
    m.mat('skin', CHAR)
    m.mat('belly', ['#b84a2a', '#ec8a3c'])
    m.mat('ember', EMBER, emissive=0.85)
    m.mat('flame', EMBER[:2], emissive=0.35)
    m.eye_dark = rgb(CHAR[0])
    m.white = rgb(EMBER[2])
    m.height = 34
    m.max_w = 60
    m.front_yaw = -50
    # long low body
    m.tube([(0, 3.6, 5.4), (0, 3.9, 1.0), (0, 3.6, -3.4), (0, 3.0, -6.0)], [2.6, 3.0, 2.8, 2.2], 'skin', 'body')
    m.paint((0, 1.2, 0), (2.8, 1.2, 7.0), 'belly', ['body'])
    # splayed little legs with round toes
    for s in (-1, 1):
        for z, lg in ((4.2, 'legF%d' % s), (-3.6, 'legB%d' % s)):
            m.tube([(s * 2.0, 3.2, z), (s * 4.2, 2.8, z + 0.6), (s * 5.0, 1.0, z + 1.2)], [1.6, 1.4, 1.2],
                   'skin', lg)
            for t in (-1, 0, 1):
                m.sph((s * (5.3 + 0.3 * t), 0.6, z + 1.8 + 0.2 * abs(t) - 0.2 + t * 0.2), 0.6, 'skin', lg)
    # a tail curling up over its back, a flicker of flame at the tip
    m.tube([(0, 3.2, -6.0), (0.8, 3.4, -9.2), (2.2, 5.6, -11.2), (3.0, 8.8, -10.8), (2.8, 11.0, -8.8)],
           [2.2, 1.8, 1.4, 1.0, 0.6], 'skin', 'tail')
    g.flame(m, (2.8, 11.2, -8.6), 4.6, 1.6, 'tail', mats=('flame', 'ember', 'ember'), up=(0.1, 1, 0.3),
            tongues=2, core=False, seed=3)
    # broad round newt head
    head_c, head_r = (0, 5.4, 9.2), (4.6, 3.6, 4.2)
    m.ell(head_c, head_r, 'skin', 'head')
    m.paint((0, 3.0, 11.0), (3.8, 1.4, 2.8), 'belly', ['head'])
    # glowing spots and a seam down the spine
    paint_path(g, m, [(0, 7.4, 7.6), (0, 6.6, 3.6), (0, 6.8, -1.0), (0, 6.2, -4.8), (0, 5.2, -7.0)], 0.55,
               'ember', ['body', 'head'])
    for (x, y, z, r) in ((2.3, 5.4, 3.6, 0.9), (-2.4, 5.6, 0.8, 0.95), (2.6, 5.2, -2.2, 0.9),
                         (-2.2, 4.8, -5.0, 0.8), (2.4, 5.8, 8.2, 0.7), (-2.3, 5.8, 8.4, 0.7)):
        m.paint((x, y, z), r, 'ember', ['body', 'head'])
    for (x, y, z) in ((1.8, 4.6, -10.4), (3.8, 8.4, -10.8)):
        m.paint((x, y, z), 0.6, 'ember', ['tail'])
    for s in (-1, 1):
        eb = g.on(head_c, head_r, sdir(s * 34 + 8, 34))[0]
        m.sph(eb, 1.4, 'skin', 'head')
        p, n = g.on(eb, 1.4, sdir(s * 30 + 20, 14))
        m.eye(p, n, 1.8, 2.0, style='iris', iris=('ember', 1), center=(0, 5, 14))
    p, n = g.on(head_c, head_r, sdir(12, -14))
    m.mouth(p, n, 'smile', w=5.0, color=('belly', 1))
    return m


def foundrake(g):
    m = g.Model('FOUNDRAKE')
    m.outline = (30, 16, 24)
    m.mat('skin', CHAR)
    m.mat('ingot', BRONZE)
    m.mat('ember', EMBER, emissive=0.85)
    m.mat('flame', EMBER[:2], emissive=0.35)
    m.mat('grate', CHAR[:1])
    m.eye_dark = rgb(CHAR[0])
    m.white = rgb(EMBER[2])
    m.height = 56
    m.max_w = 62
    m.front_yaw = -42
    # heavy low torso and deep chest with a belly furnace
    m.ell((0, 14.0, -1.0), (7.8, 7.4, 12.0), 'skin', 'body')
    m.ell((0, 14.6, 7.6), (7.2, 7.4, 6.4), 'skin', 'body')
    fc = (0, 11.8, 13.2)
    m.paint(fc, (4.0, 3.6, 1.8), 'ember', ['body'])
    for x in (-1.8, 0.0, 1.8):
        m.paint((x, 11.8, 13.4), (0.55, 3.6, 1.8), 'grate', ['body'])
    # glowing seams along the back, then the ingot plates over them
    for x in (-3.2, 0.0, 3.2):
        paint_path(g, m, [(x, 21.4, 10.0), (x * 1.05, 21.8, 2.0), (x * 1.05, 21.2, -6.0), (x, 19.6, -11.0)],
                   1.0, 'ember', ['body'])
    for z in (9.0, 4.6, 0.2, -4.2, -8.4):
        yb = 21.4 - 0.022 * z * z - (0.6 if z > 7 else 0.0)
        for x in (-4.9, -1.6, 1.6, 4.9):
            tilt = -x * 5.0
            m.box((x, yb - 0.08 * x * x, z), (1.2, 1.0, 1.6), 'ingot', 'plate', rot=(0, 0, tilt), bevel=0.45)
    # sturdy legs with dark claws
    for s in (-1, 1):
        lf = 'legF%d' % s
        m.ell((s * 6.4, 14.0, 8.4), (2.8, 4.4, 3.2), 'skin', lf)
        m.tube([(s * 6.6, 12.0, 8.8), (s * 7.0, 6.0, 9.6), (s * 7.0, 1.8, 10.0)], [2.6, 2.3, 2.4], 'skin', lf)
        m.box((s * 6.8, 9.4, 10.6), (1.6, 2.2, 1.0), 'ingot', lf, bevel=0.4)
        lb = 'legB%d' % s
        m.ell((s * 6.0, 13.0, -8.4), (3.2, 5.0, 4.2), 'skin', lb)
        m.tube([(s * 6.4, 10.0, -8.4), (s * 6.8, 5.0, -6.8), (s * 6.8, 1.8, -7.4)], [2.8, 2.4, 2.4], 'skin', lb)
        for lg, z in ((lf, 11.4), (lb, -5.0)):
            for t in (-1, 0, 1):
                m.crystal((s * 7.0 + t * 1.5, 1.0, z + 0.2), (s * 7.0 + t * 1.8, 0.4, z + 2.2), 0.6, 'ingot', lg,
                          sides=4, tip_frac=0.8)
    # thick plated tail ending in a molten tip
    m.tube([(0, 15.0, -11.6), (1.6, 11.4, -18.0), (5.6, 7.4, -22.4), (10.6, 6.0, -23.0), (13.4, 7.6, -21.4)],
           [4.2, 3.2, 2.4, 1.6, 0.9], 'skin', 'tail')
    for (p, r) in (((0.6, 15.6, -14.6), 1.6), ((2.8, 12.4, -19.0), 1.3), ((6.8, 9.6, -22.2), 1.0)):
        m.box(p, (r, 0.8, r * 1.1), 'ingot', 'tail', bevel=0.35)
    paint_path(g, m, [(0, 16.4, -12.0), (1.4, 13.2, -17.4), (5.0, 9.4, -21.6), (10.2, 8.0, -22.8)], 0.6,
               'ember', ['tail'])
    g.flame(m, (13.6, 8.0, -21.2), 7.0, 2.4, 'tail', mats=('flame', 'ember', 'ember'), up=(0.3, 1, 0.1),
            tongues=2, core=False, seed=5)
    # neck and a blocky drake head, turned toward the viewer
    m.tube([(0, 17.0, 10.0), (0, 20.6, 13.6), (0, 23.4, 15.4)], [5.0, 4.2, 3.8], 'skin', 'neck')
    head_c, head_r = (0, 25.2, 17.4), (4.6, 4.0, 4.6)
    m.ell(head_c, head_r, 'skin', 'head')
    mz_c, mz_r = (0, 23.8, 22.2), (3.4, 2.6, 3.8)
    m.ell(mz_c, mz_r, 'skin', 'head')
    m.ell((0, 21.4, 21.0), (3.0, 1.2, 3.6), 'skin', 'jaw')
    m.paint((0, 22.4, 22.8), (2.6, 0.6, 2.8), 'ember', ['head', 'jaw'])
    m.box((0, 28.4, 17.2), (2.6, 1.0, 2.8), 'ingot', 'head', bevel=0.4)
    for s in (-1, 1):
        m.tube([(s * 3.0, 28.0, 15.4), (s * 4.8, 30.4, 12.8), (s * 5.6, 31.4, 9.6)], [1.3, 0.9, 0.3], 'ingot',
               'horn%d' % s)
        m.paint((s * 1.3, 25.2, 25.8), (0.6, 0.6, 0.6), 'ember', ['head'])
        p, n = g.on(head_c, head_r, sdir(s * 40, 14))
        m.paint(p, (1.8, 1.4, 1.4), 'grate', ['head'])
    g.eye_pair(m, head_c, head_r, 40, 14, 3.4, 2.8, style='glow', iris=('ember', 1), slant=0.6,
               center=(0, 24, 26), minh=3, minw=2)
    # long drake: 3/4 view in the overworld down/up frames
    g.OW_TURN[m.name] = -38.0
    return m


# ---- end of batch ----
