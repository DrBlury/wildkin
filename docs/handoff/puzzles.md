# Puzzle solver handoff

`tools/tests/test_puzzles.c` (run by `make test`, about 9 s) proves that
every map can be played through with the game's real movement rules. It
replaces the old trust in `FLOOD_SOLVED` (which assumed every gate and
barrier open and ignored boulders).

## What it searches

For every map except the debug viewer maps (`MF_DEBUG`) and the traversal
fixtures `TEST SHORE/ICE/HALL/DARK` (dev maps driven by `test_travel.c`):

- **State**: the player's cell and elevation level (elev.c), every boulder (boulders with the same `arg`
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
  and map edges, and on maps with a height layer (elev.c: cliffs, stairs,
  decks, tunnels) every step goes through the game (`elevated`), since the
  level you stand on decides where you can go.
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

Environment knobs for debugging: `PZ_MAP=<id or name>` solves one map
(`PZ_MAP="RIME HALL"`), `PZ_PATH=1` prints the event path to the hardest
target and to a Hall Master, `PZ_TRACE=1` prints progress, `PZ_CAP=<n>`
changes the entry limit. On a failure it prints the offending state and the
event path that reaches it.

## Per-map results

"events" = pushes + switch presses + legends + pick-ups + re-entries on the
event-minimal solution; "moves" = steps along that solution (a slide, a
current ride or a pad jump counts as one).

| map | abilities | states | hardest target | events | pushes | moves |
| --- | --- | --- | --- | --- | --- | --- |
| MAPLE VILLAGE | all | 2 | door to MAPLE SHOP | 0 | 0 | 326 |
| VOLT HALL (1) | none | 8 | MASTER FARA | 3 | 0 | 55 |
| CURRENT HALL (2) | none | 16 | MASTER MAREN | 4 | 0 | 73 |
| ANVIL HALL (3) | none | 197566 | MASTER BRONWEN | 12 | 12 | 149 |
| RIME HALL (4) | none | 232 | warden (MASTER SIGRUN: 8 events, 101 moves) | 8 | 8 | 108 |
| LANTERN CRYPT (5) | none | 32 | HALL MASTER MORWEN | 6 | 0 | 170 |
| MIRROR HALL (6) | none | 8 | MASTER VESPER | 6 | 0 | 203 |
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

6. **MAPLE VILLAGE (terraces from the elevation merge): a ledge trap.**
   The ash ledges at x 33-35, row 28 drop into a five-cell yard (row 29,
   x 33-37) walled by trees, the woodpile and a hay bale: one hop and there
   was no way back (10 soft-locked states). Fix (`world/village/data.h`):
   the hay bale moved from 32,29 to 29,29, so the yard opens west onto the
   field below.

`tools/test_field.c` no longer floods with `FLOOD_SOLVED`: it floods the
map as it is, and on puzzle maps (boulders, plates, gates, switches,
barriers, pads, ice, currents) it leaves people, satchels, doors and exits
to `test_puzzles` and only checks signs and grass over every entrance.

## The Hall redesigns (hall order 1-6, difficulty rising)

The Halls CURRENT, RIME, LANTERN and MIRROR were plain walks (15-75
moves, no events). They are now real puzzles, all on flat ground, all
solvable without SURF or STRENGTH, with the wardens (sight 1, so they
never walk onto a puzzle cell) beside the route and a way home from the
Master's dais. Numbers are the solver's event-minimal solution from the
door to the Master.

- **CURRENT HALL** (`world/west/data.h`, 17 x 22, door 8,21): 4 events,
  73 moves. Isles in a pool joined by one-way channels; three tides of
  sluice gates (barriers). Switch A (west isle) opens the east rise and
  shuts the gate before MAREN; switch B (east isle) / B' (middle isle)
  swap the west and east crossings and open the north rise; a bell
  switch *inside* the east chute rings tide C (the north landing's gate)
  every time the water carries you over it. Answer: A, ride the east
  chute (bell), B', then A again, cross west, rise, rise. The west chute
  (x 1) takes you from the dais or the west isle back to the door.
  `test_west` checks the start is shut and the final tides open.
- **RIME HALL** (`world/north/data.h`, 19 x 27, door 9,26): 8 pushes,
  101 moves (108 for the dais warden). Two rinks between rock rows: the
  lower rink is a pure slide maze (about 23 slides, from the gap at 9,23
  to the gap at 15,15); the upper rink has one pumice boulder (16,7) that
  must be pushed to 10,5 so that a slide east along row 5 stops under the
  dais gap (9,4). The rinks were found with a random search that rejected
  any layout with a soft-lock, then confirmed here. `test_north` checks
  the Master is out of reach with the pumice at home and reached with it
  at 10,5.
- **LANTERN CRYPT** (`world/grim/data.h`, 23 x 23, dark, door 11,22):
  6 events, 170 moves. The spine (x 11) ends in gates A and B under the
  false wall (11,7) into the sanctum. Candle switch 3 (west gallery)
  opens the east wing's inner door; switch 2 (east inner) opens the west
  wing's inner door; switch 1 (east inner) lowers gate B but raises the
  east walk behind you; switch 0 (west inner) lowers gate A but raises the
  west door. Star pads lead out of each sealed wing (east walk <-> a
  niche on the spine, gallery foot <-> the vestibule). Switch 2 lies on
  the way to switch 1, so walking back over it shuts the west door again:
  step on it once more (the solver's answer does exactly that).
- **MIRROR HALL** (`world/far/data.h`, 21 x 22, door 2,21): 6 events,
  203 moves. Six rooms in mirrored pairs (L1|R1, L2|R2, L3|R3), each
  split by a mirror wall with one doorway barrier. Switch k lowers the
  west room's doorway of row k+1 and raises the east twin's (0x80
  barriers). Seven pad pairs cross between the halves; the Master stands
  in R1's east half. Found with an abstract search over pads/switches for
  the longest event-minimal solution, then placed and confirmed here.
  `test_far` checks the doorway pairs are mirrored.

`tools/make_demo_save.c` takes a new `beaten` flag (every warden on the
map already beaten) so a Hall can be replayed in the ROM without bouts.

## Checked in the ROM

CURRENT HALL (after the redesign): `build/make_demo_save current.sav 32 8 20
calm beaten`, then the solver's answer as a `build/shot` script with
`peek`s of the player and `sw_on` after every leg: every stop (west isle,
switch A, the chute foot, east isle, the bell ride, the middle isle,
switch B', switch A again, the west crossing, the north landing, the
dais at 8,3) and every tide state matched the search, and A in front of
MAREN opens her Master dialogue.


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
- The LANTERN CRYPT's barriers, pads and satchels are sprites and are not
  darkened by the light circle (engine behaviour for every dark map): the
  glowing pads and wisp gates read as deliberate cues, but a designer may
  want them dimmed.
