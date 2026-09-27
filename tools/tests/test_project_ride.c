/* Project transport scene, gating and land-arrival checks. */
#include "harness.h"

static void enter_stop(int map, int x, int y)
{
    dialog_clear();
    game_mode = MODE_FIELD;
    field_enter_map(map, x, y, DIR_DOWN);
    warp.active = 0;
    set_brightness(0);
}

static void finish_ride(void)
{
    for (int f = 0; f < PROJECT_RIDE_END + 20 && game_mode == MODE_EXT; f++) step(0);
    settle();
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    fresh_game();
    give_starter();
    enter_stop(MAP_TOWN, 12, 17);

    travel_project_ride_to(PROJECT_RIDE_TRAM, MAP_BROOKMILL, 31, 29);
    CHECK(game_mode == MODE_FIELD && !warp.active && cur_map == MAP_TOWN,
          "unfinished tram cannot launch or warp");
    flag_set(FLAG_PROJECT_TRAM);
    travel_project_ride_to(99, MAP_BROOKMILL, 31, 29);
    travel_project_ride_to(PROJECT_RIDE_TRAM, MAP_COUNT, 0, 0);
    travel_project_ride_to(PROJECT_RIDE_TRAM, MAP_BROOKMILL, 999, 29);
    CHECK(game_mode == MODE_FIELD && !warp.active, "unknown kind and invalid destinations do nothing");

    travel_project_ride_to(PROJECT_RIDE_TRAM, MAP_BROOKMILL, 31, 29);
    CHECK(game_mode == MODE_EXT && project_ride.t == 0 && project_ride.kind == PROJECT_RIDE_TRAM,
          "tram opens its own timed land scene");
    CHECK(VRAM_MAP(SB_FIELD_BOTTOM)[14 * 32] == 2 &&
          VRAM_OBJ_TILES[OT_BOAT * 8 + 44] != travel_boat_gfx[0][44],
          "tram draws rails and a non-boat vehicle sprite");
    for (int f = 0; f < 32; f++) step(0);
    int before = project_ride.t;
    step(KEY_A);
    CHECK(before >= 24 && project_ride.t >= PROJECT_RIDE_END - 16,
          "A skips the middle but preserves the exit fade");
    finish_ride();
    CHECK(game_mode == MODE_FIELD && !warp.active && cur_map == MAP_BROOKMILL &&
          cell_walkable(player.x, player.y) && !(cell_attr(player.x, player.y) & A_WATER),
          "tram lands safely on walkable Brookmill ground");

    enter_stop(MAP_FOOTHILLS, 11, 52);
    travel_project_ride_to(PROJECT_RIDE_LIFT, MAP_TIMBERLINE, 11, 29);
    CHECK(game_mode == MODE_FIELD && !warp.active && cur_map == MAP_FOOTHILLS,
          "unfinished lift cannot launch or warp");
    flag_set(FLAG_PROJECT_LIFT);
    travel_project_ride_to(PROJECT_RIDE_LIFT, MAP_TIMBERLINE, 11, 29);
    CHECK(game_mode == MODE_EXT && project_ride.kind == PROJECT_RIDE_LIFT &&
          VRAM_MAP(SB_FIELD_BOTTOM)[6 * 32] == 0,
          "lift opens a distinct cable-and-hillside scene");
    finish_ride();
    CHECK(game_mode == MODE_FIELD && !warp.active && cur_map == MAP_TIMBERLINE &&
          cell_walkable(player.x, player.y) && !(cell_attr(player.x, player.y) & A_WATER),
          "lift lands safely on walkable Timberline ground");

    travel_project_ride_to(PROJECT_RIDE_TRAM, MAP_TOWN, 12, 17);
    CHECK(game_mode == MODE_FIELD && warp.active && warp.dest == MAP_TOWN,
          "unsupported stop pair retains the fade-warp fallback");
    settle();
    CHECK(sizeof(TravelState) == 65, "project ride leaves travel save layout unchanged");
    if (failures) printf("%d project ride checks failed\n", failures);
    else printf("all project ride checks passed\n");
    return failures ? 1 : 0;
}
