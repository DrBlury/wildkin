"""Art for the legends 121-129 (owner: KIN-C).

Each model function takes the gen_monsters module `g` (see tools/kin/__init__)
and returns a g.Model. The renderer helpers are bound into this module's
globals by _use(g) so the model code reads like the models in gen_monsters.

Legends fill the 64x64 frame like DRAKORA and stand (or hover) in their
lairs as 32x32 overworld sprites.
"""

import math

_NAMES = ('Model', 'add', 'sub', 'mul', 'dot', 'cross', 'length', 'norm', 'lerp',
          'rot_matrix', 'mat_apply', 'surf', 'on', 'eye_pair', 'flame', 'leaf',
          'curl_horn', 'seedball', 'poly_local', 'jagged_leaf', 'zigzag',
          'wing_shape', 'gill', 'lantern', 'Rand', 'DEG', 'catmull')


def _use(g):
    gl = globals()
    for n in _NAMES:
        gl[n] = getattr(g, n)
    return g


def hover(g, name, px):
    """Overworld hover (px of lift) for kin that float in their lair."""
    g.OW_FLOAT[name] = px


def side_yaw(g, name, yaw):
    """Overworld profile yaw: winged kin turn toward the camera a little."""
    g.OW_SIDE_YAW[name] = yaw


# --------------------------------------------------------------------------
# shared helpers
# --------------------------------------------------------------------------
def frame(fwd, up):
    """Orthonormal (right, up, forward) basis from a forward and rough up."""
    f = norm(fwd)
    u = norm(sub(up, mul(f, dot(up, f))))
    r = cross(u, f)
    return r, u, f


def local(o, basis, x, y, z):
    r, u, f = basis
    return add(o, add(mul(r, x), add(mul(u, y), mul(f, z))))


def disc_rot(normal):
    """(yaw, pitch, 0) that turns a disc's local +Z onto `normal`."""
    n = norm(normal)
    yaw = math.atan2(n[0], n[2]) / DEG
    pitch = -math.asin(max(-1.0, min(1.0, n[1]))) / DEG
    return (yaw, pitch, 0)


def gear_ring(m, c, r, normal, teeth, mat, part, rim=1.1, tooth=1.2, spokes=4,
              hub_mat=None, phase=0.0):
    """An open cog: a rim ring with teeth, spokes and a hub."""
    n = norm(normal)
    a = norm(cross(n, (0, 1, 0) if abs(n[1]) < 0.9 else (1, 0, 0)))
    b = cross(n, a)
    ring = []
    for k in range(25):
        t = 2 * math.pi * k / 24 + phase
        ring.append(add(c, mul(add(mul(a, math.cos(t)), mul(b, math.sin(t))), r)))
    m.tube(ring, rim, mat, part)
    for k in range(teeth):
        t = 2 * math.pi * (k + 0.5) / teeth + phase
        d = add(mul(a, math.cos(t)), mul(b, math.sin(t)))
        m.sph(add(c, mul(d, r + rim * 0.95)), tooth * 0.8, mat, part)
    for k in range(spokes):
        t = 2 * math.pi * k / spokes + phase + 0.4
        d = add(mul(a, math.cos(t)), mul(b, math.sin(t)))
        m.tube([c, add(c, mul(d, r))], rim * 0.7, mat, part)
    m.ell(c, (r * 0.26, r * 0.26, rim * 1.2), hub_mat or mat, part, rot=disc_rot(n))


def vertebrae(m, pts, r0, r1, mat, part, gap=0.9):
    """Knobbly bone chain along a polyline: touching spheres shrinking r0->r1."""
    dense = []
    for i in range(len(pts) - 1):
        for k in range(8):
            dense.append(lerp(pts[i], pts[i + 1], k / 8.0))
    dense.append(tuple(pts[-1]))
    cum = [0.0]
    for i in range(1, len(dense)):
        cum.append(cum[-1] + length(sub(dense[i], dense[i - 1])))
    total = cum[-1]
    s = 0.0
    j = 0
    while s <= total + 1e-6:
        t = s / total if total > 0 else 0
        r = r0 + (r1 - r0) * t
        while j < len(cum) - 2 and cum[j + 1] < s:
            j += 1
        seg = max(cum[j + 1] - cum[j], 1e-9)
        f = min(1.0, max(0.0, (s - cum[j]) / seg))
        m.sph(lerp(dense[j], dense[j + 1], f), r, mat, part)
        s += max(0.5, r * 2 * gap)


# --------------------------------------------------------------------------
# 121 CALDERON: colossal forge salamander (BLAZE/METAL), CALDERA HEART
# --------------------------------------------------------------------------
def calderon(g):
    _use(g)
    m = Model('CALDERON')
    m.outline = (24, 12, 20)
    m.mat('skin', ['#1c1620', '#342834', '#564250'])
    m.mat('iron', ['#2e3440', '#56606e', '#8a96a4', '#c8d2dc'], spec=0.45)
    m.mat('fire', ['#c4301a', '#ff7a1c'], emissive=0.6)
    m.mat('magma', ['#ffa02a', '#ffe070', '#fff8d4'], emissive=0.9)
    m.eye_dark = (24, 12, 20)
    m.white = (255, 248, 212)
    m.height = 58
    m.max_w = 62
    m.front_yaw = -34
    m.back_scale = 1.1
    # heavy body, chest reared up on planted fore legs
    body = [(0, 27.0, 10.0), (0, 23.0, 4.0), (0, 18.5, -2.5), (0, 15.5, -9.0)]
    m.tube(body, [7.0, 8.6, 8.8, 7.6], 'skin', 'body')
    tail = [(0.5, 14.5, -13.0), (3.5, 12.0, -18.5), (9.5, 10.5, -21.5), (16.0, 10.5, -20.0),
            (20.5, 12.5, -15.5), (22.5, 16.5, -10.5)]
    m.tube(tail, [6.4, 5.2, 4.2, 3.4, 2.6, 1.8], 'skin', 'tail')
    flame(m, (22.8, 17.5, -9.8), 12, 4.2, 'tail', mats=('fire', 'magma', 'magma'),
          up=(0.1, 1, 0.35), seed=121)
    # molten blotches: a fire salamander's spots, glowing from inside
    for s in (-1, 1):
        for (x, y, z, r) in ((7.8, 21.0, 4.0, 2.8), (8.2, 17.0, -4.5, 2.6),
                             (6.6, 25.5, 10.0, 2.0), (6.8, 13.5, -10.5, 2.0)):
            m.paint((s * x, y, z), (r * 0.8, r * 0.7, r * 1.2), 'fire', ['body'])
            m.paint((s * (x + 0.8), y, z), (r * 0.4, r * 0.35, r * 0.6), 'magma', ['body'])
    for (q, r) in (((5.6, 13.8, -17.5), 1.9), ((12.4, 13.0, -20.6), 1.6),
                   ((19.0, 14.6, -16.0), 1.3)):
        m.paint(q, (r, r * 0.8, r * 1.2), 'fire', ['tail'])
    # ingot plates standing up the spine like a forge's fins
    fins = [((0, 33.2, 8.5), 3.0, 2.2), ((0, 31.6, 3.2), 3.9, 2.6), ((0, 28.8, -2.2), 4.0, 2.6),
            ((0, 25.0, -7.4), 3.4, 2.4), ((0.6, 20.8, -12.6), 2.8, 2.0),
            ((4.0, 17.4, -18.0), 2.2, 1.7), ((10.0, 15.0, -21.2), 1.7, 1.4),
            ((16.2, 14.2, -19.6), 1.3, 1.1)]
    for k, (c, h, w) in enumerate(fins):
        part = 'body' if k < 5 else 'tail'
        yaw = 0 if k < 5 else (35 + 30 * (k - 5))
        m.box(add(c, (0, h * 0.5, 0)), (0.9, h, w), 'iron', part, rot=(yaw, 0, 0),
              bevel=0.5)
        m.paint(add(c, (0, -0.6, 0)), (1.6, 1.0, w), 'magma', [part], rot=(yaw, 0, 0))
    # smokestack vents on the shoulders, venting the forge
    for s in (-1, 1):
        b = (s * 5.0, 29.5, 6.5)
        t = (s * 6.6, 35.5, 5.0)
        m.tube([b, t], [2.2, 1.8], 'iron', 'vent%d' % s)
        m.ell(t, (2.2, 0.9, 2.2), 'iron', 'vent%d' % s)
        m.ell(add(t, (0, 0.5, 0)), (1.4, 0.6, 1.4), 'magma', 'vent%d' % s)
        flame(m, add(t, (0, 0.6, 0)), 12 if s > 0 else 10, 3.0, 'vent%d' % s,
              mats=('fire', 'magma', 'magma'), up=(s * 0.12, 1, -0.2), seed=40 + s,
              tongues=2)
    # legs: splayed like a salamander, iron spurs and claws
    for s in (-1, 1):
        sh = (s * 7.2, 23.0, 8.5)
        el = (s * 13.2, 17.5, 10.5)
        wr = (s * 13.4, 4.8, 13.0)
        m.sph(sh, 4.4, 'skin', 'legF%d' % s)
        m.tube([sh, el, wr], [4.2, 3.6, 3.1], 'skin', 'legF%d' % s)
        m.ell((s * 13.6, 2.2, 14.6), (3.9, 2.2, 4.6), 'skin', 'legF%d' % s)
        m.crystal(add(el, (s * 1.0, 0.5, -2.0)), add(el, (s * 3.0, 3.5, -6.5)), 1.4, 'iron',
                  'legF%d' % s, sides=4, tip_frac=0.7)
        for t in (-1, 0, 1):
            m.crystal((s * 13.6 + t * 2.0, 1.6, 17.4), (s * 13.6 + t * 2.6, 0.5, 20.6),
                      0.95, 'iron', 'legF%d' % s, sides=4, tip_frac=0.8)
        hp = (s * 7.2, 15.5, -9.5)
        kn = (s * 13.2, 13.2, -7.4)
        an = (s * 13.4, 3.6, -8.6)
        m.sph(hp, 4.8, 'skin', 'legB%d' % s)
        m.tube([hp, kn, an], [4.6, 3.8, 3.1], 'skin', 'legB%d' % s)
        m.ell((s * 13.6, 2.0, -6.8), (3.7, 2.0, 4.4), 'skin', 'legB%d' % s)
        m.crystal(add(kn, (s * 1.0, 0.8, -1.0)), add(kn, (s * 3.2, 4.0, -5.0)), 1.3, 'iron',
                  'legB%d' % s, sides=4, tip_frac=0.7)
        for t in (-1, 0, 1):
            m.crystal((s * 13.6 + t * 1.9, 1.5, -4.0), (s * 13.6 + t * 2.4, 0.5, -1.0),
                      0.9, 'iron', 'legB%d' % s, sides=4, tip_frac=0.8)
    # broad flat head thrown back, jaw open on a molten maw
    m.tube([(0, 29.0, 10.5), (0, 32.0, 14.0)], [6.4, 6.0], 'skin', 'head')
    head_c, head_r = (0, 35.2, 18.5), (7.6, 4.0, 9.0)
    m.ell(head_c, head_r, 'skin', 'head', rot=(0, -14, 0))
    m.ell((0, 30.0, 18.2), (6.6, 2.3, 8.0), 'skin', 'jaw', rot=(0, 12, 0))
    m.ell((0, 32.2, 19.6), (5.6, 2.2, 6.6), 'magma', 'maw')
    for s in (-1, 1):
        for k in range(3):
            q = (s * (2.2 + k * 1.7), 33.6 + k * 0.1, 25.4 - k * 1.9)
            m.crystal(q, add(q, (0, -2.0, 0.2)), 0.55, 'iron', 'head', sides=4,
                      tip_frac=0.8)
        # bulging eye mounds and swept iron horns
        m.ell((s * 4.4, 38.6, 16.4), (2.6, 2.1, 2.6), 'skin', 'head')
        m.crystal((s * 5.4, 38.4, 13.0), (s * 9.0, 42.0, 6.0), 1.5, 'iron', 'head',
                  sides=4, tip_frac=0.7)
    m.crystal((0, 38.2, 13.0), (0, 44.8, 6.5), 1.9, 'iron', 'head', sides=4, tip_frac=0.7)
    for s in (-1, 1):
        m.eye((s * 4.4, 39.2, 18.0), (s * 0.5, 0.5, 0.8), 3.2, 2.8, style='glow',
              iris=('magma', 1), slant=0.9, center=(0, 36, 30), glint=False,
              pupil='outline')
        p, n = on(head_c, head_r, (s * 0.2, 0.35, 1), rot=(0, -14, 0))
        m.dot(p, n, w=1.2, h=1.0, color='outline', minw=1)
    return m


# --------------------------------------------------------------------------
# 122 NOCTHALE: star whale that sings under the sea (TIDE/ASTRAL), DROWNED BELL
# --------------------------------------------------------------------------
def nocthale(g):
    _use(g)
    hover(g, 'NOCTHALE', 3)
    side_yaw(g, 'NOCTHALE', -64.0)
    m = Model('NOCTHALE')
    m.outline = (10, 14, 44)
    m.mat('hide', ['#121848', '#1e2e72', '#30509e', '#5478cc'])
    m.mat('belly', ['#6a86c4', '#a8c4ea', '#e2eeff'])
    m.mat('neb', ['#4c2c8a', '#8e5ed2'])
    m.mat('groove', ['#5ad4f6'], emissive=0.9)
    m.mat('star', ['#fffbd8'], emissive=0.95)
    m.eye_dark = (10, 14, 44)
    m.white = (255, 251, 216)
    m.height = 54
    m.max_w = 62
    m.float_lift = 3
    m.front_yaw = -30
    # body: head raised, flank arcing down, tail rising to the flukes
    spine = [(-1.0, 41.5, 20.0), (0.0, 38.5, 13.0), (0.0, 34.0, 5.0), (0.5, 28.5, -3.0),
             (2.5, 23.0, -9.5), (6.5, 19.5, -14.5), (12.0, 18.5, -17.5), (17.0, 20.5, -18.0),
             (20.5, 24.5, -16.5)]
    radii = [5.6, 8.6, 10.6, 10.8, 9.4, 7.2, 5.0, 3.4, 2.2]
    m.tube(spine[:6], radii[:6], 'hide', 'body')
    m.tube(spine[5:], radii[5:], 'hide', 'tail')
    # pale lower jaw and throat; its grooves glow like starlight
    m.tube([(0, 36.5, 20.5), (0, 33.0, 13.0), (0.5, 27.0, 4.0), (1.5, 21.0, -3.0)],
           [4.6, 7.4, 8.0, 5.0], 'belly', 'body', flat=0.6, up=(0, -0.3, 1))
    for k in range(-2, 3):
        pts = [(k * 1.9, 35.2 - abs(k) * 0.3, 21.5 - abs(k) * 1.2),
               (k * 2.6, 30.2 - abs(k) * 0.3, 15.4 - abs(k) * 1.6),
               (k * 2.8, 24.5, 7.4 - abs(k) * 1.8)]
        for a, b in zip(pts, pts[1:]):
            for j in range(6):
                m.paint(lerp(a, b, j / 5.0), (0.55, 0.9, 1.6), 'groove', ['body'])
    # nebula band and a sky of stars along the flank and back
    for (x, y, z, r) in ((8.0, 31.0, -1.0, 3.6), (8.6, 25.5, -7.0, 3.2), (-7.0, 31.0, -1.0, 3.4),
                         (7.0, 20.0, -12.5, 2.6), (3.0, 40.0, 8.0, 2.8)):
        m.paint((x, y, z), (r, r * 1.3, r * 1.2), 'neb', ['body'])
    rnd = Rand(122)
    for i in range(26):
        k = min(len(spine) - 2, int(rnd.f() * 7))
        a, b = spine[k], spine[k + 1]
        q = lerp(a, b, rnd.f())
        rr = radii[k] + (radii[k + 1] - radii[k]) * 0.5
        ang = (10 + 110 * rnd.f()) * DEG
        d = (math.sin(ang), 0.35 + 0.6 * rnd.f(), -0.35 + 0.5 * math.cos(ang))
        p, n = on(q, (rr, rr, rr), d)
        part = 'body' if k < 5 else 'tail'
        if i % 4 == 0:
            m.sparkle(p, n, size=1, color=('star', 0))
        else:
            m.paint(p, 0.95, 'star', [part])
    # the bell-kernel on its brow
    p, n = on(spine[1], (8.6, 8.6, 8.6), (0.1, 0.9, 0.42))
    m.paint(p, (2.8, 2.2, 2.8), 'groove', ['body'])
    m.paint(add(p, mul(n, 0.5)), (1.5, 1.2, 1.5), 'star', ['body'])
    # long humpback flippers spread like wings
    fl = {1: [(9.0, 29.0, 6.0), (19.0, 26.5, 9.0), (29.0, 21.0, 8.5)],
          -1: [(-9.0, 33.0, 2.0), (-18.0, 41.0, -3.0), (-25.0, 48.5, -9.0)]}
    for s in (-1, 1):
        root, mid, tip = fl[s]
        m.tube([root, mid, tip], None, 'hide', 'fin%d' % s, flat=0.3, up=(0, 0.35, 1),
               rfn=lambda t: 4.8 * math.sin(math.pi * min(1, 0.15 + t * 0.88)) ** 0.55 + 0.2)
        for k in range(1, 6):
            t = k / 6.0
            q = lerp(root, mid, t * 2) if t < 0.5 else lerp(mid, tip, (t - 0.5) * 2)
            lead = (0, 3.2, 0) if s > 0 else (1.5, 1.5, 2.5)
            m.paint(add(q, lead), (2.4, 1.4, 2.4), 'belly', ['fin%d' % s])
        m.paint(tip, 1.6, 'groove', ['fin%d' % s])
    # flukes: a crescent with glowing points
    tb = spine[-1]
    for s in (-1, 1):
        leaf(m, tb, add(tb, (1.5, 3.5, s * 4.5)), add(tb, (3.0, 7.5 + s * 1.5, s * 9.5)), 3.6,
             'hide', 'tail', up=(0.9, 0.2, 0.3), flat=0.3)
        m.paint(add(tb, (3.0, 7.5 + s * 1.5, s * 9.0)), 1.7, 'star', ['tail'])
    m.crystal((5.5, 27.0, -9.0), (9.0, 29.5, -12.5), 2.0, 'hide', 'body', sides=5,
              tip_frac=0.8)
    head_c, head_r = (0, 37.5, 14.0), (8.2, 7.6, 8.0)
    for s in (-1, 1):
        p, n = on(head_c, head_r, (s * 0.8, -0.18, 0.58))
        m.eye(p, n, 3.2, 3.4, iris=('groove', 0), center=(0, 36, 24))
    p, n = on(head_c, head_r, (0.55, -0.42, 0.72))
    m.mouth(p, n, 'smile', w=4.0)
    return m


# --------------------------------------------------------------------------
# 123 HOARFANG: the winter wolf (FROST/DUSK), WHITECROWN PEAK
# --------------------------------------------------------------------------
def hoarfang(g):
    _use(g)
    m = Model('HOARFANG')
    m.outline = (22, 22, 52)
    m.mat('fur', ['#5a6aa0', '#9cb0dc', '#d6e4f8', '#ffffff'], th=[0.2, 0.46, 0.78])
    m.mat('dusk', ['#1c1636', '#382c62', '#5e4c92'])
    m.mat('ice', ['#3e9ee6', '#a4e6ff', '#effeff'], emissive=0.35)
    m.eye_dark = (22, 22, 52)
    m.white = (255, 255, 255)
    m.height = 58
    m.max_w = 62
    m.front_yaw = -30
    # body: deep chest, strong haunches
    m.ell((0, 25.0, 6.0), (8.4, 9.4, 8.6), 'fur', 'body')
    m.ell((0, 23.0, -7.0), (7.2, 7.8, 10.0), 'fur', 'body', rot=(0, 6, 0))
    # the shadow that runs over its back
    m.paint((0, 30.5, -4.0), (6.4, 3.6, 12.0), 'dusk', ['body'])
    for s in (-1, 1):
        top = (s * 4.8, 20.0, 8.5)
        m.tube([top, (s * 5.1, 11.0, 9.4), (s * 5.2, 3.4, 10.0)], [3.6, 2.8, 2.6], 'fur',
               'legF%d' % s)
        m.ell((s * 5.3, 1.9, 11.8), (3.0, 1.9, 3.8), 'fur', 'legF%d' % s)
        m.ell((s * 5.2, 20.5, -11.0), (4.4, 6.8, 6.0), 'fur', 'legB%d' % s, rot=(0, -10, 0))
        m.tube([(s * 5.4, 16.0, -14.5), (s * 5.6, 9.0, -17.0), (s * 5.6, 3.4, -14.0)],
               [3.0, 2.4, 2.4], 'fur', 'legB%d' % s)
        m.ell((s * 5.6, 1.9, -12.2), (2.8, 1.9, 3.6), 'fur', 'legB%d' % s)
    # great bushy tail, dusk-tipped
    m.tube([(0, 26.0, -16.0), (2.0, 32.0, -22.0), (6.0, 38.0, -23.0), (10.0, 43.0, -20.0),
            (12.0, 45.5, -16.0)], [3.6, 5.2, 5.4, 4.2, 1.6], 'fur', 'tail',
           mats=[(0, 'fur'), (0.72, 'dusk')])
    # crown of ice shards fanning up behind the head
    for k, (x, y, z, dx, dz, ln, r) in enumerate((
            (0.0, 35.0, 3.0, 0.0, -0.25, 17, 2.2), (4.0, 34.5, 2.5, 0.42, -0.2, 14, 1.9),
            (-4.0, 34.5, 2.5, -0.42, -0.2, 14, 1.9), (7.0, 33.0, 1.5, 0.9, -0.1, 11, 1.6),
            (-7.0, 33.0, 1.5, -0.9, -0.1, 11, 1.6), (2.4, 33.0, -2.0, 0.2, -0.55, 10, 1.5),
            (-2.4, 33.0, -2.0, -0.2, -0.55, 10, 1.5), (0.0, 31.5, -7.0, 0.0, -0.8, 8, 1.3))):
        b = (x, y, z)
        d = norm((dx, 1.0, dz))
        m.crystal(add(b, mul(d, -2.0)), add(b, mul(d, ln)), r, 'ice', 'crown', sides=4,
                  tip_frac=0.55, twist=k * 17)
    # thick white ruff round the neck
    rnd = Rand(123)
    for k in range(9):
        a = (-100 + 200.0 * k / 8) * DEG
        q = (math.sin(a) * 7.2, 31.5 + math.cos(a) * 2.0 - abs(math.sin(a)) * 2.0,
             8.5 + math.cos(a) * 3.0)
        m.sph(q, 3.6 * (0.85 + 0.3 * rnd.f()), 'fur', 'ruff')
    # neck + head
    m.tube([(0, 30.0, 8.0), (0, 35.5, 11.0)], [5.6, 5.0], 'fur', 'body')
    head_c, head_r = (0, 40.0, 13.0), (6.2, 5.6, 6.4)
    m.ell(head_c, head_r, 'fur', 'head')
    m.tube([(0, 38.8, 17.0), (0, 37.8, 21.5), (0, 37.2, 24.0)], [3.6, 2.7, 2.2], 'fur',
           'head')
    m.tube([(0, 35.8, 17.0), (0, 35.6, 22.0)], [2.4, 1.8], 'fur', 'head')
    m.ell((0, 38.8, 24.6), (1.6, 1.2, 1.1), 'dusk', 'head')
    m.paint((0, 43.5, 15.0), (3.0, 1.4, 4.0), 'dusk', ['head'])
    for s in (-1, 1):
        m.crystal((s * 1.4, 36.9, 21.6), (s * 1.5, 34.2, 22.0), 0.6, 'ice', 'head',
                  sides=4, tip_frac=0.8)
        m.tube([(s * 3.4, 44.0, 11.5), (s * 5.0, 49.5, 10.0), (s * 6.0, 54.5, 8.8)],
               [3.0, 2.0, 0.2], 'fur', 'ear%d' % s, flat=0.45, up=(0, 0.1, 1))
        m.paint((s * 4.6, 48.0, 11.0), (1.2, 2.6, 1.0), 'dusk', ['ear%d' % s])
        m.tube([(s * 5.0, 38.0, 11.0), (s * 7.8, 36.0, 9.5), (s * 9.2, 34.0, 8.0)],
               [2.4, 1.6, 0.2], 'fur', 'head', flat=0.5, up=(0, 0, 1))
    eye_pair(m, head_c, head_r, 32, 16, 4.0, 3.0, style='glow', iris=('ice', 1), slant=1.0,
             center=(0, 38, 23), turn=4, pupil='outline')
    m.mouth((0, 36.9, 21.0), (0, -0.1, 1), 'line', w=3.0)
    return m


# --------------------------------------------------------------------------
# 124 OSSUREX: bone dragon of the Ossuary (HOLLOW/WYRM), BONE THRONE
# --------------------------------------------------------------------------
def ossurex(g):
    _use(g)
    side_yaw(g, 'OSSUREX', -62.0)
    m = Model('OSSUREX')
    m.outline = (30, 20, 22)
    m.mat('bone', ['#5c5244', '#968c72', '#cec4a2', '#f4eedc'])
    m.mat('shroud', ['#241a26', '#3e2c3e', '#5e4658'])
    m.mat('ember', ['#e0501c', '#ffa02c', '#ffe68a'], emissive=0.85)
    m.eye_dark = (30, 20, 22)
    m.white = (255, 230, 138)
    m.height = 58
    m.max_w = 62
    m.back_scale = 1.12
    # tattered wings on bone struts (behind)
    for s in (-1, 1):
        sh_ = (s * 5.0, 35.0, -3.0)
        el = (s * 14.0, 45.0, -6.5)
        wr = (s * 22.0, 54.0, -9.0)
        fingers = [(s * 31.0, 46.0, -10.0), (s * 30.0, 35.0, -9.0),
                   (s * 24.5, 26.0, -7.5), (s * 15.0, 23.0, -5.0)]
        m.tube([sh_, el, wr], [2.2, 1.7, 1.3], 'bone', 'wing%d' % s)
        m.sph(el, 2.0, 'bone', 'wing%d' % s)
        m.sph(wr, 1.8, 'bone', 'wing%d' % s)
        mem = [sh_, el, wr, fingers[0]]
        for i in range(3):
            a, b = fingers[i], fingers[i + 1]
            mem.append(add(lerp(a, b, 0.3), (-s * 1.2, 1.4, 0.3)))
            mem.append(add(lerp(a, b, 0.5), (-s * 4.6, 3.0, 0.6)))
            mem.append(add(lerp(a, b, 0.7), (-s * 1.6, 1.6, 0.3)))
            mem.append(b)
        mem.append((s * 6.0, 27.0, -3.0))
        m.poly(mem, 'shroud', 'wing%d' % s, puff=0.3)
        for f in fingers:
            m.tube([wr, f], [1.0, 0.45], 'bone', 'wing%d' % s)
        m.crystal(wr, add(wr, (s * 0.8, 4.2, -0.5)), 0.9, 'bone', 'wing%d' % s,
                  sides=4, tip_frac=0.8)
    # spine: neck vertebrae -> back -> tail curling to +X
    neck = [(0.5, 42.5, 7.5), (1.0, 38.5, 5.0), (0.0, 34.0, 1.5)]
    back = [(0.0, 34.0, 1.5), (-1.0, 28.0, -1.0), (-0.5, 22.0, -1.5), (1.5, 17.0, -1.5)]
    tail = [(1.5, 17.0, -1.5), (5.0, 11.0, -3.0), (10.5, 7.0, -3.0), (16.0, 6.5, -1.5),
            (21.0, 9.0, 0.5), (23.5, 13.5, 1.5), (23.0, 18.0, 1.0)]
    vertebrae(m, neck, 2.3, 2.5, 'bone', 'neck')
    vertebrae(m, back, 2.4, 2.4, 'bone', 'body')
    vertebrae(m, tail, 2.4, 1.0, 'bone', 'tail')
    tip = tail[-1]
    m.crystal(add(tip, (0, -1.5, 0)), add(tip, (-1.0, 6.5, -0.4)), 1.8, 'bone', 'tail',
              sides=4, tip_frac=0.6)
    m.crystal(add(tip, (0.5, -1.0, 0)), add(tip, (3.5, 4.0, -0.4)), 1.3, 'bone', 'tail',
              sides=4, tip_frac=0.6)
    for q in back[1:3] + tail[1:4]:
        m.crystal(add(q, (0, 0.5, -1.2)), add(q, (0, 3.0, -4.0)), 0.8, 'bone', 'body',
                  sides=4, tip_frac=0.8)
    # ribcage, open at the front round the ember kernel (the heat of old bone)
    kc = (0.0, 27.0, 5.5)
    m.sph(add(kc, (0, -0.5, -2.8)), 5.6, 'shroud', 'core')
    m.sph(kc, 4.2, 'ember', 'core')
    for k in range(5):
        y = 32.0 - k * 2.7
        rr = 6.6 - abs(k - 1.5) * 0.55
        for s in (-1, 1):
            pts = []
            for i in range(7):
                a = (i / 6.0) * 128 * DEG
                pts.append((s * math.sin(a) * rr, y - i * 0.4 - 0.5 * math.sin(a),
                            -1.2 + (1 - math.cos(a)) * rr * 0.72))
            m.tube(pts, 0.85, 'bone', 'ribs')
    # pelvis + legs
    m.ell((0.8, 17.5, -1.0), (5.4, 2.6, 3.4), 'bone', 'body')
    for s in (-1, 1):
        hp = (s * 4.8, 17.0, 0.0)
        kn = (s * 6.4, 10.5, 4.0)
        an = (s * 6.0, 5.5, -1.0)
        ft = (s * 6.2, 1.2, 1.5)
        m.tube([hp, kn], [1.8, 1.3], 'bone', 'leg%d' % s)
        m.sph(kn, 2.0, 'bone', 'leg%d' % s)
        m.tube([kn, an, ft], [1.3, 1.1, 1.0], 'bone', 'leg%d' % s)
        for t in (-1, 0, 1):
            m.crystal(add(ft, (t * 1.2, 0, 0.5)), add(ft, (t * 1.8, -0.8, 4.0)), 0.6,
                      'bone', 'leg%d' % s, sides=4, tip_frac=0.8)
    # arms with raking claws
    for s in (-1, 1):
        a0 = (s * 6.2, 31.0, 2.0)
        a1 = (s * 10.0, 25.0, 5.0)
        a2 = (s * 8.6, 21.5, 9.5)
        m.tube([a0, a1], [1.3, 1.1], 'bone', 'arm%d' % s)
        m.sph(a1, 1.5, 'bone', 'arm%d' % s)
        m.tube([a1, a2], [1.1, 1.0], 'bone', 'arm%d' % s)
        for t in (-1, 0, 1):
            m.crystal(add(a2, (t * 0.9, 0, 0)), add(a2, (t * 1.3, -2.8, 2.2)), 0.5,
                      'bone', 'arm%d' % s, sides=4, tip_frac=0.8)
    # skull: heavy brow, open jaw lit from inside
    head_c, head_r = (0.5, 46.5, 9.5), (5.2, 4.4, 5.6)
    m.ell(head_c, head_r, 'bone', 'head')
    m.tube([(0.5, 45.8, 12.5), (0.5, 45.0, 16.5), (0.5, 44.2, 19.5)], [3.4, 2.8, 2.0],
           'bone', 'head')
    m.tube([(0.5, 41.6, 10.5), (0.5, 40.0, 15.0), (0.5, 39.4, 18.5)], [2.0, 1.6, 1.2],
           'bone', 'jaw')
    m.ell((0.5, 42.6, 13.5), (2.4, 1.5, 4.6), 'ember', 'jaw')
    for s in (-1, 1):
        for k in range(3):
            m.crystal((0.5 + s * 1.7, 43.0, 18.5 - k * 2.2),
                      (0.5 + s * 1.7, 41.2, 18.7 - k * 2.2), 0.5, 'bone', 'head', sides=4,
                      tip_frac=0.8)
        m.tube([(0.5 + s * 2.8, 49.6, 8.0), (0.5 + s * 5.6, 53.0, 4.5),
                (0.5 + s * 6.8, 56.5, 0.5), (0.5 + s * 6.2, 59.0, -2.5)],
               [1.7, 1.3, 0.9, 0.2], 'bone', 'horn%d' % s)
        m.tube([(0.5 + s * 4.4, 45.5, 7.0), (0.5 + s * 7.4, 45.0, 4.0),
                (0.5 + s * 8.8, 45.4, 1.5)], [1.3, 0.9, 0.2], 'bone', 'head')
        p, n = on(head_c, head_r, (s * 0.62, 0.22, 0.76))
        m.paint(p, (2.2, 1.8, 1.8), 'shroud', ['head'])
    eye_pair(m, head_c, head_r, 38, 13, 3.4, 2.8, style='glow', iris=('ember', 1),
             slant=0.8, center=(0.5, 44, 20), glint=False)
    return m


# --------------------------------------------------------------------------
# 125 SELENOTH: the moon moth (ASTRAL/DREAM), STARFALL GROTTO
# --------------------------------------------------------------------------
def selenoth(g):
    _use(g)
    hover(g, 'SELENOTH', 4)
    side_yaw(g, 'SELENOTH', -56.0)
    m = Model('SELENOTH')
    m.outline = (28, 22, 62)
    m.mat('wing', ['#6c68ac', '#a4a2da', '#d8d8f4', '#fbfbff'], th=[0.2, 0.46, 0.76])
    m.mat('night', ['#1c1a4c', '#322e78'])
    m.mat('gold', ['#e0a42c', '#ffe68a'], emissive=0.7)
    m.mat('fuzz', ['#b4b0d8', '#ffffff'])
    m.eye_dark = (22, 18, 56)
    m.white = (255, 255, 255)
    m.height = 58
    m.max_w = 62
    m.float_lift = 1
    root = (0, 38.0, -3.0)
    for s in (-1, 1):
        uv = norm((s * 1.0, 0.0, -0.32))

        def W(u, v, uv=uv):
            return add(root, add(mul(uv, u), (0, v, 0)))
        # falcate forewing sweeping up and out
        fore = [(0.5, 2.0), (6.0, 9.5), (13.0, 16.5), (21.0, 22.0), (28.0, 25.5), (33.0, 26.0),
                (32.5, 22.0), (29.0, 15.5), (22.5, 8.5), (13.0, 2.5), (5.0, -0.5), (1.0, -1.0)]
        m.poly([W(u, v) for u, v in fore], 'wing', 'wingF%d' % s, puff=0.35)
        # hindwing trailing a long ribbon tail
        hind = [(1.0, -1.5), (8.0, -2.5), (15.0, -5.0), (18.5, -9.5), (17.5, -14.5),
                (15.0, -19.0), (14.5, -26.0), (16.5, -32.5), (20.0, -37.5), (16.0, -36.5),
                (12.0, -30.5), (10.0, -23.0), (8.0, -15.5), (4.0, -9.0), (1.0, -4.0)]
        m.poly([W(u, v) for u, v in hind], 'wing', 'wingH%d' % s, puff=0.35)
        # night-blue costal edge, crescent-moon eyespots, dark tail tips
        for k in range(6):
            t = k / 5.0
            m.paint(W(3.0 + t * 27.0, 7.0 + t * 18.5), (2.6, 2.0, 2.4), 'night',
                    ['wingF%d' % s])
        c = W(20.0, 12.5)
        m.paint(c, 4.4, 'gold', ['wingF%d' % s])
        m.paint(add(c, add(mul(uv, 1.6), (0, 0.6, 0))), (3.7, 3.8, 3.7), 'wing',
                ['wingF%d' % s])
        c2 = W(11.5, -10.5)
        m.paint(c2, 3.2, 'gold', ['wingH%d' % s])
        m.paint(add(c2, add(mul(uv, 1.2), (0, 0.4, 0))), (2.7, 2.8, 2.7), 'wing',
                ['wingH%d' % s])
        m.paint(W(17.5, -34.5), (2.4, 3.2, 2.4), 'night', ['wingH%d' % s])
        for (u, v) in ((27.0, 20.0), (25.0, 14.0), (9.0, -21.0), (13.0, 4.5), (15.0, -27.0)):
            m.sparkle(W(u, v), (s * 0.3, 0.1, 1), size=1, color=('gold', 1))
    # body: fuzzy thorax with a gold crescent, banded abdomen
    m.ell((0, 30.5, -4.5), (3.4, 7.5, 3.4), 'night', 'abdomen', rot=(0, -25, 0))
    for k in range(3):
        m.paint((0, 32.5 - k * 3.3, -3.3 - k * 1.5), (3.8, 0.7, 3.8), 'gold', ['abdomen'])
    m.ell((0, 38.5, -0.5), (5.2, 5.4, 4.8), 'fuzz', 'thorax')
    for k in range(10):
        a = (k * 36) * DEG
        m.sph((math.sin(a) * 5.0, 42.0 + math.cos(a * 2) * 0.4, 1.0 + math.cos(a) * 3.8),
              2.1, 'fuzz', 'thorax')
    p = (0, 37.5, 4.0)
    m.paint(p, (2.2, 2.2, 1.4), 'gold', ['thorax'])
    m.paint(add(p, (0.9, 0.5, 0.3)), (1.9, 1.9, 1.6), 'fuzz', ['thorax'])
    head_c, head_r = (0, 46.0, 3.2), (5.4, 4.8, 4.8)
    m.ell(head_c, head_r, 'fuzz', 'head')
    # feathery antennae arching into a crescent
    for s in (-1, 1):
        pts = [(s * 2.0, 50.0, 3.8), (s * 4.5, 55.0, 3.2), (s * 8.5, 58.5, 2.2),
               (s * 12.5, 59.0, 1.4), (s * 15.0, 56.5, 0.8)]
        m.tube(pts, [0.9, 0.8, 0.7, 0.6, 0.4], 'gold', 'ant%d' % s)
        for k in range(1, 5):
            q = pts[k]
            m.tube([q, add(q, (s * 0.9, 1.8, 0))], [0.5, 0.25], 'gold', 'ant%d' % s)
        m.tube([(s * 2.6, 35.5, 2.0), (s * 4.2, 31.0, 3.5), (s * 4.6, 28.0, 4.0)],
               [0.9, 0.8, 0.6], 'night', 'leg%d' % s)
    eye_pair(m, head_c, head_r, 34, 8, 4.2, 5.0, iris=('night', 1), center=(0, 45, 9),
             turn=12)
    p, n = on(head_c, head_r, (0.1, -0.45, 1))
    m.mouth(p, n, 'smile', w=2.4)
    return m


# --------------------------------------------------------------------------
# 126 SYLVARCH: the great forest stag (BLOOM/BEAST), ELDERWOOD HEART
# --------------------------------------------------------------------------
def foliage(m, c, r, mat, part, seed, n=5, bloom_mat=None, blooms=0):
    """A pad of leaves: a clump of spheres, a few blossoms dotted on top."""
    rnd = Rand(seed)
    m.sph(c, r, mat, part)
    for k in range(n):
        a = 2 * math.pi * k / n + rnd.f()
        q = add(c, (math.cos(a) * r * 0.8, (rnd.f() - 0.3) * r * 0.6, math.sin(a) * r * 0.7))
        m.sph(q, r * (0.55 + 0.25 * rnd.f()), mat, part)
    for k in range(blooms):
        a = 2 * math.pi * (k + 0.3) / max(1, blooms) + rnd.f()
        q = add(c, (math.cos(a) * r * 0.7, r * 0.55, math.sin(a) * r * 0.5 + r * 0.4))
        m.sph(q, r * 0.32, bloom_mat, part)


def sylvarch(g):
    _use(g)
    m = Model('SYLVARCH')
    m.outline = (32, 22, 16)
    m.mat('fur', ['#4a2c1c', '#7a4a2c', '#a8703e', '#d4a468'])
    m.mat('moss', ['#28561c', '#4a8a2c', '#86c24c'])
    m.mat('bark', ['#3a2a20', '#6a5038', '#9a7a56'])
    m.mat('bloom', ['#e67aa8', '#ffd4e8'], emissive=0.2)
    m.mat('glow', ['#b8f070'], emissive=0.9)
    m.eye_dark = (32, 22, 16)
    m.white = (255, 244, 220)
    m.height = 58
    m.max_w = 62
    m.front_yaw = -28
    # legs: strong, dark hooves
    for s in (-1, 1):
        top = (s * 4.2, 18.0, 7.0)
        m.tube([top, (s * 4.5, 9.5, 7.8), (s * 4.6, 2.8, 7.4)], [3.0, 1.9, 1.6], 'fur',
               'legF%d' % s)
        m.ell((s * 4.6, 1.3, 8.0), (1.9, 1.3, 2.3), 'bark', 'legF%d' % s)
        m.ell((s * 4.4, 18.5, -8.5), (3.6, 5.8, 5.2), 'fur', 'legB%d' % s, rot=(0, -10, 0))
        m.tube([(s * 4.6, 14.0, -10.5), (s * 4.8, 7.5, -12.0), (s * 4.8, 2.8, -9.6)],
               [2.4, 1.7, 1.5], 'fur', 'legB%d' % s)
        m.ell((s * 4.8, 1.3, -9.0), (1.8, 1.3, 2.2), 'bark', 'legB%d' % s)
    # body and chest
    m.ell((0, 21.0, -1.5), (7.6, 7.2, 12.5), 'fur', 'body', rot=(0, -5, 0))
    m.ell((0, 23.5, 7.0), (7.4, 8.2, 6.6), 'fur', 'body')
    m.paint((0, 16.0, 0.0), (5.6, 2.6, 11.0), 'fur', ['body'])
    # moss mantle over the back, dotted with flowers
    rnd = Rand(126)
    for k in range(8):
        t = k / 7.0
        q = (1.2 * (rnd.f() - 0.5), 27.5 - 1.2 * math.sin(t * 3), 7.0 - t * 18.0)
        m.sph(q, 3.4 + 0.8 * rnd.f(), 'moss', 'mantle')
    for q in ((2.8, 30.0, -4.0), (-1.8, 30.5, 1.0), (3.8, 29.0, 3.0), (1.0, 28.8, -10.0)):
        m.sph(q, 1.0, 'bloom', 'mantle')
    m.ell((0, 23.5, -13.8), (1.8, 2.6, 1.6), 'fur', 'tail', rot=(0, 30, 0))
    # neck with a mossy beard
    m.tube([(0, 26.0, 8.0), (0, 32.0, 11.0), (0, 37.0, 12.5)], [5.0, 4.2, 3.8], 'fur',
           'body')
    for k in range(6):
        t = k / 5.0
        q = (0.4 * (rnd.f() - 0.5), 35.0 - t * 11.0, 13.8 - t * 0.5)
        m.sph(q, 2.4 + 0.6 * rnd.f(), 'moss', 'beard')
    # head
    head_c, head_r = (0, 40.5, 14.0), (4.8, 4.6, 5.2)
    m.ell(head_c, head_r, 'fur', 'head')
    sn_c, sn_r = (0, 38.6, 18.4), (2.8, 2.6, 3.4)
    m.ell(sn_c, sn_r, 'fur', 'head')
    m.paint(add(sn_c, (0, -0.4, 2.2)), (2.0, 1.6, 1.4), 'bark', ['head'])
    for s in (-1, 1):
        leaf(m, (s * 3.6, 42.5, 12.5), (s * 6.8, 43.5, 11.5), (s * 9.6, 42.5, 10.5), 1.9,
             'fur', 'ear%d' % s, up=(0, 1, 0.6), flat=0.35)
        m.paint((s * 6.6, 43.4, 11.9), (1.7, 0.8, 0.8), 'moss', ['ear%d' % s])
    # antlers: boughs crowned with leaf pads and blossoms
    for s in (-1, 1):
        b = (s * 2.4, 44.0, 12.5)
        main = [b, (s * 5.5, 48.5, 11.0), (s * 9.5, 52.0, 9.0), (s * 14.0, 54.5, 7.0),
                (s * 18.0, 58.0, 5.5)]
        m.tube(main, None, 'bark', 'antler%d' % s, rfn=lambda t: 1.7 - 1.1 * t)
        for (a, tip, r) in ((1, (s * 4.0, 55.5, 13.0), 0.9), (2, (s * 9.0, 60.0, 8.0), 0.8),
                            (3, (s * 20.0, 51.5, 7.5), 0.7), (2, (s * 14.5, 48.0, 10.0), 0.6)):
            m.tube([main[a], lerp(main[a], tip, 0.5), tip], None, 'bark', 'antler%d' % s,
                   rfn=lambda t, r=r: r * (1 - 0.5 * t))
        for k, (q, r, nb) in enumerate(((main[4], 2.6, 2), ((s * 9.0, 60.5, 8.0), 2.2, 1),
                                        ((s * 20.5, 51.5, 7.5), 2.2, 1),
                                        ((s * 4.0, 56.0, 13.0), 1.9, 1),
                                        ((s * 14.5, 48.0, 10.0), 1.7, 0))):
            foliage(m, q, r, 'moss', 'antler%d' % s, seed=60 + k + (10 if s > 0 else 0),
                    n=4, bloom_mat='bloom', blooms=nb)
    eye_pair(m, head_c, head_r, 40, 16, 3.2, 3.2, style='glow', iris=('glow', 0), slant=0.5,
             center=(0, 38, 22), turn=6, pupil='outline')
    m.dot(on(sn_c, sn_r, (0, 0.2, 1))[0], (0, 0.2, 1), w=1.6, h=1.0, minw=2)
    return m


# --------------------------------------------------------------------------
# 127 HOROLOGOS: the clockwork titan (METAL/RELIC), CLOCKWORK SPIRE
# --------------------------------------------------------------------------
def horologos(g):
    _use(g)
    m = Model('HOROLOGOS')
    m.outline = (30, 22, 18)
    m.mat('brass', ['#6a4212', '#a8741e', '#e0b040', '#fff0a4'], spec=0.5)
    m.mat('iron', ['#262a36', '#44505e', '#76808e'])
    m.mat('face', ['#c8bc98', '#f6eed2'])
    m.mat('glow', ['#3ab4e6', '#b6f4ff'], emissive=0.85)
    m.eye_dark = (26, 22, 30)
    m.white = (255, 240, 164)
    m.height = 58
    m.max_w = 60
    m.front_yaw = -24
    # the great escapement wheel turning behind the shoulders
    gear_ring(m, (0, 37.0, -8.0), 13.0, (0.05, 0.1, 1), 14, 'brass', 'gearback', rim=1.3,
              tooth=1.8, spokes=5, hub_mat='iron')
    # column legs with gear knees
    for s in (-1, 1):
        m.box((s * 6.0, 4.5, 0.5), (3.6, 4.5, 4.0), 'iron', 'leg%d' % s, bevel=1.2)
        m.box((s * 6.0, 1.3, 2.5), (4.2, 1.3, 4.8), 'brass', 'leg%d' % s, bevel=0.6)
        gear_ring(m, (s * 9.6, 10.5, 0.8), 2.6, (s, 0, 0.3), 8, 'brass', 'leg%d' % s,
                  rim=0.8, tooth=1.0, spokes=3, hub_mat='iron')
        m.box((s * 5.6, 13.5, 0.0), (3.2, 3.5, 3.4), 'iron', 'leg%d' % s, bevel=1.0)
    # hips + torso: a clock tower, face on the chest
    m.box((0, 18.0, -0.5), (8.2, 2.6, 5.2), 'brass', 'body', bevel=1.0)
    m.box((0, 28.0, -0.5), (9.5, 8.5, 6.2), 'iron', 'body', bevel=2.0)
    m.box((0, 36.0, -0.5), (11.0, 1.6, 7.0), 'brass', 'body', bevel=0.6)
    fc = (0, 28.5, 5.9)
    m.ell(fc, (6.6, 6.6, 1.0), 'brass', 'face')
    m.ell(add(fc, (0, 0, 0.5)), (5.6, 5.6, 0.9), 'face', 'face')
    for k in range(12):
        a = k * 30 * DEG
        q = add(fc, (math.sin(a) * 4.6, math.cos(a) * 4.6, 1.3))
        m.paint(q, (0.55, 0.55, 0.8) if k % 3 else (0.8, 0.8, 0.8), 'iron', ['face'])
    m.tube([add(fc, (0, 0, 1.45)), add(fc, (2.6, 2.2, 1.45))], [0.55, 0.35], 'iron', 'hands')
    m.tube([add(fc, (0, 0, 1.45)), add(fc, (-0.4, 4.0, 1.45))], [0.45, 0.3], 'iron', 'hands')
    m.sph(add(fc, (0, 0, 1.5)), 0.7, 'brass', 'hands')
    # pendulum window below the face
    m.paint((0, 21.0, 5.5), (3.0, 2.6, 1.6), 'glow', ['body'])
    # shoulders: gears + pauldrons, arms like mallets
    for s in (-1, 1):
        gear_ring(m, (s * 12.4, 33.0, 0.0), 4.0, (s, 0.2, 0.2), 10, 'brass', 'sh%d' % s,
                  rim=0.9, tooth=1.2, spokes=4, hub_mat='iron')
        m.ell((s * 11.0, 35.8, -0.5), (4.6, 3.2, 5.0), 'iron', 'sh%d' % s)
        m.tube([(s * 12.5, 31.0, 0.0), (s * 14.0, 24.0, 1.5)], [2.8, 2.6], 'iron', 'arm%d' % s)
        m.sph((s * 14.0, 24.0, 1.5), 2.8, 'brass', 'arm%d' % s)
        m.tube([(s * 14.0, 24.0, 1.5), (s * 14.5, 17.0, 3.0)], [2.6, 2.6], 'iron', 'arm%d' % s)
        m.box((s * 14.6, 13.8, 3.4), (3.4, 3.4, 3.4), 'brass', 'arm%d' % s, bevel=1.2)
    # head: a belfry cupola with a lit visor and a spire
    m.box((0, 40.0, 0.0), (5.4, 3.2, 5.0), 'iron', 'head', bevel=1.2)
    m.ell((0, 43.2, 0.0), (6.0, 3.8, 5.6), 'brass', 'head')
    m.crystal((0, 45.0, 0.0), (0, 55.0, -0.5), 1.8, 'brass', 'head', sides=6, tip_frac=0.8)
    m.sph((0, 50.0, -0.3), 1.2, 'glow', 'head')
    m.box((0, 40.3, 4.6), (4.2, 1.1, 0.6), 'iron', 'head', bevel=0.3)
    for s in (-1, 1):
        m.eye((s * 2.0, 40.3, 5.3), (0, 0, 1), 2.8, 1.8, style='glow', iris=('glow', 1),
              glint=False, minw=2, minh=1)
    # wind-up key on the back
    m.tube([(0, 29.0, -7.0), (0, 29.0, -11.0)], 0.8, 'brass', 'key')
    for s in (-1, 1):
        m.ell((s * 2.2, 29.0, -12.0), (2.2, 1.6, 0.6), 'brass', 'key')
    return m


# --------------------------------------------------------------------------
# 128 SCRIPTORA: serpent of living pages (RELIC/DREAM), DUST LIBRARY
# --------------------------------------------------------------------------
def scriptora(g):
    _use(g)
    hover(g, 'SCRIPTORA', 2)
    m = Model('SCRIPTORA')
    m.outline = (36, 20, 26)
    m.mat('paper', ['#8c7c5c', '#c6b690', '#eee2c2', '#fffaee'], th=[0.18, 0.42, 0.74])
    m.mat('edge', ['#9a8660', '#c2ae84'])
    m.mat('leather', ['#44141e', '#74242e', '#a44242'])
    m.mat('gold', ['#b8841c', '#ffe070'], spec=0.4)
    m.mat('ink', ['#5a2ea4', '#b278f0'], emissive=0.55)
    m.eye_dark = (36, 20, 26)
    m.white = (255, 250, 238)
    m.height = 58
    m.max_w = 62
    m.float_lift = 2
    # coiled body rising in an S, bound like a book: leather above, pages below
    spine = [(1.0, 44.0, 7.0), (-0.5, 39.0, 4.0), (-2.5, 33.5, 1.0), (-1.5, 28.0, -2.0),
             (2.5, 23.5, -3.0), (7.0, 20.5, -1.0), (8.5, 16.5, 2.0), (5.5, 12.0, 4.0),
             (0.0, 9.5, 4.0), (-5.0, 7.5, 1.0), (-7.0, 5.5, -3.5), (-4.0, 4.5, -7.5),
             (2.5, 4.0, -8.5), (8.5, 4.5, -6.5), (12.5, 6.0, -2.5), (13.5, 7.5, 1.5)]
    radii = [3.8, 4.2, 4.5, 4.6, 4.6, 4.5, 4.4, 4.2, 4.0, 3.8, 3.6, 3.3, 2.9, 2.4, 1.6, 0.7]
    m.tube(spine[:9], radii[:9], 'paper', 'body')
    m.tube(spine[8:], radii[8:], 'paper', 'tail')
    # page edges: fine lines running along the body
    for i in range(len(spine) - 1):
        a, b = spine[i], spine[i + 1]
        r = (radii[i] + radii[i + 1]) * 0.5
        part = 'body' if i < 8 else 'tail'
        for f in (0.2, 0.5, 0.8):
            q = lerp(a, b, f)
            for off in (-0.45, 0.45):
                m.paint(add(q, (off * r * 0.4, -r * (0.35 + abs(off) * 0.2), r * 0.3)),
                        (r * 0.18, 0.28, r * 0.9), 'edge', [part])
    # leather cover over the back with gold bands, pages fanned out as a frill
    back = [add(q, (0, r * 0.35, -r * 0.55)) for q, r in zip(spine[:15], radii[:15])]
    m.tube(back, [r * 0.82 for r in radii[:15]], 'leather', 'binding')
    for i in range(1, 14, 2):
        m.tube([lerp(back[i], back[i + 1], 0.35), lerp(back[i], back[i + 1], 0.6)],
               radii[i] * 0.88, 'gold', 'binding')
    for i in range(0, 12):
        a, b = back[i], back[i + 1]
        d = norm(sub(b, a))
        c = add(lerp(a, b, 0.5), (0, radii[i] * 0.75, -radii[i] * 0.2))
        yaw = math.atan2(d[0], d[2]) / DEG
        h = 2.6 + 1.2 * math.sin(i * 1.7)
        m.box(add(c, (0, h * 0.4, 0)), (0.25, h, 1.5), 'paper', 'frill',
              rot=(yaw + 90, 0, 8 * math.sin(i * 2.3)), bevel=0.1)
    # dream runes glowing on the pages
    for (i, off) in ((2, (-3.4, -1.0, 2.5)), (4, (-2.0, -0.6, 3.8)), (6, (2.5, -1.5, 3.4)),
                     (9, (-2.0, -1.0, 3.0)), (11, (-1.2, -0.6, 2.6))):
        m.paint(add(spine[i], off), (0.9, 1.3, 1.2), 'ink', ['body' if i < 8 else 'tail'])
    # head: a bound book snout, jaws of pages, a gold clasp
    hc = (1.5, 47.5, 10.0)
    m.ell(hc, (4.6, 3.6, 5.2), 'leather', 'head')
    m.ell(add(hc, (0, 0.2, 4.2)), (3.4, 2.4, 4.0), 'leather', 'head')
    m.ell(add(hc, (0, -2.8, 3.8)), (3.0, 1.4, 4.2), 'paper', 'jaw', rot=(0, 16, 0))
    m.ell(add(hc, (0, -1.6, 4.4)), (2.6, 1.0, 3.6), 'ink', 'jaw')
    m.box(add(hc, (0, 1.4, 8.2)), (1.2, 1.3, 0.5), 'gold', 'head', bevel=0.3)
    m.tube([add(hc, (0, -1.8, 6.0)), add(hc, (0.5, -3.6, 9.5)), add(hc, (1.4, -2.6, 12.0)),
            add(hc, (1.8, -4.4, 13.2))], [0.8, 0.7, 0.6, 0.4], 'leather', 'tongue',
           flat=0.4, up=(0, 1, 0))
    # quill-feather crest
    for k, (dx, ln) in enumerate(((0.0, 12.0), (2.8, 9.5), (-2.8, 9.5))):
        b = add(hc, (dx, 2.6, -3.0))
        d = norm((dx * 0.14, 0.85, -0.55))
        leaf(m, b, add(b, mul(d, ln * 0.5)), add(b, mul(d, ln)), 1.8, 'paper', 'crest',
             up=(0, 0.3, 1), flat=0.3)
        m.tube([b, add(b, mul(d, ln * 0.95))], [0.35, 0.25], 'gold', 'crest')
    # loose pages drifting round the coils
    for k, (c, yaw, pitch) in enumerate((((-13.0, 30.0, 4.0), 25, 15),
                                        ((15.0, 31.0, -2.0), -20, -10),
                                        ((-13.0, 15.0, 6.0), 40, 10))):
        m.box(c, (2.6, 3.2, 0.25), 'paper', 'page%d' % k, rot=(yaw, pitch, 12), bevel=0.1)
        for j in range(3):
            m.paint(add(c, (0, 1.4 - j * 1.2, 0)), (1.8, 0.28, 1.0), 'edge', ['page%d' % k],
                    rot=(yaw, pitch, 12))
        m.paint(add(c, (0.4, -1.6, 0)), (0.8, 0.8, 1.0), 'ink', ['page%d' % k])
    for s in (-1, 1):
        m.eye(add(hc, (s * 2.6, 1.8, 3.8)), (s * 0.4, 0.3, 1), 3.0, 2.8, style='glow',
              iris=('ink', 1), slant=0.7, glint=True, center=add(hc, (0, 0, 9)))
    return m


# --------------------------------------------------------------------------
# 129 SKYLORN: the sky manta above the clouds (GALE/ASTRAL), SKY ISLE
# --------------------------------------------------------------------------
def skylorn(g):
    _use(g)
    hover(g, 'SKYLORN', 4)
    side_yaw(g, 'SKYLORN', -50.0)
    m = Model('SKYLORN')
    m.outline = (14, 18, 52)
    m.mat('top', ['#141c4c', '#24367c', '#3c5ab0', '#6488dc'])
    m.mat('belly', ['#9cb0e0', '#e6eeff'])
    m.mat('star', ['#fff4b0'], emissive=0.95)
    m.mat('cloud', ['#aab8dc', '#e4ecfa', '#ffffff'])
    m.eye_dark = (14, 18, 52)
    m.white = (255, 255, 255)
    m.height = 56
    m.max_w = 62
    m.float_lift = 3
    # the manta rises nose-up with its starry back to the viewer
    B = frame((0.0, 1.0, 0.2), (0.0, -0.2, 1.0))
    r_, u_, f_ = B
    o = (0.0, 31.0, 0.0)

    def L(x, y, z):
        return local(o, B, x, y, z)
    m.ell_axes(L(0, 0, 0), (mul(r_, 8.0), mul(u_, 3.4), mul(f_, 10.5)), 'top', 'body')
    # wings: broad, sweeping back, tips curled back and trailing cloud
    for s in (-1, 1):
        pts = [L(s * 5.0, 0.2, 8.5), L(s * 14.0, -0.4, 5.5), L(s * 23.0, -2.2, 2.0),
               L(s * 29.5, -4.8, -2.5), L(s * 27.0, -4.0, -4.5), L(s * 20.0, -2.0, -5.5),
               L(s * 13.0, -0.8, -7.0), L(s * 7.0, 0.0, -9.0)]
        m.poly(pts, 'top', 'wing%d' % s, puff=0.45)
        m.tube([L(s * 5.0, 0.4, 7.5), L(s * 15.0, -0.4, 4.6), L(s * 23.0, -2.2, 1.6),
                L(s * 29.5, -4.8, -2.5)], [2.0, 1.5, 1.0, 0.3], 'top', 'wing%d' % s,
               flat=0.5, up=u_)
        m.paint(L(s * 17.0, -1.2, -5.0), (7.0, 2.0, 1.6), 'belly', ['wing%d' % s])
        tip = L(s * 30.0, -5.5, -3.5)
        for k, (dx, dz, r) in enumerate(((0, -1.5, 1.8), (s * -1.6, -3.4, 1.5),
                                         (s * -3.6, -4.6, 1.2))):
            m.sph(add(tip, add(mul(r_, dx), mul(f_, dz))), r, 'cloud', 'cloud%d' % s)
        for (x, z) in ((11.0, 2.5), (18.0, -1.0), (24.0, -1.5), (14.0, -3.5), (8.0, 4.5),
                       (21.0, 1.5)):
            m.sparkle(L(s * x, 0.6, z), u_, size=1, color=('star', 0))
    # cephalic fins framing the face
    for s in (-1, 1):
        m.tube([L(s * 4.0, 0.5, 9.0), L(s * 5.4, 1.2, 12.5), L(s * 4.4, 1.8, 15.0),
                L(s * 2.8, 1.6, 15.4)], [1.7, 1.4, 1.0, 0.4], 'top', 'horn%d' % s,
               flat=0.6, up=u_)
        m.paint(L(s * 4.4, 2.0, 14.6), 1.0, 'star', ['horn%d' % s])
    # tail
    m.tube([L(0, 0, -9.0), L(0.5, -0.6, -16.0), L(-0.5, -1.4, -23.0), L(1.0, -2.0, -28.0)],
           [1.4, 0.9, 0.6, 0.3], 'top', 'tail')
    # a constellation down the back
    for (x, z) in ((0, 5.0), (-2.5, 1.0), (2.0, -2.0), (-1.0, -5.5), (3.5, 3.0)):
        m.paint(L(x, 3.2, z), (0.9, 0.9, 0.9), 'star', ['body'])
    # clouds below
    for k, (x, y, z, r) in enumerate(((-6.0, 4.5, 2.0, 4.2), (0.0, 3.5, 4.0, 5.0),
                                      (6.5, 4.0, 1.0, 4.4), (-11.0, 2.5, 0.0, 3.0),
                                      (11.0, 2.8, 0.5, 3.2), (3.0, 6.5, 1.0, 3.6))):
        m.sph((x, y, z), r, 'cloud', 'clouds')
    for s in (-1, 1):
        p = L(s * 3.4, 2.0, 9.4)
        n = norm(add(add(mul(u_, 0.7), mul(f_, 0.6)), mul(r_, s * 0.35)))
        m.eye(p, n, 3.2, 3.4, iris=('top', 3), center=L(0, 3, 14))
    m.mouth(L(0, 1.6, 11.2), norm(add(u_, f_)), 'smile', w=3.0)
    return m
