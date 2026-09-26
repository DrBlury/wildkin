/*
 * UI and QoL checks (docs/EXPANSION.md 7.6): the START menu (MAP, FIELD,
 * QUESTS, the clock, scrolling), options, the bag's pockets / order /
 * register / routing, the LANTERN SHELF (boxes, withdraw, deposit, move,
 * release, sort, find, stored-kin summary), Almanac filters, the quest log
 * (with an injected quest table), the Lorebook chapters, the CREST CASE,
 * item icons and the kin viewer layout.
 */
#include "harness.h"

static void run_until_idle(int (*busy)(void), int limit)
{
    for (int f = 0; f < limit && busy(); f++) step((f & 3) == 0 ? KEY_A : 0);
}

static int bag_busy(void) { return game_mode == MODE_BAG && bscr.state == BS_DIALOG; }
static int pc_busy(void) { return game_mode == MODE_PC && pc.state == SH_DIALOG; }
static int start_busy(void) { return game_mode == MODE_START_MENU && start_dialog; }

static int menu_index(int sm)
{
    start_menu_build();
    for (int i = 0; i < start_count; i++)
        if (start_items[i] == sm) return i;
    return -1;
}

static void open_start(void)
{
    game_mode = MODE_FIELD;
    dialog_clear();
    tap(KEY_START);
}

static void pick(int sm)
{
    start_cursor = menu_index(sm);
    tap(KEY_A);
}

static int item_of_kind(int kind)
{
    for (int i = 0; i < ITEM_COUNT; i++)
        if (ITEMS[i].kind == kind) return i;
    return -1;
}

static void setup_world(void)
{
    fresh_game();
    static const u8 TEAM[4] = { SP_PYREFOX, SP_AXOLURK, SP_ZAPPET, SP_GOLEMIT };
    for (int i = 0; i < 4; i++) {
        Monster m = monster_make(TEAM[i], 12 + i);
        give_monster(&m);
    }
    flag_set(FLAG_STARTER);
    flag_set(FLAG_TWIN_CRYSTAL);
    follower_reset();
    field_enter_map(MAP_TOWN, 20, 16, DIR_DOWN);
    settle();
}

/* ---------------- icons, battle items ---------------- */

static void test_items(void)
{
    int ok = 1;
    for (int i = 0; i < ITEM_COUNT; i++) {
        if (item_icon_index(i) != ITEMS[i].icon) ok = 0;
        draw_item_icon(1, 15, i);
        for (int c = 2; c < 16; c++)
            if (bg_palette[BANK_ITEM_ICON * 16 + c] != item_icon_pal[ITEMS[i].icon][c]) ok = 0;
        if (bg_palette[BANK_ITEM_ICON * 16 + 1] != ui_pal_std[1]) ok = 0; /* the page's paper */
    }
    CHECK(ok, "draw_item_icon uses each item's own icon (no out-of-bounds read)");
    CHECK(item_battle_usable(item_of_kind(IK_HEAL_CURE)) && item_battle_usable(item_of_kind(IK_TEA_ALL)) &&
              item_battle_usable(item_of_kind(IK_REVIVE)) && item_battle_usable(ITEM_TONIC),
          "the new brews work in bouts");
    CHECK(!item_battle_usable(item_of_kind(IK_FOOD)) && !item_battle_usable(ITEM_BIKE) &&
              !item_battle_usable(item_of_kind(IK_MATERIAL)),
          "food, key items and materials don't");
}

/* ---------------- START menu ---------------- */

static void test_start_menu(void)
{
    setup_world();
    char buf[32];
    gtime.day = 3;
    gtime.minute = 14 * 60 + 5;
    time_text(buf);
    CHECK(!strcmp(buf, "DAY 3  14:05"), "the clock reads DAY 3  14:05");
    open_start();
    CHECK(game_mode == MODE_START_MENU, "START opens the menu");
    CHECK(menu_index(SM_QUESTS) >= 0 && menu_index(SM_MAP) < 0 && menu_index(SM_FIELD) < 0,
          "QUESTS is there; MAP needs the TOWN MAP and FIELD a crest or the BIKE");
    bag[ITEM_TOWN_MAP] = 1;
    bag[ITEM_BIKE] = 1;
    start_menu_build();
    CHECK(menu_index(SM_MAP) >= 0 && menu_index(SM_FIELD) >= 0 && start_count > START_ROWS,
          "with the TOWN MAP and BIKE the menu has MAP and FIELD and scrolls");
    start_cursor = 0;
    for (int i = 0; i < start_count - 1; i++) tap(KEY_DOWN);
    CHECK(start_items[start_cursor] == SM_EXIT && start_scroll == start_count - START_ROWS,
          "scrolling down reaches EXIT");
    tap(KEY_DOWN);
    CHECK(start_cursor == 0 && start_scroll == 0, "and wraps back to the top");

    pick(SM_MAP);
    CHECK(game_mode == MODE_EXT, "MAP opens the town map");
    for (int i = 0; i < 20 && game_mode == MODE_EXT; i++) tap(KEY_B);
    run_until_idle(start_busy, 300);
    CHECK(game_mode != MODE_EXT, "B leaves the town map");
    if (game_mode != MODE_START_MENU) open_start();
    pick(SM_FIELD);
    for (int i = 0; i < 20 && game_mode != MODE_START_MENU && game_mode != MODE_FIELD; i++) tap(KEY_B);
    run_until_idle(start_busy, 300);
    CHECK(game_mode == MODE_START_MENU || game_mode == MODE_FIELD, "FIELD opens the traversal menu and B leaves it");
    if (game_mode != MODE_START_MENU) open_start();

    pick(SM_CARD);
    CHECK(start_card, "CARD shows the warden card with the crests");
    tap(KEY_B);
    CHECK(game_mode == MODE_START_MENU && !start_card, "B closes the card");
    tap(KEY_B);
    CHECK(game_mode == MODE_FIELD, "B closes the menu");
}

/* ---------------- options ---------------- */

static void test_options(void)
{
    setup_world();
    open_start();
    pick(SM_OPTIONS);
    CHECK(game_mode == MODE_OPTIONS, "OPTIONS opens");
    int fits = 1, cycles = 1;
    for (int i = 0; i < OPT_ROWS; i++) {
        const OptRow *o = &OPT_ROWS_DEF[i];
        if (text_width(o->label) > 128) fits = 0;
        u8 before = *o->value;
        for (int k = 0; k < o->count; k++) {
            if (text_width(o->names[k]) > 56) fits = 0;
            opt_cursor = i;
            tap(KEY_RIGHT);
        }
        if (*o->value != before) cycles = 0;
    }
    CHECK(fits, "every option label and value fits its column");
    CHECK(cycles, "every option cycles through its values and wraps");
    opt_cursor = opt_scroll = 0;
    for (int i = 0; i < OPT_ROWS - 1; i++) tap(KEY_DOWN);
    CHECK(opt_cursor == OPT_ROWS - 1 && opt_scroll == OPT_ROWS - OPT_VISIBLE, "the option list scrolls");
    opt_cursor = 0;
    int hud = -1;
    for (int i = 0; i < OPT_ROWS; i++)
        if (OPT_ROWS_DEF[i].value == &opt.hud_clock) hud = i;
    opt_cursor = hud;
    tap(KEY_A);
    CHECK(hud >= 0 && opt.hud_clock == 1, "HUD CLOCK toggles");
    opt.hud_clock = 0;
    tap(KEY_B);
    CHECK(game_mode == MODE_START_MENU, "B leaves the options");
}

/* ---------------- bag ---------------- */

static void test_bag(void)
{
    setup_world();
    for (int i = 0; i < ITEM_COUNT; i++) bag[i] = 1 + i % 5;
    open_start();
    pick(SM_BAG);
    CHECK(game_mode == MODE_BAG, "BAG opens");
    int seen = 0;
    for (int p = 0; p < POCKET_COUNT; p++) {
        seen |= 1 << bscr.pocket;
        tap(KEY_RIGHT);
    }
    CHECK(seen == (1 << POCKET_COUNT) - 1 && bscr.pocket == 0, "RIGHT visits all seven pockets and wraps");
    tap(KEY_DOWN);
    tap(KEY_DOWN);
    tap(KEY_RIGHT);
    tap(KEY_LEFT);
    CHECK(bscr.cursor[0] == 2, "each pocket remembers its cursor");

    /* order */
    tap(KEY_SELECT);
    CHECK(bscr.sort == BSORT_NAME, "SELECT changes the order");
    int sorted = 1;
    for (int i = 1; i < bscr.count - 1; i++) {
        const char *a = ITEMS[bscr.list[i - 1]].name, *b = ITEMS[bscr.list[i]].name;
        if (strcmp(a, b) > 0) sorted = 0;
    }
    CHECK(sorted, "A TO Z sorts the pocket by name");
    tap(KEY_SELECT);
    int most = 1;
    for (int i = 1; i < bscr.count - 1; i++)
        if (bag[bscr.list[i - 1]] < bag[bscr.list[i]]) most = 0;
    CHECK(bscr.sort == BSORT_MOST && most, "MOST FIRST puts the biggest stacks first");
    tap(KEY_SELECT);
    CHECK(bscr.sort == BSORT_DEFAULT, "and back to the order found");

    /* materials don't open the team */
    bscr.pocket = POCKET_MATERIALS;
    bag_redraw();
    BAG_CUR = 0;
    tap(KEY_A);
    tap(KEY_A);
    CHECK(game_mode == MODE_BAG && bscr.state == BS_DIALOG, "a material only explains itself");
    run_until_idle(bag_busy, 300);

    /* food goes to the team picker */
    bscr.pocket = POCKET_FOOD;
    bag_redraw();
    BAG_CUR = 0;
    tap(KEY_A);
    tap(KEY_A);
    CHECK(game_mode == MODE_PARTY && pscr.ctx == PCTX_ITEM_FIELD, "food asks which kin eats it");
    tap(KEY_B);
    CHECK(game_mode == MODE_BAG && bscr.pocket == POCKET_FOOD, "B goes back to the same pocket");

    /* key items: register, direct use, CREST CASE */
    bscr.pocket = POCKET_KEY;
    bag_redraw();
    BAG_CUR = 0;
    CHECK(bscr.list[0] == ITEM_BIKE, "the KEY pocket lists the BIKE first");
    tap(KEY_A);
    CHECK(bscr.action_count == 3 && bscr.action_id[1] == BA_REGISTER, "key items can be registered");
    choice.cursor = 1;
    tap(KEY_A);
    CHECK(opt.registered == ITEM_BIKE + 1 && registered_item() == ITEM_BIKE, "REGISTER puts the BIKE on SELECT");
    run_until_idle(bag_busy, 300);
    tap(KEY_A);
    tap(KEY_A);   /* USE */
    CHECK(game_mode == MODE_BAG && bscr.state == BS_DIALOG, "a key item is used straight away (no team picker)");
    run_until_idle(bag_busy, 300);
    if (game_mode != MODE_BAG) {           /* the BIKE really mounts and returns to the field */
        if (travel.biking) bike_toggle(0);
        open_start();
        pick(SM_BAG);
        bscr.pocket = POCKET_KEY;
        bag_redraw();
    }
    for (int i = 0; i < bscr.count; i++)
        if (bscr.list[i] == ITEM_CREST_CASE) BAG_CUR = i;
    tap(KEY_A);
    tap(KEY_A);
    CHECK(game_mode == MODE_EXT && ext.update == crest_case_update, "the CREST CASE opens its screen");
    tap(KEY_RIGHT);
    CHECK(crest_case.cursor == 1, "LEFT/RIGHT look at each crest");
    tap(KEY_B);
    CHECK(game_mode == MODE_BAG && bscr.pocket == POCKET_KEY, "and B goes back to the bag");
    tap(KEY_B);
    CHECK(game_mode == MODE_START_MENU, "B closes the bag");
    opt.registered = 0;

    /* in a bout, unusable items are refused */
    bscr.ctx = BAGCTX_BATTLE;
    bscr.pocket = POCKET_FOOD;
    CHECK(!item_battle_usable(ITEM_BERRY_TART), "food is not for bouts");
    bscr.ctx = BAGCTX_FIELD;
}

/* ---------------- LANTERN SHELF ---------------- */

static int box_levels_descending(int b)
{
    int s = storage_box_start(b);
    for (int i = s + 1; i < s + storage_box_count(b); i++)
        if (storage[i - 1].level < storage[i].level) return 0;
    return 1;
}

static void test_shelf(void)
{
    setup_world();
    for (int i = 0; i < 70; i++) {
        Monster m = monster_make((i * 7 + 3) % SP_COUNT, 5 + (i * 13) % 40);
        storage_add(&m);
    }
    CHECK(storage_box_count(0) == 30 && storage_box_count(1) == 30 && storage_box_count(2) == 10,
          "70 kin fill boxes 1, 2 and part of 3");
    opt.shelf_box = 0;
    open_start();
    pick(SM_SHELF);
    CHECK(game_mode == MODE_PC && pc.page == 1, "SHELF opens on the box last viewed");
    tap(KEY_RIGHT);
    CHECK(pc.page == 2 && opt.shelf_box == 1, "RIGHT turns to the next box and remembers it");
    tap(KEY_LEFT);
    tap(KEY_LEFT);
    CHECK(pc.page == 0, "the team is the page before box 1");
    tap(KEY_LEFT);
    CHECK(pc.page == SHELF_PAGES - 1, "and the pages wrap");

    /* deposit goes to the box last viewed */
    opt.shelf_box = 2;
    pc_set_page(0);
    pc.cursor = 3;
    pc_redraw();
    int sp = party[3].species;
    tap(KEY_A);
    choice.cursor = 1; /* DEPOSIT */
    tap(KEY_A);
    run_until_idle(pc_busy, 300);
    CHECK(party_count == 3 && storage_box_count(2) == 11 &&
              storage[storage_box_start(2) + 10].species == sp,
          "DEPOSIT puts the kin at the end of the box last viewed");

    /* withdraw */
    pc_set_page(3);
    pc.cursor = 10;
    pc_redraw();
    tap(KEY_A);
    choice.cursor = 1; /* WITHDRAW */
    tap(KEY_A);
    run_until_idle(pc_busy, 300);
    CHECK(party_count == 4 && party[3].species == sp && storage_count == 70, "WITHDRAW brings it back");

    /* move a kin from box 1 to the end of box 3 */
    pc_set_page(1);
    pc.cursor = 0;
    pc_redraw();
    int moved = storage[0].species;
    tap(KEY_A);
    choice.cursor = 2; /* MOVE */
    tap(KEY_A);
    CHECK(pc.moving, "MOVE picks the kin up");
    tap(KEY_RIGHT);
    tap(KEY_RIGHT);
    CHECK(pc.page == 3 && pc_rows() == 11, "the box shows a spot at the end");
    pc.cursor = 10;
    tap(KEY_A);
    CHECK(!pc.moving && storage_box_count(0) == 29 && storage_box_count(2) == 11 &&
              storage[storage_box_start(2) + 10].species == moved,
          "A puts it down in the other box");
    /* a full box refuses */
    pc_set_page(3);
    pc.cursor = 0;
    tap(KEY_A);
    choice.cursor = 2;
    tap(KEY_A);
    tap(KEY_LEFT);
    pc.cursor = 0;
    tap(KEY_A);
    CHECK(pc.state == SH_DIALOG && pc.moving, "a full box refuses the kin");
    run_until_idle(pc_busy, 300);
    tap(KEY_B);
    CHECK(!pc.moving, "B puts it back");

    /* release asks twice */
    pc_set_page(1);
    pc.cursor = 0;
    pc_redraw();
    int before = storage_count;
    tap(KEY_A);
    choice.cursor = 3; /* RELEASE */
    tap(KEY_A);
    for (int f = 0; f < 200 && !choice.active; f++) step(0);
    choice.cursor = 1; /* NO */
    tap(KEY_A);
    run_until_idle(pc_busy, 300);
    CHECK(storage_count == before, "NO keeps the kin");
    tap(KEY_A);
    choice.cursor = 3;
    tap(KEY_A);
    for (int f = 0; f < 200 && !choice.active; f++) step(0);
    tap(KEY_A);   /* YES */
    for (int f = 0; f < 200 && !choice.active; f++) step(f & 1 ? 0 : KEY_A);
    CHECK(choice.active && storage_count == before, "YES asks a second time");
    choice.cursor = 0;
    tap(KEY_A);
    run_until_idle(pc_busy, 300);
    CHECK(storage_count == before - 1, "the second YES releases it");

    /* sorting */
    pc_set_page(2);
    pc_redraw();
    tap(KEY_START);
    CHECK(pc.state == SH_TOOLS && pc.act_id[0] == SHA_SORT_BOX, "START opens the tools");
    tap(KEY_A);
    CHECK(pc.state == SH_SORT, "SORT THIS BOX asks how");
    choice.cursor = SORT_LEVEL;
    tap(KEY_A);
    CHECK(box_levels_descending(1), "SORT by LEVEL puts the highest first");
    storage_sort_all(SORT_NUMBER);
    int by_number = 1;
    for (int i = 1; i < storage_count; i++)
        if (storage[i - 1].species > storage[i].species) by_number = 0;
    CHECK(by_number && storage_box_count(0) == 30, "SORT ALL BOXES by NUMBER lays the Shelf out again");
    tap(KEY_START);
    for (int i = 0; i < pc.act_n; i++)
        if (pc.act_id[i] == SHA_BY_TYPE) choice.cursor = i;
    tap(KEY_A);
    run_until_idle(pc_busy, 300);
    int grouped = 1;
    for (int i = 1; i < storage_count; i++) {
        int a = SPECIES[storage[i - 1].species].type1, b = SPECIES[storage[i].species].type1;
        if (a > b) grouped = 0;
    }
    CHECK(grouped && pc.page == 1, "BOXES BY TYPE groups the kin by type");

    /* find by type */
    tap(KEY_START);
    for (int i = 0; i < pc.act_n; i++)
        if (pc.act_id[i] == SHA_FIND) choice.cursor = i;
    tap(KEY_A);
    CHECK(pc.state == SH_FIND, "FIND BY TYPE asks for a type");
    while (pc.find_pick != T_BLAZE) tap(KEY_RIGHT);
    tap(KEY_A);
    Monster at = pc_mon(pc.cursor);
    CHECK(pc.find_type == T_BLAZE && pc.found_n > 0 &&
              (SPECIES[at.species].type1 == T_BLAZE || SPECIES[at.species].type2 == T_BLAZE),
          "it jumps to a kin of that type");
    if (pc.found_n > 1) {
        tap(KEY_SELECT);
        CHECK(pc.found_k == 1, "SELECT jumps to the next one");
    }
    tap(KEY_B);
    CHECK(pc.find_type < 0 && game_mode == MODE_PC, "B ends the search");

    /* summary of a stored kin */
    pc_set_page(2);
    pc.cursor = 4;
    pc_redraw();
    int want = storage[storage_box_start(1) + 4].species;
    tap(KEY_A);
    choice.cursor = 0; /* SUMMARY */
    tap(KEY_A);
    CHECK(game_mode == MODE_SUMMARY && sum.src == SUMSRC_SHELF && sum_mon()->species == want,
          "SUMMARY shows the stored kin");
    tap(KEY_DOWN);
    CHECK(sum.slot == 5, "UP/DOWN go through the box");
    tap(KEY_B);
    CHECK(game_mode == MODE_PC && pc.page == 2 && pc.cursor == 5, "B goes back to the Shelf, on that kin");
    tap(KEY_B);
    CHECK(game_mode == MODE_START_MENU, "B closes the Shelf");

    /* boxes survive a save */
    static u8 sram[32768];
    memset(sram, 0xFF, sizeof(sram));
    int b2 = storage_box_count(1);
    opt.registered = ITEM_HOE + 1;
    save_write_to(sram);
    new_game();
    CHECK(save_load_from(sram) == 4 && storage_box_count(1) == b2 && opt.registered == ITEM_HOE + 1,
          "boxes and the registered item survive a save");
    opt.registered = 0;
}

/* ---------------- Almanac ---------------- */

static void test_almanac(void)
{
    setup_world();
    for (int sp = 0; sp < SP_COUNT; sp++) dex_seen[sp] = 1;
    dex_caught[SP_PYREFOX] = 1;
    open_start();
    pick(SM_ALMANAC);
    CHECK(game_mode == MODE_DEX && dex_list_n == SP_COUNT, "the Almanac lists every kin");
    tap(KEY_START);
    CHECK(dex.state == 2, "START opens the filter");
    tap(KEY_DOWN);
    tap(KEY_RIGHT);
    tap(KEY_RIGHT);   /* TYPE: BLAZE */
    int ok = dex_list_n > 0;
    for (int i = 0; i < dex_list_n; i++)
        if (SPECIES[dex_list[i]].type1 != T_BLAZE && SPECIES[dex_list[i]].type2 != T_BLAZE) ok = 0;
    CHECK(dexf.type == T_BLAZE + 1 && ok, "the TYPE filter keeps only BLAZE kin");
    tap(KEY_A);
    CHECK(dex.state == 0 && SPECIES[dex.cursor].type1 == T_BLAZE, "A closes the filter on a matching kin");
    memset(&dexf, 0, sizeof(dexf));
    dexf.rarity = R_LEGEND + 1;
    dex_build_list();
    ok = dex_list_n > 0;
    for (int i = 0; i < dex_list_n; i++)
        if (SPECIES[dex_list[i]].rarity != R_LEGEND) ok = 0;
    CHECK(ok, "the RARITY filter keeps only legends");
    memset(&dexf, 0, sizeof(dexf));
    dexf.own = DF_FRIENDS;
    dex_build_list();
    CHECK(dex_list_n == dex_caught_count(), "FRIENDS shows the befriended kin");
    memset(&dexf, 0, sizeof(dexf));
    dexf.region = REG_VALE + 1;
    dex_build_list();
    int has_flarix = 0;
    for (int i = 0; i < dex_list_n; i++) has_flarix |= dex_list[i] == SP_FLARIX;
    CHECK(has_flarix && dex_list_n < SP_COUNT, "PLACE: THE VALE has the starters, not everyone");
    memset(&dexf, 0, sizeof(dexf));
    dexf.type = T_ASTRAL + 1;
    dexf.own = DF_FRIENDS;
    dexf.rarity = R_COMMON + 1;
    dex_build_list();
    dex_list_redraw();
    tap(KEY_A);
    CHECK(dex_list_n == 0 && dex.state == 0, "an empty result is shown and A does nothing");
    memset(&dexf, 0, sizeof(dexf));
    dex_build_list();

    /* every page (with fusion signatures shown) fits the panel */
    int narrow = 1, fusion_sig = 0;
    for (int s = 0; s < SP_COUNT; s++) {
        dex_build_content(s);
        for (int k = 0; k < dex.content_lines; k++) {
            const PanelLine *l = &dex.lines[k];
            int w = text_width(l->text) + (l->kind == PL_MOVE ? 32 : 0);
            if (l->kind != PL_STAT && w > panel_cols * 8 - 8) {
                narrow = 0;
                printf("  %s: \"%s\" is too wide\n", SPECIES[s].name, l->text);
            }
            if (SPECIES[s].rarity == R_FUSION && !strcmp(l->text, "Woven from the energy")) fusion_sig++;
        }
    }
    CHECK(narrow, "every Almanac line fits the panel (fusion signatures shown)");
    int fusions = 0;
    for (int s = 0; s < SP_COUNT; s++) fusions += SPECIES[s].rarity == R_FUSION;
    CHECK(fusion_sig == fusions, "met fusion kin show what they are woven from");
    tap(KEY_B);
    CHECK(game_mode == MODE_START_MENU, "B leaves the Almanac");
}

/* ---------------- quest log ---------------- */

static const QuestDef TEST_QUESTS[4] = {
    { "", "" },
    { "LOST LANTERN", "Find the lantern the lamplighter dropped somewhere along the lake shore." },
    { "BERRY BASKET", "Bring three GLOWBERRY to REEVE." },
    { "OLD FRIEND", "Say hello to the hermit." },
};

static void test_quest_log(void)
{
    setup_world();
    open_start();
    pick(SM_QUESTS);
    CHECK(game_mode == MODE_EXT && ext.update == qlog_update && qlog.count == 0, "QUESTS opens the (empty) log");
    tap(KEY_B);
    CHECK(game_mode == MODE_START_MENU, "B goes back to the START menu");

    quest_defs = TEST_QUESTS;
    quest_def_count = 4;
    quest.stage[1] = 255;
    quest.stage[2] = 1;
    pick(SM_QUESTS);
    CHECK(qlog.count == 2 && qlog.open == 1 && qlog.ids[0] == 2 && qlog.ids[1] == 1,
          "started quests are listed, open ones first");
    tap(KEY_DOWN);
    tap(KEY_A);
    CHECK(qlog.state == 1 && dex.content_lines >= 4 && (REG_DISPCNT & DCNT_BG2), "A shows the quest's goal");
    tap(KEY_B);
    CHECK(qlog.state == 0 && !(REG_DISPCNT & DCNT_BG2), "B goes back to the list");
    tap(KEY_B);
    CHECK(game_mode == MODE_START_MENU, "and B closes the log");
    quest_defs = QUESTS;
    quest_def_count = QUEST_COUNT;
    quest_reset();
}

/* ---------------- Lorebook ---------------- */

static void test_lorebook(void)
{
    setup_world();
    for (int i = 0; i < LORE_COUNT; i++) lore_learn(i);
    open_start();
    pick(SM_LORE);
    CHECK(game_mode == MODE_LORE, "LOREBOOK opens");
    for (int i = 0; i < LORE_CHAPTER_COUNT - 1; i++) tap(KEY_DOWN);
    CHECK(lb.chapter == LORE_CHAPTER_COUNT - 1 && lb.ch_scroll == LORE_CHAPTER_COUNT - LB_CH_ROWS,
          "the chapter list scrolls to the last chapter");
    int all = 1;
    for (int c = 0; c < LORE_CHAPTER_COUNT; c++) {
        int total;
        lore_chapter_known(c, &total);
        lb.chapter = c;
        lb_collect();
        if (lb.count != total) all = 0;
    }
    CHECK(all, "every chapter lists all of its entries");
    tap(KEY_B);
    CHECK(game_mode == MODE_START_MENU, "B leaves the Lorebook");
}

/* ---------------- kin viewer ---------------- */

static void test_kin_viewer(void)
{
    fresh_game();
    debug_open();
    dbg.state = DBG_KIN;
    int sp = SP_MANDRAGOR;
    dbg.sp = sp;
    dbg_kin_redraw();
    int clear = text_width("LEFT/RIGHT: kin") + 12 < 19 * 8 && text_width("L/R: 10   A: lustrous") + 12 < 19 * 8;
    for (int y = 15; y <= 16; y++)
        for (int x = 19; x < 28; x++)
            if (x != 23 && canvas_banks[y * CANVAS_COLS + x] == BANK_UI_STD) clear = 0;
    CHECK(SPECIES[sp].type2 != TYPE_NONE && clear, "the kin viewer's type badges keep clear of its help text");
    canvas_clear();
    game_mode = MODE_FIELD;
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    test_items();
    test_start_menu();
    test_options();
    test_bag();
    test_shelf();
    test_almanac();
    test_quest_log();
    test_lorebook();
    test_kin_viewer();
    if (failures == 0) {
        printf("all ui checks passed\n");
        return 0;
    }
    printf("%d check(s) FAILED\n", failures);
    return 1;
}
