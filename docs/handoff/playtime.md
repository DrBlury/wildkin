# Playtime measurement handoff

Plan 12 §3/6 requests complete ROM-backed act measurements plus real tester passes. The current `tools/playthrough/` runner advances dialog and ROM-observed warden bouts (highest available raw-power×accuracy attacking move), counts battle outcomes, checks exact waypoints/explicit edge transitions, and fails closed on unsupported choices, healing, party switches and losses. **Whole-act scripted timing and human Act II/III playtime remain incomplete.** No 16–18h finding is supported. See [measured checkpoints](../playtest/plan12-scripted.md), [runner policy](../../tools/playthrough/README.md), and the unchanged human [Act II](../playtest/act2.md)/[Act III](../playtest/act3.md) templates.

Reproduce: from `/tmp/wildkin-finish-timing-v2`, run `make && make shot && python3 -m unittest tools.tests.test_playthrough_runner`, then `python3 tools/playthrough/run.py tools/playthrough/act2.route` and `python3 tools/playthrough/run.py tools/playthrough/act3.route`. Exit 2 means a blocked waypoint, not a completed act. Blank in-memory SRAM; do not pass, modify or release any user `.sav`. Act II blocks from Brookmill Trail (34,18) east across the bridge x35 (source `BROOK_TRAIL_ELEV` rows 17–18); this was sent to the coordinator. Act III defeats the Heron Fen warden and reaches Reedwick (39,19), but the single debug Lv20 starter loses a subsequent Reedwick warden probe; Saltwind and Current Hall remain unmeasured. Act VIII loses its warden battle with the debug Lv20 single kin. No gameplay source, Makefile, or save layout changed here.

## Human pass to request from a tester (not yet performed)

1. Record ROM build commit, tester/date, starter/team levels and clean Act II start save/flags. Play naturally **from Act II start through VOLT HALL Master victory**, including Brookmill Trail, Brookmill, Copperline and Lumen; time each leg separately with a clock. Capture every gate reason and note Brookmill bridge at (34,17–19) if inaccessible. Save/load at a safe checkpoint; do not overwrite a personal save without first making a copy.
2. Continue **from Act III start through CURRENT HALL Master victory** via Heron Fen, Reedwick, Saltwind and Port Brine/Gull Isle as required by the game. Time each leg and all recovery/healing, detours, wild fights and retries rather than discarding them. Note at Heron Fen (21,19) whether the warden can be fought and walked around afterward.
3. Copy the following blank note template into the existing `docs/playtest/act2.md` and `act3.md` *only after the tester supplies results*. Human and ROM-scripted times must be kept distinct.

```text
Act / date / tester / ROM commit:
Start save or flags; party levels and composition:
End flag / Master victory evidence; party arrival levels:
Time by route / hamlet / town / Hall / healing / retry; total:
Wild fights, flights, warden bouts, healing assumptions:
Got lost? map and coordinates:
Difficulty; best/worst moment:
Bugs: map, x, y, flags/weather, reproduction steps, screenshot:
```

For complete automated act totals still needed: transition and interior door checkpoints, in-game quest/Hall interactions and choices, correct per-act party, measured recoveries (not RAM restores), wild encounter counts and 3/6 quotas, and victories through each Master. Review blocked map source separately; never extrapolate a partial clip to the 16–18h target.
