/*
 * The ALMANAC: every kin of the Vale is listed from the start; the list
 * marks the ones you have befriended. The detail page shows the portrait
 * (front/back), types, size, and a smoothly scrolling info panel with the
 * description, base stats, growth chain, level-up moves and habitat.
 *
 * The panel lives on BG2 as an 8-line ring buffer of panel_cols x 2 tiles
 * (tiles 600..1015), repeated twice down the 32-row map so it wraps every
 * 128 px; lines are rendered into the ring as they scroll into view and
 * WIN0 clips BG2 to the panel rectangle. The Lorebook reader uses the same
 * panel at full width (panel_wide).
 */

#define DEX_ROWS 7
#define PANEL_COLS_MAX 26
#define PANEL_Y 40
#define PANEL_H 112
#define PANEL_BLANK_TILE 1016

static int panel_cols = 18, panel_x = 88;   /* 18 cols at x=88, or 26 at x=16 */

enum { PL_BLANK, PL_TEXT, PL_HEADER, PL_GOOD, PL_BAD, PL_STAT, PL_MOVE, PL_LINE2 };

typedef struct { u8 kind, a; s16 b; char text[48]; } PanelLine;

#define PANEL_MAX_LINES 112

static struct {
    int state, cursor, scroll, back;
    int scroll_px, target_px, content_lines;
    int ring_line[8];
    PanelLine lines[PANEL_MAX_LINES];
} dex EWRAM_BSS;

EWRAM_BSS static u32 panel_strip[PANEL_COLS_MAX * 2 * 8];

/* ---------------- content ---------------- */

static PanelLine *pl_add(int kind, const char *text)
{
    if (dex.content_lines >= PANEL_MAX_LINES) return &dex.lines[PANEL_MAX_LINES - 1];
    PanelLine *l = &dex.lines[dex.content_lines++];
    l->kind = (u8)kind;
    l->a = 0;
    l->b = 0;
    str_copy(l->text, text ? text : "");
    return l;
}

static void pl_add_wrapped(const char *text, int kind)
{
    char wrapped[420];
    text_wrap(wrapped, text, panel_cols * 8 - 8);
    char line[48];
    int n = 0;
    for (const char *p = wrapped;; p++) {
        if (*p == '\n' || !*p) {
            line[n] = 0;
            pl_add(kind, line);
            n = 0;
            if (!*p) break;
        } else if (n < 47) {
            line[n++] = *p;
        }
    }
}

static int species_chain_root(int sp)
{
    for (int guard = 0; guard < 3; guard++) {
        int p = species_prevo(sp);
        if (p < 0) break;
        sp = p;
    }
    return sp;
}

static void dex_habitat(int sp)
{
    int any = 0;
    char buf[40];
    for (int z = 0; z < WILD_ZONE_COUNT; z++) {
        const WildZone *zone = &WILD_ZONES[z];
        int total = 0, w = 0, lo = 0, hi = 0;
        for (int i = 0; i < zone->count; i++) {
            total += zone->slots[i].weight;
            if (zone->slots[i].species == sp) {
                w = zone->slots[i].weight;
                lo = zone->slots[i].min_level;
                hi = zone->slots[i].max_level;
            }
        }
        if (!w) continue;
        pl_add(PL_TEXT, zone->name);
        str_copy(buf, "  Lv");
        str_put_int(buf, lo);
        str_put(buf, "-");
        str_put_int(buf, hi);
        str_put(buf, w * 100 / total >= 15 ? "  common" : w * 100 / total >= 8 ? "  uncommon" : "  rare");
        pl_add(PL_TEXT, buf);
        any = 1;
    }
    for (int i = 0; i < 3; i++)
        if (STARTER_SPECIES[i] == sp) {
            pl_add(PL_TEXT, "A Kindling kit");
            any = 1;
        }
    if (sp == SP_DRAKORA) {
        pl_add(PL_TEXT, "Above STORMSTONE RISE");
        any = 1;
    }
    int prevo = species_prevo(sp);
    if (prevo >= 0) {
        str_copy(buf, "Grows from ");
        str_put(buf, SPECIES[prevo].name);
        pl_add(PL_TEXT, buf);
        any = 1;
    }
    if (!any) pl_add(PL_TEXT, "Unknown");
}

static void dex_build_content(int sp)
{
    const Species *s = &SPECIES[sp];
    char buf[40];
    dex.content_lines = 0;

    int own = species_ownership(sp);
    static const char *const OWN_TEXT[4] = {
        "NOT BEFRIENDED YET", "BEFRIENDED BEFORE", "ON THE LANTERN SHELF", "IN YOUR TEAM",
    };
    pl_add(own >= OWN_IN_PC ? PL_GOOD : own == OWN_CAUGHT_BEFORE ? PL_TEXT : PL_BAD, OWN_TEXT[own]);
    pl_add(PL_TEXT, dex_seen[sp] ? "Met in the wild: YES" : "Met in the wild: NO");
    pl_add(PL_BLANK, 0);

    pl_add(PL_HEADER, "DESCRIPTION");
    pl_add_wrapped(s->desc, PL_TEXT);
    pl_add(PL_BLANK, 0);

    pl_add(PL_HEADER, "BASE STATS");
    for (int i = 0; i < BS_COUNT; i++) {
        PanelLine *l = pl_add(PL_STAT, BASE_STAT_NAMES[i]);
        l->b = s->base[i];
    }
    str_copy(buf, "TOTAL ");
    str_put_int(buf, species_base_stat_total(sp));
    pl_add(PL_TEXT, buf);
    str_copy(buf, "BEFRIEND RATE ");
    str_put_int(buf, s->catch_rate);
    pl_add(PL_TEXT, buf);
    pl_add(PL_BLANK, 0);

    pl_add(PL_HEADER, "GROWTH");
    int cur = species_chain_root(sp);
    pl_add(cur == sp ? PL_GOOD : PL_TEXT, SPECIES[cur].name);
    for (int guard = 0; guard < 3 && SPECIES[cur].evo_kind != EVO_NONE; guard++) {
        const Species *c = &SPECIES[cur];
        buf[0] = 0;
        if (c->evo_kind == EVO_LEVEL) {
            str_put(buf, " Lv");
            str_put_int(buf, c->evo_param);
            str_put(buf, " > ");
        } else {
            /* shard names are long: they get a line of their own */
            str_copy(buf, "  touch a ");
            str_put(buf, ITEMS[c->evo_param].name);
            pl_add(PL_TEXT, buf);
            str_copy(buf, " > ");
        }
        str_put(buf, SPECIES[c->evo_into].name);
        cur = c->evo_into;
        pl_add(cur == sp ? PL_GOOD : PL_TEXT, buf);
    }
    if (SPECIES[species_chain_root(sp)].evo_kind == EVO_NONE)
        pl_add(PL_TEXT, "Does not grow");
    pl_add(PL_BLANK, 0);

    pl_add(PL_HEADER, "LEVEL-UP MOVES");
    for (const LearnEntry *e = s->learnset; e->level; e++) {
        PanelLine *l = pl_add(PL_MOVE, MOVES[e->move].name);
        l->a = e->level;
        l->b = MOVES[e->move].type;
    }
    pl_add(PL_BLANK, 0);

    pl_add(PL_HEADER, "HABITAT");
    dex_habitat(sp);
    pl_add(PL_BLANK, 0);
}

/* ---------------- panel ring ---------------- */

static void panel_render_line(int line)
{
    int slot = line & 7;
    target_set(panel_strip, panel_cols, 2);
    fill32(panel_strip, 0x11111111u, panel_cols * 2 * 8);
    if (line < dex.content_lines) {
        const PanelLine *l = &dex.lines[line];
        char buf[16];
        switch (l->kind) {
        case PL_HEADER:
            text_draw_col(2, 1, l->text, INK_BLUE, INK_BLUE_SH);
            canvas_fill(2, 14, panel_cols * 8 - 12, 1, 6);
            break;
        case PL_GOOD:
            text_draw_col(2, 1, l->text, INK_GREEN, INK_GREEN_SH);
            break;
        case PL_BAD:
            text_draw_col(2, 1, l->text, INK_RED, INK_RED_SH);
            break;
        case PL_TEXT:
            text_draw(2, 1, l->text);
            break;
        case PL_STAT: {
            text_draw(2, 1, l->text);
            buf[0] = 0;
            str_put_int(buf, l->b);
            text_draw_right(80, 1, buf);
            int w = l->b * 52 / 130;
            if (w > 52) w = 52;
            int col = l->b < 50 ? 8 : l->b < 80 ? 10 : 12;
            canvas_fill(84, 6, 54, 5, 4);
            canvas_fill(85, 7, w, 3, col);
            break;
        }
        case PL_MOVE:
            str_copy(buf, "Lv");
            str_put_int(buf, l->a);
            text_draw(2, 1, buf);
            text_draw(34, 1, l->text);
            break;
        default:
            break;
        }
    }
    target_canvas();
    copy32(VRAM_UI_TILES + (PANEL_TILE_BASE + slot * panel_cols * 2) * 8, panel_strip,
           (unsigned)panel_cols * 2 * 8);
    dex.ring_line[slot] = line;
}

static void panel_setup_map(void)
{
    u16 *map = VRAM_MAP(SB_PANEL);
    fill32(VRAM_UI_TILES + PANEL_BLANK_TILE * 8, 0, 8);
    for (int i = 0; i < 32 * 32; i++) map[i] = PANEL_BLANK_TILE;
    for (int row = 0; row < 32; row++) {
        int r = row & 15;
        for (int c = 0; c < panel_cols; c++)
            map[row * 32 + panel_x / 8 + c] = (u16)((PANEL_TILE_BASE + (r >> 1) * panel_cols * 2 +
                                                     (r & 1) * panel_cols + c) | (BANK_UI_STD << 12));
    }
    for (int i = 0; i < 8; i++) dex.ring_line[i] = -1;
}

static int panel_max_scroll(void)
{
    int h = dex.content_lines * LINE_H - PANEL_H;
    return h > 0 ? h : 0;
}

static void panel_draw_scrollbar(void)
{
    canvas_fill(226, PANEL_Y, 6, PANEL_H, 0);
    int max = panel_max_scroll();
    if (!max) return;
    canvas_fill(228, PANEL_Y + 2, 2, PANEL_H - 4, 6);
    int thumb = (PANEL_H - 4) * PANEL_H / (dex.content_lines * LINE_H);
    if (thumb < 8) thumb = 8;
    int ty = PANEL_Y + 2 + (PANEL_H - 4 - thumb) * dex.scroll_px / max;
    canvas_fill(227, ty, 4, thumb, 4);
}

/* Render lines entering view and position BG2; runs in vblank. */
static void panel_present(void)
{
    int first = dex.scroll_px / LINE_H, last = (dex.scroll_px + PANEL_H - 1) / LINE_H;
    for (int l = first; l <= last; l++)
        if (dex.ring_line[l & 7] != l) panel_render_line(l);
    REG_BG2HOFS = 0;
    REG_BG2VOFS = (u16)(dex.scroll_px - PANEL_Y);
}

/* The Lorebook reader uses the panel at (almost) full width. */
static void panel_wide(int on)
{
    panel_cols = on ? PANEL_COLS_MAX : 18;
    panel_x = on ? 16 : 88;
}

/* The panel sits in front of the UI canvas (whose window stays white
 * underneath), so a line that is still being rendered shows as blank paper
 * rather than a hole down to the backdrop. */
static void panel_enable(int on)
{
    REG_BG1CNT = BGCNT_CHARBLOCK(1) | BGCNT_SCREENBLOCK(SB_UI) | BGCNT_PRIO(on ? 1 : 0);
    if (on) {
        REG_BG2CNT = BGCNT_CHARBLOCK(1) | BGCNT_SCREENBLOCK(SB_PANEL) | BGCNT_PRIO(0);
        /* the scrollbar column (x 226..231) stays on the canvas */
        int right = panel_x + panel_cols * 8 > 226 ? 226 : panel_x + panel_cols * 8;
        REG_WIN0H = (u16)((panel_x << 8) | right);
        REG_WIN0V = (u16)((PANEL_Y << 8) | (PANEL_Y + PANEL_H));
        REG_WININ = 0x1F;
        REG_WINOUT = 0x1B;
        REG_DISPCNT = (u16)(REG_DISPCNT | DCNT_BG2 | DCNT_WIN0);
    } else {
        REG_DISPCNT = (u16)(REG_DISPCNT & ~(DCNT_BG2 | DCNT_WIN0));
    }
}

/* ---------------- screens ---------------- */

static void dex_list_redraw(void)
{
    char buf[40];
    screen_begin(1);
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    text_draw_col(16, 8, "ALMANAC", INK_RED, INK_RED_SH);
    str_copy(buf, "MET ");
    str_put_int(buf, dex_seen_count());
    str_put(buf, "  FRIENDS ");
    str_put_int(buf, dex_caught_count());
    text_draw_right(228, 8, buf);

    canvas_window(0, 3, 11, 11, WIN_STD);
    canvas_window(0, 14, 11, 6, WIN_STD);
    int sp = dex.cursor;
    draw_type_badge(1, 15, SPECIES[sp].type1);
    if (SPECIES[sp].type2 != TYPE_NONE) draw_type_badge(5, 15, SPECIES[sp].type2);
    text_draw_col(10, 135, "A: DETAILS", INK_BLUE, INK_BLUE_SH);

    canvas_window(11, 3, 19, 17, WIN_STD);
    for (int r = 0; r < DEX_ROWS && dex.scroll + r < SP_COUNT; r++) {
        int s = dex.scroll + r;
        int y = 32 + r * LINE_H;
        if (s == dex.cursor) {
            canvas_fill(96, y - 2, 128, 14, 7);
            text_draw(97, y - 2, "{");
        }
        canvas_tile(13, y / 8, dex_caught[s] ? ui_icon_caught : ui_icon_empty, s == dex.cursor ? 7 : 1);
        str_copy(buf, "No.");
        str_put_int3(buf, s + 1);
        text_draw(115, y - 2, buf);
        text_draw(160, y - 2, SPECIES[s].name);
    }
    if (dex.scroll > 0) text_draw_col(214, 22, "^", INK_RED, INK_RED_SH);
    if (dex.scroll + DEX_ROWS < SP_COUNT) text_draw_col(214, 144, "}", INK_RED, INK_RED_SH);
    load_monster_gfx(0, sp, 0);
}

static void dex_detail_redraw(void)
{
    int sp = dex.cursor;
    const Species *s = &SPECIES[sp];
    char buf[40];
    screen_begin(1);
    canvas_window(0, 0, CANVAS_COLS, 4, WIN_STD);
    str_copy(buf, "No.");
    str_put_int3(buf, sp + 1);
    text_draw(12, 9, buf);
    text_draw(60, 9, s->name);
    draw_type_badge(21, 1, s->type1);
    if (s->type2 != TYPE_NONE) draw_type_badge(25, 1, s->type2);

    canvas_window(0, 4, 10, 10, WIN_STD);
    canvas_window(0, 14, 10, 6, WIN_STD);
    text_draw_fit(8, 120, s->category, 64);
    str_copy(buf, "");
    str_put_int(buf, s->height_dm / 10);
    str_put(buf, ".");
    str_put_int(buf, s->height_dm % 10);
    str_put(buf, "m ");
    str_put_int(buf, s->weight_hg / 10);
    str_put(buf, ".");
    str_put_int(buf, s->weight_hg % 10);
    str_put(buf, "kg");
    text_draw(8, 136, buf);

    canvas_window(10, 4, 20, 16, WIN_STD);

    dex_build_content(sp);
    dex.scroll_px = dex.target_px = 0;
    panel_setup_map();
    panel_draw_scrollbar();
    panel_enable(1); /* screen_begin() switched the panel layer off */
    load_monster_gfx(0, sp, dex.back);
}

static void dex_open(void)
{
    game_mode = MODE_DEX;
    dex.state = 0;
    if (dex.cursor < 0 || dex.cursor >= SP_COUNT) dex.cursor = 0;
    dex_list_redraw();
}

static void dex_update(void)
{
    if (dex.state == 0) {
        int old = dex.cursor;
        if (key_rep(KEY_UP) && dex.cursor > 0) dex.cursor--;
        if (key_rep(KEY_DOWN) && dex.cursor < SP_COUNT - 1) dex.cursor++;
        if (key_rep(KEY_LEFT) || key_rep(KEY_L)) dex.cursor = clampi(dex.cursor - DEX_ROWS, 0, SP_COUNT - 1);
        if (key_rep(KEY_RIGHT) || key_rep(KEY_R)) dex.cursor = clampi(dex.cursor + DEX_ROWS, 0, SP_COUNT - 1);
        if (dex.cursor < dex.scroll) dex.scroll = dex.cursor;
        if (dex.cursor >= dex.scroll + DEX_ROWS) dex.scroll = dex.cursor - DEX_ROWS + 1;
        if (old != dex.cursor) dex_list_redraw();
        if (key_hit(KEY_B)) {
            canvas_clear();
            start_menu_open();
        } else if (key_hit(KEY_A)) {
            dex.state = 1;
            dex.back = 0;
            dex_detail_redraw();
        }
        return;
    }
    int max = panel_max_scroll();
    if (key_down(KEY_DOWN)) dex.target_px = clampi(dex.target_px + 3, 0, max);
    if (key_down(KEY_UP)) dex.target_px = clampi(dex.target_px - 3, 0, max);
    if (key_hit(KEY_R)) dex.target_px = clampi(dex.target_px + PANEL_H, 0, max);
    if (key_hit(KEY_L)) dex.target_px = clampi(dex.target_px - PANEL_H, 0, max);
    if (dex.scroll_px != dex.target_px) {
        int d = dex.target_px - dex.scroll_px;
        int step = absi(d) > 24 ? absi(d) / 4 : absi(d) > 3 ? 3 : absi(d);
        dex.scroll_px += d > 0 ? step : -step;
        panel_draw_scrollbar();
    }
    int change = 0;
    if (key_rep(KEY_LEFT)) change = -1;
    if (key_rep(KEY_RIGHT)) change = 1;
    if (change) {
        dex.cursor = (dex.cursor + change + SP_COUNT) % SP_COUNT;
        if (dex.cursor < dex.scroll) dex.scroll = dex.cursor;
        if (dex.cursor >= dex.scroll + DEX_ROWS) dex.scroll = dex.cursor - DEX_ROWS + 1;
        dex_detail_redraw();
    }
    if (key_hit(KEY_A)) {
        dex.back ^= 1;
        load_monster_gfx(0, dex.cursor, dex.back);
    }
    if (key_hit(KEY_B)) {
        panel_enable(0);
        dex.state = 0;
        dex_list_redraw();
    }
}

static void dex_draw(void)
{
    if (dex.state == 0) spr_push(12, 36, OT_MON_A, SQ64, OBANK_MON_A, 0, 0);
    else spr_push(8, 40, OT_MON_A, SQ64, OBANK_MON_A, 0, 0);
}
