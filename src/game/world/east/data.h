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
 *   ELDERWOOD HEART  north x 30-31 <-> BRAMBLEWOOD south (behind a STRENGTH
 *                    boulder on Bramblewood, WOOD_OBJS below)
 * Doors: see warps.inc. The CLOCKWORK SPIRE is entered through the clock
 * tower in Lumen City (CY CLOCK_TOWER stamp).
 *
 * Legends: route maps use the wild tileset (. grass  , tall grass  = path
 * ~ water  T/t trees  P/p pines  C/c cliff  L [ ] ledges  d dirt  f forest
 * floor  R reeds  w flowering tall grass  g golden tall grass -- tools/grass.py);
 * Lumen uses the city tileset (tools/tilesets/ts_city.py:
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
    "pp,,,ggggggg,,..dddddddddddddddddd..,,,,,,pp", /*  9 */
    "PP,gggggggggg,..dddddddddddddddddd..,,,,,,PP", /* 10 */
    "ppgggggggggggg..dddddddddddddddddd..,,,,,,pp", /* 11 */
    "PPgggggggggg,,..dddddddddddddddddd..,,,,,,PP", /* 12 */
    "pp,ggggggg,,,,..dddddddddddddddddd..,,,,,,pp", /* 13 */
    "PP,,,ggg,,,,,,..dddddddddddddddddd..,,,,,,PP", /* 14 */
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
/*
 * A lamp-lit hill city on four levels (docs/ELEVATION.md; docs/handoff/towns_east.md):
 *   3  THE CROWN (north): the Volt Hall, the row houses, the tinker's house and
 *      the Spire's clock tower along the old rampart; the north gate (x 24-25).
 *      Wooded bluff to the west, forest to the east. A 3-row cliff drops into
 *      the Works yard; 2-row cliffs onto the west terrace and the inn strip.
 *   2  THE BEACON TERRACE: the octagonal plaza, raised above everything
 *      around it, with a bastion and double stairs (24-25, 26-27) down to the
 *      canal quarter, grand stairs (24-25, 10) up to the Crown and ledges
 *      (17-18, 11) to hop down from the Crown walk. The sunken WELL GARDEN
 *      (28-32, 3-7) inside the Crown is reached only by the old conduit: a
 *      TUNNEL under the Crown walk (30, 8-9) whose mouth (30, 10) is HIDDEN in
 *      the terrace's cliff (hint: pebbles and a crate; the LAMPLIGHTER).
 *   1  THE WEST TERRACE (Hearth, bike shop, west gate y 20-21; ledges 10-12,27
 *      into the canal quarter), the INN STRIP, the EAST WARD (market, east gate
 *      y 20-21) and LUMEN PARK. The Boulevard climbs onto the plaza by side
 *      stairs (16, 20-21) and down again (32, 20-21).
 *   0  THE CUT: the canal and its towpath in a gorge. The Boulevard crosses it
 *      on a bridge (BRIDGE_H 40-43, 20-21); the towpath runs UNDER it from the
 *      canal side (park stairs 45,33) north to the RESONANCE WORKS yard. The
 *      CANAL QUARTER, the low canal, the basin and the canal gardens.
 * A gap in the park's tree line (52, 44-45) hides the lamplighters' grove.
 */


static const char *const LUMEN_ROWS[] = {
    "TTTTTT##################==#########TTTTTTTTTTTTTTTTTTTTT", /*  0 */
    "ttttttwwwwwwwwwwwwwwwwww==wwwwwwwwwttttttttttttttttttttt", /*  1 */
    "TTTTTT..................====.................cccccTTTTTT", /*  2 */
    "tttttt..................====rgggr............ccccctttttt", /*  3 */
    "TTTTT...................====ggggg............cccccTTTTTT", /*  4 */
    "ttttt...................====ggggg............ccccctttttt", /*  5 */
    "TTTTg...........============ggggg===========.cccccccTTTT", /*  6 */
    "ttttg.cccccccccc============ygggy===========.ccccccctttt", /*  7 */
    "TTTTT.cccccccccc........=====================cccccccTTTT", /*  8 */
    "ttttt.cccccccccccccc....======.===..................tttt", /*  9 */
    "TTTgg.cccccccccccccc................................TTTT", /* 10 */
    "tttgg.....c.........................................tttt", /* 11 */
    "TTTTT................pppppppp...........~~~~ccccccccTTTT", /* 12 */
    "ttttt.......gggg...pppppppppppp.........~~~~cccccccctttt", /* 13 */
    "............gggg..pppppppppppppp........~~==ccccccccTTTT", /* 14 */
    "............gggg..pppppppppppppp........~~==cccccccctttt", /* 15 */
    "#yyyg.......gggg..pppppppppppppp........~~==ccccccccTTTT", /* 16 */
    "#gggg.......grrg..pppppppppppppp........~~=ccccccccctttt", /* 17 */
    "#gggg....=........pppppppppppppp........~~=ccccccccc....", /* 18 */
    "#gggg....=........pppppppppppppp........~~=ccccccccc....", /* 19 */
    "==================pppppppppppppp========~~==============", /* 20 */
    "==================pppppppppppppp========~~==============", /* 21 */
    "#gg....=..........pppppppppppppp........~~==ccccccccccTT", /* 22 */
    "#gg......ggggg.....pppppppppppp.........~~==cccccccccctt", /* 23 */
    "#gg......ggggg.......pppppppp...........~~==ccccccccccTT", /* 24 */
    "#gg......gyyyg..........pp..............~~==cccccccccctt", /* 25 */
    "#gg......grrgg..........==..............~~==ccccccccccTT", /* 26 */
    "#gg.......ggg...........==..cccccccccccc~~==cccc==cccctt", /* 27 */
    "........========........==========cccccc~~==cccc==ccccTT", /* 28 */
    "#.....................===.........cccccc~~==cccc==cccctt", /* 29 */
    "#...................===...........cccccc~~==.ggg==ggggTT", /* 30 */
    "#.................===.............cccccc~~==.ggg==gyygtt", /* 31 */
    "#...............===.gggg..........cccccc~~==.ggg==grrgTT", /* 32 */
    "#gg...........===...yyyg..........cccccc~~==.=====ggggtt", /* 33 */
    "#yy.........===.....gggg..........cccccc~~==.TTgggggggTT", /* 34 */
    "#.======================================~~==.tt,,,,,,,tt", /* 35 */
    "#...==..~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~==.gg,,,,,,,TT", /* 36 */
    "#...==..~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~==.gg,,,,,,,tt", /* 37 */
    "TTggggggggggggggggggggggggg~~~~~~~~~~~~~~~~~~,,,,,,,,,TT", /* 38 */
    "ttggrrrrgggggggggggggggggg~~~~~~~~~~~~~~~~~~~,,,,,,,,,tt", /* 39 */
    "TTggyyyygggggggggggggTTg~~~~~~~~~~~~~~~~~~~~~,,,,,,,,,TT", /* 40 */
    "ttgggggggggggggggggggttg~~~~~~~~~~~~~~~~~~~~~,,,,,,,,,tt", /* 41 */
    "TTggggggggggggggggggggggg~~~~~~~gTTg~~~~~~~~~gg,,,,,,,TT", /* 42 */
    "ttg===============ggggggg~~~~~~~gttg~~~~~~~~~gyyggggggtt", /* 43 */
    "TTggggggggggyyyyggTTgggggg~~~~~~gTTg~~~~~~~~~TTTTTTTTTTT", /* 44 */
    "ttggggggggggrrrrggttggggg~~~~~~~gttg~~~~~~~~~ttttttttttt", /* 45 */
    "TTTTTTTTTTggggggggggyyyg~~~~~~~~~~~~~~~~~~~~~TTTTTgggrrT", /* 46 */
    "ttttttttttggggggggggggg~~~~~~~~~~~~~~~~~~~~~~tttttgggggt", /* 47 */
    "TTTTTTTTTTTTTTTTTTTTTTTT~~~~~~~~~~~~~~~~~~~~~TTTTTTTTTTT", /* 48 */
    "tttttttttttttttttttttttt~~~~~~~~~~~~~~~~~~~~~ttttttttttt", /* 49 */
};

/* heights (0-3), stairs (^ v < >) and ledges (_): docs/ELEVATION.md */
static const char *const LUMEN_ELEV[] = {
    "33333333333333333333333333333333333333333333333333333333", /*  0 */
    "33333333333333333333333333333333333333333333333333333333", /*  1 */
    "33333333333333333333333333332222233333333333333333333333", /*  2 */
    "33333333333333333333333333332222233333333333333333333333", /*  3 */
    "33333333333333333333333333332222233333333333333333333333", /*  4 */
    "33333333333333333333333333332222233333333333333333333333", /*  5 */
    "33333333333333333333333333332222233333333333333333333333", /*  6 */
    "33333333333333333333333333332222233333333333333333333333", /*  7 */
    "33333333333333333333333333333323333333333333333333333333", /*  8 */
    "33333333333333333333333333333323331111110000000000003333", /*  9 */
    "333333333333333333332222^^222222111111110000000000003333", /* 10 */
    "3333311111^111112__2222222222222111111110000000000003333", /* 11 */
    "3333311111^111112222222222222222111111110000000000003333", /* 12 */
    "33333111111111112222222222222222111111110000000000003333", /* 13 */
    "11111111111111112222222222222222111111110000000000003333", /* 14 */
    "11111111111111112222222222222222111111110000000000003333", /* 15 */
    "11111111111111112222222222222222111111110000000000003333", /* 16 */
    "11111111111111112222222222222222111111110000000000003333", /* 17 */
    "11111111111111112222222222222222111111110000000000001111", /* 18 */
    "11111111111111112222222222222222111111110000000000001111", /* 19 */
    "1111111111111111>222222222222222<11111110000111111111111", /* 20 */
    "1111111111111111>222222222222222<11111110000111111111111", /* 21 */
    "11111111111111112222222222222222111111110000111111111111", /* 22 */
    "11111111111111112222222222222222111111110000111111111111", /* 23 */
    "11111111111111112222222222222222111111110000111111111111", /* 24 */
    "11111111111111111111112222221111111111110000111111111111", /* 25 */
    "111111111111111100000000^^00000000000^000000111111111111", /* 26 */
    "1111111100___00000000000^^000000000000000000111111111111", /* 27 */
    "00000000000000000000000000000000000000000000111111111111", /* 28 */
    "00000000000000000000000000000000000000000000111111111111", /* 29 */
    "00000000000000000000000000000000000000000000011111111111", /* 30 */
    "00000000000000000000000000000000000000000000011111111111", /* 31 */
    "00000000000000000000000000000000000000000000011111111111", /* 32 */
    "000000000000000000000000000000000000000000000>1111111111", /* 33 */
    "00000000000000000000000000000000000000000000011111111111", /* 34 */
    "00000000000000000000000000000000000000000000011111111111", /* 35 */
    "00000000000000000000000000000000000000000000011111111111", /* 36 */
    "00000000000000000000000000000000000000000000011111111111", /* 37 */
    "00000000000000000000000000000000000000000000011111111111", /* 38 */
    "00000000000000000000000000000000000000000000011111111111", /* 39 */
    "00000000000000000000000000000000000000000000011111111111", /* 40 */
    "00000000000000000000000000000000000000000000011111111111", /* 41 */
    "00000000000000000000000000000000000000000000011111111111", /* 42 */
    "00000000000000000000000000000000000000000000011111111111", /* 43 */
    "00000000000000000000000000000000000000000000011111111111", /* 44 */
    "00000000000000000000000000000000000000000000011111111111", /* 45 */
    "00000000000000000000000000000000000000000000011111111111", /* 46 */
    "00000000000000000000000000000000000000000000011111111111", /* 47 */
    "00000000000000000000000000000000000000000000011111111111", /* 48 */
    "00000000000000000000000000000000000000000000011111111111", /* 49 */
};

static const ElevFeat LUMEN_FEATS[] = {
    EF(BRIDGE_H, 40, 20, 4, 2),  /* the Boulevard over the Cut; the towpath under it */
    EF(TUNNEL, 30, 8, 1, 2),     /* the old conduit under the Crown walk */
    EF(HIDDEN, 30, 10, 1, 1),    /* ...its mouth, hidden in the Crown's face */
    EF(HIDDEN, 52, 44, 1, 2),    /* a gap in the park's tree line to the lamplighters' grove */
};

static const Stamp LUMEN_STAMPS[] = {
    STAMP(CY, VOLT_HALL, 6, 2),     /* door 10,6  (the Crown) */
    STAMP(CY, ROW_HOUSES, 15, 2),   /* doors 16,5 and 20,5 (locked) */
    STAMP(CY, HOUSE_B, 38, 2),      /* door 40,5: TINKER'S HOUSE */
    STAMP(CY, CLOCK_TOWER, 47, 2),  /* door 48,7: the CLOCKWORK SPIRE (the Crown's east end) */
    STAMP(CY, HEARTH, 6, 14),       /* door 9,17  */
    STAMP(CY, BIKE_SHOP, 4, 23),    /* door 7,26  */
    STAMP(CY, INN, 32, 13),         /* door 35,16 */
    STAMP(CY, WORKS, 44, 13),       /* door 47,16 (the Works yard, down in the Cut) */
    STAMP(CY, MARKET, 45, 23),      /* door 49,26 (east ward) */
    STAMP(CY, HOUSE_A, 3, 29),      /* door 5,32 (canal quarter) */
    STAMP(CY, HOUSE_C, 30, 28),     /* door 31,31 (locked) */
};

static const DecorPlace LUMEN_DECOR[] = {
    DP(SIGNPOST, 23, 2), DP(SIGNPOST, 2, 19), DP(SIGNPOST, 51, 22), DP(SIGNPOST, 17, 19),
    DP(SIGNPOST, 43, 7),
    /* the Crown: the Volt Hall's forecourt, the row houses, the tinker */
    DP(TESLA_COIL, 6, 8), DP(TESLA_COIL, 15, 8), DP(CITY_LAMP, 23, 4), DP(CITY_LAMP, 22, 8),
    DP(FLOWER_POT, 34, 3), DP(FLOWER_POT, 37, 3), DP(CITY_LAMP, 33, 4), DP(PARKED_BIKE, 43, 3),
    DP(FLOWER_POT, 14, 6), DP(BUSH, 12, 10),
    /* the sunken Well garden (only through the old conduit) */
    DP(FOUNTAIN, 29, 4), DP(CITY_LAMP, 28, 4), DP(BENCH, 31, 7), DP(SMALL_FLOWERS, 32, 3),
    /* the Spire's terrace */
    DP(TESLA_COIL, 45, 2), DP(TESLA_COIL, 50, 6), DP(BENCH, 45, 7),
    /* the Hearth, the west gate and the bike shop */
    DP(FLOWER_POT, 5, 17), DP(BENCH, 13, 14), DP(CITY_LAMP, 11, 18), DP(CITY_LAMP, 4, 18),
    DP(CITY_LAMP, 4, 22), DP(CITY_LAMP, 12, 22), DP(PARKED_BIKE, 3, 25), DP(PARKED_BIKE, 9, 26),
    /* the Beacon plaza */
    DP(BEACON, 24, 16), DP(FOUNTAIN, 20, 15), DP(FOUNTAIN, 28, 15),
    DP(MARKET_STALL, 19, 22), DP(MARKET_STALL, 28, 22), DP(SACKS, 22, 23), DP(BARREL, 27, 23),
    DP(BENCH, 20, 18), DP(BENCH, 28, 18), DP(TESLA_COIL, 18, 13), DP(TESLA_COIL, 31, 13),
    DP(CITY_LAMP, 22, 12), DP(CITY_LAMP, 27, 12), DP(CITY_LAMP, 34, 18), DP(CITY_LAMP, 38, 18),
    DP(CITY_LAMP, 34, 22), DP(CITY_LAMP, 38, 22), DP(BENCH, 36, 18), DP(FLOWER_POT, 33, 17),
    DP(PEBBLES, 30, 11), DP(CRATE, 29, 11),
    /* the Works yard */
    DP(BARREL, 51, 17), DP(CRATE, 51, 16), DP(SACKS, 50, 19), DP(BARREL, 44, 19),
    /* the east ward */
    DP(CITY_LAMP, 47, 28), DP(CITY_LAMP, 50, 28), DP(BARREL, 53, 28), DP(CRATE, 44, 29),
    /* LUMEN PARK and the grove */
    DP(BUSH, 46, 30), DP(BUSH, 47, 31), DP(BUSH, 53, 33), DP(BENCH, 50, 43), DP(PEBBLES, 52, 43),
    /* the canal quarter */
    DP(FOUNTAIN, 9, 31), DP(BENCH, 9, 34), DP(FLOWER_POT, 14, 29), DP(CITY_LAMP, 21, 28),
    DP(CITY_LAMP, 27, 29), DP(BENCH, 27, 33), DP(FLOWER_POT, 35, 30), DP(BARREL, 38, 28),
    DP(TESLA_COIL, 34, 32), DP(FLOWER_POT, 2, 29), DP(FLOWER_POT, 18, 33),
    /* the canal gardens */
    DP(FOUNTAIN, 7, 41), DP(BENCH, 4, 44), DP(BENCH, 15, 40), DP(BUSH, 16, 46),
    DP(BUSH, 23, 43), DP(SMALL_FLOWERS, 10, 45),
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
    "PPfR~~~~~Rffy.............f,,,www,,,,,PP", /* 22 */
    "ppfR~~~~~Rff..............f,,wwwww,,,,pp", /* 23 */
    "PPfR~~~~~Rff..............f,,,wwww,,,,PP", /* 24 */
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

/* Bramblewood's south path to Elderwood Heart narrows to x 31 at row 34 (a
 * stump, WOOD_DECOR) and a STRENGTH boulder stands in front of the gap (the
 * core owns Bramblewood; its MapDef points here). Push it aside. One boulder,
 * not two: two free boulders in the open wood made the reachable states
 * explode (tools/tests/test_puzzles.c proves every map). */
static const MapObj WOOD_OBJS[] = {
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
