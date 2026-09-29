# Biome routes implementation contract

Approved scope: twelve new maps, three villages and selected existing-route improvements. Existing uncommitted field residency, sprite restoration, and concurrent Rootways/underworld work are preserved. New regional content is isolated in `world/<region>/biomes/` and appended to the region's existing lists. No saved list is reordered.

## Baseline (2026-09-28)

Before biome edits, `make test` and `make` both exited 2: concurrently authored world-position markers referenced missing generated `WM_*` identifiers, including `WM_ROOTWOOD`. Logs: `build/biome-validation/baseline-tests.log`, `baseline-build.log`; preexisting diff/status saved beside them. This is a moving-tree integration failure, not a biome test failure or a passing baseline. Re-run after the shared-file owner finishes generation.

## Map checklist

| Region | New map | Parent / purpose | Required evidence |
|---|---|---|---|
| east | Mistfall Gorge | Brookmill; river gorge and terraces | three landscape beats, bridge encounter, reward branch, safe return |
| east | Mistbell | gorge rim village | crescent layout, bell custom, service access |
| east | Mistbell Bellhouse | gathering/rest interior | repair quest, cancel/insufficient/idempotent reward, persistence |
| links | Saffron Dunes | Scorchwaste branch | dry wash, crescent ridges, caravan encounter, no story bypass |
| links | Sunwell | oasis village | ring of homes, jars, garden patch |
| links | Sunwell Cistern | rest/quest interior | irrigation quest, one-time resource/reward changes |
| east | Rootcoil Jungle | Elderwood branch | irregular roots/river, terrace/bridge, optional loop |
| east | Canopy Hearth | raised settlement | readable platforms, woven markers and herb plots |
| east | Canopy Lodge | rest/supply interior | waymarker quest and return shortcut persistence |
| west | Coralhook Reef | Sea Route | curved surf channels, coral islands, wreck encounter |
| north | Rimewind Tundra | Aurora Ridge | treeless snowbanks, cairns, combat hollow, lake overlook |
| north | Sporelight Hollow | Glimmer Caverns | uneven chambers, fungal shelves/pools, reward branch |

## Authored-route rules

- Change walkable shape, not only path paint; use 2–4-cell ordinary passages and wider battle clearings.
- Entrance reveal, three landscape beats, encounter pocket, optional reward, readable exit; no unavoidable blind passage.
- Place props by purpose and ecology. Keep enemy silhouettes and warp landings clear.
- Existing story gate/patch/door/NPC coordinates remain protected unless changed with their tests.
- All new branches inherit parent progression. Both ends of gated portals enforce the same flag.
- New villages have rest access, distinctive interaction, one bounded quest, and persistent one-time rewards.
- Preserve valid saves, including bridge/surf positions; changed terrain needs progression-safe recovery.

## Resource contracts

Maps <=64x64; objects <=48; target <128 decor placements; resident scene <=768 8x8 tiles; ROM terrain IDs <1024; field palette banks 0–7. Reuse generators, never hand-edit generated graphics. Append desert/jungle registry entries after existing entries. Review global map/script/quest/save capacities after integration.

## Existing-area pass

Brookmill Trail/Brookmill: stream bends, wooded sections and mill custom. Heron Fen/Reedwick: winding boardwalks, reed craft. Saltwind/Port Brine/Gull Isle: scalloped shore, workyards and salvage gardens. Frostpine/Timberline/Frosthollow: switchbacks, sawmill and geothermal spaces. Ember Tunnel/Caldera/Cindermoor/Railhead: lava shelves and working forge/rail yards. Hollow Downs/Gravewood/Duskmere: eroded paths, roots, lantern memorials. Moonveil/Dreamspire: crescent pools and night gatherings.

## Validation gates

1. Fresh baseline after concurrent world integration; save recovery tests before old terrain reshaping.
2. Dedicated art catalog build/encoding and resident cache tests.
3. Waterfall branch movement/quest/save and visual proof before integrating remaining branches.
4. Remaining branch movement, encounters, quests, reward idempotence and gate checks.
5. Full `make test`, `make`, map renders and native ROM captures; report host vs ROM evidence separately.

## Integration outcome

The concurrent world task released its shared files before integration. Its
field/travel/save hashes were checked, a fresh baseline `make test` passed, and
those engine/save files remained byte-identical after the biome work. The twelve
new maps and three village quests are integrated, with four collision-shaped
existing routes and the broader nineteen-area scenery/dialogue pass.

Final evidence and reproduction commands are recorded in `docs/BIOMES.md`.
All 53 host test executables, the ARM build, 13 Python checks, map renders and
fourteen memory-verified ROM captures passed. Single-room interiors deliberately
use existing exit mats rather than redundant reverse warp records. The GBA
keeps tile-grid storage; organic playable contours come from collision, terrain,
elevation and transparent scenery, not a replacement engine.
