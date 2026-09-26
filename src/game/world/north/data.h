/*
 * world/north/data.h -- map rows, stamps, decor, objects and wild slots of
 * the NORTH region (owner: W-NORTH): Frostpine Pass, Frosthollow and its
 * interiors, the Rime Hall, the hot spring, Whitecrown Peak, the Sky Isle,
 * Glimmer Caverns (two floors) and the Starfall Grotto.
 *
 * Edge contracts (docs/EXPANSION.md 9):
 *   FROSTPINE PASS south  x 11-12  <-> STORMSTONE RISE north (x 11-12)
 *   FROSTPINE PASS north  x 19-20  <-> FROSTHOLLOW south
 *   FROSTHOLLOW north     x 19-20  <-> WHITECROWN PEAK south
 * Doors: Frosthollow's cave mouth -> GLIMMER CAVERNS (exit mat back);
 * Glimmer stairs down <-> Glimmer Depths stairs up; the Depths' violet
 * crack -> STARFALL GROTTO (exit mat back). The SKY ISLE is reached only by
 * FLY (fly point in flypoints.inc).
 *
 * 'snow' legend (tools/tilesets/ts_snow.py):
 *   .  snow   ,  drift (wild kin)   =  trodden path   ~  icy water
 *   P p  snowy pine (top / bottom)   L [ ]  icy ledge   C c  cliff / face
 *   R  crag   #  slate cobbles   i  ice (slide)   7 8 9 4 6 1 2 3  ice rim
 *   o  rock in the ice   K  sea of clouds   F  hall floor   W w  hall wall
 *   D  exit mat   ' '  void
 * 'cave' legend (tools/tilesets/ts_cave.py):
 *   .  floor   ,  glowmoss (wild kin)   =  gravel path   ~  underground lake
 *   X  rock mass   c  wall face   Q  crystal vein   *  crystal outcrop
 *   L [ ]  ledge   D  exit mat   7 8 9 4 5 6 1 2 3  the starlit pool
 */

/* FROSTPINE PASS (40 x 44) */
static const char *const FROSTPINE_ROWS[] = {
    "PPPPPPPPPPPPPPPPPPP==PPPPPPPPPPPPPPPPPPP", /*  0 */
    "ppppppppppppppppppp==ppppppppppppppppppp", /*  1 */
    "PP..........RRR....==..PPP..........PPPP", /*  2 */
    "pp.,,,,,,,,.RRR....==..ppp.,,,,,,,,,pppp", /*  3 */
    "PP.,,,,,,,,.RRR....==..PPP.,,,,,,,,,PPPP", /*  4 */
    "pp.,,,,,,,,........==..ppp.,,,,,,,,,pppp", /*  5 */
    "PP.,,,,,,,,........==......,,,,,,,,,PPPP", /*  6 */
    "pp.,,,,,,,,........==...............pppp", /*  7 */
    "PP.................==.................PP", /*  8 */
    "ppCCCCCCCCCCCCCCCC.==.CCCC........CCCCpp", /*  9 */
    "PPcccccccccccccccc.==.cccc[LLLLLL]ccccPP", /* 10 */
    "pp.................==.................pp", /* 11 */
    "PP............PPP..==.................PP", /* 12 */
    "pp............ppp..==.....,,,,,,,,,,..pp", /* 13 */
    "PP.7888888889......==.....,,,,,,,,,,..PP", /* 14 */
    "pp.4iiiiiiii6......==.....,,,,PPP,,,..pp", /* 15 */
    "PP.4iioiiiii6......==.....,,,,ppp,,,..PP", /* 16 */
    "pp.4iiiiiiii6......==.....,,,,,,,,,,..pp", /* 17 */
    "PP.4iiiiioii6......==.....,,,,,,,,,,..PP", /* 18 */
    "pp.4iiiiiiii6......==.....,,,,,,,,,,..pp", /* 19 */
    "PP.1222222223......==.PPP.............PP", /* 20 */
    "pp.................==.ppp...,,,,,,,,..pp", /* 21 */
    "PP.,,,,,,..........==.......,,,,,,,,..PP", /* 22 */
    "pp.................==.................pp", /* 23 */
    "PP~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~PP", /* 24 */
    "pp~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~pp", /* 25 */
    "PP.................==.................PP", /* 26 */
    "pp.................==.................pp", /* 27 */
    "PP.................==.................PP", /* 28 */
    "pp.................==.................pp", /* 29 */
    "PP.........==========.................PP", /* 30 */
    "pp.........==========.................pp", /* 31 */
    "PP.........==.........PPPP..,,,,......PP", /* 32 */
    "pp.........==.........pppp..,,,,......pp", /* 33 */
    "PP.,,,,,,..==......................PPPPP", /* 34 */
    "pp.,,,,,,..==......................ppppp", /* 35 */
    "PP.,,,,,,..==.PPPP......,,,,,,,,,,,PPPPP", /* 36 */
    "pp.,,,,,,..==.pppp......,,,,,,,,,,,ppppp", /* 37 */
    "PP.,,,,,,..==.PPPP......,,,,,,,,,,,PPPPP", /* 38 */
    "pp.,,,,,,..==.pppp......,,,,,,,,,,,ppppp", /* 39 */
    "PPPPPPPP...==.PPPP......,,,,,,,,,,,PPPPP", /* 40 */
    "pppppppp...==.pppp.................ppppp", /* 41 */
    "PPPPPPPPPPP==PPPPPPPPPPPPPPPPPPPPPPPPPPP", /* 42 */
    "ppppppppppp==ppppppppppppppppppppppppppp", /* 43 */
};
static const DecorPlace FROSTPINE_DECOR[] = {
    DP(BRIDGE_V, 19, 24), DP(BRIDGE_V, 20, 24), DP(BRIDGE_V, 19, 25), DP(BRIDGE_V, 20, 25),
    DP(SIGNPOST, 13, 39), DP(SIGNPOST, 21, 3), DP(SKI_RACK, 18, 28), DP(SLED, 17, 28),
    DP(FROZEN_TREE, 2, 12), DP(FROZEN_TREE, 36, 12), DP(FROZEN_TREE, 21, 14),
    DP(ICE_CRYSTAL, 13, 20), DP(ICE_CRYSTAL, 2, 21), DP(ROCK, 9, 27), DP(ROCK, 33, 27),
    DP(LOG, 4, 30), DP(STUMP, 26, 29), DP(CAMPFIRE, 30, 29),
};
static const MapObj FROSTPINE_OBJS[] = {
    OBJ(BERRY, 3, 28, 20), OBJ(BERRY, 36, 23, 21),
};

/* FROSTHOLLOW (40 x 36) */
static const char *const FROSTHOLLOW_ROWS[] = {
    "PPPPPPPPPPPPPPPPPPP==PPPPPPPPPPPPPPPPPPP", /*  0 */
    "ppppppppppppppppppp==ppppppppppppppppppp", /*  1 */
    "PPPP............PP.==.PP..........PPPPPP", /*  2 */
    "pppp............pp.==.pp..........pppppp", /*  3 */
    "PP..............PP.==.PP..........PPPPPP", /*  4 */
    "pp..............pp.==.pp..........pppppp", /*  5 */
    "PP.................==.............PPPPPP", /*  6 */
    "pp.................==.............pppppp", /*  7 */
    "PP.....=.....=.....==.......=.........PP", /*  8 */
    "pp....=========================.......pp", /*  9 */
    "PP....=========================.RRRRRRPP", /* 10 */
    "pp.................==...........RRRRRRpp", /* 11 */
    "PP.................==...........RRRRRRPP", /* 12 */
    "pp.78888889........==...........CCCCCCpp", /* 13 */
    "PP.4iiiiii6...############......ccccccPP", /* 14 */
    "pp.4iiiiii6...############.........=..pp", /* 15 */
    "PP.4iiiiii6...############===========.PP", /* 16 */
    "pp.4iiiiii6...############===========.pp", /* 17 */
    "PP.4iiiiii6...############.........P..PP", /* 18 */
    "pp.12222223...############.........p..pp", /* 19 */
    "PP............############............PP", /* 20 */
    "pp.................==.................pp", /* 21 */
    "PP.................==..PP........PPPP.PP", /* 22 */
    "pp.............PP..==..pp........pppp.pp", /* 23 */
    "PP.............pp..==..PP........PPPP.PP", /* 24 */
    "pp.............PP..==..pp........pppp.pp", /* 25 */
    "PP.................==............PPPP.PP", /* 26 */
    "pp....=.....=......==........=...pppp.pp", /* 27 */
    "PP....=========================..PPPP.PP", /* 28 */
    "pp....=========================..pppp.pp", /* 29 */
    "PPPPPP.............==............PPPP.PP", /* 30 */
    "pppppp..PPPPPP.....==............pppp.pp", /* 31 */
    "PP......pppppp.....==.................PP", /* 32 */
    "pp.................==.................pp", /* 33 */
    "PPPPPPPPPPPPPPPPPPP==PPPPPPPPPPPPPPPPPPP", /* 34 */
    "ppppppppppppppppppp==ppppppppppppppppppp", /* 35 */
};
static const Stamp FROSTHOLLOW_STAMPS[] = {
    STAMP(SN, HEARTH, 5, 4), STAMP(SN, SHOP, 11, 4), STAMP(SN, HALL, 25, 3), STAMP(SN, HOUSE, 4, 23), STAMP(SN, HOUSE, 10, 23), STAMP(SN, BATHS, 27, 23), STAMP(SN, CAVE, 34, 13),
};
static const DecorPlace FROSTHOLLOW_DECOR[] = {
    DP(ICE_STATUE, 16, 16), DP(ICE_STATUE, 23, 16), DP(LANTERN_POST, 14, 13),
    DP(LANTERN_POST, 25, 13), DP(LANTERN_POST, 14, 21), DP(LANTERN_POST, 25, 21),
    DP(SIGNPOST, 21, 31), DP(SIGNPOST, 30, 8), DP(SIGNPOST, 36, 17), DP(NOTICE_BOARD, 11, 11),
    DP(SNOWMAN, 11, 15), DP(BENCH, 17, 18), DP(SLED, 4, 21), DP(SKI_RACK, 10, 7),
    DP(WOODPILE, 2, 26), DP(STEAM, 31, 22), DP(STEAM, 27, 21), DP(FROZEN_TREE, 26, 18),
    DP(ICE_BLOCKS, 32, 16), DP(BARREL, 16, 8), DP(CRATE, 17, 7),
};
static const MapObj FROSTHOLLOW_OBJS[] = {
    OBJ(BERRY, 37, 26, 24),
};

/* WHITECROWN PEAK (32 x 40) */
static const char *const WHITECROWN_ROWS[] = {
    "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", /*  0 */
    "pppppppppppppppppppppppppppppppp", /*  1 */
    "PPRRRRRRRRRRRRRRRRRRRRRRRRRRRRPP", /*  2 */
    "ppRRRRRR..................RRRRpp", /*  3 */
    "PPRRRRRR..,,,.............RRRRPP", /*  4 */
    "ppRRRRRR..,,,.............RRRRpp", /*  5 */
    "PPRRRRRR..................RRRRPP", /*  6 */
    "ppCCCCCC.CCCCCCCCCCCCCCCCCCCCCpp", /*  7 */
    "PPcccccc.cccccccccccccccccccccPP", /*  8 */
    "ppRRRR...................RRRRRpp", /*  9 */
    "PPRRRRRRRRRRRRRRRRRRRRR==RRRRRPP", /* 10 */
    "ppCCCCCCCCCCCCCCCCCCCCC..CCCCCpp", /* 11 */
    "PPccccccccccccccccccccc..cccccPP", /* 12 */
    "pp.....................==.....pp", /* 13 */
    "PP.....................==.....PP", /* 14 */
    "pp.,,,,,,,.............==.,,,,pp", /* 15 */
    "PP.,,,,,,,.............==.,,,,PP", /* 16 */
    "pp.,,,,,,,..,,,,,,,,,..==.,,,,pp", /* 17 */
    "PP.,,,,,,,..,,,,,,,,,..==.,,,,PP", /* 18 */
    "pp.,,,,,,,..,,,,,,,,,..==.,,,,pp", /* 19 */
    "PP.,,,,,,,.............==.,,,,PP", /* 20 */
    "pp......=================.,,,,pp", /* 21 */
    "PP......=================.....PP", /* 22 */
    "ppCCCCCC==CCCCCCCCCCCCCCCCCCCCpp", /* 23 */
    "PPcccccc==ccccccccccccccccccccPP", /* 24 */
    "pp......==............[LLLL]..pp", /* 25 */
    "PP......==...........,,,PPPPP.PP", /* 26 */
    "pp......==...........,,,ppppp.pp", /* 27 */
    "PP......==...........,,,PPPPP.PP", /* 28 */
    "pp......==...........,,,ppppp.pp", /* 29 */
    "PP......=============.........PP", /* 30 */
    "pp......=============.........pp", /* 31 */
    "PP.................==.,,,,,,,.PP", /* 32 */
    "pp.,,,,,...PPPPPP..==.,,,,,,,.pp", /* 33 */
    "PP.,,,,,...pppppp..==.,,,,,,,.PP", /* 34 */
    "pp.,,,,,...PPPPPP..==.,,,,,,,.pp", /* 35 */
    "PP.,,,,,...pppppp..==.,,,,,,,.PP", /* 36 */
    "pp.................==.........pp", /* 37 */
    "PPPPPPPPPPPPPPPPPPP==PPPPPPPPPPP", /* 38 */
    "ppppppppppppppppppp==ppppppppppp", /* 39 */
};
static const DecorPlace WHITECROWN_DECOR[] = {
    DP(WOLF_STATUE, 14, 3), DP(WOLF_STATUE, 20, 3), DP(AURORA_STONE, 11, 3),
    DP(AURORA_STONE, 23, 3), DP(SIGNPOST, 21, 37), DP(SIGNPOST, 10, 29), DP(FROZEN_TREE, 5, 29),
    DP(ICE_CRYSTAL, 27, 18), DP(ICE_CRYSTAL, 16, 14), DP(ROCK, 14, 26), DP(SHRINE, 24, 3),
};
static const MapObj WHITECROWN_OBJS[] = {
    OBJ(BOULDER, 18, 9, 0), OBJ(LEGEND, 17, 4, SP_HOARFANG), OBJ(BERRY, 28, 33, 22), OBJ(BERRY, 3, 17, 23),
};

/* SKY ISLE (24 x 20) */
static const char *const SKY_ISLE_ROWS[] = {
    "KKKKKKKKKKKKKKKKKKKKKKKK", /*  0 */
    "KKKKKKKKKKKKKKKKKKKKKKKK", /*  1 */
    "KKKKKKKKKKKKKKKKKKKKKKKK", /*  2 */
    "KKKKKKKKKKKKKKKKKKKKKKKK", /*  3 */
    "KKKKKK............KKKKKK", /*  4 */
    "KKKK................KKKK", /*  5 */
    "KKK......######......KKK", /*  6 */
    "KKK......######......KKK", /*  7 */
    "KK.........==.........KK", /*  8 */
    "KK.........==.........KK", /*  9 */
    "KKK........==.........KK", /* 10 */
    "KKK........==........KKK", /* 11 */
    "KKKK.......==........KKK", /* 12 */
    "KKKK.......==.......KKKK", /* 13 */
    "KKKKK..............KKKKK", /* 14 */
    "KKKKKKK..........KKKKKKK", /* 15 */
    "KKKKKKKKKKKKKKKKKKKKKKKK", /* 16 */
    "KKKKKKKKKKKKKKKKKKKKKKKK", /* 17 */
    "KKKKKKKKKKKKKKKKKKKKKKKK", /* 18 */
    "KKKKKKKKKKKKKKKKKKKKKKKK", /* 19 */
};
static const DecorPlace SKY_ISLE_DECOR[] = {
    DP(SKY_ARCH, 10, 4), DP(AURORA_STONE, 5, 6), DP(AURORA_STONE, 18, 6), DP(ICE_CRYSTAL, 4, 11),
    DP(ICE_CRYSTAL, 18, 12), DP(ICE_CRYSTAL, 7, 13),
};
static const MapObj SKY_ISLE_OBJS[] = {
    OBJ(LEGEND, 11, 6, SP_SKYLORN),
};

/* RIME HALL (15 x 20) */
static const char *const RIME_HALL_ROWS[] = {
    "WWWWWWWWWWWWWWW", /*  0 */
    "wwwwwwwwwwwwwww", /*  1 */
    "FFFFFFFFFFFFFFF", /*  2 */
    "FFFFFFFFFFFFFFF", /*  3 */
    "oooooooooooooio", /*  4 */
    "ioiiiiiiiiiiiii", /*  5 */
    "iiiiiiiiiioiiii", /*  6 */
    "iiiiiiiiiiiiiii", /*  7 */
    "iiiFFiiiiiiiiii", /*  8 */
    "iiiiiiiiiiiiiio", /*  9 */
    "iiiiiiiiioiiiii", /* 10 */
    "iiiiiioiiiiiiii", /* 11 */
    "oiiiiiiiiiiiiii", /* 12 */
    "iiiiiiiiiiiFFii", /* 13 */
    "iiiiiiiiiiiiiii", /* 14 */
    "iiiiiiioiiiiiii", /* 15: the rock beside the way out */
    "ooooooioooooooo", /* 16 */
    "FFFFFFFFFFFFFFF", /* 17 */
    "FFFFFFFFFFFFFFF", /* 18 */
    "FFFFFFFDFFFFFFF", /* 19 */
};
static const DecorPlace RIME_HALL_DECOR[] = {
    DP(FROST_BANNER, 3, 0), DP(FROST_BANNER, 11, 0), DP(RIME_PILLAR, 1, 2), DP(RIME_PILLAR, 5, 2),
    DP(RIME_PILLAR, 9, 2), DP(ICE_STATUE, 0, 17), DP(ICE_STATUE, 14, 17), DP(RIME_PILLAR, 3, 18),
    DP(RIME_PILLAR, 11, 18),
};

/* HOT SPRING (13 x 10) */
static const char *const HOT_SPRING_ROWS[] = {
    "WWWWWWWWWWWWW", /*  0 */
    "wwwwwwwwwwwww", /*  1 */
    "#############", /*  2 */
    "#############", /*  3 */
    "#############", /*  4 */
    "#############", /*  5 */
    "#############", /*  6 */
    "#############", /*  7 */
    "#############", /*  8 */
    "######D######", /*  9 */
};
static const DecorPlace HOT_SPRING_DECOR[] = {
    DP(HOT_SPRING, 4, 2), DP(STEAM, 5, 2), DP(STEAM, 7, 3), DP(WASH_BUCKET, 1, 6),
    DP(WASH_BUCKET, 2, 6), DP(BENCH, 9, 7), DP(BARREL, 11, 2), DP(SKI_RACK, 0, 2),
};

/* GLIMMER CAVERNS (40 x 30) */
static const char *const GLIMMER_1_ROWS[] = {
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", /*  0 */
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", /*  1 */
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", /*  2 */
    "XXXXXccQccccQccXXXXXXXXXcccQcccccQccXXXX", /*  3 */
    "XXXXX.........*XXXXXXXXX............XXXX", /*  4 */
    "XXXXX.,,,,,,,..XXXXXXXXX..,,,,,,,,..XXXX", /*  5 */
    "XXXXX.,,,,,,,..XXXXXXXXX..,,,,,,,,..XXXX", /*  6 */
    "XXXXX.,,,,,,,..XXXXXXXXX............XXXX", /*  7 */
    "XXXXX..........XXXXXXXXX............XXXX", /*  8 */
    "XXXXX[LLLLLLL].XXXXXXXXX*...........XXXX", /*  9 */
    "XXXXX..........XXXXXXXXXXXXX~~~XXXXXXXXX", /* 10 */
    "XXXXX..........XXXXXXXXXXXXX~~~XXXXXXXXX", /* 11 */
    "XXXXXXXX...XXXXXXXXXXXXXXXXX~~~XXXXXXXXX", /* 12 */
    "XXXccQcc...cccccccccccQccccc~~~cccQccXXX", /* 13 */
    "XXX.................................*XXX", /* 14 */
    "XXX.,,,,,,.....,,,,,......~~~~~~~~~..XXX", /* 15 */
    "XXX.,,,,,,.....,,,,,......~~~~~~~~~..XXX", /* 16 */
    "XXX.,,,,,,.==========.....~~~~~~~~~..XXX", /* 17 */
    "XXX.,,,,,,.==========.....~~~~~~~~~..XXX", /* 18 */
    "XXX.,,,,,,................~~~~~~~~~..XXX", /* 19 */
    "XXX*.................................XXX", /* 20 */
    "XXXXXXXXXXXXXXXX...==..*XXXXXXXXXXXXXXXX", /* 21 */
    "XXXXXXXXXXXXXXXX...==...XXXXXXXXXXXXXXXX", /* 22 */
    "XXXXXXXXXXXXXXXX...==...XXXXXXXXXXXXXXXX", /* 23 */
    "XXXXXXXXXXXXXXXX...==...XXXXXXXXXXXXXXXX", /* 24 */
    "XXXXXXXXXXXXXXXX...==...XXXXXXXXXXXXXXXX", /* 25 */
    "XXXXXXXXXXXXXXXX...==...XXXXXXXXXXXXXXXX", /* 26 */
    "XXXXXXXXXXXXXXXX...==...XXXXXXXXXXXXXXXX", /* 27 */
    "XXXXXXXXXXXXXXXX*..==...XXXXXXXXXXXXXXXX", /* 28 */
    "XXXXXXXXXXXXXXXXXXXDDXXXXXXXXXXXXXXXXXXX", /* 29 */
};
static const Stamp GLIMMER_1_STAMPS[] = {
    STAMP(CV, STAIRS_DOWN, 9, 4),
};
static const DecorPlace GLIMMER_1_DECOR[] = {
    DP(CAVE_CRYSTAL, 17, 22), DP(AMETHYST, 22, 25), DP(STALAGMITE, 16, 24), DP(STALAGMITE, 11, 19),
    DP(GLOWCAP, 23, 27), DP(GLOWCAP, 3, 14), DP(MINE_CART, 35, 5), DP(ORE_ROCKS, 24, 4),
    DP(CRYSTAL_PILLAR, 13, 10), DP(BRIDGE_V, 29, 10), DP(BRIDGE_V, 29, 11), DP(BRIDGE_V, 29, 12),
    DP(BRIDGE_V, 29, 13), DP(SIGNPOST, 21, 21), DP(CRATE, 34, 8),
};

/* GLIMMER DEPTHS (36 x 28) */
static const char *const GLIMMER_2_ROWS[] = {
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", /*  0 */
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", /*  1 */
    "XXXccQccccQccXXXXXXXXXXXXXXXXXXXXXXX", /*  2 */
    "XXX.........*XXXXXXXXXXXXXccQccccXXX", /*  3 */
    "XXX..........ccQccccQccXXX.......XXX", /*  4 */
    "XXX....................XXX.......XXX", /*  5 */
    "XXX...........,,,,,,,,.XXX.......XXX", /*  6 */
    "XXX...........,,,,,,,,...........XXX", /*  7 */
    "XXX...........,,,,,,,,...........XXX", /*  8 */
    "XXX....................XXX.......XXX", /*  9 */
    "XXXX....*XXXX..........XXX.,,,,,.XXX", /* 10 */
    "XXXX.....XXXX..........XXX.,,,,,.XXX", /* 11 */
    "XXXX.....XXXX*.........XXX.,,,,,.XXX", /* 12 */
    "XXXX.....XXXXXXXXXXXXXXXXX.,,,,,.XXX", /* 13 */
    "XXXX.....XXXXXXXXXXXXXXXXX[LLLLL]XXX", /* 14 */
    "XXXX.....XXXXXXXXXXXXXXXXX.......XXX", /* 15 */
    "XXXX.....XXXXXXXXXXXXXXXXX.......XXX", /* 16 */
    "XXXX.....XXXXXXXXXXXXXXXXX.......XXX", /* 17 */
    "XXXX...........................XXXXX", /* 18 */
    "XXXX...............~~~~~~......XXXXX", /* 19 */
    "XXXX......,,,,,,,,.~~~~~~......XXXXX", /* 20 */
    "XXXX......,,,,,,,,.~~~~~~......XXXXX", /* 21 */
    "XXXX......,,,,,,,,.............XXXXX", /* 22 */
    "XXXXXXXXX.....................*XXXXX", /* 23 */
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", /* 24 */
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", /* 25 */
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", /* 26 */
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX", /* 27 */
};
static const Stamp GLIMMER_2_STAMPS[] = {
    STAMP(CV, STAIRS_UP, 7, 2), STAMP(CV, CRACK, 30, 3),
};
static const DecorPlace GLIMMER_2_DECOR[] = {
    DP(CAVE_CRYSTAL, 22, 5), DP(AMETHYST, 26, 5), DP(AMETHYST, 9, 23), DP(STALAGMITE, 4, 14),
    DP(STALAGMITE, 25, 22), DP(GLOWCAP, 7, 21), DP(GLOWCAP, 32, 7), DP(ORE_ROCKS, 13, 9),
    DP(CRYSTAL_PILLAR, 3, 7), DP(CRYSTAL_PILLAR, 32, 15),
};

/* STARFALL GROTTO (24 x 20) */
static const char *const STARFALL_ROWS[] = {
    "XXXXXXXXXXXXXXXXXXXXXXXX", /*  0 */
    "XXXXXXXXXXXXXXXXXXXXXXXX", /*  1 */
    "XXXccQcccccQccccccQccXXX", /*  2 */
    "XXX*................*XXX", /*  3 */
    "XXX..................XXX", /*  4 */
    "XXX..................XXX", /*  5 */
    "XX....................XX", /*  6 */
    "XX....................XX", /*  7 */
    "XX....................XX", /*  8 */
    "XX....788888888889....XX", /*  9 */
    "XX....455555555556....XX", /* 10 */
    "XX....455555555556....XX", /* 11 */
    "XX....455555555556....XX", /* 12 */
    "XX....455555555556....XX", /* 13 */
    "XX....122222222223....XX", /* 14 */
    "XXX..................XXX", /* 15 */
    "XXX..................XXX", /* 16 */
    "XXX*................*XXX", /* 17 */
    "XXXXXXXXXXX..XXXXXXXXXXX", /* 18 */
    "XXXXXXXXXXXDDXXXXXXXXXXX", /* 19 */
};
static const DecorPlace STARFALL_DECOR[] = {
    DP(MOTH_DAIS, 11, 4), DP(MOONBEAM, 9, 3), DP(MOONBEAM, 14, 3), DP(MOONBEAM, 11, 12),
    DP(CRYSTAL_PILLAR, 5, 5), DP(CRYSTAL_PILLAR, 18, 5), DP(CAVE_CRYSTAL, 4, 15),
    DP(CAVE_CRYSTAL, 19, 15), DP(GLOWCAP, 8, 16), DP(GLOWCAP, 16, 7),
};
static const MapObj STARFALL_OBJS[] = {
    OBJ(LEGEND, 11, 6, SP_SELENOTH),
};

/* FROST HEARTH HALL (11 x 9) */
static const char *const FROST_HEARTH_ROWS[] = {
    "WWnWWkWWnWW", /*  0 */
    "wwwwwwwwwww", /*  1 */
    ":::::::::::", /*  2 */
    ":::<===>:::", /*  3 */
    ":::::::::::", /*  4 */
    ":::::::::::", /*  5 */
    ":::::::::::", /*  6 */
    ":::::::::::", /*  7 */
    ":::::D:::::", /*  8 */
};
static const Stamp FROST_HEARTH_STAMPS[] = {
    STAMP(I, RUG, 4, 6),
};
static const DecorPlace FROST_HEARTH_DECOR[] = {
    DP(LANTERN_RACK, 3, 1), DP(HEAL_MACHINE, 6, 1), DP(PC, 10, 1), DP(PENNANT, 1, 0),
    DP(CALENDAR, 9, 0), DP(FIREPLACE, 0, 1), DP(TABLE_ROUND, 8, 5), DP(CHAIR, 8, 4),
    DP(KIN_BASKET, 0, 6), DP(SMALL_PLANT, 10, 7), DP(COAT_RACK, 10, 5),
};

/* FROST SHOP (11 x 9) */
static const char *const FROST_SHOP_ROWS[] = {
    "WWnWWkWWnWW", /*  0 */
    "wwwwwwwwwww", /*  1 */
    ":::::::::::", /*  2 */
    "<==>:::::::", /*  3 */
    ":::::::::::", /*  4 */
    ":::::::::::", /*  5 */
    ":::::::::::", /*  6 */
    ":::::::::::", /*  7 */
    ":::::D:::::", /*  8 */
};
static const DecorPlace FROST_SHOP_DECOR[] = {
    DP(BARREL_IN, 0, 2), DP(SACKS_IN, 3, 2), DP(PENNANT, 1, 0), DP(SHOP_SHELF, 5, 1),
    DP(SHOP_SHELF, 7, 1), DP(LANTERN_RACK, 9, 1), DP(ICEBOX, 10, 5), DP(BARREL_IN, 9, 6),
    DP(SMALL_RUG, 5, 7), DP(SMALL_PLANT, 0, 7),
};

/* THE ALDER HOUSE (11 x 9) */
static const char *const FROST_HOUSE_ROWS[] = {
    "WWnWWkWWnWW", /*  0 */
    "wwwwwwwwwww", /*  1 */
    "...........", /*  2 */
    "...........", /*  3 */
    "...........", /*  4 */
    "...........", /*  5 */
    "...........", /*  6 */
    "...........", /*  7 */
    ".....D.....", /*  8 */
};
static const Stamp FROST_HOUSE_STAMPS[] = {
    STAMP(I, RUG, 4, 5),
};
static const DecorPlace FROST_HOUSE_DECOR[] = {
    DP(FIREPLACE, 3, 1), DP(BOOKSHELF_SMALL, 0, 1), DP(DOUBLE_BED, 9, 2), DP(WARDROBE, 7, 1),
    DP(TABLE, 1, 4), DP(CHAIR_SIDE, 0, 4), DP(CHAIR_UP, 1, 6), DP(KIN_BASKET, 10, 5),
    DP(TOY_BOX, 9, 7), DP(TEA_SET, 3, 5), DP(CALENDAR, 6, 0),
};

/* STARGAZER'S HOUSE (11 x 9) */
static const char *const STARGAZER_ROWS[] = {
    "WWnWWpWWnWW", /*  0 */
    "wwwwwwwwwww", /*  1 */
    "...........", /*  2 */
    "...........", /*  3 */
    "...........", /*  4 */
    "...........", /*  5 */
    "...........", /*  6 */
    "...........", /*  7 */
    ".....D.....", /*  8 */
};
static const DecorPlace STARGAZER_DECOR[] = {
    DP(BOOKSHELF, 0, 1), DP(TELESCOPE_IN, 4, 1), DP(GLOBE, 5, 2), DP(MAP_POSTER, 7, 0),
    DP(DESK, 7, 2), DP(CHAIR_UP, 7, 3), DP(BED, 10, 2), DP(CHALKBOARD, 2, 0),
    DP(BOOKSHELF_SMALL, 10, 5), DP(STOOL, 3, 5), DP(FLOOR_LAMP, 0, 5), DP(SMALL_PLANT, 0, 7),
};

/* ---------------- wild kin (docs/EXPANSION.md 4: SNOW, PEAK, CAVE) ---------------- */

static const WildSlot WILD_FROSTPINE[] = {
    { SP_FLURRABBIT, 22, 18, 22 }, { SP_TUXFLAKE, 18, 18, 22 }, { SP_YAKLING, 16, 19, 23 },
    { SP_RAMBLET, 14, 18, 22 }, { SP_FROSTOAT, 10, 19, 23 }, { SP_GLACIBLOB, 6, 20, 24 },
    { SP_MOONHARE, 8, 21, 24, WHEN_NIGHT }, { SP_PUFFOWL, 8, 19, 22, WHEN_DAY },
};
static const WildSlot WILD_WHITECROWN[] = {
    { SP_CRAGHORN, 18, 27, 31 }, { SP_GLACIYAK, 14, 28, 32 }, { SP_EMPERICE, 12, 27, 31 },
    { SP_RAMBLET, 14, 26, 29 }, { SP_FLURRABBIT, 14, 26, 29 },
    { SP_MOONHARE, 12, 28, 31, WHEN_NIGHT }, { SP_TENGALE, 3, 30, 33, WHEN_DAY },
    { SP_WENDIGAUNT, 2, 30, 33, WHEN_NIGHT },
};
static const WildSlot WILD_GLIMMER[] = {
    { SP_DIGGET, 22, 23, 27 }, { SP_SQUEAKLE, 22, 23, 27 }, { SP_QUARTZLING, 18, 24, 27 },
    { SP_BLINKET, 14, 23, 26 }, { SP_GOLEMIT, 10, 24, 27 }, { SP_LURELING, 6, 24, 27 },
};
static const WildSlot WILD_GLIMMER_DEEP[] = {
    { SP_QUARTZLING, 20, 27, 30 }, { SP_SQUEAKLE, 18, 26, 29 }, { SP_NOCTAVE, 12, 28, 31 },
    { SP_DIGGET, 14, 26, 29 }, { SP_QUARTZPEDE, 8, 29, 32 }, { SP_BLINKET, 10, 27, 30 },
    { SP_METEORB, 3, 29, 32, WHEN_NIGHT },
};
static const WildSlot WILD_GLIMMER_LAKE[] = {
    { SP_LURELING, 40, 24, 28 }, { SP_BUBBLIN, 30, 23, 27 }, { SP_TUXFLAKE, 20, 24, 27 },
    { SP_ABYSSLURE, 5, 28, 31, WHEN_NIGHT },
};
