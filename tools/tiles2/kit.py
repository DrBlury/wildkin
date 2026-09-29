"""Standard entry groups shared by the area sets.

Each helper adds a family of entries to a Sheet with consistent names, so
every area exposes the same vocabulary (grass/grass_b..., path, water,
cliff_top/cliff_face/ledge/stairs, forest...) and the map designer can
move between areas without relearning the catalogue. Prefixes keep
several families apart inside one sheet (e.g. 'sand_' on the coast).
"""

import paint as P
import terrain as T
import flora as F
import props as PR


def grass_family(S, prefix, R, seeds=(1, 2, 3, 4), flowers=None, pebbles=None, doc='grass',
                 attrs=(), tufts=(3, 5, 2, 4)):
    """Four textured variants (+ optional flower / pebble variants) in one
    random group named `prefix`. Returns the main variant image."""
    imgs = [P.grass(R, seeds[0], tufts=tufts[0], flecks=2),
            P.grass(R, seeds[1], tufts=tufts[1], flecks=3),
            P.grass(R, seeds[2], tufts=tufts[2], flecks=4),
            P.grass(R, seeds[3], tufts=tufts[3], flecks=1)]
    weights = (9, 4, 3, 3)
    for i, (img, wt) in enumerate(zip(imgs, weights)):
        n = prefix if i == 0 else '%s_%s' % (prefix, 'bcd'[i - 1])
        S.tile(n, img, group=prefix, weight=wt, attrs=list(attrs), doc=doc if i == 0 else '')
    if flowers:
        S.tile(prefix + '_flowers', P.grass(R, seeds[0] + 10, tufts=2, flecks=2, flowers=flowers),
               group=prefix, weight=1, attrs=list(attrs), doc=doc + ' with tiny flowers')
    if pebbles:
        S.tile(prefix + '_pebbles', P.grass(dict(R, **pebbles), seeds[0] + 20, tufts=2, flecks=2, pebbles=2),
               group=prefix, weight=1, attrs=list(attrs), doc=doc + ' with pebbles')
    return imgs[0]


def speckle_family(S, prefix, R, seeds=(5, 8, 9), doc='ground', attrs=(), dots=(8, 10, 6),
                   pebbles=(1, 2, 0), cracks=(0, 0, 1), grain=0.0, weights=(6, 3, 1)):
    imgs = []
    for i, sd in enumerate(seeds):
        img = P.speckle_ground(R, sd, dots=dots[i % len(dots)], pebbles=pebbles[i % len(pebbles)],
                               cracks=cracks[i % len(cracks)], grain=grain)
        n = prefix if i == 0 else '%s_%s' % (prefix, 'bcdefg'[i - 1])
        S.tile(n, img, group=prefix, weight=weights[i % len(weights)], attrs=list(attrs),
               doc=doc if i == 0 else '')
        imgs.append(img)
    return imgs


def path(S, name, inner, outer, rim_in, rim_out, lip, over, doc, inner_alt=None, seed=2, attrs=(),
         E=4.0, amp=0.8, R=4.5):
    S.autotile(name, T.material_autotile(inner, outer, rim_in=rim_in, rim_out=rim_out, lip=lip,
                                         seed=seed, inner_alt=inner_alt, E=E, amp=amp, R=R),
               over=over, attrs=list(attrs), doc=doc)


def water(S, W, ground, edge, wet, over, name='water', deep=True, doc=None, period=20, calm=False):
    wf = [T.water_autotile(W, ground, f, edge=edge, wet=wet) for f in range(4)]
    S.autotile(name, wf[0], frames=wf, over=over, attrs=['WATER'], period=period,
               doc=doc or 'water over %s (4-frame ripples)' % over)
    if deep:
        D = dict(W, base=W['deep'], deep=W['dark'], lt=W['base'], hi=W['lt'])
        fr = [T.material_autotile(T.water_surface(D, f, seed=5), T.water_surface(W, f),
                                  rim_in=W['dark'], rim_out=W['lt'], seed=7, E=3.0, amp=1.2, dither=0.0)
              for f in range(4)]
        S.autotile('deep_' + name, fr[0], frames=fr, over=name, attrs=['WATER', 'DEEP'], period=period,
                   doc='deep channel inside ' + name)
    return wf


def cliffs(S, rock, outline, top, low, bevel, drip, tufts, ledge_profile, stairs_roles=None,
           prefix='', lump=None, seed=1, doc_face='cliff face (>= 2 rows: top, middle..., foot)',
           face_tex=None, face_tex2=None):
    """cliff_top (plateau rim autotile), cliff_face (patch9), ledge block,
    stairs. rock: 5 roles dark -> light."""
    lk = dict(rx=5.5, ry=4.2, sx=8, sy=6.5)
    lk.update(lump or {})
    face = face_tex or T.lump_texture(rock, 32, 32, seed, **lk)
    face2 = face_tex2 or face_tex or T.lump_texture(rock, 32, 32, seed + 8, **lk)
    S.autotile(prefix + 'cliff_top', T.cliff_rim(top, low, rock, outline, face_tex=face, bevel=bevel,
                                                  drip=drip),
               over=None, doc='upper level of a plateau; its south side flows into %scliff_face' % prefix)
    S.patch9(prefix + 'cliff_face', T.cliff_face(rock, outline, low, tufts=tufts, tex=face, tex2=face2),
             attrs=['SOLID'], doc=doc_face)
    S.custom(prefix + 'cliff_face_single', T.cliff_face_single(rock, outline, low, face, tufts=tufts), 'strip4',
             attrs=['SOLID'], doc='one-row face (a single level of drop): [W end][mid][E end][lone]')
    S.custom(prefix + 'ledge', T.ledge_block(low, ledge_profile), 'ledge', attrs=['LEDGE'],
             doc='one-way ledges: row 0 south [W end][mid][E end][single], row 1 east-facing '
                 '[N end][mid][S end][SE corner], row 2 west-facing')
    if stairs_roles:
        hi, mid, riser, out, side = stairs_roles
        S.object(prefix + 'stairs', T.stairs(hi, mid, riser, out, side, 1, 2), solid='./.', layer='ground',
                 doc='steps cut into a 2-row face')
        S.object(prefix + 'stairs_wide', T.stairs(hi, mid, riser, out, side, 2, 2), solid='../..',
                 layer='ground', doc='wide steps')
    return face


def waterfall(S, W, rock, name='waterfall', w=2, h=3):
    fall = [T.waterfall(W, rock, f, w=w, h=h) for f in range(4)]
    S.object(name, fall[0], frames=fall, period=8, solid='/'.join(['X' * w] * h), layer='ground',
             attrs=['WATER'], doc='%dx%d falls; the bottom row foams into the pool' % (w, h))


def broadleaf(S, leaf, out, bark, bark_out, prefix='', fruit=None, seeds=(3, 8, 4, 5, 6), big=True,
              forest=True, forest_seed=1, doc='broadleaf'):
    S.object(prefix + 'tree', F.round_tree('mid', leaf, out, bark, bark_out, seed=seeds[0]),
             top='XX/..', solid='../XX', doc='%s tree 2x2; crown above people' % doc)
    S.object(prefix + 'tree_b', F.round_tree('mid', leaf, out, bark, bark_out, seed=seeds[1]),
             top='XX/..', solid='../XX')
    S.object(prefix + 'tree_small', F.round_tree('small', leaf, out, bark, bark_out, seed=seeds[2]),
             top='X/.', solid='./X', doc='young %s 1x2' % doc)
    if big:
        S.object(prefix + 'tree_big', F.round_tree('big', leaf, out, bark, bark_out, seed=seeds[3]),
                 top='XXX/XXX/...', solid='.../.../XXX', doc='elder %s 3x3' % doc)
    if fruit:
        S.object(prefix + 'tree_fruit', F.round_tree('mid', leaf, out, bark, bark_out, seed=seeds[4],
                                                     fruit=fruit), top='XX/..', solid='../XX',
                 doc='fruiting tree 2x2 (interact)')
    if forest:
        S.patch9(prefix + 'forest', F.forest_wall(leaf, out, bark, bark_out, seed=forest_seed),
                 layer='mid', attrs=['SOLID'], doc='dense %s woods (mass layer; trunks on the south edge)' % doc)


def conifers(S, leaf, out, bark, bark_out, prefix='', snow=None, forest=True, doc='pine'):
    S.object(prefix + 'pine', F.conifer(32, 48, leaf, out, bark, bark_out, seed=2, tiers=5, snow=snow),
             top='XX/XX/..', solid='../../XX', doc='tall %s 2x3' % doc)
    S.object(prefix + 'pine_small', F.conifer(16, 32, leaf, out, bark, bark_out, seed=3, tiers=4, snow=snow),
             top='X/.', solid='./X', doc='young %s 1x2' % doc)
    if forest:
        S.patch9(prefix + 'pine_forest', F.forest_wall(leaf, out, bark, bark_out, seed=2, r=6.4, snow=snow),
                 layer='mid', attrs=['SOLID'], doc='dense %s woods' % doc)


def rocks(S, stone, out, prefix='', moss=None, rune=None):
    S.object(prefix + 'rock', PR.small_rock(stone, out, 1), doc='small rock')
    S.object(prefix + 'boulder', PR.boulder(stone, out, 2), doc='push boulder (strength)')
    S.object(prefix + 'rock_cracked', PR.cracked_rock(stone, out, 3), doc='breakable rock')
    S.object(prefix + 'rock_big', PR.big_rock(stone, out, 4, moss=moss), doc='crag 2x2')
    S.object(prefix + 'pebbles', PR.pebbles(stone, out, 5), solid='.', doc='pebbles (decor)')
    S.object(prefix + 'standing_stone', PR.standing_stone(stone, out, seed=6, moss=moss), top='X/.',
             solid='./X', doc='menhir 1x2')
    if rune:
        S.object(prefix + 'rune_stone', PR.standing_stone(stone, out, seed=7, rune=rune), top='X/.',
                 solid='./X', doc='rune stone 1x2')


# ---------------------------------------------------------------------------
# shared outdoor props and civic buildings
# ---------------------------------------------------------------------------

def outdoor(S, R, only=None, skip=()):
    """Common outdoor furniture (old TW decor kinds). R roles:
    wood [4 dark->light], out, stone [5], stone_out, metal [3], red, yellow,
    orange, white, cloth [3], roof [3], hay [3], glow [2], leaf [4]."""
    import extras as X
    import townprops as TP
    import farmart as FA
    import coastart as CO
    wood, out = R['wood'], R['out']
    items = [
        ('crate_stack', lambda: X.crate_stack(wood, out), dict(top='X/.', solid='./X', doc='stacked crates 1x2')),
        ('lantern_post', lambda: TP.lamp_post(R['metal'], out, [R['orange'], R['orange'], R['yellow']]),
         dict(top='X/.', solid='./X', doc='lantern post 1x2')),
        ('stone_lantern', lambda: X.stone_lantern(R['stone'][:3], R['glow'], R['stone_out']),
         dict(top='X/.', solid='./X', doc='stone lantern 1x2')),
        ('flag', None, dict(top='X/.', solid='./X', doc='flag on a pole 1x2 (waves)')),
        ('woodpile', lambda: TP.woodpile(wood, wood[1:], out), dict(doc='firewood 2x1')),
        ('hay_bale', lambda: FA.hay_bale(R['hay'], out, wood[0]), dict(doc='hay bales 2x1')),
        ('picnic_table', lambda: X.picnic_table(wood[1:], out), dict(top='XX/..', solid='../XX', doc='picnic table 2x2')),
        ('wheelbarrow', lambda: X.wheelbarrow(wood[1:], R['metal'], out, load=R['hay']), dict(doc='wheelbarrow')),
        ('shrine', lambda: X.shrine(wood[1:], R['roof'], R['stone'][:3], R['red'], out),
         dict(top='XX/..', solid='../XX', doc='wayside shrine 2x2')),
        ('telescope', lambda: X.telescope(R['metal'], wood[1:], out), dict(top='X/.', solid='./X',
                                                                           doc='telescope on a tripod 1x2')),
        ('rain_gauge', lambda: X.rain_gauge(R['metal'], R['white'], R['stone'][2], out), dict(doc='rain gauge')),
        ('cart', lambda: TP.cart(wood, [wood[0], wood[2]], out, load=[R['hay']]), dict(doc='hand cart 2x1')),
        ('scarecrow', lambda: FA.scarecrow(wood, R['cloth'], R['cloth'], R['hay'][2], R['hay'][1], out),
         dict(top='X/.', solid='./X', doc='scarecrow 1x2')),
        ('beehive', lambda: FA.beehive(wood[1:], R['stone'][:3], out, R['yellow']), dict(doc='beehive')),
        ('small_flowers', lambda: X.small_flowers([R['red'], R['yellow'], R['white']], R['leaf'][1]),
         dict(solid='.', doc='sprinkle of tiny flowers (decor)')),
        ('fallen_leaves', lambda: X.fallen_leaves([R['orange'], R['red'], R['yellow']]), dict(solid='.',
                                                                                            doc='fallen leaves (decor)')),
        ('rowboat', lambda: CO.rowboat(wood, out, wood[0]), dict(solid='..', doc='rowboat 2x1 (on water)')),
        ('old_hearth', lambda: X.old_hearth(R['stone'][:3], [R['stone_out'], R['stone'][0]], R['stone_out']),
         dict(solid='../..', doc='ruined hearth 2x2 (walkable)')),
        ('stag_altar', lambda: X.stag_altar(R['stone'][:3], [wood[0], wood[2], R['white']], R['stone_out']),
         dict(top='XX/..', solid='../XX', doc='antlered altar 2x2')),
    ]
    for name, fn, kw in items:
        if (only and name not in only) or name in skip:
            continue
        if name == 'flag':
            fr = [X.flag(R['metal'], R['cloth'], out, f) for f in range(3)]
            S.object('flag', fr[0], frames=fr, period=12, **kw)
            continue
        S.object(name, fn(), **kw)


def civic(S, st, emblem, prefix='', roof_style='shingle', siding='plaster', sign=None, skip=(), door_w=14,
          storeys=2, chimney=True):
    """Hearth Hall (flame plate), shop (awning), inn and a hall for an area,
    all in the area's building style st (see buildings.house)."""
    import buildings as B
    if 'hearth_hall' not in skip:
        hall = B.house(96, 80, st, door_at=48, windows=[(10, 6), (74, 6), (10, 22), (74, 22)], roof_style=roof_style,
                       siding=siding, beams=True, storeys=2, door_w=door_w, roof_h=40, sign=(40, 8, 16, 8),
                       chimney=12 if chimney else None)
        B.flame_emblem(*emblem)(hall, 48, 52)
        S.object(prefix + 'hearth_hall', hall, doc='Hearth Hall 6x5 (flame plate over the door)',
                 extra={'door': [3, 4]})
    if 'shop' not in skip:
        R = st['roof']
        S.object(prefix + 'shop', B.house(80, 64, st, door_at=40, windows=[(6, 8), (62, 8)], roof_style=roof_style,
                                          siding=siding, awning=(24, 55, [R[1], st['wall'][2], R[3]])),
                 doc='provisions shop 5x4 (awning)', extra={'door': [2, 3]})
    if 'inn' not in skip:
        S.object(prefix + 'inn', B.house(112, 80, st, door_at=40, windows='auto', roof_style=roof_style,
                                         siding=siding, storeys=storeys, beams=True, chimney=90 if chimney else None,
                                         sign=(60, 10, 20, 8)),
                 doc='inn 7x5', extra={'door': [2, 4]})
    if 'hall' not in skip:
        S.object(prefix + 'hall', B.house(128, 96, st, door_at=64, windows='auto', roof_style=roof_style,
                                          siding=siding, storeys=2, door_w=20, beams=True),
                 doc='town hall / guild hall 8x6', extra={'door': [4, 5]})
