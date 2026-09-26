/* world/elev/maps.inc -- Map definitions: [MAP_X] = { w, h, TS_..., SC_..., ROWS, ... },. Owner: ELEVATION system (docs/ELEVATION.md). */
    [MAP_EV_TEST] = { 30, NROWS(EV_TEST_ROWS), TS_TOWN, SC_MEADOW, EV_TEST_ROWS, 0, 0, EV_TEST_DECOR,
                      NDEC(EV_TEST_DECOR), "TEST HEIGHTS", ZONE_NONE, MF_OUTDOOR | MF_NIGHTLESS, NO_LINKS,
                      ELEV(EV_TEST_ELEV, EV_TEST_FEATS) },
