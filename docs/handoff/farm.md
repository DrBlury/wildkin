# Farming and time: handoff

Owner: FARM system (docs/EXPANSION.md 7.1, 7.2). Branch based on `expansion` (d918146).
`make art && make && make test` is green. The 6 `-Wunused-function` warnings in party.c
(storage_move, storage_sort_*...) already exist on `expansion` (UI owner's helpers); farm/time
add none. `tools/tests/test_farm.c` has 45 checks.

## Done

**Time (`src/game/time.c`)**
- The clock: 1 game minute per field second, day 24 min, day counter turns at 06:00.
  `time_text(buf)` gives "DAY 3  14:05"; `time_is_night()` is 20:00-05:59.
- Tint via `field_tint()`: dusk 18:00-20:40 (warm, then blue), night, dawn 04:00-06:40, grey
  under rain. Only MF_OUTDOOR maps that are not MF_NIGHTLESS/MF_DEBUG. Palettes are reloaded
  when the 10-minute tint band changes (`time_update_tint`). Stacks with the storm tint.
- Weather: rolled each new day (day 1-2 always clear, ~1 in 4 rain). MF_RAIN maps always rain.
  Rain streaks are drawn by farm.c when it rains and the storm isn't on.
- `time_sleep()`: to 06:00 the next day, runs the new day, fades by re-entering the map.
  Called from every bed (script.c `bed_answer`) and the farmhouse bed.
- `WildSlot.when` is honoured in `roll_wild` (field.c): day-only / night-only slots.
- START menu shows the clock (menu.c); a HUD clock top-left when `opt.hud_clock` is on.

**Farm (`src/game/farm.c`)**
- 152 plots on WILLOW ACRE (144 soil + 8 orchard mounds), numbered row-major from the map rows.
- Tool ring on the farm: L/R cycle HOE, CAN, every seed/sapling, the 3 fertilisers and the
  sprinkler you carry (label top-right); A uses it on the faced plot (white corner cursor).
  Effects (clods, drops, seeds, sparks) with SFX; the player pauses 12 frames per action.
- Rules: till -> plant -> water -> grows 4 units/day when wet (+1 FERTILIZER); dry crops don't
  grow and never die. 12 field crops + apple/peach trees (12 days, no water, then fruit every
  3 days, solid). Regrowing crops (berries, chili, tomato, corn). RICH COMPOST/tending raise
  GREAT/PERFECT odds (+1/+2 yield); GROW MULCH keeps soil wet a second day. Sprinklers water
  the 8 plots around them each morning (pick up again with A).
- Shipping bin (SHIP ALL / KEEP ONE EACH), paid next morning. Processors: PRESERVES JAR
  (jam, pickles), FRUIT PRESS (BERRY JUICE / APPLE PRESS / PEACH NECTAR, craft's items),
  DRYING RACK (2 days: dried chili, dried fruit, sun seeds), up to 5 batches.
- Storage chest (STORE PRODUCE / TAKE ALL), keyed by item_code.
- Workers: WORK BOARD screen (ext_open) assigns 4 Shelf kin to WATER/TEND/HARVEST/GUARD/FORAGE/
  HONEY; suited types work twice as hard; they gain bond + XP each morning; found on the Shelf by
  species + pot (a withdrawn kin loses its job). They walk on the farm as overworld kin, are solid
  and can be talked to. Crows peck crops when nobody GUARDs.
- Berry patches (OBJ_BERRY, arg = patch id): pick 2-3, regrow in 3 days. On the farm they are
  BG overlays on the mounds; elsewhere OBJ sprites built at map load from the ts_farm crop art,
  squeezed into satchel bank colours 9-15. One berry kind per region range (farm.c berry_crop).
- A morning report dialog (only once you own the farm): pay, rain, worker results, crows,
  processors done.
- Items: 5 new goods in items/farm.inc (FRUIT JAM, PICKLES, DRIED CHILI, DRIED FRUIT,
  SUN SEEDS); SPRINKLER now sells for 800c. 36 icons in tools/icons/icons_farm.py.

**World (`src/game/world/farm/`)**: real WILLOW ACRE (40x36: yard, farmhouse stamp, pond,
4 wild glowberry bushes 50-53, fence + FARM_GATE decor, fields, work yard, orchard) and the
FARMHOUSE (work board, chest, bed, stove, bookshelf). REEVE (SCR_REEVE) stands by the FOR SALE
sign: deed 15,000c, or 10,000c after QUEST_REEVE_BERRIES (3 GLOWBERRY); the deed opens the gate
and gives FARM DEED, HOE, WATERING CAN, 5 radish + 3 carrot seeds; afterwards she sells
FARM_SHOP_STOCK. 7 lore entries (LSRC_REEVE, LSRC_FARM_NOTES = farmhouse bookshelf).

Verified in the ROM with `build/shot` (noon/dusk/night/rain tints, tilling/planting, workers
walking, REEVE, work board, START clock).

## Left

- REEVE belongs in MAP_LAND_OFFICE (east owns it; it has no door in Maple Village yet). Move her
  NPC line from world/farm/npcs.inc once the Land Office is reachable.
- traversal: `obj_interact` should leave OBJ_BERRY to farm.c (farm_interact runs first today).
  BIKE on R clashes with the tool ring only on WILLOW ACRE (farm.c reads L/R there only).
- UI: an options row for `opt.hud_clock`; START menu entry layout may want the clock elsewhere.
- Craft: jam/pickles/dried goods are IK_CROP (sellable); craft may want them as recipe inputs.
- World owners: place OBJ_BERRY patches on routes (ids per region, see farm.c berry_crop).
- No per-crop seasons; no quality stored in the bag (quality becomes extra yield).

## Shared files touched

- `src/main.c`: moved `#include "game/farm.c"` to after quest.c (needs menu/lore/quest APIs).
- `src/game/field.c`: `cell_attr` -> `farm_cell_attr(...)`; `map_load` -> `farm_map_loaded()`;
  kin sprite list gets `farm_field_kin()` (+4 slots); `roll_wild` honours `WildSlot.when`;
  prototypes.
- `src/game/script.c`: `farm_interact()` before `obj_interact`; `farm_draw_fx()` /
  `farm_draw()` around `field_draw_sprites()`; `bed_answer` calls `time_sleep()`.
- `src/game/menu.c`: 4 lines in `start_menu_draw` (clock window).
- Generated: `src/gfx_battle.h` (icons), `src/gfx_field.h` (decor text). No save layout change
  (FarmState 1.1 KB of the 3072 blob, TimeState 8 bytes).
