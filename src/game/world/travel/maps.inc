/* world/travel/maps.inc -- Map definitions: [MAP_X] = { w, h, TS_..., SC_..., ROWS, ... },. Owner: TRAVERSAL system.
 * The TEST maps (see data.h). */
    [MAP_TT_SHORE] = { 20, NROWS(TT_SHORE_ROWS), TS_COAST, SC_COAST, TT_SHORE_ROWS, 0, 0, 0, 0, "TEST SHORE", ZONE_NONE,
                       MF_OUTDOOR, NO_LINKS, TT_SHORE_OBJS, NOBJ(TT_SHORE_OBJS), ZONE_TT_SEA },
    [MAP_TT_ICE] = { 20, NROWS(TT_ICE_ROWS), TS_SNOW, SC_SNOW, TT_ICE_ROWS, 0, 0, 0, 0, "TEST ICE", ZONE_NONE,
                     MF_OUTDOOR, NO_LINKS, TT_ICE_OBJS, NOBJ(TT_ICE_OBJS) },
    [MAP_TT_HALL] = { 20, NROWS(TT_HALL_ROWS), TS_COAST, SC_COAST, TT_HALL_ROWS, 0, 0, 0, 0, "TEST HALL", ZONE_NONE,
                      MF_NIGHTLESS, NO_LINKS, TT_HALL_OBJS, NOBJ(TT_HALL_OBJS) },
    [MAP_TT_DARK] = { 12, NROWS(TT_DARK_ROWS), TS_COAST, SC_CAVE, TT_DARK_ROWS, 0, 0, 0, 0, "TEST DARK", ZONE_NONE,
                      MF_DARK | MF_NIGHTLESS, NO_LINKS },
