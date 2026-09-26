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
    int state, cursor, scroll, back;   /* cursor: species; scroll: list row */
    int pos;                           /* cursor's row in the filtered list */
    int frow;                          /* FILTER panel row */
    int scroll_px, target_px, content_lines;
    int ring_line[8];
    PanelLine lines[PANEL_MAX_LINES];
} dex EWRAM_BSS;

EWRAM_BSS static u32 panel_strip[PANEL_COLS_MAX * 2 * 8];

/* ---------------- filters ---------------- */

/* Regions of the Vale, by map id range (docs/EXPANSION.md 9). */
enum { REG_VALE, REG_EAST, REG_WEST, REG_NORTH, REG_ASHEN, REG_FAR, REG_FARM, REG_COUNT };
static const char *const REGION_NAMES[REG_COUNT] = {
    "THE VALE", "EAST", "THE COAST", "THE NORTH", "ASHEN MARCH", "FAR REACHES", "WILLOW ACRE",
};
enum { DF_ALL, DF_MET, DF_FRIENDS, DF_OWN_COUNT };
static const char *const DF_OWN_NAMES[DF_OWN_COUNT] = { "ALL", "MET", "FRIENDS" };

/* 0 = any; otherwise the TYPE / R_ / REG_ value + 1. */
static struct { u8 own, type, rarity, region; } dexf;

EWRAM_BSS static u8 dex_list[SP_COUNT];
static int dex_list_n;
static u8 dex_region_mask[SP_COUNT];
static int dex_regions_ready;

static int map_region(int map)
{
    if (map < 0 || map >= MAP_COUNT || (MAPS[map].flags & MF_DEBUG)) return -1;
    if (map >= MAP_WILLOW_ACRE) return REG_FARM;
    if (map >= MAP_CINDER_ROAD) return REG_FAR;
    if (map >= MAP_ASHEN_FIELDS) return REG_ASHEN;
    if (map >= MAP_FROSTPINE) return REG_NORTH;
    if (map >= MAP_SALTWIND) return REG_WEST;
    if (map >= MAP_COPPERLINE) return REG_EAST;
    return REG_VALE;
}

static void zone_mark_region(int zone, int reg)
{
    if (zone <= ZONE_NONE || zone >= ZONE_COUNT) return;
    const WildZone *z = &WILD_ZONES[zone];
    for (int i = 0; i < z->count; i++)
        if (z->slots[i].species < SP_COUNT) dex_region_mask[z->slots[i].species] |= (u8)(1u << reg);
}

/* Where each kin can be met: wild zones (land and water) and legend lairs. */
static void dex_regions_build(void)
{
    if (dex_regions_ready) return;
    for (int sp = 0; sp < SP_COUNT; sp++) dex_region_mask[sp] = 0;
    for (int m = 0; m < MAP_COUNT; m++) {
        int reg = map_region(m);
        if (reg < 0) continue;
        zone_mark_region(MAPS[m].zone, reg);
        zone_mark_region(MAPS[m].water_zone, reg);
        for (int i = 0; i < MAPS[m].obj_count; i++)
            if (MAPS[m].objs[i].kind == OBJ_LEGEND && MAPS[m].objs[i].arg < SP_COUNT)
                dex_region_mask[MAPS[m].objs[i].arg] |= (u8)(1u << reg);
    }
    for (int i = 0; i < 3; i++) dex_region_mask[STARTER_SPECIES[i]] |= 1u << REG_VALE;
    dex_region_mask[SP_DRAKORA] |= 1u << REG_VALE;
    /* kin that only grow out of another share its places */
    for (int pass = 0; pass < 3; pass++)
        for (int sp = 0; sp < SP_COUNT; sp++) {
            int p = species_prevo(sp);
            if (p >= 0) dex_region_mask[sp] |= dex_region_mask[p];
        }
    dex_regions_ready = 1;
}

static int dex_filter_active(void)
{
    return dexf.own || dexf.type || dexf.rarity || dexf.region;
}

static int dex_passes(int sp)
{
    const Species *s = &SPECIES[sp];
    if (dexf.own == DF_MET && !dex_seen[sp] && !dex_caught[sp]) return 0;
    if (dexf.own == DF_FRIENDS && !dex_caught[sp]) return 0;
    if (dexf.type && s->type1 != dexf.type - 1 && s->type2 != dexf.type - 1) return 0;
    if (dexf.rarity && s->rarity != dexf.rarity - 1) return 0;
    if (dexf.region) {
        dex_regions_build();
        if (!(dex_region_mask[sp] & (1u << (dexf.region - 1)))) return 0;
    }
    return 1;
}

/* Rebuilds the filtered list and keeps the cursor on the same kin if it
 * is still listed (otherwise on the first one). */
static void dex_build_list(void)
{
    dex_list_n = 0;
    dex.pos = 0;
    for (int sp = 0; sp < SP_COUNT; sp++)
        if (dex_passes(sp)) {
            if (sp == dex.cursor) dex.pos = dex_list_n;
            dex_list[dex_list_n++] = (u8)sp;
        }
    if (dex_list_n) dex.cursor = dex_list[dex.pos];
    if (dex.pos < dex.scroll) dex.scroll = dex.pos;
    if (dex.pos >= dex.scroll + DEX_ROWS) dex.scroll = dex.pos - DEX_ROWS + 1;
    if (dex.scroll > dex_list_n - DEX_ROWS) dex.scroll = dex_list_n > DEX_ROWS ? dex_list_n - DEX_ROWS : 0;
}

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
        int total = 0, w = 0, lo = 0, hi = 0, when = 0;
        for (int i = 0; i < zone->count; i++) {
            total += zone->slots[i].weight;
            if (zone->slots[i].species == sp) {
                w += zone->slots[i].weight;
                lo = zone->slots[i].min_level;
                hi = zone->slots[i].max_level;
                when |= 1 << zone->slots[i].when;
            }
        }
        if (!w) continue;
        pl_add(PL_TEXT, zone->name);
        str_copy(buf, "  Lv");
        str_put_int(buf, lo);
        str_put(buf, "-");
        str_put_int(buf, hi);
        str_put(buf, w * 100 / total >= 15 ? "  common" : w * 100 / total >= 8 ? "  uncommon" : "  rare");
        if (!(when & (1 << WHEN_ANY)) && when == (1 << WHEN_DAY)) str_put(buf, "  DAY");
        if (!(when & (1 << WHEN_ANY)) && when == (1 << WHEN_NIGHT)) str_put(buf, "  NIGHT");
        pl_add(PL_TEXT, buf);
        any = 1;
    }
    for (int m = 0; m < MAP_COUNT; m++) {
        if (MAPS[m].flags & MF_DEBUG) continue;
        for (int i = 0; i < MAPS[m].obj_count; i++)
            if (MAPS[m].objs[i].kind == OBJ_LEGEND && MAPS[m].objs[i].arg == sp) {
                pl_add(PL_GOOD, "LAIR");
                str_copy(buf, "  ");
                str_put(buf, MAPS[m].name);
                pl_add(PL_TEXT, buf);
                any = 1;
            }
    }
    if (SPECIES[sp].rarity == R_FUSION) {
        pl_add(PL_TEXT, "The FUSION LOOM");
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

    str_copy(buf, "RARITY: ");
    str_put(buf, RARITY_NAMES[s->rarity % RARITY_COUNT]);
    pl_add(PL_TEXT, buf);
    if (s->rarity == R_FUSION) {
        if (dex_seen[sp] || dex_caught[sp]) {
            pl_add(PL_TEXT, "Woven from the energy");
            buf[0] = 0;
            for (int i = 0; i < 2; i++) {
                if (s->fusion[i] >= TYPE_COUNT) continue;
                if (i && s->fusion[0] < TYPE_COUNT) str_put(buf, " + ");
                str_put(buf, TYPE_NAMES[s->fusion[i]]);
            }
            pl_add(PL_GOOD, buf);
        } else {
            pl_add(PL_TEXT, "Weave not known yet");
        }
    }
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
    if (dex_list_n) {
        draw_type_badge(1, 15, SPECIES[sp].type1);
        if (SPECIES[sp].type2 != TYPE_NONE) draw_type_badge(5, 15, SPECIES[sp].type2);
    }
    if (dex_filter_active()) {
        buf[0] = 0;
        str_put_int(buf, dex_list_n);
        str_put(buf, " SHOWN");
        text_draw_col(10, 136, buf, INK_GREEN, INK_GREEN_SH);
    } else {
        text_draw_col(10, 136, "START: FILTER", INK_BLUE, INK_BLUE_SH);
    }

    canvas_window(11, 3, 19, 17, WIN_STD);
    if (!dex_list_n) text_draw(100, 32, "No kin match.\nSTART: change\nthe filter.");
    for (int r = 0; r < DEX_ROWS && dex.scroll + r < dex_list_n; r++) {
        int s = dex_list[dex.scroll + r];
        int y = 32 + r * LINE_H;
        if (s == dex.cursor) {
            canvas_fill(96, y - 2, 128, 14, 7);
            text_draw(97, y - 2, "{");
        }
        canvas_tile(13, y / 8, dex_caught[s] ? ui_icon_caught : ui_icon_empty, s == dex.cursor ? 7 : 1);
        str_copy(buf, "No.");
        str_put_int3(buf, s + 1);
        text_draw(125, y - 2, buf);
        text_draw_fit(166, y - 2, SPECIES[s].name, 58);
    }
    if (dex.scroll > 0) text_draw_col(214, 22, "^", INK_RED, INK_RED_SH);
    if (dex.scroll + DEX_ROWS < dex_list_n) text_draw_col(214, 144, "}", INK_RED, INK_RED_SH);
    if (dex_list_n) load_monster_gfx(0, sp, 0);
    if (dex.state == 2) {
        static const char *const LABEL[4] = { "SHOW", "TYPE", "RARITY", "PLACE" };
        canvas_window(3, 4, 24, 14, WIN_STD);
        text_draw_col(40, 40, "FILTER THE ALMANAC", INK_BLUE, INK_BLUE_SH);
        for (int r = 0; r < 4; r++) {
            int y = 60 + r * 16;
            const char *v;
            switch (r) {
            case 0: v = DF_OWN_NAMES[dexf.own]; break;
            case 1: v = dexf.type ? TYPE_NAMES[dexf.type - 1] : "ANY"; break;
            case 2: v = dexf.rarity ? RARITY_NAMES[dexf.rarity - 1] : "ANY"; break;
            default: v = dexf.region ? REGION_NAMES[dexf.region - 1] : "ANY"; break;
            }
            if (r == dex.frow) {
                canvas_fill(36, y - 2, 172, 14, 7);
                text_draw(37, y - 2, "{");
            }
            text_draw(48, y - 2, LABEL[r]);
            text_draw_col(108, y - 2, "<", INK_BLUE, INK_BLUE_SH);
            text_draw_center(154, y - 2, v);
            text_draw_col(198, y - 2, ">", INK_BLUE, INK_BLUE_SH);
        }
        buf[0] = 0;
        str_put_int(buf, dex_list_n);
        str_put(buf, " KIN   A: DONE");
        text_draw_col(48, 124, buf, INK_SHADOW, INK_SHADOW);
    }
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
    gems_load();
    dex_build_list();
    dex_list_redraw();
}

/* Moves the list cursor to row `pos` of the filtered list. */
static void dex_goto(int pos)
{
    if (!dex_list_n) return;
    dex.pos = clampi(pos, 0, dex_list_n - 1);
    dex.cursor = dex_list[dex.pos];
    if (dex.pos < dex.scroll) dex.scroll = dex.pos;
    if (dex.pos >= dex.scroll + DEX_ROWS) dex.scroll = dex.pos - DEX_ROWS + 1;
}

static void dex_filter_update(void)
{
    int old_row = dex.frow, change = 0;
    if (key_rep(KEY_UP)) dex.frow = (dex.frow + 3) % 4;
    if (key_rep(KEY_DOWN)) dex.frow = (dex.frow + 1) % 4;
    if (key_rep(KEY_LEFT)) change = -1;
    if (key_rep(KEY_RIGHT)) change = 1;
    if (change) {
        switch (dex.frow) {
        case 0: dexf.own = (u8)((dexf.own + DF_OWN_COUNT + change) % DF_OWN_COUNT); break;
        case 1: dexf.type = (u8)((dexf.type + TYPE_COUNT + 1 + change) % (TYPE_COUNT + 1)); break;
        case 2: dexf.rarity = (u8)((dexf.rarity + RARITY_COUNT + 1 + change) % (RARITY_COUNT + 1)); break;
        default: dexf.region = (u8)((dexf.region + REG_COUNT + 1 + change) % (REG_COUNT + 1)); break;
        }
        dex_build_list();
    }
    if (old_row != dex.frow || change) {
        sfx_play(SFX_CURSOR);
        dex_list_redraw();
    }
    if (key_hit(KEY_A) || key_hit(KEY_B) || key_hit(KEY_START)) {
        sfx_play(SFX_CONFIRM);
        dex.state = 0;
        dex_list_redraw();
    }
}

static void dex_update(void)
{
    if (dex.state == 2) {
        dex_filter_update();
        return;
    }
    if (dex.state == 0) {
        int old = dex.cursor;
        if (key_rep(KEY_UP) && dex.pos > 0) dex_goto(dex.pos - 1);
        if (key_rep(KEY_DOWN)) dex_goto(dex.pos + 1);
        if (key_rep(KEY_LEFT) || key_rep(KEY_L)) dex_goto(dex.pos - DEX_ROWS);
        if (key_rep(KEY_RIGHT) || key_rep(KEY_R)) dex_goto(dex.pos + DEX_ROWS);
        if (old != dex.cursor) dex_list_redraw();
        if (key_hit(KEY_B)) {
            canvas_clear();
            start_menu_open();
        } else if (key_hit(KEY_START) || key_hit(KEY_SELECT)) {
            sfx_play(SFX_CONFIRM);
            dex.state = 2;
            dex.frow = 0;
            dex_list_redraw();
        } else if (key_hit(KEY_A) && dex_list_n) {
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
    if (change && dex_list_n) {
        dex_goto((dex.pos + change + dex_list_n) % dex_list_n);
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
    if (dex.state == 1) {
        spr_push(8, 40, OT_MON_A, SQ64, OBANK_MON_A, 0, 0);
        gem_push(60 + text_width(SPECIES[dex.cursor].name) + 4, 14, SPECIES[dex.cursor].rarity);
        return;
    }
    if (dex.state == 2) return;   /* the FILTER panel covers the list */
    if (dex_list_n) spr_push(12, 36, OT_MON_A, SQ64, OBANK_MON_A, 0, 0);
    /* rarity gems of the kin you have met */
    for (int r = 0; r < DEX_ROWS && dex.scroll + r < dex_list_n; r++) {
        int sp = dex_list[dex.scroll + r];
        if (dex_seen[sp] || dex_caught[sp]) gem_push(114, 32 + r * LINE_H + 1, SPECIES[sp].rarity);
    }
}
