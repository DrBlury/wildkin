# Plans: long routes, a linear path, backtracking and a living Vale

These plans turn WILDKIN's compact world into a Pokémon-style journey:

- long routes of two or more maps between towns, with hamlets on the way;
- one critical path through the six Hall towns, with a gate that has an
  in-world reason at the end of each act;
- backtracking that pays: ability secrets, cross-region quest chains, town
  projects and loop routes;
- a world that changes day to day: weather fronts, outbreaks, a travelling
  caravan, rematches, festivals and a daily Gazette.

Each plan is written as a **self-contained brief for one agent**, with what
it needs first, which files it owns, what to build and the tests that prove
it.

## Files

| # | File | Work package | Wave | What it does |
| --- | --- | --- | --- | --- |
| — | `README.md` | — | — | This index. |
| 01 | `01_progression_contract.md` | (the contract) | — | The world graph, critical path, gates G1–G7, level curve, new map ids and sizes, save-id and file-ownership rules, the route checklist, the ability-secret register and playtime targets. **Every agent reads it first.** |
| 02 | `02_engine_foundation.md` | ENGINE | 0 (alone, first) | Stable save ids (v6), map id space, NPC show/hide conditions, scripted walking and camera, flag-driven map patches, the **progression solver test**, faster or seamless edges, route authoring tools, quest engine upgrades and event hooks. |
| 03 | `03_routes_east.md` | REGION-EAST | 1 | Brookmill Trail, the Brookmill hamlet, the Copperline rework and mine, Lumen depth (Act II). |
| 04 | `04_routes_west.md` | REGION-WEST | 1 | Heron Fen (the G2 boardwalk), the Reedwick hamlet, Saltwind and Port Brine rework (Act III). |
| 05 | `05_routes_far.md` | REGION-FAR | 1 | Cinder Crossing (G3), the Railhead hamlet and Cindermoor (Act IV); Mistfen (the G6 fog) and the Moonveil and Dreamspire re-level (Act VII). |
| 06 | `06_routes_north.md` | REGION-NORTH | 1 | Stormstep Foothills (the G4 rockslide), the Timberline hamlet, Frostpine and Frosthollow re-level (Act V). |
| 07 | `07_routes_grim.md` | REGION-GRIM | 1 | The Accord Checkpoint (G5), Hollow Downs and the Waychapel, barrows, the Ashen March re-level, the WARD LANTERN (Act VI). |
| 08 | `08_loop_routes.md` | LINKS | 2 | Loop routes Scorchwaste, Aurora Ridge and Greywater Fjord, gated so they never skip a gate. |
| 09 | `09_dynamic_events.md` | EVENTS | 2 | `events.c`: weather fronts, outbreaks, the caravan, happenings, rematches, festivals and the Vale Gazette. |
| 10 | `10_quests_backtracking.md` | SAGA | 3 | FIELD NOTES, town projects (the tram, the Cinder bridge, the lift…), the Vale Courier, the Almanac Survey, the Legend Trail and smaller chains. |
| 11 | `11_story_rival_pacing.md` | STORY | 1 (Acts I–II), then 2 | The act beats and wires, the rival SORREL, the Stillwardens thread, the G1 road wardens, Maple as a hub, pacing rules. |
| 12 | `12_balance_integration_qa.md` | INTEGRATION | 4 (and after each wave) | Merge order, the balance and money sim, playtime measurement, the QA checklist, docs, media and release. |

## Dependency order

```
02 ENGINE ──┬─> 03 EAST ─┐
            ├─> 04 WEST ─┤
            ├─> 05 FAR  ─┼─> 08 LINKS ─┐
            ├─> 06 NORTH─┤             ├─> 10 SAGA ─> 12 INTEGRATION
            ├─> 07 GRIM ─┘             │
            ├─> 11 STORY (I–II) ... (rest after wave 1) ┘
            └─> 09 EVENTS (needs E10) ─┘
```

## How to hand a plan to an agent

Give each agent this prompt, adapted:

> You are the **<WORK PACKAGE>** agent for WILDKIN (GBA, C) in
> `/Users/drblury/Documents/gameboy_test`. Read, in order:
> `docs/plans/01_progression_contract.md`, then `docs/plans/<NN>_*.md`
> (your brief), then `docs/HANDOFF.md` and the `docs/handoff/*.md` notes
> your brief names.
>
> - Work in your own git worktree off `expansion`.
> - Edit only the files your brief says you own.
> - If you need something outside that, write it under "Requests" in your
>   handoff note instead of editing it.
> - Keep `make art && make && make test` green, with zero warnings.
> - Finish by writing the handoff note your brief names, with screenshots
>   from `build/shot`.

**Tips:**

- **Run 02 alone, and merge it before anything else.** The save-id work (E1)
  is what makes parallel region work safe.
- **Wave 1 agents may run in parallel.** They only touch their own region
  directory, plus a few agreed one-line edits listed in each brief. Door
  and edge coordinates that two plans share are marked "agree with plan
  NN". If agents run at the same time, have them record the chosen
  coordinate in the contract's §6 table, or pick the stated default.
- **Plan 05 is the biggest**: two acts, both in `world/far/`. Split it into
  part A and part B for two agents if you like; part B appends only after
  part A merges.
- **Cut scope** if needed:
  - the Stillwardens thread (plan 11 §3 has a fallback);
  - E7 step 2 (seamless edges);
  - the Greywater Fjord;
  - festivals.
- **Keep:** gates G1–G7, the progression solver, the new routes and
  hamlets, FIELD NOTES and at least the tram and bridge projects.

## Facts these plans rely on (checked 2026-09-27)

- **83 real maps.** Every route is one map (40–50 cells) today.
- **No gate** exists beyond "have a starter". Cindermoor is reachable at
  Lv5.
- **Positional ids.** Save version 5. Every saved id (flags, satchels,
  wardens, quests, lore, maps, puzzle and secret bits) is positional across
  the region `.inc` files. **Adding ids breaks saves until plan 02 E1
  lands.**
- **`visited` overflow.** `TravelState.visited` holds 128 map bits, with
  no bound check (`travel.c:1199`).
- **Engine gaps:**
  - edges always fade (not seamless);
  - NPCs can't be shown or hidden by flag, and scripts can't walk them;
  - weather is global CLEAR or RAIN only, and `MF_SNOW` is unused;
  - there is no outbreak or roaming support.
- **Free save capacity:** story flags about 460 bits, satchels about 400,
  wardens about 445, quests 36 of 48, and about 2.2 KB in the save slot.
