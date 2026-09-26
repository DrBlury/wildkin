/* world/farm/maps.inc -- Map definitions. PLACEHOLDER maps (see data.h): replace freely,
 * but keep the ids and the edge contracts in docs/EXPANSION.md 9. */
    [MAP_WILLOW_ACRE] = { 40, NROWS(WILLOW_ACRE_ROWS), TS_FARM, SC_FARM, WILLOW_ACRE_ROWS, 0, 0, 0, 0, "WILLOW ACRE", ZONE_NONE, MF_OUTDOOR,
        { MAP_TOWN, MAP_NONE, MAP_NONE, MAP_NONE }, { 0, 0, 0, 0 } },
    [MAP_FARMHOUSE] = { 11, NROWS(FARMHOUSE_ROWS), TS_INTERIOR, SC_MEADOW, FARMHOUSE_ROWS, 0, 0, 0, 0, "FARMHOUSE", ZONE_NONE, MF_NIGHTLESS, NO_LINKS },
