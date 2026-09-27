# Act II ROM timing: Volt Hall approach, not Master victory

In the isolated `finish-act2-hall-timing` worktree, the route starts at
Brookmill Trail with only `FLAG_STORM_CALMED`, a blank in-memory SRAM, and the
title debug warp's **single Lv20 FLARIX**. No post-start RAM heal, warp,
teleport, switch or flag write occurs. ROM movement climbs the Lumen Beacon
stair (23,11 → 24,11 → 24,9), crosses the Crown to (10,7), and enters the
Hall via its actual door, arriving (7,16). The Hall route steps on switches
at (4,13), (3,9), (11,9); each expected on-state is read from `sw_on` after
the walking animation settles. It ends (7,3), beside Fara at (7,2).

| Observed checkpoint | Cumulative frames | Minutes at 59.7275 fps |
| --- | ---: | ---: |
| Juno victory | 3,040 | 0.848 |
| Lumen entry | 3,466 | 0.967 |
| Volt Hall door settles | 4,324 | 1.207 |
| Hall warden victory | 5,440 | 1.518 |
| Switches a / b / c on | 5,496 / 5,615 / 5,926 | 1.533 / 1.567 / 1.653 |
| Fara-adjacent (7,3), **no challenge** | **6,154** | **1.717** |

Two opponent victories are ROM-observed (`BOUT_END kind=warden result=1`):
Juno on Copperline and one Hall warden. Wild wins/runs are both zero; no
encounters are manufactured to satisfy the plan's quota. Switches are
verified but no crest or Master victory was observed. Plan 01 §10 targets
2–2.5h per Act II–VII and 16–18h critical path; Plan 12 §3's 2.5× factor
is only a heuristic for complete scripted runs, not a way to extrapolate
this partial probe. No human tester is available; human templates remain
blank.

## Reproduce the stopping gate

From `/tmp/wildkin-finish-act2-hall-timing`, run `make`, `make shot`,
`python3 -m unittest tools.tests.test_playthrough_runner`, and
`python3 tools/playthrough/run.py tools/playthrough/act2.route`. To reproduce
the blocked party probe without editing the committed route or a save:

```sh
cp /tmp/wildkin-finish-act2-hall-timing/tools/playthrough/act2.route /tmp/wildkin-act2-party-probe.route
printf 'party_min 4\n' >> /tmp/wildkin-act2-party-probe.route
python3 /tmp/wildkin-finish-act2-hall-timing/tools/playthrough/run.py /tmp/wildkin-act2-party-probe.route
```

Expected exit **2**: `BLOCKED line=45 reason=insufficient in-game party for
Master map=19 x=7 y=3 ... wardens=2 ... frames=6154`. This is a policy
block at Fara's adjacent cell, not a claim that the Hall is unreachable.
A separate exploratory `warden MAP_VOLT_HALL 7 3 north` probe was also
rejected after 12,000 attempts: Fara's ROM script uses an explicit YES/NO
challenge and this generic command cannot authorize it. Do **not** append
that command to the passing route or count its attempted frames as playtime.

To measure a Master victory, prepare a representative team **at act start**
through the game's admin ADD KIN menu or a deterministic disposable act-start
save (never a user's save); verify its levels, HP/PP and composition, handle
the Master YES/NO choice explicitly, account for any real in-game healing and
party switches, then demand a ROM-observed six-opponent victory and
`FLAG_VOLT_CREST`. The current single-kin route cannot substantiate that
result. No game source or human template was altered.
