# Handoff: fusion kin 130-151 (KIN-D)

Files: `tools/kin/fusion_a.py` (data), `tools/kin/art_fusion_a.py` (art).
Generated headers are up to date: `src/species_data.h`, `src/gfx_monsters.h`.

## Done

Data and art for 130-137. Each has a model function in `art_fusion_a.py`
and `model=art.<name>` in `fusion_a.py`:

- 130 STEAMOTH: hawk-moth with steam-glass wings on brass ribs, a copper boiler thorax with a firebox glow, and exhaust puffs.
- 131 VOLTORTLE: basalt tortoise with a copper lightning rod, glowing grounding seams and a grounding chain on its tail.
- 132 EMBERIME: fox split down the middle (ember left, rime right), with a flame tail and a frost tail and mismatched eyes.
- 133 OSSIFLORA: bone deer whose ribcage is a flowerbed, with blossom-crowned antlers and green glow in its skull.
- 134 COGHIVE: clockwork queen bee rising out of a riveted iron skep on six legs, with a cog crown and orbiting wind-up drones.
- 135 HOARDWYRM: violet wyrm armoured in coin scales with a gem ridge, coiled on a coin heap; it wears a crown on one horn and holds a goblet in its tail.
- 136 STARSQUID: tall star-speckled squid with arrow fins, trailing pink nebula ink.
- 137 VOLTSHARK: leaping navy shark with lightning flank stripes and a three-blade copper turbine on its dorsal fin.

## In progress

138-151 have final data: stats, learnset, traits, field abilities, category
and description. All of it validates. They have no art yet: `model=None`, so
the generic placeholder sprite is drawn. Planned art briefs:

- 138 DULLAHAN: charcoal horse with bone rib markings, a smoky mane and ghost-flame hooves. The neck ends in a stump of pale spectral fire. A bone crook rising from its back hangs a lantern (the "head") in front of the stump. Use `g.lantern` with a ghost-green glow and two dark eye slits.
- 139 CHIMERAX: tawny lion with a shaggy venom-purple mane, goat horns (`g.curl_horn`) and a goat beard. Its tail is a green serpent with its own head and fangs.
- 140 RIDDLEON: sandstone cat lying in the sphinx pose. Folded stone wings with lapis tips, spiral stone "question-mark" curls at the sides of the face, a pink third-eye gem, and a floating ring of glowing rune tiles.
- 141 GRIFFALON: falcon-headed (peregrine) lion with large slate-blue wings. The front half is feathered with talons, the rear is a tawny lion with a tufted tail. Set `overworld(g, m, side_yaw=-62)`.
- 142 MANTICLAW: upright crimson lion boxer with wrapped fists and a quill mane. A scorpion tail arches overhead to a purple stinger with a green drop.
- 143 INKRAKEN: squat, wide, ink-black octopus with a curled hood tip and big teal glowing eyes. Thick arms curl outward and ink droplets hang around it. It must read clearly apart from the tall STARSQUID.
- 144 OBSIDRAKE: low, heavy quadruped drake of glossy black glass (spec highlights). Shard ridge, knapped-blade folded wings, violet glowing seams.
- 145 AURORELK: snowy elk with a star-speckled night saddle and a frost dewlap. Palmate antlers of emissive aurora ribbons, green grading to violet.
- 146 RAIJUKO: storm-navy weasel in a leaping arch. Cyan-white zigzag lightning mane, a forked bolt tail and two orbiting ball-lightning orbs.
- 147 SPOREGHOUL: gaunt, hunched ghoul in a tattered shroud with long bony arms. A huge purple spotted mushroom cap acts as a hood, with glowing green gills and eyes underneath. Small mushrooms sprout on its shoulders, and spores drift around it.
- 148 CLOCKOWL: round steel owl with an ivory clock face on its chest (ticks, hands, brass bezel), gear-tooth ear tufts, pink dream eyes and a pendulum tail.
- 149 CINDERANT: dark chitin fire ant with ember-ringed gaster, big mandibles and glowing seams, with tiny ants crawling over the armour.
- 150 STARWEAVER: indigo spider with a spiral-galaxy abdomen and eight long legs, hanging in a web whose knots are stars joined into a constellation. Silk tubes need radius of at least ~0.45 or they vanish. Use sparkle decals for the stars.
- 151 NOSFERBAT: upright bat noble whose wing membranes form a high-collared cape with crimson lining. Pale bone mask face, fangs, big ears, a ruby brooch.

## Not started

None. Every id has final data; the missing piece is art for 138-151.

## Notes

- Build and tests: `make` builds and `check_rom` passes. `make test` reports all field, game and core checks passed. Both were run after regenerating.
- This worktree started on `main` (89bf1cb). It was fast-forwarded to `expansion` (59e79d5) before any work, so this branch sits on top of `expansion`.
- Art functions take `g` (the gen_monsters module) and return a Model. `art_fusion_a.overworld(g, m, lift, side_yaw)` registers hover lift and profile yaw by name in `g.OW_FLOAT` / `g.OW_SIDE_YAW`, because those tables are dicts in gen_monsters that I am not allowed to edit. Other helpers: `disk` (a thin plate facing a normal), `puff_cloud`, `ring_paint`.
- The palette is limited to 15 colours, and the outline and eye colours count toward that. Share ramp colours between materials, and set `m.white` to an existing highlight to save a slot.
- Polish still open on 130-137:
  - The overworld frames and back sprites were only spot-checked.
  - STEAMOTH's body is small next to its wings.
  - In the front view, EMBERIME's frost tail reads a little like crystal wings.
  - HOARDWYRM's coins could be larger.
- Preview: `python3 tools/gen_monsters.py --only 130,...,151 --preview build/kinprev_d`, then look at `review_*.png` and `contact_overworld.png`.
- The session scratchpad is shared with the fusion_b artist. Use unique file names there.
