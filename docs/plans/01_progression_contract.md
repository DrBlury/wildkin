# 01 — Progression contract: the long-route world

**Read this first. Every other plan in `docs/plans/` follows it.**

**What this file fixes:** the new world graph, the critical path, the gates,
the level curve, the names and ids of every new map, and which work package
owns what. If a region plan and this file disagree, this file wins. Change it
only on purpose, and tell every open work package when you do.

The file does not implement anything; the work packages do (see
`README.md`).

---

## 1. Why we are changing the world

Here is what we have today (inventory taken 2026-09-27):

- **Routes are short.** Every town sits one map (40–50 cells) from the next.
  Maple → Bramblewood → Copperline → Lumen → Cinder Road → Cindermoor is five
  fades.
- **Nothing is gated.** Straight after picking a starter (Lv5) you can walk to
  Cindermoor (wild Lv24–31), the Ashen March (24–34) or Dreamspire (30–36).
  No edge has a flag check, NPC blocker or crest check. Every Hall can be
  taken in any order.
- **The level curve is broken by the neighbours.**
  - Frostpine (18–24) sits next to the start area, but its Hall is Lv33–37.
  - Ashen (24–31) touches Copperline (13–20).
  - Cinder Road (24–31) touches Lumen (14–24).
  - Elderwood (28–35) opens straight off Bramblewood (4–11).
- **Backtracking is thin.** Of the 12 quests, only ISLE_SALT and HOLLOWING
  cross regions. Every legend lair is a dead end that nothing sends you back
  to.

What we want:

- **Pokémon-style long routes.** Two or more map segments between towns,
  each with its own landmark, wardens and a mid-route stop (a hamlet, rest
  house or camp).
- **One clear critical path.** It runs through every Hall town in a fixed
  order. Each gate has an in-world reason, and each gate opens with a crest,
  a field ability or a story beat.
- **Backtracking that pays.** Every early route hides at least one spot that
  a later ability opens. Quest chains send you back through old towns. Loop
  routes and shortcuts make the return trips short.
- **A world that moves.** Daily events, weather fronts, a travelling
  caravan, outbreaks and rematches (see plan 09).

---

## 2. The new world graph

`[x]` = lair or dungeon. `(h)` = hamlet (a small stop with a rest spot).
**NEW** = a new map. `==` = a new loop route (plan 08).

```
                                   [SKY ISLE] (FLY)
                     [WHITECROWN PEAK]
                            |
   GREYWATER FJORD ==== FROSTHOLLOW ==== AURORA RIDGE (NEW, cave-warp loop) ==== DREAMSPIRE -- [DUST LIBRARY]
   (NEW, SURF loop)         |      \__ GLIMMER CAVERNS -- [STARFALL]                 |
        ||           FROSTPINE PASS                                             MOONVEIL PATH
        ||                  |                                                        |
        ||         TIMBERLINE (h, NEW)                                          MISTFEN (NEW)
        ||                  |                                                        |
        ||        STORMSTEP FOOTHILLS (NEW)                                    [fog gate: G6]
        ||                  |  [rockslide: G4]                                       |
        ||           STORMSTONE RISE                                                 |
        ||                  |                                                        |
        ||           WHISPER MEADOW                                                  |
        ||                  |                                                        |
   PORT BRINE - SALTWIND - REEDWICK(h,NEW) - HERON FEN(NEW) - MIRROR LAKE - MAPLE - BRAMBLEWOOD - BROOKMILL TRAIL(NEW) - BROOKMILL(h,NEW) - COPPERLINE - LUMEN -+- CINDER CROSSING(NEW) - RAILHEAD(h,NEW) - CINDER ROAD - CINDERMOOR -- EMBER TUNNEL -- [CALDERA]
      |                                    [boardwalk: G2]            |    [storm: G1]  |                                          |      [bridge out: G3]                                  |                 |
   SEA ROUTE                                                  WILLOW ACRE     [ELDERWOOD HEART]                          [Accord: G5]                                            SCORCHWASTE (NEW loop)   [CLOCKWORK SPIRE]
      |                                                                                                                      |                                                        ||
   GULL ISLE -- [DROWNED BELL]                                                                                         HOLLOW DOWNS (NEW) - WAYCHAPEL (interior)                     ||
                                                                                                                             |                                                        ||
                                                                                                                       ASHEN FIELDS - GRAVEWOOD - DUSKMERE ======================== ++ - THE OSSUARY - [BONE THRONE]
```

**Edge rules.**

- A map has at most **one neighbour per side** (`MapDef.link[4]`). Where
  more than one path leaves a map on the same side, use a gatehouse or cave
  **warp**, not an edge.
- Loop routes that close a cycle (AURORA RIDGE, SCORCHWASTE, GREYWATER FJORD)
  join the graph through **warps** (a cave mouth or a gatehouse) at one end
  at least. The world renderer (`tools/make_media.py clip_world`) lays maps
  out by BFS over edges; a cycle of edges only draws correctly if the
  widths and heights along it add up exactly, and nobody should have to
  guarantee that.

---

## 3. The critical path

Hall order is fixed. The crest ids stay as they are (`travel.c:46`); only the
order the story sends you in changes. Two masters are re-levelled.

| Act | Where | Gate out of the act (see §4) | Hall / Master | Ability won |
| --- | --- | --- | --- | --- |
| I Home | Maple, Meadow, Wood, Lake, Rise | G1: storm calmed | Bout Ring / MARLO (sash); DRAKORA at the Rise | — |
| II East | Brookmill Trail, Brookmill, Copperline, Lumen | G2: VOLT crest | Volt Hall / FARA | LIGHT |
| III West | Heron Fen, Reedwick, Saltwind, Port Brine (optional: Sea Route, Gull Isle) | G3: TIDE crest | Current Hall / MAREN | SURF |
| IV Forge | Cinder Crossing, Railhead, Cinder Road, Cindermoor, Ember Tunnel | G4: ANVIL crest | Anvil Hall / BRONWEN | STRENGTH |
| V North | Stormstep Foothills, Timberline, Frostpine, Frosthollow, Glimmer | G5: RIME crest | Rime Hall / SIGRUN | FLY |
| VI Ash | Hollow Downs, Ashen Fields, Gravewood, Duskmere | G6: LANTERN crest | Lantern Crypt / MORWEN | WARD LANTERN (key item, opens the fog) |
| VII Dream | Mistfen, Moonveil, Dreamspire, Dust Library | G7: 6 crests | Mirror Hall / VESPER | TELEPORT |
| VIII Finale | The Ossuary, Bone Throne | — | OSSUREX | the March heals |
| Post | the legend lairs, loop routes, rematches | — | — | — |

**Why this order.**

- Each ability opens the next act: LIGHT, then SURF, then STRENGTH, then FLY.
  That is the classic backtracking engine.
- The acts swing east, west, east, north, south and north again. Every swing
  passes back through Maple or Lumen, the two hub towns. That is where the
  quests, the caravan and the rematches pay off.
- FLY arrives in Act V, so the last three acts do not become walking chores.

**Shortcuts that open along the way** (their content lives in plans 03–08):

| When | Shortcut | Why it matters |
| --- | --- | --- |
| After Act II | **COPPERLINE TRAM**: the Lumen ↔ Maple tram (a Brookmill town project, plan 10). | Takes the grind out of the Act III trip west. |
| After Act III | **Ferry route**: Port Brine ↔ Gull Isle, plus a SURF back path along the Mirror Lake shore into Willow Acre. | — |
| After Act IV | **One-way ledges** on Cinder Road and the Foothills, dropping back toward the hubs. | Return trips are short. |
| After Act V | **FLY** to every visited town. | The late game doesn't turn into walking chores. |
| After Act VI | **SCORCHWASTE loop**: Duskmere ↔ Cindermoor. | — |
| After Act VII | **AURORA RIDGE loop**: Dreamspire ↔ Frosthollow, and **TELEPORT**. | — |

---

## 4. Gates

Each gate needs four things:

- an in-world reason, told by an NPC or a sign **before** the player hits it;
- a physical form: an NPC blocker, a map patch, a boulder, water, a fog
  barrier or a checkpoint;
- a single opening condition (a flag or a crest);
- a line in `tools/tests/test_progression.c` (plan 02, E6).

| Gate | Where | Form | Opens on | Reason told in-world |
| --- | --- | --- | --- | --- |
| G1 | Bramblewood E, Mirror Lake W, Rise N, Wood S | Road warden NPCs (plan 11) at Wood E and Lake W; the Rise N rockslide (G4) is physical; Wood S stays the existing boulder | `FLAG_STORM_CALMED` | "Nobody leaves the valley while the sky grumbles; the Keeper's orders." |
| G2 | Heron Fen boardwalk (fen east edge) | **Map patch**: planks missing over deep water; carpenters working | `FLAG_VOLT_CREST` (Brookmill carpenters finish on the next visit, or at once if the player already holds it) | "Lumen's lamps went out west; the Fen boardwalk needs Lumen rivets." |
| G3 | Cinder Crossing: the river at Lumen E | **Map patch**: bridge washed out; the river is `A_WATER` | SURF (TIDE crest). After the Anvil crest, a rebuilt bridge patch (town project) makes it walkable. | "The spring flood took the Cinder bridge." |
| G4 | Stormstone Rise N → Foothills | Rockslide: 2–3 `OBJ_BOULDER` (not pumice) in a one-cell corridor | STRENGTH (ANVIL crest) | "The storm's last thunderclap brought the ridge down." |
| G5 | Copperline S → Hollow Downs | **Accord checkpoint** gatehouse (interior warp pair); a warden NPC blocks | `FLAG_RIME_CREST` (4 crests) | "The March is under quarantine; only four-crest wardens may enter." |
| G6 | Lumen N → Mistfen | **Fog barrier** (`OBJ_BARRIER` group or a map patch) plus a signpost | `FLAG_LANTERN_CREST` gives the WARD LANTERN, which parts the fog | "Moonveil mist makes wanderers forget their way home." |
| G7 | Duskmere → the Ossuary | Existing gate warden (`grim/scripts.c:230`) | all 6 crests | exists |

**Post-game gates.** These areas re-scale to Lv44+ and open on
`FLAG_OSSUREX_ANSWERED`, in addition to their existing ability locks:

- Elderwood Heart
- Clockwork Spire
- Whitecrown summit
- Sky Isle legend
- the Drowned Bell legend

Their entrances stay visible from the start and show a *sign* that hints at
them, so they read as promises.

**Rules for gates.**

- **Never soft-lock.** Every gate is closed from one side only, or has an
  exit behind it. `test_puzzles.c` and `test_progression.c` must prove this.
- **Never gate the way home.** A player past a gate can always walk back to
  a Hearth.
- **Only story flags open gates.** Warden-beaten bits never do.

---

## 5. Level curve (targets)

These are wild levels (min–max) and warden team levels. Region owners
re-scale the existing zones to this table. **Bold** rows are new maps.

| Act | Map | Wild Lv | Wardens Lv | Notes |
| --- | --- | --- | --- | --- |
| I | Whisper Meadow | 2–9 | 4–6 | unchanged |
| I | Bramblewood | 4–11 | 7–11 | unchanged |
| I | Mirror Lake | 5–11 | 8–11 | unchanged |
| I | Stormstone Rise | 9–15 | 12–14 | trim max to 15 |
| I | MARLO | — | 12–13 | unchanged |
| II | **Brookmill Trail** | 10–15 | 12–16 | |
| II | **Brookmill** (hamlet) | — | 15–16 (1 exhibition warden) | |
| II | Copperline Road | 14–19 | 15–19 | |
| II | Lumen City | 16–22 | 18–20 | |
| II | FARA (Volt) | — | 21–24 | unchanged |
| III | **Heron Fen** | 17–21 | 18–22 | |
| III | **Reedwick** (hamlet) | 18–22 on the water | 20–21 | |
| III | Saltwind Trail | 19–23 | 20–23 | was 14–19 |
| III | MAREN (Tide) | — | 25–28 | was 23–27 |
| III opt | Sea Route / Gull Isle | 24–30 | 25–28 | unchanged, optional in Act III |
| IV | **Cinder Crossing** | 24–28 (SURF zone 25–29) | 25–28 | |
| IV | **Railhead** (hamlet) | — | 27–28 | |
| IV | Cinder Road | 26–30 | 27–30 | was 24–31 |
| IV | Ember Tunnel | 27–32 | 28–31 | |
| IV | BRONWEN (Anvil) | — | 31–34 | was 32–35 |
| V | **Stormstep Foothills** | 28–32 | 29–32 | |
| V | **Timberline** (hamlet) | — | 31 | |
| V | Frostpine Pass | 30–34 | 31–34 | was 18–24 |
| V | Glimmer Caverns 1 / 2 | 30–34 / 32–36 | 31–35 | was 23–32 |
| V | SIGRUN (Rime) | — | 34–37 | was 33–37 |
| VI | **Hollow Downs** | 33–37 | 34–37 | |
| VI | Ashen Fields | 34–38 | 35–37 | was 24–31 |
| VI | Gravewood | 35–39 | 36–38 | was 27–34 |
| VI | Duskmere (mire) | 36–40 | — | was 28–33 |
| VI | MORWEN (Lantern) | — | 38–41 | was 37–41 |
| VII | **Mistfen** | 37–41 | 38–41 | |
| VII | Moonveil Path | 38–42 | 39–42 | was 30–36 |
| VII | Dreamspire / Dust Library | 39–43 | 40–42 | was 31–36 |
| VII | VESPER (Dream) | — | 42–45 | was 38–41 |
| VIII | Ossuary 1 / 2 | 44–48 / 46–50 | 46–50 | was 39–48 |
| VIII | OSSUREX | — | party max + 3, clamped to 50–70 | unchanged |
| Post | Elderwood, Whitecrown, Clockwork Spire, loops | 44–55 | 48–56 | |

**Balance rules.**

- A player who fights every warden on the critical path once, and meets wild
  kin at a normal rate, arrives at each Master within ±2 levels of the
  Master's lowest kin. Plan 12 checks this with the balance sim.
- Grinding is never required.

**Warden density on a new route:**

- 5–8 wardens per two-segment route.
- At least one double bout.
- At least one warden who is off the main path and guards a satchel.

---

## 6. New maps: names, ids, sizes, owners

These are the ids and display names (names are at most 18 characters). Sizes
are targets; maps can be up to 64x64. The owner is the plan that builds the
map.

| Id | Display name | Size | Tileset | Owner plan | Links |
| --- | --- | --- | --- | --- | --- |
| MAP_BROOKMILL_TRAIL | BROOKMILL TRAIL | 64x36 | WILD | 03 east | W → WOOD (y17–18), E → BROOKMILL |
| MAP_BROOKMILL | BROOKMILL | 40x36 | TOWN | 03 east | W → BROOKMILL_TRAIL, E → COPPERLINE (y17–18) |
| MAP_BROOKMILL_MILL, _HOUSE, _REST | (interiors) | 11–13 wide | INTERIOR | 03 east | warps |
| MAP_COPPER_MINE | COPPERLINE MINE | 36x28 | CAVE, MF_DARK | 03 east | warp from Copperline; LIGHT secret, optional |
| MAP_HERON_FEN | HERON FEN | 64x40 | WILD (+ coast decor) | 04 west | E → LAKE (y31–32), W → REEDWICK |
| MAP_REEDWICK | REEDWICK | 40x32 | COAST | 04 west | E → HERON_FEN, W → SALTWIND (keep Saltwind's east opening y31–32) |
| MAP_REEDWICK_* | (2 interiors) | | INTERIOR | 04 west | warps |
| MAP_CINDER_CROSSING | CINDER CROSSING | 60x36 | VOLCANIC | 05 far | W → LUMEN (y20–21), E → RAILHEAD |
| MAP_RAILHEAD | RAILHEAD | 40x30 | VOLCANIC | 05 far | W → CINDER_CROSSING, E → CINDER_ROAD (y20–21) |
| MAP_RAILHEAD_* | (2 interiors) | | INTERIOR | 05 far | warps |
| MAP_MISTFEN | MISTFEN | 48x60 | DREAM | 05 far | S → LUMEN (x24–25), N → MOONVEIL (x24–25) |
| MAP_PILGRIM_REST | PILGRIM REST | 13x9 | INTERIOR | 05 far | warp from Mistfen |
| MAP_FOOTHILLS | STORMSTEP FOOTHILLS | 40x60 | WILD → SNOW edge (WILD tileset) | 06 north | S → RISE (x11–12), N → TIMBERLINE |
| MAP_TIMBERLINE | TIMBERLINE | 40x36 | SNOW | 06 north | S → FOOTHILLS, N → FROSTPINE (keep Frostpine's south opening) |
| MAP_TIMBER_LODGE, _SAWMILL | (interiors) | | INTERIOR | 06 north | warps |
| MAP_ACCORD_GATE | ACCORD CHECKPOINT | 13x9 | INTERIOR | 07 grim | warp pair: Copperline S door ↔ Hollow Downs N door |
| MAP_HOLLOW_DOWNS | HOLLOW DOWNS | 60x40 | GRIM | 07 grim | reached by the ACCORD_GATE warp (door on its north side); S → ASHEN (keep Ashen's north opening x20–21) |
| MAP_WAYCHAPEL | WAYCHAPEL | 13x10 | CRYPT | 07 grim | warp from Hollow Downs; heals (MF_HEAL) |
| MAP_SCORCHWASTE_1 / _2 | SCORCHWASTE | 48x40 each | VOLCANIC → GRIM | 08 loops | Cindermoor S (edge) → SW_1 → SW_2 → warp into Duskmere (cave mouth) |
| MAP_AURORA_RIDGE_1 / _2 | AURORA RIDGE | 56x36 each | SNOW | 08 loops | Frosthollow E (edge) → AR_1 → AR_2 → warp (cave) → Dreamspire W |
| MAP_GREYWATER_FJORD | GREYWATER FJORD | 40x64 | COAST (+ snow decor) | 08 loops | Port Brine N (edge, SURF) → warp (sea cave) into Frostpine W |

**Small extra maps.** Region plans may add small interiors and single-room
dungeons that hang off their own maps by warps, without changing this
table. Examples: `MAP_REED_TUNNEL` (04), `MAP_RAILHEAD_SHAFT` (05) and
`MAP_BARROW_A` / `_B` (07). Name them `MAP_<REGIONISH>_<THING>` and list them
in the region handoff. Keep the total new map count under about 45
(plan 02, E2).

**Re-linking existing maps.**

- WOOD E and COPPERLINE W now point at the new maps.
- LAKE W and SALTWIND E, LUMEN E and CINDER_ROAD W, LUMEN N and MOONVEIL S,
  RISE N and FROSTPINE S likewise.
- COPPERLINE S no longer links to ASHEN: it becomes a gatehouse door (G5),
  and ASHEN N links to HOLLOW_DOWNS S.
- Each region plan edits the `link[]` fields of its own existing maps.
- The contract above fixes the openings. Keep existing openings where the
  table says so. A new map matches the opening of the map it attaches to.
  `link_off` is allowed but discouraged (`test_field.c` checks landings).

**Hubs.**

- Maple Village and Lumen City are the two hubs. Every act starts or ends in
  one of them.
- Both get a **Hearth notice board** (the Vale Gazette, plan 09), a
  **caravan stop** and a **rematch board**.

---

## 7. Ids, saves and file ownership

**Save-id rules** (read `02_engine_foundation.md` E1 before adding anything):

- Flags, satchels, wardens, quests, lore, maps, puzzle bits and hidden
  passages are all numbered by **position** across the region `.inc` files,
  concatenated in the order village, east, west, north, grim, far, farm,
  craft, fusion, travel, elev, ui, debug.
- Until E1 (stable save ids) lands, adding an id anywhere but at the very
  end breaks every existing save.
- After E1: **append only, inside your own region's files.** Never insert,
  reorder or rename an existing id.

**New region directories:**

| Directory | Owner plan | Holds |
| --- | --- | --- |
| `world/story/` | 11 | Gate blockers, the rival, act transitions, the Keeper's nudges. NPCs in it may stand on any map (`NpcDef.map`). |
| `world/saga/` | 10 | Cross-region quest chains and town projects. |
| `world/links/` | 08 | The loop routes. |
| `world/events/` | 09 | Event NPCs (caravan, festival hosts, gazette boards). |

Add them to the `world/all_*.inc` lists **after `ui` and before `debug`**.
Debug map ids may shift; no real save stores them.

**Each region plan owns:**

- its `world/<region>/` directory;
- its tileset and decor modules;
- its `test_<region>.c`.

It edits no other region's files. Cross-region needs go through this
contract.

**Shared files:**

- Only plan 02 (engine) edits `field.c`, `script.c`, `travel.c`, `time.c`,
  `quest.c`, `save_game.h` and `world.h`.
- Only plan 09 (events) edits the new `events.c`.
- A region plan that needs an engine change asks plan 02. It does not patch
  the engine itself.

---

## 8. What makes a good route (every region plan follows this)

A route in this game has:

1. **A shape.** Not a straight corridor: at least one fork (the short way
   past wardens vs. a long way through grass) and at least one loop back.
   Use the elevation layer: ledges for one-way shortcuts, stairs, and one
   bridge you walk over and under.
2. **A landmark** you can name from the town map: a mill wheel, a heron
   rookery, a lava fall, a signal tower.
3. **Two or more wild zones** with different mixes, split by terrain (grass,
   reeds, water, cave mouth) or by time (day and night slots). Use at least
   one uncommon kin not found elsewhere in that act.
4. **Wardens with a theme**, placed on sight lines you can see coming, plus
   a double bout and one warden who guards a satchel.
5. **A mid-route stop.** A hamlet (a heal spot, a shop with a regional
   specialty, 1–2 side quests), a rest house or a camp.
6. **Satchels**:
   - 3 visible;
   - 2 hidden (examine a spot);
   - 1 that needs a later ability (see §9).
7. **Lore**: 2–4 Lorebook entries from people or signs on the route.
8. **A berry patch or forage spot** (`OBJ_BERRY`), so routes feed the farm
   and crafting loop.
9. **A hook for events** (plan 09): a spot where the caravan camps, an
   outbreak grass patch, or a weather-front map flag.
10. **Tests**:
    - reachable (`test_field.c`);
    - under the tile and NPC budgets;
    - the progression solver passes;
    - every map has a song.

---

## 9. The ability-secret register (the backtracking promise)

Every early map gets at least one spot that a later ability opens. The plan
that owns the map builds it; plan 10 lists them all in the quest log's
**FIELD NOTES** and ties some into quests.

| Ability (act won) | Where it pays back (at least) |
| --- | --- |
| LIGHT (II) | Copperline Mine (dark, Mine Boss rematch); the Bramblewood hollow log; the Heron Fen reed tunnel |
| SURF (III) | Mirror Lake islet (satchel + rare); the Brookmill millpond; the Willow Acre creek back path; Cinder Crossing (critical) |
| STRENGTH (IV) | The Whisper Meadow boulder cave; the Saltwind cliff cache; Elderwood (post); Railhead collapsed shaft |
| FLY (V) | Sky Isle (post); the Stormstone high ledge (DRAKORA shrine, post-game rematch); rooftop satchels in Lumen |
| WARD LANTERN (VI) | Mistfen (critical); the fog pockets in Bramblewood and Gravewood |
| TELEPORT (VII) | Mirror-pad secrets in Dreamspire; a return pad in the Ossuary |

---

## 10. Playtime targets

These are targets for a first run, not measurements. Plan 12 measures them.

| Segment | Today (estimate) | Target |
| --- | --- | --- |
| Act I | 1.5 h | 2 h (the storm gate keeps it together) |
| Each of Acts II–VII | ~1 h | 2–2.5 h (route, hamlet, town, Hall, side quests) |
| Finale | 0.5 h | 1 h |
| Critical path | ~8 h | 16–18 h |
| With side quests, events and the post-game | — | 30 h+ |

## 11. Implemented underground connections

The cave expansion preserves G1–G7 and adds the following optional loops;
[UNDERWORLD.md](../UNDERWORLD.md) is the current authoring/entrance reference.

| Earliest act | New maps / connections | Requirement |
| --- | --- | --- |
| III | Rootwood Path, Rootways, Mill Cellar; Bramblewood ↔ Brookmill Mill ↔ Copperline Mine | Volt Crest on both ends |
| IV | Tidal Underflow; Reed Tunnel ↔ Reedwick / Port Brine; Rootways ↔ Underflow | Tide Crest; flooded channel still needs SURF |
| V | Karst Chamber and Frost Spur; Stormstep ↔ Glimmer / Timberline sawmill | Anvil Crest; frost stopper needs STRENGTH |
| V | Ember Span and Cooling Chamber; Railhead shaft ↔ Ember Tunnel; Copperline Mine ↔ shaft | Anvil Crest; permanent cooling puzzle |
| VI | Root Gallery and Dusk Vault; Chalk Barrow ↔ Gravewood / Duskmere | Rime Crest; optional symbol shortcut |
| VII | Cooling Chamber ↔ Root Gallery | Lantern Crest |

No underground route enters a Hall behind its Master or bypasses the
six-crest Ossuary gate. New IDs append within their regions; saved regional
layouts rebase shifted global IDs. Do not move existing IDs to make numeric
values appear unchanged. Old-save migration and per-entrance return proofs
are acceptance requirements for every further connection.
