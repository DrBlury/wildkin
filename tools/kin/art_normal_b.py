"""Art for kin 67-100 (owner: KIN-B).

One model function per species, called by tools/gen_monsters.py as
fn(g) with g = the gen_monsters module (g.Model, g.eye_pair, g.on, ...).
Coordinates: +Y up, +Z the way the kin faces, +X its left; the ground is
y = 0. Sizes are in model units; the renderer scales to m.height pixels.
"""

import math

DEG = math.pi / 180.0

# Shared ramps (hue-shifted: shadows lean violet/cool, lights lean warm).
BONE = ['#5e4c58', '#a0907e', '#d8ccb2', '#f8f2e0']
BONE3 = ['#8c7e72', '#d6caae', '#f8f2de']
BONE2 = ['#b0a48e', '#f2ecd6']
DUST = ['#261c2e', '#3e3248', '#5c4c66']
EMBER = ['#ff7a1c', '#ffc43a', '#fff4b8']
PEAT = ['#2a2220', '#473828', '#6a5836', '#8e7e4c']
SWAMP_GLOW = ['#a8d838', '#eeff9c']
CRAB = ['#1c3458', '#2c5e86', '#4894b2', '#8ccad8']
CORAL = ['#c8503c', '#f4906a']


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
        g.OW_FLOAT[m.name] = lift
    if side is not None:
        g.OW_SIDE_YAW[m.name] = side


def beads(g, m, pts, r0, r1, mat, part, n=5, depth=0.30):
    """A string of vertebrae: a tube whose radius pulses n times."""
    m.tube(pts, None, mat, part,
           rfn=lambda t: (r0 + (r1 - r0) * t) * (1 - depth + depth * abs(math.cos(t * math.pi * n))))


def bone(g, m, a, b, r, mat, part, knob=1.25):
    """A cartoon bone from a to b: a shaft with a double knob at each end."""
    m.tube([a, b], [r, r], mat, part)
    d = g.norm(g.sub(b, a))
    side = g.norm(g.cross(d, (0, 0, 1) if abs(d[2]) < 0.8 else (0, 1, 0)))
    for p in (a, b):
        for s in (-1, 1):
            m.sph(g.add(p, g.mul(side, s * r * 0.8)), r * knob * 0.78, mat, part)


def ring(g, m, c, axis, rad, r, mat, part, n=12, skip=()):
    """A torus-like ring of beads around c in the plane normal to axis."""
    ax = g.norm(axis)
    u = g.norm(g.cross(ax, (0, 0, 1) if abs(ax[2]) < 0.9 else (1, 0, 0)))
    v = g.cross(ax, u)
    for k in range(n):
        if k in skip:
            continue
        a = 2 * math.pi * k / n
        m.sph(g.add(c, g.add(g.mul(u, math.cos(a) * rad), g.mul(v, math.sin(a) * rad))), r, mat, part)


def sockets(g, m, c, r, az, el, size, mat, part):
    """Dark eye sockets painted on an ellipsoid head at +-az, el."""
    for s in (-1, 1):
        p, n = g.on(c, r, sdir(az * s, el))
        m.paint(p, size, mat, [part])


def rib_pair(g, m, x0, y0, z, w, h, r, mat, part, drop=0.5):
    """One pair of ribs hanging from the spine at (0, y0, z)."""
    for s in (-1, 1):
        pts = [(s * x0, y0, z), (s * w * 0.85, y0 - h * 0.12, z), (s * w, y0 - h * 0.5, z - drop * 0.4),
               (s * w * 0.78, y0 - h * 0.85, z - drop * 0.8), (s * w * 0.28, y0 - h, z - drop)]
        m.tube(pts, [r, r, r * 0.95, r * 0.9, r * 0.75], mat, part)


def yrot(p, pivot, ang):
    """Rotate point p about a vertical axis through pivot (yaw>0: +Z toward +X)."""
    a = ang * DEG
    x, y, z = p[0] - pivot[0], p[1] - pivot[1], p[2] - pivot[2]
    return (pivot[0] + x * math.cos(a) + z * math.sin(a), p[1], pivot[2] - x * math.sin(a) + z * math.cos(a))


def ribcage(g, m, c, r, n, mat, dark, part, gap=0.5, kernel=None, top=0.75, span=0.66):
    """A ribcage that reads from any angle: a barrel of bone with n-1 dark
    rib gaps painted round its sides (not across the spine on top), and
    optionally a kernel glowing through the middle gap on both sides."""
    m.ell(c, r, mat, part)
    z0, z1 = c[2] + r[2] * span, c[2] - r[2] * span
    for k in range(n - 1):
        z = z0 + (z1 - z0) * (k + 0.5) / (n - 1)
        m.paint((c[0], c[1] - r[1] * 0.1, z), (r[0] * 3.0, r[1] * top, gap), dark, [part])
    if kernel:
        zk = z0 + (z1 - z0) * (((n - 1) // 2) + 0.5) / (n - 1)
        for s in (-1, 1):
            m.paint((c[0] + s * r[0], c[1] - r[1] * 0.15, zk), (r[0] * 0.3, r[1] * 0.28, gap * 1.1), kernel, [part])


def claw(g, m, root, elbow, palm, pr, size, part, crab='crab', tip='coral', gape=1.0):
    """Crab claw: arm root->elbow->palm, a swollen palm and a two-finger pincer
    pointing roughly +Z."""
    m.tube([root, elbow, palm], [0.9 * size, 0.8 * size, 0.9 * size], crab, part)
    m.ell(palm, pr, crab, part, rot=(0, 0, 0))
    f0 = g.add(palm, (0, pr[1] * 0.35, pr[2] * 0.8))
    m.tube([f0, g.add(f0, (0, 0.5 * size * gape, 1.6 * size)), g.add(f0, (0, 0.2 * size, 2.9 * size))],
           [1.25 * size, 0.95 * size, 0.3 * size], tip, part)
    f1 = g.add(palm, (0, -pr[1] * 0.45, pr[2] * 0.75))
    m.tube([f1, g.add(f1, (0, -0.4 * size * gape, 1.3 * size)), g.add(f1, (0, 0.2 * size, 2.3 * size))],
           [1.0 * size, 0.75 * size, 0.25 * size], tip, part)


# ==========================================================================
# HOLLOW
# ==========================================================================
def calcipup(g):
    m = g.Model('CALCIPUP')
    m.outline = (44, 30, 42)
    m.mat('bone', BONE)
    m.mat('dust', DUST)
    m.mat('gap', DUST[:1])
    m.mat('ember', EMBER, emissive=0.85)
    m.mat('collar', ['#8e2a36', '#d8504a'])
    m.eye_dark = rgb(DUST[0])
    m.height = 30
    m.front_yaw = -50
    # ribcage: a bone barrel with dark gaps between the ribs (grave dust
    # inside), the kernel glowing through one gap; a thin waist to the hips
    ribcage(g, m, (0, 9.8, 0.6), (4.0, 3.7, 4.6), 4, 'bone', 'gap', 'ribs', gap=0.62, kernel='ember',
            span=0.92)
    beads(g, m, [(0, 12.4, 1.0), (0, 12.2, -3.4), (0, 11.6, -5.8)], 1.3, 1.15, 'bone', 'ribs', n=4)
    m.ell((0, 10.2, -3.6), (2.0, 2.0, 2.0), 'dust', 'ribs')
    m.ell((0, 11.0, -5.8), (3.0, 2.0, 2.2), 'bone', 'ribs')
    # legs
    for s in (-1, 1):
        lf = 'legF%d' % s
        m.ell((s * 3.1, 11.2, 3.3), (1.0, 2.3, 1.8), 'bone', lf)
        m.tube([(s * 3.3, 10.2, 3.4), (s * 3.5, 6.0, 3.8)], [1.05, 1.0], 'bone', lf)
        m.sph((s * 3.5, 6.0, 3.8), 1.35, 'bone', lf)
        m.tube([(s * 3.5, 6.0, 3.8), (s * 3.5, 2.0, 4.0)], [1.0, 0.95], 'bone', lf)
        m.ell((s * 3.5, 1.1, 5.0), (1.7, 1.1, 2.2), 'bone', lf)
        lb = 'legB%d' % s
        m.tube([(s * 3.0, 11.0, -5.4), (s * 3.4, 7.0, -3.8)], [1.2, 1.05], 'bone', lb)
        m.sph((s * 3.4, 7.0, -3.8), 1.3, 'bone', lb)
        m.tube([(s * 3.4, 7.0, -3.8), (s * 3.4, 3.8, -6.4)], [1.0, 0.95], 'bone', lb)
        m.sph((s * 3.4, 3.8, -6.4), 1.05, 'bone', lb)
        m.tube([(s * 3.4, 3.8, -6.4), (s * 3.4, 1.4, -5.6)], [0.95, 0.9], 'bone', lb)
        m.ell((s * 3.4, 1.0, -4.8), (1.6, 1.0, 2.0), 'bone', lb)
    # wagging bone tail with a tuft of grave dust
    beads(g, m, [(0, 12.6, -7.0), (0.6, 14.8, -9.4), (1.8, 17.4, -10.2), (3.0, 19.6, -9.6)], 1.15, 0.75,
          'bone', 'tail', n=5)
    for d in ((0.3, 1, 0.2), (0.9, 0.7, 0.1), (-0.2, 0.8, -0.5), (0.6, 0.6, -0.6)):
        dd = g.norm(d)
        m.tube([(3.1, 20.0, -9.5), g.add((3.1, 20.0, -9.5), g.mul(dd, 2.6))], [1.1, 0.25], 'dust', 'tail')
    # neck + collar with a little bone tag
    beads(g, m, [(0, 12.8, 4.4), (0, 14.8, 6.4)], 1.5, 1.4, 'bone', 'neck', n=2)
    ring(g, m, (0, 14.0, 5.8), (0, 0.8, 0.6), 2.2, 0.75, 'collar', 'collar', n=14)
    bone(g, m, (-0.9, 12.1, 7.6), (0.9, 12.1, 7.6), 0.45, 'bone', 'collar')
    # skull: round puppy cranium, short muzzle, hinged jaw; the head turns
    # toward the viewer while the body stands side-on
    T, pv = 34, (0, 15.0, 6.0)

    def H(p):
        return yrot(p, pv, T)
    rot = (T, 0, 0)
    head_c, head_r = H((0, 17.8, 7.0)), (5.7, 5.1, 5.3)
    m.ell(head_c, head_r, 'bone', 'head', rot=rot)
    mz_c, mz_r = H((0, 15.8, 11.6)), (2.8, 2.1, 3.0)
    m.ell(mz_c, mz_r, 'bone', 'head', rot=rot)
    m.ell(H((0, 14.0, 10.4)), (2.2, 1.0, 2.6), 'bone', 'jaw', rot=rot)
    m.ell(H((0, 16.9, 14.3)), (1.1, 0.75, 0.7), 'dust', 'head', rot=rot)
    for s in (-1, 1):
        p, n = g.on(head_c, head_r, sdir(30 * s + T, 8), rot)
        m.paint(p, (2.1, 2.3, 1.6), 'dust', ['head'], rot=rot)
    # floppy grave-dust ears and a tuft
    for s in (-1, 1):
        m.tube([H((s * 3.6, 21.4, 4.8)), H((s * 5.6, 21.0, 3.8)), H((s * 6.6, 18.6, 3.2)), H((s * 6.4, 16.4, 3.0))],
               [1.5, 1.8, 1.5, 0.8], 'dust', 'ear%d' % s, flat=0.45, up=yrot((s, 0.1, 0.2), (0, 0, 0), T))
    for d in ((0, 1, 0.3), (0.5, 0.9, -0.1), (-0.5, 0.9, 0.0)):
        dd = g.norm(yrot(d, (0, 0, 0), T))
        b = H((0, 21.6, 6.6))
        m.tube([b, g.add(b, g.mul(dd, 2.8))], [1.0, 0.2], 'dust', 'head')
    g.eye_pair(m, head_c, head_r, 30, 8, 2.8, 3.2, style='glow', iris=('ember', 1), pupil='eye',
               center=H((0, 16, 13)), rot=rot, turn=T)
    p, n = g.on(mz_c, mz_r, yrot((0, -0.55, 1), (0, 0, 0), T), rot)
    m.mouth(p, n, 'smile', w=2.6, fang=1)
    return m


def ossihound(g):
    m = g.Model('OSSIHOUND')
    m.outline = (40, 26, 38)
    m.mat('bone', BONE)
    m.mat('dust', DUST)
    m.mat('gap', DUST[:1])
    m.mat('ember', EMBER, emissive=0.85)
    m.mat('flame', EMBER[:2], emissive=0.3)
    m.eye_dark = rgb(DUST[0])
    m.height = 50
    m.max_w = 60
    m.front_yaw = -50
    # deep ribcage, a lean dark waist, the hips
    ribcage(g, m, (0, 18.2, 2.0), (4.8, 5.4, 6.4), 5, 'bone', 'gap', 'ribs', gap=0.8, kernel='ember',
            span=0.92)
    beads(g, m, [(0, 22.6, 2.0), (0, 22.4, -5.0), (0, 21.4, -9.8)], 1.6, 1.4, 'bone', 'ribs', n=5)
    m.ell((0, 19.2, -6.2), (2.4, 2.4, 3.2), 'dust', 'ribs')
    m.ell((0, 20.6, -10.0), (3.8, 2.6, 2.8), 'bone', 'ribs')
    # bony dorsal spikes
    for k, (z, ln) in enumerate(((4.5, 4.4), (1.6, 4.0), (-1.4, 3.6), (-4.4, 3.2), (-7.2, 2.6))):
        y = 23.0 - 0.02 * z * z
        m.crystal((0, y, z), (0, y + ln, z - ln * 0.6), 0.9, 'bone', 'spike', sides=4, tip_frac=0.8, twist=45)
    # legs: bone with dark sinew
    for s in (-1, 1):
        lf = 'legF%d' % s
        m.ell((s * 4.6, 19.4, 6.0), (1.2, 2.6, 1.8), 'bone', lf, rot=(0, -10, 0))
        m.tube([(s * 4.5, 18.5, 6.0), (s * 4.8, 11.5, 7.0)], [1.4, 1.25], 'bone', lf)
        m.sph((s * 4.8, 11.5, 7.0), 1.8, 'bone', lf)
        m.tube([(s * 4.8, 11.5, 7.0), (s * 4.8, 3.2, 7.4)], [1.35, 1.25], 'bone', lf)
        m.ell((s * 4.8, 1.4, 8.8), (2.2, 1.4, 2.8), 'bone', lf)
        for t in (-1, 0, 1):
            m.crystal((s * 4.8 + t * 1.2, 1.2, 10.6), (s * 4.8 + t * 1.5, 0.4, 12.2), 0.55, 'bone', lf,
                      sides=4, tip_frac=0.8)
        lb = 'legB%d' % s
        m.ell((s * 3.6, 19.4, -10.2), (1.8, 2.4, 3.0), 'bone', lb)
        m.tube([(s * 4.2, 18.5, -10.0), (s * 4.6, 12.0, -7.4)], [1.45, 1.3], 'bone', lb)
        m.sph((s * 4.6, 12.0, -7.4), 1.75, 'bone', lb)
        m.tube([(s * 4.6, 12.0, -7.4), (s * 4.6, 6.0, -11.4)], [1.35, 1.25], 'bone', lb)
        m.sph((s * 4.6, 6.0, -11.4), 1.4, 'bone', lb)
        m.tube([(s * 4.6, 6.0, -11.4), (s * 4.6, 1.6, -10.0)], [1.25, 1.2], 'bone', lb)
        m.ell((s * 4.6, 1.3, -8.6), (2.1, 1.3, 2.6), 'bone', lb)
    # tail arching back to an ember tip
    beads(g, m, [(0, 21.6, -12.0), (0.8, 23.4, -16.0), (2.4, 26.8, -18.4), (4.2, 29.6, -18.4)], 1.4, 0.8,
          'bone', 'tail', n=6)
    g.flame(m, (4.4, 29.4, -18.3), 9.0, 3.2, 'tail', mats=('flame', 'ember', 'ember'), up=(0.2, 1, 0.1),
            tongues=2, core=False, seed=8)
    # neck and a ragged grave-dust ruff
    beads(g, m, [(0, 22.6, 7.2), (0, 25.8, 10.0), (0, 27.8, 11.8)], 2.0, 1.8, 'bone', 'neck', n=3)
    rnd = g.Rand(85)
    for k in range(7):
        a = (-100 + 200.0 * k / 6) * DEG
        b = (math.sin(a) * 3.0, 26.0 + math.cos(a) * 1.6, 9.4 - abs(math.sin(a)) * 1.6)
        d = g.norm((math.sin(a) * 0.8, -0.3 + 0.3 * math.cos(a), -1.0))
        ln = 3.2 + 1.6 * rnd.f()
        m.tube([b, g.add(b, g.mul(d, ln * 0.5)), g.add(b, g.mul(d, ln))], [1.7, 1.2, 0.2], 'dust', 'ruff',
               flat=0.5, up=(0, 1, 0))
    # long skull, turned toward the viewer
    T, pv = 30, (0, 27.0, 11.0)

    def H(p):
        return yrot(p, pv, T)
    rot = (T, 0, 0)
    head_c, head_r = H((0, 30.2, 13.4)), (4.4, 3.8, 4.4)
    m.ell(head_c, head_r, 'bone', 'head', rot=rot)
    mz_c, mz_r = H((0, 28.9, 18.6)), (2.5, 2.0, 4.0)
    m.ell(mz_c, mz_r, 'bone', 'head', rot=rot)
    m.ell(H((0, 26.9, 17.6)), (2.1, 1.0, 3.6), 'bone', 'jaw', rot=rot)
    for s in (-1, 1):
        m.ell(H((s * 2.3, 32.0, 15.8)), (1.6, 0.9, 1.8), 'bone', 'head', rot=(T, 0, -s * 12))
        m.crystal(H((s * 1.2, 28.0, 21.4)), H((s * 1.2, 26.2, 21.7)), 0.45, 'bone', 'head', sides=4,
                  tip_frac=0.8)
        m.tube([H((s * 2.4, 33.0, 12.2)), H((s * 3.4, 36.4, 10.9)), H((s * 3.9, 39.2, 9.6))], [1.8, 1.3, 0.2],
               'dust', 'ear%d' % s, flat=0.45, up=yrot((0, 0.25, 1), (0, 0, 0), T))
    m.ell(H((0, 29.7, 22.4)), (1.3, 0.9, 0.8), 'dust', 'head', rot=rot)
    for s in (-1, 1):
        p, n = g.on(head_c, head_r, sdir(34 * s + T, 12), rot)
        m.paint(p, (1.9, 1.7, 1.6), 'dust', ['head'], rot=rot)
    g.eye_pair(m, head_c, head_r, 34, 12, 3.2, 2.6, style='glow', iris=('ember', 1), slant=0.6,
               center=H((0, 28, 20)), rot=rot, turn=T)
    p, n = g.on(mz_c, mz_r, yrot((0, -0.6, 0.8), (0, 0, 0), T), rot)
    m.mouth(p, n, 'line', w=3.4)
    return m


def muddle(g):
    m = g.Model('MUDDLE')
    m.outline = (30, 24, 20)
    m.mat('peat', PEAT)
    m.mat('moss', ['#3c682e', '#72a03c', '#a8cc5a'])
    m.mat('bone', BONE3)
    m.mat('glow', SWAMP_GLOW, emissive=0.8)
    m.mat('pink', ['#e07a9a'])
    m.eye_dark = (30, 24, 20)
    m.height = 30
    m.front_yaw = -24
    body_c, body_r = (0, 7.4, 0.4), (8.4, 6.8, 7.8)
    m.ell(body_c, body_r, 'peat', 'body')
    for c, r in (((-4.8, 10.0, -2.4), 4.2), ((4.4, 10.6, -3.0), 3.8), ((0.2, 11.8, -2.2), 4.6),
                 ((-6.4, 5.2, -1.0), 3.6), ((6.6, 5.0, -1.6), 3.4)):
        m.sph(c, r, 'peat', 'body')
    m.ell((0, 1.3, 0.4), (10.4, 1.5, 9.6), 'peat', 'body')
    # drips running down its front
    for (x, z, ln) in ((-5.6, 5.4, 3.4), (6.4, 4.2, 2.4)):
        m.tube([(x, 5.2 + ln * 0.3, z), (x * 1.04, 3.0, z + 0.6), (x * 1.08, 1.6, z + 1.0)], [1.4, 1.1, 1.3],
               'peat', 'body')
    m.paint((0, 14.6, -1.8), (8.0, 3.6, 7.4), 'moss', ['body'])
    for (x, y, z) in ((5.8, 9.2, 4.6), (-6.6, 8.4, 3.0), (-2.4, 4.2, 7.0)):
        m.paint((x, y, z), 1.3, 'moss', ['body'])
    # lily pad hat with a pink flower
    m.ell((-2.2, 16.2, -1.4), (4.4, 0.5, 4.1), 'moss', 'lily', rot=(10, 16, -8))
    for k in range(5):
        a = k * 72 * DEG
        m.sph((-1.6 + math.cos(a) * 0.9, 17.1, -0.8 + math.sin(a) * 0.9), 0.85, 'pink', 'lily')
    m.sph((-1.6, 17.6, -0.8), 0.6, 'glow', 'lily')
    # a stray bone stuck through it
    bone(g, m, (3.6, 9.0, -3.6), (10.6, 13.6, -4.6), 0.9, 'bone', 'bone')
    # stubby arms
    for s in (-1, 1):
        m.ell((s * 8.2, 5.4, 3.6), (2.3, 1.8, 2.6), 'peat', 'arm%d' % s, rot=(0, s * 30, s * 20))
    # mismatched eyes, a wide wobbly mouth
    p, n = g.on(body_c, body_r, sdir(30, 22))
    m.eye(p, n, 4.2, 4.8, style='glow', iris=('glow', 1), pupil='outline', center=(0, 7, 9))
    p, n = g.on(body_c, body_r, sdir(-8, 30))
    m.eye(p, n, 3.0, 3.2, style='glow', iris=('glow', 1), center=(0, 7, 9))
    p, n = g.on(body_c, body_r, sdir(14, -8))
    m.mouth(p, n, 'open', w=6.4, h=3.2, inner=('peat', 0), fang=1)
    return m


def bogshamble(g):
    m = g.Model('BOGSHAMBLE')
    m.outline = (30, 24, 20)
    m.mat('peat', PEAT)
    m.mat('moss', ['#3c682e', '#78a640'])
    m.mat('bone', BONE2)
    m.mat('glow', SWAMP_GLOW, emissive=0.8)
    m.mat('cap', ['#8a3420', '#d46c34'])
    m.eye_dark = (30, 24, 20)
    m.height = 56
    m.max_w = 60
    m.front_yaw = -22
    # stumpy legs
    for s in (-1, 1):
        m.ell((s * 5.0, 5.4, 0.0), (3.6, 5.4, 3.8), 'peat', 'leg%d' % s)
        m.ell((s * 5.4, 1.5, 2.0), (3.4, 1.6, 4.2), 'peat', 'leg%d' % s)
    # hunched torso
    m.ell((0, 11.4, -0.6), (7.2, 4.4, 5.4), 'peat', 'body')
    m.ell((0, 20.0, 0.2), (10.0, 9.4, 7.4), 'peat', 'body', rot=(0, 14, 0))
    m.sph((0, 24.6, -3.6), 7.0, 'peat', 'body')
    for s in (-1, 1):
        m.sph((s * 8.2, 25.4, -0.6), 4.3, 'peat', 'body')
    m.paint((0, 30.0, -3.0), (10.0, 3.6, 7.0), 'moss', ['body'])
    for s in (-1, 1):
        m.paint((s * 8.6, 29.0, -0.6), (3.8, 1.8, 4.0), 'moss', ['body'])
    # ribs showing through the peat
    m.ell((0, 19.2, 7.6), (1.0, 4.4, 0.9), 'bone', 'ribs')
    for k in range(3):
        y = 22.6 - k * 2.8
        for s in (-1, 1):
            m.tube([(s * 0.8, y, 7.7), (s * 3.4, y - 0.5, 7.4), (s * 5.8, y - 1.8, 5.8)], [0.9, 0.85, 0.7],
                   'bone', 'ribs')
    # long drooping arms with moss strands
    for s in (-1, 1):
        a = 'arm%d' % s
        m.tube([(s * 9.0, 25.0, 0.0), (s * 12.8, 17.0, 2.4), (s * 13.2, 9.4, 4.6)], [3.2, 2.8, 2.6], 'peat', a)
        m.sph((s * 13.3, 7.8, 5.2), 3.0, 'peat', a)
        for t in (-1, 0, 1):
            b = (s * 13.3 + t * 1.6, 6.0, 6.2)
            m.tube([b, g.add(b, (t * 0.3, -2.2, 0.8)), g.add(b, (t * 0.4, -3.6, 0.4))], [1.1, 0.9, 0.5],
                   'peat', a)
        for (dz, ln) in ((-1.2, 6.0), (1.4, 4.4)):
            b = (s * 12.4, 20.5, 1.8 + dz)
            m.tube([b, g.add(b, (s * 0.4, -ln * 0.6, 0.2)), g.add(b, (s * 0.2, -ln, 0.4))], [1.0, 0.8, 0.3],
                   'moss', a, flat=0.5, up=(s, 0, 0))
    # slumped head
    head_c, head_r = (0, 27.4, 6.6), (5.2, 4.6, 4.8)
    m.ell(head_c, head_r, 'peat', 'head')
    m.paint(g.add(head_c, (0, 3.4, -0.8)), (5.0, 1.8, 4.6), 'moss', ['head'])
    # mushrooms: a cluster on the left shoulder, one on the head, one on the right
    for (c, rr) in (((8.8, 29.6, -1.0), 3.4), ((6.2, 28.8, 2.0), 2.1), ((-1.4, 32.2, 5.2), 2.5),
                    ((-9.0, 29.0, -0.8), 2.3), ((10.6, 28.2, 1.4), 1.6)):
        base = g.add(c, (0, -rr * 0.9, 0))
        m.tube([base, g.add(c, (0, -rr * 0.2, 0))], [rr * 0.34, rr * 0.3], 'bone', 'shroom')
        m.ell(c, (rr, rr * 0.5, rr), 'cap', 'shroom')
        for d in ((0.5, 0.8, 0.3), (-0.4, 0.8, 0.5), (0.1, 0.9, -0.5), (0.8, 0.4, -0.3)):
            p, n = g.on(c, (rr, rr * 0.5, rr), d)
            m.paint(p, rr * 0.22, 'bone', ['shroom'])
    # a bone poking out of the right shoulder
    bone(g, m, (-7.0, 24.4, -3.4), (-12.4, 31.4, -5.4), 1.1, 'bone', 'bonestick')
    p, n = g.on(head_c, head_r, sdir(28, 14))
    m.eye(p, n, 3.6, 4.2, style='glow', iris=('glow', 1), pupil='outline', center=(0, 26, 13))
    p, n = g.on(head_c, head_r, sdir(-24, 20))
    m.eye(p, n, 2.6, 2.8, style='glow', iris=('glow', 1), center=(0, 26, 13))
    p, n = g.on(head_c, head_r, (0.08, -0.45, 1))
    m.mouth(p, n, 'open', w=4.4, h=2.4, inner=('peat', 0), fang=1)
    return m


def dregcrow(g):
    m = g.Model('DREGCROW')
    m.outline = (18, 16, 28)
    m.mat('feath', ['#1a1828', '#2e2c46', '#4a486a', '#76769c'])
    m.mat('bone', BONE3)
    m.mat('ember', EMBER[:2], emissive=0.85)
    m.mat('beak', ['#34323e', '#5e5c6c', '#8e8c9c'])
    m.eye_dark = (26, 24, 40)
    m.height = 36
    m.front_yaw = -28
    # bare bone legs
    for s in (-1, 1):
        lg = 'leg%d' % s
        m.tube([(s * 2.4, 7.2, 0.2), (s * 2.6, 3.6, 1.0), (s * 2.6, 1.2, 1.4)], [1.0, 0.8, 0.8], 'bone', lg)
        for t in (-1, 0, 1):
            m.tube([(s * 2.6, 0.9, 1.4), (s * 2.6 + t * 1.3, 0.6, 3.6)], [0.6, 0.4], 'bone', lg)
        m.tube([(s * 2.6, 0.9, 1.4), (s * 2.6, 0.6, -0.6)], [0.55, 0.35], 'bone', lg)
    # ragged tail fan
    for k, ln in enumerate((8.0, 10.5, 7.0, 11.0, 8.5)):
        a = (k - 2) * 14 * DEG
        d = g.norm((math.sin(a), -0.55, -1))
        b = (0, 9.0, -6.0)
        g.leaf(m, b, g.add(b, g.mul(d, ln * 0.5)), g.add(b, g.mul(d, ln)), 1.9, 'feath', 'tail',
               up=(0, 1, -0.5), flat=0.25)
    # body, leaning forward, chest tufts
    m.ell((0, 11.2, -0.8), (5.2, 6.4, 6.6), 'feath', 'body', rot=(0, -28, 0))
    for (x, y, z, dx, dy) in ((-1.4, 9.0, 4.4, -0.3, -1), (1.2, 8.0, 4.2, 0.4, -1), (0.2, 10.8, 5.0, 0.1, -0.8)):
        b = (x, y, z)
        d = g.norm((dx, dy, 0.6))
        m.tube([b, g.add(b, g.mul(d, 2.6))], [1.0, 0.2], 'feath', 'body', flat=0.5, up=(0, 0, 1))
    # folded wings with ragged primaries and a bare wing bone
    for s in (-1, 1):
        w = 'wing%d' % s
        m.ell((s * 4.6, 12.0, -1.6), (1.6, 4.6, 6.8), 'feath', w, rot=(s * 8, -22, 0))
        for k, ln in enumerate((6.0, 4.0, 7.0, 5.0)):
            b = (s * (4.4 + 0.3 * k), 10.8 - k * 0.9, -5.2 - k * 0.6)
            d = g.norm((s * 0.15, -0.7, -1))
            g.leaf(m, b, g.add(b, g.mul(d, ln * 0.5)), g.add(b, g.mul(d, ln)), 1.4, 'feath', w,
                   up=(s, 0, 0), flat=0.3)
        bone(g, m, (s * 5.9, 15.0, 1.6), (s * 6.0, 12.4, -4.2), 0.55, 'bone', w, knob=1.1)
    # head: one side has lost its feathers down to the skull; dark beak
    m.tube([(0, 15.4, 2.0), (0, 17.6, 3.4)], [3.1, 2.9], 'feath', 'body')
    head_c, head_r = (0, 19.8, 4.2), (4.3, 4.0, 4.4)
    m.ell(head_c, head_r, 'feath', 'head')
    p, n = g.on(head_c, head_r, sdir(34, 12))
    m.paint(p, (2.4, 2.5, 2.2), 'bone', ['head'])
    m.paint(g.add(p, (-0.4, 0.2, 0.4)), (1.5, 1.6, 1.6), 'feath', ['head'])
    m.tube([(0, 19.4, 7.9), (0, 18.6, 11.0), (0, 17.0, 13.2)], [1.8, 1.2, 0.3], 'beak', 'beak')
    m.tube([(0, 17.8, 8.0), (0, 17.1, 10.6)], [1.2, 0.3], 'beak', 'beak')
    # scraggly crest
    for (dx, dy, dz, ln) in ((0.0, 1, -0.4, 4.4), (0.6, 0.9, -0.6, 3.4), (-0.5, 1, -0.8, 3.8),
                             (0.2, 0.7, -1, 3.0)):
        b = (dx * 1.4, 22.6, 3.4)
        d = g.norm((dx, dy, dz))
        m.tube([b, g.add(b, g.mul(d, ln * 0.6)), g.add(b, g.add(g.mul(d, ln), (dx * 0.6, 0, 0)))],
               [0.9, 0.6, 0.15], 'feath', 'crest')
    for s in (-1, 1):
        b = (s * 3.4, 18.4, 3.0)
        m.tube([b, g.add(b, (s * 1.8, -0.8, -1.4))], [0.8, 0.15], 'feath', 'head')
    g.eye_pair(m, head_c, head_r, 34, 12, 2.6, 2.8, style='glow', iris=('ember', 1), center=(0, 18, 12))
    return m


def cawdaver(g):
    m = g.Model('CAWDAVER')
    m.outline = (22, 16, 30)
    m.mat('bone', BONE)
    m.mat('feath', ['#16141f', '#2a2840', '#46445f'])
    m.mat('ember', EMBER, emissive=0.85)
    m.eye_dark = (22, 20, 31)
    m.height = 58
    m.max_w = 62
    m.front_yaw = -22
    # legs and talons
    for s in (-1, 1):
        lg = 'leg%d' % s
        m.tube([(s * 3.0, 12.0, 0.0), (s * 3.4, 6.2, 1.0), (s * 3.4, 1.6, 1.6)], [1.2, 1.0, 0.95], 'bone', lg)
        m.sph((s * 3.4, 6.2, 1.0), 1.4, 'bone', lg)
        for t in (-1, 0, 1):
            m.crystal((s * 3.4 + t * 0.9, 1.2, 2.2), (s * 3.4 + t * 2.0, 0.3, 5.4), 0.7, 'bone', lg,
                      sides=4, tip_frac=0.7)
    # ribcage + kernel in the open front of the cloak
    m.ell((0, 20.5, 0.8), (3.8, 5.6, 3.4), 'feath', 'core')
    m.paint((1.2, 20.0, 4.0), (2.0, 2.2, 1.6), 'ember', ['core'])
    for k, y in enumerate((25.0, 22.6, 20.2, 17.8)):
        sc = 1 - 0.08 * k
        for s in (-1, 1):
            m.tube([(s * 0.6, y, 4.2), (s * 3.0 * sc, y - 0.6, 3.8), (s * 4.4 * sc, y - 1.8, 1.8)],
                   [0.8, 0.75, 0.6], 'bone', 'ribs')
    m.ell((0, 21.5, 4.3), (0.8, 4.4, 0.7), 'bone', 'ribs')
    # tattered cloak draped round the back and sides
    NU, NV = 8, 4
    jag = [0.0, 3.0, 1.0, 4.2, 0.6, 3.6, 1.2, 2.6]

    def cape(u, v, i):
        th = u * 128 * DEG
        R = 5.8 + 5.4 * v
        y = 30.0 - 21.0 * v - (jag[i] * v ** 3)
        return (math.sin(th) * R, y, -0.6 - math.cos(th) * R * 0.66 - 1.4 * v)
    for j in range(NV):
        for i in range(NU):
            u0 = -1 + 2.0 * i / NU
            u1 = -1 + 2.0 * (i + 1) / NU
            v0, v1 = j / float(NV), (j + 1) / float(NV)
            q = [cape(u0, v0, i), cape(u1, v0, i), cape(u1, v1, i), cape(u0, v1, i)]
            m.poly(q, 'feath', 'cloak', puff=0.3)
    # wings: bare bone struts hung with ragged feathers
    for s in (-1, 1):
        w = 'wing%d' % s
        sh_, el, wr = (s * 5.4, 28.4, -1.4), (s * 13.2, 34.4, -3.6), (s * 20.6, 39.2, -5.2)
        m.tube([sh_, el, wr], [1.3, 1.1, 0.9], 'bone', w)
        m.sph(el, 1.4, 'bone', w)
        m.sph(wr, 1.2, 'bone', w)
        tips = [(s * 27.4, 37.2, -6.2), (s * 28.4, 31.4, -6.4), (s * 25.8, 26.4, -6.0)]
        for tp in tips:
            m.tube([wr, tp], [0.8, 0.45], 'bone', w)
        rnd = g.Rand(89 + s)
        feathers = []
        for k in range(5):
            feathers.append(g.lerp(sh_, el, 0.2 + 0.2 * k) if k < 3 else g.lerp(el, wr, 0.3 * (k - 2)))
        feathers += [g.lerp(wr, tips[0], 0.8), g.lerp(wr, tips[1], 0.85), g.lerp(wr, tips[2], 0.9)]
        for k, b in enumerate(feathers):
            if k == 4:
                continue      # a gap: the cloak is tattered
            ln = 7.0 + 5.5 * rnd.f() + (2.0 if k >= 5 else 0)
            d = g.norm((s * (0.12 + 0.07 * k), -1, -0.15))
            g.leaf(m, b, g.add(b, g.mul(d, ln * 0.5)), g.add(b, g.mul(d, ln)), 1.9, 'feath', w,
                   up=(0, 0, 1), flat=0.25)
    # neck, hood and bone skull with a long beak
    beads(g, m, [(0, 26.6, 0.6), (0, 30.6, 2.2), (0, 33.4, 3.6)], 1.6, 1.4, 'bone', 'neck', n=3)
    m.ell((0, 38.0, 1.4), (5.6, 5.6, 4.6), 'feath', 'hood')
    for (x, y, z, dx, dy) in ((-4.6, 34.0, 0.0, -0.4, -1), (4.6, 34.0, 0.0, 0.4, -1), (0, 42.6, -0.6, 0, 1),
                              (-3.4, 41.4, -1.4, -0.6, 0.8), (3.2, 41.6, -1.2, 0.6, 0.8)):
        b = (x, y, z)
        d = g.norm((dx, dy, -0.5))
        m.tube([b, g.add(b, g.mul(d, 3.0))], [1.6, 0.2], 'feath', 'hood', flat=0.5, up=(0, 0, 1))
    head_c, head_r = (0, 37.0, 5.2), (3.9, 3.7, 4.1)
    m.ell(head_c, head_r, 'bone', 'head')
    m.tube([(0, 36.6, 8.6), (0, 35.6, 13.2), (0, 33.8, 16.2)], [1.9, 1.2, 0.3], 'bone', 'beak')
    m.tube([(0, 34.8, 8.6), (0, 34.0, 12.0)], [1.2, 0.3], 'bone', 'beak')
    m.dot(g.on((0, 36.2, 10.0), (1.6, 1.4, 2.2), (0.3, 0.6, 0.8))[0], (0.3, 0.6, 0.8), w=0.8, h=0.5,
          color=('feath', 0))
    sockets(g, m, head_c, head_r, 34, 10, (1.8, 1.9, 1.6), 'feath', 'head')
    g.eye_pair(m, head_c, head_r, 34, 10, 2.8, 2.8, style='glow', iris=('ember', 1), slant=0.5,
               center=(0, 35, 14))
    return m


def cranicrab(g):
    m = g.Model('CRANICRAB')
    m.outline = (36, 28, 40)
    m.mat('bone', BONE)
    m.mat('crab', CRAB)
    m.mat('coral', CORAL)
    m.mat('hole', ['#2a2030'])
    m.eye_dark = (42, 32, 48)
    m.height = 30
    m.front_yaw = -28
    # walking legs from under the skull
    for k, z in enumerate((2.0, -1.4, -4.6)):
        for s in (-1, 1):
            lg = 'leg%s%d' % ('ABC'[k], s)
            m.tube([(s * 5.2, 4.2, z), (s * 9.2, 5.2, z + 0.6), (s * 11.4, 0.9, z + 1.4)], [1.0, 0.85, 0.45],
                   'crab', lg)
            m.sph((s * 9.2, 5.2, z + 0.6), 1.0, 'crab', lg)
    # the skull it lives in
    cr_c, cr_r = (0, 10.6, -1.6), (7.4, 6.8, 7.6)
    m.ell(cr_c, cr_r, 'bone', 'skull')
    m.ell((0, 7.0, 3.6), (5.4, 3.4, 4.2), 'bone', 'skull')
    for s in (-1, 1):
        m.ell((s * 5.2, 7.8, 2.6), (1.6, 1.4, 2.2), 'bone', 'skull')
    for x in (-2.4, -1.2, 0.0, 1.2, 2.4):
        m.ell((x, 4.3, 6.9 - x * x * 0.1), (0.52, 0.9, 0.5), 'bone', 'skull')
    m.ell((0, 4.4, 4.0), (4.4, 1.6, 3.0), 'hole', 'gap')
    sockets(g, m, cr_c, cr_r, 25, -2, (2.3, 2.5, 1.9), 'hole', 'skull')
    m.paint((0, 7.8, 7.7), (0.9, 1.1, 0.9), 'hole', ['skull'])
    for (a, b) in (((-4.2, 16.4, 0.4), (-2.6, 13.8, 3.4)), ((-2.6, 13.8, 3.4), (-3.6, 12.2, 4.8))):
        for k in range(5):
            m.paint(g.lerp(a, b, k / 4.0), (0.45, 0.45, 1.2), 'hole', ['skull'])
    # a starfish on the dome
    sf = (2.2, 17.1, -1.4)
    for k in range(5):
        a = (k * 72 + 10) * DEG
        m.tube([sf, g.add(sf, (math.cos(a) * 2.2, 0.2 - 0.3 * abs(math.sin(a)), math.sin(a) * 2.2))], [0.8, 0.25],
               'coral', 'star')
    # eyestalks poking out through the eye sockets
    for s in (-1, 1):
        base, _ = g.on(cr_c, cr_r, sdir(25 * s, -2))
        base = g.add(base, (0, -0.4, -1.4))
        tip = g.add(base, (s * 1.2, 4.6, 3.0))
        m.tube([base, g.add(base, (s * 0.2, 1.6, 2.2)), tip], [0.85, 0.75, 0.7], 'crab', 'stalk%d' % s)
        ec = g.add(tip, (s * 0.2, 0.9, 0.3))
        m.sph(ec, 1.75, 'crab', 'eyeball%d' % s)
        p, n = g.on(ec, 1.75, (s * 0.2, 0.05, 1))
        m.eye(p, n, 2.6, 3.0, style='cute', center=(0, 12, 14))
    # claws: a big one on its left, a small one on its right
    claw(g, m, (3.2, 4.0, 4.2), (5.6, 3.2, 7.4), (6.2, 4.0, 9.8), (2.3, 2.1, 2.8), 1.25, 'claw1')
    claw(g, m, (-3.0, 4.0, 4.2), (-4.6, 3.0, 6.8), (-4.8, 3.4, 8.6), (1.5, 1.4, 1.9), 0.85, 'claw-1')
    return m


def cryptclaw(g):
    m = g.Model('CRYPTCLAW')
    m.outline = (24, 22, 34)
    m.mat('urn', ['#262c3c', '#3e4a64', '#62728e', '#9aaac0'])
    m.mat('bone', BONE2)
    m.mat('crab', CRAB[:3])
    m.mat('coral', CORAL)
    m.mat('hole', ['#221c28'])
    m.eye_dark = (34, 28, 40)
    m.height = 52
    m.max_w = 62
    m.front_yaw = -26
    # legs lifting the urn
    for k, z in enumerate((4.4, 0.0, -4.4)):
        for s in (-1, 1):
            lg = 'leg%s%d' % ('ABC'[k], s)
            m.tube([(s * 6.0, 7.6, z), (s * 12.0, 9.0, z + 1.0), (s * 14.4, 1.0, z + 2.0)], [1.6, 1.3, 0.7],
                   'crab', lg)
            m.sph((s * 12.0, 9.0, z + 1.0), 1.6, 'crab', lg)
    # the crypt urn
    m.ell((0, 7.6, 0), (5.4, 1.7, 5.4), 'urn', 'urn')
    m.ell((0, 16.0, 0), (10.0, 9.0, 10.0), 'urn', 'urn')
    m.ell((0, 24.0, 0), (7.2, 2.4, 7.2), 'urn', 'urn')
    m.ell((0, 26.2, 0), (5.2, 1.6, 5.2), 'urn', 'urn')
    m.ell((0, 27.8, 0), (6.6, 1.2, 6.6), 'urn', 'urn')
    m.ell((0, 28.6, 0.4), (5.4, 0.7, 5.4), 'hole', 'gap')
    for y, t in ((20.6, 0.8), (10.4, 0.7)):
        m.paint((0, y, 0), (10.6, t, 10.6), 'bone', ['urn'])
    # carved skull on its front
    fc = (-1.2, 15.2, 9.8)
    m.paint(fc, (3.2, 3.5, 1.4), 'bone', ['urn'])
    for s in (-1, 1):
        m.paint(g.add(fc, (s * 1.3, 0.6, 0.4)), (1.0, 1.1, 1.2), 'hole', ['urn'])
    m.paint(g.add(fc, (0, -1.0, 0.4)), (0.5, 0.6, 1.2), 'hole', ['urn'])
    for x in (-1.2, 0.0, 1.2):
        m.paint(g.add(fc, (x, -2.6, 0.2)), (0.35, 0.8, 1.2), 'hole', ['urn'])
    for (a, b) in (((6.4, 23.0, 5.0), (7.8, 17.0, 6.2)), ((7.8, 17.0, 6.2), (6.4, 13.0, 7.4))):
        for k in range(6):
            m.paint(g.lerp(a, b, k / 5.0), (0.5, 0.5, 1.6), 'hole', ['urn'])
    # lid, pushed up at the front, with a little skull knob
    m.ell((0, 32.2, -1.4), (7.4, 2.2, 7.4), 'urn', 'lid', rot=(0, -22, 0))
    m.ell((0, 35.8, -2.8), (3.6, 3.3, 3.5), 'bone', 'lid')
    m.ell((0, 34.2, -0.4), (2.5, 1.6, 2.1), 'bone', 'lid')
    sockets(g, m, (0, 35.8, -2.8), (3.6, 3.3, 3.5), 28, -6, (1.1, 1.2, 1.0), 'hole', 'lid')
    # eyestalks peeking out from under the lid
    for s in (-1, 1):
        base = (s * 2.2, 27.4, 3.4)
        tip = (s * 3.2, 31.4, 7.4)
        m.tube([base, g.add(base, (s * 0.3, 2.4, 1.6)), tip], [1.0, 0.9, 0.85], 'crab', 'stalk%d' % s)
        ec = g.add(tip, (s * 0.2, 0.8, 0.4))
        m.sph(ec, 2.0, 'crab', 'eyeball%d' % s)
        p, n = g.on(ec, 2.0, (s * 0.2, 0.05, 1))
        m.eye(p, n, 3.0, 3.4, style='cute', center=(0, 30, 16))
    # heavy claws from the urn's side holes, bone-studded
    claw(g, m, (7.6, 14.0, 5.6), (12.0, 12.6, 8.2), (12.6, 13.4, 12.2), (3.6, 3.4, 4.2), 2.0, 'claw1')
    claw(g, m, (-7.6, 14.0, 5.6), (-10.6, 12.0, 8.0), (-10.8, 12.4, 10.8), (2.6, 2.4, 3.0), 1.4, 'claw-1')
    for (c, r) in (((12.6, 16.6, 11.6), 0.8), ((14.8, 14.6, 11.0), 0.7), ((-10.8, 14.6, 10.4), 0.6)):
        m.crystal(c, g.add(c, (0.3 if c[0] > 0 else -0.3, 1.8, -0.4)), r, 'bone', 'claw1' if c[0] > 0 else 'claw-1',
                  sides=4, tip_frac=0.8)
    return m
