# Energy and fusion: handoff

Owner: FUSION system (docs/EXPANSION.md 7.4). Gameplay is done and checked
in the ROM with the headless harness; `make art && make && make test` is
green (tools/tests/test_fusion.c: 71 checks).

## Done

- **src/game/fusion.c** (rules and screens):
  - **FusionState** (48 bytes, same size as the old stub so v4 saves still
    load): energy[18], pity, weaves, hits, unbound, mixes, flags
    (FZF_INTRO / UNBOUND / MIXED / WOVEN / WEAVED). Validate clamps it.
  - **Unbinding**: `8 + lv/2`, x1.5 rare and fusion, x4 legend, x2
    lustrous; dual types 60/40; fusion kin give their signature 50/50. Team
    or Shelf. The last awake team kin (or the only one) can't go. Legends and
    lustrous kin ask twice. The text names the kin's home wild zone (from
    WILD_ZONES, following its line back to the first stage).
  - **Mixing**: the 26-recipe table (MIX_RECIPES). Amount in steps of 10.
    The **tuner** minigame (pitch and phase knobs, 10 s timer, match meter)
    sets the yield 60..120%.
  - **Loom**: pick up to 3 types on a scrolling glyph strip, stake 10/30/60
    (L/R), START weaves. Chance `6 + 0/6/14 + 8*min/max + 3*pity`, 100% at
    25 misses; the candidates and the chance are always on screen. Hit:
    candidates weigh 3 when never owned, else 1; level 15/25/40; joins the
    team or the Shelf. Miss: 1/2/3 MOTE DUST and 30% of the stake back.
    Animation: orbiting motes, two reels behind the canvas, a white flash, and
    the kin scaling in with a spark shower.
  - **Screens**: WORKS hall (a cursor over the 4 machines), EXTRACTOR
    (portrait behind the dome, mosaic dissolve, motes stream into the flask,
    and the flask liquid in the type colours rises), ENERGY (18 pools, what
    makes each type and what it weaves), MIXER list, TUNER, LOOM.
  - **APIs**: `fusion_open(FUSION_SCREEN_MENU|UNBIND|MIX|LOOM|ENERGY)`,
    `fusion_key_use` (the ENERGY FLASK opens the energy screen),
    `fusion_energy(t)`, `fusion_energy_add(t, n)`,
    `fusion_tuner_open(title, done(yield))` (usable for craft's STATION_TUNE;
    on its own it returns to the field before calling done), and
    `fusion_examine(decor_kind)`.
- **world/fusion/**:
  - `scripts.c` SCR_FUSION_DESK: ENGINEER NELL explains once and gives the
    ENERGY FLASK, then offers MACHINES / CHAT / BYE (CHAT reveals LSRC_WORKS
    lore).
  - `npcs.inc`: NELL at MAP_RESONANCE_WORKS 8,5.
  - `data.h`: WORKS_DECOR (the 4 machines plus a plant).
  - Lore: 9 entries. LSRC_WORKS: RESONANCE WORKS, TYPED ENERGY, TUNING A
    MIX, THE FUSION LOOM, SIGNATURES. Story: UNBINDING (first unbind), THE
    MIXING TABLE (first mix, lists all 26), THE LOOM'S ODDS (first weave),
    WOVEN KIN (first fusion).
- **tools/decor_fusion.py**: FZ_EXTRACTOR, FZ_MIXER (2x2), FZ_LOOM (3x3) and
  FZ_TANKS (2x2), for interior banks 4 and 6. `fit_banks()` maps each
  quadrant onto one bank. It is registered in `gen_field_gfx.all_decor()`.
- **tools/icons/icons_fusion.py**: MOTE_DUST (items/fusion.inc uses it).
- **Scratch tools** (not committed): `build/make_fusion_save.c` writes a save
  standing in the Works (`intro` = desk done plus energy; `pity` = 25
  misses).

## Shared files I edited (expect merge conflicts)

- `tools/gen_field_gfx.py`: one line in `all_decor()` (decor_fusion).
- `src/game/world/east/maps.inc`: the MAP_RESONANCE_WORKS entry now points
  at `WORKS_DECOR, NDEC(WORKS_DECOR)`. The array is defined in
  world/fusion/data.h. If W-EAST redraws the room (11x9, walls in rows 0-1,
  door at 5,8), re-place the machines and NELL.
- `src/game/script.c` examine_cell: one line,
  `if (fusion_examine(p->kind)) return 1;`.
- `tools/test_field.c` map_entry: when no door or edge leads into a map (a
  placeholder interior), the reachability flood starts on the exit mat.
  Without this, any NPC in a placeholder interior fails the test.
- Regenerated: src/gfx_field.h, src/gfx_battle.h, src/game/world/debug/*.

## Left / known issues

- **No door leads into the RESONANCE WORKS yet.** W-EAST must add the Lumen
  door warp. To test now, use the DEBUG menu (WARP) or the scratch save.
- **Scene art quantisation.** The TUNER scene has a few purple stray cells
  by the knobs and the meter caps, and the other scenes have minor ones. The
  fix is in gen_fusion_gfx.py (force banks or add bank colours).
- **DMA to OBJ VRAM.** `copy32` (DMA3) of `fz_particle_gfx` left the tiles
  blank on hardware (mGBA), while the same DMA of the glyphs worked. The
  particles are now copied with a CPU loop. The cause was not found; watch
  for it elsewhere.
- **WORKS scene tanks** show fixed art, not your energy levels.
- **Opening the flask from the bag** goes through the UI owner's
  party-select flow (PCTX_ITEM_FIELD). Closing the energy screen returns to
  the field, not to the bag.
- **Balance** is untested in play: unbinding yields versus Loom stakes.
- **Pre-existing warnings**: party.c has unused-function warnings for Shelf
  helpers (UI's WIP). They were already on the base; none come from fusion.
