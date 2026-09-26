/*
 * world/east/data.h -- map rows, stamps, decor, objects and wild slots for
 * REGION EAST (owner: W-EAST, docs/EXPANSION.md 9): COPPERLINE ROAD, LUMEN
 * CITY and its interiors, the VOLT HALL, the CLOCKWORK SPIRE, ELDERWOOD HEART
 * and the LAND OFFICE in Maple Village.
 *
 * Exits (edge contracts):
 *   COPPERLINE ROAD  west  y 17-18 <-> BRAMBLEWOOD east
 *                    south x 20-21 <-> ASHEN FIELDS north
 *                    east  y 20-21 <-> LUMEN CITY west
 *   LUMEN CITY       north x 24-25 <-> MOONVEIL PATH south
 *                    east  y 20-21 <-> CINDER ROAD west
 *   ELDERWOOD HEART  north x 30-31 <-> BRAMBLEWOOD south (behind two STRENGTH
 *                    boulders on Bramblewood, WOOD_OBJS below)
 * Doors: see warps.inc. The CLOCKWORK SPIRE is entered through the clock
 * tower in Lumen City (CY CLOCK_TOWER stamp).
 *
 * Legends: route maps use the wild tileset (. grass  , tall grass  = path
 * ~ water  T/t trees  P/p pines  C/c cliff  L [ ] ledges  d dirt  f forest
 * floor  R reeds); Lumen uses the city tileset (tools/tilesets/ts_city.py:
 * . pavement  = street  ~ canal  c cobbles  p plaza  g lawn  , park grass
 * r/y flowers  T/t trees  # w city wall); interiors use W w n k walls,
 * . : floors, < = > counter, D exit mat.
 */

/* ================================================================ */
/*  COPPERLINE ROAD                                                 */
/* ================================================================ */

static const char *const COPPERLINE_ROWS[] = {
    "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", /*  0 */
    "pppppppppppppppppppppppppppppppppppppppppppp", /*  1 */
    "PPPPPPPPPPPP..yy....................PPPPPPPP", /*  2 */
    "pppppppppppp........................,,,,,,pp", /*  3 */
    "PPPPPPPPPPPP........................,,,,,,PP", /*  4 */
    "pppppppppppp..CCCCCCCCCCCCCCCCCCCCC.,,,,,,pp", /*  5 */
    "PPPPPPPPPPPP..CCCCCCCCCCCCCCCCCCCCC.,,,,,,PP", /*  6 */
    "pppppppppppp..ccccccccccccccccccccc.,,,,,,pp", /*  7 */
    "PP............ccccccccccccccccccccc.,,,,,,PP", /*  8 */
    "pp,,,,,,,,,,,,..dddddddddddddddddd..,,,,,,pp", /*  9 */
    "PP,,,,,,,,,,,,..dddddddddddddddddd..,,,,,,PP", /* 10 */
    "pp,,,,,,,,,,,,..dddddddddddddddddd..,,,,,,pp", /* 11 */
    "PP,,,,,,,,,,,,..dddddddddddddddddd..,,,,,,PP", /* 12 */
    "pp,,,,,,,,,,,,..dddddddddddddddddd..,,,,,,pp", /* 13 */
    "PP,,,,,,,,,,,,..dddddddddddddddddd..,,,,,,PP", /* 14 */
    "pp..................==...............rrr..pp", /* 15 */
    "PP..................==....................PP", /* 16 */
    "==================================........pp", /* 17 */
    "==================================........PP", /* 18 */
    "pp.yyy..............==..........==........pp", /* 19 */
    "PP.,,,,,,,,,,,,,TTT.==..........============", /* 20 */
    "pp.,,,,,,,,,,,,,ttt.==..........============", /* 21 */
    "PP.,,,,,,,,,,,,,TTT.==,,~~~~,,,,......rr..PP", /* 22 */
    "pp.,,,,,,,,,,,,,ttt.==,~~~~~~,,,..........pp", /* 23 */
    "PP.,,,,,,,,,,,,,TTT.==,,~~~~,,,,TT.,,,,,,.PP", /* 24 */
    "pp.,,,,,,,,,,,,,ttt.==,,,,,,,,,,tt.,,,,,,.pp", /* 25 */
    "PP.[LLLLLLLLLLL]....==,,,,,,,,,,TT.,,,,,,.PP", /* 26 */
    "pp.,,,,,,,,,,,,,....==,,,,,,,,,,tt.,,,,,,.pp", /* 27 */
    "PP.,,,,,,,,,,,,,TTT.==,,,,,,,,,,TT.,,,,,,.PP", /* 28 */
    "pp.,,,,,,,,,,,,,ttt.==,,,,,,,,,,tt.,,,,,,.pp", /* 29 */
    "PP.,,,,,,,,,,,,,TTT.==,,,,,,,,,,TT.,,,,,,.PP", /* 30 */
    "pp.,,,,,,,,,,,,,ttt.==,,,,,,,,,,tt.,,,,,,.pp", /* 31 */
    "PPPPPPPPPPPPP.......==..............yy....PP", /* 32 */
    "ppppppppppppp.......==....................pp", /* 33 */
    "PPPPPPPPPPPPPPPPPPPP==PPPPPPPPPPPPPPPPPPPPPP", /* 34 */
    "pppppppppppppppppppp==pppppppppppppppppppppp", /* 35 */
};

static const DecorPlace COPPERLINE_DECOR[] = {
    DP(SIGNPOST, 3, 16), DP(SIGNPOST, 23, 33), DP(SIGNPOST, 40, 19),
    /* the old mine: adit, headframe, rails and the ore yard */
    DP(MINE_MOUTH, 23, 7), DP(HEADFRAME, 29, 9),
    DP(RAILS_V, 24, 9), DP(RAILS_V, 24, 10), DP(RAILS_V, 24, 11), DP(RAILS_H, 24, 12),
    DP(RAILS_H, 25, 12), DP(RAILS_H, 26, 12), DP(RAILS_H, 28, 12), DP(RAILS_H, 29, 12),
    DP(RAILS_H, 30, 12), DP(RAILS_H, 31, 12), DP(ORE_CART, 27, 12),
    DP(ORE_PILE, 17, 10), DP(ORE_PILE, 18, 9), DP(ORE_PILE, 32, 14), DP(ORE_PILE, 16, 13),
    DP(COPPER_ROCK, 33, 9), DP(COPPER_ROCK, 13, 3), DP(COPPER_ROCK, 30, 3), DP(COPPER_ROCK, 21, 3),
    DP(CRATE, 19, 13), DP(BARREL, 18, 13), DP(CRATE_STACK, 32, 10), DP(LANTERN_POST, 22, 9),
    DP(WOODPILE, 26, 14),
    /* the prospectors' camp */
    DP(TENT, 38, 16), DP(CAMPFIRE, 37, 18), DP(LOG, 39, 18),
    /* roadside */
    DP(ROCK, 5, 19), DP(ROCK, 30, 22), DP(BOULDER, 34, 22), DP(STUMP, 12, 16),
    DP(BUSH, 13, 19), DP(BUSH, 41, 16), DP(BUSH, 26, 32), DP(LOG, 14, 32),
    DP(SMALL_FLOWERS, 7, 16), DP(SMALL_FLOWERS, 29, 19), DP(PEBBLES, 25, 16), DP(PEBBLES, 18, 20),
    DP(PEBBLES, 36, 33), DP(FALLEN_LEAVES, 17, 27), DP(BERRY_BUSH, 3, 32), DP(MUSHROOMS, 34, 33),
};

static const MapObj COPPERLINE_OBJS[] = {
    OBJ(BERRY, 22, 20, 0),   /* wild berry patches (farm.c: east 0-9) */
    OBJ(BERRY, 40, 23, 1),
};


static const WildSlot WILD_COPPERLINE[] = {
    { SP_STATICKO, 22, 13, 17, WHEN_ANY }, { SP_MAGNITICK, 20, 13, 17, WHEN_ANY },
    { SP_RIVETILLO, 12, 14, 18, WHEN_ANY }, { SP_RACCOIN, 12, 13, 16, WHEN_NIGHT },
    { SP_FLYSQUIRL, 14, 13, 17, WHEN_DAY }, { SP_QUILLDRUM, 8, 15, 18, WHEN_ANY },
    { SP_MANDRAGOR, 7, 15, 18, WHEN_ANY }, { SP_TRUFFLOAR, 5, 16, 19, WHEN_DAY },
    { SP_BEACONFLY, 8, 16, 19, WHEN_NIGHT }, { SP_FULGECKO, 2, 18, 20, WHEN_ANY },
};

/* ================================================================ */
/*  LUMEN CITY                                                      */
/* ================================================================ */

static const char *const LUMEN_ROWS[] = {
    "########################==######################", /*  0 */
    "#wwwwwwwwwwwwwwwwwwwwwww==wwwwwwwwwwwwwwwwwwwww#", /*  1 */
    "#ggggggggggggggg........==........ggggggggggggg#", /*  2 */
    "#ggggggggggggggg........==........ggggggggggggg#", /*  3 */
    "#gg..........ggg........==...................gg#", /*  4 */
    "#gg..........ggg........==...................gg#", /*  5 */
    "#gg..........ggg........==...................gg#", /*  6 */
    "#gg..........ggg........==...................gg#", /*  7 */
    "#gg..........ggg.............................gg#", /*  8 */
    "#gg..........ggg..................cccccccccccgg#", /*  9 */
    "#ccccccccccc.ggg..................cccccccccccgg#", /* 10 */
    "#ccccccccccc.rrrppppppppppppppppppcccccccccccgg#", /* 11 */
    "#gg..........yyyppppppppppppppppppyy.........rr#", /* 12 */
    "#gg.......ggggggpppppppppppppppppp...........gg#", /* 13 */
    "#gg.......ggggggpppppppppppppppppp...........gg#", /* 14 */
    "#gg.......ggggggpppppppppppppppppp...........gg#", /* 15 */
    "#gg.......ggggggpppppppppppppppppp...........gg#", /* 16 */
    "#gg.............pppppppppppppppppp...........gg#", /* 17 */
    "#gg.............pppppppppppppppppp...........gg#", /* 18 */
    "#gg.............pppppppppppppppppp...........gg#", /* 19 */
    "================================================", /* 20 */
    "================================================", /* 21 */
    "#.......................==.....................#", /* 22 */
    "#.......................==.....................#", /* 23 */
    "#.......................==.....................#", /* 24 */
    "#.......................==.....................#", /* 25 */
    "#.......................==.....................#", /* 26 */
    "#.......................==.....................#", /* 27 */
    "#.......................==.....................#", /* 28 */
    "#.......................==.....................#", /* 29 */
    "#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#", /* 30 */
    "#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#", /* 31 */
    "#ggggggggggggggggggggggg==gggggyyyygggrrrrgggTT#", /* 32 */
    "#gggggggggggggggrrrrgggg==gggggggggggggggggggtt#", /* 33 */
    "#ggccccccccccgggyyyygggg==ggTT,,,,,,,,,,,,,,,TT#", /* 34 */
    "#ggccccccccccggggggggggg==ggtt,,,,,,,,,,,,,,,tt#", /* 35 */
    "#ggccccccccccgggggggggggccgggg,,,,,,,,,,,,,,,TT#", /* 36 */
    "#ggccccccccccgggggggggggccgggg,,,,,,,,,,,,,,,tt#", /* 37 */
    "#ggccccccccccggTTTTggTTTccggTT,,,,,,,,,,,,,,,TT#", /* 38 */
    "#ggggggggggggggttttggtttccggtt,,,,,,,,,,,,,,,tt#", /* 39 */
    "#grrrrggggyyyyggggggggggccggTT,,,,,,,,,,,,,,,TT#", /* 40 */
    "#gggggggggggggggggggggggccggttgggggggggggggggtt#", /* 41 */
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT", /* 42 */
    "tttttttttttttttttttttttttttttttttttttttttttttttt", /* 43 */
};

static const Stamp LUMEN_STAMPS[] = {
    STAMP(CY, VOLT_HALL, 3, 4),     /* door 7,8   */
    STAMP(CY, HEARTH, 4, 13),       /* door 7,16  */
    STAMP(CY, BIKE_SHOP, 17, 4),    /* door 20,7  */
    STAMP(CY, INN, 27, 4),          /* door 30,7  */
    STAMP(CY, WORKS, 37, 4),        /* door 40,7  */
    STAMP(CY, MARKET, 37, 13),      /* door 41,16 */
    STAMP(CY, HOUSE_A, 3, 24),      /* door 5,27  */
    STAMP(CY, HOUSE_C, 10, 24),     /* door 11,27 (locked) */
    STAMP(CY, CLOCK_TOWER, 17, 22), /* door 18,27: the CLOCKWORK SPIRE */
    STAMP(CY, ROW_HOUSES, 29, 24),  /* doors 30,27 and 34,27 (locked) */
    STAMP(CY, HOUSE_B, 39, 24),     /* door 41,27 */
};

static const DecorPlace LUMEN_DECOR[] = {
    DP(SIGNPOST, 23, 2), DP(SIGNPOST, 2, 19), DP(SIGNPOST, 45, 19), DP(SIGNPOST, 23, 18),
    DP(SIGNPOST, 16, 28),
    /* the market square: the Beacon, coils, fountains and stalls */
    DP(BEACON, 24, 13), DP(TESLA_COIL, 16, 11), DP(TESLA_COIL, 33, 11),
    DP(FOUNTAIN, 19, 13), DP(FOUNTAIN, 29, 13),
    DP(MARKET_STALL, 17, 17), DP(MARKET_STALL, 30, 17), DP(SACKS, 20, 18), DP(BARREL, 29, 18),
    DP(BENCH, 21, 16), DP(BENCH, 27, 16),
    DP(CITY_LAMP, 22, 11), DP(CITY_LAMP, 27, 11), DP(CITY_LAMP, 16, 18), DP(CITY_LAMP, 33, 18),
    /* the boulevard and the avenues */
    DP(CITY_LAMP, 4, 18), DP(CITY_LAMP, 12, 18), DP(CITY_LAMP, 38, 18), DP(CITY_LAMP, 44, 18),
    DP(CITY_LAMP, 4, 22), DP(CITY_LAMP, 14, 22), DP(CITY_LAMP, 22, 22), DP(CITY_LAMP, 27, 22),
    DP(CITY_LAMP, 36, 22), DP(CITY_LAMP, 45, 22), DP(CITY_LAMP, 23, 4), DP(CITY_LAMP, 26, 4),
    DP(CITY_LAMP, 23, 33), DP(CITY_LAMP, 26, 33),
    /* the Volt Hall's forecourt */
    DP(TESLA_COIL, 2, 6), DP(TESLA_COIL, 12, 6), DP(HEDGE, 1, 12), DP(HEDGE, 2, 12),
    DP(BIG_TREE, 13, 2), DP(BUSH, 1, 3), DP(BUSH, 14, 9),
    /* the hearth hall and its garden */
    DP(BENCH, 11, 14), DP(BUSH, 10, 16), DP(BUSH, 15, 13), DP(FLOWER_POT, 3, 16), DP(FLOWER_POT, 10, 13),
    /* shop fronts */
    DP(PARKED_BIKE, 16, 6), DP(PARKED_BIKE, 22, 7), DP(PARKED_BIKE, 23, 8),
    DP(CAFE_TABLE, 26, 6), DP(CAFE_TABLE, 33, 6),
    DP(CRATE_STACK, 36, 5), DP(BARREL, 36, 7), DP(PARKED_BIKE, 45, 7), DP(NOTICE_BOARD, 34, 9),
    DP(CRATE, 36, 15), DP(SACKS, 36, 16), DP(BARREL, 45, 16), DP(BIG_TREE, 45, 2),
    DP(PLANTER, 34, 12),
    /* south of the boulevard */
    DP(PLANTER, 1, 28), DP(FLOWER_POT, 8, 27), DP(FLOWER_POT, 14, 27), DP(BENCH, 21, 28),
    DP(PLANTER, 27, 28), DP(FLOWER_POT, 38, 27), DP(FLOWER_POT, 44, 27), DP(BENCH, 44, 23),
    /* bridges over the canal */
    DP(BRIDGE_V, 24, 30), DP(BRIDGE_V, 25, 30), DP(BRIDGE_V, 24, 31), DP(BRIDGE_V, 25, 31),
    DP(BRIDGE_V, 6, 30), DP(BRIDGE_V, 7, 30), DP(BRIDGE_V, 6, 31), DP(BRIDGE_V, 7, 31),
    DP(BRIDGE_V, 40, 30), DP(BRIDGE_V, 41, 30), DP(BRIDGE_V, 40, 31), DP(BRIDGE_V, 41, 31),
    DP(RAILING, 2, 29), DP(RAILING, 3, 29), DP(RAILING, 17, 29), DP(RAILING, 18, 29),
    DP(RAILING, 30, 29), DP(RAILING, 31, 29), DP(RAILING, 44, 29), DP(RAILING, 45, 29),
    DP(LILY_PADS, 12, 31), DP(LILY_PADS, 33, 30),
    /* the canal gardens and the cafe */
    DP(CAFE_TABLE, 4, 34), DP(CAFE_TABLE, 7, 34), DP(CAFE_TABLE, 10, 34), DP(CAFE_TABLE, 5, 37),
    DP(CAFE_TABLE, 9, 37), DP(FOUNTAIN, 1, 35), DP(BENCH, 3, 39), DP(BENCH, 8, 39),
    DP(HEDGE, 13, 33), DP(HEDGE, 13, 34), DP(BUSH, 13, 36), DP(TESLA_COIL, 12, 37),
    /* the flower gardens */
    DP(BENCH, 17, 36), DP(BIG_TREE, 21, 32), DP(SMALL_FLOWERS, 16, 37), DP(BUSH, 15, 41),
    DP(BENCH, 25, 38), DP(PARKED_BIKE, 26, 36),
    /* LUMEN PARK */
    DP(BENCH, 31, 33), DP(BENCH, 40, 33), DP(BIG_TREE, 34, 32), DP(BUSH, 27, 34),
};

static const WildSlot WILD_LUMEN[] = {
    { SP_STATICKO, 28, 14, 18, WHEN_ANY }, { SP_KETTLEKIN, 22, 14, 18, WHEN_DAY },
    { SP_PARASOLE, 18, 15, 18, WHEN_ANY }, { SP_RACCOIN, 14, 15, 18, WHEN_NIGHT },
    { SP_BANDIRACC, 6, 19, 21, WHEN_NIGHT }, { SP_BLINKET, 12, 14, 17, WHEN_NIGHT },
    { SP_HUMBEE, 12, 14, 17, WHEN_DAY }, { SP_GARGOLITH, 2, 22, 24, WHEN_NIGHT },
};


/* ================================================================ */
/*  ELDERWOOD HEART                                                 */
/* ================================================================ */

static const char *const ELDERWOOD_ROWS[] = {
    "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPP==PPPPPPPP", /*  0 */
    "pppppppppppppppppppppppppppppp==pppppppp", /*  1 */
    "PPPPPPPPPPPPPPffffffTTTTTTTTff==ffPPPPPP", /*  2 */
    "ppppppppppppppffffffttttttttff==ffpppppp", /*  3 */
    "PPffffffffffffffffffTTTTTTTTff==ffffffPP", /*  4 */
    "ppf,,,,,,,,,,fffffffttttttttff==f,,,,,pp", /*  5 */
    "PPf,,,,,,,,,,fffffffffffffffff==f,,,,,PP", /*  6 */
    "ppf,,,,,,,,,,fffffffffffffffff==f,,,,,pp", /*  7 */
    "PPf,,,,,,,,,,fffffffffffffffff==f,,,,,PP", /*  8 */
    "ppf,,,,,,,,,,ffff===============f,,,,,pp", /*  9 */
    "PPf,,,,,,,,,,ffff===============f,,,,,PP", /* 10 */
    "ppf,,,,,,,,,,ffff==ffffffffffffff,,,,,pp", /* 11 */
    "PPf,,,,,,,,,,ffff==fffTTTTTTfffff,,,,,PP", /* 12 */
    "ppf,,,,,,,,,,ffff==fffttttttfffff,,,,,pp", /* 13 */
    "PPf,,,,,,,,,,ffff==fffTTTTTTfffff,,,,,PP", /* 14 */
    "ppf,,,,,,,,,,ffff==fffttttttffffffffffpp", /* 15 */
    "PPfffffffffffffff==fffffffffffPPPPPPPPPP", /* 16 */
    "ppfffffffffffffff==fffffffffffpppppppppp", /* 17 */
    "PPPPPPPPPPfffffff==fffffffffffffffffffPP", /* 18 */
    "ppppppppppff..............ffffffffffffpp", /* 19 */
    "PPffffffffff...........rr.f,,,,,,,,,,,PP", /* 20 */
    "ppfRRRRRRRff..............f,,,,,,,,,,,pp", /* 21 */
    "PPfR~~~~~Rffy.............f,,,,,,,,,,,PP", /* 22 */
    "ppfR~~~~~Rff..............f,,,,,,,,,,,pp", /* 23 */
    "PPfR~~~~~Rff..............f,,,,,,,,,,,PP", /* 24 */
    "ppfR~~~~~Rff..............f,,,,,,,,,,,pp", /* 25 */
    "PPfR~~~~~Rff..............f,,,,,,,,,,,PP", /* 26 */
    "ppfR~~~~~Rff.............rf,,,,,,,,,,,pp", /* 27 */
    "PPfRRRRRRRff.yy...........f,,,,,,,,,,,PP", /* 28 */
    "ppffffffffff..............ffffffffffffpp", /* 29 */
    "PPPPPPPPPPPPPPffffffffffffPPPPPPPPPPPPPP", /* 30 */
    "ppppppppppppppffffffffffffpppppppppppppp", /* 31 */
    "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", /* 32 */
    "pppppppppppppppppppppppppppppppppppppppp", /* 33 */
};

static const DecorPlace ELDERWOOD_DECOR[] = {
    DP(SIGNPOST, 29, 2),
    /* the glade of the Elder */
    DP(ELDER_TREE, 17, 21), DP(STAG_ALTAR, 14, 25),
    DP(GLOWCAPS, 13, 20), DP(GLOWCAPS, 24, 22), DP(GLOWCAPS, 12, 27), DP(GLOWCAPS, 21, 29),
    DP(GLOWCAPS, 16, 24), DP(FERN, 22, 21), DP(FERN, 15, 22), DP(FERN, 23, 26), DP(FERN, 12, 24),
    DP(SMALL_FLOWERS, 20, 25), DP(SMALL_FLOWERS, 16, 28), DP(STANDING_STONE, 12, 19),
    DP(STANDING_STONE, 25, 19), DP(STANDING_STONE, 25, 28),
    /* the grove keeper's camp */
    DP(TENT, 24, 16), DP(CAMPFIRE, 23, 18), DP(LOG, 26, 18), DP(WOODPILE, 27, 16),
    /* the old forest */
    DP(GLOWCAPS, 15, 6), DP(GLOWCAPS, 28, 7), DP(GLOWCAPS, 8, 17), DP(GLOWCAPS, 36, 19),
    DP(FERN, 14, 4), DP(FERN, 16, 7), DP(FERN, 19, 7), DP(FERN, 29, 12), DP(FERN, 20, 16),
    DP(FERN, 11, 17), DP(FERN, 27, 19), DP(FERN, 10, 29), DP(FERN, 34, 15), DP(FERN, 3, 17),
    DP(FERN, 37, 29), DP(FERN, 15, 30),
    DP(MUSHROOMS, 14, 12), DP(MUSHROOMS, 28, 18), DP(MUSHROOMS, 11, 20), DP(MUSHROOMS, 32, 29),
    DP(LOG, 14, 16), DP(LOG, 3, 29), DP(STUMP, 16, 3), DP(STUMP, 33, 4), DP(STUMP, 10, 21),
    DP(BERRY_BUSH, 29, 15), DP(BERRY_BUSH, 2, 20), DP(FALLEN_LEAVES, 21, 11),
    DP(FALLEN_LEAVES, 25, 10), DP(FALLEN_LEAVES, 13, 13), DP(BOULDER, 34, 2),
    DP(CRYSTAL_CLUSTER, 2, 16), DP(LILY_PADS, 5, 24), DP(LILY_PADS, 7, 26),
};

static const MapObj ELDERWOOD_OBJS[] = {
    OBJ(LEGEND, 18, 25, SP_SYLVARCH),   /* the great stag, before the Elder */
    OBJ(BERRY, 24, 28, 2),
    OBJ(BERRY, 35, 19, 3),
};

static const WildSlot WILD_ELDERWOOD[] = {
    { SP_TRUFFLOAR, 18, 29, 33, WHEN_ANY }, { SP_GALESQUIRL, 16, 30, 34, WHEN_DAY },
    { SP_COMBQUEEN, 10, 31, 34, WHEN_DAY }, { SP_MYCOLOSSUS, 12, 31, 35, WHEN_ANY },
    { SP_DOZLOTH, 14, 29, 32, WHEN_ANY }, { SP_SHROOMLET, 14, 28, 31, WHEN_NIGHT },
    { SP_BEACONFLY, 12, 30, 33, WHEN_NIGHT }, { SP_WEBBIT, 10, 28, 31, WHEN_NIGHT },
};

/* Bramblewood's south path (x 30-31) to Elderwood Heart is blocked by two
 * STRENGTH boulders (the core owns Bramblewood; its MapDef points here).
 * Push the left one down, then the right one out to the east. */
static const MapObj WOOD_OBJS[] = {
    OBJ(BOULDER, 30, 33, 0),
    OBJ(BOULDER, 31, 33, 0),
};

/* ================================================================ */
/*  Interiors                                                       */
/* ================================================================ */

/* LAND OFFICE (Maple Village): REEVE sells the FARM DEED (farm.c). */
static const char *const LAND_OFFICE_ROWS[] = {
    "WWnWWkWWnWW",
    "wwwwwwwwwww",
    ":::::::::::",
    "<===>::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::D:::::",
};
static const DecorPlace LAND_OFFICE_DECOR[] = {
    DP(FILE_CABINET, 0, 1), DP(FILE_CABINET, 1, 1), DP(MAP_POSTER, 3, 0), DP(CALENDAR, 6, 0),
    DP(BOOKSHELF, 7, 1), DP(GRANDFATHER_CLOCK, 10, 1), DP(DESK, 7, 5), DP(CHAIR_UP, 7, 6),
    DP(PLANT, 10, 5), DP(CHAIR, 1, 5), DP(CHAIR, 3, 5), DP(SMALL_PLANT, 0, 7), DP(SMALL_RUG, 5, 7),
};

/* LUMEN HEARTH HALL */
static const char *const LUMEN_HEARTH_ROWS[] = {
    "WWnWWkWWnWW",
    "wwwwwwwwwww",
    ":::::::::::",
    ":::<===>:::",
    ":::::::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::D:::::",
};
static const Stamp LUMEN_HEARTH_STAMPS[] = { STAMP(I, RUG, 4, 6) };
static const DecorPlace LUMEN_HEARTH_DECOR[] = {
    DP(PLANT, 0, 1), DP(LANTERN_RACK, 3, 1), DP(HEAL_MACHINE, 7, 1), DP(FLOOR_LAMP, 9, 1), DP(PC, 10, 1),
    DP(PENNANT, 1, 0), DP(CALENDAR, 9, 0),
    DP(TABLE_ROUND, 1, 5), DP(CHAIR, 1, 4), DP(CHAIR, 2, 4), DP(TEA_SET, 0, 6),
    DP(RESONANCE_COIL, 10, 4), DP(KIN_BASKET, 8, 6), DP(KIN_BASKET, 10, 6), DP(SMALL_PLANT, 10, 7),
};

/* LUMEN MARKET */
static const char *const LUMEN_MARKET_ROWS[] = {
    "WWnWWkWWnWW",
    "wwwwwwwwwww",
    ":::::::::::",
    "<==>:::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::D:::::",
};
static const DecorPlace LUMEN_MARKET_DECOR[] = {
    DP(BARREL_IN, 0, 2), DP(SACKS_IN, 3, 2), DP(PENNANT, 1, 0), DP(CALENDAR, 3, 0),
    DP(SHOP_SHELF, 5, 1), DP(SHOP_SHELF, 7, 1), DP(LANTERN_RACK, 9, 1),
    DP(DISPLAY_CASE, 6, 5), DP(DISPLAY_CASE, 8, 5), DP(BARREL_IN, 10, 4),
    DP(PLANT, 10, 6), DP(SMALL_PLANT, 0, 7), DP(SMALL_RUG, 5, 7),
};

/* VOLT HALL: pylons (decor) wall a maze; floor switches (OBJ_SWITCH, arg =
 * group) toggle the crackling barriers of the same group (OBJ_BARRIER,
 * raised at first). Solution: a (4,13), then b (3,9), then c (11,9). The
 * switch at (5,6) is a trap: it flips group b back. (See test_east.c.)
 *   row  4: pylons, barrier c at x 7
 *   row  7: pylons, barrier b at x 1, barrier a at x 13
 *   rows 8-10: a pylon column at x 7
 *   row 11: pylons, barrier a at x 2, barrier b at x 12 */
static const char *const VOLT_HALL_ROWS[] = {
    "WWWWWWnWnWWWWWW",
    "wwwwwwwwwwwwwww",
    ":::::::::::::::",
    ":::::::::::::::",
    ":::::::::::::::",
    ":::::::::::::::",
    ":::::::::::::::",
    ":::::::::::::::",
    ":::::::::::::::",
    ":::::::::::::::",
    ":::::::::::::::",
    ":::::::::::::::",
    ":::::::::::::::",
    ":::::::::::::::",
    ":::::::::::::::",
    ":::::::::::::::",
    ":::::::D:::::::",
};
static const DecorPlace VOLT_HALL_DECOR[] = {
    /* row 4 */
    DP(PYLON, 0, 4), DP(PYLON, 1, 4), DP(PYLON, 2, 4), DP(PYLON, 3, 4), DP(PYLON, 4, 4),
    DP(PYLON, 5, 4), DP(PYLON, 6, 4), DP(PYLON, 8, 4), DP(PYLON, 9, 4), DP(PYLON, 10, 4),
    DP(PYLON, 11, 4), DP(PYLON, 12, 4), DP(PYLON, 13, 4), DP(PYLON, 14, 4),
    /* row 7 */
    DP(PYLON, 0, 7), DP(PYLON, 2, 7), DP(PYLON, 3, 7), DP(PYLON, 4, 7), DP(PYLON, 5, 7),
    DP(PYLON, 6, 7), DP(PYLON, 7, 7), DP(PYLON, 8, 7), DP(PYLON, 9, 7), DP(PYLON, 10, 7),
    DP(PYLON, 11, 7), DP(PYLON, 12, 7), DP(PYLON, 14, 7),
    /* the column between the west and east rooms */
    DP(PYLON, 7, 8), DP(PYLON, 7, 9), DP(PYLON, 7, 10),
    /* row 11 */
    DP(PYLON, 0, 11), DP(PYLON, 1, 11), DP(PYLON, 3, 11), DP(PYLON, 4, 11), DP(PYLON, 5, 11),
    DP(PYLON, 6, 11), DP(PYLON, 7, 11), DP(PYLON, 8, 11), DP(PYLON, 9, 11), DP(PYLON, 10, 11),
    DP(PYLON, 11, 11), DP(PYLON, 13, 11), DP(PYLON, 14, 11),
    /* the master's gallery */
    DP(VOLT_BANNER, 3, 0), DP(VOLT_BANNER, 11, 0), DP(RESONANCE_COIL, 0, 1), DP(RESONANCE_COIL, 14, 1),
    DP(DYNAMO, 1, 2), DP(DYNAMO, 12, 2),
    /* the entrance */
    DP(PLANT, 0, 15), DP(PLANT, 14, 15), DP(SMALL_RUG, 6, 15),
};
static const MapObj VOLT_HALL_OBJS[] = {
    OBJ(BARRIER, 7, 4, 2),
    OBJ(BARRIER, 1, 7, 1), OBJ(BARRIER, 13, 7, 0),
    OBJ(BARRIER, 2, 11, 0), OBJ(BARRIER, 12, 11, 1),
    OBJ(SWITCH, 4, 13, 0),     /* a */
    OBJ(SWITCH, 3, 9, 1),      /* b */
    OBJ(SWITCH, 11, 9, 2),     /* c */
    OBJ(SWITCH, 5, 6, 1),      /* the trap: b again */
};
#define VOLT_MASTER_X 7
#define VOLT_MASTER_Y 2

/* RESONANCE WORKS: the front desk hosts SCR_FUSION_DESK (fusion.c); the
 * floor in front of it is left open for the fusion machines' decor. */
static const char *const RESONANCE_WORKS_ROWS[] = {
    "WWnWWWkWWWnWW",
    "wwwwwwwwwwwww",
    ":::::::::::::",
    "::::<===>::::",
    ":::::::::::::",
    ":::::::::::::",
    ":::::::::::::",
    ":::::::::::::",
    ":::::::::::::",
    "::::::D::::::",
};
static const DecorPlace RESONANCE_WORKS_DECOR[] = {
    DP(ENERGY_VAT, 0, 1), DP(ENERGY_VAT, 1, 1), DP(RESONANCE_COIL, 2, 1), DP(CHALKBOARD, 4, 0),
    DP(RESONANCE_COIL, 10, 1), DP(ENERGY_VAT, 11, 1), DP(ENERGY_VAT, 12, 1),
    /* the fusion machines (FUSION owner: fusion_examine opens each one) */
    DP(FZ_EXTRACTOR, 0, 4), DP(FZ_MIXER, 2, 4), DP(FZ_TANKS, 0, 6), DP(FZ_LOOM, 9, 4),
    DP(TELEGRAPH, 12, 7), DP(PLANT, 0, 8), DP(SMALL_PLANT, 12, 8),
};

/* BIKE SHOP */
static const char *const BIKE_SHOP_ROWS[] = {
    "WWnWWkWWnWW",
    "wwwwwwwwwww",
    "...........",
    ".......<==>",
    "...........",
    "...........",
    "...........",
    "...........",
    ".....D.....",
};
static const DecorPlace BIKE_SHOP_DECOR[] = {
    DP(BIKE_DISPLAY, 0, 2), DP(BIKE_DISPLAY, 3, 2), DP(PENNANT, 1, 0), DP(CALENDAR, 6, 0),
    DP(GEARS, 3, 0), DP(SHOP_SHELF, 7, 1), DP(BIKE_DISPLAY, 0, 5), DP(BIKE_DISPLAY, 8, 5),
    DP(BARREL_IN, 10, 7), DP(SMALL_PLANT, 0, 7),
};

/* COPPER KETTLE INN: the innkeeper lets rooms; the cook (SCR_CHEF, craft.c)
 * works the stove. */
static const char *const LUMEN_INN_ROWS[] = {
    "WWnWWpWWnWW",
    "wwwwwwwwwww",
    "...........",
    "<==>.......",
    "...........",
    "...........",
    "...........",
    "...........",
    ".....D.....",
};
static const DecorPlace LUMEN_INN_DECOR[] = {
    DP(SHOP_SHELF, 0, 1), DP(CALENDAR, 3, 0), DP(STOVE, 6, 1), DP(SINK_COUNTER, 7, 1),
    DP(ICEBOX, 9, 1), DP(BARREL_IN, 10, 2),
    DP(LONG_TABLE, 6, 4), DP(STOOL, 6, 6), DP(STOOL, 8, 6), DP(TABLE_ROUND, 1, 5),
    DP(STOOL, 0, 6), DP(STOOL, 3, 6), DP(PLANT, 10, 6), DP(SMALL_RUG, 5, 7),
};

/* LUMEN HOUSE (canal row, west): a family */
static const char *const LUMEN_HOUSE_ROWS[] = {
    "WWnWWkWWnWW",
    "wwwwwwwwwww",
    "...........",
    "...........",
    "...........",
    "...........",
    "...........",
    "...........",
    ".....D.....",
};
static const DecorPlace LUMEN_HOUSE_DECOR[] = {
    DP(BOOKSHELF, 0, 1), DP(FIREPLACE, 3, 1), DP(TV, 5, 2), DP(CALENDAR, 6, 0),
    DP(DRESSER, 8, 2), DP(DOUBLE_BED, 9, 1),
    DP(TABLE, 1, 4), DP(CHAIR_SIDE, 0, 4), DPF(CHAIR_SIDE, 3, 4), DP(CUSHION, 5, 5),
    DP(KIN_BASKET, 9, 5), DP(TOY_BOX, 10, 7), DP(PLANT, 0, 7), DP(SMALL_RUG, 5, 7),
};

/* LUMEN HOUSE (canal row, east): the tinker's workshop */
static const char *const LUMEN_HOUSE_B_ROWS[] = {
    "WWnWWkWWnWW",
    "wwwwwwwwwww",
    ":::::::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::D:::::",
};
static const DecorPlace LUMEN_HOUSE_B_DECOR[] = {
    DP(GEARS, 0, 0), DP(DYNAMO, 3, 2), DP(RESONANCE_COIL, 5, 1), DP(TELEGRAPH, 6, 2),
    DP(CHALKBOARD, 7, 0), DP(BED, 10, 2), DP(DESK, 1, 5), DP(CHAIR_UP, 1, 6),
    DP(ENERGY_VAT, 9, 4), DP(BIKE_DISPLAY, 7, 7), DP(SACKS_IN, 0, 7),
};

/* CLOCKWORK SPIRE: the gear hall below, the Crown above. The stair up is
 * sealed by a boulder (STRENGTH); HOROLOGOS waits in the Crown. */
static const char *const CLOCKWORK_SPIRE_ROWS[] = {
    "WWWWWWkWWWWWW", /*  0 */
    "wwwwwwwwwwwww", /*  1 */
    ":::::::::::::", /*  2  the Crown */
    ":::::::::::::", /*  3 */
    ":::::::::::::", /*  4 */
    ":::::::::::::", /*  5 */
    ":::::::::::::", /*  6 */
    "WWWWWW:WWWWWW", /*  7  the stair */
    "wwwwww:wwwwww", /*  8 */
    ":::::::::::::", /*  9  the gear hall */
    ":::::::::::::", /* 10 */
    ":::::::::::::", /* 11 */
    ":::::::::::::", /* 12 */
    ":::::::::::::", /* 13 */
    ":::::::::::::", /* 14 */
    ":::::::::::::", /* 15 */
    ":::::::::::::", /* 16 */
    ":::::::::::::", /* 17 */
    "::::::D::::::", /* 18 */
};
static const DecorPlace CLOCKWORK_SPIRE_DECOR[] = {
    /* the Crown */
    DP(GEARS, 0, 0), DP(GEARS, 11, 0), DP(GRANDFATHER_CLOCK, 3, 1), DP(GRANDFATHER_CLOCK, 9, 1),
    DP(RESONANCE_COIL, 0, 4), DP(RESONANCE_COIL, 12, 4),
    /* the gear hall */
    DP(GEARS, 0, 7), DP(GEARS, 2, 7), DP(GEARS, 9, 7), DP(GEARS, 11, 7),
    DP(GRANDFATHER_CLOCK, 0, 10), DP(GRANDFATHER_CLOCK, 12, 10), DP(DYNAMO, 1, 14),
    DP(DISPLAY_CASE, 10, 14), DP(DESK, 2, 12), DP(CHAIR_UP, 2, 13), DP(GLOBE, 11, 12),
    DP(PLANT, 0, 17), DP(PLANT, 12, 17), DP(SMALL_RUG, 5, 17),
};
static const MapObj CLOCKWORK_SPIRE_OBJS[] = {
    OBJ(BOULDER, 6, 9, 0),              /* seals the stair: push it aside */
    OBJ(LEGEND, 6, 3, SP_HOROLOGOS),    /* the clockwork titan */
};
