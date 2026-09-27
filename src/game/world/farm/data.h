/*
 * world/farm/data.h -- WILLOW ACRE (the farm south of Maple Village) and
 * its FARMHOUSE. Owner: FARM system (docs/EXPANSION.md 7.2).
 *
 * WILLOW ACRE: the village path comes in at x 19-20 on the north edge (the
 * edge contract) and runs down the middle of the fenced field. The FARM
 * GATE decor closes the fence until you own the deed (farm.c opens it).
 * Outside the fence: the farmhouse yard, a pond, REEVE by the FOR SALE
 * sign and four wild glowberry bushes (patches 50-53). Inside: three soil
 * blocks of 12x4 plots, the work yard (bin, jar, press, drying rack),
 * beehives, a pond to fill the can, and eight orchard mounds (row 30; the
 * tree crowns take row 29). farm.c numbers the plots row-major over the
 * A_SOIL cells, and keeps its workers inside x 4-35, y 13-32.
 */

static const char *const WILLOW_ACRE_ROWS[] = {
    "TTTTTTTTTTTTTTTTTTT==TTTTTTTTTTTTTTTTTTT", /*  0 */
    "ttttttttttttttttttt==ttttttttttttttttttt", /*  1 */
    "TTxxxxxxxxxx.......==.................TT", /*  2 */
    "ttxxxxxxxxxx.rr....==..yy.........rr..tt", /*  3 */
    "TTxxxxxxxxxx.r.....==.....m.m.m.m.....TT", /*  4 */
    "ttxxxxxxxxxx.......==.................tt", /*  5 */
    "TTxxxxxxxxxx...rr..==.................TT", /*  6 */
    "ttxxxxxxxxxx..yy...==..........~~~~~..tt", /*  7 */
    "TTxxxxxxxxxx.......==...rr....~~~~~~..TT", /*  8 */
    "ttxxxxxxxxxx.......==..........~~~~~..tt", /*  9 */
    "TTxxx================...............y.TT", /* 10 */
    "tt......y..........==...............y.tt", /* 11 */
    "TT.----------------==---------------].TT", /* 12 */
    "tt.|eeeeeeeeeeeeee.==.eeeeeeeeeeeeee|.tt", /* 13 */
    "TT.|esssssssssssse.==.esssssssssssse|.TT", /* 14 */
    "tt.|esssssssssssse.==.esssssssssssse|.tt", /* 15 */
    "TT.|esssssssssssse.==.esssssssssssse|.TT", /* 16 */
    "tt.|esssssssssssse.==.esssssssssssse|.tt", /* 17 */
    "TT.|eeeeeeeeeeeeee.==.eeeeeeeeeeeeee|.TT", /* 18 */
    "tt.|eeeeeeeeeeeeee.==xxxxxxx........|.tt", /* 19 */
    "TT.|esssssssssssse.==xxxxxxx........|.TT", /* 20 */
    "tt.|esssssssssssse.==xxxxxxx........|.tt", /* 21 */
    "TT.|esssssssssssse.==xxxxxxx........|.TT", /* 22 */
    "tt.|esssssssssssse.==...............|.tt", /* 23 */
    "TT.|eeeeeeeeeeeeee.==........~~~~~~.|.TT", /* 24 */
    "tt.|...............==........~~~~~~.|.tt", /* 25 */
    "TT.|...............==........~~~~~~.|.TT", /* 26 */
    "tt.|...............==...............|.tt", /* 27 */
    "TT.|...............==...............|.TT", /* 28 */
    "tt.|...............==...............|.tt", /* 29 */
    "TT.|..o..o..o..o...==...o..o..o..o..|.TT", /* 30 */
    "tt.|...............==...............|.tt", /* 31 */
    "TT.|...............==...............|.TT", /* 32 */
    "tt.{--------------------------------}.tt", /* 33 */
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT", /* 34 */
    "tttttttttttttttttttttttttttttttttttttttt", /* 35 */
};

static const Stamp WILLOW_ACRE_STAMPS[] = { STAMP(FA, FARMHOUSE, 3, 3) };

static const DecorPlace WILLOW_ACRE_DECOR[] = {
    /* the yard */
    DP(SIGNPOST, 18, 3), DP(CART, 9, 3), DP(WOODPILE, 9, 8), DP(BARREL, 2, 8), DP(CRATE, 2, 9),
    DP(WATER_TROUGH, 13, 8), DP(HAY_BALE, 16, 8), DP(HAY_BALE, 17, 8), DP(STUMP, 25, 6),
    /* the fence gate and the sign (gone once you own the farm) */
    DP(FARM_GATE, 19, 12), DPF(FARM_GATE, 20, 12), DP(FOR_SALE, 22, 11),
    /* the work yard */
    DP(SHIPPING_BIN, 21, 19), DP(PRESERVES_JAR, 24, 19), DP(PRESS, 26, 19), DP(DRIER, 22, 22),
    DP(SACKS, 27, 22), DP(WHEELBARROW, 17, 19), DP(SCARECROW, 10, 18),
    DP(BEEHIVE, 33, 20), DP(BEEHIVE, 34, 21), DP(PUMPKINS, 34, 31), DP(PUMPKINS, 5, 26),
};

static const MapObj WILLOW_ACRE_OBJS[] = {
    OBJ(BERRY, 26, 4, 50), OBJ(BERRY, 28, 4, 51), OBJ(BERRY, 30, 4, 52), OBJ(BERRY, 32, 4, 53),
};

static const char *const FARMHOUSE_ROWS[] = {
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

static const Stamp FARMHOUSE_STAMPS[] = { STAMP(I, RUG, 4, 5) };

static const DecorPlace FARMHOUSE_DECOR[] = {
    /* kitchen corner and the work board on the back wall */
    DP(STOVE, 0, 1), DP(SINK_COUNTER, 1, 1), DP(WORK_BOARD, 3, 0), DP(BOOKSHELF_SMALL, 6, 1),
    DP(FARM_CHEST, 7, 2), DP(KIN_BASKET, 9, 2), DP(BED, 10, 2),
    DP(TABLE, 1, 4), DP(CHAIR_UP, 1, 6), DP(CHAIR_UP, 2, 6),
    DP(SACKS_IN, 0, 7), DP(BARREL_IN, 1, 7), DP(PLANT, 10, 6), DP(SMALL_PLANT, 9, 7),
};
