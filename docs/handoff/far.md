# W-FAR handoff (Cinder Road, Cindermoor, Ember Tunnel, Caldera Heart, Moonveil Path, Dreamspire, Dust Library)

## Done

`make art && make && make test` is green (the only compiler warnings are the pre-existing unused
`storage_*` functions in `party.c`, not mine).

- **Art**
  - `tools/terrain_far.py`: volcanic terrain (unchanged) plus the dream terrain: moon grass (3), moonstone
    flagstones (2), moonpetals (wild grass with a front layer), moonflowers, blossom tree overlay, pastel
    cliffs and ledges, the animated moon pond, moonstone gravel paths, Mirror Hall floor / star inlay / walls /
    mat, Dust Library boards / shelves / paper-dust "grass" / mat.
  - `tools/far_buildings.py`: `dream_stamps()` (hearth, shop, 2 houses, 2 stacked towers, MIRROR HALL with a
    spire, DUST LIBRARY) and `DREAM_DOORS`. Tower roof eaves end on the 8px grid (bank fit).
  - `tools/tilesets/ts_dream.py`: the real tileset (293 tiles, 8 banks documented at the top).
  - `tools/decor_far.py`: 13 volcanic decor kinds (STEAM_VENT, OBSIDIAN, EMBER_ROCK, ORE_CART, FORGE_ANVIL,
    FURNACE, BIG_BELL, BRAZIER, COAL_PILE, TOOL_RACK, SALAMANDER_STATUE, SMOKE, HALL_BANNER) and 10 dream kinds
    (MOON_LANTERN, FLOAT_PAGES, BOOK_PILE, READING_DESK, BOOKCASE, MOONSTONE, PETALS, STANDING_MIRROR,
    DREAM_STATUE, SCRIPT_PEDESTAL), several animated, all with examine lines.
- **Maps** (`src/game/world/far/`, legend in the `data.h` header; edge contracts kept and tested):
  CINDER ROAD (lava lake, ember brush, hot spring, rails, ledge), CINDERMOOR (hearth, shop, forge, Anvil Hall,
  houses, the bell plaza, cave mouth), CINDER HEARTH / CINDER SHOP (interior), THE FORGE and ANVIL HALL
  (volcanic), EMBER TUNNEL (lava tube, ember moss, rails, 2 STRENGTH boulders, `MF_DARK`), CALDERA HEART (lava
  lake, `OBJ(LEGEND, 9, 7, SP_CALDERON)`), MOONVEIL PATH, DREAMSPIRE (hearth, shop, towers, MIRROR HALL, DUST
  LIBRARY, pond, moonpetal meadow), SPIRE HEARTH / SPIRE SHOP, MIRROR HALL (4 rooms, 5 pad pairs), DUST
  LIBRARY (`OBJ(LEGEND, 11, 2, SP_SCRIPTORA)`).
- **Anvil Hall puzzle**: 3 chambers behind 2 gates; 4 pumice boulders (arg 1), plates/gates grouped by arg
  1 and 2. `test_far` proves it solvable with a Sokoban search, and that the gates are the only way through.
- **Mirror Hall**: A -1-> B -2-> C -4-> D (Master); C's pad 3 is a decoy back to A, D's pad 5 goes home.
- **People**: 16 wardens (≤ 4 kin) + Hall Masters BRONWEN (6 kin, ANVIL CREST) and VESPER (6 kin, DREAM CREST)
  via `team_from` + `battle_start_master`; on win: `travel_award_crest`, `FLAG_CREST_*`, lantern rewards.
  Tenders, clerks (`shop_open_stock` with per-town stock), SMITH DAGNY (`SCR_SMITH`, craft's), miners,
  stargazer, poet, sleepers, kids.
- **Quests**: IRON FOR THE BELL (3 IRON ORE → METAL SHARD + 1500c; 3 ore satchels on the road and in the
  tunnel) and THE DRIFTING VERSES (3 sleepers on 3 maps → MOONCAKE ×3, LURE INCENSE ×2).
- **Lore**: 14 entries from 9 sources (PLACES, LEGENDS CALDERON / SCRIPTORA, HALLS, TYPES METAL, CRAFTING
  forging, BIOLOGY basalt/glass and dream fields).
- Signs (10), satchels (13), fly points (CINDERMOOR 204,88; DREAMSPIRE 166,48), 5 wild zones (levels 24-36,
  day/night slots, SLUMBAKU at night in Dreamspire, LAMPJINN in the library).
- `tools/tests/test_far.c` (37 checks).

## Left / notes for other owners

- **Traversal** must implement: OBJ_BOULDER arg 1 = pushable without STRENGTH, arg 0 = needs the ANVIL CREST;
  PLATE/GATE by group; PAD pairs by arg; OBJ_LEGEND starts the static encounter (CALDERON, SCRIPTORA). Until
  then the objects are invisible and non-solid, the legends can't be met, and the halls can be walked through.
  When gates/boulders become solid, `test_field`'s plain flood will fail on the ANVIL HALL (Master behind
  gates) and the EMBER TUNNEL arch; it needs a "puzzles solved" mode.
- **Craft**: SMITH DAGNY uses `SCR_SMITH`; the forge decor is my FURNACE / FORGE_ANVIL, so `station_examine`
  should accept `DK_FORGE_ANVIL` (or place craft's own ANVIL decor in `FORGE_DECOR`).
- The BIG_BELL's examine text always says "cracked", even after IRON FOR THE BELL.
- LCH_PLACES gains 5 entries; with every region adding places it may pass the Lorebook's 40 per chapter.
- `data.h` was produced by a scratch generator (not committed); it is plain C now, edit it by hand.
- Art polish ideas: bigger cliff features on Moonveil, a proper bridge tile over lava.

## Shared files edited

- `tools/gen_field_gfx.py`: one line in `all_decor()` registering `decor_far.FAR_DECOR`.
- `tools/tests/harness.h`: `flood()` follows OBJ_PAD pairs (same arg, same map).
- Regenerated (by `make art`): `src/gfx_field.h`, `src/game/world/debug/*`.

## Routes: REGION-FAR plan 05, parts A and B (branch `plan-routes-far`)

Append-only IDs add CINDER CROSSING (60x36), RAILHEAD (40x30), its BUNK,
OFFICE and collapsed SHAFT, MISTFEN (48x60), and PILGRIM REST (13x9).
Cinder Road W now points to Railhead; Moonveil S points to Mistfen. The Far
ends of Lumen E (y20-21) and N (x24-25) are in place; East owns the two
reciprocal Lumen links. Both routes have stop interiors, healers, wardens,
satchels, berry objects, songs via the automatic scene/music map, and wild
zones. The Cinder river x6-9 separates the bank from Railhead on foot;
SURF traverses it. The Railhead shaft door takes one STRENGTH push in the
real puzzle solver. Mistfen has a sealed fog wall on rows 52-54 and a
teaser sign/pilgrim on its southern side. Existing Act IV/VII wild levels,
Hall Masters, and route wardens are re-levelled to contract bands.

**Outstanding integration, not silently implemented:**

- E5's `MapPatch` is absent at checkpoint ca6a672. The guarded definitions
  in `far/data.h` specify the exact intended overlays: G3 repaired bridge
  `(6,20,4,2)` on `FLAG_PROJECT_CINDER_BRIDGE`; G6 open path
  `(24,52,2,3)` on `FLAG_LANTERN_CREST`. The project flag belongs to saga
  plan 10 and does not exist yet. Wire the arrays into `MapDef` after E5
  establishes its final field ordering; the pre-E5 build intentionally
  keeps G6 **closed** and G3 **SURF-only**. Remove `FAR_HAS_E5_PATCHES`
  guarding once the patch ABI and project flag are available. Greta's script
  currently describes the project but cannot call missing
  `saga_project_offer(PROJ_CINDER_BRIDGE)`; wire the actual offer when saga
  lands. Do not reinterpret her current dialogue as a completed project.
- E3 NPC conditions are also absent. If fog blockers need visibility
  conditions, add them only after E3 lands; the physical wall is closed now.
- No `battle_start_double` or double-warden API exists. The spa friends and
  dream twins are paired adjacent single bouts, not a genuine double bout.
  The static FOUNDRAKE uses existing `OBJ_LEGEND` encounter semantics; its
  level is `clamp(party_max_level()+4,30,60)`, **not** fixed Lv32. This must
  be changed by the owner of static encounters to satisfy the plan.
- The loop maps `MAP_SCORCHWASTE_1` and `MAP_AURORA_RIDGE_2` are not in this
  checkpoint. Cindermoor S and Dreamspire cave warps, plus their flag gates,
  await plan 08 IDs. Dust Library's postgame SCRIPTORA lock likewise awaits
  E5; do not add a gate that could strand the player.
- Hidden satchels, TELEPORT mirror return, three-switch fog puzzle, bridge
  construction, optional quests/locale lore, elevated Crossing bridges and
  one-way Road ledge are not in this commit. Add them with the engine/loop
  APIs once available; do not claim plan 05 is fully complete.

**Validation in this isolated worktree:** `test_far` passes, and
`test_puzzles` finds the Railhead shaft door (1 push) and all targets on
Railhead/Mistfen with its all-abilities/entry-union model. `test_field`
passes row widths, decor and scene tile budgets, edge landings and door
terrain. It fails reciprocal links until East re-points Lumen and its
closed-fog Mistfen reachability check (the solver's entrances/patch states
need E5). Its save/load checks also fail when run standalone because the
checked-in generated save layout still describes pre-append counts; no
shared generated files were edited here. Run `make test` after integrating
E3/E5, East, saga and regenerated save layout.

### LINKS integration reservation (plan 08)

No dangling edge or warp was inserted: this checkpoint has neither
`MAP_SCORCHWASTE_1` nor `MAP_AURORA_RIDGE_2`, and E5's flag patch mechanism
is not installed. Exact Far-side edits when plan 08 and E5 merge:

1. **Cindermoor south:** keep x20-21 as the *only* south edge opening.
   `CINDERMOOR_ROWS` y38 and y39 currently have solid `T/t` at those
   columns; turn x20-21 on both rows into `=` once `MAP_SCORCHWASTE_1`
   exists, and set `MAPS[MAP_CINDERMOOR].link[LINK_S]` to that map.
   Cindermoor's elevation at x20-21,y36-39 is level 0, so no stair or
   `link_off` is needed. Gate the approach with an **inverted** E5 patch
   on `FLAG_LANTERN_CREST` (heat-haze vent wall over x20-21 on y37,
   clear only after the crest), then assert closed/open traversal and
   walkable landing on `MAP_SCORCHWASTE_1` N x20-21. Plan 08 owns that
   northern reciprocal link and opening. Make sure the closed wall does
   not block the way home from the Scorchwaste side.
2. **Dreamspire west cave:** reserve `DREAMSPIRE` (2,18) as the door tile;
   approach from (3,18) is level 1 and presently open. Add a DREAM
   cave-mouth stamp/door registration in `far_buildings.py` and
   `ts_dream.py`, set a Far-owned warp
   `{ MAP_DREAMSPIRE, 2, 18, MAP_AURORA_RIDGE_2, <east-cave-x>, <east-cave-y> }`
   after the loop's east-cave coordinates are published, and gate the
   Dreamspire approach on `FLAG_CREST_DREAM` with E5 or an equivalent
   flag-aware barrier. Plan 08 owns the reciprocal cave warp and its own
   gate. This must **not** become a Dreamspire west edge link; its
   `link[LINK_W]` stays `MAP_NONE` to avoid an edge cycle.
