/*
 * The name slate: giving a kin a nickname.
 *
 * A carved tablet: the kin's portrait top left, the slate with ten letter
 * grooves beside it, and a keyboard of stone keys below (A-Z, 0-9, a few
 * marks, SPACE, ERASE, DONE). D-pad moves, A carves the key, B erases the
 * last letter (or leaves unchanged when the slate is empty), START jumps
 * to DONE. DONE with an empty slate clears the nickname (the kin goes by
 * its species name again).
 *
 *   naming_open(NM_TEAM, slot, done) / naming_open(NM_SHELF, index, done)
 *
 * runs as an ext screen; `done` is called once it closes (nm.accepted says
 * whether a name was set) and restores whatever screen came before.
 */

enum { NM_TEAM, NM_SHELF };

#define NM_COLS 11
#define NM_ROWS 5            /* four rows of letters, then SPACE / ERASE / DONE */
static const char NM_KEYS[4][NM_COLS + 1] = {
    "ABCDEFGHIJK",
    "LMNOPQRSTUV",
    "WXYZ'.-!?&+",
    "0123456789/",
};
enum { NMK_SPACE = 0, NMK_ERASE = 4, NMK_DONE = 7 };   /* first column of each wide key */

static struct {
    int where, idx, species, lustrous;
    char buf[KIN_NAME_LEN + 1];
    int len, row, col;
    int dirty, blink, accepted;
    void (*done)(void);
} nm;

static void naming_update(void);
static void naming_draw(void);

/* Keyboard geometry (pixels). */
#define NM_KX  10
#define NM_KY  81
#define NM_KW  20
#define NM_KH  14

/* The wide key a column of the last row belongs to. */
static int nm_wide_key(int col)
{
    return col >= NMK_DONE ? NMK_DONE : col >= NMK_ERASE ? NMK_ERASE : NMK_SPACE;
}

static int nm_wide_width(int key)
{
    return key == NMK_ERASE ? 3 : 4;
}

static Monster nm_target(void)
{
    if (nm.where == NM_SHELF) return storage_get(nm.idx);
    return party[nm.idx];
}

/* One stone key: raised (6 with a 5 lip), pressed-in when selected. */
static void nm_key(int x, int w, int y, const char *label, int sel, int kind)
{
    int face = 6, lip = 5, ink = INK_DARK;
    if (kind == 1) { face = 13; lip = 12; ink = INK_GREEN; }      /* DONE */
    else if (kind == 2) { face = 9; lip = 8; ink = INK_RED; }     /* ERASE */
    if (sel) {
        canvas_fill(x, y, w, NM_KH - 1, 4);
        canvas_fill(x + 1, y + 1, w - 2, NM_KH - 3, kind == 1 ? 12 : kind == 2 ? 8 : 10);
        text_draw_col(x + (w - text_width(label)) / 2, y, label, 1, 4);
        return;
    }
    canvas_fill(x, y, w, NM_KH - 2, face);
    canvas_fill(x, y + NM_KH - 3, w, 1, lip);
    text_draw_col(x + (w - text_width(label)) / 2, y - 1, label, ink, face);
}

static void nm_draw_keys(void)
{
    char s[2] = { 0, 0 };
    canvas_window_clear(0, 9, CANVAS_COLS, 11);
    for (int r = 0; r < 4; r++)
        for (int c = 0; c < NM_COLS; c++) {
            s[0] = NM_KEYS[r][c];
            nm_key(NM_KX + c * NM_KW, NM_KW - 2, NM_KY + r * NM_KH, s, nm.row == r && nm.col == c, 0);
        }
    static const char *const WIDE[3] = { "SPACE", "ERASE", "DONE" };
    static const u8 FIRST[3] = { NMK_SPACE, NMK_ERASE, NMK_DONE };
    for (int k = 0; k < 3; k++) {
        int w = nm_wide_width(FIRST[k]) * NM_KW - 2;
        int sel = nm.row == 4 && nm_wide_key(nm.col) == FIRST[k];
        nm_key(NM_KX + FIRST[k] * NM_KW, w, NM_KY + 4 * NM_KH + 1, WIDE[k], sel, k == 2 ? 1 : k == 1 ? 2 : 0);
    }
}

/* The slate: ten grooves, the letters so far, a blinking chisel mark. */
static void nm_draw_slate(void)
{
    canvas_window_clear(10, 5, 20, 4);
    const char *ghost = SPECIES[nm.species].name;
    for (int i = 0; i < KIN_NAME_LEN; i++) {
        int x = 92 + i * 14, y = 47;
        char s[2] = { 0, 0 };
        int cursor = i == nm.len;
        canvas_fill(x, y + 13, 12, 2, cursor && !nm.blink ? 8 : 5);
        if (i < nm.len) {
            s[0] = nm.buf[i];
            text_draw(x + (12 - char_width(s[0])) / 2 + 1, y, s);
        } else if (!nm.len && i < (int)str_len(ghost)) {
            s[0] = ghost[i];      /* the name it keeps if the slate stays empty */
            text_draw_col(x + (12 - char_width(s[0])) / 2 + 1, y, s, INK_SHADOW, INK_SHADOW);
        }
    }
    /* letters used, top right of the header */
    char n[8];
    n[0] = 0;
    str_put_int(n, nm.len);
    str_put(n, "/");
    str_put_int(n, KIN_NAME_LEN);
    canvas_fill(196, 10, 36, 8, 1);
    small_text_draw(230 - small_text_width(n), 11, n);
}

static void nm_redraw(void)
{
    char buf[24];
    Monster m = nm_target();
    screen_begin(1);
    canvas_window(0, 0, 10, 9, WIN_STD);           /* portrait (the sprite sits on it) */
    canvas_window(10, 0, 20, 5, WIN_STD);
    text_draw_col(90, 7, "CARVE A NAME", INK_BLUE, INK_BLUE_SH);
    str_copy(buf, SPECIES[m.species].name);
    text_draw(90, 21, buf);
    mon_level_text(buf, &m);
    small_text_draw(230 - small_text_width(buf), 25, buf);
    canvas_window(10, 5, 20, 4, WIN_STD);
    nm_draw_slate();
    canvas_window(0, 9, CANVAS_COLS, 11, WIN_STD);
    nm_draw_keys();
}

static void naming_open(int where, int idx, void (*done)(void))
{
    nm.where = where;
    nm.idx = idx;
    nm.done = done;
    Monster m = nm_target();
    nm.species = m.species;
    nm.lustrous = (m.flags & MF_LUSTROUS) != 0;
    nm.len = 0;
    for (int i = 0; i <= KIN_NAME_LEN; i++) nm.buf[i] = m.name[i];
    nm.buf[KIN_NAME_LEN] = 0;
    nm.len = (int)str_len(nm.buf);
    nm.row = 0;
    nm.col = 0;
    nm.blink = 0;
    nm.accepted = 0;
    nm.dirty = 1;             /* drawn on the first update: a closing dialog may still clear its box */
    load_monster_gfx_ex(0, nm.species, 0, nm.lustrous);
    ext_open(naming_update, naming_draw, 0);
}

static int naming_active(void)
{
    return game_mode == MODE_EXT && ext.update == naming_update;
}

static void nm_close(int accept)
{
    if (accept) {
        if (nm.where == NM_SHELF) {
            if (nm.idx >= 0 && nm.idx < storage_count) {
                Monster m = storage_get(nm.idx);
                kin_set_name(&m, nm.buf);
                for (int i = 0; i < KIN_NAME_LEN; i++) storage[nm.idx].name[i] = m.name[i];
            }
        } else if (nm.idx >= 0 && nm.idx < party_count) {
            kin_set_name(&party[nm.idx], nm.buf);
        }
    }
    nm.accepted = accept;
    canvas_clear();
    game_mode = MODE_FIELD;   /* the callback picks the real screen */
    ext.update = 0;
    ext.draw = 0;
    ext.present = 0;
    if (nm.done) nm.done();
}

static void nm_type(char c)
{
    if (nm.len >= KIN_NAME_LEN || (c == ' ' && nm.len == 0)) {
        sfx_play(SFX_ERROR);
        return;
    }
    nm.buf[nm.len++] = c;
    nm.buf[nm.len] = 0;
    sfx_play(SFX_CURSOR);
    if (nm.len == KIN_NAME_LEN) {   /* full: on to DONE */
        nm.row = 4;
        nm.col = NMK_DONE;
    }
}

static void naming_update(void)
{
    int keys = 0, slate = 0;
    if ((frame_count & 15) == 0) {
        nm.blink ^= 1;
        slate = 1;
    }
    if (key_rep(KEY_UP)) {
        nm.row = (nm.row + NM_ROWS - 1) % NM_ROWS;
        keys = 1;
    }
    if (key_rep(KEY_DOWN)) {
        nm.row = (nm.row + 1) % NM_ROWS;
        keys = 1;
    }
    if (key_rep(KEY_LEFT)) {
        if (nm.row == 4) {
            int k = nm_wide_key(nm.col);
            nm.col = k == NMK_SPACE ? NMK_DONE : k == NMK_ERASE ? NMK_SPACE : NMK_ERASE;
        } else {
            nm.col = (nm.col + NM_COLS - 1) % NM_COLS;
        }
        keys = 1;
    }
    if (key_rep(KEY_RIGHT)) {
        if (nm.row == 4) {
            int k = nm_wide_key(nm.col);
            nm.col = k == NMK_SPACE ? NMK_ERASE : k == NMK_ERASE ? NMK_DONE : NMK_SPACE;
        } else {
            nm.col = (nm.col + 1) % NM_COLS;
        }
        keys = 1;
    }
    if (keys) sfx_play(SFX_CURSOR);
    if (key_hit(KEY_START)) {
        nm.row = 4;
        nm.col = NMK_DONE;
        keys = 1;
    }
    if (key_hit(KEY_B)) {
        if (!nm.len) {
            sfx_play(SFX_CANCEL);
            nm_close(0);
            return;
        }
        nm.buf[--nm.len] = 0;
        sfx_play(SFX_CANCEL);
        slate = 1;
    } else if (key_hit(KEY_A)) {
        if (nm.row < 4) {
            nm_type(NM_KEYS[nm.row][nm.col]);
        } else {
            int k = nm_wide_key(nm.col);
            if (k == NMK_SPACE) {
                nm_type(' ');
            } else if (k == NMK_ERASE) {
                if (nm.len) nm.buf[--nm.len] = 0;
                sfx_play(SFX_CANCEL);
            } else {
                sfx_play(SFX_CONFIRM);
                nm_close(1);
                return;
            }
        }
        slate = keys = 1;
    }
    if (nm.dirty) {
        nm_redraw();
        nm.dirty = 0;
        return;
    }
    if (keys) nm_draw_keys();
    if (slate || keys) nm_draw_slate();
}

static void naming_draw(void)
{
    spr_push(8, 4, OT_MON_A, SQ64, OBANK_MON_A, 0, 0);
}

/* ---------------- after a catch (battle event EV_NAME) ---------------- */

/* EV_NAME: a = 0 joined the team / 1 went to the Shelf, b = its slot. */
static struct { int where, idx; } catch_nm;

static void catch_name_done(void)
{
    game_mode = MODE_BATTLE;
    canvas_clear();
    battle_reload_gfx();
    battle.hud_dirty = 3;
}

static void catch_name_answer(int c)
{
    if (c != 0) return;
    battle_lines_off();       /* the bout's scanline effects stay out of the slate */
    naming_open(catch_nm.where ? NM_SHELF : NM_TEAM, catch_nm.idx, catch_name_done);
}

static void catch_name_begin(BEvent *e)
{
    char msg[64];
    catch_nm.where = e->a;
    catch_nm.idx = e->b;
    Monster m = catch_nm.where ? storage_get(catch_nm.idx) : party[catch_nm.idx];
    str_copy(msg, "Give ");
    str_put(msg, kin_name(&m));
    str_put(msg, " a name?");
    dlg_ask(msg, YES_NO, 2, catch_name_answer);
}

/* 1 once the question (and the slate, if opened) is done. */
static int catch_name_update(BEvent *e)
{
    if (naming_active() || dialog_update()) return 0;
    if (e->a) {
        Monster m = storage_get(catch_nm.idx);
        BEvent *t = bev_insert_next(EV_TEXT, 0, MSGM_WAIT, 0, 0);
        str_copy(t->text, kin_name(&m));
        str_put(t->text, " was sent to the LANTERN SHELF.");
    }
    return 1;
}
