# Plan 12 scripted playtime — measured ROM checkpoints, not act totals

2026-09-27, isolated branch `finish-timing-v2`, based on d60000b. Local `make && make shot` produced `game.gba`, matching `game.elf`, and `build/shot`; runner compiled against libmGBA. Reproduce with `python3 tools/playthrough/run.py tools/playthrough/actN.route` in `/tmp/wildkin-finish-timing-v2`. Blank memory-backed SRAM; no user save opened. Timer rate: 59.7275 ROM frames/s. Setup/debug warp excluded; blocked waits included in attempted count. `CHECKPOINTS_COMPLETE` is not a full act.

| Act | Last ROM checkpoint | Frames observed | Minutes | Outcome |
| --- | --- | ---: | ---: | --- |
| I | Meadow (23,22) | 49 | 0.014 | Checkpoint only; no Master |
| II | Brookmill Trail (34,18), after detour via (34,19) | 683 attempted; 82 to last verified waypoint | 0.191 attempted | Blocked east at (34,18) toward (50,18), mode 0/dialog 0; x35 bridge transition |
| III | Heron Fen (22,19) warden victory → (10,18) → (1,19) → Reedwick (39,19) | 2226 | 0.621 | Checkpoints only; one ROM-observed warden victory (frame 1760), zero wild; Reedwick reached, no Hall |
| IV | Cinder Crossing (33,18) | 50 | 0.014 | Checkpoint only |
| V | Foothills (25,30) | 57 | 0.016 | Checkpoint only |
| VI | Hollow Downs (33,20) | 59 | 0.016 | Checkpoint only |
| VII | Mistfen (24,27) | 51 | 0.014 | Checkpoint only |
| VIII | Ossuary 1 (15,10) | 556 attempted | 0.155 attempted | Adjacent warden battle lost with debug Lv20 starter; recovery to map 5, not traversed |

The Act II `BROOK_TRAIL_ELEV` rows 17–18 in `src/game/world/east/data.h` mark elevated bridge x27–34 and transition x35 (`<`); south towpath (34,19) → east and bridge (34,17) or (34,18) → east all fail in the ROM with no active dialog. Source owner needs to inspect passage from x34 to x35 before the route can be claimed reachable. Act III's x21,19 NPC is occupied even after victory; moving from x22,19 north then west bypasses it. The new explicit `warden` fixture ensures that detour does not silently omit the bout. A separate temporary probe reached Reedwick (27,19) at frame 2414 but lost to its warden by frame 5478 with the single debug Lv20 starter; that probe is not a fixture success and no salvage/recovery is counted. Act VIII loss likewise requires a correctly levelled party and in-game healing, not a RAM heal.

No fixture reaches a Master or completes a whole act, so **none is an act lower bound**. Contract §10's 120 min Act I, 120–150 min Acts II–VII, 60 min Act VIII and 960–1080 min critical-path targets remain targets. A 2.5× human factor may be applied only to *complete* automated act runs and never substitutes for a human session. Automated scripting does not stand in for a human tester; `act2.md` and `act3.md` remain unfilled templates. See `docs/handoff/playtime.md` for reproducible human instructions.
