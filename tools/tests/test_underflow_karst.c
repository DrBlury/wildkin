/* Focused regional connector checks; compile directly, not via the global suite. */
#include "harness.h"

static const Warp *passage(int from, int x, int y, int to)
{
    for (int i = 0; i < WARP_COUNT; i++)
        if (WARPS[i].map == from && WARPS[i].x == x && WARPS[i].y == y && WARPS[i].dest == to)
            return &WARPS[i];
    return 0;
}

static void check_pair(int from, int x, int y, int to, int rx, int ry, int gate)
{
    const Warp *out = passage(from, x, y, to);
    const Warp *back = passage(to, rx, ry, from);
    CHECK(out && back, "explicit reciprocal portal pair");
    if (!out || !back) return;
    CHECK(out->required_flag == gate && back->required_flag == gate, "gate mirrors on both ends");
    map_load(from);
    CHECK((cell_attr(x, y) & A_DOOR) != 0, "outbound portal renders as a door");
    map_load(to);
    CHECK((cell_attr(rx, ry) & A_DOOR) != 0, "return portal renders as a door");
    CHECK(out->dx < map_w && out->dy < map_h && !(cell_attr(out->dx, out->dy) & (A_SOLID | A_WATER | A_DOOR)),
          "outbound landing is safe and not another portal");
    map_load(from);
    CHECK(back->dx < map_w && back->dy < map_h && !(cell_attr(back->dx, back->dy) & (A_SOLID | A_WATER | A_DOOR)),
          "return landing is safe and not another portal");
}

static void check_sign(int map, int x, int y, int sx, int sy)
{
    map_load(map);
    flood(sx, sy);
    CHECK((cell_attr(x, y) & A_SOLID) && reached_beside(x, y),
          "connector sign is visible, solid and readable from its approach");
}

static void check_rows(int map)
{
    const MapDef *m = &MAPS[map];
    CHECK(m->w <= 64 && m->h <= 64 && m->obj_count <= 48, "new cave within map and object caps");
    for (int y = 0; y < m->h; y++) {
        if ((int)strlen(m->rows[y]) != m->w) { CHECK(0, "row width matches map width"); return; }
        if (m->elev && (int)strlen(m->elev[y]) != m->w) { CHECK(0, "height row matches map width"); return; }
    }
    CHECK(1, "terrain and elevation rows match widths");
}

int main(void)
{
    fresh_game();
    printf("map ids: TIDAL_UNDERFLOW=%d KARST_CHAMBER=%d KARST_FROST=%d MAP_COUNT=%d\n",
           MAP_TIDAL_UNDERFLOW, MAP_KARST_CHAMBER, MAP_KARST_FROST, MAP_COUNT);
    CHECK(MAP_COUNT < 254, "map IDs fit the capacity ceiling");
    check_rows(MAP_TIDAL_UNDERFLOW);
    check_rows(MAP_KARST_CHAMBER);
    check_rows(MAP_KARST_FROST);
    CHECK(MAPS[MAP_REED_TUNNEL].depth == 1 && MAPS[MAP_REED_TUNNEL].surface_map == MAP_HERON_FEN,
          "Reed Tunnel has an explicit fen surface anchor");
    CHECK(MAPS[MAP_TIDAL_UNDERFLOW].depth == 2 && (MAPS[MAP_TIDAL_UNDERFLOW].flags & MF_NOFLY),
          "underflow is deep and non-flyable");
    CHECK(MAPS[MAP_KARST_CHAMBER].depth == 2 && MAPS[MAP_KARST_CHAMBER].surface_map == MAP_FOOTHILLS,
          "karst has an explicit foothills surface anchor");
    check_pair(MAP_REED_TUNNEL, 2, 10, MAP_HERON_FEN, 12, 8, 0);
    check_pair(MAP_REED_TUNNEL, 17, 3, MAP_TIDAL_UNDERFLOW, 3, 10, FLAG_TIDE_CREST);
    check_pair(MAP_REEDWICK, 23, 23, MAP_TIDAL_UNDERFLOW, 27, 5, FLAG_TIDE_CREST);
    check_pair(MAP_PORT_BRINE, 35, 33, MAP_TIDAL_UNDERFLOW, 27, 14, FLAG_TIDE_CREST);
    check_pair(MAP_STORM_CAVE, 18, 3, MAP_KARST_CHAMBER, 3, 14, FLAG_CREST_ANVIL);
    check_pair(MAP_KARST_CHAMBER, 24, 5, MAP_KARST_FROST, 3, 12, FLAG_CREST_ANVIL);
    check_pair(MAP_TIMBER_SAWMILL, 10, 6, MAP_KARST_FROST, 14, 5, FLAG_CREST_ANVIL);
    check_pair(MAP_GLIMMER_1, 34, 14, MAP_KARST_CHAMBER, 24, 12, FLAG_CREST_ANVIL);
    const Warp *rootways = passage(MAP_TIDAL_UNDERFLOW, 10, 3, MAP_ROOTWAYS);
    CHECK(rootways && rootways->required_flag == FLAG_TIDE_CREST && rootways->dx == 20 && rootways->dy == 11,
          "west bank has the approved Tide-gated Rootways endpoint");
    map_load(MAP_TIDAL_UNDERFLOW);
    CHECK((cell_attr(10, 3) & A_DOOR) && !(cell_attr(11, 3) & (A_SOLID | A_WATER | A_DOOR)),
          "Rootways source ladder and adjacent return landing are safe");
    map_load(MAP_ROOTWAYS);
    CHECK(!(cell_attr(20, 11) & (A_SOLID | A_WATER | A_DOOR)),
          "Rootways arrival is plain floor rather than a door or wall");
    map_load(MAP_PORT_BRINE);
    flood(35, 24);
    CHECK(reached_beside(35, 33), "Brine low quay reaches its cave portal from town");
    map_load(MAP_REEDWICK);
    flood(35, 19);
    CHECK(reached_beside(23, 23), "Reedwick road reaches its sluice portal");
    check_sign(MAP_REED_TUNNEL, 1, 7, 3, 10);
    check_sign(MAP_TIDAL_UNDERFLOW, 5, 10, 4, 10);
    check_sign(MAP_TIDAL_UNDERFLOW, 9, 4, 10, 4);
    check_sign(MAP_TIDAL_UNDERFLOW, 21, 10, 20, 10);
    check_sign(MAP_STORM_CAVE, 15, 3, 14, 3);
    check_sign(MAP_KARST_CHAMBER, 7, 14, 6, 14);
    check_sign(MAP_KARST_FROST, 6, 12, 5, 12);
    const Warp *tide = passage(MAP_REED_TUNNEL, 17, 3, MAP_TIDAL_UNDERFLOW);
    const Warp *anvil = passage(MAP_STORM_CAVE, 18, 3, MAP_KARST_CHAMBER);
    CHECK(tide && !warp_is_open(tide) && rootways && !warp_is_open(rootways) && anvil && !warp_is_open(anvil), "both cave branches closed before crests");
    flag_set(FLAG_TIDE_CREST);
    CHECK(tide && warp_is_open(tide) && rootways && warp_is_open(rootways) && anvil && !warp_is_open(anvil), "only tidal branch opens with Tide");
    flag_set(FLAG_CREST_ANVIL);
    CHECK(anvil && warp_is_open(anvil), "karst branch opens with Anvil");
    map_load(MAP_REED_TUNNEL);
    flood(3, 10);
    CHECK(reached(8, 7) && !reached(16, 3) && reached_beside(2, 10), "sluice switch reachable; closed barrier protects exit and fen escape");
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].kind == OBJ_SWITCH && tobj[i].arg == 6) { switch_press(&tobj[i]); break; }
    flood(3, 10);
    CHECK(reached_beside(17, 3) && reached_beside(2, 10), "switch opens sluice without cutting off retreat");
    map_load(MAP_TIDAL_UNDERFLOW);
    flood(4, 10);
    CHECK(!reached_beside(27, 5) && !reached_beside(27, 14), "dry traversal cannot bypass flooded underflow");
    flood_ex(4, 10, FLOOD_SURF);
    CHECK(reached_beside(27, 5) && reached_beside(27, 14), "SURF reaches both east-bank exits");
    flood_ex(4, 13, FLOOD_SOLVED);
    CHECK(reached_lv(8, 13, 1) && reached_lv(11, 13, 0),
          "side span rises over water and descends back to the gallery");
    CHECK(MAPS[MAP_TIDAL_UNDERFLOW].feat_count && MAPS[MAP_TIDAL_UNDERFLOW].feats[0].kind == EF_BRIDGE_H &&
          (cell_attr_raw(8, 13) & A_WATER), "elevated side bridge spans actual water");
    map_load(MAP_KARST_CHAMBER);
    flood_ex(4, 14, FLOOD_SOLVED);
    CHECK(reached_beside(24, 5) && reached_beside(24, 12) && reached_beside(3, 14),
          "karst's two branches and Stormstep retreat are traversable");
    map_load(MAP_KARST_FROST);
    CHECK((cell_attr(12, 8) & A_ICE) && (cell_attr(14, 7) & (A_SOLID | A_WATER | A_DOOR)) == 0,
          "the frost slide is real ice with a turn north toward the cellar");
    int stone = boulder_at(15, 10);
    CHECK(stone >= 0 && tobj[stone].arg == 0, "movable stopper requires Strength");
    if (stone >= 0) {
        CHECK(!boulder_push(stone, DIR_UP), "stopper will not move without Strength");
        tv.strength_on = 1;
        CHECK(boulder_push(stone, DIR_UP), "Strength moves stopper to the feeder lane");
        tobj[stone].ox = tobj[stone].oy = 0;
        CHECK(boulder_push(stone, DIR_UP) && tobj[stone].x == 15 && tobj[stone].y == 8,
              "second push places stopper beside the north turn");
        tv.strength_on = 0;
        CHECK((cell_attr(15, 8) & A_SOLID) && !(cell_attr(14, 8) & A_SOLID),
              "eastbound slide stops on the cell beneath the north turn");
    }
    flood(4, 12);
    CHECK(reached_beside(3, 12), "lower return walk remains open after the stone moves");
    map_load(MAP_SEA_ROUTE);
    flood(20, 4);
    CHECK(!reached(20, 46), "sea remains impassable on foot");
    flood_ex(20, 4, FLOOD_SURF);
    CHECK(reached(20, 46), "sea straits remain navigable by SURF");
    check_rows(MAP_SEA_ROUTE);
    int north_seam_water = 1;
    for (int y = 0; y < 4; y++)
        for (int x = 0; x < 40; x++) north_seam_water &= MAPS[MAP_SEA_ROUTE].rows[y][x] == '~';
    CHECK(north_seam_water, "sea north edge remains water off the existing pier");
    printf("underflow/karst: %d failure(s)\n", failures);
    return failures ? 1 : 0;
}
