# Crafting handoff (CRAFT owner)

Branch: `worktree-agent-a71c27c9df7c2a807`, based on `expansion` @ d918146
(the worktree had to be reset from 89bf1cb first).
`make art && make && make test` is green (the 6 `-Wunused-function`
warnings in party.c are from the base, UI owner's Shelf helpers).

## Done

- **craft.c** (all gameplay):
  - 32 recipes (13 kitchen, 8 cauldron, 11 forge), with ingredients, yield
    and source (start / teacher lesson / book). Four are known from the
    start: BERRY TART, BERRY JUICE, GLOW TONIC, LANTERN.
  - Lessons are gated by things made at that station: chef 0,1,2,4,6,8,11,15;
    brewer 0,1,3,5,8; smith 0,1,2,4,6,8,11.
  - Books: COOKBOOK, BREW NOTES, FORGE MANUAL (IK_FOOD params 20-22,
    POCKET_MATERIALS, sold by the teachers). Reading one teaches its recipes
    and uses it up.
  - The crafting screen (`ext_open`):
    - recipe list with have/need counts (missing in red) and ????? for
      unknown recipes
    - batch picker 1-10
    - a how-to intro (B there costs nothing)
    - the minigame
    - a result, with a big pop-in rating label
  - The minigames:
    - KITCHEN: three pan tosses on a narrowing zone, then D-pad stirring
    - CAULDRON: hold-A heat with inertia against a drifting band, then A
      at the big bubble's peak (an affine sprite that grows)
    - FORGE: marks slide to the anvil line on a beat, then a quench where
      the iron cools from glowing to steel, with steam
  - Scores are 0-100. PERFECT is 90 or more, GREAT 60, OK 25; anything
    lower is BURNT, FIZZLED or CRACKED. A fail costs one batch of
    ingredients.
  - Lanterns and potions: GREAT gives half a batch more, PERFECT a whole
    batch more. Dishes instead keep their quality (`fine[]` and
    `perfect[]` counts per dish, clamped to the bag).
  - The RECIPE BOOK key item opens the screen:
    - facing a station, it opens that station
    - anywhere else, it opens as a read-only book with station tabs
  - Stations: STOVE, BRICK_OVEN, CAMPFIRE and COOKTOP are kitchens.
    CAULDRON brews and ANVIL forges. `station_examine` asks "Cook
    something?". In the asset viewer, examining a station also learns
    every recipe and stocks ingredients (a debug convenience).
- **Meal buffs:** one at a time, and a new one replaces the old. They are
  stored in the save.
  - Buffs that last a number of bouts (by quality):
    - TART: XP +25/35/50%
    - TRUFFLE: XP +50/75/100%
    - STEW: DEF and WILL +1/+1/+2
    - CHILI: ATK and FOCUS +1/+1/+2
    - SKEWER: SPEED +1/+1/+2
    - PIE: catch +3/4/6
    - BUN: heals 10/15/20% after each bout
    - MOONCAKE: `meal_lure_active()` 1-3
  - Eaten at once:
    - SALAD heals the team 50/65/80%
    - JUICE heals 40/50/60 HP
    - APPLE heals 80/100/120 HP
    - NECTAR is a full restore, moves included
    - CANDY gives +1 level and bond, then learns moves and evolves the
      same way as a SUNSEED
- **Items and icons:** there are 3 new items (the books). Every craft item
  now has its own icon, 32 in all (`tools/icons/icons_craft.py`).
- **Decor:** `tools/decor_craft.py` adds COOKTOP, CAULDRON and ANVIL: 2x2,
  animated, interior only. They're registered in
  `gen_field_gfx.all_decor()` and appear in the asset viewer's VIEW
  INTERIOR 2/2.
- **NPCs:** the teachers are SCR_CHEF, SCR_BREWER and SCR_SMITH (in
  world/craft/scripts.c).
  - On first talk they give the RECIPE BOOK (once) and starter
    ingredients.
  - After that their menu is LESSON / COOK|BREW|FORGE (lends the station)
    / BUY (`shop_open_stock`) / CHAT (lore) / BYE.
  - CHEF ROSA is placed in the Maple Village BAKERY at (4,3), next to its
    STOVE and BRICK OVEN.
- **Lore:** there are 7 LCH_CRAFTING entries, from the sources LSRC_CHEF,
  LSRC_BREWER and LSRC_SMITH:
  - the Maillard reaction
  - why meals help
  - honey crystallising into KERNEL CANDY
  - the enzyme temperature optimum
  - bubbles and bottling
  - annealing glass
  - quenching steel
- **Tests:** tools/tests/test_craft.c covers:
  - the data
  - yields and ratings
  - quality tracking
  - every meal buff and food item
  - books and lessons
  - stations, the screen and the RECIPE BOOK
  - each minigame played with keys (perfect and idle runs)
  - the teacher's menu and shop
  - the save round trip and validation
- **Verified in the ROM** (headless shots): the chef's intro and menu, the
  kitchen list, batch picker, intro, tosses, stirring and result. The
  cauldron and forge were checked in the asset viewer.

## Placing the brewer and the smith (left for W-GRIM / W-FAR or the merger)

`MAP_APOTHECARY` and `MAP_FORGE` are still door-less placeholders. The map
test requires every person to be reachable, so the two teachers are
**commented out** in `src/game/world/craft/npcs.inc`. Once the room has
its door:

1. Uncomment the `PERSON(...)` line and set x / y. Leave a free cell in
   front of the teacher.
2. In the region's `data.h` decor list, add `DP(CAULDRON, x, y)` to the
   apothecary or `DP(ANVIL, x, y)` to the forge. They are solid 2x2
   blocks, faced from the cell below.
3. Any interior kitchen (an inn, the FARMHOUSE) can use `DP(COOKTOP, x,
   y)` or the existing STOVE. Every one is a working kitchen.

## Left

- **Traversal:** call `meal_lure_active()` (0 or 1-3) in the rare-kin roll,
  next to LURE INCENSE.
- **UI:** team-wide dishes and the books still go through the bag's "Use it
  on which kin?" picker. They work, but ignore the pick. A hook like
  `craft_food_needs_kin(item)` would skip the picker. Also, `draw_item_icon`
  indexes `item_icon_pal` by item id instead of `ITEMS[item].icon`, which
  is the known out-of-bounds bug. The craft screen uses its own correct
  `craft_draw_icon`.
- **Farm:** most kitchen recipes need farm crops (`ITEM_CROP_*`). Until
  farming lands, only the chef's gift berries and the shops' materials are
  obtainable. MOTE DUST (KERNEL CANDY, RADIANT TONIC, LURE INCENSE) comes
  from fusion misses.
- **Polish:**
  - a stir-speed indicator
  - a hammer-strike shake
  - the art notes from the first pass: kitchen utensils, a rounder
    apothecary cauldron
- **STATION_TUNE** (energy tuning) belongs to the fusion owner.
  `craft_open(STATION_TUNE)` just prints a pointer to the Resonance Works.

## Shared files touched

- `tools/gen_field_gfx.py`: one line in `all_decor()` (`decor_craft`).
- `src/game/debug.c`: one line in `debug_examine`, so stations aren't
  swallowed by the viewer's "DECOR X" text.
- Regenerated: `src/gfx_field.h`, `src/gfx_battle.h`,
  `src/game/world/debug/*`.
