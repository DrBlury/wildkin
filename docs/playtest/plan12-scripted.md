# Plan 12 scripted playtime — measured ROM checkpoints, not act totals

## Current expansion ROM: four-actor layout follow-up (2026-09-27)

Branch `finish-timing-layout` at expansion base `87beed5`; local `make` produced `game.gba`/`game.elf` (3,649,680-byte ROM) and `make shot` built `build/shot`. The runner resolves the anonymous Battle by a unique DWARF member signature: **21,396 bytes**, with `state=792`, `result=820`, `timer=860` (and the other live offsets supplied to C at invocation). This replaces the older 10,556-byte/source-line policy. Blank in-memory SRAM; setup/debug warp excluded. No human playtest and no full act result.

| Act | Last verified checkpoint on this ROM | Frames | Minutes | Outcome |
| --- | --- | ---: | ---: | --- |
| I | Meadow (23,22) | 50 | 0.014 | Checkpoint only |
| II | Brookmill Trail shore → Brookmill (37,17) → Copperline entry (0,17) | 1393 | 0.389 | Last settled checkpoint; at Copperline (9,17) warden bout intro stalls with state 0/timer 1; exit 2 at 2220 attempted frames/0.619 min, no victory |
| III | Heron Fen (22,19), adjacent to warden | 840 | 0.234 | Last settled checkpoint; warden bout intro stalls with state 0/timer 1; exit 2 at 1514 attempted frames/0.422 min, no victory |
| IV | Cinder Crossing (33,18) | 50 | 0.014 | Checkpoint only |
| V | Foothills (25,30) | 57 | 0.016 | Checkpoint only |
| VI | Hollow Downs (33,20) | 58 | 0.016 | Checkpoint only |
| VII | Mistfen (24,27) | 50 | 0.014 | Checkpoint only |
| VIII | Ossuary 1 (15,10), bout initiated | 524 attempted | 0.146 attempted | Battle ran and party lost; recovery to map 5, not a victory |

The Act II/III success tests fail on this ROM: both bouts enter mode 8 but the intro timer stops advancing at 1. After 300 unchanged intro iterations the runner fails closed instead of counting arbitrary stalled frames. This is a ROM-observed runtime blocker, not evidence of a won warden fight or of a particular source-code defect; Act VIII's different bout does progress to loss. Until the intro issue is resolved, the old branch's Copperline/Lumen and Heron/Reedwick victories below are **historical measurements on an older ROM, not current expansion evidence**. Even once bouts work, a pair fight will stop at an explicit unsupported actor/target-policy error rather than fake a single-target win. Master wins, properly prepared party, natural Act II/III starts, healing and human timing remain unmeasured.

## Historical pre-merge measurements

2026-09-27, isolated branch `finish-timing-followup`, based on 2837b2e (integrated shore fix and fail-closed runner). Local `make && make shot` produced `game.gba`, matching `game.elf`, and `build/shot`; runner compiled against libmGBA. Reproduce with `python3 tools/playthrough/run.py tools/playthrough/actN.route` in `/tmp/wildkin-finish-timing-followup`. Blank memory-backed SRAM; no user save opened. Timer rate: 59.7275 ROM frames/s. Setup/debug warp excluded; blocked waits included in attempted count. `CHECKPOINTS_COMPLETE` is not a full act.

| Act | Last ROM checkpoint | Frames observed | Minutes | Outcome |
| --- | --- | ---: | ---: | --- |
| I | Meadow (23,22) | 49 | 0.014 | Checkpoint only; no Master |
| II | Brookmill Trail shore (50,19) → north of Sorrel (57,17) → Brookmill (0,17) → Copperline (0,17) → Lumen (0,20) | 3086 | 0.861 | Checkpoints only; Copperline road warden victory, zero wild; no Hall |
| III | Heron Fen (22,19) warden victory → (10,18) → (1,19) → Reedwick (39,19) | 3462 | 0.966 | Checkpoints only; one ROM-observed warden victory (frame 2992), zero wild; Reedwick reached, no Hall |
| IV | Cinder Crossing (33,18) | 50 | 0.014 | Checkpoint only |
| V | Foothills (25,30) | 57 | 0.016 | Checkpoint only |
| VI | Hollow Downs (33,20) | 59 | 0.016 | Checkpoint only |
| VII | Mistfen (24,27) | 51 | 0.014 | Checkpoint only |
| VIII | Ossuary 1 (15,10) | 556 attempted | 0.155 attempted | Adjacent warden battle lost with debug Lv20 starter; recovery to map 5, not traversed |

The Act II `BROOK_TRAIL_ELEV` bridge x27–34/y17–18 remains raised above the shore, so the old direct x34,18 → x35,18 waypoint still collides. The integrated shore fix opens x34,19 → x50,19. A deliberate probe continuing east at y19 blocked at (53,19), frame 1028, mode 0/dialog 0: `src/game/world/east/npcs.inc` has warden Tam on (54,19). This is a route waypoint error, **not** a newly proven source blocker. From (50,19), stepping north to (50,18), proceeding to (57,18), north to (57,17), and east avoids Tam and Sorrel (58,18); all are ROM-walked without a post-start teleport. Act II reaches Lumen after a Copperline road warden victory at frame 2577; the successful fixture ends at its entry, not at Volt Hall. An independent optional probe physically walked from the same Brookmill Trail start to Brookmill Hearth door (5,13), verified arrival inside at (5,8) in 868 frames/0.242 minutes; it did **not** heal and is not additive to the Act II fixture. A Lumen Hall probe reached the grand stairs (24,9) at frame 3806 but did not establish a passable continuation to the Hall: x22,9 blocked the simple westward waypoint. Do not count that probe as a Hall interaction or source defect until an alternate route has been verified.

Act III's (21,19) Heron Fen warden is occupied even after victory; the fixture verifies victory and walks north around it to Reedwick. A separate Reedwick warden probe reached (27,19) at frame 3650, engaged the real warden at (26,19), then lost at frame 4714/1.315 minutes with the single debug Lv20 starter, recovering to map 5 (5,8); those attempted frames are **not** an Act III completion. No scripted healing, properly levelled four-kin party, Saltwind or Current Hall victory was measured. Act VIII loss likewise requires a correctly levelled party and in-game healing, not a RAM heal.

No fixture reaches a Master or completes a whole act, so **none is an act lower bound**. Contract §10's 120 min Act I, 120–150 min Acts II–VII, 60 min Act VIII and 960–1080 min critical-path targets remain targets. A 2.5× human factor may be applied only to *complete* automated act runs and never substitutes for a human session. Automated scripting does not stand in for a human tester; `act2.md` and `act3.md` remain unfilled templates. See `docs/handoff/playtime.md` for reproducible human instructions.
