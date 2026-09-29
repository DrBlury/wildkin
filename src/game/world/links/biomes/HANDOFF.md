# Integrated frontier authoring notes

These fragments are included at the end of the owning links/west/north regional
lists. `data.h` includes `data_extra.h` exactly once. The save-manifest generator
follows region-local includes in compiler order; append new IDs and do not reorder
existing entries.

Parent entrances and clear return pads:

| Parent | Entrance | Return | Gate |
| --- | --- | --- | --- |
| Scorchwaste | 40,16 | 39,16 | Lantern |
| Sea Route | 10,30 | 10,29 | Tide |
| Aurora Crest | 44,14 | 45,14 | Rime |
| Glimmer Caverns | 11,17 | 12,17 | Rime |

The parent object lists contain visible ladder markers; each outdoor/cave portal
has an explicit guarded reciprocal warp. Use ordinary floor underneath these
ladders, **not an A_EXIT glyph**. The Cistern is a single-room interior: its exit
mat returns through its incoming Sunwell doorway using the normal engine handler,
without an unused reverse warp entry.

`tools/tests/test_biome_frontiers.c` exercises geometry, landings, inherited gates,
real movement, encounter/reward access, resident art, and irrigation cancellation,
missing materials, full reward stacks, success, repeated claims and persistence.
`test_biome_integration.c` additionally drives actual trainer battle entry and
field return across the new wilderness routes.

See `docs/BIOMES.md` for the player-facing journeys and
`tools/capture_biomes.py` for reproducible, memory-verified ROM captures.
