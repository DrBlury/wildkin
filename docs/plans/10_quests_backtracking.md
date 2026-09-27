# 10 — Quests, town projects and backtracking

**Work package:** SAGA.

**Needs:**

- plan 02 merged, including E3, E5 and E9 (per-stage quest text, markers,
  categories, `QUEST_MAX` 96);
- the region plans 03–07 merged, since this plan places NPCs on their maps;
- plan 09 merged before §5 (the event-category errands).

**Owns:**

- the new region directory `src/game/world/saga/`, registered after `ui`
  and before `debug`: quests, NPCs, scripts, flags, lore, satchels and
  milestones;
- `src/game/items/saga.inc`, for new materials and key items;
- `tools/tests/test_saga.c`.

**Contract:** `01_progression_contract.md` §3 (shortcuts) and §9 (the secret
register).

**How to place people on other regions' maps:** `NpcDef.map` can be any map.
After the region plans merge:

1. Pick free walkable cells.
2. Run `test_field.c` and the per-map people and sprite limits.
3. Never move a region's own NPCs. If a spot is too crowded, ask that
   region's owner.

---

## 1. Goals

- **Every act sends you back at least once.** A quest started in act *N*
  finishes in an earlier town, or needs an ability from act *N+1*.
- **Backtracking is short and rewarded:**
  - shortcuts (the tram, the rebuilt bridge, the lift, FLY);
  - the quest markers on the town map (E9);
  - FIELD NOTES that remember every locked spot.
- **Quests have people in them**, not just fetch lists. Every chain has a
  small arc that ends with a change you can see in the world.

---

## 2. FIELD NOTES: the backtracking memory

**What:**

- When the player examines a locked spot, the spot is recorded: a dark
  hollow, a boulder, surf water, a fog pocket, a mirror pad or a high ledge.
- It is recorded with the ability it needs. There is one bit per spot: 64
  spots in `u8 notes[8]`, appended to QuestState or the saga module.
- The quest log gets a **FIELD NOTES** page:
  - notes are grouped by ability;
  - each note shows the map name and ✓ once solved;
  - once the ability is owned, the note's map gets a small marker on the
    town map (E9).

**Data:** `world/saga/notes.inc`, one entry per note: `{note_id, map, x, y,
ability, solved_flag_or_satchel}`. The §9 secret register in the contract
is the source list; every region plan built its spots.

**Hook:**

- The locked-spot interaction already exists in some form (a sign or
  trigger). Region plans call `saga_note(NOTE_ID)` from it.
- If a region already merged without the call, add a sign-trigger NPC or
  sign in `world/saga/signs.inc` on that spot.

**Test:** every note's `(map, x, y)` is next to a reachable cell, and
becomes solvable when its ability is present (the progression solver).

---

## 3. Town projects (category PROJECT)

**The idea.** Brookmill's carpenters' guild builds things for the Vale. You
bring materials and coins; the next dawn it is built. The map changes for
good through an E5 patch on the project's done flag.

**API** (`world/saga/scripts.c`, exposed for region scripts):

```c
void saga_project_offer(int proj);   /* shows needs, sets stage 1 */
int  saga_project_state(int proj);   /* 0 none, 1 offered, 2 paid (building), 3 done */
/* saga day hook (via events_new_day or E10's hook list): 2 -> 3 and flag_set(done_flag) */
```

| Project | Offered by / when | Needs | Done flag → effect |
| --- | --- | --- | --- |
| COPPERLINE TRAM | Guildmaster Holt, after `FLAG_VOLT_CREST` | 5 IRON ORE (Copperline Mine) + 3,000c | `FLAG_PROJECT_TRAM`. Tram stops appear in Maple (a new stop NPC by the Land Office), Brookmill (the depot patch, plan 03) and Lumen (the Copperline buffer-stop patch, plan 03). Riding is a short cutscene between any two stops; reuse `travel_boat_to` with a tram sprite, or a fade warp with a rail sound. |
| CINDER BRIDGE | Foreman Greta (Railhead), after `FLAG_CREST_ANVIL` | 4 IRON ORE + 2 COAL + 4,000c | `FLAG_PROJECT_CINDER_BRIDGE`: plan 05's bridge patch. The forge road becomes walkable. |
| TIMBERLINE LIFT | Lodgekeeper Astrid, after `FLAG_RIME_CREST` | 6 TIMBER (Timberline sawyer) + 2,500c | `FLAG_PROJECT_LIFT`: a cable-lift NPC pair at the Foothills' south end and in Timberline (a fade warp). |
| REEDWICK FERRY | Postmistress, after the COURIER stage 3 | 4 TIMBER + 2 SALT + 2,000c | `FLAG_PROJECT_REED_FERRY`: a punt ferry Reedwick ↔ Mirror Lake dock (`travel_boat_to`). |
| MAPLE MARKET HALL | Keeper Linden, after 3 other projects | MILL FLOUR x5 + HONEY x5 + 6,000c | `FLAG_PROJECT_MARKET`: a new building in Maple (E5 patch on a reserved lot; ask the village map owner, plan 11, to reserve it) with a rotating regional-goods shop and the Hearth-side caravan stop. |

**Money balance.** Project costs sit next to the coins a player has at each
act. Plan 12 checks they are affordable after the act's Master, plus a
little farming.

---

## 4. Quest chains

Use per-stage goal text (E9) and markers. The ids are appended in
`world/saga/quest_ids.inc`.

### 4.1 THE VALE COURIER (SIDE, Acts III–VII)

**Arc.** Postmistress **ELSPETH** of Reedwick runs the Vale's mail by
hand since the telegraph doesn't reach the hamlets. Each stage is a
delivery that crosses the map. Reply letters send you back.

**Stages:**

1. **(III)** A parcel to Brookmill's miller. His reply goes to Elspeth.
2. **(III)** A letter to the Lumen telegraph clerk, who asks to wire the
   hamlets. Needs the TRAM project done, *or* just walking.
3. **(IV)** Mail to Railhead (past the Cinder bridge, so it needs SURF or
   the project). Greta's reply goes to Elspeth.
4. **(V)** Mail to Timberline. Offers REEDWICK FERRY.
5. **(VI)** A sealed letter for the Accord captain at the checkpoint, and
   her answer for the Waychapel.
6. **(VII)** The last letter goes to Pilgrim Rest in Mistfen. Its sender
   turns out to be Elspeth's missing brother, a pilgrim. Bring him home to
   Reedwick: he walks there, via an E3 `show_flag` swap.

**Rewards** per stage: coins, then the FERRY PASS discount. At the end, the
**COURIER'S SATCHEL**, a key item that makes the Gazette show quest-marker
towns. It needs E9.

### 4.2 THE ALMANAC SURVEY (SIDE, all acts)

- **Giver:** **Keeper Linden** asks you to survey each region.
- **Goal:** "meet" (see) N kin species native to it. Region membership comes
  from the zones: `zone → region` via the map.
- **Stages:** one per region; the goal shows "EAST 7/10".
- **Reward per region:** a regional lantern type (TIDE LANTERN, DUSK
  LANTERN…) and lore.
- **Completing all:** the STAR LANTERN x5 and the Keeper's final lore
  chapter.
- **Why it matters:** it gives a reason to walk every route at every time
  of day, since night slots count.

### 4.3 THE LEGEND TRAIL (SIDE, post-game with teasers from Act II)

**Arc.** The innkeeper of **Pilgrim Rest** keeps the old pilgrims' book of
the ten legends. Each legend's lair has a **verse** found much earlier. A
verse names the lair and the ability it needs, and marks it on the town map.
The lairs themselves open on `FLAG_OSSUREX_ANSWERED` (contract §4), not on
the verses. Answering every legend unlocks the DRAKORA rematch. That turns
the post-game into a tour of the whole world.

**Verse table.** A verse is a lore entry from a sign or stone. Its location
is the backtracking hook; the "opens" column is the ability the lair needs.

| Legend | Verse found in | Opens with |
| --- | --- | --- |
| SYLVARCH | Brookmill Trail rookery (II) | STRENGTH + post-game |
| NOCTHALE | Greywater Fjord drowned village (post-SURF) | SURF + post-game |
| HOARFANG | Timberline (V) | STRENGTH + post-game |
| CALDERON | Scorchwaste Glass Dunes (VI) | STRENGTH |
| SELENOTH | Aurora Ridge Star Cairn (VII) | nothing new: Starfall is reached through Glimmer. Its verse *reveals* the lair's hidden inner chamber (an `EF_HIDDEN` passage, owned by plan 06) |
| HOROLOGOS | Copperline Mine (LIGHT gallery) | STRENGTH + post-game |
| SCRIPTORA | Mistfen Weeping Stone | post-game |
| SKYLORN | Stormstep shrine high ledge (FLY) | FLY + post-game |
| DRAKORA rematch | the Rise, once 9 legends are answered | — |

**Stages** = the number of verses read. The book NPC reads your Lorebook to
count them.

**DRAKORA rematch:** Lv60, at the Stormstep high-ledge shrine. It gives the
title "STORMFRIEND", shown on the trainer card if one exists; otherwise
lore.

### 4.4 Smaller chains (each 3–4 stages, SIDE)

| Chain | Acts | Arc and backtracking |
| --- | --- | --- |
| THE HERON'S RING | III → VI | A Reedwick widow lost a ring when the fen flooded. A heron (a static PEBBOTTER that steals shiny things) took it to the rookery island. With SURF (III) you find the nest empty: a RACCOIN took it on to Maple's night streets (village, night, E3). Reward: RING OF REEDS, a hold item or trinket; or coins. |
| MINER'S LAMP | II → IV | The Copperline Mine boss lost a lamp in the dark gallery (LIGHT, II). The lamp's maker is in Cindermoor (IV), and it needs re-forging (a forge minigame, craft plan). Reward: a LIGHT radius upgrade, or a METAL SHARD. |
| THE CHALK HORSE | VI → post | Hollow Downs' chalk-cutter restores the hill figure. Bring BONE MEAL (grim) and SALT (west); the figure is re-drawn (E5 patch) and a rare DULLAHAN hint appears (a fusion recipe lore). |
| STARLIGHT FOR IDA | V → VII | It extends STAR_CHART: after Starfall, Ida wants a reading from the Star Cairn on Aurora Ridge at AURORA night (plan 09). Reward: an ASTRAL SHARD and a QILUMEN sighting guaranteed that night. |
| RIVAL'S LOST LANTERN | set by plan 11 | See plan 11. This plan owns nothing for it. |

### 4.5 Changes to existing quests

- **ISLE_SALT:** unchanged. It already backtracks.
- **ASH_LANTERN** and **MIRE_LETTER:** re-level any wild encounters to the
  new Act VI levels (plan 07 re-levels the zones; nothing to do here).
- **GLOWCAPS:** fine.
- **STAR_CHART:** its reward stays; the follow-up is STARLIGHT FOR IDA.
- **REEVE_BERRIES:** fine.
- **HOLLOWING:** plan 11 re-times it.

---

## 5. EVENT errands (category EVENT, with plan 09)

- **Repeatable one-day errands** from the caravan and the Gazette board:
  deliver X to a town before dawn, find a LOST KIN, or clear a BRIMMING
  SURGE route.
- **State:** one reusable quest slot (`QUEST_ERRAND`), re-initialised by
  events each day. Its goal text is built from a template.
- **Rewards:** coins and a small chance of a rare material.

---

## 6. Tests (`test_saga.c`)

- Every quest's stage text exists for every reachable stage, and the markers
  point at real maps.
- **Every project:**
  - its done-patch fits the budgets;
  - the progression solver passes with it on and off;
  - costs are ≤ the coin estimate for its act (a table shared with plan
    12).
- **The FIELD NOTES test** from §2.
- **Legend Trail:** every verse lore id exists and its source is reachable
  in its act.
- **Save:** quest stages round-trip; an old save without saga state loads.

**Handoff.** Write `docs/handoff/saga.md`.
