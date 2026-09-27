# 07 — Grim: the Accord Checkpoint, Hollow Downs, Ashen Fields, Gravewood, Duskmere (Act VI)

**Work package:** REGION-GRIM.

**Needs:** plan 02 merged (E1, E3, E5, E8).

**Owns:**

- `src/game/world/grim/`
- `tools/tilesets/ts_grim.py`, `ts_crypt.py`, `tools/decor_grim.py`
- `tools/tests/test_grim.c`

**Contract:** `01_progression_contract.md`: §3 Act VI, §4 G5 and G7, §5, §6,
§8, §9.

**Don't touch:**

- Copperline's rows (plan 03). Plan 03 builds the checkpoint *door* on
  Copperline's south edge and its warp into `MAP_ACCORD_GATE`. Agree the
  door cell with plan 03 (default (20,35)).
- Engine files.
- The Keeper's main-story beats in Maple. Plan 11 (story) re-times
  QUEST_HOLLOWING. This plan keeps `grim_keeper_talk()` working and
  exposes the flags plan 11 needs.

---

## 1. Act VI in one paragraph

The Ashen March has been under **quarantine** since the hollow kernels
began to wake. The Wardens' Accord keeps a **checkpoint** south of
Copperline and lets through only wardens with four crests (gate G5).

Past it the road descends:

1. **Hollow Downs**: grey chalk downs with barrows, and the lonely
   **Waychapel** where wardens rest;
2. **Ashen Fields**;
3. **Gravewood**;
4. **Duskmere**, where Morwen's Lantern Crypt gives the LANTERN crest and
   the **WARD LANTERN**. Its steady light parts the Moonveil mist (G6,
   plan 05) and wards the Ossuary.

---

## 2. ACCORD CHECKPOINT (new, `MAP_ACCORD_GATE`, 13x9, TS_INTERIOR)

Use the gatehouse template from plan 02 E8.

**Doors:**

- north door → Copperline (20,35) or the agreed cell;
- south door → `MAP_HOLLOW_DOWNS` north door.

**Blocker:**

- The warden **CAPTAIN AUDRA** stands in the south lane.
- She is visible with `hide_flag = FLAG_RIME_CREST`.
- A second Audra NPC (`show_flag = FLAG_RIME_CREST`) stands aside at the
  desk and gives the **ACCORD PASS** flavour line.

**Script:**

- Before 4 crests: "Only wardens with four crests may enter the March. You
  have *N*." Show *N* from `travel.crests`.
- After: a short briefing on hollow kin, plus lore on HOLLOW type physics.
- **Test:** the progression solver must see the blocker as solid until the
  flag is set.

A checkpoint guard sells supplies: IGNITERs, TUNING FORKs and BONE
LANTERNs.

---

## 3. HOLLOW DOWNS (new, `MAP_HOLLOW_DOWNS`, 60x40, TS_GRIM)

**Access:**

- A **door** on its north side, from the Accord Checkpoint.
- S → ASHEN_FIELDS at x20–21. This is Ashen's existing north opening; it
  used to link to Copperline.

**Feel.** Rolling chalk downs, greyed by ash:

- **barrows** (burial mounds);
- a white **chalk horse** hill figure (the landmark, big decor seen from
  the path);
- dry-stone walls, and a **Waychapel** on a knoll.

**Shape:**

- Walls make lanes, so the fork is between wall-lanes.
- The **barrows** are small hidden-passage entrances (`EF_HIDDEN`) into
  one-room barrow interiors. Build 2 barrows:
  - `MAP_BARROW_A` holds a satchel;
  - `MAP_BARROW_B` holds a **mimic chest** (TRINKIT, arg 254/255) and lore
    on the old burial customs that seeded HOLLOW kin.
- **A §9 WARD LANTERN secret** (returning after Act VI): a fog pocket in a
  dene holding a satchel with a HOLLOW SHARD and a CALCIPUP static
  encounter, a lustrous-roll bonus.

**WAYCHAPEL** (`MAP_WAYCHAPEL`, 13x10, TS_CRYPT):

- `MF_HEAL`, and a fly point.
- **SISTER MAUD.** Heals you; lore on the Kinship vows. She starts the side
  quest **CANDLES FOR THE BARROWS**: light 3 barrow candles. The candles
  are SWITCH objects in the barrows plus an overworld cairn. Reward: 3
  WARD INCENSE, or 3 HUSH BELL if the item doesn't exist.

**Wild zone** DOWNS (Lv33–37):

| Kin | When | Weight |
| --- | --- | --- |
| CALCIPUP | any | 20 |
| DREGCROW | any | 20 |
| DIGGET | any | 10 |
| SCYTHLING | day | 10 |
| STRAWSPECT | day | 10 |
| JACKOGRIM | night | 10 |
| OSSIHOUND | any | 5 |
| NOXKIT | night | 10 |
| RATTLEBONE | night | 2 (rare) |

**Contents:**

- **Wardens** (6): Accord patrols, a barrow-digger, a pair of pilgrims
  (double bout), and a chalk-cutter. Levels 34–37.
- **Satchels:** 3 visible, 2 hidden, the barrows and the secret.
- **Events:** an ash-storm front (plan 09 `WX_ASH`); night outbreaks of
  CALCIPUP.

---

## 4. Ashen Fields, Gravewood, Duskmere, the Ossuary (existing)

**Links:** ASHEN N → HOLLOW_DOWNS (was COPPERLINE).

**Re-level** (contract §5):

| Area | Wild | Wardens |
| --- | --- | --- |
| Ashen Fields | 34–38 | 35–37 |
| Gravewood | 35–39 | 36–38 |
| Duskmere mire | 36–40 | — |
| Lantern Crypt | — | 37–39 |
| MORWEN | — | 38–41 |
| Ossuary 1 / 2 | 44–48 / 46–50 | 46–50 |

**The WARD LANTERN:**

- Add it as a new key item, appended to `items/grim.inc`.
- MORWEN gives it together with the LANTERN crest.
- Plan 05 reads `FLAG_LANTERN_CREST` for the fog, so the item is flavour
  plus a field "use" line: "The ward lantern glows steadily." Optionally,
  it widens the dark-map light radius like LIGHT.

**The Ossuary gate (G7):** unchanged. It needs 6 crests.

**The Duskmere east cave** (for plan 08, SCORCHWASTE):

- Put a cave-mouth door on Duskmere's east side, with a warp to
  `MAP_SCORCHWASTE_2`'s west cave. Agree the coordinates with plan 08.
- **One-way at first.** From Duskmere the cave is sealed by a
  **rockfall**: STRENGTH boulders, so it is openable in Act VI. That makes
  it a shortcut back toward Cindermoor.

**The healed March** (existing `grim_healed()` / `MF_ASH`):

- Once OSSUREX is answered, apply **map patches** (E5) that turn a few ash
  fields back into grass and flowers on Ashen Fields and Hollow Downs.
- Add seasonal wild slots that only appear after healing (plan 09 hooks):
  BLOOM kin return.

---

## 5. Tests (`test_grim.c`, extend)

**G5:**

- With 3 crests, Hollow Downs is unreachable.
- With `FLAG_RIME_CREST`, it is reachable.
- Test the 4-crest *count* line too. The gate is the flag; the count is
  text only.

**Barrows:** hidden entrances are found and reachable, and no puzzle
soft-locks (`test_puzzles.c`).

**Healed patches:** fit the tile budget and keep reachability.

**Milestones:**

- MORWEN → `FLAG_LANTERN_CREST`;
- the Ossuary gate → `FLAG_OSSUARY_OPEN`;
- OSSUREX → `FLAG_OSSUREX_ANSWERED`.

**Handoff.** Update `docs/handoff/grim.md` with a Routes section.
