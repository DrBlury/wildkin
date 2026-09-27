"""The bout-portrait cast: 20 keeper archetypes and the player.

Each archetype is a config for person(): body kind, hair, hat, outfit
pieces, the prop it carries, its signature FLAIR pose, and its default
look plus the looks its variations draw from (keeper_art ramp names).
"""

import math

from keeper_art import (T, OUT, WHITE, EYE, SKIN, SKIN_S, BLUSH, HAIR, HAIR_S, HAIR_L,
                        CA, CA_S, CB, CB_S, AC, AC_S, Painter, Body,
                        ell, rect, poly, cap, union, minus, inter,
                        arm_points, draw_arm, draw_legs, draw_torso, draw_head, draw_face, lantern)
import keeper_parts as K

FRAMES = ('IDLE', 'BREATH', 'FLAIR', 'THROW', 'LOSE')
PLAYER_FRONT = ('IDLE', 'BREATH', 'WAVE', 'CHEER')
PLAYER_BACK = ('IDLE', 'BREATH', 'WINDUP', 'THROW')


# ---------------------------------------------------------------- props
# prop(p, b, hx, hy, frame): drawn under the hand at (hx, hy)

class Mirror:
    """a Painter seen in a mirror around x = ax: props are drawn for the
    screen-right hand (reaching outward = +x) and mirrored for the left"""

    def __init__(self, p, ax):
        self.p, self.ax = p, ax

    def fill(self, f, *a, **k):
        clip = k.get('clip')
        if clip:
            k['clip'] = lambda x, y: clip(2 * self.ax - x, y)
        self.p.fill(lambda x, y: f(2 * self.ax - x, y), *a, **k)

    def detail(self, pts, *a, **k):
        self.p.detail([(int(2 * self.ax - x - 1), y) for (x, y) in pts], *a, **k)

    def __getattr__(self, name):
        return getattr(self.p, name)


def draw_prop(p, b, name, hx, hy, frame, side):
    q = p if side > 0 else Mirror(p, hx)
    PROPS[name](q, b, hx, hy, frame)


def _grp(p, g='prop'):
    p.group(g)
    return g


def prop_net(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(cap(hx, hy + 3, hx + 8, hy - 13, .8), AC, g)
    p.fill(minus(ell(hx + 10, hy - 18, 4.2, 5), ell(hx + 10, hy - 18, 2.8, 3.6)), AC, g)
    p.fill(ell(hx + 10, hy - 18, 2.8, 3.6), WHITE, 'netmesh', flat=True)
    p.line['netmesh'] = None
    p.detail([(int(hx + 10 + dx), int(hy - 18 + dy)) for dx in (-1, 1) for dy in (-2, 0, 2)], CB, flat=True)


def prop_basket(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(minus(ell(hx, hy - 2, 4, 5), ell(hx, hy - 1, 3, 4)), AC_S, g)
    p.fill(ell(hx, hy + 3, 5, 3.2), AC, g)
    p.fill(rect(hx - 5, hy + 1, hx + 5, hy + 1), AC_S, g, only=(g,))
    for dx, c in ((-3, CB), (0, WHITE), (3, CB)):
        p.fill(ell(hx + dx, hy + .5, 1.5, 1.3), c, 'flowers', flat=True)


def prop_rod(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(cap(hx + 1, hy + 3, hx + 11, hy - 22, .7), AC, g)
    p.detail([(int(hx + 11), int(hy - 22) + k) for k in range(1, 18)], WHITE, 'line')
    p.fill(ell(hx + 11, hy - 3, 1.6, 1.6), CA, 'bob')


def prop_book(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(rect(hx - 4, hy - 4, hx + 3, hy + 5), CB, g)
    p.fill(rect(hx - 3, hy - 3, hx + 3, hy + 4), WHITE, 'pages', flat=True)
    p.fill(rect(hx - 4, hy - 4, hx + 1, hy + 5), CB, 'cover')
    p.detail([(int(hx - 2), int(hy)), (int(hx - 1), int(hy)), (int(hx - 2), int(hy - 1))], AC)


def prop_wrench(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(cap(hx, hy + 2, hx + 7, hy - 9, 1.1), AC, g)
    p.fill(minus(ell(hx + 8, hy - 11, 3.2, 3.2), poly([(hx + 7, hy - 11), (hx + 12, hy - 16), (hx + 13, hy - 12)])),
           AC, g)


def prop_pick(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(cap(hx, hy + 3, hx + 4, hy - 14, .9), AC_S, g)
    p.fill(poly([(hx - 5, hy - 12), (hx + 4, hy - 17), (hx + 13, hy - 14), (hx + 4, hy - 15)]), 14, 'pickhead')


def prop_broom(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(cap(hx + 4, hy - 16, hx - 3, hy + 10, .8), AC_S, g)
    p.fill(poly([(hx - 4, hy + 7), (hx - 1, hy + 8), (hx + 1, hy + 16), (hx - 9, hy + 14)]), AC, 'bristle')


def prop_hammer(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(cap(hx, hy + 2, hx + 5, hy - 11, .9), AC_S, g)
    p.fill(poly([(hx + 1, hy - 11), (hx + 11, hy - 15), (hx + 12, hy - 11), (hx + 2, hy - 7)]), CB, 'hamhead')


def prop_mic(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(cap(hx, hy + 1, hx + 2, hy - 6, 1.0), AC_S, g)
    p.fill(ell(hx + 2.5, hy - 8, 2.4, 2.4), AC, 'mic')
    p.detail([(int(hx + 1), int(hy - 9))], WHITE)


def prop_star_wand(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(cap(hx, hy + 2, hx + 3, hy - 9, .7), WHITE, g)
    cx, cy = hx + 3.5, hy - 12
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        r = 5 if k % 2 == 0 else 2.2
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    p.fill(poly(pts), AC, 'star')


def prop_spoon(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(cap(hx, hy + 2, hx + 3, hy - 9, .8), AC, g)
    p.fill(ell(hx + 3.5, hy - 12, 2.6, 3.4), AC, g)


def prop_anchor(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(cap(hx, hy - 3, hx, hy + 10, 1), AC, g)
    p.fill(minus(ell(hx, hy - 5, 2.2, 2.2), ell(hx, hy - 5, 1, 1)), AC, g)
    p.fill(minus(inter(ell(hx, hy + 6, 6, 6), rect(hx - 7, hy + 7, hx + 7, hy + 13)), ell(hx, hy + 6, 4.3, 4.6)),
           AC, g)
    p.fill(rect(hx - 3, hy - 1, hx + 3, hy), AC, g)


def prop_binoculars(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(union(rect(hx - 4, hy - 3, hx - 1, hy + 2), rect(hx + 1, hy - 3, hx + 4, hy + 2)), CB_S, g)
    p.detail([(int(hx - 3), int(hy - 3)), (int(hx + 2), int(hy - 3))], WHITE)


def prop_cane(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(cap(hx, hy, hx + 1, b.feet, .9), AC, g)
    p.fill(minus(ell(hx - 2, hy - 1, 3, 2.4), ell(hx - 2.2, hy, 1.8, 1.4)), AC, g)


def prop_staff(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(cap(hx, hy - 16, hx, b.feet, .9), AC, g)
    p.fill(ell(hx, hy - 19, 3.2, 3.6), CB, 'orb')
    p.detail([(int(hx - 1), int(hy - 20))], WHITE)


def prop_shield(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(poly([(hx - 7, hy - 7), (hx + 7, hy - 7), (hx + 7, hy + 1), (hx, hy + 9), (hx - 7, hy + 1)]), AC, g)
    p.fill(poly([(hx - 5, hy - 5), (hx + 5, hy - 5), (hx + 5, hy + 1), (hx, hy + 6), (hx - 5, hy + 1)]), CA,
           'crest', flat=True)
    p.fill(union(rect(hx - 1, hy - 4, hx, hy + 4), rect(hx - 4, hy - 2, hx + 3, hy - 1)), AC, 'crestmark', flat=True)
    p.line['crest'] = None
    p.line['crestmark'] = None


def prop_floatie(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(minus(ell(hx, hy + 1, 7, 5.5), ell(hx, hy + 1, 3, 2)), CB, g)
    for a in (0.6, 2.2, 3.8, 5.4):
        p.fill(inter(ell(hx, hy + 1, 7, 5.5), ell(hx + math.cos(a) * 5, hy + 1 + math.sin(a) * 4, 2.2, 2.2)),
               WHITE, g, flat=True, only=(g,))


def prop_fork(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(cap(hx, hy + 12, hx, hy - 14, .8), AC_S, g)
    for dx in (-3, 0, 3):
        p.fill(rect(hx + dx - .5, hy - 20, hx + dx, hy - 15), 14, 'tines')
    p.fill(rect(hx - 3.5, hy - 15, hx + 3, hy - 14), 14, 'tines')


def prop_beads(p, b, hx, hy, frame):
    g = _grp(p)
    for k in range(7):
        a = k * .9
        p.fill(ell(hx + math.sin(a) * 3, hy + 2 + k * 1.4, 1.2, 1.2), AC, g)


def prop_scroll(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(rect(hx - 6, hy - 2, hx + 6, hy + 4), WHITE, g)
    p.fill(union(ell(hx - 6.5, hy + 1, 1.6, 3.8), ell(hx + 6.5, hy + 1, 1.6, 3.8)), AC, 'rolls')
    p.detail([(int(hx - 3 + k), int(hy + 1)) for k in range(0, 6, 2)], CB_S)


def prop_kettle(p, b, hx, hy, frame):
    g = _grp(p)
    p.fill(ell(hx, hy + 4, 5, 4), AC, g)
    p.fill(minus(ell(hx, hy + 1, 3.6, 4), ell(hx, hy + 1, 2.4, 3)), AC_S, g, clip=lambda x, y: y < hy + 1)
    p.fill(cap(hx + 4, hy + 4, hx + 8, hy + 1, .8), AC, g)


PROPS = {
    'net': prop_net, 'basket': prop_basket, 'rod': prop_rod, 'book': prop_book, 'wrench': prop_wrench,
    'pick': prop_pick, 'broom': prop_broom, 'hammer': prop_hammer, 'mic': prop_mic, 'wand': prop_star_wand,
    'spoon': prop_spoon, 'anchor': prop_anchor, 'binoculars': prop_binoculars, 'cane': prop_cane,
    'staff': prop_staff, 'shield': prop_shield, 'floatie': prop_floatie, 'fork': prop_fork,
    'beads': prop_beads, 'scroll': prop_scroll, 'kettle': prop_kettle,
}


# ---------------------------------------------------------------- poses
# arms: (angle, bend) per side; -1 is the screen-left arm (the one nearer
# the player's kin when a keeper faces left).

BASE_POSES = {
    'IDLE':   dict(L=(10, 6), R=(10, 6), face='smile'),
    'BREATH': dict(L=(8, 4), R=(8, 4), face='blink', breath=1),
    'THROW':  dict(L=(35, 20), R=(165, -10), face='open', hop=2, lantern='R'),
    'LOSE':   dict(L=(12, 10), R=(130, 60), face='sweat', brows='worried'),
}

FLAIRS = {  # signature FLAIR poses
    'wave':   dict(L=(10, 6), R=(150, 20), face='open', hop=1),
    'point':  dict(L=(95, -5), R=(10, 6), face='grin', brows='fierce'),
    'cheer':  dict(L=(160, -10), R=(160, -10), face='happy', hop=3),
    'flex':   dict(L=(80, 80), R=(80, 80), face='grin', brows='fierce'),
    'bow':    dict(L=(20, 70), R=(20, 70), face='calm', breath=2),
    'hips':   dict(L=(35, 110), R=(35, 110), face='grin', brows='fierce'),
    'raise':  dict(L=(10, 6), R=(160, 0), face='open', hop=1, prop_hand='R'),
    'salute': dict(L=(10, 6), R=(130, 100), face='smile', brows='fierce'),
    'peace':  dict(L=(10, 6), R=(150, 25), face='happy', hop=1, peace=True),
    'think':  dict(L=(40, 110), R=(50, 125), face='calm'),
    'hug':    dict(L=(45, 80), R=(45, 80), face='happy'),
}


def pose_for(spec, frame):
    if frame == 'FLAIR':
        pose = dict(FLAIRS[spec.get('flair', 'wave')])
    else:
        pose = dict(BASE_POSES[frame])
    # the prop hand keeps its prop in a sensible pose
    return pose


# ---------------------------------------------------------------- person

def person(spec, frame, look_face=0):
    pose = pose_for(spec, frame)
    b = Body(spec.get('kind', 'teen'), breath=pose.get('breath', 0), hop=pose.get('hop', 0))
    p = Painter()
    # back layers
    for f in spec.get('back', ()):
        f(p, b)
    if spec.get('hairback'):
        K.hair_back(p, b, spec['hairback'])
    # arms behind? (none: arms are painted in front)
    legs = spec.get('legs', ('pants', CB, CA))
    draw_legs(p, b, pants=legs[1], shoes=legs[2], style=legs[0], sock=legs[3] if len(legs) > 3 else None)
    for f in spec.get('under', ()):
        f(p, b)
    draw_torso(p, b, spec.get('shirt', CA), flare=spec.get('flare', 0))
    for f in spec.get('over', ()):
        f(p, b)
    draw_head(p, b)
    face = pose.get('face', 'smile')
    draw_face(p, b, face, look=look_face, eyes=spec.get('eyes', 'round'),
              brows=pose.get('brows', spec.get('brows')))
    K.hair_front(p, b, spec.get('hair', 'straight'), spec.get('part', 0))
    for f in spec.get('head', ()):
        f(p, b)
    if spec.get('glasses'):
        K.glasses(p, b)
    for f in spec.get('neck', ()):
        f(p, b)
    # arms, props
    prop = spec.get('prop')
    prop_hand = pose.get('prop_hand', spec.get('prop_hand', 'L'))
    lantern_hand = pose.get('lantern')
    sleeve = spec.get('sleeve', ('long', CA))
    hands = {}
    for side, key in ((-1, 'L'), (1, 'R')):
        ang, bend = pose[key]
        if key == prop_hand and frame not in ('FLAIR', 'LOSE') and spec.get('prop_pose'):
            ang, bend = spec['prop_pose']
        hands[key] = arm_points(b, side, ang, bend)[2]
    for side, key in ((-1, 'L'), (1, 'R')):
        ang, bend = pose[key]
        if key == prop_hand and frame not in ('FLAIR', 'LOSE') and spec.get('prop_pose'):
            ang, bend = spec['prop_pose']
        hx, hy = hands[key]
        holding = None
        if lantern_hand == key:
            holding = 'lantern'
        elif prop and key == prop_hand and not (frame == 'LOSE' and key == 'R'):
            holding = prop
        if holding and holding != 'lantern' and spec.get('prop_behind'):
            draw_prop(p, b, holding, hx, hy, frame, side)
        draw_arm(p, b, side, ang, bend, sleeve=sleeve[1], sleeve_len=sleeve[0],
                 hand=spec.get('glove', SKIN), cuff=spec.get('cuff'))
        if holding == 'lantern':
            lantern(p, int(hx), int(hy) - 5)
            p.fill(ell(hx, hy, 2.4, 2.4), spec.get('glove', SKIN), 'handtop')
        elif holding and not spec.get('prop_behind'):
            draw_prop(p, b, holding, hx, hy, frame, side)
            p.fill(ell(hx, hy, 2.4, 2.4), spec.get('glove', SKIN), 'handtop')
        if pose.get('peace') and key == 'R':
            p.fill(union(cap(hx - 1, hy - 1, hx - 2, hy - 5, .7), cap(hx + 1, hy - 1, hx + 2, hy - 5, .7)),
                   spec.get('glove', SKIN), 'peace')
    for f in spec.get('post', ()):
        f(p, b)
    return p.finish()


# ---------------------------------------------------------------- the player

PLAYER_LOOK = dict(skin='light', hair='cocoa', a='orange', b='navy', acc='wood')


def player_front(frame):
    pose = {'IDLE': dict(L=(10, 6), R=(10, 6), face='smile'),
            'BREATH': dict(L=(8, 4), R=(8, 4), face='blink', breath=1),
            'WAVE': dict(L=(10, 6), R=(150, 20), face='open', hop=1),
            'CHEER': dict(L=(160, -10), R=(160, -10), face='happy', hop=3)}[frame]
    return _player(pose, back=False)


def _player(pose, back):
    b = Body('teen', breath=pose.get('breath', 0), hop=pose.get('hop', 0))
    p = Painter()
    if back:
        draw_legs(p, b, pants=CB, shoes=CB_S, style='pants')
        draw_torso(p, b, CA)
        # arms before the pack only when hanging
        for side, key in ((-1, 'L'), (1, 'R')):
            ang, bend = pose[key]
            if ang < 90:
                draw_arm(p, b, side, ang, bend, sleeve=CA, sleeve_len='short', hand=SKIN)
        # the head from behind
        p.fill(rect(b.hcx - 4, b.hcy + 6, b.hcx + 3, b.neck + 1), SKIN, 'neck')
        for s in (-1, 1):
            p.fill(ell(b.hcx + s * (b.hrx - .5), b.hcy + 2.5, 1.6, 2.2), SKIN, 'ears')
        K.hair_back_view(p, b, 'short')
        K.cap_hat(p, b, AC, AC_S, WHITE, back=True)
        # the satchel/backpack over the back
        p.group('pack')
        p.fill(rect(b.cx - 6, b.neck + 1, b.cx + 5, b.waist - 1), HAIR_L, 'pack')
        p.fill(rect(b.cx - 6, b.neck + 1, b.cx + 5, b.neck + 4), HAIR, 'pack')
        p.fill(rect(b.cx - 1, b.neck + 3, b.cx, b.neck + 6), WHITE, 'pack', flat=True)
        for side, key in ((-1, 'L'), (1, 'R')):
            ang, bend = pose[key]
            if ang >= 90:
                hx, hy = draw_arm(p, b, side, ang, bend, sleeve=CA, sleeve_len='short', hand=SKIN)
                if pose.get('lantern') == key:
                    lantern(p, int(hx), int(hy) - 5)
                    p.fill(ell(hx, hy, 2.4, 2.4), SKIN, 'handtop')
        return p.finish()
    K.backpack(p, b, HAIR_L, HAIR)
    K.hair_back(p, b, 'short')
    draw_legs(p, b, pants=CB, shoes=CB_S, style='pants')
    draw_torso(p, b, CA)
    K.collar(p, b, WHITE)
    # jacket zip
    p.fill(rect(b.cx - .5, b.neck + 3, b.cx, b.waist), WHITE, 'zip', flat=True)
    p.line['zip'] = None
    draw_head(p, b)
    draw_face(p, b, pose.get('face', 'smile'))
    K.hair_front(p, b, 'swoop')
    K.cap_hat(p, b, AC, AC_S, WHITE)
    for side, key in ((-1, 'L'), (1, 'R')):
        ang, bend = pose[key]
        draw_arm(p, b, side, ang, bend, sleeve=CA, sleeve_len='short', hand=SKIN)
    return p.finish()


def player_back(frame):
    pose = {'IDLE': dict(L=(10, 6), R=(10, 6)),
            'BREATH': dict(L=(8, 4), R=(8, 4), breath=1),
            'WINDUP': dict(L=(30, 10), R=(100, -40), lantern='R'),
            'THROW': dict(L=(20, 10), R=(170, -20), hop=1)}[frame]
    return _player(pose, back=True)


# ---------------------------------------------------------------- the cast

ALL_SKINS = ('pale', 'light', 'golden', 'tan', 'brown', 'deep')
NATURAL = ('ink', 'cocoa', 'chestnut', 'ginger', 'honey')
FANCY = ('rose', 'teal', 'lilac', 'moss')


def arch(key, title, blurb, look, pools, **spec):
    spec.update(key=key, title=title, blurb=blurb, look=look, pools=pools)
    return spec


ARCHETYPES = [
    arch('SPROUT', 'Bug-net kid', 'meadow and forest paths; swings a net at anything that buzzes',
         dict(skin='light', hair='chestnut', a='sun', b='leaf', acc='wood'),
         dict(hair=NATURAL, a=('sun', 'sky', 'red', 'orange', 'mint'), b=('leaf', 'navy', 'brown', 'pine')),
         kind='kid', hair='spiky', hairback='short', shirt=CA, sleeve=('short', CA),
         legs=('shorts', CB, CB_S, WHITE), prop='net', prop_hand='R', flair='raise',
         head=[lambda p, b: K.cap_hat(p, b, CB, CB_S, WHITE)]),
    arch('BLOSSOM', 'Flower picker', 'meadows and the farm; a basket of blossoms and a big sun hat',
         dict(skin='pale', hair='honey', a='pink', b='cream', acc='straw'),
         dict(hair=NATURAL + ('rose',), a=('pink', 'sky', 'mint', 'sun', 'plum'), b=('cream', 'pink', 'mint')),
         kind='teen', hair='straight', hairback='bob', shirt=CA, sleeve=('short', CA), flare=1,
         legs=('bare', CA, CA_S, WHITE), prop='basket', prop_hand='L', flair='peace', eyes='big',
         over=[lambda p, b: K.skirt(p, b, CA, 4, 7), lambda p, b: K.collar(p, b, CB)],
         head=[lambda p, b: K.sun_hat(p, b, AC, CA, CB, brim_w=19)]),
    arch('ANGLER', 'Angler', 'lakes and piers; waits all day for one good bite',
         dict(skin='tan', hair='cocoa', a='sky', b='pine', acc='wood'),
         dict(hair=NATURAL + ('silver',), a=('sky', 'cream', 'stone', 'sun'), b=('pine', 'brown', 'navy', 'leaf')),
         kind='adult', hair='short', hairback='short', shirt=CA, sleeve=('short', CA), eyes='sleepy',
         legs=('pants', CB_S, CB_S), prop='rod', prop_hand='R', flair='point',
         over=[lambda p, b: K.vest(p, b, CB)],
         head=[lambda p, b: K.bucket_hat(p, b, CB, CA)]),
    arch('HIKER', 'Hiker', 'mountain roads and caves; carries a pack bigger than some kin',
         dict(skin='golden', hair='chestnut', a='red', b='brown', acc='leather'),
         dict(hair=NATURAL + ('silver',), a=('red', 'orange', 'sun', 'leaf', 'sky'), b=('brown', 'navy', 'pine', 'coal')),
         kind='big', hair='short', hairback='short', shirt=CA, sleeve=('long', CA), eyes='dot',
         legs=('pants', CB, AC_S), flair='flex',
         back=[lambda p, b: K.backpack(p, b, AC, CB, big=True)],
         head=[lambda p, b: K.beard(p, b), lambda p, b: K.beanie(p, b, CA, CA_S, WHITE)]),
    arch('FARMER', 'Farmhand', 'fields and orchards; smells of hay and sweet berries',
         dict(skin='tan', hair='ginger', a='red', b='sky', acc='straw'),
         dict(hair=NATURAL, a=('red', 'leaf', 'cream', 'sun'), b=('sky', 'navy', 'brown')),
         kind='adult', hair='parted', hairback='short', shirt=CA, sleeve=('short', CA),
         legs=('pants', CB, CB_S), prop='fork', prop_hand='R', flair='wave',
         over=[lambda p, b: K.overall_bib(p, b, CB, AC)],
         head=[lambda p, b: K.straw_hat(p, b)]),
    arch('SWIMMER', 'Swimmer', 'beaches and the coast road; never without a float ring',
         dict(skin='brown', hair='ink', a='sky', b='red', acc='white'),
         dict(hair=NATURAL + FANCY, a=('sky', 'red', 'sun', 'pink', 'mint', 'plum'), b=('red', 'sun', 'sky')),
         kind='teen', hair='swoop', hairback='ponytail', shirt=CA, sleeve=('none', CA),
         legs=('bare', CA, CB), prop='floatie', prop_hand='L', flair='cheer', eyes='big',
         over=[lambda p, b: K.swimsuit(p, b, CA, WHITE)],
         head=[lambda p, b: K.goggles(p, b, CB, WHITE)]),
    arch('SCHOLAR', 'Scholar', 'libraries and old ruins; has read about your kin, twice',
         dict(skin='pale', hair='ink', a='navy', b='cream', acc='gold'),
         dict(hair=NATURAL + ('lilac', 'silver'), a=('navy', 'plum', 'pine', 'brown'), b=('cream', 'stone', 'sky')),
         kind='teen', hair='parted', part=-3, hairback='short', shirt=CB, sleeve=('long', CA),
         legs=('pants', CA_S, CA_S), prop='book', prop_hand='L', flair='think', glasses=True,
         over=[lambda p, b: K.robe(p, b, CA, None, b.feet - 5), lambda p, b: K.collar(p, b, CB)],
         cuff=CB),
    arch('TINKER', 'Tinkerer', 'cities and the Clockwork works; oil on the cheek, spark in the eye',
         dict(skin='golden', hair='ginger', a='stone', b='brown', acc='steel'),
         dict(hair=NATURAL + FANCY, a=('stone', 'sky', 'orange', 'coal'), b=('brown', 'navy', 'coal')),
         kind='teen', hair='spiky', hairback='short', shirt=CA, sleeve=('short', CA),
         legs=('pants', CB, CB_S), prop='wrench', prop_hand='R', flair='hips', eyes='sharp',
         over=[lambda p, b: K.apron(p, b, CB, bib=True), lambda p, b: K.belt(p, b, AC_S, AC)],
         head=[lambda p, b: K.goggles(p, b, AC, WHITE)]),
    arch('SNOWBELL', 'Snow kid', 'the frozen north; bundled up so only the cheeks show',
         dict(skin='pale', hair='cocoa', a='sky', b='red', acc='white'),
         dict(hair=NATURAL, a=('sky', 'pink', 'mint', 'sun', 'plum'), b=('red', 'navy', 'sun', 'pink')),
         kind='kid', hair='straight', shirt=CA, sleeve=('long', CA), glove=CB, eyes='big',
         legs=('pants', CA, CB), flair='cheer',
         back=[lambda p, b: K.hood(p, b, CA, WHITE)],
         post=[lambda p, b: K.scarf(p, b, CB, WHITE)]),
    arch('MINER', 'Miner', 'caves and quarries; the lamp on the helmet never goes out',
         dict(skin='tan', hair='cocoa', a='orange', b='navy', acc='gold'),
         dict(hair=NATURAL + ('silver',), a=('orange', 'sun', 'red'), b=('navy', 'brown', 'coal', 'stone')),
         kind='big', hair='short', shirt=CA, sleeve=('short', CA), eyes='dot',
         legs=('pants', CB, AC_S), prop='pick', prop_hand='R', flair='flex',
         over=[lambda p, b: K.overall_bib(p, b, CB, AC)],
         head=[lambda p, b: K.helmet_lamp(p, b, AC, WHITE)]),
    arch('HEXLING', 'Hexling', 'the grim moors; brews tea that tastes of thunder',
         dict(skin='pale', hair='lilac', a='plum', b='coal', acc='violet'),
         dict(hair=('ink', 'lilac', 'rose', 'teal', 'silver', 'ginger'), a=('plum', 'coal', 'navy', 'pine'),
              b=('coal', 'plum', 'sun')),
         kind='teen', hair='straight', hairback='long', shirt=CA, sleeve=('long', CA), eyes='sharp',
         legs=('bare', CB, CB, CB), prop='broom', prop_hand='L', flair='point', prop_behind=True,
         over=[lambda p, b: K.robe(p, b, CA, CB, b.feet - 4)],
         head=[lambda p, b: K.witch_hat(p, b, CA, CB)]),
    arch('MYSTIC', 'Mystic', 'dream temples; hums a note that makes kin sleepy',
         dict(skin='brown', hair='ink', a='sun', b='red', acc='wood'),
         dict(hair=('ink', 'silver', 'cocoa'), a=('sun', 'orange', 'mint', 'sky'), b=('red', 'plum', 'navy')),
         kind='adult', hair='short', hairback='bun', shirt=CA, sleeve=('long', CA), eyes='sleepy',
         legs=('bare', CA, CB), prop='beads', prop_hand='L', flair='bow',
         over=[lambda p, b: K.robe(p, b, CA, CB), lambda p, b: K.shawl(p, b, CB)]),
    arch('SMITH', 'Smith', 'forges and volcano towns; arms like anvils, heart like a cinnamon bun',
         dict(skin='deep', hair='ink', a='red', b='stone', acc='steel'),
         dict(hair=NATURAL, a=('red', 'orange', 'sky', 'sun'), b=('stone', 'brown', 'cream')),
         kind='big', hair='short', hairback='short', shirt=CA, sleeve=('none', CA), eyes='sharp',
         legs=('pants', CA, CB_S), prop='hammer', prop_hand='R', flair='flex',
         over=[lambda p, b: K.apron(p, b, CB, bib=True)],
         head=[lambda p, b: K.headband(p, b, CA)]),
    arch('SENTINEL', 'Sentinel', 'city gates and the throne road; very serious, very small',
         dict(skin='light', hair='honey', a='red', b='navy', acc='steel'),
         dict(hair=NATURAL + ('silver',), a=('red', 'sky', 'leaf', 'plum', 'sun'), b=('navy', 'coal', 'brown')),
         kind='teen', hair='straight', shirt=CA, sleeve=('long', CB), glove=AC,
         legs=('pants', CB, AC_S), prop='shield', prop_hand='L', flair='salute', brows='fierce',
         over=[lambda p, b: K.breastplate(p, b, AC)],
         head=[lambda p, b: K.knight_helm(p, b, AC, CA)],
         post=[lambda p, b: K.pauldrons(p, b, AC)]),
    arch('IDOL', 'Idol', 'town squares and festivals; sings to her kin before every bout',
         dict(skin='golden', hair='rose', a='pink', b='sky', acc='gold'),
         dict(hair=('rose', 'teal', 'lilac', 'honey', 'ink', 'moss'), a=('pink', 'sky', 'mint', 'plum', 'sun'),
              b=('sky', 'pink', 'cream', 'mint')),
         kind='teen', hair='straight', hairback='twintails', shirt=CA, sleeve=('short', CA), eyes='big',
         legs=('bare', CB, CA, WHITE), prop='mic', prop_hand='R', flair='peace',
         over=[lambda p, b: K.skirt(p, b, CB, 5, 6), lambda p, b: K.collar(p, b, WHITE)],
         head=[lambda p, b: K.bow_ribbon(p, b, CB, 'side')]),
    arch('COOK', 'Cook', 'inns and market stalls; brings snacks for your kin, not for you',
         dict(skin='light', hair='chestnut', a='cream', b='red', acc='steel'),
         dict(hair=NATURAL + ('silver',), a=('cream',), b=('red', 'sky', 'leaf', 'coal', 'sun')),
         kind='adult', hair='short', hairback='short', shirt=CA, sleeve=('short', CA),
         legs=('pants', CB, CB_S), prop='spoon', prop_hand='R', flair='wave',
         over=[lambda p, b: K.apron(p, b, WHITE, bib=True), lambda p, b: K.scarf(p, b, CB, CB)],
         head=[lambda p, b: K.toque(p, b, WHITE)]),
    arch('SAILOR', 'Deckhand', 'ships and harbours; salty, sunny, loud',
         dict(skin='tan', hair='honey', a='cream', b='navy', acc='steel'),
         dict(hair=NATURAL + ('teal',), a=('cream', 'sky'), b=('navy', 'red', 'sky')),
         kind='teen', hair='swoop', hairback='short', shirt=CA, sleeve=('short', CA),
         legs=('pants', CB, CB_S), prop='anchor', prop_hand='L', flair='salute',
         over=[lambda p, b: K.sailor_collar(p, b, CB, CA, 6)],
         head=[lambda p, b: K.sailor_hat(p, b, WHITE, CB)]),
    arch('RANGER', 'Ranger', 'deep forests; knows every kin by its footprints',
         dict(skin='brown', hair='ink', a='pine', b='brown', acc='gold'),
         dict(hair=NATURAL + ('moss',), a=('pine', 'leaf', 'brown', 'orange'), b=('brown', 'pine', 'navy')),
         kind='adult', hair='swoop', hairback='ponytail', shirt=CA, sleeve=('long', CA), eyes='sharp',
         legs=('pants', CB, CB_S), prop='binoculars', prop_hand='L', flair='point',
         over=[lambda p, b: K.belt(p, b, CB_S, AC)],
         head=[lambda p, b: K.ranger_hat(p, b, CA, CB, AC)]),
    arch('ELDER', 'Elder', 'villages everywhere; has seen three Brimming Storms and won a bout in each',
         dict(skin='light', hair='silver', a='plum', b='cream', acc='wood'),
         dict(hair=('silver',), a=('plum', 'pine', 'navy', 'brown', 'red'), b=('cream', 'pink', 'mint')),
         kind='elder', hair='straight', hairback='bun', shirt=CA, sleeve=('long', CA), eyes='sleepy',
         legs=('bare', CA, AC_S), prop='cane', prop_hand='L', flair='think',
         over=[lambda p, b: K.robe(p, b, CA, None), lambda p, b: K.shawl(p, b, CB)]),
    arch('MASTER', 'Hall Master', 'a Hearth Hall\'s keeper; the cape colour tells you which Hall',
         dict(skin='golden', hair='ink', a='red', b='sun', acc='gold'),
         dict(hair=NATURAL + FANCY + ('silver',), a=('red', 'navy', 'pine', 'plum', 'coal', 'sky'),
              b=('sun', 'cream', 'mint', 'pink')),
         kind='adult', hair='swoop', hairback='long', shirt=CB, sleeve=('long', CA), eyes='sharp',
         legs=('pants', CA_S, CA_S), prop='staff', prop_hand='L', flair='raise', brows='fierce',
         back=[lambda p, b: K.cape(p, b, CA, CB)],
         over=[lambda p, b: K.belt(p, b, AC_S, AC), lambda p, b: K.collar(p, b, CA)],
         head=[lambda p, b: K.circlet(p, b, AC, CA)]),
]
