# Puzzle solver handoff

`tools/tests/test_puzzles.c` (run by `make test`, about 9 s) proves that
every map can be played through with the game's real movement rules. It
replaces the old trust in `FLOOD_SOLVED` (which assumed every gate and
barrier open and ignored boulders).

## What it searches

For every map except the debug viewer maps (`MF_DEBUG`) and the traversal
fixtures `TEST SHORE/ICE/HALL/DARK` (dev maps driven by `test_travel.c`):

- **State**: the player's cell, every boulder (boulders with the same `arg`
  are interchangeable, so their positions are sorted), the 16 switch groups,
  opened gates, answered legends, and one "satchels picked up" bit.
- **Moves are played by the real code.** The state is written into
  travel.c's run-time objects and the player, then `player_try_move()` (or
  `surf_begin()`) runs and frames are stepped with `travel_update()`,
  `actor_step()` and `travel_player_arrived()` exactly like
  `field_player_update()`, until the player and every object are at rest.
  The new state is then read back. This covers boulder pushes (STRENGTH vs
  pumice, plates, gates, blocked cells), ledge hops, ice slides, currents,
  pads, switches and barriers, surfing on and off, doors, ladders, exit mats
  and map edges.
- **Fast path, checked against the game.** A step between two plain cells
  (walkable, nothing happens on arrival, no door, mat, ledge, edge or
  object), a step between two plain water cells while surfing, and a plain
  hop onto the water skip the frame loop. `validate_fast_path()` replays
  every such step of every map through the real code, and the test fails on
  any disagreement, so the solver cannot drift from the game.
- **Nodes** are (objects state, component), where a component is the cells
  joined by plain steps that work both ways. The search is a 0-1 BFS: an
  event (a push, a switch press, a legend answered, a satchel picked up,
  leaving and coming back) costs 1, everything else 0.
- **Entrances**: every door into the map, every walkable (or, with SURF,
  surfable) cell of a linked edge, ferry landings and, with FLY, fly points.
  Leaving through any exit and coming back through any entrance resets the
  boulders and switches and keeps gates, legends and satchels, as travel.c
  does on `map_load`.

## What it checks

1. **Targets** are reachable from the entrances: every person (standing
   beside them, or across a counter), satchel, chest, legend and ferry, every
   door or ladder out, every linked edge and the exit mat.
2. **No soft-locks**: from every reachable state some exit is still
   reachable (a reverse search over all found transitions). Map reloads only
   happen through exits, so a state with no way out is a real soft-lock.
3. No endless forced move (an ice / current loop), and the state space was
   searched completely (limit 12M search entries; `PZ_CAP` overrides it).

**Abilities.** Halls (VOLT, CURRENT, ANVIL, RIME, LANTERN CRYPT, MIRROR)
must be solvable with no SURF and no STRENGTH: they are self-contained.
Every other map is searched with SURF + STRENGTH (+ FLY landings). Maps
where an ability changes anything (STRENGTH boulders, surfable water, fly
points) are searched a second time with the other ability set for
soft-locks.

**Assumptions / limits.** People stand on their home cell (wanderers are
treated as still). Satchels are modelled as all present or all taken (one
bit): picking one up is an event that clears them all, an approximation
that is only optimistic if a later satchel is what walls you in. Wild kin are ignored. The follower
is off (it can only swap places with you).

Environment knobs for debugging: `PZ_MAP=<id>` solves one map,
`PZ_TRACE=1` prints progress, `PZ_CAP=<n>` changes the entry limit. On a
failure it prints the offending state and the event path that reaches it.

## Per-map results

"events" = pushes + switch presses + legends + pick-ups + re-entries on the
event-minimal solution; "moves" = steps along that solution (a slide, a
current ride or a pad jump counts as one).

| map | abilities | states | hardest target | events | pushes | moves |
| --- | --- | --- | --- | --- | --- | --- |
| VOLT HALL | none | 8 | MASTER FARA | 3 | 0 | 55 |
| CURRENT HALL | none | 2 | MASTER MAREN | 0 | 0 | 15 |
| RIME HALL | none | 1 | warden (MASTER SIGRUN: 18 moves) | 0 | 0 | 28 |
| LANTERN CRYPT | none | 2 | warden | 0 | 0 | 75 |
| ANVIL HALL | none | 197566 | MASTER BRONWEN | 12 | 12 | 149 |
| MIRROR HALL | none | 1 | MASTER VESPER | 0 | 0 | 35 |
| BRAMBLEWOOD | all | 1899 | edge to MAPLE VILLAGE | 0 | 0 | 53 |
| CLOCKWORK SPIRE | all | 706 | satchel | 1 | 1 | 22 |
| WHITECROWN PEAK | all | 52 | legend HOARFANG | 11 | 11 | 83 |
| EMBER TUNNEL | all | 76994 | satchel | 3 | 3 | 42 |
| FROSTPINE PASS | all | 2 | edge to FROSTHOLLOW | 0 | 0 | 50 |
| FROSTHOLLOW | all | 2 | door to HOT SPRING | 0 | 0 | 41 |

All other maps (towns, routes, interiors, legend lairs) pass too; the test
prints a line for every map with puzzle objects, puzzle tiles or ledges.

## Broken puzzles found, and the fixes

1. **Boulders could be pushed onto exit mats** (any map; found on TEST
   HALL, and reachable in the old ANVIL HALL): a boulder on the mat seals
   the only way out. Fix: `boulder_push()` in `src/game/travel.c` now also
   refuses `A_EXIT` cells (one flag added to the existing mask).
2. **CURRENT HALL: the Master's dais was a one-way trip.** The up-current
   carries you onto the dais and nothing leads back: after beating MAREN you
   were stuck for good. Fix (`world/west/data.h`): a down-current at x 4,
   rows 4-6, from the dais into the east-flowing channel of row 7, which
   lands on the middle island; the island's down-current leads back to the
   door. The dais is still only reached by the up-current (`test_west`
   checks both).
3. **RIME HALL: the ice field had no way back.** The only way out is to
   stop on (6,12) and slide down the gap at (6,16), and (6,12) can only be
   reached from below, so anyone who went up could never leave (36
   soft-locked states, including standing beside MASTER SIGRUN). Fix
   (`world/north/data.h`): one ice rock at (7,15); sliding east along row 15
   now stops at (6,15), right above the gap. The solver tried a rock on
   every cell; only (5,15) or (7,15) fix it on their own.
4. **ANVIL HALL: jams and an unsearchable state space.** Four pumice
   boulders roamed two open rooms and could be pushed through the gate
   corridors. A boulder pushed down the corridor onto another one sealed the
   player in the upper rooms (a soft-lock), and the rooms together had more
   than 10^8 boulder positions. Fix (`world/far/data.h`, `npcs.inc`,
   `satchels.inc`): each chamber is now an aisle (x 7-9) with two walled pens
   off it, one boulder and one plate per pen. Each pen door has a brazier
   two cells in, so a boulder can never be pushed out into the aisle (you
   would have to stand in the fire), and a lone boulder can never shut you
   in a pen. The intended solution is the same idea (a few pushes per
   boulder): chamber 1 "up twice, then in", chamber 2 "up twice, then out".
   The warden, guide and satchel moved to the aisle and the entrance row.
5. **BRAMBLEWOOD: two STRENGTH boulders loose in the open wood.** They
   could be pushed anywhere in the wood and jam its narrow lanes (450 000
   states, 2 minutes to search). Fix (`world/east/data.h`,
   `world/village/data.h`): a stump at (30,34) narrows the Elderwood gap to
   x 31 and one STRENGTH boulder at (31,33) guards it (push it aside); the
   edge contract (x 30-31 on row 35) is unchanged. `test_east` now expects
   one boulder.

`tools/test_field.c` no longer floods with `FLOOD_SOLVED`: it floods the
map as it is, and on puzzle maps (boulders, plates, gates, switches,
barriers, pads, ice, currents) it leaves people, satchels, doors and exits
to `test_puzzles` and only checks signs and grass over every entrance.

## Checked in the ROM

`make shot` + `build/shot game.gba script.txt anvil.sav` with a demo save
in ANVIL HALL (8,21): the solver's chamber-1 solution (west pen: up twice,
then right; east pen: up twice, then left) puts both pumice boulders on the
plates and the first gate sinks, exactly as the search predicts.

## Left

- Satchels are one "all taken" bit; per-satchel bits would be exact but
  multiply the states.
- Wandering people are searched on their home cell.
- The test maps (TEST HALL etc.) are skipped: the TEST HALL's STRENGTH
  boulder can still be pushed into the gate corridor and shut you in its
  chest room (it is a traversal fixture, not part of the game).
- CURRENT HALL and MIRROR HALL are short (15 and 35 moves, no events): a
  designer may want to make them harder; the solver will say if a change
  breaks them.
