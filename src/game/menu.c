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

enum { SM_ALMANAC, SM_LORE, SM_KIN, SM_BAG, SM_MAP, SM_FIELD, SM_SHELF, SM_CARD, SM_OPTIONS, SM_SAVE, SM_EXIT };
static const char *const START_NAMES[] = {
    "ALMANAC", "LOREBOOK", "KIN", "BAG", "MAP", "FIELD", "SHELF", "CARD", "OPTIONS", "SAVE", "EXIT",
};
static u8 start_items[11];
static int start_count, start_cursor, start_card;

static void start_menu_build(void)
{
    start_count = 0;
    for (int i = SM_ALMANAC; i <= SM_EXIT; i++) {
        if (i == SM_SHELF && !(flag(FLAG_TWIN_CRYSTAL))) continue;
        if (i == SM_KIN && !party_count) continue;
        if (i == SM_MAP && bag[ITEM_TOWN_MAP] <= 0) continue;                        /* travel.c */
        if (i == SM_FIELD && !(party_count && (travel.crests || bag[ITEM_BIKE] > 0))) continue;
        if (i == SM_EXIT && start_count > 9) continue;   /* B closes the menu too */
        start_items[start_count++] = (u8)i;
    }
    if (start_cursor >= start_count) start_cursor = 0;
}

static int start_pitch(void) { return start_count > 9 ? 14 : LINE_H; }

static void start_menu_draw(void)
{
    start_menu_build();
    canvas_window(20, 0, 10, (start_count * start_pitch() + 16 + 7) / 8, WIN_STD);
    for (int i = 0; i < start_count; i++) {
        int y = 8 + i * start_pitch();
        text_draw(172, y, START_NAMES[start_items[i]]);
        if (start_items[i] == SM_LORE && lore_unread_count())
            text_draw_col(224, y, "*", INK_RED, INK_RED_SH);
        if (i == start_cursor) text_draw(163, y, "{");
    }
}

static void start_menu_open(void)
{
    field_setup_bg(); /* the almanac and lorebook borrow BG2 and WIN0 */
    game_mode = MODE_START_MENU;
    start_card = 0;
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

static void start_card_draw(void)
{
    char buf[40];
    canvas_window(1, 1, 18, 17, WIN_STD);
    text_draw_col(16, 16, "WARDEN CARD", INK_BLUE, INK_BLUE_SH);
    if (flag(FLAG_SASH)) text_draw_col(104, 16, "RING SASH", INK_RED, INK_RED_SH);
    static const char *const LABEL[6] = { "COINS", "BEFRIENDED", "MET", "LORE PAGES", "WARDENS", "SHELF" };
    for (int i = 0; i < 6; i++) {
        int y = 36 + i * LINE_H;
        text_draw(16, y, LABEL[i]);
        buf[0] = 0;
        switch (i) {
        case 0: money_text(buf, money); break;
        case 1: str_put_int(buf, dex_caught_count()); str_put(buf, "/"); str_put_int(buf, SP_COUNT); break;
        case 2: str_put_int(buf, dex_seen_count()); break;
        case 3: str_put_int(buf, lore_known_count()); str_put(buf, "/"); str_put_int(buf, LORE_COUNT); break;
        case 4: str_put_int(buf, trainers_beaten_count()); str_put(buf, "/"); str_put_int(buf, TRAINER_COUNT); break;
        default: str_put_int(buf, storage_count); break;
        }
        text_draw_right(136, y, buf);
    }
}

static void options_open(void);
static void pc_open_from_menu(void);

static void start_menu_update(void)
{
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
        start_menu_draw();
    }
    if (!key_hit(KEY_A)) return;
    sfx_play(SFX_CONFIRM);
    switch (start_items[start_cursor]) {
    case SM_ALMANAC: dex_open(); break;
    case SM_LORE: lorebook_open(); break;
    case SM_KIN: party_screen_open(PCTX_FIELD, 0); break;
    case SM_BAG: bag_screen_open(BAGCTX_FIELD); break;
    case SM_MAP:
        start_menu_close();
        worldmap_open(0);
        break;
    case SM_FIELD:
        start_menu_close();
        travel_field_menu_open();
        break;
    case SM_SHELF: pc_open_from_menu(); break;
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

static int opt_cursor;
#define OPT_ROWS 5

static void options_redraw(void)
{
    static const char *const LABEL[OPT_ROWS] = { "TEXT SPEED", "BOUT ANIMATIONS", "SOUND", "KIN FOLLOWS YOU", "AUTOSAVE" };
    static const char *const SPEED[TEXT_SPEED_COUNT] = { "SLOW", "MID", "FAST", "INSTANT" };
    screen_begin(0);
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    text_draw_col(16, 8, "OPTIONS", INK_BLUE, INK_BLUE_SH);
    canvas_window(0, 3, CANVAS_COLS, 12, WIN_STD);
    for (int i = 0; i < OPT_ROWS; i++) {
        int y = 32 + i * 18;
        if (i == opt_cursor) {
            canvas_fill(12, y - 3, 216, 16, 7);
            text_draw(13, y - 2, "{");
        }
        text_draw(24, y - 2, LABEL[i]);
        const char *v;
        switch (i) {
        case 0: v = SPEED[opt.text_speed % TEXT_SPEED_COUNT]; break;
        case 1: v = opt.battle_anims ? "ON" : "OFF"; break;
        case 2: v = opt.sound ? "ON" : "OFF"; break;
        case 3: v = opt.follower ? "ON" : "OFF"; break;
        default: v = opt.autosave ? "ON" : "OFF"; break;
        }
        text_draw_col(160, y - 2, "<", INK_BLUE, INK_BLUE_SH);
        text_draw_center(194, y - 2, v);
        text_draw_col(222, y - 2, ">", INK_BLUE, INK_BLUE_SH);
    }
    canvas_window(0, 15, CANVAS_COLS, 5, WIN_STD);
    static const char *const HELP[OPT_ROWS] = {
        "How fast text appears.\nHold A or B to hurry it along.",
        "OFF plays quick hits instead of\nthe full move animations.",
        "Sound effects for menus, the\nfield and bouts.",
        "Your lead kin walks behind you\nin the field.",
        "Save automatically whenever you\nenter a HEARTH HALL.",
    };
    text_draw(16, 124, HELP[opt_cursor]);
}

static void options_open(void)
{
    game_mode = MODE_OPTIONS;
    opt_cursor = 0;
    options_redraw();
}

static void options_update(void)
{
    int old = opt_cursor, change = 0;
    if (key_rep(KEY_UP)) opt_cursor = (opt_cursor + OPT_ROWS - 1) % OPT_ROWS;
    if (key_rep(KEY_DOWN)) opt_cursor = (opt_cursor + 1) % OPT_ROWS;
    if (key_rep(KEY_LEFT)) change = -1;
    if (key_rep(KEY_RIGHT) || key_hit(KEY_A)) change = 1;
    if (change) {
        switch (opt_cursor) {
        case 0: opt.text_speed = (u8)((opt.text_speed + TEXT_SPEED_COUNT + change) % TEXT_SPEED_COUNT); break;
        case 1: opt.battle_anims ^= 1; break;
        case 2: opt.sound ^= 1; break;
        case 3: opt.follower ^= 1; break;
        default: opt.autosave ^= 1; break;
        }
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

static struct { int slot, page, move_cursor, return_mode; } sum;

static void summary_redraw(void)
{
    const Monster *m = &party[sum.slot];
    const Species *s = &SPECIES[m->species];
    char buf[48];
    screen_begin(0);
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    text_draw_col(16, 8, SUM_TITLES[sum.page], INK_BLUE, INK_BLUE_SH);
    for (int p = 0; p < SUM_PAGES; p++)
        canvas_fill(186 + p * 10, 12, 6, 6, p == sum.page ? 10 : 4);
    text_draw(172, 8, "<");
    text_draw(226, 8, ">");

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
        text_draw(x, y, "STATUS");
        text_draw_right(232, y, m->hp == 0 ? "DOZING" : m->status ? STATUS_NAMES[m->status] : "OK");
        y += LINE_H;
        const Species *evo = s->evo_kind != EVO_NONE ? &SPECIES[s->evo_into] : 0;
        if (evo) {
            str_copy(buf, "Grows ");
            if (s->evo_kind == EVO_LEVEL) {
                str_put(buf, "at Lv");
                str_put_int(buf, s->evo_param);
            } else {
                str_put(buf, "by ");
                str_put(buf, ITEMS[s->evo_param].name);
            }
            text_draw_col(x, y, buf, INK_GREEN, INK_GREEN_SH);
        } else {
            text_draw_col(x, y, "Fully grown", INK_GREEN, INK_GREEN_SH);
        }
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
    sum.slot = slot;
    sum.return_mode = return_mode;
    sum.move_cursor = 0;
    game_mode = MODE_SUMMARY;
    summary_redraw();
}

static void summary_update(void)
{
    int redraw = 0;
    if (key_hit(KEY_B)) {
        if (sum.return_mode == MODE_PARTY) {
            game_mode = MODE_PARTY;
            pscr.cursor = sum.slot;
            party_redraw();
        }
        return;
    }
    if (key_hit(KEY_LEFT)) { sum.page = (sum.page + SUM_PAGES - 1) % SUM_PAGES; redraw = 1; }
    if (key_hit(KEY_RIGHT)) { sum.page = (sum.page + 1) % SUM_PAGES; redraw = 1; }
    if (sum.page == SUM_MOVES) {
        int n = monster_move_count(&party[sum.slot]);
        if (key_rep(KEY_UP) && sum.move_cursor > 0) { sum.move_cursor--; redraw = 1; }
        if (key_rep(KEY_DOWN) && sum.move_cursor < n - 1) { sum.move_cursor++; redraw = 1; }
        if (key_hit(KEY_L) && sum.slot > 0) { sum.slot--; sum.move_cursor = 0; redraw = 1; }
        if (key_hit(KEY_R) && sum.slot < party_count - 1) { sum.slot++; sum.move_cursor = 0; redraw = 1; }
    } else {
        if (key_rep(KEY_UP) && sum.slot > 0) { sum.slot--; redraw = 1; }
        if (key_rep(KEY_DOWN) && sum.slot < party_count - 1) { sum.slot++; redraw = 1; }
    }
    if (redraw) summary_redraw();
}

static void summary_draw(void)
{
    spr_push(8, 32, OT_MON_A, SQ64, OBANK_MON_A, 0, 0);
}

/* ================================================================ */
/*  Bag                                                             */
/* ================================================================ */

static struct {
    int ctx, pocket, cursor, scroll;
    int list[ITEM_COUNT + 1], count; /* item ids; -1 = close */
    int state; /* 0 list, 1 action menu, 2 dialog */
    const char *actions[3];
    int action_count;
} bscr;

#define BAG_ROWS 6

static void bag_build_list(void)
{
    bscr.count = 0;
    for (int i = 0; i < ITEM_COUNT; i++)
        if (ITEMS[i].pocket == bscr.pocket && bag[i] > 0) bscr.list[bscr.count++] = i;
    bscr.list[bscr.count++] = -1;
    if (bscr.cursor >= bscr.count) bscr.cursor = bscr.count - 1;
    if (bscr.scroll > bscr.cursor) bscr.scroll = bscr.cursor;
    if (bscr.cursor >= bscr.scroll + BAG_ROWS) bscr.scroll = bscr.cursor - BAG_ROWS + 1;
}

static void bag_redraw(void)
{
    char buf[40];
    screen_begin(0);
    bag_build_list();
    canvas_window(0, 0, 11, 14, WIN_STD);
    text_draw(8, 8, "<");
    text_draw_center(44, 8, POCKET_NAMES[bscr.pocket]);
    text_draw(74, 8, ">");
    for (int p = 0; p < POCKET_COUNT; p++)
        canvas_fill(28 + p * 12, 28, 8, 4, p == bscr.pocket ? 10 : 4);
    text_draw(12, 48, "COINS");
    money_text(buf, money);
    text_draw_right(80, 64, buf);
    text_draw_col(12, 88, bscr.ctx == BAGCTX_BATTLE ? "BOUT" : "FIELD", INK_BLUE, INK_BLUE_SH);

    canvas_window(11, 0, 19, 14, WIN_STD);
    for (int r = 0; r < BAG_ROWS && bscr.scroll + r < bscr.count; r++) {
        int idx = bscr.scroll + r, y = 8 + r * LINE_H;
        int item = bscr.list[idx];
        if (idx == bscr.cursor) text_draw(94, y, "{");
        if (item < 0) {
            text_draw(104, y, "CLOSE BAG");
            continue;
        }
        text_draw(104, y, ITEMS[item].name);
        str_copy(buf, "|");
        str_put_int(buf, bag[item]);
        text_draw_right(228, y, buf);
    }
    if (bscr.scroll > 0) text_draw_col(214, 0, "^", INK_BLUE, INK_BLUE_SH);
    if (bscr.scroll + BAG_ROWS < bscr.count) text_draw_col(214, 98, "}", INK_BLUE, INK_BLUE_SH);

    canvas_window(0, 14, CANVAS_COLS, 6, WIN_STD);
    int item = bscr.list[bscr.cursor];
    if (item >= 0) {
        char wrapped[160];
        draw_item_icon(1, 15, item);
        text_wrap(wrapped, ITEMS[item].desc, 184);
        text_draw(40, 120, wrapped);
    } else {
        text_draw(16, 120, "Close the bag and go back.");
    }
}

static void bag_screen_open(int ctx)
{
    bscr.ctx = ctx;
    bscr.state = 0;
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

static int item_battle_usable(int item)
{
    int k = ITEMS[item].kind;
    return k == IK_HEAL || k == IK_FULL_HEAL || k == IK_WAKE || k == IK_TEA ||
           k == IK_XSTAT || k == IK_LANTERN;
}

static int bag_hush(int item)
{
    bscr.state = 2;
    return item_use_field(item, 0);
}

static void bag_use(int item)
{
    int k = ITEMS[item].kind;
    if (bscr.ctx == BAGCTX_BATTLE) {
        if (!item_battle_usable(item)) {
            bscr.state = 2;
            dlg_say("You can't use that here.");
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
    if (k == IK_HUSH || k == IK_KEY) {   /* key items need no kin (travel.c, farm.c...) */
        bag_hush(item);
        return;
    }
    if (k == IK_LANTERN || k == IK_XSTAT) {
        bscr.state = 2;
        dlg_say(k == IK_LANTERN ? "Offer lanterns to tired wild kin during a bout!"
                                : "That clips on during a bout.");
        return;
    }
    if (!party_count) {
        bscr.state = 2;
        dlg_say("You don't have any kin yet.");
        return;
    }
    party_screen_open(PCTX_ITEM_FIELD, item);
}

static void bag_screen_update(void)
{
    if (bscr.state == 2) {
        if (!dialog_update()) {
            bscr.state = 0;
            bag_redraw();
        }
        return;
    }
    if (bscr.state == 1) {
        int c = choice_update();
        if (c == -1) return;
        choice_close();
        bscr.state = 0;
        if (c == 0) bag_use(bscr.list[bscr.cursor]);
        else bag_redraw();
        return;
    }
    int redraw = 0;
    if (key_hit(KEY_LEFT)) { bscr.pocket = (bscr.pocket + POCKET_COUNT - 1) % POCKET_COUNT; bscr.cursor = bscr.scroll = 0; redraw = 1; }
    if (key_hit(KEY_RIGHT)) { bscr.pocket = (bscr.pocket + 1) % POCKET_COUNT; bscr.cursor = bscr.scroll = 0; redraw = 1; }
    if (key_rep(KEY_UP) && bscr.cursor > 0) { bscr.cursor--; redraw = 1; }
    if (key_rep(KEY_DOWN) && bscr.cursor < bscr.count - 1) { bscr.cursor++; redraw = 1; }
    if (redraw) bag_redraw();
    if (key_hit(KEY_B)) {
        bag_close();
        return;
    }
    if (key_hit(KEY_A)) {
        int item = bscr.list[bscr.cursor];
        if (item < 0) {
            bag_close();
            return;
        }
        bscr.actions[0] = "USE";
        bscr.actions[1] = "CANCEL";
        bscr.state = 1;
        choice_open(bscr.actions, 2, CANVAS_COLS, 14);
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
/*  PC storage                                                      */
/* ================================================================ */

static struct { int deposit, cursor, scroll, state, from_menu; } pc;

static int pc_count(void)
{
    return pc.deposit ? party_count : storage_count;
}

static const Monster *pc_mon(int i)
{
    static Monster view;
    if (pc.deposit) return &party[i];
    view = storage_get(i);
    return &view;
}

static void pc_redraw(void)
{
    char buf[32];
    screen_begin(0);
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    text_draw_col(16, 8, pc.deposit ? "LANTERN SHELF: DEPOSIT" : "LANTERN SHELF: WITHDRAW",
                  INK_BLUE, INK_BLUE_SH);
    small_text_draw(170, 11, "SELECT: SWAP");
    canvas_window(0, 3, 12, 12, WIN_STD);
    canvas_window(12, 3, 18, 17, WIN_STD);
    int n = pc_count();
    if (!n) text_draw(112, 32, pc.deposit ? "Your team is empty." : "The shelf is empty.");
    for (int r = 0; r < 7 && pc.scroll + r < n; r++) {
        int idx = pc.scroll + r, y = 32 + r * LINE_H;
        const Monster *m = pc_mon(idx);
        if (idx == pc.cursor) text_draw(104, y, "{");
        text_draw(114, y, SPECIES[m->species].name);
        mon_level_text(buf, m);
        small_text_draw(228 - small_text_width(buf), y + 4, buf);
    }
    canvas_window(0, 15, 12, 5, WIN_STD);
    str_copy(buf, "STORED ");
    str_put_int(buf, storage_count);
    str_put(buf, "/");
    str_put_int(buf, STORAGE_MAX);
    text_draw(12, 128, buf);
    if (n) load_monster_gfx(0, pc_mon(pc.cursor)->species, 0);
}

static void pc_open(int deposit)
{
    pc.from_menu = 0;
    pc.deposit = deposit;
    pc.cursor = pc.scroll = 0;
    pc.state = 0;
    game_mode = MODE_PC;
    pc_redraw();
}

static void pc_update(void)
{
    if (pc.state == 2) {
        if (!dialog_update()) {
            pc.state = 0;
            if (pc.cursor >= pc_count() && pc.cursor > 0) pc.cursor--;
            pc_redraw();
        }
        return;
    }
    int n = pc_count(), old = pc.cursor;
    if (key_rep(KEY_UP) && pc.cursor > 0) pc.cursor--;
    if (key_rep(KEY_DOWN) && pc.cursor < n - 1) pc.cursor++;
    if (pc.cursor < pc.scroll) pc.scroll = pc.cursor;
    if (pc.cursor >= pc.scroll + 7) pc.scroll = pc.cursor - 6;
    if (old != pc.cursor) pc_redraw();
    if (key_hit(KEY_SELECT)) {
        sfx_play(SFX_CURSOR);
        pc.deposit ^= 1;
        pc.cursor = pc.scroll = 0;
        pc_redraw();
        return;
    }
    if (key_hit(KEY_B)) {
        sfx_play(SFX_CANCEL);
        canvas_clear();
        if (pc.from_menu) {
            start_menu_open();
            return;
        }
        field_setup_bg();
        game_mode = MODE_FIELD;
        return;
    }
    if (!key_hit(KEY_A) || !n) return;
    pc.state = 2;
    char msg[64];
    if (pc.deposit) {
        int healthy_others = 0;
        for (int i = 0; i < party_count; i++)
            if (i != pc.cursor && party[i].hp > 0) healthy_others++;
        if (party_count <= 1 || !healthy_others) {
            dlg_say("You can't send away your last kin that's awake!");
        } else if (storage_count >= STORAGE_MAX) {
            dlg_say("The LANTERN SHELF is full.");
        } else {
            storage_add(&party[pc.cursor]);
            str_copy(msg, SPECIES[party[pc.cursor].species].name);
            str_put(msg, " went across the wire to the LANTERN SHELF.");
            for (int i = pc.cursor; i < party_count - 1; i++) party[i] = party[i + 1];
            party_count--;
            dlg_say(msg);
        }
    } else {
        if (party_count >= PARTY_MAX) {
            dlg_say("Your team is full!");
        } else {
            party[party_count++] = storage_take(pc.cursor);
            str_copy(msg, SPECIES[party[party_count - 1].species].name);
            str_put(msg, " joined your team!");
            dlg_say(msg);
        }
    }
}

static void pc_draw(void)
{
    if (pc_count()) spr_push(16, 36, OT_MON_A, SQ64, OBANK_MON_A, 0, 0);
}

/* LANTERN SHELF through the TWIN CRYSTAL (from the START menu). */
static void pc_open_from_menu(void)
{
    pc_open(0);
    pc.from_menu = 1;
}
