/*
 * Battle presentation: plays the event queue built by battle.c, draws the
 * HUD from display values (eased HP bars that change colour, a lighter
 * "lost HP" chunk that catches up, a jolt when the kin is hit), runs the
 * action/move menus, the lantern throw and send-out, dozing off, and the
 * lantern-light intro (a circle of light opening on a dark scene).
 *
 * Kin sprites are affine (double-size 64x64) so they can squash, stretch,
 * breathe and pop in. Per-scanline tables (HBlank DMA, re-armed in vblank
 * by oam_commit) wobble the scene, jolt the HUD bands and shape the intro
 * iris window.
 */

enum { PCTX_FIELD, PCTX_BATTLE_SWITCH, PCTX_BATTLE_FORCED, PCTX_ITEM_FIELD, PCTX_ITEM_BATTLE };
enum { BAGCTX_FIELD, BAGCTX_BATTLE };

static void party_screen_open(int ctx, int item);
static void bag_screen_open(int ctx);
static void field_return(void);
static void evolve_start_next(void);

enum {
    MODE_FIELD, MODE_START_MENU, MODE_PARTY, MODE_SUMMARY, MODE_BAG, MODE_DEX,
    MODE_SHOP, MODE_PC, MODE_BATTLE, MODE_EVOLVE, MODE_TITLE
};
static int game_mode;
static unsigned frame_count;

#define HUD_ENEMY_CX 1
#define HUD_ENEMY_CY 1
#define HUD_ALLY_CX 16
#define HUD_ALLY_CY 8

/* BG palette banks used during a bout (the field reloads 0..7 afterwards). */
#define BANK_SCENE      0   /* 0..3 */
#define BANK_HUD_ENEMY  4
#define BANK_HUD_ALLY   5
#define BANK_LABELS     6

/* HUD palette entries: 8/9 HP fill (light, shade), 10/11 the lost-HP
 * chunk, 14 XP, 15 bar trough. */
#define HUDC_FILL   8
#define HUDC_FILL_S 9
#define HUDC_TRAIL  10
#define HUDC_TRAIL_S 11

#define INTRO_DARK  18   /* frames the field dissolves */
#define INTRO_OPEN  30   /* frames the lantern light takes to open */

static u8 battle_leveled;   /* party slots that gained a level this battle */

/* the current scene's palettes (tints are blended from these) */
static u16 scene_pal[4][16];
static int scene_tint_applied = -1;
static u16 scene_tint_color;

/*
 * Scanline tables, double-buffered. Each holds the 160 lines three times
 * over: the HBlank DMA runs on through the table until it is re-armed in
 * vblank, so if a slow frame misses a vblank the next frame still reads
 * the same values instead of whatever follows the table.
 */
#define LINE_COPIES 3
EWRAM_BSS static u32 line_bg0[2][SCREEN_HEIGHT * LINE_COPIES + 1];
EWRAM_BSS static u32 line_bg1[2][SCREEN_HEIGHT * LINE_COPIES + 1];
EWRAM_BSS static u16 line_win[2][SCREEN_HEIGHT * LINE_COPIES + 1];
static int line_buf;

/* OBJ bank 15 belongs to the field's emotes; borrowed for lantern light
 * during a bout and put back afterwards. */
static u16 saved_light_bank[16];

/* afterimage history of each battler (screen positions) */
static s16 trail_x[2][8], trail_y[2][8];
static int trail_head;

/* ---------------- HUD ---------------- */

static int hud_cx(int side) { return side == SIDE_ENEMY ? HUD_ENEMY_CX : HUD_ALLY_CX; }
static int hud_cy(int side) { return side == SIDE_ENEMY ? HUD_ENEMY_CY : HUD_ALLY_CY; }
static int hud_bank(int side) { return side == SIDE_ENEMY ? BANK_HUD_ENEMY : BANK_HUD_ALLY; }

static void hud_load_palettes(void)
{
    for (int s = 0; s < 2; s++) {
        u16 *p = bg_palette + hud_bank(s) * 16;
        copy16(p, ui_pal_hud, 16);
        p[HUDC_TRAIL] = RGB15(31, 27, 20);
        p[HUDC_TRAIL_S] = RGB15(29, 17, 12);
    }
    load_pal(bg_palette + BANK_LABELS * 16, bl_pal);
}

/* HP fill colour: green, easing through yellow into red as HP drops. */
static void hud_bar_colors(int side)
{
    static const u16 G[2] = { RGB15(14, 31, 21), RGB15(11, 25, 15) };
    static const u16 Y[2] = { RGB15(31, 28, 7), RGB15(25, 20, 1) };
    static const u16 R[2] = { RGB15(31, 11, 7), RGB15(21, 7, 8) };
    int max = battle.disp[side].max_hp;
    int f = max > 0 ? battle.disp[side].hp * 256 / max : 0;
    u16 *p = bg_palette + hud_bank(side) * 16;
    for (int k = 0; k < 2; k++) {
        u16 c;
        if (f >= 140) c = G[k];
        else if (f >= 64) c = mix15(Y[k], G[k], f - 64, 76);
        else c = mix15(R[k], Y[k], f, 64);
        p[HUDC_FILL + k] = c;
    }
}

static void hud_draw_bar(int side)
{
    int px = hud_cx(side) * 8, py = hud_cy(side) * 8;
    int x = px + (side == SIDE_ENEMY ? HUD_ENEMY_BAR_X : HUD_ALLY_BAR_X);
    int y = py + (side == SIDE_ENEMY ? HUD_ENEMY_BAR_Y : HUD_ALLY_BAR_Y);
    int w = 48, max = battle.disp[side].max_hp;
    int hp = battle.disp[side].hp, tr = battle.disp[side].trail;
    int fill = max > 0 ? (hp * w + max - 1) / max : 0;
    int tfill = max > 0 ? (tr * w + max - 1) / max : 0;
    if (hp <= 0) fill = 0;
    fill = clampi(fill, 0, w);
    tfill = clampi(tfill, fill, w);
    canvas_fill(x, y, w, 3, 15);
    if (tfill > fill) {
        canvas_fill(x + fill, y, tfill - fill, 1, HUDC_TRAIL_S);
        canvas_fill(x + fill, y + 1, tfill - fill, 2, HUDC_TRAIL);
    }
    if (fill) {
        canvas_fill(x, y, fill, 1, HUDC_FILL_S);
        canvas_fill(x, y + 1, fill, 2, HUDC_FILL);
    }
    if (side == SIDE_ALLY) {
        char buf[16];
        canvas_fill(px + HUD_ALLY_HPNUM_X - 40, py + HUD_ALLY_HPNUM_Y, 40, FONT_SMALL_HEIGHT, 1);
        buf[0] = 0;
        str_put_int(buf, hp);
        str_put(buf, "/");
        str_put_int(buf, max);
        small_text_draw(px + HUD_ALLY_HPNUM_X - small_text_width(buf), py + HUD_ALLY_HPNUM_Y, buf);
    }
    hud_bar_colors(side);
}

static int hud_shown(int side)
{
    return battle.disp[side].visible && !battle.disp[side].inlantern && !battle.disp[side].fade &&
           !battle.disp[side].shrink;
}

static void hud_draw(int side)
{
    int cx = hud_cx(side), cy = hud_cy(side);
    int th = side == SIDE_ENEMY ? 4 : 5;
    canvas_clear_cells(cx, cy, 13, th);
    canvas_set_banks(cx, cy, 13, th, hud_bank(side));
    if (!hud_shown(side)) return;
    const u32 *art = side == SIDE_ENEMY ? hud_enemy_gfx : hud_ally_gfx;
    canvas_image(cx, cy, 13, th, art, 0, hud_bank(side));
    int px = cx * 8, py = cy * 8;
    char buf[24];
    int nx = side == SIDE_ENEMY ? HUD_ENEMY_NAME_X : HUD_ALLY_NAME_X;
    int ny = side == SIDE_ENEMY ? HUD_ENEMY_NAME_Y : HUD_ALLY_NAME_Y;
    text_draw(px + nx, py + ny, SPECIES[battle.disp[side].species].name);
    str_copy(buf, "Lv");
    str_put_int(buf, battle.disp[side].level);
    small_text_draw(px + (side == SIDE_ENEMY ? HUD_ENEMY_LV_X : HUD_ALLY_LV_X),
                    py + (side == SIDE_ENEMY ? HUD_ENEMY_LV_Y : HUD_ALLY_LV_Y), buf);
    hud_draw_bar(side);
    int st = battle.disp[side].status;
    if (st != STATUS_NONE)
        draw_status_badge(cx + (side == SIDE_ENEMY ? HUD_ENEMY_STATUS_X : HUD_ALLY_STATUS_X) / 8,
                          cy + (side == SIDE_ENEMY ? HUD_ENEMY_STATUS_Y : HUD_ALLY_STATUS_Y) / 8, st);
    if (side == SIDE_ALLY) {
        int lv = battle.disp[side].level;
        u32 lo = xp_for_level(lv), hi = xp_for_level(lv + 1);
        u32 cur = battle.disp_xp < lo ? lo : battle.disp_xp;
        draw_xp_bar(px + HUD_ALLY_EXP_X, py + HUD_ALLY_EXP_Y, 64,
                    lv >= MAX_LEVEL ? 0 : (int)(cur - lo), (int)(hi - lo));
    }
}

static void disp_sync(int side)
{
    Monster *m = side_mon(side);
    battle.disp[side].species = m->species;
    battle.disp[side].level = m->level;
    battle.disp[side].hp = m->hp;
    battle.disp[side].trail = m->hp;
    battle.disp[side].trail_hold = 0;
    battle.disp[side].max_hp = m->max_hp;
    battle.disp[side].status = m->status;
    battle.disp[side].lustrous = (m->flags & MF_LUSTROUS) != 0;
    mon_palette_get(battle.disp[side].pal, m->species, battle.disp[side].lustrous);
    if (side == SIDE_ALLY) battle.disp_xp = m->xp;
    if (side == SIDE_ENEMY) battle.disp[side].caught = battle.kind == BK_WILD && dex_caught[m->species];
    battle.hud_dirty |= 1 << side;
}

static void battle_load_mon_gfx(int side)
{
    Monster *m = side_mon(side);
    if (side == SIDE_ALLY) load_monster_gfx_ex(1, m->species, 1, (m->flags & MF_LUSTROUS) != 0);
    else load_monster_gfx_ex(0, m->species, 0, (m->flags & MF_LUSTROUS) != 0);
}

/* ---------------- bottom boxes ---------------- */

static const char *const ACTION_LABELS[4] = { "FIGHT", "BAG", "TEAM", "RUN" };

static void clear_tab(void)
{
    canvas_clear_cells(22, 13, 8, 1);
}

static void draw_action_box(void)
{
    char buf[48];
    clear_tab();
    canvas_window(0, 14, CANVAS_COLS, 6, WIN_BATTLE);
    str_copy(buf, "What will\n");
    str_put(buf, SPECIES[side_mon(SIDE_ALLY)->species].name);
    str_put(buf, " do?");
    text_draw_col(16, 120, buf, INK_DARK, INK_SHADOW);
    canvas_window(15, 14, 15, 6, WIN_STD);
    for (int i = 0; i < 4; i++) {
        int x = 15 * 8 + 18 + (i & 1) * 48, y = 120 + (i >> 1) * LINE_H;
        text_draw(x, y, ACTION_LABELS[i]);
        if (i == battle.cursor) text_draw(x - 10, y, "{");
    }
    /* on RUN in a wild bout: the escape odds when they are not certain */
    int pct = battle.kind == BK_WILD && battle.cursor == 3 ? battle_run_chance() : 100;
    if (pct > 0 && pct < 100) {
        char odds[8];
        odds[0] = 0;
        str_put_int(odds, pct);
        str_put(odds, "%");
        int x = 15 * 8 + 18 + 48 + text_width("RUN") + 3;
        text_draw_col(x, 120 + LINE_H, odds, INK_BLUE, INK_BLUE_SH);
    }
}

/* Which effectiveness tab a move shows against the current foe (-1 none). */
static int move_tab(int move)
{
    const Move *mv = &MOVES[move];
    int eff = type_effectiveness(mv->type, side_mon(SIDE_ENEMY)->species);
    if (mv->cat == CAT_STATUS) {
        if ((mv->effect == EF_STATUS || mv->effect == EF_FOE_STAT || mv->effect == EF_FOE_STATS) && eff == 0)
            return BL_NONE;
        return -1;
    }
    if (eff == 0) return BL_NONE;
    if (eff > 100) return BL_WEAK;
    if (eff < 100) return BL_RESIST;
    return -1;
}

static void draw_move_box(void)
{
    Monster *m = side_mon(SIDE_ALLY);
    canvas_window(0, 14, 22, 6, WIN_STD);
    canvas_window(22, 14, 8, 6, WIN_STD);
    for (int i = 0; i < MAX_MOVES; i++) {
        int x = 16 + (i & 1) * 80, y = 120 + (i >> 1) * LINE_H;
        text_draw_fit(x, y, m->moves[i] == MOVE_NONE ? "-" : MOVES[m->moves[i]].name, 72);
        if (i == battle.move_cursor) text_draw(x - 10, y, "{");
    }
    clear_tab();
    int mv = m->moves[battle.move_cursor];
    if (mv == MOVE_NONE) return;
    char buf[16];
    canvas_image(23, 15, 2, 1, bl_uses_gfx, 1, BANK_LABELS);
    buf[0] = 0;
    str_put_int(buf, m->pp[battle.move_cursor]);
    str_put(buf, "/");
    str_put_int(buf, MOVES[mv].pp);
    small_text_draw(230 - small_text_width(buf), 121, buf);
    draw_type_badge(24, 17, MOVES[mv].type);
    int tab = move_tab(mv);
    if (tab >= 0) canvas_image(22, 13, 8, 1, bl_tab_gfx[tab], 0, BANK_LABELS);
}

static void battle_redraw_ui(void)
{
    if (battle.state == BST_ACTION) draw_action_box();
    else if (battle.state == BST_MOVES) draw_move_box();
}

/* ---------------- lantern throw ---------------- */

#define LANTERN_ARC   22
#define LANTERN_OPEN  18
#define LANTERN_DROP  12
#define LANTERN_WOBBLE 32

static void lantern_update(BEvent *e)
{
    int t = battle.ev_timer, shakes = e->a;
    int ex = ENEMY_X + 32, ey = ENEMY_Y + 52;
    int top = ey - 36;
    battle.lantern_visible = 1;
    battle.lantern_frame = 0;
    battle.lantern_glow = 0;
    if (t == 1) sfx_play(SFX_THROW);
    if (t < LANTERN_ARC) {                               /* arc from the player's side */
        int k = t * 256 / LANTERN_ARC;
        battle.lantern_x = 24 + (ex - 24) * k / 256;
        battle.lantern_y = 104 + (top - 104) * k / 256 - soft_sin(k / 2) * 48 / 64;
        battle.lantern_frame = (t >> 2) & 1 ? 1 : 2;
        return;
    }
    t -= LANTERN_ARC;
    if (t < LANTERN_OPEN) {                              /* opens; the kin mode-matches in */
        battle.lantern_x = ex;
        battle.lantern_y = top;
        battle.lantern_frame = 3;
        battle.lantern_glow = 16 - t;
        if (t == 0) {
            sfx_play(SFX_SEND_OUT);
            part_add(PK_BIG_GROW, ex, top, 0, 0, FXB_GLOW, OBANK_LIGHT, 14, 0);
        }
        feel.flash[SIDE_ENEMY] = 6;
        battle.disp[SIDE_ENEMY].shrink = (t + 1) * 256 / LANTERN_OPEN;
        if (t == 0) battle.hud_dirty |= 1 << SIDE_ENEMY;
        if (t == LANTERN_OPEN - 1) {
            battle.disp[SIDE_ENEMY].visible = 0;
            battle.disp[SIDE_ENEMY].shrink = 0;
        }
        return;
    }
    t -= LANTERN_OPEN;
    if (t < LANTERN_DROP) {                              /* closes and drops to the ground */
        battle.lantern_x = ex;
        battle.lantern_y = top + (ey - top) * ease_in(t, LANTERN_DROP) / 256;
        if (t == LANTERN_DROP - 1) sfx_play(SFX_WOBBLE);
        return;
    }
    t -= LANTERN_DROP;
    battle.lantern_x = ex;
    battle.lantern_y = ey;
    int shown = shakes >= 4 ? 3 : shakes;
    int shake_i = t / LANTERN_WOBBLE, phase = t % LANTERN_WOBBLE;
    if (shake_i < shown) {
        if (phase == 8) sfx_play(SFX_WOBBLE);
        battle.lantern_frame = phase < 8 ? 0 : phase < 14 ? 1 : phase < 20 ? 2 : 0;
        battle.lantern_glow = phase >= 8 && phase < 20 ? 4 : 0;
        return;
    }
    int after = t - shown * LANTERN_WOBBLE;
    if (shakes >= 4) {                                   /* it settles: sparkles */
        battle.lantern_frame = 0;
        battle.lantern_glow = after < 30 ? 6 - after / 5 : 0;
        if (after == 0) {
            sfx_play(SFX_BEFRIEND);
            build_fx_palette(OBANK_FX_HIT, RGB15(31, 30, 18), RGB15(31, 22, 6));
            spark_burst(ex, ey - 6, 6, 26, FX_STAR, OBANK_FX_HIT);
        }
    } else {                                             /* it breaks free */
        battle.lantern_frame = 3;
        if (after == 0) {
            sfx_play(SFX_BREAK_FREE);
            part_add(PK_BIG_GROW, ex, ey - 8, 0, 0, FXB_GLOW, OBANK_LIGHT, 12, 0);
            battle.disp[SIDE_ENEMY].visible = 1;
            battle.disp[SIDE_ENEMY].pop = 1;
            battle.hud_dirty |= 1 << SIDE_ENEMY;
        }
        if (after > 8) battle.lantern_visible = 0;
    }
}

static int lantern_done(const BEvent *e)
{
    int shown = e->a >= 4 ? 3 : e->a;
    return battle.ev_timer >= LANTERN_ARC + LANTERN_OPEN + LANTERN_DROP + shown * LANTERN_WOBBLE + 34;
}

/* ---------------- the Hall Master's banner ---------------- */

/*
 * A band across the middle of the screen with the master's title, wiped in
 * from the left by WIN0 (per-scanline, like the intro iris), held, then
 * wiped out to the right. Sparkles ride the wipe's edge.
 */
#define BANNER_ROW   6
#define BANNER_ROWS  3
#define BANNER_Y0    (BANNER_ROW * 8)
#define BANNER_Y1    ((BANNER_ROW + BANNER_ROWS) * 8)
#define BANNER_IN    14
#define BANNER_HOLD  74
#define BANNER_OUT   14

static int banner_on, banner_l, banner_r;

static void banner_begin(const char *title)
{
    canvas_window(0, BANNER_ROW, CANVAS_COLS, BANNER_ROWS, WIN_BATTLE);
    text_draw_col(120 - text_width(title) / 2, BANNER_Y0 + 6, title, INK_RED, INK_RED_SH);
    banner_on = 1;
    banner_l = banner_r = 0;
    REG_WIN0V = SCREEN_HEIGHT;
    REG_WININ = 0x003F;           /* inside: everything */
    REG_WINOUT = 0x003D;          /* outside: all but the canvas (BG1) */
    REG_DISPCNT = (u16)(REG_DISPCNT | DCNT_WIN0);
    sfx_play(SFX_BANNER);
    feel.bright = 3;
}

static void banner_end(void)
{
    banner_on = 0;
    oam_line_win0h = 0;
    REG_DISPCNT = (u16)(REG_DISPCNT & ~DCNT_WIN0);
    canvas_clear_cells(0, BANNER_ROW, CANVAS_COLS, BANNER_ROWS);
}

/* Returns 1 when the banner is gone. */
static int banner_update(int t)
{
    if (t < BANNER_IN) {
        banner_l = 0;
        banner_r = 240 * ease_out(t + 1, BANNER_IN) / 256;
    } else if (t < BANNER_IN + BANNER_HOLD) {
        banner_l = 0;
        banner_r = 240;
    } else if (t < BANNER_IN + BANNER_HOLD + BANNER_OUT) {
        banner_l = 240 * ease_in(t - BANNER_IN - BANNER_HOLD + 1, BANNER_OUT) / 256;
        banner_r = 240;
    } else {
        banner_end();
        return 1;
    }
    return 0;
}

/* Sparkles along the wipe's moving edge (drawn with the other sprites). */
static void banner_draw(void)
{
    if (!banner_on) return;
    int edge = banner_r < 240 ? banner_r : banner_l > 0 ? banner_l : -1;
    for (int k = 0; k < 4; k++) {
        int y = BANNER_Y0 - 4 + ((k * 11 + (int)frame_count * 3) % (BANNER_Y1 - BANNER_Y0 + 8));
        if (edge >= 0) fx_spr_aff(edge + ((k & 1) ? 3 : -3), y, FX_SPARKLE, OBANK_LIGHT, 192 + k * 24, k * 40);
    }
    if (edge < 0 && (frame_count & 7) < 4)          /* held: two twinkles at the ends */
        for (int k = 0; k < 2; k++)
            fx_spr_aff(k ? 228 : 12, BANNER_Y0 + 12, FX_SPARKLE, OBANK_LIGHT, 256, (int)frame_count * 6);
}

/* ---------------- the warden's team row ---------------- */

/* A lantern per warden kin under the foe's HUD: lit = ready, dark = dozing. */
static int disp_foe_idx;   /* the warden kin the screen shows (set as it is sent out) */

static void team_row_draw(void)
{
    if (battle.kind != BK_TRAINER || battle.team_count < 1) return;
    if (!battle.disp[SIDE_ENEMY].visible && battle.state != BST_EVENTS) return;
    int x0 = HUD_ENEMY_CX * 8 + 6, y = HUD_ENEMY_CY * 8 + 33;
    for (int i = 0; i < battle.team_count; i++) {
        int awake = battle.team[i].hp > 0;
        /* the one on screen goes dark when its bar empties, not before */
        if (i == disp_foe_idx && battle.disp[SIDE_ENEMY].visible) awake = battle.disp[SIDE_ENEMY].hp > 0;
        spr_push(x0 + i * 9, y, OT_LANTERN_MINI + (awake ? 0 : 1), SQ8, OBANK_CAPSULE, 0, 0);
    }
}

/* ---------------- event playback ---------------- */

static void bev_pop(void)
{
    for (int i = 1; i < battle.ev_count; i++) battle.ev[i - 1] = battle.ev[i];
    battle.ev_count--;
    battle.ev_started = 0;
    battle.ev_timer = 0;
}

static void xp_level_up(int slot, int remaining)
{
    Monster *m = &party[slot];
    char msg[BEV_TEXT];
    monster_level_up(m);
    battle_leveled |= (u8)(1u << slot);
    int off = 0;
    str_copy(msg, SPECIES[m->species].name);
    str_put(msg, " reached Lv. ");
    str_put_int(msg, m->level);
    str_put(msg, "!");
    if (slot == battle.ally) bev_insert_next(EV_SYNC, SIDE_ALLY, 0, 0, off++);
    bev_insert_next(EV_SFX, 0, SFX_LEVEL_UP, 0, off++);
    BEvent *t = bev_insert_next(EV_TEXT, 0, MSGM_WAIT, 0, off++);
    str_copy(t->text, msg);
    u8 moves[4];
    int n = learnset_at(m->species, m->level, moves);
    for (int i = 0; i < n; i++) bev_insert_next(EV_LEARN, SIDE_ALLY, slot, moves[i], off++);
    if (remaining > 0) bev_insert_next(EV_XP, SIDE_ALLY, slot, remaining, off++);
}

/* Pop-in scale of a kin being sent out (8.8): 0 -> 1.12 -> 1.0. */
static int pop_scale(int t)
{
    if (t < 10) return 270 * ease_out(t + 1, 11) / 256 + 16;
    if (t < 18) return 286 - (t - 10) * 30 / 8;
    return 256;
}
#define POP_LEN 18

#define SEND_OUT_LEN 32
#define SEND_OUT_OPEN 12

/* Returns 1 when the event is finished. */
static int bev_run(BEvent *e)
{
    int side = e->side;
    if (!battle.ev_started) {
        battle.ev_started = 1;
        battle.ev_timer = 0;
        switch (e->type) {
        case EV_TEXT:
            battle.impacted = 0;
            msg_start(e->text, WIN_BATTLE, e->a);
            if (battle.ev_count > 1 && battle.ev[1].type == EV_ANIM) msg.hold = opt.battle_speed ? 4 : 8;
            else msg.hold = opt.battle_speed ? 15 : 30;
            break;
        case EV_BANNER:
            banner_begin(e->text);
            break;
        case EV_LEGEND:
            anim_start_legend(side);
            break;
        case EV_CUE:
            battle_cue(e->a);
            return 1;
        case EV_ANIM:
            anim_start(e->a, side, e->b);
            break;
        case EV_HIT:
            if (battle.impacted == side + 1) {   /* the animation already landed it */
                battle.impacted = 0;
                return 1;
            }
            anim_start_react(side, e->a);
            break;
        case EV_STAT:
            anim_start_stat(side, e->a > 0);
            break;
        case EV_STATUS:
            battle.disp[side].status = e->a;
            battle.hud_dirty |= 1 << side;
            anim_start_status(side, e->a, e->b);
            break;
        case EV_TRAIT:
            anim_start_trait(side);
            break;
        case EV_HP: {
            int from = battle.disp[side].hp, to = e->a;
            int max = battle.disp[side].max_hp > 0 ? battle.disp[side].max_hp : 1;
            battle.disp[side].hp_from = from;
            battle.disp[side].hp_t = 0;
            battle.disp[side].hp_dur = 10 + absi(to - from) * 34 / max;
            if (to < from) {
                battle.disp[side].jolt = 10;
                if (battle.disp[side].trail < from) battle.disp[side].trail = from;
                battle.disp[side].trail_hold = battle.disp[side].hp_dur + 12;
            } else {
                sfx_play(SFX_SPARKLE);
            }
            break;
        }
        case EV_SEND_OUT:
            if (side == SIDE_ALLY) battle.ally = e->a;
            else battle.team_idx = disp_foe_idx = e->a;
            battle_load_mon_gfx(side);
            if (side == SIDE_ENEMY) dex_seen[battle.team[e->a].species] = 1;
            disp_sync(side);
            battle.disp[side].visible = 1;
            battle.disp[side].fade = 0;
            battle.disp[side].drop = 0;
            battle.disp[side].slide = 0;
            battle.disp[side].pop = 0;
            battle.disp[side].shrink = 0;
            battle.disp[side].inlantern = !e->b;   /* b: already in view (wild intro) */
            battle.hud_dirty |= 1 << side;
            if (e->b) {
                anim_begin(ANIM_TRAIT, side);        /* a brimming shimmer */
                anim.dur = 24;
                anim.tint_color = TYPE_TINT[SPECIES[battle.disp[side].species].type1];
                build_fx_palette(OBANK_FX_A, anim.tint_color, RGB15(31, 31, 31));
                if (battle.disp[side].lustrous) {    /* a rare hue: it sparkles */
                    build_fx_palette(OBANK_FX_HIT, RGB15(31, 31, 20), RGB15(20, 31, 31));
                    spark_burst(side_cx(side), side_cy(side), 8, 28, FX_SPARKLE, OBANK_FX_HIT);
                    sfx_play(SFX_SPARKLE);
                }
            }
            break;
        case EV_LANTERN:
            battle.lantern_kind = clampi(e->b, 0, 2);
            break;
        case EV_FAINT:
            sfx_play(SFX_DOZE);
            feel.flash[side] = 8;
            squash(side, 236, 280);
            break;
        case EV_FLEE:
            sfx_play(SFX_RUN);
            break;
        case EV_WITHDRAW:
            sfx_play(SFX_THROW);
            break;
        case EV_SFX:
            sfx_play(e->a);
            return 1;
        case EV_SYNC:
            disp_sync(side);
            return 1;
        case EV_MONEY:
            money = clampi(money + e->a, 0, 999999);
            sfx_play(SFX_BUY);
            return 1;
        case EV_END:
            battle.result = e->a;
            battle.state = BST_END;
            battle.timer = 0;
            return 1;
        case EV_LEARN: {
            Monster *m = &party[e->a];
            if (monster_knows(m, e->b)) return 1;
            if (monster_add_move(m, e->b)) {
                BEvent *t = bev_insert_next(EV_TEXT, 0, MSGM_WAIT, 0, 0);
                str_copy(t->text, SPECIES[m->species].name);
                str_put(t->text, " learned ");
                str_put(t->text, MOVES[e->b].name);
                str_put(t->text, "!");
                return 1;
            }
            learn_begin(e->a, e->b);
            break;
        }
        case EV_XP:
            if (e->a != battle.ally) {
                /* the rest of the team levels instantly */
                Monster *m = &party[e->a];
                u32 target = m->xp + (u32)e->b;
                if (m->level < MAX_LEVEL && target >= xp_for_level(m->level + 1)) {
                    int rem = (int)(target - xp_for_level(m->level + 1));
                    m->xp = xp_for_level(m->level + 1);
                    xp_level_up(e->a, rem);
                } else {
                    m->xp = target;
                }
                return 1;
            }
            break;
        default:
            break;
        }
    }
    battle.ev_timer++;
    int t = battle.ev_timer;
    switch (e->type) {
    case EV_TEXT:
        msg_update();
        return msg.state == MSG_DONE;
    case EV_ANIM:
    case EV_STAT:
    case EV_STATUS:
    case EV_TRAIT:
    case EV_HIT:
    case EV_LEGEND:
        return !anim_busy();
    case EV_BANNER:
        return banner_update(t);
    case EV_HP: {
        int *hp = &battle.disp[side].hp;
        battle.disp[side].hp_t++;
        int k = ease_out(battle.disp[side].hp_t, battle.disp[side].hp_dur);
        int v = battle.disp[side].hp_from + (e->a - battle.disp[side].hp_from) * k / 256;
        if (v != *hp) {
            *hp = v;
            battle.hud_dirty |= 4 << side;
        }
        if (battle.disp[side].hp_t >= battle.disp[side].hp_dur) {
            *hp = e->a;
            if (e->a > battle.disp[side].trail) battle.disp[side].trail = e->a;
            battle.hud_dirty |= 4 << side;
            return 1;
        }
        return 0;
    }
    case EV_FAINT:
        if (t < 8) return 0;
        battle.disp[side].fade = clampi((t - 8) * 16 / 22, 1, 16);
        battle.disp[side].drop = (t - 8) * (t - 8) / 20;
        if (t == 8) battle.hud_dirty |= 1 << side;
        if (t >= 30) {
            battle.disp[side].visible = 0;
            battle.disp[side].drop = 0;
            battle.disp[side].fade = 0;
            battle.hud_dirty |= 1 << side;
            return 1;
        }
        return 0;
    case EV_SEND_OUT: {
        if (e->b) return t >= 24;                       /* wild: already there */
        /* the lantern arcs in, opens with a burst of light, the kin pops out */
        int from_x = side == SIDE_ALLY ? -8 : 248, from_y = side == SIDE_ALLY ? 120 : 20;
        int cx = side_cx(side), cy = side_cy(side) - 12;
        if (t < SEND_OUT_OPEN) {
            int k = t * 256 / SEND_OUT_OPEN;
            battle.lantern_visible = 1;
            battle.lantern_kind = 0;
            battle.lantern_x = from_x + (cx - from_x) * k / 256;
            battle.lantern_y = from_y + (cy - from_y) * k / 256 - soft_sin(k / 2) * 30 / 64;
            battle.lantern_frame = (t >> 2) & 1 ? 1 : 2;
            battle.lantern_glow = 0;
            if (t == 1) sfx_play(SFX_THROW);
            return 0;
        }
        int it = t - SEND_OUT_OPEN;
        battle.lantern_x = cx;
        battle.lantern_y = cy;
        battle.lantern_frame = 3;
        battle.lantern_glow = 16 - it;
        battle.lantern_visible = it < 8;
        if (it == 0) {
            sfx_play(SFX_SEND_OUT);
            part_add(PK_BIG_GROW, cx, cy + 8, 0, 0, FXB_GLOW, OBANK_LIGHT, 14, 0);
            feel.bright = 3;
            if (battle.disp[side].lustrous) {
                build_fx_palette(OBANK_FX_HIT, RGB15(31, 31, 20), RGB15(20, 31, 31));
                spark_burst(cx, cy + 10, 8, 28, FX_SPARKLE, OBANK_FX_HIT);
                sfx_play(SFX_SPARKLE);
            }
        }
        if (it == 0) {
            battle.disp[side].inlantern = 0;
            battle.disp[side].pop = 1;
        }
        feel.flash[side] = it < 6 ? 6 - it : 0;
        if (it >= SEND_OUT_LEN - SEND_OUT_OPEN) {
            battle.lantern_visible = 0;
            battle.hud_dirty |= 1 << side;
            return 1;
        }
        return 0;
    }
    case EV_WITHDRAW:
        feel.flash[side] = 8;
        battle.disp[side].shrink = t * 256 / 14;
        if (t == 1) battle.hud_dirty |= 1 << side;
        if (t >= 14) {
            battle.disp[side].visible = 0;
            battle.disp[side].shrink = 0;
            battle.hud_dirty |= 1 << side;
            return 1;
        }
        return 0;
    case EV_FLEE:
        battle.disp[SIDE_ALLY].slide = -ease_in(t, 14) * 90 / 256;
        return t >= 16;
    case EV_LANTERN:
        lantern_update(e);
        if (lantern_done(e)) {
            battle.lantern_visible = e->a >= 4;
            return 1;
        }
        return 0;
    case EV_LEARN:
        return !dialog_update();
    case EV_XP: {
        Monster *m = &party[e->a];
        if (m->level >= MAX_LEVEL || e->b <= 0) return 1;
        u32 next = xp_for_level(m->level + 1);
        u32 span = next - xp_for_level(m->level);
        int step = (int)(span / 48) + 1;
        int give = step < e->b ? step : e->b;
        if (m->xp + (u32)give >= next) {
            int used = (int)(next - m->xp);
            m->xp = next;
            battle.disp_xp = m->xp;
            battle.hud_dirty |= 1 << SIDE_ALLY;
            xp_level_up(e->a, e->b - used);
            return 1;
        }
        m->xp += (u32)give;
        e->b = (s16)(e->b - give);
        battle.disp_xp = m->xp;
        battle.hud_dirty |= 1 << SIDE_ALLY;
        return e->b <= 0;
    }
    default:
        return 1;
    }
}

static void battle_events_update(void)
{
    while (battle.state == BST_EVENTS) {
        if (battle.ev_count == 0) {
            int next = battle.return_state;
            battle.return_state = BST_ACTION;
            battle.state = next;
            if (next == BST_FORCED) {
                party_screen_open(PCTX_BATTLE_FORCED, 0);
                return;
            }
            battle.ui_dirty = 1;
            return;
        }
        BEvent *e = &battle.ev[0];
        int was_started = battle.ev_started;
        if (!bev_run(e)) return;
        if (battle.state != BST_EVENTS) {
            bev_pop();
            return;
        }
        bev_pop();
        /* instant events chain within one frame; timed ones wait a frame */
        if (was_started) return;
    }
}

static void battle_play(void)
{
    battle.state = BST_EVENTS;
    battle.ev_started = 0;
}

/* ---------------- setup ---------------- */

static void battle_apply_scene_tint(int amount16, u16 color)
{
    amount16 = clampi(amount16, 0, 256);
    for (int b = 0; b < 4; b++)
        for (int i = 1; i < 16; i++)
            bg_palette[(BANK_SCENE + b) * 16 + i] =
                amount16 ? mix15_sh(scene_pal[b][i], color, amount16, 8) : scene_pal[b][i];
    bg_palette[0] = amount16 ? mix15_sh(scene_pal[0][1], color, amount16, 8) : scene_pal[0][1];
    scene_tint_applied = amount16;
    scene_tint_color = color;
}

static void battle_load_scene(void)
{
    int sc = clampi(battle.scene, 0, BBG_SCENE_COUNT - 1);
    const BattleSceneArt *a = &bbg_scenes[sc];
    copy32(VRAM_SCENE_TILES, a->tiles, (unsigned)a->tile_count * 8);
    u16 *dst = VRAM_MAP(SB_FIELD_BOTTOM);
    for (int i = 0; i < 20 * 32; i++) dst[i] = a->map[i];
    for (int i = 20 * 32; i < 32 * 32; i++) dst[i] = a->map[19 * 32];
    for (int b = 0; b < 4; b++) copy16(scene_pal[b], a->pal[b], 16);
    battle_apply_scene_tint(0, 0);
    hud_load_palettes();
    REG_BG0HOFS = 0;
    REG_BG0VOFS = 0;
    REG_BG0CNT = BGCNT_CHARBLOCK(0) | BGCNT_SCREENBLOCK(SB_FIELD_BOTTOM) | BGCNT_PRIO(3) | 0x0040;
    REG_DISPCNT = DCNT_MODE0 | DCNT_BG0 | DCNT_BG1 | DCNT_OBJ | DCNT_OBJ_1D;
    copy32(VRAM_OBJ_TILES + OT_FX * 8, fx_gfx, FX_COUNT * 4 * 8);
    copy32(VRAM_OBJ_TILES + OT_FX_BIG * 8, fx_big_gfx, FXB_COUNT * 16 * 8);
    copy32(VRAM_OBJ_TILES + OT_LANTERN_MINI * 8, lantern_mini_gfx, 8);
    copy32(VRAM_OBJ_TILES + OT_CAPSULE * 8, capsule_gfx, 4 * 4 * 8);
    build_fx_palette(OBANK_LIGHT, RGB15(31, 22, 8), RGB15(31, 31, 24));
}

static void battle_reset(int kind)
{
    battle.kind = kind;
    battle.ev_count = 0;
    battle.ev_started = 0;
    battle.result = BR_NONE;
    battle.return_state = BST_ACTION;
    battle.cursor = 0;
    battle.move_cursor = 0;
    battle.escape_tries = 0;
    battle.team_idx = 0;
    battle.turn = 0;
    battle.lantern_visible = 0;
    battle.hud_dirty = 3;
    battle.ui_dirty = 0;
    battle.impacted = 0;
    battle.scene = clampi(battle_next_scene, 0, BSCENE_COUNT - 1);
    battle.foe_title[0] = 0;
    battle.lose_line = 0;
    battle_leveled = 0;
    for (int i = 0; i < 6; i++) battle.move_cursor_of[i] = 0;
    for (int s = 0; s < 2; s++) {
        battle.flinch[s] = 0;
        for (int i = 0; i < STAT_COUNT; i++) battle.stages[s][i] = 0;
        battle.disp[s].visible = 0;
        battle.disp[s].drop = 0;
        battle.disp[s].slide = 0;
        battle.disp[s].blink = 0;
        battle.disp[s].pop = 0;
        battle.disp[s].fade = 0;
        battle.disp[s].jolt = 0;
        battle.disp[s].caught = 0;
    }
    battle.ally = party_first_healthy();
    if (battle.ally < 0) battle.ally = 0;
    battle.participants = (u8)(1u << battle.ally);
    battle.fought = battle.participants;
    battle.state = BST_INTRO;
    battle.timer = 0;
    anim_clear();
    if (game_mode != MODE_BATTLE) copy16(saved_light_bank, obj_palette + OBANK_LIGHT * 16, 16);
    game_mode = MODE_BATTLE;
}

static void battle_queue_intro(void)
{
    char msg[BEV_TEXT];
    if (battle.kind == BK_WILD) {
        bev_push(EV_SEND_OUT, SIDE_ENEMY, 0, 1);
        str_copy(msg, "A brimming ");
        str_put(msg, SPECIES[battle.team[0].species].name);
        str_put(msg, " wants a bout!");
        bsay_wait(msg);
    } else {
        str_copy(msg, battle.foe_title);
        str_put(msg, " wants a bout!");
        bsay_wait(msg);
        str_copy(msg, battle.foe_title);
        str_put(msg, " sent out ");
        str_put(msg, SPECIES[battle.team[0].species].name);
        str_put(msg, "!");
        bsay(msg);
        bev_push(EV_SEND_OUT, SIDE_ENEMY, 0, 0);
    }
    str_copy(msg, "Out you come, ");
    str_put(msg, SPECIES[party[battle.ally].species].name);
    str_put(msg, "!");
    bsay(msg);
    bev_push(EV_SEND_OUT, SIDE_ALLY, battle.ally, 0);
    entry_traits(SIDE_ENEMY);
    entry_traits(SIDE_ALLY);
}

static void battle_start_wild(Monster wild)
{
    battle_reset(BK_WILD);
    battle.team[0] = wild;
    battle.team_count = 1;
    battle.prize = 0;
    dex_seen[wild.species] = 1;
}

static void battle_set_title(const char *name)
{
    int spaced = 0;
    for (const char *c = name; *c; c++)
        if (*c == ' ') spaced = 1;
    battle.foe_title[0] = 0;
    if (!spaced) str_copy(battle.foe_title, "WARDEN ");
    if (str_len(battle.foe_title) + str_len(name) < sizeof(battle.foe_title))
        str_put(battle.foe_title, name);
}

static void battle_start_trainer_team(const TrainerTeam *t)
{
    battle_reset(BK_TRAINER);
    int n = clampi(t->count, 1, TEAM_MAX);
    for (int i = 0; i < n; i++) battle.team[i] = monster_make(t->species[i], t->level[i]);
    battle.team_count = n;
    battle.prize = t->prize;
    battle_set_title(t->name ? t->name : "WARDEN");
    battle.lose_line = t->lose_line;
    battle.scene = t->scene == BSCENE_AREA ? clampi(battle_next_scene, 0, BSCENE_COUNT - 1) :
                   clampi(t->scene, 0, BSCENE_COUNT - 1);
}

static const u8 TRAINER_POOL[] = {
    SP_PYREFOX, SP_AXOLURK, SP_PUFFLEECE, SP_CINDERUB, SP_BUBBLIN, SP_THORNIP,
    SP_MOSSHELL, SP_ZAPPET, SP_VOLTUX, SP_GOLEMIT, SP_PUFFOWL, SP_SKYWISP,
    SP_NIBBIT, SP_FROSTOAT, SP_WISPIRE,
};

/* The stage a species has reached by `level` (level growths only). */
static int battle_grown_species(int sp, int level)
{
    for (int guard = 0; guard < 3; guard++) {
        const Species *s = &SPECIES[sp];
        if (s->evo_kind != EVO_LEVEL || level < s->evo_param + 3) break;
        sp = s->evo_into;
    }
    return sp;
}

/* WARDEN MARLO at the Bout Ring: a random team around your level. */
static void battle_start_trainer(void)
{
    static TrainerTeam marlo;
    int top = party_max_level();
    marlo.name = "WARDEN MARLO";
    marlo.count = (u8)(top < 8 ? 2 : 3);
    int best = 1;
    for (int i = 0; i < marlo.count; i++) {
        int sp = TRAINER_POOL[rng_range(sizeof(TRAINER_POOL))];
        int level = clampi(top - 1 + (int)rng_range(3), 4, 70);
        marlo.species[i] = (u8)battle_grown_species(sp, level);
        marlo.level[i] = (u8)level;
        if (level > best) best = level;
    }
    marlo.prize = (u16)(best * 60);
    marlo.scene = BSCENE_RING;
    marlo.lose_line = "MARLO: Ha! Now that's a bout. Come back any time!";
    battle_start_trainer_team(&marlo);
}

/* ---------------- exit ---------------- */

static void battle_lines_off(void)
{
    oam_line_win0h = 0;
    oam_line_bg0 = 0;
    oam_line_bg1 = 0;
}

static void battle_exit(void)
{
    dialog_style = WIN_STD;
    set_brightness(0);
    REG_MOSAIC = 0;
    REG_DISPCNT = (u16)(REG_DISPCNT & ~DCNT_WIN0);
    anim_clear();
    battle_lines_off();
    copy16(obj_palette + OBANK_LIGHT * 16, saved_light_bank, 16);
    battle.lantern_visible = 0;
    if (battle.result == BR_LOSE) {
        party_heal_all();
        field_enter_map(MAP_REST, 5, 4, DIR_UP);
    }
    for (int i = 0; i < party_count; i++) {
        if (!(battle_leveled & (1u << i))) continue;
        int into = monster_level_evolution(&party[i]);
        if (into >= 0) evo_request(i, into);
    }
    void (*hook)(int) = battle_end_hook;
    battle_end_hook = 0;
    battle.no_run = 0;
    if (hook) hook(battle.result);
    field_return();
}

/* ---------------- input ---------------- */

static void battle_action_input(void)
{
    int old = battle.cursor;
    if (key_hit(KEY_LEFT) && (battle.cursor & 1)) battle.cursor--;
    if (key_hit(KEY_RIGHT) && !(battle.cursor & 1)) battle.cursor++;
    if (key_hit(KEY_UP) && (battle.cursor & 2)) battle.cursor -= 2;
    if (key_hit(KEY_DOWN) && !(battle.cursor & 2)) battle.cursor += 2;
    if (old != battle.cursor) {
        battle.ui_dirty = 1;
        sfx_play(SFX_CURSOR);
    }
    if (key_hit(KEY_L)) {                     /* quick-throw the best lantern */
        int item = battle_best_lantern();
        if (battle.kind == BK_TRAINER) {
            sfx_play(SFX_ERROR);
            battle_throw_lantern(item >= 0 ? item : ITEM_LANTERN);
        } else if (item < 0) {
            sfx_play(SFX_ERROR);
            bsay_wait("You don't have any lanterns!");
            battle.return_state = BST_ACTION;
            battle_play();
        } else {
            sfx_play(SFX_CONFIRM);
            battle_throw_lantern(item);
        }
        return;
    }
    if (!key_hit(KEY_A)) return;
    sfx_play(SFX_CONFIRM);
    switch (battle.cursor) {
    case 0: {
        Monster *m = side_mon(SIDE_ALLY);
        int c = battle.move_cursor_of[battle.ally] & 3;
        battle.move_cursor = m->moves[c] != MOVE_NONE ? c : 0;
        battle.state = BST_MOVES;
        battle.ui_dirty = 1;
        break;
    }
    case 1:
        battle_lines_off();
        bag_screen_open(BAGCTX_BATTLE);
        break;
    case 2:
        battle_lines_off();
        party_screen_open(PCTX_BATTLE_SWITCH, 0);
        break;
    case 3:
        battle_try_run();
        break;
    }
}

static void battle_moves_input(void)
{
    Monster *m = side_mon(SIDE_ALLY);
    int old = battle.move_cursor, c = battle.move_cursor;
    if (key_hit(KEY_LEFT) && (c & 1)) c--;
    if (key_hit(KEY_RIGHT) && !(c & 1)) c++;
    if (key_hit(KEY_UP) && (c & 2)) c -= 2;
    if (key_hit(KEY_DOWN) && !(c & 2)) c += 2;
    if (m->moves[c] != MOVE_NONE) battle.move_cursor = c;
    if (old != battle.move_cursor) {
        battle.ui_dirty = 1;
        sfx_play(SFX_CURSOR);
    }
    if (key_hit(KEY_B)) {
        sfx_play(SFX_CANCEL);
        battle.state = BST_ACTION;
        battle.ui_dirty = 1;
        return;
    }
    if (key_hit(KEY_A)) {
        sfx_play(SFX_CONFIRM);
        clear_tab();
        battle_player_move(battle.move_cursor);
    }
}

/* Menus may have borrowed the kin sprite slots (e.g. a summary). */
static void battle_reload_gfx(void)
{
    battle_load_mon_gfx(SIDE_ENEMY);
    battle_load_mon_gfx(SIDE_ALLY);
    copy32(VRAM_OBJ_TILES + OT_FX_BIG * 8, fx_big_gfx, FXB_COUNT * 16 * 8);
    copy32(VRAM_OBJ_TILES + OT_LANTERN_MINI * 8, lantern_mini_gfx, 8);
    hud_load_palettes();
    battle_apply_scene_tint(0, 0);
    build_fx_palette(OBANK_LIGHT, RGB15(31, 22, 8), RGB15(31, 31, 24));
    REG_DISPCNT = DCNT_MODE0 | DCNT_BG0 | DCNT_BG1 | DCNT_OBJ | DCNT_OBJ_1D;
}

/* Called by the party screen. slot < 0 = cancelled. */
static void battle_party_result(int slot, int forced)
{
    game_mode = MODE_BATTLE;
    canvas_clear();
    battle_reload_gfx();
    battle.hud_dirty = 3;
    if (slot < 0 || slot == battle.ally || party[slot].hp == 0) {
        battle.state = forced ? BST_FORCED : BST_ACTION;
        battle.ui_dirty = 1;
        if (forced) party_screen_open(PCTX_BATTLE_FORCED, 0);
        return;
    }
    battle.state = BST_ACTION;
    battle_switch_to(slot, forced);
}

/* Called by the bag/party screens after choosing an item (and target). */
static void battle_item_result(int item, int target)
{
    game_mode = MODE_BATTLE;
    canvas_clear();
    battle_reload_gfx();
    battle.hud_dirty = 3;
    battle.state = BST_ACTION;
    battle.ui_dirty = 1;
    if (item < 0) return;
    if (!battle_use_item(item, target)) {
        bsay_wait("It won't have any effect.");
        battle.return_state = BST_ACTION;
        battle_play();
    }
}

/* ---------------- intro: the lantern-light wipe ---------------- */

static void intro_update(void)
{
    int t = ++battle.timer;
    if (t == 1) {
        sfx_play(SFX_WIPE);
        REG_BG0CNT = (u16)(REG_BG0CNT | 0x0040);
        REG_BG2CNT = (u16)(REG_BG2CNT | 0x0040);
        REG_BG3CNT = (u16)(REG_BG3CNT | 0x0040);
    }
    if (t <= INTRO_DARK) {
        /* the field dissolves into night */
        int m = t * 9 / INTRO_DARK;
        REG_MOSAIC = (u16)(m | (m << 4));
        set_brightness(-(ease_in(t, INTRO_DARK) * 16 / 256));
        return;
    }
    if (t == INTRO_DARK + 1) {
        REG_MOSAIC = 0;
        canvas_clear();
        battle_load_scene();
        dialog_style = WIN_BATTLE;
        canvas_window(0, 14, CANVAS_COLS, 6, WIN_BATTLE);
        if (battle.kind == BK_WILD) {
            battle_load_mon_gfx(SIDE_ENEMY);
            disp_sync(SIDE_ENEMY);
            battle.disp[SIDE_ENEMY].visible = 1;
            battle.disp[SIDE_ENEMY].pop = 0;
            battle.disp[SIDE_ENEMY].inlantern = 0;
            battle.hud_dirty &= ~(1 << SIDE_ENEMY);
        }
        REG_WIN0V = SCREEN_HEIGHT;
        REG_WININ = 0x001F;          /* inside the light: everything, no darkening */
        REG_WINOUT = 0x003F;         /* outside: everything, darkened */
        REG_DISPCNT = (u16)(REG_DISPCNT | DCNT_WIN0);
        return;
    }
    if (t > INTRO_DARK + 1 + INTRO_OPEN) {
        REG_DISPCNT = (u16)(REG_DISPCNT & ~DCNT_WIN0);
        oam_line_win0h = 0;
        battle_apply_scene_tint(0, 0);
        battle_queue_intro();
        battle_play();
    }
}

/* Radius of the intro light at this frame, or -1 when not in the iris. */
static int intro_radius(void)
{
    if (battle.state != BST_INTRO || battle.timer <= INTRO_DARK) return -1;
    int t = battle.timer - INTRO_DARK - 1;
    return 4 + ease_out(t, INTRO_OPEN) * 150 / 256;
}

static void battle_update(void)
{
    switch (battle.state) {
    case BST_INTRO:
        intro_update();
        break;
    case BST_EVENTS:
        battle_events_update();
        break;
    case BST_ACTION:
        battle_action_input();
        break;
    case BST_MOVES:
        battle_moves_input();
        break;
    case BST_END:
        battle.timer++;
        if (battle.timer >= 16) battle_exit();
        break;
    default:
        break;
    }
}

/* ---------------- drawing ---------------- */

static int isqrt_small(int v)
{
    int r = 0, bit = 1 << 16;
    while (bit > v) bit >>= 2;
    while (bit) {
        if (v >= r + bit) {
            v -= r + bit;
            r = (r >> 1) + bit;
        } else {
            r >>= 1;
        }
        bit >>= 2;
    }
    return r;
}

/* Repeat the first 160 entries so a missed re-arm reads the same lines. */
static void lines_repeat32(u32 *t)
{
    for (int k = 1; k < LINE_COPIES; k++) {
        t[k * SCREEN_HEIGHT] = t[0];
        for (int y = 1; y < SCREEN_HEIGHT; y++) t[k * SCREEN_HEIGHT + y] = t[y];
    }
    t[LINE_COPIES * SCREEN_HEIGHT] = t[0];
}

static void lines_repeat16(u16 *t)
{
    for (int k = 1; k < LINE_COPIES; k++)
        for (int y = 0; y < SCREEN_HEIGHT; y++) t[k * SCREEN_HEIGHT + y] = t[y];
    t[LINE_COPIES * SCREEN_HEIGHT] = t[0];
}

static void battle_draw_lines(void)
{
    u32 *b0 = line_bg0[line_buf], *b1 = line_bg1[line_buf];
    int w = anim.wobble;
    for (int y = 0; y < SCREEN_HEIGHT; y++) {
        int hx = -shake_x, vy = -shake_y;
        if (w) hx += soft_sin(y * 6 + (int)frame_count * 10) * w / 64;
        b0[y] = (u32)(hx & 0x1FF) | ((u32)(vy & 0x1FF) << 16);
    }
    for (int s = 0; s < 2; s++) {
        int j = battle.disp[s].jolt;
        int jx = j ? ((j & 2) ? 1 : -1) * (j + 2) / 4 : 0;
        int jy = j > 5 ? ((j & 1) ? 1 : 0) : 0;
        int y0 = s == SIDE_ENEMY ? 4 : 60, y1 = s == SIDE_ENEMY ? 46 : 110;
        if (s == SIDE_ENEMY) for (int y = 0; y < y0; y++) b1[y] = 0;
        else for (int y = 46; y < y0; y++) b1[y] = 0;
        for (int y = y0; y < y1; y++) b1[y] = (u32)(-jx & 0x1FF) | ((u32)(-jy & 0x1FF) << 16);
    }
    for (int y = 110; y < SCREEN_HEIGHT; y++) b1[y] = 0;
    lines_repeat32(b0);
    lines_repeat32(b1);
    oam_line_bg0 = b0;
    oam_line_bg1 = b1;
    int r = intro_radius();
    if (r >= 0) {
        u16 *wl = line_win[line_buf];
        int cx = 120, cy = 58;
        for (int y = 0; y < SCREEN_HEIGHT; y++) {
            int d = y - cy, h2 = r * r - d * d;
            if (h2 <= 0) {
                wl[y] = 0;
                continue;
            }
            int h = isqrt_small(h2);
            int l = clampi(cx - h, 0, 240), rr = clampi(cx + h, 0, 240);
            wl[y] = (u16)((l << 8) | rr);
        }
        lines_repeat16(wl);
        oam_line_win0h = wl;
    }
    line_buf ^= 1;
}

/* Palettes of both kin: base (lustre) -> move tint -> white flash. */
static void battle_draw_palettes(void)
{
    for (int side = 0; side < 2; side++) {
        u16 *dst = obj_palette + (side == SIDE_ENEMY ? OBANK_MON_A : OBANK_MON_B) * 16;
        int tint = anim.active && anim.tint_side == side ? anim.tint_amount : 0;
        int flash = clampi(feel.flash[side] * 3, 0, 16);
        const u16 *src = battle.disp[side].pal;
        if (!tint && !flash) {
            copy16(dst + 1, src + 1, 15);
            continue;
        }
        for (int i = 1; i < 16; i++) {
            u16 c = src[i];
            if (tint) c = mix15_sh(c, anim.tint_color, clampi(tint, 0, 16), 4);
            if (flash) c = mix15_sh(c, RGB15(31, 31, 31), flash, 4);
            dst[i] = c;
        }
    }
}

static void battle_draw_battlers(void)
{
    trail_head = (trail_head + 1) & 7;
    for (int side = 0; side < 2; side++) {
        if (battle.disp[side].pop > 0 && ++battle.disp[side].pop > POP_LEN) battle.disp[side].pop = 0;
        if (!battle.disp[side].visible || battle.disp[side].inlantern || anim.hide[side]) continue;
        int base_x = side == SIDE_ENEMY ? ENEMY_X : ALLY_X, base_y = side == SIDE_ENEMY ? ENEMY_Y : ALLY_Y;
        int x = base_x + battle.disp[side].slide + anim.mon_dx[side] + feel.kb[side] / 16 + shake_x;
        int y = base_y + battle.disp[side].drop + anim.mon_dy[side] + shake_y;
        int sx = feel.sx[side] * anim.scale_x[side] / 256;
        int sy = feel.sy[side] * anim.scale_y[side] / 256;
        /* idle breathing */
        if (battle.disp[side].fade == 0) sy = sy * (256 + soft_sin((int)frame_count * 3 + side * 90) / 16) / 256;
        if (battle.disp[side].pop > 0) {
            int ps = pop_scale(battle.disp[side].pop - 1);
            sx = sx * ps / 256;
            sy = sy * ps / 256;
        }
        if (battle.disp[side].shrink) {
            int k = 256 - battle.disp[side].shrink;   /* shrinking into a lantern */
            sx = sx * k / 256;
            sy = sy * k / 256;
            if (battle.ev_count && battle.ev[0].type == EV_LANTERN) {
                x += (battle.lantern_x - 32 - x) * (256 - k) / 256;
                y += (battle.lantern_y - 32 - y) * (256 - k) / 256;
            }
        }
        if (battle.disp[side].fade) {
            int f = battle.disp[side].fade;
            sx = sx * (256 - f * 5) / 256;
            sy = sy * (256 - f * 7) / 256;
        }
        if (sx < 4 || sy < 4) continue;
        /* keep the feet planted: scale about the bottom of the sprite */
        int anchor = side == SIDE_ENEMY ? 26 : 32;
        y += anchor * (256 - sy) / 256;
        int aff = oam_affine_scale_rot(sx, sy, 0);
        int flags = battle.disp[side].fade ? ATTR0_BLEND : 0;
        if (anim.mosaic) flags |= SPR_MOSAIC;
        int tile = side == SIDE_ENEMY ? OT_MON_A : OT_MON_B;
        int bank = side == SIDE_ENEMY ? OBANK_MON_A : OBANK_MON_B;
        trail_x[side][trail_head] = (s16)x;
        trail_y[side][trail_head] = (s16)y;
        spr_push_affine(x, y, tile, SQ64, bank, 1, flags, aff, 1);
        if (anim.afterimage && anim.side == side)
            for (int k = 3; k <= 6; k += 3) {
                int i = (trail_head - k) & 7;
                spr_push_affine(trail_x[side][i], trail_y[side][i], tile, SQ64, bank, 1, ATTR0_BLEND, aff, 1);
            }
    }
}

static void battle_draw(void)
{
    if (battle.state == BST_INTRO && battle.timer <= INTRO_DARK) {
        field_draw_sprites();
        return;
    }
    if (battle.ui_dirty) {
        battle_redraw_ui();
        battle.ui_dirty = 0;
    }
    /* HUD: full redraws when needed, bar-only while HP moves */
    for (int side = 0; side < 2; side++) {
        int *tr = &battle.disp[side].trail, hp = battle.disp[side].hp;
        if (*tr > hp) {
            if (battle.disp[side].trail_hold > 0) {
                battle.disp[side].trail_hold--;
            } else {
                *tr -= (*tr - hp) / 5 + 1;
                if (*tr < hp) *tr = hp;
                battle.hud_dirty |= 4 << side;
            }
        } else if (*tr < hp) {
            *tr = hp;
        }
        if (battle.disp[side].jolt > 0) battle.disp[side].jolt--;
    }
    for (int side = 0; side < 2; side++) {
        if (battle.hud_dirty & (1 << side)) hud_draw(side);
        else if ((battle.hud_dirty & (4 << side)) && hud_shown(side)) hud_draw_bar(side);
    }
    battle.hud_dirty = 0;

    /* befriended mark on a wild foe's HUD */
    if (battle.disp[SIDE_ENEMY].caught && hud_shown(SIDE_ENEMY)) {
        int j = battle.disp[SIDE_ENEMY].jolt;
        int jx = j ? ((j & 2) ? 1 : -1) * (j + 2) / 4 : 0;
        spr_push(HUD_ENEMY_CX * 8 + 98 + jx, HUD_ENEMY_CY * 8 - 3, OT_LANTERN_MINI, SQ8, OBANK_CAPSULE, 0, 0);
    }

    anim_update();

    /* the rim of the intro's lantern light glitters */
    int ir = intro_radius();
    if (ir > 0 && ir < 150)
        for (int k = 0; k < 10; k++) {
            int a = k * 26 + battle.timer * 3;
            int x = 120 + soft_sin(a + 64) * ir / 64, y = 58 + soft_sin(a) * ir / 64;
            if (x > -8 && x < 248 && y > -8 && y < 168 && ((k + battle.timer / 2) & 1))
                fx_spr_aff(x, y, FX_SPARKLE, OBANK_LIGHT, 192 + ((k * 37 + battle.timer * 5) & 63), k * 25);
        }

    if (battle.lantern_visible) {
        if (battle.lantern_glow > 0)
            big_spr(battle.lantern_x, battle.lantern_y + 2, FXB_GLOW, OBANK_LIGHT,
                    64 + battle.lantern_glow * 8, 64 + battle.lantern_glow * 8);
        spr_push(battle.lantern_x - 8 + shake_x, battle.lantern_y - 8 + shake_y,
                 OT_CAPSULE + battle.lantern_frame * 4, SQ16, OBANK_CAPSULE, 1, 0);
    }
    load_pal(obj_palette + OBANK_CAPSULE * 16, capsule_pal[battle.lantern_kind]);

    battle_draw_battlers();
    battle_draw_palettes();

    /* background tint eases toward what the animation wants */
    int want = anim.active ? anim.bg_amount * 16 : 0;
    if (want && anim.bg_color != feel.bg_color) feel.bg_color = anim.bg_color;
    if (feel.bg_amount < want) feel.bg_amount = feel.bg_amount + 24 > want ? want : feel.bg_amount + 24;
    else if (feel.bg_amount > want) feel.bg_amount = feel.bg_amount - 16 < want ? want : feel.bg_amount - 16;
    int intro_warm = 0;
    if (battle.state == BST_INTRO && battle.timer > INTRO_DARK)
        intro_warm = 120 - (battle.timer - INTRO_DARK) * 4;
    if (intro_warm > 0) {
        if (scene_tint_applied != intro_warm) battle_apply_scene_tint(intro_warm, RGB15(31, 22, 10));
    } else if (feel.bg_amount != scene_tint_applied || (feel.bg_amount && feel.bg_color != scene_tint_color)) {
        battle_apply_scene_tint(feel.bg_amount, feel.bg_color);
    }

    /* blending: screen flashes, the exit fade, semi-transparent sprites */
    int bright = anim.bright + feel.bright * 2;
    if (battle.state == BST_END) bright = -battle.timer;
    u16 bld = 0x2100;   /* 2nd targets for semi-transparent OBJ: BG0, backdrop */
    if (battle.state == BST_INTRO) {
        REG_BLDCNT = 0x3F | 0xC0;
        REG_BLDY = 11;
    } else {
        if (bright) bld |= (u16)(0x3F | (bright > 0 ? 0x80 : 0xC0));
        REG_BLDCNT = bld;
        REG_BLDY = (u16)clampi(absi(bright), 0, 16);
    }
    int fade = battle.disp[0].fade > battle.disp[1].fade ? battle.disp[0].fade : battle.disp[1].fade;
    if (fade) REG_BLDALPHA = (u16)((16 - fade) | (fade << 8));
    else REG_BLDALPHA = (u16)(7 | (9 << 8));
    REG_MOSAIC = (u16)(anim.mosaic | (anim.mosaic << 4) | (anim.mosaic << 8) | (anim.mosaic << 12));
    battle_draw_lines();
}
