# Farming and time: handoff

Owner: FARM system (docs/EXPANSION.md 7.1, 7.2). Branch is based on `expansion` (6118872).

## Done

- **Farm tileset** (`tools/tilesets/ts_farm.py`). It replaces the placeholder copy of the wild tileset and uses 291 tiles and 87 metatiles. It has:
  - ground: grass, flowers, path, pond water, dirt yard, and field soil `SOIL`/`SOIL2` (A_SOIL)
  - soil states for `dyn_cell`: `TILLED`, `TILLED_WET`, `TILLED_FERT`, `TILLED_WET_FERT`
  - mounds: `ORCHARD` (A_SOIL) and `BERRY_MOUND` (solid)
  - fence overlays: `FENCE_H`, `FENCE_V`, `FENCE_END`, `FENCE_SW`, `FENCE_SE`
  - crop overlays, drawn on transparency: `SEEDED`, `SPROUT`, `SAPLING`, and `<CROP>_GROW` / `<CROP>_RIPE` for all 12 field crops
  - fruit trees as `YOUNG`, `FRUIT`, `APPLE`, `PEACH` with `_TOP`/`_BOTTOM` pairs. The crown goes on BG3 of the cell above the orchard cell.
  - `SPRINKLER` overlay
  - `FARMHOUSE` stamp, 6x5 cells, door at column 2, row 4
  - The map legend and palette-bank plan are documented at the top of the file.
- **Decor catalog** (`tools/decor_farm.py`), registered in `gen_field_gfx.all_decor()`:
  - outdoor: `SHIPPING_BIN`, `PRESERVES_JAR`, `PRESS`, `DRIER`, `FOR_SALE`, `FARM_GATE`
  - interior: `WORK_BOARD`, `FARM_CHEST`
  - The farm tileset also reuses village props through `USES_DECOR`, including `BEEHIVE`, `SCARECROW` and `HAY_BALE`.
- The art is regenerated: `src/gfx_field.h` and the viewer maps in `world/debug/`. The art lint passes and `make test` is green.

## In progress

Nothing is half-written in the C code. The design below is worked out but not coded:

- **FarmState** (at most 3072 bytes, with a version byte):
  - plots: 144 x {crop, growth, flags (tilled, wet, fert, mulch), care}. Each plot is an A_SOIL cell of WILLOW ACRE, indexed in row-major order.
  - 64 berry patches: {berry, growth, flags}
  - 4 workers: {job, species, slot, pot}. A worker is re-identified on the Shelf by its species and pot, because Shelf slots shift.
  - 3 processors
  - shipping bin counts and pending coins
  - storage chest
  - quality counts per crop: GREAT and PERFECT
- **Growth**: plots that are wet at the day rollover grow +4 units, or +5 with FERTILIZER. After growth, WET is cleared. Then rain, sprinklers, mulch and WATER workers wet the plots again for the new day.
- **Berry patches**: the art must use OBJ sprites off the farm, because other tilesets' BG palettes are not ours. Use OBJ bank 8 entries 9-15 (the item-ball palette uses only 1-8) and OBJ tiles 512-639.

## Not started

- `time.c`:
  - tint: dusk, night, dawn and rain for `MF_OUTDOOR` maps that are not `MF_NIGHTLESS`
  - re-tint with `field_load_palettes()` when the tint band changes
  - weather roll each day
  - `time_sleep`, `time_text`, and the HUD clock on the canvas
- `farm.c`:
  - the whole farming loop, tool ring (L/R), animations, harvest and quality
  - shipping bin, workers and the work board screen, processors, berry patches
  - `FARM_SHOP_STOCK`
- The real WILLOW ACRE and FARMHOUSE maps in `world/farm/data.h`. They are still placeholders.
- `scr_reeve` (the deed for 15,000c, or 10,000c after a quest to bring 3 GLOWBERRY), farm NPCs, lore entries, the quest, and the farm item icons (`icons_farm.py`).
- `tools/tests/test_farm.c`.

## APIs other owners should call (planned; they do not exist yet)

- `time_text(char *buf)` returns text like "DAY 3  14:05" for the START menu.
- `time_sleep()` should be called from `script.c` `bed_answer` after `hearth_rest()`. It skips to 06:00 the next day and runs `farm_new_day()`.
- `farm_interact(fx, fy)` should be one line in `field_try_interact`, placed before `obj_interact`. It handles soil, water refill, farm decor and OBJ_BERRY.
- `farm_draw(0)` goes before `field_draw_sprites()` and `farm_draw(1)` after it. They draw workers, berry sprites, effects and rain.
- `FARM_SHOP_STOCK` / `FARM_SHOP_STOCK_COUNT` are for `shop_open_stock()`.
- `farm_berry_interact(patch)` is for OBJ_BERRY.
  - Patch ids: east 0-9, west 10-19, north 20-29, grim 30-39, far 40-49, village/farm 50-63.

## Notes

- `make test` is green. `make` was not re-run after the art change, but it compiled before and the header changes only add data.
- Edits outside my files: one line in `tools/gen_field_gfx.py` `all_decor()` appends `decor_farm.FARM_DECOR`. The generated files `src/gfx_field.h` and `src/game/world/debug/*` were regenerated.
- The existing `field_tint()` stub in `time.c` returns the colour unchanged.
- L/R are planned as the farm tool ring on the farm map only. This may clash with a BIKE registered to R.
- WILLOW ACRE still uses the placeholder rows. Its fence gate should be `FARM_GATE` decor. After purchase, clear its `map_decor` entry at run time so the gate opens.
