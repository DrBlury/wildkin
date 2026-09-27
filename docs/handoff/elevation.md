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
- Puzzle tiles (ice, currents, boulders, pads) and farm plots don't know
  levels: keep them on flat ground.
- A hidden passage is "found" only for the visit (a rustle and a "!"), not
  saved; there is no changed look after finding it.
- Decks are one level above their ground (no double-height bridges);
  bridges have no support pillars; no tall grass under decks (a rustle
  would still play for someone walking over it).
- Wandering people may take stairs inside their two-cell range; wild kin
  wander only grass on their own level (a chasing one may take stairs).

## Town art pass (deck styles, frost cliffs, Hollow Bridge, Maple Village v2)

- **Deck styles** (`tools/elevation.py`, `deck_styled()`): besides the wooden
  deck, `'iron'` (riveted plates, lit edges, girders with a riveted web) and
  `'stone'` (flagstones in a running bond between parapets with a coping).
  Chosen per tileset in `ROLES` (`'deck'` + `'deck_roles'`, six colours of
  one bank; docs/ELEVATION.md section 8): volcanic = iron (Cindermoor's
  Iron Bridge), city = pale sandstone (Lumen's Boulevard bridge), dream =
  moonstone (the Dream Bridge), snow = frosted granite (the Hollow Bridge,
  Sky Isle's Stone Span). Town, wild, coast, farm and grim keep wood.
  Per-bridge styles would need an engine change (a second deck table).
- **Snow cliffs**: the snow ROLES now use the light end of the granite ramp
  (`rk_hi` / `sn_dk` / `rk_lt`, outline `rk_dk`) and `'frost': True` caps the
  lit top edge of every slab with snow, so Frosthollow's valley reads bright.
- **Frosthollow's Hollow Bridge** is 3 rows (was 7): the south bank juts out
  as a spur (18-21, rows 26-29, level 1) that the bridge lands on, and the
  Hollow lane passes under it on rows 24-25 only, so you are hidden for the
  two steps under the deck instead of wandering six rows under it. The lane
  under the bridge is still the only way between the west Hollow and the
  Steam Hollow at the foot of the cliffs (the bathhouse), besides the
  terrace stairs (26,30) and the one-way ledges. test_north follows (19,24).
- **MAPLE VILLAGE redesigned again** (same size, doors and edges): four
  levels; the north ridge and the Almanac knoll are level 3 over **two-row
  faces** whose edge steps in and out; the west bluff and a wooded bump run
  down the west edge; the raised Hearth mound; High Street (2) with the
  Hearth Hall and the shop, whose two-row face juts out over the pond dell;
  the lily pond runs off the west and south edges; the Maple Run widens into
  a mill pond and leaves by the south edge; the south-east terrace drops
  into the field by stairs and a ledge yard; the hidden gap in the thicket
  (33-34,33) still leads to the SUNSEED; tree borders vary in depth. The map
  was painted with a scratch script (not committed): `data.h` is the source
  of truth (header comment above `TOWN_ROWS`).
  Moved: doors home (7,7), bakery (14,9), Almanac (30,5), Hearth Hall
  (5,23), shop (12,23) (garden house 33,24 and the Land Office 26,25 in
  world/east unchanged); Elder Bram (11,13), kid (7,14), kid by the pond
  (9,29); signs (17,16) (18,7) (26,6) (8,22) (15,22) (17,9); fly point
  (5,24). Satchels, Marlo, the farmer, the bridge and the edge openings
  are where they were. Tests updated: test_field (movement on row 10, the
  home door, Elder Bram). `tools/make_media.py elevation` re-shot.
- Tile budget: `SCENE_TILE_MAX` is 768 now (farm seasons merge), so the
  per-map decor budget is no longer tight (Maple Village 505, Frosthollow
  510). Tileset sizes: snow 435, volcanic 410, city 407, dream 395.

Screenshots (ROM, build/shot): `docs/images/towns_art/` — `cm_iron_over`,
`cm_iron_under`, `lumen_stone_bridge`, `ds_stone_bridge`, `sky_stone_span`,
`fh_bridge_over`, `fh_bridge_front`, `fh_bridge_under` (hidden under the
3-row deck), `fh_valley`, `mv_home`, `mv_knoll`, `mv_high_street`,
`mv_dell`, `mv_hidden` (the "!" in the thicket gap), `mv_over`; renders
`maple_village_map.png`, `frosthollow_map.png`.
