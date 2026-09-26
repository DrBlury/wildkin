/*
 * Render every map to a PNG exactly the way the game draws it: the host
 * build of the game loads each map and its tileset into (host) VRAM and
 * the field renderer writes every cell's three layers, which are then
 * decoded here -- BG0 ground, BG2 decor, the people (standing, first
 * frame), BG3 top layer. Tile animations show their first frame.
 *
 *   cc -std=c11 -o build/render_maps tools/render_maps.c -lz
 *   build/render_maps OUTDIR [scale]      (make maps)
 */
#define main gba_main
#include "../src/main.c"
#undef main

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>

static unsigned char *img;
static int img_w, img_h;

static void put(int x, int y, u16 c)
{
    if (x < 0 || y < 0 || x >= img_w || y >= img_h) return;
    unsigned char *p = img + ((size_t)y * img_w + x) * 3;
    int r = c & 31, g = (c >> 5) & 31, b = (c >> 10) & 31;
    p[0] = (unsigned char)(r << 3 | r >> 2);
    p[1] = (unsigned char)(g << 3 | g >> 2);
    p[2] = (unsigned char)(b << 3 | b >> 2);
}

/* One 8x8 BG tile entry at (x0, y0). */
static void draw_entry(u16 e, int x0, int y0, int transparent)
{
    int t = e & 1023, hf = (e >> 10) & 1, vf = (e >> 11) & 1, bank = e >> 12;
    const u32 *tile = VRAM_SCENE_TILES + t * 8;
    for (int y = 0; y < 8; y++)
        for (int x = 0; x < 8; x++) {
            int sx = hf ? 7 - x : x, sy = vf ? 7 - y : y;
            int i = (tile[sy] >> (sx * 4)) & 15;
            if (!i && transparent) continue;
            put(x0 + x, y0 + y, i ? bg_palette[bank * 16 + i] : bg_palette[0]);
        }
}

static void draw_sprite(const u32 *tiles, const u16 *pal, int tw, int th, int x0, int y0, int flip)
{
    for (int ty = 0; ty < th; ty++)
        for (int tx = 0; tx < tw; tx++)
            for (int y = 0; y < 8; y++)
                for (int x = 0; x < 8; x++) {
                    int i = (tiles[(ty * tw + tx) * 8 + y] >> (x * 4)) & 15;
                    if (!i) continue;
                    int px = tx * 8 + x;
                    if (flip) px = tw * 8 - 1 - px;
                    put(x0 + px, y0 + ty * 8 + y, pal[i]);
                }
}

static void write_png(const char *path, int scale)
{
    int w = img_w * scale, h = img_h * scale;
    size_t raw_len = (size_t)(w * 3 + 1) * h;
    unsigned char *raw = malloc(raw_len);
    for (int y = 0; y < h; y++) {
        unsigned char *row = raw + (size_t)y * (w * 3 + 1);
        row[0] = 0;
        for (int x = 0; x < w; x++)
            memcpy(row + 1 + x * 3, img + ((size_t)(y / scale) * img_w + x / scale) * 3, 3);
    }
    uLongf zlen = compressBound(raw_len);
    unsigned char *z = malloc(zlen);
    compress2(z, &zlen, raw, raw_len, 6);
    FILE *f = fopen(path, "wb");
    if (!f) {
        perror(path);
        exit(1);
    }
    static const unsigned char sig[8] = { 137, 'P', 'N', 'G', 13, 10, 26, 10 };
    fwrite(sig, 1, 8, f);
    unsigned char ihdr[13] = { (unsigned char)(w >> 24), (unsigned char)(w >> 16), (unsigned char)(w >> 8),
                               (unsigned char)w, (unsigned char)(h >> 24), (unsigned char)(h >> 16),
                               (unsigned char)(h >> 8), (unsigned char)h, 8, 2, 0, 0, 0 };
    const struct { const char *type; const unsigned char *data; unsigned len; } chunks[3] = {
        { "IHDR", ihdr, 13 }, { "IDAT", z, (unsigned)zlen }, { "IEND", 0, 0 } };
    for (int c = 0; c < 3; c++) {
        unsigned char hdr[8] = { (unsigned char)(chunks[c].len >> 24), (unsigned char)(chunks[c].len >> 16),
                                 (unsigned char)(chunks[c].len >> 8), (unsigned char)chunks[c].len };
        memcpy(hdr + 4, chunks[c].type, 4);
        fwrite(hdr, 1, 8, f);
        if (chunks[c].len) fwrite(chunks[c].data, 1, chunks[c].len, f);
        unsigned crc = (unsigned)crc32(0, (const unsigned char *)chunks[c].type, 4);
        if (chunks[c].len) crc = (unsigned)crc32(crc, chunks[c].data, chunks[c].len);
        unsigned char cb[4] = { (unsigned char)(crc >> 24), (unsigned char)(crc >> 16), (unsigned char)(crc >> 8),
                                (unsigned char)crc };
        fwrite(cb, 1, 4, f);
    }
    fclose(f);
    free(raw);
    free(z);
}

int main(int argc, char **argv)
{
    const char *outdir = argc > 1 ? argv[1] : "build/maps";
    int scale = argc > 2 ? atoi(argv[2]) : 1;
    if (scale < 1) scale = 1;
    game_init();
    int n = 0;
    for (int m = 0; m < MAP_COUNT; m++) {
        if (MAPS[m].flags & MF_DEBUG) continue;
        map_load(m);
        field_load_tileset();
        img_w = map_w * 16;
        img_h = map_h * 16;
        img = calloc((size_t)img_w * img_h, 3);
        static const u8 OFF[4] = { 0, 1, 32, 33 };
        for (int layer = 0; layer < 3; layer++) {
            if (layer == 2) {
                /* people between the decor and the top layer, back to front */
                for (int y = 0; y < map_h; y++)
                    for (int i = 0; i < NPC_COUNT; i++)
                        if (NPCS[i].map == m && NPCS[i].y == y)
                            draw_sprite(char_gfx[NPCS[i].chr][actor_frame(&npc_state[i])],
                                        char_palettes[NPCS[i].chr], 2, 4, NPCS[i].x * 16, y * 16 - 16,
                                        npc_state[i].facing == DIR_RIGHT);
            }
            u16 *layer_map = VRAM_MAP(layer == 0 ? SB_FIELD_BOTTOM : layer == 1 ? SB_PANEL : SB_FIELD_TOP);
            for (int my = 0; my < map_h; my++)
                for (int mx = 0; mx < map_w; mx++) {
                    ring_invalidate();
                    render_cell(mx, my);
                    int idx = (my & 15) * 2 * 32 + (mx & 15) * 2;
                    for (int q = 0; q < 4; q++) {
                        u16 e = layer_map[idx + OFF[q]];
                        if (layer && !e) continue;
                        draw_entry(e, mx * 16 + (q & 1) * 8, my * 16 + (q >> 1) * 8, layer != 0);
                    }
                }
        }
        char name[64], path[256];
        int k = 0;
        for (const char *c = MAPS[m].name; *c && k < 60; c++)
            name[k++] = (*c >= 'A' && *c <= 'Z') ? (char)(*c - 'A' + 'a')
                      : ((*c >= 'a' && *c <= 'z') || (*c >= '0' && *c <= '9')) ? *c : '_';
        name[k] = 0;
        snprintf(path, sizeof(path), "%s/%02d_%s.png", outdir, m, name);
        write_png(path, scale);
        free(img);
        n++;
    }
    printf("wrote %d maps to %s\n", n, outdir);
    return 0;
}
