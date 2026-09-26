# Far towns handoff: CINDERMOOR, DREAMSPIRE, SKY ISLE on heights

The three far towns were rebuilt on the elevation engine (docs/ELEVATION.md).
Each one now has 3-4 height levels, faces two rows tall where the drop matters,
an outline that is not a box, a bridge (or span) you walk over one way and under
the other on its main route, ledge shortcuts and a hidden path to a reward.
`make && make test` is green with no warnings, test_puzzles included. The only
failure seen was a flaky balance check in test_game ("super-effective hits
far harder…"). It comes from species data, not maps, and passed on a rerun.

| map | size | levels | over / under | hidden |
| --- | --- | --- | --- | --- |
| CINDERMOOR | 44x36 → **48x40** | 0-3 | Iron Bridge (22-25,17-18): the plaza road runs over the rail cut, and the mine rails run under it | a gap in the crags (8,3-4) leads to the smiths' soak: BRAVE CHILI satchel and OLD SOAKER |
| DREAMSPIRE | 48x40 → **48x44** | 0-3 | Dream Bridge (23-24,13-16): the Grand Stair runs north over the Sleepers' Lane, which runs east-west under it; also a TUNNEL (16,17-24) under the Lantern Terrace | a gap in the trees (45,10-11) leads to the secret moon garden: GRAND TONIC satchel and NIGHT GARDENER |
| SKY ISLE | 24x20 → **36x30** | 0-3 | Stone Span (16-19,14-15): walk over it between the spires, or under it along the Wind Walk | a gap in the crags (5,14) leads to the Eyrie: new ASTRAL SHARD satchel |

Renders and in-ROM shots are in `docs/images/towns_far/`: `*_map.png` (game renderer),
`cm_bridge_under/over`, `ds_bridge_under/over`, `ds_tunnel_mouth`,
`sky_span_under/over` and `*_hidden_in` (the player inside each hidden passage).

## CINDERMOOR: a smithing town stepped up the volcano

- **LOWER WARD (0).** The west gate is unchanged (edge y 20-21). This level
  holds the Hearth, a house, and hot springs that spill off the west edge.
  The road climbs side stairs (12,20-21) onto the WEST TERRACE (1).
- **WEST TERRACE (1).** An octagonal Bell Plaza (the bell and FOUNDER HALVARD)
  and the shop. The OLD QUARTER bluff (2) sits above it: side stairs at
  (12,7), and a 2-high face over the ward with stairs at (9,12-13).
- **RAIL CUT (0).** Mine rails run from the EMBER TUNNEL mouth (23,4) south
  to the slag yard, under the Iron Bridge. The MINER stands at the mouth.
- **FORGE WARD (1).** The Forge, Enid and a house.
- **ANVIL CRAG (3).** A 2-high face with stairs at (38,10-11) leads up to the
  ANVIL HALL (door 34,7) and the hall crier.
- **SLAG YARD (0).** Both terraces drop into it by ledges (17-18,28 and
  28-30,29); there are also stairs at (16,28) and (36,26). The rails tip ore
  into a lava pool that runs off the south and east edges. The lava river
  runs down the whole east side from the north edge.
- **Doors:** Hearth 5,18; Shop 15,12; Forge 29,16; Anvil Hall 34,7; Ember
  Tunnel 23,4. **Fly point:** 19,19. **Signs:** 2,19; 30,8; 25,6.

## DREAMSPIRE: rings rising to the Mirror Hall

- **GARDENS (0).** The south gate is unchanged (edge x 24-25). The moon pond
  spills off the south-east corner, and the moonpetal meadow (wild kin) has
  the DOZING BOY.
- **GRAND STAIR.** A 2-high staircase (24-25,25-26) climbs from the
  semicircular plaza (fly point 24,29) straight up the wall to the octagonal
  LANTERN TERRACE (2). The SLUMBAKU statue and the DREAM READER are there.
- **LOWER RINGS (1).** Hearth 5,21 and shop 9,27 on the west ring; a tower
  and a house on the east ring. Side stairs lead up to the terrace at (13,20)
  and (34,21). Ledges drop into the gardens (17-19,31 and 35-36,29).
- **SLEEPERS' LANE (1).** Runs east-west between the terrace and the north
  blocks, under the Dream Bridge. POET ISOLDE sits by the bridge at (21,14).
- **TUNNEL.** Runs from the lantern walk under the terrace to the lane; its
  mouth is at (16,25).
- **NORTH BLOCKS (2).** Stairs at (8,13) and (38,13). This level has the
  towers and the DUST LIBRARY (door 39,8), and the CROWN (3) with the MIRROR
  HALL (door 24,7, stairs 23-24,10).
- **Signs:** 22,39; 35,9; 20,8.

## SKY ISLE: islands over the clouds

The clouds are height 0, so every island's cliff hangs over them. FLY lands
you on the LANDING (1) at 17,21, where the new WIND WATCHER stands. The WIND
WALK (1) runs north under the Stone Span to the NORTH TERRACE (1). A 2-high
staircase (17-18,7-8) climbs to the SUMMIT (3), where the SKY ARCH and
`OBJ(LEGEND, 17, 4, SP_SKYLORN)` are. The WEST and EAST SPIRES (2) are
reached by `v` stairs at (10,12) and (25,12). The Stone Span joins them, and
ledges drop from both spires back onto the landing.

## Files

- `src/game/world/far/data.h`: the CINDERMOOR and DREAMSPIRE sections (rows,
  `_ELEV`, `_FEATS`, stamps, decor). The Exits comment was updated. No other
  map section was touched.
- `src/game/world/far/maps.inc`: new widths and heights, plus `ELEV(...)`
  for both towns.
- `src/game/world/far/`: `warps.inc`, `npcs.inc` (2 new NPCs: OLD SOAKER and
  NIGHT GARDENER), `signs.inc`, `satchels.inc` and `flypoints.inc` hold the
  new coordinates.
- `src/game/world/north/data.h`: only the SKY ISLE section. `maps.inc` (the
  Sky Isle entry), `flypoints.inc` (17,21), `npcs.inc` (WIND WATCHER,
  appended) and `satchels.inc` (ASTRAL SHARD, appended).
- `tools/make_media.py`: the town-clip start cells for the 3 towns.
- No tileset, art, decor kind or test file changed. The towns reuse
  existing terrain and decor, so tile budgets are unchanged.

## Notes and leftovers

- The maps were drawn with a scratch painter (not committed). `data.h` is now
  the source of truth: edit the `_ROWS` and `_ELEV` arrays by hand. The rules
  from ELEVATION.md apply: write the lower digit on face rows and keep them
  free of decor, trees and people.
- Border trees and crags stop at face rows, so there are a few single tree
  tops on a cliff lip (for example Dreamspire (0-1,12)). That is intentional.
- The volcanic bridge deck uses the shared wooden deck art. An iron deck
  (ELEVATION.md section 8 roles) would suit Cindermoor better.
- The Sky Isle satchel is appended to the north list, so it shifts the global
  satchel index of every later region by one. That only matters for
  "taken" bits in old dev saves.
- The Cindermoor hidden pocket uses crag bottoms (`t`) on row 0, with the
  out-of-bounds crag tops above them.
