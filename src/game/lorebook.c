/*
 * LOREBOOK: the knowledge base. Every entry in lore.h is revealed by one
 * source in the world (a person, a sign, a bookshelf or a story moment)
 * and kept here to be re-read at any time, sorted into chapters.
 *
 *   chapters  ->  entries of a chapter (unread ones marked NEW)  ->  reader
 *
 * The reader is the Almanac's smooth-scrolling BG2 panel (dex.c) set to
 * the full screen width.
 */

#define LORE_BYTES ((LORE_COUNT + 7) / 8)
static u8 lore_known[LORE_BYTES];
static u8 lore_unread[LORE_BYTES];

static int lore_is_known(int i) { return (lore_known[i >> 3] >> (i & 7)) & 1; }
static int lore_is_unread(int i) { return (lore_unread[i >> 3] >> (i & 7)) & 1; }

/* Returns 1 if the entry was new. */
static int lore_learn(int i)
{
    if (i < 0 || i >= LORE_COUNT || lore_is_known(i)) return 0;
    lore_known[i >> 3] |= (u8)(1u << (i & 7));
    lore_unread[i >> 3] |= (u8)(1u << (i & 7));
    return 1;
}

static void lore_reset(void)
{
    for (int i = 0; i < LORE_BYTES; i++) lore_known[i] = lore_unread[i] = 0;
    for (int i = 0; i < LORE_COUNT; i++)
        if (LORE[i].source == LSRC_START) lore_learn(i);
    for (int i = 0; i < LORE_BYTES; i++) lore_unread[i] = 0;
}

static int lore_known_count(void)
{
    int n = 0;
    for (int i = 0; i < LORE_COUNT; i++) n += lore_is_known(i);
    return n;
}

static int lore_unread_count(void)
{
    int n = 0;
    for (int i = 0; i < LORE_COUNT; i++) n += lore_is_unread(i);
    return n;
}

/* Next entry a source still has to tell, or -1. */
static int lore_next_from(int src)
{
    for (int i = 0; i < LORE_COUNT; i++)
        if (LORE[i].source == src && !lore_is_known(i)) return i;
    return -1;
}

static void lore_announce(int id)
{
    char msg[64];
    if (!lore_learn(id)) return;
    sfx_play(SFX_LORE);
    str_copy(msg, "LOREBOOK: ");
    str_put(msg, LORE[id].title);
    str_put(msg, " added.");
    dlg_say(msg);
}

/* Queue an entry as a story moment (no talk; just the notice). */
static void lore_story(int id)
{
    if (id >= 0 && id < LORE_COUNT && !lore_is_known(id)) dlg_call(lore_announce, id);
}

/*
 * A person/sign/book with lore: tells the next entry they know and adds it
 * to the Lorebook. Returns 1 if something was told; otherwise says `idle`
 * (if given) and returns 0.
 */
static int lore_reveal(int src, const char *idle)
{
    int id = src == NO_LORE ? -1 : lore_next_from(src);
    if (id < 0) {
        if (idle) dlg_say(idle);
        return 0;
    }
    if (LORE[id].talk) dlg_say(LORE[id].talk);
    dlg_call(lore_announce, id);
    return 1;
}

/* ---------------- screens ---------------- */

static struct {
    int state;          /* 0 chapters, 1 entries, 2 reader */
    int chapter, cursor, scroll;
    int ids[40];
    int count;
    int entry;
    int from_field;     /* opened with SELECT: B goes straight back to the field */
} lb;

#define LB_ROWS 7

static void start_menu_open(void);

static int lore_chapter_known(int ch, int *total)
{
    int n = 0, t = 0;
    for (int i = 0; i < LORE_COUNT; i++)
        if (LORE[i].chapter == ch) {
            t++;
            n += lore_is_known(i);
        }
    if (total) *total = t;
    return n;
}

static int lore_chapter_unread(int ch)
{
    for (int i = 0; i < LORE_COUNT; i++)
        if (LORE[i].chapter == ch && lore_is_unread(i)) return 1;
    return 0;
}

static void lb_header(const char *title)
{
    char buf[32];
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    text_draw_col(16, 8, title, INK_BLUE, INK_BLUE_SH);
    buf[0] = 0;
    str_put_int(buf, lore_known_count());
    str_put(buf, "/");
    str_put_int(buf, LORE_COUNT);
    str_put(buf, " PAGES");
    text_draw_right(228, 8, buf);
}

static void lb_chapters_redraw(void)
{
    char buf[16];
    screen_begin(1);
    lb_header("LOREBOOK");
    canvas_window(0, 3, CANVAS_COLS, 17, WIN_STD);
    for (int c = 0; c < LORE_CHAPTER_COUNT; c++) {
        int y = 30 + c * 14, total;
        int known = lore_chapter_known(c, &total);
        if (c == lb.chapter) {
            canvas_fill(14, y - 2, 212, 14, 7);
            text_draw(15, y - 2, "{");
        }
        if (known) text_draw(26, y - 2, LORE_CHAPTER_NAMES[c]);
        else text_draw_col(26, y - 2, LORE_CHAPTER_NAMES[c], INK_SHADOW, INK_SHADOW);
        if (lore_chapter_unread(c)) small_text_draw(140, y + 1, "NEW");
        buf[0] = 0;
        str_put_int(buf, known);
        str_put(buf, "/");
        str_put_int(buf, total);
        text_draw_right(224, y - 2, buf);
    }
}

static void lb_collect(void)
{
    lb.count = 0;
    for (int i = 0; i < LORE_COUNT && lb.count < 40; i++)
        if (LORE[i].chapter == lb.chapter) lb.ids[lb.count++] = i;
}

static void lb_entries_redraw(void)
{
    screen_begin(1);
    lb_header(LORE_CHAPTER_NAMES[lb.chapter]);
    canvas_window(0, 3, CANVAS_COLS, 17, WIN_STD);
    for (int r = 0; r < LB_ROWS + 2 && lb.scroll + r < lb.count; r++) {
        int k = lb.scroll + r, id = lb.ids[k];
        int y = 30 + r * 14;
        if (k == lb.cursor) {
            canvas_fill(14, y - 2, 212, 14, 7);
            text_draw(15, y - 2, "{");
        }
        if (lore_is_known(id)) {
            text_draw(26, y - 2, LORE[id].title);
            if (lore_is_unread(id)) small_text_draw(196, y + 1, "NEW");
        } else {
            text_draw_col(26, y - 2, "- - - - -", INK_SHADOW, INK_SHADOW);
        }
    }
    if (lb.scroll > 0) text_draw_col(214, 22, "^", INK_RED, INK_RED_SH);
    if (lb.scroll + LB_ROWS + 2 < lb.count) text_draw_col(214, 144, "}", INK_RED, INK_RED_SH);
}

/* Fill the panel with an entry: title, then wrapped paragraphs. */
static void lb_build_page(int id)
{
    dex.content_lines = 0;
    pl_add(PL_HEADER, LORE[id].title);
    pl_add(PL_BLANK, 0);
    const char *p = LORE[id].text;
    char para[400];
    while (*p) {
        int n = 0;
        /* one paragraph (up to a blank line), chunked to fit the wrapper */
        while (*p && !(p[0] == '\n' && p[1] == '\n') && n < 380) {
            para[n++] = *p == '\n' ? ' ' : *p;
            p++;
        }
        /* don't split a word when a long paragraph is chunked */
        if (n >= 380) {
            while (n > 0 && para[n - 1] != ' ') {
                n--;
                p--;
            }
        }
        para[n] = 0;
        if (n) pl_add_wrapped(para, PL_TEXT);
        if (p[0] == '\n' && p[1] == '\n') {
            pl_add(PL_BLANK, 0);
            p += 2;
        }
    }
}

static void lb_reader_redraw(void)
{
    int id = lb.ids[lb.entry];
    char buf[24];
    screen_begin(1);
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    text_draw_col(16, 8, LORE_CHAPTER_NAMES[lb.chapter], INK_BLUE, INK_BLUE_SH);
    buf[0] = 0;
    str_put_int(buf, lb.entry + 1);
    str_put(buf, "/");
    str_put_int(buf, lb.count);
    text_draw_right(228, 8, buf);
    canvas_window(0, 3, CANVAS_COLS, 17, WIN_STD);
    lore_unread[id >> 3] &= (u8)~(1u << (id & 7));
    panel_wide(1);
    lb_build_page(id);
    dex.scroll_px = dex.target_px = 0;
    panel_setup_map();
    panel_draw_scrollbar();
    panel_enable(1); /* screen_begin() switched the panel layer off */
}

static void lorebook_open(void)
{
    lb.from_field = game_mode == MODE_FIELD;
    game_mode = MODE_LORE;
    lb.state = 0;
    if (lb.chapter < 0 || lb.chapter >= LORE_CHAPTER_COUNT) lb.chapter = 0;
    lb_chapters_redraw();
}

static void lb_leave_reader(void)
{
    panel_enable(0);
    panel_wide(0);
    lb.state = 1;
    lb_entries_redraw();
}

/* Next known entry in the chapter from `from` in direction `d`, or -1. */
static int lb_step_known(int from, int d)
{
    for (int k = from + d; k >= 0 && k < lb.count; k += d)
        if (lore_is_known(lb.ids[k])) return k;
    return -1;
}

static void lorebook_update(void)
{
    switch (lb.state) {
    case 0: {
        int old = lb.chapter;
        if (key_rep(KEY_UP)) lb.chapter = (lb.chapter + LORE_CHAPTER_COUNT - 1) % LORE_CHAPTER_COUNT;
        if (key_rep(KEY_DOWN)) lb.chapter = (lb.chapter + 1) % LORE_CHAPTER_COUNT;
        if (old != lb.chapter) {
            sfx_play(SFX_CURSOR);
            lb_chapters_redraw();
        }
        if (key_hit(KEY_B)) {
            sfx_play(SFX_CANCEL);
            canvas_clear();
            if (lb.from_field) {
                field_setup_bg();
                game_mode = MODE_FIELD;
            } else {
                start_menu_open();
            }
        } else if (key_hit(KEY_A)) {
            if (!lore_chapter_known(lb.chapter, 0)) {
                sfx_play(SFX_ERROR);
                return;
            }
            sfx_play(SFX_CONFIRM);
            lb_collect();
            lb.state = 1;
            lb.cursor = lb_step_known(-1, 1);
            if (lb.cursor < 0) lb.cursor = 0;
            lb.scroll = clampi(lb.cursor - LB_ROWS + 1, 0, lb.count);
            lb_entries_redraw();
        }
        return;
    }
    case 1: {
        int old = lb.cursor;
        if (key_rep(KEY_UP) && lb.cursor > 0) lb.cursor--;
        if (key_rep(KEY_DOWN) && lb.cursor < lb.count - 1) lb.cursor++;
        if (key_rep(KEY_L)) lb.cursor = clampi(lb.cursor - (LB_ROWS + 2), 0, lb.count - 1);
        if (key_rep(KEY_R)) lb.cursor = clampi(lb.cursor + (LB_ROWS + 2), 0, lb.count - 1);
        if (lb.cursor < lb.scroll) lb.scroll = lb.cursor;
        if (lb.cursor >= lb.scroll + LB_ROWS + 2) lb.scroll = lb.cursor - LB_ROWS - 1;
        if (old != lb.cursor) {
            sfx_play(SFX_CURSOR);
            lb_entries_redraw();
        }
        if (key_hit(KEY_B)) {
            sfx_play(SFX_CANCEL);
            lb.state = 0;
            lb_chapters_redraw();
        } else if (key_hit(KEY_A)) {
            if (!lore_is_known(lb.ids[lb.cursor])) {
                sfx_play(SFX_ERROR);
                return;
            }
            sfx_play(SFX_CONFIRM);
            lb.state = 2;
            lb.entry = lb.cursor;
            lb_reader_redraw();
        }
        return;
    }
    default: {
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
        int change = key_rep(KEY_LEFT) ? -1 : key_rep(KEY_RIGHT) ? 1 : 0;
        if (change) {
            int k = lb_step_known(lb.entry, change);
            if (k >= 0) {
                sfx_play(SFX_CURSOR);
                lb.entry = lb.cursor = k;
                if (lb.cursor < lb.scroll) lb.scroll = lb.cursor;
                if (lb.cursor >= lb.scroll + LB_ROWS + 2) lb.scroll = lb.cursor - LB_ROWS - 1;
                lb_reader_redraw();
            }
        }
        if (key_hit(KEY_B)) {
            sfx_play(SFX_CANCEL);
            lb_leave_reader();
        }
        return;
    }
    }
}
