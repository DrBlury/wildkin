"""Terrain painters: ground families, autotiled materials, water, cliffs,
ledges, stairs. All return Imgs of role names (see paint.py for style)."""

import math

from core import Img, rnd, hash32, bayer, value_noise, fbm, worley, jitter_points
from paint import (autotile_block, scatter, stamp, grass, speckle_ground, CELL,
                   clump_crown)


# ---------------------------------------------------------------------------
# generic autotiles over a base ground
# ---------------------------------------------------------------------------

def wobble(seed, amp=0.9, freq=0.9):
    def w(t):
        return (math.sin(t * freq + seed) * 0.6 + math.sin(t * freq * 2.3 + seed * 1.7) * 0.4) * amp
    return w


def material_autotile(inner, outer, rim_in=None, rim_out=None, lip=None, E=4.0, R=4.5, Rn=2.5,
                      seed=0, amp=0.8, dither=0.9, inner_alt=None):
    """A material (path, sand, mud...) autotiled over a base ground.

    inner/outer: 16x16 Imgs sampled at cell coordinates.
    rim_out: role for the outer band (e.g. grass overhang shadow) -1..0
    rim_in:  role just inside on the N/W (shadowed) sides 0..1
    lip:     role just inside on the S/E (lit) sides 0..1"""
    wob = wobble(seed, amp)

    def color_at(d, X, Y, side, v, alt):
        if d < -1.0:
            return outer.p[Y][X]
        if d < 0.0:
            return rim_out if rim_out else outer.p[Y][X]
        if d < 1.0:
            lit = ('S' in side or 'E' in side) and 'N' not in side and 'W' not in side
            if lit and lip:
                return lip
            if rim_in:
                return rim_in
        src = inner_alt if (alt and inner_alt is not None) else inner
        return src.p[Y][X]
    return autotile_block(color_at, E=E, R=R, Rn=Rn, wob=wob, dither=dither)


# ---------------------------------------------------------------------------
# water
# ---------------------------------------------------------------------------

def water_surface(W, frame, seed=0, w=CELL, h=CELL, calm=False, density=1.0):
    """Open water: flat base with horizontal ripple strokes (light top, dark
    underline) that drift and breathe over 4 frames. Tiles at 16 px.
    W = {'deep','base','lt','hi','foam'}."""
    img = Img(w, h, W['base'])
    strokes = [(1, 1, 5), (10, 3, 4), (5, 6, 3), (13, 8, 4), (2, 10, 4), (8, 13, 5), (14, 14, 2)]
    if density < 1.0:
        strokes = strokes[::2]
    for i, (sx, sy, ln) in enumerate(strokes):
        ph = (frame + i * 3) % 4
        L = ln + (1 if ph == 1 else (-1 if ph == 3 else 0))
        x0 = (sx + (frame if i % 2 else -frame) + seed) % w
        for k in range(L):
            img.p[sy][(x0 + k) % w] = W['lt']
            if k and k < L - 1:
                img.p[(sy + 1) % h][(x0 + k) % w] = W['deep']
        if ph == 1 and not calm:
            img.p[sy][(x0 + 1) % w] = W['hi']
    return img


def water_autotile(W, ground, frame, edge=None, seed=0, E=4.0, R=5.0, Rn=2.5, wet=None):
    """Pond/lake over a ground tile. edge: role of the dark bank line.
    wet: optional role for a damp band on the ground side."""
    surf = water_surface(W, frame, seed)
    wob = wobble(seed + 3, 0.7)

    def color_at(d, X, Y, side, v, alt):
        if d < -1.6:
            return ground.p[Y][X]
        if d < -0.6:
            return wet if wet else ground.p[Y][X]
        if d < 0.35:
            return edge if edge else W['deep']
        # foam line that breathes with the frame
        if d < 1.3:
            if ((X + Y + frame) & 3) == 0:
                return W['foam']
            return W['hi']
        if d < 2.6:
            return W['lt'] if bayer(X, Y) < (2.6 - d) / 1.3 else surf.p[Y][X]
        return surf.p[Y][X]
    return autotile_block(color_at, E=E, R=R, Rn=Rn, wob=wob, dither=0.6)


def waterfall(W, rock, frame, w=2, h=3, seed=0):
    """Falling water block (w x h cells) with a foam pool row at the bottom.
    W as water_surface, rock = dark -> light roles for the side lips."""
    img = Img(w * CELL, h * CELL, W['base'])
    ww, hh = img.w, img.h
    for y in range(hh - 10):
        for x in range(ww):
            band = (x * 7 + hash32(x, seed) % 5) % 6
            v = (y - frame * 4 + hash32(x, 3, seed) % 16) % 16
            if band in (0, 3) and v < 9:
                c = W['lt']
            elif band == 1 and v < 4:
                c = W['hi']
            elif band == 5 and v > 10:
                c = W['deep']
            else:
                c = W['base']
            img.p[y][x] = c
    # side lips (darker water sliding over the rock edge)
    for y in range(hh - 10):
        img.p[y][0] = W['deep']
        img.p[y][ww - 1] = W['deep']
    # plunge foam
    for y in range(hh - 10, hh):
        for x in range(ww):
            t = (y - (hh - 10)) / 10.0
            n = rnd(x // 2, (y + frame) // 2, seed + frame)
            if t < 0.5 or n < 0.55 - t * 0.4:
                img.p[y][x] = W['foam'] if (x + y + frame) % 3 else W['hi']
            else:
                img.p[y][x] = W['lt'] if n < 0.8 else W['base']
    return img


# ---------------------------------------------------------------------------
# cliffs: plateau rim autotile + face nine-slice
# ---------------------------------------------------------------------------

def cliff_rim(top, low, rock, outline, face_tex=None, E=4.0, R=4.0, Rn=2.0, seed=0, bevel=None,
              drip=None):
    """Autotile for the upper level of a plateau (rmxp16).

    top/low: 16x16 ground Imgs (upper, lower level). rock: dark -> light
    roles (>= 5). face_tex: the 32x32 face texture shared with cliff_face so
    the south lip flows into the face below. N shows a thin rock rim, W/E a
    narrow band of the face texture; drip = grass role hanging over the lip."""
    wob = wobble(seed, 0.5, 1.2)
    ft = face_tex

    def color_at(d, X, Y, side, v, alt):
        south = 'S' in side
        north = 'N' in side
        west = 'W' in side
        if d >= 1.0:
            return top.p[Y][X]
        if d >= 0.0:
            if south:
                return bevel or top.p[Y][X]
            return bevel or top.p[Y][X]
        if south:
            if d > -1.0:
                # grass overhang: tufts hang over the face
                return drip if (drip and (X * 5 + seed) % 7 < 4) else rock[-1]
            if d > -2.0:
                return drip if (drip and (X * 5 + seed) % 7 < 2) else rock[-2]
            if ft is not None:
                return ft.p[(Y + 16) % ft.h][X % ft.w]
            return rock[1]
        if north:
            if d > -1.0:
                return rock[-2]
            if d > -2.2:
                return rock[1]
            if d > -3.2:
                return outline
            return low.p[Y][X]
        # west / east bands
        if d > -1.0:
            return rock[-1] if west else rock[1]
        if d > -3.2:
            if ft is not None:
                c = ft.p[(Y + 8) % ft.h][(X + 7) % ft.w]
                return c
            return rock[2]
        return outline
    return autotile_block(color_at, E=E, R=R, Rn=Rn, wob=wob, dither=0.0)


def rock_face(rock, outline, w, h, seed, slab=5.0, strata=False, wrap=True):
    """Rock texture for cliff faces: vertical slabs lit from the left, dark
    crevices, lighter slab tops. rock: dark -> light (>= 4 roles)."""
    n = len(rock)
    img = Img(w, h)
    if strata:
        pts = jitter_points(w, h, slab, seed, jitter=0.9)
        pts = [(x, y) for (x, y) in pts]
        sx, sy = 0.55, 1.6
    else:
        pts = jitter_points(w, h, slab, seed, jitter=0.9)
        sx, sy = 1.35, 0.6
    for y in range(h):
        for x in range(w):
            best, sec, bi = 1e9, 1e9, -1
            for i, (px, py) in enumerate(pts):
                dx, dy = x + 0.5 - px, y + 0.5 - py
                if wrap:
                    dx = (dx + w / 2) % w - w / 2
                    dy = (dy + h / 2) % h - h / 2
                d = math.hypot(dx * sx, dy * sy)
                if d < best:
                    sec, best, bi = best, d, i
                elif d < sec:
                    sec = d
            px, py = pts[bi]
            dx = x + 0.5 - px
            if wrap:
                dx = (dx + w / 2) % w - w / 2
            dy = y + 0.5 - py
            if wrap:
                dy = (dy + h / 2) % h - h / 2
            # slab is a rounded column: lit on its left, shadowed right/bottom
            lum = 0.55 - dx * 0.09 - dy * 0.03 + (rnd(bi, seed) - 0.5) * 0.25
            t = lum * (n - 1) + (bayer(x, y) - 0.5) * 0.6
            k = max(1, min(n - 1, int(round(t))))
            if sec - best < 1.0:
                k = 0
            elif sec - best < 1.8 and dy < 0:
                k = min(n - 1, k + 1)       # lit slab top edge
            img.p[y][x] = rock[k]
    return img


def cliff_face(rock, outline, low, seed=0, tufts=None, strata=False, tex=None, tex2=None):
    """patch9 block (80x48) for the cliff face below a plateau.

    Row 0 = face under the rim, row 1 = middle (repeat for tall cliffs),
    row 2 = foot meeting the lower ground. Col 0/2 = rounded ends (lower
    ground beyond), col 1 = repeating face. Cols 3-4 rows 0-1: ends where the
    face tucks against more plateau (concave corners); row 2 cols 3-4:
    alternative middle / single-column face."""
    tex = tex or lump_texture(rock, 32, 32, seed)
    tex2 = tex2 or lump_texture(rock, 32, 32, seed + 50)
    img = Img(80, 48)

    def put(col, row, end=None, alt=False, tuck=False):
        t = tex2 if alt else tex
        for y in range(16):
            for x in range(16):
                X, Y = col * 16 + x, row * 16 + y
                ty = (row * 16 + y) % 32
                c = t.p[ty][x + (16 if alt else 0)]
                # the foot: bottom 4 px sink into the lower ground
                if row == 2:
                    foot = 12 + (hash32(x, seed, 9) % 2)
                    if y >= foot + 1:
                        c = low.p[y][x]
                    elif y == foot:
                        c = outline
                    elif y == foot - 1:
                        c = rock[0] if x % 3 else rock[1]
                # rounded ends
                if end is not None:
                    lx = x if end == 'W' else 15 - x
                    if row == 0:
                        yy = y
                    else:
                        yy = 16 + y
                    # the end bulges out: an eased curve
                    edge = 3.0 + 1.5 * math.sin(yy / 32.0 * math.pi)
                    if tuck:
                        edge = 1.0
                    if lx < edge - 1:
                        c = low.p[y][x] if not tuck else rock[0]
                        if tuck:
                            c = outline
                    elif lx < edge:
                        c = outline
                    elif lx < edge + 1.5:
                        c = rock[-1] if end == 'W' else rock[0]
                img.p[Y][X] = c
    for row in range(3):
        put(0, row, 'W')
        put(1, row)
        put(2, row, 'E')
    put(3, 0, 'W', tuck=True)
    put(4, 0, 'E', tuck=True)
    put(3, 1, 'W', tuck=True)
    put(4, 1, 'E', tuck=True)
    put(3, 2, alt=True)
    put(4, 2, alt=True)
    if tufts:
        # grass clumps growing at the foot of the face
        for (col, row) in ((0, 2), (1, 2), (2, 2), (3, 2), (4, 2)):
            for i, (x, y) in enumerate(scatter(14, 4, 2, seed + col * 7, margin=1, min_dist=5)):
                stamp(img, col * 16 + x, row * 16 + 10 + y, '''
                l.l
                dld
                ''', {'l': tufts[1], 'd': tufts[0]})
    return img


def ledge_block(ground, profile, R=None):
    """One-way ledges (hop down). profile: roles from the grass lip outward,
    e.g. [highlight, grass, rock light, rock dark, outline, shadow].
    64x48 custom block:
      row 0: south-facing [W end][middle][E end][single]
      row 1: east-facing  [N end][middle][S end][SE corner]
      row 2: west-facing  [N end][middle][S end][SW corner]"""
    img = Img(64, 48)
    for row in range(3):
        for col in range(4):
            img.paste(ground, col * 16, row * 16)
    n = len(profile)
    start = 16 - n - 1

    def band(ox, oy, orient, a0=None, a1=None, lo=0, hi=15):
        # orient 'S': bands are rows; 'E'/'W': columns. ends taper by 1 px/px
        for t in range(lo, hi + 1):
            inset = 0
            if a0 is not None and t - lo < 3:
                inset = 3 - (t - lo)
            if a1 is not None and hi - t < 3:
                inset = max(inset, 3 - (hi - t))
            for k, role in enumerate(profile):
                q = start + k + inset
                if q > 15:
                    continue
                if orient == 'S':
                    img.set(ox + t, oy + q, role)
                elif orient == 'E':
                    img.set(ox + q, oy + t, role)
                else:
                    img.set(ox + 15 - q, oy + t, role)
    band(0, 0, 'S', a0=True)
    band(16, 0, 'S')
    band(32, 0, 'S', a1=True)
    band(48, 0, 'S', a0=True, a1=True)
    band(0, 16, 'E', a0=True)
    band(16, 16, 'E')
    band(32, 16, 'E', a1=True)
    band(0, 32, 'W', a0=True)
    band(16, 32, 'W')
    band(32, 32, 'W', a1=True)
    # corners: the south ledge turns north along the east / west side
    band(48, 16, 'S', lo=0, hi=start + n - 1)
    band(48, 16, 'E', lo=0, hi=start + n - 1)
    band(48, 32, 'S', lo=16 - start - n, hi=15)
    band(48, 32, 'W', lo=0, hi=start + n - 1)
    return img


def stairs(step_hi, step, riser, outline, side, w=1, h=2, ground=None):
    """Stone/earth steps cut into a cliff face: w x h cells, steps every 4 px."""
    img = Img(w * 16, h * 16)
    W, H = img.w, img.h
    for y in range(H):
        for x in range(W):
            k = y % 4
            if x in (0, W - 1):
                c = outline
            elif x in (1, W - 2):
                c = side
            else:
                c = step_hi if k == 0 else (step if k in (1, 2) else riser)
            img.p[y][x] = c
    # worn centre
    for y in range(0, H, 4):
        for x in range(4, W - 4):
            if (x + y // 4) % 5 == 0:
                img.set(x, y + 1, step_hi)
    return img


def lump_texture(rock, w, h, seed, rx=4.6, ry=3.6, sx=7.0, sy=5.5, jit=1.2, gap=None, dither=0.45, bias=-0.18):
    """Seamless (w x h) texture of rounded rock lumps in staggered rows,
    lit from the upper left with dark gaps: GBA-style cliff faces, walls of
    boulders, scree. rock: dark -> light roles."""
    cl = []
    rows = max(1, int(round(h / sy)))
    cols = max(1, int(round(w / sx)))
    for j in range(rows):
        for i in range(cols):
            x = (i + 0.5 * (j & 1) + (rnd(i, j, seed) - 0.5) * 0.4) * w / cols
            y = (j + 0.5 + (rnd(i, j, seed + 3) - 0.5) * 0.3) * h / rows
            r = rx * (0.85 + rnd(i, j, seed + 5) * 0.35)
            q = ry * (0.85 + rnd(i, j, seed + 6) * 0.3)
            cl.append((x, y, r, q))
    return clump_crown(w, h, cl, rock, None, seed=seed, wrap=True, speck=False,
                       fill=gap or rock[0], rim=1.1, bias=bias, dither=dither)


def cobbles(stone, mortar, w=16, h=16, seed=0, rx=3.2, ry=2.6, sx=4.6, sy=4.0):
    """Seamless rounded cobblestones with mortar gaps."""
    return lump_texture(stone, w, h, seed, rx=rx, ry=ry, sx=sx, sy=sy, gap=mortar, bias=0.05, dither=0.25)


def bricks(B, w=16, h=16, bw=8, bh=4, herring=False):
    """Paving bricks: B = [mortar, dark, base, light]."""
    img = Img(w, h, B[2])
    for y in range(h):
        for x in range(w):
            row = y // bh
            off = (row % 2) * (bw // 2)
            k = y % bh
            if k == bh - 1 or (x + off) % bw == bw - 1:
                img.p[y][x] = B[0]
            elif k == 0:
                img.p[y][x] = B[3]
            elif (x + off) % bw == bw - 2 or k == bh - 2:
                img.p[y][x] = B[1]
            if hash32(x // bw, row, 5) % 5 == 0 and img.p[y][x] == B[2]:
                img.p[y][x] = B[1] if (x + y) % 2 else B[2]
    return img


def flagstones(S, w=16, h=16, seed=0):
    """Large irregular slabs: S = [gap, dark, base, light]."""
    from core import jitter_points, worley
    pts = jitter_points(w, h, 6.5, seed)
    img = Img(w, h)
    for y in range(h):
        for x in range(w):
            i, d1, d2 = worley(x + 0.5, y + 0.5, pts, wrap=(w, h))
            if d2 - d1 < 1.0:
                img.p[y][x] = S[0]
            else:
                # each slab: lit top-left edge
                i2, e1, e2 = worley(x - 0.5, y - 0.5, pts, wrap=(w, h))
                if i2 != i:
                    img.p[y][x] = S[3]
                else:
                    img.p[y][x] = S[2] if hash32(i, seed) % 3 else S[1]
    return img


def cliff_face_single(rock, outline, low, tex, tufts=None, seed=0):
    """One-row face for a single level of drop (docs/ELEVATION.md draws one
    face row per level): 64x16 [W end][middle][E end][lone column]. The top
    of the row continues the rim's lip, the bottom 4 px are the foot."""
    img = Img(64, 16)
    for col, (west, east) in enumerate(((True, False), (False, False), (False, True), (True, True))):
        for y in range(16):
            for x in range(16):
                c = tex.p[y % tex.h][x % tex.w]
                foot = 12 + (hash32(x, seed, 9) % 2)
                if y >= foot + 1:
                    c = low.p[y][x]
                elif y == foot:
                    c = outline
                elif y == foot - 1:
                    c = rock[0] if x % 3 else rock[1]
                for (on, lx) in ((west, x), (east, 15 - x)):
                    if not on:
                        continue
                    edge = 3.0 + 1.2 * math.sin(y / 16.0 * math.pi)
                    if lx < edge - 1:
                        c = low.p[y][x]
                    elif lx < edge:
                        c = outline
                    elif lx < edge + 1.5 and y < foot:
                        c = rock[-1] if lx == x else rock[0]
                img.p[y][col * 16 + x] = c
        if tufts:
            for i, (x, y) in enumerate(scatter(14, 3, 1, seed + col, margin=1, min_dist=5)):
                stamp(img, col * 16 + x, 11 + y, '''
                l.l
                dld
                ''', {'l': tufts[1], 'd': tufts[0]})
    return img
