/*
 * Title screen: the WILDKIN logo, DRAKORA circling in a storm-dark sky and
 * a blinking PRESS START; then CONTINUE (when a save exists) or NEW GAME.
 * A new game opens with a storybook: the Kinship told in a few pages,
 * each with one of the kin it mentions, before you wake up at home.
 */

static struct { int state, timer, has_save, page_species; } title;
static const char *const TITLE_CONTINUE[] = { "CONTINUE", "NEW GAME" };
static const char *const TITLE_NEW[] = { "NEW GAME" };

/* Text scaled up by `s`, filled with `ink` and a drop shadow `sh`. */
static void title_big_text(int x, int y, const char *str, int s, int ink, int sh)
{
    for (int pass = 0; pass < 2; pass++) {
        int cx = x;
        for (const char *p = str; *p; p++) {
            int g = glyph_index(*p);
            for (int r = 0; r < FONT_HEIGHT; r++)
                for (int b = 0; b < 8; b++)
                    if (font_bits[g][r] & (0x80 >> b)) {
                        int off = pass ? 0 : s;
                        canvas_fill(cx + b * s + off, y + r * s + off, s, s, pass ? ink : sh);
                    }
            cx += font_width[g] * s;
        }
    }
}

static int title_text_width(const char *s, int scale)
{
    return text_width(s) * scale;
}

static void title_draw(void)
{
    dialog_clear();
    canvas_clear();
    canvas_fill(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 1);
    canvas_set_banks(0, 0, CANVAS_COLS, CANVAS_ROWS, BANK_UI_BATTLE);
    REG_DISPCNT = DCNT_MODE0 | DCNT_BG1 | DCNT_OBJ | DCNT_OBJ_1D;
    bg_palette[0] = ui_pal_battle[1];
    const char *logo = "WILDKIN";
    title_big_text((SCREEN_WIDTH - title_text_width(logo, 3)) / 2, 6, logo, 3, 12, 9);
    const char *sub = "The Brimming Storm";
    text_draw_col((SCREEN_WIDTH - text_width(sub)) / 2, 52, sub, INK_DARK, INK_SHADOW);
    load_monster_gfx(0, SP_DRAKORA, 0);
    load_monster_gfx(1, SP_FLARIX, 0);
}

static void title_open(int has_save)
{
    title.has_save = has_save;
    title.state = 0;
    title.timer = 0;
    game_mode = MODE_TITLE;
    title_draw();
}

static void title_enter_field(void)
{
    choice.active = 0;
    canvas_clear();
    set_brightness(0);
    game_mode = MODE_FIELD;
    field_setup_bg();
    field_load_tileset();
    field_update_camera();
}

/* ---------------- storybook ---------------- */

static const u8 STORY_KIN[] = {
    SP_DRAKORA, SP_MAGMAUL, SP_ZAPPET, SP_DANDELAMB, SP_WISPIRE, SP_AQUAPO, SP_FLARIX,
    SP_DRAKORA, SP_STORMHAWK, SP_DRAKORA,
};

static void story_page(int i)
{
    int sp = STORY_KIN[i % (int)sizeof(STORY_KIN)];
    title.page_species = sp;
    load_monster_gfx(0, sp, 0);
    sfx_play(SFX_TEXT);
}

static void story_done(int unused)
{
    (void)unused;
    title.state = 3;
    title.timer = 0;
}

static void story_begin(void)
{
    dialog_clear();
    canvas_clear();
    canvas_fill(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 1);
    canvas_set_banks(0, 0, CANVAS_COLS, CANVAS_ROWS, BANK_UI_BATTLE);
    dialog_style = WIN_BATTLE;
    title.state = 2;
    title.timer = 0;
    for (int i = 0; INTRO_PAGES[i]; i++) {
        dlg_call(story_page, i);
        dlg_say(INTRO_PAGES[i]);
    }
    dlg_call(story_done, 0);
}

static void title_update(void)
{
    title.timer++;
    if (title.state == 0) {
        int on = (title.timer >> 5) & 1;
        canvas_fill(0, 132, SCREEN_WIDTH, 16, 1);
        if (on) text_draw_center(SCREEN_WIDTH / 2, 134, "PRESS START");
        if (key_hit(KEY_START) || key_hit(KEY_A)) {
            sfx_play(SFX_CONFIRM);
            canvas_fill(0, 132, SCREEN_WIDTH, 16, 1);
            title.state = 1;
            if (title.has_save) choice_open(TITLE_CONTINUE, 2, 21, 19);
            else choice_open(TITLE_NEW, 1, 21, 19);
        }
        return;
    }
    if (title.state == 1) {
        int c = choice_update();
        if (c == -2) {
            choice_close();
            title.state = 0;
            return;
        }
        if (c < 0) return;
        choice_close();
        if (title.has_save && c == 0) {
            title_enter_field();
            follower_reset();
            return;
        }
        new_game();
        story_begin();
        return;
    }
    if (title.state == 2) {
        dialog_update();
        return;
    }
    /* storybook over: fade into the morning at home */
    if (title.timer <= 16) {
        set_brightness(-title.timer);
        return;
    }
    dialog_style = WIN_STD;
    story_flags |= FLAG_INTRO;
    title_enter_field();
    set_brightness(0);
    dlg_say("...It's morning. Sunlight on the floorboards, and Gran humming downstairs. Today is your KINDLING!");
}

static void title_draw_sprites(void)
{
    if (title.state == 2) {
        int bob = tri_sin(title.timer * 2) / 20;
        spr_push(88, 24 + bob, OT_MON_A, SQ64, OBANK_MON_A, 0, 0);
        return;
    }
    if (title.state != 0) return; /* keep the menu box readable */
    int bob = tri_sin(title.timer * 2) / 16;
    spr_push(120, 60 + bob, OT_MON_A, SQ64, OBANK_MON_A, 0, 0);
    spr_push(40, 72 - bob / 2, OT_MON_B, SQ64, OBANK_MON_B, 0, 0);
}
