# Bouts (battle) handoff

Owner files: `src/game/battle.c`, `battle_ui.c`, `anim.c`, `moves.h`,
`tools/gen_battle_gfx.py` (+ `src/gfx_battle.h`), `tools/test_game.c`,
`tools/tests/test_battle.c`, `src/game/items/core.inc`. Helper modules read
by `gen_battle_gfx.py`: `tools/bout_fx.py` (particles), `tools/bout_icons.py`
(supply icons), `tools/bout_scenes.py` (backgrounds).

`make art && make && make test` is green. The only compiler warnings are
the unused `storage_*` functions in party.c, which is not a bouts file.

## Done

- **Rules (battle.c)**:
  - 16 BSCENE ids. Each one has a painted background, and battle.c checks
    `BSCENE_COUNT == BBG_SCENE_COUNT` at compile time.
  - 6-kin warden teams (`TT_MASTER`).
  - Poison can't touch HOLLOW or METAL kin.
  - `EF_FOE_STATS`.
  - AI: moves are scored with stat stages, a sure KO scores double, and
    wardens switch out an outmatched kin.
  - Music cues (`BCUE_*`).
  - Meal hooks.
  - Lantern bonuses (`lantern_finesse`).
  - New items.
  - Fixed run odds.
  - Legends: `battle_start_legend`, `no_run` and the rear-up intro.
  - Hall Masters: `battle_start_master`, a banner and the team row.
- **Art**:
  - New particles: 16 small plus FXB_ANVIL and FXB_CHEST.
  - Lantern palettes.
  - Supply icons.
  - 11 new battle backgrounds in `tools/bout_scenes.py`: CITY, COAST, SEA,
    SNOW, CAVE, GRIM, CRYPT, VOLCANO, DREAM, FARM and LAIR, at 167 to 381
    tiles each. The budget is 500, asserted in gen_battle_gfx.py.
- **Animations (anim.c)**:
  - All 16 expansion kinds are implemented, with durations:
    - AK_RATTLE: bones jitter round the foe, then clatter in.
    - AK_MIST: a ground fog rolls over and rises.
    - AK_SHROUD: mist spirals up the user.
    - AK_TOLL: a swinging bell; each toll sends a ring and plays
      SFX_KNELL.
    - AK_CHOIR: skull spirits rise, sing notes, then converge.
    - AK_CHOMP: the FXB_CHEST jaws, with the lower jaw flipped; coins fly.
    - AK_WHIRL: a rising tornado of cups and trinkets, or of flames.
    - AK_MAGNET: a magnet with field rings; flakes fly to it and the foe is
      pulled.
    - AK_GEARS: counter-rotating gears grind, with sparks.
    - AK_ANVIL: a shadow ring, then FXB_ANVIL drops: squash, dust, stars.
    - AK_MOONLIT: night falls, the moon rises, a shaft of light, then a
      drain.
    - AK_MUON: streaks rain through everything.
    - AK_METEOR: a big meteor, a flash, a crater and debris.
    - AK_NOVA: a charge-up, darkness, then a blinding burst.
    - AK_ARC: jagged sparks from the user to the foe.
    - AK_DANCE: the user sways, turns (mirrored scale) and scales spiral.
  - Per-move touches:
    - LAST RITES: a candle ring.
    - GILDED GLEAM: a flipping coin and a flash.
    - LODE BEAM: red and blue pole cycling.
    - TRINKET TOSS: spinning trinkets.
    - RIVET SHOT: a hot rivet trail.
    - TWINKLE: curls in, with a sparkle trail.
    - ACID SPIT: a sizzle.
    - OSSIFY: cracks and bone debris.
    - CURSED CURIO: a trinket lure and eyes.
    - COMET DASH: a comet head.
    - RIPTIDE: waves.
    - SWARM RUSH: a riding swarm.
    - STEEL SHELL: flakes.
    - THORN WALL: a hedge.
    - SNOWDRIFT: a snow pile.
    - SNARL: eyes.
    - SANDBLAST: grit.
    - SHADE CUT: darkness and a wisp.
    - LULLABY: Zzz.
    - COUNTERJAB: a fist.
    - IRON TAP: a ring.
    - MARROW SIP: a skull.
    - FORGE FLASH: a flash.
  - TYPE_TINT tuned for the four new types: HOLLOW grave-moss, RELIC gilt,
    METAL steel, ASTRAL night.
  - `anim_nodraw`: `fx_spr*` and `big_spr` push nothing, and the
    shake/`anim_frame` only advances on shown steps.
- **Battle speed (battle_ui.c)**:
  - With `opt.battle_speed`, `battle_draw` runs a hidden `anim_update()`
    step, then the shown one.
  - A started timed event runs twice per frame. That covers everything
    except EV_TEXT and EV_LEARN.
  - `intro_update` runs twice.
  - A turn takes about 70% of the frames, and less when you skip text.
    Every impact still fires.
- **Tests**:
  - `tools/tests/test_battle.c`:
    - The new moves match the doc table (parsed at run time).
    - The 18x18 chart equals the doc block.
    - Every new move's recipe is unique.
    - Every new effect resolves: stat moves, drain, recoil, 2-5 hits,
      CURSED CURIO doubling, priority, and chance rates over 400 trials.
    - The poison immunity.
    - Every AK kind is used, finishes, draws and lands its impact.
    - The legend intro.
    - A hidden step draws nothing.
    - Every scene loads.
    - Speed mode is faster and keeps every DEATH KNELL toll.
  - `tools/test_game.c`: a whole-roster balance round robin, tiered by
    stage and rarity:
    - basic (Lv15), final, rare and fusion (Lv50), each within 20..85%.
    - Every legend beats final forms at least 55% of the time.
    - It runs in under 1 s.
- **Balance tuning** (kin data, see below):
  - Learnset reorders so kin don't carry 2 debuffs or lack a STAB attack
    at the tested levels: SNUFFLET, STATICKO, TUXFLAKE, CALCIPUP, HOARDMAW,
    WENDIGAUNT, QILUMEN, GRIFFALON, FAEFLY, KITSUFLAME, PHOENEX, SYLVARCH.
  - Small base-stat nudges:
    - PHOENEX: FOCUS 130→112, WILL 90→88, SPEED 115→100.
    - SYLVARCH: ATK 115→122, WILL 110→100, SPEED 75→92.
    - MAGNITICK: ATK 58→54, DEF 78→70.
    - CALCIPUP: HP 50→56, ATK 55→64.
- **Checked in the real ROM** with build/shot and scratch demo ROMs (see
  Notes): every new scene, and every new animation kind plus most touches.

## Left

- The team row and banner were wired by the coordinator. A shot of a real
  Hall Master bout (with its region script) is still worth taking.
- The note's other test ideas are not written yet: a full 6-kin warden bout
  played through, the legend catch path, and lantern/meal hooks in
  test_battle.c.
- AI: debuffs score a flat 35..55 however strong the kin's attacks are. I
  tried capping them at 3/4 of the best attack; it barely changed the
  results, so I reverted it.
- The balance bands (20..85%) are wide on purpose: type matchups swing
  single kin a lot (for example, CALCIPUP goes 0% into BLAZE or RELIC and
  100% into BLOOM).

## Shared files edited (not bouts-owned)

- `tools/kin/normal_a.py`, `normal_b.py`, `rare.py`, `fusion_a.py`,
  `fusion_b.py`, `legend.py`: learnset order and a few base stats, for
  balance only (listed above). No art or other fields changed.
  `src/species_data.h` was regenerated.

## APIs other owners should call

- **Region scripts**:
  - Hall Master: `battle_start_master(&t)`, or set
    `t.flags |= TT_MASTER` and call `battle_start_trainer_team(&t)`.
  - Legend: `battle_start_legend(m, BSCENE_LAIR)`. A wild kin with
    `R_LEGEND` gets the same treatment by itself.
  - `battle_end_hook` receives the `BR_*` result.
- **Traversal**: set `battle.on_water = 1` for bouts on water, or rely on
  `travel.surfing`.
- **Music**: set `battle_music_hook` for the `BCUE_*` cues.
- **UI (menu.c)**: `item_battle_usable()` should accept `IK_HEAL_CURE`,
  `IK_TEA_ALL` and `IK_REVIVE`, or call `battle_item_kind_usable()`.

## Notes

- Battle OBJ tiles end at 746 (OT_FX 400 + 70x4 + 4x16 + 2), under the 768
  where the field's kin tiles start. No particles were added in this pass.
- BG scene tiles: at most 381 of the 500 allowed (charblock 0).
- `gen_battle_gfx.py` rewrites `src/gfx_battle.h`. To preview a helper
  module, import it instead of running the generator.
- Visual check recipe (scratch, not committed): `build/animdev/demo.c`
  builds a ROM that boots straight into a wild bout, with a scene, 4 ally
  moves and a battle-speed setting from -D flags. `build/animdev/demo.py`
  builds it, drives build/shot and writes contact sheets to
  `build/animdev/out/`.
