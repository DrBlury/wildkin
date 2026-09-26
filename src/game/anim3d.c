/*
 * Pseudo-3D toolkit for the battle animations (anim.c includes nothing
 * from here it could not do itself; main.c includes this file first).
 *
 * The bout is seen by a camera standing behind the ally: the ally is near
 * (back-left, low, big), the foe is far (front-right, high, smaller). This
 * file gives that scene a world space plus the pieces the move animations
 * are built from; everything is integer / 8.8 fixed point with tables.
 *
 * World space (units are pixels at the ally's depth):
 *   X to the right, Y up from the ground, Z away from the camera
 *   screen x = W3_VX + X * s / 256,  screen y = W3_VY + (W3_HC - Y) * s / 256
 *   with s = 65536 / Z the perspective scale (8.8: ally 256, foe 179).
 * The ally stands at (-48, 0, 256), the foe at (80, 0, 366); their centres
 * are 32 / 40 units up, so the projections of w3_side_* land exactly on
 * anim.c's side_cx / side_cy / side_gy.
 *
 *   w3_scale(z)                     perspective scale (8.8) of depth z
 *   w3_proj(x, y, z, &sx, &sy)      world -> screen with the camera applied;
 *                                   returns the scale
 *   w3_spr_scale(s)                 how big a particle is drawn at scale s:
 *                                   gentler than true perspective so a 16x16
 *                                   particle stays readable far away
 *   w3_side_x/z/h(side)             where a battler stands; h = its centre
 *   w3_path(from, to, k, arc, ...)  a point k/256 of the way between two
 *                                   battlers' centres, lifted by a parabola
 *                                   (projectiles grow or shrink in flight)
 *   w3_ground_squash(z)             vertical squash (8.8) of a circle lying on
 *                                   the ground at depth z
 *   w3_floor(z)                     the drawn ground height there (lifted near
 *                                   the foe, whose feet the ally's HUD hides)
 *   a3_sin / a3_cos                 true sine, amplitude 256, 256 steps a turn
 *   a3_affine(sx, sy, rot)          OBJ matrix "scale, then rotate" from a
 *                                   per-frame cache: particles with the same
 *                                   (quantised) scale and angle share one.
 *                                   The animations take at most A3_AFF_CAP of
 *                                   the 32, so the battlers (and the HUD
 *                                   sparkles) always get theirs; past the cap
 *                                   the nearest cached matrix is reused (or,
 *                                   if none is close, a plain sprite).
 *   a3_affine_flat(sx, sy, rot)     a flat image turned in its own plane,
 *                                   then squashed: rings and vortices lying on
 *                                   the ground
 *   camera: a3_cam_x / a3_cam_y (sway, px at the ally's depth) and
 *     a3_cam_zoom (8.8 punch-in about A3_FOCUS). Sprites get it through
 *     w3_proj / a3_cam_apply (parallax: near things move more), the
 *     battlers through a3_cam_battler and BG0 per line through a3_cam_line
 *     (the ground slides with its depth, the sky barely moves).
 *   back layer: between a3_back_begin() and a3_back_end() sprites are
 *     queued instead of pushed; a3_flush_back() pushes them after the
 *     battlers, so they are drawn under them (the far half of an orbit,
 *     ground shadows). Lower OAM index wins between sprites, whatever their
 *     priority bits, hence the queue.
 */

#define W3_VX 120
#define W3_VY (-23)
#define W3_HC 133
#define W3_ZMIN 96

static const s16 A3_SIN[256] = {
    0, 6, 13, 19, 25, 31, 38, 44, 50, 56, 62, 68, 74, 80, 86, 92,
    98, 104, 109, 115, 121, 126, 132, 137, 142, 147, 152, 157, 162, 167, 172, 177,
    181, 185, 190, 194, 198, 202, 206, 209, 213, 216, 220, 223, 226, 229, 231, 234,
    237, 239, 241, 243, 245, 247, 248, 250, 251, 252, 253, 254, 255, 255, 256, 256,
    256, 256, 256, 255, 255, 254, 253, 252, 251, 250, 248, 247, 245, 243, 241, 239,
    237, 234, 231, 229, 226, 223, 220, 216, 213, 209, 206, 202, 198, 194, 190, 185,
    181, 177, 172, 167, 162, 157, 152, 147, 142, 137, 132, 126, 121, 115, 109, 104,
    98, 92, 86, 80, 74, 68, 62, 56, 50, 44, 38, 31, 25, 19, 13, 6,
    0, -6, -13, -19, -25, -31, -38, -44, -50, -56, -62, -68, -74, -80, -86, -92,
    -98, -104, -109, -115, -121, -126, -132, -137, -142, -147, -152, -157, -162, -167, -172, -177,
    -181, -185, -190, -194, -198, -202, -206, -209, -213, -216, -220, -223, -226, -229, -231, -234,
    -237, -239, -241, -243, -245, -247, -248, -250, -251, -252, -253, -254, -255, -255, -256, -256,
    -256, -256, -256, -255, -255, -254, -253, -252, -251, -250, -248, -247, -245, -243, -241, -239,
    -237, -234, -231, -229, -226, -223, -220, -216, -213, -209, -206, -202, -198, -194, -190, -185,
    -181, -177, -172, -167, -162, -157, -152, -147, -142, -137, -132, -126, -121, -115, -109, -104,
    -98, -92, -86, -80, -74, -68, -62, -56, -50, -44, -38, -31, -25, -19, -13, -6,
};

/* s = 65536 / z for z = W3_ZMIN + 2 * i */
static const u16 W3_PERSP[256] = {
    683, 669, 655, 643, 630, 618, 607, 596, 585, 575, 565, 555, 546, 537, 529, 520,
    512, 504, 496, 489, 482, 475, 468, 462, 455, 449, 443, 437, 431, 426, 420, 415,
    410, 405, 400, 395, 390, 386, 381, 377, 372, 368, 364, 360, 356, 352, 349, 345,
    341, 338, 334, 331, 328, 324, 321, 318, 315, 312, 309, 306, 303, 301, 298, 295,
    293, 290, 287, 285, 282, 280, 278, 275, 273, 271, 269, 266, 264, 262, 260, 258,
    256, 254, 252, 250, 248, 246, 245, 243, 241, 239, 237, 236, 234, 232, 231, 229,
    228, 226, 224, 223, 221, 220, 218, 217, 216, 214, 213, 211, 210, 209, 207, 206,
    205, 204, 202, 201, 200, 199, 197, 196, 195, 194, 193, 192, 191, 189, 188, 187,
    186, 185, 184, 183, 182, 181, 180, 179, 178, 177, 176, 175, 174, 173, 172, 172,
    171, 170, 169, 168, 167, 166, 165, 165, 164, 163, 162, 161, 161, 160, 159, 158,
    158, 157, 156, 155, 155, 154, 153, 152, 152, 151, 150, 150, 149, 148, 148, 147,
    146, 146, 145, 144, 144, 143, 142, 142, 141, 141, 140, 139, 139, 138, 138, 137,
    137, 136, 135, 135, 134, 134, 133, 133, 132, 132, 131, 131, 130, 130, 129, 129,
    128, 128, 127, 127, 126, 126, 125, 125, 124, 124, 123, 123, 122, 122, 121, 121,
    120, 120, 120, 119, 119, 118, 118, 117, 117, 117, 116, 116, 115, 115, 115, 114,
    114, 113, 113, 113, 112, 112, 111, 111, 111, 110, 110, 110, 109, 109, 109, 108,
};

static int a3_sin(int a) { return A3_SIN[a & 255]; }
static int a3_cos(int a) { return A3_SIN[(a + 64) & 255]; }

/* ---------------- camera ---------------- */

static int a3_cam_x, a3_cam_y;   /* sway, px at the ally's depth */
static int a3_cam_zoom = 256;    /* 8.8 punch-in about (A3_FOCUS_X, A3_FOCUS_Y) */
#define A3_FOCUS_X 124
#define A3_FOCUS_Y 70

static int a3_cam_moved(void) { return a3_cam_x || a3_cam_y || a3_cam_zoom != 256; }

/* ---------------- world ---------------- */

static int w3_scale(int z)
{
    int i = (z - W3_ZMIN) >> 1;
    return W3_PERSP[i < 0 ? 0 : i > 255 ? 255 : i];
}

static int w3_side_x(int side) { return side == SIDE_ENEMY ? 80 : -48; }
static int w3_side_z(int side) { return side == SIDE_ENEMY ? 366 : 256; }
static int w3_side_h(int side) { return side == SIDE_ENEMY ? 40 : 32; }

/* Camera sway and zoom for a point drawn at perspective scale s. */
static void a3_cam_apply(int *x, int *y, int s)
{
    if (!a3_cam_moved()) return;
    *x += (a3_cam_x * s) >> 8;
    *y += (a3_cam_y * s) >> 8;
    if (a3_cam_zoom != 256) {
        *x = A3_FOCUS_X + (((*x - A3_FOCUS_X) * a3_cam_zoom) >> 8);
        *y = A3_FOCUS_Y + (((*y - A3_FOCUS_Y) * a3_cam_zoom) >> 8);
    }
}

/* Perspective scale of the ground seen at screen line y. */
static int a3_line_scale(int y)
{
    int s = ((y - W3_VY) * 493) >> 8;            /* (y - VY) * 256 / HC */
    return s < 64 ? 64 : s;
}

static int w3_proj(int x, int y, int z, int *px, int *py)
{
    int s = w3_scale(z);
    *px = W3_VX + ((x * s) >> 8);
    *py = W3_VY + (((W3_HC - y) * s) >> 8);
    a3_cam_apply(px, py, s);
    return a3_cam_zoom == 256 ? s : (s * a3_cam_zoom) >> 8;
}

/* How big a particle is drawn at perspective scale s (8.8). */
static int w3_spr_scale(int s) { return s + 48; }

static void w3_path(int from, int to, int k, int arc, int *x, int *y, int *z)
{
    int x0 = w3_side_x(from), y0 = w3_side_h(from), z0 = w3_side_z(from);
    int x1 = w3_side_x(to), y1 = w3_side_h(to), z1 = w3_side_z(to);
    *x = x0 + (((x1 - x0) * k) >> 8);
    *z = z0 + (((z1 - z0) * k) >> 8);
    *y = y0 + (((y1 - y0) * k) >> 8) + ((arc * k * (256 - k)) >> 14);
}

/* The drawn ground height at depth z. The ally's HUD box covers the foe's
 * feet, so near the foe things lying on the ground (rings, shadows,
 * bouncing debris) are drawn up to 12 units higher, where they show. */
static int w3_floor(int z)
{
    int f = ((z - 300) * 186) >> 10;
    return f < 0 ? 0 : f > 12 ? 12 : f;
}

/* A circle on the ground at depth z looks squashed by about HC / z (drawn a
 * little rounder than true, it reads better at 240x160). */
static int w3_ground_squash(int z) { return (w3_scale(z) * 166) >> 8; }   /* HC * 1.25 / z */

/* ---------------- affine matrices ---------------- */

/*
 * The cache is a small open-addressed hash keyed by the quantised
 * transform: scales in 1/16 steps from -4x to 4x, angles in 32 steps (fine
 * for 16x16 particles, and it lets many share). Entries belong to a frame
 * (epoch, bumped by a3_frame_begin() at the start of every drawn animation
 * step); a hit is also checked against this frame's OAM shadow, and if
 * oam_begin() ran without a new epoch the cache starts over. The
 * reciprocals are a table: no divisions. The last lookup is remembered, as
 * runs of equal transforms are common.
 */
#define A3_AFF_CAP 24
#define A3_HASH 32
EWRAM_BSS static struct { u32 key; s16 pa, pd; s8 idx; u8 epoch; } a3_aff[A3_HASH];   /* IWRAM is kept for the stack */
static u8 a3_used[A3_AFF_CAP];   /* the slots filled this frame */
static int a3_aff_n;             /* matrices the animations took this frame */
static u8 a3_epoch = 1;
static u32 a3_last_key = 0xFFFFFFFFu;
static int a3_last_slot;

/* 65536 / (q * 16 - 1024) */
static const s16 A3_RECIP[128] = {
    -64, -65, -66, -67, -68, -69, -70, -71, -73, -74, -75, -77, -78, -80, -81, -83,
    -85, -87, -89, -91, -93, -95, -97, -99, -102, -105, -107, -110, -113, -117, -120, -124,
    -128, -132, -136, -141, -146, -151, -157, -163, -170, -178, -186, -195, -204, -215, -227, -240,
    -256, -273, -292, -315, -341, -372, -409, -455, -512, -585, -682, -819, -1024, -1365, -2048, -4096,
    4096, 4096, 2048, 1365, 1024, 819, 682, 585, 512, 455, 409, 372, 341, 315, 292, 273,
    256, 240, 227, 215, 204, 195, 186, 178, 170, 163, 157, 151, 146, 141, 136, 132,
    128, 124, 120, 117, 113, 110, 107, 105, 102, 99, 97, 95, 93, 91, 89, 87,
    85, 83, 81, 80, 78, 77, 75, 74, 73, 71, 70, 69, 68, 67, 66, 65,
};

static void a3_frame_begin(void)
{
    a3_aff_n = 0;
    a3_last_key = 0xFFFFFFFFu;
    if (++a3_epoch == 0) a3_epoch = 1;
}

static int a3_aff_valid(int i)
{
    int n = a3_aff[i].idx;
    return n < oam_affine_count && oam_shadow[(n * 4 + 0) * 4 + 3] == (u16)a3_aff[i].pa &&
           oam_shadow[(n * 4 + 3) * 4 + 3] == (u16)a3_aff[i].pd;
}

static int a3_quant(int v)
{
    int q = (v + 1032) >> 4;
    if (q < 1) q = 1;
    else if (q > 127) q = 127;
    if (q == 64) q = v < 0 ? 63 : 65;
    return q;
}

static int a3_matrix(int kind, int sx, int sy, int rot)
{
    int qx = a3_quant(sx), qy = a3_quant(sy), qr = ((rot + 4) >> 3) & 31;
    u32 key = (u32)qx | ((u32)qy << 7) | ((u32)qr << 14) | ((u32)kind << 19);
    if (key == a3_last_key && a3_aff_valid(a3_last_slot)) return a3_aff[a3_last_slot].idx;
    int h = (int)((key * 2654435761u) >> 27);
    while (a3_aff[h].epoch == a3_epoch) {
        if (a3_aff[h].key == key) {
            if (a3_aff_valid(h)) {
                a3_last_key = key;
                a3_last_slot = h;
                return a3_aff[h].idx;
            }
            a3_frame_begin();                        /* a new frame we were not told about */
            break;
        }
        h = (h + 1) & (A3_HASH - 1);
    }
    if (a3_aff_n >= A3_AFF_CAP || oam_affine_count >= 30) {
        /* out of matrices: the closest one of the same kind this frame, if close enough */
        int best = -1, bestd = 8;
        for (int i = 0; i < a3_aff_n; i++) {
            u32 k = a3_aff[a3_used[i]].key;
            if ((int)(k >> 19) != kind) continue;
            int dr = absi((int)((k >> 14) & 31) - qr);
            if (dr > 16) dr = 32 - dr;
            int d = absi((int)(k & 127) - qx) + absi((int)((k >> 7) & 127) - qy) + dr;
            if (d < bestd) bestd = d, best = a3_aff[a3_used[i]].idx;
        }
        return best;
    }
    while (a3_aff[h].epoch == a3_epoch) h = (h + 1) & (A3_HASH - 1);
    int s = A3_SIN[(qr << 3) & 255], c = A3_SIN[((qr << 3) + 64) & 255];
    int ix = A3_RECIP[qx], iy = A3_RECIP[qy];
    int pa = (c * ix) >> 8, pd = (c * iy) >> 8, pb, pc;
    if (kind) {         /* flat: turn in its own plane, then squash */
        pb = (s * iy) >> 8;
        pc = (-s * ix) >> 8;
    } else {            /* scale, then rotate */
        pb = (s * ix) >> 8;
        pc = (-s * iy) >> 8;
    }
    int n = oam_affine(pa, pb, pc, pd);
    if (n < 0) return -1;
    a3_aff[h].key = key;
    a3_aff[h].idx = (s8)n;
    a3_aff[h].pa = (s16)pa;
    a3_aff[h].pd = (s16)pd;
    a3_aff[h].epoch = a3_epoch;
    a3_used[a3_aff_n++] = (u8)h;
    a3_last_key = key;
    a3_last_slot = h;
    return n;
}

static int a3_affine(int sx, int sy, int rot) { return a3_matrix(0, sx, sy, rot); }
static int a3_affine_flat(int sx, int sy, int rot) { return a3_matrix(1, sx, sy, rot); }

/* ---------------- the back layer ---------------- */

#define A3_BACK_MAX 40
EWRAM_BSS static u16 a3_back[A3_BACK_MAX][3];   /* OAM attributes 0..2 */
static int a3_back_n, a3_layer_back;
static int a3_defer_back;        /* set by battle_draw: it flushes after the battlers */

static void a3_back_begin(void) { a3_layer_back = 1; }
static void a3_back_end(void) { a3_layer_back = 0; }

/*
 * Push a particle sprite (SQ16 or SQ32, priority 1; aff < 0 = plain, dbl =
 * double-size box centred on the same point), or queue it while the back
 * layer is open. The attributes are built here directly (the particles
 * are the bulk of a busy frame's sprites).
 */
static void a3_push(int x, int y, int tile, int shape, int bank, int flags, int aff, int dbl)
{
    int w = shape == SQ32 ? 32 : 16;
    u16 a0, a1 = (u16)(shape == SQ32 ? ATTR1_SIZE(2) : ATTR1_SIZE(1));
    if (aff >= 0) {
        if (dbl) {
            x -= w >> 1;
            y -= w >> 1;
            w <<= 1;
        }
        a0 = (u16)(ATTR0_AFFINE | (dbl ? ATTR0_DOUBLE : 0));
        a1 |= (u16)((aff & 31) << 9);
    } else {
        a0 = 0;
        a1 |= (u16)(flags & (ATTR1_HFLIP | ATTR1_VFLIP));
    }
    if (x <= -w || x >= SCREEN_WIDTH || y <= -w || y >= SCREEN_HEIGHT) return;
    a0 |= (u16)((y & 0xFF) | (flags & ATTR0_BLEND));
    a1 |= (u16)(x & 0x1FF);
    u16 a2 = (u16)(tile | ATTR2_PRIO(1) | ATTR2_BANK(bank));
    u16 *o;
    if (a3_layer_back) {
        if (a3_back_n >= A3_BACK_MAX) return;
        o = a3_back[a3_back_n++];
    } else {
        if (oam_count >= 128) return;
        o = &oam_shadow[oam_count++ * 4];
    }
    o[0] = a0;
    o[1] = a1;
    o[2] = a2;
}

static void a3_flush_back(void)
{
    for (int i = 0; i < a3_back_n && oam_count < 128; i++) {
        u16 *o = &oam_shadow[oam_count++ * 4];
        o[0] = a3_back[i][0];
        o[1] = a3_back[i][1];
        o[2] = a3_back[i][2];
    }
    a3_back_n = 0;
}

/* ---------------- camera hooks for battle_ui.c ---------------- */

/* BG0 offsets for screen line y under the camera. */
static void a3_cam_line(int y, int *hx, int *vy)
{
    static int zoom_of = 256, zoom_inv = 256;    /* 65536 / zoom, worked out once a frame */
    if (!a3_cam_moved()) return;
    int s = y < 24 ? 72 : a3_line_scale(y);      /* the sky is far away */
    *hx -= (a3_cam_x * s) >> 8;
    *vy -= (a3_cam_y * s) >> 8;
    if (a3_cam_zoom != 256) {                    /* vertical punch-in */
        if (zoom_of != a3_cam_zoom) zoom_of = a3_cam_zoom, zoom_inv = 65536 / a3_cam_zoom;
        *vy += (((y - A3_FOCUS_Y) * zoom_inv) >> 8) - (y - A3_FOCUS_Y);
    }
}

/* A battler under the camera: x, y = top-left of its 64x64 sprite (before
 * battle_draw_battlers plants the feet for the scale), sx, sy its scale. */
static void a3_cam_battler(int side, int *x, int *y, int *sx, int *sy)
{
    if (!a3_cam_moved()) return;
    int s = side == SIDE_ENEMY ? 179 : 256;
    int fx = *x + 32, fy = *y + 64;
    a3_cam_apply(&fx, &fy, s);
    *sx = (*sx * a3_cam_zoom) >> 8;
    *sy = (*sy * a3_cam_zoom) >> 8;
    *x = fx - 32;
    *y = fy - 64;
}
