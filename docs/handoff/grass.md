# Handoff: tall grass, in-grass look and dithering

## What was wrong
Tall grass drew its front blades on the BG3 top layer (rows 9-15 of every
grass cell). That layer is fixed to the map, so the cell *above* an actor also
cut through their head and shoulders: people showed only a hat plus a band of
face, 32x32 kin were cut by the neighbouring cells, and mid-step the sprite
was striped by two or three cells. Every tall-grass cell was the same 16x16
tile (hard rows, obvious tiling), there was no rustle and nothing moved.

## What changed
* **tools/grass.py** (new): procedural tall grass for every tileset, built
  from hand-drawn tuft templates (tuft, fan, pair, stalk, reed, frond, moss)
  recoloured per style. `install()` is called from
  `gen_field_gfx.finish_tileset()` and, for every registered variety:
  * regenerates the metatile (the old hand art's orphaned tiles are
    compacted away) and adds `NAME_B`, `NAME_C` variants; the legend char now
    picks the three variants by cell hash (6/5/5 of 16),
  * gives each variant its own 4 BG tiles animated as a 4-pose wind cycle
    (one `TileAnim` per variety; each variant runs at its own phase),
  * renders the *front blades* of every pose, 4 rustle frames (whole cell +
    front blades) and 2 particle frames, emitted as `GrassDef`/`GRASS_SETS`
    in `src/gfx_field.h`,
  * sets `A_GRASS` on every variant and clears their BG3 top layer.
  Varieties (REGISTRY): town/city/coast meadow grass, wild meadow + REEDS +
  new **FLOWERGRASS** (`w`, flowers shimmer) + new **GOLDGRASS** (`g`),
  coast DUNEGRASS, snow DRIFT (snow-capped tips, snow puffs), cave MOSS (glow
  tips), grim ASH_GRASS / GRAVE_BRUSH (bracken) / MIRE_REEDS (wisp motes),
  volcanic EMBERBRUSH (glowing seed heads, sparks) / EMBERMOSS, dream
  MOONPETAL (pulsing petals). Crypt BONEDUST and dream LIB_DUST are floor
  dust and were left alone. Preview: `cd tools && python3 grass.py OUT.png 3`.
* **src/game/grass.c** (new, included after field.c): per frame, every
  grass cell an actor's footprint overlaps (people 16 wide, kin/bike 32
  wide, both cells mid-step) gets a 16x16 sprite of its front blades, sorted
  just in front of anyone standing in that cell -- only the lower body hides
  behind ragged, dithered tips. Stepping in (hook in `actor_start_move` /
  `actor_start_hop`) starts a rustle: a repaint of the cell behind the actors,
  the rustling front blades over them, two particles. Also a dithered shadow
  (two checker phases chosen by world position) under everyone on open
  ground. Uploads happen in vblank (`grass_present`, end of
  `field_animate_tiles`): only on wind-pose changes / rustle frame changes,
  plus a full refresh after menus (detected by a gap in `frame_count`).
  Palettes: object banks 7 (and 6 when a tileset's grass uses two BG
  banks) are copies of the (tinted) BG banks, so time-of-day/storm/ash tints
  apply. Consequence: on maps with tall grass, 6 (5) NPC palette slots
  instead of 7 (`grass_npc_slots()`).
  Object tiles: 132..251 (party-icon area, unused in the field).
* **field.c** hooks only (grep `grass_`): prototypes block, one call each in
  `field_load_tileset`, `field_animate_tiles`, `field_draw_sprites` (+ list
  size 96, NPC slot limit), `actor_start_move`, `actor_start_hop`.
* **Dithering** (tools/terrain_common.py): `autotile()` jitters its signed
  distance with a 4x4 Bayer threshold (`DITHER`, per call `dither=`), so every
  path/shore/lava/pond/canal band boundary in every tileset is ordered-dithered;
  the grass/path edge is redrawn as grass -> shaded lip -> sandy rim -> path
  over ~2 px of checker. Trees (overlay) got a checker shadow pool at the
  trunk; GRASS2 got a dithered sunlit patch (large-scale variation). Tall
  grass fades from ground to shadow through ordered dither with a wavy edge.
* **make maps** was broken (render_maps.py only knew the old 3 tilesets and
  a `maps.h` that no longer exists). tools/render_maps.c now renders every
  non-debug map from the game's own renderer (host build);
  render_maps.py is a wrapper. Output: `build/maps/<id>_<name>.png`.
  make_media.py's world clip updated to the new names.
* **tools/grass_shots.py**: scripted mGBA shots of player/follower/wild kin
  in grass in 12 regions (+ a rustle strip) and `--compare` sheets.
* Tests: test_field checks every grass variant is A_GRASS with no BG top;
  test_west coast tile cap 385 -> 410 (the real per-map 512 budget check
  still passes everywhere).

## Maps with new grass
* WHISPER MEADOW (village/data.h) rows 11-15 x 27-35: FLOWERGRASS patch.
* COPPERLINE ROAD (east/data.h) rows 9-14 x 2-13: GOLDGRASS field.
* ELDERWOOD HEART (east/data.h) rows 22-24 x 29-33: FLOWERGRASS.
Legend chars added to the wild tileset: `w`, `g` (both A_GRASS, same zone).

## Verification
`make art && make && make test` green, zero warnings. Before/after:
`build/grass_compare_zoom.png` (3x, standing + mid-step, 12 regions),
`build/grass_compare_full.png` (1x); raw shots in `build/grass_before`,
`build/grass_after` (`rustle.png` = frame strip of a step).
Regenerate: build the old ROM in a scratch tree, run grass_shots.py there
and here, then `grass_shots.py --compare`.

## Leftovers / ideas
* Cliffs were not re-shaded (another agent is reworking cliffs/elevation);
  `terrain_common.bayer()` is there for them.
* Sand/dirt terrain cells (not autotiled) still meet grass on a hard cell edge.
* Rustle/particle timing is in grass.c (`GRASS_RUSTLE_STEP`, `PARTS` in
  grass.py); wind speed per style (`period`).
