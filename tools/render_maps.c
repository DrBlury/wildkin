/*
 * Render maps to PNG exactly the way the game draws them: the host build of
 * the game (src/main.c) decodes each map and its streaming renderer fills
 * the three BG layers cell by cell (ground, decor, top), including the
 * elevation autotiles (elev.c); people and satchels are drawn between the
 * layers with the same OBJ priorities as in the field.
 *
 *   cc -O2 -o build/render_maps tools/render_maps.c -lz
 *   build/render_maps OUTDIR [--scale N] [--levels] [NAME_OR_ID ...]
 *
 * With no names every map (but the asset viewers) is written as
 * OUTDIR/<id>_<name>.png (e.g. 00_maple_village.png); a name selects the
 * maps whose file name contains it. A lone digit after OUTDIR is the scale
 * (as make_media.py passes it). --levels prints each cell's elevation
 * (ground height; deck / stairs top) over the picture: white ground, red
 * cliff faces and ledges, green stairs, blue decks and tunnels, magenta
 * hidden passages.
 *
 * tools/render_maps.py (make maps) builds and runs this.
 */
#define main gba_main
#include "../src/main.c"
#undef main

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>

static u32 *pix;          /* 0xRRGGBB, map-sized */
static int pw, ph;

static u32 rgb(u16 c)
{
    int r = c & 31, g = (c >> 5) & 31, b = (c >> 10) & 31;
    return (u32)(((r << 3) | (r >> 2)) << 16 | ((g << 3) | (g >> 2)) << 8 | ((b << 3) | (b >> 2)));
}

/* One 8x8 BG entry at (x0, y0); transparent pixels skipped unless opaque. */
static void draw_entry(u16 ent, int x0, int y0, int opaque)
{
    int t = ent & 1023, hf = (ent >> 10) & 1, vf = (ent >> 11) & 1, bank = ent >> 12;
    const u32 *tile = VRAM_SCENE_TILES + t * 8;
    for (int y = 0; y < 8; y++)
        for (int x = 0; x < 8; x++) {
            int sy = vf ? 7 - y : y, sx = hf ? 7 - x : x;
            int i = (tile[sy] >> (sx * 4)) & 15;
            if (!i && !opaque) continue;
            int px = x0 + x, py = y0 + y;
            if (px < 0 || py < 0 || px >= pw || py >= ph) continue;
            pix[py * pw + px] = rgb(i ? bg_palette[bank * 16 + i] : bg_palette[0]);
        }
}

/* A sprite made of 8x8 tiles (4bpp words), tw x th tiles. */
static void draw_obj(const u32 *tiles, const u16 *pal, int x0, int y0, int tw, int th, int flip)
{
    for (int ty = 0; ty < th; ty++)
        for (int tx = 0; tx < tw; tx++) {
            const u32 *tile = tiles + (ty * tw + tx) * 8;
            for (int y = 0; y < 8; y++)
                for (int x = 0; x < 8; x++) {
                    int i = (tile[y] >> (x * 4)) & 15;
                    if (!i) continue;
                    int px = tx * 8 + x;
                    if (flip) px = tw * 8 - 1 - px;
                    px += x0;
                    int py = y0 + ty * 8 + y;
                    if (px < 0 || py < 0 || px >= pw || py >= ph) continue;
                    pix[py * pw + px] = rgb(pal[i]);
                }
        }
}

static const u8 OFF[4] = { 0, 1, 32, 33 };

static void draw_layer(int which)
{
    u16 *sb = VRAM_MAP(which == 0 ? SB_FIELD_BOTTOM : which == 2 ? SB_PANEL : SB_FIELD_TOP);
    for (int my = 0; my < map_h; my++)
        for (int mx = 0; mx < map_w; mx++) {
            field_redraw_cell(mx, my);
            render_cell(mx, my);
            int idx = (my & 15) * 64 + (mx & 15) * 2;
            for (int q = 0; q < 4; q++) {
                u16 e = sb[idx + OFF[q]];
                if (which != 0 && !e) continue;
                draw_entry(e, mx * 16 + (q & 1) * 8, my * 16 + (q >> 1) * 8, which == 0);
            }
        }
}

static void draw_people(int prio)
{
    for (int i = 0; i < NPC_COUNT; i++) {
        if (NPCS[i].map != cur_map || NPCS[i].fixture) continue;
        const Actor *a = &npc_state[i];
        if (elev_obj_prio(a) != prio) continue;
        draw_obj(char_gfx[NPCS[i].chr][actor_frame(a)], char_palettes[NPCS[i].chr], a->x * 16,
                 a->y * 16 - 16, 2, 4, a->facing == DIR_RIGHT);
    }
    if (prio != 2) return;
    for (int i = 0; i < ITEM_BALL_COUNT; i++)
        if (ITEM_BALLS[i].map == cur_map)
            draw_obj(item_ball_gfx, item_ball_palette, ITEM_BALLS[i].x * 16, ITEM_BALLS[i].y * 16, 2, 2, 0);
}

/* 3x5 digits for --levels (bit 14 = top-left) */
static const u16 FONT35[16] = {
    0x7B6F, 0x2C97, 0x73E7, 0x73CF, 0x5BC9, 0x79CF, 0x79EF, 0x7249, 0x7BEF, 0x7BCF,   /* 0-9 */
    0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000,
};

static void glyph(int x0, int y0, int d, u32 col)
{
    u16 bits = FONT35[d & 15];
    for (int y = 0; y < 5; y++)
        for (int x = 0; x < 3; x++)
            if ((bits >> (14 - (y * 3 + x))) & 1) {
                for (int yy = -1; yy <= 1; yy++)      /* dark outline */
                    for (int xx = -1; xx <= 1; xx++) {
                        int px = x0 + x + xx, py = y0 + y + yy;
                        if (px >= 0 && py >= 0 && px < pw && py < ph && pix[py * pw + px] != col)
                            pix[py * pw + px] = 0x101018;
                    }
            }
    for (int y = 0; y < 5; y++)
        for (int x = 0; x < 3; x++)
            if ((bits >> (14 - (y * 3 + x))) & 1) {
                int px = x0 + x, py = y0 + y;
                if (px >= 0 && py >= 0 && px < pw && py < ph) pix[py * pw + px] = col;
            }
}

static void draw_levels(void)
{
    for (int my = 0; my < map_h; my++)
        for (int mx = 0; mx < map_w; mx++) {
            u16 e = elev_at(mx, my);
            int k = EV_KIND(e), c = EV_COVER(e);
            u32 col = 0xFFFFFF;
            if (k == EK_FACE || k == EK_LEDGE) col = 0xFF8060;
            if (EK_IS_STAIRS(k)) col = 0x60FF60;
            if (c == EC_BRIDGE_H || c == EC_BRIDGE_V || c == EC_TUNNEL) col = 0x60C0FF;
            if (c == EC_HIDDEN) col = 0xFF60FF;
            glyph(mx * 16 + 2, my * 16 + 2, EV_LO(e), col);
            if (ec_walkable(c) || EK_IS_STAIRS(k)) glyph(mx * 16 + 9, my * 16 + 2, EK_IS_STAIRS(k) ? EV_LO(e) + 1 : EV_HI(e), col);
        }
}

static void put32be(unsigned char *p, unsigned v)
{
    p[0] = (unsigned char)(v >> 24);
    p[1] = (unsigned char)(v >> 16);
    p[2] = (unsigned char)(v >> 8);
    p[3] = (unsigned char)v;
}

static void chunk(FILE *f, const char *type, const unsigned char *data, unsigned len)
{
    unsigned char hdr[8];
    put32be(hdr, len);
    memcpy(hdr + 4, type, 4);
    fwrite(hdr, 1, 8, f);
    if (len) fwrite(data, 1, len, f);
    unsigned crc = (unsigned)crc32(0, (const unsigned char *)type, 4);
    if (len) crc = (unsigned)crc32(crc, data, len);
    unsigned char c[4];
    put32be(c, crc);
    fwrite(c, 1, 4, f);
}

static int write_png(const char *path, int scale)
{
    int ow = pw * scale, oh = ph * scale;
    size_t raw_len = (size_t)(ow * 3 + 1) * oh;
    unsigned char *raw = malloc(raw_len);
    for (int y = 0; y < oh; y++) {
        unsigned char *row = raw + (size_t)y * (ow * 3 + 1);
        row[0] = 0;
        for (int x = 0; x < ow; x++) {
            u32 c = pix[(y / scale) * pw + x / scale];
            row[1 + x * 3] = (unsigned char)(c >> 16);
            row[2 + x * 3] = (unsigned char)(c >> 8);
            row[3 + x * 3] = (unsigned char)c;
        }
    }
    uLongf zlen = compressBound(raw_len);
    unsigned char *z = malloc(zlen);
    compress2(z, &zlen, raw, raw_len, 6);
    FILE *f = fopen(path, "wb");
    if (!f) {
        perror(path);
        return 0;
    }
    fwrite("\x89PNG\r\n\x1a\n", 1, 8, f);
    unsigned char ihdr[13];
    put32be(ihdr, (unsigned)ow);
    put32be(ihdr + 4, (unsigned)oh);
    ihdr[8] = 8;
    ihdr[9] = 2;
    ihdr[10] = ihdr[11] = ihdr[12] = 0;
    chunk(f, "IHDR", ihdr, 13);
    chunk(f, "IDAT", z, (unsigned)zlen);
    chunk(f, "IEND", 0, 0);
    fclose(f);
    free(raw);
    free(z);
    return 1;
}

/* OUTDIR/<id>_<name>.png: the id (two digits at least), then the name in
 * lower case with '_' for anything but letters and digits. */
static void file_name(int m, char *out, int n)
{
    int k = snprintf(out, (size_t)n, "%02d_", m);
    for (const char *s = MAPS[m].name; *s && k < n - 1; s++) {
        char c = *s;
        out[k++] = (c >= 'A' && c <= 'Z') ? (char)(c - 'A' + 'a')
                 : ((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')) ? c : '_';
    }
    out[k] = 0;
}

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: %s OUTDIR [--scale N] [--levels] [NAME_OR_ID ...]\n", argv[0]);
        return 1;
    }
    const char *outdir = argv[1];
    int scale = 1, levels = 0;
    const char *want[64];
    int nwant = 0;
    for (int i = 2; i < argc; i++) {
        if (!strcmp(argv[i], "--scale") && i + 1 < argc) scale = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--levels")) levels = 1;
        else if (i == 2 && argv[i][0] >= '1' && argv[i][0] <= '9' && !argv[i][1]) scale = atoi(argv[i]);
        else if (nwant < 64) want[nwant++] = argv[i];
    }
    if (scale < 1) scale = 1;
    game_init();
    rng_seed(1);
    new_game();
    flag_set(FLAG_STARTER);
    flag_set(FLAG_STORM_CALMED);
    gtime.minute = 12 * 60;
    gtime.weather = 0;
    int written = 0;
    for (int m = 0; m < MAP_COUNT; m++) {
        char name[96], path[512];
        file_name(m, name, sizeof(name));
        int ok = !nwant && !(MAPS[m].flags & MF_DEBUG);   /* the asset viewers only by name */
        for (int i = 0; i < nwant; i++)
            if (strstr(name, want[i]) || (want[i][0] >= '0' && want[i][0] <= '9' && atoi(want[i]) == m))
                ok = 1;
        if (!ok) continue;
        map_load(m);
        field_load_tileset();
        player.x = player.y = -100;
        pw = map_w * 16;
        ph = map_h * 16;
        pix = realloc(pix, (size_t)pw * ph * sizeof(u32));
        draw_layer(0);
        draw_layer(2);
        draw_people(2);
        draw_layer(3);
        draw_people(1);
        if (levels) draw_levels();
        snprintf(path, sizeof(path), "%s/%s.png", outdir, name);
        if (write_png(path, scale)) written++;
    }
    printf("wrote %d map(s) to %s\n", written, outdir);
    return 0;
}
