# LINKS / plan 08 handoff — loop routes

Branch `plan-routes-links`, based on `ca6a672`. Owns `world/links/`, `test_links.c`, and one include registration per `world/all_*` list after `ui`. No engine, other region, generated manifest or golden change belongs to this branch.

## Implemented here

- Five maps: Scorchwaste 1/2 (48×40, volcanic → grim), Aurora Ridge 1/2 (56×36, snow), and Greywater Fjord (40×64, coast), with internal reciprocal edges, themed wild zones (including night HOPSHI/METEORB, day TENGALE, night WENDIGAUNT, night KELPYRE), signs, three Lorebook pages, berries, satchels, 6+6+5 wardens and a fjord chest.
- Cave passages on the links side use scripted conversations rather than an automatic `WARPS` entry, preventing a normal door interaction from skipping a crest check. Scorchwaste → Duskmere checks `FLAG_LANTERN_CREST`; Aurora → Dreamspire checks **both** `FLAG_LANTERN_CREST` and `FLAG_CREST_DREAM`; Fjord → Frostpine checks `FLAG_CREST_ANVIL`. The fjord's north island has a separate south-facing ledge and STRENGTH boulder (19,12) on its only land passage; verify surf/ledge direction once endpoints land.
- `test_links.c` compiles and passes local route dimensions, songs, tilesets, internal edge reciprocity, cave gate predicates, safe current destination cells and content counts. `test_field` now passes local decor and reachability checks; external reciprocity and save layout are deliberately deferred.

## Exact stub contract for region owners / coordinator

| Owner | Existing-map stub to add | Links-side landing / outgoing behavior |
| --- | --- | --- |
| FAR (05) | Cindermoor south x20–21 open to `MAP_SCORCHWASTE_1`, guarded by heat-wall patch until `FLAG_LANTERN_CREST`. Make Cindermoor's row39 x20–21 walkable; keep return path. | SW1 north x20–21 and SW1 south x20–21; SW2 north x20–21. |
| GRIM (07) | Duskmere east cave in its region, behind a STRENGTH rockfall; warp to `MAP_SCORCHWASTE_2` (4,21). Coordinate cave approach on return to Duskmere x38,34 (currently walkable); adjust the links script landing if the final stub moves it. | SW2 cave ranger at (4,20) checks Lantern and warps to Duskmere (38,34). No ungated warp in links. |
| NORTH (06) | Frosthollow east y18–19 open to `MAP_AURORA_RIDGE_1`, gated by an ice wall until `FLAG_RIME_CREST`. Make Frosthollow row18–19 x43 walkable. | AR1 west y18–19 and east y18–19; AR2 west y18–19. |
| FAR (05) | Dreamspire west cave, owner-side gate `FLAG_CREST_DREAM`; warp to `MAP_AURORA_RIDGE_2` (49,19), on the cave approach. Current links script returns to Dreamspire (4,29), verified walkable; relocate only together with stub. | AR2 cave guide at (50,18) checks Lantern **and** Dream before warping. |
| WEST (04) | Port Brine north x19–20 as water opening with `MAP_GREYWATER_FJORD` link; only SURF can pass. Ensure its row0 x19–20 and nearby harbour approach are surfable. | Fjord south x19–20 is water; islets and open sea use `ZONE_FJORD_SURF` water encounters. |
| NORTH (06) | Frostpine west cave with reciprocal warp to `MAP_GREYWATER_FJORD` (20,7), inside the northern island above the barrier. Return destination on base is Frostpine (3,29), verified walkable; align with final cave stub. | Fjord fisher (20,6) checks Anvil before warping; ledge at (20,12), boulder at (19,12) block the south→north shortcut without STRENGTH. |

**Do not add unconditional links-side cave warps** alongside these scripts: the door would trigger before the NPC gate. Region owners should gate their own reverse warps. With current base maps, the three outside edges do not yet have reciprocal links and two land in walls; this is a known merge dependency, not a pass. The `WORLD_POS` renderer hint format is not present in base `ca6a672`; plan 02/central integration should position all three loops and validate the render.

## Unfinished integration and plan differences

- Base `ca6a672` has no E5 flag-driven map patch, no `TS_VOLCANIC` ice glyph carrying `A_ICE`, and no double-bout battle API. Thus the Cindermoor heat wall, Frosthollow ice wall, Scorchwaste lava-crust slide and paired wardens' *actual* double bout need their owning engine/tileset integrations. SW1 has cooling-crust lanes visually but not slide physics; Aurora Ridge has working snow `A_ICE` cells. The snow ridge's cave is script-gated rather than visually patch-gated and the requested elevation level-3 knife edge is not present. Greywater's drowned village is communicated by lore/terrain rather than a unique undersea prop.
- Region-owner stubs and the plan 02 global progression solver must prove no approach skips G4, G5 or G6, all gates can return to a Hearth, and every external path is bidirectional at the appropriate act. The current local test proves only internal edges and local script predicates. Postgame aurora-only QILUMEN and weather overlay depend on plan 09; this branch does **not** put QILUMEN in the ordinary night pool.
- No hidden searchable satchel behavior exists in this module; the placed rewards are normal visible balls. The PRISM LANTERN item named in plan 08 does not exist in the current item enum (crafting recipe `RC_PRISM_LANTERN` does), so the route cache is currently `ITEM_STAR_LANTERN` and should be replaced with its real item ID after the item owner adds one, if desired.
- **Save layout:** `tools/gen_save_layout.py` sees links region growth. It writes `src/game/world/save_layout.inc` even without `--accept-growth`; this branch restored the original generated file. The coordinator alone must regenerate the manifest and accept its golden after all region merges. Until then `test_field` saving/current-load assertions fail by stale manifest. Never accept golden from this branch.

## Validation observed

- `cc ... tools/tests/test_links.c && build/test_links`: pass, 16 checks, zero failures.
- `cc ... tools/tests/test_north.c && build/test_north`: pass.
- `cc ... tools/tests/test_puzzles.c && build/test_puzzles`: pass; solver reports all Greywater targets reachable, two STRENGTH pushes to reach the cave fisher, no endless moves or soft-locks.
- `cc ... tools/test_field.c && build/test_field`: local rows, decor, budget and reachable-content checks pass; six failures remain from three missing external reciprocal edges/walkable landings and four current-save assertions due to stale generated save layout (overlapping counts: see log). Re-run after integration.
