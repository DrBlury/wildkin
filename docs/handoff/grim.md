# W-GRIM handoff: the Ashen March and the Hollowing

## Done

- The worktree branch was fast-forwarded onto the `expansion` base (6118872).
- `tools/decor_grim.py`: the grim and crypt colour tables, the palette bank plans
  (`GRIM_BANKS`, `CRYPT_BANKS`, 8 banks of 15 colours each) and drawing helpers
  (`seg_mask`, `shade_mask`, `outline_mask` and others). `DECOR = []` is still
  empty, and the module is not yet registered in `gen_field_gfx.all_decor()`.
- No maps, NPCs, story beats, puzzles, quests, lore or tests are finished.

## In progress

- `tools/tilesets/ts_grim.py` is drafted but **breaks `python3 tools/gen_field_gfx.py`**:
  - Drafted: the 26 terrains (ash and variants, dead grass, scorch, animated embers,
    cobble, Gravewood soil and bracken, mud, moss, reeds, deck); three overlay trees
    (gnarled oak, charred snag, swamp cypress); ash ledges and crags; the ash-road
    path autotile and the animated black-water autotile.
  - Drafted: six stamps (HOUSE, SHOP, APOTHECARY, HEARTH, CRYPT_HALL, BONE_GATE) and
    the legend. The legend is documented in the module docstring.
  - Failure: the error is `grim: tile HOUSE[0,0] ... fit no bank`. The ground baked
    into the stamps uses `grm_mud_hi` and `grm_moss_dk`, and those colours are not in
    the roof or stone banks.
  - Fix I had planned:
    1. Bake stamp ground with
       `MUD_A.replace({'grm_mud_hi': 'grm_mud', 'grm_moss_dk': 'grm_mud_dk'})`.
    2. In the stilt house, keep the timber wall at y 24-39 and span it across the full
       stamp width. Start the stilts (bank 5 colours only, no `grm_char`) at y 40, and
       end the door at y 39.
    3. Bank 5 becomes: out, rf x5, wd_hi, wd, wd_dk, mud, mud_dk, peat, lamp, lamp_hi,
       lamp_dk.
    4. Bank 7 becomes: out, wd x3, pl x3, lamp x3, gl, char, wisp_hi, wisp, cloth.
    5. Draw the name plates in bank 5 colours: `wd_hi` board with `grm_out` ink. There
       may be more bank conflicts after this, since the generator stops at the first one.

## Not started

- `ts_crypt.py`, and all decor: graves, iron fences, bone piles, burnt carts, wisps,
  fog, boardwalks, lanterns, sarcophagi, candles, the bone throne, plus apothecary
  interior pieces.
- All of `src/game/world/grim/`, which is still placeholders: the map rows (ASHEN
  FIELDS, GRAVEWOOD, DUSKMERE, the interiors, LANTERN CRYPT, OSSUARY 1 and 2, BONE
  THRONE), warps, NPCs, wardens, signs, satchels, wild zones, berry patches, the fly
  point, lore, quests, flags and scripts.
- The `keeper_after` post-storm branch in `src/game/script.c`.
- `tools/tests/test_grim.c`.

## Notes

- **Build and test status:**
  - `make` and `make test` are green, but only because `src/gfx_field.h` was not
    regenerated: the generator stops before it writes anything.
  - The art pipeline itself (`gen_field_gfx.py`) is broken until `ts_grim.py` is fixed,
    or reverted to the placeholder (`return gf.build_wild(name)`).
- **Edits outside the grim files:** none yet.
  - `keeper_after` is untouched.
  - The planned one-line registration in `all_decor()` is not added:
    `items += __import__('decor_grim').DECOR`.
- **Design decisions for whoever continues:**
  - **Ossuary gate:** a gate-warden NPC checks `travel_has_crest` for CREST_VOLT through
    CREST_DREAM. It lists what is missing, then calls `field_begin_warp` into
    OSSUARY_1. The gate stamp is solid, with no door. A sign on the gate cell explains
    the seal. OSSUARY_1 exits through a STAIRS_UP door cell that has its own warp back
    to DUSKMERE. An exit mat would not work there: it would pick the OSSUARY_2 warp.
  - **Finale:** a vigil NPC at the BONE THRONE plays the scene and starts the OSSUREX
    bout, with no run and a level-scaled team. The bout's end hook sets the answered
    and healed flags.
  - **Legend object:** `OBJ(LEGEND, x, y, SP_OSSUREX)` sits on the throne. Traversal
    should defer to grim, through a proposed `grim_legend_interact(species)` and
    `grim_legend_answered(species, result)`.
  - **Lantern Crypt:** FAKE walls look solid but are walkable. GHOST floor looks
    walkable but is solid. Wardens stand in alcoves: people block the flood fill, so a
    warden in a corridor would block it.
- **APIs to expose (not written yet):** `grim_healed()` and
  `grim_ash_active(map) = (MAPS[map].flags & MF_ASH) && !grim_healed()`, both in
  `world/grim/scripts.c`. They are included after `field.c` and `time.c`, so the
  traversal and time owners need a forward declaration
  `static int grim_healed(void);` before their MF_ASH check.
- **Other APIs relied on:** `quest_set`, `travel_has_crest` / `travel_award_crest`,
  `shop_open_stock`, `SCR_BREWER` (craft), `OBJ_CHEST` mimics and `OBJ_LEGEND` (traversal).
