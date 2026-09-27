# 08 — Loop routes: Scorchwaste, Aurora Ridge, Greywater Fjord

**Work package:** LINKS.

**Needs:**

- plan 02 merged;
- plans 04, 05, 06 and 07 merged, or at least their door and edge stubs
  agreed. You build the maps between their doors.

**Owns:**

- the new region directory `src/game/world/links/`. Register it in every
  `world/all_*.inc` **after `ui` and before `debug`**; see contract §7.
- `tools/tests/test_links.c`

Tilesets are reused (volcanic, grim, snow, coast); you add no new tileset.
Add decor only in a new `tools/decor_links.py`, if you need any.

**Contract:** `01_progression_contract.md`: §2 (why loops join by warps), §3
shortcuts, §5 post levels, §6.

---

## 1. Why loops

A long linear path gets tedious on the way back. Loops give:

- **shortcuts** that open *after* you have walked the long way once;
- **optional high-level content** between acts and in the post-game:
  wardens at 40–48, rare kin, legend hints;
- a map that feels like a **web**, not a tree.

The rule that makes loops safe:

- Every loop joins the graph by a **warp at one end** (a cave mouth or a
  gatehouse), so the world renderer's edge BFS never has to close a cycle.
- Each end is **gated from both sides** by a flag the player can only get
  at the right act. That way a loop never becomes a way to skip a gate.

---

## 2. SCORCHWASTE (`MAP_SCORCHWASTE_1`, `MAP_SCORCHWASTE_2`, 48x40 each)

**Joins** Cindermoor (Act IV) and Duskmere (Act VI).

**Opens:**

- From the Cindermoor side: a heat-vent wall, a map patch owned by plan 05,
  that opens on `FLAG_LANTERN_CREST`.
- From the Duskmere side: a rockfall, STRENGTH boulders owned by plan 07.

Together these mean the loop never lets you into the March before G5.

**Links:**

- CINDERMOOR S → SW_1 N (an edge; x agreed with plan 05).
- SW_1 S → SW_2 N (an edge).
- SW_2's west cave door → Duskmere's east cave (a warp; coordinates agreed
  with plan 07).

**Feel:**

- SW_1 is TS_VOLCANIC: cooling lava flats and obsidian spires.
- SW_2 is TS_GRIM: the lava gives way to ash.
- The transition is a fade (tileset change); dress the maps so it reads as
  a gradient.

**Shape:**

- **Obsidian maze** lanes on SW_1.
- **A cooling lava-crust puzzle:**
  - crust cells are ice-like (`A_ICE`) and slide you until you hit a rock;
  - reuse the ice mechanic with lava-crust art;
  - prove it with `test_puzzles.c`.
- **Landmark:** the **Glass Dunes**, black obsidian sand in dunes.

**Wild** (Lv40–44):

- SCORCHION, FORTADILLO, LODEHORN, FOUNDRAKE, REAPMANTIS, CAWDAVER and
  METEORB (night, 3%).
- A special night slot: **HOPSHI** (2%).

**Contents:**

- **Wardens** (6, Lv41–44): ash prospectors, a volcanologist and a pair of
  Accord rangers.
- **Satchels:** 4, plus one PRISM LANTERN cache.
- **A legend hint:** a lore stone about CALDERON and OSSUREX as "two fires
  under one land".

---

## 3. AURORA RIDGE (`MAP_AURORA_RIDGE_1`, `_2`, 56x36 each, TS_SNOW)

**Joins** Frosthollow (Act V) and Dreamspire (Act VII).

**Opens:**

- From the Frosthollow side: an ice wall (plan 06), thawing on
  `FLAG_RIME_CREST`.
- From the Dreamspire side: a cave door (plan 05), open on
  `FLAG_CREST_DREAM`.
- **Inside the loop**, place a **one-way** barrier near the Dreamspire end:
  a frozen waterfall ledge (an elevation ledge), so from the Frosthollow
  side you can reach the ridge but **cannot drop into Dreamspire before G6**.
  - Also put a second, flag-gated barrier (a map patch on
    `FLAG_LANTERN_CREST`) at the cave end.
  - Prove it in the progression solver: Dreamspire must not be reachable
    via the ridge before `FLAG_LANTERN_CREST`.

**Links:**

- FROSTHOLLOW E → AR_1 W (an edge; y agreed with plan 06).
- AR_1 E → AR_2 W (an edge).
- AR_2's east cave door → Dreamspire's west cave (a warp; agreed with plan
  05).

**Feel:** a knife-edge ridge above the clouds, with an **aurora** at night.
Plan 09 adds the `WX_AURORA` event that tints the sky and raises the
ASTRAL slots.

**Shape:**

- A narrow crest path on elevation level 3, with drops to level 1 snowfields
  on either side.
- Ice slides between snowfields.
- **Landmark:** the **Star Cairn**, a stargazers' cairn where the STAR
  CHART quest line (plan 10) ends.

**Wild** (Lv40–45):

| Kin | When | Weight |
| --- | --- | --- |
| MOONHARE | any | — |
| GLACIYAK | any | — |
| CRAGHORN | any | — |
| TENGALE | day | 3% |
| WENDIGAUNT | night | 3% |
| METEORB | night | — |
| QILUMEN | night, aurora only | 1% (via plan 09) |

**Contents:**

- **Wardens** (6, Lv42–45): stargazers, mountaineers, and a skiing double
  bout.
- **Satchels:** 4, plus an ASTRAL SHARD.

---

## 4. GREYWATER FJORD (`MAP_GREYWATER_FJORD`, 40x64, TS_COAST)

**Joins** Port Brine (Act III) and Frostpine Pass (Act V).

**Opens:**

- From the Port Brine side: SURF only (the harbour-mouth opening, plan 04).
- From the Frostpine side: a sea-cave door (plan 06).

**Prevent skipping G4** (Stormstep rockslide, STRENGTH): with SURF alone
(Act III) the fjord could take you to Frostpine early. So:

- the sea-cave into Frostpine sits behind a **STRENGTH boulder** on the
  fjord side, **or**
- the fjord's north end is a waterfall (an elevation ledge) you can only
  *descend*, i.e. from Frostpine toward Port Brine.

**Use both.** Prove it with the progression solver: Frostpine must stay
unreachable before `FLAG_CREST_ANVIL`.

**Links:**

- PORT_BRINE N → FJORD S (an edge; water cells; x agreed with plan 04).
- FJORD's north sea-cave door → Frostpine's west cave (a warp; agreed with
  plan 06).

**Feel:** steep grey cliffs, floating ice, seals on rocks, and a **drowned
village** on the bottom (visible as decor through shallows). Rain and fog
are common: plan 09 gives it high odds of WX_FOG.

**Wild:**

- Surf zone (Lv36–42): MEDUSHOCK, ABYSSLURE (night), EMPERICE, TUXFLAKE,
  KELPYRE (night, 2%) and NOCTHALE's song.
  - NOCTHALE's song is a lore hint for the Drowned Bell, not an encounter.
- A few islets carry grass zones.

**Contents:**

- **Wardens** (5, Lv38–42), placed on islets: sailors and ice fishers.
- **Satchels:** 3, plus a sunken chest (a CHEST object on an islet).

---

## 5. Tests (`test_links.c`)

- All maps load, and the links and warps are two-way.
- The maps are within budget and reachable in the "all flags" state.
- **Progression solver assertions** (add rows to E6's act table, via
  `links/milestones.inc` or the act table):
  - Scorchwaste is unreachable before `FLAG_LANTERN_CREST` from Cindermoor.
    From Duskmere it needs STRENGTH, which comes earlier, but Duskmere
    itself needs G5.
  - Dreamspire is unreachable via Aurora Ridge before `FLAG_LANTERN_CREST`.
  - Frostpine is unreachable via the fjord before `FLAG_CREST_ANVIL`.
- `test_puzzles.c` covers the lava-crust slide and the ridge ice.
- The world render (plan 02 E8) shows all three loops, using the
  `WORLD_POS` hints.

**Handoff.** Write a new `docs/handoff/links.md`.
