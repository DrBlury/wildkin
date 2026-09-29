"""Reusable painters for the second-generation tilesets.

Every painter takes *role names* (usually ramps listed dark -> light) so the
same routine draws meadow grass, ash, snow or moss by swapping the ramp.
Style rules (docs/TILES2.md):
  * light from the upper left; forms shade towards the lower right,
  * coloured outlines (the darkest ramp step), never pure black,
  * ground is low-contrast so objects and people read on top of it,
  * texture in clusters (tufts, pebbles, leaf clumps), not pixel noise,
  * dithering only in transitions and wide gradients.
"""

import math

from core import (Img, Height, shade, rnd, hash32, bayer, value_noise, fbm, worley,
                  jitter_points, G, LIGHT)

CELL = 16


# ---------------------------------------------------------------------------
# small stamps
# ---------------------------------------------------------------------------

def stamp(img, x, y, text, legend, wrap=False):
    rows = [r.strip() for r in text.strip('\n').split('\n') if r.strip()]
    for j, r in enumerate(rows):
        for i, ch in enumerate(r):
            c = legend.get(ch)
            if c is None:
                continue
            if wrap:
                img.setw(x + i, y + j, c)
            else:
                img.set(x + i, y + j, c)


def scatter(w, h, n, seed, margin=1, min_dist=3.0, tries=400):
    """n well-spaced integer points inside [margin, w-margin)."""
    pts = []
    t = 0
    while len(pts) < n and t < tries:
        t += 1
        x = margin + int(rnd(t, 11, seed) * (w - 2 * margin))
        y = margin + int(rnd(t, 13, seed) * (h - 2 * margin))
        if all(math.hypot(x - a, y - b) >= min_dist for a, b in pts):
            pts.append((x, y))
    return pts


# ---------------------------------------------------------------------------
# ground textures (16x16, seamless against any tile of the same family)
# ---------------------------------------------------------------------------

TUFTS = [
    # d = dark blade, m = mid, l = light tip
    '''
    l.l
    d.d
    .d.
    ''',
    '''
    .l..
    ld.l
    .dd.
    ''',
    '''
    l..
    dl.
    .d.
    ''',
    '''
    ..l
    .ld
    .d.
    ''',
]


def grass(R, seed, tufts=5, flecks=4, dark_patch=0.0, flowers=None, pebbles=0,
          w=CELL, h=CELL, x0=0, y0=0):
    """Short grass. R = {'dk','mid','base','lt','hi'} roles.
    Tufts stay 1 px inside the cell so any two variants tile together."""
    img = Img(w, h, R['base'])
    # soft low-frequency patches (two tones) - sampled in absolute coords
    if dark_patch:
        for y in range(h):
            for x in range(w):
                n = value_noise(x + x0, y + y0, 6.0, seed + 3)
                if n < dark_patch and bayer(x, y) < (dark_patch - n) * 6:
                    img.p[y][x] = R['mid']
    leg = {'d': R['mid'], 'm': R['mid'], 'l': R['lt']}
    for i, (x, y) in enumerate(scatter(w - 3, h - 3, tufts, seed, margin=1, min_dist=4.2)):
        t = TUFTS[hash32(i, seed) % len(TUFTS)]
        stamp(img, x, y, t, leg)
    for i, (x, y) in enumerate(scatter(w - 1, h - 1, flecks, seed + 99, margin=1, min_dist=3)):
        if img.get(x, y) == R['base'] and img.get(x + 1, y) == R['base']:
            img.set(x, y, R['lt'])
            if rnd(i, seed, 4) < 0.5:
                img.set(x + 1, y, R['hi'])
    if flowers:
        for i, (x, y) in enumerate(scatter(w - 4, h - 4, flowers['n'], seed + 7, margin=2, min_dist=5)):
            petal = flowers['petals'][i % len(flowers['petals'])]
            stamp(img, x, y, '''
            .p.
            pcp
            .p.
            ''', {'p': petal, 'c': flowers['center']})
            img.set(x + 1, y + 3, R['mid'])
    for i, (x, y) in enumerate(scatter(w - 3, h - 3, pebbles, seed + 31, margin=2, min_dist=5)):
        stamp(img, x, y, '''
        lb
        bd
        ''', {'l': R.get('peb_hi', R['hi']), 'b': R.get('peb', R['lt']), 'd': R.get('peb_dk', R['mid'])})
    return img


def speckle_ground(R, seed, dots=10, cracks=0, pebbles=2, w=CELL, h=CELL, x0=0, y0=0,
                   grain=0.0):
    """Dirt / sand / ash floors. R: dk mid base lt hi (+ optional peb*)."""
    img = Img(w, h, R['base'])
    if grain:
        for y in range(h):
            for x in range(w):
                n = value_noise(x + x0, y + y0, 3.0, seed + 5)
                if n > 1 - grain and bayer(x + x0, y + y0) < 0.5:
                    img.p[y][x] = R['lt']
                elif n < grain * 0.8 and bayer(x + x0, y + y0) > 0.5:
                    img.p[y][x] = R['mid']
    for i, (x, y) in enumerate(scatter(w - 2, h - 2, dots, seed, margin=1, min_dist=2.6)):
        k = hash32(i, seed) % 3
        if k == 0:
            img.set(x, y, R['mid'])
        elif k == 1:
            img.set(x, y, R['lt'])
            img.set(x + 1, y, R['lt'])
        else:
            img.set(x, y, R['mid'])
            img.set(x - 1, y - 1, R['lt'])
    for i, (x, y) in enumerate(scatter(w - 4, h - 4, pebbles, seed + 17, margin=2, min_dist=5)):
        big = hash32(i, seed, 2) & 1
        if big:
            stamp(img, x, y, '''
            .hl.
            hlld
            .dd.
            ''', {'h': R['hi'], 'l': R['lt'], 'd': R['dk']})
        else:
            stamp(img, x, y, '''
            hl
            ld
            ''', {'h': R['hi'], 'l': R['lt'], 'd': R['dk']})
    for i in range(cracks):
        x = 2 + hash32(i, seed, 3) % (w - 5)
        y = 2 + hash32(i, seed, 4) % (h - 5)
        for s in range(4):
            img.set(x, y, R['dk'])
            x += 1
            y += (hash32(i, s, seed) % 3) - 1
            y = max(1, min(h - 2, y))
    return img


# ---------------------------------------------------------------------------
# quad autotiles (rmxp16 blocks) from a signed-distance description
# ---------------------------------------------------------------------------

def _quad_sdf(v, px, py, E, R, Rn, wob):
    if v == 0:
        return 99.0
    if v == 2:
        return px - E - wob(py)
    if v == 3:
        return py - E - wob(px)
    if v == 4:
        ax, ay = (E + R) - px, (E + R) - py
        if ax > 0 and ay > 0:
            return R - math.hypot(ax, ay)
        return min(px - E - wob(py), py - E - wob(px))
    if v == 1:
        ax, ay = px - (E - Rn), py - (E - Rn)
        if ax > 0 and ay > 0:
            return math.hypot(ax, ay) - Rn
        return max(ax, ay) - Rn
    raise ValueError(v)


def _virtual_variant(bx, by, c):
    """Quad variant of quadrant c for block cell (bx, by) of an rmxp16 block,
    plus which side(s) face outward."""
    if by == 0:
        if bx == 0:
            return 4
        if bx == 1:
            return 0
        return 1
    gx, gy = bx, by - 1          # 3x3 island inside a 5x5 map

    def inside(x, y):
        return 0 <= x < 3 and 0 <= y < 3
    dx = -1 if c in (0, 2) else 1
    dy = -1 if c in (0, 1) else 1
    vs = inside(gx, gy + dy)
    hs = inside(gx + dx, gy)
    ds = inside(gx + dx, gy + dy)
    if vs and hs:
        return 0 if ds else 1
    return 2 if vs else (3 if hs else 4)


QUAD_OFF = ((0, 0), (8, 0), (0, 8), (8, 8))


def side_of(v, c):
    """Which outward side a quadrant faces: N/S/W/E or corner NW..."""
    ns = 'N' if c in (0, 1) else 'S'
    we = 'W' if c in (0, 2) else 'E'
    if v == 2:
        return we
    if v == 3:
        return ns
    if v in (1, 4):
        return ns + we
    return ''


def autotile_block(color_at, E=4.0, R=4.0, Rn=3.0, wob=None, dither=1.0, alt_seed=None):
    """Build a 48x64 rmxp16 block.

    color_at(d, X, Y, side, v, alt) -> role. d > 0 inside the autotiled
    material, < 0 outside (the surrounding ground). X, Y are absolute pixel
    coordinates within a 16-px cell (texture continuity), side is 'N', 'SW'...
    """
    if wob is None:
        def wob(t):
            return 0.0
    img = Img(48, 64)
    for by in range(4):
        for bx in range(3):
            for c, (qx, qy) in enumerate(QUAD_OFF):
                v = _virtual_variant(bx, by, c)
                side = side_of(v, c)
                alt = (bx == 1 and by == 0)
                for y in range(8):
                    for x in range(8):
                        X, Y = qx + x, qy + y
                        lx = x if (c & 1) == 0 else 7 - x
                        ly = y if (c >> 1) == 0 else 7 - y
                        d = _quad_sdf(v, lx + 0.5, ly + 0.5, E, R, Rn,
                                      (lambda t, _c=c: wob(t, _c)) if wob.__code__.co_argcount == 2 else wob)
                        if v and dither:
                            d += (bayer(X, Y) - 0.5) * dither
                        img.p[by * 16 + Y][bx * 16 + X] = color_at(d, X, Y, side, v, alt)
    return img


def block_from_cells(cells):
    """cells: dict (bx, by) -> 16x16 Img for a 3x4 block."""
    img = Img(48, 64)
    for (bx, by), c in cells.items():
        img.paste(c, bx * 16, by * 16)
    return img


# ---------------------------------------------------------------------------
# foliage and rounded forms
# ---------------------------------------------------------------------------

def foliage(w, h, clumps_list, ramp, outline, seed=0, light=LIGHT, crown_ao=None,
            leaf_tex=True, contrast=1.15, bias=0.0, rim_light=None):
    """Union of leaf clumps (x, y, r[, ry]) shaded as a clumpy crown.
    ramp: dark -> light roles (4-6). Returns an Img with an outline."""
    H = Height(w, h)
    for cl in clumps_list:
        x, y, r = cl[0], cl[1], cl[2]
        ry = cl[3] if len(cl) > 3 else r * 0.92
        H.add_ellipsoid(x, y, r, ry, top=1.0)
    img = shade(H, ramp, light=light, contrast=contrast, bias=bias, dither=0.3,
                ao=crown_ao, seed=seed)
    if leaf_tex:
        # little leaf notches: dark pixel under a light one, on lit areas
        for i, (x, y) in enumerate(scatter(w, h, (w * h) // 22, seed + 5, margin=1, min_dist=2.8)):
            c = img.get(x, y)
            if c is None or img.get(x, y + 1) is None:
                continue
            k = ramp.index(c) if c in ramp else 0
            if 1 <= k < len(ramp) - 1:
                img.set(x, y, ramp[k + 1])
                img.set(x, y + 1, ramp[k - 1])
    out = img.outline(outline)
    if rim_light:
        # soften the lit top-left silhouette
        for y in range(h):
            for x in range(w):
                if out.p[y][x] == outline and img.p[y][x] is None:
                    if img.inside(x + 1, y + 1) and not img.inside(x - 1, y) and not img.inside(x, y - 1):
                        out.p[y][x] = rim_light
    return out


def crown_ao(cx, cy, rx, ry, strength=0.35):
    """Darken the lower right of a crown (global form)."""
    def f(x, y):
        dx = (x - cx) / rx
        dy = (y - cy) / ry
        return max(0.0, (dx * 0.4 + dy * 0.9)) * strength
    return f


def blob(w, h, parts, ramp, outline, seed=0, contrast=1.1, bias=0.0, jitter=0.0,
         light=LIGHT, dither=0.3, ao=None):
    """Smooth rounded forms (rocks, bushes, snow mounds, pots)."""
    H = Height(w, h)
    for p in parts:
        H.add_ellipsoid(*p)
    img = shade(H, ramp, light=light, contrast=contrast, bias=bias, dither=dither,
                seed=seed, jitter=jitter, ao=ao)
    return img.outline(outline)


def faceted(w, h, mask, ramp, outline, seed, cells=6.0, light=LIGHT, flat=0.65, crack=None):
    """Faceted stone: Worley cells inside mask (callable x,y->bool), each with
    its own tilted plane; creases between facets darken."""
    pts = jitter_points(w, h, cells, seed)
    normals = []
    for i in range(len(pts)):
        a = rnd(i, seed, 1) * math.tau
        tilt = 0.25 + rnd(i, seed, 2) * 0.5
        normals.append((math.cos(a) * tilt, math.sin(a) * tilt * 0.8 - 0.25, 1.0))
    L = LIGHT
    ln = math.sqrt(sum(c * c for c in L))
    img = Img(w, h)
    n = len(ramp)
    for y in range(h):
        for x in range(w):
            if not mask(x, y):
                continue
            i, d1, d2 = worley(x + 0.5, y + 0.5, pts)
            nx, ny, nz = normals[i]
            # global dome: facets near the lower right face away from the light
            gx = (x - w / 2) / (w / 2)
            gy = (y - h / 2) / (h / 2)
            nx += gx * (1 - flat)
            ny += gy * (1 - flat)
            nl = math.sqrt(nx * nx + ny * ny + nz * nz)
            lum = (nx * L[0] + ny * L[1] + nz * L[2]) / (nl * ln)
            t = (lum - 0.3) * 1.4 * (n - 1) + (n - 1) * 0.45
            t += (bayer(x, y) - 0.5) * 0.5
            k = max(0, min(n - 1, int(round(t))))
            if d2 - d1 < 0.9 and k > 0:
                k = max(0, k - 2) if crack is None else k
                if crack:
                    img.set(x, y, crack)
                    continue
            img.set(x, y, ramp[k])
    return img.outline(outline)


# ---------------------------------------------------------------------------
# helpers for building blocks
# ---------------------------------------------------------------------------

def cells_of(img):
    """Split an image into a dict (cx, cy) -> 16x16 Img."""
    out = {}
    for cy in range(img.h // CELL):
        for cx in range(img.w // CELL):
            out[(cx, cy)] = img.crop(cx * CELL, cy * CELL, CELL, CELL)
    return out


def tile_texture(fn, w=CELL, h=CELL):
    img = Img(w, h)
    for y in range(h):
        for x in range(w):
            img.p[y][x] = fn(x, y)
    return img


def overlay(base, top):
    o = base.copy()
    o.paste(top, 0, 0)
    return o


def shadow_under(img, ground_dark, rows=2):
    """For ground-baked objects: darken the ground right below the shape."""
    return img


def clump_crown(w, h, clumps_list, ramp, outline, seed=0, light=LIGHT, gdark=0.35,
                bias=0.0, rim=1.3, speck=True, cx=None, cy=None, sep=None, wrap=False,
                fill=None, dither=0.7, snow=None):
    """Foliage from clumps drawn back to front: each clump is a small lit
    dome with a dark lower rim, so overlapping clumps read as separate
    leaf masses (the GBA-era look). ramp: dark -> light (4-6 roles)."""
    if not clumps_list:
        return Img(w, h)
    n = len(ramp)
    Lx, Ly, Lz = light
    ll = math.sqrt(Lx * Lx + Ly * Ly + Lz * Lz)
    Lx, Ly, Lz = Lx / ll, Ly / ll, Lz / ll
    if cx is None:
        cx = sum(c[0] for c in clumps_list) / len(clumps_list)
        cy = sum(c[1] for c in clumps_list) / len(clumps_list)
    gx0 = max(abs(c[0] - cx) + c[2] for c in clumps_list)
    gy0 = max(abs(c[1] - cy) + (c[3] if len(c) > 3 else c[2]) for c in clumps_list)
    img = Img(w, h, fill)
    if wrap:
        base = list(clumps_list)
        clumps_list = []
        for c in base:
            for ox in (-w, 0, w):
                for oy in (-h, 0, h):
                    clumps_list.append((c[0] + ox, c[1] + oy) + tuple(c[2:]))
    order = sorted(range(len(clumps_list)), key=lambda i: (clumps_list[i][1], clumps_list[i][0]))
    for i in order:
        c = clumps_list[i]
        x0, y0, r = c[0], c[1], c[2]
        ry = c[3] if len(c) > 3 else r
        for y in range(int(y0 - ry - 1), int(y0 + ry + 2)):
            for x in range(int(x0 - r - 1), int(x0 + r + 2)):
                if not (0 <= x < w and 0 <= y < h):
                    continue
                dx = (x + 0.5 - x0) / r
                dy = (y + 0.5 - y0) / ry
                q = 1 - dx * dx - dy * dy
                if q < 0:
                    continue
                nz = math.sqrt(q)
                lum = dx * Lx + dy * Ly + nz * Lz
                # global crown form: lower right is darker
                if not wrap:
                    gx = (x + 0.5 - cx) / gx0
                    gy = (y + 0.5 - cy) / gy0
                    lum -= max(0.0, gx * 0.45 + gy * 0.8) * gdark
                if len(c) > 4 and c[4]:
                    gcx, gcy, gr = c[4]
                    lum -= max(0.0, ((x + 0.5 - gcx) * 0.45 + (y + 0.5 - gcy) * 0.85) / gr) * 0.45
                    lum += max(0.0, -((x + 0.5 - gcx) * 0.5 + (y + 0.5 - gcy) * 0.8) / gr) * 0.12
                lum += 0.08
                t = (lum + bias) * (n - 0.6)
                t += (bayer(x, y) - 0.5) * dither
                k = max(0, min(n - 1, int(t)))
                # dark rim on the lower-right part of the clump edge
                edge = (1 - math.sqrt(dx * dx + dy * dy)) * min(r, ry)
                if edge < rim and (dx * 0.5 + dy) > 0.1:
                    k = 0 if sep is None else sep
                img.p[y][x] = ramp[k]
                if snow and dy < -0.25:
                    if edge < 1.4 + (0.6 if dy < -0.6 else 0):
                        img.p[y][x] = snow[0]
                    elif edge < 2.6 and (x + y) % 2 and dy < -0.5:
                        img.p[y][x] = snow[1]
    if speck:
        for i, (x, y) in enumerate(scatter(w, h, max(2, (w * h) // 40), seed + 5, margin=2, min_dist=3.5)):
            c = img.get(x, y)
            if c is None or c not in ramp:
                continue
            k = ramp.index(c)
            if 2 <= k <= n - 2 and img.get(x + 1, y) is not None and img.get(x, y + 1) is not None:
                img.set(x, y, ramp[min(n - 1, k + 1)])
                img.set(x + 1, y, ramp[min(n - 1, k + 1)])
                img.set(x, y + 1, ramp[k - 1])
    if wrap or outline is None:
        return img
    return img.outline(outline)


def snowcap(img, hi, lo, out=None, depth=2, edges=()):
    """Settle snow on every upward-facing edge of a shape (crowns, rocks,
    walls): the top pixel of each column run becomes hi, the next lo.
    edges: extra roles that count as an edge above (e.g. the dark rim
    between leaf clumps), so inner clumps get snow too."""
    o = img.copy()
    stop = (None, out) + tuple(edges)
    for y in range(img.h):
        for x in range(img.w):
            c = img.p[y][x]
            if c in stop:
                continue
            above = img.get(x, y - 1)
            if above in stop:
                o.p[y][x] = hi
                if depth > 1 and img.get(x, y + 1) not in (None, out) and (x + y) % 2:
                    o.p[y + 1][x] = lo
    return o
