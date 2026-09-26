#!/usr/bin/env python3
"""Crafting station decor (owner: CRAFT, docs/EXPANSION.md 7.3 and 10.1).

Three interior kinds; craft.c (station_of_decor) turns them into stations:

    COOKTOP   2x2 kitchen island: two burners (one lit) and a stock pot on
              top, cupboard doors below.                -> the KITCHEN
    CAULDRON  2x2 iron cauldron of bubbling green brew over a stone fire
              ring (animated).                          -> the CAULDRON
    ANVIL     2x2 anvil on a tree-stump block, a glowing bar on its face
              (animated glow).                          -> the FORGE

Palette plan (interior banks, gen_field_gfx.INTERIOR_BANKS): every 8x8
quadrant must fit one bank, so
    COOKTOP  everything in bank 5 (fire, brick & stone: ck_* steel-greys,
             bb_* wood, if_org / rd_base / gd_hi flame)
    CAULDRON top half (y < 16) in bank 4 (mt_* iron, sc_* green brew,
             white froth); bottom half in bank 5 (ck_* for the lower iron,
             br_* ring stones, flame)
    ANVIL    everything in bank 4 (mt_* steel, bb_* stump, rd_hi glow)

Place them with DP(COOKTOP, x, y) / DP(CAULDRON, x, y) / DP(ANVIL, x, y)
in an interior map's decor list, with a free cell below (the player faces
them from the front). They're solid 2x2 blocks.
"""

import math
from pixelart import Decor, Img
from decor_outdoor import in_ell, outline

I = ['interior']
OUT = 'i_out'


def _sh(x, w, cols):
    """Pick a shade from left (lit) to right (shadow) across a width."""
    t = x / max(1, w - 1)
    return cols[0] if t < 0.3 else cols[1] if t < 0.72 else cols[2]


# ------------------------------------------------------------------ cooktop

def cooktop_frames():
    frames = []
    for f in range(4):
        img = Img(32, 32)
        # counter top (y 3..13) with a lip
        for y in range(3, 14):
            for x in range(1, 31):
                img.set(x, y, 'ck_hi' if y < 5 else 'ck_base' if y < 12 else 'ck_line')
        # two burner rings on the left
        for (cx, cy) in ((8.5, 8.0), (18.5, 8.0)):
            for y in range(3, 14):
                for x in range(1, 31):
                    d = math.hypot((x + 0.5 - cx) / 1.25, y + 0.5 - cy)
                    if 2.2 <= d <= 3.4:
                        img.set(x, y, 'ck_dk')
                    elif d < 1.2:
                        img.set(x, y, OUT)
        # the lit burner: little blue-less flame tongues (fire colours)
        lit = [(6, 9), (8, 10), (10, 9), (7, 8), (9, 8)]
        for i, (x, y) in enumerate(lit):
            c = ('gd_hi', 'if_org', 'rd_base')[(i + f) % 3]
            img.set(x, y, c)
            if (i + f) % 2 == 0:
                img.set(x, y - 1, 'if_org')
        # stock pot on the right burner... no: on a trivet at the right end
        for y in range(1, 11):
            for x in range(22, 30):
                if y == 1:
                    c = 'ck_dk'
                elif y < 3:
                    c = 'ck_line' if x in (22, 29) else 'ck_base'
                else:
                    c = _sh(x - 22, 8, ('ck_hi', 'ck_base', 'ck_line'))
                img.set(x, y, c)
        for x in (21, 30):
            img.set(x, 4, 'ck_dk')
        # steam puffs over the pot (drift with the frame)
        for k in range(2):
            sx, sy = 24 + ((f + k * 2) % 4), -1 + ((f + k) % 2)
            if 0 <= sy:
                img.set(sx, sy, 'ck_hi')
        # front: cupboard doors (y 14..30)
        for y in range(14, 31):
            for x in range(1, 31):
                if y == 14:
                    c = 'ck_dk'
                elif x in (1, 30) or y == 30:
                    c = 'bb_dk'
                elif x == 15 or x == 16:
                    c = 'bb_dk'
                elif y in (16, 28):
                    c = 'bb_dk'
                else:
                    c = 'bb_base'
                img.set(x, y, c)
        # knobs and handles
        for x in (5, 10, 21, 26):
            img.set(x, 15, 'gd_hi')
        for x in (13, 18):
            for y in (21, 22):
                img.set(x, y, 'gd_hi')
        img = outline(img, OUT)
        frames.append(img)
    return frames


# ----------------------------------------------------------------- cauldron

def cauldron_frames():
    frames = []
    for f in range(4):
        img = Img(32, 32)
        # the pot: a wide belly from y 7 to 27 under a thick rim
        for y in range(3, 28):
            for x in range(0, 32):
                if y < 9:
                    if abs(x + 0.5 - 16) <= 14.5 and (y <= 3 or y >= 7):
                        img.set(x, y, 'mt_hi' if y == 3 else 'mt_base' if y in (7,) else 'mt_dk')
                    elif abs(x + 0.5 - 16) <= 14.5 and x in (1, 2, 29, 30):
                        img.set(x, y, 'mt_base' if x < 16 else 'mt_dk')
                    continue
                if in_ell(x, y, 16, 14, 14.2, 13.0):
                    t = x / 31.0 + (y - 14) * 0.012
                    k = 0 if t < 0.34 else 1 if t < 0.8 else 2
                    if y < 16:
                        img.set(x, y, ('mt_base', 'mt_dk', OUT)[k])
                    else:
                        img.set(x, y, ('ck_line', 'ck_dk', OUT)[k])
        # the brew filling the mouth (y 4..6), with bubbles
        for x in range(3, 29):
            for y in (4, 5, 6):
                img.set(x, y, 'sc_hi' if y == 4 else 'sc_base' if y == 5 else 'sc_dk')
        bubbles = [(6, 4), (12, 5), (19, 4), (24, 5), (9, 5), (16, 4)]
        for i, (x, y) in enumerate(bubbles):
            if (i + f) % 3 == 0:
                img.set(x, y - 1, 'white')
                img.set(x, y, 'white')
                img.set(x + 1, y, 'sc_hi')
            elif (i + f) % 3 == 1:
                img.set(x, y, 'white')
        # a drip of brew down the side
        for y in range(8, 11 + (f & 1)):
            img.set(6, y, 'sc_base')
        # glint on the belly
        for y in range(10, 15):
            img.set(5, y, 'mt_hi')
        # stone fire ring and fire under the belly (y 26..31)
        for x in range(2, 30):
            for y in range(27, 32):
                if y >= 29 or x < 5 or x > 26:
                    k = (x // 4 + y) % 3
                    img.set(x, y, ('br_hi', 'br_base', 'br_dk')[k])
        for i, x in enumerate(range(8, 25, 2)):
            h = 1 + ((i + f) % 3)
            for y in range(29 - h, 29):
                c = 'gd_hi' if y == 28 else 'if_org' if (x + y + f) % 2 else 'rd_base'
                if img.get(x, y) is None or img.get(x, y).startswith('ck'):
                    img.set(x, y, c)
        img = outline(img, OUT)
        frames.append(img)
    return frames


# -------------------------------------------------------------------- anvil

def anvil_frames():
    frames = []
    glow = ['rd_hi', 'white', 'rd_hi', 'mt_hi']
    for f in range(4):
        img = Img(32, 32)
        # face and horn (y 8..13): horn tapers to the left
        for y in range(8, 14):
            for x in range(1, 31):
                if x < 9:
                    # the horn: a cone from x 1 to 9
                    half = (x - 1) / 8.0 * 3.0
                    if abs(y + 0.5 - 10.5) > half:
                        continue
                if y == 8:
                    c = 'mt_hi'
                elif y < 11:
                    c = 'mt_base'
                else:
                    c = 'mt_dk'
                img.set(x, y, c)
        # heel on the right: a square step
        for y in range(8, 16):
            for x in range(26, 31):
                img.set(x, y, 'mt_dk' if y > 11 else 'mt_base')
        # waist (y 14..18) and feet (y 18..21)
        for y in range(14, 22):
            hw = 4 if y < 18 else 4 + (y - 17) * 2
            for x in range(16 - hw, 16 + hw):
                img.set(x, y, 'mt_base' if x < 16 - hw + 2 else 'mt_dk')
        # the glowing bar lying on the face
        for x in range(11, 22):
            img.set(x, 7, glow[(x + f) % 4] if x % 3 else 'rd_hi')
        # tree-stump block (y 21..31)
        for y in range(21, 32):
            for x in range(6, 26):
                if y < 23:
                    c = 'bb_lt' if (x + y) % 5 else 'bb_base'
                else:
                    c = _sh(x - 6, 20, ('bb_lt', 'bb_base', 'bb_dk'))
                    if x in (11, 18) and y > 24:
                        c = 'bb_dk'
                img.set(x, y, c)
        # a spark leaping off the bar
        sx, sy = 20 + f * 2, 5 - (f % 2) * 2
        img.set(sx, sy, 'white' if f % 2 else 'rd_hi')
        img = outline(img, OUT)
        frames.append(img)
    return frames


CRAFT_DECOR = [
    Decor('COOKTOP', I, frames=cooktop_frames(), period=10,
          doc='kitchen island: two burners and a stock pot on top, cupboards below (a KITCHEN station)',
          examine=''),
    Decor('CAULDRON', I, frames=cauldron_frames(), period=12,
          doc='iron cauldron of bubbling green brew over a fire ring (a CAULDRON station)',
          examine=''),
    Decor('ANVIL', I, frames=anvil_frames(), period=14,
          doc='anvil on a stump block, a glowing bar on its face (a FORGE station)',
          examine=''),
]
