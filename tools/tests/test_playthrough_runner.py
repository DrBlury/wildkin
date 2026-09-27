"""Fail-closed parser and ELF-layout checks for the isolated ROM timer."""
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.playthrough.run import ROOT, check_layout, ids


class PlaythroughRunnerTest(unittest.TestCase):
    def test_live_layout(self):
        if not (ROOT / 'game.elf').exists():
            self.skipTest('build local ROM first with make')
        check_layout()

    def test_route_ids_are_unique(self):
        for file, prefix in [('all_ids.inc', 'MAP_'), ('all_flag_ids.inc', 'FLAG_')]:
            table = ids(file, prefix)
            self.assertEqual(len(table), len(set(table.values())))

    def test_heron_warden_is_observed_not_skipped(self):
        if not (ROOT / 'game.elf').exists():
            self.skipTest('build local ROM first with make')
        result = subprocess.run(['python3', str(ROOT / 'tools/playthrough/run.py'),
                                 str(ROOT / 'tools/playthrough/act3.route')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('BOUT_END kind=warden result=1', result.stdout)
        self.assertIn('CHECKPOINTS_COMPLETE frames=2226', result.stdout)
        self.assertIn('EDGE line=11 map=', result.stdout)
        self.assertNotIn('ACT_COMPLETE', result.stdout)

    def test_invalid_routes_fail_before_emulation(self):
        cases = [
            ('start MAP_MEADOW\nstart MAP_MEADOW\n', 'exactly one start'),
            ('start MAP_MEADOW\nflag FLAG_STORM_CALMED\n', 'flags must precede'),
            ('start MAP_MEADOW\nway MAP_MEADOW 64 5\n', 'outside 64x64'),
            ('start MAP_MEADOW\nedge MAP_MEADOW diagonal MAP_TOWN\n', 'direction'),
            ('start MAP_MEADOW\nwild_limit 7\n', 'wild_limit'),
            ('start MAP_MEADOW\nwarden MAP_MEADOW 0 0 sideways\n', 'direction'),
        ]
        if not (ROOT / 'game.elf').exists():
            self.skipTest('build local ROM first with make')
        for route, expected in cases:
            with self.subTest(route=route), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'invalid.route'
                path.write_text(route)
                result = subprocess.run(['python3', str(ROOT / 'tools/playthrough/run.py'),
                                         str(path)], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stderr)


if __name__ == '__main__':
    unittest.main()
