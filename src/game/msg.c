/*
 * Message box with a typewriter effect, page breaks and a blinking ▼,
 * plus a small choice box and a queue of dialog steps (text, questions
 * and callbacks) that scripts use to chain conversations.
 */

#define MSG_TEXT_MAX 400

enum { MSG_IDLE, MSG_TYPING, MSG_PAGE_WAIT, MSG_END_WAIT, MSG_DONE };

/* WAIT: blinking arrow and A at the end. NOWAIT: done as soon as the last
 * character is typed (pages still need A). AUTO: pages and the end move on
 * by themselves after `hold` frames; A skips ahead. */
enum { MSGM_WAIT, MSGM_NOWAIT, MSGM_AUTO };

static struct {
    char text[MSG_TEXT_MAX];
    int pos;          /* next character to draw */
    int line;         /* line within the current page */
    int x, y;
    int state;
    int style;
    int box_y;        /* top cell row of the box */
    int mode;         /* MSGM_* */
    int hold;         /* frames before an auto message moves on */
    int timer;
    int instant;
} msg;

#define MSG_BOX_ROW 14
#define MSG_TEXT_X  16
#define MSG_TEXT_W  208

static void msg_draw_box(void)
{
    canvas_window(0, msg.box_y, CANVAS_COLS, 6, msg.style);
}

static void msg_clear_text(void)
{
    canvas_window_clear(0, msg.box_y, CANVAS_COLS, 6);
    msg.x = MSG_TEXT_X;
    msg.y = msg.box_y * 8 + 8;
    msg.line = 0;
}

static int msg_ink(void)
{
    return INK_DARK;
}

/* Start a message; text is word-wrapped to the box. */
static void msg_start(const char *text, int style, int mode)
{
    text_wrap(msg.text, text, MSG_TEXT_W);
    msg.style = style;
    msg.box_y = MSG_BOX_ROW;
    msg.pos = 0;
    msg.state = MSG_TYPING;
    msg.mode = mode;
    msg.hold = 40;
    msg.timer = 0;
    msg.instant = 0;
    msg_draw_box();
    msg_clear_text();
}

static void msg_draw_arrow(int on)
{
    int ax = 224, ay = msg.box_y * 8 + 8 + LINE_H + 4;
    canvas_fill(ax, ay, 8, 10, 1);
    if (on) text_draw_col(ax, ay - 3, "}", msg_ink(), INK_SHADOW);
}

/* Draw the next character; returns 0 when the page or text is full. */
static int msg_type_char(void)
{
    char c = msg.text[msg.pos];
    if (!c) {
        msg.state = msg.mode == MSGM_NOWAIT ? MSG_DONE : MSG_END_WAIT;
        msg.timer = 0;
        return 0;
    }
    if (c == '\n' || c == '\f') {
        msg.pos++;
        if (msg.line == 1 || c == '\f') {
            msg.state = MSG_PAGE_WAIT;
            msg.timer = 0;
            return 0;
        }
        msg.line++;
        msg.x = MSG_TEXT_X;
        msg.y += LINE_H;
        return 1;
    }
    char one[2] = { c, 0 };
    msg.x = text_draw_col(msg.x, msg.y, one, msg_ink(), INK_SHADOW);
    msg.pos++;
    return 1;
}

static void msg_update(void)
{
    switch (msg.state) {
    case MSG_TYPING: {
        /* option speed; holding A or B always hurries it along */
        static const u8 SPEED[TEXT_SPEED_COUNT] = { 1, 1, 2, 255 };
        int speed = SPEED[opt.text_speed % TEXT_SPEED_COUNT];
        if (opt.text_speed == TEXT_SLOW && (msg.timer++ & 1)) break;
        if (key_down(KEY_A) || key_down(KEY_B)) speed = speed < 4 ? 4 : speed;
        if (msg.instant) speed = 255;
        for (int i = 0; i < speed; i++) {
            if (!msg_type_char()) break;
            if (speed < 4 && (msg.pos & 3) == 0 && msg.text[msg.pos] != ' ') sfx_play(SFX_TEXT);
        }
        break;
    }
    case MSG_PAGE_WAIT:
        msg.timer++;
        if (msg.mode != MSGM_AUTO) msg_draw_arrow((msg.timer >> 4) & 1);
        if (key_hit(KEY_A) || key_hit(KEY_B) || (msg.mode == MSGM_AUTO && msg.timer > msg.hold)) {
            msg_clear_text();
            msg.state = MSG_TYPING;
        }
        break;
    case MSG_END_WAIT:
        msg.timer++;
        if (msg.mode == MSGM_WAIT) msg_draw_arrow((msg.timer >> 4) & 1);
        if (key_hit(KEY_A) || key_hit(KEY_B) || (msg.mode == MSGM_AUTO && msg.timer > msg.hold)) {
            if (msg.mode == MSGM_WAIT) msg_draw_arrow(0);
            msg.state = MSG_DONE;
        }
        break;
    case MSG_DONE:
    default:
        break;
    }
}

/* ---------------- choice box ---------------- */

#define CHOICE_MAX 8

static struct {
    const char *items[CHOICE_MAX];
    int count, cursor, active;
    int cx, cy, cw, ch;
} choice;

static void choice_draw_cursor(void)
{
    for (int i = 0; i < choice.count; i++) {
        int y = (choice.cy + 1) * 8 + i * LINE_H;
        canvas_fill(choice.cx * 8 + 8, y, 8, 14, 1);
        if (i == choice.cursor) text_draw((choice.cx + 1) * 8, y, "{");
    }
}

/* Open a choice box whose bottom-right corner sits at cell (right, bottom). */
static void choice_open(const char *const *items, int count, int right, int bottom)
{
    int w = 0;
    for (int i = 0; i < count && i < CHOICE_MAX; i++) {
        choice.items[i] = items[i];
        int tw = text_width(items[i]);
        if (tw > w) w = tw;
    }
    choice.count = count < CHOICE_MAX ? count : CHOICE_MAX;
    choice.cursor = 0;
    choice.active = 1;
    choice.cw = (w + 7) / 8 + 4;
    choice.ch = choice.count * 2 + 2;
    choice.cx = right - choice.cw;
    choice.cy = bottom - choice.ch;
    canvas_window(choice.cx, choice.cy, choice.cw, choice.ch, WIN_STD);
    for (int i = 0; i < choice.count; i++)
        text_draw((choice.cx + 2) * 8, (choice.cy + 1) * 8 + i * LINE_H, choice.items[i]);
    choice_draw_cursor();
}

static void choice_close(void)
{
    choice.active = 0;
    canvas_clear_cells(choice.cx, choice.cy, choice.cw, choice.ch);
}

/* Returns the chosen index, -2 for cancel (B), or -1 while undecided. */
static int choice_update(void)
{
    if (!choice.active) return -1;
    int old = choice.cursor;
    if (key_rep(KEY_UP)) choice.cursor = (choice.cursor + choice.count - 1) % choice.count;
    if (key_rep(KEY_DOWN)) choice.cursor = (choice.cursor + 1) % choice.count;
    if (old != choice.cursor) choice_draw_cursor();
    if (key_hit(KEY_A)) return choice.cursor;
    if (key_hit(KEY_B)) return -2;
    return -1;
}

/* ---------------- dialog queue ---------------- */

typedef void (*DialogFn)(int choice);

enum { DQ_TEXT, DQ_ASK, DQ_CALL };

typedef struct {
    u8 kind;
    char text[MSG_TEXT_MAX];
    const char *const *choices;
    int choice_count;
    DialogFn fn;
    int arg;
} DialogStep;

#define DIALOG_QUEUE 24
EWRAM_BSS static DialogStep dialog_q[DIALOG_QUEUE];
static int dialog_head, dialog_count;
static int dialog_phase; /* 0 = step not started, 1 = message, 2 = choosing */
static int dialog_style = WIN_STD; /* WIN_BATTLE while a battle runs */

static DialogStep *dialog_push(int kind)
{
    if (dialog_count >= DIALOG_QUEUE) return 0;
    DialogStep *s = &dialog_q[(dialog_head + dialog_count) % DIALOG_QUEUE];
    dialog_count++;
    s->kind = (u8)kind;
    s->text[0] = 0;
    s->choices = 0;
    s->choice_count = 0;
    s->fn = 0;
    s->arg = 0;
    return s;
}

static void dlg_say(const char *text)
{
    DialogStep *s = dialog_push(DQ_TEXT);
    if (s) str_copy(s->text, text);
}

static void dlg_ask(const char *text, const char *const *choices, int n, DialogFn fn)
{
    DialogStep *s = dialog_push(DQ_ASK);
    if (!s) return;
    str_copy(s->text, text);
    s->choices = choices;
    s->choice_count = n;
    s->fn = fn;
}

/* Run fn(arg) once the preceding steps have finished. */
static void dlg_call(DialogFn fn, int arg)
{
    DialogStep *s = dialog_push(DQ_CALL);
    if (!s) return;
    s->fn = fn;
    s->arg = arg;
}

static void dialog_clear(void)
{
    dialog_head = dialog_count = 0;
    dialog_phase = 0;
    choice.active = 0;
}

static int dialog_active(void)
{
    return dialog_count > 0;
}

static void dialog_pop(void)
{
    dialog_head = (dialog_head + 1) % DIALOG_QUEUE;
    dialog_count--;
    dialog_phase = 0;
}

static const char *const YES_NO[] = { "YES", "NO" };

/* Drives the queue; returns 1 while dialog is still running. */
static int dialog_update(void)
{
    while (dialog_count > 0) {
        DialogStep *s = &dialog_q[dialog_head];
        if (s->kind == DQ_CALL) {
            DialogFn fn = s->fn;
            int arg = s->arg;
            dialog_pop();
            if (fn) fn(arg);
            continue;
        }
        if (dialog_phase == 0) {
            msg_start(s->text, dialog_style, s->kind == DQ_TEXT ? MSGM_WAIT : MSGM_NOWAIT);
            dialog_phase = 1;
            return 1;
        }
        if (dialog_phase == 1) {
            msg_update();
            if (s->kind == DQ_ASK && msg.state == MSG_DONE) {
                choice_open(s->choices, s->choice_count, CANVAS_COLS, MSG_BOX_ROW);
                dialog_phase = 2;
            } else if (msg.state == MSG_DONE) {
                dialog_pop();
                if (!dialog_count) canvas_clear_cells(0, MSG_BOX_ROW, CANVAS_COLS, 6);
                continue;
            }
            return 1;
        }
        if (dialog_phase == 2) {
            int c = choice_update();
            if (c == -1) return 1;
            DialogFn fn = s->fn;
            int n = s->choice_count;
            choice_close();
            dialog_pop();
            /* B picks the last option ("NO"/"CANCEL") */
            if (c == -2) c = n - 1;
            if (fn) fn(c);
            if (!dialog_count) canvas_clear_cells(0, MSG_BOX_ROW, CANVAS_COLS, 6);
            continue;
        }
    }
    return 0;
}
