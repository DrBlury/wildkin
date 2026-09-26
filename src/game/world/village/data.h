/*
 * world/village/data.h -- map rows, stamps, decor, objects and wild slots.
 * Owner: core (the original Maple Village area).
 */

/* ================================================================ */
/*  MAPLE VILLAGE                                                   */
/* ================================================================ */

static const char *const TOWN_ROWS[] = {
    "TTTTTTTTTTTTTTTTTTT==~~TTTTTTTTTTTTTTTTT", /*  0 */
    "ttttttttttttttttttt==~~ttttttttttttttttt", /*  1 */
    "TTTT............TT.==~~T............T.TT", /*  2 */
    "tttt............tt.==~~t............t.tt", /*  3 */
    "TTTT...............==~~...............TT", /*  4 */
    "tttt...............==~~...............tt", /*  5 */
    "TTTT...............==~~...............TT", /*  6 */
    "tttt..=......=.....==~~.......=.......tt", /*  7 */
    "TTT...===========..==~~.......=.......TT", /*  8 */
    "ttt.......=.....=..==~~.============..tt", /*  9 */
    "..........=.....=..==~~.=.............TT", /* 10 */
    "TTrr......=..######==~~.=vccccccccv.yytt", /* 11 */
    "ttrr......=..######==~~.=vccccccccv.yyTT", /* 12 */
    "TT........=..######==~~.=vccccccccv...tt", /* 13 */
    "tt.yy.....=..######==~~.=vccccccccv...TT", /* 14 */
    "TT.yy.....=..######==~~.=vccccccccv...tt", /* 15 */
    "tt........=.....=..==~~.=.............TT", /* 16 */
    "=====================~~=================", /* 17 */
    "=====================~~=================", /* 18 */
    "TT.yy.....=........==~~......=.rr.....TT", /* 19 */
    "tt........=........==~~......=......yytt", /* 20 */
    "TT........=........==~~......=......yyTT", /* 21 */
    "tt........=........==~~......=........tt", /* 22 */
    "TT........=.....rr===~~......=........TT", /* 23 */
    "tt........=.....rr===~~......=........tt", /* 24 */
    "TT........=.......===~~......=...=....TT", /* 25 */
    "tt....===============~~...===========.tt", /* 26 */
    ".......=.......=...==~~.....==........TT", /* 27 */
    "~~~....=.......=...==~~.....=...........", /* 28 */
    "~~~~~..=.......=...==~~.....=.........TT", /* 29 */
    "~~~~~~.==============~~..,,,=,,,.TTTTTtt", /* 30 */
    "~~~~~~......yy.....==~~..,,,,,,,.tttttTT", /* 31 */
    "~~~~~.....rryy.rr..==~~..,,,,,,,.TT...tt", /* 32 */
    "~~~~...............==~~.........=tt...TT", /* 33 */
    "TTTTTTTTTTTTTTTTTTT==~~TTTTTTTTTTTTTTTTT", /* 34 */
    "ttttttttttttttttttt==~~ttttttttttttttttt", /* 35 */
};

/* heights (0-3), stairs (^ v < >) and ledges (_): docs/ELEVATION.md */
static const char *const TOWN_ELEV[] = {
    "2222111111111111111000011222222222222111", /*  0 */
    "2222111111111111111000011222222222222111", /*  1 */
    "2222111111111111111000011222222222222111", /*  2 */
    "2222111111111111111000011222222222222111", /*  3 */
    "2222111111111111111000011222222222222111", /*  4 */
    "2222111111111111111000011222222222222111", /*  5 */
    "2222111111111111111000011222222222222111", /*  6 */
    "2222111111111111111000011222222222222111", /*  7 */
    "222111111111111111100001111111^111111111", /*  8 */
    "2221111111111111111000011111111111111111", /*  9 */
    "1111111111111111111000011111111111111111", /* 10 */
    "1111111111111111111<00011111111111111111", /* 11 */
    "1111111111111111111000011111111111111111", /* 12 */
    "1111111111111111111000011111111111111111", /* 13 */
    "1111111111111111111000011111111111111111", /* 14 */
    "1111111111111111111000011111111111111111", /* 15 */
    "1111111111111111111000011111111111111111", /* 16 */
    "1111111111111111111000011111111111111111", /* 17 */
    "1111111111111111111000011111111111111111", /* 18 */
    "1111111111111111111000011111111111111111", /* 19 */
    "1111111111111111111000011111111111111111", /* 20 */
    "1111111111111111111000011111111111111111", /* 21 */
    "1111111111111111111000011111111111111111", /* 22 */
    "1111111111111111111<00011111111111111111", /* 23 */
    "1111111111111111111000011111111111111111", /* 24 */
    "1111111111111111111000011111111111111111", /* 25 */
    "1111111111111111111000011111111111111111", /* 26 */
    "0000000^0011111111100001111111111111__11", /* 27 */
    "000000000000000^000000000000^00000000000", /* 28 */
    "0000000000000000000000000000000000000000", /* 29 */
    "0000000000000000000000000000000000000000", /* 30 */
    "0000000000000000000000000000000000000000", /* 31 */
    "0000000000000000000000000000000000000000", /* 32 */
    "0000000000000000000000000000000000000000", /* 33 */
    "0000000000000000000000000000000000000000", /* 34 */
    "0000000000000000000000000000000000000000", /* 35 */
};

static const ElevFeat TOWN_FEATS[] = {
    EF(BRIDGE_H, 19, 17, 4, 2),  /* the Maple Run bridge: the road over, the lane under */
    EF(HIDDEN, 33, 33, 2, 1),  /* a gap in the thicket to the SUNSEED */
};

static const char *const MEADOW_ROWS[] = {
    "TTTTTTTTTTT==TTTTTTTTTTTTTTTTTTTTTTTTTTT", /*  0 */
    "ttttttttttt==ttttttttttttttttttttttttttt", /*  1 */
    "TT.........==..,,,,,,.....TTTT........TT", /*  2 */
    "tt.,,,,,,,.==..,,,,,,.....tttt..yyyy..tt", /*  3 */
    "TT.,,,,,,,.==..,,,,,,.....TTTT..yyyy..TT", /*  4 */
    "tt.,,,,,,,.==..,,,,,,.....tttt..yyyy..tt", /*  5 */
    "TT.,,,,,,,.==.........................TT", /*  6 */
    "tt.,,,,,,,.==============.............tt", /*  7 */
    "TT.,,,,,,,.==============.............TT", /*  8 */
    "tt.,,,,,,,.............==.............tt", /*  9 */
    "TT.,,,,,,,.............==..,,,,,,,,,,.TT", /* 10 */
    "tt.....mmmmm....rrrr...==..,,,www,,,,.tt", /* 11 */
    "TTTTTT..mmmmm...rrrr...==..,,wwwwww,,.TT", /* 12 */
    "tttttt.rrr......rrrr...==..,wwwwwww,,.tt", /* 13 */
    "TTTTTT.rrr.............==..,,wwwww,,,.TT", /* 14 */
    "tttttt.rrr.............==dd,,,ww,,,,,.tt", /* 15 */
    "TT.....................==dd,,,,,,,,,,.TT", /* 16 */
    "tt............===========..,,,,,,,,,,.tt", /* 17 */
    "TT............===========..,,,,,,,,,,.TT", /* 18 */
    "tt.,,,,,,,,,..==...........,,,,,,,,,,.tt", /* 19 */
    "TT.,,,,,,,,,..==..............TTTTTTT.TT", /* 20 */
    "tt.,,,,,,,,,..==..............ttttttt.tt", /* 21 */
    "TT.,,,,,,,,,..==.mmmmm................TT", /* 22 */
    "tt.,,,,,,,,,..==.mmmmmm...............tt", /* 23 */
    "TT.,,,,,,,,,..==[LLLL]==[LLLLLLLLLL]..TT", /* 24 */
    "tt.,,,,,,,,,..==......................tt", /* 25 */
    "TT.,,,,,,,,,..==.............sssssss..TT", /* 26 */
    "tt............==.............s~~~~~s..tt", /* 27 */
    "TT............==.............s~~~~~s..TT", /* 28 */
    "tt..yyyy......=======........sssssss..tt", /* 29 */
    "TT..yyyy......=======..mmmmmm.........TT", /* 30 */
    "tt.................==.mmmmmm..........tt", /* 31 */
    "TT.,,,,,,,,,,......==...,,,,,,,,,,,,..TT", /* 32 */
    "tt.,,,,,,,,,,......==...,,,,,,,,,,,,..tt", /* 33 */
    "TT.,,,,,,,,,,......==...,,,,,,,,,,,,..TT", /* 34 */
    "tt.,,,,,,,,,,......==...,,,,,,,,,,,,..tt", /* 35 */
    "TT.,,,,,,,,,,......==...,,,,,,,,,,,,..TT", /* 36 */
    "tt.,,,,,,,,,,......==...,,,,,,,,,,,,..tt", /* 37 */
    "TT.,,,,,,,,,,......==...,,,,,,,,,,,,..TT", /* 38 */
    "tt.,,,,,,,,,,......==.................tt", /* 39 */
    "TT.................==.....rrrr........TT", /* 40 */
    "tt.................==.....rrrr........tt", /* 41 */
    "TTTTTTTTTTTTTTTTTTT==TTTTTTTTTTTTTTTTTTT", /* 42 */
    "ttttttttttttttttttt==ttttttttttttttttttt", /* 43 */
};

static const char *const RISE_ROWS[] = {
    "PPPPPPPPPPP==PPPPPPPPPPP", /*  0 */
    "ppppppppppp==ppppppppppp", /*  1 */
    "PP.........==.........PP", /*  2 */
    "pp.,,,.##########.,,,.pp", /*  3 */
    "PP.,,,.#........#.,,,.PP", /*  4 */
    "pp.,,,.#..####..#.,,,.pp", /*  5 */
    "PP.,,,.#..####..#.,,,.PP", /*  6 */
    "pp.,,,.#..####..#.,,,.pp", /*  7 */
    "PP.,,,.#..####..#.,,,.PP", /*  8 */
    "ppPPPP.#..####..#.PPPPpp", /*  9 */
    "PPpppp.#........#.ppppPP", /* 10 */
    "pp.....##########.....pp", /* 11 */
    "PP.,,,,,,..==..,,,,,,.PP", /* 12 */
    "pp.,,,,,,..==..,,,,,,.pp", /* 13 */
    "PP.,,,,,,..==..,,,,,,.PP", /* 14 */
    "pp.,,,,,,..==..,,,,,,.pp", /* 15 */
    "PP.,,,,,,..==..,,,,,,.PP", /* 16 */
    "pp.........==.........pp", /* 17 */
    "PPPPPPPPPPP==PPPPPPPPPPP", /* 18 */
    "ppppppppppp==ppppppppppp", /* 19 */
};

static const char *const WOOD_ROWS[] = {
    "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", /*  0 */
    "pppppppppppppppppppppppppppppppppppppppppppp", /*  1 */
    "PPffffffffff,,,,,,,,,f~~ffffffffffffffffffPP", /*  2 */
    "ppfPPPPPffff,,,,,,,,,f~~fPPPPffffPPPPPPPPfpp", /*  3 */
    "PPfpppppffff,,,,,,,,,f~~fppppffffppppppppfPP", /*  4 */
    "ppfPPPPPffff,,,,,,,,,f~~fffffffff.XXXXX..fpp", /*  5 */
    "PPfpppppffffffffffffff~~fffffffff.XXXXX..fPP", /*  6 */
    "ppfffffff=============~~=======ff.XXXXX..fpp", /*  7 */
    "PPfffffff=============~~=======ff.XXXXX..fPP", /*  8 */
    "ppf,,,,,,==fffffffffff~~fffff========....fpp", /*  9 */
    "PPf,,,,,,==fffffffffff~~f,,,,========....fPP", /* 10 */
    "ppf,,,,,,==fPPPPPPPPff~~f,,,,==fPPPPPPPPffpp", /* 11 */
    "PPf,,,,,,==fppppppppff~~f,,,,==fppppppppffPP", /* 12 */
    "ppf,,,,,,==fPPPPPPPPff~~f,,,,==fPPPPPPPPffpp", /* 13 */
    "PPf,,,,,,==fppppppppff~~f,,,,==fppppppppffPP", /* 14 */
    "ppf,,,,,,==f,,,,,,,,,f~~f,,,,==fffffffffffpp", /* 15 */
    "PPf,,,,,,==f,,,,,,,,,f~~f,,,,==,,,,,,,,,,fPP", /* 16 */
    "===========f,,,,,,,,,f~~f,,,,===============", /* 17 */
    "===========fdddddd,,,f~~f,,,,===============", /* 18 */
    "ppffffffffffdddddd,,,f~~f,,,,==,,,,,,,,,,fpp", /* 19 */
    "PPffffffffff,dddd,,,,f~~f,,,,==,,,,,,,,,,fPP", /* 20 */
    "ppfPPPPPPPPP,,,,,,,,,f~~fffff==,,,,,,,,,,fpp", /* 21 */
    "PPfppppppppppfffffffff~~fffff==,,,,,,,,,,fPP", /* 22 */
    "ppfPPPPPPPPPPfff======~~=======fffffffffffpp", /* 23 */
    "PPfppppppppppfff======~~=======fffffffffffPP", /* 24 */
    "ppfPPPPPPPPPPfff==ffff~~f,,,,,,,,,,,,,,,,fpp", /* 25 */
    "PPfppppppppppfff==ffff~~f,,,,,,,,,,,,,,,,fPP", /* 26 */
    "ppffffffffffffff==ffff~~f,,,,,,,,,,,,,,,,fpp", /* 27 */
    "PPffffffffffffff==ffff~~ffffffffffffffffffPP", /* 28 */
    "ppfPPPPPPPPPPfff======~~=============fffffpp", /* 29 */
    "PPfppppppppppfff======~~=============fffffPP", /* 30 */
    "ppfPPPPPPPPPPfffffffff~~ffffff==,,,,,,,,,fpp", /* 31 */
    "PPfppppppppppfffffffff~~ffffff==,,,,,,,,,fPP", /* 32 */
    "ppffffffffffffffffffff~~ffffff==,,,,,,,,,fpp", /* 33 */
    "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPP==PPPPPPPPPPPP", /* 34 */
    "pppppppppppppppppppppppppppppp==pppppppppppp", /* 35 */
};

static const char *const LAKE_ROWS[] = {
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT", /*  0 */
    "tttttttttttttttttttttttttttttttttttttttt", /*  1 */
    "TT......TTTTTTTTTTTTTT................TT", /*  2 */
    "tt......tttttttttttttt.....XXXXX.rrrr.tt", /*  3 */
    "TT......TTTTTTTTTTTTTT.....XXXXX.rrrr.TT", /*  4 */
    "tt......tttttttttttttt.....XXXXX.rrrr.tt", /*  5 */
    "TT.........................XXXXX.rrrr.TT", /*  6 */
    "tt..sssssssssssssssssss.=======.......tt", /*  7 */
    "TT..sssssssssssssssssss.=======.......TT", /*  8 */
    "tt.ssss~~~~~~~~~~~~~ssss==............tt", /*  9 */
    "TT.sss~~~~~~~~~~~~~~~sss==.,,,,,,,,,,.TT", /* 10 */
    "tt.ss~~~~~~~~~~~~~~~~~ss==.,,,,,,,,,,.tt", /* 11 */
    "TT.RR~~~~~~~~~~~~~~~~~ss==.,,,,,,,,,,.TT", /* 12 */
    "tt.RR~~~~~~~~~~~~~~~~~ss==.,,,,,,,,,,.tt", /* 13 */
    "TT.RR~~~~~~~~~~~~~~~~~ss==.,,,,,,,,,,.TT", /* 14 */
    "tt.RR~~~~~~~~~~~~~~~~~ss==.,,,,,,,,,,.tt", /* 15 */
    "TT.RR~~~~~~~~~~~~~~~~~ss==............TT", /* 16 */
    "tt.RR~~~~~~~~~~~~~~~~~ss================", /* 17 */
    "TT.RR~~~~~~~~~~~~~~~~~ss================", /* 18 */
    "tt.RR~~~~~~~~~~~~~~~~~ss==.TTTTTTTTTT.tt", /* 19 */
    "TT.RR~~~~~~~~~~~~~~~~~RR==............TT", /* 20 */
    "tt.RR~~~~~~~~~~~~~~~~~RR==..,,,,,,,,,.tt", /* 21 */
    "TT.RR~~~~~~~~~~~~~~~~~RR==..,,,,,,,,,.TT", /* 22 */
    "tt.RR~~~~~~~~~~~~~~~~~RR==..,,,,,,,,,.tt", /* 23 */
    "TT.RR~~~~~~~~~~~~~~~~~RR==..,,,,,,,,,.TT", /* 24 */
    "tt.RR~~~~~~~~~~~~~~~~~RR==..,,,,,,,,,.tt", /* 25 */
    "TT.ss~~~~~~~~~~~~~~~~~RR==..,,,,,,,,,.TT", /* 26 */
    "tt.sss~~~~~~~~~~~~~~~sss==..,,,,,,,,,.tt", /* 27 */
    "TT.ssss~~~~~~~~~~~~~ssss==..,,,,,,,,,.TT", /* 28 */
    "tt...sssssRRRRRRRRRsss..==..,,,,,,,,,.tt", /* 29 */
    "TT...sssssRRRRRRRRRsss..==............TT", /* 30 */
    "==========================.....yyyyyy.tt", /* 31 */
    "==========================.....yyyyyy.TT", /* 32 */
    "tt.............................yyyyyy.tt", /* 33 */
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT", /* 34 */
    "tttttttttttttttttttttttttttttttttttttttt", /* 35 */
};

static const Stamp TOWN_STAMPS[] = {
    STAMP(T, HOUSE_RED, 4, 3),    /* home */
    STAMP(T, HOUSE_BLUE, 11, 3),  /* bakery */
    STAMP(T, LAB, 27, 2),         /* almanac house, up on the knoll */
    STAMP(T, HEAL, 4, 22),        /* hearth hall */
    STAMP(T, SHOP, 11, 22),       /* shop */
    STAMP(T, HOUSE_BLUE, 31, 21), /* garden house */
    STAMP(T, COURT_CIRCLE, 29, 12),
    STAMP(T, HOUSE_RED, 24, 22),  /* LAND OFFICE (W-EAST: world/east/warps.inc) */
};

static const DecorPlace TOWN_DECOR[] = {
    /* the plaza and the Old Hearth */
    DP(OLD_HEARTH, 15, 12), DP(BENCH, 13, 15), DP(BENCH, 17, 11),
    DP(STONE_LANTERN, 12, 11), DP(STONE_LANTERN, 18, 15),
    /* market */
    DP(MARKET_STALL, 6, 10), DP(BARREL, 9, 10), DP(CRATE, 9, 11), DP(SACKS, 5, 11),
    /* homes */
    DP(MAILBOX, 4, 7), DP(FLOWER_POT, 5, 7), DP(FLOWER_POT, 16, 6), DP(PLANTER, 26, 7),
    DP(PLANTER, 33, 7), DP(WELL, 2, 22), DP(FLOWER_POT, 9, 25), DP(FLOWER_POT, 3, 25),
    /* signs */
    DP(SIGNPOST, 16, 7), DP(SIGNPOST, 28, 7), DP(SIGNPOST, 17, 19), DP(SIGNPOST, 18, 2),
    DP(SIGNPOST, 2, 16), DP(SIGNPOST, 37, 16), DP(SIGNPOST, 8, 26), DP(SIGNPOST, 16, 25),
    DP(SIGNPOST, 23, 16),
    /* lights */
    DP(LAMP, 9, 15), DP(LAMP, 23, 14), DP(LAMP, 15, 19), DP(LAMP, 30, 19),
    DP(LANTERN_POST, 23, 11), DP(LANTERN_POST, 35, 11), DP(FLAG, 35, 13),
    /* the bout ring fence */
    DP(FENCE, 25, 16), DP(FENCE, 26, 16), DP(FENCE, 27, 16), DP(FENCE, 28, 16),
    DP(FENCE, 29, 16), DP(FENCE, 30, 16), DP(FENCE, 31, 16), DP(FENCE, 32, 16),
    DP(FENCE, 33, 16), DP(FENCE_END, 34, 16),
    /* the farm corner, down in the south-east field */
    DP(HAY_BALE, 37, 24), DP(HAY_BALE, 36, 23), DP(WATER_TROUGH, 24, 29), DP(WOODPILE, 30, 29),
    DP(HAY_BALE, 32, 29),
    /* green bits */
    DP(BIG_TREE, 17, 31), DP(BUSH, 4, 10), DP(BUSH, 2, 20), DP(BUSH, 37, 23), DP(BUSH, 9, 20),
    DP(BUSH, 17, 27), DP(BENCH, 5, 28),
    DP(LILY_PADS, 2, 30), DP(LILY_PADS, 3, 32), DP(ROCK, 24, 32), DP(ROCK, 11, 27),
    DP(SMALL_FLOWERS, 23, 6), DP(SMALL_FLOWERS, 34, 4), DP(SMALL_FLOWERS, 9, 16),
    DP(PEBBLES, 28, 24), DP(SMALL_FLOWERS, 31, 20), DP(PEBBLES, 31, 33),
};

/* ================================================================ */
/*  Routes                                                          */
/* ================================================================ */

static const DecorPlace MEADOW_DECOR[] = {
    DP(SIGNPOST, 21, 40), DP(SIGNPOST, 13, 2),
    /* the shepherd's fold */
    DP(FENCE, 3, 27), DP(FENCE, 4, 27), DP(FENCE, 5, 27), DP(FENCE, 6, 27), DP(FENCE_END, 7, 27),
    DP(WATER_TROUGH, 9, 28), DP(HAY_BALE, 11, 28), DP(HAY_BALE, 12, 29),
    /* warden camp */
    DP(TENT, 25, 13), DP(CAMPFIRE, 26, 15), DP(LOG, 25, 16),
    /* old stones and trees */
    DP(STANDING_STONE, 32, 7), DP(STANDING_STONE, 36, 9), DP(BIG_TREE, 16, 20),
    DP(BIG_TREE, 7, 16), DP(STUMP, 21, 21), DP(LOG, 30, 31),
    DP(ROCK, 12, 21), DP(ROCK, 25, 30), DP(ROCK, 5, 17), DP(ROCK, 20, 26),
    DP(BUSH, 9, 18), DP(BUSH, 22, 36), DP(BUSH, 26, 7), DP(BUSH, 35, 40),
    DP(BENCH, 29, 25), DP(BERRY_BUSH, 36, 30), DP(BERRY_BUSH, 3, 30),
    DP(SMALL_FLOWERS, 17, 26), DP(SMALL_FLOWERS, 24, 20), DP(SMALL_FLOWERS, 6, 41),
    DP(SMALL_FLOWERS, 34, 16), DP(PEBBLES, 21, 33), DP(PEBBLES, 13, 9),
};

static const DecorPlace RISE_DECOR[] = {
    DP(STORMSTONE, 11, 5),                  /* the Stormstone (story, see script.c) */
    DP(STANDING_STONE, 8, 4), DP(STANDING_STONE, 15, 4), DP(STANDING_STONE, 8, 8),
    DP(STANDING_STONE, 15, 8), DP(CRYSTAL_CLUSTER, 10, 9), DP(CRYSTAL_CLUSTER, 13, 4),
    DP(ROCK, 4, 11), DP(ROCK, 19, 11), DP(BOULDER, 17, 2), DP(PEBBLES, 9, 6),
    DP(SIGNPOST, 13, 17), DP(FLAG, 3, 16),
};
#define STORMSTONE_X 11   /* a base cell of the Stormstone decor */
#define STORMSTONE_Y 7

static const Stamp WOOD_STAMPS[] = { STAMP(W, CABIN, 34, 5) };
static const DecorPlace WOOD_DECOR[] = {
    DP(SIGNPOST, 2, 16), DP(SIGNPOST, 33, 10),
    /* bridges over the creek */
    DP(BRIDGE_H, 22, 7), DP(BRIDGE_H, 23, 7), DP(BRIDGE_H, 22, 8), DP(BRIDGE_H, 23, 8),
    DP(BRIDGE_H, 22, 23), DP(BRIDGE_H, 23, 23), DP(BRIDGE_H, 22, 24), DP(BRIDGE_H, 23, 24),
    DP(BRIDGE_H, 22, 29), DP(BRIDGE_H, 23, 29), DP(BRIDGE_H, 22, 30), DP(BRIDGE_H, 23, 30),
    /* the woodward's camp */
    DP(TENT, 13, 18), DP(CAMPFIRE, 16, 19), DP(WOODPILE, 5, 19), DP(STUMP, 7, 20),
    /* the hermit's clearing */
    DP(WOODPILE, 39, 9), DP(BARREL, 33, 6), DP(LANTERN_POST, 38, 9),
    /* forest floor */
    DP(LOG, 19, 9), DP(LOG, 34, 24), DP(STUMP, 25, 21), DP(STUMP, 5, 7),
    DP(MUSHROOMS, 11, 16), DP(MUSHROOMS, 20, 26), DP(MUSHROOMS, 38, 28), DP(MUSHROOMS, 4, 28),
    DP(MUSHROOMS, 27, 9), DP(BERRY_BUSH, 13, 22), DP(BERRY_BUSH, 40, 15), DP(BERRY_BUSH, 3, 27),
    DP(FALLEN_LEAVES, 12, 7), DP(FALLEN_LEAVES, 26, 23), DP(FALLEN_LEAVES, 34, 30),
    DP(FALLEN_LEAVES, 18, 16), DP(ROCK, 38, 24), DP(BOULDER, 36, 19),
};

static const Stamp LAKE_STAMPS[] = { STAMP(W, STATION, 27, 3) };
static const DecorPlace LAKE_DECOR[] = {
    DP(SIGNPOST, 36, 16), DP(SIGNPOST, 28, 7),
    /* the fishing dock */
    DP(DOCK, 21, 16), DP(DOCK, 20, 16), DP(DOCK, 19, 16), DP(DOCK_EDGE, 18, 16),
    DP(DOCK, 21, 17), DP(DOCK, 20, 17), DP(DOCK, 19, 17), DP(DOCK_EDGE, 18, 17),
    DP(DOCK_POST, 17, 15), DP(DOCK_POST, 17, 18), DP(ROWBOAT, 14, 20),
    DP(CRATE, 23, 15), DP(BARREL, 23, 18),
    /* around the station */
    DP(BENCH, 33, 7), DP(CRATE_STACK, 26, 5), DP(BARREL, 32, 6), DP(WEATHER_VANE, 34, 3),
    /* lakeshore */
    DP(LILY_PADS, 9, 13), DP(LILY_PADS, 12, 22), DP(LILY_PADS, 16, 11), DP(LILY_PADS, 7, 24),
    DP(ROCK, 3, 5), DP(ROCK, 37, 21), DP(ROCK, 4, 32), DP(BOULDER, 34, 32),
    DP(BUSH, 22, 6), DP(BUSH, 37, 8), DP(BUSH, 26, 16), DP(STUMP, 29, 33),
    DP(SMALL_FLOWERS, 26, 20), DP(PEBBLES, 23, 30), DP(CAMPFIRE, 4, 30),
};

/* ================================================================ */
/*  Interiors                                                       */
/* ================================================================ */

static const char *const HOME_ROWS[] = {
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
static const Stamp HOME_STAMPS[] = { STAMP(I, RUG, 4, 6) };
static const DecorPlace HOME_DECOR[] = {
    /* living corner: books, the fire, a table for three */
    DP(BOOKSHELF, 0, 1), DP(FIREPLACE, 3, 1), DP(TV, 5, 2), DP(KIN_PLUSH, 6, 2), DP(CALENDAR, 6, 0),
    DP(TABLE, 1, 4), DP(CHAIR_SIDE, 0, 4), DPF(CHAIR_SIDE, 3, 4), DP(CHAIR_UP, 1, 6), DP(CHAIR_UP, 2, 6),
    DP(CUSHION, 5, 4), DP(PLANT, 0, 6), DP(COAT_RACK, 3, 6),
    /* your corner: shelf terminal, wardrobe, bed and a basket for your kin */
    DP(PC, 7, 1), DP(WARDROBE, 8, 1), DP(PENNANT, 9, 0), DP(DRESSER, 9, 2), DP(BED, 10, 2),
    DP(KIN_BASKET, 10, 4), DP(FLOOR_LAMP, 9, 5), DP(TOY_BOX, 8, 7), DP(SMALL_PLANT, 10, 7),
};

static const char *const BAKERY_ROWS[] = {
    "WWnWWpWWnWW",
    "wwwwwwwwwww",
    "...........",
    "...........",
    "...........",
    "...........",
    "...........",
    "...........",
    ".....D.....",
};
static const DecorPlace BAKERY_DECOR[] = {
    /* the kitchen wall */
    DP(BRICK_OVEN, 0, 1), DP(STOVE, 2, 1), DP(ICEBOX, 3, 1), DP(SACKS_IN, 4, 2), DP(CALENDAR, 4, 0),
    DP(BREAD_DISPLAY, 7, 1), DP(BARREL_IN, 9, 2), DP(SACKS_IN, 10, 2),
    /* tables for customers */
    DP(TABLE_ROUND, 1, 4), DP(STOOL, 0, 5), DP(STOOL, 3, 5),
    DP(LONG_TABLE, 8, 4), DP(STOOL, 8, 6), DP(STOOL, 10, 6),
    DP(PLANT, 0, 6), DP(SMALL_PLANT, 10, 7), DP(SMALL_RUG, 5, 7),
};

static const char *const LAB_ROWS[] = {
    "WWnWWkWWWnWWW",
    "wwwwwwwwwwwww",
    ":::::::::::::",
    ":::::::::::::",
    ":::::::::::::",
    ":::::::::::::",
    ":::::::::::::",
    ":::::::::::::",
    ":::::::::::::",
    "::::::D::::::",
};
static const DecorPlace LAB_DECOR[] = {
    /* research wall */
    DP(LAB_MACHINE, 0, 1), DP(SPECIMEN_SHELF, 2, 1), DP(BOOKSHELF_SMALL, 3, 1), DP(CHALKBOARD, 3, 0),
    DP(GLOBE, 5, 2), DP(PC, 6, 1), DP(BOOKSHELF, 7, 1), DP(TELESCOPE_IN, 9, 1),
    DP(BOOKSHELF, 10, 1), DP(MAP_POSTER, 10, 0), DP(GRANDFATHER_CLOCK, 12, 1),
    /* the floor */
    DP(AQUARIUM, 0, 4), DP(DESK, 9, 5), DP(CHAIR_UP, 9, 6), DP(MICROSCOPE, 11, 5),
    DP(DISPLAY_CASE, 2, 7), DP(PLANT, 0, 7), DP(PLANT, 12, 7), DP(SMALL_RUG, 5, 8),
};

static const char *const SHOP_ROWS[] = {
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
static const DecorPlace SHOP_DECOR[] = {
    DP(BARREL_IN, 0, 2), DP(SACKS_IN, 3, 2), DP(PENNANT, 1, 0), DP(CALENDAR, 3, 0),
    DP(SHOP_SHELF, 5, 1), DP(SHOP_SHELF, 7, 1), DP(LANTERN_RACK, 9, 1),
    DP(DISPLAY_CASE, 6, 5), DP(BARREL_IN, 9, 5), DP(SACKS_IN, 10, 5),
    DP(PLANT, 10, 6), DP(SMALL_PLANT, 0, 7), DP(SMALL_RUG, 5, 7),
};

static const char *const REST_ROWS[] = {
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
static const Stamp REST_STAMPS[] = { STAMP(I, RUG, 4, 6) };
static const DecorPlace REST_DECOR[] = {
    /* behind the counter: lanterns resting and the hearth resonator */
    DP(PLANT, 0, 1), DP(LANTERN_RACK, 3, 1), DP(HEAL_MACHINE, 7, 1), DP(FLOOR_LAMP, 9, 1), DP(PC, 10, 1),
    DP(PENNANT, 1, 0), DP(CALENDAR, 9, 0),
    /* the waiting room */
    DP(TABLE_ROUND, 1, 5), DP(CHAIR, 1, 4), DP(CHAIR, 2, 4), DP(TEA_SET, 0, 6),
    DP(AQUARIUM, 9, 4), DP(KIN_BASKET, 8, 6), DP(KIN_BASKET, 10, 6), DP(SMALL_PLANT, 10, 7),
};

static const char *const GARDEN_ROWS[] = {
    "WWnWWpWWnWW",
    "wwwwwwwwwww",
    "...........",
    "...........",
    "...........",
    "...........",
    "...........",
    "...........",
    ".....D.....",
};
static const DecorPlace GARDEN_DECOR[] = {
    DP(BOOKSHELF, 0, 1), DP(PLANT, 2, 1), DP(SMALL_PLANT, 3, 2), DP(CACTUS, 4, 2), DP(FLOWER_VASE, 6, 2),
    DP(CALENDAR, 7, 0), DP(DRESSER, 9, 2), DP(BED, 10, 2),
    DP(TABLE, 4, 4), DP(CHAIR, 4, 3), DP(CHAIR, 5, 3), DP(CHAIR_UP, 4, 6),
    DP(PLANT, 0, 6), DP(PLANT, 10, 6), DP(SMALL_PLANT, 1, 7), DP(CACTUS, 9, 7), DP(SMALL_RUG, 5, 7),
};

static const char *const CABIN_ROWS[] = {
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
static const DecorPlace CABIN_DECOR[] = {
    DP(BOOKSHELF, 0, 1), DP(FIREPLACE, 3, 1), DP(BOOKSHELF_SMALL, 6, 1), DP(MAP_POSTER, 6, 0),
    DP(TELESCOPE_IN, 8, 1), DP(BED, 10, 2),
    DP(TABLE, 5, 4), DP(CHAIR, 5, 3), DP(CHAIR, 6, 3),
    DP(PLANT, 0, 6), DP(SACKS_IN, 1, 7), DP(KIN_BASKET, 9, 6), DP(COAT_RACK, 10, 6),
};

static const char *const STATION_ROWS[] = {
    "WWnWWkWWWnWWW",
    "wwwwwwwwwwwww",
    ":::::::::::::",
    ":::::::::::::",
    ":::::::::::::",
    ":::::::::::::",
    ":::::::::::::",
    ":::::::::::::",
    "::::::D::::::",
};
static const DecorPlace STATION_DECOR[] = {
    /* instruments along the wall */
    DP(LAB_MACHINE, 0, 1), DP(SPECIMEN_SHELF, 2, 1), DP(AQUARIUM, 3, 2), DP(CHALKBOARD, 3, 0),
    DP(TELEGRAPH, 6, 2), DP(MAP_POSTER, 7, 0), DP(TELESCOPE_IN, 9, 1), DP(BOOKSHELF, 10, 1),
    DP(PC, 12, 1),
    /* a cot and a workbench */
    DP(BED, 0, 3), DP(DESK, 1, 5), DP(CHAIR_UP, 1, 6), DP(MICROSCOPE, 3, 5),
    DP(DISPLAY_CASE, 9, 5), DP(GLOBE, 11, 5),
    DP(PLANT, 12, 6), DP(SMALL_PLANT, 0, 7), DP(SMALL_RUG, 6, 7),
};


/* Wild kin (visible in tall grass and reeds) */
static const WildSlot WILD_MEADOW[] = {
    { SP_NIBBIT, 24, 2, 5 }, { SP_PUFFOWL, 20, 3, 6 }, { SP_ZAPPET, 14, 3, 7 },
    { SP_SKYWISP, 12, 4, 7 }, { SP_THORNIP, 10, 3, 6 }, { SP_DANDELAMB, 6, 3, 5 },
    { SP_VOLTUX, 8, 5, 9 },
};
static const WildSlot WILD_WOOD[] = {
    { SP_THORNIP, 18, 4, 8 }, { SP_MOSSHELL, 16, 5, 9 }, { SP_NIBBIT, 12, 4, 7 },
    { SP_SKYWISP, 12, 5, 9 }, { SP_CINDERUB, 10, 6, 10 }, { SP_GOLEMIT, 8, 6, 9 },
    { SP_WISPIRE, 6, 7, 11 }, { SP_FLARIX, 5, 5, 8 },
};
static const WildSlot WILD_LAKE[] = {
    { SP_BUBBLIN, 20, 5, 9 }, { SP_AQUAPO, 12, 5, 8 }, { SP_GOLEMIT, 12, 6, 10 },
    { SP_ZAPPET, 10, 6, 9 }, { SP_PUFFOWL, 10, 6, 9 }, { SP_FROSTOAT, 8, 7, 11 },
    { SP_SKYWISP, 8, 6, 9 },
};
static const WildSlot WILD_RISE[] = {
    { SP_VOLTUX, 25, 9, 13 }, { SP_ZAPPET, 25, 9, 12 }, { SP_GOLEMIT, 20, 9, 12 },
    { SP_PUFFOWL, 15, 9, 12 }, { SP_FROSTOAT, 10, 10, 13 }, { SP_STORMHAWK, 5, 14, 17 },
};

