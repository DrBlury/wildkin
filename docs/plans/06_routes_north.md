# 06 — North: Stormstep Foothills, Timberline, Frostpine, Frosthollow (Act V)

**Work package:** REGION-NORTH.

**Needs:** plan 02 merged (E1, E3, E5, E8; E10's `WX_SNOW` is nice to
have).

**Owns:**

- `src/game/world/north/`
- `tools/tilesets/ts_snow.py`, `ts_cave.py`, `tools/decor_north.py`
- `tools/tests/test_north.c`

**Contract:** `01_progression_contract.md`: §3 Act V, §4 G4, §5, §6, §8, §9.

**Don't touch:**

- Stormstone Rise's map data (village).
  - Change Rise's `link[N]` to `MAP_FOOTHILLS` yourself (one line in
    `village/maps.inc`; the village has no plan) and note it in the
    handoff.
  - The **rockslide** (G4) sits on **your** side, at the Foothills' south
    end, so you never edit Rise's rows.
- Engine files.

---

## 1. Act V in one paragraph

The storm's last thunderclap brought the ridge above Stormstone Rise down
(gate G4). With STRENGTH from Cindermoor you shove the boulders aside and
climb:

1. the **Stormstep Foothills**: a switchback climb from green meadow into
   the first snow;
2. **Timberline**, a logging hamlet with a lodge and a sawmill;
3. the higher **Frostpine Pass**, now a real alpine route;
4. **Frosthollow**, where Sigrun's Rime Hall gives FLY.

---

## 2. STORMSTEP FOOTHILLS (new, `MAP_FOOTHILLS`, 40x60, TS_WILD)

**Tileset.** Use TS_WILD; the snow edge is drawn with decor and blends (see
the ground-blends note in HANDOFF.md). If the snow look needs TS_SNOW, make
the **north half** a separate map (`MAP_FOOTHILLS_2`, TS_SNOW) and keep the
edge fade short (E7).

**Edges:**

- S → RISE at x11–12. This is Rise's existing north opening. The Foothills'
  south opening must be at x11–12.
- N → TIMBERLINE at x19–20.

**Gate G4:**

- The south entrance leads into a **one-cell corridor** between cliffs.
- In it are **3 `OBJ_BOULDER`s** (arg 0, *not* pumice) in a pattern that
  STRENGTH clears in two pushes.
- **Prove it** with `test_puzzles.c`, and prove there is no soft-lock:
  - a boulder pushed wrongly must never seal the way back to Rise;
  - the corridor must not let a boulder be pushed south into Rise's
    opening.
- Put a warning sign at Rise's north edge: "RIDGE CLOSED BY ROCKFALL —
  WARDENS WITH THE ANVIL CREST MAY CLEAR IT". The sign sits on your side,
  just inside the corridor, readable from Rise's top rows.
- A **ledge drop** on the way back skips the corridor: a return shortcut.

**Shape** (switchbacks up the elevation layer, levels 0–3):

- **Zone 1 (south):** alpine meadow, in grass.
- **Zone 2 (north):** snowline scree, first snow and pines.
- **Landmark: the Stormstep.** A stair of natural basalt steps with a
  weather shrine to DRAKORA. After FLY, the **high ledge** above the
  shrine (a §9 FLY secret, reached from a fly point, or a FLY-only elevated
  level) holds the DRAKORA rematch shrine, post-game (plan 10).
- **A STRENGTH secret:** a boulder cave with a SPARK SHARD.

**Wild zones:**

FOOTHILLS_LOW (Lv28–32):

| Kin | When | Weight |
| --- | --- | --- |
| RAMBLET | any | 20 |
| CRAGHORN | any | 5 |
| PUFFOWL | day | 10 |
| HOOTLORD | night | 5 |
| VOLTUX | any | 15 |
| STORMHAWK | any | 10 |
| TRUFFLOAR | day | 10 |
| FLYSQUIRL | any | 15 |

FOOTHILLS_SNOW (Lv29–32): FLURRABBIT, YAKLING, FROSTOAT, TUXFLAKE and
MOONHARE (night).

**Contents:**

- **Wardens** (7):
  - hikers;
  - a mountain guide;
  - a double bout of climbers;
  - a storm-watcher, whose lore is on DRAKORA's weather after the calm;
  - a guard on the scree satchel.
  - Levels 29–32.
- **Satchels:** 3 visible, 2 hidden, and the two secrets above.
- **Events:** a snowstorm-front hook (plan 09) on the north half.

---

## 3. TIMBERLINE (new hamlet, `MAP_TIMBERLINE`, 40x36, TS_SNOW)

**Edges:**

- S → FOOTHILLS at x19–20.
- N → FROSTPINE. Frostpine's existing south opening stays; it was linked to
  Rise at x11–12. Timberline's north opening matches it, at x11–12.

**Feel.** A logging camp at the tree line:

- log piles, a flume, and a sawmill wheel (anim);
- **TIMBER LODGE** (interior, MF_HEAL, fly point);
- **SAWMILL** (interior).

**People:**

- **LODGEKEEPER ASTRID.** Hot cocoa, a warm meal and lore on how FROST kin
  cool the air.
- **Side quest LOST AXE:** a logger's axe was carried off by a GNAWLORD.
  The GNAWLORD is a static wild encounter in the Foothills' STRENGTH cave,
  which gives backtracking inside the act. The reward is a HEAVY LANTERN
  x3.
- **The sawyer.** Sells TIMBER, a material for town projects (plan 10). If
  the material doesn't exist, plan 10 adds it to `items/saga.inc`, and you
  only reference it.
- **A night-only aurora watcher** (E3 NIGHT, WINTER via plan 09 events).
  Lore on the aurora, and the ASTRAL kin that pump from muons.

**Wardens:** 2 (lumberjacks, Lv31).

---

## 4. Frostpine, Frosthollow, Glimmer, Whitecrown (existing)

**Frostpine Pass:**

- Re-level to 30–34 and its wardens to 31–34 (was 18–24). **This fixes the
  biggest curve break in the current game.**
- S → TIMBERLINE (was RISE).
- W edge: plan 08's GREYWATER FJORD arrives by a **sea-cave warp** (not an
  edge). Place a cave door on Frostpine's west cliff that leads to
  `MAP_GREYWATER_FJORD`'s cave, and agree the coordinates with plan 08.

**Glimmer Caverns:** Glimmer 1 to 30–34, Glimmer 2 to 32–36, and the
wardens to 31–35.

**SIGRUN (Rime Hall):** 34–37 (was 33–37).

**Frosthollow:**

- **East side** (for plan 08): an **edge** E → `MAP_AURORA_RIDGE_1`. Build a
  2-cell opening, agree the y with plan 08, and link it.
  - Gate it from your side with a map patch: an ice wall, solid until
    `FLAG_RIME_CREST`. The wall thaws, as the in-world story tells it.
- **Hot spring:** add a daily-buff interaction if plan 09 offers one
  ("warm soak": +bond to the team). Optional.

**Whitecrown (HOARFANG):**

- Re-level to 44–50 (post-game).
- Keep the boulder, and add the post-game gate on the lair
  (`FLAG_OSSUREX_ANSWERED`): a sealed ice door with a hint sign.
- The lower Whitecrown (below the boulder) may stay open at 44–50 as a
  dangerous optional area, with a warning sign.

**Sky Isle (SKYLORN):** FLY, plus the post-game gate on the legend only.

---

## 5. Tests (`test_north.c`, extend)

**G4:**

- Without the ANVIL crest (STRENGTH), Timberline is unreachable from Rise.
- With it, Timberline is reachable, and `test_puzzles.c` proves the
  corridor has no soft-lock.

**Aurora wall:** the Aurora Ridge edge is blocked until `FLAG_RIME_CREST`.

**Budgets:** hold with every patch and condition on and off.

**Milestones:** SIGRUN → `FLAG_RIME_CREST`.

**Handoff.** Update `docs/handoff/north.md` with a Routes section.
