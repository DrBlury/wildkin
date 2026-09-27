# Town project visuals and transport

Worktree `finish-projects-v2`, based on `d60000b`. No save flag IDs, ordering, shop inventories, travel engine, or regional NPC placements changed.

## What is live

- `FLAG_PROJECT_TRAM` already drives the Brookmill depot ground apron `(33,29,5,4)` and Lumen buffer stop `(33,22,5,2)`. The three saga tram guides remain bidirectional fade warps; the existing code has no vehicle scene for tram travel.
- `FLAG_PROJECT_CINDER_BRIDGE` already drives the Cinder Crossing deck `(6,20,4,2)` and Railhead apron `(24,18,5,2)`. Host flood from `(4,21)` to `(11,21)` is blocked before repair and walkable in **both directions** after it, without SURF. The optional two-way guide warp remains for players crossing with SURF and as a redundant fallback, pending broader progression playthroughs. Nothing opens the rockslide or bypasses a story crest.
- `FLAG_PROJECT_LIFT` already drives approach aprons at Foothills `(8,49,3,2)` and Timberline `(8,28,3,2)`. The two guides remain safe two-way fade warps; the engine has no supported lift vehicle scene yet.
- `FLAG_PROJECT_REED_FERRY` already drives the Reedwick landing `(24,25,3,2)`. Both guide directions now use `travel_boat_to` through `dlg_call`, displaying the engine's animated boat, wake, gulls, and sailing voyage; arrival remains `(31,17)` at Mirror Lake and `(25,20)` in Reedwick. Ferry payment and flag gating are unchanged.

## Deliberately not faked

- `FLAG_PROJECT_MARKET` is saved and the project can finish, but Maple has no reserved market-hall footprint, interior map/entrance, rotating regional-goods shop, or conditional building-stamp/decor hook. The E5 `MapPatch` replaces **ground tiles only**, not building stamps. Existing Maple stamps, elevation seams, occupied market stalls, roads, existing entrances, and the ledge yard rule out treating a random tile rectangle as a functioning hall. A court/stone patch labelled a shop would falsely advertise a nonexistent destination. Reserve a viable site and specify the hall interior and shop contract before adding a market facade/warp. Do not repurpose Lumen's market as Maple's.
- Tram/lift cutscenes must be provided by the travel owner; the only existing animated vehicle API is a **sea** voyage. Proposed travel-owned API: `travel_project_ride_to(int kind, int map, int x, int y)`, supporting tram/lift kinds with vehicle frames and a safe arrival. Saga callers can switch their existing `field_begin_warp` routes to it once available; do not paint a sea boat as a tram.

## Validation

- `python3 tools/gen_field_gfx.py --no-header`: asset lint/generation succeeds, 266 decor kinds; no generated files modified.
- `cc ... tools/tests/test_project_visuals.c` and executable: zero failures. Tests patch dimensions, visible flag transitions, pre/post scene-tile budgets, blocked-until-built Cinder and two-way foot crossing, pre-build return landings, and both animated ferry route endpoints.
- Host `test_field` and `test_saga`: zero failures. `make -j2 all`: valid GBA ROM, 3,629,500 bytes, `check_rom.py` passes; `git diff --check` passes.
