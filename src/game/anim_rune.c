/*
 * The RUNE moves: ten battle animations in the RUNESTONE's arcane style
 * (included right after anim.c, whose state and hit feedback they share).
 *
 * Everything is built from a handful of pieces (src/gfx_rune.h) turned in
 * pseudo-3D with affine sprites:
 *
 *   rn_mat      one matrix for "turn in its own plane, squash, then lean":
 *               a circle lying on the ground (spin, squash), a gate standing
 *               across the path (thin, leaned to the path's angle), a rune
 *               turning about its vertical axis (sx = cos yaw, mirrored on
 *               the back), a spike leaning out.
 *   rn_ring     runes on an inclined ellipse: position, depth (front = low
 *               on screen), size and brightness by depth, prio 1 in front of
 *               the kin, prio 2 behind it.
 *   rn_persp    the camera looks from behind the ally: things near the ally
 *               are big, near the foe small; a flight scales between them.
 *   draw list   every piece is queued with its depth and emitted sorted
 *               (front first), so overlapping runes layer correctly.
 *
 * VRAM and palettes while a RUNE move plays (loaded on its first frame):
 *   OBJ tiles RN_OT..+RT_TILE_COUNT (0..215): the player/NPC/party-icon
 *       slots, unused in a bout (menus that borrow them never overlap a
 *       move animation, and the art is reloaded on every RUNE move).
 *   OBJ banks 2..6 (NPC banks, unused in a bout): the element palette at
 *       three depths (full, mid, far) and the ARCANE palette (full, dim).
 * Up to ~48 sprites and ~20 affine matrices a frame (the kin keep theirs).
 */

#define RN_OT       0
#define RB_EL         2      /* element palette, in front */
#define RB_EL_MID     3      /* element palette, half faded */
#define RB_EL_FAR     4      /* element palette, far behind */
#define RB_ARC        5      /* the set's arcane violet */
#define RB_ARC_DIM    6

enum { RN_G16, RN_G32, RN_SPARK8, RN_TALL };

typedef struct {
    s16 x, y;                 /* centre (px) */
    s16 sx, sy;               /* 8.8 scale; negative mirrors */
    s16 depth;                /* larger = nearer the camera */
    u16 tile, flags;
    u8 kind, bank, prio, spin, tilt;
} RnItem;

#define RN_MAX 72
EWRAM_BSS static RnItem rn_list[RN_MAX];
static int rn_count;

typedef struct { s16 x, y, vx, vy; u8 life, max, kind, bank; s8 grav; } RnPart;   /* 1/16 px */
#define RN_PARTS 28
EWRAM_BSS static RnPart rn_parts[RN_PARTS];

/* ---------------- maths ---------------- */

static int rs(int a) { return travel_sin[a & 255]; }        /* -256..256 */
static int rc(int a) { return travel_sin[(a + 64) & 255]; }

/* The angle (0..255) pointing along (vx, vy). */
static int rn_angle_of(int vx, int vy)
{
    int best = 0, bd = -0x7FFFFFFF;
    for (int a = 0; a < 256; a += 2) {
        int d = rc(a) * vx + rs(a) * vy;
        if (d > bd) bd = d, best = a;
    }
    return best;
}

static int rn_lerp(int a, int b, int u) { return a + (b - a) * u / 256; }

/* A quadratic curve p0 -> p2 bent toward p1 (u 0..256). */
static int rn_bez(int p0, int p1, int p2, int u)
{
    int v = 256 - u;
    return (p0 * v * v + 2 * p1 * u * v + p2 * u * u) / 65536;
}

/* Where effects meet the ground by a side: the ally's feet are under the
 * message box, the foe's under the ally's panel, so both sit a little up. */
static int rn_gy(int side) { return side == SIDE_ALLY ? 104 : 60; }

/* 0..256 smooth in and out over n frames */
static int rn_smooth(int t, int n)
{
    if (t <= 0) return 0;
    if (t >= n) return 256;
    int u = t * 256 / n;
    return u * u * (768 - 2 * u) / 65536;
}

/* Size of things next to a side: the ally stands near the camera. */
static int rn_persp(int side) { return side == SIDE_ALLY ? 300 : 210; }

/* ---------------- palettes and tiles ---------------- */

static const u8 RUNE_PAL_OF[] = {
    RP_ARCANE, RP_SIGIL, RP_ALGIZ, RP_KENAZ, RP_ARCANE, RP_THURS, RP_RAIDO, RP_ISA, RP_SOWILO, RP_SIPHON,
};

static void rn_bank(int bank, const u16 *src, int fade)
{
    u16 *p = obj_palette + bank * 16;
    p[0] = 0;
    for (int i = 1; i < 16; i++) p[i] = fade ? mix15(src[i], RGB15(12, 10, 20), fade, 100) : src[i];
}

static void rn_palettes(int kind)
{
    const u16 *el = rune_palettes[RUNE_PAL_OF[kind - AK_RUNE_BOLT]];
    rn_bank(RB_EL, el, 0);
    rn_bank(RB_EL_MID, el, 26);
    rn_bank(RB_EL_FAR, el, 50);
    rn_bank(RB_ARC, rune_palettes[RP_ARCANE], 0);
    rn_bank(RB_ARC_DIM, rune_palettes[RP_ARCANE], 30);
}

/* ---------------- the draw list ---------------- */

static RnItem *rn_add(int kind, int x, int y, int tile, int bank, int prio, int depth)
{
    if (rn_count >= RN_MAX) return 0;
    RnItem *it = &rn_list[rn_count++];
    it->kind = (u8)kind;
    it->x = (s16)x;
    it->y = (s16)y;
    it->tile = (u16)tile;
    it->bank = (u8)bank;
    it->prio = (u8)prio;
    it->depth = (s16)depth;
    it->sx = it->sy = 256;
    it->spin = it->tilt = 0;
    it->flags = 0;
    return it;
}

static void rn_xf(RnItem *it, int sx, int sy, int spin, int tilt)
{
    if (!it) return;
    it->sx = (s16)clampi(sx, -1024, 1024);
    it->sy = (s16)clampi(sy, -1024, 1024);
    it->spin = (u8)(spin & 255);
    it->tilt = (u8)(tilt & 255);
}

/* Inverse of R(tilt) * S(sx, sy) * R(spin) as an OAM matrix. */
static int rn_mat(int sx, int sy, int spin, int tilt)
{
    if (sx > -8 && sx < 8) sx = sx < 0 ? -8 : 8;
    if (sy > -8 && sy < 8) sy = sy < 0 ? -8 : 8;
    int c1 = rc(spin), s1 = rs(spin), ct = rc(tilt), st = rs(tilt);
    int b00 = ct * 256 / sx, b01 = st * 256 / sx, b10 = -st * 256 / sy, b11 = ct * 256 / sy;
    return oam_affine((c1 * b00 + s1 * b10) >> 8, (c1 * b01 + s1 * b11) >> 8,
                      (-s1 * b00 + c1 * b10) >> 8, (-s1 * b01 + c1 * b11) >> 8);
}

/* Offset of a point (lx, ly) of a flat piece after rn_mat's transform. */
static void rn_map(int lx, int ly, int sx, int sy, int spin, int tilt, int *ox, int *oy)
{
    int x0 = (lx * rc(spin) - ly * rs(spin)) >> 8, y0 = (lx * rs(spin) + ly * rc(spin)) >> 8;
    int x1 = x0 * sx / 256, y1 = y0 * sy / 256;
    *ox = (x1 * rc(tilt) - y1 * rs(tilt)) >> 8;
    *oy = (x1 * rs(tilt) + y1 * rc(tilt)) >> 8;
}

static void rn_flush(void)
{
    /* front first: prio ascending, then nearer first */
    for (int i = 1; i < rn_count; i++) {
        RnItem k = rn_list[i];
        int j = i - 1;
        while (j >= 0 && (rn_list[j].prio > k.prio || (rn_list[j].prio == k.prio && rn_list[j].depth < k.depth))) {
            rn_list[j + 1] = rn_list[j];
            j--;
        }
        rn_list[j + 1] = k;
    }
    typedef struct { s16 sx, sy; u8 spin, tilt; s8 aff; } RnMat;
    RnMat mk[32];
    int nm = 0;
    if (!anim_nodraw)
        for (int i = 0; i < rn_count; i++) {
            const RnItem *it = &rn_list[i];
            int shape = SQ16, w = 16, h = 16;
            if (it->kind == RN_G32) shape = SQ32, w = h = 32;
            else if (it->kind == RN_SPARK8) shape = SQ8, w = h = 8;
            else if (it->kind == RN_TALL) shape = TALL16x32, h = 32;
            int x = it->x - w / 2 + shake_x, y = it->y - h / 2 + shake_y;
            int flags = it->flags;
            /* things behind (the faded banks) are also see-through */
            if (it->bank == RB_EL_MID || it->bank == RB_EL_FAR || it->bank == RB_ARC_DIM) flags |= ATTR0_BLEND;
            if (it->sx == 256 && it->sy == 256 && !it->spin && !it->tilt) {
                spr_push(x, y, it->tile, shape, it->bank, it->prio, flags);
                continue;
            }
            /* pieces with the same transform share one matrix */
            int aff = -1;
            for (int k = 0; k < nm; k++)
                if (mk[k].sx == it->sx && mk[k].sy == it->sy && mk[k].spin == it->spin && mk[k].tilt == it->tilt) {
                    aff = mk[k].aff;
                    break;
                }
            if (aff < 0) {
                aff = rn_mat(it->sx, it->sy, it->spin, it->tilt);
                if (aff >= 0 && nm < 32) mk[nm++] = (RnMat){ it->sx, it->sy, it->spin, it->tilt, (s8)aff };
            }
            spr_push_affine(x, y, it->tile, shape, it->bank, it->prio, flags, aff, 1);
        }
    rn_count = 0;
}

/* ---------------- pieces ---------------- */

static int rn_prio(int depth) { return depth >= 0 ? 1 : 2; }
static int rn_el_bank(int depth) { return depth >= 0 ? RB_EL : depth > -150 ? RB_EL_MID : RB_EL_FAR; }

static RnItem *rn_glyph(int x, int y, int g, int bank, int prio, int depth)
{
    return rn_add(RN_G16, x, y, RN_OT + RT_GLYPH + (g % RG_COUNT) * 4, bank, prio, depth);
}

static RnItem *rn_hero(int x, int y, int h, int bank, int prio, int depth)
{
    return rn_add(RN_G32, x, y, RN_OT + RT_HERO + h * 16, bank, prio, depth);
}

/* A circle lying on the ground: `sc` wide, squashed to `sq` / 256 tall. */
static RnItem *rn_ground(int x, int y, int tile, int bank, int sc, int sq, int spin, int blend)
{
    RnItem *it = rn_add(RN_G32, x, y, RN_OT + tile, bank, 2, -2000);
    if (sc > 508) sc = 508;
    rn_xf(it, sc, sc * sq / 256, spin, 0);
    if (it && blend) it->flags = ATTR0_BLEND;
    return it;
}

static void rn_spark(int x, int y, int k, int bank, int prio)
{
    rn_add(RN_SPARK8, x, y, RN_OT + RT_SPARK + k, bank, prio, 100);
}

/* Runes on an inclined ellipse round (cx, cy): rx, ry, leaned by `tilt`.
 * face 1 turns each rune tangent to the ring (edge-on at the sides). */
static void rn_ring(int cx, int cy, int rx, int ry, int tilt, int base, int count, int shown, int g0,
                    int sc, int face)
{
    for (int i = 0; i < count && i < shown; i++) {
        int a = base + i * 256 / count;
        int px = rc(a) * rx >> 8, py = rs(a) * ry >> 8, depth = rs(a);
        int x = cx + ((px * rc(tilt) - py * rs(tilt)) >> 8);
        int y = cy + ((px * rs(tilt) + py * rc(tilt)) >> 8);
        int s = sc * (256 + depth / 4) / 256;
        int sx = face ? s * rs(a) / 256 : s;
        if (face && sx > -s / 3 && sx < s / 3) sx = sx < 0 ? -s / 3 : s / 3;
        rn_xf(rn_glyph(x, y, g0 + i, rn_el_bank(depth), rn_prio(depth), depth), sx, s, 0,
              face ? tilt : 0);
    }
}

/* ---------------- particles ---------------- */

enum { RNP_SPARK, RNP_GLYPH };

static void rn_part(int kind, int x, int y, int vx, int vy, int life, int grav, int bank)
{
    for (int i = 0; i < RN_PARTS; i++) {
        RnPart *p = &rn_parts[i];
        if (p->life) continue;
        *p = (RnPart){ (s16)(x * 16), (s16)(y * 16), (s16)vx, (s16)vy, (u8)life, (u8)life, (u8)kind, (u8)bank,
                       (s8)grav };
        return;
    }
}

/* Sparks rising from a ground ellipse. */
static void rn_rise(int cx, int gy, int rx, int n, int bank)
{
    for (int k = 0; k < n; k++) {
        int a = fx_rand(256);
        rn_part(RNP_SPARK, cx + rc(a) * rx / 256, gy + rs(a) * rx / 768, -rc(a) / 64, -(12 + fx_rand(14)),
                18 + fx_rand(14), 0, bank);
    }
}

/* A burst of sparks (and glyph shards) flying out of a point. */
static void rn_burst(int x, int y, int n, int speed, int glyphs, int grav)
{
    for (int k = 0; k < n; k++) {
        int a = k * 256 / n + fx_rand(12), sp = speed + fx_rand(speed / 2 + 1);
        rn_part(glyphs && (k & 1) ? RNP_GLYPH : RNP_SPARK, x, y, rc(a) * sp / 256, rs(a) * sp / 320 - 6,
                16 + fx_rand(10), grav, RB_EL);
    }
}

static void rn_parts_step(int frozen)
{
    for (int i = 0; i < RN_PARTS; i++) {
        RnPart *p = &rn_parts[i];
        if (!p->life) continue;
        int x = p->x / 16, y = p->y / 16, age = p->max - p->life;
        if (p->kind == RNP_GLYPH) {
            int s = 256 - age * 160 / p->max;
            rn_xf(rn_glyph(x, y, (i * 5) % RG_COUNT, p->life < 6 ? RB_EL_MID : p->bank, 1, 50), s * rc(age * 20) / 256,
                  s, 0, 0);
        } else {
            int f = age * 4 / (p->max + 1);
            if (p->life > 3 || (p->life & 1)) rn_spark(x, y, clampi(f, 0, 3), p->bank, 1);
        }
        if (frozen) continue;
        p->x = (s16)(p->x + p->vx);
        p->y = (s16)(p->y + p->vy);
        p->vy = (s16)(p->vy + p->grav);
        p->life--;
    }
}

/* ---------------- durations ---------------- */

static int anim_rune_duration(int kind)
{
    static const u8 DUR[] = { 62, 76, 72, 78, 96, 70, 58, 74, 68, 80 };
    int k = kind - AK_RUNE_BOLT;
    return k >= 0 && k < (int)sizeof DUR ? DUR[k] : 40;
}

/* ================================================================ */
/*  The ten moves                                                   */
/* ================================================================ */

typedef struct {
    int t, side, foe, dir, st;
    int sx, sy, dx, dy, ugy, fgy;
    int path;                 /* angle from the user to the foe */
} RnCtx;

/* A seal standing across the path at (x, y): thin along the path, turning
 * in its own plane. */
static RnItem *rn_gate(const RnCtx *c, int x, int y, int tile, int bank, int sc, int spin)
{
    RnItem *it = rn_add(RN_G32, x, y, RN_OT + tile, bank, 1, -50);
    rn_xf(it, sc * 150 / 256, sc * 290 / 256, spin, c->path);
    return it;
}

/* RUNE BOLT: a casting seal stands across the path, TIWAZ (the spear
 * rune) forms in it, flies at the foe point first, rocking on its axis and
 * shrinking or growing with distance, a trail of ghosts behind; it bursts
 * in a ring on the foe. */
static void rn_bolt(const RnCtx *c)
{
    int t = c->t;
    int gx = c->sx + c->dir * 20, gy = c->sy - 14;
    int big = rn_persp(c->side) * 3 / 2;
    if (t < 30) {
        int g = t < 18 ? ease_out(t, 12) : 256 - ease_in(t - 18, 12);
        rn_gate(c, gx, gy, RT_SEAL, RB_ARC, rn_persp(c->side) * 5 / 4 * g / 256, t * 7);
    }
    if (t < 16) {
        int s = big * ease_out(t - 3, 12) / 256;
        if (t >= 3)
            rn_xf(rn_glyph(gx, gy, RG_TIWAZ, RB_EL, 1, 0), s * (150 + absi(rc(t * 16)) * 106 / 256) / 256, s, 0,
                  c->path + 64);
        if (t == 3) sfx_play(SFX_SPARKLE);
        if (t > 4 && (t & 1)) {
            int a = fx_rand(256);
            rn_part(RNP_SPARK, gx + rc(a) * 26 / 256, gy + rs(a) * 26 / 256, -rc(a) / 24, -rs(a) / 24, 10, 0, RB_EL);
        }
        return;
    }
    if (t < 34) {
        for (int k = 5; k >= 0; k--) {
            int tt = t - k * 2;
            if (tt < 16) continue;
            int u = ease_in(tt - 16, 18);
            int x = rn_lerp(gx, c->dx, u), y = rn_lerp(gy, c->dy - 4, u) - rs(u / 2) * 14 / 256;
            int s = rn_lerp(big, rn_persp(c->foe) * 3 / 2, u) * (256 - k * 30) / 256;
            if (k == 0) {
                rn_xf(rn_glyph(x, y, RG_TIWAZ, RB_EL, 1, 10), s * (150 + absi(rc(t * 22)) * 106 / 256) / 256, s, 0,
                      c->path + 64);
                rn_part(RNP_SPARK, x - c->dir * 6, y + fx_rand(9) - 4, -c->dir * 10, fx_rand(9) - 4, 10, 0, RB_EL);
            } else {
                rn_xf(rn_glyph(x, y, RG_TIWAZ, k < 3 ? RB_EL_MID : RB_EL_FAR, 1, -k), s, s, 0, c->path + 64);
            }
        }
        return;
    }
    if (impact_when(34, c->st, c->dx, c->dy)) rn_burst(c->dx, c->dy - 4, 10, 30, 1, 2);
    int bt = t - 34;
    anim.tint_amount = bt < 16 ? 10 - bt * 10 / 16 : 0;
    if (bt < 20 && (bt < 14 || (bt & 1))) {
        int sc = 96 + ease_out(bt, 16) * 400 / 256;
        rn_xf(rn_add(RN_G32, c->dx, c->dy - 4, RN_OT + RT_RING, RB_EL, 1, 5), sc, sc, bt * 3, 0);
        rn_ground(c->dx, c->fgy, RT_RING, RB_ARC, 200 + bt * 16, 100, bt * 4, bt > 10);
    }
    if (bt < 10) rn_xf(rn_hero(c->dx, c->dy - 4, RH_ANSUZ, RB_EL, 1, 20), 320 - bt * 20, 320 - bt * 20, 0, 0);
}

/* SIGIL SNARE: a seal opens on the ground under the foe, runes climb out
 * of its rim and circle, then clamp down on the foe's feet with chains of
 * light. */
static void rn_snare(const RnCtx *c)
{
    int t = c->t, foe = c->foe;
    int cx = c->dx, gy = c->fgy - 2;
    anim.tint_side = foe;
    anim.bg_amount = t < 66 ? 5 : 0;
    /* the caster's glyph lights up first */
    if (t < 20) {
        int s = rn_persp(c->side) * ease_out(t, 10) / 256;
        rn_xf(rn_glyph(c->sx + c->dir * 6, c->sy - 20, RG_INGWAZ, RB_EL, 1, 0), s * rc(t * 12) / 256, s, 0, 0);
        if ((t & 3) == 0) rn_rise(c->sx, c->ugy, 20, 2, RB_EL);
    }
    if (t >= 6) {
        int op = ease_out(t - 6, 14);
        int fade = t > 64 ? (t - 64) * 30 : 0;
        int sc = 500 * op / 256 - fade;
        if (sc > 16) {
            rn_ground(cx, gy, RT_SEAL, RB_EL, sc, 100, t * 2 + (t > 44 ? (t - 44) * (t - 44) / 3 : 0), t > 66);
            if (t < 62) rn_ground(cx, gy, RT_CIRCLE, RB_ARC_DIM, sc * 3 / 4, 100, -t * 3, 1);
        }
        if (t == 8) sfx_play(SFX_DREAM);
    }
    /* runes rise out of the rim, circle, then snap in */
    if (t >= 14 && t < 60) {
        int clamp = t < 44 ? 0 : ease_in(t - 44, 8);
        int rx = 44 - 30 * clamp / 256, ry = 12 - 7 * clamp / 256;
        for (int i = 0; i < 6; i++) {
            int rt = t - 14 - i * 3;
            if (rt < 0) continue;
            int a = t * 3 + (t > 44 ? (t - 44) * 10 : 0) + i * 256 / 6;
            int h = t < 44 ? 30 * ease_out(rt, 12) / 256 : 30 - 24 * clamp / 256;
            int depth = rs(a);
            int x = cx + rc(a) * rx / 256, y = gy + rs(a) * ry / 256 - h;
            int s = 300 * (256 + depth / 4) / 256;
            rn_xf(rn_glyph(x, y, i * 2 + 1, rn_el_bank(depth), rn_prio(depth), depth), s * (128 + rs(a) / 2) / 256, s,
                  0, 0);
            /* the chains: beads of light to the centre as it clamps */
            if (clamp > 0)
                for (int k = 1; k < 4; k++)
                    rn_spark(rn_lerp(x, cx, k * 64), rn_lerp(y, gy - 10, k * 64), (k + t / 2) & 1 ? RS_SMALL : RS_LILAC,
                             depth >= 0 ? RB_EL : RB_EL_MID, rn_prio(depth));
        }
    }
    if (impact_when(52, 0, cx, c->dy)) {
        sfx_play(SFX_STAT_DOWN);
        rn_rise(cx, gy, 26, 8, RB_EL);
    }
    if (t >= 52) {
        anim.scale_y[foe] = 256 - (t < 66 ? 22 : 22 - (t - 66) * 2);
        anim.scale_x[foe] = 256 + (t < 66 ? 12 : 0);
        anim.mon_dx[foe] = t < 64 ? ((t & 2) ? 1 : -1) : 0;
        anim.tint_amount = t < 66 ? 9 : 4;
        if (t < 70 && (t < 62 || (t & 1))) rn_ring(cx, gy - 5, 14, 5, 0, t * 12, 6, 6, 1, 200, 0);
    }
}

/* ALGIZ WARD: two rings of runes, leaned opposite ways, spin round the user
 * like an armillary; the ALGIZ rune rises and a warding shell closes. */
static void rn_ward(const RnCtx *c)
{
    int t = c->t, side = c->side;
    int cx = c->sx, cy = c->sy - 6, gy = c->ugy;
    int base = rn_persp(side) * 240 / 256;
    anim.tint_side = side;
    anim.tint_color = RGB15(31, 28, 16);
    if (t < 20) rn_ground(cx, gy, RT_RING, RB_EL, 500 * ease_out(t, 16) / 256, 90, t * 3, 1);
    else if (t < 66) rn_ground(cx, gy, RT_SEAL, RB_EL, 480 + rs(t * 8) * 16 / 256, 90, t * 3, 1);
    if (t == 4) sfx_play(SFX_SPARKLE);
    if (t < 60) {
        int shown = clampi((t - 4) / 3, 0, 5);
        int r = t < 42 ? 40 : 40 - (t - 42) * 12 / 18;
        int spd = t * 4 + t * t / 40;
        rn_ring(cx, cy, r, r * 5 / 16, 26, spd, 5, shown, RG_ALGIZ, base, 1);
        rn_ring(cx, cy, r, r * 5 / 16, -26, -spd + 20, 5, shown, RG_OTHALA, base, 1);
    }
    if (t >= 14 && t < 66) {
        int rt = t - 14;
        int s = 60 + ease_out(rt, 20) * 220 / 256;
        int y = cy - 6 - ease_out(rt, 24) * 14 / 256 + rs(t * 6) * 2 / 256;
        rn_xf(rn_hero(cx, y, RH_ALGIZ, RB_EL, 1, 40), s * rc(rs(t * 3) / 5) / 256, s, 0, 0);
        if ((t & 3) == 0) rn_rise(cx, gy, 22, 1, RB_EL);
    }
    if (self_pulse_when(46)) sfx_play(SFX_STAT_UP);
    if (t >= 44 && t < 70 && (t < 62 || (t & 1))) {
        int s = 380 + ease_out(t - 44, 10) * 110 / 256;
        RnItem *it = rn_add(RN_G32, cx, cy - 2, RN_OT + RT_RING, RB_EL, 1, 60);
        rn_xf(it, s, s * 15 / 16, t * 2, 0);
        if (it) it->flags = ATTR0_BLEND;
    }
    anim.tint_amount = t < 44 ? t / 11 : t < 52 ? 7 : 7 - (t - 52) / 3;
}

/* KENAZ FLARE: the torch rune forms over the user turning on its axis,
 * flies over the foe, stamps into the ground; a pillar of flame and a
 * helix of embers roar up out of a fire circle. */
static void rn_kenaz(const RnCtx *c)
{
    int t = c->t, foe = c->foe;
    int hx = c->sx + c->dir * 6, hy = c->sy - 26;
    int tx = c->dx, ty = c->dy - 18;
    int hs = rn_persp(c->side) * 280 / 300;
    if (t < 18) {
        int s = hs * ease_out(t, 14) / 256;
        rn_xf(rn_hero(hx, hy, RH_KENAZ, RB_EL, 1, 20), s * rc(t * 14) / 256, s, 0, 0);
        if (t & 1) rn_part(RNP_SPARK, hx + fx_rand(40) - 20, hy + 16, 0, -10 - fx_rand(10), 12, 0, RB_EL);
        if (t == 2) sfx_play(SFX_FIRE);
        return;
    }
    if (t < 34) {
        int u = rn_smooth(t - 18, 16);
        int x = rn_lerp(hx, tx, u), y = rn_lerp(hy, ty, u) - rs(u / 2) * 12 / 256;
        int s = rn_lerp(hs, rn_persp(foe) * 300 / 210, u);
        rn_xf(rn_hero(x, y, RH_KENAZ, RB_EL, 1, 20), s * rc(t * 20) / 256, s, 0, rs(t * 9) / 24);
        rn_part(RNP_SPARK, x, y + 6, -c->dir * 6, 4, 10, 1, RB_EL);
        return;
    }
    /* the stamp: drops and lies down flat on the ground */
    if (t < 40) {
        int u = ease_in(t - 34, 6);
        rn_xf(rn_hero(tx, rn_lerp(ty, c->fgy - 4, u), RH_KENAZ, RB_EL, 1, 20), 300, 300 - 190 * u / 256, 0, 0);
        return;
    }
    if (impact_when(40, c->st, tx, c->dy)) {
        sfx_play(SFX_FIRE);
        shake(64, 1);
        rn_burst(tx, c->fgy - 8, 8, 34, 0, 3);
    }
    int ft = t - 40;
    anim.bg_amount = ft < 30 ? 5 : 2;
    anim.bg_color = RGB15(24, 6, 2);
    anim.tint_side = foe;
    anim.tint_amount = ft < 24 ? 10 + (ft & 2) * 2 : 6;
    /* the fire circle and the burnt-in rune */
    int cs = 300 + ease_out(ft, 8) * 200 / 256;
    rn_ground(tx, c->fgy, RT_CIRCLE, RB_EL, cs, 100, t * 9, ft > 26);
    if (ft < 30) rn_xf(rn_hero(tx, c->fgy - 1, RH_KENAZ, RB_EL, 2, -1500), 300, 110, 0, 0);
    /* the pillar: a bright core and a wider see-through glow, tiled up */
    int h = ease_out(ft, 6) * 130 / 256;
    int w = ft < 22 ? 380 + rs(t * 40) * 50 / 256 : 380 - (ft - 22) * 30;
    if (w > 24)
        for (int y = c->fgy - 14; y > c->fgy - 14 - h; y -= 30) {
            RnItem *core = rn_add(RN_TALL, tx, y, RN_OT + RT_BEAM, RB_EL, 1, 0);
            rn_xf(core, w * 5 / 4, 256 + ((ft & 2) ? 16 : 0), 0, 0);
            if (core && ft > 3) core->flags = ATTR0_BLEND;
            for (int k = -1; k <= 1; k += 2)
                rn_xf(rn_add(RN_TALL, tx + k * 11, y + 8 + k * 6, RN_OT + RT_BEAM, RB_EL_MID, 1, -1), w, 256, 0, 0);
        }
    /* a helix of embers round the foe */
    for (int k = 0; k < 12; k++) {
        int et = (ft * 2 + k * 11) % 64;
        if (ft > 30 && et < ft - 30) continue;
        int a = et * 10 + k * 22;
        int depth = rs(a);
        int x = tx + rc(a) * (30 - et / 5) / 256, y = c->fgy - 6 - et + depth * 6 / 256;
        rn_add(RN_SPARK8, x, y, RN_OT + RT_SPARK + (et > 40 ? RS_SMALL : RS_EMBER), depth >= 0 ? RB_EL : RB_EL_MID,
               rn_prio(depth), depth);
    }
    if (ft < 28)
        for (int k = 0; k < 2; k++)
            fx_spr(tx + fx_rand(36) - 18, c->fgy - 12 - fx_rand(40), fx_frame(FX_FLAME_A, FX_FLAME_B, t + k * 4), OBANK_FX_A);
}

/* RUNE ORBIT: eight runes gather round the foe on a ring that leans and
 * precesses, accelerate and tighten, then collapse into a flash. */
static void rn_orbit(const RnCtx *c)
{
    int t = c->t;
    int cx = c->dx, gy = c->fgy - 2;
    int spin = 2 * t + t * t * t / 2400;
    anim.bg_amount = t < 86 ? 10 : 0;
    anim.bg_color = RGB15(4, 2, 12);
    /* the circle on the ground */
    if (t < 80) {
        int sc = 480 * ease_out(t, 16) / 256 - (t > 70 ? (t - 70) * 40 : 0);
        if (sc > 16) rn_ground(cx, gy, RT_CIRCLE, RB_ARC, sc, 100, spin / 2, 0);
        if (t > 10 && (t % 3) == 0) rn_rise(cx, gy, 28, 1, RB_ARC);
    }
    if (t == 6) sfx_play(SFX_ASTRAL);
    if (t == 44) sfx_play(SFX_CHARGE);
    if (t < 76) {
        int p = rn_smooth(t - 8, 64);
        int rx = 58 - 46 * p / 256;
        int lean = rs(t * 3) * 24 / 256;
        int incl = 80 + rs(t * 2 + 40) * 34 / 256;          /* how far the ring is tipped toward us */
        int cy = rn_lerp(gy - 6, c->dy - 8, ease_out(t, 30));
        int shown = clampi(t / 3 - 1, 0, 8);
        int s = 330 - 110 * p / 256;
        rn_ring(cx, cy, rx, rx * incl / 256, lean, spin, 8, shown, 0, s, 0);
        /* a counter-ring of motes on the other slant */
        if (t > 20)
            for (int k = 0; k < 6; k++) {
                int a = -spin * 3 / 2 + k * 43, depth = rc(a);
                int x = cx + rs(a) * rx / 3 / 256, y = cy + rc(a) * rx * 3 / 4 / 256 + rs(a) * 6 / 256;
                rn_add(RN_SPARK8, x, y, RN_OT + RT_SPARK + (k & 1 ? RS_MOTE : RS_STAR),
                       depth >= 0 ? RB_ARC : RB_ARC_DIM, rn_prio(depth), depth);
            }
        if (t > 64) anim.bright = (t - 64) * 14 / 12;
        anim.tint_side = c->foe;
        anim.tint_amount = t / 10;
        return;
    }
    if (impact_when(76, c->st + 1, cx, c->dy)) {
        shake(96, 0);
        rn_burst(cx, c->dy - 6, 12, 36, 1, 1);
    }
    int bt = t - 76;
    anim.bright = bt < 4 ? 14 - bt * 3 : 0;
    for (int k = 0; k < 2; k++) {
        int kt = bt - k * 4;
        if (kt < 0 || kt >= 16) continue;
        int sc = 80 + ease_out(kt, 14) * 420 / 256;
        RnItem *it = rn_add(RN_G32, cx, c->dy - 6, RN_OT + RT_RING, k ? RB_ARC : RB_EL, 1, 10 - k);
        rn_xf(it, sc, sc, kt * 5, 0);
        if (it && kt > 9) it->flags = ATTR0_BLEND;
    }
    if (bt < 18) rn_ground(cx, gy, RT_RING, RB_ARC, 200 + ease_out(bt, 16) * 300 / 256, 100, bt * 6, bt > 8);
}

/* THURS SPIKE: the user stamps, thorn runes race flat along the ground,
 * then crystal thorns erupt in a ring round the foe and throw it up. */
static void rn_thurs(const RnCtx *c)
{
    int t = c->t, side = c->side, foe = c->foe;
    if (t < 10) {
        anim.scale_y[side] = 256 - (t < 5 ? t * 6 : (10 - t) * 6);
        anim.mon_dy[side] = t < 5 ? t / 2 : 0;
    }
    if (t == 5) {
        shake(40, 1);
        sfx_play(SFX_ROCK);
    }
    int x0 = c->sx + c->dir * 22, y0 = c->ugy;
    if (t >= 5 && t < 22) rn_ground(x0, y0, RT_SEAL, RB_EL, 220 + (t - 5) * 18, 96, t * 6, t > 14);
    /* three thorn runes lying flat, racing to the foe round the panels */
    int bx = ALLY_X + 52, by = rn_gy(SIDE_ENEMY) + 4;
    for (int k = 0; k < 3; k++) {
        int rt = t - 8 - k * 5;
        if (rt < 0 || rt >= 22) continue;
        int u = rn_smooth(rt, 22);
        int x = rn_bez(x0, bx, c->dx, u), y = rn_bez(y0, by, c->fgy, u);
        int s = rn_lerp(rn_persp(side), rn_persp(foe), u) * 5 / 4;
        rn_xf(rn_glyph(x, y, RG_THURISAZ, RB_EL, 2, -1000 + k), s, s * 120 / 256, 0, 0);
        if ((rt & 1) == 0) rn_part(RNP_SPARK, x, y, 0, -10, 10, 1, RB_EL);
    }
    int gx = c->dx, gy = c->fgy;
    if (t >= 28 && t < 40) {
        int s = 280 * ease_out(t - 28, 8) / 256;
        rn_xf(rn_hero(gx, gy - 1, RH_THURISAZ, RB_EL, 2, -1500), s, s * 100 / 256, 0, 0);
        rn_ground(gx, gy, RT_SEAL, RB_ARC, 220 + (t - 28) * 18, 100, t * 5, 1);
    }
    if (impact_when(36, c->st, gx, c->dy)) {
        shake(80, 1);
        sfx_play(SFX_ROCK);
        rn_burst(gx, gy - 6, 8, 28, 0, 3);
    }
    if (t >= 36) {
        int et = t - 36;
        int h = et < 5 ? et * 330 / 5 : et < 9 ? 330 - (et - 5) * 18 : et < 16 ? 256 : 256 - (et - 16) * 20;
        if (h > 16) {
            for (int i = 0; i < 7; i++) {
                int a = i * 256 / 7 + 18;
                int depth = rs(a);
                int px = gx + rc(a) * 36 / 256, py = gy + rs(a) * 10 / 256;
                int ls = rn_persp(foe) * (240 + depth / 5) / 256;
                int hh = h * ls / 256 * (i & 1 ? 200 : 256) / 256;
                int lean = -rc(a) * 28 / 256;
                int d = 16 * hh / 256;
                RnItem *it = rn_add(RN_TALL, px + (rs(lean) * d >> 8), py - (rc(lean) * d >> 8), RN_OT + RT_SPIKE,
                                    depth >= 0 ? RB_EL : RB_EL_MID, rn_prio(depth), depth);
                rn_xf(it, ls * 220 / 256, hh, 0, lean);
            }
            /* the great thorn behind the foe */
            int hh = h * 420 / 256, d = 16 * hh / 256;
            rn_xf(rn_add(RN_TALL, gx, gy - 2 - d, RN_OT + RT_SPIKE, RB_EL, 2, -300), 400, clampi(hh, 0, 500), 0, 0);
        }
        anim.mon_dy[foe] = et < 6 ? -et * 3 : et < 16 ? -18 + (et - 6) * 18 / 10 : 0;
        if (et < 20) anim.scale_y[foe] = 256 + (et < 6 ? 20 : 0);
        if (et == 28) {
            rn_burst(gx, gy - 10, 10, 26, 0, 4);
            sfx_play(SFX_ROCK);
        }
    }
}

/* RAIDO RUSH: a rune gate stands up across the path, runes riding its rim;
 * the user dashes through it (afterimages, the gate flares) and slams into
 * the foe, where a second gate bursts. */
static void rn_raido(const RnCtx *c)
{
    int t = c->t, side = c->side;
    int gx = c->sx + c->dir * 28, gy = c->sy - 12;
    int thin = 150, tall = rn_persp(side) * 290 / 256;
    int grow = t < 26 ? ease_out(t, 10) : 256 - ease_in(t - 26, 14);
    int flare = (t >= 13 && t < 22) ? 256 + (22 - t) * 14 : 256;
    if (grow > 8) {
        int sx = thin * grow / 256 * flare / 256, sy = tall * grow / 256 * flare / 256;
        RnItem *it = rn_add(RN_G32, gx, gy, RN_OT + RT_SEAL, RB_EL, 1, 0);
        rn_xf(it, sx, sy, t * 8, c->path);
        if (it && t > 20) it->flags = ATTR0_BLEND;
        /* runes riding the gate's rim (the far half behind the user) */
        for (int i = 0; i < 6; i++) {
            int a = t * 6 + i * 256 / 6, ox, oy;
            rn_map(rc(a) * 15 / 256, rs(a) * 15 / 256, sx, sy, 0, c->path, &ox, &oy);
            int depth = -rc(a) * c->dir;
            rn_xf(rn_glyph(gx + ox, gy + oy, RG_RAIDO, depth >= 0 ? RB_EL : RB_EL_MID, rn_prio(depth), depth), 200,
                  200, 0, 0);
        }
    }
    if (t == 2) sfx_play(SFX_SPARKLE);
    /* the dash */
    int l = lunge(t, 12, 7, 5, 16, 46);
    anim.mon_dx[side] = c->dir * l;
    anim.mon_dy[side] = -c->dir * l / 3;
    anim.afterimage = t >= 12 && t < 24;
    if (t >= 12 && t < 20) {
        anim.scale_x[side] = 296;
        anim.scale_y[side] = 222;
        if (t == 13) {
            sfx_play(SFX_WIND);
            rn_burst(gx, gy, 8, 26, 0, 0);
        }
        /* rune streaks racing ahead */
        for (int k = 0; k < 3; k++) {
            int u = ((t - 12) * 40 + k * 70) % 256;
            int x = rn_lerp(gx, c->dx, u), y = rn_lerp(gy, c->dy, u) + (k - 1) * 10;
            rn_xf(rn_glyph(x, y, RG_RAIDO, RB_EL, 1, 0), 300, 180, 0, c->path + 64);
        }
    }
    if (impact_when(19, c->st, c->dx, c->dy)) rn_burst(c->dx - c->dir * 8, c->dy, 8, 30, 1, 1);
    if (t >= 19 && t < 34 && (t < 28 || (t & 1))) {
        int sc = 140 + ease_out(t - 19, 12) * 300 / 256;
        rn_xf(rn_add(RN_G32, c->dx - c->dir * 6, c->dy, RN_OT + RT_RING, RB_EL, 1, 10), sc * 160 / 256, sc, t * 4,
              c->path);
    }
}

/* ISA SEAL: an ice seal forms before the foe spinning like a coin, slows
 * to face it, slams on; crystals grow out of the foe and shatter. */
static void rn_isa(const RnCtx *c)
{
    int t = c->t, foe = c->foe;
    int cx = c->dx - c->dir * 4, cy = c->dy - 8;
    anim.bg_amount = t < 62 ? 6 : 0;
    anim.bg_color = RGB15(8, 16, 30);
    if (t < 14 && (t & 1)) {
        int a = fx_rand(256);
        rn_part(RNP_SPARK, cx + rc(a) * 40 / 256, cy + rs(a) * 30 / 256, -rc(a) * 3 / 64, -rs(a) * 3 / 64, 12, 0,
                RB_EL);
    }
    if (t == 4) sfx_play(SFX_ICE);
    if (t >= 4 && t < 36) {
        int rt = t - 4;
        int s = rn_persp(foe) * 360 / 210 * ease_out(rt, 12) / 256;
        if (t >= 30) s = clampi(s + (t - 30) * 36, 0, 500);
        /* the yaw slows from a blur to face-on at rt = 26 */
        int left = rt < 26 ? 26 - rt : 0;
        int yaw = left * left * 3 / 2;
        int sx = s * rc(yaw) / 256;
        int bank = sx >= 0 ? RB_EL : RB_EL_MID;
        RnItem *it = rn_add(RN_G32, cx, cy, RN_OT + RT_SEAL, bank, 1, 0);
        rn_xf(it, sx, s, rt * 3, 0);
        if (it && t >= 30) it->flags = ATTR0_BLEND;
        if (t < 32) rn_xf(rn_hero(cx, cy, RH_ISA, bank, 1, 5), sx * 200 / 256, s * 200 / 256, 0, 0);
    }
    if (impact_when(32, c->st, c->dx, c->dy)) sfx_play(SFX_ICE);
    if (t >= 32) {
        int ft = t - 32;
        anim.tint_side = foe;
        anim.tint_color = RGB15(22, 28, 31);
        anim.tint_amount = ft < 26 ? 13 : 13 - (ft - 26);
        anim.scale_x[foe] = ft < 26 ? 262 : 256;
        if (ft < 20) rn_ground(c->dx, c->fgy, RT_RING, RB_EL, 220 + ft * 16, 100, ft * 2, ft > 12);
        if (ft < 26) {
            for (int i = 0; i < 8; i++) {
                int a = i * 32 + 12 + (i & 1) * 6;
                int depth = (i & 2) ? 60 : -60;
                int len = (i & 1) ? 200 : 270;
                int hh = len * ease_out(ft - (i & 3), 8) / 256;
                if (hh < 16) continue;
                /* a crystal grows out of the centre along angle a */
                int d = 16 * hh / 256;
                RnItem *it = rn_add(RN_TALL, c->dx + (rc(a) * d >> 8), c->dy - 6 + (rs(a) * d >> 8), RN_OT + RT_SPIKE,
                                    depth >= 0 ? RB_EL : RB_EL_MID, rn_prio(depth), depth);
                rn_xf(it, 180, hh, 0, a + 64);
            }
        }
        if (ft == 26) {
            sfx_play(SFX_ICE);
            for (int k = 0; k < 12; k++) {
                int a = k * 21 + fx_rand(10), sp = 24 + fx_rand(16);
                rn_part(RNP_SPARK, c->dx + rc(a) * 16 / 256, c->dy - 6 + rs(a) * 16 / 256, rc(a) * sp / 256,
                        rs(a) * sp / 256 - 10, 16 + fx_rand(8), 3, RB_EL);
            }
        }
        if (ft >= 26 && ft < 40 && (ft & 1))
            for (int k = 0; k < 5; k++)
                rn_add(RN_SPARK8, c->dx + rc(k * 51 + ft * 9) * (ft - 18) / 256,
                       c->dy - 6 + rs(k * 51 + ft * 9) * (ft - 18) / 256, RN_OT + RT_SPARK + RS_SHARD, RB_EL, 1, 0);
    }
}

/* SOWILO BEAM: a sun circle stands across the path, turning fast with the
 * SOWILO rune at its heart; a beam of light joins it to the foe. */
static void rn_sowilo(const RnCtx *c)
{
    int t = c->t, side = c->side, foe = c->foe;
    int ox = c->sx + c->dir * 22, oy = c->sy - 14;
    int grow = t < 48 ? ease_out(t, 12) : 256 - ease_in(t - 48, 14);
    anim.bg_amount = t < 52 ? 6 : 0;
    anim.bg_color = RGB15(31, 22, 6);
    if (t == 2) sfx_play(SFX_CHARGE);
    if (grow > 8) {
        int s = rn_persp(side) * 5 / 4 * grow / 256;
        rn_gate(c, ox, oy, RT_SEAL, RB_EL, s, t * (t < 16 ? t / 2 : 8));
        rn_xf(rn_hero(ox, oy, RH_SOWILO, RB_EL, 1, 0), s * 140 / 256, s * 200 / 256, 0, rs(t * 4) / 40);
        rn_ground(c->sx, c->ugy, RT_CIRCLE, RB_ARC, s * 3 / 2, 90, -t * 4, 1);
    }
    if (t < 16 && (t & 1)) {
        int a = fx_rand(256);
        rn_part(RNP_SPARK, ox + rc(a) * 36 / 256, oy + rs(a) * 36 / 256, -rc(a) / 20, -rs(a) / 20, 12, 0, RB_EL);
    }
    if (t >= 16 && t < 50) {
        int bt = t - 16;
        int reach = ease_out(bt, 6);
        int w = bt < 26 ? 260 + rs(t * 36) * 40 / 256 : 260 - (bt - 26) * 32;
        int ex = c->dx, ey = c->dy - 4;
        int ang = rn_angle_of(ey - oy, -(ex - ox));
        int ddx = ex - ox, ddy = ey - oy, len = 0;
        while (len * len < ddx * ddx + ddy * ddy) len++;
        int segs = len / 24 + 1;
        if (w > 20)
            for (int k = 0; k < segs; k++) {
                int u = (k * 256 + 128) / segs;
                if (u > reach) break;
                int ps = rn_lerp(rn_persp(side), rn_persp(foe), u);
                RnItem *it = rn_add(RN_TALL, rn_lerp(ox, ex, u), rn_lerp(oy, ey, u), RN_OT + RT_BEAM, RB_EL, 1, -5);
                rn_xf(it, w * ps / 256, len * 8 / segs + 12, 0, ang);
            }
        /* bright nodes running down the beam */
        if (reach >= 256 && bt < 30)
            for (int k = 0; k < 3; k++) {
                int u = (bt * 24 + k * 85) & 255;
                rn_spark(rn_lerp(ox, ex, u), rn_lerp(oy, ey, u), RS_STAR, RB_EL, 1);
            }
    }
    if (impact_when(22, c->st, c->dx, c->dy)) rn_burst(c->dx, c->dy - 4, 8, 28, 0, 1);
    if (t >= 22 && t < 50) {
        int ft = t - 22;
        int sc = 220 + rs(t * 20) * 40 / 256;
        rn_xf(rn_add(RN_G32, c->dx, c->dy - 4, RN_OT + RT_RING, RB_EL, 1, 20), sc * 170 / 256, sc, ft * 9, c->path);
        anim.tint_side = foe;
        anim.tint_amount = ft < 20 ? 11 : 4;
        if ((ft & 3) == 0) rn_rise(c->dx, c->fgy, 22, 1, RB_EL);
    }
}

/* RUNE SIPHON: circles open under both kin; a ribbon of motes and runes is
 * drawn out of the foe along a helix round the flight line (in depth: in
 * front bright, behind see-through) and sinks into the user, who glows. */
static void rn_siphon(const RnCtx *c)
{
    int t = c->t, side = c->side, foe = c->foe;
    int op = t < 66 ? ease_out(t, 12) : 256 - (t - 66) * 18;
    if (op > 10) {
        rn_ground(c->dx, c->fgy, RT_CIRCLE, RB_ARC, 460 * op / 256, 100, t * 4, 1);
        rn_ground(c->sx, c->ugy, RT_SEAL, RB_EL, 500 * op / 256, 96, -t * 3, 1);
    }
    if (t == 4) sfx_play(SFX_DRAIN);
    if (impact_when(14, c->st, c->dx, c->dy)) rn_rise(c->dx, c->fgy, 24, 4, RB_EL);
    if (t >= 12 && t < 52) {
        anim.tint_side = foe;
        anim.tint_amount = 7 + ((t >> 2) & 1) * 3;
    }
    /* the ribbon itself: see-through light along the arc */
    if (t >= 14 && t < 60) {
        int w = (t < 22 ? (t - 14) * 26 : t < 52 ? 200 : 200 - (t - 52) * 24) + rs(t * 24) * 30 / 256;
        int reach = ease_out(t - 14, 10);
        int px = c->dx, py = c->dy - 4;
        for (int k = 1; k <= 6; k++) {
            int u = k * 256 / 6;
            if (u - 43 > reach) break;
            int qx = rn_lerp(c->dx, c->sx, u), qy = rn_lerp(c->dy - 4, c->sy - 8, u) - rs(u / 2) * 30 / 256;
            int ddx = qx - px, ddy = qy - py, len = 0;
            while (len * len < ddx * ddx + ddy * ddy) len++;
            RnItem *it = rn_add(RN_TALL, (px + qx) / 2, (py + qy) / 2, RN_OT + RT_BEAM, RB_EL, 1, -20);
            rn_xf(it, w * rn_lerp(rn_persp(foe), rn_persp(side), u) / 256, len * 8 + 16, 0, rn_angle_of(ddy, -ddx));
            if (it) it->flags = ATTR0_BLEND;
            px = qx, py = qy;
        }
    }
    for (int i = 0; i < 22; i++) {
        int rt = t - 12 - i * 2;
        if (rt < 0 || rt >= 28) continue;
        int u = rn_smooth(rt, 28);
        int bx = rn_lerp(c->dx, c->sx, u), by = rn_lerp(c->dy - 4, c->sy - 8, u) - rs(u / 2) * 30 / 256;
        int ph = rt * 14 + i * 40, r = 3 + rs(u / 2) * 12 / 256;
        int depth = rs(ph);
        int x = bx + rc(ph) * r / 256, y = by + rc(ph) * r / 512 - depth * r / 1024;
        int s = rn_lerp(rn_persp(foe), rn_persp(side), u) * (256 + depth / 4) / 256;
        int bank = depth >= 0 ? RB_EL : RB_EL_MID;
        if (i % 3 == 1)
            rn_xf(rn_glyph(x, y, RG_ANSUZ + i, bank, rn_prio(depth), depth), s * rc(rt * 10) / 256, s, 0, 0);
        else
            rn_add(RN_SPARK8, x, y, RN_OT + RT_SPARK + (i & 1 ? RS_MOTE : RS_STAR), bank, rn_prio(depth), depth);
    }
    if (t >= 38) {
        int gt = t - 38;
        anim.tint_side = side;
        anim.tint_color = RGB15(28, 24, 31);
        anim.tint_amount = gt < 24 ? 3 + gt / 4 : 9 - (gt - 24) / 2;
        if ((gt & 3) == 0) rn_rise(c->sx, c->ugy, 24, 2, RB_EL);
    }
    if (t >= 56 && t < 76 && (t < 70 || (t & 1))) {
        int sc = 480 - ease_in(t - 56, 18) * 320 / 256;
        RnItem *it = rn_add(RN_G32, c->sx, c->sy - 8, RN_OT + RT_RING, RB_EL, 1, 30);
        rn_xf(it, sc, sc, -t * 5, 0);
        if (it) it->flags = ATTR0_BLEND;
    }
    if (t == 62) {
        squash(side, 276, 236);
        sfx_play(SFX_HEAL);
    }
}

/* One frame of a RUNE move (from anim_move_frame's default case). */
static void anim_rune_frame(void)
{
    if (anim.kind < AK_RUNE_BOLT || anim.kind >= AK_COUNT) return;
    if (anim.t == 0) {
        copy32(VRAM_OBJ_TILES + RN_OT * 8, rune_gfx, RT_TILE_COUNT * 8);
        for (int i = 0; i < RN_PARTS; i++) rn_parts[i].life = 0;
    }
    rn_palettes(anim.kind);
    rn_count = 0;
    RnCtx c;
    c.t = anim.t;
    c.side = anim.side;
    c.foe = !anim.side;
    c.dir = c.side == SIDE_ALLY ? 1 : -1;
    c.st = move_strength();
    c.sx = side_cx(c.side);
    c.sy = side_cy(c.side);
    c.dx = side_cx(c.foe);
    c.dy = side_cy(c.foe);
    c.ugy = rn_gy(c.side);
    c.fgy = rn_gy(c.foe);
    c.path = rn_angle_of(c.dx - c.sx, c.dy - c.sy);
    rn_parts_step(feel.hitstop > 0);
    switch (anim.kind) {
    case AK_RUNE_BOLT: rn_bolt(&c); break;
    case AK_SIGIL_SNARE: rn_snare(&c); break;
    case AK_ALGIZ_WARD: rn_ward(&c); break;
    case AK_KENAZ_FLARE: rn_kenaz(&c); break;
    case AK_RUNE_ORBIT: rn_orbit(&c); break;
    case AK_THURS_SPIKE: rn_thurs(&c); break;
    case AK_RAIDO_RUSH: rn_raido(&c); break;
    case AK_ISA_SEAL: rn_isa(&c); break;
    case AK_SOWILO_BEAM: rn_sowilo(&c); break;
    case AK_RUNE_SIPHON: rn_siphon(&c); break;
    }
    rn_flush();
}
