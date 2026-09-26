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
