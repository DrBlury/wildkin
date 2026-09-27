/*
 * The ADMIN menu: a cheat screen for testing and for players who want to
 * shape their own game. It is reached from the START menu once ADMIN MODE
 * is switched on (title screen: SELECT+START opens the debug menu, the
 * ADMIN MODE row toggles opt.admin, which the save keeps).
 *
 *   ADD 10000 COINS  up to the purse's cap (MONEY_CAP)
 *   GIVE ITEM        any item of any pocket, 1-99 at a time (key items: 1)
 *   ADD KIN          any species, level 1-100, lustrous or not, a nickname
 *                    (the name slate) and any four moves of the whole move
 *                    list; to the Shelf (default) or the team
 *   TEACH A MOVE     put any move in any slot of a team kin (or clear it)
 *   HEAL TEAM        full HP and uses, no status
 *
 * Every list is one picker (adm_pick_*): UP/DOWN step, L/R a page,
 * LEFT/RIGHT the previous / next group (pocket, type, ten species, first
 * letter), SELECT the order, A picks, B goes back.
 *
 * Runs as an ext screen (menu.c ext_open); B on the main list goes back to
 * the START menu.
 */

#define MONEY_CAP 9999999   /* the save refuses more (save_game.h) */
#define ADMIN_COINS 10000
#define ADM_ROWS 6          /* picker rows on screen */
#define ADM_LIST_MAX 256
#define ADM_ORDER_RIGHT 188 /* the order label ends here; the count sits right of it */

enum { AD_MAIN, AD_PICK, AD_QTY, AD_FORM, AD_DIALOG };
enum { AM_COINS, AM_ITEM, AM_KIN, AM_TEACH, AM_HEAL, AM_BACK, AM_COUNT };
/* what a picker is choosing */
enum { PF_ITEM, PF_SPECIES, PF_FORM_MOVE, PF_TEACH_KIN, PF_TEACH_SLOT, PF_TEACH_MOVE, PF_COUNT };
/* the ADD KIN form's rows */
enum { AF_KIN, AF_LEVEL, AF_LUSTROUS, AF_NAME, AF_MOVE1, AF_MOVE4 = AF_MOVE1 + 3, AF_DEST, AF_ADD, AF_COUNT };

static const char *const ADM_MAIN[AM_COUNT] = {
    "ADD 10000 COINS", "GIVE ITEM", "ADD KIN", "TEACH A MOVE", "HEAL TEAM", "BACK",
};
static const char *const ADM_MAIN_HELP[AM_COUNT] = {
    "Adds 10000c to your purse\n(it holds up to 9999999c).",
    "Any item from any pocket,\n1 to 99 at a time, into the bag.",
    "Any kin at any level, with any\nfour moves. It goes to the Shelf.",
    "Put any move in any slot of a\nkin on your team.",
    "Full HP and uses and no status\nfor the whole team.",
    "Back to the START menu.",
};
static const char *const ADM_TITLES[PF_COUNT] = {
    "GIVE ITEM", "CHOOSE A KIN", "CHOOSE A MOVE", "TEACH: WHO?", "TEACH: SLOT", "TEACH: MOVE",
};
/* SELECT orders: 0 = by pocket / number / type, 1 = A to Z */
static const char *const ADM_ORDER[PF_COUNT][2] = {
    { "BY POCKET", "A TO Z" }, { "BY NUMBER", "A TO Z" }, { "BY TYPE", "A TO Z" },
    { 0, 0 }, { 0, 0 }, { "BY TYPE", "A TO Z" },
};

static struct {
    int state, main_cursor;
    /* picker */
    int pf, count, cursor, scroll;
    u8 order[PF_COUNT];
    u16 ids[ADM_LIST_MAX];
    int qty;
    /* ADD KIN form */
    int row, sp, level, lustrous, to_team, custom;
    Monster draft;          /* species, level, flags, moves and nickname of the kin to add */
    int slot;               /* the move slot being chosen (form or TEACH) */
    int teach;              /* the team kin being taught */
    char msg[96];           /* a result line (green) until the cursor moves */
    int return_state;       /* where AD_DIALOG goes back to */
} adm;

static void admin_update(void);
static void admin_draw(void);
static void adm_redraw(void);

/* ---------------- the kin being made ---------------- */

/* The moves a wild kin of this species and level knows (monster_make). */
static void adm_natural_moves(void)
{
    Monster m = monster_make(adm.sp, adm.level);
    for (int i = 0; i < MAX_MOVES; i++) {
        adm.draft.moves[i] = m.moves[i];
        adm.draft.pp[i] = m.pp[i];
    }
    adm.custom = 0;
}

static void adm_draft_sync(void)
{
    adm.draft.species = (u8)adm.sp;
    adm.draft.level = (u8)adm.level;
    adm.draft.flags = adm.lustrous ? MF_LUSTROUS : 0;
    if (!adm.custom) adm_natural_moves();
    load_monster_gfx_ex(0, adm.sp, 0, adm.lustrous);
}

static void adm_set_species(int sp)
{
    adm.sp = ((sp % SP_COUNT) + SP_COUNT) % SP_COUNT;
    adm.custom = 0;          /* a new kin starts from its own moves */
    adm_draft_sync();
}

/* Moves first, empty slots last (the bout menus expect that). */
static void moves_compact(u8 *moves, u8 *pp)
{
    int n = 0;
    for (int i = 0; i < MAX_MOVES; i++)
        if (moves[i] != MOVE_NONE) {
            moves[n] = moves[i];
            pp[n] = pp[i];
            n++;
        }
    for (; n < MAX_MOVES; n++) {
        moves[n] = MOVE_NONE;
        pp[n] = 0;
    }
}

/* 1 if `move` is already in a slot other than `slot`. */
static int moves_has_other(const u8 *moves, int slot, int move)
{
    for (int i = 0; i < MAX_MOVES; i++)
        if (i != slot && moves[i] == move) return 1;
    return 0;
}

static int moves_count(const u8 *moves)
{
    int n = 0;
    for (int i = 0; i < MAX_MOVES; i++) n += moves[i] != MOVE_NONE;
    return n;
}

/*
 * The finished kin: a fresh monster_make (stats, XP for its level, rolled
 * potential, temperament, trait and size), then the form's lustre, moves
 * (full uses) and nickname. Met here, at this level.
 */
static Monster admin_build_kin(int sp, int level, int lustrous, const u8 *moves, const char *name)
{
    Monster m = monster_make(sp, level);
    m.flags = lustrous ? MF_LUSTROUS : 0;
    for (int i = 0; i < MAX_MOVES; i++) {
        int mv = moves[i];
        m.moves[i] = mv < MOVE_COUNT ? (u8)mv : MOVE_NONE;
        m.pp[i] = mv < MOVE_COUNT ? MOVES[mv].pp : 0;
    }
    moves_compact(m.moves, m.pp);
    kin_set_name(&m, name);
    m.met_map = cur_map >= 0 && cur_map < MAP_COUNT ? (u8)cur_map : MET_NOWHERE;
    m.met_level = m.level;
    monster_heal_full(&m);
    return m;
}

/*
 * Gives the kin to the player: to the Shelf (the box last viewed, or the
 * next with room) unless `to_team`; whichever is full, the other one.
 * The Almanac marks it met and befriended. Returns 0 team, 1 Shelf,
 * -1 no room; *where is the team slot or the Shelf box.
 */
static int admin_give_kin(const Monster *m, int to_team, int *where)
{
    int r = -1;
    if (to_team && party_count < PARTY_MAX) {
        *where = party_count;
        party[party_count++] = *m;
        r = 0;
    } else {
        int b = storage_add_box(m, opt.shelf_box);
        if (b >= 0) {
            *where = b;
            r = 1;
        } else if (party_count < PARTY_MAX) {
            *where = party_count;
            party[party_count++] = *m;
            r = 0;
        }
    }
    if (r >= 0) {
        dex_seen[m->species] = 1;
        dex_caught[m->species] = 1;
    }
    return r;
}

/* ---------------- actions ---------------- */

static void admin_add_coins(void)
{
    int before = money;
    money = clampi(money + ADMIN_COINS, 0, MONEY_CAP);
    char buf[24];
    if (money == before) {
        str_copy(adm.msg, "The purse is full: ");
    } else {
        str_copy(adm.msg, "+");
        str_put_int(adm.msg, money - before);
        str_put(adm.msg, "c. You have ");
    }
    money_text(buf, money);
    str_put(adm.msg, buf);
    str_put(adm.msg, ".");
}

static void admin_heal(void)
{
    party_heal_all();
    str_copy(adm.msg, party_count ? "Your team is fully healed." : "You have no kin on your team.");
}

static int adm_qty_max(int item)
{
    return ITEMS[item].pocket == POCKET_KEY ? 1 : 99;
}

static void admin_give_item(int item, int qty)
{
    int before = bag[item];
    bag_add(item, qty);
    str_copy(adm.msg, "+");
    str_put_int(adm.msg, bag[item] - before);
    str_put(adm.msg, " ");
    str_put(adm.msg, ITEMS[item].name);
    str_put(adm.msg, ". Now ");
    str_put_int(adm.msg, bag[item]);
    str_put(adm.msg, ".");
}

/* ---------------- the picker ---------------- */

static const char *adm_label(int pf, int id)
{
    switch (pf) {
    case PF_ITEM: return ITEMS[id].name;
    case PF_SPECIES: return SPECIES[id].name;
    case PF_TEACH_KIN: return kin_name(&party[id]);
    default: return id < MOVE_COUNT ? MOVES[id].name : "";
    }
}

/* Sort key group (order 0): pocket, tens of species, move type. */
static int adm_group(int pf, int id)
{
    if (adm.order[pf]) {
        const char *s = adm_label(pf, id);
        return s[0];
    }
    switch (pf) {
    case PF_ITEM: return ITEMS[id].pocket;
    case PF_SPECIES: return id / 10;
    case PF_FORM_MOVE:
    case PF_TEACH_MOVE: return id < MOVE_COUNT ? MOVES[id].type : -1;
    default: return id;
    }
}

static int adm_before(int pf, int a, int b)
{
    if ((pf == PF_FORM_MOVE || pf == PF_TEACH_MOVE) && (a == MOVE_NONE || b == MOVE_NONE))
        return a == MOVE_NONE && b != MOVE_NONE;   /* NO MOVE first */
    if (adm.order[pf]) {
        const char *x = adm_label(pf, a), *y = adm_label(pf, b);
        while (*x && *x == *y) {
            x++;
            y++;
        }
        if (*x != *y) return (u8)*x < (u8)*y;
        return a < b;
    }
    int ga = adm_group(pf, a), gb = adm_group(pf, b);
    if (ga != gb) return ga < gb;
    return a < b;
}

static void adm_pick_build(void)
{
    int pf = adm.pf, n = 0;
    switch (pf) {
    case PF_ITEM:
        for (int i = 0; i < ITEM_COUNT; i++) adm.ids[n++] = (u16)i;
        break;
    case PF_SPECIES:
        for (int i = 0; i < SP_COUNT; i++) adm.ids[n++] = (u16)i;
        break;
    case PF_FORM_MOVE:
    case PF_TEACH_MOVE:
        adm.ids[n++] = MOVE_NONE;
        for (int i = 0; i < MOVE_COUNT && n < ADM_LIST_MAX; i++) adm.ids[n++] = (u16)i;
        break;
    case PF_TEACH_KIN:
        for (int i = 0; i < party_count; i++) adm.ids[n++] = (u16)i;
        break;
    case PF_TEACH_SLOT:
        for (int i = 0; i < MAX_MOVES; i++) adm.ids[n++] = (u16)i;
        break;
    }
    /* insertion sort (a few hundred names, only when the order changes) */
    if (pf == PF_ITEM || pf == PF_SPECIES || pf == PF_FORM_MOVE || pf == PF_TEACH_MOVE)
        for (int i = 1; i < n; i++) {
            u16 v = adm.ids[i];
            int j = i - 1;
            while (j >= 0 && adm_before(pf, v, adm.ids[j])) {
                adm.ids[j + 1] = adm.ids[j];
                j--;
            }
            adm.ids[j + 1] = v;
        }
    adm.count = n;
}

static void adm_pick_scroll(void)
{
    adm.cursor = clampi(adm.cursor, 0, adm.count > 0 ? adm.count - 1 : 0);
    if (adm.cursor < adm.scroll) adm.scroll = adm.cursor;
    if (adm.cursor >= adm.scroll + ADM_ROWS) adm.scroll = adm.cursor - ADM_ROWS + 1;
    adm.scroll = clampi(adm.scroll, 0, adm.count > ADM_ROWS ? adm.count - ADM_ROWS : 0);
}

/* Put the cursor on `id` (if it is in the list). */
static void adm_pick_goto(int id)
{
    for (int i = 0; i < adm.count; i++)
        if (adm.ids[i] == id) adm.cursor = i;
    adm_pick_scroll();
}

static void adm_pick_open(int pf, int select_id)
{
    adm.pf = pf;
    adm.state = AD_PICK;
    adm.cursor = adm.scroll = 0;
    adm.msg[0] = 0;
    adm_pick_build();
    if (select_id >= 0) adm_pick_goto(select_id);
    adm_pick_scroll();
    adm_redraw();
}

static int adm_pick_id(void)
{
    return adm.count ? adm.ids[adm.cursor] : -1;
}

/* LEFT/RIGHT: the first entry of the previous / next group. */
static void adm_pick_group_jump(int dir)
{
    int pf = adm.pf, c = adm.cursor;
    if (!adm.count) return;
    int g = adm_group(pf, adm.ids[c]);
    if (dir > 0) {
        while (c < adm.count - 1 && adm_group(pf, adm.ids[c]) == g) c++;
    } else {
        /* to the start of this group, or of the one before if already there */
        if (c > 0 && adm_group(pf, adm.ids[c - 1]) != g) {
            c--;
            g = adm_group(pf, adm.ids[c]);
        }
        while (c > 0 && adm_group(pf, adm.ids[c - 1]) == g) c--;
    }
    adm.cursor = c;
}

/* ---------------- drawing ---------------- */

static void adm_header(const char *title)
{
    char buf[24];
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    text_draw_col(16, 8, title, INK_RED, INK_RED_SH);
    money_text(buf, money);
    text_draw_right(228, 8, buf);
}

/* The bottom panel: two lines (a result message replaces the second). */
static void adm_bottom_msg(int x, int y)
{
    if (adm.msg[0]) text_draw_col(x, y, adm.msg, INK_GREEN, INK_GREEN_SH);
}

static void adm_draw_main(void)
{
    screen_begin(0);
    adm_header("ADMIN");
    canvas_window(0, 3, CANVAS_COLS, 12, WIN_STD);
    for (int i = 0; i < AM_COUNT; i++) {
        int y = 28 + i * 14;
        if (i == adm.main_cursor) {
            canvas_glow(12, y, 216, 14);
            text_draw(13, y, "{");
        }
        text_draw(24, y, ADM_MAIN[i]);
    }
    canvas_window(0, 15, CANVAS_COLS, 5, WIN_STD);
    if (adm.msg[0]) {
        char wrapped[128];
        text_wrap(wrapped, adm.msg, 208);
        text_draw_col(16, 124, wrapped, INK_GREEN, INK_GREEN_SH);
    } else {
        text_draw(16, 124, ADM_MAIN_HELP[adm.main_cursor]);
    }
}

static const char *adm_cat_name(int cat)
{
    return cat == CAT_PHYS ? "PHYSICAL" : cat == CAT_SPEC ? "ELEMENTAL" : "STATUS";
}

/* A move's details in the picker's bottom panel: the type badge, its kind
 * and uses, then power and accuracy (or the result message). */
static void adm_move_info_wide(int mv)
{
    char buf[32];
    if (mv == MOVE_NONE || mv >= MOVE_COUNT) {
        text_draw_col(16, 124, "No move: the slot stays empty.", INK_SHADOW, INK_SHADOW);
        if (adm.msg[0]) adm_bottom_msg(16, 140);
        return;
    }
    const Move *md = &MOVES[mv];
    draw_type_badge(1, 16, md->type);
    text_draw_col(48, 124, adm_cat_name(md->cat), INK_BLUE, INK_BLUE_SH);
    str_copy(buf, "USES ");
    str_put_int(buf, md->pp);
    text_draw_right(228, 124, buf);
    if (adm.msg[0]) {
        adm_bottom_msg(48, 140);
        return;
    }
    buf[0] = 0;
    if (md->power) {
        str_put(buf, "POW ");
        str_put_int(buf, md->power);
        str_put(buf, "   ");
    }
    str_put(buf, "ACC ");
    if (md->acc) str_put_int(buf, md->acc);
    else str_put(buf, "sure");
    text_draw(48, 140, buf);
}

static void adm_evo_text(char *buf, int sp)
{
    const Species *s = &SPECIES[sp];
    switch (s->evo_kind) {
    case EVO_LEVEL: str_copy(buf, "GROWS AT "); str_put_int(buf, s->evo_param); break;
    case EVO_ITEM: str_copy(buf, "GROWS: ITEM"); break;
    case EVO_BOND: str_copy(buf, "GROWS: BOND"); break;
    default: str_copy(buf, "FINAL FORM"); break;
    }
}

static void adm_draw_pick(void)
{
    char buf[40];
    int pf = adm.pf;
    screen_begin(0);
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    const char *title = ADM_TITLES[pf];
    if (pf == PF_TEACH_SLOT) {        /* no order label here: room for the name */
        str_copy(buf, "SLOT: ");
        str_put(buf, kin_name(&party[adm.teach]));
        title = buf;
    }
    text_draw_col(16, 8, title, INK_RED, INK_RED_SH);
    if (ADM_ORDER[pf][0]) {
        const char *o = ADM_ORDER[pf][adm.order[pf] & 1];
        text_draw_col(ADM_ORDER_RIGHT - text_width(o), 8, o, INK_BLUE, INK_BLUE_SH);
    }
    buf[0] = 0;
    str_put_int(buf, adm.cursor + 1);
    str_put(buf, "/");
    str_put_int(buf, adm.count);
    small_text_draw(230 - small_text_width(buf), 12, buf);

    canvas_window(0, 3, CANVAS_COLS, 12, WIN_STD);
    for (int r = 0; r < ADM_ROWS && adm.scroll + r < adm.count; r++) {
        int i = adm.scroll + r, id = adm.ids[i], y = 28 + r * 14;
        if (i == adm.cursor) {
            canvas_glow(8, y, 224, 14);
            text_draw(9, y, "{");
        }
        switch (pf) {
        case PF_ITEM:
            text_draw_fit(20, y, ITEMS[id].name, 118);
            text_draw_col(142, y, POCKET_NAMES[ITEMS[id].pocket], INK_BLUE, INK_BLUE_SH);
            if (bag[id] > 0) {
                buf[0] = 0;
                str_put_int(buf, bag[id]);
                small_text_draw(230 - small_text_width(buf), y + 4, buf);
            }
            break;
        case PF_SPECIES:
            buf[0] = 0;
            str_put_int3(buf, id + 1);
            small_text_draw(20, y + 4, buf);
            text_draw_fit(40, y, SPECIES[id].name, 88);
            str_copy(buf, TYPE_NAMES[SPECIES[id].type1]);
            if (SPECIES[id].type2 != TYPE_NONE) {
                str_put(buf, " ");
                str_put(buf, TYPE_NAMES[SPECIES[id].type2]);
            }
            text_draw_col(228 - text_width(buf), y, buf, INK_BLUE, INK_BLUE_SH);
            break;
        case PF_FORM_MOVE:
        case PF_TEACH_MOVE:
            if (id == MOVE_NONE) {
                text_draw_col(20, y, "- NO MOVE -", INK_SHADOW, INK_SHADOW);
                break;
            }
            text_draw_col(20, y, TYPE_NAMES[MOVES[id].type], INK_BLUE, INK_BLUE_SH);
            text_draw_fit(72, y, MOVES[id].name, 124);
            if (MOVES[id].power) {
                buf[0] = 0;
                str_put_int(buf, MOVES[id].power);
                small_text_draw(230 - small_text_width(buf), y + 4, buf);
            }
            break;
        case PF_TEACH_KIN:
            text_draw(20, y, kin_name(&party[id]));
            mon_level_text(buf, &party[id]);
            small_text_draw(230 - small_text_width(buf), y + 4, buf);
            break;
        case PF_TEACH_SLOT: {
            int mv = party[adm.teach].moves[id];
            buf[0] = 0;
            str_put_int(buf, id + 1);
            small_text_draw(20, y + 4, buf);
            if (mv == MOVE_NONE || mv >= MOVE_COUNT) {
                text_draw_col(32, y, "- empty -", INK_SHADOW, INK_SHADOW);
                break;
            }
            text_draw(32, y, MOVES[mv].name);
            buf[0] = 0;
            str_put_int(buf, party[adm.teach].pp[id]);
            str_put(buf, "/");
            str_put_int(buf, MOVES[mv].pp);
            small_text_draw(230 - small_text_width(buf), y + 4, buf);
            break;
        }
        }
    }
    if (adm.scroll > 0) text_draw_col(112, 20, "^", INK_BLUE, INK_BLUE_SH);
    if (adm.scroll + ADM_ROWS < adm.count) text_draw_col(112, 106, "}", INK_BLUE, INK_BLUE_SH);

    /* bottom: what the cursor is on */
    canvas_window(0, 15, CANVAS_COLS, 5, WIN_STD);
    int id = adm_pick_id();
    if (id < 0) {
        text_draw(16, 124, "Nothing to choose.");
        return;
    }
    switch (pf) {
    case PF_ITEM:
        draw_item_icon(1, 15, id);
        if (adm.state == AD_QTY) {
            text_draw_col(40, 124, "HOW MANY?", INK_BLUE, INK_BLUE_SH);
            text_draw_col(140, 124, "<", INK_BLUE, INK_BLUE_SH);
            buf[0] = 0;
            str_put_int(buf, adm.qty);
            text_draw_center(170, 124, buf);
            text_draw_col(196, 124, ">", INK_BLUE, INK_BLUE_SH);
            text_draw_col(40, 140, "UP/DOWN 1  L/R 10  A: GIVE", INK_SHADOW, INK_SHADOW);
            break;
        }
        {
            /* the description's first two lines (the pocket and count are
             * in the row); a result message takes the second */
            char wrapped[400];
            text_wrap(wrapped, ITEMS[id].desc, 188);
            char *second = 0;
            for (char *p = wrapped; *p; p++)
                if (*p == '\n') {
                    *p = 0;
                    if (second) break;
                    second = p + 1;
                }
            text_draw(40, 124, wrapped);
            if (adm.msg[0]) adm_bottom_msg(40, 140);
            else if (second) text_draw(40, 140, second);
        }
        break;
    case PF_SPECIES: {
        const Species *s = &SPECIES[id];
        draw_type_badge(6, 16, s->type1);
        if (s->type2 != TYPE_NONE) draw_type_badge(10, 16, s->type2);
        text_draw(128, 124, RARITY_NAMES[s->rarity % RARITY_COUNT]);
        adm_evo_text(buf, id);
        text_draw_col(128, 140, buf, INK_GREEN, INK_GREEN_SH);
        break;
    }
    case PF_FORM_MOVE:
    case PF_TEACH_MOVE:
        adm_move_info_wide(id);
        break;
    case PF_TEACH_KIN: {
        const Monster *m = &party[id];
        mon_hp_text(buf, m);
        text_draw(48, 124, SPECIES[m->species].name);   /* the icon sits left of it */
        small_text_draw(228 - small_text_width(buf), 128, buf);
        text_draw_col(48, 140, "A: choose a slot", INK_SHADOW, INK_SHADOW);
        break;
    }
    case PF_TEACH_SLOT:
        if (adm.msg[0]) {
            text_draw_col(16, 124, adm.msg, INK_GREEN, INK_GREEN_SH);
            text_draw_col(16, 140, "A: another slot   B: back", INK_SHADOW, INK_SHADOW);
        } else {
            text_draw(16, 124, "A: choose the move for this slot");
            text_draw_col(16, 140, "(or NO MOVE to clear it)", INK_SHADOW, INK_SHADOW);
        }
        break;
    }
}

static const char *const ADM_FORM_LABELS[AF_COUNT] = {
    "KIN", "LEVEL", "LUSTROUS", "NAME", "", "", "", "", "SEND TO", "",
};

static void adm_draw_form(void)
{
    char buf[40];
    const Species *s = &SPECIES[adm.sp];
    screen_begin(0);
    canvas_window(0, 0, 10, 3, WIN_STD);
    text_draw_col(12, 8, "ADD KIN", INK_RED, INK_RED_SH);
    canvas_window(0, 3, 10, 9, WIN_STD);     /* the portrait sits on it */
    canvas_window(0, 12, 10, 8, WIN_STD);
    int mrow = adm.row >= AF_MOVE1 && adm.row <= AF_MOVE4;
    int mv = mrow ? adm.draft.moves[adm.row - AF_MOVE1] : MOVE_NONE;
    if (mrow && mv < MOVE_COUNT) {
        const Move *md = &MOVES[mv];
        text_draw_col(8, 100, adm_cat_name(md->cat), INK_BLUE, INK_BLUE_SH);
        draw_type_badge(1, 14, md->type);
        buf[0] = 0;
        if (md->power) {
            str_copy(buf, "POW ");
            str_put_int(buf, md->power);
        } else {
            str_copy(buf, "USES ");
            str_put_int(buf, md->pp);
        }
        text_draw(8, 128, buf);
        str_copy(buf, "ACC ");
        if (md->acc) str_put_int(buf, md->acc);
        else str_put(buf, "sure");
        text_draw(8, 142, buf);
    } else if (mrow) {
        text_draw_col(8, 100, "EMPTY SLOT", INK_SHADOW, INK_SHADOW);
        text_draw_col(8, 128, "A: pick one", INK_SHADOW, INK_SHADOW);
    } else {
        str_copy(buf, "No.");
        str_put_int3(buf, adm.sp + 1);
        text_draw(8, 100, buf);
        if (adm.lustrous) text_draw_col(64, 100, "*", INK_RED, INK_RED_SH);
        draw_type_badge(1, 14, s->type1);
        if (s->type2 != TYPE_NONE) draw_type_badge(5, 14, s->type2);
        text_draw(8, 128, RARITY_NAMES[s->rarity % RARITY_COUNT]);
        adm_evo_text(buf, adm.sp);
        text_draw_fit(8, 142, buf, 64);
    }

    canvas_window(10, 0, 20, 20, WIN_STD);
    for (int r = 0; r < AF_COUNT; r++) {
        int y = 8 + r * 14;
        if (r == adm.row) {
            canvas_glow(86, y, 148, 14);
            text_draw(87, y, "{");
        }
        if (r >= AF_MOVE1 && r <= AF_MOVE4) {
            int k = r - AF_MOVE1, m = adm.draft.moves[k];
            str_copy(buf, "MOVE ");
            str_put_int(buf, k + 1);
            text_draw(98, y, buf);
            if (m < MOVE_COUNT) text_draw_fit(146, y, MOVES[m].name, 84);
            else text_draw_col(146, y, "-", INK_SHADOW, INK_SHADOW);
            continue;
        }
        if (r == AF_ADD) {
            text_draw_col(98, y, "ADD THIS KIN", INK_GREEN, INK_GREEN_SH);
            continue;
        }
        text_draw(98, y, ADM_FORM_LABELS[r]);
        const char *val = "";
        int ink = INK_DARK, sh = INK_SHADOW;
        switch (r) {
        case AF_KIN: val = s->name; break;
        case AF_LEVEL:
            buf[0] = 0;
            str_put_int(buf, adm.level);
            val = buf;
            break;
        case AF_LUSTROUS:
            val = adm.lustrous ? "YES" : "NO";
            if (adm.lustrous) { ink = INK_RED; sh = INK_RED_SH; }
            break;
        case AF_NAME:
            if (adm.draft.name[0]) {
                val = adm.draft.name;
            } else {
                val = "(none)";
                ink = sh = INK_SHADOW;
            }
            break;
        case AF_DEST:
            val = adm.to_team ? "TEAM" : "SHELF";
            ink = INK_BLUE;
            sh = INK_BLUE_SH;
            break;
        }
        int w = text_width(val);
        int adjustable = r == AF_KIN || r == AF_LEVEL || r == AF_LUSTROUS || r == AF_DEST;
        int right = adjustable && r == adm.row ? 222 : 230;
        text_draw_col(right - w, y, val, ink, sh);
        if (adjustable && r == adm.row) {
            text_draw_col(right - w - 8, y, "<", INK_BLUE, INK_BLUE_SH);
            text_draw_col(224, y, ">", INK_BLUE, INK_BLUE_SH);
        }
    }
}

static void adm_redraw(void)
{
    switch (adm.state) {
    case AD_MAIN: adm_draw_main(); break;
    case AD_PICK:
    case AD_QTY: adm_draw_pick(); break;
    case AD_FORM: adm_draw_form(); break;
    default: break;
    }
    if (adm.state == AD_PICK && adm.pf == PF_SPECIES && adm.count)
        load_monster_icon_ex(0, adm_pick_id(), 0);
    if (adm.state == AD_PICK && adm.pf == PF_TEACH_KIN && adm.count) {
        const Monster *m = &party[adm_pick_id()];
        load_monster_icon_ex(0, m->species, (m->flags & MF_LUSTROUS) != 0);
    }
}

/* ---------------- the screen ---------------- */

static void admin_open(void)
{
    dialog_clear();
    adm.state = AD_MAIN;
    adm.main_cursor = 0;
    adm.msg[0] = 0;
    ext_open(admin_update, admin_draw, 0);
    adm_redraw();
}

static void admin_close(void)
{
    sfx_play(SFX_CANCEL);
    dialog_clear();
    canvas_clear();
    start_menu_open();
}

static void adm_form_open(void)
{
    adm.state = AD_FORM;
    adm.row = 0;
    if (adm.level < 1 || adm.level > MAX_LEVEL) adm.level = 5;
    for (unsigned i = 0; i < sizeof(adm.draft.name); i++) adm.draft.name[i] = 0;
    adm.lustrous = 0;
    adm.to_team = 0;
    adm_set_species(adm.sp);
    adm_redraw();
}

/* A result over the form (the message box), then back to the form. */
static void adm_say(const char *text)
{
    adm.return_state = adm.state;
    adm.state = AD_DIALOG;
    dlg_say(text);
}

static void admin_after_naming(void)
{
    ext_open(admin_update, admin_draw, 0);
    adm.state = AD_FORM;
    load_monster_gfx_ex(0, adm.sp, 0, adm.lustrous);
    adm_redraw();
}

static void adm_form_add(void)
{
    char msg[MSG_TEXT_MAX];
    if (!moves_count(adm.draft.moves)) {
        sfx_play(SFX_ERROR);
        adm_say("A kin needs at least one move.");
        return;
    }
    Monster m = admin_build_kin(adm.sp, adm.level, adm.lustrous, adm.draft.moves, adm.draft.name);
    int where = 0, r = admin_give_kin(&m, adm.to_team, &where);
    if (r < 0) {
        sfx_play(SFX_ERROR);
        adm_say("There is no room on the team or on the Shelf.");
        return;
    }
    sfx_play(SFX_CONFIRM);
    str_copy(msg, kin_name(&m));
    if (r == 0) {
        str_put(msg, " joined your team!");
    } else {
        str_put(msg, adm.to_team ? " went to SHELF BOX " : " is on the Shelf, in BOX ");
        str_put_int(msg, where + 1);
        str_put(msg, adm.to_team ? " (the team is full)." : ".");
    }
    adm_say(msg);
}

static void adm_form_update(void)
{
    int old_row = adm.row, changed = 0;
    if (key_rep(KEY_UP)) adm.row = (adm.row + AF_COUNT - 1) % AF_COUNT;
    if (key_rep(KEY_DOWN)) adm.row = (adm.row + 1) % AF_COUNT;
    int d = 0;
    if (key_rep(KEY_LEFT)) d = -1;
    if (key_rep(KEY_RIGHT)) d = 1;
    if (key_rep(KEY_L)) d = -10;
    if (key_rep(KEY_R)) d = 10;
    if (d && old_row == adm.row) {
        switch (adm.row) {
        case AF_KIN: adm_set_species(adm.sp + d); changed = 1; break;
        case AF_LEVEL: {
            int lv = clampi(adm.level + d, 1, MAX_LEVEL);
            if (lv != adm.level) {
                adm.level = lv;
                adm_draft_sync();
                changed = 1;
            }
            break;
        }
        case AF_LUSTROUS:
            if (d == 1 || d == -1) {
                adm.lustrous ^= 1;
                adm_draft_sync();
                changed = 1;
            }
            break;
        case AF_DEST:
            if (d == 1 || d == -1) {
                adm.to_team ^= 1;
                changed = 1;
            }
            break;
        }
    }
    if (key_hit(KEY_SELECT) && adm.row >= AF_MOVE1 && adm.row <= AF_MOVE4) {
        adm_natural_moves();     /* back to its own moves at this level */
        changed = 1;
    }
    if (old_row != adm.row || changed) {
        sfx_play(SFX_CURSOR);
        adm_redraw();
    }
    if (key_hit(KEY_B)) {
        sfx_play(SFX_CANCEL);
        adm.state = AD_MAIN;
        adm.msg[0] = 0;
        adm_redraw();
        return;
    }
    if (!key_hit(KEY_A)) return;
    switch (adm.row) {
    case AF_KIN:
        sfx_play(SFX_CONFIRM);
        adm_pick_open(PF_SPECIES, adm.sp);
        break;
    case AF_LUSTROUS:
        adm.lustrous ^= 1;
        adm_draft_sync();
        sfx_play(SFX_CURSOR);
        adm_redraw();
        break;
    case AF_DEST:
        adm.to_team ^= 1;
        sfx_play(SFX_CURSOR);
        adm_redraw();
        break;
    case AF_NAME:
        sfx_play(SFX_CONFIRM);
        nm_draft = &adm.draft;
        naming_open(NM_DRAFT, 0, admin_after_naming);
        break;
    case AF_ADD: adm_form_add(); break;
    case AF_LEVEL: break;
    default:
        sfx_play(SFX_CONFIRM);
        adm.slot = adm.row - AF_MOVE1;
        adm_pick_open(PF_FORM_MOVE, adm.draft.moves[adm.slot]);
        break;
    }
}

/* B in a picker: back to where it was opened from. */
static void adm_pick_back(void)
{
    sfx_play(SFX_CANCEL);
    adm.msg[0] = 0;
    switch (adm.pf) {
    case PF_SPECIES:
    case PF_FORM_MOVE:
        adm.state = AD_FORM;
        load_monster_gfx_ex(0, adm.sp, 0, adm.lustrous);
        adm_redraw();
        break;
    case PF_TEACH_SLOT: adm_pick_open(PF_TEACH_KIN, adm.teach); break;
    case PF_TEACH_MOVE:
        adm_pick_open(PF_TEACH_SLOT, adm.slot);
        break;
    default:
        adm.state = AD_MAIN;
        adm_redraw();
        break;
    }
}

/* Teach `mv` (or MOVE_NONE: clear) in slot adm.slot of team kin adm.teach. */
static void adm_teach(int mv)
{
    Monster *m = &party[adm.teach];
    int slot = adm.slot;
    if (mv == MOVE_NONE) {
        if (m->moves[slot] == MOVE_NONE || moves_count(m->moves) <= 1) {
            sfx_play(SFX_ERROR);
            str_copy(adm.msg, "It must keep at least one move.");
            adm_redraw();
            return;
        }
        str_copy(adm.msg, "Cleared: ");
        str_put(adm.msg, MOVES[m->moves[slot]].name);
        str_put(adm.msg, ".");
        m->moves[slot] = MOVE_NONE;
        m->pp[slot] = 0;
    } else {
        if (moves_has_other(m->moves, slot, mv)) {
            sfx_play(SFX_ERROR);
            str_copy(adm.msg, "It already knows that move.");
            adm_redraw();
            return;
        }
        monster_replace_move(m, slot, mv);
        str_copy(adm.msg, "Learned ");
        str_put(adm.msg, MOVES[mv].name);
        str_put(adm.msg, "!");
    }
    moves_compact(m->moves, m->pp);
    sfx_play(SFX_CONFIRM);
    char keep[96];
    str_copy(keep, adm.msg);
    adm_pick_open(PF_TEACH_SLOT, slot);
    str_copy(adm.msg, keep);
    adm_redraw();
}

static void adm_pick_choose(void)
{
    int id = adm_pick_id();
    if (id < 0) return;
    switch (adm.pf) {
    case PF_ITEM:
        sfx_play(SFX_CONFIRM);
        adm.state = AD_QTY;
        adm.qty = 1;
        adm.msg[0] = 0;
        adm_redraw();
        break;
    case PF_SPECIES:
        sfx_play(SFX_CONFIRM);
        adm_set_species(id);
        adm.state = AD_FORM;
        adm_redraw();
        break;
    case PF_FORM_MOVE:
        if (id != MOVE_NONE && moves_has_other(adm.draft.moves, adm.slot, id)) {
            sfx_play(SFX_ERROR);
            str_copy(adm.msg, "It already has that move.");
            adm_redraw();
            break;
        }
        sfx_play(SFX_CONFIRM);
        adm.draft.moves[adm.slot] = (u8)id;
        adm.draft.pp[adm.slot] = id < MOVE_COUNT ? MOVES[id].pp : 0;
        adm.custom = 1;
        adm.state = AD_FORM;
        load_monster_gfx_ex(0, adm.sp, 0, adm.lustrous);
        adm_redraw();
        break;
    case PF_TEACH_KIN:
        sfx_play(SFX_CONFIRM);
        adm.teach = id;
        adm_pick_open(PF_TEACH_SLOT, 0);
        break;
    case PF_TEACH_SLOT:
        sfx_play(SFX_CONFIRM);
        adm.slot = id;
        adm_pick_open(PF_TEACH_MOVE, party[adm.teach].moves[id]);
        break;
    case PF_TEACH_MOVE: adm_teach(id); break;
    }
}

static void adm_pick_update(void)
{
    int old = adm.cursor, redraw = 0;
    if (key_rep(KEY_UP)) adm.cursor = adm.cursor > 0 ? adm.cursor - 1 : adm.count - 1;
    if (key_rep(KEY_DOWN)) adm.cursor = adm.cursor < adm.count - 1 ? adm.cursor + 1 : 0;
    if (key_rep(KEY_L)) adm.cursor = clampi(adm.cursor - ADM_ROWS, 0, adm.count - 1);
    if (key_rep(KEY_R)) adm.cursor = clampi(adm.cursor + ADM_ROWS, 0, adm.count - 1);
    if (key_rep(KEY_LEFT)) adm_pick_group_jump(-1);
    if (key_rep(KEY_RIGHT)) adm_pick_group_jump(1);
    if (key_hit(KEY_SELECT) && ADM_ORDER[adm.pf][0]) {
        int id = adm_pick_id();
        adm.order[adm.pf] ^= 1;
        adm_pick_build();
        adm_pick_goto(id);     /* the same entry stays selected */
        redraw = 1;
    }
    if (old != adm.cursor || redraw) {
        adm_pick_scroll();
        adm.msg[0] = 0;
        sfx_play(SFX_CURSOR);
        adm_redraw();
    }
    if (key_hit(KEY_B)) {
        adm_pick_back();
        return;
    }
    if (key_hit(KEY_A)) adm_pick_choose();
}

static void adm_qty_update(void)
{
    int id = adm_pick_id(), max = adm_qty_max(id), old = adm.qty;
    if (key_rep(KEY_UP) || key_rep(KEY_RIGHT)) adm.qty = adm.qty >= max ? 1 : adm.qty + 1;
    if (key_rep(KEY_DOWN) || key_rep(KEY_LEFT)) adm.qty = adm.qty <= 1 ? max : adm.qty - 1;
    if (key_rep(KEY_R)) adm.qty = clampi(adm.qty + 10, 1, max);
    if (key_rep(KEY_L)) adm.qty = clampi(adm.qty - 10, 1, max);
    if (old != adm.qty) {
        sfx_play(SFX_CURSOR);
        adm_redraw();
    }
    if (key_hit(KEY_B)) {
        sfx_play(SFX_CANCEL);
        adm.state = AD_PICK;
        adm_redraw();
        return;
    }
    if (key_hit(KEY_A)) {
        sfx_play(SFX_CONFIRM);
        admin_give_item(id, adm.qty);
        adm.state = AD_PICK;
        adm_redraw();
    }
}

static void adm_main_update(void)
{
    int old = adm.main_cursor;
    if (key_rep(KEY_UP)) adm.main_cursor = (adm.main_cursor + AM_COUNT - 1) % AM_COUNT;
    if (key_rep(KEY_DOWN)) adm.main_cursor = (adm.main_cursor + 1) % AM_COUNT;
    if (old != adm.main_cursor) {
        adm.msg[0] = 0;
        sfx_play(SFX_CURSOR);
        adm_redraw();
    }
    if (key_hit(KEY_B) || key_hit(KEY_START)) {
        admin_close();
        return;
    }
    if (!key_hit(KEY_A)) return;
    switch (adm.main_cursor) {
    case AM_COINS:
        sfx_play(SFX_CONFIRM);
        admin_add_coins();
        adm_redraw();
        break;
    case AM_ITEM:
        sfx_play(SFX_CONFIRM);
        adm_pick_open(PF_ITEM, -1);
        break;
    case AM_KIN:
        sfx_play(SFX_CONFIRM);
        adm_form_open();
        break;
    case AM_TEACH:
        if (!party_count) {
            sfx_play(SFX_ERROR);
            str_copy(adm.msg, "You have no kin on your team.");
            adm_redraw();
            break;
        }
        sfx_play(SFX_CONFIRM);
        adm_pick_open(PF_TEACH_KIN, 0);
        break;
    case AM_HEAL:
        sfx_play(SFX_CONFIRM);
        admin_heal();
        adm_redraw();
        break;
    default: admin_close(); break;
    }
}

static void admin_update(void)
{
    switch (adm.state) {
    case AD_MAIN: adm_main_update(); break;
    case AD_PICK: adm_pick_update(); break;
    case AD_QTY: adm_qty_update(); break;
    case AD_FORM: adm_form_update(); break;
    case AD_DIALOG:
        if (!dialog_update()) {
            adm.state = adm.return_state;
            adm_redraw();
        }
        break;
    }
}

static void admin_draw(void)
{
    if (adm.state == AD_FORM || (adm.state == AD_DIALOG && adm.return_state == AD_FORM))
        spr_push(8, 28, OT_MON_A, SQ64, OBANK_MON_A, 0, 0);
    else if (adm.state == AD_PICK && (adm.pf == PF_SPECIES || adm.pf == PF_TEACH_KIN) && adm.count)
        spr_push(8, 124, OT_ICON(0), SQ32, OBANK_NPC, 0, 0);
}
