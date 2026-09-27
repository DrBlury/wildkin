/*
 * NPC quests and the quest log (docs/EXPANSION.md 7.6). Owner: UI system;
 * regions add quest ids in world/<region>/ and advance them in scripts.
 */

#define QUEST_MAX 96
typedef char QuestsFit[QUEST_COUNT <= QUEST_MAX ? 1 : -1];

typedef struct {
    u8 stage[QUEST_MAX];     /* 0 = not started, 255 = done */
    u8 pad[16];
} QuestState;

static QuestState quest;

static void quest_reset(void)
{
    u8 *raw = (u8 *)&quest;
    for (unsigned i = 0; i < sizeof(quest); i++) raw[i] = 0;
}

static void quest_validate(void)
{
}

MAYBE_UNUSED static int quest_get(int q);
MAYBE_UNUSED static int quest_is(int q, int stage) { return quest_get(q) == stage; }
MAYBE_UNUSED static int quest_between(int q, int a, int b) { int st = quest_get(q); return st >= a && st <= b; }
MAYBE_UNUSED static void quest_advance_to(int q, int stage)
{
    if (q > 0 && q < QUEST_COUNT && stage > quest.stage[q] && quest.stage[q] != 255)
        quest.stage[q] = (u8)clampi(stage, 0, 255);
}

MAYBE_UNUSED static int quest_get(int q) { return q > 0 && q < QUEST_COUNT ? quest.stage[q] : 0; }
MAYBE_UNUSED static void quest_set(int q, int stage) { if (q > 0 && q < QUEST_COUNT) quest.stage[q] = (u8)stage; }
MAYBE_UNUSED static int quest_done(int q) { return quest_get(q) == 255; }

static int quest_marker_map(int q)
{
    int stage = quest_get(q);
    const QuestDef *def = &QUESTS[q];
    return stage > 0 && stage != 255 && def->stage_maps && stage < def->n_stages
        ? def->stage_maps[stage] : MAP_NONE;
}

/* ================================================================ */
/*  The quest log                                                   */
/* ================================================================ */

/*
 * Quests you have started, the ones still open first; A shows what to do
 * next (the QuestDef goal) on the Almanac's scrolling panel. The table is
 * read through a pointer so the tests can inject quests before any region
 * defines one.
 */

static const QuestDef *quest_defs = QUESTS;
static int quest_def_count = QUEST_COUNT;

#define QLOG_ROWS 7

static struct {
    int state;               /* 0 list, 1 details, 2 field notes */
    int cursor, scroll;
    int ids[QUEST_MAX], count, open;
    int back_mode;           /* MODE_START_MENU or MODE_FIELD */
    int note_ability, note_scroll;
} qlog;

static int quest_stage_of(int q)
{
    return q > 0 && q < quest_def_count && q < QUEST_MAX ? quest.stage[q] : 0;
}

static void qlog_collect(void)
{
    qlog.count = qlog.open = 0;
    for (int pass = 0; pass < 2 * QUEST_CATEGORY_COUNT; pass++)
        for (int q = 1; q < quest_def_count && q < QUEST_MAX; q++) {
            int st = quest_stage_of(q);
            if (!st || (st == 255) != (pass >= QUEST_CATEGORY_COUNT) ||
                quest_defs[q].category != pass % QUEST_CATEGORY_COUNT) continue;
            qlog.ids[qlog.count++] = q;
            if (pass < QUEST_CATEGORY_COUNT) qlog.open++;
        }
    if (qlog.cursor >= qlog.count) qlog.cursor = qlog.count ? qlog.count - 1 : 0;
    if (qlog.cursor < qlog.scroll) qlog.scroll = qlog.cursor;
    if (qlog.cursor >= qlog.scroll + QLOG_ROWS) qlog.scroll = qlog.cursor - QLOG_ROWS + 1;
}

static void qlog_header(void)
{
    char buf[32];
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    text_draw_col(16, 8, "QUEST LOG", INK_BLUE, INK_BLUE_SH);
    buf[0] = 0;
    str_put_int(buf, qlog.open);
    str_put(buf, " OPEN  ");
    str_put_int(buf, qlog.count - qlog.open);
    str_put(buf, " DONE");
    text_draw_right(228, 8, buf);
    if (qlog.count) {
        static const char *const CATEGORIES[] = { "SIDE", "MAIN", "PROJECT", "EVENT" };
        int cat = quest_defs[qlog.ids[qlog.cursor]].category;
        text_draw_col(16, 20, CATEGORIES[cat < QUEST_CATEGORY_COUNT ? cat : QUEST_SIDE], INK_BLUE, INK_BLUE_SH);
    }
}

static void qlog_list_redraw(void)
{
    screen_begin(1);
    qlog_collect();
    qlog_header();
    canvas_window(0, 3, CANVAS_COLS, 17, WIN_STD);
    text_draw_col(16, 150, "SELECT: FIELD NOTES", INK_BLUE, INK_BLUE_SH);
    if (!qlog.count) {
        text_draw(24, 36, "No quests yet.");
        text_draw_col(24, 60, "People around the Vale may\nask for your help.", INK_SHADOW, INK_SHADOW);
        return;
    }
    for (int r = 0; r < QLOG_ROWS && qlog.scroll + r < qlog.count; r++) {
        int k = qlog.scroll + r, q = qlog.ids[k];
        int y = 30 + r * 16;
        if (k == qlog.cursor) {
            canvas_glow(14, y - 2, 212, 14);
            text_draw(15, y - 2, "{");
        }
        if (quest_stage_of(q) == 255) {
            text_draw_col(26, y - 2, quest_defs[q].name, INK_SHADOW, INK_SHADOW);
            text_draw_col(188, y - 2, "DONE", INK_GREEN, INK_GREEN_SH);
        } else {
            text_draw(26, y - 2, quest_defs[q].name);
            text_draw_col(188, y - 2, "OPEN", INK_RED, INK_RED_SH);
        }
    }
    if (qlog.scroll > 0) text_draw_col(214, 22, "^", INK_BLUE, INK_BLUE_SH);
    if (qlog.scroll + QLOG_ROWS < qlog.count) text_draw_col(214, 144, "}", INK_BLUE, INK_BLUE_SH);
}

static void qlog_detail_redraw(void)
{
    int q = qlog.ids[qlog.cursor];
    screen_begin(1);
    qlog_header();
    canvas_window(0, 3, CANVAS_COLS, 17, WIN_STD);
    panel_wide(1);
    dex.content_lines = 0;
    pl_add(PL_HEADER, quest_defs[q].name);
    pl_add(quest_stage_of(q) == 255 ? PL_GOOD : PL_BAD, quest_stage_of(q) == 255 ? "DONE" : "IN PROGRESS");
    pl_add(PL_BLANK, 0);
    int stage = quest_stage_of(q);
    const QuestDef *def = &quest_defs[q];
    const char *goal = def->goal;
    if (stage != 255 && def->stage_goals && stage < def->n_stages && def->stage_goals[stage])
        goal = def->stage_goals[stage];
    pl_add_wrapped(goal, PL_TEXT);
    dex.scroll_px = dex.target_px = 0;
    panel_setup_map();
    panel_draw_scrollbar();
    panel_enable(1);
}

/* FIELD NOTES is a separate log page, not another quest stage. Only observed
 * locations appear; switching ability tabs keeps the selected group readable. */
static int qlog_note_count(int ability)
{
    int count = 0;
    for (int i = 0; i < NOTE_COUNT; i++)
        if (saga_note_ability(i) == ability && saga_note_bit(i, 0)) count++;
    return count;
}

static const char *qlog_note_status(int i)
{
    return saga_note_bit(i, 3) ? "DONE" :
        saga_note_ready(saga_note_ability(i)) ? "READY" : "LOCKED";
}

static void qlog_notes_redraw(void)
{
    static const char *const abilities[] = {
        "LIGHT", "SURF", "STRENGTH", "FLY", "WARD", "TELEPORT"
    };
    int ability = qlog.note_ability, count = qlog_note_count(ability), row = 0;
    char label[72];
    screen_begin(1);
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    text_draw_col(16, 8, "FIELD NOTES", INK_BLUE, INK_BLUE_SH);
    text_draw_right(228, 8, "B:QUESTS");
    canvas_window(0, 3, CANVAS_COLS, 17, WIN_STD);
    text_draw_col(16, 20, abilities[ability], INK_BLUE, INK_BLUE_SH);
    text_draw_right(228, 20, "<  >");
    if (!count) text_draw_col(24, 48, "No places recorded yet.", INK_SHADOW, INK_SHADOW);
    for (int i = 0; i < NOTE_COUNT; i++) {
        int map = saga_note_map(i);
        if (saga_note_ability(i) != ability || !saga_note_bit(i, 0)) continue;
        if (row++ < qlog.note_scroll || row > qlog.note_scroll + QLOG_ROWS) continue;
        int y = 36 + (row - qlog.note_scroll - 1) * 16;
        str_copy(label, MAPS[map].name);
        if (str_len(label) > 18) label[18] = 0; /* leave room for coordinates and status */
        str_put(label, " ("); str_put_int(label, saga_note_x(i));
        str_put(label, ","); str_put_int(label, saga_note_y(i)); str_put(label, ")");
        text_draw(16, y, label);
        text_draw_col(186, y, qlog_note_status(i),
                      saga_note_bit(i, 3) ? INK_GREEN : INK_BLUE,
                      saga_note_bit(i, 3) ? INK_GREEN_SH : INK_BLUE_SH);
    }
    if (qlog.note_scroll) text_draw_col(214, 22, "^", INK_BLUE, INK_BLUE_SH);
    if (qlog.note_scroll + QLOG_ROWS < count) text_draw_col(214, 144, "}", INK_BLUE, INK_BLUE_SH);
}

static void qlog_notes_open(void)
{
    qlog.state = 2;
    qlog.note_ability = qlog.note_scroll = 0;
    panel_enable(0);
    panel_wide(0);
    qlog_notes_redraw();
}

static void qlog_present(void)
{
    if (qlog.state == 1) panel_present();
}

static void qlog_close(void)
{
    sfx_play(SFX_CANCEL);
    panel_enable(0);
    panel_wide(0);
    canvas_clear();
    if (qlog.back_mode == MODE_START_MENU) {
        start_menu_open();
        return;
    }
    field_setup_bg();
    game_mode = MODE_FIELD;
}

static void qlog_update(void)
{
    if (qlog.state == 2) {
        if (key_hit(KEY_B) || key_hit(KEY_SELECT)) {
            sfx_play(SFX_CANCEL);
            qlog.state = 0;
            qlog_list_redraw();
        } else if (key_hit(KEY_LEFT) || key_hit(KEY_RIGHT)) {
            int direction = key_hit(KEY_RIGHT) ? 1 : -1;
            qlog.note_ability = (qlog.note_ability + SAGA_TELEPORT + 1 + direction) % (SAGA_TELEPORT + 1);
            qlog.note_scroll = 0;
            sfx_play(SFX_CURSOR);
            qlog_notes_redraw();
        } else {
            int old = qlog.note_scroll;
            if (key_rep(KEY_DOWN) && qlog.note_scroll + QLOG_ROWS < qlog_note_count(qlog.note_ability)) qlog.note_scroll++;
            if (key_rep(KEY_UP) && qlog.note_scroll) qlog.note_scroll--;
            if (old != qlog.note_scroll) { sfx_play(SFX_CURSOR); qlog_notes_redraw(); }
        }
        return;
    }
    if (qlog.state == 1) {
        int max = panel_max_scroll();
        if (key_down(KEY_DOWN)) dex.target_px = clampi(dex.target_px + 3, 0, max);
        if (key_down(KEY_UP)) dex.target_px = clampi(dex.target_px - 3, 0, max);
        if (dex.scroll_px != dex.target_px) {
            int d = dex.target_px - dex.scroll_px;
            dex.scroll_px += d > 0 ? (d > 3 ? 3 : d) : (d < -3 ? -3 : d);
            panel_draw_scrollbar();
        }
        if (key_hit(KEY_B) || key_hit(KEY_A)) {
            sfx_play(SFX_CANCEL);
            panel_enable(0);
            panel_wide(0);
            qlog.state = 0;
            qlog_list_redraw();
        }
        return;
    }
    int old = qlog.cursor;
    if (qlog.count) {
        if (key_rep(KEY_UP)) qlog.cursor = (qlog.cursor + qlog.count - 1) % qlog.count;
        if (key_rep(KEY_DOWN)) qlog.cursor = (qlog.cursor + 1) % qlog.count;
    }
    if (old != qlog.cursor) {
        sfx_play(SFX_CURSOR);
        qlog_list_redraw();
    }
    if (key_hit(KEY_B) || key_hit(KEY_START)) {
        qlog_close();
    } else if (key_hit(KEY_SELECT)) {
        sfx_play(SFX_CONFIRM);
        qlog_notes_open();
    } else if (key_hit(KEY_A) && qlog.count) {
        sfx_play(SFX_CONFIRM);
        if (qlog.ids[qlog.cursor] == QUEST_FIELD_NOTES) qlog_notes_open();
        else { qlog.state = 1; qlog_detail_redraw(); }
    }
}

/* The quest log screen (START > QUESTS). */
static void quest_log_open(void)
{
    saga_notes_sync();
    qlog.back_mode = game_mode == MODE_START_MENU ? MODE_START_MENU : MODE_FIELD;
    qlog.state = 0;
    qlog.cursor = qlog.scroll = 0;
    dialog_clear();
    qlog_list_redraw();
    ext_open(qlog_update, 0, qlog_present);
}
