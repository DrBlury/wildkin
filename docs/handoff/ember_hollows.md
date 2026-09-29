# Ember Conduits and Dusk Hollows handoff

Four append-only map IDs (current compiled values in parentheses): `MAP_EMBER_SPAN` (113; 24×18, depth 1, Railhead anchor), `MAP_COOLING_CHAMBER` (114; 20×15, depth 2, Railhead anchor), `MAP_ROOT_GALLERY` (90; 24×18, depth 1, Hollow Downs anchor), and `MAP_DUSK_VAULT` (91; 24×17, depth 2, Hollow Downs anchor). Numeric values may shift while parallel region ID appends land; use the symbols as the stable interface. Each has `MF_NOFLY` and `ZONE_NONE` (compact chambers have no meaningful 20-cell wild habitat). Existing Collapsed Shaft, Ember Tunnel, Caldera, Lantern Crypt, and both barrows have underground depth/anchor metadata; Lantern Crypt and barrows now also prohibit flight. Gravewood alone uses `TS_DUSK`, not `MF_DARK`.

## Entrances and order

Every pair below has explicit reciprocal `Warp` rows with the listed `required_flag`; source coordinates are real `OBJ_LADDER` doors or crypt `U/S/A` doors and arrivals are on adjacent ordinary floor, never on a door or `A_EXIT` mat. Coordinates are `(x,y)`; `→` gives the source **door** and destination **arrival**. Reverse doors/arrivals are in the right column.

| Gate | Forward | Reverse |
|---|---|---|
| `FLAG_CREST_ANVIL` | `MAP_RAILHEAD_SHAFT` (11,3) → `MAP_EMBER_SPAN` (11,15) | `MAP_EMBER_SPAN` (11,16) → `MAP_RAILHEAD_SHAFT` (11,4) |
| `FLAG_CREST_ANVIL` | `MAP_EMBER_SPAN` (11,1) → `MAP_COOLING_CHAMBER` (9,12) | `MAP_COOLING_CHAMBER` (9,13) → `MAP_EMBER_SPAN` (11,2) |
| `FLAG_CREST_ANVIL` | `MAP_COOLING_CHAMBER` (9,1) → `MAP_EMBER_TUNNEL` (5,10) | `MAP_EMBER_TUNNEL` (5,9) → `MAP_COOLING_CHAMBER` (9,2) |
| `FLAG_RIME_CREST` | `MAP_BARROW_B` (8,5) → `MAP_DUSK_VAULT` (11,14) | `MAP_DUSK_VAULT` (11,15) → `MAP_BARROW_B` (8,6) |
| `FLAG_RIME_CREST` | `MAP_DUSK_VAULT` (11,1) → `MAP_ROOT_GALLERY` (11,15) | `MAP_ROOT_GALLERY` (11,16) → `MAP_DUSK_VAULT` (11,2) |
| `FLAG_RIME_CREST` | `MAP_GRAVEWOOD` sinkhole (10,12) → `MAP_ROOT_GALLERY` (4,3) | `MAP_ROOT_GALLERY` (4,2) → `MAP_GRAVEWOOD` (10,13) |
| `FLAG_RIME_CREST` | `MAP_DUSKMERE` old well (25,27) → `MAP_ROOT_GALLERY` (19,3) | `MAP_ROOT_GALLERY` (19,2) → `MAP_DUSKMERE` (25,28) |
| `FLAG_DUSK_SHORTCUT` | `MAP_DUSK_VAULT` (20,4) → `MAP_DUSKMERE` (26,28) | `MAP_DUSKMERE` (26,27) → `MAP_DUSK_VAULT` (20,5) |
| `FLAG_LANTERN_CREST` | `MAP_COOLING_CHAMBER` (15,3) → `MAP_ROOT_GALLERY` (15,4) | `MAP_ROOT_GALLERY` (15,3) → `MAP_COOLING_CHAMBER` (15,10), safely on the south bank |
| `FLAG_CREST_ANVIL` (FAR side, eastern reciprocal supplied by coordinator) | `MAP_RAILHEAD_SHAFT` (4,9) → `MAP_COPPER_MINE` (9,18) | Coordinator-owned `MAP_COPPER_MINE` (8,18) → `MAP_RAILHEAD_SHAFT` (4,10) |

The Lantern shortcut joins the two existing underworld networks only after the Lantern Crest, normally earned after the Anvil and Rime Crests; arriving from the gallery lands south of the unsolved cooling seam and cannot skip the controls. The Copper Mine link enters the shaft before the lava bridge, so it also cannot skip cooling. The shortcut from the vault is earned inside the Rime-gated vault. Neither route touches `MAP_OSSUARY_1`, `MAP_OSSUARY_2`, or their sealed six-crest gate. Existing Caldera arch and Anvil Hall gate are unchanged. The original single-parent `A_EXIT` mats remain intact and are not reused for new multibranch returns.

## Solvable authored puzzles

- **Cooling chamber:** From the south entry (9,12), interact with the solid iron **INTAKE VALVE** (anvil fixture) at (5,10), then the **RELEASE VALVE** (tool-wheel fixture) at (14,10). Neither control renders as a person. A note at (7,11) spells out this order. Release first is harmless and explicitly requests intake. The permanent `FLAG_EMBER_COOLED` turns **only** two molten tiles (9–10,7) into solid basalt `##` via `MapPatch`; all other lava remains impassable. Controls and the entry stay on the south bank; from the north bank the player can leave by the north passage even before solving. `MAP_EMBER_SPAN` has a real `EF_BRIDGE_V` at (11–12,7–9), lower lava height 0 and deck height 1, meeting both level-1 banks at rows 6 and 10.
- **Dusk vault:** At the plaque (9,10), the vow reads “roots remember, bells answer, lanterns guide.” Interact with the solid **ROOT SIGIL** (coffin carving, 6,6), **BELL SIGIL** (foxfire brazier, 12,8), **LANTERN SIGIL** (lantern pedestal, 17,6) in that order. The scripted anchors render as fixtures rather than people. Wrong input clears only the temporary `FLAG_DUSK_FIRST` / `FLAG_DUSK_SECOND` sequence and gives a retry hint. Completion persists `FLAG_DUSK_SHORTCUT` and patches both solid wall cells (19,4–5) to floor, opening the arch (20,4) and giving the Duskmere reverse arrival at (20,5) an inward step via (19,5). The ordinary barrow→gallery through-route never depends on this optional shortcut.

Neither puzzle uses a fluid simulation or adds a persistent `MapObj` chest/pickup. The new ladder objects are structural doors, not consumed persistent rewards. New maps have at most three objects each (the cooling chamber's three ladders); existing map counts remain below 48.

## Safe inspection spawns

- Ember: `MAP_EMBER_SPAN` (11,11) looking north shows the raised lava span; `MAP_COOLING_CHAMBER` (9,11) looking north shows the molten seam and valve area (avoid standing on (9,7) until solved).
- Dusk: `MAP_DUSK_VAULT` (11,11) looking north shows the marked three-sigil room; `MAP_ROOT_GALLERY` (11,10) shows the diverging root aisles; `MAP_GRAVEWOOD` (20,20) shows the winding TS_DUSK woodland and preserved through-road. All suggested cells are ordinary ground, not warp doors.

## Validation and integration

`tools/tests/test_ember_hollows.c` exercises paired and gated doors, actual barred/open shaft and barrow movement, both bridge heights and lava solidity, unsolved/solved chamber reachability, harmless vault reset and persistent shortcut, and the Gravewood essential routes. It runs via `cc -std=c11 -O0 -I src/game -I tools/tests -o build/world-expansion/test_ember_hollows tools/tests/test_ember_hollows.c && build/world-expansion/test_ember_hollows`. Existing `test_far.c` and `test_grim.c` also run from this isolated build directory. The safety agent's `test_puzzles.c` strict per-entry proof was rerun with `PZ_MAP` for DUSK VAULT (3 entries), COOLING CHAMBER (3), ROOT GALLERY (4), and EMBER SPAN (2): every search passed, zero failures. An actual Duskmere→vault inward walk is covered in the focused test to guard against reverse-entry traps. The Lantern cross-region seam has reciprocal regional rows. The Copper Mine reciprocal belongs to the east-region coordinator and is intentionally not edited here. Standalone `tools/test_field.c` now passes with the coordinator's puzzle-aware staged reachability checks, while dedicated focused coverage tests both initial entry sides and solved reachability. Shared integration must continue to provide `MapDef.depth/surface_map`, `Warp.required_flag`, guarded A_DOOR movement, and the generated `TS_DUSK` glyph-compatible tileset; no engine changes are requested here. Existing FAR map and story-flag enum ordinals can shift because GRIM IDs/flags precede FAR in the global include order; shared save-layout migration/verification is coordinator-owned. No save manifest or golden was edited here.
