/*
 * world/west/data.h -- map rows, stamps, decor, objects and wild slots of
 * W-WEST: SALTWIND TRAIL, PORT BRINE (+ interiors, the CURRENT HALL), the
 * SEA ROUTE, GULL ISLE and the DROWNED BELL. Owner: W-WEST.
 *
 * Outdoor maps, the Current Hall and the grotto use the 'coast' tileset
 * (tools/tilesets/ts_coast.py); props come from tools/decor_west.py and the
 * village props listed in ts_coast.USES_DECOR. Legend:
 *
 *   outdoor  . grass   , tall grass (kin)   ; marram dune grass (kin)
 *            s sand    = path   ~ sea (surf; sand shore autotile)
 *            # plaza slabs   q quay setts   k rock shelf   o tide pool
 *            % salt pan   C cliff (grass lip)   c cliff face
 *            L ledge  [ ] ledge ends   l dune ledge (hop south)
 *            r y flowers   P/p pine top/bottom   A/a palm top/bottom
 *   hall     H wall top   h wall   n porthole   _ floor   M exit mat
 *            v ^ < > currents   O still pool (deep, solid)
 *   grotto   G rock   g rock face   : wet floor   ' glowing moss
 *            t temple slabs   * glowing pool (deep, solid)   m exit steps
 *
 * CURRENTS (A_CURRENT, direction (A_DIR_HI << 1 | A_DIR_LO) = the field.c
 * DIR_* order: 0 down, 1 up, 2 left, 3 right). A current cell is walkable.
 * Stepping onto one carries the player one cell per step in the direction
 * of the cell they stand on, until they reach a cell that is not a current
 * (or the way ahead is blocked). tools/tests/test_west.c solves the Hall
 * with exactly this rule.
 *
 * Edges (docs/EXPANSION.md 9): SALTWIND east y 31-32 = MIRROR LAKE west;
 * SALTWIND west y 19-20 = PORT BRINE east; PORT BRINE south x 20-21 = SEA
 * ROUTE north (a plank pier); SEA ROUTE south x 20-21 = GULL ISLE north.
 * The SEA ROUTE is open water: cross it with SURF (TIDE CREST) or take the
 * ferry (HARBOR OFFICE, 500c or the FERRY PASS).
 */

static const char *const SALTWIND_ROWS[] = {
    "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", /*  0 */
    "pppppppppppppppppppppppppppppppppppppppppppppppppp", /*  1 */
    "PPPP...PP.P...PP.P...PP.P...PP.P...PP.P...PP.PPPPP", /*  2 */
    "pppp...pp.p...pp.p...pp.p...pp.p...pp.p...pp.ppppp", /*  3 */
    "PP.............P.....P..........................PP", /*  4 */
    "pp..,,,,,,,,,,.p.....p..,,,,,,,,,,,,,,..,,,,,,..pp", /*  5 */
    "PP..,,,,,,,,,,..........,,,,,,,,,,,,,,..,,,,,,..PP", /*  6 */
    "pp..,,,,,,,,,,..........,,,,,,,,,,,,,,..,,,,,,..pp", /*  7 */
    "PP..,,,,,,,,,,...P......,,,,,,,,,,,,,,..........PP", /*  8 */
    "pp..,,,,,,,,,,...p......,,,,,,,,,,,,,,..........pp", /*  9 */
    "PP..............................................PP", /* 10 */
    "pp.P....P.......................................pp", /* 11 */
    "...p...rp.y.......................................", /* 12 */
    ".........=......=.................................", /* 13 */
    "PP...,,,,,,,,....................P....======....PP", /* 14 */
    "pp...,,,,,,,,.............P......p....======....pp", /* 15 */
    "PP...,,,,,,,,.............p...........==....P...PP", /* 16 */
    "pp...,,,,,,,,.....==..ry.......P......==....p...pp", /* 17 */
    "................r.==..y........p......==.yr.....PP", /* 18 */
    "====================.......P..........==........pp", /* 19 */
    "====================.......p.r........==......P.PP", /* 20 */
    "..s%%s%%s%%ss.....==..................==......p.pp", /* 21 */
    "PPsssssssssss.P...====================..........PP", /* 22 */
    "pps%%s%%s%%ss.p...====================..........pp", /* 23 */
    "PPsssssssssss.......................==..........PP", /* 24 */
    "ppsssssssssssssssssssllllllllllllsss==..........pp", /* 25 */
    "PPssss;;;;;;ssssssssss;;;;sss;;;;sss==..........PP", /* 26 */
    "ppss;;;;;;;;;;sssss;;;;;;;;;;;;;;;ss==kkkkkkkkkkpp", /* 27 */
    "PPss;;;;;;;;;;ssss;;;;;;;;;;;;;;;sss==kkokkkkkkkPP", /* 28 */
    "ppss;;;;;;;;;;ssss;;;;;;;;;;;;ssssss==kkkkkkokkkpp", /* 29 */
    "PPssss;;;;;;sssssss;;;;;;;;;;sssssss==kkkkkkkkkk..", /* 30 */
    "ppssssssssssssssssssss;;;;ssssssssss==============", /* 31 */
    "..ssssssssssssssssssssssssssssssssss==============", /* 32 */
    "~~sssssssssssssssssssssssssssssssssssskkkkkkkkkk~~", /* 33 */
    "~~sssssssssssssssssssssssssssssssssssskkkkkkkkkk~~", /* 34 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ssssss~~~~~~~~~~~~~~~", /* 35 */
    "~~~~~~ssssss~~~~~~~~~~~~sssssssssss~~~~~~~sssss~~~", /* 36 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ssss~~~~~~~~~~~~~~~~", /* 37 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 38 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 39 */
};
/* heights: the meadow and the bluff (rows 0-12) stand one level above the
 * dunes; stairs at (9,13) and (16,13), the bluff ledge at (41-43,13). */
static const char *const SALTWIND_ELEV[] = {
    "11111111111111111111111111111111111111111111111111", /*  0 */
    "11111111111111111111111111111111111111111111111111", /*  1 */
    "11111111111111111111111111111111111111111111111111", /*  2 */
    "11111111111111111111111111111111111111111111111111", /*  3 */
    "11111111111111111111111111111111111111111111111111", /*  4 */
    "11111111111111111111111111111111111111111111111111", /*  5 */
    "11111111111111111111111111111111111111111111111111", /*  6 */
    "11111111111111111111111111111111111111111111111111", /*  7 */
    "11111111111111111111111111111111111111111111111111", /*  8 */
    "11111111111111111111111111111111111111111111111111", /*  9 */
    "11111111111111111111111111111111111111111111111111", /* 10 */
    "11111111111111111111111111111111111111111111111111", /* 11 */
    "11111111111111111111111111111111111111111111111111", /* 12 */
    "000000000^000000^000000000000000000000000___000000", /* 13 */
    "00000000000000000000000000000000000000000000000000", /* 14 */
    "00000000000000000000000000000000000000000000000000", /* 15 */
    "00000000000000000000000000000000000000000000000000", /* 16 */
    "00000000000000000000000000000000000000000000000000", /* 17 */
    "00000000000000000000000000000000000000000000000000", /* 18 */
    "00000000000000000000000000000000000000000000000000", /* 19 */
    "00000000000000000000000000000000000000000000000000", /* 20 */
    "00000000000000000000000000000000000000000000000000", /* 21 */
    "00000000000000000000000000000000000000000000000000", /* 22 */
    "00000000000000000000000000000000000000000000000000", /* 23 */
    "00000000000000000000000000000000000000000000000000", /* 24 */
    "00000000000000000000000000000000000000000000000000", /* 25 */
    "00000000000000000000000000000000000000000000000000", /* 26 */
    "00000000000000000000000000000000000000000000000000", /* 27 */
    "00000000000000000000000000000000000000000000000000", /* 28 */
    "00000000000000000000000000000000000000000000000000", /* 29 */
    "00000000000000000000000000000000000000000000000000", /* 30 */
    "00000000000000000000000000000000000000000000000000", /* 31 */
    "00000000000000000000000000000000000000000000000000", /* 32 */
    "00000000000000000000000000000000000000000000000000", /* 33 */
    "00000000000000000000000000000000000000000000000000", /* 34 */
    "00000000000000000000000000000000000000000000000000", /* 35 */
    "00000000000000000000000000000000000000000000000000", /* 36 */
    "00000000000000000000000000000000000000000000000000", /* 37 */
    "00000000000000000000000000000000000000000000000000", /* 38 */
    "00000000000000000000000000000000000000000000000000", /* 39 */
};
static const DecorPlace SALTWIND_DECOR[] = {
    DP(SIGNPOST, 44, 30), DP(SIGNPOST, 4, 18), DP(SALT_HEAP, 12, 21), DP(SALT_HEAP, 12, 23),
    DPF(SALT_HEAP, 2, 25), DP(SHELLS, 18, 33), DP(STARFISH, 26, 34), DP(SEAWEED, 8, 34),
    DP(SEAWEED, 40, 35), DP(DRIFTWOOD, 13, 33), DP(CRAB_SHELL, 33, 36), DP(SEA_ROCK, 5, 37),
    DPF(SEA_ROCK, 22, 38), DP(SEA_ROCK, 43, 37), DP(BELL_BUOY, 37, 38), DP(GULL_POST, 35, 34),
    DP(ROCK, 30, 11), DP(BUSH, 16, 20), DP(BUSH, 33, 20), DP(LOG, 6, 12), DP(BENCH, 40, 24),
    DP(ROCK, 0, 18), DP(ROCK, 0, 21), DP(ROCK, 0, 32), DP(ROCK, 49, 30), DP(ROCK, 0, 12),
    DP(ROCK, 49, 12), DP(BUSH, 1, 12),
};
static const MapObj SALTWIND_OBJS[] = {
    OBJ(BERRY, 15, 15, 10), OBJ(BERRY, 34, 4, 11),
};

static const char *const PORT_BRINE_ROWS[] = {
    "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", /*  0 */
    "pppppppppppppppppppppppppppppppppppppppppppppppp", /*  1 */
    "PP............................................PP", /*  2 */
    "pp.....P....P...................P..........P..pp", /*  3 */
    "PP..P..p....p...................p..........p..PP", /*  4 */
    "pp..p........ry....................P..........pp", /*  5 */
    "PP...........y.....................p..........PP", /*  6 */
    "pp..............###############..ry....=......pp", /*  7 */
    "PP...P..........###############........=......PP", /*  8 */
    "pp...p..........######==#######........=....P.pp", /*  9 */
    "PP....................==...............=....p.PP", /* 10 */
    "pp....................==...............=......pp", /* 11 */
    "PP....yr..............==.ryr.......yr..=......PP", /* 12 */
    "pp....................==...............=......pp", /* 13 */
    "PP........=.....=.....==.......=.......=......PP", /* 14 */
    "pp============================================pp", /* 15 */
    "PP============================================PP", /* 16 */
    "pp....................==................==....pp", /* 17 */
    "PP..P.........P.......==................==......", /* 18 */
    "pp..p.......ryp.......==......yr..P.....========", /* 19 */
    "kkkkkk................==..P.......p.....========", /* 20 */
    "kkkkkk...P............==..p...................PP", /* 21 */
    "kkkkkk...p.......P....==......................pp", /* 22 */
    "kkkkkk...........p.yr.==..ry.........P.....P..PP", /* 23 */
    "kkkkkk................==.............p.....p..pp", /* 24 */
    "kkkkkk................==......=...............PP", /* 25 */
    "kkkkkkqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqpp", /* 26 */
    "kokkkkqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqss", /* 27 */
    "kkkkkkqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqss", /* 28 */
    "kkkkokqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqss", /* 29 */
    "kkok~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 30 */
    "kkkk~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 31 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 32 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 33 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 34 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 35 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 36 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 37 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 38 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 39 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 40 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 41 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 42 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 43 */
};
static const Stamp PORT_BRINE_STAMPS[] = {
    STAMP(CO, HALL, 20, 2), STAMP(CO, HEAL, 8, 10), STAMP(CO, SHOP, 14, 10), STAMP(CO, INN, 29, 10), STAMP(CO, HOUSE_BLUE, 37, 3), STAMP(CO, HARBOR, 28, 21),
};
static const DecorPlace PORT_BRINE_DECOR[] = {
    DP(FISH_STALL, 12, 26), DP(NETS, 6, 26), DP(LOBSTER_POTS, 18, 26), DP(BARREL, 25, 26),
    DP(CRATE_STACK, 26, 26), DP(CRATE, 27, 27), DP(SACKS, 35, 26), DPF(LOBSTER_POTS, 40, 26),
    DP(BARREL, 43, 26), DP(BOLLARD, 8, 29), DP(BOLLARD, 15, 29), DP(BOLLARD, 26, 29),
    DP(BOLLARD, 33, 29), DP(BOLLARD, 38, 29), DP(BOLLARD, 44, 29), DP(ANCHOR, 4, 16),
    DP(LIFEBUOY, 24, 29), DP(SHELL_LAMP, 13, 17), DP(SHELL_LAMP, 20, 17), DP(SHELL_LAMP, 25, 17),
    DP(SHELL_LAMP, 36, 17), DP(BENCH, 26, 8), DP(BENCH, 17, 8), DP(FLOWER_POT, 16, 7),
    DP(FLOWER_POT, 30, 7), DP(SIGNPOST, 19, 9), DP(SIGNPOST, 44, 18), DP(SIGNPOST, 27, 24),
    DP(SIGNPOST, 12, 14), DP(NOTICE_BOARD, 33, 14), DP(MAILBOX, 41, 7), DP(WATER_TROUGH, 7, 17),
    DP(CLOTHESLINE, 42, 11), DP(LIGHTHOUSE, 1, 20), DP(GULL_POST, 5, 30), DP(BRIDGE_V, 10, 30),
    DP(BRIDGE_V, 10, 31), DP(BRIDGE_V, 10, 32), DP(BRIDGE_V, 10, 33), DP(BRIDGE_V, 10, 34),
    DP(FERRY_BOAT, 11, 33), DP(BRIDGE_V, 20, 30), DP(BRIDGE_V, 21, 30), DP(BRIDGE_V, 20, 31),
    DP(BRIDGE_V, 21, 31), DP(BRIDGE_V, 20, 32), DP(BRIDGE_V, 21, 32), DP(BRIDGE_V, 20, 33),
    DP(BRIDGE_V, 21, 33), DP(BRIDGE_V, 20, 34), DP(BRIDGE_V, 21, 34), DP(BRIDGE_V, 20, 35),
    DP(BRIDGE_V, 21, 35), DP(BRIDGE_V, 20, 36), DP(BRIDGE_V, 21, 36), DP(BRIDGE_V, 20, 37),
    DP(BRIDGE_V, 21, 37), DP(BRIDGE_V, 20, 38), DP(BRIDGE_V, 21, 38), DP(BRIDGE_V, 20, 39),
    DP(BRIDGE_V, 21, 39), DP(BRIDGE_V, 20, 40), DP(BRIDGE_V, 21, 40), DP(BRIDGE_V, 20, 41),
    DP(BRIDGE_V, 21, 41), DP(BRIDGE_V, 20, 42), DP(BRIDGE_V, 21, 42), DP(BRIDGE_V, 20, 43),
    DP(BRIDGE_V, 21, 43), DP(BRIDGE_V, 36, 30), DP(BRIDGE_V, 36, 31), DP(BRIDGE_V, 36, 32),
    DP(FISHING_BOAT, 37, 31), DP(FISHING_BOAT, 27, 34), DP(ROWBOAT, 15, 31), DP(PIER_POST, 34, 31),
    DP(PIER_POST, 34, 33), DP(BELL_BUOY, 42, 40), DP(BELL_BUOY, 6, 40), DP(SEA_ROCK, 3, 35),
    DPF(SEA_ROCK, 45, 36), DP(SEA_ROCK, 31, 41), DP(ROCK, 47, 18), DP(ROCK, 47, 27),
    DP(ROCK, 47, 28), DP(ROCK, 47, 29),
};
static const MapObj PORT_BRINE_OBJS[] = {
    OBJ(FERRY, 11, 34, MAP_GULL_ISLE),
};

static const char *const SEA_ROUTE_ROWS[] = {
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /*  0 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /*  1 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /*  2 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /*  3 */
    "~~~~~~~~~~~~~~~~~qqqqqqqq~~~~~~~~~~~~~~~", /*  4 */
    "~~~~~~~~~~~~~~~~~qqqqqqqq~~~~~~~~~~~~~~~", /*  5 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /*  6 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /*  7 */
    "~~~~~~ssssss~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /*  8 */
    "~~~~ssss;;ssAs~~~~~~~~~~~~~~~~~~~~~~~~~~", /*  9 */
    "~~~sss;;;;;;ass~~~~~~~~~~~~~~~~~~~~~~~~~", /* 10 */
    "~~~ss;;;;;;;;ss~~~~~~~~~~~~~~~~~~~~~~~~~", /* 11 */
    "~~~ss;;;;;;;;ss~~~~~~~~~~~~~~~~~~~~~~~~~", /* 12 */
    "~~~sss;;;;;;sss~~~~~~~~~~~~~~~~~~~~~~~~~", /* 13 */
    "~~~~ssss;;ssss~~~~ssss~~~~~~~~~~~~~~~~~~", /* 14 */
    "~~~~~~ssssss~~~~~~ssss~~~~~~~~~~~~~~~~~~", /* 15 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~ssssssss~~~~~~", /* 16 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~sAssssssss~~~~~", /* 17 */
    "~~~~~~~~~~~~~~~~~~~~~~~~ssa;;;;;;sAs~~~~", /* 18 */
    "~~~~~~~~~~~~~~~~~~~~~~~sss;;;;;;;;ass~~~", /* 19 */
    "~~~~~~~~~~~~~~~~~~~~~~~ss;;;;;;;;;;ss~~~", /* 20 */
    "~~~~~~~~~~~~~~~~~~~~~~~ss;;;;;;;;;;ss~~~", /* 21 */
    "~~~~~~~~~~~~~~~~~~~~~~~sss;;;;;;;;sss~~~", /* 22 */
    "~~~~~~~~~~~~~~~~~~~~~~~~sss;;;;;;skkk~~~", /* 23 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~ssssssssskok~~~", /* 24 */
    "~~~~~~~~~~~~~~~~~~~ssss~~~sssssssskkk~~~", /* 25 */
    "~~~~~~~~~~~~~~~~~~~ssss~~~~~~~~~~~~~~~~~", /* 26 */
    "~~~~~~~ssssssss~~~~~~~~~~~~~~~~~~~~~~~~~", /* 27 */
    "~~~~~~ssss;;ssss~~~~~~~~~~~~~~~~~~~~~~~~", /* 28 */
    "~~~~~sA;;;;;;;;ss~~~~~~~~~~~~~~~~~~~~~~~", /* 29 */
    "~~~~~sa;;;;;;;;ss~~~~~~~~~~~~~~~~~~~~~~~", /* 30 */
    "~~~~~ss;;;;;;;;ss~~~~~~~~~~~~~~~~~~~~~~~", /* 31 */
    "~~~~~ss;;;;;;;;ss~~~~~~~~~~~~~~~~~~~~~~~", /* 32 */
    "~~~~~~ssss;;ssss~~~~~~~~~~~~~~kk~~~~~~~~", /* 33 */
    "~~~~~~~ssssssss~~~~~~~~~~~~~kkkkkk~~~~~~", /* 34 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~kkkkkkkk~~~~~", /* 35 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~kkkokkkk~~~~~", /* 36 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~kkkkkk~~~~~~", /* 37 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~kk~~~~~~~~", /* 38 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 39 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 40 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 41 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 42 */
    "~~~~~~~~~~~~~~~~~~~~s~~~~~~~~~~~~~~~~~~~", /* 43 */
    "~~~~~~~~~~~~~~~sssssssssss~~~~~~~~~~~~~~", /* 44 */
    "~~~~~~~~~~~~~sssssssssssssss~~~~~~~~~~~~", /* 45 */
    "~~~~~~~~~~~~sssssssssssssssss~~~~~~~~~~~", /* 46 */
    "~~~~~~~~~~~~sssssssssssssssss~~~~~~~~~~~", /* 47 */
};
static const DecorPlace SEA_ROUTE_DECOR[] = {
    DP(BRIDGE_V, 20, 0), DP(BRIDGE_V, 21, 0), DP(BRIDGE_V, 20, 1), DP(BRIDGE_V, 21, 1),
    DP(BRIDGE_V, 20, 2), DP(BRIDGE_V, 21, 2), DP(BRIDGE_V, 20, 3), DP(BRIDGE_V, 21, 3),
    DP(SIGNPOST, 17, 4), DP(PIER_POST, 16, 5), DP(PIER_POST, 25, 5), DP(BELL_BUOY, 14, 7),
    DP(BELL_BUOY, 27, 30), DP(BELL_BUOY, 4, 42), DP(SEA_ROCK, 3, 4), DPF(SEA_ROCK, 36, 9),
    DP(SEA_ROCK, 20, 20), DP(SEA_ROCK, 37, 30), DPF(SEA_ROCK, 16, 39), DP(SEA_ROCK, 26, 43),
    DP(DRIFTWOOD, 6, 14), DP(DRIFTWOOD, 27, 24), DP(STARFISH, 13, 34), DP(SHELLS, 7, 10),
    DP(GULL_POST, 13, 13), DP(GULL_POST, 32, 34), DP(SEAWEED, 24, 45),
};
static const MapObj SEA_ROUTE_OBJS[] = {
    OBJ(BERRY, 14, 29, 12),
};

static const char *const GULL_ISLE_ROWS[] = {
    "~~~~~~~~~~~~ssssssss==sssssss~~~~~~~~~~~", /*  0 */
    "~~~~~~~~~~~~ssssssss==sssssss~~~~~~~~~~~", /*  1 */
    "~~~~~~~~~~~~~~ssssss==sssss~~~~~~~~~~~~~", /*  2 */
    "~~~~~~~~~~~~~sssssss==sssss~~~~~~~~~~~~~", /*  3 */
    "~~~~~~~~~~~sssssssss==sssssss~~~~~~~~~~~", /*  4 */
    "~~~~~~~~~sssssssssss==ssssssAss~~~~~~~~~", /*  5 */
    "~~~~~~~~sssssAss....==..ssssasss~~~~~~~~", /*  6 */
    "~~~~~~sssssssa......==.....sssssss~~~~~~", /*  7 */
    "~~~~~ssssss.........==.;;..y.ssssss~~~~~", /*  8 */
    "~~~~~sAsss.....ry...==;;;;;;..sssssA~~~~", /*  9 */
    "~~~~ssass..........;==;;;;;;;..ssssa~~~~", /* 10 */
    "~~~sssss.=============;;;;;;;..;;;;ss~~~", /* 11 */
    "~~~ssss..=======================;;;;s~~~", /* 12 */
    "~~~ssss.............============;;;;s~~~", /* 13 */
    "~~ssAs......r....y..==........==;;;;ss~~", /* 14 */
    "~~ssas........................==;;;;ss~~", /* 15 */
    "~~ssss..........A.........A...==;;;sss~~", /* 16 */
    "~~ssssssssssss..a.........a...==..ssss~~", /* 17 */
    "~~sss%%s%%s%%s....................ssss~~", /* 18 */
    "~~ssssssssssss..........CCCCCCCCCCCCss~~", /* 19 */
    "~~~ss%%s%%s%%s..........ccccccccccccs~~~", /* 20 */
    "~~~sssssssssss........sssssssssssssss~~~", /* 21 */
    "~~~ss%%s%%ssss........sssssssssssssss~~~", /* 22 */
    "~~~~ssssssssss..;;;;..ssssssssssssss~~~~", /* 23 */
    "~~~~ssssssssss;;;;;;;;ssssssssssssss~~~~", /* 24 */
    "~~~~~ssssssss.;;;;;;;;ssssssssssssss~~~~", /* 25 */
    "~~~~~~ssssssss;;;;;;;;ssssssssssssss~~~~", /* 26 */
    "~~~~~~~~ssssssss;;;;ssssssssssssssss~~~~", /* 27 */
    "~~~~~~~~~ssssssssssssssssssssss~~~~~~~~~", /* 28 */
    "~~~~~~~~~~~ssssssssssssssssss~~~~~~~~~~~", /* 29 */
    "~~~~~~~~~~~~~ssssssssssssss~~~~~~~~~~~~~", /* 30 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 31 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 32 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 33 */
};
static const Stamp GULL_ISLE_STAMPS[] = {
    STAMP(CO, CAVE, 30, 19), STAMP(CO, HUT, 8, 8),
};
static const DecorPlace GULL_ISLE_DECOR[] = {
    DP(WHALE_ARCH, 30, 22), DP(SALT_HEAP, 12, 22), DP(SALT_HEAP, 13, 23), DP(NETS, 11, 13),
    DP(LOBSTER_POTS, 7, 11), DP(CAMPFIRE, 16, 12), DP(SIGNPOST, 18, 3), DP(SIGNPOST, 28, 26),
    DP(DRIFTWOOD, 24, 27), DP(SHELLS, 34, 25), DP(STARFISH, 21, 29), DP(CRAB_SHELL, 6, 27),
    DP(SEA_ROCK, 1, 20), DPF(SEA_ROCK, 38, 24), DP(GULL_POST, 23, 3), DP(BRIDGE_H, 36, 5),
    DP(BRIDGE_H, 35, 5), DP(BRIDGE_H, 34, 5), DP(BRIDGE_H, 33, 5), DP(BRIDGE_H, 32, 5),
    DP(BRIDGE_H, 31, 5), DP(FERRY_BOAT, 36, 6), DP(PIER_POST, 37, 4),
};
static const MapObj GULL_ISLE_OBJS[] = {
    OBJ(FERRY, 36, 6, MAP_PORT_BRINE), OBJ(BERRY, 26, 13, 13),
};

static const char *const CURRENT_HALL_ROWS[] = {
    "HHHHHHHHHHHHHHH", /*  0 */
    "hhnhhhhhhhhhnhh", /*  1 */
    "OOO_________OOO", /*  2 */
    "OOO_________OOO", /*  3 */
    "OOOOvOOOOO^OOOO", /*  4 */
    "OOOOvOOOOO^OOOO", /*  5 */
    "O___vOOOO____OO", /*  6 */
    "O___>>>>>____OO", /*  7 */
    "O___OOOOO____OO", /*  8 */
    "O___OOOOOOOvOOO", /*  9 */
    "O___OOO>>>>>vOO", /* 10 */
    "OOv^OOO^OOOOvOO", /* 11 */
    "OOv^OOO^OOOOvOO", /* 12 */
    "OOv^OOO^OOOOvOO", /* 13 */
    "O__^O_____OOvOO", /* 14 */
    "O__^<_____<<<OO", /* 15 */
    "O__>>_____OOOOO", /* 16 */
    "OOOOOOOMOOOOOOO", /* 17 */
};
static const DecorPlace CURRENT_HALL_DECOR[] = {
    DP(HALL_COLUMN, 3, 2), DP(HALL_COLUMN, 11, 2), DP(SHELL_LAMP, 5, 2), DP(SHELL_LAMP, 9, 2),
};

static const char *const DROWNED_BELL_ROWS[] = {
    "GGGGGGGGGGGGGGGGGGGG", /*  0 */
    "GGGGGGggggggggGGGGGG", /*  1 */
    "GGGGGgttttttttgGGGGG", /*  2 */
    "GGGGg:tttttttt:gGGGG", /*  3 */
    "GGGg::tttttttt::gGGG", /*  4 */
    "GGg:**tttttttt**:gGG", /*  5 */
    "GG::**tttttttt**::GG", /*  6 */
    "Gg::*****tt*****::gG", /*  7 */
    "G:::*****tt*****:::G", /*  8 */
    "G:::*****tt*****:::G", /*  9 */
    "G::::::::tt::::::::G", /* 10 */
    "GG::::::::':::::::GG", /* 11 */
    "GG:::':::'::::':::GG", /* 12 */
    "GGG:::::::'::::::GGG", /* 13 */
    "GGGG::'::':':'::GGGG", /* 14 */
    "GGGGG:::'::::::GGGGG", /* 15 */
    "GGGGGGG::::::GGGGGGG", /* 16 */
    "GGGGGGGGGmmGGGGGGGGG", /* 17 */
};
static const DecorPlace DROWNED_BELL_DECOR[] = {
    DP(DROWNED_BELL, 8, 2), DP(GROT_PILLAR, 6, 3), DP(GROT_PILLAR, 13, 3), DP(GLOW_CORAL, 3, 12),
    DP(GLOW_CORAL, 16, 11), DP(GLOW_CORAL, 12, 15), DP(WHALE_CARVING, 1, 7),
};
static const MapObj DROWNED_BELL_OBJS[] = {
    OBJ(LEGEND, 11, 8, SP_NOCTHALE),
};


/* ---------------- interiors (tileset 'interior') ---------------- */

static const char *const BRINE_HEARTH_ROWS[] = {
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
static const Stamp BRINE_HEARTH_STAMPS[] = { STAMP(I, RUG, 4, 6) };
static const DecorPlace BRINE_HEARTH_DECOR[] = {
    DP(PLANT, 0, 1), DP(LANTERN_RACK, 3, 1), DP(HEAL_MACHINE, 7, 1), DP(FLOOR_LAMP, 9, 1), DP(PC, 10, 1),
    DP(SHIP_WHEEL, 1, 0), DP(CALENDAR, 9, 0),
    DP(TABLE_ROUND, 1, 5), DP(CHAIR, 1, 4), DP(CHAIR, 2, 4), DP(TEA_SET, 0, 6),
    DP(AQUARIUM, 9, 4), DP(KIN_BASKET, 8, 6), DP(KIN_BASKET, 10, 6), DP(SMALL_PLANT, 10, 7),
};

static const char *const BRINE_SHOP_ROWS[] = {
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
static const DecorPlace BRINE_SHOP_DECOR[] = {
    DP(BARREL_IN, 0, 2), DP(SACKS_IN, 3, 2), DP(NET_WALL, 3, 0), DP(CALENDAR, 7, 0),
    DP(SHOP_SHELF, 5, 1), DP(SHOP_SHELF, 7, 1), DP(LANTERN_RACK, 9, 1),
    DP(DISPLAY_CASE, 6, 5), DP(BARREL_IN, 9, 5), DP(SACKS_IN, 10, 5),
    DP(PLANT, 10, 6), DP(SMALL_PLANT, 0, 7), DP(SMALL_RUG, 5, 7),
};

static const char *const HARBOR_OFFICE_ROWS[] = {
    "WWnWWkWWnWWWW",
    "wwwwwwwwwwwww",
    ".............",
    ".............",
    ".....<===>...",
    ".............",
    ".............",
    ".............",
    "......D......",
};
static const DecorPlace HARBOR_OFFICE_DECOR[] = {
    DP(MAP_POSTER, 3, 0), DP(SHIP_WHEEL, 7, 0), DP(FISH_TROPHY, 10, 0),
    DP(BOOKSHELF, 0, 1), DP(TELEGRAPH, 6, 2), DP(DESK, 8, 2), DP(SHIP_BOTTLE, 11, 2),
    DP(GLOBE, 12, 2), DP(NET_WALL, 11, 0), DP(CHAIR, 1, 7), DP(BARREL_IN, 12, 6),
    DP(SMALL_PLANT, 0, 7), DP(PLANT, 12, 7),
};

static const char *const BRINE_INN_ROWS[] = {
    "WWnWWkWWnWWWW",
    "wwwwwwwwwwwww",
    ".............",
    "<====>.......",
    ".............",
    ".............",
    ".............",
    ".............",
    "......D......",
};
static const Stamp BRINE_INN_STAMPS[] = { STAMP(I, RUG, 8, 5) };
static const DecorPlace BRINE_INN_DECOR[] = {
    DP(STOVE, 0, 1), DP(SINK_COUNTER, 2, 1), DP(ICEBOX, 4, 1), DP(FISH_TROPHY, 7, 0),
    DP(NET_WALL, 9, 0), DP(BED, 11, 2), DP(BED, 11, 5),
    DP(TABLE_ROUND, 1, 5), DP(CHAIR, 0, 5), DP(CHAIR, 3, 5), DP(TABLE_ROUND, 5, 6),
    DP(CHAIR, 4, 6), DP(CHAIR, 7, 6), DP(SHIP_BOTTLE, 8, 2), DP(PLANT, 12, 7), DP(SMALL_PLANT, 0, 7),
};

static const char *const BRINE_HOUSE_ROWS[] = {
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
static const DecorPlace BRINE_HOUSE_DECOR[] = {
    DP(SHIP_BOTTLE, 1, 2), DP(BOOKSHELF_SMALL, 3, 1), DP(FISH_TROPHY, 1, 0), DP(BED, 9, 2),
    DP(TABLE_ROUND, 3, 5), DP(CHAIR, 2, 5), DP(CHAIR, 5, 5), DP(KIN_BASKET, 9, 6),
    DP(NET_WALL, 6, 0), DP(SMALL_PLANT, 0, 7), DP(TOY_BOX, 10, 5),
};

static const char *const GULL_HOUSE_ROWS[] = {
    "WWnWWWWWnWW",
    "wwwwwwwwwww",
    "...........",
    "...........",
    "...........",
    "...........",
    "...........",
    "...........",
    ".....D.....",
};
static const DecorPlace GULL_HOUSE_DECOR[] = {
    DP(FIREPLACE, 4, 1), DP(NET_WALL, 3, 0), DP(SHIP_WHEEL, 7, 0), DP(BED, 9, 2),
    DP(TABLE_ROUND, 2, 5), DP(CHAIR, 1, 5), DP(TEA_SET, 3, 4), DP(BARREL_IN, 0, 2),
    DP(SACKS_IN, 1, 2), DP(KIN_BASKET, 9, 6), DP(SMALL_PLANT, 10, 7),
};


/* ---------------- wild kin ---------------- */

/* SALTWIND TRAIL: dunes and meadow, levels 14-19 */
static const WildSlot WILD_SALTWIND[] = {
    { SP_PEBBOTTER, 20, 14, 18, WHEN_ANY }, { SP_CRANICRAB, 16, 14, 18, WHEN_ANY },
    { SP_PUFFOWL, 12, 15, 18, WHEN_DAY }, { SP_PARASOLE, 12, 14, 18, WHEN_ANY },
    { SP_ZAPPET, 10, 15, 19, WHEN_DAY }, { SP_SKYWISP, 8, 15, 18, WHEN_NIGHT },
    { SP_NOXKIT, 8, 15, 18, WHEN_NIGHT }, { SP_TUXFLAKE, 6, 16, 19, WHEN_ANY },
    { SP_STORMBRELA, 3, 18, 19, WHEN_ANY },
};

/* SEA ROUTE sandbars, levels 22-27 */
static const WildSlot WILD_SANDBARS[] = {
    { SP_CRANICRAB, 20, 22, 26, WHEN_ANY }, { SP_TUXFLAKE, 16, 22, 26, WHEN_ANY },
    { SP_PEBBOTTER, 14, 22, 25, WHEN_ANY }, { SP_STORMBRELA, 12, 23, 27, WHEN_DAY },
    { SP_PARASOLE, 10, 22, 26, WHEN_ANY }, { SP_TORRENTTER, 6, 25, 27, WHEN_ANY },
    { SP_LURELING, 8, 23, 27, WHEN_NIGHT },
};

/* GULL ISLE, levels 24-30 */
static const WildSlot WILD_ISLE[] = {
    { SP_CRYPTCLAW, 16, 25, 29, WHEN_ANY }, { SP_CRANICRAB, 16, 24, 28, WHEN_ANY },
    { SP_STORMBRELA, 14, 25, 29, WHEN_DAY }, { SP_TUXFLAKE, 12, 24, 28, WHEN_ANY },
    { SP_EMPERICE, 6, 28, 30, WHEN_ANY }, { SP_NOXKIT, 10, 24, 28, WHEN_NIGHT },
    { SP_LURELING, 8, 25, 29, WHEN_NIGHT }, { SP_LAMPJINN, 2, 28, 30, WHEN_NIGHT },
};

/* on the water (SURF): the harbour, the Sea Route and the island shores.
 * KELPYRE rises at night (about 2%). */
static const WildSlot WILD_SEA[] = {
    { SP_JELLUME, 22, 22, 28, WHEN_ANY }, { SP_BUBBLIN, 16, 20, 26, WHEN_ANY },
    { SP_PEBBOTTER, 14, 22, 26, WHEN_ANY }, { SP_MEDUSHOCK, 8, 26, 30, WHEN_ANY },
    { SP_LURELING, 12, 22, 28, WHEN_NIGHT }, { SP_ABYSSLURE, 5, 28, 32, WHEN_NIGHT },
    { SP_TORRENTTER, 6, 26, 30, WHEN_DAY }, { SP_KELPYRE, 2, 30, 34, WHEN_NIGHT },
};
