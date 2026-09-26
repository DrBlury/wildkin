/*
 * Menu screens: START menu, warden card, options, team, summary, bag, shop
 * and the LANTERN SHELF. Each screen redraws its canvas only when its state
 * changes and pushes its sprites (party icons, portraits) every frame.
 */

#define MODE_LORE    (MODE_TITLE + 1)
#define MODE_OPTIONS (MODE_TITLE + 2)
/* Screens owned by other modules (crafting, fusion, farm board, debug...):
 * ext_open(update, draw, present) runs them without a new mode id. */
#define MODE_EXT     (MODE_TITLE + 3)

static struct { void (*update)(void); void (*draw)(void); void (*present)(void); } ext;

static void ext_open(void (*update)(void), void (*draw)(void), void (*present)(void))
{
    ext.update = update;
    ext.draw = draw;
    ext.present = present;
    game_mode = MODE_EXT;
}

static void dex_open(void);
static void lorebook_open(void);
static void save_prompt(void);
static int lore_known_count(void);
static int lore_unread_count(void);

/* "1234c" */
static void money_text(char *buf, int amount)
{
    buf[0] = 0;
    str_put_int(buf, amount);
    str_put(buf, "c");
}

static void screen_begin(int pattern)
{
    dialog_clear();
    canvas_clear();
    canvas_backdrop(pattern);
    /* full-screen menus hide the scene layers underneath */
    REG_DISPCNT = DCNT_MODE0 | DCNT_BG1 | DCNT_OBJ | DCNT_OBJ_1D;
}

static void mon_level_text(char *buf, const Monster *m)
{
    str_copy(buf, "Lv");
    str_put_int(buf, m->level);
}

static void mon_hp_text(char *buf, const Monster *m)
{
    buf[0] = 0;
    str_put_int(buf, m->hp);
    str_put(buf, "/");
    str_put_int(buf, m->max_hp);
}

static int menu_bob(int selected)
{
    return selected && ((frame_count >> 3) & 1) ? -2 : 0;
}

/* ================================================================ */
/*  START menu                                                      */
/* ================================================================ */

enum { SM_ALMANAC, SM_LORE, SM_KIN, SM_BAG, SM_SHELF, SM_MAP, SM_FIELD, SM_QUESTS, SM_CARD, SM_OPTIONS,
       SM_SAVE, SM_EXIT, SM_COUNT };
static const char *const START_NAMES[SM_COUNT] = {
    "ALMANAC", "LOREBOOK", "KIN", "BAG", "SHELF", "MAP", "FIELD", "QUESTS", "CARD", "OPTIONS", "SAVE", "EXIT",
};
#define START_ROWS 8   /* visible entries; the list scrolls past that */
static u8 start_items[SM_COUNT];
static int start_count, start_cursor, start_scroll, start_card, start_dialog;

static void quest_log_open(void);
static void start_menu_open(void);

static void start_menu_build(void)
{
    start_count = 0;
    for (int i = 0; i < SM_COUNT; i++) {
        if (i == SM_SHELF && !(flag(FLAG_TWIN_CRYSTAL))) continue;
        if (i == SM_KIN && !party_count) continue;
        if (i == SM_FIELD && !(party_count && (travel.crests || bag[ITEM_BIKE] > 0))) continue;   /* travel.c */
        if (i == SM_MAP && bag[ITEM_TOWN_MAP] <= 0) continue;
        start_items[start_count++] = (u8)i;
    }
    if (start_cursor >= start_count) start_cursor = 0;
    if (start_cursor < start_scroll) start_scroll = start_cursor;
    if (start_cursor >= start_scroll + START_ROWS) start_scroll = start_cursor - START_ROWS + 1;
    if (start_scroll > start_count - START_ROWS) start_scroll = start_count > START_ROWS ? start_count - START_ROWS : 0;
}


static void start_menu_draw(void)
{
    char buf[24];
    start_menu_build();
    int rows = start_count < START_ROWS ? start_count : START_ROWS;
    canvas_window(20, 0, 10, rows * 2 + 2, WIN_STD);
    for (int r = 0; r < rows; r++) {
        int i = start_scroll + r, y = 8 + r * LINE_H;
        text_draw(172, y, START_NAMES[start_items[i]]);
        if (start_items[i] == SM_LORE && lore_unread_count())
            text_draw_col(226, y, "*", INK_RED, INK_RED_SH);
        if (i == start_cursor) text_draw(163, y, "{");
    }
    if (start_scroll > 0) text_draw_col(218, 0, "^", INK_BLUE, INK_BLUE_SH);
    if (start_scroll + rows < start_count) text_draw_col(218, rows * 16 + 2, "}", INK_BLUE, INK_BLUE_SH);
    /* the clock */
    canvas_window(0, 0, 12, 3, WIN_STD);
    time_text(buf);
    text_draw_center(48, 5, buf);
}

static void start_menu_open(void)
{
    field_setup_bg(); /* the almanac and lorebook borrow BG2 and WIN0 */
    canvas_clear();
    game_mode = MODE_START_MENU;
    start_card = 0;
    start_dialog = 0;
    start_menu_draw();
}

static void start_menu_close(void)
{
    canvas_clear();
    game_mode = MODE_FIELD;
}

static int trainers_beaten_count(void)
{
    int n = 0;
    for (int t = 0; t < TRAINER_COUNT; t++) n += trainer_beaten(t);
    return n;
}

/* The six Hall crests in a row at cell (cx, cy), 3 cells apart. Bank 9 is
 * the menu backdrop's: over the field it has to be loaded first. */
static void draw_crest_row(int cx, int cy, int gap)
{
    for (int i = 0; i < 16; i++) bg_palette[BANK_MENU_BG * 16 + i] = menu_bg_pal[0][i];
    for (int c = 0; c < CREST_COUNT && c < CREST_ART_COUNT; c++) {
        if (travel_has_crest(c)) canvas_image(cx + c * gap, cy, 2, 2, crest_gfx[c], crest_paper[c], crest_bank[c]);
        else canvas_image(cx + c * gap, cy, 2, 2, crest_empty_gfx, 1, BANK_UI_STD);
    }
}

static int crest_count(void)
{
    int n = 0;
    for (int c = 0; c < CREST_COUNT; c++) n += travel_has_crest(c);
    return n;
}

static void start_card_draw(void)
{
    char buf[40];
    canvas_clear();
    canvas_window(1, 0, 20, 20, WIN_STD);
    text_draw_col(16, 10, "WARDEN CARD", INK_BLUE, INK_BLUE_SH);
    if (flag(FLAG_SASH)) text_draw_col(104, 10, "RING SASH", INK_RED, INK_RED_SH);
    static const char *const LABEL[6] = { "COINS", "BEFRIENDED", "MET", "LORE PAGES", "WARDENS", "SHELF" };
    for (int i = 0; i < 6; i++) {
        int y = 30 + i * LINE_H;
        text_draw(16, y, LABEL[i]);
        buf[0] = 0;
        switch (i) {
        case 0: money_text(buf, money); break;
        case 1: str_put_int(buf, dex_caught_count()); str_put(buf, "/"); str_put_int(buf, SP_COUNT); break;
        case 2: str_put_int(buf, dex_seen_count()); break;
        case 3: str_put_int(buf, lore_known_count()); str_put(buf, "/"); str_put_int(buf, LORE_COUNT); break;
        case 4: str_put_int(buf, trainers_beaten_count()); str_put(buf, "/"); str_put_int(buf, TRAINER_COUNT); break;
        default: str_put_int(buf, storage_count); str_put(buf, "/"); str_put_int(buf, STORAGE_MAX); break;
        }
        text_draw_right(152, y, buf);
    }
    draw_crest_row(3, 16, 3);
}

/* ---------------- the CREST CASE (key item) ---------------- */

static const char *const CREST_GIVES[CREST_COUNT] = {
    "LIGHT: a brighter circle in the dark",
    "SURF: cross open water",
    "STRENGTH: push boulders",
    "FLY: to towns you have visited",
    "Opens the way into the OSSUARY",
    "TELEPORT: back to a HEARTH HALL",
};
static const char *const CREST_HALLS[CREST_COUNT] = {
    "VOLT HALL, LUMEN CITY", "CURRENT HALL, PORT BRINE", "ANVIL HALL, CINDERMOOR",
    "RIME HALL, FROSTHOLLOW", "LANTERN CRYPT, DUSKMERE", "MIRROR HALL, DREAMSPIRE",
};

static struct { int cursor, back_mode; } crest_case;

static void crest_case_redraw(void)
{
    char buf[48];
    screen_begin(0);
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    text_draw_col(16, 8, "CREST CASE", INK_BLUE, INK_BLUE_SH);
    str_copy(buf, "");
    str_put_int(buf, crest_count());
    str_put(buf, "/");
    str_put_int(buf, CREST_COUNT);
    text_draw_right(228, 8, buf);
    canvas_window(0, 3, CANVAS_COLS, 8, WIN_STD);
    draw_crest_row(3, 5, 4);
    int c = crest_case.cursor;
    canvas_fill(3 * 8 + c * 32 - 3, 5 * 8 - 3, 22, 3, 10);
    canvas_fill(3 * 8 + c * 32 - 3, 7 * 8, 22, 3, 10);
    canvas_window(0, 11, CANVAS_COLS, 9, WIN_STD);
    str_copy(buf, CREST_NAMES[c]);
    str_put(buf, " CREST");
    if (travel_has_crest(c)) {
        text_draw_col(16, 98, buf, INK_BLUE, INK_BLUE_SH);
        text_draw(16, 116, CREST_GIVES[c]);
        text_draw_col(16, 134, CREST_HALLS[c], INK_GREEN, INK_GREEN_SH);
    } else {
        text_draw_col(16, 98, "- - - - -", INK_SHADOW, INK_SHADOW);
        str_copy(buf, "Beat the Master of the ");
        text_draw(16, 116, buf);
        text_draw_col(16, 134, CREST_HALLS[c], INK_GREEN, INK_GREEN_SH);
    }
}

static void crest_case_update(void)
{
    int old = crest_case.cursor;
    if (key_rep(KEY_LEFT)) crest_case.cursor = (crest_case.cursor + CREST_COUNT - 1) % CREST_COUNT;
    if (key_rep(KEY_RIGHT)) crest_case.cursor = (crest_case.cursor + 1) % CREST_COUNT;
    if (old != crest_case.cursor) {
        sfx_play(SFX_CURSOR);
        crest_case_redraw();
    }
    if (key_hit(KEY_B) || key_hit(KEY_A)) {
        sfx_play(SFX_CANCEL);
        canvas_clear();
        if (crest_case.back_mode == MODE_BAG) {
            bag_screen_open(BAGCTX_FIELD);
            return;
        }
        if (crest_case.back_mode == MODE_START_MENU) {
            start_menu_open();
            return;
        }
        field_setup_bg();
        game_mode = MODE_FIELD;
    }
}

/* The CREST CASE screen (KEY_CREST_CASE). Opened from the bag it goes back
 * to the bag; from anywhere else, back to the field. */
static void crest_case_open(void)
{
    crest_case.back_mode = game_mode;
    crest_case.cursor = 0;
    dialog_clear();
    crest_case_redraw();
    ext_open(crest_case_update, 0, 0);
}

static void options_open(void);
static void pc_open_from_menu(void);

/* A module's entry (MAP, FIELD...) that answered with a message instead of
 * a screen of its own: show it over the field, then come back. */
static void start_menu_after_module(void)
{
    if (game_mode != MODE_START_MENU) return;   /* it opened its own screen */
    if (dialog_active()) {
        canvas_clear();
        start_dialog = 1;
        return;
    }
    start_menu_draw();
}

static void start_menu_update(void)
{
    if (start_dialog) {
        if (!dialog_update()) {
            start_dialog = 0;
            if (game_mode == MODE_START_MENU) {
                canvas_clear();
                start_menu_draw();
            }
        }
        return;
    }
    if (start_card) {
        if (key_hit(KEY_A) || key_hit(KEY_B) || key_hit(KEY_START)) {
            start_card = 0;
            canvas_clear();
            start_menu_draw();
        }
        return;
    }
    if (key_hit(KEY_START) || key_hit(KEY_B)) {
        sfx_play(SFX_CANCEL);
        start_menu_close();
        return;
    }
    int old = start_cursor;
    if (key_rep(KEY_UP)) start_cursor = (start_cursor + start_count - 1) % start_count;
    if (key_rep(KEY_DOWN)) start_cursor = (start_cursor + 1) % start_count;
    if (old != start_cursor) {
        sfx_play(SFX_CURSOR);
        if (start_count > START_ROWS) canvas_clear();
        start_menu_draw();
    }
    if (!key_hit(KEY_A)) return;
    sfx_play(SFX_CONFIRM);
    switch (start_items[start_cursor]) {
    case SM_ALMANAC: dex_open(); break;
    case SM_LORE: lorebook_open(); break;
    case SM_KIN: party_screen_open(PCTX_FIELD, 0); break;
    case SM_BAG: bag_screen_open(BAGCTX_FIELD); break;
    case SM_SHELF: pc_open_from_menu(); break;
    case SM_MAP:
        worldmap_open(0);
        start_menu_after_module();
        break;
    case SM_FIELD:
        travel_field_menu_open();
        start_menu_after_module();
        break;
    case SM_QUESTS:
        quest_log_open();
        start_menu_after_module();
        break;
    case SM_CARD:
        start_card = 1;
        start_card_draw();
        break;
    case SM_OPTIONS: options_open(); break;
    case SM_SAVE:
        start_menu_close();
        save_prompt();
        break;
    default:
        start_menu_close();
        break;
    }
}

/* ================================================================ */
/*  Options                                                         */
/* ================================================================ */

/*
 * One row per option: the byte it changes, how many values it has and
 * their names, and two lines of help. Add a row here (the list scrolls):
 * the music session's MUSIC / MUSIC VOLUME rows (opt.music, opt.music_vol)
 * slot in after SOUND.
 */
typedef struct {
    const char *label;
    u8 *value;
    u8 count;
    const char *const *names;
    const char *help;
} OptRow;

static const char *const OPT_ON_OFF[2] = { "OFF", "ON" };
static const char *const OPT_SPEED[TEXT_SPEED_COUNT] = { "SLOW", "MID", "FAST", "INSTANT" };
static const char *const OPT_BOUT_SPEED[2] = { "NORMAL", "FAST" };
static const char *const OPT_MUSIC_VOL[3] = { "HIGH", "LOW", "MID" };   /* opt.music_vol: 0 full */

static const OptRow OPT_ROWS_DEF[] = {
    { "TEXT SPEED", &opt.text_speed, TEXT_SPEED_COUNT, OPT_SPEED,
      "How fast text appears.\nHold A or B to hurry it along." },
    { "BOUT ANIMATIONS", &opt.battle_anims, 2, OPT_ON_OFF,
      "OFF plays quick hits instead of\nthe full move animations." },
    { "SOUND", &opt.sound, 2, OPT_ON_OFF,
      "Sound effects for menus, the\nfield and bouts." },
    { "MUSIC", &opt.music, 2, OPT_ON_OFF,
      "Background music in the field,\nin bouts and on the title." },
    { "MUSIC VOLUME", &opt.music_vol, 3, OPT_MUSIC_VOL,
      "How loud the music plays under\nthe sound effects." },
    { "BOUT SPEED", &opt.battle_speed, 2, OPT_BOUT_SPEED,
      "FAST plays bout animations at\ntwice the speed." },
    { "KIN FOLLOWS YOU", &opt.follower, 2, OPT_ON_OFF,
      "Your lead kin walks behind you\nin the field." },
    { "HUD CLOCK", &opt.hud_clock, 2, OPT_ON_OFF,
      "Shows the day and time in a\ncorner of the field." },
    { "BIKE AUTO", &opt.bike_auto, 2, OPT_ON_OFF,
      "ON keeps you on the BIKE outdoors\nuntil you step off it." },
    { "AUTOSAVE", &opt.autosave, 2, OPT_ON_OFF,
      "Save automatically whenever you\nenter a HEARTH HALL." },
};
#define OPT_ROWS ((int)(sizeof(OPT_ROWS_DEF) / sizeof(OPT_ROWS_DEF[0])))
#define OPT_VISIBLE 6

static int opt_cursor, opt_scroll;

static void options_redraw(void)
{
    screen_begin(0);
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    text_draw_col(16, 8, "OPTIONS", INK_BLUE, INK_BLUE_SH);
    canvas_window(0, 3, CANVAS_COLS, 12, WIN_STD);
    for (int r = 0; r < OPT_VISIBLE && opt_scroll + r < OPT_ROWS; r++) {
        int i = opt_scroll + r, y = 32 + r * 14;
        const OptRow *o = &OPT_ROWS_DEF[i];
        if (i == opt_cursor) {
            canvas_fill(12, y - 3, 216, 14, 7);
            text_draw(13, y - 3, "{");
        }
        text_draw(24, y - 3, o->label);
        text_draw_col(154, y - 3, "<", INK_BLUE, INK_BLUE_SH);
        text_draw_center(192, y - 3, o->names[*o->value % o->count]);
        text_draw_col(222, y - 3, ">", INK_BLUE, INK_BLUE_SH);
    }
    if (opt_scroll > 0) text_draw_col(112, 20, "^", INK_BLUE, INK_BLUE_SH);
    if (opt_scroll + OPT_VISIBLE < OPT_ROWS) text_draw_col(112, 106, "}", INK_BLUE, INK_BLUE_SH);
    canvas_window(0, 15, CANVAS_COLS, 5, WIN_STD);
    text_draw(16, 124, OPT_ROWS_DEF[opt_cursor].help);
}

static void options_open(void)
{
    game_mode = MODE_OPTIONS;
    opt_cursor = opt_scroll = 0;
    options_redraw();
}

static void options_update(void)
{
    int old = opt_cursor, change = 0;
    if (key_rep(KEY_UP)) opt_cursor = (opt_cursor + OPT_ROWS - 1) % OPT_ROWS;
    if (key_rep(KEY_DOWN)) opt_cursor = (opt_cursor + 1) % OPT_ROWS;
    if (opt_cursor < opt_scroll) opt_scroll = opt_cursor;
    if (opt_cursor >= opt_scroll + OPT_VISIBLE) opt_scroll = opt_cursor - OPT_VISIBLE + 1;
    if (key_rep(KEY_LEFT)) change = -1;
    if (key_rep(KEY_RIGHT) || key_hit(KEY_A)) change = 1;
    if (change) {
        const OptRow *o = &OPT_ROWS_DEF[opt_cursor];
        *o->value = (u8)((*o->value % o->count + o->count + change) % o->count);
    }
    if (old != opt_cursor || change) {
        sfx_play(SFX_CURSOR);
        options_redraw();
    }
    if (key_hit(KEY_B) || key_hit(KEY_START)) {
        sfx_play(SFX_CANCEL);
        canvas_clear();
        start_menu_open();
    }
}

/* ================================================================ */
/*  Team screen                                                     */
/* ================================================================ */

enum { PS_SELECT, PS_SUBMENU, PS_SWITCH, PS_DIALOG };

static struct {
    int ctx, item, cursor, state, switch_from;
    int submenu_count;
    const char *submenu[4];
} pscr;

static void summary_open(int slot, int return_mode);

/* Panels are whole-cell windows so their palette never mixes with the
 * backdrop: slot 0 is the big card on the left, 1..5 are rows. */
static void party_panel_geometry(int i, int *x, int *y, int *w, int *h)
{
    if (i == 0) {
        *x = 1; *y = 2; *w = 11; *h = 9;
    } else {
        *x = 13; *y = 1 + (i - 1) * 3; *w = 16; *h = 3;
    }
}

static void party_draw_panel(int i)
{
    int cx, cy, cw, ch;
    char buf[16];
    party_panel_geometry(i, &cx, &cy, &cw, &ch);
    const Monster *m = &party[i];
    int x = cx * 8, y = cy * 8, w = cw * 8, h = ch * 8;
    canvas_window(cx, cy, cw, ch, WIN_MENU);
    int fill = 0;
    if (i == pscr.cursor) fill = 7;
    if (pscr.state == PS_SWITCH && i == pscr.switch_from) fill = 14;
    if (fill) canvas_fill(x + 3, y + 3, w - 6, h - 6, fill);
    if (i == 0) {
        mon_level_text(buf, m);
        small_text_draw(48, 28, buf);
        if (m->status) draw_status_badge(6, 5, m->status);
        else if (m->hp == 0) text_draw_col(44, 38, "DOZE", INK_RED, INK_RED_SH);
        text_draw(12, 56, SPECIES[m->species].name);
        menu_hp_bar(40, 74, 48, m->hp, m->max_hp);
        mon_hp_text(buf, m);
        small_text_draw(90 - small_text_width(buf), 78, buf);
    } else {
        text_draw(138, y + 3, SPECIES[m->species].name);
        if (m->status) text_draw_col(206, y + 3, STATUS_NAMES[m->status], INK_RED, INK_RED_SH);
        else if (m->hp == 0) text_draw_col(200, y + 3, "DOZE", INK_RED, INK_RED_SH);
        mon_level_text(buf, m);
        small_text_draw(138, y + 15, buf);
        menu_hp_bar(162, y + 17, 32, m->hp, m->max_hp);
        mon_hp_text(buf, m);
        small_text_draw(229 - small_text_width(buf), y + 14, buf);
    }
}

static const char *party_prompt(void)
{
    if (pscr.state == PS_SWITCH) return "Move to where?";
    switch (pscr.ctx) {
    case PCTX_BATTLE_FORCED: return "Who goes out next?";
    case PCTX_ITEM_FIELD:
    case PCTX_ITEM_BATTLE: return "Use it on which kin?";
    default: return "Choose a kin.";
    }
}

static void party_redraw(void)
{
    screen_begin(0);
    for (int i = 0; i < party_count; i++) party_draw_panel(i);
    canvas_window(0, 16, CANVAS_COLS, 4, WIN_STD);
    text_draw(16, 136, party_prompt());
}

static void party_screen_open(int ctx, int item)
{
    pscr.ctx = ctx;
    pscr.item = item;
    pscr.state = PS_SELECT;
    if (ctx == PCTX_BATTLE_SWITCH || ctx == PCTX_BATTLE_FORCED) pscr.cursor = battle.ally;
    else pscr.cursor = 0;
    if (pscr.cursor >= party_count) pscr.cursor = 0;
    game_mode = MODE_PARTY;
    for (int i = 0; i < party_count; i++) load_monster_icon(i, party[i].species);
    party_redraw();
}

static void party_close(int result)
{
    int ctx = pscr.ctx;
    dialog_clear();
    switch (ctx) {
    case PCTX_FIELD:
        canvas_clear();
        start_menu_open();
        break;
    case PCTX_BATTLE_SWITCH:
        battle_party_result(result, 0);
        break;
    case PCTX_BATTLE_FORCED:
        battle_party_result(result, 1);
        break;
    case PCTX_ITEM_FIELD:
        bag_screen_open(BAGCTX_FIELD);
        break;
    case PCTX_ITEM_BATTLE:
        if (result < 0) bag_screen_open(BAGCTX_BATTLE);
        else battle_item_result(pscr.item, result);
        break;
    }
}

static void party_submenu_choose(int c);

static void party_open_submenu(void)
{
    int n = 0;
    if (pscr.ctx == PCTX_FIELD) {
        pscr.submenu[n++] = "SUMMARY";
        if (party_count > 1) pscr.submenu[n++] = "SWITCH";
    } else {
        pscr.submenu[n++] = "SHIFT";
        pscr.submenu[n++] = "SUMMARY";
    }
    pscr.submenu[n++] = "CANCEL";
    pscr.submenu_count = n;
    pscr.state = PS_SUBMENU;
    choice_open(pscr.submenu, n, CANVAS_COLS, 16);
}

static void party_submenu_choose(int c)
{
    const char *pick = c >= 0 && c < pscr.submenu_count ? pscr.submenu[c] : "CANCEL";
    choice_close();
    pscr.state = PS_SELECT;
    if (str_eq(pick, "SUMMARY")) {
        summary_open(pscr.cursor, MODE_PARTY);
        return;
    }
    if (str_eq(pick, "SWITCH")) {
        pscr.state = PS_SWITCH;
        pscr.switch_from = pscr.cursor;
        party_redraw();
        return;
    }
    if (str_eq(pick, "SHIFT")) {
        const Monster *m = &party[pscr.cursor];
        if (m->hp == 0 || pscr.cursor == battle.ally) {
            pscr.state = PS_DIALOG;
            dlg_say(m->hp == 0 ? "It's dozing and can't go out!" : "It's already out there!");
            return;
        }
        party_close(pscr.cursor);
        return;
    }
    party_redraw();
}

static void party_screen_update(void)
{
    if (pscr.state == PS_DIALOG) {
        if (!dialog_update()) {
            if (pscr.ctx == PCTX_ITEM_FIELD) {
                /* evolution stones hand off to the evolution scene */
                if (evo_count) {
                    evolve_start_next();
                    return;
                }
                party_close(-1);
                return;
            }
            pscr.state = PS_SELECT;
            party_redraw();
        }
        return;
    }
    if (pscr.state == PS_SUBMENU) {
        int c = choice_update();
        if (c == -1) return;
        party_submenu_choose(c == -2 ? pscr.submenu_count - 1 : c);
        return;
    }
    int old = pscr.cursor;
    if (key_rep(KEY_UP)) pscr.cursor = (pscr.cursor + party_count - 1) % party_count;
    if (key_rep(KEY_DOWN)) pscr.cursor = (pscr.cursor + 1) % party_count;
    if (key_hit(KEY_LEFT) && pscr.cursor > 0) pscr.cursor = 0;
    if (key_hit(KEY_RIGHT) && pscr.cursor == 0 && party_count > 1) pscr.cursor = 1;
    if (old != pscr.cursor) {
        party_draw_panel(old);
        party_draw_panel(pscr.cursor);
    }
    if (key_hit(KEY_B)) {
        if (pscr.state == PS_SWITCH) {
            pscr.state = PS_SELECT;
            party_redraw();
            return;
        }
        if (pscr.ctx != PCTX_BATTLE_FORCED) party_close(-1);
        return;
    }
    if (!key_hit(KEY_A)) return;
    if (pscr.state == PS_SWITCH) {
        if (pscr.cursor != pscr.switch_from) {
            Monster t = party[pscr.cursor];
            party[pscr.cursor] = party[pscr.switch_from];
            party[pscr.switch_from] = t;
            for (int i = 0; i < party_count; i++) load_monster_icon(i, party[i].species);
        }
        pscr.state = PS_SELECT;
        party_redraw();
        return;
    }
    switch (pscr.ctx) {
    case PCTX_FIELD:
    case PCTX_BATTLE_SWITCH:
        party_open_submenu();
        break;
    case PCTX_BATTLE_FORCED:
        if (party[pscr.cursor].hp == 0) {
            pscr.state = PS_DIALOG;
            dlg_say("It's dozing and can't go out!");
        } else {
            party_close(pscr.cursor);
        }
        break;
    case PCTX_ITEM_FIELD:
        pscr.state = PS_DIALOG;
        if (!item_use_field(pscr.item, pscr.cursor)) dlg_say("It won't have any effect.");
        break;
    case PCTX_ITEM_BATTLE:
        party_close(pscr.cursor);
        break;
    }
}

static void party_screen_draw(void)
{
    for (int i = 0; i < party_count; i++) {
        int x, y, w, h;
        party_panel_geometry(i, &x, &y, &w, &h);
        int bob = party[i].hp > 0 ? menu_bob(i == pscr.cursor) : 0;
        if (i == 0) spr_push(12, 20 + bob, OT_ICON(i), SQ32, OBANK_NPC + i, 0, 0);
        else spr_push(104, y * 8 - 6 + bob, OT_ICON(i), SQ32, OBANK_NPC + i, 0, 0);
    }
}

/* ================================================================ */
/*  Summary                                                         */
/* ================================================================ */

enum { SUM_INFO, SUM_TRAITS, SUM_STATS, SUM_MOVES, SUM_PAGES };
static const char *const SUM_TITLES[SUM_PAGES] = { "KIN INFO", "TRAITS", "STATS", "MOVES" };

/* src: the team, or one box of the LANTERN SHELF (slot = position in it) */
enum { SUMSRC_TEAM, SUMSRC_SHELF };
static struct { int slot, page, move_cursor, return_mode, src, box; } sum;

static int sum_count(void)
{
    return sum.src == SUMSRC_SHELF ? storage_box_count(sum.box) : party_count;
}

static const Monster *sum_mon(void)
{
    static Monster view;
    if (sum.src != SUMSRC_SHELF) return &party[sum.slot];
    view = storage_get(storage_box_start(sum.box) + sum.slot);
    return &view;
}

/* "SURF  FLY" for the field abilities a species lends (empty when none). */
static void field_ability_text(char *buf, int field)
{
    static const char *const NAMES[5] = { "SURF", "FLY", "TELEPORT", "LIGHT", "STRENGTH" };
    buf[0] = 0;
    for (int i = 0; i < 5; i++)
        if (field & (1 << i)) {
            if (buf[0]) str_put(buf, " ");
            str_put(buf, NAMES[i]);
        }
}

static void summary_redraw(void)
{
    const Monster *m = sum_mon();
    const Species *s = &SPECIES[m->species];
    char buf[48];
    screen_begin(0);
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    text_draw_col(16, 8, SUM_TITLES[sum.page], INK_BLUE, INK_BLUE_SH);
    for (int p = 0; p < SUM_PAGES; p++)
        canvas_fill(186 + p * 10, 12, 6, 6, p == sum.page ? 10 : 4);
    text_draw(172, 8, "<");
    text_draw(226, 8, ">");
    if (sum.src == SUMSRC_SHELF) {
        str_copy(buf, "SHELF BOX ");
        str_put_int(buf, sum.box + 1);
        text_draw_col(84, 8, buf, INK_GREEN, INK_GREEN_SH);
    }

    canvas_window(0, 3, 10, 10, WIN_STD);
    if (sum.page != SUM_MOVES && sum.page != SUM_TRAITS) {
        canvas_window(0, 13, 10, 7, WIN_STD);
        text_draw(8, 112, s->name);
        mon_level_text(buf, m);
        small_text_draw(8, 132, buf);
        if (m->flags & MF_LUSTROUS) text_draw_col(66, 128, "*", INK_RED, INK_RED_SH);
        if (m->status) draw_status_badge(5, 16, m->status);
        else if (m->hp == 0) text_draw_col(36, 128, "DOZE", INK_RED, INK_RED_SH);
    }

    int right_h = sum.page == SUM_MOVES || sum.page == SUM_TRAITS ? 12 : 17;
    canvas_window(10, 3, 20, right_h, WIN_STD);
    int x = 88, y = 32;
    if (sum.page == SUM_INFO) {
        str_copy(buf, "No. ");
        str_put_int3(buf, m->species + 1);
        text_draw(x, y, buf);
        text_draw_right(232, y, s->category);
        draw_type_badge(11, 6, s->type1);
        if (s->type2 != TYPE_NONE) draw_type_badge(15, 6, s->type2);
        text_draw(168, 50, RARITY_NAMES[s->rarity % RARITY_COUNT]);
        y = 72;
        text_draw(x, y, "XP");
        buf[0] = 0;
        str_put_int(buf, (int)m->xp);
        text_draw_right(232, y, buf);
        y += LINE_H;
        text_draw(x, y, "TO NEXT LV");
        buf[0] = 0;
        str_put_int(buf, m->level >= MAX_LEVEL ? 0 : (int)(xp_for_level(m->level + 1) - m->xp));
        text_draw_right(232, y, buf);
        y += LINE_H;
        u32 lo = xp_for_level(m->level), hi = xp_for_level(m->level + 1);
        canvas_fill(x, y + 4, 144, 4, 4);
        canvas_fill(x + 1, y + 5, m->level >= MAX_LEVEL ? 0 : (int)((m->xp - lo) * 142 / (hi - lo)), 2, 10);
        y += 12;
        const Species *evo = s->evo_kind != EVO_NONE ? &SPECIES[s->evo_into] : 0;
        if (evo) {
            str_copy(buf, "Grows ");
            if (s->evo_kind == EVO_LEVEL) {
                str_put(buf, "at Lv");
                str_put_int(buf, s->evo_param);
            } else if (s->evo_kind == EVO_BOND) {
                str_put(buf, "with a strong bond");
            } else {
                str_put(buf, "by ");
                str_put(buf, ITEMS[s->evo_param].name);
            }
            text_draw_col(x, y, buf, INK_GREEN, INK_GREEN_SH);
        } else {
            text_draw_col(x, y, "Fully grown", INK_GREEN, INK_GREEN_SH);
        }
        y += LINE_H;
        text_draw(x, y, "FIELD");
        field_ability_text(buf, s->field);
        if (buf[0]) text_draw_col(x + 40, y, buf, INK_BLUE, INK_BLUE_SH);
        else text_draw_col(x + 40, y, "-", INK_SHADOW, INK_SHADOW);
    } else if (sum.page == SUM_TRAITS) {
        const Temperament *t = &TEMPERAMENTS[m->temper % TEMPERAMENT_COUNT];
        const Trait *tr = &TRAITS[m->trait % TRAIT_COUNT];
        text_draw(x, y, "TEMPERAMENT");
        text_draw_right(232, y, t->name);
        y += LINE_H;
        if (t->up >= 0) {
            str_copy(buf, "+");
            str_put(buf, STAT_NAMES[t->up]);
            int nx = text_draw_col(x + 8, y, buf, INK_RED, INK_RED_SH);
            str_copy(buf, "  -");
            str_put(buf, STAT_NAMES[t->down]);
            text_draw_col(nx, y, buf, INK_BLUE, INK_BLUE_SH);
        } else {
            text_draw_col(x + 8, y, "no strong leanings", INK_BLUE, INK_BLUE_SH);
        }
        y += LINE_H;
        text_draw(x, y, "TRAIT");
        text_draw_right(232, y, tr->name);
        y += LINE_H;
        text_draw(x, y, "SIZE");
        buf[0] = 0;
        str_put(buf, size_name(m->size));
        str_put(buf, " ");
        {
            int h = size_scale(s->height_dm, m->size);
            str_put_int(buf, h / 10);
            str_put(buf, ".");
            str_put_int(buf, h % 10);
            str_put(buf, "m");
        }
        text_draw_right(232, y, buf);
        y += LINE_H;
        text_draw(x, y, "BOND");
        for (int i = 0; i < 5; i++)
            canvas_fill(186 + i * 9, y + 4, 7, 7, m->bond >= 50 * (i + 1) ? 8 : 4);
        if (m->flags & MF_LUSTROUS) {
            y += LINE_H;
            text_draw_col(x, y, "* LUSTROUS *", INK_RED, INK_RED_SH);
        }
        canvas_window(0, 15, CANVAS_COLS, 5, WIN_STD);
        {
            char wrapped[160];
            text_wrap(wrapped, tr->desc, 208);
            char *second = 0;
            for (char *p = wrapped; *p; p++)
                if (*p == '\n') { *p = 0; second = p + 1; break; }
            text_draw(16, 124, wrapped);
            if (second) {
                for (char *p = second; *p; p++)
                    if (*p == '\n') { *p = 0; break; }
                text_draw(16, 140, second);
            } else {
                str_copy(buf, "Met ");
                if (m->met_map < MAP_COUNT) {
                    str_put(buf, "at ");
                    str_put(buf, MAPS[m->met_map].name);
                } else {
                    str_put(buf, "long ago");
                }
                str_put(buf, ", Lv");
                str_put_int(buf, m->met_level);
                text_draw_col(16, 140, buf, INK_BLUE, INK_BLUE_SH);
            }
        }
    } else if (sum.page == SUM_STATS) {
        static const char *const LABELS[5] = { "ATTACK", "DEFENSE", "FOCUS", "WILL", "SPEED" };
        const Temperament *t = &TEMPERAMENTS[m->temper % TEMPERAMENT_COUNT];
        text_draw(x, y, "HP");
        text_draw_col(x + 58, y, potential_grade(m->pot[0]), INK_BLUE, INK_BLUE_SH);
        mon_hp_text(buf, m);
        text_draw_right(232, y, buf);
        menu_hp_bar(x + 40, y + 16, 104, m->hp, m->max_hp);
        y += 24;
        for (int i = 0; i < 5; i++) {
            if (t->up == i) text_draw_col(x, y, LABELS[i], INK_RED, INK_RED_SH);
            else if (t->down == i) text_draw_col(x, y, LABELS[i], INK_BLUE, INK_BLUE_SH);
            else text_draw(x, y, LABELS[i]);
            text_draw_col(x + 58, y, potential_grade(m->pot[1 + i]), INK_BLUE, INK_BLUE_SH);
            buf[0] = 0;
            str_put_int(buf, m->stat[i]);
            text_draw_right(232, y, buf);
            y += LINE_H;
        }
        (void)0;
    } else {
        for (int i = 0; i < MAX_MOVES; i++) {
            int ry = 32 + i * 24;
            int mv = m->moves[i];
            if (i == sum.move_cursor) canvas_fill(86, ry - 2, 148, 20, 7);
            if (mv == MOVE_NONE) {
                text_draw(124, ry, "-");
                continue;
            }
            draw_type_badge(11, ry / 8, MOVES[mv].type);
            text_draw(124, ry, MOVES[mv].name);
            buf[0] = 0;
            str_put_int(buf, m->pp[i]);
            str_put(buf, "/");
            str_put_int(buf, MOVES[mv].pp);
            small_text_draw(232 - small_text_width(buf), ry + 4, buf);
        }
        canvas_window(0, 15, CANVAS_COLS, 5, WIN_STD);
        int mv = m->moves[sum.move_cursor];
        if (mv != MOVE_NONE) {
            const Move *md = &MOVES[mv];
            str_copy(buf, md->cat == CAT_PHYS ? "PHYSICAL" : md->cat == CAT_SPEC ? "ELEMENTAL" : "STATUS");
            text_draw_col(16, 124, buf, INK_BLUE, INK_BLUE_SH);
            buf[0] = 0;
            if (md->power) {
                str_put(buf, "POW ");
                str_put_int(buf, md->power);
                str_put(buf, "  ");
            }
            str_put(buf, "ACC ");
            if (md->acc) str_put_int(buf, md->acc);
            else str_put(buf, "--");
            text_draw_right(224, 124, buf);
            char wrapped[128];
            text_wrap(wrapped, md->desc, 208);
            for (char *p = wrapped; *p; p++)
                if (*p == '\n') { *p = 0; break; }
            text_draw(16, 140, wrapped);
        }
    }
    load_monster_gfx(0, m->species, 0);
}

static void summary_open(int slot, int return_mode)
{
    sum.src = SUMSRC_TEAM;
    sum.slot = slot;
    sum.return_mode = return_mode;
    sum.move_cursor = 0;
    game_mode = MODE_SUMMARY;
    gems_load();
    summary_redraw();
}

/* Summary of a kin on the Shelf (storage index i); B goes back to the Shelf. */
static void summary_open_shelf(int i)
{
    storage_boxes_sync();
    sum.src = SUMSRC_SHELF;
    sum.box = i >= 0 && i < storage_count ? storage[i].box : 0;
    sum.slot = i - storage_box_start(sum.box);
    sum.return_mode = MODE_PC;
    sum.move_cursor = 0;
    game_mode = MODE_SUMMARY;
    gems_load();
    summary_redraw();
}

static void pc_summary_back(int slot);

static void summary_update(void)
{
    int redraw = 0;
    int n = sum_count();
    if (key_hit(KEY_B)) {
        sfx_play(SFX_CANCEL);
        if (sum.return_mode == MODE_PC) {
            pc_summary_back(sum.slot);
        } else {
            game_mode = MODE_PARTY;
            pscr.cursor = sum.slot;
            party_redraw();
        }
        return;
    }
    if (key_hit(KEY_LEFT)) { sum.page = (sum.page + SUM_PAGES - 1) % SUM_PAGES; redraw = 1; }
    if (key_hit(KEY_RIGHT)) { sum.page = (sum.page + 1) % SUM_PAGES; redraw = 1; }
    if (sum.page == SUM_MOVES) {
        int moves = monster_move_count(sum_mon());
        if (key_rep(KEY_UP) && sum.move_cursor > 0) { sum.move_cursor--; redraw = 1; }
        if (key_rep(KEY_DOWN) && sum.move_cursor < moves - 1) { sum.move_cursor++; redraw = 1; }
        if (key_hit(KEY_L) && sum.slot > 0) { sum.slot--; sum.move_cursor = 0; redraw = 1; }
        if (key_hit(KEY_R) && sum.slot < n - 1) { sum.slot++; sum.move_cursor = 0; redraw = 1; }
    } else {
        if (key_rep(KEY_UP) && sum.slot > 0) { sum.slot--; redraw = 1; }
        if (key_rep(KEY_DOWN) && sum.slot < n - 1) { sum.slot++; redraw = 1; }
    }
    if (redraw) summary_redraw();
}

static void summary_draw(void)
{
    spr_push(8, 32, OT_MON_A, SQ64, OBANK_MON_A, 0, 0);
    if (sum.page == SUM_INFO) gem_push(157, 53, SPECIES[sum_mon()->species].rarity);
}

/* ================================================================ */
/*  Bag                                                             */
/* ================================================================ */

/* List orders (SELECT cycles them). */
enum { BSORT_DEFAULT, BSORT_NAME, BSORT_MOST, BSORT_COUNT };
static const char *const BSORT_NAMES[BSORT_COUNT] = { "AS FOUND", "A TO Z", "MOST FIRST" };

enum { BS_LIST, BS_ACTION, BS_DIALOG };
enum { BA_USE, BA_REGISTER, BA_CANCEL };

static struct {
    int ctx, pocket, state, sort;
    int cursor[POCKET_COUNT], scroll[POCKET_COUNT];   /* remembered per pocket */
    int list[ITEM_COUNT + 1], count;                  /* item ids; -1 = close */
    const char *actions[3];
    u8 action_id[3];
    int action_count;
    int close_after;        /* back to the field once the dialog ends */
} bscr;

#define BAG_ROWS 6
#define BAG_CUR bscr.cursor[bscr.pocket]
#define BAG_SCROLL bscr.scroll[bscr.pocket]

/* Can this item be used in a bout? (battle.c knows the kinds.) */
static int item_battle_usable(int item)
{
    return item >= 0 && item < ITEM_COUNT && battle_item_kind_usable(ITEMS[item].kind);
}

/* Field items that act on one kin (the team picker opens first). */
static int item_needs_kin(int item)
{
    switch (ITEMS[item].kind) {
    case IK_HEAL: case IK_FULL_HEAL: case IK_WAKE: case IK_TEA: case IK_SEED: case IK_SHARD:
    case IK_HEAL_CURE: case IK_TEA_ALL: case IK_REVIVE: case IK_FOOD:
        return 1;
    default:
        return 0;
    }
}

static int bag_sort_before(int a, int b)
{
    switch (bscr.sort) {
    case BSORT_NAME: {
        const char *x = ITEMS[a].name, *y = ITEMS[b].name;
        while (*x && *x == *y) { x++; y++; }
        return (u8)*x < (u8)*y;
    }
    case BSORT_MOST: return bag[a] > bag[b];
    default: return a < b;
    }
}

static void bag_build_list(void)
{
    bscr.count = 0;
    for (int i = 0; i < ITEM_COUNT; i++)
        if (ITEMS[i].pocket == bscr.pocket && bag[i] > 0) {
            int k = bscr.count++;
            while (k > 0 && bag_sort_before(i, bscr.list[k - 1])) {
                bscr.list[k] = bscr.list[k - 1];
                k--;
            }
            bscr.list[k] = i;
        }
    bscr.list[bscr.count++] = -1;
    if (BAG_CUR >= bscr.count) BAG_CUR = bscr.count - 1;
    if (BAG_CUR < 0) BAG_CUR = 0;
    if (BAG_SCROLL > BAG_CUR) BAG_SCROLL = BAG_CUR;
    if (BAG_CUR >= BAG_SCROLL + BAG_ROWS) BAG_SCROLL = BAG_CUR - BAG_ROWS + 1;
}

static void bag_redraw(void)
{
    char buf[40];
    screen_begin(0);
    bag_build_list();
    /* left: the pocket, its tab strip, coins and the list order */
    canvas_window(0, 0, 11, 14, WIN_STD);
    text_draw_center(44, 7, POCKET_NAMES[bscr.pocket]);
    text_draw_col(9, 20, "<", INK_BLUE, INK_BLUE_SH);
    text_draw_col(74, 20, ">", INK_BLUE, INK_BLUE_SH);
    for (int p = 0; p < POCKET_COUNT; p++) {
        int x = 18 + p * 8;
        canvas_fill(x, 25, 6, p == bscr.pocket ? 7 : 5, p == bscr.pocket ? 10 : 4);
    }
    text_draw(12, 40, "COINS");
    money_text(buf, money);
    text_draw_right(80, 54, buf);
    if (bscr.ctx == BAGCTX_BATTLE) {
        text_draw_col(12, 78, "IN A BOUT", INK_RED, INK_RED_SH);
    } else {
        text_draw_col(12, 72, BSORT_NAMES[bscr.sort], INK_BLUE, INK_BLUE_SH);
        text_draw_col(12, 88, "SEL: ORDER", INK_SHADOW, INK_SHADOW);
    }

    /* right: the items */
    canvas_window(11, 0, 19, 14, WIN_STD);
    for (int r = 0; r < BAG_ROWS && BAG_SCROLL + r < bscr.count; r++) {
        int idx = BAG_SCROLL + r, y = 8 + r * LINE_H;
        int item = bscr.list[idx];
        if (idx == BAG_CUR) text_draw(94, y, "{");
        if (item < 0) {
            text_draw(104, y, "CLOSE BAG");
            continue;
        }
        if (bscr.ctx == BAGCTX_BATTLE && !item_battle_usable(item))
            text_draw_col(104, y, ITEMS[item].name, INK_SHADOW, INK_SHADOW);
        else
            text_draw(104, y, ITEMS[item].name);
        if (ITEMS[item].pocket == POCKET_KEY) {
            if (opt.registered == item + 1) text_draw_col(206, y, "SEL", INK_BLUE, INK_BLUE_SH);
            continue;
        }
        str_copy(buf, "|");
        str_put_int(buf, bag[item]);
        text_draw_right(228, y, buf);
        if (ITEMS[item].kind == IK_LANTERN) {
            /* in a wild bout: the odds of befriending the foe with this
             * lantern right now; elsewhere: the lantern's base strength */
            int pct = bscr.ctx == BAGCTX_BATTLE ? lantern_catch_pct(item) : -1;
            buf[0] = 0;
            if (bscr.ctx == BAGCTX_BATTLE) {
                if (pct < 0) continue;
                str_put(buf, pct == 0 ? "<1" : "");
                if (pct) str_put_int(buf, pct);
                str_put(buf, "%");
            } else {
                str_put(buf, "x");
                str_put_int(buf, ITEMS[item].param / 10);
                str_put(buf, ".");
                str_put_int(buf, ITEMS[item].param % 10);
            }
            text_draw_col(228 - 24 - text_width(buf), y, buf, INK_BLUE, INK_BLUE_SH);
        }
    }
    if (BAG_SCROLL > 0) text_draw_col(214, 0, "^", INK_BLUE, INK_BLUE_SH);
    if (BAG_SCROLL + BAG_ROWS < bscr.count) text_draw_col(214, 98, "}", INK_BLUE, INK_BLUE_SH);

    /* bottom: icon and description */
    canvas_window(0, 14, CANVAS_COLS, 6, WIN_STD);
    int item = bscr.list[BAG_CUR];
    if (item >= 0) {
        char wrapped[400];
        draw_item_icon(1, 15, item);
        text_wrap(wrapped, ITEMS[item].desc, 184);
        text_draw(40, 120, wrapped);
    } else if (bscr.count == 1) {
        text_draw(16, 120, "Nothing in this pocket yet.\nLEFT / RIGHT: other pockets");
    } else {
        text_draw(16, 120, "Close the bag and go back.");
    }
}

static void bag_screen_open(int ctx)
{
    bscr.ctx = ctx;
    bscr.state = BS_LIST;
    bscr.close_after = 0;
    if (bscr.pocket < 0 || bscr.pocket >= POCKET_COUNT) bscr.pocket = 0;
    game_mode = MODE_BAG;
    bag_redraw();
}

static void bag_close(void)
{
    dialog_clear();
    if (bscr.ctx == BAGCTX_BATTLE) {
        battle_item_result(-1, 0);
    } else {
        canvas_clear();
        start_menu_open();
    }
}

/* Straight back to the field (after using a key item, a seed...). */
static void bag_close_to_field(void)
{
    dialog_clear();
    canvas_clear();
    field_setup_bg();
    game_mode = MODE_FIELD;
}

static void bag_say(const char *text)
{
    bscr.state = BS_DIALOG;
    dlg_say(text);
}

/* Items used where you stand: key items, seeds, fertiliser, lures,
 * waystones, the HUSH BELL. A module may open its own screen. */
static void bag_use_direct(int item)
{
    int ok = item_use_field(item, 0);
    if (game_mode != MODE_BAG) return;
    if (!ok && !dialog_active()) dlg_say("It won't have any effect here.");
    bscr.close_after = ok && ITEMS[item].kind != IK_HUSH;
    if (dialog_active()) {
        bscr.state = BS_DIALOG;
    } else if (bscr.close_after) {
        bag_close_to_field();
    } else {
        bscr.state = BS_LIST;
        bag_redraw();
    }
}

static void bag_use(int item)
{
    int k = ITEMS[item].kind;
    if (bscr.ctx == BAGCTX_BATTLE) {
        if (!item_battle_usable(item)) {
            bag_say("You can't use that here.");
            return;
        }
        if (k == IK_LANTERN || k == IK_XSTAT) {
            dialog_clear();
            battle_item_result(item, battle.ally);
            return;
        }
        party_screen_open(PCTX_ITEM_BATTLE, item);
        return;
    }
    if (k == IK_LANTERN || k == IK_XSTAT) {
        bag_say(k == IK_LANTERN ? "Offer lanterns to tired wild kin during a bout!"
                                : "That clips on during a bout.");
        return;
    }
    if (k == IK_MATERIAL) {
        bag_say("A crafting material. Use it at a kitchen, a cauldron or an anvil.");
        return;
    }
    if (!item_needs_kin(item)) {
        bag_use_direct(item);
        return;
    }
    if (!party_count) {
        bag_say("You don't have any kin yet.");
        return;
    }
    party_screen_open(PCTX_ITEM_FIELD, item);
}

static void bag_register(int item)
{
    char msg[64];
    if (opt.registered == item + 1) {
        opt.registered = 0;
        str_copy(msg, ITEMS[item].name);
        str_put(msg, " is no longer on SELECT.");
    } else {
        opt.registered = (u8)(item + 1);
        str_copy(msg, ITEMS[item].name);
        str_put(msg, " is ready on SELECT.");
    }
    sfx_play(SFX_CONFIRM);
    bag_say(msg);
}

static void bag_open_actions(int item)
{
    int n = 0;
    bscr.actions[n] = "USE";
    bscr.action_id[n++] = BA_USE;
    if (bscr.ctx == BAGCTX_FIELD && ITEMS[item].pocket == POCKET_KEY) {
        bscr.actions[n] = opt.registered == item + 1 ? "UNREGISTER" : "REGISTER";
        bscr.action_id[n++] = BA_REGISTER;
    }
    bscr.actions[n] = "CANCEL";
    bscr.action_id[n++] = BA_CANCEL;
    bscr.action_count = n;
    bscr.state = BS_ACTION;
    choice_open(bscr.actions, n, CANVAS_COLS, 14);
}

static void bag_screen_update(void)
{
    if (bscr.state == BS_DIALOG) {
        if (!dialog_update()) {
            if (game_mode != MODE_BAG) return;
            if (bscr.close_after) {
                bag_close_to_field();
                return;
            }
            bscr.state = BS_LIST;
            bag_redraw();
        }
        return;
    }
    if (bscr.state == BS_ACTION) {
        int c = choice_update();
        if (c == -1) return;
        choice_close();
        bscr.state = BS_LIST;
        int act = c >= 0 && c < bscr.action_count ? bscr.action_id[c] : BA_CANCEL;
        int item = bscr.list[BAG_CUR];
        if (act == BA_USE) bag_use(item);
        else if (act == BA_REGISTER) bag_register(item);
        else bag_redraw();
        return;
    }
    int redraw = 0;
    if (key_rep(KEY_LEFT) || key_hit(KEY_L)) {
        bscr.pocket = (bscr.pocket + POCKET_COUNT - 1) % POCKET_COUNT;
        redraw = 1;
    }
    if (key_rep(KEY_RIGHT) || key_hit(KEY_R)) {
        bscr.pocket = (bscr.pocket + 1) % POCKET_COUNT;
        redraw = 1;
    }
    if (key_rep(KEY_UP)) {
        BAG_CUR = BAG_CUR > 0 ? BAG_CUR - 1 : bscr.count - 1;
        redraw = 1;
    }
    if (key_rep(KEY_DOWN)) {
        BAG_CUR = BAG_CUR < bscr.count - 1 ? BAG_CUR + 1 : 0;
        redraw = 1;
    }
    if (key_hit(KEY_SELECT) && bscr.ctx == BAGCTX_FIELD) {
        int item = bscr.list[BAG_CUR];
        bscr.sort = (bscr.sort + 1) % BSORT_COUNT;
        bag_build_list();
        for (int i = 0; i < bscr.count; i++)
            if (bscr.list[i] == item) BAG_CUR = i;   /* keep the same item selected */
        redraw = 1;
    }
    if (redraw) {
        sfx_play(SFX_CURSOR);
        bag_redraw();
    }
    if (key_hit(KEY_B)) {
        sfx_play(SFX_CANCEL);
        bag_close();
        return;
    }
    if (key_hit(KEY_A)) {
        int item = bscr.list[BAG_CUR];
        if (item < 0) {
            bag_close();
            return;
        }
        sfx_play(SFX_CONFIRM);
        if (bscr.ctx == BAGCTX_BATTLE && !item_battle_usable(item)) {
            bag_say("You can't use that here.");
            return;
        }
        bag_open_actions(item);
    }
}

/* ================================================================ */
/*  Shop                                                            */
/* ================================================================ */

static const u8 SHOP_STOCK[] = {
    ITEM_LANTERN, ITEM_GLOW_LANTERN, ITEM_STAR_LANTERN, ITEM_TONIC, ITEM_BIG_TONIC,
    ITEM_GRAND_TONIC, ITEM_SOOTHE_BALM, ITEM_WAKE_BELL, ITEM_MINT_TEA, ITEM_HUSH_BELL,
    ITEM_BRAVE_CHILI, ITEM_IRONBARK,
    ITEM_BLOOM_SHARD, ITEM_SPARK_SHARD, ITEM_FROST_SHARD,
};
/* What the open shop sells (every town has its own list: shop_open_stock). */
static const u8 *shop_stock = SHOP_STOCK;
static int shop_stock_count = (int)sizeof(SHOP_STOCK);
#define SHOP_COUNT shop_stock_count

static struct { int cursor, scroll, state, qty; } shop;

static void shop_redraw(void)
{
    char buf[32];
    screen_begin(0);
    canvas_window(0, 0, 11, 5, WIN_STD);
    text_draw(12, 8, "COINS");
    money_text(buf, money);
    text_draw_right(80, 22, buf);
    canvas_window(0, 5, 11, 9, WIN_STD);
    text_draw(12, 48, "IN BAG");
    int sel = shop.cursor < SHOP_COUNT ? shop_stock[shop.cursor] : -1;
    if (sel >= 0) {
        buf[0] = 0;
        str_put_int(buf, bag[sel]);
        text_draw_right(80, 64, buf);
    }
    canvas_window(11, 0, 19, 14, WIN_STD);
    for (int r = 0; r < BAG_ROWS && shop.scroll + r <= SHOP_COUNT; r++) {
        int idx = shop.scroll + r, y = 8 + r * LINE_H;
        if (idx == shop.cursor) text_draw(94, y, "{");
        if (idx == SHOP_COUNT) {
            text_draw(104, y, "QUIT");
            continue;
        }
        int item = shop_stock[idx];
        text_draw(104, y, ITEMS[item].name);
        money_text(buf, ITEMS[item].price);
        text_draw_right(228, y, buf);
    }
    canvas_window(0, 14, CANVAS_COLS, 6, WIN_STD);
    if (sel >= 0) {
        char wrapped[160];
        draw_item_icon(1, 15, sel);
        text_wrap(wrapped, ITEMS[sel].desc, 184);
        text_draw(40, 120, wrapped);
    } else {
        text_draw(16, 120, "Please come again!");
    }
    if (shop.state == 1) {
        canvas_window(16, 9, 14, 5, WIN_STD);
        str_copy(buf, "| ");
        str_put_int(buf, shop.qty);
        text_draw(136, 84, buf);
        money_text(buf, shop.qty * ITEMS[sel].price);
        text_draw_right(228, 84, buf);
        text_draw_col(136, 98, "^/} amount", INK_BLUE, INK_BLUE_SH);
    }
}

MAYBE_UNUSED static void shop_open_stock(const u8 *items, int count)
{
    shop_stock = items;
    shop_stock_count = count;
    shop.cursor = shop.scroll = 0;
    shop.state = 0;
    game_mode = MODE_SHOP;
    shop_redraw();
}

static void shop_open(void)
{
    shop_stock = SHOP_STOCK;
    shop_stock_count = (int)sizeof(SHOP_STOCK);
    shop.cursor = shop.scroll = 0;
    shop.state = 0;
    game_mode = MODE_SHOP;
    shop_redraw();
}

static void shop_close(void)
{
    canvas_clear();
    field_setup_bg();
    game_mode = MODE_FIELD;
    dlg_say("Please come again!");
}

static void shop_update(void)
{
    if (shop.state == 2) {
        if (!dialog_update()) {
            shop.state = 0;
            shop_redraw();
        }
        return;
    }
    int item = shop.cursor < SHOP_COUNT ? shop_stock[shop.cursor] : -1;
    if (shop.state == 1) {
        int max = ITEMS[item].price ? money / ITEMS[item].price : 0;
        if (max > 99) max = 99;
        if (max < 1) max = 1;
        int old = shop.qty;
        if (key_rep(KEY_UP)) shop.qty = shop.qty >= max ? 1 : shop.qty + 1;
        if (key_rep(KEY_DOWN)) shop.qty = shop.qty <= 1 ? max : shop.qty - 1;
        if (key_rep(KEY_RIGHT)) shop.qty = clampi(shop.qty + 10, 1, max);
        if (key_rep(KEY_LEFT)) shop.qty = clampi(shop.qty - 10, 1, max);
        if (old != shop.qty) shop_redraw();
        if (key_hit(KEY_B)) {
            shop.state = 0;
            shop_redraw();
        } else if (key_hit(KEY_A)) {
            int cost = shop.qty * ITEMS[item].price;
            shop.state = 2;
            if (cost > money) {
                sfx_play(SFX_ERROR);
                dlg_say("You don't have enough coins.");
            } else {
                char msg[64];
                money -= cost;
                bag_add(item, shop.qty);
                sfx_play(SFX_BUY);
                str_copy(msg, "Here you go! ");
                str_put_int(msg, shop.qty);
                str_put(msg, " ");
                str_put(msg, ITEMS[item].name);
                str_put(msg, ". Thank you!");
                dlg_say(msg);
            }
        }
        return;
    }
    int old = shop.cursor;
    if (key_rep(KEY_UP) && shop.cursor > 0) shop.cursor--;
    if (key_rep(KEY_DOWN) && shop.cursor < SHOP_COUNT) shop.cursor++;
    if (shop.cursor < shop.scroll) shop.scroll = shop.cursor;
    if (shop.cursor >= shop.scroll + BAG_ROWS) shop.scroll = shop.cursor - BAG_ROWS + 1;
    if (old != shop.cursor) shop_redraw();
    if (key_hit(KEY_B) || (key_hit(KEY_A) && item < 0)) {
        shop_close();
        return;
    }
    if (key_hit(KEY_A)) {
        shop.qty = 1;
        shop.state = 1;
        shop_redraw();
    }
}

/* ================================================================ */
/*  LANTERN SHELF                                                   */
/* ================================================================ */

/*
 * Page 0 is your team, pages 1..8 are the Shelf's boxes of 30. Each row
 * shows the kin's icon (OBJ banks 1-5), name, rarity gem and level; the
 * left panel shows the selected kin. A: SUMMARY / MOVE / RELEASE (asked
 * twice). MOVE picks a kin up from the team or a box and puts it down on
 * any page: that is how kin join the team or go onto the Shelf. START: SORT, BOXES BY TYPE, FIND BY TYPE;
 * while a search is on, SELECT jumps to the next kin of that type.
 */

#define SHELF_ROWS 5
#define SHELF_PAGES (1 + BOX_COUNT)
#define SHELF_ROW_Y(r) (30 + (r) * 24)

enum { SH_LIST, SH_ACTION, SH_DIALOG, SH_TOOLS, SH_SORT, SH_FIND };
enum { SHA_SUMMARY, SHA_MOVE, SHA_RELEASE, SHA_SORT_BOX, SHA_SORT_ALL,
       SHA_BY_TYPE, SHA_FIND, SHA_CANCEL };
static const char *const SORT_NAMES[SORT_COUNT] = { "NUMBER", "LEVEL", "TYPE", "RARITY", "NEWEST" };

static struct {
    int page, cursor, scroll, state, from_menu;
    int moving, move_from;          /* carrying storage[move_from] (MOVE) ... */
    int move_team;                  /* ... or party[move_from] */
    int sort_all;                   /* the SORT menu is for every box */
    int find_type, find_pick;       /* FIND BY TYPE: the type searched (-1 = none) */
    int found_n, found_k;
    u8 found[STORAGE_MAX];
    const char *acts[8];
    u8 act_id[8];
    int act_n;
    int pending;                    /* storage index a RELEASE question is about */
    s16 row_sp[SHELF_ROWS];         /* species shown on each visible row, -1 = none */
    u8 row_rarity[SHELF_ROWS];
} pc;

static int pc_box(void) { return pc.page - 1; }
static const char *pc_drop(void);

static int pc_count(void)
{
    return pc.page == 0 ? party_count : storage_box_count(pc_box());
}

/* Rows in the list: the kin, plus a "put it at the end" row while moving
 * (on the team page only when there is room, or to reorder the team). */
static int pc_rows(void)
{
    if (!pc.moving) return pc_count();
    if (pc.page == 0) return party_count + (pc.move_team || party_count < PARTY_MAX ? 1 : 0);
    return pc_count() + 1;
}

static int pc_index(int k)
{
    return storage_box_start(pc_box()) + k;
}

static Monster pc_mon(int k)
{
    if (pc.page == 0) return party[k];
    return storage_get(pc_index(k));
}

/* The kin being carried by MOVE. */
static Monster pc_carried(void)
{
    return pc.move_team ? party[pc.move_from] : storage_get(pc.move_from);
}

/* Row k of this page is the carried kin itself. */
static int pc_is_carried(int k)
{
    if (!pc.moving || k >= pc_count()) return 0;
    if (pc.page == 0) return pc.move_team && k == pc.move_from;
    return !pc.move_team && pc_index(k) == pc.move_from;
}

static void pc_clamp(void)
{
    int n = pc_rows();
    if (pc.cursor >= n) pc.cursor = n > 0 ? n - 1 : 0;
    if (pc.cursor < 0) pc.cursor = 0;
    if (pc.cursor < pc.scroll) pc.scroll = pc.cursor;
    if (pc.cursor >= pc.scroll + SHELF_ROWS) pc.scroll = pc.cursor - SHELF_ROWS + 1;
    if (pc.scroll > 0 && pc.scroll > n - SHELF_ROWS) pc.scroll = n > SHELF_ROWS ? n - SHELF_ROWS : 0;
}

static void pc_set_page(int page)
{
    pc.page = page;
    if (page > 0) opt.shelf_box = (u8)(page - 1);
}

/* Shows stored kin i (its box, selected). */
static void pc_jump_to(int i)
{
    storage_boxes_sync();
    if (i < 0 || i >= storage_count) return;
    pc_set_page(storage[i].box + 1);
    pc.cursor = i - storage_box_start(storage[i].box);
    pc_clamp();
}

static void pc_draw_left(const Monster *m, const char *label)
{
    char buf[24];
    const Species *s = &SPECIES[m->species];
    text_draw_fit(8, 96, s->name, 80);
    mon_level_text(buf, m);
    small_text_draw(8, 116, buf);
    if (m->flags & MF_LUSTROUS) text_draw_col(40, 112, "*", INK_RED, INK_RED_SH);
    if (pc.page == 0 && !label) {
        mon_hp_text(buf, m);
        small_text_draw(88 - small_text_width(buf), 116, buf);
    }
    if (label) text_draw_col(48, 112, label, INK_RED, INK_RED_SH);
    draw_type_badge(1, 16, s->type1);
    if (s->type2 != TYPE_NONE) draw_type_badge(5, 16, s->type2);
    load_monster_gfx_ex(0, m->species, 0, (m->flags & MF_LUSTROUS) != 0);
}

static void pc_redraw(void)
{
    char buf[40];
    storage_boxes_sync();
    pc_clamp();
    screen_begin(0);
    int n = pc_count(), rows = pc_rows();

    /* header: page, fill, and what START / SELECT do */
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    text_draw_col(8, 8, "<", INK_BLUE, INK_BLUE_SH);
    if (pc.page == 0) {
        str_copy(buf, "TEAM");
    } else {
        str_copy(buf, "BOX ");
        str_put_int(buf, pc.page);
    }
    int x = text_draw_col(18, 8, buf, INK_BLUE, INK_BLUE_SH);
    text_draw_col(x + 4, 8, ">", INK_BLUE, INK_BLUE_SH);
    buf[0] = 0;
    str_put_int(buf, n);
    str_put(buf, "/");
    str_put_int(buf, pc.page == 0 ? PARTY_MAX : BOX_SIZE);
    small_text_draw(x + 16, 11, buf);
    if (pc.moving) {
        text_draw_right(228, 8, "A: PUT IT HERE");
    } else if (pc.find_type >= 0) {
        str_copy(buf, "FIND ");
        str_put(buf, TYPE_NAMES[pc.find_type]);
        str_put(buf, " ");
        str_put_int(buf, pc.found_k + 1);
        str_put(buf, "/");
        str_put_int(buf, pc.found_n);
        text_draw_right(228, 8, buf);
    } else {
        text_draw_right(228, 8, "START: TOOLS");
    }

    /* left: the kin under the cursor (or the one being carried) */
    canvas_window(0, 3, 12, 17, WIN_STD);
    if (pc.moving) {
        Monster carried = pc_carried();
        pc_draw_left(&carried, 0);
    } else if (pc.cursor < n) {
        Monster m = pc_mon(pc.cursor);
        pc_draw_left(&m, 0);
    }

    /* right: the list */
    canvas_window(12, 3, 18, 17, WIN_STD);
    for (int r = 0; r < SHELF_ROWS; r++) pc.row_sp[r] = -1;
    if (!rows) text_draw(108, 34, pc.page == 0 ? "Your team is empty." : "This box is empty.");
    for (int r = 0; r < SHELF_ROWS && pc.scroll + r < rows; r++) {
        int k = pc.scroll + r, y = SHELF_ROW_Y(r);
        if (k == pc.cursor) canvas_fill(102, y - 4, 126, 22, 7);
        if (k >= n) {
            text_draw_col(142, y, "PUT AT THE END", INK_BLUE, INK_BLUE_SH);
            continue;
        }
        Monster m = pc_mon(k);
        const Species *s = &SPECIES[m.species];
        int match = pc.find_type >= 0 && (s->type1 == pc.find_type || s->type2 == pc.find_type);
        if (pc_is_carried(k))
            text_draw_col(142, y, s->name, INK_SHADOW, INK_SHADOW);
        else if (match)
            text_draw_col(142, y, s->name, INK_GREEN, INK_GREEN_SH);
        else
            text_draw_fit(142, y, s->name, 60);
        mon_level_text(buf, &m);
        small_text_draw(226 - small_text_width(buf), y + 4, buf);
        pc.row_sp[r] = (s16)m.species;
        pc.row_rarity[r] = s->rarity;
        load_monster_icon_ex(r, m.species, (m.flags & MF_LUSTROUS) != 0);
    }
    if (pc.scroll > 0) text_draw_col(216, 22, "^", INK_BLUE, INK_BLUE_SH);
    if (pc.scroll + SHELF_ROWS < rows) text_draw_col(216, 146, "}", INK_BLUE, INK_BLUE_SH);
    if (pc.moving) {
        Monster carried = pc_carried();
        load_monster_icon_ex(5, carried.species, (carried.flags & MF_LUSTROUS) != 0);
    }
    if (pc.state == SH_FIND) {
        canvas_window(8, 7, 20, 6, WIN_STD);
        text_draw(80, 66, "FIND WHICH TYPE?");
        draw_type_badge(14, 10, pc.find_pick);
        text_draw_col(96, 84, "<", INK_BLUE, INK_BLUE_SH);
        text_draw_col(152, 84, ">", INK_BLUE, INK_BLUE_SH);
    }
}

static void pc_open(int deposit)
{
    storage_boxes_sync();
    if (opt.shelf_box >= BOX_COUNT) opt.shelf_box = 0;
    pc.from_menu = 0;
    pc.page = deposit ? 0 : opt.shelf_box + 1;
    pc.cursor = pc.scroll = 0;
    pc.state = SH_LIST;
    pc.moving = 0;
    pc.find_type = -1;
    pc.find_pick = 0;
    game_mode = MODE_PC;
    gems_load();
    pc_redraw();
}

/* Back from the summary of a kin shown on the Shelf. */
static void pc_summary_back(int slot)
{
    game_mode = MODE_PC;
    pc.state = SH_LIST;
    if (sum.src == SUMSRC_SHELF) pc_set_page(sum.box + 1);
    pc.cursor = slot;
    gems_load();
    pc_redraw();
}

static void pc_say(const char *text)
{
    pc.state = SH_DIALOG;
    dlg_say(text);
}

static void pc_release_final(int c)
{
    if (c != 0 || pc.pending < 0 || pc.pending >= storage_count) return;
    char msg[96];
    Monster m = storage_take(pc.pending);
    const char *name = SPECIES[m.species].name;
    str_copy(msg, name);
    str_put(msg, " went back to its home in the wild. Farewell, ");
    str_put(msg, name);
    str_put(msg, "!");
    sfx_play(SFX_CONFIRM);
    dlg_say(msg);
    pc.find_type = -1;
}

static void pc_release_confirm(int c)
{
    if (c != 0 || pc.pending < 0 || pc.pending >= storage_count) return;
    char msg[96];
    const Species *s = &SPECIES[storage[pc.pending].species];
    str_copy(msg, "Really? ");
    str_put(msg, s->name);
    str_put(msg, s->rarity == R_LEGEND ? " is a legend. It won't come back." : " won't come back.");
    dlg_ask(msg, YES_NO, 2, pc_release_final);
}

static void pc_act(int act)
{
    int k = pc.cursor;
    char msg[80];
    switch (act) {
    case SHA_SUMMARY:
        if (pc.page == 0) summary_open(k, MODE_PC);
        else summary_open_shelf(pc_index(k));
        return;
    case SHA_MOVE:
        pc.moving = 1;
        pc.move_team = pc.page == 0;
        pc.move_from = pc.page == 0 ? k : pc_index(k);
        pc.find_type = -1;
        pc_redraw();
        return;
    case SHA_RELEASE:
        pc.pending = pc_index(k);
        str_copy(msg, "Release ");
        str_put(msg, SPECIES[storage[pc.pending].species].name);
        str_put(msg, "? It will go back to its home in the wild.");
        pc.state = SH_DIALOG;
        dlg_ask(msg, YES_NO, 2, pc_release_confirm);
        return;
    case SHA_SORT_BOX:
    case SHA_SORT_ALL:
        pc.sort_all = act == SHA_SORT_ALL;
        pc.act_n = 0;
        for (int i = 0; i < SORT_COUNT; i++) {
            pc.acts[pc.act_n] = SORT_NAMES[i];
            pc.act_id[pc.act_n++] = (u8)i;
        }
        pc.acts[pc.act_n] = "CANCEL";
        pc.act_id[pc.act_n++] = SORT_COUNT;
        pc.state = SH_SORT;
        choice_open(pc.acts, pc.act_n, CANVAS_COLS, 20);
        return;
    case SHA_BY_TYPE:
        storage_sort_type_boxes();
        pc_set_page(1);
        pc.cursor = pc.scroll = 0;
        pc.find_type = -1;
        sfx_play(SFX_CONFIRM);
        pc_say("Every kin on the Shelf now sits in a box with others of its type.");
        return;
    case SHA_FIND:
        pc.state = SH_FIND;
        pc_redraw();
        return;
    default:
        pc_redraw();
        return;
    }
}

static void pc_open_menu(int tools)
{
    pc.act_n = 0;
#define PC_ADD(name, id) do { pc.acts[pc.act_n] = name; pc.act_id[pc.act_n++] = id; } while (0)
    if (tools) {
        if (pc.page > 0) PC_ADD("SORT THIS BOX", SHA_SORT_BOX);
        PC_ADD("SORT ALL BOXES", SHA_SORT_ALL);
        PC_ADD("BOXES BY TYPE", SHA_BY_TYPE);
        PC_ADD("FIND BY TYPE", SHA_FIND);
    } else {
        PC_ADD("SUMMARY", SHA_SUMMARY);
        PC_ADD("MOVE", SHA_MOVE);
        if (pc.page > 0) PC_ADD("RELEASE", SHA_RELEASE);
    }
    PC_ADD("CANCEL", SHA_CANCEL);
#undef PC_ADD
    pc.state = tools ? SH_TOOLS : SH_ACTION;
    choice_open(pc.acts, pc.act_n, CANVAS_COLS, 20);
}

static void pc_find_next(void)
{
    if (pc.found_n <= 0) return;
    pc.found_k = (pc.found_k + 1) % pc.found_n;
    pc_jump_to(pc.found[pc.found_k]);
    sfx_play(SFX_CURSOR);
    pc_redraw();
}

static void pc_close(void)
{
    canvas_clear();
    if (pc.from_menu) {
        start_menu_open();
        return;
    }
    field_setup_bg();
    game_mode = MODE_FIELD;
}

static void pc_update(void)
{
    if (pc.state == SH_DIALOG) {
        if (!dialog_update()) {
            pc.state = SH_LIST;
            pc_redraw();
        }
        return;
    }
    if (pc.state == SH_ACTION || pc.state == SH_TOOLS || pc.state == SH_SORT) {
        int c = choice_update();
        if (c == -1) return;
        choice_close();
        int id = c >= 0 && c < pc.act_n ? pc.act_id[c] : -1;
        if (pc.state == SH_SORT) {
            pc.state = SH_LIST;
            if (id >= 0 && id < SORT_COUNT) {
                if (pc.sort_all) storage_sort_all(id);
                else storage_sort_box(pc_box(), id);
                pc.find_type = -1;
                sfx_play(SFX_CONFIRM);
            }
            pc_redraw();
            return;
        }
        pc.state = SH_LIST;
        pc_act(id < 0 ? SHA_CANCEL : id);
        return;
    }
    if (pc.state == SH_FIND) {
        int old = pc.find_pick;
        if (key_rep(KEY_LEFT) || key_rep(KEY_UP)) pc.find_pick = (pc.find_pick + TYPE_COUNT - 1) % TYPE_COUNT;
        if (key_rep(KEY_RIGHT) || key_rep(KEY_DOWN)) pc.find_pick = (pc.find_pick + 1) % TYPE_COUNT;
        if (old != pc.find_pick) {
            sfx_play(SFX_CURSOR);
            pc_redraw();
        }
        if (key_hit(KEY_B)) {
            sfx_play(SFX_CANCEL);
            pc.state = SH_LIST;
            pc_redraw();
        } else if (key_hit(KEY_A)) {
            pc.state = SH_LIST;
            pc.found_n = storage_find_type(pc.find_pick, pc.found);
            if (!pc.found_n) {
                pc.find_type = -1;
                pc_redraw();
                pc_say("No kin of that type rests on the Shelf.");
                return;
            }
            sfx_play(SFX_CONFIRM);
            pc.find_type = pc.find_pick;
            pc.found_k = 0;
            pc_jump_to(pc.found[0]);
            pc_redraw();
        }
        return;
    }

    int old_page = pc.page, old = pc.cursor, rows = pc_rows();
    if (key_rep(KEY_LEFT) || key_rep(KEY_L))
        pc_set_page(pc.page <= 0 ? SHELF_PAGES - 1 : pc.page - 1);
    if (key_rep(KEY_RIGHT) || key_rep(KEY_R))
        pc_set_page(pc.page >= SHELF_PAGES - 1 ? 0 : pc.page + 1);
    if (old_page != pc.page) {
        pc.cursor = pc.scroll = 0;
    } else if (rows) {
        if (key_rep(KEY_UP)) pc.cursor = (pc.cursor + rows - 1) % rows;
        if (key_rep(KEY_DOWN)) pc.cursor = (pc.cursor + 1) % rows;
    }
    if (old_page != pc.page || old != pc.cursor) {
        sfx_play(SFX_CURSOR);
        pc_redraw();
        return;
    }
    if (key_hit(KEY_B)) {
        sfx_play(SFX_CANCEL);
        if (pc.moving) {
            pc.moving = 0;
            pc_redraw();
        } else if (pc.find_type >= 0) {
            pc.find_type = -1;
            pc_redraw();
        } else {
            pc_close();
        }
        return;
    }
    if (key_hit(KEY_START) && !pc.moving) {
        sfx_play(SFX_CONFIRM);
        pc_open_menu(1);
        return;
    }
    if (key_hit(KEY_SELECT) && !pc.moving) {
        if (pc.find_type >= 0) pc_find_next();
        else {
            sfx_play(SFX_CONFIRM);
            pc_open_menu(1);
        }
        return;
    }
    if (!key_hit(KEY_A)) return;
    if (pc.moving) {
        const char *why = pc_drop();
        if (why) {
            sfx_play(SFX_ERROR);
            pc_say(why);
            return;
        }
        pc.moving = 0;
        sfx_play(SFX_CONFIRM);
        pc.find_type = -1;
        pc_redraw();
        return;
    }
    if (pc.cursor >= pc_count()) return;
    sfx_play(SFX_CONFIRM);
    pc_open_menu(0);
}

/* Can party[k] leave the team? Someone awake must stay behind. */
static int pc_team_can_spare(int k)
{
    for (int i = 0; i < party_count; i++)
        if (i != k && party[i].hp > 0) return 1;
    return 0;
}

/* Puts the carried kin down in front of the row under the cursor (the last
 * row: at the end). Team to box sends it onto the Shelf, box to team brings
 * it along (onto a full team: the two swap places). Returns why it can't
 * go there, or 0 when it went; the cursor ends on it. */
static const char *pc_drop(void)
{
    int k = pc.cursor, from = pc.move_from;
    if (pc.page > 0) {
        int b = pc_box();
        if (!pc.move_team) {
            int same = storage[from].box == b;
            int within = from - storage_box_start(b);
            if (!storage_move(from, b, k)) return "That box is full.";
            if (same && within < k) k--;
        } else {
            if (!pc_team_can_spare(from)) return "You can't send away your last kin that's awake!";
            if (storage_count >= STORAGE_MAX || storage_box_count(b) >= BOX_SIZE) return "That box is full.";
            Monster m = party[from];
            for (int i = from; i < party_count - 1; i++) party[i] = party[i + 1];
            party_count--;
            BoxMon bm = box_pack(&m);
            bm.order = storage_next_order();
            k = clampi(k, 0, storage_box_count(b));
            storage_insert(storage_box_start(b) + k, bm, b);
        }
        pc.cursor = clampi(k, 0, pc_count() - 1);
        return 0;
    }
    if (pc.move_team) {
        Monster m = party[from];
        if (k > from) k--;
        for (int i = from; i < party_count - 1; i++) party[i] = party[i + 1];
        k = clampi(k, 0, party_count - 1);
        for (int i = party_count - 1; i > k; i--) party[i] = party[i - 1];
        party[k] = m;
    } else if (party_count < PARTY_MAX) {
        Monster m = storage_take(from);
        k = clampi(k, 0, party_count);
        for (int i = party_count; i > k; i--) party[i] = party[i - 1];
        party[k] = m;
        party_count++;
    } else {
        if (k >= party_count) return "Your team is full!";
        if (party[k].hp > 0 && !pc_team_can_spare(k) && storage_get(from).hp == 0)
            return "You can't send away your last kin that's awake!";
        /* a full team: the two trade places */
        u16 order = storage_next_order();
        BoxMon bm = box_pack(&party[k]);
        bm.order = order;
        bm.box = storage[from].box;
        party[k] = box_unpack(&storage[from]);
        storage[from] = bm;
    }
    pc.cursor = k;
    return 0;
}

static void pc_draw(void)
{
    int n = pc_count();
    if (pc.moving || pc.cursor < n) spr_push(16, 28, OT_MON_A, SQ64, OBANK_MON_A, 0, 0);
    if (pc.state != SH_LIST) return;   /* menus and messages sit over the list */
    for (int r = 0; r < SHELF_ROWS; r++) {
        if (pc.row_sp[r] < 0) continue;
        int y = SHELF_ROW_Y(r);
        int bob = menu_bob(pc.scroll + r == pc.cursor && pc.state == SH_LIST);
        spr_push(100, y - 10 + bob, OT_ICON(r), SQ32, OBANK_NPC + r, 0, 0);
        gem_push(131, y + 3, pc.row_rarity[r]);
    }
    if (pc.moving) {
        int r = pc.cursor - pc.scroll;
        spr_push(70, SHELF_ROW_Y(r) - 12 + menu_bob(1), OT_ICON(5), SQ32, OBANK_NPC + 5, 0, 0);
    }
}

/* LANTERN SHELF through the TWIN CRYSTAL (from the START menu). */
static void pc_open_from_menu(void)
{
    pc_open(0);
    pc.from_menu = 1;
}
