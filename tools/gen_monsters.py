#!/usr/bin/env python3
"""Generate src/gfx_monsters.h: sprites for all 32 WILDKIN species (kin).

Every species is modelled as a handful of 3D primitives (ellipsoids, swept
tubes, flat polygons and faceted convex solids) and rendered with a tiny
orthographic z-buffer renderer:

  * supersampled rasterisation with per-pixel normals, paint volumes for
    markings and a light-space shadow map for cast shadows,
  * Lambert lighting from the top-left quantised onto hand-picked,
    hue-shifted 3-4 colour ramps,
  * a 1px hue-tinted silhouette outline plus interior lines wherever one body
    part occludes another,
  * eyes / mouths / noses stamped as crisp pixel-art decals (hidden on the
    back view automatically because they face away from the camera).

Per species it emits a 64x64 front sprite, a 64x64 back sprite (bigger,
cropped at the bottom edge like Emerald back sprites), a 32x32 menu icon and
six 32x32 overworld frames (down/up/left x 2-step walk), all sharing one
16-colour palette (index 0 = transparent), packed as GBA 4bpp tiles.
Standard library only.

    python3 tools/gen_monsters.py                    # write the header
    python3 tools/gen_monsters.py --preview DIR      # + contact sheet PNGs
    python3 tools/gen_monsters.py --only 0,1,2 --preview DIR
"""
import math
import os
import struct
import sys
import zlib

SS = 3                       # supersampling factor
WRAP = 0.42                  # wrap lighting amount
SHADOW_FLOOR = 0.20          # cast shadow never darker than this
SHADOW_SUB = 0.24            # intensity drop in cast shadow
DEG = math.pi / 180.0


# --------------------------------------------------------------------------
# vector helpers
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


def length(a):
    return math.sqrt(dot(a, a))


def norm(a):
    l = length(a)
    if l < 1e-12:
        return (0.0, 0.0, 1.0)
    return (a[0] / l, a[1] / l, a[2] / l)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t)


def mirror(p, s):
    """Mirror a model-space point to side s (+1 = creature's left / +X)."""
    return (p[0] * s, p[1], p[2])


def rot_matrix(yaw=0.0, pitch=0.0, roll=0.0):
    """M = Ry(yaw) * Rx(pitch) * Rz(roll), degrees.

    yaw>0 turns +Z toward +X, pitch>0 tips +Z down toward -Y,
    roll>0 turns +X toward +Y."""
    cy, sy = math.cos(yaw * DEG), math.sin(yaw * DEG)
    cp, sp = math.cos(pitch * DEG), math.sin(pitch * DEG)
    cr, sr = math.cos(roll * DEG), math.sin(roll * DEG)
    ry = ((cy, 0, sy), (0, 1, 0), (-sy, 0, cy))
    rx = ((1, 0, 0), (0, cp, -sp), (0, sp, cp))
    rz = ((cr, -sr, 0), (sr, cr, 0), (0, 0, 1))
    return mat_mul(ry, mat_mul(rx, rz))


def mat_mul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3))
                       for j in range(3)) for i in range(3))


def mat_apply(m, v):
    return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
            m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
            m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2])


def mat_t(m):
    return tuple(tuple(m[j][i] for j in range(3)) for i in range(3))


LIGHT = norm((-0.45, -0.55, 0.70))


# --------------------------------------------------------------------------
# colour helpers
# --------------------------------------------------------------------------
def hexrgb(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def to555(rgb):
    return tuple(max(0, min(31, int(round(c * 31.0 / 255.0)))) for c in rgb)


def from555(c5):
    return tuple((c << 3) | (c >> 2) for c in c5)


# --------------------------------------------------------------------------
# model description
# --------------------------------------------------------------------------
class Model:
    """A creature: primitives + paint volumes + face decals + palette."""

    def __init__(self, name):
        self.name = name
        self.prims = []
        self.paints = []
        self.decals = []
        self.mats = {}          # name -> dict(colors=[rgb...], emissive=, th=)
        self.mat_order = []
        self.outline = (40, 24, 32)
        self.white = (255, 255, 248)
        self.eye_dark = (24, 20, 36)
        self.height = 36        # front silhouette height in px
        self.max_w = 60
        self.back_scale = 1.30
        self.back_show = 0.82   # fraction of back sprite height visible
        self.back_min_vis = 34  # px of back sprite visible at least
        self.icon_h = 26
        self.icon_w = 27
        self.line_depth = 1.6   # depth jump (px) that triggers inner lines
        self.line_mode = 'dark'
        self.groups = {}        # part -> line group
        self.front_yaw = -30.0
        self.front_pitch = 10.0
        self.back_yaw = 140.0
        self.back_pitch = 22.0
        self.float_lift = 0     # px lift for floating creatures
        self.dither = 0.0
        self._auto = 0
        self.shadows = True
        self.cov = 4            # coverage threshold (of SS*SS samples)
        self.icon_cov = 4
        self.ow_offsets = {}    # part -> translation, overworld frames only

    # ---- palette ------------------------------------------------------
    def mat(self, name, colors, emissive=0.0, th=None, spec=0.0):
        cols = [hexrgb(c) if isinstance(c, str) else c for c in colors]
        self.mats[name] = dict(colors=cols, emissive=emissive, th=th,
                               spec=spec)
        if name not in self.mat_order:
            self.mat_order.append(name)

    def group(self, *parts):
        g = parts[0]
        for p in parts:
            self.groups[p] = g

    def _part(self, part):
        if part is None:
            self._auto += 1
            return '_p%d' % self._auto
        return part

    # ---- primitives ---------------------------------------------------
    def sph(self, c, r, mat, part=None):
        part = self._part(part)
        self.prims.append(('S', tuple(c), float(r), mat, part))
        return part

    def ell(self, c, r, mat, part=None, rot=None):
        part = self._part(part)
        if isinstance(r, (int, float)):
            r = (r, r, r)
        m = rot_matrix(*rot) if rot else ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        axes = (mat_apply(m, (r[0], 0, 0)), mat_apply(m, (0, r[1], 0)),
                mat_apply(m, (0, 0, r[2])))
        self.prims.append(('E', tuple(c), axes, mat, part))
        return part

    def ell_axes(self, c, axes, mat, part=None):
        part = self._part(part)
        self.prims.append(('E', tuple(c), tuple(axes), mat, part))
        return part

    def tube(self, pts, radii, mat, part=None, flat=1.0, up=None, mats=None,
             step=0.22, rfn=None):
        """Swept sphere (or flattened ellipsoid) along a Catmull-Rom curve.

        radii: one per control point (linear in between) or rfn(t) with t
        the normalised arc length.  flat<1 squashes the cross section along
        `up` (a model-space direction) - for ears, fins, leaves, flames.
        mats: [(t0, mat0), (t1, mat1), ...] changes material along the tube.
        """
        part = self._part(part)
        pts = [tuple(p) for p in pts]
        dense = catmull(pts)
        # arc length
        cum = [0.0]
        for i in range(1, len(dense)):
            cum.append(cum[-1] + length(sub(dense[i][0], dense[i - 1][0])))
        total = max(cum[-1], 1e-6)
        if isinstance(radii, (int, float)):
            radii = [radii] * len(pts)
        if radii is None:
            radii = [1.0] * len(pts)

        def radius_at(i_dense, frac_t):
            if rfn is not None:
                return rfn(frac_t)
            u = dense[i_dense][1]
            k = min(int(u), len(pts) - 2) if len(pts) > 1 else 0
            f = u - k
            if len(pts) == 1:
                return radii[0]
            return radii[k] + (radii[k + 1] - radii[k]) * f

        def mat_at(t):
            m = mat
            if mats:
                for t0, mm in mats:
                    if t >= t0:
                        m = mm
            return m

        s = 0.0
        j = 0
        out = []
        while True:
            while j < len(cum) - 2 and cum[j + 1] < s:
                j += 1
            seg = max(cum[j + 1] - cum[j], 1e-9)
            f = min(1.0, max(0.0, (s - cum[j]) / seg))
            p = lerp(dense[j][0], dense[j + 1][0], f)
            tng = norm(sub(dense[j + 1][0], dense[j][0]))
            t = s / total
            r = radius_at(j, t)
            out.append((p, tng, max(r, 0.05), mat_at(t)))
            if s >= total:
                break
            s = min(total, s + max(0.06, step * max(r, 0.3)))
        for p, tng, r, m in out:
            if flat >= 0.999:
                self.prims.append(('S', p, r, m, part))
            else:
                upv = up if up is not None else (0, 0, 1)
                fn = sub(upv, mul(tng, dot(upv, tng)))
                if length(fn) < 1e-6:
                    fn = cross(tng, (1, 0, 0))
                fn = norm(fn)
                b = norm(cross(tng, fn))
                self.prims.append(('E', p, (mul(tng, r), mul(b, r),
                                            mul(fn, r * flat)), m, part))
        return part

    def poly(self, pts, mat, part=None, puff=0.5, spine=None):
        part = self._part(part)
        self.prims.append(('P', [tuple(p) for p in pts], mat, part, puff,
                           spine))
        return part

    def hull(self, planes, center, radius, mat, part=None):
        part = self._part(part)
        self.prims.append(('H', planes, tuple(center), radius, mat, part))
        return part

    def rock(self, c, r, mat, part=None, seed=1, rot=None, n=16, jitter=0.10,
             shrink=0.93):
        if isinstance(r, (int, float)):
            r = (r, r, r)
        m = rot_matrix(*rot) if rot else ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        rnd = Rand(seed)
        planes = []
        ga = math.pi * (3 - math.sqrt(5))
        off = rnd.f() * 6.28
        for i in range(n):
            y = 1 - 2 * (i + 0.5) / n
            rad = math.sqrt(max(0, 1 - y * y))
            th = ga * i + off
            d = (math.cos(th) * rad, y, math.sin(th) * rad)
            d = norm(add(d, (rnd.f() * 0.25 - 0.125, rnd.f() * 0.25 - 0.125,
                             rnd.f() * 0.25 - 0.125)))
            sup = math.sqrt((r[0] * d[0]) ** 2 + (r[1] * d[1]) ** 2 +
                            (r[2] * d[2]) ** 2)
            sup *= shrink * (1 - jitter * rnd.f())
            nw = mat_apply(m, d)
            planes.append((nw, sup + dot(nw, c)))
        return self.hull(planes, c, max(r) * 1.25, mat, part)

    def box(self, c, half, mat, part=None, rot=None, bevel=0.3):
        m = rot_matrix(*rot) if rot else ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        hx, hy, hz = half
        planes = []
        for d, h in (((1, 0, 0), hx), ((-1, 0, 0), hx), ((0, 1, 0), hy),
                     ((0, -1, 0), hy), ((0, 0, 1), hz), ((0, 0, -1), hz)):
            planes.append((d, h))
        if bevel > 0:
            s2 = 1 / math.sqrt(2)
            for sx in (-1, 1):
                for sy in (-1, 1):
                    planes.append(((sx * s2, sy * s2, 0), (hx + hy - bevel) * s2))
                    planes.append(((sx * s2, 0, sy * s2), (hx + hz - bevel) * s2))
                    planes.append(((0, sx * s2, sy * s2), (hy + hz - bevel) * s2))
            s3 = 1 / math.sqrt(3)
            for sx in (-1, 1):
                for sy in (-1, 1):
                    for sz in (-1, 1):
                        planes.append(((sx * s3, sy * s3, sz * s3),
                                       (hx + hy + hz - 1.7 * bevel) * s3))
        wp = []
        for d, h in planes:
            nw = mat_apply(m, d)
            wp.append((nw, h + dot(nw, c)))
        return self.hull(wp, c, math.sqrt(hx * hx + hy * hy + hz * hz) + 0.5,
                         mat, part)

    def crystal(self, base, tip, r, mat, part=None, sides=6, tip_frac=0.35,
                twist=0.0):
        a = norm(sub(tip, base))
        L = length(sub(tip, base))
        u = norm(cross(a, (0.3, 0.9, 0.2) if abs(a[1]) < 0.9 else (1, 0, 0)))
        v = cross(a, u)
        planes = [(mul(a, -1), -dot(a, base))]
        ht = L * tip_frac
        for k in range(sides):
            ang = 2 * math.pi * k / sides + twist * DEG
            d = add(mul(u, math.cos(ang)), mul(v, math.sin(ang)))
            planes.append((d, r + dot(d, base)))
            n = norm(add(mul(d, ht), mul(a, r)))
            planes.append((n, dot(n, tip)))
        c = lerp(base, tip, 0.5)
        return self.hull(planes, c, L / 2 + r + 0.5, mat, part)

    # ---- markings / decals -------------------------------------------
    def paint(self, c, r, mat, parts=None, rot=None):
        if isinstance(r, (int, float)):
            r = (r, r, r)
        m = rot_matrix(*rot) if rot else ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        axes = (mat_apply(m, (r[0], 0, 0)), mat_apply(m, (0, r[1], 0)),
                mat_apply(m, (0, 0, r[2])))
        if isinstance(parts, str):
            parts = [parts]
        self.paints.append((tuple(c), axes, mat,
                            set(parts) if parts else None))

    def eye(self, pos, nrm, w, h, style='cute', iris=None, slant=0.0,
            look=-1, glint=True, lid=0, minw=2, minh=2, pupil=None,
            center=None):
        self.decals.append(dict(kind='eye', pos=tuple(pos), nrm=norm(nrm),
                                w=w, h=h, style=style, iris=iris,
                                slant=slant, look=look, glint=glint,
                                lid=lid, minw=minw, minh=minh, pupil=pupil,
                                center=center))

    def mouth(self, pos, nrm, kind='smile', w=3.0, h=2.0, color='outline',
              inner=None, minw=2, fang=0):
        self.decals.append(dict(kind='mouth', pos=tuple(pos), nrm=norm(nrm),
                                mk=kind, w=w, h=h, color=color, inner=inner,
                                minw=minw, fang=fang))

    def dot(self, pos, nrm, w=1.0, h=1.0, color='outline', minw=1, minh=1,
            shape='rect'):
        self.decals.append(dict(kind='dot', pos=tuple(pos), nrm=norm(nrm),
                                w=w, h=h, color=color, minw=minw, minh=minh,
                                shape=shape))

    def sparkle(self, pos, nrm, size=2, color='white'):
        self.decals.append(dict(kind='sparkle', pos=tuple(pos),
                                nrm=norm(nrm), size=size, color=color))


def seedball(m, c, r, mat, part, n=70, fil=0.30, tip=0.55, seed=3,
             skip_below=-2.0, rot=None, core_mat=None, skip_dir=None):
    """Dandelion clock: a soft ball with fine radiating seed filaments that
    give the silhouette a fuzzy starburst edge."""
    if isinstance(r, (int, float)):
        r = (r, r, r)
    m.ell(c, r, core_mat or mat, part, rot=rot)
    rnd = Rand(seed)
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n
        rad = math.sqrt(max(0, 1 - y * y))
        th = ga * i + rnd.f() * 0.4
        d = (math.cos(th) * rad, y, math.sin(th) * rad)
        if d[1] < skip_below:
            continue
        if skip_dir is not None and dot(d, norm(skip_dir[0])) > skip_dir[1]:
            continue
        p0, nn = surf(c, r, d, rot)
        ln = (0.9 + 0.5 * rnd.f()) * (r[0] + r[1] + r[2]) / 3.0 * fil
        p1 = add(p0, mul(nn, ln))
        m.tube([add(p0, mul(nn, -0.4)), p1], [0.42, 0.3], mat, part)
        m.sph(p1, tip * (0.8 + 0.4 * rnd.f()), mat, part)


def surf(c, r, d, rot=None):
    """Point + normal on an ellipsoid surface along model direction d."""
    if isinstance(r, (int, float)):
        r = (r, r, r)
    m = rot_matrix(*rot) if rot else ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    mt = mat_t(m)
    dl = mat_apply(mt, norm(d))
    t = 1.0 / math.sqrt((dl[0] / r[0]) ** 2 + (dl[1] / r[1]) ** 2 +
                        (dl[2] / r[2]) ** 2)
    pl = mul(dl, t)
    nl = (pl[0] / r[0] ** 2, pl[1] / r[1] ** 2, pl[2] / r[2] ** 2)
    return add(c, mat_apply(m, pl)), norm(mat_apply(m, nl))


class Rand:
    def __init__(self, seed):
        self.s = (seed * 2654435761 + 12345) & 0x7fffffff

    def f(self):
        self.s = (self.s * 1103515245 + 12345) & 0x7fffffff
        return (self.s >> 8) / float(1 << 23)


def catmull(pts, nsub=12):
    """Dense polyline [(point, u)] through pts (u = control index + frac)."""
    if len(pts) == 1:
        return [(pts[0], 0.0), (pts[0], 0.0)]
    P = [sub(mul(pts[0], 2), pts[1])] + list(pts) + \
        [sub(mul(pts[-1], 2), pts[-2])]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(nsub):
            t = k / float(nsub)
            t2, t3 = t * t, t * t * t
            pt = tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t +
                              (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 +
                              (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3)
                       for j in range(3))
            out.append((pt, (i - 1) + t))
    out.append((pts[-1], float(len(pts) - 1)))
    return out


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------
class View:
    def __init__(self, yaw, pitch, scale, ox, oy, ss):
        self.ca, self.sa = math.cos(yaw * DEG), math.sin(yaw * DEG)
        self.cp, self.sp = math.cos(pitch * DEG), math.sin(pitch * DEG)
        self.S = scale * ss
        self.ox = ox * ss
        self.oy = oy * ss
        self.ss = ss

    def g(self, v):
        x, y, z = v
        x1 = x * self.ca + z * self.sa
        z1 = -x * self.sa + z * self.ca
        y2 = y * self.cp - z1 * self.sp
        z2 = y * self.sp + z1 * self.cp
        return (x1, -y2, z2)

    def p(self, v):
        g = self.g(v)
        return (g[0] * self.S + self.ox, g[1] * self.S + self.oy,
                g[2] * self.S)

    def vec(self, v):
        g = self.g(v)
        return (g[0] * self.S, g[1] * self.S, g[2] * self.S)


def compile_prims(model, view, mat_ids, part_ids):
    """Model-space prims -> view-space prims (tuples ready for raster)."""
    out = []
    for pr in model.prims:
        k = pr[0]
        if k == 'S':
            _, c, r, mat, part = pr
            out.append(('S', view.p(c), r * view.S, mat_ids[mat],
                        part_ids[part]))
        elif k == 'E':
            _, c, axes, mat, part = pr
            out.append(('E', view.p(c), tuple(view.vec(a) for a in axes),
                        mat_ids[mat], part_ids[part]))
        elif k == 'P':
            _, pts, mat, part, puff, spine = pr
            sp = None
            if spine:
                sp = (view.p(spine[0]), view.p(spine[1]))
            out.append(('P', [view.p(q) for q in pts], mat_ids[mat],
                        part_ids[part], puff, sp))
        elif k == 'H':
            _, planes, c, rad, mat, part = pr
            vp = []
            for n, d in planes:
                n2 = view.g(n)
                p0 = view.p(mul(n, d))
                vp.append((n2, dot(n2, p0)))
            out.append(('H', vp, view.p(c), rad * view.S, mat_ids[mat],
                        part_ids[part]))
    return out


def transform_prims(prims, Q, o):
    """Apply rotation Q (rows) + offset o to view-space prims."""
    def tp(v):
        return (dot(Q[0], v) + o[0], dot(Q[1], v) + o[1], dot(Q[2], v) + o[2])

    def tv(v):
        return (dot(Q[0], v), dot(Q[1], v), dot(Q[2], v))
    out = []
    for pr in prims:
        k = pr[0]
        if k == 'S':
            out.append(('S', tp(pr[1]), pr[2], pr[3], pr[4]))
        elif k == 'E':
            out.append(('E', tp(pr[1]), tuple(tv(a) for a in pr[2]), pr[3],
                        pr[4]))
        elif k == 'P':
            sp = None
            if pr[5]:
                sp = (tp(pr[5][0]), tp(pr[5][1]))
            out.append(('P', [tp(q) for q in pr[1]], pr[2], pr[3], pr[4], sp))
        elif k == 'H':
            vp = []
            for n, d in pr[1]:
                n2 = tv(n)
                vp.append((n2, d + dot(n2, o)))
            out.append(('H', vp, tp(pr[2]), pr[3], pr[4], pr[5]))
    return out


def prim_bounds(pr):
    k = pr[0]
    if k == 'S':
        c, r = pr[1], pr[2]
        return (c[0] - r, c[1] - r, c[0] + r, c[1] + r)
    if k == 'E':
        c, ax = pr[1], pr[2]
        ex = math.sqrt(sum(a[0] * a[0] for a in ax))
        ey = math.sqrt(sum(a[1] * a[1] for a in ax))
        return (c[0] - ex, c[1] - ey, c[0] + ex, c[1] + ey)
    if k == 'P':
        xs = [q[0] for q in pr[1]]
        ys = [q[1] for q in pr[1]]
        return (min(xs), min(ys), max(xs), max(ys))
    if k == 'H':
        c, r = pr[2], pr[3]
        return (c[0] - r, c[1] - r, c[0] + r, c[1] + r)


class Buffers:
    def __init__(self, W, H, full=True):
        self.W, self.H = W, H
        n = W * H
        self.depth = [-1e30] * n
        self.part = [-1] * n
        if full:
            self.nx = [0.0] * n
            self.ny = [0.0] * n
            self.nz = [1.0] * n
            self.mat = [0] * n


def compile_paints(model, view, mat_ids, part_ids):
    out = []
    for c, axes, mat, parts in model.paints:
        cv = view.p(c)
        av = [view.vec(a) for a in axes]
        w = []
        for a in av:
            l2 = dot(a, a)
            w.append((a[0] / l2, a[1] / l2, a[2] / l2))
        ex = math.sqrt(sum(a[0] * a[0] for a in av))
        ey = math.sqrt(sum(a[1] * a[1] for a in av))
        pset = None if parts is None else set(part_ids[p] for p in parts
                                              if p in part_ids)
        out.append((cv, w, mat_ids[mat], pset,
                    (cv[0] - ex, cv[1] - ey, cv[0] + ex, cv[1] + ey)))
    return out


def raster(prims, buf, paints=None):
    W, H = buf.W, buf.H
    depth, part = buf.depth, buf.part
    full = hasattr(buf, 'nx')
    sqrt = math.sqrt
    for pr in prims:
        k = pr[0]
        bx0, by0, bx1, by1 = prim_bounds(pr)
        x0 = max(0, int(bx0) - 1)
        y0 = max(0, int(by0) - 1)
        x1 = min(W - 1, int(bx1) + 1)
        y1 = min(H - 1, int(by1) + 1)
        if x0 > x1 or y0 > y1:
            continue
        if k == 'P':
            pid, mid = pr[3], pr[2]
        elif k == 'H':
            pid, mid = pr[5], pr[4]
        else:
            pid, mid = pr[4], pr[3]
        pl = []
        if full and paints:
            for pv in paints:
                if pv[3] is not None and pid not in pv[3]:
                    continue
                b = pv[4]
                if b[2] < bx0 or b[0] > bx1 or b[3] < by0 or b[1] > by1:
                    continue
                pl.append(pv)

        def paint_mat(px, py, pz, m):
            for cv, w, pm, _, _ in pl:
                dx, dy, dz = px - cv[0], py - cv[1], pz - cv[2]
                q1 = w[0][0] * dx + w[0][1] * dy + w[0][2] * dz
                q2 = w[1][0] * dx + w[1][1] * dy + w[1][2] * dz
                q3 = w[2][0] * dx + w[2][1] * dy + w[2][2] * dz
                if q1 * q1 + q2 * q2 + q3 * q3 <= 1.0:
                    m = pm
            return m

        if k == 'S':
            (cx, cy, cz), r = pr[1], pr[2]
            r2 = r * r
            ir = 1.0 / r
            for y in range(y0, y1 + 1):
                dy = y + 0.5 - cy
                dy2 = dy * dy
                if dy2 > r2:
                    continue
                row = y * W
                for x in range(x0, x1 + 1):
                    dx = x + 0.5 - cx
                    d2 = r2 - dx * dx - dy2
                    if d2 < 0:
                        continue
                    dz = sqrt(d2)
                    z = cz + dz
                    idx = row + x
                    if z <= depth[idx]:
                        continue
                    depth[idx] = z
                    part[idx] = pid
                    if full:
                        buf.nx[idx] = dx * ir
                        buf.ny[idx] = dy * ir
                        buf.nz[idx] = dz * ir
                        buf.mat[idx] = paint_mat(x + 0.5, y + 0.5, z, mid) \
                            if pl else mid
        elif k == 'E':
            c = pr[1]
            ax = pr[2]
            w = []
            for a in ax:
                l2 = dot(a, a)
                w.append((a[0] / l2, a[1] / l2, a[2] / l2))
            (w1x, w1y, w1z), (w2x, w2y, w2z), (w3x, w3y, w3z) = w
            b1 = -(w1x * c[0] + w1y * c[1] + w1z * c[2])
            b2 = -(w2x * c[0] + w2y * c[1] + w2z * c[2])
            b3 = -(w3x * c[0] + w3y * c[1] + w3z * c[2])
            kk = w1z * w1z + w2z * w2z + w3z * w3z
            if kk < 1e-12:
                continue
            for y in range(y0, y1 + 1):
                py = y + 0.5
                r1 = w1y * py + b1
                r2 = w2y * py + b2
                r3 = w3y * py + b3
                row = y * W
                for x in range(x0, x1 + 1):
                    px = x + 0.5
                    q1 = w1x * px + r1
                    q2 = w2x * px + r2
                    q3 = w3x * px + r3
                    bb = q1 * w1z + q2 * w2z + q3 * w3z
                    cc = q1 * q1 + q2 * q2 + q3 * q3 - 1.0
                    disc = bb * bb - kk * cc
                    if disc < 0:
                        continue
                    z = (-bb + sqrt(disc)) / kk
                    idx = row + x
                    if z <= depth[idx]:
                        continue
                    depth[idx] = z
                    part[idx] = pid
                    if full:
                        q1 += z * w1z
                        q2 += z * w2z
                        q3 += z * w3z
                        nx = q1 * w1x + q2 * w2x + q3 * w3x
                        ny = q1 * w1y + q2 * w2y + q3 * w3y
                        nz = q1 * w1z + q2 * w2z + q3 * w3z
                        il = 1.0 / (sqrt(nx * nx + ny * ny + nz * nz) + 1e-12)
                        buf.nx[idx] = nx * il
                        buf.ny[idx] = ny * il
                        buf.nz[idx] = nz * il
                        buf.mat[idx] = paint_mat(px, py, z, mid) if pl else mid
        elif k == 'P':
            pts = pr[1]
            puff, spine = pr[4], pr[5]
            # Newell normal
            n = [0.0, 0.0, 0.0]
            m = len(pts)
            for i in range(m):
                a, b = pts[i], pts[(i + 1) % m]
                n[0] += (a[1] - b[1]) * (a[2] + b[2])
                n[1] += (a[2] - b[2]) * (a[0] + b[0])
                n[2] += (a[0] - b[0]) * (a[1] + b[1])
            n = norm(n)
            if abs(n[2]) < 0.02:
                continue
            cen = mul(tuple(sum(q[j] for q in pts) for j in range(3)), 1.0 / m)
            d = dot(n, cen)
            R = max(length(sub(q, cen)) for q in pts) + 1e-6
            if n[2] < 0:
                n = mul(n, -1)
                d = -d
            poly2 = [(q[0], q[1]) for q in pts]
            if spine:
                sa, sb = spine
                sd = sub(sb, sa)
                sl2 = max(dot(sd, sd), 1e-9)
            for y in range(y0, y1 + 1):
                py = y + 0.5
                # scanline crossings
                xs = []
                for i in range(m):
                    ax_, ay_ = poly2[i]
                    bx_, by_ = poly2[(i + 1) % m]
                    if (ay_ <= py < by_) or (by_ <= py < ay_):
                        xs.append(ax_ + (py - ay_) * (bx_ - ax_) / (by_ - ay_))
                if not xs:
                    continue
                xs.sort()
                row = y * W
                for s in range(0, len(xs) - 1, 2):
                    xa = max(x0, int(math.ceil(xs[s] - 0.5)))
                    xb = min(x1, int(math.floor(xs[s + 1] - 0.5)))
                    for x in range(xa, xb + 1):
                        px = x + 0.5
                        z = (d - n[0] * px - n[1] * py) / n[2]
                        idx = row + x
                        if z <= depth[idx]:
                            continue
                        depth[idx] = z
                        part[idx] = pid
                        if full:
                            p = (px, py, z)
                            if spine:
                                t = dot(sub(p, sa), sd) / sl2
                                off = sub(p, add(sa, mul(sd, t)))
                            else:
                                off = sub(p, cen)
                            nn = norm(add(n, mul(off, puff / R)))
                            if nn[2] < 0.05:
                                nn = norm((nn[0], nn[1], 0.05))
                            buf.nx[idx], buf.ny[idx], buf.nz[idx] = nn
                            buf.mat[idx] = paint_mat(px, py, z, mid) \
                                if pl else mid
        elif k == 'H':
            planes = pr[1]
            ups = []
            lows = []
            sides = []
            for (nx, ny, nz), d in planes:
                if nz > 1e-6:
                    ups.append((nx / nz, ny / nz, d / nz, (nx, ny, nz)))
                elif nz < -1e-6:
                    lows.append((nx / nz, ny / nz, d / nz))
                else:
                    sides.append((nx, ny, d))
            if not ups:
                continue
            for y in range(y0, y1 + 1):
                py = y + 0.5
                row = y * W
                for x in range(x0, x1 + 1):
                    px = x + 0.5
                    ok = True
                    for sx, sy, sd in sides:
                        if sx * px + sy * py > sd:
                            ok = False
                            break
                    if not ok:
                        continue
                    zmax = 1e30
                    best = None
                    for ax_, ay_, ad, nn in ups:
                        zu = ad - ax_ * px - ay_ * py
                        if zu < zmax:
                            zmax = zu
                            best = nn
                    zmin = -1e30
                    for ax_, ay_, ad in lows:
                        zl = ad - ax_ * px - ay_ * py
                        if zl > zmin:
                            zmin = zl
                    if zmax < zmin:
                        continue
                    idx = row + x
                    if zmax <= depth[idx]:
                        continue
                    depth[idx] = zmax
                    part[idx] = pid
                    if full:
                        buf.nx[idx], buf.ny[idx], buf.nz[idx] = best
                        buf.mat[idx] = paint_mat(px, py, zmax, mid) \
                            if pl else mid


def light_basis():
    l = LIGHT
    u = norm(cross((0, 1, 0), l))
    v = cross(l, u)
    return (u, v, l)


def render(model, yaw, pitch, scale, ox, oy, fw, fh, ss=SS, icon=False):
    """Render one view into final-resolution buffers + palette indices."""
    mat_ids = {n: i for i, n in enumerate(model.mat_order)}
    parts = []
    for pr in model.prims:
        p = pr[5] if pr[0] == 'H' else (pr[3] if pr[0] == 'P' else pr[4])
        if p not in parts:
            parts.append(p)
    part_ids = {p: i for i, p in enumerate(parts)}
    group_of = [part_ids.get(model.groups.get(p, p), part_ids[p])
                for p in parts]
    view = View(yaw, pitch, scale, ox, oy, ss)
    vprims = compile_prims(model, view, mat_ids, part_ids)
    paints = compile_paints(model, view, mat_ids, part_ids)
    W, H = fw * ss, fh * ss
    buf = Buffers(W, H, True)
    raster(vprims, buf, paints)

    # ---- shadow map in light space
    shadow = None
    if model.shadows:
        Q = light_basis()
        lp = transform_prims(vprims, Q, (0, 0, 0))
        bx0 = by0 = 1e30
        bx1 = by1 = -1e30
        for pr in lp:
            b = prim_bounds(pr)
            bx0, by0 = min(bx0, b[0]), min(by0, b[1])
            bx1, by1 = max(bx1, b[2]), max(by1, b[3])
        o = (-bx0 + 2, -by0 + 2, 0)
        lp = transform_prims(vprims, Q, o)
        LW = int(bx1 - bx0) + 5
        LH = int(by1 - by0) + 5
        lbuf = Buffers(LW, LH, False)
        raster(lp, lbuf)
        shadow = (Q, o, lbuf)

    # ---- per-sample intensity
    n = W * H
    inten = [0.0] * n
    Lx, Ly, Lz = LIGHT
    emis = [model.mats[nm]['emissive'] for nm in model.mat_order]
    spec = [model.mats[nm]['spec'] for nm in model.mat_order]
    Hh = norm(add(LIGHT, (0, 0, 1)))
    bias = 1.2 * ss
    for idx in range(n):
        pid = buf.part[idx]
        if pid < 0:
            continue
        nx, ny, nz = buf.nx[idx], buf.ny[idx], buf.nz[idx]
        lam = nx * Lx + ny * Ly + nz * Lz
        I = (lam + WRAP) / (1.0 + WRAP)
        if I < 0:
            I = 0.0
        if shadow is not None:
            Q, o, lbuf = shadow
            x = idx % W + 0.5
            y = idx // W + 0.5
            z = buf.depth[idx]
            lu = Q[0][0] * x + Q[0][1] * y + Q[0][2] * z + o[0]
            lv = Q[1][0] * x + Q[1][1] * y + Q[1][2] * z + o[1]
            ld = Q[2][0] * x + Q[2][1] * y + Q[2][2] * z
            iu, iv = int(lu), int(lv)
            if 0 <= iu < lbuf.W and 0 <= iv < lbuf.H:
                li = iv * lbuf.W + iu
                if lbuf.depth[li] > ld + bias and \
                        group_of[lbuf.part[li]] != group_of[pid]:
                    I = min(I, max(SHADOW_FLOOR, I - SHADOW_SUB))
        m = buf.mat[idx]
        if spec[m] > 0:
            sd = nx * Hh[0] + ny * Hh[1] + nz * Hh[2]
            if sd > 0:
                I += spec[m] * sd ** 24
        if emis[m] > 0:
            I = I * (1 - emis[m]) + emis[m]
        inten[idx] = I

    # ---- downsample to final pixels
    fn = fw * fh
    solid = [False] * fn
    fpart = [-1] * fn
    fmat = [0] * fn
    fint = [0.0] * fn
    fdep = [0.0] * fn
    cov = model.icon_cov if icon else model.cov
    for fy in range(fh):
        for fx in range(fw):
            cnt = {}
            tot = 0
            for sy in range(ss):
                row = (fy * ss + sy) * W + fx * ss
                for sx in range(ss):
                    idx = row + sx
                    p = buf.part[idx]
                    if p < 0:
                        continue
                    tot += 1
                    e = cnt.get(p)
                    if e is None:
                        cnt[p] = [idx]
                    else:
                        e.append(idx)
            if tot < cov:
                continue
            best = None
            bestk = None
            for p, lst in cnt.items():
                key = (len(lst), sum(buf.depth[i] for i in lst) / len(lst))
                if bestk is None or key > bestk:
                    bestk, best = key, p
            lst = cnt[best]
            mc = {}
            for i in lst:
                mc[buf.mat[i]] = mc.get(buf.mat[i], 0) + 1
            m = max(mc.items(), key=lambda kv: kv[1])[0]
            ii = [i for i in lst if buf.mat[i] == m]
            f = fy * fw + fx
            solid[f] = True
            fpart[f] = best
            fmat[f] = m
            fint[f] = sum(inten[i] for i in ii) / len(ii)
            fdep[f] = sum(buf.depth[i] for i in lst) / len(lst) / ss

    return dict(fw=fw, fh=fh, solid=solid, part=fpart, mat=fmat, inten=fint,
                depth=fdep, group=group_of, view=view, zbuf=buf, W=W,
                mat_ids=mat_ids, part_ids=part_ids)


def measure(model, yaw, pitch):
    """Projected silhouette extents in model units (x0, y0, x1, y1)."""
    mat_ids = {n: i for i, n in enumerate(model.mat_order)}
    part_ids = {}
    for pr in model.prims:
        p = pr[5] if pr[0] == 'H' else (pr[3] if pr[0] == 'P' else pr[4])
        part_ids.setdefault(p, len(part_ids))
    s0 = 4.0
    view = View(yaw, pitch, s0, 0, 0, 1)
    vp = compile_prims(model, view, mat_ids, part_ids)
    bx0 = by0 = 1e30
    bx1 = by1 = -1e30
    for pr in vp:
        b = prim_bounds(pr)
        bx0, by0 = min(bx0, b[0]), min(by0, b[1])
        bx1, by1 = max(bx1, b[2]), max(by1, b[3])
    o = (-bx0 + 2, -by0 + 2, 0)
    I3 = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    vp = transform_prims(vp, I3, o)
    W = int(bx1 - bx0) + 5
    H = int(by1 - by0) + 5
    buf = Buffers(W, H, False)
    raster(vp, buf)
    xs0 = ys0 = 10 ** 9
    xs1 = ys1 = -10 ** 9
    for y in range(H):
        row = y * W
        for x in range(W):
            if buf.part[row + x] >= 0:
                if x < xs0:
                    xs0 = x
                if x > xs1:
                    xs1 = x
                if y < ys0:
                    ys0 = y
                if y > ys1:
                    ys1 = y
    return ((xs0 - o[0]) / s0, (ys0 - o[1]) / s0, (xs1 + 1 - o[0]) / s0,
            (ys1 + 1 - o[1]) / s0)


# --------------------------------------------------------------------------
# palette + post-processing
# --------------------------------------------------------------------------
DEFAULT_TH = {1: [], 2: [0.45], 3: [0.33, 0.74], 4: [0.16, 0.45, 0.78],
              5: [0.16, 0.36, 0.58, 0.84]}


def build_palette(model):
    """Assign palette indices. Returns (pal[16] rgb, ramps{mat: [idx...]},
    roles{outline, white, eye})."""
    cols = [(255, 0, 255)]
    index = {}

    def get(c):
        c5 = to555(c)
        if c5 in index:
            return index[c5]
        cols.append(c)
        index[c5] = len(cols) - 1
        return index[c5]
    roles = {'outline': get(model.outline)}
    ramps = {}
    for nm in model.mat_order:
        ramps[nm] = [get(c) for c in model.mats[nm]['colors']]
    roles['white'] = get(model.white)
    roles['eye'] = get(model.eye_dark)
    if len(cols) > 16:
        raise ValueError('%s: palette has %d colours (max 15 + transparent)'
                         % (model.name, len(cols) - 1))
    while len(cols) < 16:
        cols.append((0, 0, 0))
    return cols, ramps, roles


BAYER2 = (0.0, 0.5, 0.75, 0.25)


def shade_index(model, mname, I, fx, fy):
    spec = model.mats[mname]
    n = len(spec['colors'])
    th = spec['th'] or DEFAULT_TH.get(n)
    if th is None:
        th = [(i + 1) / float(n) for i in range(n - 1)]
    if model.dither > 0:
        for t in th:
            if abs(I - t) < model.dither:
                b = BAYER2[(fy & 1) * 2 + (fx & 1)]
                I = I + (b - 0.375) * 2 * model.dither
                break
    s = 0
    for t in th:
        if I >= t:
            s += 1
    return s


def postprocess(model, R, pal_info, icon=False):
    cols, ramps, roles = pal_info
    fw, fh = R['fw'], R['fh']
    solid, part, mat = R['solid'], R['part'], R['mat']
    inten, depth, group = R['inten'], R['depth'], R['group']
    mat_names = model.mat_order
    N = fw * fh

    def nb4(f):
        x, y = f % fw, f // fw
        if x > 0:
            yield f - 1
        if x < fw - 1:
            yield f + 1
        if y > 0:
            yield f - fw
        if y < fh - 1:
            yield f + fw

    # --- silhouette cleanup: drop spurs, fill notches
    for _ in range(2):
        changed = False
        for f in range(N):
            ns = list(nb4(f))
            k = sum(1 for g in ns if solid[g])
            if solid[f] and k <= 1:
                solid[f] = False
                changed = True
            elif not solid[f] and k >= 3 and len(ns) == 4:
                src = [g for g in ns if solid[g]]
                g = max(src, key=lambda q: depth[q])
                solid[f] = True
                part[f], mat[f] = part[g], mat[g]
                inten[f], depth[f] = inten[g], depth[g]
                changed = True
        if not changed:
            break

    # --- shade quantisation
    shade = [0] * N
    for f in range(N):
        if solid[f]:
            shade[f] = shade_index(model, mat_names[mat[f]], inten[f],
                                   f % fw, f // fw)
    # --- despeckle isolated shade pixels
    for f in range(N):
        if not solid[f]:
            continue
        same = [g for g in nb4(f) if solid[g] and mat[g] == mat[f]
                and part[g] == part[f]]
        if len(same) < 3:
            continue
        if any(shade[g] == shade[f] for g in same):
            continue
        cnt = {}
        for g in same:
            cnt[shade[g]] = cnt.get(shade[g], 0) + 1
        s, c = max(cnt.items(), key=lambda kv: kv[1])
        if c >= 2:
            shade[f] = s

    img = [0] * N
    for f in range(N):
        if solid[f]:
            img[f] = ramps[mat_names[mat[f]]][shade[f]]

    # --- interior lines where a nearer part occludes a farther one
    ld = model.line_depth * (0.8 if icon else 1.0)
    line = [False] * N
    for f in range(N):
        if not solid[f]:
            continue
        for g in nb4(f):
            if solid[g] and group[part[g]] != group[part[f]] and \
                    depth[g] - depth[f] > ld:
                line[f] = True
                break
    for f in range(N):
        if line[f]:
            if model.line_mode == 'outline':
                img[f] = roles['outline']
            else:
                img[f] = ramps[mat_names[mat[f]]][0]

    # --- exterior outline
    for f in range(N):
        if not solid[f] and any(solid[g] for g in nb4(f)):
            img[f] = roles['outline']
    outlined = [img[f] != 0 for f in range(N)]

    # --- decals
    draw_decals(model, R, img, outlined, pal_info, icon)
    return img


# --------------------------------------------------------------------------
# decals: eyes, mouths, dots
# --------------------------------------------------------------------------
def ellipse_mask(w, h, fill=1.0):
    m = []
    for j in range(h):
        for i in range(w):
            dx = (i + 0.5 - w / 2.0) / (w / 2.0)
            dy = (j + 0.5 - h / 2.0) / (h / 2.0)
            if dx * dx + dy * dy <= fill:
                m.append((i, j))
    return set(m)


def decal_visible(R, d, tol_units=1.6):
    view = R['view']
    p = view.p(d['pos'])
    nv = norm(view.g(d['nrm']))
    if nv[2] < 0.12:
        return None
    buf = R['zbuf']
    x, y = int(p[0]), int(p[1])
    if not (0 <= x < buf.W and 0 <= y < buf.H):
        return None
    z = buf.depth[y * buf.W + x]
    if z - p[2] > tol_units * view.S:
        return None
    return (p[0] / view.ss, p[1] / view.ss, nv)


def draw_decals(model, R, img, outlined, pal_info, icon):
    cols, ramps, roles = pal_info
    fw, fh = R['fw'], R['fh']
    view = R['view']
    scale = view.S / view.ss

    def col(c):
        if isinstance(c, int):
            return c
        if c in roles:
            return roles[c]
        nm, k = c
        r = ramps[nm]
        return r[k if k >= 0 else len(r) + k]

    def put(x, y, c):
        if 0 <= x < fw and 0 <= y < fh and outlined[y * fw + x]:
            img[y * fw + x] = c

    for d in model.decals:
        vis = decal_visible(R, d)
        if vis is None:
            continue
        cx, cy, nv = vis
        if d['kind'] == 'eye':
            fore = max(0.45, nv[2]) ** 0.7
            w = max(d['minw'], int(round(d['w'] * scale * fore)))
            h = max(d['minh'], int(round(d['h'] * scale)))
            inner = 1
            if d['center'] is not None:
                pc = view.p(d['center'])
                inner = 1 if pc[0] / view.ss > cx else -1
            draw_eye(put, cx, cy, w, h, d, col, inner, icon)
        elif d['kind'] == 'mouth':
            w = max(d['minw'], int(round(d['w'] * scale)))
            h = max(1, int(round(d['h'] * scale)))
            draw_mouth(put, cx, cy, w, h, d, col)
        elif d['kind'] == 'dot':
            w = max(d['minw'], int(round(d['w'] * scale)))
            h = max(d['minh'], int(round(d['h'] * scale)))
            x0 = int(round(cx - w / 2.0))
            y0 = int(round(cy - h / 2.0))
            c = col(d['color'])
            msk = ellipse_mask(w, h, 1.0) if d['shape'] == 'oval' else \
                set((i, j) for i in range(w) for j in range(h))
            for i, j in msk:
                put(x0 + i, y0 + j, c)
        elif d['kind'] == 'sparkle':
            s = d['size'] if not icon else max(1, d['size'] - 1)
            x0, y0 = int(round(cx)), int(round(cy))
            c = col(d['color'])
            put(x0, y0, c)
            for k in range(1, s + 1):
                for ddx, ddy in ((k, 0), (-k, 0), (0, k), (0, -k)):
                    put(x0 + ddx, y0 + ddy, c)


def draw_eye(put, cx, cy, w, h, d, col, inner, icon):
    style = d['style']
    x0 = int(round(cx - w / 2.0))
    y0 = int(round(cy - h / 2.0))
    msk = ellipse_mask(w, h, 1.05)
    slant = d['slant']
    if slant and w >= 3:
        cut = set()
        for i in range(w):
            u = i / float(w - 1)
            if inner < 0:
                u = 1 - u
            c = int(round(slant * u * h * 0.5))
            for j in range(c):
                cut.add((i, j))
        msk -= cut
    EYE = col('eye')
    WH = col('white')
    OUT = col('outline')
    IR = col(d['iris']) if d['iris'] is not None else EYE
    look = d['look']
    if style in ('iris', 'sharp') and (w < 4 or h < 4):
        style = 'cute'

    def boundary(p):
        i, j = p
        return any((i + a, j + b) not in msk
                   for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    if style == 'cute':
        for p in msk:
            put(x0 + p[0], y0 + p[1], EYE)
        if h >= 5 and d['iris'] is not None:
            for p in msk:
                if p[1] >= int(math.ceil(h * 0.6)) and not boundary(p):
                    put(x0 + p[0], y0 + p[1], IR)
        if d['glint']:
            if w <= 2 or h <= 2:
                gl = [(0, 0)]
            elif w <= 3 or h <= 4:
                gl = [(0 if w <= 3 else 1, 1)] if h >= 3 else [(0, 0)]
            else:
                gw = 2 if w >= 6 else 1
                gh = 2 if h >= 6 else 1
                gx = 1
                gl = [(gx + a, 1 + b) for a in range(gw) for b in range(gh)]
                if h >= 7 and w >= 5:
                    gl.append((w - 2, h - 3))
            for p in gl:
                if p in msk:
                    put(x0 + p[0], y0 + p[1], WH)
    elif style == 'iris':
        # dark rim, coloured iris, pupil toward `look`, glint
        for p in msk:
            put(x0 + p[0], y0 + p[1], EYE if boundary(p) else IR)
        pw = max(1, int(round(w * 0.45)))
        ph = max(1, int(round(h * 0.55)))
        px0 = x0 + (w - pw) // 2 + (look if w >= 5 else 0)
        py0 = y0 + (h - ph) // 2 + (1 if h >= 6 else 0)
        for i in range(pw):
            for j in range(ph):
                if (px0 - x0 + i, py0 - y0 + j) in msk:
                    put(px0 + i, py0 + j, EYE)
        if d['glint']:
            gx = x0 + 1 if w >= 4 else x0
            gy = y0 + 1 if h >= 4 else y0
            put(gx, gy, WH)
            if w >= 6 and h >= 6:
                put(gx + 1, gy, WH)
                put(gx, gy + 1, WH)
    elif style == 'sharp':
        # white sclera, iris toward look, dark rim, heavier upper lid
        for p in msk:
            put(x0 + p[0], y0 + p[1], WH)
        iw = max(1, int(round(w * 0.5)))
        ix0 = x0 if look < 0 else x0 + w - iw
        if w >= 5:
            ix0 += 1 if look < 0 else -1
        for p in msk:
            X = x0 + p[0]
            if ix0 <= X < ix0 + iw and not boundary(p):
                put(X, y0 + p[1], IR)
        # pupil column
        pxc = ix0 + (iw - 1) // 2 if iw > 1 else ix0
        for p in msk:
            if x0 + p[0] == pxc and not boundary(p) and p[1] >= 1:
                put(x0 + p[0], y0 + p[1], EYE)
        for p in msk:
            if boundary(p):
                put(x0 + p[0], y0 + p[1], OUT)
        # thick upper lid
        tops = {}
        for p in msk:
            if p[0] not in tops or p[1] < tops[p[0]]:
                tops[p[0]] = p[1]
        for i, j in tops.items():
            put(x0 + i, y0 + j, OUT)
            if d['lid'] and (i, j + 1) in msk:
                put(x0 + i, y0 + j + 1, OUT)
        if d['glint'] and h >= 4 and w >= 4:
            put(pxc + (1 if look < 0 else -1), y0 + 2, WH)
    elif style == 'glow':
        ring = IR
        if isinstance(d['iris'], tuple):
            ring = col((d['iris'][0], max(0, d['iris'][1] - 1)))
        for p in msk:
            top = (p[0], p[1] - 1) not in msk
            if top and slant:
                c = OUT
            elif (p[0], p[1] + 1) not in msk and h >= 3:
                c = ring
            else:
                c = IR
            put(x0 + p[0], y0 + p[1], c)
        if d['pupil'] is not None:
            pc = col(d['pupil'])
            if h >= 4:
                xc = x0 + w // 2 + (look if w >= 4 else 0)
                for j in range(1, h - 1):
                    if (xc - x0, j) in msk:
                        put(xc, y0 + j, pc)
        if d['glint'] and w >= 3 and h >= 3:
            put(x0 + 1, y0 + 1, WH)
    elif style == 'solid':
        for p in msk:
            put(x0 + p[0], y0 + p[1], IR)
    elif style == 'sleepy':
        # half-lidded: skin above, a dark lid line, the eye below it
        lid = max(1, int(round(h * 0.42)))
        for p in msk:
            if p[1] < lid:
                continue
            put(x0 + p[0], y0 + p[1], OUT if p[1] == lid else EYE)
        if d['glint'] and h - lid >= 3 and w >= 3:
            put(x0 + 1, y0 + lid + 1, WH)
    elif style == 'closed':
        # content closed eye: a downward arc
        for i in range(w):
            e = i == 0 or i == w - 1
            put(x0 + i, y0 + h // 2 - (1 if e else 0), OUT)


def draw_mouth(put, cx, cy, w, h, d, col):
    kind = d['mk']
    c = col(d['color'])
    x0 = int(round(cx - w / 2.0))
    y0 = int(round(cy - h / 2.0))
    if kind == 'smile':
        for i in range(w):
            end = i == 0 or i == w - 1
            put(x0 + i, y0 + (0 if end else 1), c)
        if d['fang'] and w >= 3:
            put(x0 + 1 if d['fang'] < 0 else x0 + w - 2, y0 + 2,
                col('white'))
    elif kind == 'line':
        for i in range(w):
            put(x0 + i, y0, c)
    elif kind == 'w':
        # cat mouth: two small arcs
        pts = []
        half = max(1, w // 2)
        for i in range(w):
            pts.append((i, 1 if (i % half) not in (0,) else 0))
        for i, j in pts:
            put(x0 + i, y0 + j, c)
    elif kind == 'open':
        hh = max(2, h)
        inner = col(d['inner']) if d['inner'] else c
        for j in range(hh):
            for i in range(w):
                edge = j == 0 or j == hh - 1 or i == 0 or i == w - 1
                corner = (j == hh - 1) and (i == 0 or i == w - 1)
                if corner:
                    continue
                if j > 0 and (i == 0 or i == w - 1) and j == hh - 1:
                    continue
                put(x0 + i, y0 + j, c if edge else inner)
        if d['fang'] and w >= 4:
            fx = x0 + 1 if d['fang'] < 0 else x0 + w - 2
            put(fx, y0 + 1, col('white'))
    elif kind == 'teeth':
        # smile line with buck teeth hanging below it
        tw = max(2, w)
        th = max(2, h)
        for i in range(-2, tw + 2):
            put(x0 + i, y0 - (1 if i in (-2, tw + 1) else 0), c)
        for j in range(1, th + 1):
            put(x0 - 1, y0 + j, c)
            put(x0 + tw, y0 + j, c)
            for i in range(tw):
                put(x0 + i, y0 + j, col('white'))
        for i in range(tw):
            put(x0 + i, y0 + th + 1, c)
        if tw >= 4:
            for j in range(1, th + 1):
                put(x0 + tw // 2, y0 + j, c)
    elif kind == 'beak':
        pass


# --------------------------------------------------------------------------
# sprite generation for one species
# --------------------------------------------------------------------------
def make_sprites(model):
    pal_info = build_palette(model)
    # front
    ex = measure(model, model.front_yaw, model.front_pitch)
    wu, hu = ex[2] - ex[0], ex[3] - ex[1]
    bottom = 60.0 - model.float_lift
    # never taller than the frame: a hovering kin shrinks rather than clip
    s = min(model.height / hu, min(model.max_w, 59.0) / wu, (bottom - 2.0) / hu)
    ox = 32.0 - s * (ex[0] + ex[2]) / 2.0
    oy = bottom - s * ex[3]
    Rf = render(model, model.front_yaw, model.front_pitch, s, ox, oy, 64, 64)
    front = postprocess(model, Rf, pal_info)
    # back
    exb = measure(model, model.back_yaw, model.back_pitch)
    wb, hb = exb[2] - exb[0], exb[3] - exb[1]
    sb = s * model.back_scale
    if model.back_show * sb * hb < model.back_min_vis:
        sb = model.back_min_vis / (model.back_show * hb)
    if sb * wb > 59:
        sb = 59.0 / wb
    top = max(2.0, 64.0 - model.back_show * sb * hb)
    oxb = 32.0 - sb * (exb[0] + exb[2]) / 2.0
    oyb = top - sb * exb[1]
    Rb = render(model, model.back_yaw, model.back_pitch, sb, oxb, oyb, 64, 64)
    back = postprocess(model, Rb, pal_info)
    # icon
    si = min(model.icon_h / hu, model.icon_w / wu)
    oxi = 16.0 - si * (ex[0] + ex[2]) / 2.0
    oyi = 29.0 - si * ex[3]
    Ri = render(model, model.front_yaw, model.front_pitch, si, oxi, oyi, 32,
                32, ss=4, icon=True)
    icon = postprocess(model, Ri, pal_info, icon=True)
    ow, ow_h = make_overworld(model, pal_info)
    return front, back, icon, pal_info[0], ow, ow_h


# --------------------------------------------------------------------------
# overworld sprites: 32x32, 6 frames (down x2, up x2, left x2)
# --------------------------------------------------------------------------
OW_FRAMES = 6
OW_GROUND = 30              # feet rest on this row (exclusive bottom edge)
OW_YAW = {'down': 0.0, 'up': 180.0, 'left': -82.0}
# winged kin turn a little toward the camera in profile so wings show
OW_SIDE_YAW = {'STORMHAWK': -62.0, 'SKYWISP': -58.0, 'LUMOTH': -58.0,
               'HOOTLORD': -66.0, 'DRAKORA': -62.0, 'ZAPPET': -72.0,
               'PUFFOWL': -72.0}
OW_PITCH = {'down': 24.0, 'up': 28.0, 'left': 18.0}
# kin that hover above the ground in the overworld (px of lift)
OW_FLOAT = {'NOSFERBAT': 2, 'BUBBLIN': 3, 'STORMHAWK': 4, 'HOOTLORD': 3, 'SKYWISP': 4,
            'LUMOTH': 4, 'WISPIRE': 4, 'DRAKORA': 3}
LEG_WORDS = ('leg', 'foot', 'hip', 'shin', 'thigh')
# long side-on kin (horses, big cats, drakes) are a thin column head-on, so
# their down/up frames turn to a 3/4 view. OW_TURN[name] sets the angle (0 =
# never turn); otherwise a kin turns by OW_AUTO_TURN when its head-on view is
# narrow and its profile is much wider.
OW_TURN = {'HOPSHI': 0.0}
OW_AUTO_TURN = -50.0


def part_side(name):
    if name.endswith('-1'):
        return -1
    if name.endswith('1') and not name.endswith('-1'):
        return 1
    return 0


def variant(model, offsets=None, scale=None):
    """Copy of `model` with per-part translations and/or a squash-and-
    stretch scale about the ground point (0,0,0)."""
    offsets = offsets or {}
    sx, sy, sz = scale if scale else (1.0, 1.0, 1.0)
    uni = abs(sx - 1) < 1e-9 and abs(sy - 1) < 1e-9 and abs(sz - 1) < 1e-9

    def P(p, t):
        return (p[0] * sx + t[0], p[1] * sy + t[1], p[2] * sz + t[2])

    def V(v):
        return (v[0] * sx, v[1] * sy, v[2] * sz)
    z3 = (0.0, 0.0, 0.0)
    out = []
    for pr in model.prims:
        k = pr[0]
        part = pr[5] if k == 'H' else (pr[3] if k == 'P' else pr[4])
        t = offsets.get(part, z3)
        if k == 'S':
            _, c, r, mat, pt = pr
            if uni:
                out.append(('S', P(c, t), r, mat, pt))
            else:
                out.append(('E', P(c, t), ((r * sx, 0, 0), (0, r * sy, 0),
                                           (0, 0, r * sz)), mat, pt))
        elif k == 'E':
            _, c, axes, mat, pt = pr
            out.append(('E', P(c, t), tuple(V(a) for a in axes), mat, pt))
        elif k == 'P':
            _, pts, mat, pt, puff, spine = pr
            sp = (P(spine[0], t), P(spine[1], t)) if spine else None
            out.append(('P', [P(q, t) for q in pts], mat, pt, puff, sp))
        elif k == 'H':
            _, planes, c, rad, mat, pt = pr
            npl = []
            for n, d in planes:
                n2 = (n[0] / sx, n[1] / sy, n[2] / sz)
                ln = length(n2)
                n2 = mul(n2, 1.0 / ln)
                npl.append((n2, (d / ln) + dot(n2, t)))
            out.append(('H', npl, P(c, t), rad * max(sx, sy, sz), mat, pt))
    v = Model.__new__(Model)
    v.__dict__.update(model.__dict__)
    v.prims = out
    paints = []
    for c, axes, mat, parts in model.paints:
        t = z3
        if parts:
            offs = set(offsets.get(p, z3) for p in parts)
            if len(offs) == 1:
                t = offs.pop()
        paints.append((P(c, t), tuple(V(a) for a in axes), mat, parts))
    v.paints = paints
    decs = []
    for d in model.decals:
        d = dict(d)
        d['pos'] = P(d['pos'], z3)
        decs.append(d)
    v.decals = decs
    return v


def walk_variant(model, unit):
    """Second walk frame: stride the legs (diagonal pairs for quadrupeds,
    alternate for bipeds), flick the tail; legless kin squash instead."""
    parts = []
    for pr in model.prims:
        p = pr[5] if pr[0] == 'H' else (pr[3] if pr[0] == 'P' else pr[4])
        if p not in parts:
            parts.append(p)
    legs = [p for p in parts if any(p.startswith(w) for w in LEG_WORDS)
            and part_side(p) != 0 or p in ('legFa', 'legFb')]
    quad = any(p.startswith(('legF', 'legB', 'hip')) for p in legs)
    offs = {}
    dz, lift = 1.3 * unit, 0.9 * unit
    for p in legs:
        s = part_side(p)
        if p == 'legFa':
            s, front = -1, True
        elif p == 'legFb':
            s, front = 1, True
        else:
            front = p.startswith('legF')
        if quad:
            a = (s < 0) == front        # diagonal pairs move together
        else:
            a = s < 0
        offs[p] = (0.0, lift, dz) if a else (0.0, 0.0, -dz)
    for p in parts:
        if p.startswith(('tail', 'lamp')):
            offs[p] = (0.7 * unit, 0.3 * unit, 0.0)
    if legs:
        return variant(model, offs)
    return variant(model, offs, scale=(1.07, 0.9, 1.07))


# Overworld size by rank (docs: the player is 24 px tall and 14 px wide, and a
# kin must still fit through a one-tile corridor behind them). Tier from
# tools/kin: (min height, max height, max width) in px, outline included.
# Within its range a kin's height follows its battle height (m.height).
OW_SIZE = {'first': (16, 19, 20), 'middle': (18, 22, 22), 'final': (20, 24, 24),
           'single': (20, 24, 24), 'rare': (21, 25, 24), 'fusion': (23, 26, 24),
           'legend': (26, 29, 26)}
OW_TIER = {}                # name -> (tier, rarity), filled by _roster()


def ow_size(model):
    tier, rarity = OW_TIER.get(model.name, ('final', 'U'))
    lo, hi, wmax = OW_SIZE[tier]
    if rarity == 'R' and tier != 'rare':          # rare lines sit one step up
        lo, hi = lo + 1, hi + 1
    if OW_FLOAT.get(model.name, 0) > 0:           # flyers pass over things: wings may spread
        hi, wmax = hi + 1, min(30, wmax + 4)
    # battle heights run ~26 (tiny) .. ~62 (huge); map that onto lo..hi
    t = max(0.0, min(1.0, (model.height - 28) / 30.0))
    return int(round(lo + (hi - lo) * t)), wmax


def ow_target_height(model):
    return ow_size(model)[0]


def make_overworld(model, pal_info):
    """Six 32x32 frames: down0, down1, up0, up1, left0, left1."""
    if model.ow_offsets:
        model = variant(model, model.ow_offsets)
    lift = OW_FLOAT.get(model.name, 0)
    floating = lift > 0
    bottom = OW_GROUND - lift
    yaws = dict(OW_YAW)
    yaws['left'] = OW_SIDE_YAW.get(model.name, yaws['left'])
    exts = {v: measure(model, yaws[v], OW_PITCH[v]) for v in yaws}
    turn = OW_TURN.get(model.name)
    if turn is None:
        d, l = exts['down'], exts['left']
        dw, dh, lw = d[2] - d[0], d[3] - d[1], l[2] - l[0]
        turn = OW_AUTO_TURN if dw < 0.6 * dh and lw > 1.5 * dw else 0.0
    if turn:
        yaws['down'], yaws['up'] = turn, 180.0 + turn
        for v in ('down', 'up'):
            exts[v] = measure(model, yaws[v], OW_PITCH[v])
    ex = exts['down']
    # target counts the 1px outline on top and bottom
    target_h, max_w = ow_size(model)
    # the height target holds in every direction (the walk bob adds 1 px)
    s = (target_h - 3) / max(e[3] - e[1] for e in exts.values())
    for v, e in exts.items():
        # width only matters across a corridor (down/up); walking sideways a
        # kin may be long, up to the frame
        w = max_w if v != 'left' else 30
        s = min(s, (w - 2.0) / (e[2] - e[0]), (bottom - 3.0) / (e[3] - e[1]))
    unit = 1.0 / s                      # model units per pixel
    walk = model if floating else walk_variant(model, unit)
    frames = []
    for v in ('down', 'up', 'left'):
        e = exts[v]
        ox = 16.0 - s * (e[0] + e[2]) / 2.0
        oy = bottom - s * e[3]
        for k, mm in enumerate((model, walk)):
            bob = 1.0 if k == 1 else 0.0
            R = render(mm, yaws[v], OW_PITCH[v], s, ox, oy - bob, 32, 32,
                       ss=4, icon=True)
            frames.append(postprocess(mm, R, pal_info, icon=True))
    rows = [y for y in range(32) if any(frames[0][y * 32 + x]
                                        for x in range(32))]
    height = (rows[-1] - rows[0] + 1) if rows else 0
    return frames, height


# --------------------------------------------------------------------------
# PNG + contact sheets
# --------------------------------------------------------------------------
def write_png(path, w, h, pix):
    """pix: list of (r,g,b) rows-major."""
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw.extend(pix[y * w + x])

    def chunk(t, data):
        return struct.pack('>I', len(data)) + t + data + \
            struct.pack('>I', zlib.crc32(t + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack(
        '>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + \
        chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b'')
    with open(path, 'wb') as fh:
        fh.write(png)


FONT = {
    'A': '010101111101101', 'B': '110101110101110', 'C': '011100100100011',
    'D': '110101101101110', 'E': '111100110100111', 'F': '111100110100100',
    'G': '011100101101011', 'H': '101101111101101', 'I': '111010010010111',
    'J': '001001001101010', 'K': '101101110101101', 'L': '100100100100111',
    'M': '101111111101101', 'N': '110101101101101', 'O': '010101101101010',
    'P': '110101110100100', 'Q': '010101101110011', 'R': '110101110101101',
    'S': '011100010001110', 'T': '111010010010010', 'U': '101101101101111',
    'V': '101101101101010', 'W': '101101111111101', 'X': '101101010101101',
    'Y': '101101010010010', 'Z': '111001010100111', '0': '111101101101111',
    '1': '010110010010111', '2': '110001010100111', '3': '110001010001110',
    '4': '101101111001001', '5': '111100110001110', '6': '011100111101111',
    '7': '111001010010010', '8': '111101111101111', '9': '111101111001110',
    ' ': '000000000000000', '-': '000000111000000', ':': '000010000010000',
}


class Sheet:
    def __init__(self, w, h, bg=(40, 40, 48)):
        self.w, self.h = w, h
        self.pix = [bg] * (w * h)

    def rect(self, x, y, w, h, c):
        for j in range(max(0, y), min(self.h, y + h)):
            for i in range(max(0, x), min(self.w, x + w)):
                self.pix[j * self.w + i] = c

    def text(self, x, y, s, c=(255, 255, 255), sc=2):
        for ch in s.upper():
            g = FONT.get(ch, FONT[' '])
            for j in range(5):
                for i in range(3):
                    if g[j * 3 + i] == '1':
                        self.rect(x + i * sc, y + j * sc, sc, sc, c)
            x += 4 * sc

    def sprite(self, x, y, img, sw, sh, pal, sc, bg):
        pal8 = [from555(to555(c)) for c in pal]
        for j in range(sh):
            for i in range(sw):
                v = img[j * sw + i]
                if v == 0:
                    if bg == 'check':
                        c = (232, 232, 224) if ((i // 4 + j // 4) & 1) \
                            else (208, 212, 204)
                    elif bg == 'grass':
                        c = (112, 184, 88) if ((j // 6) & 1) else \
                            (96, 168, 80)
                    else:
                        c = bg
                else:
                    c = pal8[v]
                self.rect(x + i * sc, y + j * sc, sc, sc, c)

    def save(self, path):
        write_png(path, self.w, self.h, self.pix)


def contact_sheets(results, outdir, names):
    ids = sorted(results)
    cols = 8
    rows = (len(ids) + cols - 1) // cols
    for kind, size, sc in (('front', 64, 3), ('back', 64, 3),
                           ('icons', 32, 4)):
        cw = size * sc + 8
        ch = size * sc * 2 + 20
        sh = Sheet(cols * cw + 8, rows * ch + 8)
        for n, i in enumerate(ids):
            front, back, icon, pal = results[i][:4]
            img = {'front': front, 'back': back, 'icons': icon}[kind]
            cx = 8 + (n % cols) * cw
            cy = 8 + (n // cols) * ch
            sh.text(cx, cy, '%d %s' % (i, names[i]), sc=2)
            sh.sprite(cx, cy + 14, img, size, size, pal, sc, 'check')
            sh.sprite(cx, cy + 14 + size * sc, img, size, size, pal, sc,
                      'grass')
        sh.save(os.path.join(outdir, 'contact_%s.png' % kind))


def review_sheet(results, outdir, ids, names, tag):
    """Detailed sheet: per species front/back/icon at 4x, light + grass."""
    sc = 4
    cw = 64 * sc * 2 + 32 * sc * 2 + 40
    ch = 64 * sc + 22
    sh = Sheet(cw + 16, len(ids) * ch + 16)
    for n, i in enumerate(ids):
        front, back, icon, pal = results[i][:4]
        y = 8 + n * ch
        sh.text(8, y, '%d %s' % (i, names[i]), sc=2)
        y += 14
        sh.sprite(8, y, front, 64, 64, pal, sc, 'check')
        sh.sprite(8 + 64 * sc + 8, y, back, 64, 64, pal, sc, 'grass')
        sh.sprite(8 + 128 * sc + 16, y, icon, 32, 32, pal, sc, 'check')
        sh.sprite(8 + 128 * sc + 16, y + 32 * sc, front, 64, 64, pal, 1,
                  'grass')
        sh.sprite(8 + 128 * sc + 24 + 32 * sc, y, icon, 32, 32, pal, sc,
                  'grass')
        sh.sprite(8 + 128 * sc + 24 + 32 * sc, y + 32 * sc, back, 64, 64,
                  pal, 1, 'check')
    sh.save(os.path.join(outdir, 'review_%s.png' % tag))


def ow_sheet(results, outdir, names, tag='overworld'):
    """All overworld frames on grass at 3x (+ a 1x strip per species)."""
    ids = sorted(results)
    sc = 3
    cw = OW_FRAMES * (32 * sc + 4) + 8 + OW_FRAMES * 34 + 8
    ch = 32 * sc + 18
    cols = 2
    rows = (len(ids) + cols - 1) // cols
    sh = Sheet(cols * cw + 8, rows * ch + 8)
    for n, i in enumerate(ids):
        pal = results[i][3]
        frames = results[i][4]
        x0 = 8 + (n % cols) * cw
        y0 = 6 + (n // cols) * ch
        sh.text(x0, y0, '%d %s  H%d' % (i, names[i], results[i][5]), sc=2)
        for f, img in enumerate(frames):
            sh.sprite(x0 + f * (32 * sc + 4), y0 + 14, img, 32, 32, pal, sc,
                      'grass')
        xs = x0 + OW_FRAMES * (32 * sc + 4) + 4
        for f, img in enumerate(frames):
            sh.sprite(xs + f * 34, y0 + 14, img, 32, 32, pal, 1, 'grass')
            sh.sprite(xs + f * 34, y0 + 14 + 36, img, 32, 32, pal, 1,
                      (200, 176, 128))
    sh.save(os.path.join(outdir, 'contact_%s.png' % tag))


# --------------------------------------------------------------------------
# header output
# --------------------------------------------------------------------------
def pack_tiles(img, w, h):
    out = []
    for ty in range(h // 8):
        for tx in range(w // 8):
            for y in range(8):
                v = 0
                for x in range(8):
                    p = img[(ty * 8 + y) * w + tx * 8 + x] & 15
                    v |= p << (4 * x)
                out.append(v)
    return out


def fmt_u32_block(vals, indent='        '):
    lines = []
    for i in range(0, len(vals), 8):
        lines.append(indent + ', '.join('0x%08Xu' % v for v in vals[i:i + 8]))
    return ',\n'.join(lines)


def write_header(path, results):
    n = len(SPECIES)
    out = ['/* GENERATED by tools/gen_monsters.py -- do not edit. '
           'Regenerate: python3 tools/gen_monsters.py */',
           '#ifndef GFX_MONSTERS_H', '#define GFX_MONSTERS_H',
           '#define MON_GFX_COUNT %d' % n]
    for arr, key, w, h in (('mon_front_gfx', 0, 64, 64),
                           ('mon_back_gfx', 1, 64, 64),
                           ('mon_icon_gfx', 2, 32, 32)):
        words = (w // 8) * (h // 8) * 8
        out.append('static const u32 %s[MON_GFX_COUNT][%s] = {' %
                   (arr, '64 * 8' if w == 64 else '16 * 8'))
        blocks = []
        for i in range(n):
            vals = pack_tiles(results[i][key], w, h)
            assert len(vals) == words
            blocks.append('    { /* %d %s */\n%s\n    }' %
                          (i, SPECIES[i][0], fmt_u32_block(vals)))
        out.append(',\n'.join(blocks))
        out.append('};')
    out.append('static const u16 mon_palettes[MON_GFX_COUNT][16] = {')
    rows = []
    for i in range(n):
        pal = results[i][3]
        vals = []
        for k, c in enumerate(pal):
            if k == 0:
                vals.append(0)
                continue
            r, g, b = to555(c)
            vals.append(r | (g << 5) | (b << 10))
        rows.append('    { ' + ', '.join('0x%04X' % v for v in vals) +
                    ' } /* %d %s */' % (i, SPECIES[i][0]))
    out.append(',\n'.join(rows))
    out.append('};')
    # overworld frames: 32x32 = 4x4 tiles row-major, same palettes
    out.append('/* Overworld sprites: MON_OW_FRAMES 32x32 4bpp frames per '
               'species (4x4 tiles,')
    out.append('   row-major), palette = mon_palettes[species]. Frames: '
               '0,1 facing down;')
    out.append('   2,3 facing up; 4,5 facing left (h-flip for right). Each '
               'pair is a')
    out.append('   2-step walk cycle (frame 0/2/4 also serve as the idle '
               'pose; the second')
    out.append('   frame is a stride/squash lifted 1px). Ground kin: '
               'lowest opaque row')
    out.append('   (outline under the feet) is row 30; hovering kin sit '
               '3-4px higher.')
    out.append('   mon_ow_height = visible height in px of frame 0. */')
    out.append('#define MON_OW_FRAMES %d' % OW_FRAMES)
    out.append('static const u32 mon_ow_gfx[MON_GFX_COUNT][MON_OW_FRAMES]'
               '[16 * 8] = {')
    blocks = []
    for i in range(n):
        fr = []
        for f, img in enumerate(results[i][4]):
            vals = pack_tiles(img, 32, 32)
            assert len(vals) == 16 * 8
            fr.append('        { /* frame %d */\n%s\n        }' %
                      (f, fmt_u32_block(vals, indent='            ')))
        blocks.append('    { /* %d %s */\n%s\n    }' %
                      (i, SPECIES[i][0], ',\n'.join(fr)))
    out.append(',\n'.join(blocks))
    out.append('};')
    out.append('static const u8 mon_ow_height[MON_GFX_COUNT] = {')
    hs = [str(results[i][5]) for i in range(n)]
    for k in range(0, n, 16):
        out.append('    ' + ', '.join(hs[k:k + 16]) +
                   (',' if k + 16 < n else ''))
    out.append('};')
    out.append('#endif')
    with open(path, 'w') as fh:
        fh.write('\n'.join(out) + '\n')


# ==========================================================================
# SPECIES
# ==========================================================================
def eye_pair(m, head_c, head_r, az, el, w, h, rot=None, center=None, turn=0.0,
             **kw):
    """Place two eyes on an ellipsoid head at +-az degrees (yaw), el up.
    turn>0 swings both toward the creature's left (+X), i.e. toward the
    camera in the default 3/4 front view."""
    for s in (-1, 1):
        a = (az * s + turn) * DEG
        e = el * DEG
        d = (math.sin(a) * math.cos(e), math.sin(e), math.cos(a) * math.cos(e))
        p, n = surf(head_c, head_r, d, rot)
        m.eye(p, n, w, h, center=center, **kw)


def on(c, r, d, rot=None):
    return surf(c, r, d, rot)


def flame(m, base, h, w, part, mats=('flame', 'gold', 'core'),
          up=(0, 1, 0), face=(0.5, 0.15, 0.85), tongues=2, wig=0.28,
          flat=0.38, inner=True, core=True, seed=0):
    """Layered stylised flame: outer tongues + inner + core, all one part."""
    up = norm(up)
    face = norm(sub(face, mul(up, dot(face, up))))
    side = norm(cross(up, face))
    rnd = Rand(seed + 7)

    def P(a, b):  # a along up, b along side
        return add(base, add(mul(up, a), mul(side, b)))
    main = [P(0, 0), P(h * 0.35, w * wig), P(h * 0.7, -w * wig * 0.8),
            P(h, w * wig * 0.5)]
    m.tube(main, None, mats[0], part, flat=flat, up=face,
           rfn=lambda t: w * (1 - t) ** 0.85 * (0.62 + 0.38 * min(1, t * 5)))
    sides = [1, -1, 0.6, -0.6][:tongues]
    for k, sg in enumerate(sides):
        hh = h * (0.52 - 0.12 * (k // 2)) * (0.9 + 0.2 * rnd.f())
        b0 = P(h * 0.10, w * 0.40 * sg)
        pts = [b0, add(b0, add(mul(up, hh * 0.45), mul(side, w * 0.50 * sg))),
               add(b0, add(mul(up, hh), mul(side, w * 0.62 * sg)))]
        ww = w * 0.55
        m.tube(pts, None, mats[0], part, flat=flat, up=face,
               rfn=lambda t, ww=ww: ww * (1 - t) ** 0.8 + 0.1)
    if inner and len(mats) > 1:
        pts = [P(h * 0.02, 0), P(h * 0.28, w * wig * 0.6),
               P(h * 0.62, -w * wig * 0.3)]
        m.tube(pts, None, mats[1], part, flat=max(0.95, flat * 2.4),
               up=face, rfn=lambda t: w * 0.60 * (1 - t) ** 0.8 + 0.1)
    if core and len(mats) > 2:
        pts = [P(h * 0.02, 0), P(h * 0.30, w * wig * 0.3)]
        m.tube(pts, None, mats[2], part, flat=2.4, up=face,
               rfn=lambda t: w * 0.30 * (1 - t) ** 0.7 + 0.1)


def lantern(m, c, r, part, axis=(0, 1, 0), ribs=6, rib_r=0.7, fur='fur',
            ember='ember', ember_r=0.74, phase=0.0, cap=True, cap_len=None,
            cap_mat=None):
    """A round cage of fur ribs (meridians) around a glowing ember sphere -
    the lantern tail tip of the fire foxes."""
    ax = norm(axis)
    u = norm(cross(ax, (0.3, 0.1, 1.0) if abs(ax[2]) < 0.9 else (1, 0, 0)))
    v = cross(ax, u)
    m.sph(c, r * ember_r, ember, part)
    # rotate the ribs so two of them flank the centre line seen from the
    # front view (reads as a cage rather than a solid ball)
    yw = m.front_yaw * DEG
    cam = (-math.sin(yw), 0.0, math.cos(yw))
    a0 = math.atan2(dot(cam, v), dot(cam, u)) / DEG + 180.0 / ribs
    for k in range(ribs):
        a = (360.0 * k / ribs + a0 + phase) * DEG
        d = add(mul(u, math.cos(a)), mul(v, math.sin(a)))
        pts = []
        for i in range(9):
            th = math.pi * (0.06 + 0.88 * i / 8.0)
            pts.append(add(c, add(mul(ax, -r * math.cos(th)),
                                  mul(d, r * math.sin(th)))))
        m.tube(pts, None, fur, part,
               rfn=lambda t: rib_r * (0.75 + 0.5 * math.sin(math.pi * t)))
    # collar where the ribs gather at the bottom + a little top knot
    m.sph(add(c, mul(ax, -r * 0.92)), rib_r * 1.9, fur, part)
    if cap:
        cl = cap_len if cap_len is not None else r * 0.75
        top = add(c, mul(ax, r * 0.9))
        m.tube([top, add(top, mul(ax, cl * 0.6)), add(top, add(mul(ax, cl),
                                                              mul(u, cl * 0.35)))],
               [rib_r * 1.7, rib_r * 1.1, 0.15], cap_mat or fur, part)


# ---- 0 FLARIX ------------------------------------------------------------
def flarix():
    m = Model('FLARIX')
    m.outline = (70, 22, 30)
    m.mat('fur', ['#7e1c36', '#bc3230', '#e45a3a', '#fa9464'])
    m.mat('cream', ['#dea57c', '#f6dcad', '#fff7e0'])
    m.mat('ember', ['#ffa826', '#ffe45a', '#fffbd0'], emissive=0.85)
    m.mat('rib', ['#7e1c36', '#bc3230', '#e45a3a'])
    m.eye_dark = (34, 18, 30)
    m.height = 36
    m.front_yaw = -26
    head_c, head_r = (0, 20, 5), (9, 8, 8.2)
    # body + legs
    m.ell((0, 9.5, -1.5), (6.5, 6, 8.5), 'fur', 'body')
    m.paint((0, 10, 6.5), (5.2, 5.5, 4.5), 'cream', ['body'])
    for s in (-1, 1):
        m.tube([(s * 3.8, 8, 4.0), (s * 3.9, 4, 5.0), (s * 3.9, 1.8, 5.8)],
               [2.4, 2.1, 2.3], 'fur', 'legF%d' % s)
        m.ell((s * 4.3, 8.5, -6), (3.0, 4.2, 4.2), 'fur', 'hip%d' % s)
        m.tube([(s * 4.6, 6, -6), (s * 4.6, 2, -5.2)], [2.4, 2.2], 'fur',
               'hip%d' % s)
        m.paint((s * 3.9, 1.3, 6.2), (2.6, 1.5, 2.6), 'cream',
                ['legF%d' % s])
    # bushy tail curling up to a lantern tip
    m.tube([(0.5, 9, -9), (3, 11.5, -14.5), (6.5, 15.5, -18.5),
            (8.2, 19.5, -19.5)], [2.2, 3.6, 3.4, 1.7], 'fur', 'tail')
    lantern(m, (8.6, 24.0, -19.4), 4.6, 'lamp', axis=(0.1, 1, 0.05),
            ribs=5, rib_r=0.6, ember_r=0.86, fur='rib')
    # head
    m.ell(head_c, head_r, 'fur', 'head')
    m.ell((0, 16.8, 10.8), (4.4, 3.3, 3.6), 'cream', 'head')
    m.paint((0, 14.5, 7), (6.5, 3.2, 5), 'cream', ['head'])
    for s in (-1, 1):
        m.tube([(s * 7.2, 17.5, 4.5), (s * 10.2, 15.8, 3.2),
                (s * 11.6, 14.2, 2.2)], [2.6, 1.6, 0.3], 'fur', 'head',
               flat=0.5, up=(0, 0, 1))
        m.tube([(s * 5.2, 25.5, 3.2), (s * 7.4, 30, 2.2),
                (s * 8.9, 35.5, 1.2)], [3.6, 2.6, 0.25], 'fur',
               'ear%d' % s, flat=0.42, up=(0, 0.25, 1))
        m.paint((s * 6.2, 28.2, 4.2), (1.7, 3.0, 1.2), 'cream', ['ear%d' % s],
                rot=(0, 0, -s * 20))
    eye_pair(m, head_c, head_r, 30, 8, 4.4, 6.0, iris=('fur', 0),
             center=(0, 17, 14))
    m.dot(on((0, 16.8, 10.8), (4.4, 3.3, 3.6), (0, 0.55, 1))[0], (0, 0, 1),
          w=2.0, h=1.2, minw=2)
    p, n = on((0, 16.8, 10.8), (4.4, 3.3, 3.6), (0, -0.45, 1))
    m.mouth(p, n, 'open', w=3.2, h=2.2, inner=('fur', 0))
    return m


# ---- 1 PYREFOX -----------------------------------------------------------
def pyrefox():
    m = Model('PYREFOX')
    m.outline = (66, 20, 30)
    m.mat('fur', ['#7e1c36', '#bc3230', '#e45a3a', '#fa9464'])
    m.mat('cream', ['#dea57c', '#f6dcad', '#fff7e0'])
    m.mat('sock', ['#4a1c2c', '#7e1c36'])
    m.mat('ember', ['#ffa826', '#ffe45a', '#fffbd0'], emissive=0.85)
    m.mat('rib', ['#7e1c36', '#bc3230', '#e45a3a'])
    m.eye_dark = (34, 18, 30)
    m.height = 48
    m.front_yaw = -26
    # torso
    m.ell((0, 17.5, -3), (5.2, 5.2, 10.5), 'fur', 'body', rot=(0, -6, 0))
    m.ell((0, 18.5, 5.0), (5.4, 6.0, 5.4), 'fur', 'body')
    m.paint((0, 14.5, 5), (4.6, 5.0, 5), 'cream', ['body'])
    # legs
    for s in (-1, 1):
        m.tube([(s * 3.0, 16, 6), (s * 3.3, 9, 7.2), (s * 3.3, 2.0, 8.2)],
               [2.3, 1.7, 1.6], 'fur', 'legF%d' % s,
               mats=[(0, 'fur'), (0.66, 'sock')])
        m.sph((s * 3.3, 1.7, 8.8), 2.0, 'sock', 'legF%d' % s)
        m.ell((s * 3.4, 17, -10), (2.9, 5, 4.6), 'fur', 'legB%d' % s)
        m.tube([(s * 3.6, 14, -11), (s * 3.8, 7, -13.5), (s * 3.8, 2, -11.6)],
               [2.6, 1.7, 1.6], 'fur', 'legB%d' % s,
               mats=[(0, 'fur'), (0.6, 'sock')])
        m.sph((s * 3.8, 1.7, -11), 2.0, 'sock', 'legB%d' % s)
    # two bushy tails ending in lanterns
    m.tube([(0, 19, -12), (3.5, 23.5, -17), (7.5, 30, -19.5),
            (9.0, 33.5, -19.5)], [2.2, 3.0, 2.8, 1.5], 'fur', 'tailA')
    lantern(m, (9.4, 37.6, -19.2), 4.0, 'lampA', axis=(0.15, 1, 0),
            ribs=5, rib_r=0.55, ember_r=0.86, fur='rib')
    m.tube([(0, 18.5, -12.5), (0.5, 21.5, -19), (0.0, 23.5, -25),
            (-0.5, 24.5, -27.5)], [2.2, 3.0, 2.8, 1.5], 'fur', 'tailB')
    lantern(m, (-0.6, 28.4, -29.0), 4.0, 'lampB', axis=(-0.05, 1, -0.2),
            ribs=5, rib_r=0.55, ember_r=0.86, fur='rib', phase=40)
    # neck + fluffy ruff with ember flecks
    m.tube([(0, 19, 6), (0, 23.5, 8), (0, 27, 9.5)], [3.9, 3.5, 3.3], 'fur',
           'body')
    for k in range(7):
        a = (k - 3) * 30 * DEG
        b = (math.sin(a) * 3.4, 24.5 - abs(k - 3) * 0.6,
             8.2 + math.cos(a) * 2.0)
        d = norm((math.sin(a) * 0.9, -1.0, 0.35 + 0.3 * math.cos(a)))
        m.tube([b, add(b, mul(d, 2.6)), add(b, mul(d, 4.6))],
               [2.3, 1.6, 0.3], 'cream', 'ruff')
    for (x, y, z) in ((-2.2, 22.2, 11.2), (1.8, 21.0, 11.0),
                      (3.6, 23.0, 9.6), (-0.2, 20.2, 11.4)):
        m.paint((x, y, z), 0.75, 'ember', ['ruff'])
    # head
    head_c, head_r = (0, 30.5, 10.5), (6.4, 5.8, 6.0)
    m.ell(head_c, head_r, 'fur', 'head')
    mz_c, mz_r = (0, 28.6, 15.4), (3.3, 2.5, 3.4)
    m.ell(mz_c, mz_r, 'cream', 'head')
    m.paint((0, 27.6, 12.5), (5.2, 2.2, 4.5), 'cream', ['head'])
    for s in (-1, 1):
        m.tube([(s * 3.4, 34.2, 9.4), (s * 5.0, 39.0, 8.6),
                (s * 6.3, 44.5, 7.6)], [3.1, 2.2, 0.2], 'fur', 'ear%d' % s,
               flat=0.4, up=(0, 0.2, 1))
        m.paint((s * 4.4, 37.2, 10.0), (1.4, 2.6, 1.0), 'cream',
                ['ear%d' % s], rot=(0, 0, -s * 18))
        m.tube([(s * 5.4, 28.8, 10.0), (s * 7.8, 27.2, 8.6),
                (s * 9.0, 25.8, 7.4)], [2.0, 1.2, 0.2], 'cream', 'head',
               flat=0.5, up=(0, 0, 1))
    # overworld: fan the two lantern tails out to either side
    m.ow_offsets = {'tailB': (-7.0, -2.0, 4.0), 'lampB': (-9.0, -2.0, 5.0),
                    'tailA': (1.5, 0.0, 0.0), 'lampA': (2.5, -2.0, 0.0)}
    eye_pair(m, head_c, head_r, 32, 14, 3.8, 4.6, style='iris',
             iris=('ember', 0), slant=0.45, center=(0, 29, 20))
    m.dot(on(mz_c, mz_r, (0, 0.35, 1))[0], (0, 0.2, 1), w=1.8, h=1.2, minw=2)
    p, n = on(mz_c, mz_r, (0, -0.35, 1))
    m.mouth(p, n, 'smile', w=2.6)
    return m


# ---- 2 INFERNOX ----------------------------------------------------------
def infernox():
    m = Model('INFERNOX')
    m.outline = (40, 16, 30)
    m.mat('fur', ['#7e1c36', '#bc3230', '#e45a3a', '#fa9464'])
    m.mat('cream', ['#dea57c', '#f6dcad'])
    m.mat('smoke', ['#2c2036', '#4d3a58', '#78628c'])
    m.mat('ember', ['#ffa826', '#ffe45a', '#fffbd0'], emissive=0.85)
    m.mat('rib', ['#7e1c36', '#bc3230', '#e45a3a'])
    m.eye_dark = (40, 16, 30)
    m.white = (255, 251, 208)
    m.height = 58
    m.max_w = 58
    m.front_yaw = -18
    # slender digitigrade legs
    for s in (-1, 1):
        m.ell((s * 3.0, 18.0, -0.6), (2.5, 5.0, 3.0), 'fur', 'leg%d' % s,
              rot=(0, -14, s * 4))
        m.tube([(s * 3.3, 14, 0.2), (s * 3.7, 8.0, -2.2), (s * 3.8, 2.8, -1.2)],
               [1.9, 1.3, 1.1], 'fur', 'leg%d' % s,
               mats=[(0, 'fur'), (0.55, 'smoke')])
        m.tube([(s * 3.8, 2.0, -1.8), (s * 4.0, 1.4, 2.4)], [1.3, 1.4],
               'smoke', 'leg%d' % s)
    # slim torso with cream chest
    m.ell((0, 22.8, -0.6), (4.2, 3.6, 3.3), 'fur', 'body')
    m.ell((0, 27.0, -0.2), (3.8, 3.6, 3.2), 'fur', 'body')
    m.ell((0, 31.2, 0.3), (4.9, 4.4, 3.8), 'fur', 'body')
    m.paint((0, 29.5, 3.2), (2.8, 5.8, 2.0), 'cream', ['body'])
    # bushy tail sweeping up to a lantern held high
    m.tube([(0.5, 21.0, -3.2), (5.5, 18.5, -7.0), (10.5, 21.0, -8.5),
            (12.0, 27.5, -8.2), (11.2, 34.5, -7.4), (12.0, 40.5, -7.2)],
           [1.6, 3.0, 3.5, 2.9, 1.7, 1.1], 'fur', 'tail')
    lantern(m, (12.2, 45.2, -7.2), 4.6, 'lamp', axis=(0.03, 1, 0.0),
            ribs=5, rib_r=0.66, ember_r=0.86, fur='rib')
    # arms: one relaxed, one raised in a guiding gesture
    arms = {-1: ((-4.6, 33.6, 0.4), (-6.8, 28.8, 3.0), (-5.0, 30.8, 7.6)),
            1: ((4.6, 33.6, 0.4), (6.2, 27.0, 0.8), (6.0, 21.6, 2.6))}
    for s in (-1, 1):
        sh_, el, wr = arms[s]
        m.sph(sh_, 2.2, 'fur', 'arm%d' % s)
        m.tube([sh_, el], [1.9, 1.5], 'fur', 'arm%d' % s)
        m.tube([el, wr], [1.5, 1.3], 'fur', 'arm%d' % s,
               mats=[(0, 'fur'), (0.6, 'smoke')])
        m.sph(add(wr, mul(norm(sub(wr, el)), 0.8)), 1.55, 'smoke',
              'arm%d' % s)
    # a little ember floating over the raised paw
    m.sph((-4.8, 34.2, 8.6), 1.3, 'ember', 'spark')
    # neck + head
    m.tube([(0, 35, 0.6), (0, 38.5, 1.6)], [2.6, 2.4], 'fur', 'body')
    head_c, head_r = (0, 42.5, 2.8), (6.0, 5.5, 5.6)
    m.ell(head_c, head_r, 'fur', 'head')
    mz_c, mz_r = (0, 40.4, 8.4), (2.4, 2.1, 3.4)
    m.ell(mz_c, mz_r, 'cream', 'head')
    m.paint((0, 39.4, 5.4), (3.4, 1.9, 3.5), 'cream', ['head'])
    for s in (-1, 1):
        m.tube([(s * 3.0, 46.2, 1.6), (s * 4.6, 51.0, 0.6),
                (s * 5.8, 56.5, -0.4)], [2.7, 1.9, 0.2], 'fur', 'ear%d' % s,
               flat=0.4, up=(0, 0.2, 1))
        m.paint((s * 3.9, 49.2, 2.2), (1.2, 2.6, 0.9), 'cream',
                ['ear%d' % s], rot=(0, 0, -s * 16))
        m.tube([(s * 4.8, 40.6, 2.8), (s * 6.8, 39.4, 1.4),
                (s * 7.6, 38.4, 0.4)], [1.5, 0.9, 0.2], 'fur', 'head',
               flat=0.5, up=(0, 0, 1))
    # hooded mane: a billowing collar of smoke puffs rising behind the head
    hc = (0, 41.5, -2.4)
    rnd = Rand(22)
    for ring, (rr, pr, dz) in enumerate(((7.6, 3.2, 0.0), (5.0, 3.0, -1.4))):
        n = 11 if ring == 0 else 7
        for k in range(n):
            a = (-124 + 248.0 * k / (n - 1)) * DEG
            q = (math.sin(a) * rr * 1.05, hc[1] + math.cos(a) * rr * 1.05,
                 hc[2] + dz - 0.8 * abs(math.sin(a)))
            m.sph(q, pr * (0.85 + 0.3 * rnd.f()), 'smoke', 'hood')
    m.sph((0, 44.0, -4.6), 4.6, 'smoke', 'hood')
    m.sph((0, 39.0, -4.2), 4.4, 'smoke', 'hood')
    for s in (-1, 1):
        m.sph((s * 5.4, 35.4, -1.6), 3.0, 'smoke', 'hood')
    m.tube([(0, 37.0, -3.4), (0.4, 31.0, -4.2), (-0.4, 26.0, -4.6),
            (1.0, 22.0, -5.0), (3.0, 19.5, -5.2)],
           [4.4, 4.0, 3.2, 1.9, 0.3], 'smoke', 'hood')
    # drifting curls at the crown of the hood
    for s in (-1, 1):
        m.tube([(s * 6.4, 47.5, -3.6), (s * 8.6, 50.5, -3.8),
                (s * 7.6, 53.2, -4.0), (s * 5.8, 52.6, -4.0)],
               [1.8, 1.3, 0.8, 0.2], 'smoke', 'hood')
    eye_pair(m, head_c, head_r, 31, 16, 3.6, 4.0, style='glow',
             iris=('ember', 1), slant=0.7, center=(0, 41, 12), glint=True,
             pupil='outline')
    m.dot(on(mz_c, mz_r, (0, 0.35, 1))[0], (0, 0.2, 1), w=1.6, h=1.2, minw=2)
    return m


# ---- 3 AQUAPO ------------------------------------------------------------
def gill(m, base, tip, r, part, mat='gill', face=(0, 0.3, 1), fronds=4,
         flat=0.55):
    fr = fronds

    def rf(t, r=r):
        return r * (0.75 + 0.45 * abs(math.sin(t * math.pi * fr))) * \
            (1 - 0.55 * t)
    mid = add(lerp(base, tip, 0.5), (0, 0.6, 0))
    m.tube([base, mid, tip], None, mat, part, flat=flat, up=face, rfn=rf)


def aquapo():
    m = Model('AQUAPO')
    m.outline = (22, 30, 74)
    m.mat('skin', ['#2c4fa8', '#3f7fd8', '#62aef0', '#a8dcff'])
    m.mat('belly', ['#7fa6d8', '#b8def6', '#eefcff'])
    m.mat('gill', ['#a02a78', '#e0509e', '#ff9ccc'])
    m.eye_dark = (20, 20, 44)
    m.height = 30
    head_c, head_r = (0, 12, 4), (9, 7, 7.4)
    m.ell((0, 7.2, -4.2), (5.6, 5, 7.4), 'skin', 'body')
    m.paint((0, 3.5, -3), (4.5, 3, 8), 'belly', ['body'])
    for s in (-1, 1):
        m.tube([(s * 4.8, 5, 1.5), (s * 6.0, 2.6, 2.8), (s * 6.4, 1.4, 3.4)],
               [1.7, 1.5, 1.5], 'skin', 'legF%d' % s)
        m.tube([(s * 4.4, 5, -8), (s * 5.6, 2.6, -8.4), (s * 6.0, 1.4, -8)],
               [1.8, 1.5, 1.5], 'skin', 'legB%d' % s)
    # tail with fin
    m.tube([(0, 7.5, -10), (1.2, 8.2, -15), (3.4, 9.4, -19.5),
            (5.2, 10.8, -22)], [3.4, 2.6, 1.5, 0.3], 'skin', 'tail',
           flat=0.55, up=(1, 0, 0))
    m.tube([(0, 9.5, -8), (1.2, 9.6, -15), (3.4, 10.4, -19.5),
            (5.4, 11.6, -22.5)], [2.0, 3.8, 3.0, 0.4], 'belly', 'tail',
           flat=0.25, up=(1, 0, 0))
    m.ell(head_c, head_r, 'skin', 'head')
    m.paint((0, 7.5, 7), (7, 3.5, 5), 'belly', ['head'])
    for s in (-1, 1):
        for i in range(3):
            base = (s * 7.4, 13.2 + (i - 1) * 2.6, 0.5)
            tip = (s * 12.6, 14.5 + (i - 1) * 4.6, -2.5)
            gill(m, base, tip, 1.25, 'gill%d' % s, fronds=3)
    eye_pair(m, head_c, head_r, 34, 14, 3.0, 3.6, iris=('skin', 0),
             center=(0, 11, 12))
    p, n = on(head_c, head_r, (0, -0.12, 1))
    m.mouth(p, n, 'smile', w=6.0)
    m.dot(on(head_c, head_r, (-0.5, -0.1, 0.85))[0], (-0.5, 0, 0.85),
          w=1.6, h=1.0, color=('gill', 1), minw=2)
    m.dot(on(head_c, head_r, (0.5, -0.1, 0.85))[0], (0.5, 0, 0.85),
          w=1.6, h=1.0, color=('gill', 1), minw=2)
    return m


# ---- 4 AXOLURK -----------------------------------------------------------
def axolurk():
    m = Model('AXOLURK')
    m.outline = (20, 28, 70)
    m.mat('skin', ['#29489c', '#3a74cc', '#5aa2ea', '#a0d6ff'])
    m.mat('belly', ['#7fa6d8', '#b8def6', '#eefcff'])
    m.mat('gill', ['#962470', '#d84898', '#ff94c8'])
    m.mat('fin', ['#6c8fd0', '#a6cdf4'])
    m.eye_dark = (20, 20, 44)
    m.height = 42
    m.ell((0, 8.8, -3), (6.2, 5.4, 13), 'skin', 'body')
    m.paint((0, 4.2, -2), (5, 3, 13), 'belly', ['body'])
    for s in (-1, 1):
        m.tube([(s * 5.2, 7, 6.5), (s * 8.6, 5, 7.8), (s * 9.2, 1.5, 9.5)],
               [2.1, 1.8, 1.7], 'skin', 'legF%d' % s)
        m.tube([(s * 5.0, 7, -10), (s * 8.6, 5, -11), (s * 9.2, 1.5, -9.5)],
               [2.4, 1.9, 1.7], 'skin', 'legB%d' % s)
    m.tube([(0, 9, -14), (1.5, 10, -21), (5.5, 12, -27), (9.5, 15.5, -30)],
           [4.2, 3.2, 1.9, 0.4], 'skin', 'tail', flat=0.5, up=(1, 0, 0))
    m.tube([(0, 11.5, -12), (1.5, 12.5, -21), (5.5, 14.2, -27),
            (10, 18, -31)], [2.5, 4.4, 3.6, 0.5], 'fin', 'tail', flat=0.2,
           up=(1, 0, 0))
    # dorsal crest
    m.tube([(0, 11.5, 6), (0, 13.2, 0), (0, 13.4, -7), (0, 12.4, -13)],
           [1.0, 3.0, 3.2, 2.0], 'fin', 'crest', flat=0.2, up=(1, 0, 0))
    head_c, head_r = (0, 11.2, 12), (7.6, 5.6, 7)
    m.ell(head_c, head_r, 'skin', 'head')
    m.paint((0, 7.8, 15), (6, 2.6, 5), 'belly', ['head'])
    for s in (-1, 1):
        for i in range(3):
            base = (s * 6.2, 12.5 + (i - 1) * 2.4, 8.5)
            tip = (s * 12.5, 15.0 + (i - 1) * 5.4, 4.5)
            gill(m, base, tip, 1.5, 'gill%d' % s, fronds=4)
    eye_pair(m, head_c, head_r, 38, 20, 2.8, 3.0, style='iris',
             iris=('gill', 1), center=(0, 10, 19))
    p, n = on(head_c, head_r, (0, -0.2, 1))
    m.mouth(p, n, 'smile', w=5.0)
    return m


# ---- 5 TIDALOTL ----------------------------------------------------------
def tidalotl():
    m = Model('TIDALOTL')
    m.outline = (22, 26, 60)
    m.mat('skin', ['#26448e', '#3670c4', '#56a0e6', '#9cd2fc'])
    m.mat('belly', ['#86a6cc', '#bfdcf0', '#eefaff'])
    m.mat('gill', ['#a02a78', '#e0509e', '#ff9ccc'])
    m.mat('fin', ['#6a62c0', '#a8a2ec'])
    m.eye_dark = (22, 20, 40)
    m.height = 56
    m.max_w = 60
    D = norm((0.62, 0, -0.78))           # body runs back and to its left
    N = (-D[2], 0, D[0])                 # horizontal normal (sideways)

    def P(u, y, w=0.0):
        return (D[0] * u + N[0] * w, y, D[2] * u + N[2] * w)
    # (u, y, sideways wiggle, radius): swan-neck S into a low wave + tail
    prof = [(-0.5, 37.0, 0.0, 4.0), (2.0, 33.5, 0.0, 4.4), (3.2, 28.0, 0.2, 4.8),
            (2.8, 22.0, 0.6, 5.2), (4.0, 16.5, 1.0, 5.6), (8.0, 11.5, 1.2, 5.6),
            (13.0, 10.0, 0.8, 5.4), (18.0, 13.0, -0.4, 5.0),
            (22.0, 17.0, -1.2, 4.4), (26.0, 17.5, -1.0, 3.8),
            (30.0, 13.5, 0.0, 3.2), (34.0, 10.5, 1.0, 2.6), (38.0, 12.5, 1.6, 2.0),
            (40.5, 17.0, 2.0, 1.5), (41.0, 21.5, 2.2, 0.9)]
    spine = [P(u, y, w) for u, y, w, r in prof]
    radii = [r * 1.12 for u, y, w, r in prof]
    m.tube(spine, radii, 'skin', 'body')
    # pale throat / belly stripe on the front of the neck and chest
    bel = [add(P(u - r * 0.78, y - r * 0.1, w), (0, 0, 0))
           for u, y, w, r in prof[0:6]]
    m.tube(bel, [r * 0.62 for u, y, w, r in prof[0:6]], 'belly', 'body',
           flat=0.55, up=D)
    # dorsal crest and a paddle tail fin, flat in the body's plane
    crest = []
    crr = []
    for (u, y, w, r) in prof[2:13]:
        crest.append(add(P(u + 0.8, y, w), (0, r * 1.12 + 0.3, 0)))
        crr.append(1.4 if u < 5 else 2.2)
    m.tube(crest, None, 'fin', 'fin', flat=0.25, up=N,
           rfn=lambda t: (1.6 + 1.8 * min(1, t * 3)) *
           (0.7 + 0.3 * abs(math.sin(t * math.pi * 5))))
    m.tube([P(38.5, 13.0, 1.6), P(42.5, 16.5, 2.0), P(44.5, 21.0, 2.2),
            P(43.0, 25.5, 2.2)], [1.6, 3.4, 3.4, 0.5], 'fin', 'fin',
           flat=0.2, up=N)
    m.tube([P(39.5, 20.0, 2.0), P(37.8, 23.5, 2.2), P(38.0, 26.5, 2.2)],
           [1.4, 2.4, 0.4], 'fin', 'fin', flat=0.2, up=N)
    # short legs
    for s in (-1, 1):
        a = add(P(6.5, 12.5, 1.0), mul(N, s * 4.4))
        m.tube([a, add(add(a, (0, -5.0, -0.5)), mul(N, s * 1.6)),
                add(a, (0, -10.5, 2.4))],
               [2.6, 2.1, 1.9], 'skin', 'legF%d' % s)
        f = add(a, (0, -11.1, 3.4))
        for t in (-1, 0, 1):
            m.sph(add(f, mul(N, t * 1.4)), 1.15, 'skin', 'legF%d' % s)
        b = add(P(30.5, 12.5, 0.0), mul(N, s * 3.0))
        m.tube([b, add(b, (0, -5.0, 1.0)), add(b, (0, -8.5, 1.6))],
               [2.2, 1.9, 1.8], 'skin', 'legB%d' % s)
        f = add(b, (0, -9.1, 2.6))
        for t in (-1, 0, 1):
            m.sph(add(f, mul(N, t * 1.3)), 1.05, 'skin', 'legB%d' % s)
    # head: broad axolotl head with a crown of feathery gill frills
    head_c, head_r = add(P(-3.0, 40.0, 0.0), (0, 0, 2.0)), (8.0, 5.6, 6.8)
    m.ell(head_c, head_r, 'skin', 'head')
    m.paint(add(head_c, (0, -3.8, 3.4)), (6.4, 2.0, 4.2), 'belly', ['head'])
    for s in (-1, 1):
        for i in range(3):
            base = add(head_c, (s * 6.4, 0.8 + (i - 1) * 2.8, -2.2))
            tip = add(head_c, (s * 13.5, 3.5 + (i - 1) * 6.6, -5.0))
            gill(m, base, tip, 1.9, 'gill%d' % s, fronds=4)
    eye_pair(m, head_c, head_r, 30, 16, 3.2, 3.6, style='iris',
             iris=('gill', 1), slant=0.35, center=add(head_c, (0, -1, 7)))
    p, n = on(head_c, head_r, (0, -0.3, 1))
    m.mouth(p, n, 'smile', w=6.0)
    for s in (-1, 1):
        m.dot(on(head_c, head_r, (s * 0.52, -0.12, 0.85))[0],
              (s * 0.5, 0, 0.85), w=1.6, h=1.0, color=('gill', 1), minw=2)
    return m


# ---- 6 DANDELAMB --------------------------------------------------------
def leaf(m, base, mid, tip, wdt, mat, part, up=(0, 1, 0.3), flat=0.28,
         mats=None):
    m.tube([base, mid, tip], None, mat, part, flat=flat, up=up, mats=mats,
           rfn=lambda t: wdt * math.sin(math.pi * min(1, t * 1.02)) ** 0.75
           + 0.15)


def dandelamb():
    m = Model('DANDELAMB')
    m.outline = (44, 46, 34)
    m.mat('wool', ['#aaa488', '#d8d4bc', '#f4f2e2', '#ffffff'],
          th=[0.22, 0.5, 0.8])
    m.mat('face', ['#4e8a52', '#7cb86e', '#b0dc96'])
    m.mat('leaf', ['#2c6a2a', '#56a236', '#98d25a'])
    m.eye_dark = (30, 40, 28)
    m.white = (255, 255, 255)
    m.height = 30
    m.front_yaw = -26
    # short legs with green hooves
    for s in (-1, 1):
        for zz, nm in ((2.4, 'F'), (-2.6, 'B')):
            m.tube([(s * 3.8, 6.0, zz), (s * 4.0, 2.4, zz + 0.3)], [1.25, 1.15],
                   'face', 'leg%s%d' % (nm, s))
            m.ell((s * 4.0, 1.3, zz + 0.5), (1.5, 1.3, 1.7), 'leaf',
                  'leg%s%d' % (nm, s))
    # the round dandelion-clock fleece
    bc, br = (0, 12.6, 0.0), (8.6, 8.2, 8.6)
    seedball(m, bc, br, 'wool', 'wool', n=90, fil=0.22, tip=0.6, seed=6,
             skip_below=-0.45, skip_dir=((0, 0.05, 1), 0.8))
    # face peeking out of the front of the puff
    fc, fr = (0, 13.4, 6.6), (4.2, 3.9, 2.9)
    m.ell(fc, fr, 'face', 'face')
    sn_c, sn_r = (0, 12.0, 8.5), (2.5, 2.1, 1.9)
    m.ell(sn_c, sn_r, 'face', 'face')
    # leaf ears
    for s in (-1, 1):
        b = (s * 3.4, 15.4, 6.6)
        leaf(m, b, (s * 6.8, 16.2, 7.4), (s * 10.4, 14.6, 7.0), 2.0, 'leaf',
             'ear%d' % s, up=(0, 1, 0.5), flat=0.3)
    eye_pair(m, fc, fr, 34, 16, 3.6, 4.4, style='closed', center=(0, 12, 12))
    p, n = on(sn_c, sn_r, (0, -0.2, 1))
    m.mouth(p, n, 'smile', w=2.6)
    for s in (-1, 1):
        m.dot(on(fc, fr, (s * 0.62, -0.25, 0.75))[0], (s * 0.6, 0, 0.8),
              w=1.4, h=0.8, color=('face', 2), minw=2)
    return m


# ---- 7 PUFFLEECE --------------------------------------------------------
def curl_horn(m, base, out, up, size, mat, part, turns=1.1, r0=1.2, r1=0.35,
              leaves=None, leaf_mat=None):
    """Fiddlehead / ram-horn spiral starting at base, heading along `out`
    then curling around (in the plane spanned by out and up)."""
    out = norm(out)
    up = norm(sub(up, mul(out, dot(up, out))))
    pts = []
    n = 14
    for i in range(n + 1):
        t = i / float(n)
        a = t * turns * 2 * math.pi
        rad = size * (1.0 - 0.72 * t)
        # start heading 'out', curling toward 'up' then back
        cx = math.sin(a) * rad
        cy = (1 - math.cos(a)) * rad
        pts.append(add(base, add(mul(out, cx), mul(up, cy))))
    m.tube(pts, None, mat, part, rfn=lambda t: r0 + (r1 - r0) * t)
    if leaves:
        npl = norm(cross(out, up))
        cen = add(base, mul(up, size * 0.55))
        for (t, ln, w) in leaves:
            k = int(t * n)
            q = pts[k]
            d = norm(sub(pts[min(n, k + 1)], pts[max(0, k - 1)]))
            sd = norm(cross(d, npl))
            if dot(sd, sub(q, cen)) < 0:
                sd = mul(sd, -1)
            sd = norm(add(sd, mul(npl, 0.5)))
            tip = add(q, mul(sd, ln))
            leaf(m, q, lerp(q, tip, 0.5), tip, w, leaf_mat or mat, part,
                 up=up, flat=0.3)
    return pts


def puffleece():
    m = Model('PUFFLEECE')
    m.outline = (44, 46, 34)
    m.mat('wool', ['#aaa488', '#d8d4bc', '#f4f2e2', '#ffffff'],
          th=[0.22, 0.5, 0.8])
    m.mat('face', ['#4e8a52', '#7cb86e', '#b0dc96'])
    m.mat('leaf', ['#2c6a2a', '#56a236', '#98d25a'])
    m.mat('bloom', ['#e8a818', '#ffe45c'])
    m.eye_dark = (30, 40, 28)
    m.white = (255, 255, 255)
    m.height = 44
    m.front_yaw = -28
    # slender legs with green hooves
    for s in (-1, 1):
        for zz, nm in ((5.0, 'F'), (-6.5, 'B')):
            m.tube([(s * 4.2, 10.0, zz), (s * 4.4, 5.0, zz + 0.4),
                    (s * 4.5, 2.4, zz + 0.6)], [1.25, 1.0, 0.95], 'face',
                   'leg%s%d' % (nm, s))
            m.ell((s * 4.5, 1.3, zz + 0.9), (1.5, 1.3, 1.7), 'leaf',
                  'leg%s%d' % (nm, s))
    # fleece burst into a cloud of seed fluff
    rnd = Rand(77)
    for k, (c, r) in enumerate((((0, 17.0, 1.5), (8.8, 7.6, 8.4)),
                                ((0, 17.5, -6.5), (8.4, 7.8, 7.6)),
                                ((0.5, 23.5, -2.5), (7.0, 5.6, 7.4)),
                                ((-3.5, 21.5, 3.5), (5.0, 4.6, 5.0)),
                                ((4.0, 22.0, -8.0), (5.0, 4.6, 5.0)))):
        seedball(m, c, r, 'wool', 'wool', n=48, fil=0.26, tip=0.66,
                 seed=20 + k, skip_below=-0.5,
                 skip_dir=((0, -0.1, 1), 0.86) if k == 0 else None)
    # little yellow blossoms dotted over the fluff
    blobs = (((0, 17.0, 1.5), (8.8, 7.6, 8.4)), ((0, 17.5, -6.5), (8.4, 7.8, 7.6)),
             ((0.5, 23.5, -2.5), (7.0, 5.6, 7.4)))
    for bi, d in ((2, (0.3, 0.8, 0.5)), (0, (-0.7, 0.5, 0.5)),
                  (0, (0.8, 0.45, 0.4)), (1, (0.9, 0.3, -0.3)),
                  (2, (-0.5, 0.9, -0.2)), (0, (0.55, -0.25, 0.8)),
                  (1, (0.4, 0.6, -0.8)), (1, (0.85, -0.3, 0.3)),
                  (2, (0.9, 0.5, 0.2)), (0, (-0.9, -0.1, 0.4))):
        c, r = blobs[bi]
        p, n = surf(c, r, d)
        q = add(p, mul(n, 0.9))
        m.sph(q, 1.45, 'bloom', 'wool')
        m.paint(add(q, mul(n, 0.8)), 0.6, 'leaf', ['wool'])
    # head poking out of the front of the cloud
    head_c, head_r = (0, 22.0, 9.2), (4.4, 4.2, 4.2)
    m.ell(head_c, head_r, 'face', 'head')
    sn_c, sn_r = (0, 20.2, 12.2), (2.8, 2.4, 2.6)
    m.ell(sn_c, sn_r, 'face', 'head')
    m.tube([(0, 21.0, 5.0), (0, 21.6, 7.5)], [3.2, 3.4], 'face', 'head')
    for s in (-1, 1):
        b = (s * 3.6, 23.2, 8.6)
        leaf(m, b, (s * 6.8, 23.6, 8.8), (s * 10.0, 22.0, 8.0), 2.0, 'leaf',
             'ear%d' % s, up=(0, 1, 0.5), flat=0.3)
        curl_horn(m, (s * 2.4, 25.6, 8.4), (s * 0.8, 0.9, -0.2),
                  (s * 0.1, 0.2, 1.0), 2.2, 'leaf', 'horn%d' % s, turns=0.9,
                  r0=0.9, r1=0.5)
    eye_pair(m, head_c, head_r, 36, 12, 3.2, 3.8, iris=('face', 0),
             center=(0, 21, 14))
    p, n = on(sn_c, sn_r, (0, -0.35, 1))
    m.mouth(p, n, 'smile', w=2.6)
    return m


# ---- 8 ZEPHRAM ----------------------------------------------------------
def zephram():
    m = Model('ZEPHRAM')
    m.outline = (38, 42, 30)
    m.mat('wool', ['#aaa488', '#d8d4bc', '#f4f2e2', '#ffffff'],
          th=[0.22, 0.5, 0.8])
    m.mat('skin', ['#44784c', '#6ea468', '#a4d08c'])
    m.mat('leaf', ['#2c6a2a', '#56a236', '#98d25a'])
    m.mat('vine', ['#5a5a26', '#8c8a3a', '#c2c064'])
    m.eye_dark = (26, 36, 24)
    m.white = (255, 255, 255)
    m.height = 58
    m.max_w = 60
    m.front_yaw = -24
    # slender legs with dark hooves
    for s in (-1, 1):
        for zz, nm in ((7.0, 'F'), (-8.5, 'B')):
            top = (s * 3.8, 15.5, zz)
            m.tube([top, (s * 4.1, 8.5, zz + 0.8), (s * 4.2, 2.6, zz + 0.2)],
                   [2.3, 1.3, 1.1], 'skin', 'leg%s%d' % (nm, s))
            m.ell((s * 4.2, 1.4, zz + 0.6), (1.6, 1.4, 1.9), 'leaf',
                  'leg%s%d' % (nm, s))
    # body with a proud chest
    m.ell((0, 18.0, -1.0), (6.4, 6.0, 11.5), 'skin', 'body', rot=(0, -6, 0))
    m.ell((0, 20.5, 7.5), (6.2, 7.0, 5.8), 'skin', 'body')
    # neck up to a raised head
    m.tube([(0, 22.0, 8.0), (0, 28.0, 10.5), (0, 32.5, 11.5)],
           [4.2, 3.6, 3.4], 'skin', 'body')
    head_c, head_r = (0, 35.5, 12.0), (5.0, 4.8, 4.8)
    m.ell(head_c, head_r, 'skin', 'head')
    sn_c, sn_r = (0, 33.4, 15.6), (3.0, 2.8, 3.2)
    m.ell(sn_c, sn_r, 'skin', 'head')
    # fluffy beard tuft
    seedball(m, (0, 30.2, 13.4), (2.3, 2.5, 2.1), 'wool', 'beard', n=10,
             fil=0.35, tip=0.55, seed=9)
    # the floating cloud of seed fluff riding over the back
    for k, (c, r) in enumerate((((0, 26.0, 2.5), (8.0, 6.2, 6.8)),
                                ((0, 27.5, -6.0), (9.2, 7.4, 8.6)),
                                ((0.5, 26.0, -14.5), (6.8, 5.8, 6.2)),
                                ((1.0, 34.5, -4.5), (7.4, 5.8, 7.2)),
                                ((2.0, 35.0, -12.5), (5.4, 4.6, 5.2)),
                                ((-1.0, 41.0, -7.5), (4.6, 4.0, 4.6)))):
        seedball(m, c, r, 'wool', 'cloud', n=48, fil=0.28, tip=0.66,
                 seed=40 + k, skip_below=-0.35)
    m.sph((0.5, 21.0, -16.5), 2.4, 'wool', 'cloud')
    # big spiral vine horns sweeping back around the ears, sprouting leaves
    for s in (-1, 1):
        curl_horn(m, (s * 2.8, 38.8, 11.0), (s * 0.9, 0.8, -0.7),
                  (s * 0.45, -1.0, -0.2), 5.4, 'vine', 'horn%d' % s,
                  turns=1.2, r0=2.2, r1=0.7,
                  leaves=[(0.3, 4.4, 1.9), (0.62, 4.0, 1.8), (0.93, 3.2, 1.5)],
                  leaf_mat='leaf')
    eye_pair(m, head_c, head_r, 36, 18, 3.2, 3.8, style='iris',
             iris=('leaf', 1), slant=0.5, center=(0, 34, 18))
    p, n = on(sn_c, sn_r, (0, -0.35, 1))
    m.mouth(p, n, 'line', w=2.4)
    m.dot(on(sn_c, sn_r, (0, 0.25, 1))[0], (0, 0.2, 1), w=1.4, h=1.0, minw=2,
          color=('skin', 0))
    return m


# ---- 9 CINDERUB ----------------------------------------------------------
def cinderub():
    m = Model('CINDERUB')
    m.outline = (40, 16, 22)
    m.mat('fur', ['#42162a', '#74242e', '#a63c32', '#d4684c'])
    m.mat('cream', ['#c08a64', '#ecc690', '#fff0cc'])
    m.mat('ember', ['#ff8a1c', '#ffe25a'], emissive=0.9)
    m.eye_dark = (30, 14, 22)
    m.height = 34
    m.ell((0, 9.5, -1), (8.4, 9, 8), 'fur', 'body')
    m.sph((0.5, 5, -8.6), 2.2, 'fur', 'tail')
    m.paint((0, 13, 7), (5.5, 2.4, 3), 'cream', ['body'])
    for s in (-1, 1):
        m.tube([(s * 5, 5, 1), (s * 5.6, 2.6, 5.5)], [3.1, 3.0], 'fur',
               'leg%d' % s)
        m.paint((s * 5.6, 2.4, 8.2), (2.4, 2.2, 1.2), 'cream', ['leg%d' % s])
        m.tube([(s * 7, 14.5, 1.5), (s * 8.2, 10.5, 4.5), (s * 7.4, 8.6, 6.8)],
               [2.7, 2.4, 2.4], 'fur', 'arm%d' % s)
    head_c, head_r = (0, 21, 2), (8, 7.2, 7.2)
    m.ell(head_c, head_r, 'fur', 'head')
    m.ell((0, 18.2, 8.6), (4.0, 2.9, 2.6), 'cream', 'head')
    for s in (-1, 1):
        m.ell((s * 5.8, 27.0, 0), (2.9, 2.9, 1.7), 'fur', 'ear%d' % s,
              rot=(s * 15, 0, 0))
        m.paint((s * 5.9, 27.0, 1.5), (1.7, 1.7, 1), 'cream', ['ear%d' % s])
    p, n = on(head_c, head_r, (0, 0.62, 0.78))
    m.paint(p, (1.8, 2.4, 1.6), 'ember', ['head'])
    m.paint(add(p, (-1.9, -0.6, -0.4)), (0.9, 1.3, 1.2), 'ember', ['head'])
    m.paint(add(p, (1.9, -0.6, -0.4)), (0.9, 1.3, 1.2), 'ember', ['head'])
    eye_pair(m, head_c, head_r, 30, 8, 3.8, 4.6, iris=('fur', 2),
             center=(0, 18, 11))
    m.dot(on((0, 18.2, 8.6), (4.0, 2.9, 2.6), (0, 0.6, 1))[0], (0, 0, 1),
          w=2.4, h=1.4, minw=2)
    p, n = on((0, 18.2, 8.6), (4.0, 2.9, 2.6), (0, -0.4, 1))
    m.mouth(p, n, 'open', w=3.0, h=2.0, inner=('fur', 1))
    return m


# ---- 10 MAGMAUL ----------------------------------------------------------
def magmaul():
    m = Model('MAGMAUL')
    m.outline = (22, 12, 18)
    m.mat('fur', ['#261a22', '#422c34', '#624448', '#8a6664'])
    m.mat('rock', ['#4c444e', '#786e78', '#aa9ea6'])
    m.mat('magma', ['#e8501a', '#ffa22a', '#ffe676'], emissive=0.9)
    m.mat('claw', ['#786e78', '#aa9ea6'])
    m.mat('muzzle', ['#6e5654', '#a2807a'])
    m.eye_dark = (24, 12, 16)
    m.height = 58
    m.max_w = 62
    # stout legs
    for s in (-1, 1):
        m.ell((s * 6.6, 12, 0), (5.2, 7, 5.6), 'fur', 'leg%d' % s)
        m.ell((s * 7.2, 2.6, 3), (4.0, 2.6, 5.2), 'fur', 'leg%d' % s)
        for t in (-1, 0, 1):
            m.crystal((s * 7.2 + t * 2.0, 1.4, 6.8),
                      (s * 7.2 + t * 2.3, 0.5, 9.0), 0.8, 'claw',
                      'leg%d' % s, sides=4, tip_frac=0.8)
    m.ell((0, 21.5, 0), (10.6, 11, 8.6), 'fur', 'body')
    m.ell((0, 31, 1.2), (11.8, 8.4, 8.2), 'fur', 'body')
    m.rock((0, 38, -5.5), (7, 5, 5), 'rock', 'back0', seed=21, n=14)
    # arms: boulder shoulders, heavy clawed paws
    for s in (-1, 1):
        shp = (s * 11.5, 33.5, 1)
        el = (s * 15.5, 25, 3.5)
        pw = (s * 14.8, 16.5, 7.5)
        m.tube([shp, el, pw], [4.8, 4.2, 4.0], 'fur', 'arm%d' % s)
        m.sph(pw, 4.6, 'fur', 'arm%d' % s)
        for t in (-1, 0, 1):
            m.crystal(add(pw, (t * 1.9, -3.0, 2.4)),
                      add(pw, (t * 2.3, -6.2, 4.2)), 0.9, 'claw',
                      'arm%d' % s, sides=4, tip_frac=0.85)
        m.rock((s * 11.8, 37.5, 0.5), (6.4, 5.4, 6.4), 'rock', 'sh%d' % s,
               seed=4 + s, n=15)
    # head, jutting forward
    head_c, head_r = (0, 41.5, 6.0), (7.6, 6.9, 6.8)
    m.ell(head_c, head_r, 'fur', 'head')
    mz_c, mz_r = (0, 38.6, 11.6), (4.4, 3.3, 3.4)
    m.ell(mz_c, mz_r, 'muzzle', 'head')
    for s in (-1, 1):
        m.ell((s * 5.8, 47.6, 3.6), (2.7, 2.7, 1.7), 'fur', 'head')
        m.paint((s * 5.9, 47.7, 4.8), (1.5, 1.5, 1.0), 'magma', ['head'])
    # glowing fissures: one down the chest, seams under the rock pauldrons
    cracks = [
        [(0, 34.0, 9.0), (-1.4, 30.5, 9.4), (0.6, 26.5, 9.0), (-0.8, 22.0, 8.6),
         (0.4, 17.0, 8.2)],
        [(0.6, 27.0, 9.8), (3.6, 24.0, 9.2)],
        [(-0.8, 22.0, 9.2), (-3.8, 19.5, 8.8)],
        [(0, 38.0, -7.6), (1.8, 33.0, -8.4), (-0.6, 28.0, -8.6),
         (1.4, 22.0, -8.2)],
        [(-0.6, 28.0, -8.6), (-3.6, 25.0, -8.0)],
    ]
    for cr in cracks:
        for i in range(len(cr) - 1):
            a, b = cr[i], cr[i + 1]
            for k in range(7):
                m.paint(lerp(a, b, k / 6.0), (0.95, 0.95, 3.2), 'magma',
                        ['body'])
    for s in (-1, 1):
        for k in range(9):
            a = (k / 8.0) * math.pi
            q = (s * 11.8 + math.cos(a) * 6.2, 33.2, 0.5 + math.sin(a) * 5.4)
            m.paint(q, 1.0, 'magma', ['body', 'arm%d' % s])
    eye_pair(m, head_c, head_r, 32, 16, 3.8, 3.2, style='glow',
             iris=('magma', 2), slant=0.6, center=(0, 38, 15), turn=6)
    p, n = on(mz_c, mz_r, (0.1, -0.45, 1))
    m.mouth(p, n, 'smile', w=3.6, fang=1)
    m.dot(on(mz_c, mz_r, (0.1, 0.55, 1))[0], (0, 0.2, 1), w=2.6, h=1.6,
          minw=2)
    return m


# ---- 11 BUBBLIN ----------------------------------------------------------
def bubblin():
    m = Model('BUBBLIN')
    m.outline = (18, 34, 84)
    m.mat('water', ['#2250b0', '#3c88e4', '#6cc2f8', '#b8eeff'], spec=0.6)
    m.mat('deep', ['#3a6cd0', '#8ad6fa'])
    m.eye_dark = (16, 24, 56)
    m.height = 30
    body_c, body_r = (0, 9.6, 0), (9.6, 9.0, 9.2)
    m.ell(body_c, body_r, 'water', 'body')
    m.tube([(0, 13.5, -0.6), (0, 19, -1.4), (1.2, 23.5, -2.2),
            (2.8, 26.4, -2.8)], [7.4, 4.2, 1.8, 0.2], 'water', 'body')
    m.paint((2.5, 4.5, 6), (6, 3.6, 4.5), 'deep', ['body'])
    for s in (-1, 1):
        m.ell((s * 4.2, 1.3, 3.2), (2.5, 1.4, 2.6), 'water', 'foot%d' % s)
    p, n = on(body_c, body_r, (-0.62, 0.55, 0.56))
    m.dot(p, n, w=2.6, h=4.2, color='white', shape='oval', minw=2, minh=3)
    p, n = on(body_c, body_r, (-0.78, 0.18, 0.6))
    m.dot(p, n, w=1.2, h=1.2, color='white', minw=1)
    eye_pair(m, body_c, body_r, 24, 14, 3.6, 4.8, iris=('water', 1),
             center=(0, 8, 10))
    p, n = on(body_c, body_r, (0.05, -0.12, 1))
    m.mouth(p, n, 'open', w=3.4, h=2.2, inner=('water', 0))
    return m


# ---- 12 GLACIBLOB --------------------------------------------------------
def glacibloob():
    m = Model('GLACIBLOB')
    m.outline = (22, 40, 88)
    m.mat('ice', ['#4a82c4', '#7cbce8', '#b8e6f8', '#f2fdff'])
    m.mat('core', ['#1c3a90', '#2a60c2', '#4c90e6'])
    m.mat('spike', ['#6aaee4', '#c6f0ff', '#ffffff'])
    m.eye_dark = (18, 26, 64)
    m.height = 46
    body_c, body_r = (0, 12.5, 0), (13, 12, 11.5)
    m.rock(body_c, body_r, 'ice', 'body', seed=5, n=26, jitter=0.05,
           shrink=0.96)
    m.paint((0.5, 10, 7), (7.5, 6.5, 6), 'core', ['body'])
    spikes = [(0, 1, 0, 13), (-0.55, 0.85, 0.2, 10), (0.55, 0.85, 0.15, 10.5),
              (-0.3, 0.8, -0.55, 9), (0.35, 0.8, -0.5, 9.5),
              (-0.85, 0.55, -0.1, 7), (0.85, 0.5, -0.2, 7.5)]
    for k, (dx, dy, dz, ln) in enumerate(spikes):
        d = norm((dx, dy, dz))
        base = add(body_c, (d[0] * 7, d[1] * 8, d[2] * 7))
        m.crystal(base, add(base, mul(d, ln + 2)), 2.2 if k == 0 else 1.8,
                  'spike', 'spike%d' % k, sides=5, tip_frac=0.45,
                  twist=k * 23)
    eye_pair(m, body_c, (12, 11, 11.2), 26, 12, 4.0, 4.8, style='iris',
             iris=('core', 1), center=(0, 10, 12))
    p, n = on(body_c, (12, 11, 11.2), (0, -0.2, 1))
    m.mouth(p, n, 'smile', w=4.0)
    for q in ((-10, 22, 4), (11, 8, 6), (-6, 4, 9)):
        m.sparkle(q, (0, 0, 1), size=1)
    return m


# ---- 13 THORNIP ----------------------------------------------------------
def poly_local(m, origin, uvec, vvec, pts, mat, part=None, puff=0.4,
               su=1.0, sv=1.0):
    P = [add(origin, add(mul(uvec, u * su), mul(vvec, v * sv)))
         for u, v in pts]
    return m.poly(P, mat, part, puff)


BOLT = [(-0.20, 0.0), (0.20, 0.0), (0.06, 0.40), (0.32, 0.40), (0.0, 1.0),
        (0.06, 0.60), (-0.20, 0.60)]


def jagged_leaf(m, base, d, ln, wdt, mat, part, up, teeth=3, flat=0.3):
    tip = add(base, mul(d, ln))
    mid = add(lerp(base, tip, 0.5), mul(up, ln * 0.08))
    m.tube([base, mid, tip], None, mat, part, flat=flat, up=up,
           rfn=lambda t: (wdt * math.sin(math.pi * min(1, t * 1.02)) ** 0.7) *
           (0.72 + 0.28 * abs(math.sin(t * math.pi * teeth))) + 0.15)


def thornip():
    m = Model('THORNIP')
    m.outline = (46, 18, 50)
    m.mat('skin', ['#5a2268', '#943a8e', '#c85ca8', '#f092c8'])
    m.mat('root', ['#d6aad0', '#fff0f8'])
    m.mat('leaf', ['#2c7630', '#5aae3e', '#aade6c'])
    m.eye_dark = (36, 14, 40)
    m.height = 32
    body_c, body_r = (0, 11.5, 0), (9, 8.6, 8.4)
    m.ell(body_c, body_r, 'skin', 'body')
    m.tube([(0, 4.5, -3.5), (1.2, 2.6, -8.5), (3.4, 3.8, -12.0),
            (4.6, 5.4, -13.2)], [3.2, 1.8, 0.8, 0.2], 'root', 'roottail')
    m.tube([(0, 18.5, -0.4), (0, 20.5, -0.6)], [3.0, 1.4], 'skin', 'body')
    for s in (-1, 1):
        m.ell((s * 3.6, 1.3, 2.8), (2.1, 1.3, 2.4), 'root', 'foot%d' % s)
    for k, (dx, dy, dz, ln) in enumerate(((0, 1, -0.1, 11),
                                          (-0.7, 0.8, 0.1, 9),
                                          (0.7, 0.8, 0.05, 9.5),
                                          (-0.35, 0.8, -0.6, 8.5),
                                          (0.4, 0.8, -0.6, 8))):
        d = norm((dx, dy, dz))
        up = norm(cross(d, (0.9, 0, -0.4) if abs(d[0]) < 0.3 else (0, 0, 1)))
        jagged_leaf(m, (0, 20, -0.6), d, ln, 2.8, 'leaf', 'leaf%d' % k,
                    up=up if up[2] >= 0 else mul(up, -1))
    eye_pair(m, body_c, body_r, 27, 12, 4.0, 4.4, iris=('skin', 1),
             slant=0.7, center=(0, 11, 9))
    p, n = on(body_c, body_r, (0.06, -0.12, 1))
    m.mouth(p, n, 'smile', w=5.0, fang=1)
    return m


# ---- 14 BRAMBLOR ---------------------------------------------------------
def bramblor():
    m = Model('BRAMBLOR')
    m.outline = (14, 12, 20)
    m.mat('vine', ['#1c1a26', '#2e3c30', '#4a6644', '#7e9c5a'],
          th=[0.26, 0.56, 0.9])
    m.mat('wrap', ['#2e3c30', '#4a6644', '#7e9c5a', '#a8c474'])
    m.mat('thorn', ['#3c1a52', '#76349e', '#b468d6'])
    m.mat('glow', ['#ffc02c', '#fff49e'], emissive=0.9)
    m.mat('leaf', ['#4c9a3a', '#9ad660'])
    m.eye_dark = (20, 10, 24)
    m.height = 54
    m.max_w = 62
    rnd = Rand(14)
    # legs
    for s in (-1, 1):
        m.tube([(s * 4.2, 17, -2), (s * 6.2, 9, -1), (s * 6.6, 2.2, 1.5)],
               [3.4, 2.8, 2.6], 'vine', 'leg%d' % s)
        m.tube([(s * 3.6, 16, -3), (s * 7.4, 8, -2.4), (s * 6.0, 3, 0)],
               [1.2, 1.1, 1.0], 'vine', 'leg%d' % s)
        for t in (-1, 1):
            m.crystal((s * 6.6 + t * 1.4, 1.4, 3.0),
                      (s * 7.0 + t * 2.6, 0.6, 6.5), 1.0, 'thorn',
                      'leg%d' % s, sides=4, tip_frac=0.8)
    # hunched torso
    m.ell((0, 24, -2), (8.6, 9.6, 7.6), 'vine', 'body', rot=(0, 28, 0))
    # wrapping vines with thorns
    for k in range(5):
        ph = k * 1.25
        pts = []
        for i in range(7):
            t = i / 6.0
            ang = ph + t * 4.4
            y = 16 + t * 17
            rr = 8.6 - 2.6 * abs(t - 0.45)
            pts.append((math.sin(ang) * rr, y, math.cos(ang) * rr * 0.9 +
                        (t - 0.5) * 5 - 1))
        m.tube(pts, 1.5 + 0.25 * (k % 2), 'wrap', 'wrap%d' % k)
        for i in range(1, 6):
            if rnd.f() < 0.75:
                q = pts[i]
                d = norm((q[0], 0.4, q[2] + 1))
                m.crystal(sub(q, mul(d, 0.4)), add(q, mul(d, 4.0)), 1.1,
                          'thorn', 'wrap%d' % k, sides=4, tip_frac=0.85)
    # head (low and forward)
    head_c, head_r = (0, 32.5, 8.8), (7.0, 6.2, 6.2)
    m.ell(head_c, head_r, 'vine', 'head')
    # paler bark mask so the face reads
    m.paint(add(head_c, (0, -0.8, 5.0)), (5.6, 3.6, 2.6), 'wrap', ['head'])
    for k, (dx, dz, ln, w) in enumerate(((-0.55, -0.3, 8, 2.6),
                                         (0.1, -0.5, 10, 3.0),
                                         (0.65, -0.2, 8.5, 2.6))):
        b = add(head_c, (dx * 3.5, 4.2, dz * 3))
        d = norm((dx, 1, dz))
        leaf(m, b, add(b, mul(d, ln * 0.5)), add(b, mul(d, ln)), w, 'leaf',
             'crown%d' % k, up=(0, 0.2, 1), flat=0.3)
    for d in ((-0.85, 0.4, 0.2), (0.85, 0.35, 0.2), (-0.4, 0.3, -0.8),
              (0.45, 0.2, -0.8)):
        p, n = on(head_c, head_r, d)
        m.crystal(sub(p, mul(n, 0.6)), add(p, mul(n, 3.6)), 1.1, 'thorn',
                  'head', sides=4, tip_frac=0.85)
    # long arms reaching down to big thorn claws
    for s in (-1, 1):
        shp = (s * 8.4, 28.5, 2)
        el = (s * 13.5, 20, 4.5)
        hd = (s * 13, 9.5, 8.5)
        m.tube([shp, el, hd], [3.0, 2.5, 2.4], 'vine', 'arm%d' % s)
        m.tube([add(shp, (0, 1, -1)), add(el, (s * 1.4, 0.5, -1)),
                add(hd, (0, 2, -0.5))], [1.2, 1.1, 1.0], 'vine', 'arm%d' % s)
        for t in (-1, 0, 1):
            m.crystal(add(hd, (t * 1.5, -0.5, 0.5)),
                      add(hd, (t * 2.8 + s * 0.6, -6.5, 2.8)), 1.1, 'thorn',
                      'claw%d' % s, sides=4, tip_frac=0.85)
        for u in (0.3, 0.7):
            q = lerp(shp, el, u * 2) if u < 0.5 else lerp(el, hd, u)
            m.crystal(q, add(q, (s * 3.6, 1.8, -1.2)), 1.0, 'thorn',
                      'arm%d' % s, sides=4, tip_frac=0.85)
    eye_pair(m, head_c, head_r, 30, 10, 4.2, 4.4, style='glow',
             iris=('glow', 1), slant=0.6, center=(0, 31, 15), glint=True,
             turn=6, pupil='outline')
    p, n = on(head_c, head_r, (0.1, -0.42, 1))
    m.mouth(p, n, 'open', w=5.0, h=2.4, color='outline', inner='eye',
            fang=1)
    # clusters of purple poison berries
    for (c, k0) in (((-8.6, 30.5, 2.5), 0), ((8.2, 30.0, 1.5), 3),
                    ((3.8, 38.2, 5.0), 6), ((-12.6, 17.0, 6.8), 9)):
        for k in range(4):
            a = (k0 + k) * 2.1
            q = add(c, (math.cos(a) * 1.3, (k % 2) * 1.2 - 0.4,
                        math.sin(a) * 1.3 + 0.6))
            m.sph(q, 1.25, 'thorn', 'berries')
    return m


# ---- 15 MOSSHELL ---------------------------------------------------------
def shell_spiral(m, c, r, side, mat, part, turns=2.0, n=70, dot_r=0.55,
                 rot=None, spread=1.55):
    """Paint a spiral groove on the +X (side=1) or -X face of a shell."""
    for i in range(n):
        t = i / float(n - 1)
        a = t * turns * 2 * math.pi
        rad = 0.10 + 0.80 * t
        d = (side * 1.0, math.sin(a) * rad * spread,
             -math.cos(a) * rad * spread)
        p, nn = surf(c, r, d, rot)
        m.paint(p, dot_r * (0.7 + 0.5 * t), mat, [part])


def mosshell():
    m = Model('MOSSHELL')
    m.outline = (40, 30, 22)
    m.mat('skin', ['#9a6a4a', '#d09a70', '#f4cca0'])
    m.mat('shell', ['#6a4424', '#9a6a36', '#c89a58', '#ecc884'])
    m.mat('moss', ['#3c7a2c', '#6cae3c', '#b0dc6a'])
    m.mat('eyeball', ['#c4bcb4', '#ffffff'])
    m.eye_dark = (30, 22, 16)
    m.white = (255, 255, 255)
    m.height = 30
    m.front_yaw = -32
    # soft foot + neck + head
    m.ell((0, 3.0, 0.5), (4.4, 3.0, 11.0), 'skin', 'foot')
    m.tube([(0, 3.0, -8.0), (0.8, 2.4, -12.0), (1.4, 1.8, -13.6)],
           [2.8, 1.6, 0.4], 'skin', 'foot')
    m.tube([(0, 4.0, 5.5), (0, 7.5, 9.0), (0, 10.0, 10.2)], [3.6, 3.4, 3.3],
           'skin', 'foot')
    head_c, head_r = (0, 11.2, 10.8), (4.0, 3.8, 3.6)
    m.ell(head_c, head_r, 'skin', 'head')
    m.group('head', 'foot')
    # eye stalks with big eyeballs
    eyes = []
    for s in (-1, 1):
        b = (s * 1.8, 13.8, 11.0)
        t = (s * 3.8, 22.0, 12.2)
        m.tube([b, lerp(b, t, 0.5), t], [1.1, 0.85, 0.8], 'skin', 'stalk%d' % s)
        m.sph(t, 2.5, 'eyeball', 'stalk%d' % s)
        eyes.append(t)
        # little feelers by the mouth
        m.tube([(s * 2.2, 9.6, 13.4), (s * 3.2, 8.6, 15.2)], [0.8, 0.5],
               'skin', 'head')
    # round mossy shell
    sc, sr = (0, 11.6, -3.6), (6.2, 8.8, 8.8)
    m.ell(sc, sr, 'shell', 'shell')
    m.mat('groove', [m.outline])
    shell_spiral(m, sc, sr, 1, 'groove', 'shell')
    # moss cap over the top of the shell with a bumpy edge
    m.paint(add(sc, (0, 6.4, 0)), (7.4, 3.6, 9.6), 'moss', ['shell'])
    for (d, rr) in (((0.7, 0.45, 0.3), 1.8), ((0.75, 0.3, -0.45), 2.0),
                    ((0.6, 0.2, 0.7), 1.5)):
        p, n = surf(sc, sr, d)
        m.paint(p, rr, 'moss', ['shell'])
    rnd = Rand(15)
    for k in range(9):
        a = (k / 9.0) * 2 * math.pi
        d = (math.cos(a) * 0.62, 0.72, math.sin(a) * 0.62)
        p, n = surf(sc, sr, d)
        m.sph(add(p, mul(n, 0.1)), 1.3 + 0.4 * rnd.f(), 'moss', 'shell')
    top, tn = surf(sc, sr, (0, 1, 0.1))
    m.sph(add(top, (0, 0.6, 0)), 2.0, 'moss', 'shell')
    q = add(top, (0.2, 2.2, 0.2))
    m.tube([add(top, (0, 1.2, 0)), q], [0.55, 0.5], 'moss', 'sprout')
    for s in (-1, 1):
        leaf(m, q, add(q, (s * 1.2, 0.8, 0.3)), add(q, (s * 2.4, 0.4, 0.4)),
             0.9, 'moss', 'sprout', up=(0, 1, 0.3))
    for s, t in zip((-1, 1), eyes):
        p, n = on(t, 2.5, (0.36, 0.0, 1))
        m.eye(p, n, 2.2, 3.0, center=(0, 20, 16))
    p, n = on(head_c, head_r, (0.0, -0.72, 0.7))
    m.mouth(p, (0, -0.3, 1), 'smile', w=2.6)
    return m


# ---- 16 TERRASHELL -------------------------------------------------------
def terrashell():
    m = Model('TERRASHELL')
    m.outline = (32, 26, 22)
    m.mat('skin', ['#8a5c3e', '#c08a60', '#eabc8c'])
    m.mat('shell', ['#5a3c26', '#8a6034', '#b88c50'])
    m.mat('stone', ['#4e505e', '#7c7e8e', '#aeb0bc'])
    m.mat('moss', ['#356e2a', '#62a238', '#a8d666'])
    m.mat('eyeball', ['#aeb0bc', '#ffffff'])
    m.eye_dark = (30, 22, 16)
    m.white = (255, 255, 255)
    m.height = 56
    m.max_w = 62
    m.front_yaw = -32
    # broad soft foot, neck and head
    m.ell((0, 4.4, 0.5), (7.4, 4.4, 17.0), 'skin', 'foot')
    m.tube([(0, 4.2, -13.0), (1.0, 3.0, -18.5), (1.8, 2.2, -21.0)],
           [4.0, 2.2, 0.5], 'skin', 'foot')
    m.tube([(0, 6.0, 10.0), (0, 11.5, 14.5), (0, 15.0, 16.0)],
           [5.6, 5.2, 5.0], 'skin', 'foot')
    head_c, head_r = (0, 17.0, 16.6), (5.8, 5.4, 5.2)
    m.ell(head_c, head_r, 'skin', 'head')
    m.group('head', 'foot')
    eyes = []
    for s in (-1, 1):
        b = (s * 2.6, 20.8, 16.6)
        t = (s * 5.6, 30.0, 18.0)
        m.tube([b, lerp(b, t, 0.5), t], [1.6, 1.2, 1.1], 'skin',
               'stalk%d' % s)
        m.sph(t, 3.2, 'eyeball', 'stalk%d' % s)
        eyes.append(t)
        m.tube([(s * 3.2, 14.4, 20.4), (s * 4.6, 12.8, 23.0)], [1.1, 0.6],
               'skin', 'head')
    # big round shell with a spiral groove and a moss cap
    sc, sr = (0, 17.5, -5.5), (9.4, 12.6, 13.2)
    m.ell(sc, sr, 'shell', 'shell')
    m.mat('groove', [m.outline])
    shell_spiral(m, sc, sr, 1, 'groove', 'shell', n=90, dot_r=0.75)
    m.paint(add(sc, (0, 9.4, 0)), (10.5, 4.6, 13.0), 'moss', ['shell'])
    rnd = Rand(16)
    for k in range(11):
        a = (k / 11.0) * 2 * math.pi
        d = (math.cos(a) * 0.6, 0.62, math.sin(a) * 0.6)
        p, n = surf(sc, sr, d)
        m.sph(add(p, mul(n, 0.2)), 1.8 + 0.6 * rnd.f(), 'moss', 'shell')
    # mossy cairn of stacked stones
    stones = [((0.0, 30.5, -5.0), (7.2, 2.8, 6.6), 51),
              ((0.8, 35.2, -5.6), (5.4, 2.5, 5.0), 52),
              ((-0.4, 39.4, -5.0), (3.9, 2.3, 3.8), 53),
              ((0.3, 43.0, -5.3), (2.5, 1.7, 2.5), 54)]
    for k, (c, r, sd) in enumerate(stones):
        m.rock(c, r, 'stone', 'stone%d' % k, seed=sd, n=16, jitter=0.12,
               rot=(k * 37, 0, 0))
        m.paint(add(c, (0, r[1] * 0.9, 0)), (r[0] * 0.7, r[1] * 0.5,
                                              r[2] * 0.7), 'moss',
                ['stone%d' % k])
    # ferns unfurling from between the stones
    for (b, d, ln, w) in (((3.5, 33.0, -3.0), (1.0, 0.55, 0.35), 9.0, 1.9),
                          ((-4.0, 32.8, -6.5), (-1.0, 0.6, -0.1), 8.0, 1.8),
                          ((2.0, 37.8, -7.5), (0.6, 0.9, -0.5), 7.0, 1.6),
                          ((-2.2, 41.5, -4.0), (-0.6, 1.0, 0.2), 6.0, 1.4),
                          ((1.0, 33.5, -10.5), (0.3, 0.5, -1.0), 7.0, 1.6)):
        d = norm(d)
        up = norm(cross(d, (0, 0, 1) if abs(d[2]) < 0.7 else (1, 0, 0)))
        if up[1] < 0:
            up = mul(up, -1)
        jagged_leaf(m, b, d, ln, w, 'moss', 'fern', up=up, teeth=4)
    for s, t in zip((-1, 1), eyes):
        p, n = on(t, 3.2, (0.36, 0.0, 1))
        m.eye(p, n, 2.8, 3.8, center=(0, 28, 22))
    p, n = on(head_c, head_r, (0.0, -0.72, 0.7))
    m.mouth(p, (0, -0.3, 1), 'smile', w=3.2)
    return m


# ---- 17 ZAPPET -----------------------------------------------------------
def zappet():
    m = Model('ZAPPET')
    m.outline = (58, 38, 16)
    m.mat('fluff', ['#b8761a', '#eab424', '#ffe04c', '#fff6aa'])
    m.mat('orange', ['#c2481c', '#f27c2c', '#ffb466'])
    m.mat('spark', ['#ffe04c', '#fffce4'], emissive=0.55)
    m.eye_dark = (40, 24, 12)
    m.height = 30
    body_c, body_r = (0, 10.5, 0), (9, 9, 8.6)
    for s in (-1, 1):
        m.tube([(s * 3.2, 3, 1), (s * 3.4, 0.9, 2.5)], [1.0, 0.9], 'orange',
               'foot%d' % s)
        for t in (-1, 0, 1):
            m.tube([(s * 3.4, 0.9, 2.5), (s * 3.4 + t * 1.3, 0.8, 4.4)],
                   [0.8, 0.6], 'orange', 'foot%d' % s)
    # zigzag spark tail feathers (bolts)
    for k, (ang, sc) in enumerate(((-38, 0.95), (0, 1.2), (38, 0.95))):
        a = ang * DEG
        up = norm((math.sin(a) * 1.0, 0.8, -0.55))
        uu = norm(cross(up, (0.5, 0, 0.87)))
        org = (math.sin(a) * 3.5, 9 + abs(ang) * 0.02, -6.5)
        poly_local(m, org, uu, up, BOLT, 'spark', 'tail%d' % k, puff=0.3,
                   su=10 * sc, sv=14 * sc)
    m.ell(body_c, body_r, 'fluff', 'body')
    for s in (-1, 1):
        m.ell((s * 8.4, 9.6, -0.8), (1.6, 4.2, 3.6), 'fluff', 'wing%d' % s,
              rot=(s * 10, 0, s * 18))
        p, n = on(body_c, body_r, (s * 0.72, -0.12, 0.66))
        m.paint(p, (1.9, 1.5, 1.9), 'orange', ['body'])
    # head tuft bolt
    poly_local(m, (0.5, 17.2, 1.5), (0.87, 0, -0.5), norm((0.1, 1, -0.25)),
               BOLT, 'fluff', 'tuft', puff=0.3, su=6.5, sv=9)
    m.tube([(0, 11.2, 7.8), (0, 10.4, 10.6)], [1.8, 0.4], 'orange', 'beak')
    eye_pair(m, body_c, body_r, 25, 16, 3.6, 4.6, iris=('fluff', 0),
             center=(0, 10, 11))
    return m


# ---- 18 STORMHAWK --------------------------------------------------------
def stormhawk():
    m = Model('STORMHAWK')
    m.outline = (18, 20, 34)
    m.mat('gold', ['#aa7414', '#e2ae22', '#ffdc44', '#fff2a0'])
    m.mat('dark', ['#1c2036', '#343a5c', '#56608a'])
    m.mat('white', ['#b8bed0', '#eef2ff'])
    m.mat('horn', ['#3c4268', '#8a92bc', '#cfd6f0'])
    m.eye_dark = (20, 18, 30)
    m.height = 58
    m.max_w = 62
    # legs + talons
    for s in (-1, 1):
        m.tube([(s * 3.6, 14, 0.5), (s * 3.9, 7, 1.5), (s * 4.0, 2.2, 2.2)],
               [2.6, 1.7, 1.5], 'gold', 'leg%d' % s,
               mats=[(0, 'dark'), (0.3, 'gold')])
        for t in (-1, 0, 1):
            m.crystal((s * 4.0 + t * 1.3, 1.6, 3.0),
                      (s * 4.0 + t * 2.4, 0.4, 6.6), 0.8, 'dark', 'leg%d' % s,
                      sides=4, tip_frac=0.8)
    # tail fan
    for k in range(5):
        a = (k - 2) * 15 * DEG
        d = norm((math.sin(a), -0.6, -1))
        leaf(m, (0, 17, -4), add((0, 17, -4), mul(d, 7)),
             add((0, 17, -4), mul(d, 14)), 2.6, 'dark', 'tail',
             up=(0, 1, -0.4), flat=0.25)
    # wings: gold coverts + dark jagged primaries
    for s in (-1, 1):
        sh_ = (s * 6.5, 30, -1)
        el = (s * 14, 36, -3)
        wr = (s * 21.5, 43, -5)
        m.tube([sh_, el, wr], [3.0, 2.2, 1.5], 'gold', 'wing%d' % s)
        pts = [sh_, el, wr, (s * 24.5, 42, -5.5), (s * 21, 35, -4.5),
               (s * 19, 32, -4), (s * 15, 28, -3), (s * 12, 26, -2.5),
               (s * 8, 23, -1.5)]
        m.poly(pts, 'gold', 'wing%d' % s, puff=0.25)
        for k in range(6):
            t = k / 5.0
            b = lerp(el, (s * 24.5, 43, -5.5), t)
            d = norm((s * (0.35 + 0.6 * t), -0.45 + 0.95 * t, -0.1))
            ln = 12 - 3 * abs(t - 0.7)
            leaf(m, b, add(b, mul(d, ln * 0.5)), add(b, mul(d, ln)), 2.1,
                 'dark', 'prim%d' % s, up=(0, 0, 1), flat=0.25)
        m.group('prim%d' % s, 'wing%d' % s)
    # body
    m.ell((0, 23, 0.5), (7.6, 10.4, 7.2), 'gold', 'body', rot=(0, -12, 0))
    m.paint((0, 22, 6), (5, 8.5, 3.8), 'white', ['body'])
    m.tube([(0, 31, 1.5), (0, 34, 2.5)], [5.6, 5.0], 'gold', 'body')
    head_c, head_r = (0, 39.0, 4.0), (6.4, 5.8, 6.4)
    m.ell(head_c, head_r, 'gold', 'head')
    # hooked raptor beak
    m.tube([(-1.4, 38.9, 8.8), (-2.8, 38.8, 11.8), (-3.8, 37.6, 14.0),
            (-3.9, 35.2, 14.2)], [2.3, 1.8, 1.1, 0.3], 'horn', 'beak')
    m.tube([(-1.4, 37.0, 9.0), (-2.4, 36.4, 11.2)], [1.4, 0.6], 'horn',
           'beak')
    # pale cheeks and a dark storm-stripe behind each eye
    m.paint((0, 35.4, 7.8), (4.4, 2.4, 3.2), 'white', ['head'])
    for s in (-1, 1):
        p, n = on(head_c, head_r, (s * 0.8, 0.12, 0.2))
        m.paint(p, (1.6, 1.2, 3.2), 'dark', ['head'], rot=(0, 0, s * 12))
    # lightning-bolt crest
    poly_local(m, (0, 42, 0), (0.87, 0, -0.5), norm((0.1, 0.85, -0.55)),
               BOLT, 'gold', 'crest', puff=0.25, su=12, sv=17)
    poly_local(m, (0.3, 42.4, 0.3), (0.87, 0, -0.5), norm((0.1, 0.85, -0.55)),
               [(u * 0.5, v * 0.5 + 0.45) for u, v in BOLT], 'dark', 'crest',
               puff=0.2, su=12, sv=17)
    eye_pair(m, head_c, head_r, 36, 14, 4.4, 3.8, style='sharp',
             iris=('gold', 1), slant=0.8, lid=1, center=(-3, 37, 14),
             turn=0)
    return m


# ---- 19 VOLTUX -----------------------------------------------------------
def zigzag(m, pts, widths, mat, part, flat=0.4, up=(0, 0.2, 1), mats=None):
    """Sharp-cornered flattened strip through pts (one straight tube per
    segment), e.g. lightning-bolt ears and antlers."""
    n = len(pts) - 1
    for i in range(n):
        seg_mats = None
        if mats:
            t0 = i / float(n)
            t1 = (i + 1) / float(n)
            seg_mats = [(max(0.0, (t - t0) / (t1 - t0)), mm) for t, mm in mats
                        if t < t1]
            if not seg_mats:
                seg_mats = None
        m.tube([pts[i], pts[i + 1]], [widths[i], widths[i + 1]], mat, part,
               flat=flat, up=up, mats=seg_mats)
        if i < n - 1:
            mm = mat
            if mats:
                for t, q in mats:
                    if (i + 1) / float(n) >= t:
                        mm = q
            m.ell(pts[i + 1], (widths[i + 1], widths[i + 1],
                               widths[i + 1] * flat), mm, part)


EAR_BOLT = [(-0.50, 0.00), (0.50, 0.00), (0.80, 0.54), (0.28, 0.54),
            (0.50, 1.00), (-0.62, 0.44), (-0.10, 0.44)]


def bolt_ear(m, base, s, w, h, part, mat='fur', tip_mat='spark',
             inner_mat=None, lean=0.15, back=0.15, tip_from=0.62):
    """Lightning-bolt shaped ear (flat, slightly domed) with a coloured tip."""
    uvec = (s * 1.0, 0.0, 0.0)
    vvec = norm((s * lean, 1.0, -back))
    poly_local(m, base, uvec, vvec, EAR_BOLT, mat, part, puff=0.45, su=w,
               sv=h)
    top = add(base, add(mul(uvec, 0.25 * w), mul(vvec, 0.9 * h)))
    m.paint(top, (w * 0.7, h * (1 - tip_from) * 0.7, 3.0), tip_mat, [part])
    if inner_mat:
        c = add(base, add(mul(uvec, 0.12 * w), mul(vvec, 0.3 * h)))
        m.paint(add(c, (0, 0, 0.3)), (w * 0.2, h * 0.22, 1.2), inner_mat,
                [part], rot=(0, 0, -s * 20))


def voltux():
    m = Model('VOLTUX')
    m.outline = (34, 30, 64)
    m.mat('fur', ['#4c4a8c', '#7a7cc4', '#a8acec', '#dadeff'])
    m.mat('cream', ['#c4c2e2', '#f6f4ff'])
    m.mat('spark', ['#e8a41c', '#ffd84a', '#fff8b8'], emissive=0.45)
    m.mat('pink', ['#d0708e', '#ffa8c0'])
    m.eye_dark = (28, 24, 52)
    m.height = 40
    m.front_yaw = -20
    # crackling puff tail
    tc = (4.8, 7.8, -6.8)
    seedball(m, tc, 3.8, 'cream', 'tail', n=28, fil=0.42, tip=0.62, seed=4)
    for d in ((0.5, 1, -0.2), (1, 0.2, -0.3), (0.2, -0.3, -1), (0.9, 0.8, 0.1)):
        d = norm(d)
        b = add(tc, mul(d, 3.0))
        zigzag(m, [b, add(b, add(mul(d, 1.8), (0.9, 0.3, 0))),
                   add(b, add(mul(d, 2.6), (-0.4, 0, 0))),
                   add(b, mul(d, 4.6))], [0.75, 0.6, 0.55, 0.15], 'spark',
               'tail', flat=0.6)
    # haunches and big hind feet
    for s in (-1, 1):
        m.ell((s * 4.4, 5.6, -2.5), (3.2, 4.4, 5.2), 'fur', 'hip%d' % s)
        m.ell((s * 4.8, 1.5, 1.2), (1.9, 1.5, 4.2), 'fur', 'hip%d' % s)
        m.paint((s * 4.8, 1.2, 4.8), (1.8, 1.2, 1.2), 'spark', ['hip%d' % s])
        m.tube([(s * 2.6, 11.0, 3.0), (s * 2.8, 6.0, 4.2), (s * 2.8, 2.0, 4.6)],
               [1.7, 1.4, 1.5], 'fur', 'legF%d' % s)
        m.paint((s * 2.8, 1.4, 5.4), (1.4, 1.0, 1.1), 'spark', ['legF%d' % s])
    m.ell((0, 9.5, -0.5), (5.4, 7.2, 5.2), 'fur', 'body', rot=(0, -16, 0))
    m.paint((0, 10.5, 4.5), (3.6, 5.0, 2.4), 'cream', ['body'])
    # head
    head_c, head_r = (0, 19.5, 2.2), (6.2, 5.6, 5.6)
    m.ell(head_c, head_r, 'fur', 'head')
    mz_c, mz_r = (0, 17.6, 6.4), (3.0, 2.4, 2.2)
    m.ell(mz_c, mz_r, 'cream', 'head')
    for s in (-1, 1):
        # cheek fluff
        m.tube([(s * 5.0, 18.0, 3.2), (s * 7.6, 16.8, 2.2),
                (s * 8.8, 15.8, 1.2)], [2.0, 1.2, 0.2], 'fur', 'head',
               flat=0.5, up=(0, 0, 1))
        # long zigzag ears with yellow tips
        bolt_ear(m, (s * 2.8, 21.0, 1.2), s, 6.2, 22.0, 'ear%d' % s,
                 inner_mat='pink')
    eye_pair(m, head_c, head_r, 28, 10, 3.4, 4.4, iris=('fur', 0),
             center=(0, 18, 10))
    m.dot(on(mz_c, mz_r, (0, 0.55, 1))[0], (0, 0.2, 1), w=1.8, h=1.1, minw=2,
          color=('pink', 0))
    p, n = on(mz_c, mz_r, (0, -0.3, 1))
    m.mouth(p, n, 'w', w=3.0)
    return m


# ---- 20 VOLTLOPE --------------------------------------------------------
def voltlope():
    m = Model('VOLTLOPE')
    m.outline = (30, 26, 60)
    m.mat('fur', ['#46448a', '#7274c0', '#a2a6ea', '#d6daff'])
    m.mat('cream', ['#c4c2e2', '#f6f4ff'])
    m.mat('spark', ['#e8a41c', '#ffd84a', '#fff8b8'], emissive=0.45)
    m.mat('pink', ['#d0708e', '#ffa8c0'])
    m.eye_dark = (26, 22, 50)
    m.height = 56
    m.max_w = 60
    m.front_yaw = -18
    # crackling puff tail
    tc = (3.5, 14.5, -6.0)
    seedball(m, tc, 3.2, 'cream', 'tail', n=26, fil=0.42, tip=0.6, seed=8)
    # powerful hind legs: big thighs, long feet
    for s in (-1, 1):
        m.ell((s * 4.4, 14.0, -0.5), (3.6, 5.6, 5.0), 'fur', 'leg%d' % s,
              rot=(0, -12, s * 6))
        m.tube([(s * 4.8, 11.0, -3.0), (s * 5.2, 6.0, -5.2),
                (s * 5.3, 2.4, -3.4)], [2.8, 1.9, 1.7], 'fur', 'leg%d' % s)
        m.ell((s * 5.4, 1.5, 0.8), (2.1, 1.5, 5.6), 'fur', 'leg%d' % s)
        m.paint((s * 5.4, 1.3, 5.6), (2.2, 1.6, 1.6), 'spark', ['leg%d' % s])
    # lean upright torso
    m.ell((0, 20.5, -0.6), (5.0, 6.4, 4.2), 'fur', 'body')
    m.ell((0, 27.0, 0.2), (6.0, 5.2, 4.4), 'fur', 'body')
    m.paint((0, 22.5, 3.6), (3.4, 7.0, 2.2), 'cream', ['body'])
    # fighting guard: forearms raised, paws at chin height
    for s in (-1, 1):
        sh_ = (s * 5.8, 29.0, 0.0)
        el = (s * 8.4, 23.8, 3.2)
        pw = (s * 5.6, 30.6, 7.0)
        m.sph(sh_, 2.6, 'fur', 'arm%d' % s)
        m.tube([sh_, el], [2.3, 1.8], 'fur', 'arm%d' % s)
        m.tube([el, pw], [1.8, 1.7], 'fur', 'arm%d' % s,
               mats=[(0, 'fur'), (0.6, 'spark')])
        m.sph(add(pw, (0, 0.8, 0.4)), 2.2, 'fur', 'arm%d' % s)
    # head
    m.tube([(0, 30.5, 0.4), (0, 33.5, 1.2)], [3.0, 2.8], 'fur', 'body')
    head_c, head_r = (0, 37.0, 2.2), (5.8, 5.3, 5.2)
    m.ell(head_c, head_r, 'fur', 'head')
    mz_c, mz_r = (0, 35.2, 6.1), (2.7, 2.2, 2.1)
    m.ell(mz_c, mz_r, 'cream', 'head')
    for s in (-1, 1):
        m.tube([(s * 4.4, 35.8, 2.8), (s * 6.8, 34.8, 1.8),
                (s * 7.9, 33.8, 0.8)], [1.7, 1.0, 0.2], 'fur', 'head',
               flat=0.5, up=(0, 0, 1))
        # ears laid back
        bolt_ear(m, (s * 2.8, 39.0, -0.4), s, 4.8, 15.0, 'ear%d' % s,
                 inner_mat='pink', lean=1.0, back=1.2)
        # forked lightning antlers
        b = (s * 1.8, 40.6, 3.0)
        p1 = (s * 4.0, 46.0, 3.3)
        p2 = (s * 2.6, 47.8, 3.3)
        p3 = (s * 5.2, 55.0, 2.9)
        zigzag(m, [b, p1, p2, p3], [1.2, 1.0, 0.95, 0.55], 'spark',
               'antler%d' % s, flat=1.0)
        q1 = (s * 8.0, 47.2, 3.1)
        q2 = (s * 7.0, 49.0, 3.0)
        q3 = (s * 10.6, 52.6, 2.7)
        zigzag(m, [p1, q1, q2, q3], [1.0, 0.9, 0.85, 0.5], 'spark',
               'antler%d' % s, flat=1.0)
    eye_pair(m, head_c, head_r, 30, 14, 4.2, 4.2, style='sharp',
             iris=('spark', 1), slant=0.6, center=(0, 36, 10))
    m.dot(on(mz_c, mz_r, (0, 0.55, 1))[0], (0, 0.2, 1), w=1.8, h=1.1, minw=2,
          color=('pink', 0))
    p, n = on(mz_c, mz_r, (0, -0.35, 1))
    m.mouth(p, n, 'smile', w=2.6, fang=1)
    return m


# ---- 21 GOLEMIT ----------------------------------------------------------
def golemit():
    m = Model('GOLEMIT')
    m.outline = (34, 28, 26)
    m.mat('stone', ['#4a4038', '#72665a', '#9e907c', '#cabca4'])
    m.mat('moss', ['#468a34', '#8ac454'])
    m.mat('glow', ['#ffb82a', '#fff4a8'], emissive=0.9)
    m.mat('crack', ['#221a1c'])
    m.eye_dark = (28, 20, 22)
    m.height = 32
    for s in (-1, 1):
        m.box((s * 3.8, 2.4, 0.5), (2.5, 2.4, 2.8), 'stone', 'leg%d' % s,
              bevel=1.0, rot=(s * 6, 0, 0))
        m.box((s * 9.8, 10, 1), (2.4, 3.4, 2.6), 'stone', 'arm%d' % s,
              bevel=1.0, rot=(0, -10, s * 12))
    m.box((0, 10, 0), (7.4, 6.4, 5.8), 'stone', 'body', bevel=2.2,
          rot=(4, 0, 2))
    head_c = (0, 21.2, 0.8)
    m.box(head_c, (6.4, 5.2, 5.4), 'stone', 'head', bevel=2.0,
          rot=(0, 0, -3))
    m.paint((0, 26.4, 0), (5.6, 1.8, 5), 'moss', ['head'])
    m.paint((-5, 16.5, -1), (3, 1.6, 4), 'moss', ['body'])
    m.paint((4, 16.5, -3), (3.6, 1.4, 3), 'moss', ['body'])
    for (a, b) in (((-2.5, 12.5, 5.9), (-1.2, 9, 6.1)),
                   ((-1.2, 9, 6.1), (-2.8, 6, 5.9))):
        for k in range(5):
            m.paint(lerp(a, b, k / 4.0), (0.5, 0.5, 1.2), 'crack', ['body'])
    # jagged crack across the face with bright eyes inside it
    for (x, y) in ((-5.5, 21.6), (-3.8, 21.0), (-1.8, 21.4), (0, 20.8),
                   (1.8, 21.4), (3.8, 21.0), (5.5, 21.6)):
        m.paint((x, y, 6.2), (1.2, 1.25, 1.8), 'crack', ['head'])
    m.paint((0.8, 23.2, 6.2), (0.6, 1.4, 1.8), 'crack', ['head'])
    for s in (-1, 1):
        m.eye((s * 2.8, 21.2, 6.3), (0, 0, 1), 3.4, 2.4, style='glow',
              iris=('glow', 1), glint=False, minh=2, minw=3)
    m.mouth((0.3, 17.9, 6.3), (0, -0.1, 1), 'line', w=2.4)
    return m


# ---- 22 BOULDRON ---------------------------------------------------------
def bouldron():
    m = Model('BOULDRON')
    m.outline = (28, 24, 26)
    m.mat('stone', ['#40382f', '#6c604f', '#9a8b74', '#cabca0'])
    m.mat('moss', ['#407e30', '#82be4c'])
    m.mat('crys', ['#4c3290', '#8a5ed0', '#dcc6ff'], emissive=0.35)
    m.mat('socket', ['#221c20'])
    m.eye_dark = (26, 18, 20)
    m.height = 58
    m.max_w = 62
    for s in (-1, 1):
        m.rock((s * 6, 5.5, 0.5), (4.6, 5.6, 4.8), 'stone', 'leg%d' % s,
               seed=40 + s, n=14)
    m.rock((0, 24, -1), (12.5, 13, 9.4), 'stone', 'body', seed=44, n=22,
           jitter=0.06)
    for s in (-1, 1):
        m.rock((s * 12.8, 33, -0.5), (6.4, 6.0, 6.4), 'stone', 'body',
               seed=50 + s, n=16, jitter=0.06)
        m.rock((s * 18.0, 23, 1.5), (4.4, 7.0, 4.6), 'stone', 'arm%d' % s,
               seed=52 + s, n=14)
        m.rock((s * 18.6, 10, 4), (7.6, 7.4, 7.6), 'stone', 'arm%d' % s,
               seed=54 + s, n=20, jitter=0.06)
        m.paint((s * 12.8, 38.5, -0.5), (6, 2.6, 6), 'moss', ['body'])
        m.paint((s * 18.6, 16.8, 4), (5.6, 1.8, 5.6), 'moss', ['arm%d' % s])
    head_c = (0, 40, 4)
    m.rock(head_c, (6.8, 5.8, 6.4), 'stone', 'head', seed=61, n=18,
           jitter=0.06)
    m.paint((0, 45.5, 3), (5.6, 2.0, 5.2), 'moss', ['head'])
    for k, (b, d, ln, r) in enumerate((((4, 33, -6), (0.5, 0.8, -0.4), 11,
                                        2.6),
                                       ((-3.5, 34, -6.5), (-0.3, 0.9, -0.4),
                                        13, 3.0),
                                       ((0.5, 30, -8), (0.1, 0.6, -0.8), 9,
                                        2.2),
                                       ((15.5, 37.5, -2), (0.6, 0.8, -0.3), 7,
                                        2.0),
                                       ((-20, 15, 0.5), (-0.7, 0.6, -0.2), 6,
                                        1.8))):
        m.crystal(b, add(b, mul(norm(d), ln)), r, 'crys', 'crys%d' % k,
                  sides=5, tip_frac=0.4, twist=k * 30)
    for s in (-1, 1):
        m.paint((s * 2.7, 40.6, 10.2), (2.4, 1.8, 2.0), 'socket', ['head'])
        m.eye((s * 2.7, 40.7, 10.5), (s * 0.2, 0, 1), 3.4, 2.8,
              style='glow', iris=('crys', 2), glint=False, minh=2, minw=3,
              slant=0.7, center=(0, 40, 12))
    m.mouth((0, 36.4, 10.2), (0, 0, 1), 'line', w=4.0)
    return m


# ---- 23 PUFFOWL ----------------------------------------------------------
def puffowl():
    m = Model('PUFFOWL')
    m.outline = (44, 26, 22)
    m.mat('fur', ['#4c2c22', '#7c4a30', '#aa703e', '#d49e64'])
    m.mat('cream', ['#c6a476', '#ecd6aa', '#fff6e0'])
    m.mat('beak', ['#d0801e', '#ffc442'])
    m.eye_dark = (32, 20, 18)
    m.height = 32
    body_c, body_r = (0, 12, 0), (9, 11, 8.6)
    for s in (-1, 1):
        for t in (-1, 0, 1):
            m.tube([(s * 3, 1.8, 2.5), (s * 3 + t * 1.2, 0.8, 4.6)],
                   [0.9, 0.7], 'beak', 'foot%d' % s)
    m.ell(body_c, body_r, 'fur', 'body')
    leaf(m, (0, 6, -7), (0, 3.5, -9.5), (0, 2.0, -11.5), 2.6, 'fur', 'tail',
         up=(0, 0.5, -1), flat=0.3)
    for (x, y, z) in ((-3, 15, -7.6), (2, 13, -8.2), (-1, 9, -8.4),
                      (4, 9, -7.6), (0, 18, -6.6), (5, 16, -6.4)):
        m.paint((x, y, z), (1.0, 0.7, 1.4), 'cream', ['body'])
    m.paint((0, 8, 6), (6.5, 7, 4), 'cream', ['body'])
    for (x, y) in ((-2.5, 9.5), (1.5, 10.5), (-0.5, 6.5), (3.2, 7.2),
                   (-3.6, 5.6), (1.0, 3.8)):
        m.paint((x, y, 8.6), (0.9, 0.7, 1.4), 'fur', ['body'])
    for s in (-1, 1):
        p, n = on(body_c, body_r, (s * 0.38, 0.42, 0.82))
        m.paint(p, (3.6, 3.6, 2.6), 'cream', ['body'])
        m.ell((s * 8.0, 10.5, -2.4), (2.0, 5.8, 4.8), 'fur', 'wing%d' % s,
              rot=(s * 18, 0, s * 14))
        for k in range(3):
            m.paint((s * 9.6, 8.2 + k * 2.4, -3.5 + k * 0.4), (1.2, 0.6, 1.6),
                    'cream', ['wing%d' % s])
        m.tube([(s * 4.2, 20.6, -0.5), (s * 6.0, 23.6, -1.0),
                (s * 7.2, 26.2, -1.4)], [2.6, 1.6, 0.2], 'fur', 'tuft%d' % s,
               flat=0.45, up=(0, 0.2, 1))
    m.tube([(0, 14.5, 8.2), (0, 13.2, 9.8)], [1.5, 0.3], 'beak', 'beak')
    eye_pair(m, body_c, body_r, 21, 26, 4.4, 5.0, style='iris',
             iris=('beak', 1), center=(0, 14, 10))
    return m


# ---- 24 HOOTLORD ---------------------------------------------------------
def hootlord():
    m = Model('HOOTLORD')
    m.outline = (40, 24, 22)
    m.mat('fur', ['#44261e', '#74442c', '#a2683a', '#cc965e'])
    m.mat('cream', ['#c2a074', '#ead2a4', '#fff4dc'])
    m.mat('gold', ['#c07a18', '#ffcc40'])
    m.mat('dark', ['#2a1a1a', '#4c3024'])
    m.eye_dark = (30, 18, 16)
    m.height = 58
    m.max_w = 62
    for s in (-1, 1):
        m.tube([(s * 4, 8, 1), (s * 4.4, 2.2, 2.5)], [2.4, 1.6], 'fur',
               'leg%d' % s)
        for t in (-1, 0, 1):
            m.crystal((s * 4.4 + t * 1.4, 1.5, 3.2),
                      (s * 4.4 + t * 2.2, 0.4, 6.4), 0.8, 'dark', 'leg%d' % s,
                      sides=4, tip_frac=0.8)
    # tail
    leaf(m, (0, 10, -6), (0, 6, -9), (0, 2.5, -11), 4.0, 'dark', 'tail',
         up=(0, 0.4, -1))
    # wings partly spread
    for s in (-1, 1):
        sh_ = (s * 9, 31, -1.5)
        pts = [sh_, (s * 16, 30, -3), (s * 21, 24, -4.5), (s * 23, 15, -5),
               (s * 20, 11, -4.5), (s * 17, 12, -4), (s * 14, 9, -3.4),
               (s * 11, 11, -2.5), (s * 8, 16, -1.5)]
        m.poly(pts, 'fur', 'wing%d' % s, puff=0.3)
        for k in range(5):
            t = k / 4.0
            b = (s * (13 + 7 * t), 22 - 6 * t, -3.5 - t)
            d = norm((s * (0.2 + 0.5 * t), -1, -0.1))
            leaf(m, b, add(b, mul(d, 4.5)), add(b, mul(d, 9 - 2 * t)), 1.8,
                 'dark', 'prim%d' % s, up=(0, 0, 1), flat=0.25)
        m.group('prim%d' % s, 'wing%d' % s)
        # star speckles over the night-dark wing
        m.paint((s * 16.5, 20.0, -3.8), (6.5, 8.0, 3.0), 'dark',
                ['wing%d' % s])
        for (x, y) in ((13.0, 26.5), (17.5, 24.0), (20.0, 18.5),
                       (15.5, 17.0), (18.5, 13.5)):
            m.sparkle((s * x, y, -3.0 - (x - 12) * 0.25), (s * 0.2, 0, 1),
                      size=1, color=('cream', 2))
    body_c, body_r = (0, 23, 0), (10, 14.5, 8.8)
    m.ell(body_c, body_r, 'fur', 'body')
    m.paint((0, 20, 6), (7, 11, 4), 'cream', ['body'])
    for (x, y) in ((-3, 24), (2, 25.5), (-0.5, 20), (3.5, 19.5), (-4, 15.5),
                   (1, 14.5), (4, 12)):
        m.paint((x, y, 8.8), (1.1, 0.6, 1.6), 'fur', ['body'])
    head_c, head_r = (0, 40.0, 1.8), (9.6, 8.0, 8.2)
    m.ell(head_c, head_r, 'fur', 'head')
    # scholar's face disc: dark rim, pale disc, a spectacle ring per eye
    p, n = on(head_c, head_r, (0.08, -0.02, 1))
    m.paint(add(p, (0, 0, -0.4)), (8.2, 6.6, 3.2), 'dark', ['head'])
    m.paint(add(p, (0, 0, -0.2)), (7.2, 5.8, 3.2), 'cream', ['head'])
    for s in (-1, 1):
        m.tube([(s * 5, 45, 0), (s * 7.5, 49, -0.5), (s * 9.5, 53, -1.2)],
               [3.0, 1.8, 0.2], 'fur', 'tuft%d' % s, flat=0.4,
               up=(0, 0.2, 1), mats=[(0, 'fur'), (0.7, 'gold')])
    for k in range(5):
        a = (k - 2) * 22 * DEG
        d = norm((math.sin(a) * 0.8, 1, -0.5))
        b = (0, 45.5, -1)
        m.tube([b, add(b, mul(d, 5)), add(b, mul(d, 10 - abs(k - 2)))],
               [1.8, 1.6, 0.2], 'fur', 'crest', flat=0.4, up=(0, 0.3, 1),
               mats=[(0, 'fur'), (0.6, 'gold')])
    m.tube([(0.4, 38.8, 9.6), (0.4, 37.0, 10.8), (0.4, 35.4, 10.4)],
           [1.7, 1.1, 0.2], 'gold', 'beak')
    eye_pair(m, head_c, head_r, 26, 8, 5.0, 4.8, style='sharp',
             iris=('gold', 1), slant=0.3, lid=0, center=(0, 38, 11), turn=5)
    return m


# ---- 25 SKYWISP ----------------------------------------------------------
def wing_shape(cx, cy, rx, ry, n=14, tip=0.0, rot=0.0):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1.0 + tip * max(0, math.cos(a)) ** 3
        x, y = math.cos(a) * rx * r, math.sin(a) * ry * r
        ca, sa = math.cos(rot * DEG), math.sin(rot * DEG)
        pts.append((cx + x * ca - y * sa, cy + x * sa + y * ca))
    return pts


def moth_wings(m, root, s, fore, hind, mat, part, tilt=0.35):
    """fore/hind: (len, width, angle_deg) wings in a plane tilted back."""
    uvec = norm((s * 1, 0, -tilt))
    vvec = (0, 1, 0)
    for (ln, wd, ang, dy), nm in ((fore, 'F'), (hind, 'H')):
        pts = wing_shape(ln * 0.55, dy, ln * 0.55, wd, 16, tip=0.25,
                         rot=ang)
        P = [add(root, add(mul(uvec, x), mul(vvec, y))) for x, y in pts]
        m.poly(P, mat, part + nm + str(s), puff=0.35)


def skywisp():
    m = Model('SKYWISP')
    m.outline = (30, 44, 74)
    m.mat('wing', ['#4a8cc0', '#7ec2e6', '#b6e8f6', '#ecfcff'])
    m.mat('fuzz', ['#aeb0c8', '#dcdcec', '#ffffff'])
    m.mat('body', ['#5c5c90', '#8e8ec4'])
    m.eye_dark = (22, 22, 46)
    m.height = 34
    m.max_w = 56
    m.float_lift = 3
    for s in (-1, 1):
        moth_wings(m, (s * 1.5, 13, -4.0), s, (15, 7.5, 28, 3),
                   (10, 5.5, -30, -3), 'wing', 'wing')
        m.paint((s * 12, 21, -7.5), (4.5, 3.5, 3), 'fuzz', ['wingF%d' % s])
    m.ell((0, 9.5, -3.5), (2.6, 3.6, 2.6), 'fuzz', 'abdomen',
          rot=(0, -45, 0))
    for k in range(3):
        m.paint((0, 10.5 - k * 2.2, -1.6 - k * 1.4), (3.0, 0.5, 3.0), 'body',
                ['abdomen'])
    m.ell((0, 13, -0.5), (4, 4.4, 3.8), 'fuzz', 'thorax')
    for k in range(9):
        a = (k * 40) * DEG
        m.sph((math.sin(a) * 3.8, 16 + math.cos(a * 2) * 0.4,
               1 + math.cos(a) * 3.0), 1.7, 'fuzz', 'thorax')
    head_c, head_r = (0, 20.0, 3.4), (5.2, 4.6, 4.6)
    m.ell(head_c, head_r, 'fuzz', 'head')
    for s in (-1, 1):
        pts = [(s * 1.6, 23.2, 3), (s * 2.6, 27.5, 3), (s * 4.4, 31, 2.5),
               (s * 7.0, 32.4, 2), (s * 8.8, 31.2, 2), (s * 8.4, 29.4, 2),
               (s * 7.0, 29.6, 2)]
        m.tube(pts, 0.62, 'body', 'ant%d' % s)
        m.tube([(s * 2.2, 11, 1.8), (s * 3.0, 8.6, 3.2), (s * 2.6, 7.4, 4.4)],
               [0.8, 0.7, 0.6], 'body', 'leg%d' % s)
    eye_pair(m, head_c, head_r, 34, 8, 3.8, 4.6, iris=('body', 1),
             center=(0, 19, 9), turn=12)
    p, n = on(head_c, head_r, (0.1, -0.42, 1))
    m.mouth(p, n, 'smile', w=2.4)
    return m


# ---- 26 LUMOTH -----------------------------------------------------------
def lumoth():
    m = Model('LUMOTH')
    m.outline = (26, 16, 50)
    m.mat('wing', ['#362268', '#6038a4', '#9468d6', '#c8a4f4'])
    m.mat('glow', ['#26a0cc', '#6ae4f4', '#dafeff'], emissive=0.6)
    m.mat('body', ['#20224a', '#3c3e78'])
    m.mat('fuzz', ['#c4c2e0', '#ffffff'])
    m.eye_dark = (18, 14, 40)
    m.height = 56
    m.max_w = 62
    m.float_lift = 2
    for s in (-1, 1):
        moth_wings(m, (s * 2, 26, -3), s, (27, 12, 30, 5),
                   (18, 9.5, -32, -6), 'wing', 'wing')
        uv = norm((s, 0, -0.35))
        root = (s * 2, 26, -3)

        def W(u, v, root=root, uv=uv):
            return add(root, add(mul(uv, u), (0, v, 0)))
        for (u, v, r1, nm) in ((17, 9, 5.4, 'wingF'), (11.5, -7.5, 4.0,
                                                        'wingH')):
            part = nm + str(s)
            c = W(u, v)
            m.paint(c, r1, 'body', [part])
            m.paint(c, r1 * 0.68, 'glow', [part])
            m.paint(add(c, (0, 0.4, 0)), r1 * 0.28, 'fuzz', [part])
        for (u, v, nm) in ((25.5, 15, 'wingF'), (28.5, 8, 'wingF'),
                           (21.5, 18.5, 'wingF'), (17, -13.5, 'wingH'),
                           (20, -10, 'wingH')):
            m.paint(W(u, v), 1.9, 'glow', [nm + str(s)])
    m.ell((0, 19, -4), (3.6, 6.5, 3.6), 'body', 'abdomen', rot=(0, -30, 0))
    for k in range(3):
        m.paint((0, 21 - k * 3.2, -2.8 - k * 1.8), (3.8, 0.6, 3.8), 'glow',
                ['abdomen'])
    m.ell((0, 26, -0.5), (5.2, 5.6, 5), 'fuzz', 'thorax')
    for k in range(10):
        a = (k * 36) * DEG
        m.sph((math.sin(a) * 5, 30 + math.cos(a * 2) * 0.4,
               1 + math.cos(a) * 3.8), 2.1, 'fuzz', 'thorax')
    head_c, head_r = (0, 34, 3.4), (5.6, 5.0, 5.0)
    m.ell(head_c, head_r, 'fuzz', 'head')
    for s in (-1, 1):
        pts = [(s * 2, 37.5, 3.5), (s * 5, 43, 3), (s * 9, 48.5, 2),
               (s * 13, 51.5, 1), (s * 16, 51, 0.5)]
        m.tube(pts, [1.0, 0.9, 0.8, 0.7, 0.5], 'glow', 'ant%d' % s)
        for k in range(1, 4):
            q = pts[k]
            m.tube([q, add(q, (s * 1.2, 2.2, 0))], [0.6, 0.3], 'glow',
                   'ant%d' % s)
        m.tube([(s * 2.6, 23, 2), (s * 4.2, 18, 3.5), (s * 4.6, 15, 4)],
               [0.9, 0.8, 0.6], 'body', 'leg%d' % s)
    eye_pair(m, head_c, head_r, 34, 8, 4.4, 5.4, iris=('body', 1),
             center=(0, 33, 9), turn=12)
    p, n = on(head_c, head_r, (0.1, -0.45, 1))
    m.mouth(p, n, 'smile', w=2.6)
    return m


# ---- 27 NIBBIT -----------------------------------------------------------
def nibbit():
    m = Model('NIBBIT')
    m.outline = (34, 34, 48)
    m.mat('fur', ['#3e4a62', '#62718c', '#8e9cb4', '#c2cedc'])
    m.mat('cream', ['#d8d2c0', '#fbf6e8'])
    m.mat('pink', ['#c0687c', '#f4a0b0'])
    m.mat('cloth', ['#a83a2c', '#e0664a'])
    m.mat('gold', ['#c88a18', '#ffe070'], spec=0.5)
    m.eye_dark = (26, 26, 40)
    m.white = (255, 255, 255)
    m.height = 31
    m.front_yaw = -24
    # long pink tail curling behind
    m.tube([(0.5, 4.0, -4.5), (3.0, 1.8, -9.0), (7.5, 1.5, -10.5),
            (11.0, 3.0, -8.5), (12.0, 5.5, -5.5)], [1.4, 1.2, 1.0, 0.8, 0.4],
           'pink', 'tail')
    # feet + haunches
    for s in (-1, 1):
        m.ell((s * 3.4, 1.3, 2.4), (1.8, 1.3, 3.2), 'pink', 'leg%d' % s)
        m.ell((s * 3.8, 5.6, -0.8), (3.0, 3.8, 4.0), 'fur', 'leg%d' % s)
    # body
    m.ell((0, 10.0, -0.2), (5.6, 6.8, 5.0), 'fur', 'body')
    m.paint((0, 9.5, 3.8), (3.8, 5.2, 2.2), 'cream', ['body'])
    # the bundle of trinkets hanging from a stick over its shoulder
    bc, br = (9.6, 19.0, -8.0), (5.0, 4.4, 4.8)
    st0 = (4.2, 14.6, 5.0)
    st1 = (9.0, 25.6, -6.6)
    m.tube([st0, st1], [0.7, 0.7], 'gold', 'stick')
    m.ell(bc, br, 'cloth', 'bundle')
    for d in ((0.5, 0.3, 0.8), (-0.3, -0.25, 0.9), (0.9, -0.4, 0.2),
              (0.2, 0.6, 0.7), (0.8, 0.3, -0.4)):
        p, n = surf(bc, br, d)
        m.paint(p, 0.8, 'cream', ['bundle'])
    m.ell(add(bc, (-0.6, 4.2, 1.2)), (1.8, 1.4, 1.8), 'cloth', 'bundle')
    # trinkets poking out of the knot: a coin, a key, a bead
    m.ell(add(bc, (-2.2, 5.0, 2.6)), (2.0, 2.0, 0.6), 'gold', 'trinket',
          rot=(-35, 0, 12))
    m.tube([add(bc, (1.2, 4.4, 2.0)), add(bc, (2.2, 7.4, 2.2))], [0.5, 0.5],
           'gold', 'trinket')
    m.ell(add(bc, (2.4, 7.9, 2.2)), (1.1, 1.1, 0.6), 'gold', 'trinket')
    m.sph(add(bc, (0.4, 5.6, -1.4)), 1.1, 'pink', 'trinket')
    # arms: one grips the stick at the shoulder, one rests on the belly
    m.tube([(4.6, 14.0, 0.8), (6.2, 12.4, 3.0), (4.8, 14.8, 5.0)],
           [1.6, 1.3, 1.2], 'fur', 'armR')
    m.sph((4.6, 15.0, 5.4), 1.5, 'pink', 'armR')
    m.tube([(-4.6, 14.0, 1.2), (-5.2, 10.6, 3.2), (-2.4, 9.2, 5.4)],
           [1.6, 1.3, 1.2], 'fur', 'armL')
    m.sph((-2.0, 9.2, 5.6), 1.4, 'pink', 'armL')
    # head with big round ears
    head_c, head_r = (0, 19.2, 1.6), (6.0, 5.3, 5.4)
    m.ell(head_c, head_r, 'fur', 'head')
    sn_c, sn_r = (0, 17.6, 6.2), (2.8, 2.3, 2.6)
    m.ell(sn_c, sn_r, 'cream', 'head')
    for s in (-1, 1):
        m.ell((s * 5.6, 24.6, -0.6), (4.2, 4.3, 1.3), 'fur', 'ear%d' % s,
              rot=(s * 20, -8, s * 12))
        m.paint((s * 5.7, 24.7, 0.6), (2.8, 2.9, 1.2), 'pink', ['ear%d' % s])
    eye_pair(m, head_c, head_r, 32, 14, 3.4, 4.2, iris=('fur', 0),
             center=(0, 17, 9))
    m.dot(on(sn_c, sn_r, (0, 0.2, 1))[0], (0, 0.2, 1), w=2.0, h=1.4, minw=2,
          color=('pink', 0))
    p, n = on(sn_c, sn_r, (0, -0.45, 1))
    m.mouth(p, n, 'smile', w=2.4)
    m.dot(add(p, (0, -0.9, 0.2)), n, w=1.0, h=1.0, color='white')
    m.sparkle(add(bc, (-2.2, 5.4, 3.3)), (0, 0, 1), size=1)
    return m


# ---- 28 GNAWLORD ---------------------------------------------------------
def gnawlord():
    m = Model('GNAWLORD')
    m.outline = (30, 28, 44)
    m.mat('fur', ['#353f56', '#56647e', '#8390aa', '#b8c4d6'])
    m.mat('cream', ['#cfc8b4', '#f6f0e0'])
    m.mat('red', ['#8e2a2a', '#d0503c'])
    m.mat('teal', ['#2a6a70', '#4aa0a0'])
    m.mat('gold', ['#c08a1c', '#ffe070'], spec=0.4)
    m.mat('pink', ['#e890a4'])
    m.eye_dark = (30, 28, 44)
    m.white = (255, 255, 255)
    m.height = 54
    m.max_w = 60
    m.front_yaw = -22
    # long tail sweeping out behind
    m.tube([(1.0, 8.0, -5.0), (6.0, 3.0, -10.0), (13.0, 2.0, -11.0),
            (18.0, 4.5, -8.0), (20.0, 8.5, -5.0)], [1.9, 1.6, 1.3, 1.0, 0.4],
           'pink', 'tail')
    # patchwork cape falling from the shoulders: a draped half-cylinder
    # built from quads, each patch its own fabric
    NU, NV = 5, 4
    pattern = ['red', 'red', 'teal', 'red', 'red',
               'red', 'gold', 'red', 'red', 'teal',
               'teal', 'red', 'red', 'gold', 'red',
               'red', 'red', 'teal', 'red', 'red']

    def cape_pt(u, v):
        th = u * 96 * DEG
        R = 6.2 + 6.2 * v
        y = 31.0 - 28.5 * v
        zc = -1.0 - 2.5 * v
        wob = 0.6 * math.sin(u * 9.0 + v * 3.0) * v
        return (math.sin(th) * R * 1.05, y + (0.8 * abs(u) if v > 0.95 else 0),
                zc - math.cos(th) * R * 0.62 + wob)
    for j in range(NV):
        for i in range(NU):
            u0 = -1 + 2.0 * i / NU
            u1 = -1 + 2.0 * (i + 1) / NU
            v0 = j / float(NV)
            v1 = (j + 1) / float(NV)
            q = [cape_pt(u0, v0), cape_pt(u1, v0), cape_pt(u1, v1),
                 cape_pt(u0, v1)]
            m.poly(q, pattern[j * NU + i], 'cape', puff=0.25)
    # legs + big feet
    for s in (-1, 1):
        m.ell((s * 4.2, 11.5, 0.0), (3.4, 5.0, 4.2), 'fur', 'leg%d' % s,
              rot=(0, -8, s * 6))
        m.tube([(s * 4.6, 8.0, -1.4), (s * 5.0, 4.0, -1.8),
                (s * 5.2, 2.2, -0.4)], [2.4, 1.8, 1.6], 'fur', 'leg%d' % s)
        m.ell((s * 5.4, 1.4, 2.4), (2.0, 1.4, 3.6), 'pink', 'leg%d' % s)
    # chest-out torso with cream belly
    m.ell((0, 19.0, 0.0), (6.4, 7.2, 5.0), 'fur', 'body')
    m.ell((0, 26.5, 0.6), (6.8, 5.2, 4.8), 'fur', 'body')
    m.paint((0, 20.0, 4.0), (4.2, 7.0, 2.4), 'cream', ['body'])
    # ruffled cream collar where the cape is fastened
    for k in range(7):
        a = (k - 3) * 32 * DEG
        b = (math.sin(a) * 4.6, 30.4, 1.2 + math.cos(a) * 2.6)
        m.sph(b, 1.9, 'cream', 'collar')
    m.sph((0, 29.6, 4.4), 1.3, 'gold', 'collar')
    # arms: one fist on the hip, one holding a fork sceptre
    m.sph((-6.4, 27.5, 0.2), 2.6, 'fur', 'armL')
    m.tube([(-6.4, 27.5, 0.2), (-9.6, 22.5, 1.2), (-6.6, 18.6, 2.6)],
           [2.3, 1.9, 1.7], 'fur', 'armL')
    m.sph((-6.2, 18.4, 2.8), 1.9, 'fur', 'armL')
    m.sph((6.4, 27.5, 0.2), 2.6, 'fur', 'armR')
    m.tube([(6.4, 27.5, 0.2), (10.4, 23.0, 1.6), (11.6, 20.4, 5.0)],
           [2.3, 1.9, 1.7], 'fur', 'armR')
    m.sph((11.6, 20.6, 5.4), 1.9, 'fur', 'armR')
    # sceptre: a bent old fork
    f0, f1 = (12.2, 1.6, 6.4), (11.6, 31.0, 5.0)
    m.tube([f0, f1], [0.7, 0.7], 'gold', 'fork')
    for t in (-1, 0, 1):
        m.tube([add(f1, (t * 1.0, -0.4, 0)), add(f1, (t * 1.2, 4.0, -0.2))],
               [0.5, 0.4], 'gold', 'fork')
    m.ell(add(f1, (0, -0.6, 0)), (1.9, 0.9, 0.8), 'gold', 'fork')
    # head, big round ears, bottle-cap crown
    head_c, head_r = (0, 36.5, 2.0), (6.0, 5.4, 5.4)
    m.ell(head_c, head_r, 'fur', 'head')
    sn_c, sn_r = (0, 34.6, 6.8), (3.0, 2.5, 3.0)
    m.ell(sn_c, sn_r, 'cream', 'head')
    for s in (-1, 1):
        m.ell((s * 5.8, 42.0, -0.6), (4.2, 4.4, 1.3), 'fur', 'ear%d' % s,
              rot=(s * 20, -8, s * 14))
        m.paint((s * 5.9, 42.1, 0.6), (2.8, 3.0, 1.2), 'pink', ['ear%d' % s])
    cc = (0.8, 44.2, 1.4)
    crot = (0, -10, -14)
    m.ell(cc, (4.2, 2.3, 4.2), 'gold', 'crown', rot=crot)
    for k in range(18):
        a = k / 18.0 * 2 * math.pi
        p, n = surf(cc, (4.5, 2.0, 4.5), (math.cos(a), -0.5, math.sin(a)),
                    crot)
        m.sph(p, 0.95, 'gold', 'crown')
    top, tn = surf(cc, (4.2, 2.3, 4.2), (0, 1, 0), crot)
    m.paint(top, (3.3, 1.2, 3.3), 'red', ['crown'], rot=crot)
    eye_pair(m, head_c, head_r, 30, 16, 3.8, 3.4, style='sharp',
             iris=('red', 1), slant=0.8, lid=1, center=(0, 34, 10))
    m.dot(on(sn_c, sn_r, (0, 0.25, 1))[0], (0, 0.2, 1), w=2.2, h=1.4, minw=2,
          color=('pink', 0))
    p, n = on(sn_c, sn_r, (0.1, -0.45, 1))
    m.mouth(p, n, 'smile', w=3.0)
    m.dot(add(p, (0, -1.0, 0.2)), n, w=1.6, h=1.2, color='white', minw=2)
    return m


# ---- 29 FROSTOAT --------------------------------------------------------
def frostoat():
    m = Model('FROSTOAT')
    m.outline = (30, 36, 70)
    m.mat('snow', ['#7a86b8', '#b4c2e4', '#e8eefa', '#ffffff'],
          th=[0.2, 0.46, 0.76])
    m.mat('black', ['#1c1c2c', '#3a3c56'])
    m.mat('ice', ['#3a9ee0', '#9ae4ff', '#e8fdff'], emissive=0.3)
    m.mat('pink', ['#e890a8'])
    m.eye_dark = (22, 22, 40)
    m.white = (255, 255, 255)
    m.height = 36
    m.max_w = 58
    m.front_yaw = -28
    D = norm((0.62, 0, -0.78))
    N = (-D[2], 0, D[0])

    def P(u, y, w=0.0):
        return (D[0] * u + N[0] * w, y, D[2] * u + N[2] * w)
    # long slinky body: raised neck -> low back -> hips
    prof = [(-1.6, 17.0, 0.0, 2.9), (0.2, 13.6, 0.0, 3.4), (2.8, 10.0, 0.3, 4.0),
            (7.5, 8.4, 0.6, 4.0), (11.5, 8.8, 0.3, 4.1), (14.5, 9.2, 0.0, 3.9)]
    m.tube([P(u, y, w) for u, y, w, r in prof], [r for u, y, w, r in prof],
           'snow', 'body')
    # tail: white, then black, tipped with frost crystals
    tail = [P(16.5, 9.8, 0.0), P(19.5, 11.5, 0.2), P(22.0, 14.5, 0.3),
            P(23.4, 18.0, 0.2), P(23.8, 21.0, 0.0)]
    m.tube(tail, [2.2, 2.3, 2.3, 2.1, 1.3], 'snow', 'tail',
           mats=[(0, 'snow'), (0.6, 'black')])
    tip = P(23.9, 22.0, 0.0)
    for k, (dx, dy, dz, ln) in enumerate(((0, 1, 0, 4.2), (-0.7, 0.6, 0.2, 3.2),
                                          (0.7, 0.7, -0.1, 3.4),
                                          (0.3, 0.5, 0.8, 2.6),
                                          (-0.3, 0.6, -0.8, 2.6))):
        d = norm((dx, dy, dz))
        m.crystal(sub(tip, mul(d, 0.8)), add(tip, mul(d, ln)),
                  1.0 if k else 1.2, 'ice', 'tail', sides=4, tip_frac=0.6,
                  twist=k * 20)
    # legs: hind pair planted, one fore paw raised (alert)
    for s in (-1, 1):
        h = add(P(13.0, 9.0, 0.0), mul(N, s * 2.8))
        m.ell(add(h, (0, -0.8, 0)), (2.4, 3.4, 3.0), 'snow', 'legB%d' % s)
        m.tube([add(h, (0, -2.0, 0.6)), add(h, (0, -5.8, 1.0)),
                add(h, (0, -7.8, 2.2))], [1.7, 1.3, 1.3], 'snow', 'legB%d' % s)
    fl = add(P(3.0, 9.0, 0.0), mul(N, -2.4))
    m.tube([fl, add(fl, (0, -4.5, 0.6)), add(fl, (0, -7.8, 1.4))],
           [1.6, 1.3, 1.3], 'snow', 'legFa')
    fr = add(P(3.0, 10.5, 0.0), mul(N, 2.6))
    m.tube([fr, add(fr, (0.4, -2.6, 2.6)), add(fr, (0.6, -4.2, 3.8))],
           [1.6, 1.3, 1.25], 'snow', 'legFb')
    # head: small, alert, rounded ears
    head_c, head_r = add(P(-2.8, 20.6, 0.0), (0, 0, 0.8)), (4.6, 4.1, 4.3)
    m.ell(head_c, head_r, 'snow', 'head')
    sn_c, sn_r = add(head_c, (0.9, -1.0, 3.5)), (2.2, 1.8, 2.2)
    m.ell(sn_c, sn_r, 'snow', 'head')
    for s in (-1, 1):
        e = add(head_c, (s * 3.2, 3.0, -0.8))
        m.ell(e, (1.8, 1.8, 0.8), 'snow', 'ear%d' % s, rot=(s * 15, 0, 0))
        m.paint(add(e, (0, 0, 0.5)), (1.0, 1.0, 0.6), 'pink', ['ear%d' % s])
    eye_pair(m, head_c, head_r, 28, 14, 3.2, 3.8, iris=('black', 1), turn=10,
             center=add(head_c, (0, -1, 6)))
    m.dot(on(sn_c, sn_r, (0, 0.3, 1))[0], (0, 0.2, 1), w=1.6, h=1.1, minw=2,
          color=('pink', 0))
    p, n = on(sn_c, sn_r, (0, -0.5, 1))
    m.mouth(p, n, 'w', w=2.6)
    return m


# ---- 30 WISPIRE ----------------------------------------------------------
def wispire():
    m = Model('WISPIRE')
    m.outline = (20, 12, 36)
    m.mat('body', ['#1e1434', '#3a245a', '#5e3c86', '#8e64b6'])
    m.mat('glow', ['#46b8e2', '#a6eeff', '#f2ffff'], emissive=0.8)
    m.mat('flame', ['#6a8ef0', '#a6eeff'], emissive=0.55)
    m.mat('core', ['#f2ffff'], emissive=0.9)
    m.eye_dark = (14, 8, 30)
    m.height = 50
    m.float_lift = 2
    # trailing tail
    m.tube([(0, 14, -1), (1.5, 8, -3), (5, 3.5, -4), (10, 2.5, -2),
            (13, 4.5, 0.5)], [7.2, 5.2, 3.2, 1.6, 0.2], 'body', 'body')
    body_c, body_r = (0, 21, 0), (9, 10, 8.4)
    m.ell(body_c, body_r, 'body', 'body')
    # wispy arms
    for s in (-1, 1):
        m.tube([(s * 7.5, 21, 1), (s * 11, 18, 2), (s * 13.5, 14, 2.5),
                (s * 13, 11.5, 3)], [2.6, 2.0, 1.2, 0.2], 'body',
               'arm%d' % s)
    # hollow glowing face
    p, n = on(body_c, body_r, (0, 0.05, 1))
    m.paint(add(p, (0, 0.2, 0)), (6.2, 5.4, 3.2), 'glow', ['body'])
    for s in (-1, 1):
        q, nn = on(body_c, body_r, (s * 0.32, 0.18, 0.93))
        m.eye(q, nn, 2.6, 4.0, style='solid', iris='eye', slant=0.6,
              center=p)
    q, nn = on(body_c, body_r, (0.03, -0.22, 0.97))
    m.mouth(q, nn, 'open', w=3.6, h=2.2, color='eye', inner='eye')
    # ghost flame on the head
    flame(m, (0, 29.5, -0.5), 17, 6.0, 'flame', mats=('flame', 'glow',
                                                      'core'),
          up=(0.05, 1, -0.1), tongues=2, seed=30)
    return m


# ---- 31 DRAKORA ----------------------------------------------------------
def drakora():
    m = Model('DRAKORA')
    m.outline = (10, 30, 38)
    m.mat('scale', ['#0e4656', '#167480', '#28a8a0', '#72dcc4'])
    m.mat('gold', ['#a26c18', '#e6ae30', '#ffe486'])
    m.mat('memb', ['#244e86', '#3e82bc', '#80c4e8'])
    m.eye_dark = (12, 22, 30)
    m.height = 58
    m.max_w = 62
    m.back_scale = 1.12
    # wings (behind)
    for s in (-1, 1):
        sh_ = (s * 4.5, 35, -3)
        el = (s * 14, 45, -6.5)
        wr = (s * 23, 55, -9)
        fingers = [(s * 31, 48, -10), (s * 30, 37, -9), (s * 25, 28, -7.5),
                   (s * 16, 24, -5)]
        m.tube([sh_, el, wr], [2.4, 1.8, 1.3], 'scale', 'wing%d' % s)
        mem = [sh_, el, wr, fingers[0]]
        for i in range(3):
            mid = lerp(fingers[i], fingers[i + 1], 0.5)
            mem.append(add(mid, (-s * 3.2, 0.8, 0.4)))
            mem.append(fingers[i + 1])
        mem.append((s * 6, 27, -3))
        m.poly(mem, 'memb', 'wing%d' % s, puff=0.3)
        for f in fingers:
            m.tube([wr, f], [1.0, 0.4], 'gold', 'wing%d' % s)
        m.crystal(wr, add(wr, (s * 1, 4, -0.5)), 0.9, 'gold', 'wing%d' % s,
                  sides=4, tip_frac=0.7)
    # serpentine body: neck -> chest -> belly -> tail curling to +X
    spine = [(0.5, 41, 7.5), (1, 36, 5), (0, 30, 2.5), (-1.5, 23, 1.5),
             (-0.5, 16, 0.5), (3, 10, -1), (9, 6.5, -2), (15, 5.5, -1),
             (20, 7.5, 1), (23, 12, 2), (22.5, 16.5, 1.5)]
    radii = [3.8, 4.4, 5.2, 5.6, 5.4, 4.6, 3.6, 2.8, 2.0, 1.2, 0.3]
    m.tube(spine, radii, 'scale', 'body')
    fin = spine[-1]
    leaf(m, spine[-2], add(fin, (-0.5, 2.5, 0)), add(fin, (-2.5, 6, -0.5)),
         2.4, 'gold', 'tailfin', up=(0.6, 0, 0.8), flat=0.3)
    belly = [add(q, (0, -r * 0.1, r * 0.62))
             for q, r in zip(spine[1:6], radii[1:6])]
    m.tube(belly, [r * 0.66 for r in radii[1:6]], 'gold', 'body',
           flat=0.5, up=(0, 0, 1))
    for i in range(2, 9):
        q, r = spine[i], radii[i]
        m.crystal(add(q, (0, 0, -r * 0.6)), add(q, (0, 1.4, -r - 2.8)),
                  1.0, 'gold', 'body', sides=4, tip_frac=0.8)
    # arms
    for s in (-1, 1):
        m.tube([(s * 4.6, 28, 3), (s * 7, 23.5, 6), (s * 5.6, 21, 9)],
               [1.9, 1.5, 1.4], 'scale', 'arm%d' % s)
        for t in (-1, 0, 1):
            m.crystal((s * 5.6 + t * 0.8, 21, 9), (s * 5.6 + t * 1.4, 19, 11),
                      0.5, 'gold', 'arm%d' % s, sides=4, tip_frac=0.8)
    # head
    head_c, head_r = (0.5, 44.5, 9), (5.0, 4.4, 5.4)
    m.ell(head_c, head_r, 'scale', 'head')
    m.tube([(0.5, 43.6, 12), (0.5, 42.6, 15.5), (0.5, 41.8, 18.5)],
           [3.4, 2.6, 1.8], 'scale', 'head')
    m.tube([(0.5, 41.2, 11.5), (0.5, 40.4, 15.5), (0.5, 40.2, 17.5)],
           [2.4, 1.8, 1.2], 'gold', 'head')
    for s in (-1, 1):
        m.tube([(0.5 + s * 2.6, 47.5, 7.5), (0.5 + s * 4.8, 51, 4.5),
                (0.5 + s * 5.8, 54.5, 0.5), (0.5 + s * 5.4, 57.5, -2.5)],
               [1.5, 1.2, 0.8, 0.2], 'gold', 'horn%d' % s)
        m.tube([(0.5 + s * 4.0, 43.5, 6.5), (0.5 + s * 7.0, 42.5, 3.5),
                (0.5 + s * 8.6, 42.0, 1.5)], [1.6, 1.0, 0.2], 'memb', 'head',
               flat=0.35, up=(0, 0.3, 1))
    eye_pair(m, head_c, head_r, 40, 22, 4.0, 3.0, style='sharp',
             iris=('gold', 1), slant=1.0, lid=1, center=(0.5, 42, 19))
    m.mouth((0.5, 40.4, 17.4), (0, -0.2, 1), 'line', w=3.0)
    return m


# ---- placeholders for roster entries that have no art yet ----------------
TYPE_RAMPS = {
    'BEAST': ['#6a4a30', '#9c7248', '#c8a070', '#ecd2a4'], 'BLAZE': ['#8a2418', '#d0482a', '#f48a3c', '#ffd070'],
    'TIDE': ['#1c3c90', '#3470d0', '#62a8f0', '#b2e2ff'], 'BLOOM': ['#2c5a1c', '#4a8a2c', '#7cc044', '#c4ec8c'],
    'SPARK': ['#8a6a08', '#d0a818', '#f4dc40', '#fff6a8'], 'FROST': ['#3a6c90', '#68a4c8', '#a4d8ec', '#e8fbff'],
    'BRAWL': ['#6c1c14', '#a8382a', '#d86a4c', '#f4ac8c'], 'VENOM': ['#48184c', '#7a3486', '#b060bc', '#e0a6e6'],
    'STONE': ['#4c3c28', '#7c6644', '#a89068', '#d4c29c'], 'GALE': ['#3c4c8c', '#6478c4', '#98acec', '#d4e0ff'],
    'DREAM': ['#8a2458', '#c84c8c', '#f082b8', '#ffc4e0'], 'SWARM': ['#48560c', '#788a1c', '#a8bc3c', '#dcec84'],
    'DUSK': ['#1c1430', '#382a58', '#5c4a88', '#9082bc'], 'WYRM': ['#2c1870', '#4a30b0', '#7658e0', '#b4a0ff'],
    'HOLLOW': ['#4a4640', '#8a857a', '#c4beac', '#f2eee0'], 'RELIC': ['#5a3410', '#946020', '#c89440', '#f2d488'],
    'METAL': ['#343c48', '#5a6878', '#8c9cac', '#d0dce6'], 'ASTRAL': ['#34206c', '#6448b4', '#9c88e4', '#dcd2ff'],
}


def placeholder_model(spec):
    """A plain stand-in until the real art exists: body + head in type colours."""
    import zlib as _z
    h = _z.crc32(spec.name.encode())
    m = Model(spec.name)
    m.mat('a', TYPE_RAMPS[spec.types[0]])
    m.mat('b', TYPE_RAMPS[spec.types[-1]][1:])
    m.outline = (32, 24, 40)
    big = spec.rarity in 'LF'
    m.height = 40 if big else 32
    body_c, body_r = (0, 8, -1), (7.5 + (h % 3), 6.5, 8)
    m.ell(body_c, body_r, 'a', 'body')
    head_c, head_r = (0, 17 + (h >> 3) % 3, 4), (6.5, 6, 6)
    m.ell(head_c, head_r, 'a', 'head')
    m.paint((0, 8, 6), (5, 4.5, 3.5), 'b', ['body'])
    for sgn in (-1, 1):
        m.ell((sgn * 4, 2, 2), (2.2, 2.4, 2.4), 'a', 'foot%d' % sgn)
        kind = (h >> 5) % 3
        if kind == 0:
            m.tube([(sgn * 3.5, 22, 3), (sgn * 5.5, 27, 2)], [2.0, 0.4], 'b', 'ear%d' % sgn)
        elif kind == 1:
            m.ell((sgn * 6.2, 20, 3), (1.6, 3, 2), 'b', 'ear%d' % sgn)
    m.tube([(0, 8, -8), (0, 11, -12), (0, 14, -13)], [2.4, 1.8, 0.6], 'b', 'tail')
    eye_pair(m, head_c, head_r, 28, 10, 3.6, 4.6, iris=('a', 0), center=(0, 17, 12))
    return m


def _roster():
    """(name, build function) for every species in id order (tools/kin/)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import kin
    out = []
    g = sys.modules[__name__]
    specs = kin.load()
    for spec in specs:
        OW_TIER[spec.name] = (kin.tier(spec, specs), spec.rarity)
        if isinstance(spec.model, str):
            out.append((spec.name, globals()[spec.model]))
        elif callable(spec.model):
            out.append((spec.name, (lambda f: (lambda: f(g)))(spec.model)))
        else:
            out.append((spec.name, (lambda sp: (lambda: placeholder_model(sp)))(spec)))
    return out


SPECIES = _roster()


# --------------------------------------------------------------------------
def build_one(i):
    name, fn = SPECIES[i]
    m = fn()
    return i, make_sprites(m)


def main():
    args = sys.argv[1:]
    preview = None
    only = None
    header = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                          'src', 'gfx_monsters.h')
    jobs = os.cpu_count() or 1
    i = 0
    while i < len(args):
        if args[i] == '--preview':
            preview = args[i + 1]
            i += 2
        elif args[i] == '--only':
            only = [int(x) for x in args[i + 1].split(',')]
            i += 2
        elif args[i] == '--jobs':
            jobs = int(args[i + 1])
            i += 2
        else:
            raise SystemExit('unknown arg ' + args[i])
    ids = only if only is not None else list(range(len(SPECIES)))
    results = {}
    if jobs > 1 and len(ids) > 1:
        from multiprocessing import Pool
        with Pool(min(jobs, len(ids))) as pool:
            for i, res in pool.imap_unordered(build_one, ids):
                results[i] = res
    else:
        for i in ids:
            results[i] = build_one(i)[1]
    names = [s[0] for s in SPECIES]
    if preview:
        os.makedirs(preview, exist_ok=True)
        contact_sheets(results, preview, names)
        ow_sheet(results, preview, names)
        for k in range(0, len(ids), 4):
            chunk = ids[k:k + 4]
            review_sheet(results, preview, chunk, names,
                         '_'.join(str(c) for c in chunk))
    if only is None:
        write_header(os.path.abspath(header), results)
        print('wrote', os.path.abspath(header))


if __name__ == '__main__':
    main()
