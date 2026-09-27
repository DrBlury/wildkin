/*
 * The ADMIN menu (src/game/admin.c), driven frame by frame with key
 * presses: switching ADMIN MODE on in the title's debug menu (and the save
 * keeping it), the START menu entry, ADD 10000 COINS (and the cap), GIVE
 * ITEM (pickers, quantity, key items), ADD KIN with a custom moveset, a
 * nickname and lustre to the Shelf and to the team, TEACH A MOVE, HEAL
 * TEAM, the save round trip, and older saves loading with admin off.
 */
#include "harness.h"

static u8 sram[32768];

/* ---------------- helpers ---------------- */

static void open_title_debug(int has_save)
{
    title_open(has_save);
    step(0);
    step(KEY_SELECT);
    step(KEY_SELECT | KEY_START);
    step(0);
}

static void to_field(void)
{
    dialog_clear();
    canvas_clear();
    field_setup_bg();
    game_mode = MODE_FIELD;
    settle();
}

static int start_menu_has(int entry)
{
    start_menu_build();
    for (int i = 0; i < start_count; i++)
        if (start_items[i] == entry) return 1;
    return 0;
}

/* From the field: START, walk to ADMIN, A. */
static void open_admin_from_field(void)
{
    to_field();
    tap(KEY_START);
    for (int i = 0; i < SM_COUNT && start_items[start_cursor] != SM_ADMIN; i++) tap(KEY_DOWN);
    tap(KEY_A);
}

static int in_admin(void)
{
    return game_mode == MODE_EXT && ext.update == admin_update;
}

static void main_goto(int row)
{
    for (int i = 0; i < AM_COUNT && adm.main_cursor != row; i++) tap(KEY_DOWN);
}

/* In a picker: pages (R) then single steps until the cursor is on `id`. */
static int pick_goto(int id)
{
    for (int i = 0; i < 400 && adm_pick_id() != id; i++) {
        int at = -1;
        for (int k = 0; k < adm.count; k++)
            if (adm.ids[k] == id) at = k;
        if (at < 0) return 0;
        if (at >= adm.cursor + ADM_ROWS) tap(KEY_R);
        else if (at <= adm.cursor - ADM_ROWS) tap(KEY_L);
        else tap(at > adm.cursor ? KEY_DOWN : KEY_UP);
    }
    return adm_pick_id() == id;
}

static void form_goto(int row)
{
    for (int i = 0; i < AF_COUNT && adm.row != row; i++) tap(adm.row < row ? KEY_DOWN : KEY_UP);
}

/* the name slate (as in test_names.c) */
static void nm_goto(int row, int col)
{
    for (int i = 0; i < 12 && nm.row != row; i++) tap(nm.row < row ? KEY_DOWN : KEY_UP);
    for (int i = 0; i < 12 && nm.col != col; i++) tap(nm.col < col ? KEY_RIGHT : KEY_LEFT);
}

static void nm_carve(const char *s)
{
    for (; *s; s++)
        for (int r = 0; r < 4; r++)
            for (int c = 0; c < NM_COLS; c++)
                if (NM_KEYS[r][c] == *s) {
                    nm_goto(r, c);
                    tap(KEY_A);
                    r = 4;
                    break;
                }
}

static void run_admin_dialog(void)
{
    for (int f = 0; f < 600 && adm.state == AD_DIALOG; f++) step((f & 3) == 0 ? KEY_A : 0);
}

/* ---------------- tests ---------------- */

static void test_enable(void)
{
    fresh_game();
    give_starter();
    opt.admin = 0;
    CHECK(sizeof(opt) == 16, "options are still 16 bytes");
    CHECK(!start_menu_has(SM_ADMIN), "no ADMIN in the START menu while admin mode is off");

    /* a save on the cartridge: the debug menu writes the switch into it */
    memset(host_sram, 0xFF, sizeof(host_sram));
    CHECK(save_write(), "a game is saved");
    open_title_debug(1);
    CHECK(game_mode == MODE_EXT && dbg.state == DBG_MENU, "SELECT+START on the title opens the debug menu");
    for (int i = 0; i < DBG_ITEM_COUNT && dbg.cursor != DBGI_ADMIN; i++) tap(KEY_DOWN);
    CHECK(dbg.cursor == DBGI_ADMIN && !strcmp(DBG_ITEMS[dbg.cursor], "ADMIN MODE"), "the ADMIN MODE row");
    tap(KEY_A);
    CHECK(opt.admin == 1 && dbg.admin_note == 1, "A switches admin mode on and saves it");
    tap(KEY_B);
    CHECK(game_mode == MODE_TITLE && opt.admin == 1, "back on the title (the save reloaded) it is still on");
    opt.admin = 0;
    CHECK(save_load() == SAVE_VERSION && opt.admin == 1, "the save on the cartridge carries the switch");

    /* toggling it off again */
    open_title_debug(1);
    for (int i = 0; i < DBG_ITEM_COUNT && dbg.cursor != DBGI_ADMIN; i++) tap(KEY_DOWN);
    tap(KEY_A);
    CHECK(opt.admin == 0, "A again switches it off");
    tap(KEY_A);
    CHECK(opt.admin == 1, "and on");
    tap(KEY_B);

    /* no save yet: the switch is kept in memory for the new game */
    memset(host_sram, 0xFF, sizeof(host_sram));
    opt.admin = 0;
    new_game();
    open_title_debug(0);
    for (int i = 0; i < DBG_ITEM_COUNT && dbg.cursor != DBGI_ADMIN; i++) tap(KEY_DOWN);
    tap(KEY_A);
    CHECK(opt.admin == 1 && dbg.admin_note == 2, "without a save the switch waits for the first save");
    tap(KEY_B);
    CHECK(opt.admin == 1, "leaving the debug menu keeps it");
    new_game();
    CHECK(opt.admin == 1, "a NEW GAME keeps it too");

    give_starter();
    CHECK(start_menu_has(SM_ADMIN), "ADMIN shows in the START menu once admin mode is on");
    open_admin_from_field();
    CHECK(in_admin() && adm.state == AD_MAIN, "START > ADMIN opens the admin menu");
    tap(KEY_B);
    CHECK(game_mode == MODE_START_MENU, "B goes back to the START menu");
}

static void test_coins(void)
{
    open_admin_from_field();
    money = 3000;
    main_goto(AM_COINS);
    tap(KEY_A);
    CHECK(money == 13000, "ADD 10000 COINS adds 10000c");
    CHECK(strstr(adm.msg, "13000c") != 0, "and shows the new total");
    tap(KEY_A);
    CHECK(money == 23000, "again: 23000c");
    money = 9995000;
    tap(KEY_A);
    CHECK(money == MONEY_CAP && strstr(adm.msg, "+4999c") != 0, "it stops at the purse's cap");
    tap(KEY_A);
    CHECK(money == MONEY_CAP && strstr(adm.msg, "full") != 0, "a full purse says so");
    money = 5000;
}

static void test_items(void)
{
    open_admin_from_field();
    main_goto(AM_ITEM);
    tap(KEY_A);
    CHECK(adm.state == AD_PICK && adm.pf == PF_ITEM && adm.count == ITEM_COUNT, "GIVE ITEM lists every item");
    int sorted = 1;
    for (int i = 1; i < adm.count; i++)
        if (ITEMS[adm.ids[i]].pocket < ITEMS[adm.ids[i - 1]].pocket) sorted = 0;
    CHECK(sorted, "grouped by pocket");
    tap(KEY_RIGHT);
    CHECK(ITEMS[adm_pick_id()].pocket == POCKET_LANTERNS && adm.cursor > 0, "RIGHT jumps to the next pocket");
    tap(KEY_LEFT);
    CHECK(adm.cursor == 0, "LEFT back to the first");
    tap(KEY_R);
    CHECK(adm.cursor == ADM_ROWS, "R pages down");

    bag[ITEM_STAR_LANTERN] = 2;
    CHECK(pick_goto(ITEM_STAR_LANTERN), "walk to the STAR LANTERN");
    tap(KEY_A);
    CHECK(adm.state == AD_QTY && adm.qty == 1, "A asks how many");
    for (int i = 0; i < 4; i++) tap(KEY_UP);
    tap(KEY_R);
    CHECK(adm.qty == 15, "UP x4 and R: 15");
    tap(KEY_A);
    CHECK(bag[ITEM_STAR_LANTERN] == 17 && adm.state == AD_PICK, "15 more STAR LANTERNs in the bag");
    CHECK(strstr(adm.msg, "Now 17.") != 0, "the picker says how many there are now");
    tap(KEY_A);
    tap(KEY_DOWN);
    CHECK(adm.qty == 99, "DOWN from 1 wraps to 99");
    tap(KEY_B);
    CHECK(adm.state == AD_PICK && bag[ITEM_STAR_LANTERN] == 17, "B leaves the quantity without giving");

    /* A to Z */
    tap(KEY_SELECT);
    CHECK(adm.order[PF_ITEM] == 1 && adm_pick_id() == ITEM_STAR_LANTERN, "SELECT sorts A to Z, same item kept");
    int az = 1;
    for (int i = 1; i < adm.count; i++)
        if (strcmp(ITEMS[adm.ids[i - 1]].name, ITEMS[adm.ids[i]].name) > 0) az = 0;
    CHECK(az, "the A to Z order is alphabetical");
    tap(KEY_SELECT);

    /* a key item comes one at a time */
    int key = -1;
    for (int i = 0; i < ITEM_COUNT && key < 0; i++)
        if (ITEMS[i].pocket == POCKET_KEY && i != ITEM_RUNESTONE) key = i;
    bag[key] = 0;
    CHECK(pick_goto(key), "walk to a key item");
    tap(KEY_A);
    tap(KEY_UP);
    CHECK(adm.qty == 1, "key items: one at a time");
    tap(KEY_A);
    CHECK(bag[key] == 1, "the key item is in the bag");

    /* the last item of the list */
    int last = adm.ids[adm.count - 1];
    tap(KEY_UP);
    for (int i = 0; i < 80 && adm.cursor != adm.count - 1; i++) tap(KEY_R);
    CHECK(adm_pick_id() == last, "R pages to the end of the list");
    tap(KEY_B);
    CHECK(adm.state == AD_MAIN, "B goes back to the admin menu");
}

static int custom_moveset_ok(const Monster *m, int a, int b, int c)
{
    return m->moves[0] == a && m->moves[1] == b && m->moves[2] == c && m->moves[3] == MOVE_NONE &&
           m->pp[0] == MOVES[a].pp && m->pp[1] == MOVES[b].pp && m->pp[2] == MOVES[c].pp;
}

static int learnset_has(int sp, int move)
{
    for (const LearnEntry *e = SPECIES[sp].learnset; e->level; e++)
        if (e->move == move) return 1;
    return 0;
}

static void test_add_kin(void)
{
    open_admin_from_field();
    main_goto(AM_KIN);
    tap(KEY_A);
    CHECK(adm.state == AD_FORM && adm.row == AF_KIN, "ADD KIN opens the form");
    CHECK(adm.draft.moves[0] != MOVE_NONE, "the form starts with the kin's natural moves");
    int sp0 = adm.sp;
    tap(KEY_RIGHT);
    CHECK(adm.sp == (sp0 + 1) % SP_COUNT, "RIGHT: the next species");
    tap(KEY_R);
    CHECK(adm.sp == (sp0 + 11) % SP_COUNT, "R: ten on");
    tap(KEY_A);
    CHECK(adm.state == AD_PICK && adm.pf == PF_SPECIES && adm.count == SP_COUNT && adm_pick_id() == adm.sp,
          "A on KIN opens the species list on the current kin");
    CHECK(pick_goto(SP_DRAKORA), "walk to DRAKORA");
    tap(KEY_A);
    CHECK(adm.state == AD_FORM && adm.sp == SP_DRAKORA, "DRAKORA chosen");

    form_goto(AF_LEVEL);
    int lv = adm.level;
    tap(KEY_L);
    tap(KEY_L);
    CHECK(adm.level == 1 || adm.level == lv - 20, "L: ten levels down (not below 1)");
    for (int i = 0; i < 12; i++) tap(KEY_R);
    CHECK(adm.level == MAX_LEVEL, "R: up to level 100, no further");
    for (int i = 0; i < 5; i++) tap(KEY_L);
    tap(KEY_LEFT);
    tap(KEY_LEFT);
    tap(KEY_RIGHT);
    CHECK(adm.level == 49, "LEFT / RIGHT: one level (49)");
    tap(KEY_RIGHT);
    CHECK(adm.level == 50, "level 50");
    Monster nat = monster_make(SP_DRAKORA, 50);
    CHECK(!memcmp(adm.draft.moves, nat.moves, 4), "the moves follow the level (its natural moves at 50)");

    form_goto(AF_LUSTROUS);
    tap(KEY_A);
    CHECK(adm.lustrous == 1, "LUSTROUS: YES");

    form_goto(AF_NAME);
    tap(KEY_A);
    CHECK(naming_active() && nm.where == NM_DRAFT && nm.species == SP_DRAKORA && nm.lustrous,
          "NAME opens the name slate for the new kin");
    for (int f = 0; f < 3; f++) step(0);
    nm_carve("STORMY");
    tap(KEY_START);
    tap(KEY_A);
    CHECK(in_admin() && adm.state == AD_FORM && !strcmp(adm.draft.name, "STORMY"), "the slate names it STORMY");

    /* a custom moveset from the whole move list */
    int a = M_BONK, b = M_RUNE_BOLT, c = M_SUPERNOVA;
    CHECK(!learnset_has(SP_DRAKORA, a) && !learnset_has(SP_DRAKORA, b), "(moves DRAKORA can't learn)");
    form_goto(AF_MOVE1);
    tap(KEY_A);
    CHECK(adm.state == AD_PICK && adm.pf == PF_FORM_MOVE && adm.count == MOVE_COUNT + 1 && adm.ids[0] == MOVE_NONE,
          "A on a move opens every move, NO MOVE first");
    CHECK(pick_goto(a), "walk to BONK");
    tap(KEY_A);
    CHECK(adm.state == AD_FORM && adm.draft.moves[0] == a && adm.custom, "MOVE 1: BONK");
    form_goto(AF_MOVE1 + 1);
    tap(KEY_A);
    tap(KEY_SELECT);   /* A to Z */
    CHECK(adm.order[PF_FORM_MOVE] == 1, "moves A to Z");
    CHECK(pick_goto(a), "BONK again");
    tap(KEY_A);
    CHECK(adm.state == AD_PICK && strstr(adm.msg, "already") && adm.draft.moves[1] != a, "a move twice is refused");
    CHECK(pick_goto(b), "walk to RUNE BOLT");
    tap(KEY_A);
    CHECK(adm.draft.moves[1] == b, "MOVE 2: RUNE BOLT");
    form_goto(AF_MOVE1 + 2);
    tap(KEY_A);
    CHECK(pick_goto(c), "walk to SUPERNOVA");
    tap(KEY_A);
    form_goto(AF_MOVE4);
    tap(KEY_A);
    CHECK(pick_goto(MOVE_NONE), "NO MOVE");
    tap(KEY_A);
    CHECK(adm.draft.moves[2] == c && adm.draft.moves[3] == MOVE_NONE, "MOVE 3: SUPERNOVA, MOVE 4 cleared");
    form_goto(AF_LEVEL);
    tap(KEY_LEFT);
    tap(KEY_RIGHT);
    CHECK(adm.draft.moves[0] == a && adm.level == 50, "changing the level keeps a custom moveset");
    form_goto(AF_DEST);
    CHECK(adm.to_team == 0, "SEND TO starts on the SHELF");

    int before_store = storage_count, before_team = party_count;
    dex_seen[SP_DRAKORA] = dex_caught[SP_DRAKORA] = 0;
    form_goto(AF_ADD);
    tap(KEY_A);
    CHECK(adm.state == AD_DIALOG, "ADD THIS KIN answers in the message box");
    run_admin_dialog();
    CHECK(adm.state == AD_FORM, "and the form comes back");
    CHECK(storage_count == before_store + 1 && party_count == before_team, "the kin went to the Shelf");
    int ni = storage_newest();
    Monster m = storage_get(ni);
    CHECK(m.species == SP_DRAKORA && m.level == 50 && (m.flags & MF_LUSTROUS), "a lustrous DRAKORA at level 50");
    CHECK(!strcmp(kin_name(&m), "STORMY"), "named STORMY");
    CHECK(custom_moveset_ok(&m, a, b, c), "with BONK, RUNE BOLT, SUPERNOVA and full uses");
    CHECK(m.xp == xp_for_level(50) && m.hp == m.max_hp &&
              m.max_hp == calc_hp_stat(SPECIES[SP_DRAKORA].base[BS_HP], m.pot[0], 50),
          "its XP, HP and stats match its level");
    CHECK(dex_seen[SP_DRAKORA] && dex_caught[SP_DRAKORA], "the Almanac marks it met and befriended");
    CHECK(boxmon_valid(&storage[ni]), "the Shelf entry passes the save check");
    CHECK(m.met_level == 50 && m.met_map == cur_map, "met here, at level 50");

    /* to the team */
    form_goto(AF_DEST);
    tap(KEY_RIGHT);
    CHECK(adm.to_team == 1, "SEND TO: TEAM");
    form_goto(AF_ADD);
    tap(KEY_A);
    run_admin_dialog();
    CHECK(party_count == before_team + 1 && party[party_count - 1].species == SP_DRAKORA &&
              custom_moveset_ok(&party[party_count - 1], a, b, c) && monster_valid(&party[party_count - 1]),
          "with TEAM it joins the team, moves and all");

    /* a full team: to the Shelf instead */
    while (party_count < PARTY_MAX) {
        Monster f = monster_make(SP_NIBBIT, 5);
        give_monster(&f);
    }
    before_store = storage_count;
    tap(KEY_A);
    run_admin_dialog();
    CHECK(party_count == PARTY_MAX && storage_count == before_store + 1, "a full team sends it to the Shelf");

    /* a kin with no move at all is refused */
    for (int k = 0; k < 3; k++) {
        form_goto(AF_MOVE1 + k);
        tap(KEY_A);
        pick_goto(MOVE_NONE);
        tap(KEY_A);
    }
    CHECK(moves_count(adm.draft.moves) == 0, "(every move cleared)");
    before_store = storage_count;
    form_goto(AF_ADD);
    tap(KEY_A);
    run_admin_dialog();
    CHECK(storage_count == before_store, "a kin without moves is not added");
    form_goto(AF_MOVE1);
    tap(KEY_SELECT);
    CHECK(moves_count(adm.draft.moves) > 0 && !adm.custom, "SELECT on a move row: its natural moves again");

    /* changing the species resets the moves */
    form_goto(AF_KIN);
    tap(KEY_RIGHT);
    Monster n2 = monster_make(adm.sp, adm.level);
    CHECK(!memcmp(adm.draft.moves, n2.moves, 4), "another species starts from its own moves");
    tap(KEY_B);
    CHECK(adm.state == AD_MAIN, "B: back to the admin menu");
}

static void test_teach_heal(void)
{
    open_admin_from_field();
    main_goto(AM_TEACH);
    tap(KEY_A);
    CHECK(adm.state == AD_PICK && adm.pf == PF_TEACH_KIN && adm.count == party_count, "TEACH lists the team");
    tap(KEY_A);
    CHECK(adm.pf == PF_TEACH_SLOT && adm.teach == 0 && adm.count == MAX_MOVES, "then the four slots");
    tap(KEY_DOWN);
    Monster *p = &party[0];
    int had = monster_move_count(p);
    tap(KEY_A);
    CHECK(adm.pf == PF_TEACH_MOVE, "then every move");
    CHECK(pick_goto(M_METEOR_FALL), "walk to METEOR FALL");
    tap(KEY_A);
    int at = -1;
    for (int i = 0; i < MAX_MOVES; i++)
        if (p->moves[i] == M_METEOR_FALL) at = i;
    CHECK(at >= 0 && p->pp[at] == MOVES[M_METEOR_FALL].pp && adm.pf == PF_TEACH_SLOT,
          "the team kin learned METEOR FALL with full uses");
    CHECK(monster_move_count(p) == (had >= 2 ? had : had + 1), "in slot 2 (or the first free one)");
    CHECK(strstr(adm.msg, "METEOR FALL") != 0, "the slot list says what it learned");

    /* clearing: never the last move */
    Monster keep = *p;
    for (int i = 1; i < MAX_MOVES; i++) {
        p->moves[i] = MOVE_NONE;
        p->pp[i] = 0;
    }
    adm_pick_open(PF_TEACH_SLOT, 0);
    tap(KEY_A);
    pick_goto(MOVE_NONE);
    tap(KEY_A);
    CHECK(p->moves[0] != MOVE_NONE && strstr(adm.msg, "at least one"), "the last move can't be cleared");
    *p = keep;
    tap(KEY_B);
    tap(KEY_B);
    tap(KEY_B);
    CHECK(adm.state == AD_MAIN, "B, B, B: back to the admin menu");

    for (int i = 0; i < party_count; i++) {
        party[i].hp = 0;
        party[i].status = STATUS_PSN;
        party[i].pp[0] = 0;
    }
    main_goto(AM_HEAL);
    tap(KEY_A);
    int ok = 1;
    for (int i = 0; i < party_count; i++)
        ok &= party[i].hp == party[i].max_hp && party[i].status == STATUS_NONE &&
              party[i].pp[0] == MOVES[party[i].moves[0]].pp;
    CHECK(ok, "HEAL TEAM heals everyone");
    main_goto(AM_BACK);
    tap(KEY_A);
    CHECK(game_mode == MODE_START_MENU, "BACK: the START menu");
}

static void test_save_round_trip(void)
{
    int ni = storage_newest();
    BoxMon want = storage[ni];
    int count = storage_count, cash = money, lanterns = bag[ITEM_STAR_LANTERN];
    CHECK(opt.admin == 1, "(admin mode is on)");
    memset(sram, 0xFF, sizeof(sram));
    CHECK(save_write_to(sram), "the game saves");
    new_game();
    opt.admin = 0;
    CHECK(save_load_from(sram) == SAVE_VERSION, "and loads");
    CHECK(opt.admin == 1, "admin mode survives the save");
    CHECK(storage_count == count && !memcmp(&storage[ni], &want, sizeof(want)), "the added kin is on the Shelf");
    Monster m = storage_get(ni);
    CHECK(m.species == SP_DRAKORA && custom_moveset_ok(&m, M_BONK, M_RUNE_BOLT, M_SUPERNOVA) &&
              !strcmp(kin_name(&m), "STORMY") && (m.flags & MF_LUSTROUS),
          "with its custom moveset, nickname and lustre");
    CHECK(money == cash && bag[ITEM_STAR_LANTERN] == lanterns, "coins and items too");

    /* a save written before admin mode (the byte was padding: 0) */
    SaveData *d = (SaveData *)sram;
    CHECK(d->options[12] == 1, "(the switch is options byte 12)");
    d->options[12] = 0;
    d->checksum = save_checksum(d);
    SaveData *b = (SaveData *)(sram + SAVE_BACKUP_OFFSET);
    b->options[12] = 0;
    b->checksum = save_checksum(b);
    opt.admin = 1;
    CHECK(save_load_from(sram) == SAVE_VERSION && opt.admin == 0 && !start_menu_has(SM_ADMIN),
          "an older version-5 save loads with admin mode off");

    /* a stray value is clamped */
    d->options[12] = 7;
    d->checksum = save_checksum(d);
    CHECK(save_load_from(sram) == SAVE_VERSION && opt.admin == 1, "(a stray byte reads as on, never as 7)");

    /* a version-4 save (no admin byte at all) */
    static SaveDataV4 v4;
    static SaveData cur;
    opt.admin = 0;
    save_capture(&cur);
    memset(&v4, 0, sizeof(v4));
    v4.magic = SAVE_MAGIC;
    v4.version = 4;
    v4.size = sizeof(v4);
    v4.party_count = cur.party_count;
    v4.map = cur.map;
    v4.player_x = cur.player_x;
    v4.player_y = cur.player_y;
    v4.facing = cur.facing;
    for (int i = 0; i < PARTY_MAX; i++) v4.party[i] = monster_to_v4(&cur.party[i]);
    v4.money = cur.money;
    memcpy(v4.flags, cur.flags, 64);
    memcpy(v4.options, cur.options, 16);
    v4.options[12] = 0;
    v4.checksum = fnv_bytes(&v4, sizeof(v4) - sizeof(v4.checksum));
    memset(sram, 0xFF, sizeof(sram));
    memcpy(sram, &v4, sizeof(v4));
    opt.admin = 1;
    CHECK(save_load_from(sram) == 4 && opt.admin == 0, "a version-4 save loads with admin mode off");
}

/* Every string fits where it is drawn (the small font has digits only). */
static void test_fits(void)
{
    int ok = 1;
    for (int i = 0; i < AM_COUNT; i++) {
        ok &= text_width(ADM_MAIN[i]) <= 200;
        char buf[128];
        str_copy(buf, ADM_MAIN_HELP[i]);
        for (char *line = buf, *p = buf;; p++)
            if (*p == '\n' || !*p) {
                int end = !*p;
                *p = 0;
                if (text_width(line) > 208) {
                    printf("   too wide: %s\n", line);
                    ok = 0;
                }
                if (end) break;
                line = p + 1;
            }
    }
    CHECK(ok, "the admin menu's rows and help fit their window");
    ok = 1;
    for (int pf = 0; pf < PF_COUNT; pf++) {
        int w = text_width(ADM_TITLES[pf]);
        if (ADM_ORDER[pf][0])
            for (int o = 0; o < 2; o++) ok &= 16 + w + 8 <= ADM_ORDER_RIGHT - text_width(ADM_ORDER[pf][o]);
        else ok &= 16 + w < 190;
    }
    ok &= 16 + text_width("SLOT: WWWWWWWWWW") < 190;
    CHECK(ok, "picker titles leave room for the order and the count");
    {
        int wi = 0, widest = 0;
        for (int i = 0; i < ITEM_COUNT; i++)
            if (text_width(ITEMS[i].name) > wi) {
                wi = text_width(ITEMS[i].name);
                widest = i;
            }
        int keep = bag[widest];
        bag[widest] = 900;
        admin_give_item(widest, 99);
        bag[widest] = keep;
        CHECK(40 + text_width(adm.msg) <= 230, "the GIVE ITEM result line fits (widest item, 999)");
        printf("   (%s: %d px)\n", adm.msg, text_width(adm.msg));
    }
    int widest_sp = 0, widest_types = 0, widest_mv = 0;
    for (int s = 0; s < SP_COUNT; s++) {
        char buf[32];
        str_copy(buf, TYPE_NAMES[SPECIES[s].type1]);
        if (SPECIES[s].type2 != TYPE_NONE) {
            str_put(buf, " ");
            str_put(buf, TYPE_NAMES[SPECIES[s].type2]);
        }
        if (text_width(SPECIES[s].name) > widest_sp) widest_sp = text_width(SPECIES[s].name);
        if (text_width(buf) > widest_types) widest_types = text_width(buf);
    }
    for (int m = 0; m < MOVE_COUNT; m++)
        if (text_width(MOVES[m].name) > widest_mv) widest_mv = text_width(MOVES[m].name);
    int widest_type = 0;
    for (int t = 0; t < TYPE_COUNT; t++)
        if (text_width(TYPE_NAMES[t]) > widest_type) widest_type = text_width(TYPE_NAMES[t]);
    printf("   (widest: kin %d, kin types %d, move %d, type %d px)\n", widest_sp, widest_types, widest_mv,
           widest_type);
    CHECK(40 + (widest_sp < 88 ? widest_sp : 88) + 4 <= 228 - widest_types, "species rows: name and types apart");
    CHECK(20 + widest_type < 72, "move rows: the type name ends before the move name");
    CHECK(text_width("LUSTROUS") + 98 < 222 - text_width("YES") - 8, "form labels and values apart");
    CHECK(text_width("MOVE 4") + 98 < 146, "form move labels end before the move names");
    CHECK(text_width("ELEMENTAL") <= 64 && text_width("FINAL FORM") <= 64 && text_width("UNCOMMON") <= 64 &&
              text_width("ACC sure") <= 64 && text_width("USES 40") <= 64,
          "the form's left panel lines fit 64 px");
    CHECK(40 + text_width("UP/DOWN 1  L/R 10  A: GIVE") <= 230, "the quantity hint fits");
    CHECK(24 + text_width("Kept for the new game's save.") <= 230, "the debug menu note fits");
}

/* Every admin screen draws without trouble, a few times over. */
static void test_screens(void)
{
    opt.admin = 1;
    open_admin_from_field();
    for (int r = 0; r < AM_COUNT - 1; r++) {
        main_goto(r);
        if (r == AM_COINS || r == AM_HEAL) continue;
        tap(KEY_A);
        for (int k = 0; k < 30; k++) tap(KEY_R);
        for (int k = 0; k < 10; k++) tap(KEY_LEFT);
        tap(KEY_B);
        if (!(in_admin() && adm.state == AD_MAIN)) printf("   r=%d mode=%d in=%d state=%d pf=%d\n", r, game_mode, in_admin(), adm.state, adm.pf);
        CHECK(in_admin() && adm.state == AD_MAIN, "a screen opens, scrolls and closes");
    }
}

int main(void)
{
    test_enable();
    test_coins();
    test_items();
    test_add_kin();
    test_teach_heal();
    test_save_round_trip();
    test_fits();
    test_screens();
    printf("%s: %d failure(s)\n", failures ? "FAILED" : "passed", failures);
    return failures ? 1 : 0;
}
