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
