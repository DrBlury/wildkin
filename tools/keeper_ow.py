"""Overworld people drawn from the bout-portrait cast (keeper_cast.py).

Each archetype also walks the map as a 16x32 person with the usual nine
frames (gen_field_gfx.py's layout: 0 down, 1-2 down walking, 3 up, 4-5 up
walking, 6 left, 7-8 left walking; right = mirrored left). They are painted
in the same palette slots as the portraits, so a warden's colour variation
(keeper_palette) looks the same on the map and in the bout.

How: the body, clothes, hair and hats are painted with the portrait parts
at twice the size (keeper_parts.VIEW picks front, back or side), the part
map is shrunk 2:1 by majority, and outlines, shading and the face are done
at full size on the small image.
"""

from keeper_art import (T, OUT, WHITE, EYE, SKIN, SKIN_S, BLUSH, HAIR, HAIR_S, HAIR_L, CA, AC,
                        Painter, Body, draw_arm, draw_legs, draw_torso, draw_head)
import keeper_parts as K

OW_W, OW_H = 16, 32
X0 = 16          # the 32px-wide strip of the 64px painting that becomes the sprite
VIEWS = (('down', 0), ('down', 1), ('down', 2), ('up', 0), ('up', 1), ('up', 2),
         ('left', 0), ('left', 1), ('left', 2))


def _paint(spec, view, phase):
    K.VIEW = view
    try:
        return _paint_view(spec, view, phase)
    finally:
        K.VIEW = 'down'


def _paint_view(spec, view, phase):
    side = view == 'left'
    b = Body(spec.get('kind', 'teen'), hop=-2, bob=2 if phase else 0, side=side)
    p = Painter()
    legs = spec.get('legs', ('pants', CB_DEFAULT, CA))
    sock = legs[3] if len(legs) > 3 else None
    if side:
        stride, lift = ((1.0, (0, 0)), (3.5, (0, 0)), (1.5, (2, 0)))[phase]
    else:
        stride, lift = 0, ((0, 0), (3, 0), (0, 3))[phase]
    sleeve = spec.get('sleeve', ('long', CA))
    glove = spec.get('glove', SKIN)

    def arms():
        if side:
            ang = (4, 28, -22)[phase]
            draw_arm(p, b, -1, ang, 4, sleeve=sleeve[1], sleeve_len=sleeve[0], hand=glove, cuff=spec.get('cuff'))
            return
        sw = (0, 8, -8)[phase]
        draw_arm(p, b, -1, 6 + sw, 6, sleeve=sleeve[1], sleeve_len=sleeve[0], hand=glove, cuff=spec.get('cuff'))
        draw_arm(p, b, 1, 6 - sw, 6, sleeve=sleeve[1], sleeve_len=sleeve[0], hand=glove, cuff=spec.get('cuff'))

    if view != 'up':
        for f in spec.get('back', ()):
            f(p, b)
        if spec.get('hairback'):
            K.hair_back(p, b, spec['hairback'])
    draw_legs(p, b, pants=legs[1], shoes=legs[2], style=legs[0], sock=sock, lift=lift, stride=stride)
    for f in spec.get('under', ()):
        f(p, b)
    draw_torso(p, b, spec.get('shirt', CA), flare=spec.get('flare', 0))
    for f in spec.get('over', ()):
        f(p, b)
    if view == 'up':
        arms()
        for f in spec.get('back', ()):
            f(p, b)
    draw_head(p, b, back=view == 'up')
    if side:
        p.fill(lambda x, y: ((x - (b.hcx + 2)) / 2.2) ** 2 + ((y - (b.hcy + 2.5)) / 2.8) ** 2 <= 1, SKIN, 'ear')
    K.hair_front(p, b, spec.get('hair', 'straight'), spec.get('part', 0))
    if view == 'up' and spec.get('hairback'):
        K.hair_back(p, b, spec['hairback'])
    for f in spec.get('head', ()):
        f(p, b)
    for f in spec.get('neck', ()):
        f(p, b)
    if view != 'up':
        arms()
    for f in spec.get('post', ()):
        f(p, b)
    return p, b


CB_DEFAULT = 12


def _shrink(big):
    """2:1 majority shrink of the part map (x 16..47 of the painting)"""
    small = Painter(OW_W, OW_H, small=True)
    small.z = dict(big.z)
    small.line = dict(big.line)
    for y in range(OW_H):
        for x in range(OW_W):
            cells = []
            for dy in (0, 1):
                for dx in (0, 1):
                    X, Y = X0 + x * 2 + dx, y * 2 + dy
                    if big.grp[Y][X] is not None and big.slot[Y][X] != T:
                        cells.append((big.slot[Y][X], big.grp[Y][X], big.flat[Y][X]))
            if len(cells) < 2:
                continue
            best, score = None, -1
            for c in cells:
                n = sum(1 for d in cells if d[1] == c[1])
                sc = n * 100 + big.z.get(c[1], 0)       # most pixels, then the front-most part
                if sc > score:
                    best, score = c, sc
            # keep the part's own colour: its most common slot in the block
            slots = [c[0] for c in cells if c[1] == best[1]]
            slot = max(set(slots), key=slots.count)
            small.slot[y][x] = slot
            small.grp[y][x] = best[1]
            small.flat[y][x] = best[2]
    return small


def _face(p, b, view, spec):
    """eyes, blush and mouth at full size"""
    ey = int(b.eye_y + 2) // 2
    cx = (b.hcx - X0) / 2      # 8.0 for a centred head
    p.group('face', None)

    def put(x, y, slot):
        if p.g(x, y) in ('head',):
            p.detail([(x, y)], slot)
    if view == 'down':
        for ex in (int(cx) - 4, int(cx) + 2):
            if spec.get('eyes') in ('sleepy',):
                put(ex, ey + 1, EYE)
                put(ex + 1, ey + 1, EYE)
            else:
                put(ex, ey, EYE)
                put(ex + 1, ey, WHITE if ex < cx else EYE)
                put(ex, ey + 1, EYE)
                put(ex + 1, ey + 1, EYE)
                if ex > cx:
                    put(ex, ey, WHITE)
                    put(ex + 1, ey, EYE)
        put(int(cx) - 5, ey + 2, BLUSH)
        put(int(cx) + 4, ey + 2, BLUSH)
        put(int(cx) - 1, ey + 2, OUT)
        put(int(cx), ey + 2, OUT)
    elif view == 'left':
        ex = int(cx) - 5
        if spec.get('eyes') in ('sleepy',):
            put(ex, ey + 1, EYE)
            put(ex + 1, ey + 1, EYE)
        else:
            put(ex, ey, WHITE)
            put(ex + 1, ey, EYE)
            put(ex, ey + 1, EYE)
            put(ex + 1, ey + 1, EYE)
        put(ex + 1, ey + 2, BLUSH)
        put(ex - 1, ey + 2, OUT)


def _shine(p, view):
    """a little shine on the hair (front and side)"""
    if view == 'up':
        xs = (5, 6)
    else:
        xs = (4, 5, 6) if view == 'down' else (7, 8, 9)
    for x in xs:
        for y in range(OW_H):
            if p.grp[y][x] == 'hair':
                if y + 1 < OW_H and p.grp[y + 1][x] == 'hair' and y + 2 < OW_H and p.grp[y + 2][x] == 'hair':
                    p.detail([(x, y + 1)], HAIR_L)
                break


def person_ow(spec, view, phase):
    big, b = _paint(spec, view, phase)
    small = _shrink(big)
    # small parts read better without a line between them and the cloth
    for g in list(small.line):
        if small.line[g] == 'out' and g not in ('head', 'hair', 'hat', 'hood', 'armL', 'armR', 'legs', 'shoes',
                                                'torso', 'hairback', 'pack', 'cape', 'robe', 'skirt', 'prop'):
            small.line[g] = 'shade'
    _shine(small, view)
    _face(small, b, view, spec)
    return small.finish()


def frames_ow(spec):
    return [person_ow(spec, v, ph) for v, ph in VIEWS]
