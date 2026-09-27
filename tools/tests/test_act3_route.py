"""ROM-backed Act III westward checkpoint, not a Hall or act-clear assertion."""
import subprocess
import sys
import unittest

from tools.playthrough.run import ROOT, ids


class Act3RouteTest(unittest.TestCase):
    def test_physical_westward_transitions_and_upper_town(self):
        if not (ROOT / 'game.gba').is_file() or not (ROOT / 'game.elf').is_file():
            self.skipTest('build the matching local ROM and ELF with make first')
        maps = ids('all_ids.inc', 'MAP_')
        result = subprocess.run(
            [sys.executable, str(ROOT / 'tools/playthrough/run.py'),
             str(ROOT / 'tools/playthrough/act3.route')],
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('BOUT_END kind=warden result=1', result.stdout)
        for destination in ('MAP_REEDWICK', 'MAP_SALTWIND', 'MAP_PORT_BRINE'):
            self.assertRegex(result.stdout, rf'EDGE line=\d+ map={maps[destination]} x=\d+ y=\d+ frames=\d+')
        self.assertRegex(result.stdout,
                         rf'WAY line=\d+ map={maps["MAP_PORT_BRINE"]} x=27 y=5 frames=\d+')
        self.assertRegex(result.stdout,
                         r'CHECKPOINTS_COMPLETE frames=\d+ minutes=\d+\.\d+ wardens=1 wild_wins=0 wild_runs=0')
        self.assertNotIn('DOOR line=', result.stdout)
        self.assertNotIn('ACT_COMPLETE', result.stdout)


if __name__ == '__main__':
    unittest.main()
