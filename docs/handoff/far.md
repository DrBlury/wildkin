# W-FAR handoff (Cinder Road, Cindermoor, Moonveil Path, Dreamspire)

## Done

- The worktree is fast-forwarded to the expansion base (6118872).
- Nothing in `src/game/world/far/` has changed. The placeholder maps are still in place, and there are no NPCs, wardens, quests, lore or puzzles yet.

## In progress

- **Volcanic tileset art** (Python only; not wired into the build yet):
  - `tools/terrain_far.py` holds FAR_COLORS for both tilesets and the volcanic terrain:
    - ash (3 variants), columnar basalt (2), dressed basalt setts, sulfur crust
    - ember brush (wild-kin grass with a front layer), basalt column cliff with an ash lip, and plain cliff face
    - one-way ash ledges (plus left and right ends), mine rails running each way
    - crag spires and charred trees (16x32 overlays)
    - cave floor, wall, face, exit mat and ember moss
    - Anvil Hall iron deck, vent, brick walls and exit mat
    - animated lava as 16 pieces (legend is a numpad: `5` is the centre, `7 8 9 4 6 1 2 3` the edges and corners, `q p b n` the inner corners, `- |` one-cell streams, `o` a pool)
    - an animated hot spring (the tileset's WATER) and cinder-gravel path autotiles
  - `tools/far_buildings.py` has an animated autotile block helper and a bigger sign font. Its buildings are drawn in placeholder colours that get swapped for each tileset's real ones:
    - cottage (5x4): hearth with the flame emblem, shop, forge with two chimneys, house
    - hall (7x5): anvil, mirror or book emblem, optional spire
    - rock arch cave mouth / tunnel arch (3x2)
    - Dreamspire stacked tower (3x5) with hanging lanterns
  - `tools/tilesets/ts_volcanic.py`: the bank plan, terrain list, legend, attributes, stamps and door list are written.
  - **Current blocker:** `python3 tools/gen_field_gfx.py` fails. The `RAIL_H` tile's colours fit no bank: `rail_img` still uses `vb_out`, but bank 2 now uses `b_out`. Fix it by using `b_out` for the sleeper ends in `terrain_far.rail_img`. After that, iterate on any further bank or lint errors.
- The dream colours are defined in FAR_COLORS. The `tower()` stamp art exists, but `ts_dream.py` is still the placeholder (a copy of the wild tileset).

## Not started

- **`ts_dream.py` terrain:**
  - pastel stone, mint moon grass, moonpetal grass (wild-kin grass)
  - blossom tree overlays, moon pond, pastel cliffs
  - Mirror Hall floors and walls, Dust Library shelves
- **`tools/decor_far.py`:**
  - steam vents, obsidian, mine carts, smoke, anvil and furnace, lanterns, floating pages, mirrors, bookshelves
  - registering it in `gen_field_gfx.all_decor()` (a one-line change)
- **Maps and data:**
  - all 14 maps (`data.h` legend header, rows, stamps, decor, objects)
  - warps, signs, satchels, berry patches (ids 40-49)
  - wild zones: VOLC, DREAM and LIBRARY with day/night slots, levels 22-36, SLUMBAKU at night in Dreamspire
- **Puzzles:**
  - Anvil Hall pumice boulders, plates and gates
  - Ember Tunnel STRENGTH boulders
  - Mirror Hall pad maze
- **People and story:**
  - wardens and trainers, and Hall Masters with 5-6 kin that award CREST_ANVIL / CREST_DREAM
  - shop scripts using `shop_open_stock`
  - 2 quests: IRON FOR THE BELL (3 IRON ORE) and THE DRIFTING VERSES (3 dreamers' verses)
  - 10-12 lore entries
  - fly points for Cindermoor and Dreamspire
- **Tests:** `tools/tests/test_far.c`.

## Notes

- **Build and tests:** the C side is untouched, and `src/gfx_field.h` is still the base version (the generator stops before writing it). So `make` and `make test` stay as green as the base. Only the new Python art is mid-change. `python3 tools/gen_field_gfx.py` currently fails with the rail palette error above.
- **Edits outside `world/far/`:**
  - new files `tools/terrain_far.py` and `tools/far_buildings.py`
  - `tools/tilesets/ts_volcanic.py`, which is mine
  - no core files touched
- **Planned edit outside my folder:** `tools/tests/harness.h` `flood()` should follow OBJ_PAD pairs (same arg on the same map). Without it, the Mirror Hall's pad-only rooms fail `test_field`'s reachability check. The TRAVERSAL owner may make the same change, so coordinate with them.
- **APIs expected from other systems:**
  - **TRAVERSAL:**
    - OBJ_BOULDER with arg 1 should mean a "pumice" Hall boulder that can be pushed without STRENGTH. Otherwise the Anvil Hall can't be solved before its own crest.
    - OBJ_PLATE and OBJ_GATE: a gate is open while every plate of its group is covered.
    - OBJ_PAD teleports you onto the other pad with the same arg.
    - OBJ_LEGEND should start the static encounter.
    - `travel_award_crest`.
  - **BATTLE:** `TrainerTeam` and `TEAM_MAX` are 3 today, and `team_from` copies 3. Masters need 6.
  - **CRAFT:** `SCR_SMITH` is used for the forge smith.
  - **UI:** `quest_set` / `quest_get`, and the Lorebook chapter list (`lb.ids[40]` per chapter).
- **Test integration risk:** `test_field`'s flood ignores puzzles. Once traversal makes gates and boulders solid, the Hall and tunnel checks need a puzzle-aware flood.
- **Lava** is explicit solid terrain pieces, not WATER, because CELL_WATER is always surfable.
