# 05 — Far: Cinder Crossing, Railhead, Cindermoor (Act IV) and Mistfen, Moonveil, Dreamspire (Act VII)

**Work package:** REGION-FAR.

**Needs:** plan 02 merged (E1, E3, E5, E8).

**Owns:**

- `src/game/world/far/`
- `tools/tilesets/ts_volcanic.py`, `ts_dream.py`
- `tools/decor_far.py`, `terrain_far.py`, `far_buildings.py`
- `tools/tests/test_far.c`

**Contract:** `01_progression_contract.md`: §3 Acts IV and VII, §4 G3 and G6,
§5, §6, §8, §9.

**Don't touch:**

- Lumen's map data (plan 03). You set only the far side of the Lumen E and
  N edges, and plan 03 re-points Lumen's `link[]`.
  - Lumen E → `MAP_CINDER_CROSSING`, y20–21 (unchanged).
  - Lumen N → `MAP_MISTFEN`, x24–25 (unchanged).
  - Put these two one-line changes in plan 03's scope. If plan 03 has
    already merged, make the edit yourself and say so in the handoff.

This plan covers two acts because both live in `world/far/`. The work
splits cleanly into **part A** (volcanic) and **part B** (dream). One agent
can do both in sequence, or two agents can share the directory if part B
only *appends* to the `.inc` files after part A merges.

---

# Part A — Act IV, the forge road

## A1. Act IV in one paragraph

The spring flood took the **Cinder bridge** east of Lumen (gate G3). With
SURF from Port Brine you cross the river, then pass through:

1. **Cinder Crossing**, a basalt canyon with hot springs;
2. **Railhead**, a miners' camp at the end of the ore railway;
3. the old **Cinder Road** over the lava fields;
4. **Cindermoor** and the Anvil Hall, where STRENGTH is won.

Railhead's foreman, and a town project (plan 10), later rebuild the bridge,
so the forge road becomes a walking road again.

## A2. CINDER CROSSING (new, `MAP_CINDER_CROSSING`, 60x36, TS_VOLCANIC)

**Edges:**

- W → LUMEN at y20–21.
- E → RAILHEAD at y20–21.

**Gate G3:**

- A **river** runs north–south at x6–9: `A_WATER`, surfable.
- The bridge is a map patch. With `FLAG_PROJECT_CINDER_BRIDGE` clear, the
  deck is shown washed out, with broken piles as decor. With it set, the
  deck is a whole BRIDGE_H.
- The west bank (x0–5) is a small ledge with a sign: "CINDER BRIDGE — OUT.
  SURF OR WAIT FOR REPAIR". The river zone is visible from Lumen as a
  teaser.
- **Test:** without SURF and without the project flag, nothing east of x9
  is reachable.

**Shape:**

- A **basalt canyon** with columnar cliffs (elevation levels 0–2).
- The **hot spring terraces** are the landmark. Terraces step down with
  animated steam, and an NPC bather gives lore on the water heat that kin
  pump.
- A fork:
  - the upper rim path (wardens);
  - the canyon floor (grass zone, plus a **one-way ledge** back west: an
    Act IV return shortcut, contract §3).

**Wild zones:**

CROSSING (Lv24–28):

| Kin | When | Weight |
| --- | --- | --- |
| SALAMBER | any | 20 |
| STINGLET | any | 15 |
| FULGECKO | any | 10 |
| MAGNITICK | any | 15 |
| RAMBLET | any | 15 |
| CINDERUB | day | 10 |
| SCORCHION | night | 5 |

CROSSING_WATER (surf, Lv25–29): PEBBOTTER, TORRENTTER and KOIRIN (3%).

**Contents:**

- **Wardens** (6):
  - a surveyor;
  - two spa-goers (a double bout);
  - a rail worker;
  - a geologist;
  - a guard on the upper rim satchel.
- **Satchels:** 3 visible and 2 hidden.

## A3. RAILHEAD (new hamlet, `MAP_RAILHEAD`, 40x30, TS_VOLCANIC)

**Edges:**

- W → CINDER_CROSSING at y20–21.
- E → CINDER_ROAD at y20–21. Cinder Road's existing west opening stays.

**Feel:**

- The end of the ore railway: an ore-cart turntable (decor), tents, a
  cookhouse and a small **Hearth** (fly point).
- **Interiors:** `MAP_RAILHEAD_BUNK` (the Hearth and bunks) and
  `MAP_RAILHEAD_OFFICE` (the foreman).

**People:**

- **FOREMAN GRETA.**
  - Talks about the washed-out bridge.
  - After the ANVIL crest, starts the **CINDER BRIDGE** town project with
    plan 10, which owns the project state. You place Greta and a script
    that calls `saga_project_offer(PROJ_CINDER_BRIDGE)`, the API plan 10
    exposes. If plan 10 isn't merged, stub it.
- **The cook.** Regional dish: CHILI POT ingredients on sale.
- **A collapsed shaft** (§9 STRENGTH): a boulder-sealed mine door. Behind
  it is `MAP_RAILHEAD_SHAFT` (small, dark), holding a FOUNDRAKE static
  encounter (Lv32) and IRON ORE.
- **A rail enthusiast kid.** Lore on the ore railway.

**Wardens:** 1–2 (27–28).

## A4. Cinder Road, Ember Tunnel, Cindermoor (existing)

**Re-level** (contract §5):

| Area | Wild | Wardens |
| --- | --- | --- |
| Cinder Road | 26–30 | 27–30 |
| Ember Tunnel | 27–32 | 28–31 |
| BRONWEN | — | 31–34 |
| Anvil Hall | — | 29–31 |

**Cinder Road:**

- Add a **one-way ledge** drop back to Railhead.
- Add one berry patch (EMBERBERRY).

**Cindermoor:**

- **South edge** (for plan 08): Cindermoor S → `MAP_SCORCHWASTE_1`. Build a
  2-cell opening, agree the x with plan 08, and link it.
- **Hook:** a scorch-wind barrier on the Cindermoor side, gated so the loop
  stays closed until Act VI. Use a map patch on `FLAG_LANTERN_CREST`,
  inverted: a heat-haze vent wall. Plan 08 explains why.

**Caldera (CALDERON):** stays behind STRENGTH. Add the post-game gate only if
plan 12's balance run says CALDERON is too easy to reach early. Default:
**no** extra gate. A legend in mid-game is fine.

---

# Part B — Act VII, the dream road

## B1. Act VII in one paragraph

North of Lumen lies a mist that makes wanderers forget their way home (gate
G6). Morwen's LANTERN crest comes with a **WARD LANTERN**; plan 07 gives the
item. Its steady light parts the fog:

1. **Mistfen**, a drowned moor of standing stones and fog pockets;
2. the **Pilgrim Rest** inn;
3. **Moonveil Path**;
4. **Dreamspire**, where Vesper's Mirror Hall gives TELEPORT.

## B2. MISTFEN (new, `MAP_MISTFEN`, 48x60, TS_DREAM)

**Edges:**

- S → LUMEN at x24–25.
- N → MOONVEIL at x24–25. Moonveil's existing south opening stays.

**Gate G6:**

- A **fog wall** runs across the south end (rows 52–54), as a map patch
  `{flag: FLAG_LANTERN_CREST, invert: 1}`. The cells are solid fog decor,
  with the fog animation from `ts_dream`.
- South of the wall, rows 55–59 are a teaser strip with a sign and a
  lost-pilgrim NPC.
- With the flag set, the wall becomes a path lit by lantern posts.

**Fog mechanic** (optional, recommended; uses E3 and E5, no new engine):

- **Fog pockets** are small regions that are hidden passages
  (`EF_HIDDEN`), or map patches revealed by stepping on a **lantern post**
  switch.
- Use the existing SWITCH/BARRIER objects: a switch lights a post, and the
  post opens a BARRIER group of fog.
- **Design the route as a light-the-posts puzzle,** 3 posts, where lighting
  a post reveals the next stretch of path. Keep it simple, and prove it
  with `test_puzzles.c`: no soft-locks.
- Barrier groups reset on map load (`travel.c`), so the puzzle must be
  solvable from either side.

**Shape:**

- Standing stones, the drowned causeway (bridges) and will-o'-wisp lights
  (decor anim).
- **The landmark:** the **Weeping Stone**, a menhir in a pool.
- **Pilgrim Rest** (`MAP_PILGRIM_REST`, interior, **MF_HEAL**): an innkeeper
  with lore, plus a quest hook for plan 10's LEGEND TRAIL.

**Wild zone** MISTFEN (Lv37–41):

| Kin | When | Weight |
| --- | --- | --- |
| MANDRAGOR | any | 15 |
| DOZLOTH | day | 15 |
| LUMOTH | night | 15 |
| WISPIRE | night | 10 |
| BOGSHAMBLE | any | 10 |
| MUDDLE | any | 15 |
| WICKLET | night | 5 (rare) |
| SOMNISLOTH | any | 5 |

**Wardens** (6): pilgrims, a lost scholar, and a double bout of dream
twins, all at 38–41.

**Satchels and secrets:**

- 3 visible and 2 hidden satchels.
- A §9 TELEPORT mirror-pad secret. It is useful post-Act VII: a pad pair
  back from Dreamspire to the Weeping Stone.

## B3. Moonveil, Dreamspire, Mirror Hall, Dust Library (existing)

**Re-level** (contract §5):

| Area | Wild | Wardens |
| --- | --- | --- |
| Moonveil | 38–42 | 39–42 |
| Dreamspire / Library | 39–43 | 40–42 |
| VESPER | — | 42–45 |
| Mirror Hall | — | 40–42 |

**Dreamspire west edge** (for plan 08): AURORA RIDGE arrives by a **cave
warp**, not an edge.

- Place a cave-mouth door on Dreamspire's west cliff and a warp to
  `MAP_AURORA_RIDGE_2`'s east cave; plan 08 builds the other side.
- Gate it with `FLAG_CREST_DREAM` from the Dreamspire side. Plan 08 also
  gates it from the ridge side.

**Dust Library (SCRIPTORA):** post-game gate (`FLAG_OSSUREX_ANSWERED`),
unless plan 12 says otherwise.

---

## Tests (`test_far.c`, extend)

**G3:**

- Without SURF and without the project flag, Railhead is unreachable.
- With SURF, it is reachable.
- With the project flag, it is reachable on foot.

**G6:**

- Moonveil is unreachable from Lumen until `FLAG_LANTERN_CREST` is set.
- The fog-post puzzle is proven by `test_puzzles.c`.

**Budgets:** hold with every patch on and off.

**Milestones:**

- BRONWEN → `FLAG_CREST_ANVIL`;
- VESPER → `FLAG_CREST_DREAM`;
- Greta offering the bridge project.

**Handoff.** Update `docs/handoff/far.md` with a Routes section for both acts.
