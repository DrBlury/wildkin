# Eastern Rootways pilot handoff

## Map IDs and topology

Append-only `src/game/world/east/ids.inc` entries: `MAP_ROOTWOOD_PATH` (20×10 woodland connector), `MAP_ROOTWAYS` (24×17 cave, depth 1, Bramblewood surface anchor), `MAP_MILL_CELLAR` (13×9 cave, depth 1, Brookmill surface anchor). Existing Copperline Mine now declares depth 1, Copperline surface anchor, and `MF_NOFLY`; Brookmill Mill remains an ordinary interior (depth 0). Existing Bramblewood 44×36, Brookmill Mill 13×10, Copperline Mine 36×28 and all edge/quest coordinates remain unchanged. Bramblewood's three existing creek bridges remain intact on its surface crossing. New maps have no edge links: every portal has an explicit return warp and `OBJ_LADDER`, not an `A_EXIT` fallback.

Each of the following ten directional portals sets `.required_flag = FLAG_VOLT_CREST`; the central `warp_is_open()` check must reject uncrested entry in **both** directions. Coordinates are `source -> destination (spawn)`, zero-based:

| Portal | Forward | Return |
| --- | --- | --- |
| Hollow | `MAP_WOOD (17,5) -> MAP_ROOTWOOD_PATH (3,7)` | `MAP_ROOTWOOD_PATH (2,7) -> MAP_WOOD (17,6)` |
| Root mouth | `MAP_ROOTWOOD_PATH (17,3) -> MAP_ROOTWAYS (3,8)` | `MAP_ROOTWAYS (2,8) -> MAP_ROOTWOOD_PATH (16,3)` |
| Mill root | `MAP_ROOTWAYS (21,3) -> MAP_MILL_CELLAR (6,3)` | `MAP_MILL_CELLAR (6,2) -> MAP_ROOTWAYS (20,3)` |
| Mill stairs | `MAP_MILL_CELLAR (6,7) -> MAP_BROOKMILL_MILL (6,5)` | `MAP_BROOKMILL_MILL (6,6) -> MAP_MILL_CELLAR (6,6)` |
| Mine root | `MAP_ROOTWAYS (21,14) -> MAP_COPPER_MINE (4,18)` | `MAP_COPPER_MINE (3,18) -> MAP_ROOTWAYS (20,14)` |

The Bramblewood stump at (17,4), with a ladder just south, indicates the hollow entrance. The hooked surface approach leads into asymmetric root chambers; upper branch leads to the mill and lower branch to Copperline. Existing storm/Act II edge and quest gates are not replaced or changed. Reaching the Bramblewood stump from Maple Village follows the existing wooded surface route; no new gate bypasses the Volt Hall progression.

## Puzzle and capacity

`MAP_ROOTWAYS`: push the **pumice** (6,8) **east once** onto plate (7,8), opening gate (12,8) permanently (group 3). The gate is only a shortcut across the cave's central ridge; the upper and lower walkable loops always provide a way around it. All three cave exits are beyond the puzzle chamber, so a boulder cannot seal an entrance. Its placement is independent of STRENGTH; reloading resets the pumice, not the gate bit. Seven signs on the route and existing surrounding maps explain the destinations and the solution. One new persistent object (`OBJ_GATE`), three new maps, and at most six objects on any new map; well under the supplied limits of four persistent objects, four maps and 48 objects/map. Append-only existing map/object lists preserve their prior ordering **within the east and village regions**; coordinator should verify global save bit/ID migrations since the all-region ID lists enumerate east before later regions and persistent bits are map-order derived.

## Focused verification and integration

Compile and run: `cc -std=c11 -w -o build/world-expansion/test_rootways tools/tests/test_rootways.c && build/world-expansion/test_rootways`. This tests every portal/spawn, both crest states, row widths, anchors and pumice persistence. Full map/reachability/progression and ROM tests belong to the central owner; expect to update the centrally owned map-count/progression earliest-act assertions for the three appended maps. Do not regenerate art/saves here.

Safe screenshot/save inspection spawn: `MAP_ROOTWOOD_PATH (5,7)` facing right **with `FLAG_VOLT_CREST` set**; from there, the short woodland elbow, sign and hollow-tree return are visible. For a cave screenshot, `MAP_ROOTWAYS (5,8)` facing right; its plate is nearby. Central integration wired the later links: `MAP_ROOTWAYS (19,11)` → `MAP_TIDAL_UNDERFLOW (11,3)` after Tide, with return to Rootways (20,11); `MAP_COPPER_MINE (8,18)` → `MAP_RAILHEAD_SHAFT (4,10)` after Anvil, with return to the mine (9,18). Both use appended ladder objects and explicit mirrored gates. Rootways is now a safe `ZONE_NONE` puzzle room with visible solid signs; its original gate retains its persistent object index.
