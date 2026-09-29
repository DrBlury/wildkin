# Guarded existing-area biome pass

This pass is applied to the regional source. The pinned manifest is retained as
an authoring/audit artifact, not as a runtime dependency. Gameplay documentation
is in [BIOMES.md](../../docs/BIOMES.md).

## What changed

Nineteen maps have individually authored terrain-material strokes and ten
settlement NPC conversations describe local customs. Brookmill Trail, Saltwind,
Frostpine and Moonveil additionally have solid terrain banks that interrupt old
straight lanes, tested detours, and clusters of existing compatible props.
`authored.py` records design intent; `guarded_spans.json` is the exact reviewed
source contract. The caravan clearing at Saltwind (12,12) and the cross-region
Field Notes guide at Brookmill Trail (20,16) remain clear.

## Safe authoring checks

```
python3 tools/biome_redesign/apply.py --check
python3 -m unittest discover -s tools/biome_redesign -p 'test_*.py'
```

`--check` is read-only. On the integrated tree it reports no pending changes.
`--apply` is idempotent but is not necessary on this tree. It preflights every
file, rejects overlapping edits, allows only the exact pinned collision changes,
and preserves unrelated same-file edits. Do not regenerate the original manifest
against a changed tree to bypass a conflict. `prepare_manifest.py` is a historical
pre-edit capture helper, not a routine build step.

The guards inspect placements across **all world regions**, because event and
story actors are not necessarily owned by the region containing their map.
They also check map dimensions, edge contracts and named route endpoints.
Static character checks alone cannot establish runtime elevation, NPC, story,
or puzzle reachability: the actual host tests remain required.

`test_biome_redesign.c` is included by `make test`. It checks decoded terrain,
newly blocked straight crossings, walkable detours, retained story anchors and
ten local-custom conversations. The Python tests reconstruct the pinned original
text **in memory**, so they work both before and after application without
rewriting game files.

Existing towns retain their established architecture and services. The remaining
fifteen maps receive contextual terrain/detail improvements rather than wholesale
collision-layout replacement; the twelve new biome maps carry the larger new
landscapes, settlements, native scenery and quests.
