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
        p, n = g.on(head_c, head_r, (s * 0.72, 0.35, 0.6))
        m.dot(p, n, w=3.0, h=3.0, color='outline', shape='oval', minw=3, minh=3)
        m.eye(p, n, 1.8, 1.8, style='glow', iris=('spark', 1), minw=2, minh=2,
              center=(0, 29, 14))
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
    m.mat('fire', ['#0c50d0', '#1896f0', '#6cdcff'], emissive=0.75)
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
        a = (-88 + 22 * k) * DEG
        d = (math.sin(a), math.cos(a) * 0.95 + 0.2, 0)
        b = (0.0, 6.0, -6.0)
        p1 = add(b, (d[0] * 6.0, d[1] * 6.0, -3.0))
        p2 = add(b, (d[0] * 13.0, d[1] * 13.0, -5.0 + 0.6 * abs(k - 4)))
        p3 = add(b, (d[0] * 17.0, d[1] * 17.0, -4.4 + 0.6 * abs(k - 4)))
        part = 'tail%d' % k
        m.tube([b, p1, p2, p3], [1.2, 1.9, 2.1, 1.6], 'fur', part,
               mats=[(0, 'fur'), (0.5, 'fire')])
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


# ==========================================================================
# 164 TRIHYDRA  VENOM/WYRM  three-headed marsh hydra
# ==========================================================================
def trihydra(g):
    m = g.Model('TRIHYDRA')
    m.outline = (14, 24, 20)
    m.mat('skin', ['#1a3230', '#2c5446', '#467a5a', '#6ea070'])
    m.mat('belly', ['#8a7c44', '#c8bc78'])
    m.mat('toxin', ['#8ad81c', '#e4ff7a'], emissive=0.85)
    m.mat('crest', ['#561c46', '#90346a', '#cc628c'])
    m.eye_dark = (14, 24, 20)
    m.white = (228, 255, 122)
    m.height = 54
    m.max_w = 62
    m.front_yaw = -26
    # squat body on stumpy clawed legs
    bc, br = (0, 11.5, -3.0), (10.0, 7.6, 11.5)
    m.ell(bc, br, 'skin', 'body')
    m.paint((0, 7.0, 3.0), (7.4, 3.6, 8.0), 'belly', ['body'])
    for s in (-1, 1):
        for nm, z in (('legF', 4.5), ('legB', -10.0)):
            part = '%s%d' % (nm, s)
            m.tube([(s * 7.2, 9.5, z), (s * 8.8, 4.6, z + 1.0), (s * 9.0, 2.0, z + 1.6)],
                   [3.6, 3.0, 2.7], 'skin', part)
            m.ell((s * 9.0, 1.5, z + 2.8), (3.0, 1.5, 3.2), 'skin', part)
            for t in (-1, 0, 1):
                m.crystal((s * 9.0 + t * 1.3, 1.2, z + 5.0), (s * 9.0 + t * 1.8, 0.4, z + 6.8),
                          0.6, 'belly', part, sides=4, tip_frac=0.8)
    # tail curling round the side, spiked
    tail = [(0, 10.0, -13.0), (4.0, 6.0, -20.0), (11.0, 3.4, -22.0), (17.0, 3.2, -18.0),
            (19.6, 4.2, -12.6)]
    m.tube(tail, [5.2, 3.8, 2.6, 1.6, 0.5], 'skin', 'tail')
    for q in tail[1:4]:
        m.crystal(add(q, (0, 1.4, 0)), add(q, (0, 4.2, 0.4)), 0.9, 'crest', 'tail', sides=4,
                  tip_frac=0.8)
    # dorsal ridge
    for k in range(5):
        q = (0, 18.4 - k * 0.5, 2.0 - k * 3.6)
        m.crystal(q, add(q, (0, 3.2, -1.4)), 1.1, 'crest', 'ridge', sides=4, tip_frac=0.8)
    # glowing venom spots
    for d, r in (((0.55, 0.62, 0.35), 2.0), ((0.8, 0.35, -0.3), 1.9), ((-0.6, 0.55, 0.2), 1.9),
                 ((0.3, 0.8, -0.55), 1.7), ((-0.45, 0.7, -0.6), 1.7), ((0.9, 0.2, 0.3), 1.6),
                 ((-0.85, 0.3, -0.2), 1.6), ((0.2, 0.55, 0.85), 1.6)):
        p, n = g.on(bc, br, d)
        m.paint(p, (r, r, r), 'toxin', ['body'])

    # three necks, each head with its own crest
    def neck_head(pts, radii, hc, kind, part):
        m.tube(pts, radii, 'skin', part + 'neck')
        for q in pts[1:3]:
            m.paint(add(q, (0, -0.6, radii[1] * 0.8)), (1.8, 1.8, 1.4), 'belly', [part + 'neck'])
        p, n = g.on(pts[1], (radii[1],) * 3, (0.3, 0.5, -0.8))
        m.paint(p, 1.5, 'toxin', [part + 'neck'])
        hr = (4.2, 3.6, 4.4)
        m.ell(hc, hr, 'skin', part)
        m.tube([add(hc, (0, -0.2, 2.6)), add(hc, (0, -0.8, 5.6)), add(hc, (0, -1.0, 7.0))],
               [3.0, 2.3, 1.8], 'skin', part)
        m.tube([add(hc, (0, -2.4, 2.0)), add(hc, (0, -2.9, 5.6))], [1.9, 1.2], 'belly', part)
        if kind == 'fin':
            m.poly([add(hc, (0, 2.6, 2.0)), add(hc, (0, 9.6, -0.6)), add(hc, (0, 7.6, -4.2)),
                    add(hc, (0, 4.2, -5.8)), add(hc, (0, 2.0, -3.0))], 'crest', part + 'crest',
                   puff=0.6)
            for a, b in (((0, 2.8, 1.6), (0, 9.4, -0.4)), ((0, 2.4, -1.2), (0, 7.4, -4.0))):
                m.tube([add(hc, a), add(hc, b)], [0.7, 0.3], 'crest', part + 'crest')
        elif kind == 'horns':
            for s in (-1, 1):
                m.tube([add(hc, (s * 2.2, 2.4, 0.8)), add(hc, (s * 3.6, 5.2, -1.4)),
                        add(hc, (s * 4.0, 6.6, -4.6))], [1.4, 1.0, 0.3], 'crest',
                       part + 'crest')
        else:
            b = add(hc, (0, 1.0, -2.2))
            for k in range(5):
                a = (10 + 40 * k) * DEG
                tip = add(b, (math.cos(a) * 7.0, math.sin(a) * 6.0, -1.6))
                m.crystal(b, tip, 0.9, 'crest', part + 'crest', sides=4, tip_frac=0.5)
            fan = [b] + [add(b, (math.cos(a * DEG) * 5.2, math.sin(a * DEG) * 4.6, -1.0))
                         for a in range(10, 171, 20)]
            m.poly(fan, 'crest', part + 'crest', puff=0.3)
        for s in (-1, 1):
            p, n = g.on(hc, hr, (s * 0.62, 0.42, 0.66))
            m.dot(p, n, w=3.4, h=2.8, color='outline', shape='oval', minw=3, minh=2)
            m.eye(p, n, 2.6, 1.8, style='glow', iris=('toxin', 1), slant=0.6,
                  center=add(hc, (0, 0, 9)))
        return hc
    neck_head([(0, 15.0, 5.0), (0, 24.0, 7.4), (0, 31.0, 6.0), (0, 36.0, 7.0)],
              [4.6, 3.6, 3.2, 3.2], (0, 38.6, 9.4), 'fin', 'headC')
    for s, kind in ((-1, 'horns'), (1, 'frill')):
        hc = (s * 16.0, 29.6, 10.6)
        neck_head([(s * 4.0, 14.6, 4.6), (s * 9.4, 19.4, 7.0), (s * 13.6, 24.0, 6.6),
                   (s * 15.6, 27.2, 7.8)], [4.4, 3.5, 3.2, 3.2], hc, kind, 'head%d' % s)
    # mouths: the middle one hisses, the side ones grin with fangs
    m.mouth((0, 36.8, 16.2), (0, -0.3, 1), 'open', w=2.6, h=2.0, color='outline',
            inner=('crest', 0))
    for s in (-1, 1):
        m.mouth((s * 16.0, 27.8, 17.2), (0, -0.3, 1), 'line', w=2.4, fang=1)
    # a venom drip from the middle jaw
    m.tube([(0, 35.8, 16.0), (0, 33.8, 16.2)], [0.5, 0.9], 'toxin', 'drip')
    return m


# ==========================================================================
# 165 PHOENEX  BLAZE/ASTRAL  phoenix of starfire
# ==========================================================================
def phoenex(g):
    m = g.Model('PHOENEX')
    m.outline = (40, 14, 34)
    m.mat('plume', ['#6e1420', '#b42c1e', '#ea5a1c', '#ffa030'])
    m.mat('flame', ['#ff5a1a', '#ffa030'], emissive=0.75)
    m.mat('night', ['#160e3c', '#2e1e6e', '#5a3ea6'])
    m.mat('gold', ['#b07a1a', '#ffe070'], spec=0.4)
    m.eye_dark = (40, 14, 34)
    m.white = (255, 244, 200)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -20
    hover(g, m, 4)
    side_yaw(g, m, -60)
    # the starfield tail: long night plumes with burning rims, fanned below
    root = (0, 20.0, -3.4)
    for k in range(5):
        a = (-50 + 25 * k) * DEG
        ln = 22.0 - 2.6 * abs(k - 2)
        d = (math.sin(a) * 1.1, -math.cos(a), -0.3)
        tip = add(root, mul(d, ln))
        mid = add(lerp(root, tip, 0.5), (d[0] * 1.2, 0, -1.2))
        w = 3.0
        part = 'tail%d' % k
        g.leaf(m, root, mid, add(tip, mul(d, 1.8)), w + 1.1, 'flame', part, up=(0, 0.3, 1),
               flat=0.2)
        g.leaf(m, root, mid, tip, w, 'night', part, up=(0, 0.3, 1), flat=0.5)
        for t in (0.45, 0.72):
            q = lerp(lerp(root, mid, t * 2) if t < 0.5 else lerp(mid, tip, t * 2 - 1), root, 0)
            m.sparkle(add(q, (0, 0.4, w * 0.55)), (0, 0.3, 1), size=1)
    # upright body, pale gold breast
    bc, br = (0, 25.0, 0.0), (5.4, 7.6, 5.2)
    m.ell(bc, br, 'plume', 'body', rot=(8, 0, 0))
    m.paint((0, 24.0, 4.2), (3.8, 5.6, 2.0), 'gold', ['body'])
    # tucked talons
    for s in (-1, 1):
        m.tube([(s * 2.4, 19.0, 1.0), (s * 2.6, 16.4, 2.4)], [1.2, 0.8], 'gold', 'leg%d' % s)
        for t in (-1, 0, 1):
            m.crystal((s * 2.6, 16.2, 2.4), (s * 2.6 + t * 0.9, 14.6, 3.8), 0.45, 'gold',
                      'leg%d' % s, sides=4, tip_frac=0.8)
    # raised wings: fiery flight feathers along the arm, starry coverts
    for s in (-1, 1):
        sh = (s * 4.2, 29.0, -1.0)
        el = (s * 11.0, 35.0, -3.4)
        wr = (s * 18.0, 42.0, -4.4)
        part = 'wing%d' % s
        m.tube([sh, el, wr], [2.4, 1.9, 1.2], 'plume', part)
        for k in range(7):
            t = k / 6.0
            b = lerp(sh, el, t * 2) if t <= 0.5 else lerp(el, wr, t * 2 - 1)
            ln = 8.0 + 7.0 * t
            tip = add(b, (s * (2.0 + 6.0 * t) * (ln / 12.0), -ln * (1.0 - 0.55 * t), -0.8))
            g.leaf(m, b, lerp(b, tip, 0.5), tip, 1.9, 'plume', part, up=(0, 0.2, 1), flat=0.3,
                   mats=[(0, 'plume'), (0.62, 'flame')])
        m.poly([sh, el, wr, add(wr, (s * 1.0, -6.0, 0)), add(el, (s * 1.0, -7.0, 0.2)),
                add(sh, (s * 1.0, -5.0, 0.4))], 'night', part, puff=0.35)
        for q in (add(el, (s * -1.4, -2.8, 1.2)), add(el, (s * 3.2, -1.2, 1.0))):
            m.sparkle(q, (0, 0.2, 1), size=1)
    # head with a flame crest and a gold beak
    hc, hr = (0, 35.6, 2.0), (3.9, 3.7, 3.9)
    m.tube([(0, 30.0, 0.6), (0, 33.6, 1.6)], [3.6, 3.2], 'plume', 'head')
    m.ell(hc, hr, 'plume', 'head')
    m.crystal((0, 35.4, 5.0), (0, 33.6, 9.4), 1.5, 'gold', 'beak', sides=5, tip_frac=0.9)
    for k, (dx, h) in enumerate(((-1.6, 6.0), (0.0, 8.0), (1.6, 6.0))):
        g.flame(m, (dx, 38.4, 0.8), h, 1.9, 'crest', mats=('flame', 'plume', 'gold'),
                up=(dx * 0.18, 1, -0.55), tongues=0, seed=k)
    g.eye_pair(m, hc, hr, 36, 12, 2.8, 2.6, style='sharp', iris=('night', 2), slant=0.8,
               lid=1, center=(0, 34, 10), turn=4)
    return m


# ==========================================================================
# 166 IRONHOWL  METAL/BEAST  armoured wolf
# ==========================================================================
def ironhowl(g):
    m = g.Model('IRONHOWL')
    m.outline = (12, 14, 24)
    m.mat('fur', ['#1c1e2c', '#30364a', '#4c5470', '#727c9c'])
    m.mat('steel', ['#4a5264', '#808c9e', '#c8d2e0'], spec=0.5)
    m.mat('mag', ['#2a86ff', '#aee2ff'], emissive=0.85)
    m.eye_dark = (12, 14, 24)
    m.white = (200, 210, 224)
    m.height = 54
    m.max_w = 62
    m.front_yaw = -56
    # long lean body on tall legs
    m.ell((0, 20.0, -2.0), (5.4, 5.8, 13.0), 'fur', 'body')
    m.ell((0, 21.0, 8.0), (6.0, 7.2, 6.0), 'fur', 'body')
    m.paint((0, 16.4, 8.0), (4.4, 3.0, 5.0), 'fur', ['body'])
    for s in (-1, 1):
        m.tube([(s * 3.6, 17.0, 9.0), (s * 3.8, 9.0, 10.0), (s * 3.8, 2.4, 10.4)],
               [2.8, 2.1, 1.9], 'fur', 'legF%d' % s)
        m.ell((s * 3.8, 1.5, 11.6), (2.2, 1.5, 2.8), 'fur', 'legF%d' % s)
        m.ell((s * 3.9, 7.6, 10.2), (2.5, 3.0, 2.5), 'steel', 'legF%d' % s)
        m.ell((s * 4.2, 18.0, -10.0), (3.4, 6.0, 5.4), 'fur', 'legB%d' % s)
        m.tube([(s * 4.4, 14.0, -12.0), (s * 4.6, 8.0, -14.4), (s * 4.4, 2.4, -12.4)],
               [2.8, 2.1, 1.9], 'fur', 'legB%d' % s)
        m.ell((s * 4.4, 1.5, -11.2), (2.2, 1.5, 2.8), 'fur', 'legB%d' % s)
        m.ell((s * 4.6, 7.4, -14.2), (2.4, 2.8, 2.4), 'steel', 'legB%d' % s)
        # riveted shoulder pauldron and haunch plate, split by glowing seams
        m.ell((s * 4.4, 23.0, 7.0), (2.8, 5.4, 5.6), 'steel', 'plate%d' % s, rot=(0, 0, s * 20))
        m.paint((s * 6.6, 22.0, 7.0), (1.6, 5.0, 0.9), 'mag', ['plate%d' % s])
        m.ell((s * 4.6, 20.6, -10.0), (2.4, 4.6, 4.8), 'steel', 'plate%d' % s, rot=(0, 0, s * 16))
        m.paint((s * 6.6, 19.6, -10.0), (1.6, 4.0, 0.9), 'mag', ['plate%d' % s])
        for z in (4.2, 9.8):
            m.dot((s * 6.8, 25.4, z), (s * 0.9, 0.3, 0.2), color=('steel', 0))
    # segmented back armour: three plates, magnet-blue light between them
    for k, z in enumerate((2.6, -3.4, -9.4)):
        m.ell((0, 25.0 - k * 0.5, z), (4.4, 2.6, 3.4), 'steel', 'armor')
    for z in (-0.4, -6.4):
        m.paint((0, 25.0, z), (3.8, 3.4, 0.9), 'mag', ['armor', 'body'])
    # bushy tail hanging low, steel-capped
    tail = [(0, 21.0, -14.0), (0, 19.0, -19.0), (0, 15.4, -23.0), (0, 13.0, -25.4)]
    m.tube(tail, [2.2, 3.4, 3.0, 1.6], 'fur', 'tail')
    m.crystal((0, 13.6, -25.0), (0, 11.0, -28.6), 1.8, 'steel', 'tail', sides=5, tip_frac=0.6)
    # shaggy ruff, neck stretched up, head raised to howl
    for k in range(7):
        a = (-70 + k * 23) * DEG
        b = (math.sin(a) * 4.6, 26.0 + math.cos(a) * 2.0, 9.0)
        m.crystal(b, add(b, (math.sin(a) * 2.4, 1.4 + math.cos(a) * 1.4, -5.6)), 1.8, 'fur',
                  'ruff', sides=4, tip_frac=0.8)
    m.tube([(0, 24.0, 9.0), (0, 29.4, 11.6), (0, 34.0, 12.6)], [5.0, 4.0, 3.5], 'fur', 'neck')
    m.paint((0, 28.0, 14.6), (2.6, 4.4, 1.6), 'steel', ['neck'])
    m.paint((0, 30.4, 14.2), (3.0, 0.8, 1.6), 'mag', ['neck'])
    hc, hr = (0, 37.0, 13.2), (4.4, 4.0, 4.6)
    m.ell(hc, hr, 'fur', 'head')
    m.tube([(0, 37.6, 16.0), (0, 40.2, 19.4), (0, 42.2, 22.0)], [3.1, 2.4, 1.7], 'fur', 'head')
    m.tube([(0, 39.2, 15.6), (0, 41.6, 18.8), (0, 43.2, 21.0)], [2.2, 1.8, 1.2], 'steel',
           'head')
    m.sph((0, 42.6, 22.6), 1.1, 'fur', 'head')
    # dropped jaw with a magnet-blue glow in the throat
    m.tube([(0, 34.8, 15.4), (0, 35.4, 19.0), (0, 36.2, 21.2)], [2.0, 1.4, 0.9], 'fur', 'jaw')
    m.ell((0, 37.2, 18.6), (1.3, 1.3, 2.2), 'mag', 'jaw')
    # tall ears with steel tips
    for s in (-1, 1):
        b = (s * 2.2, 39.6, 12.0)
        m.tube([b, add(b, (s * 0.6, 3.0, -1.6)), add(b, (s * 0.8, 5.6, -3.0))], [1.8, 1.2, 0.2],
               'fur', 'ear%d' % s, flat=0.5, up=(s * 0.8, 0, 0.6))
        m.paint(add(b, (s * 0.7, 4.4, -2.4)), 1.3, 'steel', ['ear%d' % s])
        p, n = g.on(hc, hr, (s * 0.7, 0.3, 0.62))
        m.dot(p, n, w=3.4, h=2.8, color='outline', shape='oval', minw=3, minh=3)
        m.eye(p, n, 2.6, 2.0, style='glow', iris=('mag', 1), slant=0.5, minh=3,
              center=(0, 36, 24))
    # rings of sound rising from the howl
    D = norm((0, 0.72, 0.7))
    P = norm((0, -0.7, 0.72))
    for k, r in enumerate((3.4,)):
        c = add((0, 42.4, 22.4), mul(D, 3.6))
        arc = [add(c, add(mul(P, math.sin(a * DEG) * r), mul(D, math.cos(a * DEG) * r * 0.45)))
               for a in range(-60, 61, 20)]
        m.tube(arc, 0.6, 'mag', 'howl')
    return m


# ==========================================================================
# 167 NIMBWHALE  GALE/TIDE  cloud whale
# ==========================================================================
def nimbwhale(g):
    m = g.Model('NIMBWHALE')
    m.outline = (20, 34, 70)
    m.mat('skin', ['#2a5aa8', '#4a86d0', '#78b4ec', '#a8d8ff'])
    m.mat('cloud', ['#aab8dc', '#dce6f8', '#ffffff'])
    m.mat('r_red', ['#ff6a80'], emissive=0.8)
    m.mat('r_yel', ['#ffe060'], emissive=0.8)
    m.mat('r_grn', ['#6ae08a'], emissive=0.8)
    m.mat('r_blu', ['#6ac8ff'], emissive=0.8)
    m.eye_dark = (20, 34, 70)
    m.white = (255, 255, 255)
    m.height = 52
    m.max_w = 62
    m.front_yaw = -28
    hover(g, m, 4)
    side_yaw(g, m, -70)
    # round body, pale grooved throat
    bc, br = (0, 18.0, 0.0), (11.6, 10.2, 13.0)
    m.ell(bc, br, 'skin', 'body')
    m.paint((0, 11.0, 5.0), (9.4, 5.6, 9.4), 'cloud', ['body'])
    for x in (-3.6, 0.0, 3.6):
        m.paint((x, 10.4, 9.4), (0.7, 3.4, 3.0), 'skin', ['body'])
    # pectoral flippers and a raised tail with broad flukes
    for s in (-1, 1):
        m.ell((s * 11.4, 12.4, 4.0), (5.4, 1.3, 2.8), 'skin', 'fin%d' % s, rot=(0, s * 20, s * -28))
    m.tube([(0, 19.0, -10.0), (0, 22.4, -16.0), (0, 26.4, -19.4)], [7.0, 4.2, 2.2], 'skin', 'tail')
    tt = (0, 27.4, -20.2)
    for s in (-1, 1):
        m.poly([tt, add(tt, (s * 3.0, 3.6, -1.6)), add(tt, (s * 8.4, 5.4, -2.4)),
                add(tt, (s * 7.2, 2.0, -1.4)), add(tt, (s * 3.4, 0.4, -0.4))], 'skin', 'tail',
               puff=0.4)
    # the cloud mantle draped over its back
    rnd = g.Rand(167)
    for el in (82, 58, 36):
        for az in range(185, 360, 26 if el > 40 else 22):
            a = (az + (13 if el == 58 else 0)) * DEG
            d = (math.cos(a) * math.cos(el * DEG), math.sin(el * DEG), math.sin(a) * math.cos(el * DEG))
            p, n = g.on(bc, br, d)
            m.sph(add(p, mul(n, 0.8)), 3.4 + 1.2 * rnd.f(), 'cloud', 'mantle')
    for az in (200, 340):
        a = az * DEG
        p, n = g.on(bc, br, (math.cos(a) * 0.6, 0.8, math.sin(a) * 0.6))
        m.sph(add(p, mul(n, 0.6)), 3.4, 'cloud', 'mantle')
    # rainbow spout from the blowhole, arcing out to both sides
    bh = (0, 28.2, 1.0)
    m.sph(bh, 1.8, 'cloud', 'spout')
    bands = ('r_red', 'r_yel', 'r_grn', 'r_blu')
    for s in (-1, 1):
        for i, mat in enumerate(bands):
            R = 7.0 - i * 1.15
            c = (s * 7.4, 30.0, 1.0)
            arc = [add(c, (s * R * math.cos(a * DEG) * -1, R * math.sin(a * DEG) * 1.15, 0))
                   for a in range(0, 181, 15)]
            arc = [q for q in arc if q[1] > 29.4 or abs(q[0]) > 7.4]
            m.tube(arc, 0.66, mat, 'spout')
        m.sph((s * 14.8, 29.4, 1.0), 1.4, 'cloud', 'spout')
        m.sph((s * 13.4, 27.4, 1.4), 0.9, 'cloud', 'spout')
    # face: wide smile, round eyes low on the head
    g.eye_pair(m, bc, br, 42, 6, 3.4, 3.6, style='cute', turn=6)
    for s in (-1, 1):
        p, n = g.on(bc, br, (s * 0.62, -0.12, 0.78))
        m.paint(p, (1.8, 1.0, 1.0), 'r_red', ['body'])
    p, n = g.on(bc, br, (0.05, -0.12, 1.0))
    m.mouth(p, n, 'smile', w=7.0, h=2.0)
    return m


# ==========================================================================
# 168 JOLLYROGUE  HOLLOW/RELIC  skeleton pirate with a ship in a bottle
# ==========================================================================
def jollyrogue(g):
    m = g.Model('JOLLYROGUE')
    m.outline = (24, 14, 26)
    m.mat('bone', ['#9c8e74', '#d6ccb0', '#fff8e4'])
    m.mat('coat', ['#4a1020', '#841c30', '#b83a44'])
    m.mat('hat', ['#1c1828', '#383250'])
    m.mat('gold', ['#a87418', '#f4c850'], spec=0.4)
    m.mat('glass', ['#32b8a8', '#b4fff0'], emissive=0.8)
    m.eye_dark = (24, 14, 26)
    m.white = (255, 248, 228)
    m.height = 56
    m.max_w = 54
    m.front_yaw = -22
    # bone legs in cuffed boots
    for s in (-1, 1):
        m.tube([(s * 2.6, 13.0, 0.0), (s * 2.9, 7.6, 1.0), (s * 3.0, 3.6, 0.8)], 0.95, 'bone',
               'leg%d' % s)
        m.sph((s * 2.9, 7.6, 1.0), 1.3, 'bone', 'leg%d' % s)
        m.ell((s * 3.1, 1.8, 1.8), (2.2, 1.8, 3.4), 'hat', 'leg%d' % s)
        m.tube([(s * 3.0, 3.6, 0.8), (s * 3.0, 4.6, 0.8)], 2.2, 'hat', 'leg%d' % s)
        m.paint((s * 3.0, 4.4, 0.8), (2.6, 0.7, 2.6), 'gold', ['leg%d' % s])
    # long tattered coat with gold trim, ragged hem
    frustum(m, (0, 9.0, 0), 7.6, 5.2, 21.0, 12, 'coat', 'coat', phase=15.0)
    m.ell((0, 29.0, 0), (6.4, 3.4, 4.8), 'coat', 'coat')
    rnd = g.Rand(168)
    for k in range(14):
        a = (k * 360.0 / 14 + 8) * DEG
        if math.sin(a) > 0.75:
            continue
        ln = 3.0 + 2.6 * rnd.f() + (2.0 if math.sin(a) < -0.3 else 0.0)
        b = (math.cos(a) * 7.0, 10.0, math.sin(a) * 7.0)
        m.crystal(b, add(b, (math.cos(a) * 1.0, -ln, math.sin(a) * 1.0)), 1.7, 'coat', 'hem',
                  sides=4, tip_frac=0.9)
    m.group('hem', 'coat')
    # open front: ribcage between gold-trimmed lapels
    m.paint((0, 22.0, 5.4), (2.4, 7.4, 1.6), 'bone', ['coat'])
    for y in (18.6, 21.4, 24.2):
        m.paint((0, y, 5.8), (2.6, 0.7, 1.4), 'coat', ['coat'])
    for s in (-1, 1):
        paint_path(m, [(s * 2.8, 29.4, 5.0), (s * 3.0, 20.0, 5.8), (s * 3.6, 11.0, 7.0)],
                   (0.8, 0.8, 1.2), 'gold', ['coat'])
        m.ell((s * 6.2, 30.0, 0.0), (2.6, 1.3, 2.6), 'gold', 'epaulet%d' % s)
    # skull under a tricorn
    hc, hr = (0, 35.4, 1.6), (4.8, 4.6, 4.4)
    m.tube([(0, 30.0, 0.4), (0, 32.6, 0.8)], 1.4, 'bone', 'neck')
    m.ell(hc, hr, 'bone', 'head')
    m.ell((0, 31.6, 2.6), (3.2, 1.8, 3.0), 'bone', 'head')
    for s in (-1, 1):
        p, n = g.on(hc, hr, (s * 0.5, 0.0, 0.86))
        # dark hollow sockets, each with a small glowing pupil
        m.dot(p, n, w=3.2, h=3.4, color='outline', shape='oval', minw=3, minh=3)
        m.eye(add(p, (0, -0.2, 0.1)), n, 1.3, 1.3, style='solid', iris=('glass', 1),
              minw=1, minh=1, center=(0, 34, 12))
    m.dot(g.on(hc, hr, (0, -0.4, 1))[0], (0, 0, 1), w=1.6, h=1.6, minw=2, color='outline')
    m.mouth((0, 31.4, 5.5), (0, -0.1, 1), 'teeth', w=4.4, h=1.6)
    m.ell((0, 40.4, 0.8), (4.4, 2.6, 4.2), 'hat', 'hat')
    corners = [(math.cos(a * DEG) * 7.0, 39.8, math.sin(a * DEG) * 6.2 + 0.4)
               for a in (90, 210, 330)]
    for i in range(3):
        c0, c1 = corners[i], corners[(i + 1) % 3]
        mid = add(mul(lerp(c0, c1, 0.5), 0.55), (0, 4.2, 0.2))
        m.tube([c0, mid, c1], [1.0, 1.5, 1.0], 'hat', 'hat', flat=0.45,
               up=norm((mid[0], 0, mid[2] - 0.4)))
        m.tube([c0, add(mid, (0, 1.4, 0)), c1], [0.4, 0.6, 0.4], 'gold', 'hat')
    m.paint((0, 42.0, 4.4), (1.2, 1.2, 1.2), 'bone', ['hat'])
    # bony arms in coat sleeves, hugging the glowing ship-in-a-bottle
    bt = (0, 20.6, 8.0)
    for s in (-1, 1):
        sh, el, wr = (s * 6.2, 28.0, 0.4), (s * 8.0, 21.0, 3.8), (s * 5.4, 18.4, 8.4)
        m.tube([sh, el], [2.4, 2.2], 'coat', 'arm%d' % s)
        m.tube([el, wr], 1.0, 'bone', 'arm%d' % s)
        m.tube([el, add(el, (0, 0, 0.6))], 2.4, 'gold', 'arm%d' % s)
        for t in (-1, 0, 1):
            f0 = add(wr, (0, t * 1.0, 0.6))
            m.tube([f0, add(f0, (-s * 1.8, t * 0.4, 1.8)), add(f0, (-s * 3.0, t * 0.3, 2.0))],
                   0.55, 'bone', 'arm%d' % s)
    m.ell(bt, (5.6, 3.4, 3.4), 'glass', 'bottle', rot=(0, 0, 18))
    m.tube([(-5.4, 19.0, 8.0), (-7.6, 18.2, 8.0)], [1.6, 1.3], 'glass', 'bottle')
    m.tube([(-7.6, 18.2, 8.0), (-8.8, 17.8, 8.0)], 1.2, 'coat', 'bottle')
    # the tiny ship inside: dark hull, pale sails
    m.paint((0.4, 19.2, 11.2), (3.0, 0.9, 1.0), 'coat', ['bottle'])
    for x, h in ((-0.8, 1.8), (1.4, 2.2)):
        m.paint((x, 21.2, 11.2), (0.9, h * 0.8, 1.0), 'bone', ['bottle'])
    return m


# ==========================================================================
# 169 RUNELITH  RELIC/STONE  walking rune stone
# ==========================================================================
def runelith(g):
    m = g.Model('RUNELITH')
    m.outline = (22, 20, 30)
    m.mat('stone', ['#3a3c4c', '#5c606e', '#868a96', '#b4b6bc'])
    m.mat('rune', ['#f08a10', '#ffd870'], emissive=0.85)
    m.mat('moss', ['#3c6a2a', '#6ea040'])
    m.eye_dark = (22, 20, 30)
    m.white = (255, 216, 112)
    m.height = 56
    m.max_w = 60
    m.front_yaw = -24
    # stubby stone legs
    for s in (-1, 1):
        m.tube([(s * 3.8, 8.0, 0.0), (s * 4.0, 3.0, 0.4)], [2.8, 2.6], 'stone', 'leg%d' % s)
        m.rock((s * 4.1, 1.8, 1.2), (3.2, 1.9, 3.8), 'stone', 'leg%d' % s, seed=3 + s, n=12)
    # the standing stone: a tall bevelled slab with a rough crown
    SC, SH = (0, 24.0, 0), (7.2, 15.0, 3.4)
    m.box(SC, SH, 'stone', 'slab', rot=(0, 0, 3), bevel=1.4)
    m.rock((0.8, 38.6, 0), (6.8, 3.2, 3.4), 'stone', 'slab', seed=9, n=14)
    fz = SH[2] + 0.1
    # glowing runes carved down the face
    glyphs = [[(-2.0, 25.0), (-2.0, 29.0), (0.0, 27.0), (2.0, 29.0), (2.0, 25.0)],
              [(-2.2, 22.4), (2.2, 22.4)],
              [(0.0, 21.4), (0.0, 16.6)], [(-2.0, 19.8), (2.0, 18.0)],
              [(-2.2, 14.4), (0.0, 12.2), (2.2, 14.4)]]
    for gl in glyphs:
        paint_path(m, [(x + 0.1 * (y - 24.0) * -0.05, y, fz) for x, y in gl], (0.8, 0.8, 1.4),
                   'rune', ['slab'])
    for s in (-1, 1):
        paint_path(m, [(s * 7.3, 30.0, 1.0), (s * 7.3, 26.0, -1.0), (s * 7.3, 20.0, 1.0)],
                   (1.4, 0.8, 0.8), 'rune', ['slab'])
    # moss and lichen
    for (x, y, rx, ry) in ((-4.6, 36.4, 3.0, 1.8), (5.0, 12.0, 2.2, 3.0), (3.6, 39.6, 3.4, 1.6),
                           (-5.4, 16.0, 1.6, 2.0)):
        m.paint((x, y, fz), (rx, ry, 1.6), 'moss', ['slab'])
    # rune-eyes under a stone brow
    for s in (-1, 1):
        p = (s * 3.0, 32.4, fz)
        m.dot(p, (0, 0, 1), w=4.0, h=3.2, color='outline', shape='oval', minw=3, minh=3)
        m.eye(p, (0, 0, 1), 3.0, 2.0, style='glow', iris=('rune', 1), slant=0.6,
              center=(0, 32, 14))
    m.box((0, 34.8, fz - 0.2), (6.0, 0.9, 0.8), 'stone', 'brow', bevel=0.3)
    # floating stone fists with rune bands, pebbles trailing to the shoulders
    for s in (-1, 1):
        fc = (s * 13.6, 18.0, 3.0)
        part = 'fist%d' % s
        m.rock(fc, (4.2, 4.0, 3.8), 'stone', part, seed=20 + s, n=16)
        m.paint(add(fc, (0, 1.2, 0)), (4.6, 0.9, 4.4), 'rune', [part])
        for t, r in ((0.35, 1.3), (0.65, 1.0)):
            q = lerp((s * 8.4, 30.0, 0.6), add(fc, (0, 4.4, -1.0)), t)
            m.rock(q, r, 'stone', 'pebble%d' % s, seed=int(30 + t * 10 + s), n=8)
    return m


# ==========================================================================
# 170 FAEFLY  DREAM/SWARM  dragonfly fairy in a petal tutu
# ==========================================================================
def faefly(g):
    m = g.Model('FAEFLY')
    m.outline = (30, 20, 56)
    m.mat('body', ['#1c4a64', '#2c7c96', '#58b8c4'])
    m.mat('petal', ['#b0407e', '#ec74b2', '#ffc2e2'])
    m.mat('wingA', ['#8ed2ec', '#e4f8ff'], emissive=0.3)
    m.mat('wingB', ['#d4a8f0', '#fbeaff'], emissive=0.3)
    m.mat('gem', ['#3a2a8a', '#6a58d4', '#b4a4ff'], spec=0.6)
    m.eye_dark = (30, 20, 56)
    m.white = (255, 255, 255)
    m.height = 54
    m.max_w = 62
    m.front_yaw = -18
    hover(g, m, 4)
    side_yaw(g, m, -56)
    # four long wings: forewings raised, hindwings swept low, tilted back
    root = (0, 27.0, -2.0)
    for s in (-1, 1):
        for nm, ang, ln, wd, mat in (('F', 22, 22.0, 3.8, 'wingA'), ('H', -14, 19.0, 3.6, 'wingB')):
            a = ang * DEG
            u = norm((s * math.cos(a), math.sin(a), -0.32))
            v = norm(cross((0, 0.3, 1), u))
            pts = []
            for k in range(16):
                t = 2 * math.pi * k / 16
                x = (1 + math.cos(t)) * 0.5 * ln
                y = math.sin(t) * wd * (1.0 + 0.25 * math.cos(t))
                pts.append(add(root, add(mul(u, x), mul(v, y))))
            part = 'wing%s%d' % (nm, s)
            m.poly(pts, mat, part, puff=0.3)
            tip = add(root, mul(u, ln * 0.82))
            m.paint(tip, (2.4, 2.4, 2.0), 'petal', [part])
            m.tube([add(root, mul(u, 1.0)), add(root, mul(u, ln * 0.9))], 0.4, 'body', part)
            for t in (0.4, 0.62):
                m.sparkle(add(add(root, mul(u, ln * t)), mul(v, wd * 0.3)), (0, 0.3, 1), size=1)
    # thorax, and a long segmented abdomen curling down under the tutu
    m.ell((0, 26.0, -0.6), (3.6, 4.4, 3.4), 'body', 'body')
    abd = [(0, 21.0, -1.0), (0, 15.0, -1.6), (0, 9.0, -1.0), (0.6, 4.4, 0.8), (1.4, 2.2, 3.0)]
    mats = [(0, 'body')]
    for k in range(6):
        mats += [(0.14 + k * 0.14, 'petal'), (0.19 + k * 0.14, 'body')]
    m.tube(abd, [2.4, 2.0, 1.6, 1.1, 0.8], 'body', 'tail', mats=mats)
    m.sph((1.6, 2.0, 3.6), 1.0, 'gem', 'tail')
    # petal tutu round the waist, two layers
    for layer, (cnt, r0, ln, y, drop, a0) in enumerate(((9, 2.4, 6.4, 21.8, 2.4, 0),
                                                        (9, 2.2, 4.8, 22.6, 1.2, 20))):
        for k in range(cnt):
            a = (360.0 * k / cnt + a0) * DEG
            d = (math.cos(a), 0, math.sin(a))
            b = add((0, y, -0.6), mul(d, r0))
            tip = add(b, add(mul(d, ln), (0, -drop, 0)))
            g.leaf(m, b, add(lerp(b, tip, 0.5), (0, 0.6, 0)), tip, 2.4 - 0.3 * layer, 'petal',
                   'tutu', up=(0, 1, 0), flat=0.3)
    # tiny legs tucked in front
    for s in (-1, 1):
        for k in range(2):
            b = (s * 1.6, 24.0 - k * 1.6, 1.8)
            m.tube([b, add(b, (s * 1.6, -1.2, 1.6)), add(b, (s * 1.8, -3.0, 1.8))], 0.45, 'body',
                   'legs')
    # head: big faceted gem eyes, feelers, a small smile
    hc, hr = (0, 33.0, 0.6), (3.8, 3.4, 3.4)
    m.ell(hc, hr, 'body', 'head')
    for s in (-1, 1):
        ec = (s * 2.8, 34.0, 1.6)
        m.sph(ec, 2.6, 'gem', 'head')
        p, n = g.on(ec, (2.6, 2.6, 2.6), (s * 0.3, 0.1, 1))
        m.eye(p, n, 3.0, 3.4, style='cute', minw=3, minh=3)
        m.tube([(s * 1.2, 36.0, 1.6), (s * 2.4, 39.4, 2.0), (s * 4.0, 41.4, 1.0)], [0.45, 0.35, 0.3],
               'body', 'feeler%d' % s)
        m.sph((s * 4.2, 41.6, 0.9), 0.9, 'petal', 'feeler%d' % s)
    p, n = g.on(hc, hr, (0, -0.4, 1))
    m.mouth(p, n, 'smile', w=2.0)
    return m


# ==========================================================================
# 171 SNOWBRUTE  FROST/BRAWL  yeti boxer with ice gauntlets
# ==========================================================================
def snowbrute(g):
    m = g.Model('SNOWBRUTE')
    m.outline = (26, 22, 48)
    m.mat('fur', ['#585c8c', '#8a92c0', '#c2cae8', '#f2f4ff'], th=[0.3, 0.55, 0.82])
    m.mat('shag', ['#585c8c', '#8a92c0', '#c2cae8'])   # same ramp minus white: strand contrast
    m.mat('skin', ['#1a1e36', '#343c60'])
    m.mat('ice', ['#1462c0', '#3aaef0', '#b8f2ff'], emissive=0.35, spec=0.6)
    m.mat('wrap', ['#9a1e2c', '#e04448'])
    m.eye_dark = (26, 22, 48)
    m.white = (255, 255, 255)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -24
    rnd = g.Rand(171)

    def tuft(p, n, ln, part, r=0.95, k=3):
        """A tuft of long hanging fur strands rooted at p (surface normal n)."""
        side = norm(cross(n, (0, 1, 0.01)))
        for j in range(k):
            o = (j - (k - 1) / 2.0) * r * 1.4
            b = add(p, add(mul(side, o), mul(n, -0.4)))
            ll = ln * (0.8 + 0.4 * rnd.f())
            tip = add(b, add(mul(n, ll * 0.45), add(mul(side, o * 0.5), (0, -ll, 0))))
            m.crystal(b, tip, r, 'shag' if j % 2 else 'fur', part, sides=4, tip_frac=1.0)

    def shag(c, r, dirs, ln, part, **kw):
        for d in dirs:
            p, n = g.on(c, r, d)
            tuft(p, n, ln, part, **kw)
    # short bowed legs planted wide, dark padded feet
    for s in (-1, 1):
        part = 'leg%d' % s
        m.tube([(s * 5.0, 14.0, -0.6), (s * 7.2, 8.0, 0.4), (s * 7.6, 3.2, 1.0)],
               [4.4, 3.8, 3.2], 'fur', part)
        m.ell((s * 7.8, 1.8, 2.6), (3.4, 1.8, 4.2), 'skin', part)
        shag((s * 7.0, 8.4, 0.4), (3.8, 4.0, 3.8), [(s * 0.9, 0.1, 0.4), (s * 0.3, 0.1, 1.0),
                                                    (s * 1.0, 0.1, -0.4)], 4.6, part)
    # barrel torso and massive hunched shoulders
    bc, br = (0, 21.0, -0.6), (8.6, 9.0, 7.0)
    m.ell(bc, br, 'fur', 'body')
    for s in (-1, 1):
        m.ell((s * 8.4, 28.6, -1.0), (5.6, 4.8, 5.4), 'fur', 'body')
    # long shaggy fur hanging in strands off the flanks, belly and shoulders
    shag(bc, br, [(math.cos(a * DEG), 0.1, math.sin(a * DEG)) for a in range(-170, 181, 34)],
         6.4, 'body')
    shag(bc, br, [(-0.4, -0.3, 0.9), (0.4, -0.3, 0.9), (0, -0.35, 1)], 5.0, 'body', k=2)
    for s in (-1, 1):
        shag((s * 8.4, 28.6, -1.0), (5.6, 4.8, 5.4),
             [(s * 0.9, 0.3, 0.3), (s * 0.95, 0.1, -0.4), (s * 0.4, 0.6, -0.6)], 5.6, 'body')
    # head sunk low between the shoulders, a swept-back fur crest
    hc, hr = (0, 33.0, 3.6), (6.2, 5.6, 5.4)
    m.ell(hc, hr, 'fur', 'head')
    for d in ((0, 1, 0.2), (0.6, 0.8, 0.0), (-0.6, 0.8, 0.0)):
        p, n = g.on(hc, hr, d)
        m.crystal(add(p, mul(n, -0.5)), add(p, (d[0] * 2.0, 2.0, -3.4)), 1.1, 'fur', 'crown',
                  sides=4, tip_frac=1.0)
    for s in (-1, 1):
        p, n = g.on(hc, hr, (s * 0.95, -0.2, 0.3))
        tuft(p, n, 4.6, 'head', k=2)
    # shaggy bangs hanging over the forehead
    for x, ln in ((-3.6, 2.6), (-1.4, 3.0), (1.2, 2.8), (3.4, 2.4)):
        b = (x, 37.8, 7.0)
        m.crystal(b, (x * 1.15, 37.8 - ln, 10.4), 1.3, 'fur', 'bangs', sides=4, tip_frac=1.0)
    # big dark face with a heavy angry brow ridge
    fc, fr = (0, 32.0, 7.0), (5.8, 4.6, 2.8)
    m.ell(fc, fr, 'skin', 'face')
    m.ell((0, 29.4, 8.4), (3.6, 2.0, 2.2), 'skin', 'face')
    m.tube([(-5.8, 36.0, 7.2), (-2.2, 34.6, 9.4), (0, 34.0, 9.8), (2.2, 34.6, 9.4),
            (5.8, 36.0, 7.2)], [1.2, 1.2, 1.1, 1.2, 1.2], 'skin', 'brow')
    # glowing eyes under the brow
    for s in (-1, 1):
        p, n = g.on(fc, fr, (s * 0.72, 0.2, 0.64))
        m.eye(p, n, 1.9, 2.0, style='glow', iris=('ice', 2), slant=0.8, minw=2, minh=3,
              center=(0, 32, 16))
    # snarling mouth, lower fangs jutting up
    p, n = g.on((0, 29.4, 8.4), (3.6, 2.0, 2.2), (0, 0.1, 1))
    m.mouth(p, n, 'open', w=4.6, h=2.2, color='outline', inner=('wrap', 0), minw=4)
    for s in (-1, 1):
        m.dot(add(p, (s * 1.3, 0.3, 0.2)), n, w=0.8, h=1.6, color='white', minw=1, minh=2)
    # arms up in a boxer's guard, glowing ice gauntlets either side of the chin
    for s, el, fist in ((1, (12.6, 19.6, 2.4), (9.4, 24.6, 10.0)),
                        (-1, (-13.0, 21.0, 3.0), (-10.2, 28.0, 9.0))):
        sh = (s * 9.8, 28.0, -0.8)
        part = 'arm%d' % s
        m.tube([sh, el, fist], [4.2, 3.6, 3.0], 'fur', part)
        # fur strands hanging from the forearm and elbow
        for t in (0.3, 0.65):
            q = lerp(el, fist, t)
            tuft(add(q, (s * 1.6, -2.0, -0.8)), norm((s * 0.7, -0.6, -0.2)), 4.4, part, k=2)
        tuft(add(el, (s * 1.4, -2.6, -1.0)), norm((s * 0.6, -0.7, -0.4)), 5.0, part, k=3)
        fp = 'fist%d' % s
        fd = norm(sub(fist, el))
        fc2 = add(fist, mul(fd, 1.6))
        m.ell(fc2, (3.8, 3.8, 3.6), 'ice', fp)
        m.tube([lerp(el, fist, 0.72), lerp(el, fist, 0.92)], 3.4, 'wrap', fp)
        # frost spikes on the knuckles and cuff
        for k in range(3):
            q = add(fc2, (s * (k - 1) * 0.9, 1.4 - k * 1.3, 2.6))
            m.crystal(q, add(q, add(mul(fd, 1.0), (0, 0.4, 2.2))), 0.8, 'ice', fp, sides=4,
                      tip_frac=0.9)
        b = add(fc2, (s * 2.6, 2.2, -0.6))
        m.crystal(b, add(b, (s * 2.2, 2.8, -0.6)), 1.0, 'ice', fp, sides=4, tip_frac=0.9)
    return m


# ==========================================================================
# 172 TESLAROSE  BLOOM/SPARK  rose with copper-coil vines
# ==========================================================================
def teslarose(g):
    m = g.Model('TESLAROSE')
    m.outline = (34, 10, 20)
    m.mat('rose', ['#5a0a1c', '#9c1430', '#dc3446', '#ff8088'])
    m.mat('stem', ['#1a4220', '#347a2e', '#72b448'])
    m.mat('copper', ['#7a3a14', '#c46a28', '#f4ac64'], spec=0.5)
    m.mat('spark', ['#2c7cff', '#d4f4ff'], emissive=0.7)
    m.eye_dark = (34, 10, 20)
    m.white = (212, 244, 255)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -20
    # root feet under a skirt of leaves
    for s, a in ((-1, 125), (1, 55), (0, 270)):
        d = (math.cos(a * DEG), 0, math.sin(a * DEG))
        part = 'leg%d' % s if s else 'roots'
        m.tube([(d[0] * 1.2, 5.0, d[2] * 1.2), (d[0] * 4.2, 2.2, d[2] * 4.2),
                (d[0] * 6.6, 0.9, d[2] * 6.6)], [2.4, 1.8, 0.8], 'stem', part)
    for k in range(7):
        a = (k * 360.0 / 7 + 13) * DEG
        d = (math.cos(a), 0, math.sin(a))
        b = add((0, 9.0, 0), mul(d, 2.0))
        g.leaf(m, b, add(b, add(mul(d, 4.0), (0, -1.0, 0))), add(b, add(mul(d, 7.4), (0, -4.6, 0))),
               2.8, 'stem', 'skirt', up=(0, 1, 0), flat=0.32)
    # thorny stem body
    stem = [(0, 4.0, 0), (0.5, 10.0, 0.3), (-0.3, 17.0, 0.3), (0, 24.0, 0.8)]
    m.tube(stem, [3.0, 3.0, 2.7, 2.5], 'stem', 'body')
    for y, a in ((12.0, 30), (14.6, 160), (17.4, 280), (20.0, 60), (22.4, 200)):
        d = (math.cos(a * DEG), 0.35, math.sin(a * DEG))
        b = (d[0] * 2.2, y, d[2] * 2.2 + 0.3)
        m.crystal(b, add(b, mul(norm(d), 3.0)), 1.0, 'rose', 'thorns', sides=4, tip_frac=1.0)
    # copper-coil vine arms ending in spark terminals with crackling blue arcs
    for s in (-1, 1):
        sh = (s * 2.0, 19.6, 0.6)
        el = (s * 8.0, 19.4, 2.6)
        tip = (s * 12.8, 25.0, 3.4)
        part = 'arm%d' % s
        m.tube([sh, el, tip], [1.3, 1.1, 0.9], 'stem', part)
        pts = []
        N = 40
        for i in range(N + 1):
            t = i / float(N)
            c = lerp(sh, el, t * 2) if t < 0.5 else lerp(el, tip, t * 2 - 1)
            a = t * 5 * 2 * math.pi
            pts.append(add(c, (0, math.cos(a) * 1.8, math.sin(a) * 1.8)))
        m.tube(pts, 0.65, 'copper', part)
        m.sph(tip, 1.7, 'copper', part)
        m.sph(add(tip, (s * 0.5, 1.3, 0.5)), 1.4, 'spark', part)
        g.zigzag(m, [add(tip, (s * 0.6, 1.8, 0.6)), add(tip, (s * 2.8, 3.4, 1.0)),
                     add(tip, (s * 1.4, 5.4, 1.4)), add(tip, (s * 3.8, 7.6, 1.6))],
                 [0.8, 0.7, 0.6, 0.3], 'spark', 'arc%d' % s, flat=0.6, up=(0, 0, 1))
        g.zigzag(m, [add(tip, (s * 1.0, -0.4, 0.6)), add(tip, (s * 3.4, -1.2, 1.0)),
                     add(tip, (s * 3.0, -3.4, 1.2)), add(tip, (s * 5.2, -4.4, 1.2))],
                 [0.7, 0.6, 0.55, 0.3], 'spark', 'arc%d' % s, flat=0.6, up=(0, 0, 1))
    # round green hip under the bloom: the face
    hc, hr = (0, 27.4, 2.2), (5.2, 4.6, 4.4)
    m.ell(hc, hr, 'stem', 'head')
    for s in (-1, 1):
        p, n = g.on(hc, hr, (s * 0.54, 0.0, 0.84))
        m.dot(p, n, w=3.2, h=3.2, color='outline', shape='oval', minw=3, minh=3)
        m.eye(p, n, 2.4, 2.6, style='glow', iris=('spark', 1), minw=2, minh=2,
              center=(0, 28, 14))
    p, n = g.on(hc, hr, (0, -0.46, 0.88))
    m.mouth(p, n, 'open', w=3.2, h=2.0, inner=('rose', 1), minw=3)
    # sepals flaring out behind the face
    for k in range(5):
        a = (200 + k * 35) * DEG
        d = (math.cos(a), 0, math.sin(a))
        b = add((0, 31.0, 1.0), mul(d, 3.0))
        g.leaf(m, b, add(b, add(mul(d, 3.4), (0, 0.4, 0))), add(b, add(mul(d, 6.2), (0, -1.6, 0))),
               1.7, 'stem', 'sepal', up=(0, 1, 0), flat=0.35)
    # the rose bloom, tipped toward the viewer: rings of cupped petals
    # spiralling in to a tight bud
    base = (0, 32.6, 0.0)
    A = norm((0, 1, 0.36))
    U = (1.0, 0.0, 0.0)
    W = norm(cross(U, A))
    for ring, (cnt, R, h, wd, ht, th, tilt, ph) in enumerate((
            (6, 5.4, 1.2, 3.8, 4.2, 1.0, 55, 0),
            (5, 4.2, 2.6, 3.4, 4.2, 0.9, 38, 34),
            (4, 2.8, 3.8, 2.8, 3.6, 0.8, 20, 70),
            (3, 1.4, 4.8, 2.2, 3.0, 0.7, 8, 15))):
        for k in range(cnt):
            a = (k * 360.0 / cnt + ph) * DEG
            r = add(mul(U, math.cos(a)), mul(W, math.sin(a)))
            t = add(mul(U, -math.sin(a)), mul(W, math.cos(a)))
            q = norm(add(mul(A, math.cos(tilt * DEG)), mul(r, math.sin(tilt * DEG))))
            nn = norm(cross(t, q))
            c = add(base, add(mul(r, R), mul(A, h)))
            m.ell_axes(c, (mul(t, wd), mul(q, ht), mul(nn, th)), 'rose', 'bloom%d' % ring)
    sp = [add(base, add(mul(A, 7.4 - tt * 0.08),
                        add(mul(U, math.cos(tt) * (0.3 + tt * 0.2)),
                            mul(W, math.sin(tt) * (0.3 + tt * 0.2))))) for tt in
          [i * 0.45 for i in range(16)]]
    m.tube(sp, 0.5, 'rose', 'bud')
    m.ell(add(base, mul(A, 6.2)), (1.8, 1.8, 1.8), 'rose', 'bud')
    for ring in range(4):
        m.group('bloom%d' % ring)
    return m


# ==========================================================================
# 173 NOCTMARE  DUSK/DREAM  night mare with a starry smoke mane
# ==========================================================================
def noctmare(g):
    m = g.Model('NOCTMARE')
    m.outline = (8, 6, 16)
    m.mat('coat', ['#12101e', '#242034', '#3c3654', '#5e5478'])
    m.mat('smoke', ['#4a2a8a', '#7a4ec8', '#b490f4'], emissive=0.4)
    m.mat('flame', ['#a8b8ff', '#eef2ff'], emissive=0.8)
    m.eye_dark = (8, 6, 16)
    m.white = (238, 242, 255)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -50
    # body and long legs ending in pale-flame hooves
    m.ell((0, 21.0, -1.0), (5.6, 6.2, 12.4), 'coat', 'body')
    m.ell((0, 22.0, 8.0), (5.8, 6.6, 5.6), 'coat', 'body')
    for s in (-1, 1):
        for nm, z0, zf in (('legF', 8.6, 10.0), ('legB', -9.4, -10.4)):
            part = '%s%d' % (nm, s)
            if nm == 'legB':
                m.ell((s * 3.8, 20.0, z0), (3.2, 5.6, 5.0), 'coat', part)
            m.tube([(s * 3.4, 17.0, z0), (s * 3.6, 10.0, zf + (1.0 if nm == 'legF' else -1.4)),
                    (s * 3.6, 4.2, zf)], [2.6, 1.7, 1.5], 'coat', part)
            m.ell((s * 3.6, 2.8, zf), (1.9, 1.6, 2.0), 'coat', part)
            g.flame(m, (s * 3.6, 0.4, zf + 0.2), 6.4, 2.8, part, mats=('flame', 'smoke', 'flame'),
                    up=(0, 1, -0.2), tongues=2, seed=3 + s + int(z0))
    # neck arching up, long head
    m.tube([(0, 24.0, 9.0), (0, 30.0, 12.0), (0, 34.4, 13.0)], [4.6, 3.6, 3.0], 'coat', 'neck')
    hc, hr = (0, 36.0, 13.6), (3.2, 3.4, 3.6)
    m.ell(hc, hr, 'coat', 'head')
    m.tube([(0, 35.4, 15.4), (0, 33.2, 19.0), (0, 31.6, 21.0)], [2.8, 2.3, 2.1], 'coat', 'head')
    m.dot((0, 31.8, 23.0), (0, 0.1, 1), w=2.2, h=1.0, minw=2, color=('coat', 3))
    for s in (-1, 1):
        m.crystal((s * 1.8, 38.6, 12.8), (s * 2.4, 42.4, 11.4), 1.1, 'coat', 'ear%d' % s,
                  sides=4, tip_frac=0.8)
        p, n = g.on(hc, hr, (s * 0.72, 0.1, 0.62))
        m.dot(p, n, w=3.4, h=2.8, color='outline', shape='oval', minw=3, minh=3)
        m.eye(p, n, 2.8, 2.0, style='glow', iris=('flame', 1), slant=0.5, minh=3,
              center=(0, 36, 26))
    # a violet smoke mane full of stars, from forelock down the neck
    rnd = g.Rand(173)
    mane = [(0, 40.0, 13.0), (0, 38.0, 10.0), (0, 34.0, 8.6), (0, 30.0, 6.4), (0, 26.4, 4.2),
            (0, 23.0, 2.6)]
    for k, q in enumerate(mane):
        r = 3.4 + 0.6 * math.sin(k * 1.3)
        for j in range(2):
            c = add(q, (0.0 if j == 0 else (1.4 if k % 2 else -1.4), 1.2 * j,
                        -1.6 - 2.4 * j - 0.4 * k))
            m.sph(c, r - 0.8 * j, 'smoke', 'mane')
        m.sparkle(add(q, (2.4, 0.6 + 0.8 * (k % 2), -2.2)), (0.8, 0.3, 0.4), size=1)
    m.sph((0, 40.8, 15.0), 2.0, 'smoke', 'mane')
    # smoke tail with stars
    tail = [(0, 23.6, -13.0), (0, 22.0, -18.0), (0, 17.0, -21.4), (0, 11.0, -22.0)]
    for k, q in enumerate(tail):
        m.sph(q, 3.0 + 0.6 * (k % 2), 'smoke', 'tail')
        m.sph(add(q, (0.8, -1.6, -1.8)), 2.4, 'smoke', 'tail')
    for q in tail[1:]:
        m.sparkle(add(q, (3.0, 0.6, 0)), (1, 0.2, 0.2), size=1)
    return m
