/* Area boundaries must never reinterpret the previous area's screen entries. */
#include "harness.h"

static void test_room_edges(void)
{
    fresh_game();
    int checked = 0, ok = 1;
    for (int id = 0; id < MAP_COUNT; id++) {
        if (MAPS[id].tileset != TS_INTERIOR || MAPS[id].w >= 15) continue;
        field_enter_map(id, MAPS[id].w / 2, MAPS[id].h / 2, DIR_DOWN);
        field_setup_bg();
        /* Simulate the outdoor ring left behind by a door transition. */
        for (int i = 0; i < 1024; i++) {
            VRAM_MAP(SB_FIELD_BOTTOM)[i] = 0x1234;
            VRAM_MAP(SB_PANEL)[i] = 0x2345;
            VRAM_MAP(SB_FIELD_TOP)[i] = 0x3456;
        }
        field_render_view();
        int x0 = floor_div16(cam_x), y0 = floor_div16(cam_y);
        for (int y = y0; y <= y0 + 10; y++)
            for (int x = x0; x <= x0 + 15; x++) {
                if (x >= 0 && x < map_w) continue;
                int at = (y & 15) * 64 + (x & 15) * 2;
                static const int off[] = {0, 1, 32, 33};
                for (int q = 0; q < 4; q++) {
                    u16 e = VRAM_MAP(SB_FIELD_BOTTOM)[at + off[q]];
                    if (VRAM_MAP(SB_PANEL)[at + off[q]] || VRAM_MAP(SB_FIELD_TOP)[at + off[q]]) ok = 0;
                    for (int row = 0; row < 8; row++) {
                        u32 pixels = VRAM_SCENE_TILES[(e & 1023) * 8 + row];
                        for (int px = 0; px < 8; px++) {
                            int c = (pixels >> (px * 4)) & 15;
                            if (bg_palette[c ? (e >> 12) * 16 + c : 0] != 0) ok = 0;
                        }
                    }
                }
                if (ring_x[y & 15][x & 15] != x || ring_y[y & 15][x & 15] != y) ok = 0;
            }
        checked++;
    }
    CHECK(checked > 0 && ok, "every narrow interior repaints both margins black and clears all overlay layers");
}

static int resident_pixels_match(void)
{
    const TilesetDef *t = tset();
    for (int id = 0; id < t->tile_count; id++) {
        int slot = field_tile_slot[id];
        if (slot == FIELD_TILE_MISSING) continue;
        if (slot >= decor_tiles_used) return 0;
        const u32 *expected = t->tiles + id * 8;
        for (int a = 0; a < t->anim_count; a++) {
            const TileAnim *anim = &t->anims[a];
            if (id >= anim->tile && id < anim->tile + anim->count) {
                int frame = field_anim_frame / anim->period % anim->frames;
                expected = anim->data + (frame * anim->count + id - anim->tile) * 8;
            }
        }
        if (memcmp(VRAM_SCENE_TILES + slot * 8, expected, 32)) return 0;
    }
    for (int k = 0; k < DK_COUNT; k++) {
        if (!decor_base[k]) continue;
        const DecorDef *d = &DECOR_DEFS[map_tileset][k];
        int frame = d->frames > 1 && d->period ? field_anim_frame / d->period % d->frames : 0;
        if (memcmp(VRAM_SCENE_TILES + decor_base[k] * 8,
                   decor_tiles + (d->tile_first + frame * d->tile_count) * 8, d->tile_count * 32)) return 0;
    }
    return 1;
}

static void test_area_residency(void)
{
    fresh_game();
    int fits = 1, pixels = 1, isolated = 1, compact = 0, peak = 0;
    for (int id = 0; id < MAP_COUNT; id++) {
        map_load(id);
        field_anim_frame = 0;
        /* The area loader must not overwrite the adjacent UI allocation. */
        fill32(VRAM_UI_TILES, 0x76543210, CANVAS_CELLS * 8);
        field_load_tileset();
        for (int tile = 1; tile < tset()->tile_count; tile++)
            if (field_tile_slot[tile] != FIELD_TILE_MISSING) isolated = 0;
        u8 kinds[DK_COUNT] = {0};
        for (int i = 0; i < MAPS[id].decor_count; i++) kinds[MAPS[id].decor[i].kind] = 1;
        for (int k = 0; k < DK_COUNT; k++)
            if (!!decor_base[k] != !!kinds[k]) isolated = 0;
        for (int y = -1; y <= map_h; y++)
            for (int x = -1; x <= map_w; x++) render_cell(x, y);
        if (!resident_pixels_match()) pixels = 0;
        if (field_tiles_failed || decor_tiles_used > SCENE_TILE_MAX || decor_tiles_wanted != decor_tiles_used) {
            printf("  area %s exceeded its tile budget (%d/%d)\n", MAPS[id].name, decor_tiles_used, decor_tiles_wanted);
            fits = 0;
        }
        int old_budget = tset()->tile_count + field_decor_tiles;
        if (decor_tiles_used < old_budget) compact++;
        if (decor_tiles_used > peak) peak = decor_tiles_used;
        if (id == MAP_TOWN || id == MAP_MEADOW || id == MAP_HOME)
            printf("  %s: %d resident tiles, previously %d\n", MAPS[id].name, decor_tiles_used, old_budget);
        /* Animate only resident terrain, never into a decor or UI slot. */
        for (int f = 0; f < 120; f++) field_animate_tiles();
        if (!resident_pixels_match()) pixels = 0;
        for (int word = 0; word < CANVAS_CELLS * 8; word++)
            if (VRAM_UI_TILES[word] != 0x76543210) isolated = 0;
        for (int word = decor_tiles_used * 8; word < SCENE_TILE_MAX * 8; word++)
            if (VRAM_SCENE_TILES[word]) isolated = 0;
    }
    printf("  %d maps checked; peak %d/%d resident tiles; %d maps use fewer tiles\n", MAP_COUNT, peak, SCENE_TILE_MAX, compact);
    CHECK(fits, "all maps and their boundaries fit in the area-local scene cache");
    CHECK(pixels, "resident terrain and decor match ROM pixels before and after animation");
    CHECK(isolated, "area changes discard other-area tiles and preserve UI memory");
    CHECK(compact > MAP_COUNT / 2, "most maps leave unused regional graphics in ROM rather than VRAM");

    map_load(MAP_WILLOW_ACRE);
    field_load_tileset();
    /* Every possible crop/soil state may appear during a long farm visit. */
    for (int tile = 1; tile < tset()->tile_count; tile++) field_tile_entry((u16)tile);
    CHECK(!field_tiles_failed && resident_pixels_match(), "all dynamic farm art can become resident without overwriting decor");

    map_load(MAP_HOME);
    field_load_tileset();
    int kind = MAPS[MAP_HOME].decor[0].kind;
    CHECK(decor_entry(0x1000, kind) == 0 && field_tiles_failed,
          "decor with a missing local tile cannot alias another graphics block");
    field_load_tileset();
    int before = decor_tiles_used;
    CHECK(field_tile_entry(1023) == 0 && field_tiles_failed && decor_tiles_used == before,
          "invalid terrain references fail closed without reading unrelated graphics");
    field_load_tileset();
    int missing = 1;
    while (missing < tset()->tile_count && field_tile_slot[missing] != FIELD_TILE_MISSING) missing++;
    decor_tiles_used = SCENE_TILE_MAX;
    CHECK(field_tile_entry((u16)missing) == 0 && field_tiles_failed && decor_tiles_used == SCENE_TILE_MAX,
          "tile capacity exhaustion cannot write into UI VRAM");
}

int main(void)
{
    test_room_edges();
    test_area_residency();
    return failures ? 1 : 0;
}
