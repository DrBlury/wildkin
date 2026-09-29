"""Committed tiles2 sheets as images for the field generator.

A Kit wraps one set (assets/tiles2/<set>/<set>.png + .json). Pixels become
colour names 'T2:rrggbb' (the exact, already GBA-quantised colour), so the
old encoder in tools/gen_field_gfx.py can take them as they are: two roles
that share a colour are the same name, and a bank is simply the set of
colours its roles have.

    k = Kit('verdant')
    k.img('tree')                 whole entry (frame 0) as an Img
    k.cells('fence', 2, 0)        one 16x16 cell of an entry (col, row)
    k.cells('forest', 0, 0, 3, 2) a region of cells
    k.frames('water')             every animation frame of an entry
    k.role('g3')                  colour name of a palette role
    k.paint(img)                  a painter's role image -> colour names
    k.banks                       <= 8 lists of colour names (bank 0..7)
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
T2 = os.path.dirname(HERE)
if T2 not in sys.path:
    sys.path.insert(0, T2)

import gba                     # noqa: E402
from core import Img, hex_rgb, q15   # noqa: E402

_CACHE = {}


def cname(rgb):
    return 'T2:%02x%02x%02x' % tuple(rgb)


def rgb_of(name):
    h = name[3:]
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


class Kit:
    def __init__(self, name, variant=None):
        self.name = name
        self.ts = gba.load(name)
        self.man = self.ts['manifest']
        self.entries = self.ts['entries']
        pal = dict(self.man['palette'])
        if variant:
            pal.update(self.man['variants'][variant])
        self.roles = {r: cname(q15(hex_rgb(h))) for r, h in pal.items()}
        banks = []
        for b in self.man['banks']:
            names = []
            for r in b:
                n = self.roles[r]
                if n not in names:
                    names.append(n)
            banks.append(names)
        self.banks = banks
        self._rows = self.ts['rows']

    # -- colours -------------------------------------------------------
    def role(self, r):
        return self.roles[r]

    def colors(self):
        """{colour name: (r, g, b)} for every colour of the set."""
        return {n: rgb_of(n) for n in self.roles.values()}

    def paint(self, img):
        """Role image (a tiles2 painter's output) -> colour names."""
        out = Img(img.w, img.h)
        for y in range(img.h):
            for x in range(img.w):
                c = img.p[y][x]
                out.p[y][x] = None if c is None else (c if c.startswith('T2:') else self.roles[c])
        return out

    # -- sheet access ----------------------------------------------------
    def _px(self, X, Y):
        r, g, b, a = self._rows[Y][X]
        return None if a < 128 else cname((r, g, b))

    def entry(self, name):
        if name not in self.entries:
            raise KeyError('%s: no entry %r' % (self.name, name))
        return self.entries[name]

    def has(self, name):
        return name in self.entries

    def nframes(self, name):
        e = self.entry(name)
        return len(e.get('frames') or [0])

    def cells(self, name, cx=0, cy=0, cw=1, ch=1, frame=0):
        e = self.entry(name)
        fr = e.get('frames') or [[e['x'], e['y']]]
        fx, fy = fr[frame % len(fr)]
        if cx + cw > e['w'] or cy + ch > e['h']:
            raise ValueError('%s.%s: cells %d,%d+%dx%d outside %dx%d' % (
                self.name, name, cx, cy, cw, ch, e['w'], e['h']))
        img = Img(cw * 16, ch * 16)
        for y in range(ch * 16):
            for x in range(cw * 16):
                img.p[y][x] = self._px((fx + cx) * 16 + x, (fy + cy) * 16 + y)
        return img

    def img(self, name, frame=0):
        e = self.entry(name)
        return self.cells(name, 0, 0, e['w'], e['h'], frame)

    def frames(self, name):
        return [self.img(name, f) for f in range(self.nframes(name))]

    def size(self, name):
        e = self.entry(name)
        return e['w'], e['h']


def kit(name, variant=None):
    key = (name, variant)
    if key not in _CACHE:
        _CACHE[key] = Kit(name, variant)
    return _CACHE[key]


# ---------------------------------------------------------------------------
# image helpers
# ---------------------------------------------------------------------------

def over(base, top, ox=0, oy=0):
    """top pasted over a copy of base (transparent pixels of top keep base)."""
    out = base.copy()
    for y in range(top.h):
        for x in range(top.w):
            c = top.p[y][x]
            if c is not None and 0 <= x + ox < out.w and 0 <= y + oy < out.h:
                out.p[y + oy][x + ox] = c
    return out


def tile(img, w, h):
    """Repeat img to fill w x h pixels."""
    out = Img(w, h)
    for y in range(h):
        for x in range(w):
            out.p[y][x] = img.p[y % img.h][x % img.w]
    return out


def minus(img, ground):
    """img with every pixel equal to the (tiled) ground image made
    transparent: an opaque autotile -> the overlay drawn over that ground."""
    out = img.copy()
    for y in range(img.h):
        for x in range(img.w):
            if img.p[y][x] == ground.p[y % ground.h][x % ground.w]:
                out.p[y][x] = None
    return out


# RPG Maker XP (rmxp16) block -> engine quadrant variants (docs/TILES2.md 4.3)
QUADS = ((0, 0), (8, 0), (0, 8), (8, 8))
_SIDE = {0: (0, 2), 2: (0, 2), 1: (2, 2), 3: (2, 2)}
_TOPB = {0: (1, 1), 1: (1, 1), 2: (1, 3), 3: (1, 3)}
_OUTER = {0: (0, 1), 1: (2, 1), 2: (0, 3), 3: (2, 3)}


def rmxp_cell(c, v):
    """Block cell (col, row) holding quadrant c of engine variant v."""
    if v == 0:
        return (1, 2)
    if v == 1:
        return (2, 0)
    if v == 2:
        return _SIDE[c]
    if v == 3:
        return _TOPB[c]
    return _OUTER[c]


def rmxp_quad(block, c, v):
    """8x8 pixel list of quadrant c, variant v of a 48x64 rmxp16 block."""
    bx, by = rmxp_cell(c, v)
    qx, qy = QUADS[c]
    x0, y0 = bx * 16 + qx, by * 16 + qy
    return [block.p[y0 + y][x0 + x] for y in range(8) for x in range(8)]


def quad_pix(img, c, x0=0, y0=0):
    qx, qy = QUADS[c]
    return [img.p[y0 + qy + y][x0 + qx + x] for y in range(8) for x in range(8)]
