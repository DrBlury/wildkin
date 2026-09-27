#!/usr/bin/env python3
"""Compile the isolated mGBA timer and resolve map/flag names from current IDs."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
WORLD = ROOT / 'src/game/world'

def ids(name, prefix):
    result = []
    for include in re.findall(r'#include "([^"]+)"', (WORLD / name).read_text()):
        text = (WORLD / include).read_text()
        result.extend(re.findall(r'^\s*(' + prefix + r'[A-Z0-9_]+)\s*,', text, re.M))
    return {token: i for i, token in enumerate(result)}

def symbols():
    output = subprocess.check_output(['arm-none-eabi-nm', str(ROOT / 'game.elf')], text=True)
    found = dict((name, address) for address, _, name in re.findall(r'^(\w+)\s+(\w)\s+(\w+)$', output, re.M))
    return [found[name] for name in ('cur_map', 'player', 'game_mode', 'story_bits', 'dialog_count',
                                     'dialog_phase', 'battle', 'party', 'MOVES', 'warp')]

# These are the only live RAM/ROM fields consumed by runner.c. Resolve anonymous
# structures by their complete distinctive field signature, not source line.
LAYOUT_FIELDS = {
    'battle': ('kind', 'team', 'team2', 'team_idx', 'ally', 'pair', 'no_run',
               'state', 'cursor', 'move_cursor', 'result', 'timer'),
    'monster': ('moves', 'pp', 'hp', 'name'),
    'move': ('cat', 'power', 'acc', 'effect'),
}


def parse_layout(output):
    """Resolve unique DWARF structures; never guess offsets from source lines."""
    structures = []
    blocks = re.split(r'(?=^ <1><[0-9a-f]+>: Abbrev Number: \d+ \(DW_TAG_structure_type\))',
                      output, flags=re.M)
    for block in blocks[1:]:
        header, *children = re.split(r'(?=^ <2><[0-9a-f]+>: Abbrev Number: \d+ \(DW_TAG_member\))',
                                      block.split('\n <1><', 1)[0], flags=re.M)
        size_match = re.search(r'DW_AT_byte_size\s+: (\d+)\b', header)
        if not size_match:
            continue
        members = {}
        for child in children:
            name = re.search(r'DW_AT_name\s+: (?:\([^\n]*\): )?([A-Za-z_][A-Za-z_0-9]*)\s*$',
                             child, re.M)
            location = re.search(r'DW_AT_data_member_location\s*:\s*(\d+)\b', child)
            if name:
                members.setdefault(name.group(1), []).append(int(location.group(1)) if location else None)
        structures.append((int(size_match.group(1)), members))
    layout = {}
    for label, fields in LAYOUT_FIELDS.items():
        matches = [(size, members) for size, members in structures
                   if all(field in members for field in fields)]
        if len(matches) != 1:
            raise ValueError(f'ELF {label} layout is missing or ambiguous ({len(matches)} candidates)')
        size, members = matches[0]
        for field in fields:
            offsets = members[field]
            width = (4 if label == 'battle' and field != 'no_run' or
                     label == 'monster' and field in ('moves', 'pp') else 1)
            if len(offsets) != 1 or offsets[0] is None or not 0 <= offsets[0] <= size - width:
                raise ValueError(f'ELF {label}.{field} offset is missing, ambiguous or out of bounds')
        layout[label] = {'size': size, **{field: members[field][0] for field in fields}}
    return layout


def check_layout():
    output = subprocess.check_output(['arm-none-eabi-readelf', '--debug-dump=info',
                                      str(ROOT / 'game.elf')], text=True)
    return parse_layout(output)


def layout_args(layout):
    return [str(layout[label][field]) for label, fields in LAYOUT_FIELDS.items()
            for field in ('size', *fields)]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('route', type=Path)
    args = parser.parse_args()
    maps, flags = ids('all_ids.inc', 'MAP_'), ids('all_flag_ids.inc', 'FLAG_')
    if not (ROOT / "game.gba").is_file() or not (ROOT / "game.elf").is_file():
        parser.error("build this worktree first with make (game.gba and matching game.elf required)")
    converted = []
    for number, line in enumerate(args.route.read_text().splitlines(), 1):
        parts = line.split('#', 1)[0].split()
        if not parts:
            continue
        if parts[0] not in ('start', 'flag', 'way', 'edge', 'door', 'warden', 'wild_limit'):
            parser.error(f'line {number}: invalid command {parts[0]}')
        expected = {'start': 2, 'flag': 2, 'way': 4, 'edge': 4, 'door': 6, 'warden': 5, 'wild_limit': 2}[parts[0]]
        if len(parts) != expected:
            parser.error(f'line {number}: expected {expected - 1} arguments')
        table = flags if parts[0] == 'flag' else maps if parts[0] != 'wild_limit' else None
        if table is not None and parts[1] not in table:
            parser.error(f"line {number}: unknown ID {parts[1]}")
        if table is not None:
            parts[1] = str(table[parts[1]])
        if parts[0] == "way":
            try:
                x, y = map(int, parts[2:])
            except ValueError:
                parser.error(f"line {number}: waypoint coordinates must be integers")
            if not (0 <= x < 64 and 0 <= y < 64):
                parser.error(f"line {number}: waypoint outside 64x64 map bounds")
        if parts[0] == 'edge':
            if parts[2] not in ('north', 'south', 'west', 'east') or parts[3] not in maps:
                parser.error(f'line {number}: edge needs direction and destination map ID')
            parts[2] = str({'north': 6, 'south': 7, 'west': 5, 'east': 4}[parts[2]])
            parts[3] = str(maps[parts[3]])
        if parts[0] == 'door':
            try:
                x, y = map(int, parts[2:4])
            except ValueError:
                parser.error(f'line {number}: door coordinates must be integers')
            if not (0 <= x < 64 and 0 <= y < 64) or parts[4] not in ('north', 'south', 'west', 'east') or parts[5] not in maps:
                parser.error(f'line {number}: door needs adjacent position, direction and destination map ID')
            parts[4] = str({'north': 6, 'south': 7, 'west': 5, 'east': 4}[parts[4]])
            parts[5] = str(maps[parts[5]])
        if parts[0] == 'warden':
            try:
                x, y = map(int, parts[2:4])
            except ValueError:
                parser.error(f'line {number}: warden coordinates must be integers')
            if not (0 <= x < 64 and 0 <= y < 64) or parts[4] not in ('north', 'south', 'west', 'east'):
                parser.error(f'line {number}: warden needs valid adjacent position and direction')
            parts[4] = str({'north': 6, 'south': 7, 'west': 5, 'east': 4}[parts[4]])
        if parts[0] == 'wild_limit' and parts[1] not in ('3', '6'):
            parser.error(f'line {number}: wild_limit must be 3 (hamlet) or 6 (route)')
        converted.append(' '.join(parts))
    if sum(line.startswith('start ') for line in converted) != 1:
        parser.error('route must contain exactly one start')
    start_index = next(i for i, line in enumerate(converted) if line.startswith('start '))
    if any(line.startswith('flag ') for line in converted[start_index + 1:]):
        parser.error('prerequisite flags must precede start')
    try:
        layout = check_layout()
    except ValueError as exc:
        parser.error(str(exc))
    build = ROOT / 'build'
    build.mkdir(exist_ok=True)
    route = build / 'playtime-route.txt'
    route.write_text('\n'.join(converted) + '\n')
    binary = build / 'playtime-runner'
    prefix = os.environ.get('MGBA_PREFIX', '/opt/homebrew')
    subprocess.run(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-I' + prefix + '/include',
                    '-o', str(binary), str(ROOT / 'tools/playthrough/runner.c'),
                    '-L' + prefix + '/lib', '-lmgba'], check=True)
    return subprocess.run([str(binary), str(ROOT / 'game.gba'), str(route), *symbols(), *layout_args(layout)]).returncode

if __name__ == '__main__':
    sys.exit(main())
