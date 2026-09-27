# 11 — Story, the rival, gate blockers and pacing

**Work package:** STORY.

**Needs:**

- plan 02 merged, including E3 (NPC conditions), E4 (scripted walking and
  camera) and E9 (quest stages);
- the region plans for the maps where you place people. You can start with
  Acts I–II as soon as plan 03 merges.

**Owns:**

- the new region directory `src/game/world/story/`, registered after `ui`
  and before `debug`: gate blockers, the rival, the Stillwardens, act
  transitions and story milestones;
- `src/game/world/village/` (the home area has no other plan). Two
  exceptions: plans 04 and 06 each make a one-line `link[]` edit in
  `village/maps.inc`, and the grim-owned `grim_keeper_talk()` hook stays
  where it is;
- `tools/tests/test_story.c`.

**Contract:** `01_progression_contract.md`: §3 acts, §4 G1, §5 levels.

**Voice:** follow `docs/WORLD.md`, especially the §4b glossary:

- kin **doze**, they don't faint;
- wardens, lanterns, **brimming**, the Kinship;
- nobody is hurt, ever.

Keep dialog pages ≤ 400 characters (`msg.c`), in the plain, warm tone of the
existing village scripts.

---

## 1. The spine: what the player is doing in each act

Every act has three beats:

1. **Hook**: who sends you and why.
2. **Turn**: something on the way changes the stakes.
3. **Hand-off**: the crest, and a pointer to the next act.

Pointers arrive as a **wire from Keeper Linden**. The Hearth Tender reads it
out when you next heal after a crest: `show_flag` crest, `hide_flag`
wire-read. That way the player is never lost and never forced back to
Maple. Two acts *do* bring you home on purpose (II → III and IV → V),
because Maple is the hub.

| Act | Hook | Turn | Hand-off |
| --- | --- | --- | --- |
| I Home | Kindling day; the storm grumbles (existing). | The rival's first bout, then Marlo's sash. | DRAKORA calmed. The Keeper: "Old kernels are stirring all over the Vale. The Wardens' Accord wants every warden it can get. Go east to Lumen; Fara holds the first crest." The road wardens step aside (G1). |
| II East | The road east, Brookmill, Lumen. | Lumen's lamps flicker every night: someone is **hushing** kin around the Volt Hall's resonators (Stillwardens, §3). Fara asks you to chase them off the roofs. | VOLT crest. A wire: "Port Brine's lighthouse is dark. The fen boardwalk is fixed, thanks to Brookmill." (G2). Home through Maple (the tram project gets offered). |
| III West | The lighthouse is dark: Stillwardens hushed the lighthouse kin at Saltwind. | At Port Brine, Maren explains why brimming matters at sea: the storm surges. The rival loses to Maren and sulks at the harbour. | TIDE crest. A wire: "The Cinder bridge is out, but a surfer can cross." (G3). |
| IV Forge | The Railhead miners are stuck behind the flood. | In the Ember Tunnel, the Stillwardens try to hush the Caldera. The first Stillwarden **lieutenant** bout. | ANVIL crest. A wire: "The Rise's ridge fell in the storm. Your STRENGTH could clear it, and Frosthollow is beyond." Home through Maple and the Rise. |
| V North | The climb; Timberline. | At Frosthollow, the aurora fails: Stillwardens in Glimmer Caverns. A **rival team-up** double bout against two lieutenants. | RIME crest (4 crests). A wire: "The Accord will open the March to you. Captain Audra waits south of Copperline." (G5). |
| VI Ash | The March in quarantine; the Waychapel. | Hollow kernels wake *faster* where the Stillwardens hushed wild kin: the surplus pools. The Stillwarden leader **VESTA HALE** is found at the barrows. A bout; she starts to doubt. The rival's lantern quest (§2). | LANTERN crest and the WARD LANTERN. A wire: "The Moonveil mist won't hold back a lantern like that." (G6). |
| VII Dream | Mistfen's pilgrims. | Vesta Hale at Dreamspire, now asking for help: the hush made the March worse, and OSSUREX is brimming. | DREAM crest (6 crests). The Keeper *in person* at the Duskmere gate: the Ossuary opens (G7). |
| VIII Finale | The Ossuary. | The last rival bout at the Ossuary door, as friends. | OSSUREX answered; the March heals; credits; the post-game (the Legend Trail, plan 10). |

**QUEST_HOLLOWING re-timing.** The stages exist; `grim/scripts.c` owns the
quest today.

- Map its stages onto the acts above. Stage 1 is given after DRAKORA and is
  renamed in the log to "THE WARDENS' ACCORD": earn crests.
- Grim keeps the Ossuary stages.
- Use E9's per-stage goal text: "Earn crests (2/6). Next: PORT BRINE." The
  marker is the next act's Hall town.
- Coordinate with plan 07: grim keeps `grim_keeper_talk()`, and this plan
  calls it, or replaces its text only.

---

## 2. The rival: SORREL

**Who:**

- **SORREL** is Keeper Linden's grandchild, Kindled the same morning.
- Always a step ahead, in a hurry to be the first to every Hall.
- They take the starter that is strong against yours (the classic
  triangle).
- Their arc: they learn that the Kinship is about the kin's rest, not the
  warden's crests.
- Use the existing overworld look pipeline (`tools/keeper_ow.py` /
  `keeper_cast.py`) for their sprite and bout portrait. One new cast entry.
- Pronouns in dialogue: they.

**Encounters.** Each is a `story` NPC with `show_flag` / `hide_flag` so they
appear once, walk up with E4 `npc_walk`, bout, and leave. "Levels" means the
lead kin; the team size grows.

| # | Act | Where | Team (lead Lv) | Beat |
| --- | --- | --- | --- | --- |
| 1 | I | Maple, after Kindling (outside the Almanac House) | 1 kin, Lv5 | "Let's see whose kin is better!" |
| 2 | I | Whisper Meadow, before the Rise | 2 kin, Lv11 | Racing you to DRAKORA; you get there first. |
| 3 | II | Brookmill Trail, east end | 3 kin, Lv15 | Already has the Brookmill stamp. |
| 4 | III | Port Brine harbour, after they lose to Maren | 4, Lv24 | Sulks; the first hint of the arc. |
| 5 | V | Glimmer Caverns | **double bout, with you** vs two Stillwarden lieutenants | Team-up; you share heals. The double bout already exists; the ally side needs checking with the bouts owner (plan 12 lists the risk). |
| 6 | VI | Gravewood, **RIVAL'S LOST LANTERN** | — | Sorrel pushed their lead kin too hard and it dozed deep and ran into Gravewood. Find it at night: a static encounter that follows you back, not a catch. Sorrel thanks you, changed. |
| 7 | VIII | The Ossuary door | 6 kin, Lv46 | A friendly last bout: "Go answer it. I'll hold the door." |
| post | — | The Rise, weekly | 6, Lv58 | Via plan 09's rematch table. |

**Rules:**

- A rival encounter is never a gate: each is skippable or unmissable only
  where it sits on a one-cell path. The team-up in Glimmer is optional:
  lieutenants move on after the Rime crest even if you skip it.
- **Test (`test_story.c`):** every rival NPC's show and hide flags make it
  appear in exactly one act window.

---

## 3. THE STILLWARDENS (a gentle antagonist thread)

**Premise.** Some people think bouts are cruel. The **Stillwardens** go
around *hushing* brimming kin with great bronze bells, so there are no
bouts. The result is the opposite of what they want: the surplus has
nowhere to go, the weather sours, and hollow kernels wake faster.

They aren't villains. They are wrong, and they come around. This fits
WORLD.md §3 ("Ignoring brimming kin is how wildfires start").

**Cast:**

- **Hushers** (grunt wardens, grey robes, a bell), 2–3 per act on routes.
  Put them in `world/story/trainers.inc` and place them on region maps.
  Their teams are calm kin: DREAM and DUSK, with hush-themed moves. Reuse
  moves; no new moves.
- **Two lieutenants,** BELLWRIGHT and MUFFLE. They appear in Acts IV and V.
- **VESTA HALE**, the leader, in Acts VI and VII.

**Beats:** see the act table (§1).

**Field effect** (uses plan 09): where Hushers stand, a route's wild kin
are *fewer but brimming more*. That is an E10 wild override with
`event = EV_HUSH`, active while the Husher is unbeaten on that map.

**Map needs:** none new. The barrows (plan 07) host Vesta's first bout. Ask
plan 07 for a free cell in `MAP_BARROW_A`.

**Scope switch.** If the thread is cut, the act turns fall back to natural
causes:

- a lamp fault, instead of the Lumen lamps being hushed;
- the Caldera brimming;
- the aurora failing because of a storm.

---

## 4. Gate blockers (G1) and act hand-offs

**G1 road wardens:**

- Two NPCs, `hide_flag = FLAG_STORM_CALMED`:
  - one at Bramblewood's east exit (y17–18), standing on the exit cells;
  - one at Mirror Lake's west exit (y31–32).
- Line: "Nobody leaves the valley while the sky grumbles. Keeper's orders."
- After the calm, a second NPC version (`show_flag`) stands to the side
  with a farewell line.
- **Rise north:** the rockslide (plan 06) blocks it physically. Add a sign
  and a Rise NPC who mentions it.
- **Wood south (Elderwood):** the existing boulder, plus the post-game gate
  (plan 03).

**Wires.**

- Wire texts live in `world/story/scripts.c`.
- The Tender's line in every Hearth checks "the newest crest whose wire is
  not yet read". This needs a hook in the Hearth script
  (`hearth_rest`/Tender) calling `story_hearth_talk()`.
- Ask plan 02 for the hook in the shared Tender script, or add it to E10's
  hook list.

**Milestones** (`world/story/milestones.inc`, for E6):

- `FLAG_STORM_CALMED` (G1);
- the wire flags;
- the rival flags (never required).

---

## 5. Maple as a hub (`world/village/`)

Maple is where the player returns most, so it should change the most:

- **Post-act lines.** Every named villager gets one line per act, via
  `show_flag` variants or a switch on the highest crest. Keep it cheap:
  one script per NPC, with a `story_act()` helper that returns 1–9.
- **Reserved lots:**
  - the **Market Hall** lot for plan 10 (an E5 patch; a fence-and-sign
    placeholder until built);
  - the **tram stop** cell by the Land Office.
- **The Hearth** hosts the **Gazette** board (plan 09) and the **rematch
  board**. Place the decor and leave cells free.
- **The Bout Ring:**
  - Marlo's post-game rematch;
  - a weekly "Ring night" tourney hook (plan 09, WARDEN TOURNEY).

---

## 6. Pacing rules

- **One new idea per act.** An ability, a traversal toy, a system (farm,
  craft, fusion) or a town project. Put system tutorials where they fit:
  - the farm, after Act I (Reeve);
  - crafting, in Act II (Brookmill's miller cooks);
  - fusion, in Act II at Lumen (the Resonance Works);
  - town projects, from the end of Act II.
- **Every 10–15 minutes of route,** something happens: a rival, a story
  beat, a landmark, a hamlet or a satchel cluster.
- **Never two gates in a row without a town.** Every act has a Hearth
  before its Hall. Hamlets have Hearths.
- **No backtracking without a shortcut or a reward.** Every forced return
  (II → III, IV → V) has either the tram or a one-way ledge, plus a quest
  payoff on the way.

---

## 7. Tests (`test_story.c`)

- **G1:** before `FLAG_STORM_CALMED`, only Act I maps are reachable (with
  E6). After it, Brookmill is.
- Every wire appears exactly once, in the right act window.
- **Rival and Stillwarden visibility windows:** at most one visible
  instance per act.
- **Budgets:** story NPCs added to region maps keep every map within 24
  people and 7 sprites, at the worst time and flag state.
- **Stillwarden teams:** levels fall within ±2 of contract §5 for their map.

**Handoff.** Write `docs/handoff/story.md`: the act table as built, and every
flag with its meaning.
