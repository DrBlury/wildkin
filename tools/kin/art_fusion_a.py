"""Art for the fusion kin 130-151 (tools/kin/fusion_a.py). Owner: KIN-D.

Every function takes `g`, the tools/gen_monsters.py module (Model, the
shared helpers such as eye_pair/leaf/flame, and the overworld tables), and
returns a gen_monsters.Model. Fusion kin are woven from two energies, so each
design mixes two themes and carries a signature glow.

Stdlib only; everything is deterministic.
"""

import math

DEG = math.pi / 180.0


# ---- small vector helpers (same conventions as gen_monsters) -------------
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


def overworld(g, m, lift=0, side_yaw=None):
    """Hovering lift / profile yaw for the overworld frames (the tables live
    in gen_monsters and are keyed by name)."""
    if lift:
        g.OW_FLOAT[m.name] = lift
    if side_yaw is not None:
        g.OW_SIDE_YAW[m.name] = side_yaw


def ring_paint(m, c, r, n, mat, parts, rad=0.6, axis_u=(1, 0, 0),
               axis_v=(0, 1, 0), start=0.0, span=360.0):
    """A ring of small paint dots (rivets, star chains, seams)."""
    for k in range(n):
        a = (start + span * k / float(n)) * DEG
        p = add(c, add(mul(axis_u, math.cos(a) * r), mul(axis_v, math.sin(a) * r)))
        m.paint(p, rad, mat, parts)


def disk(m, c, n, r, mat, part, th=0.35):
    """A thin disk (coin, plate, lens) centred at c facing along n."""
    n = norm(n)
    yaw = math.atan2(n[0], n[2]) / DEG
    pitch = -math.asin(max(-1.0, min(1.0, n[1]))) / DEG
    m.ell(c, (r, r, th), mat, part, rot=(yaw, pitch, 0))


def puff_cloud(m, c, r, mat, part, n=6, seed=1, spread=1.0):
    """A little cumulus: a few overlapping spheres around c."""
    rnd = _Rand(seed)
    m.sph(c, r, mat, part)
    for k in range(n):
        a = 2 * math.pi * k / n + rnd.f() * 0.6
        q = add(c, (math.cos(a) * r * 0.75 * spread, (rnd.f() - 0.3) * r * 0.5,
                    math.sin(a) * r * 0.55 * spread))
        m.sph(q, r * (0.55 + 0.25 * rnd.f()), mat, part)


class _Rand:
    def __init__(self, seed):
        self.s = (seed * 2654435761 + 12345) & 0x7fffffff

    def f(self):
        self.s = (self.s * 1103515245 + 12345) & 0x7fffffff
        return (self.s >> 8) / float(1 << 23)


# ==========================================================================
# 130 STEAMOTH  GALE/BLAZE  (BLAZE + TIDE)
# A hawk-moth whose wings are brass frames glazed with steam-fogged
# portholes; a copper boiler thorax with a glowing firebox, a collar of
# steam, and exhaust puffs trailing from its abdomen.
# ==========================================================================
def steamoth(g):
    m = g.Model('STEAMOTH')
    m.outline = (46, 24, 22)
    m.mat('brass', ['#6c4216', '#ac7226', '#dea646', '#fff0a4'], spec=0.5)
    m.mat('copper', ['#582a26', '#924632', '#c8703e'])
    m.mat('steam', ['#7894b4', '#b4cce2', '#eef6fb'])
    m.mat('mist', ['#7894b4', '#b4cce2'])
    m.mat('ember', ['#ff7c1c', '#ffe066'], emissive=0.85)
    m.eye_dark = (40, 22, 22)
    m.white = (238, 246, 251)
    m.height = 54
    m.max_w = 62
    m.float_lift = 3
    m.front_yaw = -24
    overworld(g, m, lift=4, side_yaw=-58)
    # ---- wings: long swept hawk-moth forewings + small hindwings; fogged
    #      steam-glass membranes stretched on a fan of brass ribs
    root_y = 27.0
    for s in (-1, 1):
        root = (s * 2.2, root_y, -3.0)
        uvec = norm((s * 1.0, 0, -0.32))

        def W(u, v, root=root, uvec=uvec):
            return add(root, add(mul(uvec, u), (0, v, 0)))
        fore = [(0, 2.0), (6, 7.5), (14, 13.0), (22, 18.0), (28, 21.5),
                (31.5, 22.0), (33.0, 18.5), (30.5, 13.0), (27.5, 10.5),
                (24.0, 6.0), (20.0, 4.0), (16.0, 0.5), (10, -1.5), (4, -2.0)]
        m.poly([W(u, v) for u, v in fore], 'steam', 'wingF%d' % s, puff=0.3)
        hind = [(0, -1.0), (7, -1.5), (13.5, -4.5), (17.5, -9.5), (15.5, -13.0),
                (12.5, -13.8), (9.5, -16.0), (5, -13.0), (1.5, -7.5)]
        m.poly([W(u, v) for u, v in hind], 'steam', 'wingH%d' % s, puff=0.3)
        m.group('wingH%d' % s, 'wingF%d' % s)
        # brass spar along the leading edge + fanned ribs
        m.tube([W(0, 2.0), W(8, 8.8), W(18, 15.2), W(28, 21.3), W(32.2, 21.0)],
               [1.6, 1.3, 1.1, 0.85, 0.5], 'brass', 'wingF%d' % s)
        for (u, v) in ((32.6, 18.2), (27.5, 10.5), (20.0, 4.0), (11.0, -1.0)):
            m.tube([W(1.0, 1.0), W(u * 0.55, v * 0.55 + 0.9), W(u, v)],
                   [0.8, 0.65, 0.45], 'brass', 'wingF%d' % s)
        for (u, v) in ((16.5, -9.5), (10.0, -15.0), (3.5, -10.5)):
            m.tube([W(1.0, -0.8), W(u, v)], [0.75, 0.45], 'brass',
                   'wingH%d' % s)
        # scalloped trailing edge: fogged cells between the ribs
        for (u, v, r) in ((29.5, 13.0, 1.9), (23.5, 7.0, 2.1), (16.0, 1.4, 2.0),
                          (13.5, -12.0, 1.8), (6.5, -13.2, 1.8)):
            m.paint(W(u, v), (r, r, 2.6), 'mist', ['wingF%d' % s, 'wingH%d' % s])
    # ---- abdomen: copper, banded with brass, tipped with an exhaust vent
    m.ell((0, 19.0, -5.0), (3.8, 7.0, 3.8), 'copper', 'abdomen', rot=(0, -34, 0))
    for k in range(3):
        m.paint((0, 21.5 - k * 3.0, -3.4 - k * 1.9), (4.3, 0.75, 4.3), 'brass',
                ['abdomen'])
    m.tube([(0, 13.8, -8.8), (0, 12.4, -10.2)], [1.9, 1.5], 'brass', 'abdomen')
    # steam exhaust drifting from the vent
    puff_cloud(m, (1.5, 10.0, -12.0), 2.4, 'steam', 'exhaust', n=4, seed=3)
    puff_cloud(m, (4.5, 6.2, -13.0), 3.0, 'steam', 'exhaust', n=5, seed=5)
    m.sph((8.5, 3.6, -13.0), 2.0, 'steam', 'exhaust')
    # ---- boiler thorax with a firebox grate
    m.ell((0, 27.0, -0.8), (5.6, 5.8, 5.2), 'copper', 'thorax')
    m.paint((0.6, 24.8, 3.8), (3.4, 2.8, 2.4), 'brass', ['thorax'])
    m.paint((0.6, 24.8, 4.0), (2.7, 2.1, 2.4), 'ember', ['thorax'])
    for k in (-1, 0, 1):
        m.paint((0.6 + k * 1.3, 24.8, 4.4), (0.3, 2.4, 2.2), 'copper', ['thorax'])
    for k in range(10):
        a = k * 36 * DEG
        m.paint((math.sin(a) * 5.6, 22.4, -0.8 + math.cos(a) * 5.2), 0.55,
                'brass', ['thorax'])
    # collar of steam
    for k in range(11):
        a = (k * 32.7) * DEG
        m.sph((math.sin(a) * 5.0, 31.0 + math.cos(a * 2) * 0.4,
               0.2 + math.cos(a) * 3.8), 2.2, 'steam', 'collar')
    # little legs folded against the boiler
    for s in (-1, 1):
        m.tube([(s * 3.6, 23.5, 2.6), (s * 5.0, 21.0, 4.0),
                (s * 3.8, 19.4, 4.6)], [0.9, 0.75, 0.6], 'brass', 'arm%d' % s)
    # ---- dark copper face with brass goggle rims, feathered antennae
    head_c, head_r = (0, 35.0, 3.0), (5.4, 4.8, 4.8)
    m.ell(head_c, head_r, 'copper', 'head')
    for s in (-1, 1):
        base = (s * 1.8, 38.6, 3.2)
        pts = [base, (s * 4.2, 43.5, 3.6), (s * 8.0, 47.5, 2.8),
               (s * 12.0, 49.0, 1.6), (s * 14.5, 48.0, 0.8)]
        m.tube(pts, [0.9, 0.8, 0.7, 0.55, 0.4], 'brass', 'ant%d' % s)
        for k in range(1, 4):
            q = lerp(pts[k], pts[k + 1], 0.3)
            m.tube([q, add(q, (s * 0.6, 2.0, 0.4))], [0.45, 0.25], 'brass',
                   'ant%d' % s)
            m.tube([q, add(q, (s * 1.6, -1.2, 0.3))], [0.45, 0.25], 'brass',
                   'ant%d' % s)
        m.sph(add(pts[-1], (s * 1.2, 0.6, 0)), 1.3, 'steam', 'ant%d' % s)
    for s in (-1, 1):
        a = (34 * s) * DEG
        e = 10 * DEG
        d = (math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e))
        p, n = g.surf(head_c, head_r, d)
        m.paint(p, (2.9, 3.2, 1.8), 'brass', ['head'])
    g.eye_pair(m, head_c, head_r, 34, 10, 4.2, 4.8, style='iris',
               iris=('ember', 0), center=(0, 34, 9), turn=6)
    p, n = g.on(head_c, head_r, (0.1, -0.5, 1))
    m.mouth(p, n, 'smile', w=2.4, color=('brass', 3))
    return m


# ==========================================================================
# 131 VOLTORTLE  SPARK/STONE  (SPARK + STONE)
# A basalt tortoise with a copper lightning rod rising from its shell; the
# charge it catches runs down glowing seams to a grounding chain on its tail.
# ==========================================================================
def voltortle(g):
    m = g.Model('VOLTORTLE')
    m.outline = (26, 24, 36)
    m.mat('stone', ['#34363f', '#50545f', '#767c88', '#a6acb6'])
    m.mat('skin', ['#6a5a34', '#a08a4c', '#d4bc78'])
    m.mat('copper', ['#7a3e1e', '#c0702e', '#f0a860'], spec=0.6)
    m.mat('spark', ['#ffd23a', '#fffbd0'], emissive=0.8)
    m.eye_dark = (26, 22, 30)
    m.white = (255, 251, 208)
    m.height = 46
    m.max_w = 60
    m.front_yaw = -34
    # ---- legs: four stout columns with stone claws
    for s in (-1, 1):
        for zz, nm in ((7.0, 'legF'), (-7.5, 'legB')):
            top = (s * 8.0, 8.5, zz)
            m.tube([top, (s * 8.6, 4.5, zz + 0.4), (s * 8.8, 2.2, zz + 0.6)],
                   [3.3, 3.0, 3.2], 'skin', '%s%d' % (nm, s))
            m.ell((s * 8.8, 1.6, zz + 1.0), (3.4, 1.6, 3.6), 'skin', '%s%d' % (nm, s))
            for t in (-1, 0, 1):
                m.crystal((s * 8.8 + t * 1.5, 1.2, zz + 3.4),
                          (s * 8.8 + t * 1.8, 0.4, zz + 5.0), 0.7, 'stone',
                          '%s%d' % (nm, s), sides=4, tip_frac=0.8)
            for k in range(3):
                m.paint((s * (10.6 + 0.3 * k), 5.5 - k * 1.4, zz + (k - 1) * 1.2), 0.6,
                        'skin', ['%s%d' % (nm, s)])
    # ---- tail with a grounding chain trailing to the floor
    m.tube([(0, 7.5, -12.5), (0.4, 5.5, -15.5), (1.0, 3.6, -17.0)], [2.2, 1.6, 0.9],
           'skin', 'tail')
    for k in range(6):
        q = (1.2 + k * 0.9, max(0.7, 3.2 - k * 0.55), -17.6 - k * 1.3)
        m.ell(q, (0.75, 0.75, 0.75), 'copper', 'tail')
    # ---- shell: basalt dome over a skirt of marginal plates
    sh_c, sh_r = (0, 11.0, -0.5), (11.0, 9.0, 13.0)
    m.ell(sh_c, sh_r, 'stone', 'shell')
    m.ell((0, 7.4, -0.5), (12.6, 2.6, 14.6), 'stone', 'shell')
    for k in range(14):
        a = 2 * math.pi * k / 14
        m.sph((math.sin(a) * 12.4, 6.6, -0.5 + math.cos(a) * 14.2), 1.7, 'stone', 'shell')
    # raised scutes (faceted rock plates)
    scutes = [(0, 1, 0, 3.8, 5), (0, 0.8, 0.62, 3.2, 7), (0, 0.8, -0.62, 3.2, 9),
              (0.72, 0.62, 0.2, 3.0, 11), (-0.72, 0.62, 0.2, 3.0, 13),
              (0.7, 0.55, -0.45, 3.0, 15), (-0.7, 0.55, -0.45, 3.0, 17),
              (0.6, 0.45, 0.7, 2.8, 19), (-0.6, 0.45, 0.7, 2.8, 21)]
    for dx, dy, dz, r, seed in scutes:
        p, n = g.surf(sh_c, sh_r, (dx, dy, dz))
        m.rock(add(p, mul(n, -0.9)), (r, r * 0.55, r), 'stone', 'shell', seed=seed,
               n=12, jitter=0.12)
    # glowing grounding seams: thin zigzags from the rod base to the rim
    for k in range(6):
        a = (30 + 60 * k) * DEG
        pts = []
        for i in range(7):
            t = i / 6.0
            el = (78 - 66 * t) * DEG
            wig = (0.16 if i % 2 else -0.16) * (1 if k % 2 else -1)
            d = (math.cos(el) * math.sin(a + wig), math.sin(el),
                 math.cos(el) * math.cos(a + wig))
            p, n = g.surf(sh_c, sh_r, d)
            pts.append(add(p, mul(n, 0.3)))
        for i in range(len(pts) - 1):
            for j in range(6):
                m.paint(lerp(pts[i], pts[i + 1], j / 6.0), (0.55, 0.55, 1.6), 'spark',
                        ['shell'])
    # ---- the lightning rod: collar, insulators, a ball of charge, a spike
    top = (0, 19.4, -0.5)
    m.ell(add(top, (0, 0.2, 0)), (3.6, 1.5, 3.6), 'copper', 'rod')
    m.tube([top, add(top, (0, 14.0, 0))], [1.3, 1.1], 'copper', 'rod')
    for y, r in ((3.2, 2.8), (6.0, 2.4)):
        m.ell(add(top, (0, y, 0)), (r, 0.9, r), 'stone', 'rod')
    m.sph(add(top, (0, 10.0, 0)), 2.8, 'spark', 'rod')
    for s in (-1, 1):
        m.tube([add(top, (0, 12.4, 0)), add(top, (s * 2.6, 13.4, 0)),
                add(top, (s * 3.0, 15.8, 0))], [0.7, 0.6, 0.35], 'copper', 'rod')
    m.crystal(add(top, (0, 13.0, 0)), add(top, (0, 18.5, 0)), 1.1, 'copper', 'rod',
              sides=4, tip_frac=0.7)
    # a crackle leaping off the tip
    g.zigzag(m, [add(top, (0.6, 17.4, 0)), add(top, (3.4, 18.6, 0.4)),
                 add(top, (2.6, 20.2, 0.5)), add(top, (6.0, 21.8, 0.6))],
             [0.8, 0.7, 0.6, 0.2], 'spark', 'bolt', flat=0.7)
    # ---- neck and beaked head, heavy brow
    m.tube([(0, 8.0, 11.0), (0, 10.5, 14.8), (0, 13.0, 17.6)], [3.6, 3.3, 3.1],
           'skin', 'head')
    head_c, head_r = (0, 15.0, 19.4), (4.8, 4.2, 5.0)
    m.ell(head_c, head_r, 'skin', 'head')
    m.tube([(0, 14.6, 22.8), (0, 13.4, 24.6), (0, 11.8, 24.9)], [2.4, 1.6, 0.5],
           'stone', 'head')
    for s in (-1, 1):
        m.ell((s * 2.8, 18.4, 20.0), (2.2, 1.1, 2.2), 'stone', 'head')
    g.eye_pair(m, head_c, head_r, 42, 12, 3.8, 3.6, style='sharp',
               iris=('spark', 0), slant=0.5, lid=1, center=(0, 14, 26), turn=-4)
    p, n = g.on(head_c, head_r, (0.25, -0.45, 1))
    m.mouth(p, n, 'line', w=2.8)
    return m


# ==========================================================================
# 132 EMBERIME  BLAZE/FROST  (BLAZE + FROST)
# A slender fox split down the middle: ember-red on its left, rime-blue on
# its right, one tail of living flame and one of fluffy frost tipped with
# icicles.  Heat flows from one tail to the other.
# ==========================================================================
def emberime(g):
    m = g.Model('EMBERIME')
    m.outline = (44, 20, 40)
    m.mat('fur', ['#7a1e2c', '#c23a2c', '#ec6a36', '#ffae6c'])
    m.mat('rime', ['#3e5a9c', '#7aa8dc', '#d6f0ff'])
    m.mat('flame', ['#e8420c', '#ff8a1e', '#ffd040'], emissive=0.3)
    m.mat('ice', ['#58c4ee', '#d6f0ff'], emissive=0.35)
    m.eye_dark = (40, 18, 36)
    m.white = (255, 246, 208)
    m.height = 50
    m.max_w = 60
    m.front_yaw = -28

    def split(parts):
        # everything on the fox's right side (-X) is rime
        m.paint((-300.0, 20.0, 0.0), (300.0, 600.0, 600.0), 'rime', parts)
    # ---- legs (slim, fox-length)
    for s in (-1, 1):
        m.tube([(s * 3.0, 12.5, 6.5), (s * 3.2, 7.0, 7.4), (s * 3.2, 2.0, 8.0)],
               [2.1, 1.5, 1.4], 'fur', 'legF%d' % s)
        m.sph((s * 3.2, 1.6, 8.7), 1.8, 'fur', 'legF%d' % s)
        m.ell((s * 3.4, 12.5, -8.5), (2.9, 4.4, 4.4), 'fur', 'legB%d' % s)
        m.tube([(s * 3.6, 10.0, -9.5), (s * 3.8, 5.5, -11.6), (s * 3.8, 2.0, -10.2)],
               [2.3, 1.5, 1.4], 'fur', 'legB%d' % s)
        m.sph((s * 3.8, 1.6, -9.5), 1.8, 'fur', 'legB%d' % s)
    # ---- torso and chest
    m.ell((0, 13.5, -2.0), (5.0, 5.0, 9.8), 'fur', 'body', rot=(0, -6, 0))
    m.ell((0, 15.0, 5.5), (5.2, 5.8, 5.0), 'fur', 'body')
    m.tube([(0, 16, 6.5), (0, 20, 8.2), (0, 23.5, 9.2)], [3.8, 3.4, 3.1], 'fur', 'body')
    # ---- head
    head_c, head_r = (0, 26.5, 10.0), (5.8, 5.1, 5.3)
    m.ell(head_c, head_r, 'fur', 'head')
    mz_c, mz_r = (0, 24.8, 14.5), (2.7, 2.1, 3.3)
    m.ell(mz_c, mz_r, 'fur', 'head')
    for s in (-1, 1):
        m.tube([(s * 3.0, 29.8, 9.0), (s * 4.8, 34.8, 8.2), (s * 6.0, 39.8, 7.2)],
               [3.0, 2.1, 0.3], 'fur', 'ear%d' % s, flat=0.42, up=(0, 0.2, 1))
        m.tube([(s * 4.8, 25.2, 9.4), (s * 7.4, 23.6, 8.2), (s * 8.6, 22.4, 7.2)],
               [1.8, 1.1, 0.2], 'fur', 'head', flat=0.5, up=(0, 0, 1))
    # ear tips: an ember on the left ear, an icicle on the right
    g.flame(m, (5.8, 38.6, 7.3), 5.5, 1.9, 'ear1', mats=('flame', 'flame', 'flame'),
            up=(0.25, 1, 0), tongues=1, inner=False, core=False, seed=4)
    m.crystal((-5.7, 38.4, 7.3), (-7.0, 44.0, 6.8), 0.95, 'ice', 'ear-1', sides=4,
              tip_frac=0.6)
    split(['body', 'head', 'legF-1', 'legB-1', 'ear-1'])
    # ---- the tails, fanned in a V behind the rump
    # fire tail: fur root bursting into a tall flame on the left
    m.tube([(1.0, 15.0, -11.0), (4.5, 18.0, -15.0), (7.5, 22.5, -17.5)],
           [2.2, 3.0, 3.1], 'fur', 'tailA')
    g.flame(m, (7.8, 21.5, -17.5), 21.0, 5.6, 'tailA', mats=('flame', 'flame', 'flame'),
            up=(0.3, 1, -0.1), face=(0.4, 0.1, 1), tongues=3, seed=11)
    g.flame(m, (7.8, 22.0, -17.3), 13.0, 3.2, 'tailA', mats=('fur', 'fur', 'fur'),
            up=(0.25, 1, -0.1), face=(0.4, 0.1, 1), tongues=2, seed=12, inner=False,
            core=False)
    # frost tail: a big bushy rime brush with icicles hanging beneath and
    #      a frosted tip, swept back and up
    tb = [(-1.0, 15.0, -11.0), (-4.0, 18.0, -16.5), (-6.0, 23.5, -21.0),
          (-6.2, 29.5, -23.0), (-5.0, 34.0, -22.2)]
    m.tube(tb, [2.2, 3.8, 4.6, 4.2, 2.4], 'rime', 'tailB')
    m.paint(tb[4], (3.4, 3.4, 3.4), 'ice', ['tailB'])
    m.crystal(add(tb[4], (0, 1.0, 0)), add(tb[4], (0.4, 6.0, 0.2)), 1.2, 'ice', 'tailB',
              sides=4, tip_frac=0.55)
    for k, (t, ln) in enumerate(((0.35, 3.4), (0.5, 4.2), (0.65, 3.6))):
        q = lerp(tb[1], tb[3], t)
        base = add(q, (-2.0, -2.4, 2.0))
        m.crystal(add(base, (0, 1.4, 0)), add(base, (-0.6, -ln, 0.8)), 0.8, 'ice',
                  'tailB', sides=4, tip_frac=0.7)
    # ---- face: a mismatched pair of eyes (ember left, ice right)
    for s, iris in ((1, ('flame', 0)), (-1, ('ice', 0))):
        a = (32 * s) * DEG
        e = 14 * DEG
        d = (math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e))
        p, n = g.surf(head_c, head_r, d)
        m.eye(p, n, 3.8, 4.6, style='iris', iris=iris, slant=0.45, center=(0, 25, 19))
    m.dot(g.on(mz_c, mz_r, (0, 0.35, 1))[0], (0, 0.2, 1), w=1.8, h=1.2, minw=2)
    p, n = g.on(mz_c, mz_r, (0, -0.35, 1))
    m.mouth(p, n, 'smile', w=2.6, fang=1)
    return m


# ==========================================================================
# 133 OSSIFLORA  HOLLOW/BLOOM  (HOLLOW + BLOOM)
# A deer of old bone whose ribcage is a flowerbed; moss wraps its legs,
# blossoms crown its antlers and green light glows in its skull.
# ==========================================================================
def ossiflora(g):
    m = g.Model('OSSIFLORA')
    m.outline = (40, 34, 30)
    m.mat('bone', ['#6e6452', '#a89c84', '#d8ceb4', '#f6f0de'])
    m.mat('moss', ['#2c5428', '#4c8436', '#88bc58'])
    m.mat('deep', ['#1e3a22', '#2c5428'])
    m.mat('bloom', ['#b83c6c', '#ee7ca8', '#ffd2e6'])
    m.mat('glow', ['#3cd08c', '#b4ffd8'], emissive=0.7)
    m.mat('socket', ['#1e1a1c'])
    m.eye_dark = (30, 26, 28)
    m.white = (246, 240, 222)
    m.height = 56
    m.max_w = 58
    m.front_yaw = -28
    # ---- legs: slender bone, moss-wrapped thighs, dark hooves
    for s in (-1, 1):
        for zz, nm, up in ((7.0, 'legF', 17.0), (-8.0, 'legB', 18.0)):
            top = (s * 3.8, up, zz)
            knee = (s * 4.0, 9.5, zz + (1.0 if nm == 'legF' else -1.6))
            foot = (s * 4.0, 1.8, zz + 0.4)
            m.tube([top, knee], [2.4, 1.2], 'moss', '%s%d' % (nm, s))
            m.tube([knee, foot], [1.1, 0.9], 'bone', '%s%d' % (nm, s))
            m.sph(knee, 1.35, 'bone', '%s%d' % (nm, s))
            m.ell(add(foot, (0, -0.4, 0.6)), (1.3, 1.2, 1.7), 'bone', '%s%d' % (nm, s))
            m.paint(add(foot, (0, -0.8, 0.6)), (1.6, 0.7, 2.0), 'moss', ['%s%d' % (nm, s)])
    # ---- the ribcage: a bone barrel with dark gaps between the ribs, and a
    #      flowerbed spilling out of the gaps
    body_c, body_r = (0, 19.0, -0.5), (5.4, 5.2, 10.0)
    m.ell(body_c, body_r, 'bone', 'body')
    gaps = (4.6, 1.4, -1.8, -5.0)
    for z in gaps:
        m.paint((0, 17.6, z), (7.0, 4.2, 0.85), 'deep', ['body'], rot=(-10, 0, 0))
    m.paint((0, 13.8, -0.5), (6.0, 1.8, 8.0), 'deep', ['body'])
    rnd = _Rand(7)
    for k, z in enumerate(gaps * 3):
        a = (rnd.f() * 150 - 75) * DEG
        s = 1 if k % 2 == 0 else -1
        d = (s * math.cos(a) * 0.9, math.sin(a) * 0.6 - 0.1, z / 10.0)
        p, n = g.surf(body_c, body_r, d)
        if k % 4 == 3:
            g.leaf(m, p, add(p, mul(n, 1.3)), add(p, mul(n, 2.5)), 0.9, 'moss',
                   'flowers', up=(0, 1, 0), flat=0.4)
        else:
            m.sph(add(p, mul(n, 0.5)), 0.9 + 0.35 * rnd.f(), 'bloom', 'flowers')
            m.paint(add(p, mul(n, 1.2)), 0.42, 'glow', ['flowers'])
    # spine
    for k in range(9):
        z = 9.0 - k * 2.4
        m.sph((0, 24.0 - abs(z + 1) * 0.06, z), 1.3, 'bone', 'spine')
    # pelvis and shoulder blades
    m.ell((0, 20.5, -8.8), (4.4, 3.4, 3.4), 'bone', 'pelvis')
    for s in (-1, 1):
        m.ell((s * 4.2, 21.5, 5.8), (1.4, 3.6, 2.6), 'bone', 'ribs', rot=(0, 0, s * 12))
    # flower-tuft tail
    g.seedball(m, (0, 22.5, -12.5), 1.6, 'bloom', 'tail', n=14, fil=0.5, tip=0.7, seed=5)
    # ---- neck: vertebrae with a moss mane
    neck = [(0, 23.5, 8.0), (0, 27.5, 10.0), (0, 31.5, 11.2), (0, 35.0, 11.8)]
    m.tube(neck, [2.0, 1.8, 1.7, 1.6], 'moss', 'neck')
    for q in neck:
        m.sph(add(q, (0, 0.4, -1.3)), 1.2, 'bone', 'neck')
    for k in range(3):
        m.sph(add(neck[k + 1], (0.9, -0.4, 1.2)), 0.9, 'bloom', 'neck')
    # ---- the skull
    head_c, head_r = (0, 37.5, 12.8), (3.6, 3.4, 4.0)
    m.ell(head_c, head_r, 'bone', 'head')
    sn = [(0, 37.0, 15.0), (0, 35.8, 18.0), (0, 34.8, 19.8)]
    m.tube(sn, [2.8, 2.1, 1.6], 'bone', 'head')
    m.dot((0, 35.6, 20.9), (0, 0.1, 1), w=1.4, h=1.0, color='eye', minw=2)
    for s in (-1, 1):
        p, n = g.on(head_c, head_r, (s * 0.62, 0.18, 0.7))
        m.paint(p, (1.9, 1.7, 1.4), 'socket', ['head'])
        m.eye(p, n, 2.4, 2.6, style='glow', iris=('glow', 1), glint=False,
              center=(0, 36, 22), minw=2, minh=2)
        # small ears
        m.tube([(s * 2.8, 39.5, 11.0), (s * 5.4, 40.6, 9.8), (s * 6.8, 40.4, 9.0)],
               [1.4, 1.0, 0.2], 'bone', 'head', flat=0.45, up=(0, 0.3, 1))
    # ---- antlers of bone crowned with blossoms and hanging vines
    for s in (-1, 1):
        b = (s * 1.8, 40.2, 11.8)
        p1 = (s * 4.0, 45.0, 10.8)
        p2 = (s * 6.4, 49.5, 9.0)
        p3 = (s * 7.2, 54.0, 8.0)
        m.tube([b, p1, p2, p3], [1.1, 0.9, 0.75, 0.45], 'bone', 'antler%d' % s)
        tines = [(p1, (s * 7.8, 46.8, 12.2)), (p2, (s * 10.0, 51.5, 9.4)),
                 (lerp(p1, p2, 0.5), (s * 3.2, 51.0, 11.2))]
        for a0, a1 in tines:
            m.tube([a0, a1], [0.7, 0.4], 'bone', 'antler%d' % s)
        for q, r in ((p3, 1.7), (tines[0][1], 1.4), (tines[1][1], 1.5),
                     (tines[2][1], 1.2)):
            m.sph(q, r, 'bloom', 'antler%d' % s)
            m.paint(add(q, (0, 0.3, 0.6)), r * 0.45, 'glow', ['antler%d' % s])
        g.leaf(m, p1, add(p1, (s * 1.0, -1.8, 1.4)), add(p1, (s * 1.4, -4.2, 2.0)),
               1.0, 'moss', 'antler%d' % s, up=(s, 0, 0.3), flat=0.3)
        m.tube([p2, add(p2, (s * 0.6, -3.0, 0.4)), add(p2, (s * 0.2, -6.0, 0.8))],
               [0.45, 0.4, 0.3], 'moss', 'antler%d' % s)
    return m


# ==========================================================================
# 134 COGHIVE  METAL/SWARM  (METAL + SWARM)
# A clockwork queen bee rising from a riveted iron skep that walks on six
# jointed legs; honey-light glows in the hive door, a cog crown turns on her
# head and three wind-up drones orbit her.
# ==========================================================================
def _clock_bee(m, c, s, part, scale=1.0):
    """A tiny wind-up drone: striped body, glass wings, a key on its back."""
    m.ell(c, (1.5 * scale, 1.3 * scale, 2.0 * scale), 'brass', part)
    m.paint(add(c, (0, 0, -0.5 * scale)), (1.7 * scale, 1.5 * scale, 0.45 * scale), 'iron',
            [part])
    m.sph(add(c, (0, 0.2 * scale, 1.9 * scale)), 1.1 * scale, 'iron', part)
    for k in (-1, 1):
        m.ell(add(c, (k * 1.6 * scale, 1.4 * scale, -0.4 * scale)),
              (1.5 * scale, 0.5 * scale, 1.1 * scale), 'glass', part, rot=(0, 0, k * 30))
    m.tube([add(c, (0, 1.2 * scale, -0.9 * scale)), add(c, (0, 2.4 * scale, -1.3 * scale))],
           [0.35 * scale, 0.35 * scale], 'brass', part)
    m.ell(add(c, (0, 2.8 * scale, -1.4 * scale)), (0.9 * scale, 0.6 * scale, 0.3 * scale),
          'brass', part)


def coghive(g):
    m = g.Model('COGHIVE')
    m.outline = (28, 24, 30)
    m.mat('iron', ['#2e3440', '#4c5668', '#7a8699', '#b8c4d0'], spec=0.4)
    m.mat('brass', ['#7a4e14', '#c08a28', '#f4d060'], spec=0.5)
    m.mat('honey', ['#ff9a1a', '#ffe070'], emissive=0.8)
    m.mat('glass', ['#9cc4dc', '#e4f4fc'])
    m.eye_dark = (26, 20, 24)
    m.white = (244, 250, 252)
    m.height = 56
    m.max_w = 60
    m.front_yaw = -26
    # ---- six jointed legs carrying the hive
    for s in (-1, 1):
        for k, zz in enumerate((5.5, 0.0, -5.5)):
            hip = (s * 6.0, 6.0, zz)
            knee = (s * 12.0, 7.6, zz * 1.35)
            foot = (s * 13.2, 0.8, zz * 1.5 + 1.0)
            nm = 'leg%s%d' % ('FMB'[k], s)
            m.tube([hip, knee], [1.1, 0.9], 'iron', nm)
            m.sph(knee, 1.2, 'brass', nm)
            m.tube([knee, foot], [0.9, 0.55], 'iron', nm)
    # ---- the skep: stacked riveted rings, iron and brass
    rings = [(4.4, 7.8), (6.8, 9.0), (9.3, 9.2), (11.8, 8.7), (14.2, 7.6), (16.3, 6.0),
             (18.0, 4.0)]
    for i, (y, r) in enumerate(rings):
        m.ell((0, y, 0), (r, 1.75, r * 0.95), 'brass' if i % 2 else 'iron', 'hive')
    for i, (y, r) in enumerate(rings[:-1]):
        if i % 2 == 0:
            for k in range(10):
                a = (k * 36 + 18) * DEG
                m.paint((math.sin(a) * r, y + 0.2, math.cos(a) * r * 0.95), 0.5, 'brass',
                        ['hive'])
    # glowing door with a brass sill
    m.paint((0, 7.0, 8.6), (3.0, 3.4, 2.4), 'iron', ['hive'])
    m.paint((0, 6.6, 9.0), (2.2, 2.6, 2.4), 'honey', ['hive'])
    m.paint((0, 4.8, 9.0), (2.6, 0.8, 2.4), 'brass', ['hive'])
    # honey drips over the lower rim
    for x, ln in ((-4.5, 2.0), (4.4, 1.6)):
        z = math.sqrt(max(0.0, 8.4 ** 2 - x * x))
        m.tube([(x, 5.2, z + 0.1), (x, 5.2 - ln, z + 0.3)], [0.6, 0.5], 'honey', 'hive')
    # ---- queen's thorax, striped abdomen hidden in the hive
    m.ell((0, 21.5, 0.2), (4.8, 4.2, 4.2), 'iron', 'thorax')
    for k in range(9):
        a = k * 40 * DEG
        m.sph((math.sin(a) * 3.9, 24.6, 0.2 + math.cos(a) * 3.4), 1.3, 'brass', 'thorax')
    # arms: slender, one raised like a conductor keeping time
    arms = {1: ((4.2, 22.5, 1.0), (7.8, 25.8, 2.4), (9.0, 30.0, 3.6)),
            -1: ((-4.2, 22.5, 1.0), (-7.4, 19.6, 3.2), (-5.0, 18.2, 6.2))}
    for s, (a0, a1, a2) in arms.items():
        m.tube([a0, a1], [1.0, 0.85], 'iron', 'arm%d' % s)
        m.sph(a1, 0.9, 'brass', 'arm%d' % s)
        m.tube([a1, a2], [0.85, 0.7], 'iron', 'arm%d' % s)
        m.sph(a2, 1.0, 'brass', 'arm%d' % s)
    # wings: glass panes on brass struts
    for s in (-1, 1):
        for (ln, wd, ang, dy, nm) in ((12.0, 4.2, 38, 3.0, 'wingF'), (8.5, 3.0, 12, -1.0,
                                                                        'wingH')):
            root = (s * 2.5, 24.0 + dy * 0.3, -3.2)
            uvec = norm((s * 1.0, 0, -0.5))
            pts = g.wing_shape(ln * 0.55, dy, ln * 0.55, wd, 12, tip=0.2, rot=ang)
            P = [add(root, add(mul(uvec, x), (0, y, 0))) for x, y in pts]
            m.poly(P, 'glass', nm + str(s), puff=0.25)
            tip = add(root, add(mul(uvec, ln * 1.0 * math.cos(ang * DEG)),
                                (0, dy + ln * math.sin(ang * DEG), 0)))
            m.tube([root, tip], [0.5, 0.3], 'brass', nm + str(s))
        m.group('wingH%d' % s, 'wingF%d' % s)
    # ---- head: round, big honey-lamp eyes, cog crown, key antennae
    head_c, head_r = (0, 30.2, 1.6), (4.6, 4.2, 4.2)
    m.ell(head_c, head_r, 'iron', 'head')
    m.paint(g.on(head_c, head_r, (0, -0.35, 1))[0], (2.6, 1.6, 1.6), 'brass', ['head'])
    for s in (-1, 1):
        p, n = g.on(head_c, head_r, (s * 0.62, 0.12, 0.78))
        m.eye(p, n, 3.2, 4.0, style='glow', iris=('honey', 1), center=(0, 29, 8),
              glint=True)
        m.tube([(s * 1.6, 33.8, 2.2), (s * 3.2, 37.6, 2.6), (s * 5.4, 39.4, 2.2)],
               [0.5, 0.45, 0.4], 'brass', 'ant%d' % s)
        m.ell((s * 5.9, 39.6, 2.1), (1.1, 1.1, 0.5), 'brass', 'ant%d' % s)
    # the cog crown
    cc = (0, 34.6, 1.0)
    m.ell(cc, (3.4, 1.0, 3.4), 'brass', 'crown')
    for k in range(10):
        a = k * 36 * DEG
        m.box(add(cc, (math.sin(a) * 3.3, 1.2, math.cos(a) * 3.3)), (0.55, 1.1, 0.55),
              'brass', 'crown', rot=(k * 36, 0, 0), bevel=0.15)
    m.sph(add(cc, (0, 1.6, 0)), 1.1, 'honey', 'crown')
    p, n = g.on(head_c, head_r, (0.1, -0.55, 1))
    m.mouth(p, n, 'smile', w=2.2)
    # ---- three wind-up drones
    for k, (c, sc) in enumerate((((12.5, 16.0, 4.0), 1.0), ((-12.0, 24.0, -2.0), 0.9),
                                 ((9.0, 36.5, -4.5), 0.8))):
        _clock_bee(m, c, 1, 'drone%d' % k, sc)
    return m


# ==========================================================================
# 135 HOARDWYRM  RELIC/WYRM  (RELIC + WYRM)
# A wyrm whose scales are old coins and whose spine is studded with gems,
# coiled on its own heap of treasure; a crown hangs askew on one horn and its
# tail cradles a golden goblet.
# ==========================================================================
def hoardwyrm(g):
    m = g.Model('HOARDWYRM')
    m.outline = (42, 22, 30)
    m.mat('gold', ['#7a4a10', '#c08420', '#f0c040', '#fff4a8'], spec=0.5)
    m.mat('bronze', ['#4e2c0a', '#7a4a10', '#c08420'])
    m.mat('wyrm', ['#2c1870', '#5a3cc0', '#9a80f0'])
    m.mat('ruby', ['#a8183a', '#ff5a74'], spec=0.6)
    m.mat('jade', ['#16805a', '#62dca0'], spec=0.6)
    m.eye_dark = (34, 16, 30)
    m.white = (255, 244, 168)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -26
    # ---- the heap: a low bronze mound strewn with rimmed coins and gems
    heap_c, heap_r = (0, 1.6, -1.0), (15.5, 4.2, 12.5)
    m.ell(heap_c, heap_r, 'bronze', 'heap')
    rnd = _Rand(11)
    for k in range(34):
        a = rnd.f() * 2 * math.pi
        rr = 0.25 + 0.72 * math.sqrt(rnd.f())
        d = (math.cos(a) * rr, 1.0 - rr * 0.8, math.sin(a) * rr)
        p, n = g.surf(heap_c, heap_r, d)
        n = norm(add(n, (rnd.f() - 0.5, 0, rnd.f() - 0.5)))
        if k % 7 == 3:
            m.crystal(sub(p, mul(n, 0.4)), add(p, mul(n, 1.8)), 0.9,
                      'ruby' if k % 2 else 'jade', 'heap', sides=5, tip_frac=0.5)
        else:
            disk(m, add(p, mul(n, 0.1)), n, 1.8, 'bronze', 'heap', th=0.35)
            disk(m, add(p, mul(n, 0.35)), n, 1.25, 'gold', 'heap', th=0.3)
    # ---- coiled body: one loop around the heap, rising to the neck
    spine = [(-9.0, 7.5, 6.5), (-11.0, 7.5, -2.0), (-6.0, 7.8, -9.0), (3.0, 8.0, -10.0),
             (10.0, 8.2, -4.0), (10.5, 8.5, 4.0), (5.0, 10.0, 8.0), (0.5, 15.0, 6.5),
             (-0.5, 21.0, 4.0), (0.5, 27.0, 3.5), (2.0, 32.0, 5.0)]
    radii = [2.2, 3.0, 3.6, 4.0, 4.4, 4.6, 4.8, 4.6, 4.0, 3.6, 3.2]
    m.tube(spine, radii, 'wyrm', 'body')
    # coin scales armouring the violet hide in overlapping rows
    dense = g.catmull(spine, 4)
    for i in range(2, len(dense) - 2, 2):
        q, u = dense[i]
        k0 = min(int(u), len(radii) - 2)
        r = radii[k0] + (radii[k0 + 1] - radii[k0]) * (u - k0)
        tng = norm(sub(dense[i + 1][0], dense[i - 1][0]))
        side = norm(cross(tng, (0, 1, 0))) if abs(tng[1]) < 0.9 else (1, 0, 0)
        upv = norm(cross(side, tng))
        for k in range(5):
            a = (k * 60 - 30 + (i % 4) * 15) * DEG
            d = norm(add(mul(side, math.cos(a)), mul(upv, math.sin(a))))
            d2 = norm(add(mul(side, -math.cos(a)), mul(upv, math.sin(a))))
            for dd in (d, d2):
                if dot(dd, upv) < -0.2:
                    continue
                p = add(q, mul(dd, r * 0.9))
                nrm = norm(add(dd, mul(tng, 0.5)))
                disk(m, p, nrm, 1.7, 'bronze', 'scales', th=0.45)
                disk(m, add(p, mul(nrm, 0.3)), nrm, 1.15, 'gold', 'scales', th=0.4)
    m.group('scales', 'body')
    # gold belly plates down the front of the rising neck
    belly = [add(q, (0, -r * 0.1, r * 0.66)) for q, r in zip(spine[6:11], radii[6:11])]
    m.tube(belly, [r * 0.62 for r in radii[6:11]], 'gold', 'body', flat=0.5, up=(0, 0, 1))
    # gem ridge along the spine
    for i in range(1, 10):
        q, r = spine[i], radii[i]
        mat = 'ruby' if i % 2 else 'jade'
        base = add(q, (0, r * 0.75, -r * 0.35))
        m.crystal(base, add(base, (0, 2.4, -1.0)), 1.0, mat, 'body', sides=5, tip_frac=0.55)
    # ---- tail curling around a goblet
    m.tube([(-9.0, 7.5, 6.5), (-6.5, 6.5, 11.0), (-2.5, 5.5, 12.5), (0.0, 7.0, 11.5)],
           [2.2, 1.8, 1.4, 0.6], 'wyrm', 'tail')
    gb = (-3.0, 6.2, 12.2)
    m.ell(add(gb, (0, 0.2, 0)), (1.8, 0.5, 1.8), 'gold', 'goblet')
    m.tube([gb, add(gb, (0, 2.6, 0))], [0.5, 0.5], 'gold', 'goblet')
    m.ell(add(gb, (0, 4.2, 0)), (2.0, 1.9, 2.0), 'gold', 'goblet')
    m.paint(add(gb, (0, 5.4, 0)), (1.6, 0.6, 1.6), 'ruby', ['goblet'])
    # ---- little wings: violet membranes on gold fingers
    for s in (-1, 1):
        sh_ = (s * 4.0, 26.0, 0.5)
        wr = (s * 12.0, 33.5, -3.0)
        fingers = [(s * 16.0, 30.5, -4.0), (s * 14.0, 25.0, -3.5), (s * 9.5, 22.5, -2.2)]
        m.tube([sh_, wr], [1.4, 0.9], 'gold', 'wing%d' % s)
        mem = [sh_, wr]
        for i, f in enumerate(fingers):
            prev = wr if i == 0 else fingers[i - 1]
            mid = lerp(prev, f, 0.5)
            mem.append(add(mid, (-s * 1.6, 0.4, 0.2)))
            mem.append(f)
        mem.append((s * 5.0, 22.0, 0.0))
        m.poly(mem, 'wyrm', 'wing%d' % s, puff=0.3)
        for f in fingers:
            m.tube([wr, f], [0.7, 0.3], 'gold', 'wing%d' % s)
    # ---- head: blunt snout, gem brow, horns with a crown hanging askew
    head_c, head_r = (2.2, 36.0, 6.5), (4.6, 4.0, 4.8)
    m.ell(head_c, head_r, 'wyrm', 'head')
    m.tube([(2.2, 35.2, 9.0), (2.2, 34.2, 12.4), (2.2, 33.6, 14.4)], [3.2, 2.5, 1.9],
           'wyrm', 'head')
    m.tube([(2.2, 32.8, 9.0), (2.2, 32.0, 12.0), (2.2, 31.8, 13.8)], [2.2, 1.7, 1.2],
           'gold', 'head')
    m.crystal((2.2, 38.8, 9.5), (2.2, 40.5, 10.8), 1.0, 'ruby', 'head', sides=5,
              tip_frac=0.5)
    for s in (-1, 1):
        m.tube([(2.2 + s * 2.6, 38.8, 5.0), (2.2 + s * 4.6, 42.0, 2.6),
                (2.2 + s * 5.4, 45.2, 0.4)], [1.3, 1.0, 0.3], 'gold', 'horn%d' % s)
        m.tube([(2.2 + s * 4.0, 35.5, 5.0), (2.2 + s * 6.6, 34.8, 2.8),
                (2.2 + s * 7.8, 34.4, 1.2)], [1.4, 0.9, 0.2], 'gold', 'head',
               flat=0.35, up=(0, 0.3, 1))
    # crown slipped over the left horn
    cc, crot = (7.2, 42.2, 2.2), (0, 0, -24)
    m.ell(cc, (2.4, 1.2, 2.4), 'gold', 'crown', rot=crot)
    for k in range(6):
        a = k * 60 * DEG
        p, n = g.surf(cc, (2.4, 1.2, 2.4), (math.cos(a), 0.9, math.sin(a)), crot)
        m.crystal(p, add(p, mul(n, 1.6)), 0.45, 'gold', 'crown', sides=4, tip_frac=0.7)
    m.paint(g.surf(cc, (2.4, 1.2, 2.4), (0.2, 0, 1), crot)[0], 0.7, 'ruby', ['crown'])
    g.eye_pair(m, head_c, head_r, 38, 18, 3.6, 3.0, style='sharp', iris=('ruby', 1),
               slant=0.9, lid=1, center=(2.2, 33, 15))
    m.mouth((2.2, 32.4, 13.9), (0, -0.2, 1), 'smile', w=3.0, fang=1)
    return m


# ==========================================================================
# 136 STARSQUID  ASTRAL/TIDE  (ASTRAL + TIDE)
# A tall night-blue squid speckled with stars, arrow fins held high like a
# comet's head, trailing its arms through clouds of glowing nebula ink.
# ==========================================================================
def starsquid(g):
    m = g.Model('STARSQUID')
    m.outline = (16, 12, 40)
    m.mat('space', ['#1a1440', '#2e2a78', '#4a4cb4', '#7c8ae6'])
    m.mat('nebula', ['#6a2a8a', '#b04cb8', '#f28ad8'], emissive=0.25)
    m.mat('glow', ['#4ae0f0', '#d8ffff'], emissive=0.75)
    m.eye_dark = (14, 10, 36)
    m.white = (216, 255, 255)
    m.height = 58
    m.max_w = 58
    m.float_lift = 3
    m.front_yaw = -20
    overworld(g, m, lift=3)
    # ---- nebula ink billowing from the siphon, curling up behind
    for (c, r, seed) in (((-8.0, 6.5, -3.0), 3.6, 3), ((6.5, 4.5, -4.0), 4.0, 5),
                         ((11.5, 11.5, -7.0), 3.2, 7), ((-1.5, 3.5, -7.0), 3.4, 9),
                         ((13.0, 19.0, -9.0), 2.6, 13), ((-11.5, 13.5, -7.5), 2.8, 15)):
        puff_cloud(m, c, r, 'nebula', 'ink', n=5, seed=seed)
    for (c, r) in (((6.5, 5.2, -1.2), 1.6), ((-8.0, 7.2, -0.6), 1.4), ((11.5, 12.2, -4.8), 1.2)):
        m.paint(c, r, 'glow', ['ink'])
    for (x, y, z) in ((-9.5, 9.5, 0.3), (8.8, 7.4, 0.2), (13.2, 14.2, -3.6), (-1.0, 4.4, -3.0),
                      (14.0, 21.0, -6.0), (-12.5, 15.5, -4.5)):
        m.sparkle((x, y, z), (0, 0, 1), size=1, color='white')
    # ---- arms: eight short curling arms and two long tentacles
    base = (0, 17.5, 0.5)
    for k in range(8):
        a = (k * 45 + 22) * DEG
        d = (math.sin(a), 0, math.cos(a))
        p0 = add(base, mul(d, 2.4))
        p1 = add(add(base, mul(d, 4.2)), (0, -4.0, 0))
        p2 = add(add(base, mul(d, 5.2)), (0, -8.0, 0))
        p3 = add(add(base, mul(d, 4.0)), (0, -10.5, 0))
        m.tube([p0, p1, p2, p3], [1.5, 1.2, 0.9, 0.35], 'space', 'arms')
    for s in (-1, 1):
        pts = [(s * 1.5, 16.0, 2.0), (s * 4.5, 10.0, 3.5), (s * 9.0, 4.5, 3.0),
               (s * 13.0, 3.0, 1.5), (s * 15.0, 5.5, 0.5)]
        m.tube(pts, [1.0, 0.9, 0.8, 0.7, 0.3], 'space', 'tent%d' % s)
        club = (s * 14.2, 4.6, 1.0)
        m.ell(club, (2.0, 1.4, 1.2), 'space', 'tent%d' % s, rot=(0, 0, s * 30))
        for t in (-1, 0, 1):
            m.paint(add(club, (s * t * 0.8, -0.4, 1.0)), 0.45, 'glow', ['tent%d' % s])
    # ---- head with big glowing eyes
    head_c, head_r = (0, 20.5, 0.8), (5.0, 4.4, 4.6)
    m.ell(head_c, head_r, 'space', 'head')
    g.eye_pair(m, head_c, head_r, 42, 6, 4.4, 5.4, style='iris', iris=('glow', 0),
               center=(0, 20, 9), turn=6)
    # ---- mantle: a tall tapered cone rising to a pair of arrow fins
    m.tube([(0, 23.0, 0.0), (0, 30.0, -0.6), (0, 38.0, -1.2), (0, 45.0, -1.4),
            (0, 49.5, -1.2)], [5.2, 5.4, 4.6, 3.0, 0.6], 'space', 'mantle')
    for s in (-1, 1):
        fin = [(0, 50.5, -1.2), (s * 4.0, 48.5, -1.4), (s * 12.0, 42.0, -1.8),
               (s * 11.0, 39.8, -1.8), (s * 4.5, 35.5, -1.6), (0, 36.5, -1.4)]
        m.poly(fin, 'space', 'fin%d' % s, puff=0.25)
        m.paint((s * 8.6, 41.6, -1.6), (2.8, 1.8, 2.0), 'nebula', ['fin%d' % s])
        m.paint((s * 10.2, 41.0, -1.6), (1.0, 0.9, 2.0), 'glow', ['fin%d' % s])
        m.group('fin%d' % s, 'mantle')
    # stripe of photophores down the mantle and a scatter of stars
    for k in range(5):
        y = 26.0 + k * 4.0
        p, n = g.on((0, y, -0.8), (5.2 - k * 0.5, 2.0, 5.2 - k * 0.5), (0.2, 0, 1))
        m.paint(p, 0.6, 'glow', ['mantle'])
    for (x, y, z) in ((3.2, 29.5, 3.8), (-2.8, 33.0, 3.4), (2.0, 37.5, 2.6), (4.2, 25.5, 3.0),
                      (-3.8, 27.0, 3.6), (1.0, 42.5, 1.6)):
        m.sparkle((x, y, z), (x * 0.2, 0, 1), size=1, color='white')
    return m


# ==========================================================================
# 137 VOLTSHARK  TIDE/SPARK  (TIDE + SPARK)
# A leaping navy shark with lightning stripes down its flanks and a dynamo
# for a dorsal fin: three turbine blades around a crackling copper hub.
# ==========================================================================
def voltshark(g):
    m = g.Model('VOLTSHARK')
    m.outline = (14, 18, 36)
    m.mat('navy', ['#142038', '#243a64', '#3c6098', '#6a94c8'])
    m.mat('belly', ['#b8c8dc', '#f0f6ff'])
    m.mat('copper', ['#9a5424', '#e09848'], spec=0.6)
    m.mat('spark', ['#ffe03a', '#fffbd0'], emissive=0.8)
    m.eye_dark = (14, 16, 30)
    m.white = (240, 246, 255)
    m.height = 50
    m.max_w = 62
    m.float_lift = 3
    m.front_yaw = -30
    overworld(g, m, lift=3)
    # ---- body: a sleek torpedo, nose raised, tail sweeping down and back
    spine = [(0, 24.5, 21.0), (0, 23.8, 17.0), (0, 22.0, 10.0), (0, 19.5, 3.0),
             (0, 16.5, -4.0), (0, 13.5, -10.5), (0, 11.5, -15.5), (0, 10.8, -18.5)]
    radii = [0.9, 3.0, 4.6, 5.0, 4.4, 3.0, 1.8, 1.2]
    m.tube(spine, radii, 'navy', 'body')
    bel = [add(q, (0, -r * 0.5, 0)) for q, r in zip(spine[1:7], radii[1:7])]
    m.tube(bel, [r * 0.66 for r in radii[1:7]], 'belly', 'body', flat=0.55, up=(0, 1, 0))
    # lightning stripes along both flanks
    for s in (-1, 1):
        pts = [(s * 4.0, 22.2, 12.0), (s * 4.6, 18.8, 8.0), (s * 4.8, 21.4, 5.2),
               (s * 4.6, 17.0, 0.8), (s * 4.3, 19.0, -1.8), (s * 3.2, 14.2, -7.5)]
        for i in range(len(pts) - 1):
            for j in range(6):
                m.paint(lerp(pts[i], pts[i + 1], j / 6.0), (0.8, 0.8, 1.6), 'spark',
                        ['body'])
        # gill slits
        for k in range(3):
            m.paint((s * 3.8, 21.6 - k * 0.2, 13.8 - k * 1.2), (0.45, 1.8, 0.4), 'navy',
                    ['body'])
    # ---- crescent tail fin and swept pectoral fins
    tf = spine[-1]
    g.leaf(m, add(tf, (0, 0.5, 1.0)), add(tf, (0, 5.0, -2.0)), add(tf, (0, 10.0, -3.8)),
           2.4, 'navy', 'tail', up=(1, 0, 0), flat=0.25)
    g.leaf(m, add(tf, (0, -0.5, 1.0)), add(tf, (0, -3.5, -1.2)), add(tf, (0, -6.5, -2.8)),
           2.0, 'navy', 'tail', up=(1, 0, 0), flat=0.25)
    for s in (-1, 1):
        b = (s * 3.8, 18.5, 8.0)
        g.leaf(m, b, add(b, (s * 3.6, -3.4, -2.0)), add(b, (s * 7.0, -7.0, -4.5)), 2.2,
               'navy', 'fin%d' % s, up=(0, 1, 0.2), flat=0.25)
        m.paint(add(b, (s * 6.2, -6.2, -4.0)), 1.3, 'spark', ['fin%d' % s])
    # ---- the dynamo dorsal fin: a swept fin carrying a copper hub with three
    #      curved turbine blades, turned to catch the current (and the eye)
    hub = (0.6, 33.0, 0.5)
    g.leaf(m, (0, 22.5, 5.0), (0.2, 28.0, 2.2), hub, 3.2, 'navy', 'dorsal',
           up=(1, 0, 0), flat=0.35)
    pn = norm((1.0, 0, 0.35))
    pu = (0.0, 1.0, 0.0)
    pw = norm(cross(pn, pu))
    for k in range(3):
        a = (k * 120 + 10) * DEG
        a2 = a - 55 * DEG
        d1 = add(mul(pu, math.cos(a)), mul(pw, math.sin(a)))
        d2 = add(mul(pu, math.cos(a2)), mul(pw, math.sin(a2)))
        pts = [add(hub, mul(d1, 1.6)), add(hub, add(mul(d1, 4.6), mul(d2, 1.0))),
               add(hub, add(mul(d1, 7.2), mul(d2, 3.0)))]
        m.tube(pts, [1.4, 2.0, 0.6], 'copper', 'rotor', flat=0.3, up=pn)
        m.paint(pts[2], 1.1, 'spark', ['rotor'])
    disk(m, hub, pn, 2.4, 'copper', 'rotor', th=1.4)
    disk(m, add(hub, mul(pn, 0.9)), pn, 1.4, 'spark', 'rotor', th=0.8)
    m.group('rotor', 'dorsal')
    # a spark jumping from the hub
    g.zigzag(m, [add(hub, (0.5, 2.0, 2.0)), add(hub, (1.2, 3.6, 4.6)),
                 add(hub, (1.0, 2.6, 6.2)), add(hub, (1.6, 4.4, 8.4))],
             [0.55, 0.5, 0.45, 0.2], 'spark', 'arc', flat=0.7)
    # ---- face: sharp eyes, toothy grin
    head_c, head_r = (0, 23.2, 15.5), (3.8, 3.6, 5.2)
    g.eye_pair(m, head_c, head_r, 50, 20, 3.4, 3.0, style='sharp', iris=('spark', 0),
               slant=0.8, lid=1, center=(0, 23, 22))
    p, n = g.on(head_c, head_r, (0.2, -0.6, 1))
    m.mouth(p, n, 'open', w=4.0, h=2.0, inner=('navy', 0), fang=1)
    return m


def paint_path(m, pts, r, mat, parts, steps=6):
    """A painted line (seam, stripe, rib) through pts."""
    if isinstance(r, (int, float)):
        r = (r, r, r)
    for i in range(len(pts) - 1):
        for k in range(steps + 1):
            m.paint(lerp(pts[i], pts[i + 1], k / float(steps)), r, mat, parts)


# ==========================================================================
# 138 DULLAHAN  HOLLOW/BEAST  (HOLLOW + BEAST)
# A charcoal horse painted with bone ribs, its neck ending in a stump of pale
# spectral fire. A bone crook rising from its back hangs a caged lantern in
# front of the stump: that lantern is its head, and it looks out of it.
# ==========================================================================
def dullahan(g):
    m = g.Model('DULLAHAN')
    m.outline = (18, 16, 24)
    m.mat('coal', ['#1e1c26', '#34323e', '#4e4c5a', '#72707e'])
    m.mat('smoke', ['#4e4c5a', '#72707e', '#a4a2ae'])
    m.mat('bone', ['#8a8472', '#c8c2a8', '#f2eedc'])
    m.mat('ghost', ['#1e7a5a', '#3ecf8a', '#a8f8c8'], emissive=0.55)
    m.mat('wisp', ['#3ecf8a', '#a8f8c8'], emissive=0.7)
    m.mat('pale', ['#a8f8c8', '#eafff4'], emissive=0.8)
    m.eye_dark = (18, 16, 24)
    m.white = (242, 238, 220)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -46
    # ---- lean barrel body + deep chest, raised on long legs
    m.ell((0, 22.0, -1.5), (5.2, 5.6, 11.5), 'coal', 'body')
    m.ell((0, 22.5, 6.0), (5.6, 6.4, 5.6), 'coal', 'body')
    m.ell((0, 22.8, -9.0), (5.8, 5.8, 5.2), 'coal', 'body')
    # bone rib markings down the flanks and a spine line
    for s in (-1, 1):
        for k in range(4):
            z = 5.0 - k * 3.4
            paint_path(m, [(s * 5.4, 26.5, z), (s * 5.9, 22.5, z - 0.6),
                           (s * 5.2, 18.5, z - 1.2)], (1.1, 1.1, 1.1), 'bone', ['body'])
    # ---- long legs on hooves of ghost fire
    for s in (-1, 1):
        for zz, nm, hip in ((7.0, 'legF', 0), (-9.5, 'legB', 1)):
            part = '%s%d' % (nm, s)
            if hip:
                m.ell((s * 4.0, 21.0, zz), (2.6, 5.6, 4.4), 'coal', part)
                pts = [(s * 4.2, 17.0, zz - 0.8), (s * 4.3, 10.5, zz - 2.4),
                       (s * 4.3, 4.6, zz - 1.0)]
            else:
                pts = [(s * 3.6, 18.0, zz), (s * 3.7, 10.5, zz + 0.4),
                       (s * 3.7, 4.6, zz + 0.8)]
            m.tube(pts, [2.4, 1.6, 1.3], 'coal', part)
            m.ell(add(pts[-1], (0, -0.6, 0.2)), (1.7, 1.2, 1.9), 'bone', part)
            g.flame(m, add(pts[-1], (0, -4.0, 0.2)), 8.5, 2.4, part,
                    mats=('ghost', 'wisp', 'wisp'), up=(0, 1, -0.3), tongues=2,
                    core=False, seed=int(zz + 20 * s))
    # ---- neck arching up and forward to a stump of pale fire
    neck = [(0, 24.5, 8.0), (0, 29.0, 11.0), (0, 33.0, 13.0)]
    m.tube(neck, [4.2, 3.4, 3.0], 'coal', 'neck')
    m.ell((0, 34.0, 13.4), (3.0, 1.0, 3.0), 'bone', 'neck', rot=(0, -22, 0))
    g.flame(m, (0, 34.2, 13.2), 11.0, 3.0, 'stump', mats=('wisp', 'pale', 'pale'),
            up=(0, 1, -0.55), tongues=2, seed=4)
    # smoky mane streaming back along the neck
    for k in range(6):
        b = lerp((0, 34.0, 11.8), (0, 27.0, 4.0), k / 5.0)
        m.tube([b, add(b, (0.6, 1.8, -3.0)), add(b, (1.2, 0.8, -6.0 + k * 0.2))],
               [1.7, 1.3, 0.3], 'smoke', 'mane')
    # smoky tail
    m.tube([(0, 24.5, -13.5), (1.0, 23.0, -17.5), (2.2, 17.5, -19.5), (3.4, 11.0, -19.0)],
           [1.8, 2.4, 2.0, 0.4], 'smoke', 'tail')
    # ---- bone crook rising from the withers, hooking far out in front
    crook = [(0, 27.0, 1.0), (0, 36.0, 1.5), (0, 44.0, 6.0), (0, 47.0, 14.0),
             (0, 46.0, 22.0), (0, 43.5, 26.0)]
    m.tube(crook, [1.3, 1.1, 1.0, 0.95, 0.85, 0.7], 'bone', 'crook')
    m.ell((0, 27.2, 1.0), (2.6, 1.4, 3.0), 'bone', 'crook')
    # ---- the lantern head: iron cap and base, bars over a glowing green pane
    lc = (0, 34.5, 26.0)
    m.ell(add(lc, (0, 8.0, 0)), (0.9, 1.2, 0.5), 'bone', 'crook')
    m.ell(lc, (5.0, 5.0, 5.0), 'ghost', 'lamp')
    m.ell(add(lc, (0, 5.0, 0)), (5.4, 1.2, 5.4), 'coal', 'lamp')
    m.tube([add(lc, (0, 5.8, 0)), add(lc, (0, 7.0, 0))], [3.2, 0.8], 'coal', 'lamp')
    m.ell(add(lc, (0, -5.0, 0)), (5.2, 1.3, 5.2), 'coal', 'lamp')
    m.paint(add(lc, (0, 4.8, 0)), (5.8, 0.45, 5.8), 'bone', ['lamp'])
    m.paint(add(lc, (0, -5.0, 0)), (5.6, 0.45, 5.6), 'bone', ['lamp'])
    m.sph(add(lc, (0, -6.8, 0)), 1.2, 'coal', 'lamp')
    # cage bars only at the edges and back, so the glowing pane stays clear
    # (and the face readable) even in the small icon and overworld sprites
    yw = m.front_yaw * DEG
    cam = math.atan2(-math.sin(yw), math.cos(yw))
    for off in (-92, 92, 180):
        a = cam + off * DEG
        d = (math.sin(a), 0, math.cos(a))
        m.tube([add(lc, (d[0] * 5.0, -4.4, d[2] * 5.0)),
                add(lc, (d[0] * 5.3, 0, d[2] * 5.3)),
                add(lc, (d[0] * 5.0, 4.4, d[2] * 5.0))], [0.7, 0.7, 0.7], 'coal', 'lamp')
    # two separate dark eye holes glaring out through the pane
    for s in (-1, 1):
        a = cam + s * 34 * DEG
        n = (math.sin(a), 0.1, math.cos(a))
        p = add(lc, (n[0] * 5.0, 0.4, n[2] * 5.0))
        m.eye(p, n, 1.7, 3.4, style='solid', iris=('coal', 0), glint=False, minw=1,
              minh=2)
    return m


# ==========================================================================
# 139 CHIMERAX  VENOM/BEAST  (VENOM + BEAST)
# A tawny lion with a shaggy venom-purple mane, swept goat horns and a goat
# beard. Its tail is a green serpent with a head (and fangs) of its own.
# ==========================================================================
def chimerax(g):
    m = g.Model('CHIMERAX')
    m.outline = (46, 22, 26)
    m.mat('fur', ['#7a4818', '#b87a30', '#e0a84c', '#f8d68a'])
    m.mat('mane', ['#3e1a52', '#6c2e8a', '#a456c0'])
    m.mat('horn', ['#4e4238', '#8a7862', '#d0c0a0'])
    m.mat('snake', ['#1e5a2a', '#3c9a3a', '#86d25a'])
    m.mat('venom', ['#eef046'], emissive=0.7)
    m.eye_dark = (46, 22, 26)
    m.white = (248, 214, 138)
    m.height = 54
    m.max_w = 62
    m.front_yaw = -36
    # ---- body and legs
    m.ell((0, 14.5, -2.5), (6.6, 6.4, 11.0), 'fur', 'body')
    m.ell((0, 15.5, 5.5), (6.8, 7.2, 6.0), 'fur', 'body')
    m.paint((0, 9.5, 1.0), (5.0, 2.6, 10.0), 'fur', ['body'])
    for s in (-1, 1):
        m.tube([(s * 3.9, 12.0, 7.0), (s * 4.1, 6.0, 7.8), (s * 4.1, 2.2, 8.4)],
               [2.9, 2.4, 2.4], 'fur', 'legF%d' % s)
        m.ell((s * 4.1, 1.6, 9.6), (2.7, 1.6, 3.0), 'fur', 'legF%d' % s)
        m.ell((s * 4.5, 13.5, -9.0), (3.4, 5.0, 4.6), 'fur', 'legB%d' % s)
        m.tube([(s * 4.7, 10.0, -10.5), (s * 4.9, 5.0, -11.2), (s * 4.7, 2.2, -9.8)],
               [2.8, 2.2, 2.2], 'fur', 'legB%d' % s)
        m.ell((s * 4.7, 1.6, -8.6), (2.5, 1.6, 2.8), 'fur', 'legB%d' % s)
        for t in (-1, 0, 1):
            m.paint((s * 4.1 + t * 1.0, 1.4, 12.4), (0.35, 0.9, 0.6), 'mane',
                    ['legF%d' % s])
    # ---- serpent tail: rises in an S behind the lion, head turned forward
    tail = [(0, 16.0, -12.5), (0.5, 17.5, -17.0), (2.0, 22.5, -19.5), (4.0, 28.5, -18.5),
            (5.0, 32.5, -15.5), (5.6, 34.0, -12.0)]
    m.tube(tail, [2.0, 2.2, 2.3, 2.2, 2.0, 1.8], 'snake', 'tail')
    for k in range(1, 5):
        q = lerp(tail[k], tail[k + 1], 0.5)
        m.paint(add(q, (0.4, 0.4, -1.6)), (1.8, 0.6, 1.4), 'snake', ['tail'])
    # serpent head turned toward the viewer, jaws open on two fangs
    tip = tail[-1]
    fwd = norm((0.62, -0.12, 0.78))
    upv = norm(cross(fwd, cross((0, 1, 0), fwd)))
    side = norm(cross(upv, fwd))
    hc = add(tip, mul(fwd, 1.6))
    m.tube([sub(hc, mul(fwd, 1.8)), hc, add(hc, mul(fwd, 3.4))], [2.8, 3.3, 2.1],
           'snake', 'snakehead', flat=0.72, up=upv)
    jaw = add(hc, mul(upv, -2.2))
    m.tube([sub(jaw, mul(fwd, 1.0)), add(jaw, mul(fwd, 2.6))], [1.4, 0.9], 'snake',
           'snakehead', flat=0.6, up=upv)
    for s in (-1, 1):
        m.eye(add(add(hc, mul(side, s * 2.0)), mul(upv, 1.4)),
              norm(add(add(mul(side, s * 0.6), mul(upv, 0.4)), mul(fwd, 0.7))), 2.0, 2.0,
              style='solid', iris=('venom', 0), glint=False, minw=2, minh=2)
        f0 = add(add(hc, mul(fwd, 2.4)), add(mul(side, s * 0.9), mul(upv, -1.2)))
        m.tube([f0, add(f0, mul(upv, -1.6))], [0.45, 0.15], 'horn', 'snakehead')
    m.sph(add(add(hc, mul(fwd, 2.6)), mul(upv, -3.6)), 0.6, 'venom', 'snakehead')
    # ---- shaggy venom mane: locks radiating from a ring around the face
    head_c, head_r = (0, 24.0, 10.5), (5.2, 4.8, 5.0)
    mc = (0, 24.0, 7.6)
    m.ell(mc, (6.8, 7.0, 4.6), 'mane', 'mane')
    rnd = _Rand(7)
    for k in range(18):
        a = 2 * math.pi * k / 18
        d = (math.cos(a), math.sin(a), 0)
        b = add(mc, (d[0] * 5.8, d[1] * 5.8, -0.5))
        ln = 3.0 + rnd.f() * 1.6
        tip = add(b, (d[0] * ln, d[1] * ln - 1.4, -2.6 - rnd.f() * 1.5))
        m.tube([b, lerp(b, tip, 0.55), tip], [2.6, 1.9, 0.4], 'mane', 'mane')
    for k in range(5):
        a = (k - 2) * 0.5
        b = (math.sin(a) * 5.0, 17.5 - abs(k - 2) * 0.8, 10.0)
        m.tube([b, add(b, (math.sin(a) * 1.5, -4.0, 0.8))], [2.2, 0.4], 'mane', 'mane')
    # ---- head: broad lion muzzle, goat horns, goat beard
    m.ell(head_c, head_r, 'fur', 'head')
    mz_c, mz_r = (0, 22.0, 14.6), (3.4, 2.6, 2.8)
    m.ell(mz_c, mz_r, 'fur', 'head')
    m.paint((0, 21.2, 16.0), (2.8, 1.8, 1.8), 'fur', ['head'])
    for s in (-1, 1):
        m.ell((s * 4.0, 28.2, 9.0), (1.6, 1.8, 1.1), 'fur', 'head')
        pts = g.curl_horn(m, (s * 2.4, 27.6, 11.0), (s * 0.5, 1.0, -0.2),
                          (s * 0.3, 0.0, -1.0), 7.2, 'horn', 'horn%d' % s, turns=0.6,
                          r0=1.6, r1=0.45)
    # goat beard hanging from the chin
    m.tube([(0, 20.2, 15.8), (0, 17.4, 16.2), (0.4, 14.4, 15.6)], [1.5, 1.2, 0.35],
           'mane', 'beard')
    g.eye_pair(m, head_c, head_r, 30, 14, 3.4, 3.4, style='sharp', iris=('snake', 2),
               slant=0.8, lid=1, center=(0, 22, 18), turn=8)
    m.dot(g.on(mz_c, mz_r, (0, 0.55, 1))[0], (0, 0.3, 1), w=2.2, h=1.4, minw=2,
          color=('mane', 0))
    p, nn = g.on(mz_c, mz_r, (0, -0.4, 1))
    m.mouth(p, nn, 'smile', w=3.0, fang=1)
    return m


# ==========================================================================
# 140 RIDDLEON  MIND/STONE  (MIND + STONE)
# A sandstone sphinx-cat lying in the sphinx pose under a striped lapis-and-
# gold nemes head-cloth whose lappets fall onto its chest. A pink third eye
# sits on the gold brow band, stone wings are folded along its back, its tail
# rises in a "?" hook, and one glowing gold rune tile hovers beside it.
# ==========================================================================
def riddleon(g):
    m = g.Model('RIDDLEON')
    m.outline = (52, 32, 30)
    m.mat('sand', ['#8a6034', '#c0904e', '#e2bc78', '#f8e2aa'])
    m.mat('stone', ['#6e4a2c', '#8a6034', '#c0904e', '#e2bc78'])
    m.mat('lapis', ['#1c2c78', '#3456c0', '#6c94ec'])
    m.mat('gold', ['#a07018', '#e0b030', '#fff0a0'], spec=0.5)
    m.mat('glow', ['#e0b030', '#fff0a0'], emissive=0.7)
    m.mat('gem', ['#c02a78', '#ff7cc0'], spec=0.6)
    m.eye_dark = (52, 32, 30)
    m.white = (248, 226, 170)
    m.height = 52
    m.max_w = 60
    m.front_yaw = -28
    g.OW_TURN[m.name] = -36.0
    # ---- lying body, haunches tucked, forepaws stretched out in front
    m.ell((0, 7.5, -3.5), (6.8, 6.0, 11.0), 'sand', 'body')
    m.ell((0, 11.0, 4.5), (6.2, 8.0, 5.4), 'sand', 'body')
    for s in (-1, 1):
        m.ell((s * 5.2, 7.0, -8.5), (3.2, 5.2, 5.6), 'sand', 'hip%d' % s)
        m.ell((s * 5.6, 2.2, -4.0), (2.2, 1.8, 5.0), 'sand', 'hip%d' % s)
        m.tube([(s * 4.0, 6.0, 5.5), (s * 4.2, 2.8, 10.0), (s * 4.2, 2.2, 14.0)],
               [2.8, 2.4, 2.3], 'sand', 'legF%d' % s)
        m.ell((s * 4.2, 2.0, 15.0), (2.6, 1.9, 2.6), 'sand', 'legF%d' % s)
        for t in (-1, 0, 1):
            m.paint((s * 4.2 + t * 1.0, 1.8, 17.4), (0.3, 1.0, 0.6), 'stone',
                    ['legF%d' % s])
    # carved stripes on the flanks
    for s in (-1, 1):
        for k in range(3):
            z = -1.0 - k * 3.8
            m.paint((s * 6.4, 9.0, z), (0.9, 3.4, 0.9), 'stone', ['body'])
    # ---- tail rising behind the haunch and hooking over into a "?"
    tl = [(3.0, 4.0, -13.5), (7.5, 4.5, -14.5), (10.0, 9.0, -13.0), (10.4, 14.0, -12.0)]
    for i in range(7):
        a = (180 - i * 40) * DEG
        tl.append((12.8 + math.cos(a) * 2.4, 16.0 + math.sin(a) * 2.6, -12.0))
    m.tube(tl, None, 'sand', 'tail', rfn=lambda t: 1.4 - 0.35 * t)
    m.sph(tl[-1], 1.5, 'lapis', 'tail')
    # ---- folded stone wings raised along the back, lapis-tipped feathers
    for s in (-1, 1):
        root = (s * 4.2, 13.0, 3.5)
        for k, (ln, rise, wd) in enumerate(((17.0, 13.0, 3.4), (15.0, 9.0, 3.0),
                                           (12.5, 5.5, 2.6))):
            tip = (s * (5.2 - k * 0.4), 13.0 + rise, 3.5 - ln)
            mid = add(lerp(root, tip, 0.5), (s * 1.2, 2.0, 0))
            base = add(root, (0, -k * 1.4, -k * 1.2))
            g.leaf(m, base, mid, tip, wd, 'stone', 'wing%d' % s, up=(s * 1, 0.1, 0),
                   flat=0.34, mats=[(0, 'stone'), (0.72, 'lapis')])
        m.group('wing%d' % s, 'body')
    # ---- head raised proud on the chest
    head_c, head_r = (0, 22.0, 8.0), (5.6, 5.3, 5.0)
    m.ell(head_c, head_r, 'sand', 'head')
    mz_c, mz_r = (0, 20.0, 12.4), (2.8, 2.2, 2.2)
    m.ell(mz_c, mz_r, 'sand', 'head')
    # ---- the nemes: a striped cap over crown and nape, broad side flaps
    #      behind the cheeks, and lappets falling onto the chest
    m.ell((0, 25.0, 7.0), (6.1, 4.6, 5.4), 'gold', 'nemes')
    m.tube([(0, 26.0, 3.0), (0, 22.0, 1.0), (0, 17.5, 0.5)], [3.4, 2.6, 1.8], 'gold',
           'nemes')
    for s in (-1, 1):
        m.tube([(s * 6.0, 25.0, 5.6), (s * 7.8, 21.0, 5.2), (s * 8.0, 17.0, 5.8)],
               [3.2, 3.6, 3.6], 'gold', 'nemes', flat=0.4, up=(1, 0, 0.2))
        m.tube([(s * 7.0, 17.5, 7.2), (s * 5.8, 14.0, 9.4), (s * 5.2, 10.5, 9.8)],
               [2.2, 2.0, 1.8], 'gold', 'nemes', flat=0.45, up=(0, 0.2, 1))
    for k in range(10):
        y = 9.6 + k * 2.3
        m.paint((0, y, 5.0), (11.0, 0.7, 12.0), 'lapis', ['nemes'])
    # gold brow band with the pink third eye
    m.paint((0, 25.4, 12.2), (6.0, 0.9, 1.6), 'gold', ['nemes', 'head'])
    m.ell((0, 26.4, 12.0), (1.3, 1.6, 0.8), 'gem', 'nemes', rot=(0, -20, 0))
    # ---- face: big kohl-lined eyes, nose, a knowing smile
    g.eye_pair(m, head_c, head_r, 27, 4, 4.0, 4.4, style='iris', iris=('lapis', 1),
               slant=0.5, lid=1, center=(0, 20, 16), turn=10)
    m.dot(g.on(mz_c, mz_r, (0, 0.5, 1))[0], (0, 0.3, 1), w=1.8, h=1.2, minw=2,
          color=('gem', 0))
    p, nn = g.on(mz_c, mz_r, (0, -0.4, 1))
    m.mouth(p, nn, 'smile', w=2.4)
    # ---- one glowing rune tile hovering beside it
    tc = (-13.0, 29.0, 7.0)
    m.box(tc, (2.0, 2.0, 0.6), 'glow', 'rune', rot=(28, 0, 8), bevel=0.3)
    f = (math.sin(28 * DEG), 0, math.cos(28 * DEG))
    m.paint(add(tc, mul(f, 0.6)), (0.45, 1.4, 0.4), 'lapis', ['rune'], rot=(28, 0, 8))
    m.paint(add(add(tc, mul(f, 0.6)), (0, 0.9, 0)), (1.2, 0.45, 0.4), 'lapis', ['rune'],
            rot=(28, 0, 8))
    return m


# ==========================================================================
# 141 GRIFFALON  GALE/BEAST  (GALE + BEAST)
# A griffin with a peregrine falcon's head: slate hood, pale cheeks and a
# dark moustache stripe. Big slate-blue wings; the front half is feathered
# and walks on yellow talons, the rear is a tawny lion with a tufted tail.
# ==========================================================================
def griffalon(g):
    m = g.Model('GRIFFALON')
    m.outline = (22, 24, 38)
    m.mat('slate', ['#262c4a', '#3e4a74', '#5e70a2', '#8ea2cc'])
    m.mat('fur', ['#8a5a24', '#c48c3e', '#eabe70'])
    m.mat('cream', ['#c8c4b8', '#f4f0e4'])
    m.mat('talon', ['#c89018', '#f8d040'])
    m.mat('hood', ['#14182a', '#262c4a', '#3e4a74'])
    m.eye_dark = (22, 24, 38)
    m.white = (244, 240, 228)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -32
    overworld(g, m, side_yaw=-60)
    # ---- lion hindquarters with a tufted tail
    m.ell((0, 15.0, -5.5), (6.2, 6.2, 8.5), 'fur', 'body')
    for s in (-1, 1):
        m.ell((s * 4.3, 13.5, -9.5), (3.3, 5.0, 4.6), 'fur', 'legB%d' % s)
        m.tube([(s * 4.6, 10.0, -11.0), (s * 4.8, 5.0, -11.6), (s * 4.6, 2.2, -10.2)],
               [2.7, 2.1, 2.1], 'fur', 'legB%d' % s)
        m.ell((s * 4.6, 1.6, -9.0), (2.4, 1.6, 2.8), 'fur', 'legB%d' % s)
    m.tube([(0, 17.0, -13.0), (1.0, 19.5, -17.5), (2.4, 22.0, -20.5), (3.6, 23.8, -22.0)],
           [1.3, 1.1, 0.9, 0.8], 'fur', 'tail')
    m.ell((4.2, 24.6, -23.0), (1.9, 2.6, 1.9), 'slate', 'tail', rot=(0, 30, -20))
    # ---- feathered forequarters and a pale spotted breast
    m.ell((0, 18.0, 4.0), (6.4, 7.6, 6.4), 'slate', 'chest')
    m.paint((0, 16.5, 9.0), (4.4, 6.4, 2.8), 'cream', ['chest'])
    for (x, y) in ((-1.8, 18.5), (1.6, 17.0), (0.0, 14.5), (-2.4, 14.0), (2.4, 13.4)):
        m.paint((x, y, 10.2), (0.55, 0.45, 0.8), 'slate', ['chest'])
    # feathered front legs down to bare yellow shanks and talons
    for s in (-1, 1):
        part = 'legF%d' % s
        m.tube([(s * 3.8, 13.0, 6.5), (s * 4.0, 8.0, 7.2), (s * 4.0, 3.0, 7.8)],
               [2.8, 1.5, 1.3], 'slate', part, mats=[(0, 'slate'), (0.5, 'talon')])
        m.ell((s * 4.0, 9.6, 7.0), (2.6, 2.6, 2.6), 'slate', part)
        for t in (-1, 0, 1):
            m.tube([(s * 4.0 + t * 0.8, 2.4, 8.2), (s * 4.0 + t * 1.7, 1.2, 10.4)],
                   [0.8, 0.6], 'talon', part)
            m.crystal((s * 4.0 + t * 1.7, 1.2, 10.2), (s * 4.0 + t * 2.0, 0.2, 12.0), 0.55,
                      'slate', part, sides=4, tip_frac=0.8)
    # ---- big slate wings raised behind: coverts on the arm, long primaries
    for s in (-1, 1):
        # the near wing (+x) sweeps back and the far wing a little forward,
        # so both show broad in the front view and in the profile view
        bk = 0.75 if s > 0 else -0.45
        def sw(x, y, z):
            return (s * x, y, z - bk * (x - 5.0))
        sh_ = sw(5.0, 22.0, 1.0)
        el = sw(11.5, 31.0, -2.5)
        wr = sw(17.0, 41.0, -6.0)
        m.tube([sh_, el, wr], [2.6, 2.0, 1.4], 'slate', 'wing%d' % s)
        mem = [sh_, el, wr, sw(19.5, 43.5, -6.5), sw(21.0, 36.0, -7.0),
               sw(18.0, 27.0, -6.0), sw(13.0, 20.0, -4.5), sw(7.5, 17.0, -2.0)]
        m.poly(mem, 'slate', 'wing%d' % s, puff=0.3)
        for k in range(7):
            t = k / 6.0
            b = lerp(lerp(sh_, el, min(1, t * 2)), lerp(el, wr, max(0, t * 2 - 1)),
                     1.0 if t > 0.5 else 0.0)
            d = norm((s * (0.15 + 0.65 * t), -1.0 + 0.9 * t, -0.35))
            ln = 8.0 + 7.0 * t
            g.leaf(m, b, add(b, mul(d, ln * 0.5)), add(b, mul(d, ln)), 2.0 + 0.4 * t,
                   'slate', 'prim%d' % s, up=(0, 0.2, 1), flat=0.25,
                   mats=[(0, 'slate'), (0.62, 'hood')])
        m.group('prim%d' % s, 'wing%d' % s)
    # ---- neck and peregrine head
    m.tube([(0, 21.0, 6.0), (0, 25.0, 8.0), (0, 28.0, 9.0)], [4.4, 3.8, 3.6], 'slate',
           'chest')
    m.paint((0, 24.0, 11.4), (3.4, 3.4, 2.0), 'cream', ['chest'])
    head_c, head_r = (0, 31.2, 9.8), (5.0, 4.8, 5.0)
    m.ell(head_c, head_r, 'cream', 'head')
    # the peregrine's dark hood over crown and nape, a moustache stripe
    # dropping below each eye, pale cheeks and throat left bare
    m.paint((0, 33.2, 8.4), (5.2, 3.2, 5.6), 'hood', ['head'])
    m.paint((0, 31.0, 5.4), (5.2, 5.0, 3.0), 'hood', ['head'])
    for s in (-1, 1):
        m.paint((s * 3.7, 29.0, 11.6), (1.3, 3.0, 1.6), 'hood', ['head'],
                rot=(0, 0, s * 8))
    # hooked beak with a yellow cere
    m.ell((0, 31.2, 13.9), (1.9, 1.5, 1.4), 'talon', 'beak')
    m.tube([(0, 31.0, 14.4), (0, 30.8, 17.4), (0, 29.0, 19.2), (0, 27.0, 18.8)],
           [2.0, 1.6, 1.0, 0.3], 'slate', 'beak')
    m.tube([(0, 29.4, 14.2), (0, 28.9, 16.2)], [1.0, 0.45], 'slate', 'beak')
    g.eye_pair(m, head_c, head_r, 40, 16, 3.8, 4.0, style='iris', iris=('talon', 1),
               center=(0, 30, 16), turn=6)
    return m


# ==========================================================================
# 142 MANTICLAW  VENOM/BRAWL  (VENOM + BRAWL)
# A powerful upright lion brawler in deep crimson: heavy shoulders and chest,
# cream-wrapped fists raised in guard, a snarling fanged face under a heavy
# brow, and a huge dark mane of quills. A thick segmented scorpion tail arches
# high over its head and hangs a hooked purple barb out in front of it.
# ==========================================================================
def manticlaw(g):
    m = g.Model('MANTICLAW')
    m.outline = (26, 6, 16)
    m.mat('fur', ['#4a0e14', '#7e1a1e', '#b02e28', '#d8583a'])
    m.mat('chest', ['#b02e28', '#c87a50'])
    m.mat('mane', ['#1a0610', '#34101c', '#561a26'])
    m.mat('shell', ['#7e1a1e', '#b02e28', '#d8583a'])
    m.mat('wrap', ['#c8b8a0', '#f4ead4'])
    m.mat('sting', ['#3a1858', '#7438b0', '#be80f0'])
    m.mat('venom', ['#86ec58'], emissive=0.7)
    m.eye_dark = (26, 6, 16)
    m.white = (244, 234, 212)
    m.height = 62
    m.max_w = 62
    m.front_yaw = -18
    # ---- thick legs planted wide, wrapped ankles
    for s in (-1, 1):
        part = 'leg%d' % s
        zz = 1.5 if s > 0 else -1.5
        m.ell((s * 4.4, 13.5, zz), (3.9, 5.2, 4.0), 'fur', part)
        m.tube([(s * 4.8, 10.0, zz), (s * 5.6, 5.5, zz + 1.2), (s * 5.8, 2.4, zz)],
               [3.2, 2.6, 2.4], 'fur', part)
        m.ell((s * 5.8, 1.6, zz + 1.6), (2.8, 1.7, 3.6), 'fur', part)
        m.paint((s * 5.8, 3.6, zz + 0.4), (3.2, 1.5, 3.2), 'wrap', [part])
    # ---- V-shaped torso: narrow waist, deep chest, heavy traps and delts
    m.ell((0, 18.5, 0.0), (5.6, 5.0, 4.4), 'fur', 'body')
    m.ell((0, 25.0, 0.6), (8.4, 6.2, 5.6), 'fur', 'body')
    m.ell((0, 30.0, -0.8), (7.6, 2.8, 4.4), 'fur', 'body')
    for s in (-1, 1):
        # pectorals: two subtly lighter tan plates split by a dark line
        m.paint((s * 3.4, 26.0, 5.6), (3.4, 2.8, 1.6), 'chest', ['body'])
        m.paint((s * 1.4, 20.0, 4.2), (1.3, 1.1, 1.2), 'chest', ['body'])
        m.paint((s * 1.4, 17.4, 4.0), (1.2, 1.0, 1.2), 'chest', ['body'])
    m.paint((0, 24.0, 6.0), (0.5, 4.2, 1.2), 'fur', ['body'])
    # ---- scorpion tail: thick armoured segments up behind the right
    #      shoulder, over the head, and down in front of the brow
    spine = [(1.5, 15.5, -4.0), (6.0, 17.0, -10.5), (10.0, 25.0, -14.5),
             (11.5, 36.0, -15.0), (10.0, 46.0, -11.5), (6.0, 53.5, -5.0),
             (2.5, 57.0, 2.0), (0.0, 56.0, 7.0)]
    dense = g.catmull(spine, 8)
    n = len(dense)
    segs = 14
    for j in range(segs):
        i = int(j * (n - 2) / (segs - 1))
        q = dense[i][0]
        tng = norm(sub(dense[i + 1][0], q))
        r = 3.2 - 1.2 * j / (segs - 1)
        yaw = math.atan2(tng[0], tng[2]) / DEG
        pitch = -math.asin(max(-1, min(1, tng[1]))) / DEG
        m.ell(q, (r * 1.05, r * 1.0, r * 1.15), 'shell', 'tail', rot=(yaw, pitch, 0))
        m.paint(add(q, mul(tng, -r * 0.95)), (r * 1.1, r * 1.1, 0.6), 'mane', ['tail'],
                rot=(yaw, pitch, 0))
    # stinger: a bulb in front of the brow and a long barb hooking down
    #      and forward, venom beading on the point
    sc = (-1.0, 55.5, 9.0)
    m.ell(sc, (2.6, 2.4, 2.6), 'sting', 'stinger', rot=(0, 0, 20))
    hook = [add(sc, (-2.2, 0.6, 0.6)), add(sc, (-5.6, -0.2, 1.0)),
            add(sc, (-7.4, -3.4, 1.4)), add(sc, (-6.4, -7.0, 1.8)),
            add(sc, (-3.4, -8.6, 2.0))]
    m.tube(hook, [2.1, 1.8, 1.4, 0.9, 0.35], 'sting', 'stinger')
    m.sph(add(sc, (-2.2, -9.4, 2.0)), 1.1, 'venom', 'stinger')
    # ---- the huge dark quill mane: a disc behind the head bristling with
    #      long spikes that widen the whole silhouette
    mc = (0, 37.0, -1.0)
    m.ell(mc, (7.8, 7.8, 4.0), 'mane', 'mane')
    m.ell(add(mc, (0, 0, -2.4)), (10.2, 10.2, 2.2), 'mane', 'mane')
    rnd = _Rand(11)
    for k in range(13):
        a = 2 * math.pi * (k + 0.5) / 13
        d = (math.cos(a), math.sin(a), 0)
        b = add(mc, (d[0] * 6.0, d[1] * 6.0, 0.4))
        ln = 9.0 + rnd.f() * 2.5 - (3.5 if d[1] < -0.4 else 0)
        tip = add(b, (d[0] * ln, d[1] * ln - 0.8, -2.2))
        m.crystal(b, tip, 2.4, 'mane', 'mane', sides=4, tip_frac=0.95, twist=45)
    # a ruff of shorter quills under the jaw
    for k in range(5):
        a = (k - 2) * 0.45
        b = (math.sin(a) * 4.4, 31.0, 4.0)
        m.crystal(b, add(b, (math.sin(a) * 2.0, -4.2, 1.2)), 1.4, 'mane', 'mane', sides=4,
                  tip_frac=0.8)
    # ---- head: broad lion face, heavy brow, snarling muzzle
    head_c, head_r = (0, 37.0, 2.8), (5.8, 5.4, 4.8)
    m.ell(head_c, head_r, 'fur', 'head')
    mz_c, mz_r = (0, 34.4, 6.8), (3.6, 2.8, 2.6)
    m.ell(mz_c, mz_r, 'fur', 'head')
    m.paint((0, 33.8, 8.6), (3.0, 1.9, 1.4), 'chest', ['head'])
    for s in (-1, 1):
        m.ell((s * 4.8, 41.6, 1.4), (1.8, 1.9, 1.1), 'fur', 'head')
        m.paint((s * 4.8, 41.6, 2.4), (0.9, 1.0, 0.6), 'mane', ['head'])
        # heavy brow ridge slanting down toward the nose
        m.ell((s * 2.5, 40.2, 6.3), (2.6, 0.9, 1.4), 'fur', 'head', rot=(0, 0, s * 20))
        m.paint((s * 2.4, 40.6, 6.8), (2.6, 0.55, 1.2), 'mane', ['head'], rot=(0, 0, s * 20))
    g.eye_pair(m, head_c, head_r, 28, 8, 3.8, 3.2, style='sharp', iris=('venom', 0),
               slant=1.0, lid=1, center=(0, 34, 12), turn=4)
    m.dot(g.on(mz_c, mz_r, (0, 0.6, 1))[0], (0, 0.3, 1), w=2.4, h=1.4, minw=2)
    p, nn = g.on(mz_c, mz_r, (0, -0.55, 1))
    m.mouth(p, nn, 'open', w=4.0, h=2.0, inner=('mane', 0), fang=1)
    for s in (-1, 1):
        f0 = (s * 1.5, 33.2, 9.0)
        m.crystal(f0, add(f0, (0, -2.4, 0.3)), 0.55, 'wrap', 'head', sides=4,
                  tip_frac=0.9)
    # ---- massive arms up in a guard, cream-wrapped fists beside the chin
    for s in (-1, 1):
        part = 'arm%d' % s
        sh_ = (s * 8.8, 28.5, 0.0)
        el = (s * 10.6, 22.0, 4.0)
        fist = (s * 7.4, 29.4, 8.6)
        m.sph(sh_, 4.0, 'fur', part)
        m.tube([sh_, el], [3.4, 2.8], 'fur', part)
        m.tube([el, fist], [2.8, 2.5], 'wrap', part, mats=[(0, 'fur'), (0.55, 'wrap')])
        m.sph(fist, 3.4, 'wrap', part)
        m.paint(add(fist, (0, 0.2, 0)), (3.5, 0.5, 3.5), 'fur', [part])
    return m


# ==========================================================================
# 143 INKRAKEN  TIDE/HOLLOW  (TIDE + HOLLOW)
# A squat, wide octopus of ink, its mantle drooping into a curled hood tip,
# big teal lamps for eyes. Thick arms spread and curl outward across the
# ground, and drops of ink hang in the air around it.
# ==========================================================================
def inkraken(g):
    m = g.Model('INKRAKEN')
    m.outline = (10, 8, 18)
    m.mat('ink', ['#0c0a16', '#1a1830', '#2c2a4c', '#4c4a80'], spec=0.5)
    m.mat('teal', ['#14908a', '#4ae8d8', '#d0fff6'], emissive=0.8)
    m.mat('sucker', ['#5a4878', '#9a82c0'])
    m.eye_dark = (10, 8, 18)
    m.white = (208, 255, 246)
    m.height = 52
    m.max_w = 62
    m.front_yaw = -26
    # ---- eight thick arms spreading out and curling up at the tips
    for k in range(8):
        a = (k * 45 + 22.5) * DEG
        d = (math.sin(a), 0, math.cos(a))
        side = (d[2], 0, -d[0])
        b = add((0, 8.0, 0.0), mul(d, 5.5))
        pts = [b, add(mul(d, 11.0), (0, 3.2, 0)), add(mul(d, 16.5), (0, 2.6, 0)),
               add(add(mul(d, 20.0), mul(side, 1.0)), (0, 4.6, 0)),
               add(add(mul(d, 18.8), mul(side, 2.0)), (0, 7.4, 0)),
               add(add(mul(d, 16.6), mul(side, 1.6)), (0, 7.4, 0))]
        part = 'arm%d' % k
        m.tube(pts, [3.4, 2.9, 2.3, 1.7, 1.1, 0.5], 'ink', part)
        # a row of pale suckers along the underside of the curl
        for i, t in enumerate((0.32, 0.5, 0.66, 0.8)):
            q = lerp(pts[int(t * 5)], pts[min(5, int(t * 5) + 1)], (t * 5) % 1)
            m.paint(add(q, (0, -1.2, 0)), 0.9 - i * 0.12, 'sucker', [part])
    # ---- the squat mantle, drooping back into a curled hood tip
    body_c, body_r = (0, 16.0, -1.0), (10.0, 8.6, 9.0)
    m.ell(body_c, body_r, 'ink', 'body')
    m.ell((0, 10.0, 0.0), (8.0, 4.0, 7.6), 'ink', 'body')
    hood = [(0, 20.0, -3.0), (0.5, 26.0, -3.8), (2.2, 30.5, -3.5), (5.2, 33.0, -3.0),
            (8.2, 32.0, -2.6), (8.8, 29.2, -2.2), (7.0, 28.2, -2.0)]
    m.tube(hood, [6.6, 4.8, 3.3, 2.3, 1.6, 1.0, 0.5], 'ink', 'hood')
    m.sph((7.2, 28.6, -1.4), 0.8, 'teal', 'hood')
    # teal spots on the mantle
    for (x, y, z, r) in ((6.8, 21.0, 2.5, 1.2), (-7.0, 20.5, 2.0, 1.1),
                         (4.0, 24.0, 0.5, 1.0), (9.4, 16.5, 1.0, 0.9),
                         (-4.0, 24.0, 0.0, 0.9)):
        m.paint((x, y, z), r, 'teal', ['body'])
    # ---- huge glowing eyes and a little beak
    for s in (-1, 1):
        a = (s * 30 + 6) * DEG
        dd = (math.sin(a), 0.05, math.cos(a))
        p, n = g.surf(body_c, body_r, dd)
        m.paint(p, (3.6, 3.8, 1.6), 'ink', ['body'])
        m.eye(p, n, 5.0, 5.6, style='glow', iris=('teal', 1), pupil=('ink', 0),
              glint=True, center=(0, 15, 12))
    p, n = g.surf(body_c, body_r, (0.08, -0.45, 1))
    m.mouth(p, n, 'w', w=3.0, color=('sucker', 1))
    # ---- drops of ink hanging around it
    for (c, r) in (((13.5, 21.0, 4.0), 1.6), ((-14.0, 18.0, 2.0), 1.4),
                   ((9.0, 29.0, -2.0), 1.2), ((-10.0, 27.0, -3.0), 1.3),
                   ((16.0, 13.0, 8.0), 1.1)):
        m.sph(c, r, 'ink', 'drops')
        m.tube([add(c, (0, r * 0.6, 0)), add(c, (0, r * 2.4, 0))], [r * 0.7, 0.15], 'ink',
               'drops')
        m.paint(add(c, (-r * 0.4, r * 0.3, r * 0.6)), r * 0.45, 'teal', ['drops'])
    return m


# ==========================================================================
# 144 OBSIDRAKE  WYRM/STONE  (WYRM + STONE)
# A low, heavy drake of glossy volcanic glass. A ridge of shards runs from
# brow to tail, its folded wings are knapped blades, and violet heat glows
# through the cracks between its plates.
# ==========================================================================
def obsidrake(g):
    m = g.Model('OBSIDRAKE')
    m.outline = (12, 8, 20)
    m.mat('glass', ['#0a0812', '#1a1530', '#2e2850', '#b0a8e0'], spec=0.9,
          th=[0.2, 0.6, 0.97])
    m.mat('blade', ['#1a1530', '#2e2850', '#4c4480', '#d8d0ff'], spec=0.9,
          th=[0.22, 0.58, 0.93])
    m.mat('seam', ['#6a1aa8', '#a848f0', '#dc9cff'], emissive=0.45)
    m.eye_dark = (12, 8, 20)
    m.white = (220, 156, 255)
    m.height = 54
    m.max_w = 62
    m.front_yaw = -24
    # ---- heavy low body
    m.ell((0, 11.0, -3.0), (8.0, 6.4, 11.5), 'glass', 'body')
    m.ell((0, 12.0, 6.5), (7.4, 6.8, 6.4), 'glass', 'body')
    # violet seams glowing through cracks between the plates
    for cc, rr, dirs in (((0, 12.0, 6.5), (7.4, 6.8, 6.4),
                          [(0.2, 0.9, 0.5), (0.0, 0.5, 1), (0.25, 0.1, 1), (0.05, -0.3, 1),
                           (0.3, -0.6, 1)]),
                         ((0, 11.0, -3.0), (8.0, 6.4, 11.5),
                          [(1, 0.75, 0.55), (1, 0.0, 0.3), (1, 0.6, 0.02),
                           (1, -0.15, -0.28), (1, 0.55, -0.55), (0.8, -0.1, -0.85)]),
                         ((0, 11.0, -3.0), (8.0, 6.4, 11.5),
                          [(-1, 0.75, 0.55), (-1, 0.0, 0.3), (-1, 0.6, 0.02),
                           (-1, -0.15, -0.28), (-1, 0.55, -0.55), (-0.8, -0.1, -0.85)])):
        pts = [g.surf(cc, rr, norm(d))[0] for d in dirs]
        paint_path(m, pts, 1.0, 'seam', ['body'], steps=6)
    # ---- short, splayed legs on glass claws
    for s in (-1, 1):
        for zz, nm in ((7.5, 'legF'), (-8.5, 'legB')):
            part = '%s%d' % (nm, s)
            m.ell((s * 6.4, 10.5, zz), (3.4, 4.6, 4.0), 'glass', part)
            m.tube([(s * 7.4, 8.0, zz), (s * 8.6, 4.4, zz + 0.8), (s * 8.8, 2.2, zz + 1.2)],
                   [3.0, 2.6, 2.6], 'glass', part)
            m.ell((s * 8.8, 1.6, zz + 1.8), (3.0, 1.6, 3.2), 'glass', part)
            paint_path(m, [(s * 9.0, 8.4, zz + 2.6), (s * 9.6, 6.2, zz + 3.2),
                           (s * 9.2, 4.2, zz + 3.4)], (0.8, 0.8, 1.0), 'seam', [part],
                           steps=4)
            for t in (-1, 0, 1):
                m.crystal((s * 8.8 + t * 1.4, 1.4, zz + 3.4),
                          (s * 8.8 + t * 1.9, 0.5, zz + 5.4), 0.7, 'blade', part,
                          sides=3, tip_frac=0.8)
    # ---- thick tail tapering to a blade
    tail = [(0, 10.0, -13.0), (1.0, 8.0, -18.0), (3.0, 5.5, -22.5), (6.0, 4.0, -25.5)]
    m.tube(tail, [5.0, 3.6, 2.4, 1.2], 'glass', 'tail')
    m.crystal((6.0, 4.0, -25.5), (9.5, 4.2, -29.5), 1.6, 'blade', 'tail', sides=3,
              tip_frac=0.7)
    paint_path(m, [(3.0, 11.6, -14.0), (4.0, 8.5, -18.0), (4.2, 6.6, -21.0)], 0.6, 'seam',
               ['tail'], steps=5)
    # ---- half-raised wings: a glass arm to the wrist, then a fan of knapped
    #      blades hanging down and back, violet glow between the blades
    for s in (-1, 1):
        part = 'wing%d' % s
        sh_ = (s * 5.0, 16.5, 3.0)
        el = (s * 12.0, 23.5, -2.0)
        wr = (s * 16.5, 29.0, -7.0)
        m.tube([sh_, el, wr], [2.2, 1.7, 1.2], 'glass', part)
        m.crystal(wr, add(wr, (s * 1.0, 3.2, -1.2)), 0.9, 'blade', part, sides=3,
                  tip_frac=0.7)
        # (the blades trail back rather than down, leaving the flank seams bare)
        for k, (dx, dy, dz, ln, wd) in enumerate(((0.35, -0.35, -0.9, 16.0, 3.0),
                                                  (0.3, -0.55, -0.8, 13.5, 2.8),
                                                  (0.2, -0.7, -0.6, 10.5, 2.6),
                                                  (0.1, -0.8, -0.4, 7.0, 2.3))):
            base = lerp(wr, el, k * 0.3)
            d = norm((s * dx, dy, dz))
            tip = add(base, mul(d, ln))
            mid = add(lerp(base, tip, 0.5), (s * 0.4, 0.6, -0.6))
            nrm = (s * 1.0, 0.1, 0.25)
            g.leaf(m, base, mid, tip, wd, 'blade', part, up=nrm, flat=0.22)
            if k:
                dn = mul(norm((-s * 0.3, 0.4, 0.8)), 0.9)
                g.leaf(m, add(base, dn), add(mid, dn), add(tip, dn), wd + 0.3, 'seam', part,
                       up=nrm, flat=0.18)
    # ---- shard ridge from the nape to the tail
    ridge = [((0, 18.8, 8.0), 3.2), ((0, 18.6, 3.5), 4.6), ((0, 17.8, -1.5), 5.6),
             ((0, 16.8, -6.5), 4.8), ((0, 15.0, -11.0), 3.8), ((0.8, 12.4, -16.0), 3.0),
             ((2.4, 9.0, -20.5), 2.2)]
    for i, (q, h) in enumerate(ridge):
        lean = (0.3 * (-1) ** i, 1.0, -0.45)
        m.crystal(add(q, (0, -1.4, 0)), add(q, mul(norm(lean), h)), 1.4 + h * 0.12,
                  'blade', 'ridge', sides=4, tip_frac=0.55, twist=20 * i)
    # ---- short neck, low wedge head with swept glass horns
    m.tube([(0, 13.0, 10.0), (0, 14.5, 13.5), (0, 15.2, 16.0)], [5.0, 4.4, 4.0], 'glass',
           'neck')
    for s in (-1, 1):
        paint_path(m, [(s * 4.2, 15.0, 11.0), (s * 4.4, 13.0, 12.8), (s * 3.9, 15.4, 15.0)],
                   0.9, 'seam', ['neck'], steps=4)
    head_c, head_r = (0, 16.2, 18.0), (4.8, 3.8, 5.0)
    m.ell(head_c, head_r, 'glass', 'head')
    m.tube([(0, 15.4, 20.0), (0, 14.8, 23.2), (0, 14.4, 25.0)], [3.4, 2.8, 2.2], 'glass',
           'head')
    for s in (-1, 1):
        pts = [g.surf(head_c, head_r, norm(d))[0] for d in
               ((s * 0.6, -0.5, 0.6), (s * 0.95, -0.3, 0.1), (s * 0.85, 0.1, -0.5))]
        paint_path(m, pts, 0.8, 'seam', ['head'], steps=4)
    for s in (-1, 1):
        m.crystal((s * 2.8, 18.8, 16.5), (s * 4.8, 22.2, 11.0), 1.2, 'blade', 'horn%d' % s,
                  sides=4, tip_frac=0.6)
        m.crystal((s * 4.2, 16.6, 15.8), (s * 7.4, 17.2, 11.8), 0.9, 'blade', 'horn%d' % s,
                  sides=3, tip_frac=0.6)
    m.crystal((0, 19.4, 18.0), (0, 23.0, 14.5), 1.1, 'blade', 'ridge', sides=4,
              tip_frac=0.6)
    g.eye_pair(m, head_c, head_r, 40, 16, 3.6, 2.6, style='glow', iris=('seam', 1),
               slant=0.9, glint=False, center=(0, 15, 24), turn=4)
    m.dot((0.8, 15.6, 25.2), (0.2, 0.3, 1), w=1.0, h=1.0, color=('seam', 0))
    return m
