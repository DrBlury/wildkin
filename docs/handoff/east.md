# W-EAST handoff (Copperline Road, Lumen City, Volt Hall, lairs)

## Done

- **Tileset** `tools/tilesets/ts_city.py` (310 tiles, 11 building stamps).
  `USES_DECOR` now also pulls in BRIDGE_H/V, FOUNTAIN, FLOWER_POT and PLANTER.
- **Decor** `tools/decor_east.py` (25 kinds, registered in
  `gen_field_gfx.all_decor()`):
  - city: CITY_LAMP, TESLA_COIL (animated), PARKED_BIKE, CAFE_TABLE, RAILING,
    BEACON (2x3, animated plaza centrepiece)
  - Copperline (wild): MINE_MOUTH (3x2), RAILS_H/V, ORE_CART, ORE_PILE,
    COPPER_ROCK, HEADFRAME (2x3)
  - Elderwood (wild): ELDER_TREE (3x3, `ground_ok` for its dense crown), FERN,
    GLOWCAPS (animated), STAG_ALTAR
  - interior: PYLON (animated), RESONANCE_COIL, ENERGY_VAT (animated),
    DYNAMO, BIKE_DISPLAY, GEARS, FILE_CABINET, VOLT_BANNER
- **Maps** (`src/game/world/east/data.h`; exits documented in its header):
  - COPPERLINE ROAD 44x36: old copper mine (adit, headframe, rails, ore yard),
    prospectors' camp, pond, ledge, 4 wardens (Lv 15-18), miner, 5 satchels,
    berry patches 0-1.
  - LUMEN CITY (redesigned 56x50 on four levels: docs/handoff/towns_east.md; first pass:) walled city, market square with the
    BEACON, canal with 3 bridges, cafe gardens, LUMEN PARK (wild zone),
    11 stamps, 7 people, warden ARLO, fly point (lands at 7,17).
  - ELDERWOOD HEART 40x34: the Elder's glade, `OBJ(LEGEND, 18, 25,
    SP_SYLVARCH)`, grove keeper, 2 wardens (Lv 31-33), berry patches 2-3.
  - Interiors: LAND OFFICE (REEVE, SCR_REEVE), LUMEN HEARTH HALL (MF_HEAL,
    SCR_TENDER), LUMEN MARKET (own stock), VOLT HALL (15x17 puzzle), RESONANCE
    WORKS (SCR_FUSION_DESK behind a counter, lower floor left free for the
    fusion machines), BIKE SHOP, COPPER KETTLE INN (innkeeper + SCR_CHEF by a
    STOVE), LUMEN HOUSE, TINKER'S HOUSE, CLOCKWORK SPIRE (gear hall + Crown,
    stair sealed by `OBJ(BOULDER, 6, 9, 0)`, `OBJ(LEGEND, 6, 3,
    SP_HOROLOGOS)`, warden COGSWORTH Lv 38-40). New ids: MAP_LUMEN_INN,
    MAP_LUMEN_HOUSE_B.
  - Volt Hall: pylons are decor; barriers/switches are `OBJ_BARRIER` /
    `OBJ_SWITCH` (arg = group), design as before (a 4,13 / b 3,9 / c 11,9,
    trap b at 5,6). 4 wardens (Lv 19-22) and MASTER FARA (6 SPARK kin, Lv
    21-24) via `battle_start_master`, scene BSCENE_CITY. The win sets
    FLAG_VOLT_CREST, `travel_award_crest(CREST_VOLT)`, finishes
    QUEST_VOLT_HALL, unlocks LORE_VOLT_CREST, gives 2 SWIFT COIL.
- **Scripts/quests/lore**: miner, market, BIKE errand (OTTO -> VEX -> OTTO,
  QUEST_BIKE_ERRAND, `give_item(ITEM_BIKE)`), tinker, inn (50c rest), hall
  guide (hints), FARA, grove keeper, clockmaker. 12 Lorebook entries
  (places, METAL type, energy, halls, the two legends), 7 lore sources.
- **Bramblewood boulders**: `WOOD_OBJS` (30,33) and (31,33), defined in
  east/data.h and referenced from Bramblewood's MapDef.
- **Land Office** in Maple Village: HOUSE_RED stamp at (22,22), door (24,25),
  wall sign at (23,25).
- **Tests** `tools/tests/test_east.c`: edge contracts, every door both ways,
  walking in/out of the hall, region reachability, the Spire stair, Volt Hall
  BFS (gated, solvable, 946 states, no soft-lock, a-b-c works), people limits,
  teams, lore sources, the BIKE errand, the market stock, the inn, FARA's
  master bout and crest. `make art && make && make test` are green.
- Checked in the ROM (`build/shot`, debug WARP): Lumen and the Volt Hall.

## Shared files edited (minimal)

- `tools/gen_field_gfx.py`: one line in `all_decor()` (decor_east).
- `src/game/world/village/data.h`: one STAMP line (Land Office) and a PEBBLES
  decal moved from (25,25) to (28,25) (it sat on the new building).
- `src/game/world/village/maps.inc`: Bramblewood's MapDef gets
  `WOOD_OBJS, NOBJ(WOOD_OBJS)`.
- Regenerated: `src/gfx_field.h`, `src/game/world/debug/*`.

## Left / for other owners

- **Traversal**: barriers, switches, boulders, legends and berries are data
  only until `travel_attr` / `travel_dyn_cell` / `obj_interact` exist. Once
  barriers are solid, the core reachability test (tools/test_field.c) must
  flood the Volt Hall and the Spire in "puzzles solved" mode (test_east.c
  already models the switches itself).
- **Clockwork Spire location**: the contract diagram and the town-map SPOTS
  (gen_travel_gfx, 206,112) put the Spire by CINDERMOOR, but Cindermoor
  (W-FAR) has no south exit. Its door is the CLOCK_TOWER in Lumen (48,7).
  Either move the SPOT next to Lumen or W-FAR adds a door warp to
  MAP_CLOCKWORK_SPIRE (then the exit mat returns to the nearer door).
- Craft: no COOKTOP/station decor exists yet; the inn has a STOVE next to the
  cook. Fusion: machines decor can go on the Works' lower floor (rows 4-8).
- `party.c` has 6 pre-existing unused-function warnings (UI owner), not ours.
