# 03 — East: Brookmill Trail, Brookmill, Copperline, Lumen (Act II)

**Work package:** REGION-EAST.

**Needs:** plan 02 merged (E1 stable ids, E3 NPC conditions, E5 map
patches, E8 templates).

**Owns:**

- `src/game/world/east/`
- `tools/tilesets/ts_city.py`, `tools/decor_east.py`
- `tools/tests/test_east.c`

**Contract:** `01_progression_contract.md`: §3 Act II, §5 levels, §6 map
ids, §8 the route checklist, §9 the secret register.

**Don't touch:**

- other regions' files;
- engine files (ask plan 02);
- gate blockers (plan 11 places the G1 road warden on Bramblewood's east
  exit).

---

## 1. Act II in one paragraph

Now that the storm is calmed, the road east opens:

1. **Brookmill Trail** follows the Brook out of Bramblewood, past a heron
   rookery and a ruined toll bridge.
2. The trail ends at **Brookmill**, a watermill hamlet whose carpenters'
   guild builds things for the whole Vale. It is the source of later
   **town projects** (plan 10).
3. **Copperline Road** climbs past the copper workings (now with a real
   **mine**) to the gates of **Lumen**, where Fara's Volt Hall waits.
4. Brookmill's carpenters need Lumen rivets for the Heron Fen boardwalk.
   The Volt crest earns them, which opens Act III (gate G2, built in plan
   04).

---

## 2. BROOKMILL TRAIL (new, `MAP_BROOKMILL_TRAIL`, 64x36, TS_WILD)

**Edges:**

- W → WOOD at y17–18 (Bramblewood's existing east opening).
- E → BROOKMILL at y17–18.
- `link_off` 0.

**Shape.** Split the 64 columns into three stretches:

| Stretch | Columns | Content |
| --- | --- | --- |
| West | 0–20 | **Brook meadow**. The path follows the Brook's north bank. Tall grass on both sides. A one-way ledge row drops back toward the west entrance: a shortcut home for later trips. |
| Middle | 21–42 | **The old toll bridge.** The main path crosses the Brook on a BRIDGE_H (elevation feature): you walk over it on level 1, and a towpath runs under it on level 0. The towpath leads to a hidden satchel and the **heron rookery**, a stand of dead trees with nests: the landmark. Two wardens watch the bridge approach. |
| East | 43–63 | **Orchard edge.** Wild apple trees (decor) and a **berry patch** (`OBJ_BERRY`, GLOWBERRY). A fork: the short way north past a double bout, or the long way south through reeds (a second wild zone). |

**Wild zones.**

BROOK_TRAIL (grass, Lv10–15):

| Kin | When | Weight |
| --- | --- | --- |
| PRICKLET | any | 20 |
| SNUFFLET | day | 15 |
| HUMBEE | day | 15 |
| FLYSQUIRL | day | 10 |
| RADISHOO | any | 15 |
| SCYTHLING | day | 10 |
| BLINKET | night | 15 |
| RACCOIN | night | 10 |
| QUILLDRUM | any | 4 (uncommon) |

BROOK_REEDS (reeds, south fork, Lv12–15):

| Kin | When | Weight |
| --- | --- | --- |
| PEBBOTTER | any | 25 |
| BUBBLIN | any | 20 |
| MOSSHELL | any | 20 |
| WEBBIT | night | 15 |
| KOIRIN | any | 2 (rare: the waterfall-climbing koi; a hint for the millpond) |

**Wardens** (6):

- ANGLER BESS (12–13), at the west ledge.
- The bridge pair: TWINS OAK & ASH, a double bout (13–14).
- BEEKEEPER TAM (14), in the orchard; guards a satchel with a HONEY DROP.
- HIKER ROLF (15), on the reed fork.
- **The rival's first road bout** is on the east end (plan 11 places it).

**Satchels:**

- Visible: GLOW TONIC, LANTERN x3, BLOOM SHARD.
- Hidden: an OLD COIN in the rookery, a SUNSEED behind the toll booth.
- **Secret** (§9): a hollow under the toll bridge that is too dark to
  search. With **LIGHT** it holds a PRISM LANTERN x3 and lore.

**Lore** (3):

- the toll bridge's history (the Brook was the Vale's first trade road);
- herons and kin (why PEBBOTTER juggle stones);
- a signpost with a Brookmill advert.

**Event hooks** (for plan 09):

- A caravan camp spot at the orchard clearing: a 4x3 open area. Mark it
  `EVENT_SPOT(CARAVAN, x, y)` once plan 09 defines the macro; until then,
  leave a comment.
- An outbreak patch in the reeds.

---

## 3. BROOKMILL (new hamlet, `MAP_BROOKMILL`, 40x36, TS_TOWN)

**Edges:**

- W → BROOKMILL_TRAIL at y17–18.
- E → COPPERLINE at y17–18 (Copperline's existing west opening).

**Feel.** A millpond village on two levels:

- The **mill wheel** is animated (a tileset anim) and sits on the Brook at
  the centre; the millpond above it is level 1 and the village lanes are
  level 0.
- A **carpenters' guild yard** holds stacked timber, half-built carts and
  a boat frame. It is where the Vale's projects are built (plan 10).
- **Buildings:**
  - a small **Hearth** (MF_HEAL, fly point);
  - a guild hall (the interior `MAP_BROOKMILL_MILL` doubles as the mill
    and the guild);
  - two houses (`MAP_BROOKMILL_HOUSE`, `MAP_BROOKMILL_REST`, the rest
    house).
- **Shop:** the Hearth counter sells basic supplies, plus a **regional
  specialty**: MILL FLOUR (a new cooking material, if crafting agrees;
  otherwise HONEY DROP).

**People** (≤ 24 people, ≤ 7 sprites; test it):

- **GUILDMASTER HOLT.** Asks you to bring Lumen rivets. The item is RIVET
  BUNDLE, given by Tinker Vex in Lumen once you hold the Volt crest.
  Handing it over sets `FLAG_FEN_RIVETS`. Plan 04 applies the Heron Fen
  boardwalk patch on `FLAG_FEN_RIVETS || FLAG_VOLT_CREST`. Also give
  Holt's line a fallback: with the Volt crest already held, talking to
  him sets the flag directly.
- **The miller.**
  - Lore on water power and why TIDE kin keep mills turning.
  - A side quest, **GRIST FOR THE WHEEL**: bring 3 CORN (farm) or 3 IRON
    ORE for a new cog, for a reward. Put it in the east `quests.inc`.
- **A kid who wants to see a KOIRIN.** Show them one (party check) for a
  LURE INCENSE. A backtracking hint.
- **A night-only fiddler** (E3 `when` = NIGHT) who plays by the pond. Lore
  on the song of the Brook.
- **An exhibition warden** at the guild yard (15–16). Re-battle daily after
  plan 09's rematch board exists.

**Secrets:**

- **SURF** the millpond: an islet with a KOIRIN static encounter (Lv18) and
  a satchel (TIDE LANTERN).
- **Town project hook** (plan 10): the **tram depot**. An empty lot at the
  east end is a map patch that becomes the COPPERLINE TRAM stop once the
  project is done.

---

## 4. COPPERLINE ROAD (existing, rework)

**Edges:**

- W → BROOKMILL (was WOOD).
- E → LUMEN (unchanged).
- S: **no longer an edge.** Replace the south opening at x20–21 with the
  **ACCORD CHECKPOINT** gatehouse door (contract G5). Plan 07 builds the
  interior and the Hollow Downs side. You build the door and the warp to
  `MAP_ACCORD_GATE`. Agree the door cell with plan 07; use (20,35) unless
  the art needs otherwise.

**Changes:**

- **Re-level** the COPPERLINE zone to 14–19 (was 13–20) and the wardens to
  15–19.
- **Add COPPERLINE MINE** (`MAP_COPPER_MINE`, 36x28, TS_CAVE, MF_DARK),
  through a mine-mouth warp on the road:
  - one floor, with rails and carts as decor;
  - a zone of DIGGET, QUARTZLING, SQUEAKLE, MAGNITICK and STATICKO,
    Lv15–19;
  - the **Mine Boss** warden (19) at the back;
  - a satchel of IRON ORE x2.
  - It is dark but passable, so it is optional in Act II. **LIGHT** reveals
    a side gallery with a METAL SHARD and a lore tablet on the copper
    rush.
- **A tram line under construction.** Rails end at a buffer stop by the
  Lumen gate. The COPPERLINE TRAM project (plan 10) adds the tram NPC and
  the finished rails (a map patch). Leave the space for it.
- **One berry patch** (EMBERBERRY), plus a caravan camp spot.

---

## 5. LUMEN CITY (existing hub; add depth)

Lumen is hub #2. Add these, and keep the tile and NPC budgets:

- **Tinker Vex gives the RIVET BUNDLE** after the Volt crest. This is a new
  key item in `items/east.inc`, appended.
- **Telegraph office.** Reuse `MAP_LUMEN_HOUSE_B`, or add a new interior.
  It is where the **Vale Gazette** is printed. Plan 09 puts the daily board
  here and in Maple; you provide the room and one clerk NPC.
- **Night market.** A market-square layout that plan 09 fills on market
  nights (event NPCs). Reserve four stall cells with decor that reads as
  closed during the day.
- **Rooftop satchels.** Two, reachable only by **FLY** landing on the
  clock-tower plaza: add a fly point there, or an elevated level that only
  a FLY-drop reaches. These are §9 FLY secrets.
- **District NPC schedules** (E3 `when`):
  - market traders by day;
  - lamplighters at dusk;
  - a night watch that tells you about rare night kin.
- **North gate.** Lumen N → MISTFEN. Plan 05 builds Mistfen and the fog
  barrier, which sits on the Mistfen side. On your side, add a
  **signpost** and a **worried pilgrim** NPC who explains the mist
  (contract G6).

---

## 6. Post-game re-scale

Both areas below open on `FLAG_OSSUREX_ANSWERED`, in addition to the
existing boulder (contract §4 post-game gates). Use an elder NPC (E3
`hide_flag`) or a map patch of thorns, with a sign that hints at it from
Act I.

**ELDERWOOD HEART:**

- Zone to 44–50, wardens to 48–52.
- It keeps its STRENGTH boulder.

**CLOCKWORK SPIRE:**

- Its warden goes to 50–52.
- It stays behind STRENGTH plus the post-game flag.

---

## 7. Tests (`test_east.c`, extend)

- The new maps load, the links are two-way, and they are reachable.
- Tile and NPC budgets hold with **every** E3 condition on.
- The Heron Fen boardwalk patch flag is set by exactly one script path
  (either `FLAG_VOLT_CREST` or Holt).
- The mine is dark and passable without LIGHT; the side gallery needs
  LIGHT.
- **Milestones** (`world/east/milestones.inc`, for E6):
  - FARA → `FLAG_VOLT_CREST`;
  - HOLT → `FLAG_FEN_RIVETS`.
- Update the region header comment in `east/data.h` with the new edge
  contracts.

**Handoff.** Update `docs/handoff/east.md` with a "Routes" section:

- maps, zones, wardens, secrets, event spots;
- screenshots from `build/shot`.
