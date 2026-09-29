"""Focused guard regressions for the four collision-changing landscapes."""
import copy
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import apply
from fixtures import before_sources


class RouteGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = json.loads(apply.MANIFEST.read_text())
        current = {entry['path']: (apply.ROOT / entry['path']).read_text()
                   for entry in cls.entries}
        cls.originals = before_sources(cls.entries, current)

    def test_four_routes_gain_only_pinned_collisions(self):
        staged, _ = apply.prepare(self.entries, self.originals)
        routes = [entry for entry in self.entries if 'route' in entry]
        self.assertEqual(len(routes), 4)
        for entry in routes:
            old_rows = [m['tile'] for m in apply.rows_of(self.originals[entry['path']], entry['array'])[3]]
            new_rows = [m['tile'] for m in apply.rows_of(staged[entry['path']], entry['array'])[3]]
            for x, y, old, new in entry['approvedCollisions']:
                self.assertEqual((old_rows[y][x], new_rows[y][x]), (old, new))
            wall = entry['route']['wall']
            self.assertNotEqual(old_rows[wall[1]][wall[0]], new_rows[wall[1]][wall[0]])

    def test_unapproved_collision_rejected(self):
        entries = copy.deepcopy(self.entries)
        route = next(entry for entry in entries if entry.get('array') == 'FROSTPINE_ROWS')
        route['approvedCollisions'] = route['approvedCollisions'][1:]
        with self.assertRaisesRegex(ValueError, 'unsafe terrain|unapproved old walkable'):
            apply.prepare(entries, self.originals)

    def test_changed_approved_old_cell_rejected(self):
        entries = copy.deepcopy(self.entries)
        route = next(entry for entry in entries if entry.get('array') == 'MOONVEIL_ROWS')
        route['approvedCollisions'][0][2] = '='
        with self.assertRaisesRegex(ValueError, 'unsafe terrain|unapproved old walkable'):
            apply.prepare(entries, self.originals)


if __name__ == '__main__':
    unittest.main()
