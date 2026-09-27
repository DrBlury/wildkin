# 02 — Engine foundation for long routes, gates and a living world

**Work package:** ENGINE. **Blocks:** every other plan. Land this first and
merge it before region work starts.

**Owns:**

- `src/game/field.c`, `script.c`, `travel.c`, `quest.c`, `elev.c`,
  `world/world.h`, `src/save_game.h`
- `tools/test_field.c`, `tools/tests/harness.h`, the new
  `tools/tests/test_progression.c` and `tools/tests/test_save_ids.c`
- `tools/render_world.c`, `tools/make_media.py`

**Contract:** `docs/plans/01_progression_contract.md`.

**Gate:** `make art && make && make test` must be green, with zero warnings,
after every item below.

**Findings this plan builds on** (verified 2026-09-27; re-check the line
numbers before editing):

- Save version is **5** (`src/save_game.h:20`). `SaveData` is 14164 of
  16384 bytes.
- Every id is **positional** across the concatenated region `.inc` files:
  flags, satchels, wardens, quests, lore, maps, `travel.c` puzzle bits
  (`pbit_base`, `travel.c:174`) and hidden-passage bits (`elev.c:112`).
  Adding an id before the end of the list silently corrupts saves.
- `TravelState.visited[16]` holds 128 map bits, but `travel_map_entered`
  calls `bit_set(travel.visited, map)` with **no bound check**
  (`travel.c:1199`). There are 83 real maps and 54 debug maps; ids ≥128
  already write into the next field.
- **Edges are not seamless.** Every crossing is an 18-frame fade
  (`field.c:1626`), even though `docs/EXPANSION.md` claims otherwise.
- `NpcDef` (`field.c:91-100`) has **no visibility condition**: every NPC on
  the map is spawned. Scripts cannot move NPCs, and the camera always
  follows the player.
- Runtime map edits are possible but ad hoc:
  - `farm_dyn_cell` / `travel_dyn_cell` (the travel one is an empty stub,
    `travel.c:414`);
  - the `cell_attr` chain (`field.c:364`);
  - patching `map_cells` in `travel_map_loaded` and then calling
    `ring_invalidate`.
- `MF_SNOW` is set on maps but never read.

---

## E1. Stable save ids (BLOCKING, do first)

**Goal:** content plans can append ids inside their own region without
breaking existing saves.

**Design** (recommended):

1. Each region contributes a count per id kind: maps, flags, satchels,
   wardens, quests, lore, puzzle bits and secret bits.
   - Generate the table in C from the region `.inc` files, e.g. a
     `REGION_COUNTS` macro per region that `world.h` sums. A per-region
     `enum { ..._END }` sentinel also works.
2. **Save v6** stores this *layout manifest* next to the data: for each
   region and each kind, `u16 base` and `u16 count` at save time. At most
   ~20 regions × 8 kinds × 4 bytes = 640 bytes; about 2.2 KB is free.
3. On load, when the manifest differs from the ROM's, copy the bits
   **region by region**:
   - old `[base, base+count)` goes to new `[base', base'+min(count,count'))`;
   - map ids (the player's current map, the last Hearth, fly points,
     `visited` bits) go through the same remap;
   - the quest stages array (`quest.stage[]`) is remapped the same way.
4. **Puzzle and secret bits** are numbered per map in map order. Remap
   them per map with a per-map count table in the manifest. That costs
   1 byte per map, or 2 bytes to cover puzzle and secret bits both.
   If that is too costly, key them by a hash of (map name, object index)
   instead.
5. **Migration v5 → v6:** assume the v5 layout is exactly the region counts
   of the commit that lands E1. Freeze them in `save_game.h` as the
   `V5_LAYOUT` table.
6. Add a **`tools/tests/test_save_ids.c`** golden test:
   - it writes the current layout to `tools/tests/save_layout.golden`;
   - it fails if a region's count **shrinks**, or if any id **moved within
     its region**. Check the latter by hashing the id names per region, in
     order: a prefix must stay a prefix.
   - Growth is allowed; the test prints the new golden to commit.

**Acceptance:**

- A v5 save made on `main` loads.
- With 1 flag, 1 satchel and 1 warden added to `east` and 1 map added to
  `west`, all west, north and later flags, wardens and satchels read back
  unchanged.
- The test above covers this with a synthetic save.

**Fallback** (only if E1 is dropped): every new id goes into the new region
directories (`story`, `saga`, `links`, `events`, plus one new dir per
region, e.g. `east2`) listed after `ui` and before `debug`. Existing region
files may then never add ids. This makes region plans awkward. Avoid it.

---

## E2. Map id space and `visited`

- **Bound check.** Bound-check every `bit_set` / `bit_get` on map-indexed
  arrays (`travel.c:1199` and similar).
- **Widen `visited`.**
  - Widen it to 32 bytes (256 maps) by **appending** a `visited_hi[16]` to
    `TravelState` (cap `MOD_TRAVEL_MAX 256`; 49 bytes used).
  - Or move `visited` into the v6 layout from E1.
- **Move the debug and asset-viewer maps last**, so real maps keep low ids.
  After E1 this is harmless.
- **Budget.** About 35 new real maps, plus 54 debug maps, stays under 255
  (`MAP_NONE`).
- **Assert** `MAP_COUNT < 255` at compile time.

---

## E3. NPC conditions (show or hide people by flag, time and event)

We need this for gate blockers, the rival, festivals, the caravan, day and
night schedules, and NPCs who move town after a story beat.

**Add to `NpcDef`** (not saved, so the layout is free):

```c
u16 show_flag;   /* 0 = always; else visible only while flag is set */
u16 hide_flag;   /* 0 = never;  else hidden once flag is set        */
u8  when;        /* WHEN_ANY / WHEN_DAY / WHEN_NIGHT (reuse wild_slot_now)  */
u8  event;       /* 0 = none; else visible only while events_active(event)  */
```

**Macros.** Extend `PERSON`, `PERSON_KIN` and `WARDEN` in `world.h` with
defaulted variants (`PERSON_IF(..., show, hide)` and `PERSON_WHEN(...)`), so
existing `.inc` files compile unchanged.

**Runtime:**

- `npcs_reset` (`field.c:676`) skips hidden NPCs.
- Add `npcs_refresh()` so a script can re-evaluate visibility after
  `flag_set`, without re-entering the map. Call it from `flag_set`, or
  explicitly.

**Tests:**

- The reachability flood (`test_field.c`) must treat NPCs as present or
  absent according to the flag state under test. `test_progression.c` (E6)
  feeds the flag set.
- The 24-people and 7-sprite limits must hold for the **worst case**: all
  visible at once, or all visible for any single time window. Make the
  limit test global; today only east and west check it
  (`test_east.c:344`, `test_west.c:135`).

---

## E4. Scripted movement and camera (cutscenes)

We need this for:

- blockers who step aside when a gate opens;
- the rival who walks up to you;
- the caravan arriving;
- a festival parade;
- "follow me" guides.

**API** (`script.c`, callback style to match `dlg_*`):

```c
void npc_walk(int npc, const u8 *path, int n, void (*done)(int arg), int arg); /* path: DIR_* steps */
void npc_face(int npc, int dir);
void npc_warp_out(int npc);             /* fade/poof out, stays hidden until map reload or flag */
void player_walk(const u8 *path, int n, void (*done)(int), int arg);
void cam_pan_to(int x, int y, int frames, void (*done)(int), int arg);
void cam_follow_player(void);
```

**Rules:**

- Input is locked while any walk or pan runs.
- Walking respects solidity. It fails gracefully: a blocked step waits a
  few frames, then skips.
- A walk may not end on the player's cell.

**Tests:** in a headless script, run an `npc_walk` along an L-path and
assert the final cell and facing. Do the same for a camera round-trip.

---

## E5. Map patches (world edits driven by flags)

We need this for:

- the G2 boardwalk, the G3 bridge washed out and then rebuilt, and the G6
  fog;
- town projects (plan 10);
- event hazards (plan 09);
- the healed Ashen March.

**Data**, per region, in `data.h`, referenced from `maps.inc`:

```c
typedef struct {
    u16 flag;         /* applied while this flag is set (see invert) */
    u8  invert;       /* 1 = applied while the flag is CLEAR          */
    u8  x, y, w, h;
    const char *const *rows;   /* legend chars, same tileset as the map */
    const char *const *elev;   /* optional height rows (NULL = unchanged) */
} MapPatch;
```

**Add to `MapDef`:** `patches` and `patch_count`.

**Runtime:**

- `map_decode` applies active patches after decoding the rows, and before
  ground inference and elevation derivation.
- A `map_patches_reapply()` runs after a script sets a flag while you stand
  on that map: redecode the cells, `ring_invalidate`, and redraw with a
  short dip.
- Event patches (plan 09) use `event` instead of `flag`. Reserve a `u8
  event` field.

**Tests:**

- `test_field.c` decodes every map with every patch on and with every patch
  off. Rows must be the right width, and the map must stay within the tile
  budget.
- The reachability flood takes the flag set into account.
- The elevation lint (`test_elevation.c`) runs on patched maps too.

---

## E6. Progression solver test (`tools/tests/test_progression.c`)

This is the most important test in this effort. It proves the critical path
of contract §3–§4.

**Model.** The state is a set of story flags and crests, plus a party level
estimate.

- **Start:** after `FLAG_STARTER`.
- **Loop:**
  1. Flood-fill the reachable maps and cells with the real `cell_attr` and
     NPC visibility (E3), the active patches (E5), and the abilities that
     the current crests allow (SURF, STRENGTH boulders, the fog and so on).
  2. Collect every "milestone" reachable in that area: a Master, a story
     script that sets a gate flag, a key item giver.
  3. Apply the milestones in **contract order**, and repeat.

**Milestones.** Each region declares its milestones in a small table:
`{map, x, y, sets_flag, requires_flag}`. Use `world/<region>/milestones.inc`,
concatenated like the other `.inc` lists.

**Assertions:**

- **Reachability order:** for each act *N*, no map of act *N+1* or later is
  reachable before act *N*'s gate flag is set. Read the act membership from
  a contract table in the test that lists each map's act.
- **Completeness:** every map in the world is reachable once all flags are
  set. The only exceptions are the debug and test maps.
- **No soft-lock:** from every reachable state, a Hearth (`MF_HEAL` map) is
  reachable.
- **Level sanity:** check each zone's min/max against the contract §5 table,
  within ±1. The table lives in the test.

Print the act-by-act reachable map list when a check fails.

---

## E7. Transitions: faster edges, and seamless edges when the tileset matches

Long routes mean more edges, and an 18-frame fade on each one feels slow.

**Step 1 (cheap).** Where both maps share a tileset:

- cut the edge dip to about 6 frames out and 6 in;
- skip the banner re-slide when the location name doesn't change.

**Step 2 (real seamless).**

- When crossing into a neighbour with the same tileset, keep scrolling:
  1. stream the neighbour's cells into the ring buffer as the camera
     approaches the edge;
  2. swap `cur_map` when the player steps over;
  3. rebase the coordinates by the map size and `link_off`.
- NPCs and wild kin of the neighbour spawn on crossing.
- This needs the map streaming that `field.c` already uses for scrolling;
  check the "scroll written before map streaming" fix in commit 46d8468.
- **Constraint:** the palette banks of both maps must match. That is true
  for the same tileset, but check decor-driven palette differences.

**Acceptance:** walk Bramblewood → Brookmill Trail → Brookmill → Copperline
with no fade, and with no visible tear in `build/shot` frames taken on the
crossing.

---

## E8. Map authoring support for routes

1. **Gatehouse template.**
   - A reusable 13x9 interior layout (`TS_INTERIOR`) with doors on both
     ends and a guard desk.
   - Region plans copy it for route gates (contract G5, loop-route ends).
   - Document it in `docs/plans/templates/gatehouse.md`; create the file
     when you build the template.
2. **Route signs.**
   - A `SIGN_ROUTE(map, x, y, "BROOKMILL TRAIL", "<- MAPLE  BROOKMILL ->")`
     helper that formats a two-line signpost consistently.
3. **World render.**
   - `tools/render_world.c` + `make_media.py clip_world` must include
     warp-only areas (loop routes and gatehouse-linked maps). Add a
     `WORLD_POS(map, x, y)` hint table
     (`world/<region>/worldpos.inc`) that places a map relative to another
     when the BFS can't reach it by edges.
   - The BFS must detect and report overlaps instead of silently drawing
     one map over another.
4. **Town map.**
   - The UI town map has fixed pixel positions (`gen_travel_gfx.py`,
     "the Vale town map with pixel positions").
   - Add the new maps and hamlets, and make the positions data-driven from
     the same `WORLD_POS` table, so region plans don't touch the UI
     generator.
   - Hamlets get fly points only if they have a Hearth. Brookmill,
     Reedwick, Railhead and Timberline do; plan 03–06 each adds one small
     hearth.
5. **Lorebook PLACES limit.** It was a known leftover in HANDOFF.md. Raise
   it for about 12 new places.
6. **Music.** Every map needs a song (`test_music.c:77`). Route maps reuse
   the route themes. Add a `SONG_ROUTE_*` alias table in `music_map.c`, so
   region plans set a song without touching music code. The music session
   owns the actual tracks; do not clobber `music.c` or `music_data.h`.

---

## E9. Quest engine upgrades (for plan 10)

- **Per-stage goal text.**
  - Today a quest has one `goal` string (`world.h:111`).
  - Add `const char *const *stage_goals; u8 n_stages;` to `QuestDef`.
  - The log shows the goal for the current stage, and falls back to `goal`.
- **Quest markers.** `QuestDef.where(stage) -> MAP_*` (or a table). The town
  map draws a small marker on that map's position. No markers inside maps.
- **Quest categories:** MAIN, SIDE, PROJECT, EVENT. The log groups by them.
  The 7-row list gets a page header.
- **Raise `QUEST_MAX`** from 48 to 96 (`quest.c:6`). The state grows by 48
  bytes, inside `MOD_QUEST_MAX 128`; move `pad[16]` accordingly. Append;
  don't reorder.
- **Helpers** in `quest.c`:
  - `quest_advance_to(q, stage)`: generalise `grim_quest_at_least`,
    `grim/scripts.c:75`;
  - `quest_is(q, stage)`;
  - `quest_between(q, a, b)`.

---

## E10. Hooks the events system needs (for plan 09)

Build only the hooks here. Plan 09 builds the events themselves.

- **Daily hook registry.** `time_new_day` (`time.c:176`) today calls only
  `time_roll_weather` and `farm_new_day`. Add a fixed list of hooks, with
  `events_new_day()` first.
- **Deterministic daily seed.** Add `u32 time_day_seed(void)`: a hash of
  `gtime.day` and a per-save random `u32` (append it to `TimeState`, which
  has a pad byte, or keep it in the events module). Replace the unseeded
  `rng_range` in `time_roll_weather` with it, so a day's weather and events
  agree after a reload.
- **Wild overrides.** In `wild_spawn` / `roll_wild` (`field.c:1431`), call
  `events_wild_override(zone, &slot)`. It can replace a roll with an
  outbreak species or raise levels.
- **Weather override.** `time_raining_here` (`time.c:92`) and the weather
  drawing (`farm.c:1928`) call `events_weather_here(map)`. It returns a
  `WX_*` kind: CLEAR, RAIN, STORM, FOG, SNOW, ASH, HEAT, AURORA. Wire up the
  unused `MF_SNOW` as the default SNOW kind for its maps.
- **Map-enter hook.** Today `field_on_enter` (`script.c:917`) is hardcoded.
  Turn it into a registry and add `events_map_entered(map)`,
  `story_map_entered(map)` and `saga_map_entered(map)`.

---

## Order and acceptance

1. E1 and E2, merged alone. All existing tests pass, and a v5 save loads.
2. E3, E5 and E6 (E6 depends on E3 and E5), with E6 running on today's
   world and today's (lack of) gates. Mark the ordering asserts as `xfail`
   until the region plans land. The test is *expected* to report that
   Cindermoor is reachable at Act I; that is the baseline.
3. E4, E8 and E9.
4. E7 step 1. E7 step 2 may run in parallel with the region plans.
5. E10, before plan 09 starts its content.

**Write `docs/handoff/engine_routes.md`** when done. List the new APIs with
one example each. Region agents copy from it.
