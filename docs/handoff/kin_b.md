# Handoff: KIN-B (kin 67-100)

Files: `tools/kin/normal_b.py` (data), `tools/kin/art_normal_b.py` (art),
regenerated `src/species_data.h` and `src/gfx_monsters.h`.

## Done

- **Data for all 34 kin (67-100)**: base stats inside the tier BST ranges,
  catch rates, XP, categories (all <= 72 px), height/weight, two traits,
  8-11-move learnsets (only moves in `src/game/moves.h`, level-1 moves
  first, a same-type attack by Lv20, no duplicates), field abilities per
  the roster, in-world Almanac text (<= 180 chars). Checked with a script
  against the rules in `tools/test_game.c`. `M_ANVIL_DROP` and
  `M_LODE_BEAM` are learned only by this batch (LODEHORN, FORTADILLO,
  FOUNDRAKE), so keep them in these learnsets.
- No species is fully finished: art is still being tuned, see below.

## In progress (real data + first-pass art, placeholder=False)

`normal_b.py` looks up `art_normal_b.<lowercase name>`; if the function
exists the kin gets that model and `placeholder=False`.

- 84 CALCIPUP, 85 OSSIHOUND: bone pup / bone hound with ember eyes, grave-
  dust ears, collar (pup). Body turned side-on (front_yaw -50) with the
  skull turned toward the viewer (`yrot` + `rot=(T,0,0)` + `turn=T`).
  Missing: the rib gaps still read weakly in the front sprite. The
  `ribcage()` helper paints dark slabs across a bone barrel; the barrel's
  front cap shows no ribs. Just changed to span=0.92 and more gaps; not yet
  previewed. Consider shifting the barrel back behind the shoulders.
- 86 MUDDLE (good), 87 BOGSHAMBLE (good): peat blob / peat hulk with
  mismatched swamp-glow eyes, lily pad, stray bone, ribs, mushrooms.
- 88 DREGCROW: dark beak and a bone patch round one eye. Needs another
  preview pass for scruffiness and size.
- 89 CAWDAVER (good): bone skull and beak, hood, tattered cloak, bone wing
  struts with ragged feathers, ribcage and kernel.
- 90 CRANICRAB (good): skull shell, eyestalks through the sockets (just
  lengthened, not re-previewed), starfish, one big claw.
- 91 CRYPTCLAW: urn on crab legs, skull emblem, lid pushed up with a skull
  knob, eyestalks under the lid (just enlarged, not re-previewed).

## Not started (real data, placeholder art, placeholder=True)

67 QUARTZPEDE, 68 FLYSQUIRL, 69 GALESQUIRL, 70 DOZLOTH, 71 SOMNISLOTH,
72 SCYTHLING, 73 REAPMANTIS, 74 MAGNITICK, 75 LODEHORN, 76 HUMBEE,
77 COMBQUEEN, 78 WEBBIT, 79 LACEWIDOW, 80 SQUEAKLE, 81 NOCTAVE, 82 NOXKIT,
83 UMBRAKAT, 92 PARASOLE, 93 STORMBRELA, 94 KETTLEKIN, 95 TANUKETTLE,
96 STRAWSPECT, 97 RIVETILLO, 98 FORTADILLO, 99 SALAMBER, 100 FOUNDRAKE.

Design notes for these are in the `concept` field and the descriptions.
Planned motifs: DOZLOTH hangs under a floating dream cloud; KETTLEKIN has
tanuki ears on its lid (foreshadows TANUKETTLE, a tanuki in an iron
chagama with a leaf on its head); PARASOLE one eye + crook-handle foot,
STORMBRELA blown inside out with spark-tipped ribs; FORTADILLO has
battlements; FOUNDRAKE has ingot plates and SALAMBER-style glowing seams.

## Notes

- This worktree started on the pre-expansion commit (89bf1cb); I fast-
  forwarded it to `expansion` (59e79d5) before working.
- Build/tests: `gen_species.py` and `gen_monsters.py` run cleanly (validator
  passes). `make` and `make test` were NOT run.
- `ow(g, m, lift=, side=)` in art_normal_b.py sets `g.OW_FLOAT` /
  `g.OW_SIDE_YAW` for a kin from inside its model function (those tables
  are keyed by name in gen_monsters.py, which this batch must not edit).
- Palettes: max 15 colours incl. outline, white and eye_dark; reuse ramp
  colours (build_palette dedups identical 555 colours), e.g. eye_dark =
  DUST[0].
- Paint slabs thinner than ~1.5 px vanish after downsampling; view-angle
  foreshortening (front_yaw) matters a lot for anything spaced along z.
- Preview: `python3 tools/gen_monsters.py --only 84,85 --preview DIR`. The
  Read tool may cache a PNG by path; write each preview to a new filename.
