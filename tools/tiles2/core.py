"""Core pixel-art toolkit for the second-generation tilesets (tools/tiles2).

Images hold colour *role names* (keys of a set's palette) or None for
transparent pixels, exactly like tools/pixelart.py, so one drawing can be
encoded against any palette variant (seasons, night, lustre...).

Standard library only. Everything is deterministic: noise comes from integer
hashes, never from `random`, so regenerating a sheet is bit-for-bit stable.
"""

import math
import struct
import zlib

# ---------------------------------------------------------------------------
# Colour helpers (GBA BGR555)
# ---------------------------------------------------------------------------


def hex_rgb(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def q15(rgb):
    """Quantise to what the GBA shows: 5 bits per channel, expanded back."""
    out = []
    for c in rgb:
        v = max(0, min(255, int(round(c)))) >> 3
        out.append((v << 3) | (v >> 2))
    return tuple(out)


def c15(rgb):
    r, g, b = (max(0, min(255, int(round(c)))) >> 3 for c in rgb)
    return r | (g << 5) | (b << 10)


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


# ---------------------------------------------------------------------------
# Deterministic noise
# ---------------------------------------------------------------------------

def hash32(*vals):
    h = 0x811C9DC5
    for v in vals:
        v = int(v) & 0xFFFFFFFF
        for _ in range(4):
            h ^= v & 0xFF
            h = (h * 0x01000193) & 0xFFFFFFFF
            v >>= 8
    h ^= h >> 15
    h = (h * 0x2C1B3C6D) & 0xFFFFFFFF
    h ^= h >> 12
    h = (h * 0x297A2D39) & 0xFFFFFFFF
    h ^= h >> 15
    return h


def rnd(*vals):
    """Uniform float in [0, 1) from integer inputs."""
    return hash32(*vals) / 4294967296.0


BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def bayer(x, y):
    """Ordered-dither threshold in [0, 1)."""
    return (BAYER4[y & 3][x & 3] + 0.5) / 16.0


def value_noise(x, y, scale, seed, wrap=None):
    """Smooth value noise in [0, 1). wrap=(W, H) makes it tile (in px)."""
    fx, fy = x / scale, y / scale
    ix, iy = int(math.floor(fx)), int(math.floor(fy))
    tx, ty = fx - ix, fy - iy
    tx = tx * tx * (3 - 2 * tx)
    ty = ty * ty * (3 - 2 * ty)

    def g(a, b):
        if wrap:
            a %= max(1, int(round(wrap[0] / scale)))
            b %= max(1, int(round(wrap[1] / scale)))
        return rnd(a, b, seed)
    a = g(ix, iy) + (g(ix + 1, iy) - g(ix, iy)) * tx
    b = g(ix, iy + 1) + (g(ix + 1, iy + 1) - g(ix, iy + 1)) * tx
    return a + (b - a) * ty


def fbm(x, y, scale, seed, octaves=3, wrap=None):
    v, amp, tot = 0.0, 1.0, 0.0
    for o in range(octaves):
        v += value_noise(x, y, scale, seed + o * 101, wrap) * amp
        tot += amp
        amp *= 0.5
        scale = max(1.0, scale / 2)
    return v / tot


def jitter_points(w, h, cell, seed, jitter=0.8, wrap=False):
    """Poisson-ish points: one per grid cell, jittered. Returns [(x, y)]."""
    pts = []
    nx, ny = max(1, int(round(w / cell))), max(1, int(round(h / cell)))
    cw, ch = w / nx, h / ny
    for j in range(ny):
        for i in range(nx):
            px = (i + 0.5 + (rnd(i, j, seed) - 0.5) * jitter) * cw
            py = (j + 0.5 + (rnd(i, j, seed + 7) - 0.5) * jitter) * ch
            pts.append((px, py))
    return pts


def worley(x, y, pts, wrap=None):
    """(index of nearest point, d1, d2). wrap=(W, H) for tiling."""
    best = (1e9, -1)
    second = 1e9
    for i, (px, py) in enumerate(pts):
        dx, dy = x - px, y - py
        if wrap:
            W, H = wrap
            dx = (dx + W / 2) % W - W / 2
            dy = (dy + H / 2) % H - H / 2
        d = math.hypot(dx, dy)
        if d < best[0]:
            second = best[0]
            best = (d, i)
        elif d < second:
            second = d
    return best[1], best[0], second


# ---------------------------------------------------------------------------
# Image of role names
# ---------------------------------------------------------------------------

class Img:
    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.p = [[fill] * w for _ in range(h)]

    # -- access --------------------------------------------------------
    def get(self, x, y, default=None):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.p[y][x]
        return default

    def set(self, x, y, c):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    def setw(self, x, y, c):
        """Set with wrap-around (for tiling textures)."""
        self.p[y % self.h][x % self.w] = c

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h and self.p[y][x] is not None

    # -- whole-image ops ---------------------------------------------------
    def copy(self):
        o = Img(self.w, self.h)
        o.p = [r[:] for r in self.p]
        return o

    def crop(self, x0, y0, w, h):
        o = Img(w, h)
        for y in range(h):
            for x in range(w):
                o.p[y][x] = self.get(x0 + x, y0 + y)
        return o

    def paste(self, src, ox, oy, only=None):
        """Draw src's opaque pixels at (ox, oy). only: mask Img/None."""
        for y in range(src.h):
            for x in range(src.w):
                c = src.p[y][x]
                if c is not None and (only is None or only.get(ox + x, oy + y) is not None):
                    self.set(ox + x, oy + y, c)
        return self

    def under(self, src, ox=0, oy=0):
        """Fill this image's transparent pixels from src (draw src beneath)."""
        for y in range(self.h):
            for x in range(self.w):
                if self.p[y][x] is None:
                    c = src.get(x - ox, y - oy)
                    if c is not None:
                        self.p[y][x] = c
        return self

    def flip_h(self):
        o = Img(self.w, self.h)
        o.p = [r[::-1] for r in self.p]
        return o

    def flip_v(self):
        o = Img(self.w, self.h)
        o.p = [r[:] for r in self.p[::-1]]
        return o

    def rot90(self):
        """Clockwise."""
        o = Img(self.h, self.w)
        for y in range(self.h):
            for x in range(self.w):
                o.p[x][self.h - 1 - y] = self.p[y][x]
        return o

    def replace(self, mapping):
        o = self.copy()
        for r in o.p:
            for i, c in enumerate(r):
                if c in mapping:
                    r[i] = mapping[c]
        return o

    def colors(self):
        return set(c for r in self.p for c in r if c is not None)

    def mask(self):
        return [[c is not None for c in r] for r in self.p]

    # -- drawing -------------------------------------------------------------
    def fill(self, c):
        for r in self.p:
            for i in range(len(r)):
                r[i] = c
        return self

    def rect(self, x0, y0, x1, y1, c):
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)
        return self

    def hline(self, x0, x1, y, c):
        x0, x1, y = int(x0), int(x1), int(y)
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.set(x, y, c)

    def vline(self, x, y0, y1, c):
        x, y0, y1 = int(x), int(y0), int(y1)
        for y in range(min(y0, y1), max(y0, y1) + 1):
            self.set(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def ellipse(self, cx, cy, rx, ry, c):
        """Filled ellipse, centre may be fractional (use .5 for even sizes)."""
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                dx = (x + 0.5 - cx) / max(rx, 0.01)
                dy = (y + 0.5 - cy) / max(ry, 0.01)
                if dx * dx + dy * dy <= 1.0:
                    self.set(x, y, c)

    def draw(self, text, legend, ox=0, oy=0):
        """Stamp a text grid; chars missing from legend (and '.') skip."""
        rows = [r for r in text.strip('\n').split('\n')]
        rows = [r.strip() for r in rows if r.strip()]
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch in legend and legend[ch] is not None:
                    self.set(ox + x, oy + y, legend[ch])
        return self

    def outline(self, c, inner=None, light=None, diagonal=False):
        """Selective outline: transparent pixels touching the shape become
        c. If light is given, outline pixels on the top/left (lit) side use
        light instead. inner: also darken the shape's own edge pixels."""
        o = self.copy()
        nb = ((1, 0), (-1, 0), (0, 1), (0, -1))
        if diagonal:
            nb = nb + ((1, 1), (-1, 1), (1, -1), (-1, -1))
        for y in range(self.h):
            for x in range(self.w):
                if self.p[y][x] is None:
                    touch = [(dx, dy) for dx, dy in nb if self.inside(x + dx, y + dy)]
                    if touch:
                        lit = light is not None and all(dx >= 0 and dy >= 0 for dx, dy in touch) \
                            and any(dx > 0 or dy > 0 for dx, dy in touch)
                        o.p[y][x] = light if lit else c
        return o

    def edge_pixels(self):
        """Opaque pixels that touch transparency or the image border."""
        out = []
        for y in range(self.h):
            for x in range(self.w):
                if self.p[y][x] is None:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if not self.inside(x + dx, y + dy):
                        out.append((x, y, dx, dy))
                        break
        return out


def G(text, legend):
    """Parse a text grid into an Img (rows stripped, '.' = transparent)."""
    rows = [r.strip() for r in text.strip('\n').split('\n')]
    rows = [r for r in rows if r]
    w = max(len(r) for r in rows)
    img = Img(w, len(rows))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            img.p[y][x] = legend.get(ch)
    return img


# ---------------------------------------------------------------------------
# Volumetric shading: height fields -> ramp colours
# ---------------------------------------------------------------------------

LIGHT = (-0.55, -0.75, 0.9)   # from the upper left, towards the viewer


def _norm(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / l for c in v)


class Height:
    """A height field over a w x h grid; None = outside the shape."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.v = [[None] * w for _ in range(h)]

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.v[y][x]
        return None

    def add_ellipsoid(self, cx, cy, rx, ry, top=1.0, z0=0.0, mode='max'):
        """Union (max) an ellipsoid dome of peak z0+top*ry."""
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if not (0 <= x < self.w and 0 <= y < self.h):
                    continue
                dx = (x + 0.5 - cx) / rx
                dy = (y + 0.5 - cy) / ry
                q = 1.0 - dx * dx - dy * dy
                if q < 0:
                    continue
                z = z0 + math.sqrt(q) * ry * top
                cur = self.v[y][x]
                if cur is None or (mode == 'max' and z > cur):
                    self.v[y][x] = z
                elif mode == 'add':
                    self.v[y][x] = cur + z
        return self

    def add_box(self, x0, y0, x1, y1, z=0.0):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if 0 <= x < self.w and 0 <= y < self.h:
                    cur = self.v[y][x]
                    if cur is None or z > cur:
                        self.v[y][x] = z
        return self

    def normal(self, x, y):
        c = self.v[y][x]

        def s(xx, yy):
            v = self.get(xx, yy)
            return c - 1.2 if v is None else v
        dx = (s(x + 1, y) - s(x - 1, y)) * 0.5
        dy = (s(x, y + 1) - s(x, y - 1)) * 0.5
        return _norm((-dx, -dy, 1.0))

    def light(self, x, y, light=LIGHT):
        n = self.normal(x, y)
        L = _norm(light)
        return max(0.0, sum(n[i] * L[i] for i in range(3)))


def shade(height, ramp, img=None, light=LIGHT, bias=0.0, contrast=1.0,
          dither=0.35, ao=None, ox=0, oy=0, seed=0, jitter=0.0):
    """Paint a height field with a ramp (dark -> light).

    ao(x, y) -> extra darkening in [0, 1] (occlusion / global form).
    dither: fraction of a ramp step blended with ordered dither.
    jitter: random per-pixel lighting noise (texture)."""
    if img is None:
        img = Img(height.w, height.h)
    n = len(ramp)
    Ln = _norm(light)
    for y in range(height.h):
        for x in range(height.w):
            if height.v[y][x] is None:
                continue
            nrm = height.normal(x, y)
            lum = sum(nrm[i] * Ln[i] for i in range(3))
            lum = (lum - 0.35) * contrast + 0.55 + bias
            if ao:
                lum -= ao(x, y)
            if jitter:
                lum += (rnd(x, y, seed) - 0.5) * jitter
            t = lum * (n - 1)
            t += (bayer(x + ox, y + oy) - 0.5) * dither * 2
            k = max(0, min(n - 1, int(round(t))))
            img.set(x + ox, y + oy, ramp[k])
    return img


def rim_outline(img, dark, light=None, mid=None):
    """Colour the shape's own boundary pixels: dark on the bottom/right,
    optional lighter tone on the top/left (selective outline)."""
    o = img.copy()
    for (x, y, dx, dy) in img.edge_pixels():
        up_left = not img.inside(x - 1, y) or not img.inside(x, y - 1)
        down_right = not img.inside(x + 1, y) or not img.inside(x, y + 1)
        if down_right or light is None:
            o.p[y][x] = dark
        elif up_left:
            o.p[y][x] = light if mid is None else mid
    return o


def clumps(w, h, n_or_pts, seed, rmin, rmax, region=None):
    """Clump centres for foliage: list of (x, y, r)."""
    out = []
    if isinstance(n_or_pts, int):
        k = 0
        tries = 0
        while len(out) < n_or_pts and tries < n_or_pts * 60:
            tries += 1
            x = rnd(tries, 1, seed) * w
            y = rnd(tries, 2, seed) * h
            if region and not region(x, y):
                continue
            r = rmin + rnd(tries, 3, seed) * (rmax - rmin)
            out.append((x, y, r))
            k += 1
    else:
        for i, (x, y) in enumerate(n_or_pts):
            r = rmin + rnd(i, 3, seed) * (rmax - rmin)
            out.append((x, y, r))
    return out


# ---------------------------------------------------------------------------
# PNG output
# ---------------------------------------------------------------------------

def write_png_rgba(path, w, h, rows):
    """rows: list of h lists of (r, g, b, a) tuples."""
    raw = bytearray()
    for r in rows:
        raw.append(0)
        for (R, Gc, B, A) in r:
            raw += bytes((R, Gc, B, A))

    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xFFFFFFFF)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def read_png_rgba(path):
    """Minimal reader for 8-bit RGB/RGBA non-interlaced PNGs (our output)."""
    with open(path, 'rb') as f:
        data = f.read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', path
    pos, idat, w = 8, b'', 0
    while pos < len(data):
        ln, = struct.unpack('>I', data[pos:pos + 4])
        t = data[pos + 4:pos + 8]
        d = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if t == b'IHDR':
            w, h, bd, ct, _, _, il = struct.unpack('>IIBBBBB', d)
            assert bd == 8 and ct in (2, 6) and il == 0, 'unsupported PNG ' + path
            bpp = 4 if ct == 6 else 3
        elif t == b'IDAT':
            idat += d
    raw = zlib.decompress(idat)
    stride = w * bpp
    rows, prev = [], bytearray(stride)
    p = 0
    for _ in range(h):
        ft = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            if ft == 1:
                line[i] = (line[i] + a) & 255
            elif ft == 2:
                line[i] = (line[i] + b) & 255
            elif ft == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif ft == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        prev = line
        row = []
        for x in range(w):
            px = line[x * bpp:(x + 1) * bpp]
            row.append((px[0], px[1], px[2], px[3] if bpp == 4 else 255))
        rows.append(row)
    return w, h, rows


def render(img, palette, scale=1, bg=None):
    """Img of role names -> RGBA rows using palette {role: (r, g, b)}."""
    rows = []
    for y in range(img.h):
        row = []
        for x in range(img.w):
            c = img.p[y][x]
            if c is None:
                px = bg(x, y) if callable(bg) else (bg + (255,) if bg else (0, 0, 0, 0))
            else:
                r, g, b = q15(palette[c])
                px = (r, g, b, 255)
            row.extend([px] * scale)
        for _ in range(scale):
            rows.append(list(row))
    return rows


def save(img, palette, path, scale=1, bg=None):
    write_png_rgba(path, img.w * scale, img.h * scale, render(img, palette, scale, bg))


# ---------------------------------------------------------------------------
# Tiny label font (3x5) for preview sheets
# ---------------------------------------------------------------------------

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
    '_': '000000000000111', '-': '000000111000000', '.': '000000000000010',
    ' ': '000000000000000', '/': '001001010100100', ':': '000010000010000',
    '(': '010100100100010', ')': '010001001001010', '+': '000010111010000',
    '#': '101111101111101', ',': '000000000010100', '%': '101001010100101',
    '=': '000111000111000', "'": '010010000000000', '&': '010101010101011',
    '>': '100010001010100', '<': '001010100010001', '!': '010010010000010',
    '?': '110001010000010', 'x': '000101010101000',
}


def draw_text(rows, x, y, text, rgba=(255, 255, 255, 255), scale=1):
    """Draw text into RGBA rows (in place)."""
    H = len(rows)
    W = len(rows[0]) if H else 0
    cx = x
    for ch in text.upper():
        g = FONT.get(ch, FONT['?'])
        for j in range(5):
            for i in range(3):
                if g[j * 3 + i] == '1':
                    for sy in range(scale):
                        for sx in range(scale):
                            px, py = cx + i * scale + sx, y + j * scale + sy
                            if 0 <= px < W and 0 <= py < H:
                                rows[py][px] = rgba
        cx += 4 * scale
    return cx
