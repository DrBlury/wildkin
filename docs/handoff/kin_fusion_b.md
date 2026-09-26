# Handoff: fusion kin 152-173 (KIN-E)

Files: `tools/kin/fusion_b.py` (data), `tools/kin/art_fusion_b.py` (art),
plus the regenerated `src/species_data.h` and `src/gfx_monsters.h`.

## Done

- **Data for all 22 (152-173)**: stats (BST 525-560), catch 45, XP 205-215,
  category (all fit in 72 px), height and weight, two traits, 11-13 move
  learnsets using both parent types, field abilities, and Almanac text
  ("Woven from X and Y energy...", all 180 characters or fewer). The ids,
  names, types, rarity `F` and fusion signatures are unchanged.
- **Art finished and reviewed (front, back, icon, overworld)**: 152 BARKOLEM,
  153 PORCELYNX, 154 KABUTORAI, 155 DROWNJELLY, 156 SUNMANE, 157 DREAMKITE,
  158 BOGNEWT, 159 RIMEGOLEM.

## In progress

- **Art written but only looked at once**: 160 DYNAMOLE, 161 LULLABOX,
  162 KITSUFLAME, 163 WYVERNIX. They render and are in the header, but
  nobody has checked the sheets. Check the faces (decal visibility), the
  nine tails of KITSUFLAME and the wing spread of WYVERNIX first.

## Not started

- **Art for 164-173**: TRIHYDRA, PHOENEX, IRONHOWL, NIMBWHALE, JOLLYROGUE,
  RUNELITH, FAEFLY, SNOWBRUTE, TESLAROSE, NOCTMARE. Their model is a
  `_todo(...)` stub at the bottom of `art_fusion_b.py`, which draws the
  generic placeholder in type colours. Replace each stub with a real
  `def name(g):` function. Planned designs:
  - TRIHYDRA: squat marsh wyrm, three differently crested necks, glowing lime venom spots.
  - PHOENEX: bird whose tail plumes are a night-violet starfield with burning edges; hovers.
  - IRONHOWL: wolf with riveted steel plates, magnet-blue glowing seams, head raised to howl.
  - NIMBWHALE: round sky-blue whale with a cloud mantle and a rainbow spout; hovers.
  - JOLLYROGUE: skeleton in a tricorn and a tattered coat, hugging a glowing ship-in-a-bottle.
  - RUNELITH: tall standing-stone slab on stubby legs, glowing amber runes, floating stone fists.
  - FAEFLY: dragonfly with four long iridescent wings and a petal tutu; hovers.
  - SNOWBRUTE: shaggy lavender-white yeti in a boxer's stance with glowing ice gauntlets.
  - TESLAROSE: crimson rose head on a stem body, copper-coil vine arms, blue arcs.
  - NOCTMARE: black horse with a violet smoke mane full of stars, pale-flame hooves.

## Notes

- Status at handoff: `make` builds, and `make test` passes (field, game and
  core checks).
- `placeholder=False` is set for all 22 on purpose, because the data is
  final and its BST is checked by tier. Only the art of 164-173 is a
  stand-in.
- Model functions take the `gen_monsters` module as `g`. The helpers
  `hover(g, m, px)` and `side_yaw(g, m, yaw)` set `g.OW_FLOAT` and
  `g.OW_SIDE_YAW` for a species from inside its own model function, so
  `gen_monsters.py` itself stays untouched.
- The palette limit is 15 colours, counting outline, white and eye. Reuse
  a ramp colour for `white` and `eye_dark` so they dedupe.
- Glowing eyes on a lit surface disappear. Put a dark `m.dot(...)` band
  behind them (see KABUTORAI and RIMEGOLEM).
- This worktree started on `main` by mistake, so it was reset to the
  `expansion` base (59e79d5) before any work.
- Nothing outside the files above was changed. Music files were not touched.
