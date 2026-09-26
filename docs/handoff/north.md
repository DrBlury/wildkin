# North region: handoff (W-NORTH)

## Done

- **'snow' tileset** (`tools/tilesets/ts_snow.py`, 349 tiles): unchanged from
  the first pass (legend at the top of the file and of `world/north/data.h`).
- **'cave' tileset** (`tools/tilesets/ts_cave.py`, 113 tiles, 25 metatiles):
  floor (+ crystal grit, pebbles), glowmoss (A_GRASS, top layer), rock mass,
  wall face, crystal-vein wall, crystal outcrop, rock ledges, the exit mat
  (daylight + blown-in snow), void, animated underground lake (autotile),
  gravel path (autotile) and the Starfall starlit pool (numpad rim). Door
  stamps (1x1, walked into from the south): STAIRS_DOWN, STAIRS_UP, CRACK.
  Banks in `tools/north_palette.py` (CAVE_BANK_*; hs_ values untouched).
- **Cave decor registered** (`decor_north.NORTH_DECOR` now includes it).
- **Maps** (`src/game/world/north/`), all verified in the ROM with `build/shot`:
  FROSTPINE PASS (40x44), FROSTHOLLOW (40x36: Hearth, Shop, Rime Hall, 2
  houses, bathhouse, cave mouth, skating pond, plaza), WHITECROWN PEAK
  (32x40, switchbacks, ledges, the STRENGTH boulder corridor, summit),
  SKY ISLE (24x20, clouds, SKY_ARCH), RIME HALL (15x20 ice puzzle), HOT
  SPRING, FROST HEARTH HALL, FROST SHOP, THE ALDER HOUSE and STARGAZER'S HOUSE
  (two new map ids), GLIMMER CAVERNS (40x30, MF_DARK, lake + bridge),
  GLIMMER DEPTHS (36x28, MF_DARK, ledge loop), STARFALL GROTTO (24x20).
  Edge contracts kept: Frostpine south x 11-12 (Rise), Frostpine/Frosthollow
  and Frosthollow/Whitecrown at x 19-20.
- **Objects**: `OBJ(LEGEND, ..., SP_HOARFANG)` on the summit,
  `SP_SELENOTH` by the moth dais, `SP_SKYLORN` under the sky arch;
  `OBJ(BOULDER, 18, 9, 0)` in the Whitecrown corridor (push it WEST into the
  pocket at x 6-7, then go north at x 8); berry patches 20-24.
- **People**: 17 wardens (<= 6 kin each), Hall Master SIGRUN (6 FROST kin,
  `battle_start_master`, awards `CREST_RIME` + `FLAG_RIME_CREST` + story lore),
  tender (sets `travel.last_hearth`), Frost Shop (`shop_open_stock`), hall
  guide, ice carver, stargazer, grotto scholar, spring keeper (soak heals),
  spring cook (`SCR_CHEF`, craft owner), Granny Alder, villagers.
- **Wild zones**: FROSTPINE, WHITECROWN, GLIMMER, GLIMMER_DEEP (with
  WHEN_DAY / WHEN_NIGHT slots) and GLIMMER_LAKE as the caves' water_zone.
- **Lore**: 13 entries (places, legends, Rime Hall, aurora, snowflakes,
  winter coats, the crest). **Quests**: LAMPS FOR THE LONG NIGHT (3
  GLOWCAPS), THE STAR CHART. **Fly points**: FROSTHOLLOW, SKY ISLE.
- **Tests**: `tools/tests/test_north.c` (edges, Rime Hall slide solver,
  cave floor-to-floor reachability, boulder push, warden teams, lore
  sources, both quests, the Master bout and crest). `make art && make &&
  make test` green, no new warnings.

## Left

- Art review: BATHS stamp hot-spring mark, CLOUD vs CRAG, the starlit pool
  rim reads weakly in the ROM.
- The map rows were drawn with a scratch generator (not committed);
  `data.h` is now the source of truth, edit it directly.
- Depends on other systems: ice sliding / MF_DARK / OBJ_LEGEND /
  OBJ_BOULDER / OBJ_BERRY behaviour (traversal, farm), FLY to the Sky Isle.
  The core reachability flood ignores objects; once boulders are solid it
  needs a "puzzles solved" mode (the Whitecrown summit is behind one).
  Nothing at the summit is an NPC, satchel or sign, so only the legend
  object is behind the boulder.
- Sky Isle carries no NPCs, signs, satchels or warps (the core flood has no
  fly-point start).
- `WildSlot.when` is still ignored by `roll_wild` (time owner).

## Shared files edited

- None by hand. Regenerated: `src/gfx_field.h`, `src/game/world/debug/*`.
