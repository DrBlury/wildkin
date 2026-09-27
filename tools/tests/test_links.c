/* Isolated loop data and local crest gates. External reciprocal stubs are
 * validated by the integration progression suite after regions merge. */
#include "harness.h"

static int has_warp(int from, int to)
{
    for (int i = 0; i < WARP_COUNT; i++)
        if (WARPS[i].map == from && WARPS[i].dest == to) return 1;
    return 0;
}

static int edge_open(int map, int side, int k)
{
    map_load(map);
    int x = side < 2 ? k : side == LINK_W ? 0 : map_w - 1;
    int y = side < 2 ? side == LINK_N ? 0 : map_h - 1 : k;
    return !(cell_attr(x, y) & (A_SOLID | A_LEDGE));
}

static void test_maps(void)
{
    static const u8 ids[] = { MAP_SCORCHWASTE_1, MAP_SCORCHWASTE_2,
        MAP_AURORA_RIDGE_1, MAP_AURORA_RIDGE_2, MAP_GREYWATER_FJORD };
    static const u8 width[] = { 48, 48, 56, 56, 40 };
    static const u8 height[] = { 40, 40, 36, 36, 64 };
    int ok = 1, music = 1, budget = 1;
    for (int i = 0; i < 5; i++) {
        map_load(ids[i]);
        const MapDef *m = &MAPS[ids[i]];
        ok &= m->w == width[i] && m->h == height[i] && m->rows;
        music &= music_song_for_map(ids[i]) != SONG_NONE;
        budget &= m->w <= MAP_MAX_W && m->h <= MAP_MAX_H && m->decor_count < 128;
        for (int y = 0; y < m->h; y++) ok &= (int)strlen(m->rows[y]) == m->w;
    }
    CHECK(ok, "all five maps load with contract dimensions and complete rows");
    CHECK(budget, "each route is within the map and decor budgets");
    CHECK(music, "every route selects a field song");
    CHECK(MAPS[MAP_SCORCHWASTE_1].tileset == TS_VOLCANIC &&
          MAPS[MAP_SCORCHWASTE_2].tileset == TS_GRIM &&
          MAPS[MAP_AURORA_RIDGE_1].tileset == TS_SNOW &&
          MAPS[MAP_GREYWATER_FJORD].tileset == TS_COAST,
          "all loops reuse their intended tilesets");
}

static void test_internal_edges(void)
{
    CHECK(MAPS[MAP_SCORCHWASTE_1].link[LINK_S] == MAP_SCORCHWASTE_2 &&
          MAPS[MAP_SCORCHWASTE_2].link[LINK_N] == MAP_SCORCHWASTE_1 &&
          edge_open(MAP_SCORCHWASTE_1, LINK_S, 20) && edge_open(MAP_SCORCHWASTE_2, LINK_N, 20),
          "Scorchwaste's two segments link at x20-21 in both directions");
    CHECK(MAPS[MAP_AURORA_RIDGE_1].link[LINK_E] == MAP_AURORA_RIDGE_2 &&
          MAPS[MAP_AURORA_RIDGE_2].link[LINK_W] == MAP_AURORA_RIDGE_1 &&
          edge_open(MAP_AURORA_RIDGE_1, LINK_E, 18) && edge_open(MAP_AURORA_RIDGE_2, LINK_W, 18),
          "Aurora Ridge's two segments link at y18-19 in both directions");
    CHECK(MAPS[MAP_SCORCHWASTE_1].link[LINK_N] == MAP_CINDERMOOR &&
          MAPS[MAP_AURORA_RIDGE_1].link[LINK_W] == MAP_FROSTHOLLOW &&
          MAPS[MAP_GREYWATER_FJORD].link[LINK_S] == MAP_PORT_BRINE,
          "each route names its external endpoint for integration");
}

static void test_gates(void)
{
    fresh_game();
    CHECK(!links_scorch_ready() && !links_aurora_ready() && !links_fjord_ready(),
          "no cave exit opens before its crest");
    flag_set(FLAG_CREST_ANVIL);
    CHECK(links_fjord_ready() && !links_scorch_ready() && !links_aurora_ready(),
          "STRENGTH opens Frostpine only after the Anvil crest");
    flag_set(FLAG_LANTERN_CREST);
    CHECK(links_scorch_ready() && !links_aurora_ready(),
          "Lantern opens Duskmere but cannot shortcut into Dreamspire");
    flag_set(FLAG_CREST_DREAM);
    CHECK(links_aurora_ready(), "Dream and Lantern together open the Aurora cave");
    map_load(MAP_DUSKMERE);
    int scorch_landing = cell_walkable(38, 34);
    map_load(MAP_DREAMSPIRE);
    int aurora_landing = cell_walkable(4, 29);
    map_load(MAP_FROSTPINE);
    int fjord_landing = cell_walkable(3, 29);
    CHECK(scorch_landing && aurora_landing && fjord_landing,
          "gated cave exits land on walkable cells in the existing maps");
    CHECK(!has_warp(MAP_SCORCHWASTE_2, MAP_DUSKMERE) &&
          !has_warp(MAP_AURORA_RIDGE_2, MAP_DREAMSPIRE) &&
          !has_warp(MAP_GREYWATER_FJORD, MAP_FROSTPINE),
          "no automatic cave warp bypasses the local crest checks");
}

static void test_integrated_joins(void)
{
    CHECK(MAPS[MAP_CINDERMOOR].link[LINK_S] == MAP_SCORCHWASTE_1 &&
          MAPS[MAP_FROSTHOLLOW].link[LINK_E] == MAP_AURORA_RIDGE_1 &&
          MAPS[MAP_PORT_BRINE].link[LINK_N] == MAP_GREYWATER_FJORD,
          "external loop edges are reciprocal");
    fresh_game();
    map_load(MAP_CINDERMOOR);
    int heat_closed = cell_attr(20, 37) & A_SOLID;
    map_load(MAP_FROSTHOLLOW);
    int ice_closed = cell_attr(42, 18) & A_SOLID;
    flag_set(FLAG_LANTERN_CREST);
    map_load(MAP_CINDERMOOR);
    int heat_open = !(cell_attr(20, 37) & A_SOLID);
    flag_set(FLAG_RIME_CREST);
    map_load(MAP_FROSTHOLLOW);
    int ice_open = !(cell_attr(42, 18) & A_SOLID);
    CHECK(heat_closed && heat_open && ice_closed && ice_open,
          "Cindermoor and Frosthollow approaches open only after their crests");
    int back[3] = { 0 }, from[3] = { MAP_DUSKMERE, MAP_DREAMSPIRE, MAP_FROSTPINE };
    int scr[3] = { SCR_LINKS_DUSK_RETURN, SCR_LINKS_DREAM_RETURN, SCR_LINKS_FROST_RETURN };
    for (int i = 0; i < NPC_COUNT; i++)
        for (int k = 0; k < 3; k++)
            if (NPCS[i].map == from[k] && NPCS[i].script == scr[k]) back[k]++;
    CHECK(back[0] == 1 && back[1] == 1 && back[2] == 1 &&
          !has_warp(MAP_DUSKMERE, MAP_SCORCHWASTE_2) &&
          !has_warp(MAP_DREAMSPIRE, MAP_AURORA_RIDGE_2) &&
          !has_warp(MAP_FROSTPINE, MAP_GREYWATER_FJORD),
          "every cave has one checked reverse guide and no ungated warp");
    map_load(MAP_SCORCHWASTE_2);
    int dusk_land = cell_walkable(4, 21);
    map_load(MAP_AURORA_RIDGE_2);
    int dream_land = cell_walkable(49, 19);
    map_load(MAP_GREYWATER_FJORD);
    CHECK(dusk_land && dream_land && cell_walkable(20, 7),
          "reverse cave landings remain walkable");
}

static void test_content(void)
{
    int count[5] = { 0 }, ice = 0, sea = 0, chest = 0;
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].trainer >= TR_LINK_ASH_A && NPCS[i].trainer <= TR_LINK_FJORD_E) {
            int map = NPCS[i].map;
            if (map == MAP_SCORCHWASTE_1 || map == MAP_SCORCHWASTE_2) count[0]++;
            if (map == MAP_AURORA_RIDGE_1 || map == MAP_AURORA_RIDGE_2) count[1]++;
            if (map == MAP_GREYWATER_FJORD) count[2]++;
        }
    CHECK(count[0] == 6 && count[1] == 6 && count[2] == 5,
          "Scorchwaste, Aurora and Greywater have 6, 6 and 5 wardens");
    for (int m = MAP_AURORA_RIDGE_1; m <= MAP_AURORA_RIDGE_2; m++) {
        map_load(m);
        for (int y = 0; y < map_h; y++) for (int x = 0; x < map_w; x++)
            ice += (cell_attr_raw(x, y) & A_ICE) != 0;
    }
    map_load(MAP_GREYWATER_FJORD);
    for (int y = 0; y < map_h; y++) for (int x = 0; x < map_w; x++)
        sea += (cell_attr_raw(x, y) & A_WATER) != 0;
    for (int i = 0; i < MAPS[MAP_GREYWATER_FJORD].obj_count; i++)
        chest += MAPS[MAP_GREYWATER_FJORD].objs[i].kind == OBJ_CHEST;
    CHECK(ice > 0 && sea > 0 && chest == 1,
          "ridge ice, fjord surf and drowned chest are present");
    CHECK(WILD_ZONES[ZONE_FJORD_SURF].count >= 5 &&
          WILD_ZONES[ZONE_GLASS_DUNES].count >= 6,
          "fjord and Glass Dunes use distinct wild encounter mixes");
}

int main(void)
{
    test_maps();
    test_internal_edges();
    test_gates();
    test_integrated_joins();
    test_content();
    printf("%d links failures\n", failures);
    return failures != 0;
}
