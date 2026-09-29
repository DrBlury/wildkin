# Second-generation tile sets (tiles2)

A complete replacement for the overworld graphics: **16 area sets** of
16x16-cell pixel art (terrain, autotiles, cliffs, trees, buildings, props
and animations) with GBA-exact palettes, a JSON manifest per set, sample
maps for every area and an old→new name map for every decor kind and
building the current maps use.

**Status:** the game draws every field map with this art. All 16 of
`src/gfx_field.h`'s tilesets are built from these sheets by
`tools/tiles2/engine/` (section 8 describes how), so the maps, warps,
puzzles and scripts are unchanged while the terrain, trees, water, cliffs,
buildings and all 502 decor kinds come from tiles2.

- Sheets, manifests and sample maps: [`assets/tiles2/`](../assets/tiles2/README.md)
  (the README there has the per-set budget table and links every sheet)
- Generator: `tools/tiles2/` (Python 3 standard library only)
- Overview of every sample map: [`assets/tiles2/overview.png`](../assets/tiles2/overview.png)

```
python3 tools/tiles2/build.py [set ...]    # regenerate sheets, manifests, scenes (~45 s for all)
python3 tools/tiles2/test_tiles2.py        # budgets, geometry, legacy coverage (~5 s)
TILES2_REBUILD=1 python3 tools/tiles2/test_tiles2.py   # + byte-for-byte regeneration check
python3 tools/tiles2/gba.py verdant --entry tree        # encode one entry for the GBA
python3 tools/tiles2/legacy.py             # check every used old decor kind has a counterpart
```

---

## 1. The sets

| Set | Replaces | Areas | Look |
| --- | --- | --- | --- |
| `verdant` | `wild` | Whisper Meadow, Bramblewood, Mirror Lake, Stormstone Rise, Brookmill Trail, Copperline Road, Elderwood, Foothills, Mistfall Gorge, Rootwood Path | meadow grass, dirt trails, ponds and rivers, brown cliffs, oaks, pines, dense woods, camps, the old copper mine |
| `hamlet` | `town` | Maple Village, Brookmill, Mistbell | the verdant ground plus cobbled squares, cottages, houses, Hearth Hall, shop, mill and wheel, bell tower, gardens and street furniture |
| `farm` | `farm` | Willow Acre and the homestead views | tilled and watered soil, 8 crops x 4 growth stages, barn, silo, windmill, greenhouse, coop, hay, orchard |
| `coast` | `coast` | Sea Route, Saltwind, Port Brine, Gull Isle, Heron Fen, Reedwick, Coralhook Reef, Greywater Fjord | sand, surf, deep sea, fen marsh and mud, blue-grey fjord rock, docks, boats, lighthouse, reef life |
| `snow` | `snow` | Frostpine, Timberline, Frosthollow, Aurora Ridge, Whitecrown, Rimewind, Hot Spring, Sky Isle | wind-rippled snow, ice floors, cold lakes, snowy pines, log cabins with lit windows, hot springs, aurora stones |
| `cave` | `cave` | Glimmer Caverns, Copper Mine, Storm Cave, Starfall, Karst, Mill Cellar, Rootways, Sporelight, Tidal Underflow | rock floors, wall masses with lit faces, chasms, underground pools, crystals, glowcaps, mine rails |
| `volcanic` | `volcanic` | Caldera, Cindermoor, Cinder Crossing/Road, Ember Tunnel/Span, Railhead, Forge, Anvil Hall | ash, basalt, flowing lava, vents, obsidian, the ballast railway, brick forges and smokestacks |
| `desert` | `desert` | Saffron Dunes, Sunwell | rippled dunes, hard-pan, sandstone strata, oasis, palms, cacti, adobe, canopies, ruins |
| `jungle` | `jungle` | Rootcoil Jungle, Canopy Hearth (and Elderwood groves) | dark loam, mud trails, a teal river, buttress giants, broad leaves, bamboo, vines, woven stilt homes, temple ruins |
| `grim` | `grim` | Hollow Downs, Ashen Fields, Duskmere, Scorchwaste 2 | withered grass, cold stone and slate, the dark mere, barrows, graves, wisps, pumpkins, a ruined mill |
| `dusk` | `dusk` | Gravewood | purple-tinged woods, bog pools, gnarled trees, glowing toadstools, fog, graves, a mausoleum |
| `dream` | `dream` | Mistfen, Moonveil, Dreamspire, Dust Library, Mirror Hall | twilight grass, moonstone paths, a star-mist lake, moon lilies, crystal trees, marble spires |
| `crypt` | `crypt` | Barrows, Ossuaries, Lantern Crypt, Dusk Vault, Root Gallery, Waychapel, Bone Throne | dressed-stone walls, slab floors, carpet runners, braziers, sarcophagi, niches, the throne |
| `tide` | `tide` | Tidal Temple, Current Hall, Drowned Bell, Reed Tunnel | wet masonry, flooded channels, current floors in four directions, coral pillars, the drowned bell |
| `city` | `city` | Lumen | brick streets with tram rails, curbed pavements, a canal and arch bridges, townhouses, clock tower, station, works, electric lamps |
| `interior` | `interior` | every house, shop, hall, lodge and workshop | floors, four wallpapers over wainscot, windows, counters and ~90 pieces of furniture |

Palette variants re-colour a set without new tiles: `verdant` autumn and
spring, `hamlet` autumn and dusk, `farm` spring/autumn/winter, `coast`
storm, `snow` night, `cave` deep, `volcanic` eruption, `desert` dusk,
`jungle` dusk, `grim` night, `dusk` moonlit, `dream` dawn, `crypt` lit,
`tide` biolume, `city` night, `interior` evening. Each variant has its own
sheet (`<set>@<variant>.png`) and sample map render.

## 2. Style rules (what "good" means here)

1. **16x16 cells.** Everything is authored on a 16-pixel grid; larger
   things are several cells (a tree is 2x2, a house 4x4 to 8x6).
2. **Light from the upper left.** Forms get lighter towards the top-left
   and darker towards the bottom-right; roofs are lit at the ridge; furniture
   has a lit top and a darker front face (the GBA 3/4 look).
3. **Hue-shifted ramps.** Each material has 4-6 steps; shadows lean
   cooler and bluer, highlights warmer and yellower (`tools/tiles2/palettes.py`).
4. **Coloured outlines.** Objects are outlined with the darkest step of
   their own material, never pure black.
5. **Quiet ground, loud objects.** Ground textures are low-contrast
   clusters (tufts, pebbles, ripples); trees, buildings and props carry the
   contrast so people and paths read on top.
6. **Clusters, not noise.** Leaf clumps, lumps of rock, shingle rows;
   ordered dithering only at transitions and soft wisps (steam, fog).
7. **Tile-friendly textures.** Ground textures stay inside the cell (any
   two variants sit side by side); building textures repeat every 8 px so
   repeated wall and roof tiles deduplicate.
8. **Nothing from other franchises** (docs/WORLD.md section 9): the
   healing building is the **Hearth Hall** with a flame plate, statues show
   original kin (a fox-eared kin, a wolf, a salamander, a heron).

## 3. Files

```
assets/tiles2/
  README.md, overview.png, stats.json, legacy_map.json
  <set>/<set>.png                 sheet, 256 px wide, RGBA, colours exactly as the GBA shows them
  <set>/<set>.json                manifest (section 4)
  <set>/<set>@<variant>.png       the same sheet under a palette variant
  <set>/<set>_sheet_x3.png        labelled review sheet (sections, entry names, grid)
  <set>/scene_<key>.png           sample map at 1x (+ _x2 and @<variant>)
tools/tiles2/
  core.py      images of colour roles, noise, volumetric shading, PNG io, label font
  sheet.py     Sheet (layout, bank solver, encoder, manifest, review sheet) and Scene
  paint.py     ground textures, quad autotiles, foliage/clump shading
  terrain.py   paths, water, cliffs (rim, face, one-row face), ledges, stairs, cobbles, bricks
  flora.py     trees, conifers, dead trees, bushes, forest/hedge masses, tall grass, flowers
  props.py townprops.py buildings.py farmart.py coastart.py snowart.py caveart.py
  fireart.py desertart.py jungleart.py gothart.py dreamart.py dungeonart.py
  cityart.py interiorart.py extras.py   painters per theme
  kit.py       standard entry families (grass, path, water, cliffs, trees, rocks, outdoor, civic)
  palettes.py  shared ramps
  sets/<set>.py  one module per set: palette, bank plan, entries, sample map(s)
  build.py     builds everything, writes stats/README/overview/legacy map
  gba.py       loads a committed PNG + manifest and encodes it for the GBA
  legacy.py    old decor kinds / stamps -> new entries, checked against src/game/world
  test_tiles2.py
  engine/      the game's tilesets drawn from these sheets (section 8):
               assemble.py (recorder + builder), load.py (sheets as images),
               common.py (masses, cliffs, buildings, decor tables),
               art_<old set>.py (one per game tileset)
```

## 4. Formats

All coordinates are in cells of the sheet (16 cells wide). Every entry has
`name`, `kind`, `section`, `x`, `y`, `w`, `h` (cells), `layer`, optional
`doc`, `attrs` (engine attribute names from `A_*`), `group`/`weight`
(random ground variants), `frames` + `period` (animation), `tiles8`
(distinct 8x8 tiles it uses) and kind-specific fields.

### 4.1 `tile` - one opaque ground cell

Ground cells are fully opaque. Several tiles sharing a `group` are random
variants with integer `weight`s (like the engine's `LG_VARIANT` legend:
pick by cell hash). Example: `grass` (9), `grass_b` (4), `grass_c` (3),
`grass_d` (3), `grass_flowers` (1) all have `group: "grass"`.

### 4.2 `object` - W x H cells over the ground

Transparent where empty. Per-cell masks as strings, rows split by `/`:

- `solid` - blocks walking (default: every cell with pixels that is not
  `top` or `floor`),
- `top` - drawn **above** people (tree crowns, lamp heads, roof ridges),
- `floor` - walkable surface over water or void (bridges, stepping stones).

`layer` is `mid` (normal decor), `top` (entirely above people: vines, fog,
bunting) or `ground` (stairs, rugs, the waterfall: part of the floor).
Buildings carry `door: [col, row]`, the cell that is the entrance.
Farm crops carry `crop` and `stage`; current floors carry `dir`.

### 4.3 `autotile` (`format: "rmxp16"`) - quad autotile, 3x4 cells

The RPG Maker XP autotile layout at 16 px:

```
row 0:  [preview: lone cell] [alternative fill] [inner corners]
row 1:  [NW corner] [N edge] [NE corner]
row 2:  [W edge]    [fill]   [E edge]
row 3:  [SW corner] [S edge] [SE corner]
```

Every 16x16 cell is drawn from four 8x8 quadrants chosen exactly like
`autotile_quads()` in `src/game/field.c`. For quadrant `c` (0 TL, 1 TR,
2 BL, 3 BR), with `vs`/`hs`/`ds` = the vertical / horizontal / diagonal
neighbour on that quadrant's side is the same kind:

| engine variant | condition | take quadrant `c` from block cell |
| --- | --- | --- |
| 0 fill | vs and hs and ds | (1,2) fill (the scene renderer uses (1,0) for 1 in 4 fills) |
| 1 inner corner | vs and hs, not ds | (2,0) |
| 2 side edge | vs only | (0,2) for c = 0, 2; (2,2) for c = 1, 3 |
| 3 top/bottom edge | hs only | (1,1) for c = 0, 1; (1,3) for c = 2, 3 |
| 4 outer corner | neither | (0,1), (2,1), (0,3), (2,3) for c = 0..3 |

So `path_q[c][v]` / `water_q[c][v]` / `blend_q[...][c][v]` are
the 8x8 tile at those positions. `over` names the ground the outside of the
block is painted with (paths over grass, surf over sand); an autotile whose
`over` is another autotile (deep water in water, a hole in an ice sheet)
counts as that material's same-kind neighbour.

### 4.4 `patch9` - cell-resolution nine-slice, 5x3 cells

For masses whose borders need whole cells: forests, hedges, stone walls,
snowbanks, docks, cliff faces.

```
cols 0-2: 3x3 nine-slice (NW N NE / W fill E / SW S SE)
cols 3-4, rows 0-1: inner corners  [NW][NE] / [SW][SE]
cols 3-4, row 2:   [alternative fill] [lone cell]
```

Pick per cell from the four orthogonal neighbours (same kind or not):
column = W edge / middle / E edge, row = N edge / middle / S edge; when all
four are the same, a missing diagonal selects the matching inner corner.
Forests and hedges are transparent and belong on a **mass layer** over the
ground (scenes use `sc.set(x, y, 'forest', 'over')`); their south edge
shows trunks. The `cliff_face` patch9 rows are: top (under the rim),
middle (repeat for tall faces), foot (meeting the low ground); its ends are
rounded, cols 3-4 rows 0-1 are ends tucked against more plateau.

### 4.5 Blocks with their own layout (`kind: "block"`, see `format`)

| format | cells | layout |
| --- | --- | --- |
| `ledge` | 4x3 | row 0 south-facing [W end][mid][E end][single]; row 1 east-facing [N end][mid][S end][SE corner]; row 2 west-facing [N end][mid][S end][SW corner] |
| `strip4` | 4x1 | one-row cliff face [W end][mid][E end][lone column] |
| `fence` | 4x2 | row 0 [post][W end][mid][E end]; row 1 [N end][mid][S end][gate] (rail, picket, iron, railing) |
| `rails` | 4x2 | row 0 [E-W][N-S][curve S-E][curve S-W]; row 1 [curve N-E][curve N-W][buffer][crossing] |
| `railway` | 4x2 | ballast track: row 0 [E-W][N-S][W end][E end]; row 1 [N end][S end][crossing][buffer] |
| `tram` | 4x1 | rails in the street [E-W][N-S][crossing][stop] |

A single piece is addressed as `entry:col,row` (`fence:2,0` = a fence
middle), which is also how `legacy_map.json` names them.

### 4.6 Plateaus and cliffs

A raised area is drawn with two kinds: its cells use **`cliff_top`**
(rmxp16; the high ground with a rock rim on the N/W/E sides and a grass lip
on the south side that flows into the face texture), and the rows south of
it use **`cliff_face`** (patch9, 2+ rows) or **`cliff_face_single`** (one
row). This is the same model as docs/ELEVATION.md (one face row per level
of drop; faces south of the high cells; rims on the high cells): the rim
block supplies `ElevArt.rim`, the face pieces `ElevArt.face`, `stairs` /
`stairs_wide` the stairs, `bridge_h` / `bridge_v` the decks, `cave_mouth` /
`tunnel_arch` / `mine_mouth` the mouths and the `ledge` block the ledges.

### 4.7 Manifest top level

```
name, title, doc, cell (16), cols (16), rows
palette   {role: "#rrggbb"}          role names are what the art is drawn in
variants  {variant: {role: "#rrggbb"}}  only the roles that change
banks     [[role, ...] x <= 8]       palette bank b = these roles at indices 1..15
stats     {unique_tiles8, by_kind, entries, colours}
sections, entries, scenes
```

Colours in the PNG are already quantised to 5 bits per channel, so
`q15(hex)` of a palette entry equals the pixel value; `gba.load()` maps
pixels back to roles.

## 5. GBA budgets and how they are enforced

| Budget | Limit | Where it is checked |
| --- | --- | --- |
| palette banks per field | 8 (banks 0-7; UI owns 8-15) | `Sheet.solve_banks`, test |
| colours per bank | 15 (+ transparent index 0) | same |
| colours per 8x8 tile | all from **one** bank | encoder: every tile must fit a bank or the build fails and lists the entries |
| terrain catalogue | 1024 tile ids (10-bit) | `build.py`, test (`terrain_tiles8` in stats) |
| resident tiles per map | 768 (docs/AREA_TILESETS.md) | every sample map is counted (`resident_tiles8`) |

Each set module declares a **bank plan** (`BANKS`): one bank per material
family (ground + path, water + shore, cliff rock + grass, one per roof
colour with its walls/trim/glass, foliage + bark + fruit, props). The
solver fits every 8x8 tile into the plan and only adds banks if the plan
leaves room. When art does not fit, the build prints each offending colour
set and the entries that use it; the fix is to redraw that detail from the
bank's own colours (e.g. foundations and chimneys use the wall and trim
colours, the Hearth Hall flame plate covers whole tiles so its warm colours
can live in the props bank, the coast's flame borrows the red roof's warm
tones). Tiles are deduplicated with horizontal and vertical flips.

The sample maps are real budget checks: the village first needed 782
resident tiles with nine building types; the committed version stays at
728 by sharing textures. Designers should expect the same trade-off:
roughly 4-6 distinct buildings plus the area's usual props per map.

## 6. Area guide - composing "ideal" maps

Each sample map (`scene_*.png`, source in `tools/tiles2/sets/<set>.py`) is
the recipe. General rules that make them work:

- **Frame with masses, not rows of trees.** Use `forest` / `pine_forest` /
  `hedge` / `stone_wall` / `snowbank` on the mass layer for edges; place
  individual trees in small clusters of 2-3 inside the playable space.
- **Paths are 2-3 cells wide** and bend every 4-6 cells; one-cell paths
  read as ditches. Let paths reach doors (`door` cell of each building).
- **Water joins orthogonally.** Diagonal steps of one cell break an
  autotiled river; overlap each row with the next by at least one cell.
- **Height in steps of whole rows.** A plateau (`cliff_top`) needs its face
  rows directly south; put `stairs` in the face; use ledges for one-way
  drops on open ground.
- **Clusters of props tell stories**: a camp (tent, campfire, log, crate,
  woodpile on `dirt_patch`), a fishing spot (reeds, lily pads, rowboat,
  jetty), a market (stall, crates, sacks, lamps), a shrine clearing.
- **Sprinkle last.** Small walkable decor (`small_flowers`, `pebbles`,
  `fern`, `mushrooms`, `fallen_leaves`, shells, toadstools) at low density
  breaks up large ground areas; the scene helper `Scene.sprinkle()` never
  places it next to other objects.
- **Tall grass is habitat.** Encounter patches use `tallgrass_patch`
  (soft edges); keep them 3x3 or larger.

Per area:

| Set | Signature moves |
| --- | --- |
| verdant | winding trail, river with waterfall and bridge, hill with menhirs and stairs, lily pond with jetty, camp clearing, fenced cabin, copper mine (`mine_mouth`, `headframe`, `rails`, `ore_*`) on Copperline |
| hamlet | cobbled `plaza` with `fountain` + `statue` + stalls + lamps; houses of 2-3 roof colours; gardens behind `fence_picket` or `hedge`; the mill + `waterwheel` on a stream; `bell_tower` for Mistbell |
| farm | fields as `field` / `field_wet` patches with rows of `crop_*`, a `fence` paddock, barn + silo + windmill as a yard, orchard of `tree_fruit` / `tree_peach`; use the seasonal variants |
| coast | `sea` over `sand` with `deep_sea` beyond; `dock` on the mass layer over sand and sea; harbour buildings on grass above a `sand_patch` beach; `marsh` + `mud_patch` + `stilt_hut` + `reeds` for the fens; `sea_stack` / fjord cliffs for Greywater |
| snow | trodden `trail`s between cabins, `ice_patch` with an `ice_hole` lake, `snowbank` walls, `hot_spring` + `steam` under a cliff, cairns guiding the tundra, `night` variant for aurora maps |
| cave | wall masses as `cliff_top` over `rock_top` with faces; `chasm` + `rope_bridge`; `pool`; crystal/glowcap pockets for light; the `rails` gallery with `timber_frame` for mines; `deep` variant for lower levels |
| volcanic | lava rivers with `crust_patch` causeways, basalt cliffs, `vent` clusters, the `railway` along the town edge with depot/water tower/coal, forge district with `smokestack` + `smoke` |
| desert | oasis at the centre (`oasis`, palms, well, canopies), adobe homes around it, `dune_field` and `hardpan_patch` to break the sand, strata cliffs with ruins on top |
| jungle | a river through `loam`, `woven_hut`s on root decks, `rope_bridge`/`root_bridge`, `buttress_tree` landmarks, dense `forest`, understorey sprinkles (`fern`, `big_leaf`, `orchid`), temple `ruin_wall` + `idol` |
| grim | slate town on the `mere`, `memorial` lanterns along the shore, a walled graveyard with `wisp`s, barrows and the ruined windmill on the downs, `night` variant |
| dusk | winding `trail` through the gnarled `forest`, `bog` pools, graveyard with `iron_fence` and `mausoleum`, `fog` overlay tiles, glowing toadstools |
| dream | `path` of moonstone to the `spire`, columns and `moon_orb`s, the `mistlake`, `moon_lilies`, crystal trees, floating `pages` and `mote`s |
| crypt | halls as wall masses; a `carpet` nave to the `throne`; braziers and banners in pairs; side crypts with coffins, niches and a `pit` |
| tide | channels (`pool`) ringed by `current_*` floors that loop, the `drowned_bell` as centrepiece, coral pillars and shell lamps |
| city | streets of `road` with `tram` rails, `sidewalk` curbs, a `canal` with `railing` and `bridge`s, plaza with `fountain`, `clock_tower` and `beacon`, terraced `row_houses` and townhouses |
| interior | two wall rows (`wall_*_top`, `wall_*_low`) over the floor, windows and pictures on the wall rows, furniture against the back wall, a rug or carpet in the middle, the exit mat centred at the bottom |

## 7. Adding art

1. Painters take **role names** and ramps, not colours. Reuse a painter
   with another ramp before writing a new one (`kit.py` families do this
   for every set).
2. Add the entry in the set module (`S.tile`, `S.object`, `S.autotile`,
   `S.patch9`, `S.custom`), with masks, `attrs`, `doc`.
3. `python3 tools/tiles2/build.py <set>`; if a colour set fits no bank the
   build lists the entries: redraw them from one bank's roles or extend the
   plan.
4. Look at `<set>_sheet_x3.png` and the scene; add the piece to the sample
   map if it is a signature piece.
5. `python3 tools/tiles2/test_tiles2.py` and commit the regenerated assets
   (the rebuild test fails on stale files).

The generator is deterministic (integer hashes, no `random`), so a rebuild
produces identical bytes.

## 8. How the game uses them

`python3 tools/gen_field_gfx.py` (part of `make art`) still writes
`src/gfx_field.h`, but every tileset's art now comes from these sheets:

1. **Structure from the old builders, art from tiles2.** The old builders
   (`build_town`, `tools/tilesets/ts_*.py`) still run first; a recorder
   (`tools/tiles2/engine/assemble.py`, `Recorder`) captures what each one
   hands to `finish_tileset`: terrain names and order (the `MT_*` ids),
   legends, attributes, doors, stamps with their sizes, blend groups and
   the decor kinds the set offers. Maps and game code depend on all of
   that, so it stays exactly as it was. `assemble.build()` then rebuilds
   the tileset from an art module `tools/tiles2/engine/art_<set>.py`, which
   says, per old name, which tiles2 entry (or painter call, in the set's
   own colour roles) draws it.
2. **Colours.** Sheet pixels become colour names `T2:rrggbb` (the exact
   GBA colour), so the old encoder takes them as they are; a set's banks
   are its manifest banks. Composites that bake an object into a ground
   cell (a door mat on floorboards, a window in wallpaper) and blend edges
   use nearest-colour fitting (`('fit', img)`, `fit_bank_pix`).
3. **Forest masses** (`TilesetDef.mass_of / mass_pick / mass_meta`,
   `field.c mass_piece`). `TREE_TOP`/`TREE_BOTTOM` bands (and pines,
   gnarled trees, blossoms, jungle canopy, volcanic crags) are drawn as one
   canopy: each cell takes the piece its eight neighbours select, rendered
   ahead of time for every neighbourhood with the tiles2 forest painter
   (`common.forest_render`), deduplicated. A lone crown-over-trunk pair
   draws a young tree.
4. **Overlay stamps** (`field.c map_decode`). Buildings are transparent
   and drawn over whatever ground the map has under the stamp, like trees;
   only opaque stamps (a ring floor) are ground.
5. **Autotiles.** Paths, water (animated) and ground blends come from the
   sets' rmxp16 blocks (section 4.3 is the conversion); hand-placed 9-slice
   pieces the old maps use (`POOL_N`, `ICE_SE`, `LAVA_INW`...) are cut from
   the same blocks (`common.rmxp_piece`).
6. **Elevation** (`ElevArt`) is cut from `cliff_top` (rim = the block minus
   the plain ground), `cliff_face`, `cliff_face_single`, the `ledge` block
   and the bridges; sets without cliffs (`farm` has none, `city` paints
   them with the same cliff painters in paving stone).
7. **Tall grass** stays procedural (`tools/grass.py`), its styles remapped
   to each set's roles (`grass_colors`).
8. **Richer ground.** Legend entries hold up to 8 variants now; the main
   ground characters mix extra variants and baked-in details (flowers,
   pebbles, shells, ferns, dry tufts) at low density, so every map gains
   detail without any change to its data. New variants count wherever the
   ground they vary does (blends, ground flags: `variant_of`).
9. **Decor** keeps each kind's footprint and masks (collision and the
   over-people cells are unchanged); the art modules paint a version at
   the old size where the tiles2 entry is larger (`common.decor_table`).
10. **Paths through another ground.** A tileset may give a second path
    drawing for one other ground (`path_alt`: coast paths through sand,
    village lanes meeting the cobbled square); each path quadrant picks it
    when the neighbour its edge shows is that ground (`field.c
    autotile_quads`, `TilesetDef.path_alt_q / path_alt_of`).
11. **Interior wallpapers.** Rooms use four wallpapers: `W w n k p` (cream
    top, low wall, window, clock, picture), `B b N K P` (blue), `G g M C Y`
    (green), `R r O Q Z` (brick); `_` is a stone floor. Shops and offices
    are blue, homes green, workshops, inns and halls brick, Hearth Halls
    cream.
12. **Farm.** Soil and watered-soil quadrants come from the old
    `add_soil_quads` over tiles2 soil textures; crops tiles2 draws
    (turnip, carrot, pumpkin, tomato) use them, the others keep their old
    two-cell shapes recoloured into the farm's crop bank.

Budgets after the switch (`make test`, `test_area_tiles.c`): every map fits
its 768 resident tiles (peak 706); catalogues range from 55 (`tide`) to 606
(`city`) of the 1024 ids.

Not done yet: palette variants (seasons, night) are sheets only, the game
still tints with its own `field_tint`; outdoor map layouts are the old
ones (the art, the ground mixes and the interior wallpapers make them
richer; the full redesign in section 6 is still open); the old
generators keep owning the structure, so their art code cannot be deleted
until that structure moves into the art modules.

## 9. Validation

`python3 tools/tiles2/test_tiles2.py` checks, from the committed files
alone: all 16 sets present; <= 8 banks of <= 15 colours; every 8x8 tile of
every entry and frame fits a bank (full re-encode); palette variants encode
to the same tile count; terrain catalogue <= 1024; every sample map <= 768
resident tiles; entry geometry (names, masks, autotile / patch9 sizes,
opaque ground tiles); and that every old decor kind and building stamp the
current maps use resolves to a new entry. `TILES2_REBUILD=1` additionally
regenerates everything and requires byte-identical output.
