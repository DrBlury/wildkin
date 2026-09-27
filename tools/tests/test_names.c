/*
 * Kin nicknames: the name rules (kin_name / kin_set_name), the name slate
 * driven by key presses (from the team menu, the summary and after a
 * catch), the Shelf round trip, evolution, the save (v5) and the v4 -> v5
 * migration.
 */
#include "harness.h"

static u8 sram[32768];

/* ---------------- slate helpers ---------------- */

static void nm_goto(int row, int col)
{
    for (int i = 0; i < 12 && nm.row != row; i++) tap(nm.row < row ? KEY_DOWN : KEY_UP);
    if (row == 4) {
        for (int i = 0; i < 4 && nm_wide_key(nm.col) != nm_wide_key(col); i++) tap(KEY_RIGHT);
        return;
    }
    for (int i = 0; i < 12 && nm.col != col; i++) tap(nm.col < col ? KEY_RIGHT : KEY_LEFT);
}

/* Walk the cursor to each letter and press A. */
static void nm_carve(const char *s)
{
    for (; *s; s++) {
        if (*s == ' ') {
            nm_goto(4, NMK_SPACE);
        } else {
            int found = 0;
            for (int r = 0; r < 4 && !found; r++)
                for (int c = 0; c < NM_COLS && !found; c++)
                    if (NM_KEYS[r][c] == *s) {
                        nm_goto(r, c);
                        found = 1;
                    }
            if (!found) continue;
        }
        tap(KEY_A);
    }
}

static void nm_done(void)
{
    tap(KEY_START);
    tap(KEY_A);
}

static int name_is(const Monster *m, const char *s)
{
    return strcmp(kin_name(m), s) == 0;
}

/* ---------------- rules ---------------- */

static void test_rules(void)
{
    Monster m = monster_make(SP_FLARIX, 5);
    CHECK(m.name[0] == 0 && name_is(&m, "FLARIX"), "a new kin has no nickname and goes by its species");
    kin_set_name(&m, "  EMBER ");
    CHECK(name_is(&m, "EMBER"), "a nickname is trimmed");
    kin_set_name(&m, "ABCDEFGHIJKLMN");
    CHECK(name_is(&m, "ABCDEFGHIJ") && m.name[KIN_NAME_LEN] == 0, "a nickname is clipped to 10 letters");
    kin_set_name(&m, "pip!~7");
    CHECK(name_is(&m, "!7"), "characters the slate can't carve are dropped");
    kin_set_name(&m, "FLARIX");
    CHECK(m.name[0] == 0, "naming a kin after its species clears the nickname");
    kin_set_name(&m, "");
    CHECK(m.name[0] == 0 && name_is(&m, "FLARIX"), "an empty name clears it");
    CHECK(sizeof(BoxMon) == 36 && sizeof(Monster) == 56, "kin are 56 bytes, Shelf kin 36");
    CHECK(sizeof(SaveData) <= SAVE_SLOT_SIZE, "the named save still fits its 16 KB slot");
    printf("   (SaveData is %u of %u bytes)\n", (unsigned)sizeof(SaveData), (unsigned)SAVE_SLOT_SIZE);
}

/* ---------------- the slate from the team screen ---------------- */

static void open_team_name(int slot)
{
    game_mode = MODE_FIELD;
    dialog_clear();
    tap(KEY_START);
    start_menu_build();
    for (int i = 0; i < start_count; i++)
        if (start_items[i] == SM_KIN) start_cursor = i;
    tap(KEY_A);
    pscr.cursor = slot;
    tap(KEY_A);                             /* the submenu */
    for (int i = 0; i < pscr.submenu_count; i++)
        if (str_eq(pscr.submenu[i], "NAME")) {
            for (int k = 0; k < i; k++) tap(KEY_DOWN);
        }
    tap(KEY_A);
}

static void test_slate(void)
{
    fresh_game();
    give_starter();
    Monster second = monster_make(SP_AQUAPO, 6);
    give_monster(&second);
    open_team_name(1);
    CHECK(naming_active() && nm.idx == 1 && nm.where == NM_TEAM, "NAME in the team menu opens the name slate");
    step(0);
    CHECK(!nm.dirty && canvas_banks[0] == BANK_UI_STD && canvas_banks[CANVAS_CELLS - 1] == BANK_UI_STD,
          "the slate draws itself");
    nm_carve("TIDE");
    CHECK(nm.len == 4 && !strcmp(nm.buf, "TIDE"), "the D-pad and A carve letters");
    tap(KEY_B);
    CHECK(nm.len == 3 && !strcmp(nm.buf, "TID"), "B erases the last letter");
    nm_goto(4, NMK_ERASE);
    tap(KEY_A);
    CHECK(!strcmp(nm.buf, "TI"), "ERASE erases too");
    nm_carve("P 2");
    CHECK(!strcmp(nm.buf, "TIP 2"), "SPACE and digits carve");
    nm_done();
    CHECK(game_mode == MODE_PARTY && name_is(&party[1], "TIP 2") && party[0].name[0] == 0,
          "DONE names the kin and goes back to the team screen");

    /* full slate: jumps to DONE */
    open_team_name(0);
    CHECK(naming_active() && nm.len == 0, "the starter has no name yet");
    nm_carve("ABCDEFGHIJ");
    CHECK(nm.len == KIN_NAME_LEN && nm.row == 4 && nm_wide_key(nm.col) == NMK_DONE,
          "a full slate moves the cursor to DONE");
    nm_carve("K");
    CHECK(nm.len == KIN_NAME_LEN, "an eleventh letter is refused");
    nm_done();
    CHECK(name_is(&party[0], "ABCDEFGHIJ"), "a ten-letter name fits");

    /* B on an empty slate leaves the name as it was */
    open_team_name(1);
    CHECK(!strcmp(nm.buf, "TIP 2"), "the slate starts with the current nickname");
    for (int i = 0; i < 6; i++) tap(KEY_B);
    CHECK(game_mode == MODE_PARTY && name_is(&party[1], "TIP 2"), "B on an empty slate leaves it unchanged");

    /* DONE on an empty slate clears the nickname */
    open_team_name(1);
    for (int i = 0; i < 5; i++) tap(KEY_B);
    nm_done();
    CHECK(party[1].name[0] == 0 && name_is(&party[1], "AQUAPO"), "DONE with nothing carved clears the nickname");
    tap(KEY_B);
}

/* ---------------- summary, Shelf, names on screens ---------------- */

static void test_shelf_and_summary(void)
{
    fresh_game();
    give_starter();
    kin_set_name(&party[0], "SPARK");
    Monster s = monster_make(SP_ZAPPET, 9);
    kin_set_name(&s, "VOLTINA");
    storage_add(&s);
    CHECK(storage_count == 1 && !strcmp(box_name(&storage[0]), "VOLTINA"), "a named kin keeps its name on the Shelf");
    Monster back = storage_get(0);
    CHECK(name_is(&back, "VOLTINA"), "and when it comes back off the Shelf");
    Monster ten = monster_make(SP_ZAPPET, 9);
    kin_set_name(&ten, "ABCDEFGHIJ");
    storage_add(&ten);
    CHECK(!strcmp(box_name(&storage[1]), "ABCDEFGHIJ"), "a ten-letter name round-trips the packed Shelf slot");
    Monster t = storage_take(1);
    CHECK(name_is(&t, "ABCDEFGHIJ") && t.name[KIN_NAME_LEN] == 0, "taking it back keeps all ten letters");
    Monster plain = monster_make(SP_GOLEMIT, 4);
    storage_add(&plain);
    CHECK(!strcmp(box_name(&storage[1]), "GOLEMIT"), "an unnamed Shelf kin shows its species");

    /* the summary of a Shelf kin: SELECT names it */
    summary_open_shelf(0);
    tap(KEY_SELECT);
    CHECK(naming_active() && nm.where == NM_SHELF && nm.idx == 0, "SELECT in a Shelf kin's summary opens the slate");
    for (int i = 0; i < 7; i++) tap(KEY_B);
    nm_carve("VOLT");
    nm_done();
    CHECK(game_mode == MODE_SUMMARY && !strcmp(box_name(&storage[0]), "VOLT"), "the Shelf kin is renamed");

    /* the team summary too */
    summary_open(0, MODE_PARTY);
    pscr.ctx = PCTX_FIELD;
    tap(KEY_SELECT);
    CHECK(naming_active() && nm.where == NM_TEAM, "SELECT in a team kin's summary opens the slate");
    tap(KEY_B);
    nm_done();
    CHECK(game_mode == MODE_SUMMARY && name_is(&party[0], "SPAR"), "and renames it");

    /* the team screen, the Shelf list and the bout HUD use the nickname */
    party_screen_open(PCTX_FIELD, 0);
    CHECK(game_mode == MODE_PARTY, "team screen opens");
    game_mode = MODE_FIELD;
    battle_start_wild(monster_make(SP_NIBBIT, 3));
    int said = 0;
    for (int f = 0; f < 3000 && battle.state != BST_ACTION; f++) {
        for (int i = 0; i < battle.ev_count; i++)
            if (battle.ev[i].type == EV_TEXT && strstr(battle.ev[i].text, "Out you come, SPAR!")) said = 1;
        step((f & 7) == 0 ? KEY_A : 0);
    }
    CHECK(said, "a bout calls your kin by its nickname");
    CHECK(!strcmp(battle.disp[SIDE_ALLY].name, "SPAR") && !strcmp(battle.disp[SIDE_ENEMY].name, "NIBBIT"),
          "the HUD shows the nickname (and the wild kin's species)");
    fresh_game();
}

/* ---------------- evolution ---------------- */

static void run_evolution(int slot, int into)
{
    evo_request(slot, into);
    evolve_start_next();
    for (int f = 0; f < 2000 && game_mode == MODE_EVOLVE; f++) step((f & 7) == 0 && f > 400 ? KEY_A : 0);
    run_dialog(600);
}

static void test_evolution(void)
{
    fresh_game();
    Monster a = monster_make(SP_FLARIX, 16), b = monster_make(SP_AQUAPO, 16);
    kin_set_name(&a, "CINDER");
    give_monster(&a);
    give_monster(&b);
    run_evolution(0, SP_PYREFOX);
    CHECK(party[0].species == SP_PYREFOX && name_is(&party[0], "CINDER"), "growing keeps a nickname");
    run_evolution(1, SP_AXOLURK);
    CHECK(party[1].species == SP_AXOLURK && name_is(&party[1], "AXOLURK"),
          "a kin without a nickname shows its new species name");
    fresh_game();
}

/* ---------------- catching ---------------- */

static int catch_one(int yes, const char *name)
{
    bag[ITEM_STAR_LANTERN] = 20;
    Monster target = monster_make(SP_PUFFOWL, 7);
    target.hp = 1;
    target.status = STATUS_SLP;
    battle_start_wild(target);
    for (int f = 0; f < 3000 && battle.state != BST_ACTION; f++) step((f & 7) == 0 ? KEY_A : 0);
    int asked = 0;
    for (int k = 0; k < 10 && game_mode == MODE_BATTLE && !asked; k++) {
        battle_item_result(ITEM_STAR_LANTERN, 0);
        for (int f = 0; f < 1500 && game_mode == MODE_BATTLE && battle.state != BST_ACTION; f++) {
            if (battle.ev_count && battle.ev[0].type == EV_NAME && choice.active) {
                asked = 1;
                if (!yes) tap(KEY_DOWN);
                tap(KEY_A);
                break;
            }
            step((f & 7) == 0 ? KEY_A : 0);
        }
    }
    if (!asked) return 0;
    if (yes) {
        if (!naming_active()) return 0;
        nm_carve(name);
        nm_done();
        if (game_mode != MODE_BATTLE) return 0;
    }
    for (int f = 0; f < 3000 && game_mode == MODE_BATTLE; f++) step((f & 7) == 0 ? KEY_A : 0);
    run_dialog(600);
    return 1;
}

static void test_catch(void)
{
    fresh_game();
    Monster c = monster_make(SP_FLARIX, 30);
    give_monster(&c);
    CHECK(catch_one(1, "HOOT"), "after a catch you're asked for a name and the slate opens");
    CHECK(party_count == 2 && party[1].species == SP_PUFFOWL && name_is(&party[1], "HOOT") &&
          game_mode == MODE_FIELD, "the new kin joins with its name and the bout ends normally");
    CHECK(catch_one(0, 0) && party_count == 3 && party[2].name[0] == 0, "NO keeps the species name");

    /* a catch that goes to the Shelf */
    for (int i = 0; i < 3; i++) {
        Monster f = monster_make(SP_NIBBIT, 5);
        give_monster(&f);
    }
    int before = storage_count;
    CHECK(catch_one(1, "OWLET") && storage_count == before + 1 &&
          !strcmp(box_name(&storage[storage_newest()]), "OWLET"),
          "a kin sent to the Shelf can be named too");
    fresh_game();
}

/* ---------------- saving ---------------- */

static void test_save(void)
{
    fresh_game();
    give_starter();
    kin_set_name(&party[0], "BLAZE");
    Monster s = monster_make(SP_ZAPPET, 9);
    kin_set_name(&s, "ZIP-ZAP!");
    storage_add(&s);
    Monster u = monster_make(SP_GOLEMIT, 9);
    storage_add(&u);
    money = 777;
    memset(sram, 0xFF, sizeof(sram));
    CHECK(save_write_to(sram), "a save with nicknames writes");
    new_game();
    CHECK(save_load_from(sram) == SAVE_VERSION && SAVE_VERSION == 7, "it loads back as version 7");
    CHECK(name_is(&party[0], "BLAZE") && !strcmp(box_name(&storage[0]), "ZIP-ZAP!") &&
          !strcmp(box_name(&storage[1]), "GOLEMIT") && money == 777,
          "team and Shelf nicknames survive a save");

    /* a broken nickname makes the slot invalid (the backup is used) */
    SaveData *d = (SaveData *)sram;
    d->party[0].name[KIN_NAME_LEN] = 'X';
    new_game();
    CHECK(save_load_from(sram) == SAVE_VERSION && name_is(&party[0], "BLAZE"),
          "an unterminated nickname fails the check and the backup slot loads");
}

/* The current game as version 4 wrote it. */
static void write_v4(u8 *dst, int slot_offset)
{
    static SaveData cur;
    static SaveDataV4 v4;
    save_capture(&cur);
    memset(&v4, 0, sizeof(v4));
    v4.magic = SAVE_MAGIC;
    v4.version = 4;
    v4.size = sizeof(v4);
    v4.party_count = cur.party_count;
    v4.map = cur.map;
    v4.player_x = cur.player_x;
    v4.player_y = cur.player_y;
    v4.storage_count = cur.storage_count;
    v4.bag_count = cur.bag_count;
    v4.facing = cur.facing;
    for (int i = 0; i < PARTY_MAX; i++) v4.party[i] = monster_to_v4(&cur.party[i]);
    for (int i = 0; i < STORAGE_MAX; i++) {
        const BoxMon *b = &cur.storage[i];
        BoxMonV4 *o = &v4.storage[i];
        o->species = b->species;
        o->level = b->level;
        o->flags = b->flags;
        o->bond = b->bond;
        memcpy(o->moves, b->moves, sizeof(o->moves));
        o->xp = b->xp;
        o->pot = b->pot;
        o->temper = b->temper;
        o->trait = b->trait;
        o->size = b->size;
        o->met_map = b->met_map;
        o->met_level = b->met_level;
        o->box = b->box;
        o->order = b->order;
    }
    memcpy(v4.bag, cur.bag, sizeof(v4.bag));
    v4.money = cur.money;
    memcpy(v4.seen, cur.seen, 32);
    memcpy(v4.caught, cur.caught, 32);
    memcpy(v4.flags, cur.flags, 64);
    memcpy(v4.satchels, cur.satchels, 64);
    memcpy(v4.wardens, cur.wardens, 64);
    memcpy(v4.lore_known, cur.lore_known, 32);
    memcpy(v4.lore_unread, cur.lore_unread, 32);
    v4.hush_steps = cur.hush_steps;
    v4.step_counter = cur.step_counter;
    memcpy(v4.options, cur.options, 16);
    memcpy(v4.mod_size, cur.mod_size, sizeof(v4.mod_size));
    memcpy(v4.time, cur.time, sizeof(v4.time));
    memcpy(v4.farm, cur.farm, sizeof(v4.farm));
    memcpy(v4.craft, cur.craft, sizeof(v4.craft));
    memcpy(v4.fusion, cur.fusion, sizeof(v4.fusion));
    memcpy(v4.travel, cur.travel, sizeof(v4.travel));
    memcpy(v4.quest, cur.quest, sizeof(v4.quest));
    v4.checksum = fnv_bytes(&v4, sizeof(v4) - sizeof(v4.checksum));
    memcpy(dst + slot_offset, &v4, sizeof(v4));
}

static void test_migration(void)
{
    fresh_game();
    give_starter();
    Monster a = monster_make(SP_AQUAPO, 12);
    a.flags |= MF_LUSTROUS;
    give_monster(&a);
    for (int i = 0; i < 40; i++) {
        Monster m = monster_make(i % SP_COUNT, 5 + i);
        storage_add(&m);
    }
    bag[ITEM_GLOW_LANTERN] = 9;
    money = 4242;
    flag_set(FLAG_SASH);
    lore_learn(LORE_POLARITONS);
    farm.owned = 1;
    field_enter_map(MAP_LAKE, 30, 17, DIR_LEFT);
    Monster p0 = party[0], p1 = party[1];
    BoxMon s39 = storage[39];
    memset(sram, 0xFF, sizeof(sram));
    write_v4(sram, SAVE_BACKUP_OFFSET);     /* only the backup slot holds it */
    new_game();
    CHECK(save_load_from(sram) == 4, "a version 4 save is recognised");
    CHECK(party_count == 2 && party[0].species == p0.species && party[0].xp == p0.xp &&
          !memcmp(party[0].pot, p0.pot, 6) && party[1].hp == p1.hp && (party[1].flags & MF_LUSTROUS) &&
          party[0].name[0] == 0 && name_is(&party[1], "AQUAPO"),
          "its team carries over (with no nicknames)");
    CHECK(storage_count == 40 && storage[39].species == s39.species && storage[39].xp == s39.xp &&
          storage[39].pot == s39.pot && storage[39].order == s39.order && storage[39].name[0] == 0,
          "its Shelf carries over");
    CHECK(bag[ITEM_GLOW_LANTERN] == 9 && money == 4242 && flag(FLAG_SASH) && lore_is_known(LORE_POLARITONS) &&
          farm.owned && cur_map == MAP_LAKE && player.x == 30 && player.facing == DIR_LEFT,
          "bag, coins, flags, lore, modules and position carry over");
    kin_set_name(&party[0], "KINDLE");
    memset(sram, 0xFF, sizeof(sram));
    CHECK(save_write_to(sram), "the migrated game saves");
    new_game();
    CHECK(save_load_from(sram) == SAVE_VERSION && name_is(&party[0], "KINDLE"), "and loads back as the current version");

    /* a broken v4 save is not taken */
    memset(sram, 0xFF, sizeof(sram));
    write_v4(sram, 0);
    sram[40] ^= 0x5A;
    new_game();
    CHECK(save_load_from(sram) == 0, "a damaged version 4 save is refused");
    fresh_game();
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    test_rules();
    test_slate();
    test_shelf_and_summary();
    test_evolution();
    test_catch();
    test_save();
    test_migration();
    if (failures == 0) {
        printf("all names checks passed\n");
        return 0;
    }
    printf("%d check(s) FAILED\n", failures);
    return 1;
}
