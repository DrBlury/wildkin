"""Art for kin 113-120 (KIN-R3): the eight lone rares out of folklore.

One model function per species (the lowercase species name), called by
tools/gen_monsters.py as fn(g) with g = the gen_monsters module. Coordinates:
+Y up, +Z the way the kin faces, +X its left (the side nearer the camera in
the 3/4 front view); the ground is y = 0, roughly 1 unit = 1 px on the front
sprite.

Every rare carries one glowing accent (emissive material) so it reads as
something special next to the common kin.
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
    """Overworld side view yaw (winged kin turn a little toward the camera)."""
    g.OW_SIDE_YAW[m.name] = yaw


def paint_path(m, pts, r, mat, parts, steps=6):
    """A painted line (stripe, crack, script stroke) through pts."""
    if isinstance(r, (int, float)):
        r = (r, r, r)
    for i in range(len(pts) - 1):
        for k in range(steps + 1):
            m.paint(lerp(pts[i], pts[i + 1], k / float(steps)), r, mat, parts)


def ribbon(m, pts, w, mat, part, side=(1, 0, 0), mats=None):
    """A flat strip (kelp frond, smoke wisp, tassel) whose flat face points along side."""
    m.tube(pts, None, mat, part, flat=0.32, up=side, mats=mats,
           rfn=lambda t: w * (0.55 + 0.45 * math.sin(math.pi * min(1.0, 0.2 + t))) + 0.12)


def frustum(m, base, rb, rt, h, sides, mat, part):
    """Faceted vertical frustum (convex hull) standing on base: a robe, a pedestal."""
    x0, y0, z0 = base
    planes = [((0.0, 1.0, 0.0), y0 + h), ((0.0, -1.0, 0.0), -y0)]
    for k in range(sides):
        a = 2 * math.pi * (k + 0.5) / sides
        n = norm((math.cos(a) * h, rb - rt, math.sin(a) * h))
        p = (x0 + math.cos(a) * rb, y0, z0 + math.sin(a) * rb)
        planes.append((n, dot(n, p)))
    c = (x0, y0 + h / 2.0, z0)
    return m.hull(planes, c, math.sqrt(max(rb, rt) ** 2 + (h / 2.0) ** 2) + 0.6, mat, part)


def star(m, c, n, s, mat, part):
    """A small 4-point star (two crossed thin crystals) facing n."""
    n = norm(n)
    u = norm(cross(n, (0, 1, 0) if abs(n[1]) < 0.9 else (1, 0, 0)))
    v = cross(n, u)
    for d in (u, v):
        m.tube([add(c, mul(d, -s)), c, add(c, mul(d, s))], [0.3, s * 0.42, 0.3], mat, part)


# ==========================================================================
# 113 KELPYRE  TIDE/DUSK  kelp-maned water horse (kelpie)
# ==========================================================================
def kelpyre(g):
    m = g.Model('KELPYRE')
    m.outline = (8, 18, 28)
    m.mat('hide', ['#0c2634', '#17485a', '#2a7e80', '#62c2ac'], th=[0.22, 0.5, 0.9])
    m.mat('belly', ['#3e9a92', '#9ee0c8'])
    m.mat('kelp', ['#24340c', '#4c7420', '#94ba3a'])
    m.mat('dusk', ['#0a1222', '#24304e'])
    m.mat('glow', ['#3ae6c4', '#d8fff2'], emissive=0.9)
    m.eye_dark = (10, 18, 34)
    m.white = (216, 255, 242)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -36
    # barrel body and deep chest, pale sea-foam underside
    m.ell((0, 21.0, -1.5), (6.0, 6.6, 11.6), 'hide', 'body')
    m.ell((0, 22.4, 6.4), (6.0, 7.2, 5.8), 'hide', 'body')
    m.paint((0, 14.6, 0.6), (5.0, 3.4, 10.4), 'belly', ['body'])
    # dusky saddle down the spine
    m.paint((0, 27.6, -3.0), (4.4, 2.2, 10.0), 'dusk', ['body'])

    def fin(base, part, s):
        # a translucent fin frill trailing back from a fetlock
        for (dy, ln, w) in ((1.2, 7.4, 2.4), (-0.6, 5.6, 1.9)):
            b = add(base, (0, dy, 0))
            tip = add(b, (s * ln * 0.62, 1.0 + dy * 1.4, -ln * 0.78))
            g.leaf(m, b, add(lerp(b, tip, 0.5), (0, 0.6, 0)), tip, w, 'belly', part,
                   up=norm((0.8, 0, 0.6)), flat=0.3, mats=[(0, 'belly'), (0.6, 'glow')])
    # legs: the near foreleg raised and curled, dark hooves, fin frills at the fetlocks
    for s in (-1, 1):
        if s > 0:
            m.tube([(s * 3.6, 18.0, 8.4), (s * 4.0, 14.6, 13.4), (s * 4.0, 11.0, 12.8)],
                   [2.7, 1.9, 1.7], 'hide', 'legF%d' % s)
            m.ell((s * 4.0, 9.6, 12.0), (2.1, 1.6, 2.3), 'dusk', 'legF%d' % s, rot=(-40, 0, 0))
            fin((s * 4.1, 11.8, 12.4), 'legF%d' % s, s)
        else:
            m.tube([(s * 3.6, 18.0, 8.4), (s * 3.8, 10.0, 9.0), (s * 3.8, 3.2, 9.2)],
                   [2.7, 1.8, 1.7], 'hide', 'legF%d' % s)
            m.ell((s * 3.8, 1.5, 9.6), (2.1, 1.5, 2.3), 'dusk', 'legF%d' % s)
            fin((s * 4.0, 4.4, 9.0), 'legF%d' % s, s)
        m.ell((s * 4.0, 19.5, -8.5), (3.4, 5.6, 4.8), 'hide', 'legB%d' % s)
        m.tube([(s * 4.2, 15.0, -10.4), (s * 4.3, 8.4, -12.0), (s * 4.0, 3.2, -10.4)],
               [2.4, 1.8, 1.7], 'hide', 'legB%d' % s)
        m.ell((s * 4.0, 1.5, -10.0), (2.1, 1.5, 2.3), 'dusk', 'legB%d' % s)
        fin((s * 4.2, 4.4, -10.8), 'legB%d' % s, s)
    # tail: a fish tail sweeping back and up, kelp fronds hanging off it
    tail = [(0, 24.0, -12.0), (0, 22.0, -15.6), (0.6, 18.4, -18.0), (1.4, 16.8, -21.0)]
    m.tube(tail, [2.2, 1.8, 1.4, 1.0], 'hide', 'tail')
    for sgn in (-1, 1):
        b = tail[-1]
        tip = add(b, (0.4, sgn * 5.4 + 1.0, -4.6))
        g.leaf(m, b, lerp(b, tip, 0.5), tip, 2.4, 'belly', 'tail', up=(1, 0, 0.1), flat=0.3,
               mats=[(0, 'belly'), (0.6, 'glow')])
    for k, (dx, ln) in enumerate(((1.6, 1.0), (-1.4, 0.8), (0.2, 0.9))):
        b = tail[1 + (k % 2)]
        pts = [b, add(b, (dx, -3.0 * ln, -1.2)), add(b, (dx * 1.3, -7.0 * ln, 0.2)),
               add(b, (dx * 1.1, -11.0 * ln, -0.8))]
        ribbon(m, pts, 1.3, 'kelp', 'tail', side=(1, 0, 0.2))
    # neck arched, head turned toward the viewer
    m.tube([(0, 24.0, 7.4), (0.4, 30.5, 11.4), (1.0, 36.0, 13.6)], [4.6, 3.8, 3.2], 'hide', 'neck')
    head_c, head_r = (1.2, 38.4, 15.2), (3.6, 3.7, 4.2)
    m.ell(head_c, head_r, 'hide', 'head')
    m.tube([(1.4, 37.6, 17.2), (2.0, 35.8, 20.8), (2.4, 34.6, 23.0)], [3.1, 2.6, 2.3], 'hide', 'head')
    m.paint((2.6, 34.2, 23.4), (2.4, 1.8, 1.4), 'dusk', ['head'])
    m.paint((2.0, 34.0, 20.4), (2.2, 1.4, 3.0), 'belly', ['head'])
    for s in (-1, 1):
        m.tube([(1.2 + s * 1.9, 41.0, 14.0), (1.2 + s * 2.7, 43.4, 13.2), (1.2 + s * 3.2, 45.6, 12.6)],
               [1.3, 0.95, 0.25], 'hide', 'ear%d' % s, flat=0.5, up=(0, 0, 1))
        m.dot((2.4 + s * 1.1, 35.0, 24.3), (s * 0.3 + 0.15, 0.2, 1), w=1.0, h=1.0, color=('dusk', 0))
    # glowing eyes, each on a dark dot so the glow shows on the lit hide
    for s in (-1, 1):
        a = (s * 44 + 9) * DEG
        p, n = g.on(head_c, head_r, (math.sin(a) * 0.95, 0.22, math.cos(a) * 0.95))
        m.dot(p, n, w=3.6, h=3.0, color=('dusk', 0), minw=3, minh=3)
        m.eye(p, n, 2.6, 2.2, style='glow', iris=('glow', 0), slant=0.7, center=(1.5, 38, 24),
              minw=2, minh=2)
    m.mouth((2.2, 33.8, 22.4), (0.15, -0.3, 1), 'line', w=2.4)
    # the kelp mane: many long ribbon strands streaming back over both sides of
    # the neck and shoulders, some ending in glowing float bladders
    crest = [(1.1, 42.6, 13.8), (0.9, 41.0, 12.0), (0.7, 38.6, 10.6), (0.5, 36.0, 9.0),
             (0.3, 33.2, 7.4), (0.1, 30.4, 5.4), (0, 27.8, 3.2), (0, 26.2, 0.6)]
    for k, q in enumerate(crest):
        for s in (1, -1):
            ln = 1.0 + (0.22 if (k + (s > 0)) % 2 else 0.0)
            w = 0.6 * math.sin(k * 1.7 + s)
            pts = [q, add(q, (s * 3.0, 1.0, -2.0)), add(q, (s * (5.0 + w), -2.4 * ln, -4.8)),
                   add(q, (s * (5.6 - w), -6.0 * ln, -6.4)), add(q, (s * (6.2 + w), -9.8 * ln, -7.8)),
                   add(q, (s * (5.8 - w), -13.0 * ln, -9.8))]
            ribbon(m, pts, 1.45, 'kelp', 'mane', side=(1, 0.3, 0.2))
            if s > 0 and k % 2 == 0:
                m.sph(add(pts[-1], (0.2, -1.0, -0.2)), 1.25, 'glow', 'mane')
    # forelock down the face between the eyes
    ribbon(m, [(1.1, 42.6, 14.6), (1.3, 43.0, 16.8), (1.6, 41.6, 18.6), (1.8, 40.0, 19.2)], 0.9,
           'kelp', 'mane', side=(0, 1, 0.5))
    return m


# ==========================================================================
# 114 TENGALE  GALE/BRAWL  red-faced, long-nosed tengu with a feather fan
# ==========================================================================
def tengale(g):
    m = g.Model('TENGALE')
    m.outline = (30, 16, 24)
    m.mat('skin', ['#861a1c', '#c43228', '#ee6a4a'])
    m.mat('robe', ['#5a6cae', '#9cb2e6', '#eef4ff'])
    m.mat('wing', ['#16182a', '#2e3452', '#5a6490'])
    m.mat('fan', ['#6a4a18', '#b88a34', '#f0d27a'])
    m.mat('wind', ['#9ae8ff', '#f0ffff'], emissive=0.8)
    m.eye_dark = (22, 24, 42)
    m.white = (240, 255, 255)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -22
    m.back_min_vis = 36
    # one-toothed geta under dark leggings
    for s in (-1, 1):
        m.tube([(s * 2.8, 11.0, 0.0), (s * 3.0, 6.0, 0.6), (s * 3.0, 3.4, 0.8)], [2.0, 1.5, 1.4],
               'wing', 'leg%d' % s)
        m.box((s * 3.0, 2.1, 1.4), (1.6, 0.5, 3.0), 'fan', 'leg%d' % s, bevel=0.2)
        m.box((s * 3.0, 0.8, 1.4), (1.2, 0.8, 0.5), 'fan', 'leg%d' % s, bevel=0.1)
    # dark baggy hakama, pale robe and a gold sash
    m.ell((0, 13.4, 0.0), (6.2, 5.4, 4.6), 'wing', 'body')
    m.ell((0, 22.6, 0.2), (5.8, 6.6, 4.4), 'robe', 'body')
    m.ell((0, 17.8, 0.0), (6.0, 1.5, 4.6), 'fan', 'body')
    paint_path(m, [(-4.0, 27.6, 3.4), (-0.6, 23.0, 4.6), (0.6, 19.6, 4.6)], 0.9, 'robe', ['body'])
    # yamabushi pom-poms on the chest
    for (x, y) in ((-2.4, 25.0), (2.4, 25.0)):
        m.sph((x, y, 4.2), 1.5, 'fan', 'body')
    # great dark wings, spread wide, with pale tips
    for s in (-1, 1):
        root = (s * 3.4, 28.0, -3.6)
        for k, (ang, ln, w) in enumerate(((78, 17.0, 2.6), (58, 19.0, 2.8), (38, 18.0, 2.7),
                                          (18, 15.0, 2.5), (-2, 11.5, 2.2))):
            a = ang * DEG
            d = norm((s * math.cos(a), math.sin(a), -0.45))
            tip = add(root, mul(d, ln))
            g.leaf(m, root, lerp(root, tip, 0.55), tip, w, 'wing', 'wing%d' % s,
                   up=(0, 0.1, 1), flat=0.3, mats=[(0, 'wing'), (0.82, 'robe')])
    side_yaw(g, m, -64)
    # arms: the near hand holds the fan out, the far one a fist on the hip
    m.tube([(5.0, 27.0, 0.4), (9.4, 24.4, 2.4), (12.0, 26.4, 4.4)], [2.3, 2.0, 1.8], 'robe',
           'arm1')
    m.sph((12.6, 27.0, 4.8), 1.9, 'skin', 'arm1')
    m.tube([(-5.0, 27.0, 0.4), (-8.0, 22.0, 1.0), (-5.6, 19.0, 2.6)], [2.3, 2.0, 1.8], 'robe',
           'arm-1')
    m.sph((-5.0, 18.8, 3.0), 1.9, 'skin', 'arm-1')
    # hauchiwa: a fan of feathers on a handle, with a gust curling off it
    fc = (13.8, 33.2, 5.6)
    m.tube([(12.6, 25.6, 4.8), (13.2, 29.4, 5.2), fc], [0.8, 0.8, 1.0], 'fan', 'fan')
    fn = norm((0.2, 0.1, 1.0))
    fu = norm(cross((0, 1, 0), fn))
    for k in range(7):
        a = (-72 + 144.0 * k / 6) * DEG
        d = norm(add(mul(fu, math.sin(a)), (0, math.cos(a), 0)))
        tip = add(fc, mul(d, 7.0 - abs(k - 3) * 0.45))
        g.leaf(m, fc, lerp(fc, tip, 0.5), tip, 1.7, 'fan', 'fan', up=fn, flat=0.3)
    m.sph(fc, 1.2, 'skin', 'fan')
    for (b, r) in ((((16.6, 38.6, 4.0), (19.0, 41.6, 2.6), (20.6, 40.0, 1.0)), 0.7),
                   (((15.0, 42.6, 4.6), (17.0, 45.8, 3.6), (19.0, 45.4, 2.6)), 0.6)):
        m.tube(list(b), [r, r, 0.2], 'wind', 'gust')
    # head: red face, very long nose, wild white hair behind, a black tokin cap
    head_c, head_r = (0, 36.0, 1.0), (5.2, 5.0, 4.8)
    m.tube([(0, 29.0, 0.4), (0, 32.0, 0.8)], [2.8, 2.8], 'skin', 'head')
    m.ell(head_c, head_r, 'skin', 'head')
    m.tube([(0, 35.4, 5.0), (-0.8, 35.4, 9.0), (-1.8, 35.8, 13.6)], [1.9, 1.5, 1.1], 'skin', 'head')
    m.sph((-1.9, 35.9, 13.8), 1.2, 'skin', 'head')
    for k in range(9):
        a = (-130 + 260.0 * k / 8) * DEG
        q = (math.sin(a) * 5.0, 37.6 + 1.2 * math.cos(a * 0.6), -2.4 - 1.8 * math.cos(a))
        m.sph(q, 2.4 + 0.3 * (k % 2), 'robe', 'hair')
    for s in (-1, 1):
        m.tube([(s * 4.4, 35.6, -1.6), (s * 6.8, 32.8, -3.0), (s * 7.4, 29.6, -3.6)],
               [2.2, 1.7, 0.4], 'robe', 'hair')
        m.tube([(s * 3.6, 32.0, 3.2), (s * 4.0, 29.4, 4.0), (s * 3.2, 27.8, 4.0)], [1.4, 1.1, 0.3],
               'robe', 'hair')
    m.box((0, 42.0, 1.6), (1.5, 1.3, 1.5), 'wing', 'cap', bevel=0.4)
    m.ell((0, 41.0, 2.0), (2.2, 0.9, 2.0), 'wing', 'cap')
    # fierce brows over sharp golden eyes, a scowl under the nose
    g.eye_pair(m, head_c, head_r, 30, 14, 3.6, 3.4, style='sharp', iris=('fan', 2), slant=1.0,
               center=(0, 36, 12), turn=5)
    for s in (-1, 1):
        a = (s * 30 + 5) * DEG
        p, n = g.on(head_c, head_r, (math.sin(a) * 0.8, 0.62, math.cos(a) * 0.8))
        m.dot(p, n, w=3.6, h=1.2, color='outline', minw=3, minh=1)
    m.mouth((0.4, 32.6, 5.0), (0, -0.2, 1), 'line', w=2.8)
    return m


# ==========================================================================
# 115 SLUMBAKU  DREAM/BEAST  night-blue and cream tapir that eats nightmares
# ==========================================================================
def slumbaku(g):
    m = g.Model('SLUMBAKU')
    m.outline = (16, 16, 40)
    m.mat('night', ['#141a3e', '#27316c', '#3e4d9c', '#6a7ccc'], th=[0.2, 0.46, 0.78])
    m.mat('cream', ['#b6a482', '#e6d8b2', '#fff8e6'])
    m.mat('dream', ['#c65aa2', '#f39cd2', '#ffe4f6'], emissive=0.3)
    m.mat('moon', ['#e8b640', '#fff0a0'], emissive=0.6)
    m.eye_dark = (20, 26, 62)
    m.white = (255, 248, 230)
    m.height = 44
    m.max_w = 62
    m.front_yaw = -52
    # round body: night-blue front, head and legs, a cream saddle round the middle
    body_c, body_r = (0, 14.0, -1.0), (7.4, 7.6, 11.6)
    m.ell(body_c, body_r, 'night', 'body')
    m.paint((0, 14.6, -3.6), (8.4, 8.8, 4.8), 'cream', ['body'])
    # stubby legs with cream toes
    for s in (-1, 1):
        for (nm, z) in (('legF', 6.6), ('legB', -8.4)):
            part = '%s%d' % (nm, s)
            m.tube([(s * 4.4, 9.0, z), (s * 4.6, 4.0, z + 0.4), (s * 4.6, 2.0, z + 0.6)],
                   [3.0, 2.7, 2.7], 'night', part)
            for t in (-1, 0, 1):
                m.sph((s * 4.6 + t * 1.1, 1.0, z + 2.6), 0.9, 'cream', part)
    m.tube([(0, 16.0, -12.4), (0.6, 15.0, -14.0), (1.0, 13.2, -14.4)], [1.4, 1.0, 0.6], 'night',
           'tail')
    # big head turned a little toward us, the trunk drooping and curling up at the tip
    head_c, head_r = (1.0, 17.8, 11.0), (6.0, 5.8, 6.0)
    m.ell(head_c, head_r, 'night', 'head')
    m.tube([(1.4, 16.4, 15.6), (1.8, 14.4, 19.2), (2.2, 11.6, 21.0), (2.8, 9.4, 20.8),
            (3.4, 9.2, 19.0)], [3.0, 2.5, 2.0, 1.6, 1.3], 'night', 'head')
    for s in (-1, 1):
        m.ell((1.0 + s * 4.6, 23.2, 8.6), (2.0, 2.8, 1.2), 'night', 'ear%d' % s, rot=(0, 0, -s * 22))
        m.paint((1.0 + s * 5.2, 25.2, 8.8), (1.5, 1.3, 1.6), 'cream', ['ear%d' % s])
    # crescent moon on the brow
    p, n = g.on(head_c, head_r, (0.15, 0.66, 0.74))
    m.paint(p, (2.2, 2.2, 1.4), 'moon', ['head'])
    m.paint(add(p, (1.0, 0.8, 0.3)), (1.8, 1.8, 1.8), 'night', ['head'])
    # sleepy half-closed eyes: a pale eye with a dark pupil sunk to the bottom,
    # the night-blue lid drooping over its top half, a dark arc along the lid edge
    for s in (-1, 1):
        a = (s * 40 + 16) * DEG
        e = 8 * DEG
        p, n = g.on(head_c, head_r, (math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e)))
        up = (0, 1.0, 0)
        m.eye(p, n, 5.0, 4.2, style='solid', iris=('cream', 2), minw=3, minh=3)
        m.dot(add(p, mul(up, -0.9)), n, w=2.2, h=1.8, color='eye', minw=2, minh=1)
        m.dot(add(p, mul(up, 1.4)), n, w=5.4, h=2.2, color=('night', 2), minw=4, minh=1)
        m.dot(add(p, mul(up, 0.2)), n, w=4.6, h=1.0, color='outline', minw=3, minh=1)
        for t in (-1, 1):
            m.dot(add(p, (t * math.cos(a) * 2.5, -0.7, -t * math.sin(a) * 2.5)), n, w=1.0, h=1.0,
                  color='outline')
    # dream bubbles rising from the trunk, each holding a twinkle
    for k, (c, r) in enumerate((((1.0, 22.4, 22.6), 2.6), ((0.0, 28.6, 21.2), 2.0),
                                 ((-0.6, 33.6, 18.4), 1.5))):
        m.sph(c, r, 'dream', 'bubble%d' % k)
        m.dot(add(c, (0.5 * r, 0.5 * r, 0.6 * r)), (0.4, 0.5, 1), w=1.0, h=1.0, color='white')
    # twinkles on the cream saddle
    for (x, y, z) in ((6.6, 17.6, -2.0), (5.4, 20.4, -5.4), (7.2, 13.0, -5.0)):
        m.paint((x, y, z), 1.0, 'moon', ['body'])
    return m


# ==========================================================================
# 116 WENDIGAUNT  FROST/HOLLOW  gaunt stalker with a frosted deer-skull head
# ==========================================================================
def wendigaunt(g):
    m = g.Model('WENDIGAUNT')
    m.outline = (14, 14, 24)
    m.mat('fur', ['#17151f', '#2c2838', '#484258', '#6e6682'], th=[0.2, 0.46, 0.78])
    m.mat('bone', ['#a8a496', '#dcd8c8', '#fbfaf2'])
    m.mat('frost', ['#8cc0e2', '#e6f8ff'])
    m.mat('ice', ['#3cc0f4', '#d4faff'], emissive=0.9)
    m.eye_dark = (23, 21, 31)
    m.white = (230, 248, 255)
    m.height = 62
    m.max_w = 62
    m.front_yaw = -20
    m.back_min_vis = 38
    side_yaw(g, m, -42)
    # long deer legs bent backward, ending in pale hooves
    for s in (-1, 1):
        part = 'leg%d' % s
        m.tube([(s * 2.8, 21.0, -1.0), (s * 3.4, 15.0, 2.2), (s * 3.6, 8.4, -1.8),
                (s * 3.6, 2.4, 0.0)], [2.5, 1.6, 1.2, 1.1], 'fur', part)
        m.ell((s * 3.6, 1.2, 0.6), (1.5, 1.2, 1.9), 'bone', part)
    # starved torso hunched forward, the ribs showing through
    m.ell((0, 22.0, -1.2), (4.2, 3.2, 3.0), 'fur', 'body')
    m.ell((0, 29.6, 0.6), (5.0, 7.4, 3.6), 'fur', 'body', rot=(18, 0, 0))
    for k in range(3):
        y = 32.6 - 3.0 * k
        z = 4.4 - 0.7 * k
        paint_path(m, [(-3.8, y + 0.6, z - 1.6), (-1.4, y - 0.4, z), (1.4, y - 0.4, z),
                       (3.8, y + 0.6, z - 1.6)], (0.9, 0.85, 1.0), 'bone', ['body'], steps=4)
    # broad bony shoulders joined by a collarbone
    m.tube([(-7.6, 36.2, 0.8), (0, 35.0, 2.6), (7.6, 36.2, 0.8)], [1.3, 1.1, 1.3], 'bone', 'body')
    for s in (-1, 1):
        m.ell((s * 7.8, 36.4, 0.4), (2.6, 2.2, 2.4), 'bone', 'body')
    # a ragged frost-rimed shawl flaring wide off the shoulders
    for k in range(13):
        a = (-165 + 330.0 * k / 12) * DEG
        sx = math.sin(a)
        q = (sx * 7.0, 37.6, 0.8 + math.cos(a) * 3.4)
        out = (sx * 5.6, -3.6 - 1.8 * (k % 3), math.cos(a) * 1.8)
        m.tube([q, add(q, mul(out, 0.5)), add(q, out)], [2.0, 1.4, 0.35], 'fur', 'shawl')
        m.sph(add(q, (0, 0.8, 0)), 1.1, 'frost', 'shawl')
    for s in (-1, 1):
        for (dx, dy, dz, ln) in ((0.3, 1.0, -0.2, 4.6), (0.9, 0.6, -0.4, 4.0)):
            b = (s * 8.0, 38.0, 0.0)
            d = norm((s * dx, dy, dz))
            m.crystal(b, add(b, mul(d, ln)), 0.9, 'frost', 'shawl', sides=4, tip_frac=0.7)
    # overlong arms hanging wide, dark knuckly hands, each with three long
    # separate bone claws raking down and out
    for s in (-1, 1):
        part = 'arm%d' % s
        m.tube([(s * 8.4, 35.0, 0.8), (s * 11.4, 27.6, 2.2), (s * 12.8, 21.0, 3.8)],
               [1.9, 1.4, 1.2], 'fur', part)
        m.sph((s * 11.4, 27.6, 2.2), 1.6, 'bone', part)
        w = (s * 13.0, 19.8, 4.0)
        m.ell(add(w, (0, -0.6, 0.2)), (2.3, 2.4, 1.9), 'fur', part)
        # three scythe claws from separate knuckles, hanging down and hooking in
        for k in range(3):
            o = (k - 1) * 1.6
            b0 = add(w, (s * 0.3 + o, -1.6, 0.8))
            mid = add(b0, (o * 1.3 - s * 0.2, -6.0, 1.0))
            tip = add(b0, (o * 2.2 - s * 1.4, -11.0 + abs(o) * 1.0, 2.8))
            m.tube([b0, mid, tip], [0.9, 0.75, 0.3], 'bone', 'claw%d%s' % (k, 'a' if s > 0 else 'b'))
    # thin neck thrust forward; the deer skull hangs face-down like a long mask
    m.tube([(0, 35.0, 2.0), (0, 39.0, 5.0), (0, 42.0, 6.4)], [1.9, 1.7, 1.6], 'fur', 'neck')
    head_c, head_r = (0, 45.0, 7.4), (4.4, 3.8, 3.6)
    m.ell(head_c, head_r, 'bone', 'head')
    m.tube([(0, 42.4, 9.4), (0, 39.8, 11.6), (0, 37.4, 12.8)], [2.2, 1.9, 1.5], 'bone', 'head')
    m.paint((0, 48.0, 7.0), (3.0, 1.2, 3.2), 'frost', ['head'])
    for s in (-1, 1):
        m.dot((s * 0.6, 37.2, 14.4), (0, -0.2, 1), w=1.0, h=1.4, color=('fur', 0))
    # deep sockets with cold glowing pupils
    for s in (-1, 1):
        p, n = g.on(head_c, head_r, (s * 0.6, 0.1, 0.79))
        m.dot(p, n, w=4.4, h=4.4, color=('fur', 0), minw=4, minh=4, shape='oval')
        m.eye(p, n, 2.8, 2.8, style='glow', iris=('ice', 1), center=(0, 44, 18), minw=2,
              minh=2, glint=False)
    # great frosted antlers, wide and uneven: a beam sweeping out to each side,
    # a few thick tines rising off it
    for s, tines, reach in ((1, ((1, (-0.1, 1.0, 0.15), 9.0), (2, (0.05, 1.0, 0.1), 11.0),
                                 (3, (0.5, 0.9, 0.1), 6.0)), 1.0),
                            (-1, ((1, (-0.2, 1.0, 0.2), 7.0), (2, (0.2, 1.0, 0.0), 10.0)), 0.88)):
        part = 'antler%d' % s
        beam = [(s * 2.2, 46.8, 5.6), (s * 7.0 * reach, 48.0, 4.6), (s * 12.0 * reach, 49.0, 3.6),
                (s * 16.4 * reach, 51.4, 3.0), (s * 18.2 * reach, 56.6, 3.0)]
        m.tube(beam, [1.4, 1.2, 1.0, 0.8, 0.35], 'bone', part,
               mats=[(0, 'bone'), (0.86, 'frost')])
        for (i, d, ln) in tines:
            b = beam[i]
            dd = norm((s * d[0], d[1], d[2]))
            tip = add(b, mul(dd, ln))
            m.tube([b, lerp(b, add(tip, (s * 0.8, 0, 0)), 0.55), tip], [1.2, 1.0, 0.4], 'bone',
                   part, mats=[(0, 'bone'), (0.62, 'frost')])
    # cold breath curling from the muzzle
    m.tube([(0.8, 36.4, 14.6), (2.6, 35.4, 16.6), (4.4, 36.4, 17.4)], [0.7, 0.9, 0.3], 'frost',
           'breath')
    return m


# ==========================================================================
# 117 LAMPJINN  RELIC/GALE  smoke genie rising from a brass oil lamp
# ==========================================================================
def lampjinn(g):
    m = g.Model('LAMPJINN')
    m.outline = (26, 18, 40)
    m.mat('brass', ['#5a3410', '#946020', '#d0a040', '#f8e08a'], spec=0.5)
    m.mat('skin', ['#243a78', '#3c5aa8', '#6488d0', '#a4c4f0'], th=[0.2, 0.46, 0.78])
    m.mat('smoke', ['#6a6ea8', '#a2a8dc', '#e2e6fc'])
    m.mat('ruby', ['#7a1434', '#c83060', '#f47898'], emissive=0.15)
    m.eye_dark = (36, 58, 120)
    m.white = (226, 230, 252)
    m.height = 58
    m.max_w = 62
    m.front_yaw = -28
    m.back_min_vis = 36
    # the oil lamp: squat bowl, long spout, curled handle, domed lid
    m.ell((0, 4.4, 0.0), (8.4, 4.0, 6.0), 'brass', 'lamp')
    m.ell((0, 1.1, 0.0), (3.8, 1.1, 3.0), 'brass', 'lamp')
    m.tube([(0, 5.0, 5.4), (0, 6.2, 9.4), (0, 8.6, 12.6), (0, 9.8, 13.8)], [2.6, 1.8, 1.3, 1.2],
           'brass', 'lamp')
    m.tube([(0, 5.8, -5.6), (0, 10.0, -8.4), (0, 10.6, -11.4), (0, 7.6, -12.4), (0, 5.2, -10.4)],
           [1.1, 1.1, 1.1, 1.0, 0.9], 'brass', 'lamp')
    m.ell((0, 8.0, 0.0), (4.0, 1.6, 3.4), 'brass', 'lamp')
    m.paint((0, 4.4, 6.0), (1.8, 1.4, 1.2), 'ruby', ['lamp'])
    for k in range(5):
        a = (k * 72 + 20) * DEG
        m.paint((math.sin(a) * 8.2, 4.8, math.cos(a) * 5.8), 0.9, 'ruby', ['lamp'])
    # the smoke tail spiralling up out of the lamp and swelling into the body
    pts, rads = [], []
    for i in range(9):
        t = i / 8.0
        a = t * 1.6 * math.pi
        pts.append((math.sin(a) * 3.0 * (1 - t), 9.0 + 15.0 * t, 1.0 + math.cos(a) * 2.0 * (1 - t)))
        rads.append(1.2 + 3.8 * t * t)
    m.tube(pts, rads, 'smoke', 'smoke', mats=[(0, 'smoke'), (0.9, 'skin')])
    for (b, d) in ((((2.6, 13.0, 2.0), (5.4, 15.0, 1.0), (6.6, 13.8, -0.6)), 1.0),
                   (((-2.8, 16.4, 0.2), (-6.0, 17.4, 0.4), (-7.0, 16.0, 2.0)), 0.9)):
        m.tube(list(b), [d, d * 0.9, 0.3], 'smoke', 'smoke')
    # broad torso and a gold sash
    m.ell((0, 28.0, 0.6), (6.8, 6.2, 4.4), 'skin', 'body')
    m.ell((0, 23.6, 0.6), (5.2, 1.6, 3.8), 'brass', 'body')
    # arms folded across the chest, gold cuffs
    for s in (-1, 1):
        m.sph((s * 6.8, 31.0, 0.2), 3.0, 'skin', 'arm%d' % s)
        m.tube([(s * 7.4, 30.0, 0.4), (s * 8.4, 25.4, 2.6), (s * 3.6, 27.0, 5.6),
                (-s * 2.2, 28.4, 5.6)], [2.4, 2.2, 2.0, 1.9], 'skin', 'arm%d' % s)
        m.tube([(s * 8.2, 26.2, 2.4), (s * 8.4, 25.2, 3.0)], [2.4, 2.4], 'brass', 'arm%d' % s)
    # head: a red turban with a gold jewel and a smoky plume, gold hoop earrings
    head_c, head_r = (0, 37.8, 1.6), (4.8, 4.8, 4.4)
    m.ell(head_c, head_r, 'skin', 'head')
    m.ell((0, 41.8, 1.0), (5.2, 2.6, 4.8), 'ruby', 'turban')
    m.ell((0, 43.6, 0.6), (3.8, 2.0, 3.8), 'ruby', 'turban')
    m.sph((0, 42.4, 5.6), 1.3, 'brass', 'turban')
    m.tube([(0, 45.0, 0.0), (0.4, 48.4, -1.0), (1.6, 51.4, -2.4), (3.4, 52.8, -3.6)],
           [1.6, 1.4, 1.0, 0.3], 'smoke', 'turban')
    for s in (-1, 1):
        m.tube([(s * 4.8, 36.4, 0.4), (s * 5.3, 34.6, 0.8), (s * 4.9, 33.4, 0.6)], [0.5, 0.5, 0.5],
               'brass', 'head')
        m.tube([(s * 3.8, 38.0, 1.0), (s * 5.6, 39.6, 0.2), (s * 6.6, 41.2, -0.4)], [1.2, 0.8, 0.2],
               'skin', 'head', flat=0.5, up=(0, 0, 1))
    # sly golden eyes, a curled moustache and a grin
    g.eye_pair(m, head_c, head_r, 30, 10, 3.6, 3.2, style='sharp', iris=('brass', 2), slant=0.9,
               center=(0, 37, 12), turn=6)
    for s in (-1, 1):
        m.tube([(s * 0.4, 35.4, 5.8), (s * 2.2, 34.8, 5.6), (s * 3.6, 35.6, 4.8)],
               [0.6, 0.5, 0.3], 'smoke', 'head')
    m.mouth((0.4, 33.8, 5.4), (0, -0.2, 1), 'smile', w=3.0)
    # sparks of wish-magic around it
    for (x, y, z) in ((10.4, 36.0, 2.0), (-10.0, 21.0, 2.0), (9.0, 15.0, 3.0)):
        star(m, (x, y, z), (0.3, 0, 1), 1.4, 'brass', 'magic')
    return m


# ==========================================================================
# 118 GARGOLITH  STONE/DUSK  cathedral gargoyle crouched on its ledge
# ==========================================================================
def gargolith(g):
    m = g.Model('GARGOLITH')
    m.outline = (22, 20, 26)
    m.mat('stone', ['#56545a', '#817e80', '#aeaaa2', '#d8d3c4'], th=[0.2, 0.46, 0.78])
    m.mat('dark', ['#2c2a34', '#46444e', '#66636c'])
    m.mat('moss', ['#3e6224', '#7aa23c'])
    m.mat('glow', ['#ff7a1e', '#ffe07a'], emissive=0.9)
    m.mat('fang', ['#f2eedc'])
    m.eye_dark = (22, 20, 26)
    m.white = (242, 238, 220)
    m.height = 54
    m.max_w = 62
    m.front_yaw = -20
    m.back_min_vis = 36
    # the little cathedral ledge it squats on: a dark block with a cornice lip
    m.box((0, 2.6, 0.6), (8.6, 2.6, 7.4), 'dark', 'plinth', bevel=0.3)
    m.box((0, 5.6, 1.0), (9.4, 0.7, 8.2), 'dark', 'plinth', bevel=0.3)
    ytop = 6.3
    # squat haunches, big hind feet with talons hooked over the lip
    m.ell((0, 12.4, -2.6), (6.4, 5.8, 5.6), 'stone', 'body')
    for s in (-1, 1):
        part = 'haunch%d' % s
        m.ell((s * 5.4, 11.4, -1.2), (3.2, 5.0, 5.4), 'stone', part, rot=(24, 0, 0))
        m.ell((s * 5.8, ytop + 1.3, 3.0), (2.4, 1.4, 3.8), 'stone', part)
        for t in (-1, 0, 1):
            x = s * 5.8 + t * 1.1
            m.tube([(x, ytop + 1.2, 6.2), (x, ytop + 0.6, 8.6), (x, ytop - 1.2, 9.6)],
                   [0.7, 0.55, 0.2], 'fang', part)
    # chest thrust forward over the ledge
    m.ell((0, 18.6, 1.0), (6.4, 7.2, 5.0), 'stone', 'body', rot=(26, 0, 0))
    # arms braced wide, hands gripping the front edge, ivory talons curled over it
    for s in (-1, 1):
        part = 'arm%d' % s
        m.sph((s * 6.0, 22.4, 2.4), 2.9, 'stone', part)
        m.tube([(s * 6.4, 21.6, 3.0), (s * 8.4, 15.0, 5.2), (s * 6.4, ytop + 1.8, 8.0)],
               [2.6, 2.1, 1.8], 'stone', part)
        m.ell((s * 6.2, ytop + 1.2, 8.4), (2.2, 1.3, 2.2), 'stone', part)
        for t in (-1, 0, 1):
            x = s * 6.2 + t * 1.0
            m.tube([(x, ytop + 1.0, 9.8), (x, ytop + 0.4, 10.6), (x, ytop - 1.6, 10.8)],
                   [0.65, 0.5, 0.2], 'fang', part)
    # bat wings half spread behind it, dark membranes framing the pale stone
    for s in (-1, 1):
        part = 'wing%d' % s
        sh = (s * 4.2, 23.0, -3.0)
        el = (s * 10.0, 31.0, -5.4)
        wr = (s * 16.0, 39.6, -7.0)
        claw = (s * 16.4, 43.4, -7.2)
        fingers = [(s * 21.0, 34.0, -8.0), (s * 21.4, 24.0, -8.4), (s * 16.8, 15.0, -7.8)]
        mem = [sh, el, wr]
        prev = wr
        for f in fingers:
            mid = lerp(prev, f, 0.5)
            mem.append(add(mid, mul(norm(sub((s * 6.0, 26.0, -5.0), mid)), 2.2)))
            mem.append(f)
            prev = f
        mem.append(add(lerp(prev, (s * 5.0, 13.0, -4.0), 0.5), (s * 1.4, 1.0, 0)))
        mem.append((s * 5.0, 13.0, -4.0))
        m.poly(mem, 'dark', part, puff=0.35)
        m.tube([sh, el, wr], [1.8, 1.5, 1.2], 'stone', part)
        m.tube([wr, claw], [1.0, 0.25], 'fang', part)
        for f in fingers:
            m.tube([wr, lerp(wr, f, 0.5), f], [1.0, 0.8, 0.3], 'stone', part)
    side_yaw(g, m, -64)
    # spade-tipped tail hanging down over the side of the ledge
    m.tube([(0, 10.0, -7.4), (4.0, 8.6, -9.2), (8.4, 7.4, -7.6), (10.4, 4.4, -5.0),
            (10.6, 1.6, -3.4)], [1.8, 1.5, 1.2, 1.0, 0.8], 'stone', 'tail')
    m.crystal((10.6, 2.2, -3.6), (10.7, -0.4, -2.6), 1.7, 'stone', 'tail', sides=4, tip_frac=0.6)
    # head: a grotesque with a heavy brow, a flat snout, great horns, a wide snarl
    head_c, head_r = (0, 28.4, 6.6), (6.0, 5.2, 5.0)
    m.ell(head_c, head_r, 'stone', 'head')
    m.ell((0, 32.0, 9.0), (5.4, 1.5, 2.2), 'stone', 'head')
    m.ell((0, 28.0, 11.0), (1.8, 2.4, 1.8), 'stone', 'head')
    m.ell((0, 27.4, 12.4), (2.4, 1.3, 1.2), 'stone', 'head')
    for s in (-1, 1):
        m.dot((s * 0.9, 27.2, 13.6), (s * 0.3, -0.2, 1), w=1.0, h=1.0, color=('dark', 0))
    # the jaw hangs wide open: a dark throat with a glowing ember deep inside,
    # ivory fangs top and bottom
    m.ell((0, 23.6, 10.0), (4.0, 2.8, 2.6), 'dark', 'maw')
    m.ell((0, 22.4, 11.2), (1.8, 1.0, 1.6), 'glow', 'maw')
    m.ell((0, 20.6, 9.6), (4.2, 1.3, 3.4), 'stone', 'head', rot=(-16, 0, 0))
    for s in (-1, 1):
        m.crystal((s * 2.4, 26.2, 11.4), (s * 2.2, 22.8, 12.2), 0.85, 'fang', 'head', sides=4,
                  tip_frac=0.8)
        m.crystal((s * 3.0, 21.4, 12.0), (s * 2.9, 24.0, 12.4), 0.75, 'fang', 'head', sides=4,
                  tip_frac=0.8)
    # big horns sweeping up and back, pointed ears flaring out
    for s in (-1, 1):
        m.tube([(s * 3.0, 31.2, 6.4), (s * 5.4, 35.0, 5.6), (s * 6.8, 39.4, 3.4),
                (s * 6.0, 43.0, 0.2), (s * 4.0, 44.2, -1.8)],
               [1.9, 1.6, 1.2, 0.8, 0.25], 'dark', 'horn%d' % s)
        m.tube([(s * 4.8, 28.6, 4.8), (s * 7.4, 29.8, 4.0), (s * 9.6, 31.4, 3.2)],
               [1.6, 1.0, 0.2], 'stone', 'head', flat=0.45, up=(0, 0, 1))
    # glowing eyes deep in dark sockets under the brow
    for s in (-1, 1):
        p, n = g.on(head_c, head_r, (s * 0.58, 0.3, 0.76))
        m.dot(p, n, w=4.4, h=3.6, color=('dark', 0), minw=4, minh=3)
        m.eye(p, n, 2.8, 2.0, style='glow', iris=('glow', 1), slant=1.0, center=(0, 28, 14),
              minw=2, minh=2)
    # moss creeping over the brow, shoulders, haunches and ledge
    for (c, r, parts) in (((1.4, 33.4, 9.0), (3.0, 1.2, 2.0), ['head']),
                          ((6.2, 24.8, 3.4), (2.6, 2.0, 2.6), ['arm1', 'body']),
                          ((-5.8, 24.6, 3.0), (2.2, 1.8, 2.4), ['arm-1', 'body']),
                          ((8.4, 14.6, 5.6), (1.6, 2.2, 1.8), ['arm1']),
                          ((7.6, 13.6, -0.6), (2.0, 2.6, 2.6), ['haunch1']),
                          ((-3.4, 5.6, 9.2), (3.2, 1.2, 1.4), ['plinth']),
                          ((9.4, 4.0, 2.0), (1.4, 2.6, 3.0), ['plinth']),
                          ((5.0, 6.2, -4.0), (3.0, 0.9, 3.0), ['plinth'])):
        m.paint(c, r, 'moss', parts)
    # a weathering crack down the chest
    paint_path(m, [(1.0, 22.6, 6.6), (-0.4, 19.4, 7.0), (0.6, 16.0, 6.4)], 0.6, 'dark', ['body'], 4)
    return m


# ==========================================================================
# 119 HOPSHI  HOLLOW/BRAWL  stiff-armed hopping jiangshi with a talisman
# ==========================================================================
def hopshi(g):
    m = g.Model('HOPSHI')
    m.outline = (18, 16, 30)
    m.mat('robe', ['#1a1e3c', '#2c3466', '#44508e', '#6a78b4'], th=[0.2, 0.46, 0.78])
    m.mat('gold', ['#b0801c', '#f0cc5c'])
    m.mat('paper', ['#e4c040', '#fff4a8'])
    m.mat('skin', ['#5e8272', '#9cc0a4', '#d4ecd0'])
    m.mat('red', ['#8a1c1c', '#e0402c'], emissive=0.2)
    m.eye_dark = (26, 30, 60)
    m.white = (255, 244, 168)
    m.height = 52
    m.max_w = 60
    m.front_yaw = -38
    m.back_min_vis = 36
    # little black boots peeking under the hem (no leg stride: it hops)
    for s in (-1, 1):
        m.ell((s * 2.4, 1.4, 2.0), (1.9, 1.4, 3.0), 'robe', 'shoe%d' % s)
    # long official's robe, flaring to the hem, broad square shoulders
    frustum(m, (0, 1.2, 0.0), 7.4, 5.2, 24.0, 16, 'robe', 'body')
    m.ell((0, 26.0, 0.0), (7.0, 3.0, 4.8), 'robe', 'body')
    m.paint((0, 2.6, 0.0), (8.4, 1.4, 8.4), 'gold', ['body'])
    # the rank badge: a gold square with a red sun, and a gold placket
    m.box((0, 19.4, 5.6), (2.6, 2.6, 0.4), 'gold', 'body', rot=(-4, 0, 0), bevel=0.0)
    m.paint((0, 19.4, 6.2), (1.2, 1.2, 1.0), 'red', ['body'])
    paint_path(m, [(0, 15.4, 6.2), (0, 5.0, 7.0)], (0.75, 0.75, 0.8), 'gold', ['body'])
    # arms held stiffly straight out in front, wide sleeves with gold edges
    for s in (-1, 1):
        part = 'arm%d' % s
        m.tube([(s * 5.4, 26.4, 0.6), (s * 5.0, 26.4, 6.0), (s * 4.8, 26.4, 10.6)], [2.6, 2.7, 2.9],
               'robe', part)
        m.paint((s * 4.8, 26.4, 11.0), (3.4, 3.4, 0.9), 'gold', [part])
        m.ell((s * 4.8, 26.2, 12.6), (1.6, 1.3, 1.8), 'skin', part)
        for t in (-1, 0, 1):
            m.tube([(s * 4.8 + t * 0.8, 26.2, 13.8), (s * 4.8 + t * 0.9, 25.8, 16.4)], [0.5, 0.2],
                   'skin', part)
    # pale head under a round black official's hat with a red button
    head_c, head_r = (0, 32.2, 1.4), (4.2, 4.4, 4.0)
    m.ell(head_c, head_r, 'skin', 'head')
    m.ell((0, 36.6, 1.2), (6.2, 1.0, 6.0), 'robe', 'hat')
    m.ell((0, 38.4, 1.0), (4.2, 2.4, 4.0), 'robe', 'hat')
    m.sph((0, 41.2, 1.0), 1.3, 'red', 'hat')
    # red silk fringe falling from the button down the back of the crown
    for k in range(5):
        a = (130 + 100.0 * k / 4) * DEG
        q = (math.cos(a) * 3.6, 38.8, 1.0 - math.sin(a) * 3.4)
        m.tube([(0, 40.6, 1.0), q, add(q, (math.cos(a) * 1.4, -3.0, -math.sin(a) * 1.2))],
               [0.55, 0.55, 0.35], 'red', 'hat')
    # the paper talisman hanging from the brim over its face, red script on it
    m.box((0.6, 31.6, 6.0), (1.5, 4.4, 0.25), 'paper', 'talisman', rot=(6, 0, 4), bevel=0.0)
    paint_path(m, [(0.8, 34.6, 6.4), (0.6, 32.0, 6.6), (0.9, 29.0, 6.4)], (0.55, 0.55, 0.6), 'red',
               ['talisman'], 5)
    paint_path(m, [(-0.3, 32.6, 6.4), (1.6, 32.2, 6.4)], (0.5, 0.5, 0.6), 'red', ['talisman'], 3)
    # small blank eyes either side of the talisman, a stiff line of a mouth
    for s in (-1, 1):
        a = (s * 44 + 4) * DEG
        p, n = g.on(head_c, head_r, (math.sin(a), 0.12, math.cos(a)))
        m.eye(p, n, 2.6, 2.6, style='cute', center=(0, 32, 12), minw=2, minh=2, glint=True)
    m.mouth((-2.4, 29.2, 4.2), (-0.4, -0.2, 1), 'line', w=1.6)
    # a braid down the back
    m.tube([(0, 33.0, -3.4), (0.4, 28.0, -5.4), (0.8, 22.0, -5.6), (1.2, 18.0, -5.0)],
           [1.2, 1.0, 0.8, 0.5], 'robe', 'braid')
    m.sph((1.2, 17.6, -4.9), 0.8, 'red', 'braid')
    return m


# ==========================================================================
# 120 QILUMEN  ASTRAL/SPARK  gold-scaled kirin with a starry mane
# ==========================================================================
def qilumen(g):
    m = g.Model('QILUMEN')
    m.outline = (34, 18, 44)
    m.mat('gold', ['#7a4a10', '#c08420', '#f0c040', '#fff0a0'], th=[0.2, 0.46, 0.78], spec=0.4)
    m.mat('scale', ['#7a4a10', '#c08420'])
    m.mat('mane', ['#2a1a5c', '#4a34a0', '#7c64d8'])
    m.mat('spark', ['#2a84d8', '#52d4ff', '#e6fcff'], emissive=0.35)
    m.eye_dark = (42, 26, 92)
    m.white = (255, 255, 255)
    m.height = 60
    m.max_w = 62
    m.front_yaw = -36
    # lean deer body with a row of scales down the back
    m.ell((0, 22.0, -1.0), (5.6, 5.8, 11.0), 'gold', 'body')
    m.ell((0, 23.4, 6.0), (5.6, 6.6, 5.4), 'gold', 'body')
    for k in range(6):
        z = 5.0 - 3.2 * k
        for s in (-1, 1):
            m.paint((s * 2.0, 27.2 - 0.25 * k, z), (1.5, 1.2, 1.3), 'scale', ['body'])
    # slender legs, dark cloven hooves, starry flame tufts at the heels
    for s in (-1, 1):
        m.tube([(s * 3.4, 19.0, 7.6), (s * 3.6, 10.0, 8.6), (s * 3.6, 3.0, 8.4)], [2.3, 1.4, 1.3],
               'gold', 'legF%d' % s)
        m.ell((s * 3.6, 1.3, 8.8), (1.7, 1.3, 2.0), 'mane', 'legF%d' % s)
        m.ell((s * 3.8, 20.0, -8.0), (3.0, 5.2, 4.4), 'gold', 'legB%d' % s)
        m.tube([(s * 3.9, 16.0, -10.0), (s * 4.0, 9.0, -11.6), (s * 3.8, 3.0, -10.2)],
               [2.1, 1.4, 1.3], 'gold', 'legB%d' % s)
        m.ell((s * 3.8, 1.3, -9.8), (1.7, 1.3, 2.0), 'mane', 'legB%d' % s)
        for (nm, z) in (('legF', 8.0), ('legB', -10.4)):
            b = (s * 3.8, 4.6, z - 0.6)
            m.tube([b, add(b, (s * 0.8, 0.4, -2.2)), add(b, (s * 1.0, 1.6, -3.6))], [1.3, 1.0, 0.3],
                   'mane', '%s%d' % (nm, s), mats=[(0, 'mane'), (0.7, 'spark')])
    # lion tail ending in a starry tuft
    m.tube([(0, 24.0, -11.6), (0, 25.0, -15.0), (1.0, 22.0, -17.0), (2.0, 19.0, -17.6)],
           [1.2, 1.0, 0.9, 0.8], 'gold', 'tail')
    g.flame(m, (2.0, 19.0, -17.8), 7.0, 2.6, 'tail', mats=('mane', 'mane', 'spark'),
            up=(0.2, -0.6, -1), tongues=2, seed=11)
    # neck and dragonish head
    m.tube([(0, 25.0, 7.0), (0, 31.0, 10.6), (0, 36.4, 12.4)], [4.2, 3.4, 3.0], 'gold', 'neck')
    head_c, head_r = (0, 39.0, 14.4), (4.6, 4.2, 4.6)
    m.ell(head_c, head_r, 'gold', 'head')
    m.tube([(0, 38.2, 16.8), (0, 37.0, 20.0), (0, 36.2, 22.2)], [3.2, 2.7, 2.5], 'gold', 'head')
    m.ell((0, 39.4, 18.2), (3.2, 1.0, 1.6), 'gold', 'head')
    m.dot((0, 37.2, 24.6), (0, 0.3, 1), w=2.0, h=1.0, color=('scale', 0))
    m.mouth((0, 35.2, 23.4), (0, -0.3, 1), 'smile', w=2.6)
    # a starry goatee under the chin
    m.tube([(0, 34.6, 19.0), (0, 32.4, 19.4), (0, 30.6, 18.6)], [1.4, 1.1, 0.3], 'mane', 'head',
           flat=0.5, up=(1, 0, 0))
    # great branching antlers of living starlight: a thick beam sweeping up and
    # back from each brow, three tines off it and a forked crown at the top
    for s in (-1, 1):
        part = 'antler%d' % s
        beam = [(s * 1.8, 42.0, 13.6), (s * 4.6, 45.4, 13.0), (s * 8.0, 47.4, 12.4),
                (s * 11.4, 49.6, 11.8), (s * 13.0, 53.4, 11.4)]
        m.tube(beam, [1.4, 1.15, 0.95, 0.8, 0.35], 'spark', part)
        for k, (i, d, ln, r) in enumerate(((1, (-0.2, 1.0, 0.1), 6.4, 0.85),
                                           (2, (0.0, 1.0, 0.0), 6.0, 0.8),
                                           (3, (0.1, 1.0, 0.0), 3.8, 0.7))):
            b0 = beam[i]
            dd = norm((s * d[0], d[1], d[2]))
            tip = add(b0, mul(dd, ln))
            m.tube([b0, add(lerp(b0, tip, 0.6), (s * -0.3, 0, 0)), add(tip, (s * 0.6, 0, 0))],
                   [r, r * 0.8, 0.25], 'spark', 'tine%d%s' % (k, 'a' if s > 0 else 'b'))
        m.tube([(s * 2.8, 41.2, 12.2), (s * 4.8, 42.4, 11.2), (s * 6.0, 43.4, 10.2)], [1.1, 0.7, 0.2],
               'gold', 'head', flat=0.5, up=(0, 0, 1))
    # sharp bright eyes
    for s in (-1, 1):
        p, n = g.on(head_c, head_r, (s * 0.66, 0.16, 0.74))
        m.dot(p, n, w=4.4, h=3.6, color=('mane', 0), minw=4, minh=3)
        m.eye(p, n, 3.0, 2.4, style='glow', iris=('spark', 1), slant=0.8, center=(0, 38, 22),
              minw=2, minh=2)
    # the starry mane: a thick night-sky ridge from brow to withers, streaming
    # back over both sides of the neck and full of bright stars
    crest = [(0, 42.4, 11.4), (0, 40.4, 10.0), (0, 37.8, 8.8), (0, 35.0, 7.4), (0, 32.2, 5.8),
             (0, 29.4, 3.8), (0, 27.6, 1.2)]
    for k, q in enumerate(crest):
        for s in (1, -1):
            ln = 1.0 + 0.15 * (k % 2)
            pts = [q, add(q, (s * 2.8, 2.2, -2.6)), add(q, (s * 4.6, 1.0, -6.0 * ln)),
                   add(q, (s * 5.0, -2.8, -8.4 * ln))]
            m.tube(pts, [2.5, 2.3, 1.6, 0.35], 'mane', 'mane', flat=0.55, up=(1, 0.3, 0))
    for (x, y, z, r) in ((4.6, 43.0, 8.6, 1.0), (5.6, 39.6, 5.0, 1.1), (6.0, 35.2, 2.4, 1.0),
                         (5.8, 31.4, -0.4, 1.1), (6.2, 27.6, -3.2, 0.9), (4.8, 37.2, 0.0, 0.8),
                         (4.4, 33.0, -4.4, 0.8), (-5.4, 38.4, 5.0, 1.0), (-5.8, 31.8, 0.0, 1.0)):
        m.sph((x, y, z), r, 'spark', 'mane')
    for (x, y, z) in ((6.4, 41.6, 6.6), (6.6, 33.2, 1.0), (6.4, 29.2, -1.8)):
        m.sparkle((x, y, z), (1, 0.2, 0.4), size=1)
    return m


# ---- end of batch ----
