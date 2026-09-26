# Traversal handoff

The gameplay is implemented on top of the art (`tools/gen_travel_gfx.py` →
`src/gfx_travel.h`). `make art && make && make test` is green (field,
game, core and the new travel suite). The only compiler warnings are the 6
pre-existing unused Shelf-box functions in `party.c` (UI owner).

## Done

All in `src/game/travel.c` unless noted.

- **Map objects** (`MapDef.objs`) become run-time objects in `map_load`
  (`travel_map_loaded`). An EWRAM cell grid makes `travel_attr()` O(1).
  Boulders and switches reset whenever a map loads (the soft-lock guard).
  Solved gates, opened chests and answered legends persist in
  `travel.puzzle` (bits numbered in map order, then object order; tested
  to stay <= 128).
- **Object arguments** (the convention every region should use):

  | Object | `arg` |
  | --- | --- |
  | `OBJ_BOULDER` | 0 needs STRENGTH, 1 "pumice" (pushable without it) |
  | `OBJ_PLATE` / `OBJ_GATE` | group; a gate opens for good once every plate of its group holds a boulder |
  | `OBJ_SWITCH` | group 0-15; stepping on it toggles every barrier of the group |
  | `OBJ_BARRIER` | group (low 4 bits); bit 7 = starts lowered. Barriers start raised |
  | `OBJ_PAD` | pads with the same arg on a map are partners |
  | `OBJ_FERRY` | destination map; you land on the cell below the ferry there whose arg is the map you left |
  | `OBJ_LEGEND` | species (static bout, no running, gone once won or befriended) |
  | `OBJ_CHEST` | item id; 255 TRINKIT mimic, 254 HOARDMAW mimic |
  | `OBJ_LADDER` | none: `A_DOOR|A_SOLID`, walks into its WARPS entry |
  | `OBJ_BERRY` | patch id for `farm_berry_interact()` (solid; the farm owner draws it) |

- **Puzzle tiles:** A_ICE sliding (until blocked or off the ice), A_CURRENT
  (west's convention: direction = DIR_HI<<1 | DIR_LO, carried per cell),
  pads (flash, short input freeze), switches, plates, gates (sink animation).
- **Abilities** need the crest plus a party kin with the species flag and
  level (SURF 20, STRENGTH 20, FLY 30). Species carry no size, so the
  "size AVERAGE or bigger" rule is not checked.
  - SURF: A facing water (or FIELD menu). You ride the kin (drawn under
    you, bobbing, wake/ripple); step onto land to get off. Surf state is
    derived from the player's cell every frame, so saves made on water load
    correctly. `MapDef.water_zone` kin spawn and swim on water while you
    surf; those bouts use `SC_SEA`.
  - STRENGTH: A on a boulder (or FIELD menu) turns it on for the map.
  - LIGHT: widens the light circle on `MF_DARK` maps.
  - FLY: town map in fly mode, visited fly points (the Sky Isle is always
    offered), fade-in landing.
  - TELEPORT / WAYSTONE: to the door mat of the last Hearth Hall
    (`travel.last_hearth`, set on entering any `MF_HEAL` map).
- **Bike:** BIKE key item or R in the field (not on MF_DEBUG maps), speed
  4, not indoors, auto-mounts outdoors with `opt.bike_auto`. 32x32 frames.
- **Ferry + voyage:** 500c or FERRY PASS, sailing cutscene (A skips),
  `travel_boat_to(map, x, y)` (x = 255 lands next to the ferry back).
- **Town map** (`worldmap_open(0/1)`), with markers for visited places,
  a blinking "you are here" pin (interiors resolve to their town through
  WARPS) and the fly cursor. **Crest case** screen (CREST CASE key item).
- **FIELD menu** (`travel_field_menu_open`) lists only what works right
  now. **LURE INCENSE** (param*10 steps; slots with weight <= 5 come 3x as
  often, `field.c roll_wild`).
- **Dark maps:** per-line WIN0 light circle + BLDY darkening (BG1 UI never
  darkened); switched off by `field_setup_bg()` and all traversal screens.
- **Location banners** slide in when you enter an outdoor/dark/town map
  with a new name.
- **Test maps** (`world/travel/`, reach them with the debug WARP menu):
  TEST SHORE (surf lake + island satchel, ferry, ladder), TEST ICE (ice
  pond, STRENGTH boulder, legend HOARFANG, ferry, ladder), TEST HALL
  (pumice/plate/gate, switch/barrier, pads, chest, mimic chest, currents),
  TEST DARK.
- **Reachability:** `tools/tests/harness.h` has `flood_ex(x, y, mode)` with
  `FLOOD_SOLVED` (gates/barriers open, boulders ignored, pads followed) and
  `FLOOD_SURF` (A_WATER without A_DEEP). `flood()` is unchanged (walk
  only). `tools/test_field.c` now floods with `FLOOD_SOLVED`, plus
  `FLOOD_SURF` on maps with a `water_zone`, and `map_entry` falls back to a
  ferry landing, a fly point, then the walkable cell nearest the middle
  (maps reached only by boat or FLY, e.g. the Sky Isle).
- `tools/tests/test_travel.c`: 60+ checks driving all of the above frame by
  frame, including the save round trip.
- Verified in the ROM with `build/shot`: surfing + water kin, dismount,
  bike, START menu with MAP/FIELD, FIELD menu, town map, hall
  plate/gate, ice slide, dark circle, voyage + banner.

## Shared files edited

- `src/game/field.c` (mine): hooks in `map_load`, `cell_attr` (split into
  `cell_attr_raw`), `field_load_tileset`, `field_setup_bg`,
  `field_render_view`, `field_draw_sprites` (FieldSprite gained `dy`,
  `shape`; kind 4 = map object; list size 80), `follower_active`,
  `player_try_move`, `field_player_update`, `field_enter_map`, wild kin on
  water (`wild[].water`) and the lure in `roll_wild`.
- `src/game/script.c`: `wild_touch` uses SC_SEA while surfing;
  `field_draw` calls `travel_dark_frame`.
- `src/game/menu.c`: START entries MAP (with TOWN MAP) and FIELD (crest or
  BIKE); EXIT is dropped and rows get 14 px when more than 9 entries;
  `bag_use` runs IK_KEY items directly (no kin picker).
- `tools/tests/harness.h`, `tools/test_field.c` (see above).
- Not touched: Makefile, main.c, gen_field_gfx.py, world.h, generated files.

## Left

- Seamless map edges (neighbour drawn beyond the edge, no fade). Edges
  still use the 8-frame fade.
- Weather particles from the sheet (snow on MF_SNOW, ash on MF_ASH) are
  not drawn yet; the tiles are loaded (`OT_TF`).
- Regions must place their objects (Volt Hall switches, Anvil Hall pumice,
  Mirror Hall pads, ferries at Port Brine/Gull Isle, legends), award
  crests with `travel_award_crest`, and set FlyPoint `map_x/map_y` to
  `WM_SPOTS` (Maple Village is 104,110).
- `battle_ui.c` still sends a lost bout to MAP_REST; it could use
  `travel.last_hearth` + `hearth_spot()`.
- Polish: the follower overlaps the wider bike sprite a little; the
  test hall's mid-map wall rows use wall-top tiles.
- OBJ tiles 256-399 and 640-765 are traversal's in the field; they are
  reloaded in `field_load_tileset()` after every menu, bout and screen.
