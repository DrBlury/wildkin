#!/usr/bin/env python3
"""Shared pixel-art helpers for the field art generators.

Images hold colour *names* (keys of a colour table) or None for
transparent pixels, so art can be authored once and encoded against any
tileset palette. Standard library only.
"""

import struct
import zlib


def c15(rgb):
    r, g, b = rgb
    return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)


def c15_to_rgb(v):
    r, g, b = v & 31, (v >> 5) & 31, (v >> 10) & 31
    return ((r << 3) | (r >> 2), (g << 3) | (g >> 2), (b << 3) | (b >> 2))



class Img:
    def __init__(self, w, h, fill=None):
        self.w, self.h = w, h
        self.p = [[fill] * w for _ in range(h)]

    def get(self, x, y, default=None):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.p[y][x]
        return default

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    def copy(self):
        o = Img(self.w, self.h)
        o.p = [row[:] for row in self.p]
        return o

    def crop(self, x0, y0, w, h):
        o = Img(w, h)
        for y in range(h):
            for x in range(w):
                o.p[y][x] = self.get(x0 + x, y0 + y)
        return o

    def paste(self, src, ox, oy):
        for y in range(src.h):
            for x in range(src.w):
                c = src.p[y][x]
                if c is not None:
                    self.set(ox + x, oy + y, c)

    def flip_h(self):
        o = Img(self.w, self.h)
        o.p = [row[::-1] for row in self.p]
        return o

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def replace(self, mapping):
        o = self.copy()
        for row in o.p:
            for i, c in enumerate(row):
                if c in mapping:
                    row[i] = mapping[c]
        return o


def G(text, legend):
    """Parse a pixel grid. Rows are whitespace-stripped lines."""
    rows = [r.strip() for r in text.strip('\n').split('\n')]
    rows = [r for r in rows if r]
    w = max(len(r) for r in rows)
    img = Img(w, len(rows))
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch not in legend:
                raise KeyError('grid char %r not in legend (row %d: %s)' % (ch, y, r))
            img.p[y][x] = legend[ch]
    return img


def tex_fill(img, tex, x0=0, y0=0, x1=None, y1=None, only_none=False):
    """Fill a region with a 16x16-periodic texture at absolute coordinates."""
    x1 = img.w - 1 if x1 is None else x1
    y1 = img.h - 1 if y1 is None else y1
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if only_none and img.get(x, y) is not None:
                continue
            img.set(x, y, tex.p[y % tex.h][x % tex.w])


def hash2(x, y, s=0):
    h = (x * 374761393 + y * 668265263 + s * 2246822519) & 0xffffffff
    h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
    return (h ^ (h >> 16)) & 0xffff



def write_png(path, w, h, rgb_rows):
    raw = bytearray()
    for row in rgb_rows:
        raw.append(0)
        for (r, g, b) in row:
            raw += bytes((r, g, b))

    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def scale_rows(rows, s):
    out = []
    for row in rows:
        r2 = []
        for px in row:
            r2.extend([px] * s)
        for _ in range(s):
            out.append(r2)
    return out



class Canvas:
    def __init__(self, w, h, bg=(0, 0, 0)):
        self.w, self.h = w, h
        self.rows = [[bg] * w for _ in range(h)]

    def put(self, x, y, rgb):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.rows[y][x] = rgb

    def entry(self, tiles, pals, ent, x0, y0, transparent):
        t, hf, vf, b = ent & 1023, (ent >> 10) & 1, (ent >> 11) & 1, ent >> 12
        idx = tiles[t]
        for y in range(8):
            for x in range(8):
                i = idx[(7 - y if vf else y) * 8 + (7 - x if hf else x)]
                if i == 0 and transparent:
                    continue
                self.put(x0 + x, y0 + y, c15_to_rgb(pals[b][i]))

    def meta(self, tiles, pals, ents, x0, y0, transparent=False):
        for k, (dx, dy) in enumerate(((0, 0), (8, 0), (0, 8), (8, 8))):
            self.entry(tiles, pals, ents[k], x0 + dx, y0 + dy, transparent)

    def sprite(self, words_tiles, pal, x0, y0, tw, th, hflip=False):
        """words_tiles: list of tiles (each 8 u32 rows), row-major tw x th."""
        for ty in range(th):
            for tx in range(tw):
                words = words_tiles[ty * tw + tx]
                for y in range(8):
                    for x in range(8):
                        i = (words[y] >> (4 * x)) & 15
                        if i == 0:
                            continue
                        px = tx * 8 + x
                        if hflip:
                            px = tw * 8 - 1 - px
                        self.put(x0 + px, y0 + ty * 8 + y, c15_to_rgb(pal[i]))

    def save(self, path, scale=1):
        write_png(path, self.w * scale, self.h * scale, scale_rows(self.rows, scale))




def shade_clumps(w, h, clumps, ramp, outline, shadow_edge=True, seed=0,
                 dither=True, clip=None):
    """Render overlapping round leaf clumps (back to front) with top-left
    light. ramp: colors light->dark. Returns (img, mask)."""
    img = Img(w, h)
    owner = [[-1] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            px, py = x + 0.5, y + 0.5
            for i in range(len(clumps) - 1, -1, -1):
                cx, cy, rx, ry = clumps[i]
                if ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 <= 1.0:
                    owner[y][x] = i
                    break
            if clip and not clip(x, y):
                owner[y][x] = -1
    n = len(ramp)
    for y in range(h):
        for x in range(w):
            i = owner[y][x]
            if i < 0:
                continue
            cx, cy, rx, ry = clumps[i]
            nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            b = -(nx * 0.55 + ny * 0.85) * 0.9 + 0.35 - 0.35 * (nx * nx + ny * ny)
            # b roughly in [-1, 1]; map to ramp index
            t = (1.0 - b) / 2.0 * (n - 1)
            if dither:
                t += ((hash2(x, y, seed) & 255) / 255.0 - 0.5) * 0.7
            k = max(0, min(n - 1, int(round(t))))
            if shadow_edge:
                for (dx, dy) in ((0, -1), (-1, 0), (0, -2)):
                    j = owner[y + dy][x + dx] if 0 <= y + dy < h and 0 <= x + dx < w else -1
                    if j > i:
                        k = n - 1 if (dx, dy) != (0, -2) else max(k, n - 2)
                        break
            img.p[y][x] = ramp[k]
    for y in range(h):
        for x in range(w):
            if owner[y][x] >= 0:
                continue
            for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < w and 0 <= yy < h and owner[yy][xx] >= 0:
                    img.p[y][x] = outline
                    break
    return img, owner


# ---------------------------------------------------------------------------
# Decor catalog entries
# ---------------------------------------------------------------------------

# Tileset registry order: fixes the TS_* ids in gfx_field.h (docs/EXPANSION.md 10.1).
SETS = ('town', 'wild', 'interior', 'city', 'coast', 'snow', 'cave', 'grim', 'crypt',
        'volcanic', 'dream', 'farm', 'tide', 'dusk', 'desert', 'jungle')


def _mask(spec, w, h, name, what):
    """'XX/.X' (rows split by '/', one char per 16x16 cell) -> bit mask."""
    if spec is None:
        return None
    rows = spec.split('/')
    if len(rows) != h or any(len(r) != w for r in rows):
        raise ValueError('%s: %s mask %r does not match %dx%d cells' % (name, what, spec, w, h))
    m = 0
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch not in '.X':
                raise ValueError('%s: %s mask uses %r (only X and .)' % (name, what, ch))
            if ch == 'X':
                m |= 1 << (y * w + x)
    return m


class Decor:
    """A transparent object placed over any ground.

    name   : C identifier suffix (DK_<name>)
    sets   : tilesets it can be used in: any of 'town', 'wild', 'interior'
    img    : Img whose size is a multiple of 16 (colour names / None)
    frames : instead of img, a list of equally sized Imgs (animated decor)
    period : frames between animation steps (animated decor)
    solid  : cells that block walking      (default: every cell not in top/floor)
    top    : cells drawn above people       (e.g. the upper half of a lamp post)
    floor  : cells that make the ground walkable (bridges, planks over water)
    doc    : one-line description (goes into the header)
    examine: what the game says when the player examines it (A); '' = nothing
    Masks are strings like 'XX/..' -- rows split by '/', one char per cell.
    """

    def __init__(self, name, sets, img=None, frames=None, solid=None, top=None,
                 floor=None, period=16, doc='', examine=''):
        self.name = name
        self.examine = examine
        self.sets = tuple(sets)
        for s in self.sets:
            if s not in SETS:
                raise ValueError('%s: unknown set %r' % (name, s))
        self.frames = list(frames) if frames else [img]
        f0 = self.frames[0]
        if f0.w % 16 or f0.h % 16:
            raise ValueError('%s: size %dx%d is not a multiple of 16' % (name, f0.w, f0.h))
        for f in self.frames:
            if (f.w, f.h) != (f0.w, f0.h):
                raise ValueError('%s: animation frames differ in size' % name)
        self.w, self.h = f0.w // 16, f0.h // 16
        if self.w * self.h > 16:
            raise ValueError('%s: at most 16 cells (got %dx%d)' % (name, self.w, self.h))
        self.period = period
        self.doc = doc
        full = (1 << (self.w * self.h)) - 1
        self.top = _mask(top, self.w, self.h, name, 'top') or 0
        self.floor = _mask(floor, self.w, self.h, name, 'floor') or 0
        s = _mask(solid, self.w, self.h, name, 'solid')
        self.solid = s if s is not None else full & ~self.top & ~self.floor
