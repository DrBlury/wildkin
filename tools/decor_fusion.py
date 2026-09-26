#!/usr/bin/env python3
"""Fusion machines decor (owner: FUSION, docs/EXPANSION.md 7.4 and 10.1).

The four machines of the RESONANCE WORKS in Lumen City, for the interior
tileset: EXTRACTOR (glass dome on a bronze base), MIXER (steel cabinet with
the tuning scope), FUSION LOOM (heartglass ring on a gold stand) and ENERGY
TANKS (two glass tubes). fusion.c opens the matching machine screen when one
is examined (fusion_examine); elsewhere they just say their examine line.

Every 8x8 quadrant must fit one interior palette bank. The machines are
drawn with the colours of banks 4 (metal, glass, bronze, screen green) and
6 (gold, heartglass, blue glass); fit_banks() then maps each quadrant onto
the bank most of its pixels already use, so a stray pixel can't break the
build. Everything is drawn on transparency with an i_out outline.
"""

import math

from pixelart import Decor, Img
from decor_indoor import INDOOR_DECOR_BANKS
from decor_outdoor import outline

I = ['interior']

BANK_A = INDOOR_DECOR_BANKS[4]
BANK_B = INDOOR_DECOR_BANKS[6]

# nearest stand-ins when a quadrant has to move to the other bank
TO_B = {'bb_lt': 'gd_base', 'bb_base': 'if_org', 'bb_dk': 'i_out', 'mt_hi': 'white',
        'mt_base': 'bl_hi', 'mt_dk': 'bl_base', 'gl_hi': 'white', 'gl_base': 'bl_hi',
        'gl_dk': 'bl_base', 'sc_hi': 'lf_hi', 'sc_base': 'lf_base', 'sc_dk': 'lf_dk',
        'rd_hi': 'pk_base'}
TO_A = {'gd_hi': 'bb_lt', 'gd_base': 'bb_base', 'if_org': 'bb_lt', 'lf_hi': 'sc_hi',
        'lf_base': 'sc_base', 'lf_dk': 'sc_dk', 'pk_hi': 'rd_hi', 'pk_base': 'rd_hi',
        'hg_hi': 'white', 'hg_base': 'rd_hi', 'hg_dk': 'bb_dk', 'bl_hi': 'gl_base',
        'bl_base': 'gl_dk'}


def fit_banks(img):
    """Map every 8x8 quadrant onto bank 4 or 6 (whichever it mostly uses)."""
    o = img.copy()
    for qy in range(0, img.h, 8):
        for qx in range(0, img.w, 8):
            px = [(x, y) for y in range(qy, qy + 8) for x in range(qx, qx + 8)
                  if img.p[y][x] is not None]
            if not px:
                continue
            na = sum(1 for (x, y) in px if img.p[y][x] in BANK_A)
            nb = sum(1 for (x, y) in px if img.p[y][x] in BANK_B)
            bank, sub = (BANK_A, TO_A) if na >= nb else (BANK_B, TO_B)
            for (x, y) in px:
                c = img.p[y][x]
                if c not in bank:
                    c = sub.get(c, 'i_out')
                o.p[y][x] = c
    return o


def disc(img, cx, cy, r, col):
    for y in range(img.h):
        for x in range(img.w):
            if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r:
                img.set(x, y, col)


def ring(img, cx, cy, r0, r1, col):
    for y in range(img.h):
        for x in range(img.w):
            if r0 <= math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= r1:
                img.set(x, y, col)


def box(img, x0, y0, x1, y1, lit, base, dark):
    """A lit box: light top row and left column, dark right and bottom."""
    img.rect(x0, y0, x1, y1, base)
    img.rect(x0, y0, x1, y0, lit)
    img.rect(x0, y0, x0, y1, lit)
    img.rect(x1, y0 + 1, x1, y1, dark)
    img.rect(x0 + 1, y1, x1, y1, dark)


def rivet(img, x, y, lit, dark):
    img.set(x, y, lit)
    img.set(x + 1, y + 1, dark)


def extractor():
    """Glass dome (with a faint teal kernel glow) on a bronze base."""
    img = Img(32, 32)
    # the bronze base with a gauge and a red lamp
    box(img, 2, 21, 29, 30, 'bb_lt', 'bb_base', 'bb_dk')
    for x in (4, 27):
        rivet(img, x, 23, 'bb_lt', 'bb_dk')
    disc(img, 21.5, 26.5, 3.2, 'mt_base')
    disc(img, 21.5, 26.5, 2.2, 'mt_hi')
    img.set(22, 25, 'i_out')
    img.set(21, 26, 'i_out')
    img.rect(7, 25, 9, 27, 'rd_hi')
    img.set(7, 25, 'white')
    # the dome
    disc(img, 16, 13, 10.5, 'gl_dk')
    disc(img, 16, 13, 9.5, 'gl_base')
    disc(img, 16, 14, 5.5, 'sc_dk')
    disc(img, 16, 14, 3.5, 'sc_base')
    disc(img, 16, 14, 1.6, 'sc_hi')
    for (x, y) in ((11, 7), (12, 6), (10, 8), (10, 9), (13, 6)):
        img.set(x, y, 'gl_hi')
    img.set(12, 8, 'white')
    # the collar and the cap
    img.rect(6, 19, 25, 20, 'bb_base')
    img.rect(6, 19, 25, 19, 'bb_lt')
    img.rect(12, 2, 19, 3, 'bb_base')
    img.rect(12, 2, 19, 2, 'bb_lt')
    img.rect(15, 0, 16, 1, 'mt_base')
    return fit_banks(outline(img, 'i_out'))


def mixer():
    """Steel cabinet: a green scope with two waves, two bronze knobs."""
    img = Img(32, 32)
    box(img, 2, 2, 29, 30, 'mt_hi', 'mt_base', 'mt_dk')
    img.rect(4, 4, 27, 16, 'mt_dk')
    img.rect(5, 5, 26, 15, 'sc_dk')
    for x in range(5, 27):
        yt = 10 - round(3.5 * math.sin((x - 5) * 2 * math.pi / 11))
        yp = 10 - round(3.5 * math.sin((x - 5) * 2 * math.pi / 11 + 0.9))
        img.set(x, yp, 'sc_base')
        img.set(x, yt, 'sc_hi')
    for x in (10, 16, 22):
        for y in range(5, 16, 2):
            if img.get(x, y) == 'sc_dk':
                img.set(x, y, 'sc_base')
    for cx in (10.5, 21.5):
        disc(img, cx, 23.5, 3.6, 'bb_dk')
        disc(img, cx, 23.2, 2.8, 'bb_base')
        disc(img, cx - 0.6, 22.6, 1.3, 'bb_lt')
    img.rect(14, 27, 17, 28, 'rd_hi')
    for (x, y) in ((4, 28), (27, 28)):
        rivet(img, x, y, 'mt_hi', 'mt_dk')
    return fit_banks(outline(img, 'i_out'))


def loom():
    """The FUSION LOOM: a gold ring of heartglass with three sockets."""
    img = Img(48, 48)
    cx, cy = 24, 18.5
    # stand: two legs and a gold plinth with pink lamps
    for x0 in (12, 33):
        img.rect(x0, 28, x0 + 2, 36, 'gd_base')
        img.rect(x0, 28, x0, 36, 'gd_hi')
        img.rect(x0 + 2, 28, x0 + 2, 36, 'if_org')
    box(img, 5, 36, 42, 46, 'gd_hi', 'gd_base', 'if_org')
    for i, x in enumerate(range(10, 40, 7)):
        img.rect(x, 40, x + 2, 42, 'pk_base' if i % 2 else 'hg_base')
        img.set(x, 40, 'pk_hi')
    # the ring
    ring(img, cx, cy, 13.0, 16.5, 'gd_base')
    ring(img, cx, cy, 15.5, 16.5, 'if_org')
    for y in range(img.h):
        for x in range(img.w):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            a = math.atan2(y + 0.5 - cy, x + 0.5 - cx)
            if 13.0 <= d <= 14.5 and -2.6 < a < -0.6:
                img.set(x, y, 'gd_hi')
    disc(img, cx, cy, 12.5, 'hg_dk')
    disc(img, cx, cy, 10.0, 'hg_base')
    disc(img, cx + 1, cy + 1, 6.0, 'pk_base')
    disc(img, cx + 1, cy + 1, 3.0, 'hg_hi')
    for (x, y) in ((18, 11), (19, 10), (17, 12), (20, 10)):
        img.set(x, y, 'white')
    # sockets at the top and the lower sides
    for ang in (-90, 150, 30):
        sx = cx + 15.0 * math.cos(math.radians(ang))
        sy = cy + 15.0 * math.sin(math.radians(ang))
        disc(img, sx, sy, 3.2, 'gd_hi')
        disc(img, sx, sy, 2.0, 'bl_base')
        img.set(int(sx) - 1, int(sy) - 1, 'bl_hi')
    return fit_banks(outline(img, 'i_out'))


def tanks():
    """Two glass tubes: teal energy (bank 4) and heartglass pink (bank 6)."""
    img = Img(32, 32)
    # left tube: grey-blue glass, teal liquid
    img.rect(3, 3, 12, 23, 'gl_dk')
    img.rect(4, 3, 11, 23, 'gl_base')
    img.rect(5, 10, 10, 23, 'sc_base')
    img.rect(5, 10, 10, 10, 'sc_hi')
    img.rect(10, 11, 10, 23, 'sc_dk')
    img.rect(5, 4, 5, 20, 'gl_hi')
    # right tube: blue glass, pink liquid
    img.rect(19, 3, 28, 23, 'bl_base')
    img.rect(20, 3, 27, 23, 'bl_hi')
    img.rect(21, 14, 26, 23, 'hg_base')
    img.rect(21, 14, 26, 14, 'hg_hi')
    img.rect(26, 15, 26, 23, 'hg_dk')
    img.rect(21, 4, 21, 12, 'white')
    # caps
    for x0 in (2, 18):
        box(img, x0, 0, x0 + 11, 2, 'bb_lt', 'bb_base', 'bb_dk')
    # bronze base with a dial
    box(img, 1, 24, 30, 31, 'bb_lt', 'bb_base', 'bb_dk')
    img.rect(14, 26, 17, 29, 'mt_dk')
    img.rect(15, 27, 16, 28, 'sc_hi')
    return fit_banks(outline(img, 'i_out'))


FUSION_DECOR = [
    Decor('FZ_EXTRACTOR', I, extractor(), top='XX/..',
          doc='RESONANCE WORKS extractor: glass dome on a bronze base (2x2; dome over people)',
          examine='The EXTRACTOR. Its glass dome hums softly.'),
    Decor('FZ_MIXER', I, mixer(), top='XX/..',
          doc='RESONANCE WORKS mixer: steel cabinet with the tuning scope (2x2)',
          examine='The MIXER. Two waves wobble on its little green screen.'),
    Decor('FZ_LOOM', I, loom(), top='XXX/.../...',
          doc='RESONANCE WORKS fusion loom: heartglass ring on a gold stand (3x3; ring over people)',
          examine='The FUSION LOOM. Motes drift around its heartglass ring.'),
    Decor('FZ_TANKS', I, tanks(), top='XX/..',
          doc='RESONANCE WORKS energy tanks: two glass tubes of typed energy (2x2)',
          examine='The ENERGY TANKS. One glows teal, the other pink.'),
]


if __name__ == '__main__':
    for d in FUSION_DECOR:
        print(d.name, d.w, d.h)
