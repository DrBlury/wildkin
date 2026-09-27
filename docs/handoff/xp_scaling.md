# Per-recipient XP scaling handoff

`monster_xp_yield` still computes the species/level/trainer base. For each awake,
non-max-level recipient, the battle first computes its existing full active or
half bench share and applies QUICK STUDY (+20%), bond 200+ (+10%) and the meal
percentage in that order. Then `monster_scaled_xp(share, foe_level,
recipient_level)` applies the same rule used by the act simulator:

- If recipient level <= foe level, awarded XP = max(1, share): **no bonus** for
  an underlevelled kin.
- Otherwise, with gap = recipient level - foe level, awarded XP =
  **max(1, floor(share * 3 / (3 + gap)))**. The multiplier is 3/(3+gap),
  monotonically decreasing from 75% at gap 1 toward zero; an award never
  falls below 1 XP. Neither the stored XP curve nor save layout changes.

For a 120 XP share against a Lv20 foe, a Lv15 or Lv20 kin gets 120 XP, Lv21
gets 90, Lv23 gets 60, and Lv29 gets 30. A Lv20 active kin facing a Lv15 foe
receives floor(3/8 of its modified share), while a Lv15 bench kin still
receives its unscaled half share. The simulator deliberately uses neutral
traits/bond and no meal buffs and shares XP round-robin as before.

## Deterministic direct Hall-path trace

Fresh runs compiled from `tools/test_game.c` before/after this change. Each
entry is mean party level on arrival; Master minima and all ±2 assertions
remain unchanged. Master XP is awarded only **after** the arrival check.

| Act | Master minimum | Before (delta) | After (delta) | After zero-wild diagnostic |
| --- | ---: | ---: | ---: | ---: |
| I Home | 12 | 14 (+2) | 13 (+1) | 12 |
| II East | 21 | 22 (+1) | 20 (-1) | 19 |
| III West | 25 | 27 (+2) | 25 (0) | 24 |
| IV Forge | 31 | 33 (+2) | 31 (0) | 29 |
| V North | 34 | 40 (+6) | 36 (+2) | 35 |
| VI Ash | 38 | 46 (+8) | 40 (+2) | 39 |
| VII Dream | 42 | 51 (+9) | 44 (+2) | 42 |
| VIII Finale | dynamic | 57 | 51 | 49 |

All seven arrival bands and the normal-rate no-extra-grinding checks pass;
the zero-wild pass is a stress diagnostic, not the no-grind criterion. The
model assumes all mapped wardens are fought and does not simulate survival,
route walkability or time-specific NPC availability.

## Validation caveats and decision needed

`tools/tests/test_xp_scale.c` and `tools/tests/test_battle.c` pass. The
unchanged `tools/test_game.c` has one XP assertion that expects the **full**
base and half-base from a Lv10 wild foe for a Lv20 active/bench pair. That
expectation is incompatible with any strictly lower-level-opponent reduction
at a ten-level gap; it now fails even though its other battle and all act
checks pass. No test assertion or Master level was changed. The owner of
`tools/test_game.c` should update the fixture/expectation to test both sharing
and the new level-gap rule after reviewing this policy. `make test` is also
blocked earlier by three unrelated `tools/test_field.c` map edge/door/reachability
failures on this branch and therefore does not reach `test_game` in the make
sequence. Keep the failing checks visible rather than marking the suite green.
