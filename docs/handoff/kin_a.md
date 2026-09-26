# Handoff: kin 32-66 (KIN-A)

Files: `tools/kin/normal_a.py` (data) and `tools/kin/art_normal_a.py` (art,
one `def name(g)` model per species). `normal_a.py` wires art in with
`_m('name')`, which returns `None` until the function exists, so an
unpainted species falls back to the gen_monsters placeholder art.

## Done (final data + art, placeholder=False)

32 PRICKLET, 33 QUILLDRUM, 34 SNUFFLET, 35 TRUFFLOAR, 36 RACCOIN,
37 BANDIRACC, 38 PEBBOTTER, 39 TORRENTTER, 40 JELLUME, 41 MEDUSHOCK,
42 LURELING, 43 ABYSSLURE, 44 RADISHOO, 45 MANDRAGOR, 46 PUMPKLING,
47 JACKOGRIM, 48 SHROOMLET, 49 MYCOLOSSUS, 50 BLINKET, 51 BEACONFLY.

These have been previewed and iterated. The last round of tweaks was only
checked on the contact sheet, not zoomed in:

- BLINKET, BEACONFLY: brighter eyes, lantern bands.
- MANDRAGOR: plumper creased root torso.
- PUMPKLING: round carved eyes.

## In progress: data done, art missing

52 STATICKO, 53 FULGECKO, 54 FLURRABBIT, 55 MOONHARE, 56 TUXFLAKE,
57 EMPERICE, 58 YAKLING, 59 GLACIYAK, 60 RAMBLET, 61 CRAGHORN, 62 STINGLET,
63 SCORCHION, 64 DIGGET, 65 SEXTONE, 66 QUARTZLING.

Their stats, learnsets, traits, category and Almanac text are final and
validated (placeholder=False). Each one still needs a model function in
`art_normal_a.py`. Add it above the `# ---- end of batch ----` marker, using
exactly the lowercase species name, and it is picked up automatically. The
planned art briefs:

- STATICKO: a leopard-gecko-style gold body with dark spots, big eyes and
  glowing static toe pads.
- FULGECKO: the same lizard running upright, with a wide neck frill carrying
  bolt spines and an open mouth.
- FLURRABBIT: a chubby white snowshoe hare with ice-blue ear tips and a
  snowball tail.
- MOONHARE: an upright white-lavender rabbit with a wooden mochi mallet, a
  crescent mark and star-speckled ears.
- TUXFLAKE: a grey downy penguin chick in a fluffy snow puff (use
  `seedball`), with a black cap and orange feet.
- EMPERICE: a tall emperor penguin with gold neck patches and a crown of ice
  crystals.
- YAKLING: a shaggy slate-blue calf with frost-tipped fringe over its eyes and
  horn nubs.
- GLACIYAK: a massive shaggy yak with curved ice-crystal horns and icicles.
- RAMBLET: a cinnamon-wool lamb with a woolly helmet tuft, charging.
  Keep it unlike DANDELAMB.
- CRAGHORN: a bighorn ram with curled stone horns (`m.rock` segments).
- STINGLET: a small purple scorpion with a curled tail and a lime stinger
  drop.
- SCORCHION: a dark carapace with glowing ember seams and a flame stinger
  (`g.flame`).
- DIGGET: a velvet mole with pink spade paws and a tiny lantern.
- SEXTONE: an upright mole holding a spade and a lantern, with faint glowing
  eyes.
- QUARTZLING: a pale segmented grub with amethyst quartz points on its back.

## Not started

Nothing else. All 35 entries have real data.

## Notes

- Regenerated with `python3 tools/gen_species.py && python3 tools/gen_monsters.py`.
  Both succeeded and the kin validator passed: BST tiers, moves, names.
- Balance numbers: first stages have a BST of 294-310, finals 490-516. Every
  stat is 30-125, and category widths are at most 70 px (the limit is 72).
  Every learnset has 8-12 moves, with a same-type attack by Lv20.
- `make test` passes on the regenerated headers, with no FAIL lines.
  `make` (the ROM) was not run.
- `float_ow(g, m, lift, side_yaw)` makes a kin hover in its overworld frames.
  It writes `g.OW_FLOAT` / `g.OW_SIDE_YAW` from inside the model function,
  so gen_monsters.py itself did not need editing. The jellies, anglerfish and
  fireflies use it.
- The palette limit is 15 colours, counting outline, white and eye_dark.
  build_palette raises an error when a model goes over.
- `tube()` needs exactly one radius per point. Use `rfn=` for a taper
  along many points.
- The scratchpad is shared with the other kin agents. My helper scripts are
  prefixed `kina_`.
- Preview: `python3 tools/gen_monsters.py --only 52,53 --preview build/kinprev_a`.
