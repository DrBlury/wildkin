# Traversal handoff

Branch `worktree-agent-ab9ced5310f9ef4aa`. The worktree started on the old
initial commit (89bf1cb). I reset it to the expansion base (6118872) before
doing any work.

## Done

- `tools/gen_travel_gfx.py` (new, stdlib only, deterministic) writes
  `src/gfx_travel.h`. It runs cleanly: the town map uses 345 tiles and the
  voyage sea uses 98 (the budget is 512 each). Previews:
  `python3 tools/gen_travel_gfx.py --preview DIR`. The header contains:
  - Palettes. `travel_misc_palette` is OBJ bank 8: the satchel colours
    stay at indices 1-8 and seven new colours follow. `travel_fx_palette`
    is OBJ bank 15: the emote colours stay at indices 1-6 and nine new
    colours follow. `TPAL_*` are the banner ink indices.
  - Sprites:
    - 16x16 objects (`TO_*`): boulder, plate up/down, switch off/on, pad
      (4 frames), chest closed/open, ladder, gate slot.
    - 16x32 objects (`TT_*`): gate plus 3 sinking frames, barrier (4
      crackle frames plus off), ferry post.
    - 8x8 particles (`TF_*`): snow, ash, ember, dust, spark, sparkle,
      bubble, streak, town-map markers.
    - 16x16 effects (`TX_*`): wake, splash, shadows, flash, cursor, pin,
      gulls, current chevrons, ripple.
  - `travel_bike_gfx[6]`: 32x32 frames in the player palette (down, up and
    left, 2 pedal frames each).
  - `travel_boat_gfx[2]` and `travel_crest_gfx[7]` (the 6 crests plus an
    empty slot, with their own palette).
  - The town map of the Vale: `travel_map_tiles`, `travel_map_screen`
    (30x20) and `travel_map_palette`. `WM_SPOTS[WM_*]` holds the pixel
    position of every place in the world graph.
  - The voyage sea: 256x160, it wraps horizontally.
- Nothing in the game uses the header yet. It is not included in
  `main.c`, not in the Makefile ART list and not in the CI diff list.

## In progress

- The art is generated, but I have not looked at the previews, so the look
  may still need polish. The bike side view and the town-map biome
  borders are the first things to check.

## Not started

All of the C work:

- `travel.c`: abilities, bike, objects, puzzles, screens, items.
- `field.c`: engine changes.
- The script.c hooks.
- The test maps in `world/travel/`.
- `tools/tests/test_travel.c`.
- The icons in `icons_travel.py`.
- The Makefile, CI and main.c wiring.

This is the design I worked out; follow it or change it:

- **Include order.** `travel.c` is compiled before `battle_ui.c`, where
  `game_mode` and `MODE_*` are defined, and before `menu.c`, where
  `ext_open` is defined. So:
  - Forward-declare `ext_open`, `screen_begin`, `start_menu_open` and
    `field_return`.
  - Put the glue that needs `battle` / `game_mode` / `bag_screen_open` in
    `world/travel/scripts.c`, which is compiled after them.
  - `KEY_*` is defined later in `modules.c`. Compare the key against
    `ITEMS[ITEM_BIKE].param` and similar instead.
- **Map objects.** Draw them as OBJ sprites in tiles 256-511:
  - banner 256-319 (64 tiles, text rendered with `target_set`)
  - legend front sprite 320-383
  - bike 384-399
  - object and fx sheet in the rest

  Keep an EWRAM `obj_grid[64*64]` cell index so `travel_attr` is O(1). It
  is called very often. Rebuild the objects in `map_load`, because tests
  flood-fill right after `map_load`. Boulders then reset whenever you
  leave a map, which is also the softlock guard.
- **Ladder.** Have `travel_attr` add `A_DOOR|A_SOLID`. `test_field`
  requires every WARPS entry to sit on an `A_DOOR` cell, and walking into
  the ladder then climbs it like a door.
- **Seamless edges.**
  - Add a ring-buffer origin (`ring_ox`/`ring_oy`) so that translating
    coordinates after a crossing re-renders identical content into the
    same slots.
  - Draw neighbour cells beyond linked edges, decoded from
    rows/cells/stamps/decor.
  - Unclamp the camera on seamless edges.
  - Load the neighbour's decor kinds only if they fit in 512 tiles;
    otherwise that link falls back to the 8-frame dip.
  - A link is seamless only if the tileset and the palette tint class
    match.
- **Dark maps.** Build a per-line WIN0H table through `oam_line_win0h`
  (DMA0). In `field_render_view` (vblank) set:
  - BLDCNT = 0xFD (darken BG0/2/3/OBJ/BD, not the BG1 UI)
  - WININ = 0x1F, WINOUT = 0x3F
  - BLDY of about 10

  Do not touch DMA1 or REG_IE. Only enable it on frames where
  `field_update` ran; `start_menu_open` → `field_setup_bg` must turn it
  off. Fold warp fades into it (shrink the radius and ramp BLDY), because
  `set_brightness` would otherwise clobber it.
- **Surf state.** Derive it from the player's cell when a map loads or the
  tileset reloads. Saves are restored through `map_load`, not
  `field_enter_map`. The current `travel_validate` sets `surfing = 0`,
  which strands a player who saved on water.
- **MF_DEBUG test maps.**
  - `field_try_interact` must call `obj_interact` before `debug_examine`.
  - Restrict the debug L/R parade and `debug_parade_spawn` to viewer maps
    (those with `cells`). Otherwise R, which also toggles the bike, adds a
    parade to the test maps.
- **Puzzle floors.** No tileset has ice or current terrain yet (the
  coast, snow and other sets are placeholders). The ice and current tests
  need a travel-owned floor overlay for the test maps.

## APIs other owners should call

These are planned. Only the existing stubs exist today.

- `travel_award_crest(CREST_*)`
- `travel_has_crest(CREST_*)`
- `travel_boat_to(map, x, y)`: for now it only warps.
- `travel_field_menu_open()`: START → FIELD.
- `worldmap_open(0/1)`: START → MAP.

Planned object argument conventions:

| Object | `arg` |
| --- | --- |
| `OBJ_PLATE`, `OBJ_GATE` | the group (gates stay open once solved) |
| `OBJ_SWITCH`, `OBJ_BARRIER` | the group |
| `OBJ_PAD` | the partner pad's id (pads pair by `arg` within a map) |
| `OBJ_FERRY` | the destination map (lands next to the ferry there whose `arg` is the source map) |
| `OBJ_LEGEND` | the species |
| `OBJ_CHEST` | an item id; 255 is a TRINKIT mimic, 254 a HOARDMAW mimic |
| `OBJ_LADDER` | none; it uses the WARPS entry on its cell |
| `OBJ_BERRY` | passed to `farm_berry_interact(arg)` |

Town-map pixel positions are the `SPOTS` table in `tools/gen_travel_gfx.py`
(Maple Village is 104,110). Region owners should set their FlyPoint
`map_x`/`map_y` to match.

## Notes

- Build and test status is unchanged from the base. The baseline `make`
  and `make test` (field, game and core suites) passed at the start. I
  have not edited any C file, so they should still pass. I did not re-run
  them after adding the generator, because nothing includes its output
  yet.
- I made no edits outside my own files. The only new files are
  `tools/gen_travel_gfx.py`, `src/gfx_travel.h` and this document.
- Wiring still to do:
  - Add `python3 tools/gen_travel_gfx.py` to `make art`.
  - Add `src/gfx_travel.h` to the Makefile ART list and the CI diff list.
  - Add `#include "gfx_travel.h"` after `gfx_battle.h` in `main.c`.
- OBJ tiles 400+ also hold the battle FX (`OT_FX`). `battle_ui` reloads
  them, but the evolve scene does not. If the field overwrites 400-511,
  restore the sparkle tiles before evolving, or keep that range free.
