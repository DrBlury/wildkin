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

## Routes — plan 03 (branch `plan-routes-east`)

**East-owned data prepared:** `MAP_BROOKMILL_TRAIL` (64x36 WILD), `MAP_BROOKMILL`
(40x36 TOWN), `MAP_BROOKMILL_MILL`, `_HOUSE`, `_REST` (Hearth/heal + shop),
and `MAP_COPPER_MINE` (36x28 CAVE, `MF_DARK`). IDs were appended in east
registries only. The old Copperline west link now leads to Brookmill; south
is `MAP_NONE` with a cabin door at **(20,34)** to `MAP_ACCORD_GATE` landing
(6,8). Lumen N points to `MAP_MISTFEN` at x24-25; Lumen E points to
`MAP_CINDER_CROSSING` at y20-21. The default G5 coordinate (20,35) would put a CABIN stamp door directly on
the map edge, with its only approach tile solid; (20,34) is the nearest
enterable door and needs grim to agree. These three destination map IDs are not yet
provided by the independent grim/far branches in this worktree.

**Route:** the Brook runs past the old toll bridge, a heron rookery, a west
ledge shortcut, north and south forks, a caravan clearing (51-54,10-12) and
an outbreak patch (45-52,25-26). Its elevation feature is a BRIDGE_H over a
lower towpath. Grass mix is Lv10-15 (uncommon QUILLDRUM); reeds/water mix is
Lv12-15 (rare KOIRIN). The engine currently chooses a wild zone per map or
while surfing (`water_zone`), not by reed terrain: the reed mix is assigned to
the Brook's water zone and needs a terrain-zone API to activate on dry reeds.
Wardens BESS, OAK, ASH, TAM and ROLF range Lv12-15; guild exhibition Lv15-16
and Mine Boss Lv18-19. OAK and ASH are adjacent paired wardens; there is no
current double-bout API to actually launch one joint bout. TAM guards a
GLOW HONEY satchel. Three route satchels (BIG TONIC, LANTERN x3, BLOOM SHARD),
the guarded honey, one-once LIGHT cache (GLOW LANTERN x3), mine IRON ORE x2,
mine LIGHT gallery METAL SHARD and SURF-islet TIDE LANTERN are placed.
Two hidden-examine satchels and a PRISM LANTERN item are not realizable with
current owned files: `ItemBall` is always visible, and PRISM LANTERN has no
item ID. The rookery cache uses a script NPC and the existing GLOW LANTERN.

**Hamlet:** four town stamps surround a raised millpond and an animated
waterwheel; the guild yard has timber, a cart, and a reserved tram lot
(33-37,29-32). The Hearth counter sells HONEY BUN as the available local
specialty (MILL FLOUR is not registered). ADA's GRIST quest consumes 3 CORN
or IRON ORE; Brookmill's kid rewards showing a party KOIRIN. Four new lore
entries cover the old toll, rookery, wheel and night music; a fifth covers
the copper rush. The fiddler is `WHEN_NIGHT`; Lumen market trader / night
watch are `WHEN_DAY` / `WHEN_NIGHT`. The Telegraph clerk shares TINKER'S HOUSE
until a dedicated Gazette office is approved. Lumen market stalls are
reserved. Two satchels are placed on the Crown, but FLY-only rooftop access
requires a distinct landing API; the second `FlyPoint` alone doesn't restrict
walking to these spots.

**Gates and scripting:** FARA sets `FLAG_VOLT_CREST`; only `scr_holt` sets
`FLAG_FEN_RIVETS` and accepts a previously held crest directly. Vex sets a
virtual `FLAG_RIVET_BUNDLE` after Volt. A real `ITEM_RIVET_BUNDLE` key item
cannot be added without permission for `src/game/items/east.inc` and central
item registration. G5 checkpoint warden belongs to grim/story; east supplies
its door and quarantine sign. G6 barrier belongs to far; east supplies the
pilgrim warning and sign. E5 data closes the mine side gallery until LIGHT
and Elderwood/Spire passages until `FLAG_OSSUREX_ANSWERED`. E6 east milestones
are in `milestones.inc` but need engine registration.

**Merge dependencies (do not patch these from the east branch):**

- `village/maps.inc`: WOOD E must be `MAP_BROOKMILL_TRAIL` instead of
  `MAP_COPPERLINE`; its east opening already uses y17-18.
- Grim: publish `MAP_ACCORD_GATE` with reciprocal exit and G5 RIME warden;
  north entrance from Copperline (20,34) lands at (6,8).
- Far: publish `MAP_MISTFEN` (S x24-25) and `MAP_CINDER_CROSSING` (W y20-21).
- Engine E3: expose `NpcDef.when`, default to `WHEN_ANY` and refresh scheduled
  NPCs; E5: expose `MapPatch`, `MapDef.patches` and `.patch_count`, apply
  inverted patches and refresh after flags. E6: concatenate east milestones.
- Story/E6: G1 blocker and progression solver are their owners' work.
- Town project owner: activate the tram lot; events owner: populate caravan
  clearing, outbreak patch and market stalls. No unsupported APIs were added
  to shared files in this branch.

**Validation:** `git diff --check`, Python syntax/import for `decor_east`,
in-memory `build_tilesets()`/`build_decor()` including the two-frame
waterwheel, and static row-width checks (Trail 36x64, Brookmill 36x40, mine 28x36,
and both elevations) passed. `make art`, `make`, `make test`, `build/shot`
and gameplay screenshots were **not run**: E3/E5 fields and grim/far IDs are
missing in this worktree. `tools/tests/test_east.c` was extended for the
expected integrated graph, scripts and gates; it is not executable until the
above merges. Screenshots: **none** (cannot build a current ROM without the
pending engine/neighbor APIs).
