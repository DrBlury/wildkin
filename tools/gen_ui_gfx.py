#!/usr/bin/env python3
"""Generate src/gfx_ui.h: the WILDKIN UI art for the GBA engine.

Contents: a 14-row variable-width dialogue font, a small HUD digit font,
9-slice window frames (standard / menu / battle), battle health boxes,
type + status badges, menu backdrop patterns and two list icons, together
with their 16-colour palettes.

Run from anywhere (Python 3, standard library only):

    python3 tools/gen_ui_gfx.py                 # writes src/gfx_ui.h
    python3 tools/gen_ui_gfx.py --preview DIR   # also writes 3x preview PNGs

UI palette convention (every bank): 0 transparent, 1 paper, 2 ink,
3 ink shadow.  Text shadow = +1 right, +1 down, +1 diagonal where no ink.

4bpp tiles: 8 u32 per tile, one per pixel row, pixel x at bits 4x..4x+3.
"""

import os
import struct
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_H = os.path.join(ROOT, "src", "gfx_ui.h")


# ---------------------------------------------------------------------------
# colours
# ---------------------------------------------------------------------------

def c15(r, g, b):
    return r | (g << 5) | (b << 10)


def rgb8(c):
    r, g, b = c & 31, (c >> 5) & 31, (c >> 10) & 31
    return ((r << 3) | (r >> 2), (g << 3) | (g >> 2), (b << 3) | (b >> 2))


# The WILDKIN look: lantern-lit parchment pages bound in dark ink-walnut
# with thin gold filigree and corner studs; bouts and the HUD use night
# slate plaques with the same gold.  Menus sit on a deep rune-lattice
# backdrop.

# bank 15: dialog boxes, menus, lists (parchment page)
PAL_STD = [
    c15(0, 0, 0),       # 0 transparent
    c15(29, 27, 21),    # 1 paper: parchment
    c15(6, 4, 4),       # 2 ink: sepia-black
    c15(23, 20, 14),    # 3 ink shadow: parchment shade
    c15(3, 3, 5),       # 4 frame dark (ink outline)
    c15(9, 7, 7),       # 5 frame band (walnut-ink)
    c15(27, 20, 8),     # 6 frame gold filigree
    c15(31, 24, 12),    # 7 selection glow (lantern amber)
    c15(21, 3, 4),      # 8 red ink (crimson)
    c15(27, 18, 14),    # 9 red shadow
    c15(2, 10, 14),     # 10 blue ink (deep teal)
    c15(20, 21, 18),    # 11 blue shadow
    c15(4, 13, 5),      # 12 green ink (forest)
    c15(21, 23, 14),    # 13 green shadow
    c15(31, 29, 19),    # 14 frame accent: pale gold / glow rim
    c15(26, 23, 16),    # 15 frame accent: parchment edge
]

# bank 14: battle message box, bout banner, title and growth scene
# (night slate)
PAL_BATTLE = [
    c15(0, 0, 0),       # 0 transparent
    c15(4, 5, 8),       # 1 paper: night slate
    c15(29, 28, 23),    # 2 ink: parchment white
    c15(1, 1, 3),       # 3 shadow
    c15(1, 1, 2),       # 4 outer outline
    c15(27, 20, 8),     # 5 gold filigree
    c15(15, 10, 5),     # 6 bronze
    c15(9, 10, 15),     # 7 glow (selection on slate)
    c15(31, 17, 14),    # 8 red ink (rose ember)
    c15(12, 4, 3),      # 9 red shadow / logo shadow
    c15(14, 27, 27),    # 10 blue ink (lantern teal)
    c15(1, 5, 7),       # 11 blue shadow
    c15(31, 26, 11),    # 12 bright gold (logo, green ink on slate)
    c15(8, 6, 3),       # 13 gold shadow
    c15(31, 30, 21),    # 14 pale gold highlight
    c15(7, 8, 12),      # 15 slate rim
]

# bank 13: battle plaques (night slate banners)
PAL_HUD = [
    c15(0, 0, 0),       # 0 transparent
    c15(4, 5, 8),       # 1 plaque: night slate
    c15(29, 28, 23),    # 2 ink: parchment white
    c15(1, 1, 3),       # 3 ink shadow
    c15(1, 1, 2),       # 4 outline
    c15(27, 20, 8),     # 5 gold trim
    c15(14, 9, 4),      # 6 bronze
    c15(31, 29, 19),    # 7 pale gold
    c15(9, 27, 23),     # 8 vitality teal
    c15(3, 17, 16),     # 9 vitality teal shade
    c15(31, 22, 6),     # 10 vitality amber
    c15(23, 13, 2),     # 11 vitality amber shade
    c15(30, 7, 9),      # 12 vitality crimson
    c15(18, 2, 6),      # 13 vitality crimson shade
    c15(16, 22, 31),    # 14 EXP: arcane blue
    c15(1, 2, 4),       # 15 empty bar trough
]


# ---------------------------------------------------------------------------
# small image helper (palette-index images)
# ---------------------------------------------------------------------------

class Img:
    def __init__(self, w, h, fill=0):
        self.w, self.h = w, h
        self.p = [[fill] * w for _ in range(h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    def get(self, x, y, default=0):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.p[y][x]
        return default

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def blit(self, o, x, y, skip0=True):
        for yy in range(o.h):
            for xx in range(o.w):
                v = o.p[yy][xx]
                if v or not skip0:
                    self.set(x + xx, y + yy, v)

    def tile(self, tx, ty):
        rows = []
        for y in range(8):
            v = 0
            for x in range(8):
                v |= (self.p[ty * 8 + y][tx * 8 + x] & 15) << (4 * x)
            rows.append(v)
        return rows

    def tiles(self):
        out = []
        for ty in range(self.h // 8):
            for tx in range(self.w // 8):
                out.append(self.tile(tx, ty))
        return out


def from_rows(rows, cmap):
    """Build an Img from strings; cmap maps characters to indices."""
    img = Img(len(rows[0]), len(rows))
    for y, row in enumerate(rows):
        assert len(row) == img.w, rows
        for x, ch in enumerate(row):
            img.p[y][x] = cmap[ch]
    return img


def layer_map(mask):
    """Onion-peel a boolean mask (4-neighbourhood); returns depth or -1."""
    h, w = len(mask), len(mask[0])
    depth = [[-1] * w for _ in range(h)]
    cur = [[mask[y][x] for x in range(w)] for y in range(h)]
    d = 0
    while any(any(r) for r in cur):
        edge = []
        for y in range(h):
            for x in range(w):
                if not cur[y][x]:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < w and 0 <= ny < h) or not cur[ny][nx]:
                        edge.append((x, y))
                        break
        for x, y in edge:
            depth[y][x] = d
            cur[y][x] = False
        d += 1
    return depth


def span_mask(w, h, spans):
    """spans: {y: (x0, x1)} inclusive -> boolean mask."""
    m = [[False] * w for _ in range(h)]
    for y, (x0, x1) in spans.items():
        for x in range(max(0, x0), min(w - 1, x1) + 1):
            m[y][x] = True
    return m


def rounded_spans(x0, y0, x1, y1, insets_top, insets_bot=None):
    if insets_bot is None:
        insets_bot = insets_top
    sp = {}
    for y in range(y0, y1 + 1):
        a, b = x0, x1
        i = y - y0
        if i < len(insets_top):
            a += insets_top[i]
            b -= insets_top[i]
        j = y1 - y
        if j < len(insets_bot):
            a += insets_bot[j]
            b -= insets_bot[j]
        sp[y] = (a, b)
    return sp


# ---------------------------------------------------------------------------
# main font: 14 rows, caps on rows 1..10, x-height rows 4..10,
# descenders to row 13.  Entry: (top_row, "row row row ...", advance|None)
# ---------------------------------------------------------------------------

FONT_HEIGHT = 14

GLYPHS = {
    " ": (1, "....", None),
    "!": (1, "X X X X X X X . . X", None),
    '"': (1, "X.X X.X X.X", None),
    "#": (2, ".X.X. .X.X. XXXXX .X.X. .X.X. XXXXX .X.X. .X.X.", None),
    "$": (1, "..X.. .XXX. X.X.X X.X.. .XXX. ..X.X ..X.X X.X.X .XXX. ..X..", None),
    "%": (1, ".X...X X.X..X .X..X. ....X. ...X.. ..X... .X.... .X..X. X..X.X X...X.", None),
    "&": (1, ".XX... X..X.. X..X.. X..X.. .XX... X.X..X X..X.X X...X. X..X.X .XX..X", None),
    "'": (1, "X X X", None),
    "(": (1, "..X .X. .X. X.. X.. X.. X.. .X. .X. ..X", None),
    ")": (1, "X.. .X. .X. ..X ..X ..X ..X .X. .X. X..", None),
    "*": (2, "..X.. X.X.X .XXX. X.X.X ..X..", None),
    "+": (4, "..X.. ..X.. XXXXX ..X.. ..X..", None),
    ",": (9, ".X .X X.", None),
    "-": (6, "XXXX", None),
    ".": (10, "X", None),
    "/": (1, "....X ....X ...X. ...X. ..X.. ..X.. .X... .X... X.... X....", None),
    "0": (1, ".XXX. X...X X...X X...X X...X X...X X...X X...X X...X .XXX.", None),
    "1": (1, "..X.. .XX.. X.X.. ..X.. ..X.. ..X.. ..X.. ..X.. ..X.. XXXXX", None),
    "2": (1, ".XXX. X...X ....X ....X ...X. ..X.. .X... X.... X.... XXXXX", None),
    "3": (1, ".XXX. X...X ....X ....X ..XX. ....X ....X ....X X...X .XXX.", None),
    "4": (1, "...X. ..XX. ..XX. .X.X. .X.X. X..X. XXXXX ...X. ...X. ...X.", None),
    "5": (1, "XXXXX X.... X.... XXXX. ....X ....X ....X ....X X...X .XXX.", None),
    "6": (1, ".XXX. X...X X.... X.... XXXX. X...X X...X X...X X...X .XXX.", None),
    "7": (1, "XXXXX X...X ....X ...X. ...X. ..X.. ..X.. ..X.. ..X.. ..X..", None),
    "8": (1, ".XXX. X...X X...X X...X .XXX. X...X X...X X...X X...X .XXX.", None),
    "9": (1, ".XXX. X...X X...X X...X X...X .XXXX ....X ....X X...X .XXX.", None),
    ":": (5, "X . . . . X", None),
    ";": (5, ".X .. .. .. .. .X X.", None),
    "<": (3, "...X ..X. .X.. X... .X.. ..X. ...X", None),
    "=": (5, "XXXXX ..... XXXXX", None),
    ">": (3, "X... .X.. ..X. ...X ..X. .X.. X...", None),
    "?": (1, ".XXX. X...X ....X ....X ...X. ..X.. ..X.. ..... ..... ..X..", None),
    "@": (1, "..XXX.. .X...X. X..XX.X X.X.X.X X.X.X.X X.X.X.X X..XXX. .X..... ..XXXX. .......", None),
    "A": (1, ".XXXX. X....X X....X X....X X....X XXXXXX X....X X....X X....X X....X", None),
    "B": (1, "XXXXX. X....X X....X X....X XXXXX. X....X X....X X....X X....X XXXXX.", None),
    "C": (1, ".XXXX. X....X X..... X..... X..... X..... X..... X..... X....X .XXXX.", None),
    "D": (1, "XXXX.. X...X. X....X X....X X....X X....X X....X X....X X...X. XXXX..", None),
    "E": (1, "XXXXX X.... X.... X.... XXXX. X.... X.... X.... X.... XXXXX", None),
    "F": (1, "XXXXX X.... X.... X.... XXXX. X.... X.... X.... X.... X....", None),
    "G": (1, ".XXXX. X....X X..... X..... X..... X..XXX X....X X....X X....X .XXXX.", None),
    "H": (1, "X....X X....X X....X X....X XXXXXX X....X X....X X....X X....X X....X", None),
    "I": (1, "XXX .X. .X. .X. .X. .X. .X. .X. .X. XXX", None),
    "J": (1, "....X ....X ....X ....X ....X ....X ....X X...X X...X .XXX.", None),
    "K": (1, "X....X X...X. X..X.. X.X... XX.... XX.... X.X... X..X.. X...X. X....X", None),
    "L": (1, "X.... X.... X.... X.... X.... X.... X.... X.... X.... XXXXX", None),
    "M": (1, "X.....X XX...XX X.X.X.X X..X..X X..X..X X.....X X.....X X.....X X.....X X.....X", None),
    "N": (1, "X....X XX...X XX...X X.X..X X.X..X X..X.X X..X.X X...XX X...XX X....X", None),
    "O": (1, ".XXXX. X....X X....X X....X X....X X....X X....X X....X X....X .XXXX.", None),
    "P": (1, "XXXXX. X....X X....X X....X X....X XXXXX. X..... X..... X..... X.....", None),
    "Q": (1, ".XXXX. X....X X....X X....X X....X X....X X....X X..X.X X...X. .XXX.X", None),
    "R": (1, "XXXXX. X....X X....X X....X X....X XXXXX. X..X.. X...X. X....X X....X", None),
    "S": (1, ".XXXX. X....X X..... X..... .XXXX. .....X .....X .....X X....X .XXXX.", None),
    "T": (1, "XXXXX ..X.. ..X.. ..X.. ..X.. ..X.. ..X.. ..X.. ..X.. ..X..", None),
    "U": (1, "X....X X....X X....X X....X X....X X....X X....X X....X X....X .XXXX.", None),
    "V": (1, "X....X X....X X....X X....X X....X .X..X. .X..X. .X..X. ..XX.. ..XX..", None),
    "W": (1, "X.....X X.....X X.....X X.....X X..X..X X..X..X X..X..X X.X.X.X XX...XX X.....X", None),
    "X": (1, "X....X X....X .X..X. .X..X. ..XX.. ..XX.. .X..X. .X..X. X....X X....X", None),
    "Y": (1, "X...X X...X X...X .X.X. .X.X. ..X.. ..X.. ..X.. ..X.. ..X..", None),
    "Z": (1, "XXXXXX .....X ....X. ....X. ...X.. ..X... .X.... .X.... X..... XXXXXX", None),
    "[": (1, "XXX X.. X.. X.. X.. X.. X.. X.. X.. XXX", None),
    "\\": (1, "X.... X.... .X... .X... ..X.. ..X.. ...X. ...X. ....X ....X", None),
    "]": (1, "XXX ..X ..X ..X ..X ..X ..X ..X ..X XXX", None),
    "^": (1, "..X.. .X.X. X...X", None),
    "_": (12, "XXXXX", None),
    "`": (1, "X. .X", None),
    "a": (4, ".XXX. ....X .XXXX X...X X...X X...X .XXXX", None),
    "b": (1, "X.... X.... X.... XXXX. X...X X...X X...X X...X X...X XXXX.", None),
    "c": (4, ".XXX. X...X X.... X.... X.... X...X .XXX.", None),
    "d": (1, "....X ....X ....X .XXXX X...X X...X X...X X...X X...X .XXXX", None),
    "e": (4, ".XXX. X...X X...X XXXXX X.... X...X .XXX.", None),
    "f": (1, "..XX .X.. .X.. XXXX .X.. .X.. .X.. .X.. .X.. .X..", None),
    "g": (4, ".XXXX X...X X...X X...X X...X X...X .XXXX ....X X...X .XXX.", None),
    "h": (1, "X.... X.... X.... XXXX. X...X X...X X...X X...X X...X X...X", None),
    "i": (2, "X . X X X X X X X", None),
    "j": (2, "..X ... ..X ..X ..X ..X ..X ..X ..X ..X X.X .X.", None),
    "k": (1, "X.... X.... X.... X...X X..X. X.X.. XX... X.X.. X..X. X...X", None),
    "l": (1, "X X X X X X X X X X", None),
    "m": (4, "XXX.XX. X..X..X X..X..X X..X..X X..X..X X..X..X X..X..X", None),
    "n": (4, "XXXX. X...X X...X X...X X...X X...X X...X", None),
    "o": (4, ".XXX. X...X X...X X...X X...X X...X .XXX.", None),
    "p": (4, "XXXX. X...X X...X X...X X...X X...X XXXX. X.... X.... X....", None),
    "q": (4, ".XXXX X...X X...X X...X X...X X...X .XXXX ....X ....X ....X", None),
    "r": (4, "X.XX XX.. X... X... X... X... X...", None),
    "s": (4, ".XXX. X...X X.... .XXX. ....X X...X .XXX.", None),
    "t": (2, ".X.. .X.. XXXX .X.. .X.. .X.. .X.. .X.. ..XX", None),
    "u": (4, "X...X X...X X...X X...X X...X X...X .XXXX", None),
    "v": (4, "X...X X...X X...X .X.X. .X.X. .X.X. ..X..", None),
    "w": (4, "X.....X X.....X X..X..X X..X..X X..X..X X..X..X .XX.XX.", None),
    "x": (4, "X...X X...X .X.X. ..X.. .X.X. X...X X...X", None),
    "y": (4, "X...X X...X X...X X...X X...X X...X .XXXX ....X X...X .XXX.", None),
    "z": (4, "XXXXX ....X ...X. ..X.. .X... X.... XXXXX", None),
    # remaps
    "{": (2, "..X.. ..X.. .XXX. XX.XX .XXX. ..X.. ..X..", 7),  # rune cursor
    "|": (4, "X...X .X.X. ..X.. .X.X. X...X", None),          # multiplication
    "}": (6, "XX.XX .XXX. ..X..", 8),                          # continue mark
    "~": (5, ".X. XXX .X.", None),                            # bullet
}

FONT_FIRST, FONT_COUNT = 32, 95


def build_font():
    widths, bits = [], []
    for code in range(FONT_FIRST, FONT_FIRST + FONT_COUNT):
        ch = chr(code)
        top, rows, adv = GLYPHS[ch]
        rows = rows.split()
        w = len(rows[0])
        assert all(len(r) == w for r in rows), ch
        assert w <= 8 and top + len(rows) <= FONT_HEIGHT, ch
        g = [0] * FONT_HEIGHT
        for i, r in enumerate(rows):
            v = 0
            for x, c in enumerate(r):
                if c == "X":
                    v |= 0x80 >> x
            g[top + i] = v
        widths.append(adv if adv else w + 1)
        bits.append(g)
    return widths, bits


FONT_W, FONT_BITS = build_font()

# ---------------------------------------------------------------------------
# small font (HUD digits, level, HP): rows 0..6
# ---------------------------------------------------------------------------

SMALL_CHARS = "0123456789/LvHP"
SMALL_GLYPHS = {
    "0": ".XX. X..X X..X X..X X..X X..X .XX.",
    "1": ".X.. XX.. .X.. .X.. .X.. .X.. XXX.",
    "2": ".XX. X..X ...X ..X. .X.. X... XXXX",
    "3": ".XX. X..X ...X .XX. ...X X..X .XX.",
    "4": "..X. .XX. X.X. X.X. XXXX ..X. ..X.",
    "5": "XXXX X... XXX. ...X ...X X..X .XX.",
    "6": ".XX. X... X... XXX. X..X X..X .XX.",
    "7": "XXXX ...X ..X. ..X. .X.. .X.. .X..",
    "8": ".XX. X..X X..X .XX. X..X X..X .XX.",
    "9": ".XX. X..X X..X .XXX ...X ...X .XX.",
    "/": "..X ..X .X. .X. .X. X.. X..",
    "L": "X.. X.. X.. X.. X.. X.. XXX",
    "v": "... ... ... X.X X.X X.X .X.",
    "H": "X..X X..X X..X XXXX X..X X..X X..X",
    "P": "XXX. X..X X..X XXX. X... X... X...",
}
FONT_SMALL_HEIGHT = 8


def build_small():
    widths, bits = [], []
    for ch in SMALL_CHARS:
        rows = SMALL_GLYPHS[ch].split()
        w = len(rows[0])
        g = [0] * FONT_SMALL_HEIGHT
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c == "X":
                    g[y] |= 0x80 >> x
        widths.append(w + 1)
        bits.append(g)
    return widths, bits


SMALL_W, SMALL_BITS = build_small()

# ---------------------------------------------------------------------------
# tiny 3x5 label font (badges, HP / EXP labels) -- art only, not exported
# ---------------------------------------------------------------------------

TINY = {
    "A": ".X. X.X XXX X.X X.X",
    "B": "XX. X.X XX. X.X XX.",
    "C": ".XX X.. X.. X.. .XX",
    "D": "XX. X.X X.X X.X XX.",
    "E": "XXX X.. XX. X.. XXX",
    "F": "XXX X.. XX. X.. X..",
    "G": ".XX X.. X.X X.X .XX",
    "H": "X.X X.X XXX X.X X.X",
    "I": "XXX .X. .X. .X. XXX",
    "K": "X.X X.X XX. X.X X.X",
    "L": "X.. X.. X.. X.. XXX",
    "M": "X...X XX.XX X.X.X X...X X...X",
    "N": "X..X XX.X X.XX X..X X..X",
    "O": ".X. X.X X.X X.X .X.",
    "P": "XX. X.X XX. X.. X..",
    "R": "XX. X.X XX. X.X X.X",
    "S": ".XX X.. .X. ..X XX.",
    "T": "XXX .X. .X. .X. .X.",
    "U": "X.X X.X X.X X.X XXX",
    "V": "X.X X.X X.X X.X .X.",
    "Y": "X.X X.X .X. .X. .X.",
    "W": "X...X X...X X.X.X XX.XX X...X",
    "X": "X.X X.X .X. X.X X.X",
    "Z": "XXX ..X .X. X.. XXX",
}


def tiny_width(s):
    return sum(len(TINY[c].split()[0]) + 1 for c in s) - 1


def tiny_draw(img, x, y, s, ink, shadow=None):
    pts = []
    for ch in s:
        rows = TINY[ch].split()
        for yy, r in enumerate(rows):
            for xx, c in enumerate(r):
                if c == "X":
                    pts.append((x + xx, y + yy))
        x += len(rows[0]) + 1
    ps = set(pts)
    if shadow is not None:
        for px, py in pts:
            for dx, dy in ((1, 0), (0, 1), (1, 1)):
                q = (px + dx, py + dy)
                if q not in ps:
                    img.set(q[0], q[1], shadow)
    for px, py in pts:
        img.set(px, py, ink)


# ---------------------------------------------------------------------------
# window frames (9-slice)
# ---------------------------------------------------------------------------

def frame_tiles(img):
    return [img.tile(tx, ty) for ty in range(3) for tx in range(3)]


def frame_from_corner(rows, cmap):
    """Hand-drawn 8x8 top-left corner -> 24x24 box (mirrored corners, edges
    extruded from the corner's last column / row, solid paper centre)."""
    tl = from_rows(rows, cmap)
    img = Img(24, 24, 1)
    for y in range(24):
        for x in range(24):
            fx = min(x, 23 - x)
            fy = min(y, 23 - y)
            if fx < 8 and fy < 8:
                v = tl.p[fy][fx]
            elif fy < 8:
                v = tl.p[fy][7]
            elif fx < 8:
                v = tl.p[7][fx]
            else:
                v = 1
            img.p[y][x] = v
    return img


# standard page frame: an ink outline, a dark walnut band carrying one gold
# filigree line, and a gold stud with a dark rivet at every corner; the
# parchment starts 5 px in (bank 15: 4 outline, 5 band, 6 gold, 14 glint)
std_img = frame_from_corner([
    ".OOOOOOO",
    "OHGGGOWW",
    "OGOOGOGG",
    "OGOOGOWW",
    "OGGGGOOO",
    "OOOOOOpp",
    "OWGWOppp",
    "OWGWOppp",
], {".": 0, "O": 4, "W": 5, "G": 6, "H": 14, "p": 1})
FRAME_STD = frame_tiles(std_img)

# menu / card frame: a thin gold rule between ink lines, corners cut at
# 45 degrees
menu_img = frame_from_corner([
    "...OOOOO",
    "..OGGGGG",
    ".OGOOOOO",
    "OGOppppp",
    "OGOppppp",
    "OGOppppp",
    "OGOppppp",
    "OGOppppp",
], {".": 0, "O": 4, "G": 6, "p": 1})
FRAME_MENU = frame_tiles(menu_img)

# bout frame (bank 14): night slate with the same studded gold binding
battle_img = frame_from_corner([
    ".OOOOOOO",
    "OHGGGOBB",
    "OGOOGOGG",
    "OGOOGOBB",
    "OGGGGOOO",
    "OOOOOOrr",
    "OBGBOrpp",
    "OBGBOrpp",
], {".": 0, "O": 4, "B": 6, "G": 5, "H": 14, "r": 15, "p": 1})
FRAME_BATTLE = frame_tiles(battle_img)


def assemble_box(tiles9, wc, hc):
    img = Img(wc * 8, hc * 8)
    for cy in range(hc):
        for cx in range(wc):
            col = 0 if cx == 0 else (2 if cx == wc - 1 else 1)
            row = 0 if cy == 0 else (2 if cy == hc - 1 else 1)
            t = tiles9[row * 3 + col]
            for y in range(8):
                v = t[y]
                for x in range(8):
                    img.p[cy * 8 + y][cx * 8 + x] = (v >> (4 * x)) & 15
    return img


# ---------------------------------------------------------------------------
# battle health boxes (bank 13)
# ---------------------------------------------------------------------------

LEAF = [             # vitality glyph: a leaf, drawn in the live HP colour
    "....OOO",
    "..OO88O",
    ".O8889O",
    "O8898O.",
    "O898O..",
    "O9OO...",
    "O......",
]


def plaque(img, left, right, y0, y1):
    """Night-slate banner: ink outline, gold trim, slate fill.
    left/right(y) give the inclusive span of each row."""
    spans = {y: (left(y), right(y)) for y in range(y0, y1 + 1)}
    mask = span_mask(img.w, img.h, spans)
    depth = layer_map(mask)
    for y in range(img.h):
        for x in range(img.w):
            d = depth[y][x]
            if d == 0:
                img.p[y][x] = 4
            elif d == 1:
                img.p[y][x] = 5
            elif d > 1:
                img.p[y][x] = 1
    return depth


def swallowtail(y, y0, y1, depth):
    """Inset of a V notch: 0 at the tips, `depth` at the middle row."""
    mid = (y0 + y1) / 2.0
    half = (y1 - y0) / 2.0
    return int(round(depth * (1 - abs(y - mid) / half)))


def chamfer(y, y0, y1, n=2):
    return max(0, n - (y - y0), n - (y1 - y))


def vitality_track(img, bar_x, bar_y):
    """48x3 trough in an ink ring with gold end studs and the leaf."""
    img.rect(bar_x - 1, bar_y - 1, bar_x + 48, bar_y + 3, 4)
    img.rect(bar_x, bar_y, bar_x + 47, bar_y + 2, 15)
    for x in (bar_x - 2, bar_x + 49):
        img.set(x, bar_y + 1, 5)
    img.blit(from_rows(LEAF, {".": 0, "O": 4, "8": 8, "9": 9}), bar_x - 10, bar_y - 3)


def divider(img, x0, x1, y):
    """A bronze rule that fades out at both ends."""
    for x in range(x0, x1 + 1):
        if x - x0 < 3 or x1 - x < 3:
            if (x - x0) % 2 == 0:
                img.set(x, y, 6)
        else:
            img.set(x, y, 6)


def make_enemy_hud():
    W, H = 104, 32
    img = Img(W, H)
    y0, y1 = 0, 27
    plaque(img, lambda y: chamfer(y, y0, y1),
           lambda y: 103 - swallowtail(y, y0, y1, 6), y0, y1)
    anchors = dict(NAME_X=7, NAME_Y=1, LV_X=74, LV_Y=5,
                   BAR_X=44, BAR_Y=19, STATUS_X=8, STATUS_Y=16)
    divider(img, 6, 88, 15)
    vitality_track(img, anchors["BAR_X"], anchors["BAR_Y"])
    return img, anchors


def make_ally_hud():
    W, H = 104, 40
    img = Img(W, H)
    y0, y1 = 0, 39
    plaque(img, lambda y: swallowtail(y, y0, y1, 5),
           lambda y: 103 - chamfer(y, y0, y1), y0, y1)
    anchors = dict(NAME_X=12, NAME_Y=1, LV_X=76, LV_Y=5,
                   BAR_X=48, BAR_Y=19, STATUS_X=8, STATUS_Y=16,
                   HPNUM_X=97, HPNUM_Y=24, EXP_X=33, EXP_Y=34)
    divider(img, 14, 96, 15)
    vitality_track(img, anchors["BAR_X"], anchors["BAR_Y"])
    ex, ey = anchors["EXP_X"], anchors["EXP_Y"]
    img.rect(ex - 1, ey - 1, ex + 64, ey + 2, 4)
    img.rect(ex, ey, ex + 63, ey + 1, 15)
    # a small gold diamond: the rune of growth
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if abs(dx) + abs(dy) <= 2:
                img.set(ex - 5 + dx, ey + dy, 7 if abs(dx) + abs(dy) == 0 else
                        (5 if abs(dx) + abs(dy) == 1 else 4))
    return img, anchors


HUD_ENEMY, ANCH_ENEMY = make_enemy_hud()
HUD_ALLY, ANCH_ALLY = make_ally_hud()


# ---------------------------------------------------------------------------
# type and status badges (banks 12 / 11)
# ---------------------------------------------------------------------------

# WILDKIN types in data.h order (docs/WORLD.md section 5).
TYPES = ["BEAST", "BLAZE", "TIDE", "BLOOM", "SPARK", "FROST", "BRAWL",
         "VENOM", "STONE", "GALE", "DREAM", "SWARM", "DUSK", "WYRM",
         "HOLLOW", "RELIC", "METAL", "ASTRAL"]
# The first 14 fill banks 12 and 11; the expansion types live in spare
# slots 5..12 of the menu-backdrop bank (9), with white at 13.
BANK9_TYPES = ["HOLLOW", "RELIC", "METAL", "ASTRAL"]
BANK9_FIRST, BANK9_WHITE = 5, 13
LABELS = TYPES
TYPE_COLORS = {            # (fill, dark)
    "BEAST":  ((21, 19, 13), (11, 9, 6)),
    "BLAZE":  ((30, 15, 5), (18, 6, 2)),
    "TIDE":   ((12, 17, 30), (5, 7, 19)),
    "BLOOM":  ((14, 25, 9), (5, 13, 3)),
    "SPARK":  ((31, 25, 5), (18, 13, 1)),
    "FROST":  ((17, 27, 28), (6, 15, 18)),
    "BRAWL":  ((24, 8, 5), (13, 3, 2)),
    "VENOM":  ((20, 8, 20), (10, 3, 12)),
    "STONE":  ((25, 20, 12), (14, 10, 4)),
    "GALE":   ((19, 20, 30), (9, 10, 20)),
    "DREAM":  ((31, 12, 19), (18, 4, 10)),
    "SWARM":  ((20, 23, 4), (10, 12, 1)),
    "DUSK":   ((12, 9, 17), (5, 3, 8)),
    "WYRM":   ((14, 8, 30), (6, 2, 17)),
    "HOLLOW": ((23, 22, 18), (9, 8, 10)),
    "RELIC":  ((27, 19, 8), (13, 7, 3)),
    "METAL":  ((18, 21, 24), (7, 8, 12)),
    "ASTRAL": ((26, 21, 31), (11, 7, 22)),
}

TYPE_BANK = []      # 12 or 11
TYPE_IDX = {}       # type -> (fill idx, dark idx)
BADGE_PAL = [[c15(0, 0, 0), PAL_STD[1]] for _ in range(2)]   # 1 = page parchment
BANK9_EXTRA = [c15(0, 0, 0)] * 16   # merged into both menu backdrop palettes
for t in TYPES:
    fill, dark = TYPE_COLORS[t]
    if t in BANK9_TYPES:
        fi = BANK9_FIRST + 2 * BANK9_TYPES.index(t)
        BANK9_EXTRA[fi], BANK9_EXTRA[fi + 1] = c15(*fill), c15(*dark)
        TYPE_IDX[t] = (fi, fi + 1)
        TYPE_BANK.append(9)
        continue
    b = 0 if len(BADGE_PAL[0]) < 16 else 1
    fi = len(BADGE_PAL[b])
    BADGE_PAL[b] += [c15(*fill), c15(*dark)]
    TYPE_IDX[t] = (fi, fi + 1)
    TYPE_BANK.append(12 if b == 0 else 11)
BANK9_EXTRA[BANK9_WHITE] = PAL_STD[1]
assert all(len(p) == 16 for p in BADGE_PAL)


def make_type_badge(t, label):
    fi, di = TYPE_IDX[t]
    img = Img(32, 16)
    sp = rounded_spans(0, 2, 31, 13, [2, 1])
    mask = span_mask(32, 16, sp)
    depth = layer_map(mask)
    for y in range(16):
        for x in range(32):
            if depth[y][x] == 0:
                img.p[y][x] = di
            elif depth[y][x] > 0:
                img.p[y][x] = fi
    # darker lower half band for a little depth
    for x in range(32):
        if depth[12][x] > 0:
            img.p[12][x] = di
    w = tiny_width(label) + 1
    white = BANK9_WHITE if t in BANK9_TYPES else 1
    tiny_draw(img, (32 - w + 1) // 2, 5, label, white, di)
    return img


TYPE_BADGES = [make_type_badge(t, l) for t, l in zip(TYPES, LABELS)]

STATUS = [("BRN", "BLAZE"), ("PSN", "VENOM"), ("NMB", "SPARK"),
          ("SLP", "BEAST"), ("FRZ", "FROST")]


def make_status_badge(label, t):
    fi, di = TYPE_IDX[t]
    img = Img(24, 8, fi)
    for x in range(24):
        img.p[0][x] = di
        img.p[7][x] = di
    for y in range(8):
        img.p[y][0] = di
        img.p[y][23] = di
    w = tiny_width(label) + 1
    tiny_draw(img, (24 - w + 1) // 2, 1, label, 1, di)
    return img


STATUS_BADGES = [make_status_badge(l, t) for l, t in STATUS]
STATUS_BANK = [TYPE_BANK[TYPES.index(t)] for _, t in STATUS]


# ---------------------------------------------------------------------------
# menu backdrops (bank 9) and list icons (bank 15)
# ---------------------------------------------------------------------------

MENU_PAL = [
    # night moss: 1 base, 2 inner tone, 3 lattice line, 4 gold knot
    [c15(0, 0, 0), c15(3, 6, 7), c15(4, 8, 9), c15(7, 12, 12),
     c15(20, 15, 6)] + BANK9_EXTRA[5:],
    # catalogue oxblood: 1 base, 2 inner tone, 3 lattice line, 4 gold knot
    [c15(0, 0, 0), c15(8, 3, 4), c15(10, 4, 5), c15(15, 6, 6),
     c15(22, 15, 6)] + BANK9_EXTRA[5:],
]


def make_menu_bg(kind):
    """16x16 seamless rune lattice: a diamond net of fine lines with a gold
    knot where they cross and a small lighter rune-diamond in each cell."""
    img = Img(16, 16, 1)
    for y in range(16):
        for x in range(16):
            a, b = (x + y) % 16, (x - y) % 16
            if a == 0 or b == 0:
                img.p[y][x] = 3
            # a softer inner diamond around each cell centre (8, 0)/(0, 8)
            elif abs(((x + 8) % 16) - 8) + abs(y - 8) <= 2 if kind == 0 else \
                    abs(((x + 8) % 16) - 8) + abs(y - 8) == 2:
                img.p[y][x] = 2
    # knots where the lines cross
    for (x, y) in ((0, 0), (8, 8)):
        img.p[y][x] = 4
    # cell centres get a dim dot
    for (x, y) in ((8, 0), (0, 8)):
        img.p[y][x] = 2
    return img


MENU_BG = [make_menu_bg(0), make_menu_bg(1)]

# a tiny glowing lantern: "befriended"
ICON_CAUGHT = from_rows([
    "..4444..",
    ".444444.",
    ".499994.",
    ".491194.",
    ".491194.",
    ".498894.",
    ".444444.",
    "..4..4..",
], {".": 0, "4": 4, "8": 8, "1": 1, "9": 9})

ICON_EMPTY = from_rows([
    "..3333..",
    ".3....3.",
    "3......3",
    "3......3",
    "3......3",
    "3......3",
    ".3....3.",
    "..3333..",
], {".": 0, "3": 3})


# ---------------------------------------------------------------------------
# rarity gems (8x8 OBJ tiles, one shared OBJ palette): the Almanac, the
# LANTERN SHELF and the summary show a kin's rarity as a coloured gem --
# grey common, green uncommon, blue rare, gold legend, purple spiral fusion
# (docs/EXPANSION.md 3).
# ---------------------------------------------------------------------------

GEM_PAL = [
    c15(0, 0, 0),       # 0 transparent
    c15(4, 4, 9),       # 1 outline
    c15(31, 31, 31),    # 2 sparkle
    c15(25, 25, 27),    # 3 grey light
    c15(14, 15, 18),    # 4 grey dark
    c15(15, 30, 13),    # 5 green light
    c15(3, 17, 6),      # 6 green dark
    c15(14, 23, 31),    # 7 blue light
    c15(3, 8, 25),      # 8 blue dark
    c15(31, 30, 14),    # 9 gold light
    c15(30, 20, 2),     # 10 gold mid
    c15(19, 10, 1),     # 11 gold dark
    c15(28, 20, 31),    # 12 purple light
    c15(19, 7, 27),     # 13 purple mid
    c15(10, 3, 17),     # 14 purple dark
    c15(0, 0, 0),       # 15 spare
]

GEM_CUT = [          # L light, M mid, D dark, W sparkle, O outline
    "........",
    ".OOOOOO.",
    "OLWLLMMO",
    "OLLMMMDO",
    ".OMMMDO.",
    "..OMDO..",
    "...OO...",
    "........",
]
GEM_STAR = [         # legend: a gold star-cut gem
    "...OO...",
    "..OLWO..",
    "OOOLLMOO",
    "OLWLMMDO",
    ".OLMMDO.",
    ".OMMODDO",
    "OMDO.ODO",
    "OOO...OO",
]
GEM_SPIRAL = [       # fusion: a purple spiral
    "..OOOO..",
    ".OLLLLO.",
    "OLDDDDLO",
    "ODLLLDLO",
    "ODLDWDLO",
    "ODLDDDLO",
    ".OLLLLO.",
    "..OOOO..",
]


def make_gem(rows, light, mid, dark):
    cmap = {".": 0, "O": 1, "W": 2, "L": light, "M": mid, "D": dark}
    return from_rows(rows, cmap)


GEMS = [
    make_gem(GEM_CUT, 3, 3, 4),        # R_COMMON
    make_gem(GEM_CUT, 5, 5, 6),        # R_UNCOMMON
    make_gem(GEM_CUT, 7, 7, 8),        # R_RARE
    make_gem(GEM_STAR, 9, 10, 11),     # R_LEGEND
    make_gem(GEM_SPIRAL, 12, 13, 14),  # R_FUSION
]


# ---------------------------------------------------------------------------
# Hall crests (16x16 medallions, drawn in the badge bank of their Hall's
# type so no extra palette is needed) and an empty crest slot (bank 15)
# ---------------------------------------------------------------------------

CREST_TYPES = [("VOLT", "SPARK"), ("TIDE", "TIDE"), ("ANVIL", "METAL"),
               ("RIME", "FROST"), ("LANTERN", "BLAZE"), ("DREAM", "DREAM")]

CREST_SYMBOLS = {
    "VOLT": [
        ".....WW..",
        "....WW...",
        "...WW....",
        "..WWWWW..",
        "....WW...",
        "...WW....",
        "..WW.....",
        "..W......",
        ".........",
    ],
    "TIDE": [
        ".........",
        ".WW...WW.",
        "W..W.W..W",
        "....W....",
        ".........",
        ".WW...WW.",
        "W..W.W..W",
        "....W....",
        ".........",
    ],
    "ANVIL": [
        ".........",
        "WWWWWWWW.",
        ".WWWWWWWW",
        "...WWWW..",
        "....WW...",
        "....WW...",
        "..WWWWWW.",
        "..WWWWWW.",
        ".........",
    ],
    "RIME": [
        "....W....",
        ".W..W..W.",
        "..W.W.W..",
        "...WWW...",
        "WWWWWWWWW",
        "...WWW...",
        "..W.W.W..",
        ".W..W..W.",
        "....W....",
    ],
    "LANTERN": [
        "...WWW...",
        "...W.W...",
        "..WWWWW..",
        ".WW...WW.",
        ".W..W..W.",
        ".W.WW..W.",
        ".W.WWW.W.",
        ".WW...WW.",
        "..WWWWW..",
    ],
    "DREAM": [
        "....WWW..",
        "..WWW....",
        ".WWW...W.",
        ".WW.....W",
        ".WW....W.",
        ".WWW.....",
        "..WWW....",
        "....WWW..",
        ".........",
    ],
}


def crest_disc(fill, dark, white, rim_only=False):
    """16x16 medallion: dark rim, fill inside, a white glint top-left."""
    img = Img(16, 16)
    cx = cy = 7.5
    inside = [[(x - cx) ** 2 + (y - cy) ** 2 <= 7.6 ** 2 for x in range(16)] for y in range(16)]
    for y in range(16):
        for x in range(16):
            if not inside[y][x]:
                continue
            edge = any(not (0 <= x + dx < 16 and 0 <= y + dy < 16 and inside[y + dy][x + dx])
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge:
                img.p[y][x] = dark
            elif not rim_only:
                img.p[y][x] = fill
    if not rim_only:
        for (x, y) in ((4, 2), (3, 3), (2, 4)):
            img.p[y][x] = white
    return img


def make_crest(name, t):
    fi, di = TYPE_IDX[t]
    white = BANK9_WHITE if t in BANK9_TYPES else 1
    img = crest_disc(fi, di, white)
    for yy, row in enumerate(CREST_SYMBOLS[name]):
        for xx, ch in enumerate(row):
            if ch == "W":
                img.set(4 + xx, 3 + yy, white)
    return img, TYPE_BANK[TYPES.index(t)], white


CRESTS = [make_crest(n, t) for n, t in CREST_TYPES]


def make_crest_empty():
    """An unearned crest: a dotted grey ring (bank 15: 3 shadow, 6 frame light)."""
    ring = crest_disc(0, 3, 0, rim_only=True)
    for y in range(16):
        for x in range(16):
            if ring.p[y][x] == 3 and (x + y) % 3 == 0:
                ring.p[y][x] = 6
    return ring


CREST_EMPTY = make_crest_empty()


# ---------------------------------------------------------------------------
# header output
# ---------------------------------------------------------------------------

def fmt_u32_rows(rows, indent="    ", per=4):
    out = []
    for i in range(0, len(rows), per):
        out.append(indent + ", ".join("0x%08X" % v for v in rows[i:i + per]) + ",")
    return "\n".join(out)


def fmt_u16(vals):
    return ", ".join("0x%04X" % v for v in vals)


def c_tiles_2d(name, tiles, comment=None):
    s = []
    if comment:
        s.append("/* %s */" % comment)
    s.append("static const u32 %s[%d][8] = {" % (name, len(tiles)))
    for t in tiles:
        s.append("    { " + ", ".join("0x%08X" % v for v in t) + " },")
    s.append("};")
    return "\n".join(s)


def c_flat_tiles(name, img):
    tiles = img.tiles()
    flat = [v for t in tiles for v in t]
    s = ["static const u32 %s[%d * %d * 8] = {" % (name, img.w // 8, img.h // 8)]
    for i, t in enumerate(tiles):
        s.append("    " + ", ".join("0x%08X" % v for v in t) + ",")
    s.append("};")
    return "\n".join(s)


def write_header():
    L = []
    A = L.append
    A("/* Generated by tools/gen_ui_gfx.py -- do not edit by hand. */")
    A("/*")
    A(" * WILDKIN UI art (parchment, night slate, gold). Include after the u8/u16/u32 typedefs.")
    A(" * Palette convention for every UI bank: 0 transparent, 1 paper, 2 ink,")
    A(" * 3 ink shadow (drawn +1 right, +1 down, +1 diagonal where no ink).")
    A(" * Tiles are 4bpp, 8 u32 per tile (one per row, pixel x at bits 4x..4x+3),")
    A(" * multi-tile images in row-major tile order.")
    A(" */")
    A("#ifndef GFX_UI_H")
    A("#define GFX_UI_H")
    A("")
    A("/* silence -Wunused-const-variable for tables a build doesn't use */")
    A("#if defined(__GNUC__)")
    A("#define GFX_UI_UNUSED __attribute__((unused))")
    A("#else")
    A("#define GFX_UI_UNUSED")
    A("#endif")
    A("")
    # --- main font
    A("/* ---- main variable-width font --------------------------------------- */")
    A("/* Caps on rows 1..10 (baseline = bottom of row 10), x-height rows 4..10,")
    A(" * descenders to row 13. Use a 16 px line pitch. bit 7 = leftmost pixel.")
    A(" * font_width = advance incl. 1 px spacing (shadow overlaps the spacing).")
    A(" * Remaps: '{' = rune cursor, '}' = down 'continue' mark,")
    A(" *         '|' = multiplication sign, '~' = bullet. */")
    A("#define FONT_FIRST 32")
    A("#define FONT_COUNT 95")
    A("#define FONT_HEIGHT 14")
    A("static const u8 font_width[FONT_COUNT] = {")
    for i in range(0, FONT_COUNT, 16):
        A("    " + ", ".join("%d" % w for w in FONT_W[i:i + 16]) + ",")
    A("};")
    A("static const u8 font_bits[FONT_COUNT][FONT_HEIGHT] = {")
    for i, g in enumerate(FONT_BITS):
        ch = chr(FONT_FIRST + i)
        name = {"\\": "backslash", "'": "quote", "*": "star", "/": "slash"}.get(ch, ch)
        if ch == " ":
            name = "space"
        A("    { " + ", ".join("0x%02X" % v for v in g) + " }, /* %s */" % name)
    A("};")
    A("")
    # --- small font
    A("/* ---- small HUD font (rows 0..6) -------------------------------------- */")
    A('static const char font_small_chars[] = "%s";' % SMALL_CHARS)
    A("#define FONT_SMALL_HEIGHT 8")
    A("static const u8 font_small_width[15] = { " + ", ".join(str(w) for w in SMALL_W) + " };")
    A("static const u8 font_small_bits[15][FONT_SMALL_HEIGHT] = {")
    for ch, g in zip(SMALL_CHARS, SMALL_BITS):
        A("    { " + ", ".join("0x%02X" % v for v in g) + " }, /* %s */" % ch)
    A("};")
    A("")
    # --- palettes
    A("/* ---- palettes (RGB15) ------------------------------------------------ */")
    A("/* bank 15 STD (parchment page): 0 -, 1 paper, 2 ink, 3 shadow,")
    A(" * 4/5/6 frame outline/band/gold, 7 selection glow, 8/9 red ink/shadow,")
    A(" * 10/11 blue (teal), 12/13 green, 14 pale gold, 15 parchment edge */")
    A("static const u16 ui_pal_std[16] = { %s };" % fmt_u16(PAL_STD))
    A("/* bank 14 BATTLE (night slate): 1 paper, 2 light ink, 3 shadow, 4 outline,")
    A(" * 5 gold, 6 bronze, 7 glow, 8/9 red ink, 10/11 teal ink, 12/13 gold ink,")
    A(" * 14 pale gold, 15 slate rim */")
    A("static const u16 ui_pal_battle[16] = { %s };" % fmt_u16(PAL_BATTLE))
    A("/* bank 13 HUD (slate plaques): 1 slate, 2 light ink, 3 shadow, 4-7 plaque")
    A(" * art, 8/9 vitality teal/shade, 10/11 amber, 12/13 crimson, 14 EXP,")
    A(" * 15 empty trough. Fill: bar row 0 = shade (9/11/13), rows 1-2 = light. */")
    A("static const u16 ui_pal_hud[16] = { %s };" % fmt_u16(PAL_HUD))
    A("")
    # --- frames
    A("/* ---- 9-slice window frames: TL,T,TR,L,C,R,BL,B,BR (one 8x8 tile each) - */")
    A(c_tiles_2d("ui_frame_std", FRAME_STD, "bank 15: dialog frame"))
    A(c_tiles_2d("ui_frame_menu", FRAME_MENU, "bank 15: menu / list frame"))
    A(c_tiles_2d("ui_frame_battle", FRAME_BATTLE, "bank 14: battle message box"))
    A("")
    # --- HUD
    A("/* ---- battle plaques (bank 13) --------------------------------------------- */")
    A("/* Anchors are pixel offsets from the box's top-left. HP fill area 48x3 at")
    A(" * (BAR_X, BAR_Y); EXP fill area 64x2 at (EXP_X, EXP_Y). Name: main font")
    A(" * glyph box top-left. Level: small font top-left. STATUS: 24x8 badge")
    A(" * (8-aligned cells, plain paper in the art). HPNUM_X: exclusive right")
    A(" * edge of the right-aligned HP numbers incl. trailing spacing, i.e. draw")
    A(" * at x = HPNUM_X - sum(font_small_width) (small font, top row HPNUM_Y);")
    A(" * the ink then ends flush with the HP bar's right end. */")
    A("/* enemy: 104x32 (13x4 tiles) */")
    for k in ("NAME_X", "NAME_Y", "LV_X", "LV_Y", "BAR_X", "BAR_Y",
              "STATUS_X", "STATUS_Y"):
        A("#define HUD_ENEMY_%s %d" % (k, ANCH_ENEMY[k]))
    A("/* ally: 104x40 (13x5 tiles) */")
    for k in ("NAME_X", "NAME_Y", "LV_X", "LV_Y", "BAR_X", "BAR_Y",
              "STATUS_X", "STATUS_Y", "HPNUM_X", "HPNUM_Y", "EXP_X", "EXP_Y"):
        A("#define HUD_ALLY_%s %d" % (k, ANCH_ALLY[k]))
    A(c_flat_tiles("hud_enemy_gfx", HUD_ENEMY))
    A(c_flat_tiles("hud_ally_gfx", HUD_ALLY))
    A("")
    # --- badges
    A("/* ---- type badges (32x16, 4x2 tiles) and status badges (24x8) --------- */")
    A("/* order: " + " ".join(TYPES) + " */")
    A("#define TYPE_BADGE_COUNT %d" % len(TYPES))
    A("static const u32 type_badge_gfx[%d][8 * 8] = {" % len(TYPES))
    for t, img in zip(TYPES, TYPE_BADGES):
        A("    { /* %s */" % t)
        A(fmt_u32_rows([v for tl in img.tiles() for v in tl], "        ", 8))
        A("    },")
    A("};")
    A("static const u8 type_badge_bank[%d] = { " % len(TYPES) + ", ".join(str(b) for b in TYPE_BANK) + " };")
    A("/* [0] -> bank 12, [1] -> bank 11; index 1 = the page parchment (label text and paper) */")
    A("static const u16 type_badge_pal[2][16] = {")
    for p in BADGE_PAL:
        A("    { %s }," % fmt_u16(p))
    A("};")
    A("/* BRN PSN NMB SLP FRZ; fully opaque */")
    A("static const u32 status_badge_gfx[5][3 * 8] = {")
    for (lbl, _), img in zip(STATUS, STATUS_BADGES):
        A("    { /* %s */" % lbl)
        A(fmt_u32_rows([v for tl in img.tiles() for v in tl], "        ", 8))
        A("    },")
    A("};")
    A("static const u8 status_badge_bank[5] = { " + ", ".join(str(b) for b in STATUS_BANK) + " };")
    A("")
    # --- menu bg + icons
    A("/* ---- menu backdrops (bank 9, 16x16 = 2x2 tiles) and list icons ------- */")
    A("static const u32 menu_bg_gfx[2][4 * 8] = {")
    for img in MENU_BG:
        A("    {")
        A(fmt_u32_rows([v for tl in img.tiles() for v in tl], "        ", 8))
        A("    },")
    A("};")
    A("static const u16 menu_bg_pal[2][16] = {")
    for p in MENU_PAL:
        A("    { %s }," % fmt_u16(p))
    A("};")
    A("/* bank 15 indices; 0 = transparent */")
    A("static const u32 ui_icon_caught[8] = { %s };" %
      ", ".join("0x%08X" % v for v in ICON_CAUGHT.tile(0, 0)))
    A("static const u32 ui_icon_empty[8] = { %s };" %
      ", ".join("0x%08X" % v for v in ICON_EMPTY.tile(0, 0)))
    A("")
    # --- rarity gems
    A("/* ---- rarity gems: 8x8 OBJ tiles in R_* order (common, uncommon, rare,")
    A(" * legend, fusion) sharing one OBJ palette ------------------------------ */")
    A("#define GEM_COUNT %d" % len(GEMS))
    A("static const u32 gem_obj_gfx[%d][8] = {" % len(GEMS))
    for img in GEMS:
        A("    { " + ", ".join("0x%08X" % v for v in img.tile(0, 0)) + " },")
    A("};")
    A("static const u16 gem_obj_pal[16] = { %s };" % fmt_u16(GEM_PAL))
    A("")
    # --- crests
    A("/* ---- Hall crests: 16x16 (2x2 tiles) medallions drawn in their Hall")
    A(" * type's badge bank (crest_bank); crest_paper = that bank's white, used")
    A(" * to fill the transparent corners. Order: " + " ".join(n for n, _ in CREST_TYPES) + ".")
    A(" * crest_empty_gfx: an unearned slot, bank 15 (fill with paper, 1). */")
    A("#define CREST_ART_COUNT %d" % len(CRESTS))
    A("static const u32 crest_gfx[%d][4 * 8] = {" % len(CRESTS))
    for (n, _), (img, _, _) in zip(CREST_TYPES, CRESTS):
        A("    { /* %s */" % n)
        A(fmt_u32_rows([v for tl in img.tiles() for v in tl], "        ", 8))
        A("    },")
    A("};")
    A("static const u8 crest_bank[%d] = { " % len(CRESTS) + ", ".join(str(b) for _, b, _ in CRESTS) + " };")
    A("static const u8 crest_paper[%d] = { " % len(CRESTS) + ", ".join(str(w) for _, _, w in CRESTS) + " };")
    A("static const u32 crest_empty_gfx[4 * 8] = {")
    A(fmt_u32_rows([v for tl in CREST_EMPTY.tiles() for v in tl], "    ", 8))
    A("};")
    A("")
    A("#endif /* GFX_UI_H */")
    text = "\n".join(L) + "\n"
    out = []
    for line in text.split("\n"):
        if line.startswith("static const ") and " = " in line:
            i = line.index(" = ")
            line = line[:i] + " GFX_UI_UNUSED" + line[i:]
        out.append(line)
    with open(OUT_H, "w") as f:
        f.write("\n".join(out))


# ---------------------------------------------------------------------------
# previews: RGB canvas, mock compositor, PNG writer
# ---------------------------------------------------------------------------

class Canvas:
    def __init__(self, w, h, bg=(0, 0, 0)):
        self.w, self.h = w, h
        self.p = [[bg] * w for _ in range(h)]
        self.ink = set()

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def blit(self, img, pal, x, y, skip0=True, fill0=None):
        for yy in range(img.h):
            for xx in range(img.w):
                v = img.p[yy][xx]
                if v == 0 and fill0 is not None:
                    v = fill0
                if v or not skip0:
                    self.set(x + xx, y + yy, rgb8(pal[v]))

    def text(self, x, y, s, pal, ink=2, shadow=3):
        for ch in s:
            i = ord(ch) - FONT_FIRST
            g = FONT_BITS[i]
            pts = set()
            for yy in range(FONT_HEIGHT):
                for xx in range(8):
                    if g[yy] & (0x80 >> xx):
                        pts.add((x + xx, y + yy))
            sh = set()
            for px, py in pts:
                for dx, dy in ((1, 0), (0, 1), (1, 1)):
                    q = (px + dx, py + dy)
                    if q not in pts:
                        sh.add(q)
            for q in sh:
                if q not in self.ink:
                    self.set(q[0], q[1], rgb8(pal[shadow]))
            for q in pts:
                self.set(q[0], q[1], rgb8(pal[ink]))
                self.ink.add(q)
            x += FONT_W[i]
        return x

    def small(self, x, y, s, pal, ink=2, shadow=3):
        for ch in s:
            if ch == " ":
                x += 4
                continue
            i = SMALL_CHARS.index(ch)
            g = SMALL_BITS[i]
            pts = set()
            for yy in range(FONT_SMALL_HEIGHT):
                for xx in range(8):
                    if g[yy] & (0x80 >> xx):
                        pts.add((x + xx, y + yy))
            for px, py in pts:
                for dx, dy in ((1, 0), (0, 1), (1, 1)):
                    q = (px + dx, py + dy)
                    if q not in pts and q not in self.ink:
                        self.set(q[0], q[1], rgb8(pal[shadow]))
            for q in pts:
                self.set(q[0], q[1], rgb8(pal[ink]))
                self.ink.add(q)
            x += SMALL_W[i]
        return x

    def save(self, path, scale=3):
        rows = []
        for y in range(self.h):
            row = bytearray()
            for x in range(self.w):
                row += bytes(self.p[y][x]) * scale
            for _ in range(scale):
                rows.append(bytes(row))
        write_png(path, self.w * scale, self.h * scale, rows)


def write_png(path, w, h, rows):
    raw = b"".join(b"\x00" + r for r in rows)

    def chunk(t, d):
        return (struct.pack(">I", len(d)) + t + d +
                struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF))
    data = (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(data)


def text_width(s):
    return sum(FONT_W[ord(c) - FONT_FIRST] for c in s)


def small_width(s):
    return sum(SMALL_W[SMALL_CHARS.index(c)] for c in s)


def field_bg(cv):
    g1, g2, g3 = (96, 176, 72), (80, 160, 64), (136, 208, 104)
    for y in range(cv.h):
        for x in range(cv.w):
            c = g1
            if ((x // 16) + (y // 16)) % 2:
                c = g2
            if (x % 16, y % 16) in ((3, 4), (4, 3), (5, 4), (11, 11), (12, 10), (13, 11)):
                c = g3
            cv.p[y][x] = c
    # a sandy path
    for y in range(40, 112):
        for x in range(60, 100):
            cv.p[y][x] = (216, 192, 136) if (x + y) % 7 else (200, 176, 120)


def preview_font(path):
    cols = 16
    cw, ch = 12, 18
    W = max(cols * cw + 16, 256)
    rows = (FONT_COUNT + cols - 1) // cols
    H = rows * ch + 16 + 4 * 18 + 30
    paper = rgb8(PAL_STD[1])
    cv = Canvas(W, H, paper)
    grid = (232, 236, 240)
    for i in range(FONT_COUNT):
        cx = 8 + (i % cols) * cw
        cy = 8 + (i // cols) * ch
        cv.rect(cx, cy, cx + cw - 2, cy + FONT_HEIGHT + 1, grid)
        # baseline marker
        cv.rect(cx, cy + 11, cx + cw - 2, cy + 11, (210, 220, 236))
        cv.text(cx + 1, cy + 1, chr(FONT_FIRST + i), PAL_STD)
    y = 8 + rows * ch + 6
    for s in ["Hello! Welcome to the world of MONQUEST.",
              "FLARIX used EMBER! It's super effective!",
              "0123456789 ?!.,'-:;()/%&",
              "{ Quick brown fox jumps over lazy dogs } |~"]:
        cv.text(8, y, s, PAL_STD)
        y += 16
    # red / blue / green ink variants
    x = cv.text(8, y, "Female ", PAL_STD, 8, 9)
    x = cv.text(x, y, "Male ", PAL_STD, 10, 11)
    x = cv.text(x, y, "Caught ", PAL_STD, 12, 13)
    y += 18
    cv.small(8, y, "0123456789/LvHP  Lv50 126/126", PAL_STD)
    cv.save(path)


def draw_hp(cv, x, y, frac, pal=PAL_HUD):
    n = int(round(48 * frac))
    if frac > 0.5:
        lt, sh = 8, 9   # teal
    elif frac > 0.2:
        lt, sh = 10, 11
    else:
        lt, sh = 12, 13
    for i in range(n):
        cv.set(x + i, y, rgb8(pal[sh]))
        cv.set(x + i, y + 1, rgb8(pal[lt]))
        cv.set(x + i, y + 2, rgb8(pal[lt]))


def preview_dialog(path):
    cv = Canvas(240, 160)
    field_bg(cv)
    # a menu on the right
    mx, my, mw, mh = 21, 0, 9, 13
    menu = assemble_box(FRAME_MENU, mw, mh)
    cv.blit(menu, PAL_STD, mx * 8, my * 8)
    items = ["MONDEX", "TEAM", "BAG", "JULIAN", "SAVE", "OPTION"]
    sel = 1
    for i, it in enumerate(items):
        ty = my * 8 + 6 + i * 16
        if i == sel:
            cv.rect(mx * 8 + 4, ty, mx * 8 + mw * 8 - 5, ty + 15, rgb8(PAL_STD[7]))
            cv.text(mx * 8 + 7, ty + 1, "{", PAL_STD)
        cv.text(mx * 8 + 16, ty + 1, it, PAL_STD)
    # dialog
    box = assemble_box(FRAME_STD, 30, 6)
    cv.blit(box, PAL_STD, 0, 14 * 8)
    cv.text(16, 120, "Hello! Welcome to the world of", PAL_STD)
    x = cv.text(16, 136, "MONQUEST! My name is ", PAL_STD)
    x = cv.text(x, 136, "OAKLEY", PAL_STD, 10, 11)
    x = cv.text(x, 136, ".", PAL_STD)
    cv.text(x + 3, 136, "}", PAL_STD, 8, 9)
    cv.save(path)


def preview_battle(path):
    cv = Canvas(240, 160, (120, 200, 104))
    # platforms for context
    for (cx, cy, rx, ry) in ((176, 60, 44, 10), (64, 108, 56, 12)):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                    cv.set(x, y, (152, 216, 120) if y < cy else (104, 176, 88))
    # enemy HUD
    ex, ey = 8, 16
    cv.blit(HUD_ENEMY, PAL_HUD, ex, ey)
    a = ANCH_ENEMY
    cv.text(ex + a["NAME_X"], ey + a["NAME_Y"], "GLOOMOTH", PAL_HUD)
    cv.small(ex + a["LV_X"], ey + a["LV_Y"], "Lv18", PAL_HUD)
    draw_hp(cv, ex + a["BAR_X"], ey + a["BAR_Y"], 0.62)
    sb = STATUS_BADGES[1]
    cv.blit(sb, BADGE_PAL[0 if STATUS_BANK[1] == 12 else 1],
            ex + a["STATUS_X"], ey + a["STATUS_Y"])
    # ally HUD
    axx, ayy = 128, 64
    cv.blit(HUD_ALLY, PAL_HUD, axx, ayy)
    a = ANCH_ALLY
    cv.text(axx + a["NAME_X"], ayy + a["NAME_Y"], "FLARIX", PAL_HUD)
    cv.small(axx + a["LV_X"], ayy + a["LV_Y"], "Lv50", PAL_HUD)
    draw_hp(cv, axx + a["BAR_X"], ayy + a["BAR_Y"], 0.38)
    s = "48/126"
    cv.small(axx + a["HPNUM_X"] - small_width(s), ayy + a["HPNUM_Y"], s, PAL_HUD)
    for i in range(int(64 * 0.45)):
        cv.set(axx + a["EXP_X"] + i, ayy + a["EXP_Y"], rgb8(PAL_HUD[14]))
        cv.set(axx + a["EXP_X"] + i, ayy + a["EXP_Y"] + 1, rgb8(PAL_HUD[14]))
    # message plate + command card (battle_ui.c draw_action_box)
    cv.blit(assemble_box(FRAME_BATTLE, 21, 6), PAL_BATTLE, 0, 112)
    cv.text(16, 120, "FLARIX awaits", PAL_BATTLE)
    cv.text(16, 136, "your call.", PAL_BATTLE)
    cv.blit(assemble_box(FRAME_MENU, 9, 7), PAL_STD, 168, 104)
    cv.rect(172, 119, 235, 130, rgb8(PAL_STD[7]))
    for i, label in enumerate(("MOVES", "PACK", "KIN", "FLEE")):
        y = 107 + i * 12
        if i == 1:
            cv.text(175, y, "{", PAL_STD, 8, 3)
        cv.text(184, y, label, PAL_STD)
    cv.save(path)


def preview_badges(path):
    W, H = 240, 176
    cv = Canvas(W, H, rgb8(PAL_STD[1]))
    for i, img in enumerate(TYPE_BADGES):
        x = 8 + (i % 6) * 38
        y = 8 + (i // 6) * 20
        pal = BADGE_PAL[0 if TYPE_BANK[i] == 12 else 1]
        cv.blit(img, pal, x, y)
    # on cream + with white fill on paper
    y = 72
    for i, img in enumerate(STATUS_BADGES):
        pal = BADGE_PAL[0 if STATUS_BANK[i] == 12 else 1]
        cv.blit(img, pal, 8 + i * 30, y)
    # backdrops
    y = 88
    for k in range(2):
        for ty in range(3):
            for tx in range(6):
                cv.blit(MENU_BG[k], MENU_PAL[k], 8 + k * 112 + tx * 16, y + ty * 16, skip0=False)
    # icons
    y = 146
    cv.blit(ICON_CAUGHT, PAL_STD, 8, y + 4)
    cv.text(20, y, "Befriended", PAL_STD, 12, 13)
    cv.blit(ICON_EMPTY, PAL_STD, 80, y + 4)
    cv.text(92, y, "Unseen", PAL_STD)
    cv.save(path)


def preview_gems_crests(path):
    cv = Canvas(160, 64, rgb8(PAL_STD[1]))
    for i, img in enumerate(GEMS):
        cv.blit(img, GEM_PAL, 8 + i * 14, 6)
        cv.rect(8 + i * 14, 18, 15 + i * 14, 29, rgb8(PAL_STD[7]))
        cv.blit(img, GEM_PAL, 8 + i * 14, 20)
    menu9 = MENU_PAL[0][:5] + BANK9_EXTRA[5:]
    for i, (img, bank, white) in enumerate(CRESTS):
        pal = menu9 if bank == 9 else BADGE_PAL[0 if bank == 12 else 1]
        cv.blit(img, pal, 8 + i * 20, 40, skip0=False, fill0=white)
    cv.blit(CREST_EMPTY, PAL_STD, 128, 40, skip0=False, fill0=1)
    cv.save(path, 4)


def preview_frames(path):
    cv = Canvas(240, 120, (96, 176, 72))
    cv.blit(assemble_box(FRAME_STD, 10, 5), PAL_STD, 8, 8)
    cv.blit(assemble_box(FRAME_MENU, 10, 5), PAL_STD, 96, 8)
    cv.blit(assemble_box(FRAME_BATTLE, 12, 5), PAL_BATTLE, 8, 64)
    cv.blit(HUD_ENEMY, PAL_HUD, 112, 56)
    cv.save(path, 4)


def main():
    write_header()
    if "--preview" in sys.argv:
        d = sys.argv[sys.argv.index("--preview") + 1]
        os.makedirs(d, exist_ok=True)
        preview_font(os.path.join(d, "font.png"))
        preview_dialog(os.path.join(d, "dialog.png"))
        preview_battle(os.path.join(d, "battle.png"))
        preview_badges(os.path.join(d, "badges.png"))
        preview_frames(os.path.join(d, "frames.png"))
        preview_gems_crests(os.path.join(d, "gems_crests.png"))
    print("wrote", OUT_H)


if __name__ == "__main__":
    main()
