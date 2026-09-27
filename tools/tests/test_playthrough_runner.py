"""Fail-closed parser and ELF-layout checks for the isolated ROM timer."""
import subprocess
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.playthrough.run import ROOT, check_layout, ids, parse_layout, layout_args


class PlaythroughRunnerTest(unittest.TestCase):
    def test_live_layout(self):
        if not (ROOT / 'game.elf').exists():
            self.skipTest('build local ROM first with make')
        check_layout()

    def test_layout_rejects_missing_and_duplicate_members(self):
        if not (ROOT / 'game.elf').exists():
            self.skipTest('build local ROM first with make')
        dwarf = subprocess.check_output(['arm-none-eabi-readelf', '--debug-dump=info',
                                         str(ROOT / 'game.elf')], text=True)
        layout = parse_layout(dwarf)
        self.assertGreater(layout['battle']['size'], layout['battle']['timer'])
        self.assertEqual(layout_args(layout)[8], str(layout['battle']['state']))
        for modified in (dwarf.replace('DW_TAG_structure_type', 'DW_TAG_typedef'),
                         dwarf.replace('DW_AT_data_member_location:',
                                       'DW_AT_missing_member_location:')):
            with self.subTest(modified=modified[:80]), self.assertRaises(ValueError):
                parse_layout(modified)
        synthetic = (" <1><abc>: Abbrev Number: 1 (DW_TAG_structure_type)\n"
                     "    DW_AT_byte_size : 100\n" + ''.join(
                         f" <2><{i:x}>: Abbrev Number: 2 (DW_TAG_member)\n"
                         f"    DW_AT_name : {name}\n"
                         f"    DW_AT_data_member_location: {i}\n"
                         for i, name in enumerate(('kind', 'team', 'team2', 'team_idx',
                                                    'ally', 'pair', 'no_run', 'state',
                                                    'cursor', 'move_cursor', 'result', 'timer'))))
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            parse_layout(dwarf + synthetic)

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
        self.assertRegex(result.stdout, r'CHECKPOINTS_COMPLETE frames=\d+ minutes=\d+\.\d+ wardens=1')
        self.assertIn('EDGE line=11 map=', result.stdout)
        self.assertNotIn('ACT_COMPLETE', result.stdout)

    def test_act3_reset_is_reported_without_counting_a_warden(self):
        if not (ROOT / 'game.elf').exists():
            self.skipTest('build local ROM first with make')
        result = subprocess.run(['python3', str(ROOT / 'tools/playthrough/run.py'),
                                 str(ROOT / 'tools/playthrough/act3.route')],
                                capture_output=True, text=True)
        if result.returncode == 0:
            # A repaired ROM must still satisfy the independent acceptance test.
            self.assertIn('BOUT_END kind=warden result=1', result.stdout)
            self.assertIn('CHECKPOINTS_COMPLETE', result.stdout)
            return
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertRegex(result.stdout, r'WAY line=6 map=44 x=22 y=19 frames=\d+')
        self.assertIn('reason=returned to title during timed route; possible ROM reset', result.stderr)
        self.assertIn('mode=10', result.stderr)
        self.assertIn('title_from_mode=0', result.stderr)
        self.assertIn('saw_battle=0', result.stderr)
        self.assertIn('wardens=0', result.stderr)
        self.assertNotIn('BOUT_END kind=warden result=1', result.stdout)
        self.assertNotIn('CHECKPOINTS_COMPLETE', result.stdout)

    def test_brookmill_shore_and_hearth_door_are_observed(self):
        if not (ROOT / 'game.elf').exists():
            self.skipTest('build local ROM first with make')
        with tempfile.TemporaryDirectory() as directory:
            approach = Path(directory) / 'act2-approach.route'
            approach.write_text((ROOT / 'tools/playthrough/act2.route').read_text().split('party_min 4')[0])
            result = subprocess.run(['python3', str(ROOT / 'tools/playthrough/run.py'), str(approach)],
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('WAY line=7 map=', result.stdout)
        self.assertIn('WARDEN line=15 map=', result.stdout)
        self.assertIn('BOUT_END kind=warden result=1', result.stdout)
        self.assertIn('EDGE line=19 map=', result.stdout)
        self.assertIn('BOUT_END kind=warden result=1 wild_wins=0 wild_runs=0 wardens=1 frames=3040', result.stdout)
        route = (ROOT / 'tools/playthrough/act2.route').read_text().split('way MAP_BROOKMILL 37 17')[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'hearth.route'
            path.write_text(route + 'way MAP_BROOKMILL 5 17\nway MAP_BROOKMILL 5 14\n'
                            'door MAP_BROOKMILL 5 14 north MAP_BROOKMILL_REST\n')
            hearth = subprocess.run(['python3', str(ROOT / 'tools/playthrough/run.py'), str(path)],
                                    capture_output=True, text=True)
            self.assertEqual(hearth.returncode, 0, hearth.stderr)
            self.assertRegex(hearth.stdout, r'DOOR line=\d+ map=\d+ x=5 y=8 frames=\d+')
            self.assertIn('CHECKPOINTS_COMPLETE', hearth.stdout)

    def test_act2_hall_switches_and_party_gate(self):
        if not (ROOT / 'game.elf').exists():
            self.skipTest('build local ROM first with make')
        route = ROOT / 'tools/playthrough/act2.route'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'hall-only.route'
            path.write_text(route.read_text().split('party_min 4')[0])
            result = subprocess.run(['python3', str(ROOT / 'tools/playthrough/run.py'), str(path)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('DOOR line=27 map=19 x=7 y=16 frames=4324', result.stdout)
            for group in range(3):
                self.assertRegex(result.stdout, rf'SWITCH line=\d+ group={group} state=1 frames=\d+')
            self.assertIn('WAY line=44 map=19 x=7 y=3 frames=6154', result.stdout)
            self.assertRegex(result.stdout, r'CHECKPOINTS_COMPLETE frames=6154 .* wardens=2 wild_wins=0')
            path.write_text(path.read_text() + 'party_min 4\n')
            blocked = subprocess.run(['python3', str(ROOT / 'tools/playthrough/run.py'), str(path)],
                                     capture_output=True, text=True)
            self.assertEqual(blocked.returncode, 2, blocked.stderr)
            self.assertIn('reason=insufficient in-game party for Master map=19 x=7 y=3', blocked.stderr)
            self.assertIn('frames=6154', blocked.stderr)
            path.write_text(route.read_text().split('party_min 4')[0].replace(
                'switch MAP_VOLT_HALL 0 1', 'switch MAP_VOLT_HALL 0 0'))
            wrong = subprocess.run(['python3', str(ROOT / 'tools/playthrough/run.py'), str(path)],
                                   capture_output=True, text=True)
            self.assertEqual(wrong.returncode, 2, wrong.stderr)
            self.assertIn('reason=Hall switch state mismatch map=19 x=4 y=13', wrong.stderr)

    def test_act2_fixture_master_loss_never_claims_crest(self):
        if not (ROOT / 'game.elf').exists():
            self.skipTest('build local ROM first with make')
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / 'make-save'
            fixture = Path(directory) / 'act2.sav'
            subprocess.run(['cc', '-std=c11', '-O2', '-Wno-unused-function',
                            '-Wno-missing-field-initializers', '-o', str(binary),
                            str(ROOT / 'tools/playthrough/make_act_start_save.c')], check=True)
            generate = lambda: subprocess.run([str(binary), str(fixture)], capture_output=True, text=True, check=True)
            first = generate()
            digest = hashlib.sha256(fixture.read_bytes()).hexdigest()
            self.assertEqual(len(fixture.read_bytes()), 32768)
            self.assertIn('SAVE version=7 party=4 map=26 x=34 y=18', first.stdout)
            generate()
            self.assertEqual(hashlib.sha256(fixture.read_bytes()).hexdigest(), digest)
            route = ROOT / 'tools/playthrough/act2.route'
            command = ['python3', str(ROOT / 'tools/playthrough/run.py'), '--act-start-save',
                       str(fixture), str(route)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn('MASTER_CHOICE yes', result.stdout)
            self.assertIn('MASTER_TEAM opponents=6 trainer_kind=1', result.stdout)
            self.assertIn('FORCED_SWITCH slot=1', result.stdout)
            self.assertIn('MASTER_LOSS team_index=4/6 frames=8849', result.stderr)
            self.assertEqual(result.stdout.count('PARTY_STATE master_loss_in_battle_before_heal'), 1)
            self.assertRegex(result.stdout, r'PARTY_STATE master_loss_in_battle_before_heal frames=8462.*slot0=species:0,lv:20,hp:0.*slot1=species:3,lv:19,hp:0.*slot2=species:13,lv:19,hp:0.*slot3=species:21,lv:20,hp:0')
            self.assertIn('PARTY_STATE blocked_after_game_recovery_possible frames=8849', result.stdout)
            self.assertIn('reason=party lost; no unmeasured recovery', result.stderr)
            self.assertNotIn('MASTER line=', result.stdout)
            self.assertNotIn('ACT_COMPLETE', result.stdout)
            self.assertNotIn('CHECKPOINTS_COMPLETE', result.stdout)
            self.assertNotIn('crest=', result.stdout)
            no_fixture = subprocess.run(['python3', str(ROOT / 'tools/playthrough/run.py'),
                                         str(route)], capture_output=True, text=True)
            self.assertNotEqual(no_fixture.returncode, 0)
            self.assertIn('master requires --act-start-save', no_fixture.stderr)

    def test_invalid_routes_fail_before_emulation(self):
        cases = [
            ('start MAP_MEADOW\nstart MAP_MEADOW\n', 'exactly one start'),
            ('start MAP_MEADOW\nflag FLAG_STORM_CALMED\n', 'flags must precede'),
            ('start MAP_MEADOW\nway MAP_MEADOW 64 5\n', 'outside 64x64'),
            ('start MAP_MEADOW\nedge MAP_MEADOW diagonal MAP_TOWN\n', 'direction'),
            ('start MAP_MEADOW\nwild_limit 7\n', 'wild_limit'),
            ('start MAP_MEADOW\nwarden MAP_MEADOW 0 0 sideways\n', 'direction'),
            ('start MAP_MEADOW\ndoor MAP_MEADOW 0 0 sideways MAP_TOWN\n', 'direction'),
            ('start MAP_MEADOW\ndoor MAP_MEADOW 0 0 east MAP_INVALID\n', 'destination'),
            ('start MAP_MEADOW\nswitch MAP_VOLT_HALL 3 1\n', 'switch needs'),
            ('start MAP_MEADOW\nparty_min 7\n', 'party_min needs'),
            ('start MAP_MEADOW\nmaster MAP_VOLT_HALL 7 3 north FLAG_INVALID\n', 'master needs'),
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
