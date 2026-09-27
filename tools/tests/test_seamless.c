/* Real two-map horizontal streaming and palette-safe fade fallbacks. */
#include "harness.h"

static int split_weather(int map)
{
    return map == MAP_BROOKMILL_TRAIL ? WX_RAIN : WX_CLEAR;
}

static void prepare_edge(int source, int dest, int side, int x, int y)
{
    map_load(source);
    field_load_tileset();
    player.x = (s16)x;
    player.y = (s16)y;
    player.ox = player.oy = player.moving = 0;
    player.facing = side == LINK_E ? DIR_RIGHT : DIR_LEFT;
    field_update_camera();
    field_render_view();
    int origin = side == LINK_E ? map_w : -MAPS[dest].w;
    for (int frame = 0; frame < 48 && !(seam.ready && seam.map == dest); frame++) {
        seam_prepare(dest, origin, side);
        field_render_view(); /* stage one missing decor kind in VRAM per vblank */
    }
    field_update_camera();
    field_render_view();
}

static void check_visible_ring(void)
{
    int complete = 1;
    for (int y = floor_div16(cam_y); y <= floor_div16(cam_y) + 10; y++)
        for (int x = floor_div16(cam_x); x <= floor_div16(cam_x) + 15; x++)
            if (ring_x[y & 15][x & 15] != x || ring_y[y & 15][x & 15] != y)
                complete = 0;
    CHECK(complete, "all camera cells carry the matching world-space ring coordinates");
}

static void finish_fade(void)
{
    for (int frame = 0; frame < 20 && warp.active; frame++) field_warp_update();
}

int main(void)
{
    fresh_game();
    give_starter();
    flag_set(FLAG_STORM_CALMED); /* road wardens leave both y=17 and y=18 exits */
    opt.autosave = 0;
    CHECK(MAPS[MAP_WOOD].tileset == MAPS[MAP_BROOKMILL_TRAIL].tileset &&
          MAPS[MAP_WOOD].h == MAPS[MAP_BROOKMILL_TRAIL].h, "Bramblewood and Trail qualify for horizontal streaming");
    CHECK(MAPS[MAP_BROOKMILL_TRAIL].tileset != MAPS[MAP_BROOKMILL].tileset &&
          MAPS[MAP_BROOKMILL].tileset != MAPS[MAP_COPPERLINE].tileset,
          "the other two route edges use incompatible tilesets and must fade");

    prepare_edge(MAP_WOOD, MAP_BROOKMILL_TRAIL, LINK_E, MAPS[MAP_WOOD].w - 1, 17);
    CHECK(seam.ready && seam.map == MAP_BROOKMILL_TRAIL && seam.origin == map_w &&
          seam_pending == MAP_NONE, "neighbour terrain is decoded before crossing and decor upload is complete");
    int (*normal_weather)(int) = events_weather_here;
    events_weather_here = split_weather;
    CHECK(!edge_palette_compatible(MAP_WOOD, MAP_BROOKMILL_TRAIL),
          "same tileset but different rain tints cannot share a palette");
    events_weather_here = normal_weather;
    CHECK(cam_x > map_w * 16 - SCREEN_WIDTH &&
          ring_x[17 & 15][(map_w - 1) & 15] == map_w - 1 &&
          ring_x[17 & 15][map_w & 15] == map_w,
          "scroll passes the former camera clamp with both maps resident in one ring");
    check_visible_ring();
    int unique = -1;
    for (int i = 0; i < MAPS[MAP_BROOKMILL_TRAIL].decor_count; i++) {
        int k = MAPS[MAP_BROOKMILL_TRAIL].decor[i].kind;
        int found = 0;
        for (int j = 0; j < MAPS[MAP_WOOD].decor_count; j++)
            if (MAPS[MAP_WOOD].decor[j].kind == k) found = 1;
        if (!found) { unique = k; break; }
    }
    CHECK(unique >= 0 && decor_base[unique] &&
          memcmp(VRAM_SCENE_TILES + decor_base[unique] * 8,
                 decor_tiles + DECOR_DEFS[map_tileset][unique].tile_first * 8,
                 DECOR_DEFS[map_tileset][unique].tile_count * 32) == 0,
          "destination-only decor is staged at its actual VRAM tile index");
    u16 palette[128], preview[8][11][12];
    for (int i = 0; i < 128; i++) palette[i] = bg_palette[i];
    int y0 = floor_div16(cam_y);
    static const u8 off[4] = { 0, 1, 32, 33 };
    for (int x = 0; x < 8; x++)
        for (int y = 0; y < 11; y++) {
            int idx = ((y0 + y) & 15) * 64 + ((map_w + x) & 15) * 2;
            for (int i = 0; i < 4; i++) {
                preview[x][y][i] = VRAM_MAP(SB_FIELD_BOTTOM)[idx + off[i]];
                preview[x][y][i + 4] = VRAM_MAP(SB_PANEL)[idx + off[i]];
                preview[x][y][i + 8] = VRAM_MAP(SB_FIELD_TOP)[idx + off[i]];
            }
        }
    int before = cam_x, old_w = map_w;
    CHECK(cell_walkable(player.x, player.y) && try_edge_link(DIR_RIGHT, map_w, player.y) &&
          cur_map == MAP_BROOKMILL_TRAIL && !warp.active && player.moving && player.ox == -15 &&
          player.x == 0 && player.y == 17 && seam_origin_x == old_w,
          "crossing rebases the player and starts a normal walking step without any fade");
    field_update_camera();
    field_render_view();
    CHECK(cam_x == before + 1, "camera advances one pixel, not a whole tile, at the map swap");
    check_visible_ring();
    int exact = 1;
    for (int x = 0; x < 8; x++)
        for (int y = 0; y < 11; y++) {
            field_redraw_cell(x, y0 + y);
            render_cell(x, y0 + y); /* destination's authoritative full-elevation renderer */
            int idx = ((y0 + y) & 15) * 64 + ((seam_origin_x + x) & 15) * 2;
            for (int i = 0; i < 4; i++)
                if (preview[x][y][i] != VRAM_MAP(SB_FIELD_BOTTOM)[idx + off[i]] ||
                    preview[x][y][i + 4] != VRAM_MAP(SB_PANEL)[idx + off[i]] ||
                    preview[x][y][i + 8] != VRAM_MAP(SB_FIELD_TOP)[idx + off[i]]) exact = 0;
        }
    CHECK(exact, "all streamed BG0/BG2/BG3 entries match destination decor and elevation rendering");
    int same_palette = 1;
    for (int i = 0; i < 128; i++) if (palette[i] != bg_palette[i]) same_palette = 0;
    CHECK(same_palette && decor_base[unique], "both sides retain the same BG palette and decor address after arrival");
    int npcs_loaded = 1;
    for (int i = 0; i < NPC_COUNT; i++)
        if (!!npc_visible[i] != (NPCS[i].map == cur_map && npc_condition(&NPCS[i]))) npcs_loaded = 0;
    CHECK(npcs_loaded && wild_spawn_timer == 30, "destination NPCs and wild spawn timer refresh on the seam");
    CHECK(travel_visited_get(MAP_BROOKMILL_TRAIL), "seam arrival records map visitation");
    while (player.moving) actor_step(&player, 2);
    for (int offset = 1; offset <= 5; offset++) {
        player.y = (s16)(17 + offset);
        for (int frame = 0; frame < 5; frame++) {
            seam_prepare(MAP_WOOD, 0, LINK_W);
            field_update_camera();
            field_render_view();
        }
        check_visible_ring();
    }
    CHECK(seam.ready && seam.y[(floor_div16(cam_y) + 10) & 15][43 & 15] ==
          floor_div16(cam_y) + 10,
          "former map's new rows stream before vertical scroll exposes them");
    player.y = 17;
    field_update_camera();
    seam_prepare(MAP_WOOD, 0, LINK_W);
    field_render_view();
    field_update_camera();
    before = cam_x;
    CHECK(seam.ready && seam.map == MAP_WOOD &&
          try_edge_link(DIR_LEFT, -1, 17) && !warp.active &&
          cur_map == MAP_WOOD && player.x == MAPS[MAP_WOOD].w - 1 && player.ox == 15,
          "return crossing rebases to the exact former border without a fade");
    field_update_camera();
    field_render_view();
    CHECK(cam_x == before - 1, "return scroll also advances by just one pixel");
    check_visible_ring();
    while (player.moving) actor_step(&player, 2);
    CHECK(save_write() && save_load() && cur_map == MAP_WOOD &&
          player.x == MAPS[MAP_WOOD].w - 1 && player.y == 17 &&
          flag(FLAG_STORM_CALMED) && travel_visited_get(MAP_BROOKMILL_TRAIL) &&
          seam_origin_x == 0, "saving after a seam reloads normal map-local coordinates and story state");

    map_load(MAP_BROOKMILL_TRAIL);
    field_load_tileset();
    warp.active = 0;
    CHECK(try_edge_link(DIR_RIGHT, map_w, 17) && warp.active && warp.duration == 9,
          "Trail to Brookmill retains the full palette-safe fade");
    finish_fade();
    map_load(MAP_BROOKMILL);
    field_load_tileset();
    warp.active = 0;
    CHECK(try_edge_link(DIR_RIGHT, map_w, 17) && warp.active && warp.duration == 9,
          "Brookmill to Copperline retains the full palette-safe fade");
    map_load(MAP_WOOD);
    field_load_tileset();
    warp.active = 0;
    CHECK(try_edge_link(DIR_RIGHT, map_w, 17) && warp.active && warp.duration == 6,
          "a same-palette edge not yet prefetched retains its short fade");
    return failures ? 1 : 0;
}
