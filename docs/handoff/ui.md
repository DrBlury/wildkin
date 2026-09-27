# UI and QoL handoff (docs/EXPANSION.md 7.6)

`make art && make && make test` are green, with zero ROM warnings. Every
screen below was checked in the real ROM with `build/shot`.
`tools/tests/test_ui.c` has 91 checks.

## Done

### Earlier groundwork

- Key-item icons, rarity gems (`gem_obj_gfx`, OBJ tiles 120-124, bank 7)
  and crest art (`crest_gfx`) in `tools/gen_ui_gfx.py`.
- `opt.registered` / `opt.shelf_box`.
- Shelf boxes in party.c (`storage_*`), field use of the new brews and
  the SELECT register.

### START menu (menu.c)

- Entries: ALMANAC, LOREBOOK, KIN, BAG, SHELF, MAP, FIELD, QUESTS, CARD,
  OPTIONS, ADMIN, SAVE, EXIT.
  - ADMIN (in red) needs ADMIN MODE on (`opt.admin`, from the title's debug
    menu). See docs/handoff/admin.md.
  - MAP needs the TOWN MAP.
  - KIN and FIELD need a kin.
  - SHELF needs the TWIN CRYSTAL.
- The list shows 8 rows and scrolls, with arrows.
- A clock window uses `time_text()`.
- MAP, FIELD and QUESTS call `worldmap_open(0)`, `travel_field_menu_open()`
  and `quest_log_open()`. When a module answers with a message instead of
  opening a screen, the message runs over the field and the menu comes
  back (`start_menu_after_module`).
- The WARDEN CARD is a bigger window with the six crest medallions (it
  loads bank 9 itself, since the card sits over the field).

### CREST CASE

`crest_case_open()` (ext screen): the six crests, and for each one what it
gives and which Hall awards it. `modules.c` routes KEY_CREST_CASE to it.
It goes back to the bag, the START menu or the field.

### Options

- A table (`OPT_ROWS_DEF`) that scrolls, with two lines of help per row.
- Rows: TEXT SPEED, BOUT ANIMATIONS, SOUND, BOUT SPEED, KIN FOLLOWS, HUD
  CLOCK, BIKE AUTO, AUTOSAVE.
- **The music session adds MUSIC / MUSIC VOLUME as two table rows after
  SOUND.** They are not added here.

### Bag

- Seven pockets, with a tab strip (LEFT/RIGHT or L/R).
- The cursor and scroll are remembered per pocket.
- SELECT changes the order: AS FOUND, A TO Z, MOST FIRST.
- Key items get REGISTER / UNREGISTER, and the registered one is marked
  SEL in the list.
- Routing:
  - Supplies, shards and food open the team picker.
  - Key items, seeds, fertiliser, lures, waystones and the HUSH BELL are
    used directly. After a successful direct use (not the bell), the bag
    goes back to the field.
  - Materials explain themselves.
  - In a bout, unusable items are greyed out and refused.
- `item_battle_usable()` calls `battle_item_kind_usable()`, so
  IK_HEAL_CURE, IK_TEA_ALL and IK_REVIVE now work in bouts.
- **Fixed:** `draw_item_icon` now uses `ITEMS[item].icon` (via
  `item_icon_index`), so it no longer reads out of bounds.

### LANTERN SHELF (`pc_*` in menu.c, still MODE_PC)

- Page 0 is the TEAM; pages 1-8 are the boxes. Use LEFT/RIGHT or L/R.
- Each row shows a 32x32 icon (OBJ banks 1-5), the name, a rarity gem and
  the level. The left panel shows the portrait, the types and HP.
- A opens a menu:
  - on a box kin: SUMMARY / WITHDRAW / MOVE / RELEASE (asked twice);
  - on a team kin: SUMMARY / DEPOSIT (goes to the box last viewed).
- MOVE carries the kin, with a floating icon. There is a "PUT AT THE END"
  row, and a full box refuses the kin.
- START opens the tools:
  - SORT THIS BOX / SORT ALL BOXES (NUMBER, LEVEL, TYPE, RARITY, NEWEST);
  - BOXES BY TYPE;
  - FIND BY TYPE: while a search is on, matches show in green and SELECT
    jumps to the next one. B ends the search.
- Every `storage_*` helper is now used.

### Summary

- It can show a stored kin (`summary_open_shelf`). UP/DOWN walk through
  the box, and B goes back to the Shelf on that kin.
- The INFO page has a rarity gem and name, and a FIELD line (field
  abilities). The STATUS row was dropped: the left panel already shows it.
- It says "Grows with a strong bond" for EVO_BOND.

### Almanac (dex.c)

- START/SELECT opens a FILTER panel:
  - SHOW: ALL / MET / FRIENDS;
  - TYPE: any of the 18;
  - RARITY;
  - PLACE: 7 regions, taken from wild zones (land and water) and
    OBJ_LEGEND lairs by map id range, and inherited along growth chains.
- The list shows the filtered count and gems for kin you have met.
- The detail page shows:
  - a gem by the name and a RARITY line;
  - for fusion kin: "Woven from the energy" + "X + Y" once met;
  - in the habitats: DAY/NIGHT marks, legend LAIRs and "The FUSION LOOM".

### Quest log (quest.c)

- An ext screen with open quests first and DONE ones greyed. A shows the
  goal on the scrolling panel.
- Its table is read through `quest_defs` / `quest_def_count`, so tests can
  inject quests. No region defines a quest yet.

### Lorebook

- The chapter list scrolls (8 rows).
- NEW now shows, in red with the big font.
- `lb.ids` is sized LORE_COUNT.

### Kin viewer (debug.c)

The help text was shortened, and the badges moved to rows 15-16 on the
right, so they no longer overlap.

## Left

- **`time_text()` is a placeholder in time.c.** The farm owner's version
  replaces it. Keep the signature `time_text(char *buf)`.
- **Town map / FLY picker:** traversal owns `worldmap_open`. The START menu
  just calls it.
- **No quests exist yet.** Regions add them in `world/<region>/quests.inc`.
- **A HUD clock drawn in the field** (farm owner). The option exists.
- **Bike auto and bout speed** only store the option. Traversal and bouts
  read `opt.bike_auto` and `opt.battle_speed`.
- **Shelf icons:** 32x32 kin icons in 24 px rows overlap a little for tall
  art.
- **Crests on the Hall Master banner, and a crest-award animation**
  (traversal / bouts).

## APIs

- `crest_case_open()`
- `quest_log_open()`
- `summary_open_shelf(i)`
- `gems_load()` / `gem_push(x, y, rarity)`
- `item_icon_index(item)`
- `storage_*` (as before)

## Edits outside my files

- `src/game/time.c`: added a placeholder `time_text()`. **It conflicts with
  the farm owner's version: keep theirs.**
- `src/game/modules.c`: one line,
  `case KEY_CREST_CASE: crest_case_open(); return 1;`.
- `tools/test_field.c`: the Shelf block uses pages and the DEPOSIT /
  WITHDRAW menu, instead of `pc.deposit` and SELECT.
- `src/game/script.c` (earlier): the SELECT register line in
  `field_update`.
