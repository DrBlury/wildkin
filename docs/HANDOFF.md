# WILDKIN expansion: handoff

> **Current follow-up (2026-09-27; supersedes the long-route gap list below):**
> Named route wardens now enter actual four-active 2v2 battles when both NPCs
> and two healthy allied kin are available; a solo bout remains the fallback.
> The Oak/Ash encounter was captured from the production ROM with four separate
> kin and HP panels after a stack-overflow fix in the battle-intro wipe.
> Bramblewood ↔ Brookmill Trail now streams aligned, compatible horizontal
> borders without a fade. Incompatible palettes/tilesets, offset or elevated
> borders still use the short safe fade; seamless crossing is not universal.
> Regional weather and festival effects, direct A-to-examine FIELD NOTES,
> animated tram/lift/punt scenes, the wagon arrival, and five authentic
> route/event GIFs are integrated. The event animation is transient and does
> not change save IDs. ROM-backed Act II currently reaches Lumen in 2,971
> frames; full act timing, Act III victory, and human Acts II/III playtests are
> still unverified. The 16–18-hour target must not be inferred from partial
> scripted segments. See [doubles](handoff/double_bouts.md),
> [playtime](handoff/playtime.md) and the [route media](../README.md).
>
> **Long-route checkpoint (2026-09-27; historical, superseded above):**
> The engine save layout and v5→v7 migrations, seven-act gated route graph,
> new hamlets and loop maps, daily events, cross-region projects/quests, Sorrel
> and Stillwarden route bouts, FIELD NOTES quest page and town-map markers are
> integrated on `expansion`. `make art && make && make test` passes with no
> compiler warnings. The bounded puzzle search covers 157 map/ability cases;
> the progression suite checks physical G1–G6 gates, Hall solutions, the
> postgame Sky Isle flag, entry-component Hearth returns and level ranges.
> XP from lower-level opponents now scales per recipient by `3/(3+level gap)`
> (minimum one XP); the production award and direct-path balance simulation
> share that rule, and all seven Hall arrival assertions pass. The stitched
> world image covers 39 authored outdoor maps, including warp-only areas.
>
> **Still not complete against every plan detail:** the one-map renderer uses
> short palette-safe fades, not seamless two-map crossings; paired wardens
> fight separate 1v1 bouts because a real four-battler combat/UI redesign is
> required ([doubles handoff](handoff/double_bouts.md)). Special weather and
> festival art, some still-only project vehicles, direct tile-examination
> FIELD NOTES triggers, and four requested event/project clips are missing.
> [ROM-backed playtime probes](handoff/playtime.md) stop at specific blockers;
> no complete act or 16–18-hour human playthrough has been measured, and
> human Acts II/III playtests remain open. Older branch handoffs below record
> their earlier isolated status, not the current integrated result. No remote
> release, push or tag was requested or performed.

> **Wave 2–4 integration (2026-09-27):** Links `330a69d`, Events
> `2f11c89`, Saga `50fd42e` and QA `c732942` are merged, after wave-one
> Story. The route registration lists share the same saved-ID order, and
> `tools/gen_save_layout.py --accept-growth` approved the combined manifest.
> Reciprocal Scorchwaste/Aurora/Greywater edges and crest-checked cave guides
> are wired. `make art`, the ROM build and 30 of 31 non-puzzle host suites pass;
> the QA act diagnostic still fails all seven ±2 Master arrival assertions
> (+3, +5, +7, +10, +18, +21, +23). It assumes all mapped wardens and
> satchels, so these are **not** measured critical-path levels. The full
> puzzle solver is separately owned and currently bounded; do not claim
> soft-lock proof. Event daily rolls persist in the v7 event module; an
> authenticated v6 fixture migrates and v5/v4 tests pass. Known remaining
> acceptance gaps include the cell-level progression/return solver, event
> rematch teams and festival rewards, visual project construction, loop-route
> slide/double-bout mechanics, act playthrough timings and human playtests.
> See [wave one](handoff/wave1_integration.md), [Links](handoff/links_routes.md),
> [Events](handoff/events_routes.md), [Saga](handoff/saga_routes.md), and the
> [QA contract](plans/12_balance_integration_qa.md).

> **ADMIN mode (2026-09-27):** in the title's debug menu (SELECT+START), the
> ADMIN MODE row adds an ADMIN entry to the START menu. It can add coins, give
> any item, add any kin with any moveset, teach any move and heal the team.
> See `docs/handoff/admin.md`.

> **Update (2026-09-27): ground blends and a bigger scene.** Any ground laid on another
> (sand on grass, mud on ash...) can fade into it instead of changing at a hard 16px edge:
> call `gf.add_blend(ts, out, inner_terrains, inner_img, outer_img, outer_terrains)` in a tileset
> builder (see ts_grim.py, ts_farm.py); field.c `blend_quads` autotiles it per 8x8 quadrant and
> draws edges only against the listed outer terrains (never water, paths or buildings). The VRAM
> layout changed (gba.h): the scene now has **768 tiles** (`SCENE_TILE_MAX`, tileset + decor), the
> UI canvas moved to 0x6000 (`UI_TILE_BASE`), screenblocks are 28-31. The map budget tests now
> count decor kinds that do not fit (field.c used to drop them silently: PORT BRINE needed 598).

> **Earlier puzzle checkpoint:** `tools/tests/test_puzzles.c` is the
> real-movement solver; the current expanded map set is not yet green under
> its bounded search. See the wave 2–4 status above and `docs/handoff/puzzles.md`.

> **Update (2026-09-26, later):** every area is now implemented and merged
> into `expansion`: the 16 first-round branches plus a second round of 11
> agents (traversal, farm + time, crafting, fusion, UI, bouts, and the east,
> west, north, grim and far regions). `make art && make && make test` is
> green (14 suites) with zero warnings. Each area's current done/left list
> is in `docs/handoff/<area>.md`; sections 2-7 below describe the earlier
> state. Still open: the README and
> media, the music hooks, cross-region balance and story pacing, and the
> small per-area leftovers (e.g. the Clockwork Spire's town-map spot, the
> brewer/smith rooms, per-region berry patches, the Lorebook PLACES limit).

Where the big expansion (docs/EXPANSION.md) stands, how the work is organised,
and exactly how to continue.

## 1. State in one paragraph

The **foundation is done and green** on branch `expansion`. It covers:

- a table-driven tileset registry (12 tilesets), with trees drawn as overlays
  on real ground (the original "trees have a background" bug is fixed)
- an art lint that fails the build on baked-in ground
- the generated asset viewer, kin viewer and warp menu (title screen: tap
  SELECT+START)
- the 174-kin roster pipeline (tools/kin → src/species_data.h +
  src/gfx_monsters.h)
- 18 types, 130 moves and 100 items in 7 pockets
- save v4 (16 KB slots, a 240-slot Shelf, migration from v3/v2/v1)
- placeholder maps for every planned region, with the edge contracts
- stub modules with documented APIs for every system
- a shared test harness

**Sixteen agents then worked in parallel git worktrees and were stopped
early to hand off.** Each committed a WIP commit and a
`docs/handoff/<area>.md` on its own branch. None of those branches is
merged into `expansion` yet.

## 2. Branches

Base: `expansion`. Agent branches: `worktree-agent-<id>`, checked out under
`.claude/worktrees/agent-<id>/`. See section 7 for what each one contains.

| area | branch suffix | handoff note | owns |
| --- | --- | --- | --- |
| kin 32-66 | ad6cd84b107afe4a0 | docs/handoff/kin_a.md | tools/kin/normal_a.py, art_normal_a.py |
| kin 67-100 | a6290e35d2b8957b8 | docs/handoff/kin_b.md | tools/kin/normal_b.py, art_normal_b.py |
| rare 101-120 + legends 121-129 | ad8fec484c53eef39 | docs/handoff/kin_rare_legend.md | tools/kin/rare.py, legend.py (+ art files) |
| fusion 130-151 | a267b6ca422c2033a | docs/handoff/kin_fusion_a.md | tools/kin/fusion_a.py (+ art) |
| fusion 152-173 | aeb73654872577bd5 | docs/handoff/kin_fusion_b.md | tools/kin/fusion_b.py (+ art) |
| traversal | ab9ced5310f9ef4aa | docs/handoff/travel.md | field.c, travel.c, world/travel, gen_travel_gfx.py |
| farming + time | a7756de7a75df0a7c | docs/handoff/farm.md | time.c, farm.c, world/farm, ts_farm.py, decor_farm.py |
| crafting | aa7dc17c0638b679b | docs/handoff/craft.md | craft.c, world/craft, items/craft.inc, decor_craft.py |
| energy + fusion | a49ec0b52b45f77d6 | docs/handoff/fusion.md | fusion.c, world/fusion, gen_fusion_gfx.py |
| bouts | ae3b935e2cf9f5727 | docs/handoff/battle.md | battle*.c, anim.c, moves.h, gen_battle_gfx.py, test_game.c |
| UI + QoL | a090f272da7c691e4 | docs/handoff/ui.md | menu.c, dex.c, lorebook.c, party.c, quest.c, gfx.c, gen_ui_gfx.py |
| region east | a71bab12b1c7f65e6 | docs/handoff/east.md | world/east, ts_city.py, decor_east.py |
| region west | abed7b02f39b9815e | docs/handoff/west.md | world/west, ts_coast.py, decor_west.py |
| region north | aaa383667c2954281 | docs/handoff/north.md | world/north, ts_snow.py, ts_cave.py, decor_north.py |
| region grim + story | a45063c9f22065202 | docs/handoff/grim.md | world/grim, ts_grim.py, ts_crypt.py, decor_grim.py, keeper_after |
| region far | a37d16aecebcea49b | docs/handoff/far.md | world/far, ts_volcanic.py, ts_dream.py, decor_far.py |

To see a branch's work: `git log expansion..worktree-agent-<id>` and
`cat .claude/worktrees/agent-<id>/docs/handoff/*.md`.

## 3. How to continue

1. **Finish or merge each area.** Either resume the area (in a new session,
   give an agent the same brief plus its handoff note, working in that
   worktree), or merge what exists.
2. **Merge order:** kin first, then systems (battle, UI, traversal, farm,
   craft, fusion), then regions. For each branch:
   `git merge --no-ff worktree-agent-<id>`.
3. **Expected conflicts** are only in shared registration lines and
   generated files:
   - `gen_field_gfx.all_decor()` (each region adds a decor module)
   - `Makefile` ART/art (new generators: gen_travel_gfx, gen_craft_gfx,
     gen_fusion_gfx)
   - `src/main.c` (new `gfx_*.h` includes)
   - `.github/workflows/build.yml` (the diff list)
   - `src/species_data.h`, `src/gfx_monsters.h`, `src/gfx_field.h`,
     `src/game/world/debug/*`

   Resolve the generated files by regenerating, never by hand: run
   `make art` after merging, then `make` and `make test`.
4. **Integration work known to be needed:**
   - **Reachability test vs. puzzles.** Once traversal's `travel_attr()`
     makes boulders, gates and barriers solid, the core reachability test
     (tools/test_field.c) must flood in a "puzzles solved" mode (treat
     GATE/BARRIER as open, allow pads). Otherwise Hall Masters behind gates
     will fail it.
   - **Crafting stations.** Place station decor (CAULDRON / ANVIL / COOKTOP
     from decor_craft.py) in the region interiors that host SCR_BREWER,
     SCR_SMITH and SCR_CHEF.
   - **Fusion machines.** Place the fusion machines decor (decor_fusion.py)
     in LUMEN's RESONANCE WORKS next to SCR_FUSION_DESK.
   - **START menu vs. modules.** Check that the UI's START entries (MAP,
     FIELD, QUESTS, clock) match the traversal/time APIs (`worldmap_open`,
     `travel_field_menu_open`, `time_text`).
   - **Balance.** The balance sim (tools/test_game.c) against the finished
     roster.
   - **MF_ASH after the finale.** Tie MF_ASH effects to `grim_healed()`
     once the Hollowing finale is done.
   - **Music.** Another session owns src/game/music.c, src/music_data.h,
     tools/music*, tools/gen_music.py, tools/render_music.c and
     tools/record_audio.c. These are untracked here and must never be
     clobbered. When it resumes, it adds:
     - `#include "game/music.c"` after sfx.c in main.c, and
       `#include "game/music_map.c"` after script.c;
     - `music_init()` / `music_host_frame()` calls;
     - the option rows.

     Its gfx.c DMA fix (DMA1 is reserved for the sound FIFO) is already
     applied. Its sfx.c changes (snd_power_on, SNDCNT_H_MIX 0x0302) must be
     kept.
5. **Finish:**
   - rewrite the README for the expansion
   - re-record media (`python3 tools/make_media.py`; extend the clips to the
     new areas and systems)
   - merge `expansion` into `main`, push, and tag a release (CI builds the
     ROM on `v*` tags)

## 4. Conventions every contributor follows

- **Contract:** docs/EXPANSION.md (names, ids, types, roster, world graph,
  attributes, map flags, MapObj kinds, OBJ VRAM ranges, save layout).
- **World data** lives in `src/game/world/<region>/`, one file per registry.
  The central world.h includes `all_*.inc`; don't edit those files.
- **Items** live in `src/game/items/<owner>.inc` (ITEM_DEF). Save files store
  bag entries by a hash of the item name, so ids may move but renames lose
  the item.
- **Kin** live in `tools/kin/<batch>.py` (KinSpec); every kin has real art. Check sprites with
  `python3 tools/check_kin_clip.py [ids]` (nothing may touch a frame edge). Overworld size
  follows rank (gen_monsters OW_SIZE: first ~15 px tall up to legends ~26-29, the player is 24);
  down/up widths are capped so a kin fits a one-tile corridor, flyers get extra wing room. Regenerate with
  `python3 tools/gen_species.py && python3 tools/gen_monsters.py`.
- **Tilesets** live in `tools/tilesets/ts_<name>.py`, **decor** in
  `tools/decor_<owner>.py`, and **icons** in `tools/icons/icons_<owner>.py`.
- **Tests:** every owner adds `tools/tests/test_<owner>.c` using
  `tools/tests/harness.h`; `make test` runs them all.
- **Cross-module calls** go through the stub APIs in the module files
  (travel.c, farm.c, craft.c, fusion.c, quest.c, time.c, modules.c).
- **Debugging:**
  - Title screen: tap SELECT+START for the DEBUG menu (ASSET VIEWER, KIN
    VIEWER, WARP).
  - Headless screenshots: `make shot`, then
    `build/shot game.gba script.txt [save.sav]`.
  - Map renders: `python3 tools/render_maps.py build/maps`.

## 5. Base state at handoff

- `make` builds a ~2 MB ROM.
- `make test` is green on `expansion`: field, game and core suites.
- Your old v3 save migrates. A backup is at `game.v3-backup.sav`.
- The released game (`main`, tag v1.0.0 on GitHub) is untouched.

## 6. Not started at all

These are not in any agent's scope yet:

- the README rewrite and media for the expansion
- music hooks (the music session)
- final polish passes on story pacing across regions

## 7. Per-area status (from the agents' handoff reports)

**Build status legend:**

- **green:** the branch builds and `make test` passes.
- **gen-fail:** `python3 tools/gen_field_gfx.py` fails on that branch; fix the
  named tile first.
- **not run:** the agent didn't run `make` / `make test` after its last change.

Every branch's worktree was reset or fast-forwarded onto the expansion base
before work started.

### Kin

| area | status | done | left |
| --- | --- | --- | --- |
| kin 32-66 | green | all 35: data + art (art_normal_a.py) | polished in a second pass (SCORCHION/STINGLET redesigned) |
| kin 67-100 | green | all 34: data + art (art_normal_b.py 67-75 + 84-91, art_normal_b2.py 76-83, art_normal_b3.py 92-100) | **Keep** M_ANVIL_DROP / M_LODE_BEAM in these learnsets. second pass: LODEHORN, SCYTHLING, COMBQUEEN, UMBRAKAT, RIVETILLO redesigned |
| rare 101-120 + legends 121-129 | green | all 20 rares: real data + art (rare.py/rare_b.py/rare_c.py + art_rare*.py); legends polished (SCRIPTORA rebuilt, CALDERON reared) | second pass: HOARDMAW, GARGOLITH redesigned; SCRIPTORA, CALDERON rebuilt |
| fusion 130-151 | green | all 22: data + art (138-144 in art_fusion_a.py, 145-151 in art_fusion_a2.py) | second pass: MANTICLAW, RIDDLEON, NOSFERBAT, STARWEAVER redesigned |
| fusion 152-173 | green | all 22: data + art; 160/162 fixed | second pass: TESLAROSE, SNOWBRUTE redesigned. Long side-on kin turn to 3/4 in overworld up/down (gen_monsters OW_TURN / OW_AUTO_TURN) |

### Systems

| area | status | done | left |
| --- | --- | --- | --- |
| bouts | **does not compile** | all 46 move recipes; EF_FOE_STATS (SNOWDRIFT); 6-kin warden teams + TT_MASTER; smarter AI and switching; meal hooks; 5 lantern bonuses; new brews and coils; run odds fix; 16 particles + 2 big ones; CITY/COAST backgrounds | anim.c frame code for 16 new kinds; the legend intro; SFX ids (SFX_BANNER, SFX_VICTORY...); battle_ui wiring; 9 backgrounds; test_battle.c; balance sim over the full roster |
| UI | green | key-item icons, rarity gems, crest art; opt.registered / shelf_box; Shelf boxes in party.c; field use of the new brews; SELECT registered item | every screen (START, bag pockets, Shelf, Almanac filters, quest log, options, Lorebook chapters), test_ui.c. **Known out-of-bounds bug in draw_item_icon** |
| traversal | not run | tools/gen_travel_gfx.py → src/gfx_travel.h (objects, particles, bike, boat, crests, the Vale town map with pixel positions, voyage sea) | all C code (travel.c, field.c, script.c hooks), test maps, test_travel.c; the header is not wired into main.c / Makefile / CI |
| farming + time | green | ts_farm.py (soil, 14 crops, trees, fences, farmhouse) and decor_farm.py (bin, jar, press, drier, sign, board, chest) | all C code (clock, tint, sleep, farming, bin, workers, processors, berries, REEVE), maps, lore, icons, test_farm.c |
| crafting | not run | tools/gen_craft_gfx.py → src/gfx_craft.h (3 minigame backdrops, sprites, rating labels) | craft.c gameplay (32 recipes designed in the note), icons, decor, NPC scripts, lore, tests; header not wired |
| energy + fusion | not run | tools/gen_fusion_gfx.py → src/gfx_fusion.h (18 type glyphs, particles, sine table, 4 machine scenes) | all gameplay (unbind, energy screen, mixing + tuning, Loom), desk script, lore, icons, decor, tests. Designed in the note: the 26-recipe mixing table and the Loom odds (6% + stake 0/6/14 + harmony up to 8 + 3% per miss; guaranteed at 25) |

### Regions

| area | status | done | left |
| --- | --- | --- | --- |
| east | not run | ts_city.py (310 tiles, 11 building stamps); Volt Hall puzzle designed and verified by search (switch a, b, c) | decor_east.py, all maps, NPCs, wardens, scripts, quests, lore, Land Office, the Bramblewood boulders, test_east.c |
| west | **gen-fail** | first draft of ts_coast.py | fix: in the INN stamp, change sign ink `rb_dkr` to `gl_dk`. Then all maps, NPCs, test_west.c. A_CURRENT convention proposed in the note |
| north | not run | ts_snow.py (349 tiles, 150 metatiles); decor_north.py (15 snow decor kinds; cave decor written but not registered); placeholder borders now `P` | ts_cave.py, all maps, NPCs, lairs, quests, test_north.c |
| grim + story | **gen-fail** | grim palettes and helpers (decor_grim.py); draft ts_grim.py | fix the HOUSE stamp palette-bank conflict (or revert ts_grim.build to `return gf.build_wild(name)`). Then maps, the Hollowing story, keeper_after, NPCs, test_grim.c. The designs (Ossuary gate, finale, grim_healed / MF_ASH) are in the note |
| far | **gen-fail** | terrain_far.py (animated lava, hot spring), far_buildings.py, ts_volcanic.py | fix: in terrain_far.rail_img, sleeper ends use `vb_out`; should be `b_out`. Then ts_dream.py, decor_far.py, maps, NPCs, test_far.c. Anvil Hall boulders need arg 1 ("pumice") so they can be pushed before the Anvil crest |

## 8. Known issues on the base (`expansion`) to fix next

- **`tools/render_maps.py` still expects the old three tilesets** (KeyError
  'city'). Port it to `tools/fieldmap.py` + `gen_field_gfx.build_tilesets()`
  and parse `src/game/world/*/data.h` instead of the old maps.h.
  `tools/make_media.py` (clip_world) depends on it.
- **Warden teams are cut to 3 kin.** `script.c team_from()` copies only 3,
  and `battle.c` has TEAM_MAX 3 on the base. The bouts branch raises this;
  merge it first.
- **`script.c set_battle_scene` maps only 5 scenes.** Extend it to
  SC_CITY..SC_LAIR once the bouts branch's backgrounds exist.
- **`menu.c item_battle_usable()`** must accept IK_HEAL_CURE / IK_TEA_ALL /
  IK_REVIVE (or call the bouts branch's `battle_item_kind_usable()`).
- **The reachability flood in tools/tests/harness.h** must follow teleport
  pads (Mirror Hall) and water when surfing (Sea Route), and treat solved
  puzzles as open once traversal makes objects solid. Several region notes
  ask for this.
- **Pushable boulders:** traversal must support boulders that can be pushed
  without the STRENGTH crest (far's arg-1 "pumice" convention).
- **The kin viewer's type badges overlap its help text** (cosmetic, debug.c).
- **Scratchpad:** agents shared the session scratchpad and overwrote each
  other's helper scripts; that didn't affect any repo file.
