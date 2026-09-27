"""Art for the fusion kin 152-173 (data in tools/kin/fusion_b.py).

Every function takes the tools/gen_monsters.py module `g` (Model API and
shape helpers) and returns a Model. Coordinates: +Y up, +Z toward the
creature's front, +X the creature's own left (the side nearer the camera in
the 3/4 front view); roughly 1 unit = 1 px on the 64x64 front sprite.

Each fusion reads as a hybrid of its two energies and carries one glowing
"signature" material (emissive) where the two energies meet.
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


def frustum_surf(base, rb, rt, h, sides, x, y, phase=0.0):
    """Front surface point + normal of a frustum at (x, y)."""
    best = None
    for n, d in frustum_planes(base, rb, rt, h, sides, phase)[2:]:
        if n[2] <= 1e-6:
            continue
        z = (d - n[0] * x - n[1] * y) / n[2]
        if best is None or z < best[0]:
            best = (z, n)
    return (x, y, best[0]), best[1]


# ==========================================================================
# 152 BARKOLEM  BLOOM/STONE  stump golem with a birdhouse
# ==========================================================================
def barkolem(g):
    m = g.Model('BARKOLEM')
    m.outline = (34, 22, 18)
    m.mat('bark', ['#3e2a1e', '#644430', '#8c6444', '#b48c64'])
    m.mat('wood', ['#8c6444', '#b48c64', '#e6c48a'])
    m.mat('stone', ['#4a4a58', '#777786', '#a6a6b4'])
    m.mat('moss', ['#355e22', '#5e9a34', '#9ed052'])
    m.mat('sap', ['#e8961c', '#ffe27a'], emissive=0.85)
    m.eye_dark = (34, 22, 18)
    m.height = 54
    m.max_w = 60
    m.front_yaw = -26
    TB, RB, RT, TH, SIDES, PH = (0, 6.5, 0), 10.5, 9.2, 27.0, 11, 90.0
    top = TB[1] + TH

    def S(x, y):
        return frustum_surf(TB, RB, RT, TH, SIDES, x, y, PH)
    frustum(m, TB, RB, RT, TH, SIDES, 'bark', 'body', phase=PH)
    # mossy crown with a cut face of pale wood and one growth ring
    m.paint((0, top, 0), (12.5, 2.6, 12.5), 'moss', ['body'])
    m.paint((0, top + 0.2, 0), (7.8, 0.6, 7.8), 'wood', ['body'])
    m.paint((0, top + 0.3, 0), (5.4, 0.5, 5.4), 'bark', ['body'])
    m.paint((0, top + 0.4, 0), (4.4, 0.5, 4.4), 'wood', ['body'])
    for (x, y, rx, ry) in ((-6.5, top - 3.4, 2.0, 2.8), (3.5, top - 3.0, 1.8, 2.2),
                           (7.5, top - 3.8, 1.6, 3.0)):
        p, n = S(x, y)
        m.paint(p, (rx, ry, 2.0), 'moss', ['body'])
    # splintered rim
    rnd = g.Rand(52)
    for a in (35, 125, 160, 205, 250, 290, 335):
        d = (math.cos(a * DEG), 0, math.sin(a * DEG))
        b = add((0, top - 1.2, 0), mul(d, 8.2))
        tip = add(b, add(mul(d, 1.0), (0, 2.6 + 2.0 * rnd.f(), 0)))
        m.crystal(b, tip, 1.2, 'wood', 'rim', sides=4, tip_frac=0.8)
    # root legs
    for s in (-1, 1):
        m.tube([(s * 5.2, 9.0, 1.5), (s * 6.4, 4.5, 3.0), (s * 6.8, 1.8, 4.2)],
               [4.2, 3.6, 3.2], 'bark', 'leg%d' % s)
        m.ell((s * 6.9, 1.6, 5.2), (3.7, 1.7, 4.2), 'bark', 'leg%d' % s)
        for t in (-1, 0, 1):
            m.tube([(s * 6.9 + t * 1.6, 1.5, 7.4), (s * 6.9 + t * 2.6, 0.8, 10.2)],
                   [1.2, 0.45], 'bark', 'leg%d' % s)
    # root flares spreading behind
    for a in (200, 245, 295, 340):
        d = (math.cos(a * DEG), 0, math.sin(a * DEG))
        m.tube([add((0, 9, 0), mul(d, 8.5)), add((0, 3.5, 0), mul(d, 12.5)),
                add((0, 0.9, 0), mul(d, 15.0))], [3.2, 2.1, 0.6], 'bark', 'roots')
    # branch arms gripping boulder fists; leafy twigs at the elbows
    for s in (-1, 1):
        sh = (s * 8.6, 27.5, 0.5)
        el = (s * 14.2, 23.2, 2.4)
        wr = (s * 16.4, 16.0, 4.4)
        m.tube([sh, el, wr], [3.6, 3.0, 2.6], 'bark', 'arm%d' % s)
        fc = (s * 16.8, 12.2, 5.4)
        m.rock(fc, (4.0, 3.8, 3.8), 'stone', 'fist%d' % s, seed=11 + s, n=14)
        for t in (-1, 0, 1):
            m.tube([add(wr, (t * 1.3, -0.4, 0.6)), add(fc, (t * 1.8, 0.8, 3.6))],
                   [1.0, 0.6], 'bark', 'arm%d' % s)
        tw0 = add(el, (s * 0.8, 1.6, -0.8))
        tw1 = add(el, (s * 3.4, 7.2, -1.8))
        m.tube([el, tw0, tw1], [1.2, 0.9, 0.4], 'bark', 'twig%d' % s)
        g.leaf(m, tw1, add(tw1, (s * 1.6, 2.2, 0.4)), add(tw1, (s * 2.6, 4.8, 0.6)), 1.9,
               'moss', 'twig%d' % s, up=(0, 0.2, 1))
        g.leaf(m, lerp(tw0, tw1, 0.5), add(lerp(tw0, tw1, 0.5), (s * 2.4, 0.6, 0.6)),
               add(lerp(tw0, tw1, 0.5), (s * 4.6, 0.2, 1.0)), 1.6, 'moss', 'twig%d' % s,
               up=(0, 1, 0.3))
    # granite heart with sap-lit cracks
    hp, hn = S(0, 12.6)
    hc = add(hp, (0, 0, -0.6))
    m.rock(hc, (3.6, 3.9, 2.6), 'stone', 'heart', seed=5, n=13)
    m.paint(add(hc, (0.3, 0.2, 2.3)), (1.3, 1.5, 1.2), 'sap', ['heart'])
    for path in (((1.0, 15.6), (2.6, 17.4), (4.4, 17.0)), ((-1.4, 15.4), (-2.6, 17.8))):
        paint_path(m, [S(x, y)[0] for x, y in path], (0.7, 0.7, 3.0), 'sap', ['body'])
    # face: brow ridge, knot-hole eyes and a hollow mouth
    brow = [add(S(x, y)[0], (0, 0, 0.5)) for x, y in ((-6.2, 26.8), (-2.2, 28.0), (0, 27.4),
                                                         (2.2, 28.0), (6.2, 26.8))]
    m.tube(brow, [1.0, 1.5, 1.2, 1.5, 1.0], 'bark', 'brow')
    for s in (-1, 1):
        p, n = S(s * 3.4, 24.2)
        m.dot(p, n, w=3.8, h=4.4, color=('bark', 0), shape='oval', minw=3, minh=3)
        m.eye(p, n, 2.4, 3.0, style='glow', iris=('sap', 1), center=(0, 24, 14))
    p, n = S(0, 19.8)
    m.mouth(p, n, 'open', w=4.0, h=2.4, color='outline', inner=('bark', 0))
    # the birdhouse on its crown
    m.tube([(0.5, top - 0.5, -1.5), (0.5, top + 2.2, -1.5)], [1.5, 1.2], 'bark', 'house')
    hw, hh, hd = 4.0, 3.9, 3.6
    bh = (0.5, top + 2.0 + hh, -1.5)
    m.box(bh, (hw, hh, hd), 'wood', 'house', bevel=0.4)
    ridge_y = bh[1] + hh + 4.6
    eave_y = bh[1] + hh - 0.8
    ang = math.atan2(ridge_y - eave_y, hw + 1.4) / DEG
    for s in (-1, 1):
        c = (0.5 + s * (hw + 1.4) / 2.0, (ridge_y + eave_y) / 2.0, -1.5)
        m.box(c, (4.3, 0.6, hd + 0.9), 'stone', 'roof', rot=(0, 0, -s * ang), bevel=0.2)
    m.paint((0.5, ridge_y, -1.5), (2.4, 1.5, hd + 1.4), 'moss', ['roof'])
    for z in (-1.5 + hd + 0.02, -1.5 - hd - 0.02):
        m.poly([(0.5 - hw, bh[1] + hh, z), (0.5 + hw, bh[1] + hh, z), (0.5, ridge_y - 0.6, z)],
               'wood', 'house', puff=0.0)
    m.dot((0.5, bh[1] + 0.8, -1.5 + hd + 0.05), (0, 0, 1), w=2.6, h=2.8, color='eye',
          shape='oval', minw=2, minh=2)
    m.tube([(0.5, bh[1] - 2.0, -1.5 + hd - 0.2), (0.5, bh[1] - 2.0, -1.5 + hd + 1.8)], 0.5,
           'wood', 'house')
    m.group('house', 'roof')
    return m


# ==========================================================================
# 153 PORCELYNX  RELIC/FROST  porcelain lynx with frost glaze
# ==========================================================================
def porcelynx(g):
    m = g.Model('PORCELYNX')
    m.outline = (22, 26, 58)
    m.mat('porc', ['#7e8fb0', '#bcc8de', '#e8eef6', '#ffffff'], spec=0.5,
          th=[0.22, 0.52, 0.86])
    m.mat('glaze', ['#1a347e', '#2f5cb8', '#5c8ee0'])
    m.mat('frost', ['#3c9ad0', '#94e2f8'], emissive=0.2)
    m.mat('gold', ['#c08a1a', '#ffd84e'], emissive=0.4)
    m.eye_dark = (26, 52, 126)
    m.white = (255, 255, 255)
    m.height = 52
    m.front_yaw = -28
    # seated: haunches, hind feet, upright chest, straight forelegs
    for s in (-1, 1):
        m.ell((s * 5.0, 7.6, -3.4), (4.4, 6.0, 6.2), 'porc', 'hip%d' % s)
        m.ell((s * 5.8, 1.4, 1.8), (2.2, 1.4, 3.6), 'porc', 'foot%d' % s)
    m.ell((0, 13.5, -0.8), (5.6, 8.6, 5.8), 'porc', 'body', rot=(0, -14, 0))
    for s in (-1, 1):
        m.tube([(s * 2.7, 12.0, 2.8), (s * 2.9, 6.0, 3.8), (s * 3.0, 2.0, 4.4)],
               [2.3, 1.9, 1.8], 'porc', 'legF%d' % s)
        m.ell((s * 3.0, 1.5, 5.4), (2.2, 1.5, 2.5), 'porc', 'legF%d' % s)
    # short bob tail with a blue tip
    m.tube([(0, 4.2, -9.0), (2.6, 2.4, -10.6), (5.6, 1.7, -9.4)], [2.4, 2.2, 1.7], 'porc', 'tail')
    m.paint((5.6, 1.8, -9.4), 2.1, 'glaze', ['tail'])
    # head, muzzle, a flared ruff that ends in icicles
    m.tube([(0, 19.0, 0.4), (0, 22.0, 1.4)], [3.6, 3.4], 'porc', 'body')
    head_c, head_r = (0, 24.8, 2.4), (6.6, 5.6, 5.6)
    m.ell(head_c, head_r, 'porc', 'head')
    mz_c, mz_r = (0, 22.4, 7.0), (3.0, 2.1, 2.0)
    m.ell(mz_c, mz_r, 'porc', 'head')
    m.paint((0, 19.6, 3.6), (3.6, 1.4, 3.0), 'glaze', ['body'])
    for s in (-1, 1):
        for k in range(3):
            b = (s * 4.8, 24.0 - k * 1.5, 3.4 - k * 0.5)
            tip = (s * (9.8 + k * 0.4), 21.2 - k * 2.8, 2.0 - k * 0.7)
            m.tube([b, lerp(b, tip, 0.5), tip], [2.4, 1.5, 0.25], 'porc', 'ruff', flat=0.45,
                   up=(0, 0, 1), mats=[(0, 'porc'), (0.62, 'frost')])
        # short triangular ears with long dark tufts
        m.tube([(s * 3.4, 28.8, 1.6), (s * 4.3, 31.6, 1.2), (s * 4.9, 34.0, 0.8)],
               [2.9, 1.8, 0.3], 'porc', 'ear%d' % s, flat=0.45, up=(0, 0.1, 1))
        m.paint((s * 3.9, 30.6, 2.4), (1.2, 1.8, 1.0), 'glaze', ['ear%d' % s])
        m.tube([(s * 4.9, 33.6, 0.8), (s * 5.2, 36.4, 0.6), (s * 5.0, 38.6, 0.4)],
               [0.55, 0.45, 0.2], 'glaze', 'ear%d' % s)
    # blue glaze: lynx spots, forehead stripes, a flower on the chest, paw bands
    for s in (-1, 1):
        for (x, y, z, r) in ((6.8, 9.5, -0.5, 0.9), (8.0, 6.5, -3.0, 0.8), (6.4, 12.0, -4.6, 0.8),
                             (7.4, 4.2, -5.6, 0.7), (4.8, 3.6, 0.8, 0.7), (7.6, 9.0, -7.0, 0.8),
                             (5.6, 13.0, -1.2, 0.7), (8.6, 3.2, -2.0, 0.7)):
            m.paint((s * x, y, z), r * 1.3, 'glaze', ['hip%d' % s])
        m.paint((s * 1.4, 29.2, 5.0), (0.6, 1.6, 1.0), 'glaze', ['head'])
        m.paint((s * 4.6, 17.0, 3.0), 1.0, 'glaze', ['body'])
        m.paint((s * 3.0, 3.4, 4.2), (2.8, 0.6, 2.8), 'glaze', ['legF%d' % s])
    m.paint((0, 29.6, 4.8), (0.6, 1.8, 1.0), 'glaze', ['head'])
    for (x, y, z) in ((0, 21.0, -3.6), (0, 17.6, -5.6), (0, 13.8, -6.4), (-2.6, 15.8, -5.6),
                      (2.6, 12.0, -6.2), (-2.4, 9.8, -6.2), (2.2, 19.2, -4.4)):
        m.paint((x, y, z), 1.0, 'glaze', ['body'])
    for s in (-1, 1):
        m.paint((s * 3.4, 27.8, -2.4), (1.0, 1.4, 1.0), 'glaze', ['head'])
    fc = (0, 14.4, 5.2)
    for k in range(5):
        a = k * 72 * DEG
        m.paint(add(fc, (math.sin(a) * 1.6, math.cos(a) * 1.6, 0)), (1.0, 1.0, 1.4), 'glaze',
                ['body'])
    m.paint(fc, (0.8, 0.8, 1.6), 'gold', ['body'])
    # kintsugi: gold mended cracks
    paint_path(m, [(-4.6, 17.0, 3.4), (-3.0, 15.4, 5.0), (-3.4, 12.8, 5.4), (-1.6, 10.2, 5.4)],
               (0.55, 0.55, 2.4), 'gold', ['body'])
    paint_path(m, [(6.4, 13.0, -1.0), (8.4, 10.2, -2.4), (8.2, 7.0, -4.4), (9.0, 5.0, -5.0)],
               (0.55, 0.55, 2.4), 'gold', ['hip1'])
    paint_path(m, [(-5.2, 27.4, 3.6), (-3.4, 26.2, 5.0), (-3.8, 28.4, 4.8)], (0.5, 0.5, 2.2),
               'gold', ['head'])
    # frost ferns on the ground around its paws
    for (bx, bz, a0) in ((-6.5, 5.5, 0), (7.5, 4.0, 40), (1.5, 8.5, 80)):
        for k in range(3):
            a = (a0 + k * 120) * DEG
            b = (bx, 0.2, bz)
            tip = add(b, (math.cos(a) * 1.4, 2.4 + k * 0.8, math.sin(a) * 1.4))
            m.crystal(b, tip, 0.7, 'frost', 'rime', sides=4, tip_frac=0.6)
    eye_c = (0, 23, 12)
    g.eye_pair(m, head_c, head_r, 30, 12, 4.0, 4.0, style='sharp', iris=('gold', 1), slant=0.7,
               lid=1, center=eye_c, turn=9)
    m.dot(g.on(mz_c, mz_r, (0, 0.5, 1))[0], (0, 0.2, 1), w=1.8, h=1.2, minw=2,
          color=('glaze', 0))
    p, n = g.on(mz_c, mz_r, (0, -0.35, 1))
    m.mouth(p, n, 'w', w=3.0)
    return m


# ==========================================================================
# 154 KABUTORAI  METAL/BRAWL  samurai beetle
# ==========================================================================
def kabutorai(g):
    m = g.Model('KABUTORAI')
    m.outline = (16, 14, 26)
    m.mat('shell', ['#1a1c2c', '#2e3452', '#4a567c', '#7e8cb6'], spec=0.5)
    m.mat('red', ['#6a1420', '#a82a30', '#e05a48'])
    m.mat('gold', ['#9c6a14', '#e0aa2a', '#fff0a0'], emissive=0.2)
    m.mat('steel', ['#8c98b4', '#e4ecf6'], spec=0.6)
    m.white = (228, 236, 246)
    m.eye_dark = (26, 28, 44)
    m.height = 58
    m.max_w = 60
    m.front_yaw = -24
    # wide stance: armoured thighs, segmented shins with spurs, two-claw feet
    for s in (-1, 1):
        m.ell((s * 4.6, 14.4, 0.3), (3.2, 4.2, 3.4), 'shell', 'leg%d' % s)
        m.tube([(s * 5.2, 11.5, 1.0), (s * 6.6, 6.5, 2.4), (s * 6.6, 2.0, 1.4)],
               [2.4, 1.8, 1.6], 'shell', 'leg%d' % s)
        m.paint((s * 6.4, 7.0, 3.8), (1.9, 3.0, 1.4), 'red', ['leg%d' % s])
        m.crystal((s * 6.6, 7.6, 0.4), (s * 7.4, 9.4, -3.0), 0.7, 'steel', 'leg%d' % s,
                  sides=4, tip_frac=0.8)
        for t in (-1, 1):
            m.crystal((s * 6.6 + t * 0.9, 1.6, 1.8), (s * 7.0 + t * 1.8, 0.4, 5.8), 0.85,
                      'shell', 'leg%d' % s, sides=4, tip_frac=0.8)
    # waist + lamellar skirt plates
    m.ell((0, 18.5, -0.3), (5.8, 3.6, 4.6), 'shell', 'body')
    for a in (-105, -63, -21, 21, 63, 105):
        c = (math.sin(a * DEG) * 6.2, 15.0, math.cos(a * DEG) * 5.4)
        m.box(c, (2.4, 3.6, 0.5), 'red', 'skirt', rot=(a, 16, 0), bevel=0.25)
    m.paint((0, 17.8, 0), (9.0, 0.6, 8.6), 'gold', ['skirt'])
    m.paint((0, 14.0, 0), (9.6, 0.55, 9.2), 'shell', ['skirt'])
    # round beetle thorax as the breastplate, one cord band and a gold crest
    m.ell((0, 26.5, 0.4), (8.2, 7.4, 6.2), 'shell', 'body')
    m.paint((0, 21.6, 3.0), (8.6, 0.7, 5.0), 'red', ['body'])
    m.paint((0, 28.2, 6.4), (1.6, 1.6, 1.2), 'gold', ['body'])
    # elytra hang behind like a split war-cloak, each with a gold crest
    for s in (-1, 1):
        m.ell((s * 4.0, 23.5, -6.2), (4.6, 11.0, 2.8), 'shell', 'elytra%d' % s,
              rot=(s * 12, 8, -s * 5))
        m.paint((s * 4.8, 26.5, -9.2), (1.8, 1.8, 1.4), 'gold', ['elytra%d' % s])
    # shoulder plates (sode)
    for s in (-1, 1):
        m.box((s * 10.4, 28.6, 0.3), (1.2, 4.6, 3.8), 'red', 'sode%d' % s, rot=(0, 0, s * 16),
              bevel=0.4)
        for yy in (26.6, 29.8):
            m.paint((s * 11.0, yy, 0.3), (2.4, 0.5, 4.4), 'shell', ['sode%d' % s])
    # arms raised in a guard, spiny forearms
    for s in (-1, 1):
        sh = (s * 8.8, 30.5, 0.6)
        el = (s * 11.8, 24.0, 3.6)
        fi = (s * 6.0, 24.2, 9.4)
        m.tube([sh, el], [2.4, 2.1], 'shell', 'arm%d' % s)
        m.tube([el, fi], [2.1, 1.9], 'shell', 'arm%d' % s, mats=[(0, 'shell'), (0.4, 'red')])
        m.sph(fi, 2.5, 'shell', 'arm%d' % s)
        for t in (0.25, 0.6):
            q = lerp(el, fi, t)
            m.crystal(add(q, (s * 1.2, 0.8, -0.6)), add(q, (s * 3.2, 2.2, -2.2)), 0.6, 'steel',
                      'arm%d' % s, sides=4, tip_frac=0.8)
    # helmet, visor, red face mask with gold mandibles
    m.tube([(0, 32.5, 0.8), (0, 34.5, 1.4)], [3.2, 3.0], 'shell', 'body')
    head_c, head_r = (0, 39.2, 0.8), (5.8, 4.8, 5.4)
    m.ell(head_c, head_r, 'shell', 'head')
    m.ell((0, 41.4, 4.2), (5.4, 0.7, 1.8), 'shell', 'visor')
    m.ell((0, 34.8, 4.4), (3.0, 1.9, 2.3), 'red', 'head')
    for s in (-1, 1):
        m.tube([(s * 2.2, 34.0, 6.0), (s * 1.8, 32.6, 7.4), (-s * 0.2, 32.2, 8.0)],
               [0.7, 0.55, 0.25], 'gold', 'head')
    # neck guard (shikoro): tiers of plates flaring round the back
    for k in range(3):
        R = 6.0 + k * 1.4
        y = 37.4 - k * 1.9
        pts = []
        for a in range(-105, 106, 15):
            pts.append((math.sin(a * DEG) * R, y, 0.8 - math.cos(a * DEG) * R * 0.95))
        m.tube(pts, 1.5, 'shell' if k != 1 else 'red', 'shikoro', flat=0.4, up=(0, 1, 0.25))
    # crest: gold kuwagata prongs and the beetle's own horn
    for s in (-1, 1):
        m.tube([(s * 1.6, 41.6, 4.8), (s * 4.0, 45.0, 5.2), (s * 6.6, 49.6, 4.8),
                (s * 7.2, 54.0, 4.0)], [1.1, 1.0, 0.8, 0.25], 'gold', 'crest', flat=0.45,
               up=(0, 0, 1))
    m.sph((0, 41.8, 5.8), 1.4, 'gold', 'crest')
    m.tube([(0, 41.4, 4.2), (0, 44.5, 7.8), (0, 48.4, 9.4), (0, 51.6, 8.4)],
           [2.2, 1.7, 1.2, 0.35], 'steel', 'horn')
    p, n = g.on(head_c, head_r, (0.0, -0.12, 1.0))
    m.dot(p, n, w=8.0, h=2.8, color=('shell', 0), minw=7, minh=3)
    for s in (-1, 1):
        p, n = g.on(head_c, head_r, (s * 0.38, -0.12, 0.92))
        m.eye(p, n, 3.2, 2.4, style='glow', iris=('gold', 2), slant=0.6, center=(0, 37, 12),
              minh=2, minw=3)
    return m


# ==========================================================================
# 155 DROWNJELLY  TIDE/HOLLOW  drowned jellyfish lantern
# ==========================================================================
def drownjelly(g):
    m = g.Model('DROWNJELLY')
    m.outline = (14, 30, 42)
    m.mat('bell', ['#1e4a64', '#2e7a8e', '#56b2b8', '#a2e6dc'], spec=0.5)
    m.mat('bone', ['#6e6a5a', '#aaa48e', '#dcd6c0'])
    m.mat('lamp', ['#46d69a', '#c8ffe0'], emissive=0.85)
    m.mat('iron', ['#3a2a2c', '#6c4c3c'])
    m.eye_dark = (14, 30, 42)
    m.white = (220, 214, 192)
    m.height = 52
    hover(g, m, 4)
    bell_c, bell_r = (0, 31.0, 0), (13.0, 10.5, 12.0)
    m.ell(bell_c, bell_r, 'bell', 'bell')
    for k in range(14):
        a = 2 * math.pi * k / 14
        m.sph((math.sin(a) * 12.0, 21.8, math.cos(a) * 11.0), 2.3, 'bell', 'bell')
    # a ribcage lying over the bell
    spine = []
    for t in (62, 34, 6, -22, -50, -74):
        d = (0, math.cos(t * DEG), math.sin(t * DEG))
        p, n = g.on(bell_c, bell_r, d)
        spine.append(add(p, mul(n, 0.5)))
    m.tube(spine, [0.7, 0.9, 1.0, 0.9, 0.8, 0.6], 'bone', 'ribs')
    for t in (26, -8, -42):
        u = (0, math.cos(t * DEG), math.sin(t * DEG))
        for s in (-1, 1):
            pts = []
            for ph in (0, 22, 44, 66, 86, 100):
                d = add(mul(u, math.cos(ph * DEG)), (s * math.sin(ph * DEG), 0, 0))
                p, n = g.on(bell_c, bell_r, d)
                pts.append(add(p, mul(n, 0.35)))
            m.tube(pts, [0.8, 0.75, 0.7, 0.6, 0.45, 0.3], 'bone', 'ribs')
    m.group('ribs', 'bell')
    # hollow sockets with glowing pinprick eyes, and a gaping mouth
    for s in (-1, 1):
        p, n = g.on(bell_c, bell_r, (s * 0.34, -0.12, 1))
        m.dot(p, n, w=4.2, h=4.8, color=('bell', 0), shape='oval', minw=3, minh=4)
        m.eye(p, n, 1.8, 2.4, style='solid', iris=('lamp', 1), minw=2, minh=2)
    p, n = g.on(bell_c, bell_r, (0.04, -0.46, 1))
    m.mouth(p, n, 'open', w=3.6, h=2.4, color=('bell', 0), inner=('bell', 0))
    # the drowned ship's lantern, hung on a string of vertebrae
    for k in range(3):
        m.sph((0, 20.2 - k * 1.8, 0.4), 0.95, 'bone', 'lamp')
    lc = (0, 11.0, 0.4)
    m.ell(add(lc, (0, 4.4, 0)), (3.0, 1.2, 3.0), 'iron', 'lamp')
    m.ell(add(lc, (0, 5.6, 0)), (1.4, 0.8, 1.4), 'iron', 'lamp')
    m.ell(lc, (2.9, 3.8, 2.9), 'lamp', 'lamp')
    for k in range(4):
        a = (45 + 90 * k) * DEG
        dx, dz = math.sin(a), math.cos(a)
        m.tube([add(lc, (dx * 2.9, 3.8, dz * 2.9)), add(lc, (dx * 3.2, 0, dz * 3.2)),
                add(lc, (dx * 2.9, -3.8, dz * 2.9))], 0.5, 'iron', 'lamp')
    m.ell(add(lc, (0, -4.2, 0)), (2.6, 1.0, 2.6), 'iron', 'lamp')
    m.sph(add(lc, (0, -5.4, 0)), 0.9, 'iron', 'lamp')
    # ribbon tentacles and two trailing spines
    rnd = g.Rand(155)
    for a in (-150, -118, -62, 62, 118, 150, 180):
        d = (math.sin(a * DEG), 0, math.cos(a * DEG))
        b = add((0, 21.5, 0), mul(d, 9.6))
        ph = rnd.f() * 6.28
        pts = []
        for k in range(6):
            w = math.sin(ph + k * 1.3) * 1.6
            pts.append(add(b, add(mul(d, 0.6 * k), (w * d[2], -3.8 * k, -w * d[0]))))
        m.tube(pts, [1.8, 1.5, 1.2, 0.9, 0.6, 0.25], 'bell', 'tent', flat=0.4, up=d)
    for s in (-1, 1):
        b = (s * 6.5, 20.5, 3.5)
        for k in range(7):
            q = add(b, (s * (0.4 * k + 0.6 * math.sin(k * 1.1)), -2.3 * k, 0.4 * k))
            m.sph(q, 1.25 - k * 0.12, 'bone', 'spine%d' % s)
    return m


# ==========================================================================
# 156 SUNMANE  BLOOM/BLAZE  lion with a sunflower mane
# ==========================================================================
def sunmane(g):
    m = g.Model('SUNMANE')
    m.outline = (58, 26, 12)
    m.mat('fur', ['#8a4a1c', '#c07a2c', '#e8a848', '#fad27a'])
    m.mat('petal', ['#d88a10', '#ffc81e', '#fff27a'])
    m.mat('flame', ['#e8401a', '#ff8a2a'], emissive=0.6)
    m.mat('seed', ['#4a2a14', '#8a4a1c'])
    m.mat('leaf', ['#3c7a24', '#74b43c'])
    m.eye_dark = (58, 26, 12)
    m.height = 50
    m.max_w = 62
    m.front_yaw = -34
    # body and legs
    m.ell((0, 14.0, -2.0), (6.8, 6.6, 11.0), 'fur', 'body')
    m.ell((0, 15.0, 6.0), (6.6, 7.0, 6.0), 'fur', 'body')
    m.paint((0, 10.0, 4.0), (5.0, 3.4, 9.0), 'fur', ['body'])
    for s in (-1, 1):
        m.tube([(s * 3.8, 12.0, 7.5), (s * 4.0, 6.0, 8.2), (s * 4.0, 2.2, 8.6)],
               [2.8, 2.3, 2.3], 'fur', 'legF%d' % s)
        m.ell((s * 4.0, 1.6, 9.8), (2.6, 1.6, 3.0), 'fur', 'legF%d' % s)
        m.ell((s * 4.4, 13.0, -9.0), (3.4, 5.0, 4.6), 'fur', 'legB%d' % s)
        m.tube([(s * 4.6, 10.0, -10.5), (s * 4.8, 5.0, -11.2), (s * 4.6, 2.2, -9.8)],
               [2.8, 2.2, 2.2], 'fur', 'legB%d' % s)
        m.ell((s * 4.6, 1.6, -8.6), (2.5, 1.6, 2.8), 'fur', 'legB%d' % s)
    # tail ending in a flame bud
    m.tube([(0, 16.0, -12.5), (1.5, 19.0, -17.0), (3.2, 21.5, -20.5), (4.6, 22.2, -23.0)],
           [1.6, 1.3, 1.1, 1.0], 'fur', 'tail')
    g.flame(m, (4.8, 22.0, -23.4), 7.0, 2.6, 'tail', mats=('flame', 'petal', 'petal'),
            up=(0.3, 1, -0.3), tongues=2, seed=5)
    # sunflower mane: a ring of seeds around the face, petals with burning tips
    head_c, head_r = (0, 23.5, 10.5), (5.4, 5.0, 5.2)
    n = norm((0, 0.2, 1))
    u = (1, 0, 0)
    v = norm(cross(n, u))
    mc = (0, 23.8, 8.2)
    ring = []
    for k in range(17):
        a = 2 * math.pi * k / 16
        ring.append(add(mc, add(mul(u, math.cos(a) * 6.4), mul(v, math.sin(a) * 6.4))))
    m.tube(ring, 2.4, 'seed', 'mane', flat=0.7, up=n)
    for layer, (cnt, r0, ln, wd, dz, a0) in enumerate(((12, 6.8, 9.6, 2.9, -0.4, 0.0),
                                                        (12, 6.4, 10.6, 2.2, -2.2, 15.0))):
        for k in range(cnt):
            a = 2 * math.pi * k / cnt + a0 * DEG
            d = add(mul(u, math.cos(a)), mul(v, math.sin(a)))
            b = add(add(mc, mul(n, dz)), mul(d, r0))
            tip = add(b, add(mul(d, ln), mul(n, -1.6 - layer)))
            if layer == 0:
                g.leaf(m, b, lerp(b, tip, 0.5), tip, wd, 'petal', 'petals', up=n, flat=0.3)
            else:
                g.leaf(m, b, lerp(b, tip, 0.5), tip, wd, 'flame', 'flames', up=n, flat=0.3,
                       mats=[(0, 'petal'), (0.45, 'flame')])
    # sunflower leaves on the shoulders
    for s in (-1, 1):
        b = (s * 5.6, 17.0, 3.0)
        g.leaf(m, b, add(b, (s * 3.6, -1.0, -3.0)), add(b, (s * 6.0, -3.2, -7.0)), 3.0, 'leaf',
               'leaf%d' % s, up=(s * 0.5, 1, 0.2))
    # head
    m.ell(head_c, head_r, 'fur', 'head')
    mz_c, mz_r = (0, 21.4, 14.6), (3.4, 2.6, 2.8)
    m.ell(mz_c, mz_r, 'fur', 'head')
    m.paint((0, 20.6, 16.0), (2.8, 2.0, 1.8), 'petal', ['head'])
    for s in (-1, 1):
        m.ell((s * 3.4, 28.0, 9.4), (1.6, 1.8, 1.1), 'fur', 'head')
    g.eye_pair(m, head_c, head_r, 30, 14, 3.4, 3.4, style='sharp', iris=('flame', 1), slant=0.7,
               lid=1, center=(0, 22, 18), turn=8)
    m.dot(g.on(mz_c, mz_r, (0, 0.55, 1))[0], (0, 0.3, 1), w=2.2, h=1.4, minw=2,
          color=('seed', 0))
    p, nn = g.on(mz_c, mz_r, (0, -0.4, 1))
    m.mouth(p, nn, 'smile', w=3.0, fang=1)
    return m


# ==========================================================================
# 157 DREAMKITE  DREAM/GALE  kite-shaped dream spirit
# ==========================================================================
def dreamkite(g):
    m = g.Model('DREAMKITE')
    m.outline = (30, 18, 60)
    m.mat('sail', ['#3a2a78', '#5a48b4', '#8a78e4', '#c2b6ff'])
    m.mat('panel', ['#b04a8c', '#f07ab8', '#ffc0e0'])
    m.mat('spar', ['#a8761c', '#f0c44a'])
    m.mat('ribbon', ['#3aa8c8', '#8ee8f4'], emissive=0.45)
    m.eye_dark = (30, 18, 60)
    m.height = 56
    m.max_w = 48
    m.front_yaw = -24
    hover(g, m, 4)
    side_yaw(g, m, -48)
    tilt = 18.0

    def K(x, y, z=0.0):
        """Point on the kite plane (tilted back) around its crossing."""
        c, s_ = math.cos(tilt * DEG), math.sin(tilt * DEG)
        yy = y - 34.0
        return (x, 34.0 + yy * c - z * s_, -yy * s_ + z * c)
    top, bot, lft, rgt, mid = K(0, 50), K(0, 14), K(-13, 36), K(13, 36), K(0, 36)
    for (a, b, mat) in ((top, lft, 'sail'), (top, rgt, 'panel'), (bot, lft, 'panel'),
                        (bot, rgt, 'sail')):
        m.poly([mid, a, b], mat, 'sail', puff=0.35)
    # gold frame + spars behind the sail
    for a, b in ((top, lft), (lft, bot), (bot, rgt), (rgt, top)):
        m.tube([a, b], 0.55, 'spar', 'frame')
    m.tube([K(0, 50, -0.7), K(0, 14, -0.7)], 0.6, 'spar', 'frame')
    m.tube([K(-13, 36, -0.7), K(13, 36, -0.7)], 0.6, 'spar', 'frame')
    m.group('frame', 'sail')
    # a crescent moon and stars painted on the panels
    mc = K(-4.6, 43.0, 0.2)
    m.paint(mc, (2.6, 2.6, 1.2), 'spar', ['sail'])
    m.paint(add(mc, (1.3, 0.8, 0.3)), (2.3, 2.3, 1.4), 'sail', ['sail'])
    fn = norm((0, math.sin(tilt * DEG), math.cos(tilt * DEG)))
    for (x, y, sz) in ((5.0, 42.0, 1), (7.4, 38.6, 1), (3.2, 46.0, 1), (-5.6, 22.0, 1),
                       (5.6, 26.0, 1)):
        m.sparkle(K(x, y, 0.2), fn, size=sz)
    # sleepy face in the middle
    for s in (-1, 1):
        m.eye(K(s * 3.6, 32.0, 0.3), fn, 3.6, 4.0, style='sleepy', center=K(0, 32, 5))
        m.paint(K(s * 5.8, 29.2, 0.1), (1.4, 0.9, 1.0), 'panel', ['sail'])
    m.mouth(K(0, 28.0, 0.3), fn, 'smile', w=2.6)
    # side streamers with little bows
    for s in (-1, 1):
        c = K(s * 13.4, 36.0, 0.2)
        for k in (-1, 1):
            m.tube([c, add(c, (s * 1.8, k * 1.4, 0.4)), add(c, (s * 3.0, k * 0.6, 0.2))],
                   [0.7, 0.9, 0.3], 'ribbon', 'bow%d' % s)
        m.tube([c, add(c, (s * 2.4, -3.4, 0.4)), add(c, (s * 1.8, -6.6, 0.8))], [0.6, 0.5, 0.2],
               'ribbon', 'bow%d' % s, flat=0.4, up=(0, 0, 1))
    # the dream tail: a glowing ribbon that sways down to the ground, tied with bows
    pts = [bot, add(bot, (2.2, -3.4, 0.6)), add(bot, (1.0, -7.0, 1.2)), add(bot, (-2.6, -9.6, 1.4)),
           add(bot, (-3.0, -13.0, 1.0)), add(bot, (0.4, -15.4, 0.4)), add(bot, (3.0, -17.4, 0.0))]
    m.tube(pts, [1.0, 0.9, 0.9, 0.8, 0.7, 0.6, 0.3], 'ribbon', 'tail', flat=0.4, up=(0, 0, 1))
    for q in (pts[1], pts[3], pts[5]):
        for k in (-1, 1):
            m.tube([q, add(q, (k * 1.8, 0.8, 0.3)), add(q, (k * 2.4, -0.4, 0.3))],
                   [0.6, 0.8, 0.3], 'panel', 'tail', flat=0.5, up=(0, 0, 1))
    return m


# ==========================================================================
# 158 BOGNEWT  VENOM/TIDE  toxic bog newt
# ==========================================================================
def bognewt(g):
    m = g.Model('BOGNEWT')
    m.outline = (16, 20, 14)
    m.mat('skin', ['#1e2a1c', '#34482a', '#4e6a36', '#74904a'])
    m.mat('belly', ['#c0501a', '#f08a2a', '#ffc060'])
    m.mat('toxin', ['#5ae05a', '#d0ff8a'], emissive=0.8)
    m.mat('crest', ['#4a2060', '#7c3c9a', '#b070d0'])
    m.eye_dark = (16, 20, 14)
    m.height = 34
    m.max_w = 62
    m.front_yaw = -26
    m.front_pitch = 16
    m.back_min_vis = 30
    # body and paddle tail
    m.tube([(0, 9.6, 8.0), (0, 9.2, 2.0), (0, 8.6, -4.0), (0.8, 8.0, -8.0)],
           [4.6, 5.4, 5.2, 4.4], 'skin', 'body')
    m.tube([(0.8, 8.0, -8.0), (2.4, 7.2, -13.0), (5.0, 6.0, -17.0), (8.0, 5.0, -20.5),
            (9.8, 4.4, -23.0)], [4.2, 3.6, 2.8, 1.8, 0.4], 'skin', 'tail', flat=0.55,
           up=(1, 0, 0.3))
    m.paint((0, 5.0, 1.0), (5.6, 3.2, 12.0), 'belly', ['body'])
    m.paint((1.4, 4.4, -12.0), (3.0, 2.0, 5.0), 'belly', ['tail'])
    # sprawling legs
    for s in (-1, 1):
        for (nm, z0, z1) in (('legF', 7.0, 9.0), ('legB', -5.0, -4.6)):
            part = '%s%d' % (nm, s)
            m.tube([(s * 4.0, 8.0, z0), (s * 8.4, 7.4, z0 + 0.6), (s * 9.6, 2.2, z1)],
                   [2.1, 1.8, 1.5], 'skin', part)
            for t in (-1, 0, 1):
                m.tube([(s * 9.6, 1.6, z1), (s * 10.2 + t * 1.1, 0.8, z1 + 2.2 + t * 0.2)],
                       [0.9, 0.5], 'skin', part)
            m.paint((s * 9.8, 1.0, z1 + 1.4), (2.4, 1.2, 2.4), 'belly', [part])
    # broad flat head with bulging golden eyes
    head_c, head_r = (0, 10.8, 13.8), (6.0, 4.2, 6.0)
    m.ell(head_c, head_r, 'skin', 'head')
    m.paint((0, 7.8, 15.6), (5.0, 2.0, 4.4), 'belly', ['head'])
    for s in (-1, 1):
        m.sph((s * 3.6, 13.6, 14.6), 2.3, 'skin', 'head')
        # parotoid toxin glands behind the eyes
        m.ell((s * 3.6, 13.0, 9.6), (1.8, 1.3, 2.4), 'toxin', 'gland%d' % s)
        m.eye((s * 4.3, 14.4, 16.0), (s * 0.5, 0.4, 1), 3.8, 3.8, style='iris',
              iris=('belly', 2), center=(0, 12, 22), minw=3, minh=3)
    p, n = g.on(head_c, head_r, (0, -0.25, 1))
    m.mouth(p, n, 'smile', w=5.6)
    # jagged dorsal crest from neck to tail tip
    crest = [(0, 13.6, 9.0), (0, 14.4, 5.0), (0, 14.4, 1.0), (0, 13.6, -3.0), (0.4, 12.6, -7.0),
             (1.6, 11.2, -11.0), (3.6, 9.6, -15.0), (6.2, 8.2, -18.4), (8.6, 6.8, -21.4)]
    for k, q in enumerate(crest):
        h = (3.4 if k % 2 == 0 else 2.2) * (1.0 - 0.05 * k)
        m.crystal(add(q, (0, -1.4, 0)), add(q, (0, h, -1.4)), 1.2, 'crest', 'crest',
                  sides=4, tip_frac=0.85)
    # glowing warts
    for (x, y, z) in ((3.8, 11.6, 4.0), (-3.6, 11.8, 2.4), (4.6, 10.0, -1.4), (-4.4, 10.4, -3.6),
                      (3.4, 10.8, -6.0), (-2.6, 10.2, -8.6), (4.2, 8.8, 0.8), (-4.8, 8.6, 5.0)):
        m.paint((x, y, z), 0.9, 'toxin', ['body'])
    for (x, y, z) in ((3.4, 8.4, -12.0), (5.4, 7.2, -15.6), (7.8, 6.0, -19.0)):
        m.paint((x, y, z), 0.8, 'toxin', ['tail'])
    return m


# ==========================================================================
# 159 RIMEGOLEM  FROST/STONE  ice golem
# ==========================================================================
def rimegolem(g):
    m = g.Model('RIMEGOLEM')
    m.outline = (20, 24, 36)
    m.mat('rock', ['#2e3440', '#4a5364', '#6c7888', '#97a4b2'])
    m.mat('ice', ['#3a8cc8', '#7ccdf0', '#c8f4ff'], spec=0.6)
    m.mat('glow', ['#6af0ff', '#e8ffff'], emissive=0.85)
    m.mat('snow', ['#c4d4e4', '#ffffff'])
    m.eye_dark = (46, 52, 64)
    m.white = (255, 255, 255)
    m.height = 56
    m.max_w = 62
    # short legs
    for s in (-1, 1):
        m.tube([(s * 5.0, 11.0, 0.0), (s * 6.0, 6.0, 1.0), (s * 6.2, 2.4, 1.6)], [4.0, 3.6, 3.4],
               'rock', 'leg%d' % s)
        m.rock((s * 6.4, 2.2, 2.8), (4.0, 2.4, 4.6), 'rock', 'leg%d' % s, seed=30 + s, n=12)
    # ice core bound by rock plates
    m.ell((0, 20.0, -0.5), (8.4, 10.0, 6.4), 'ice', 'core')
    m.rock((0, 12.6, -0.8), (7.0, 4.0, 5.2), 'rock', 'hips', seed=3, n=14)
    m.rock((0.4, 24.6, 0.6), (10.0, 6.6, 6.6), 'rock', 'chest', seed=8, n=16)
    m.rock((-0.6, 17.6, 1.0), (6.2, 3.2, 5.4), 'rock', 'belly', seed=12, n=12)
    for s in (-1, 1):
        m.rock((s * 10.2, 28.6, -1.0), (5.6, 5.2, 5.6), 'rock', 'sh%d' % s, seed=20 + s, n=15)
        m.paint((s * 10.6, 33.2, -1.0), (5.0, 2.2, 5.4), 'snow', ['sh%d' % s])
    # glowing seams where the ice shows through
    paint_path(m, [(-5.0, 20.6, 6.4), (-1.6, 21.0, 7.0), (1.4, 20.4, 7.0), (4.8, 21.2, 6.2)],
               (0.9, 0.9, 2.6), 'glow', ['core', 'chest', 'belly'])
    paint_path(m, [(0.6, 28.0, 7.0), (1.6, 25.0, 7.4), (0.2, 22.0, 7.4)], (0.7, 0.7, 2.6), 'glow',
               ['chest'])
    # long arms ending in huge ice fists that rest on the ground
    for s in (-1, 1):
        m.tube([(s * 11.0, 26.0, 0.0), (s * 14.6, 18.0, 2.0), (s * 15.2, 11.0, 3.6)],
               [3.8, 3.2, 3.0], 'rock', 'arm%d' % s)
        m.rock((s * 14.0, 20.0, 2.0), (3.6, 4.4, 3.6), 'rock', 'arm%d' % s, seed=40 + s, n=12)
        fc = (s * 15.4, 6.2, 4.6)
        m.ell(fc, (3.8, 3.8, 3.8), 'ice', 'fist%d' % s)
        for k, (dx, dy, dz) in enumerate(((0.6, 0.3, 1.0), (1.0, -0.1, 0.3), (0.2, 0.9, 0.5),
                                          (0.9, 0.8, -0.4), (-0.5, 0.4, 0.9), (0.3, -0.2, 1.0),
                                          (1.0, 0.3, 0.9))):
            d = norm((s * dx, dy, dz))
            m.crystal(add(fc, mul(d, 1.6)), add(fc, mul(d, 7.6 - 0.35 * k)), 1.4, 'ice',
                      'fist%d' % s, sides=4, tip_frac=0.6)
        for t in (0.35, 0.7):
            q = lerp((s * 14.6, 18.0, 2.0), (s * 15.2, 11.0, 3.6), t)
            m.crystal(add(q, (s * 1.2, -1.0, -1.6)), add(q, (s * 1.6, -4.4, -2.4)), 0.9, 'ice',
                      'arm%d' % s, sides=4, tip_frac=0.8)
    # ice spikes on the shoulders and back
    for s in (-1, 1):
        for (dx, dy, dz, ln) in ((0.3, 1.0, -0.3, 6.0), (0.8, 0.6, -0.5, 5.0), (-0.1, 0.8, -0.9, 5.4)):
            b = (s * 10.4, 31.4, -2.0)
            d = norm((s * dx, dy, dz))
            m.crystal(add(b, mul(d, 2.0)), add(b, mul(d, ln + 2.0)), 1.4, 'ice', 'spike%d' % s,
                      sides=5, tip_frac=0.6)
    for (x, y, z, h) in ((-2.6, 27.0, -5.6, 5.0), (2.8, 25.0, -6.0, 4.4), (0.0, 21.0, -6.4, 4.0)):
        m.crystal((x, y, z), (x * 1.2, y + h * 0.6, z - h), 1.3, 'ice', 'spike0', sides=5,
                  tip_frac=0.6)
    # head sunk between the shoulders, icicle beard, snow cap
    head_c, head_r = (0, 33.2, 3.4), (5.2, 4.4, 4.6)
    m.rock(head_c, head_r, 'rock', 'head', seed=17, n=13)
    m.paint((0, 37.2, 2.8), (5.0, 1.8, 4.6), 'snow', ['head'])
    for k, x in enumerate((-2.4, -0.8, 0.8, 2.4)):
        b = (x, 30.2, 6.6)
        m.crystal(b, add(b, (x * 0.1, -2.8 - (k % 2) * 1.6, 0.4)), 0.8, 'ice', 'beard', sides=4,
                  tip_frac=0.7)
    p, n = (0, 33.6, 7.7), (0, 0.1, 1)
    m.dot(p, n, w=7.0, h=2.6, color=('rock', 0), minw=6, minh=3)
    for s in (-1, 1):
        m.eye((s * 2.0, 33.6, 7.6), (s * 0.25, 0.1, 1), 2.6, 2.0, style='glow',
              iris=('glow', 1), slant=0.5, center=(0, 33, 12), minh=2, minw=2)
    return m


# ==========================================================================
# 160 DYNAMOLE  METAL/SPARK  mole with a dynamo
# ==========================================================================
def dynamole(g):
    m = g.Model('DYNAMOLE')
    m.outline = (22, 18, 30)
    m.mat('fur', ['#2a2436', '#443a56', '#665a7c', '#8e82a4'])
    m.mat('nose', ['#c85a78', '#f094aa'])
    m.mat('steel', ['#5a6474', '#9aa6b4', '#e0e8f0'], spec=0.5)
    m.mat('copper', ['#8a4418', '#d07a30', '#f4b060'], spec=0.4)
    m.mat('spark', ['#f4d020', '#fffab0'], emissive=0.85)
    m.eye_dark = (42, 36, 54)
    m.white = (255, 250, 176)
    m.height = 50
    m.max_w = 60
    # stout upright body on short legs
    for s in (-1, 1):
        m.tube([(s * 4.2, 8.0, 0.0), (s * 4.4, 3.4, 1.0)], [3.2, 2.8], 'fur', 'leg%d' % s)
        m.ell((s * 4.4, 1.6, 2.6), (2.9, 1.6, 3.8), 'fur', 'leg%d' % s)
        for t in (-1, 0, 1):
            m.crystal((s * 4.4 + t * 1.2, 1.4, 5.4), (s * 4.4 + t * 1.6, 0.6, 7.6), 0.55, 'steel',
                      'leg%d' % s, sides=4, tip_frac=0.8)
    m.ell((0, 13.0, 0.0), (8.2, 9.0, 7.2), 'fur', 'body')
    m.ell((0, 20.5, 1.0), (7.2, 6.2, 6.2), 'fur', 'body')
    m.paint((0, 13.0, 6.0), (5.6, 7.0, 3.0), 'fur', ['body'])
    m.tube([(0, 7.0, -6.4), (0.8, 5.4, -8.8), (1.2, 4.6, -10.0)], [1.4, 1.0, 0.6], 'nose', 'tail')
    # huge shovel hands with steel claws
    for s in (-1, 1):
        m.tube([(s * 6.6, 21.0, 1.0), (s * 10.0, 16.4, 3.4)], [3.0, 2.6], 'fur', 'arm%d' % s)
        hc = (s * 10.8, 13.8, 5.6)
        m.ell(hc, (3.8, 3.4, 1.8), 'fur', 'arm%d' % s, rot=(s * 30, 0, s * 12))
        m.paint(add(hc, (s * 0.6, 0, 1.2)), (2.6, 2.4, 1.4), 'nose', ['arm%d' % s])
        for t in (-1.5, -0.5, 0.5, 1.5):
            b = add(hc, (s * 0.4 + t * 1.5, -2.2, 0.8))
            m.crystal(b, add(b, (s * 0.6 + t * 0.4, -3.6, 1.8)), 0.7, 'steel', 'arm%d' % s,
                      sides=4, tip_frac=0.85)
    # the dynamo on its back: copper coil drum, steel end caps, a toothed crank wheel
    dc = (0, 20.5, -8.4)
    m.ell(dc, (6.2, 4.4, 4.4), 'copper', 'dynamo', rot=(0, 0, 0))
    for k in range(5):
        x = -4.0 + k * 2.0
        m.paint((x, dc[1], dc[2]), (0.35, 4.8, 4.8), 'copper', ['dynamo'])
    for s in (-1, 1):
        m.ell((s * 6.0, dc[1], dc[2]), (0.9, 3.6, 3.6), 'steel', 'dynamo')
    wc = (7.2, dc[1], dc[2])
    m.ell(wc, (0.8, 5.0, 5.0), 'steel', 'wheel')
    for k in range(10):
        a = 2 * math.pi * k / 10
        m.box(add(wc, (0, math.cos(a) * 5.2, math.sin(a) * 5.2)), (0.7, 0.8, 0.8), 'steel', 'wheel',
              rot=(0, -a / DEG, 0), bevel=0.1)
    m.ell(wc, (1.2, 1.4, 1.4), 'copper', 'wheel')
    m.tube([add(wc, (0.8, 0, 0)), add(wc, (2.0, 2.4, 1.6)), add(wc, (2.2, 3.0, 3.4))], 0.5,
           'steel', 'wheel')
    # terminal posts with a crackling arc between them
    for s in (-1, 1):
        m.tube([(s * 2.8, 24.2, -8.4), (s * 2.8, 27.4, -8.4)], 0.6, 'steel', 'posts')
        m.sph((s * 2.8, 27.6, -8.4), 0.9, 'spark', 'posts')
    g.zigzag(m, [(-2.2, 28.0, -8.4), (-0.8, 29.8, -8.0), (0.4, 27.8, -8.6), (2.2, 29.4, -8.2)],
             [0.6, 0.55, 0.55, 0.5], 'spark', 'arc', flat=0.7, up=(0, 0, 1))
    # head: tapered snout, star nose, tiny eyes, miner's lamp wired to the dynamo
    head_c, head_r = (0, 28.4, 3.4), (5.8, 5.0, 5.4)
    m.ell(head_c, head_r, 'fur', 'head')
    m.tube([(0, 27.4, 6.8), (0, 26.6, 9.6), (0, 26.0, 11.4)], [3.4, 2.5, 2.0], 'fur', 'head')
    nc = (0, 26.0, 12.0)
    m.sph(nc, 1.5, 'nose', 'nose')
    for k in range(10):
        a = 2 * math.pi * k / 10
        d = (math.cos(a), math.sin(a), 0.25)
        m.tube([add(nc, mul(d, 0.8)), add(nc, mul(d, 2.6))], [0.75, 0.45], 'nose', 'nose')
    lamp = (0, 32.6, 6.6)
    m.tube([(-4.8, 30.6, 3.6), (-2.6, 32.4, 5.8), (0, 32.8, 6.4), (2.6, 32.4, 5.8),
            (4.8, 30.6, 3.6)], 0.7, 'copper', 'strap')
    m.ell(lamp, (2.0, 1.8, 1.6), 'steel', 'lamp', rot=(0, -12, 0))
    m.ell(add(lamp, (0, 0.2, 1.4)), (1.4, 1.3, 0.6), 'spark', 'lamp')
    m.tube([(-3.4, 33.8, -1.0), (-5.0, 32.0, -5.4), (-3.8, 27.0, -8.0)], 0.55, 'copper', 'cable')
    for s in (-1, 1):
        p, n = g.on(head_c, head_r, (s * 0.42, -0.05, 0.9))
        m.eye(p, n, 1.4, 1.4, style='cute', minw=2, minh=2, glint=False)
    return m


# ==========================================================================
# 161 LULLABOX  RELIC/DREAM  music box that sings lullabies
# ==========================================================================
def lullabox(g):
    m = g.Model('LULLABOX')
    m.outline = (40, 16, 30)
    m.mat('wood', ['#4a1c28', '#7a3040', '#a84c5a', '#d27a80'])
    m.mat('gold', ['#9a6a18', '#e0b040', '#fff0a0'], spec=0.4)
    m.mat('dream', ['#b48cf0', '#f0e0ff'], emissive=0.8)
    m.mat('velvet', ['#28306e', '#4658a8', '#7a90d8'])
    m.eye_dark = (40, 16, 30)
    m.white = (240, 224, 255)
    m.height = 48
    m.max_w = 50
    DB, R, H = (0, 3.0, 0), 9.4, 11.0
    frustum(m, DB, R, R - 0.4, H, 16, 'wood', 'drum', phase=90.0 + 11.25)
    for y, r in ((DB[1] + 0.3, R + 0.4), (DB[1] + H - 0.2, R)):
        ring = [(math.cos(a * DEG) * r, y, math.sin(a * DEG) * r) for a in range(0, 361, 20)]
        m.tube(ring, 0.8, 'gold', 'drum')
    for a in (45, 135, 225, 315):
        m.sph((math.cos(a * DEG) * 7.2, 1.6, math.sin(a * DEG) * 7.2), 1.9, 'gold', 'feet')
    # gold filigree dots around the drum
    for a in range(0, 360, 30):
        p = (math.cos(a * DEG) * (R - 0.2), DB[1] + 2.2, math.sin(a * DEG) * (R - 0.2))
        m.paint(p, 0.7, 'gold', ['drum'])
    # carousel canopy on twisted gold poles, a scalloped velvet rim
    top = DB[1] + H
    for a in (45, 135, 225, 315):
        pts = [(math.cos((a + t * 30) * DEG) * 6.8, top + t * 7.0, math.sin((a + t * 30) * DEG) * 6.8)
               for t in (0, 0.33, 0.66, 1.0)]
        m.tube(pts, 0.55, 'gold', 'poles')
    cy = top + 8.2
    m.ell((0, cy, 0), (10.6, 2.2, 10.6), 'velvet', 'canopy')
    m.ell((0, cy + 1.6, 0), (8.6, 4.2, 8.6), 'velvet', 'canopy')
    for k in range(16):
        a = 2 * math.pi * k / 16
        m.sph((math.cos(a) * 10.4, cy - 1.8, math.sin(a) * 10.4), 1.5, 'velvet', 'canopy')
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        m.paint((math.cos(a) * 7.0, cy + 3.0, math.sin(a) * 7.0), (1.2, 2.4, 1.2), 'gold',
                ['canopy'])
    # finial: a glowing crescent moon and a star
    m.tube([(0, cy + 5.4, 0), (0, cy + 7.6, 0)], 0.5, 'gold', 'finial')
    mc = (0, cy + 10.4, 0.4)
    ring = [add(mc, (math.cos(a * DEG) * 2.8, math.sin(a * DEG) * 2.8, 0))
            for a in range(-60, 181, 20)]
    m.tube(ring, [0.5, 0.9, 1.3, 1.5, 1.6, 1.6, 1.5, 1.3, 1.1, 0.9, 0.7, 0.5, 0.3], 'dream',
           'moon', flat=0.6, up=(0, 0, 1))
    # the dream it plays: a small glowing sheep turning on the spindle
    m.tube([(0, top, 0), (0, cy - 1.6, 0)], 0.5, 'gold', 'spindle')
    sc = (0, top + 3.6, 0.6)
    g.seedball(m, sc, (2.4, 2.0, 2.0), 'dream', 'sheep', n=18, fil=0.25, tip=0.5, seed=6)
    m.ell(add(sc, (0, 0.4, 2.2)), (1.1, 1.0, 1.0), 'velvet', 'sheep')
    for s in (-1, 1):
        m.tube([add(sc, (s * 1.2, -1.2, 0.8)), add(sc, (s * 1.2, -3.0, 0.8))], 0.4, 'velvet',
               'sheep')
    # wind-up key behind
    kb = (0, DB[1] + H * 0.5, -R)
    m.tube([kb, add(kb, (0, 0, -3.0))], 0.6, 'gold', 'key')
    for s in (-1, 1):
        lp = [add(kb, (s * math.sin(a * DEG) * 2.4, math.cos(a * DEG) * 1.6 + 1.6, -3.6))
              for a in range(0, 361, 45)]
        m.tube(lp, 0.55, 'gold', 'key')
    # music notes drifting up
    for (x, y, z, h) in ((-10.6, top + 4.6, 4.0, 3.0), (11.4, top + 1.6, 3.0, 2.6),
                         (9.6, cy + 6.0, 2.0, 2.4)):
        m.ell((x, y, z), (0.9, 0.7, 0.4), 'dream', 'notes', rot=(0, 0, 20))
        m.tube([(x + 0.8, y + 0.2, z), (x + 0.8, y + h, z)], 0.25, 'dream', 'notes')
        m.tube([(x + 0.8, y + h, z), (x + 1.8, y + h - 1.0, z)], 0.25, 'dream', 'notes')
    # face on the drum: closed singing eyes and a round mouth
    def S(x, y):
        return frustum_surf(DB, R, R - 0.4, H, 16, x, y, 90.0 + 11.25)
    for s in (-1, 1):
        p, n = S(s * 3.2, DB[1] + 6.6)
        m.eye(p, n, 2.6, 1.6, style='closed', minw=3)
        p, n = S(s * 5.4, DB[1] + 4.6)
        m.dot(p, n, w=1.8, h=1.0, color=('wood', 3), shape='oval', minw=2)
    p, n = S(0, DB[1] + 3.8)
    m.mouth(p, n, 'open', w=2.2, h=2.2, color='outline', inner=('wood', 0))
    return m


# ==========================================================================
# 162 KITSUFLAME  BLAZE/DREAM  nine-tailed fox of foxfire
# ==========================================================================
def kitsuflame(g):
    m = g.Model('KITSUFLAME')
    m.outline = (38, 26, 70)
    m.mat('fur', ['#8a7aa8', '#c4b8dc', '#ece6f6', '#ffffff'], th=[0.22, 0.5, 0.84])
    m.mat('mark', ['#a8204a', '#e0487a'])
    m.mat('fire', ['#5a4ae0', '#8a8cff', '#d0e0ff'], emissive=0.7)
    m.eye_dark = (38, 26, 70)
    m.white = (255, 255, 255)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -22
    # seated slender fox
    for s in (-1, 1):
        m.ell((s * 4.0, 7.0, -3.0), (3.6, 5.4, 5.4), 'fur', 'hip%d' % s)
        m.ell((s * 4.6, 1.3, 1.6), (1.9, 1.3, 3.4), 'fur', 'foot%d' % s)
        m.tube([(s * 2.4, 11.0, 2.0), (s * 2.6, 5.5, 3.2), (s * 2.7, 1.8, 3.8)], [1.9, 1.5, 1.4],
               'fur', 'legF%d' % s)
        m.ell((s * 2.7, 1.3, 4.6), (1.7, 1.3, 2.1), 'fur', 'legF%d' % s)
        m.paint((s * 2.7, 1.4, 4.8), (2.0, 1.0, 2.0), 'mark', ['legF%d' % s])
    m.ell((0, 12.5, -0.6), (4.6, 7.8, 4.8), 'fur', 'body', rot=(0, -12, 0))
    m.tube([(0, 17.0, 0.4), (0, 21.0, 1.6)], [3.0, 2.6], 'fur', 'body')
    # nine tails fanned behind, each tipped with foxfire
    for k in range(9):
        a = (-84 + 21 * k) * DEG
        d = (math.sin(a), math.cos(a) * 0.95 + 0.2, 0)
        b = (0.0, 6.0, -6.0)
        p1 = add(b, (d[0] * 6.0, d[1] * 6.0, -3.0))
        p2 = add(b, (d[0] * 13.0, d[1] * 13.0, -5.0 + 0.6 * abs(k - 4)))
        p3 = add(b, (d[0] * 17.0, d[1] * 17.0, -4.4 + 0.6 * abs(k - 4)))
        part = 'tail%d' % k
        m.tube([b, p1, p2, p3], [1.2, 2.2, 2.4, 1.4], 'fur', part)
        g.flame(m, p3, 6.0, 2.2, part, mats=('fire', 'fire', 'fur'),
                up=norm((d[0], d[1], -0.1)), face=(0.3, 0.2, 1), tongues=2, seed=k)
    # head: long ears, pointed muzzle, red kitsune markings
    head_c, head_r = (0, 24.4, 2.4), (4.6, 4.2, 4.4)
    m.ell(head_c, head_r, 'fur', 'head')
    m.tube([(0, 23.2, 5.6), (0, 22.4, 8.2), (0, 22.0, 9.4)], [2.4, 1.6, 0.9], 'fur', 'head')
    for s in (-1, 1):
        m.tube([(s * 2.6, 27.4, 1.6), (s * 3.8, 31.6, 1.0), (s * 4.8, 36.0, 0.2)],
               [2.4, 1.6, 0.2], 'fur', 'ear%d' % s, flat=0.4, up=(0, 0.1, 1))
        m.paint((s * 3.4, 30.0, 2.2), (0.9, 2.4, 0.9), 'mark', ['ear%d' % s])
        m.tube([(s * 3.8, 23.6, 2.4), (s * 6.4, 22.0, 1.2), (s * 7.2, 20.6, 0.4)],
               [1.4, 0.9, 0.2], 'fur', 'head', flat=0.5, up=(0, 0, 1))
        p, n = g.on(head_c, head_r, (s * 0.5, 0.35, 0.8))
        m.paint(add(p, (s * 0.6, 0.8, 0)), (0.6, 1.4, 0.8), 'mark', ['head'])
    m.paint((0, 27.6, 5.2), (0.7, 1.4, 1.0), 'mark', ['head'])
    # a foxfire orb held before its chest
    m.sph((0, 14.0, 6.4), 2.0, 'fire', 'orb')
    m.sph((0.4, 14.4, 7.6), 0.9, 'fur', 'orb')
    g.eye_pair(m, head_c, head_r, 34, 10, 3.2, 2.6, style='sharp', iris=('fire', 1), slant=0.9,
               lid=1, center=(0, 23, 12), turn=6)
    m.dot((0, 22.2, 9.8), (0, 0.3, 1), w=1.4, h=1.0, minw=2, color='outline')
    p, n = g.on(head_c, head_r, (0.05, -0.55, 0.8))
    m.mouth(p, n, 'w', w=2.6)
    return m


# ==========================================================================
# 163 WYVERNIX  GALE/WYRM  wyvern
# ==========================================================================
def wyvernix(g):
    m = g.Model('WYVERNIX')
    m.outline = (16, 12, 40)
    m.mat('scale', ['#1e1a48', '#342e78', '#5048a8', '#7a74d0'])
    m.mat('belly', ['#9aa8d0', '#d8e0f4'])
    m.mat('memb', ['#8894c0', '#c0cae8', '#f0f4ff'])
    m.mat('wind', ['#3ad0e8', '#b0f8ff'], emissive=0.6)
    m.eye_dark = (16, 12, 40)
    m.white = (240, 244, 255)
    m.height = 58
    m.max_w = 62
    m.back_scale = 1.12
    side_yaw(g, m, -62)
    # arm-wings spread wide, membrane streaked with jet-stream light
    for s in (-1, 1):
        sh = (s * 4.6, 26.0, -1.0)
        el = (s * 12.5, 33.0, -3.6)
        wr = (s * 20.0, 41.0, -5.6)
        m.tube([sh, el, wr], [2.2, 1.7, 1.2], 'scale', 'wing%d' % s)
        f0 = (s * 28.5, 36.0, -7.0)
        f1 = (s * 27.0, 25.0, -6.2)
        f2 = (s * 19.0, 16.5, -4.4)
        mem = [sh, el, wr, f0, (s * 25.4, 31.2, -6.4), f1, (s * 21.4, 22.0, -5.2), f2,
               (s * 11.0, 16.4, -2.8), (s * 5.0, 18.0, -1.8)]
        m.poly(mem, 'memb', 'wing%d' % s, puff=0.3)
        for f in (f0, f1, f2):
            m.tube([wr, f], [0.9, 0.35], 'scale', 'wing%d' % s)
        m.crystal(wr, add(wr, (s * 0.6, 3.4, 0.6)), 0.7, 'belly', 'wing%d' % s, sides=4,
                  tip_frac=0.7)
        for t0, t1 in ((0.25, 0.8), (0.45, 0.95)):
            a = lerp(el, (s * 6.0, 19.0, -2.0), t0)
            b = lerp(wr, f1, t1 * 0.8)
            paint_path(m, [a, lerp(a, b, 0.5), b], (0.7, 0.7, 2.4), 'wind', ['wing%d' % s],
                       steps=8)
    # long tail with a kite-vane tip
    tail = [(0, 16.0, -3.6), (1.0, 12.4, -10.0), (4.0, 8.6, -16.0), (9.0, 6.8, -20.4),
            (14.4, 7.6, -22.0), (18.0, 10.2, -21.0)]
    m.tube(tail, [3.4, 2.8, 2.2, 1.6, 1.0, 0.5], 'scale', 'tail')
    tt = tail[-1]
    m.poly([add(tt, (-0.4, 0, 0)), add(tt, (1.6, 3.8, 0.6)), add(tt, (4.6, 2.2, 1.0)),
            add(tt, (2.6, -1.4, 0.4))], 'memb', 'tailfin', puff=0.3)
    m.paint(add(tt, (2.0, 1.4, 0.6)), 1.0, 'wind', ['tailfin'])
    # legs with talons
    for s in (-1, 1):
        m.ell((s * 4.2, 14.4, -1.6), (3.2, 5.0, 4.2), 'scale', 'leg%d' % s)
        m.tube([(s * 4.6, 11.0, -3.0), (s * 5.0, 6.0, -5.2), (s * 5.0, 2.2, -2.6)],
               [2.4, 1.7, 1.4], 'scale', 'leg%d' % s)
        for t in (-1, 0, 1):
            m.crystal((s * 5.0 + t * 1.0, 1.6, -1.8), (s * 5.0 + t * 1.8, 0.4, 1.8), 0.7, 'belly',
                      'leg%d' % s, sides=4, tip_frac=0.8)
    # torso leaning forward, pale belly, S-curved neck
    m.ell((0, 20.5, 0.0), (5.6, 7.2, 5.8), 'scale', 'body', rot=(0, -18, 0))
    m.paint((0, 19.0, 5.2), (3.8, 6.0, 2.4), 'belly', ['body'])
    neck = [(0, 25.0, 2.4), (0, 29.0, 4.2), (0, 33.0, 4.4), (0, 36.0, 6.0)]
    m.tube(neck, [3.6, 2.9, 2.6, 2.6], 'scale', 'neck')
    for q in neck[1:3]:
        m.paint(add(q, (0, -0.4, 2.2)), (1.8, 1.8, 1.4), 'belly', ['neck'])
    for k, q in enumerate(neck + [(0, 22.0, -4.6), (0, 18.6, -5.4)]):
        m.crystal(add(q, (0, 1.8, -1.6)), add(q, (0, 3.2, -3.8)), 0.8, 'wind', 'fins', sides=4,
                  tip_frac=0.8)
    # head: long snout, swept-back horns like wind vanes
    head_c, head_r = (0, 37.8, 7.6), (3.8, 3.3, 4.4)
    m.ell(head_c, head_r, 'scale', 'head')
    m.tube([(0, 37.2, 10.4), (0, 36.6, 13.2), (0, 36.2, 15.0)], [2.6, 2.0, 1.4], 'scale', 'head')
    m.tube([(0, 35.4, 10.0), (0, 35.0, 13.4)], [1.6, 1.0], 'belly', 'head')
    for s in (-1, 1):
        m.tube([(s * 2.2, 40.2, 6.2), (s * 3.6, 41.8, 2.8), (s * 4.2, 42.2, -1.2)],
               [1.1, 0.8, 0.2], 'belly', 'horn%d' % s)
        m.tube([(s * 3.4, 38.0, 5.4), (s * 5.6, 37.2, 3.4), (s * 6.4, 36.8, 1.8)],
               [1.0, 0.6, 0.2], 'memb', 'head', flat=0.4, up=(0, 0.3, 1))
    g.eye_pair(m, head_c, head_r, 38, 18, 3.2, 2.6, style='sharp', iris=('wind', 0), slant=1.0,
               lid=1, center=(0, 36, 16), turn=4)
    m.mouth((0, 35.6, 14.2), (0, -0.2, 1), 'line', w=2.4)
    return m


# ---- not yet drawn -------------------------------------------------------
class _Stub:
    def __init__(self, name, types):
        self.name, self.types, self.rarity = name, types, 'F'


def _todo(name, t1, t2):
    def build(g):
        return g.placeholder_model(_Stub(name, (t1, t2)))
    return build


trihydra = _todo('TRIHYDRA', 'VENOM', 'WYRM')
phoenex = _todo('PHOENEX', 'BLAZE', 'ASTRAL')
ironhowl = _todo('IRONHOWL', 'METAL', 'BEAST')
nimbwhale = _todo('NIMBWHALE', 'GALE', 'TIDE')
jollyrogue = _todo('JOLLYROGUE', 'HOLLOW', 'RELIC')
runelith = _todo('RUNELITH', 'RELIC', 'STONE')
faefly = _todo('FAEFLY', 'DREAM', 'SWARM')
snowbrute = _todo('SNOWBRUTE', 'FROST', 'BRAWL')
teslarose = _todo('TESLAROSE', 'BLOOM', 'SPARK')
noctmare = _todo('NOCTMARE', 'DUSK', 'DREAM')
