# Area-local field graphics

The field uses the area's `MapDef.tileset` as a **ROM catalog**, not a
fixed VRAM image. `src/game/field_tiles.c` packs only the terrain tiles
that area actually draws into the 768-tile scene allocation. Decorations
are loaded only for the kinds declared by the map. A normal map change,
menu return, or battle return discards the previous field cache.

This leaves room for richer local decorations without making every map
pay for all buildings and terrain in its regional catalog. It does not
increase the GBA's VRAM or add new artwork automatically.

## Ownership and composition

- Terrain, autotiles, elevation art, and dynamic farm tiles retain their
  original ROM tile IDs while `render_cell` composes its three layers.
- Decor blocks have actual, contiguous VRAM addresses. `decor_entry`
  marks them with `FIELD_DECOR_ENTRY` (bit 15) until final composition.
  Field palette banks are **0–7**, so that bit is available internally;
  it is stripped before writing a hardware screen entry.
- `field_tile_entry` resolves terrain IDs into compact resident slots,
  copying a tile from ROM on first use. Palette and flip bits survive.
  Tile zero is permanently transparent. Invalid references or a full
  cache set `field_tiles_failed` and resolve to transparent instead of
  reading arbitrary art or overwriting UI VRAM.
- Animation uploads follow the resident mapping, not ROM tile numbers.
  Newly loaded terrain and decor start at their current animation frame.
- Every visible ring cell is written, including both margins of a narrow
  room. An unavailable neighbour uses the current tileset's out-of-bounds
  terrain. Ready seam previews replace those cached boundary cells.

Compatible horizontal neighbours can share the cache while both are
visible. Their preflight reserves the whole regional terrain catalog
plus the combined decor set; if that does not fit, the existing fade and
fresh area load are used. Slots are not evicted mid-visit, avoiding stale
screen entries and visible tiles changing underneath the player.

## Sprite restoration

Battle portraits occupy OBJ tiles 0–127, including the field's rain and
emote range at 64–83. `field_load_tileset` restores the field's object art
and player palette before loading travel's compatible extended palettes.
This prevents portrait fragments appearing as rain after a bout. Farm
and berry OBJ graphics are restored after the shared travel upload, so
their reserved colours are not replaced by another area's graphics;
restoring art does not reset workers or crop state.

Travel's small objects now use OBJ tiles 552–603, separate from the ash
flake at 640. Offscreen sprite culling uses the actual sprite dimensions.
Ordinary and storm rain both normalize their repeating screen phase when
the camera moves. NPC rendering additionally checks the current map;
the existing story/schedule visibility rules still determine who belongs
there.

## Authoring and validation

Keep source terrain IDs within the 10-bit catalog space (1024 IDs), field
palettes within banks 0–7, and total resident scene tiles within 768.
The generator's existing per-catalog limits still apply. New per-area
catalogs can be registered through `tools/tilesets` as before; shared art
need not be duplicated merely to obtain area-local residency.

Run `make test` and `make`. `tools/tests/test_area_tiles.c` traverses every
map and its boundary, verifies resident pixels against ROM before and
after animation, checks unused tiles and UI memory, exercises all dynamic
farm art, and tests invalid-reference and overflow handling.
`test_field_sprites.c` reproduces portrait-to-rain corruption and verifies
restoration, clipping, rain placement, and OBJ ownership. Elevation and
seamless-transition tests also exercise the packed representation.

The current full-map traversal checks 172 maps: 169 use fewer tiles than
loading the whole regional catalog. Examples (including declared decor):

| Area | Previous tiles | Resident tiles |
| --- | ---: | ---: |
| Maple Village | 505 | 478 |
| Your House | 187 | 174 |
| Whisper Meadow | 432 | 230 |

These are complete static-map traversal counts, not just one viewport.
Dynamic farm states are checked separately; no new detailed art is
included in these measurements.
