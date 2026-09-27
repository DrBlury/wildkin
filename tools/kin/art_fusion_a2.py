"""Art for kin 145-151 (KIN-D2).

One model function per species (the lowercase species name), called by
tools/gen_monsters.py as fn(g) with g = the gen_monsters module. Coordinates:
+Y up, +Z the way the kin faces, +X its left; the ground is y = 0.
"""

import math

from kin.art_fusion_a import (_Rand, add, cross, disk, lerp, mul, norm, overworld,
                              puff_cloud, ring_paint, sub)

DEG = math.pi / 180.0


# ==========================================================================
# 145 AURORELK  FROST/DREAM
# A snowy elk wearing a star-speckled saddle of night sky, with a frost
# dewlap; its antlers branch into separate ribbons of aurora, green to violet.
# ==========================================================================
def aurorelk(g):
    m = g.Model('AURORELK')
    m.outline = (30, 30, 58)
    m.mat('snow', ['#7c88b0', '#b8c4dc', '#e4ecf8'])
    m.mat('night', ['#1c1c4c', '#303478'])
    m.mat('frost', ['#6cc4e8', '#d8f4ff'], emissive=0.3)
    m.mat('green', ['#18b078', '#6cf0b0'], emissive=0.5)
    m.mat('violet', ['#7a44d8', '#c49cff'], emissive=0.5)
    m.eye_dark = (22, 20, 50)
    m.white = (248, 252, 255)
    m.height = 58
    m.max_w = 62
    m.front_yaw = -30
    # ---- long legs with dark hooves
    for s in (-1, 1):
        for zz, nm in ((7.5, 'legF'), (-8.5, 'legB')):
            top = (s * 4.4, 15.0, zz)
            knee = (s * 4.6, 8.5, zz + (0.8 if nm == 'legF' else -1.4))
            foot = (s * 4.6, 1.7, zz + 0.3)
            m.tube([top, knee, foot], [3.0, 1.8, 1.5], 'snow', '%s%d' % (nm, s))
            m.ell(add(foot, (0, -0.3, 0.5)), (1.8, 1.4, 2.1), 'night', '%s%d' % (nm, s))
    # ---- barrel body wearing a starry night saddle
    body_c, body_r = (0, 18.5, -0.5), (6.8, 6.4, 11.2)
    m.ell(body_c, body_r, 'snow', 'body')
    m.ell((0, 19.0, 6.8), (6.4, 7.2, 5.6), 'snow', 'body')
    m.ell((0, 17.5, -9.0), (5.4, 5.6, 4.4), 'snow', 'body')
    m.paint((0, 24.0, -1.5), (8.0, 5.4, 8.0), 'night', ['body'])
    m.paint((0, 18.4, -1.5), (8.0, 0.8, 8.0), 'frost', ['body'])
    for (x, z) in ((0.55, 3.5), (-0.1, -0.5), (0.3, -4.5), (0.75, 0.0), (-0.6, 3.0),
                   (-0.5, -5.0)):
        el = 0.5 if abs(x) > 0.5 else 0.9
        p, n = g.on(body_c, body_r, (x, el, z / 11.0))
        m.sparkle(p, n, size=1, color='white')
    # stubby tail tuft
    m.tube([(0, 21.0, -12.4), (0, 19.0, -14.2)], [1.8, 0.9], 'snow', 'body')
    # ---- neck, shaggy throat and frost dewlap
    neck = [(0, 22.0, 8.5), (0, 27.0, 11.0), (0, 31.0, 12.4)]
    m.tube(neck, [4.4, 3.6, 3.0], 'snow', 'neck')
    m.tube([(0, 26.5, 13.4), (0, 22.5, 14.2), (0, 18.5, 13.4)], [2.6, 2.3, 0.7],
           'frost', 'neck', flat=0.55, up=(1, 0, 0))
    for y in (24.2, 21.0):
        m.crystal((0, y, 14.2), (0.2, y - 3.0, 14.6), 0.8, 'frost', 'neck', sides=4,
                  tip_frac=0.7)
    # ---- head with a long muzzle
    head_c, head_r = (0, 33.5, 14.0), (4.4, 4.0, 4.4)
    m.ell(head_c, head_r, 'snow', 'head')
    mz_c, mz_r = (0, 31.6, 18.8), (2.7, 2.4, 3.4)
    m.ell(mz_c, mz_r, 'snow', 'head')
    m.dot(g.on(mz_c, mz_r, (0, 0.3, 1))[0], (0, 0.2, 1), w=1.8, h=1.1, minw=2,
          color=('night', 0))
    for s in (-1, 1):
        m.tube([(s * 3.4, 35.6, 12.8), (s * 6.4, 36.4, 11.6), (s * 8.0, 35.6, 11.0)],
               [1.6, 1.1, 0.2], 'snow', 'head', flat=0.45, up=(0, 0.3, 1))
    g.eye_pair(m, head_c, head_r, 40, 14, 3.4, 3.6, style='iris', iris=('violet', 0),
               center=(0, 32, 21), turn=6)
    # ---- aurora antlers: a snowy beam on each side, three separate wavy
    #      light ribbons branching off it, green at the root, violet at the tip
    for s in (-1, 1):
        b = (s * 2.0, 36.8, 13.0)
        mid = (s * 4.2, 39.0, 12.4)
        end = (s * 6.6, 40.2, 11.8)
        m.tube([b, mid, end], [1.3, 1.1, 0.9], 'snow', 'antler%d' % s)
        for k, (root, ang, ln) in enumerate(((mid, 98, 11.5), (end, 52, 13.0),
                                             (end, 2, 11.0))):
            a = ang * DEG
            d = (s * math.cos(a), math.sin(a), -0.15)
            pts = []
            for i in range(5):
                t = i / 4.0
                wob = math.sin(t * math.pi * 1.5 + k * 1.3) * 1.0
                q = add(root, mul(d, ln * t))
                pts.append(add(q, (-s * math.sin(a) * wob, math.cos(a) * wob, 0)))
            m.tube(pts, [0.8, 1.0, 1.0, 0.85, 0.3], 'green', 'antler%d%d' % (s, k),
                   flat=0.45, up=(0, 0, 1), mats=[(0, 'green'), (0.5, 'violet')])
    return m


# ==========================================================================
# 146 RAIJUKO  SPARK/GALE
# A storm-navy weasel caught mid-leap in an arch; a zigzag lightning mane
# runs down its spine, its tail is a forked bolt and two balls of lightning
# orbit it.
# ==========================================================================
def _crackle(g, m, c, r, part, seed, n=3):
    """A few tiny zigzag sparks jumping off a ball of lightning."""
    rnd = _Rand(seed)
    for k in range(n):
        a = (k * 360.0 / n + rnd.f() * 40) * DEG
        d = (math.cos(a), math.sin(a), 0.3)
        p0 = add(c, mul(d, r * 0.8))
        side = (-d[1] * 0.9, d[0] * 0.9, 0)
        p1 = add(add(c, mul(d, r * 1.45)), side)
        p2 = add(add(c, mul(d, r * 1.9)), mul(side, -0.5))
        g.zigzag(m, [p0, p1, p2], [0.55, 0.45, 0.2], 'spark', part, flat=0.7)


def raijuko(g):
    m = g.Model('RAIJUKO')
    m.outline = (16, 18, 44)
    m.mat('fur', ['#1a2250', '#2c3c80', '#4862b4', '#7c9ae0'])
    m.mat('belly', ['#8ca4d8', '#c4d4f4'])
    m.mat('spark', ['#1ea0f0', '#6ae4ff', '#e6ffff'], emissive=0.55)
    m.eye_dark = (14, 16, 40)
    m.white = (230, 255, 255)
    m.height = 54
    m.max_w = 62
    m.front_yaw = -52
    # ---- hind legs planted, pushing off
    for s in (-1, 1):
        m.ell((s * 3.4, 10.5, -8.5), (2.8, 4.4, 4.0), 'fur', 'legB%d' % s)
        m.tube([(s * 3.6, 8.0, -9.5), (s * 3.8, 4.0, -12.0), (s * 3.8, 1.8, -10.8)],
               [2.2, 1.4, 1.3], 'fur', 'legB%d' % s)
        m.ell((s * 3.8, 1.3, -9.8), (1.5, 1.2, 2.4), 'fur', 'legB%d' % s)
    # ---- the arched body: a long weasel spine bowed upward
    spine = [(0, 10.5, -9.5), (0, 16.0, -5.5), (0, 19.0, -0.5), (0, 18.5, 4.5),
             (0, 16.0, 8.5)]
    m.tube(spine, [3.8, 4.2, 4.2, 4.0, 3.6], 'fur', 'body')
    m.tube([(0, 13.0, -6.0), (0, 15.2, -0.8), (0, 14.6, 4.6), (0, 12.6, 8.2)],
           [1.8, 2.2, 2.2, 1.8], 'belly', 'body')
    # ---- front legs reaching forward and down mid-leap
    for s in (-1, 1):
        m.tube([(s * 3.0, 14.5, 8.5), (s * 3.4, 10.5, 12.5), (s * 3.2, 7.2, 15.6)],
               [2.0, 1.5, 1.3], 'fur', 'legF%d' % s)
        m.ell((s * 3.2, 6.6, 16.6), (1.5, 1.2, 2.1), 'fur', 'legF%d' % s,
              rot=(0, 30, 0))
    # ---- forked lightning-bolt tail sweeping up behind
    tail = [(0, 11.0, -11.5), (1.0, 15.0, -16.0), (-1.4, 19.0, -16.5),
            (1.6, 23.5, -20.5), (-0.6, 27.5, -21.0)]
    g.zigzag(m, tail, [2.6, 2.2, 1.9, 1.6, 1.3], 'fur', 'tail', flat=0.5,
             up=(1, 0, 0), mats=[(0, 'fur'), (0.5, 'spark')])
    for dx, dz in ((3.0, 1.0), (-3.2, -1.5)):
        g.zigzag(m, [tail[-1], add(tail[-1], (dx * 0.5, 2.6, dz - 1.0)),
                     add(tail[-1], (dx, 4.2, dz - 0.6)),
                     add(tail[-1], (dx * 1.6, 7.0, dz - 1.6))],
                 [1.3, 1.0, 0.8, 0.2], 'spark', 'tail', flat=0.5, up=(1, 0, 0))
    # ---- head with a pointed muzzle, round ears
    head_c, head_r = (0, 20.5, 11.5), (4.4, 3.9, 4.4)
    m.ell(head_c, head_r, 'fur', 'head')
    mz_c, mz_r = (0, 19.4, 15.4), (2.4, 2.0, 2.8)
    m.ell(mz_c, mz_r, 'belly', 'head')
    m.dot(g.on(mz_c, mz_r, (0, 0.4, 1))[0], (0, 0.3, 1), w=1.5, h=1.0, minw=2)
    for s in (-1, 1):
        m.ell((s * 3.2, 24.0, 10.4), (1.8, 1.9, 0.9), 'fur', 'head', rot=(s * 20, 0, 0))
        m.paint((s * 3.2, 24.0, 11.1), (1.0, 1.1, 0.8), 'spark', ['head'])
        # cheek sparks
        m.paint(g.on(head_c, head_r, (s * 0.8, -0.35, 0.5))[0], (1.2, 0.9, 1.2), 'spark',
                ['head'])
    g.eye_pair(m, head_c, head_r, 36, 12, 3.6, 4.0, style='sharp', iris=('spark', 0),
               slant=0.6, center=(0, 20, 18), turn=8)
    p, n = g.on(mz_c, mz_r, (0, -0.4, 1))
    m.mouth(p, n, 'smile', w=2.4, fang=1)
    # ---- lightning mane: jagged bolts standing along the spine
    mane = [(0, 23.0, 8.5), (0, 22.5, 3.5), (0, 21.5, -1.5), (0, 18.0, -5.8)]
    for k, q in enumerate(mane):
        h = (8.0, 9.0, 8.0, 6.0)[k]
        pts = [add(q, (0, -1.5, 0)), add(q, (0, h * 0.45, 1.0)),
               add(q, (0, h * 0.55, -2.6)), add(q, (0, h, -1.8))]
        g.zigzag(m, pts, [1.5, 1.2, 1.0, 0.2], 'spark', 'mane', flat=0.55, up=(1, 0, 0))
    # ---- two orbiting balls of lightning
    for c, r, seed in (((2.0, 32.0, 20.5), 2.4, 3), ((6.5, 5.0, 0.5), 2.3, 7)):
        m.sph(c, r, 'spark', 'orb%d' % seed)
        m.paint(add(c, (0.5, 0.6, r * 0.6)), r * 0.45, 'belly', ['orb%d' % seed])
        _crackle(g, m, c, r, 'orb%d' % seed, seed)
    return m


# ==========================================================================
# 147 SPOREGHOUL  HOLLOW/VENOM
# A gaunt, hunched ghoul in a tattered shroud whose hood is a huge purple
# spotted toadstool; green gills and eyes glow beneath it, small mushrooms
# sprout from its shoulders and spores drift around its long bony arms.
# ==========================================================================
def _toadstool(m, base, h, r, part, tilt=(0, 0, 0)):
    """A little mushroom: pale stem, purple cap with a white spot."""
    top = add(base, (tilt[0], h, tilt[2]))
    m.tube([base, top], [r * 0.45, r * 0.35], 'bone', part)
    m.ell(add(top, (0, r * 0.25, 0)), (r, r * 0.6, r), 'cap', part)
    m.paint(add(top, (0, r * 0.35, 0)), (r * 0.9, 0.35, r * 0.9), 'gill', [part])
    m.paint(add(top, (r * 0.3, r * 0.8, r * 0.3)), r * 0.3, 'bone', [part])


def sporeghoul(g):
    m = g.Model('SPOREGHOUL')
    m.outline = (22, 16, 28)
    m.mat('shroud', ['#34303e', '#565062', '#7e788c'])
    m.mat('bone', ['#8a8270', '#c6bca2', '#eee6cc'])
    m.mat('cap', ['#46185a', '#76308c', '#aa56c0'])
    m.mat('gill', ['#3cd868', '#c0ffb0'], emissive=0.75)
    m.mat('void', ['#141018'])
    m.eye_dark = (20, 16, 24)
    m.white = (238, 230, 204)
    m.height = 56
    m.max_w = 60
    m.front_yaw = -28
    # ---- the shroud: a hunched robe that leans forward, tattered hem
    robe = [(0, 6.0, -2.0), (0, 10.0, -2.2), (0, 14.5, -1.4), (0, 19.0, 1.0),
            (0, 22.0, 4.0)]
    m.tube(robe, [6.4, 6.2, 5.8, 5.6, 4.6], 'shroud', 'robe')
    for k in range(14):
        a = (k * 360.0 / 14 + 8) * DEG
        lo = 0.3 + (k * 7 % 4) * 0.9
        b = (math.sin(a) * 5.4, 8.0, -2.0 + math.cos(a) * 5.4)
        tip = (math.sin(a) * 8.2, lo, -2.0 + math.cos(a) * 8.2)
        m.crystal(b, tip, 2.0, 'shroud', 'robe', sides=4, tip_frac=0.8,
                  twist=a / DEG)
    for k in range(5):
        a = (k * 72 + 20) * DEG
        m.paint((math.sin(a) * 6.2, 11.0 - (k % 2) * 3.0, -1.6 + math.cos(a) * 6.2),
                (0.9, 3.4, 0.9), 'void', ['robe'])
    # ---- long bony arms reaching forward, draped ragged sleeves
    for s in (-1, 1):
        sh = (s * 5.2, 19.5, 4.0)
        elb = (s * 8.4, 13.5, 8.0)
        wr = (s * 8.2, 8.5, 12.8)
        m.tube([sh, add(sh, (s * 1.8, -3.0, 1.8))], [3.2, 2.8], 'shroud', 'arm%d' % s)
        for k in range(3):
            m.crystal(add(sh, (s * 2.0, -3.2, 0.6 + k * 1.3)),
                      add(sh, (s * 2.6, -8.5 + k * 1.2, 0.2 + k * 1.6)), 1.2, 'shroud',
                      'arm%d' % s, sides=4, tip_frac=0.9)
        m.tube([add(sh, (s * 1.6, -2.6, 1.6)), elb], [1.6, 1.3], 'bone', 'arm%d' % s)
        m.sph(elb, 1.7, 'bone', 'arm%d' % s)
        m.tube([elb, wr], [1.3, 1.1], 'bone', 'arm%d' % s)
        m.ell(wr, (1.9, 1.5, 1.9), 'bone', 'arm%d' % s)
        for f in (-1, 0, 1):
            k1 = add(wr, (s * 0.4 + f * 1.3, -2.4, 1.8))
            k2 = add(wr, (s * 0.2 + f * 1.5, -5.2, 1.2))
            m.tube([add(wr, (f * 0.8, -0.4, 0.8)), k1, k2], [0.75, 0.6, 0.2], 'bone',
                   'arm%d' % s)
    # ---- the face in the dark: a sunken void with glowing eyes and grin
    face_c, face_r = (0, 22.6, 9.6), (3.8, 3.4, 2.8)
    m.ell((0, 23.0, 7.4), (4.6, 4.0, 3.6), 'void', 'head')
    m.ell(face_c, face_r, 'void', 'head')
    g.eye_pair(m, face_c, face_r, 40, 18, 2.6, 2.8, style='glow', iris=('gill', 1),
               glint=False, center=(0, 22, 16), turn=4)
    p, n = g.on(face_c, face_r, (0.1, -0.5, 1))
    m.mouth(p, n, 'w', w=4.0, color=('gill', 0))
    # ---- the toadstool hood: a big domed cap, its brim lifted at the front
    cap_c, cap_r, cap_rot = (0, 30.0, 5.4), (10.8, 6.0, 9.4), (0, -10, 0)
    m.ell(cap_c, cap_r, 'cap', 'cap', rot=cap_rot)
    m.ell((0, 27.6, 5.6), (10.4, 1.8, 9.0), 'gill', 'cap', rot=cap_rot)
    for k in range(20):
        a = k * 18 * DEG
        m.paint((math.sin(a) * 6.5, 26.4 + math.cos(a) * 1.4, 5.8 + math.cos(a) * 6.0),
                (0.35, 1.2, 0.35), 'cap', ['cap'])
    # white warts / spots on the cap
    for (dx, dy, dz, r) in ((0.0, 1.0, 0.1, 2.0), (0.55, 0.62, 0.45, 1.6),
                            (-0.6, 0.6, 0.4, 1.6), (0.2, 0.55, 0.8, 1.5),
                            (-0.25, 0.7, -0.6, 1.5), (0.75, 0.45, -0.3, 1.4),
                            (-0.8, 0.4, -0.2, 1.3), (-0.3, 0.4, 0.85, 1.2)):
        p, n = g.on(cap_c, cap_r, (dx, dy, dz), rot=cap_rot)
        m.paint(p, (r, r * 0.7, r), 'bone', ['cap'])
    # ---- small toadstools on the shoulders
    _toadstool(m, (6.4, 18.5, 3.0), 2.4, 2.1, 'shroomR', tilt=(2.4, 0, 0.6))
    _toadstool(m, (-6.2, 18.0, 2.6), 2.0, 1.8, 'shroomL', tilt=(-2.2, 0, 0.4))
    _toadstool(m, (4.6, 13.0, 4.0), 1.4, 1.3, 'shroomB', tilt=(1.4, 0, 0.8))
    # ---- drifting spores
    for (x, y, z, r) in ((10.0, 38.0, 4.0, 1.2), (-11.0, 35.5, 2.0, 1.3),
                         (12.5, 20.0, 8.0, 1.0), (-12.5, 18.0, 7.0, 1.1),
                         (4.0, 40.0, -2.0, 0.9), (-5.0, 16.0, 13.0, 0.9)):
        m.sph((x, y, z), r, 'gill', 'spores')
    return m


# ==========================================================================
# 148 CLOCKOWL  METAL/DREAM
# A round steel owl with a clock set into its chest (ivory face, ticks and
# hands, brass bezel), pointed gear-tooth ear tufts, pink dreaming eyes and a
# pendulum for a tail.
# ==========================================================================
def _gear(m, c, n, r, teeth, mat, part, th=0.8, tooth=0.9, arc=(0, 360)):
    """A flat cog: a disk facing n with square teeth round its rim."""
    n = norm(n)
    disk(m, c, n, r, mat, part, th=th)
    u = norm(cross(n, (0, 1, 0) if abs(n[1]) < 0.9 else (1, 0, 0)))
    v = cross(n, u)
    for k in range(teeth):
        a = arc[0] + (arc[1] - arc[0]) * (k + 0.5) / teeth
        if a > 360:
            a -= 360
        a *= DEG
        d = add(mul(u, math.cos(a)), mul(v, math.sin(a)))
        q = add(c, mul(d, r + tooth * 0.4))
        m.tube([add(c, mul(d, r - 0.4)), q], [tooth * 0.6, tooth * 0.55], mat, part,
               flat=th / (tooth * 0.6), up=n)


def clockowl(g):
    m = g.Model('CLOCKOWL')
    m.outline = (26, 26, 38)
    m.mat('steel', ['#343c4c', '#56627a', '#8894aa', '#c2cad8'], spec=0.5)
    m.mat('brass', ['#6c4814', '#b8842a', '#f0ca5c'], spec=0.5)
    m.mat('ivory', ['#c8b88e', '#f4ecd2'])
    m.mat('ink', ['#28202e'])
    m.mat('dream', ['#e0509e', '#ffb2dc'], emissive=0.6)
    m.eye_dark = (40, 20, 44)
    m.white = (244, 236, 210)
    m.height = 52
    m.max_w = 58
    m.front_yaw = -22
    # ---- brass talons
    for s in (-1, 1):
        m.tube([(s * 3.4, 7.0, 1.0), (s * 3.6, 2.2, 2.0)], [1.4, 1.0], 'brass', 'leg%d' % s)
        for t in (-1, 0, 1):
            m.tube([(s * 3.6, 1.6, 2.2), (s * 3.6 + t * 1.3, 0.8, 4.4)], [0.8, 0.45],
                   'brass', 'leg%d' % s)
    # ---- pendulum tail: a brass rod swinging a round bob
    m.tube([(0, 10.0, -6.5), (1.6, 5.0, -8.6), (3.0, 2.8, -9.4)], [0.7, 0.6, 0.6],
           'brass', 'pend')
    disk(m, (3.3, 3.0, -9.6), (0.3, 0, -1), 2.6, 'brass', 'pend', th=0.8)
    m.paint((3.2, 3.0, -10.3), 1.2, 'steel', ['pend'])
    # ---- round steel body with folded feather wings
    body_c, body_r = (0, 16.0, 0.0), (9.2, 9.6, 8.4)
    m.ell(body_c, body_r, 'steel', 'body')
    for s in (-1, 1):
        wc = (s * 8.4, 16.5, -1.2)
        m.ell(wc, (2.6, 8.0, 6.2), 'steel', 'wing%d' % s, rot=(s * 8, -8, s * 6))
        for k in range(3):
            m.paint(add(wc, (s * 1.8, -3.0 - k * 2.2, -1.5 + k * 0.4)), (1.4, 0.5, 4.5),
                    'steel', ['wing%d' % s])
            m.paint(add(wc, (s * 2.2, 2.0 - k * 2.6, -1.0)), (0.6, 0.6, 0.6), 'brass',
                    ['wing%d' % s])
    # ---- the chest clock: brass bezel, ivory face, ticks and hands
    cc, cn = (0, 14.4, 8.0), norm((0, 0.1, 1))
    disk(m, cc, cn, 6.0, 'brass', 'clock', th=1.4)
    disk(m, add(cc, mul(cn, 0.35)), cn, 4.9, 'ivory', 'clock', th=1.4)
    for k in range(12):
        a = k * 30 * DEG
        big = k % 3 == 0
        q = add(cc, (math.sin(a) * 4.0, math.cos(a) * 4.0, 1.55))
        m.paint(q, (0.55, 0.55, 0.6) if big else (0.4, 0.4, 0.5), 'ink', ['clock'])
    m.tube([add(cc, (0, 0, 1.6)), add(cc, (1.6, 2.4, 1.6))], [0.55, 0.45], 'ink', 'clock')
    m.tube([add(cc, (0, 0, 1.6)), add(cc, (-2.8, -1.4, 1.5))], [0.5, 0.35], 'ink',
           'clock')
    m.sph(add(cc, (0, 0, 1.6)), 0.7, 'brass', 'clock')
    # ---- round head: pale facial discs, pink dream eyes, brass beak
    head_c, head_r = (0, 28.0, 0.8), (8.4, 6.8, 7.2)
    m.ell(head_c, head_r, 'steel', 'head')
    for s in (-1, 1):
        p, n = g.on(head_c, head_r, (s * 0.52, 0.02, 1))
        m.paint(p, (3.4, 3.4, 1.6), 'ivory', ['head'])
    g.eye_pair(m, head_c, head_r, 31, 2, 4.4, 4.6, style='iris', iris=('dream', 0),
               center=(0, 28, 10), turn=3)
    p, n = g.on(head_c, head_r, (0, -0.25, 1))
    m.tube([add(p, (0, 0.6, -0.4)), add(p, (0, -1.2, 1.0))], [1.2, 0.3], 'brass', 'head')
    # ---- gear-tooth ear tufts: tall pointed brass tufts swept up and out,
    #      the outer edge cut into square cog teeth, a steel rivet at the root
    for s in (-1, 1):
        part = 'ear%d' % s
        root_i, root_o = (s * 3.2, 33.8, 1.0), (s * 6.4, 32.2, 0.6)
        tip = (s * 11.6, 44.0, -0.4)
        e = sub(tip, root_o)
        out = norm((abs(e[1]) * s, -abs(e[0]), 0))
        pts = [root_i, root_o]
        for t0, t1 in ((0.1, 0.28), (0.44, 0.62)):
            a0, a1 = lerp(root_o, tip, t0), lerp(root_o, tip, t1)
            pts += [a0, add(a0, mul(out, 2.4)), add(a1, mul(out, 2.4)), a1]
        pts.append(tip)
        if s < 0:
            pts = pts[::-1]
        m.poly(pts, 'brass', part, puff=0.4)
        m.paint(add(lerp(root_i, root_o, 0.5), (s * 0.8, 2.0, 0.8)), 1.0, 'steel', [part])
    # ---- a wind-up key in its back
    m.tube([(0, 19.0, -7.6), (0, 19.0, -11.4)], [1.0, 1.0], 'brass', 'key')
    for s in (-1, 1):
        m.ell((s * 2.6, 19.0, -11.8), (2.6, 2.0, 0.8), 'brass', 'key')
        m.paint((s * 2.9, 19.0, -11.8), (1.0, 0.8, 1.2), 'steel', ['key'])
    m.sph((0, 19.0, -11.8), 1.1, 'brass', 'key')
    return m


# ==========================================================================
# 149 CINDERANT  BLAZE/SWARM
# A dark-chitin fire ant, rearing, with ember rings round its gaster, huge
# hooked pincers and glowing seams between its plates.
# ==========================================================================
def cinderant(g):
    m = g.Model('CINDERANT')
    m.outline = (20, 10, 14)
    m.mat('chitin', ['#1c1418', '#36272c', '#584240', '#86685e'], spec=0.45)
    m.mat('ember', ['#e0420e', '#ff9c22', '#ffe266'], emissive=0.7)
    m.mat('rust', ['#8c3818', '#d0642a'])
    m.eye_dark = (20, 10, 14)
    m.white = (255, 226, 102)
    m.height = 50
    m.max_w = 62
    m.front_yaw = -26
    # ---- six legs splayed from the thorax, bent knees high
    for s in (-1, 1):
        for k, (zz, fz) in enumerate(((5.5, 11.0), (3.0, 3.0), (0.5, -6.0))):
            hip = (s * 2.6, 11.0, zz)
            knee = (s * 9.0, 12.5 - k * 0.6, (zz + fz) * 0.5 + (1.0 - k))
            foot = (s * 11.0, 0.8, fz)
            nm = 'leg%s%d' % ('FMB'[k], s)
            m.tube([hip, knee], [1.3, 1.0], 'chitin', nm)
            m.sph(knee, 1.15, 'chitin', nm)
            m.paint(knee, 0.7, 'ember', [nm])
            m.tube([knee, lerp(knee, foot, 0.6), foot], [1.0, 0.8, 0.45], 'chitin', nm)
    # ---- raised gaster ringed with embers
    gc, gr, grot = (0, 15.0, -9.0), (6.6, 6.2, 8.2), (0, 28, 0)
    m.ell(gc, gr, 'chitin', 'gaster', rot=grot)
    for k, t in enumerate((0.55, 0.05, -0.45)):
        c = add(gc, (0, -t * 3.6, t * 6.8))
        m.paint(c, (7.4, 7.0, 1.3), 'ember', ['gaster'], rot=grot)
    m.paint(add(gc, (0, -4.2, -6.0)), 2.0, 'ember', ['gaster'])
    # ---- waist node, armoured thorax with glowing seams
    m.sph((0, 12.0, -1.4), 1.9, 'chitin', 'waist')
    tc, tr = (0, 12.5, 3.6), (3.6, 3.4, 4.6)
    m.ell(tc, tr, 'chitin', 'thorax', rot=(0, -12, 0))
    m.ell((0, 15.0, 3.0), (3.0, 1.8, 3.0), 'chitin', 'thorax')
    for z in (1.6, 4.4):
        m.paint((0, 13.0, z), (4.2, 4.2, 0.4), 'ember', ['thorax'])
    # ---- head held high, big curved mandibles
    head_c, head_r = (0, 18.0, 10.4), (5.2, 4.8, 4.4)
    m.ell(head_c, head_r, 'chitin', 'head', rot=(0, -10, 0))
    m.paint((0, 22.4, 9.6), (0.5, 3.0, 4.0), 'ember', ['head'])
    # two big hooked pincers, splayed wide open so each reads on its own
    for s in (-1, 1):
        base = (s * 2.4, 15.0, 13.4)
        pts = [base, (s * 5.6, 14.0, 16.4), (s * 6.4, 11.2, 18.4), (s * 5.0, 9.0, 19.2),
               (s * 1.8, 9.4, 19.0)]
        m.tube(pts, [1.7, 1.6, 1.3, 0.95, 0.3], 'rust', 'jaw%d' % s,
               mats=[(0, 'rust'), (0.8, 'chitin')])
        # a saw tooth on the inner edge
        m.crystal((s * 5.8, 11.6, 18.4), (s * 3.8, 11.8, 18.8), 0.7, 'chitin',
                  'jaw%d' % s, sides=4, tip_frac=0.9)
        # elbowed antennae with glowing tips
        a0 = (s * 1.8, 21.8, 12.4)
        a1 = (s * 4.2, 27.0, 12.5)
        a2 = (s * 8.0, 29.0, 16.0)
        m.tube([a0, a1], [0.6, 0.55], 'chitin', 'ant%d' % s)
        m.tube([a1, lerp(a1, a2, 0.5), a2], [0.55, 0.6, 0.8], 'chitin', 'ant%d' % s)
        m.sph(a2, 1.0, 'ember', 'ant%d' % s)
    g.eye_pair(m, head_c, head_r, 48, 12, 3.4, 3.2, style='glow', iris=('ember', 1),
               glint=False, rot=(0, -10, 0), center=(0, 17, 16), turn=4)
    return m


# ==========================================================================
# 150 STARWEAVER  DREAM/SWARM
# An indigo spider sitting in the middle of a big round web; its abdomen is
# a two-armed spiral galaxy (a dark disc, bright arms, a glowing core) and
# the web's knots are stars, the brightest joined into a constellation.
# ==========================================================================
def starweaver(g):
    m = g.Model('STARWEAVER')
    m.outline = (16, 12, 44)
    m.mat('indigo', ['#1c1650', '#322a86', '#5048b8', '#8078e0'])
    m.mat('silk', ['#8a92d0', '#d4dafa'])
    m.mat('void', ['#0e0a26'])
    m.mat('arm', ['#3ab4f0', '#bff4ff'], emissive=0.6)
    m.mat('star', ['#ffc83a', '#fff6c4'], emissive=0.8)
    m.eye_dark = (14, 10, 40)
    m.white = (255, 250, 230)
    m.height = 58
    m.max_w = 62
    m.front_yaw = -12
    g.OW_TURN[m.name] = 0.0
    g.OW_SIDE_YAW[m.name] = -55.0
    # ---- the web: a big round orb web on a plane behind the spider,
    #      eight spokes and one ring of silk
    wc, wz, R = (0.0, 25.0), -3.5, 22.0

    def W(r, a, dz=0.0):
        return (wc[0] + math.cos(a * DEG) * r, wc[1] + math.sin(a * DEG) * r, wz + dz)
    spokes = [k * 45 + 22.5 for k in range(8)]
    # a disc of night sky stretched inside the web, so the silk reads as
    # bright threads instead of a tangle of holes at small sizes
    m.poly([W(18.6, a0) for a0 in spokes], 'void', 'web', puff=0.05)
    for a in spokes:
        m.tube([W(3.0, a), W(R, a)], [0.5, 0.45], 'silk', 'web')
    for rr in (19.0,):
        ring = [W(rr, spokes[k % 8]) for k in range(9)]
        for k in range(8):
            m.tube([ring[k], ring[k + 1]], [0.45, 0.45], 'silk', 'web')
    # ---- star knots, the brightest joined into a constellation arching over
    #      the top of the web
    knots = [W(19.0, 202.5, 0.4), W(13.0, 157.5, 0.4), W(19.0, 112.5, 0.4),
             W(13.0, 67.5, 0.4), W(19.0, 22.5, 0.4)]
    for a, b in zip(knots, knots[1:]):
        m.tube([add(a, (0, 0, 0.3)), add(b, (0, 0, 0.3))], [0.35, 0.35], 'star', 'stars')
    for q in knots:
        m.sph(q, 1.4, 'star', 'stars')
    for q in (W(R, -67.5, 0.4), W(R, -112.5, 0.4), W(12.0, -22.5, 0.4)):
        m.sparkle(q, (0, 0, 1), size=1, color='white')
    # ---- eight long jointed legs spread out over the web
    ceph = (0, 20.0, 1.0)
    for s in (-1, 1):
        for k, ang in enumerate((58, 24, -12, -46)):
            a = ang * DEG
            d = (s * math.cos(a), math.sin(a), 0)
            hip = add(ceph, mul(d, 2.8))
            knee = add(add(ceph, mul(d, 10.0)), (0, 3.4, 3.4))
            tip = add(add(ceph, mul(d, 19.0)), (0, -1.5, wz + 0.6 - ceph[2]))
            nm = 'leg%d%d' % (k, s)
            m.tube([hip, knee], [1.3, 1.0], 'indigo', nm)
            m.sph(knee, 1.15, 'indigo', nm)
            m.paint(add(knee, (0, 0.4, 0.3)), 0.7, 'arm', [nm])
            m.tube([knee, lerp(knee, tip, 0.55), tip], [1.0, 0.75, 0.45], 'indigo', nm)
    # ---- the galaxy abdomen: a dark disc facing out, two bright spiral arms
    #      wound round a glowing core
    ab_c, ab_r = (0, 28.5, -0.2), (7.4, 7.6, 4.6)
    m.ell(ab_c, ab_r, 'indigo', 'abdomen')
    m.paint(add(ab_c, (0, 0, 3.6)), (6.6, 6.8, 2.0), 'void', ['abdomen'])
    for arm in (0, 1):
        for i in range(16):
            t = i / 15.0
            a = arm * math.pi + t * 3.8 + 0.4
            r = 1.4 + t * 5.0
            x, y = math.cos(a) * r, math.sin(a) * r * 1.02
            dz = math.sqrt(max(0.05, 1.0 - (x / ab_r[0]) ** 2 - (y / ab_r[1]) ** 2))
            p = add(ab_c, (x, y, dz * ab_r[2]))
            m.paint(p, (1.3 - 0.55 * t, 1.3 - 0.55 * t, 1.6), 'arm', ['abdomen'])
        tip = arm * math.pi + 3.8 + 0.4
        q = add(ab_c, (math.cos(tip) * 6.4, math.sin(tip) * 6.5, 2.4))
        m.sparkle(q, (0, 0, 1), size=1, color='white')
    m.paint(add(ab_c, (0, 0, ab_r[2])), (1.9, 1.9, 1.6), 'star', ['abdomen'])
    # ---- cephalothorax and face: big starlit eyes, two small fangs
    m.ell(ceph, (4.6, 3.8, 3.8), 'indigo', 'body')
    head_c, head_r = (0, 18.4, 4.0), (4.6, 3.8, 3.4)
    m.ell(head_c, head_r, 'indigo', 'body')
    g.eye_pair(m, head_c, head_r, 32, 12, 3.8, 4.0, style='iris', iris=('arm', 0),
               center=(0, 18, 9), turn=2)
    for s in (-1, 1):
        p, n = g.on(head_c, head_r, (s * 0.3, 0.8, 0.55))
        m.paint(p, 0.75, 'star', ['body'])
        m.tube([(s * 1.2, 16.6, 6.4), (s * 1.0, 14.8, 7.0), (s * 0.5, 14.0, 6.8)],
               [0.85, 0.6, 0.25], 'indigo', 'fang%d' % s)
    return m


# ==========================================================================
# 151 NOSFERBAT  HOLLOW/GALE
# A vampire bat noble throwing its wing-cape wide open like a cloak: the
# finger bones are the cape's ribs, the crimson lining faces out; a high
# pointed collar, big ears, a pale face with red eyes and fangs, and a ruby
# brooch at the throat.
# ==========================================================================
def _cape_wing(m, s, shoulder, elbow, wrist, fingers, hip, part, sag=2.6):
    """One half of the wing-cape: crimson lining in front, dark fur behind,
    pale finger bones running over the lining as ribs."""
    pts = [shoulder, elbow, wrist, fingers[0]]
    for i in range(len(fingers) - 1):
        a, b = fingers[i], fingers[i + 1]
        pts.append(lerp(lerp(a, b, 0.5), wrist, sag / 10.0))
        pts.append(b)
    pts.append(lerp(lerp(fingers[-1], hip, 0.5), wrist, 0.18))
    pts.append(hip)
    m.poly([add(q, (0, 0, 0.5)) for q in pts], 'crimson', part, puff=0.2)
    m.poly([add(q, (0, 0, -0.5)) for q in pts], 'fur', part, puff=0.2)
    m.tube([shoulder, elbow, wrist], [1.5, 1.2, 1.1], 'fur', part)
    for f in fingers:
        m.tube([add(wrist, (0, 0, 0.7)), add(f, (0, 0, 0.7))], [0.7, 0.35], 'bone', part)
    m.sph(wrist, 1.2, 'fur', part)
    # the thumb claw hooks up off the wrist
    m.crystal(wrist, add(wrist, (s * 0.6, 3.4, 0.6)), 0.8, 'bone', part, sides=4,
              tip_frac=0.8)


def nosferbat(g):
    m = g.Model('NOSFERBAT')
    m.outline = (22, 12, 26)
    m.mat('fur', ['#1e1628', '#382a46', '#5a4666'])
    m.mat('crimson', ['#4c0818', '#8e1630', '#c83248'])
    m.mat('bone', ['#b8aa9a', '#f4ecdc'])
    m.mat('gold', ['#a87a22', '#f0d060'], spec=0.5)
    m.mat('ruby', ['#ff2c4c', '#ffb4bc'], emissive=0.55)
    m.eye_dark = (30, 22, 40)
    m.white = (255, 248, 236)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -16
    g.OW_TURN[m.name] = 0.0
    g.OW_SIDE_YAW[m.name] = -58.0
    # ---- short legs, clawed feet
    for s in (-1, 1):
        m.tube([(s * 2.4, 8.0, 0.0), (s * 2.6, 2.0, 0.6)], [1.7, 1.3], 'fur', 'leg%d' % s)
        for t in (-1, 0, 1):
            m.tube([(s * 2.6, 1.2, 0.8), (s * 2.6 + t * 1.0, 0.6, 3.0)], [0.6, 0.3],
                   'bone', 'leg%d' % s)
    # ---- torso in a dark waistcoat with a crimson front and gold buttons
    m.ell((0, 15.5, 0.0), (4.8, 8.0, 4.0), 'fur', 'body')
    m.paint((0, 16.0, 3.6), (2.0, 6.0, 1.6), 'crimson', ['body'])
    for y in (18.0, 14.8, 11.6):
        m.paint((0, y, 4.0), 0.55, 'gold', ['body'])
    # ---- the wing-cape thrown wide open: arms raised, fingers fanning
    #      down to a scalloped hem that sweeps the ground
    for s in (-1, 1):
        sh = (s * 4.2, 22.5, 0.0)
        el = (s * 11.0, 28.0, 0.6)
        wr = (s * 17.0, 31.0, 1.4)
        fingers = [(s * 26.0, 29.0, 2.6), (s * 27.5, 18.5, 3.0), (s * 24.5, 7.5, 2.8),
                   (s * 16.0, 1.6, 2.2)]
        _cape_wing(m, s, sh, el, wr, fingers, (s * 4.4, 3.0, 0.2), 'cape%d' % s)
    # ---- high collar: stiff pointed crimson wings behind the head
    for s in (-1, 1):
        col = [(s * 1.5, 22.5, 0.0), (s * 6.0, 23.0, 0.4), (s * 12.5, 35.5, -0.6),
               (s * 9.4, 37.0, -1.6), (s * 2.0, 32.0, -2.4)]
        m.poly(col, 'crimson', 'collar%d' % s, puff=0.3)
        m.poly([add(q, (0, 0, -0.8)) for q in col], 'fur', 'collar%d' % s, puff=0.3)
    # ---- ruby brooch at the throat
    m.ell((0, 21.6, 3.9), (2.0, 2.0, 0.8), 'gold', 'brooch')
    m.sph((0, 21.6, 4.5), 1.3, 'ruby', 'brooch')
    # ---- a big head: dark fur, a pale heart-shaped face, huge pointed ears
    head_c, head_r = (0, 30.0, 1.2), (6.8, 6.0, 5.4)
    m.ell(head_c, head_r, 'fur', 'head')
    p, n = g.on(head_c, head_r, (0, -0.05, 1))
    m.paint(add(p, (0, 0.6, -0.6)), (6.0, 4.8, 3.4), 'bone', ['head'])
    m.paint(add(p, (0, 4.4, -1.4)), (2.0, 2.0, 2.8), 'bone', ['head'])
    for s in (-1, 1):
        base = (s * 4.0, 33.4, 0.4)
        m.tube([base, (s * 6.0, 38.0, 0.6), (s * 7.4, 44.0, 0.4)], [2.9, 2.0, 0.2], 'fur',
               'ear%d' % s, flat=0.4, up=(s * 0.2, 0, 1))
        m.paint((s * 5.8, 37.8, 1.4), (1.2, 3.0, 1.0), 'crimson', ['ear%d' % s],
                rot=(0, 0, s * 18))
    # red eyes set in dark sockets so they glow against the pale face
    for s in (-1, 1):
        q, nq = g.on(head_c, head_r, (s * 0.62 + 0.05, 0.14, 1))
        m.dot(q, nq, w=2.6, h=2.4, minw=2, minh=2, color=('fur', 0))
    g.eye_pair(m, head_c, head_r, 36, 8, 3.8, 3.4, style='glow', iris=('ruby', 0),
               slant=0.5, pupil='outline', glint=False, center=(0, 30, 9), turn=3)
    # a small dark nose and a thin grin
    m.dot(g.on(head_c, head_r, (0.05, -0.18, 1))[0], (0, 0.1, 1), w=1.4, h=0.8, minw=2)
    p, n = g.on(head_c, head_r, (0.05, -0.42, 1))
    m.mouth(p, n, 'open', w=3.6, h=1.8, inner=('crimson', 0))
    for s in (-1, 1):
        m.crystal((s * 1.2, 27.0, 6.4), (s * 1.1, 24.6, 6.6), 0.6, 'bone', 'fang%d' % s,
                  sides=4, tip_frac=0.9)
    return m


# ---- end of batch ----
