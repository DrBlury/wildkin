"""Expand local world-data includes in compiler order for metadata tools."""
import re
from pathlib import Path

INCLUDE = re.compile(r'^\s*#include\s+"([^"\n]+)"\s*$', re.MULTILINE)
COMMENTS = re.compile(r'"(?:\\.|[^"\\])*"|/\*.*?\*/|//[^\n]*', re.DOTALL)


def read_world_source(path, root, stack=()):
    path, root = Path(path).resolve(), Path(root).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"world include escapes its root: {path}")
    if path in stack:
        raise ValueError(f"world include cycle: {path}")
    source = COMMENTS.sub(lambda m: m.group() if m.group().startswith('"') else ' ',
                          path.read_text())
    return INCLUDE.sub(lambda m: read_world_source(path.parent / m.group(1), root, stack + (path,)),
                       source)
