/* Focused Rootways topology, bilateral crest gate and permanent plate test. */
#include "harness.h"

static int adjacent_open(int map, int x, int y)
{
    if (cur_map != map) map_load(map);
    return cell_walkable(x - 1, y) || cell_walkable(x + 1, y) ||
           cell_walkable(x, y - 1) || cell_walkable(x, y + 1);
}

static void check_warps(void)
{
    const struct { int map, x, y, dest; } links[] = {
        { MAP_WOOD, 17, 5, MAP_ROOTWOOD_PATH },
        { MAP_ROOTWOOD_PATH, 2, 7, MAP_WOOD },
        { MAP_ROOTWOOD_PATH, 17, 3, MAP_ROOTWAYS },
        { MAP_ROOTWAYS, 2, 8, MAP_ROOTWOOD_PATH },
        { MAP_ROOTWAYS, 21, 3, MAP_MILL_CELLAR },
        { MAP_MILL_CELLAR, 6, 2, MAP_ROOTWAYS },
        { MAP_MILL_CELLAR, 6, 7, MAP_BROOKMILL_MILL },
        { MAP_BROOKMILL_MILL, 6, 6, MAP_MILL_CELLAR },
        { MAP_ROOTWAYS, 21, 14, MAP_COPPER_MINE },
        { MAP_COPPER_MINE, 3, 18, MAP_ROOTWAYS },
    };
    for (int i = 0; i < (int)(sizeof links / sizeof links[0]); i++) {
        const int w = warp_at(links[i].map, links[i].x, links[i].y);
        if (w < 0) { CHECK(0, "pilot warp exists"); continue; }
        CHECK(WARPS[w].dest == links[i].dest && WARPS[w].required_flag == FLAG_VOLT_CREST,
              "pilot warp has the paired crest condition");
        map_load(links[i].map);
        CHECK((cell_attr(links[i].x, links[i].y) & A_DOOR) &&
              adjacent_open(links[i].map, links[i].x, links[i].y),
              "portal is a visible door with a plain approach");
        map_load(links[i].dest);
        CHECK(WARPS[w].dx < map_w && WARPS[w].dy < map_h &&
              cell_walkable(WARPS[w].dx, WARPS[w].dy),
              "destination is a walkable non-portal spawn");
    }
    flag_clear(FLAG_VOLT_CREST);
    for (int i = 0; i < (int)(sizeof links / sizeof links[0]); i++) {
        int w = warp_at(links[i].map, links[i].x, links[i].y);
        CHECK(w >= 0 && !warp_is_open(&WARPS[w]), "crest blocks both directions");
    }
    field_enter_map(MAP_WOOD, 17, 6, DIR_UP);
    warp.active = 0;
    player_try_move(DIR_UP);
    CHECK(cur_map == MAP_WOOD && !warp.active, "uncrested step into hollow is blocked in gameplay");
    dialog_clear();
    flag_set(FLAG_VOLT_CREST);
    for (int i = 0; i < (int)(sizeof links / sizeof links[0]); i++) {
        int w = warp_at(links[i].map, links[i].x, links[i].y);
        CHECK(w >= 0 && warp_is_open(&WARPS[w]), "crest opens both directions");
    }
    player_try_move(DIR_UP);
    CHECK(warp.active && warp.dest == MAP_ROOTWOOD_PATH,
          "crested step into hollow starts its map transition");
    warp.active = 0;
}

static void check_maps(void)
{
    const int maps[] = { MAP_ROOTWOOD_PATH, MAP_ROOTWAYS, MAP_MILL_CELLAR };
    for (int i = 0; i < 3; i++) {
        const MapDef *m = &MAPS[maps[i]];
        for (int y = 0; y < m->h; y++)
            CHECK((int)strlen(m->rows[y]) == m->w, "pilot row matches width");
        CHECK(m->obj_count <= 48, "pilot object capacity");
        for (int d = 0; d < m->decor_count; d++)
            CHECK(DECOR_DEFS[m->tileset][m->decor[d].kind].tile_count > 0,
                  "pilot decoration exists in its own tileset");
    }
    CHECK(MAPS[MAP_ROOTWOOD_PATH].w != MAPS[MAP_ROOTWOOD_PATH].h &&
          MAPS[MAP_ROOTWOOD_PATH].h <= 12 && MAPS[MAP_ROOTWOOD_PATH].depth == 0,
          "connector is a short, non-square surface woodland");
    CHECK(MAPS[MAP_ROOTWAYS].depth == 1 && MAPS[MAP_ROOTWAYS].surface_map == MAP_WOOD &&
          (MAPS[MAP_ROOTWAYS].flags & MF_NOFLY), "Rootways has cave anchor and no fly");
    CHECK(MAPS[MAP_MILL_CELLAR].depth == 1 &&
          MAPS[MAP_MILL_CELLAR].surface_map == MAP_BROOKMILL &&
          (MAPS[MAP_MILL_CELLAR].flags & MF_NOFLY), "cellar has mill anchor and no fly");
    CHECK(MAPS[MAP_BROOKMILL_MILL].depth == 0, "ordinary mill interior remains surface depth");
    CHECK(MAPS[MAP_COPPER_MINE].depth == 1 &&
          MAPS[MAP_COPPER_MINE].surface_map == MAP_COPPERLINE,
          "existing Copperline Mine retains entrance and gains an explicit surface anchor");
    CHECK(WOOD_ROWS[7][22] == '~' && WOOD_DECOR[4].x == 22 &&
          WOOD_DECOR[4].y == 7,
          "Bramblewood creek bridge remains on the existing surface route");
}

static void check_reachability(void)
{
    map_load(MAP_ROOTWOOD_PATH);
    flood(3, 7);
    CHECK(reached_beside(17, 3), "short woodland elbow reaches the cave mouth");
    map_load(MAP_ROOTWAYS);
    flood(3, 8);
    CHECK(reached_beside(21, 3) && reached_beside(21, 14),
          "both cave branches stay reachable around the closed shortcut");
    flood(20, 14);
    CHECK(reached_beside(2, 8) && reached_beside(21, 3),
          "reverse approach reaches hollow and mill without opening the gate");
    map_load(MAP_MILL_CELLAR);
    flood(6, 3);
    CHECK(reached_beside(6, 7), "mill cellar has an open passage to its south stair");
}

static void check_shortcut(void)
{
    map_load(MAP_ROOTWAYS);
    CHECK(tobj_count == 7 && tobj[6].kind == OBJ_LADDER &&
          tobj[3].kind == OBJ_BOULDER && tobj[3].arg == 1 &&
          tobj[4].kind == OBJ_PLATE && tobj[5].kind == OBJ_GATE,
          "contained pumice, plate and gate are present");
    CHECK(!tobj[5].state, "shortcut begins closed");
    CHECK(boulder_push(3, DIR_RIGHT), "pumice pushes east onto plate without STRENGTH");
    CHECK(tobj[3].x == 7 && tobj[4].state && tobj[5].state,
          "one push opens the shortcut");
    int bit = tobj[5].bit;
    CHECK(bit != 0xFF && pbit_get(bit), "shortcut records a persistent bit");
    map_load(MAP_ROOTWAYS);
    CHECK(tobj[5].state == 2 && pbit_get(bit), "shortcut remains open after re-entry");
}

int main(void)
{
    fresh_game();
    check_maps();
    check_warps();
    check_reachability();
    check_shortcut();
    printf("rootways failures: %d\n", failures);
    return failures ? 1 : 0;
}
