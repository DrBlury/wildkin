/*
 * Growth scene: "Huh? X is growing!", the old and new forms flicker
 * faster and faster in white silhouette, then the new form is revealed.
 * B cancels while it is still flickering. Afterwards the grown form may
 * learn moves for its current level.
 */

enum { EVS_INTRO, EVS_ANIM, EVS_OUTRO };

static struct { int slot, from, into, t, state, show_new, white; } evo;

static void evolve_draw_scene(void)
{
    dialog_clear();
    canvas_clear();
    canvas_fill(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 1);
    canvas_set_banks(0, 0, CANVAS_COLS, CANVAS_ROWS, BANK_UI_BATTLE);
    /* only the UI layer: closed message boxes reveal the backdrop color */
    REG_DISPCNT = DCNT_MODE0 | DCNT_BG1 | DCNT_OBJ | DCNT_OBJ_1D;
    bg_palette[0] = ui_pal_battle[1];
}

static void evolve_start_next(void)
{
    if (!evo_count) {
        field_return();
        return;
    }
    EvoRequest r = evo_queue[0];
    for (int i = 1; i < evo_count; i++) evo_queue[i - 1] = evo_queue[i];
    evo_count--;
    evo.slot = r.slot;
    evo.from = party[r.slot].species;
    evo.into = r.into;
    evo.t = 0;
    evo.state = EVS_INTRO;
    evo.show_new = 0;
    evo.white = 0;
    game_mode = MODE_EVOLVE;
    evolve_draw_scene();
    load_monster_gfx(0, evo.from, 0);
    load_monster_gfx(1, evo.into, 0);
    build_fx_palette(OBANK_FX_HIT, RGB15(31, 31, 22), RGB15(26, 28, 31));
    char msg[64];
    str_copy(msg, "Huh? ");
    str_put(msg, kin_name(&party[evo.slot]));
    str_put(msg, " is growing!");
    dlg_say(msg);
}

static void evolve_whiten(int amount)
{
    const u16 white = RGB15(31, 31, 31);
    for (int s = 0; s < 2; s++) {
        const u16 *src = mon_palettes[s ? evo.into : evo.from];
        u16 *dst = obj_palette + (s ? OBANK_MON_B : OBANK_MON_A) * 16;
        for (int i = 1; i < 16; i++) dst[i] = mix15(src[i], white, amount, 16);
    }
}

static void evolve_update(void)
{
    char msg[96];
    switch (evo.state) {
    case EVS_INTRO:
        if (!dialog_update()) {
            evo.state = EVS_ANIM;
            evo.t = 0;
        }
        break;
    case EVS_ANIM:
        evo.t++;
        evo.white = evo.t < 48 ? evo.t / 3 : 16;
        {
            int period = 40 - evo.t / 6;
            if (period < 2) period = 2;
            evo.show_new = (evo.t / period) & 1;
        }
        evolve_whiten(evo.white);
        if (evo.t < 220 && key_hit(KEY_B)) {
            evolve_whiten(0);
            evo.show_new = 0;
            str_copy(msg, "Huh? ");
            str_put(msg, kin_name(&party[evo.slot]));
            str_put(msg, " settled back down. It stopped growing.");
            dlg_say(msg);
            evo.state = EVS_OUTRO;
            break;
        }
        if (evo.t >= 240) {
            set_brightness(0);
            evolve_whiten(0);
            evo.show_new = 1;
            Monster *m = &party[evo.slot];
            char was[KIN_NAME_LEN + 16];
            str_copy(was, kin_name(m));
            monster_evolve(m, evo.into);
            sfx_play(SFX_GROW);
            dex_seen[evo.into] = 1;
            dex_caught[evo.into] = 1;
            str_copy(msg, "Your ");
            str_put(msg, was);
            str_put(msg, " grew into ");
            str_put(msg, SPECIES[evo.into].name);
            str_put(msg, "!");
            dlg_say(msg);
            u8 moves[4];
            int n = learnset_at(evo.into, m->level, moves);
            for (int i = 0; i < n; i++) learn_begin(evo.slot, moves[i]);
            evo.state = EVS_OUTRO;
        } else if (evo.t >= 228) {
            set_brightness((evo.t - 228) + 4);
        }
        break;
    case EVS_OUTRO:
        if (!dialog_update()) evolve_start_next();
        break;
    }
}

static void evolve_draw(void)
{
    spr_push(88, 32, evo.show_new ? OT_MON_B : OT_MON_A, SQ64, evo.show_new ? OBANK_MON_B : OBANK_MON_A, 0, 0);
    if (evo.state == EVS_ANIM && evo.t > 30) {
        for (int k = 0; k < 6; k++) {
            int a = evo.t * 5 + k * 43;
            int r = 44 - (evo.t * 2 + k * 17) % 40;
            spr_push(112 + tri_sin(a) * r / 64, 60 + tri_sin(a + 64) * r / 64, OT_FX + FX_SPARKLE * 4,
                     SQ16, OBANK_FX_HIT, 0, 0);
        }
    }
}
