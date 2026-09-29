"""Native desert/jungle terrain art. Names are palette keys, never RGB approximations."""
import math
from pixelart import Img, hash2

COLORS = {
    'bio_desert_hi': (255, 237, 173), 'bio_desert_lt': (246, 210, 133),
    'bio_desert_mid': (222, 169, 93), 'bio_desert_dk': (177, 117, 70),
    'bio_desert_out': (101, 72, 58), 'bio_desert_rust': (199, 106, 68),
    'bio_jungle_hi': (105, 190, 114), 'bio_jungle_lt': (67, 153, 96),
    'bio_jungle_mid': (41, 118, 83), 'bio_jungle_dk': (27, 83, 70),
    'bio_jungle_out': (23, 57, 63), 'bio_jungle_moss': (170, 199, 105),
    'bio_jungle_bark': (121, 91, 64), 'bio_jungle_bark_dk': (75, 65, 58),
    'bio_jungle_bloom': (247, 178, 112), 'bio_jungle_pink': (235, 117, 126),
    'bio_jungle_water': (42, 150, 150), 'bio_jungle_water_dk': (29, 106, 127),
    'bio_desert_water': (48, 168, 174), 'bio_desert_water_dk': (31, 118, 147),
    'bio_desert_foam': (191, 239, 218), 'bio_jungle_foam': (179, 240, 220),
    'bio_desert_adobe': (236, 183, 116), 'bio_desert_adobe_lt': (254, 211, 149),
    'bio_desert_adobe_dk': (157, 95, 65), 'bio_desert_roof': (195, 109, 72),
    'bio_jungle_roof': (193, 155, 83), 'bio_jungle_roof_lt': (233, 202, 126),
    'bio_jungle_thatch_lt': (246, 221, 151), 'bio_jungle_wicker': (163, 124, 77),
}


def ground(base, light, shade, seed=0, mode='sand'):
    im = Img(16, 16, base)
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, seed)
            if mode == 'sand':
                # Broken wind combs sweep diagonally, never rectangular paving.
                wave = math.sin((x + y * .46 + seed * 3) * .65)
                if wave > .72 and h % 5 < 3:
                    im.set(x, y, light)
                elif h % 19 == 0:
                    im.set(x, y, shade)
            else:
                # Dense leaf litter, exposed black loam and irregular roots.
                if h % 9 == 0:
                    im.set(x, y, light)
                elif h % 11 == 0 or (y % 7 == 4 and h % 4 == 0):
                    im.set(x, y, shade)
    return im


def dune(base, crest, shadow, seed=0):
    im = ground(base, crest, shadow, seed)
    for x in range(16):
        y = round(5 + 2.2 * math.sin(x * .28 + seed))
        im.set(x, y, crest)
        if x % 3:
            im.set(x, y + 1, shadow)
        if x % 5 == 0:
            im.set(x, y - 1, crest)
    return im


def rock(bg, rim, face, deep, seed=0, foliage=None):
    im = Img(16, 16, bg)
    for y in range(16):
        for x in range(16):
            edge = (abs(x - 7.5) / 7.5) ** 2 + (abs(y - 7.5) / 8.5) ** 2
            wob = (hash2(x // 3, y // 3, seed) % 5 - 2) * .045
            if edge < .98 + wob:
                im.set(x, y, rim if y < 4 or (x + y) % 9 == 0 else
                       deep if y > 12 or (x > 11 and y > 7) else face)
            if foliage and edge < .78 and hash2(x, y, seed) % 17 == 0:
                im.set(x, y, foliage)
    return im


def brush(bg, shade, blade, glint, seed=0):
    im = ground(bg, glint, shade, seed, 'leaf' if bg.startswith('bio_jungle_') else 'sand')
    for x0, h in ((2, 6), (6, 8), (10, 5), (14, 7)):
        for y in range(15, 15 - h, -1):
            x = x0 + (15 - y) // 4 * (-1 if x0 % 3 else 1)
            im.set(x, y, blade)
            if y < 15 - h + 2:
                im.set(x, y, glint)
        im.set(x0 - 1, 15, shade)
    return im


def path_quads(base, gravel, highlight, surrounding):
    """Five mirrored-quadrant path masks matching the field autotile tables."""
    result = []
    for c in range(4):
        row = []
        for v in range(5):
            im = Img(8, 8)
            for y in range(8):
                for x in range(8):
                    xx = x if c % 2 == 0 else 7 - x
                    yy = y if c < 2 else 7 - y
                    inside = (v == 0 or
                              v == 1 and (xx < 5 or yy < 5) or
                              v == 2 and xx >= 3 or
                              v == 3 and yy >= 3 or
                              v == 4 and xx >= 3 and yy >= 3)
                    h = hash2(xx, yy, 8)
                    im.set(x, y, (gravel if h % 9 == 0 else highlight if h % 13 == 0 else base)
                           if inside else surrounding)
            row.append(im)
        result.append(row)
    return result


def water_quads(foam, bright, water, deep, frame):
    result = []
    for c in range(4):
        row = []
        for v in range(5):
            im = Img(8, 8)
            for y in range(8):
                for x in range(8):
                    xx = x if c % 2 == 0 else 7 - x
                    yy = y if c < 2 else 7 - y
                    edge = v == 1 and xx + yy < 5 or v == 2 and xx < 3 or v == 3 and yy < 3 or v == 4 and (xx < 3 or yy < 3)
                    h = hash2(x + frame * 3, y - frame * 2, c)
                    im.set(x, y, foam if edge and h % 3 else bright if (x + y * 2 + frame * 3) % 11 < 2
                           else deep if h % 7 == 0 else water)
            row.append(im)
        result.append(row)
    return result


def waterfall(foam, bright, water, deep, frame=0):
    im = Img(16, 16, water)
    for y in range(16):
        for x in range(16):
            h = hash2(x, y, 9)
            if (x + (y + frame * 4) // 3) % 6 == 0:
                im.set(x, y, bright)
            elif h % 13 == 0:
                im.set(x, y, deep)
            if y >= 12 and (x + frame * 2) % 5 < 3:
                im.set(x, y, foam)
    return im


def door(floor, border, leaf, glint):
    im = Img(16, 16, floor)
    im.rect(3, 4, 12, 14, border)
    im.rect(4, 5, 11, 13, leaf)
    im.rect(10, 9, 10, 10, glint)
    im.rect(3, 15, 12, 15, glint)
    return im


def animated_water(gf, ts, out, colors):
    bank = 1
    quads = [water_quads(*colors, frame=f) for f in range(3)]
    first = len(ts.tiles)
    seen = {}
    anim = [[], [], []]
    table = [[0] * 5 for _ in range(4)]
    for c in range(4):
        for v in range(5):
            frames = tuple(ts.indices(gf.img_pix(quads[f][c][v]), bank) for f in range(3))
            if frames not in seen:
                seen[frames] = ts.add_raw(frames[0])
                for f in range(3):
                    anim[f].append(frames[f])
            table[c][v] = seen[frames] | bank << 12
    out.update(water_q=table, water_first=first, water_anim=anim)


def add_path(gf, ts, out, colors):
    quads = path_quads(*colors)
    out['path_q'] = [[ts.add(gf.img_pix(quads[c][v]), (0,), 'path[%d][%d]' % (c, v))
                      for v in range(5)] for c in range(4)]
