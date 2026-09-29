"""Shared pieces for the engine art modules (engine/art_<set>.py)."""

from core import Img
import flora as F
import terrain as T

from .load import over, tile, minus


def on_ground(img, ground):
    """An object image over tiled opaque ground."""
    return over(tile(ground, img.w, img.h), img)


def over_tiled(img, ground):
    return over(tile(ground, img.w, img.h), img)


def cell_of(img, cx, cy):
    return img.crop(cx * 16, cy * 16, 16, 16)


# ---------------------------------------------------------------------------
# masses
# ---------------------------------------------------------------------------

NB = ((0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1))


def grid_mask(mask):
    """Neighbour bit mask -> mask(cx, cy) on a 3x3 grid (centre (1, 1))."""
    on = {(1, 1)}
    for i, (dx, dy) in enumerate(NB):
        if mask & (1 << i):
            on.add((1 + dx, 1 + dy))
    return lambda cx, cy: (cx, cy) in on


def forest_render(k, leaf, leaf_out, bark, bark_out, seed=1, r=7.2, snow=None, trunks=True, lone=None):
    """fn(mask) -> 48x48 Img (colour names): the forest canopy of a cell
    (centre) with the given neighbours, drawn like tiles2 forest_wall.
    lone: a 16x32 tree for a lone pair (a crown cell whose only neighbour
    is the trunk cell below, and that trunk cell): maps plant single trees
    as TREE_TOP over TREE_BOTTOM. Default: tiles2's young round tree."""
    if lone is None and trunks:
        lone = k.paint(F.round_tree('small', leaf, leaf_out, bark, bark_out, seed=seed + 3))

    def render(mask):
        if lone is not None and mask in (16, 1):
            img = Img(48, 48)
            img.paste(lone.crop(0, 0 if mask == 16 else 16, 16, 16), 16, 16)
            return img
        img = F.lattice_render(grid_mask(mask), 48, 48, leaf, leaf_out, seed, r=r,
                               bottom='trunks' if trunks else None,
                               trunks=(bark, bark_out) if trunks else None, snow=snow)
        return k.paint(img)
    return render


def forest_mass(render, top='TREE_TOP', bottom='TREE_BOTTOM'):
    return {'render': render, 'layer': {top: 'top', bottom: 'mid'}}


def hedge_piece(k, leaf, leaf_out, seed, base, cells):
    """One 16x16 hedge cell: cells = set of (dx, dy) neighbours that are
    hedge too (the centre is always hedge)."""
    on = {(1, 1)} | {(1 + dx, 1 + dy) for (dx, dy) in cells}

    def mask(cx, cy):
        return (cx, cy) in on
    img = F.lattice_render(mask, 48, 48, leaf, leaf_out, seed, period=16, r=4.6, ry=4.6 * 0.85,
                           centers=((4, 4.5), (12, 4.5), (0, 11.5), (8, 11.5)), lobes=2)
    if base:
        for y in range(47):
            for x in range(48):
                if img.p[y][x] is not None and img.p[y + 1][x] is None and not mask(x // 16, (y + 1) // 16):
                    img.p[y][x] = base
    return k.paint(img).crop(16, 16, 16, 16)


# ---------------------------------------------------------------------------
# elevation
# ---------------------------------------------------------------------------

def shadow(role):
    img = Img(16, 16)
    for y in range(16):
        for x in range(3):
            if (x + y) % 2 == 0 or x == 0:
                img.p[y][x] = role
    return img


def mouth(face_cell, dark, rim):
    img = face_cell.copy()
    for y in range(3, 16):
        for x in range(2, 14):
            dx = (x + 0.5 - 8) / 5.8
            dy = (y + 0.5 - 16) / 12.5
            d = dx * dx + dy * dy
            if d < 1.0:
                img.p[y][x] = dark
            elif d < 1.35:
                img.p[y][x] = rim
    return img


def elev(k, ground, stairs_roles, face_prefix='', deck=('bridge_h', 'bridge_v'), rock_out='r0', rock_dk='r1',
         deck_imgs=None):
    """ElevArt pieces from a set's cliff entries (docs/TILES2.md 4.6).
    ground: the high/low ground tile the rim is drawn over.
    stairs_roles: (step_hi, step, riser, outline, side) for T.stairs."""
    p = face_prefix
    rim = minus(k.img(p + 'cliff_top'), ground)
    face9 = k.img(p + 'cliff_face')
    face1 = k.img(p + 'cliff_face_single')
    hi, mid, riser, out, side = stairs_roles
    st = k.paint(T.stairs(hi, mid, riser, out, side, 1, 1))
    st = over(Img(16, 16), st)
    stw = st.rot90()
    ste = stw.flip_h()
    ledge = minus(k.cells(p + 'ledge', 0, 0, 4, 1), ground)
    if deck_imgs:
        dh, dv = deck_imgs
    else:
        dh = k.img(deck[0]) if k.has(deck[0]) else None
        dv = k.img(deck[1]) if k.has(deck[1]) else None
    return {'rim': rim, 'face9': face9, 'face1': face1, 'stairs': [st, st, stw, ste],
            'deck_h': dh, 'deck_v': dv,
            'mouth': mouth(cell_of(face1, 1, 0), k.role(rock_out), k.role(rock_dk)),
            'ledge': ledge, 'shadow': shadow(k.role(rock_out))}


# ---------------------------------------------------------------------------
# bridges as single cells (old BRIDGE_H / BRIDGE_V decor tile along a span)
# ---------------------------------------------------------------------------

def bridge_cell_h(bh):
    """48x32 E-W bridge -> one 16x16 cell with both railings."""
    img = Img(16, 16)
    img.paste(bh.crop(16, 0, 16, 8), 0, 0)
    img.paste(bh.crop(16, 24, 16, 8), 0, 8)
    return img


def bridge_cell_v(bv):
    img = Img(16, 16)
    img.paste(bv.crop(0, 16, 8, 16), 0, 0)
    img.paste(bv.crop(24, 16, 8, 16), 8, 0)
    return img


# ---------------------------------------------------------------------------
# decor tables
# ---------------------------------------------------------------------------

def _fit(img, w, h, align='bottom'):
    """Place a smaller image into a w x h cell footprint (bottom, centred
    horizontally on the 8 px grid)."""
    if (img.w, img.h) == (w * 16, h * 16):
        return img
    if img.w > w * 16 or img.h > h * 16:
        return None
    out = Img(w * 16, h * 16)
    ox = ((w * 16 - img.w) // 2) // 8 * 8
    oy = h * 16 - img.h if align == 'bottom' else 0
    out.paste(img, ox, oy)
    return out


def decor_table(k, kinds, table):
    """kinds: [(name, w, h)] the set must provide; table: {kind: spec}.
    spec: 'entry' (same size, or smaller: padded into the footprint),
    'entry@cx,cy' (the footprint cropped from cell cx, cy of the entry),
    an Img, a list of frames or (frames, period). Unlisted kinds try their
    lower-case name. Raises one error listing every problem."""
    out, bad = {}, []
    for (name, w, h) in kinds:
        spec = table.get(name, name.lower())
        if not isinstance(spec, str):
            out[name] = spec
            continue
        ent, at = spec, None
        if '@' in spec:
            ent, at = spec.split('@')
            at = tuple(int(v) for v in at.split(','))
        if not k.has(ent):
            bad.append('%s: no entry %r' % (name, ent))
            continue
        ew, eh = k.size(ent)
        n = k.nframes(ent)
        frames = []
        for f in range(n):
            if at:
                if at[0] + w > ew or at[1] + h > eh:
                    bad.append('%s: %s@%s outside %dx%d' % (name, ent, at, ew, eh))
                    break
                frames.append(k.cells(ent, at[0], at[1], w, h, f))
            else:
                im = _fit(k.img(ent, f), w, h)
                if im is None:
                    bad.append('%s (%dx%d): %s is %dx%d' % (name, w, h, ent, ew, eh))
                    break
                frames.append(im)
        else:
            per = k.entry(ent).get('period') or 16
            out[name] = (frames, per) if n > 1 else frames[0]
    if bad:
        raise ValueError('%s decor:\n  ' % k.name + '\n  '.join(bad))
    return out


def blend_block(k, inner, outer, rim_in=None, rim_out=None, lip=None, seed=2, **kw):
    """rmxp16 block of ground `inner` laid over ground `outer` (16x16 each)."""
    return k.paint(T.material_autotile(inner, outer, rim_in=rim_in, rim_out=rim_out, lip=lip, seed=seed, **kw))


def pair(a, b):
    """Two cells side by side (2x1 from two 1x1 images)."""
    img = Img(a.w + b.w, max(a.h, b.h))
    img.paste(a, 0, 0)
    img.paste(b, a.w, 0)
    return img


def at_bottom(img, w, h, ox=0):
    out = Img(w * 16, h * 16)
    out.paste(img, ox, h * 16 - img.h)
    return out


# ---------------------------------------------------------------------------
# buildings in an old stamp's footprint (door cell kept)
# ---------------------------------------------------------------------------

def house(k, st, w, h, door_col, **kw):
    import buildings as B
    kw.setdefault('door_w', 14)
    return k.paint(B.house(w * 16, h * 16, st, door_at=door_col * 16 + 8, **kw))


def hearth(k, st, w, h, door_col, flame, **kw):
    """Hearth Hall with the flame plate on its door: flame = (hot, mid,
    dark) roles from the roof's bank (the door tiles use that bank)."""
    import buildings as B
    kw.setdefault('roof_h', h * 16 // 2 - 2)
    kw.setdefault('beams', True)
    img = B.house(w * 16, h * 16, st, door_at=door_col * 16 + 8, door_w=16, **kw)
    B.flame_emblem(*flame)(img, door_col * 16 + 8, h * 16 - 13)
    return k.paint(img)


# ---------------------------------------------------------------------------
# hand-placed 9-slice pieces cut from an rmxp16 block (old POOL_N, LAVA_SE...)
# ---------------------------------------------------------------------------

SLICE9 = {'': (1, 2), 'N': (1, 1), 'S': (1, 3), 'W': (0, 2), 'E': (2, 2),
          'NW': (0, 1), 'NE': (2, 1), 'SW': (0, 3), 'SE': (2, 3)}


def rmxp_piece(block, kind):
    """16x16 cell of an rmxp16 block: '', N, S, W, E, NW, NE, SW, SE (the
    9-slice), INW/INE/ISW/ISE (filled with one inner corner), H / V (a
    one-cell channel), LONE."""
    if kind in SLICE9:
        cx, cy = SLICE9[kind]
        return block.crop(cx * 16, cy * 16, 16, 16)
    img = block.crop(16, 32, 16, 16)
    if kind in ('INW', 'INE', 'ISW', 'ISE'):
        c = ('INW', 'INE', 'ISW', 'ISE').index(kind)
        qx, qy = (0, 0, 8, 8)[c % 2 * 2], (0, 0, 8, 8)[c // 2 * 2]
        qx, qy = (c % 2) * 8, (c // 2) * 8
        img.paste(block.crop(32 + qx, qy, 8, 8), qx, qy)
        return img
    if kind == 'H':
        img.paste(block.crop(16, 16, 16, 8), 0, 0)
        img.paste(block.crop(16, 56, 16, 8), 0, 8)
        return img
    if kind == 'V':
        img.paste(block.crop(0, 32, 8, 16), 0, 0)
        img.paste(block.crop(40, 32, 8, 16), 8, 0)
        return img
    if kind == 'LONE':
        return block.crop(0, 0, 16, 16)
    raise KeyError(kind)


def rock_mass(k, ramp, out, seed=5, r=6.0):
    """A boulder-pile 'forest' (crag walls): rock clumps instead of crowns."""
    def render(mask):
        img = F.lattice_render(grid_mask(mask), 48, 48, ramp, out, seed, r=r, lobes=3)
        return k.paint(img)
    return render


def recolor_old(gf, k, img, banks):
    """An image drawn by the old generator (gen_field_gfx colour names) in
    this set's colours: each colour -> the nearest colour of the given
    banks (for the few dynamic pieces tiles2 has no drawing of)."""
    from .load import rgb_of
    cands = []
    for b in banks:
        for n in k.banks[b]:
            if n not in cands:
                cands.append(n)
    memo = {}
    out = Img(img.w, img.h)
    for y in range(img.h):
        for x in range(img.w):
            c = img.p[y][x]
            if c is None:
                continue
            if c not in memo:
                r, g, b = gf.C[c]
                memo[c] = min(cands, key=lambda n: sum((u - v) ** 2 for u, v in zip(rgb_of(n), (r, g, b))))
            out.p[y][x] = memo[c]
    return out


def painted_elev(k, ground, rock, outline, stairs_roles, deck_imgs, bevel=None, drip=None, tufts=None,
                 ledge_profile=None, lump=None, rock_dk=None):
    """ElevArt pieces painted with tiles2's cliff painters for a set whose
    sheet has no cliffs (the same painters kit.cliffs uses). rock: 5 roles
    dark -> light."""
    lk = dict(rx=5.5, ry=4.2, sx=8, sy=6.5)
    lk.update(lump or {})
    face = T.lump_texture(rock, 32, 32, 1, **lk)
    face2 = T.lump_texture(rock, 32, 32, 9, **lk)
    rim = minus(k.paint(T.cliff_rim(ground, ground, rock, outline, face_tex=face, bevel=bevel, drip=drip)), ground)
    face9 = k.paint(T.cliff_face(rock, outline, ground, tufts=tufts, tex=face, tex2=face2))
    face1 = k.paint(T.cliff_face_single(rock, outline, ground, face, tufts=tufts))
    prof = ledge_profile or [rock[4], rock[3], rock[2], rock[1], outline, rock[0]]
    ledge = minus(k.paint(T.ledge_block(ground, prof)).crop(0, 0, 64, 16), ground)
    hi, mid, riser, out, side = stairs_roles
    st = over(Img(16, 16), k.paint(T.stairs(hi, mid, riser, out, side, 1, 1)))
    stw = st.rot90()
    return {'rim': rim, 'face9': face9, 'face1': face1, 'stairs': [st, st, stw, stw.flip_h()],
            'deck_h': deck_imgs[0], 'deck_v': deck_imgs[1],
            'mouth': mouth(cell_of(face1, 1, 0), k.role(outline), k.role(rock_dk or rock[0])),
            'ledge': ledge, 'shadow': shadow(k.role(outline))}
