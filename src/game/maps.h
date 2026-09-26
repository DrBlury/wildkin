/*
 * The world: maps, doors, people, wardens, signs, satchels and wild kin.
 *
 * Outdoor maps use the TOWN (village) or WILD (route) tileset legend:
 *   T/t tree top/bottom   P/p pine top/bottom   . grass   , tall grass
 *   r/y flowers   = path   ~ water   # paving   c/v bout ring floor/line
 *   L ledge (hop down), [ ] its left/right ends   s sand   f forest floor
 *   R reeds   d dirt   m clover meadow   C cliff (c: plain rock below)   X building
 * Interiors: W upper wall, w lower wall, n window, k clock, p painting,
 *   . wood floor, : tile floor, D door mat, < = > counter, space = void.
 * Furniture, props and everything else placed on top are decor (see the
 * DK_* catalog in gfx_field.h); edges link maps into one world:
 *
 *             STORMSTONE RISE
 *                   |
 *             WHISPER MEADOW
 *                   |
 *   MIRROR LAKE - MAPLE VILLAGE - BRAMBLEWOOD
 */

enum {
    MAP_TOWN, MAP_HOME, MAP_BAKERY, MAP_LAB, MAP_SHOP, MAP_REST, MAP_GARDEN,
    MAP_MEADOW, MAP_RISE, MAP_WOOD, MAP_LAKE, MAP_CABIN, MAP_STATION,
    MAP_COUNT
};

/* Battle backdrops (mapped onto the battle engine's scenes in script.c). */
enum { SC_MEADOW, SC_FOREST, SC_LAKE, SC_RING, SC_STORM };

enum {
    SCR_TALK,      /* says NpcDef.text; reveals lore if it has a source */
    SCR_KEEPER, SCR_AIDE, SCR_GRAN, SCR_BAKER, SCR_GARDENER, SCR_MARLO,
    SCR_SHOP, SCR_TENDER, SCR_HERMIT, SCR_VASS, SCR_WOODWARD, SCR_WARDEN,
    SCR_KID,
};

#define DP(K, X, Y) { DK_##K, X, Y, 0 }
#define DPF(K, X, Y) { DK_##K, X, Y, DF_HFLIP }

/* ================================================================ */
/*  MAPLE VILLAGE                                                   */
/* ================================================================ */

static const char *const TOWN_ROWS[] = {
    "TTTTTTTTTTTTTTTTTTT==TTTTTTTTTTTTTTTTTTT", /*  0 */
    "ttttttttttttttttttt==ttttttttttttttttttt", /*  1 */
    "TT.................==......XXXXXXX....TT", /*  2 */
    "tt..XXXXX..XXXXX...==.rrr..XXXXXXX....tt", /*  3 */
    "TT..XXXXX..XXXXX...==.rrr..XXXXXXX....TT", /*  4 */
    "tt..XXXXX..XXXXX...==.rrr..XXXXXXX....tt", /*  5 */
    "TT..XXXXX..XXXXX...==......XXXXXXX....TT", /*  6 */
    "tt....========.....==.........=.......tt", /*  7 */
    "TT....===============.........=.......TT", /*  8 */
    "tt....=............============....yy.tt", /*  9 */
    "TT....=............============....yy.TT", /* 10 */
    "tt....=......######==##..vccccccccv...tt", /* 11 */
    "TTrr..=..yy..######==##..vccccccccv...TT", /* 12 */
    "ttrr..=..yy..######==##..vccccccccv...tt", /* 13 */
    "TT....=......######==##..vccccccccv...TT", /* 14 */
    "tt....=......######==##..vccccccccv...tt", /* 15 */
    "TT....=............==.................TT", /* 16 */
    "========================================", /* 17 */
    "========================================", /* 18 */
    "tt.................==.................tt", /* 19 */
    "TT.................==...yyyy..........TT", /* 20 */
    "tt.................==...yyyy...XXXXX..tt", /* 21 */
    "TT..XXXXX..XXXXX...==..........XXXXX..TT", /* 22 */
    "tt..XXXXX..XXXXX...==..........XXXXX..tt", /* 23 */
    "TT..XXXXX..XXXXX...==..........XXXXX..TT", /* 24 */
    "tt..XXXXX..XXXXX...==............=....tt", /* 25 */
    "TT..==============================....TT", /* 26 */
    "tt....................................tt", /* 27 */
    "TT..~~~~~...rrrrr......,,,,,,,,..yyyy.TT", /* 28 */
    "tt.~~~~~~~..rrrrr......,,,,,,,,..yyyy.tt", /* 29 */
    "TT.~~~~~~~..yyyyy......,,,,,,,,..rrrr.TT", /* 30 */
    "tt..~~~~~...yyyyy......,,,,,,,,.......tt", /* 31 */
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT", /* 32 */
    "tttttttttttttttttttttttttttttttttttttttt", /* 33 */
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
    "tt.....mmmmm....rrrr...==..,,,,,,,,,,.tt", /* 11 */
    "TTTTTT..mmmmm...rrrr...==..,,,,,,,,,,.TT", /* 12 */
    "tttttt.rrr......rrrr...==..,,,,,,,,,,.tt", /* 13 */
    "TTTTTT.rrr.............==..,,,,,,,,,,.TT", /* 14 */
    "tttttt.rrr.............==dd,,,,,,,,,,.tt", /* 15 */
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
    "PPPPPPPPPPPPPPPPPPPPPPPP", /*  0 */
    "pppppppppppppppppppppppp", /*  1 */
    "PP....................PP", /*  2 */
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
    "===========f,,,,,,,,,f~~f,,,,==,,,,,,,,,,fpp", /* 17 */
    "===========fdddddd,,,f~~f,,,,==,,,,,,,,,,fPP", /* 18 */
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
    "ppfPPPPPPPPPPfffffffff~~fffffff,,,,,,,,,,fpp", /* 31 */
    "PPfppppppppppfffffffff~~fffffff,,,,,,,,,,fPP", /* 32 */
    "ppffffffffffffffffffff~~fffffff,,,,,,,,,,fpp", /* 33 */
    "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", /* 34 */
    "pppppppppppppppppppppppppppppppppppppppppppp", /* 35 */
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
    "tt......==================.....yyyyyy.tt", /* 31 */
    "TT......==================.....yyyyyy.TT", /* 32 */
    "tt.............................yyyyyy.tt", /* 33 */
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT", /* 34 */
    "tttttttttttttttttttttttttttttttttttttttt", /* 35 */
};

static const Stamp TOWN_STAMPS[] = {
    STAMP(T, HOUSE_RED, 4, 3),    /* home */
    STAMP(T, HOUSE_BLUE, 11, 3),  /* bakery */
    STAMP(T, LAB, 27, 2),         /* almanac house */
    STAMP(T, HEAL, 4, 22),        /* hearth hall */
    STAMP(T, SHOP, 11, 22),       /* shop */
    STAMP(T, HOUSE_BLUE, 31, 21), /* garden house */
    STAMP(T, COURT_CIRCLE, 29, 12),
};

static const DecorPlace TOWN_DECOR[] = {
    /* the plaza and the Old Hearth */
    DP(OLD_HEARTH, 15, 12), DP(BENCH, 13, 15), DP(BENCH, 17, 11),
    DP(STONE_LANTERN, 12, 11), DP(STONE_LANTERN, 22, 11),
    /* market */
    DP(MARKET_STALL, 8, 10), DP(BARREL, 11, 10), DP(CRATE, 11, 11), DP(SACKS, 7, 11),
    DP(MARKET_STALL, 15, 20), DP(SACKS, 14, 21), DP(BARREL, 18, 21), DP(CRATE_STACK, 18, 19),
    /* homes */
    DP(MAILBOX, 4, 7), DP(FLOWER_POT, 3, 7), DP(FLOWER_POT, 16, 6), DP(PLANTER, 27, 7),
    DP(PLANTER, 32, 7), DP(WELL, 2, 22), DP(FLOWER_POT, 10, 25), DP(FLOWER_POT, 3, 25),
    /* signs */
    DP(SIGNPOST, 16, 7), DP(SIGNPOST, 26, 7), DP(SIGNPOST, 21, 19), DP(SIGNPOST, 21, 2),
    DP(SIGNPOST, 2, 16), DP(SIGNPOST, 37, 16), DP(SIGNPOST, 9, 27), DP(SIGNPOST, 16, 25),
    DP(SIGNPOST, 24, 16),
    /* lights */
    DP(LAMP, 10, 15), DP(LAMP, 23, 15), DP(LAMP, 17, 19), DP(LAMP, 29, 19),
    DP(LANTERN_POST, 24, 11), DP(LANTERN_POST, 35, 11), DP(FLAG, 35, 13),
    /* the bout ring fence */
    DP(FENCE, 25, 16), DP(FENCE, 26, 16), DP(FENCE, 27, 16), DP(FENCE, 28, 16),
    DP(FENCE, 29, 16), DP(FENCE, 30, 16), DP(FENCE, 31, 16), DP(FENCE, 32, 16),
    DP(FENCE, 33, 16), DP(FENCE_END, 34, 16),
    /* the farm corner */
    DP(HAY_BALE, 37, 24), DP(HAY_BALE, 36, 23), DP(WATER_TROUGH, 35, 26), DP(WOODPILE, 29, 25),
    /* green bits */
    DP(BIG_TREE, 19, 28), DP(BUSH, 2, 9), DP(BUSH, 2, 19), DP(BUSH, 37, 21), DP(BUSH, 9, 20),
    DP(BUSH, 17, 27), DP(BUSH, 36, 2), DP(BUSH, 2, 2), DP(BENCH, 4, 27),
    DP(LILY_PADS, 5, 29), DP(LILY_PADS, 7, 30), DP(ROCK, 36, 27), DP(ROCK, 11, 27),
    DP(SMALL_FLOWERS, 22, 7), DP(SMALL_FLOWERS, 34, 4), DP(SMALL_FLOWERS, 9, 16),
    DP(PEBBLES, 25, 25), DP(SMALL_FLOWERS, 30, 20),
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

#define NDEC(a) ((u8)(sizeof(a) / sizeof(a[0])))
#define NO_LINKS { MAP_NONE, MAP_NONE, MAP_NONE, MAP_NONE }, { 0, 0, 0, 0 }

static const MapDef MAPS[MAP_COUNT] = {
    [MAP_TOWN] = { 40, NROWS(TOWN_ROWS), TS_TOWN, SC_MEADOW, TOWN_ROWS, TOWN_STAMPS, NSTAMP(TOWN_STAMPS),
                   TOWN_DECOR, NDEC(TOWN_DECOR), "MAPLE VILLAGE", ZONE_NONE, MF_OUTDOOR,
                   { MAP_MEADOW, MAP_NONE, MAP_LAKE, MAP_WOOD }, { 0, 0, 0, 0 } },
    [MAP_MEADOW] = { 40, NROWS(MEADOW_ROWS), TS_WILD, SC_MEADOW, MEADOW_ROWS, 0, 0,
                     MEADOW_DECOR, NDEC(MEADOW_DECOR), "WHISPER MEADOW", 0, MF_OUTDOOR,
                     { MAP_RISE, MAP_TOWN, MAP_NONE, MAP_NONE }, { 0, 0, 0, 0 } },
    [MAP_RISE] = { 24, NROWS(RISE_ROWS), TS_WILD, SC_STORM, RISE_ROWS, 0, 0,
                   RISE_DECOR, NDEC(RISE_DECOR), "STORMSTONE RISE", 3, MF_OUTDOOR,
                   { MAP_NONE, MAP_MEADOW, MAP_NONE, MAP_NONE }, { 0, 0, 0, 0 } },
    [MAP_WOOD] = { 44, NROWS(WOOD_ROWS), TS_WILD, SC_FOREST, WOOD_ROWS, WOOD_STAMPS, NSTAMP(WOOD_STAMPS),
                   WOOD_DECOR, NDEC(WOOD_DECOR), "BRAMBLEWOOD", 1, MF_OUTDOOR,
                   { MAP_NONE, MAP_NONE, MAP_TOWN, MAP_NONE }, { 0, 0, 0, 0 } },
    [MAP_LAKE] = { 40, NROWS(LAKE_ROWS), TS_WILD, SC_LAKE, LAKE_ROWS, LAKE_STAMPS, NSTAMP(LAKE_STAMPS),
                   LAKE_DECOR, NDEC(LAKE_DECOR), "MIRROR LAKE", 2, MF_OUTDOOR,
                   { MAP_NONE, MAP_NONE, MAP_NONE, MAP_TOWN }, { 0, 0, 0, 0 } },
    [MAP_HOME]   = { 11, NROWS(HOME_ROWS), TS_INTERIOR, SC_MEADOW, HOME_ROWS, HOME_STAMPS, NSTAMP(HOME_STAMPS),
                     HOME_DECOR, NDEC(HOME_DECOR), "YOUR HOUSE", ZONE_NONE, 0, NO_LINKS },
    [MAP_BAKERY] = { 11, NROWS(BAKERY_ROWS), TS_INTERIOR, SC_MEADOW, BAKERY_ROWS, 0, 0,
                     BAKERY_DECOR, NDEC(BAKERY_DECOR), "BAKERY", ZONE_NONE, 0, NO_LINKS },
    [MAP_LAB]    = { 13, NROWS(LAB_ROWS), TS_INTERIOR, SC_MEADOW, LAB_ROWS, 0, 0,
                     LAB_DECOR, NDEC(LAB_DECOR), "ALMANAC HOUSE", ZONE_NONE, 0, NO_LINKS },
    [MAP_SHOP]   = { 11, NROWS(SHOP_ROWS), TS_INTERIOR, SC_MEADOW, SHOP_ROWS, 0, 0,
                     SHOP_DECOR, NDEC(SHOP_DECOR), "MAPLE SHOP", ZONE_NONE, 0, NO_LINKS },
    [MAP_REST]   = { 11, NROWS(REST_ROWS), TS_INTERIOR, SC_MEADOW, REST_ROWS, REST_STAMPS, NSTAMP(REST_STAMPS),
                     REST_DECOR, NDEC(REST_DECOR), "HEARTH HALL", ZONE_NONE, MF_HEAL, NO_LINKS },
    [MAP_GARDEN] = { 11, NROWS(GARDEN_ROWS), TS_INTERIOR, SC_MEADOW, GARDEN_ROWS, 0, 0,
                     GARDEN_DECOR, NDEC(GARDEN_DECOR), "GARDEN HOUSE", ZONE_NONE, 0, NO_LINKS },
    [MAP_CABIN]  = { 11, NROWS(CABIN_ROWS), TS_INTERIOR, SC_FOREST, CABIN_ROWS, 0, 0,
                     CABIN_DECOR, NDEC(CABIN_DECOR), "HERMIT'S CABIN", ZONE_NONE, 0, NO_LINKS },
    [MAP_STATION] = { 13, NROWS(STATION_ROWS), TS_INTERIOR, SC_LAKE, STATION_ROWS, 0, 0,
                      STATION_DECOR, NDEC(STATION_DECOR), "FIELD STATION", ZONE_NONE, 0, NO_LINKS },
};

/* Doors and where they lead (interiors exit back through their door). */
static const Warp WARPS[] = {
    { MAP_TOWN, 6, 6, MAP_HOME, 5, 8 },
    { MAP_TOWN, 13, 6, MAP_BAKERY, 5, 8 },
    { MAP_TOWN, 30, 6, MAP_LAB, 6, 9 },
    { MAP_TOWN, 6, 25, MAP_REST, 5, 8 },
    { MAP_TOWN, 13, 25, MAP_SHOP, 5, 8 },
    { MAP_TOWN, 33, 24, MAP_GARDEN, 5, 8 },
    { MAP_WOOD, 36, 8, MAP_CABIN, 5, 8 },
    { MAP_LAKE, 29, 6, MAP_STATION, 6, 8 },
};

/* ================================================================ */
/*  Wardens                                                         */
/* ================================================================ */

enum {
    TR_LUCA, TR_MAE, TR_IDA, TR_FERN, TR_KAI, TR_ORLA, TR_BRIN, TR_SELA, TR_TOMAS,
    TR_MARLO,
};

static const TrainerDef TRAINERS[] = {
    [TR_LUCA] = { "WARDEN LUCA", 2, { SP_NIBBIT, SP_ZAPPET }, { 4, 5 }, 240,
                  "Hey, you're new! First bout of the day is always the best one!",
                  "Aww! My NIBBIT's all spilled out. Good bout!" },
    [TR_MAE] = { "WARDEN MAE", 2, { SP_PUFFOWL, SP_DANDELAMB }, { 6, 6 }, 300,
                 "The meadow's brimming today. Let's spill some of it, you and me!",
                 "Now THAT was a bucket of rain. Thank you!" },
    [TR_IDA] = { "WARDEN IDA", 3, { SP_VOLTUX, SP_GOLEMIT, SP_ZAPPET }, { 13, 13, 14 }, 700,
                 "I chase storms. You feel that charge in the air? Prove you can handle it!",
                 "Ha! You'd do fine in a thunderstorm." },
    [TR_FERN] = { "WARDEN FERN", 2, { SP_THORNIP, SP_MOSSHELL }, { 7, 8 }, 330,
                  "Shh! You'll wake the wood. ...Oh, a warden! Bout time!",
                  "The brambles approve of you. I think." },
    [TR_KAI] = { "WARDEN KAI", 3, { SP_CINDERUB, SP_SKYWISP, SP_NIBBIT }, { 8, 8, 9 }, 420,
                 "Three kin, three chances to lose. Ready?",
                 "Guess I'm the one who lost three times. Nice!" },
    [TR_ORLA] = { "WARDEN ORLA", 1, { SP_WISPIRE }, { 11 }, 480,
                  "Follow the little light... and you'll find me. Everyone does.",
                  "My wisp says you're no easy traveler to lead astray." },
    [TR_BRIN] = { "WARDEN BRIN", 2, { SP_BUBBLIN, SP_AQUAPO }, { 8, 9 }, 360,
                  "Fish aren't biting, so I'm biting! Bout me!",
                  "Splashed! Totally splashed." },
    [TR_SELA] = { "WARDEN SELA", 2, { SP_FROSTOAT, SP_GOLEMIT }, { 10, 10 }, 450,
                  "The lake's too warm this year. Let's cool things down.",
                  "Brr. You're tougher than the lake ice." },
    [TR_TOMAS] = { "WARDEN TOMAS", 3, { SP_ZAPPET, SP_PUFFOWL, SP_BUBBLIN }, { 10, 10, 11 }, 520,
                   "Dr. Vass says every bout is an experiment. Let's collect data!",
                   "Data collected: you win. Fascinating." },
    [TR_MARLO] = { "WARDEN MARLO", 3, { SP_CINDERUB, SP_VOLTUX, SP_PUFFOWL }, { 12, 12, 13 }, 1200,
                   "", "HAH! That's a warden's bout! The RING SASH is yours!" },
};

/* ================================================================ */
/*  People                                                          */
/* ================================================================ */

#define PERSON(map, x, y, chr, face, beh, scr, lore, name, text) \
    { map, x, y, CHR_##chr, DIR_##face, BEH_##beh, SCR_##scr, lore, NO_TRAINER, 0, NO_KIN, name, text }
#define PERSON_KIN(map, x, y, chr, face, beh, scr, lore, kin, name, text) \
    { map, x, y, CHR_##chr, DIR_##face, BEH_##beh, SCR_##scr, lore, NO_TRAINER, 0, kin, name, text }
#define WARDEN(map, x, y, chr, face, sight, tr, kin, text) \
    { map, x, y, CHR_##chr, DIR_##face, BEH_LOOK, SCR_WARDEN, NO_LORE, tr, sight, kin, 0, text }

static const NpcDef NPCS[] = {
    /* village */
    PERSON(MAP_TOWN, 16, 14, ELDER, DOWN, STILL, TALK, LSRC_ELDER, "ELDER BRAM",
           "The Old Hearth has burned here since the first Kinship. Sit a while with it."),
    PERSON_KIN(MAP_TOWN, 29, 13, GUIDE, LEFT, LOOK, MARLO, LSRC_MARLO, SP_CINDERUB, "WARDEN MARLO", 0),
    PERSON(MAP_TOWN, 22, 13, KID, DOWN, WANDER, KID, LSRC_KID, "KID", 0),
    PERSON(MAP_TOWN, 10, 29, KID_B, LEFT, LOOK, TALK, NO_LORE, "KID",
           "I saw the sky flash green over the RISE last night! Something up there is BRIMMING."),
    PERSON_KIN(MAP_TOWN, 28, 22, VILLAGER, DOWN, WANDER, TALK, NO_LORE, SP_DANDELAMB, "FARMER",
               "My DANDELAMB naps in the carrot rows. Best harvest in years, every year."),
    /* interiors */
    PERSON(MAP_HOME, 7, 4, GRAN, DOWN, LOOK, GRAN, LSRC_GRAN, "GRAN", 0),
    PERSON(MAP_BAKERY, 5, 6, BAKER, DOWN, WANDER, BAKER, LSRC_BAKER, "BAKER", 0),
    PERSON(MAP_LAB, 6, 4, PROFESSOR, DOWN, LOOK, KEEPER, LSRC_KEEPER, "KEEPER LINDEN", 0),
    PERSON(MAP_LAB, 3, 5, KID_B, DOWN, LOOK, AIDE, LSRC_AIDE, "AIDE PIP", 0),
    PERSON(MAP_SHOP, 1, 2, SHOPKEEPER, DOWN, STILL, SHOP, LSRC_CLERK, "CLERK", 0),
    PERSON(MAP_REST, 5, 2, HEALER, DOWN, STILL, TENDER, LSRC_TENDER, "TENDER OLA", 0),
    PERSON(MAP_GARDEN, 7, 4, GARDENER, DOWN, LOOK, GARDENER, LSRC_GARDENER, "GARDENER", 0),
    PERSON(MAP_CABIN, 8, 5, HERMIT, DOWN, LOOK, HERMIT, LSRC_HERMIT, "HERMIT", 0),
    PERSON(MAP_STATION, 7, 4, SCIENTIST, DOWN, LOOK, VASS, LSRC_RESEARCHER, "DR. VASS", 0),
    /* whisper meadow */
    PERSON_KIN(MAP_MEADOW, 8, 26, VILLAGER, DOWN, WANDER, TALK, LSRC_SHEPHERD, SP_PUFFLEECE, "SHEPHERD",
               "Flock's calm today. They had a good long bout with the wind this morning."),
    PERSON(MAP_MEADOW, 33, 7, KID, DOWN, LOOK, TALK, LSRC_KITEFLYER, "KITE FLYER",
           "No kite today... the wind keeps changing its mind. Something up north is pulling at it."),
    WARDEN(MAP_MEADOW, 18, 35, WARDEN_A, RIGHT, 4, TR_LUCA, SP_NIBBIT, "I'm gonna train until NIBBIT grows into a GNAWLORD!"),
    WARDEN(MAP_MEADOW, 22, 12, WARDEN_B, RIGHT, 4, TR_MAE, NO_KIN, "The grass hums after a good bout. Listen!"),
    /* stormstone rise */
    WARDEN(MAP_RISE, 10, 13, WARDEN_A, RIGHT, 3, TR_IDA, SP_VOLTUX, "The Stormstone's been singing for weeks. Whatever's up there, it's big."),
    /* bramblewood */
    PERSON_KIN(MAP_WOOD, 11, 19, GARDENER, RIGHT, LOOK, WOODWARD, LSRC_WOODWARD, SP_MOSSHELL, "WOODWARD", 0),
    PERSON(MAP_WOOD, 40, 24, VILLAGER, LEFT, WANDER, TALK, LSRC_FORAGER, "FORAGER",
           "Glowcaps, stinkhorns, lady's-lanterns... the wood's a pantry if you know where to look."),
    WARDEN(MAP_WOOD, 15, 10, WARDEN_B, UP, 3, TR_FERN, NO_KIN, "The wood is louder than it looks."),
    WARDEN(MAP_WOOD, 32, 19, WARDEN_A, LEFT, 3, TR_KAI, SP_CINDERUB, "Next time I'm bringing four kin."),
    WARDEN(MAP_WOOD, 27, 27, WARDEN_B, DOWN, 3, TR_ORLA, SP_WISPIRE, "Lost? No. Nobody's lost in Bramblewood. Just early."),
    /* mirror lake */
    PERSON(MAP_LAKE, 22, 16, FISHER, LEFT, LOOK, TALK, LSRC_FISHER, "FISHER",
           "The lake's glassy today. Too glassy. Water holds its breath before a storm."),
    PERSON(MAP_LAKE, 26, 33, KID_B, UP, WANDER, TALK, LSRC_LAKEKID, "KID",
           "FROSTOAT curled up on my boots and now they're frozen to the dock!"),
    WARDEN(MAP_LAKE, 26, 22, WARDEN_A, LEFT, 2, TR_BRIN, SP_BUBBLIN, "The fish still aren't biting."),
    WARDEN(MAP_LAKE, 31, 9, WARDEN_B, DOWN, 4, TR_SELA, SP_FROSTOAT, "Winter will come early if the storm spills over the lake."),
    WARDEN(MAP_LAKE, 12, 33, WARDEN_A, UP, 2, TR_TOMAS, NO_KIN, "My notebook is full of your bout. Thank you!"),
};

/* ================================================================ */
/*  Signs & satchels                                                */
/* ================================================================ */

static const Sign SIGNS[] = {
    { MAP_TOWN, 21, 19, "MAPLE VILLAGE\fHome of the Old Hearth. Every bout is a bucket of rain." },
    { MAP_TOWN, 21, 2, "NORTH: WHISPER MEADOW\fSTORMSTONE RISE lies at the top of the meadow." },
    { MAP_TOWN, 2, 16, "WEST: MIRROR LAKE\fThe Almanac field station stands on the north shore." },
    { MAP_TOWN, 37, 16, "EAST: BRAMBLEWOOD\fMind the brambles. Mind the wisps." },
    { MAP_TOWN, 26, 7, "ALMANAC HOUSE\fKeeper Linden records every kin, every season and every storm." },
    { MAP_TOWN, 9, 27, "HEARTH HALL\fRest your kin by the hearth. Free, as it has always been." },
    { MAP_TOWN, 16, 25, "MAPLE SHOP\fLanterns, tonics, tuning forks and shards." },
    { MAP_TOWN, 24, 16, "BOUT RING\fWarden Marlo takes on all comers!" },
    { MAP_TOWN, 16, 7, "BAKERY\fGlow-bee honey buns every morning!" },
    { MAP_MEADOW, 21, 40, "WHISPER MEADOW\fBrimming kin roam the tall grass. Answer them!" },
    { MAP_MEADOW, 13, 2, "STORMSTONE RISE ahead\fThe wind up there never stops." },
    { MAP_RISE, 13, 17, "STORMSTONE RISE\fAn old stone circle. The air hums like a plucked string." },
    { MAP_WOOD, 2, 16, "BRAMBLEWOOD\fThe woodward's path runs east over the creek." },
    { MAP_WOOD, 33, 10, "HERMIT'S CABIN\fKnock. Wait. Knock again. Then wait longer." },
    { MAP_LAKE, 36, 16, "MIRROR LAKE\fField station: follow the path north." },
    { MAP_LAKE, 28, 7, "ALMANAC FIELD STATION\fDR. VASS. Please do not tap on the heartglass." },
};

static const ItemBall ITEM_BALLS[] = {
    { MAP_TOWN, 37, 3, ITEM_TONIC, 2 },
    { MAP_TOWN, 2, 21, ITEM_BIG_TONIC, 1 },
    { MAP_TOWN, 37, 31, ITEM_SUNSEED, 1 },
    { MAP_MEADOW, 4, 29, ITEM_TONIC, 2 },
    { MAP_MEADOW, 37, 33, ITEM_LANTERN, 3 },
    { MAP_MEADOW, 33, 2, ITEM_MINT_TEA, 1 },
    { MAP_MEADOW, 17, 40, ITEM_HUSH_BELL, 1 },
    { MAP_MEADOW, 3, 11, ITEM_BRAVE_CHILI, 1 },
    { MAP_RISE, 20, 3, ITEM_STAR_LANTERN, 1 },
    { MAP_RISE, 3, 3, ITEM_GRAND_TONIC, 1 },
    { MAP_WOOD, 40, 33, ITEM_DUSK_SHARD, 1 },
    { MAP_WOOD, 3, 19, ITEM_SUNSEED, 1 },
    { MAP_WOOD, 39, 2, ITEM_SOOTHE_BALM, 1 },
    { MAP_WOOD, 20, 22, ITEM_GLOW_LANTERN, 2 },
    { MAP_WOOD, 12, 2, ITEM_WAKE_BELL, 1 },
    { MAP_LAKE, 3, 33, ITEM_WAKE_BELL, 1 },
    { MAP_LAKE, 36, 33, ITEM_GLOW_LANTERN, 3 },
    { MAP_LAKE, 3, 3, ITEM_IRONBARK, 1 },
    { MAP_LAKE, 36, 6, ITEM_BIG_TONIC, 2 },
};

/* ================================================================ */
/*  Wild kin (visible in tall grass and reeds)                      */
/* ================================================================ */

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

#define NSLOT(a) ((u8)(sizeof(a) / sizeof(a[0])))
static const WildZone WILD_ZONES[] = {
    { WILD_MEADOW, NSLOT(WILD_MEADOW), 4, "WHISPER MEADOW" },
    { WILD_WOOD, NSLOT(WILD_WOOD), 4, "BRAMBLEWOOD" },
    { WILD_LAKE, NSLOT(WILD_LAKE), 4, "MIRROR LAKE" },
    { WILD_RISE, NSLOT(WILD_RISE), 3, "STORMSTONE RISE" },
};
