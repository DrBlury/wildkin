"""Build the game's field tilesets from the tiles2 art (docs/TILES2.md 8).

tools/gen_field_gfx.py still owns the *structure* of every tileset: the
terrain names and their order (MT_* ids), legends, attributes, stamps and
their sizes, doors, blend groups, grass varieties and which decor kinds a
set offers. Maps and game code depend on all of it. This module replaces
the *art*: build() takes the structure recorded from the old builder
(Recorder) and an art module engine/art_<set>.py, and returns the same
`out` dict the old builder returned, drawn entirely from tiles2.

An art module defines art(ctx) -> dict with
  'set'       tiles2 set name (colours, banks and entries come from it)
  'terrain'   {old terrain name: spec}  spec = Img (opaque ground cell) |
              ('fit', img) (a composite: stray colours take the nearest
              colour of the best bank) | ('top', bottom, top) |
              ('anim', [frames], period) | ('overlay', img, above_people) |
              ('mass', group)
  'add_terrain', 'legend', 'attrs', 'ground', 'overlay'
              new terrain names (appended after the old ones) and the
              legend / attribute / flag entries that use them
  'path', 'water' (+ 'water_period')   rmxp16 blocks (water: list of frames)
  'blends'    {first inner terrain name: rmxp16 block (the ground over its outer ground)}
  'stamps'    {stamp name: Img exactly w*16 x h*16}; transparent pixels
              make it an overlay stamp (a building over the map's ground)
  'masses'    {group: {'render': fn(mask) -> Img 48x48, 'layer': {terrain: 'top'|'mid'}}}
  'elev'      see elev_art()
  'grass_colors' {old colour name: role} for the set's tools/grass.py styles
  'decor'     {decor kind: Img | [frames] | (frames, period)}  (old footprint)
  'backdrop'  (r, g, b) or None (keep the old choice)
  'extra'     fn(gf, ts, out, art) for set-specific tables (farm soil)
"""

import copy
import importlib

from .load import kit as get_kit, rmxp_quad, quad_pix, QUADS, minus, rgb_of

PORTED = ['town', 'wild', 'interior', 'coast', 'snow', 'cave', 'volcanic', 'grim', 'dusk', 'dream', 'farm', 'crypt', 'tide', 'desert', 'jungle', 'city']   # old tileset names drawn from tiles2 (gen_field_gfx.build_tilesets)


# Colours emitted differently from their name: the rooms' near-black void
# must be exactly black (tools/tests/test_area_tiles.c: margins of narrow
# interiors are black).
FORCE = {'T2:080808': (0, 0, 0)}


def set_ported(names):
    PORTED[:] = list(names)


# ---------------------------------------------------------------------------
# structure capture
# ---------------------------------------------------------------------------

class Recorder:
    """Wraps gf.finish_tileset while the old builders run."""

    def __init__(self, gf):
        self.gf = gf
        self.orig = gf.finish_tileset
        self.current = None
        self.rec = {}

    def __enter__(self):
        gf = self.gf
        rec = self

        def finish(out, name, tag, attrs, ground, overlay, legend, oob, default_ground,
                   backdrop, doors=(), legend_default='.', elev=None):
            rec.rec[rec.current] = dict(
                terrain=list(out['terrain']),
                stamps=[(s[0], s[2], s[3], s[4]) for s in out.get('stamps', [])],
                blends=[(list(b['inner']), list(b['outer'])) for b in out.get('blends', [])],
                has_path='path_q' in out, has_water='water_q' in out,
                docs=copy.deepcopy(out.get('docs')),
                args=dict(name=name, tag=tag, attrs=copy.deepcopy(attrs), ground=list(ground),
                          overlay=list(overlay), legend=copy.deepcopy(legend), oob=oob,
                          default_ground=default_ground, backdrop=backdrop, doors=list(doors),
                          legend_default=legend_default, elev=copy.deepcopy(elev)))
            return rec.orig(out, name, tag, attrs, ground, overlay, legend, oob, default_ground,
                            backdrop, doors=doors, legend_default=legend_default, elev=elev)
        gf.finish_tileset = finish
        return self

    def __exit__(self, *a):
        self.gf.finish_tileset = self.orig


# ---------------------------------------------------------------------------
# encoding helpers (all return GBA screen entries)
# ---------------------------------------------------------------------------

def _bank_for_frames(ts, pixf, what):
    cols = set(c for pix in pixf for c in pix if c is not None)
    b = ts.bank_for(cols, ())
    if b is None:
        raise ValueError('%s: %s colours %s fit no bank' % (ts.name, what, sorted(cols)))
    return b


def anim_quads(ts, qframes, what):
    """qframes[f][c][v] 8x8 pixel lists -> (q[c][v] entries, anim tuple).
    Animated tiles are contiguous and never shared (the engine copies each
    frame over the block)."""
    nf = len(qframes)
    first = len(ts.tiles)
    frames = [[] for _ in range(nf)]
    seen = {}
    nv = len(qframes[0][0])
    q = [[0] * nv for _ in range(4)]
    for c in range(4):
        for v in range(nv):
            pixf = [qframes[f][c][v] for f in range(nf)]
            if all(all(x is None for x in p) for p in pixf):
                q[c][v] = 0
                continue
            b = _bank_for_frames(ts, pixf, '%s[%d][%d]' % (what, c, v))
            key = (b, tuple(tuple(p) for p in pixf))
            if key not in seen:
                idx = [ts.indices(p, b) for p in pixf]
                seen[key] = ts.add_raw(idx[0])
                for f in range(nf):
                    frames[f].append(idx[f])
            q[c][v] = seen[key] | (b << 12)
    return q, (first, frames, None)


def anim_cell(ts, imgs, what):
    """Animated 16x16 cell -> (4 entries, anim)."""
    qf = [[[quad_pix(im, c)] for c in range(4)] for im in imgs]
    q, anim = anim_quads(ts, qf, what)
    return [q[c][0] for c in range(4)], anim


def rmxp_entries(ts, block, what, opaque=True):
    """q[c][v] entries of a static rmxp16 block."""
    return [[ts.add(rmxp_quad(block, c, v), where='%s[%d][%d]' % (what, c, v), opaque=opaque)
             for v in range(5)] for c in range(4)]


def cell_entries(ts, img, what, opaque=True, x0=0, y0=0, fit=None):
    """fit: gen_field_gfx.fit_bank_pix, for composites (an object baked
    over a floor) whose 8x8 tiles mix two banks' colours: the few foreign
    colours take the nearest colour of the bank that fits best."""
    out = []
    for c in range(4):
        pix = quad_pix(img, c, x0, y0)
        if fit:
            pix = fit(ts, pix)
        out.append(ts.add(pix, where='%s[%d]' % (what, c), opaque=opaque))
    return out


# ---------------------------------------------------------------------------
# masses: neighbour-aware overlay cells (forests of TREE_TOP/TREE_BOTTOM...)
# ---------------------------------------------------------------------------

# mask bits: N NE E SE S SW W NW
NB = ((0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1))


def canonical_mask(m):
    """Diagonals only matter when both adjacent orthogonals are set."""
    n, e, s, w = m & 1, m & 4, m & 16, m & 64
    out = m & (1 | 4 | 16 | 64)
    if n and e:
        out |= m & 2
    if s and e:
        out |= m & 8
    if s and w:
        out |= m & 32
    if n and w:
        out |= m & 128
    return out


def build_mass(ts, group, spec):
    """-> (pick[256] piece index, pieces[[4 entries]])."""
    render = spec['render']
    pieces, index, pick = [], {}, [0] * 256
    cache = {}
    for m in range(256):
        cm = canonical_mask(m)
        if cm not in cache:
            cache[cm] = render(cm)
        img = cache[cm]
        ents = tuple(ts.add(quad_pix(img, c, 16, 16), where='mass.%s[%d]' % (group, cm), opaque=False)
                     for c in range(4))
        if ents not in index:
            index[ents] = len(pieces)
            pieces.append(list(ents))
        pick[m] = index[ents]
    return pick, pieces


# ---------------------------------------------------------------------------
# elevation art (ElevArt, docs/ELEVATION.md) from tiles2 cliff pieces
# ---------------------------------------------------------------------------

def elev_art(ts, E, where):
    """E: {'rim': 48x64 overlay block (transparent where the high ground
    shows), 'face9': 80x48 cliff_face patch9, 'face1': 64x16 one-row face,
    'stairs': [N, S, W, E] 16x16, 'deck_h': 48x32, 'deck_v': 32x48,
    'mouth': 16x16, 'ledge': 64x16 (south-facing row), 'shadow': 16x16}"""
    def enc(img, c, what, x0=0, y0=0):
        return ts.add(quad_pix(img, c, x0, y0), where='%s.%s[%d]' % (where, what, c), opaque=False)

    art = {}
    f9, f1 = E['face9'], E['face1']
    face = []
    for c in range(4):
        row = []
        for v in range(4):
            cont_v, cont_s = v & 1, v & 2
            left = c % 2 == 0
            col = 1 if cont_s else (0 if left else 2)
            img, x0, y0 = (f9, col * 16, 16) if cont_v else (f1, col * 16, 0)
            row.append(enc(img, c, 'face%d' % v, x0, y0))
        face.append(row)
    art['face'] = face
    rim = E['rim']
    art['rim'] = [[0] + [ts.add(rmxp_quad(rim, c, v), where='%s.rim[%d][%d]' % (where, c, v), opaque=False)
                         for v in range(1, 5)] for c in range(4)]
    sh = E['shadow']
    art['shadow'] = [enc(sh, 0, 'shadow'), 0, enc(sh, 2, 'shadow'), 0]
    art['stairs'] = [[enc(E['stairs'][d], c, 'stairs%d' % d) for c in range(4)] for d in range(4)]
    dh, dv = E['deck_h'], E['deck_v']
    tab = []
    for c in range(4):
        row = []
        for v in range(4):
            rail, end = v & 1, v & 2
            col = (0 if c % 2 == 0 else 2) if end else 1
            if c < 2:
                r = 0 if rail else 1
            else:
                r = 1 if rail else 0
            row.append(enc(dh, c, 'deck_h%d' % v, col * 16, r * 16))
        tab.append(row)
    art['deck_h'] = tab
    tab = []
    for c in range(4):
        row = []
        for v in range(4):
            rail, end = v & 1, v & 2
            col = (0 if c % 2 == 0 else 1) if rail else (1 if c % 2 == 0 else 0)
            r = (0 if c < 2 else 2) if end else 1
            row.append(enc(dv, c, 'deck_v%d' % v, col * 16, r * 16))
        tab.append(row)
    art['deck_v'] = tab
    art['mouth'] = [enc(E['mouth'], c, 'mouth') for c in range(4)]
    lg = E['ledge']
    art['ledge'] = [[enc(lg, c, 'ledge%d' % v, (1 if v else (0 if c % 2 == 0 else 2)) * 16, 0)
                     for v in range(2)] for c in range(4)]
    return art


def remap_style(st, colors, k, sname, what):
    """A tools/grass.py style with its colour names swapped for tiles2 roles."""
    def m(v):
        if isinstance(v, str):
            if v in colors:
                c = colors[v]
                return c if c.startswith('T2:') else k.role(c)
            return v
        if isinstance(v, list):
            return [m(x) for x in v]
        if isinstance(v, tuple):
            return tuple(m(x) for x in v)
        return v
    out = {}
    for key, v in st.items():
        out[key] = v if key in ('ground', 'back', 'front', 'part_kind', 'rows') else m(v)
    return out


# ---------------------------------------------------------------------------
# the builder
# ---------------------------------------------------------------------------

class Ctx:
    def __init__(self, gf, sname, cap, old):
        self.gf, self.sname, self.cap, self.old = gf, sname, cap, old
        self.terrain = cap['terrain']
        self.stamps = {s[0]: (s[1], s[2]) for s in cap['stamps']}
        uses = set(old.get('uses_decor', ()))
        self.decor = [(d.name, d.w, d.h) for d in gf.all_decor() if sname in d.sets or d.name in uses]


def art_module(sname):
    return importlib.import_module('engine.art_%s' % sname)


def build(gf, sname, cap, old):
    ctx = Ctx(gf, sname, cap, old)
    art = art_module(sname).art(ctx)
    k = get_kit(art['set'], art.get('variant'))
    cols = k.colors()
    cols.update({n: v for n, v in FORCE.items() if n in cols})
    gf.register_colors(cols)
    for extra in art.get('colors', []):
        gf.register_colors({extra: rgb_of(extra)})
    banks = art.get('banks') or k.banks
    if len(banks) > 8:
        raise ValueError('%s: %d banks' % (sname, len(banks)))
    ts = gf.TileSet(sname, banks, limit=1024)
    names = list(cap['terrain']) + list(art.get('add_terrain', []))
    out = {'ts': ts, 'meta_b': [], 'meta_t': [], 'terrain': names, 'anims': []}
    if cap.get('docs') is not None:
        out['docs'] = cap['docs']

    def add_anim(anim, period):
        first, frames, _ = anim
        if frames and frames[0]:
            out['anims'].append((first, frames, period))

    # water first (its animation block), then terrain
    if cap['has_water']:
        wfr = art['water']
        qf = [[[rmxp_quad(b, c, v) for v in range(5)] for c in range(4)] for b in wfr]
        if len(wfr) > 1:
            q, anim = anim_quads(ts, qf, 'water')
            add_anim(anim, art.get('water_period', 16))
        else:
            q = rmxp_entries(ts, wfr[0], 'water')
        out['water_q'] = q
    masses = art.get('masses', {})
    terr = dict(art['terrain'])
    import grass as grass_mod
    for (gname, _st, _ch, _doc) in grass_mod.REGISTRY.get(cap['args']['name'], []):
        # tools/grass.py redraws these; a placeholder that shares the
        # default ground's tiles leaves nothing for it to drop
        if gname in terr:
            terr[gname] = terr[cap['args']['default_ground']]
    for n in names:
        if n not in terr:
            raise KeyError('%s: art has no terrain %s' % (sname, n))
        spec = terr[n]
        what = '%s.%s' % (sname, n)
        if isinstance(spec, tuple) and spec[0] == 'anim':
            ents, anim = anim_cell(ts, spec[1], what)
            add_anim(anim, spec[2])
            out['meta_b'].append(ents)
            out['meta_t'].append([0, 0, 0, 0])
        elif isinstance(spec, tuple) and spec[0] == 'fit':
            out['meta_b'].append(cell_entries(ts, spec[1], what, fit=gf.fit_bank_pix))
            out['meta_t'].append([0, 0, 0, 0])
        elif isinstance(spec, tuple) and spec[0] == 'top':
            out['meta_b'].append(cell_entries(ts, spec[1], what))
            out['meta_t'].append(cell_entries(ts, spec[2], what + '.top', opaque=False))
        elif isinstance(spec, tuple) and spec[0] in ('overlay', 'mass'):
            if spec[0] == 'mass':
                g = spec[1]
                img = masses[g]['render'](0).crop(16, 16, 16, 16)
                above = masses[g]['layer'][n] == 'top'
            else:
                img, above = spec[1], spec[2]
            ents = cell_entries(ts, img, what, opaque=False)
            if above:
                out['meta_b'].append([0, 0, 0, 0])
                out['meta_t'].append(ents)
            else:
                out['meta_b'].append(ents)
                out['meta_t'].append([0, 0, 0, 0])
        else:
            out['meta_b'].append(cell_entries(ts, spec, what))
            out['meta_t'].append([0, 0, 0, 0])
    # stamps (same names, sizes and order as before). A stamp with
    # transparent pixels is an overlay (a building drawn over whatever
    # ground the map has there, field.c map_decode); an opaque one is ground.
    out['stamps'] = []
    overlay_stamps = []
    for (name, cw, chh, doc) in cap['stamps']:
        im = art['stamps'][name]
        if (im.w, im.h) != (cw * 16, chh * 16):
            raise ValueError('%s: stamp %s is %dx%d, needs %dx%d' % (sname, name, im.w, im.h, cw * 16, chh * 16))
        opaque = all(c is not None for row in im.p for c in row)
        sid = len(out['meta_b'])
        for my in range(chh):
            for mx in range(cw):
                ents = cell_entries(ts, im, '%s.%s[%d,%d]' % (sname, name, mx, my), opaque=opaque,
                                    x0=mx * 16, y0=my * 16)
                out['meta_b'].append(ents)
                out['meta_t'].append([0, 0, 0, 0])
        out['stamps'].append((name, sid, cw, chh, doc))
        if not opaque:
            overlay_stamps.append(name)
    if cap['has_path']:
        out['path_q'] = rmxp_entries(ts, art['path'], sname + '.path')
        if art.get('path_alt'):
            blk, alt_names = art['path_alt']
            # a path over another ground: edge tiles mix two grounds' colours
            out['path_alt_q'] = [[ts.add(gf.fit_bank_pix(ts, rmxp_quad(blk, c, v)),
                                         where='%s.path_alt[%d][%d]' % (sname, c, v))
                                  for v in range(5)] for c in range(4)]
            out['path_alt_names'] = list(alt_names)
    if cap['has_path'] and 'water_q' not in out:
        raise ValueError('%s: path without water' % sname)
    # blends; ground variants an art module adds (variant_of: new -> the old
    # terrain it varies) count wherever the old one does
    vof = art.get('variant_of', {})
    out['blends'] = []
    for (inner, outer) in cap['blends']:
        outer = list(outer) + [n for n, o in vof.items() if o in outer and n not in outer]
        inner = list(inner) + [n for n, o in vof.items() if o in inner and n not in inner]
        blk = art['blends'][inner[0]]
        blks = blk if isinstance(blk, list) else [blk, blk]
        qs = []
        for b in blks:
            # two grounds meet in an edge tile: foreign colours take the
            # nearest of the best bank (as gen_field_gfx.blend_quads does)
            q = [[0] + [ts.add(gf.fit_bank_pix(ts, rmxp_quad(b, c, v)), where='%s.blend.%s' % (sname, inner[0]))
                        for v in range(1, 5)] for c in range(4)]
            qs.append(q)
        out['blends'].append({'inner': inner, 'outer': outer, 'q': qs})
    if art.get('extra'):
        art['extra'](gf, ts, out, art)
    # masses
    if masses:
        mass_tab = []
        for g, spec in masses.items():
            pick, pieces = build_mass(ts, g, spec)
            mass_tab.append({'group': g, 'members': list(spec['layer']), 'pick': pick, 'pieces': pieces})
        out['masses'] = mass_tab
    # finish with the recorded structure; grass and elevation from tiles2
    a = cap['args']
    import grass as grass_mod
    import elevation as elev_mod
    saved_reg = grass_mod.REGISTRY.get(a['name'])
    saved_elev = elev_mod.elevation_art
    if art.get('grass_colors') is not None and saved_reg:
        grass_mod.REGISTRY[a['name']] = [(n, remap_style(st, art['grass_colors'], k, sname, n), ch, doc)
                                         for (n, st, ch, doc) in saved_reg]
    E = art.get('elev')
    saved_roles = elev_mod.ROLES.pop(a['name'], None) if E is None else None
    if E is not None:
        elev_mod.elevation_art = lambda ts_, roles=None, where='elev': elev_art(ts_, E, where)
    try:
        attrs = copy.deepcopy(a['attrs'])
        attrs.update(art.get('attrs', {}))
        legend = copy.deepcopy(a['legend'])
        legend.update(art.get('legend', {}))
        ground = a['ground'] + [n for n in art.get('ground', [])] + \
            [n for n, o in vof.items() if o in a['ground'] and n not in art.get('ground', [])]
        for n, o in vof.items():
            if o in attrs and n not in attrs:
                attrs[n] = attrs[o]
        res = gf.finish_tileset(out, a['name'], a['tag'], attrs, ground,
                                a['overlay'] + art.get('overlay', []),
                                legend, a['oob'], a['default_ground'], a['backdrop'],
                                doors=a['doors'], legend_default=a['legend_default'],
                                elev=a['elev'] if E is not None else None)
        if E is not None and 'elev' not in res:
            res['elev'] = elev_art(ts, E, sname)
    finally:
        elev_mod.elevation_art = saved_elev
        if saved_roles is not None:
            elev_mod.ROLES[a['name']] = saved_roles
        if saved_reg is None:
            grass_mod.REGISTRY.pop(a['name'], None)
        else:
            grass_mod.REGISTRY[a['name']] = saved_reg
    if E is None:
        res.pop('elev', None)
    for (name, sid, cw, chh, doc) in res['stamps']:
        if name in overlay_stamps:
            for i in range(cw * chh):
                res['mflags'][sid + i] |= gf.MF_OVERLAY
    for key in ('uses_decor',):
        if key in old:
            res[key] = old[key]
    if art.get('backdrop'):
        res['backdrop'] = art['backdrop']
    elif old.get('backdrop') != a['backdrop']:
        res['backdrop'] = old['backdrop']
    if res['backdrop'] != 'ground' and not isinstance(res['backdrop'], tuple):
        res['backdrop'] = tuple(res['backdrop'])
    res['art2'] = art
    res['masses'] = out.get('masses', [])
    for key in ('path_alt_q', 'path_alt_names'):
        if key in out:
            res[key] = out[key]
    return res


# ---------------------------------------------------------------------------
# decor
# ---------------------------------------------------------------------------

def decor_frames(sname, out, d):
    """(frames, period) for decor kind d in a ported set (old footprint)."""
    art = out['art2']
    spec = art['decor'].get(d.name)
    if spec is None:
        raise KeyError('%s: art has no decor %s' % (sname, d.name))
    if isinstance(spec, tuple):
        frames, period = spec
    elif isinstance(spec, list):
        frames, period = spec, d.period
    else:
        frames, period = [spec], d.period
    for f in frames:
        if (f.w, f.h) != (d.w * 16, d.h * 16):
            raise ValueError('%s: decor %s is %dx%d px, needs %dx%d cells' % (sname, d.name, f.w, f.h, d.w, d.h))
    return frames, period
