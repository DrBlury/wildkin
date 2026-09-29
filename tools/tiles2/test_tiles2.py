#!/usr/bin/env python3
"""Checks for the second-generation tile sets (docs/TILES2.md).

    python3 tools/tiles2/test_tiles2.py            # committed assets
    TILES2_REBUILD=1 python3 tools/tiles2/test_tiles2.py   # also regenerate

Committed-asset checks (fast): every set has a sheet PNG and manifest;
palettes fit the GBA field budget (<= 8 banks x 15 colours); every 8x8
tile of every entry fits one bank; terrain catalogue <= 1024 tiles; every
sample scene fits the 768-tile resident budget; entry geometry, masks,
frames and names are well formed; variants only re-colour known roles.
With TILES2_REBUILD=1 the generator is run and its output must match the
committed files byte for byte (determinism / no stale assets).
"""

import json
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gba  # noqa: E402
from build import SETS, RESIDENT_MAX  # noqa: E402

CATALOG_MAX = 1024
NAME = re.compile(r'^[a-z][a-z0-9_]*$')
TERRAIN_KINDS = ('tile', 'autotile', 'patch9', 'block')


class CommittedSets(unittest.TestCase):
    loaded = {}

    @classmethod
    def ts(cls, name):
        if name not in cls.loaded:
            cls.loaded[name] = gba.load(name)
        return cls.loaded[name]

    def test_every_set_present(self):
        for n in SETS:
            d = os.path.join(gba.ASSETS, n)
            self.assertTrue(os.path.exists(os.path.join(d, n + '.png')), n)
            self.assertTrue(os.path.exists(os.path.join(d, n + '.json')), n)

    def test_palette_budget(self):
        for n in SETS:
            man = self.ts(n)['manifest']
            self.assertLessEqual(len(man['banks']), 8, n)
            for b in man['banks']:
                self.assertLessEqual(len(b), 15, '%s bank %s' % (n, b))
                for r in b:
                    self.assertIn(r, man['palette'])
            for vn, over in man['variants'].items():
                for r in over:
                    self.assertIn(r, man['palette'], '%s variant %s' % (n, vn))

    def test_encode_and_catalogue(self):
        for n in SETS:
            ts = self.ts(n)
            enc = gba.encode(ts)
            man = ts['manifest']
            terrain = set()
            for e in man['entries']:
                if e['kind'] in TERRAIN_KINDS:
                    for fr in enc['refs'][e['name']]:
                        for q in fr:
                            for v in q:
                                if v & 1023:
                                    terrain.add(v & 1023)
            self.assertLessEqual(len(terrain), CATALOG_MAX, '%s terrain catalogue %d' % (n, len(terrain)))
            for vn in man['variants']:
                self.assertEqual(len(gba.encode(ts, vn)['tiles']), len(enc['tiles']), '%s@%s' % (n, vn))

    def test_scenes_fit_resident_budget(self):
        for n in SETS:
            man = self.ts(n)['manifest']
            self.assertTrue(man['scenes'], '%s has no sample scene' % n)
            for sc in man['scenes']:
                path = os.path.join(gba.ASSETS, n, 'scene_%s.png' % sc['key'])
                self.assertTrue(os.path.exists(path), path)
        stats = os.path.join(gba.ASSETS, 'stats.json')
        with open(stats) as f:
            data = json.load(f)
        for n in SETS:
            for sc in data[n]['scenes']:
                self.assertLessEqual(sc['resident_tiles8'], RESIDENT_MAX, '%s/%s' % (n, sc['scene']))

    def test_entry_geometry(self):
        for n in SETS:
            ts = self.ts(n)
            man = ts['manifest']
            cols, rows = man['cols'], man['rows']
            seen = set()
            for e in man['entries']:
                self.assertRegex(e['name'], NAME)
                self.assertNotIn(e['name'], seen)
                seen.add(e['name'])
                for cells in gba.entry_cells(e):
                    for (cx, cy) in cells:
                        self.assertTrue(0 <= cx < cols and 0 <= cy < rows, '%s.%s' % (n, e['name']))
                if e['kind'] == 'object':
                    for k in ('solid', 'top'):
                        rws = e[k].split('/')
                        self.assertEqual(len(rws), e['h'], '%s.%s %s' % (n, e['name'], k))
                        self.assertTrue(all(len(r) == e['w'] for r in rws))
                if e['kind'] == 'autotile':
                    self.assertEqual((e['w'], e['h']), (3, 4))
                if e['kind'] == 'patch9':
                    self.assertEqual((e['w'], e['h']), (5, 3))
                if e['kind'] == 'tile':
                    for cells in gba.entry_cells(e):
                        px = gba.cell_pixels(ts, *cells[0])
                        self.assertTrue(all(p is not None for row in px for p in row),
                                        '%s.%s ground tile has transparency' % (n, e['name']))


class Legacy(unittest.TestCase):
    def test_every_used_old_kind_has_a_counterpart(self):
        import legacy
        m = legacy.build_map()
        self.assertEqual(m['missing'], {}, 'old decor kinds / stamps without a new entry')
        self.assertTrue(m['tilesets'])


@unittest.skipUnless(os.environ.get('TILES2_REBUILD'), 'set TILES2_REBUILD=1 to regenerate')
class Rebuild(unittest.TestCase):
    def test_generator_matches_committed(self):
        import importlib
        with tempfile.TemporaryDirectory() as tmp:
            for n in SETS:
                sheet = importlib.import_module('sets.' + n).build()
                sheet.write(tmp)
                for fn in (n + '.png', n + '.json'):
                    with open(os.path.join(tmp, n, fn), 'rb') as a, open(os.path.join(gba.ASSETS, n, fn), 'rb') as b:
                        self.assertEqual(a.read(), b.read(), '%s/%s is stale: run tools/tiles2/build.py' % (n, fn))


if __name__ == '__main__':
    unittest.main()
