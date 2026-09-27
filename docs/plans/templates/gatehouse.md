# 13x9 gatehouse template

Use `TS_INTERIOR`, a warp at each end, and a guarded one-cell passage. The
13-column rows below are an authoring sketch; replace each symbol with a
character from the actual interior tileset legend in your region's `data.h`.

```
######.######
#.....#.....#
#.....#.....#
#..desk.....#
#....g......#
#.....#.....#
#.....#.....#
#.....#.....#
######.######
```

Place the north door/exit mat at (6,0)/(6,1) and south door/exit mat at
(6,8)/(6,7), or use a side door with a reciprocal warp. Replace `g` with a
`PERSON_IF` blocker whose hide flag is the gate-opening story flag. Give the
warden a line explaining the restriction before the player enters the aisle.
Do not make either return door conditional; verify both directions by flood
and a manual warp test. For the Accord gate use `FLAG_RIME_CREST`.
