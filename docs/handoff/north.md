# North region: handoff (W-NORTH)

## Done

- **'snow' tileset** (`tools/tilesets/ts_snow.py`, 349 tiles): unchanged from
  the first pass (legend at the top of the file and of `world/north/data.h`).
- **'cave' tileset** (`tools/tilesets/ts_cave.py`, 113 tiles, 25 metatiles):
  floor (+ crystal grit, pebbles), glowmoss (A_GRASS, top layer), rock mass,
  wall face, crystal-vein wall, crystal outcrop, rock ledges, the exit mat
  (daylight + blown-in snow), void, animated underground lake (autotile),
  gravel path (autotile) and the Starfall starlit pool (numpad rim). Door
  stamps (1x1, walked into from the south): STAIRS_DOWN, STAIRS_UP, CRACK.
  Banks in `tools/north_palette.py` (CAVE_BANK_*; hs_ values untouched).
- **Cave decor registered** (`decor_north.NORTH_DECOR` now includes it).
- **Maps** (`src/game/world/north/`), all verified in the ROM with `build/shot`:
  FROSTPINE PASS (40x44), FROSTHOLLOW (40x36: Hearth, Shop, Rime Hall, 2
  houses, bathhouse, cave mouth, skating pond, plaza), WHITECROWN PEAK
  (32x40, switchbacks, ledges, the STRENGTH boulder corridor, summit),
  SKY ISLE (24x20, clouds, SKY_ARCH), RIME HALL (15x20 ice puzzle), HOT
  SPRING, FROST HEARTH HALL, FROST SHOP, THE ALDER HOUSE and STARGAZER'S HOUSE
  (two new map ids), GLIMMER CAVERNS (40x30, MF_DARK, lake + bridge),
  GLIMMER DEPTHS (36x28, MF_DARK, ledge loop), STARFALL GROTTO (24x20).
  Edge contracts kept: Frostpine south x 11-12 (Rise), Frostpine/Frosthollow
  and Frosthollow/Whitecrown at x 19-20.
- **Objects**: `OBJ(LEGEND, ..., SP_HOARFANG)` on the summit,
  `SP_SELENOTH` by the moth dais, `SP_SKYLORN` under the sky arch;
  `OBJ(BOULDER, 18, 9, 0)` in the Whitecrown corridor (push it WEST into the
  pocket at x 6-7, then go north at x 8); berry patches 20-24.
- **People**: 17 wardens (<= 6 kin each), Hall Master SIGRUN (6 FROST kin,
  `battle_start_master`, awards `CREST_RIME` + `FLAG_RIME_CREST` + story lore),
  tender (sets `travel.last_hearth`), Frost Shop (`shop_open_stock`), hall
  guide, ice carver, stargazer, grotto scholar, spring keeper (soak heals),
  spring cook (`SCR_CHEF`, craft owner), Granny Alder, villagers.
- **Wild zones**: FROSTPINE, WHITECROWN, GLIMMER, GLIMMER_DEEP (with
  WHEN_DAY / WHEN_NIGHT slots) and GLIMMER_LAKE as the caves' water_zone.
- **Lore**: 13 entries (places, legends, Rime Hall, aurora, snowflakes,
  winter coats, the crest). **Quests**: LAMPS FOR THE LONG NIGHT (3
  GLOWCAPS), THE STAR CHART. **Fly points**: FROSTHOLLOW, SKY ISLE.
- **Tests**: `tools/tests/test_north.c` (edges, Rime Hall slide solver,
  cave floor-to-floor reachability, boulder push, warden teams, lore
  sources, both quests, the Master bout and crest). `make art && make &&
  make test` green, no new warnings.

## Left

- Art review: BATHS stamp hot-spring mark, CLOUD vs CRAG, the starlit pool
  rim reads weakly in the ROM.
- The map rows were drawn with a scratch generator (not committed);
  `data.h` is now the source of truth, edit it directly.
- Depends on other systems: ice sliding / MF_DARK / OBJ_LEGEND /
  OBJ_BOULDER / OBJ_BERRY behaviour (traversal, farm), FLY to the Sky Isle.
  The core reachability flood ignores objects; once boulders are solid it
  needs a "puzzles solved" mode (the Whitecrown summit is behind one).
  Nothing at the summit is an NPC, satchel or sign, so only the legend
  object is behind the boulder.
- Sky Isle carries no NPCs, signs, satchels or warps (the core flood has no
  fly-point start).
- `WildSlot.when` is still ignored by `roll_wild` (time owner).

## Shared files edited

- None by hand. Regenerated: `src/gfx_field.h`, `src/game/world/debug/*`.

## Routes (plan 06, branch plan-routes-north)

- Appended `MAP_FOOTHILLS` (40x60, TS_WILD), `MAP_TIMBERLINE` (40x36, TS_SNOW), `MAP_TIMBER_LODGE`, `MAP_TIMBER_SAWMILL` and the optional `MAP_STORM_CAVE` after all existing north map IDs; appended matching zone, lore, quest, script and trainer IDs, without renumbering earlier north IDs.
- Changed only Rise's north link in `village/maps.inc` to `MAP_FOOTHILLS`; the route continues through Timberline to Frostpine (south x11–12, Foothills north/south x19–20/x11–12, Timberline north/south x11–12/x19–20). G4's three arg-0 boulders stand in the Foothills south corridor; the warning sign names the Anvil crest. A guide also explains the storm rockfall. The east-side ranger shelter entrance leads to the lost-axe cave.
- Foothills has a basalt crossing, two paths, meadow grass, 7 wardens, route items, a berry patch, a DRAKORA shrine sign and a storm-watcher lore source. Timberline has a lodge hearth and fly point, sawmill NPC, two logger wardens, LOST AXE quest and a GNAWLORD cave bout awarding three HEAVY LANTERNS. Frostpine wild slots are now Lv30–34, Glimmer 1 Lv30–34, Glimmer 2 Lv32–36, Sigrun Lv34–37 and Whitecrown Lv44–50. North field tests cover the new edge coordinates, map sizes, blockers, lodge, quest and Hall levels.

### Plan 08 LINKS reservation (not wired yet)

- **Aurora Ridge:** Frosthollow's east border is currently open at `(43,20)` and `(43,21)`, with walkable approach `(42,20–21)` at elevation 0, but `link[LINK_E]` is `MAP_NONE` because `MAP_AURORA_RIDGE_1` is not declared yet. When plan 08's ID and E5 flag-patch API exist, set `MAP_FROSTHOLLOW.link[LINK_E] = MAP_AURORA_RIDGE_1`, give Ridge 1 `link[LINK_W] = MAP_FROSTHOLLOW` and only y20–21 as its west edge opening; add a two-cell solid ice-wall patch at `(42,20–21)` on Frosthollow until `FLAG_RIME_CREST`, then thaw. Keep Ridge's downstream waterfall and Lantern-crest barrier as specified by plan 08 so the route cannot bypass G6. Do not add a raw edge before the crest patch exists.
- **Greywater Fjord:** reserve Frostpine's west cliff cave door at `(2,11)` (`STAMP(SN, CAVE, 1, 10)` places the door at `(2,11)`; approach is `(2,12)`). Once plan 08 declares `MAP_GREYWATER_FJORD`, add that stamp to `FROSTPINE_STAMPS` (currently the map has no stamps) and the north-owned warp `{ MAP_FROSTPINE, 2, 11, MAP_GREYWATER_FJORD, fjord_cave_x, fjord_cave_y }`. Have plan 08 provide the reciprocal cave door/warp on the Fjord's north end and choose its landing coordinates; place a Strength boulder and one-way waterfall **on the Fjord side** to prevent reaching Frostpine before G4. Do not add the door until it has a real destination. Validate both directions and the pre-Anvil progression state.

### Requests / gaps

- **E1 shared save golden:** `make` / `make test` invoke `tools/gen_save_layout.py`; appending north IDs regenerates `src/game/world/save_layout.inc` and needs `tools/gen_save_layout.py --accept-growth` to update `tools/tests/save_layout.golden.json`. Those shared/generated paths belong to ENGINE/integration and are intentionally not committed here. Integrator must accept the appended north prefix and regenerate the manifest before normal `make && make test`.
- **E3/E5 not at this checkpoint:** no NPC show/hide condition or flag-driven map patch interface exists. The Aurora ice wall, Whitecrown/Sky Isle postgame legend seals, seasonal night-only watcher, north-half storm hook and on-map snow-zone split cannot be represented faithfully. Current Foothills has a low zone; the high snow zone is used in the optional cave, not the north half of the same map. Link only after E5; add exact patch tests in `test_north.c` and progression solver then.
- **G4 puzzle limits:** three physical boulders close both entry cells; `test_north.c` proves the initially shut corridor and a manually cleared northward path, not exhaustive push-state reachability or impossible south pushes. Full `test_puzzles` grew beyond three minutes after reaching the new route and was stopped. The push engine accepts a boulder on any walkable non-exit tile, so the contract's no-south-into-Rise guarantee needs a safe gate layout / engine no-push tile and a bounded solver run. Do not claim G4 soft-lock proof until both hold.
- **Other deferred content:** no true double battle mechanism is present for the paired climbers; no later-FLY elevated shrine/rematch (plan 10), one-way drop, hot-spring daily bond hook (plan 09), visible snow blend in TS_WILD, second Timberline side quest, or sawyer TIMBER sales until the saga item is supplied. Existing Whitecrown legend and Sky Isle are not postgame sealed. The sawyer explicitly describes unavailable stock rather than referencing an undeclared item.

### Validation of this branch

- `make art` completed (all tilesets and decor within generator constraints); generated assets and the temporary save manifest were restored to the checkpoint after checking.
- Direct `cc ... tools/tests/test_north.c` passed; direct `cc ... tools/test_field.c` passed after the ranger shelter doorway and shrine sign correction.
- `make all -o save-layout` built a valid GBA ROM with no reported compiler warnings, using the temporary generated save manifest. This is *not* a green normal `make all` while the shared golden is unchanged.
- Full `test_puzzles` progressed through the prior north maps, then stalled at the new Foothills boulder state search (>3 minutes) and was stopped; no G4 solve/soft-lock claim.
