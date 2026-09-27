# Plan 12 scripted playtime — measured ROM segments, not act totals

2026-09-27, isolated branch `plan-routes-playtime`; `make` built local ROM and `make shot` built libmGBA. Reproduce from `/tmp/wildkin-plan-playtime` with `python3 tools/playthrough/run.py tools/playthrough/actN.route` after building. Blank in-memory SRAM, no external save input or save writes. Start warp and setup excluded. Time uses 59.7275 ROM frames/second. See [runner policy](../../tools/playthrough/README.md).

| Act | ROM start / checked end | Verified traversed frames | Minutes | 2.5× human heuristic (not measured) | Result |
| --- | --- | ---: | ---: | ---: | --- |
| I | Meadow (20,22) → (23,22) | 49 | 0.014 | 0.034 | segment only |
| II | Brookmill Trail (32,18) → (34,18) → (34,19) | 50 | 0.014 | 0.035 | stalls east at (34,19), 291 attempted frames / 0.081 min including blocked wait |
| III | Heron Fen (32,20) → (50,19) → (22,19) | 827 | 0.231 | 0.577 | stalls west at (22,19), 1068 attempted frames / 0.298 min including blocked wait; warden at (21,19) |
| IV | Cinder Crossing (30,18) → (33,18) | 51 | 0.014 | 0.036 | segment only |
| V | Foothills (22,30) → (25,30) | 54 | 0.015 | 0.038 | segment only |
| VI | Hollow Downs (30,20) → (33,20) | 53 | 0.015 | 0.037 | segment only |
| VII | Mistfen (24,30) → (24,27) | 51 | 0.014 | 0.036 | segment only |
| VIII | Ossuary 1 (15,10) | 0 verified | — | — | stalls immediately on adjacent move; warden at (15,9), 241 attempted frames / 0.067 min |

The Act II obstruction is at the Brookmill bridge/towpath elevation transition, with field mode 0 and no checkpoint beyond (34,19); dialog=0, so collision/elevation rather than an active dialog. Act III's next tile is occupied by a route warden, which the runner cannot battle. Act VIII queues a dialog (dialog=2) at the start beside a warden. The other five green segments are only short, verified coordinate traversals, not critical paths. None reaches a Master or yields a lower bound for a **whole act**. The 2–2.5h per-act and 16–18h total figures in contract §10 remain targets, not observed results. No human Act II/III pass is represented here; the existing `act2.md` and `act3.md` remain unfilled user-facing templates.
