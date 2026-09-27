# 12 — Balance, integration, QA and release

**Work package:** INTEGRATION. It runs last. It may also be run in small
slices after each wave merges.

**Needs:** everything else merged, or the wave being integrated.

**Owns:**

- `tools/test_game.c` (the balance sim);
- the new `tools/playthrough/` scripts;
- `README.md`, `docs/HANDOFF.md`, `docs/EXPANSION.md` §9 (the world map
  section) and `docs/WORLD.md` §11;
- `tools/make_media.py` clips for the new areas;
- the CI workflow's file lists.

**Contract:** `01_progression_contract.md`, all of it. This plan checks it.

---

## 1. Merge order and conflicts

**Merge in waves.** After each wave:

1. `make art && make && make test` passes, with zero warnings;
2. a v5 save from `main` still loads.

| Wave | Plans | Notes |
| --- | --- | --- |
| 0 | 02 ENGINE | Alone. E6 is expected to report today's lack of gates (xfail). |
| 1 | 03 EAST, 04 WEST, 05 FAR, 06 NORTH, 07 GRIM, 11 STORY (Acts I–II slice) | Parallel worktrees. They conflict only in `world/all_*.inc` (new files are appended; keep the region order), the three one-line `village/maps.inc` link edits, and generated files. |
| 2 | 08 LINKS, 09 EVENTS, the rest of 11 STORY | 08 needs the door stubs from wave 1. |
| 3 | 10 SAGA | Needs everything placed. |
| 4 | 12 INTEGRATION | This plan. |

**Generated files** are never merged by hand. Regenerate them with
`make art`:

- `src/gfx_field.h`, `src/gfx_travel.h`
- `src/species_data.h`, `src/gfx_monsters.h`
- `src/game/world/debug/*`

**Save ids.** After each wave:

- run `test_save_ids` (E1);
- commit the new golden layout **in the merge commit**;
- load a v5 save and the previous wave's save, and diff flag, satchel and
  warden bits by *name*. Add a `tools/save_dump` helper if needed; it prints
  set flags by name.

---

## 2. Balance

**Sim.** Extend `tools/test_game.c`:

1. Walk the **critical path act by act**, using contract §3 and the E6 act
   table.
2. Per act, simulate:
   - one fight against every warden on critical-path maps;
   - *k* wild bouts per route map, with *k* = 6 on routes and 3 on
     hamlets, at the zone's mean level;
   - the XP rules as coded (team XP, bench half, QUICK STUDY off, no meal
     buffs);
   - a starter plus a typical team of 4, picked from that act's zones.
3. Record the **team level on arrival at each Master**.

**Asserts:**

- The arrival level is within ±2 of the Master's lowest kin.
- If it is too low, raise route warden counts or wild levels, in that
  order. Never raise the Master.
- **No act needs grinding:** with 0 extra wild bouts, the arrival level is
  ≥ the Master's lowest kin − 4.

**Money.** Simulate coins from wardens, satchel sell values and 1 farm
harvest per act. Then assert that:

- project costs (plan 10 §3) are affordable by the act where each project
  is offered, plus one;
- the ferry (500c) is affordable in Act III.

**Rival and Stillwarden teams:** within ±2 of contract §5 for their map.

**Levels table:** E6 checks zone min/max against contract §5. Keep one
source of truth: move the table into a C header that the test and this sim
share.

**Legends:** CALDERON and NOCTHALE are reachable mid-game (see plan 05 A4).
Decide from the sim whether they need the post-game gate. A legend at Lv50+
met at party Lv32 is fine *if it can't be caught trivially*: check its
catch odds at 1 HP with a STAR LANTERN.

---

## 3. Playtime measurement

**Scripted playthroughs.** `build/shot` already takes a script file.
Extend `tools/playthrough/`:

1. One script per act. It warps to the act start with the right flags and
   walks the critical path by coordinates, via a waypoint list. Bouts
   auto-resolve through the sim's policy: always use the best move, never
   run from wardens, and flee wild bouts after *k*.
2. Count frames, converted to minutes.

This is a **lower bound**: a human explores. Compare it with contract §10
(the targets). Use a 2.5× human factor as a rule of thumb, and report both
numbers.

**Human pass.** Ask the user to play Act II and Act III end to end. Collect
notes in `docs/playtest/act2.md` and `act3.md` with the templates in §6.

---

## 4. QA checklist (per act)

**Gates:**

- The gate's reason is shown before the gate.
- The gate opens on its condition.
- No soft-lock: try walking back from every map in the act without the next
  gate's flag.

**Routes:**

- The §8 checklist items are all present: shape, landmark, 2+ zones,
  wardens, a stop, satchels, lore, berry and event hook.
- Signs name both ends.
- Banners slide in once.

**Transitions:** walking a whole route has either no fades (E7 step 2) or
short ones (E7 step 1).

**Budgets:** on every map, at the worst flag, time and event state,
`test_field`'s people, sprite and tile budgets pass.

**Night and day:** walk each route at night. Night slots appear, and E3
night-only NPCs swap.

**Events:** force each `EV_*` on each act's routes (debug menu, below) and
check for no glitches.

**Saves:**

- Save mid-route, mid-quest and mid-project. Reload.
- Load a v5 save made at the Rise before DRAKORA, then play to Brookmill.

**Art:** the art lint passes, with no ground baked into objects.
`check_kin_clip` isn't relevant here.

**Admin and debug:**

- The WARP menu lists every new map.
- Add an EVENTS page to the debug menu (force an event or front for today).
- Add an ACT page (set the flags for act *N*). The ADMIN mode doc
  (`docs/handoff/admin.md`) should mention both.

---

## 5. Docs and media

- **`README.md`:** the new world map image, one screenshot per new route and
  hamlet, a short "The Vale's routes" section, and events and quests
  summaries.
- **`docs/EXPANSION.md` §9:** replace the ASCII world map with contract §2,
  and link `docs/plans/01_progression_contract.md`.
- **`docs/WORLD.md` §11:** update the world map and area table, and add
  the Stillwardens and Sorrel to the story section if plan 11 shipped them.
- **`docs/HANDOFF.md`:** a new top note that summarises this effort, links
  every `docs/handoff/*.md`, and lists known leftovers.
- **Media** (`python3 tools/make_media.py`):
  - re-render the world with the loops (plan 02 E8 `WORLD_POS`);
  - new clips: a Brookmill mill wheel, a Heron Fen fog front, the Cinder
    bridge before and after, the Mistfen fog lifting, and the caravan
    arriving.
- **Release:** merge `expansion` into `main`, push, and tag the release as
  in the existing memory notes (CI builds the ROM on `v*` tags). **Only
  when the user asks.**

---

## 6. Templates

`docs/playtest/actN.md`:

```
# Act N playtest — <date>, <tester>
Start: save / flags   | Party on arrival at Master: levels
Time: route A __ min, hamlet __, town __, Hall __
Got lost? where:
Too hard / too easy:
Bugs (map, x, y, what):
Best moment / worst moment:
```
