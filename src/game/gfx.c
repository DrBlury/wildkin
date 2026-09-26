/*
 * Graphics services shared by every screen.
 *
 * UI canvas: BG1 shows a 240x160 bitmap built from 600 unique 8x8 tiles
 * (one per screen cell). Everything -- window frames, variable-width text
 * with drop shadows, HP bars, icons -- is drawn into a RAM copy that is
 * DMA'd to VRAM during vblank, only for the rows that changed. Each cell
 * has its own palette bank so badges and icons can use their own colors.
 *
 * Sprites: a shadow OAM rebuilt every frame (front-most sprite first) and
 * copied to hardware in vblank.
 */

/* ---------------- palette banks ---------------- */

#define BANK_UI_STD     15
#define BANK_UI_BATTLE  14
#define BANK_UI_HUD     13
#define BANK_TYPE_A     12
#define BANK_TYPE_B     11
#define BANK_ITEM_ICON  10
#define BANK_MENU_BG     9
#define BANK_UI_BAR      8   /* STD colors + HP/EXP bar colors (menus) */

#define OBANK_PLAYER     0
#define OBANK_NPC        1   /* 1..7; party icons reuse 1..6 in menus */
#define OBANK_ITEM_BALL  8
#define OBANK_CAPSULE    9
#define OBANK_MON_A     10
#define OBANK_MON_B     11
#define OBANK_FX_A      12
#define OBANK_FX_B      13
#define OBANK_FX_HIT    14

/* ---------------- OBJ VRAM tile layout ---------------- */

#define OT_PLAYER       0
#define OT_NPC(i)       (8 + (i) * 8)     /* 15 people */
#define OT_ITEM_BALL    128
#define OT_ICON(i)      (132 + (i) * 16)  /* 6 party icons, 32x32 */
#define OT_MON_A        256
#define OT_MON_B        320
#define OT_CAPSULE      384
#define OT_FX           400               /* FX_COUNT x 4 tiles */

/* ---------------- canvas ---------------- */

#define CANVAS_COLS  30
#define CANVAS_ROWS  20
#define CANVAS_CELLS (CANVAS_COLS * CANVAS_ROWS)
#define PANEL_TILE_BASE CANVAS_CELLS

EWRAM_BSS static u32 canvas[CANVAS_CELLS * 8];
static u8 canvas_banks[CANVAS_CELLS];
static int canvas_dirty_lo = 0, canvas_dirty_hi = CANVAS_ROWS - 1;
static int canvas_banks_dirty = 1;

/* nib_lut[b]: 8 pixels (bit 7 = leftmost) expanded to 4bpp nibble masks. */
static u32 nib_lut[256];

static void gfx_init_tables(void)
{
    for (int b = 0; b < 256; b++) {
        u32 m = 0;
        for (int px = 0; px < 8; px++)
            if (b & (0x80 >> px)) m |= 15u << (px * 4);
        nib_lut[b] = m;
    }
}

/* Current pixel-drawing target: the canvas, or a small off-screen strip
 * (used to render catalogue panel lines before copying them to VRAM). */
static u32 *tgt_px = canvas;
static int tgt_cols = CANVAS_COLS, tgt_w = SCREEN_WIDTH, tgt_h = SCREEN_HEIGHT;

static void target_set(u32 *px, int cols, int rows)
{
    tgt_px = px;
    tgt_cols = cols;
    tgt_w = cols * 8;
    tgt_h = rows * 8;
}

static void target_canvas(void)
{
    target_set(canvas, CANVAS_COLS, CANVAS_ROWS);
}

static void canvas_mark_rows(int r0, int r1)
{
    if (tgt_px != canvas) return;
    if (r0 < 0) r0 = 0;
    if (r1 >= CANVAS_ROWS) r1 = CANVAS_ROWS - 1;
    if (r0 < canvas_dirty_lo) canvas_dirty_lo = r0;
    if (r1 > canvas_dirty_hi) canvas_dirty_hi = r1;
}

static void canvas_mark_px(int y0, int y1)
{
    canvas_mark_rows(y0 >> 3, y1 >> 3);
}

static void canvas_clear(void)
{
    fill32(canvas, 0, CANVAS_CELLS * 8);
    for (int i = 0; i < CANVAS_CELLS; i++) canvas_banks[i] = BANK_UI_STD;
    canvas_banks_dirty = 1;
    canvas_mark_rows(0, CANVAS_ROWS - 1);
}

/* Clear a cell rectangle back to transparent. */
static void canvas_clear_cells(int cx, int cy, int cw, int ch)
{
    for (int y = cy; y < cy + ch; y++)
        for (int x = cx; x < cx + cw; x++) {
            if ((unsigned)x >= CANVAS_COLS || (unsigned)y >= CANVAS_ROWS) continue;
            fill32(&canvas[(y * CANVAS_COLS + x) * 8], 0, 8);
        }
    canvas_mark_rows(cy, cy + ch - 1);
}

static void canvas_set_banks(int cx, int cy, int cw, int ch, int bank)
{
    for (int y = cy; y < cy + ch; y++)
        for (int x = cx; x < cx + cw; x++)
            if ((unsigned)x < CANVAS_COLS && (unsigned)y < CANVAS_ROWS &&
                canvas_banks[y * CANVAS_COLS + x] != bank) {
                canvas_banks[y * CANVAS_COLS + x] = (u8)bank;
                canvas_banks_dirty = 1;
            }
}

/* Solid rectangle in pixel coordinates. */
static void canvas_fill(int x, int y, int w, int h, int c)
{
    int x0 = clampi(x, 0, tgt_w), x1 = clampi(x + w, 0, tgt_w);
    int y0 = clampi(y, 0, tgt_h), y1 = clampi(y + h, 0, tgt_h);
    if (x0 >= x1 || y0 >= y1) return;
    u32 cw = (u32)c * 0x11111111u;
    for (int py = y0; py < y1; py++) {
        for (int tx = x0 >> 3; tx <= (x1 - 1) >> 3; tx++) {
            int a = tx * 8 > x0 ? 0 : x0 - tx * 8;
            int b = (tx + 1) * 8 < x1 ? 8 : x1 - tx * 8;
            u32 mask = (b - a >= 8) ? 0xFFFFFFFFu : (((1u << ((b - a) * 4)) - 1u) << (a * 4));
            u32 *wd = &tgt_px[((py >> 3) * tgt_cols + tx) * 8 + (py & 7)];
            *wd = (*wd & ~mask) | (cw & mask);
        }
    }
    canvas_mark_px(y0, y1 - 1);
}

/* Replace a whole cell with tile data; index-0 pixels become `fill`
 * (pass 0 to keep them transparent). */
static void canvas_tile(int cx, int cy, const u32 *tile, int fill)
{
    if ((unsigned)cx >= CANVAS_COLS || (unsigned)cy >= CANVAS_ROWS) return;
    u32 *dst = &canvas[(cy * CANVAS_COLS + cx) * 8];
    for (int r = 0; r < 8; r++) {
        u32 w = tile[r];
        if (fill) {
            u32 t = w | (w >> 1);
            t |= t >> 2;
            u32 zero = ~t & 0x11111111u;
            w |= zero * (u32)fill;
        }
        dst[r] = w;
    }
    canvas_mark_rows(cy, cy);
}

/* A tiles_w x tiles_h image in row-major tile order. */
static void canvas_image(int cx, int cy, int tw, int th, const u32 *tiles, int fill, int bank)
{
    for (int ty = 0; ty < th; ty++)
        for (int tx = 0; tx < tw; tx++)
            canvas_tile(cx + tx, cy + ty, tiles + (ty * tw + tx) * 8, fill);
    if (bank >= 0) canvas_set_banks(cx, cy, tw, th, bank);
}

/* Window frame styles */
enum { WIN_STD, WIN_MENU, WIN_BATTLE };

static void canvas_window(int cx, int cy, int cw, int ch, int style)
{
    const u32 (*f)[8] = style == WIN_BATTLE ? ui_frame_battle :
                        style == WIN_MENU ? ui_frame_menu : ui_frame_std;
    for (int y = 0; y < ch; y++)
        for (int x = 0; x < cw; x++) {
            int col = x == 0 ? 0 : (x == cw - 1 ? 2 : 1);
            int row = y == 0 ? 0 : (y == ch - 1 ? 2 : 1);
            canvas_tile(cx + x, cy + y, f[row * 3 + col], 0);
        }
    canvas_set_banks(cx, cy, cw, ch, style == WIN_BATTLE ? BANK_UI_BATTLE : BANK_UI_STD);
}

/* Selection glow: a lantern-amber bar with softened ends and a pale top
 * rim (colour 7, rim 14 in banks 15 and 14); replaces a flat highlight. */
static void canvas_glow(int x, int y, int w, int h)
{
    canvas_fill(x + 1, y, w - 2, h, 7);
    canvas_fill(x, y + 1, 1, h - 2, 7);
    canvas_fill(x + w - 1, y + 1, 1, h - 2, 7);
    canvas_fill(x + 2, y, w - 4, 1, 14);
}

/* Paper-fill the inside of a window (cells), keeping the frame. */
static void canvas_window_clear(int cx, int cy, int cw, int ch)
{
    canvas_fill((cx + 1) * 8, (cy + 1) * 8, (cw - 2) * 8, (ch - 2) * 8, 1);
}

/* Tiled menu backdrop over the whole screen. */
static void canvas_backdrop(int pattern)
{
    for (int i = 0; i < 16; i++) bg_palette[BANK_MENU_BG * 16 + i] = menu_bg_pal[pattern][i];
    for (int y = 0; y < CANVAS_ROWS; y++)
        for (int x = 0; x < CANVAS_COLS; x++)
            canvas_tile(x, y, menu_bg_gfx[pattern] + ((y & 1) * 2 + (x & 1)) * 8, 0);
    canvas_set_banks(0, 0, CANVAS_COLS, CANVAS_ROWS, BANK_MENU_BG);
}

/* ---------------- text ---------------- */

#define INK_DARK    2
#define INK_SHADOW  3
#define INK_RED     8
#define INK_RED_SH  9
#define INK_BLUE   10
#define INK_BLUE_SH 11
#define INK_GREEN  12
#define INK_GREEN_SH 13
#define LINE_H     16
/* The '{' cursor glyph is drawn as a crimson rune rather than in ink. */
#define CURSOR_CH  '{'

static void glyph_rows(int x, int y, const u8 *bits, int rows, int ink, int shadow)
{
    u32 ink_w = (u32)ink * 0x11111111u, sh_w = (u32)shadow * 0x11111111u;
    int sub = x & 7, tx0 = x >> 3;
    u32 prev = 0;
    for (int r = 0; r <= rows; r++) {
        int py = y + r;
        u32 cur = r < rows ? (u32)bits[r] << 8 : 0;
        u32 sh = shadow ? (((cur >> 1) | prev | (prev >> 1)) & ~cur) & 0xFFFF : 0;
        prev = cur;
        if ((unsigned)py >= (unsigned)tgt_h || !(cur | sh)) continue;
        for (int pass = 0; pass < 2; pass++) {
            u32 m16 = pass ? cur : sh;
            if (!m16) continue;
            u32 m = (m16 << 16) >> sub;
            u32 color = pass ? ink_w : sh_w;
            for (int k = 0; k < 3; k++) {
                u32 byte = (m >> (24 - 8 * k)) & 0xFF;
                int tx = tx0 + k;
                if (!byte || (unsigned)tx >= (unsigned)tgt_cols) continue;
                u32 nib = nib_lut[byte];
                u32 *wd = &tgt_px[((py >> 3) * tgt_cols + tx) * 8 + (py & 7)];
                *wd = (*wd & ~nib) | (color & nib);
            }
        }
    }
}

static int glyph_index(char c)
{
    int i = (unsigned char)c - FONT_FIRST;
    return (i < 0 || i >= FONT_COUNT) ? ('?' - FONT_FIRST) : i;
}

static int char_width(char c)
{
    return font_width[glyph_index(c)];
}

/* Width of the first line of s in pixels. */
static int text_width(const char *s)
{
    int w = 0;
    for (; *s && *s != '\n'; s++) w += char_width(*s);
    return w;
}

/* Draw text; '\n' starts a new line 16 px lower. Returns the end x. */
static int text_draw_col(int x, int y, const char *s, int ink, int shadow)
{
    int x0 = x;
    int top = y;
    for (; *s; s++) {
        if (*s == '\n') {
            x = x0;
            y += LINE_H;
            continue;
        }
        int g = glyph_index(*s);
        if (*s == CURSOR_CH && ink == INK_DARK)
            glyph_rows(x, y, font_bits[g], FONT_HEIGHT, INK_RED, INK_SHADOW);
        else if (*s != ' ')
            glyph_rows(x, y, font_bits[g], FONT_HEIGHT, ink, shadow);
        x += font_width[g];
    }
    canvas_mark_px(top, y + FONT_HEIGHT + 1);
    return x;
}

static int text_draw(int x, int y, const char *s)
{
    return text_draw_col(x, y, s, INK_DARK, INK_SHADOW);
}

/* Single-line text squeezed by 1 px per letter when it would exceed max_w. */
static int text_draw_fit(int x, int y, const char *s, int max_w)
{
    int w = text_width(s);
    if (w <= max_w) return text_draw(x, y, s);
    int n = (int)str_len(s);
    int squeeze = n > 1 ? (w - max_w + n - 2) / (n - 1) : 0;
    if (squeeze > 2) squeeze = 2;
    for (; *s; s++) {
        int g = glyph_index(*s);
        if (*s != ' ') glyph_rows(x, y, font_bits[g], FONT_HEIGHT, INK_DARK, INK_SHADOW);
        x += font_width[g] - (*s == ' ' ? squeeze + 1 : squeeze);
    }
    canvas_mark_px(y, y + FONT_HEIGHT + 1);
    return x;
}

static void text_draw_right(int right_x, int y, const char *s)
{
    text_draw(right_x - text_width(s), y, s);
}

static void text_draw_center(int cx, int y, const char *s)
{
    text_draw(cx - text_width(s) / 2, y, s);
}

/* Small font (digits, '/', "Lv", "HP"). Returns end x. */
static int small_text_draw(int x, int y, const char *s)
{
    for (; *s; s++) {
        if (*s == ' ') {
            x += 4;
            continue;
        }
        int g = -1;
        for (int i = 0; font_small_chars[i]; i++)
            if (font_small_chars[i] == *s) g = i;
        if (g < 0) continue;
        glyph_rows(x, y, font_small_bits[g], FONT_SMALL_HEIGHT, INK_DARK, INK_SHADOW);
        x += font_small_width[g];
    }
    canvas_mark_px(y, y + FONT_SMALL_HEIGHT + 1);
    return x;
}

static int small_text_width(const char *s)
{
    int w = 0;
    for (; *s; s++) {
        if (*s == ' ') {
            w += 4;
            continue;
        }
        for (int i = 0; font_small_chars[i]; i++)
            if (font_small_chars[i] == *s) w += font_small_width[i];
    }
    return w;
}

/* Greedy word wrap of src into dst using '\n', lines at most max_w px. */
static void text_wrap(char *dst, const char *src, int max_w)
{
    int line_w = 0;
    int last_space = -1, n = 0;
    int w_since_space = 0;
    for (const char *s = src; *s && n < 398; s++) { /* callers pass 400-byte buffers */
        char c = *s;
        if (c == '\n' || c == '\f') {
            dst[n++] = c;
            line_w = 0;
            last_space = -1;
            continue;
        }
        int cw = char_width(c);
        if (c == ' ') {
            last_space = n;
            w_since_space = 0;
        } else {
            w_since_space += cw;
        }
        dst[n++] = c;
        line_w += cw;
        if (line_w > max_w && last_space >= 0) {
            dst[last_space] = '\n';
            line_w = w_since_space;
            last_space = -1;
        }
    }
    dst[n] = 0;
}

/* ---------------- bars, badges, icons ---------------- */

/* Notches every 8 px split a vitality bar into segments. */
static void bar_segments(int x, int y, int w, int h)
{
    for (int i = 7; i < w - 1; i += 8) canvas_fill(x + i, y, 1, h, 15);
}

/* Vitality bar: 3 px tall and segmented; colours from the HUD palette by
 * the remaining fraction (teal, amber, crimson). */
static void draw_hp_bar(int x, int y, int w, int cur, int max)
{
    int px = max > 0 ? (cur * w + max - 1) / max : 0;
    if (cur <= 0) px = 0;
    px = clampi(px, 0, w);
    int light = 8, shade = 9;
    if (px * 2 <= w) { light = 10; shade = 11; }
    if (px * 5 <= w) { light = 12; shade = 13; }
    canvas_fill(x, y, w, 3, 15);
    if (px) {
        canvas_fill(x, y, px, 1, shade);
        canvas_fill(x, y + 1, px, 2, light);
    }
    bar_segments(x, y, w, 3);
}

/* HP bar inside a standard window: its cells switch to the bar palette. */
static void menu_hp_bar(int x, int y, int w, int cur, int max)
{
    draw_hp_bar(x, y, w, cur, max);
    canvas_set_banks(x >> 3, y >> 3, ((x + w - 1) >> 3) - (x >> 3) + 1,
                     ((y + 2) >> 3) - (y >> 3) + 1, BANK_UI_BAR);
}

static void draw_xp_bar(int x, int y, int w, int num, int den)
{
    int px = den > 0 ? num * w / den : 0;
    px = clampi(px, 0, w);
    canvas_fill(x, y, w, 2, 15);
    if (px) canvas_fill(x, y, px, 2, 14);
}

static void draw_type_badge(int cx, int cy, int type)
{
    canvas_image(cx, cy, 4, 2, type_badge_gfx[type], 1, type_badge_bank[type]);
}

static void draw_status_badge(int cx, int cy, int status)
{
    if (status == STATUS_NONE) return;
    canvas_image(cx, cy, 3, 1, status_badge_gfx[status - 1], 0, status_badge_bank[status - 1]);
}

/* ICON_* art of an item (0 for anything out of range). */
static int item_icon_index(int item)
{
    if (item < 0 || item >= ITEM_COUNT) return 0;
    int icon = ITEMS[item].icon;
    return icon < ITEM_ICON_COUNT ? icon : 0;
}

static void draw_item_icon(int cx, int cy, int item)
{
    int icon = item_icon_index(item);
    for (int i = 0; i < 16; i++) bg_palette[BANK_ITEM_ICON * 16 + i] = item_icon_pal[icon][i];
    bg_palette[BANK_ITEM_ICON * 16 + 1] = ui_pal_std[1]; /* sit on the page */
    canvas_image(cx, cy, 3, 3, item_icon_gfx[icon], 1, BANK_ITEM_ICON);
}

/* ---------------- present ---------------- */

static void canvas_present(void)
{
    if (canvas_dirty_hi >= canvas_dirty_lo) {
        int start = canvas_dirty_lo * CANVAS_COLS * 8;
        int words = (canvas_dirty_hi - canvas_dirty_lo + 1) * CANVAS_COLS * 8;
        copy32(VRAM_UI_TILES + start, canvas + start, (unsigned)words);
        canvas_dirty_lo = CANVAS_ROWS;
        canvas_dirty_hi = -1;
    }
    if (canvas_banks_dirty) {
        u16 *map = VRAM_MAP(SB_UI);
        for (int y = 0; y < CANVAS_ROWS; y++)
            for (int x = 0; x < CANVAS_COLS; x++)
                map[y * 32 + x] = (u16)((y * CANVAS_COLS + x) |
                                        (canvas_banks[y * CANVAS_COLS + x] << 12));
        canvas_banks_dirty = 0;
    }
}

/* ---------------- sprites ---------------- */

/*
 * attr3 of every group of four OAM entries holds one affine matrix (32 in
 * all): spr_push never writes attr3, oam_affine() fills it, and the whole
 * shadow (attributes and matrices) is copied in vblank.
 */
static u16 oam_shadow[128 * 4];
static int oam_count;
static int oam_affine_count;

/* OBJ shapes/sizes */
enum { SQ8, SQ16, SQ32, SQ64, TALL16x32, WIDE32x16 };

/* Extra spr_push / spr_push_affine flag: OBJ mosaic (REG_MOSAIC OBJ size). */
#define SPR_MOSAIC 0x0001
#define ATTR0_AFFINE 0x0100
#define ATTR0_DOUBLE 0x0200
#define ATTR0_MOSAIC 0x1000

static int spr_shape_bits(int shape, u16 *a0, u16 *a1)
{
    switch (shape) {
    case SQ8: return 8;
    case SQ16: *a1 |= ATTR1_SIZE(1); return 16;
    case SQ32: *a1 |= ATTR1_SIZE(2); return 32;
    case SQ64: *a1 |= ATTR1_SIZE(3); return 64;
    case TALL16x32: *a0 |= ATTR0_TALL; *a1 |= ATTR1_SIZE(2); return 32;
    case WIDE32x16: *a0 |= ATTR0_WIDE; *a1 |= ATTR1_SIZE(2); return 32;
    }
    return 8;
}

static void spr_push(int x, int y, int tile, int shape, int bank, int prio, int flags)
{
    if (oam_count >= 128) return;
    if (x <= -64 || x >= SCREEN_WIDTH || y <= -64 || y >= SCREEN_HEIGHT) return;
    u16 a0 = (u16)(y & 0xFF), a1 = (u16)(x & 0x1FF);
    spr_shape_bits(shape, &a0, &a1);
    a1 |= (u16)(flags & (ATTR1_HFLIP | ATTR1_VFLIP));
    if (flags & ATTR0_BLEND) a0 |= ATTR0_BLEND;
    if (flags & SPR_MOSAIC) a0 |= ATTR0_MOSAIC;
    u16 *o = &oam_shadow[oam_count * 4];
    o[0] = a0;
    o[1] = a1;
    o[2] = (u16)(tile | ATTR2_PRIO(prio) | ATTR2_BANK(bank));
    oam_count++;
}

/*
 * Reserve an affine matrix for this frame. pa..pd are 8.8 fixed point and
 * map screen space to texture space (the inverse of the drawn transform).
 * Returns the matrix index, or -1 when all 32 are taken.
 */
static int oam_affine(int pa, int pb, int pc, int pd)
{
    if (oam_affine_count >= 32) return -1;
    int n = oam_affine_count++;
    oam_shadow[(n * 4 + 0) * 4 + 3] = (u16)pa;
    oam_shadow[(n * 4 + 1) * 4 + 3] = (u16)pb;
    oam_shadow[(n * 4 + 2) * 4 + 3] = (u16)pc;
    oam_shadow[(n * 4 + 3) * 4 + 3] = (u16)pd;
    return n;
}

/*
 * Matrix for a drawn scale (sx, sy in 8.8, 256 = 100%) and rotation `ang`
 * (0..255 = one turn); uses the triangle-wave sine below for the angle.
 */
static int oam_tri_sin(int phase)
{
    phase &= 255;
    if (phase < 64) return phase * 4;           /* 0..256 */
    if (phase < 192) return (128 - phase) * 4;
    return (phase - 256) * 4;
}

static int oam_affine_scale_rot(int sx, int sy, int ang)
{
    /* negative scales mirror the sprite */
    if (sx > -8 && sx < 8) sx = sx < 0 ? -8 : 8;
    if (sy > -8 && sy < 8) sy = sy < 0 ? -8 : 8;
    int s = oam_tri_sin(ang), c = oam_tri_sin(ang + 64);
    /* inverse of R(ang) * S(sx, sy): S^-1 * R(-ang) */
    int pa = c * 256 / sx, pb = s * 256 / sx;
    int pc = -s * 256 / sy, pd = c * 256 / sy;
    return oam_affine(pa, pb, pc, pd);
}

/*
 * Affine sprite. (x, y) is the top-left of the untransformed sprite; with
 * `dbl` the sprite gets a double-size box centred on the same point so a
 * scaled-up image is not clipped. aff < 0 falls back to a plain sprite.
 */
static void spr_push_affine(int x, int y, int tile, int shape, int bank, int prio, int flags,
                            int aff, int dbl)
{
    if (aff < 0) {
        spr_push(x, y, tile, shape, bank, prio, flags);
        return;
    }
    if (oam_count >= 128) return;
    u16 a0 = 0, a1 = 0;
    int size = spr_shape_bits(shape, &a0, &a1);
    int w = size, h = size;
    if (shape == TALL16x32) w = 16;
    if (shape == WIDE32x16) h = 16;
    if (dbl) {
        x -= w / 2;
        y -= h / 2;
        w *= 2;
        h *= 2;
    }
    if (x <= -w || x >= SCREEN_WIDTH || y <= -h || y >= SCREEN_HEIGHT) return;
    a0 |= (u16)((y & 0xFF) | ATTR0_AFFINE | (dbl ? ATTR0_DOUBLE : 0));
    a1 |= (u16)((x & 0x1FF) | ((aff & 31) << 9));
    if (flags & ATTR0_BLEND) a0 |= ATTR0_BLEND;
    if (flags & SPR_MOSAIC) a0 |= ATTR0_MOSAIC;
    u16 *o = &oam_shadow[oam_count * 4];
    o[0] = a0;
    o[1] = a1;
    o[2] = (u16)(tile | ATTR2_PRIO(prio) | ATTR2_BANK(bank));
    oam_count++;
}

static void oam_begin(void)
{
    oam_count = 0;
    oam_affine_count = 0;
}

static void oam_line_prepare(void);

static void oam_end(void)
{
    for (int i = oam_count; i < 128; i++) {
        oam_shadow[i * 4] = ATTR0_HIDE;
        oam_shadow[i * 4 + 1] = 0;
        oam_shadow[i * 4 + 2] = 0;
    }
    oam_line_prepare();
}

/*
 * Optional per-scanline register tables (HBlank DMA), re-armed together
 * with OAM every vblank. Each points at LINE_COPIES * 160 + 1 entries (one
 * per line, repeated so a frame that misses its re-arm reads the same
 * lines again); set a pointer to 0 to stop it (the register is reset to 0).
 *   oam_line_win0h  u16 REG_WIN0H per line (window iris)          DMA0
 *   oam_line_bg0    u32 BG0HOFS | BG0VOFS << 16 per line           DMA2
 *   oam_line_bg1    u32 BG1HOFS | BG1VOFS << 16 per line           DMA2
 * DMA1 belongs to the music (sound FIFO A, music.c) and is never touched
 * here. When both BG tables are set, oam_end() interleaves them (after the
 * frame is drawn, outside vblank), so one HBlank transfer of two words
 * writes BG0HOFS..BG1VOFS. The tables must hold LINE_COPIES repeats.
 */
#ifndef LINE_COPIES
#define LINE_COPIES 3
#endif
#define OAM_LINES (SCREEN_HEIGHT * LINE_COPIES + 1)

static const u16 *oam_line_win0h;
static const u32 *oam_line_bg0, *oam_line_bg1;
static u8 oam_line_active;          /* registers driven: 1 WIN0H, 2 BG0, 4 BG1 */
static u32 oam_line_pairs[2][OAM_LINES * 2] EWRAM_BSS;
static u8 oam_line_pair_buf;
static const u32 *oam_line_pair;    /* both BG tables interleaved, or 0 */

static void oam_line_prepare(void)
{
    oam_line_pair = 0;
    if (!oam_line_bg0 || !oam_line_bg1) return;
    u32 *p = oam_line_pairs[oam_line_pair_buf ^= 1];
    const u32 *a = oam_line_bg0, *b = oam_line_bg1;
    for (int y = 0; y < SCREEN_HEIGHT; y++) {
        p[y * 2] = a[y];
        p[y * 2 + 1] = b[y];
    }
    for (int k = 1; k < LINE_COPIES; k++) copy32(p + k * SCREEN_HEIGHT * 2, p, SCREEN_HEIGHT * 2);
    p[OAM_LINES * 2 - 2] = a[OAM_LINES - 1];
    p[OAM_LINES * 2 - 1] = b[OAM_LINES - 1];
    oam_line_pair = p;
}

/* Arm DMA `ch` to copy `units` entries per HBlank from `table` to `reg`
 * (`mask`: the registers that drives), or stop it when table is 0. */
static void oam_line_arm(int ch, const void *table, unsigned reg, int wide, int units, int mask)
{
    volatile u32 *cnt = (volatile u32 *)(MEM_IO + 0x0B8 + ch * 12);
    *cnt = 0;
    int stop = (ch == 0 ? 1 : 6) & oam_line_active & ~(table ? mask : 0);
    if (stop & 1) REG16(0x040) = 0;
    if (stop & 2) REG32(0x010) = 0;
    if (stop & 4) REG32(0x014) = 0;
    oam_line_active &= (u8)~stop;
    if (!table) return;
    oam_line_active |= (u8)mask;
    if (wide) {
        const u32 *t = table;
        for (int u = 0; u < units; u++) REG32(reg + u * 4) = t[u];
        REG32(0x0B0 + ch * 12) = (u32)(unsigned long)(t + units);
    } else {
        const u16 *t = table;
        REG16(reg) = t[0];
        REG32(0x0B0 + ch * 12) = (u32)(unsigned long)(t + 1);
    }
#ifdef GBA
    REG32(0x0B4 + ch * 12) = MEM_IO + reg;
    /* enable, HBlank start, repeat, 16/32-bit, destination fixed (one
     * unit) or incremented and reloaded (several) */
    u32 ctl = 0xA200 | (wide ? 0x0400 : 0) | (units > 1 ? 0x0060 : 0x0040);
    *cnt = (u32)units | (ctl << 16);
#endif
}

static void oam_commit(void)
{
    for (int i = 0; i < 128 * 4; i++) oam[i] = oam_shadow[i];
    oam_line_arm(0, oam_line_win0h, 0x040, 0, 1, 1);
    if (oam_line_pair && oam_line_bg0 && oam_line_bg1)
        oam_line_arm(2, oam_line_pair, 0x010, 1, 2, 6);
    else if (oam_line_bg1) {
        oam_line_arm(2, oam_line_bg1, 0x014, 1, 1, 4);
    } else {
        oam_line_arm(2, oam_line_bg0, 0x010, 1, 1, 2);
    }
}

/* ---------------- palettes & loaders ---------------- */

static void load_pal(u16 *dst_bank, const u16 *src)
{
    copy16(dst_bank, src, 16);
}

static void load_ui_palettes(void)
{
    load_pal(bg_palette + BANK_UI_STD * 16, ui_pal_std);
    load_pal(bg_palette + BANK_UI_BATTLE * 16, ui_pal_battle);
    load_pal(bg_palette + BANK_UI_HUD * 16, ui_pal_hud);
    load_pal(bg_palette + BANK_TYPE_A * 16, type_badge_pal[0]);
    load_pal(bg_palette + BANK_TYPE_B * 16, type_badge_pal[1]);
    load_pal(bg_palette + BANK_UI_BAR * 16, ui_pal_std);
    for (int i = 8; i < 16; i++) bg_palette[BANK_UI_BAR * 16 + i] = ui_pal_hud[i];
}

/*
 * A species' 16-colour palette; lustrous kin get the hue rotated by about
 * 140 degrees (and a touch more saturation) so they read as a rare colour
 * variant while keeping the same shading ramps.
 */
static void mon_palette_get(u16 *out, int species, int lustrous)
{
    const u16 *src = mon_palettes[species];
    out[0] = src[0];
    for (int i = 1; i < 16; i++) {
        int c = src[i];
        if (!lustrous) {
            out[i] = (u16)c;
            continue;
        }
        int r = c & 31, g = (c >> 5) & 31, b = (c >> 10) & 31;
        int mx = r > g ? (r > b ? r : b) : (g > b ? g : b);
        int mn = r < g ? (r < b ? r : b) : (g < b ? g : b);
        int d = mx - mn;
        if (d < 2) { /* greys and outlines stay as they are */
            out[i] = (u16)c;
            continue;
        }
        /* hue in 0..191 (32 per sextant) */
        int h;
        if (mx == r) h = (g - b) * 32 / d;
        else if (mx == g) h = 64 + (b - r) * 32 / d;
        else h = 128 + (r - g) * 32 / d;
        h = (h + 75 + 192 * 2) % 192;
        int s = d * 36 / 32; /* a little more saturated */
        if (s > mx) s = mx;
        int lo = mx - s, sext = h / 32, f = h % 32;
        int up = lo + s * f / 32, down = mx - s * f / 32;
        int rr, gg, bb;
        switch (sext) {
        case 0: rr = mx; gg = up; bb = lo; break;
        case 1: rr = down; gg = mx; bb = lo; break;
        case 2: rr = lo; gg = mx; bb = up; break;
        case 3: rr = lo; gg = down; bb = mx; break;
        case 4: rr = up; gg = lo; bb = mx; break;
        default: rr = mx; gg = lo; bb = down; break;
        }
        out[i] = RGB15(rr, gg, bb);
    }
}

static void load_mon_pal(int obj_bank, int species, int lustrous)
{
    u16 pal[16];
    mon_palette_get(pal, species, lustrous);
    load_pal(obj_palette + obj_bank * 16, pal);
}

/* Monster sprites: slot 0 = A, 1 = B. */
static void load_monster_gfx_ex(int slot, int species, int back, int lustrous)
{
    u32 *dst = VRAM_OBJ_TILES + (slot ? OT_MON_B : OT_MON_A) * 8;
    copy32(dst, back ? mon_back_gfx[species] : mon_front_gfx[species], 64 * 8);
    load_mon_pal(slot ? OBANK_MON_B : OBANK_MON_A, species, lustrous);
}

static void load_monster_gfx(int slot, int species, int back)
{
    load_monster_gfx_ex(slot, species, back, 0);
}

static void load_monster_icon_ex(int i, int species, int lustrous)
{
    copy32(VRAM_OBJ_TILES + OT_ICON(i) * 8, mon_icon_gfx[species], 16 * 8);
    load_mon_pal(OBANK_NPC + i, species, lustrous);
}

static void load_monster_icon(int i, int species)
{
    load_monster_icon_ex(i, species, 0);
}

/* Screen brightness: 0 normal, >0 toward white, <0 toward black (16 max). */
static void set_brightness(int level)
{
    if (level == 0) {
        REG_BLDCNT = 0;
        REG_BLDY = 0;
    } else {
        REG_BLDCNT = (u16)(0x3F | (level > 0 ? 0x80 : 0xC0));
        REG_BLDY = (u16)clampi(absi(level), 0, 16);
    }
}

/* ---------------- rarity gems (8x8 OBJ sprites) ---------------- */

#define OT_GEM          120   /* GEM_COUNT tiles; NPC slots 14+ are never used in menus */
#define OBANK_GEM         7

/* Menus call this once when they open (the field reuses the bank). */
static void gems_load(void)
{
    copy32(VRAM_OBJ_TILES + OT_GEM * 8, gem_obj_gfx, GEM_COUNT * 8);
    load_pal(obj_palette + OBANK_GEM * 16, gem_obj_pal);
}

static void gem_push(int x, int y, int rarity)
{
    if (rarity < 0 || rarity >= GEM_COUNT) return;
    spr_push(x, y, OT_GEM + rarity, SQ8, OBANK_GEM, 0, 0);
}
