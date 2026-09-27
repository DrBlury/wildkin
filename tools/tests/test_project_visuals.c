/* Project terrain and ferry regression. Host build: cc -std=c11 -Wall -Wextra
 * -Wno-missing-field-initializers -Wno-unused-function -o build/test_project_visuals
 * tools/tests/test_project_visuals.c && build/test_project_visuals */
#include "harness.h"

static int clear_land(int x, int y)
{
    return !(cell_attr(x, y) & (A_SOLID | A_WATER | A_LEDGE));
}

static void test_patch_shapes(void)
{
    const int maps[] = { MAP_BROOKMILL, MAP_LUMEN, MAP_CINDER_CROSSING,
                         MAP_RAILHEAD, MAP_FOOTHILLS, MAP_TIMBERLINE, MAP_REEDWICK };
    fresh_game();
    for (unsigned i = 0; i < sizeof(maps) / sizeof(maps[0]); i++) {
        const MapDef *m = &MAPS[maps[i]];
        CHECK(m->patch_count > 0, "project map has an attached patch");
        map_load(maps[i]);
        field_load_tileset();
        CHECK(decor_tiles_wanted <= SCENE_TILE_MAX,
              "project map fits its scene-tile budget before construction");
        for (int j = 0; j < m->patch_count; j++) {
            const MapPatch *p = &m->patches[j];
            CHECK(p->x + p->w <= m->w && p->y + p->h <= m->h && p->w && p->h,
                  "project patch stays within its map");
            for (int y = 0; y < p->h; y++)
                CHECK(!p->rows || (int)strlen(p->rows[y]) == p->w,
                      "project patch row has declared width");
        }
    }
}

static void test_cinder_bridge(void)
{
    fresh_game();
    map_load(MAP_CINDER_CROSSING);
    CHECK(cell_attr(7, 20) & A_WATER, "Cinder deck is flooded before construction");
    CHECK(clear_land(4, 21) && clear_land(11, 21), "both guide landings remain on dry land");
    flood(4, 21);
    CHECK(!reached(11, 21), "without SURF the unrepaired crossing blocks the road");
    flag_set(FLAG_PROJECT_CINDER_BRIDGE);
    map_load(MAP_CINDER_CROSSING);
    CHECK(clear_land(7, 20) && clear_land(7, 21), "the repaired deck replaces both flooded rows");
    flood(4, 21);
    CHECK(reached(11, 21), "repaired deck leads from west to east on foot");
    flood(11, 21);
    CHECK(reached(4, 21), "repaired deck leads back from east to west on foot");
}

static void test_projects_and_landings(void)
{
    const struct { int map, x, y, flag; } sites[] = {
        { MAP_BROOKMILL, 35, 30, FLAG_PROJECT_TRAM },
        { MAP_LUMEN, 35, 22, FLAG_PROJECT_TRAM },
        { MAP_RAILHEAD, 26, 18, FLAG_PROJECT_CINDER_BRIDGE },
        { MAP_FOOTHILLS, 9, 49, FLAG_PROJECT_LIFT },
        { MAP_TIMBERLINE, 9, 28, FLAG_PROJECT_LIFT },
        { MAP_REEDWICK, 25, 25, FLAG_PROJECT_REED_FERRY }
    };
    for (unsigned i = 0; i < sizeof(sites) / sizeof(sites[0]); i++) {
        fresh_game();
        map_load(sites[i].map);
        u16 before = map_cells[sites[i].y * map_w + sites[i].x];
        flag_set(sites[i].flag);
        map_load(sites[i].map);
        CHECK(map_cells[sites[i].y * map_w + sites[i].x] != before,
              "completion flag visibly changes the project site");
        field_load_tileset();
        CHECK(decor_tiles_wanted <= SCENE_TILE_MAX,
              "completed project still fits its scene-tile budget");
    }
    const struct { int map, x, y; } landings[] = {
        { MAP_TOWN, 12, 17 }, { MAP_BROOKMILL, 31, 29 },
        { MAP_LUMEN, 36, 20 }, { MAP_FOOTHILLS, 11, 52 },
        { MAP_TIMBERLINE, 11, 30 }, { MAP_REEDWICK, 25, 20 }, { MAP_LAKE, 31, 17 }
    };
    fresh_game();
    for (unsigned i = 0; i < sizeof(landings) / sizeof(landings[0]); i++) {
        map_load(landings[i].map);
        CHECK(clear_land(landings[i].x, landings[i].y) &&
              npc_at(landings[i].x, landings[i].y) < 0,
              "return landing is clear before the project is built");
    }
}

static void test_punt_voyage(void)
{
    fresh_game();
    flag_set(FLAG_PROJECT_REED_FERRY);
    field_enter_map(MAP_REEDWICK, 25, 20, DIR_DOWN);
    saga_punt_sail(1);
    CHECK(game_mode == MODE_EXT && voy.map == MAP_LAKE && voy.x == 31 && voy.y == 17,
          "outbound punt opens the animated boat voyage");
    voyage_land();
    CHECK(cur_map == MAP_LAKE && player.x == 31 && player.y == 17,
          "outbound punt lands at the lake return guide");
    saga_punt_sail(0);
    CHECK(game_mode == MODE_EXT && voy.map == MAP_REEDWICK && voy.x == 25 && voy.y == 20,
          "return punt opens the animated boat voyage");
    voyage_land();
    CHECK(cur_map == MAP_REEDWICK && player.x == 25 && player.y == 20,
          "return punt lands at Reedwick's guide");
}

int main(void)
{
    game_init();
    test_patch_shapes();
    test_cinder_bridge();
    test_projects_and_landings();
    test_punt_voyage();
    printf("project visuals: %d failures\n", failures);
    return failures ? 1 : 0;
}
