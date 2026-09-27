"""Art for kin 76-83 (KIN-B2).

One model function per species (the lowercase species name), called by
tools/gen_monsters.py as fn(g) with g = the gen_monsters module. Coordinates:
+Y up, +Z the way the kin faces, +X its left; the ground is y = 0.
"""

import math

DEG = math.pi / 180.0


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def norm(a):
    ln = math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])
    return (0.0, 0.0, 1.0) if ln < 1e-12 else (a[0] / ln, a[1] / ln, a[2] / ln)


def sdir(az, el):
    """Unit direction: az degrees toward +X from +Z, el degrees up."""
    a, e = az * DEG, el * DEG
    return (math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e))


def hover(g, m, px, side=None):
    """Hovering kin: lifted on the front sprite and in the overworld."""
    m.float_lift = max(m.float_lift, 2)
    g.OW_FLOAT[m.name] = px
    if side is not None:
        g.OW_SIDE_YAW[m.name] = side


def flower(m, c, nrm, r, petal, heart, part, n=5, phase=0.0):
    """A flat daisy facing nrm: n round petals and a heart."""
    ax = norm(nrm)
    u = norm((ax[1] * 0 - ax[2] * 1, 0.0, ax[0])) if abs(ax[1]) < 0.9 else (1.0, 0.0, 0.0)
    u = norm(sub(u, mul(ax, u[0] * ax[0] + u[1] * ax[1] + u[2] * ax[2])))
    v = (ax[1] * u[2] - ax[2] * u[1], ax[2] * u[0] - ax[0] * u[2], ax[0] * u[1] - ax[1] * u[0])
    for k in range(n):
        a = (360.0 * k / n + phase) * DEG
        d = add(mul(u, math.cos(a)), mul(v, math.sin(a)))
        m.ell_axes(add(c, mul(d, r * 0.62)), (mul(d, r * 0.55), mul(norm(add(mul(u, -math.sin(a)), mul(v, math.cos(a)))), r * 0.36), mul(ax, r * 0.18)), petal, part)
    m.sph(add(c, mul(ax, r * 0.12)), r * 0.36, heart, part)


def gauze_wing(g, m, root, s, ln, wd, ang, mat, part, back=0.45, lift=0.0, puff=0.3):
    """A rounded glassy insect wing in a plane swept back from root."""
    uvec = norm((s * 1.0, lift, -back))
    pts = g.wing_shape(ln * 0.5, 0.0, ln * 0.5, wd, 14, tip=0.15, rot=ang)
    m.poly([add(root, add(mul(uvec, x), (0, y, 0))) for x, y in pts], mat, part, puff=puff)


# ==========================================================================
# 76 HUMBEE  SWARM/BLOOM  round glow bee
# A chubby fuzzy bumblebee: a honey-glow tail that flashes in time with
# the hive, pollen baskets on its legs and a clover flower on its head.
# ==========================================================================
def humbee(g):
    m = g.Model('HUMBEE')
    m.outline = (48, 30, 24)
    m.mat('fuzz', ['#c07818', '#f0b828', '#ffe474'])
    m.mat('band', ['#2e2020', '#553a34'])
    m.mat('glow', ['#ffd84a', '#fffbd0'], emissive=1.0)
    m.mat('wing', ['#a8c8e0', '#eef8ff'])
    m.mat('petal', ['#e45c96', '#ffb4d2'])
    m.eye_dark = (46, 32, 32)
    m.white = (255, 255, 248)
    m.height = 30
    m.front_yaw = -46
    hover(g, m, 4, side=-66)
    # glassy wings buzzing up and back
    for s in (-1, 1):
        gauze_wing(g, m, (s * 2.0, 15.4, -1.0), s, 8.0, 3.2, 38, 'wing', 'wingF%d' % s, back=0.5)
        gauze_wing(g, m, (s * 2.0, 14.6, -1.8), s, 5.6, 2.2, 6, 'wing', 'wingH%d' % s, back=0.7)
        m.group('wingF%d' % s, 'wingH%d' % s)
    # round fuzzy body: one ball, a dark band, the glowing tail
    bc, br = (0, 9.6, -1.6), (6.0, 5.8, 7.2)
    g.seedball(m, bc, br, 'fuzz', 'body', n=60, fil=0.16, tip=0.5, seed=5)
    for z in (0.4, -3.6, -6.6):
        m.paint((0, 9.8, z), (7.8, 7.4, 1.5), 'band', ['body'], rot=(0, -10, 0))
    # the honey-glow tail: a big lantern bulb poking out behind and up
    m.ell((0, 10.4, -8.6), (4.8, 4.8, 3.6), 'glow', 'tail', rot=(0, -24, 0))
    m.tube([(0, 9.4, -11.6), (0, 8.8, -13.4)], [0.8, 0.2], 'band', 'tail')
    # stubby legs with fat pollen baskets
    for s in (-1, 1):
        for k, z in enumerate((2.2, -0.4)):
            b = (s * 3.2, 5.2, z)
            m.tube([b, add(b, (s * 1.0, -2.0, 0.6)), add(b, (s * 1.2, -3.4, 0.8))],
                   [0.7, 0.6, 0.5], 'band', 'leg%d' % s)
        m.sph((s * 4.6, 2.6, -0.4), 1.25, 'glow', 'leg%d' % s)
    # head: cream-fuzzy face, big eyes, antennae with pollen tips
    hc, hr = (0, 11.4, 5.0), (4.4, 4.0, 3.4)
    m.ell(hc, hr, 'fuzz', 'head')
    for s in (-1, 1):
        pts = [(s * 1.4, 14.6, 5.2), (s * 2.4, 17.6, 5.6), (s * 4.0, 19.0, 4.8)]
        m.tube(pts, [0.45, 0.4, 0.35], 'band', 'ant%d' % s)
        m.sph(pts[-1], 0.9, 'glow', 'ant%d' % s)
    # clover flower tucked on the head
    flower(m, (1.6, 16.4, 2.4), (0.45, 0.8, 0.45), 3.8, 'petal', 'glow', 'flower', n=5)
    g.eye_pair(m, hc, hr, 25, 8, 3.2, 3.8, style='cute', center=(0, 11, 9), turn=16)
    for s in (-1, 1):
        p, n = g.on(hc, hr, sdir(52 * s + 14, -14))
        m.paint(p, (1.0, 0.7, 0.8), 'petal', ['head'])
    p, n = g.on(hc, hr, sdir(14, -30))
    m.mouth(p, n, 'smile', w=1.8)
    return m


def hex_cells(m, c, r, rows, mat, part, cell=1.0, y0=-0.9, y1=0.85, az0=-160, az1=160, step=2.6):
    """Honeycomb: glowing cells painted on an ellipsoid gown in an offset
    hex lattice, the wax between them left as the cell walls."""
    for j in range(rows):
        t = j / float(max(1, rows - 1))
        yy = y0 + (y1 - y0) * t
        rr = math.sqrt(max(0.0, 1 - yy * yy))
        circ = 2 * math.pi * rr * (r[0] + r[2]) * 0.5
        n = max(4, int(circ / step))
        off = 0.5 if j % 2 else 0.0
        for k in range(n):
            a = (k + off) * 360.0 / n
            if a > 180:
                a -= 360
            if a < az0 or a > az1:
                continue
            p, nn = surf(c, r, sdir(a, math.asin(yy) / DEG))
            m.paint(p, cell, mat, [part])


def surf(c, r, d):
    t = 1.0 / math.sqrt((d[0] / r[0]) ** 2 + (d[1] / r[1]) ** 2 + (d[2] / r[2]) ** 2)
    p = mul(d, t)
    return add(c, p), norm((p[0] / r[0] ** 2, p[1] / r[1] ** 2, p[2] / r[2] ** 2))


# ==========================================================================
# 77 COMBQUEEN  SWARM/BLOOM  hive queen in a honeycomb gown
# A regal queen bee standing tall: a big golden bee face with huge eyes, a
# crown and curled antennae, a fuzzy striped thorax with a white ruff, her
# abdomen a flared gown of living honeycomb with every cell aglow, glassy
# wings spread wide behind her, and a flower sceptre in one hand.
# ==========================================================================
def combqueen(g):
    m = g.Model('COMBQUEEN')
    m.outline = (52, 28, 22)
    m.mat('wax', ['#8a4e14', '#c8841e', '#f0b43a'])
    m.mat('honey', ['#ff9e1a', '#fff09a'], emissive=0.8)
    m.mat('fuzz', ['#3a2622', '#5c3e34'])
    m.mat('ruff', ['#fffff8'])
    m.mat('wing', ['#86b2d8', '#dcf0ff'])
    m.mat('petal', ['#e45c96', '#ffb4d2'])
    m.eye_dark = (58, 38, 34)
    m.white = (255, 255, 248)
    m.height = 58
    m.max_w = 62
    m.front_yaw = -22
    # glassy wings spread wide behind her, the hind pair lower
    for s in (-1, 1):
        root = (s * 2.6, 29.0, -4.2)
        gauze_wing(g, m, root, s, 20.0, 6.4, 34, 'wing', 'wingF%d' % s, back=0.32, puff=0.25)
        gauze_wing(g, m, add(root, (0, -2.2, -0.4)), s, 13.0, 4.4, -12, 'wing', 'wingH%d' % s,
                   back=0.36, puff=0.25)
        m.group('wingF%d' % s, 'wingH%d' % s)
    # the gown: a flared bell of dark wax (her abdomen) built as a lathe of
    # thin discs, every honeycomb cell on it aglow; flowers along the hem
    ys = (0.6, 4.0, 9.0, 14.0, 18.4, 20.4)
    rs = (10.6, 10.4, 9.0, 6.8, 4.6, 3.6)
    gz = -0.8
    y = ys[0]
    while y <= ys[-1]:
        rr = g_rad(ys, rs, y)
        m.ell((0, y, gz), (rr, 0.7, rr * 0.94), 'fuzz', 'gown')
        y += 0.5
    for j in range(5):
        y = 2.6 + j * 3.3
        rr = g_rad(ys, rs, y)
        n = max(5, int(2 * math.pi * rr / 3.4))
        for k in range(n):
            az = (k + (0.5 if j % 2 else 0)) * 360.0 / n
            p = (math.sin(az * DEG) * rr, y, gz + math.cos(az * DEG) * rr * 0.94)
            m.paint(p, (1.4, 1.3, 1.4), 'honey', ['gown'])
    for k, az in enumerate((-70, -28, 14, 56)):
        rr = g_rad(ys, rs, 1.8) + 0.2
        p = (math.sin(az * DEG) * rr, 1.8, gz + math.cos(az * DEG) * rr)
        flower(m, p, sdir(az, 8), 2.2, 'petal', 'honey', 'hem', n=5, phase=k * 17)
    # fuzzy thorax in gold and black stripes, a white ruff collar
    tc, tr = (0, 25.4, 0.0), (5.6, 4.8, 5.0)
    g.seedball(m, tc, tr, 'wax', 'thorax', n=40, fil=0.12, tip=0.4, seed=4)
    for y in (22.6, 26.2):
        m.paint((0, y, 0), (7.0, 0.95, 7.0), 'fuzz', ['thorax'])
    for k in range(14):
        a = k * 360.0 / 14 * DEG
        m.ell((math.sin(a) * 5.0, 29.6, math.cos(a) * 4.6), (2.0, 1.2, 2.0), 'ruff', 'ruff',
              rot=(k * 360.0 / 14, 0, 30))
    # arms: one hand on her gown, one raising a flower sceptre
    m.tube([(-4.8, 27.0, 1.0), (-8.0, 22.6, 2.6), (-6.4, 18.8, 5.2)], [1.25, 1.05, 1.0], 'fuzz', 'arm-1')
    m.sph((-6.2, 18.6, 5.6), 1.4, 'fuzz', 'arm-1')
    m.tube([(4.8, 27.0, 1.0), (9.6, 23.6, 3.8), (11.6, 26.4, 6.4)], [1.25, 1.05, 1.0], 'fuzz', 'arm1')
    m.tube([(12.2, 11.0, 7.2), (12.0, 26.0, 6.6), (11.8, 36.0, 6.2)], [0.75, 0.75, 0.7], 'wax', 'sceptre')
    m.sph((11.9, 26.4, 6.6), 1.5, 'fuzz', 'sceptre')
    flower(m, (11.8, 38.4, 6.6), (0.2, 0.25, 1.0), 4.6, 'petal', 'honey', 'bloom', n=6)
    # big golden bee head: round face, huge dark eyes
    hc, hr = (0, 36.6, 1.4), (7.4, 6.2, 6.0)
    m.ell(hc, hr, 'wax', 'head')
    m.paint(g.on(hc, hr, sdir(8, -26))[0], (3.2, 2.2, 2.0), 'honey', ['head'])
    # antennae curling out, glowing tips
    for s in (-1, 1):
        pts = [(s * 2.6, 41.4, 2.6), (s * 4.6, 45.6, 2.8), (s * 7.4, 47.6, 2.2), (s * 9.0, 46.0, 2.0)]
        m.tube(pts, [0.55, 0.5, 0.45, 0.42], 'fuzz', 'ant%d' % s)
        m.sph(pts[-1], 1.1, 'honey', 'ant%d' % s)
    # a crown of golden points with a honey jewel
    cc = (0, 42.8, 0.4)
    m.tube([add(cc, (math.sin(a * DEG) * 3.4, 0, math.cos(a * DEG) * 2.6)) for a in range(-180, 181, 30)],
           0.9, 'fuzz', 'crown')
    for k in range(5):
        a = (k - 2) * 36 * DEG
        b = add(cc, (math.sin(a) * 3.2, 0.2, math.cos(a) * 2.4))
        m.crystal(b, add(b, (math.sin(a) * 1.0, 6.4 - abs(k - 2) * 1.2, 0)), 1.2, 'honey', 'crown',
                  sides=4, tip_frac=0.55)
    m.sph(add(cc, (0, 1.0, 2.6)), 1.1, 'petal', 'crown')
    g.eye_pair(m, hc, hr, 34, 4, 5.0, 6.0, style='cute', center=(0, 36, 8), turn=8)
    p, n = g.on(hc, hr, sdir(8, -34))
    m.mouth(p, n, 'smile', w=2.2)
    return m


def g_rad(ys, rs, y):
    """Radius of a straight-segment profile (ys, rs) at height y."""
    for i in range(len(ys) - 1):
        if ys[i] <= y <= ys[i + 1]:
            t = (y - ys[i]) / (ys[i + 1] - ys[i])
            return rs[i] + (rs[i + 1] - rs[i]) * t
    return rs[0] if y < ys[0] else rs[-1]


def spider_leg(m, hip, knee, foot, r, mat, part, tip_mat=None):
    """A jointed spider leg: hip -> high knee -> foot, with a knee bead."""
    m.tube([hip, knee], [r, r * 0.9], mat, part)
    m.sph(knee, r * 1.05, mat, part)
    m.tube([knee, lerp(knee, foot, 0.6), foot], [r * 0.9, r * 0.75, r * 0.5],
           mat, part, mats=[(0, mat), (0.7, tip_mat or mat)])


# ==========================================================================
# 78 WEBBIT  SWARM/VENOM  fuzzy spiderling
# A round purple fuzzball on eight stubby legs, lime spots on its bottom,
# big shiny eyes (and two little ones), and a silk thread with a tuft to
# sail away on.
# ==========================================================================
def webbit(g):
    m = g.Model('WEBBIT')
    m.outline = (36, 20, 48)
    m.mat('fur', ['#3c2462', '#6a44a0', '#9a76cc'])
    m.mat('lime', ['#86c41c', '#d8fa6a'], emissive=0.3)
    m.mat('leg', ['#4c3470', '#7858a4'])
    m.mat('silk', ['#c4c0dc', '#fffff8'])
    m.mat('face', ['#a482d4', '#d2bcee'])
    m.eye_dark = (26, 16, 38)
    m.white = (255, 255, 248)
    m.height = 35
    m.front_yaw = -30
    # the fuzzy abdomen with lime spots and a curl of silk on the spinnerets
    ac, ar = (0, 9.2, -4.6), (5.6, 5.2, 5.2)
    g.seedball(m, ac, ar, 'fur', 'body', n=56, fil=0.2, tip=0.55, seed=11)
    for (az, el, r) in ((0, 62, 1.5), (-44, 34, 1.3), (44, 34, 1.3), (-90, 10, 1.2), (90, 10, 1.2),
                        (0, 20, 1.4)):
        p, n = surf(ac, ar, sdir(az + 180, el))
        m.paint(p, r, 'lime', ['body'])
    m.tube([(0, 8.4, -9.8), (0.6, 11.0, -11.4), (1.6, 13.0, -10.8), (1.4, 11.8, -9.8)],
           [0.55, 0.5, 0.45, 0.4], 'silk', 'silk')
    # eight stubby legs
    for s in (-1, 1):
        for k, (z, sp) in enumerate(((4.4, 0.6), (2.4, 0.25), (0.2, -0.2), (-2.0, -0.6))):
            hip = (s * 2.6, 6.2, z)
            knee = (s * 7.0, 7.2, z + sp * 2.4)
            foot = (s * 8.8, 0.6, z + sp * 4.6)
            spider_leg(m, hip, knee, foot, 0.8, 'leg', 'leg%s%d' % ('abcd'[k], s), tip_mat='lime')
    # head: a big round face in front with a fuzzy tuft
    hc, hr = (0, 9.2, 3.4), (6.0, 5.4, 4.6)
    m.ell(hc, hr, 'fur', 'head')
    m.paint(g.on(hc, hr, sdir(8, 0))[0], (5.4, 4.4, 2.6), 'face', ['head'])
    for d in ((0, 1, -0.3), (0.5, 0.85, -0.4), (-0.5, 0.85, -0.4)):
        b = add(hc, (0, hr[1] * 0.8, -1.4))
        m.tube([b, add(b, mul(norm(d), 2.4))], [1.0, 0.25], 'fur', 'head')
    # two tiny lime fangs
    for s in (-1, 1):
        m.tube([(s * 1.2, 5.2, 7.0), (s * 1.2, 4.0, 7.4), (s * 0.9, 3.4, 7.2)], [0.6, 0.45, 0.2],
               'lime', 'head')
    g.eye_pair(m, hc, hr, 40, 6, 3.8, 4.6, style='cute', center=(0, 9, 10), turn=8)
    # the little second pair of eyes above
    g.eye_pair(m, hc, hr, 20, 48, 1.8, 1.8, style='solid', iris=('lime', 1), center=(0, 10, 10), turn=8,
               glint=False, minw=2, minh=2)
    p, n = g.on(hc, hr, sdir(8, -30))
    m.mouth(p, n, 'smile', w=1.8)
    # overworld: sink the abdomen a little so the face shows from above
    m.ow_offsets = {'body': (0, -1.8, -1.2), 'silk': (0, -1.8, -1.2)}
    return m


# ==========================================================================
# 79 LACEWIDOW  SWARM/VENOM  spider in a lace veil
# A tall, elegant widow on arched legs: glossy violet-black body, a lime
# hourglass, and a mourning veil of web-lace draped over head and back.
# ==========================================================================
def lacewidow(g):
    m = g.Model('LACEWIDOW')
    m.outline = (26, 14, 34)
    m.mat('body', ['#1c1228', '#352450', '#5c4280', '#8a6cb4'], spec=0.5)
    m.mat('lace', ['#a49ec8', '#dcd8f0', '#fffff8'])
    m.mat('hole', ['#352450'])
    m.mat('lime', ['#86c41c', '#d8fa6a'], emissive=0.5)
    m.mat('leg', ['#2a1c3e', '#46366a', '#6c5a94'])
    m.eye_dark = (22, 12, 30)
    m.white = (255, 255, 248)
    m.height = 46
    m.max_w = 62
    m.front_yaw = -30
    # eight strong arched legs: up and out to high knees, then splayed wide
    # to the tips, the front pair reaching forward well clear of the face
    for s in (-1, 1):
        for k, (z, fz, kx, ky, fx) in enumerate(((3.0, 8.0, 8.4, 20.0, 18.0), (1.4, 3.0, 9.6, 21.6, 21.0),
                                                (-0.4, -3.0, 9.6, 21.2, 21.0), (-2.0, -9.0, 8.6, 19.4, 18.0))):
            hip = (s * 3.0, 11.0, z)
            knee = (s * kx, ky, lerp((0, 0, z), (0, 0, fz), 0.45)[2])
            foot = (s * fx, 0.6, fz)
            part = 'leg%s%d' % ('abcd'[k], s)
            m.tube([hip, lerp(hip, knee, 0.5), knee], [1.25, 1.15, 1.05], 'leg', part)
            m.sph(knee, 1.2, 'leg', part)
            mid = add(lerp(knee, foot, 0.45), (s * 0.6, 3.2, 0))
            m.tube([knee, mid, foot], [1.05, 0.85, 0.45], 'leg', part, mats=[(0, 'leg'), (0.86, 'lime')])
    # thorax
    m.ell((0, 11.6, 0.6), (4.0, 3.2, 4.2), 'body', 'thorax')
    # the abdomen: a big glossy drop tilted up behind
    ac, ar = (0, 19.0, -8.6), (8.6, 9.2, 8.2)
    m.ell(ac, ar, 'body', 'abdomen')
    # the lace shawl draped over her back and down both flanks, leaving the
    # front slope (and the hourglass) bare: pale lace with rows of holes and
    # a scalloped hem along its edge
    sc, sr = (0, ac[1] + 7.0, ac[2] - 3.4), (10.0, 10.4, 11.4)

    def inside(p):
        return sum(((p[q] - sc[q]) / sr[q]) ** 2 for q in range(3))
    m.paint(sc, sr, 'lace', ['abdomen'])
    for j in range(6):
        el = 72 - j * 17
        n = max(3, int(round(12 * math.cos(el * DEG) + 1)))
        for k in range(n):
            az = (k + (0.5 if j % 2 else 0)) * 360.0 / n
            p, nn = surf(ac, ar, sdir(az, el))
            if inside(p) < 0.72:
                m.paint(p, 1.35, 'hole', ['abdomen'])
    for k in range(24):
        az = k * 15
        prev = None
        for e in range(80, -45, -3):
            p, nn = surf(ac, ar, sdir(az, e))
            if inside(p) > 1.0:
                break
            prev = p
        if prev is not None:
            m.sph(prev, 1.15, 'lace', 'hem')
    # a bare window in the lace on top of her back, the lime hourglass in it
    hg, hn = surf(ac, ar, sdir(16, 44))
    rot_hg = (16, -40, 0)
    m.paint(hg, (3.6, 4.8, 3.6), 'hole', ['abdomen'], rot=rot_hg)
    for dy in (-1, 1):
        m.paint(add(hg, mul((0, 0.72, -0.69), dy * 2.1)), (2.2, 1.4, 2.2), 'lime', ['abdomen'], rot=rot_hg)
    m.paint(hg, (0.9, 1.6, 2.0), 'lime', ['abdomen'], rot=rot_hg)
    m.group('hem', 'abdomen')
    # head, set forward and turned to the viewer
    hc, hr = (0, 15.0, 6.2), (5.0, 4.6, 4.2)
    m.ell(hc, hr, 'body', 'head')
    for s in (-1, 1):
        m.tube([(s * 1.4, 12.0, 9.2), (s * 1.5, 10.2, 10.0), (s * 1.0, 9.0, 9.6)], [0.9, 0.65, 0.2],
               'leg', 'head', mats=[(0, 'leg'), (0.7, 'lime')])
    # a lace mantilla comb on her head, lime pearl in the middle
    comb = (0, 19.2, 3.4)
    for k in range(7):
        a = (k - 3) * 22 * DEG
        b = add(comb, (math.sin(a) * 2.8, 0, math.cos(a) * 0.6))
        m.tube([b, add(b, (math.sin(a) * 1.6, 4.6 - abs(k - 3) * 0.7, -0.4))], [0.8, 0.45], 'lace', 'comb')
    m.ell(comb, (3.2, 1.0, 1.4), 'lace', 'comb')
    m.sph(add(comb, (0, 1.4, 0.4)), 0.9, 'lime', 'comb')
    g.eye_pair(m, hc, hr, 32, 4, 3.4, 4.0, style='glow', iris=('lime', 1), pupil='eye',
               center=(0, 15, 11), turn=16, slant=0.7)
    return m


def bat_wing(m, s, shoulder, elbow, wrist, fingers, hip, mem, bone, part, r=0.8, sag=2.4, puff=0.3):
    """Bat wing: an arm shoulder->elbow->wrist, finger struts fanning from
    the wrist, and a membrane scalloped between the finger tips."""
    pts = [shoulder, elbow, wrist, fingers[0]]
    for i in range(len(fingers) - 1):
        a, b = fingers[i], fingers[i + 1]
        mid = lerp(a, b, 0.5)
        pts.append(add(lerp(mid, wrist, sag / 10.0), (0, 0, 0.2)))
        pts.append(b)
    mid = lerp(fingers[-1], hip, 0.5)
    pts.append(lerp(mid, wrist, sag / 12.0))
    pts.append(hip)
    m.poly(pts, mem, part, puff=puff)
    m.tube([shoulder, elbow, wrist], [r * 1.2, r, r * 0.9], bone, part)
    for f in fingers:
        m.tube([wrist, f], [r * 0.75, r * 0.35], bone, part)
    m.sph(wrist, r * 1.1, bone, part)


# ==========================================================================
# 80 SQUEAKLE  DUSK/GALE  bat pup
# A plum fuzzball that is mostly ears: two huge pink-lined ears, a pair of
# little scalloped wings, a squeaky open mouth with one fang.
# ==========================================================================
def squeakle(g):
    m = g.Model('SQUEAKLE')
    m.outline = (34, 20, 44)
    m.mat('fur', ['#3a2656', '#5e4282', '#8a6cae'])
    m.mat('mem', ['#2a1c40', '#46305e'])
    m.mat('pink', ['#c85a8c', '#f09ab8'])
    m.mat('belly', ['#b8a0c8', '#e4d8ec'])
    m.eye_dark = (26, 16, 34)
    m.white = (255, 255, 248)
    m.height = 26
    m.front_yaw = -24
    hover(g, m, 4, side=-64)
    # little wings held out wide
    for s in (-1, 1):
        sh_ = (s * 3.4, 9.6, -1.0)
        el = (s * 7.4, 12.0, -2.4)
        wr = (s * 10.4, 12.6, -3.2)
        fingers = [(s * 14.0, 11.0, -3.8), (s * 13.2, 6.6, -3.4), (s * 10.0, 3.8, -2.8)]
        bat_wing(m, s, sh_, el, wr, fingers, (s * 3.0, 5.0, -1.2), 'mem', 'fur', 'wing%d' % s, r=0.65)
    # round fuzzy body with a pale belly
    bc, br = (0, 8.6, 0.0), (4.8, 5.0, 4.4)
    g.seedball(m, bc, br, 'fur', 'body', n=44, fil=0.14, tip=0.45, seed=21)
    m.paint(g.on(bc, br, (0.1, -0.2, 1))[0], (2.6, 3.0, 2.0), 'belly', ['body'])
    # tiny feet
    for s in (-1, 1):
        m.ell((s * 1.8, 3.6, 1.8), (0.9, 0.7, 1.1), 'pink', 'foot%d' % s)
    # head merged high on the body
    hc, hr = (0, 12.0, 1.8), (4.2, 3.8, 3.6)
    m.ell(hc, hr, 'fur', 'head')
    # the huge ears
    for s in (-1, 1):
        m.tube([(s * 2.0, 14.4, 1.4), (s * 4.0, 18.8, 1.2), (s * 5.4, 22.4, 0.6), (s * 5.8, 24.2, 0.2)],
               [2.4, 2.9, 2.0, 0.3], 'fur', 'ear%d' % s, flat=0.35, up=(s * 0.25, 0.1, 1))
        m.paint((s * 4.0, 18.8, 2.2), (1.6, 3.4, 1.2), 'pink', ['ear%d' % s], rot=(0, 0, -s * 22))
    # snout, nose, squeaky mouth
    m.ell((0, 11.0, 5.0), (1.8, 1.3, 1.2), 'fur', 'head')
    m.dot(g.on((0, 11.0, 5.0), (1.8, 1.3, 1.2), (0.1, 0.4, 1))[0], (0, 0.3, 1), w=1.4, h=1.0,
          color=('pink', 0))
    g.eye_pair(m, hc, hr, 34, 12, 3.0, 3.6, style='cute', center=(0, 12, 8), turn=8)
    p, n = g.on((0, 11.0, 5.0), (1.8, 1.3, 1.2), (0.1, -0.6, 1))
    m.mouth(p, n, 'open', w=1.8, h=1.6, inner=('pink', 0), fang=1)
    return m


# ==========================================================================
# 81 NOCTAVE  DUSK/GALE  sonar bat with tuning-fork ears
# A big night bat on wide wings; its ears split into silver tuning forks
# and rings of sound roll off them.  The wings carry glowing sound-wave
# bands and its tail curls into a musical note.
# ==========================================================================
def noctave(g):
    m = g.Model('NOCTAVE')
    m.outline = (24, 16, 40)
    m.mat('fur', ['#261a44', '#3e2c66', '#5e4a8e'])
    m.mat('mem', ['#34205a', '#5a3a8a', '#7e5eb2'])
    m.mat('silver', ['#6c6e9a', '#a8acd0', '#fffff8'], spec=0.6)
    m.mat('wave', ['#38c4d8', '#b4f6fa'], emissive=0.7)
    m.mat('pink', ['#c85a8c', '#f09ab8'])
    m.eye_dark = (20, 14, 34)
    m.white = (255, 255, 248)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -20
    hover(g, m, 4, side=-62)
    # wide wings, sound-wave bands glowing across them
    for s in (-1, 1):
        sh_ = (s * 5.0, 24.0, -2.0)
        el = (s * 13.0, 30.0, -4.0)
        wr = (s * 20.0, 32.0, -5.4)
        fingers = [(s * 29.0, 28.0, -6.4), (s * 28.0, 18.0, -6.0), (s * 23.5, 9.4, -5.2),
                   (s * 15.0, 6.0, -4.0)]
        part = 'wing%d' % s
        bat_wing(m, s, sh_, el, wr, fingers, (s * 5.0, 12.0, -2.2), 'mem', 'fur', part, r=1.1)
        for k, rad in enumerate((6.5, 11.5, 16.5)):
            for j in range(11):
                a = (-62 + j * 12) * DEG
                c = add(sh_, (s * (math.cos(a) * rad + 1.0), math.sin(a) * rad * 0.9 - 2.0,
                              -1.4 - rad * 0.12))
                m.paint(c, (0.85, 0.85, 1.6), 'wave', [part])
    # body: a deep furry chest with a glowing note on it
    bc, br = (0, 19.0, 0.0), (6.2, 8.2, 5.4)
    g.seedball(m, bc, br, 'fur', 'body', n=60, fil=0.12, tip=0.6, seed=8)
    nh = (0.2, 14.6, 5.0)
    m.paint(nh, (2.4, 1.8, 2.2), 'wave', ['body'], rot=(0, 0, 20))
    for k in range(6):
        m.paint((2.2, 15.4 + k * 1.3, 4.8), (0.8, 0.9, 2.2), 'wave', ['body'])
    for k in range(4):
        m.paint((2.8 + k * 0.8, 21.8 - k * 1.0, 4.2), (0.85, 0.85, 2.2), 'wave', ['body'])
    # feet tucked up with silver claws
    for s in (-1, 1):
        m.tube([(s * 2.6, 12.0, 0.4), (s * 3.0, 9.0, 1.6)], [1.2, 0.9], 'fur', 'foot%d' % s)
        for k in range(3):
            m.tube([(s * 3.0, 9.0, 1.6), (s * (2.2 + k * 0.8), 7.4, 2.6)], [0.5, 0.3], 'silver', 'foot%d' % s)
    # head
    hc, hr = (0, 30.6, 2.0), (6.0, 5.2, 5.0)
    m.ell(hc, hr, 'fur', 'head')
    mc, mr = (0, 28.4, 6.2), (2.8, 2.1, 1.9)
    m.ell(mc, mr, 'fur', 'head')
    m.ell((0, 29.8, 7.8), (1.3, 0.9, 0.7), 'pink', 'head')
    # tuning-fork ears: a stem out of the head, a U, two tall silver tines
    for s in (-1, 1):
        base = (s * 3.4, 34.4, 0.8)
        stem = (s * 5.6, 38.2, 0.4)
        m.tube([base, stem], [2.0, 1.2], 'fur', 'ear%d' % s)
        u = []
        for j in range(7):
            a = (180 + j * 30) * DEG
            u.append(add(stem, (math.cos(a) * 2.2 + s * 1.2, 1.8 + math.sin(a) * 1.6, 0)))
        m.tube(u, 0.95, 'silver', 'ear%d' % s)
        for t in (-1, 1):
            b = add(stem, (t * 2.2 + s * 1.2, 1.8, 0))
            m.tube([b, add(b, (s * 0.8, 5.0, -0.2)), add(b, (s * 1.4, 9.0, -0.4))], [0.95, 0.95, 0.85],
                   'silver', 'ear%d' % s)
        # rings of sound rolling off the tines
        tip = add(stem, (s * 3.0, 9.4, -0.4))
        for k, rad in enumerate((3.4, 6.0)):
            pts = []
            for j in range(7):
                a = (-50 + j * 100 / 6.0) * DEG
                pts.append(add(tip, (s * (math.cos(a) * rad + 0.8), math.sin(a) * rad + 1.0, 0.4)))
            m.tube(pts, 0.6, 'wave', 'sound%d' % s)
    g.eye_pair(m, hc, hr, 32, 10, 3.8, 4.6, style='sharp', iris=('wave', 0), slant=0.5, lid=1,
               center=(0, 30, 9), turn=6)
    p, n = g.on(mc, mr, (0.05, -0.6, 1))
    m.mouth(p, n, 'open', w=2.6, h=1.8, inner=('pink', 0), fang=1)
    return m


def yrot(p, pivot, ang):
    """Rotate p about a vertical axis through pivot (ang>0 swings +Z toward +X)."""
    a = ang * DEG
    x, z = p[0] - pivot[0], p[2] - pivot[2]
    return (pivot[0] + x * math.cos(a) + z * math.sin(a), p[1], pivot[2] - x * math.sin(a) + z * math.cos(a))


def smoke(m, c, r, mat, part, n=5, seed=1, up=(0, 1, 0)):
    """A little cloud of shadow smoke: overlapping puffs drifting along up."""
    rnd = 0.37 + seed * 0.61
    for k in range(n):
        rnd = (rnd * 7.13 + 0.31) % 1.0
        a = (k * 137.5 + seed * 40) * DEG
        off = (math.cos(a) * r * 0.7, (k / float(max(1, n - 1))) * r * 1.2, math.sin(a) * r * 0.5)
        off = add(off, mul(up, k * r * 0.25))
        m.sph(add(c, off), r * (0.75 - 0.35 * k / float(n) + 0.15 * rnd), mat, part)


# ==========================================================================
# 82 NOXKIT  DUSK  black kitten with glowing eyes
# A sooty kitten sitting up, all ears and eyes: huge gold lamps on a
# black face, a tail curled up into a wisp of shadow smoke.
# ==========================================================================
def noxkit(g):
    m = g.Model('NOXKIT')
    m.outline = (20, 12, 28)
    m.mat('fur', ['#1c1428', '#322650', '#54427a'])
    m.mat('mist', ['#5a4490', '#9a80d0'])
    m.mat('glow', ['#e89c18', '#ffe066', '#fffbd0'], emissive=0.9)
    m.mat('pink', ['#b8507c', '#e888ac'])
    m.mat('sock', ['#1c1428'])
    m.eye_dark = (20, 12, 28)
    m.white = (255, 255, 248)
    m.height = 30
    m.front_yaw = -26
    # sitting: haunches, hind feet, chest, forelegs
    for s in (-1, 1):
        m.ell((s * 3.0, 4.4, -2.0), (2.6, 3.6, 3.8), 'fur', 'hip%d' % s)
        m.ell((s * 3.6, 0.9, 1.0), (1.4, 0.9, 2.2), 'fur', 'foot%d' % s)
        m.tube([(s * 1.7, 7.0, 1.6), (s * 1.8, 3.4, 2.4), (s * 1.9, 1.2, 2.8)], [1.3, 1.1, 1.0],
               'fur', 'legF%d' % s)
        m.ell((s * 1.9, 0.9, 3.4), (1.2, 0.9, 1.4), 'fur', 'legF%d' % s)
    m.ell((0, 7.4, -0.4), (3.4, 4.8, 3.4), 'fur', 'body', rot=(0, -12, 0))
    # tail curling up behind, ending in a wisp of smoke
    tail = [(0, 2.2, -5.2), (3.6, 2.6, -6.4), (6.2, 6.0, -5.8), (6.4, 10.4, -4.6), (5.0, 13.2, -4.0)]
    m.tube(tail, [1.1, 1.0, 0.95, 0.9, 0.8], 'fur', 'tail')
    smoke(m, (5.0, 13.6, -4.0), 1.8, 'mist', 'tail', n=4, seed=2, up=(-0.3, 1, 0))
    # big round head, tall ears
    hc, hr = (0, 14.6, 1.0), (5.4, 4.6, 4.4)
    m.ell(hc, hr, 'fur', 'head')
    for s in (-1, 1):
        m.tube([(s * 2.8, 17.8, 0.4), (s * 3.9, 20.6, 0.0), (s * 4.6, 23.2, -0.4)], [2.4, 1.5, 0.2],
               'fur', 'ear%d' % s, flat=0.4, up=(s * 0.2, 0.1, 1))
        m.paint((s * 3.6, 19.6, 1.0), (1.0, 1.8, 0.8), 'pink', ['ear%d' % s])
        # cheek tufts
        m.tube([(s * 4.4, 13.4, 1.8), (s * 6.6, 12.6, 1.2)], [1.2, 0.2], 'fur', 'head')
        m.tube([(s * 4.4, 12.4, 1.8), (s * 6.2, 11.2, 1.2)], [1.0, 0.2], 'fur', 'head')
    # dark sockets behind the glowing eyes so they read on the lit side too
    for s in (-1, 1):
        p, n = g.on(hc, hr, sdir(30 * s + 8, 6))
        m.paint(p, (2.1, 2.1, 1.2), 'sock', ['head'])
    g.eye_pair(m, hc, hr, 30, 6, 4.2, 4.8, style='glow', iris=('glow', 1), pupil='eye',
               center=(0, 14, 8), turn=8, minw=3, minh=3)
    m.ell((0, 13.0, 5.2), (1.6, 1.1, 0.8), 'fur', 'head')
    m.dot(g.on((0, 13.0, 5.2), (1.6, 1.1, 0.8), (0, 0.4, 1))[0], (0, 0.2, 1), w=1.4, h=1.0,
          color=('pink', 1))
    p, n = g.on(hc, hr, sdir(8, -34))
    m.mouth(p, n, 'w', w=2.2, color=('mist', 1))
    return m


# ==========================================================================
# 83 UMBRAKAT  DUSK/BEAST  shadow panther
# A heavy, muscular panther on the prowl: massive shoulders and neck, head
# slung low below them, one forepaw raised mid-stalk.  Dusky violet fur
# with dark rosettes, burning gold eyes, and a long tail that trails off
# into smoke.
# ==========================================================================
def rosette(m, p, r, mat, fill, part):
    """A panther rosette: a dark ring (a dark disc re-filled with fur)."""
    m.paint(p, r, mat, [part])
    m.paint(p, r * 0.48, fill, [part])


def umbrakat(g):
    m = g.Model('UMBRAKAT')
    m.outline = (8, 5, 15)
    m.mat('fur', ['#120c22', '#221a3e', '#373066', '#56508e'])
    m.mat('mist', ['#6a5aa0', '#b4a4e2'])
    m.mat('glow', ['#e89c18', '#ffe066', '#fffbd0'], emissive=0.9)
    m.mat('ros', ['#08050f'])
    m.mat('pink', ['#9a3e68', '#d07098'])
    m.eye_dark = (8, 5, 15)
    m.white = (255, 255, 248)
    m.height = 48
    m.max_w = 62
    m.front_yaw = -54
    # heavy body: huge shoulders, deep chest, a leaner waist, strong haunches
    parts = []
    sh_c, sh_r = (0, 17.4, 5.4), (5.8, 6.6, 6.2)
    ch_c, ch_r = (0, 12.8, 7.8), (4.4, 5.0, 4.4)
    wa_c, wa_r = (0, 15.6, -2.4), (3.8, 3.6, 7.6)
    hp_c, hp_r = (0, 15.6, -9.6), (5.0, 5.4, 5.0)
    for c, r in ((sh_c, sh_r), (ch_c, ch_r), (wa_c, wa_r), (hp_c, hp_r)):
        m.ell(c, r, 'fur', 'body')
    # rosettes over shoulders, flanks and haunches
    for c, r, spots in ((sh_c, sh_r, ((62, 34), (96, 4), (104, 40))),
                        (wa_c, wa_r, ((90, 34), (95, 2), (72, 14))),
                        (hp_c, hp_r, ((80, 32), (120, 8), (140, 40)))):
        for az, el in spots:
            for s in (-1, 1):
                p, n = surf(c, r, sdir(az * s, el))
                rosette(m, p, 1.8, 'ros', 'fur', 'body')
    # forelegs: thick, one planted, one raised mid-stalk, big paws
    for s in (-1, 1):
        lf = 'legF%d' % s
        m.ell((s * 3.9, 13.6, 7.2), (2.4, 5.0, 3.2), 'fur', lf)
        if s > 0:
            pts = [(s * 4.0, 10.0, 8.0), (s * 4.2, 6.4, 11.4), (s * 4.2, 4.6, 13.4)]
            paw = (s * 4.2, 3.8, 14.4)
        else:
            pts = [(s * 4.0, 10.0, 8.0), (s * 4.1, 5.0, 8.6), (s * 4.1, 1.8, 9.0)]
            paw = (s * 4.1, 1.3, 10.0)
        m.tube(pts, [2.3, 1.6, 1.5], 'fur', lf)
        m.ell(paw, (2.0, 1.2, 2.4), 'fur', lf)
        # hind legs: a crouched, springy bend
        lb = 'legB%d' % s
        bz = -9.0 if s > 0 else -11.0
        m.ell((s * 3.8, 13.4, -9.8), (2.2, 5.4, 4.2), 'fur', lb)
        m.tube([(s * 3.9, 10.0, -10.6), (s * 4.0, 5.2, bz - 4.0), (s * 4.0, 1.8, bz - 1.8)],
               [2.1, 1.4, 1.3], 'fur', lb)
        m.ell((s * 4.0, 1.2, bz - 0.8), (1.9, 1.2, 2.3), 'fur', lb)
    # long tail sweeping low then up, fraying into shadow smoke
    tail = [(0, 16.0, -14.0), (0.4, 14.0, -18.6), (1.0, 14.6, -22.8), (1.8, 18.6, -25.0), (2.2, 22.0, -24.4)]
    m.tube(tail, [2.0, 1.8, 1.6, 1.4, 1.2], 'fur', 'tail')
    for c, r in (((2.2, 22.6, -24.0), 1.9), ((2.8, 24.6, -23.0), 1.6), ((1.6, 26.0, -24.6), 1.2),
                 ((3.2, 26.8, -21.2), 1.1), ((2.0, 28.4, -22.0), 0.8), ((3.4, 29.2, -19.6), 0.7),
                 ((3.0, 31.4, -17.4), 1.2), ((3.6, 32.4, -16.0), 0.9), ((2.4, 34.4, -14.8), 0.9)):
        m.sph(c, r, 'mist', 'smoke')
    m.group('smoke', 'tail')
    # thick neck slung forward and down; the head low, turned to the viewer
    T, pv = 38, (0, 13.6, 13.6)

    def H(p):
        return yrot(p, pv, T)
    rot = (T, 0, 0)
    m.tube([(0, 18.6, 7.0), (0, 17.0, 11.2), (0, 15.6, 13.8)], [4.4, 3.6, 3.0], 'fur', 'body')
    # a panther skull: small, flat and long, a squared muzzle and strong jaw
    hc, hr = H((0, 16.0, 16.0)), (4.9, 3.9, 4.6)
    m.ell(hc, hr, 'fur', 'head', rot=rot)
    mc, mr = H((0, 14.4, 20.2)), (2.8, 2.0, 2.5)
    m.ell(mc, mr, 'fur', 'head', rot=rot)
    m.ell(H((0, 12.9, 19.0)), (2.3, 1.2, 2.3), 'fur', 'head', rot=rot)
    # pointed ears standing up and forward
    for s in (-1, 1):
        m.tube([H((s * 2.9, 18.6, 14.4)), H((s * 3.5, 20.8, 14.8)), H((s * 3.8, 22.8, 15.0))],
               [1.8, 1.0, 0.1], 'fur', 'ear%d' % s, flat=0.45, up=yrot((s * 0.2, 0.1, 1), (0, 0, 0), T))
    # dark eye sockets under a heavy brow that slopes down to the nose
    for s in (-1, 1):
        p, n = g.on(hc, hr, yrot(sdir(30 * s, 10), (0, 0, 0), T), rot)
        m.paint(p, (2.5, 1.9, 1.4), 'ros', ['head'], rot=rot)
        m.ell(H((s * 2.0, 18.4, 18.8)), (2.0, 0.6, 1.0), 'fur', 'head', rot=(T, 0, -s * 22))
    g.eye_pair(m, hc, hr, 30, 10, 4.8, 3.6, style='glow', iris=('glow', 1), pupil='eye', slant=0.8,
               center=H((0, 16, 23)), rot=rot, turn=T, minw=3, minh=3)
    m.dot(g.on(mc, mr, yrot((0, 0.55, 1), (0, 0, 0), T), rot)[0], yrot((0, 0.3, 1), (0, 0, 0), T),
          w=1.4, h=1.0, color=('ros', 0))
    p, n = g.on(mc, mr, yrot((0, -0.5, 1), (0, 0, 0), T), rot)
    m.mouth(p, n, 'line', w=2.4, fang=1, color=('ros', 0))
    return m


# ---- end of batch ----
