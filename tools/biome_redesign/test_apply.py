"""Run with python3 -m unittest discover -s tools/biome_redesign -p 'test_*.py'."""
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import apply
from fixtures import before_sources


class GuardedBiomeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = json.loads(apply.MANIFEST.read_text())
        cls.paths = {entry['path'] for entry in cls.entries}
        cls.disk_sources = {path: (apply.ROOT / path).read_text() for path in cls.paths}
        cls.originals = before_sources(cls.entries, cls.disk_sources)

    def test_preflight_is_read_only_and_idempotent(self):
        staged, proof = apply.prepare(self.entries, self.originals)
        self.assertEqual(len(proof), 19)
        self.assertEqual(sum(staged[p] != self.originals[p] for p in self.paths), 10)
        self.assertEqual(apply.prepare(self.entries, staged)[0], staged)
        self.assertEqual(self.disk_sources, {p: (apply.ROOT / p).read_text() for p in self.paths})

    def test_overlap_aborts_without_touching_source(self):
        bad = dict(self.originals)
        entry = self.entries[0]
        old = entry['rows'][0]['before']
        start, _, _, matches = apply.rows_of(bad[entry['path']], entry['array'])
        match = matches[entry['rows'][0]['y']]
        index = start + match.start('tile')
        bad[entry['path']] = bad[entry['path']][:index] + '!' + bad[entry['path']][index + 1:]
        with self.assertRaisesRegex(ValueError, 'concurrent overlap'):
            apply.prepare(self.entries, bad)
        self.assertEqual(self.disk_sources, {p: (apply.ROOT / p).read_text() for p in self.paths})

    def test_all_edits_are_guarded_and_fixed_size(self):
        staged, _ = apply.prepare(self.entries, self.originals)
        for entry in self.entries:
            if 'rows' not in entry:
                self.assertEqual(self.originals[entry['path']].count(entry['before']), 1)
                self.assertIn(entry['after'], staged[entry['path']])
                continue
            _, _, old, old_rows = apply.rows_of(self.originals[entry['path']], entry['array'])
            _, _, new, new_rows = apply.rows_of(staged[entry['path']], entry['array'])
            self.assertEqual(len(old_rows), len(new_rows))
            self.assertEqual(entry['width'], len(old_rows[0]['tile']))
            self.assertEqual(entry['height'], len(old_rows))
            self.assertEqual(sum(a['tile'] != b['tile'] for a, b in zip(old_rows, new_rows)), len(entry['rows']))
            self.assertNotEqual(old, new)


if __name__ == '__main__':
    unittest.main()
