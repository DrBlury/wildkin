# North region: handoff (W-NORTH)

## Done

- **'snow' tileset** (`tools/tilesets/ts_snow.py`, 349 tiles, 150 metatiles):
  snow ground with footprint and kin-track variants, drifts with frosted
  grass (A_GRASS, top layer hides legs), trodden-snow path autotile, animated
  icy-water autotile, snowy pines as transparent overlays, icy ledges (+ ends),
  snow-capped granite cliffs and cliff faces, crags, slate cobbles, ice
  (A_ICE) with a 9-slice snowy rim (numpad legend 7 8 9 / 4 6 / 1 2 3),
  rocks frozen into ice, a sea of clouds, and Rime Hall interior terrain
  (flagstones, ice-brick walls, exit mat, void). Stamps: HOUSE, HEARTH,
  SHOP, BATHS (5x4 log houses with snowy roofs and warm windows), HALL
  (7x5 Rime Hall), CAVE (3x2 cave mouth). Legend is documented at the top
  of ts_snow.py. Art lint passes.
- **Palette** (`tools/north_palette.py`): all north colours and the bank
  layouts for 'snow' and 'cave'.
- **Snow decor** (`tools/decor_north.py`, registered): SNOWMAN,
  ICE_CRYSTAL, ICE_BLOCKS, HOT_SPRING (4x3 animated pool), STEAM,
  WOLF_STATUE, AURORA_STONE, FROST_BANNER, ICE_STATUE, RIME_PILLAR, SKY_ARCH,
  SLED, SKI_RACK, FROZEN_TREE, WASH_BUCKET, with examine lines. The snow
  tileset also reuses 36 village props (USES_DECOR).

## In progress

- **Cave decor** is written in decor_north.py (CAVE_CRYSTAL, AMETHYST,
  CRYSTAL_PILLAR, STALAGMITE, GLOWCAP, MINE_CART, ORE_ROCKS, MOONBEAM,
  MOTH_DAIS) but held out of the catalogue (`NORTH_DECOR` filters out
  'cave') until the real cave tileset exists; its banks are already planned
  in north_palette.py (CAVE_BANK_*, CAVE_DECOR_BANK).
- **Art review**: the hot-spring mark on the BATHS stamp reads poorly
  (redraw as a bowl with three steam curls); CLOUD and CRAG look alike.
- **Preview tool**: a map/tile renderer based on tools/fieldmap.py was used
  from the scratchpad (not committed); tools/render_maps.py is outdated
  (reads the old src/game/maps.h).

## Not started

- `tools/tilesets/ts_cave.py` (still the placeholder copy of 'wild').
- All maps: FROSTPINE PASS, FROSTHOLLOW, WHITECROWN PEAK, SKY ISLE, the
  Frosthollow interiors (Hearth Hall, Frost Shop, houses), RIME HALL ice
  puzzle, HOT SPRING, GLIMMER CAVERNS 1/2, STARFALL GROTTO. The placeholder
  maps are still in src/game/world/north/ (borders switched from `T` to `P`
  so they stay solid under the new snow legend).
- NPCs, wardens and teams, the Hall Master + crest award, scripts (frost
  shop stock, chef, Tender), signs, satchels, wild zones (day/night slots),
  lore (6-10 entries), 2 quests, fly points (FROSTHOLLOW, SKY ISLE), berry
  patches 20-29, legends (OBJ LEGEND for HOARFANG, SELENOTH, SKYLORN),
  the STRENGTH boulder on Whitecrown.
- tools/tests/test_north.c (ice-puzzle solver, floor-to-floor cave
  reachability, lore/quest wiring, warden teams).

## Notes

- **Build/test status**: `python3 tools/gen_field_gfx.py` runs clean
  (regenerated src/gfx_field.h and the asset viewer maps). `make` and
  `make test` were NOT run after the last changes.
- **Edits outside my folder**: one line in `tools/gen_field_gfx.py`
  `all_decor()` registering decor_north (allowed by the brief); new files
  tools/north_palette.py, tools/decor_north.py; tools/tilesets/ts_snow.py
  rewritten. Generated files changed: src/gfx_field.h,
  src/game/world/debug/*.
- **The worktree branch started at the old base (89bf1cb)**; it was reset
  to the expansion base 6118872 before any work.
- **APIs relied on / expected from other systems**:
  - Traversal: A_ICE sliding, MF_DARK light circle, OBJ_LEGEND /
    OBJ_BOULDER / OBJ_BERRY behaviour (`obj_interact`, `travel_attr`),
    FLY to the SKY ISLE with the RIME crest, `travel_award_crest(CREST_RIME)`.
  - The Sky Isle is reachable only by FLY; the core reachability test in
    tools/test_field.c has no fly-point entries, so the Sky Isle map must
    carry no NPCs, signs, satchels, door warps or wild zone unless that test
    learns to start from fly points.
  - Battle: TEAM_MAX is 3 and `team_from` copies 3 kin, so a Hall Master
    with 5-6 kin currently fights with the first 3.
  - Time: `WildSlot.when` (day/night) is not read by `roll_wild` yet.
