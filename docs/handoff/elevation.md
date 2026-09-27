# Elevation handoff

Heights, cliffs, stairs, ledges, bridges walked over one way and under the
other, tunnels and hidden passages; the engine and art for every outdoor
tileset; a test map; Maple Village redesigned as the showcase. The
authoring reference for region designers is **docs/ELEVATION.md**.
`make art && make && make test` is green, no warnings; `make maps` renders
every map through the game renderer.

## Done

- **Engine** — `src/game/elev.c` (included by `field.c` before
  `map_decode`). A map's optional height layer (`MapDef.elev`, one char per
  cell: `0`-`3`, stairs `^ v < >`, ledges `_`) and feature rectangles
  (`MapDef.feats`: `EF_BRIDGE_H`, `EF_BRIDGE_V`, `EF_TUNNEL`, `EF_HIDDEN`)
  decode into `map_elev[]` (EWRAM, 8 KB): ground, deck height, drawn height,
  kind, cover. Cliff faces and tunnel mouths are derived. `elev_attr()` is
  folded into `cell_attr_raw()` (faces solid, ledges `A_LEDGE`, stairs /
  mouths / hidden open), so every old check sees cliffs as walls.
- **Movement** — `Actor.level` for the player, people, their kin, the
  follower and wild kin. `elev_enter()` decides every step (stairs only
  along their direction, bridges only along their axis on top, same
  height otherwise); ledges hop down only from the rise above;
  `cell_walkable_lv()` / `npc_at_lv()` / `wild_at_lv()` make occupancy
  per level. Wandering people keep to their level and out of hidden
  passages; wild kin don't cross cliffs or charge across them; wardens
  don't spot across them and walk levels correctly; talking to people and
  taking satchels needs a real step between you (signs read across);
  SURF isn't offered off a cliff or a deck. Hidden passages: a rustle and
  a "!" the first time per visit.
- **Drawing** — faces, ledges, stairs, mouths, rims and cast shadows on
  BG2 (autotiled per quadrant: caps, inner/outer corners); decks, tunnel
  tops and hidden cells' art on BG3. OBJ priority per actor
  (`elev_obj_prio`): 1 on a deck / tunnel top and just south of one, 2
  under it. Grass blades and ground shadows (grass.c) follow the actor's
  priority, and no blades are drawn over someone on a deck.
- **Save** — `SaveData.level` (was `pad0[0]`, same size, version 5): the
  level + 1; 0 (older saves) derives it from the cell and the facing.
- **Art** — `tools/elevation.py`: faces, rims, shadows, stairs (north/south
  and stepped side stairs), ledges, bridge decks (both axes), tunnel mouths;
  ~80 tiles per tileset, colour roles per tileset (`elevation.ROLES`):
  town, wild, city, coast, farm, snow, cave, volcanic, dream, grim.
  `gfx_field.h`: `ElevArt` table, `TilesetDef.elev`.
- **Maps** — TEST HEIGHTS (`src/game/world/elev/`, new region, debug WARP
  only) exercises everything. MAPLE VILLAGE redesigned: two terraces either
  side of the Maple Run ravine (creek + lane at height 0); the lane (the
  north-south road, edges x 19-20) runs **under** the Maple Run bridge that
  carries the east-west road (edges y 17-18) **over** it; side stairs from
  the lane; a wooded ridge along the north with bumps; the NW bluff; the
  Almanac knoll; the raised Hearth plaza; the sunken Bout Ring; the dell
  with the lily pond reaching the map edge; the south-east field with
  ledges; a hidden gap in a thicket to the SUNSEED satchel. Every door,
  NPC, sign, satchel and the fly point still work (the Land Office moved
  to (24,22): its warp/sign in `world/east/` follow). Edge contracts
  unchanged.
- **Tools** — `tools/render_maps.c` (kept from both branches: the game
  renderer, now with `--levels` overlay, name filters, satchels and OBJ
  priorities; files `OUTDIR/<id>_<name>.png`); `tools/tests/harness.h`
  floods over (x, y, level) (`flood_ex_lv`, `reached_lv`; `flood_ex` keeps
  its signature); `tools/tests/test_elevation.c` (decoding, step rules,
  stairs of every kind, ledges, bridge over/under, tunnel, hidden passage,
  OBJ priority, follower, NPC and wild levels, reach, save, flood, a lint
  of every height layer, the art tables); `tools/make_media.py elevation`
  (docs/images/elevation_{front,under,over}.png) and a new village clip.
- Makefile: `main.o` now depends on `src/game/world/**` (map edits
  rebuilt nothing before).

## Puzzles on heights, saved secrets, TEST HALL (2026-09-27)

- **Level-aware puzzles** (travel.c, farm.c; docs/ELEVATION.md 3.1 and 7):
  every map object has a level (`TObj.level`). Boulders keep theirs: no
  stairs, no pushing off a cliff edge, never into a face, mouth or hidden
  passage; **pushed south off a ledge a boulder drops** to the ground below
  (lands past the ledge, like a hopping player: chosen over "ledges are
  walls" because it is a new, readable puzzle move and the same rule as the
  player's hop). Over and under bridges and tunnel tops by the pusher's
  level (deck boulders are pushed from the deck; walkers on the other level
  pass by). Plates/switches/gates/barriers answer on their own level; ice
  and currents stop at height changes and don't act on someone on a deck;
  teleport pads put you on the partner's level. Farm: `plot_lv`,
  sprinklers per terrace, workers keep to their terrace, tools and the
  cursor only reach plots on your level. Surfing isn't switched on by
  standing on a deck over water. OBJ priority of object sprites follows
  their level.
- **TEST HEIGHTS terrace puzzle**: a pumice boulder in a chute of bushes on
  the east plateau (24,12) → off the ledge (24,14) → west onto the plate
  (22,15) → the gate (27,13) at the foot of the new knoll stairs (27,12)
  sinks → chest on the knoll (27,10). (25,14) is now a face (the old ledge
  test uses x 26.) The map's gate and chest are the last persistent
  objects in map order (nothing after TEST HEIGHTS has any: tested), so no
  saved puzzle bit moved.
- **Hidden passages are found for good**: `TravelState.secrets[8]` (bit per
  EF_HIDDEN in map order, 12 used of 64), appended to the travel module
  blob (41 → 49 bytes); save still version 5, an older save's 41-byte blob
  loads with nothing found (tested, plus a round trip). Found passages show
  a worn gap (path under the crowns; the whole cell down a N-S passage) or,
  in a cliff face, an open cave mouth; the "!" plays once ever.
- **TEST HALL soft-lock fixed** (`world/travel/data.h`): the boulders sit in
  dead-end slots (x 3 and x 6, walls around them) so they can only be
  pushed deeper in and never reach the gate corridor or the mat; the
  current row starts at x 5 (test_travel follows).
- **Solver** (`tools/tests/test_puzzles.c`): boulder level in the state
  (y | level << 6), positions (level, cell), a validated fast path on height
  maps (plain ground, same level) — elevated maps went from "simulate every
  step" to fast, the whole run is ~10 s including the TEST maps; TEST maps
  are no longer skipped (one without an entrance starts at the WARP menu's
  spot, `dbg_find_spot`, which is then its way out); chests, legends and
  ferries need a real step to be used (like people), matching
  `field_try_interact`. `PZ_MAP` takes a map name too.
- **Tests**: `tools/tests/test_elev_puzzles.c` (boulders on cliffs,
  stairs, decks, tunnel tops, ledge drops; the terrace puzzle played
  through; ice, currents, pads, switches and plates with height layers
  poked into TEST ICE / TEST HALL; farm sprinklers, tools and workers on a
  poked terrace; secrets found, reloaded, saved, older save, changed look,
  cliff-face mouth; lint of objects and plots).
- ROM check (`make shot`, demo saves on map 82): the drop, the plate and
  the gate; the passage before/after and after reloading an in-game save
  (docs/images/elevation_terrace_*.png, elevation_secret_*.png).

## Screenshots

- `docs/images/elevation_front.png`, `elevation_under.png`,
  `elevation_over.png` (in the ROM, via build/shot).
- `docs/images/village.gif` / `village.png` (crossing the bridge),
  `docs/images/place_town_clear.png`, `docs/images/world.png`.
- `make maps` → `build/maps/00_maple_village.png`,
  `build/maps/82_test_heights.png`.

## Known limits / next

- The other towns (Lumen City, Cindermoor, Dreamspire, Duskmere,
  Frosthollow, Sky Isle, Port Brine, Gull Isle) are next: their tilesets
  already carry the art; follow docs/ELEVATION.md section 6. Tune a
  tileset's colours in `elevation.ROLES`.
- Tile room: coast 478 and grim 497 of 500 tiles after the art (test_west's
  coast cap raised to 490). Drop a tileset's ROLES entry if it never uses
  heights and needs the room.
- Puzzles on heights are done (below); farm plots only exist on WILLOW
  ACRE, which has no height layer yet: `plot_lv` follows it once it gets
  one (the lint checks plots stand on plain ground of their terrace).
- Decks are one level above their ground (no double-height bridges);
  bridges have no support pillars; no tall grass under decks (a rustle
  would still play for someone walking over it).
- Wandering people may take stairs inside their two-cell range; wild kin
  wander only grass on their own level (a chasing one may take stairs).
- Puzzles: boulders can't be lifted back up a ledge (by design: reload the
  map); objects other than boulders can't be authored on a deck; the
  boulder drop has no hop arc (it slides two cells down). The found-gap
  look uses the tileset's path quadrants (none on a tileset without paths:
  the trunks' lower half just disappears).
- Adding a hidden passage (or a gate/chest/legend) to a map shifts the
  saved bits of every later map: append new ones to maps late in the
  order, or accept that found secrets of later maps reset.
