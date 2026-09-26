# W-WEST handoff (Saltwind Trail, Port Brine, Current Hall, Sea Route, Gull Isle, Drowned Bell)

## Done
- Nothing in `src/game/world/west/` has changed yet: the maps, NPCs, wardens,
  scripts, lore, quests, fly points and zones are still the base placeholders.
- Worktree branch fast-forwarded from `main` to the `expansion` base (6118872).

## In progress
- `tools/tilesets/ts_coast.py`: first full draft of the real 'coast' tileset.
  - Banks: 0 ground, 1 sea/sand, 2 trees/cliffs, 3 village prop bank (for
    reused decor), 4 red roof, 5 blue roof, 6 walls, 7 grotto.
  - Terrain: grass, tall grass, marram dune grass (A_GRASS), sand x3, plaza
    slabs, quay setts, rock shelf, tide pool, salt pan, cliff, ledges, dune
    ledge, pines, palms; Current Hall floor/walls/porthole/exit mat/deep pool;
    four animated currents; grotto rock, floors, temple slabs, glowing pool
    (animated), exit steps, void.
  - A sand-edged, foam-lapping water autotile.
  - Stamps: HEAL, SHOP, HOUSE_RED, HOUSE_BLUE, HARBOR, INN, HALL (7x5 Current
    Hall), HUT (thatched), CAVE (cliff cave mouth with a door).
  - The legend is documented at the top of the module.
  - `USES_DECOR` lists the existing props to reuse. Their colours are not
    verified yet.
- **Broken:** `python3 tools/gen_field_gfx.py` currently fails.
  - Error: `coast: tile INN[2,2] colors [... rb_dkr, wd_lt ...] fit no bank`.
  - Cause: the GULL INN sign ink `rb_dkr` shares a tile with the wooden
    frame.
  - Likely fix: ink `gl_dk` (like the other signs), or keep the sign off the
    beam.
  - Nothing was regenerated. `src/gfx_field.h` and the debug viewer maps are
    unchanged, so `make` and `make test` still build from the old header.
  - Next steps after the fix:
    - check the tile budget (tileset must stay well under about 380 tiles so
      maps can add decor)
    - check the `USES_DECOR` colour fit
    - preview the tileset

## Not started
- `tools/decor_west.py` has not been written or registered in
  `gen_field_gfx.all_decor()`. Planned props:
  - piers, posts and bollards
  - fishing and ferry boats
  - the lighthouse (as decor), gull posts, nets, lobster pots
  - fish stall, anchor, lifebuoy, shells, starfish, seaweed, driftwood, sea
    rocks, salt heaps, bell buoy
  - Hall: columns, shell lamps
  - grotto: the drowned bell, pillars, glow coral, whale carving
  - Gull Isle: whale-bone arch
  - interiors: ship wheel, fish trophy, ship in a bottle
- All maps:
  - SALTWIND TRAIL: 56x40, east exit y 31-32 (contract), west exit to Port
    Brine planned at y 19-20.
  - PORT BRINE: 56x48.
  - SEA ROUTE: 40x48.
  - GULL ISLE.
  - DROWNED BELL: grotto with `OBJ(LEGEND, x, y, SP_NOCTHALE)`.
  - Interiors: hearth, shop, harbor office, inn with SCR_CHEF, house.
  - CURRENT HALL: TS_COAST interior with a current network.
- NPCs, wardens:
  - 4-8 route wardens with ≤3 kin each.
  - 3-4 Hall wardens.
  - The Hall Master's 6-kin team. `TrainerTeam` / `TEAM_MAX` are still 3, so
    copy only `sizeof(tt.species)` kin.
- Scripts:
  - BRINE SHOP with `shop_open_stock`.
  - Master win: `travel_award_crest(CREST_TIDE)`.
  - Harbour master / ferry: 500c or FERRY PASS, then `travel_boat_to`.
- Two quests:
  - Harbour post delivery that ends with the FERRY PASS.
  - Gull Isle salt / sandbar quest.
- Also not started:
  - 6-10 lore entries.
  - Fly points.
  - Berry patches (ids 10-19).
  - Wild zones: Saltwind, sandbars, ISLE, and a sea water zone with KELPYRE
    at night about 2%.
- `tools/tests/test_west.c`.

## Notes
- **Build and tests:**
  - `make` and `make test` were green at the base before this work.
  - The only change since then is `ts_coast.py`, and the generator is broken
    by it (see above). The committed generated files are still the base ones.
- **Edits outside `src/game/world/west/`:** only `tools/tilesets/ts_coast.py`
  (owned) and this file.
- **A_CURRENT convention (proposed; documented in `ts_coast.py`):**
  - Direction = `(A_DIR_HI << 1) | A_DIR_LO`: 0 down, 1 up, 2 left, 3 right,
    the same order as field.c `DIR_*`.
  - Current cells are walkable (not SOLID).
  - Stepping onto one carries the player one cell per step in the direction
    of the cell they stand on, until they reach a non-current cell or the way
    ahead is blocked.
  - Still hall pools are SOLID | WATER | DEEP.
- **Reachability test (needs a decision):**
  - The harness `flood()` in `tools/test_field.c` is walk-only, so a
    surf-only Sea Route fails the reachability check.
  - Plan: treat surfable water (A_WATER without A_DEEP) as open on maps with
    `MapDef.water_zone` set. That is a small edit to `tools/tests/harness.h`,
    to agree with the traversal owner.
  - The alternative is walkable sandbars through the Sea Route, which would
    make the boat pointless.
- **APIs relied on:**
  - `travel_boat_to`, `travel_award_crest`, `quest_set` / `quest_get`,
    `shop_open_stock`, `lore_reveal` / `lore_story`, `give_item`
  - SCR_TENDER, SCR_CHEF
  - OBJ_LEGEND, OBJ_BERRY
  - Traversal to implement currents, surf and the water-zone spawns per the
    convention above.
- **Local tools:**
  - `tools/render_maps.py` is stale: it reads the removed
    `src/game/maps.h`.
  - A working region renderer (fieldmap-based) is kept in the session
    scratchpad (`render.py`). It is not committed.
