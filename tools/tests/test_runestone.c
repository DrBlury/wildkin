/*
 * The RUNESTONE (src/game/travel.c): a KEY item every game owns that spins
 * you home (MAP_HOME 9,3 facing down) in a ring of runes. Checks the item,
 * using it from the bag and from SELECT, the frozen field while the spell
 * plays, the places it refuses, and that saves without it get one.
 */
#include "harness.h"

static void enter(int map, int x, int y, int dir)
{
    game_mode = MODE_FIELD;
    dialog_clear();
    field_enter_map(map, x, y, dir);
    warp.active = 0;
    set_brightness(0);
    step(0);
}

static int debug_map(void)
{
    for (int m = 0; m < MAP_COUNT; m++)
        if (MAPS[m].flags & MF_DEBUG) return m;
    return -1;
}

static int at_home(void)
{
    return cur_map == MAP_HOME && player.x == 9 && player.y == 3 && player.facing == DIR_DOWN;
}

static int fx_palette_back(void)
{
    for (int i = 0; i < 16; i++)
        if (obj_palette[OBANK_TFX * 16 + i] != travel_fx_palette[i]) return 0;
    return 1;
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    fresh_game();
    give_starter();

    /* ---- the item ---- */
    const Item *it = &ITEMS[ITEM_RUNESTONE];
    CHECK(it->pocket == POCKET_KEY && it->kind == IK_KEY && it->icon == ICON_RUNESTONE && it->price == 0,
          "the RUNESTONE is a KEY item with its own icon");
    CHECK(bag[ITEM_RUNESTONE] == 1, "a new game starts with the RUNESTONE");
    CHECK(RUNE_OT >= 400 && RUNE_OT + TR_TILE_COUNT <= 512, "its art fits the free OBJ tiles 400-511");

    /* ---- refusals ---- */
    enter(MAP_HOME, 9, 3, DIR_DOWN);
    CHECK(!item_use_field(ITEM_RUNESTONE, 0) && dialog_active() && !tv.pending, "it refuses at home");
    run_dialog(200);
    int dbg = debug_map();
    if (dbg >= 0) {
        enter(dbg, 2, MAPS[dbg].h - 3, DIR_UP);
        CHECK(!item_use_field(ITEM_RUNESTONE, 0) && dialog_active() && !tv.pending, "and on debug maps");
        run_dialog(200);
    }

    /* ---- from the bag ---- */
    enter(MAP_TOWN, 20, 18, DIR_UP);
    travel.biking = 1;
    CHECK(item_use_field(ITEM_RUNESTONE, 0) && !dialog_active() && tv.pending == PEND_HOME,
          "using it in town starts the spell (no message, the bag just closes)");
    CHECK(bag[ITEM_RUNESTONE] == 1, "and it is not used up");
    step(0);
    CHECK(travel_rune_active() && rune.active == 1, "the runes gather once the player stands still");
    int x0 = player.x, y0 = player.y, turned = 0, lifted = 0, blocked = 1;
    for (int f = 0; f < RUNE_CHARGE - 4; f++) {
        u8 face = player.facing;
        step((f & 1) ? KEY_START : KEY_LEFT);
        turned += player.facing != face;
        lifted |= travel_player_lift() > 0;
        if (game_mode != MODE_FIELD || player.x != x0 || player.y != y0 || cur_map != MAP_TOWN) blocked = 0;
    }
    CHECK(blocked, "while it charges, the field is frozen (no walking, no START menu)");
    CHECK(turned >= 12 && lifted, "the player spins on the spot and floats");
    CHECK(REG_BLDCNT != 0, "the world burns white at the climax");
    for (int f = 0; f < 10; f++) step(0);
    CHECK(rune.active == 2 && at_home(), "then you are home: MAP_HOME at 9,3 facing down");
    CHECK(!travel.biking && !travel.surfing, "off the bike");
    for (int f = 0; f < RUNE_ARRIVE + 4; f++) step(0);
    CHECK(!travel_rune_active() && at_home() && REG_BLDCNT == 0 && fx_palette_back(),
          "the arrival sparkle ends: brightness and the fx palette are back");
    CHECK(game_mode == MODE_FIELD && !dialog_active(), "and you can move again");

    /* ---- from SELECT ---- */
    enter(MAP_MEADOW, 21, 38, DIR_UP);
    opt.registered = (u8)(ITEM_RUNESTONE + 1);
    CHECK(registered_item() == ITEM_RUNESTONE, "the RUNESTONE can be registered to SELECT");
    tap(KEY_SELECT);
    for (int f = 0; f < RUNE_CHARGE + RUNE_ARRIVE + 10; f++) step(0);
    CHECK(at_home() && !travel_rune_active(), "SELECT spins you home too");
    opt.registered = 0;

    /* ---- surfing ---- */
    enter(MAP_TOWN, 20, 18, DIR_UP);
    travel.surfing = 1;
    CHECK(item_use_field(ITEM_RUNESTONE, 0), "it works while surfing");
    for (int f = 0; f < RUNE_CHARGE + RUNE_ARRIVE + 10; f++) step(0);
    CHECK(at_home() && !travel.surfing, "and lands you on dry floor at home");

    /* ---- older saves get one ---- */
    static u8 sram[32768];
    memset(sram, 0xFF, sizeof(sram));
    bag[ITEM_RUNESTONE] = 0;
    CHECK(save_write_to(sram), "a save without the RUNESTONE writes");
    new_game();
    bag[ITEM_RUNESTONE] = 0;
    CHECK(save_load_from(sram) == SAVE_VERSION && bag[ITEM_RUNESTONE] == 1, "loading it hands the RUNESTONE over");

    if (!failures) {
        printf("all runestone checks passed\n");
        return 0;
    }
    printf("%d check(s) FAILED\n", failures);
    return 1;
}
