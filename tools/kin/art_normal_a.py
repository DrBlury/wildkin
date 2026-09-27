"""Art for kin 32-66 (owner: KIN-A). One model function per species.

Every function takes the gen_monsters module as `g` (so it can use g.Model,
g.eye_pair, g.on, g.leaf, g.flame, g.lantern, ...) and returns a Model.
Shared helpers used only by this batch live at the top of this file.
Everything is deterministic (g.Rand with fixed seeds, no dict ordering).
"""

import math

DEG = math.pi / 180.0


# --------------------------------------------------------------------------
# small vector helpers (kept local so this file stands alone)
# --------------------------------------------------------------------------
def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def norm(a):
    ln = math.sqrt(dot(a, a))
    if ln < 1e-12:
        return (0.0, 0.0, 1.0)
    return (a[0] / ln, a[1] / ln, a[2] / ln)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t)


def fib_dirs(n, seed=0, jitter=0.0, g=None):
    """n roughly even directions on the unit sphere (golden spiral)."""
    ga = math.pi * (3 - math.sqrt(5))
    rnd = g.Rand(seed) if (g is not None and jitter) else None
    out = []
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        rad = math.sqrt(max(0.0, 1 - y * y))
        th = ga * i + (rnd.f() * jitter if rnd else 0.0)
        out.append((math.cos(th) * rad, y, math.sin(th) * rad))
    return out


def float_ow(g, m, lift, side_yaw=None):
    """Make a kin hover in its overworld frames (and optionally turn its
    profile toward the camera so wings / bells show)."""
    g.OW_FLOAT[m.name] = lift
    if side_yaw is not None:
        g.OW_SIDE_YAW[m.name] = side_yaw


def quill_coat(g, m, c, r, part, n=90, keep=None, length=4.5, rad=1.0,
               sweep=(0.0, 0.15, -0.6), mats=None, seed=1, lvar=0.35,
               tip=0.12):
    """A coat of tapering spines on an ellipsoid (hedgehog quills).
    keep(d) -> bool chooses which surface directions sprout a spine."""
    rnd = g.Rand(seed)
    for d in fib_dirs(n, seed, 0.35, g):
        if keep is not None and not keep(d):
            continue
        p, nn = g.on(c, r, d)
        dirn = norm(add(nn, sweep))
        ln = length * (1 - lvar * 0.5 + lvar * rnd.f())
        b = sub(p, mul(nn, rad * 0.6))
        m.tube([b, add(p, mul(dirn, ln * 0.5)), add(p, mul(dirn, ln))],
               [rad, rad * 0.62, tip], mats[0][1] if mats else 'quill', part,
               mats=mats)


def burr(g, m, c, r, part, mat='burr', seed=3):
    """A little spiky seed burr (hitchhiking seed)."""
    m.sph(c, r, mat, part)
    for d in fib_dirs(10, seed, 0.6, g):
        m.tube([c, add(c, mul(d, r * 1.9))], [r * 0.38, 0.12], mat, part)


def hoof(m, c, r, mat, part):
    m.ell(c, r, mat, part)


# ==========================================================================
# 32 PRICKLET -- hedgehog kit that rolls into a burr
# ==========================================================================
def pricklet(g):
    m = g.Model('PRICKLET')
    m.outline = (50, 28, 24)
    m.mat('quill', ['#4a2a22', '#744632', '#a06c48', '#cc9a68'])
    m.mat('face', ['#a87a5c', '#d8aa82', '#f6d8b0'])
    m.mat('nose', ['#34201e', '#6a463c'])
    m.mat('burr', ['#4e7028', '#8ab440', '#c4e070'])
    m.eye_dark = (36, 22, 20)
    m.white = (255, 250, 236)
    m.height = 28
    m.front_yaw = -30
    bc, br = (0, 7.4, -1.4), (7.2, 6.6, 8.0)
    m.ell(bc, br, 'quill', 'body')
    # little feet
    for s in (-1, 1):
        m.ell((s * 3.4, 1.2, 4.0), (1.7, 1.3, 2.1), 'face', 'legF%d' % s)
        m.ell((s * 3.8, 1.2, -5.0), (1.8, 1.3, 2.2), 'face', 'legB%d' % s)
    # pale face and pointed snout
    fc, fr = (0, 6.6, 4.8), (4.9, 4.6, 4.4)
    m.ell(fc, fr, 'face', 'head')
    m.tube([(0, 6.0, 7.4), (0, 5.4, 10.0), (0, 5.0, 11.8)], [2.8, 1.9, 1.2],
           'face', 'head')
    m.sph((0, 5.1, 12.5), 1.15, 'nose', 'head')
    m.group('head', 'body')
    for s in (-1, 1):
        m.ell((s * 4.1, 10.2, 3.6), (1.7, 1.8, 0.9), 'face', 'ear%d' % s,
              rot=(s * 25, 0, 0))
        m.paint((s * 4.1, 10.2, 4.1), (0.9, 1.0, 0.6), 'nose', ['ear%d' % s])

    # the spiny coat: everything but the face and belly, in swept rows
    def keep(d):
        return d[1] > -0.22 and dot(d, norm((0, 0.1, 1))) < 0.30
    quill_coat(g, m, bc, br, 'quills', n=64, keep=keep, length=5.6,
               rad=1.55, sweep=(0, 0.35, -0.8), seed=32, lvar=0.2)
    m.group('quills', 'body')
    # seed burrs caught in the quills
    for k, d in enumerate(((0.75, 0.6, -0.1), (0.1, 0.95, -0.35))):
        p, n = g.on(bc, br, d)
        burr(g, m, add(p, mul(n, 3.2)), 1.5, 'burr%d' % k, seed=5 + k)
    g.eye_pair(m, fc, fr, 36, 22, 2.8, 3.6, center=(0, 6, 11))
    p, n = g.on((0, 5.4, 10.0), (1.9, 1.9, 1.9), (0, -0.7, 0.7))
    m.mouth(p, n, 'smile', w=2.2)
    return m


# ==========================================================================
# 33 QUILLDRUM -- hedgehog that drums its quills as a warning
# ==========================================================================
def quilldrum(g):
    m = g.Model('QUILLDRUM')
    m.outline = (44, 24, 22)
    m.mat('fur', ['#4a2a22', '#744632', '#a06a46'])
    m.mat('tip', ['#d8bf94', '#fff2d2'])
    m.mat('face', ['#a07458', '#d4a67e', '#f4d6ae'])
    m.mat('nose', ['#30201e', '#624036'])
    m.mat('burr', ['#56782c', '#9cc050'])
    m.eye_dark = (34, 20, 18)
    m.white = (255, 250, 236)
    m.height = 54
    m.max_w = 60
    m.front_yaw = -24
    # stocky legs, broad feet
    for s in (-1, 1):
        m.ell((s * 4.8, 9.5, -0.5), (3.8, 5.2, 4.4), 'fur', 'leg%d' % s)
        m.tube([(s * 5.0, 7.0, 0.0), (s * 5.3, 3.0, 0.8)], [3.0, 2.6], 'fur',
               'leg%d' % s)
        m.ell((s * 5.4, 1.7, 2.4), (2.8, 1.7, 3.8), 'face', 'leg%d' % s)
    # barrel body, cream belly
    m.ell((0, 19.0, -0.5), (8.4, 9.8, 7.4), 'fur', 'body')
    m.paint((0, 18.0, 5.5), (6.0, 7.8, 3.4), 'face', ['body'])
    # rattle quills on the tail: short hollow cups
    rc = (0, 11.5, -7.0)
    for k, d in enumerate(((0, 0.5, -1), (-0.55, 0.35, -0.9), (0.55, 0.35, -0.9),
                           (-0.3, 0.9, -0.7), (0.3, 0.9, -0.7), (0, 0.1, -1),
                           (-0.7, 0.0, -0.8), (0.7, 0.0, -0.8))):
        d = norm(d)
        a = add(rc, mul(d, 1.0))
        b = add(rc, mul(d, 6.5))
        m.tube([a, b], [0.9, 1.35], 'tip', 'tail')
        m.paint(b, 0.9, 'nose', ['tail'])
    # arms raised in a guard, fists up
    for s in (-1, 1):
        sh = (s * 8.0, 25.0, 0.5)
        el = (s * 11.0, 19.5, 3.5)
        fs = (s * 7.4, 24.0, 8.2)
        m.sph(sh, 3.2, 'fur', 'arm%d' % s)
        m.tube([sh, el, fs], [2.9, 2.5, 2.4], 'fur', 'arm%d' % s)
        m.sph(fs, 3.0, 'face', 'arm%d' % s)
        m.paint(add(fs, (0, 1.2, 2.2)), (2.4, 1.0, 1.2), 'nose', ['arm%d' % s])
    # head with a pale face mask and a long pointed snout
    hc, hr = (0, 33.0, 1.0), (6.4, 5.8, 5.6)
    m.ell(hc, hr, 'fur', 'head')
    # the pale cone of the face, tapering to a black button nose
    m.tube([(0, 32.4, 2.6), (0, 31.4, 7.6), (0, 30.4, 11.6), (0, 30.0, 13.4)],
           [5.2, 4.0, 2.2, 1.3], 'face', 'head')
    m.sph((0, 30.2, 14.0), 1.6, 'nose', 'head')
    for s in (-1, 1):
        m.ell((s * 5.2, 37.4, 0.4), (2.0, 2.2, 1.0), 'face', 'head',
              rot=(s * 25, 0, 0))
    # a brush of short quills over the crown
    quill_coat(g, m, hc, hr, 'crest', n=40,
               keep=lambda d: d[1] > 0.25 and d[2] < 0.55, length=5.0, rad=1.3,
               sweep=(0, 0.2, -0.9), seed=35, lvar=0.3, mats=[(0, 'fur')])
    # the war crest: a raised fan of long banded quills behind the head and
    # shoulders (the crested-porcupine display), two rows deep
    band = [(0, 'nose'), (0.3, 'tip'), (0.5, 'nose'), (0.72, 'tip')]
    rnd = g.Rand(33)
    fan_c = (0, 26.0, -5.0)
    for row, (n, ln0, rr, dz) in enumerate(((13, 22.0, 1.6, 0.0),
                                            (10, 16.0, 1.5, 1.6))):
        for k in range(n):
            a = (-105 + 210.0 * k / (n - 1)) * DEG
            if row:
                a += 210.0 / (n - 1) / 2 * DEG
            d = norm((math.sin(a), math.cos(a) * 0.95 + 0.1, -0.55))
            ln = ln0 * (0.78 + 0.22 * math.cos(a * 0.8)) * (0.92 + 0.16 * rnd.f())
            b = add(fan_c, (math.sin(a) * 3.0, math.cos(a) * 4.0, dz))
            m.tube([b, add(b, mul(d, ln * 0.5)), add(b, mul(d, ln))],
                   [rr, rr * 0.75, 0.2], 'nose', 'crest', mats=band)
    # short spurs on the forearms
    for s in (-1, 1):
        for k in range(3):
            b = (s * (10.0 - k * 1.1), 20.5 + k * 1.6, 3.0 + k * 1.6)
            d = norm((s * 0.9, 0.2, -0.5))
            m.tube([b, add(b, mul(d, 5.0))], [1.0, 0.15], 'nose', 'arm%d' % s,
                   mats=[(0, 'nose'), (0.6, 'tip')])
    for k, (p, r) in enumerate((((9.5, 38.0, -8.0), 1.6), ((-7.0, 33.0, -9.0), 1.4))):
        burr(g, m, p, r, 'burr%d' % k, seed=11 + k)
    for s in (-1, 1):
        m.eye((s * 3.0, 35.0, 5.4), (s * 0.5, 0.35, 0.8), 2.8, 3.4, slant=0.55,
              center=(0, 33, 12))
    p, n = g.on((0, 30.6, 10.2), (2.6, 2.6, 2.6), (0.1, -0.8, 0.6))
    m.mouth(p, n, 'smile', w=3.0, fang=1)
    return m


# ==========================================================================
# 34 SNUFFLET -- truffle piglet with a leaf on its snout
# ==========================================================================
def snufflet(g):
    m = g.Model('SNUFFLET')
    m.outline = (60, 30, 30)
    m.mat('skin', ['#94605a', '#c88c7c', '#eab4a0', '#fcd8c4'])
    m.mat('spot', ['#5a3a2e', '#86583e'])
    m.mat('snout', ['#b46a6a', '#e8a09a'])
    m.mat('leaf', ['#2e6e2c', '#5aa23a', '#a8d86a'])
    m.eye_dark = (40, 24, 26)
    m.white = (255, 250, 240)
    m.height = 27
    m.front_yaw = -30
    # round body, short trotters
    bc, br = (0, 7.6, -1.5), (6.2, 5.8, 7.6)
    m.ell(bc, br, 'skin', 'body')
    m.paint((2.5, 10.0, -4.0), (3.6, 3.0, 3.0), 'spot', ['body'])
    m.paint((-3.0, 8.5, -6.5), (2.6, 2.6, 2.4), 'spot', ['body'])
    for s in (-1, 1):
        for zz, nm in ((3.2, 'F'), (-5.6, 'B')):
            m.tube([(s * 3.4, 4.5, zz), (s * 3.5, 1.6, zz + 0.3)], [1.7, 1.5],
                   'skin', 'leg%s%d' % (nm, s))
            m.ell((s * 3.5, 1.0, zz + 0.4), (1.6, 1.0, 1.7), 'spot',
                  'leg%s%d' % (nm, s))
    # curly tail
    pts = []
    for i in range(9):
        a = i / 8.0 * 1.6 * 2 * math.pi
        rr = 1.4 * (1 - i / 12.0)
        pts.append((math.sin(a) * rr, 10.0 + math.cos(a) * rr, -9.0 - i * 0.18))
    m.tube(pts, 0.55, 'skin', 'tail')
    # head
    hc, hr = (0, 10.0, 5.2), (5.4, 4.9, 4.6)
    m.ell(hc, hr, 'skin', 'head')
    sc, sr = (0, 8.8, 10.2), (3.0, 2.5, 1.8)
    m.tube([(0, 9.0, 7.5), (0, 8.8, 9.6)], [2.9, 2.8], 'skin', 'head')
    m.ell(sc, sr, 'snout', 'head')
    for s in (-1, 1):
        m.dot(g.on(sc, sr, (s * 0.45, -0.05, 1))[0], (0, 0, 1), w=1.0, h=1.3,
              color=('spot', 0), minw=1, minh=2)
        # floppy ears folding forward
        m.tube([(s * 3.4, 13.4, 4.6), (s * 5.4, 14.4, 5.6), (s * 6.4, 12.4, 7.2)],
               [1.9, 1.6, 0.4], 'skin', 'ear%d' % s, flat=0.4, up=(s * 0.3, 1, 0.2))
    # a truffle-brown patch round one eye
    m.paint(g.on(hc, hr, (0.62, 0.3, 0.72))[0], (2.3, 2.1, 2.0), 'spot', ['head'])
    # a seedling sprouting from the top of the snout: stem + two leaves
    st0, st1 = (-0.4, 10.2, 10.6), (-1.0, 14.0, 11.4)
    m.tube([st0, lerp(st0, st1, 0.5), st1], [0.5, 0.45, 0.4], 'leaf', 'leaf')
    g.leaf(m, st1, add(st1, (-1.8, 1.6, 0.2)), add(st1, (-4.4, 2.2, 0.0)), 1.5,
           'leaf', 'leaf', up=(0.3, 1, 0.3), flat=0.3)
    g.leaf(m, st1, add(st1, (1.4, 1.8, 0.0)), add(st1, (3.2, 3.2, -0.6)), 1.3,
           'leaf', 'leaf', up=(-0.3, 1, 0.3), flat=0.3)
    g.eye_pair(m, hc, hr, 34, 16, 2.8, 3.4, center=(0, 9, 12))
    p, n = g.on(hc, hr, (0.0, -0.55, 0.85))
    m.mouth(p, n, 'smile', w=2.4)
    for s in (-1, 1):
        m.dot(g.on(hc, hr, (s * 0.72, -0.2, 0.66))[0], (s * 0.6, 0, 0.8),
              w=1.3, h=0.8, color=('snout', 1), minw=2)
    return m


# ==========================================================================
# 35 TRUFFLOAR -- boar with a mossy garden on its back
# ==========================================================================
def truffloar(g):
    m = g.Model('TRUFFLOAR')
    m.outline = (34, 22, 20)
    m.mat('fur', ['#3a2620', '#63402e', '#94664a'])
    m.mat('snout', ['#a8625e', '#e0968a'])
    m.mat('moss', ['#2c5a22', '#4e8a32', '#8cc254'])
    m.mat('tusk', ['#c8b890', '#fff4d8'])
    m.mat('cap', ['#9a3a2a', '#e06a44'])
    m.mat('spot', ['#3a2620'])
    m.eye_dark = (30, 18, 16)
    m.white = (255, 248, 230)
    m.height = 50
    m.max_w = 62
    m.front_yaw = -32
    # sturdy legs, dark hooves
    for s in (-1, 1):
        for zz, nm, top in ((9.5, 'F', 14.0), (-11.0, 'B', 15.0)):
            m.tube([(s * 5.4, top, zz), (s * 5.6, 7.0, zz + 0.4),
                    (s * 5.6, 2.4, zz + 0.8)], [3.6, 2.6, 2.3], 'fur',
                   'leg%s%d' % (nm, s))
            m.ell((s * 5.6, 1.4, zz + 1.2), (2.4, 1.4, 2.6), 'spot',
                  'leg%s%d' % (nm, s))
    # massive body, higher at the shoulders
    m.ell((0, 17.5, -2.0), (9.6, 8.8, 15.0), 'fur', 'body', rot=(0, -5, 0))
    m.ell((0, 20.5, 7.0), (9.8, 9.6, 8.0), 'fur', 'body')
    # bristly dark mane along the spine
    for k in range(10):
        t = k / 9.0
        b = (0, 29.5 - t * 4.5, 10.0 - t * 22.0)
        m.tube([b, add(b, (0, 3.0 - t, -2.0))], [1.5, 0.2], 'spot', 'mane')
    # head, lowered, with a pink snout disc and curling tusks
    hc, hr = (0, 16.5, 17.5), (6.8, 6.6, 6.2)
    m.ell(hc, hr, 'fur', 'head')
    m.tube([(0, 15.0, 20.0), (0, 13.6, 23.0)], [4.2, 3.6], 'fur', 'head')
    sc, sr = (0, 13.4, 24.6), (3.6, 3.0, 1.9)
    m.ell(sc, sr, 'snout', 'head')
    for s in (-1, 1):
        m.dot(g.on(sc, sr, (s * 0.45, 0.0, 1))[0], (0, 0, 1), w=0.9, h=1.3,
              color=('spot', 0), minw=1, minh=1)
        b = (s * 3.4, 12.2, 21.6)
        m.tube([b, add(b, (s * 1.8, 1.4, 1.2)), add(b, (s * 2.6, 4.8, 0.8)),
                add(b, (s * 1.8, 6.6, -0.4))], [1.2, 1.0, 0.7, 0.15], 'tusk',
               'tusk%d' % s)
        m.tube([(s * 5.0, 21.5, 15.5), (s * 7.6, 23.6, 14.0),
                (s * 9.0, 22.4, 12.0)], [2.4, 1.7, 0.3], 'fur', 'ear%d' % s,
               flat=0.4, up=(s * 0.2, 1, 0.3))
    # the leaf on its snout has grown into a sapling
    lb = (0, 16.4, 23.4)
    m.tube([(0, 15.2, 23.0), lb, (0.6, 19.0, 23.6)], [0.6, 0.55, 0.4], 'moss',
           'sprout')
    for s, (dx, dy) in ((-1, (-3.2, 3.0)), (1, (3.4, 3.8))):
        q = (0.6, 19.0, 23.6)
        g.leaf(m, q, add(q, (dx * 0.5, dy * 0.6, 0.3)), add(q, (dx, dy, 0.2)),
               1.6, 'moss', 'sprout', up=(0, 0.3, 1), flat=0.3)
    # the garden on its back: a moss mat, ferns, mushrooms and a flower
    m.paint((0, 27.0, -1.0), (10.8, 5.5, 16.0), 'moss', ['body'])
    rnd = g.Rand(35)
    for k in range(14):
        t = k / 13.0
        x = (rnd.f() - 0.5) * 12.0
        z = 12.0 - t * 26.0
        y = 25.0 + 2.2 * math.cos((z + 2) / 16.0 * 1.5) - abs(x) * 0.25
        m.sph((x, y, z), 2.0 + rnd.f() * 1.3, 'moss', 'garden')
    for (b, d, ln, w) in (((-3.5, 27.5, -6.0), (-0.6, 1.0, -0.2), 8.0, 1.8),
                          ((4.0, 27.5, -10.0), (0.7, 1.0, -0.3), 7.5, 1.7),
                          ((1.0, 28.0, 2.0), (0.3, 1.0, 0.3), 6.5, 1.6),
                          ((-2.0, 26.5, -14.0), (-0.3, 0.8, -0.8), 6.5, 1.5)):
        d = norm(d)
        up = norm(cross(d, (0, 0, 1) if abs(d[2]) < 0.7 else (1, 0, 0)))
        if up[1] < 0:
            up = mul(up, -1)
        g.jagged_leaf(m, b, d, ln, w, 'moss', 'fern', up=up, teeth=4)
    for k, (b, h, cr) in enumerate((((3.2, 27.5, -3.0), 3.2, 2.6),
                                     ((5.0, 26.5, 4.5), 2.4, 1.9),
                                     ((-4.6, 27.0, 1.0), 2.6, 2.1),
                                     ((-1.0, 27.5, -9.5), 2.0, 1.7))):
        top = add(b, (0, h, 0))
        m.tube([b, top], [0.8, 0.7], 'tusk', 'mush%d' % k)
        m.ell(top, (cr, cr * 0.62, cr), 'cap', 'mush%d' % k)
        m.paint(add(top, (cr * 0.3, cr * 0.5, cr * 0.2)), cr * 0.3, 'tusk',
                ['mush%d' % k])
    # short tufted tail
    m.tube([(0, 20.0, -16.5), (0.8, 17.0, -18.5), (1.2, 14.0, -18.8)],
           [1.0, 0.8, 0.6], 'fur', 'tail')
    m.ell((1.3, 13.2, -18.8), (1.2, 1.8, 1.2), 'spot', 'tail')
    g.eye_pair(m, hc, hr, 38, 20, 3.2, 3.2, style='iris', iris=('moss', 2),
               slant=0.5, center=(0, 16, 24), turn=4)
    p, n = g.on(hc, hr, (0.1, -0.62, 0.75))
    m.mouth(p, n, 'smile', w=3.4)
    return m


# ==========================================================================
# 36 RACCOIN -- masked raccoon hoarding shiny coins
# ==========================================================================
def ringed_tail(m, pts, radii, part, rings=3, fur='fur', dark='dark'):
    """Bushy tail with dark rings, ending dark."""
    mats = [(0, fur)]
    for k in range(rings):
        t0 = 0.18 + k * (0.78 / rings)
        mats.append((t0, dark))
        mats.append((t0 + 0.4 / rings, fur))
    mats.append((0.9, dark))
    m.tube(pts, radii, fur, part, mats=mats)


def coin(m, c, r, part, rot, mat='gold', hole='dark', th=0.55):
    m.ell(c, (r, r, th), mat, part, rot=rot)
    m.paint(c, (r * 0.32, r * 0.32, th * 2.2), hole, [part], rot=rot)


def raccoin(g):
    m = g.Model('RACCOIN')
    m.outline = (30, 28, 40)
    m.mat('fur', ['#4a4858', '#737486', '#a4a6b6', '#cfd0da'])
    m.mat('dark', ['#221f2c', '#3e3a4a'])
    m.mat('cream', ['#cfc8b8', '#f8f4e8'])
    m.mat('gold', ['#8e5a12', '#d69a26', '#ffe06a'], spec=0.5)
    m.eye_dark = (22, 20, 30)
    m.white = (255, 255, 248)
    m.height = 30
    m.front_yaw = -26
    # ringed tail curling up on its left (+X, toward the camera)
    ringed_tail(m, [(1.0, 4.0, -4.5), (5.0, 3.6, -7.5), (8.6, 6.6, -8.0),
                    (10.2, 11.0, -6.0), (9.6, 15.0, -4.4)],
                [2.0, 2.8, 3.0, 2.6, 1.2], 'tail', rings=3)
    # haunches and feet (sitting)
    for s in (-1, 1):
        m.ell((s * 3.8, 4.8, -0.6), (3.0, 3.6, 4.0), 'fur', 'leg%d' % s)
        m.ell((s * 3.6, 1.2, 2.8), (1.8, 1.2, 2.6), 'dark', 'leg%d' % s)
    # pear-shaped body, pale belly
    m.ell((0, 9.4, -0.4), (5.4, 6.6, 4.8), 'fur', 'body')
    m.paint((0, 8.6, 3.6), (3.6, 5.0, 2.2), 'cream', ['body'])
    # the prize: a big square-holed coin hugged to the chest
    cc = (0.2, 10.4, 5.4)
    coin(m, cc, 3.3, 'coin', rot=(-12, 8, 0))
    for s in (-1, 1):
        sh = (s * 4.6, 13.2, 1.0)
        pw = (s * 2.6, 10.6, 5.6)
        m.tube([sh, (s * 5.4, 10.2, 3.2), pw], [1.5, 1.3, 1.2], 'fur', 'arm%d' % s)
        m.sph(add(pw, (s * 0.6, 0, 0.4)), 1.4, 'dark', 'arm%d' % s)
    # a little stack of coins at its feet
    for k in range(3):
        coin(m, (-5.2 + k * 0.25, 0.7 + k * 1.05, 4.4), 1.9, 'stack',
             rot=(0, 90, 0), th=0.5)
    # head: round, pointed muzzle, mask, big ears
    hc, hr = (0, 18.2, 1.2), (5.8, 5.0, 5.0)
    m.ell(hc, hr, 'fur', 'head')
    mz_c, mz_r = (0, 16.6, 5.4), (2.6, 2.1, 2.4)
    m.ell(mz_c, mz_r, 'cream', 'head')
    m.sph((0, 17.2, 7.6), 0.95, 'dark', 'head')
    # the mask: a dark band across the eyes, pale brows above
    for s in (-1, 1):
        p, n = g.on(hc, hr, (s * 0.52, 0.12, 0.84))
        m.paint(p, (2.8, 1.9, 2.4), 'dark', ['head'], rot=(0, 0, -s * 12))
        m.paint(add(p, (s * 0.2, 2.0, -0.2)), (2.0, 0.8, 1.8), 'cream', ['head'])
    for s in (-1, 1):
        m.tube([(s * 3.4, 21.6, 0.2), (s * 4.8, 24.8, -0.2), (s * 5.4, 26.4, -0.4)],
               [2.6, 1.8, 0.3], 'fur', 'ear%d' % s, flat=0.45, up=(0, 0.2, 1))
        m.paint((s * 4.6, 24.6, 0.6), (1.2, 1.8, 0.9), 'cream', ['ear%d' % s])
        # cheek ruff
        m.tube([(s * 4.6, 16.4, 2.4), (s * 6.8, 15.2, 1.6), (s * 7.6, 14.2, 0.8)],
               [1.8, 1.1, 0.2], 'cream', 'head', flat=0.5, up=(0, 0, 1))
    g.eye_pair(m, hc, hr, 30, 12, 3.0, 3.4, style='iris', iris=('gold', 2),
               center=(0, 17, 9))
    p, n = g.on(mz_c, mz_r, (0.05, -0.5, 1))
    m.mouth(p, n, 'w', w=2.6)
    m.sparkle(add(cc, (-1.4, 1.6, 0.8)), (0, 0, 1), size=1)
    return m


# ==========================================================================
# 37 BANDIRACC -- bandit raccoon with a bandana and a coin sack
# ==========================================================================
def bandiracc(g):
    m = g.Model('BANDIRACC')
    m.outline = (26, 24, 36)
    m.mat('fur', ['#44424f', '#6c6c80', '#9ea0b2'])
    m.mat('dark', ['#1e1b28', '#383446'])
    m.mat('cream', ['#ece6d8'])
    m.mat('red', ['#8a2030', '#d2443c'])
    m.mat('sack', ['#6e5438', '#a8845a'])
    m.mat('gold', ['#c08a1c', '#ffe070'], spec=0.5)
    m.eye_dark = (20, 18, 28)
    m.white = (255, 255, 248)
    m.height = 54
    m.max_w = 60
    m.front_yaw = -22
    # big ringed tail sweeping out to its right (-X)
    ringed_tail(m, [(-1.0, 13.0, -4.0), (-6.0, 9.0, -8.0), (-12.0, 9.5, -8.5),
                    (-16.0, 14.0, -6.5), (-16.5, 19.5, -4.5)],
                [2.4, 3.8, 4.4, 3.8, 1.6], 'tail', rings=4)
    # lean legs, dark 'gloves' and boots
    for s in (-1, 1):
        m.ell((s * 3.8, 13.0, -0.2), (3.0, 4.8, 3.6), 'fur', 'leg%d' % s,
              rot=(0, -8, s * 4))
        m.tube([(s * 4.0, 10.0, -1.0), (s * 4.4, 5.0, -1.4), (s * 4.5, 2.2, -0.4)],
               [2.2, 1.7, 1.6], 'fur', 'leg%d' % s,
               mats=[(0, 'fur'), (0.55, 'dark')])
        m.ell((s * 4.6, 1.3, 1.8), (1.9, 1.3, 3.2), 'dark', 'leg%d' % s)
    # torso, pale belly
    m.ell((0, 20.0, -0.4), (5.4, 6.8, 4.2), 'fur', 'body')
    m.ell((0, 27.0, 0.2), (6.4, 5.0, 4.4), 'fur', 'body')
    m.paint((0, 21.0, 3.4), (3.4, 6.6, 2.0), 'cream', ['body'])
    # the coin sack slung over its left shoulder (+X), held by the neck
    sk_c, sk_r = (9.6, 27.0, -6.0), (5.6, 6.4, 5.2)
    m.ell(sk_c, sk_r, 'sack', 'sack', rot=(0, 0, -20))
    m.tube([(7.0, 32.6, -2.6), (7.6, 31.6, -0.2), (7.2, 30.2, 2.0)],
           [1.7, 1.4, 1.2], 'sack', 'sack')
    m.paint(g.on(sk_c, sk_r, (0.8, 0.1, 0.55))[0], (2.0, 2.0, 1.6), 'red', ['sack'])
    for k, d in enumerate(((0.25, 0.85, 0.45), (0.65, 0.7, 0.1))):
        p, n = g.on(sk_c, sk_r, d)
        coin(m, add(p, mul(n, 0.3)), 1.7, 'loot', rot=(-30 + k * 50, 20, 0), th=0.45)
    # arms: left hand grips the sack at the shoulder, right flips a coin
    m.sph((6.4, 27.8, 0.2), 2.5, 'fur', 'armL')
    m.tube([(6.4, 27.8, 0.2), (9.0, 24.2, 2.6), (7.4, 29.8, 2.6)],
           [2.1, 1.7, 1.5], 'fur', 'armL', mats=[(0, 'fur'), (0.6, 'dark')])
    m.sph((7.2, 30.6, 2.2), 1.8, 'dark', 'armL')
    m.sph((-6.4, 27.8, 0.2), 2.5, 'fur', 'armR')
    m.tube([(-6.4, 27.8, 0.2), (-10.2, 26.0, 2.8), (-11.0, 31.4, 4.6)],
           [2.1, 1.7, 1.5], 'fur', 'armR', mats=[(0, 'fur'), (0.6, 'dark')])
    m.sph((-11.0, 32.2, 4.8), 1.7, 'dark', 'armR')
    coin(m, (-11.4, 37.2, 5.0), 2.0, 'flip', rot=(0, 30, -20), th=0.5)
    # the bandana: a red kerchief knotted at the neck, point on the chest,
    # knot tails flicking out behind
    for k in range(9):
        a = (-160 + 320.0 * k / 8) * DEG
        m.sph((math.sin(a) * 4.4, 31.0 - 0.4 * math.cos(a), 0.8 + math.cos(a) * 3.2),
              1.7, 'red', 'bandana')
    m.poly([(-3.8, 31.2, 4.0), (3.8, 31.2, 4.0), (0.4, 25.4, 5.4)], 'red', 'bandana',
           puff=0.3)
    for s in (-1, 1):
        m.tube([(s * 0.8, 31.4, -3.0), (s * 3.0, 30.4, -6.4), (s * 4.6, 31.2, -9.0)],
               [1.2, 1.0, 0.3], 'red', 'bandana', flat=0.4, up=(0, 1, 0))
    # head: mask, muzzle, big ears, sly look
    hc, hr = (0, 37.0, 1.4), (6.0, 5.2, 5.2)
    m.ell(hc, hr, 'fur', 'head')
    mz_c, mz_r = (0, 35.2, 5.8), (2.8, 2.2, 2.6)
    m.ell(mz_c, mz_r, 'cream', 'head')
    m.sph((0, 35.9, 8.2), 1.05, 'dark', 'head')
    for s in (-1, 1):
        p, n = g.on(hc, hr, (s * 0.52, 0.14, 0.84))
        m.paint(p, (3.0, 2.0, 2.5), 'dark', ['head'], rot=(0, 0, -s * 14))
        m.paint(add(p, (s * 0.2, 2.1, -0.2)), (2.2, 0.8, 1.8), 'cream', ['head'])
        m.tube([(s * 3.6, 40.8, 0.2), (s * 5.2, 44.4, -0.4), (s * 5.8, 46.4, -0.6)],
               [2.8, 1.9, 0.3], 'fur', 'ear%d' % s, flat=0.45, up=(0, 0.2, 1))
        m.paint((s * 4.9, 44.0, 0.5), (1.3, 1.9, 0.9), 'cream', ['ear%d' % s])
        m.tube([(s * 4.8, 35.4, 2.4), (s * 6.6, 34.2, 1.6), (s * 7.2, 33.2, 0.8)],
               [1.8, 1.1, 0.2], 'fur', 'head', flat=0.5, up=(0, 0, 1))
    g.eye_pair(m, hc, hr, 30, 14, 3.4, 3.2, style='sharp', iris=('gold', 1),
               slant=0.8, lid=1, center=(0, 36, 10))
    p, n = g.on(mz_c, mz_r, (0.2, -0.45, 1))
    m.mouth(p, n, 'smile', w=2.8, fang=1)
    m.sparkle((-11.4, 39.6, 6.0), (0, 0, 1), size=1)
    return m


# ==========================================================================
# 38 PEBBOTTER -- otter juggling river stones
# ==========================================================================
def pebble(m, c, r, part, seed, mat='stone', rot=None):
    m.rock(c, r, mat, part, seed=seed, n=14, jitter=0.05, shrink=0.97, rot=rot)


def otter_head(g, m, hc, hr, fur='fur', cream='cream', nose='nose', ear=1.5):
    m.ell(hc, hr, fur, 'head')
    mz_c = add(hc, (0, -hr[1] * 0.28, hr[2] * 0.72))
    mz_r = (hr[0] * 0.55, hr[1] * 0.42, hr[2] * 0.45)
    m.ell(mz_c, mz_r, cream, 'head')
    m.paint(add(hc, (0, -hr[1] * 0.4, hr[2] * 0.5)),
            (hr[0] * 0.72, hr[1] * 0.45, hr[2] * 0.5), cream, ['head'])
    nz = add(mz_c, (0, mz_r[1] * 0.45, mz_r[2] * 0.85))
    m.ell(nz, (mz_r[0] * 0.42, mz_r[1] * 0.32, mz_r[2] * 0.3), nose, 'head')
    for s in (-1, 1):
        m.ell(add(hc, (s * hr[0] * 0.78, hr[1] * 0.55, -hr[2] * 0.2)),
              (ear, ear, ear * 0.6), fur, 'head', rot=(s * 30, 0, 0))
        # whiskers
        for k in (-1, 1):
            b = add(mz_c, (s * mz_r[0] * 0.8, k * 0.3, mz_r[2] * 0.3))
            m.tube([b, add(b, (s * hr[0] * 0.55, k * 0.5 - 0.2, -0.4))],
                   [0.22, 0.12], cream, 'whisk')
    return mz_c, mz_r


def pebbotter(g):
    m = g.Model('PEBBOTTER')
    m.outline = (40, 26, 22)
    m.mat('fur', ['#4a2c1e', '#7a4c30', '#a8744a', '#d09e6c'])
    m.mat('cream', ['#d8c2a0', '#fbefd6'])
    m.mat('stone', ['#4a5870', '#7a8ca4', '#b4c4d4'])
    m.mat('nose', ['#2e1c18'])
    m.mat('water', ['#3c86d0', '#8cd0f4'])
    m.eye_dark = (32, 20, 18)
    m.white = (255, 255, 248)
    m.height = 32
    m.front_yaw = -24
    # thick tail curling round in front of its feet
    m.tube([(0, 3.0, -4.0), (4.5, 1.6, -5.0), (7.5, 1.4, -1.0), (6.5, 1.3, 3.5),
            (3.5, 1.2, 5.6)], [2.6, 2.4, 2.0, 1.4, 0.4], 'fur', 'tail')
    # sitting haunches and webbed feet
    for s in (-1, 1):
        m.ell((s * 3.4, 4.2, -0.4), (2.8, 3.4, 3.8), 'fur', 'leg%d' % s)
        m.ell((s * 3.2, 1.1, 3.0), (1.9, 1.1, 2.4), 'fur', 'leg%d' % s)
    # long body, leaning back a little
    m.ell((0, 10.0, -0.8), (4.8, 7.4, 4.4), 'fur', 'body', rot=(0, -8, 0))
    m.paint((0, 9.6, 3.0), (3.2, 6.0, 2.0), 'cream', ['body'])
    # head
    hc, hr = (0, 20.0, 0.6), (5.0, 4.4, 4.4)
    mz_c, mz_r = otter_head(g, m, hc, hr, ear=1.3)
    # arms up, juggling: one stone in each paw, one in the air overhead
    stones = [((-6.6, 21.6, 3.2), 1.9, 7), ((1.2, 30.0, 2.0), 2.1, 8),
              ((7.6, 24.6, 2.6), 1.8, 9)]
    for s, (sh, el, pw) in ((-1, ((-4.2, 15.2, 0.6), (-6.8, 16.0, 2.4), (-6.4, 19.4, 3.4))),
                            (1, ((4.2, 15.2, 0.6), (6.6, 17.8, 2.0), (7.0, 22.2, 2.6)))):
        m.tube([sh, el, pw], [1.5, 1.3, 1.2], 'fur', 'arm%d' % s)
        m.sph(pw, 1.35, 'fur', 'arm%d' % s)
    for k, (c, r, sd) in enumerate(stones):
        pebble(m, c, (r, r * 0.85, r), 'stone%d' % k, sd)
        m.paint(add(c, (-r * 0.35, r * 0.4, r * 0.3)), r * 0.35, 'water',
                ['stone%d' % k])
    # a dotted arc showing the juggle
    for t in (0.3, 0.5, 0.7):
        a = math.pi * t
        m.sph((-6.2 * math.cos(a) + 0.6, 26.0 + 6.0 * math.sin(a) - 1.5, 2.4), 0.45,
              'water', 'arc')
    g.eye_pair(m, hc, hr, 30, 16, 2.8, 3.4, iris=('fur', 0), center=(0, 19, 8))
    p, n = g.on(mz_c, mz_r, (0, -0.55, 1))
    m.mouth(p, n, 'w', w=2.6)
    return m


# ==========================================================================
# 39 TORRENTTER -- river otter with a stone club
# ==========================================================================
def torrentter(g):
    m = g.Model('TORRENTTER')
    m.outline = (34, 22, 20)
    m.mat('fur', ['#42261a', '#6e4228', '#9c6a40'])
    m.mat('cream', ['#d4bc98', '#f8ead0'])
    m.mat('stone', ['#44506a', '#6e809a', '#a6b8cc'])
    m.mat('wood', ['#6a4a2c', '#a47c4c'])
    m.mat('reed', ['#3c6a2c', '#74a444'])
    m.mat('nose', ['#42261a'])
    m.eye_dark = (28, 18, 16)
    m.white = (255, 255, 248)
    m.height = 56
    m.max_w = 60
    m.front_yaw = -22
    # heavy rudder tail propping it up behind
    m.tube([(0, 11.0, -3.5), (1.5, 6.0, -8.5), (3.5, 2.2, -13.5), (5.5, 1.4, -17.5)],
           [3.8, 3.4, 2.4, 0.6], 'fur', 'tail', flat=0.6, up=(0, 1, 0))
    # legs: strong haunches, webbed feet planted wide
    for s in (-1, 1):
        m.ell((s * 4.6, 10.0, -0.4), (3.6, 5.4, 4.4), 'fur', 'leg%d' % s,
              rot=(0, -6, s * 6))
        m.tube([(s * 5.0, 7.0, -0.2), (s * 5.4, 3.0, 0.6)], [2.6, 2.3], 'fur',
               'leg%d' % s)
        m.ell((s * 5.6, 1.4, 2.6), (2.6, 1.4, 3.6), 'fur', 'leg%d' % s)
    # long muscular torso, pale chest
    m.ell((0, 19.0, -0.2), (6.2, 8.0, 5.0), 'fur', 'body')
    m.ell((0, 28.5, 0.6), (7.4, 5.8, 5.2), 'fur', 'body')
    m.paint((0, 24.0, 4.2), (4.2, 9.0, 2.2), 'cream', ['body'])
    # a reed sash across the chest
    for k in range(10):
        t = k / 9.0
        a = lerp((-6.2, 31.0, 2.0), (5.6, 16.5, 3.0), t)
        zc = 5.2 * math.sin(math.pi * (0.15 + 0.7 * t)) + 0.2
        m.sph((a[0], a[1], zc), 1.25, 'reed', 'sash')
    # arms: right arm shoulders the stone club, left fist forward
    m.sph((-7.2, 29.0, 0.6), 3.0, 'fur', 'armR')
    m.tube([(-7.2, 29.0, 0.6), (-10.4, 23.2, 2.8), (-8.4, 28.2, 5.6)],
           [2.7, 2.3, 2.1], 'fur', 'armR')
    m.sph((-8.2, 28.8, 6.0), 2.3, 'fur', 'armR')
    m.sph((7.2, 29.0, 0.6), 3.0, 'fur', 'armL')
    m.tube([(7.2, 29.0, 0.6), (10.6, 23.6, 2.6), (8.6, 20.4, 7.6)],
           [2.7, 2.3, 2.1], 'fur', 'armL')
    m.sph((8.4, 20.2, 8.4), 2.4, 'fur', 'armL')
    # the club: driftwood haft, a big river stone lashed on with reed
    h0, h1 = (-8.0, 22.5, 7.8), (-9.0, 40.0, -3.0)
    m.tube([h0, lerp(h0, h1, 0.5), h1], [0.95, 1.0, 1.1], 'wood', 'club')
    sc = add(h1, (-0.6, 3.4, -1.6))
    pebble(m, sc, (5.2, 4.4, 4.6), 'club', seed=39, rot=(20, 10, 30))
    for k in range(7):
        a = k / 6.0 * 2 * math.pi
        m.sph(add(h1, (math.cos(a) * 1.4, 0.2 + k * 0.25, math.sin(a) * 1.4)), 0.6,
              'reed', 'club')
    # head
    hc, hr = (0, 37.6, 1.8), (5.6, 5.0, 5.0)
    mz_c, mz_r = otter_head(g, m, hc, hr, ear=1.5)
    g.eye_pair(m, hc, hr, 30, 18, 3.4, 3.2, style='sharp', iris=('fur', 1),
               slant=0.6, lid=1, center=(0, 36, 10))
    p, n = g.on(mz_c, mz_r, (0.15, -0.55, 1))
    m.mouth(p, n, 'smile', w=2.8, fang=1)
    return m


# ==========================================================================
# 40 JELLUME -- jellyfish whose bell glows like a lamp
# ==========================================================================
def jelly_bell(m, c, r, part, mat, rim_mat, scallops=12, rim_r=1.1, rim_y=0.0):
    """Dome bell (upper ellipsoid) with a scalloped rim round its base."""
    m.ell(c, r, mat, part)
    for k in range(scallops):
        a = 2 * math.pi * k / scallops
        m.sph((c[0] + math.sin(a) * r[0] * 0.92, c[1] + rim_y,
               c[2] + math.cos(a) * r[2] * 0.92), rim_r, rim_mat, part)


def wavy(p0, p1, amp, waves, n=8, side=(1, 0, 0), phase=0.0):
    pts = []
    for i in range(n + 1):
        t = i / float(n)
        q = lerp(p0, p1, t)
        pts.append(add(q, mul(side, amp * math.sin(t * waves * 2 * math.pi + phase))))
    return pts


def jellume(g):
    m = g.Model('JELLUME')
    m.outline = (20, 36, 78)
    m.mat('bell', ['#2a64a4', '#4aa0d8', '#8cd6f2', '#d4f6ff'])
    m.mat('glow', ['#ffcc3a', '#fff4b0'], emissive=0.8)
    m.mat('frill', ['#a4488a', '#e488c0'])
    m.eye_dark = (18, 26, 58)
    m.white = (255, 255, 255)
    m.height = 32
    m.float_lift = 3
    float_ow(g, m, 3)
    bc, br = (0, 16.0, 0), (7.6, 6.4, 7.6)
    # trailing tentacles with little spark tips
    for k in range(6):
        a = (k / 6.0) * 2 * math.pi + 0.3
        top = (math.sin(a) * 4.8, 13.0, math.cos(a) * 4.8)
        bot = (math.sin(a) * 5.8, 1.6 + (k % 2) * 1.6, math.cos(a) * 5.8)
        pts = wavy(top, bot, 0.8, 1.2, n=6, side=(math.cos(a), 0, -math.sin(a)),
                   phase=k)
        m.tube(pts, None, 'bell', 'tent%d' % k, rfn=lambda t: 0.75 - 0.3 * t)
        m.sph(pts[-1], 0.75, 'glow', 'tent%d' % k)
    # frilly oral arms under the bell
    for k in range(4):
        a = (k / 4.0) * 2 * math.pi + 0.8
        top = (math.sin(a) * 1.6, 12.5, math.cos(a) * 1.6)
        bot = (math.sin(a) * 2.8, 5.0, math.cos(a) * 2.8)
        g.gill(m, top, bot, 1.3, 'frill', mat='frill', face=(math.sin(a), 0, math.cos(a)),
               fronds=3, flat=0.6)
    # the bell, its scalloped rim and the lamp glowing inside
    m.ell((0, 12.6, 0), (6.0, 1.6, 6.0), 'frill', 'under')
    jelly_bell(m, bc, br, 'bell', 'bell', 'bell', scallops=12, rim_r=1.3,
               rim_y=-2.6)
    # the lamp heart: a round glow high in the bell, with a soft halo ring
    p, n = g.on(bc, br, (0.12, 0.62, 0.78))
    m.paint(p, (3.6, 3.0, 2.6), 'bell', ['bell'])
    m.paint(p, (2.7, 2.2, 2.6), 'glow', ['bell'])
    for k in range(6):
        a = k / 6.0 * 2 * math.pi
        m.paint(g.on(bc, br, (math.sin(a), 0.2, math.cos(a)))[0], (0.6, 2.2, 0.6),
                'bell', ['bell'])
    g.eye_pair(m, bc, br, 26, -4, 3.0, 3.8, center=(0, 15, 9), turn=6)
    p, n = g.on(bc, br, (0.12, -0.32, 1))
    m.mouth(p, n, 'smile', w=2.8)
    for s in (-1, 1):
        m.dot(g.on(bc, br, (s * 0.62 + 0.1, -0.3, 0.75))[0], (s * 0.6, 0, 0.8),
              w=1.4, h=0.8, color=('frill', 1), minw=2)
    return m


# ==========================================================================
# 41 MEDUSHOCK -- tall jellyfish whose tendrils arc
# ==========================================================================
def medushock(g):
    m = g.Model('MEDUSHOCK')
    m.outline = (18, 30, 70)
    m.mat('bell', ['#24569a', '#3c8ccc', '#78c6ec', '#c6eeff'])
    m.mat('glow', ['#ffc830', '#fff4a8'], emissive=0.8)
    m.mat('frill', ['#8c3a8a', '#d06cc0', '#f4a8e0'])
    m.mat('arc', ['#fff27a', '#ffffff'], emissive=0.9)
    m.eye_dark = (16, 22, 52)
    m.white = (255, 255, 255)
    m.height = 60
    m.max_w = 56
    m.float_lift = 2
    float_ow(g, m, 3)
    bc, br = (0, 40.0, 0), (8.6, 11.0, 8.6)
    # long tendrils, arcs of lightning jumping between them
    tips = []
    tops = []
    for k in range(6):
        a = (k / 6.0) * 2 * math.pi + 0.25
        top = (math.sin(a) * 6.4, 31.0, math.cos(a) * 6.4)
        bot = (math.sin(a) * 9.0, 1.5 + (k % 3) * 2.5, math.cos(a) * 9.0)
        pts = wavy(top, bot, 1.2, 1.6, n=10, side=(math.cos(a), 0, -math.sin(a)),
                   phase=k * 1.3)
        m.tube(pts, None, 'bell', 'tent%d' % k, rfn=lambda t: 1.05 - 0.55 * t)
        m.sph(pts[-1], 0.9, 'glow', 'tent%d' % k)
        tips.append(pts)
        tops.append(top)
    for (i, j, t) in ((0, 1, 0.45), (1, 2, 0.7), (4, 5, 0.55), (5, 0, 0.3),
                      (3, 4, 0.8)):
        a = tips[i][int(t * 10)]
        b = tips[j][int(t * 10)]
        mid = lerp(a, b, 0.5)
        off = norm(cross(sub(b, a), (0, 0, 1)))
        pts = [a, add(lerp(a, b, 0.3), mul(off, 1.6)), add(mid, mul(off, -1.4)),
               add(lerp(a, b, 0.72), mul(off, 1.2)), b]
        g.zigzag(m, pts, [0.55, 0.5, 0.5, 0.5, 0.45], 'arc', 'arc', flat=1.0)
    # frilled oral curtains down the middle
    for k in range(4):
        a = (k / 4.0) * 2 * math.pi + 0.8
        top = (math.sin(a) * 2.2, 31.0, math.cos(a) * 2.2)
        bot = (math.sin(a) * 3.6, 14.0, math.cos(a) * 3.6)
        g.gill(m, top, bot, 1.7, 'frill', mat='frill', face=(math.sin(a), 0, math.cos(a)),
               fronds=5, flat=0.6)
    m.ell((0, 31.4, 0), (7.4, 1.8, 7.4), 'frill', 'under')
    # the tall lantern bell, a glowing band round its waist, ribbed
    jelly_bell(m, bc, br, 'bell', 'bell', 'bell', scallops=14, rim_r=1.5,
               rim_y=-8.2)
    for k in range(18):
        a = k / 18.0 * 2 * math.pi
        p, n = g.on(bc, br, (math.sin(a), 0.42, math.cos(a)))
        m.paint(p, 1.3, 'glow', ['bell'])
    for k in range(8):
        a = k / 8.0 * 2 * math.pi
        for y in (0.75, 0.05, -0.35):
            m.paint(g.on(bc, br, (math.sin(a), y, math.cos(a)))[0], (0.6, 1.8, 0.6),
                    'bell', ['bell'])
    m.paint(g.on(bc, br, (0, 1, 0))[0], (3.4, 2.0, 3.4), 'glow', ['bell'])
    g.eye_pair(m, bc, br, 24, -6, 3.6, 4.2, style='iris', iris=('glow', 0),
               slant=0.45, center=(0, 38, 10), turn=6)
    p, n = g.on(bc, br, (0.12, -0.38, 1))
    m.mouth(p, n, 'smile', w=3.4)
    return m


# ==========================================================================
# 42 LURELING -- anglerfish fry; its lure is a tiny kernel
# ==========================================================================
def fin(m, base, d, ln, wdt, mat, part, up, teeth=3, flat=0.2):
    tip = add(base, mul(norm(d), ln))
    mid = lerp(base, tip, 0.5)
    m.tube([base, mid, tip], None, mat, part, flat=flat, up=up,
           rfn=lambda t: wdt * (0.35 + 0.65 * math.sin(math.pi * min(1, t * 0.9 + 0.1)))
           * (0.8 + 0.2 * abs(math.sin(t * math.pi * teeth))) + 0.1)


def lureling(g):
    m = g.Model('LURELING')
    m.outline = (16, 18, 44)
    m.mat('body', ['#1e2450', '#2e3c78', '#4a62a8', '#7c98d4'])
    m.mat('belly', ['#8aa0c8', '#c8d8f0'])
    m.mat('glow', ['#1a9c90', '#3cdcc4', '#c4fff4'], emissive=0.5)
    m.eye_dark = (14, 16, 36)
    m.white = (255, 255, 255)
    m.height = 28
    m.front_yaw = -34
    m.float_lift = 3
    float_ow(g, m, 3)
    bc, br = (0, 10.0, 0.5), (6.8, 6.2, 6.6)
    # tail and tail fin
    m.tube([(0, 10.0, -4.0), (0, 10.6, -8.0), (0.4, 11.4, -10.5)], [4.0, 2.4, 1.2],
           'body', 'tail')
    fin(m, (0.4, 11.4, -10.0), (0, 0.5, -1), 5.0, 3.2, 'body', 'tail', up=(1, 0, 0),
        teeth=3)
    # the round head-body with a pale underside
    m.ell(bc, br, 'body', 'body')
    m.paint((0, 6.0, 2.0), (5.8, 3.4, 5.8), 'belly', ['body'])
    # pectoral fins, a small dorsal fin
    for s in (-1, 1):
        fin(m, (s * 5.8, 8.6, -0.5), (s * 1.0, -0.2, -0.5), 4.2, 2.2, 'body',
            'fin%d' % s, up=(0, 0.3, 1), teeth=2)
    fin(m, (0, 15.6, -2.0), (0, 0.7, -1), 3.6, 1.8, 'body', 'dorsal', up=(1, 0, 0),
        teeth=2)
    # the lure: a thin stalk arcing forward with its own glowing kernel
    stalk = [(0, 15.4, 2.6), (0, 19.6, 3.4), (0, 21.6, 6.4), (0, 20.8, 9.6)]
    m.tube(stalk, [0.55, 0.5, 0.45, 0.4], 'body', 'lure')
    kc = (0, 19.2, 10.4)
    m.crystal(add(kc, (0, -2.0, 0)), add(kc, (0, 2.2, 0)), 1.8, 'glow', 'lure',
              sides=6, tip_frac=0.45, twist=15)
    # freckles of light along its cheeks
    for s in (-1, 1):
        for k in range(3):
            m.paint(g.on(bc, br, (s * 0.8, -0.1 - k * 0.14, 0.55 - k * 0.2))[0], 0.6,
                    'glow', ['body'])
    # big curious eyes and a wide toothy grin
    g.eye_pair(m, bc, br, 28, 18, 3.8, 4.4, style='iris', iris=('glow', 1),
               center=(0, 10, 12), turn=6)
    p, n = g.on(bc, br, (0.05, -0.28, 1))
    m.mouth(p, n, 'open', w=6.0, h=2.0, inner=('body', 0), fang=1)
    return m


# ==========================================================================
# 43 ABYSSLURE -- deep anglerfish, lure like a lantern
# ==========================================================================
def abysslure(g):
    m = g.Model('ABYSSLURE')
    m.outline = (12, 12, 30)
    m.mat('body', ['#141838', '#222a5a', '#363f82', '#5662aa'])
    m.mat('belly', ['#5c6a9a', '#8c9cc8'])
    m.mat('glow', ['#1a9c90', '#3cdcc4', '#c4fff4'], emissive=0.5)
    m.mat('tooth', ['#b8c4d8', '#ffffff'])
    m.eye_dark = (10, 10, 28)
    m.white = (255, 255, 255)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -36
    m.float_lift = 2
    float_ow(g, m, 3)
    bc, br = (0, 24.0, -1.0), (12.0, 11.0, 12.5)
    # tail + ragged tail fin
    m.tube([(0, 23.0, -9.0), (0, 22.0, -16.0), (0.6, 22.6, -20.0)], [7.0, 4.0, 2.0],
           'body', 'tail')
    fin(m, (0.6, 22.6, -19.0), (0, 0.6, -1), 9.0, 5.6, 'body', 'tail',
        up=(1, 0, 0), teeth=4)
    fin(m, (0.6, 22.0, -19.0), (0, -0.5, -1), 7.0, 4.0, 'body', 'tail',
        up=(1, 0, 0), teeth=3)
    # the great round body
    m.ell(bc, br, 'body', 'body')
    # huge underslung jaw
    jc, jr = (0, 15.8, 6.0), (11.0, 5.4, 8.4)
    m.ell(jc, jr, 'body', 'jaw')
    m.paint((0, 12.0, 6.0), (9.4, 3.6, 7.6), 'belly', ['jaw'])
    # needle teeth along the jaw rim, pointing up
    for k in range(9):
        a = (-70 + 140.0 * k / 8) * DEG
        p = (math.sin(a) * jr[0] * 0.86, jc[1] + jr[1] * 0.55,
             jc[2] + math.cos(a) * jr[2] * 0.86)
        h = 3.2 + 1.2 * (k % 2)
        m.crystal(sub(p, (0, 0.8, 0)), add(p, (0, h, 0.5)), 0.7, 'tooth', 'teeth',
                  sides=4, tip_frac=0.8)
    # upper teeth hanging down from the lip
    for k in range(6):
        a = (-55 + 110.0 * k / 5) * DEG
        p = (math.sin(a) * 9.4, 21.6, 1.0 + math.cos(a) * 9.6)
        m.crystal(add(p, (0, 0.6, 0)), add(p, (0, -2.6, 0.4)), 0.6, 'tooth', 'teeth',
                  sides=4, tip_frac=0.8)
    # ragged pectoral fins, a spiny dorsal
    for s in (-1, 1):
        fin(m, (s * 10.5, 20.0, -2.0), (s * 1.0, -0.3, -0.6), 9.0, 4.2, 'body',
            'fin%d' % s, up=(0, 0.3, 1), teeth=4)
    for k in range(4):
        b = (0, 33.5 - k * 1.2, -4.0 - k * 2.6)
        m.tube([b, add(b, (0, 4.2 - k * 0.6, -1.8))], [0.7, 0.2], 'body', 'dorsal')
    # glowing photophores along the flanks
    for k in range(5):
        for s in (-1, 1):
            d = (s * 0.92, 0.02 - 0.03 * k, 0.35 - 0.24 * k)
            m.paint(g.on(bc, br, d)[0], 1.15 - 0.1 * k, 'glow', ['body'])
    # the lure: a long rod arcing up and forward to a caged lantern
    rod = [(0, 34.0, 3.0), (0, 41.0, 5.0), (0.5, 45.0, 10.0), (1.0, 44.0, 15.0),
           (1.2, 41.0, 17.0)]
    m.tube(rod, [1.1, 0.9, 0.75, 0.6, 0.5], 'body', 'lure')
    g.lantern(m, (1.2, 36.6, 17.2), 4.0, 'lure', axis=(0, 1, 0), ribs=4, rib_r=0.42,
              fur='body', ember='glow', ember_r=0.9, cap=False)
    # chin barbels
    for s in (-1, 0, 1):
        b = (s * 3.5, 11.0, 12.0)
        m.tube([b, add(b, (s * 0.8, -3.0, 0.6)), add(b, (s * 1.4, -5.2, 0.2))],
               [0.5, 0.4, 0.2], 'body', 'barbel')
        m.sph(add(b, (s * 1.4, -5.4, 0.2)), 0.55, 'glow', 'barbel')
    # small fierce glowing eyes above the jaw
    for s in (-1, 1):
        p, n = g.on(bc, br, (s * 0.46 + 0.14, 0.22, 0.86))
        m.eye(p, n, 3.2, 2.8, style='glow', iris=('glow', 1), slant=0.8,
              center=(0, 24, 14), glint=True, pupil='eye')
    return m


# ==========================================================================
# 44 RADISHOO -- radish sprite with a leafy tuft
# ==========================================================================
def leaf_tuft(g, m, base, specs, mat, part, teeth=3):
    """specs: [(direction, length, width), ...] jagged leaves from one base."""
    for d, ln, w in specs:
        d = norm(d)
        up = norm(cross(d, (0.9, 0, -0.4) if abs(d[0]) < 0.3 else (0, 0, 1)))
        if up[2] < 0:
            up = mul(up, -1)
        g.jagged_leaf(m, base, d, ln, w, mat, part, up=up, teeth=teeth)


def radishoo(g):
    m = g.Model('RADISHOO')
    m.outline = (60, 22, 40)
    m.mat('root', ['#b4a0ae', '#e2d4de', '#fdf6fa'])
    m.mat('red', ['#8e1838', '#d0385a', '#f27892'])
    m.mat('leaf', ['#2c6e2c', '#56a63c', '#a2d866'])
    m.eye_dark = (40, 16, 30)
    m.white = (255, 255, 255)
    m.height = 30
    m.front_yaw = -24
    bc, br = (0, 10.0, 0), (5.0, 7.4, 4.8)
    m.ell(bc, br, 'root', 'body')
    # rosy top fading down to a white root
    m.paint((0, 15.8, 0), (5.8, 5.0, 5.8), 'red', ['body'])
    for k in range(10):
        a = k / 10.0 * 2 * math.pi
        m.paint((math.sin(a) * 4.6, 12.2 + 0.7 * math.sin(a * 3), math.cos(a) * 4.4),
                (1.5, 1.4, 1.5), 'red', ['body'])
    # forked root legs and a curly root tail
    for s in (-1, 1):
        m.tube([(s * 2.0, 4.0, 0.6), (s * 3.0, 1.8, 1.4), (s * 3.4, 0.8, 2.6)],
               [1.5, 1.1, 0.9], 'root', 'leg%d' % s)
    m.tube([(0, 3.0, -1.6), (0.4, 1.2, -4.0), (1.8, 0.8, -6.0), (2.8, 1.8, -6.6)],
           [0.9, 0.6, 0.4, 0.15], 'root', 'tail')
    # little root arms
    for s in (-1, 1):
        m.tube([(s * 4.4, 9.4, 0.6), (s * 6.4, 7.8, 1.6), (s * 7.2, 6.2, 2.4)],
               [0.9, 0.7, 0.3], 'root', 'arm%d' % s)
    # leafy tuft
    top = (0, 17.2, -0.2)
    m.tube([(0, 16.0, -0.2), top], [1.3, 1.1], 'leaf', 'tuft')
    leaf_tuft(g, m, top, [((0, 1, -0.15), 10.5, 2.6), ((-0.75, 0.85, 0.1), 8.5, 2.3),
                          ((0.8, 0.8, 0.05), 9.0, 2.4), ((0.2, 0.7, -0.8), 7.0, 2.0)],
              'leaf', 'tuft')
    g.eye_pair(m, bc, br, 26, 2, 2.8, 3.6, center=(0, 9, 8))
    p, n = g.on(bc, br, (0.08, -0.22, 1))
    m.mouth(p, n, 'smile', w=2.4)
    for s in (-1, 1):
        m.dot(g.on(bc, br, (s * 0.6 + 0.08, -0.12, 0.8))[0], (s * 0.6, 0, 0.8),
              w=1.4, h=0.8, color=('red', 2), minw=2)
    return m


# ==========================================================================
# 45 MANDRAGOR -- mandrake whose scream is a lullaby
# ==========================================================================
def mandragor(g):
    m = g.Model('MANDRAGOR')
    m.outline = (50, 20, 40)
    m.mat('root', ['#9c8a8e', '#cebcc0', '#f2e6e6'])
    m.mat('red', ['#7c1634', '#bc3054', '#e86c86'])
    m.mat('leaf', ['#245a28', '#478c34', '#86c056'])
    m.mat('bloom', ['#5a2c8c', '#9c64d4'])
    m.mat('berry', ['#f0b830'])
    m.eye_dark = (36, 14, 28)
    m.white = (255, 255, 255)
    m.height = 56
    m.max_w = 60
    m.front_yaw = -20
    m.mat('crease', ['#9c8a8e'])
    # forked root legs splaying out, with trailing root hairs
    for s in (-1, 1):
        pts = [(s * 3.0, 15.0, 0.0), (s * 5.2, 9.0, 0.6), (s * 6.4, 4.2, 1.2),
               (s * 7.4, 1.4, 2.4)]
        m.tube(pts, [3.6, 2.8, 1.9, 1.1], 'root', 'leg%d' % s)
        for k, d in enumerate(((s * 1.0, -0.2, 0.9), (s * 0.4, -0.3, -1.0),
                               (s * 1.0, -0.1, -0.2))):
            b = pts[1 + (k % 2)]
            m.tube([b, add(b, mul(norm(d), 3.4))], [0.6, 0.15], 'root', 'leg%d' % s)
    # a plump, creased root torso, rosy at the top
    m.ell((0, 19.5, 0), (7.0, 7.2, 5.6), 'root', 'body')
    m.ell((0, 29.0, 0.2), (7.6, 7.0, 6.2), 'root', 'body')
    for y, rx in ((17.0, 7.0), (21.5, 7.0), (25.5, 7.4)):
        m.paint((0, y, 0.2), (rx + 0.3, 0.32, 6.4), 'crease', ['body'])
    for s in (-1, 1):
        for y in (18.0, 23.0):
            b = (s * 6.8, y, 1.0)
            m.tube([b, add(b, (s * 2.4, -1.4, 0.6))], [0.5, 0.12], 'root', 'body')
    m.paint((0, 33.0, 0.2), (8.4, 4.4, 7.0), 'red', ['body'])
    for k in range(12):
        a = k / 12.0 * 2 * math.pi
        m.paint((math.sin(a) * 6.8, 30.2 + 0.8 * math.sin(a * 3), math.cos(a) * 5.6 + 0.2),
                (1.6, 1.6, 1.6), 'red', ['body'])
    # gnarled root arms raised, conducting its song
    for s in (-1, 1):
        sh = (s * 6.4, 31.0, 0.0)
        el = (s * 11.4, 34.0, 1.6)
        hd = (s * 13.0, 40.0, 3.4)
        m.tube([sh, el, hd], [1.9, 1.5, 1.2], 'root', 'arm%d' % s)
        for k, d in enumerate(((s * 0.2, 1, 0.3), (s * 0.8, 0.8, 0.2), (s * 0.9, 0.3, 0.4))):
            m.tube([hd, add(hd, mul(norm(d), 2.6))], [0.8, 0.25], 'root', 'arm%d' % s)
    # a crown of leaves with purple bell flowers and golden berries
    top = (0, 36.4, -0.6)
    leaf_tuft(g, m, top, [((0, 1, -0.25), 15.0, 3.6), ((-0.7, 0.9, -0.1), 13.0, 3.2),
                          ((0.75, 0.85, -0.15), 13.5, 3.3), ((-0.35, 0.8, -0.75), 11.0, 3.0),
                          ((0.4, 0.75, -0.75), 11.0, 3.0), ((-1.0, 0.45, 0.2), 10.0, 2.6),
                          ((1.0, 0.4, 0.15), 10.0, 2.6)], 'leaf', 'crown', teeth=4)
    for k, (b, d) in enumerate((((-2.5, 40.0, 1.8), (-0.3, 1, 0.5)),
                                ((2.6, 40.4, 1.2), (0.4, 1, 0.4)),
                                ((0.2, 41.0, -2.4), (0.0, 1, -0.3)))):
        tip = add(b, mul(norm(d), 4.4))
        m.tube([b, tip], [0.4, 0.35], 'leaf', 'bloom%d' % k)
        m.ell(add(tip, (0, -0.4, 0)), (1.8, 1.6, 1.8), 'bloom', 'bloom%d' % k)
        m.ell(add(tip, (0, -1.4, 0)), (1.3, 0.8, 1.3), 'bloom', 'bloom%d' % k)
    for q in ((-5.4, 37.2, 3.0), (5.2, 37.6, 2.6), (-4.2, 38.6, 4.0)):
        m.sph(q, 1.2, 'berry', 'berries')
    # the singing face: serene closed eyes, round open mouth
    hc, hr = (0, 29.0, 0.2), (7.6, 7.0, 6.2)
    g.eye_pair(m, hc, hr, 30, 16, 3.4, 3.4, style='closed', center=(0, 30, 8))
    p, n = g.on(hc, hr, (0.08, -0.25, 1))
    m.mouth(p, n, 'open', w=3.2, h=3.4, inner=('red', 0))
    for s in (-1, 1):
        m.dot(g.on(hc, hr, (s * 0.62 + 0.08, -0.05, 0.8))[0], (s * 0.6, 0, 0.8),
              w=1.6, h=0.9, color=('red', 2), minw=2)
    # musical motes drifting up from the song
    for q in ((-9.0, 45.0, 4.0), (8.6, 47.0, 3.0)):
        m.sph(q, 0.9, 'bloom', 'note')
        m.tube([add(q, (0.8, 0, 0)), add(q, (0.8, 3.0, 0))], [0.3, 0.3], 'bloom', 'note')
    return m


# ==========================================================================
# 46 PUMPKLING -- pumpkin sprout with a carved grin
# ==========================================================================
def pumpkin(m, c, rx, ry, ribs, mat, part, tilt=0.0):
    """Ribbed pumpkin: overlapping upright ellipsoid lobes round an axis."""
    for k in range(ribs):
        a = 2 * math.pi * k / ribs
        off = (math.sin(a) * rx * 0.42, 0, math.cos(a) * rx * 0.42)
        m.ell(add(c, off), (rx * 0.62, ry, rx * 0.62), mat, part,
              rot=(a / DEG, 0, tilt))
    m.ell(c, (rx * 0.8, ry * 1.02, rx * 0.8), mat, part)


def carved_face(m, c, r, eyes_at, mouth_w, slant=1.0, eye_w=3.2, eye_h=3.2,
                mouth_h=2.4, center=None):
    import math as _m
    for s in (-1, 1):
        a = (eyes_at[0] * s) * DEG
        e = eyes_at[1] * DEG
        d = (_m.sin(a) * _m.cos(e), _m.sin(e), _m.cos(a) * _m.cos(e))
        p = add(c, (d[0] * r[0], d[1] * r[1], d[2] * r[2]))
        m.eye(p, d, eye_w, eye_h, style='glow', iris=('glow', 1), slant=slant,
              glint=False, center=center, pupil=None)


def pumpkling(g):
    m = g.Model('PUMPKLING')
    m.outline = (64, 24, 12)
    m.mat('pump', ['#8c3810', '#d46218', '#f49232', '#ffc66a'])
    m.mat('leaf', ['#2c6624', '#529a36', '#98cc5a'])
    m.mat('glow', ['#ffb424', '#fff08a'], emissive=0.85)
    m.eye_dark = (60, 20, 8)
    m.white = (255, 250, 220)
    m.height = 28
    m.front_yaw = -24
    pc, rx, ry = (0, 8.4, 0), 8.6, 6.6
    pumpkin(m, pc, rx, ry, 8, 'pump', 'body')
    m.group('body')
    # stubby vine feet and leaf hands
    for s in (-1, 1):
        m.ell((s * 3.8, 1.2, 2.6), (2.0, 1.2, 2.4), 'leaf', 'foot%d' % s)
        g.leaf(m, (s * 7.8, 7.6, 2.0), (s * 10.0, 6.4, 3.4), (s * 11.6, 5.0, 4.2), 1.8,
               'leaf', 'arm%d' % s, up=(0, 1, 0.3), flat=0.3)
    # curly stem, a leaf and a corkscrew tendril
    st = [(0, 14.2, 0), (0.4, 16.4, -0.4), (1.6, 17.6, -0.6)]
    m.tube(st, [1.4, 1.2, 0.9], 'leaf', 'stem')
    g.leaf(m, (0.6, 16.0, -0.4), (-2.4, 18.4, 0.6), (-5.4, 18.6, 1.2), 2.4, 'leaf',
           'stem', up=(0.2, 1, 0.3), flat=0.3)
    pts = []
    for i in range(14):
        a = i / 13.0 * 2.4 * 2 * math.pi
        pts.append((1.6 + i * 0.32 + math.cos(a) * 0.9, 17.6 + math.sin(a) * 0.9,
                    -0.6 + i * 0.1))
    m.tube(pts, 0.32, 'leaf', 'stem')
    # the carved grin, lit from inside
    fr = (rx * 0.94, ry * 1.0, rx * 0.94)
    carved_face(m, pc, fr, (26, 16), 6.0, slant=0.0, eye_w=2.6, eye_h=3.6,
                center=(0, 8, 12))
    p = add(pc, (0.6, -1.8, rx * 0.92))
    m.mouth(p, (0.05, -0.2, 1), 'open', w=6.4, h=2.4, color='outline',
            inner=('glow', 1))
    for dx in (-1.2, 1.6):
        m.dot(add(p, (dx, 0.9, 0.2)), (0, 0, 1), w=1.0, h=1.0, color=('pump', 2))
    return m


# ==========================================================================
# 47 JACKOGRIM -- vine-bodied jack-o'-lantern with a lantern head
# ==========================================================================
def jackogrim(g):
    m = g.Model('JACKOGRIM')
    m.outline = (30, 16, 12)
    m.mat('pump', ['#6e2a0e', '#b44e14', '#e0782a'])
    m.mat('vine', ['#1e2a1c', '#34482c', '#566c3e'])
    m.mat('leaf', ['#44602c', '#7c9c44'])
    m.mat('glow', ['#f07818', '#ffc83a', '#fff4b4'], emissive=0.7)
    m.eye_dark = (40, 16, 8)
    m.white = (255, 244, 200)
    m.height = 60
    m.max_w = 60
    m.front_yaw = -20

    def braid(p0, p1, r, part, strands=3, turns=1.2, amp=1.0, n=10, phase=0.0):
        d = norm(sub(p1, p0))
        u = norm(cross(d, (0, 0, 1) if abs(d[2]) < 0.9 else (1, 0, 0)))
        v = cross(d, u)
        for k in range(strands):
            pts = []
            for i in range(n + 1):
                t = i / float(n)
                a = t * turns * 2 * math.pi + k * 2 * math.pi / strands + phase
                q = lerp(p0, p1, t)
                pts.append(add(q, add(mul(u, math.cos(a) * amp), mul(v, math.sin(a) * amp))))
            m.tube(pts, r, 'vine', part)
    # legs: braided vines ending in root feet
    for s in (-1, 1):
        braid((s * 3.2, 18.0, 0), (s * 4.6, 2.6, 1.0), 1.25, 'leg%d' % s, amp=0.9,
              phase=s)
        for d in ((s * 0.5, -0.2, 1), (s * 1, -0.3, 0.2), (0, -0.2, -1)):
            b = (s * 4.6, 1.8, 1.0)
            m.tube([b, add(b, mul(norm(d), 3.0))], [1.0, 0.3], 'vine', 'leg%d' % s)
    # braided vine torso
    braid((0, 17.0, 0), (0, 35.0, 0.6), 1.7, 'body', strands=4, turns=0.8, amp=2.4)
    m.ell((0, 20.0, 0), (3.2, 3.0, 2.8), 'vine', 'body')
    # long vine arms reaching down, curling tendril fingers
    for s in (-1, 1):
        pts = [(s * 3.0, 34.0, 0.4), (s * 8.0, 33.0, 1.0), (s * 12.0, 26.0, 2.6),
               (s * 13.4, 18.5, 4.0)]
        m.tube(pts, [1.8, 1.5, 1.3, 1.1], 'vine', 'arm%d' % s)
        hd = pts[-1]
        for k in range(3):
            q = []
            for i in range(7):
                a = i / 6.0 * 1.3 * math.pi
                q.append(add(hd, ((k - 1) * 0.9 + s * math.sin(a) * 1.4,
                                  -math.sin(a * 0.9) * 2.4 - i * 0.2,
                                  1.0 - math.cos(a) * 1.2)))
            m.tube(q, 0.45, 'vine', 'arm%d' % s)
        for t in (0.3, 0.62):
            b = lerp(pts[1], pts[2], t * 1.6) if t < 0.5 else lerp(pts[2], pts[3], t)
            g.leaf(m, b, add(b, (s * 1.8, 1.6, -0.6)), add(b, (s * 3.8, 1.8, -1.0)), 1.5,
                   'leaf', 'arm%d' % s, up=(0, 1, 0.3), flat=0.3)
    # a ragged collar of dry leaves at the neck
    for k in range(9):
        a = (k / 9.0) * 2 * math.pi
        d = (math.sin(a), -0.55, math.cos(a))
        b = (math.sin(a) * 2.6, 36.0, math.cos(a) * 2.4)
        g.leaf(m, b, add(b, mul(d, 2.6)), add(b, mul(d, 5.2)), 1.8, 'leaf', 'collar',
               up=(0, 1, 0), flat=0.3)
    # the lantern head: a big ribbed pumpkin, lit from inside
    hc, rx, ry = (0, 43.0, 0.6), 9.6, 7.4
    pumpkin(m, hc, rx, ry, 9, 'pump', 'head')
    st = [(0, 49.6, 0.4), (0.8, 52.0, -0.4), (2.2, 53.2, -1.6)]
    m.tube(st, [1.6, 1.3, 0.9], 'vine', 'head')
    # a wisp of flame escaping the stem hole
    g.flame(m, (-1.6, 49.8, -1.2), 7.0, 2.4, 'flame', mats=('glow', 'glow', 'glow'),
            up=(-0.2, 1, -0.1), tongues=2, seed=47, inner=False, core=False)
    fr = (rx * 0.94, ry, rx * 0.94)
    carved_face(m, hc, fr, (24, 16), 7.0, slant=1.2, eye_w=4.0, eye_h=3.4,
                center=(0, 43, 14))
    p = add(hc, (0.8, -2.2, rx * 0.9))
    m.mouth(p, (0.05, -0.2, 1), 'open', w=8.0, h=2.8, color='outline',
            inner=('glow', 1))
    for dx, dy in ((-2.0, 1.1), (0.6, 1.1), (-0.7, -1.1), (2.2, -1.1)):
        m.dot(add(p, (dx, dy, 0.3)), (0, 0, 1), w=1.0, h=1.0, color=('pump', 1))
    return m


# ==========================================================================
# 48 SHROOMLET -- mushroom-cap tot that puffs spores
# ==========================================================================
def mushroom_cap(m, c, r, part, cap, spot, gill, spots=(), gill_lines=0):
    m.ell(c, r, cap, part)
    for d, sr in spots:
        m.paint(add(c, (d[0] * r[0], d[1] * r[1], d[2] * r[2])), sr, spot, [part])
    gc = add(c, (0, -r[1] * 0.35, 0))
    m.ell(gc, (r[0] * 0.9, r[1] * 0.28, r[2] * 0.9), gill, part + 'g')
    for k in range(gill_lines):
        a = k / float(gill_lines) * 2 * math.pi
        m.paint(add(gc, (math.sin(a) * r[0] * 0.55, -r[1] * 0.2, math.cos(a) * r[2] * 0.55)),
                (0.35, 0.5, 0.35), cap, [part + 'g'])


def shroomlet(g):
    m = g.Model('SHROOMLET')
    m.outline = (44, 18, 50)
    m.mat('cap', ['#4a1a5e', '#7c3492', '#b060c6', '#d89ae2'])
    m.mat('stem', ['#b4a486', '#e2d6ba', '#fff8e4'])
    m.mat('gill', ['#8a6a98', '#c4a6d0'])
    m.eye_dark = (40, 18, 40)
    m.white = (255, 255, 255)
    m.height = 28
    m.front_yaw = -24
    # stubby stem body, little feet and nub arms
    sc, sr = (0, 5.8, 0), (4.4, 5.2, 4.2)
    m.ell(sc, sr, 'stem', 'body')
    for s in (-1, 1):
        m.ell((s * 2.6, 1.1, 1.8), (1.7, 1.1, 2.0), 'stem', 'foot%d' % s)
        m.ell((s * 4.6, 5.6, 0.8), (1.3, 1.9, 1.3), 'stem', 'arm%d' % s,
              rot=(0, 0, s * 30))
    # the big spotted cap, gills underneath
    cc, cr = (0, 12.2, -0.4), (8.8, 5.4, 8.6)
    mushroom_cap(m, cc, cr, 'cap', 'cap', 'stem', 'gill',
                 spots=[((0.1, 0.9, 0.35), 1.6), ((0.7, 0.55, 0.4), 1.3),
                        ((-0.55, 0.65, 0.45), 1.3), ((0.5, 0.75, -0.4), 1.2),
                        ((-0.2, 0.7, -0.7), 1.2), ((0.9, 0.2, -0.2), 1.0),
                        ((-0.85, 0.3, -0.1), 1.0)], gill_lines=12)
    # a sneeze of spores drifting up
    for k, (q, r) in enumerate((((-7.8, 17.8, 3.0), 1.1), ((-9.6, 20.6, 2.0), 0.8),
                                ((-7.0, 22.2, 1.4), 0.6))):
        m.sph(q, r, 'gill', 'spore%d' % k)
    g.eye_pair(m, sc, sr, 30, 8, 2.8, 3.4, center=(0, 5, 8))
    p, n = g.on(sc, sr, (0.1, -0.3, 1))
    m.mouth(p, n, 'open', w=1.8, h=1.8, inner=('cap', 0))
    for s in (-1, 1):
        m.dot(g.on(sc, sr, (s * 0.6 + 0.1, -0.1, 0.8))[0], (s * 0.6, 0, 0.8),
              w=1.3, h=0.8, color=('cap', 3), minw=2)
    return m


# ==========================================================================
# 49 MYCOLOSSUS -- walking giant fungus
# ==========================================================================
def mycolossus(g):
    m = g.Model('MYCOLOSSUS')
    m.outline = (34, 14, 40)
    m.mat('cap', ['#3e1450', '#6e2e86', '#a85ec0'])
    m.mat('stem', ['#8c7c68', '#bcae94', '#e6dcc4'])
    m.mat('gill', ['#6c4c7c', '#a484b2'])
    m.mat('shelf', ['#9c5a24', '#dc9a44'])
    m.mat('glow', ['#b4f04a', '#f0ffb0'], emissive=0.8)
    m.eye_dark = (24, 10, 30)
    m.white = (255, 255, 240)
    m.height = 60
    m.max_w = 62
    m.front_yaw = -22
    # root-legs: thick mycelium strands splaying at the base
    for s in (-1, 1):
        m.tube([(s * 4.0, 14.0, 0.0), (s * 6.4, 7.0, 1.0), (s * 7.6, 2.0, 2.4)],
               [4.0, 3.2, 2.6], 'stem', 'leg%d' % s)
        m.ell((s * 8.0, 1.4, 3.4), (3.4, 1.6, 4.2), 'stem', 'leg%d' % s)
        for d in ((s * 1, -0.1, 0.6), (s * 0.6, -0.1, -1.0)):
            b = (s * 8.0, 1.2, 3.0)
            m.tube([b, add(b, mul(norm(d), 4.2))], [1.1, 0.3], 'stem', 'leg%d' % s)
    # the great stem torso, bracket fungi growing up its side
    m.tube([(0, 12.0, 0), (0, 24.0, 0.4), (0, 36.0, 0.0)], [7.4, 7.0, 5.8], 'stem', 'body')
    for k, (c, r, a) in enumerate((((6.2, 20.0, 2.8), 3.6, 20), ((6.6, 25.0, 0.2), 2.8, 0),
                                   ((-6.4, 22.4, 1.8), 3.0, -10))):
        m.ell(c, (r, r * 0.35, r * 0.8), 'shelf', 'shelf%d' % k, rot=(a, 0, 0))
    # arms: thick stalks ending in clusters of little mushrooms
    for s in (-1, 1):
        sh = (s * 6.0, 32.0, 0.6)
        el = (s * 12.5, 27.0, 2.4)
        hd = (s * 14.4, 19.0, 4.2)
        m.tube([sh, el, hd], [3.0, 2.6, 2.4], 'stem', 'arm%d' % s)
        for k, d in enumerate(((s * 0.3, -0.2, 1), (s * 1.0, 0.3, 0.3), (s * 0.3, -0.6, 0.5))):
            q = add(hd, mul(norm(d), 2.6))
            m.tube([hd, q], [1.0, 0.8], 'stem', 'arm%d' % s)
            m.ell(add(q, mul(norm(d), 0.8)), (1.9, 1.2, 1.9), 'cap', 'arm%d' % s,
                  rot=(0, 0, 0))
    # the vast cap with pale spots, and the gills underneath
    cc, cr = (0, 42.0, -0.6), (18.0, 7.6, 16.0)
    mushroom_cap(m, cc, cr, 'cap', 'cap', 'stem', 'gill',
                 spots=[((0.1, 0.9, 0.3), 2.8), ((0.6, 0.6, 0.45), 2.2),
                        ((-0.5, 0.7, 0.4), 2.2), ((0.5, 0.75, -0.4), 2.0),
                        ((-0.3, 0.75, -0.6), 2.0), ((0.9, 0.3, 0.0), 1.8),
                        ((-0.9, 0.35, -0.1), 1.8), ((0.2, 0.55, 0.8), 1.8)],
                 gill_lines=18)
    # little mushrooms sprouting on the cap
    for k, (b, h, r) in enumerate((((5.0, 47.5, 3.0), 2.4, 1.8), ((-6.0, 47.0, -2.0), 2.0, 1.5),
                                   ((1.0, 49.0, -4.0), 1.8, 1.3))):
        m.tube([b, add(b, (0, h, 0))], [0.7, 0.6], 'stem', 'sprout%d' % k)
        m.ell(add(b, (0, h, 0)), (r, r * 0.7, r), 'cap', 'sprout%d' % k)
    # a face in the shade of the cap: glowing eyes, a grim mouth
    fc, fr = (0, 30.0, 0.2), (6.4, 6.4, 6.4)
    for s in (-1, 1):
        p, n = g.on(fc, fr, (s * 0.38 + 0.08, 0.28, 0.9))
        m.paint(p, (2.2, 1.6, 1.6), 'gill', ['body'])
        m.eye(p, n, 3.2, 2.4, style='glow', iris=('glow', 1), slant=0.6,
              center=(0, 30, 10), glint=False)
    p, n = g.on(fc, fr, (0.1, -0.12, 1))
    m.mouth(p, n, 'line', w=3.4)
    # spores drifting off
    for q in ((13.0, 38.0, 6.0), (15.6, 41.0, 4.0), (-14.0, 36.0, 5.0)):
        m.sph(q, 0.8, 'glow', 'spores')
    return m


# ==========================================================================
# 50 BLINKET -- firefly with a blinking tail
# ==========================================================================
def firefly_wing(m, root, s, ln, wd, ang, mat, part, tilt=0.5, lift=0.3):
    uvec = norm((s * 1.0, lift, -tilt))
    vvec = norm(cross((0, 0, 1), uvec)) if s > 0 else norm(cross(uvec, (0, 0, 1)))
    pts = []
    for i in range(14):
        a = 2 * math.pi * i / 14
        x = ln * 0.5 + math.cos(a) * ln * 0.5
        y = math.sin(a) * wd * (0.7 + 0.3 * math.cos(a))
        ca, sa = math.cos(ang * DEG), math.sin(ang * DEG)
        xx, yy = x * ca - y * sa, x * sa + y * ca
        pts.append(add(root, add(mul(uvec, xx), (0, yy, -abs(xx) * 0.3))))
    m.poly(pts, mat, part, puff=0.35)


def blinket(g):
    m = g.Model('BLINKET')
    m.outline = (22, 22, 20)
    m.mat('shell', ['#1c1e1c', '#363a30', '#5a5e48'])
    m.mat('pron', ['#b8461a', '#ee8436'])
    m.mat('glow', ['#94c418', '#dcf850', '#fcffd0'], emissive=0.6)
    m.mat('wing', ['#9aacbc', '#dceaf4'])
    m.eye_dark = (20, 20, 18)
    m.white = (255, 255, 255)
    m.height = 27
    m.front_yaw = -30
    m.float_lift = 4
    float_ow(g, m, 4)
    # glassy wings fanned out behind the wing cases
    for s in (-1, 1):
        firefly_wing(m, (s * 1.6, 11.0, -1.5), s, 9.0, 3.4, 18, 'wing', 'wing%d' % s)
    # the lamp: a fat glowing tail curled down and back
    m.ell((0, 6.4, -4.6), (3.6, 3.8, 4.2), 'glow', 'tail', rot=(0, 30, 0))
    m.paint((0, 8.6, -3.0), (4.2, 1.0, 4.0), 'shell', ['tail'], rot=(0, 30, 0))
    # body under the wing cases
    m.ell((0, 9.2, -0.6), (3.6, 3.0, 4.6), 'shell', 'body')
    # wing cases, parted a little
    for s in (-1, 1):
        m.ell((s * 2.2, 11.0, -1.6), (2.4, 1.6, 5.0), 'shell', 'case%d' % s,
              rot=(s * 12, -8, s * 20))
    # orange hood-shield over the head with a dark spot
    m.ell((0, 12.0, 3.6), (4.2, 2.0, 3.2), 'pron', 'pron', rot=(0, 20, 0))
    m.paint((0, 13.8, 3.4), (1.0, 0.8, 1.0), 'shell', ['pron'])
    # round head with big bright eyes, long antennae
    hc, hr = (0, 9.4, 6.0), (3.9, 3.5, 3.2)
    m.ell(hc, hr, 'shell', 'head')
    for s in (-1, 1):
        pts = [(s * 1.2, 12.4, 6.8), (s * 2.6, 15.6, 8.0), (s * 4.4, 18.0, 7.6),
               (s * 5.4, 18.8, 6.4)]
        m.tube(pts, [0.45, 0.4, 0.35, 0.3], 'shell', 'ant%d' % s)
        m.sph(pts[-1], 0.7, 'glow', 'ant%d' % s)
        for k in range(3):
            b = (s * 1.6, 7.2, 2.4 - k * 2.2)
            m.tube([b, add(b, (s * 1.6, -2.4, 0.4)), add(b, (s * 2.0, -4.6, 0.8))],
                   [0.35, 0.3, 0.25], 'shell', 'leg%d' % s)
    g.eye_pair(m, hc, hr, 36, 10, 3.4, 4.0, style='iris', iris=('glow', 1),
               center=(0, 9, 10), turn=8)
    p, n = g.on(hc, hr, (0.2, -0.45, 1))
    m.mouth(p, n, 'smile', w=1.8, color=('pron', 1))
    return m


# ==========================================================================
# 51 BEACONFLY -- big firefly with a lantern abdomen
# ==========================================================================
def beaconfly(g):
    m = g.Model('BEACONFLY')
    m.outline = (20, 20, 18)
    m.mat('shell', ['#1a1c1a', '#34382e', '#565a44'])
    m.mat('pron', ['#a83c16', '#e87830'])
    m.mat('glow', ['#94c418', '#dcf850', '#fcffd0'], emissive=0.6)
    m.mat('wing', ['#8ea0b2', '#c8dcec', '#f0f8ff'])
    m.eye_dark = (18, 18, 16)
    m.white = (255, 255, 255)
    m.height = 60
    m.max_w = 62
    m.front_yaw = -24
    m.float_lift = 2
    float_ow(g, m, 4, side_yaw=-62)
    # two pairs of long glassy wings spread wide
    for s in (-1, 1):
        firefly_wing(m, (s * 2.4, 34.0, -2.4), s, 19.0, 6.0, 28, 'wing', 'wingF%d' % s,
                     tilt=0.35)
        firefly_wing(m, (s * 2.2, 31.0, -3.0), s, 15.0, 4.6, -8, 'wing', 'wingH%d' % s,
                     tilt=0.45)
        # the wing cases lifted open
        m.ell((s * 5.4, 34.5, -3.4), (2.6, 1.6, 7.0), 'shell', 'case%d' % s,
              rot=(s * 40, -24, s * 48))
    # the lantern abdomen: ribbed like a paper lantern, capped top and bottom
    lc, lr = (0, 17.0, -2.6), (7.6, 9.6, 7.4)
    m.ell(lc, lr, 'glow', 'lamp')
    # paper-lantern bands
    for y in (-0.5, -0.12, 0.26):
        yy = lc[1] + y * lr[1]
        rr = math.sqrt(max(0.0, 1 - y * y))
        m.paint((0, yy, lc[2]), (lr[0] * rr + 0.4, 0.42, lr[2] * rr + 0.4), 'shell',
                ['lamp'])
    m.ell((0, 27.0, -2.4), (4.6, 1.8, 4.4), 'shell', 'lampcap')
    m.ell((0, 7.2, -2.6), (3.0, 1.6, 3.0), 'shell', 'lampcap')
    m.tube([(0, 6.0, -2.6), (0, 3.4, -2.2)], [1.2, 0.4], 'shell', 'lampcap')
    # thorax and the orange shield
    m.ell((0, 31.0, 0.4), (5.0, 4.4, 5.0), 'shell', 'body')
    m.ell((0, 36.0, 3.6), (5.6, 2.4, 4.2), 'pron', 'pron', rot=(0, 25, 0))
    m.paint((0, 38.0, 3.4), (1.6, 1.0, 1.6), 'shell', ['pron'])
    # legs tucked under, holding the lantern's top
    for s in (-1, 1):
        for k in range(3):
            b = (s * 3.2, 29.0, 2.6 - k * 2.4)
            m.tube([b, add(b, (s * 3.4, -3.0, 0.8)), add(b, (s * 3.0, -6.4, 1.4))],
                   [0.8, 0.7, 0.5], 'shell', 'leg%d' % s)
    # head, big eyes, long feathered antennae with glowing tips
    hc, hr = (0, 32.4, 7.0), (5.0, 4.4, 4.0)
    m.ell(hc, hr, 'shell', 'head')
    for s in (-1, 1):
        pts = [(s * 1.6, 35.4, 8.0), (s * 4.0, 41.0, 9.4), (s * 7.4, 45.0, 8.6),
               (s * 9.6, 46.4, 7.0)]
        m.tube(pts, [0.7, 0.6, 0.5, 0.4], 'shell', 'ant%d' % s)
        for t in range(1, 3):
            q = pts[t]
            m.tube([q, add(q, (s * 1.4, 1.6, 0.4))], [0.4, 0.2], 'shell', 'ant%d' % s)
        m.sph(pts[-1], 0.9, 'glow', 'ant%d' % s)
    g.eye_pair(m, hc, hr, 36, 10, 3.8, 4.4, style='iris', iris=('glow', 1),
               slant=0.35, center=(0, 32, 12), turn=8)
    p, n = g.on(hc, hr, (0.2, -0.45, 1))
    m.mouth(p, n, 'smile', w=2.2, color=('pron', 1))
    return m


# ==========================================================================
# 52 STATICKO -- leopard gecko with crackling static toe pads
# ==========================================================================
def gecko_foot(g, m, ft, s, fwd, part, ln=2.0, mat='skin', pad='spark'):
    """Four splayed toes ending in round (glowing) pads."""
    for k in range(4):
        a = (-25 + 32 * k) * DEG
        d = norm((s * math.sin(a), -0.08, math.cos(a) * fwd))
        tip = add(ft, mul(d, ln))
        m.tube([ft, tip], [0.55, 0.4], mat, part)
        m.sph(add(tip, mul(d, 0.3)), 0.72, pad, part)


def staticko(g):
    m = g.Model('STATICKO')
    m.outline = (58, 34, 14)
    m.mat('skin', ['#94601a', '#d49a2c', '#f4c858', '#fff0a4'])
    m.mat('spot', ['#3c2616', '#5e3c20'])
    m.mat('belly', ['#e0cc9c', '#fff6dc'])
    m.mat('spark', ['#2c96e0', '#8ae4ff', '#f0ffff'], emissive=0.65)
    m.eye_dark = (40, 24, 12)
    m.white = (255, 252, 236)
    m.height = 24
    m.front_yaw = -34
    # fat leopard-gecko tail curling round to its left
    tail = [(0, 4.2, -4.6), (0.6, 3.6, -8.6), (3.6, 3.4, -11.6),
            (7.6, 3.8, -11.4), (9.6, 5.4, -8.4)]
    m.tube(tail, [3.0, 3.3, 2.8, 1.8, 0.6], 'skin', 'tail')
    # long low body, cream belly
    bc, br = (0, 4.6, 0.0), (4.2, 3.2, 6.4)
    m.ell(bc, br, 'skin', 'body')
    m.paint((0, 2.2, 0.5), (3.4, 1.3, 5.4), 'belly', ['body'])
    # splayed legs, elbows up, sticky glowing pads
    for s in (-1, 1):
        for zz, nm, fwd in ((3.6, 'F', 1), (-3.6, 'B', 0.6)):
            sh = (s * 3.0, 4.4, zz)
            el = (s * 6.0, 4.8, zz + 0.6 * fwd)
            ft = (s * 7.0, 1.0, zz + 1.6 * fwd)
            m.tube([sh, el, ft], [1.6, 1.3, 1.0], 'skin', 'leg%s%d' % (nm, s))
            gecko_foot(g, m, ft, s, 1 if nm == 'F' else -0.3, 'leg%s%d' % (nm, s))
    # big round head and blunt snout
    m.tube([(0, 5.2, 4.6), (0, 6.8, 7.0)], [2.8, 2.9], 'skin', 'body')
    hc, hr = (0, 8.4, 8.6), (4.8, 3.9, 4.4)
    m.ell(hc, hr, 'skin', 'head')
    sc, sr = (0, 7.4, 11.4), (3.6, 2.6, 2.4)
    m.ell(sc, sr, 'skin', 'head')
    m.paint((0, 5.6, 10.8), (3.2, 1.0, 2.6), 'belly', ['head'])
    # leopard spots over back, head and tail
    rnd = g.Rand(52)
    for d in fib_dirs(40, 52, 0.5, g):
        if d[1] < 0.15 or rnd.f() < 0.35:
            continue
        m.paint(g.on(bc, br, d)[0], 0.75 + rnd.f() * 0.25, 'spot', ['body'])
    for d in ((0.5, 0.8, -0.3), (-0.5, 0.8, -0.3), (0.0, 1.0, -0.6),
              (0.8, 0.5, 0.2), (-0.8, 0.5, 0.2)):
        m.paint(g.on(hc, hr, norm(d))[0], 0.9, 'spot', ['head'])
    # dark bands round the tail
    for t in (0.2, 0.42, 0.62):
        i = min(3, int(t * 4))
        q = lerp(tail[i], tail[i + 1], t * 4 - i)
        dn = norm(sub(tail[i + 1], tail[i]))
        m.paint(q, (3.6, 3.6, 0.6), 'spot', ['tail'],
                rot=(math.atan2(dn[0], dn[2]) / DEG, 0, 0))
    # a crackle of static off the front pads
    for s in (-1, 1):
        b = (s * 8.6, 1.4, 7.6)
        g.zigzag(m, [b, add(b, (s * 1.2, 1.4, 0.4)), add(b, (s * 0.4, 2.4, 0.6)),
                     add(b, (s * 1.6, 3.8, 0.8))], [0.4, 0.35, 0.35, 0.12],
                 'spark', 'zap%d' % s, flat=0.6)
    # huge gecko eyes and a wide grin
    # (swung toward the camera and up onto the head so both eyes show)
    g.eye_pair(m, hc, hr, 36, 20, 4.0, 4.6, iris=('skin', 0), center=(0, 8, 14),
               turn=12)
    # overworld: a 3/4 turn so the long body and banded tail show
    g.OW_TURN[m.name] = -30.0
    p, n = g.on(sc, sr, (0.1, -0.35, 1))
    m.mouth(p, n, 'smile', w=4.2)
    return m


# ==========================================================================
# 53 FULGECKO -- upright running lizard with a crackling bolt frill
# ==========================================================================
def fulgecko(g):
    m = g.Model('FULGECKO')
    m.outline = (52, 28, 12)
    m.mat('skin', ['#a06a18', '#dca434', '#fcd86a'])
    m.mat('spot', ['#3a2410'])
    m.mat('belly', ['#fff2d0'])
    m.mat('frill', ['#2e4e98', '#5a8ad8'])
    m.mat('spark', ['#ffd840', '#fffac8'], emissive=0.55)
    m.mat('pad', ['#4ac0f4', '#e0ffff'], emissive=0.65)
    m.mat('mouth', ['#c04a44'])
    m.eye_dark = (36, 20, 10)
    m.white = (255, 252, 236)
    m.height = 58
    m.max_w = 62
    m.front_yaw = -30
    # long whip tail streaming out behind for balance
    tail = [(0, 16.0, -5.0), (0.6, 13.0, -11.0), (2.0, 10.0, -17.0),
            (4.4, 8.4, -22.0), (7.0, 8.6, -25.0)]
    m.tube(tail, [3.4, 2.8, 2.0, 1.2, 0.3], 'skin', 'tail')
    for k in range(5):
        t = 0.1 + k * 0.17
        i = min(3, int(t * 4))
        q = lerp(tail[i], tail[i + 1], t * 4 - i)
        m.paint(add(q, (0, 2.0 - t, 0)), (2.6, 0.9, 1.0), 'spot', ['tail'])
    # running legs: long thighs, digitigrade shins, splayed glowing toes
    for s, (kz, fz) in ((1, (5.0, 4.0)), (-1, (0.0, -4.0))):
        hip = (s * 3.6, 17.0, -1.0)
        kn = (s * 5.2, 11.0, kz)
        an = (s * 5.0, 4.2, fz - 2.4)
        ft = (s * 5.2, 1.0, fz)
        m.ell(hip, (3.2, 4.4, 4.0), 'skin', 'leg%d' % s)
        m.tube([hip, kn, an, ft], [2.8, 2.0, 1.4, 1.1], 'skin', 'leg%d' % s)
        gecko_foot(g, m, ft, s, 1, 'leg%d' % s, ln=2.6, pad='pad')
    # lean torso pitched forward, pale throat and belly
    tc = (0, 23.0, 2.2)
    m.ell(tc, (5.2, 8.4, 5.0), 'skin', 'body', rot=(0, 38, 0))
    m.paint((0, 21.6, 6.4), (3.4, 6.4, 2.0), 'belly', ['body'], rot=(0, 38, 0))
    for d in ((0.6, 0.3, -0.7), (-0.6, 0.1, -0.7), (0.8, -0.3, -0.3),
              (-0.8, -0.2, -0.4), (0.2, 0.7, -0.6)):
        m.paint(g.on(tc, (5.2, 8.4, 5.0), norm(d), rot=(0, 38, 0))[0], 1.3,
                'spot', ['body'])
    # short arms flung back as it sprints
    for s in (-1, 1):
        sh = (s * 4.4, 27.0, 5.0)
        el = (s * 7.0, 23.0, 3.0 + s * 2.0)
        hd = (s * 7.4, 20.0, 6.0 + s * 2.0)
        m.tube([sh, el, hd], [1.6, 1.3, 1.1], 'skin', 'arm%d' % s)
        for k in range(3):
            d = norm((s * (0.3 * k - 0.2), -0.6, 1.0))
            m.tube([hd, add(hd, mul(d, 1.8))], [0.5, 0.35], 'skin', 'arm%d' % s)
            m.sph(add(hd, mul(d, 2.0)), 0.6, 'pad', 'arm%d' % s)
    # the neck frill: a wide blue fan behind the head, ribbed with bolt spines
    fc = (0, 32.0, 4.0)
    rimpts = []
    for k in range(17):
        a = (-125 + 250.0 * k / 16) * DEG
        rr = 12.5 + 1.8 * (k % 2)
        rimpts.append(add(fc, (math.sin(a) * rr, math.cos(a) * rr * 0.85,
                               -3.0 - 0.8 * (k % 2))))
    m.poly([add(fc, (0, -6.0, -1.0))] + rimpts, 'frill', 'frill', puff=0.3)
    for k in range(1, 16, 2):
        a = (-125 + 250.0 * k / 16) * DEG
        d = (math.sin(a), math.cos(a) * 0.85, -0.16)
        b = add(fc, mul(d, 4.0))
        mid = add(fc, mul(d, 9.0))
        tip = add(fc, mul(d, 17.0))
        side = (math.cos(a) * 1.4, -math.sin(a) * 1.4, 0)
        g.zigzag(m, [b, add(mid, side), add(mid, mul(side, -0.7)), tip],
                 [0.9, 0.8, 0.75, 0.15], 'spark', 'frill', flat=0.8,
                 up=(0, 0, 1))
        # the same spine seen from behind
        bk = (0, 0, -2.2)
        g.zigzag(m, [add(b, (0, 0, -3.0)), add(add(mid, side), bk),
                     add(add(mid, mul(side, -0.7)), bk), add(tip, (0, 0, -1.4))],
                 [0.8, 0.7, 0.65, 0.15], 'spark', 'frill', flat=0.8,
                 up=(0, 0, 1))
    # head thrust forward, jaws open in a hiss
    hc, hr = (0, 34.0, 9.4), (5.0, 4.2, 5.0)
    m.ell(hc, hr, 'skin', 'head')
    m.ell((0, 34.4, 13.6), (3.6, 2.2, 3.2), 'skin', 'head')
    m.ell((0, 30.8, 12.6), (3.2, 1.3, 3.0), 'skin', 'jaw', rot=(0, -18, 0))
    m.ell((0, 32.2, 12.8), (2.8, 1.2, 2.6), 'mouth', 'jaw')
    for d in ((0.5, 0.8, -0.3), (-0.5, 0.8, -0.3), (0.0, 1.0, -0.5)):
        m.paint(g.on(hc, hr, norm(d))[0], 1.0, 'spot', ['head'])
    g.eye_pair(m, hc, hr, 42, 24, 3.6, 3.8, style='iris', iris=('spark', 1),
               slant=0.6, center=(0, 34, 16))
    return m


# ==========================================================================
# 54 FLURRABBIT -- chubby snowshoe hare with frosted ear tips
# ==========================================================================
def flurrabbit(g):
    m = g.Model('FLURRABBIT')
    m.outline = (40, 50, 78)
    m.mat('fur', ['#8494b4', '#c4d0e4', '#eaf1fb', '#ffffff'])
    m.mat('ice', ['#2e7cc4', '#6cc0f0', '#c4ecff'])
    m.mat('pink', ['#c0707e', '#f4a8b4'])
    m.eye_dark = (26, 30, 54)
    m.white = (255, 255, 255)
    m.height = 36
    m.front_yaw = -28
    # snowball tail
    g.seedball(m, (0, 7.0, -7.6), 2.6, 'fur', 'tail', n=26, fil=0.36,
               tip=0.5, seed=54)
    # big snowshoe hind feet, fuzzy haunches
    for s in (-1, 1):
        m.ell((s * 4.2, 5.0, -2.2), (3.2, 3.8, 4.2), 'fur', 'hip%d' % s)
        m.ell((s * 4.4, 1.3, 1.4), (2.2, 1.3, 4.6), 'fur', 'foot%d' % s)
        m.paint((s * 4.4, 0.6, 1.6), (1.8, 0.8, 3.6), 'ice', ['foot%d' % s])
        m.ell((s * 2.2, 2.2, 4.4), (1.3, 1.6, 1.5), 'fur', 'legF%d' % s)
    # chubby round body
    m.ell((0, 7.4, -0.6), (6.0, 6.4, 6.4), 'fur', 'body')
    # round head with a little muzzle
    hc, hr = (0, 13.6, 3.2), (5.0, 4.6, 4.6)
    m.ell(hc, hr, 'fur', 'head')
    mc, mr = (0, 12.2, 7.0), (2.4, 1.8, 1.5)
    m.ell(mc, mr, 'fur', 'head')
    # tall ears laid back, frosted blue at the tips
    for s in (-1, 1):
        pts = [(s * 2.0, 16.8, 2.0), (s * 3.2, 21.0, 0.6), (s * 4.0, 24.2, -1.4),
               (s * 4.2, 25.8, -2.8)]
        m.tube(pts, [1.8, 2.1, 1.7, 0.5], 'fur', 'ear%d' % s, flat=0.45,
               up=(s * 0.6, 0.1, 1), mats=[(0, 'fur'), (0.62, 'ice')])
        m.paint((s * 3.2, 20.6, 1.4), (0.9, 2.6, 0.9), 'pink', ['ear%d' % s],
                rot=(s * 10, -20, 0))
    # frosty cheek tufts
    for s in (-1, 1):
        m.tube([(s * 4.0, 12.0, 4.0), (s * 6.4, 11.2, 3.8), (s * 7.6, 10.4, 3.0)],
               [1.6, 1.0, 0.2], 'fur', 'head', flat=0.5, up=(0, 0, 1))
    g.eye_pair(m, hc, hr, 34, 12, 3.2, 3.8, iris=('ice', 0), center=(0, 13, 10))
    m.dot(g.on(mc, mr, (0, 0.5, 1))[0], (0, 0.2, 1), w=1.6, h=1.0, minw=2,
          color=('pink', 0))
    p, n = g.on(mc, mr, (0, -0.35, 1))
    m.mouth(p, n, 'w', w=2.6)
    return m


# ==========================================================================
# 55 MOONHARE -- moon rabbit with a mochi mallet
# ==========================================================================
def moonhare(g):
    m = g.Model('MOONHARE')
    m.outline = (40, 32, 70)
    m.mat('fur', ['#7a6ca0', '#b0a6d6', '#e2def6', '#ffffff'])
    m.mat('night', ['#24245e', '#3c3e8e'])
    m.mat('gold', ['#a86a10', '#e8a828', '#ffe070'])
    m.mat('wood', ['#5e3a1e', '#96643a', '#c89a62'])
    m.mat('pink', ['#e890a8'])
    m.eye_dark = (30, 24, 56)
    m.white = (255, 255, 255)
    m.height = 58
    m.max_w = 60
    m.front_yaw = -26
    # long hind feet
    for s in (-1, 1):
        m.ell((s * 4.2, 6.4, -1.8), (3.4, 5.4, 4.8), 'fur', 'leg%d' % s)
        m.ell((s * 4.6, 1.5, 2.6), (2.3, 1.5, 5.2), 'fur', 'leg%d' % s)
    g.seedball(m, (0, 10.0, -6.8), 2.6, 'fur', 'tail', n=24, fil=0.32,
               tip=0.5, seed=55)
    # upright body with a pale belly
    m.ell((0, 16.0, 0.0), (6.0, 8.6, 5.2), 'fur', 'body')
    # the mochi mallet over its shoulder: long handle, fat barrel head
    h0, h1 = (3.0, 13.0, 7.4), (11.4, 38.0, 1.0)
    m.tube([h0, h1], [1.0, 1.0], 'wood', 'mallet')
    ax = norm((1.0, -0.34, 0.1))
    mh = add(h1, mul(norm(sub(h1, h0)), 2.0))
    m.ell_axes(mh, (mul(ax, 5.2), mul(norm(sub(h1, h0)), 3.4),
                    (0, 0, 3.4)), 'wood', 'mallet')
    for t in (-4.0, 4.0):
        m.paint(add(mh, mul(ax, t)), (1.0, 3.8, 3.8), 'night', ['mallet'],
                rot=(0, 0, -19))
    # both paws gripping the handle
    for s, hp in ((1, (5.6, 20.4, 6.0)), (-1, (4.0, 16.0, 7.0))):
        sh = (s * 5.2, 21.6, 1.0)
        el = (s * 5.4 + 1.4, 16.4, 3.0)
        m.tube([sh, el, hp], [1.8, 1.5, 1.4], 'fur', 'arm%d' % s)
        m.sph(hp, 1.8, 'fur', 'arm%d' % s)
    # head
    hc, hr = (0, 29.0, 1.8), (5.8, 5.4, 5.2)
    m.ell(hc, hr, 'fur', 'head')
    mc, mr = (0, 27.4, 5.8), (2.6, 2.0, 1.6)
    m.ell(mc, mr, 'fur', 'head')
    # golden crescent on the brow (a disc with a bite taken out)
    # (a night-blue rim under the gold so it reads on the white fur)
    # (a raised gold crescent set on the forehead, horns up, so it gets
    # its own outline and reads even at 1x)
    cp, cn = g.on(hc, hr, norm((0.06, 0.72, 0.69)))
    cp = add(cp, mul(cn, 0.3))
    cup = [add(cp, (math.cos(a * DEG) * 3.0, 1.4 + math.sin(a * DEG) * 1.9, 0.0))
           for a in (200, 230, 270, 310, 340)]
    m.tube(cup, [0.6, 1.1, 1.35, 1.1, 0.6], 'gold', 'crest', flat=0.7,
           up=cn)
    # tall night-sky ears speckled with stars
    for s in (-1, 1):
        pts = [(s * 2.2, 32.4, 0.6), (s * 3.2, 38.0, -0.4), (s * 4.0, 44.0, -1.6),
               (s * 4.2, 48.0, -2.8)]
        m.tube(pts, [1.9, 2.4, 2.0, 0.6], 'fur', 'ear%d' % s, flat=0.45,
               up=(s * 0.5, 0, 1))
        m.paint((s * 3.4, 39.6, 0.4), (1.3, 5.6, 1.2), 'night', ['ear%d' % s],
                rot=(s * 8, 0, 0))
        for k, (dy, dx) in enumerate(((-3.6, 0.2), (-0.8, -0.4), (1.8, 0.3),
                                      (4.0, -0.2))):
            m.paint((s * 3.4 + dx, 39.6 + dy, 0.8), 0.95, 'gold',
                    ['ear%d' % s])
    g.eye_pair(m, hc, hr, 34, 10, 3.8, 4.6, iris=("night", 1), slant=0.0,
               center=(0, 28, 10))
    m.dot(g.on(mc, mr, (0, 0.5, 1))[0], (0, 0.2, 1), w=1.6, h=1.0, minw=2,
          color=('pink', 0))
    p, n = g.on(mc, mr, (0, -0.35, 1))
    m.mouth(p, n, 'w', w=2.8)
    return m


# ==========================================================================
# 56 TUXFLAKE -- downy penguin chick wrapped in a puff of snow
# ==========================================================================
def tuxflake(g):
    m = g.Model('TUXFLAKE')
    m.outline = (34, 40, 60)
    m.mat('snow', ['#94a8c8', '#cddcf0', '#f2f7ff', '#ffffff'])
    m.mat('down', ['#5e6472', '#8c929e', '#bcc0ca'])
    m.mat('cap', ['#1c2030', '#343a4c'])
    m.mat('feet', ['#c85e18', '#ff9c3a'])
    m.eye_dark = (22, 24, 36)
    m.white = (255, 255, 255)
    m.height = 28
    m.front_yaw = -26
    # orange feet poking out under the puff
    for s in (-1, 1):
        m.ell((s * 2.8, 1.0, 3.6), (1.8, 1.0, 2.6), 'feet', 'foot%d' % s)
    # the grey downy chick inside
    m.ell((0, 8.6, 0.6), (6.0, 7.0, 5.6), 'down', 'body')
    # the snow puff clinging round it, open at the front
    g.seedball(m, (0, 8.4, -1.0), (7.6, 7.2, 7.0), 'snow', 'puff', n=80,
               fil=0.24, tip=0.62, seed=56, skip_below=-0.8,
               skip_dir=((0, 0.2, 1), 0.55))
    # stubby grey flippers held out of the snow
    for s in (-1, 1):
        m.tube([(s * 6.0, 9.4, 2.0), (s * 8.4, 7.4, 3.0), (s * 9.4, 5.6, 3.6)],
               [1.6, 1.2, 0.6], 'down', 'arm%d' % s, flat=0.45,
               up=(s * 1, 0.2, 0.1))
    # head: black cap, white face mask, tiny beak
    hc, hr = (0, 15.0, 2.4), (5.0, 4.6, 4.6)
    m.ell(hc, hr, 'down', 'head')
    m.paint(add(hc, (0, 3.6, -1.2)), (5.6, 2.8, 5.6), 'cap', ['head'])
    for s in (-1, 1):
        m.paint(g.on(hc, hr, norm((s * 0.5, 0.05, 0.85)))[0], (2.4, 2.6, 2.0),
                'snow', ['head'])
    m.paint(g.on(hc, hr, (0, -0.4, 1))[0], (2.4, 1.6, 1.8), 'snow', ['head'])
    bp = g.on(hc, hr, (0, 0.0, 1))[0]
    m.tube([bp, add(bp, (0, -0.4, 1.8))], [0.9, 0.3], 'cap', 'head')
    # snowflakes caught in the puff
    for d in ((0.6, 0.7, 0.3), (-0.7, 0.5, 0.2), (0.3, 0.95, -0.2)):
        m.sparkle(g.on((0, 8.4, -1.0), (9.0, 8.6, 8.4), norm(d))[0], (0, 0, 1),
                  size=1, color=('snow', 0))
    g.eye_pair(m, hc, hr, 30, 8, 3.0, 3.6, iris=('cap', 1), center=(0, 14, 9))
    for s in (-1, 1):
        m.dot(g.on(hc, hr, (s * 0.6, -0.35, 0.72))[0], (s * 0.6, 0, 0.8),
              w=1.3, h=0.8, color=('feet', 1), minw=2)
    return m


# ==========================================================================
# 57 EMPERICE -- emperor penguin crowned with rime crystals
# ==========================================================================
def emperice(g):
    m = g.Model('EMPERICE')
    m.outline = (18, 20, 34)
    m.mat('coat', ['#161a28', '#2a3044', '#465070'])
    m.mat('belly', ['#b8c4d6', '#e4ecf6', '#ffffff'])
    m.mat('gold', ['#d88a14', '#ffc840', '#fff0a0'])
    m.mat('ice', ['#3a8ad0', '#86d0f8', '#e0f8ff'], spec=0.4)
    m.eye_dark = (14, 16, 26)
    m.white = (255, 255, 255)
    m.height = 60
    m.max_w = 60
    m.front_yaw = -24
    # black feet
    for s in (-1, 1):
        m.ell((s * 3.6, 1.2, 4.0), (2.6, 1.2, 3.6), 'coat', 'foot%d' % s)
    # tall body, white front, stubby tail
    bc, br = (0, 19.0, 0.0), (8.6, 17.0, 7.6)
    m.ell(bc, br, 'coat', 'body')
    m.paint((0, 17.0, 4.6), (7.0, 15.6, 4.4), 'belly', ['body'])
    m.tube([(0, 5.0, -6.0), (0, 2.4, -9.0)], [2.4, 1.0], 'coat', 'tail')
    # flippers held out a little, like a cape
    for s in (-1, 1):
        m.tube([(s * 7.4, 30.0, 0.0), (s * 10.4, 22.0, 0.8), (s * 11.6, 13.0, 1.4)],
               [2.6, 2.4, 0.8], 'coat', 'arm%d' % s, flat=0.4,
               up=(s * 1, 0, 0.25))
    # neck and head
    m.ell((0, 34.0, 0.8), (6.2, 5.0, 5.8), 'coat', 'body')
    hc, hr = (0, 40.0, 1.6), (5.6, 5.4, 5.6)
    m.ell(hc, hr, 'coat', 'head')
    # the gold ear patches flowing down into a pale bib
    for s in (-1, 1):
        m.paint(g.on(hc, hr, norm((s * 0.95, -0.35, -0.1)))[0], (2.0, 3.4, 2.4),
                'gold', ['head'], rot=(0, 0, s * 18))
        m.paint((s * 4.6, 34.2, 3.4), (2.2, 2.4, 2.2), 'gold', ['body'])
    m.paint((0, 32.0, 5.8), (4.8, 3.0, 2.0), 'gold', ['body'])
    # long curved beak with a gold stripe
    b0 = g.on(hc, hr, (0, -0.1, 1))[0]
    m.tube([b0, add(b0, (0, -0.8, 3.2)), add(b0, (0, -2.2, 5.8))],
           [1.5, 1.0, 0.3], 'coat', 'beak')
    for s in (-1, 1):
        m.paint(add(b0, (s * 0.9, -0.5, 1.6)), (0.6, 0.6, 1.8), 'gold', ['beak'])
    # crown of rime: ice crystals fanned round the top of the head
    for k in range(5):
        a = (-64 + 32.0 * k) * DEG
        d = norm((math.sin(a) * 1.1, 1.0, 0.15))
        bb = g.on(hc, hr, norm((math.sin(a) * 0.75, 0.8, 0.05)))[0]
        ln = (10.0 if k == 2 else 7.6 if k in (1, 3) else 5.6)
        m.crystal(sub(bb, mul(d, 1.2)), add(bb, mul(d, ln)), 1.5, 'ice',
                  'crown', sides=4, tip_frac=0.5)
    m.ell(add(hc, (0, 4.2, 0)), (4.2, 1.4, 4.0), 'ice', 'crown')
    # frost rime along the flipper edges
    for s in (-1, 1):
        for k, t in enumerate((0.35, 0.65)):
            q = lerp((s * 10.4, 22.0, 0.8), (s * 11.6, 13.0, 1.4), t)
            m.crystal(q, add(q, (s * 2.6, -1.4, 0.2)), 0.7, 'ice', 'arm%d' % s,
                      sides=4)
    # bright ice-blue eyes (flat colour, so they still read on the black
    # head when the overworld shrinks them to 2 px)
    g.eye_pair(m, hc, hr, 30, 10, 4.2, 4.6, style='glow', iris=('ice', 2),
               pupil=('coat', 0), slant=0.35, center=(0, 40, 8), turn=4,
               minw=2, minh=2)
    return m


# ==========================================================================
# 58 YAKLING -- shaggy yak calf with a frosty fringe
# ==========================================================================
def shag(m, c, r, part, n, mat, mats, y_min, ln, seed, g, rad=1.3, keep=None):
    """Hanging locks of hair round the lower rim of an ellipsoid."""
    rnd = g.Rand(seed)
    for d in fib_dirs(n, seed, 0.4, g):
        if d[1] > 0.35 or d[1] < y_min:
            continue
        if keep is not None and not keep(d):
            continue
        p, nn = g.on(c, r, d)
        b = sub(p, mul(nn, 0.8))
        l = ln * (0.8 + 0.4 * rnd.f())
        out = add(p, mul(nn, 0.8))
        m.tube([b, out, add(out, (nn[0] * 0.4, -l, nn[2] * 0.4))],
               [rad, rad * 0.9, rad * 0.35], mat, part, mats=mats)


def yakling(g):
    m = g.Model('YAKLING')
    m.outline = (22, 28, 44)
    m.mat('fur', ['#2c3852', '#475878', '#6e82a4'])
    m.mat('frost', ['#bcdcf0', '#ffffff'])
    m.mat('muzzle', ['#7c8ca4', '#b4c0d2'])
    m.mat('horn', ['#c8baa0', '#fff2d6'])
    m.mat('hoof', ['#161c2a'])
    m.mat('pink', ['#e89aa8'])
    m.eye_dark = (16, 20, 34)
    m.white = (255, 255, 255)
    m.height = 30
    m.front_yaw = -30
    # short sturdy legs
    for s in (-1, 1):
        for zz, nm in ((4.0, 'F'), (-4.6, 'B')):
            m.tube([(s * 3.6, 6.0, zz), (s * 3.7, 2.2, zz + 0.2)], [1.7, 1.5],
                   'fur', 'leg%s%d' % (nm, s))
            m.ell((s * 3.7, 1.0, zz + 0.4), (1.6, 1.0, 1.8), 'hoof',
                  'leg%s%d' % (nm, s))
    # round woolly body with a shaggy skirt tipped in frost
    bc, br = (0, 9.4, -0.6), (6.2, 5.4, 7.6)
    m.ell(bc, br, 'fur', 'body')
    shag(m, bc, br, 'body', 70, 'fur', [(0, 'fur'), (0.72, 'frost')], -0.5,
         3.2, 58, g, rad=1.3, keep=lambda d: d[2] < 0.75)
    # tufted tail
    m.tube([(0, 11.0, -8.0), (0, 9.0, -9.6), (0, 6.6, -9.8)], [0.8, 0.9, 1.2],
           'fur', 'tail', mats=[(0, 'fur'), (0.7, 'frost')])
    # big head with a pale muzzle
    hc, hr = (0, 12.4, 6.6), (4.8, 4.4, 4.2)
    m.ell(hc, hr, 'fur', 'head')
    mc, mr = (0, 10.2, 9.8), (3.2, 2.5, 2.0)
    m.ell(mc, mr, 'muzzle', 'head')
    for s in (-1, 1):
        m.dot(g.on(mc, mr, (s * 0.4, 0.1, 1))[0], (0, 0, 1), w=0.9, h=1.1,
              color=('hoof', 0), minw=1, minh=1)
        # floppy ears and little horn nubs
        m.tube([(s * 4.2, 13.6, 5.8), (s * 6.6, 13.0, 5.4), (s * 7.6, 12.0, 5.0)],
               [1.4, 1.2, 0.4], 'fur', 'ear%d' % s, flat=0.45, up=(0, 1, 0.2))
        m.tube([(s * 2.6, 15.6, 5.6), (s * 3.6, 17.2, 5.6), (s * 3.8, 18.2, 6.2)],
               [1.1, 0.9, 0.5], 'horn', 'horn%d' % s)
    # the frosty fringe hanging down over its eyes
    for k in range(9):
        x = -3.6 + k * 0.9
        b = (x, 16.0, 7.0 - abs(x) * 0.3)
        ln = 4.2 + 0.8 * math.cos(k * 1.7)
        m.tube([b, add(b, (x * 0.12, -ln * 0.5, 2.2)),
                add(b, (x * 0.18, -ln, 2.2))], [1.2, 1.0, 0.4], 'fur',
               'fringe', mats=[(0, 'fur'), (0.6, 'frost')])
    g.eye_pair(m, hc, hr, 32, 2, 2.6, 2.6, iris=('fur', 0), center=(0, 12, 12),
               lid=1)
    p, n = g.on(mc, mr, (0, -0.45, 1))
    m.mouth(p, n, 'smile', w=2.2)
    m.dot(add(p, (0, -0.8, 0.2)), n, w=1.2, h=0.8, color=('pink', 0))
    return m


# ==========================================================================
# 59 GLACIYAK -- massive glacier yak with ice-crystal horns
# ==========================================================================
def glaciyak(g):
    m = g.Model('GLACIYAK')
    m.outline = (16, 22, 38)
    m.mat('fur', ['#222c44', '#3a4a6a', '#5e7294'])
    m.mat('frost', ['#a8cce4', '#e6f6ff'])
    m.mat('ice', ['#3480c8', '#80ccf6', '#e4faff'], spec=0.4)
    m.mat('muzzle', ['#6c7c96', '#a4b2c8'])
    m.mat('hoof', ['#10141e'])
    m.eye_dark = (12, 16, 28)
    m.white = (255, 255, 255)
    m.height = 58
    m.max_w = 62
    m.front_yaw = -30
    # pillar legs, mostly hidden in the coat
    for s in (-1, 1):
        for zz, nm in ((9.0, 'F'), (-10.0, 'B')):
            m.tube([(s * 6.4, 12.0, zz), (s * 6.6, 3.0, zz + 0.4)], [3.4, 3.0],
                   'fur', 'leg%s%d' % (nm, s))
            m.ell((s * 6.6, 1.6, zz + 0.8), (3.0, 1.6, 3.2), 'hoof',
                  'leg%s%d' % (nm, s))
    # huge body with a shoulder hump
    bc, br = (0, 20.0, -1.0), (10.4, 9.4, 15.0)
    m.ell(bc, br, 'fur', 'body')
    hmc, hmr = (0, 27.0, 6.0), (9.4, 8.0, 8.4)
    m.ell(hmc, hmr, 'fur', 'body')
    # the long shaggy skirt, frosted at the ends, with icicles in it
    shag(m, bc, br, 'skirt', 120, 'fur', [(0, 'fur'), (0.75, 'frost')], -0.45,
         8.4, 59, g, rad=2.0, keep=lambda d: d[2] < 0.8)
    shag(m, hmc, hmr, 'skirt', 50, 'fur', [(0, 'fur'), (0.75, 'frost')], -0.2,
         7.0, 60, g, rad=1.9, keep=lambda d: d[2] > 0.2)
    rnd = g.Rand(591)
    for k in range(9):
        a = (-80 + 160.0 * k / 8) * DEG
        s = 1 if k % 2 else -1
        q = (math.sin(a) * 10.6 * s, 12.0 + rnd.f() * 2.0, math.cos(a) * 11.0 - 2)
        m.crystal(q, add(q, (0, -4.0 - rnd.f() * 2.0, 0)), 0.9, 'ice',
                  'icicle', sides=4, tip_frac=0.8)
    # frost rime settled along the spine
    m.paint((0, 34.0, 5.0), (7.0, 2.2, 7.0), 'frost', ['body'])
    m.paint((0, 29.4, -6.0), (6.0, 1.6, 9.0), 'frost', ['body'])
    # tail
    m.tube([(0, 23.0, -15.6), (0, 17.0, -17.4), (0, 11.0, -17.0)],
           [1.4, 1.6, 2.2], 'fur', 'tail', mats=[(0, 'fur'), (0.7, 'frost')])
    # low heavy head
    hc, hr = (0, 21.0, 15.0), (6.4, 6.0, 5.6)
    m.ell(hc, hr, 'fur', 'head')
    mc, mr = (0, 17.4, 19.2), (4.2, 3.4, 2.8)
    m.ell(mc, mr, 'muzzle', 'head')
    for s in (-1, 1):
        m.dot(g.on(mc, mr, (s * 0.4, 0.1, 1))[0], (0, 0, 1), w=1.0, h=1.2,
              color=('hoof', 0), minw=1, minh=1)
    # beard with icicles
    for k in range(5):
        x = -3.0 + k * 1.5
        b = (x, 15.0, 17.6)
        m.tube([b, add(b, (0, -3.0, 0.2)), add(b, (0, -6.0 + abs(x) * 0.5, -0.2))],
               [1.5, 1.2, 0.4], 'fur', 'beard', mats=[(0, 'fur'), (0.65, 'frost')])
    for x in (-1.5, 1.5):
        m.crystal((x, 12.0, 17.4), (x, 7.4, 17.4), 0.7, 'ice', 'beard', sides=4,
                  tip_frac=0.8)
    # fringe
    for k in range(9):
        x = -4.4 + k * 1.1
        b = (x, 26.0, 15.4 - abs(x) * 0.3)
        ln = 5.4 + 1.0 * math.cos(k * 1.7)
        m.tube([b, add(b, (x * 0.1, -ln * 0.5, 2.6)), add(b, (x * 0.15, -ln, 2.8))],
               [1.4, 1.2, 0.5], 'fur', 'fringe', mats=[(0, 'fur'), (0.6, 'frost')])
    # great curved ice horns sweeping out, forward and up, spiked with crystals
    for s in (-1, 1):
        pts = [(s * 4.4, 25.0, 13.6), (s * 10.0, 26.0, 13.0), (s * 14.4, 29.0, 14.0),
               (s * 15.6, 34.0, 16.0), (s * 14.0, 37.6, 18.0)]
        m.tube(pts, [2.2, 2.0, 1.7, 1.2, 0.3], 'ice', 'horn%d' % s)
        for t, d in ((1, (s * 0.2, 1, -0.4)), (2, (s * 1, 0.4, -0.4)), (3, (s * 1, 0.2, 0.2))):
            m.crystal(pts[t], add(pts[t], mul(norm(d), 3.6)), 0.8, 'ice',
                      'horn%d' % s, sides=4)
    g.eye_pair(m, hc, hr, 36, 4, 2.8, 2.6, style='iris', iris=('ice', 1),
               slant=0.5, center=(0, 21, 20))
    p, n = g.on(mc, mr, (0, -0.5, 1))
    m.mouth(p, n, 'line', w=3.0)
    return m


# ==========================================================================
# 60 RAMBLET -- cinnamon lamb charging head-first
# ==========================================================================
def curls(g, m, c, r, part, n, mat, rad, seed, keep=None, rot=None):
    """Tight wool curls: little balls studded over an ellipsoid."""
    rnd = g.Rand(seed)
    for d in fib_dirs(n, seed, 0.5, g):
        if keep is not None and not keep(d):
            continue
        p, nn = g.on(c, r, d, rot)
        m.sph(add(p, mul(nn, -rad * 0.3)), rad * (0.8 + 0.4 * rnd.f()), mat, part)


def ramblet(g):
    m = g.Model('RAMBLET')
    m.outline = (54, 26, 14)
    m.mat('wool', ['#7a3a18', '#b2622e', '#dc9454', '#f6c488'])
    m.mat('face', ['#5a3828', '#8e6446', '#bc9270'])
    m.mat('cream', ['#f2dcb8'])
    m.mat('horn', ['#f0e0bc'])
    m.mat('dust', ['#c8bc9c'])
    m.mat('tuft', ['#e2a868', '#ffe0ae'])
    m.eye_dark = (30, 18, 14)
    m.white = (255, 250, 240)
    m.height = 29
    m.front_yaw = -36
    # legs: front pair braced forward, hind pair kicking off
    for s in (-1, 1):
        m.tube([(s * 3.2, 7.0, 4.6), (s * 3.4, 3.6, 7.4), (s * 3.5, 1.2, 8.6)],
               [1.4, 1.1, 1.0], 'face', 'legF%d' % s)
        m.ell((s * 3.5, 0.9, 9.0), (1.2, 0.9, 1.4), 'face', 'legF%d' % s)
        m.tube([(s * 3.4, 8.0, -4.6), (s * 3.6, 4.2, -7.4), (s * 3.6, 1.2, -9.6)],
               [1.5, 1.1, 1.0], 'face', 'legB%d' % s)
        m.ell((s * 3.6, 0.9, -10.0), (1.2, 0.9, 1.4), 'face', 'legB%d' % s)
    # kicked-up dust behind the hind hooves
    for k, (q, r) in enumerate((((2.0, 1.8, -12.8), 1.6), ((-1.6, 2.2, -13.4), 1.4),
                                ((0.4, 3.6, -14.6), 1.1))):
        m.sph(q, r, 'dust', 'dust')
    # the cinnamon fleece: a curly body pitched forward
    bc, br = (0, 9.6, -1.2), (5.8, 5.0, 7.0)
    m.ell(bc, br, 'wool', 'body', rot=(0, 10, 0))
    curls(g, m, bc, br, 'body', 46, 'wool', 1.8, 60, rot=(0, 10, 0),
          keep=lambda d: d[1] > -0.55)
    m.tube([(0, 12.0, -7.6), (0, 11.0, -9.4)], [1.3, 1.0], 'wool', 'tail')
    # head lowered for the charge
    m.tube([(0, 10.0, 6.0), (0, 8.8, 9.0)], [3.0, 3.0], 'wool', 'body')
    hc, hr = (0, 8.4, 11.2), (5.0, 4.8, 4.4)
    m.ell(hc, hr, 'face', 'head')
    mc, mr = (0, 6.2, 14.4), (2.8, 2.2, 2.2)
    m.ell(mc, mr, 'face', 'head')
    m.paint(add(mc, (0, -0.4, 1.0)), (2.4, 1.6, 1.4), 'cream', ['head'])
    for s in (-1, 1):
        m.tube([(s * 4.2, 9.8, 10.0), (s * 6.6, 8.8, 9.2), (s * 7.6, 7.6, 8.8)],
               [1.3, 1.1, 0.4], 'face', 'ear%d' % s, flat=0.45, up=(0, 1, 0.2))
        # budding horns under the tuft
        m.tube([(s * 3.0, 12.2, 10.0), (s * 4.6, 13.0, 9.8), (s * 5.4, 12.2, 11.2)],
               [1.0, 0.9, 0.5], 'horn', 'horn%d' % s)
    # the woolly helmet: a dense cap of curls over the brow, jutting forward
    tc, tr = (0, 12.8, 10.6), (3.2, 1.9, 2.8)
    m.ell(tc, tr, 'tuft', 'tuft', rot=(0, 30, 0))
    curls(g, m, tc, tr, 'tuft', 22, 'tuft', 1.3, 61, rot=(0, 30, 0),
          keep=lambda d: d[1] > -0.3)
    g.eye_pair(m, hc, hr, 32, 4, 4.2, 4.4, style='iris', iris=('tuft', 0),
               slant=0.6, center=(0, 8, 16), turn=8)
    p, n = g.on(mc, mr, (0, -0.2, 1))
    m.mouth(p, n, 'line', w=2.0, color=('face', 0))
    return m


# ==========================================================================
# 61 CRAGHORN -- bighorn ram with curled stone horns
# ==========================================================================
def stone_curl(g, m, base, out, up, size, part, turns=1.05, r0=2.6, r1=0.9,
               n=11, seed=0):
    """A ram's horn built from chunky rock segments along a spiral."""
    out = norm(out)
    up = norm(sub(up, mul(out, dot(up, out))))
    side = norm(cross(out, up))
    for i in range(n + 1):
        t = i / float(n)
        a = t * turns * 2 * math.pi
        rad = size * (1.0 - 0.6 * t)
        q = add(base, add(mul(out, math.sin(a) * rad),
                          mul(up, (1 - math.cos(a)) * rad)))
        q = add(q, mul(side, t * size * 0.35))
        rr = r0 + (r1 - r0) * t
        m.rock(q, (rr * 1.15, rr, rr * 1.15), 'stone', part, seed=seed + i,
               n=12, jitter=0.18)


def craghorn(g):
    m = g.Model('CRAGHORN')
    m.outline = (34, 24, 18)
    m.mat('fur', ['#46301e', '#74523a', '#a07c58'])
    m.mat('cream', ['#c8b89a', '#f2e6cc'])
    m.mat('stone', ['#4c4844', '#7a7468', '#a8a292', '#d0cabc'])
    m.mat('hoof', ['#1e1814', '#3a302a'])
    m.eye_dark = (28, 18, 14)
    m.white = (255, 250, 236)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -32
    # strong legs, planted wide
    for s in (-1, 1):
        for zz, nm in ((8.0, 'F'), (-9.0, 'B')):
            m.tube([(s * 5.0, 15.0, zz), (s * 5.4, 7.0, zz + 0.6),
                    (s * 5.6, 2.2, zz + 0.4)], [2.8, 1.8, 1.6], 'fur',
                   'leg%s%d' % (nm, s))
            m.ell((s * 5.6, 1.2, zz + 0.8), (1.9, 1.2, 2.2), 'hoof',
                  'leg%s%d' % (nm, s))
    # deep barrel chest, pale rump and belly
    bc, br = (0, 19.0, -1.0), (8.0, 7.6, 12.4)
    m.ell(bc, br, 'fur', 'body')
    m.ell((0, 22.0, 7.0), (8.4, 8.4, 7.0), 'fur', 'body')
    m.paint((0, 13.0, -1.0), (6.4, 3.0, 11.0), 'cream', ['body'])
    m.paint((0, 20.0, -12.6), (5.6, 5.6, 2.4), 'cream', ['body'])
    m.tube([(0, 23.0, -12.8), (0, 21.0, -14.4)], [1.6, 1.2], 'fur', 'tail')
    # stone plates grown into the shoulders
    for s in (-1, 1):
        m.rock((s * 6.8, 26.0, 6.0), (2.6, 2.0, 3.0), 'stone', 'plate%d' % s,
               seed=61 + s, rot=(0, 0, s * 30))
    m.rock((0, 30.0, 4.0), (3.0, 2.0, 3.2), 'stone', 'plate0', seed=64)
    # neck and head, slightly lowered: ready to clash
    m.tube([(0, 25.0, 9.0), (0, 27.0, 13.0)], [5.2, 4.4], 'fur', 'body')
    hc, hr = (0, 28.0, 15.4), (4.8, 4.8, 5.2)
    m.ell(hc, hr, 'fur', 'head')
    mc, mr = (0, 25.0, 19.6), (3.0, 2.8, 2.6)
    m.ell(mc, mr, 'cream', 'head')
    for s in (-1, 1):
        m.dot(g.on(mc, mr, (s * 0.4, 0.3, 1))[0], (0, 0.2, 1), w=0.9, h=1.1,
              color=('hoof', 0), minw=1, minh=1)
        m.tube([(s * 4.2, 29.0, 13.8), (s * 6.8, 28.0, 12.6), (s * 7.8, 27.0, 12.0)],
               [1.4, 1.2, 0.4], 'fur', 'ear%d' % s, flat=0.45, up=(0, 1, 0.2))
        # the great curled stone horns
        stone_curl(g, m, (s * 3.4, 32.0, 14.4), (s * 0.35, 0.5, -1.0),
                   (s * 0.6, -1.0, 0.0), 6.4, 'horn%d' % s, seed=610 + 20 * (s + 1))
    g.eye_pair(m, hc, hr, 42, 10, 3.0, 2.8, style='iris', iris=('stone', 3),
               slant=0.8, center=(0, 27, 21), turn=4)
    p, n = g.on(mc, mr, (0, -0.5, 1))
    m.mouth(p, n, 'line', w=2.4)
    return m


# ==========================================================================
# 62 STINGLET -- little purple scorpion with a sour lime drop
# ==========================================================================
def length3(a):
    return math.sqrt(dot(a, a))


def arc_pts(c, rad, a0, a1, n, x=0.0):
    """Points on a vertical circle (Y/Z plane) round c, angles in degrees
    measured from -Z (behind) toward +Y (up) and on to +Z."""
    out = []
    for i in range(n):
        a = (a0 + (a1 - a0) * i / float(n - 1)) * DEG
        out.append((x, c[1] + math.sin(a) * rad, c[2] - math.cos(a) * rad))
    return out


def pincer(m, c, s, size, d, mat, part, edge=None):
    """A raised crab-style claw centred on c, pointing along d: a fat palm and
    two curved fingers that open sideways (so the gap shows from the front).
    `edge` paints the inner (cutting) edge of both fingers."""
    d = norm(d)
    side = norm(sub((s, 0, 0), mul(d, s * d[0])))
    th = cross(d, side)
    m.ell_axes(c, (mul(side, 1.05 * size), mul(d, 1.35 * size),
                   mul(th, 0.9 * size)), mat, part)
    for sg, rr in ((1, 0.55), (-1, 0.45)):
        b = add(c, add(mul(d, 0.9 * size), mul(side, 0.52 * size * sg)))
        mid = add(b, add(mul(d, 1.0 * size), mul(side, 0.5 * size * sg)))
        tip = add(b, add(mul(d, 1.9 * size), mul(side, -0.1 * size * sg)))
        m.tube([b, mid, tip], [rr * size, rr * 0.75 * size, 0.14 * size],
               mat, part)
        if edge:
            m.paint(add(mid, mul(side, -0.4 * size * sg)),
                    (0.5 * size, 0.9 * size, 0.5 * size), edge, [part])
    return side


def arched_tail(m, base, top, tip, n, r0, r1, mat, part, seam=None, every=3):
    """A beaded tail from base up through top and down to tip (a smooth
    Catmull curve), one part per bead so the joints get outlined.  Every
    `every`-th bead is a thin glowing seam when `seam` is given."""
    ctrl = [base, lerp(base, top, 0.55), top, lerp(top, tip, 0.6), tip]
    # sample a Catmull-Rom curve by hand (the gen_monsters one is internal)
    dense = []
    P = [ctrl[0]] + ctrl + [ctrl[-1]]
    for i in range(1, len(P) - 2):
        for k in range(12):
            t = k / 12.0
            t2, t3 = t * t, t * t * t
            dense.append(tuple(0.5 * (2 * P[i][j] + (-P[i - 1][j] + P[i + 1][j]) * t
                                      + (2 * P[i - 1][j] - 5 * P[i][j] + 4 * P[i + 1][j]
                                         - P[i + 2][j]) * t2
                                      + (-P[i - 1][j] + 3 * P[i][j] - 3 * P[i + 1][j]
                                         + P[i + 2][j]) * t3) for j in range(3)))
    dense.append(ctrl[-1])
    cum = [0.0]
    for i in range(1, len(dense)):
        cum.append(cum[-1] + length3(sub(dense[i], dense[i - 1])))
    out = []
    for k in range(n):
        want = cum[-1] * k / (n - 1)
        j = min(len(dense) - 2, max(0, next((i for i, c in enumerate(cum)
                                             if c >= want), len(cum) - 1) - 1))
        f = (want - cum[j]) / max(1e-6, cum[j + 1] - cum[j])
        q = lerp(dense[j], dense[j + 1], min(1.0, f))
        dn = norm(sub(dense[j + 1], dense[j]))
        r = r0 + (r1 - r0) * k / (n - 1.0)
        if seam and k % every == every - 1 and k < n - 1:
            up = norm(cross(dn, (1, 0, 0)))
            m.ell_axes(q, ((r * 0.96, 0, 0), mul(dn, 0.5), mul(up, r * 0.96)),
                       seam, '%s%d' % (part, k))
        else:
            up = norm(cross(dn, (1, 0, 0)))
            m.ell_axes(q, ((r, 0, 0), mul(dn, r * 1.05), mul(up, r * 0.98)),
                       mat, '%s%d' % (part, k))
        out.append((q, dn, r))
    return out


def stinglet(g):
    m = g.Model('STINGLET')
    m.outline = (36, 16, 50)
    m.mat('shell', ['#43206a', '#6c3c9c', '#9c6cd0', '#ceb0f4'])
    m.mat('belly', ['#b494dc', '#e2d4f8'])
    m.mat('lime', ['#5aa018', '#b4ec3a', '#f2ffbc'], emissive=0.5)
    m.eye_dark = (30, 12, 40)
    m.white = (255, 255, 255)
    m.height = 38
    m.front_yaw = -22
    # four pairs of little legs
    for s in (-1, 1):
        for k in range(4):
            z = 1.6 - k * 1.8
            b = (s * 3.0, 3.4, z)
            m.tube([b, (s * 5.4, 4.2, z - k * 0.3), (s * 6.6, 0.8, z - k * 0.5)],
                   [0.75, 0.6, 0.4], 'shell', 'leg%d' % s)
    # plump segmented body, pale underside
    for k in range(4):
        c = (0, 4.4, 1.2 - k * 2.2)
        m.ell(c, (4.0 - k * 0.35, 2.6, 1.9), 'shell', 'body%d' % k)
        m.paint(add(c, (0, -1.4, 0)), (3.2 - k * 0.3, 1.2, 1.6), 'belly',
                ['body%d' % k])
    # tail: beads arching up over the back, the sting hanging above the head
    tl = arched_tail(m, (0, 5.0, -6.0), (2.2, 14.8, -7.4), (0.8, 17.8, -1.8), 9,
                     1.6, 1.15, 'shell', 'tail')
    q, dn, r = tl[-1]
    sb = add(q, (0, -0.2, 1.2))
    m.ell(sb, (1.9, 1.8, 2.1), 'shell', 'tailS')
    tip = add(sb, (0, -3.0, 1.6))
    m.tube([add(sb, (0, -0.6, 1.2)), add(sb, (0, -2.0, 2.0)), tip],
           [1.0, 0.6, 0.2], 'shell', 'tailS')
    m.sph(add(tip, (0, -0.9, 0.1)), 1.35, 'lime', 'tailS')
    # big round head with a pale face
    hc, hr = (0, 6.0, 4.4), (4.4, 3.8, 3.5)
    m.ell(hc, hr, 'shell', 'head')
    m.paint(add(hc, (0, -1.2, 2.2)), (3.0, 1.6, 1.6), 'belly', ['head'])
    # chunky pincers raised either side of the face, opening upward
    for s in (-1, 1):
        sh = (s * 3.6, 5.0, 5.6)
        el = (s * 7.8, 5.0, 6.2)
        cl = (s * 8.6, 8.8, 7.0)
        m.tube([sh, el, add(cl, (0, -1.6, 0))], [1.0, 1.1, 1.2], 'shell',
               'arm%d' % s)
        pincer(m, cl, s, 1.8, (s * 0.2, 0.9, 0.35), 'shell', 'arm%d' % s)
    g.eye_pair(m, hc, hr, 30, 20, 3.6, 4.0, iris=('lime', 0), center=(0, 5, 10),
               turn=2)
    p, n = g.on(hc, hr, (0, -0.25, 1))
    m.mouth(p, n, 'smile', w=2.4)
    # overworld: a 3/4 turn so the arched tail and pincers both show
    g.OW_TURN[m.name] = -40.0
    return m


# ==========================================================================
# 63 SCORCHION -- dark scorpion with ember seams and a burning sting
# ==========================================================================
def scorchion(g):
    m = g.Model('SCORCHION')
    m.outline = (26, 10, 8)
    m.mat('shell', ['#2e1a1c', '#52302e', '#7c4c40', '#aa7462'])
    m.mat('socket', ['#180a0a'])
    m.mat('ember', ['#d8400c', '#ff9424', '#ffe070'], emissive=0.75)
    m.mat('flame', ['#e04a10', '#ff9a2a'], emissive=0.8)
    m.mat('core', ['#fff4b0'], emissive=0.9)
    m.eye_dark = (20, 8, 6)
    m.white = (255, 244, 220)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -22
    # four pairs of jointed legs, knees glowing
    for s in (-1, 1):
        for k in range(4):
            z = 3.0 - k * 3.2
            b = (s * 4.6, 5.6, z)
            kn = (s * 9.0, 7.6, z + 0.4 - k * 0.6)
            ft = (s * 11.0, 0.9, z - k * 0.9)
            m.tube([b, kn, ft], [1.3, 1.1, 0.6], 'shell', 'leg%d' % s)
            m.sph(kn, 0.95, 'ember', 'leg%d' % s)
    # armoured body: overlapping plates with glowing seams between them
    for k in range(5):
        c = (0, 6.4 + k * 0.2, 2.4 - k * 3.0)
        m.ell(c, (6.2 - k * 0.45, 3.2, 2.4), 'shell', 'body')
        m.ell(add(c, (0, 0.1, -1.5)), (5.6 - k * 0.45, 2.8, 0.9), 'ember', 'body')
    # tail: heavy plates arching up and over, a seam glowing every third
    tl = arched_tail(m, (0, 7.4, -11.4), (2.6, 23.0, -12.8), (0.4, 29.0, -3.6),
                     12, 2.9, 1.9, 'shell', 'tail', seam='ember', every=3)
    q, dn, r = tl[-1]
    # swollen stinger bulb glowing through its shell, the sting a flame
    sb = add(q, (0, -0.2, 1.8))
    m.ell(sb, (2.6, 2.4, 2.8), 'shell', 'tailS')
    m.paint(add(sb, (0, -0.8, 1.2)), (1.8, 1.4, 1.8), 'ember', ['tailS'])
    tip = add(sb, (0, -3.4, 2.4))
    m.tube([add(sb, (0, -1.0, 1.6)), add(sb, (0, -2.4, 2.6)), tip],
           [1.3, 0.8, 0.25], 'shell', 'tailS')
    g.flame(m, add(sb, (0, 1.6, 0.2)), 11.0, 3.4, 'sting',
            mats=('flame', 'ember', 'core'), up=(0, 1, 0.15), tongues=2,
            seed=63)
    # broad head shield with a raised brow ridge
    hc, hr = (0, 9.0, 6.8), (6.6, 5.0, 4.8)
    m.ell(hc, hr, 'shell', 'head')
    for s in (-1, 1):
        m.tube([add(hc, (s * 0.8, 3.8, 2.4)), add(hc, (s * 4.2, 3.2, 2.6)),
                add(hc, (s * 6.0, 1.8, 1.6))], [1.0, 0.9, 0.5], 'shell', 'head')
    # heavy pincers raised either side of the face, ember-lit cutting edges
    for s in (-1, 1):
        sh = (s * 5.4, 7.2, 7.6)
        el = (s * 12.0, 7.4, 8.4)
        cl = (s * 12.8, 14.4, 9.6)
        m.tube([sh, el, add(cl, (0, -2.6, 0))], [1.9, 2.0, 2.2], 'shell',
               'arm%d' % s)
        m.sph(el, 1.1, 'ember', 'arm%d' % s)
        pincer(m, cl, s, 2.8, (s * 0.2, 0.9, 0.35), 'shell', 'arm%d' % s,
               edge='ember')
    # burning eyes set in dark sockets under the brow
    for s in (-1, 1):
        a = (s * 34 + 4) * DEG
        d = (math.sin(a) * math.cos(14 * DEG), math.sin(14 * DEG),
             math.cos(a) * math.cos(14 * DEG))
        p, n = g.on(hc, hr, d)
        m.paint(add(p, (0, 0.2, 0)), (3.0, 2.5, 2.2), 'socket', ['head'])
        m.eye(p, n, 4.0, 3.4, style='glow', iris=('ember', 2), slant=0.7,
              glint=True, center=(0, 8, 14), minw=2, minh=2)
    # glowing mandible seam
    p, n = g.on(hc, hr, (0, -0.35, 1))
    m.mouth(p, n, 'line', w=4.0, color=('ember', 1))
    # overworld: a 3/4 turn so the tail arch and both claws show
    g.OW_TURN[m.name] = -35.0
    return m


# ==========================================================================
# 64 DIGGET -- velvet mole carrying a tiny lantern
# ==========================================================================
def hand_lantern(m, c, sc, part, glow='glow', metal='brass'):
    """A little glass-and-brass lantern with a carry loop, centred on c."""
    m.ell(c, (1.3 * sc, 1.6 * sc, 1.3 * sc), glow, part)
    m.ell(add(c, (0, 1.7 * sc, 0)), (1.6 * sc, 0.6 * sc, 1.6 * sc), metal, part)
    m.ell(add(c, (0, -1.7 * sc, 0)), (1.5 * sc, 0.5 * sc, 1.5 * sc), metal, part)
    for a in (45, 135, 225, 315):
        d = (math.sin(a * DEG) * 1.3 * sc, 0, math.cos(a * DEG) * 1.3 * sc)
        m.tube([add(c, add(d, (0, -1.5 * sc, 0))), add(c, add(d, (0, 1.5 * sc, 0)))],
               [0.3 * sc, 0.3 * sc], metal, part)
    top = add(c, (0, 2.2 * sc, 0))
    m.tube([add(top, (-0.9 * sc, 0, 0)), add(top, (-0.7 * sc, 1.1 * sc, 0)),
            add(top, (0.7 * sc, 1.1 * sc, 0)), add(top, (0.9 * sc, 0, 0))],
           0.28 * sc, metal, part)
    return add(top, (0, 1.2 * sc, 0))


def spade_paw(m, c, s, part, mat, size=1.0, nrm=(0, 0.2, 1)):
    """A broad flat digging paw with five stubby claws."""
    n = norm(nrm)
    side = norm(cross((0, 1, 0), n)) if abs(n[1]) < 0.9 else (1, 0, 0)
    up = norm(cross(n, side))
    m.ell_axes(c, (mul(side, 2.2 * size), mul(up, 2.0 * size), mul(n, 0.9 * size)),
               mat, part)
    for k in range(5):
        u = (k - 2) * 0.85 * size
        b = add(c, add(mul(side, u), mul(up, 1.4 * size)))
        tip = add(b, add(mul(up, 1.3 * size), mul(n, 0.3 * size)))
        m.tube([b, tip], [0.45 * size, 0.2 * size], mat, part)


def digget(g):
    m = g.Model('DIGGET')
    m.outline = (26, 20, 32)
    m.mat('fur', ['#262230', '#403a4c', '#645c72', '#8a8298'])
    m.mat('pink', ['#c46a80', '#f2a0b2'])
    m.mat('glow', ['#ffb830', '#fff2a0'], emissive=0.8)
    m.mat('brass', ['#8a5a1c', '#d8a040'])
    m.mat('dirt', ['#6a4a30'])
    m.eye_dark = (20, 16, 26)
    m.white = (255, 250, 240)
    m.height = 26
    m.front_yaw = -30
    # little dirt mound it popped out of
    m.ell((0, 0.8, -1.0), (8.4, 1.8, 7.6), 'dirt', 'dirt')
    for q, r in (((-6.4, 1.8, 2.4), 1.4), ((5.8, 1.6, -4.0), 1.2), ((-3.0, 2.0, -6.0), 1.3)):
        m.sph(q, r, 'dirt', 'dirt')
    # plump velvet body, stubby tail
    bc, br = (0, 7.4, -0.6), (6.4, 5.8, 6.6)
    m.ell(bc, br, 'fur', 'body')
    m.tube([(0, 5.0, -6.8), (0, 4.4, -8.6)], [0.8, 0.5], 'pink', 'tail')
    for s in (-1, 1):
        m.ell((s * 3.6, 1.8, 2.4), (1.8, 1.0, 2.2), 'pink', 'foot%d' % s)
    # head tapering into a long pink nose
    hc, hr = (0, 9.8, 4.2), (4.6, 4.2, 4.2)
    m.ell(hc, hr, 'fur', 'head')
    m.tube([(0, 9.2, 6.8), (0, 8.6, 9.2), (0, 8.2, 10.6)], [2.6, 1.8, 1.2],
           'fur', 'head')
    m.ell((0, 8.2, 11.2), (1.5, 1.2, 1.0), 'pink', 'head')
    # the big pink spade paws: one planted, one raising the lantern
    spade_paw(m, (-5.6, 5.0, 5.2), -1, 'arm-1', 'pink', 1.0, nrm=(-0.4, 0.1, 1))
    m.tube([(-4.6, 7.0, 2.6), (-5.4, 5.8, 4.2)], [1.8, 1.6], 'fur', 'arm-1')
    m.tube([(4.8, 8.2, 2.2), (7.0, 9.8, 4.0), (7.6, 12.6, 5.0)], [1.8, 1.6, 1.4],
           'fur', 'arm1')
    spade_paw(m, (7.8, 13.4, 5.2), 1, 'arm1', 'pink', 0.8, nrm=(0.3, -0.2, 1))
    # tiny lantern dangling from the raised paw
    m.tube([(7.8, 15.0, 5.4), (8.8, 17.4, 5.6)], [0.3, 0.3], 'brass', 'lamp')
    hand_lantern(m, (9.4, 12.2, 6.2), 1.1, 'lamp')
    m.tube([(8.6, 15.2, 6.2), (8.8, 17.4, 5.6)], [0.28, 0.28], 'brass', 'lamp')
    # squinty little eyes, whiskers of a smile
    g.eye_pair(m, hc, hr, 30, 10, 2.4, 2.4, style='sleepy', center=(0, 9, 11))
    p, n = g.on(hc, hr, (0, -0.5, 0.9))
    m.mouth(p, n, 'smile', w=2.2)
    for s in (-1, 1):
        m.dot(g.on(hc, hr, (s * 0.62, -0.2, 0.75))[0], (s * 0.6, 0, 0.8),
              w=1.3, h=0.8, color=('pink', 1), minw=2)
    return m


# ==========================================================================
# 65 SEXTONE -- gravekeeper mole with a spade and a ghost-lamp
# ==========================================================================
def sextone(g):
    m = g.Model('SEXTONE')
    m.outline = (20, 16, 26)
    m.mat('fur', ['#1e1a26', '#3a3446', '#645c74'])
    m.mat('pink', ['#b0607a', '#e894aa'])
    m.mat('glow', ['#2ed88c', '#b4ffd8'], emissive=0.85)
    m.mat('iron', ['#4a5058', '#8c96a0'], spec=0.4)
    m.mat('wood', ['#7a5434'])
    m.mat('cloth', ['#3a2c3a', '#5c4658'])
    m.eye_dark = (10, 8, 14)
    m.white = (240, 255, 248)
    m.height = 58
    m.max_w = 62
    m.front_yaw = -24
    # the spade planted in the ground on its right, taller than its head
    sp0, sp1 = (-10.0, 4.0, 5.0), (-9.4, 42.0, 3.4)
    m.box((-10.0, 5.0, 5.0), (3.2, 4.4, 0.5), 'iron', 'spade', rot=(0, 0, 0))
    m.tube([sp0, sp1], [0.9, 0.9], 'wood', 'spade')
    m.tube([add(sp1, (-2.0, 0, 0)), add(sp1, (2.0, 0, 0))], [0.8, 0.8], 'wood', 'spade')
    # short legs, broad pink feet
    for s in (-1, 1):
        m.ell((s * 4.2, 4.4, 0.0), (3.2, 4.2, 3.6), 'fur', 'leg%d' % s)
        m.ell((s * 4.6, 1.3, 3.0), (2.6, 1.3, 3.6), 'pink', 'leg%d' % s)
    # pear-shaped upright body
    bc, br = (0, 17.0, -0.4), (8.0, 11.0, 7.0)
    m.ell(bc, br, 'fur', 'body')
    # a ragged gravedigger's shawl over the shoulders
    rnd = g.Rand(65)
    for k in range(13):
        a = (-150 + 300.0 * k / 12) * DEG
        b = (math.sin(a) * 6.6, 27.6, math.cos(a) * 5.6 - 0.4)
        ln = 7.0 + rnd.f() * 3.0
        d = norm((math.sin(a) * 0.35, -1.0, math.cos(a) * 0.35))
        m.tube([b, add(b, mul(d, ln * 0.5)), add(b, mul(d, ln))],
               [2.6, 2.2, 0.6], 'cloth', 'shawl', flat=0.45,
               up=(math.sin(a), 0, math.cos(a)))
    m.ell((0, 28.0, -0.2), (7.4, 3.0, 6.4), 'cloth', 'shawl')
    # right arm gripping the spade handle
    m.tube([(-6.8, 26.0, 0.6), (-10.0, 22.0, 2.6), (-9.8, 26.0, 4.4)],
           [2.4, 2.0, 1.8], 'fur', 'arm-1')
    spade_paw(m, (-9.4, 27.4, 4.8), -1, 'arm-1', 'pink', 1.1, nrm=(-0.3, 0, 1))
    # left arm holding the ghost-lamp out toward us
    m.tube([(6.8, 26.0, 0.6), (10.2, 22.0, 3.4), (11.4, 20.0, 7.0)],
           [2.4, 2.0, 1.8], 'fur', 'arm1')
    spade_paw(m, (11.6, 20.6, 8.0), 1, 'arm1', 'pink', 1.1, nrm=(0.2, -0.3, 1))
    hand_lantern(m, (11.8, 14.0, 8.4), 1.7, 'lamp', glow='glow', metal='iron')
    m.tube([(11.8, 18.0, 8.4), (11.8, 21.6, 8.2)], [0.4, 0.4], 'iron', 'lamp')
    # head with a long pink nose and a pale grave-glow in its eyes
    hc, hr = (0, 33.0, 1.6), (5.8, 5.4, 5.4)
    m.ell(hc, hr, 'fur', 'head')
    m.tube([(0, 32.2, 5.0), (0, 31.2, 8.4), (0, 30.6, 10.4)], [3.4, 2.4, 1.5],
           'fur', 'head')
    m.ell((0, 30.6, 11.0), (1.9, 1.5, 1.2), 'pink', 'head')
    # a battered wide-brimmed hat
    m.ell((0, 37.4, 0.8), (8.6, 0.8, 8.0), 'cloth', 'hat', rot=(0, -8, 6))
    m.ell((0, 39.6, 0.4), (4.8, 3.2, 4.6), 'cloth', 'hat', rot=(0, -8, 6))
    m.paint((0, 38.6, 0.5), (5.0, 0.8, 4.8), 'wood', ['hat'], rot=(0, -8, 6))
    for s in (-1, 1):
        p, n = g.on(hc, hr, norm((s * 0.5 + 0.06, 0.12, 0.85)))
        m.paint(p, (1.8, 1.4, 1.4), 'fur', ['head'])
        m.eye(p, n, 2.6, 2.0, style='glow', iris=('glow', 1), slant=0.4,
              glint=False, center=(0, 33, 10))
    p, n = g.on(hc, hr, (0, -0.55, 0.85))
    m.mouth(p, n, 'line', w=2.4)
    # wisps drifting from the lamp
    for q, r in (((13.6, 18.4, 9.6), 0.8), ((14.8, 21.4, 9.2), 0.6)):
        m.sph(q, r, 'glow', 'wisp')
    return m


# ==========================================================================
# 66 QUARTZLING -- pale grub growing amethyst points on its back
# ==========================================================================
def quartzling(g):
    m = g.Model('QUARTZLING')
    m.outline = (44, 30, 50)
    m.mat('grub', ['#a0907e', '#d4c6b4', '#f4ece0', '#fffaf2'])
    m.mat('quartz', ['#4e2482', '#8a50c8', '#c496f0', '#f0e0ff'], spec=0.5)
    m.mat('dark', ['#4a3a34'])
    m.mat('pink', ['#e8a0a8'])
    m.eye_dark = (34, 22, 30)
    m.white = (255, 255, 255)
    m.height = 30
    m.front_yaw = -28
    # plump segments in a gentle curl, biggest in the middle
    # (straight, with the front two segments reared up so the face sits
    # high and reads head-on)
    segs = []
    for k in range(6):
        t = k / 5.0
        z = 6.0 - k * 3.2
        r = 3.2 + 1.0 * math.sin(math.pi * (0.2 + 0.7 * t)) - t * 0.9
        lift = (2.6, 1.0, 0.0, 0.0, 0.0, 0.0)[k]
        segs.append(((0.0, r * 0.95 + lift, z + (0.0, 0.6, 0, 0, 0, 0)[k]), r))
    for k, (c, r) in enumerate(segs):
        m.ell(c, (r, r * 0.95, r * 0.72), 'grub', 'body')
        # stubby legs under the front segments
        if 1 < k < 5:
            for s in (-1, 1):
                m.ell(add(c, (s * r * 0.8, -r * 0.7, 0.3)), (0.8, 0.9, 0.8),
                      'grub', 'leg%d' % s)
    # amethyst points along the back, bigger toward the rear
    rnd = g.Rand(66)
    for k, (c, r) in enumerate(segs[1:]):
        n = 1 if k in (0, 4) else 2
        for j in range(n):
            sx = 0 if n == 1 else (j * 2 - 1)
            d = norm((sx * 0.55, 1.0, -0.2))
            b = add(c, (sx * r * 0.4, r * 0.7, 0))
            ln = (3.8 + k * 0.9 - (1.4 if k == 4 else 0)) * (0.9 + 0.2 * rnd.f())
            m.crystal(sub(b, mul(d, 0.8)), add(b, mul(d, ln)), 1.0 + k * 0.1,
                      'quartz', 'crys%d' % k, sides=6, tip_frac=0.4,
                      twist=rnd.f() * 60)
    # round head with tiny mandibles
    hc, hr = (0.0, 8.4, 8.6), (4.0, 3.7, 3.3)
    m.ell(hc, hr, 'grub', 'head')
    for s in (-1, 1):
        b = add(hc, (s * 1.4, -1.6, 2.2))
        m.tube([b, add(b, (s * 0.6, -0.4, 1.2)), add(b, (-s * 0.2, -0.6, 1.8))],
               [0.5, 0.4, 0.15], 'dark', 'head')
        # little antennae
        a0 = add(hc, (s * 1.4, 2.6, 1.2))
        m.tube([a0, add(a0, (s * 1.0, 1.6, 0.8)), add(a0, (s * 2.0, 2.2, 0.6))],
               [0.35, 0.3, 0.25], 'dark', 'head')
    g.eye_pair(m, hc, hr, 36, 12, 2.4, 2.8, iris=('quartz', 1), center=(0, 8, 14),
               turn=12)
    # overworld: a slight turn so the crystal-backed body shows behind
    g.OW_TURN[m.name] = -25.0
    p, n = g.on(hc, hr, (0.1, -0.25, 1))
    m.mouth(p, n, 'smile', w=1.8)
    for s in (-1, 1):
        m.dot(g.on(hc, hr, (s * 0.62, -0.2, 0.75))[0], (s * 0.6, 0, 0.8),
              w=1.2, h=0.8, color=('pink', 0), minw=2)
    return m


# ---- end of batch ----
