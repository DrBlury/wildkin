# 09 — Dynamic events: a Vale that changes day to day

**Work package:** EVENTS.

**Needs:** plan 02 merged, including E3 (NPC conditions), E5 (map patches)
and E10 (the daily hook, day seed, wild and weather overrides, and the
map-enter hook).

**Owns:**

- the new `src/game/events.c` (included in `main.c` after `time.c`);
- the new region directory `src/game/world/events/`, registered after `ui`
  and before `debug`;
- `tools/tests/test_events.c`;
- the weather particle art for the new `WX_*` kinds, in a new
  `tools/gen_events_gfx.py` or in `gen_travel_gfx.py` if the traversal
  owner agrees.

**Contract:** `01_progression_contract.md` §8.9: every route has an event
hook.

---

## 1. Design goals

- **Something is different most days.** Each dawn rolls a small set of
  events. The player learns what they are from the **Vale Gazette** board
  at every Hearth, so events are discoverable, not random noise.
- **Deterministic per day.** Every roll uses `time_day_seed()` (E10):
  reloading a save never re-rolls the day. That prevents save-scumming and
  keeps tests reproducible.
- **Events reward detours.** They are a reason to walk the long routes
  again, not a tax on the critical path.
- **Never block the critical path**, and never soft-lock. An event may make
  a route harder or richer; it never closes a gate.
- **Cheap on the GBA.**
  - Events are data tables plus a few hooks.
  - State fits in about 64 bytes: append an `EventState` to the time module
    blob (32 bytes cap, 8 used; tight), or register a new module slot. Two
    of the 8 slots in `mod_size[8]` are free; check how blob storage is
    reserved in `save_game.h` before choosing.

---

## 2. Event state and the API

```c
typedef struct {
    u32 save_seed;        /* per-save random, set at new game (if E10 put it elsewhere, drop this) */
    u16 rolled_day;       /* gtime.day these events belong to */
    u8  active[8];        /* EV_* ids active today (0 = none) */
    u8  arg[8];           /* per-event argument: zone/map/species index */
    u8  caravan_map;      /* where the caravan is today (index into CARAVAN_ROUTE) */
    u8  rematch_bits[8];  /* 64 rematch-ready wardens (index into REMATCH table) */
    u8  festival;         /* FEST_* today or 0 */
    u8  front_region;     /* region under a weather front */
    u8  front_kind;       /* WX_* */
    u8  pad[...];
} EventState;

void events_new_day(void);                       /* E10 daily hook */
int  events_active(int ev);                      /* E3 NPC visibility, E5 patches */
int  events_arg(int ev);
int  events_weather_here(int map);               /* E10: WX_* */
int  events_wild_override(int zone, WildSlot *s); /* E10: 1 = replaced */
void events_map_entered(int map);                /* E10 */
const char *events_gazette_line(int i);          /* for the board */
```

**Validate** in `events_validate()`: clamp ids, and re-roll if
`rolled_day != gtime.day`.

---

## 3. The event catalogue

Each event is `{id, kind, weight, min_act, seasons, regions, duration_days}`.
The daily roll picks:

- 1 weather front (or none);
- 0–1 outbreaks;
- 0–1 "happenings";
- the caravan's next stop;
- rematch refresh.

Festivals are calendar-driven, not rolled.

`min_act` uses the highest story flag reached (the contract §3 acts), so
Act I players only see Act I events and places.

### 3.1 Weather fronts (per region)

Extend the global `WEATHER_CLEAR/RAIN` with a **regional front**: on top of
the global roll, one region may get a special sky.

| WX | Regions | Effect in the field | Effect on wild kin | Art |
| --- | --- | --- | --- | --- |
| STORM | any outdoor | Rain, flashes (reuse the storm code at `script.c:962`), darker tint | SPARK and GALE slots ×2; +2 levels | reuse |
| FOG | west, dream, fjord | Palette haze; lower visible-kin range (spot range 4 → 2) | DUSK and DREAM ×2 | new: a fog overlay (BG blend) |
| SNOW | north | Snowfall. Wire the dead `MF_SNOW`, so snow always falls on those maps and a front makes a blizzard | FROST ×2 | new particles |
| HEAT | far volcanic, Railhead | Shimmer (a small sine on BG scroll rows) | BLAZE and METAL ×2 | none |
| ASH | grim (before healing) | Existing `MF_ASH` haze, stronger | HOLLOW ×2 | reuse |
| AURORA | north, Aurora Ridge, at night | Animated sky palette cycle | ASTRAL ×3; QILUMEN and MOONHARE unlock | palette cycle |

**Rules:**

- Fronts last 1–2 days.
- The Gazette names them ("A fog bank has rolled over Heron Fen").
- Farm rain is still the global roll only.

### 3.2 Kin outbreaks

- **What:** one zone has a single species at weight ×6 for the day, with
  +10% lustrous odds.
- **Pick:** a species from a **curated per-zone list** (not the zone's full
  table), preferring uncommons.
- **Min act:** the zone's act.
- **Gazette:** "BLINKET are swarming on BROOKMILL TRAIL!"

**Seasonal migrations** are fixed-calendar outbreaks:

| Season | Outbreak |
| --- | --- |
| Spring | Herons at Heron Fen (PEBBOTTER and KOIRIN up) |
| Summer | HUMBEE on the Meadow |
| Autumn | PUMPKLING and JACKOGRIM on Ashen and Hollow Downs |
| Winter | TUXFLAKE on the fjord |

### 3.3 The travelling caravan

- **Who:** **MERRIWEATHER'S CARAVAN**, a wagon plus two NPCs, as event NPCs
  in `world/events/npcs.inc`.
  - One NPC per caravan stop: a `CARAVAN_SPOT` on each route (contract
    §8.9).
  - `event = EV_CARAVAN` and `arg` = stop index, so only today's stop shows.
- **Route:** a fixed loop of stops that follows the critical path. Each day
  it moves one stop:
  Brookmill Trail → Copperline → Lumen → Cinder Crossing → Railhead → back →
  Lumen → Brookmill → Maple → Heron Fen → Reedwick → Saltwind → Port Brine →
  back. It skips stops past the player's act.
- **Sells** a rotating stock: 4 items from a regional pool and 1 rare, e.g.
  a shard, a LURE INCENSE, a seed the farm can't buy elsewhere, or a TM-like
  move tutor. Use `shop_open_stock`.
- **Also:**
  - **buys** crafted goods at a premium (a hook for farm and craft);
  - starts **one courier-style errand per visit**, a small repeatable EVENT
    quest (plan 10's category EVENT);
  - the **Gazette tells where the caravan is today.**

### 3.4 Happenings (small, one day)

Roll 0–1, weighted by act and region:

| Happening | What | Where |
| --- | --- | --- |
| LOST KIN | An NPC's pet kin ran off; it is a visible wild kin (a fixed species) on a nearby route that follows you back. Reward: coins and bond. | any route |
| BRIMMING SURGE | One route's wild kin are all brimming, +3 levels, +50% XP; the Gazette warns. | routes, Act II+ |
| METEOR NIGHT | METEORB at the Rise at night, 10%; a shard satchel appears (a map-patch satchel spot). | Rise, Aurora Ridge |
| NIGHT MARKET | Lumen's reserved stall cells fill with traders (plan 03). | Lumen, 1 day a week |
| FISH MARKET | Port Brine stalls (plan 04). | Port Brine, 1 day a week |
| WASHOUT | After 3+ rain days in a row, a *side* path on Brookmill Trail or Heron Fen floods (map patch, `event = EV_WASHOUT`), revealing a rare water kin; never a critical path cell. | Brookmill, Fen |
| WARDEN TOURNEY | A pop-up 3-bout ladder in a Hearth town; reward: coins and an item. | hub towns |
| HEARTH TALES | A travelling storyteller in a Hearth gives one new Lorebook entry (from a pool); a lore collection hook. | any Hearth |

### 3.5 Warden rematches

- **The REMATCH table** (`world/events/rematch.inc`):
  - `{trainer_id, team_2, team_3, min_act_2, min_act_3}`, for about 40
    route wardens;
  - the rematch teams are levelled for the later acts.
- **Each dawn**, 3–5 beaten wardens whose act is reached become "ready"
  (`rematch_bits`).
  - A ready warden shows an EXCLAIM emote when you enter their map.
  - Their spotting line re-arms. This needs an engine hook:
    `trainer_is_beaten()` consults `events_rematch_ready()`. Ask plan 02
    for it, or add it in E10.
- **The REMATCH BOARD** in Maple and Lumen Hearths lists who is ready and
  where.
- **Hall Masters** rematch once all 6 crests are held (post-game), at
  levels 55–60, from their Hall; once per week (`day % 7`).

### 3.6 Festivals (calendar)

Derive a weekday from `gtime.day % 7` and the season from `time.c`:

| Festival | When | Where | What |
| --- | --- | --- | --- |
| KINDLING DAY | Spring 1 | Maple | Villagers gather at the Old Hearth; a cake; a free SUNSEED once a year. |
| MILLRACE | Summer 3 | Brookmill | A timed walk-race along the trail (a step counter against the clock); reward. |
| LANTERN NIGHT | Autumn 7, night | Duskmere, then the healed March | Lanterns float on the mire (palette anim); wisp kin appear. |
| FROST FAIR | Winter 5 | Frosthollow | Ice sculptures (decor via map patch); a sled race on the Rime Hall rink. |
| STARFALL | Any season, day 10, night | Stormstone Rise | Meteor shower; METEORB. |

Festival NPCs use `event = EV_FESTIVAL`, `arg = FEST_*`. The Gazette
announces them 2 days ahead.

### 3.7 World-state reactions (not rolled)

Things change as the story moves:

- **NPCs remember.** Signature NPCs in each town get one post-crest line and
  one post-finale line (E3 `show_flag`). Plan 11 owns the story NPCs; each
  region plan should add 2–3 of these in its own towns. This plan lists the
  requirement only.
- **Town growth.** Finished town projects (plan 10) change maps for good
  (E5 patches).
- **After the finale,** the March heals (plan 07) and the healed-season
  slots switch on.

---

## 4. The Vale Gazette

- **Where:** a board decor in every Hearth (MF_HEAL map), plus the
  printing clerk in the Lumen telegraph office (plan 03).
- **What it reads:**
  - the weather front;
  - the outbreak;
  - the caravan stop;
  - one happening;
  - rematch count;
  - the upcoming festival.
- **How:** up to 5 short lines, built by `events_gazette_line()` from
  templates with a `%s` place name. Keep each line ≤ 30 characters so it
  fits the dialog box.
- **START menu:** a GAZETTE row once the player has read the board once.
  Optional; talk to the UI owner.

---

## 5. Tests (`test_events.c`)

- **Determinism:** the same `(save_seed, day)` gives the same events across
  1000 days. Re-running `events_new_day` on the same day is a no-op.
- **Coverage:** over 200 simulated days every event kind fires at least
  once, and no event fires where its `min_act` isn't reached.
- **Safety:**
  - for every event's map patch, the progression solver (E6) still passes
    with the patch on;
  - washouts never touch critical-path cells: mark the critical cells, or
    run the solver with every event on.
- **Budgets:**
  - the worst-case NPC count with event NPCs visible stays ≤ 24 people and
    ≤ 7 sprites per map, at the worst time of day;
  - fog, snow and aurora art fits OBJ/BG budgets.
- **Save:** EventState round-trips; an old save without it loads with
  defaults and rolls today.

---

## 6. Order of work

1. `events.c` skeleton, EventState, the Gazette, weather fronts (STORM and
   FOG first).
2. Outbreaks, then the caravan.
3. Rematches (needs the engine hook).
4. Happenings and festivals.
5. Art: fog overlay, snow particles, aurora palette cycle.

**Handoff.** Write `docs/handoff/events.md`, with a table of every event and
how to add one.
