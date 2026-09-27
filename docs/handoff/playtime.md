# Playtime measurement handoff

Plan 12 §3/6 requests complete ROM-backed act measurements plus real tester passes. The current `tools/playthrough/` runner advances dialog and ROM-observed warden bouts (highest available raw-power×accuracy attacking move), counts battle outcomes, checks exact waypoints/explicit edge transitions, and fails closed on unsupported choices, healing, party switches and losses. **Whole-act scripted timing and human Act II/III playtime remain incomplete.** No 16–18h finding is supported. See [measured checkpoints](../playtest/plan12-scripted.md), [runner policy](../../tools/playthrough/README.md), and the unchanged human [Act II](../playtest/act2.md)/[Act III](../playtest/act3.md) templates.

Reproduce the post-stack-fix expansion ROM on branch `finish-act3-timing` in `/tmp/wildkin-finish-act3-timing`: `make && make shot && python3 -m unittest tools.tests.test_playthrough_runner`, then run `python3 tools/playthrough/run.py tools/playthrough/act2.route` and `python3 tools/playthrough/run.py tools/playthrough/act3.route`. The acceptance assertion for a genuine Act III warden victory remains red. Exit 2 means blocked, not completed. Blank in-memory SRAM; never pass or modify a user `.sav`. Act II reaches Lumen after a ROM-observed Copperline warden victory (2971 frames/0.829 min). Act III reaches Heron Fen (22,19) at 838 frames/0.234 min, then returns to title mode 10 at 1138 attempted frames/0.318 min without an observed battle-mode frame or victory. Source loss handling returns to a Hearth in field mode; this looks like a reset rather than a normal loss, but the underlying fault is not established. The runner did not reach its paired-battle policy. Debug warp creates only a single Lv20 FLARIX, so prepared-party and full-act conclusions remain open. See `plan12-scripted.md` for observed output; historical pre-merge victories are not current-ROM evidence.

## Human pass to request from a tester (not yet performed)

1. Record ROM build commit, tester/date, starter/team levels and clean Act II start save/flags. Play naturally **from Act II start through VOLT HALL Master victory**, including Brookmill Trail, Brookmill, Copperline and Lumen; time each leg separately with a clock. Capture every gate reason and note if the shore detour via (34,19) differs in a normal start save. Save/load at a safe checkpoint; do not overwrite a personal save without first making a copy.
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

For complete automated act totals still needed: in-game healer, quest/Hall interactions and choices, correct per-act party, measured recoveries (not RAM restores), wild encounter counts and 3/6 quotas, and victories through each Master. Review blocked map source separately; never extrapolate a partial clip to the 16–18h target.

## Historical ROM-only follow-up (pre-merge)

A verified door command now moves from an exact adjacent tile into an interior and checks the observed destination: Brookmill Hearth entrance reached (5,8) from Brookmill (5,14), in a separate 868-frame probe. No heal was performed; do not sum this probe with the 3086-frame Act II route. A Lumen grand-stairs probe reached (24,9), but the simple west waypoint blocked at (23,9) when trying to enter (22,9), and no Volt Hall door/master interaction is verified. Act III Reedwick warden loss at 4714 attempted frames prevents extending the success fixture without a measured, correctly prepared party/recovery. Human templates are blank and the 16–18h target remains unmeasured.
