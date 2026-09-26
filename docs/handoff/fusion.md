# Energy and fusion: handoff (WIP)

Owner: FUSION system (docs/EXPANSION.md 7.4). The work stopped early, at the
art-generator stage. The gameplay code is still the base stub.

## Done

- `tools/gen_fusion_gfx.py` runs and writes `src/gfx_fusion.h`. It uses the
  standard library only and gives the same output every run. Run it with
  `--preview DIR` to get PNGs. The header holds:
  - 18 type-energy glyphs (16x16). The disc colours come from
    `gen_ui_gfx.TYPE_COLORS`. There are three 16-colour palettes:
    0 transparent, 1 white, 2 ink, 3 grey, then each type's fill at
    `4+2k` and its dark at `5+2k`.
  - `fz_type_ramp[18][4]`: glow, light, fill and dark for each type.
  - Particle tiles (dot, soft mote, orb, sparkle) in two index sets:
    ramp A uses indices 1..4 and ramp B uses 5..8. There is also a cursor
    corner tile and `fz_sin[256]`.
  - Four full-screen canvas scenes: WORKS (hall), EXTRACT (dome and
    flask), LOOM (ring and 2 reel windows) and TUNER (oscilloscope). Each
    8x8 cell is quantised to one of BG banks 3..7. Banks 3..6 are shared:
    structure, brass, heartglass and glass. Bank 7 belongs to each scene.
  - Geometry defines: dome, flask mouth, flask inner spans, loom centre,
    sockets, reels, CRT, timer, meter and knobs.
- The worktree branch now starts from `expansion` (6118872). It started at
  the older 89bf1cb.

## In progress

- Scene art is first-pass only. It has not been checked in a ROM
  screenshot. The quantiser remaps about 2-3k pixels per scene to its
  cell's bank. Add bank-friendly colours, or force banks, and look at the
  preview PNGs.
- Only the generator writes `src/gfx_fusion.h`. Nothing wires it in yet:
  - `src/main.c` needs the include after `gfx_battle.h`.
  - The `Makefile` needs it in `ART` and in the `art` target.
  - The CI diff list in `.github/workflows/build.yml` needs it too.

## Not started

- All of `fusion.c` gameplay:
  - **Unbinding.** Energy is `8+lv/2`, x1.5 for rare (and fusion), x4 for
    legend, x2 for lustrous. Dual types split 60/40. Fusion kin return
    their signature types (planned 50/50). You can't unbind your last
    healthy team kin. Legends and lustrous kin need a double confirm.
  - **Energy screen:** the 18 energy pools.
  - **Mixing and the tuning minigame.**
  - **Loom:** odds, pity, candidates, the hit and miss animations.
  - **The Works menu.**
  - **FusionState:** planned fields are energy[18], pity, weaves, hits,
    flags and pad (at most 256 bytes).
- The `scr_fusion_desk` script: the clerk explains once, gives the ENERGY
  FLASK, then shows MACHINES / CHAT / BYE.
- Lore: 7 planned `LCH_ENERGY` entries, with `LSRC_WORKS` plus story
  moments.
- Icons (`tools/icons/icons_fusion.py`): MOTE_DUST and ENERGY_FLASK. The
  `key.inc` icon line also needs updating.
- `tools/decor_fusion.py` (EXTRACTOR, MIXER, LOOM, TANKS). Use interior
  banks 4 and 6 only, with brass as gd_* plus hg_*. Add one line to
  `all_decor()`.
- `tools/tests/test_fusion.c`.

### The designed mixing table (26 recipes, unordered pairs)

Every type is the output of some recipe. Starting from BEAST, BLAZE, TIDE,
BLOOM, SPARK, GALE and STONE, mixing reaches all 18 types.

| Inputs | Output | Name |
| --- | --- | --- |
| BLAZE + TIDE | GALE | STEAM |
| SPARK + STONE | METAL | SMELTING |
| HOLLOW + DREAM | RELIC | MEMORY |
| BLOOM + DUSK | VENOM | ROT |
| BLOOM + BRAWL | BEAST | GRAZING |
| VENOM + GALE | BLAZE | MARSH GAS |
| SPARK + BLOOM | BLAZE | WILDFIRE |
| FROST + BLAZE | TIDE | MELT |
| TIDE + STONE | BLOOM | SOIL |
| GALE + FROST | SPARK | STORMCLOUD |
| DUSK + TIDE | FROST | HOARFROST |
| STONE + BEAST | BRAWL | HAULING |
| SWARM + TIDE | STONE | REEF |
| METAL + TIDE | STONE | RUST |
| HOLLOW + TIDE | STONE | FOSSIL |
| SWARM + SPARK | DREAM | NEURONS |
| BEAST + DUSK | DREAM | SLUMBER |
| RELIC + SPARK | DREAM | ECHO |
| BLOOM + GALE | SWARM | POLLEN |
| BLAZE + BLOOM | DUSK | CHARCOAL |
| GALE + TIDE | WYRM | STORM |
| BEAST + VENOM | HOLLOW | DECAY |
| WYRM + STONE | HOLLOW | DEEP TIME |
| METAL + BRAWL | RELIC | HANDWORK |
| ASTRAL + STONE | METAL | METEORITE |
| SPARK + DUSK | ASTRAL | AURORA |

- **Mixing:** n of A plus n of B gives `n * yield / 100` of C. The yield is
  60..120%, from the tuning meter.
- **Loom chance:** `6 + stake bonus + harmony + 3 * pity`.
  - The stake bonus is 0, 6 or 14 for stakes of 10, 30 or 60 units per
    picked type.
  - Harmony is `8 * min / max` of the picked stores.
  - The chance is 100% once pity reaches 25.
- **Loom results:**
  - The new kin's level is 15, 25 or 40, by stake.
  - A hit is weighted: 3 for a kin you have not caught, 1 for one you
    have.
  - A miss gives 1, 2 or 3 MOTE DUST and refunds 30% per type.

## APIs other owners should call (planned; only the stubs exist today)

- `fusion_open(FUSION_SCREEN_MENU | _UNBIND | _MIX | _LOOM)`. The Works NPC
  script calls this. `FUSION_SCREEN_ENERGY` is planned to be appended.
- `fusion_key_use(KEY_ENERGY_FLASK)`. `modules.c` already dispatches it.
- Planned: `fusion_energy(type)` and `fusion_energy_add(type, n)` for quest
  and craft rewards. A reusable tuning minigame could serve craft's
  STATION_TUNE.
- W-EAST places an NPC with `SCR_FUSION_DESK` in the RESONANCE WORKS.

## Notes

- **Build and tests.** `make` and `make test` pass at this commit (the
  baseline had 243 ok checks). The new header is not included anywhere
  yet, so it changes nothing.
- **Edits outside my files:** none so far. The only new files are
  `tools/gen_fusion_gfx.py`, `src/gfx_fusion.h` and this note.
- **Planned VRAM and palette layout for the fusion screens:**
  - BG banks 0..2 hold the glyph palettes and 3..7 the scene palettes.
    `field_return` reloads 0..7.
  - OBJ tiles 640..767 hold the glyphs and particles. `OT_MON_A` and
    `OT_MON_B` hold the portrait and silhouette.
  - OBJ banks 1..7 and 9..14 are free. Never touch 0, 8 or 15.
- **Pitfalls:**
  - Put reel glyph sprites at OBJ priority 1, behind BG1. They then show
    only through the transparent holes in the LOOM scene.
  - Text on scene art needs index 1 = white and 2 = ink. Every scene bank
    keeps them.
  - A dialog clears rows 14..19 to transparent, so redraw the screen after
    it.
  - With `-Wall`, C warns about unused static consts. The header marks
    them `GFX_FUSION_UNUSED`.
