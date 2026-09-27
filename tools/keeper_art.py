#!/usr/bin/env python3
"""Bout portraits: chibi keepers (wardens, Hall Masters) and the player.

Every portrait is a 64x64 OBJ painted from shapes on one shared chibi body
(big head, short body, feet on the bout pad), in palette SLOTS rather than
colours. A portrait's 15 colours come in ramps -- skin, hair, main cloth,
second cloth, accent -- so a variation (skin tone, hair colour, outfit
colours) is only a different palette over the same tiles:

    slot 1 outline      2 white / shine    3 eyes
         4 skin         5 skin shade       6 blush + mouth
         7 hair         8 hair shade       9 hair shine
        10 cloth A     11 cloth A shade   12 cloth B    13 cloth B shade
        14 accent      15 accent shade

A pose is a handful of numbers (arm angles, a hop, a breath, the face), so
each keeper gets the same five frames:

    0 IDLE    1 BREATH (blink, 1px squash)    2 FLAIR (its signature move)
    3 THROW   (lantern held high)             4 LOSE  (sheepish, sweat drop)

and the player gets a front set (idle, breath, wave, cheer) and a back set
(idle, breath, wind-up, throw).

Standard library only; gen_keeper_gfx.py packs the result into
src/gfx_keepers.h and writes preview sheets.
"""

import math

W = H = 64

# palette slots
T, OUT, WHITE, EYE, SKIN, SKIN_S, BLUSH, HAIR, HAIR_S, HAIR_L, CA, CA_S, CB, CB_S, AC, AC_S = range(16)
SHADE = {SKIN: SKIN_S, HAIR: HAIR_S, HAIR_L: HAIR, CA: CA_S, CB: CB_S, AC: AC_S, WHITE: None}

# ---------------------------------------------------------------- ramps

SKINS = [  # (skin, shade, blush)
    ('pale',   (252, 230, 214), (232, 186, 170), (246, 150, 162)),
    ('light',  (250, 214, 176), (220, 162, 124), (242, 138, 128)),
    ('golden', (242, 206, 146), (208, 158, 100), (236, 130, 104)),
    ('tan',    (216, 160, 112), (172, 116, 80),  (214, 104, 92)),
    ('brown',  (168, 112, 76),  (124, 78, 54),   (196, 90, 80)),
    ('deep',   (118, 74, 54),   (86, 52, 42),    (166, 72, 68)),
]

HAIRS = [  # (hair, shade, shine)
    ('ink',      (58, 54, 78),    (36, 32, 50),    (110, 112, 150)),
    ('cocoa',    (96, 62, 46),    (62, 40, 34),    (146, 100, 72)),
    ('chestnut', (156, 88, 50),   (108, 58, 38),   (208, 136, 86)),
    ('ginger',   (224, 112, 54),  (164, 70, 38),   (250, 170, 100)),
    ('honey',    (242, 200, 100), (200, 146, 62),  (252, 236, 170)),
    ('silver',   (206, 206, 220), (146, 146, 168), (248, 248, 252)),
    ('rose',     (242, 142, 176), (198, 92, 134),  (252, 200, 216)),
    ('teal',     (74, 170, 166),  (40, 112, 122),  (146, 218, 206)),
    ('lilac',    (168, 136, 216), (114, 90, 170),  (216, 200, 246)),
    ('moss',     (120, 170, 84),  (74, 118, 58),   (178, 214, 128)),
]

CLOTHS = [  # (cloth, shade)
    ('red',    (226, 78, 74),   (160, 44, 56)),
    ('orange', (240, 138, 60),  (184, 88, 40)),
    ('sun',    (248, 206, 80),  (204, 150, 48)),
    ('leaf',   (110, 184, 92),  (62, 128, 70)),
    ('pine',   (60, 128, 96),   (36, 84, 70)),
    ('sky',    (108, 172, 232), (66, 116, 184)),
    ('navy',   (70, 86, 150),   (44, 52, 100)),
    ('plum',   (150, 90, 170),  (100, 56, 124)),
    ('pink',   (244, 150, 184), (206, 98, 140)),
    ('brown',  (150, 100, 66),  (104, 66, 46)),
    ('stone',  (156, 160, 172), (108, 110, 128)),
    ('cream',  (246, 236, 206), (206, 188, 150)),
    ('coal',   (70, 66, 80),    (44, 40, 54)),
    ('mint',   (150, 226, 196), (92, 176, 150)),
]

ACCENTS = {  # (accent, shade)
    'gold':   ((250, 206, 76),  (200, 138, 48)),
    'steel':  ((188, 198, 214), (122, 132, 156)),
    'wood':   ((178, 124, 76),  (122, 80, 52)),
    'straw':  ((244, 214, 128), (200, 158, 80)),
    'leather': ((148, 96, 60),  (100, 62, 42)),
    'glass':  ((170, 226, 244), (100, 164, 204)),
    'ember':  ((252, 150, 60),  (212, 80, 40)),
    'white':  ((248, 248, 244), (200, 204, 216)),
    'green':  ((120, 196, 96),  (70, 140, 70)),
    'violet': ((196, 150, 240), (132, 94, 190)),
    'rose':   ((248, 142, 170), (204, 90, 130)),
}

OUTLINE = (44, 34, 52)
WHITE_C = (252, 252, 248)
EYE_C = (46, 38, 64)


def ramp_index(table, name):
    for i, r in enumerate(table):
        if r[0] == name:
            return i
    raise KeyError(name)


def palette(look):
    """16 RGB tuples for a look dict {skin, hair, a, b, acc} (names)."""
    s = SKINS[ramp_index(SKINS, look['skin'])]
    h = HAIRS[ramp_index(HAIRS, look['hair'])]
    a = CLOTHS[ramp_index(CLOTHS, look['a'])]
    b = CLOTHS[ramp_index(CLOTHS, look['b'])]
    acc = ACCENTS[look['acc']]
    return [(0, 0, 0), OUTLINE, WHITE_C, EYE_C, s[1], s[2], s[3], h[1], h[2], h[3],
            a[1], a[2], b[1], b[2], acc[0], acc[1]]


# ---------------------------------------------------------------- shapes
# A shape is a predicate on pixel centres (x + .5, y + .5).

def ell(cx, cy, rx, ry):
    return lambda x, y: ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0


def rect(x0, y0, x1, y1):
    """inclusive pixel rectangle"""
    return lambda x, y: x0 <= x - .5 <= x1 and y0 <= y - .5 <= y1


def poly(pts):
    def f(x, y):
        inside = False
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                    inside = not inside
        return inside
    return f


def cap(x0, y0, x1, y1, r):
    """capsule: every point within r of the segment"""
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy or 1e-9

    def f(x, y):
        t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / L2))
        px, py = x0 + t * dx - x, y0 + t * dy - y
        return px * px + py * py <= r * r
    return f


def union(*fs):
    return lambda x, y: any(f(x, y) for f in fs)


def minus(a, b):
    return lambda x, y: a(x, y) and not b(x, y)


def inter(a, b):
    return lambda x, y: a(x, y) and b(x, y)


def half(f, side, at):
    """keep the part of f left/right/above/below the line `at`"""
    tests = {'l': lambda x, y: x < at, 'r': lambda x, y: x >= at,
             'u': lambda x, y: y < at, 'd': lambda x, y: y >= at}
    t = tests[side]
    return lambda x, y: f(x, y) and t(x, y)


# ---------------------------------------------------------------- painter

class Painter:
    """Pixels hold (slot, group). Groups are paint layers: the order a
    group is first painted is its depth, and edges against a group behind
    get an outline (line='out'), the group's own shade (line='shade') or
    nothing (line=None)."""

    def __init__(self, w=W, h=H, small=False):
        self.w, self.h, self.small = w, h, small
        self.slot = [[T] * w for _ in range(h)]
        self.grp = [[None] * w for _ in range(h)]
        self.flat = [[False] * w for _ in range(h)]
        self.z = {}
        self.line = {}

    def group(self, name, line='out'):
        if name not in self.z:
            self.z[name] = len(self.z)
        self.line[name] = line

    def fill(self, f, slot, group, clip=None, flat=False, only=None):
        """paint slot over f. clip: extra predicate; only: groups (tuple)
        the paint may land on (e.g. a stripe that stays on the shirt)."""
        if group not in self.z:
            self.group(group)
        x0, y0, x1, y1 = 0, 0, self.w, self.h
        for y in range(y0, y1):
            for x in range(x0, x1):
                cx, cy = x + .5, y + .5
                if not f(cx, cy):
                    continue
                if clip and not clip(cx, cy):
                    continue
                if only is not None and self.grp[y][x] not in only:
                    continue
                self.slot[y][x] = slot
                self.grp[y][x] = group
                self.flat[y][x] = flat

    def detail(self, pts, slot, group=None, flat=True):
        """single pixels (keeps the pixel's group unless one is given)"""
        for (x, y) in pts:
            x, y = int(x), int(y)
            if 0 <= x < self.w and 0 <= y < self.h:
                self.slot[y][x] = slot
                if group:
                    if group not in self.z:
                        self.group(group, None)
                    self.grp[y][x] = group
                self.flat[y][x] = flat

    def erase(self, f):
        for y in range(self.h):
            for x in range(self.w):
                if f(x + .5, y + .5):
                    self.slot[y][x] = T
                    self.grp[y][x] = None

    def g(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.grp[y][x]
        return None

    def finish(self):
        """shading, inner lines and the outer outline -> 64x64 slot rows"""
        out = [row[:] for row in self.slot]
        # 1. form shading: light from the upper left; a pixel is in shade
        #    when its group ends 1-2px to the right or below.
        for y in range(self.h):
            for x in range(self.w):
                s = self.slot[y][x]
                gname = self.grp[y][x]
                if s not in SHADE or SHADE[s] is None or self.flat[y][x]:
                    continue
                if self.small:   # 1px bands on 16px people
                    edge = self.g(x + 1, y) != gname or self.g(x, y + 1) != gname
                else:
                    edge = (self.g(x + 1, y) != gname or self.g(x + 2, y + 1) != gname or
                            self.g(x, y + 2) != gname or self.g(x + 1, y + 1) != gname)
                # cast shadow under anything in front (hair over face, head over body)
                above = self.g(x, y - 1)
                cast = (above is not None and above != gname and
                        self.z.get(above, -1) > self.z.get(gname, -1) and self.line.get(above))
                above2 = self.g(x, y - 2)
                cast2 = (not self.small and s == SKIN and above2 is not None and above2 != gname and
                         self.z.get(above2, -1) > self.z.get(gname, -1) and self.line.get(above2)
                         and above2 != 'face')
                if edge or cast or cast2:
                    out[y][x] = SHADE[s]
        # 2. inner lines: the front group's edge against a group behind it
        final = [row[:] for row in out]
        for y in range(self.h):
            for x in range(self.w):
                gname = self.grp[y][x]
                if gname is None:
                    continue
                mode = self.line.get(gname)
                if not mode:
                    continue
                zg = self.z[gname]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = self.g(x + dx, y + dy)
                    if n is not None and n != gname and self.z.get(n, 99) < zg and self.line.get(n) != 'none-under':
                        if mode == 'out':
                            final[y][x] = OUT
                        else:
                            s = self.slot[y][x]
                            final[y][x] = SHADE.get(s) or s
                        break
        # 3. outer outline (outside the shapes)
        res = [row[:] for row in final]
        for y in range(self.h):
            for x in range(self.w):
                if final[y][x] != T:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < self.w and 0 <= yy < self.h and final[yy][xx] != T:
                        res[y][x] = OUT
                        break
        return res


# ---------------------------------------------------------------- the body

class Body:
    """Anchors of the chibi body. kind: 'kid', 'teen', 'adult', 'big', 'elder'."""

    KINDS = {
        #         head r      torso h  leg h  shoulder half  hip half
        'kid':   ((14.5, 13.0), 10, 7, 8.0, 8.0),
        'teen':  ((14.5, 13.0), 12, 9, 9.0, 8.5),
        'adult': ((14.5, 13.0), 13, 11, 10.0, 9.0),
        'big':   ((15.0, 13.0), 14, 10, 12.5, 11.5),
        'elder': ((14.5, 13.0), 12, 8, 9.5, 10.0),
    }

    def __init__(self, kind='teen', breath=0, hop=0, lean=0, bob=0, side=False):
        (rx, ry), th, lh, sh, hh = self.KINDS[kind]
        self.kind = kind
        self.feet = 61 - hop               # sole line
        self.shoe_h = 3
        self.leg_top = self.feet - self.shoe_h - lh + 1
        self.leg_h = lh
        self.waist = self.leg_top           # where torso meets legs
        self.neck = self.waist - th + breath + bob   # breath squashes the torso; bob lowers it all
        self.side = side
        self.cx = 32 + lean
        self.hrx, self.hry = rx, ry
        self.hcx = self.cx + lean
        self.hcy = self.neck - ry + 3.5     # head overlaps the collar a bit
        self.sh = sh * (.62 if side else 1)   # shoulder half-width
        self.hh = hh * (.62 if side else 1)   # hip half-width
        self.shoulder_y = self.neck + 2.5
        self.eye_y = int(self.hcy + 1)
        self.top = self.hcy - ry            # top of the skull

    def shoulder(self, side):
        return (self.cx + side * (self.sh - 1.5), self.shoulder_y)


def arm_points(b, side, ang, bend=0, length=None):
    """shoulder, elbow, hand. side -1 = screen-left arm, +1 = screen-right.
    ang: degrees from hanging straight down, positive = outward/up."""
    sx, sy = b.shoulder(side)
    L1 = length or (6.5 if b.kind == 'kid' else 7.5)
    L2 = L1 - 0.5
    a1 = math.radians(ang)
    ex = sx + side * math.sin(a1) * L1
    ey = sy + math.cos(a1) * L1
    a2 = math.radians(ang + bend)
    hx = ex + side * math.sin(a2) * L2
    hy = ey + math.cos(a2) * L2
    return (sx, sy), (ex, ey), (hx, hy)


def draw_arm(p, b, side, ang, bend=0, sleeve=CA, sleeve_len='long', hand=SKIN,
             group=None, cuff=None):
    (sx, sy), (ex, ey), (hx, hy) = arm_points(b, side, ang, bend)
    g = group or ('armL' if side < 0 else 'armR')
    p.group(g)
    r = 3.0 if b.kind != 'big' else 3.5
    if sleeve_len == 'none':
        p.fill(union(cap(sx, sy, ex, ey, r), cap(ex, ey, hx, hy, r - .3)), hand, g)
    elif sleeve_len == 'short':
        p.fill(cap(ex, ey, hx, hy, r - .4), hand, g)
        p.fill(cap(sx, sy, (sx + ex) / 2 + (ex - sx) * .3, (sy + ey) / 2 + (ey - sy) * .3, r + .3), sleeve, g)
    else:
        p.fill(union(cap(sx, sy, ex, ey, r), cap(ex, ey, hx, hy, r - .2)), sleeve, g)
        if cuff is not None:
            p.fill(ell(hx - (hx - ex) * .25, hy - (hy - ey) * .25, 2.6, 2.6), cuff, g)
    p.fill(ell(hx, hy, 2.8, 2.8), hand, g)
    return hx, hy


def draw_legs(p, b, pants=CB, shoes=CA, style='pants', sock=None, lift=(0, 0), stride=0):
    """style: pants, shorts, bare, skirt (legs bare under a skirt drawn by
    the outfit), boots. lift: how far each foot is raised (walking, front
    and back views); stride: side view, how far the legs spread."""
    p.group('legs')
    gap = 1.0 if b.kind != 'big' else 1.5
    lw = 3.0 if b.kind != 'big' else 3.8
    if b.side:
        cols = ((b.cx - stride - lw + .5, 0), (b.cx + stride - lw + .5, 1))
    else:
        cols = ((b.cx - (gap + lw) - lw, 0), (b.cx + (gap + lw) - lw, 1))
    for x0, i in cols:
        up = lift[i]
        x1 = x0 + 2 * lw - 1
        top, bot = b.leg_top - 1, b.feet - b.shoe_h - up
        if style == 'pants':
            p.fill(rect(x0, top, x1, bot), pants, 'legs')
        elif style == 'shorts':
            p.fill(rect(x0, top, x1, bot), SKIN, 'legs')
            p.fill(rect(x0 - .5, top, x1 + .5, top + b.leg_h * .45), pants, 'legs')
        else:
            p.fill(rect(x0 + .5, top, x1 - .5, bot), SKIN, 'legs')
        if sock is not None:
            p.fill(rect(x0 + .5, bot - 2, x1 - .5, bot), sock, 'legs')
    p.group('shoes')
    for x0, i in cols:
        up = lift[i]
        fx = x0 + lw + (-.8 if b.side else (-.8 if i == 0 else .8))
        if b.side:
            fx -= 1.5    # toes point the way they walk (left)
        p.fill(ell(fx, b.feet - 1.2 - up, lw + 1.1, 2.3), shoes, 'shoes')
        p.fill(rect(fx - lw - 1, b.feet - 1 - up, fx + lw + 1, b.feet - 1 - up),
               shoes, 'shoes', clip=ell(fx, b.feet - 1.5 - up, lw + 1.1, 2.6))


def torso_shape(b, flare=0.0, extra=0.0):
    top, bot = b.neck, b.waist + 1
    sh, hh = b.sh + extra, b.hh + flare + extra
    return poly([(b.cx - sh + 1, top), (b.cx + sh - 1, top), (b.cx + sh, top + 2),
                 (b.cx + hh, bot), (b.cx - hh, bot), (b.cx - sh, top + 2)])


def draw_torso(p, b, slot=CA, flare=0.0, extra=0.0):
    p.group('torso')
    p.fill(torso_shape(b, flare, extra), slot, 'torso')


def draw_head(p, b, back=False):
    p.group('head')
    p.fill(ell(b.hcx, b.hcy, b.hrx, b.hry), SKIN, 'head')
    # ears
    if not back:
        for side in (-1, 1):
            p.fill(ell(b.hcx + side * (b.hrx - .2), b.hcy + 2.5, 2.0, 2.6), SKIN, 'head')


EYE_SHAPES = {
    # rows of the eye, '#': eye, 'w': shine, '.': nothing (4 wide)
    'round': ['.##.', '#w##', '####', '####', '.##.'],
    'big':   ['.##.', '#ww#', '#w##', '####', '####', '.##.'],
    'sleepy': ['####', '#w##', '.##.'],
    'sharp': ['####', '#w##', '.###', '..#.'],
    'dot':   ['.##.', '#w##', '####', '.##.'],
}


def draw_face(p, b, face='smile', look=0, eyes='round', brows=None):
    """face: smile, open, grin, blink, happy (^ ^), sweat, shout, calm.
    eyes: EYE_SHAPES key."""
    p.group('face', None)
    ey = b.eye_y
    xs = (int(b.hcx) - 7 + look, int(b.hcx) + 4 + look)   # left column of each eye
    shape = EYE_SHAPES.get(eyes, EYE_SHAPES['round'])
    h = len(shape)
    closed = face in ('blink', 'happy', 'calm')
    for i, x in enumerate(xs):
        if face == 'blink':
            p.detail([(x + k, ey + h - 2) for k in range(4)], EYE)
            p.detail([(x - 0 if i == 0 else x + 3, ey + h - 3)], EYE)
        elif face == 'happy':
            p.detail([(x, ey + 3), (x + 1, ey + 2), (x + 2, ey + 2), (x + 3, ey + 3)], EYE)
        elif face == 'calm':
            p.detail([(x, ey + 2), (x + 1, ey + 3), (x + 2, ey + 3), (x + 3, ey + 2)], EYE)
        else:
            rows = shape if i == 0 else [r[::-1] if eyes == 'sharp' else r for r in shape]
            for dy, row in enumerate(rows):
                for dx, c in enumerate(row):
                    if c == '#':
                        p.detail([(x + dx, ey + dy)], EYE)
                    elif c == 'w':
                        p.detail([(x + dx, ey + dy)], WHITE)
    if brows:
        for i, x in enumerate(xs):
            inner = x + 3 if i == 0 else x
            outer = x if i == 0 else x + 3
            if brows == 'fierce':
                p.detail([(outer, ey - 3), (x + 1, ey - 3), (x + 2, ey - 2), (inner, ey - 2)], EYE)
            elif brows == 'worried':
                p.detail([(outer, ey - 2), (x + 1, ey - 2), (x + 2, ey - 3), (inner, ey - 3)], EYE)
            else:
                p.detail([(x + k, ey - 3) for k in range(4)], HAIR_S)
    # blush
    by = ey + h
    for x in (xs[0] - 2, xs[1] + 4):
        p.detail([(x, by), (x + 1, by)], BLUSH)
    # mouth
    mx, my = int(b.hcx) + look, ey + h + 1
    if face in ('smile', 'blink'):
        p.detail([(mx - 2, my), (mx - 1, my + 1), (mx, my + 1), (mx + 1, my)], OUT)
    elif face == 'calm':
        p.detail([(mx - 1, my + 1), (mx, my + 1)], OUT)
    elif face == 'shout':
        p.detail([(mx - 1, my), (mx, my), (mx - 2, my + 1), (mx + 1, my + 1),
                  (mx - 2, my + 2), (mx + 1, my + 2), (mx - 1, my + 3), (mx, my + 3)], OUT)
        p.detail([(mx - 1, my + 1), (mx, my + 1), (mx - 1, my + 2), (mx, my + 2)], BLUSH)
    elif face in ('open', 'grin', 'happy'):
        p.detail([(mx - 2, my), (mx - 1, my), (mx, my), (mx + 1, my),
                  (mx - 2, my + 1), (mx + 1, my + 1), (mx - 1, my + 2), (mx, my + 2)], OUT)
        p.detail([(mx - 1, my + 1), (mx, my + 1)], BLUSH if face != 'grin' else WHITE)
    elif face == 'sweat':
        p.detail([(mx - 2, my + 1), (mx - 1, my), (mx, my + 1), (mx + 1, my)], OUT)
    if face == 'sweat':
        sx, sy = int(b.hcx + b.hrx) - 1, int(b.hcy - 7)
        pts = [(sx, sy), (sx, sy + 1), (sx - 1, sy + 2), (sx, sy + 2), (sx + 1, sy + 2),
               (sx - 1, sy + 3), (sx, sy + 3), (sx + 1, sy + 3), (sx, sy + 4)]
        p.detail(pts, 14, 'sweat')   # glass-blue accent is not guaranteed: see SWEAT below
        p.detail(pts, WHITE, 'sweat')
        p.detail([(sx + 1, sy + 3), (sx, sy + 4)], SKIN_S, 'sweat')
        p.line['sweat'] = 'out'


def lantern(p, x, y, glow=True):
    """the little lantern keepers throw (in the hand at x, y)"""
    p.group('lantern')
    p.fill(rect(x - 1, y - 5, x + 1, y - 4), AC_S, 'lantern')
    p.fill(ell(x + .5, y + .5, 3.2, 3.6), AC, 'lantern')
    p.fill(rect(x - 2, y + 3, x + 2, y + 4), AC_S, 'lantern', flat=True)
    p.fill(ell(x + .5, y + .5, 1.6, 2.0), WHITE, 'lantern', flat=True)
    p.detail([(x - 1, y - 1)], WHITE)
