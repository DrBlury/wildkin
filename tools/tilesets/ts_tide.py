"""The 'tide' tileset (W-WEST): the CURRENT HALL and the DROWNED BELL.

Split off 'coast' so the outdoor towns keep room for their props in the
512-tile scene charblock. The art, legend and palette banks live in
ts_coast.py (build_tide); the banks are the same as 'coast', so the west
props (tools/decor_west.py) are encoded for both.
"""

from tilesets.ts_coast import build_tide as build  # noqa: F401

USES_DECOR = []   # its props are registered for 'tide' in decor_west.py
