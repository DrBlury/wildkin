# STORY route integration handoff (plan 11)

Branch `plan-routes-story`, worktree `/tmp/wildkin-plan-story`, starting from E1/E2 `ca6a672`.
This is **wave 1 authoring plus the crest wire spine**, not a claim that all eight acts are live.
No region map links, engine files, art generators, or other region files were changed.

## Built acts and pacing

| Act | Hook / turn / hand-off in this branch | Runtime status |
| --- | --- | --- |
| I, Home | Kindling and Marlo remain existing; Sorrel's Maple/Meadow teams and scripts are authored; DRAKORA grants existing `FLAG_STORM_CALMED`; two-cell east/west warden barriers and ridge warning are authored. Rise's STORMHAWK max is 15. | Maple Hearth's east wire is live. Sorrel and G1 NPCs wait for E3 registration. |
| II, East | Sorrel's Brookmill team, Lumen Husher and Fara-to-Port-Brine wire authored. | Crest wire is live at Maple; placements wait for route owners' coordinates and E3. |
| III, West | Harbour Sorrel team and Saltwind Husher; Tide-to-Cinder wire. | Wire live at Maple; encounters staged. |
| IV, Forge | Bellwright team and Anvil-to-Rise wire. | Wire live at Maple; encounter staged. |
| V, North | Muffle team and Rime-to-Accord wire. | Wire live at Maple; ally double-bout deferred until battle owner supplies ally API. |
| VI, Ash | Vesta team and Lantern-to-Mistfen wire. | Wire live at Maple; Gravewood rescue and barrow encounter deferred. |
| VII, Dream | Vesta reconciliation line and Dream-to-Ossuary wire. | Wire live at Maple; Dreamspire meeting deferred. |
| VIII, Finale | Sorrel six-kin finale team; existing grim Ossuary ending unchanged. | Finale NPC deferred. |

`story_act()` returns 1 before the calm, 2 after the calm, through 8 after Dream and 9 after OSSUREX. The current wire helper uses crest flags (`FLAG_VOLT_CREST`, `FLAG_TIDE_CREST`, `FLAG_CREST_ANVIL`, `FLAG_RIME_CREST`, `FLAG_LANTERN_CREST`, `FLAG_CREST_DREAM`) and `FLAG_STORM_CALMED` rather than warden-beaten bits. The newest unread wire is delivered once; older wires are silently caught up. Maple's Tender calls it before healing/autosave to persist the read flag. Other Hearths still need the same call on REST; do that centrally in the engine `heal_answer`/Hearth callback rather than duplicating regional scripts.

## Story flags

- `FLAG_STORY_WIRE_HOME`, `_VOLT`, `_TIDE`, `_ANVIL`, `_RIME`, `_LANTERN`, `_DREAM`: respective Keeper wire has been read; none is a gate key.
- `FLAG_SORREL_STARTER_FIRE`, `_WATER`, `_LEAF`: remembers the player's Kindling starter so Sorrel keeps the advantage even if party slots change. The first encounter derives it from the LAB-met starter or its evolution. If the starter leaves the party before that first encounter, add a Kindling-choice setter in engine `keeper_confirm` to establish the flag at selection.
- `FLAG_SORREL_MAPLE`, `_MEADOW`, `_BROOKMILL`, `_HARBOUR`, `_TEAMUP`, `_LANTERN`, `_FINALE`: Sorrel wins/one-off beats; **never** gates. Only Maple/Meadow callbacks currently set their flags. The latter five are reserved for regional placement/integration.
- `FLAG_STILL_LUMEN`, `_SALTWIND`, `_EMBER`, `_GLIMMER`, `_BARROW`: reserved completion flags for the corresponding Stillwarden turn; not used as gates.
- Existing `FLAG_STORM_CALMED`: sole G1 opening condition. Existing crest flags remain region-owned.

## Integration checklist

1. E3: `story/npcs.inc` is deliberately **not included** in `all_npcs.inc` while `PERSON_IF` is unavailable. Ensure its signature is ordinary `PERSON` arguments plus `show_flag, hide_flag` (0 = unrestricted); then register `#include "story/npcs.inc"` between ui and debug. The four G1 road wardens occupy both east Bramblewood exit tiles `(43,17–18)` and west Lake tiles `(0,31–32)`, hidden by `FLAG_STORM_CALMED`; two `show_flag` farewell variants stand aside. This needs a condition refresh when DRAKORA is answered. Don't gate on Sorrel's wins. Check local sprite budget with live E3 state (max seven rendered).
2. E4: after registration, Sorrel can walk up via `npc_walk` and warp out after a winning bout; no scripted movement is invoked in this base. Verify a rematch remains possible on loss. Coordinates `(26,9)` Maple and `(12,5)` Meadow should be checked with the actual elevation/path test.
3. E6: register `story/milestones.inc` in the milestone aggregator (one Rise milestone, no rival dependency), and run the progression solver before claiming G1 isolation. The existing Wood S boulder and forthcoming Rise N rockslide must complete valley containment. `test_story.c` only checks authored placement metadata here, not live G1 traversal.
4. After route merges: place Brookmill Sorrel near Trail E (Act II), Port Brine harbour Sorrel (Act III), Lumen roof Husher, Saltwind Husher, Ember Bellwright, Glimmer Muffle, and Vesta in a free `MAP_BARROW_A` cell (confirm with grim owner) and later Dreamspire. Do not refer to those map IDs in this isolated branch. Supply conditional act windows, callbacks on wins, Husher event hooks (`EV_HUSH` via plan 09/E10) and tests for each map's 24 people / 7 rendered sprites and ±2 levels. The route owners have not yet supplied the new map geometry.
5. E9 and grim: retime `QUEST_HOLLOWING` after DRAKORA into THE WARDENS' ACCORD with crest-stage goals/markers; preserve grim's `grim_keeper_talk()` and Ossuary stages. The current quest engine has neither stage-goal nor marker fields. Coordinate rather than editing grim here.
6. Sorrel cast entry/portrait (art pipeline), ally double bout, Gravewood night rescue/following kin and Rise rematch require art, battle, time/event integration outside this ownership boundary. The placeholder `KID_B` sprite is temporary; do not represent it as finished cast art. Add post-act Maple named-villager lines, Market Hall/tram reserved-lot patches and Gazette/rematch boards after plan 09/10 interface and locations are agreed.
7. Story team roster is defined in `story/trainers.inc`; only Maple/Meadow encounter handlers are implemented in `story/scripts.c`. Remaining team entries and dialogue are authored seeds, not complete encounter scripts. Preserve save-id append order; story is registered after ui before debug for flags/trainers/scripts, but NPC registration is deliberately deferred.

## Verification on isolated base

Run `cc -std=c11 -Wall -Wextra -Wno-missing-field-initializers -Wno-unused-function -o /tmp/wildkin-test-story tools/tests/test_story.c && /tmp/wildkin-test-story`. It tests wire once-only/latest precedence, Sorrel starter triangle and persistence, win/loss flag isolation, team size/levels, Rise level cap, and G1 authored coordinates. E3/E4/E6/E9 integration and cross-region progression cannot be validated on this base.
