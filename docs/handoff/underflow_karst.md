# Tidal Underflow and Northern Karst handoff

Three new maps in the west/north regional scopes: `MAP_TIDAL_UNDERFLOW` (32×20, cave/depth 2), `MAP_KARST_CHAMBER` (28×18, cave/depth 2), `MAP_KARST_FROST` (22×16, snow/depth 2). Use named IDs: appending within regions can shift later global numbers, and the existing saved-layout rebasing handles this. Central integration verified a genuine pre-expansion version-7 save, including old visits, flags, all 21 puzzle bits and 16 secrets. Do not relocate IDs to a global tail; preserve regional prefixes and regenerate the manifest centrally.

## Entrances and gates

Coordinates are `(x,y)`, warp source → destination landing; reverse ladders are explicit, on plain floor, and land adjacent to rather than on another ladder.

| Direction | Warp → landing | Requirement |
| --- | --- | --- |
| Heron Fen → Reed Tunnel | `(12,8)` → `(3,10)` | none; original Fen mouth preserved |
| Reed Tunnel → Heron Fen | `(2,10)` → `(12,10)` | none |
| Reed Tunnel → Underflow | `(17,3)` → `(4,10)` | `FLAG_TIDE_CREST` |
| Underflow → Reed Tunnel | `(3,10)` → `(16,3)` | `FLAG_TIDE_CREST` |
| Reedwick → Underflow | `(23,23)` → `(26,5)` | `FLAG_TIDE_CREST` |
| Underflow → Reedwick | `(27,5)` → `(22,23)` | `FLAG_TIDE_CREST` |
| Port Brine → Underflow | `(35,33)` → `(26,14)` | `FLAG_TIDE_CREST` |
| Underflow → Port Brine | `(27,14)` → `(35,34)` | `FLAG_TIDE_CREST` |
| Underflow → Rootways | `(10,3)` → `(20,11)` | `FLAG_TIDE_CREST`; **west-side row only** |
| Rootways → Underflow | **coordinator to add** `(19,11)` → `(11,3)` | mirror `FLAG_TIDE_CREST` |
| Stormstep Cave → Karst | `(18,3)` → `(4,14)` | `FLAG_CREST_ANVIL` |
| Karst → Stormstep Cave | `(3,14)` → `(17,3)` | `FLAG_CREST_ANVIL` |
| Karst → Frost Spur | `(24,5)` → `(4,12)` | `FLAG_CREST_ANVIL` |
| Frost Spur → Karst | `(3,12)` → `(23,5)` | `FLAG_CREST_ANVIL` |
| Frost Spur → Timberline Sawmill | `(14,5)` → `(9,6)` | `FLAG_CREST_ANVIL` |
| Timberline Sawmill → Frost Spur | `(10,6)` → `(13,5)` | `FLAG_CREST_ANVIL` |
| Glimmer Caverns → Karst | `(34,14)` → `(23,12)` | `FLAG_CREST_ANVIL` |
| Karst → Glimmer Caverns | `(24,12)` → `(33,14)` | `FLAG_CREST_ANVIL` |

The three west onward exits require Tide on **both** ends, and crossing Underflow's continuous six-column channel additionally requires SURF. Reed Tunnel's current chute flows south toward the Fen landing. Its group-6 switch lowers the barrier in the east gallery, and the west/return route remains open even when the barrier rises. The Reed Tunnel instruction is carved into a solid, reachable rock face at `(1,7)` because `TS_TIDE` has no solid SIGNPOST prop; the other new signs use solid SIGNPOST decor. The existing hermit `(15,4)` and shard `(15,5)` remain at their coordinates. The Underflow side span `EF_BRIDGE_H(7,13,3,1)` crosses an actual water pocket at elevation 1 without bypassing the main SURF channel. SEA ROUTE's north rows 0–3 and both canonical connected edge coordinates are unchanged; islands, sandbar fringes and coves change only interior rows, leaving water gaps between land masses and the ferry intact.

North's sawmill branch passes through the frost spur. Push its `OBJ_BOULDER(15,10,0)` north twice with STRENGTH to `(15,8)`, then slide east across row 8; the stone stops the slide at `(14,8)`, directly below the north passage to `(14,5)`. Without the stopper, the slide carries east to `(19,8)` and a dry lower loop `(19,11)→(3,12)` is always open. On reload, boulder position resets, so retreat cannot soft-lock. The chamber uses `TS_SNOW`, a real `A_ICE` run, `ZONE_NONE` (not a fake wild habitat), and a visible signpost. Existing Rime and Glimmer floor progression gates were not touched. Cave flags include `MF_NOFLY`, with explicit surface anchors: West → Fen (Bell → Gull Isle); Stormstep/Karst/Frost → Foothills; Glimmer/Starfall → Frosthollow.

## Safe captures and future link

Suggested existing-map capture spawns (floor, not doors): Reed Tunnel `(3,10)`, Underflow west `(4,10)` and east `(26,14)`, Stormstep Cave `(17,3)`, Karst `(4,14)` and `(23,12)`, Frost Spur `(4,12)` or solved-slide landing `(14,8)`, Port Brine quay `(35,34)`. Set Tide/Anvil flags before staging onward cave screenshots; provide a SURF-capable Tide kin for the Underflow crossing and a STRENGTH-capable kin for the frost stopper. The inter-network Rootways join uses Underflow west-bank door `(10,3)` and the adjacent, safe incoming floor `(11,3)`. Central integration added the Rootways reciprocal row `(19,11) → (11,3)` with the same Tide gate. This connection does not cross the Underflow channel or give a dry route to Reedwick/Brine. A separate optional **future north stub only** could use Karst `(15,3)`; no north↔west Warp exists now.

## Validation and constraints

Direct host command: `cc -std=c11 -Wall -Wextra -Wno-missing-field-initializers -Wno-unused-function -o build/world-expansion/test_underflow_karst tools/tests/test_underflow_karst.c && build/world-expansion/test_underflow_karst`. This checks row dimensions/caps, solid reachable signs, portal collision/landings and mirrored flags, pre/post-crest gate predicates, actual Brine/Reedwick surface access, dry versus SURF crossings, switch/escape, traversable elevation bridge, karst branches, two STRENGTH pushes/ice stopper, and dry versus SURF Sea Route. Three new maps, **zero new persistent objects** (ladders, switch, barrier and loose stones are not persistent), one new elevation feature, no secrets/scripts. No global build, art/save generation or commit performed here. The coordinator's atlas/ID integration and global test_field pass should be treated as separate integration checks, not inferred from the focused host run.
