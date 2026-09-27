"""Art for kin 101-106 (KIN-R1).

One model function per species (the lowercase species name), called by
tools/gen_monsters.py as fn(g) with g = the gen_monsters module. Coordinates:
+Y up, +Z the way the kin faces, +X its left; the ground is y = 0.
"""

import math

DEG = math.pi / 180.0

# Shared ramps (shadows lean cool, lights lean warm).
KOI_WHITE = ['#7a7c9c', '#ccd2de', '#f4f4ee', '#ffffff']
KOI_RED = ['#8c1c2c', '#d63a34', '#ff7a52']
WATER = ['#1c4c8c', '#3a8cc8', '#88d0f0']
GOLD = ['#9a6418', '#e0a834', '#ffe890']
BONE = ['#5e4c58', '#a0907e', '#d8ccb2', '#f8f2e0']
RUST = ['#4a2a26', '#8a4a30', '#c47a44']
IRON = ['#2c2a3a', '#4e5064', '#8288a0', '#c4cad8']


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def norm(a):
    ln = math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2]) or 1.0
    return (a[0] / ln, a[1] / ln, a[2] / ln)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


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
        g.OW_FLOAT[m.name] = lift
    if side is not None:
        g.OW_SIDE_YAW[m.name] = side


def veil(m, pts, wdt, mat, part, up, flat=0.22, mats=None):
    """A flowing fin: a flat tube swelling in the middle, ending in a point."""
    m.tube(pts, None, mat, part, flat=flat, up=up, mats=mats,
           rfn=lambda t: wdt * math.sin(math.pi * min(1.0, 0.12 + t * 0.9)) ** 0.7 + 0.15)


def splash(g, m, c, r, part, mat='water', foam='foam', n=9, seed=4):
    """A splash crown: a flat pool with a ring of leaping droplets."""
    m.ell(c, (r, r * 0.16, r * 0.86), mat, part)
    m.ell(add(c, (0, 0.3, 0)), (r * 0.72, r * 0.14, r * 0.62), foam, part)
    rnd = g.Rand(seed)
    for k in range(n):
        a = 2 * math.pi * (k + 0.3 * rnd.f()) / n
        b = (math.sin(a) * r * 0.8, c[1], math.cos(a) * r * 0.7 + c[2])
        h = r * (0.35 + 0.25 * rnd.f())
        tip = add(b, (math.sin(a) * r * 0.25, h, math.cos(a) * r * 0.2))
        m.tube([b, lerp(b, tip, 0.6), tip], [r * 0.14, r * 0.1, r * 0.06], mat, part)
        m.sph(add(tip, (math.sin(a) * 0.5, 0.9, math.cos(a) * 0.4)), r * 0.08, foam, part)


# ==========================================================================
# 101 KOIRIN  TIDE  kohaku koi leaping out of a splash
# ==========================================================================
def koirin(g):
    m = g.Model('KOIRIN')
    m.outline = (34, 30, 52)
    m.mat('koi', KOI_WHITE)
    m.mat('red', KOI_RED)
    m.mat('water', WATER)
    m.mat('foam', ['#d8f4ff'])
    m.mat('gold', GOLD[1:])
    m.white = rgb(KOI_WHITE[3])
    m.eye_dark = (34, 30, 52)
    m.height = 34
    m.front_yaw = -52
    # overworld down/up: turn to the same 3/4 view so the face shows
    g.OW_TURN[m.name] = -62
    # and tuck the splash up under the body there: a shorter kin draws bigger
    m.ow_offsets = {'splash': (0, 3.6, 1.0), 'tail': (0, -1.4, 0.8)}
    # the splash it leaps from, with a spout wrapping the tail root
    splash(g, m, (0, 1.2, -1.0), 8.0, 'splash')
    m.tube([(0, 1.0, -3.4), (0, 3.4, -4.6), (0, 5.4, -5.4)], [3.0, 2.0, 1.2], 'water', 'splash')
    # body: an arched leap, tail low at the back, head up and forward
    spine = [(0, 7.0, -9.4), (0, 8.2, -6.6), (0, 11.2, -3.6), (0, 15.2, -0.4), (0, 18.4, 3.2)]
    m.tube(spine, [1.1, 2.6, 3.9, 4.2, 3.8], 'koi', 'body', flat=0.8, up=(1, 0, 0))
    head_c, head_r, hrot = (0, 19.4, 4.6), (3.4, 3.5, 4.2), (0, -40, 0)
    m.ell(head_c, head_r, 'koi', 'head', rot=hrot)
    # kohaku markings: a red cap on the head and two saddles wrapping the flanks
    m.paint(add(head_c, (0, 2.4, -1.2)), (3.6, 2.4, 2.8), 'red', ['head'], rot=hrot)
    m.paint((0, 15.4, -1.8), (5.0, 3.6, 2.6), 'red', ['body'], rot=(0, -40, 0))
    m.paint((0, 9.6, -6.6), (5.0, 2.6, 2.0), 'red', ['body'], rot=(0, -20, 0))
    for s in (-1, 1):
        m.paint((s * 3.4, 12.0, -2.2), (1.6, 2.4, 2.6), 'red', ['body'], rot=(0, -40, 0))
    # long flowing butterfly tail, two lobes fanning up and back out of the spray
    tb = (0, 7.0, -9.6)
    for s in (-1, 1):
        veil(m, [tb, add(tb, (s * 1.4, 1.6 + 1.4 * s, -2.8)), add(tb, (s * 2.4, 3.0 + 3.4 * s, -5.0)),
                 add(tb, (s * 2.8, 3.4 + 5.4 * s, -6.4))], 2.6, 'koi', 'tail', up=(1, 0, 0.1),
             mats=[(0.0, 'koi'), (0.62, 'red')])
    # pectoral fins streaming back, a red dorsal ridge
    for s in (-1, 1):
        pb = (s * 3.2, 15.0, 2.2)
        veil(m, [pb, add(pb, (s * 3.2, -1.4, -1.6)), add(pb, (s * 5.2, -3.6, -3.4))], 1.9, 'koi',
             'fin%d' % s, up=(0, 0.6, 0.6))
    veil(m, [(0, 18.6, -0.2), (0, 18.4, -3.0), (0, 15.2, -5.2), (0, 11.4, -7.2)], 1.8, 'red', 'dorsal',
         up=(1, 0, 0), flat=0.3)
    # snout: a round mouth, gold barbels drooping from the lips
    snout = g.on(head_c, head_r, (0, 0.2, 1), hrot)
    for s in (-1, 1):
        b = add(snout[0], (s * 1.2, -0.6, -0.8))
        m.tube([b, add(b, (s * 1.2, -1.2, -0.6)), add(b, (s * 1.6, -3.0, -1.4))], [0.4, 0.32, 0.2],
               'gold', 'head')
    m.mouth(snout[0], snout[1], 'open', w=1.8, h=1.8, inner=('red', 0))
    g.eye_pair(m, head_c, head_r, 52, 18, 3.6, 3.8, style='iris', iris=('gold', 0), rot=hrot,
               center=add(head_c, (0, 0, 6)), turn=10)
    # a few loose droplets flying off its fins
    for p in ((6.6, 17.4, 2.4), (-6.2, 12.4, 0.2), (5.2, 22.8, -1.0)):
        m.sph(p, 0.7, 'foam', 'drops')
    return m


# ==========================================================================
# 102 RYUKOI  TIDE/WYRM  white-red-gold koi dragon holding a rain pearl
# ==========================================================================
def ryukoi(g):
    m = g.Model('RYUKOI')
    m.outline = (38, 26, 44)
    m.mat('koi', KOI_WHITE)
    m.mat('red', KOI_RED)
    m.mat('gold', GOLD, spec=0.3)
    m.mat('pearl', WATER, emissive=0.45)
    m.white = rgb(KOI_WHITE[3])
    m.eye_dark = (38, 26, 44)
    m.height = 58
    m.max_w = 60
    m.float_lift = 3
    ow(g, m, lift=3, side=-64)
    # serpentine koi body coiling up from the tail to a raised neck
    spine = [(7.5, 5.0, -8.0), (5.5, 3.4, -3.6), (0.5, 4.2, 0.6), (-4.6, 7.4, 0.4), (-6.0, 12.0, -3.2),
             (-3.0, 16.4, -6.0), (2.4, 20.2, -5.4), (5.0, 24.8, -2.0), (3.4, 29.6, 1.8), (0.4, 33.6, 4.2)]
    radii = [1.0, 2.2, 3.3, 3.9, 4.2, 4.3, 4.2, 3.9, 3.5, 3.1]
    m.tube(spine, radii, 'koi', 'body')
    # kohaku saddles along the coil (wrapping the side that faces out),
    # gold belly plates up the front of the neck
    for i, sz, side in ((2, 3.4, 1), (4, 4.2, -1), (6, 4.0, 1), (8, 3.4, -1)):
        q, r = spine[i], radii[i]
        m.paint(add(q, (side * r * 0.5, r * 0.4, r * 0.35)), (sz, sz * 0.8, sz), 'red', ['body'])
    for k in range(5):
        t = k / 4.0
        q = lerp((0.8, 32.4, 6.6), (4.4, 22.6, 1.4), t)
        m.paint(q, (2.0, 0.8, 1.8), 'gold', ['body'])
    # banner fins streaming off the outside of the coil (red, gold-tipped)
    for i, sx in ((3, -1), (5, -1), (7, 1)):
        q, r = spine[i], radii[i]
        tng = norm(sub(spine[i + 1], spine[i - 1]))
        out = norm((sx * 1.0, 0.25, -0.5))
        b = add(q, mul(out, r * 0.6))
        veil(m, [b, add(b, add(mul(out, 3.0), mul(tng, -1.0))), add(b, add(mul(out, 6.4), mul(tng, -2.6)))],
             2.2, 'red', 'banner%d' % i, up=(0, 0, 1), flat=0.25, mats=[(0.0, 'red'), (0.7, 'gold')])
    # the koi tail: a long white-to-red butterfly fin with gold tips
    tb = spine[0]
    for s in (-1, 1):
        veil(m, [tb, add(tb, (2.4, 1.8 + 2.4 * s, -1.6)), add(tb, (4.4, 2.6 + 5.6 * s, -2.8)),
                 add(tb, (5.2, 2.8 + 7.8 * s, -3.4))], 3.2, 'koi', 'tail', up=(0.4, 0, 0.9),
             mats=[(0.0, 'koi'), (0.45, 'red'), (0.86, 'gold')])
    # small arms cradling the rain pearl, gold claws, pectoral veils
    pearl = (0.0, 22.4, 6.4)
    for s in (-1, 1):
        sh = (s * 3.2, 25.6, 1.0)
        el = (s * 4.6, 22.2, 2.6)
        hd = (s * 2.8, 21.8, 6.0)
        m.tube([sh, el, hd], [1.3, 1.1, 1.0], 'koi', 'arm%d' % s)
        for t in (-1, 0, 1):
            m.tube([hd, add(hd, (-s * 0.6, t * 0.9 + 0.4, 1.4))], [0.45, 0.2], 'gold', 'arm%d' % s)
        veil(m, [sh, add(sh, (s * 3.4, -0.4, -2.2)), add(sh, (s * 6.0, -2.4, -4.0))], 1.6, 'koi',
             'pec%d' % s, up=(0, 0.7, 0.4), mats=[(0.0, 'koi'), (0.7, 'red')])
    m.sph(pearl, 3.0, 'pearl', 'pearl')
    m.paint(add(pearl, (-1.0, 1.1, 1.8)), 1.0, 'koi', ['pearl'])
    # head: a long koi-dragon skull, gold whiskers and swept horns, a red mane
    hc, hr, hrot = (0.0, 37.4, 6.4), (4.5, 4.0, 4.8), (0, 8, 0)
    m.ell(hc, hr, 'koi', 'head', rot=hrot)
    sn_c, sn_r = (0.0, 35.8, 11.0), (3.0, 2.5, 3.8)
    m.ell(sn_c, sn_r, 'koi', 'head')
    m.paint(add(hc, (0, 3.0, -0.6)), (3.4, 1.8, 3.2), 'red', ['head'])
    for s in (-1, 1):
        # antler-like horns sweeping back
        hb = (s * 2.2, 39.8, 4.6)
        m.tube([hb, add(hb, (s * 1.4, 3.2, -1.8)), add(hb, (s * 2.4, 5.6, -4.8)), add(hb, (s * 2.6, 6.6, -7.0))],
               [1.0, 0.8, 0.5, 0.2], 'gold', 'horn%d' % s)
        m.tube([add(hb, (s * 1.2, 2.8, -1.6)), add(hb, (s * 3.0, 4.6, -0.8))], [0.6, 0.2], 'gold', 'horn%d' % s)
        # long whiskers flowing back from the snout
        wb = (s * 1.8, 35.0, 13.2)
        m.tube([wb, add(wb, (s * 3.0, -0.4, -0.6)), add(wb, (s * 6.0, 1.6, -2.8)), add(wb, (s * 7.6, -0.8, -6.0)),
                add(wb, (s * 8.2, -3.4, -8.0))], [0.7, 0.65, 0.55, 0.4, 0.25], 'gold', 'whisker%d' % s)
        # finned cheeks
        veil(m, [(s * 3.2, 36.4, 5.4), (s * 5.2, 36.0, 3.6), (s * 6.4, 34.2, 2.2)], 1.4, 'red',
             'cheek%d' % s, up=(0, 0.3, 1.0))
    # flowing red mane down the nape
    for k, (dx, dy) in enumerate(((0, 0), (-1.4, -1.4), (1.4, -1.4), (0, -3.2))):
        b = (dx, 38.6 + dy, 2.4 - k * 0.6)
        veil(m, [b, add(b, (dx * 0.6, 0.6, -3.0)), add(b, (dx, -1.6, -5.6))], 1.4, 'red', 'mane', up=(1, 0, 0),
             flat=0.35)
    g.eye_pair(m, hc, hr, 36, 14, 4.0, 3.6, style='sharp', iris=('gold', 1), slant=0.7, lid=1, rot=hrot,
               center=(0, 35.5, 15))
    p, n = g.on(sn_c, sn_r, (0, -0.35, 1))
    m.mouth(p, n, 'smile', w=3.4)
    return m


def trim(m, pts, r, mat, part):
    """A thin metal band along a polyline (straight segments)."""
    for a, b in zip(pts, pts[1:]):
        m.tube([a, b], [r, r], mat, part)


# ==========================================================================
# 103 TRINKIT  RELIC  jewellery-box mimic with teeth and a pearl necklace
# ==========================================================================
def trinkit(g):
    m = g.Model('TRINKIT')
    m.outline = (36, 14, 30)
    m.mat('wood', ['#3c1632', '#6a2850', '#9c4472', '#c86e96'])
    m.mat('gold', GOLD, spec=0.4)
    m.mat('maw', ['#2a0c20'])
    m.mat('tongue', ['#c0406a', '#f48aa6'])
    m.mat('tooth', ['#d8d0c0', '#fffff4'])
    m.mat('gem', ['#16808a', '#6ae8d8'], emissive=0.5)
    m.white = (255, 255, 244)
    m.eye_dark = (42, 12, 32)
    m.height = 33
    m.max_w = 50
    m.front_yaw = -26
    m.front_pitch = 14
    W, D, H = 6.0, 4.2, 5.4          # box half width, half depth, height
    y0 = 2.0                         # box floor (it stands on claw feet)
    # the box body with gold corner posts and rim
    m.box((0, y0 + H / 2, 0), (W, H / 2, D), 'wood', 'box', bevel=0.5)
    for sx in (-1, 1):
        for sz in (-1, 1):
            trim(m, [(sx * W, y0 + 0.2, sz * D), (sx * W, y0 + H, sz * D)], 0.55, 'gold', 'box')
    trim(m, [(-W, y0 + H, D), (W, y0 + H, D), (W, y0 + H, -D), (-W, y0 + H, -D), (-W, y0 + H, D)], 0.45,
         'gold', 'box')
    trim(m, [(-W, y0 + 0.3, D), (W, y0 + 0.3, D)], 0.45, 'gold', 'box')
    # gold ball-and-claw feet
    for sx in (-1, 1):
        for sz in (-1, 1):
            f = (sx * (W - 0.8), 1.2, sz * (D - 0.6))
            m.sph(f, 1.3, 'gold', 'foot%d' % sx)
            for t in (-1, 0, 1):
                m.tube([add(f, (0, 0.2, 0)), add(f, (t * 0.9 + sx * 0.5, -0.8, sz * 1.2))], [0.5, 0.35], 'gold',
                       'foot%d' % sx)
    # the dark maw between box and lid, teeth top and bottom
    top = y0 + H
    m.ell((0, top + 0.6, 0.2), (W - 0.9, 1.6, D - 0.6), 'maw', 'maw')
    n = 7
    for k in range(n):
        x = -W + 1.2 + (2 * W - 2.4) * k / (n - 1)
        m.crystal((x, top - 0.1, D - 0.5), (x, top + 1.3, D - 0.2), 0.55, 'tooth', 'teeth', sides=4, tip_frac=0.9)
    # the lid, hinged at the back and propped open
    hinge = (0, top + 0.2, -D)
    R = g.rot_matrix(0, -38, 0)

    def L(x, y, z):
        return add(hinge, g.mat_apply(R, (x, y, z)))
    lt = 1.5                        # lid thickness
    m.box(L(0, lt, D), (W + 0.3, lt, D + 0.3), 'wood', 'lid', rot=(0, -38, 0), bevel=0.5)
    m.ell(L(0, lt * 2, D), (W - 0.6, 1.2, D - 0.8), 'wood', 'lid', rot=(0, -38, 0))
    trim(m, [L(-W - 0.3, 0.2, 2 * D + 0.3), L(W + 0.3, 0.2, 2 * D + 0.3)], 0.5, 'gold', 'lid')
    trim(m, [L(-W - 0.3, 2 * lt, 2 * D + 0.3), L(W + 0.3, 2 * lt, 2 * D + 0.3)], 0.45, 'gold', 'lid')
    for sx in (-1, 1):
        trim(m, [L(sx * (W + 0.3), 2 * lt, 0.2), L(sx * (W + 0.3), 2 * lt, 2 * D + 0.3)], 0.45, 'gold', 'lid')
    for k in range(n - 1):
        x = -W + 1.8 + (2 * W - 3.6) * k / (n - 2)
        m.crystal(L(x, 0.3, 2 * D - 0.3), L(x, -1.1, 2 * D - 0.1), 0.55, 'tooth', 'teeth', sides=4,
                  tip_frac=0.9)
    # a teal gem set in gold filigree on the lid
    gc = L(0, 2 * lt + 1.0, D + 0.4)
    m.ell(gc, (2.0, 0.9, 1.6), 'gold', 'lid', rot=(0, -38, 0))
    m.crystal(L(0, 2 * lt + 1.0, D + 0.4), L(0, 2 * lt + 3.0, D + 0.4), 1.2, 'gem', 'lid', sides=6, tip_frac=0.5)
    # eyes on the lid front, gleaming out from under the brow
    ef = g.mat_apply(R, (0, 0, 1))
    for sx in (-1, 1):
        m.eye(L(sx * 2.7, lt, 2 * D + 0.3), ef, 3.0, 3.6, style='cute', look=-1)
    # a long tongue lolling over the front, a pearl necklace spilling out
    m.tube([(0.8, top + 0.4, 1.0), (1.2, top + 0.8, D + 1.2), (1.6, top - 1.4, D + 2.0), (1.8, top - 3.2, D + 1.6)],
           [1.4, 1.5, 1.3, 1.0], 'tongue', 'tongue', flat=0.5, up=(0, 1, 0.4))
    for k in range(9):
        t = k / 8.0
        p = (-2.8 - 2.6 * t, top + 0.8 - 5.0 * t + 2.4 * t * t, D + 0.8 + 0.8 * math.sin(t * 3))
        m.sph(p, 0.75, 'tooth', 'pearls')
    # a gold keyhole plate on the front (its chin)
    kp = (0, y0 + H * 0.45, D + 0.1)
    m.ell(kp, (1.4, 1.7, 0.5), 'gold', 'box')
    m.dot(add(kp, (0, 0.2, 0.5)), (0, 0, 1), w=0.8, h=1.3, color=('maw', 0))
    return m


# ==========================================================================
# 104 HOARDMAW  RELIC/BEAST  iron-banded treasure chest on stumpy beast legs
# ==========================================================================
def hoardmaw(g):
    m = g.Model('HOARDMAW')
    m.outline = (30, 16, 20)
    m.mat('wood', ['#50261a', '#8e4a2a', '#c8743e'])
    m.mat('fur', ['#2e1c24', '#50261a'])
    m.mat('iron', IRON[:3], spec=0.35)
    m.mat('gold', GOLD, spec=0.4)
    m.mat('maw', ['#260c16'])
    m.mat('tongue', ['#a8385a', '#ee7c98'])
    m.mat('tooth', ['#f4ecd8'])
    m.white = (244, 236, 216)
    m.eye_dark = (38, 12, 22)
    m.height = 46
    m.max_w = 60
    m.front_yaw = -34
    m.front_pitch = 8
    W, D, H = 9.0, 6.0, 8.6          # box half width, half depth, height
    y0 = 3.6                         # box floor, up on its stumpy legs
    top = y0 + H
    # short sturdy beast legs tucked under the corners, pale claws
    for sx in (-1, 1):
        for sz, nm in ((1, 'legF'), (-1, 'legB')):
            part = '%s%d' % (nm, sx)
            hip = (sx * (W - 2.2), y0 + 0.4, sz * (D - 2.0))
            paw = (sx * (W - 1.6), 1.2, sz * (D - 1.4) + 0.6)
            m.ell(hip, (2.4, 2.0, 2.4), 'fur', part)
            m.tube([hip, paw], [2.1, 1.9], 'fur', part)
            m.ell(add(paw, (0, 0, 0.6)), (2.2, 1.2, 2.4), 'fur', part)
            for t in (-1, 0, 1):
                c0 = add(paw, (t * 1.1, -0.3, 2.4))
                m.crystal(c0, add(c0, (t * 0.2, -0.8, 1.2)), 0.5, 'tooth', part, sides=4, tip_frac=0.85)
    # the chest: a plain plank box, a dark plank seam, iron rims top and bottom,
    # two iron straps wrapping front to back, iron corner brackets
    m.box((0, y0 + H / 2, 0), (W, H / 2, D), 'wood', 'box', bevel=0.4)
    m.paint((0, y0 + H * 0.5, 0), (W + 1, 0.45, D + 1), 'fur', ['box'])
    m.box((0, y0 + 0.7, 0), (W + 0.35, 0.75, D + 0.35), 'iron', 'box', bevel=0.25)
    m.box((0, top - 0.8, 0), (W + 0.35, 0.8, D + 0.35), 'iron', 'box', bevel=0.25)
    for sx in (-1, 1):
        x = sx * W * 0.52
        m.box((x, y0 + H / 2, 0), (0.8, H / 2 + 0.1, D + 0.4), 'iron', 'box', bevel=0.25)
        for sz in (-1, 1):
            for y in (y0 + 1.3, top - 1.4):
                m.box((sx * (W - 0.2), y, sz * (D - 0.2)), (0.9, 1.4, 0.9), 'iron', 'box', bevel=0.3)
    # the maw: dark inside, a heap of coins at the back, teeth all round the rim
    m.paint((0, top, 0), (W - 0.8, 0.7, D - 0.8), 'maw', ['box'])
    m.ell((0, top - 0.2, -2.6), (W - 2.6, 2.2, 2.6), 'gold', 'hoard')
    rnd = g.Rand(104)
    for k in range(7):
        c = ((rnd.f() - 0.5) * (W * 1.1), top + 1.4 + rnd.f() * 0.8, -2.6 + (rnd.f() - 0.5) * 3.0)
        m.ell(c, (1.1, 0.35, 1.1), 'gold', 'hoard', rot=(rnd.f() * 90, 20 + rnd.f() * 30, 0))
    n = 7
    for k in range(n):
        x = -W + 1.4 + (2 * W - 2.8) * k / (n - 1)
        big = k in (0, n - 1)
        m.crystal((x, top - 0.4, D - 0.5), (x, top + (2.4 if big else 1.6), D - 0.3), 0.85 if big else 0.7,
                  'tooth', 'teeth', sides=4, tip_frac=0.9)
    for sx in (-1, 1):
        for zz in (1.6, -1.4):
            m.crystal((sx * (W - 0.5), top - 0.4, zz), (sx * (W - 0.4), top + 1.4, zz), 0.65, 'tooth', 'teeth',
                      sides=4, tip_frac=0.9)
    # the lid: a flat plank lid hinged at the back and thrown open as the upper
    # jaw, iron straps and rim matching the box, teeth along its front edge
    hinge = (0, top + 0.2, -D)
    rl = (0, -30, 0)
    R = g.rot_matrix(*rl)

    def L(x, y, z):
        return add(hinge, g.mat_apply(R, (x, y, z)))
    Lh = 2.4                          # lid half thickness
    m.box(L(0, Lh, D), (W + 0.3, Lh, D + 0.3), 'wood', 'lid', rot=rl, bevel=0.5)
    m.paint(L(0, 0, D), (W - 0.7, 0.6, D - 0.7), 'maw', ['lid'], rot=rl)
    m.box(L(0, 0.7, 2 * D - 0.1), (W + 0.6, 0.8, 0.75), 'iron', 'lid', rot=rl, bevel=0.25)
    for sx in (-1, 1):
        m.box(L(sx * W * 0.52, Lh + 0.1, D), (0.8, Lh + 0.25, D + 0.5), 'iron', 'lid', rot=rl, bevel=0.25)
    for k in range(n - 1):
        x = -W + 2.0 + (2 * W - 4.0) * k / (n - 2)
        big = k in (0, n - 2)
        m.crystal(L(x, 0.3, 2 * D - 0.6), L(x, -(2.4 if big else 1.6), 2 * D - 0.3), 0.8 if big else 0.7,
                  'tooth', 'teeth', sides=4, tip_frac=0.9)
    # glaring eyes on the lid front, set in dark sockets between the straps
    ef = g.mat_apply(R, (0, 0, 1))
    for sx in (-1, 1):
        ep = L(sx * 2.9, Lh + 0.5, 2 * D + 0.4)
        m.paint(ep, (2.7, 2.1, 1.2), 'maw', ['lid'], rot=rl)
        m.eye(ep, ef, 4.4, 3.4, style='glow', iris=('gold', 2), pupil='eye', slant=-sx * 0.8)
    # a heavy gold padlock hanging off the front rim
    lk = (0, top - 3.6, D + 0.9)
    m.tube([add(lk, (-1.1, 1.3, -0.4)), add(lk, (-1.1, 2.9, -0.4)), add(lk, (1.1, 2.9, -0.4)),
            add(lk, (1.1, 1.3, -0.4))], 0.45, 'iron', 'lock')
    m.box(lk, (1.8, 1.6, 0.7), 'gold', 'lock', bevel=0.45)
    m.dot(add(lk, (0, 0.1, 0.75)), (0, 0, 1), w=0.8, h=1.4, color=('maw', 0))
    # a fat tongue lolling over the rim and coins spilling down the front
    m.tube([(4.2, top + 0.2, 1.6), (4.8, top + 0.6, D + 1.0), (5.4, top - 2.2, D + 1.9), (5.6, top - 4.8, D + 1.7)],
           [1.9, 2.0, 1.8, 1.4], 'tongue', 'tongue', flat=0.45, up=(0, 1, 0.4))
    for c, rr in (((-4.2, top + 0.2, D + 0.4), (0, -30, 0)), ((-5.4, top - 2.6, D + 1.0), (0, 60, 0)),
                  ((-4.6, y0 + 1.8, D + 1.2), (20, 70, 0)), ((-5.8, 0.4, D + 2.4), (0, 0, 0)),
                  ((-3.4, 0.4, D + 3.2), (40, 0, 0)), ((-4.4, 1.0, D + 2.6), (10, 25, 0)),
                  ((5.8, 0.4, D + 3.0), (10, 0, 0))):
        m.ell(c, (1.1, 0.35, 1.1), 'gold', 'coins', rot=rr)
    return m


def cyl(m, base, axis, rb, rt, h, mat, part, sides=12):
    """Faceted cylinder / frustum (convex hull) from base along axis."""
    ax = norm(axis)
    u = norm(cross3(ax, (0, 0, 1) if abs(ax[2]) < 0.9 else (1, 0, 0)))
    v = cross3(ax, u)
    top = add(base, mul(ax, h))
    planes = [(ax, dot3(ax, top)), (mul(ax, -1), -dot3(ax, base))]
    for k in range(sides):
        a = 2 * math.pi * (k + 0.5) / sides
        d = add(mul(u, math.cos(a)), mul(v, math.sin(a)))
        n = norm(add(mul(d, h), mul(ax, rb - rt)))
        planes.append((n, dot3(n, add(base, mul(d, rb)))))
    return m.hull(planes, lerp(base, top, 0.5), math.sqrt(max(rb, rt) ** 2 + h * h / 4) + 0.6, mat, part)


def cross3(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot3(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def disc(m, c, r, th, normal, mat, part):
    """A flat round disc (shield, lid) facing `normal`."""
    n = norm(normal)
    yaw = math.atan2(n[0], n[2]) / DEG
    pitch = -math.asin(max(-1.0, min(1.0, n[1]))) / DEG
    m.ell(c, (r, r, th), mat, part, rot=(yaw, pitch, 0))
    return (yaw, pitch, 0)


def bone(g, m, a, b, r, mat, part, knob=1.25):
    """A cartoon bone from a to b: a shaft with a double knob at each end."""
    m.tube([a, b], [r, r], mat, part)
    d = norm(sub(b, a))
    side = norm(cross3(d, (0, 0, 1) if abs(d[2]) < 0.8 else (0, 1, 0)))
    for p in (a, b):
        for s in (-1, 1):
            m.sph(add(p, mul(side, s * r * 0.8)), r * knob * 0.78, mat, part)


def ribs(m, c, r, n, mat, dark, part, gap=0.5):
    """A little ribcage: a bone barrel with n-1 dark gaps round its sides."""
    m.ell(c, r, mat, part)
    for k in range(n - 1):
        y = c[1] + r[1] * 0.6 - (1.2 * r[1]) * (k + 0.5) / (n - 1)
        m.paint((c[0], y, c[2]), (r[0] * 1.1, gap, r[2] * 1.1), dark, [part])
    m.paint((c[0], c[1], c[2] + r[2]), (r[0] * 0.18, r[1] * 1.1, 0.8), mat, [part])


# ==========================================================================
# 105 RATTLEBONE  HOLLOW  skeleton squire: saucepan helmet, lid shield, spoon
# ==========================================================================
def rattlebone(g):
    m = g.Model('RATTLEBONE')
    m.outline = (40, 28, 40)
    m.mat('bone', BONE)
    m.mat('dark', ['#2a1e30'])
    m.mat('pot', ['#5e2c1c', '#a85a34', '#e89a62'], spec=0.35)
    m.mat('cloth', ['#2a3c72', '#4a68b0'])
    m.mat('wood', ['#6a4224', '#b07c44'])
    m.mat('glow', ['#9ef0ff'], emissive=0.9)
    m.mat('steel', ['#7c86a6', BONE[3]], spec=0.4)
    m.white = rgb(BONE[3])
    m.eye_dark = (42, 30, 48)
    m.height = 39
    m.max_w = 50
    m.front_yaw = -24
    # legs: bone shins and big round bone feet, a pelvis
    for s in (-1, 1):
        part = 'leg%d' % s
        bone(g, m, (s * 1.8, 8.4, 0), (s * 2.2, 5.0, 0.2), 0.7, 'bone', part, knob=1.1)
        bone(g, m, (s * 2.2, 4.6, 0.2), (s * 2.4, 1.6, 0.2), 0.65, 'bone', part, knob=1.1)
        m.ell((s * 2.5, 0.9, 1.0), (1.5, 0.9, 2.2), 'bone', part)
    m.ell((0, 9.2, 0), (2.8, 1.4, 1.8), 'bone', 'hips')
    # spine and a small ribcage under a ragged blue tabard
    m.tube([(0, 9.6, -0.6), (0, 12.6, -0.6)], [0.7, 0.7], 'bone', 'body')
    ribs(m, (0, 13.4, 0), (2.9, 2.6, 2.2), 4, 'bone', 'dark', 'body', gap=0.45)
    for sz in (1, -1):
        z = sz * 2.3
        pts = [(-2.4, 15.4, z), (2.4, 15.4, z), (2.2, 10.6, z + sz * 0.3), (1.0, 9.8, z + sz * 0.3),
               (0.0, 10.4, z + sz * 0.3), (-1.0, 9.6, z + sz * 0.3), (-2.2, 10.4, z + sz * 0.3)]
        m.poly(pts, 'cloth', 'tabard', puff=0.25)
    # a crest on the tabard: a copper cross
    m.paint((0, 12.8, 2.6), (0.45, 1.6, 0.6), 'pot', ['tabard'])
    m.paint((0, 13.4, 2.6), (1.2, 0.45, 0.6), 'pot', ['tabard'])
    m.ell((0, 15.6, 0), (3.2, 0.9, 2.4), 'bone', 'body')           # collarbones
    # right arm raises a wooden spoon like a sword
    for s in (-1, 1):
        m.sph((s * 3.2, 15.4, 0), 1.0, 'bone', 'arm%d' % s)
    bone(g, m, (-3.4, 15.2, 0), (-5.2, 12.6, 1.6), 0.55, 'bone', 'arm-1', knob=1.0)
    bone(g, m, (-5.2, 12.6, 1.6), (-6.4, 14.6, 3.4), 0.5, 'bone', 'arm-1', knob=1.0)
    hand = (-6.6, 15.0, 3.6)
    m.sph(hand, 0.9, 'bone', 'arm-1')
    # a little sword: copper pommel, wrapped grip, wide copper crossguard,
    # a long pale blade tapering to a point
    sw = norm((-0.34, 1, 0.1))
    sd = norm((1, 0.34, 0))
    m.sph(add(hand, mul(sw, -1.7)), 0.8, 'pot', 'sword')
    m.tube([add(hand, mul(sw, -1.3)), add(hand, mul(sw, 1.1))], [0.5, 0.5], 'wood', 'sword')
    cg = add(hand, mul(sw, 1.4))
    m.tube([add(cg, mul(sd, -3.0)), add(cg, mul(sd, 3.0))], [0.6, 0.6], 'pot', 'sword')
    for s_ in (-1, 1):
        m.sph(add(cg, mul(sd, s_ * 3.1)), 0.8, 'pot', 'sword')
    b0, b1 = add(hand, mul(sw, 1.9)), add(hand, mul(sw, 8.8))
    m.tube([b0, lerp(b0, b1, 0.5), b1], [0.85, 0.8, 0.72], 'steel', 'sword', flat=0.3, up=(0, 0, 1))
    m.crystal(b1, add(hand, mul(sw, 10.8)), 0.78, 'steel', 'sword', sides=4, tip_frac=0.95)
    # left arm holds up the pot-lid shield
    bone(g, m, (3.4, 15.2, 0), (4.6, 12.4, 1.8), 0.55, 'bone', 'arm1', knob=1.0)
    sc = (5.0, 12.2, 3.6)
    rr = disc(m, sc, 3.1, 0.6, (0.35, 0.1, 1), 'pot', 'shield')
    m.paint(sc, (2.2, 2.2, 1.0), 'pot', ['shield'], rot=rr)
    m.ell(add(sc, (0.3, 0.1, 0.9)), (1.0, 0.8, 0.7), 'bone', 'shield', rot=rr)
    ring = [add(sc, g.mat_apply(g.rot_matrix(*rr), (math.cos(a * DEG) * 2.9, math.sin(a * DEG) * 2.9, 0.3)))
            for a in range(0, 361, 30)]
    m.tube(ring, 0.4, 'pot', 'shield')
    # big round skull, a separate grinning jaw
    hc, hr = (0, 20.4, 0.6), (5.2, 4.7, 4.7)
    m.ell(hc, hr, 'bone', 'head')
    m.ell((0, 17.0, 1.8), (3.0, 1.5, 2.6), 'bone', 'jaw')
    m.tube([(0, 16.6, -0.4), (0, 15.6, -0.6)], 0.8, 'bone', 'body')   # neck
    for sx in (-1, 1):
        p, n = g.on(hc, hr, sdir(sx * 26, -4))
        m.paint(p, (2.0, 2.1, 1.4), 'dark', ['head'])
        m.dot(p, n, w=1.0, h=1.4, color=('glow', 0), minw=1, minh=2)
    p, n = g.on(hc, hr, sdir(0, -24))
    m.dot(p, n, w=1.0, h=1.0, color=('dark', 0))
    p, n = g.on((0, 17.0, 1.8), (3.0, 1.5, 2.6), (0, 0.1, 1))
    m.mouth(p, n, 'teeth', w=3.4, h=1.4)
    # the saucepan helmet, a bit too big and askew, handle sticking out back
    rr = (0, -6, -14)
    R = g.rot_matrix(*rr)
    pb = (0.4, 23.2, 0.0)
    ax = g.mat_apply(R, (0, 1, 0))
    cyl(m, pb, ax, 4.3, 4.2, 4.4, 'pot', 'helm')
    ring = [add(pb, g.mat_apply(R, (math.cos(a * DEG) * 4.5, 4.3, math.sin(a * DEG) * 4.5))) for a in range(0, 361, 24)]
    m.tube(ring, 0.55, 'pot', 'helm')
    # the long saucepan handle sticking out over one ear
    hb = add(pb, g.mat_apply(R, (4.4, 2.0, -0.6)))
    he = add(pb, g.mat_apply(R, (10.0, 2.6, -1.2)))
    m.tube([hb, he], [0.75, 0.75], 'wood', 'helm')
    m.sph(he, 0.95, 'wood', 'helm')
    m.paint(add(pb, g.mat_apply(R, (0, 1.8, 4.4))), (1.6, 0.5, 1.0), 'pot', ['helm'])
    return m


# ==========================================================================
# 106 OSSIGUARD  HOLLOW/METAL  rusted skeleton knight in a kettle hat
# ==========================================================================
def ossiguard(g):
    m = g.Model('OSSIGUARD')
    m.outline = (32, 24, 34)
    m.mat('bone', BONE[1:])
    m.mat('dark', ['#221a2a'])
    m.mat('iron', IRON[:3], spec=0.3)
    m.mat('rust', RUST)
    m.mat('cloth', ['#243466', '#44609e'])
    m.mat('soul', ['#56c4e4', '#d0fcff'], emissive=0.9)
    m.white = rgb(BONE[3])
    m.eye_dark = (34, 26, 42)
    m.height = 56
    m.max_w = 60
    m.front_yaw = -24
    # tattered surcoat cape behind
    cape = [(-5.2, 27.0, -3.2), (5.2, 27.0, -3.2), (6.4, 9.0, -5.6), (4.4, 7.4, -5.6), (3.0, 9.6, -5.4),
            (1.0, 6.8, -5.8), (-1.2, 9.2, -5.4), (-3.2, 7.0, -5.6), (-4.6, 9.8, -5.4), (-6.4, 8.2, -5.6)]
    m.poly(cape, 'cloth', 'cape', puff=0.3)
    # legs: bone thighs, rusty knee cops, iron greaves and sabatons
    for s in (-1, 1):
        part = 'leg%d' % s
        bone(g, m, (s * 2.4, 15.6, 0), (s * 2.8, 10.4, 0.6), 0.9, 'bone', part, knob=1.0)
        m.sph((s * 2.8, 10.0, 0.9), 1.6, 'rust', part)
        m.tube([(s * 2.9, 9.0, 0.6), (s * 3.0, 2.6, 0.4)], [1.7, 1.4], 'iron', part)
        m.ell((s * 3.1, 1.3, 1.6), (1.9, 1.3, 3.2), 'iron', part)
    # faulds (plated skirt) and the ragged blue surcoat front
    m.ell((0, 16.8, 0.2), (5.0, 2.6, 3.6), 'iron', 'hips')
    m.paint((0, 15.0, 0.2), (6, 0.5, 5), 'dark', ['hips'])
    tab = [(-3.2, 18.0, 3.4), (3.2, 18.0, 3.4), (3.0, 10.2, 3.6), (1.6, 11.4, 3.6), (0.4, 9.6, 3.7),
           (-0.8, 11.0, 3.6), (-2.2, 9.8, 3.6), (-3.0, 11.2, 3.5)]
    m.poly(tab, 'cloth', 'surcoat', puff=0.25)
    m.paint((0, 13.4, 3.8), (0.5, 2.0, 0.8), 'rust', ['surcoat'])
    m.paint((0, 14.2, 3.8), (1.5, 0.5, 0.8), 'rust', ['surcoat'])
    # a clean breastplate over the ribs; a hole rusted through where the
    # heart was, a pale soul-flame burning in it
    bc, br = (0, 22.6, 0.2), (5.4, 5.2, 3.8)
    m.ell(bc, br, 'iron', 'chest')
    m.paint((0, 22.6, 4.0), (0.35, 4.4, 0.8), 'iron', ['chest'])
    hole = (1.6, 22.8, 3.4)
    m.paint(hole, (1.9, 2.1, 1.4), 'dark', ['chest'])
    m.sph(add(hole, (0, -0.2, 0.2)), 1.1, 'soul', 'soul')
    g.flame(m, add(hole, (0, 0.2, 0.6)), 3.4, 1.2, 'soul', mats=('soul', 'soul'), up=(0, 1, 0.1),
            face=(0.3, 0, 1), tongues=2, core=False, seed=6)
    # big layered plain-iron pauldrons, bone upper arms, iron gauntlets
    for s in (-1, 1):
        part = 'arm%d' % s
        for k in range(3):
            m.ell((s * (5.8 + k * 0.3), 26.6 - k * 1.5, 0), (3.4 - k * 0.3, 1.7, 3.4 - k * 0.3), 'iron', part,
                  rot=(0, 0, s * 22))
    # its left arm (+X) carries a kite shield with the squire's copper cross
    bone(g, m, (6.6, 24.0, 0), (7.4, 18.6, 1.4), 0.8, 'bone', 'arm1', knob=1.0)
    m.tube([(7.4, 18.4, 1.4), (7.2, 15.6, 3.4)], [1.5, 1.4], 'iron', 'arm1')
    shc = (7.6, 15.6, 4.8)
    sh = [(0, 5.4), (3.6, 4.4), (3.6, 0.4), (0, -6.0), (-3.6, 0.4), (-3.6, 4.4)]
    sn = norm((0.3, 0.05, 1))
    su = norm(cross3((0, 1, 0), sn))
    m.poly([add(shc, add(mul(su, x), (0, y, 0))) for x, y in sh], 'iron', 'shield', puff=0.5)
    m.paint(add(shc, (0, 0.6, 0.4)), (0.7, 4.2, 1.4), 'rust', ['shield'])
    m.paint(add(shc, (0, 2.0, 0.4)), (2.8, 0.7, 1.4), 'rust', ['shield'])
    rim = [add(shc, add(mul(su, x * 1.02), (0, y * 1.02, 0))) for x, y in sh + sh[:1]]
    m.tube(rim, 0.45, 'rust', 'shield')
    # its right arm rests on a notched rusty broadsword planted by its side
    bone(g, m, (-6.6, 24.0, 0), (-7.8, 18.8, 1.0), 0.8, 'bone', 'arm-1', knob=1.0)
    m.tube([(-7.8, 18.6, 1.0), (-9.4, 15.8, 2.4)], [1.5, 1.4], 'iron', 'arm-1')
    hand = (-10.0, 15.4, 3.0)
    m.sph(hand, 1.5, 'iron', 'arm-1')
    m.tube([add(hand, (0, 1.6, 0)), add(hand, (0, -1.8, 0))], [0.6, 0.6], 'rust', 'sword')
    m.sph(add(hand, (0, 2.2, 0)), 0.9, 'rust', 'sword')
    m.box(add(hand, (0, -2.4, 0)), (2.8, 0.55, 0.8), 'rust', 'sword', bevel=0.2)
    m.box(add(hand, (0, -8.0, 0)), (1.2, 5.2, 0.4), 'iron', 'sword', bevel=0.2)
    m.crystal(add(hand, (0, -12.8, 0)), add(hand, (0, -14.4, 0)), 1.0, 'iron', 'sword', sides=4, tip_frac=0.9,
              twist=45)
    m.paint(add(hand, (0, -8.0, 0.4)), (0.3, 4.6, 0.6), 'dark', ['sword'])
    for p in ((0.9, -6.0), (-0.9, -9.4)):
        m.paint(add(hand, (p[0] * 1.4, p[1], 0)), (0.6, 0.8, 0.8), 'rust', ['sword'])
    # neck, skull under the brim, sockets with pale soul-light
    m.tube([(0, 27.4, -0.4), (0, 29.2, -0.2)], 1.1, 'bone', 'head')
    hc, hr = (0, 32.2, 0.8), (4.0, 3.9, 3.9)
    m.ell(hc, hr, 'bone', 'head')
    m.ell((0, 29.4, 2.0), (2.6, 1.3, 2.4), 'bone', 'jaw')
    for sx in (-1, 1):
        p, n = g.on(hc, hr, sdir(sx * 26, -2))
        m.paint(p, (1.7, 1.6, 1.3), 'dark', ['head'])
        m.dot(p, n, w=1.0, h=1.5, color=('soul', 1), minw=1, minh=2)
    p, n = g.on(hc, hr, sdir(0, -24))
    m.dot(p, n, w=1.0, h=1.0, color=('dark', 0))
    p, n = g.on((0, 29.4, 2.0), (2.6, 1.3, 2.4), (0, 0.1, 1))
    m.mouth(p, n, 'teeth', w=3.0, h=1.4)
    # the kettle hat: the squire's saucepan grown into a rusty brimmed helm
    rr = (0, -4, -8)
    R = g.rot_matrix(*rr)
    kc = (0.2, 34.2, 0.4)
    m.ell(add(kc, g.mat_apply(R, (0, 0.6, 0))), (4.6, 3.6, 4.6), 'iron', 'helm', rot=rr)
    m.ell(kc, (6.6, 0.7, 6.4), 'iron', 'helm', rot=rr)
    m.tube([add(kc, g.mat_apply(R, (math.cos(a * DEG) * 6.4, 0, math.sin(a * DEG) * 6.2))) for a in range(0, 361, 20)],
           0.45, 'rust', 'helm')
    m.tube([add(kc, g.mat_apply(R, (math.cos(a * DEG) * 4.6, 0.9, math.sin(a * DEG) * 4.6))) for a in range(0, 361, 24)],
           0.5, 'rust', 'helm')
    m.tube([add(kc, g.mat_apply(R, (0, 3.6, -3.4))), add(kc, g.mat_apply(R, (0, 4.6, 0))),
            add(kc, g.mat_apply(R, (0, 3.6, 3.4)))], 0.55, 'iron', 'helm')
    m.paint(add(kc, g.mat_apply(R, (-2.6, 2.6, 2.0))), 1.2, 'rust', ['helm'])
    # a tattered blue plume
    pb = add(kc, g.mat_apply(R, (0, 4.2, -1.0)))
    for k, d in enumerate(((0.3, 1.0, -0.8), (-0.5, 0.8, -1.0), (0.9, 0.7, -1.0))):
        dd = norm(d)
        m.tube([pb, add(pb, mul(dd, 3.0)), add(add(pb, mul(dd, 5.4)), (0, -1.4, -1.0))], [1.0, 0.9, 0.2], 'cloth',
               'plume', flat=0.5, up=(1, 0, 0))
    return m


# ---- end of batch ----
