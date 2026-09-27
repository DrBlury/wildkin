# 04 — West: Heron Fen, Reedwick, Saltwind, Port Brine (Act III)

**Work package:** REGION-WEST.

**Needs:** plan 02 merged (E1, E3, E5, E8).

**Owns:**

- `src/game/world/west/`
- `tools/tilesets/ts_coast.py`, `ts_tide.py`, `tools/decor_west.py`
- `tools/tests/test_west.c`

**Contract:** `01_progression_contract.md`: §3 Act III, §4 G2, §5, §6, §8,
§9.

**Don't touch:**

- Mirror Lake's map data (core/village): ask the village owner, or plan 11,
  which owns the gate NPC at Lake W. You set `link[]` on your side only.
  The LAKE W link change is a single line in `village/maps.inc`: `MAP_LAKE`
  W → `MAP_HERON_FEN`. The village area has no plan of its own, so **you
  make that one-line edit** and note it in your handoff.
- Engine files.

---

## 1. Act III in one paragraph

With the Volt crest and the Brookmill rivets, the **Heron Fen boardwalk** is
finished (gate G2):

1. The road west from Mirror Lake crosses a wide reed fen on stilted
   boardwalks.
2. It passes **Reedwick**, a stilt village of reed-cutters and eel-smokers.
3. Then comes **Saltwind Trail** with its salt pans and bluffs, and finally
   **Port Brine**, where Maren's Current Hall gives SURF.

Port Brine's harbour offers the ferry to Gull Isle (optional in Act III),
and SURF opens Cinder Crossing for Act IV.

---

## 2. HERON FEN (new, `MAP_HERON_FEN`, 64x40)

**Tileset.** Use TS_WILD with coast decor, or TS_COAST if the fen needs
water autotile variety. Check the scene-tile budget: coast is heavy (see
`docs/handoff/towns_west.md` on the 768-tile budget).

**Edges:**

- E → LAKE at y31–32 (Mirror Lake's existing west opening).
- W → REEDWICK at y19–20.
- `link_off` 0.

**Gate G2** (map patch, E5):

- The boardwalk's middle span, 4 cells over `A_DEEP` water at about
  x28–31, is **missing planks**. Two carpenters stand there (E3 `hide_flag`
  = `FLAG_FEN_RIVETS`), with one sign: "BOARDWALK CLOSED — AWAITING LUMEN
  RIVETS".
- The patch `{flag: FLAG_FEN_RIVETS, invert: 1}` draws the gap.
- After the flag is set the gap is gone, and the carpenters are replaced by
  one who says thanks. That NPC uses `show_flag`.
- **Never soft-lock.** The gap sits between the east entrance and
  everything west. The east part of the fen (zone, warden, satchel) stays
  reachable in Act II as a teaser.

**Shape:**

- **Boardwalks** on level 1 (elevation) over reeds and shallows on level 0.
  At least one BRIDGE_H lets a level-0 reed channel pass under the
  boardwalk.
- **The heron rookery island** is the landmark: dead trees, nests and a
  tall heron statue.
- **The reed tunnel** is a §9 LIGHT secret. It is a dark cave-like reed
  channel on level 0, blocked by a "too dark to wade" sign-trigger. Make
  it a tiny `MF_DARK` interior warp, `MAP_REED_TUNNEL` (20x12), whose exit
  is a hidden satchel nook with a DUSK SHARD and lore on will-o'-wisps.
  Optional: skip the map and use an elevation TUNNEL feature.
- **SURF secret** (§9, after Act III): a channel south to a hermit's hut
  (an interior). The hermit teaches a move tutor (1 move from a small
  list) for materials.

**Wild zones:**

FEN_REEDS (Lv17–21):

| Kin | When | Weight |
| --- | --- | --- |
| PEBBOTTER | any | 20 |
| MUDDLE | night | 10 (a teaser of grim) |
| WEBBIT | any | 10 |
| HUMBEE | day | 10 |
| BLINKET | night | 15 |
| SHROOMLET | any | 10 |
| MOSSHELL | any | 15 |
| NOXKIT | night | 5 |

FEN_WATER (surf, Lv20–24): BUBBLIN, JELLUME and LURELING (night).

**Wardens** (6):

- a birdwatcher;
- two reed-cutters (a double bout);
- a fisher on the rookery island;
- a night-only "wisp chaser" (E3 NIGHT);
- one warden on the east teaser part (Lv18).

**Other contents:**

- **Satchels:** 3 visible, 2 hidden, and the reed-tunnel secret.
- **Berry:** TIDEBERRY patch.
- **Events:** a fog-front map hook for plan 09; the heron migration in
  spring (seasonal slot, plan 09).

---

## 3. REEDWICK (new hamlet, `MAP_REEDWICK`, 40x32, TS_COAST)

**Edges:**

- E → HERON_FEN at y19–20.
- W → SALTWIND at y31–32. Saltwind's existing east opening stays at y31–32;
  Reedwick's west edge opens there.

**Feel.** Stilt houses over the water, joined by rope bridges (BRIDGE_V/H).
Eel-smoking racks. A small **Hearth** (fly point). A boat-builder's slip.

**People:**

- **SMOKER NELL** sells SMOKED EEL, a regional dish if crafting agrees;
  otherwise BERRY JUICE.
- **Side quest REEDS FOR THE ROOF** (repeatable once per season): cut reeds
  in the fen. This uses the forage interaction: `OBJ_BERRY` with a reed
  crop id, or a new forage kind through the farm owner. Bring 5 for coins.
- **Postmistress.** The first link of the **Vale Courier** chain (plan 10
  owns the chain; you place the NPC with the `SCR_` id plan 10 gives, or
  host the script in `world/saga`, which places NPCs on your map by
  itself). Coordinate: plan 10 places it, and you leave a free spot at
  (12,10).
- **An old reed-cutter** with lore: how DUSK kin drink starlight on the fen.

**Wardens:** 2 (Lv20–21).

**Secret:** the boat-builder's slip. **SURF** out to a moored wreck with a
satchel (IGNITER x2).

---

## 4. SALTWIND TRAIL (existing, rework)

- **Links:** E → REEDWICK (was LAKE); W → PORT_BRINE (unchanged).
- **Re-level** the zone to 19–23 and the wardens to 20–23 (contract §5).
- **Salt pans:** keep them; ISLE_SALT still sources SALT here.
- **A §9 STRENGTH secret:** a boulder-sealed cliff cache under the bluff,
  holding a TIDE LANTERN x3 and lore.
- **A lighthouse keeper NPC** on the bluff. Lore, plus a hook for plan 09:
  on STORM days the lighthouse beam animates.

---

## 5. PORT BRINE (existing hub of the west; add depth)

- **Re-level** MAREN to 25–28 and the Current Hall wardens to 23–26.
- **Fish market.** On market days (plan 09) there are extra traders. Reserve
  3 stall cells.
- **Ferry.** Unchanged: 500c, or the FERRY PASS from HARBOR_POST.
- **North harbour mouth** (for plan 08): Port Brine's **north edge** becomes
  the entry to GREYWATER FJORD. It is surf-only: the opening is water cells
  at the top edge.
  - Build the opening (x at your choice, 2 cells, water) and link
    N → `MAP_GREYWATER_FJORD`.
  - A buoy line and a sign: "NORTHERN WATERS — SURF ONLY".
  - Plan 08 builds the fjord. Agree the x with plan 08 and note it in the
    `west/data.h` header.
- **The south SURF back path** toward Willow Acre (contract §3 shortcuts,
  after Act III) is optional and low priority. Skip it if the tile budget
  bites.

---

## 6. Sea Route, Gull Isle, Drowned Bell

- Levels unchanged (24–30): optional content in Act III.
- **Drowned Bell legend (NOCTHALE):** add the post-game gate
  (`FLAG_OSSUREX_ANSWERED`). A sealed bell door with a sign: "THE BELL
  SLEEPS UNTIL THE MARCH IS QUIET".

---

## 7. Tests (`test_west.c`, extend)

- G2: with the flags clear, the west of the fen is unreachable from LAKE.
  With `FLAG_FEN_RIVETS` set, Port Brine is reachable on foot.
- Budgets hold with the patch on and off, and with every NPC condition on.
- The fjord opening is water only, and reachable only with SURF.
- **Milestones:** MAREN → `FLAG_TIDE_CREST`.

**Handoff.** Update `docs/handoff/west.md` with a Routes section and
screenshots.
