# Crafting handoff (CRAFT owner)

Branch base: `expansion` @ 6118872 (this worktree had to be fast-forwarded
from 89bf1cb first).

## Done

- `tools/gen_craft_gfx.py` -> `src/gfx_craft.h` (generated, deterministic,
  stdlib only; `--preview DIR` writes PNGs):
  - Three 240x160 BG0 backdrops for the minigames: KITCHEN (203 tiles,
    5 banks), APOTHECARY (463 tiles, 6 banks), FORGE (387 tiles, 4 banks).
    `craft_backdrops[CBG_*]` = { tiles, tile_count, map[20*32], pal[6][16] }.
    Load like `battle_load_scene` (charblock 0, SB 24, BG banks 0-5).
  - OBJ sprites in `craft_sprites[CSP_*]` ({first tile, tiles per frame,
    frames, w, h}) over `craft_sprite_gfx`: PAN (64x32, two 32x32 halves),
    FOOD (32x16 x2), CHUNK (8x8 x4), SPOON (16x32), POINTER (16x16), LIQUID
    (64x32), BUBBLE (32x32: bubble, pop), HAMMER (32x32 x3: raised, mid,
    strike; grip fixed at 26,24), INGOT (32x16 x3 shapes), MARK (16x16),
    labels LBL_PERFECT/GREAT/GOOD/OK/MISS/BURNT/FIZZLED/CRACKED (64 or
    32 x 16).
  - Palettes: PAN, SPOON, POINTER, HAMMER use `cpal_metal`; everything else
    uses the bout effects' value ramp (anim.c `build_fx_palette(bank, main,
    sec)`), so food, brew, glowing iron and labels are tinted at run time.
  - Backdrop packer: grows one palette bank at a time around the largest
    colour sets (6 banks max, asserts the packing decodes back exactly).

## In progress

Nothing is wired into the game yet: `src/gfx_craft.h` is not included by
`src/main.c`, and the Makefile / CI do not know about it. To finish:

1. `#include "gfx_craft.h"` in src/main.c after gfx_battle.h; add it to
   Makefile `ART` and `art:` (`python3 tools/gen_craft_gfx.py`) and to the
   CI `git diff --exit-code` list in .github/workflows/build.yml.
2. Art polish seen in previews: kitchen could use hanging utensils; the
   apothecary cauldron belly could be rounder.

## Not started

Everything in `src/game/craft.c` beyond the stub, plus tests, icons, decor,
NPC scripts and lore. The worked-out design, ready to implement:

- **CraftState** (<= 256 B, keep 64): `recipes[16]` bits, `meal` (MEAL id
  + 1, 0 none), `meal_bouts`, `meal_tier` (0 OK, 1 GREAT, 2 PERFECT),
  `flags`, `u16 made[3]` per station (lesson gating), `fine[16]` /
  `perfect[16]` per MEAL = GREAT+/PERFECT dishes in the bag (clamp
  perfect <= fine <= bag[item]), `cursor[3]`, `batch`. Validate clamps
  all of it.
- **MEAL ids** = items/craft.inc params 0-12 (TART, BUN, STEW, CHILI, PIE,
  MOONCAKE, TRUFFLE, SKEWER, SALAD, CANDY, JUICE, APPLE, NECTAR). Buffs
  (bouts OK/GREAT/PERFECT; power): TART XP +25/35/50% (5/7/10), BUN heal
  10/15/20% after each bout (5/7/10), STEW DEF+WILL +1/+1/+2 (3/5/7),
  CHILI ATK+FOCUS same, PIE catch +3/4/6 (x10 units added to the lantern
  param), MOONCAKE lure 1/2/3 (5/7/10), TRUFFLE XP +50/75/100%, SKEWER
  SPEED +1/+1/+2 (3/5/7); SALAD heals team 50/65/80%, CANDY +1 level (+bond
  by tier; mirror party.c IK_SEED: learn_begin + evo_request), JUICE
  40/50/60 HP, APPLE 80/100/120, NECTAR full restore. One buff at a time.
- **Recipes (32)**. COOK: BERRY TART (start), BERRY JUICE (start), HONEY BUN,
  VEGGIE STEW, CAMP SKEWER, CHILI POT, SUN SALAD, APPLE PRESS, MOONCAKE,
  KERNEL CANDY (chef, gated by dishes made: 0,1,2,4,6,8,11,15), PUMPKIN PIE,
  PEACH NECTAR, TRUFFLE RICE (COOKBOOK). BREW: GLOW TONIC (start), HONEY
  DROP, VIGOR DRAUGHT, BRIGHT TONIC, CLARITY BREW, RADIANT TONIC (brewer),
  REVIVAL BREW, LURE INCENSE (BREW NOTES). FORGE: LANTERN (start), PRISM,
  DUSK, TIDE, BONE, HEAVY LANTERN, SPRINKLER, STAR LANTERN (smith), QUICK
  LANTERN, TUNING FORK, HUSH BELL (FORGE MANUAL). Books = 3 new IK_FOOD
  items in POCKET_MATERIALS with params 20-22, consumed when read.
- **Minigames** (score 0-100; >=90 PERFECT, >=60 GREAT, >=25 OK, else
  FAIL; FAIL loses one batch of ingredients only; ingredients are consumed
  at the end, B during the intro cancels). COOK: 3 tosses (needle triangle
  wave, zone narrows 28/22/16 px, PERFECT +-3 px = 25, GOOD = 17) then 180
  frames of stirring (D-pad octants, signed accumulator, 6 turns = 25).
  BREW: 300 frames hold-A heat with inertia vs a sine-moving band (85% in
  band = 70), then A at the big bubble's peak (+-3 = 30, +-8 = 18). FORGE:
  4-6 marks, beat 44/38/32 frames (+-3 = 100/N, +-8 = 60/N, stray press -5),
  then quench (palette cools to steel, steam).
- **Screens** via `ext_open`: station picker (recipe list, ingredients
  have/need in red, LEFT/RIGHT batch 1-10), RECIPE BOOK (tabs per station,
  unknown recipes as ?????, active meal line, A crafts only when facing a
  matching station decor), minigame, result. OBJ tiles 768-1023 and OBJ
  banks 9-14 only (the field re-uploads those every frame); BG banks 0-7 and
  charblock 0 are restored with `field_load_tileset()` (field_return does it)
  -- call it before returning to the bag/START menu after a minigame.
- **Stations**: DK_STOVE, DK_BRICK_OVEN, DK_CAMPFIRE and new DK_COOKTOP ->
  cook; new DK_CAULDRON -> brew; new DK_ANVIL, DK_WORKBENCH -> forge
  (tools/decor_craft.py, sets ('interior',), registered in
  gen_field_gfx.all_decor()). Colour plan: cooktop fits interior bank 5;
  cauldron top quadrants bank 4, bottom bank 5; anvil top bank 7, bottom
  bank 4.
- **NPCs**: scr_chef / scr_brewer / scr_smith menus LESSON / COOK (lend the
  station) / BUY (`shop_open_stock` of their materials and book) / CHAT
  (lore) / BYE; first talk gives the RECIPE BOOK and a few ingredients.
- **Lore** (LCH_CRAFTING, LSRC_CHEF/BREWER/SMITH): luciferin enzyme
  temperature optimum, annealing heartglass, why meals help kernels pump,
  the Maillard reaction, glow-bee honey crystallising into KERNEL CANDY.
- **Icons** (tools/icons/icons_craft.py): 5 lanterns via
  `g.render_lantern` + new role palettes, 13 foods, 11 materials, 3 books.

## APIs other owners should call

Keep these exact signatures (battle.c and travel.c are compiled before
craft.c and must forward-declare them):

- `static int meal_stat_stage(int stat);` extra starting stages (STAT_*).
- `static int meal_xp_percent(void);` 100 = no bonus.
- `static int meal_catch_bonus(void);` added to the lantern param (x10).
- `static void meal_bout_finished(void);` once per finished bout.
- `static int meal_lure_active(void);` (new, planned) 0 or strength 1-3.
- `static int station_examine(int decor_kind);`, `static void
  craft_open(int station);`, `static int craft_use_food(int item, int
  slot);`, `static int craft_key_use(int key);` unchanged.

Currently all of these are still the base stubs.

## Notes

- Build and tests: unchanged from the base (nothing includes the new
  header yet); `make` built fine here before any change (about 50 s).
- No edits outside my files.
- Pitfalls: the bag sends IK_KEY and IK_FOOD items through the kin picker;
  a UI hook like `craft_food_needs_kin(item)` would let team-wide meals and
  books skip it. OBJ banks 0 and 8/15 are only loaded at game init, so
  never clobber them in a screen.
