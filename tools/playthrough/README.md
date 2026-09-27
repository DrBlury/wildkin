# ROM-backed playtime checkpoints (plan 12 §3)

From an isolated worktree run `make && make shot && python3 -m unittest tools.tests.test_playthrough_runner` and `python3 tools/playthrough/run.py tools/playthrough/act2.route` (then `act3.route`). Requires ARM `nm`/`readelf`, host C compiler and libmGBA (`MGBA_PREFIX`, default `/opt/homebrew`). The timer uses the matching local `game.gba` and `game.elf`, a blank in-memory SRAM buffer, and build outputs only in `build/`; it never opens a user `.sav`. `make shot` checks that libmGBA is available, not that this runner covers a whole act.

Route grammar: `flag FLAG_NAME` **before** the single `start MAP_NAME`; `way MAP_NAME x y` asserts a reached tile, one axis at a time; `warden MAP_NAME x y west` (or other cardinal direction) interacts from that exact adjacent position and requires a ROM-observed victory; `edge MAP_FROM east MAP_TO` (or other cardinal direction) tries movement across a map edge and requires the observed destination map; `door MAP_FROM x y north MAP_TO` starts from the specified adjacent tile, moves into the door and verifies the destination map; `wild_limit 6` for a route or `wild_limit 3` for a hamlet sets the fight-then-flee count for that map. Counts reset on a successful `edge`. Door checkpoints do not imply a healer, quest or Hall interaction; those require their own observed actions. Named IDs and addresses come from current enum includes and ELF symbols. `readelf` resolves the unique anonymous Battle, Monster and Move structures by their distinctive field sets, checks member bounds, and passes their current sizes/offsets to C; missing or ambiguous layouts fail before execution. Paired bouts stop without an explicit actor/target policy; a stationary intro timer stops after 300 attempts. `BLOCKED` (exit 2) gives attempted frame count, map, tile, field/battle/dialog states and battle counts; a timed return to mode 10 (title) is explicitly blocked with the first observed title-entry source and last observed battle state/result/pair. `saw_battle=0` means no battle-mode frame was sampled, not proof that no transient execution occurred between frames. `CHECKPOINTS_COMPLETE` confirms *only listed checkpoints*, not act completion.

The timer excludes title debug warp/flag setup from frames; attempted movement, dialog advances, bouts, and blocked waits are counted at 59.7275 fps. During ordinary dialog it pulses A for two VBlank input polls followed by two release frames; a one-frame pulse could miss Juno’s queued warden call. Unanswered choice prompts fail closed. Warden bouts are never fled; the runner selects the highest available power×accuracy attacking move from the live ROM move table (not the full type/stage-aware `ai_score`), and fails for forced switches, depleted attacking PP, loss, or unhandled menus. It fights the first six wild wins on each route or three on a hamlet when `wild_limit 3` is set; subsequent encounters attempt flight, never flight from a no-run bout. It does not fabricate wild encounters merely to reach the quota. Its debug warp grants only one Lv20 FLARIX; healing, properly levelled four-kin team, tonic use and return to Hearth are not yet scripted. No arrival-level/balance or whole-act timing claim can be made until those and the quest/Hall checkpoints are actually navigated and measured. In particular do not multiply a short segment by 2.5 to claim human playtime.

`tools/playthrough/actN.route` are exploratory entry checkpoints, **not act-completion scripts**. On the field-stack-fixed ROM, Act II physically wins Juno and one Hall warden and reaches Fara’s adjacent Volt Hall tile after all three switches (6,154 frames / 1.717 min); Act III wins a Fen warden and reaches Port Brine’s upper frontage (5,069 frames / 1.414 min). Both record zero wild wins and no Master victory. A separate historical probe entered Brookmill Hearth without healing. See `docs/playtest/plan12-scripted.md` for distinct current and historical results. Human Acts II/III and the 16–18-hour playtime target remain unmeasured.

## Act II Hall approach (isolated ROM checkpoint)

`act2.route` now walks Lumen's Beacon stair and Crown to the Volt Hall door,
then steps on the three floor switches in a/b/c order and reaches (7,3),
adjacent to Fara. `switch MAP_VOLT_HALL group state` requires the player to be
on the group's actual tile, waits 16 timed frames for the walking
animation to toggle the live ELF-resolved `sw_on[group]`, then asserts the
state. It never writes puzzle RAM. `party_min N` reads the ROM's `party_count`
and blocks if fewer than N kin are present; a disposable probe appending
`party_min 4` to this route exits 2 at Fara's adjacent tile. These are
checkpoints, not a completed Master bout or crest. The Hall's first warden
is encountered and defeated en route; other Hall wardens are not silently
credited. The existing debug warp still supplies only one Lv20 FLARIX.

Fara uses a YES/NO challenge, not the `warden` interaction; no Master
choice handler has been verified with a prepared party, so the passing route
does not interact with her. `heal` and A-triggered `interact` are likewise
not implemented: this approach requires neither, and no healer outcome is
claimed. Add them only with observed dialog/menu and HP/PP evidence. The
entry-flag setup is still a debug prerequisite, not a representative Act I
save; absence of wild bouts does not satisfy the plan's 3/6 encounter quota.
See [Act II timing](../../docs/handoff/act2_timing.md) for exact frames and
reproduction of the party gate.
