# ADMIN mode handoff

`make && make test` are green, with zero warnings. `tools/tests/test_admin.c`
has 122 checks. Every screen was checked in the real ROM with `build/shot`
(the script is described under "ROM check" below).

## How to switch it on

It works in the normal release ROM, and nothing changes until you switch
it on:

1. On the title screen, hold SELECT and press START to open the DEBUG menu.
2. Move to **ADMIN MODE** and press A. It shows ON.
3. Press B, then continue or start a game. **ADMIN** now shows in red in the
   START menu, between OPTIONS and SAVE.

What happens to the switch:

- With a save on the cartridge, the debug menu writes the switch into it at
  once. The title has just loaded that save, so nothing else in it changes.
  The note under the list says "Saved to the cartridge."
- Without a save, the switch stays in memory ("Kept for the new game's
  save."). NEW GAME keeps it, because `new_game()` does not touch `opt`, and
  the first save stores it.
- Press A on the row again to switch it off.

## Where it lives

- **`opt.admin`** (options.h) is options byte 12, which was padding until
  now. `opt` is still 16 bytes.
  - Saves from before this change carry 0 in that byte, so they load with
    ADMIN mode off. Version-4 saves copy the options and load with it off
    too.
  - `save_apply` clamps the byte (`opt.admin &= 1`), and `options_reset`
    clears it.
  - The save stays at version 5, and nothing else in its layout changed.
- **src/game/admin.c** (new, included after debug.c) is one ext screen with
  five states:
  - `AD_MAIN`: the admin menu.
  - `AD_PICK`: a list picker.
  - `AD_QTY`: the item quantity.
  - `AD_FORM`: the ADD KIN form.
  - `AD_DIALOG`: result messages over the form.
- **debug.c** gains the ADMIN MODE row (`DBGI_*` names the rows) and a note
  line.
- **menu.c** gains `SM_ADMIN`, which shows only while `opt.admin` is on.
- **naming.c** gains `NM_DRAFT`: the name slate can name a kin that is not
  owned yet (`nm_draft` points at it). ADD KIN uses it.

## Entries

### ADD 10000 COINS

- Coins are capped at `MONEY_CAP` = 9999999, the most the save accepts.
- The bottom panel shows "+10000c. You have Nc.", or "The purse is full"
  when the cap is reached.

### GIVE ITEM

- The picker lists every item, grouped by pocket.
- Each row shows the name, the pocket (in blue) and how many you have.
- The bottom panel shows the item icon and two lines of its description.
- A asks HOW MANY:
  - UP/RIGHT adds 1 and DOWN/LEFT takes 1 away, wrapping between 1 and 99.
  - L/R changes it by 10.
  - Key items come one at a time.
- `bag_add` caps a stack at 999.

### ADD KIN

The form has 10 rows on the right: KIN, LEVEL, LUSTROUS, NAME, MOVE 1-4,
SEND TO and ADD THIS KIN. On the left are the portrait (lustrous
colours included) and an info panel:

- on species rows: No., type badges, rarity and how it grows;
- on move rows: category, type badge, power or uses, and accuracy.

What each row does:

| Row | Controls |
| --- | --- |
| KIN | LEFT/RIGHT ±1 (wraps), L/R ±10, A opens the species picker. The species picker shows the number, name, types, the kin's icon, type badges, rarity and how it grows. |
| LEVEL | 1-100. LEFT/RIGHT ±1, L/R ±10. |
| LUSTROUS | LEFT, RIGHT or A toggles it. |
| NAME | A opens the name slate (NM_DRAFT). |
| MOVE n | A opens every move (`MOVE_COUNT` of them, with NO MOVE first). A move that is already in another slot is refused. SELECT brings back its natural moves. |
| SEND TO | SHELF (default) or TEAM. |
| ADD THIS KIN | Builds and gives the kin (see below). |

How the moves follow the species and level:

- The moves start as the kin's natural moves: `monster_make`'s four latest
  learnset moves for its level.
- A new species resets them.
- A new level resets them only if you have not edited any move yet
  (`adm.custom`).

`admin_build_kin` builds the kin:

- `monster_make(species, level)` sets the stats, the XP for the level (so
  evolution by level works as usual) and full HP. It also rolls potential,
  temperament, trait and size.
- Then it applies the form: the lustre flag, the moves with full uses
  (packed to the front, empty slots last) and the nickname (`kin_set_name`).
- The kin is met on the current map, at its level.

`admin_give_kin` places it:

- With SHELF it uses `storage_add_box(m, opt.shelf_box)`. With TEAM it goes
  to the team.
- If that side is full, the kin goes to the other one. If both are full,
  nothing is added and a message says so.
- It marks the species as met and befriended in the Almanac.

A kin with no moves is refused, because the save check (`monster_valid` /
`boxmon_valid`) needs at least one move. The result shows in the message
box, then the form comes back, so you can add several kin in a row.

### TEACH A MOVE

1. Pick a team kin (the list shows its icon, level and HP).
2. Pick a slot (the list shows each move and its uses).
3. Pick a move from the full list, or NO MOVE to clear the slot.

The move goes in with full uses, and the moves are packed again. Two cases
are refused with a message:

- clearing the last move;
- a move the kin already knows in another slot.

After a move is taught, the slot list comes back and shows "Learned X!".

### HEAL TEAM

Calls `party_heal_all()`.

### The picker (all lists)

- UP/DOWN steps one entry (and wraps).
- L/R moves a page (6 rows).
- LEFT/RIGHT jumps to the previous or next group: pocket, type, ten species
  numbers, or first letter in A-Z order.
- SELECT switches the order (BY POCKET / BY NUMBER / BY TYPE ↔ A TO Z) and
  keeps the same entry selected.
- A picks and B goes back.

The header shows the title, the order and "n/N" in the small font.

## Hardware limits

`test_fits` in test_admin.c measures the text with the game's font tables:

- The rows and help lines fit their windows.
- Picker titles leave room for the order label and the count.
- The widest species name and types fit on one row.
- The widest item result line fits.
- The form's labels and left-panel lines fit 64 px.
- The quantity hint and the debug note fit.

The small font has digits and "/LvHP%x.<" only, so every other word uses
the normal font. The screens use `screen_begin`, `canvas_window` (WIN_STD),
the glow bar, `{` cursors, and `^` / `}` scroll marks, like OPTIONS and the
bag.

## Also fixed

The summary now loads the portrait with its lustrous colours
(`load_monster_gfx_ex(..., MF_LUSTROUS)`). Before this, a lustrous kin
showed its normal colours there.

## Tests (tools/tests/test_admin.c)

All of these are driven by key presses, frame by frame:

- **Switching it on:** SELECT+START on the title, then the ADMIN MODE row.
  Covered: the save write, B back to the title, the reload, off/on, the
  no-save path and NEW GAME.
- **START menu:** ADMIN shows only while admin mode is on.
- **Coins:** twice, then at the cap and with a full purse.
- **Items:**
  - pocket grouping, RIGHT/LEFT group jumps, R pages;
  - 15 STAR LANTERNs (UP×4, R, A);
  - wrap to 99, and B without giving;
  - A-Z with the same item kept;
  - a key item limited to 1;
  - paging to the end.
- **Add kin:**
  - the species picker to DRAKORA, and levels 1/100/49/50 (natural moves
    at 50);
  - lustrous, and the nickname STORMY on the slate;
  - BONK, RUNE BOLT and SUPERNOVA (none of them in DRAKORA's learnset),
    with a duplicate refused and MOVE 4 cleared;
  - the custom moveset kept through a level change;
  - added to the Shelf, then checked: species, level, lustre, name, moves,
    uses, XP, HP/stats, Almanac, `boxmon_valid`, met data;
  - TEAM (`monster_valid`), then a full team falling back to the Shelf;
  - a kin with no moves refused, SELECT natural moves, and a species change
    resetting the moves.
- **Teach and heal:**
  - METEOR FALL into slot 2 with full uses;
  - clearing the last move refused;
  - HEAL TEAM on a team at 0 HP, poisoned, with no uses left;
  - BACK to the START menu.
- **Save round trip:**
  - the admin flag, the Shelf kin (moves, name, lustre), coins and items
    all survive;
  - a save with byte 12 = 0, as older v5 saves have, loads with admin off
    and no ADMIN in the START menu;
  - a stray byte is clamped;
  - a version-4 save loads with admin off.
- **Text widths** (see Hardware limits).
- **Every screen:** each one opens, scrolls and closes.

## ROM check

The scratch script opened the title's debug menu, switched ADMIN MODE on,
continued and opened START > ADMIN. It then went through every screen:
coins, item list, quantity, result, A-Z, form, species picker, lustrous,
name slate, move picker, custom moves, add result, the TEACH lists, a
refusal, a taught move, heal, and the Shelf and summary of the new kin. It
used a `tools/make_demo_save.c` save at MAP_HOME 9,5.

The shots are in `build/admin_shots/` (01_debug_menu ... 25_shelf_summary_moves).

## Left / ideas

- There is no title-screen button code. The DEBUG menu row is the only way
  to switch it on, and it needs a deliberate SELECT+START, then the row,
  then A.
- The ADD KIN form rolls potential, temperament, trait and size at random.
  Setting them by hand (potential up to PERFECT, a chosen trait) would be a
  natural next row.
- A kin added above its evolution level grows at its next level-up, like
  a SUNSEED on an overdue kin. It does not evolve on the spot.
