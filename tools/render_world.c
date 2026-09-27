/*
 * Renders every map with the game's own drawing code (field.c render_cell:
 * autotiles, ground blends, the height layer, decor, farm plots) plus the
 * people standing on it, for the README world map (tools/make_media.py
 * world) and for looking at maps without the emulator:
 *
 *   cc -std=c11 -o build/render_world tools/render_world.c
 *   build/render_world OUTDIR
 *
 * Writes OUTDIR/maps.txt (one line per map: id name|w|h|outdoor|link N S W
 * E|link offsets), OUTDIR/positions.txt (id x y in tiles for placed
 * outdoor maps), and OUTDIR/<id>.rgb (w*16 x h*16 pixels, 3 bytes each).
 * Noon, clear weather, the storm calmed.
 */
/* Tile-space layout shared by the renderer and the isolated layout test.
 * A warp hint is relative to a placed anchor; it never overrides an edge. */
#include <stdio.h>

typedef struct {
    int w, h, outdoor, link[4], off[4];
} WorldMap;
typedef struct { int map, anchor, dx, dy; } WorldHint;
typedef struct { int x, y, placed; } WorldPlace;

static int world_layout(const WorldMap *maps, int count, const WorldHint *hints,
                        int hint_count, WorldPlace *pos, FILE *errors)
{
    if (count < 1 || count > 255) return -1;
    for (int i = 0; i < count; i++) pos[i] = (WorldPlace){0, 0, 0};
    pos[0].placed = 1;
    int changed;
    do {
        changed = 0;
        for (int m = 0; m < count; m++) {
            if (!pos[m].placed) continue;
            for (int d = 0; d < 4; d++) {
                int n = maps[m].link[d];
                if (n < 0 || n >= count || pos[n].placed) continue;
                int x = pos[m].x, y = pos[m].y;
                if (d == 0) { x += maps[m].off[d]; y -= maps[n].h; }
                if (d == 1) { x += maps[m].off[d]; y += maps[m].h; }
                if (d == 2) { x -= maps[n].w; y += maps[m].off[d]; }
                if (d == 3) { x += maps[m].w; y += maps[m].off[d]; }
                pos[n] = (WorldPlace){x, y, 1};
                changed = 1;
            }
        }
        for (int i = 0; i < hint_count; i++) {
            WorldHint h = hints[i];
            if (h.map < 0 || h.map >= count || h.anchor < 0 || h.anchor >= count) {
                fprintf(errors, "invalid WORLD_POS map %d anchor %d\n", h.map, h.anchor);
                return -1;
            }
            if (!pos[h.anchor].placed || pos[h.map].placed) continue;
            pos[h.map] = (WorldPlace){pos[h.anchor].x + h.dx, pos[h.anchor].y + h.dy, 1};
            changed = 1;
        }
    } while (changed);
    int overlaps = 0;
    for (int m = 0; m < count; m++)
        if (maps[m].outdoor && !pos[m].placed)
            fprintf(errors, "world map %d has no edge path or WORLD_POS hint\n", m);
    for (int a = 0; a < count; a++) {
        if (!pos[a].placed || !maps[a].outdoor) continue;
        for (int b = a + 1; b < count; b++) {
            if (!pos[b].placed || !maps[b].outdoor) continue;
            if (pos[a].x < pos[b].x + maps[b].w && pos[b].x < pos[a].x + maps[a].w &&
                pos[a].y < pos[b].y + maps[b].h && pos[b].y < pos[a].y + maps[a].h) {
                fprintf(errors, "world overlap: map %d and map %d\n", a, b);
                overlaps++;
            }
        }
    }
    return overlaps;
}

#ifndef WORLD_LAYOUT_TEST
#define main gba_main
#include "../src/main.c"
#undef main

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static u8 *px;
static int pw, ph;

static void put(int x, int y, u16 c)
{
    if (x < 0 || y < 0 || x >= pw || y >= ph) return;
    u8 *d = px + (y * pw + x) * 3;
    d[0] = (u8)((c & 31) << 3 | (c & 31) >> 2);
    d[1] = (u8)(((c >> 5) & 31) << 3 | ((c >> 5) & 31) >> 2);
    d[2] = (u8)(((c >> 10) & 31) << 3 | ((c >> 10) & 31) >> 2);
}

/* One map entry (tile | hflip | vflip | bank) of scene tiles at (x0, y0). */
static void draw_entry(u16 e, int x0, int y0, int opaque)
{
    const u32 *t = VRAM_SCENE_TILES + (e & 1023) * 8;
    int bank = e >> 12, hf = (e >> 10) & 1, vf = (e >> 11) & 1;
    for (int y = 0; y < 8; y++) {
        u32 row = t[vf ? 7 - y : y];
        for (int x = 0; x < 8; x++) {
            int c = (row >> (4 * (hf ? 7 - x : x))) & 15;
            if (!c && !opaque) continue;
            put(x0 + x, y0 + y, c ? bg_palette[bank * 16 + c] : bg_palette[0]);
        }
    }
}

/* A 16x32 overworld sprite (2x4 tiles, 1D) with its 16 colours. */
static void draw_sprite(const u32 *gfx, const u16 *pal, int x0, int y0, int flip)
{
    for (int ty = 0; ty < 4; ty++)
        for (int tx = 0; tx < 2; tx++) {
            const u32 *t = gfx + (ty * 2 + tx) * 8;
            for (int y = 0; y < 8; y++)
                for (int x = 0; x < 8; x++) {
                    int c = (t[y] >> (4 * x)) & 15;
                    if (!c) continue;
                    int sx = tx * 8 + x;
                    put(x0 + (flip ? 15 - sx : sx), y0 + ty * 8 + y, pal[c]);
                }
        }
}

#define TOWN_SPOT(key, map, x, y, kind)
#define WORLD_POS(map, anchor, dx, dy) { map, anchor, dx, dy },
static const WorldHint world_hints[] = {
#include "../src/game/world/worldpos.inc"
    { -1, -1, 0, 0 }
};
#undef WORLD_POS
#undef TOWN_SPOT

static const u8 OFF[4] = { 0, 1, 32, 33 };

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: %s OUTDIR\n", argv[0]);
        return 1;
    }
    game_init();
    new_game();
    flag_set(FLAG_STORM_CALMED);
    gtime.minute = 12 * 60;
    gtime.weather = WEATHER_CLEAR;
    char path[512];
    snprintf(path, sizeof(path), "%s/maps.txt", argv[1]);
    FILE *list = fopen(path, "w");
    if (!list) {
        perror(path);
        return 1;
    }
    WorldMap layout_maps[MAP_COUNT];
    WorldPlace positions[MAP_COUNT];
    for (int m = 0; m < MAP_COUNT; m++) {
        const MapDef *d = &MAPS[m];
        layout_maps[m].w = d->w;
        layout_maps[m].h = d->h;
        layout_maps[m].outdoor = (d->flags & MF_OUTDOOR) && !(d->flags & MF_DEBUG) &&
                                 strncmp(d->name, "TEST ", 5) != 0;
        for (int dir = 0; dir < 4; dir++) {
            layout_maps[m].link[dir] = d->link[dir];
            layout_maps[m].off[dir] = d->link_off[dir];
        }
    }
    int layout_errors = world_layout(layout_maps, MAP_COUNT, world_hints,
                                     (int)(sizeof(world_hints) / sizeof(world_hints[0])) - 1,
                                     positions, stderr);
    if (layout_errors) {
        fclose(list);
        fprintf(stderr, "world layout failed (%d conflicts)\n", layout_errors);
        return 1;
    }
    snprintf(path, sizeof(path), "%s/positions.txt", argv[1]);
    FILE *placed = fopen(path, "w");
    if (!placed) { perror(path); fclose(list); return 1; }
    for (int m = 0; m < MAP_COUNT; m++)
        if (positions[m].placed && layout_maps[m].outdoor)
            fprintf(placed, "%d %d %d\n", m, positions[m].x, positions[m].y);
    fclose(placed);
    for (int m = 0; m < MAP_COUNT; m++) {
        const MapDef *d = &MAPS[m];
        if (d->flags & MF_DEBUG) continue;
        field_enter_map(m, 1, 1, DIR_DOWN);
        dialog_clear();
        field_load_palettes();
        pw = map_w * 16;
        ph = map_h * 16;
        px = calloc((size_t)pw * ph, 3);
        u16 *b = VRAM_MAP(SB_FIELD_BOTTOM), *mid = VRAM_MAP(SB_PANEL), *tp = VRAM_MAP(SB_FIELD_TOP);
        /* ground and mid layers, then people, then the top layer over them */
        static u16 tops[64 * 64][4];
        for (int y = 0; y < map_h; y++)
            for (int x = 0; x < map_w; x++) {
                field_redraw_cell(x, y);
                render_cell(x, y);
                int idx = (y & 15) * 2 * 32 + (x & 15) * 2;
                for (int i = 0; i < 4; i++) {
                    int qx = x * 16 + (i & 1) * 8, qy = y * 16 + (i >> 1) * 8;
                    draw_entry(b[idx + OFF[i]], qx, qy, 1);
                    if (mid[idx + OFF[i]]) draw_entry(mid[idx + OFF[i]], qx, qy, 0);
                    tops[y * map_w + x][i] = tp[idx + OFF[i]];
                }
            }
        for (int i = 0; i < NPC_COUNT; i++) {
            if (NPCS[i].map != m) continue;
            const Actor *a = &npc_state[i];
            u8 lk, lv;
            static u16 pal[16];
            const u32 *gfx;
            if (npc_keeper_look(i, &lk, &lv)) {
                gfx = keeper_ow_gfx[lk][0];
                keeper_palette(pal, lk, lv);
            } else {
                gfx = char_gfx[NPCS[i].chr][0];
                copy16(pal, char_palettes[NPCS[i].chr], 16);
            }
            draw_sprite(gfx, pal, a->x * 16, a->y * 16 - 16, a->facing == DIR_RIGHT);
        }
        for (int y = 0; y < map_h; y++)
            for (int x = 0; x < map_w; x++)
                for (int i = 0; i < 4; i++)
                    if (tops[y * map_w + x][i])
                        draw_entry(tops[y * map_w + x][i], x * 16 + (i & 1) * 8, y * 16 + (i >> 1) * 8, 0);
        snprintf(path, sizeof(path), "%s/%d.rgb", argv[1], m);
        FILE *f = fopen(path, "wb");
        fwrite(px, 3, (size_t)pw * ph, f);
        fclose(f);
        free(px);
        fprintf(list, "%d %s|%d|%d|%d|%d %d %d %d|%d %d %d %d\n", m, d->name, map_w, map_h,
                (d->flags & MF_OUTDOOR) != 0, d->link[0], d->link[1], d->link[2], d->link[3],
                d->link_off[0], d->link_off[1], d->link_off[2], d->link_off[3]);
    }
    fclose(list);
    return 0;
}

#endif /* WORLD_LAYOUT_TEST */
