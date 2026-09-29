/* Rename to test_biome_frontiers.c only after registry snippets and TS_DESERT art land. */
#include "harness.h"

static void check_geometry(void)
{
    const int all_maps[] = { MAP_SAFFRON_DUNES, MAP_SUNWELL, MAP_SUNWELL_CISTERN,
                             MAP_CORALHOOK_REEF, MAP_RIMEWIND_TUNDRA, MAP_SPORELIGHT_HOLLOW };
    for (int i = 0; i < 6; i++) {
        const MapDef *m = &MAPS[all_maps[i]];
        CHECK(m->w <= 64 && m->h <= 64 && m->obj_count <= 48 && m->decor_count < 128,
              "all six frontier maps respect geometry and prop limits");
        for (int y = 0; y < m->h; y++)
            CHECK((int)strlen(m->rows[y]) == m->w, "every frontier row has the declared width");
        map_load(all_maps[i]);
        field_load_tileset();
        CHECK(!field_tiles_failed && decor_tiles_used <= SCENE_TILE_MAX &&
              decor_tiles_wanted == decor_tiles_used, "all six maps fit 768 resident tiles");
        for (int d = 0; d < m->decor_count; d++)
            CHECK(decor_base[m->decor[d].kind] &&
                  DECOR_DEFS[m->tileset][m->decor[d].kind].tile_count,
                  "every frontier prop exists in its own tileset");
    }
    const struct { int map, x, y, turn_x, turn_y, prize_x, prize_y, back_x, back_y; } routes[] = {
        { MAP_SAFFRON_DUNES, 3, 14, 16, 17, 24, 5, 17, 17 },
        { MAP_CORALHOOK_REEF, 4, 15, 28, 19, 20, 24, 27, 19 },
        { MAP_RIMEWIND_TUNDRA, 3, 14, 24, 14, 25, 5, 23, 14 },
        { MAP_SPORELIGHT_HOLLOW, 4, 13, 24, 14, 23, 5, 23, 14 },
    };
    for (int i = 0; i < 4; i++) {
        map_load(routes[i].map);
        printf("route %s: entrance (%d,%d), encounter (%d,%d), reward (%d,%d)\n",
               MAPS[routes[i].map].name, routes[i].x, routes[i].y,
               routes[i].turn_x, routes[i].turn_y, routes[i].prize_x, routes[i].prize_y);
        flood(routes[i].x, routes[i].y);
        CHECK(reached_beside(routes[i].turn_x, routes[i].turn_y) &&
              reached_beside(routes[i].prize_x, routes[i].prize_y),
              "ordinary walk reaches encounter and optional reward without surf");
        CHECK(reached(routes[i].back_x, routes[i].back_y) &&
              cell_walkable(routes[i].back_x, routes[i].back_y),
              "reverse walk starts on reachable clear ground beside encounter");
        flood(routes[i].back_x, routes[i].back_y);
        CHECK(reached(routes[i].x, routes[i].y), "frontier has an ordinary walk back to entrance");
    }
    map_load(MAP_SAFFRON_DUNES);
    CHECK(cell_attr(23, 4) & A_GRASS, "high dune ridge holds wild encounters");
    map_load(MAP_CORALHOOK_REEF);
    CHECK((cell_attr(20, 17) & A_WATER) && MAPS[MAP_CORALHOOK_REEF].water_zone == ZONE_CORALHOOK_SURF,
          "coral channel supports surf encounters");
    map_load(MAP_SUNWELL);
    flood(3, 12);
    CHECK(reached_beside(15, 5) && reached(25, 16), "oasis ring reaches cistern and eastern gardens");
    map_load(MAP_SUNWELL_CISTERN);
    flood(6, 7);
    CHECK(reached_beside(5, 4) && reached_beside(10, 4) && reached_beside(2, 4),
          "cistern repair, healing and supplier are accessible");
}

static void check_warps(void)
{
    const struct { int from, x, y, to, dx, dy, gate; } links[] = {
        { MAP_SCORCHWASTE_1, 40, 16, MAP_SAFFRON_DUNES, 3, 14, FLAG_LANTERN_CREST },
        { MAP_SAFFRON_DUNES, 2, 14, MAP_SCORCHWASTE_1, 39, 16, FLAG_LANTERN_CREST },
        { MAP_SAFFRON_DUNES, 37, 14, MAP_SUNWELL, 3, 12, FLAG_LANTERN_CREST },
        { MAP_SUNWELL, 2, 12, MAP_SAFFRON_DUNES, 36, 14, FLAG_LANTERN_CREST },
        { MAP_SUNWELL, 15, 5, MAP_SUNWELL_CISTERN, 6, 7, FLAG_LANTERN_CREST },
        { MAP_SEA_ROUTE, 10, 30, MAP_CORALHOOK_REEF, 4, 15, FLAG_TIDE_CREST },
        { MAP_CORALHOOK_REEF, 3, 15, MAP_SEA_ROUTE, 10, 29, FLAG_TIDE_CREST },
        { MAP_AURORA_RIDGE_2, 44, 14, MAP_RIMEWIND_TUNDRA, 3, 14, FLAG_RIME_CREST },
        { MAP_RIMEWIND_TUNDRA, 2, 14, MAP_AURORA_RIDGE_2, 45, 14, FLAG_RIME_CREST },
        { MAP_GLIMMER_1, 11, 17, MAP_SPORELIGHT_HOLLOW, 4, 13, FLAG_RIME_CREST },
        { MAP_SPORELIGHT_HOLLOW, 3, 13, MAP_GLIMMER_1, 12, 17, FLAG_RIME_CREST },
    };
    for (int i = 0; i < (int)(sizeof links / sizeof links[0]); i++) {
        int w = warp_at(links[i].from, links[i].x, links[i].y);
        printf("warp %s (%d,%d) -> %s (%d,%d), flag %d\n",
               MAPS[links[i].from].name, links[i].x, links[i].y,
               MAPS[links[i].to].name, links[i].dx, links[i].dy, links[i].gate);
        CHECK(w >= 0, "frontier portal is registered");
        if (w < 0) continue;
        CHECK(WARPS[w].dest == links[i].to && WARPS[w].dx == links[i].dx &&
              WARPS[w].dy == links[i].dy && WARPS[w].required_flag == links[i].gate,
              "frontier destination and gate are exact");
        map_load(links[i].from);
        CHECK(cell_attr(links[i].x, links[i].y) & A_DOOR,
              "readable ladder portal has door semantics on new and parent floor");
        CHECK(!(cell_attr_raw(links[i].x, links[i].y) & A_EXIT),
              "explicit ladder portals do not also declare unreachable exit mats");
        map_load(links[i].to);
        CHECK(cell_walkable(links[i].dx, links[i].dy), "arrival avoids wall, water and portal");
        flag_clear(links[i].gate);
        CHECK(!warp_is_open(&WARPS[w]), "both portal directions reject absent crest");
        flag_set(links[i].gate);
        CHECK(warp_is_open(&WARPS[w]), "portal opens with inherited crest");
    }
    flag_clear(FLAG_LANTERN_CREST);
    field_enter_map(MAP_SAFFRON_DUNES, 3, 14, DIR_LEFT);
    warp.active = 0;
    player_try_move(DIR_LEFT);
    CHECK(!warp.active && cur_map == MAP_SAFFRON_DUNES,
          "real movement cannot exit dune route without Lantern crest");
    dialog_clear();
    flag_set(FLAG_LANTERN_CREST);
    player_try_move(DIR_LEFT);
    CHECK(warp.active && warp.dest == MAP_SCORCHWASTE_1,
          "real movement through newly opened reciprocal portal starts return warp");
    warp.active = 0;
    flag_clear(FLAG_LANTERN_CREST);
    field_enter_map(MAP_SUNWELL_CISTERN, 6, 8, DIR_DOWN);
    player_try_move(DIR_DOWN);
    CHECK(!warp.active && cur_map == MAP_SUNWELL_CISTERN,
          "cistern exit mat refuses the return without Lantern crest");
    flag_set(FLAG_LANTERN_CREST);
    player_try_move(DIR_DOWN);
    CHECK(warp.active && warp.dest == MAP_SUNWELL && warp.x == 15 && warp.y == 6,
          "cistern exit mat returns beside the oasis door when gate opens");
    warp.active = 0;
}

static void check_irrigation(void)
{
    fresh_game();
    CHECK(!flag(FLAG_SUNWELL_IRRIGATED), "new garden begins dry");
    scr_sunwell_repair(0);
    CHECK(quest_get(QUEST_SUNWELL_IRRIGATION) == 1 && dialog_active(),
          "meeting keeper starts bounded quest and presents a choice");
    dialog_clear();
    sunwell_repair_answer(1);
    CHECK(!flag(FLAG_SUNWELL_IRRIGATED) && bag[ITEM_IRON_ORE] == 0,
          "cancel leaves resources and garden unchanged");
    dialog_clear();
    bag_add(ITEM_IRON_ORE, 2);
    sunwell_repair_answer(0);
    CHECK(!flag(FLAG_SUNWELL_IRRIGATED) && bag[ITEM_IRON_ORE] == 2,
          "missing shard cannot partially consume repair materials");
    dialog_clear();
    bag_add(ITEM_METAL_SHARD, 1);
    bag[ITEM_GRAND_TONIC] = 998;
    sunwell_repair_answer(0);
    CHECK(!flag(FLAG_SUNWELL_IRRIGATED) && bag[ITEM_IRON_ORE] == 2 &&
          bag[ITEM_METAL_SHARD] == 1, "full reward bag cannot lose repair materials");
    dialog_clear();
    bag[ITEM_GRAND_TONIC] = 0;
    int before = bag[ITEM_GRAND_TONIC];
    sunwell_repair_answer(0);
    CHECK(flag(FLAG_SUNWELL_IRRIGATED) && quest_done(QUEST_SUNWELL_IRRIGATION) &&
          bag[ITEM_IRON_ORE] == 0 && bag[ITEM_METAL_SHARD] == 0 &&
          bag[ITEM_GRAND_TONIC] == before + 2, "successful repair exchanges materials once");
    dialog_clear();
    sunwell_repair_answer(0);
    CHECK(bag[ITEM_GRAND_TONIC] == before + 2, "repeat interaction cannot duplicate reward");
    map_load(MAP_SUNWELL);
    CHECK(MAPS[MAP_SUNWELL].zone == ZONE_NONE && cell_walkable(11, 16),
          "completed garden patch stays walkable without town encounters");
    SaveData saved;
    save_capture(&saved);
    flag_clear(FLAG_SUNWELL_IRRIGATED);
    quest_set(QUEST_SUNWELL_IRRIGATION, 1);
    save_apply(&saved);
    CHECK(flag(FLAG_SUNWELL_IRRIGATED) && quest_done(QUEST_SUNWELL_IRRIGATION),
          "garden repair flag and quest completion persist through save restore");
    map_load(MAP_SUNWELL);
    CHECK(MAPS[MAP_SUNWELL].patch_count == 1 && SUNWELL_ROWS[16][11] == '.' &&
          map_cell(11, 16) == legend_pick(legend_for(tset(), 'h'), 11, 16) &&
          !(cell_attr(11, 16) & A_GRASS),
          "restored garden patch visibly irrigates dry ground");
}

int main(void)
{
    fresh_game();
    check_geometry();
    check_warps();
    check_irrigation();
    printf("frontier failures: %d\n", failures);
    return failures ? 1 : 0;
}
