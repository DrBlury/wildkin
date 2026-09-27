# W-GRIM handoff: the Ashen March and the Hollowing

## Done

- **Tilesets.**
  - `ts_grim.py` builds (stamps are snapped to their banks by `fit_stamp`).
  - `ts_crypt.py` is the real crypt tileset (19 terrains, 59 tiles). It has
    walls, niches, bone walls, wisp cracks and flagstones, and bone dust (`,`,
    A_GRASS, so wild kin roam the Ossuary). It also has the maze BLOCK, a
    FAKE_BLOCK that looks like a block but is walkable, and a GHOST_FLOOR that
    looks like floor but is solid. Stairs up/down and an arch are door
    terrain; there is a pillar, a carpet and an exit mat. The legend is in the
    module docstring and at the top of `world/grim/data.h`.
- **Decor.** `decor_grim.py` has 26 kinds, registered in `all_decor()`:
  - grim: sign, grave, cross, iron fence, bones, shrub, stump, burnt cart,
    lantern post (flicker), wisp (walk-through), mire bell, mooring,
    pumpkin, the Burning memorial.
  - crypt: skulls, candles, sarcophagus, coffin, green-fire brazier, urn,
    hooded statue, banner, chains, the 3x3 BONE THRONE, the crest pedestal,
    a plaque.
- **Maps** (`world/grim/`). The edge contracts are kept and tested.
  - The outdoor maps are ASHEN FIELDS, GRAVEWOOD (with a fenced cemetery) and
    DUSKMERE (a stilt town on the mire). DUSKMERE has the Hearth, Shop,
    Apothecary, a house, the Lantern Crypt and the sealed Bone Gate.
  - Interiors: DUSK HEARTH HALL (MF_HEAL), DUSK SHOP, APOTHECARY and MIRE
    HOUSE (new id `MAP_DUSK_HOUSE`).
  - LANTERN CRYPT: a dark maze (MF_DARK). A ghost-floor gap tempts you and
    a false wall hides the way through; a test checks that the sanctum can
    only be reached through a false wall.
  - THE OSSUARY (2 floors, wild zones) and the BONE THRONE, with
    `OBJ(LEGEND, 8, 3, SP_OSSUREX)`, an OSSUARY mimic chest (arg 255) and
    berry patches 30-33.
- **People.** There are 29 NPCs: 14 wardens (all with 6 kin or fewer), and
  HALL MASTER MORWEN, a TT_MASTER bout through `battle_start_master` for
  `CREST_LANTERN`.
  - Other people: the gate warden, the bellkeeper, the surveyor, the ash
    farmer, the sexton, the mourner, her sister, the vigil keeper, the
    Dusk tender and clerk (with their own shop stock) and the brewer
    (SCR_BREWER from craft).
- **Story.** `grim_keeper_talk()` is the Keeper's post-DRAKORA beat (the
  Hollowing).
  - Quests: QUEST_HOLLOWING (stages 1-4 and 255), plus LIGHT FOR THE ASH and
    A LETTER TO THE MIRE.
  - The gate opens with all 6 crests (`field_begin_warp` to OSSUARY_1).
  - OSSUREX is a no-run legend bout at level party max + 3, clamped to 50-70.
    Winning or befriending it sets FLAG_OSSUREX_ANSWERED.
  - Lore: 13 entries (the HOLLOWING chapter plus places, types, halls and
    legends).
- **grim_healed / MF_ASH.**
  - `grim_ash_active(map)` returns MF_ASH && !grim_healed().
  - `field_load_palettes` applies `grim_ash_tint` (a violet-grey haze) while
    it is active.
  - `draw_weather` calls `grim_draw_ash` for falling ash flakes (OBJ tile
    640, emote palette).
  - Both switch off once OSSUREX is answered. NPCs of the March then talk
    about the rain.
- **Tests.** `tools/tests/test_grim.c` has 30 checks covering edges, zones,
  the crypt puzzle, the Keeper beat, the ash haze, the gate, Morwen and the
  crest, the OSSUREX loss and win, the heal, both side quests, the shop and
  the hearth.
- `make art && make && make test` is green, and the maps were checked in
  the real ROM with `build/shot` through the debug warp.

## Shared files edited (minimal)

- `tools/gen_field_gfx.py`: one line in `all_decor()` registers `decor_grim.DECOR`.
- `src/game/script.c`:
  - forward declarations of `grim_keeper_talk`, `grim_interact` and
    `grim_on_enter`
  - `keeper_after` calls `grim_keeper_talk()` before the Keeper's lore
  - `field_try_interact` calls `grim_interact()` just before
    `obj_interact()`
  - `field_on_enter` calls `grim_on_enter()`
- `src/game/field.c`: forward declarations of `grim_ash_active`,
  `grim_ash_tint` and `grim_draw_ash`. The ash tint goes in
  `field_load_palettes`, and `grim_draw_ash()` is called at the top of
  `draw_weather`.

## Left / for other owners

- **Traversal:**
  - Draw the OBJ_LEGEND OSSUREX on the throne, and hide it when
    `grim_legend_hidden(SP_OSSUREX)` is 1. The grim hook already handles the
    throne interaction before `obj_interact`.
  - The MF_DARK light circle for the LANTERN CRYPT and OSSUARY DEEPS.
  - The mimic chest (arg 255).
  - `travel.last_hearth` for DUSK HEARTH.
  - If traversal adds its own MF_ASH particles, call `grim_ash_active()` and
    drop `grim_draw_ash`.
- **Farm:** berry patches 30-33 (OBJ_BERRY in ASHEN FIELDS and GRAVEWOOD).
- **Craft:** place the CAULDRON decor in `MAP_APOTHECARY` next to the BREWER
  (x 5, y 3). BONE/DUSK LANTERNs are price 0, so the shop does not sell
  them; the story gives them.
- **Art polish:**
  - The stamps are still colour-snapped by `fit_stamp`; redrawing them
    natively in their banks would look cleaner.
  - The crypt floor is brick-like.
  - The March could use a small grim character set (only existing CHR_ are
    used).
- **Balance:** the levels assume the Lantern crest comes 5th (Ashen 24-31,
  Gravewood 27-34, crypt 34-41, Ossuary 39-48). Retune once the other Halls
  are levelled.
- **Base warnings:** `party.c` has 6 unused-function warnings from the UI
  branch, not from grim.

## Routes (REGION-GRIM plan 07, branch `plan-routes-grim`)

- Appended Grim map IDs for ACCORD CHECKPOINT (13x9), HOLLOW DOWNS (60x40), WAYCHAPEL (13x10), and two barrows (13x8); Ashen north now points to Downs. Copperline is deliberately untouched: East owns the south-edge doorway and removal of its direct Ashen edge. East chose Copperline door (20,34) instead of the plan default (20,35), landing at checkpoint (6,8); the reciprocal checkpoint door at (6,8) returns to Copperline (20,34), and Audra blocks the lane at (6,6).
- G5 currently uses a one-cell lane occupied by Captain Audra. Before `FLAG_RIME_CREST` she states the actual crest count and stays solid; afterward her conversation moves the player to Downs, and she can escort a returning player to Copperline. The physical gate and reversible route work locally, but E3 `hide_flag`/`show_flag` are not present at `ca6a672`, so the planned two-NPC visibility arrangement cannot compile yet. Quartermaster stock uses existing big tonics/hush bells/bone lanterns; IGNITER and TUNING FORK item IDs do not exist here.
- Downs has day/night wild slots (33–37), six wardens (34–37), a fly/heal stop, two hidden barrow entrances, a TRINKIT mimic, chalk-cairn candle quest with three persistent flags and three HUSH BELL reward, visible and hidden satchels, berry forage and lore. A walkable one-way bridge feature is declared; the region does not have a custom chalk-horse art asset or barrow stamps yet. The pilgrims are adjacent single wardens, not a double bout; current battle API is single-sided.
- Relevelled Ashen, Gravewood, Mire, Crypt/Morwen and Ossuary wild/warden tables for Act VI/VIII. Kept `grim_keeper_talk()`, existing G7 six-crest script and OSSUREX story hooks intact.

### Requests / integration blockers

1. **East**: keep its chosen Copperline checkpoint door at (20,34), landing checkpoint (6,8), and remove the old edge to Ashen. Until East merges, the old Copperline→Ashen link bypasses G5, and `tools/test_field.c` correctly fails its two-way link assertion.
2. **Engine E3**: implement NPC `show_flag`/`hide_flag` and flag-aware reachability so Audra can step aside and the desk Audra can appear after Rime. The old reachability flood reports the desk merchant and south exit unreachable because it starts from the Downs side of the guarded checkpoint. The guard *must not* be removed before this is resolved.
3. **Engine E5 / events**: no `MapPatch` fields or `map_patches_reapply` exist on `ca6a672`. Healing currently only removes ash tint/particles; grass/flowers and healed-season BLOOM slots require E5 and plan 09 event slots. The night CALCIPUP outbreak and ash-storm front also await plan 09.
4. **Item owner / integration**: no `items/grim.inc` or WARD LANTERN ID exists, and adding to shared item registries is outside this worktree's ownership. MORWEN still gives crest plus bone lanterns; register a new key item and field-use text, grant it in `morwen_end`, and wire G6 to the crest per plan 05. New item graphics also require the item owner.
5. **Links plan 08 — reserved reciprocal cave (explicit edits):** reserve **Duskmere (42,9)** on the east hill for the cave door, landing at **(41,9)**. It is east of Crypt Hall (x32–37), on height 2, and avoids the grave decor at (41,8) and (41,10). The row-9 approach is open from x38–42. `MAP_SCORCHWASTE_2` does not exist yet; adding a Grim warp now would not compile. After Links defines its map ID, place a visible cave-mouth tile/stamp or `OBJ_LADDER` at Duskmere (42,9), add `{ MAP_DUSKMERE, 42, 9, MAP_SCORCHWASTE_2, 2, 20 }` to `grim/warps.inc`, and add `{ MAP_SCORCHWASTE_2, 1, 20, MAP_DUSKMERE, 41, 9 }` to `links/warps.inc` (Links owns the latter). The proposed Links-side door (1,20) and landing (2,20) require Links confirmation. Enclose a pushable STRENGTH rockfall with a one-cell choke and a push bay west of (42,9); the current open hillside allows walking around bare boulders. Test both directions and inability to bypass Strength, with the Cindermoor heat vent gated by `FLAG_LANTERN_CREST` so the loop cannot bypass G5.
6. **Engine E1 integration**: `make test` regenerates `src/game/world/save_layout.inc` with new Grim counts; this generated file is out of scope, so the temporary change was restored. On merge, regenerate/review/accept the save layout and golden checks centrally. The E6 progression solver and its milestone registration do not exist yet; test the full graph after it merges.

### Validation

- `cc ... tools/tests/test_grim.c && /tmp/grim-test-plan`: passes including three-crest rejection, Rime admission, return path, barrow/candle persistence and existing MORWEN/G7/OSSUREX cases.
- `cc ... tools/test_field.c && /tmp/grim-field-plan`: row widths, tile budget, stamp/decor budgets, doors and edge landings pass; two assertions remain blocked: old Copperline edge violates two-way links until East merges, and guarded checkpoint makes its merchant/south exit unreachable from the Downs-side flood until E3 becomes flag-aware.
- `tools/tests/test_puzzles.c` (bounded 15s run): Hollow Downs reaches all 16 targets and Chalk Barrow reaches both; the checkpoint solver reports its Copperline side unreachable because it starts on the Downs side and does not model Audra's scripted flag transfer. The full suite timed out during the existing Anvil Hall search; it was not claimed green.
- `make test`: blocked by the two `test_field` assertions; generated save layout was restored to avoid an out-of-scope edit. `make art` not run because it rewrites generated files outside ownership. No in-ROM screenshots captured at this checkpoint.
