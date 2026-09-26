#!/usr/bin/env python3
"""Generate src/gfx_craft.h: art for the crafting minigames (craft.c).

  * three full-screen BG0 backdrops (240x160): the KITCHEN (cooking), the
    APOTHECARY (brewing) and the FORGE (forging), packed into at most six
    16-colour palette banks (BG banks 0-5; the field reloads them after);
  * OBJ sprites: the frying pan, food pile and chunks, a wooden spoon,
    gauge pointers, the cauldron's brew surface, a big bubble, the smith's
    hammer (three swing frames), the ingot (three shapes) and a beat mark,
    plus the rating labels (PERFECT!, GREAT!, GOOD, OK, MISS, BURNT,
    FIZZLED, CRACKED).

Sprites are drawn either with the fixed METAL palette (iron, wood, red and
gold) or with the value ramp the bout effects use (anim.c
build_fx_palette: 1 darkest/outline, 2 dark, 3 main, 4 light, 5
highlight, 6 white core, 7/8/9 secondary dark/mid/light), so food, brews,
glowing iron and labels are tinted at run time.

Everything is painted procedurally; standard library only, deterministic.

    python3 tools/gen_craft_gfx.py                 # writes src/gfx_craft.h
    python3 tools/gen_craft_gfx.py --preview DIR   # also writes preview PNGs
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_battle_gfx as g  # noqa: E402  (Canvas, masks, shading, PNG output)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_H = os.path.join(ROOT, "src", "gfx_craft.h")

C = g.C
Canvas = g.Canvas
WHITE = g.WHITE
SW, SH = 240, 160


# ==========================================================================
# palettes
# ==========================================================================

# METAL: iron, wood, the red pointer and brass. Index 1 = white.
METAL = [
    (0, 0, 0), WHITE, C(24, 20, 32),
    C(44, 44, 58), C(72, 74, 92), C(108, 112, 132), C(156, 162, 182), C(208, 212, 228),
    C(84, 48, 28), C(132, 80, 42), C(180, 120, 66), C(222, 168, 104),
    C(228, 56, 48), C(136, 24, 36), C(248, 208, 72), C(176, 120, 32),
]
M_OUT, M_I0, M_I1, M_I2, M_I3, M_I4 = 2, 3, 4, 5, 6, 7
M_W0, M_W1, M_W2, M_W3 = 8, 9, 10, 11
M_RED, M_RED_D, M_GOLD, M_GOLD_D = 12, 13, 14, 15


def fx_preview(main, sec):
    """Value-ramp palette the way anim.c build_fx_palette makes it."""
    return g.fx_palette(main, sec)


# ==========================================================================
# sprites
# ==========================================================================

def cv_new(w, h):
    return Canvas(w, h)


def fill_mask(cv, mask, v):
    for (x, y) in mask:
        cv.set(x, y, v)


def pan_sprite():
    """64x32 frying pan, 3/4 view: pan centre (24, 15), handle to the right."""
    cv = cv_new(64, 32)
    cx, cy = 24.0, 14.5
    rx, ry = 21.5, 7.6
    depth = 5
    # body side (visible below the rim)
    for y in range(32):
        for x in range(64):
            px, py = x + 0.5, y + 0.5
            ins_rim = ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 <= 1.0
            ins_side = ((px - cx) / (rx - 1.2)) ** 2 + ((py - cy - depth) / (ry - 0.6)) ** 2 <= 1.0
            if ins_side and not ins_rim and py > cy:
                n = (px - cx) / rx
                v = M_I2 if n < -0.55 else M_I1 if n < 0.35 else M_I0
                cv.set(x, y, v)
            if ins_rim:
                cv.set(x, y, 0)
    # rim ring and the dark cooking surface
    for y in range(32):
        for x in range(64):
            px, py = x + 0.5, y + 0.5
            d = ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2
            if d <= 1.0:
                di = ((px - cx) / (rx - 2.4)) ** 2 + ((py - cy + 0.4) / (ry - 1.8)) ** 2
                if di > 1.0:
                    # rim: lit on the far (top) edge
                    v = M_I4 if py < cy - 2 and px < cx + 8 else M_I3 if py < cy else M_I2
                    cv.set(x, y, v)
                else:
                    # inside: slight bowl shading, lighter toward the back
                    nx, ny = (px - cx) / (rx - 2.4), (py - cy) / (ry - 1.8)
                    b = -ny * 0.5 - nx * 0.25 + 0.2 - 0.3 * (nx * nx + ny * ny)
                    v = M_I2 if b > 0.28 else M_I1 if b > -0.15 else M_I0
                    cv.set(x, y, v)
    # glints on the rim
    for (x, y) in [(10, 9), (11, 8), (12, 8), (13, 8), (33, 8), (34, 8)]:
        cv.set(x, y, 1)
    # handle: riveted iron neck then a wooden grip, rising slightly
    for i in range(18):
        x = 45 + i
        yc = 14.0 - i * 0.18
        hw = 1.6 if i < 5 else 2.2
        for y in range(int(yc - hw - 0.5), int(yc + hw + 1.5)):
            t = (y + 0.5 - (yc - hw)) / (2 * hw + 1)
            if i < 5:
                v = M_I3 if t < 0.35 else M_I2 if t < 0.7 else M_I1
            else:
                v = M_W3 if t < 0.25 else M_W2 if t < 0.55 else M_W1 if t < 0.85 else M_W0
            cv.set(x, y, v)
    cv.set(59, 12, M_OUT)     # hanging hole
    cv.set(46, 13, M_I4)      # rivet
    g.outline(cv, M_OUT)
    return cv


def food_sprite(frame):
    """32x16 heap of food on the pan (value ramp: main = dish, sec = bits)."""
    cv = cv_new(32, 16)
    rng = g.Rng(77 + frame * 13)
    blobs = []
    for i in range(9):
        a = i / 9.0 * math.pi * 2 + frame * 0.7
        r = 6.0 if i % 3 else 3.0
        blobs.append((16 + math.cos(a) * r * 1.35, 9.5 + math.sin(a) * r * 0.45 - (1.5 if i % 3 == 0 else 0),
                      3.2 + (i % 2) * 0.8))
    blobs.append((16, 7.6, 4.4))
    for y in range(16):
        for x in range(32):
            best = None
            for (bx, by, br) in blobs:
                d = math.hypot((x + 0.5 - bx) / 1.1, y + 0.5 - by)
                if d <= br:
                    b = g.sphere_b((x + 0.5 - bx) / (br + 0.5), (y + 0.5 - by) / (br + 0.5))
                    if best is None or by > best[1]:
                        best = (b, by)
            if best is not None:
                cv.set(x, y, [2, 3, 4, 5][g.quant(best[0], (-0.1, 0.35, 0.78))])
    # speckles of the second colour (berries, herbs, chopped bits)
    for _ in range(14):
        x, y = rng.rand(5, 26), rng.rand(3, 13)
        if cv.get(x, y) is not None and cv.get(x + 1, y) is not None:
            cv.set(x, y, 8)
            cv.set(x + 1, y, 7 if rng.rand(0, 1) else 9)
    for (x, y) in [(11, 4), (12, 4), (18, 3)]:
        if cv.get(x, y) is not None:
            cv.set(x, y, 6)
    g.fx_outline(cv, 1)
    return cv


def chunk_sprites():
    """Four 8x8 bits tossed out of the pan: a ball, a cube, a leaf, a slice."""
    out = []
    ball = cv_new(8, 8)
    for y in range(8):
        for x in range(8):
            d = math.hypot(x + 0.5 - 4, y + 0.5 - 4)
            if d <= 2.9:
                b = g.sphere_b((x + 0.5 - 4) / 3.3, (y + 0.5 - 4) / 3.3)
                ball.set(x, y, [2, 3, 4, 5][g.quant(b, (-0.1, 0.35, 0.8))])
    ball.set(3, 2, 6)
    g.fx_outline(ball, 1)
    out.append(ball)
    cube = cv_new(8, 8)
    for y in range(2, 7):
        for x in range(2, 7):
            cube.set(x, y, 8 if y > 2 and x > 2 else 9)
    for y in range(3, 7):
        cube.set(6, y, 7)
    g.fx_outline(cube, 1)
    out.append(cube)
    leaf = cv_new(8, 8)
    for y in range(8):
        for x in range(8):
            u, v = x + 0.5 - 4, y + 0.5 - 4
            a, b = (u + v) * 0.7, (u - v) * 0.7
            if (a / 3.4) ** 2 + (b / 1.7) ** 2 <= 1:
                leaf.set(x, y, 8 if b > 0 else 9)
    for k in range(-2, 3):
        leaf.set(4 + k, 4 - k, 7)
    g.fx_outline(leaf, 1)
    out.append(leaf)
    sl = cv_new(8, 8)
    for y in range(8):
        for x in range(8):
            d = math.hypot(x + 0.5 - 4, y + 0.5 - 6)
            if d <= 3.6 and y + 0.5 <= 6:
                sl.set(x, y, 4 if d < 2.2 else 3)
    for x in range(1, 7):
        if sl.get(x, 5) is not None:
            sl.set(x, 5, 2)
    g.fx_outline(sl, 1)
    out.append(sl)
    return out


def spoon_sprite():
    """16x32 wooden spoon, bowl down (it stirs the pan)."""
    cv = cv_new(16, 32)
    for y in range(32):
        for x in range(16):
            px, py = x + 0.5, y + 0.5
            if 1.5 <= py <= 22 and abs(px - 8 - (22 - py) * 0.08) <= 1.3:
                cv.set(x, y, M_W2 if px < 8.2 + (22 - py) * 0.08 else M_W1)
            if ((px - 8) / 3.6) ** 2 + ((py - 25.5) / 4.6) ** 2 <= 1.0:
                b = g.sphere_b((px - 8) / 4.0, (py - 25.5) / 5.0)
                cv.set(x, y, [M_W0, M_W1, M_W2, M_W3][g.quant(b, (-0.2, 0.3, 0.75))])
    cv.set(7, 23, 1)
    g.outline(cv, M_OUT)
    return cv


def pointer_down():
    """16x16 gauge pointer: a red wedge pointing down, with a white glint."""
    cv = cv_new(16, 16)
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5, y + 0.5
            if 2 <= py <= 13 and abs(px - 8) <= (13 - py) * 0.5 + 0.2:
                cv.set(x, y, M_RED if px < 8.6 else M_RED_D)
    for y in range(3, 7):
        cv.set(6, y, 1)
    g.outline(cv, M_OUT)
    return cv


def bubble_big():
    """32x32 translucent bubble (value ramp); grown with affine scaling."""
    cv = cv_new(32, 32)
    cx = cy = 16.0
    R = 13.5
    for y in range(32):
        for x in range(32):
            px, py = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(px, py)
            if d > R:
                continue
            if d > R - 1.3:
                cv.set(x, y, 3 if px + py > -4 else 4)
            elif d > R - 3.0 and px + py > 6:
                cv.set(x, y, 2)
            elif py > 4 and d > R - 5.0:
                cv.set(x, y, 7)
    # curved highlight
    for k in range(-6, 3):
        a = math.radians(225 + k * 6)
        x = int(round(cx + (R - 3.4) * math.cos(a)))
        y = int(round(cy + (R - 3.4) * math.sin(a)))
        cv.set(x, y, 6)
        if k > -5:
            cv.set(x + 1, y + 1, 5)
    cv.set(21, 21, 6)
    cv.set(20, 22, 5)
    g.fx_outline(cv, 1)
    return cv


def bubble_pop():
    """32x32 burst: a broken ring of droplets."""
    cv = cv_new(32, 32)
    for k in range(10):
        a = k / 10.0 * math.pi * 2 + 0.2
        r = 12.0 if k % 2 else 10.0
        x0, y0 = 16 + r * math.cos(a), 16 + r * math.sin(a)
        for y in range(32):
            for x in range(32):
                d = math.hypot(x + 0.5 - x0, y + 0.5 - y0)
                if d <= 1.9 + (k % 3) * 0.4:
                    cv.set(x, y, 5 if d < 0.9 else 3)
    for k in range(8):
        a = k / 8.0 * math.pi * 2
        for r in (4.5, 5.5):
            cv.set(int(16 + r * math.cos(a)), int(16 + r * math.sin(a)), 6)
    g.fx_outline(cv, 1)
    return cv


def liquid_sprite():
    """64x32 brew surface for the cauldron mouth (value ramp): shaded disc
    with ripple rings in 8/9 that the game swaps to make them spread."""
    cv = cv_new(64, 32)
    cx, cy, rx, ry = 32.0, 16.0, 30.5, 9.2
    for y in range(32):
        for x in range(64):
            px, py = x + 0.5, y + 0.5
            nx, ny = (px - cx) / rx, (py - cy) / ry
            d = nx * nx + ny * ny
            if d > 1.0:
                continue
            r = math.sqrt(d)
            if r > 0.9:
                v = 2
            else:
                b = -ny * 0.55 - nx * 0.2 + 0.35 - 0.4 * d
                v = [2, 3, 4][g.quant(b, (-0.15, 0.2))]
            ring = (r * 4.2) % 1.0
            if 0.2 < r < 0.86 and 0.42 < ring < 0.62:
                v = 8 if int(r * 4.2) % 2 else 9
            cv.set(x, y, v)
    for (x, y) in [(20, 10), (21, 10), (22, 10), (24, 11), (40, 9), (41, 9)]:
        cv.set(x, y, 5)
    cv.set(22, 9, 6)
    return cv


def hammer_frames():
    """Three 32x32 smith's hammer frames (METAL): raised, mid swing, strike.
    The grip end stays at the same spot (27, 27) so frames swap cleanly."""
    frames = []
    pivot = (26.0, 24.0)

    def fn(u, v):
        # hammer laid out along -v (head at the far end); u across
        if -15.5 <= v <= 1.0 and abs(u) <= 1.25:
            return "w_hi" if u < 0 else "w_mid" if u < 0.7 else "w_dk"
        if 0.2 <= v <= 2.6 and abs(u) <= 1.5:
            return "w_dk"
        # head: a block across the handle end
        if -21.0 <= v <= -13.8 and -6.2 <= u <= 5.2:
            face = u > 4.0 or u < -5.0
            if face:
                return "i_hi" if v < -17.5 else "i_mid"
            if v < -19.8:
                return "i_hi"
            if v > -14.9:
                return "i_dk"
            return "i_mid" if u < 0 else "i_lo"
        return None

    roles = {"w_hi": M_W3, "w_mid": M_W2, "w_dk": M_W1, "i_hi": M_I4, "i_mid": M_I3,
             "i_lo": M_I2, "i_dk": M_I1}
    for ang in (15.0, -40.0, -92.0):
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        cv = cv_new(32, 32)
        for y in range(32):
            for x in range(32):
                votes = {}
                for sy in range(3):
                    for sx in range(3):
                        px = x + (sx + 0.5) / 3 - pivot[0]
                        py = y + (sy + 0.5) / 3 - pivot[1]
                        # rotate the screen point into hammer space
                        u = px * ca + py * sa
                        v = -px * sa + py * ca
                        r = fn(u, v)
                        votes[r] = votes.get(r, 0) + 1
                if votes.get(None, 0) >= 5:
                    continue
                best = max(((k, n) for k, n in votes.items() if k is not None), key=lambda kv: kv[1])
                cv.set(x, y, roles[best[0]])
        g.outline(cv, M_OUT)
        frames.append(cv)
    return frames


def ingot_frames():
    """Three 32x16 shapes of the hot metal (value ramp: main = glow):
    a rough lump, a flattened bar and the finished blank."""
    out = []
    shapes = [
        lambda px, py: ((px - 16) / 8.5) ** 2 + ((py - 10) / 4.6) ** 2 <= 1.0 or
        ((px - 12) / 5) ** 2 + ((py - 7.5) / 3.2) ** 2 <= 1.0,
        lambda px, py: abs(px - 16) <= 11 - max(0, 10 - py) * 0.5 and 7 <= py <= 13,
        lambda px, py: abs(px - 16) <= 13 and 8 <= py <= 12.8 and not (abs(px - 16) <= 2 and py < 9.2),
    ]
    for k, sh in enumerate(shapes):
        cv = cv_new(32, 16)
        for y in range(16):
            for x in range(32):
                px, py = x + 0.5, y + 0.5
                if sh(px, py):
                    t = (py - 6) / 8.0
                    v = 5 if t < 0.25 else 4 if t < 0.55 else 3 if t < 0.85 else 2
                    cv.set(x, y, v)
        # hot core streak
        for x in range(10, 23):
            if cv.get(x, 9) is not None and cv.get(x, 8) is not None:
                cv.set(x, 9, 6 if k else 5)
        g.fx_outline(cv, 1)
        out.append(cv)
    return out


def mark_sprite():
    """16x16 beat mark: a glowing diamond with a white core (value ramp)."""
    cv = cv_new(16, 16)
    for y in range(16):
        for x in range(16):
            px, py = x + 0.5 - 8, y + 0.5 - 8
            d = abs(px) + abs(py)
            if d <= 6.2:
                v = 6 if d < 1.6 else 5 if d < 3.0 else 4 if (px + py < 0) else 3
                if d > 5.2:
                    v = 2 if px + py > 0 else 3
                cv.set(x, y, v)
    g.fx_outline(cv, 1)
    return cv


# ---- labels: chunky outlined letters, value ramp ---------------------------

FONT = {
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "N": ["#...#", "##..#", "#.#.#", "#.#.#", "#..##", "#...#", "#...#"],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "!": ["#", "#", "#", "#", ".", ".", "#"],
}


def label(text, w):
    """Outlined text, w x 16, centred; letters shaded top-light to bottom."""
    cv = cv_new(w, 16)
    tw = sum(len(FONT[ch][0]) + 1 for ch in text) - 1
    x = (w - tw) // 2
    y0 = 4
    for ch in text:
        glyph = FONT[ch]
        for r, row in enumerate(glyph):
            for c, v in enumerate(row):
                if v == "#":
                    col = 5 if r == 0 else 4 if r < 3 else 3 if r < 5 else 2
                    cv.set(x + c, y0 + r, col)
                    # a 2px-deep drop: letters look chunky
                    cv.set(x + c, y0 + r + 1, cv.get(x + c, y0 + r + 1) or 2)
        x += len(glyph[0]) + 1
    for yy in range(16):
        for xx in range(w):
            if cv.get(xx, yy) == 5 and (xx + yy) % 3 == 0:
                cv.set(xx, yy, 6)
    g.fx_outline(cv, 1, diag=True)
    return cv


LABELS = [("PERFECT", "PERFECT!", 64), ("GREAT", "GREAT!", 64), ("GOOD", "GOOD", 32),
          ("OK", "OK", 32), ("MISS", "MISS", 32), ("BURNT", "BURNT", 64),
          ("FIZZLED", "FIZZLED", 64), ("CRACKED", "CRACKED", 64)]


# ---- sprite table ------------------------------------------------------------

def to_idx(cv):
    return [[0 if v is None else v for v in row] for row in cv.p]


def obj_tiles(img, w, h):
    """Tiles of one OBJ in 1D mapping order. 64-wide images are split into
    two 32-wide halves (drawn as two sprites)."""
    if w == 64:
        left = [row[:32] for row in img]
        right = [row[32:] for row in img]
        return obj_tiles(left, 32, h) + obj_tiles(right, 32, h)
    return g.tiles_from_indices(img, w // 8, h // 8)


def build_sprites():
    """[(NAME, w, h, [frame canvases])] in export order."""
    sp = []
    sp.append(("PAN", 64, 32, [pan_sprite()]))
    sp.append(("FOOD", 32, 16, [food_sprite(0), food_sprite(1)]))
    sp.append(("CHUNK", 8, 8, chunk_sprites()))
    sp.append(("SPOON", 16, 32, [spoon_sprite()]))
    sp.append(("POINTER", 16, 16, [pointer_down()]))
    sp.append(("LIQUID", 64, 32, [liquid_sprite()]))
    sp.append(("BUBBLE", 32, 32, [bubble_big(), bubble_pop()]))
    sp.append(("HAMMER", 32, 32, hammer_frames()))
    sp.append(("INGOT", 32, 16, ingot_frames()))
    sp.append(("MARK", 16, 16, [mark_sprite()]))
    for (name, text, w) in LABELS:
        sp.append(("LBL_" + name, w, 16, [label(text, w)]))
    return sp


# ==========================================================================
# backdrops (240x160, 5-bit colour images)
# ==========================================================================

class Paint:
    """A 240x160 colour image with a few drawing helpers."""

    def __init__(self, fill):
        self.S = [[fill] * SW for _ in range(SH)]

    def px(self, x, y, c):
        if 0 <= x < SW and 0 <= y < SH and c is not None:
            self.S[y][x] = c

    def get(self, x, y):
        if 0 <= x < SW and 0 <= y < SH:
            return self.S[y][x]
        return None

    def rect(self, x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(SH - 1, y1) + 1):
            for x in range(max(0, x0), min(SW - 1, x1) + 1):
                self.S[y][x] = c

    def hline(self, x0, x1, y, c):
        self.rect(x0, y, x1, y, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, y0, x, y1, c)

    def frame(self, x0, y0, x1, y1, c):
        self.hline(x0, x1, y0, c)
        self.hline(x0, x1, y1, c)
        self.vline(x0, y0, y1, c)
        self.vline(x1, y0, y1, c)

    def mask(self, m, c):
        for (x, y) in m:
            self.px(x, y, c)

    def ellipse(self, cx, cy, rx, ry, fn):
        """fn(nx, ny) -> colour/None for pixels inside the ellipse."""
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                if nx * nx + ny * ny <= 1.0:
                    c = fn(nx, ny)
                    if c is not None:
                        self.px(x, y, c)

    def outline_mask(self, m, c):
        for (x, y) in m:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + dx, y + dy) not in m:
                    self.px(x, y, c)
                    break

    def dither(self, x0, y0, x1, y1, a, b, level):
        """Ordered dither between a and b; level 0..4 (4 = all b)."""
        B = [[0, 2], [3, 1]]
        for y in range(max(0, y0), min(SH - 1, y1) + 1):
            for x in range(max(0, x0), min(SW - 1, x1) + 1):
                self.S[y][x] = b if B[y & 1][x & 1] < level else a


def poly(pts):
    return g.poly_mask(pts, SW, SH)


def ell_mask(cx, cy, rx, ry):
    return g.ellipse_mask(cx, cy, rx, ry)


# ---- the kitchen --------------------------------------------------------------

K = {
    "tile_hi": C(252, 246, 228), "tile": C(238, 226, 198), "tile_sh": C(222, 206, 172),
    "grout": C(200, 180, 150),
    "out": C(56, 36, 36),
    "wd0": C(92, 54, 34), "wd1": C(140, 88, 50), "wd2": C(190, 132, 76), "wd3": C(228, 178, 116),
    "gl": C(206, 232, 240), "gl_dk": C(136, 180, 204),
    "jam": C(200, 52, 68), "jam_hi": C(240, 112, 120), "honey": C(240, 172, 40), "honey_hi": C(255, 220, 120),
    "herb": C(84, 160, 72), "herb_hi": C(150, 212, 108), "herb_dk": C(48, 108, 56),
    "lid": C(216, 160, 56), "red": C(208, 72, 64),
    "sky": C(150, 204, 248), "sky_lo": C(200, 232, 250), "hill": C(116, 186, 96), "hill_dk": C(80, 150, 80),
    "frame": C(250, 250, 244), "frame_sh": C(208, 208, 204),
    "cur": C(226, 92, 84), "cur_hi": C(250, 190, 176),
    "pot": C(206, 110, 70), "pot_dk": C(150, 70, 48),
    "brass": C(226, 176, 64), "brass_dk": C(160, 108, 36),
    "i0": C(34, 34, 46), "i1": C(54, 56, 70), "i2": C(84, 88, 106), "i3": C(126, 130, 150), "i4": C(178, 182, 200),
    "cab": C(78, 150, 156), "cab_hi": C(124, 190, 188), "cab_dk": C(46, 102, 112),
    "ctr_hi": C(240, 200, 140),
    "carrot": C(240, 132, 40), "carrot_dk": C(196, 88, 32),
    "berry": C(120, 72, 200), "berry_hi": C(184, 150, 250),
    "glow_hi": C(255, 230, 150),
}
# shared shades keep every 8x8 cell within a few palette banks
K.update({
    "red": K["jam"], "lid": K["brass"], "leaf": K["herb"], "pot": K["carrot_dk"], "pot_dk": K["wd0"],
    "frame": K["tile_hi"], "frame_sh": K["tile_sh"], "gl": K["sky_lo"], "honey_hi": K["glow_hi"],
    "honey": K["brass"], "glow": K["brass"], "jam_hi": K["cur"], "bowl": K["tile_hi"], "bowl_dk": K["i4"],
    "ctr": K["wd3"], "ctr_dk": K["wd2"],
})


def paint_kitchen():
    P = Paint(K["tile"])
    k = K
    # ---- wall: subway tiles, 16x8, offset rows
    for y in range(0, 96):
        row = y // 8
        off = 8 if row % 2 else 0
        for x in range(SW):
            lx = (x + off) % 16
            ly = y % 8
            if ly == 7 or lx == 15:
                c = k["grout"]
            elif ly == 0 or lx == 0:
                c = k["tile_hi"]
            elif ly == 6 or lx == 14:
                c = k["tile_sh"]
            else:
                c = k["tile"]
            P.px(x, y, c)
    # ---- window on the right (sky, hills, curtains, sill with a pot of herbs)
    wx0, wy0, wx1, wy1 = 176, 16, 231, 76
    P.rect(wx0, wy0, wx1, wy1, k["frame"])
    P.rect(wx0 + 4, wy0 + 4, wx1 - 4, wy1 - 6, k["sky"])
    P.rect(wx0 + 4, wy0 + 30, wx1 - 4, wy1 - 6, k["sky_lo"])
    for x in range(wx0 + 4, wx1 - 3):
        h = int(8 + 4 * math.sin((x - wx0) * 0.13) + 2 * math.sin((x - wx0) * 0.37))
        for y in range(wy1 - 6 - h, wy1 - 5):
            P.px(x, y, k["hill"] if y < wy1 - 6 - h + 3 or (x + y) % 5 else k["hill_dk"])
    P.rect(wx0 + 4, wy0 + 30, wx1 - 4, wy0 + 31, k["frame"])  # muntin
    P.vline((wx0 + wx1) // 2, wy0 + 4, wy1 - 6, k["frame"])
    P.frame(wx0, wy0, wx1, wy1, k["out"])
    P.hline(wx0 + 1, wx1 - 1, wy1 - 5, k["frame_sh"])
    P.rect(wx0 - 4, wy1 - 3, wx1 + 4, wy1, k["frame"])        # sill
    P.frame(wx0 - 4, wy1 - 3, wx1 + 4, wy1 + 1, k["out"])
    P.hline(wx0 - 3, wx1 + 3, wy1, k["frame_sh"])
    for side in (0, 1):                                        # curtains
        for y in range(wy0 - 2, wy1 - 8):
            t = (y - wy0) / (wy1 - wy0)
            wdt = int(10 - 5 * math.sin(t * math.pi * 0.9))
            for i in range(wdt):
                x = wx0 - 3 + i if side == 0 else wx1 + 3 - i
                c = k["cur"] if (i // 2 + y // 3) % 2 else k["cur_hi"]
                if i == wdt - 1:
                    c = k["out"]
                P.px(x, y, c)
    P.rect(wx0 - 6, wy0 - 4, wx1 + 6, wy0 - 2, k["brass"])       # rod
    P.hline(wx0 - 6, wx1 + 6, wy0 - 2, k["brass_dk"])
    # herb pot on the sill
    pm = poly([(190, 76), (206, 76), (204, 64), (192, 64)])
    P.mask(pm, k["pot"])
    P.rect(190, 62, 206, 65, k["pot"])
    P.outline_mask(pm | set((x, y) for x in range(190, 207) for y in range(62, 66)), k["out"])
    P.hline(191, 205, 64, k["pot_dk"])
    for (x, y) in [(193, 60), (195, 57), (197, 55), (199, 54), (201, 56), (203, 59), (196, 60),
                   (199, 58), (202, 61), (194, 58), (200, 52), (198, 56)]:
        for dx, dy in ((0, 0), (1, 0), (0, 1)):
            P.px(x + dx, y + dy, k["herb"])
        P.px(x, y, k["herb_hi"])
    # ---- shelf on the left with jars
    sy = 74
    P.rect(8, sy, 96, sy + 3, k["wd2"])
    P.hline(8, 96, sy, k["wd3"])
    P.hline(8, 96, sy + 3, k["wd0"])
    P.frame(7, sy - 1, 97, sy + 4, k["out"])
    for bx in (16, 86):
        P.rect(bx, sy + 5, bx + 3, sy + 10, k["wd1"])
        P.frame(bx - 1, sy + 4, bx + 4, sy + 11, k["out"])
    jars = [(14, 14, 20, "jam", "jam_hi", "lid"), (32, 12, 16, "honey", "honey_hi", "red"),
            (48, 10, 22, "herb", "herb_hi", "lid"), (62, 14, 14, "jam", "jam_hi", "red"),
            (80, 12, 18, "honey", "honey_hi", "lid")]
    for (jx, jw, jh, fill, fill_hi, lid) in jars:
        top = sy - jh
        m = set()
        for y in range(top, sy):
            for x in range(jx, jx + jw):
                m.add((x, y))
        P.mask(m, k["gl"])
        lvl = top + jh // 3
        for (x, y) in m:
            if y >= lvl + 1 and jx + 1 <= x <= jx + jw - 2:
                P.px(x, y, k[fill])
        for y in range(lvl + 2, sy - 1):
            P.px(jx + 2, y, k[fill_hi])
        P.rect(jx - 1, top - 3, jx + jw, top, k[lid])
        P.outline_mask(m | set((x, y) for x in range(jx - 1, jx + jw + 1) for y in range(top - 3, top + 1)),
                       k["out"])
        P.vline(jx + jw - 2, top + 2, sy - 2, k["gl_dk"])
        P.px(jx + 1, top + 2, k["frame"])
    # hanging ladle and whisk on hooks under the shelf? (keep the centre calm)
    # ---- counter top (butcher block) and cabinets
    CT = 96
    P.rect(0, CT, SW - 1, CT + 7, k["ctr"])
    P.hline(0, SW - 1, CT, k["ctr_hi"])
    P.hline(0, SW - 1, CT + 1, k["ctr_hi"])
    for x in range(0, SW, 24):
        P.vline(x, CT + 2, CT + 7, k["ctr_dk"])
    P.hline(0, SW - 1, CT - 1, k["out"])
    P.hline(0, SW - 1, CT + 7, k["ctr_dk"])
    P.hline(0, SW - 1, CT + 8, k["out"])
    # cabinets below
    for y in range(CT + 9, SH):
        for x in range(SW):
            P.px(x, y, k["cab"])
    for (x0, x1) in ((0, 30), (32, 62), (178, 208), (210, 240)):
        P.frame(x0 + 3, CT + 13, x1 - 3, SH - 4, k["cab_dk"])
        P.hline(x0 + 4, x1 - 4, CT + 14, k["cab_hi"])
        P.vline(x0 + 4, CT + 14, SH - 5, k["cab_hi"])
        kx = x1 - 8 if x0 % 64 == 0 else x0 + 7
        P.rect(kx, CT + 30, kx + 1, CT + 31, k["brass"])
        P.px(kx, CT + 30, k["brass"])
        P.px(kx + 1, CT + 31, k["brass_dk"])
    P.rect(0, CT + 9, SW - 1, CT + 10, k["cab_dk"])
    # ---- the stove: iron top with a burner, front with knobs and an oven door
    SX0, SX1 = 64, 175
    top_y0, top_y1 = CT - 2, CT + 26
    P.rect(SX0, top_y0, SX1, SH - 1, k["i1"])
    P.rect(SX0, top_y0, SX1, top_y1, k["i0"])
    P.hline(SX0, SX1, top_y0, k["i3"])
    P.hline(SX0 + 1, SX1 - 1, top_y0 + 1, k["i2"])
    P.frame(SX0 - 1, top_y0 - 1, SX1 + 1, SH, k["out"])
    # burner: a ring of grate prongs around the flame port
    bcx, bcy = 120, CT + 17
    P.ellipse(bcx, bcy, 26, 7.5, lambda nx, ny: k["i1"] if nx * nx + ny * ny > 0.72 else None)
    P.ellipse(bcx, bcy, 17, 4.6, lambda nx, ny: k["i2"] if nx * nx + ny * ny > 0.5 else k["i0"])
    for a in range(0, 360, 45):
        r = math.radians(a)
        for t in range(10, 27):
            x = int(round(bcx + math.cos(r) * t))
            y = int(round(bcy + math.sin(r) * t * 0.29))
            P.px(x, y, k["i3"])
    P.ellipse(bcx, bcy, 26, 7.5, lambda nx, ny: k["i3"] if nx * nx + ny * ny > 0.9 else None)
    # front: knob rail, oven door with a warm window
    P.rect(SX0, top_y1 + 1, SX1, top_y1 + 9, k["i2"])
    P.hline(SX0, SX1, top_y1 + 1, k["i3"])
    P.hline(SX0, SX1, top_y1 + 9, k["i0"])
    for kx in (78, 96, 144, 162):
        P.ellipse(kx, top_y1 + 5, 3.2, 3.2, lambda nx, ny: k["brass"] if nx + ny < 0.4 else k["brass_dk"])
        P.px(kx - 1, top_y1 + 4, k["glow_hi"])
    dx0, dy0, dx1, dy1 = SX0 + 10, top_y1 + 13, SX1 - 10, SH - 4
    P.rect(dx0, dy0, dx1, dy1, k["i1"])
    P.frame(dx0, dy0, dx1, dy1, k["out"])
    P.hline(dx0 + 1, dx1 - 1, dy0 + 1, k["i3"])
    P.rect(dx0 + 6, dy0 + 3, dx1 - 6, dy0 + 5, k["brass"])       # handle bar
    P.hline(dx0 + 6, dx1 - 6, dy0 + 5, k["brass_dk"])
    wx0, wy0, wx1, wy1 = dx0 + 16, dy0 + 9, dx1 - 16, dy1 - 3
    P.rect(wx0, wy0, wx1, wy1, k["glow"])
    P.rect(wx0 + 2, wy0 + 2, wx1 - 2, wy1 - 2, k["glow_hi"])
    P.dither(wx0 + 2, wy0 + 2, wx1 - 2, wy0 + 4, k["glow_hi"], k["glow"], 2)
    P.frame(wx0 - 1, wy0 - 1, wx1 + 1, wy1 + 1, k["i0"])
    # ---- counter clutter: a cutting board with carrots, a bowl of berries
    bx0, by0 = 12, CT - 4
    P.rect(bx0, by0, bx0 + 38, by0 + 5, k["wd2"])
    P.hline(bx0, bx0 + 38, by0, k["wd3"])
    P.frame(bx0 - 1, by0 - 1, bx0 + 39, by0 + 6, k["out"])
    for cx0 in (16, 28):
        for i in range(10):
            P.px(cx0 + i, by0 - 1 - (i // 5), k["carrot"])
            P.px(cx0 + i, by0 - 2 - (i // 5), k["carrot"] if i > 1 else k["carrot_dk"])
        P.px(cx0 + 10, by0 - 3, k["leaf"])
        P.px(cx0 + 11, by0 - 4, k["leaf"])
        P.px(cx0 + 10, by0 - 4, k["leaf"])
    # bowl with berries
    bcx2, bcy2 = 200, CT - 1
    P.ellipse(bcx2, bcy2, 14, 5, lambda nx, ny: k["bowl"] if ny < 0.2 else k["bowl_dk"])
    for i, (x, y) in enumerate([(192, CT - 7), (197, CT - 8), (202, CT - 8), (207, CT - 7), (195, CT - 5),
                                (200, CT - 5), (205, CT - 5)]):
        P.ellipse(x, y, 2.6, 2.6, lambda nx, ny: k["berry_hi"] if nx + ny < -0.6 else k["berry"])
    P.hline(186, 214, CT + 3, k["out"])
    return P.S


# ---- the apothecary -----------------------------------------------------------

A = {
    "out": C(24, 16, 28),
    "pl0": C(46, 32, 52), "pl1": C(62, 44, 66), "pl2": C(80, 58, 80), "pl3": C(100, 76, 96),
    "beam": C(58, 38, 34), "beam_hi": C(96, 66, 50),
    "sh0": C(88, 58, 42), "sh1": C(128, 88, 58), "sh2": C(164, 118, 76),
    "teal": C(76, 228, 196), "teal_dk": C(34, 150, 150),
    "pink": C(248, 128, 204), "pink_dk": C(170, 64, 150),
    "amber": C(255, 198, 80), "amber_dk": C(200, 120, 32),
    "violet": C(170, 128, 250), "violet_dk": C(100, 70, 186),
    "glass": C(188, 206, 226), "cork": C(176, 128, 80),
    "herb": C(98, 150, 74), "herb_dk": C(62, 100, 56), "dry": C(176, 150, 88), "string": C(210, 190, 140),
    "st0": C(56, 52, 66), "st1": C(78, 74, 90), "st2": C(102, 98, 114), "st3": C(128, 124, 140),
    "i0": C(22, 20, 30), "i1": C(38, 36, 52), "i2": C(62, 60, 80), "i3": C(96, 96, 120), "i4": C(146, 146, 172),
    "moon": C(236, 240, 255), "night": C(40, 50, 100), "night_hi": C(70, 84, 150),
    "candle": C(244, 232, 206), "flame": C(255, 214, 90),
    "fire": C(255, 150, 40), "ember": C(200, 70, 30),
}


def paint_apothecary():
    a = A
    P = Paint(a["pl1"])
    # ---- plank wall with vertical boards
    for y in range(0, 124):
        for x in range(SW):
            lx = x % 20
            c = a["pl1"]
            if lx == 0:
                c = a["pl0"]
            elif lx == 1:
                c = a["pl2"]
            elif (x * 7 + y * 3) % 53 == 0 or (lx == 10 and (y // 9) % 3 == 1):
                c = a["pl0"]
            P.px(x, y, c)
        if y % 40 == 39:
            P.hline(0, SW - 1, y, a["pl0"])
    # a glow spot behind the cauldron (warm light on the boards)
    for y in range(56, 124):
        for x in range(40, 180):
            d = math.hypot((x - 108) / 70.0, (y - 118) / 52.0)
            if d < 1.0 and P.get(x, y) == a["pl1"] and (x + y) % 2 == 0 and d > 0.55:
                P.px(x, y, a["pl2"])
            elif d <= 0.55 and P.get(x, y) == a["pl1"]:
                P.px(x, y, a["pl2"] if (x + y) % 2 else a["pl3"])
    # ---- top beam with drying herbs
    P.rect(0, 30, SW - 1, 37, a["beam"])
    P.hline(0, SW - 1, 30, a["beam_hi"])
    P.hline(0, SW - 1, 29, a["out"])
    P.hline(0, SW - 1, 38, a["out"])
    for i, hx in enumerate(range(90, 200, 22)):
        ln = 10 + (i % 3) * 4
        P.vline(hx, 39, 39 + ln, a["string"])
        col, dk = (a["herb"], a["herb_dk"]) if i % 2 == 0 else (a["dry"], a["sh0"])
        for dy in range(0, 12):
            wdt = 1 + dy // 3
            for dx in range(-wdt, wdt + 1):
                c = dk if dx == wdt or dy == 11 else col
                if (dx + dy) % 4 == 0:
                    c = dk
                P.px(hx + dx, 39 + ln + dy, c)
        P.rect(hx - 1, 38 + ln, hx + 1, 39 + ln, a["string"])
    # ---- shelves of glowing jars on the left
    shelf_ys = (62, 88, 114)
    for sy in shelf_ys:
        P.rect(4, sy, 70, sy + 3, a["sh1"])
        P.hline(4, 70, sy, a["sh2"])
        P.hline(4, 70, sy + 3, a["sh0"])
        P.frame(3, sy - 1, 71, sy + 4, a["out"])
    P.rect(4, 44, 6, 117, a["sh0"])
    P.rect(68, 44, 70, 117, a["sh0"])
    jar_kinds = [("teal", "teal_dk"), ("pink", "pink_dk"), ("amber", "amber_dk"), ("violet", "violet_dk")]
    jn = 0
    for si, sy in enumerate(shelf_ys):
        x = 9 + (si % 2) * 4
        while x < 62:
            kind = jar_kinds[jn % 4]
            jn += 1
            w = 8 + (jn % 3) * 2
            h = 10 + (jn % 2) * 5
            if x + w > 66:
                break
            top = sy - h
            m = set()
            if jn % 3 == 0:     # round flask
                cx, cy, r = x + w / 2, sy - r_of(h), r_of(h)
                m = set(p for p in ell_mask(cx, sy - h * 0.45, w / 2 + 0.5, h * 0.45) if p[1] < sy)
                neck = set((xx, yy) for xx in range(int(cx) - 1, int(cx) + 2) for yy in range(top - 3, top + 2))
                m |= neck
            else:
                m = set((xx, yy) for xx in range(x, x + w) for yy in range(top, sy))
            P.mask(m, a[kind[1]])
            for (px_, py_) in m:
                if py_ > top + 2 and px_ > min(p[0] for p in m) + 1:
                    P.px(px_, py_, a[kind[0]] if (px_ + py_) % 7 else a[kind[1]])
            P.outline_mask(m, a["out"])
            lx = min(p[0] for p in m) + 1
            for yy in range(top + 2, sy - 2):
                if (lx, yy) in m:
                    P.px(lx, yy, a["glass"])
            ty = min(p[1] for p in m)
            cx = (min(p[0] for p in m) + max(p[0] for p in m)) // 2
            P.rect(cx - 1, ty - 2, cx + 1, ty, a["cork"])
            P.frame(cx - 2, ty - 3, cx + 2, ty, a["out"])
            x += w + 3
    # ---- a round window with the moon (upper right, above the thermometer)
    wcx, wcy, wr = 176, 72, 17
    P.ellipse(wcx, wcy, wr, wr, lambda nx, ny: a["night_hi"] if ny > 0.35 else a["night"])
    P.ellipse(wcx + 3, wcy - 4, 6.5, 6.5, lambda nx, ny: a["moon"])
    P.ellipse(wcx + 7, wcy - 6, 5.5, 5.5, lambda nx, ny: a["night"])
    for (sx, sy_) in [(166, 64), (170, 80), (184, 80), (163, 74)]:
        P.px(sx, sy_, a["moon"])
    ring = set(p for p in ell_mask(wcx, wcy, wr + 3, wr + 3)) - set(p for p in ell_mask(wcx, wcy, wr, wr))
    P.mask(ring, a["sh1"])
    P.outline_mask(ring, a["out"])
    P.hline(wcx - wr, wcx + wr, wcy, a["sh1"])
    P.vline(wcx, wcy - wr, wcy + wr, a["sh1"])
    # candle on a little bracket under the window
    P.rect(166, 100, 186, 102, a["sh1"])
    P.frame(165, 99, 187, 103, a["out"])
    P.rect(174, 90, 177, 99, a["candle"])
    P.frame(173, 89, 178, 99, a["out"])
    P.rect(175, 85, 176, 88, a["flame"])
    P.px(175, 84, a["flame"])
    # ---- stone floor
    for y in range(124, SH):
        for x in range(SW):
            row = (y - 124) // 12
            off = 14 if row % 2 else 0
            lx = (x + off) % 28
            ly = (y - 124) % 12
            c = a["st1"]
            if ly == 11 or lx == 27:
                c = a["st0"]
            elif ly == 0 or lx == 0:
                c = a["st2"]
            elif (x * 5 + y * 11) % 37 == 0:
                c = a["st0"]
            P.px(x, y, c)
    P.hline(0, SW - 1, 123, a["out"])
    # ---- the hearth ring and the cauldron
    ccx = 108
    P.ellipse(ccx, 146, 56, 11, lambda nx, ny: a["st3"] if ny < -0.2 else a["st2"])
    ring_in = ell_mask(ccx, 146, 44, 7.5)
    P.mask(ring_in, a["i0"])
    P.outline_mask(ell_mask(ccx, 146, 56, 11), a["out"])
    for i in range(12):
        ang = i / 12.0 * math.pi * 2
        x = int(ccx + math.cos(ang) * 50)
        y = int(146 + math.sin(ang) * 9.3)
        P.px(x, y, a["st0"])
    # embers in the fire pit
    for (x, y) in [(80, 146), (86, 149), (94, 147), (122, 149), (130, 146), (136, 148), (100, 150),
                   (114, 151)]:
        P.px(x, y, a["ember"])
        P.px(x + 1, y, a["fire"])
    # cauldron body: a squat iron belly, rim at y 100
    body = set()
    for y in range(96, 146):
        t = (y - 96) / 50.0
        hw = 38 + 12 * math.sin(min(1.0, t * 1.25) * math.pi * 0.62) - (max(0.0, t - 0.8) * 60)
        for x in range(int(ccx - hw), int(ccx + hw) + 1):
            body.add((x, y))
    for (x, y) in body:
        n = (x + 0.5 - ccx) / 50.0
        v = -n * 0.7 + 0.35 - ((y - 118) / 30.0) ** 2 * 0.3
        c = a["i3"] if v > 0.62 else a["i2"] if v > 0.3 else a["i1"] if v > -0.05 else a["i0"]
        P.px(x, y, c)
    # legs
    for lx in (ccx - 30, ccx + 26):
        P.rect(lx, 140, lx + 4, 150, a["i1"])
        P.px(lx, 140, a["i2"])
    P.outline_mask(body, a["out"])
    # rim: a thick lip ellipse around the mouth; mouth dark (the brew is a sprite)
    P.ellipse(ccx, 100, 38, 10, lambda nx, ny: a["i4"] if ny < -0.35 else a["i3"] if ny < 0.2 else a["i2"])
    P.ellipse(ccx, 100.5, 32, 8, lambda nx, ny: a["i0"])
    P.outline_mask(ell_mask(ccx, 100, 38, 10), a["out"])
    # a highlight streak on the belly
    for y in range(110, 134):
        x = int(ccx - 30 + (y - 110) * 0.18)
        P.px(x, y, a["i4"] if y < 124 else a["i3"])
    return P.S


def r_of(h):
    return h * 0.45


# ---- the forge --------------------------------------------------------------------

F = {
    "out": C(26, 18, 22),
    "b0": C(52, 42, 46), "b1": C(74, 62, 62), "b2": C(98, 84, 80), "b3": C(124, 108, 98),
    "mortar": C(38, 30, 34),
    "warm1": C(118, 78, 58), "warm2": C(156, 96, 60),
    "g0": C(120, 36, 26), "g1": C(200, 70, 30), "g2": C(248, 142, 44), "g3": C(255, 206, 94), "g4": C(255, 248, 200),
    "coal": C(34, 28, 32), "coal_hi": C(70, 58, 60),
    "i0": C(28, 28, 38), "i1": C(50, 52, 66), "i2": C(80, 84, 102), "i3": C(120, 124, 146), "i4": C(172, 176, 198),
    "i5": C(224, 228, 242),
    "w0": C(84, 52, 34), "w1": C(124, 80, 50), "w2": C(164, 112, 70), "w3": C(198, 150, 98),
    "fl0": C(66, 52, 46), "fl1": C(88, 70, 58), "fl2": C(112, 90, 72),
    "water": C(60, 100, 164), "water_hi": C(110, 156, 212), "hoop": C(96, 96, 112),
}


def paint_forge():
    f = F
    P = Paint(f["b1"])
    # ---- brick wall
    for y in range(0, 112):
        row = y // 10
        off = 12 if row % 2 else 0
        for x in range(SW):
            lx = (x + off) % 24
            ly = y % 10
            if ly == 9 or lx == 23:
                c = f["mortar"]
            elif ly == 0:
                c = f["b2"]
            elif (x // 24 + row) % 5 == 0:
                c = f["b0"]
            elif (x // 24 + row * 3) % 7 == 0:
                c = f["b2"]
            else:
                c = f["b1"]
            P.px(x, y, c)
    # warm light from the forge on the bricks (left side)
    for y in range(20, 112):
        for x in range(0, 150):
            d = math.hypot((x - 36) / 110.0, (y - 84) / 70.0)
            cur = P.get(x, y)
            if d < 0.55 and cur in (f["b1"], f["b2"], f["b0"]):
                P.px(x, y, f["warm2"] if (d < 0.35 and (x + y) % 2 == 0) or d < 0.25 else f["warm1"])
            elif d < 0.8 and cur in (f["b1"],) and (x + y) % 2 == 0:
                P.px(x, y, f["warm1"])
    # ---- the forge hearth: a stone arch with glowing coals
    hx0, hx1, hy0, hy1 = 6, 74, 40, 112
    P.rect(hx0, hy0, hx1, hy1, f["b2"])
    for y in range(hy0, hy1 + 1):
        for x in range(hx0, hx1 + 1):
            if (x - hx0) % 12 == 0 or (y - hy0) % 8 == 0:
                P.px(x, y, f["b1"])
    P.frame(hx0, hy0, hx1, hy1, f["out"])
    # chimney hood above
    hood = poly([(hx0 - 4, hy0), (hx1 + 4, hy0), (hx1 - 8, 8), (hx0 + 8, 8)])
    P.mask(hood, f["b0"])
    for (x, y) in hood:
        if (y % 6 == 0) or ((x + (y // 6) * 5) % 14 == 0):
            P.px(x, y, f["mortar"])
    P.outline_mask(hood, f["out"])
    P.rect(hx0 - 6, hy0 - 3, hx1 + 6, hy0, f["b3"])
    P.frame(hx0 - 6, hy0 - 3, hx1 + 6, hy0 + 1, f["out"])
    # the mouth: arch-shaped opening with a gradient of heat
    mcx, mtop, mbot, mhw = 40, 58, 104, 25
    mouth = set()
    for y in range(mtop, mbot + 1):
        for x in range(mcx - mhw, mcx + mhw + 1):
            if y < mtop + mhw:
                if math.hypot(x + 0.5 - mcx, y + 0.5 - (mtop + mhw)) <= mhw:
                    mouth.add((x, y))
            else:
                mouth.add((x, y))
    for (x, y) in mouth:
        t = (y - mtop) / float(mbot - mtop)
        d = abs(x + 0.5 - mcx) / mhw
        heat = t * 1.1 - d * 0.35
        c = f["g4"] if heat > 0.9 else f["g3"] if heat > 0.7 else f["g2"] if heat > 0.45 else f["g1"] if heat > 0.2 else f["g0"]
        P.px(x, y, c)
    P.outline_mask(mouth, f["out"])
    # heap of coals at the bottom of the mouth
    rng = g.Rng(314)
    for i in range(40):
        x = mcx + rng.rand(-22, 22)
        y = mbot - rng.rand(0, 6)
        r = 2.2 + rng.unit() * 1.4
        for yy in range(int(y - r), int(y + r) + 1):
            for xx in range(int(x - r), int(x + r) + 1):
                if (xx, yy) in mouth and math.hypot(xx - x, yy - y) <= r:
                    lit = (xx - x) + (yy - y) < -1
                    P.px(xx, yy, f["g3"] if lit and i % 3 == 0 else f["coal_hi"] if lit else f["coal"])
    # ---- the tool rack on the right wall
    P.rect(178, 50, 234, 53, f["w1"])
    P.hline(178, 234, 50, f["w3"])
    P.frame(177, 49, 235, 54, f["out"])
    tools = [(186, "tongs"), (200, "hammer"), (214, "file"), (226, "hammer2")]
    for (tx, kind) in tools:
        P.rect(tx, 54, tx, 56, f["i3"])       # hook
        if kind == "tongs":
            for y in range(56, 92):
                off = 0 if y < 80 else (y - 80) // 3
                P.px(tx - 2 - off, y, f["i2"])
                P.px(tx + 2 + off, y, f["i3"])
            P.rect(tx - 2, 56, tx + 2, 58, f["i2"])
        elif kind in ("hammer", "hammer2"):
            ln = 28 if kind == "hammer" else 22
            P.rect(tx - 1, 58, tx + 1, 58 + ln, f["w2"])
            P.vline(tx + 1, 58, 58 + ln, f["w1"])
            P.rect(tx - 5, 56, tx + 5, 62, f["i3"])
            P.hline(tx - 5, tx + 5, 56, f["i4"])
            P.frame(tx - 6, 55, tx + 6, 63, f["out"])
        else:
            P.rect(tx - 1, 58, tx + 1, 88, f["i2"])
            for y in range(60, 88, 2):
                P.px(tx, y, f["i4"])
            P.rect(tx - 2, 86, tx + 2, 96, f["w2"])
    # ---- floor: packed earth and flagstones
    for y in range(112, SH):
        for x in range(SW):
            c = f["fl1"]
            n = (x * 13 + y * 7) % 23
            if n == 0:
                c = f["fl0"]
            elif n == 5 and y % 3 == 0:
                c = f["fl2"]
            P.px(x, y, c)
    P.hline(0, SW - 1, 112, f["out"])
    P.hline(0, SW - 1, 113, f["fl0"])
    # glow pool on the floor in front of the forge
    for y in range(114, 132):
        for x in range(0, 90):
            d = math.hypot((x - 40) / 50.0, (y - 114) / 16.0)
            if d < 1.0 and (x + y) % 2 == 0:
                P.px(x, y, f["warm1"])
    # ---- quench barrel (right)
    bx0, bx1, by0, by1 = 188, 232, 110, 150
    for y in range(by0, by1 + 1):
        for x in range(bx0, bx1 + 1):
            n = (x - bx0) / float(bx1 - bx0) * 2 - 1
            c = f["w3"] if n < -0.55 else f["w2"] if n < 0.2 else f["w1"] if n < 0.7 else f["w0"]
            if (x - bx0) % 8 == 0:
                c = f["w0"]
            P.px(x, y, c)
    for hy in (by0 + 6, by1 - 7):
        P.rect(bx0, hy, bx1, hy + 2, f["hoop"])
        P.hline(bx0, bx1, hy, f["i4"])
    P.ellipse((bx0 + bx1) / 2.0, by0, (bx1 - bx0) / 2.0 + 0.5, 5,
              lambda nx, ny: f["w1"] if nx * nx + ny * ny > 0.62 else (f["water_hi"] if ny < -0.1 else f["water"]))
    P.outline_mask(set((x, y) for x in range(bx0, bx1 + 1) for y in range(by0, by1 + 1)) |
                   ell_mask((bx0 + bx1) / 2.0, by0, (bx1 - bx0) / 2.0 + 0.5, 5), f["out"])
    # ---- the anvil on its stump (centre)
    acx = 120
    # stump
    for y in range(126, 157):
        for x in range(acx - 20, acx + 21):
            n = (x - acx) / 20.0
            c = f["w3"] if n < -0.55 else f["w2"] if n < 0.15 else f["w1"] if n < 0.7 else f["w0"]
            if (x - acx + 40) % 9 == 0 and y > 130:
                c = f["w0"]
            P.px(x, y, c)
    P.ellipse(acx, 156, 21, 3, lambda nx, ny: f["w0"])
    P.outline_mask(set((x, y) for x in range(acx - 20, acx + 21) for y in range(126, 157)) |
                   ell_mask(acx, 156, 21, 3), f["out"])
    # anvil: feet, waist, body, face and horn
    anvil = set()
    for y in range(104, 132):
        if y < 108:           # face (top plate)
            x0, x1 = acx - 36, acx + 38
        elif y < 116:         # body under the face
            x0, x1 = acx - 26, acx + 36
        elif y < 124:         # waist
            k = (y - 116) / 8.0
            x0, x1 = int(acx - 16 + k * 2), int(acx + 20 - k * 2)
        else:                 # feet
            k = (y - 124) / 8.0
            x0, x1 = int(acx - 24 - k * 4), int(acx + 26 + k * 4)
        for x in range(x0, x1 + 1):
            anvil.add((x, y))
    # the horn: a cone to the left of the face
    for x in range(acx - 62, acx - 35):
        t = (x - (acx - 62)) / 27.0           # 0 at the tip .. 1 at the body
        top = 104 + (1 - t) * 1.5
        bot = 104 + 1.5 + t ** 0.8 * 9.5
        for y in range(int(top), int(bot) + 1):
            anvil.add((x, y))
    for (x, y) in anvil:
        if y < 106:
            c = f["i5"] if (x < acx + 20) else f["i4"]
        elif y < 108:
            c = f["i4"]
        else:
            n = (x - acx) / 36.0
            c = f["i3"] if n < -0.5 else f["i2"] if n < 0.3 else f["i1"]
            if y >= 124:
                c = f["i2"] if n < 0 else f["i1"]
        P.px(x, y, c)
    P.hline(acx - 35, acx + 37, 108, f["i1"])
    P.outline_mask(anvil, f["out"])
    # a hardy hole on the face
    P.rect(acx + 26, 105, acx + 28, 106, f["i1"])
    # glow reflected on the anvil face from the forge
    for x in range(acx - 34, acx - 10, 3):
        P.px(x, 105, f["g3"])
    return P.S


# ==========================================================================
# packing a backdrop into tiles, a map and up to 6 palette banks
# ==========================================================================

MAX_BANKS = 6


def lum(c):
    return c[0] * 3 + c[1] * 6 + c[2]


def pack_backdrop(S, name, max_banks=MAX_BANKS, max_tiles=500):
    sets = {}
    for ty in range(20):
        for tx in range(30):
            px = [S[ty * 8 + r][tx * 8 + c] for r in range(8) for c in range(8)]
            sets[(tx, ty)] = frozenset(px)
            if len(sets[(tx, ty)]) > 15:
                raise SystemExit("%s: tile %d,%d has %d colours" % (name, tx, ty, len(sets[(tx, ty)])))
    uniq = sorted(set(sets.values()), key=lambda st: (-len(st), sorted(st)))
    # grow one bank at a time: seed it with the biggest uncovered colour set,
    # then keep adding the set that needs the fewest new colours
    left = [st for st in uniq if not any(st < o for o in uniq)]
    banks = []
    while left:
        if len(banks) >= max_banks:
            raise SystemExit("%s: needs more than %d palette banks (%d colour sets left)" %
                             (name, max_banks, len(left)))
        b = set(left[0])
        while True:
            best = None
            for st in left:
                if st <= b:
                    continue
                add = len(st - b)
                if len(b) + add > 15:
                    continue
                score = (add, -len(st & b), sorted(st))
                if best is None or score < best[0]:
                    best = (score, st)
            if best is None:
                break
            b |= best[1]
        banks.append(b)
        left = [st for st in left if not st <= b]
    while len(banks) < max_banks:
        banks.append(set())
    bank_of = {}
    for st in uniq:
        for i, b in enumerate(banks):
            if st <= b:
                bank_of[st] = i
                break
        else:
            raise SystemExit("%s: colour set left out" % name)
    order = [sorted(b, key=lum) for b in banks]
    pals = [[(0, 0, 0)] + cols + [(0, 0, 0)] * (15 - len(cols)) for cols in order]
    tiles, lookup = [], {}

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

    mp = [0] * (20 * 32)
    for ty in range(20):
        for tx in range(32):
            if tx >= 30:
                mp[ty * 32 + tx] = mp[ty * 32 + 29]
                continue
            b = bank_of[sets[(tx, ty)]]
            px = [S[ty * 8 + r][tx * 8 + c] for r in range(8) for c in range(8)]
            idx = [order[b].index(c) + 1 for c in px]
            tid, fl = add_tile(idx)
            mp[ty * 32 + tx] = tid | ((fl & 1) << 10) | ((fl >> 1) << 11) | (b << 12)
    if len(tiles) > max_tiles:
        raise SystemExit("%s: %d tiles (max %d)" % (name, len(tiles), max_tiles))
    packed = []
    for t in tiles:
        rows = []
        for r in range(8):
            v = 0
            for c in range(8):
                v |= t[r * 8 + c] << (4 * c)
            rows.append(v)
        packed.append(rows)
    used = sum(1 for b in banks if b)
    return packed, mp, pals, used


def decode_backdrop(tiles, mp, pals):
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
# output
# ==========================================================================

def hexs(v):
    return "0x%X" % v


def c_rows(words, per=8, indent="    "):
    return "\n".join(indent + ",".join(hexs(v) for v in words[i:i + per]) + ","
                     for i in range(0, len(words), per))


BACKDROPS = (("kitchen", paint_kitchen), ("apothecary", paint_apothecary), ("forge", paint_forge))

# Preview tints for the value-ramp sprites.
PREVIEW = {
    "FOOD": ((200, 120, 60), (120, 200, 80)), "CHUNK": ((200, 120, 60), (120, 200, 80)),
    "LIQUID": ((60, 200, 170), (180, 255, 230)), "BUBBLE": ((60, 200, 170), (180, 255, 230)),
    "INGOT": ((255, 150, 40), (255, 240, 180)), "MARK": ((240, 180, 40), (255, 255, 255)),
}


def main():
    preview = None
    if "--preview" in sys.argv:
        preview = sys.argv[sys.argv.index("--preview") + 1]
        os.makedirs(preview, exist_ok=True)
    out = []
    w = out.append
    w("/*")
    w(" * Crafting minigame art. GENERATED by tools/gen_craft_gfx.py -- do not edit.")
    w(" * Backdrops: 240x160 BG0 scenes (tiles, a 32x20 map, 6 palette banks for BG")
    w(" * banks 0-5). Sprites: OBJ tiles in 1D order; 64-wide images are two 32-wide")
    w(" * halves. METAL sprites use cpal_metal; the rest use the bout effects' value")
    w(" * ramp (anim.c build_fx_palette).")
    w(" */")
    w("#ifndef GFX_CRAFT_H")
    w("#define GFX_CRAFT_H")
    w("")
    # ---- sprites
    sprites = build_sprites()
    all_words = []
    table = []
    sheet_imgs = []
    for (name, sw, sh, frames) in sprites:
        first = len(all_words) // 8
        per = (sw // 8) * (sh // 8)
        for cv in frames:
            if cv.w != sw or cv.h != sh:
                raise SystemExit("%s: frame is %dx%d, not %dx%d" % (name, cv.w, cv.h, sw, sh))
            img = to_idx(cv)
            for row in img:
                for v in row:
                    if v > 15:
                        raise SystemExit("%s: index %d" % (name, v))
            for t in obj_tiles(img, sw, sh):
                all_words.extend(t)
            sheet_imgs.append((name, img))
        table.append((name, first, per, len(frames), sw, sh))
    w("/* Sprites: CSP_x = index into craft_sprites[]; tiles per frame, frames. */")
    w("enum { " + ", ".join("CSP_" + t[0] for t in table) + ", CSP_COUNT };")
    w("typedef struct { u16 first, tiles; u8 frames, w, h; } CraftSprite;")
    w("static const CraftSprite craft_sprites[CSP_COUNT] = {")
    for (name, first, per, nf, sw, sh) in table:
        w("    { %d, %d, %d, %d, %d }, /* %s */" % (first, per, nf, sw, sh, name))
    w("};")
    w("#define CRAFT_SPRITE_TILES %d" % (len(all_words) // 8))
    w("static const u32 craft_sprite_gfx[CRAFT_SPRITE_TILES * 8] = {")
    w(c_rows(all_words))
    w("};")
    w("static const u16 cpal_metal[16] = {" + ",".join(hexs(g.rgb15(c)) for c in METAL) + "};")
    w("")
    # ---- backdrops
    scenes = []
    for key, painter in BACKDROPS:
        S = painter()
        tiles, mp, pals, used = pack_backdrop(S, key)
        dec = decode_backdrop(tiles, mp, pals)
        assert dec == S, key
        scenes.append((key, S, tiles, mp, pals))
        K_ = key.upper()
        print("  %s: %d tiles, %d palette banks" % (key, len(tiles), used))
        w("/* %s backdrop: %d tiles, %d banks. */" % (K_, len(tiles), used))
        w("#define CBG_%s_TILES %d" % (K_, len(tiles)))
        w("static const u32 cbg_%s_tiles[CBG_%s_TILES * 8] = {" % (key, K_))
        w(c_rows([v for t in tiles for v in t]))
        w("};")
        w("static const u16 cbg_%s_map[20 * 32] = {" % key)
        w(c_rows(mp, 32))
        w("};")
        w("static const u16 cbg_%s_pal[%d][16] = {" % (key, MAX_BANKS))
        for pal in pals:
            w("    {" + ",".join(hexs(g.rgb15(c)) for c in pal) + "},")
        w("};")
        w("")
    w("typedef struct { const u32 *tiles; int tile_count; const u16 *map; const u16 (*pal)[16]; } CraftBackdrop;")
    w("enum { " + ", ".join("CBG_" + k.upper() for k, _ in BACKDROPS) + ", CBG_COUNT };")
    w("static const CraftBackdrop craft_backdrops[CBG_COUNT] = {")
    for key, _ in BACKDROPS:
        w("    { cbg_%s_tiles, CBG_%s_TILES, cbg_%s_map, cbg_%s_pal }," % (key, key.upper(), key, key))
    w("};")
    w("")
    w("#endif /* GFX_CRAFT_H */")
    with open(OUT_H, "w") as fh:
        fh.write("\n".join(out) + "\n")
    print("wrote", OUT_H)
    if preview:
        write_previews(preview, sprites, scenes)


def write_previews(d, sprites, scenes):
    for key, S, tiles, mp, pals in scenes:
        sh = g.Sheet(SW * 2, SH * 2)
        sh.blit(decode_backdrop(tiles, mp, pals), 0, 0, 2)
        sh.save(os.path.join(d, "cbg_%s.png" % key))
    # sprite sheet at 4x
    sc = 4
    W = 64 * 4 + 5 * 8
    rows = []
    for (name, sw, sh_, frames) in sprites:
        rows.append((name, sw, sh_, frames))
    H = sum((r[2] + 4) for r in rows) * sc + 8
    sheet = g.Sheet(W * sc, H, bg=(96, 104, 120))
    y = 4
    for (name, sw, sh_, frames) in rows:
        pal = METAL if name in ("PAN", "SPOON", "POINTER", "HAMMER") else None
        if pal is None:
            tint = PREVIEW.get(name, ((240, 180, 40), (255, 255, 255)))
            pal = fx_preview(*tint)
        x = 4
        for cv in frames:
            sheet.blit(to_idx(cv), x, y, sc, pal=pal)
            x += (sw + 4) * sc
        y += (sh_ + 4) * sc
    sheet.save(os.path.join(d, "craft_sprites.png"))


if __name__ == "__main__":
    main()
