/* Resources are defined here, after flag IDs, before map definitions. */
static const char *const SUNWELL_GARDEN_ROWS[] = { "hhhhhhhh", "hhhhhhhh" };
static const MapPatch SUNWELL_GARDEN_PATCHES[] = {
    { .flag = FLAG_SUNWELL_IRRIGATED, .x = 11, .y = 16, .w = 8, .h = 2,
      .rows = SUNWELL_GARDEN_ROWS },
};
static const DecorPlace SAFFRON_DUNES_DECOR[] = {
    DP(DESERT_WAYPOST, 5, 12), DP(DESERT_WAYPOST, 21, 6),
    DP(DESERT_CACTUS, 7, 10), DP(DESERT_CACTUS_BLOOM, 30, 10),
    DP(DESERT_CARAVAN_CANOPY, 14, 18), DP(DESERT_JAR, 18, 18),
    DP(DESERT_DUNE_TUFT, 20, 8), DP(DESERT_DUNE_TUFT, 27, 10),
};
static const MapObj SAFFRON_DUNES_OBJS[] = {
    OBJ(LADDER, 2, 14, 0), OBJ(LADDER, 37, 14, 0),
    OBJ(CHEST, 24, 5, ITEM_GRAND_TONIC),
};
static const DecorPlace SUNWELL_DECOR[] = {
    DP(DESERT_WAYPOST, 4, 12), DP(DESERT_WAYPOST, 14, 4),
    DP(DESERT_ADOBE_HUT, 6, 5), DP(DESERT_ADOBE_HUT, 22, 5),
    DP(DESERT_ADOBE_HUT, 5, 16), DP(DESERT_ADOBE_HUT, 22, 17),
    DP(DESERT_WELL, 14, 11), DP(DESERT_JAR, 10, 9), DP(DESERT_JAR, 20, 9),
    DP(DESERT_JAR, 10, 16), DP(DESERT_JAR, 20, 16),
    DP(DESERT_DUNE_TUFT, 9, 21), DP(DESERT_CACTUS_BLOOM, 26, 14),
};
static const MapObj SUNWELL_OBJS[] = { OBJ(LADDER, 2, 12, 0), OBJ(LADDER, 15, 5, 0) };
static const DecorPlace SUNWELL_CISTERN_DECOR[] = {
    DP(HEAL_MACHINE, 10, 2), DP(BARREL_IN, 2, 3), DP(TABLE_ROUND, 3, 5),
};
static const WildSlot WILD_SAFFRON_DUNES[] = {
    { SP_FORTADILLO, 34, 40, 43 }, { SP_SCORCHION, 30, 40, 43 },
    { SP_LODEHORN, 26, 41, 44 }, { SP_METEORB, 10, 42, 44, WHEN_NIGHT },
};
