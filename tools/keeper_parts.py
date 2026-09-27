"""Hair, hats, outfits and props for the bout portraits (keeper_art.py).

VIEW is the direction being painted: 'down' (facing you: the portraits and
the overworld's front frames), 'up' (from behind) or 'left' (side view,
facing left; the overworld's right frames are this mirrored). Parts adapt:
front-only pieces (aprons, collars, beards...) vanish from behind, brims and
lamps turn to the left in side view, and so on.
"""

VIEW = 'down'


def front_only(fn):
    """a piece you only see from the front"""
    def wrap(p, b, *a, **k):
        if VIEW == 'down':
            return fn(p, b, *a, **k)
    wrap.__name__ = fn.__name__
    return wrap


from keeper_art import (T, OUT, WHITE, EYE, SKIN, SKIN_S, BLUSH, HAIR, HAIR_S, HAIR_L,
                        CA, CA_S, CB, CB_S, AC, AC_S,
                        ell, rect, poly, cap, union, minus, inter, half, torso_shape)


# ---------------------------------------------------------------- hair

def hair_back(p, b, style):
    """hair behind the head (drawn first; from behind, drawn over the back)"""
    p.group('hairback')
    cx, cy = b.hcx, b.hcy
    if VIEW == 'left':
        cx += 2.5          # the hair falls behind: to the right
        if style == 'twintails':
            p.fill(union(ell(cx + b.hrx - 1, cy + 2, 3.4, 6.5), ell(cx + b.hrx, cy + 10, 2.6, 5)), HAIR, 'hairback')
            return
        if style == 'pigtails':
            p.fill(ell(cx + b.hrx - 1, cy + 4, 3.2, 3.6), HAIR, 'hairback')
            return
    if VIEW == 'up' and style == 'ponytail':
        p.fill(union(ell(cx, cy + 4, 3.4, 4), ell(cx, cy + 10, 3.0, 5), ell(cx, cy + 15, 2.2, 3)), HAIR, 'hairback')
        return
    if VIEW == 'up' and style == 'long':    # from behind: down to the shoulder blades
        p.fill(union(rect(cx - b.hrx + 1, cy, cx + b.hrx - 2, b.neck + 4),
                     ell(cx - .5, b.neck + 4, b.hrx - 1.5, 3)), HAIR, 'hairback')
        return
    if VIEW == 'up' and style in ('short', 'bob', 'straight', None):
        return             # the back-of-head hair already covers it
    if style == 'long':
        p.fill(union(ell(cx, cy - 1, b.hrx + 1.5, b.hry + 1),
                     rect(cx - b.hrx - 1, cy, cx + b.hrx, b.neck + 9),
                     ell(cx, b.neck + 9, b.hrx + 1, 3)), HAIR, 'hairback')
    elif style == 'bob':
        p.fill(union(ell(cx, cy, b.hrx + 2, b.hry + 1.5),
                     rect(cx - b.hrx - 2, cy, cx + b.hrx + 1, cy + b.hry - 1)), HAIR, 'hairback')
    elif style == 'ponytail':
        p.fill(ell(cx, cy - 1, b.hrx + 1, b.hry + .5), HAIR, 'hairback')
        p.fill(union(ell(cx + b.hrx - 2, cy + 3, 3.2, 4), ell(cx + b.hrx, cy + 9, 3.0, 5),
                     ell(cx + b.hrx + 1, cy + 14, 2.2, 3)), HAIR, 'hairback')
    elif style == 'twintails':
        p.fill(ell(cx, cy - 1, b.hrx + 1, b.hry + .5), HAIR, 'hairback')
        for s in (-1, 1):
            p.fill(union(ell(cx + s * (b.hrx + 1), cy - 5, 2.6, 2.4),
                         ell(cx + s * (b.hrx + 3), cy + 2, 3.2, 6.5),
                         ell(cx + s * (b.hrx + 3.5), cy + 10, 2.6, 5),
                         ell(cx + s * (b.hrx + 3), cy + 15, 1.6, 2.4)), HAIR, 'hairback')
    elif style == 'pigtails':
        p.fill(ell(cx, cy - 1, b.hrx + 1, b.hry + .5), HAIR, 'hairback')
        for s in (-1, 1):
            p.fill(ell(cx + s * (b.hrx + 2), cy + 4, 3.2, 3.6), HAIR, 'hairback')
    elif style == 'braid':
        p.fill(ell(cx, cy - 1, b.hrx + 1, b.hry + .5), HAIR, 'hairback')
        for k in range(4):
            p.fill(ell(cx - b.hrx + 1 - k * .3, cy + 6 + k * 4, 2.6, 2.4), HAIR, 'hairback')
    elif style == 'bun':
        p.fill(union(ell(cx, b.top - 1, 5, 4.2), ell(cx, b.top + 3, 3, 3)), HAIR, 'hairback')
    elif style == 'mane':
        p.fill(union(ell(cx, cy, b.hrx + 3, b.hry + 2),
                     ell(cx, cy + 6, b.hrx + 2.5, b.hry - 2)), HAIR, 'hairback')
    else:
        p.fill(ell(cx, cy - 1, b.hrx + 1, b.hry + .5), HAIR, 'hairback',
               clip=lambda x, y: y < cy + 4)


def hair_front(p, b, style='straight', part=0):
    """the hair cap over the skull plus bangs; style: straight, swoop,
    spiky, parted, tuft, short, bald"""
    if VIEW == 'up':
        if style != 'bald':
            hair_back_view(p, b, style)
        return
    p.group('hair')
    cx, cy = b.hcx, b.hcy
    ey = b.eye_y
    skull = ell(cx, cy - 1.2, b.hrx + 1.2, b.hry + .6)
    if style == 'bald':
        return
    if VIEW == 'left':
        # side view: a fringe over the brow, the whole back of the head
        back = cx - 3
        p.fill(lambda x, y: skull(x, y) and (y < ey - 2 - (1 if int(x) % 3 == 0 else 0) or
                                             (x > back and y < cy + 6 - (x < back + 3) * 3)), HAIR, 'hair')
        if style == 'spiky':
            for k, dx in enumerate((-6, 0, 6)):
                p.fill(poly([(cx + dx - 2, b.top + 3), (cx + dx + 3, b.top + 3), (cx + dx + 3, b.top - 3 - (k % 2))]),
                       HAIR, 'hair')
        if style == 'tuft':
            p.fill(poly([(cx - 1, b.top + 2), (cx + 3, b.top + 2), (cx + 2, b.top - 3), (cx - 1, b.top - 1)]),
                   HAIR, 'hair')
        return
    if style == 'short':
        edge = lambda x: ey - 3 + (1 if abs(x - cx) > b.hrx - 4 else 0) * 3
    elif style == 'straight':
        edge = lambda x: ey - 1 - (1 if int(x) % 3 == 0 else 0) + (3 if abs(x - cx) > b.hrx - 3 else 0)
    elif style == 'swoop':
        edge = lambda x: ey - 4 + (x - (cx - b.hrx)) * .16 - (2 if int(x) % 5 == 0 else 0) + (5 if abs(x - cx) > b.hrx - 3 else 0)
    elif style == 'parted':
        edge = lambda x: ey - 4 + abs(x - (cx + part)) * .45 + (3 if abs(x - cx) > b.hrx - 3 else 0) - \
            (2.5 if abs(x - (cx + part)) < 1.2 else 0) * 0 - (6 if abs(x - (cx + part)) < .8 else 0)
    elif style == 'spiky':
        edge = lambda x: ey - 2 - ((int(x) % 4) in (0, 1)) * 2 + (4 if abs(x - cx) > b.hrx - 3 else 0)
    elif style == 'tuft':
        edge = lambda x: ey - 4 + (2 if abs(x - cx) > b.hrx - 3 else 0)
    else:
        edge = lambda x: ey - 3
    p.fill(lambda x, y: skull(x, y) and y < edge(x), HAIR, 'hair')
    # side locks framing the cheeks
    if style in ('straight', 'swoop', 'parted', 'spiky'):
        for s in (-1, 1):
            p.fill(poly([(cx + s * (b.hrx + 1), cy - 3), (cx + s * (b.hrx - 3), cy - 3),
                         (cx + s * (b.hrx - .5), cy + 5)]), HAIR, 'hair')
    if style == 'spiky':
        for k, dx in enumerate((-8, -3, 3, 8)):
            p.fill(poly([(cx + dx - 3, b.top + 3), (cx + dx + 2, b.top + 3),
                         (cx + dx + (1 if dx > 0 else -2), b.top - 3 - (k % 2))]), HAIR, 'hair')
    if style == 'tuft':
        p.fill(poly([(cx - 1, b.top + 2), (cx + 3, b.top + 2), (cx + 2, b.top - 3), (cx - 1, b.top - 1)]),
               HAIR, 'hair')
    hair_shine(p, b)


def hair_shine(p, b, dy=0):
    """the anime shine ring across the crown"""
    y = int(b.top + 4 + dy)
    cx = b.hcx
    pts = []
    for x in range(int(cx - b.hrx + 2), int(cx - 1)):
        yy = y + (1 if x < cx - b.hrx + 5 else 0)
        if p.g(x, yy) == 'hair' and p.g(x, yy - 2) == 'hair':
            pts.append((x, yy))
    pts2 = [(x, y) for x in range(int(cx + 2), int(cx + 5)) if p.g(x, y) == 'hair' and p.g(x, y - 2) == 'hair']
    p.detail(pts + pts2, HAIR_L, flat=True)


def hair_back_view(p, b, style):
    """player/any from behind: the whole head is hair, with strands"""
    p.group('hair')
    cx, cy = b.hcx, b.hcy
    p.fill(ell(cx, cy - .5, b.hrx + 1, b.hry + .6), HAIR, 'hair')
    nape = lambda x: cy + b.hry - 1 - (2 if int(x) % 4 in (0, 1) else 0)
    p.fill(lambda x, y: ell(cx, cy + 1.5, b.hrx - 1, b.hry)(x, y) and y < nape(x), HAIR, 'hair')
    for k, dx in enumerate((-8, -3, 2, 7)):
        p.detail([(int(cx + dx + (1 if j > 3 else 0)), int(cy - 4 + j)) for j in range(0, 7 + (k % 2) * 2)],
                 HAIR_S, flat=True)
    hair_shine(p, b, dy=1)


# ---------------------------------------------------------------- hats

def cap_hat(p, b, crown=CA, brim=CB, badge=WHITE, back=False):
    p.group('hat')
    cx, top = b.hcx, b.top
    dome = inter(ell(cx, top + 6.5, b.hrx + 1, 8), lambda x, y: y < top + 7)
    p.fill(dome, crown, 'hat')
    if VIEW == 'up':
        back = True
    if VIEW == 'left':
        p.fill(ell(cx - b.hrx + 1, top + 7.5, 8, 2.4), brim, 'hat')
        return
    if not back:
        p.fill(ell(cx - 1, top + 7.5, 11, 2.4), brim, 'hat')
        p.fill(ell(cx - 1, top + 2.5, 2.2, 2.0), badge, 'hat', flat=True)
        p.fill(rect(cx - 1, top - 2, cx, top - 1), crown, 'hat')
    else:
        p.fill(rect(cx - 3, top + 5, cx + 3, top + 6), brim, 'hat', flat=True)
        p.fill(rect(cx - 1, top - 2, cx, top - 1), crown, 'hat')


def sun_hat(p, b, crown=AC, band=CA, flower=CB, brim_w=17):
    p.group('hat')
    cx, top = b.hcx, b.top
    p.fill(ell(cx, top + 6, brim_w, 3.4), crown, 'hat')
    p.fill(ell(cx, top + 2.5, 9.5, 6), crown, 'hat', clip=lambda x, y: y < top + 6)
    p.fill(rect(cx - 10, top + 3, cx + 10, top + 4), band, 'hat', flat=True, only=('hat',))
    if flower is not None:
        fx, fy = cx + 6, top + 3
        p.fill(union(ell(fx - 1.5, fy, 1.6, 1.6), ell(fx + 1.5, fy, 1.6, 1.6), ell(fx, fy - 1.5, 1.6, 1.6),
                     ell(fx, fy + 1.5, 1.6, 1.6)), flower, 'hatflower')
        p.detail([(int(fx), int(fy))], WHITE)


def beanie(p, b, main=CA, rim=CB, pom=WHITE):
    p.group('hat')
    cx, top = b.hcx, b.top
    p.fill(inter(ell(cx, top + 7, b.hrx + 1.5, 9), lambda x, y: y < top + 6.5), main, 'hat')
    p.fill(rect(cx - b.hrx - 1, top + 4, cx + b.hrx, top + 7), rim, 'hat',
           clip=ell(cx, top + 7, b.hrx + 1.8, 9))
    for x in range(int(cx - b.hrx), int(cx + b.hrx), 2):
        p.detail([(x, top + 5), (x, top + 6)], {CA: CA_S, CB: CB_S}.get(rim, rim))
    if pom is not None:
        p.fill(ell(cx, top - 3, 3, 2.8), pom, 'pom')


def bucket_hat(p, b, main=CA, band=CB):
    p.group('hat')
    cx, top = b.hcx, b.top
    w = b.hrx
    p.fill(poly([(cx - w + 3, top - 2), (cx + w - 3, top - 2), (cx + w, top + 5), (cx - w, top + 5)]), main, 'hat')
    p.fill(ell(cx, top + 6, w + 4, 3), main, 'hat')
    p.fill(rect(cx - w, top + 2, cx + w, top + 3), band, 'hat', flat=True, only=('hat',))


def straw_hat(p, b):
    sun_hat(p, b, crown=AC, band=CA, flower=None, brim_w=20)
    for x in range(int(b.hcx - 16), int(b.hcx + 17), 3):
        p.detail([(x, int(b.top + 6))], AC_S)


def witch_hat(p, b, main=CA, band=CB):
    p.group('hat')
    cx, top = b.hcx, b.top
    p.fill(ell(cx, top + 5.5, 16, 3), main, 'hat')
    p.fill(poly([(cx - 8, top + 5), (cx + 8, top + 5), (cx + 4, top - 5), (cx + 10, top - 11),
                 (cx + 1, top - 7), (cx - 4, top - 2)]), main, 'hat')
    p.fill(rect(cx - 8, top + 2, cx + 8, top + 4), band, 'hat', flat=True, only=('hat',))
    p.fill(rect(cx - 2, top + 2, cx + 1, top + 4), AC, 'buckle', flat=True)


def helmet_lamp(p, b, main=AC, lamp=WHITE):
    p.group('hat')
    cx, top = b.hcx, b.top
    p.fill(inter(ell(cx, top + 7, b.hrx + 2, 10), lambda x, y: y < top + 6.5), main, 'hat')
    p.fill(rect(cx - b.hrx - 3, top + 5, cx + b.hrx + 2, top + 6), main, 'hat')
    if VIEW == 'up':
        return
    lx = cx - b.hrx + 3 if VIEW == 'left' else cx
    p.fill(ell(lx, top + 1.5, 3, 2.6), lamp, 'lamp', flat=True)
    p.detail([(int(lx) - 1, int(top))], WHITE)


def toque(p, b, main=WHITE):
    p.group('hat')
    cx, top = b.hcx, b.top
    p.fill(union(ell(cx - 5, top - 4, 5, 5), ell(cx + 5, top - 4, 5, 5), ell(cx, top - 7, 6, 5),
                 rect(cx - 8, top - 3, cx + 8, top + 5)), main, 'hat')
    p.fill(rect(cx - 9, top + 2, cx + 9, top + 5), main, 'hat')
    p.detail([(x, int(top + 1)) for x in range(int(cx - 8), int(cx + 9))], CA_S if main != WHITE else 14)


def sailor_hat(p, b, main=WHITE, band=CA):
    p.group('hat')
    cx, top = b.hcx, b.top
    p.fill(inter(ell(cx, top + 5, 11, 7), lambda x, y: y < top + 5), main, 'hat')
    p.fill(rect(cx - 11, top + 3, cx + 11, top + 5), band, 'hat')
    p.fill(ell(cx, top + 1, 2, 2), band, 'hat', flat=True)


def ranger_hat(p, b, main=CA, band=CB, feather=AC):
    p.group('hat')
    cx, top = b.hcx, b.top
    p.fill(ell(cx, top + 6, 17, 3.2), main, 'hat')
    p.fill(poly([(cx - 8, top + 6), (cx + 8, top + 6), (cx + 7, top - 2), (cx + 2, top - 1),
                 (cx, top - 3), (cx - 2, top - 1), (cx - 7, top - 2)]), main, 'hat')
    p.fill(rect(cx - 8, top + 3, cx + 8, top + 4), band, 'hat', flat=True, only=('hat',))
    p.fill(poly([(cx + 6, top + 3), (cx + 8, top + 3), (cx + 15, top - 8), (cx + 12, top - 7)]),
           feather, 'feather')


def hood(p, b, main=CA, fur=WHITE):
    p.group('hood')
    cx, cy = b.hcx, b.hcy
    if VIEW == 'up':
        p.fill(ell(cx, cy + .5, b.hrx + 3, b.hry + 3), main, 'hood')
        return
    if VIEW == 'left':
        p.fill(minus(ell(cx + 1, cy + .5, b.hrx + 3, b.hry + 3), ell(cx - 4, cy + 3, b.hrx - 4, b.hry - 3)),
               main, 'hood')
        p.fill(minus(ell(cx - 3, cy + 2.5, b.hrx - 3, b.hry - 1.2), ell(cx - 4, cy + 3, b.hrx - 4, b.hry - 3)),
               fur, 'hood', flat=True)
        return
    p.fill(minus(ell(cx, cy + .5, b.hrx + 3, b.hry + 3), ell(cx, cy + 3, b.hrx - 2.5, b.hry - 3)),
           main, 'hood')
    p.fill(minus(ell(cx, cy + 2.5, b.hrx - 1, b.hry - 1.2), ell(cx, cy + 3, b.hrx - 2.8, b.hry - 3.2)),
           fur, 'hood', flat=True)
    for x in range(int(cx - b.hrx), int(cx + b.hrx), 3):
        p.detail([(x, int(cy - b.hry + 4))], WHITE)


def headband(p, b, main=CA, tails=True):
    p.group('band')
    cx = b.hcx
    y = b.eye_y - 4
    p.fill(inter(rect(cx - b.hrx - 2, y, cx + b.hrx + 2, y + 2),
                 ell(b.hcx, b.hcy - 1.2, b.hrx + 1.6, b.hry + 1)), main, 'band')
    if tails:
        p.fill(union(poly([(cx + b.hrx, y), (cx + b.hrx + 6, y + 2), (cx + b.hrx + 5, y + 4), (cx + b.hrx, y + 2)]),
                     poly([(cx + b.hrx, y + 1), (cx + b.hrx + 4, y + 6), (cx + b.hrx + 2, y + 7), (cx + b.hrx - 1, y + 2)])),
               main, 'band')


def circlet(p, b, main=AC, gem=CB):
    p.group('crown')
    cx = b.hcx
    y = b.top + 3
    p.fill(inter(rect(cx - b.hrx - 2, y, cx + b.hrx + 2, y + 1),
                 ell(b.hcx, b.hcy - 1.2, b.hrx + 1.6, b.hry + 1)), main, 'crown')
    p.fill(poly([(cx - 3, y + 1), (cx + 3, y + 1), (cx, y - 5)]), main, 'crown')
    p.fill(ell(cx, y - 1, 1.5, 1.5), gem, 'crown', flat=True)


def knight_helm(p, b, main=AC, plume=CA):
    p.group('hat')
    cx, top = b.hcx, b.top
    if VIEW == 'up':
        p.fill(ell(cx, b.hcy, b.hrx + 2, b.hry + 2), main, 'hat')
    p.fill(inter(ell(cx, top + 8, b.hrx + 2, 11), lambda x, y: y < top + 7), main, 'hat')
    p.fill(rect(cx - b.hrx - 2, top + 5, cx - b.hrx + 2, b.eye_y + 6), main, 'hat',
           clip=ell(cx, b.hcy, b.hrx + 2.5, b.hry + 3))
    p.fill(rect(cx + b.hrx - 2, top + 5, cx + b.hrx + 1, b.eye_y + 6), main, 'hat',
           clip=ell(cx, b.hcy, b.hrx + 2.5, b.hry + 3))
    p.fill(rect(cx - 1, top - 1, cx, top + 6), main, 'hat', flat=True)
    p.fill(union(ell(cx + 1, top - 4, 3, 3), ell(cx + 5, top - 5, 4, 2.6), ell(cx + 9, top - 3, 3, 2.4)),
           plume, 'plume')


def goggles(p, b, frame=AC, lens=WHITE, on_eyes=False):
    p.group('goggles')
    y = b.eye_y + 2 if on_eyes else b.top + 5
    cx = b.hcx
    p.fill(inter(rect(cx - b.hrx - 2, y - 1, cx + b.hrx + 2, y), ell(cx, b.hcy - 1, b.hrx + 1.5, b.hry + 1.5)),
           CB_S, 'strap')
    if VIEW == 'up':
        return
    for s in ((-1,) if VIEW == 'left' else (-1, 1)):
        if VIEW == 'left':
            s = -1.6
        p.fill(ell(cx + s * 4.5, y, 3.6, 3.2), frame, 'goggles')
        p.fill(ell(cx + s * 4.5, y, 2.1, 1.8), lens, 'goggles', flat=True)
        p.detail([(int(cx + s * 4.5) - 1, y - 1)], WHITE)


@front_only
def glasses(p, b):
    y = b.eye_y + 2
    cx = b.hcx
    pts = []
    for s in (-1, 1):
        ex = int(cx - 5.5) if s < 0 else int(cx + 4.5)
        for dx in range(-3, 4):
            pts += [(ex + dx, y - 2), (ex + dx, y + 3)]
        for dy in range(-1, 3):
            pts += [(ex - 3, y + dy), (ex + 3, y + dy)]
    pts += [(int(cx) - 1, y), (int(cx), y)]
    p.detail(pts, OUT)


def scarf(p, b, main=CA, stripe=CB):
    p.group('scarf')
    cx, y = b.cx, b.neck
    p.fill(ell(cx, y + 1, b.sh + 1.5, 3), main, 'scarf')
    p.fill(poly([(cx + 2, y + 1), (cx + 6, y + 1), (cx + 7, y + 11), (cx + 3, y + 11)]), main, 'scarf')
    p.fill(rect(cx + 2, y + 7, cx + 8, y + 8), stripe, 'scarf', flat=True, only=('scarf',))
    p.detail([(int(cx + 3), y + 12), (int(cx + 5), y + 12), (int(cx + 7), y + 12)], main)


# ---------------------------------------------------------------- torso extras

@front_only
def collar(p, b, slot=WHITE):
    cx, y = b.cx, b.neck
    p.fill(union(poly([(cx - 4, y - 1), (cx, y + 3), (cx - 1, y + 4), (cx - 5, y + 1)]),
                 poly([(cx + 4, y - 1), (cx, y + 3), (cx + 1, y + 4), (cx + 5, y + 1)])), slot, 'collar')


def belt(p, b, slot=AC_S, buckle=AC):
    y = b.waist - 1
    p.fill(rect(b.cx - b.hh - 1, y - 1, b.cx + b.hh + 1, y), slot, 'belt', only=('torso', 'belt'))
    p.fill(rect(b.cx - 1, y - 1, b.cx + 1, y), buckle, 'belt', flat=True, only=('belt',))


def skirt(p, b, slot=CB, flare=3.5, length=6):
    p.group('skirt')
    y = b.waist - 2
    p.fill(poly([(b.cx - b.hh + 1, y), (b.cx + b.hh - 1, y), (b.cx + b.hh + flare, y + length),
                 (b.cx - b.hh - flare, y + length)]), slot, 'skirt')
    for k in (-3, 0, 3):
        p.detail([(int(b.cx + k * 1.4 + 1), y + length - 1), (int(b.cx + k * 1.4 + 1), y + length - 2)],
                 {CA: CA_S, CB: CB_S}.get(slot, slot))


def robe(p, b, slot=CA, hem=CB, length=None):
    """a long robe/dress over the legs, down to the ankles"""
    p.group('robe')
    y = b.neck
    bot = b.feet - 2 if length is None else length
    p.fill(poly([(b.cx - b.sh + 1, y), (b.cx + b.sh - 1, y), (b.cx + b.sh, y + 2),
                 (b.cx + b.hh + 5, bot), (b.cx - b.hh - 5, bot), (b.cx - b.sh, y + 2)]), slot, 'robe')
    if hem is not None:
        p.fill(rect(b.cx - b.hh - 6, bot - 1, b.cx + b.hh + 6, bot), hem, 'robe', flat=True, only=('robe',))


@front_only
def apron(p, b, slot=WHITE, bib=True):
    p.group('apron')
    y = b.neck + 3 if bib else b.waist - 2
    p.fill(union(rect(b.cx - 4, y, b.cx + 3, b.waist), poly([(b.cx - 6, b.waist - 1), (b.cx + 5, b.waist - 1),
                                                            (b.cx + 7, b.waist + 6), (b.cx - 8, b.waist + 6)])),
           slot, 'apron')
    p.fill(rect(b.cx - 2, b.waist + 1, b.cx + 1, b.waist + 3), {WHITE: 14}.get(slot, CB), 'pocket', flat=True)


@front_only
def overall_bib(p, b, slot=CB, button=AC):
    p.group('bib')
    y = b.neck + 3
    p.fill(rect(b.cx - 4, y, b.cx + 3, b.waist), slot, 'bib')
    for s in (-1, 1):
        p.fill(cap(b.cx + s * 4 - (1 if s > 0 else 0), y, b.cx + s * (b.sh - 1.5), b.neck, .8), slot, 'bib')
    p.detail([(int(b.cx - 3), y + 1), (int(b.cx + 2), y + 1)], button)


def cape(p, b, slot=CA, lining=CB):
    """behind the body (paint before the torso)"""
    p.group('cape')
    y = b.neck
    if VIEW == 'left':
        p.fill(poly([(b.cx - 1, y), (b.cx + b.sh + 1, y), (b.cx + b.sh + 6, b.feet - 1), (b.cx, b.feet - 1)]),
               slot, 'cape')
        return
    p.fill(poly([(b.cx - b.sh - 1, y), (b.cx + b.sh + 1, y), (b.cx + b.sh + 7, b.feet - 1),
                 (b.cx - b.sh - 7, b.feet - 1)]), slot, 'cape')
    p.fill(poly([(b.cx - b.sh - 4, b.feet - 12), (b.cx - b.sh - 7, b.feet - 1), (b.cx - b.sh - 2, b.feet - 1)]),
           lining, 'cape', flat=True)
    p.fill(poly([(b.cx + b.sh + 4, b.feet - 12), (b.cx + b.sh + 7, b.feet - 1), (b.cx + b.sh + 2, b.feet - 1)]),
           lining, 'cape', flat=True)


def backpack(p, b, slot=AC, flap=CB, big=False):
    """behind the body (paint before the torso): peeks out at the sides"""
    p.group('pack')
    w = b.sh + (4 if big else 2)
    top = b.neck - (6 if big else 1)
    if VIEW == 'left':
        p.fill(ell(b.cx + b.sh + 1, (top + b.waist) / 2, 4 if big else 3, (b.waist - top) / 2 + 1), slot, 'pack')
        return
    p.fill(ell(b.cx, (top + b.waist) / 2, w, (b.waist - top) / 2 + 1), slot, 'pack')
    if big:
        p.fill(ell(b.cx, top + 1, w - 1, 3.5), flap, 'pack')
        p.fill(ell(b.cx + w - 3, top - 2, 3, 2.5), CB_S, 'bedroll')


def stripes(p, b, slot, rows, group='torso'):
    for y in rows:
        p.fill(rect(b.cx - b.hh - 2, b.neck + y, b.cx + b.hh + 2, b.neck + y), slot, group, only=(group,))


def beard(p, b, slot=HAIR):
    if VIEW == 'up':
        return
    if VIEW == 'left':
        p.group('beard')
        p.fill(inter(ell(b.hcx - 3, b.hcy + b.hry - 2, 7, 4.5), ell(b.hcx, b.hcy, b.hrx + .5, b.hry + 1)), slot, 'beard')
        return
    return _beard(p, b, slot)


def _beard(p, b, slot=HAIR):
    """a round chin beard with sideburns; the smile stays visible"""
    p.group('beard')
    cx, cy = b.hcx, b.hcy
    my = b.eye_y + 8
    p.fill(union(inter(ell(cx, cy + 3, b.hrx + .5, b.hry), lambda x, y: y > my - 1 and abs(x - cx) > 3.5),
                 ell(cx, cy + b.hry - .5, 6.5, 4.2),
                 inter(ell(cx, cy + 2, b.hrx + .5, b.hry), lambda x, y: y > cy - 1 and abs(x - cx) > b.hrx - 2.5)),
           slot, 'beard')
    p.detail([(int(cx) - 2, my), (int(cx) - 1, my + 1), (int(cx), my + 1), (int(cx) + 1, my)], OUT, 'beardmouth')
    p.detail([(int(cx) - 1, my), (int(cx), my)], BLUSH, 'beardmouth')


def vest(p, b, slot=CB):
    p.group('vest')
    if VIEW == 'up':
        p.fill(torso_shape(b), slot, 'vest')
        return
    for s in (-1, 1):
        p.fill(inter(torso_shape(b), lambda x, y, s=s: (x - b.cx) * s > 1.5), slot, 'vest')
    for k in range(2):
        p.detail([(int(b.cx - 5), b.neck + 6 + k * 3), (int(b.cx + 4), b.neck + 6 + k * 3)], AC)


def breastplate(p, b, slot=AC):
    p.group('plate')
    p.fill(poly([(b.cx - b.sh + 1, b.neck + 1), (b.cx + b.sh - 1, b.neck + 1), (b.cx + b.hh - 1, b.waist - 2),
                 (b.cx, b.waist + 1), (b.cx - b.hh + 1, b.waist - 2)]), slot, 'plate')
    p.fill(rect(b.cx - 1, b.neck + 3, b.cx, b.waist - 3), CA, 'plate', flat=True, only=('plate',))


def pauldrons(p, b, slot=AC):
    p.group('pauldron')
    for s in (-1, 1):
        sx, sy = b.shoulder(s)
        p.fill(ell(sx + s * .5, sy, 4, 3.2), slot, 'pauldron')


def sailor_collar(p, b, main=WHITE, stripe=CA, tie=CB):
    p.group('sailor')
    y = b.neck
    if VIEW == 'up':      # the square flap over the shoulders
        p.fill(rect(b.cx - b.sh + 1, y, b.cx + b.sh - 2, y + 5), main, 'sailor')
        p.fill(rect(b.cx - b.sh + 1, y + 4, b.cx + b.sh - 2, y + 4), CA, 'sailor', flat=True, only=('sailor',))
        return
    if VIEW == 'left':
        return
    p.fill(poly([(b.cx - b.sh, y), (b.cx + b.sh, y), (b.cx + b.sh - 1, y + 4), (b.cx, y + 7), (b.cx - b.sh + 1, y + 4)]),
           main, 'sailor')
    p.fill(poly([(b.cx - 3, y), (b.cx + 3, y), (b.cx, y + 4)]), CA, 'sailorv', flat=True)
    p.line['sailorv'] = None
    p.fill(union(poly([(b.cx - 1, y + 6), (b.cx - 5, y + 10), (b.cx - 2, y + 10)]),
                 poly([(b.cx, y + 6), (b.cx + 4, y + 10), (b.cx + 1, y + 10)]),
                 ell(b.cx - .5, y + 6, 1.8, 1.5)), tie, 'tie')


def shawl(p, b, slot=CB):
    p.group('shawl')
    y = b.neck
    p.fill(poly([(b.cx - b.sh - 2, y + 3), (b.cx - b.sh + 1, y - 1), (b.cx + b.sh - 1, y - 1),
                 (b.cx + b.sh + 2, y + 3), (b.cx, y + 9)]), slot, 'shawl')
    for k in range(-3, 4, 2):
        p.detail([(int(b.cx + k * 2), y + 4 + (3 - abs(k)))], {CB: CB_S, CA: CA_S}.get(slot, slot))


def swimsuit(p, b, slot=CA, trim=WHITE):
    """a one-piece over bare skin: the torso is skin above the chest"""
    p.fill(inter(torso_shape(b), lambda x, y: y < b.neck + 4), SKIN, 'torso', only=('torso',))
    p.fill(rect(b.cx - 4, b.neck + 1, b.cx - 3, b.neck + 3), slot, 'torso', only=('torso',))
    p.fill(rect(b.cx + 2, b.neck + 1, b.cx + 3, b.neck + 3), slot, 'torso', only=('torso',))
    p.fill(rect(b.cx - b.hh - 2, b.neck + 6, b.cx + b.hh + 2, b.neck + 6), trim, 'torso', flat=True, only=('torso',))


def mittens(p, b):
    pass


def bow_ribbon(p, b, slot=CB, where='top'):
    p.group('ribbon')
    cx = b.hcx + (6 if where == 'side' else 0)
    y = b.top + (1 if where == 'top' else 3)
    p.fill(union(poly([(cx, y), (cx - 5, y - 3), (cx - 5, y + 3)]), poly([(cx, y), (cx + 5, y - 3), (cx + 5, y + 3)]),
                 ell(cx, y, 1.5, 1.5)), slot, 'ribbon')


def flower_pin(p, b, slot=CB):
    p.group('pin')
    fx, fy = b.hcx - b.hrx + 3, b.top + 6
    p.fill(union(ell(fx - 1.5, fy, 1.6, 1.6), ell(fx + 1.5, fy, 1.6, 1.6), ell(fx, fy - 1.5, 1.6, 1.6),
                 ell(fx, fy + 1.5, 1.6, 1.6)), slot, 'pin')
    p.detail([(int(fx), int(fy))], AC)


def leaf_sprout(p, b):
    p.group('sprout')
    cx, top = b.hcx + 1, b.top
    p.fill(cap(cx, top + 2, cx, top - 3, .6), CB_S, 'sprout')
    p.fill(union(ell(cx - 3, top - 4, 3, 1.6), ell(cx + 3, top - 5, 3, 1.6)), CB, 'sprout')
