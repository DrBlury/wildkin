# UI and QoL handoff (docs/EXPANSION.md 7.6)

## Done

- **Key item icons**: `tools/icons/icons_ui.py` paints BIKE, WATERING CAN, HOE,
  FARM DEED, FERRY PASS, TOWN MAP, CREST CASE, RECIPE BOOK and ENERGY FLASK
  (24x24, index 1 white). `src/gfx_battle.h` is regenerated and
  `src/game/items/key.inc` points each key item at its `ICON_*`.
- **UI art** (`tools/gen_ui_gfx.py`, regenerated `src/gfx_ui.h`):
  - rarity gems as 8x8 OBJ tiles `gem_obj_gfx[5]` + `gem_obj_pal` (grey
    common, green uncommon, blue rare, gold star legend, purple spiral fusion);
  - Hall crest medallions `crest_gfx[6]` (VOLT TIDE ANVIL RIME LANTERN DREAM)
    drawn in their type's badge bank (`crest_bank`, `crest_paper`) plus
    `crest_empty_gfx` (bank 15). `--preview DIR` writes `gems_crests.png`.
- **Options struct** (`options.h`): still 16 bytes; two pad bytes became
  `opt.registered` (bag item + 1 registered to SELECT) and `opt.shelf_box`
  (box last viewed; new kin go there first).
- **Shelf boxes in party.c** (storage stays packed; `BoxMon` pad bytes now
  hold `box` and an arrival stamp `order`, so boxes persist in the save with
  no format change): `storage_boxes_sync`, `storage_box_count/start`,
  `storage_add_box`, `storage_add` (active box, then next with room),
  `storage_take`, `storage_move`, `storage_sort_box/all` (SORT_NUMBER, LEVEL,
  TYPE, RARITY, NEWEST), `storage_sort_type_boxes`, `storage_find_type`.
- **Field use of the new supplies** in `item_use_field`: IK_HEAL_CURE,
  IK_TEA_ALL, IK_REVIVE.
- **SELECT register**: `registered_item()` / `registered_item_use()` in
  party.c, hooked into `field_update` (one line in script.c). With nothing
  registered SELECT still opens the Lorebook.

`make`, `make test` are green with all of the above.

## In progress

Nothing half-written is committed: every change above compiles and the
existing tests pass. The screens that use the new plumbing are not built yet.

## Not started

- START menu: MAP / FIELD / QUESTS entries, DAY n HH:MM clock (from
  `gtime.day/minute`), scrolling, running a module's dialog in the menu.
- Bag: pocket tabs (the 7 pocket dots currently overflow the left panel),
  SORT, REGISTER action, per-pocket cursor memory, routing key/farm/lure
  items to direct use and food to the kin picker. **Bug to fix first:**
  `draw_item_icon` (gfx.c) indexes `item_icon_gfx/pal` by item id instead of
  `ITEMS[item].icon` and reads out of bounds for items >= 26.
- Lantern Shelf screen (TEAM page + 8 box pages, icons for visible rows in
  OBJ banks 1-6, gems in bank 7, WITHDRAW/DEPOSIT/MOVE/RELEASE with double
  confirm, SUMMARY of stored kin, SORT/BOXES BY TYPE/FIND BY TYPE menus).
- Almanac filters (all/seen/owned, type, rarity, region by map id range),
  gems in the list, fusion signature "Woven from X + Y energy", habitats with
  day/night marks and legend lairs, SEEN/OWNED header.
- Quest log screen (quest.c, via `ext_open`; test with an injected table
  since no region defines quests yet).
- Summary: rarity + field abilities line, stored-kin source, B back to the
  Shelf (B currently does nothing unless opened from the team).
- Options screen rows MUSIC, MUSIC VOLUME, HUD CLOCK, BOUT SPEED, BIKE AUTO
  with scrolling and two-line help.
- Lorebook chapter scrolling (14 chapters overflow the list), visible unread
  markers (the small font has no N/E/W, so "NEW" is invisible today), `lb.ids`
  sized to LORE_COUNT (it is capped at 40 per chapter now).
- Crest case screen, crests on the WARDEN CARD, `tools/tests/test_ui.c`.

## APIs other owners should call

- `storage_add(&mon)` / `storage_add_box(&mon, box)` / `storage_take(i)` /
  `storage_get(i)`: always go through these so box counts stay right; call
  `storage_boxes_sync()` if you ever edit `storage[]` directly.
- `registered_item_use()`: SELECT in the field (already wired).
- `quest_get/quest_set/quest_done` (quest.c, unchanged); `quest_log_open()`
  is still the stub.
- `shop_open_stock(items, count)`, `pc_open(deposit)`, `ext_open(...)`
  unchanged.

## Notes

- Edit outside my files: `src/game/script.c` `field_update`, one line before
  the Lorebook shortcut:
  `if (key_hit(KEY_SELECT) && !player.moving && registered_item_use()) return;`
- `src/gfx_battle.h` is generated: whoever merges icon modules should rerun
  `python3 tools/gen_battle_gfx.py` after merging (icon names are ICON_BIKE,
  ICON_WATERING_CAN, ... and must stay unique across tools/icons/*).
- Palette plan for the screens still to build: gems are OBJ sprites (tiles
  at 120-124, OBJ bank 7) so they never fight BG palettes; kin icons reuse
  OT_ICON(i) / OBJ banks 1-6 like the team screen; bank 9 (menu backdrop)
  must be loaded (any `screen_begin` does it) before drawing METAL/HOLLOW
  badges or the ANVIL crest.
- The music engine reads `opt.music_vol` as 0 full, 1 low, 2 mid.
