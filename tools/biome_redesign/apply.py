#!/usr/bin/env python3
"""Validate or apply the pinned existing-area biome redesign.

Run --check first. --apply is reserved for the coordinator after the shared
regional freeze and save/progression baseline. No source is edited on --check.
"""
import argparse
import json
import pathlib
import re
import sys
from collections import deque

ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = pathlib.Path(__file__).with_name('guarded_spans.json')
ROW = re.compile(r'(?m)^(?P<indent>[ \t]*)"(?P<tile>[^"\n]+)"(?P<tail>[ \t]*,?[ \t]*(?:/\*[^\n]*\*/)?[ \t]*)$')


def section(source, array):
    header = f'static const char *const {array}[] = {{'
    if source.count(header) != 1:
        raise ValueError(f'{array}: array definition changed or absent')
    start = source.index(header) + len(header)
    end = source.index('};', start)
    return start, end, source[start:end]


def rows_of(source, array):
    start, end, block = section(source, array)
    matches = list(ROW.finditer(block))
    if not matches or len(matches) > 64:
        raise ValueError(f'{array}: invalid row layout')
    return start, end, block, matches


def changed(before, after):
    return {(x, y) for y, (a, b) in enumerate(zip(before, after))
            for x, (old, new) in enumerate(zip(a, b)) if old != new}


def protected(region, name, source, height, width):
    """Read concrete map-bound coordinates; protect every indexed placement and patch footprint."""
    marks = set()
    map_id = 'MAP_' + ('BROOKMILL_TRAIL' if name == 'BROOK_TRAIL' else name)
    # Event and story actors can be owned by a different region than their map.
    folder = ROOT / 'src/game/world'
    for file in folder.rglob('*'):
        if not file.is_file() or file.suffix not in ('.h', '.inc', '.c'):
            continue
        text = file.read_text()
        for m in re.finditer(r'\b' + map_id + r'\s*,\s*(\d+)\s*,\s*(\d+)', text):
            marks.add((int(m[1]), int(m[2])))
    for suffix in ('DECOR', 'OBJS', 'STAMPS', 'FEATS', 'PROJECT_PATCHES', 'PATCHES'):
        match = re.search(r'static const \w+ ' + name + '_' + suffix + r'\[\] = \{(.*?)\};', source, re.S)
        if not match:
            continue
        body = match[1]
        for m in re.finditer(r'\b(?:DPF|DP|OBJ|STAMP|EF)\(([^)]*)\)', body):
            args = [arg.strip() for arg in m[1].split(',')]
            try:
                x, y = (int(args[2]), int(args[3])) if m[0].startswith('STAMP') else (int(args[1]), int(args[2]))
            except (ValueError, IndexError):
                raise ValueError(f'{name}_{suffix}: unrecognized placement {m[0]}')
            if m[0].startswith('STAMP'):
                span_w = span_h = 6  # conservative stamp and door footprint
            elif m[0].startswith('EF'):
                span_w, span_h = int(args[3]), int(args[4])
            else:
                span_w = span_h = 1
            marks.update((xx, yy) for yy in range(y, y + span_h)
                         for xx in range(x, x + span_w))
        for m in re.finditer(r'\.x\s*=\s*(\d+)\s*,\s*\.y\s*=\s*(\d+)\s*,\s*\.w\s*=\s*(\d+)\s*,\s*\.h\s*=\s*(\d+)', body):
            x, y, w, h = map(int, m.groups())
            marks.update((xx, yy) for yy in range(y, y + h) for xx in range(x, x + w))
    return {(x, y) for x, y in marks if 0 <= x < width and 0 <= y < height}


def route_proof(before, after, edits, entry):
    array = entry["array"]
    h, w = len(before), len(before[0])
    if not h or h > 64 or w > 64 or any(len(row) != w for row in before + after):
        raise ValueError(f'{array}: dimensions changed')
    if not edits:
        return f'{array}: already applied, {w}x{h}'
    # Only exact approved bank cells may turn ordinary ground into solid trees.
    # Other walls, water, elevations, doors and exits remain immutable.
    forbidden = set('~xDX[]<>^v789123456pnoPpTtCcY#')
    if array != 'PORT_BRINE_ROWS': forbidden.add('q')
    if array != 'GRAVEWOOD_ROWS': forbidden.add('b')
    if array != 'CALDERA_ROWS': forbidden.add('y')
    approvals = {(x, y): (old, new) for x, y, old, new in entry.get('approvedCollisions', [])}
    if len(approvals) != len(entry.get('approvedCollisions', [])):
        raise ValueError(f'{array}: duplicate approved collision')
    if not set(approvals) <= edits:
        raise ValueError(f'{array}: approved collision absent from changed cells')
    for x, y in edits:
        old, new = before[y][x], after[y][x]
        approved = approvals.get((x, y)) == (old, new) and old not in forbidden and new in 'PpTt'
        if not approved and (old in forbidden or new in forbidden):
            raise ValueError(f'{array} ({x},{y}): unsafe terrain {old!r}->{new!r}')
    # Unapproved old walkability cannot be lost; pinches are checked against
    # named reachable endpoints below and with elevation-aware host tests.
    blocked = set('~xDX[]<>^v789123456pnoPpTtCcY#')
    if array != 'PORT_BRINE_ROWS': blocked.add('q')
    if array != 'GRAVEWOOD_ROWS': blocked.add('b')
    if array != 'CALDERA_ROWS': blocked.add('y')
    if array == 'EMBER_TUNNEL_ROWS': blocked.add('M')
    for y in range(h):
        for x in range(w):
            if before[y][x] not in blocked and after[y][x] in blocked and (x, y) not in approvals:
                raise ValueError(f'{array} ({x},{y}): unapproved old walkable cell blocked')
    for y, row in enumerate(before):
        for x in range(w):
            if x in (0, w-1) or y in (0, h-1):
                if row[x] != after[y][x]:
                    raise ValueError(f'{array}: edge contract changed')
    if array == 'EMBER_TUNNEL_ROWS':
        # The old horizontal cave-face spur opens onto existing floor both
        # north and south; the guarded boulder at (15,6) is untouched.
        if not all(after[9][x] == '_' and after[8][x] == '_' and after[10][x] == '_'
                   for x in (9, 10, 11)):
            raise ValueError('Ember Tunnel spur is not open on both ends')
    route = entry.get('route')
    if route:
        start, end, bend, wall = (tuple(route[key]) for key in ('start', 'end', 'bend', 'wall'))
        if before[wall[1]][wall[0]] in blocked or after[wall[1]][wall[0]] not in blocked:
            raise ValueError(f'{array}: straight crossing not newly blocked')
        visited = {start}
        queue = deque([start])
        while queue:
            x, y = queue.popleft()
            for pt in ((x-1,y), (x+1,y), (x,y-1), (x,y+1)):
                xx, yy = pt
                if 0 <= xx < w and 0 <= yy < h and pt not in visited and after[yy][xx] not in blocked:
                    visited.add(pt)
                    queue.append(pt)
        if not {start, end, bend} <= visited:
            raise ValueError(f'{array}: detour endpoint or bend disconnected')
    return f'{array}: {len(edits)} exact cells, {len(approvals)} approved collisions, {w}x{h}' 


def prepare(entries, originals):
    result = dict(originals)
    proof = []
    for entry in entries:
        path = entry['path']
        source = result[path]
        if 'rows' not in entry:
            old, new = entry['before'], entry['after']
            if entry.get('kind') == 'decor' and source.count(new) == 1:
                continue  # The pinned insertion includes its original prefix.
            if source.count(old) == 1:
                result[path] = source.replace(old, new, 1)
            elif source.count(new) == 1 and source.count(old) == 0:
                pass
            else:
                raise ValueError(f'{path}: NPC dialogue changed concurrently')
            continue
        start, end, block, matches = rows_of(source, entry['array'])
        before = [m['tile'] for m in matches]
        if len(before) != entry['height'] or any(len(row) != entry['width'] for row in before):
            raise ValueError(f"{entry['array']}: map shape changed concurrently")
        after = list(before)
        seen = set()
        for edit in entry['rows']:
            y = edit['y']
            if y in seen or y >= len(before):
                raise ValueError(f"{entry['array']}: duplicate/out-of-range row")
            seen.add(y)
            if before[y] == edit['before']:
                after[y] = edit['after']
            elif before[y] == edit['after']:
                pass  # Already applied: retain the target row.
            else:
                raise ValueError(f"{path}:{entry['array']} row {y}: concurrent overlap; abort")
        delta = changed(before, after)
        region = path.split('/')[3]
        name = entry['array'].removesuffix('_ROWS')
        conflict = delta & protected(region, name, source, len(before), len(before[0]))
        if conflict:
            raise ValueError(f'{entry["array"]}: protected coordinate(s) {sorted(conflict)[:8]}')
        proof.append(route_proof(before, after, delta, entry))
        if delta:
            # Replace only the pinned row tokens; comments, unrelated rows and
            # unrelated hunks in the same file remain byte-for-byte unchanged.
            pieces = []
            pos = 0
            for y, match in enumerate(matches):
                pieces.extend((block[pos:match.start('tile')], after[y]))
                pos = match.end('tile')
            pieces.append(block[pos:])
            result[path] = source[:start] + ''.join(pieces) + source[end:]
    return result, proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true', help='read-only preflight and route proof')
    group.add_argument('--apply', action='store_true', help='coordinator only, after source freeze')
    args = parser.parse_args()
    entries = json.loads(MANIFEST.read_text())
    paths = {item['path'] for item in entries}
    if any(not path.startswith('src/game/world/') or pathlib.PurePosixPath(path).is_absolute()
           or '..' in pathlib.PurePosixPath(path).parts for path in paths):
        raise ValueError('manifest path escapes regional source')
    originals = {path: (ROOT / path).read_text() for path in paths}
    staged, proof = prepare(entries, originals)
    for line in proof:
        print(line)
    print(f"{sum(staged[p] != originals[p] for p in paths)} files pending; guarded preflight OK")
    if args.apply:
        # Recheck all files immediately before writing; abort without writes
        # if any peer changed the tree while the proof was running.
        for path, old in originals.items():
            if (ROOT / path).read_text() != old:
                raise ValueError(f'{path}: concurrent change since preflight; abort')
        for path in sorted(paths):
            if staged[path] != originals[path]:
                (ROOT / path).write_text(staged[path])
        print('Applied guarded spans; run host/save tests and ROM validation now.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, IndexError) as error:
        print(f'biome redesign aborted: {error}', file=sys.stderr)
        raise SystemExit(1)
