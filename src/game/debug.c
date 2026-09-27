/*
 * Developer tools, reachable from the title screen: hold SELECT and press
 * START (docs/EXPANSION.md 10.1).
 *
 *   ASSET VIEWER  every tileset's generated viewer maps (world/debug/): all
 *                 terrain, trees, buildings and decor standing on mixed
 *                 grounds, with kin wandering a pen. A on a thing names it;
 *                 L / R change the kin in the pen; SELECT goes back here.
 *   KIN VIEWER    every species: front, back (lustrous with A), menu icon and
 *                 the walking overworld frames on light, grass and dark.
 *   PORTRAITS     the bout portraits: every keeper archetype cycling through
 *                 its five frames in any of its colour variations (with its
 *                 overworld self walking beside it), and the player from the
 *                 front and from behind.
 *   WARP          jump to any map (lands on the walkable cell nearest the
 *                 middle).
 *   ADMIN MODE    A switches it ON / OFF (opt.admin): while it is on, the
 *                 START menu has an ADMIN entry (admin.c). With a save on
 *                 the cartridge the switch is written to it at once, so it
 *                 stays set; without one it goes into the first save.
 *
 * Nothing else here touches the save unless you save from the START menu.
 */

enum { DBG_MENU, DBG_VIEWS, DBG_KIN, DBG_WARP, DBG_KEEPER };
#define VIEW_PEN_ROWS 6   /* tools/gen_field_gfx.py VIEW_PEN_H */

static struct {
    int state, cursor, scroll, sp, lustrous, parade, frame, keeper, vary;
    int admin_note;   /* 0 none, 1 saved, 2 not saved (no save yet), 3 the write failed */
} dbg;

enum { DBGI_VIEWS, DBGI_KIN, DBGI_PORTRAITS, DBGI_WARP, DBGI_ADMIN, DBGI_BACK };
static const char *const DBG_ITEMS[] = { "ASSET VIEWER", "KIN VIEWER", "PORTRAITS", "WARP TO MAP", "ADMIN MODE", "BACK" };
#define DBG_ITEM_COUNT 5
#define DBG_ROWS 8

static int dbg_view_first(void)
{
    for (int m = 0; m < MAP_COUNT; m++)
        if (MAPS[m].flags & MF_DEBUG) return m;
    return MAP_COUNT;
}

static int dbg_view_count(void)
{
    int n = 0;
    for (int m = 0; m < MAP_COUNT; m++) n += (MAPS[m].flags & MF_DEBUG) != 0;
    return n;
}

static void dbg_list_draw(const char *title, int count, const char *(*label)(int))
{
    screen_begin(0);
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    text_draw_col(16, 8, title, INK_BLUE, INK_BLUE_SH);
    canvas_window(0, 3, CANVAS_COLS, 17, WIN_STD);
    for (int r = 0; r < DBG_ROWS && dbg.scroll + r < count; r++) {
        int i = dbg.scroll + r;
        if (i == dbg.cursor) text_draw(14, 30 + r * 14, "{");
        text_draw(24, 30 + r * 14, label(i));
    }
}

static const char *dbg_menu_label(int i) { return DBG_ITEMS[i]; }
static const char *dbg_view_label(int i) { return MAPS[dbg_view_first() + i].name; }
static const char *dbg_warp_label(int i) { return MAPS[i].name; }

static void dbg_redraw(void)
{
    switch (dbg.state) {
    case DBG_MENU: {
        dbg_list_draw("DEBUG", DBG_ITEM_COUNT, dbg_menu_label);
        int y = 30 + DBGI_ADMIN * 14;
        if (opt.admin) text_draw_col(112, y, "ON", INK_GREEN, INK_GREEN_SH);
        else text_draw_col(112, y, "OFF", INK_SHADOW, INK_SHADOW);
        static const char *const NOTE[4] = {
            "A: ADMIN in the START menu",
            "Saved to the cartridge.",
            "Kept for the new game's save.",
            "Could not write the save!",
        };
        text_draw_col(24, 128, NOTE[dbg.admin_note & 3], INK_BLUE, INK_BLUE_SH);
        break;
    }
    case DBG_VIEWS: dbg_list_draw("ASSET VIEWER", dbg_view_count(), dbg_view_label); break;
    case DBG_WARP: dbg_list_draw("WARP TO MAP", MAP_COUNT, dbg_warp_label); break;
    default: break;
    }
}

static void debug_update(void);
static void debug_draw(void);
static int save_load(void);
static int save_write(void);

static void debug_open(void)
{
    dbg.state = DBG_MENU;
    dbg.cursor = dbg.scroll = 0;
    dbg.admin_note = 0;
    ext_open(debug_update, debug_draw, 0);
    dbg_redraw();
}

/* The walkable cell nearest the middle of a map (for warping in). */
static void dbg_find_spot(int map, int *ox, int *oy)
{
    map_load(map);
    int cx = map_w / 2, cy = map_h / 2, best = 1 << 30;
    *ox = cx;
    *oy = cy;
    for (int y = 0; y < map_h; y++)
        for (int x = 0; x < map_w; x++) {
            int a = cell_attr(x, y);
            if (a & (A_SOLID | A_LEDGE | A_WATER)) continue;
            int d = absi(x - cx) + absi(y - cy);
            if (MAPS[map].flags & MF_DEBUG) d = absi(x - 2) + absi(y - (map_h - 3));
            if (d < best) {
                best = d;
                *ox = x;
                *oy = y;
            }
        }
}

static void dbg_enter_map(int map)
{
    int x, y;
    dbg_find_spot(map, &x, &y);
    if (!party_count) {
        Monster m = monster_make(SP_FLARIX, 20);
        give_monster(&m);
        flag_set(FLAG_STARTER);
    }
    canvas_clear();
    field_setup_bg();
    game_mode = MODE_FIELD;
    field_enter_map(map, x, y, DIR_DOWN);
}

static void dbg_list_input(int count)
{
    int old = dbg.cursor;
    if (key_rep(KEY_UP) && dbg.cursor > 0) dbg.cursor--;
    if (key_rep(KEY_DOWN) && dbg.cursor < count - 1) dbg.cursor++;
    if (key_rep(KEY_L)) dbg.cursor = clampi(dbg.cursor - DBG_ROWS, 0, count - 1);
    if (key_rep(KEY_R)) dbg.cursor = clampi(dbg.cursor + DBG_ROWS, 0, count - 1);
    if (dbg.cursor < dbg.scroll) dbg.scroll = dbg.cursor;
    if (dbg.cursor >= dbg.scroll + DBG_ROWS) dbg.scroll = dbg.cursor - DBG_ROWS + 1;
    if (old != dbg.cursor) {
        sfx_play(SFX_CURSOR);
        dbg_redraw();
    }
}

/* ---------------- kin viewer ---------------- */

static void dbg_kin_redraw(void)
{
    char buf[40];
    screen_begin(0);
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    str_copy(buf, "No.");
    str_put_int(buf, dbg.sp + 1);
    str_put(buf, " ");
    str_put(buf, SPECIES[dbg.sp].name);
    text_draw_col(16, 8, buf, INK_BLUE, INK_BLUE_SH);
    str_copy(buf, RARITY_NAMES[SPECIES[dbg.sp].rarity]);
    text_draw_right(228, 8, buf);
    /* three backdrops: light, grass green, night */
    canvas_fill(0, 24, 80, 88, 1);
    canvas_fill(80, 24, 80, 88, 6);
    canvas_fill(160, 24, 80, 88, 4);
    canvas_window(0, 14, CANVAS_COLS, 6, WIN_STD);
    /* help on the left, the type badges on their own on the right */
    text_draw(12, 118, "LEFT/RIGHT: kin");
    text_draw(12, 134, "L/R: 10   A: lustrous");
    draw_type_badge(19, 15, SPECIES[dbg.sp].type1);
    if (SPECIES[dbg.sp].type2 != TYPE_NONE) draw_type_badge(24, 15, SPECIES[dbg.sp].type2);
    text_draw_col(160, 136, "B: back", INK_SHADOW, INK_SHADOW);
    load_monster_gfx_ex(0, dbg.sp, 0, dbg.lustrous);
    load_monster_gfx_ex(1, dbg.sp, 1, dbg.lustrous);
    load_monster_icon_ex(0, dbg.sp, dbg.lustrous);
}

static void dbg_kin_input(void)
{
    int old = dbg.sp, oldl = dbg.lustrous;
    if (key_rep(KEY_LEFT)) dbg.sp = (dbg.sp + SP_COUNT - 1) % SP_COUNT;
    if (key_rep(KEY_RIGHT)) dbg.sp = (dbg.sp + 1) % SP_COUNT;
    if (key_rep(KEY_L)) dbg.sp = (dbg.sp + SP_COUNT - 10) % SP_COUNT;
    if (key_rep(KEY_R)) dbg.sp = (dbg.sp + 10) % SP_COUNT;
    if (key_hit(KEY_A)) dbg.lustrous ^= 1;
    if (old != dbg.sp || oldl != dbg.lustrous) {
        sfx_play(SFX_CURSOR);
        dbg_kin_redraw();
    }
    if (key_hit(KEY_B)) {
        dbg.state = DBG_MENU;
        dbg.cursor = 1;
        dbg_redraw();
    }
}

/* ---------------- portrait viewer ---------------- */

static void dbg_keeper_redraw(void)
{
    char buf[40];
    screen_begin(0);
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    str_copy(buf, KEEPER_LOOK[dbg.keeper].title);
    text_draw_col(16, 8, buf, INK_BLUE, INK_BLUE_SH);
    str_copy(buf, "look ");
    str_put_int(buf, dbg.vary);
    text_draw_right(228, 8, dbg.vary ? buf : "default look");
    canvas_fill(0, 24, 80, 88, 6);
    canvas_fill(80, 24, 80, 88, 1);
    canvas_fill(160, 24, 80, 88, 4);
    canvas_window(0, 14, CANVAS_COLS, 6, WIN_STD);
    text_draw(12, 118, "LEFT/RIGHT: keeper");
    text_draw(12, 134, "UP/DOWN: look   L/R: 10");
    keeper_palette(obj_palette + OBANK_MON_A * 16, dbg.keeper, dbg.vary);
    copy16(obj_palette + OBANK_MON_B * 16, hero_palette, 16);
}

static void dbg_keeper_input(void)
{
    int ok = dbg.keeper, ov = dbg.vary;
    if (key_rep(KEY_LEFT)) dbg.keeper = (dbg.keeper + KEEPER_COUNT - 1) % KEEPER_COUNT;
    if (key_rep(KEY_RIGHT)) dbg.keeper = (dbg.keeper + 1) % KEEPER_COUNT;
    if (key_rep(KEY_UP)) dbg.vary = (dbg.vary + 1) & 255;
    if (key_rep(KEY_DOWN)) dbg.vary = (dbg.vary + 255) & 255;
    if (key_rep(KEY_R)) dbg.vary = (dbg.vary + 10) & 255;
    if (key_rep(KEY_L)) dbg.vary = (dbg.vary + 246) & 255;
    if (ok != dbg.keeper || ov != dbg.vary) {
        sfx_play(SFX_CURSOR);
        dbg_keeper_redraw();
    }
    if (key_hit(KEY_B)) {
        dbg.state = DBG_MENU;
        dbg.cursor = 2;
        dbg_redraw();
    }
}

static void dbg_keeper_draw(void)
{
    /* the overworld-kin slots: menus own the low OBJ tiles */
    int step = dbg.frame / 36;
    /* the keeper walking the overworld: each direction for a while */
    static const u8 WALK[4] = { 0, 1, 0, 2 };
    int dir = (dbg.frame / 64) % 4, walk = WALK[(dbg.frame / 8) % 4];
    int owf = (dir == 1 ? 3 : dir >= 2 ? 6 : 0) + walk;
    switch (dbg.frame % 4) {   /* one upload a frame */
    case 0: copy32(VRAM_OBJ_TILES + OT_OWKIN(0) * 8, keeper_gfx[dbg.keeper][step % KF_COUNT], 64 * 8); break;
    case 1: copy32(VRAM_OBJ_TILES + OT_OWKIN(4) * 8, hero_front_gfx[step % HF_COUNT], 64 * 8); break;
    case 2: copy32(VRAM_OBJ_TILES + OT_OWKIN(8) * 8, hero_back_gfx[step % HB_COUNT], 64 * 8); break;
    default: copy32(VRAM_OBJ_TILES + OT_OWKIN(12) * 8, keeper_ow_gfx[dbg.keeper][owf], 8 * 8); break;
    }
    spr_push(62, 76, OT_OWKIN(12), TALL16x32, OBANK_MON_A, 0, dir == 3 ? ATTR1_HFLIP : 0);
    spr_push(0, 40, OT_OWKIN(0), SQ64, OBANK_MON_A, 0, 0);
    spr_push(88, 40, OT_OWKIN(4), SQ64, OBANK_MON_B, 0, 0);
    spr_push(168, 40, OT_OWKIN(8), SQ64, OBANK_MON_B, 0, 0);
}

/* ---------------- the screen ---------------- */

static void debug_update(void)
{
    dbg.frame++;
    if (dbg.state == DBG_KIN) {
        dbg_kin_input();
        return;
    }
    if (dbg.state == DBG_KEEPER) {
        dbg_keeper_input();
        return;
    }
    int count = dbg.state == DBG_MENU ? DBG_ITEM_COUNT : dbg.state == DBG_VIEWS ? dbg_view_count() : MAP_COUNT;
    dbg_list_input(count);
    if (key_hit(KEY_B)) {
        sfx_play(SFX_CANCEL);
        if (dbg.state == DBG_MENU) {
            canvas_clear();
            title_open(save_load() != 0);
            return;
        }
        dbg.state = DBG_MENU;
        dbg.cursor = dbg.scroll = 0;
        dbg_redraw();
        return;
    }
    if (!key_hit(KEY_A)) return;
    sfx_play(SFX_CONFIRM);
    if (dbg.state == DBG_MENU) {
        switch (dbg.cursor) {
        case DBGI_VIEWS: dbg.state = DBG_VIEWS; break;
        case DBGI_KIN:
            dbg.state = DBG_KIN;
            dbg_kin_redraw();
            return;
        case DBGI_PORTRAITS:
            dbg.state = DBG_KEEPER;
            dbg_keeper_redraw();
            return;
        case DBGI_WARP: dbg.state = DBG_WARP; break;
        case DBGI_ADMIN:
            /* the title loaded the save into memory: writing it back only
             * changes the switch */
            opt.admin ^= 1;
            dbg.admin_note = !title.has_save ? 2 : save_write() ? 1 : 3;
            dbg_redraw();
            return;
        default:
            canvas_clear();
            title_open(save_load() != 0);
            return;
        }
        dbg.cursor = dbg.scroll = 0;
        dbg_redraw();
    } else if (dbg.state == DBG_VIEWS) {
        dbg_enter_map(dbg_view_first() + dbg.cursor);
    } else {
        dbg_enter_map(dbg.cursor);
    }
}

static void debug_draw(void)
{
    if (dbg.state == DBG_KEEPER) {
        dbg_keeper_draw();
        return;
    }
    if (dbg.state != DBG_KIN) return;
    spr_push(8, 40, OT_MON_A, SQ64, OBANK_MON_A, 0, 0);
    spr_push(88, 40, OT_MON_B, SQ64, OBANK_MON_B, 0, 0);
    int f = (dbg.frame >> 4) & 1;
    for (int k = 0; k < 3; k++) {
        /* overworld frames: down, up, left walking */
        copy32(VRAM_OBJ_TILES + OT_OWKIN(k) * 8, kin_frame_gfx(dbg.sp, k * 2 + f), 16 * 8);
    }
    load_mon_pal(KIN_BANK_FIRST, dbg.sp, dbg.lustrous);
    for (int k = 0; k < 3; k++)
        spr_push(164 + k * 24, 68, OT_OWKIN(k), SQ32, KIN_BANK_FIRST, 0, 0);
    spr_push(176, 30, OT_ICON(0), SQ32, OBANK_NPC, 0, 0);
}

/* ---------------- the kin parade in viewer maps (field.c hooks) ---------------- */

static void debug_parade_spawn(void)
{
    for (int i = 0; i < WILD_MAX; i++) {
        if (wild[i].active) continue;
        for (int tries = 0; tries < 20; tries++) {
            int x = (int)rng_range((unsigned)map_w), y = map_h - 1 - VIEW_PEN_ROWS + (int)rng_range(VIEW_PEN_ROWS);
            if (!cell_walkable(x, y) || (x == player.x && y == player.y)) continue;
            int sp = (dbg.parade + i) % SP_COUNT;
            wild[i].mon = monster_make(sp, 10);
            wild[i].active = 1;
            wild[i].brimming = 0;
            wild[i].noticed = 0;
            wild[i].life = 60000;
            wild[i].think = (u16)(20 + rng_range(40));
            kin_place(&wild[i].k, sp, 0, x, y, (int)rng_range(4));
            break;
        }
    }
}

static void debug_parade_touch(int slot)
{
    char msg[64];
    str_copy(msg, SPECIES[wild[slot].mon.species].name);
    str_put(msg, " (L / R change the kin in the pen)");
    dlg_say(msg);
}

static void debug_parade_shift(int by)
{
    dbg.parade = (dbg.parade + SP_COUNT + by) % SP_COUNT;
    for (int i = 0; i < WILD_MAX; i++) wild[i].active = 0;
    debug_parade_spawn();
}

/* A in a viewer map: name whatever is in front of the player. */
static int debug_examine(int x, int y)
{
    if (!(MAPS[cur_map].flags & MF_DEBUG)) return 0;
    char msg[96];
    int sub;
    const DecorDef *d;
    const DecorPlace *p = decor_at(x, y, &sub, &d);
    if (p && station_of_decor(p->kind) >= 0) return 0;   /* crafting stations work here too */
    if (p) {
        str_copy(msg, "DECOR ");
        str_put(msg, DECOR_NAMES[p->kind]);
        str_put(msg, d->solid & (1u << sub) ? " (solid" : " (walkable");
        str_put(msg, d->top & (1u << sub) ? ", over people)" : ")");
    } else {
        int v = map_cell(x, y);
        str_copy(msg, "TERRAIN ");
        if (v == CELL_PATH) str_put(msg, "PATH");
        else if (v == CELL_WATER) str_put(msg, "WATER");
        else {
            str_put(msg, "metatile ");
            str_put_int(msg, v);
            if (is_overlay((u16)v)) str_put(msg, " (tree over ground)");
        }
    }
    dlg_say(msg);
    return 1;
}
