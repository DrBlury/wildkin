"""Tile sheets, manifests, GBA validation and scene rendering (tools/tiles2).

A Sheet is one area's tileset: a 16-cell-wide grid of 16x16 cells holding
ground tiles, autotile blocks, multi-cell objects and animation strips, plus
the palette (colour roles -> RGB), optional palette variants and the GBA bank
plan. `Sheet.write()` produces

    assets/tiles2/<set>/<set>.png            the sheet (RGBA, RGB15-exact)
    assets/tiles2/<set>/<set>.json           manifest (see docs/TILES2.md)
    assets/tiles2/<set>/<set>@<variant>.png  palette variants
    assets/tiles2/<set>/<set>_sheet_x3.png   labelled 3x review sheet

Layout formats (cells are 16x16 px):

  tile      1x1 opaque ground cell.
  object    WxH cells, transparent pixels allowed. Per-cell masks: solid,
            top (drawn above people), floor (walkable over water/void).
  autotile  'rmxp16' 3x4 block (RPG Maker XP autotile at 16 px):
              row 0: [preview][fill variant][inner corners]
              rows 1-3: 3x3 of outer corners / edges / fill.
            Each 16x16 cell splits into 8x8 quadrants that map 1:1 onto the
            engine's quad variants (src/game/field.c autotile_quads):
              v0 fill, v1 inner corner, v2 side edge, v3 top/bottom edge,
              v4 outer corner.
  patch9    5x3 block of whole-cell pieces for cell-resolution borders
            (forest walls, cliffs, roofs): cols 0-2 = 3x3 nine-slice,
            cols 3-4 rows 0-1 = inner corners NW NE / SW SE,
            cols 3-4 row 2 = extra fill / isolated variants.
  Animated entries repeat their block horizontally, one block per frame.
"""

import json
import os

from core import Img, hash32, q15, c15, hex_rgb, render, write_png_rgba, draw_text

CELL = 16
COLS = 16

ATTRS = ('SOLID', 'GRASS', 'DOOR', 'WATER', 'COUNTER', 'EXIT', 'SIGN', 'LEDGE',
         'ICE', 'SOIL', 'CURRENT', 'DIR_LO', 'DIR_HI', 'PAD', 'SWITCH', 'DEEP')

# 8x8 quadrant order everywhere: 0 TL, 1 TR, 2 BL, 3 BR.
QUADS = ((0, 0), (8, 0), (0, 8), (8, 8))

# rmxp16 block: where each engine quad variant takes each quadrant from,
# as (block col, block row) of the 3x4 layout.
RMXP_SRC = {
    0: [(1, 2)] * 4,                                   # fill
    1: [(2, 0)] * 4,                                   # inner corners
    2: [(0, 2), (2, 2), (0, 2), (2, 2)],               # W / E edges
    3: [(1, 1), (1, 1), (1, 3), (1, 3)],               # N / S edges
    4: [(0, 1), (2, 1), (0, 3), (2, 3)],               # outer corners
}


def mask_bits(spec, w, h, name, what):
    """'XX/.X' (rows split by '/', one char per cell) -> list of bools."""
    if spec is None:
        return None
    if spec == 'all':
        return [True] * (w * h)
    if spec == 'none':
        return [False] * (w * h)
    rows = spec.split('/')
    if len(rows) != h or any(len(r) != w for r in rows):
        raise ValueError('%s: %s mask %r does not match %dx%d' % (name, what, spec, w, h))
    return [ch == 'X' for r in rows for ch in r]


def mask_str(bits, w):
    if bits is None:
        return None
    rows = []
    for y in range(len(bits) // w):
        rows.append(''.join('X' if bits[y * w + x] else '.' for x in range(w)))
    return '/'.join(rows)


class Entry:
    def __init__(self, name, kind, frames, w, h, section, **kw):
        self.name, self.kind, self.frames = name, kind, frames
        self.w, self.h = w, h          # cells per frame
        self.section = section
        self.x = self.y = None          # sheet cell position (frame 0)
        self.attrs = list(kw.pop('attrs', []))
        self.group = kw.pop('group', None)
        self.weight = kw.pop('weight', None)
        self.doc = kw.pop('doc', '')
        self.period = kw.pop('period', None)
        self.layer = kw.pop('layer', None)
        self.over = kw.pop('over', None)
        self.format = kw.pop('format', None)
        self.tags = list(kw.pop('tags', []))
        self.solid = kw.pop('solid', None)
        self.top = kw.pop('top', None)
        self.floor = kw.pop('floor', None)
        self.anchor = kw.pop('anchor', None)
        self.extra = kw.pop('extra', {})
        if kw:
            raise TypeError('%s: unknown entry fields %s' % (name, sorted(kw)))
        for a in self.attrs:
            if a not in ATTRS:
                raise ValueError('%s: unknown attribute %s' % (name, a))


class Sheet:
    def __init__(self, name, title, palette, variants=None, banks=None, doc=''):
        """palette: {role: '#rrggbb'}; variants: {variant: {role: '#rrggbb'}}
        banks: optional list of role lists to seed the bank solver."""
        self.name, self.title, self.doc = name, title, doc
        self.palette = {k: q15(hex_rgb(v)) for k, v in palette.items()}
        self.variants = {}
        for vn, over in (variants or {}).items():
            p = dict(self.palette)
            for k, v in over.items():
                if k not in p:
                    raise KeyError('%s variant %s: unknown role %s' % (name, vn, k))
                p[k] = q15(hex_rgb(v))
            self.variants[vn] = p
        self.seed_banks = banks
        self.entries = []
        self.by_name = {}
        self.section_name = 'misc'
        self.sections = []
        self.scenes = []

    # ------------------------------------------------------------------
    # authoring API
    # ------------------------------------------------------------------
    def section(self, name):
        self.section_name = name
        if name not in self.sections:
            self.sections.append(name)

    def _add(self, e):
        if e.name in self.by_name:
            raise ValueError('%s: duplicate entry %s' % (self.name, e.name))
        for f in e.frames:
            if f.w != e.w * CELL or f.h != e.h * CELL:
                raise ValueError('%s.%s: frame %dx%d, expected %dx%d cells' %
                                 (self.name, e.name, f.w, f.h, e.w, e.h))
            for c in f.colors():
                if c not in self.palette:
                    raise KeyError('%s.%s: colour role %r not in palette' % (self.name, e.name, c))
        self.entries.append(e)
        self.by_name[e.name] = e
        return e

    def tile(self, name, img, frames=None, **kw):
        """Opaque 16x16 ground cell (optionally animated)."""
        fr = frames or [img]
        for f in fr:
            for y in range(f.h):
                for x in range(f.w):
                    if f.p[y][x] is None:
                        raise ValueError('%s.%s: transparent pixel in ground tile' % (self.name, name))
        kw.setdefault('layer', 'ground')
        return self._add(Entry(name, 'tile', fr, 1, 1, self.section_name, **kw))

    def object(self, name, img, frames=None, **kw):
        fr = frames or [img]
        w, h = fr[0].w // CELL, fr[0].h // CELL
        if fr[0].w % CELL or fr[0].h % CELL:
            raise ValueError('%s.%s: %dx%d not a multiple of 16' % (self.name, name, fr[0].w, fr[0].h))
        kw.setdefault('layer', 'mid')
        e = Entry(name, 'object', fr, w, h, self.section_name, **kw)
        # masks: default solid = every cell not top/floor that has pixels
        top = mask_bits(e.top, w, h, name, 'top') or [False] * (w * h)
        floor = mask_bits(e.floor, w, h, name, 'floor') or [False] * (w * h)
        solid = mask_bits(e.solid, w, h, name, 'solid')
        if solid is None:
            solid = []
            for cy in range(h):
                for cx in range(w):
                    k = cy * w + cx
                    has = any(fr[0].p[cy * CELL + y][cx * CELL + x] is not None
                              for y in range(CELL) for x in range(CELL))
                    solid.append(has and not top[k] and not floor[k])
        e.top, e.floor, e.solid = mask_str(top, w), mask_str(floor, w), mask_str(solid, w)
        return self._add(e)

    def autotile(self, name, block, frames=None, **kw):
        """rmxp16 3x4 block (48x64) or list of frames."""
        fr = frames or [block]
        kw.setdefault('layer', 'ground')
        kw.setdefault('format', 'rmxp16')
        e = Entry(name, 'autotile', fr, 3, 4, self.section_name, **kw)
        return self._add(e)

    def patch9(self, name, block, frames=None, **kw):
        fr = frames or [block]
        kw.setdefault('format', 'patch9')
        kw.setdefault('layer', 'ground')
        return self._add(Entry(name, 'patch9', fr, 5, 3, self.section_name, **kw))

    def custom(self, name, img, fmt, frames=None, **kw):
        """A block with a bespoke documented layout (cliffs, bridges...)."""
        fr = frames or [img]
        w, h = fr[0].w // CELL, fr[0].h // CELL
        kw['format'] = fmt
        kw.setdefault('layer', 'ground')
        return self._add(Entry(name, 'block', fr, w, h, self.section_name, **kw))

    def scene(self, sc):
        self.scenes.append(sc)

    # ------------------------------------------------------------------
    # layout
    # ------------------------------------------------------------------
    def layout(self):
        """Shelf-pack entries section by section, COLS cells wide."""
        y = 0
        self.section_rows = []
        for sec in self.sections:
            items = [e for e in self.entries if e.section == sec]
            if not items:
                continue
            self.section_rows.append((sec, y))
            y += 1                         # label row
            occ = {}

            def free(x0, y0, w, h):
                if x0 + w > COLS:
                    return False
                for yy in range(y0, y0 + h):
                    for xx in range(x0, x0 + w):
                        if (xx, yy) in occ:
                            return False
                return True
            for e in items:
                W = e.w * len(e.frames)
                H = e.h
                if W > COLS:
                    # wrap long animation strips: frames go on further rows
                    per = max(1, COLS // e.w)
                    rows = (len(e.frames) + per - 1) // per
                    W, H = e.w * per, e.h * rows
                placed = False
                yy = y
                while not placed:
                    for xx in range(0, COLS - W + 1):
                        if free(xx, yy, W, H):
                            e.x, e.y = xx, yy
                            for a in range(yy, yy + H):
                                for b in range(xx, xx + W):
                                    occ[(b, a)] = e.name
                            placed = True
                            break
                    yy += 1
                e.frame_pos = []
                per = max(1, W // e.w)
                for i in range(len(e.frames)):
                    e.frame_pos.append((e.x + (i % per) * e.w, e.y + (i // per) * e.h))
            bottom = max(b for (_, b) in occ) + 1 if occ else y
            y = bottom + 0
        self.rows = y

    def image(self, palette=None):
        img = Img(COLS * CELL, self.rows * CELL)
        for e in self.entries:
            for f, (fx, fy) in zip(e.frames, e.frame_pos):
                img.paste(f, fx * CELL, fy * CELL)
        return img

    # ------------------------------------------------------------------
    # GBA validation: banks, tiles, budgets
    # ------------------------------------------------------------------
    def tiles8(self, e):
        """Yield (frame, cell_index, quad, pixel tuple) for an entry."""
        for fi, f in enumerate(e.frames):
            for cy in range(e.h):
                for cx in range(e.w):
                    for q, (qx, qy) in enumerate(QUADS):
                        px = tuple(f.p[cy * CELL + qy + y][cx * CELL + qx + x]
                                   for y in range(8) for x in range(8))
                        yield fi, cy * e.w + cx, q, px

    def color_sets(self):
        sets = set()
        for e in self.entries:
            for (_, _, _, px) in self.tiles8(e):
                c = frozenset(c for c in px if c is not None)
                if c:
                    sets.add(c)
        maximal = []
        for c in sorted(sets, key=lambda c: (-len(c), sorted(c))):
            if not any(c <= m for m in maximal):
                maximal.append(c)
        return maximal

    def solve_banks(self, max_banks=8, size=15):
        """Pack every 8x8 tile's colour set into <= max_banks palettes of
        <= size colours (index 0 is transparent). Agglomerative merging of
        the maximal colour sets, then greedy passes as fallbacks."""
        maximal = self.color_sets()
        if self.seed_banks:
            return self._solve_seeded(maximal, max_banks, size)
        cands = []
        # 1. agglomerative: merge the pair with the smallest union first
        banks = [set(m) for m in maximal]
        while True:
            # absorb banks that are subsets of others
            banks.sort(key=len, reverse=True)
            keep = []
            for b in banks:
                if not any(b <= k for k in keep):
                    keep.append(b)
            banks = keep
            if len(banks) <= 1:
                break
            best = None
            for i in range(len(banks)):
                for j in range(i + 1, len(banks)):
                    u = len(banks[i] | banks[j])
                    if u > size:
                        continue
                    score = (u - max(len(banks[i]), len(banks[j])), -len(banks[i] & banks[j]), u)
                    if best is None or score < best[0]:
                        best = (score, i, j)
            if best is None:
                break
            if len(banks) <= max_banks and best[0][0] > 0 and False:
                break
            _, i, j = best
            banks[i] = banks[i] | banks[j]
            del banks[j]
        if len(banks) <= max_banks:
            cands.append(banks)
        # 2. greedy first-fit over several orders
        for k in range(64):
            order = sorted(maximal, key=lambda s: (-len(s) if k % 2 == 0 else 0,
                                                   hash32(k, *sorted(hash32(*map(ord, c)) for c in s))))
            bk = []
            ok = True
            for st in order:
                if any(st <= b for b in bk):
                    continue
                c = [(len(b | st) - len(b), -len(b & st), i) for i, b in enumerate(bk) if len(b | st) <= size]
                if c:
                    bk[min(c)[2]] |= st
                elif len(bk) < max_banks:
                    bk.append(set(st))
                else:
                    ok = False
                    break
            if ok:
                cands.append(bk)
        if not cands:
            allc = set().union(*maximal) if maximal else set()
            raise ValueError('%s: colour sets do not fit %d banks of %d (%d roles; agglomerative '
                             'reached %d banks: %s)' % (self.name, max_banks, size, len(allc), len(banks),
                                                        [sorted(b) for b in banks]))
        best = min(cands, key=lambda b: (len(b), sum(len(x) for x in b)))
        order = list(self.palette)
        out = [sorted(b, key=order.index) for b in best]
        out.sort(key=lambda b: order.index(b[0]))
        return out

    def _solve_seeded(self, maximal, max_banks, size):
        """Designer banks first (the material plan in the set module), then
        fit every tile's colours into them; leftovers get new banks."""
        banks = [set(b) for b in self.seed_banks]
        for b in banks:
            if len(b) > size:
                raise ValueError('%s: seed bank has %d colours: %s' % (self.name, len(b), sorted(b)))
        left = []
        for st in maximal:
            if any(st <= b for b in banks):
                continue
            c = [(len(b | st) - len(b), -len(b & st), i) for i, b in enumerate(banks) if len(b | st) <= size]
            if c:
                banks[min(c)[2]] |= st
            else:
                left.append(st)
        bad = []
        for st in left:
            if any(st <= b for b in banks):
                continue
            c = [(len(b | st) - len(b), -len(b & st), i) for i, b in enumerate(banks) if len(b | st) <= size]
            if c:
                banks[min(c)[2]] |= st
            elif len(banks) < max_banks:
                banks.append(set(st))
            else:
                bad.append(st)
        if bad:
            msg = ['%s: %d colour sets fit no bank:' % (self.name, len(bad))]
            for st in bad:
                msg.append('  %s  <- %s' % (sorted(st), ', '.join(self.who_uses(st)[:6])))
            raise ValueError('\n'.join(msg))
        order = list(self.palette)
        return [sorted(b, key=order.index) for b in banks]

    def who_uses(self, colours):
        """Entries with an 8x8 tile using all of `colours` (debug aid)."""
        out = set()
        for e in self.entries:
            for (_, _, _, px) in self.tiles8(e):
                if set(c for c in px if c is not None) == set(colours):
                    out.add(e.name)
        return sorted(out)

    def encode(self):
        """Assign banks, dedupe 8x8 tiles (with flips). Returns stats and
        per-entry tile references {entry: [[(tile, hflip, vflip, bank) x4] per cell per frame]}."""
        banks = self.solve_banks()
        bank_sets = [set(b) for b in banks]
        uniq = {}
        refs = {}
        cats = {}
        for e in self.entries:
            er = []
            for (fi, ci, q, px) in self.tiles8(e):
                cs = set(c for c in px if c is not None)
                if not cs:
                    er.append((0, 0, 0, 0))
                    continue
                b = next(i for i, s in enumerate(bank_sets) if cs <= s)
                idx = tuple(0 if c is None else banks[b].index(c) + 1 for c in px)
                key = None
                for h in (0, 1):
                    for v in (0, 1):
                        f = _flip(idx, h, v)
                        if f in uniq:
                            key = (uniq[f], h, v)
                            break
                    if key:
                        break
                if key is None:
                    uniq[idx] = len(uniq) + 1
                    key = (uniq[idx], 0, 0)
                    cats.setdefault(e.kind, 0)
                    cats[e.kind] += 1
                er.append(key + (b,))
            refs[e.name] = er
        return {'banks': banks, 'unique': len(uniq), 'by_kind': cats, 'refs': refs}

    # ------------------------------------------------------------------
    # output
    # ------------------------------------------------------------------
    def manifest(self, enc):
        ents = []
        for e in self.entries:
            d = {'name': e.name, 'kind': e.kind, 'section': e.section,
                 'x': e.x, 'y': e.y, 'w': e.w, 'h': e.h, 'layer': e.layer}
            if len(e.frames) > 1:
                d['frames'] = [list(p) for p in e.frame_pos]
                d['period'] = e.period or 16
            for k in ('format', 'over', 'group', 'weight', 'doc', 'anchor'):
                v = getattr(e, k)
                if v not in (None, '', []):
                    d[k] = v
            if e.attrs:
                d['attrs'] = e.attrs
            if e.tags:
                d['tags'] = e.tags
            if e.kind == 'object':
                d['solid'], d['top'] = e.solid, e.top
                if e.floor and 'X' in e.floor:
                    d['floor'] = e.floor
            if e.extra:
                d.update(e.extra)
            refs = enc['refs'][e.name]
            d['tiles8'] = len(set(r[0] for r in refs if r[0]))
            ents.append(d)
        return {
            'name': self.name, 'title': self.title, 'doc': self.doc,
            'cell': CELL, 'cols': COLS, 'rows': self.rows,
            'palette': {k: '#%02x%02x%02x' % v for k, v in self.palette.items()},
            'variants': {vn: {k: '#%02x%02x%02x' % v for k, v in p.items() if v != self.palette[k]}
                         for vn, p in self.variants.items()},
            'banks': enc['banks'],
            'stats': {'unique_tiles8': enc['unique'], 'by_kind': enc['by_kind'],
                      'entries': len(self.entries), 'colours': len(self.palette)},
            'sections': self.sections,
            'entries': ents,
            'scenes': [s.summary() for s in self.scenes],
        }

    def write(self, root):
        self.layout()
        enc = self.encode()
        d = os.path.join(root, self.name)
        os.makedirs(d, exist_ok=True)
        img = self.image()
        write_png_rgba(os.path.join(d, self.name + '.png'), img.w, img.h, render(img, self.palette))
        for vn, pal in self.variants.items():
            write_png_rgba(os.path.join(d, '%s@%s.png' % (self.name, vn)), img.w, img.h, render(img, pal))
        man = self.manifest(enc)
        with open(os.path.join(d, self.name + '.json'), 'w') as f:
            json.dump(man, f, indent=1)
            f.write('\n')
        self.write_review(os.path.join(d, self.name + '_sheet_x3.png'), img)
        scene_stats = []
        for sc in self.scenes:
            st = sc.write(d, self, enc)
            scene_stats.append(st)
        return man, scene_stats

    def write_review(self, path, img, scale=3):
        """Labelled sheet over a checkerboard, with grid lines."""
        W, H = img.w * scale, img.h * scale

        def bg(x, y):
            return (200, 200, 208, 255) if ((x // 4) + (y // 4)) & 1 else (232, 232, 236, 255)
        rows = render(img, self.palette, scale, bg=lambda x, y: bg(x, y))
        for y in range(0, H, CELL * scale):
            for x in range(W):
                if rows[y][x][3] == 255 and rows[y][x][:3] in ((200, 200, 208), (232, 232, 236)):
                    rows[y][x] = (170, 170, 184, 255)
        for (sec, sy) in self.section_rows:
            y0 = sy * CELL * scale
            for yy in range(y0, y0 + CELL * scale):
                for x in range(W):
                    rows[yy][x] = (32, 34, 44, 255)
            draw_text(rows, 6, y0 + 16, sec, (255, 220, 140, 255), scale=4)
        for e in self.entries:
            x0, y0 = e.x * CELL * scale, e.y * CELL * scale
            draw_text(rows, x0 + 2, y0 + 2, e.name[:(e.w * len(e.frames) * CELL * scale) // 4 - 1],
                      (20, 20, 30, 255), scale=1)
        write_png_rgba(path, W, H, rows)


def _flip(t, h, v):
    out = []
    for y in range(8):
        sy = 7 - y if v else y
        row = t[sy * 8:sy * 8 + 8]
        out.extend(row[::-1] if h else row)
    return tuple(out)


# ---------------------------------------------------------------------------
# Scenes: sample maps composed from a sheet
# ---------------------------------------------------------------------------

class Scene:
    """A sample map.

    ground: 2D list of cell kinds. A kind is a tile/group name, an autotile
    name (quad-autotiled against same-kind neighbours, like field.c), or a
    patch9 name (cell-resolution nine-slice).
    objects: list of (entry name, x, y, flags) drawn over the ground in
    back-to-front order; flags may contain 'h' (mirror) or a frame number.
    """

    def __init__(self, key, title, w, h, fill, doc=''):
        self.key, self.title, self.w, self.h, self.doc = key, title, w, h, doc
        self.ground = [[fill] * w for _ in range(h)]
        self.over = [[None] * w for _ in range(h)]    # transparent masses (forest, hedges)
        self.objects = []
        self.join = {}       # autotile name -> kinds that count as "same"
        self.sprinkles = []  # deferred decor scatter (needs the sheet for sizes)

    def summary(self):
        return {'key': self.key, 'title': self.title, 'w': self.w, 'h': self.h, 'doc': self.doc}

    # -- authoring helpers ---------------------------------------------
    def set(self, x, y, k, layer='ground'):
        if 0 <= x < self.w and 0 <= y < self.h:
            getattr(self, layer)[y][x] = k

    def get(self, x, y, layer='ground'):
        if 0 <= x < self.w and 0 <= y < self.h:
            return getattr(self, layer)[y][x]
        return None

    def rect(self, x0, y0, x1, y1, k, layer='ground'):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, k, layer)

    def rows(self, text, legend, ox=0, oy=0):
        """legend: char -> kind, or (kind, 'over') for the mass layer, or
        ('obj', name) to place an object with its top-left at the char."""
        lines = [l for l in text.strip('\n').split('\n')]
        for y, l in enumerate(lines):
            for x, ch in enumerate(l.rstrip()):
                v = legend.get(ch)
                if v is None:
                    continue
                if isinstance(v, tuple) and v[0] == 'obj':
                    self.put(v[1], ox + x, oy + y, v[2] if len(v) > 2 else '')
                elif isinstance(v, tuple):
                    self.set(ox + x, oy + y, v[0], v[1])
                else:
                    self.set(ox + x, oy + y, v)

    def put(self, name, x, y, flags=''):
        self.objects.append((name, x, y, flags))

    def sprinkle(self, names, n, on, seed=0, margin=1):
        """Scatter n small 1x1 decor objects (cycling through names) over
        free cells whose ground kind is in `on` (applied at compose time,
        after hand-placed objects, so nothing overlaps)."""
        self.sprinkles.append((list(names), n, set(on), seed, margin))

    def _apply_sprinkles(self, sheet):
        if not self.sprinkles:
            return
        occ = set()
        for (name, x, y, flags) in self.objects:
            e = sheet.by_name[name.split(':')[0]]
            w, h = (1, 1) if ':' in name else (e.w, e.h)
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    occ.add((xx, yy))
        for (names, n, on, seed, margin) in self.sprinkles:
            placed = 0
            tries = 0
            while placed < n and tries < n * 50:
                tries += 1
                x = margin + hash32(tries, seed, 1) % max(1, self.w - 2 * margin)
                y = margin + hash32(tries, seed, 2) % max(1, self.h - 2 * margin)
                if (x, y) in occ or self.ground[y][x] not in on or self.over[y][x] is not None:
                    continue
                if any((x + dx, y + dy) in occ for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                    continue
                self.objects.append((names[placed % len(names)], x, y, ''))
                occ.add((x, y))
                placed += 1
        self.sprinkles = []

    # -- rendering -------------------------------------------------------
    def same(self, k, x, y, layer='ground'):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return True
        n = self.get(x, y, layer)
        if n == k or n in self.join.get(k, ()):
            return True
        # a material drawn "over" this one (deep water in water) continues it
        sh = getattr(self, '_sheet', None)
        if sh is not None and n in sh.by_name and sh.by_name[n].over == k:
            return True
        return False

    def compose(self, sheet, frame=0):
        self._sheet = sheet
        self._apply_sprinkles(sheet)
        img = Img(self.w * CELL, self.h * CELL)
        for layer in ('ground', 'over'):
            for y in range(self.h):
                for x in range(self.w):
                    self.draw_cell(sheet, img, x, y, frame, layer)
        def ent(name):
            return sheet.by_name[name.split(':')[0]]

        def piece(name, fr):
            if ':' not in name:
                return fr
            c, r = (int(v) for v in name.split(':')[1].split(','))
            return fr.crop(c * CELL, r * CELL, CELL, CELL)
        order = sorted(range(len(self.objects)),
                       key=lambda i: (self.objects[i][2] + (1 if ':' in self.objects[i][0] else ent(self.objects[i][0]).h)
                                      - (100 if ent(self.objects[i][0]).layer == 'ground' else 0), i))
        for i in order:
            name, x, y, flags = self.objects[i]
            e = ent(name)
            fr = piece(name, e.frames[frame % len(e.frames)])
            if 'h' in flags:
                fr = fr.flip_h()
            img.paste(fr, x * CELL, y * CELL)
        return img

    def draw_cell(self, sheet, img, x, y, frame, layer='ground'):
        k = getattr(self, layer)[y][x]
        if k is None:
            return
        e = sheet.by_name.get(k)
        if e is None:
            # a variant group
            members = [m for m in sheet.entries if m.group == k]
            if not members:
                raise KeyError('%s scene %s: unknown ground %s' % (sheet.name, self.key, k))
            tot = sum(m.weight or 1 for m in members)
            r = hash32(x, y, 77) % tot
            for m in members:
                r -= m.weight or 1
                if r < 0:
                    e = m
                    break
        f = e.frames[frame % len(e.frames)]
        if e.kind == 'tile' or e.kind == 'object':
            img.paste(f.crop(0, 0, CELL, CELL), x * CELL, y * CELL)
            return
        if e.kind == 'autotile':
            for c, (qx, qy) in enumerate(QUADS):
                dx, dy = (-1 if qx == 0 else 1), (-1 if qy == 0 else 1)
                vs = self.same(k, x, y + dy, layer)
                hs = self.same(k, x + dx, y, layer)
                ds = self.same(k, x + dx, y + dy, layer)
                v = (0 if ds else 1) if (vs and hs) else (2 if vs else (3 if hs else 4))
                bx, by = RMXP_SRC[v][c]
                if v == 0 and (hash32(x, y, c, 5) & 3) == 0:
                    bx, by = 1, 0          # the block's alternative fill
                q = f.crop(bx * CELL + qx, by * CELL + qy, 8, 8)
                img.paste(q, x * CELL + qx, y * CELL + qy)
            return
        if e.kind == 'patch9':
            sm = lambda xx, yy: self.same(k, xx, yy, layer)
            n = sm(x, y - 1)
            s = sm(x, y + 1)
            w = sm(x - 1, y)
            ea = sm(x + 1, y)
            col = 1 if (w and ea) else (0 if not w else 2)
            row = 1 if (n and s) else (0 if not n else 2)
            if w and ea and n and s:
                # inner corners
                if not sm(x - 1, y - 1):
                    col, row = 3, 0
                elif not sm(x + 1, y - 1):
                    col, row = 4, 0
                elif not sm(x - 1, y + 1):
                    col, row = 3, 1
                elif not sm(x + 1, y + 1):
                    col, row = 4, 1
                elif (hash32(x, y, 9) & 3) == 0:
                    col, row = 3, 2
            img.paste(f.crop(col * CELL, row * CELL, CELL, CELL), x * CELL, y * CELL)
            return
        raise ValueError('%s: %s (%s) cannot be used as ground' % (sheet.name, k, e.kind))

    def resident(self, sheet, enc):
        """Unique 8x8 tiles this scene needs resident (engine budget 768)."""
        self._apply_sprinkles(sheet)
        used = set()
        refs = enc['refs']
        kinds = set()
        for grid in (self.ground, self.over):
            for row in grid:
                for k in row:
                    if k is not None:
                        kinds.add(k)
        names = set()
        for k in kinds:
            if k in sheet.by_name:
                names.add(k)
            else:
                names.update(m.name for m in sheet.entries if m.group == k)
        names.update(o[0].split(':')[0] for o in self.objects)
        for n in names:
            e = sheet.by_name[n]
            per = e.w * e.h * 4
            # animation frames stream into the same slots: count frame 0
            for r in refs[n][:per]:
                if r[0]:
                    used.add(r[0])
        return len(used)

    def write(self, d, sheet, enc):
        img = self.compose(sheet)
        base = os.path.join(d, 'scene_' + self.key)
        write_png_rgba(base + '.png', img.w, img.h, render(img, sheet.palette))
        rows = render(img, sheet.palette, 2)
        write_png_rgba(base + '_x2.png', img.w * 2, img.h * 2, rows)
        for vn, pal in sheet.variants.items():
            write_png_rgba('%s@%s.png' % (base, vn), img.w, img.h, render(img, pal))
        n = self.resident(sheet, enc)
        return {'scene': self.key, 'resident_tiles8': n, 'size': (self.w, self.h)}
