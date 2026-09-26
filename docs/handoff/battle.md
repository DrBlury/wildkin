# Bouts (battle) handoff

Owner files: `src/game/battle.c`, `battle_ui.c`, `anim.c`, `moves.h`,
`tools/gen_battle_gfx.py` (+ `src/gfx_battle.h`), `tools/test_game.c`,
`src/game/items/core.inc`. New helper modules, all read by
`gen_battle_gfx.py`: `tools/bout_fx.py` (particles),
`tools/bout_icons.py` (supply icons), `tools/bout_scenes.py` (backgrounds).

**The build is broken right now.** The work stopped mid-change (see In
progress), so `make` and `make test` fail to compile.

## Done

- **Art** (regenerated into `src/gfx_battle.h`):
  - 16 new 16x16 particles: BONE, SKULL, RIVET, GEAR, COIN, MOTE, BELL,
    CUP, MOON, FLAKE, TRINKET, MAGNET, STREAK, CANDLE, BUG, SCALE.
  - 2 new 32x32 particles: FXB_ANVIL and FXB_CHEST (a mimic jaw; flip it
    for the lower jaw).
  - Thrown-lantern palettes for DUSK, TIDE, HEAVY, QUICK and BONE
    (`capsule_pal[CAPSULE_PAL_COUNT]`, `LK_*` order).
  - `lantern_mini_gfx` is now 2 tiles: lit, and unlit for a dozing kin.
  - 12 supply icons: VIGOR DRAUGHT, CLARITY BREW, REVIVAL BREW,
    SWIFT/FOCUS/WILL COIL, LURE INCENSE, WAYSTONE and the four new shards.
    `core.inc` points at them.
- **moves.h**:
  - All 46 new moves have their own recipe: kind, particles, colours and
    count. The recipes are balanced for looks, and every move's stats and
    effect were checked against docs/EXPANSION.md 5.
  - New effect `EF_FOE_STATS` (mask, stages). SNOWDRIFT uses it to lower
    SPEED and ACCURACY, as the doc says.
  - 16 new animation kind ids: AK_RATTLE, MIST, SHROUD, TOLL, CHOIR, CHOMP,
    WHIRL, MAGNET, GEARS, ANVIL, MOONLIT, MUON, METEOR, NOVA, ARC, DANCE.
- **battle.c (rules)**:
  - 16 BSCENE ids.
  - `TrainerTeam` holds 6 kin (`TEAM_MAX 6`, checked against
    `TRAINER_TEAM_MAX`) and has `flags` (`TT_MASTER`).
  - Poison can't touch HOLLOW or METAL kin.
  - `EF_FOE_STATS` works in moves and in the AI.
  - AI: moves are scored with stat stages, and a sure KO scores double.
  - Wardens switch out an outmatched kin, at most 2 times per bout (3 for
    masters), and send in their best-matched kin after a KO.
  - When both kin doze off at once, your forced switch now happens too.
  - Music cue hook `battle_music_hook` with `BCUE_*` events, queued as
    `EV_CUE`.
  - Hall Master win: plays `SFX_VICTORY` and cues `BCUE_MASTER_WIN`.
  - Meal hooks: `apply_meal_stages()` runs on every send-out, XP is scaled
    by `meal_xp_percent()`, and lanterns add `meal_catch_bonus()`.
  - Lanterns:
    - `lantern_finesse()`: DUSK x2 at night, in `MF_DARK` maps, CAVE or
      CRYPT; TIDE x2 on TIDE foes or on water (`battle.on_water`,
      `travel.surfing` or the SEA scene); BONE x2 on HOLLOW foes; QUICK
      x2.5 on turn 1; HEAVY x2 at 1000 hg and x2.5 at 2000 hg (size-scaled).
    - L quick-throw picks the best lantern for the situation.
    - FUSION kin refuse lanterns without using one up.
    - Warden kin: "X is bonded to WARDEN Y. It can't be befriended!"
  - Items: IK_HEAL_CURE, IK_TEA_ALL and IK_REVIVE work in bouts; a coil at
    +6 is refused.
  - Run odds fixed: the old `% 256` wrap made escaping harder after 5
    tries. `battle_run_chance()` gives the odds.
- **battle_ui.c (partly)**:
  - The move tab knows `EF_FOE_STATS`.
  - The RUN option shows the escape odds in wild bouts.
  - Text holds are halved with `opt.battle_speed`.
  - Written: the Hall Master banner (WIN0 wipe, `banner_begin`,
    `banner_update`, `banner_draw`) and the warden team row
    (`team_row_draw`, `disp_foe_idx`).
  - `EV_BANNER`, `EV_LEGEND` and `EV_CUE` are handled in `bev_run`.

## In progress (unfinished; why it doesn't compile)

- **sfx.c** (allowed: new ids and definitions only). Add `SFX_HOLLOW`,
  `SFX_RELIC`, `SFX_METAL`, `SFX_ASTRAL`, `SFX_KNELL`, `SFX_BANNER` and
  `SFX_VICTORY` (a priority-5 fanfare), then point `TYPE_SFX` in `anim.c`
  at the four type sounds.
- **anim.c**:
  - Write `anim_start_legend(side)`, an ANIM_LEGEND mode: rear up,
    FXB_RING shockwaves, heavy shake, a flash of the type tint, SFX_ROAR.
  - Implement the 16 new AK_* kinds in `anim_move_frame` and
    `anim_duration`. Until then they fall to the default 34 frames and
    draw nothing.
  - Add the per-move touches planned in the comments of `moves.h`, e.g.
    candles in AK_HEAL for LAST RITES, a coin in AK_BEAM for GILDED GLEAM,
    and a magnet palette cycle for LODE BEAM.
  - Add an `anim_nodraw` flag checked in `fx_spr*` and `big_spr`, so
    battle_speed can step `anim_update()` twice per frame.
  - Tune TYPE_TINT for the 4 new types.
- **battle_ui.c**:
  - `copy32(... lantern_mini_gfx, 8)` must become 16 words, in two places.
  - Call `team_row_draw()` and `banner_draw()` from `battle_draw`.
  - In `battle_draw_lines`, fill `line_win` from `banner_l`/`banner_r` for
    lines `BANNER_Y0..BANNER_Y1` (full width elsewhere) while
    `banner_on`, and set `oam_line_win0h`.
  - `battle_reset`: reset `master`, `legend`, `foe_entered`,
    `foe_switches` and `disp_foe_idx`. Don't touch `on_water`; clear it in
    `battle_exit`.
  - `battle_start_wild`: if `rarity == R_LEGEND`, set `legend` and
    `no_run`.
  - Write `battle_start_legend(Monster, scene)` and
    `battle_start_master(t)`.
  - `battle_start_trainer_team`: copy up to 6 kin and read `flags`. The
    title is "HALL MASTER <name>" when the name has no space.
  - `battle_queue_intro`:
    - legend: send out, then `EV_LEGEND`, then "The legendary X rises
      before you!"
    - master: an `EV_BANNER` carrying `foe_title`.
    - both: call `apply_meal_stages()` after the ally is sent out.
  - Start cues (`battle_cue(BCUE_START_*)`) in the start functions.
    `battle_exit` should call `meal_bout_finished()` and
    `battle_cue(BCUE_END)`.
  - battle_speed: in `battle_events_update`, run a timed non-text,
    non-LEARN event twice per frame. Run `intro_update` twice. In
    `battle_draw`, call `anim_update` twice (the first with nodraw).
- **Scenes**: `tools/bout_scenes.py` came from a helper agent that was
  stopped part-way. At commit time CITY and COAST are painted, so the
  header has 7 scenes. SEA, SNOW, CAVE, GRIM, CRYPT, VOLCANO, DREAM, FARM
  and LAIR are still to do. Only the scenes it returns are in the header, and
  `battle_load_scene` clamps to `BBG_SCENE_COUNT - 1`. Once all 11 exist,
  add `typedef char X[BSCENE_COUNT == BBG_SCENE_COUNT ? 1 : -1];` in
  `battle.c`.
- **script.c** (allowed small edits):
  - `set_battle_scene`: map `SC_CITY..SC_LAIR` onto `BSCENE_CITY..LAIR`.
    The order matches, so `battle_next_scene = sc < BSCENE_COUNT ? sc : 0`
    works.
  - `team_from()` copies only 3 kin. Loop to `TRAINER_TEAM_MAX` and set
    `flags = 0`.

## Not started

- `tools/tests/test_battle.c`:
  - new moves resolve with the right effects
  - the 18x18 chart equals the block in docs/EXPANSION.md (parse it at run
    time)
  - every scene loads
  - a 6-kin warden bout plays through
  - legend: no running, and the catch path works
  - the new items, lantern bonuses and meal hooks
  - battle_speed gives fewer frames per bout
- `tools/test_game.c`:
  - Update the TrainerTeam initialiser (it still compiles; the arrays are
    zero-filled).
  - Extend the balance simulation to the whole roster, tiered by stage
    and rarity, with sampled pairings to keep it fast.
  - Make "every move has its own animation recipe" stricter (the tuple
    anim+fx+fx2 unique among the new moves).
- Visual checks with `build/shot`.

## APIs other owners should call

- **Region scripts**:
  - Hall Master:
    `static TrainerTeam t; t = team_from(&TRAINERS[TR_X], BSCENE_CITY); t.flags |= TT_MASTER; battle_start_trainer_team(&t);`
    `battle_start_master(&t)` is planned for the same thing.
  - Legend:
    `battle_next_scene = BSCENE_LAIR; battle_start_wild(monster_make(SP_X, lv));`
    An R_LEGEND kin gets no_run and the legend intro by itself.
    `battle_start_legend(m, BSCENE_LAIR)` is planned.
  - `battle_end_hook` receives the `BR_*` result.
- **Traversal**: set `battle.on_water = 1` for bouts on water, or rely on
  `travel.surfing`.
- **Music**: set `battle_music_hook = fn(int cue)` for `BCUE_START_*`,
  `WIN`, `MASTER_WIN`, `CAUGHT`, `LOSE`, `RUN` and `END`.
- **UI (menu.c)**: `item_battle_usable()` must also accept `IK_HEAL_CURE`,
  `IK_TEA_ALL` and `IK_REVIVE`, or call `battle_item_kind_usable(kind)` in
  `battle.c`. `party.c` `item_use_field` has no field use for those 3
  kinds either.
- **Craft**: the `meal_*` functions are declared in `battle.c` with the
  exact stub signatures from `craft.c`.

## Notes

- Build and test status: they don't compile, because of the In progress
  items above. Before this work, `make test` (test_game) passed. No
  balance run was done on the expansion roster, and the kin data in this
  worktree is still placeholder.
- Edits outside my files: none yet. The script.c changes above are
  needed. sfx.c needs only new ids.
- Pitfalls:
  - Battle OBJ tiles now reach about 746 (OT_FX 400 + 70 particles x 4 +
    4 big x 16 + 2). Keep them under 768, where the field's overworld kin
    tiles start.
  - `battle.team_idx` is overwritten when EV_SEND_OUT plays (existing
    design). `disp_foe_idx` follows what the screen shows.
  - `gen_battle_gfx.py` rewrites `src/gfx_battle.h`, so preview helper
    modules by importing them rather than running the generator.
