# W-EAST handoff (Copperline Road, Lumen City, Volt Hall, lairs)

## Done

- **City tileset** (`tools/tilesets/ts_city.py`), 310 tiles, which leaves
  about 200 scene tiles for decor on LUMEN CITY. It contains:
  - Ground: flagstone pavement `.` (with a drain-grate variant), cobbled
    streets `=` (autotiled with kerbs), a stone-rimmed animated canal `~`,
    plain cobbles `c`, sandstone plaza `p`, lawn `g`, park wild grass `,`,
    flower beds `r` and `y`, overlay trees `T` and `t`, and the old city
    wall `#` (top) and `w` (face).
  - Buildings are stamps built from shared modular parts:
    - Roofs: terracotta, copper-patina standing seam and slate.
    - Walls: plaster, brick and dressed stone.
    - Details: windows, wooden and glass doors, shop windows, awnings,
      portico columns, and a variable-width sign font.
  - Stamps (`STAMP(CY, NAME, x, y)`, doors listed in `DOORS`):

    | stamp | size | door (col, row) |
    | --- | --- | --- |
    | HEARTH | 6x4 | 3,3 |
    | MARKET | 8x4 | 4,3 |
    | VOLT_HALL | 9x5 | 4,4 |
    | WORKS | 8x4 | 3,3 |
    | BIKE_SHOP | 5x4 | 3,3 |
    | INN ("KETTLE INN") | 6x4 | 3,3 |
    | HOUSE_A | 5x4 | 2,3 |
    | HOUSE_B | 5x4 | 2,3 |
    | HOUSE_C | 4x4 | 1,3 |
    | ROW_HOUSES | 7x4 | 1,3 and 5,3 |
    | CLOCK_TOWER (foot of the Clockwork Spire) | 3x6 | 1,5 |

  - `USES_DECOR` pulls 25 existing props into the city (bench, market
    stall, hedge, lantern post and others).
  - `python3 tools/gen_field_gfx.py` was re-run, so `src/gfx_field.h` and
    the debug viewer maps are regenerated. The art lint passes.
- **Volt Hall puzzle design**, verified with a BFS (not in the repo yet).
  - The map is 15x17 in the interior tileset. `P` is a pylon (a solid decor
    kind that still has to be drawn), `A`/`B`/`C` are
    `OBJ(BARRIER, x, y, 0/1/2)`, `a`/`b`/`c` are `OBJ(SWITCH, x, y, 0/1/2)`,
    `X` is a warden, `M` is the master and `D` is the entrance mat:
    ```
    WWWWWWnWnWWWWWW
    wwwwwwwwwwwwwww
    :::::::M:::::::
    :::::::::::::::
    PPPPPPPCPPPPPPP
    :::::::::::X:::
    :::::b:::::::::
    PBPPPPPPPPPPPAP
    ::::X::P:::::::
    :::b:::P:::c:::
    :::::::P:X:::::
    PPAPPPPPPPPPBPP
    :::::::::::::::
    ::::a:::::X::::
    :::::::::::::::
    :::::::::::::::
    :::::::D:::::::
    ```
  - Solution: press a (4,13), then b (3,9), then c (11,9). That is 45 steps.
  - There are 982 reachable states and none of them is a soft-lock. The
    master cannot be reached without using a switch.
  - The switch at (5,6) is a trap: it toggles B again.

## In progress

- Nothing half-written is in the tree. The only file that changed in the
  repo is `ts_city.py`, plus the art it generates.

## Not started

- `tools/decor_east.py` and its one-line registration in
  `gen_field_gfx.all_decor()`. Planned kinds:
  - City: city lamp, tesla coil, stone canal bridges, railing, planter,
    spire roof (3x3, to sit on CLOCK_TOWER), chimney, telegraph pole and
    wire, cafe table, parked bike.
  - Copperline Road: mine entrance, rails, ore cart, ore pile, headframe,
    copper rock.
  - Elderwood Heart: elder tree, fern, glowcaps, stag altar, root arch.
  - Interiors: resonance coil, energy vat, pylon, dynamo, bike display,
    spire gears, file cabinet.
- All maps are still the placeholders from the base commit: COPPERLINE
  ROAD, LUMEN CITY, ELDERWOOD HEART, the Land Office, and the interiors
  (the Lumen hearth, market, VOLT HALL, RESONANCE WORKS, bike shop,
  houses, inn and CLOCKWORK SPIRE).
- Not written yet:
  - Region content: NPCs, wardens, signs, satchels, zones, scripts,
    flags, quests, lore, fly point and berry patches.
  - The Land Office building in Maple Village.
  - The STRENGTH boulders on Bramblewood.
  - `tools/tests/test_east.c`.
- Planned people and extras:
  - Hall master MASTER FARA, a SPARK team at levels 20-23.
  - A hall guide who reveals lore.
  - SCR_TENDER in the hearth hall.
  - A market script using `shop_open_stock`.
  - SCR_FUSION_DESK in the Works.
  - A BIKE errand quest that ends with `give_item(ITEM_BIKE, 1)`.
  - SCR_CHEF in the inn.
  - SCR_REEVE in the Land Office.
  - `OBJ(LEGEND, ..., SP_SYLVARCH)` in Elderwood and
    `OBJ(LEGEND, ..., SP_HOROLOGOS)` in the Spire.
  - Wild species for Copperline (E1): STATICKO, MAGNITICK, RIVETILLO,
    RACCOIN, FLYSQUIRL, QUILLDRUM, MANDRAGOR, BEACONFLY at night, and
    FULGECKO as the rare.

## Notes

- **Branch base.** This worktree was created on `main` (89bf1cb). I
  fast-forwarded it to the expansion base (6118872) with
  `git merge --ff-only`, because the contract files only exist there.
- **Tests.** `tools/tests/test_core.c` passes with the new city tileset. I
  did not run the full `make test` or `make`.
- **Edits outside my folder.** None yet. The generated files
  `src/gfx_field.h` and `src/game/world/debug/*` changed because I re-ran
  the generator.
- **`tools/render_maps.py` is broken on the expansion base.** It fails with
  `KeyError: 'city'` and still reads the old `src/game/maps.h`. As a
  workaround I wrote a host renderer (it stays in my scratchpad, not the
  repo). It includes `src/main.c` the way the tests do, and for every
  16x16 block calls `map_load`, `field_load_tileset` and `render_cell`. It
  then composites the BG0, BG2 and BG3 screenblocks from host VRAM with
  `bg_palette`, draws NPCs from `char_gfx`/`char_palettes`, and writes a
  PNG with zlib. The output is pixel-exact and worth adding to `tools/`.
- **APIs I expect from other systems:**
  - Traversal: `OBJ_SWITCH` with arg = group toggles every `OBJ_BARRIER`
    with the same arg on the map. All barriers start raised and solid.
  - Traversal: `OBJ_BOULDER` is solid until pushed with STRENGTH.
  - Traversal: `OBJ_LEGEND` with arg = species starts a static legend
    bout.
  - Traversal: `travel_award_crest(CREST_VOLT)`.
  - Battle: `TrainerTeam` only holds 3 kin (`team_from` copies 3), so a
    6-kin hall master fights with 3 until the battle owner widens it.
  - Farm: `OBJ_BERRY` with arg = patch id.
- **Budget.** City tiles plus the decor LUMEN CITY uses must stay at or
  under 512. That leaves about 200 tiles for city decor, so keep new city
  decor small.
