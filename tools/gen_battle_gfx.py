#!/usr/bin/env python3
"""Generate src/gfx_battle.h: bag item icons, the thrown lantern OBJ frames,
move-effect particles, move-menu labels and five full-screen battle
backgrounds (meadow, forest, lake, ring, storm).

Everything is painted procedurally (shapes + quantised lighting from the
top-left), then packed into GBA 4bpp tiles. Standard library only.

    python3 tools/gen_battle_gfx.py                 # writes src/gfx_battle.h
    python3 tools/gen_battle_gfx.py --preview DIR   # also writes preview PNGs
"""

import math
import os
import struct
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_H = os.path.join(ROOT, "src", "gfx_battle.h")

# --------------------------------------------------------------------------
# colours: everything is kept as 5-bit (r, g, b) tuples
# --------------------------------------------------------------------------


def C(r, g, b):
    """8-bit RGB -> 5-bit tuple."""
    return (r >> 3, g >> 3, b >> 3)


WHITE = (31, 31, 31)


def rgb15(c):
    return c[0] | (c[1] << 5) | (c[2] << 10)


def to8(c):
    return tuple((v << 3) | (v >> 2) for v in c)


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# --------------------------------------------------------------------------
# PNG output (previews)
# --------------------------------------------------------------------------


def write_png(path, rows):
    """rows: list of rows of 8-bit (r, g, b)."""
    h = len(rows)
    w = len(rows[0])
    raw = bytearray()
    for row in rows:
        raw.append(0)
        for px in row:
            raw.extend(px)

    def chunk(t, d):
        return (struct.pack(">I", len(d)) + t + d
                + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF))

    data = (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)


class Sheet:
    """RGB preview composer (8-bit)."""

    def __init__(self, w, h, bg=(255, 255, 255)):
        self.w, self.h = w, h
        self.rows = [[bg] * w for _ in range(h)]

    def rect(self, x, y, w, h, col):
        for yy in range(max(0, y), min(self.h, y + h)):
            for xx in range(max(0, x), min(self.w, x + w)):
                self.rows[yy][xx] = col

    def blit(self, img, x, y, scale, pal=None, frame=None):
        """img: 2D list of 5-bit colours / None, or of indices with pal."""
        for yy, row in enumerate(img):
            for xx, v in enumerate(row):
                if pal is not None:
                    if v == 0:
                        continue
                    col = to8(pal[v])
                else:
                    if v is None:
                        continue
                    col = to8(v)
                self.rect(x + xx * scale, y + yy * scale, scale, scale, col)

    def save(self, path):
        write_png(path, self.rows)


# --------------------------------------------------------------------------
# canvas helpers
# --------------------------------------------------------------------------


class Canvas:
    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.p = [[fill] * w for _ in range(h)]

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.p[y][x]
        return None

    def set(self, x, y, v):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = v

    def copy(self):
        c = Canvas(self.w, self.h)
        c.p = [row[:] for row in self.p]
        return c


def outline(cv, col, diag=False, skip=()):
    """Grow a 1px border of `col` around every opaque pixel."""
    add = []
    for y in range(cv.h):
        for x in range(cv.w):
            if cv.p[y][x] is not None:
                continue
            nb = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
            if diag:
                nb += [(x - 1, y - 1), (x + 1, y - 1), (x - 1, y + 1), (x + 1, y + 1)]
            for nx, ny in nb:
                v = cv.get(nx, ny)
                if v is not None and v != col and v not in skip:
                    add.append((x, y))
                    break
    for x, y in add:
        cv.p[y][x] = col


LIGHT = (-0.52, -0.68, 0.52)
_ll = math.sqrt(sum(v * v for v in LIGHT))
LIGHT = tuple(v / _ll for v in LIGHT)


def sphere_b(nx, ny, light=LIGHT):
    nz = math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny))
    return nx * light[0] + ny * light[1] + nz * light[2]


def quant(b, th):
    """Quantise brightness b with ascending thresholds -> level index."""
    lv = 0
    for t in th:
        if b >= t:
            lv += 1
    return lv


def rows_extent(mask):
    ext = {}
    for (x, y) in mask:
        a = ext.get(y)
        if a is None:
            ext[y] = [x, x]
        else:
            a[0] = min(a[0], x)
            a[1] = max(a[1], x)
    return ext


def lathe_levels(mask, th=(0.12, 0.45, 0.78), light_x=-0.55):
    """Cylinder shading for a mask (set of (x,y)), light from the left."""
    ext = rows_extent(mask)
    out = {}
    for (x, y) in mask:
        x0, x1 = ext[y]
        w = x1 - x0 + 1
        n = ((x - x0 + 0.5) / w) * 2 - 1
        nz = math.sqrt(max(0, 1 - n * n))
        b = n * light_x + nz * 0.83
        out[(x, y)] = quant(b, th)
    return out


def ellipse_mask(cx, cy, rx, ry):
    m = set()
    for y in range(int(cy - ry - 1), int(cy + ry + 2)):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                m.add((x, y))
    return m


def rect_mask(x0, y0, x1, y1, r=0):
    """Inclusive rect with optional rounded corners of radius r (pixels)."""
    m = set()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if r:
                cx = min(max(x, x0 + r), x1 - r)
                cy = min(max(y, y0 + r), y1 - r)
                dx = x - cx
                dy = y - cy
                if dx * dx + dy * dy > r * r + 0.3 * r:
                    continue
            m.add((x, y))
    return m


def poly_mask(pts, w=64, h=64):
    """Pixels whose centre is inside polygon pts."""
    m = set()
    n = len(pts)
    for y in range(h):
        py = y + 0.5
        for x in range(w):
            px = x + 0.5
            ins = False
            j = n - 1
            for i in range(n):
                xi, yi = pts[i]
                xj, yj = pts[j]
                if (yi > py) != (yj > py):
                    xint = xi + (py - yi) * (xj - xi) / (yj - yi)
                    if px < xint:
                        ins = not ins
                j = i
            if ins:
                m.add((x, y))
    return m


def line_pts(x0, y0, x1, y1):
    pts = []
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return pts


def paint_levels(cv, levels, ramp):
    for (x, y), lv in levels.items():
        cv.set(x, y, ramp[min(lv, len(ramp) - 1)])


def ramp(*cols):
    return [C(*c) for c in cols]


# --------------------------------------------------------------------------
# tile packing
# --------------------------------------------------------------------------


def tiles_from_indices(img, tw, th):
    """img: 2D list of palette indices -> list of tiles (8 u32 each)."""
    out = []
    for ty in range(th):
        for tx in range(tw):
            t = []
            for r in range(8):
                v = 0
                for c in range(8):
                    v |= (img[ty * 8 + r][tx * 8 + c] & 15) << (4 * c)
                t.append(v)
            out.append(t)
    return out


def index_image(cv, pal_fixed=None, force_white1=True, max_colors=16):
    """Canvas of 5-bit colours -> (index image, palette of 16)."""
    pal = [(0, 0, 0), WHITE] if force_white1 else [(0, 0, 0)]
    if pal_fixed:
        for c in pal_fixed:
            if c not in pal:
                pal.append(c)
    for y in range(cv.h):
        for x in range(cv.w):
            v = cv.p[y][x]
            if v is not None and v not in pal:
                pal.append(v)
    if len(pal) > max_colors:
        raise SystemExit("too many colours: %d" % len(pal))
    img = [[0 if cv.p[y][x] is None else pal.index(cv.p[y][x])
            for x in range(cv.w)] for y in range(cv.h)]
    while len(pal) < 16:
        pal.append((0, 0, 0))
    return img, pal


# ==========================================================================
# 1. item icons (24x24, own palette each, index 1 = white)
# ==========================================================================


def rotated_render(w, h, cx, cy, ang, fn, ss=3):
    """Render fn(u, v) -> colour/None in a frame rotated by ang (radians),
    super-sampling each pixel and picking the most common result."""
    ca, sa = math.cos(ang), math.sin(ang)
    cv = Canvas(w, h)
    for y in range(h):
        for x in range(w):
            votes = {}
            for sy in range(ss):
                for sx in range(ss):
                    px = x + (sx + 0.5) / ss - cx
                    py = y + (sy + 0.5) / ss - cy
                    u = px * ca + py * sa
                    v = -px * sa + py * ca
                    r = fn(u, v)
                    votes[r] = votes.get(r, 0) + 1
            best = max(votes.items(), key=lambda kv: kv[1])
            # need majority of samples inside to be opaque
            inside = ss * ss - votes.get(None, 0)
            if inside * 2 <= ss * ss:
                continue
            if best[0] is None:
                best = max(((k, n) for k, n in votes.items() if k is not None),
                           key=lambda kv: kv[1])
            cv.set(x, y, best[0])
    return cv


# --------------------------------------------------------------------------
# WILDKIN supplies (docs/WORLD.md section 8)
# --------------------------------------------------------------------------

def icon_tonic(level):
    """Corked flask of glowing luciferin tonic; brighter with each grade."""
    LIQ = [ramp((24, 112, 104), (48, 176, 150), (120, 232, 196), (216, 255, 236)),
           ramp((112, 152, 16), (176, 216, 40), (232, 248, 112), (255, 255, 216)),
           ramp((216, 120, 16), (255, 192, 48), (255, 236, 144), (255, 255, 240))][level]
    HALO = [None, C(236, 248, 168), C(255, 236, 150)][level]
    outc = [C(16, 64, 64), C(64, 80, 16), C(112, 56, 8)][level]
    glass = ramp((168, 196, 212), (224, 236, 244))
    cork = ramp((136, 88, 48), (184, 128, 72))
    cv = Canvas(24, 24)
    cx, cy, rx, ry = 11.5, 15.2, 6.8, 6.4
    body = ellipse_mask(cx, cy, rx, ry)
    for (x, y) in body:
        nx, ny = (x + 0.5 - cx) / (rx + 0.4), (y + 0.5 - cy) / (ry + 0.4)
        if y >= 12:
            # glows from the inside: brightest at the centre
            b = 1.0 - math.hypot(nx * 1.05, ny * 1.1)
            cv.set(x, y, LIQ[quant(b, (0.12, 0.42, 0.72))])
        else:
            cv.set(x, y, glass[1] if nx < 0.1 else glass[0])
    for (x, y) in body:
        if y == 12:
            cv.set(x, y, LIQ[3] if x < 14 else LIQ[2])
    paint_levels(cv, lathe_levels(rect_mask(10, 6, 13, 9), th=(0.2, 0.7, 5)), glass)
    paint_levels(cv, lathe_levels(rect_mask(9, 2, 14, 5, r=1), th=(0.1, 0.6, 5)), cork)
    for x in range(10, 14):
        cv.set(x, 5, cork[0])
    for (x, y) in [(7, 11), (6, 12), (6, 14), (6, 15), (6, 16)]:
        cv.set(x, y, WHITE)
    cv.set(11, 7, WHITE)
    outline(cv, outc)
    if HALO is not None:
        # soft light around the flask
        pts = []
        for y in range(24):
            for x in range(24):
                if cv.get(x, y) is None:
                    d = math.hypot(x + 0.5 - cx, (y + 0.5 - cy) * 1.05)
                    if (level == 1 and 8.3 <= d <= 9.1 and (x + y) % 2 == 0) or \
                       (level == 2 and 8.2 <= d <= 9.4 and (x + y) % 2 == 0):
                        pts.append((x, y))
        for (x, y) in pts:
            cv.set(x, y, HALO)
    if level == 2:
        for (x, y) in [(3, 5), (2, 6), (3, 6), (4, 6), (3, 7), (19, 3), (20, 4), (19, 4), (18, 4), (19, 5),
                       (20, 9), (21, 9)]:
            cv.set(x, y, WHITE if (x, y) in ((3, 6), (19, 4)) else HALO)
    return cv


def icon_tuning_fork():
    M = ramp((104, 112, 136), (160, 168, 192), (216, 220, 236), (255, 255, 255))
    arc = C(96, 176, 240)
    outc = C(40, 44, 64)
    cv = Canvas(24, 24)

    def fn(u, v):
        # fork drawn upright in a rotated frame
        if -9.5 <= v <= 1.5 and 2.0 <= abs(u) <= 3.6:
            return M[2] if u < 0 else M[1]
        if 1.5 < v <= 4.0 and abs(u) <= 3.6 and math.hypot(u, v - 1.5) <= 3.6:
            return M[1] if u > 0.8 else M[2]
        if 3.5 < v <= 8.2 and abs(u) <= 0.9:
            return M[2] if u < 0 else M[1]
        if math.hypot(u, v - 9.4) <= 1.9:
            return M[3] if u + v - 9.4 < -0.8 else M[1]
        return None
    cv = rotated_render(24, 24, 11.0, 12.0, math.radians(-28), fn)
    outline(cv, outc)
    for (a0, r) in [(0, 3.0), (0, 5.2)]:
        for k in range(-5, 6):
            ang = math.radians(-40 + k * 7)
            x = int(round(17.0 + r * math.cos(ang)))
            y = int(round(6.5 + r * math.sin(ang)))
            if cv.get(x, y) is None:
                cv.set(x, y, arc)
    return cv


def icon_igniter():
    R = ramp((152, 40, 24), (216, 72, 40), (248, 128, 80), (255, 192, 152))
    G = ramp((88, 96, 112), (152, 160, 176), (216, 220, 232))
    Y = ramp((248, 184, 32), (255, 240, 136))
    outc = C(56, 20, 16)
    cv = Canvas(24, 24)
    paint_levels(cv, lathe_levels(rect_mask(7, 10, 15, 21, r=2), th=(0.05, 0.42, 0.86)), R)
    paint_levels(cv, lathe_levels(rect_mask(9, 5, 13, 9, r=1), th=(0.1, 0.55, 5)), G)
    for x in range(8, 15):
        cv.set(x, 10, G[0])
    # thumb button and grip ridges
    for (x, y) in [(15, 13), (16, 13), (15, 14), (16, 14), (15, 15), (16, 15)]:
        cv.set(x, y, Y[0] if y > 13 else Y[1])
    for y in (16, 18):
        for x in range(9, 14):
            cv.set(x, y, R[0])
    cv.set(9, 12, WHITE)
    cv.set(9, 13, R[3])
    outline(cv, outc)
    # the spark at the tip
    for (x, y, c) in [(11, 1, Y[1]), (11, 2, WHITE), (10, 2, Y[1]), (12, 2, Y[1]), (11, 3, Y[1]),
                      (8, 2, Y[0]), (14, 2, Y[0]), (9, 0, Y[0]), (13, 0, Y[0])]:
        cv.set(x, y, c)
    return cv


def icon_honey():
    H = ramp((176, 96, 8), (232, 152, 24), (255, 200, 64), (255, 236, 160))
    outc = C(96, 48, 0)
    cv = Canvas(24, 24)
    cx, cy, R = 11.5, 14.6, 6.6

    def inside(px, py):
        if py >= cy:
            return math.hypot(px - cx, py - cy) <= R
        t = (cy - py) / (cy - 2.5)
        return t <= 1 and abs(px - cx) <= R * (1 - t) ** 0.8
    m = fn_mask(inside, 24, 24)
    for (x, y) in m:
        nx = (x + 0.5 - cx) / (R + 0.5)
        ny = (y + 0.5 - cy) / (R + 3.0)
        cv.set(x, y, H[quant(sphere_b(nx, max(-0.95, ny)), (-0.1, 0.42, 0.82))])
    # honeycomb glint
    for (x, y) in [(10, 14), (11, 13), (12, 13), (13, 14), (12, 15), (11, 15)]:
        cv.set(x, y, H[3])
    for (x, y) in [(8, 12), (8, 13), (9, 11)]:
        cv.set(x, y, WHITE)
    outline(cv, outc)
    return cv


def icon_sunseed():
    S = ramp((176, 88, 16), (232, 136, 32), (255, 192, 72), (255, 232, 152))
    ray = C(255, 224, 112)
    outc = C(96, 40, 8)

    def fn(u, v):
        if (u / 7.0) ** 2 + (v / 4.3) ** 2 <= 1.0:
            b = sphere_b(u / 7.4, v / 4.8)
            if abs(v) < 0.6 and abs(u) < 5.2:
                return S[3]
            return S[quant(b, (-0.05, 0.4, 0.8))]
        return None
    cv = rotated_render(24, 24, 11.5, 12.0, math.radians(-35), fn)
    outline(cv, outc)
    for k in range(8):
        a = k * math.pi / 4 + 0.3
        for r in (9.6, 10.6):
            x = int(round(11.5 + r * math.cos(a)))
            y = int(round(12.0 + r * math.sin(a)))
            if 0 <= x < 24 and 0 <= y < 24 and cv.get(x, y) is None:
                cv.set(x, y, ray)
    cv.set(9, 10, WHITE)
    return cv


def icon_shard(base, outc):
    """A cluster of three crystal slivers; base = 4-shade ramp."""
    cv = Canvas(24, 24)
    slivers = [   # (cx, bottom y, top y, half width, lean)
        (7.0, 20.5, 9.0, 2.6, -3.0), (16.8, 20.5, 8.2, 2.6, 3.2), (11.8, 21.5, 2.0, 3.4, 0.4)]
    for (cx, yb, yt, hw, lean) in slivers:
        pts = [(cx - hw, yb), (cx - hw + lean * 0.7, yt + 3.2), (cx + lean, yt),
               (cx + hw + lean * 0.7, yt + 3.2), (cx + hw, yb)]
        m = poly_mask(pts, 24, 24)
        for (x, y) in m:
            px = x + 0.5
            t = (yb - (y + 0.5)) / (yb - yt)
            axis = cx + lean * t
            if abs(px - axis) < 0.55:
                col = base[3]
            elif px < axis:
                col = base[2]
            else:
                col = base[1] if px < axis + hw * 0.6 else base[0]
            if y + 0.5 < yt + 3.4 and px < axis:
                col = base[3]
            cv.set(x, y, col)
    outline(cv, outc)
    for (x, y) in [(11, 5), (11, 6), (6, 12)]:
        cv.set(x, y, WHITE)
    return cv


def icon_coil(wire, outc, clip, emblem):
    """A clip-on coil spring seen from the side, a clip on one end."""
    cv = Canvas(24, 24)
    x0, x1, cy, ry = 5.0, 20.0, 12.5, 5.2
    turns = 4.5
    pts_back, pts_front = [], []
    n = 400
    for i in range(n + 1):
        th = i / n * turns * 2 * math.pi
        x = x0 + (x1 - x0) * i / n
        y = cy - ry * math.cos(th)
        (pts_front if math.sin(th) > 0 else pts_back).append((x, y))
    for layer, pts in ((0, pts_back), (1, pts_front)):
        for (x, y) in pts:
            for dy in (-0.6, 0.0, 0.6):
                px, py = int(x), int(y + dy)
                if 0 <= px < 24 and 0 <= py < 24:
                    if layer == 0:
                        if cv.get(px, py) is None:
                            cv.set(px, py, wire[0])
                    else:
                        cv.set(px, py, wire[3] if py < cy - 2 else wire[2] if py < cy + 2 else wire[1])
    paint_levels(cv, lathe_levels(rect_mask(1, 9, 4, 16, r=1), th=(0.1, 0.5, 5)), clip)
    outline(cv, outc)
    for (x, y, c) in emblem:
        cv.set(x, y, c)
    return cv


def icon_hush_bell():
    B = ramp((104, 88, 152), (152, 136, 200), (200, 192, 232), (240, 236, 255))
    rib = ramp((136, 40, 88), (200, 72, 128))
    hush = C(120, 152, 216)
    outc = C(40, 32, 72)
    cv = Canvas(24, 24)

    def inside(px, py):
        if 5.0 <= py <= 17.5:
            t = (py - 5.0) / 12.5
            hw = 3.2 + 3.6 * t ** 1.6
            return abs(px - 11.5) <= hw
        if 17.5 < py <= 19.4:
            return abs(px - 11.5) <= 7.6
        return False
    m = fn_mask(inside, 24, 24)
    lv = lathe_levels(m, th=(0.05, 0.42, 0.84))
    paint_levels(cv, lv, B)
    for x in range(4, 20):
        if cv.get(x, 17) is not None:
            cv.set(x, 17, B[0])
    # clapper and ribbon
    for (x, y) in [(11, 20), (12, 20), (11, 21), (12, 21)]:
        cv.set(x, y, B[1])
    for (x, y) in [(10, 3), (11, 3), (12, 3), (13, 3), (11, 4), (12, 4), (9, 2), (14, 2)]:
        cv.set(x, y, rib[1] if y < 4 else rib[0])
    cv.set(9, 8, WHITE)
    cv.set(9, 9, B[3])
    outline(cv, outc)
    # hush marks: a soft wave on each side
    for (x, y) in [(1, 9), (2, 8), (3, 9), (4, 8), (19, 8), (20, 9), (21, 8), (22, 9)]:
        if cv.get(x, y) is None:
            cv.set(x, y, hush)
    return cv


# --------------------------------------------------------------------------
# lanterns (bag icons and the thrown OBJ sprite): a small brass hand lantern
# whose glass holds a glowing heartglass core
# --------------------------------------------------------------------------

LAN_ROLES = ["o", "c0", "c1", "c2", "t0", "t1", "g0", "g1", "k0", "k1", "h0", "h1", "w"]
LAN_INDEX = {r: i + 1 for i, r in enumerate(LAN_ROLES)}   # o=1 .. w=13

# o outline, c0-c2 cap/base (dark..light), t0/t1 trims and posts (dark,
# light), g0/g1 glass (shade, light), k0/k1 heartglass core (glow, hot),
# h0/h1 light spilling out (outer, inner), w white glint
LAN_VARIANTS = {
    "LANTERN": {       # brass and amber
        "o": (64, 36, 16), "c0": (160, 96, 32), "c1": (216, 152, 48), "c2": (248, 208, 104),
        "t0": (128, 72, 24), "t1": (232, 184, 80), "g0": (232, 184, 120), "g1": (255, 232, 184),
        "k0": (255, 176, 40), "k1": (255, 248, 200), "h0": (255, 208, 96), "h1": (255, 240, 168),
        "w": (255, 255, 255),
    },
    "PRISM LANTERN": {  # silver and cyan
        "o": (24, 40, 64), "c0": (112, 128, 160), "c1": (176, 192, 216), "c2": (232, 240, 248),
        "t0": (88, 104, 136), "t1": (200, 216, 232), "g0": (144, 208, 232), "g1": (216, 248, 255),
        "k0": (64, 216, 248), "k1": (224, 255, 255), "h0": (112, 224, 255), "h1": (200, 248, 255),
        "w": (255, 255, 255),
    },
    "STAR LANTERN": {   # midnight blue and gold
        "o": (16, 16, 48), "c0": (32, 40, 104), "c1": (56, 72, 160), "c2": (96, 112, 208),
        "t0": (176, 120, 24), "t1": (248, 208, 80), "g0": (160, 152, 224), "g1": (224, 224, 255),
        "k0": (255, 200, 48), "k1": (255, 252, 208), "h0": (255, 216, 96), "h1": (255, 244, 184),
        "w": (255, 255, 255),
    },
    # the crafted lanterns (docs/EXPANSION.md 6): thrown-sprite palettes only
    "DUSK LANTERN": {   # smoked glass and blackened iron, a violet core
        "o": (16, 8, 32), "c0": (40, 32, 64), "c1": (72, 56, 104), "c2": (120, 104, 152),
        "t0": (56, 40, 88), "t1": (144, 120, 184), "g0": (88, 72, 128), "g1": (160, 144, 200),
        "k0": (184, 96, 255), "k1": (240, 216, 255), "h0": (160, 112, 232), "h1": (224, 200, 255),
        "w": (255, 255, 255),
    },
    "TIDE LANTERN": {   # sealed sea-green brass, an aqua core
        "o": (8, 40, 48), "c0": (24, 112, 112), "c1": (48, 168, 152), "c2": (144, 224, 200),
        "t0": (16, 88, 96), "t1": (120, 216, 208), "g0": (96, 176, 216), "g1": (192, 240, 255),
        "k0": (40, 200, 255), "k1": (216, 252, 255), "h0": (96, 216, 248), "h1": (200, 248, 255),
        "w": (255, 255, 255),
    },
    "HEAVY LANTERN": {  # iron-bound, a deep forge-orange core
        "o": (24, 24, 32), "c0": (72, 72, 88), "c1": (112, 112, 128), "c2": (168, 168, 184),
        "t0": (48, 48, 64), "t1": (144, 144, 160), "g0": (176, 136, 112), "g1": (232, 200, 176),
        "k0": (255, 120, 24), "k1": (255, 232, 176), "h0": (255, 160, 72), "h1": (255, 216, 152),
        "w": (255, 255, 255),
    },
    "QUICK LANTERN": {  # lacquer red and bright gold, a lemon core
        "o": (64, 8, 16), "c0": (176, 32, 40), "c1": (224, 64, 56), "c2": (255, 144, 120),
        "t0": (176, 120, 16), "t1": (255, 216, 64), "g0": (248, 200, 144), "g1": (255, 240, 200),
        "k0": (255, 232, 48), "k1": (255, 255, 224), "h0": (255, 232, 112), "h1": (255, 248, 192),
        "w": (255, 255, 255),
    },
    "BONE LANTERN": {   # bone-meal frosting, a pale ghost-green core
        "o": (56, 48, 40), "c0": (168, 152, 128), "c1": (216, 204, 176), "c2": (248, 240, 224),
        "t0": (128, 112, 96), "t1": (232, 224, 200), "g0": (200, 216, 192), "g1": (240, 248, 232),
        "k0": (136, 240, 176), "k1": (232, 255, 240), "h0": (168, 240, 200), "h1": (224, 255, 236),
        "w": (255, 255, 255),
    },
}
CAPSULE_VARIANTS = ("LANTERN", "PRISM LANTERN", "STAR LANTERN", "DUSK LANTERN", "TIDE LANTERN",
                    "HEAVY LANTERN", "QUICK LANTERN", "BONE LANTERN")


def lantern_fn(scale=1.0, lid=0.0, glow=0.0, core=1.0):
    """fn(u, v) -> role for a lantern centred on (0, 0). scale 1.0 is the
    16px sprite (about 10 x 15 px). lid lifts/tilts the cap open (0..1),
    glow adds light spilling out, core scales the heartglass glow."""
    S = scale

    def body(u, v):
        au = abs(u)
        # base: rim then a foot that narrows
        if 3.1 * S <= v <= 3.9 * S and au <= 4.3 * S:
            return "t0" if v > 3.5 * S else "t1"
        if 3.9 * S < v <= 5.7 * S:
            hw = (4.1 - (v / S - 3.9) * 0.55) * S
            if au <= hw:
                return "c2" if u < -hw * 0.35 else "c1" if u < hw * 0.45 else "c0"
            return None
        # glass cage between the rims
        if -2.9 * S <= v < 3.1 * S and au <= 3.8 * S:
            if au >= 2.9 * S:
                return "t1" if u < 0 else "t0"          # posts
            kx, ky = u / (1.7 * S * core), (v - 0.1 * S) / (2.0 * S * core)
            d = kx * kx + ky * ky
            if d <= 0.3:
                return "k1"
            if d <= 1.0:
                return "k0"
            if -2.5 * S < u < -1.8 * S and -2.2 * S < v < 1.6 * S:
                return "w"
            return "g1" if d <= 1.9 else "g0"
        # middle bar across the glass (a cross strut)
        return None

    def cap(u, v):
        au = abs(u)
        if -3.7 * S <= v < -2.9 * S and au <= 4.3 * S:
            return "t0" if v > -3.3 * S else "t1"      # top rim
        if -5.5 * S <= v < -3.7 * S:
            t = (v / S + 5.5) / 1.8                     # 0 top .. 1 bottom
            hw = (2.0 + 2.2 * t) * S
            if au <= hw:
                return "c2" if u < -hw * 0.25 else "c1" if u < hw * 0.5 else "c0"
            return None
        # handle: a loop over the cap
        d = math.hypot(u, (v + 5.6 * S))
        if v < -5.3 * S and 1.3 * S <= d <= 2.3 * S:
            return "t1" if u < 0 else "t0"
        return None

    ang = lid * 0.9
    ca, sa = math.cos(ang), math.sin(ang)
    hinge_u, hinge_v = 4.3 * S, -2.9 * S

    def fn(u, v):
        r = body(u, v)
        if r is not None:
            return r
        if lid:
            # rotate the cap about the right-hand hinge and lift it a little
            du, dv = u - hinge_u, v - hinge_v + lid * 1.2 * S
            cu = du * ca - dv * sa + hinge_u
            cv = du * sa + dv * ca + hinge_v
            r = cap(cu, cv)
        else:
            r = cap(u, v)
        if r is not None:
            return r
        if glow:
            gd = math.hypot(u / 1.2, (v + 2.6 * S) / 1.0) / S
            if gd <= 2.6 * glow:
                return "h1"
            if gd <= 4.4 * glow:
                return "h0"
        return None

    return fn


def render_lantern(size, cx, cy, ang=0.0, ss=4, **kw):
    cv = rotated_render(size, size, cx, cy, ang, lantern_fn(**kw), ss=ss)
    outline(cv, "o", skip=("h0", "h1"))
    return cv


def lantern_frames():
    """Four 16x16 role canvases: closed, wobble left, wobble right, open."""
    return [
        render_lantern(16, 7.5, 8.2),
        render_lantern(16, 7.5, 8.2, ang=math.radians(-16)),
        render_lantern(16, 7.5, 8.2, ang=math.radians(16)),
        render_lantern(16, 7.5, 8.6, lid=1.0, glow=1.0, core=1.18),
    ]


def lantern_icon(variant):
    cv = render_lantern(24, 11.5, 12.2, scale=1.45)
    pal = LAN_VARIANTS[variant]
    out = Canvas(24, 24)
    for y in range(24):
        for x in range(24):
            r = cv.p[y][x]
            if r is not None:
                out.p[y][x] = C(*pal[r])
    return out


def lantern_mini(lit=True):
    """8x8 lantern mark for the wild HUD (befriended species) and the
    warden's team row; unlit = a dozing kin's lantern (no glowing core)."""
    cv = rotated_render(8, 8, 3.5, 4.3, 0.0, lantern_fn(scale=0.52), ss=5)
    outline(cv, "o", skip=("h0", "h1"))
    if not lit:
        dim = {"k0": "c0", "k1": "t0", "g1": "c0", "g0": "t0", "w": "c1", "c2": "c1", "t1": "c0"}
        for row in cv.p:
            for i, r in enumerate(row):
                if r in dim:
                    row[i] = dim[r]
    return cv


# ==========================================================================
# 3. move-effect particles (16x16, value-ramp indices)
#    1 darkest/outline 2 dark 3 mid 4 light 5 highlight 6 white core
#    7 secondary dark 8 secondary mid 9 secondary light
# ==========================================================================

FX_NAMES = ["IMPACT", "IMPACT_SMALL", "SLASH", "CROSS", "FIREBALL", "FLAME_A", "FLAME_B",
            "BUBBLE", "DROP", "WAVE", "LEAF_A", "LEAF_B", "SPARK_A", "SPARK_B", "BOLT",
            "ROCK", "PEBBLE", "SNOWFLAKE", "SHARD", "WIND", "GLOB", "NEEDLE", "RING", "ORB",
            "FANG_TOP", "FANG_BOTTOM", "FIST", "FOOT", "CHOP", "FEATHER", "NOTE", "SPARKLE",
            "POWDER", "DUST", "BEAM", "STAR", "THREAD", "ARROW_UP", "ARROW_DOWN", "METEOR",
            "EYES", "WISP", "CLAW", "VINE", "HEART", "TEAR", "ZZZ", "SPEEDLINE", "CRACK",
            "SUNRAY", "SPLAT", "STEAM", "BURST", "BURR"]


def sinp(s):
    return max(0.0, math.sin(math.pi * s))


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    qx, qy = ax + t * dx, ay + t * dy
    return math.hypot(px - qx, py - qy), t


def poly_dist(px, py, pts):
    """Distance to polyline and arc-length parameter s in 0..1."""
    lens = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
    tot = sum(lens) or 1.0
    best = (1e9, 0.0)
    acc = 0.0
    for i in range(len(pts) - 1):
        d, t = seg_dist(px, py, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
        if d < best[0]:
            best = (d, (acc + t * lens[i]) / tot)
        acc += lens[i]
    return best


def bezier(p0, p1, p2, n=24, p3=None):
    out = []
    for i in range(n + 1):
        t = i / n
        if p3 is None:
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        else:
            x = ((1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0]
                 + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0])
            y = ((1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1]
                 + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1])
        out.append((x, y))
    return out


def stroke(cv, pts, wfn, levels, wrap=None, only_empty=False):
    """Draw a variable-width stroke. levels: list of (frac, idx) ascending by
    frac of half-width from the centre line."""
    for y in range(cv.h):
        for x in range(cv.w):
            best = None
            offs = [(0, 0)]
            if wrap == "x":
                offs = [(-16, 0), (0, 0), (16, 0)]
            elif wrap == "y":
                offs = [(0, -16), (0, 0), (0, 16)]
            for ox, oy in offs:
                d, s = poly_dist(x + 0.5 + ox, y + 0.5 + oy, pts)
                hw = wfn(s) / 2.0
                if hw <= 0 or d > hw:
                    continue
                f = d / hw
                if best is None or f < best:
                    best = f
            if best is None:
                continue
            if only_empty and cv.get(x, y) is not None:
                continue
            for frac, idx in levels:
                if best <= frac:
                    cv.set(x, y, idx)
                    break


def fx_outline(cv, idx, wrap=None, diag=False, skip=()):
    add = []
    for y in range(cv.h):
        for x in range(cv.w):
            if cv.p[y][x] is not None:
                continue
            nb = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            if diag:
                nb += [(-1, -1), (1, -1), (-1, 1), (1, 1)]
            for dx, dy in nb:
                nx, ny = x + dx, y + dy
                if wrap == "x":
                    nx %= cv.w
                if wrap == "y":
                    ny %= cv.h
                v = cv.get(nx, ny)
                if v is not None and v != idx and v not in skip:
                    add.append((x, y))
                    break
    for x, y in add:
        cv.p[y][x] = idx


def sticker(cv, mask, shade, edge=1):
    """Paint a part whose own 1px border (inside the mask) is `edge`."""
    for (x, y) in mask:
        border = any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        cv.set(x, y, edge if border else shade(x, y))


def fn_mask(f, w=16, h=16):
    return {(x, y) for y in range(h) for x in range(w) if f(x + 0.5, y + 0.5)}


def rot_uv(px, py, cx, cy, ang):
    ca, sa = math.cos(ang), math.sin(ang)
    dx, dy = px - cx, py - cy
    return dx * ca + dy * sa, -dx * sa + dy * ca


def star_poly(cx, cy, radii, rot=0.0):
    n = len(radii)
    return [(cx + radii[i] * math.cos(rot + 2 * math.pi * i / n),
             cy + radii[i] * math.sin(rot + 2 * math.pi * i / n)) for i in range(n)]


def inner_dist(mask):
    """Chebyshev-ish distance of each mask pixel to the outside (BFS)."""
    dist = {}
    frontier = []
    for (x, y) in mask:
        if any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            dist[(x, y)] = 1
            frontier.append((x, y))
    d = 1
    while frontier:
        nxt = []
        d += 1
        for (x, y) in frontier:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q in mask and q not in dist:
                    dist[q] = d
                    nxt.append(q)
        frontier = nxt
    return dist


def art16(rows):
    assert len(rows) == 16 and all(len(r) == 16 for r in rows), rows
    cv = Canvas(16, 16)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch != ".":
                cv.set(x, y, int(ch))
    return cv


# ---- individual particles -------------------------------------------------

def fx_impact():
    cv = Canvas(16, 16)
    radii = []
    for k in range(16):
        if k % 2:
            radii.append(4.1)
        else:
            radii.append(7.6 if k % 4 == 0 else 6.6)
    m = poly_mask(star_poly(7.5, 7.5, radii, rot=-math.pi / 2), 16, 16)
    dist = inner_dist(m)
    for p, d in dist.items():
        cv.set(p[0], p[1], {1: 3, 2: 4, 3: 5}.get(d, 6))
    for (x, y) in [(7, 7), (8, 7), (7, 8), (8, 8)]:
        cv.set(x, y, 6)
    fx_outline(cv, 1)
    return cv


def fx_impact_small():
    cv = Canvas(16, 16)
    radii = [5.8, 1.9, 5.8, 1.9, 5.8, 1.9, 5.8, 1.9]
    m = poly_mask(star_poly(7.5, 7.5, radii, rot=-math.pi / 2), 16, 16)
    for (x, y) in m:
        d = math.hypot(x + 0.5 - 7.5, y + 0.5 - 7.5)
        cv.set(x, y, 6 if d < 1.6 else 5 if d < 3.0 else 4)
    fx_outline(cv, 2)
    for (x, y) in [(4, 4), (11, 4), (4, 11), (11, 11)]:
        cv.set(x, y, 3)
    return cv


SLASH_LV = [(0.34, 6), (0.68, 5), (1.0, 4)]


def slash_pts(a, b, bow):
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L
    return bezier(a, (mx + nx * bow, my + ny * bow), b)


def fx_slash():
    cv = Canvas(16, 16)
    pts = slash_pts((14.2, 1.2), (1.4, 14.4), -2.2)
    stroke(cv, pts, lambda s: 4.2 * sinp(s) ** 0.75, SLASH_LV)
    fx_outline(cv, 3)
    return cv


def fx_cross():
    cv = Canvas(16, 16)
    stroke(cv, slash_pts((14.0, 1.5), (1.5, 14.0), -1.2), lambda s: 3.4 * sinp(s) ** 0.7, SLASH_LV)
    stroke(cv, slash_pts((1.5, 1.5), (14.0, 14.0), 1.2), lambda s: 3.4 * sinp(s) ** 0.7, SLASH_LV)
    fx_outline(cv, 3)
    return cv


def heat_fill(cv, mask, heat, table):
    for (x, y) in mask:
        h = heat(x + 0.5, y + 0.5)
        for th, idx in table:
            if h >= th:
                cv.set(x, y, idx)
                break


FIRE_TABLE = [(0.86, 6), (0.7, 9), (0.56, 8), (0.42, 5), (0.28, 4), (0.12, 3), (-9, 2)]


def fx_fireball():
    cv = Canvas(16, 16)
    cx, cy, R = 9.6, 8.0, 4.5

    def inside(px, py):
        if math.hypot(px - cx, py - cy) <= R:
            return True
        # flickering flame tongues fanning out behind the ball
        for (ty, ln, w, ph) in ((4.0, 8.4, 1.8, 0.0), (8.4, 9.4, 2.4, 1.9), (12.0, 7.4, 1.6, 3.4)):
            if cx - ln <= px <= cx:
                t = (cx - px) / ln
                yc = ty + (cy - ty) * (1 - t) * 0.55 + math.sin(t * 5.0 + ph) * 0.6
                if abs(py - yc) <= w * (1 - t) ** 0.7 + 0.4 * (1 - t):
                    return True
        return False

    m = fn_mask(inside)
    heat_fill(cv, m, lambda px, py: 1.0 - math.hypot(px - cx - 0.5, (py - cy + 0.4) / 0.9) / (R + 3.3)
              - max(0.0, cx - px) * 0.018, FIRE_TABLE)
    fx_outline(cv, 1)
    return cv


def tongue_mask(tongues, base):
    """Union of curved tongues [(bx, by, w, tx, ty, bend)] and a base
    ellipse (cx, cy, rx, ry)."""
    def inside(px, py):
        cx, cy, rx, ry = base
        if ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 <= 1.0:
            return True
        for (bx, by, w, tx, ty, bend) in tongues:
            if not (ty <= py <= by):
                continue
            t = (by - py) / (by - ty)
            xc = bx + (tx - bx) * t + bend * math.sin(math.pi * t)
            if abs(px - xc) <= w * (1 - t) ** 0.62:
                return True
        return False
    return fn_mask(inside)


def flame(outer, inner, core):
    cv = Canvas(16, 16)
    m = tongue_mask(*outer)
    im = tongue_mask(*inner) & m
    dist = inner_dist(m)
    for p, d in dist.items():
        cv.set(p[0], p[1], 3 if d == 1 else 4 if d == 2 else 5)
    idist = inner_dist(im)
    for p, d in idist.items():
        cv.set(p[0], p[1], 8 if d == 1 else 9)
    cx, cy, r = core
    for (x, y) in im:
        if math.hypot(x + 0.5 - cx, (y + 0.5 - cy) * 0.8) <= r:
            cv.set(x, y, 6)
    # darker rim on the lower right for volume
    for (x, y), d in dist.items():
        if d == 1 and ((x >= 9 and y >= 7) or y >= 13):
            cv.set(x, y, 2)
    fx_outline(cv, 1)
    return cv


def fx_flame_a():
    return flame(([(7.5, 11.5, 4.6, 6.6, 0.4, -1.6), (9.6, 10.5, 2.3, 12.6, 4.4, 0.6),
                   (5.2, 11.2, 1.8, 2.6, 7.0, -0.3)], (7.6, 11.8, 4.8, 3.3)),
                 ([(7.4, 12.4, 2.7, 7.0, 4.6, -0.8)], (7.6, 12.3, 3.0, 2.1)),
                 (7.5, 12.8, 1.6))


def fx_flame_b():
    return flame(([(7.6, 11.5, 4.6, 8.8, 0.4, 1.4), (5.4, 10.5, 2.3, 2.8, 4.0, -0.6),
                   (10.0, 11.2, 1.8, 12.8, 7.6, 0.3)], (7.6, 11.8, 4.8, 3.3)),
                 ([(7.8, 12.4, 2.7, 8.6, 4.4, 0.8)], (7.6, 12.3, 3.0, 2.1)),
                 (7.7, 12.8, 1.6))


def fx_bubble():
    cv = Canvas(16, 16)
    cx = cy = 7.5
    R = 6.4
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(px, py)
            if d <= R:
                if d > R - 1.0:
                    cv.set(x, y, 3)
                elif d > R - 2.0 and px + py > 1.5:
                    cv.set(x, y, 4)
                else:
                    cv.set(x, y, 5)
    for (x, y) in [(3, 6), (3, 5), (4, 4), (5, 3), (6, 3), (4, 5)]:
        cv.set(x, y, 6)
    for (x, y) in [(11, 10), (10, 11)]:
        cv.set(x, y, 6)
    fx_outline(cv, 2)
    return cv


def fx_drop():
    cv = Canvas(16, 16)
    cx, cy, R = 7.5, 10.0, 4.6

    def inside(px, py):
        if py >= cy:
            return math.hypot(px - cx, py - cy) <= R
        t = (cy - py) / (cy - 1.2)
        if t > 1:
            return False
        return abs(px - cx) <= R * (1 - t) ** 0.75
    m = fn_mask(inside)
    for (x, y) in m:
        nx = (x + 0.5 - cx) / (R + 0.5)
        ny = (y + 0.5 - cy) / (R + 2.5)
        cv.set(x, y, [2, 3, 4, 5][quant(sphere_b(nx, max(-0.95, ny)), (-0.1, 0.45, 0.85))])
    for (x, y) in [(5, 9), (5, 10), (6, 8)]:
        cv.set(x, y, 6)
    fx_outline(cv, 1)
    return cv


def fx_wave():
    cv = Canvas(16, 16)
    cx, cy, R = 8.6, 7.6, 6.6

    def ang(px, py):
        return math.degrees(math.atan2(py - cy, px - cx))   # 0 right, 90 down

    region = {}
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5, y + 0.5
            d = math.hypot(px - cx, py - cy)
            a = ang(px, py)
            body = py >= 11.4 - 2.6 * (px / 16.0) - 0.8 * math.sin(px * 0.8) and px < 15.8
            disk = d <= R
            gap = 10 <= a <= 100 and d > 2.2
            tube = d <= 2.7 and -80 <= a <= 170
            if tube and not body:
                region[(x, y)] = "tube"
            elif disk and not gap:
                region[(x, y)] = "crest"
            elif body:
                region[(x, y)] = "body"
    for (x, y), r in region.items():
        px, py = x + 0.5, y + 0.5
        d = math.hypot(px - cx, py - cy)
        a = ang(px, py)
        if r == "tube":
            cv.set(x, y, 2)
        elif r == "crest":
            if d > R - 1.2 and -175 <= a <= 12:
                cv.set(x, y, 6)
            elif d > R - 2.4 and -175 <= a <= 25:
                cv.set(x, y, 5)
            elif a > 0 or a < -150:
                cv.set(x, y, 3)
            else:
                cv.set(x, y, 4)
        else:
            cv.set(x, y, 3)
    for (x, y, c) in [(1, 12, 4), (2, 12, 4), (3, 11, 4), (6, 13, 4), (7, 13, 4), (8, 12, 4),
                      (11, 14, 4), (12, 14, 4), (13, 13, 4), (4, 14, 2), (5, 14, 2), (10, 11, 9),
                      (14, 12, 9), (1, 14, 2), (9, 14, 2)]:
        if cv.get(x, y) is not None and region.get((x, y)) == "body":
            cv.set(x, y, c)
    fx_outline(cv, 1)
    return cv


def leaf(ang):
    cv = Canvas(16, 16)
    L, W = 6.4, 3.7
    cx, cy = 7.8, 7.8

    def uv(px, py):
        return rot_uv(px, py, cx, cy, ang)

    def inside(px, py):
        u, v = uv(px, py)
        if abs(u) > L:
            return False
        half = W * (1 - (u / L) ** 2) ** 0.8
        return abs(v) <= half

    m = fn_mask(inside)
    for (x, y) in m:
        u, v = uv(x + 0.5, y + 0.5)
        cv.set(x, y, 4 if v < 0 else 3)
    dist = inner_dist(m)
    for (x, y) in m:
        u, v = uv(x + 0.5, y + 0.5)
        if abs(v) < 0.6 and abs(u) < L - 0.8 and dist[(x, y)] > 1:
            cv.set(x, y, 9)
        elif dist[(x, y)] > 1 and abs(abs(v) - (u + L * 0.35) * 0.9) < 0.5 and -2.5 < u < 3.5:
            cv.set(x, y, 5 if v < 0 else 2)      # side veins
        elif dist[(x, y)] == 1 and v > 0:
            cv.set(x, y, 2)
    # stem off the base end
    ca, sa = math.cos(ang), math.sin(ang)
    for t in (L + 0.4, L + 1.3):
        cv.set(int(cx - t * ca), int(cy - t * sa), 2)
    fx_outline(cv, 1)
    return cv


def spark(paths, dots):
    cv = Canvas(16, 16)
    for pts, w in paths:
        stroke(cv, pts, lambda s_, w=w: w, [(0.45, 6), (1.0, 5)])
    for (x, y) in dots:
        cv.set(x, y, 5)
    fx_outline(cv, 3)
    return cv


def fx_spark_a():
    return spark([([(11.5, 0.8), (5.8, 7.0), (10.2, 7.8), (4.0, 15.0)], 2.3),
                  ([(5.8, 7.0), (1.6, 8.6)], 1.5)],
                 [(13, 5), (2, 3), (12, 12), (14, 10)])


def fx_spark_b():
    return spark([([(4.0, 0.8), (9.8, 6.4), (5.4, 8.0), (12.0, 15.0)], 2.3),
                  ([(9.8, 6.4), (14.4, 5.0)], 1.5)],
                 [(2, 11), (13, 1), (1, 6), (14, 11)])


def fx_bolt():
    cv = Canvas(16, 16)
    pts = [(4.5, -4.0), (11.0, 4.0), (4.5, 12.0), (11.0, 20.0)]
    stroke(cv, pts, lambda s: 4.4, [(0.3, 6), (0.62, 5), (1.0, 4)], wrap="y")
    fx_outline(cv, 2, wrap="y")
    return cv


def rock(pts, cx, cy, rx, ry, facets, cracks=()):
    """Lumpy boulder: sphere lighting nudged per facet (nearest facet
    centre), so the light bands break into chunky planes."""
    cv = Canvas(16, 16)
    m = poly_mask(pts, 16, 16)
    for (x, y) in m:
        k = min(range(len(facets)), key=lambda i: (facets[i][0] - x - 0.5) ** 2 + (facets[i][1] - y - 0.5) ** 2)
        nx = (x + 0.5 - cx) / rx
        ny = (y + 0.5 - cy) / ry
        b = sphere_b(max(-1, min(1, nx)) * 0.92, max(-1, min(1, ny)) * 0.92) + facets[k][2]
        cv.set(x, y, [2, 3, 4, 5][quant(b, (0.02, 0.45, 0.86))])
    for c in cracks:
        for i in range(len(c) - 1):
            for p in line_pts(*c[i], *c[i + 1]):
                if p in m:
                    cv.set(p[0], p[1], 2)
    fx_outline(cv, 1)
    return cv


def fx_rock():
    pts = [(1.4, 8.0), (2.6, 4.4), (5.6, 2.2), (8.6, 2.6), (10.8, 1.4), (13.8, 3.8), (14.6, 7.8),
           (15.0, 11.2), (12.4, 14.6), (8.0, 14.2), (4.6, 15.0), (1.6, 12.4)]
    facets = [(5.0, 5.0, 0.12), (10.5, 4.0, -0.05), (8.0, 8.5, 0.1), (3.5, 10.5, -0.12),
              (12.5, 9.5, 0.0), (8.0, 12.8, -0.1), (12.0, 13.0, -0.2)]
    return rock(pts, 7.6, 7.8, 7.4, 7.2, facets, [[(9, 6), (9, 8), (11, 9)], [(4, 12), (6, 12)]])


def fx_pebble():
    pts = [(3.6, 8.6), (5.2, 5.6), (8.0, 4.8), (10.6, 5.2), (12.4, 8.0), (11.4, 11.2), (7.6, 11.8), (4.6, 11.2)]
    facets = [(6.6, 6.6, 0.1), (10.4, 7.0, -0.05), (5.6, 10.0, -0.1), (9.6, 10.6, -0.15)]
    return rock(pts, 7.8, 7.8, 4.6, 4.0, facets, [[(9, 8), (10, 9)]])


def fx_snowflake():
    cv = Canvas(16, 16)
    arms = [[(7, 6), (7, 5), (7, 4), (7, 3), (7, 2), (7, 1)],
            [(7, 8), (7, 9), (7, 10), (7, 11), (7, 12), (7, 13)],
            [(8, 6), (9, 6), (10, 5), (11, 5), (12, 4)],
            [(8, 8), (9, 8), (10, 9), (11, 9), (12, 10)],
            [(6, 6), (5, 6), (4, 5), (3, 5), (2, 4)],
            [(6, 8), (5, 8), (4, 9), (3, 9), (2, 10)],
            [(6, 2), (8, 2), (6, 12), (8, 12)]]
    for arm in arms:
        for (x, y) in arm:
            cv.set(x + 1, y + 1, 6)
    cv.set(8, 8, 5)
    fx_outline(cv, 3)
    return cv


def fx_shard():
    cv = Canvas(16, 16)
    tip, back, top, bot = (15.2, 7.6), (1.0, 8.2), (6.2, 3.2), (5.2, 12.4)
    m = poly_mask([back, top, tip, bot], 16, 16)
    for (x, y) in m:
        px, py = x + 0.5, y + 0.5
        # centre ridge line from back to tip
        yr = back[1] + (tip[1] - back[1]) * (px - back[0]) / (tip[0] - back[0])
        cv.set(x, y, 5 if py < yr - 0.5 else 6 if py < yr + 0.5 else 3)
        # facet from top vertex toward tip
        if px > top[0] and py < yr - 0.5:
            yf = top[1] + (tip[1] - top[1]) * (px - top[0]) / (tip[0] - top[0])
            if py < yf + 1.3:
                cv.set(x, y, 4)
    fx_outline(cv, 1)
    return cv


def fx_wind():
    """Crescent air blade with a smaller inner swirl."""
    cv = Canvas(16, 16)

    def crescent(o, i):
        (ox, oy, orr), (ix, iy, ir) = o, i
        return fn_mask(lambda px, py: math.hypot(px - ox, py - oy) <= orr and math.hypot(px - ix, py - iy) > ir)
    big = crescent((6.8, 8.0, 7.0), (4.0, 7.2, 6.3))
    small = crescent((4.0, 8.6, 4.2), (1.9, 8.0, 3.8))
    for m in (big, small):
        dist = inner_dist(m)
        for p, d in dist.items():
            cv.set(p[0], p[1], 4 if d == 1 else 5 if d == 2 else 6)
    fx_outline(cv, 3)
    return cv


def fx_glob():
    cv = Canvas(16, 16)

    def inside(px, py):
        # dome with a flat, dripping underside
        if py <= 12.2 and ((px - 7.8) / 6.9) ** 2 + ((py - 9.4) / 6.8) ** 2 <= 1.0:
            return True
        if 11.0 <= py <= 12.8 and 1.6 <= px <= 14.2:
            return True
        return ((abs(px - 4.6) <= 1.1 and py <= 15.0) or (abs(px - 10.8) <= 0.9 and py <= 14.2)) and py >= 11
    m = fn_mask(inside)
    for (x, y) in m:
        nx = (x + 0.5 - 7.8) / 7.4
        ny = (y + 0.5 - 8.8) / 7.4
        cv.set(x, y, [2, 3, 4, 5][quant(sphere_b(max(-1, min(1, nx)), max(-1, min(1, ny))), (0.0, 0.42, 0.84))])
    for (bx, by, r) in [(10.2, 7.4, 1.9), (5.6, 9.6, 1.3), (9.0, 11.2, 0.9)]:
        for y in range(16):
            for x in range(16):
                d = math.hypot(x + 0.5 - bx, y + 0.5 - by)
                if d <= r + 0.5:
                    cv.set(x, y, 5 if d > r - 0.5 else 8)
        cv.set(int(bx - 0.6), int(by - 0.6), 6)
    for (x, y, c) in [(4, 5, 6), (5, 4, 6), (4, 6, 5), (6, 4, 5)]:
        cv.set(x, y, c)
    fx_outline(cv, 1)
    return cv


def fx_needle():
    cv = Canvas(16, 16)
    for x in range(1, 12):
        cv.set(x, 7, 5 if x > 2 else 4)
        cv.set(x, 8, 3)
    for x in range(12, 15):
        cv.set(x, 7, 6 if x < 14 else 5)
    cv.set(12, 8, 3)
    cv.set(13, 8, 3)
    cv.set(15, 7, 4)
    # fletch at the back
    for (x, y) in [(1, 6), (2, 6), (1, 9), (2, 9)]:
        cv.set(x, y, 4)
    fx_outline(cv, 1)
    return cv


def fx_ring():
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + 0.5 - 7.5, y + 0.5 - 7.5)
            e = abs(d - 5.2)
            if e <= 1.55:
                cv.set(x, y, 6 if e < 0.45 else 5 if e < 0.95 else 4)
    fx_outline(cv, 3)
    fx_outline(cv, 2, skip=(3,))
    return cv


def fx_orb():
    cv = Canvas(16, 16)
    cx = cy = 7.5
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= 6.0:
                cv.set(x, y, 1 if d < 2.6 else 2 if d < 4.0 else 3 if d < 5.1 else 4)
    # secondary-coloured inner reflection (upper left) and a glint
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(px, py)
            a = math.degrees(math.atan2(py, px))
            if 2.4 <= d <= 3.9 and -170 <= a <= -100:
                cv.set(x, y, 8)
    cv.set(4, 5, 9)
    cv.set(5, 4, 9)
    fx_outline(cv, 5)
    for (x, y) in [(1, 3), (14, 5), (12, 14), (2, 12), (8, 0)]:
        cv.set(x, y, 4)
    return cv


def fangs(top=True):
    """Upper / lower jaw: an arched gum line with fangs that interlock."""
    cv = Canvas(16, 16)

    def edge(x):
        k = ((x - 7.5) / 7.5) ** 2
        return 3.2 + 2.6 * k if top else 12.8 - 2.6 * k

    for y in range(16):
        for x in range(16):
            e = edge(x + 0.5)
            if top and y + 0.5 <= e:
                cv.set(x, y, 9 if y + 0.5 <= e - 2.0 else 8 if y + 0.5 <= e - 1.0 else 7)
            if not top and y + 0.5 >= e:
                cv.set(x, y, 9 if y + 0.5 <= e + 1.0 else 8 if y + 0.5 <= e + 2.0 else 7)
    if top:
        teeth = [(0.8, 5.2, 12.8), (4.8, 7.7, 8.0), (7.3, 10.2, 8.0), (9.8, 14.4, 12.8)]
    else:
        teeth = [(-0.6, 2.8, 8.0), (2.4, 7.2, 3.0), (6.4, 9.0, 7.0), (8.4, 13.2, 3.0), (12.8, 16.4, 8.0)]
    owner = {}
    for i, (x0, x1, tip_y) in enumerate(teeth):
        mid = (x0 + x1) / 2
        lean = 0.4 if mid < 8 else -0.4
        e0, e1 = edge(x0), edge(x1)
        d = -1.0 if top else 1.0
        m = poly_mask([(x0, e0 + d), (x1, e1 + d), (mid + lean, tip_y)], 16, 16)
        for (x, y) in m:
            owner[(x, y)] = i
            rel = (x + 0.5 - x0) / (x1 - x0)
            cv.set(x, y, 6 if rel < 0.55 else 4)
    for (x, y), i in owner.items():
        if owner.get((x - 1, y), i) != i:
            cv.set(x, y, 1)
        elif (x, y + (1 if top else -1)) not in owner and cv.get(x, y) == 4:
            cv.set(x, y, 3)
    fx_outline(cv, 1)
    return cv


def fx_fist():
    cv = Canvas(16, 16)

    back = rect_mask(2, 5, 14, 13, r=2)
    sticker(cv, back, lambda x, y: 3 if x < 12 else 2)
    for x0 in (2, 5, 8, 11):
        f = rect_mask(x0, 2, x0 + 3, 10, r=1)
        sh = lathe_levels(f, th=(0.1, 0.5, 0.9))
        sticker(cv, f, lambda x, y, sh=sh: ([2, 3, 4, 5][sh[(x, y)]] if y > 3 else 5 if sh[(x, y)] >= 2 else 4))
        for x in range(x0 + 1, x0 + 3):
            cv.set(x, 6, 2)          # finger crease
    thumb = rect_mask(1, 9, 11, 13, r=2)
    sticker(cv, thumb, lambda x, y: 4 if y == 10 else 3 if y == 11 else 2)
    cv.set(9, 10, 5)
    cv.set(10, 11, 2)
    # wrist cuff
    wrist = rect_mask(5, 13, 12, 15)
    sticker(cv, wrist, lambda x, y: 8 if x < 10 else 7)
    return cv


def fx_foot():
    return art16([
        "..111111........",
        "..155441........",
        "..154431........",
        "..154431........",
        "..1544331.......",
        "..15444331.111..",
        ".155444431145411",
        ".15544444313443 1".replace(" ", ""),
        ".154444444434431",
        ".154444444444331",
        ".134444444444331",
        ".133333333333321",
        "..1222222222221.",
        "...11111111111..",
        "................",
        "................",
    ])


def fx_chop():
    cv = Canvas(16, 16)
    # open hand, fingers together pointing up, thumb out to the left
    palm = rect_mask(5, 7, 14, 15, r=2)
    sticker(cv, palm, lambda x, y: 4 if x < 11 else 3)
    tops = {5: 3, 8: 1, 11: 2}
    for x0, top in tops.items():
        f = rect_mask(x0, top, x0 + 3, 9, r=1)
        sticker(cv, f, lambda x, y, x0=x0: 5 if x == x0 + 1 else 4)
    f = rect_mask(13, 4, 15, 9, r=1)
    sticker(cv, f, lambda x, y: 3)
    thumb = poly_mask([(1.2, 6.2), (3.4, 5.4), (7.2, 10.0), (6.8, 13.4), (4.6, 12.6)], 16, 16)
    sticker(cv, thumb, lambda x, y: 5 if x < 4 else 4)
    for (x, y) in [(8, 12), (9, 13), (10, 13)]:
        cv.set(x, y, 3)          # palm crease
    # speed lines above
    for (x0, y0, x1, y1) in [(1, 1, 3, 3), (4, 0, 5, 1), (0, 4, 1, 4)]:
        for p in line_pts(x0, y0, x1, y1):
            if cv.get(*p) is None:
                cv.set(p[0], p[1], 5)
    return cv


def fx_feather():
    cv = Canvas(16, 16)
    shaft = bezier((2.0, 14.5), (6.5, 6.0), (14.0, 1.5))

    def inside(px, py):
        d, s = poly_dist(px, py, shaft)
        if s < 0.12:
            return False
        w = 3.4 * sinp(min(1.0, (s - 0.12) / 0.88)) ** 0.55
        return d <= w
    m = fn_mask(inside)
    for (x, y) in m:
        d, s = poly_dist(x + 0.5, y + 0.5, shaft)
        # which side of the shaft
        i = min(range(len(shaft)), key=lambda k: (shaft[k][0] - x - 0.5) ** 2 + (shaft[k][1] - y - 0.5) ** 2)
        k2 = min(i + 1, len(shaft) - 1)
        k1 = max(i - 1, 0)
        tx, ty = shaft[k2][0] - shaft[k1][0], shaft[k2][1] - shaft[k1][1]
        side = tx * (y + 0.5 - shaft[i][1]) - ty * (x + 0.5 - shaft[i][0])
        cv.set(x, y, 4 if side < 0 else 3)
    # notches in the vane
    for (x, y) in [(6, 7), (9, 9), (11, 7), (5, 10)]:
        if (x, y) in m:
            cv.p[y][x] = None
    for i in range(len(shaft) - 1):
        for p in line_pts(int(shaft[i][0]), int(shaft[i][1]), int(shaft[i + 1][0]), int(shaft[i + 1][1])):
            cv.set(p[0], p[1], 6)
    fx_outline(cv, 1)
    return cv


def fx_note():
    cv = Canvas(16, 16)
    ang = math.radians(-24)
    head = fn_mask(lambda px, py: (lambda u, v: (u / 3.1) ** 2 + (v / 2.2) ** 2 <= 1.0)(*rot_uv(px, py, 5.6, 12.0, ang)))
    for (x, y) in head:
        u, v = rot_uv(x + 0.5, y + 0.5, 5.6, 12.0, ang)
        cv.set(x, y, 4 if v < -0.6 else 3)
    for y in range(2, 12):
        cv.set(8, y, 3)
        cv.set(7, y, 4) if y < 11 else None
    flag = bezier((8.5, 2.0), (13.5, 3.5), (12.5, 9.0), n=20)
    stroke(cv, flag, lambda s: 2.6 - 1.4 * s, [(0.5, 4), (1.0, 3)])
    cv.set(4, 11, 6)
    cv.set(7, 3, 5)
    fx_outline(cv, 1)
    return cv


def fx_sparkle():
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            dx, dy = abs(x + 0.5 - 7.5), abs(y + 0.5 - 7.5)
            v = dx ** 0.5 + dy ** 0.5
            if v <= 2.75:
                cv.set(x, y, 6 if v < 1.5 else 5 if v < 2.2 else 4)
    fx_outline(cv, 3)
    return cv


def fx_powder():
    cv = Canvas(16, 16)
    dots = [(3, 3, 1), (9, 2, 0), (12, 6, 1), (6, 7, 1), (2, 10, 0), (10, 11, 1), (5, 13, 0), (13, 13, 0), (8, 5, 2)]
    for (x, y, kind) in dots:
        big = kind == 1
        sec = (x + y) % 2 == 0
        cols = (9, 8, 7) if sec else (5, 4, 3)
        if big:
            for (dx, dy, c) in [(0, 0, 0), (1, 0, 1), (0, 1, 1), (1, 1, 2)]:
                cv.set(x + dx, y + dy, cols[c])
        elif kind == 0:
            cv.set(x, y, cols[0])
        else:
            cv.set(x, y, 6)
    fx_outline(cv, 2)
    return cv


def fx_dust():
    cv = Canvas(16, 16)
    circ = [(4.4, 10.0, 3.3), (8.2, 6.8, 3.9), (12.0, 8.8, 3.1), (13.0, 12.0, 2.4),
            (8.4, 11.2, 3.5), (2.6, 12.6, 2.2)]
    m = fn_mask(lambda px, py: py <= 14.6 and any(math.hypot(px - cx, py - cy) <= r for cx, cy, r in circ))
    for (x, y) in m:
        best = -2
        for cx, cy, r in circ:
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r:
                best = max(best, sphere_b((x + 0.5 - cx) / (r + 0.3), (y + 0.5 - cy) / (r + 0.3)))
        cv.set(x, y, [3, 4, 5, 6][quant(best, (0.1, 0.55, 0.92))])
    for x in range(16):
        for y in (14,):
            if cv.get(x, y) is not None:
                cv.set(x, y, 3)
    fx_outline(cv, 2)
    return cv


def fx_beam():
    cv = Canvas(16, 16)
    prof = {3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 6, 9: 5, 10: 4, 11: 3, 12: 2}
    for y, v in prof.items():
        for x in range(16):
            cv.set(x, y, v)
    # travelling glints (period 16 so the segment tiles)
    for (x, y, v) in [(2, 5, 5), (3, 5, 5), (10, 10, 5), (11, 10, 5), (6, 4, 4), (13, 11, 4),
                      (7, 6, 6), (8, 6, 6), (14, 9, 6), (15, 9, 6), (0, 4, 3), (9, 12, 3)]:
        cv.set(x, y, v)
    return cv


def fx_star():
    cv = Canvas(16, 16)
    cx, cy = 7.5, 8.0
    radii = [7.3 if i % 2 == 0 else 3.0 for i in range(10)]
    pts = star_poly(cx, cy, radii, rot=-math.pi / 2)
    m = poly_mask(pts, 16, 16)
    for (x, y) in m:
        a = math.atan2(y + 0.5 - cy, x + 0.5 - cx)
        # facet index and whether left/right of the ridge
        k = (a + math.pi / 2) / (2 * math.pi / 5)
        frac = k - math.floor(k + 0.5)
        ridge_a = -math.pi / 2 + math.floor(k + 0.5) * 2 * math.pi / 5
        nx = math.cos(ridge_a) + (-math.sin(ridge_a)) * (0.8 if frac < 0 else -0.8)
        ny = math.sin(ridge_a) + math.cos(ridge_a) * (0.8 if frac < 0 else -0.8)
        b = -(nx * 0.6 + ny * 0.8)
        cv.set(x, y, 5 if b > 0.5 else 4 if b > -0.4 else 3)
    cv.set(7, 7, 6)
    cv.set(7, 8, 6)
    fx_outline(cv, 1)
    return cv


def fx_thread():
    cv = Canvas(16, 16)
    pts = [(x / 2.0 - 8, 7.5 + 3.0 * math.sin(2 * math.pi * (x / 2.0 - 8) / 16)) for x in range(0, 65)]
    stroke(cv, pts, lambda s: 2.6, [(0.45, 6), (1.0, 4)], wrap=None)
    fx_outline(cv, 2, wrap="x")
    return cv


def chevrons(up=True):
    cv = Canvas(16, 16)
    for off in (0, 6):
        for x in range(1, 15):
            k = int(abs(x - 7.5) - 0.5) // 2        # rises 1 row every 2 columns
            for t in range(3):
                y = 3 + off + k + t if up else 12 - off - k - t
                c = (6, 4, 3)[t] if up else (3, 4, 6)[t]
                cv.set(x, y, c)
    fx_outline(cv, 1)
    return cv


def fx_meteor():
    cv = Canvas(16, 16)
    rx, ry = 4.6, 11.2
    trail = [(rx, ry), (15.5, 0.5)]

    def w(s):
        return 7.4 * (1 - s) ** 0.9 + 0.6
    stroke(cv, trail, w, [(0.35, 9), (0.6, 8), (0.8, 4), (1.0, 3)])
    # flicker notches along the trail edge
    for (x, y) in [(13, 4), (10, 2), (14, 1), (11, 6)]:
        if cv.get(x, y) in (3, 4):
            cv.p[y][x] = None
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + 0.5 - rx, y + 0.5 - ry)
            if d <= 3.4:
                b = sphere_b((x + 0.5 - rx) / 3.9, (y + 0.5 - ry) / 3.9)
                cv.set(x, y, [1, 2, 2, 3][quant(b, (-0.2, 0.3, 0.75))])
    cv.set(3, 10, 5)
    fx_outline(cv, 1)
    return cv


def fx_eyes():
    return art16([
        "................",
        "................",
        "................",
        ".11..........11.",
        ".1111......1111.",
        "..11111..11111..",
        "..166611116661..",
        ".1666781187666 1".replace(" ", "."),
        ".1668871178866..".replace("..", "1."),
        ".1665871178566..".replace("..", "1."),
        "..166811118661..",
        "...1111..1111...",
        "................",
        "................",
        "................",
        "................",
    ])


def fx_wisp():
    cv = Canvas(16, 16)

    def inside(px, py):
        if math.hypot(px - 8.0, (py - 10.2) * 1.1) <= 4.4:
            return True
        if 0.6 < py < 10.2:
            t = (10.2 - py) / 9.6
            xc = 8.0 - 3.2 * math.sin(t * 2.9) + 1.4 * t
            hw = 4.3 * (1 - t) ** 1.1
            return abs(px - xc) <= hw
        return False
    m = fn_mask(inside)
    dist = inner_dist(m)
    for p, d in dist.items():
        cv.set(p[0], p[1], {1: 3, 2: 4, 3: 5}.get(d, 6))
    # hollow, flickering heart in the secondary colour
    for (x, y) in [(7, 10), (8, 10), (7, 11), (8, 11)]:
        cv.set(x, y, 9)
    cv.set(8, 9, 8)
    fx_outline(cv, 2)
    for (x, y) in [(13, 4), (2, 3), (14, 10), (3, 8)]:
        cv.set(x, y, 4)
    return cv


def fx_claw():
    cv = Canvas(16, 16)
    for off in (-5.2, 0.0, 5.2):
        a = (11.8 + off * 0.707, 2.2 + off * 0.707)
        b = (2.2 + off * 0.707, 11.8 + off * 0.707)
        stroke(cv, slash_pts(a, b, -0.6), lambda s_: 2.2 * sinp(s_) ** 0.6, [(0.5, 6), (1.0, 4)])
    fx_outline(cv, 3)
    return cv


def fx_vine():
    cv = Canvas(16, 16)
    pts = bezier((0.2, 13.0), (7.0, 15.5), (8.5, 3.0), n=36, p3=(15.8, 3.6))
    stroke(cv, pts, lambda s_: 4.0 - 1.2 * s_, [(0.3, 5), (0.62, 4), (1.0, 3)])
    for y in range(15, 0, -1):
        for x in range(16):
            if cv.p[y][x] == 3 and cv.get(x, y - 1) in (3, 4, 5):
                cv.p[y][x] = 2
    # small leaves in the secondary colour
    for (lx, ly, ang) in [(5.2, 9.6, -2.2), (11.6, 2.8, -1.6)]:
        for y in range(16):
            for x in range(16):
                u, v = rot_uv(x + 0.5, y + 0.5, lx, ly, ang)
                if abs(u) <= 2.4 and abs(v) <= 1.3 * (1 - (u / 2.4) ** 2) + 0.2:
                    if cv.get(x, y) is None:
                        cv.set(x, y, 9 if v < 0 else 8)
    fx_outline(cv, 1)
    return cv


def fx_heart():
    cv = Canvas(16, 16)

    def inside(px, py):
        if math.hypot(px - 5.0, py - 5.6) <= 3.5 or math.hypot(px - 11.0, py - 5.6) <= 3.5:
            return True
        return 6.4 <= py <= 14.6 and abs(px - 8.0) <= (14.6 - py) * 0.8
    m = fn_mask(inside)
    for (x, y) in m:
        b = sphere_b((x + 0.5 - 8.0) / 7.0, (y + 0.5 - 8.0) / 7.0)
        cv.set(x, y, [3, 4, 5][quant(b, (0.2, 0.62))])
    for (x, y) in [(4, 5), (5, 4), (4, 6)]:
        cv.set(x, y, 6)
    fx_outline(cv, 2)
    return cv


def fx_tear():
    cv = Canvas(16, 16)
    cx, cy, R = 7.5, 9.6, 3.2

    def inside(px, py):
        if py >= cy:
            return math.hypot(px - cx, py - cy) <= R
        t = (cy - py) / (cy - 3.0)
        return t <= 1 and abs(px - cx) <= R * (1 - t) ** 0.8
    m = fn_mask(inside)
    for (x, y) in m:
        cv.set(x, y, 9 if x < 7 and y < 10 else 8)
    cv.set(6, 8, 6)
    fx_outline(cv, 7)
    return cv


def fx_zzz():
    cv = Canvas(16, 16)
    for (x0, y0, n) in ((7, 1, 7), (1, 9, 5)):
        for i in range(n):
            cv.set(x0 + i, y0, 6)
            cv.set(x0 + i, y0 + n - 1, 5)
            cv.set(x0 + n - 1 - i, y0 + i, 6 if i < n // 2 else 5)
    fx_outline(cv, 2)
    return cv


def fx_speedline():
    cv = Canvas(16, 16)
    for (y, x0, x1) in ((3, 2, 15), (7, 0, 12), (8, 0, 12), (12, 4, 15)):
        for x in range(x0, x1 + 1):
            t = (x - x0) / max(1, x1 - x0)
            cv.set(x, y, 6 if t > 0.6 else 5 if t > 0.3 else 4)
    fx_outline(cv, 3)
    return cv


def fx_crack():
    """A jagged ground crack that tiles horizontally (enters and leaves at y=8)."""
    cv = Canvas(16, 16)
    pts = [(-0.5, 8.0), (3.0, 6.5), (6.0, 9.5), (9.5, 6.8), (12.5, 9.2), (16.5, 8.0)]
    stroke(cv, pts, lambda s_: 2.6 + 0.8 * sinp(s_ * 3), [(0.5, 1), (1.0, 2)])
    add = []
    for y in range(16):
        for x in range(16):
            if cv.get(x, y) is None and cv.get(x, y - 1) in (1, 2):
                add.append((x, y))
    for (x, y) in add:
        cv.set(x, y, 5)
    for (x, y) in [(2, 11), (7, 12), (11, 4), (14, 11)]:
        cv.set(x, y, 4)
    return cv


def fx_sunray():
    """A soft column of light that tiles vertically."""
    cv = Canvas(16, 16)
    prof = {2: 3, 3: 4, 4: 4, 5: 5, 6: 6, 7: 6, 8: 6, 9: 6, 10: 5, 11: 4, 12: 4, 13: 3}
    for x, v in prof.items():
        for y in range(16):
            cv.set(x, y, v)
    for (x, y, v) in [(4, 2, 6), (11, 9, 6), (5, 13, 9), (10, 5, 9), (3, 7, 5), (12, 14, 5)]:
        cv.set(x, y, v)
    return cv


def fx_splat():
    cv = Canvas(16, 16)
    blobs = [(8.0, 8.6, 4.8), (5.2, 10.6, 3.0), (10.8, 10.4, 3.2), (8.4, 11.8, 3.0)]
    drops = [(2.2, 4.0, 1.3), (13.8, 3.6, 1.2), (1.8, 13.6, 1.0), (14.2, 13.4, 1.1), (8.6, 1.8, 1.0)]
    m = fn_mask(lambda px, py: any(math.hypot(px - cx, py - cy) <= r for cx, cy, r in blobs + drops))
    for (x, y) in m:
        b = sphere_b((x + 0.5 - 8.0) / 7.5, (y + 0.5 - 8.5) / 7.5)
        cv.set(x, y, [2, 3, 4, 5][quant(b, (-0.1, 0.4, 0.82))])
    cv.set(6, 7, 6)
    cv.set(7, 7, 8)
    fx_outline(cv, 1)
    return cv


def fx_steam():
    cv = Canvas(16, 16)
    circ = [(5.0, 9.6, 3.6), (9.4, 7.0, 4.3), (12.2, 10.4, 3.0), (8.4, 11.6, 3.4)]
    m = fn_mask(lambda px, py: any(math.hypot(px - cx, py - cy) <= r for cx, cy, r in circ))
    for (x, y) in m:
        best = -2
        for cx, cy, r in circ:
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r:
                best = max(best, sphere_b((x + 0.5 - cx) / (r + 0.4), (y + 0.5 - cy) / (r + 0.4)))
        cv.set(x, y, [4, 5, 6][quant(best, (0.25, 0.7))])
    fx_outline(cv, 3)
    return cv


def fx_burst():
    """Radial rays around a white-hot centre (scaled up for flares)."""
    cv = Canvas(16, 16)
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5 - 8.0, y + 0.5 - 8.0
            d = math.hypot(px, py)
            a = math.atan2(py, px)
            k = abs(math.sin(a * 4))            # 8 rays
            ray = d <= 2.2 + 5.6 * (1 - k) ** 3
            if d <= 2.4:
                cv.set(x, y, 6)
            elif ray and d <= 7.9:
                cv.set(x, y, 6 if d < 3.8 else 5 if d < 5.6 else 4)
    fx_outline(cv, 3)
    return cv


def fx_burr():
    cv = Canvas(16, 16)
    radii = [7.2 if i % 2 == 0 else 4.4 for i in range(20)]
    m = poly_mask(star_poly(8.0, 8.0, radii, rot=0.1), 16, 16)
    for (x, y) in m:
        b = sphere_b((x + 0.5 - 8.0) / 6.0, (y + 0.5 - 8.0) / 6.0)
        cv.set(x, y, [2, 3, 4, 5][quant(b, (-0.2, 0.3, 0.75))])
    for (x, y) in [(6, 6), (9, 5), (7, 9)]:
        cv.set(x, y, 9)
    fx_outline(cv, 1)
    return cv


def fx_big_ring():
    cv = Canvas(32, 32)
    for y in range(32):
        for x in range(32):
            d = math.hypot(x + 0.5 - 16.0, y + 0.5 - 16.0)
            e = abs(d - 13.0)
            if e <= 2.3:
                cv.set(x, y, 6 if e < 0.7 else 5 if e < 1.5 else 4)
    fx_outline(cv, 3)
    return cv


def fx_big_glow():
    cv = Canvas(32, 32)
    for y in range(32):
        for x in range(32):
            d = math.hypot(x + 0.5 - 16.0, y + 0.5 - 16.0)
            dither = ((x + y) & 1) == 0
            if d <= 5.5:
                cv.set(x, y, 6)
            elif d <= 8.5:
                cv.set(x, y, 5 if d > 7.5 and dither else 6 if d <= 7.5 else 5)
            elif d <= 11.5:
                cv.set(x, y, 5 if d <= 10.5 or dither else 4)
            elif d <= 14.0:
                cv.set(x, y, 4 if d <= 13.0 or dither else 3)
            elif d <= 15.6 and dither:
                cv.set(x, y, 3)
    return cv


FX_BIG = [("RING", fx_big_ring), ("GLOW", fx_big_glow)]


FX_BUILDERS = {
    "IMPACT": fx_impact, "IMPACT_SMALL": fx_impact_small, "SLASH": fx_slash, "CROSS": fx_cross,
    "FIREBALL": fx_fireball, "FLAME_A": fx_flame_a, "FLAME_B": fx_flame_b,
    "BUBBLE": fx_bubble, "DROP": fx_drop, "WAVE": fx_wave,
    "LEAF_A": lambda: leaf(math.radians(-35)), "LEAF_B": lambda: leaf(math.radians(55)),
    "SPARK_A": fx_spark_a, "SPARK_B": fx_spark_b, "BOLT": fx_bolt, "ROCK": fx_rock,
    "PEBBLE": fx_pebble, "SNOWFLAKE": fx_snowflake, "SHARD": fx_shard, "WIND": fx_wind,
    "GLOB": fx_glob, "NEEDLE": fx_needle, "RING": fx_ring, "ORB": fx_orb,
    "FANG_TOP": lambda: fangs(True), "FANG_BOTTOM": lambda: fangs(False), "FIST": fx_fist,
    "FOOT": fx_foot, "CHOP": fx_chop, "FEATHER": fx_feather, "NOTE": fx_note,
    "SPARKLE": fx_sparkle, "POWDER": fx_powder, "DUST": fx_dust, "BEAM": fx_beam,
    "STAR": fx_star, "THREAD": fx_thread, "ARROW_UP": lambda: chevrons(True),
    "ARROW_DOWN": lambda: chevrons(False), "METEOR": fx_meteor, "EYES": fx_eyes,
    "WISP": fx_wisp, "CLAW": fx_claw, "VINE": fx_vine, "HEART": fx_heart, "TEAR": fx_tear,
    "ZZZ": fx_zzz, "SPEEDLINE": fx_speedline, "CRACK": fx_crack, "SUNRAY": fx_sunray,
    "SPLAT": fx_splat, "STEAM": fx_steam, "BURST": fx_burst, "BURR": fx_burr,
}


def fx_palette(main, sec):
    """Preview palette built the way the engine is expected to."""
    m = C(*main)
    s = C(*sec)
    k = (0, 0, 0)
    return [k, mix(k, m, 0.28), mix(k, m, 0.62), m, mix(m, WHITE, 0.42), mix(m, WHITE, 0.72),
            WHITE, mix(k, s, 0.62), s, mix(s, WHITE, 0.5)] + [k] * 6


FX_PREVIEW_PAIRS = [
    ("fire", (240, 88, 32), (255, 208, 48)),
    ("water", (48, 112, 232), (104, 216, 255)),
    ("grass", (48, 168, 56), (184, 232, 72)),
    ("electric", (240, 192, 16), (255, 248, 168)),
    ("psychic", (224, 72, 168), (255, 200, 240)),
    ("shadow", (104, 56, 160), (48, 24, 72)),
]


# ==========================================================================
# 4. battle backgrounds (240x160, bottom 48px = one plain tile)
# ==========================================================================

SW, SH = 240, 160
TEXT_Y = 112
ENEMY_BASE = (176, 70, 44, 12)     # cx, cy, rx, ry
ALLY_BASE = (64, 116, 56, 14)
PLAIN = C(40, 48, 64)


class Rng:
    """Tiny deterministic LCG so the art is reproducible."""

    def __init__(self, seed):
        self.s = seed & 0xFFFFFFFF

    def next(self):
        self.s = (self.s * 1103515245 + 12345) & 0x7FFFFFFF
        return self.s

    def rand(self, a, b):
        return a + self.next() % (b - a + 1)

    def unit(self):
        return self.next() / 0x7FFFFFFF


def new_scene(fill):
    return [[fill] * SW for _ in range(SH)]


def ell_r(x, y, base):
    cx, cy, rx, ry = base
    return math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry)


# ---- grass field ------------------------------------------------------------

G = {
    "sky0": C(160, 208, 248), "sky1": C(184, 224, 248), "sky2": C(216, 240, 248),
    "cloud": C(248, 248, 248), "cloud_s": C(200, 224, 240),
    "tb0": C(104, 168, 136), "tb1": C(128, 192, 152),
    "tf0": C(32, 88, 56), "tf1": C(48, 120, 64), "tf2": C(80, 152, 72), "tf3": C(120, 184, 88),
    "g0": C(112, 184, 80), "g1": C(136, 200, 96), "g2": C(152, 216, 112), "g3": C(184, 232, 136),
    "b_rim": C(64, 128, 64), "b_dark": C(88, 160, 72), "b_fill": C(104, 176, 80), "b_hi": C(160, 216, 112),
}


def paint_grass():
    S = new_scene(PLAIN)
    rng = Rng(1234)
    HORIZON = 32
    # sky bands with a stepped edge
    for y in range(HORIZON):
        for x in range(SW):
            j = (x // 2 + (x // 7)) % 2
            if y < 7 or (y == 7 and j):
                c = G["sky0"]
            elif y < 15 or (y == 15 and j):
                c = G["sky1"]
            else:
                c = G["sky2"]
            S[y][x] = c
    # a few soft clouds peeking above the tree line
    for (cx, cy, w) in [(28, 9, 22), (112, 6, 30), (196, 10, 26)]:
        puffs = [(cx - w * 0.35, cy + 2, w * 0.28), (cx, cy, w * 0.38), (cx + w * 0.38, cy + 2.5, w * 0.26)]
        for y in range(0, 22):
            for x in range(int(cx - w), int(cx + w) + 1):
                if not (0 <= x < SW):
                    continue
                inside = [p for p in puffs if math.hypot((x + 0.5 - p[0]) / p[2], (y + 0.5 - p[1]) / (p[2] * 0.62)) <= 1.0]
                if inside and y <= cy + 4:
                    lit = any(math.hypot((x + 0.5 - p[0] + 1.5) / p[2], (y + 0.5 - p[1] + 1.5) / (p[2] * 0.62)) <= 0.95
                              for p in inside)
                    S[y][x] = G["cloud"] if lit and y < cy + 3 else G["cloud_s"]
    # back (distant) tree row: soft bumps
    back_top = []
    for x in range(SW):
        t = x / SW * math.pi * 2
        back_top.append(17 + 2.2 * math.sin(t * 3 + 0.5) + 1.5 * math.sin(t * 7 + 1.3) + 1.0 * math.sin(t * 13))
    for x in range(SW):
        for y in range(int(back_top[x]), HORIZON):
            S[y][x] = G["tb1"] if y < back_top[x] + 1.5 and (x + y) % 3 else G["tb0"]
    # front tree row: overlapping round crowns
    crowns = []
    x = -6
    while x < SW + 10:
        r = rng.rand(7, 11)
        top = rng.rand(17, 23)
        crowns.append((x, top + r, r))
        x += rng.rand(9, 14)
    for (cx, cy, r) in crowns:
        # leaf clumps on a loose grid inside the crown ("cauliflower" canopy)
        clumps = []
        for gy in range(-r, r + 1, 4):
            for gx in range(-r, r + 1, 5):
                ox = gx + (2 if (gy // 4) % 2 else 0)
                if ox * ox + gy * gy <= (r - 1) * (r - 1):
                    clumps.append((cx + ox, cy + gy))
        for y in range(max(0, cy - r), HORIZON):
            for xx in range(cx - r - 1, cx + r + 2):
                if not (0 <= xx < SW):
                    continue
                dx = (xx + 0.5 - cx) / r
                dy = (y + 0.5 - cy) / (r * 0.9)
                if dx * dx + dy * dy > 1.0 and y < cy:
                    continue
                if y >= cy and abs(dx) > 1.0:
                    continue
                b = sphere_b(max(-1, min(1, dx)), max(-1, min(1, dy)) if y < cy else 0.6)
                if clumps:
                    kx, ky = min(clumps, key=lambda c: (c[0] - xx - 0.5) ** 2 + (c[1] - y - 0.5) ** 2 * 1.4)
                    bc = sphere_b(max(-1, min(1, (xx + 0.5 - kx) / 3.6)), max(-1, min(1, (y + 0.5 - ky) / 3.0)))
                    b = 0.62 * b + 0.5 * bc - 0.1
                lv = quant(b, (0.0, 0.36, 0.7))
                S[y][xx] = [G["tf0"], G["tf1"], G["tf2"], G["tf3"]][lv]
        # dark seam on the crown's right edge so trees read separately
        for y in range(max(0, cy - r), HORIZON):
            for xx in range(cx + int(r * 0.55), cx + r + 1):
                if 0 <= xx < SW:
                    dx = (xx + 0.5 - cx) / r
                    dy = (y + 0.5 - cy) / (r * 0.9)
                    if 0.82 <= dx * dx + (dy * dy if y < cy else 0) <= 1.0:
                        S[y][xx] = G["tf0"]
    # bushes / shadow strip along the horizon
    for x in range(SW):
        h = 2 + int(1.5 + 1.5 * math.sin(x * 0.45) + math.sin(x * 1.3))
        for y in range(HORIZON - h, HORIZON):
            S[y][x] = G["tf1"] if y == HORIZON - h else G["tf0"]
    # field: perspective bands, period 32px horizontally so tiles repeat
    edges = [HORIZON, 35, 39, 44, 50, 57, 65, 75, 87, 101, TEXT_Y]
    for y in range(HORIZON, TEXT_Y):
        band = max(i for i, e in enumerate(edges) if e <= y)
        for x in range(SW):
            S[y][x] = G["g2"] if band % 2 == 0 else G["g1"]
    # jagged grass-blade edge between bands (period 8)
    saw = [0, 1, 2, 1, 0, 1, 1, 0]
    for i, e in enumerate(edges[1:-1], start=1):
        col = G["g2"] if (i - 1) % 2 == 0 else G["g1"]
        for x in range(SW):
            for k in range(saw[x % 8] + (1 if i > 5 else 0)):
                if e + k < TEXT_Y:
                    S[e + k][x] = col
        for x in range(SW):
            if (x % 8) in (2, 5):
                S[e][x] = G["g0"]
    # tufts, sized by depth; positions hashed on x % 32 so tiles repeat
    trng = Rng(77)
    for y0 in range(HORIZON + 4, TEXT_Y - 1, 4):
        depth = (y0 - HORIZON) / (TEXT_Y - HORIZON)
        n = 1 if depth < 0.5 else 2
        used = []
        for _ in range(n):
            x0 = trng.rand(0, 31)
            if any(abs(x0 - u) < 8 for u in used):
                x0 = (x0 + 16) % 32
            used.append(x0)
            yj = y0 + trng.rand(0, 2)
            for rep in range(0, SW + 32, 32):
                x = x0 + rep
                if depth < 0.3:
                    pts = [(x, yj, "g0"), (x + 1, yj - 1, "g0")]
                elif depth < 0.6:
                    pts = [(x, yj, "g0"), (x + 1, yj - 1, "g0"), (x + 2, yj, "g0"), (x + 1, yj - 2, "g3")]
                else:
                    pts = [(x, yj, "g0"), (x + 1, yj - 1, "g0"), (x + 1, yj - 2, "g0"), (x + 2, yj, "g0"),
                           (x + 3, yj - 1, "g0"), (x + 4, yj, "g0"), (x + 1, yj - 3, "g3"), (x + 3, yj - 2, "g3")]
                for (px, py, c) in pts:
                    if 0 <= px < SW and HORIZON < py < TEXT_Y:
                        S[py][px] = G[c]
    # the two grass bases
    for base in (ENEMY_BASE, ALLY_BASE):
        grass_base(S, base)
    return S


def grass_base(S, base):
    """Emerald-style patch of shorter, darker grass: dark rim (heavier at the
    front), a lit inner lip at the back, darker inner front, streaky texture."""
    cx, cy, rx, ry = base
    for y in range(int(cy - ry - 2), min(TEXT_Y, int(cy + ry + 3))):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            if not (0 <= x < SW and 0 <= y < SH):
                continue
            r = ell_r(x, y, base)
            dy = (y + 0.5 - cy) / ry
            dx = (x + 0.5 - cx) / rx
            if r > 1.0:
                if r <= 1.07 and dy > 0.25:
                    S[y][x] = G["g0"]
                continue
            rim_w = 0.09 + 0.1 * max(0.0, dy)
            if r > 1.0 - rim_w:
                S[y][x] = G["b_rim"]
            elif dy < 0 and r > 0.82 and dx < 0.55:
                S[y][x] = G["b_hi"]                    # lit back lip
            elif dy > 0.25 and r > 0.7:
                S[y][x] = G["b_dark"]                  # shaded front inside
            else:
                S[y][x] = G["b_fill"]
    rng = Rng(int(cx * 31 + cy))
    for _ in range(int(rx * ry / 9)):
        x = int(cx + (rng.unit() * 2 - 1) * rx * 0.8)
        y = int(cy + (rng.unit() * 2 - 1) * ry * 0.7)
        if y >= TEXT_Y - 1 or ell_r(x, y, base) > 0.74 or ell_r(x + 2, y, base) > 0.74:
            continue
        ln = 2 if ell_r(x, y, base) < 0.5 else 1
        for k in range(ln + 1):
            if S[y][x + k] == G["b_fill"]:
                S[y][x + k] = G["b_dark"]
        if (x + y) % 3 == 0 and y - 1 >= 0 and S[y - 1][x + 1] == G["b_fill"]:
            S[y - 1][x + 1] = G["b_hi"]


# ---- stone arena ------------------------------------------------------------

A = {
    "roof": C(40, 48, 72), "tier": C(64, 72, 104), "tier_l": C(96, 104, 136),
    "skin": C(248, 200, 152), "hair": C(88, 64, 48), "hair2": C(216, 168, 64),
    "red": C(224, 72, 64), "blue": C(72, 120, 216), "yellow": C(240, 200, 72),
    "green": C(88, 176, 96), "white": C(240, 240, 232),
    "cap": C(216, 208, 192), "wall": C(176, 168, 152), "wall_d": C(128, 120, 112),
    "ban_r": C(200, 64, 64), "ban_b": C(64, 104, 192), "ban_rl": C(232, 112, 96), "ban_bl": C(112, 152, 224),
    "fl0": C(152, 144, 128), "fl1": C(192, 184, 160), "fl2": C(208, 200, 176), "fl3": C(224, 216, 192),
    "paint": C(248, 248, 240), "base_r": C(216, 88, 72), "base_b": C(88, 136, 216),
    "shadow": C(168, 160, 136),
    "tint_r": C(232, 200, 184), "tint_rl": C(240, 216, 200),
    "tint_b": C(192, 200, 216), "tint_bl": C(208, 216, 232),
}


def paint_arena():
    S = new_scene(PLAIN)
    rng = Rng(4321)
    WALL_TOP, FLOOR_Y = 24, 36
    # stands: dark roof band, then three tiers of spectators
    for y in range(WALL_TOP):
        for x in range(SW):
            S[y][x] = A["roof"] if y < 2 else A["tier"]
    tiers = [(2, 7), (9, 7), (16, 8)]
    shirts = ["red", "blue", "yellow", "green", "white", "blue", "red"]
    for ti, (ty, th) in enumerate(tiers):
        # tier step highlight line
        for x in range(SW):
            S[ty + th - 1][x] = A["tier_l"]
        x = rng.rand(0, 3) + ti * 2
        while x < SW - 3:
            if rng.rand(0, 9) < 8:
                sh = A[shirts[rng.rand(0, len(shirts) - 1)]]
                hair = A["hair2"] if rng.rand(0, 4) == 0 else A["hair"]
                hy = ty + (0 if rng.rand(0, 3) else 1)       # some heads bob up
                # head 3x3 with hair on top, body 4 wide below
                for (dx, dy, c) in [(1, 0, hair), (2, 0, hair), (0, 1, hair), (1, 1, A["skin"]), (2, 1, A["skin"]),
                                    (3, 1, hair), (1, 2, A["skin"]), (2, 2, A["skin"])]:
                    if hy + dy < ty + th - 1:
                        S[hy + dy][x + dx] = c
                for dy in range(3, th - 1):
                    for dx in range(0, 4):
                        if hy + dy < ty + th - 1:
                            S[hy + dy][x + dx] = sh
                # waving arm
                if rng.rand(0, 5) == 0 and hy - 1 >= ty:
                    S[hy][x + 4] = A["skin"]
                    S[hy + 1][x + 4] = sh
            x += rng.rand(5, 7)
    # parapet wall with banner panels
    for y in range(WALL_TOP, FLOOR_Y):
        for x in range(SW):
            if y < WALL_TOP + 2:
                c = A["cap"] if y == WALL_TOP else A["wall"]
            elif y >= FLOOR_Y - 2:
                c = A["wall_d"]
            else:
                panel = (x // 40) % 2
                inx = x % 40
                if inx < 2 or inx > 37:
                    c = A["wall"]
                else:
                    c = A["ban_r"] if panel == 0 else A["ban_b"]
                    if y == WALL_TOP + 2:
                        c = A["ban_rl"] if panel == 0 else A["ban_bl"]
            S[y][x] = c
    # little emblem on each panel: a white chevron
    for px0 in range(0, SW, 40):
        cx = px0 + 20
        for (dx, dy) in [(-3, 1), (-2, 2), (-1, 3), (0, 4), (1, 3), (2, 2), (3, 1), (-2, 1), (0, 3), (2, 1)]:
            y = WALL_TOP + 3 + dy
            if y < FLOOR_Y - 2:
                S[y][cx + dx] = A["white"]
    # floor slabs in perspective: joints converge on a vanishing point above
    # the screen centre and the pattern is mirror-symmetric about x=120, so
    # half the floor tiles are h-flips of the other half.
    VX, VY = 120.0, -230.0
    rows = [FLOOR_Y, 40, 45, 51, 58, 66, 75, 86, 98, TEXT_Y]
    for i in range(len(rows) - 1):
        y0, y1 = rows[i], rows[i + 1]
        off = 10.0 if i % 2 else 0.0
        for y in range(y0, min(TEXT_Y, y1)):
            k = (FLOOR_Y - VY) / (y + 0.5 - VY)        # screen px -> far-edge units
            for x in range(SW):
                X0 = VX + (x + 0.5 - VX) * k
                lx = (X0 - VX - off) % 20.0
                if y == y0:
                    c = A["fl0"]
                elif lx < k:
                    c = A["fl0"]
                elif y == y0 + 1 or lx < 2 * k:
                    c = A["fl3"]
                elif lx > 20.0 - k or y == y1 - 1:
                    c = A["fl1"]
                else:
                    c = A["fl2"]
                if y < FLOOR_Y + 5 and c in (A["fl2"], A["fl3"]):
                    c = A["fl1"]                          # shadow under the wall
                S[y][x] = c
    # a few worn speckles, mirrored so the symmetry (and tile sharing) holds
    srng = Rng(55)
    for _ in range(26):
        x = srng.rand(0, 119)
        y = srng.rand(FLOOR_Y + 6, TEXT_Y - 1)
        for xx in (x, SW - 1 - x):
            if S[y][xx] == A["fl2"]:
                S[y][xx] = A["fl1"]
    # painted back line
    for x in range(SW):
        S[FLOOR_Y + 2][x] = A["paint"]
    # painted bases
    arena_base(S, ENEMY_BASE, A["base_r"])
    arena_base(S, ALLY_BASE, A["base_b"])
    return S


def ell_dist(x, y, base):
    """Approximate distance in pixels from pixel centre to the ellipse edge
    (positive inside)."""
    cx, cy, rx, ry = base
    px, py = x + 0.5 - cx, y + 0.5 - cy
    f = math.hypot(px / rx, py / ry)
    if f == 0:
        return min(rx, ry)
    gx, gy = px / (rx * rx * f), py / (ry * ry * f)
    return (1.0 - f) / math.hypot(gx, gy)


def arena_base(S, base, ring_col):
    cx, cy, rx, ry = base
    red = ring_col == A["base_r"]
    tint = {A["fl2"]: A["tint_r" if red else "tint_b"], A["fl3"]: A["tint_rl" if red else "tint_bl"],
            A["fl1"]: A["tint_r" if red else "tint_b"]}
    for y in range(int(cy - ry - 2), min(TEXT_Y, int(cy + ry + 3))):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            if not (0 <= x < SW and 0 <= y < SH):
                continue
            d = ell_dist(x, y, base)
            if d < 0:
                continue
            if d < 1.0:
                S[y][x] = A["paint"]
            elif d < 3.4:
                S[y][x] = ring_col
            elif d < 4.4:
                S[y][x] = A["paint"]
            elif S[y][x] in tint:
                S[y][x] = tint[S[y][x]]


# ---- shared helpers for the area scenes -------------------------------------

def soft_base(S, base, pal, seed=0):
    """Patch of shorter ground under a kin: rim, lit back lip, shaded front,
    streaky texture. pal: dict with rim, dark, fill, hi (and optional edge)."""
    cx, cy, rx, ry = base
    for y in range(int(cy - ry - 2), min(TEXT_Y, int(cy + ry + 3))):
        for x in range(int(cx - rx - 2), int(cx + rx + 3)):
            if not (0 <= x < SW and 0 <= y < SH):
                continue
            r = ell_r(x, y, base)
            dy = (y + 0.5 - cy) / ry
            dx = (x + 0.5 - cx) / rx
            if r > 1.0:
                if r <= 1.07 and dy > 0.25 and "edge" in pal:
                    S[y][x] = pal["edge"]
                continue
            rim_w = 0.09 + 0.1 * max(0.0, dy)
            if r > 1.0 - rim_w:
                S[y][x] = pal["rim"]
            elif dy < 0 and r > 0.82 and dx < 0.55:
                S[y][x] = pal["hi"]
            elif dy > 0.25 and r > 0.7:
                S[y][x] = pal["dark"]
            else:
                S[y][x] = pal["fill"]
    rng = Rng(int(cx * 31 + cy) + seed)
    for _ in range(int(rx * ry / 9)):
        x = int(cx + (rng.unit() * 2 - 1) * rx * 0.8)
        y = int(cy + (rng.unit() * 2 - 1) * ry * 0.7)
        if y >= TEXT_Y - 1 or ell_r(x, y, base) > 0.74 or ell_r(x + 2, y, base) > 0.74:
            continue
        for k in range(2 if ell_r(x, y, base) < 0.5 else 1):
            if S[y][x + k] == pal["fill"]:
                S[y][x + k] = pal["dark"]
        if (x + y) % 3 == 0 and y - 1 >= 0 and S[y - 1][x + 1] == pal["fill"]:
            S[y - 1][x + 1] = pal["hi"]


def perspective_bands(S, top, edges, cols, saw=(0, 1, 2, 1, 0, 1, 1, 0), seam=None):
    """Alternating ground bands from `top` to TEXT_Y with a jagged edge."""
    for y in range(top, TEXT_Y):
        band = max(i for i, e in enumerate(edges) if e <= y)
        for x in range(SW):
            S[y][x] = cols[band % 2]
    for i, e in enumerate(edges[1:-1], start=1):
        col = cols[(i - 1) % 2]
        for x in range(SW):
            for k in range(saw[x % 8] + (1 if i > 5 else 0)):
                if e + k < TEXT_Y:
                    S[e + k][x] = col
        if seam is not None:
            for x in range(SW):
                if (x % 8) in (2, 5):
                    S[e][x] = seam


# ---- forest glade -------------------------------------------------------------

F = {
    "c0": C(16, 40, 32), "c1": C(24, 64, 40), "c2": C(40, 96, 48), "c3": C(72, 136, 64),
    "c4": C(128, 184, 88),
    "t0": C(40, 28, 24), "t1": C(72, 50, 36), "t2": C(104, 76, 52),
    "m0": C(40, 84, 44), "m1": C(56, 108, 52), "m2": C(76, 132, 60), "m3": C(120, 168, 76),
    "sun": C(184, 216, 112), "cap": C(200, 72, 56), "dot": C(240, 232, 208),
    "b_rim": C(40, 80, 40), "b_dark": C(56, 104, 48), "b_fill": C(72, 128, 56), "b_hi": C(120, 168, 80),
}


def paint_forest():
    S = new_scene(PLAIN)
    rng = Rng(9876)
    HOR = 40
    # deep canopy: layered leaf clumps, darker toward the top
    for y in range(HOR):
        for x in range(SW):
            S[y][x] = F["c0"] if y < 10 else F["c1"]
    clumps = []
    for row, (y0, r0) in enumerate(((4, 7), (13, 8), (22, 7))):
        x = -8 + row * 5
        while x < SW + 10:
            clumps.append((x, y0 + rng.rand(-2, 2), r0 + rng.rand(-1, 2), row))
            x += rng.rand(11, 16)
    for (cx, cy, r, row) in clumps:
        for y in range(max(0, cy - r), min(HOR, cy + r + 1)):
            for x in range(cx - r, cx + r + 1):
                if not (0 <= x < SW):
                    continue
                dx, dy = (x + 0.5 - cx) / r, (y + 0.5 - cy) / (r * 0.8)
                if dx * dx + dy * dy > 1.0:
                    continue
                b = sphere_b(max(-1, min(1, dx)), max(-1, min(1, dy))) - 0.12 * (2 - row)
                S[y][x] = [F["c1"], F["c2"], F["c3"], F["c4"]][quant(b, (0.05, 0.45, 0.82))]
    # trunks between the clumps, from the canopy down to the ground line
    for tx in (14, 58, 97, 132, 214, 231):
        w = 5 if tx % 2 else 6
        for y in range(18, HOR + 2):
            for x in range(tx, tx + w):
                if 0 <= x < SW:
                    S[y][x] = F["t2"] if x == tx + 1 else F["t0"] if x >= tx + w - 2 else F["t1"]
    # undergrowth line
    for x in range(SW):
        h = 3 + int(1.6 + 1.6 * math.sin(x * 0.37) + math.sin(x * 1.1))
        for y in range(HOR - h, HOR + 1):
            S[y][x] = F["c2"] if y == HOR - h else F["c1"]
    # mossy ground bands
    perspective_bands(S, HOR + 1, [HOR + 1, 44, 48, 53, 59, 66, 74, 84, 96, TEXT_Y],
                      (F["m1"], F["m2"]), seam=F["m0"])
    # dappled sunlight: soft patches on a 32px grid
    lrng = Rng(31)
    for y0 in range(HOR + 8, TEXT_Y - 4, 11):
        depth = (y0 - HOR) / (TEXT_Y - HOR)
        x0 = lrng.rand(0, 31)
        rx, ry = 4 + depth * 5, 1.5 + depth * 2
        for rep in range(-32, SW + 32, 32):
            cx = x0 + rep
            for y in range(int(y0 - ry), int(y0 + ry) + 1):
                for x in range(int(cx - rx), int(cx + rx) + 1):
                    if 0 <= x < SW and HOR < y < TEXT_Y:
                        d = math.hypot((x + 0.5 - cx) / rx, (y + 0.5 - y0) / ry)
                        if d <= 0.55:
                            S[y][x] = F["sun"]
                        elif d <= 1.0 and (x + y) % 2 == 0:
                            S[y][x] = F["m3"]
    # tiny mushrooms and tufts
    mrng = Rng(5)
    for y0 in range(HOR + 6, TEXT_Y - 2, 7):
        x0 = mrng.rand(0, 31)
        for rep in range(0, SW + 32, 32):
            x = x0 + rep
            if (y0 // 7) % 3 == 0:
                for (px, py, c) in [(x, y0 - 1, "cap"), (x + 1, y0 - 1, "cap"), (x + 2, y0 - 1, "cap"),
                                    (x + 1, y0 - 2, "cap"), (x + 1, y0 - 1, "dot"), (x + 1, y0, "dot")]:
                    if 0 <= px < SW and HOR < py < TEXT_Y:
                        S[py][px] = F[c]
            else:
                for (px, py) in [(x, y0), (x + 1, y0 - 1), (x + 2, y0)]:
                    if 0 <= px < SW and HOR < py < TEXT_Y:
                        S[py][px] = F["m0"]
    pal = {"rim": F["b_rim"], "dark": F["b_dark"], "fill": F["b_fill"], "hi": F["b_hi"], "edge": F["m0"]}
    for base in (ENEMY_BASE, ALLY_BASE):
        soft_base(S, base, pal, seed=3)
    return S


# ---- mirror lake shore ----------------------------------------------------------

L = {
    "sky0": C(152, 200, 248), "sky1": C(184, 220, 248), "cloud": C(248, 248, 248),
    "cloud_s": C(208, 228, 244),
    "hill0": C(88, 136, 144), "hill1": C(112, 160, 160), "tree": C(64, 112, 96),
    "w0": C(40, 96, 168), "w1": C(64, 128, 200), "w2": C(104, 168, 224), "w3": C(200, 232, 255),
    "s0": C(192, 168, 120), "s1": C(216, 196, 144), "s2": C(232, 216, 168),
    "g0": C(88, 144, 72), "g1": C(112, 168, 88), "g2": C(144, 192, 104),
    "r0": C(64, 104, 40), "r1": C(96, 144, 56), "r2": C(120, 80, 48), "r3": C(160, 112, 64),
    "b_rim": C(168, 144, 96), "b_dark": C(200, 176, 128), "b_fill": C(216, 196, 144), "b_hi": C(240, 228, 184),
}


def paint_lake():
    S = new_scene(PLAIN)
    SKY, WATER, SHORE = 18, 24, 50
    for y in range(SKY):
        for x in range(SW):
            j = (x // 3 + x // 7) % 2
            S[y][x] = L["sky0"] if y < 8 or (y == 8 and j) else L["sky1"]
    for (cx, cy, w) in [(40, 7, 24), (150, 5, 30), (215, 9, 18)]:
        for y in range(0, SKY):
            for x in range(int(cx - w), int(cx + w) + 1):
                if 0 <= x < SW:
                    d = math.hypot((x + 0.5 - cx) / w, (y + 0.5 - cy) / (w * 0.22))
                    if d <= 1.0:
                        S[y][x] = L["cloud"] if y < cy else L["cloud_s"]
    # far shore: soft hills with a line of trees
    for x in range(SW):
        top = SKY - 3 + 2.5 * math.sin(x * 0.03 + 1.0) + 1.2 * math.sin(x * 0.11)
        for y in range(int(top), WATER):
            S[y][x] = L["hill1"] if y < top + 1.5 else L["hill0"]
        if (x // 5) % 2 == 0:
            for y in range(int(top) - 1, int(top) + 2):
                if 0 <= y < WATER:
                    S[y][x] = L["tree"]
    # lake: bands that get lighter toward the shore, sparkles on a 32px grid
    for y in range(WATER, SHORE):
        t = (y - WATER) / (SHORE - WATER)
        for x in range(SW):
            S[y][x] = L["w0"] if t < 0.3 else L["w1"] if t < 0.75 else L["w2"]
    srng = Rng(8)
    for y in range(WATER + 2, SHORE - 1, 3):
        x0 = srng.rand(0, 31)
        ln = 2 + (y - WATER) // 7
        for rep in range(0, SW + 32, 32):
            for k in range(ln):
                x = x0 + rep + k
                if 0 <= x < SW:
                    S[y][x] = L["w3"] if k < ln - 1 else L["w2"]
    # wet edge and sandy/grassy bank
    for x in range(SW):
        e = SHORE + int(1.5 * math.sin(x * 0.2))
        for y in range(SHORE - 2, TEXT_Y):
            if y < e:
                S[y][x] = L["w3"] if y == e - 1 and x % 4 else S[y][x]
            elif y < e + 2:
                S[y][x] = L["s0"]
            else:
                S[y][x] = L["s1"]
    perspective_bands(S, SHORE + 18, [SHORE + 18, 72, 78, 86, 96, TEXT_Y], (L["g1"], L["g2"]), seam=L["g0"])
    # a band of sand between water and grass with ripples
    for y in range(SHORE + 3, SHORE + 18):
        for x in range(SW):
            if (x + y * 3) % 16 == 0:
                S[y][x] = L["s2"]
    # reeds at both ends of the shore
    rrng = Rng(19)
    for (x0, x1) in ((0, 44), (196, 240)):
        x = x0
        while x < x1:
            h = rrng.rand(12, 22)
            base_y = SHORE + rrng.rand(0, 4)
            for y in range(base_y - h, base_y + 1):
                if 0 <= y < TEXT_Y:
                    S[y][x] = L["r1"] if (y + x) % 5 else L["r0"]
            if rrng.rand(0, 2) == 0:
                for y in range(base_y - h - 3, base_y - h + 1):
                    if 0 <= y:
                        S[y][x] = L["r3"] if y < base_y - h - 1 else L["r2"]
                        if x + 1 < SW:
                            S[y][x + 1] = L["r2"]
            x += rrng.rand(3, 5)
    pal = {"rim": L["b_rim"], "dark": L["b_dark"], "fill": L["b_fill"], "hi": L["b_hi"], "edge": L["s0"]}
    soft_base(S, ENEMY_BASE, pal, seed=5)
    gpal = {"rim": L["g0"], "dark": L["g1"], "fill": L["g2"], "hi": L["s2"], "edge": L["g0"]}
    soft_base(S, ALLY_BASE, gpal, seed=6)
    return S


# ---- stormstone rise -------------------------------------------------------------

T = {
    "k0": C(24, 24, 48), "k1": C(40, 40, 72), "k2": C(64, 64, 104), "k3": C(96, 96, 140),
    "k4": C(152, 152, 200), "glow": C(208, 208, 240),
    "st0": C(56, 56, 72), "st1": C(88, 88, 104), "st2": C(128, 128, 144), "st3": C(168, 168, 184),
    "h0": C(40, 56, 56), "h1": C(56, 80, 72),
    "g0": C(52, 72, 64), "g1": C(72, 96, 80), "g2": C(92, 118, 94), "g3": C(136, 156, 120),
    "b_rim": C(56, 64, 72), "b_dark": C(96, 104, 112), "b_fill": C(120, 128, 136), "b_hi": C(160, 168, 176),
}


def paint_storm():
    S = new_scene(PLAIN)
    HOR = 40
    # churning storm clouds: layered waves of noise, darkest overhead and
    # lit from a pale glow low on the horizon
    def cloud(x, y):
        return (0.55 * math.sin(x * 0.040 + y * 0.16) + 0.4 * math.sin(x * 0.093 - y * 0.23 + 1.3)
                + 0.28 * math.sin(x * 0.21 + y * 0.37 + 2.1) + 0.16 * math.sin(x * 0.47 - y * 0.5)
                + (y / HOR) * 1.9 - 0.75)
    TH = (-0.55, -0.05, 0.42, 0.85, 1.25)
    cols = [T["k0"], T["k1"], T["k2"], T["k3"], T["k4"], T["glow"]]
    for y in range(HOR):
        for x in range(SW):
            f = cloud(x, y)
            lv = quant(f, TH)
            # 1px checker dither where two levels meet
            if lv < 5 and quant(f + 0.07, TH) != lv and (x + y) % 2 == 0:
                lv += 1
            if y >= 34:
                lv = max(lv, 4)
            S[y][x] = cols[lv]
    # hill line
    for x in range(SW):
        top = HOR - 4 + 2.5 * math.sin(x * 0.025 + 0.4)
        for y in range(int(top), HOR + 2):
            S[y][x] = T["h1"] if y < top + 1 else T["h0"]
    # standing stones on the ridge
    for (sx, w, h, lean) in ((20, 11, 28, 0), (44, 8, 18, 1), (72, 6, 11, 0), (166, 6, 12, 0),
                             (192, 9, 22, -1), (220, 12, 30, 0)):
        base_y = HOR + 1
        for y in range(base_y - h, base_y + 1):
            t = (base_y - y) / h
            off = int(lean * t * 3)
            hw = w / 2 - (1 if t > 0.85 else 0)
            for x in range(int(sx - hw) + off, int(sx + hw) + off + 1):
                if 0 <= x < SW:
                    rel = (x - off - (sx - hw)) / max(1, 2 * hw)
                    S[y][x] = T["st3"] if rel < 0.2 else T["st2"] if rel < 0.55 else T["st1"] if rel < 0.85 else T["st0"]
        for y in range(base_y - h + 3, base_y, 6):
            x = int(sx) + (y % 3) - 1
            if 0 <= x < SW:
                S[y][x] = T["st0"]
    # windswept grass: bands plus slanted streaks on a 32px grid
    perspective_bands(S, HOR + 2, [HOR + 2, 46, 51, 57, 64, 72, 82, 94, TEXT_Y], (T["g1"], T["g2"]),
                      saw=(0, 1, 2, 2, 1, 0, 0, 0), seam=T["g0"])
    wrng = Rng(12)
    for y0 in range(HOR + 6, TEXT_Y - 2, 5):
        depth = (y0 - HOR) / (TEXT_Y - HOR)
        x0 = wrng.rand(0, 31)
        ln = 2 + int(depth * 5)
        for rep in range(0, SW + 32, 32):
            for k in range(ln):
                x, y = x0 + rep + k, y0 - k // 2
                if 0 <= x < SW and HOR + 2 < y < TEXT_Y:
                    S[y][x] = T["g3"] if k < ln - 1 else T["g0"]
    pal = {"rim": T["b_rim"], "dark": T["b_dark"], "fill": T["b_fill"], "hi": T["b_hi"], "edge": T["g0"]}
    for base in (ENEMY_BASE, ALLY_BASE):
        soft_base(S, base, pal, seed=8)
    return S


def lum(c):
    return c[0] * 3 + c[1] * 6 + c[2]


def pack_scene(S, name):
    """240x160 colour image -> (tiles, map[20*32], pals[4][16])."""
    tiles_px = {}
    sets = {}
    for ty in range(20):
        for tx in range(30):
            px = [S[ty * 8 + r][tx * 8 + c] for r in range(8) for c in range(8)]
            tiles_px[(tx, ty)] = px
            sets[(tx, ty)] = frozenset(px)
    # greedy bank packing, biggest colour sets first
    banks = [set() for _ in range(4)]
    uniq = sorted(set(sets.values()), key=lambda st: (-len(st), sorted(st)))
    bank_of = {}
    for st in uniq:
        best = None
        for i, b in enumerate(banks):
            if st <= b:
                best = (i, -1)
                break
            add = len(st - b)
            if len(b) + add <= 15 and (best is None or add < best[1] or (add == best[1] and len(b) > len(banks[best[0]]))):
                if b or best is None or add < best[1]:
                    best = (i, add)
        if best is None:
            raise SystemExit("%s: cannot fit colour set of %d into 4 banks" % (name, len(st)))
        banks[best[0]] |= st
        bank_of[st] = best[0]
    pals = []
    order = []
    for b in banks:
        cols = sorted(b, key=lum)
        order.append(cols)
        pals.append([(0, 0, 0)] + cols + [(0, 0, 0)] * (15 - len(cols)))
    # tile 0 = the plain text-box fill
    tiles = []
    lookup = {}

    def add_tile(idx):
        t = tuple(idx)
        variants = [
            (t, 0),
            (tuple(t[r * 8 + (7 - c)] for r in range(8) for c in range(8)), 1),
            (tuple(t[(7 - r) * 8 + c] for r in range(8) for c in range(8)), 2),
            (tuple(t[(7 - r) * 8 + (7 - c)] for r in range(8) for c in range(8)), 3),
        ]
        for v, fl in variants:
            if v in lookup:
                return lookup[v], fl
        lookup[t] = len(tiles)
        tiles.append(t)
        return lookup[t], 0

    plain_set = frozenset([PLAIN])
    pb = bank_of[plain_set] if plain_set in bank_of else next(i for i, b in enumerate(banks) if PLAIN in b)
    add_tile([order[pb].index(PLAIN) + 1] * 64)
    mp = [0] * (20 * 32)
    for ty in range(20):
        for tx in range(32):
            if tx >= 30:
                mp[ty * 32 + tx] = 0 | (pb << 12)
                continue
            b = bank_of[sets[(tx, ty)]]
            idx = [order[b].index(c) + 1 for c in tiles_px[(tx, ty)]]
            tid, fl = add_tile(idx)
            mp[ty * 32 + tx] = tid | ((fl & 1) << 10) | ((fl >> 1) << 11) | (b << 12)
    packed = []
    for t in tiles:
        rows = []
        for r in range(8):
            v = 0
            for c in range(8):
                v |= t[r * 8 + c] << (4 * c)
            rows.append(v)
        packed.append(rows)
    return packed, mp, pals


def decode_scene(tiles, mp, pals):
    img = [[None] * SW for _ in range(SH)]
    for ty in range(20):
        for tx in range(30):
            e = mp[ty * 32 + tx]
            t = tiles[e & 0x3FF]
            hf, vf, b = (e >> 10) & 1, (e >> 11) & 1, (e >> 12) & 15
            for r in range(8):
                for c in range(8):
                    sr = 7 - r if vf else r
                    sc = 7 - c if hf else c
                    i = (t[sr] >> (4 * sc)) & 15
                    img[ty * 8 + r][tx * 8 + c] = pals[b][i]
    return img


# ==========================================================================
# assembly + output
# ==========================================================================

ITEM_NAMES = ["GLOW TONIC", "BRIGHT TONIC", "RADIANT TONIC", "TUNING FORK", "IGNITER",
              "HONEY DROP", "SUNSEED", "LANTERN", "PRISM LANTERN", "STAR LANTERN", "BLOOM SHARD",
              "SPARK SHARD", "DUSK SHARD", "FROST SHARD", "AMP COIL", "GUARD COIL", "HUSH BELL"]


def build_items():
    """Bag icons in ITEM_* order (src/game/data.h)."""
    copper = ramp((136, 64, 24), (200, 104, 48), (240, 152, 88), (255, 208, 160))
    steel = ramp((56, 88, 152), (88, 128, 200), (144, 184, 240), (208, 228, 255))
    return [
        icon_tonic(0), icon_tonic(1), icon_tonic(2),
        icon_tuning_fork(), icon_igniter(), icon_honey(), icon_sunseed(),
        lantern_icon("LANTERN"), lantern_icon("PRISM LANTERN"), lantern_icon("STAR LANTERN"),
        icon_shard(ramp((24, 112, 48), (48, 168, 72), (112, 216, 112), (200, 248, 184)), C(16, 56, 32)),
        icon_shard(ramp((184, 136, 8), (240, 200, 32), (255, 236, 104), (255, 252, 200)), C(96, 64, 8)),
        icon_shard(ramp((72, 40, 128), (112, 72, 176), (168, 128, 224), (224, 200, 255)), C(32, 16, 64)),
        icon_shard(ramp((32, 136, 168), (72, 192, 216), (144, 232, 248), (216, 252, 255)), C(16, 64, 96)),
        icon_coil(copper, C(72, 32, 16), ramp((168, 40, 40), (232, 80, 72)),
                  [(20, 3, C(248, 208, 64)), (19, 4, C(248, 208, 64)), (20, 4, C(255, 248, 176)),
                   (21, 4, C(248, 208, 64)), (20, 5, C(248, 208, 64))]),
        icon_coil(steel, C(24, 40, 88), ramp((72, 80, 96), (136, 144, 160)),
                  [(19, 2, C(64, 104, 208)), (20, 2, C(64, 104, 208)), (21, 2, C(64, 104, 208)),
                   (19, 3, C(144, 184, 255)), (20, 3, C(64, 104, 208)), (21, 3, C(64, 104, 208)),
                   (20, 4, C(64, 104, 208))]),
        icon_hush_bell(),
    ]


# --------------------------------------------------------------------------
# UI labels for the move menu (BG canvas images, palette bank of their own)
# --------------------------------------------------------------------------

TINY_FONT = {
    "A": [".#.", "#.#", "###", "#.#", "#.#"], "C": [".##", "#..", "#..", "#..", ".##"],
    "D": ["##.", "#.#", "#.#", "#.#", "##."], "E": ["###", "#..", "##.", "#..", "###"],
    "F": ["###", "#..", "##.", "#..", "#.."], "I": ["###", ".#.", ".#.", ".#.", "###"],
    "K": ["#.#", "#.#", "##.", "#.#", "#.#"], "N": ["#..#", "##.#", "#.##", "#..#", "#..#"],
    "O": [".#.", "#.#", "#.#", "#.#", ".#."], "P": ["##.", "#.#", "##.", "#..", "#.."],
    "R": ["##.", "#.#", "##.", "#.#", "#.#"], "S": [".##", "#..", ".#.", "..#", "##."],
    "T": ["###", ".#.", ".#.", ".#.", ".#."], "U": ["#.#", "#.#", "#.#", "#.#", "###"],
    "W": ["#...#", "#...#", "#.#.#", "#.#.#", ".#.#."], "!": ["#", "#", "#", ".", "#"],
}

LABEL_PAL = [(0, 0, 0), WHITE, C(40, 40, 56), C(224, 80, 40), C(255, 160, 104), C(88, 104, 152),
             C(144, 160, 200), C(96, 96, 108), C(152, 152, 164), WHITE, C(72, 72, 88)]


def tiny_text_width(t):
    return sum((2 if ch == " " else len(TINY_FONT[ch][0]) + 1) for ch in t) - 1


def tiny_text(img, x, y, t, col):
    for ch in t:
        if ch == " ":
            x += 2
            continue
        g = TINY_FONT[ch]
        for r, row in enumerate(g):
            for c, v in enumerate(row):
                if v == "#":
                    img[y + r][x + c] = col
        x += len(g[0]) + 1


def label_tab(text, fill, light):
    """64x8 tab that sits on top of the move-info panel."""
    img = [[0] * 64 for _ in range(8)]
    for y in range(8):
        for x in range(64):
            if y == 0 and (x < 2 or x > 61):
                continue
            if y == 1 and (x == 0 or x == 63):
                continue
            edge = y == 0 or x == 0 or x == 63 or (y == 1 and (x == 1 or x == 62))
            img[y][x] = 2 if edge else (light if y == 1 else fill)
    tiny_text(img, (64 - tiny_text_width(text)) // 2, 2, text, 9)
    return img


def label_uses():
    img = [[0] * 16 for _ in range(8)]
    tiny_text(img, 0, 2, "USES", 10)
    return img


def hexs(v):
    return "0x%X" % v


def c_array_rows(rows, indent="    "):
    return "\n".join(indent + ",".join(hexs(v) for v in r) + "," for r in rows)


def canvas_to_idx(cv):
    return [[0 if v is None else v for v in row] for row in cv.p]


def main():
    preview = None
    if "--preview" in sys.argv:
        preview = sys.argv[sys.argv.index("--preview") + 1]
        os.makedirs(preview, exist_ok=True)

    out = []
    w = out.append
    w("/*")
    w(" * Battle / bag graphics. GENERATED by tools/gen_battle_gfx.py -- do not edit.")
    w(" * GBA 4bpp tiles: 8 u32 per 8x8 tile (one per row, pixel x at bits 4x..4x+3),")
    w(" * multi-tile images in row-major tile order. Colours are RGB15.")
    w(" */")
    w("#ifndef GFX_BATTLE_H")
    w("#define GFX_BATTLE_H")
    w("")

    # ---- items
    items = build_items()
    item_tiles, item_pals, item_imgs = [], [], []
    import icons as icon_registry
    import bout_icons
    extra = bout_icons.icons(sys.modules[__name__]) + icon_registry.collect(sys.modules[__name__])
    names = [n.replace(' ', '_') for n in ITEM_NAMES] + [n for (n, _) in extra]
    items = list(items) + [cv for (_, cv) in extra]
    all_names = list(ITEM_NAMES) + [n for (n, _) in extra]
    for cv in items:
        img, pal = index_image(cv)
        assert pal[1] == WHITE
        item_imgs.append((img, pal))
        item_tiles.append([v for t in tiles_from_indices(img, 3, 3) for v in t])
        item_pals.append(pal)
    w("/* Bag icons, 24x24 (3x3 tiles), own palette each; index 0 transparent,")
    w(" * index 1 pure white. Order: " + ", ".join(ITEM_NAMES) + ". */")
    w("enum { " + ", ".join("ICON_%s" % n for n in names) + ", ICON_COUNT };")
    w("#define ITEM_ICON_COUNT %d" % len(items))
    w("static const u32 item_icon_gfx[%d][9 * 8] = {" % len(items))
    for n, t in zip(all_names, item_tiles):
        w("    { /* %s */" % n)
        w(c_array_rows([t[i:i + 8] for i in range(0, len(t), 8)], "        "))
        w("    },")
    w("};")
    w("static const u16 item_icon_pal[%d][16] = {" % len(items))
    for n, pal in zip(all_names, item_pals):
        w("    {" + ",".join(hexs(rgb15(c)) for c in pal) + "}, /* %s */" % n)
    w("};")
    w("")

    # ---- lanterns
    frames = lantern_frames()
    w("/* Thrown lantern, 16x16 OBJ frames (2x2 tiles): 0 closed, 1 wobble left,")
    w(" * 2 wobble right, 3 open with light spilling out. Palettes: LANTERN,")
    w(" * PRISM LANTERN, STAR LANTERN and the crafted ones. (Kept under the old capsule_* names.) */")
    w("#define LANTERN_FRAMES 4")
    w("static const u32 capsule_gfx[4][4 * 8] = {")
    cap_imgs = []
    for f in frames:
        img = [[0 if r is None else LAN_INDEX[r] for r in row] for row in f.p]
        cap_imgs.append(img)
        t = [v for tt in tiles_from_indices(img, 2, 2) for v in tt]
        w("    {")
        w(c_array_rows([t[i:i + 8] for i in range(0, 32, 8)], "        "))
        w("    },")
    w("};")
    cap_pals = []
    for var in CAPSULE_VARIANTS:
        pal = [(0, 0, 0)] * 16
        for role, idx in LAN_INDEX.items():
            pal[idx] = C(*LAN_VARIANTS[var][role])
        cap_pals.append(pal)
    w("/* Thrown-lantern palettes in LK_* order: " + ", ".join(CAPSULE_VARIANTS) + ". */")
    w("#define CAPSULE_PAL_COUNT %d" % len(CAPSULE_VARIANTS))
    w("static const u16 capsule_pal[CAPSULE_PAL_COUNT][16] = {")
    for var, pal in zip(CAPSULE_VARIANTS, cap_pals):
        w("    {" + ",".join(hexs(rgb15(c)) for c in pal) + "}, /* %s */" % var)
    w("};")
    w("/* 8x8 lantern marks (lantern palette): 0 lit (wild HUD, a warden's")
    w(" * ready kin), 1 unlit (a warden's dozing kin). */")
    w("static const u32 lantern_mini_gfx[2 * 8] = {")
    for lit in (True, False):
        mimg = [[0 if r is None else LAN_INDEX[r] for r in row] for row in lantern_mini(lit).p]
        w(c_array_rows([tiles_from_indices(mimg, 1, 1)[0]]))
    w("};")
    w("")

    # ---- fx
    w("/* Move-effect particles, 16x16 OBJ (2x2 tiles), drawn with a value ramp:")
    w(" * 1 darkest/outline, 2 dark, 3 mid (main colour), 4 light, 5 highlight,")
    w(" * 6 white-hot core, 7/8/9 secondary dark/mid/light. 10-15 unused.")
    w(" * FX_BOLT tiles vertically, FX_BEAM and FX_THREAD tile horizontally. */")
    import bout_fx
    gmod = sys.modules[__name__]
    fx_list = [(n, FX_BUILDERS[n]()) for n in FX_NAMES] + bout_fx.fx(gmod)
    fxb_list = [(n, fn()) for n, fn in FX_BIG] + bout_fx.fx_big(gmod)
    w("enum {")
    names = ["FX_" + n for n, _ in fx_list]
    for i in range(0, len(names), 6):
        w("    " + ", ".join(names[i:i + 6]) + ",")
    w("    FX_COUNT")
    w("};")
    w("static const u32 fx_gfx[FX_COUNT][4 * 8] = {")
    fx_imgs = []
    for n, cv in fx_list:
        img = canvas_to_idx(cv)
        for row in img:
            for v in row:
                assert 0 <= v <= 9, (n, v)
        fx_imgs.append(img)
        t = [v for tt in tiles_from_indices(img, 2, 2) for v in tt]
        w("    { /* %s */" % n)
        w(c_array_rows([t[i:i + 8] for i in range(0, 32, 8)], "        "))
        w("    },")
    w("};")
    w("")

    # ---- big particles
    w("/* Big 32x32 particles (4x4 tiles), same value ramp as the small ones. */")
    w("enum { " + ", ".join("FXB_" + n for n, _ in fxb_list) + ", FXB_COUNT };")
    w("static const u32 fx_big_gfx[FXB_COUNT][16 * 8] = {")
    fxb_imgs = []
    for n, cv in fxb_list:
        img = canvas_to_idx(cv)
        for row in img:
            for v in row:
                assert 0 <= v <= 9, (n, v)
        fxb_imgs.append(img)
        t = [v for tt in tiles_from_indices(img, 4, 4) for v in tt]
        w("    { /* %s */" % n)
        w(c_array_rows([t[i:i + 8] for i in range(0, len(t), 8)], "        "))
        w("    },")
    w("};")
    w("")

    # ---- labels
    tabs = [label_tab("WEAK SPOT!", 3, 4), label_tab("RESISTED", 5, 6), label_tab("NO EFFECT", 7, 8)]
    w("/* Move-menu labels (BG canvas, palette bl_pal; index 1 = window paper):")
    w(" * 64x8 tabs WEAK SPOT! / RESISTED / NO EFFECT and a 16x8 USES caption. */")
    w("enum { BL_WEAK, BL_RESIST, BL_NONE, BL_TAB_COUNT };")
    w("static const u32 bl_tab_gfx[BL_TAB_COUNT][8 * 8] = {")
    for img in tabs:
        t = [v for tt in tiles_from_indices(img, 8, 1) for v in tt]
        w("    {")
        w(c_array_rows([t[i:i + 8] for i in range(0, len(t), 8)], "        "))
        w("    },")
    w("};")
    uses = label_uses()
    t = [v for tt in tiles_from_indices(uses, 2, 1) for v in tt]
    w("static const u32 bl_uses_gfx[2 * 8] = {")
    w(c_array_rows([t[i:i + 8] for i in range(0, len(t), 8)]))
    w("};")
    lp = LABEL_PAL + [(0, 0, 0)] * (16 - len(LABEL_PAL))
    w("static const u16 bl_pal[16] = {" + ",".join(hexs(rgb15(c)) for c in lp) + "};")
    w("")

    # ---- backgrounds
    scenes = {}
    import bout_scenes
    SCENES = (("meadow", paint_grass), ("forest", paint_forest), ("lake", paint_lake),
              ("ring", paint_arena), ("storm", paint_storm)) + tuple(bout_scenes.scenes(sys.modules[__name__]))
    for key, painter in SCENES:
        S = painter()
        tiles, mp, pals = pack_scene(S, key)
        assert len(tiles) <= 500, (key, len(tiles))
        # the packing must reproduce the painting exactly
        dec = decode_scene(tiles, mp, pals)
        assert dec == S, key
        scenes[key] = (S, tiles, mp, pals)
        K = key.upper()
        w("/* %s battle background: 240x160 BG, map rows 0..19 of a 32x32 screen." % K)
        w(" * Rows 14..19 (text box area) and cols 30,31 use the plain tile 0. */")
        w("#define BBG_%s_TILE_COUNT %d" % (K, len(tiles)))
        w("static const u32 bbg_%s_tiles[BBG_%s_TILE_COUNT * 8] = {" % (key, K))
        w(c_array_rows(tiles))
        w("};")
        w("static const u16 bbg_%s_map[20 * 32] = {" % key)
        w(c_array_rows([mp[i:i + 32] for i in range(0, len(mp), 32)]))
        w("};")
        w("static const u16 bbg_%s_pal[4][16] = {" % key)
        for pal in pals:
            w("    {" + ",".join(hexs(rgb15(c)) for c in pal) + "},")
        w("};")
        w("")
    w("/* Scenes in BSCENE_* order: " + ", ".join(k.upper() for k, _ in SCENES) + ". */")
    w("typedef struct { const u32 *tiles; int tile_count; const u16 *map; const u16 (*pal)[16]; } BattleSceneArt;")
    w("#define BBG_SCENE_COUNT %d" % len(SCENES))
    w("static const BattleSceneArt bbg_scenes[BBG_SCENE_COUNT] = {")
    for key, _ in SCENES:
        w("    { bbg_%s_tiles, BBG_%s_TILE_COUNT, bbg_%s_map, bbg_%s_pal }," % (key, key.upper(), key, key))
    w("};")
    w("")
    w("#endif /* GFX_BATTLE_H */")
    with open(OUT_H, "w") as f:
        f.write("\n".join(out) + "\n")
    print("wrote %s" % OUT_H)
    for key, (S, tiles, mp, pals) in scenes.items():
        used = sum(1 for p in pals if any(c != (0, 0, 0) for c in p[1:]))
        print("  %s: %d tiles, %d palette banks" % (key, len(tiles), used))

    if preview:
        write_previews(preview, item_imgs, cap_imgs, cap_pals, fx_imgs, scenes, fxb_imgs, tabs)


def write_previews(d, item_imgs, cap_imgs, cap_pals, fx_imgs, scenes, fxb_imgs=(), tabs=()):
    S = 4
    cell = 24 * S + 12
    sh = Sheet(8 * cell + 12, 3 * cell + 12)
    for i, (img, pal) in enumerate(item_imgs):
        x = 12 + (i % 8) * cell
        y = 12 + (i // 8) * cell
        sh.rect(x - 2, y - 2, 24 * S + 4, 24 * S + 4, (232, 232, 236))
        sh.rect(x, y, 24 * S, 24 * S, (255, 255, 255))
        # draw as the engine does on white menus: transparent -> index 1
        sh.blit([[v if v else 1 for v in row] for row in img], x, y, S, pal=pal)
    sh.save(os.path.join(d, "items.png"))

    S = 6
    cell = 16 * S + 10
    sh = Sheet(4 * cell + 10, 6 * cell + 10, bg=(96, 96, 108))
    for vi, pal in enumerate(cap_pals):
        for fi, img in enumerate(cap_imgs):
            for k, bgc in enumerate([(144, 208, 104), (248, 248, 248)]):
                x = 10 + fi * cell
                y = 10 + (vi * 2 + k) * cell
                sh.rect(x, y, 16 * S, 16 * S, bgc)
                sh.blit(img, x, y, S, pal=pal)
    sh.save(os.path.join(d, "lanterns.png"))

    S = 4
    sh = Sheet(max(2, len(fxb_imgs)) * (32 * S + 10) + 10, 32 * S + 20, bg=(56, 64, 88))
    pal = fx_palette((255, 200, 64), (255, 240, 176))
    for i, img in enumerate(fxb_imgs):
        sh.blit(img, 10 + i * (32 * S + 10), 10, S, pal=pal)
    sh.save(os.path.join(d, "fx_big.png"))
    S = 4
    sh = Sheet(64 * S + 20, 3 * 8 * S + 40, bg=(248, 248, 248))
    for i, img in enumerate(tabs):
        sh.blit(img, 10, 10 + i * (8 * S + 10), S, pal=LABEL_PAL + [(0, 0, 0)] * 5)
    sh.save(os.path.join(d, "labels.png"))

    S = 4
    cell = 16 * S + 4
    per_row = 11
    rows_per = (len(fx_imgs) + per_row - 1) // per_row
    bw = per_row * cell + 8
    bh = rows_per * cell + 8
    sh = Sheet(2 * bw + 8, 3 * bh + 8, bg=(72, 72, 84))
    bgs = [(200, 224, 176), (120, 160, 128), (232, 232, 240), (56, 64, 88), (248, 240, 216), (176, 200, 232)]
    for j, (pn, m, sc) in enumerate(FX_PREVIEW_PAIRS):
        pal = fx_palette(m, sc)
        bx = 8 + (j % 2) * bw
        by = 8 + (j // 2) * bh
        for i, img in enumerate(fx_imgs):
            x = bx + (i % per_row) * cell
            y = by + (i // per_row) * cell
            sh.rect(x, y, 16 * S, 16 * S, bgs[j])
            sh.blit(img, x, y, S, pal=pal)
    sh.save(os.path.join(d, "fx.png"))

    for key, (Sx, tiles, mp, pals) in scenes.items():
        sc = 2
        img = decode_scene(tiles, mp, pals)
        sh = Sheet(SW * sc, SH * sc)
        sh.blit(img, 0, 0, sc)
        # placeholder monsters (enemy feet ~y66, ally back sprite bottom y112)
        for (x, y, ww, hh, col) in [(144, 2, 64, 64, (232, 72, 72)), (32, 48, 64, 64, (72, 104, 232))]:
            for t in range(2):
                sh.rect(x * sc, y * sc + t, ww * sc, 1, col)
                sh.rect(x * sc, (y + hh) * sc - 1 - t, ww * sc, 1, col)
                sh.rect(x * sc + t, y * sc, 1, hh * sc, col)
                sh.rect((x + ww) * sc - 1 - t, y * sc, 1, hh * sc, col)
        sh.rect(0, TEXT_Y * sc, SW * sc, (SH - TEXT_Y) * sc, (32, 36, 48))
        sh.rect(4 * sc, (TEXT_Y + 4) * sc, (SW - 8) * sc, (SH - TEXT_Y - 8) * sc, (248, 248, 248))
        sh.save(os.path.join(d, "bbg_%s.png" % key))


if __name__ == "__main__":
    main()
