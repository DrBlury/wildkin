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
 *
 * The scene is pseudo-3D (anim3d.c): moves place particles in a world
 * space seen by a camera behind the ally, so projectiles grow or shrink
 * with their depth and cast shadows, orbits pass behind the battler they
 * circle (dimmer), rings and vortices lie flat on the ground (affine
 * rotate + squash), debris tumbles with gravity and bounces, and big
 * blows punch the camera in. Impacts add a 3D spark burst.
 *
 * With opt.battle_anims off only a short version plays: the hit flash and
 * shake (or a tint pulse for status moves).
 *
 * OBJ VRAM and palettes while a bout is on screen (tiles are 4bpp 8x8):
 *   256..383   the two battlers (64x64 each)            banks 10, 11
 *   384..399   the thrown lantern (4 frames of 16x16)   bank 9
 *   400..      FX_COUNT 16x16 particles (4 tiles each), then FXB_COUNT
 *              32x32 ones (16 tiles each), then the 2 lantern marks:
 *              OT_FX .. OT_FX_END - 1 (400..857 with 86 small and 7 big
 *              particles; the 10 small + 3 big pseudo-3D ones of
 *              tools/bout_fx3d.py are included in that range)
 *   OT_FX_END..1023  free for other battle art (166 tiles), e.g. the runes
 *   banks 12 / 13  particles in the move's colours (A: main ramp, B: the
 *                  secondary one), 14 hits and sparks (warm white),
 *                  8 (OBANK_FX_C) the dimmed "far side" of FX_A plus the
 *                  shadow colour (index 1), 15 lantern light (shared).
 *   banks 0..7 are not touched by the animations (free during a bout).
 * Affine matrices: the animations take at most A3_AFF_CAP (24) of the 32 per
 * frame (anim3d.c shares them between equal transforms); the battlers and
 * the HUD sparkles use the rest.
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
#define OT_FX_END      (OT_LANTERN_MINI + 2)  /* first OBJ tile the animations leave alone */
#define OBANK_FX_C     8    /* the far side of FX_A (dimmed) and the shadow colour */

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
    int zoom;                 /* camera punch-in (8.8 above 256), decays */
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

/* cos(a) kept at least `min` away from 0 (sign kept): the x scale of
 * something tumbling over (negative = its back side, mirrored). */
static int tumble(int a, int min)
{
    int c = a3_cos(a);
    if (c >= 0 && c < min) return min;
    if (c < 0 && c > -min) return -min;
    return c;
}

static int atleast(int v, int m) { return v < m ? m : v; }

/* Presentation-only randomness, so animations never shift the rules' RNG. */
static u32 fx_rng_state = 0x2468ACEu;

static int fx_rand(int n)
{
    fx_rng_state = fx_rng_state * 1103515245u + 12345u;
    return n > 0 ? (int)(((fx_rng_state >> 16) * (u32)n) >> 16) : 0;   /* no division */
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

/*
 * World-space particles (anim3d.c): debris, sparks, spray and dust that fly
 * in 3D with gravity, bounce on the ground, tumble and are sorted against
 * the battlers (behind the one they are further away than).
 */
enum {
    P3_BOUNCE = 1,    /* bounces off the ground (y = 0) */
    P3_SHADOW = 2,    /* casts a shadow on the ground */
    P3_TUMBLE = 4,    /* flips over while it spins (x scale = cos) */
    P3_SHRINK = 8,    /* shrinks away over its last frames */
    P3_FLAT = 16,     /* lies flat on the ground (dust rings, ripples) */
    P3_BIG = 32,      /* fx is an FXB_* 32x32 particle */
};

typedef struct {
    s16 x, y, z, vx, vy, vz;  /* 1/16 world units */
    u8 fx, bank, life, max, rot, flags;
    s8 vrot, grav;
} P3;

#define P3_MAX 28
EWRAM_BSS static P3 p3s[P3_MAX];   /* (IWRAM is kept for the stack) */

static int anim_frozen;         /* 1 while a hit-stop holds the animation frame */

static void p3_add(int x, int y, int z, int vx, int vy, int vz, int fx, int bank, int life, int grav, int vrot,
                   int flags)
{
    if (anim_frozen) return;   /* a held frame is drawn again: do not emit twice */
    for (int i = 0; i < P3_MAX; i++) {
        if (p3s[i].life) continue;
        P3 *p = &p3s[i];
        p->x = (s16)(x * 16);
        p->y = (s16)(y * 16);
        p->z = (s16)(z * 16);
        p->vx = (s16)vx;
        p->vy = (s16)vy;
        p->vz = (s16)vz;
        p->fx = (u8)fx;
        p->bank = (u8)bank;
        p->life = p->max = (u8)life;
        p->grav = (s8)grav;
        p->vrot = (s8)vrot;
        p->rot = (u8)fx_rand(256);
        p->flags = (u8)flags;
        return;
    }
}

static void parts_clear(void)
{
    for (int i = 0; i < PART_MAX; i++) parts[i].life = 0;
    for (int i = 0; i < P3_MAX; i++) p3s[i].life = 0;
}

/* ---------------- sprite helpers ---------------- */

static int shake_x, shake_y;  /* this frame's screen shake (px) */
static unsigned anim_frame;   /* frames drawn (drives shake and breathing) */
/* 1 while anim_update() runs a step that is not shown (opt.battle_speed
 * steps twice per frame): the state advances but no sprite is pushed. */
static int anim_nodraw;

/*
 * The one place particles reach OAM: a 16x16 particle centred on screen
 * point (x, y), scaled sx, sy (8.8; negative mirrors) and turned `rot`.
 * Near-plain transforms use a plain sprite (flips for mirroring); the rest
 * take a shared matrix from anim3d.c. Goes to the back layer when open.
 */
static int fx_coarse;            /* 1: round transforms harder (more sprites share a matrix) */

static void fx_draw(int x, int y, int fx, int bank, int sx, int sy, int rot, int flags)
{
    if (anim_nodraw) return;
    x += shake_x - 8;
    y += shake_y - 8;
    int tile = OT_FX + fx * 4;
    int ax = sx < 0 ? -sx : sx, ay = sy < 0 ? -sy : sy;
    rot = (rot + (fx_coarse ? 8 : 4)) & (fx_coarse ? 0xF0 : 0xF8);    /* the steps a3_matrix keeps */
    if (!rot && ax > 240 && ax < 272 && ay > 240 && ay < 272) {
        if (sx < 0) flags ^= ATTR1_HFLIP;
        if (sy < 0) flags ^= ATTR1_VFLIP;
        a3_push(x, y, tile, SQ16, bank, flags, -1, 0);
        return;
    }
    if (fx_coarse) {
        sx = (sx + 16) & ~31;
        sy = (sy + 16) & ~31;
    }
    int big = ax > 256 || ay > 256 || (rot && (ax > 224 || ay > 224));
    a3_push(x, y, tile, SQ16, bank, flags, a3_affine(sx, sy, rot), big);
}

/* Screen-space particles (the camera is applied by the depth of the line). */
static void fx_cam(int *x, int *y) { a3_cam_apply(x, y, a3_line_scale(*y)); }

static void fx_spr(int x, int y, int fx, int bank)
{
    fx_cam(&x, &y);
    fx_draw(x, y, fx, bank, 256, 256, 0, 0);
}

static void fx_spr_flip(int x, int y, int fx, int bank, int flags)
{
    fx_cam(&x, &y);
    fx_draw(x, y, fx, bank, 256, 256, 0, flags);
}

/* Particle with scale (8.8) and rotation (0..255). */
static void fx_spr_aff(int x, int y, int fx, int bank, int scale, int rot)
{
    fx_cam(&x, &y);
    fx_draw(x, y, fx, bank, scale, scale, rot, 0);
}

static void fx_spr_aff2(int x, int y, int fx, int bank, int sx, int sy, int rot)
{
    fx_cam(&x, &y);
    fx_draw(x, y, fx, bank, sx, sy, rot, 0);
}

/* 32x32 particle (FXB_*) scaled; up to 2x fits the double-size box. flat:
 * turned in its own plane, then squashed (lying on the ground). */
static void big_draw(int x, int y, int fxb, int bank, int sx, int sy, int rot, int flat, int flags)
{
    if (anim_nodraw) return;
    int aff = flat ? a3_affine_flat(sx, sy, rot) : a3_affine(sx, sy, rot);
    a3_push(x - 16 + shake_x, y - 16 + shake_y, OT_FX_BIG + fxb * 16, SQ32, bank, flags, aff, 1);
}

static void big_spr(int x, int y, int fxb, int bank, int sx, int sy)
{
    fx_cam(&x, &y);
    big_draw(x, y, fxb, bank, sx, sy, 0, 0, 0);
}

/* A flat particle: turned in its own plane, then squashed (a wheel or
 * disc seen at an angle). */
static void fx_flat(int x, int y, int fx, int bank, int sx, int sy, int rot)
{
    if (anim_nodraw) return;
    int big = absi(sx) > 224 || absi(sy) > 224;
    a3_push(x + shake_x - 8, y + shake_y - 8, OT_FX + fx * 4, SQ16, bank, 0, a3_affine_flat(sx, sy, rot), big);
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

/* ---------------- 3D drawing (world space, see anim3d.c) ---------------- */

/* The far bank of a bank: particles behind a battler are drawn dimmer. */
static int bank_far(int bank) { return bank == OBANK_FX_A || bank == OBANK_FX_B ? OBANK_FX_C : bank; }

/* Draw FX `fx` at world point (x, y, z). mul scales the perspective size,
 * msx / msy (8.8) squash or mirror it (tumbling), rot turns it. ref: the
 * battler it is sorted against (-1: always in front). */
static void fx3t(int x, int y, int z, int fx, int bank, int msx, int msy, int rot, int ref)
{
    if (anim_nodraw) return;
    int px, py, s = w3_proj(x, y, z, &px, &py);
    int sc = w3_spr_scale(s);
    int back = ref >= 0 && z > w3_side_z(ref) + 3;
    if (sc > 500) sc = 500;                          /* the double-size box holds 2x */
    if (back) a3_back_begin();
    int was = fx_coarse;
    fx_coarse = 1;                                   /* world particles share matrices more */
    fx_draw(px, py, fx, back ? bank_far(bank) : bank, (sc * msx) >> 8, (sc * msy) >> 8, rot, 0);
    fx_coarse = was;
    if (back) a3_back_end();
}

static void fx3(int x, int y, int z, int fx, int bank, int mul, int rot, int ref)
{
    fx3t(x, y, z, fx, bank, mul, mul, rot, ref);
}

/* Around a battler: (lx, ly, lz) from the spot it stands on. */
static void fx3_at(int side, int lx, int ly, int lz, int fx, int bank, int mul, int rot)
{
    fx3(w3_side_x(side) + lx, ly, w3_side_z(side) + lz, fx, bank, mul, rot, side);
}

/* A 32x32 particle at a world point, facing the camera. */
static void big3(int x, int y, int z, int fxb, int bank, int mul, int rot, int ref)
{
    if (anim_nodraw) return;
    int px, py, s = w3_proj(x, y, z, &px, &py);
    int sc = (w3_spr_scale(s) * mul) >> 8;
    int back = ref >= 0 && z > w3_side_z(ref) + 3;
    if (back) a3_back_begin();
    big_draw(px, py, fxb, back ? bank_far(bank) : bank, sc, sc, rot, 0, 0);
    if (back) a3_back_end();
}

/*
 * A ring lying on the ground (or at height y) centred on world (x, z),
 * radius r world units, turned `spin` in its own plane: an FXB_* image
 * (its ring drawn 13 px from the centre) up to 26 px on screen (the
 * double-size box); use bead_ring3 for wider ones. back: draw it behind the
 * battlers (a ring under a battler's feet shows round them).
 */
static void ring3(int x, int y, int z, int r, int fxb, int bank, int spin, int back)
{
    if (anim_nodraw || r <= 0) return;
    int px, py, s = w3_proj(x, y, z, &px, &py);
    int rs = (r * s) >> 8;                           /* screen radius */
    int sq = w3_ground_squash(z);
    if (back) a3_back_begin();
    int k = atleast((rs > 26 ? 26 : rs) * 256 / 13, 16);
    big_draw(px, py, fxb, bank, k, atleast((k * sq) >> 8, 8), spin, 1, 0);
    if (back) a3_back_end();
}

/* A ring of `n` beads on the ground (for rings too big for one sprite):
 * the far half behind the battler `ref`, the near half in front. */
static void bead_ring3(int x, int y, int z, int r, int n, int phase, int fx, int bank, int mul, int ref)
{
    for (int i = 0; i < n; i++) {
        int a = phase + i * 256 / n;
        fx3(x + ((a3_cos(a) * r) >> 8), y, z + ((a3_sin(a) * r) >> 8), fx, bank, mul, a, ref);
    }
}

/* A soft shadow on the ground under something at height h (world units). */
static void shadow3(int x, int z, int size, int h)
{
    if (anim_nodraw) return;
    int px, py, s = w3_proj(x, 0, z, &px, &py);
    int k = (size * s) >> 8;
    k = (k * (256 - (h > 160 ? 160 : h))) >> 8;      /* smaller the higher it is */
    if (k < 24) return;
    k = (k + 16) & ~31;                              /* few sizes: they share matrices */
    a3_back_begin();
    fx_draw(px, py, FX_SHADOW, OBANK_FX_C, k, (k * w3_ground_squash(z)) >> 8, 0, ATTR0_BLEND);
    a3_back_end();
}

/* An orbit round a battler: n particles on a circle of radius r at height
 * ly, turned by `phase`; `tilt` (x/256) lifts the far side of the circle
 * (0 = level). Sorted against the battler and dimmer behind it; spin != 0
 * also turns each particle along the orbit. */
static void orbit3(int side, int ly, int r, int tilt, int phase, int n, int fx, int fx_b, int mul, int spin)
{
    int cx = w3_side_x(side), cz = w3_side_z(side);
    for (int i = 0; i < n; i++) {
        int a = phase + i * 256 / n;
        int c = a3_cos(a), sn = a3_sin(a);
        int x = cx + ((c * r) >> 8), z = cz + ((sn * r) >> 8);
        int y = ly + ((sn * r >> 8) * tilt >> 8);
        fx3(x, y, z, (i & 1) ? fx_b : fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A, mul, spin ? a + spin : 0, side);
    }
}

/* A helix: n particles rising round a vertical axis at (x, z) from height
 * y0 to y1, radius r (shrinking by `taper` per 256 of height), `turns` x256. */
static void helix3(int side, int x, int z, int y0, int y1, int r, int taper, int turns, int phase, int n,
                   int fx, int fx_b, int mul)
{
    for (int i = 0; i < n; i++) {
        int k = i * 256 / (n > 1 ? n - 1 : 1);
        int a = phase + ((turns * k) >> 8);
        int rr = r - ((taper * k) >> 8);
        if (rr < 0) rr = 0;
        int y = y0 + (((y1 - y0) * k) >> 8);
        fx3(x + ((a3_cos(a) * rr) >> 8), y, z + ((a3_sin(a) * rr) >> 8), (i & 1) ? fx_b : fx,
            (i & 1) ? OBANK_FX_B : OBANK_FX_A, mul, a, side);
    }
}

/* Sparks / debris bursting from a battler-relative point in 3D. */
static void burst3(int side, int lx, int ly, int lz, int n, int speed, int up, int fx, int bank, int life,
                   int grav, int flags)
{
    int x = w3_side_x(side) + lx, z = w3_side_z(side) + lz;
    for (int i = 0; i < n; i++) {
        int a = i * 256 / n + fx_rand(24);
        int e = fx_rand(128) - 64;                   /* elevation */
        int ce = a3_cos(e);
        int v = speed * (192 + fx_rand(128)) >> 8;
        p3_add(x, ly, z, (a3_cos(a) * ce >> 8) * v >> 8, ((a3_sin(e) * v) >> 8) + up,
               (a3_sin(a) * ce >> 8) * v >> 8, fx, bank, life + fx_rand(life / 3 + 1), grav,
               (fx_rand(2) ? 1 : -1) * (6 + fx_rand(10)), flags);
    }
}

/* Sparks flying out of a point of impact (screen point on a battler). */
static void spark_burst(int x, int y, int n, int speed, int fx, int bank)
{
    int side = x > 120 ? SIDE_ENEMY : SIDE_ALLY;
    int s = side == SIDE_ENEMY ? 179 : 256;
    int lx = (x - side_cx(side)) * 256 / s;
    int ly = w3_side_h(side) - (y - side_cy(side)) * 256 / s;
    burst3(side, lx, ly, -6, (n + 1) >> 1, speed, 12, fx, bank, 12, 3, P3_SHRINK);
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
        p3_add(w3_side_x(side_hit), 0, w3_side_z(side_hit), 0, 0, 0, FXB_WAVE, OBANK_FX_HIT, 12, 0, 0,
               P3_FLAT | P3_BIG);
    }
    if (s >= 3 && feel.zoom < s * 4) feel.zoom = s * 4;   /* the camera flinches in */
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
    a3_cam_x = a3_cam_y = 0;
    a3_cam_zoom = 256;
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
    case AK_VOLLEY: return 36 + count * 4;
    case AK_LOB: return 66;
    case AK_LANCE: return 30 + count * 6;
    case AK_BUBBLES: return 42 + count * 3 + 12;
    case AK_FIRESTORM: return 72;
    case AK_WHIRLPOOL: return 70;
    case AK_CRESCENT: return 36 + count * 4;
    case AK_SHIELD: return 58;
    case AK_GYRE: return 62;
    case AK_IMPLODE: return 66;
    case AK_SPRAY: return 54;
    case AK_BLIZZARD: return 64;
    case AK_SPIN: return 50;
    case AK_CYCLONE: return 60;
    case AK_PRISM: return 60;
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
    build_fx_palette(OBANK_FX_C, scale15(mv->col1, 62), scale15(mv->col2, 62));
    obj_palette[OBANK_FX_C * 16 + 1] = RGB15(2, 2, 5);   /* shadows */
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

/* Screen angle (0..255, 0 = right, 64 = down) of the vector (x, y). */
static int a3_atan2(int y, int x)
{
    if (!x && !y) return 0;
    int ax = absi(x), ay = absi(y);
    int r = ax >= ay ? (ay << 8) / ax : (ax << 8) / ay;        /* 0..256 */
    int a = (r * 32 + ((r * (256 - r) * 11) >> 8)) >> 8;     /* atan in 1/256 turns, one octant */
    if (ay > ax) a = 64 - a;
    if (x < 0) a = 128 - a;
    if (y < 0) a = -a;
    return a & 255;
}

/* A slash / blade streak: a sprite swept from P0 to P1 (battler-relative,
 * world units) over `len` frames, turned along the way, with two fading
 * ghosts behind it. mir mirrors it. */
static void sweep3(int side, int st, int len, const s8 *p, int fx, int mul, int rot0, int turn, int mir)
{
    for (int g = 2; g >= 0; g--) {
        int k = (st - g * 2) * 256 / len;
        if (k < 0 || k > 256) continue;
        k = 256 - (((256 - k) * (256 - k)) >> 8);                /* ease out */
        int lx = p[0] + (((p[3] - p[0]) * k) >> 8), ly = p[1] + (((p[4] - p[1]) * k) >> 8);
        int lz = p[2] + (((p[5] - p[2]) * k) >> 8);
        if (mir) lx = -lx;
        int m = g ? mul - g * 40 : mul;
        fx3t(w3_side_x(side) + lx, w3_side_h(side) + ly, w3_side_z(side) + lz, fx, g ? OBANK_FX_B : OBANK_FX_A,
             mir ? -(m * 5 / 4) : m * 5 / 4, m, mir ? -(rot0 + ((turn * k) >> 8)) : rot0 + ((turn * k) >> 8), -1);
    }
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
    /* the same two battlers in world space (anim3d.c) */
    int ax = w3_side_x(side), az = w3_side_z(side), ah = w3_side_h(side);
    int bx = w3_side_x(foe), bz = w3_side_z(foe), bh = w3_side_h(foe);
    int ux = bx - ax, uz = bz - az;                   /* attacker -> foe on the ground */
    anim.bg_color = TYPE_TINT[anim.type];

    switch (anim.kind) {
    case AK_CONTACT: {
        /* wind-up (dust kicked back), headlong lunge, hits, return */
        int reach = 40;
        int l = lunge(t, 8, 7, 4 + n * 6, 12, reach);
        anim.mon_dx[side] = dir * l;
        anim.mon_dy[side] = -dir * l / 3;
        if (t < 8) anim.scale_x[side] = 256 - t * 3, anim.scale_y[side] = 256 + t * 3;
        else if (t < 15) anim.scale_x[side] = 290, anim.scale_y[side] = 226;
        if (t >= 6 && t < 12 && (t & 1))
            p3_add(ax - dir * 10, 2, az - dir * 6, -ux / 6 + fx_rand(16) - 8, 6 + fx_rand(6), -uz / 6, FX_DUST,
                   OBANK_FX_B, 12, 1, 0, P3_SHRINK);
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
            if (t >= ht && t < ht + 8)
                fx_spr_aff(dx + jx, dy + jy, fx_is_hit(fx) ? fx : fx_frame(fx, fx2, t),
                           fx_is_hit(fx) ? OBANK_FX_HIT : OBANK_FX_A, 320 - (t - ht) * 12, (t - ht) * 10);
        }
        if (fx2 == FX_STAR && t >= 20) {  /* cartoon stars circling the foe's head, in front and behind */
            orbit3(foe, bh + 24, 18, 0, t * 9, 3, FX_STAR, FX_STAR, 200, 0);
        } else if (fx2 != fx && t >= 17 && t < 26) {
            fx_spr(dx - 8, dy - 8, fx_frame(fx2, fx, t), fx_is_hit(fx2) ? OBANK_FX_HIT : OBANK_FX_B);
        }
        break;
    }
    case AK_SLASH: {
        /* small lean-in, then blades sweep across the foe along a tilted arc,
         * turning as they go; a lingering cut and flying chips */
        static const s8 PATH[6] = { 22, 26, -18, -20, -10, -6 };
        anim.mon_dx[side] = dir * lunge(t, 6, 4, 6, 8, 10);
        if (fx2 == FX_WISP) {                  /* SHADE CUT: a cut out of the dark */
            anim.bg_color = RGB15(2, 1, 6);
            anim.bg_amount = t < 26 ? 10 : 0;
            if (t >= 12 && t < 26 && (t & 2)) fx_spr(dx - 12 + (t - 12) * 2, dy + 10 - (t - 12), FX_WISP, OBANK_FX_B);
        }
        int mul = anim.move == M_SCALE_REND ? 320 : 256;
        for (int i = 0; i < n; i++) {
            int s0 = 8 + i * 10, stt = t - s0;
            if (stt < 0 || stt >= 18) continue;
            int mir = i & 1;
            if (stt < 10) sweep3(foe, stt, 7, PATH, fx, mul, -16, 24, mir);
            else if (stt < 16 && (stt & 1))           /* the cut hangs in the air */
                fx3t(bx + (mir ? 4 : -4), bh, bz - 12, FX_SLASH, OBANK_FX_B, mir ? -300 : 300, 300, 0, -1);
            if (impact_when(s0 + 3, i == n - 1 ? st : 0, dx + (mir ? 6 : -6), dy))
                for (int k = 0; k < 2; k++)
                    p3_add(bx, bh, bz - 10, (mir ? -1 : 1) * (24 + k * 14), 20 + k * 10, -8, FX_CRESCENT, OBANK_FX_B,
                           14, 3, 20, P3_SHRINK);
            if ((fx2 == FX_FEATHER || fx2 == FX_LEAF_A) && stt == 6)
                for (int k = 0; k < 3; k++)
                    p3_add(bx + (k - 1) * 8, bh + 6, bz - 8, (k - 1) * 12, 8 + k * 4, fx_rand(16) - 8, fx2,
                           OBANK_FX_B, 30, 1, 8, P3_TUMBLE);
        }
        break;
    }
    case AK_PROJECTILE: {
        /* thrown along a 3D arc: grows or shrinks with its depth, casts a
         * shadow, spins or points along its flight */
        int travel = fx == FX_SHARD || fx == FX_NEEDLE ? 12 : fx == FX_GLOB ? 22 : 18;
        int gap = fx == FX_PEBBLE ? 3 : 5;
        int windup = 6;
        int arc = fx == FX_GLOB ? 90 : fx == FX_BUBBLE || fx == FX_WIND ? 0 : fx == FX_FIREBALL ? 40 :
                  fx == FX_PEBBLE ? 30 : 12;
        if (t < windup) {
            anim.mon_dx[side] = -dir * t / 2;
            anim.scale_y[side] = 256 + t * 4;
        } else if (t < windup + 6) {
            anim.mon_dx[side] = dir * 4;
        }
        for (int i = 0; i < n; i++) {
            int pt = t - windup - i * gap;
            if (pt < 0) continue;
            int jx = (i * 7) % 13 - 6, jy = (i * 5) % 11 - 5, jz = (i * 3) % 9 - 4;
            if (fx == FX_PEBBLE) jx *= 2, jy *= 2;
            if (pt < travel) {
                int k = pt * 256 / travel, x, y, z;
                w3_path(side, foe, k, arc, &x, &y, &z);
                x += (jx * k) >> 8;
                y -= (jy * k) >> 8;
                z += ((jz - 8) * k) >> 8;
                if (fx == FX_BUBBLE || fx == FX_WIND) y += a3_sin(pt * 24 + i * 60) >> 5;
                if (fx == FX_SPARKLE || fx == FX_MOTE) x += a3_sin(pt * 14) >> 5, y += a3_cos(pt * 14) >> 5;
                int f = fx_frame(fx, fx2, pt + i);
                if (fx == FX_LEAF_A) f = ((pt >> 2) & 1) ? FX_LEAF_B : FX_LEAF_A;
                int px0, py0, px1, py1, x2, y2, z2;
                w3_proj(x, y, z, &px0, &py0);
                w3_path(side, foe, k + 16, arc, &x2, &y2, &z2);
                w3_proj(x2, y2, z2, &px1, &py1);
                int head = a3_atan2(py1 - py0, px1 - px0);   /* screen heading */
                if (fx == FX_ORB) {
                    fx3(x, y, z, FX_ORB, OBANK_FX_A, 192 + pt * 10, 0, -1);
                } else if (fx == FX_BURR || fx == FX_PEBBLE || fx == FX_TRINKET || fx == FX_COIN) {
                    fx3(x, y, z, f, OBANK_FX_A, 256, pt * 24, -1);
                } else if (fx == FX_SHARD || fx == FX_NEEDLE || fx == FX_FIREBALL) {
                    fx3t(x, y, z, f, OBANK_FX_A, 256, fx == FX_FIREBALL ? 256 : tumble(pt * 40, 96), head, -1);
                } else {
                    fx3(x, y, z, f, OBANK_FX_A, 256, 0, -1);
                }
                if (arc >= 30) shadow3(x, z, 200, y);
                if (fx == FX_NEEDLE && fx2 == FX_TEAR && (pt & 2)) fx_spr(px0 - dir * 6, py0 + 6, FX_TEAR, OBANK_FX_B);
                if ((fx == FX_FIREBALL || fx == FX_RIVET || fx == FX_MOTE) && (pt & 1))
                    p3_add(x, y, z, 0, 4, 0, fx == FX_FIREBALL ? FX_EMBER : fx == FX_MOTE ? FX_SPARKLE : fx2,
                           OBANK_FX_B, 8, 0, 0, P3_SHRINK);
            } else {
                int it = pt - travel;
                int last = i == n - 1;
                if (impact_when(windup + i * gap + travel, last ? st : 0, dx + jx, dy + jy)) {
                    if (fx == FX_GLOB)
                        burst3(foe, jx, bh - 6, -10, 6, 26, 18, fx2 == FX_SPLAT ? FX_SPLAT : FX_GLOB, OBANK_FX_B, 22, 3,
                               P3_BOUNCE);
                    if (fx == FX_FIREBALL) burst3(foe, jx, bh, -8, 5, 18, 10, FX_FLAME_A, OBANK_FX_A, 14, -1, P3_SHRINK);
                }
                if (fx == FX_GLOB && it < 14) {
                    fx_spr_aff(dx + jx, dy + jy + 4, fx2 == FX_SPLAT ? FX_SPLAT : FX_GLOB, OBANK_FX_A, 256 + it * 20, 0);
                    if (it < 12) fx3_at(foe, jx, 0, -6, FX_SPLASH, OBANK_FX_A, 256 + it * 16, 0);
                } else if (fx == FX_ORB && it < 16) {
                    big_spr(dx, dy, FXB_GLOW, OBANK_FX_A, 256 + it * 16, 256 + it * 16);
                } else if (fx2 == FX_STEAM && it < 16) {                  /* ACID SPIT sizzles */
                    fx_spr_aff(dx + jx + ((it & 4) ? 2 : -2), dy + jy - it, FX_STEAM, OBANK_FX_B, 192 + it * 12, 0);
                    if (it < 6) fx_spr(dx + jx, dy + jy, FX_SPLAT, OBANK_FX_A);
                } else if (fx == FX_BUBBLE && it < 8) {
                    fx_spr_aff(dx + jx, dy + jy, FX_RING, OBANK_FX_A, 256 + it * 32, 0);
                } else if (fx == FX_FIREBALL && it < 14) {
                    ring3(bx, 0, bz, 8 + it * 2, FXB_WAVE, OBANK_FX_A, it * 8, 1);
                } else if (it < 8) {
                    fx_spr_aff(dx + jx, dy + jy, fx2 == FX_STAR ? FX_STAR : FX_IMPACT_SMALL, OBANK_FX_HIT,
                               288 - it * 16, it * 12);
                }
            }
        }
        if (fx == FX_ORB) anim.bg_amount = t > 8 ? tint_amt : 0;
        break;
    }
    case AK_STREAM: {
        /* the attacker rears back, then a plume pours out: it swirls round
         * its own axis and widens as it goes, then engulfs the foe */
        if (t < 8) anim.scale_y[side] = 256 + t * 4, anim.mon_dx[side] = -dir * t / 2;
        else anim.mon_dx[side] = dir * 3;
        int ul = 169;                                   /* |(ux, uz)| (the same both ways) */
        int px = -uz * 256 / ul, pz = ux * 256 / ul;    /* sideways, on the ground */
        for (int e = 0; e < 36; e += 2) {
            int pt = t - 8 - e;
            if (pt < 0 || pt >= 16) continue;
            int k = pt * 16, x, y, z;
            w3_path(side, foe, k, 0, &x, &y, &z);
            int a = e * 40 + pt * 22, r = 3 + (k * 14 >> 8);
            int c = a3_cos(a), s = a3_sin(a);
            x += (c * r >> 8) * px >> 8;
            z += (c * r >> 8) * pz >> 8;
            y += s * r >> 8;
            int f = fx_frame(fx, fx2, pt + e);
            if (fx2 == FX_PEBBLE && (e & 4)) f = FX_PEBBLE;   /* SANDBLAST: grit in the dust */
            fx3(x, y, z, f, (e & 2) ? OBANK_FX_B : OBANK_FX_A, 176 + pt * 8, fx == FX_DUST ? a : 0, foe);
        }
        if (t >= 24 && t < 52) {                        /* round the foe */
            orbit3(foe, bh - 10 + ((t - 24) >> 1), 22, 40, t * 10, 4, fx_frame(fx, fx2, t), fx2 == FX_PEBBLE ? fx : fx2,
                   224, 0);
            ring3(bx, 0, bz, 14 + ((t - 24) & 7), FXB_WAVE, OBANK_FX_B, t * 6, 1);
        }
        impact_when(24, 0, dx, dy);
        impact_when(40, st, dx, dy);
        if (t >= 24 && t < 52) anim.tint_amount = 6;
        anim.bg_amount = t > 10 && t < 54 ? tint_amt : 0;
        if (anim.type == T_BLAZE && t > 10 && t < 54) anim.wobble = 2;   /* heat shimmer */
        break;
    }
    case AK_BEAM: {
        /* a glow gathers, then the beam reaches across: its segments turned
         * along it, thick near the camera and thin far away, a spiral of
         * sparks winding round it; a flare and a ground ring where it lands */
        int len = t < 10 ? 0 : t < 22 ? (t - 10) * 256 / 12 : t < 44 ? 256 : 256 - (t - 44) * 256 / 14;
        int head = a3_atan2(dy - sy, dx - sx);
        if (t < 10) {
            if (anim.move == M_GILDED_GLEAM)       /* a coin flips up and catches the light */
                fx_spr_aff2(sx + dir * 14, sy - 10 - t, FX_COIN, OBANK_FX_B, a3_sin(t * 24 + 64), 256, 0);
            else
                fx_spr_aff(sx + dir * 14, sy - 6, FX_GLOW, OBANK_FX_B, 96 + t * 22, 0);
            ring3(ax, 0, az, 10 + t, FXB_RING, OBANK_FX_B, t * 12, 1);
            anim.scale_y[side] = 256 + t * 3;
        }
        if (anim.move == M_GILDED_GLEAM && t >= 10 && t < 13) anim.bright = 6;
        if (anim.move == M_LODE_BEAM)  /* the poles swap: red and blue cycle along the beam */
            build_fx_palette(OBANK_FX_A, (t & 4) ? MOVES[M_LODE_BEAM].col1 : MOVES[M_LODE_BEAM].col2,
                             (t & 4) ? MOVES[M_LODE_BEAM].col2 : MOVES[M_LODE_BEAM].col1);
        if (len > 0) {
            int segs = 11, pulse = (t & 2) ? 24 : 0;
            for (int i = 0; i <= segs; i++) {
                int k = i * 256 / segs;
                if (k > len) break;
                int x, y, z, px, py;
                w3_path(side, foe, k, 0, &x, &y, &z);
                int s = w3_proj(x, y, z, &px, &py);
                fx_draw(px, py, fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 288, ((s - 64) * 5 >> 2) + pulse, head, 0);
            }
            for (int i = 0; i < 4; i++) {           /* the spiral */
                int k = ((t * 12 + i * 64) & 255);
                if (k > len) continue;
                int x, y, z, a = t * 20 + i * 64;
                w3_path(side, foe, k, 0, &x, &y, &z);
                fx3(x + (a3_cos(a) >> 5), y + (a3_sin(a) >> 5), z - (a3_cos(a) >> 5), FX_SPARKLE, OBANK_FX_HIT, 200,
                    0, -1);
            }
        }
        impact_when(22, st, dx, dy);
        if (t >= 22 && t < 44) {
            big_draw(dx, dy, FXB_FLARE, OBANK_FX_B, 224 + ((t & 2) ? 32 : 0), 224 + ((t & 2) ? 32 : 0), t * 4, 0, 0);
            ring3(bx, 0, bz, 8 + ((t - 22) % 10) * 2, FXB_WAVE, OBANK_FX_A, 0, 1);
            if (fx2 != fx) fx_spr(dx + tri_sin(t * 20) / 6, dy + tri_sin(t * 33) / 6, fx2, OBANK_FX_B);
            if (anim.move == M_WINTER_RAY && (t & 3) == 0)
                p3_add(bx + fx_rand(40) - 20, bh + 20, bz + fx_rand(30) - 15, 0, -6, 0, FX_SNOWFLAKE, OBANK_FX_B, 20,
                       0, 6, P3_TUMBLE);
            anim.tint_amount = 8;
        }
        anim.bg_amount = t >= 16 && t < 48 ? tint_amt : 0;
        break;
    }
    case AK_RAIN: {
        /* things fall from above around the foe, near and far, spinning; their
         * shadows shrink in as they come; each lands with a ring and debris */
        int fall = 16;
        int step = anim.variant ? 0 : 7;
        for (int i = 0; i < n; i++) {
            int pt = t - 4 - i * step;
            if (pt < 0) continue;
            int seed = anim.variant ? anim.variant : i;
            int ox = ((seed * 23) % 41) - 20, oz = ((seed * 13) % 29) - 16;
            int oy = ((i * 11) % 13) - 6;
            int x = bx + ox, z = bz + oz;
            if (pt < fall) {
                int h = 150 - 150 * ease_in(pt, fall) / 256 + bh + oy;
                int xx = x + (fx == FX_METEOR ? (fall - pt) * 5 : 0);
                if (fx == FX_SNOWFLAKE) xx += a3_sin(pt * 16 + i * 50) >> 5;
                int rot = (fx == FX_ROCK || fx == FX_SHARD || fx == FX_METEOR) ? pt * 12 * ((i & 1) ? 1 : -1) : 0;
                if (fx == FX_SNOWFLAKE) fx3t(xx, h, z, fx, OBANK_FX_A, tumble(pt * 12 + i * 40, 64), 256, pt * 4, foe);
                else fx3(xx, h, z, fx, OBANK_FX_A, fx == FX_METEOR ? 300 : 256, rot, foe);
                shadow3(xx, z, fx == FX_METEOR ? 300 : 220, h);
                if (fx == FX_METEOR && (pt & 1))
                    p3_add(xx + 6, h + 6, z, 10, 6, 0, FX_EMBER, OBANK_FX_B, 8, 0, 0, P3_SHRINK);
            } else if (pt < fall + 12) {
                int it = pt - fall;
                int sxp, syp;
                w3_proj(x, bh + oy, z, &sxp, &syp);
                if (fx == FX_SNOWFLAKE) {
                    if (it & 2) fx_draw(sxp, syp, FX_SPARKLE, OBANK_FX_B, 256, 256, it * 16, 0);
                    impact_when(4 + i * step + fall, 0, sxp, syp);
                } else {
                    if (impact_when(4 + i * step + fall, i == n - 1 ? st : 0, sxp, syp)) {
                        if (fx2 == FX_PEBBLE || fx == FX_ROCK)
                            burst3(foe, ox, 4, oz, 4, 22, 22, fx2 == FX_PEBBLE ? FX_PEBBLE : FX_CHUNK, OBANK_FX_A, 22, 4,
                                   P3_BOUNCE);
                        else if (fx == FX_SHARD)
                            burst3(foe, ox, 6, oz, 4, 20, 18, FX_CHUNK, OBANK_FX_B, 16, 4, P3_BOUNCE);
                        else if (fx == FX_METEOR)
                            burst3(foe, ox, 4, oz, 5, 26, 26, FX_EMBER, OBANK_FX_B, 18, 3, P3_BOUNCE);
                    }
                    if (it < 8) fx_draw(sxp, syp, fx2 == FX_PEBBLE ? FX_IMPACT_SMALL : FX_IMPACT, OBANK_FX_HIT,
                                        288 - it * 12, 288 - it * 12, it * 8, 0);
                    ring3(x, 0, z, 6 + it * 2, FXB_WAVE, OBANK_FX_B, 0, 1);
                }
            }
        }
        if (fx == FX_SNOWFLAKE) anim.tint_amount = t > 20 ? 7 : 0;
        if (fx == FX_METEOR || fx == FX_SNOWFLAKE || big) anim.bg_amount = t < anim.dur - 6 ? tint_amt : 0;
        break;
    }
    case AK_BOLT: {
        /* the sky darkens, a (forked) bolt strikes: the ground flashes in a
         * ring, sparks scatter in 3D and crawl round the foe */
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
            if (t >= t0 && t < t0 + 12) {
                ring3(bx, 0, bz, 6 + (t - t0) * 3, FXB_WAVE, OBANK_FX_A, (t - t0) * 20, 1);
                if (t - t0 < 6) ring3(bx, 0, bz, 4 + (t - t0) * 2, FXB_RING, OBANK_FX_HIT, 0, 1);
            }
            if (impact_when(t0 + 1, k == strikes - 1 ? st : 0, dx, dy))
                burst3(foe, 0, 2, 0, 6, 30, 20, fx2, OBANK_FX_B, 14, 4, P3_BOUNCE | P3_SHRINK);
        }
        if (t >= 14 && t < 44) orbit3(foe, bh - 8 + ((t & 8) ? 4 : 0), 22, 90, t * 18, 3, fx2, fx2, 224, 0);
        if (t >= 14) anim.tint_amount = 8;
        break;
    }
    case AK_BURST: {
        /* pops / bubbles erupting all over a sphere round the foe, the far
         * ones behind it */
        for (int i = 0; i < n + 3; i++) {
            int pt = t - 6 - i * 4;
            if (pt < 0 || pt >= 14) continue;
            int a = i * 97, e = (i * 53) % 128 - 64, r = 26;
            int ce = a3_cos(e) * r >> 8;
            int x = bx + (a3_cos(a) * ce >> 8), z = bz + (a3_sin(a) * ce >> 8);
            int y = bh + (a3_sin(e) * r >> 8) + (fx == FX_GLOB ? pt : 0);
            int f = fx_frame(fx, fx2, pt + i);
            if (fx == FX_GLOB) f = (pt & 4) ? FX_BUBBLE : FX_GLOB;
            fx3(x, y, z, f, (i & 1) ? OBANK_FX_B : OBANK_FX_A, pt < 4 ? 128 + pt * 48 : 320 - pt * 8, pt * 6, foe);
            if (pt == 1 && i < n) {
                int px, py;
                w3_proj(x, y, z, &px, &py);
                impact_when(6 + i * 4 + 1, i == n - 1 ? st : 0, px, py);
            }
        }
        if (t >= 8 && t < 24) ring3(bx, 0, bz, (t - 8) * 3, FXB_WAVE, OBANK_FX_A, 0, 1);
        anim.bg_amount = big && t > 6 && t < 40 ? tint_amt : 0;
        if (t >= 8 && t < 40) anim.tint_amount = 6;
        if (fx2 == FX_RIVET && t >= 6 && t < 9) anim.bright = 7;   /* FORGE FLASH */
        break;
    }
    case AK_ORBIT: {
        /* motes fly over and circle the foe on a tilted orbit (dim behind it),
         * tightening, then flare */
        int r = t < 40 ? 26 : 26 - (t - 40) * 26 / 16;
        if (r < 0) r = 0;
        if (t < 14) {
            for (int i = 0; i < n; i++) {
                int k = ease_out(t, 14), x, y, z;
                w3_path(side, foe, k, 40 + i * 12, &x, &y, &z);
                fx3(x + (i - n / 2) * 6, y, z, fx_frame(fx, fx2, t + i * 3), (i & 1) ? OBANK_FX_B : OBANK_FX_A, 256, 0,
                    -1);
            }
        } else if (t < 56) {
            orbit3(foe, bh + (a3_sin(t * 6) >> 5), r, 70, t * 8, n, fx_frame(fx, fx2, t), fx_frame(fx, fx2, t + 3),
                   256, 0);
        }
        if (fx2 == FX_EYES && t > 20 && t < 50) fx_spr(dx, dy - 6, FX_EYES, OBANK_FX_B);
        if (fx2 == FX_ZZZ && t > 44) fx_spr(dx + 14 + (t - 44) / 2, dy - 18 - (t - 44) / 2, FX_ZZZ, OBANK_FX_B);
        impact_when(52, st, dx, dy);
        if (t >= 52 && t < 62) {
            big_draw(dx, dy, FXB_FLARE, OBANK_FX_A, 128 + (t - 52) * 28, 128 + (t - 52) * 28, t * 6, 0, 0);
            ring3(bx, 0, bz, (t - 52) * 3, FXB_WAVE, OBANK_FX_B, 0, 1);
        }
        if (t >= 44) anim.tint_amount = (t & 4) ? 10 : 4;
        if (anim.type == T_DUSK) anim.bg_amount = t < 58 ? tint_amt : 0;
        if (fx == FX_SPARK_B) anim.mon_dx[foe] = t > 20 ? ((t & 2) ? 1 : -1) : 0;   /* TINGLE jitter */
        break;
    }
    case AK_WAVE: {
        /* a swell rolls along the ground from behind the attacker, rearing as
         * it nears (bigger near the camera), crashes over the foe in spray */
        int ul = 169;
        int px = -uz * 256 / ul, pz = ux * 256 / ul;
        for (int row = 0; row < 2; row++) {
            int k = t * 7 - 60 - row * 22;              /* 0 = at the attacker, 256 = at the foe */
            if (k < -80 || k > 330) continue;
            int crest = 18 + (k > 0 && k < 256 ? a3_sin(k / 2) >> 4 : 0);
            for (int i = 0; i < n; i++) {
                int lat = (i - (n - 1) / 2) * 16;
                int x = ax + ((ux * k) >> 8) + ((px * lat) >> 8);
                int z = az + ((uz * k) >> 8) + ((pz * lat) >> 8);
                int y = crest + (a3_sin(t * 12 + i * 40) >> 6) - row * 8;
                int f = (fx == FX_WAVE || !(i & 1)) ? fx : fx2;
                fx3t(x, y, z, f, row ? OBANK_FX_B : OBANK_FX_A, dir * 300, 300, (k > 200 && k < 280) ? dir * 12 : 0, foe);
                if (row == 0 && (i & 1) == 0) fx3(x, 2, z - 4, FX_SPLASH, OBANK_FX_B, 220, 0, foe);
            }
        }
        if (impact_when(26, st, dx, dy)) burst3(foe, 0, bh, -8, 7, 30, 26, fx2, OBANK_FX_B, 24, 3, P3_BOUNCE);
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
            fx3_at(foe, -30 + i * 60 / (n > 1 ? n - 1 : 1), pt, (i & 1) ? 12 : -12, (i & 1) ? fx2 : fx, OBANK_FX_A, 256,
                   pt * 8);
        }
        ring3(bx, 0, bz, (t * 3) % 40, FXB_WAVE, OBANK_FX_A, 0, 1);
        impact_when(20, st, dx, dy);
        break;
    }
    case AK_BUFF: {
        /* the user draws power in: a circle turns at its feet, particles rise
         * round it on a helix (behind it on the far side) */
        int k = t < 10 ? t * 26 : t > 44 ? (52 - t) * 32 : 256;
        if (k > 0) ring3(ax, 0, az, (k * 26) >> 8, FXB_RING, OBANK_FX_A, t * 4, 1);
        for (int i = 0; i < n; i++) {
            int pt = (t + i * 11) % 24;
            if (pt < 18) {
                int a = i * 256 / n + pt * 10;
                fx3(ax + (a3_cos(a) * 24 >> 8), pt * 3 + 2, az + (a3_sin(a) * 24 >> 8), fx,
                    (i & 1) ? OBANK_FX_B : OBANK_FX_A, 256 - pt * 4, 0, side);
            }
        }
        anim.tint_side = side;
        anim.tint_amount = 6 + tri_sin(t * 8) / 12;
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
                if (t < 34) ring3(bx, 0, bz, (t - 20) * 2, FXB_WAVE, OBANK_FX_B, 0, 1);
            }
            impact_when(24, 0, dx, dy);
            break;
        }
        if (anim.move == M_POUT) anim.mon_dx[side] = t < 16 ? ((t & 2) ? 2 : -2) : 0;
        for (int i = 0; i < n; i++) {
            int pt = t - 6 - i * 6;
            if (pt < 0) continue;
            if (pt < 24) {
                int x, y, z;
                w3_path(side, foe, pt * 256 / 24, 30 + i * 10, &x, &y, &z);
                x += a3_sin(pt * 20 + i * 70) >> 5;
                fx3(x, y, z, fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 256, 0, -1);
            } else if (pt < 36) {                     /* they circle the foe's head */
                int a = pt * 14 + i * 256 / n;
                fx3(bx + (a3_cos(a) * 18 >> 8), bh + 14, bz + (a3_sin(a) * 18 >> 8),
                    (fx2 != fx && (pt & 4)) ? fx2 : fx, OBANK_FX_A, 240, 0, foe);
            }
        }
        if (fx2 == FX_TEAR && t < 20)   /* POUT: tears roll down */
            for (int k = 0; k < 2; k++) fx_spr(sx + (k ? 8 : -8), sy - 10 + (t + k * 7) % 14, FX_TEAR, OBANK_FX_B);
        impact_when(34, 0, dx, dy);
        break;
    }
    case AK_FANGS: {
        /* jaws come in from the camera's side, open wide and snap; the bite
         * throws chips and rings the ground */
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
            int sc = ft < 10 ? 400 - ft * 14 : 260;    /* nearer the camera, then on the foe */
            int tilt = ft < 10 ? (10 - ft) * 2 : 0;
            if (rot) {
                fx_spr_aff(dx - 4 - gap, dy, FX_FANG_TOP, OBANK_FX_A, sc, 192 + tilt);
                fx_spr_aff(dx + 8 + gap, dy, FX_FANG_TOP, OBANK_FX_A, sc, 64 - tilt);
            } else {
                fx_spr_aff(dx, dy - 4 - gap, FX_FANG_TOP, OBANK_FX_A, sc, -tilt);
                fx_spr_aff(dx, dy + 8 + gap, FX_FANG_BOTTOM, OBANK_FX_A, sc, tilt);
            }
            if (impact_when(4 + i * 14 + 10, i == n - 1 ? st : 0, dx, dy))
                burst3(foe, 0, bh, -10, 4, 22, 14, FX_IMPACT_SMALL, OBANK_FX_HIT, 10, 2, P3_SHRINK);
            if (ft >= 10 && ft < 22) {
                int it = ft - 10;
                ring3(bx, 0, bz, 8 + it * 2, FXB_WAVE, OBANK_FX_B, 0, 1);
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
        /* life lifts out of the foe and streams home as a double helix,
         * growing or shrinking with its depth; it circles the user */
        for (int i = 0; i < n; i++) {
            int pt = t - 12 - i * 5;
            if (pt < 0 || pt >= 26) continue;
            int k = ease_in(pt, 26), x, y, z;
            w3_path(foe, side, k, 30, &x, &y, &z);
            int a = pt * 16 + (i & 1) * 128, r = a3_sin(k / 2) >> 4;   /* bulges mid-way */
            x += a3_cos(a) * r >> 8;
            z += a3_cos(a) * r >> 9;
            y += a3_sin(a) * r >> 8;
            fx3(x, y, z, fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 320 - pt * 5, 0, side);
        }
        impact_when(10, 0, dx, dy);
        if (t < 18) anim.tint_amount = 9;
        if (t >= 40) {
            anim.tint_side = side;
            anim.tint_amount = 7;
            orbit3(side, ah + ((t - 40) >> 1), 24, 40, t * 10, 4, fx2, fx2, 224, 0);
        }
        if (fx2 == FX_SKULL && t < 20 && (t & 2)) fx_spr(dx, dy - 20, FX_SKULL, OBANK_FX_B);
        if (t == 12) sfx_play(SFX_DRAIN);
        break;
    }
    case AK_DASH: {
        /* a blur of afterimages that strikes first; dust flies off the ground */
        int l = t < 4 ? -t : t < 10 ? -4 + (48 + 4) * ease_in(t - 4, 6) / 256 : t < 16 ? 48 :
                t < 26 ? 48 - 48 * ease_out(t - 16, 10) / 256 : 0;
        anim.mon_dx[side] = dir * l;
        anim.mon_dy[side] = -dir * l / 3;
        anim.afterimage = t >= 4 && t < 18;
        if (t >= 4 && t < 16) {
            int head = a3_atan2(dy - sy, dx - sx);
            for (int k = 1; k <= 2; k++)
                fx_spr_aff2(sx + dir * (l - k * 14), sy - dir * (l - k * 14) / 3 + k * 3, fx2, OBANK_FX_B, 256, 256,
                            fx2 == FX_SPEEDLINE ? head : 0);
            if (t & 1)
                p3_add(ax + ((ux * l) >> 7), 2, az + ((uz * l) >> 7), -ux / 5, 8 + fx_rand(8), -uz / 5, FX_DUST,
                       OBANK_FX_B, 10, 1, 0, P3_SHRINK);
        }
        impact_when(10, st, dx - dir * 6, dy);
        if (t >= 10 && t < 20) ring3(bx, 0, bz, 6 + (t - 10) * 3, FXB_WAVE, OBANK_FX_HIT, 0, 1);
        if (!fx_is_hit(fx) && t >= 10 && t < 16) fx_spr_aff(dx - dir * 8, dy, fx, OBANK_FX_A, 320 - (t - 10) * 10, 0);
        if (fx2 == FX_FLAKE && t >= 10 && t < 20)                                         /* IRON TAP rings */
            fx_spr_aff(dx - dir * 6, dy, FX_RING, OBANK_FX_B, 160 + (t - 10) * 24, 0);
        break;
    }
    case AK_SLAM: {
        /* BELLY FLOP: crouch, leap in an arc (its shadow slides along the
         * ground under it), land on the foe: shockwave and a ring of dust */
        int jt = t - 8;
        int wk = 0, hgt = 0;                           /* world progress and height of the jump */
        if (t < 8) {
            anim.scale_x[side] = 256 + t * 5;
            anim.scale_y[side] = 256 - t * 5;
        } else if (jt < 18) {
            int k = jt * 256 / 18;
            anim.mon_dx[side] = dir * (dx - sx) * k / 256;
            anim.mon_dy[side] = (dy - sy) * k / 256 - soft_sin(jt * 128 / 18) * 50 / 64;
            anim.scale_x[side] = 232;
            anim.scale_y[side] = 284;
            wk = k;
            hgt = a3_sin(jt * 128 / 18) * 70 >> 8;
        } else if (jt < 26) {
            anim.mon_dx[side] = dir * (dx - sx);
            anim.mon_dy[side] = dy - sy;
            anim.scale_x[side] = 300 - (jt - 18) * 5;
            anim.scale_y[side] = 212 + (jt - 18) * 5;
            wk = 256;
        } else {
            int k = 256 - ease_out(jt - 26, 18);
            anim.mon_dx[side] = dir * (dx - sx) * k / 256;
            anim.mon_dy[side] = (dy - sy) * k / 256 - soft_sin((jt - 26) * 128 / 18) * 12 / 64;
            wk = k;
        }
        if (t >= 8 && jt < 18) shadow3(ax + ((ux * wk) >> 8), az + ((uz * wk) >> 8), 560, hgt);
        if (impact_when(26, st, dx, dy)) {
            for (int k = 0; k < 10; k++)
                p3_add(bx, 3, bz, a3_cos(k * 26) * 3 >> 4, 4, a3_sin(k * 26) * 3 >> 4, fx2 == FX_CRACK ? fx : fx2,
                       OBANK_FX_B, 18, 0, 4, P3_SHRINK);
            feel.zoom = 14;
        }
        if (jt >= 18 && jt < 34) {
            ring3(bx, 0, bz, 6 + (jt - 18) * 3, FXB_WAVE, OBANK_FX_A, 0, 1);
            if (jt < 26) ring3(bx, 0, bz, 4 + (jt - 18) * 2, FXB_RING, OBANK_FX_HIT, 0, 1);
        }
        if (fx2 == FX_CRACK && jt >= 18 && jt < 40)   /* OSSIFY: the foe stiffens and cracks */
            for (int k = 0; k < 2; k++) fx_spr_flip(dx + (k ? 8 : -8), dy - 4 + k * 8, FX_CRACK, OBANK_FX_A, k ? ATTR1_HFLIP : 0);
        break;
    }
    case AK_WHIP:
        /* the lash snakes out through the air, each segment turned along it */
        for (int i = 0; i < n; i++) {
            int wt = t - 4 - i * 12;
            if (wt < 0 || wt >= 22) continue;
            int reach = wt < 10 ? wt : wt < 14 ? 10 : 22 - wt;
            int ppx = sx, ppy = sy;
            for (int s = 1; s <= reach; s++) {
                int x, y, z, px, py;
                w3_path(side, foe, s * 256 / 10, 20, &x, &y, &z);
                y += (a3_sin(s * 30 + i * 128 + wt * 16) * (10 - s)) >> 8;
                x += (a3_cos(s * 30 + wt * 16) * 6) >> 8;
                int sc = w3_proj(x, y, z, &px, &py);
                fx_draw(px, py, FX_VINE, OBANK_FX_A, w3_spr_scale(sc), w3_spr_scale(sc), a3_atan2(py - ppy, px - ppx),
                        0);
                ppx = px, ppy = py;
            }
            if (impact_when(4 + i * 12 + 9, i == n - 1 ? st : 0, dx, dy))
                burst3(foe, 0, bh, -8, 3, 20, 14, fx2, OBANK_FX_B, 18, 2, P3_TUMBLE);
            if (wt >= 9 && wt < 13) big_draw(dx, dy, FXB_FLARE, OBANK_FX_HIT, 160 - (wt - 9) * 24, 160 - (wt - 9) * 24,
                                            wt * 8, 0, 0);
        }
        break;
    case AK_PSYCHIC: {
        /* rings spin round the foe on tilted axes like a gyroscope; everything
         * sways */
        if (anim.move == M_DAYDREAM) build_fx_palette(OBANK_FX_A, hue15(t * 6), hue15(t * 6 + 64));
        for (int i = 0; i < n + 1; i++) {
            int pt = t - 6 - i * 8;
            if (pt < 0 || pt >= 28) continue;
            int k = 64 + pt * 7;
            int sq = a3_cos(t * 6 + i * 85);           /* the ring turning edge-on and back */
            big_draw(dx, dy, FXB_RING, (i & 1) ? OBANK_FX_B : OBANK_FX_A, k, (k * atleast(absi(sq), 24)) >> 8,
                     i * 40 + t * 3, 1, 0);
        }
        anim.mon_dx[foe] = soft_sin(t * 14) / 16;
        a3_cam_x = soft_sin(t * 6) / 22;
        anim.tint_amount = 8 + tri_sin(t * 10) / 16;
        impact_when(22, st, dx, dy);
        anim.bg_amount = big && t < anim.dur - 6 ? tint_amt : 0;
        break;
    }
    case AK_POWDER: {
        /* a puff drifts down through the air round the foe (in front of it and
         * behind), each grain tumbling */
        for (int i = 0; i < n; i++) {
            int pt = t - i * 4;
            if (pt < 0 || pt >= 44) continue;
            int lx = ((i * 17) % 44) - 22 + (a3_sin(pt * 8 + i * 30) >> 5);
            int lz = ((i * 29) % 36) - 18;
            int y = 80 - pt * 2;
            int f = (i % 3) ? fx : fx2 == FX_STEAM ? FX_POWDER : fx;
            fx3t(bx + lx, y, bz + lz, f, (i & 1) ? OBANK_FX_B : OBANK_FX_A, tumble(pt * 10 + i * 40, 80), 256, pt * 3,
                 foe);
        }
        if (fx2 == FX_STEAM && t < 40)   /* SPORE CLOUD: a cloud hangs over it */
            fx_spr_aff(dx, dy - 20 + t / 4, FX_STEAM, OBANK_FX_A, 256 + t * 4, 0);
        if (fx == FX_SNOWFLAKE && fx2 == FX_DUST && t > 28) {  /* SNOWDRIFT: snow piles up round its feet */
            ring3(bx, 0, bz, 12 + (t - 28) / 3, FXB_GLOW, OBANK_FX_B, 0, 1);
            fx_spr_aff2(dx, side_gy(foe) - 6, FX_DUST, OBANK_FX_B, 320 + (t - 28) * 6, 256, 0);
        }
        if (fx2 == FX_ZZZ && t > 36)      /* DOZE POLLEN: Zzz */
            fx_spr(dx + 16 + (t - 36) / 3, dy - 20 - (t - 36) / 2, FX_ZZZ, OBANK_FX_B);
        if (t > 44) anim.tint_amount = (t & 4) ? 9 : 5;
        impact_when(46, 0, dx, dy);
        break;
    }
    case AK_STRIKE: {
        /* fists fly in from beside the camera (big and near), shrinking onto
         * the foe; each blow rings the ground */
        int step = 14;
        for (int i = 0; i < n; i++) {
            int s0 = anim.variant ? 2 : 4 + i * step;
            int stt = t - s0;
            if (stt < 0 || stt >= 20) continue;
            int from = ((i + anim.variant) & 1) ? 1 : -1;
            if (stt < 8) {
                int k = ease_in(stt, 8);
                int x0 = bx + from * 40 - (ux >> 2), z0 = bz - 110, y0 = bh + 34;
                int x = x0 + (((bx - x0) * k) >> 8), z = z0 + (((bz - 10 - z0) * k) >> 8);
                int y = y0 + (((bh - y0) * k) >> 8);
                fx3(x, y, z, fx, OBANK_FX_A, 256, from > 0 ? 16 - stt * 2 : -16 + stt * 2, -1);
            } else if (stt < 14) {
                fx_spr_aff(dx + from * 4, dy, FX_IMPACT, OBANK_FX_HIT, 320 - (stt - 8) * 16, stt * 10);
                ring3(bx, 0, bz, (stt - 7) * 4, FXB_WAVE, OBANK_FX_B, 0, 1);
            }
            impact_when(s0 + 8, (i == n - 1 && (anim.flags & HITF_LAST)) ? st + (anim.move == M_HAMMER_FIST) : 0,
                        dx + from * 4, dy);
        }
        if (anim.move == M_HAMMER_FIST && t < 6) anim.mon_dy[side] = -t;
        break;
    }
    case AK_ROAR: {
        /* rears up, then shockwaves: rings that burst out at the camera and a
         * wave racing along the ground; a punch-in, heavy shake */
        int status = MOVES[anim.move].cat == CAT_STATUS;
        if (t < 10) {
            anim.scale_x[side] = 256 - t * 3;
            anim.scale_y[side] = 256 + t * 5;
            anim.mon_dy[side] = -t / 2;
        } else if (t < 44) {
            anim.scale_x[side] = 286 + ((t & 2) ? 6 : 0);
            anim.scale_y[side] = 236;
            if (t == 10) {
                sfx_play(SFX_ROAR);
                feel.zoom = status ? 10 : 18;
            }
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
        if (t >= 10 && t < 40) {                      /* the ground wave rolls out */
            int r = (t - 10) * 4;
            if (r <= 30) ring3(ax, 0, az, r, FXB_WAVE, OBANK_FX_A, 0, 1);
            bead_ring3(ax, 2, az, r + 8, 10, t * 2, FX_DUST, OBANK_FX_B, 200, side);
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
        /* rumble, the ground under the foe bulges in a ring, then a scalding
         * column spirals up and rains back down */
        int gy = side_gy(foe);
        if (t < 20) {
            shake(12 + t, 1);
            ring3(bx, 0, bz, 4 + t, FXB_VORTEX, OBANK_FX_B, -t * 10, 1);
            if (t & 4) fx_spr(dx + ((t * 7) % 20) - 10, gy - 2, FX_DUST, OBANK_FX_B);
        } else if (t < 50) {
            int h = ease_out(t - 20, 10) * 100 / 256;
            if (t > 40) h = h * (50 - t) / 10;
            for (int k = 0; k < h; k += 8) {
                int a = t * 24 + k * 6;
                int r = 8 + (k >> 3);
                fx3(bx + (a3_cos(a) * r >> 8), k, bz + (a3_sin(a) * r >> 8), (k / 8 + t / 2) & 1 ? FX_DROP : FX_BUBBLE,
                    (k / 8) & 1 ? OBANK_FX_B : OBANK_FX_A, 256, 0, foe);
                fx3(bx - (a3_cos(a) * r >> 8), k + 4, bz - (a3_sin(a) * r >> 8), FX_DROP, OBANK_FX_A, 240, 0, foe);
            }
            ring3(bx, 0, bz, 20 + ((t & 3) << 1), FXB_WAVE, OBANK_FX_A, 0, 1);
            if (t > 26) fx3(bx, h + 8, bz, fx2, OBANK_FX_B, 256 + (t - 26) * 8, 0, -1);
            if (t > 30 && (t & 1))
                p3_add(bx, h, bz, fx_rand(40) - 20, 10 + fx_rand(10), fx_rand(40) - 20, FX_DROP, OBANK_FX_A, 26, 2, 0,
                       P3_BOUNCE | P3_SHRINK);
            anim.mon_dy[foe] = -h / 5;
            anim.tint_amount = 7;
        }
        impact_when(22, st, dx, dy);
        anim.bg_amount = t > 16 && t < 54 ? tint_amt : 0;
        break;
    }
    case AK_SUNSHAFT: {
        /* the sky brightens, a shaft of sunlight falls on the foe and lights
         * a turning pool on the ground; motes drift up in it */
        anim.bg_color = RGB15(31, 31, 20);
        anim.bg_amount = t < 56 ? (t < 10 ? t : 9) : 0;
        if (t < 14) fx_spr_aff(sx, sy - 24, FX_SPARKLE, OBANK_FX_B, 128 + t * 20, t * 6);
        if (t >= 14 && t < 52) {
            int h = ease_in(t - 14, 8) * (dy + 16) / 256;
            int wid = t < 40 ? 256 + ((t & 2) ? 32 : 0) : 256 - (t - 40) * 18;
            for (int y = 0; y < h; y += 16)
                fx_spr_aff2(dx, y, fx, (y & 16) ? OBANK_FX_B : OBANK_FX_A, wid * 3 / 2, 256, 0);
            if (h >= dy) ring3(bx, 0, bz, 18 + ((t & 4) ? 2 : 0), FXB_RING, OBANK_FX_B, t * 3, 1);
            if (t > 22) fx_spr(dx + tri_sin(t * 21) / 5, dy + tri_sin(t * 13) / 8, fx2, OBANK_FX_B);
            if ((t & 3) == 0)
                p3_add(bx + fx_rand(30) - 15, 2, bz + fx_rand(24) - 12, 0, 10, 0, FX_SPARKLE, OBANK_FX_B, 20, -1, 8, 0);
            anim.tint_amount = 9;
        }
        if (t >= 22 && t < 25) anim.bright = 6;
        impact_when(22, st, dx, dy);
        break;
    }
    case AK_FAULT: {
        /* the ground splits along a jagged line to the foe (narrowing into the
         * distance), then heaves: slabs and chips tumble up and bounce */
        int len = t < 26 ? ease_in(t, 26) : 256;
        int segs = 11;
        for (int i = 0; i <= segs; i++) {
            int k = i * 256 / segs;
            if (k > len) break;
            int x = ax + ((ux * k) >> 8) + ((i & 1) ? 5 : -5), z = az + ((uz * k) >> 8);
            int px, py, s = w3_proj(x, 0, z, &px, &py);
            if (t < 58) fx_draw(px, py, fx, OBANK_FX_A, w3_spr_scale(s), (w3_spr_scale(s) * 3) >> 2, (i & 1) ? 8 : -8, 0);
        }
        if (t < 26) shake(20 + t, 1);
        if (t == 27)
            for (int k = 0; k < 6; k++)
                p3_add(bx + (k - 3) * 10, 2, bz + ((k * 7) % 11) - 5, (k - 3) * 6, 40 + (k & 1) * 12, fx_rand(20) - 10,
                       k & 1 ? fx2 : FX_CHUNK, k & 1 ? OBANK_FX_B : OBANK_FX_A, 30, 4, 12 * ((k & 1) ? 1 : -1),
                       P3_BOUNCE | P3_SHADOW);
        if (t >= 26 && t < 44) {
            anim.mon_dy[foe] = -soft_sin((t - 26) * 8) / 6;
            ring3(bx, 0, bz, (t - 26) * 2, FXB_WAVE, OBANK_FX_B, 0, 1);
        }
        impact_when(27, st, dx, dy);
        break;
    }
    case AK_WOBBLE: {
        /* DREAMQUAKE: the world wobbles, pixelates and the camera sways;
         * rings turn round the foe on tilted axes */
        int k = t < 12 ? t : t > 48 ? 64 - t : 12;
        anim.wobble = k * 6 / 12;
        anim.mosaic = k * 5 / 12;
        a3_cam_x = (a3_sin(t * 5) * k) >> 9;
        a3_cam_y = (a3_sin(t * 7) * k) >> 10;
        for (int i = 0; i < n; i++) {
            int pt = (t + i * 10) % 30;
            int kk = 96 + pt * 12;
            big_draw(dx, dy, FXB_RING, (i & 1) ? OBANK_FX_B : OBANK_FX_A, kk, (kk * atleast(absi(a3_sin(t * 4 + i * 60)), 40)) >> 8,
                     i * 85 + t * 2, 1, 0);
        }
        anim.mon_dx[foe] = soft_sin(t * 12) / 10;
        anim.mon_dx[side] = soft_sin(t * 12 + 128) / 20;
        anim.tint_amount = 8;
        anim.bg_amount = t < 56 ? tint_amt : 0;
        impact_when(30, st, dx, dy);
        break;
    }
    case AK_HEAL: {
        /* a glowing circle turns at the user's feet (sunlight / candles / a
         * nap on top), sparkles rise round it on a helix */
        anim.tint_side = side;
        int k = t < 10 ? t * 26 : t > 48 ? (58 - t) * 26 : 256;
        if (k > 0) ring3(ax, 0, az, (k * 24) >> 8, FXB_RING, OBANK_FX_B, -t * 3, 1);
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
            for (int i = 0; i < 6; i++) {
                if (t <= 4 + i * 3 || t >= 54) continue;
                int a = i * 43 + 16;
                fx3(ax + (a3_cos(a) * 34 >> 8), 8, az + (a3_sin(a) * 30 >> 8), FX_CANDLE,
                    ((t + i * 3) & 4) ? OBANK_FX_A : OBANK_FX_B, 256, 0, side);
            }
            anim.mon_dy[side] = t > 10 && t < 46 ? -2 : 0;
        } else {
            int curl = t < 12 ? t : t > 44 ? 56 - t : 12;
            anim.scale_x[side] = 256 + curl * 3;
            anim.scale_y[side] = 256 - curl * 4;
            if (t > 10 && t < 46) fx_spr(sx + 18 + (t - 10) / 3, sy - 22 - (t - 10) / 3, FX_ZZZ, OBANK_FX_A);
        }
        if (t < 48 && (fx != FX_CANDLE || t > 16))
            for (int i = 0; i < 5; i++) {
                int pt = (t + i * 9) % 30;
                int a = i * 51 + pt * 8;
                fx3(ax + (a3_cos(a) * 22 >> 8), pt * 2, az + (a3_sin(a) * 22 >> 8), fx2, OBANK_FX_B, 224, 0, side);
            }
        anim.tint_amount = 5 + tri_sin(t * 8) / 16;
        if (t == 12) sfx_play(SFX_SPARKLE);
        self_pulse_when(20);
        break;
    }
    case AK_CHARGE: {
        /* charge up (motes rush in from every side, near and far, a circle
         * spins faster under it), then let go with a flare */
        int rel = 38;
        if (t < rel) {
            if (t == 2) sfx_play(SFX_CHARGE);
            for (int i = 0; i < 7; i++) {
                int pt = (t * 2 + i * 11) % 24;
                int a = i * 37 + t * 3, e = (i * 45) % 128 - 64;
                int r = 48 - pt * 48 / 24;
                int ce = a3_cos(e) * r >> 8;
                fx3(ax + (a3_cos(a) * ce >> 8), ah + (a3_sin(e) * r >> 8), az + (a3_sin(a) * ce >> 8),
                    (i & 1) ? fx2 : FX_SPARKLE, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 160 + pt * 4, 0, side);
            }
            ring3(ax, 0, az, 14 + t / 4, FXB_RING, OBANK_FX_A, (t * t) >> 3, 1);
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
                if (it < 18) ring3(bx, 0, bz, 6 + it * 2, FXB_WAVE, OBANK_FX_A, it * 16, 1);
            } else {                        /* SUNFLARE / BRIM BURST: a burst at the foe */
                if (it < 8) {
                    int x, y, z;
                    w3_path(side, foe, it * 32, 20, &x, &y, &z);
                    fx3(x, y, z, FX_BURST, OBANK_FX_A, 256 + it * 16, it * 16, -1);
                } else if (it < 30) {
                    int g = it - 8;
                    big_draw(dx, dy, FXB_FLARE, OBANK_FX_A, 160 + g * 14, 160 + g * 14, g * 5, 0, 0);
                    ring3(bx, 0, bz, g * 2, FXB_WAVE, OBANK_FX_B, 0, 1);
                    for (int i = 0; i < n; i++) {
                        int a = i * 256 / n + it * 3, e = (i * 37) % 96 - 48;
                        int r = g * 3, ce = a3_cos(e) * r >> 8;
                        fx3(bx + (a3_cos(a) * ce >> 8), bh + (a3_sin(e) * r >> 8), bz + (a3_sin(a) * ce >> 8),
                            fx_frame(fx2, fx2 == FX_FLAME_B ? FX_FLAME_A : fx2, it + i), (i & 1) ? OBANK_FX_B : OBANK_FX_A,
                            256, 0, foe);
                    }
                }
                if (it >= 8 && it < 11) anim.bright = 8;
            }
            if (impact_when(fx == FX_BOLT ? rel + 1 : rel + 8, st + 1, dx, dy)) feel.zoom = 16;
            anim.tint_side = foe;
            if (it > 8) anim.tint_amount = 9;
        }
        break;
    }
    case AK_LURE: {
        /* a friendly flame bobs over, then circles the foe on a real orbit
         * (behind it and back), then flares */
        int lf = fx == FX_TRINKET ? FX_TRINKET : FX_WISP;   /* CURSED CURIO: an unlucky trinket */
        int x, y, z;
        if (t < 30) {
            w3_path(side, foe, t * 256 / 30, 30, &x, &y, &z);
            y += 12 + (a3_sin(t * 16) >> 5);
        } else {
            int a = (t - 30) * 12 - 64;
            int r = t < 54 ? 24 : 24 - (t - 54) * 3;
            x = bx + (a3_cos(a) * r >> 8);
            z = bz + (a3_sin(a) * r >> 8);
            y = bh + 12 + (a3_sin(t * 16) >> 6);
        }
        if (t < 62) fx3(x, y, z, lf, OBANK_FX_A, 256 + (a3_sin(t * 20) >> 2), lf == FX_TRINKET ? a3_sin(t * 8) >> 3 : 0,
                        foe);
        if (t < 62) shadow3(x, z, 180, y);
        if (fx2 == FX_EYES && t > 34 && t < 62 && (t & 8)) fx_spr(dx, dy - 8, FX_EYES, OBANK_FX_B);
        if (t > 8 && (t & 3) == 0 && t < 60) p3_add(x, y - 4, z, 0, -3, 0, FX_SPARKLE, OBANK_FX_B, 10, 0, 6, 0);
        if (t >= 62 && t < 72) big_draw(dx, dy, FXB_FLARE, OBANK_FX_A, 160 + (t - 62) * 16, 160 + (t - 62) * 16, t * 4,
                                        0, 0);
        impact_when(62, 0, dx, dy);
        anim.bg_amount = t > 20 && t < 70 ? 4 : 0;
        break;
    }
    case AK_STOOP: {
        /* folds its wings, rises out of sight, drops on the foe from above:
         * its shadow swells on the ground first */
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
        if (t >= 14 && t < 30) shadow3(bx, bz, 300 + (t - 14) * 20, (30 - t) * 10);
        if (impact_when(30, st, dx, dy)) {
            burst3(foe, 0, bh, 0, 6, 16, 16, fx2, OBANK_FX_B, 30, 1, P3_TUMBLE);
            feel.zoom = 16;
        }
        if (t >= 30 && t < 44) ring3(bx, 0, bz, 6 + (t - 30) * 3, FXB_WAVE, OBANK_FX_A, 0, 1);
        break;
    }
    case AK_HAYMAKER: {
        /* a huge wind-up that trembles, then the swing comes round past the
         * camera and lands: a punch-in and a shockwave */
        if (t < 24) {
            anim.mon_dx[side] = -dir * ease_out(t, 24) * 12 / 256 + ((t > 12 && (t & 1)) ? 1 : 0);
            anim.scale_x[side] = 256 - t * 2;
            anim.scale_y[side] = 256 + t * 2;
            if (t > 8) fx3_at(side, -dir * 26, ah + 10, -8, fx, OBANK_FX_A, 256 + (t - 8) * 6, -dir * t * 2);
        } else if (t < 32) {
            int k = ease_in(t - 24, 8);
            anim.mon_dx[side] = -dir * 12 + dir * 50 * k / 256;
            /* the fist swings on an arc that bulges toward the camera */
            int x = ax + ((ux * k) >> 8), z = az + ((uz * k) >> 8) - (a3_sin(k / 2) * 70 >> 8);
            int y = ah + 20 - ((20 + ah - bh) * k >> 8);
            fx3(x, y, z, fx, OBANK_FX_A, 300, dir * (t - 24) * 16, -1);
            int px, py;
            w3_proj(x, y, z, &px, &py);
            fx_spr_aff(px - dir * 14, py + 4, FX_SPEEDLINE, OBANK_FX_B, 256, 0);
        } else {
            anim.mon_dx[side] = dir * 38 * (256 - ease_out(t - 32, 20)) / 256;
            if (t < 40) big_spr(dx, dy, FXB_RING, OBANK_FX_HIT, 128 + (t - 32) * 24, 128 + (t - 32) * 24);
            if (t < 46) ring3(bx, 0, bz, 6 + (t - 32) * 2, FXB_WAVE, OBANK_FX_A, 0, 1);
        }
        if (impact_when(32, st + 1, dx, dy)) feel.zoom = 22;
        break;
    }
    case AK_SPIRAL: {
        /* LEAF FLURRY: a true corkscrew round the line to the foe (the far
         * turns shrink and pass behind), each leaf tumbling */
        int ul = 169;
        int px = -uz * 256 / ul, pz = ux * 256 / ul;
        for (int i = 0; i < n; i++) {
            int pt = t - 4 - i * 3;
            if (pt < 0 || pt >= 26) continue;
            int k = pt * 256 / 22, x, y, z;
            w3_path(side, foe, k > 256 ? 256 : k, 0, &x, &y, &z);
            int a = pt * 20 + i * 32;
            int r = 16 - (pt > 20 ? (pt - 20) * 3 : 0);
            int c = a3_cos(a) * r >> 8;
            x += (c * px) >> 8;
            z += (c * pz) >> 8;
            y += a3_sin(a) * r >> 8;
            fx3t(x, y, z, ((pt >> 2) & 1) ? fx2 : fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A, tumble(a * 2, 72), 256, a,
                 k >= 230 ? foe : -1);
        }
        impact_when(26, 0, dx, dy);
        impact_when(34, st, dx, dy);
        break;
    }
    case AK_RIPPLE: {
        /* STILL POND: calm rings spread on the ground round the user */
        anim.tint_side = side;
        anim.tint_amount = 6;
        anim.bg_amount = t < 50 ? 4 : 0;
        for (int i = 0; i < n; i++) {
            int pt = (t + i * 14) % 42;
            if (t + 10 > anim.dur && pt < 10) continue;
            ring3(ax, 0, az, 6 + pt * 3 / 4, pt < 28 ? FXB_RING : FXB_WAVE, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 0, 1);
        }
        if (t > 8 && t < 40 && ((t >> 3) & 1)) fx_spr(sx, sy - 26, fx2, OBANK_FX_B);
        self_pulse_when(20);
        break;
    }
    case AK_WRAP: {
        /* SILK SNARE: threads shoot over and wind round the foe, bands turning
         * round it (the far side of each band behind it) */
        for (int i = 0; i < n; i++) {
            int pt = t - 4 - i * 6;
            if (pt < 0) continue;
            if (pt < 16) {
                int x, y, z;
                w3_path(side, foe, pt * 16, 30, &x, &y, &z);
                fx3(x, y, z, fx, OBANK_FX_A, 256, a3_atan2(dy - sy, dx - sx), -1);
            } else if (t < 52 && i == 0) {             /* the threads wind round and round it */
                int top = 8 + ((t - 20) * 3 < 60 ? (t - 20) * 3 : 60);
                helix3(foe, bx, bz, 4, top, 22, 6, 256 * 3, t * 12, 14, fx, fx, 224);
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
        /* BRACE / THORN WALL: plant the feet (squash), things close in from
         * all round, a circle on the ground, a glint sweeps */
        int k = t < 10 ? t : t < 34 ? 10 : 46 - t;
        if (k < 0) k = 0;
        anim.scale_x[side] = 256 + k * 4;
        anim.scale_y[side] = 256 - k * 4;
        anim.tint_side = side;
        anim.tint_amount = k * 8 / 10;
        if (k) ring3(ax, 0, az, 12 + k, FXB_RING, OBANK_FX_B, t * 2, 1);
        if ((fx == FX_PEBBLE || fx == FX_FLAKE || fx == FX_VINE) && t < 20)
            orbit3(side, ah - 4, 48 - t * 2, 50, t * 4, 6, fx, fx, 256, 0);
        if (fx == FX_VINE && t >= 18 && t < 42)   /* THORN WALL: a hedge stands between it and the foe */
            for (int i = 0; i < 4; i++) {
                int lat = (i - 2) * 16 + 8;
                int grow = t < 26 ? (t - 18) * 256 / 8 : 256;
                fx3t(ax + (ux >> 3) - lat * uz / 169, 6 + ((i & 1) ? 4 : 0), az + (uz >> 3) + lat * ux / 169,
                     (i & 1) ? fx2 : fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 256, grow, 0, -1);
            }
        if (t >= 18 && t < 32) {
            int gx = sx - 24 + (t - 18) * 4;
            fx_spr_aff(gx, sy - 12 + (t - 18), FX_SPARKLE, OBANK_FX_B, 320, t * 8);
        }
        self_pulse_when(10);
        break;
    }
    case AK_RUSH: {
        /* BULLRUSH: long wind-up (dust), speed lines, huge hit with a
         * punch-in and shockwave, bounced back */
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
            if (t & 1)
                p3_add(ax - (ux >> 4), 2, az - (uz >> 4), -ux / 6 + fx_rand(12) - 6, 6 + fx_rand(8), -uz / 6, FX_DUST,
                       OBANK_FX_B, 14, 1, 0, P3_SHRINK);
        }
        anim.afterimage = t >= 12 && t < 22;
        if (t >= 12 && t < 22)
            for (int k = 0; k < 3; k++)
                fx_spr(sx + dir * (l - 16 - k * 12), sy - 8 + k * 8 - dir * l / 3,
                       fx == FX_IMPACT ? FX_SPEEDLINE : fx_is_hit(fx) ? fx2 : fx, OBANK_FX_B);
        if (fx == FX_BUG && t < 34) {           /* SWARM RUSH: the swarm rides along, round it */
            int wk = l * 256 / 64;
            int cx = ax + ((ux * wk) >> 8), cz = az + ((uz * wk) >> 8);
            for (int k = 0; k < n; k++) {
                int a = t * 16 + k * 256 / n;
                fx3(cx + (a3_cos(a) * 26 >> 8), ah + (a3_sin(a * 2) >> 5), cz + (a3_sin(a) * 20 >> 8), FX_BUG,
                    (k & 1) ? OBANK_FX_B : OBANK_FX_A, 224, 0, cz > (az + bz) / 2 ? foe : side);
            }
        }
        if (fx == FX_METEOR && t >= 12 && t < 24)   /* COMET DASH: it wears a comet's head */
            fx_spr_aff(sx + dir * l + dir * 10, sy - 8 - dir * l / 3, FX_METEOR, OBANK_FX_A, 384, 0);
        if (t >= 24 && t < 34 && (t & 1)) anim.mon_dy[side] -= 2;
        if (t >= 20 && t < 34) ring3(bx, 0, bz, 6 + (t - 20) * 3, FXB_WAVE, OBANK_FX_A, 0, 1);
        if (impact_when(20, st + 1, dx - dir * 8, dy)) feel.zoom = 18;
        break;
    }
    /* ---------------- expansion kinds ---------------- */
    case AK_RATTLE: {
        /* bones gather on a tilted orbit round the foe, tumbling and
         * jittering, then clatter in */
        anim.mon_dx[side] = t < 24 ? ((t & 2) ? 1 : -1) : 0;
        if (t < 30) {
            int r = t < 8 ? 40 - t : 32;
            if (t >= 22) r = 32 - 32 * ease_in(t - 22, 8) / 256;
            int cx = bx, cz = bz;
            for (int i = 0; i < n; i++) {
                if (t < 6 && ((t + i) & 1)) continue;          /* flicker in */
                int a = i * 256 / n + t * 5;
                int jx = ((t + i) & 2) ? 2 : -2, jy = ((t + i * 3) & 4) ? 1 : -1;
                fx3t(cx + (a3_cos(a) * r >> 8) + jx, bh + (a3_sin(a) * r >> 9) + jy, cz + (a3_sin(a) * r >> 8), fx,
                     (i & 1) ? OBANK_FX_B : OBANK_FX_A, tumble(t * 12 + i * 50, 80), 256, t * 20 + i * 50, foe);
            }
        }
        if (t > 12 && t < 30) anim.mon_dx[foe] = (t & 2) ? 1 : -1;
        if (impact_when(30, st, dx, dy))
            burst3(foe, 0, bh, 0, n, 24, 20, fx, OBANK_FX_A, 22, 3, P3_BOUNCE | P3_TUMBLE);
        if (t >= 30 && t < 36) fx_spr(dx, dy, fx2, OBANK_FX_HIT);
        break;
    }
    case AK_MIST: {
        /* a cold fog bank rolls along the ground to the foe (bigger near the
         * camera) and rises round it */
        for (int i = 0; i < n; i++) {
            int pt = t - i * 3;
            if (pt < 0 || pt >= 52) continue;
            int k = ease_out(pt < 26 ? pt : 26, 26);
            int lat = ((i * 19) % 36) - 18;
            int x = ax + ((ux * k) >> 8) - lat * uz / 169, z = az + ((uz * k) >> 8) + lat * ux / 169;
            int y = 6 + ((i * 7) % 8);
            if (pt > 26) {
                int a = pt * 8 + i * 60;
                x = bx + (a3_cos(a) * (18 + lat / 2) >> 8);
                z = bz + (a3_sin(a) * (16 + lat / 3) >> 8);
                y += (pt - 26) * (1 + (i % 3));
            }
            int sc = 320 + soft_sin(pt * 8 + i * 40) / 2;
            if (pt > 44) sc -= (pt - 44) * 24;
            fx3(x, y, z, fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A, sc, 0, foe);
        }
        if (t > 30 && t < 54 && (t & 3) == 0)
            p3_add(bx + fx_rand(40) - 20, bh + 20, bz + fx_rand(30) - 15, 0, -5, 0, fx2, OBANK_FX_B, 16, 0, 5, P3_TUMBLE);
        impact_when(30, st, dx, dy);
        if (t > 30 && t < 56) {
            anim.tint_amount = 7;
            anim.mon_dx[foe] = (t & 2) ? 1 : -1;
        }
        anim.bg_amount = t > 6 && t < 56 ? tint_amt : 0;
        break;
    }
    case AK_SHROUD: {
        /* grave mist spirals up the user (behind it on the far turns) and
         * wraps it */
        anim.tint_side = side;
        for (int i = 0; i < n; i++) {
            int pt = t - i * 4;
            if (pt < 0 || pt >= 44) continue;
            int a = pt * 10 + i * 256 / n;
            int r = 34 - pt * 18 / 44;
            fx3(ax + (a3_cos(a) * r >> 8), 2 + pt * 3 / 2, az + (a3_sin(a) * r >> 8), (pt & 8) ? fx : fx2,
                (i & 1) ? OBANK_FX_B : OBANK_FX_A, 224 + pt * 3, 0, side);
        }
        if (t > 24 && t < 50 && (t & 1)) fx_spr_aff(sx, sy - 4, fx2, OBANK_FX_A, 448 + soft_sin(t * 8) / 2, 0);
        anim.tint_amount = t < 40 ? t / 4 : t < 52 ? (52 - t) * 10 / 12 : 0;
        anim.bg_amount = t < 54 ? tint_amt / 2 : 0;
        self_pulse_when(36);
        break;
    }
    case AK_TOLL: {
        /* a bell comes down over the foe and swings; every toll sends a ring
         * through the air and a ripple along the ground */
        int by = dy - 26 - (t < 10 ? (10 - t) * 4 : 0);
        int sw = t >= 10 ? soft_sin((t - 10) * 8) / 3 : 0;
        if (t < anim.dur - 6) fx_spr_aff(dx + sw / 3, by, fx, OBANK_FX_A, 384, sw);
        for (int i = 0; i < n; i++) {
            int t0 = 18 + i * 16, pt = t - t0;
            if (t == t0) sfx_play(SFX_KNELL);
            if (pt >= 0 && pt < 18) {
                big_spr(dx, by + 8 + pt, FXB_RING, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 96 + pt * 22, 64 + pt * 12);
                ring3(bx, 0, bz, 8 + pt * 2, FXB_WAVE, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 0, 1);
            }
            if (pt >= 0 && pt < 3) anim.bright = -4;
            impact_when(t0 + 2, i == n - 1 ? st : 0, dx, dy);
        }
        anim.bg_amount = t < anim.dur - 4 ? tint_amt : 0;
        anim.tint_amount = t > 18 ? 5 + ((t & 8) ? 3 : 0) : 0;
        break;
    }
    case AK_CHOIR: {
        /* spirits rise from the ground in a ring round the foe (the far ones
         * behind it), sway and sing, then converge */
        anim.bg_color = RGB15(4, 3, 8);
        anim.bg_amount = t < 70 ? (t < 12 ? t : 12) : 0;
        for (int i = 0; i < n; i++) {
            int a = i * 256 / n + t;
            int pt = t - 4 - i * 3;
            if (pt < 0 || t >= 62) continue;
            int r = 34, y;
            if (t < 50) {
                y = (ease_out(pt < 16 ? pt : 16, 16) * 34 >> 8) + (a3_sin(pt * 10 + i * 60) >> 6);
            } else {
                int k = ease_in(t - 50, 12);
                r = 34 - (34 * k >> 8);
                y = 34 + ((bh - 34) * k >> 8);
            }
            int x = bx + (a3_cos(a) * r >> 8), z = bz + (a3_sin(a) * r >> 8);
            fx3(x, y, z, fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 256, a3_sin(pt * 6 + i * 40) >> 5, foe);
            if (t > 20 && t < 50 && (t + i * 5) % 12 == 0)
                p3_add(x, y + 10, z, (i & 1) ? 4 : -4, 8, 0, fx2, OBANK_FX_B, 16, 0, 0, 0);
        }
        impact_when(62, st, dx, dy);
        if (t >= 62 && t < 74) {
            big_draw(dx, dy, FXB_FLARE, OBANK_FX_A, 128 + (t - 62) * 24, 128 + (t - 62) * 24, t * 3, 0, 0);
            ring3(bx, 0, bz, (t - 62) * 3, FXB_WAVE, OBANK_FX_B, 0, 1);
        }
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
                burst3(foe, 0, bh, -10, 3, 18, 30, fx, OBANK_FX_B, 24, 4, P3_BOUNCE | P3_TUMBLE);
            if (bt >= 11 && bt < 22) ring3(bx, 0, bz, 6 + (bt - 11) * 2, FXB_WAVE, OBANK_FX_B, 0, 1);
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
        /* a tornado stands on the foe: a funnel of things spinning round it
         * (behind it on the far side), a vortex turning on the ground */
        int pair = fx == FX_FLAME_A;
        for (int i = 0; i < n; i++) {
            int pt = t - i * 2;
            if (pt < 0 || pt >= 56) continue;
            int a = pt * 12 + i * 256 / n;
            int h = (i * 37 + pt * 2) % 56;
            int r0 = 10 + h / 3 + (i % 3) * 3;
            int r = pt < 40 ? r0 + pt / 5 : (r0 + 8) * (56 - pt) / 16;
            int f = pair ? fx_frame(fx, fx2, pt + i) : (i & 1) ? fx2 : fx;
            fx3(bx + (a3_cos(a) * r >> 8), 4 + h, bz + (a3_sin(a) * r >> 8), f, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 240,
                pair ? 0 : pt * 16, foe);
        }
        if (t > 4 && t < 54) ring3(bx, 0, bz, 20, FXB_VORTEX, OBANK_FX_B, -t * 12, 1);
        if (!pair && t > 6 && t < 50)
            for (int k = 0; k < 2; k++) {
                int a = t * 12 + k * 128;
                fx3t(bx + (a3_cos(a) * 26 >> 8), 14 + k * 22, bz + (a3_sin(a) * 26 >> 8), FX_WIND, OBANK_FX_A,
                     a3_sin(a) < 0 ? -256 : 256, 256, 0, foe);
            }
        if (t > 10 && t < 56) anim.mon_dx[foe] = soft_sin(t * 16) / 20;
        impact_when(24, 0, dx, dy);
        impact_when(52, st, dx, dy);
        anim.bg_amount = t < 58 ? tint_amt : 0;
        if (pair && t > 8 && t < 56) anim.wobble = 2;
        break;
    }
    case AK_MAGNET: {
        /* a horseshoe magnet hauls the foe; field loops pulse between them and
         * iron flakes fly over, tumbling */
        int mx = sx + dir * 22, my = sy - 18;
        int in = t < 8 ? ease_out(t, 8) : t > 52 ? 256 - (t - 52) * 32 : 256;
        if (in > 0)
            fx_spr_aff(mx, my + ((t >> 3) & 1), fx, ((t & 4) && t > 12) ? OBANK_FX_B : OBANK_FX_A, 128 + in / 2,
                       dir > 0 ? 192 : 64);
        for (int k = 0; k < n; k++) {
            if (t < 10 || t > 50) break;
            int pt = (t + k * 8) % 24;
            big_draw(dx + (mx - dx) * pt / 24, dy + (my - dy) * pt / 24, FXB_RING, OBANK_FX_B, 48 + (24 - pt) * 4,
                     96 + (24 - pt) * 5, a3_atan2(my - dy, mx - dx), 1, 0);
        }
        for (int i = 0; i < 6; i++) {
            int pt = t - 12 - i * 5;
            if (pt < 0 || pt >= 20) continue;
            int k = ease_in(pt, 20), x, y, z;
            w3_path(foe, side, k, 20, &x, &y, &z);
            x += (((i * 23) % 30) - 15) * (256 - k) >> 8;
            z += (((i * 13) % 24) - 12) * (256 - k) >> 8;
            fx3t(x, y, z, fx2, OBANK_FX_B, tumble(pt * 20 + i * 40, 64), 256, pt * 20, -1);
        }
        int pull = t < 14 ? 0 : t < 46 ? 8 * ease_out(t - 14, 10) / 256 : 8 - 8 * ease_out(t - 46, 10) / 256;
        anim.mon_dx[foe] = -dir * pull;
        anim.scale_x[foe] = 256 + pull * 3;
        impact_when(30, 0, dx, dy);
        anim.tint_amount = t > 14 && t < 50 ? 6 : 0;
        break;
    }
    case AK_GEARS: {
        /* two big gears roll in from both sides like wheels seen at an angle
         * (turning in their own plane) and grind */
        int off = t < 12 ? 56 - 40 * ease_out(t, 12) / 256 : t < 44 ? 16 : 16 + (t - 44) * 4;
        if (t < 52) {
            fx_flat(dx - off, dy, fx, OBANK_FX_A, 250, 400, t * 12);
            fx_flat(dx + off, dy, fx, OBANK_FX_B, 250, 400, -t * 12 + 16);
        }
        if (t >= 12 && t < 44) {
            anim.mon_dy[foe] = (t & 2) ? 1 : -1;
            anim.scale_x[foe] = 236;
            shake(12, 0);
            if ((t % 3) == 0)
                p3_add(bx + ((t & 4) ? 10 : -10), bh, bz - 6, ((t & 4) ? 1 : -1) * (10 + fx_rand(10)), 20 + fx_rand(10),
                       fx_rand(20) - 10, fx2, OBANK_FX_B, 14, 3, 0, P3_BOUNCE);
        }
        for (int i = 0; i < n; i++) impact_when(14 + i * 14, i == n - 1 ? st : 0, dx, dy);
        break;
    }
    case AK_ANVIL: {
        /* a shadow swells under the foe, then an anvil drops: squash, a
         * shockwave, dust rolling out, stars */
        if (t < 26) shadow3(bx, bz, 240 + t * 10, (26 - t) * 6);
        int ay = t < 14 ? -40 : t < 26 ? -40 + (dy - 12 + 40) * ease_in(t - 14, 12) / 256 :
                 dy - 12 - (t < 30 ? (30 - t) / 2 : 0);
        if (t >= 14 && (t < 44 || (t < 52 && (t & 1)))) big_spr(dx, ay, FXB_ANVIL, OBANK_FX_A, 288, 288);
        if (t >= 16 && t < 26)
            for (int k = -1; k <= 1; k += 2) fx_spr_aff(dx + k * 14, ay - 22, FX_SPEEDLINE, OBANK_FX_B, 256, 64);
        if (impact_when(26, st + 1, dx, dy)) {
            shake(96, 1);
            feel.zoom = 20;
            for (int k = 0; k < 10; k++)
                p3_add(bx, 3, bz, a3_cos(k * 26) * 3 >> 4, 3, a3_sin(k * 26) * 3 >> 4, fx, OBANK_FX_A, 18, 0, 0,
                       P3_SHRINK);
        }
        if (t >= 26 && t < 40) ring3(bx, 0, bz, 8 + (t - 26) * 3, FXB_WAVE, OBANK_FX_B, 0, 1);
        if (t >= 26 && t < 44) {
            anim.scale_x[foe] = 256 + 48 * (44 - t) / 18;
            anim.scale_y[foe] = 256 - 64 * (44 - t) / 18;
            anim.mon_dy[foe] = 8 * (44 - t) / 18;
        }
        if (t >= 32 && t < 62) orbit3(foe, bh + 22, 18, 0, t * 10, 3, fx2, fx2, 200, 0);
        break;
    }
    case AK_MOONLIT: {
        /* night falls, the moon rises, a pale shaft falls on the foe and pools
         * on the ground, then drains back up to the user */
        anim.bg_color = RGB15(2, 3, 10);
        anim.bg_amount = t < 64 ? (t < 12 ? t : 12) : 0;
        int mx = dx - 52, my = t < 20 ? 40 - ease_out(t, 20) * 26 / 256 : 14;
        if (t < 66) {
            fx_spr_aff(mx, my, fx, OBANK_FX_A, 384, 0);
            if (t > 18 && (t & 8)) fx_spr_aff(mx, my, FX_GLOW, OBANK_FX_B, 512, 0);
        }
        if (t >= 20 && t < 48) {
            int h = ease_in(t - 20, 8) * (dy + 16) / 256;
            for (int y = 0; y < h; y += 16)
                fx_spr_aff2(dx, y, fx2, (y & 16) ? OBANK_FX_B : OBANK_FX_A, 320 + ((t & 2) ? 32 : 0), 256, 0);
            if (h >= dy) ring3(bx, 0, bz, 18, FXB_RING, OBANK_FX_B, t * 2, 1);
            anim.tint_amount = 9;
        }
        impact_when(26, st, dx, dy);
        for (int i = 0; i < n; i++) {
            int pt = t - 40 - i * 4;
            if (pt < 0 || pt >= 20) continue;
            int x, y, z;
            w3_path(foe, side, ease_in(pt, 20), 40, &x, &y, &z);
            int a = pt * 20 + i * 51;
            fx3(x + (a3_cos(a) >> 5), y + (a3_sin(a) >> 5), z, FX_SPARKLE, OBANK_FX_B, 256, 0, -1);
        }
        if (t == 40) sfx_play(SFX_DRAIN);
        if (t >= 56) {
            anim.tint_side = side;
            anim.tint_amount = 7;
        }
        break;
    }
    case AK_MUON: {
        /* thin streaks of light rain straight through everything, near ones
         * big and fast, far ones small; each sparks on the ground */
        anim.bg_amount = t < 54 ? tint_amt : 0;
        for (int i = 0; i < n; i++) {
            int pt = t - 4 - (i * 11) % 36;
            if (pt < 0 || pt >= 16) continue;
            int z = 200 + (i * 61) % 260, x = -110 + (i * 53 + 17) % 280;
            int y = 190 - pt * 16;
            if (y < 0) {
                ring3(x, 0, z, 4 + (-y >> 2), FXB_WAVE, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 0, 1);
                continue;
            }
            fx3(x + pt, y, z, fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 256, 0, -1);
            fx3(x + pt - 1, y + 20, z, fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 224, 0, -1);
        }
        if (t > 16 && t < 48 && (t & 3) == 0)
            p3_add(bx + fx_rand(44) - 22, bh + fx_rand(30) - 15, bz + fx_rand(30) - 15, 0, 0, 0, fx2, OBANK_FX_B, 8, 0,
                   16, 0);
        impact_when(20, 0, dx, dy);
        impact_when(36, st, dx, dy);
        anim.tint_amount = t > 16 && t < 48 && (t & 2) ? 10 : 0;
        break;
    }
    case AK_METEOR: {
        /* one huge meteor falls out of the far sky (growing as it nears), its
         * shadow swells; flash, crater ring, debris bouncing */
        anim.bg_color = t < 24 ? RGB15(4, 2, 8) : TYPE_TINT[anim.type];
        anim.bg_amount = t < 22 ? t / 2 : t < 60 ? tint_amt : 0;
        if (t < 24) {
            int k = ease_in(t, 24);
            int x = bx + 150 - (150 * k >> 8), y = bh + 220 - ((220) * k >> 8), z = bz + 260 - (260 * k >> 8);
            fx3(x, y, z, fx, OBANK_FX_A, 360, 0, -1);
            if (t & 1) p3_add(x + 10, y + 10, z + 10, 8, 6, 8, FX_EMBER, OBANK_FX_A, 12, 0, 0, P3_SHRINK);
            shadow3(bx, bz, 200 + t * 14, 0);
            shake(t * 2, 1);
        }
        if (t >= 24 && t < 27) anim.bright = 12;
        if (impact_when(24, st + 1, dx, dy)) {
            shake(104, 1);
            feel.zoom = 24;
            burst3(foe, 0, 6, 0, 7, 30, 30, fx2, OBANK_FX_B, 26, 4, P3_BOUNCE);
            burst3(foe, 0, 6, 0, 4, 20, 20, FX_EMBER, OBANK_FX_A, 16, 3, P3_SHRINK);
        }
        if (t >= 24 && t < 40) big_spr(dx, dy, FXB_GLOW, OBANK_FX_A, 128 + (t - 24) * 20, 128 + (t - 24) * 20);
        if (t >= 24 && t < 42) ring3(bx, 0, bz, 8 + (t - 24) * 2, FXB_WAVE, OBANK_FX_A, 0, 1);
        if (t >= 24 && t < 60 && (t < 52 || (t & 1)))
            fx_spr_aff2(dx, side_gy(foe) - 4, FX_CRACK, OBANK_FX_B, 448, 192, 0);
        anim.tint_amount = t >= 24 && t < 50 ? 8 : 0;
        break;
    }
    case AK_NOVA: {
        /* gathers starlight from a whole sphere round it, the world goes dark,
         * then a blinding burst: a shell of stars flies out in 3D, rings roll */
        int rel = 40;
        anim.bg_color = RGB15(1, 1, 4);
        if (t < rel) {
            if (t == 2) sfx_play(SFX_CHARGE);
            for (int i = 0; i < n; i++) {
                int pt = (t * 2 + i * 9) % 26;
                int a = i * 32 + t * 2, e = (i * 41) % 128 - 64;
                int r = 56 - pt * 56 / 26, ce = a3_cos(e) * r >> 8;
                fx3(ax + (a3_cos(a) * ce >> 8), ah + (a3_sin(e) * r >> 8), az + (a3_sin(a) * ce >> 8), (i & 1) ? fx2 : fx,
                    (i & 1) ? OBANK_FX_B : OBANK_FX_A, 256, 0, side);
            }
            ring3(ax, 0, az, 24 - t / 3, FXB_RING, OBANK_FX_A, t * 4, 1);
            anim.tint_side = side;
            anim.tint_amount = t * 10 / rel;
            anim.bg_amount = t * 14 / rel;
            anim.scale_x[side] = anim.scale_y[side] = 256 + t / 2;
            anim.mon_dx[side] = t > 24 ? ((t & 1) ? 1 : -1) : 0;
        } else {
            int it = t - rel;
            anim.bg_amount = it < 36 ? 14 : 0;
            if (it < 6) {
                int x, y, z;
                w3_path(side, foe, it * 42, 20, &x, &y, &z);
                fx3(x, y, z, fx, OBANK_FX_A, 384, it * 20, -1);
            } else if (it < 36) {
                int g = it - 6;
                int gs = 128 + g * 16 > 512 ? 512 : 128 + g * 16;
                big_draw(dx, dy, FXB_FLARE, OBANK_FX_A, gs, gs, g * 3, 0, 0);
                if (g < 20) ring3(bx, 0, bz, g * 2, FXB_WAVE, OBANK_FX_B, 0, 1);
                for (int i = 0; i < n; i++) {
                    int a = i * 256 / n + g * 2, e = (i * 53) % 128 - 64;
                    int r = g * 4, ce = a3_cos(e) * r >> 8;
                    fx3(bx + (a3_cos(a) * ce >> 8), bh + (a3_sin(e) * r >> 8), bz + (a3_sin(a) * ce >> 8), fx,
                        (i & 1) ? OBANK_FX_B : OBANK_FX_A, 256, g * 12, foe);
                }
            }
            anim.bright = it >= 6 && it < 14 ? 16 - (it - 6) * 2 : 0;
            if (it == 6) sfx_play(SFX_THUNDER);
            shake(it >= 6 && it < 20 ? 80 : 0, 0);
            if (impact_when(rel + 6, st + 1, dx, dy)) feel.zoom = 24;
            anim.tint_side = foe;
            anim.tint_amount = it > 6 ? 10 : 0;
        }
        break;
    }
    case AK_ARC: {
        /* a jagged arc jumps from the user to the foe; both ends flash rings
         * on the ground and spit sparks */
        anim.bg_color = RGB15(4, 4, 12);
        anim.bg_amount = t < 44 ? 6 : 0;
        if (t < 10 && (t & 1)) fx_spr(sx + tri_sin(t * 40) / 4, sy - 8 + tri_sin(t * 40 + 64) / 5, fx2, OBANK_FX_B);
        for (int k = 0; k < n; k++) {
            int t0 = 10 + k * 12, at = t - t0;
            if (at == 0 && k) sfx_play(SFX_ZAP);
            if (at >= 0 && at < 2) anim.bright = 8;
            if (impact_when(t0 + 1, k == n - 1 ? st : 0, dx, dy))
                burst3(foe, 0, bh, -6, 4, 26, 12, FX_SPARK_A, OBANK_FX_A, 12, 3, P3_SHRINK);
            if (at >= 0 && at < 12) {
                ring3(ax, 0, az, 6 + at * 2, FXB_WAVE, OBANK_FX_B, at * 20, 1);
                ring3(bx, 0, bz, 6 + at * 2, FXB_WAVE, OBANK_FX_A, -at * 20, 1);
            }
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
        /* the user sways and turns round (its sprite flips edge-on and back);
         * scales spiral up round it on a helix */
        anim.tint_side = side;
        anim.mon_dx[side] = soft_sin(t * 8) / 8;
        anim.mon_dy[side] = -absi(soft_sin(t * 16)) / 16;
        if (t >= 16 && t < 40) {
            int c = a3_cos((t - 16) * 256 / 24);
            if (c > -48 && c < 48) c = c < 0 ? -48 : 48;
            anim.scale_x[side] = c;
        }
        ring3(ax, 0, az, 22, FXB_RING, OBANK_FX_B, t * 6, 1);
        for (int i = 0; i < n; i++) {
            int pt = (t + i * 8) % 40;
            if (t > 52 && pt < 12) continue;
            int a = pt * 14 + i * 256 / n;
            int r = 32 - pt / 2;
            fx3(ax + (a3_cos(a) * r >> 8), 2 + pt * 2, az + (a3_sin(a) * r >> 8), fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A,
                256, a, side);
        }
        if (t > 40 && (t & 4)) fx_spr(sx, sy - 26, fx2, OBANK_FX_B);
        anim.tint_amount = 5 + tri_sin(t * 8) / 16;
        self_pulse_when(44);
        break;
    }
    /* ---------------- pseudo-3D kinds ---------------- */
    case AK_VOLLEY: {
        /* a volley lobbed in a spread: each shot spins on its own arc with a
         * shadow under it, strikes, then bounces off and rattles to the
         * ground */
        int travel = 16, gap = 4, windup = 5;
        if (t < windup) anim.scale_y[side] = 256 + t * 6;
        for (int i = 0; i < n; i++) {
            int pt = t - windup - i * gap;
            if (pt < 0) continue;
            int seed = anim.variant * 3 + i;
            int jx = (seed * 11) % 21 - 10, jz = (seed * 7) % 17 - 8, jy = (seed * 5) % 13 - 6;
            if (pt < travel) {
                int k = pt * 256 / travel, x, y, z;
                w3_path(side, foe, k, 34 + (seed % 3) * 14, &x, &y, &z);
                x += (jx * k) >> 8;
                z += ((jz - 10) * k) >> 8;
                y += (jy * k) >> 8;
                fx3(x, y, z, fx_frame(fx, fx2, pt), OBANK_FX_A, 256, pt * 20 * ((seed & 1) ? 1 : -1), -1);
                shadow3(x, z, 180, y);
                if (fx == FX_RIVET && (pt & 1)) p3_add(x, y, z, 0, 2, 0, fx2, OBANK_FX_B, 6, 0, 0, P3_SHRINK);
            } else if (pt == travel) {
                int px, py;
                w3_proj(bx + jx, bh + jy, bz - 10, &px, &py);
                impact_when(windup + i * gap + travel, i == n - 1 ? st : 0, px, py);
                p3_add(bx + jx, bh + jy, bz - 12, -ux / 14 + (jx << 1), 24, -uz / 14 - 10, fx, OBANK_FX_A, 34, 4,
                           (seed & 1) ? 18 : -18, P3_BOUNCE | P3_SHADOW);
            } else if (pt < travel + 6) {
                fx_spr_aff(dx + jx, dy - jy, FX_IMPACT_SMALL, OBANK_FX_HIT, 320 - (pt - travel) * 30, pt * 16);
            }
        }
        break;
    }
    case AK_LOB: {
        /* a heavy blob lobbed high, wobbling as it turns; its shadow slides
         * and swells under it; it lands in a crown of spray, goo flies and
         * bounces, the foe squashes */
        int travel = 26, t0 = 6;
        if (t < t0) {
            anim.scale_x[side] = 256 + t * 6;
            anim.scale_y[side] = 256 - t * 5;
        } else if (t < t0 + 6) {
            anim.mon_dy[side] = -(t0 + 6 - t);
        }
        int pt = t - t0;
        if (pt >= 0 && pt < travel) {
            int k = pt * 256 / travel, x, y, z;
            w3_path(side, foe, k, 150, &x, &y, &z);
            int wob = a3_sin(pt * 28) >> 3;
            fx3t(x, y, z, fx, OBANK_FX_A, 300 + wob, 300 - wob, pt * 6, -1);
            if (pt & 1) p3_add(x, y, z, 0, 0, 0, fx2 == FX_SPLAT ? FX_GLOB : fx2, OBANK_FX_B, 6, 0, 0, P3_SHRINK);
            shadow3(x, z, 280, y);
        }
        if (impact_when(t0 + travel, st, dx, dy)) {
            burst3(foe, 0, bh - 10, -8, 8, 30, 26, FX_GLOB, OBANK_FX_A, 30, 4, P3_BOUNCE);
            feel.zoom = 12;
        }
        int it = pt - travel;
        if (it >= 0 && it < 20) {
            fx3_at(foe, 0, 4, -8, FX_SPLASH, OBANK_FX_A, 300 + it * 12, 0);
            ring3(bx, 0, bz, 8 + it * 2, FXB_WAVE, OBANK_FX_B, 0, 1);
            if (it < 10) fx_spr_aff(dx, dy, fx2, OBANK_FX_A, 256 + it * 24, 0);
            anim.scale_x[foe] = 256 + (20 - it) * 3;
            anim.scale_y[foe] = 256 - (20 - it) * 3;
        }
        if (it >= 8 && it < 30 && (it & 3) == 0)                   /* drips */
            p3_add(bx + fx_rand(30) - 15, bh + 10, bz - 10, 0, 0, 0, FX_DROP, OBANK_FX_B, 16, 3, 0, 0);
        if (it >= 0 && it < 30) anim.tint_amount = 6;
        anim.bg_amount = big && t > 10 && t < anim.dur - 6 ? tint_amt : 0;
        break;
    }
    case AK_LANCE: {
        /* darts shot straight and fast, pointing along their flight and
         * rifling (turning about their own axis); they pierce the foe and
         * carry on out behind it, leaving glitter in the air */
        int travel = 11, gap = 6, windup = 5;
        if (t < windup) anim.mon_dx[side] = -dir * t;
        int head = a3_atan2(dy - sy, dx - sx);
        for (int i = 0; i < n; i++) {
            int pt = t - windup - i * gap;
            if (pt < 0 || pt >= travel + 10) continue;
            int jy = (i & 1) ? 6 : -4, jl = (i * 5) % 11 - 5;
            int k = pt * 256 / travel, x, y, z;
            w3_path(side, foe, k, 0, &x, &y, &z);
            x -= jl * uz / 169;
            z += jl * ux / 169;
            y += jy;
            fx3t(x, y, z, fx, OBANK_FX_A, 300, tumble(pt * 48, 88), head, k > 280 ? foe : -1);
            if (pt < travel && (pt & 1)) p3_add(x, y, z, 0, 1, 0, fx2, OBANK_FX_B, 12, 0, 12, P3_SHRINK);
            if (pt == travel) {
                int px, py;
                w3_proj(x, y, z, &px, &py);
                impact_when(windup + i * gap + travel, i == n - 1 ? st : 0, px, py);
                burst3(foe, 0, bh + jy, -4, 4, 20, 8, fx2, OBANK_FX_B, 12, 2, P3_SHRINK);
            }
            if (pt >= travel && pt < travel + 5)
                big_draw(dx, dy + jy / 2, FXB_FLARE, OBANK_FX_HIT, 200 - (pt - travel) * 30, 200 - (pt - travel) * 30,
                         head, 0, 0);
        }
        if (fx == FX_SHARD && t > 14) anim.tint_amount = t < 40 ? 6 : 0;
        break;
    }
    case AK_BUBBLES: {
        /* bubbles drift over in a loose, wobbling stream (bigger near the
         * camera), gather round the foe in front and behind, then pop one by
         * one in little rings */
        for (int i = 0; i < n + 4; i++) {
            int pt = t - 2 - i * 3;
            if (pt < 0) continue;
            int pop = 30 + (i * 5) % 12;
            int x, y, z;
            if (pt < 22) {
                w3_path(side, foe, ease_out(pt, 22), 20 + (i & 3) * 10, &x, &y, &z);
            } else {
                x = bx, y = bh, z = bz;
            }
            int a = i * 67 + pt * 6;
            int spread = pt < 22 ? pt : 22;
            x += (a3_cos(a) * spread) >> 8;
            z += (a3_sin(a * 2 + i) * spread) >> 8;
            y += (a3_sin(pt * 10 + i * 40) * 6 >> 8) + ((i * 7) % 13 - 6) * spread / 22;
            if (pt < pop) {
                int w = a3_sin(pt * 16 + i * 30) >> 4;
                fx3t(x, y, z, (i & 3) == 3 ? fx2 : fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 224 + w + (i & 3) * 16,
                     224 - w + (i & 3) * 16, 0, foe);
            } else if (pt < pop + 6) {
                fx3(x, y, z, FX_RING, OBANK_FX_B, 200 + (pt - pop) * 40, 0, foe);
                if (pt == pop) {
                    int px, py;
                    w3_proj(x, y, z, &px, &py);
                    if (i < n) impact_when(t, i == n - 1 ? st : 0, px, py);
                    p3_add(x, y, z, fx_rand(20) - 10, 12, fx_rand(20) - 10, FX_DROP, OBANK_FX_B, 12, 3, 0, P3_SHRINK);
                }
            }
        }
        if (t > 30) anim.tint_amount = (t & 4) ? 6 : 3;
        break;
    }
    case AK_FIRESTORM: {
        /* embers swirl up round the foe in a widening double helix (behind it
         * on the far turns), a ring of fire turns on the ground, then a
         * column of flame roars up and embers rain down */
        int k = t < 12 ? t * 21 : t > 60 ? (72 - t) * 21 : 256;
        if (k > 0) ring3(bx, 0, bz, (k * 24) >> 8, FXB_VORTEX, OBANK_FX_A, t * 10, 1);
        for (int i = 0; i < n + 4; i++) {
            int pt = (t * 3 + i * 17) % 64;
            if (t > 58 && pt < 20) continue;
            int a = t * 14 + i * 256 / (n + 4) * ((i & 1) ? 1 : -1);
            int r = 14 + pt / 3;
            int f = (i & 2) ? FX_EMBER : fx_frame(fx, fx2, t + i);
            fx3(bx + (a3_cos(a) * r >> 8), pt, bz + (a3_sin(a) * r >> 8), f, (i & 1) ? OBANK_FX_B : OBANK_FX_A,
                224 - pt, 0, foe);
        }
        if (t >= 34 && t < 58) {                         /* the column */
            int h = ease_out(t - 34, 8) * 90 >> 8;
            for (int y = 0; y < h; y += 14)
                fx3(bx + (a3_sin(t * 20 + y * 5) >> 6), y, bz - 6, fx_frame(fx, fx2, t + y / 14),
                    (y / 14) & 1 ? OBANK_FX_B : OBANK_FX_A, 320, 0, -1);
            anim.bright = t < 37 ? 5 : 0;
        }
        if (t >= 40 && t < 64 && (t & 1))
            p3_add(bx + fx_rand(50) - 25, 90, bz + fx_rand(40) - 20, fx_rand(10) - 5, -6, 0, FX_EMBER, OBANK_FX_B, 24,
                   1, 0, P3_BOUNCE | P3_SHRINK);
        impact_when(24, 0, dx, dy);
        impact_when(36, st, dx, dy);
        anim.tint_amount = t > 20 && t < 64 ? 8 : 0;
        anim.bg_amount = t < 68 ? tint_amt : 0;
        if (t > 8 && t < 64) anim.wobble = 2;
        break;
    }
    case AK_WHIRLPOOL: {
        /* a whirlpool opens on the ground under the foe and turns ever
         * faster; the foe spins round and is dragged down, spray arms whirl
         * round it; then it bursts up in spray */
        int grow = t < 14 ? t * 18 : t > 58 ? (70 - t) * 20 : 256;
        if (grow > 0) {
            int spin = -(t * t) / 6;
            ring3(bx, 0, bz, (grow * 26) >> 8, FXB_VORTEX, OBANK_FX_A, spin, 1);
            ring3(bx, 0, bz, (grow * 14) >> 8, FXB_VORTEX, OBANK_FX_B, spin * 2 + 40, 1);
        }
        if (t >= 10 && t < 56)
            for (int i = 0; i < n + 2; i++) {
                int a = -t * (8 + t / 8) + i * 256 / (n + 2);
                int r = 30 - ((t - 10) >> 2);
                fx3t(bx + (a3_cos(a) * r >> 8), 4 + ((i * 7) & 7), bz + (a3_sin(a) * r >> 8), (i & 1) ? fx2 : FX_SWIRL,
                     (i & 1) ? OBANK_FX_B : OBANK_FX_A, 240, 180, a + 64, foe);
            }
        if (t >= 16 && t < 56) {
            int c = a3_cos((t - 16) * (8 + (t - 16) / 3));   /* spinning round, faster */
            anim.scale_x[foe] = absi(c) < 40 ? (c < 0 ? -40 : 40) : c;
            anim.mon_dy[foe] = (t - 16) * 10 / 40;
            if ((t & 3) == 0) p3_add(bx + fx_rand(30) - 15, 2, bz + fx_rand(20) - 10, 0, 12, 0, FX_BUBBLE, OBANK_FX_B,
                                     14, 0, 0, P3_SHRINK);
        }
        if (impact_when(56, st, dx, dy)) burst3(foe, 0, 8, 0, 8, 34, 30, FX_DROP, OBANK_FX_A, 26, 4, P3_BOUNCE);
        if (t >= 56 && t < 66) fx3_at(foe, 0, 2, -6, FX_SPLASH, OBANK_FX_A, 320 + (t - 56) * 20, 0);
        impact_when(30, 0, dx, dy);
        anim.tint_amount = t > 16 && t < 60 ? 5 : 0;
        anim.bg_amount = t > 6 && t < 66 ? tint_amt : 0;
        break;
    }
    case AK_CRESCENT: {
        /* spinning crescent blades thrown on curving paths (from opposite
         * sides when there are two, crossing in an X), tilted like discs; the
         * cuts cross on the foe and scatter leaves / feathers */
        int travel = 18;
        for (int i = 0; i < n; i++) {
            int pt = t - 6 - i * 4;
            if (pt < 0 || pt >= travel + 8) continue;
            int side_k = (i & 1) ? -1 : 1;
            if (pt < travel) {
                int k = pt * 256 / travel, x, y, z;
                w3_path(side, foe, k, 10, &x, &y, &z);
                int bow = a3_sin(k / 2) * 44 >> 8;           /* swings out sideways, then in */
                x -= side_k * bow * uz / 169;
                z += side_k * bow * ux / 169;
                y += side_k * (a3_sin(k / 2) * 14 >> 8);
                int spin = pt * 28 * side_k;
                fx3t(x, y, z, fx, OBANK_FX_A, 300, 180 + (a3_sin(pt * 12) >> 3), spin, -1);
                if (pt > 1) {
                    int x2, y2, z2;
                    w3_path(side, foe, k - 24 < 0 ? 0 : k - 24, 10, &x2, &y2, &z2);
                    fx3t(x2 - side_k * bow * uz / 169, y2, z2 + side_k * bow * ux / 169, fx, OBANK_FX_B, 240, 150,
                         spin - 28 * side_k, -1);
                }
            } else {
                int it = pt - travel;
                if (it == 0) {
                    int px, py;
                    w3_proj(bx, bh, bz - 10, &px, &py);
                    impact_when(t, i == n - 1 ? st : 0, px, py);
                    if (fx2 == FX_FEATHER || fx2 == FX_LEAF_A)
                        burst3(foe, 0, bh + 8, -6, 4, 14, 10, fx2, OBANK_FX_B, 34, 1, P3_TUMBLE);
                }
                fx_spr_aff2(dx, dy, FX_SLASH, OBANK_FX_HIT, side_k * (320 - it * 20), 320 - it * 20, 0);
            }
        }
        if (anim.type == T_GALE && t > 6 && t < 30 && (t & 3) == 0)
            p3_add(ax, ah + 10, az, ux / 10, 0, uz / 10, FX_WIND, OBANK_FX_B, 14, 0, 0, P3_SHRINK);
        break;
    }
    case AK_SHIELD: {
        /* plates fly in from all round and lock into a dome over the user
         * (the far plates behind it, dimmer), a glint runs over them, the
         * dome pulses, then fades */
        static const s8 DOME[9][3] = {        /* azimuth (x4), elevation (x4), plate */
            { 0, 3, 0 }, { 16, 3, 0 }, { 32, 3, 0 }, { 48, 3, 0 },
            { 8, 9, 1 }, { 24, 9, 1 }, { 40, 9, 1 }, { 56, 9, 1 }, { 0, 16, 1 },
        };
        int squat = t < 8 ? t : t < 40 ? 8 : 48 - t;
        if (squat < 0) squat = 0;
        anim.scale_x[side] = 256 + squat * 3;
        anim.scale_y[side] = 256 - squat * 3;
        anim.tint_side = side;
        ring3(ax, 0, az, 30, FXB_RING, OBANK_FX_B, t * 2, 1);
        for (int i = 0; i < 9; i++) {
            int in = t - i * 2;
            if (in < 0) continue;
            int k = in < 14 ? ease_out(in, 14) : 256;
            int a = DOME[i][0] * 4 + (t >> 1), e = DOME[i][1] * 4;
            int r = 36 + ((256 - k) * 60 >> 8);
            int ce = a3_cos(e) * r >> 8;
            int x = ax + (a3_cos(a) * ce >> 8), z = az + (a3_sin(a) * ce >> 8), y = 4 + (a3_sin(e) * r * 3 >> 10);
            if (t > 50 && ((t + i) & 1)) continue;             /* fading out */
            int glint = t >= 24 && t < 36 && ((t - 24) >> 1) == (i & 7);
            fx3t(x, y, z, DOME[i][2] ? fx : FX_HEX, glint ? OBANK_FX_HIT : (i & 1) ? OBANK_FX_B : OBANK_FX_A,
                 tumble(a + 64, 96), 256 + (k < 256 ? 0 : (t & 8 ? 16 : 0)), (256 - k) >> 1, side);
        }
        if (t >= 24 && t < 36) fx_spr_aff(sx - 24 + (t - 24) * 4, sy - 16 + (t - 24), FX_SPARKLE, OBANK_FX_HIT, 320, t * 8);
        anim.tint_amount = squat;
        self_pulse_when(14);
        break;
    }
    case AK_GYRE: {
        /* three orbits on different tilts spin round the target like a
         * gyroscope (the far arcs behind it, dim); the rings themselves are
         * drawn as thin tilted ellipses; then they collapse in a flash */
        int self = MOVES[anim.move].cat == CAT_STATUS && MOVES[anim.move].effect == EF_SELF_STAT;
        int tgt = self ? side : foe;
        int cx = w3_side_x(tgt), cz = w3_side_z(tgt), ch = w3_side_h(tgt);
        int r = t < 10 ? 10 + t * 2 : t < 46 ? 30 : 30 - (t - 46) * 2;
        if (r < 0) r = 0;
        int spin = t * 3;
        for (int ring = 0; ring < 3; ring++) {
            int tilt = ring * 85 + spin;                /* each orbit's plane turns about the vertical */
            int ct = a3_cos(tilt), stl = a3_sin(tilt);
            int lean = ring == 0 ? 0 : ring == 1 ? 44 : -44;    /* how far the plane leans (256 = a turn) */
            for (int i = 0; i < n; i++) {
                int a = t * (10 + ring * 3) + i * 256 / n + ring * 40;
                int u = a3_cos(a) * r >> 8, v = a3_sin(a) * r >> 8;
                /* the circle (u, v) in a plane leaning `lean` about the axis at angle tilt */
                int hz = v * a3_cos(lean) >> 8, hy = v * a3_sin(lean) >> 8;
                int x = cx + ((u * ct - hz * stl) >> 8), z = cz + ((u * stl + hz * ct) >> 8);
                fx3(x, ch + hy, z, (ring == 1) ? fx2 : fx, ring == 2 ? OBANK_FX_B : OBANK_FX_A, 200, a, tgt);
            }
        }
        if (t >= 46 && t < 58) big_draw(side_cx(tgt), side_cy(tgt), FXB_FLARE, OBANK_FX_A, 128 + (t - 46) * 24,
                                        128 + (t - 46) * 24, t * 5, 0, 0);
        if (self) {
            anim.tint_side = side;
            anim.tint_amount = 4 + tri_sin(t * 8) / 16;
            self_pulse_when(46);
        } else {
            impact_when(46, st, dx, dy);
            anim.tint_amount = t > 12 ? 5 : 0;
            if (fx == FX_SPARK_B || fx2 == FX_SPARK_B) anim.mon_dx[foe] = t > 20 && t < 56 ? ((t & 2) ? 1 : -1) : 0;
        }
        anim.bg_amount = t < anim.dur - 4 ? tint_amt : 0;
        break;
    }
    case AK_IMPLODE: {
        /* a dark orb swells in front of the user and sails over; the world
         * dims, everything nearby spirals into it (the camera leans in), it
         * collapses to a point, then bursts */
        anim.bg_color = RGB15(2, 1, 6);
        anim.bg_amount = t < 60 ? (t < 10 ? t : 11) : 0;
        int x, y, z;
        if (t < 12) {
            w3_path(side, foe, 0, 0, &x, &y, &z);
            fx3(x + (ux >> 3), y + 10, z + (uz >> 3), fx, OBANK_FX_A, 96 + t * 16, t * 8, -1);
        } else if (t < 26) {
            w3_path(side, foe, (t - 12) * 256 / 14, 40, &x, &y, &z);
            fx3(x, y + 10 - (t - 12) * 10 / 14, z, fx, OBANK_FX_A, 288, t * 8, -1);
        } else if (t < 50) {
            int shrink = t < 40 ? 320 : 320 - (t - 40) * 28;
            fx3(bx, bh, bz - 14, fx, OBANK_FX_A, shrink, t * 12, -1);
            for (int i = 0; i < 10; i++) {
                int pt = (t * 3 + i * 13) % 40;              /* 40 = far out, 0 = swallowed */
                int rr = 60 - pt * 60 / 40;
                int a = i * 26 + pt * 12, e = (i * 29) % 96 - 48;
                int ce = a3_cos(e) * rr >> 8;
                fx3t(bx + (a3_cos(a) * ce >> 8), bh + (a3_sin(e) * rr >> 8), bz - 14 + (a3_sin(a) * ce >> 8),
                     (i & 1) ? fx2 : FX_EMBER, OBANK_FX_B, 200 + rr, 128 + rr, a + 64, foe);
            }
            anim.scale_x[foe] = 256 - (t - 26);
            anim.mon_dx[foe] = (t & 2) ? 1 : -1;
            a3_cam_zoom = 256 + (t < 44 ? (t - 26) : (50 - t) * 3);
        }
        impact_when(30, 0, dx, dy);
        if (impact_when(50, st, dx, dy)) {
            burst3(foe, 0, bh, -10, 8, 34, 10, FX_EMBER, OBANK_FX_B, 16, 1, P3_SHRINK);
            feel.zoom = 18;
        }
        if (t >= 50 && t < 64) {
            big_draw(dx, dy, FXB_FLARE, OBANK_FX_B, 128 + (t - 50) * 26, 128 + (t - 50) * 26, t * 6, 0, 0);
            ring3(bx, 0, bz, (t - 50) * 3, FXB_WAVE, OBANK_FX_A, 0, 1);
            anim.bright = t < 53 ? -6 : 0;
        }
        if (t > 26) anim.tint_amount = 8;
        break;
    }
    case AK_SPRAY: {
        /* a spray thrown in a cone: every speck flies on its own ballistic
         * arc (gravity, depth), hits and splatters or bounces on the ground */
        if (t < 8) anim.mon_dx[side] = -dir * t / 2, anim.scale_y[side] = 256 + t * 4;
        else if (t < 14) anim.mon_dx[side] = dir * 5;
        if (t >= 8 && t < 22 && !(t & 1)) {
            int T = 18, g = 4;
            for (int k = 0; k < 2; k++) {
                int tx = bx + fx_rand(36) - 18, tz = bz + fx_rand(30) - 18, ty = bh + fx_rand(30) - 15;
                int vx = (tx - ax - dir * 10) * 16 / T, vz = (tz - az) * 16 / T;
                int vy = ((ty - ah) * 16 + g * T * T / 2) / T;
                p3_add(ax + dir * 10, ah, az, vx, vy, vz, (k & 1) ? fx2 : fx, (k & 1) ? OBANK_FX_B : OBANK_FX_A, T + 10, g,
                       14, P3_BOUNCE);
            }
        }
        impact_when(26, 0, dx, dy);
        impact_when(34, st, dx, dy);
        if (t >= 26 && t < 50) {
            if (fx2 == FX_STEAM) fx_spr_aff(dx + ((t & 4) ? 3 : -3), dy - (t - 26), FX_STEAM, OBANK_FX_B, 192 + (t - 26) * 8, 0);
            if (fx == FX_DUST && t < 44) orbit3(foe, bh + 10, 20, 30, t * 12, 3, FX_DUST, FX_PEBBLE, 224, 0);
            anim.tint_amount = 6;
            anim.mon_dx[foe] = (t & 4) ? 1 : -1;
        }
        break;
    }
    case AK_BLIZZARD: {
        /* a blizzard streams across in sheets at every depth (near flakes big
         * and quick, far ones small), tumbling; it whirls round the foe and a
         * frosty ring spreads on the ground */
        anim.bg_amount = t < 60 ? (t < 10 ? t : 9) : 0;
        a3_cam_x = t < 56 ? a3_sin(t * 4) >> 6 : 0;
        for (int i = 0; i < 16; i++) {
            int pt = (t * 2 + i * 23) & 63;
            if (t < 6 && pt > t * 6) continue;
            if (t > 56 && pt < 30) continue;
            int z = 160 + ((i * 37) & 255);
            int x = dir > 0 ? -150 + pt * 5 : 150 - pt * 5;
            int y = 10 + ((i * 17) & 63) + (a3_sin(pt * 10 + i * 30) >> 5);
            fx3t(x, y, z, (i % 3) ? fx : fx2, (i & 1) ? OBANK_FX_B : OBANK_FX_A, tumble(pt * 12 + i * 40, 64), 256,
                 pt * 4, z > (az + bz) / 2 ? foe : side);
        }
        if (t > 20 && t < 60) {
            orbit3(foe, bh - 10 + ((t - 20) >> 2), 26, 40, t * 12, 5, fx, fx2, 200, 1);
            ring3(bx, 0, bz, 10 + ((t - 20) >> 1), FXB_RING, OBANK_FX_B, -t * 4, 1);
        }
        impact_when(28, 0, dx, dy);
        impact_when(44, st, dx, dy);
        anim.tint_amount = t > 28 ? 7 : 0;
        break;
    }
    case AK_SPIN: {
        /* the user spins on the spot (its sprite turning edge-on), a ring of
         * water whirls round it and a vortex under it, then it drills into
         * the foe still spinning, and bursts out in spray */
        int l = t < 16 ? 0 : t < 24 ? 44 * ease_in(t - 16, 8) / 256 : t < 32 ? 44 : 44 - 44 * ease_out(t - 32, 14) / 256;
        anim.mon_dx[side] = dir * l;
        anim.mon_dy[side] = -dir * l / 3;
        int spinning = t < 34;
        if (spinning) {
            int c = a3_cos(t * (6 + t / 2));
            anim.scale_x[side] = absi(c) < 40 ? (c < 0 ? -40 : 40) : c;
        }
        int wk = l * 256 / 64;
        int cx = ax + ((ux * wk) >> 8), cz = az + ((uz * wk) >> 8);
        if (t < 40) {
            for (int i = 0; i < 6; i++) {
                int a = t * 20 + i * 43;
                fx3(cx + (a3_cos(a) * 30 >> 8), ah - 12 + ((i & 1) ? 10 : 0) + (a3_sin(a * 2) >> 6),
                    cz + (a3_sin(a) * 24 >> 8), (i & 1) ? fx2 : fx, (i & 1) ? OBANK_FX_B : OBANK_FX_A, 232, a + 64,
                    cz > (az + bz) / 2 ? foe : side);
            }
            ring3(cx, 0, cz, 22, FXB_VORTEX, OBANK_FX_B, -t * 16, 1);
        }
        if (impact_when(24, st + 1, dx - dir * 8, dy)) {
            burst3(foe, 0, bh, -10, 8, 32, 24, FX_DROP, OBANK_FX_A, 22, 4, P3_BOUNCE);
            feel.zoom = 14;
        }
        if (t >= 24 && t < 36) ring3(bx, 0, bz, 8 + (t - 24) * 3, FXB_WAVE, OBANK_FX_A, 0, 1);
        anim.bg_amount = t > 8 && t < 44 ? tint_amt : 0;
        break;
    }
    case AK_CYCLONE: {
        /* a funnel of wind: stacked rings of gusts turning (their far sides
         * behind), wider at the top, dust at the foot. DRAFT sends it across
         * to the foe; UPDRAFT spins it up round the user and lifts it */
        int self = MOVES[anim.move].cat == CAT_STATUS;
        int cx, cz, tgt = self ? side : foe;
        if (self || t >= 22) {
            cx = w3_side_x(tgt), cz = w3_side_z(tgt);
        } else {
            int k = ease_in(t, 22);
            cx = ax + ((ux * k) >> 8), cz = az + ((uz * k) >> 8);
        }
        int grow = t < 10 ? t * 26 : t > 50 ? (60 - t) * 26 : 256;
        int levels = 5;
        for (int lv = 0; lv < levels; lv++) {
            int y = 4 + lv * 16;
            int r = ((10 + lv * 7) * grow) >> 8;
            for (int i = 0; i < 3; i++) {
                int a = t * (22 - lv * 2) + i * 85 + lv * 30;
                int f = (lv + i) % 3 == 0 ? fx2 : fx;
                fx3t(cx + (a3_cos(a) * r >> 8), y + (a3_sin(a) >> 6), cz + (a3_sin(a) * r >> 8), f,
                     (lv & 1) ? OBANK_FX_B : OBANK_FX_A, a3_sin(a) > 0 ? -224 : 224, 224, 0, tgt);
            }
        }
        if (grow > 0) ring3(cx, 0, cz, (grow * 18) >> 8, FXB_VORTEX, OBANK_FX_B, t * 20, 1);
        if (t & 1) p3_add(cx + fx_rand(30) - 15, 2, cz + fx_rand(20) - 10, 0, 6, 0, FX_DUST, OBANK_FX_B, 10, 0, 0, P3_SHRINK);
        if (self) {
            anim.mon_dy[side] = -(grow * 12 >> 8) + (a3_sin(t * 12) >> 7);
            anim.tint_side = side;
            anim.tint_amount = 5;
            self_pulse_when(30);
        } else {
            impact_when(24, 0, dx, dy);
            impact_when(44, st, dx, dy);
            if (t > 22 && t < 50) {
                anim.mon_dy[foe] = -((t - 22) < 8 ? (t - 22) : 8) + (a3_sin(t * 16) >> 7);
                anim.mon_dx[foe] = a3_sin(t * 20) >> 6;
            }
        }
        anim.bg_amount = t < 56 ? tint_amt : 0;
        break;
    }
    case AK_PRISM: {
        /* a prism turns in the air before the user; a white beam goes in, a
         * fan of coloured rays comes out, sweeps and closes on the foe */
        int px0 = sx + dir * 26, py0 = sy - 22;
        if (t < 60) fx_spr_aff2(px0, py0, FX_PRISM, OBANK_FX_HIT, tumble(t * 6, 60), 288, a3_sin(t * 4) >> 5);
        for (int b = 0; b < 2; b++) build_fx_palette(b ? OBANK_FX_B : OBANK_FX_A, hue15(t * 6 + b * 64), hue15(t * 6 + b * 64 + 96));
        if (t >= 8 && t < 50) {                          /* in */
            int head = a3_atan2(py0 - sy, px0 - sx);
            for (int s = 0; s < 2; s++)
                fx_spr_aff2(sx + (px0 - sx) * (s * 2 + 1) / 4, sy + (py0 - sy) * (s * 2 + 1) / 4, FX_BEAM, OBANK_FX_HIT,
                            288, 160, head);
        }
        if (t >= 14 && t < 54) {                         /* out: rays fan, then converge */
            int fan = t < 34 ? 40 - (t - 14) : 20 - (t - 34);
            if (fan < 0) fan = 0;
            int len = t < 24 ? (t - 14) * 26 : 256;
            for (int r = 0; r < 3; r++) {
                int tx = dx + (r - 1) * fan * 2, ty = dy + (r - 1) * fan;
                int head = a3_atan2(ty - py0, tx - px0);
                for (int s = 1; s <= 6; s++) {
                    int k = s * 256 / 6;
                    if (k > len) break;
                    int px = px0 + ((tx - px0) * k >> 8), py = py0 + ((ty - py0) * k >> 8);
                    fx_spr_aff2(px, py, FX_BEAM, r == 1 ? OBANK_FX_HIT : (r ? OBANK_FX_B : OBANK_FX_A), 256,
                                176 - s * 10, head);
                }
            }
        }
        impact_when(34, st, dx, dy);
        if (t >= 34 && t < 54) {
            big_draw(dx, dy, FXB_FLARE, OBANK_FX_A, 192 + ((t & 2) ? 40 : 0), 192 + ((t & 2) ? 40 : 0), t * 5, 0, 0);
            ring3(bx, 0, bz, 8 + ((t - 34) % 10) * 2, FXB_WAVE, OBANK_FX_B, 0, 1);
            anim.tint_amount = 8;
        }
        anim.bg_amount = t > 10 && t < 58 ? tint_amt : 0;
        break;
    }
    }
    (void)fx2;
    (void)ah;
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
    feel.zoom = feel.zoom * 3 / 4;
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
    fx_coarse = 1;
    for (int i = 0; i < P3_MAX; i++) {
        P3 *p = &p3s[i];
        if (!p->life) continue;
        int x = p->x >> 4, y = p->y >> 4, z = p->z >> 4, age = p->max - p->life;
        int ref = z > (w3_side_z(SIDE_ALLY) + w3_side_z(SIDE_ENEMY)) / 2 ? SIDE_ENEMY : SIDE_ALLY;
        int mul = (p->flags & P3_SHRINK) && p->life < 7 ? 64 + p->life * 28 : 256;
        if (p->flags & P3_FLAT) {
            ring3(x, y, z, 4 + age * 3, p->fx, p->bank, p->rot, 1);
        } else {
            if ((p->flags & P3_SHADOW) && y > 2) shadow3(x, z, 150, y);
            if (p->flags & P3_BIG) big3(x, y, z, p->fx, p->bank, mul, p->rot, ref);
            else if (p->flags & P3_TUMBLE) fx3t(x, y, z, p->fx, p->bank, (tumble(p->rot * 2, 64) * mul) >> 8, mul, p->rot, ref);
            else fx3(x, y, z, p->fx, p->bank, mul, p->rot, ref);
        }
        if (frozen) continue;
        p->x = (s16)(p->x + p->vx);
        p->y = (s16)(p->y + p->vy);
        p->z = (s16)(p->z + p->vz);
        p->vy = (s16)(p->vy - p->grav);
        p->rot = (u8)(p->rot + p->vrot);
        if (p->y < 0 && (p->flags & P3_BOUNCE)) {
            p->y = 0;
            if (p->vy < -10) {
                p->vy = (s16)(-p->vy * 2 / 5);
                p->vrot = (s8)(p->vrot / 2);
            } else {
                p->vy = 0;
                p->vrot = 0;
            }
            p->vx = (s16)(p->vx * 3 / 4);
            p->vz = (s16)(p->vz * 3 / 4);
        } else if (p->y < -16 * 24) {
            p->life = 1;                  /* fell out of sight */
        }
        p->life--;
    }
    fx_coarse = 0;
}

/* Advance one frame and push particle sprites. Returns 0 when finished. */
static int anim_step(int frozen);

static int anim_update(void)
{
    int frozen = feel.hitstop > 0;
    anim_frozen = frozen;
    if (!anim_nodraw) {
        anim_frame++;
        a3_frame_begin();
    }
    int ret = anim_step(frozen);
    /* the camera: what the kind asked for plus the decaying punch-in */
    a3_cam_zoom += feel.zoom;
    parts_update(frozen);
    anim_frozen = 0;
    if (!a3_defer_back) a3_flush_back();
    return ret;
}

static int anim_step(int frozen)
{
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
    feel.zoom = 0;
    shake_x = shake_y = 0;
    a3_cam_x = a3_cam_y = 0;
    a3_cam_zoom = 256;
    a3_back_n = 0;
    a3_layer_back = 0;
}
