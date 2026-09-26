# Handoff: rare kin (101-120) and legends (121-129), owner KIN-C

## Done

All 9 legends have real data and art (`placeholder=False`), in `tools/kin/legend.py` (data) and
`tools/kin/art_legend.py` (models):

- **CALDERON**: forge salamander with iron fins, smokestack vents and molten spots. BST 600.
- **NOCTHALE**: star whale with glowing throat grooves, stars and a bell-kernel on its brow. BST 605.
- **HOARFANG**: white winter wolf with a crown of ice shards and a dusk-tipped tail. BST 605.
- **OSSUREX**: bone dragon with tattered wings and an ember kernel in its ribcage. BST 610.
- **SELENOTH**: pale lunar moth with gold crescent eyespots and long hindwing tails. BST 600.
- **SYLVARCH**: stag whose antlers are boughs with leaf pads and blossoms. BST 605.
- **HOROLOGOS**: clock-tower titan with a clock face on its chest and a brass gear wheel. BST 600.
- **SCRIPTORA**: page serpent. BST 605. Its art is weak (see In progress).
- **SKYLORN**: sky manta seen from above, with a starry back and clouds. BST 605.

Every legend has catch 3, xp 255, 12-13 moves including the strongest moves of its types, and an
Almanac text tied to its lair.

## In progress

These models work but need another art pass:

- **SCRIPTORA** reads as a white worm. Plan: rebuild the body as a twisting scroll ribbon (quads
  along a curve, with script lines and glowing runes). Give it a rolled scroll end with a handle,
  and make the head an open book whose covers are the jaws, with pages fanned out as a mane.
- **CALDERON** reads gorilla-like head-on. Plan: a long, low salamander at `front_yaw` -40, with
  the head forward and the elbows splayed out.
- **NOCTHALE**: the flippers blend into the body. Make them pale (humpback-white), with glowing tips.
- **HOARFANG** needs a longer muzzle, a dark eye mask and a dusk saddle.
- **SELENOTH** needs flatter, broader forewings with a continuous night-blue leading edge, and
  bigger crescents.
- **SKYLORN**: the eyes are hidden behind the cephalic fins. Move them to about
  `L(+-2.8, 1.9, 7.6)`.

## Not started

All 20 rare kin, 101-120 in `tools/kin/rare.py`, are still roster placeholders. I planned the
designs but wrote no data or art for them.

Planned concepts:

- **KOIRIN / RYUKOI**: kohaku koi leaping up a falls, growing into an elegant white-red-gold koi
  dragon. Not a Gyarados.
- **TRINKIT / HOARDMAW**: a jewellery box with teeth, growing into a bulky iron-banded chest on
  beast legs.
- **RATTLEBONE / OSSIGUARD**: a pot-helmet skeleton squire, growing into a rusty skeleton knight.
- **GAUNTLING / HOLLOWHELM**: a gauntlet that walks on its fingers, growing into an empty plate
  armour with glowing gaps.
- **WICKLET / LAMPGHAST**: a candle stub, growing into a grinning paper lantern with a long tongue.
- **METEORB / BOLIDON**: a meteorite with glowing cracks, growing into a rock rhino with a comet
  mane.
- **Singles**:
  - KELPYRE: kelp-maned water horse.
  - TENGALE: red-nosed tengu with a feather fan.
  - SLUMBAKU: night-blue and cream tapir with dream bubbles.
  - WENDIGAUNT: gaunt figure with a frosted deer-skull head.
  - LAMPJINN: smoke genie from a brass lamp.
  - GARGOLITH: crouching stone gargoyle.
  - HOPSHI: stiff-armed jiangshi with a talisman.
  - QILUMEN: gold-scaled kirin with a starry mane.

BST tiers, from the validator: the first stages of the rare lines count as **first** (280-345)
and their grown forms as **final** (470-535). The singles count as **rare** (440-545). Planned
catch rates are 45 for line members and 25-35 for singles.

## Notes

- `make` and `make test` both pass (field, game and core checks), with the headers regenerated
  from this state.
- My worktree was created from `main`, so I reset it to the expansion base (59e79d5) before
  starting.
- Art helpers:
  - Model functions take the `gen_monsters` module `g`, and `_use(g)` binds its helpers into the
    art module.
  - `hover()` and `side_yaw()` write into `g.OW_FLOAT` and `g.OW_SIDE_YAW` at build time. This
    sets the overworld float and profile yaw without editing `gen_monsters.py`.
  - `gear_ring`, `vertebrae`, `foliage`, `frame` and `local` are reusable for the rares.
- The palette limit is 15 colours, counting outline, white and eye. Set `white` and `eye_dark` to
  match existing ramp colours to save slots.
- Removing a placeholder's learnset can orphan a move from the "every move is learned" test.
  Check that test after editing `rare.py`.
- Preview: `python3 tools/gen_monsters.py --only 121,...,129 --preview build/kp`.
