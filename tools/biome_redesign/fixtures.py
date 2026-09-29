"""Reconstruct pinned pre-edit text in memory so guard tests work after application."""
import apply


def before_sources(entries, current):
    result = dict(current)
    for entry in entries:
        path = entry['path']
        source = result[path]
        if 'rows' not in entry:
            if entry['after'] in source:
                source = source.replace(entry['after'], entry['before'], 1)
            elif entry['before'] not in source:
                raise ValueError(f'{path}: neither pinned text version exists')
        else:
            start, end, block, matches = apply.rows_of(source, entry['array'])
            edits = {row['y']: row for row in entry['rows']}
            for y in sorted(edits, reverse=True):
                row, match = edits[y], matches[y]
                if match['tile'] not in (row['before'], row['after']):
                    raise ValueError(f'{path}: pinned row {y} changed')
                block = block[:match.start('tile')] + row['before'] + block[match.end('tile'):]
            source = source[:start] + block + source[end:]
        result[path] = source
    return result
