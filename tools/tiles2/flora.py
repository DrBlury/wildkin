"""Plants: trees, conifers, bushes, hedges, forest walls, tall grass,
flowers, reeds, mushrooms, logs. Pass role ramps (dark -> light)."""

import math

from core import Img, rnd, hash32, bayer, value_noise
from paint import clump_crown, scatter, stamp, blob, CELL


# ---------------------------------------------------------------------------
# trunks and trees
# ---------------------------------------------------------------------------

def trunk(img, cx, y0, y1, width, bark, outline, roots=2, seed=0):
    """Draw a trunk centred on cx from y0 (hidden under the crown) to y1
    (ground line). bark: dark -> light (>= 3). Left side lit."""
    n = len(bark)
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, (y1 - y0))
        flare = roots * max(0.0, (t - 0.65) / 0.35) ** 1.6
        hw = width / 2 + flare
        xl, xr = int(math.floor(cx - hw)), int(math.ceil(cx + hw)) - 1
        for x in range(xl, xr + 1):
            u = (x + 0.5 - (cx - hw)) / max(1.0, 2 * hw)
            k = 2 if u < 0.3 else (1 if u < 0.7 else 0)
            k = min(n - 1, k + (1 if u < 0.18 else 0))
            if (x * 3 + y * 7 + seed) % 11 == 0 and 0.2 < u < 0.8:
                k = max(0, k - 1)            # bark knot
            img.set(x, y, bark[k])
        img.set(xl - 1, y, outline)
        img.set(xr + 1, y, outline)
    # ground line under the root flare
    hw = width / 2 + roots
    for x in range(int(math.floor(cx - hw)), int(math.ceil(cx + hw))):
        img.set(x, y1 + 1, outline)


def tree(w, h, clumps_list, leaf, leaf_out, bark, bark_out, trunk_w=4, trunk_top=None,
         ground_y=None, seed=0, roots=2, fruit=None, gdark=0.4, bias=0.0, sep=None,
         trunk_x=None):
    """A tree object w x h px: trunk first, crown (clumps) over it.
    fruit: optional (role_light, role_dark, count)."""
    img = Img(w, h)
    gy = ground_y if ground_y is not None else h - 3
    crown = clump_crown(w, h, clumps_list, leaf, leaf_out, seed=seed, gdark=gdark,
                        bias=bias, sep=sep)
    bottom = max(c[1] + (c[3] if len(c) > 3 else c[2]) for c in clumps_list)
    cx = trunk_x if trunk_x is not None else w / 2
    trunk(img, cx, int(trunk_top if trunk_top is not None else bottom - 6), gy, trunk_w,
          bark, bark_out, roots=roots, seed=seed)
    img.paste(crown, 0, 0)
    if fruit:
        lt, dk, n = fruit
        pts = [(x, y) for (x, y) in scatter(w, int(bottom), n * 3, seed + 21, margin=3, min_dist=5)
               if crown.get(x, y) not in (None, leaf_out) and crown.get(x + 1, y + 1) not in (None, leaf_out)]
        for (x, y) in pts[:n]:
            img.set(x, y, lt)
            img.set(x + 1, y, dk)
            img.set(x, y + 1, dk)
            img.set(x + 1, y + 1, dk)
    return img


def round_tree(size, leaf, leaf_out, bark, bark_out, seed=0, fruit=None, bias=0.0):
    """Deciduous presets. size: 'small' 16x32, 'mid' 32x32, 'big' 48x48."""
    if size == 'small':
        cl = [(8, 8, 5.5), (5, 11, 4), (11, 11, 4), (8, 14, 5), (8, 5, 4.2)]
        return tree(16, 32, cl, leaf, leaf_out, bark, bark_out, trunk_w=3, ground_y=28,
                    seed=seed, roots=1, fruit=fruit, bias=bias)
    if size == 'mid':
        cl = [(16, 10, 7.5), (9, 13, 6), (23, 13, 6), (11, 7, 5.5), (21, 7, 5.5),
              (16, 5, 5.5), (12, 18, 6), (20, 18, 6), (16, 20, 5)]
        return tree(32, 32, cl, leaf, leaf_out, bark, bark_out, trunk_w=4, ground_y=29,
                    seed=seed, fruit=fruit, bias=bias)
    if size == 'big':
        cl = [(24, 16, 10), (13, 19, 8), (35, 19, 8), (16, 10, 7.5), (32, 10, 7.5),
              (24, 7, 7.5), (8, 26, 6.5), (40, 26, 6.5), (17, 28, 8), (31, 28, 8),
              (24, 30, 7), (24, 20, 8)]
        return tree(48, 48, cl, leaf, leaf_out, bark, bark_out, trunk_w=6, ground_y=45,
                    seed=seed, roots=3, fruit=fruit, bias=bias)
    raise ValueError(size)


def conifer(w, h, leaf, leaf_out, bark, bark_out, seed=0, tiers=4, snow=None, ground_y=None):
    """Pine/fir: drooping tiers of boughs, narrow at the top.
    snow: optional (role_hi, role_lo) to cap each tier."""
    img = Img(w, h)
    gy = ground_y if ground_y is not None else h - 3
    top = 1
    bottom = gy - 5
    cl = []
    for t in range(tiers):
        f = (t + 1) / tiers
        y = top + 4 + (bottom - top - 6) * (t / max(1, tiers - 1)) ** 0.95
        half = 2.5 + (w / 2 - 2.5) * f
        n = 1 + int(half // 3.2)
        for i in range(n):
            u = (i + 0.5) / n
            x = w / 2 - half + 2 * half * u
            r = max(2.6, half / n * 1.25 + 1)
            dy = abs(u - 0.5) * 3.0            # boughs droop outward
            cl.append((x, y + dy, r, max(2.4, r * 0.75)))
        cl.append((w / 2, y - 1.5, max(2.5, half * 0.45), 3.2))
    trunk(img, w / 2, int(bottom - 2), gy, max(2, w // 10), bark, bark_out, roots=1, seed=seed)
    crown = clump_crown(w, h, cl, leaf, leaf_out, seed=seed, gdark=0.45, rim=1.2, cx=w / 2,
                        cy=h * 0.5)
    img.paste(crown, 0, 0)
    if snow:
        hi, lo = snow
        for c in cl:
            x0, y0, r = c[0], c[1], c[2]
            ry = c[3] if len(c) > 3 else r
            for x in range(int(x0 - r + 1), int(x0 + r)):
                # topmost leaf pixel of this bough gets snow
                for y in range(int(y0 - ry - 1), int(y0 + 1)):
                    if crown.get(x, y) is not None and crown.get(x, y) != leaf_out:
                        if abs(x + 0.5 - x0) < r * 0.8:
                            img.set(x, y, hi)
                            if crown.get(x, y + 1) not in (None, leaf_out) and (x + y) % 2:
                                img.set(x, y + 1, lo)
                        break
    return img


def dead_tree(w, h, bark, bark_out, seed=0, ground_y=None, spread=1.0):
    """Leafless tree: a trunk forking into upward-reaching branches."""
    img = Img(w, h)
    gy = ground_y if ground_y is not None else h - 3
    segs = []

    def branch(x, y, ang, ln, th, depth):
        # slight wiggle along each limb
        steps = max(2, int(ln / 3))
        px, py = x, y
        for i in range(steps):
            a = ang + (rnd(i, depth, int(x * 7), seed) - 0.5) * 0.35
            nx = px + math.cos(a) * ln / steps
            ny = py + math.sin(a) * ln / steps
            t = th * (1 - 0.35 * i / steps)
            segs.append((px, py, nx, ny, t))
            px, py = nx, ny
        if depth <= 0:
            return
        forks = [(-0.42, 0.72), (0.38, 0.66)]
        if depth == 3:
            forks.append((0.02, 0.5))
        for j, (da, lf) in enumerate(forks):
            a = ang + da * spread + (rnd(j, depth, seed) - 0.5) * 0.2
            a = max(-math.pi + 0.35, min(-0.35, a))      # keep limbs pointing up
            branch(px, py, a, ln * lf, max(1.0, th * 0.62), depth - 1)
    branch(w / 2, gy, -math.pi / 2, h * 0.34, max(2.5, w / 9), 3)
    mask = Img(w, h)
    for (x1, y1, x2, y2, th) in segs:
        n = int(max(abs(x2 - x1), abs(y2 - y1)) * 2) + 1
        for s_ in range(n + 1):
            t = s_ / n
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t
            r = th / 2
            for yy in range(int(y - r - 1), int(y + r + 2)):
                for xx in range(int(x - r - 1), int(x + r + 2)):
                    if (xx + 0.5 - x) ** 2 + (yy + 0.5 - y) ** 2 <= r * r + 0.3:
                        mask.set(xx, yy, 1)
    nb = len(bark)
    for y in range(h):
        for x in range(w):
            if mask.p[y][x]:
                lit = mask.get(x - 1, y) is None
                dark = mask.get(x + 1, y) is None
                k = nb - 1 if lit and not dark else (0 if dark else 1)
                img.p[y][x] = bark[k]
    for dx in (-3, -2, 2, 3):
        img.set(int(w / 2 + dx), gy, bark[0])
    img.set(int(w / 2 - 4), gy, bark[1])
    return img.outline(bark_out)


# ---------------------------------------------------------------------------
# bushes, hedges, forest walls
# ---------------------------------------------------------------------------

def bush(w, h, leaf, leaf_out, seed=0, berries=None, flowers=None, n=None):
    """Round shrub filling most of a w x h box, sitting on its bottom row."""
    cl = []
    k = n or max(3, (w * h) // 48)
    cx, cy = w / 2, h * 0.58
    rx, ry = w / 2 - 1.5, h * 0.42 - 1
    for i in range(k):
        a = (i / k) * math.tau + rnd(i, seed) * 0.6
        rr = 0.55 + rnd(i, seed, 1) * 0.3
        x = cx + math.cos(a) * rx * rr * 0.62
        y = cy + math.sin(a) * ry * rr * 0.62
        r = min(rx, ry) * (0.5 + rnd(i, seed, 2) * 0.2)
        cl.append((x, y, r * 1.1, r))
    cl.append((cx, cy - 1, min(rx, ry) * 0.62, min(rx, ry) * 0.56))
    img = clump_crown(w, h, cl, leaf, leaf_out, seed=seed, gdark=0.45, rim=1.0, cx=cx, cy=cy)
    for spec in (berries, flowers):
        if not spec:
            continue
        lt, dk, cnt = spec
        pts = [(x, y) for (x, y) in scatter(w, h, cnt * 4, seed + 9, margin=2, min_dist=3.5)
               if img.get(x, y) not in (None, leaf_out) and img.get(x + 1, y + 1) not in (None, leaf_out)]
        for (x, y) in pts[:cnt]:
            img.set(x, y, lt)
            img.set(x + 1, y + 1, dk)
            if spec is flowers:
                img.set(x + 1, y, lt)
                img.set(x, y + 1, lt)
    return img


def crown_clumps(cx, cy, R, seed=0, lobes=4):
    """Sub-clumps of one round crown centred at (cx, cy) with radius R, each
    tagged with the crown centre so the whole crown shades as one form."""
    g = (cx, cy, R)
    out = [(cx, cy - R * 0.38, R * 0.62, R * 0.55, g)]
    for i in range(lobes):
        a = math.pi * (0.15 + 0.7 * i / max(1, lobes - 1)) + (rnd(i, seed) - 0.5) * 0.3
        out.append((cx - math.cos(a) * R * 0.45, cy + math.sin(a) * R * 0.25 - R * 0.05,
                    R * 0.55, R * 0.5, g))
    out.append((cx, cy + R * 0.3, R * 0.6, R * 0.52, g))
    return out


def lattice_render(mask, W, H, leaf, leaf_out, seed, period=16, r=7.0, ry=None,
                   bottom=None, top_inset=2, trunks=None, centers=((8, 5.5), (0, 13.5)),
                   lobes=4, snow=None):
    """Render a mass of round crowns filling the cells where mask(cx, cy)
    is true. Crowns sit on a staggered lattice with the given period, so
    interior cells are seamless; crowns never cross into outside cells, so
    edges come out scalloped. bottom='trunks' shows trunks under the crowns
    of south-edge cells. trunks: (bark ramp, bark outline)."""
    ry = ry or r * 0.92
    per = period
    pts = []
    for cy in range(-1, H // per + 2):
        for cx in range(-1, W // per + 2):
            for (bx, by) in centers:
                pts.append((cx * per + bx, cy * per + by))

    def cell_in(x, y):
        return mask(int(math.floor(x / per)), int(math.floor(y / per)))

    def ok(x, y, rr, rry):
        for k in range(12):
            a = k * math.pi / 6
            if not cell_in(x + math.cos(a) * (rr - 0.6), y + math.sin(a) * (rry - 0.6)):
                return False
        if bottom == 'trunks' and not cell_in(x, y + rry + 3.5):
            return False
        return True
    crowns = []
    for i, (x, y) in enumerate(pts):
        rr = r * (0.94 + (hash32(int(x) % per, int(y) % per, seed) % 100) / 900.0)
        rry = ry
        if ok(x, y, rr, rry):
            crowns.append((x, y, rr, rry))
    if not crowns:
        for cy in range(H // per):
            for cx in range(W // per):
                if mask(cx, cy):
                    crowns.append((cx * per + 8, cy * per + 6, 6.5, 5.8))
    cl = []
    for i, (x, y, rr, rry) in enumerate(crowns):
        cl.extend(crown_clumps(x, y, rr, seed=hash32(int(x) % per, int(y) % per, seed), lobes=lobes))
    img = Img(W, H)
    if trunks and bottom == 'trunks':
        bark, bark_out = trunks
        for (x, y, rr, rry) in crowns:
            below = y + rry + 3
            if not cell_in(x, y + per):
                gy = int(math.floor((y + rry) / per)) * per + per - 3
                if gy > y + rry - 2:
                    trunk(img, x, int(y), gy, 3, bark, bark_out, roots=1)
    crown = clump_crown(W, H, cl, leaf, leaf_out, seed=seed, gdark=0.0, rim=1.15, speck=True, snow=snow)
    img.paste(crown, 0, 0)
    return img


def shape_patch9(render):
    """Build a patch9 block (80x48) from render(mask, W, H) -> Img.

    Outer pieces come from a 3x3 island, inner corners from a filled area
    missing one diagonal cell each, extras: fill again and a lone cell."""
    block = Img(80, 48)
    A = render(lambda cx, cy: 1 <= cx <= 3 and 1 <= cy <= 3, 80, 80)
    for by in range(3):
        for bx in range(3):
            block.paste(A.crop((bx + 1) * 16, (by + 1) * 16, 16, 16), bx * 16, by * 16)
    for k, (dx, dy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        B = render(lambda cx, cy, dx=dx, dy=dy: 0 <= cx <= 4 and 0 <= cy <= 4
                   and not (cx == 2 + dx and cy == 2 + dy), 80, 80)
        block.paste(B.crop(32, 32, 16, 16), (3 + k % 2) * 16, (k // 2) * 16)
    block.paste(A.crop(32, 32, 16, 16), 48, 32)
    C = render(lambda cx, cy: cx == 2 and cy == 2, 80, 80)
    block.paste(C.crop(32, 32, 16, 16), 64, 32)
    return block


def forest_wall(leaf, leaf_out, bark, bark_out, seed=0, r=7.2, snow=None):
    """Dense forest canopy as a patch9 (transparent, solid). The south edge
    shows trunks; the other edges are scalloped crowns. snow=(hi, lo) caps
    every crown."""
    from paint import snowcap

    def render(mask, W, H):
        return lattice_render(mask, W, H, leaf, leaf_out, seed, r=r, bottom='trunks',
                              trunks=(bark, bark_out), snow=snow)
    return shape_patch9(render)


def hedge_wall(leaf, leaf_out, seed=0, r=4.6, base=None):
    """Clipped hedge as a patch9: tight small crowns, dark base line."""
    def render(mask, W, H):
        img = lattice_render(mask, W, H, leaf, leaf_out, seed, period=16, r=r, ry=r * 0.85,
                             centers=((4, 4.5), (12, 4.5), (0, 11.5), (8, 11.5)), lobes=2)
        if base:
            for y in range(H - 1):
                for x in range(W):
                    if img.p[y][x] is not None and img.p[y + 1][x] is None and not mask(x // 16, (y + 1) // 16):
                        img.p[y][x] = base
        return img
    return shape_patch9(render)


# ---------------------------------------------------------------------------
# small plants
# ---------------------------------------------------------------------------

BLADE = '''
.l...l.
.ml.lm.
.dm.md.
ldmdmdl
'''


def tallgrass(G, frame=0, seed=0, w=16, h=16, sway=0):
    """Encounter grass texture (opaque, over its own dark base).
    G: {'out','dk','mid','base','lt','hi'}. Four staggered tufts per cell."""
    img = Img(w, h, G['dk'])
    for y in range(h):
        for x in range(w):
            if (x + y) % 3 == 0 and y % 2:
                img.p[y][x] = G['out']
    tuft = [
        '..l.l..',
        '.lm.ml.',
        '.mb.bm.',
        'lbd.dbl',
        'mbd.dbm',
        'bdd.ddb',
        'dd...dd',
    ]
    spots = [(0, -1), (8, -1), (4, 7), (12, 7), (-4, 7), (0, 15), (8, 15)]
    leg = {'l': G['hi'], 'm': G['lt'], 'b': G['base'], 'd': G['mid']}
    for (sx, sy) in spots:
        off = sway if (sy // 8) % 2 == 0 else -sway
        for j, row in enumerate(tuft):
            for i, ch in enumerate(row):
                if ch == '.':
                    continue
                xx = sx + i - 3 + 3 + (off if j < 3 else 0)
                yy = sy + j - 3 + 3
                if 0 <= yy < h:
                    img.p[yy][xx % w] = leg[ch]
    return img


def tallgrass_top(G, frame=0, w=16, h=16, sway=0):
    """The blade tips that cover a person standing in tall grass: lower
    half only, transparent elsewhere (draw above people)."""
    full = tallgrass(G, frame, sway=sway)
    img = Img(w, h)
    for y in range(9, h):
        for x in range(w):
            c = full.p[y][x]
            if c in (G['hi'], G['lt'], G['base']):
                img.p[y][x] = c
            elif c == G['mid'] and y >= 11:
                img.p[y][x] = c
    return img


FLOWER = {
    'daisy': """
    .pp.
    pccp
    pccd
    .dd.
    """,
    'tulip': """
    p.p.
    pppp
    dppd
    .dd.
    """,
    'bell': """
    .pp.
    pppp
    pdpd
    """,
    'star': """
    .p..
    ppcp
    .dp.
    .d.d
    """,
}


def flower_patch(ground, petal, petal_dk, center, stem, frame=0, seed=0, kind='daisy', n=3):
    """Ground tile with n flowers (4x4 heads) that sway one px between
    frames. Heads stay inside the cell so patches tile in any mix."""
    img = ground.copy()
    spots = [[(2, 2), (9, 5), (4, 10)], [(8, 1), (2, 7), (10, 10)], [(3, 3), (10, 3), (6, 10)]]
    pts = spots[seed % 3][:n]
    shape = FLOWER[kind]
    for i, (x, y) in enumerate(pts):
        dx = 1 if (frame + i) % 2 and x < 11 else 0
        img.set(x + 1, y + 4, stem)
        img.set(x + 2, y + 4, stem)
        img.set(x + 1, y + 5, stem)
        img.set(x, y + 5, stem)
        stamp(img, x + dx, y, shape, {'p': petal, 'c': center, 'd': petal_dk})
    return img


def reeds(R, w=16, h=24, seed=0, n=5, heads=None, frame=0):
    """Reed/cattail clump (transparent object). R: dark -> light (>= 3)."""
    img = Img(w, h)
    for i in range(n):
        x = 2 + int((i + 0.5) / n * (w - 4)) + (hash32(i, seed) % 3) - 1
        top = 2 + hash32(i, seed, 1) % 7
        lean = (hash32(i, seed, 2) % 3) - 1
        sw = (frame + i) % 2 if frame is not None else 0
        for y in range(top, h - 1):
            t = (y - top) / (h - top)
            xx = x + int(round(lean * (1 - t) * 2)) + (sw if y < top + 4 else 0)
            img.set(xx, y, R[1] if (y + i) % 3 else R[2])
            if y > h - 7:
                img.set(xx - 1, y, R[0])
        if heads:
            hx = x + lean * 2 + sw
            for y in range(top, top + 4):
                img.set(hx, y, heads[1])
                img.set(hx + 1, y, heads[0])
            img.set(hx, top, heads[2] if len(heads) > 2 else heads[1])
    return img


def lily_pad(leaf, leaf_out, flower=None, seed=0):
    img = Img(16, 16)
    pads = [(5, 6, 4, 3), (11, 11, 3.5, 2.6)]
    for (x, y, rx, ry) in pads:
        img.ellipse(x, y, rx, ry, leaf[1])
        img.ellipse(x - 0.8, y - 0.6, rx - 1.2, ry - 1, leaf[2])
        # notch
        img.set(int(x), int(y), None)
        img.set(int(x + 1), int(y - 1), None)
    img = img.outline(leaf_out)
    if flower:
        img.set(4, 5, flower[0])
        img.set(5, 5, flower[0])
        img.set(4, 4, flower[1])
        img.set(5, 6, flower[1])
    return img


def mushrooms(cap, cap_dk, spot, stem, out, seed=0, n=3):
    img = Img(16, 16)
    pts = [(3, 9), (8, 6), (11, 10)][:n]
    for i, (x, y) in enumerate(pts):
        s = 1 if i == 1 else 0
        img.rect(x + 1, y + 2, x + 1, y + 4 + s, stem)
        img.rect(x - 1 - s, y, x + 3 + s, y + 1, cap)
        img.rect(x - s, y - 1, x + 2 + s, y - 1, cap)
        img.set(x + 2 + s, y + 1, cap_dk)
        img.set(x + 3 + s, y + 1, cap_dk)
        img.set(x, y, spot)
        if s:
            img.set(x + 2, y - 1, spot)
    return img.outline(out)


def log_h(bark, bark_out, cut, cut_dk, w=32, h=16, moss=None):
    """Fallen log lying east-west."""
    img = Img(w, h)
    y0, y1 = 5, 12
    for y in range(y0, y1 + 1):
        t = (y - y0) / (y1 - y0)
        k = 3 if t < 0.2 else (2 if t < 0.5 else (1 if t < 0.8 else 0))
        k = min(len(bark) - 1, k)
        for x in range(2, w - 4):
            img.set(x, y, bark[k])
            if (x * 5 + y * 3) % 13 == 0 and 0.2 < t < 0.8:
                img.set(x, y, bark[max(0, k - 1)])
    # cut end (east)
    img.ellipse(w - 4.5, (y0 + y1) / 2 + 0.5, 3, 4, cut)
    img.set(w - 5, (y0 + y1) // 2, cut_dk)
    img.set(w - 4, (y0 + y1) // 2 + 1, cut_dk)
    img.set(w - 5, (y0 + y1) // 2 + 1, cut_dk)
    if moss:
        for x in range(4, w - 8, 3):
            img.set(x, y0, moss[1])
            img.set(x + 1, y0, moss[0])
            img.set(x + 1, y0 - 1, moss[1])
    return img.outline(bark_out)


def stump(bark, bark_out, cut, cut_dk, rings=None):
    img = Img(16, 16)
    for y in range(7, 14):
        for x in range(3, 13):
            u = (x - 3) / 9
            k = 2 if u < 0.3 else (1 if u < 0.75 else 0)
            img.set(x, y, bark[k])
    for dx in (2, 13):
        img.set(dx, 13, bark[0])
    img.ellipse(8, 7, 5, 2.6, cut)
    img.ellipse(8, 7, 3, 1.4, cut_dk)
    img.ellipse(8, 7, 1.5, 0.7, cut)
    return img.outline(bark_out)
