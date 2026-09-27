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
    return [found[name] for name in ('cur_map', 'player', 'game_mode', 'story_bits', 'dialog_count')]

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
        if parts[0] not in ('start', 'flag', 'way'):
            parser.error(f'line {number}: invalid command {parts[0]}')
        expected = {'start': 2, 'flag': 2, 'way': 4}[parts[0]]
        if len(parts) != expected:
            parser.error(f'line {number}: expected {expected - 1} arguments')
        table = flags if parts[0] == "flag" else maps
        if parts[1] not in table:
            parser.error(f"line {number}: unknown ID {parts[1]}")
        parts[1] = str(table[parts[1]])
        if parts[0] == "way":
            try:
                x, y = map(int, parts[2:])
            except ValueError:
                parser.error(f"line {number}: waypoint coordinates must be integers")
            if not (0 <= x < 64 and 0 <= y < 64):
                parser.error(f"line {number}: waypoint outside 64x64 map bounds")
        converted.append(' '.join(parts))
    build = ROOT / 'build'
    build.mkdir(exist_ok=True)
    route = build / 'playtime-route.txt'
    route.write_text('\n'.join(converted) + '\n')
    binary = build / 'playtime-runner'
    prefix = os.environ.get('MGBA_PREFIX', '/opt/homebrew')
    subprocess.run(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-I' + prefix + '/include',
                    '-o', str(binary), str(ROOT / 'tools/playthrough/runner.c'),
                    '-L' + prefix + '/lib', '-lmgba'], check=True)
    return subprocess.run([str(binary), str(ROOT / 'game.gba'), str(route), *symbols()]).returncode

if __name__ == '__main__':
    sys.exit(main())
