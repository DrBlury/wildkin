/* Discovered underground connections. Included by travel.c beside the town
 * map; reads ROM metadata only, so opening the atlas never reloads the field. */
#define UW_PAGE_EXITS 4
static struct {
    u8 maps[MAP_COUNT];
    u16 exits[WARP_COUNT];
    u8 reverse[WARP_COUNT];
    int count, current, exit_count, page;
} uw;

static int underworld_known(int map)
{
    return map >= 0 && map < MAP_COUNT && MAPS[map].depth &&
           (map == cur_map || travel_visited_get(map));
}

static int underworld_has_exit_mat(int map)
{
    const MapDef *m = &MAPS[map];
    const TilesetDef *t = &TILESETS[m->tileset];
    if (!m->rows) return 0;
    for (int y = 0; y < m->h; y++)
        for (int x = 0; x < m->w; x++) {
            u16 cell = legend_pick(legend_for(t, m->rows[y][x]), x, y);
            if (cell < t->meta_count && (t->attr[cell] & A_EXIT)) return 1;
        }
    return 0;
}

static void underworld_collect_exits(void)
{
    uw.exit_count = 0;
    if (!uw.count) return;
    int map = uw.maps[uw.current];
    for (int i = 0; i < WARP_COUNT; i++)
        if (WARPS[i].map == map) {
            uw.exits[uw.exit_count] = (u16)i;
            uw.reverse[uw.exit_count++] = 0;
        }
    /* Old single-room caves use an exit mat instead of a reciprocal Warp. */
    if (underworld_has_exit_mat(map))
        for (int i = 0; i < WARP_COUNT; i++) {
            if (WARPS[i].dest != map) continue;
            int explicit_return = 0;
            for (int j = 0; j < WARP_COUNT; j++)
                if (WARPS[j].map == map && WARPS[j].dest == WARPS[i].map) explicit_return = 1;
            if (explicit_return) continue;
            uw.exits[uw.exit_count] = (u16)i;
            uw.reverse[uw.exit_count++] = 1;
        }
}

static void underworld_collect(void)
{
    uw.count = uw.current = uw.page = 0;
    for (int m = 0; m < MAP_COUNT; m++)
        if (underworld_known(m)) {
            if (m == cur_map) uw.current = uw.count;
            uw.maps[uw.count++] = (u8)m;
        }
    underworld_collect_exits();
}

static int underworld_exit_map(int index)
{
    const Warp *w = &WARPS[uw.exits[index]];
    return uw.reverse[index] ? w->map : w->dest;
}

static void underworld_draw(void)
{
    canvas_clear();
    canvas_window(0, 0, CANVAS_COLS, CANVAS_ROWS, WIN_STD);
    text_draw_col(12, 9, "UNDERGROUND ATLAS", INK_BLUE, INK_BLUE_SH);
    text_draw(12, 24, "L/R: SURFACE    B: BACK");
    if (!uw.count) {
        text_draw_center(120, 68, "NO CAVES CHARTED");
        text_draw_center(120, 89, "Explore a cave to chart it.");
        return;
    }
    int map = uw.maps[uw.current], anchor = MAPS[map].surface_map;
    if (map == cur_map) text_draw_right(228, 24, "HERE");
    char info[80];
    str_copy(info, "B"); str_put_int(info, MAPS[map].depth);
    str_put(info, "  "); str_put(info, MAPS[map].name);
    text_draw_fit(12, 39, info, 216);
    str_copy(info, "BENEATH ");
    str_put(info, anchor < MAP_COUNT ? MAPS[anchor].name : "THE VALE");
    text_draw(12, 53, info);
    int first = uw.page * UW_PAGE_EXITS;
    int n = uw.exit_count - first;
    if (n > UW_PAGE_EXITS) n = UW_PAGE_EXITS;
    if (!n) text_draw(48, 91, "NO CHARTED CONNECTIONS");
    /* Solid lines are open; broken lines and an X mark sealed passages. */
    canvas_fill(23, 73, 2, n > 1 ? (n - 1) * 14 + 2 : 2, INK_BLUE);
    for (int k = 0; k < n; k++) {
        int index = first + k, y = 73 + k * 14;
        const Warp *w = &WARPS[uw.exits[index]];
        int dest = underworld_exit_map(index), open = warp_is_open(w);
        int known = dest == cur_map || travel_visited_get(dest);
        if (open) canvas_fill(25, y, 23, 2, INK_BLUE);
        else for (int x = 25; x < 48; x += 5) canvas_fill(x, y, 3, 2, INK_RED);
        text_draw(49, y - 4, open ? (MAPS[dest].depth ? "CAVE" : "OUT") : "LOCK");
        str_copy(info, known ? MAPS[dest].name : "UNCHARTED PASSAGE");
        if (!open && !known) str_copy(info, warp_gate_name(w));
        text_draw_fit(82, y - 4, info, 144);
    }
    str_copy(info, "CAVE "); str_put_int(info, uw.current + 1);
    str_put(info, "/"); str_put_int(info, uw.count);
    str_put(info, "  EXITS "); str_put_int(info, uw.page + 1);
    int pages = (uw.exit_count + UW_PAGE_EXITS - 1) / UW_PAGE_EXITS;
    str_put(info, "/"); str_put_int(info, pages ? pages : 1);
    text_draw(12, 126, info);
    text_draw(12, 140, "UP/DN:CAVE  LEFT/RIGHT:EXITS");
}

static void underworld_update(void)
{
    int move = key_hit(KEY_DOWN) - key_hit(KEY_UP);
    int page = key_hit(KEY_RIGHT) - key_hit(KEY_LEFT);
    if (move && uw.count) {
        uw.current = (uw.current + move + uw.count) % uw.count;
        uw.page = 0;
        underworld_collect_exits();
    } else if (page && uw.exit_count > UW_PAGE_EXITS) {
        int pages = (uw.exit_count + UW_PAGE_EXITS - 1) / UW_PAGE_EXITS;
        uw.page = (uw.page + page + pages) % pages;
    } else return;
    sfx_play(SFX_CURSOR);
    underworld_draw();
}
