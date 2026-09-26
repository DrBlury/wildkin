/*
 * Battle move animations and "feel".
 *
 * Every move names an animation kind (AK_*), particles, colours and a
 * repeat count (see MOVES in moves.h). A kind is a small timeline: wind-up,
 * travel, impact, follow-through. At the impact frame anim_impact() fires
 * the shared hit feedback, scaled by how hard the hit was (weak spot,
 * perfect strike, shrugged off, the last blow):
 *
 *   hit-stop     the animation freezes for a few frames
 *   flash        the target's palette goes white, then fades back
 *   squash       the target squashes (affine sprite) and springs back
 *   knockback    the target is pushed away and eases back
 *   shake        screen shake that decays
 *   sparks       particles fly off the point of impact
 *
 * Big moves also blend the battle background palette toward a colour for
 * their type (darker for DUSK, warmer for BLAZE, cooler for FROST...).
 * Particles are 16x16 OBJ sprites (plus two 32x32 ones) drawn with
 * palettes built from the move's two colours.
 *
 * With opt.battle_anims off only a short version plays: the hit flash and
 * shake (or a tint pulse for status moves).
 */

#define ENEMY_X 144
#define ENEMY_Y 8
#define ALLY_X 40
#define ALLY_Y 48

/* OBJ tiles after the small particles: the two big particles and the
 * wild-HUD lantern mark. */
#define OT_FX_BIG      (OT_FX + FX_COUNT * 4)
#define OBANK_LIGHT    15   /* warm lantern light (glows, send-out bursts) */
#define OT_LANTERN_MINI (OT_FX_BIG + FXB_COUNT * 16)

enum { ANIM_MOVE, ANIM_STAT, ANIM_STATUS, ANIM_SHORT, ANIM_MISS, ANIM_TRAIT, ANIM_REACT, ANIM_LEGEND };

static struct {
    int active, mode, kind, move, side, t, dur, variant, flags;
    int fx, fx2, count, type;
    int last_impact;          /* t of the last impact fired (not re-fired while frozen) */
    int impacted;
    /* per-frame outputs, reset every frame */
    int mon_dx[2], mon_dy[2];
    int hide[2];
    int tint_side, tint_amount;
    u16 tint_color;
    int bg_amount;            /* 0..16 background tint wanted this frame */
    u16 bg_color;
    int wobble;               /* BG0 per-line wobble amplitude (px) */
    int mosaic;               /* 0..15 */
    int afterimage;           /* draw the attacker's afterimages */
    int scale_x[2], scale_y[2]; /* extra 8.8 scale from the kind (1 = none) */
    int bright;               /* screen brightness this frame (-16..16) */
} anim;

/* Hit feedback that outlives a single animation frame. */
static struct {
    int hitstop;
    int shake;                /* amplitude, 1/16 px */
    int shake_v;              /* 1 = mostly vertical */
    int flash[2];             /* white flash frames */
    int sx[2], sy[2], vx[2], vy[2];   /* squash & stretch springs (8.8) */
    int kb[2];                /* knockback, 1/16 px, decays */
    int bright;               /* screen flash frames (brightness +) */
    int bg_amount;            /* eased background tint 0..16 (x16 fixed) */
    u16 bg_color;
    int trail_x[2][8], trail_y[2][8], trail_n;  /* afterimage history */
} feel;

static int side_cx(int side) { return side == SIDE_ENEMY ? ENEMY_X + 32 : ALLY_X + 32; }
static int side_cy(int side) { return side == SIDE_ENEMY ? ENEMY_Y + 34 : ALLY_Y + 30; }
/* ground line under a battler (for dust, cracks, geysers) */
static int side_gy(int side) { return side == SIDE_ENEMY ? ENEMY_Y + 62 : ALLY_Y + 62; }

/* Triangle-wave sine approximation: returns -64..64 for phase 0..255. */
static int tri_sin(int phase)
{
    phase &= 255;
    if (phase < 64) return phase;
    if (phase < 192) return 128 - phase;
    return phase - 256;
}

/* Smoother sine from a quarter table: -64..64 for phase 0..255. */
static int soft_sin(int phase)
{
    static const s8 Q[17] = { 0, 6, 12, 18, 24, 30, 35, 40, 45, 49, 53, 56, 59, 61, 62, 63, 64 };
    phase &= 255;
    int q = phase & 63, sgn = phase < 128 ? 1 : -1;
    if (phase & 64) q = 64 - q;
    int i = q >> 2, f = q & 3;
    int v = Q[i] + ((i < 16 ? Q[i + 1] - Q[i] : 0) * f >> 2);
    return v * sgn;
}

/* Ease-out (quadratic): 0..n -> 0..256 */
static int ease_out(int t, int n)
{
    if (n <= 0 || t >= n) return 256;
    if (t <= 0) return 0;
    int u = n - t;
    return 256 - u * u * 256 / (n * n);
}

/* Ease-in (quadratic): 0..n -> 0..256 */
static int ease_in(int t, int n)
{
    if (n <= 0 || t >= n) return 256;
    if (t <= 0) return 0;
    return t * t * 256 / (n * n);
}

/* Presentation-only randomness, so animations never shift the rules' RNG. */
static u32 fx_rng_state = 0x2468ACEu;

static int fx_rand(int n)
{
    fx_rng_state = fx_rng_state * 1103515245u + 12345u;
    return n > 0 ? (int)((fx_rng_state >> 16) % (u32)n) : 0;
}

static u16 mix15(u16 c, u16 d, int num, int den)
{
    int r = c & 31, g = (c >> 5) & 31, b = (c >> 10) & 31;
    int r2 = d & 31, g2 = (d >> 5) & 31, b2 = (d >> 10) & 31;
    r += (r2 - r) * num / den;
    g += (g2 - g) * num / den;
    b += (b2 - b) * num / den;
    return RGB15(r, g, b);
}

/* mix15 with a power-of-two denominator (no divisions): num / (1 << sh) */
static u16 mix15_sh(u16 c, u16 d, int num, int sh)
{
    int r = c & 31, g = (c >> 5) & 31, b = (c >> 10) & 31;
    int r2 = d & 31, g2 = (d >> 5) & 31, b2 = (d >> 10) & 31;
    r += ((r2 - r) * num) >> sh;
    g += ((g2 - g) * num) >> sh;
    b += ((b2 - b) * num) >> sh;
    return RGB15(r & 31, g & 31, b & 31);
}

static u16 scale15(u16 c, int pct)
{
    int r = (c & 31) * pct / 100, g = ((c >> 5) & 31) * pct / 100, b = ((c >> 10) & 31) * pct / 100;
    return RGB15(clampi(r, 0, 31), clampi(g, 0, 31), clampi(b, 0, 31));
}

/* Particle palette: value ramp of `main` (1..6) plus `sec` (7..9). */
static void build_fx_palette(int bank, u16 main, u16 sec)
{
    u16 *p = obj_palette + bank * 16;
    const u16 white = RGB15(31, 31, 31);
    p[0] = 0;
    p[1] = mix15(scale15(main, 25), RGB15(2, 2, 8), 1, 3);
    p[2] = scale15(main, 58);
    p[3] = main;
    p[4] = mix15(main, white, 35, 100);
    p[5] = mix15(main, white, 65, 100);
    p[6] = mix15(main, white, 92, 100);
    p[7] = scale15(sec, 55);
    p[8] = sec;
    p[9] = mix15(sec, white, 55, 100);
}

/* Rainbow hue for palette cycling (0..191). */
static u16 hue15(int h)
{
    h %= 192;
    if (h < 0) h += 192;
    int s = h / 32, f = (h % 32) * 31 / 32, up = f, dn = 31 - f;
    switch (s) {
    case 0: return RGB15(31, up, 6);
    case 1: return RGB15(dn, 31, 6);
    case 2: return RGB15(6, 31, up);
    case 3: return RGB15(6, dn, 31);
    case 4: return RGB15(up, 6, 31);
    default: return RGB15(31, 6, dn);
    }
}

/* Background tint per move type: colour and strength (0..16). */
static const u16 TYPE_TINT[TYPE_COUNT] = {
    RGB15(31, 28, 20), RGB15(31, 18, 4), RGB15(6, 14, 31), RGB15(22, 31, 8), RGB15(31, 31, 10),
    RGB15(18, 28, 31), RGB15(31, 22, 14), RGB15(16, 4, 22), RGB15(20, 13, 6), RGB15(26, 31, 31),
    RGB15(31, 12, 26), RGB15(24, 28, 12), RGB15(3, 1, 8), RGB15(6, 6, 22),
    /* HOLLOW grave-moss dusk, RELIC old gilt, METAL cold steel, ASTRAL night sky */
    RGB15(8, 13, 10), RGB15(30, 22, 8), RGB15(14, 18, 25), RGB15(6, 4, 18),
};
static const u8 TYPE_TINT_AMT[TYPE_COUNT] = { 3, 7, 5, 5, 6, 7, 3, 6, 5, 4, 6, 4, 10, 8, 8, 5, 6, 10 };

/* Type flavour sound played when a move starts. */
static const u8 TYPE_SFX[TYPE_COUNT] = {
    SFX_SWING, SFX_FIRE, SFX_SPLASH, SFX_LEAF, SFX_ZAP, SFX_ICE, SFX_SWING, SFX_VENOM,
    SFX_ROCK, SFX_WIND, SFX_DREAM, SFX_BUZZ, SFX_DUSK, SFX_WYRM,
    SFX_HOLLOW, SFX_RELIC, SFX_METAL, SFX_ASTRAL,   /* HOLLOW RELIC METAL ASTRAL */
};

/* ---------------- particles that outlive an animation ---------------- */

enum { PK_FX, PK_BIG_GROW, PK_RING_GROW, PK_SPARK };

typedef struct {
    s16 x, y, vx, vy;         /* 1/16 px */
    u8 kind, fx, bank, life, max;
    s8 grav;
} Particle;

#define PART_MAX 24
static Particle parts[PART_MAX];

static void part_add(int kind, int x, int y, int vx, int vy, int fx, int bank, int life, int grav)
{
    for (int i = 0; i < PART_MAX; i++) {
        if (parts[i].life) continue;
        Particle *p = &parts[i];
        p->kind = (u8)kind;
        p->x = (s16)(x * 16);
        p->y = (s16)(y * 16);
        p->vx = (s16)vx;
        p->vy = (s16)vy;
        p->fx = (u8)fx;
        p->bank = (u8)bank;
        p->life = p->max = (u8)life;
        p->grav = (s8)grav;
        return;
    }
}

static void parts_clear(void)
{
    for (int i = 0; i < PART_MAX; i++) parts[i].life = 0;
}

/* Sparks flying out of a point of impact. */
static void spark_burst(int x, int y, int n, int speed, int fx, int bank)
{
    for (int i = 0; i < n; i++) {
        int a = i * 256 / n + fx_rand(20);
        part_add(PK_SPARK, x, y, soft_sin(a + 64) * speed / 16, soft_sin(a) * speed / 16 - 8, fx, bank,
                 12 + fx_rand(6), 3);
    }
}

/* ---------------- sprite helpers ---------------- */

static int shake_x, shake_y;  /* this frame's screen shake (px) */
static unsigned anim_frame;   /* frames drawn (drives shake and breathing) */
/* 1 while anim_update() runs a step that is not shown (opt.battle_speed
 * steps twice per frame): the state advances but no sprite is pushed. */
static int anim_nodraw;

static void fx_spr(int x, int y, int fx, int bank)
{
    if (anim_nodraw) return;
    spr_push(x - 8 + shake_x, y - 8 + shake_y, OT_FX + fx * 4, SQ16, bank, 1, 0);
}

static void fx_spr_flip(int x, int y, int fx, int bank, int flags)
{
    if (anim_nodraw) return;
    spr_push(x - 8 + shake_x, y - 8 + shake_y, OT_FX + fx * 4, SQ16, bank, 1, flags);
}

/* Particle with scale (8.8) and rotation (0..255). */
static void fx_spr_aff(int x, int y, int fx, int bank, int scale, int rot)
{
    if (anim_nodraw) return;
    int aff = oam_affine_scale_rot(scale, scale, rot);
    spr_push_affine(x - 8 + shake_x, y - 8 + shake_y, OT_FX + fx * 4, SQ16, bank, 1, 0, aff,
                    scale > 256);
}

static void fx_spr_aff2(int x, int y, int fx, int bank, int sx, int sy, int rot)
{
    if (anim_nodraw) return;
    int aff = oam_affine_scale_rot(sx, sy, rot);
    spr_push_affine(x - 8 + shake_x, y - 8 + shake_y, OT_FX + fx * 4, SQ16, bank, 1, 0, aff,
                    absi(sx) > 256 || absi(sy) > 256);
}

/* 32x32 particle (FXB_*) scaled; up to 2x fits the double-size box. */
static void big_spr(int x, int y, int fxb, int bank, int sx, int sy)
{
    if (anim_nodraw) return;
    int aff = oam_affine_scale_rot(sx, sy, 0);
    spr_push_affine(x - 16 + shake_x, y - 16 + shake_y, OT_FX_BIG + fxb * 16, SQ32, bank, 1, 0, aff,
                    1);
}

/* Two-frame particles flicker between fx and fx2 when they are a pair. */
static int fx_frame(int fx, int fx2, int t)
{
    int paired = (fx == FX_FLAME_A && fx2 == FX_FLAME_B) || (fx == FX_FLAME_B && fx2 == FX_FLAME_A) ||
                 (fx == FX_LEAF_A && fx2 == FX_LEAF_B) || (fx == FX_SPARK_A && fx2 == FX_SPARK_B) ||
                 (fx == FX_SPARK_B && fx2 == FX_SPARK_A);
    return paired && ((t >> 2) & 1) ? fx2 : fx;
}

static int fx_is_hit(int fx)
{
    return fx == FX_IMPACT || fx == FX_IMPACT_SMALL || fx == FX_STAR || fx == FX_BURST;
}

/* ---------------- impacts ---------------- */

/* Kick a side's squash/stretch spring: sx, sy relative to 256. */
static void squash(int side, int sx, int sy)
{
    feel.sx[side] = sx;
    feel.sy[side] = sy;
    feel.vx[side] = feel.vy[side] = 0;
}

static void shake(int amp16, int vertical)
{
    if (amp16 > feel.shake) feel.shake = amp16;
    feel.shake_v = vertical;
}

/*
 * The moment a blow lands. strength: 0 light .. 2 heavy; the flags of the
 * hit (weak spot, perfect strike, shrugged off, KO) push it up or down.
 */
static void anim_impact_at(int side_hit, int strength, int x, int y)
{
    int f = anim.flags;
    anim.impacted = 1;
    battle.impacted = side_hit + 1;
    if (f & HITF_NODMG) {
        feel.flash[side_hit] = 3;
        squash(side_hit, 240, 272);
        return;
    }
    int s = strength;
    if (f & HITF_WEAK) s++;
    if (f & HITF_CRIT) s += 2;
    if (f & HITF_RESIST) s--;
    if ((f & HITF_KO) && (f & HITF_LAST)) s++;
    s = clampi(s, 0, 4);
    static const u8 STOP[5] = { 2, 3, 4, 6, 9 };
    static const u8 SHK[5] = { 16, 32, 48, 72, 104 };
    static const u8 SQ[5] = { 18, 28, 40, 54, 66 };
    static const u8 KB[5] = { 32, 56, 80, 104, 128 };
    feel.hitstop = STOP[s];
    feel.flash[side_hit] = 5 + s;
    shake(SHK[s], strength >= 2 && !(f & HITF_RESIST));
    squash(side_hit, 256 + SQ[s], 256 - SQ[s]);
    feel.kb[side_hit] = (side_hit == SIDE_ENEMY ? 1 : -1) * KB[s];
    if (f & (HITF_CRIT | HITF_WEAK)) {
        feel.bright = f & HITF_CRIT ? 4 : 2;
        part_add(PK_BIG_GROW, x, y, 0, 0, FXB_RING, OBANK_FX_HIT, 12, 0);
    }
    spark_burst(x, y, 3 + s, 20 + s * 6, s >= 2 ? FX_STAR : FX_SPARKLE, OBANK_FX_HIT);
    if (f & HITF_CRIT) sfx_play(SFX_PERFECT);
    else if (f & HITF_WEAK) sfx_play(SFX_WEAK_SPOT);
    else if (f & HITF_RESIST) sfx_play(SFX_SHRUGGED);
    else sfx_play(s <= 0 ? SFX_HIT_LIGHT : s >= 3 ? SFX_HIT_STRONG : SFX_HIT);
}

/* Fire an impact exactly once at frame t0 of the current animation. */
static int impact_when(int t0, int strength, int x, int y)
{
    if (anim.t != t0 || anim.last_impact == t0) return 0;
    anim.last_impact = t0;
    anim_impact_at(!anim.side, strength, x, y);
    return 1;
}

/* A self-targeted move "lands" on its user: a little squash and glow. */
static int self_pulse_when(int t0)
{
    if (anim.t != t0 || anim.last_impact == t0) return 0;
    anim.last_impact = t0;
    anim.impacted = 1;
    squash(anim.side, 276, 236);
    return 1;
}

/* Base strength of this move's hit: bigger moves hit harder. */
static int move_strength(void)
{
    int p = MOVES[anim.move].power;
    return p >= 100 ? 2 : p >= 60 ? 1 : 0;
}

/* ---------------- starting animations ---------------- */

static void anim_reset_offsets(void)
{
    for (int s = 0; s < 2; s++) {
        anim.mon_dx[s] = anim.mon_dy[s] = 0;
        anim.hide[s] = 0;
        anim.scale_x[s] = anim.scale_y[s] = 256;
    }
    anim.tint_amount = 0;
    anim.bg_amount = 0;
    anim.wobble = 0;
    anim.mosaic = 0;
    anim.afterimage = 0;
    anim.bright = 0;
}

static int anim_duration(int kind, int count, int variant)
{
    switch (kind) {
    case AK_CONTACT: return 34 + count * 8;
    case AK_SLASH: return 30 + count * 10;
    case AK_PROJECTILE: return 36 + count * 5;
    case AK_STREAM: return 60;
    case AK_BEAM: return 58;
    case AK_RAIN: return variant ? 26 : 32 + count * 7;
    case AK_BOLT: return 50;
    case AK_BURST: return 48;
    case AK_ORBIT: return 62;
    case AK_WAVE: return 60;
    case AK_QUAKE: return 60;
    case AK_BUFF: return 52;
    case AK_DEBUFF: return 54;
    case AK_FANGS: return 32 + count * 14;
    case AK_DRAIN: return 64;
    case AK_DASH: return 34;
    case AK_SLAM: return 52;
    case AK_WHIP: return 26 + count * 12;
    case AK_PSYCHIC: return 44 + count * 8;
    case AK_POWDER: return 64;
    case AK_STRIKE: return variant ? 20 : 24 + count * 14;
    case AK_ROAR: return 64;
    case AK_GEYSER: return 60;
    case AK_SUNSHAFT: return 64;
    case AK_FAULT: return 66;
    case AK_WOBBLE: return 64;
    case AK_HEAL: return 60;
    case AK_CHARGE: return 76;
    case AK_LURE: return 72;
    case AK_STOOP: return 58;
    case AK_HAYMAKER: return 56;
    case AK_SPIRAL: return 56;
    case AK_RIPPLE: return 56;
    case AK_WRAP: return 58;
    case AK_GUARD: return 46;
    case AK_RUSH: return 50;
    case AK_RATTLE: return 46;
    case AK_MIST: return 60;
    case AK_SHROUD: return 58;
    case AK_TOLL: return 30 + count * 16;
    case AK_CHOIR: return 76;
    case AK_CHOMP: return 24 + count * 14;
    case AK_WHIRL: return 64;
    case AK_MAGNET: return 60;
    case AK_GEARS: return 56;
    case AK_ANVIL: return 66;
    case AK_MOONLIT: return 70;
    case AK_MUON: return 58;
    case AK_METEOR: return 64;
    case AK_NOVA: return 80;
    case AK_ARC: return 50;
    case AK_DANCE: return 62;
    default: return 34;
    }
}

static void anim_begin(int mode, int side)
{
    anim_reset_offsets();
    anim.active = 1;
    anim.mode = mode;
    anim.side = side;
    anim.t = 0;
    anim.last_impact = -1;
    anim.impacted = 0;
    anim.flags = 0;
    anim.variant = 0;
    anim.tint_side = side;
}

/* flags: the HITF_* bits of the hit (low byte = hit index). */
static void anim_start(int move, int side, int flags)
{
    const Move *mv = &MOVES[move];
    anim_begin(ANIM_MOVE, side);
    battle.impacted = 0;
    anim.move = move;
    anim.kind = mv->anim;
    anim.fx = mv->fx;
    anim.fx2 = mv->fx2;
    anim.type = mv->type;
    anim.count = mv->count ? mv->count : 1;
    anim.variant = flags & 0xFF;
    anim.flags = flags & ~0xFF;
    anim.tint_side = !side;
    anim.tint_color = mv->col1;
    build_fx_palette(OBANK_FX_A, mv->col1, mv->col2);
    build_fx_palette(OBANK_FX_B, mv->col2, mv->col1);
    build_fx_palette(OBANK_FX_HIT, RGB15(31, 30, 18), RGB15(31, 22, 6));
    if (flags & HITF_MISS) {
        anim.mode = ANIM_MISS;
        anim.dur = 30;
        sfx_play(SFX_MISS);
        return;
    }
    if (!opt.battle_anims) {
        anim.mode = ANIM_SHORT;
        anim.dur = 18;
        return;
    }
    anim.dur = anim_duration(anim.kind, anim.count, anim.variant);
    /* the flavour sound once per move (not on every hit of a multi-hit) */
    if (anim.variant == 0) sfx_play(TYPE_SFX[mv->type]);
}

static void anim_start_stat(int side, int up)
{
    anim_begin(ANIM_STAT, side);
    anim.variant = up;
    anim.dur = opt.battle_anims ? 36 : 14;
    anim.tint_color = up ? RGB15(31, 18, 8) : RGB15(8, 14, 31);
    build_fx_palette(OBANK_FX_A, up ? RGB15(31, 20, 6) : RGB15(10, 16, 31), RGB15(31, 31, 31));
    sfx_play(up ? SFX_STAT_UP : SFX_STAT_DOWN);
}

static const u16 STATUS_COL[STATUS_COUNT] = {
    0, RGB15(31, 10, 2), RGB15(22, 6, 26), RGB15(31, 28, 4), RGB15(20, 22, 31), RGB15(16, 28, 31),
};

/* reminder: 1 = "is fast asleep" etc. (shorter) */
static void anim_start_status(int side, int status, int reminder)
{
    static const u8 FX[STATUS_COUNT] = { 0, FX_FLAME_A, FX_GLOB, FX_SPARK_A, FX_ZZZ, FX_SHARD };
    anim_begin(ANIM_STATUS, side);
    anim.active = status != STATUS_NONE;
    anim.fx = FX[status];
    anim.variant = status;
    anim.dur = opt.battle_anims ? (reminder ? 26 : 38) : 14;
    anim.tint_color = STATUS_COL[status];
    build_fx_palette(OBANK_FX_A, STATUS_COL[status], RGB15(31, 31, 31));
    if (anim.active) sfx_play(reminder ? SFX_STATUS : SFX_STATUS);
}

static void anim_start_trait(int side)
{
    anim_begin(ANIM_TRAIT, side);
    anim.dur = opt.battle_anims ? 30 : 12;
    anim.tint_color = RGB15(31, 30, 22);
    build_fx_palette(OBANK_FX_A, RGB15(31, 26, 10), RGB15(31, 31, 31));
    sfx_play(SFX_TRAIT);
}

/* A hit that no animation showed (status damage, recoil, anims off). */
static void anim_start_react(int side, int flags)
{
    anim_begin(ANIM_REACT, !side);
    anim.flags = flags & ~0xFF;
    anim.dur = 14;
    build_fx_palette(OBANK_FX_HIT, RGB15(31, 30, 18), RGB15(31, 22, 6));
}

/* A legend arrives: it rears up, shockwave rings roll out, the screen
 * shakes hard and the background flashes its type's tint. */
static void anim_start_legend(int side)
{
    int type = SPECIES[side_mon(side)->species].type1;
    anim_begin(ANIM_LEGEND, side);
    anim.type = type;
    anim.dur = opt.battle_anims ? 72 : 24;
    anim.tint_color = TYPE_TINT[type];
    build_fx_palette(OBANK_FX_A, TYPE_TINT[type], RGB15(31, 31, 31));
    build_fx_palette(OBANK_FX_B, RGB15(31, 31, 31), TYPE_TINT[type]);
    sfx_play(SFX_ROAR);
}

/* ---------------- per-kind motion ---------------- */

/* Attacker lunge toward the foe with a wind-up: returns the offset (px)
 * along the attack direction. wind = frames pulling back, go = frames
 * rushing in, hold = frames at the target, back = frames returning. */
static int lunge(int t, int wind, int go, int hold, int back, int reach)
{
    if (t < wind) return -ease_out(t, wind) * 6 / 256;
    t -= wind;
    if (t < go) return -6 + (reach + 6) * ease_in(t, go) / 256;
    t -= go;
    if (t < hold) return reach;
    t -= hold;
    if (t < back) return reach - reach * ease_out(t, back) / 256;
    return 0;
}

static void anim_move_frame(void)
{
    int t = anim.t, side = anim.side, foe = !side;
    int sx = side_cx(side), sy = side_cy(side);
    int dx = side_cx(foe), dy = side_cy(foe);
    int dir = side == SIDE_ALLY ? 1 : -1;
    int n = anim.count;
    int fx = anim.fx, fx2 = anim.fx2;
    int st = move_strength();
    int big = MOVES[anim.move].power >= 90;
    int tint_amt = TYPE_TINT_AMT[anim.type];
    anim.bg_color = TYPE_TINT[anim.type];

    switch (anim.kind) {
    case AK_CONTACT: {
        /* wind-up, headlong lunge, hits, return */
        int reach = 40;
        int l = lunge(t, 8, 7, 4 + n * 6, 12, reach);
        anim.mon_dx[side] = dir * l;
        anim.mon_dy[side] = -dir * l / 3;
        if (t < 8) anim.scale_x[side] = 256 - t * 3, anim.scale_y[side] = 256 + t * 3;
        else if (t < 15) anim.scale_x[side] = 290, anim.scale_y[side] = 226;
        if (anim.move == M_LIVE_WIRE && t >= 8 && t < 15 && (t & 1))
            fx_spr(sx + dir * (l - 8), sy - dir * l / 3, FX_SPARK_B, OBANK_FX_B);
        if (anim.move == M_LAST_EMBER) {
            Monster *m = side_mon(side);
            int hot = m->max_hp ? 256 + 256 * (m->max_hp - m->hp) / m->max_hp : 256;
            if (t < 16) fx_spr_aff(sx + dir * l, sy - 18 - dir * l / 3, fx_frame(fx, fx2, t), OBANK_FX_A, hot, 0);
        }
        for (int i = 0; i < n; i++) {
            int ht = 15 + i * 6;
            int jx = (i & 1) ? 8 : -6, jy = (i & 1) ? -6 : 4;
            impact_when(ht, i == n - 1 ? st : 0, dx + jx, dy + jy);
            if (t >= ht && t < ht + 8) fx_spr(dx + jx, dy + jy, fx_is_hit(fx) ? fx : fx_frame(fx, fx2, t),
                                             fx_is_hit(fx) ? OBANK_FX_HIT : OBANK_FX_A);
        }
        if (fx2 == FX_STAR && t >= 20) {  /* cartoon stars circling the foe's head */
            for (int k = 0; k < 3; k++) {
                int a = t * 10 + k * 85;
                fx_spr(dx + tri_sin(a) / 3, dy - 22 + tri_sin(a + 64) / 10, FX_STAR, OBANK_FX_B);
            }
        } else if (fx2 != fx && t >= 17 && t < 26) {
            fx_spr(dx - 8, dy - 8, fx_frame(fx2, fx, t), fx_is_hit(fx2) ? OBANK_FX_HIT : OBANK_FX_B);
        }
        break;
    }
    case AK_SLASH: {
        /* small lean-in, then the streaks sweep across the foe */
        anim.mon_dx[side] = dir * lunge(t, 6, 4, 6, 8, 10);
        int scale = anim.move == M_REED_BLADE || anim.move == M_SCALE_REND ? 384 : 256;
        if (fx2 == FX_WISP) {                  /* SHADE CUT: a cut out of the dark */
            anim.bg_color = RGB15(2, 1, 6);
            anim.bg_amount = t < 26 ? 10 : 0;
            if (t >= 12 && t < 26 && (t & 2)) fx_spr(dx - 12 + (t - 12) * 2, dy + 10 - (t - 12), FX_WISP, OBANK_FX_B);
        }
        for (int i = 0; i < n; i++) {
            int s0 = 8 + i * 10, stt = t - s0;
            if (stt < 0 || stt >= 18) continue;
            int ox = (i & 1) ? 10 : -6, oy = (i & 1) ? 6 : -8;
            int sweep = stt < 6 ? stt * 4 - 12 : 12;
            if (stt < 12)
                fx_spr_aff2(dx + ox - sweep * ((i & 1) ? -1 : 1), dy + oy + sweep, fx, OBANK_FX_A,
                            (i & 1) ? -scale : scale, scale, 0);
            impact_when(s0 + 3, i == n - 1 ? st : 0, dx + ox, dy + oy);
            if (fx2 == FX_FEATHER || fx2 == FX_LEAF_A) {
                if (stt >= 6)
                    for (int k = 0; k < 2; k++)
                        fx_spr(dx + ox + (stt - 6) * (k ? 2 : -2), dy + oy + (stt - 6) * (k ? 1 : 2) / 1,
                               fx2, OBANK_FX_B);
            }
        }
        break;
    }
    case AK_PROJECTILE: {
        int travel = fx == FX_SHARD || fx == FX_NEEDLE ? 12 : fx == FX_GLOB ? 22 : 18;
        int gap = fx == FX_PEBBLE ? 3 : 5;
        int windup = 6;
        if (t < windup) {
            anim.mon_dx[side] = -dir * t / 2;
            anim.scale_y[side] = 256 + t * 4;
        } else if (t < windup + 6) {
            anim.mon_dx[side] = dir * 4;
        }
        for (int i = 0; i < n; i++) {
            int pt = t - windup - i * gap;
            if (pt < 0) continue;
            int jx = (i * 7) % 13 - 6, jy = (i * 5) % 11 - 5;
            if (fx == FX_PEBBLE) jx *= 2, jy *= 2;
            if (pt < travel) {
                int x = sx + (dx + jx - sx) * pt / travel;
                int y = sy + (dy + jy - sy) * pt / travel;
                int arc = fx == FX_GLOB ? 30 : fx == FX_BUBBLE || fx == FX_WIND ? 0 :
                          fx == FX_FIREBALL ? 14 : fx == FX_PEBBLE ? 10 : 5;
                y -= arc * (pt * (travel - pt)) / (travel * travel / 4);
                if (fx == FX_BUBBLE || fx == FX_WIND) y += tri_sin(pt * 24 + i * 60) / 8;
                if (fx == FX_SPARKLE || fx == FX_MOTE) y += soft_sin(pt * 14) / 4;   /* GLINT, TWINKLE curl in */
                int f = fx_frame(fx, fx2, pt + i);
                if (fx == FX_LEAF_A) f = ((pt >> 2) & 1) ? FX_LEAF_B : FX_LEAF_A;
                if (fx == FX_ORB) {                                         /* GLOOM ORB swells */
                    fx_spr_aff(x, y, FX_ORB, OBANK_FX_A, 192 + pt * 12, 0);
                } else if (fx == FX_BURR || fx == FX_PEBBLE || fx == FX_TRINKET || fx == FX_COIN) {
                    fx_spr_aff(x, y, f, OBANK_FX_A, 256, pt * 24);
                } else {
                    fx_spr_flip(x, y, f, OBANK_FX_A, dir < 0 && (fx == FX_SHARD || fx == FX_NEEDLE) ?
                                ATTR1_HFLIP : 0);
                }
                if (fx == FX_NEEDLE && fx2 == FX_TEAR && (pt & 2)) fx_spr(x - dir * 6, y + 6, FX_TEAR, OBANK_FX_B);
                if (fx == FX_FIREBALL && (pt & 1)) fx_spr(x - dir * 8, y + 2, FX_FLAME_B, OBANK_FX_B);
                if (fx == FX_RIVET && (pt & 1)) fx_spr(x - dir * 8, y + 3, fx2, OBANK_FX_B);    /* hot rivets */
                if (fx == FX_MOTE && (pt & 2)) fx_spr(x - dir * 7, y + 4, FX_SPARKLE, OBANK_FX_B);
            } else {
                int it = pt - travel;
                int last = i == n - 1;
                impact_when(windup + i * gap + travel, last ? st : 0, dx + jx, dy + jy);
                if ((fx == FX_GLOB) && it < 14) {
                    fx_spr_aff(dx + jx, dy + jy + 4, fx2 == FX_SPLAT ? FX_SPLAT : FX_GLOB, OBANK_FX_A,
                               256 + it * 20, 0);
                    for (int k = 0; k < 4; k++) {
                        int ax = (k & 1) ? 1 : -1, ay = (k & 2) ? 1 : -1;
                        fx_spr(dx + jx + ax * it * 2, dy + jy + ay * it + it * it / 8, FX_GLOB, OBANK_FX_B);
                    }
                } else if (fx == FX_ORB && it < 16) {
                    big_spr(dx, dy, FXB_GLOW, OBANK_FX_A, 256 + it * 16, 256 + it * 16);
                } else if (fx2 == FX_STEAM && it < 16) {                  /* ACID SPIT sizzles */
                    fx_spr_aff(dx + jx + ((it & 4) ? 2 : -2), dy + jy - it, FX_STEAM, OBANK_FX_B, 192 + it * 12, 0);
                    if (it < 6) fx_spr(dx + jx, dy + jy, FX_SPLAT, OBANK_FX_A);
                } else if (fx == FX_BUBBLE && it < 8) {
                    fx_spr_aff(dx + jx, dy + jy, FX_RING, OBANK_FX_A, 256 + it * 32, 0);
                } else if (fx == FX_FIREBALL && it < 14) {
                    for (int k = 0; k < 3; k++)
                        fx_spr(dx + jx + (k - 1) * 8, dy + jy - it, fx_frame(FX_FLAME_A, FX_FLAME_B, it + k),
                               OBANK_FX_A);
                } else if (it < 8) {
                    fx_spr(dx + jx, dy + jy, fx2 == FX_STAR ? FX_STAR : FX_IMPACT_SMALL, OBANK_FX_HIT);
                }
            }
        }
        if (fx == FX_ORB) anim.bg_amount = t > 8 ? tint_amt : 0;
        break;
    }
    case AK_STREAM: {
        /* the attacker rears back, then a steady stream pours out */
        if (t < 8) anim.scale_y[side] = 256 + t * 4, anim.mon_dx[side] = -dir * t / 2;
        else anim.mon_dx[side] = dir * 3;
        for (int e = 0; e < 36; e += 2) {
            int pt = t - 8 - e;
            if (pt < 0 || pt >= 16) continue;
            int x = sx + (dx - sx) * pt / 16 + tri_sin(e * 40 + pt * 12) / 10;
            int y = sy + (dy - sy) * pt / 16 + tri_sin(e * 70 + pt * 16) / 9;
            int f = fx_frame(fx, fx2, pt + e);
            if (fx2 == FX_PEBBLE && (e & 4)) f = FX_PEBBLE;   /* SANDBLAST: grit in the dust */
            fx_spr_aff(x, y, f, (e & 2) ? OBANK_FX_B : OBANK_FX_A, 176 + pt * 8, 0);
        }
        impact_when(24, 0, dx, dy);
        impact_when(40, st, dx, dy);
        if (t >= 24 && t < 52) anim.tint_amount = 6;
        anim.bg_amount = t > 10 && t < 54 ? tint_amt : 0;
        if (anim.type == T_BLAZE && t > 10 && t < 54) anim.wobble = 2;   /* heat shimmer */
        break;
    }
    case AK_BEAM: {
        /* charge sparkle, then the beam grows across and holds */
        int len = t < 10 ? 0 : t < 22 ? (t - 10) * 16 / 12 : t < 44 ? 16 : 16 - (t - 44) * 16 / 14;
        if (t < 10) {
            if (anim.move == M_GILDED_GLEAM)       /* a coin flips up and catches the light */
                fx_spr_aff2(sx + dir * 14, sy - 10 - t, FX_COIN, OBANK_FX_B, soft_sin(t * 24 + 64) * 4, 256, 0);
            else
                fx_spr_aff(sx + dir * 14, sy - 6, FX_SPARKLE, OBANK_FX_B, 128 + t * 26, t * 8);
            anim.scale_y[side] = 256 + t * 3;
        }
        if (anim.move == M_GILDED_GLEAM && t >= 10 && t < 13) anim.bright = 6;
        if (anim.move == M_LODE_BEAM)  /* the poles swap: red and blue cycle along the beam */
            build_fx_palette(OBANK_FX_A, (t & 4) ? MOVES[M_LODE_BEAM].col1 : MOVES[M_LODE_BEAM].col2,
                             (t & 4) ? MOVES[M_LODE_BEAM].col2 : MOVES[M_LODE_BEAM].col1);
        if (anim.move == M_PRISM_RAY)  /* rainbow cycling */
            build_fx_palette(OBANK_FX_A, hue15(t * 8), hue15(t * 8 + 96));
        if (len > 0) {
            int segs = 12;
            for (int i = 0; i <= segs; i++) {
                if (i * 16 / segs > len) break;
                int x = sx + (dx - sx) * i / segs, y = sy + (dy - sy) * i / segs;
                fx_spr(x, y + ((t >> 1) & 1), fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A);
            }
        }
        impact_when(22, st, dx, dy);
        if (t >= 22 && t < 44) {
            if (fx2 != fx) fx_spr(dx + tri_sin(t * 20) / 6, dy + tri_sin(t * 33) / 6, fx2, OBANK_FX_B);
            if (anim.move == M_WINTER_RAY && (t & 3) == 0)
                part_add(PK_FX, dx + fx_rand(40) - 20, dy + fx_rand(30) - 15, 0, -4,
                         FX_SNOWFLAKE, OBANK_FX_B, 16, 0);
            anim.tint_amount = 8;
        }
        anim.bg_amount = t >= 16 && t < 48 ? tint_amt : 0;
        break;
    }
    case AK_RAIN: {
        /* things fall from above; one impact per falling object */
        int fall = 16;
        int step = anim.variant ? 0 : 7;
        for (int i = 0; i < n; i++) {
            int pt = t - 4 - i * step;
            if (pt < 0) continue;
            int ox = anim.variant ? ((anim.variant * 23) % 41) - 20 : ((i * 23) % 41) - 20;
            int oy = ((i * 11) % 13) - 6;
            if (pt < fall) {
                int y = dy - 80 + (80 + oy) * ease_in(pt, fall) / 256;
                int x = dx + ox + (fx == FX_METEOR ? (fall - pt) * 3 : 0);
                if (fx == FX_SNOWFLAKE) x += soft_sin(pt * 16 + i * 50) / 5;
                if (fx == FX_ROCK || fx == FX_SHARD) fx_spr_aff(x, y, fx, OBANK_FX_A, 256, pt * 12 * (i & 1 ? 1 : -1));
                else fx_spr(x, y, fx, OBANK_FX_A);
            } else if (pt < fall + 12) {
                int it = pt - fall;
                if (fx == FX_SNOWFLAKE) {
                    if (it & 2) fx_spr(dx + ox, dy + oy, FX_SPARKLE, OBANK_FX_B);
                    impact_when(4 + i * step + fall, 0, dx + ox, dy + oy);
                } else {
                    impact_when(4 + i * step + fall, i == n - 1 ? st : 0, dx + ox, dy + oy);
                    if (it < 8) fx_spr(dx + ox, dy + oy, fx2 == FX_PEBBLE ? FX_IMPACT_SMALL : FX_IMPACT,
                                       OBANK_FX_HIT);
                    if ((fx2 == FX_PEBBLE || fx == FX_SHARD) && it < 10) {
                        fx_spr(dx + ox - it * 2, dy + oy + 6 - (it * (10 - it)) / 3, fx2 == FX_PEBBLE ? FX_PEBBLE : FX_SNOWFLAKE, OBANK_FX_A);
                        fx_spr(dx + ox + it * 2, dy + oy + 4 - (it * (10 - it)) / 3, fx2 == FX_PEBBLE ? FX_PEBBLE : FX_SNOWFLAKE, OBANK_FX_A);
                    }
                }
            }
        }
        if (fx == FX_SNOWFLAKE) anim.tint_amount = t > 20 ? 7 : 0;
        if (fx == FX_METEOR || fx == FX_SNOWFLAKE || big) anim.bg_amount = t < anim.dur - 6 ? tint_amt : 0;
        break;
    }
    case AK_BOLT: {
        /* the sky darkens, a (forked) bolt strikes, sparks crawl */
        anim.bg_amount = t < 44 ? 8 : 0;
        anim.bg_color = RGB15(4, 4, 12);
        int strikes = n > 1 ? 2 : 1;
        for (int k = 0; k < strikes; k++) {
            int t0 = 12 + k * 10;
            if (t >= t0 && t < t0 + 10 && ((t >> 1) & 1) == 0) {
                int fork = k ? 10 : -4;
                for (int y = -8; y < dy; y += 16) {
                    int zig = ((y >> 4) & 1) ? 3 : -3;
                    fx_spr(dx + zig + fork * (dy - y) / 64, y, FX_BOLT, OBANK_FX_A);
                }
            }
            if (t >= t0 && t < t0 + 3) anim.bright = 8;
            impact_when(t0 + 1, k == strikes - 1 ? st : 0, dx, dy);
        }
        if (t >= 14 && t < 44)
            for (int k = 0; k < 3; k++) {
                int a = t * 18 + k * 85;
                if ((t + k) & 2) fx_spr(dx + tri_sin(a) / 3, dy + tri_sin(a + 64) / 4, fx2, OBANK_FX_A);
            }
        if (t >= 14) anim.tint_amount = 8;
        break;
    }
    case AK_BURST: {
        /* pops / bubbles erupting all around the foe */
        for (int i = 0; i < n + 3; i++) {
            int pt = t - 6 - i * 4;
            if (pt < 0 || pt >= 14) continue;
            int ox = ((i * 29) % 44) - 22, oy = ((i * 17) % 34) - 17;
            int f = fx_frame(fx, fx2, pt + i);
            if (fx == FX_GLOB) f = (pt & 4) ? FX_BUBBLE : FX_GLOB;
            fx_spr_aff(dx + ox, dy + oy - (fx == FX_GLOB ? pt : 0), f, (i & 1) ? OBANK_FX_B : OBANK_FX_A,
                       pt < 4 ? 128 + pt * 48 : 320 - pt * 8, 0);
            if (pt == 1 && i < n) impact_when(6 + i * 4 + 1, i == n - 1 ? st : 0, dx + ox, dy + oy);
        }
        anim.bg_amount = big && t > 6 && t < 40 ? tint_amt : 0;
        if (t >= 8 && t < 40) anim.tint_amount = 6;
        if (fx2 == FX_RIVET && t >= 6 && t < 9) anim.bright = 7;   /* FORGE FLASH */
        break;
    }
    case AK_ORBIT: {
        /* motes fly over and circle the foe, tightening, then flare */
        for (int i = 0; i < n; i++) {
            int a = t * 7 + i * 256 / n;
            int r = t < 40 ? 24 : 24 - (t - 40) * 24 / 16;
            if (r < 0) r = 0;
            int x = dx + soft_sin(a + 64) * r / 64, y = dy + soft_sin(a) * r / 128;
            if (t < 14) {
                x = sx + (x - sx) * ease_out(t, 14) / 256;
                y = sy + (y - sy) * ease_out(t, 14) / 256 - soft_sin(t * 9) / 4;
            }
            if (t < 56) fx_spr(x, y, fx_frame(fx, fx2, t + i * 3), (i & 1) ? OBANK_FX_B : OBANK_FX_A);
        }
        if (fx2 == FX_EYES && t > 20 && t < 50) fx_spr(dx, dy - 6, FX_EYES, OBANK_FX_B);
        if (fx2 == FX_ZZZ && t > 44) fx_spr(dx + 14 + (t - 44) / 2, dy - 18 - (t - 44) / 2, FX_ZZZ, OBANK_FX_B);
        impact_when(52, st, dx, dy);
        if (t >= 52 && t < 60) big_spr(dx, dy, FXB_GLOW, OBANK_FX_A, 128 + (t - 52) * 32, 128 + (t - 52) * 32);
        if (t >= 44) anim.tint_amount = (t & 4) ? 10 : 4;
        if (anim.type == T_DUSK) anim.bg_amount = t < 58 ? tint_amt : 0;
        if (fx == FX_SPARK_B) anim.mon_dx[foe] = t > 20 ? ((t & 2) ? 1 : -1) : 0;   /* TINGLE jitter */
        break;
    }
    case AK_WAVE: {
        /* a swell rolls in from behind the attacker and crashes over */
        for (int row = 0; row < 2; row++)
            for (int i = 0; i < n; i++) {
                int base = side == SIDE_ALLY ? -30 : 270;
                int x = base + dir * (t * 5 - i * 14 - row * 10);
                int y = dy - 14 + row * 20 + tri_sin(t * 12 + i * 40) / 10;
                if (x < -16 || x > 256) continue;
                int f = (fx == FX_WAVE || !(i & 1)) ? fx : fx2;
                fx_spr_flip(x, y, f, row ? OBANK_FX_B : OBANK_FX_A, dir < 0 ? ATTR1_HFLIP : 0);
            }
        impact_when(26, st, dx, dy);
        if (t > 20 && t < 52) {
            anim.tint_amount = 5;
            if (anim.move == M_UNDERTOW) anim.mon_dy[foe] = ease_out(t - 20, 12) * 8 / 256 - (t > 40 ? (t - 40) * 8 / 12 : 0);
        }
        anim.bg_amount = t > 10 && t < 54 ? tint_amt : 0;
        break;
    }
    case AK_QUAKE: {
        shake(t < 44 ? 40 : 0, 1);
        for (int i = 0; i < n; i++) {
            int pt = (t + i * 9) % 30;
            fx_spr(dx - 30 + i * 60 / (n > 1 ? n - 1 : 1), side_gy(foe) - pt, (i & 1) ? fx2 : fx, OBANK_FX_A);
        }
        impact_when(20, st, dx, dy);
        break;
    }
    case AK_BUFF: {
        /* the user draws power in; particles rise around it */
        for (int i = 0; i < n; i++) {
            int pt = (t + i * 11) % 24;
            if (pt < 18)
                fx_spr(sx + ((i * 37) % 48) - 24 + soft_sin(pt * 10 + i * 40) / 10, sy + 20 - pt * 2, fx,
                       (i & 1) ? OBANK_FX_B : OBANK_FX_A);
        }
        anim.tint_side = side;
        anim.tint_amount = 6 + tri_sin(t * 8) / 12;
        if (anim.move == M_UPDRAFT) anim.mon_dy[side] = -ease_out(t, 20) * 10 / 256 + (t > 36 ? (t - 36) * 10 / 16 : 0);
        if (fx2 != fx && t > 30 && (t & 2)) fx_spr(sx, sy - 22, fx2, OBANK_FX_B);
        self_pulse_when(30);
        break;
    }
    case AK_DEBUFF: {
        if (fx == FX_EYES) {   /* STARE DOWN: the lights go down, eyes glow */
            anim.bg_amount = t < 48 ? 10 : 0;
            anim.bg_color = RGB15(2, 1, 6);
            if (t < 20) {
                fx_spr_aff(sx + dir * 6, sy - 8, FX_EYES, OBANK_FX_A, 256 + (t > 10 ? (t - 10) * 12 : 0), 0);
            } else {
                fx_spr_aff(dx, dy - 4, FX_EYES, (t & 4) ? OBANK_FX_A : OBANK_FX_B, 320, 0);
                anim.mon_dx[foe] = (t & 2) ? 1 : -1;
                anim.scale_y[foe] = 240;
            }
            impact_when(24, 0, dx, dy);
            break;
        }
        if (anim.move == M_POUT) anim.mon_dx[side] = t < 16 ? ((t & 2) ? 2 : -2) : 0;
        if (anim.move == M_GRIT_KICK) anim.mon_dy[side] = -soft_sin(clampi(t, 0, 16) * 8) / 8;
        for (int i = 0; i < n; i++) {
            int pt = t - 6 - i * 6;
            if (pt < 0) continue;
            if (pt < 24) {
                int x = sx + (dx - sx) * pt / 24;
                int y = sy + (dy - sy) * pt / 24 + tri_sin(pt * 20 + i * 70) / 5;
                fx_spr(x, y, fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A);
            } else if (pt < 36) {
                fx_spr(dx + (i - 1) * 12, dy - 8 + ((pt >> 1) & 1), (fx2 != fx && (pt & 4)) ? fx2 : fx, OBANK_FX_A);
            }
        }
        if (fx2 == FX_TEAR && t < 20)   /* POUT: tears roll down */
            for (int k = 0; k < 2; k++) fx_spr(sx + (k ? 8 : -8), sy - 10 + (t + k * 7) % 14, FX_TEAR, OBANK_FX_B);
        impact_when(34, 0, dx, dy);
        break;
    }
    case AK_FANGS: {
        int rot = anim.move == M_PINCER ? 64 : 0;    /* mandibles close sideways */
        if (anim.move == M_SNAP) {
            anim.bg_amount = t < 20 ? 10 : 0;
            anim.bg_color = RGB15(2, 1, 6);
        }
        for (int i = 0; i < n; i++) {
            int ft = t - 4 - i * 14;
            if (ft < 0 || ft >= 26) continue;
            int gap = ft < 10 ? 22 - ft * 2 : ft < 16 ? 0 : (ft - 16);
            if (ft < 6) gap = 22 + ft;                 /* open wide first */
            if (rot) {
                fx_spr_aff(dx - 4 - gap, dy, FX_FANG_TOP, OBANK_FX_A, 256, 192);
                fx_spr_aff(dx + 8 + gap, dy, FX_FANG_TOP, OBANK_FX_A, 256, 64);
            } else {
                fx_spr(dx, dy - 4 - gap, FX_FANG_TOP, OBANK_FX_A);
                fx_spr(dx, dy + 8 + gap, FX_FANG_BOTTOM, OBANK_FX_A);
            }
            impact_when(4 + i * 14 + 10, i == n - 1 ? st : 0, dx, dy);
            if (ft >= 10 && ft < 22) {
                int it = ft - 10;
                if (fx2 == FX_FLAME_A) {
                    fx_spr(dx - 10, dy - it, (it >> 2) & 1 ? FX_FLAME_B : FX_FLAME_A, OBANK_FX_B);
                    fx_spr(dx + 10, dy - it, (it >> 2) & 1 ? FX_FLAME_A : FX_FLAME_B, OBANK_FX_B);
                } else if (anim.move == M_GNASH) {
                    anim.mon_dx[foe] = (it & 1) ? 2 : -2;   /* grinding */
                }
            }
        }
        break;
    }
    case AK_DRAIN: {
        for (int i = 0; i < n; i++) {
            int pt = t - 12 - i * 5;
            if (pt < 0 || pt >= 26) continue;
            int x = dx + (sx - dx) * ease_in(pt, 26) / 256;
            int y = dy + (sy - dy) * pt / 26 - soft_sin(pt * 5) * (i - n / 2) / 5;
            fx_spr_aff(x, y, fx, OBANK_FX_A, 320 - pt * 5, 0);
        }
        impact_when(10, 0, dx, dy);
        if (t < 18) anim.tint_amount = 9;
        if (t >= 40) {
            anim.tint_side = side;
            anim.tint_amount = 7;
            if (t & 2) fx_spr(sx + tri_sin(t * 16) / 4, sy - 10 + tri_sin(t * 16 + 64) / 5, fx2, OBANK_FX_B);
        }
        if (fx2 == FX_SKULL && t < 20 && (t & 2)) fx_spr(dx, dy - 20, FX_SKULL, OBANK_FX_B);
        if (t == 12) sfx_play(SFX_DRAIN);
        break;
    }
    case AK_DASH: {
        /* a blur of afterimages that strikes first */
        int l = t < 4 ? -t : t < 10 ? -4 + (48 + 4) * ease_in(t - 4, 6) / 256 : t < 16 ? 48 :
                t < 26 ? 48 - 48 * ease_out(t - 16, 10) / 256 : 0;
        anim.mon_dx[side] = dir * l;
        anim.mon_dy[side] = -dir * l / 3;
        anim.afterimage = t >= 4 && t < 18;
        if (t >= 4 && t < 16)
            for (int k = 1; k <= 2; k++)
                fx_spr(sx + dir * (l - k * 14), sy - dir * (l - k * 14) / 3 + k * 3, fx2, OBANK_FX_B);
        impact_when(10, st, dx - dir * 6, dy);
        if (!fx_is_hit(fx) && t >= 10 && t < 16) fx_spr(dx - dir * 8, dy, fx, OBANK_FX_A);   /* COUNTERJAB */
        if (fx2 == FX_FLAKE && t >= 10 && t < 20)                                         /* IRON TAP rings */
            fx_spr_aff(dx - dir * 6, dy, FX_RING, OBANK_FX_B, 160 + (t - 10) * 24, 0);
        break;
    }
    case AK_SLAM: {
        /* BELLY FLOP: crouch, leap up in an arc, land on the foe, dust ring */
        int jt = t - 8;
        if (t < 8) {
            anim.scale_x[side] = 256 + t * 5;
            anim.scale_y[side] = 256 - t * 5;
        } else if (jt < 18) {
            int k = jt * 256 / 18;
            anim.mon_dx[side] = dir * (dx - sx) * k / 256;
            anim.mon_dy[side] = (dy - sy) * k / 256 - soft_sin(jt * 128 / 18) * 50 / 64;
            anim.scale_x[side] = 232;
            anim.scale_y[side] = 284;
        } else if (jt < 26) {
            anim.mon_dx[side] = dir * (dx - sx);
            anim.mon_dy[side] = dy - sy;
            anim.scale_x[side] = 300 - (jt - 18) * 5;
            anim.scale_y[side] = 212 + (jt - 18) * 5;
        } else {
            int k = 256 - ease_out(jt - 26, 18);
            anim.mon_dx[side] = dir * (dx - sx) * k / 256;
            anim.mon_dy[side] = (dy - sy) * k / 256 - soft_sin((jt - 26) * 128 / 18) * 12 / 64;
        }
        if (impact_when(26, st, dx, dy))
            for (int k = 0; k < 8; k++)
                part_add(PK_FX, dx, side_gy(foe) - 4, soft_sin(k * 32 + 64) * 3 / 2, soft_sin(k * 32) / 3,
                         fx2 == FX_CRACK ? fx : fx2, OBANK_FX_B, 16, 0);
        if (fx2 == FX_CRACK && jt >= 18 && jt < 40)   /* OSSIFY: the foe stiffens and cracks */
            for (int k = 0; k < 2; k++) fx_spr_flip(dx + (k ? 8 : -8), dy - 4 + k * 8, FX_CRACK, OBANK_FX_A, k ? ATTR1_HFLIP : 0);
        break;
    }
    case AK_WHIP:
        for (int i = 0; i < n; i++) {
            int wt = t - 4 - i * 12;
            if (wt < 0 || wt >= 22) continue;
            int reach = wt < 10 ? wt : wt < 14 ? 10 : 22 - wt;
            for (int s = 1; s <= reach; s++) {
                int x = sx + (dx - sx) * s / 10;
                int y = sy + (dy - sy) * s / 10 - tri_sin(s * 12 + i * 128 + wt * 6) / 5;
                fx_spr(x, y, FX_VINE, OBANK_FX_A);
            }
            impact_when(4 + i * 12 + 9, i == n - 1 ? st : 0, dx, dy);
            if (wt >= 9 && wt < 16) fx_spr(dx - 8 + (wt - 9) * 3, dy - 10 - (wt - 9) * 2, fx2, OBANK_FX_B);
        }
        break;
    case AK_PSYCHIC: {
        /* rings pulse out around the foe; everything sways */
        if (anim.move == M_DAYDREAM) build_fx_palette(OBANK_FX_A, hue15(t * 6), hue15(t * 6 + 64));
        for (int i = 0; i < n + 1; i++) {
            int pt = t - 6 - i * 8;
            if (pt < 0 || pt >= 28) continue;
            fx_spr_aff2(dx, dy, FX_RING, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 96 + pt * 14, 64 + pt * 9, 0);
        }
        anim.mon_dx[foe] = soft_sin(t * 14) / 16;
        anim.tint_amount = 8 + tri_sin(t * 10) / 16;
        impact_when(22, st, dx, dy);
        anim.bg_amount = big && t < anim.dur - 6 ? tint_amt : 0;
        break;
    }
    case AK_POWDER: {
        /* a puff drifts down over the foe */
        for (int i = 0; i < n; i++) {
            int pt = t - i * 4;
            if (pt < 0 || pt >= 44) continue;
            int x = dx + ((i * 17) % 44) - 22 + soft_sin(pt * 8 + i * 30) / 6;
            int y = dy - 44 + pt * 3 / 2;
            fx_spr(x, y, (i % 3) ? fx : fx2 == FX_STEAM ? FX_POWDER : fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A);
        }
        if (fx2 == FX_STEAM && t < 40)   /* SPORE CLOUD: a cloud hangs over it */
            fx_spr_aff(dx, dy - 20 + t / 4, FX_STEAM, OBANK_FX_A, 256 + t * 4, 0);
        if (fx == FX_SNOWFLAKE && fx2 == FX_DUST && t > 28)   /* SNOWDRIFT: snow piles up */
            fx_spr_aff2(dx, side_gy(foe) - 6, FX_DUST, OBANK_FX_B, 320 + (t - 28) * 6, 256, 0);
        if (fx2 == FX_ZZZ && t > 36)      /* DOZE POLLEN: Zzz */
            fx_spr(dx + 16 + (t - 36) / 3, dy - 20 - (t - 36) / 2, FX_ZZZ, OBANK_FX_B);
        if (t > 44) anim.tint_amount = (t & 4) ? 9 : 5;
        impact_when(46, 0, dx, dy);
        break;
    }
    case AK_STRIKE: {
        /* fists fly in from above-left/right */
        int step = 14;
        for (int i = 0; i < n; i++) {
            int s0 = anim.variant ? 2 : 4 + i * step;
            int stt = t - s0;
            if (stt < 0 || stt >= 20) continue;
            int from = ((i + anim.variant) & 1) ? 1 : -1;
            if (stt < 8) {
                int k = ease_in(stt, 8);
                int x = dx + from * (30 - 30 * k / 256), y = dy - 30 + 30 * k / 256;
                fx_spr_aff(x, y, fx, OBANK_FX_A, 320 - stt * 8, from > 0 ? 16 : -16);
            } else if (stt < 14) {
                fx_spr(dx + from * 4, dy, FX_IMPACT, OBANK_FX_HIT);
            }
            impact_when(s0 + 8, (i == n - 1 && (anim.flags & HITF_LAST)) ? st + (anim.move == M_HAMMER_FIST) : 0,
                        dx + from * 4, dy);
        }
        if (anim.move == M_HAMMER_FIST && t < 6) anim.mon_dy[side] = -t;
        break;
    }
    case AK_ROAR: {
        /* rears up, then shockwave rings burst out; heavy shake */
        int status = MOVES[anim.move].cat == CAT_STATUS;
        if (t < 10) {
            anim.scale_x[side] = 256 - t * 3;
            anim.scale_y[side] = 256 + t * 5;
            anim.mon_dy[side] = -t / 2;
        } else if (t < 44) {
            anim.scale_x[side] = 286 + ((t & 2) ? 6 : 0);
            anim.scale_y[side] = 236;
            if (t == 10) sfx_play(SFX_ROAR);
            shake(status ? 24 : 64, 0);
        }
        for (int i = 0; i < n + 2; i++) {
            int pt = t - 10 - i * 7;
            if (pt < 0 || pt >= 24) continue;
            int x = status ? sx : sx + (dx - sx) * pt / 26;
            int y = status ? sy - 8 : sy - 8 + (dy - sy) * pt / 26;
            int sc = 96 + ease_out(pt, 24) * 420 / 256;
            if (sc > 512) sc = 512;
            if (pt < 20 || (pt & 1)) big_spr(x, y, FXB_RING, (i & 1) ? OBANK_FX_B : OBANK_FX_A, sc, sc * 3 / 4);
        }
        if (fx2 == FX_EYES && t > 8 && t < 44) fx_spr(sx + dir * 8, sy - 10, FX_EYES, OBANK_FX_B);
        if (fx2 == FX_NOTE && t > 12 && t < 40 && (t & 4))
            fx_spr(sx + dir * 20, sy - 20 - (t - 12) / 2, FX_NOTE, OBANK_FX_B);
        if (status) {
            anim.tint_side = side;
            anim.tint_amount = t > 10 ? 8 : 0;
            self_pulse_when(20);
        } else {
            impact_when(24, st, dx, dy);
            anim.bg_amount = t > 8 && t < 50 ? tint_amt : 0;
        }
        break;
    }
    case AK_GEYSER: {
        /* rumble, the ground under the foe bulges, then a scalding column */
        int gy = side_gy(foe);
        if (t < 20) {
            shake(12 + t, 1);
            if (t & 4) fx_spr(dx + ((t * 7) % 20) - 10, gy - 2, FX_DUST, OBANK_FX_B);
        } else if (t < 50) {
            int h = ease_out(t - 20, 10) * 72 / 256;
            if (t > 40) h = h * (50 - t) / 10;
            for (int k = 0; k < h; k += 10) {
                int w = (k / 10) & 1 ? 4 : -4;
                fx_spr(dx + w + tri_sin(t * 20 + k * 8) / 16, gy - k, (k / 10 + t / 2) & 1 ? FX_DROP : FX_BUBBLE,
                       (k / 10) & 1 ? OBANK_FX_B : OBANK_FX_A);
                fx_spr(dx - w + 8, gy - k - 5, FX_DROP, OBANK_FX_A);
            }
            if (t > 26) fx_spr_aff(dx + tri_sin(t * 9) / 8, gy - h - 6, fx2, OBANK_FX_B, 256 + (t - 26) * 8, 0);
            anim.mon_dy[foe] = -h / 4;
            anim.tint_amount = 7;
        }
        impact_when(22, st, dx, dy);
        anim.bg_amount = t > 16 && t < 54 ? tint_amt : 0;
        break;
    }
    case AK_SUNSHAFT: {
        /* the sky brightens and a shaft of sunlight falls on the foe */
        anim.bg_color = RGB15(31, 31, 20);
        anim.bg_amount = t < 56 ? (t < 10 ? t : 9) : 0;
        if (t < 14) fx_spr_aff(sx, sy - 24, FX_SPARKLE, OBANK_FX_B, 128 + t * 20, t * 6);
        if (t >= 14 && t < 52) {
            int h = ease_in(t - 14, 8) * (dy + 16) / 256;
            int wid = t < 40 ? 256 + ((t & 2) ? 32 : 0) : 256 - (t - 40) * 18;
            for (int y = 0; y < h; y += 16)
                fx_spr_aff2(dx, y, fx, (y & 16) ? OBANK_FX_B : OBANK_FX_A, wid * 3 / 2, 256, 0);
            if (t > 22) fx_spr(dx + tri_sin(t * 21) / 5, dy + tri_sin(t * 13) / 8, fx2, OBANK_FX_B);
            anim.tint_amount = 9;
        }
        if (t >= 22 && t < 25) anim.bright = 6;
        impact_when(22, st, dx, dy);
        break;
    }
    case AK_FAULT: {
        /* the ground splits in a jagged line toward the foe, then heaves */
        int gy0 = side_gy(side) - 6, gy1 = side_gy(foe) - 2;
        int len = t < 26 ? ease_in(t, 26) * 256 / 256 : 256;
        int segs = 11;
        for (int i = 0; i <= segs; i++) {
            if (i * 256 / segs > len) break;
            int x = sx + (dx - sx) * i / segs, y = gy0 + (gy1 - gy0) * i / segs;
            if (t < 58) fx_spr(x, y, fx, OBANK_FX_A);
        }
        if (t < 26) shake(20 + t, 1);
        if (t >= 26 && t < 44) {
            int it = t - 26;
            for (int k = 0; k < 4; k++) {
                int ox = (k - 2) * 12 + 6;
                fx_spr_aff(dx + ox, gy1 - 6 - (it * (18 - it)) / 3 - k * 2, fx2, OBANK_FX_B, 256, it * 16 * (k & 1 ? 1 : -1));
            }
            anim.mon_dy[foe] = -soft_sin(it * 8) / 6;
        }
        impact_when(27, st, dx, dy);
        break;
    }
    case AK_WOBBLE: {
        /* DREAMQUAKE: the whole world wobbles and pixelates */
        int k = t < 12 ? t : t > 48 ? 64 - t : 12;
        anim.wobble = k * 6 / 12;
        anim.mosaic = k * 5 / 12;
        for (int i = 0; i < n; i++) {
            int pt = (t + i * 10) % 30;
            fx_spr_aff2(dx, dy, FX_RING, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 96 + pt * 12, 64 + pt * 7, 0);
        }
        anim.mon_dx[foe] = soft_sin(t * 12) / 10;
        anim.mon_dx[side] = soft_sin(t * 12 + 128) / 20;
        anim.tint_amount = 8;
        anim.bg_amount = t < 56 ? tint_amt : 0;
        impact_when(30, st, dx, dy);
        break;
    }
    case AK_HEAL: {
        /* BASK: sunlight falls on the user; CATNAP: it curls up, Zzz */
        anim.tint_side = side;
        if (fx == FX_SUNRAY) {
            anim.bg_color = RGB15(31, 30, 18);
            anim.bg_amount = t < 52 ? 5 : 0;
            if (t >= 6 && t < 48)
                for (int y = 0; y < sy + 10; y += 16)
                    fx_spr_aff2(sx, y, FX_SUNRAY, OBANK_FX_A, 384, 256, 0);
        } else if (fx == FX_CANDLE) {
            /* LAST RITES: the lights go down, a ring of candles flickers round it */
            anim.bg_color = RGB15(3, 2, 6);
            anim.bg_amount = t < 52 ? (t < 8 ? t : 8) : 0;
            for (int i = 0; i < 5; i++) {
                int a = i * 51 + 20;
                int lit = t > 4 + i * 3;
                if (!lit || t >= 54) continue;
                fx_spr(sx + soft_sin(a + 64) * 30 / 64, side_gy(side) - 8 + soft_sin(a) * 8 / 64,
                       FX_CANDLE, ((t + i * 3) & 4) ? OBANK_FX_A : OBANK_FX_B);
            }
            anim.mon_dy[side] = t > 10 && t < 46 ? -2 : 0;
        } else {
            int curl = t < 12 ? t : t > 44 ? 56 - t : 12;
            anim.scale_x[side] = 256 + curl * 3;
            anim.scale_y[side] = 256 - curl * 4;
            if (t > 10 && t < 46) fx_spr(sx + 18 + (t - 10) / 3, sy - 22 - (t - 10) / 3, FX_ZZZ, OBANK_FX_A);
        }
        for (int i = 0; i < 5; i++) {
            int pt = (t + i * 9) % 30;
            if (t < 48 && (fx != FX_CANDLE || t > 16)) fx_spr(sx - 20 + i * 10, sy + 14 - pt, fx2, OBANK_FX_B);
        }
        anim.tint_amount = 5 + tri_sin(t * 8) / 16;
        if (t == 12) sfx_play(SFX_SPARKLE);
        self_pulse_when(20);
        break;
    }
    case AK_CHARGE: {
        /* charge up (motes rush in, the user glows and trembles), then let go */
        int rel = 38;
        if (t < rel) {
            if (t == 2) sfx_play(SFX_CHARGE);
            for (int i = 0; i < 6; i++) {
                int pt = (t * 2 + i * 11) % 24;
                int a = i * 42 + t * 3;
                int r = 36 - pt * 36 / 24;
                fx_spr(sx + soft_sin(a + 64) * r / 64, sy + soft_sin(a) * r / 64, (i & 1) ? fx2 : FX_SPARKLE,
                       (i & 1) ? OBANK_FX_B : OBANK_FX_A);
            }
            anim.tint_side = side;
            anim.tint_amount = t * 8 / rel;
            anim.mon_dx[side] = t > 20 ? ((t & 1) ? 1 : -1) : 0;
            anim.scale_x[side] = 256 + t;
            anim.scale_y[side] = 256 + t;
            anim.bg_amount = t * tint_amt / rel;
        } else {
            int it = t - rel;
            anim.bg_amount = it < 30 ? tint_amt + 2 : 0;
            if (fx == FX_BOLT) {           /* OVERCHARGE: a huge bolt */
                if (it < 16 && !(it & 2))
                    for (int y = -8; y < dy; y += 16)
                        fx_spr_aff2(dx + (((y >> 4) & 1) ? 4 : -4), y, FX_BOLT, OBANK_FX_A, 384, 256, 0);
                if (it < 3) anim.bright = 10;
                if (it == 0) sfx_play(SFX_THUNDER);
            } else {                        /* SUNFLARE / BRIM BURST: a burst at the foe */
                if (it < 8) {
                    int x = sx + (dx - sx) * it / 8, y = sy + (dy - sy) * it / 8;
                    fx_spr_aff(x, y, FX_BURST, OBANK_FX_A, 256 + it * 16, it * 16);
                } else if (it < 30) {
                    int g = it - 8;
                    big_spr(dx, dy, FXB_GLOW, OBANK_FX_A, 128 + g * 12, 128 + g * 12);
                    fx_spr_aff(dx, dy, FX_BURST, OBANK_FX_B, 384 + g * 8, g * 10);
                    for (int i = 0; i < n; i++) {
                        int a = i * 256 / n + it * 3;
                        fx_spr(dx + soft_sin(a + 64) * g * 3 / 64, dy + soft_sin(a) * g * 2 / 64,
                               fx_frame(fx2, fx2 == FX_FLAME_B ? FX_FLAME_A : fx2, it + i), (i & 1) ? OBANK_FX_B : OBANK_FX_A);
                    }
                }
                if (it >= 8 && it < 11) anim.bright = 8;
            }
            impact_when(fx == FX_BOLT ? rel + 1 : rel + 8, st + 1, dx, dy);
            anim.tint_side = foe;
            if (it > 8) anim.tint_amount = 9;
        }
        break;
    }
    case AK_LURE: {
        /* a friendly flame bobs over, circles the foe, then flares */
        int x, y;
        if (t < 30) {
            x = sx + (dx - sx) * t / 30;
            y = sy - 20 + (dy - sy) * t / 30 + soft_sin(t * 16) / 5;
        } else {
            int a = (t - 30) * 12;
            int r = t < 54 ? 20 : 20 - (t - 54) * 2;
            x = dx + soft_sin(a + 64) * r / 64;
            y = dy - 6 + soft_sin(a) * r / 160 + soft_sin(t * 16) / 8;
        }
        int lf = fx == FX_TRINKET ? FX_TRINKET : FX_WISP;   /* CURSED CURIO: an unlucky trinket */
        if (t < 62) fx_spr_aff(x, y, lf, OBANK_FX_A, 256 + soft_sin(t * 20) / 3, lf == FX_TRINKET ? soft_sin(t * 8) / 3 : 0);
        if (fx2 == FX_EYES && t > 34 && t < 62 && (t & 8)) fx_spr(dx, dy - 8, FX_EYES, OBANK_FX_B);
        if (t > 8 && (t & 3) == 0 && t < 60) part_add(PK_FX, x, y + 4, 0, 3, FX_SPARKLE, OBANK_FX_B, 10, 0);
        if (t >= 62 && t < 72) big_spr(dx, dy, FXB_GLOW, OBANK_FX_A, 160 + (t - 62) * 16, 160 + (t - 62) * 16);
        impact_when(62, 0, dx, dy);
        anim.bg_amount = t > 20 && t < 70 ? 4 : 0;
        break;
    }
    case AK_STOOP: {
        /* folds its wings, rises out of sight, drops on the foe from above */
        if (t < 16) {
            anim.mon_dy[side] = -ease_in(t, 16) * 140 / 256;
            anim.scale_x[side] = 230;
            anim.scale_y[side] = 290;
        } else if (t < 22) {
            anim.hide[side] = 1;
        } else if (t < 30) {
            int k = ease_in(t - 22, 8);
            anim.mon_dx[side] = dir * (dx - sx);
            anim.mon_dy[side] = (dy - sy) - 120 + 120 * k / 256;
            anim.scale_x[side] = 220;
            anim.scale_y[side] = 300;
            anim.afterimage = 1;
            fx_spr(dx - 10, dy - 40 + (t - 22) * 4, FX_SPEEDLINE, OBANK_FX_B);
        } else if (t < 36) {
            anim.mon_dx[side] = dir * (dx - sx);
            anim.mon_dy[side] = dy - sy - 10;
        } else {
            int k = 256 - ease_out(t - 36, 18);
            anim.mon_dx[side] = dir * (dx - sx) * k / 256;
            anim.mon_dy[side] = (dy - sy - 10) * k / 256;
        }
        if (impact_when(30, st, dx, dy))
            for (int k = 0; k < 5; k++)
                part_add(PK_SPARK, dx, dy, soft_sin(k * 51 + 64) * 2, soft_sin(k * 51) - 20, fx2, OBANK_FX_B, 20, 2);
        break;
    }
    case AK_HAYMAKER: {
        /* a huge wind-up that trembles, then the swing */
        if (t < 24) {
            anim.mon_dx[side] = -dir * ease_out(t, 24) * 12 / 256 + ((t > 12 && (t & 1)) ? 1 : 0);
            anim.scale_x[side] = 256 - t * 2;
            anim.scale_y[side] = 256 + t * 2;
            if (t > 8) fx_spr_aff(sx - dir * 22, sy - 10, fx, OBANK_FX_A, 256 + (t - 8) * 6, -dir * t * 2);
        } else if (t < 32) {
            int k = ease_in(t - 24, 8);
            anim.mon_dx[side] = -dir * 12 + dir * 50 * k / 256;
            int x = sx + (dx - sx) * k / 256, y = sy - 20 + (dy - sy + 20) * k / 256;
            fx_spr_aff(x, y, fx, OBANK_FX_A, 384, dir * (t - 24) * 16);
            fx_spr(x - dir * 14, y + 4, FX_SPEEDLINE, OBANK_FX_B);
        } else {
            anim.mon_dx[side] = dir * 38 * (256 - ease_out(t - 32, 20)) / 256;
            if (t < 40) big_spr(dx, dy, FXB_RING, OBANK_FX_HIT, 128 + (t - 32) * 24, 128 + (t - 32) * 24);
        }
        impact_when(32, st + 1, dx, dy);
        break;
    }
    case AK_SPIRAL: {
        /* LEAF FLURRY: a spiral of razor leaves corkscrews into the foe */
        for (int i = 0; i < n; i++) {
            int pt = t - 4 - i * 3;
            if (pt < 0 || pt >= 26) continue;
            int bx = sx + (dx - sx) * pt / 22, by = sy + (dy - sy) * pt / 22;
            int a = pt * 20 + i * 32;
            int r = 14 - (pt > 20 ? (pt - 20) * 2 : 0);
            fx_spr(bx + soft_sin(a + 64) * r / 64, by + soft_sin(a) * r / 64, ((pt >> 2) & 1) ? fx2 : fx,
                   (i & 1) ? OBANK_FX_B : OBANK_FX_A);
        }
        impact_when(26, 0, dx, dy);
        impact_when(34, st, dx, dy);
        break;
    }
    case AK_RIPPLE: {
        /* STILL POND: calm rings spread around the user */
        anim.tint_side = side;
        anim.tint_amount = 6;
        anim.bg_amount = t < 50 ? 4 : 0;
        for (int i = 0; i < n; i++) {
            int pt = (t + i * 14) % 42;
            if (t + 10 > anim.dur && pt < 10) continue;
            fx_spr_aff2(sx, side_gy(side) - 8, FX_RING, (i & 1) ? OBANK_FX_B : OBANK_FX_A,
                        128 + pt * 10, 48 + pt * 3, 0);
        }
        if (t > 8 && t < 40 && ((t >> 3) & 1)) fx_spr(sx, sy - 26, fx2, OBANK_FX_B);
        self_pulse_when(20);
        break;
    }
    case AK_WRAP: {
        /* SILK SNARE: threads shoot over and wind round the foe */
        for (int i = 0; i < n; i++) {
            int pt = t - 4 - i * 6;
            if (pt < 0) continue;
            if (pt < 16) {
                int x = sx + (dx - sx) * pt / 16, y = sy + (dy - sy) * pt / 16 - soft_sin(pt * 8) / 4;
                fx_spr(x, y, fx, OBANK_FX_A);
            } else if (t < 52) {
                int yy = dy - 12 + i * 10;
                for (int k = -2; k <= 1; k++) fx_spr(dx + k * 14 + 7, yy + (k & 1), fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A);
            }
        }
        if (t > 22 && t < 52) {
            anim.scale_x[foe] = 240;
            anim.mon_dx[foe] = (t & 4) ? 1 : -1;
        }
        impact_when(22, 0, dx, dy);
        break;
    }
    case AK_GUARD: {
        /* BRACE / STONESKIN: plant the feet (squash), harden, a glint sweeps */
        int k = t < 10 ? t : t < 34 ? 10 : 46 - t;
        if (k < 0) k = 0;
        anim.scale_x[side] = 256 + k * 4;
        anim.scale_y[side] = 256 - k * 4;
        anim.tint_side = side;
        anim.tint_amount = k * 8 / 10;
        if ((fx == FX_PEBBLE || fx == FX_FLAKE || fx == FX_VINE) && t < 20)
            for (int i = 0; i < 6; i++) {
                int a = i * 42;
                int r = 40 - t * 2;
                fx_spr(sx + soft_sin(a + 64) * r / 64, sy + soft_sin(a) * r / 80, fx, OBANK_FX_A);
            }
        if (fx == FX_VINE && t >= 18 && t < 42)   /* THORN WALL: a hedge stands in front */
            for (int i = 0; i < 4; i++)
                fx_spr(sx - 24 + i * 16 + dir * 16, side_gy(side) - 10 - ((i & 1) ? 4 : 0), (i & 1) ? fx2 : fx,
                       (i & 1) ? OBANK_FX_B : OBANK_FX_A);
        if (t >= 18 && t < 32) {
            int gx = sx - 24 + (t - 18) * 4;
            fx_spr_aff(gx, sy - 12 + (t - 18), FX_SPARKLE, OBANK_FX_B, 320, t * 8);
        }
        self_pulse_when(10);
        break;
    }
    case AK_RUSH: {
        /* BULLRUSH: long wind-up, speed lines, huge hit, bounced back */
        int l;
        if (t < 12) l = -ease_out(t, 12) * 12 / 256;
        else if (t < 20) l = -12 + 60 * ease_in(t - 12, 8) / 256;
        else if (t < 24) l = 48;
        else if (t < 34) l = 48 - 70 * ease_out(t - 24, 10) / 256;   /* jolted back past home */
        else l = -22 + 22 * ease_out(t - 34, 14) / 256;
        anim.mon_dx[side] = dir * l;
        anim.mon_dy[side] = -dir * l / 3;
        if (t < 12) {
            anim.scale_x[side] = 256 - t * 3;
            anim.scale_y[side] = 256 + t * 3;
            if (t & 2) fx_spr(sx - dir * 20, side_gy(side) - 6, FX_DUST, OBANK_FX_B);
        }
        anim.afterimage = t >= 12 && t < 22;
        if (t >= 12 && t < 22)
            for (int k = 0; k < 3; k++)
                fx_spr(sx + dir * (l - 16 - k * 12), sy - 8 + k * 8 - dir * l / 3,
                       fx == FX_IMPACT ? FX_SPEEDLINE : fx_is_hit(fx) ? fx2 : fx, OBANK_FX_B);
        if (fx == FX_BUG && t < 34)             /* SWARM RUSH: the swarm rides along */
            for (int k = 0; k < n; k++) {
                int a = t * 16 + k * 256 / n;
                fx_spr(sx + dir * l + soft_sin(a + 64) / 3, sy - 4 - dir * l / 3 + soft_sin(a) / 5, FX_BUG,
                       (k & 1) ? OBANK_FX_B : OBANK_FX_A);
            }
        if (fx == FX_METEOR && t >= 12 && t < 24)   /* COMET DASH: it wears a comet's head */
            fx_spr_aff(sx + dir * l + dir * 10, sy - 8 - dir * l / 3, FX_METEOR, OBANK_FX_A, 384, 0);
        if (t >= 24 && t < 34 && (t & 1)) anim.mon_dy[side] -= 2;
        impact_when(20, st + 1, dx - dir * 8, dy);
        break;
    }
    /* ---------------- expansion kinds ---------------- */
    case AK_RATTLE: {
        /* bones gather round the foe, rattle and jitter, then clatter in */
        anim.mon_dx[side] = t < 24 ? ((t & 2) ? 1 : -1) : 0;
        if (t < 30)
            for (int i = 0; i < n; i++) {
                if (t < 6 && ((t + i) & 1)) continue;          /* flicker in */
                int a = i * 256 / n + t * 5;
                int r = t < 8 ? 36 - t : 28;
                if (t >= 22) r = 28 - 28 * ease_in(t - 22, 8) / 256;
                int jx = ((t + i) & 2) ? 2 : -2, jy = ((t + i * 3) & 4) ? 1 : -1;
                fx_spr_aff(dx + soft_sin(a + 64) * r / 64 + jx, dy + soft_sin(a) * r / 96 + jy, fx,
                           (i & 1) ? OBANK_FX_B : OBANK_FX_A, 256, t * 20 + i * 50);
            }
        if (t > 12 && t < 30) anim.mon_dx[foe] = (t & 2) ? 1 : -1;
        if (impact_when(30, st, dx, dy))
            for (int k = 0; k < n; k++)
                part_add(PK_SPARK, dx, dy, soft_sin(k * 256 / n + 64) * 14 / 16,
                         soft_sin(k * 256 / n) * 14 / 16 - 24, fx, OBANK_FX_A, 18, 3);
        if (t >= 30 && t < 36) fx_spr(dx, dy, fx2, OBANK_FX_HIT);
        break;
    }
    case AK_MIST: {
        /* a cold fog bank rolls along the ground to the foe and rises round it */
        int gy0 = side_gy(side) - 6, gy1 = side_gy(foe) - 6;
        for (int i = 0; i < n; i++) {
            int pt = t - i * 3;
            if (pt < 0 || pt >= 52) continue;
            int k = ease_out(pt < 26 ? pt : 26, 26);
            int x = sx + (dx - sx) * k / 256 + ((i * 19) % 36) - 18;
            int y = gy0 + (gy1 - gy0) * k / 256 - ((i * 7) % 8);
            if (pt > 26) y -= (pt - 26) * (1 + (i % 3)) / 2;
            int sc = 320 + soft_sin(pt * 8 + i * 40) / 2;
            if (pt > 44) sc -= (pt - 44) * 24;
            fx_spr_aff(x, y, fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A, sc, 0);
        }
        if (t > 30 && t < 54 && (t & 3) == 0)
            part_add(PK_FX, dx + fx_rand(40) - 20, dy + fx_rand(24) - 20, 0, 5, fx2, OBANK_FX_B, 14, 0);
        impact_when(30, st, dx, dy);
        if (t > 30 && t < 56) {
            anim.tint_amount = 7;
            anim.mon_dx[foe] = (t & 2) ? 1 : -1;
        }
        anim.bg_amount = t > 6 && t < 56 ? tint_amt : 0;
        break;
    }
    case AK_SHROUD: {
        /* grave mist spirals up the user and wraps it */
        anim.tint_side = side;
        for (int i = 0; i < n; i++) {
            int pt = t - i * 4;
            if (pt < 0 || pt >= 44) continue;
            int a = pt * 10 + i * 256 / n;
            int r = 30 - pt * 16 / 44;
            int x = sx + soft_sin(a + 64) * r / 64;
            int y = side_gy(side) - 4 - pt * 3 / 2 + soft_sin(a) * r / 192;
            fx_spr_aff(x, y, (pt & 8) ? fx : fx2, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 224 + pt * 3, 0);
        }
        if (t > 24 && t < 50 && (t & 1)) fx_spr_aff(sx, sy - 4, fx2, OBANK_FX_A, 448 + soft_sin(t * 8) / 2, 0);
        anim.tint_amount = t < 40 ? t / 4 : t < 52 ? (52 - t) * 10 / 12 : 0;
        anim.bg_amount = t < 54 ? tint_amt / 2 : 0;
        self_pulse_when(36);
        break;
    }
    case AK_TOLL: {
        /* a bell comes down over the foe and swings; every toll sends a ripple */
        int by = dy - 36 - (t < 10 ? (10 - t) * 4 : 0);
        int sw = t >= 10 ? soft_sin((t - 10) * 8) / 3 : 0;
        if (t < anim.dur - 6) fx_spr_aff(dx + sw / 3, by, fx, OBANK_FX_A, 384, sw);
        for (int i = 0; i < n; i++) {
            int t0 = 18 + i * 16, pt = t - t0;
            if (t == t0) sfx_play(SFX_KNELL);
            if (pt >= 0 && pt < 18)
                big_spr(dx, by + 8 + pt, FXB_RING, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 96 + pt * 22, 64 + pt * 12);
            if (pt >= 0 && pt < 3) anim.bright = -4;
            impact_when(t0 + 2, i == n - 1 ? st : 0, dx, dy);
        }
        anim.bg_amount = t < anim.dur - 4 ? tint_amt : 0;
        anim.tint_amount = t > 18 ? 5 + ((t & 8) ? 3 : 0) : 0;
        break;
    }
    case AK_CHOIR: {
        /* spirits rise from the ground, sway and sing, then converge on the foe */
        int gy = side_gy(foe) - 6;
        anim.bg_color = RGB15(4, 3, 8);
        anim.bg_amount = t < 70 ? (t < 12 ? t : 12) : 0;
        for (int i = 0; i < n; i++) {
            int bx = dx - (n - 1) * 11 + i * 22;
            int pt = t - 4 - i * 3;
            if (pt < 0 || t >= 62) continue;
            int x, y;
            if (t < 50) {
                int rise = ease_out(pt < 16 ? pt : 16, 16) * 28 / 256;
                x = bx + soft_sin(pt * 6 + i * 40) / 10;
                y = gy - rise + soft_sin(pt * 10 + i * 60) / 16;
            } else {
                int k = ease_in(t - 50, 12);
                x = bx + (dx - bx) * k / 256;
                y = gy - 28 + (dy - gy + 28) * k / 256;
            }
            fx_spr(x, y, fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A);
            if (t > 20 && t < 50 && (t + i * 5) % 12 == 0)
                part_add(PK_FX, x + 6, y - 8, (i & 1) ? 4 : -4, -10, fx2, OBANK_FX_B, 16, 0);
        }
        impact_when(62, st, dx, dy);
        if (t >= 62 && t < 74) big_spr(dx, dy, FXB_GLOW, OBANK_FX_A, 128 + (t - 62) * 24, 128 + (t - 62) * 24);
        if (t >= 62 && t < 65) anim.bright = 6;
        anim.tint_amount = t >= 62 ? 10 : 0;
        break;
    }
    case AK_CHOMP: {
        /* a mimic's jaws open wide around the foe and snap shut */
        int sc = t < 8 ? 128 + t * 24 : 320;
        int gap = 4;
        for (int i = 0; i < n; i++) {
            int t0 = 8 + i * 14, bt = t - t0;
            if (bt >= 0 && bt < 14)
                gap = bt < 9 ? 4 + ease_out(bt, 9) * 20 / 256 : bt < 11 ? 24 - (bt - 9) * 12 : 0;
            if (impact_when(t0 + 11, i == n - 1 ? st : 0, dx, dy))
                for (int k = 0; k < 3; k++)
                    part_add(PK_SPARK, dx + (k - 1) * 8, dy, (k - 1) * 12, -36 - k * 6, fx, OBANK_FX_B, 22, 4);
        }
        if (t >= 8 + n * 14) gap = 0;
        if (t < anim.dur - 8 || (t & 1)) {
            big_spr(dx, dy - 10 - gap, FXB_CHEST, OBANK_FX_A, sc, sc);
            big_spr(dx, dy + 10 + gap, FXB_CHEST, OBANK_FX_A, sc, -sc);
        }
        if (gap == 0 && t >= 19) anim.mon_dx[foe] = (t & 2) ? 1 : -1;
        break;
    }
    case AK_WHIRL: {
        /* things whirl round the foe in a rising tornado, then close in */
        int pair = fx == FX_FLAME_A;
        for (int i = 0; i < n; i++) {
            int pt = t - i * 2;
            if (pt < 0 || pt >= 56) continue;
            int a = pt * 12 + i * 256 / n;
            int r0 = 14 + (i % 3) * 5;
            int r = pt < 40 ? r0 + pt / 4 : (r0 + 10) * (56 - pt) / 16;
            int h = (i * 37 + pt * 2) % 48;
            int x = dx + soft_sin(a + 64) * r / 64;
            int y = side_gy(foe) - 8 - h + soft_sin(a) * r / 256;
            int f = pair ? fx_frame(fx, fx2, pt + i) : (i & 1) ? fx2 : fx;
            fx_spr_aff(x, y, f, (i & 1) ? OBANK_FX_B : OBANK_FX_A, soft_sin(a) < 0 ? 200 : 256, pair ? 0 : pt * 16);
        }
        if (!pair && t > 6 && t < 50)
            for (int k = 0; k < 2; k++)
                fx_spr_flip(dx + soft_sin(t * 12 + k * 128 + 64) * 22 / 64, side_gy(foe) - 14 - k * 20, FX_WIND,
                            OBANK_FX_A, k ? ATTR1_HFLIP : 0);
        if (t > 10 && t < 56) anim.mon_dx[foe] = soft_sin(t * 16) / 20;
        impact_when(24, 0, dx, dy);
        impact_when(52, st, dx, dy);
        anim.bg_amount = t < 58 ? tint_amt : 0;
        if (pair && t > 8 && t < 56) anim.wobble = 2;
        break;
    }
    case AK_MAGNET: {
        /* a horseshoe magnet hauls the foe; iron flakes fly to it */
        int mx = sx + dir * 22, my = sy - 18;
        int in = t < 8 ? ease_out(t, 8) : t > 52 ? 256 - (t - 52) * 32 : 256;
        if (in > 0)
            fx_spr_aff(mx, my + ((t >> 3) & 1), fx, ((t & 4) && t > 12) ? OBANK_FX_B : OBANK_FX_A, 128 + in / 2,
                       dir > 0 ? 192 : 64);
        for (int k = 0; k < n; k++) {
            if (t < 10 || t > 50) break;
            int pt = (t + k * 8) % 24;
            fx_spr_aff2(dx + (mx - dx) * pt / 24, dy + (my - dy) * pt / 24, FX_RING, OBANK_FX_B,
                        96 + (24 - pt) * 8, 192 + (24 - pt) * 10, 0);
        }
        for (int i = 0; i < 6; i++) {
            int pt = t - 12 - i * 5;
            if (pt < 0 || pt >= 20) continue;
            int ox = ((i * 23) % 30) - 15, oy = ((i * 13) % 24) - 12;
            int k = ease_in(pt, 20);
            fx_spr_aff(dx + ox + (mx - dx - ox) * k / 256, dy + oy + (my - dy - oy) * k / 256, fx2, OBANK_FX_B,
                       256, pt * 20);
        }
        int pull = t < 14 ? 0 : t < 46 ? 8 * ease_out(t - 14, 10) / 256 : 8 - 8 * ease_out(t - 46, 10) / 256;
        anim.mon_dx[foe] = -dir * pull;
        anim.scale_x[foe] = 256 + pull * 3;
        impact_when(30, 0, dx, dy);
        anim.tint_amount = t > 14 && t < 50 ? 6 : 0;
        break;
    }
    case AK_GEARS: {
        /* two big gears close in from both sides and grind */
        int off = t < 12 ? 56 - 40 * ease_out(t, 12) / 256 : t < 44 ? 16 : 16 + (t - 44) * 4;
        if (t < 52) {
            fx_spr_aff(dx - off, dy, fx, OBANK_FX_A, 384, t * 12);
            fx_spr_aff(dx + off, dy, fx, OBANK_FX_B, 384, -t * 12 + 16);
        }
        if (t >= 12 && t < 44) {
            anim.mon_dy[foe] = (t & 2) ? 1 : -1;
            anim.scale_x[foe] = 236;
            shake(12, 0);
            if ((t % 3) == 0)
                part_add(PK_SPARK, dx + ((t & 4) ? 8 : -8), dy - 4, ((t & 4) ? 1 : -1) * (10 + fx_rand(10)),
                         -28 - fx_rand(12), fx2, OBANK_FX_B, 12, 4);
        }
        for (int i = 0; i < n; i++) impact_when(14 + i * 14, i == n - 1 ? st : 0, dx, dy);
        break;
    }
    case AK_ANVIL: {
        /* a shadow grows under the foe, then an anvil drops: squash, dust, stars */
        int gy = side_gy(foe);
        if (t < 26) fx_spr_aff2(dx, gy - 4, FX_RING, OBANK_FX_A, 96 + t * 10, 32 + t * 3, 0);
        int ay = t < 14 ? -40 : t < 26 ? -40 + (dy - 12 + 40) * ease_in(t - 14, 12) / 256 :
                 dy - 12 - (t < 30 ? (30 - t) / 2 : 0);
        if (t >= 14 && (t < 44 || (t < 52 && (t & 1)))) big_spr(dx, ay, FXB_ANVIL, OBANK_FX_A, 288, 288);
        if (t >= 16 && t < 26)
            for (int k = -1; k <= 1; k += 2) fx_spr_aff(dx + k * 14, ay - 22, FX_SPEEDLINE, OBANK_FX_B, 256, 64);
        if (impact_when(26, st + 1, dx, dy)) {
            shake(96, 1);
            for (int k = 0; k < 8; k++)
                part_add(PK_FX, dx, gy - 4, soft_sin(k * 32 + 64) * 3 / 2, soft_sin(k * 32) / 3, fx, OBANK_FX_A, 16, 0);
        }
        if (t >= 26 && t < 44) {
            anim.scale_x[foe] = 256 + 48 * (44 - t) / 18;
            anim.scale_y[foe] = 256 - 64 * (44 - t) / 18;
            anim.mon_dy[foe] = 8 * (44 - t) / 18;
        }
        if (t >= 32 && t < 62)
            for (int k = 0; k < 3; k++) {
                int a = t * 10 + k * 85;
                fx_spr(dx + tri_sin(a) / 3, dy - 24 + tri_sin(a + 64) / 10, fx2, OBANK_FX_B);
            }
        break;
    }
    case AK_MOONLIT: {
        /* night falls, the moon rises, a pale shaft falls on the foe, then drains */
        anim.bg_color = RGB15(2, 3, 10);
        anim.bg_amount = t < 64 ? (t < 12 ? t : 12) : 0;
        int mx = dx - 52, my = t < 20 ? 40 - ease_out(t, 20) * 26 / 256 : 14;
        if (t < 66) {
            fx_spr_aff(mx, my, fx, OBANK_FX_A, 384, 0);
            if (t > 18 && (t & 8)) fx_spr_aff(mx, my, FX_RING, OBANK_FX_B, 512, 0);
        }
        if (t >= 20 && t < 48) {
            int h = ease_in(t - 20, 8) * (dy + 16) / 256;
            for (int y = 0; y < h; y += 16)
                fx_spr_aff2(dx, y, fx2, (y & 16) ? OBANK_FX_B : OBANK_FX_A, 320 + ((t & 2) ? 32 : 0), 256, 0);
            anim.tint_amount = 9;
        }
        impact_when(26, st, dx, dy);
        for (int i = 0; i < n; i++) {
            int pt = t - 40 - i * 4;
            if (pt < 0 || pt >= 20) continue;
            int x = dx + (sx - dx) * ease_in(pt, 20) / 256;
            int y = dy + (sy - dy) * pt / 20 - soft_sin(pt * 6) * (i - n / 2) / 4;
            fx_spr(x, y, FX_SPARKLE, OBANK_FX_B);
        }
        if (t == 40) sfx_play(SFX_DRAIN);
        if (t >= 56) {
            anim.tint_side = side;
            anim.tint_amount = 7;
        }
        break;
    }
    case AK_MUON: {
        /* thin streaks of light rain straight through everything */
        anim.bg_amount = t < 54 ? tint_amt : 0;
        for (int i = 0; i < n; i++) {
            int pt = t - 4 - (i * 11) % 36;
            if (pt < 0 || pt >= 14) continue;
            int x = 8 + (i * 53 + 17) % 224 + pt * 2;
            fx_spr(x, -16 + pt * 12, fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A);
            fx_spr(x - 2, -32 + pt * 12, fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A);
        }
        if (t > 16 && t < 48 && (t & 3) == 0)
            part_add(PK_FX, dx + fx_rand(44) - 22, dy + fx_rand(36) - 18, 0, 0, fx2, OBANK_FX_B, 8, 0);
        impact_when(20, 0, dx, dy);
        impact_when(36, st, dx, dy);
        anim.tint_amount = t > 16 && t < 48 && (t & 2) ? 10 : 0;
        break;
    }
    case AK_METEOR: {
        /* one huge meteor streaks in: flash, crater, debris */
        anim.bg_color = t < 24 ? RGB15(4, 2, 8) : TYPE_TINT[anim.type];
        anim.bg_amount = t < 22 ? t / 2 : t < 60 ? tint_amt : 0;
        if (t < 24) {
            int k = ease_in(t, 24);
            int x = dx + 96 - 96 * k / 256, y = -32 + (dy + 32) * k / 256;
            int sc = 256 + t * 12;
            fx_spr_aff(x, y, fx, OBANK_FX_A, sc > 512 ? 512 : sc, 0);
            if (t & 1) part_add(PK_FX, x + 8, y - 8, 6, -4, FX_SPARKLE, OBANK_FX_A, 10, 0);
            shake(t * 2, 1);
        }
        if (t >= 24 && t < 27) anim.bright = 12;
        if (impact_when(24, st + 1, dx, dy)) {
            shake(104, 1);
            for (int k = 0; k < 6; k++)
                part_add(PK_SPARK, dx, side_gy(foe) - 8, soft_sin(k * 43 + 64) * 20 / 16,
                         soft_sin(k * 21) * 10 / 16 - 40, fx2, OBANK_FX_B, 22, 4);
        }
        if (t >= 24 && t < 40) big_spr(dx, dy, FXB_GLOW, OBANK_FX_A, 128 + (t - 24) * 20, 128 + (t - 24) * 20);
        if (t >= 24 && t < 60 && (t < 52 || (t & 1)))
            fx_spr_aff2(dx, side_gy(foe) - 4, FX_CRACK, OBANK_FX_B, 448, 192, 0);
        anim.tint_amount = t >= 24 && t < 50 ? 8 : 0;
        break;
    }
    case AK_NOVA: {
        /* gathers starlight, the world goes dark, a blinding burst */
        int rel = 40;
        anim.bg_color = RGB15(1, 1, 4);
        if (t < rel) {
            if (t == 2) sfx_play(SFX_CHARGE);
            for (int i = 0; i < n; i++) {
                int pt = (t * 2 + i * 9) % 26;
                int a = i * 32 + t * 2;
                int r = 44 - pt * 44 / 26;
                fx_spr(sx + soft_sin(a + 64) * r / 64, sy + soft_sin(a) * r / 64, (i & 1) ? fx2 : fx,
                       (i & 1) ? OBANK_FX_B : OBANK_FX_A);
            }
            anim.tint_side = side;
            anim.tint_amount = t * 10 / rel;
            anim.bg_amount = t * 14 / rel;
            anim.scale_x[side] = anim.scale_y[side] = 256 + t / 2;
            anim.mon_dx[side] = t > 24 ? ((t & 1) ? 1 : -1) : 0;
        } else {
            int it = t - rel;
            anim.bg_amount = it < 36 ? 14 : 0;
            if (it < 6) {
                fx_spr_aff(sx + (dx - sx) * it / 6, sy + (dy - sy) * it / 6, fx, OBANK_FX_A, 384, it * 20);
            } else if (it < 36) {
                int g = it - 6;
                int gs = 128 + g * 16 > 512 ? 512 : 128 + g * 16;
                big_spr(dx, dy, FXB_GLOW, OBANK_FX_A, gs, gs);
                if (g < 20) big_spr(dx, dy, FXB_RING, OBANK_FX_B, 128 + g * 19, 96 + g * 14);
                for (int i = 0; i < n; i++) {
                    int a = i * 256 / n + g * 2;
                    fx_spr_aff(dx + soft_sin(a + 64) * g * 4 / 64, dy + soft_sin(a) * g * 3 / 64, fx,
                               (i & 1) ? OBANK_FX_B : OBANK_FX_A, 256, g * 12);
                }
            }
            anim.bright = it >= 6 && it < 14 ? 16 - (it - 6) * 2 : 0;
            if (it == 6) sfx_play(SFX_THUNDER);
            shake(it >= 6 && it < 20 ? 80 : 0, 0);
            impact_when(rel + 6, st + 1, dx, dy);
            anim.tint_side = foe;
            anim.tint_amount = it > 6 ? 10 : 0;
        }
        break;
    }
    case AK_ARC: {
        /* a jagged arc jumps from the user to the foe */
        anim.bg_color = RGB15(4, 4, 12);
        anim.bg_amount = t < 44 ? 6 : 0;
        if (t < 10 && (t & 1)) fx_spr(sx + tri_sin(t * 40) / 4, sy - 8 + tri_sin(t * 40 + 64) / 5, fx2, OBANK_FX_B);
        for (int k = 0; k < n; k++) {
            int t0 = 10 + k * 12, at = t - t0;
            if (at == 0 && k) sfx_play(SFX_ZAP);
            if (at >= 0 && at < 2) anim.bright = 8;
            impact_when(t0 + 1, k == n - 1 ? st : 0, dx, dy);
            if (at < 0 || at >= 10 || (at & 2)) continue;
            int segs = 8;
            for (int s = 0; s <= segs; s++) {
                int jag = (s == 0 || s == segs) ? 0 : ((s * 7 + k * 3 + at / 4) % 5 - 2) * 5;
                int x = sx + (dx - sx) * s / segs, y = sy + (dy - sy) * s / segs + jag;
                fx_spr(x, y, (s & 1) ? FX_SPARK_A : fx2, (s & 1) ? OBANK_FX_A : OBANK_FX_B);
            }
            fx_spr(dx, dy - 10, fx, OBANK_FX_A);
        }
        if (t >= 12 && t < 44) {
            anim.mon_dx[foe] = (t & 2) ? 1 : -1;
            anim.tint_amount = 8;
            if ((t + 1) & 2) fx_spr(dx + tri_sin(t * 22) / 3, dy + tri_sin(t * 22 + 64) / 4, fx2, OBANK_FX_A);
        }
        break;
    }
    case AK_DANCE: {
        /* the user sways and turns; scales spiral up around it */
        anim.tint_side = side;
        anim.mon_dx[side] = soft_sin(t * 8) / 8;
        anim.mon_dy[side] = -absi(soft_sin(t * 16)) / 16;
        if (t >= 16 && t < 40) {
            int c = soft_sin((t - 16) * 256 / 24 + 64) * 4;
            if (c > -48 && c < 48) c = c < 0 ? -48 : 48;
            anim.scale_x[side] = c;
        }
        for (int i = 0; i < n; i++) {
            int pt = (t + i * 8) % 40;
            if (t > 52 && pt < 12) continue;
            int a = pt * 14 + i * 256 / n;
            int r = 30 - pt / 2;
            fx_spr_aff(sx + soft_sin(a + 64) * r / 64, side_gy(side) - 4 - pt * 2 + soft_sin(a) * r / 200, fx,
                       (i & 1) ? OBANK_FX_B : OBANK_FX_A, 256, a);
        }
        if (t > 40 && (t & 4)) fx_spr(sx, sy - 26, fx2, OBANK_FX_B);
        anim.tint_amount = 5 + tri_sin(t * 8) / 16;
        self_pulse_when(44);
        break;
    }
    }
    (void)fx2;
}

/* A short version for players who turned animations off. */
static void anim_short_frame(void)
{
    int t = anim.t, side = anim.side, foe = !side;
    const Move *mv = &MOVES[anim.move];
    if (mv->cat == CAT_STATUS || (anim.flags & HITF_NODMG)) {
        int target = (mv->effect == EF_SELF_STAT || mv->effect == EF_HEAL) ? side : foe;
        anim.tint_side = target;
        anim.tint_amount = t < 8 ? t : 16 - t;
        if (t == 2) sfx_play(TYPE_SFX[mv->type]);
        return;
    }
    anim.mon_dx[side] = (side == SIDE_ALLY ? 1 : -1) * (t < 4 ? t * 2 : t < 8 ? 8 - (t - 4) * 2 : 0);
    impact_when(3, move_strength(), side_cx(foe), side_cy(foe));
}

static void anim_miss_frame(void)
{
    int t = anim.t, side = anim.side, foe = !side;
    int dir = side == SIDE_ALLY ? 1 : -1;
    anim.mon_dx[side] = dir * (t < 8 ? t * 3 : t < 16 ? 24 - (t - 8) * 3 : 0);
    /* the target sidesteps and hops back */
    anim.mon_dx[foe] = dir * (t < 6 ? t * 3 : t < 20 ? 18 : 18 - (t - 20) * 2);
    anim.mon_dy[foe] = t >= 6 && t < 20 ? -soft_sin((t - 6) * 128 / 14) / 10 : 0;
    if (t >= 6 && t < 14 && (t & 1)) fx_spr(side_cx(foe) - dir * 12, side_cy(foe), FX_SPEEDLINE, OBANK_FX_B);
}

static void anim_stat_frame(void)
{
    int t = anim.t, side = anim.side;
    int cx = side_cx(side), cy = side_cy(side);
    for (int i = 0; i < 5; i++) {
        int pt = (t + i * 7) % 20;
        int x = cx - 24 + i * 12;
        int y = anim.variant ? cy + 16 - pt * 2 : cy - 20 + pt * 2;
        fx_spr(x, y, anim.variant ? FX_ARROW_UP : FX_ARROW_DOWN, OBANK_FX_A);
    }
    anim.tint_amount = 7 + tri_sin(t * 12) / 16;
    if (anim.variant) anim.scale_y[side] = 256 + (t < 10 ? t * 2 : t < 20 ? 20 - (t - 10) * 2 : 0);
    else anim.scale_y[side] = 256 - (t < 10 ? t * 2 : t < 20 ? 20 - (t - 10) * 2 : 0);
}

static void anim_status_frame(void)
{
    int t = anim.t, side = anim.side;
    int cx = side_cx(side), cy = side_cy(side);
    int st = anim.variant;
    for (int i = 0; i < 3; i++) {
        int a = t * 8 + i * 85;
        int f = anim.fx;
        if (f == FX_FLAME_A && (t & 4)) f = FX_FLAME_B;
        if (f == FX_SPARK_A && (t & 4)) f = FX_SPARK_B;
        int y = cy - 6 + tri_sin(a + 64) / 6;
        if (st == STATUS_SLP) y = cy - 16 - ((t + i * 10) % 30) / 2;
        fx_spr(cx + tri_sin(a) / 3, y, f, OBANK_FX_A);
    }
    anim.tint_amount = (t & 8) ? 9 : 4;
    if (st == STATUS_NUMB) anim.mon_dx[side] = (t & 2) ? 1 : -1;
    if (st == STATUS_FRZ) anim.scale_x[side] = 262;
    if (st == STATUS_SLP) anim.scale_y[side] = 256 - (t < 12 ? t : 12);
    if (st == STATUS_PSN) anim.scale_y[side] = 256 + soft_sin(t * 16) / 10;
}

static void anim_trait_frame(void)
{
    int t = anim.t, side = anim.side;
    anim.tint_amount = t < 8 ? t * 2 : 16 - t / 2 > 0 ? 16 - t / 2 : 0;
    if (anim.tint_amount > 12) anim.tint_amount = 12;
    if (t < 20 && opt.battle_anims)
        big_spr(side_cx(side), side_cy(side), FXB_RING, OBANK_FX_A, 128 + t * 12, 96 + t * 8);
}

static void anim_react_frame(void)
{
    int foe = !anim.side;
    if (anim.t == 0 && anim.last_impact != 0) {
        anim.last_impact = 0;
        anim_impact_at(foe, 0, side_cx(foe), side_cy(foe));
    }
}

static void anim_legend_frame(void)
{
    int t = anim.t, side = anim.side;
    int sx = side_cx(side), sy = side_cy(side);
    if (!opt.battle_anims) {
        anim.bg_color = TYPE_TINT[anim.type];
        anim.bg_amount = t < 16 ? 10 : 0;
        return;
    }
    if (t < 12) {
        anim.scale_x[side] = 256 - t * 3;
        anim.scale_y[side] = 256 + t * 5;
        anim.mon_dy[side] = -t / 2;
    } else if (t < 52) {
        anim.scale_x[side] = 286 + ((t & 2) ? 6 : 0);
        anim.scale_y[side] = 236;
        anim.mon_dy[side] = -6;
        shake(72, t & 8);
    }
    for (int i = 0; i < 4; i++) {
        int pt = t - 12 - i * 9;
        if (pt < 0 || pt >= 26) continue;
        int sc = 96 + ease_out(pt, 26) * 440 / 256;
        if (sc > 512) sc = 512;
        if (pt < 22 || (pt & 1)) big_spr(sx, sy - 8, FXB_RING, (i & 1) ? OBANK_FX_B : OBANK_FX_A, sc, sc * 3 / 4);
    }
    anim.bg_color = TYPE_TINT[anim.type];
    anim.bg_amount = (t > 10 && t < 20) ? 16 : (t >= 20 && t < 56) ? 8 : 0;
    anim.tint_side = side;
    anim.tint_amount = (t > 12 && t < 18) ? 12 : 0;
}

/* ---------------- per-frame update ---------------- */

static void feel_update(void)
{
    for (int s = 0; s < 2; s++) {
        if (feel.flash[s] > 0) feel.flash[s]--;
        /* squash & stretch spring back toward 256 */
        feel.vx[s] += (256 - feel.sx[s]) / 4;
        feel.vy[s] += (256 - feel.sy[s]) / 4;
        feel.vx[s] = feel.vx[s] * 3 / 4;
        feel.vy[s] = feel.vy[s] * 3 / 4;
        feel.sx[s] += feel.vx[s];
        feel.sy[s] += feel.vy[s];
        if (absi(feel.sx[s] - 256) < 2 && absi(feel.vx[s]) < 2) feel.sx[s] = 256, feel.vx[s] = 0;
        if (absi(feel.sy[s] - 256) < 2 && absi(feel.vy[s]) < 2) feel.sy[s] = 256, feel.vy[s] = 0;
        feel.kb[s] = feel.kb[s] * 3 / 4;
    }
    if (feel.bright > 0) feel.bright--;
    feel.shake = feel.shake * 13 / 16;
    if (feel.shake < 4) feel.shake = 0;
}

static void parts_update(int frozen)
{
    for (int i = 0; i < PART_MAX; i++) {
        Particle *p = &parts[i];
        if (!p->life) continue;
        int x = p->x / 16, y = p->y / 16, age = p->max - p->life;
        switch (p->kind) {
        case PK_BIG_GROW:
            big_spr(x, y, p->fx, p->bank, 96 + age * 26, 96 + age * 26);
            break;
        case PK_RING_GROW:
            fx_spr_aff(x, y, FX_RING, p->bank, 128 + age * 24, 0);
            break;
        default:
            if (p->life > 3 || (p->life & 1)) fx_spr(x, y, p->fx, p->bank);
            break;
        }
        if (frozen) continue;
        p->x = (s16)(p->x + p->vx);
        p->y = (s16)(p->y + p->vy);
        p->vy = (s16)(p->vy + p->grav);
        p->life--;
    }
}

/* Advance one frame and push particle sprites. Returns 0 when finished. */
static int anim_update(void)
{
    int frozen = feel.hitstop > 0;
    if (!anim_nodraw) anim_frame++;
    /* this frame's shake offset */
    int amp = feel.shake / 16;
    if (anim_nodraw) {
        /* not shown: keep the offset of the last drawn frame */
    } else if (amp) {
        int s = (anim_frame & 1) ? amp : -amp;
        if (feel.shake_v) {
            shake_y = s;
            shake_x = (anim_frame & 2) ? amp / 3 : -amp / 3;
        } else {
            shake_x = s;
            shake_y = (anim_frame & 2) ? amp / 3 : -amp / 3;
        }
    } else {
        shake_x = shake_y = 0;
    }
    parts_update(frozen);
    if (!frozen) feel_update();
    else feel.hitstop--;
    if (!anim.active) {
        anim_reset_offsets();
        return 0;
    }
    anim_reset_offsets();
    switch (anim.mode) {
    case ANIM_MOVE: anim_move_frame(); break;
    case ANIM_SHORT: anim_short_frame(); break;
    case ANIM_MISS: anim_miss_frame(); break;
    case ANIM_STAT: anim_stat_frame(); break;
    case ANIM_STATUS: anim_status_frame(); break;
    case ANIM_TRAIT: anim_trait_frame(); break;
    case ANIM_REACT: anim_react_frame(); break;
    case ANIM_LEGEND: anim_legend_frame(); break;
    }
    if (frozen) return 1;
    anim.t++;
    if (anim.t >= anim.dur) {
        anim.active = 0;
        return 0;
    }
    return 1;
}

/* Everything settled (for events that wait on the animation). */
static int anim_busy(void)
{
    return anim.active || feel.hitstop > 0;
}

static void anim_clear(void)
{
    anim.active = 0;
    anim_reset_offsets();
    parts_clear();
    for (int s = 0; s < 2; s++) {
        feel.flash[s] = 0;
        feel.sx[s] = feel.sy[s] = 256;
        feel.vx[s] = feel.vy[s] = 0;
        feel.kb[s] = 0;
    }
    feel.hitstop = 0;
    feel.shake = 0;
    feel.bright = 0;
    feel.bg_amount = 0;
    shake_x = shake_y = 0;
}
