# EVENTS (plan 09) — isolated branch handoff

Branch `plan-routes-events` is based on ca6a672. This is an **unmerged integration candidate**, not a playable complete event system: E3/E5/E10 and the contract §6 map/zone IDs are absent from the base. No engine, save, Makefile, region, generated, or shared expansion file was edited.

## Implemented event data and behavior

| Event | Roll/condition | Current effect | Integration gap |
| --- | --- | --- | --- |
| Regional STORM/FOG/SNOW/HEAT/ASH/AURORA | 1 front, 1–2 days, act-gated | `events_weather_here` returns regional kind; Gazette | E10 weather renderer/tint/particles; AURORA night visuals not wired |
| Curated outbreak | 75% each day, unlocked zone only | `events_wild_override` replaces one in six rolled spawns; Gazette | E10 wild hook, +10% lustrous modifier, seasonal migration |
| Caravan | Moves one reachable stop/day; re-entry at Maple before G1 | Stop-specific NPC visibility, rotating five-item shop script, Gazette | E3 `NpcDef.event`, E10 save, coordinates on new routes, courier/buyback |
| LOST KIN / SURGE / METEOR / TOURNEY / TALES | Daily single happening | Gazette; SURGE adds 3 levels on Meadow | Encounter/NPC gameplay and XP/bond/reward hooks |
| NIGHT/FISH MARKET | Weekly, act-gated | Gazette | Region owners' stall NPCs |
| WASHOUT | After 3 rainy days | Gazette | E5 side-path-only patch and solver proof; not currently applied |
| Rematches | 3–5 beaten wardens/day, 10 initial candidates | Ready bitmap, board, consume hook | E10 trainer sight/spot/battle hook, upgraded teams, 40-warden table, Masters |
| Five festivals | Fixed season day | Calendar, 2-day Gazette forecast, Maple festival host and dialogue | E3 condition, other hosts, mechanics/rewards |

To add a rolled event: append a stable `EV_*` in `world/events/data.h`, choose one of the existing daily slots in `events_new_day`, add a Gazette line and a test. To add a caravan stop: append to `CARAVAN_ROUTE`, add `EVENT_PERSON` using `EV_CARAVAN_STOP_BASE + index`, and confirm the stop's cell and all gates via `test_progression` after region merge. Avoid changing old event indices in a saved `EventState`.

## Required integration after E10 and route merge

1. E10 provides `time_day_seed()` and calls `events_new_day()` at dawn, `events_wild_override` on a copied `WildSlot`, `events_weather_here` on field weather rendering, and `events_map_entered` on entry. E3 calls `events_active(npc.event)`; per-stop event IDs are 32–43. Do not test the `EV_CARAVAN` umbrella bit alone or all stops will appear together. E3 defaults the new `NpcDef` fields to zero. The event people initializer explicitly requires `.event`.
2. The event struct is 32 bytes including alignment; `TimeState` uses 8 bytes before E10's additional seed, so it cannot safely share the 32-byte time blob. The save owner must reserve a **new 64-byte event blob** in `SaveData` (slot `mod_size[6]`), store/load/reset/validate it, and make old saves with zero module size roll today. Run the save-layout generator and approve the capacity change there. Until then no event state survives a save/load.
3. Contract §6 missing IDs in this base: MAP_BROOKMILL_TRAIL, MAP_BROOKMILL, MAP_HERON_FEN, MAP_REEDWICK, MAP_CINDER_CROSSING, MAP_RAILHEAD, MAP_FOOTHILLS, MAP_TIMBERLINE, MAP_HOLLOW_DOWNS, MAP_MISTFEN, ZONE_BROOKMILL_TRAIL, ZONE_HERON_FEN. New route owners must supply these. Recheck every event NPC `(x,y)` after map merge, notably provisional `(12,12)` stops (Maple was moved from a wall to `(11,8)`), before enabling them on the critical path. E6 progression must verify them.
4. Wire `events_rematch_ready` and `events_rematch_used` only after an upgraded-team interface exists; `trainer_beaten` is currently static in field.c and returns first-time bits. Rematch visits must not clear first-time rewards. Finish roster/teams and weekly Hall schedule with battle owner.
5. `all_*.inc`, `all_data.h`, `all_scripts.c` and `main.c` are registered on this branch; reconcile registration with other branch merges. No art generator or generated headers are included: weather visuals need a separate build/VRAM allocation from the engine owner. Existing snow MF is returned by the event API but does not make particles fall yet.

## Verification status

A temporary standalone C smoke harness with stubbed E10/route IDs compiled and ran 1000 days: 1000 fronts, 733 outbreaks, stable repeated-day state, all Gazette lines <=30 characters, 32-byte EventState. This validates only event-core logic, not engine integration. `cc -std=c11 -fsyntax-only tools/tests/test_events.c` cannot compile against ca6a672: the missing route map/zone IDs and E10 `time_day_seed` are the first errors. `make` also stops at existing save-layout golden growth before compiling this branch; the generated layout was restored unchanged. `test_events.c` covers 1000 days, same-day idempotence, act gates, Gazette length, validation and festival dates but has **not passed** until those interfaces merge. No patch was added; washout safety and NPC budgets are unverified. Run `make test` and `test_progression` when the engine and all routes land.
