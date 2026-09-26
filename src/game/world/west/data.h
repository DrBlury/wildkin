/*
 * world/west/data.h -- map rows, stamps, decor, objects and wild slots of
 * W-WEST: SALTWIND TRAIL, PORT BRINE (+ interiors, the CURRENT HALL), the
 * SEA ROUTE, GULL ISLE and the DROWNED BELL. Owner: W-WEST.
 *
 * Outdoor maps use the 'coast' tileset, the Current Hall and the grotto the
 * 'tide' tileset (both in tools/tilesets/ts_coast.py); props come from
 * tools/decor_west.py and the village props listed in ts_coast.USES_DECOR.
 * A coast map loads its tileset (~407 tiles) plus every decor kind it uses
 * into 512 scene tiles: a town has ~100 tiles for props (test_west checks
 * every kind fits; one that doesn't is skipped and drawn as garbage).
 * Legend:
 *
 *   outdoor  . grass   , tall grass (kin)   ; marram dune grass (kin)
 *            s sand    = path   ~ sea (surf; sand shore autotile)
 *            # plaza slabs   q quay setts   k rock shelf   o tide pool
 *            % salt pan   l dune ledge (hop south)
 *            r y flowers   P/p pine top/bottom   A/a palm top/bottom
 *            Cliffs, stairs, ledges, bridges, tunnels and hidden passages
 *            are the height layer (*_ELEV, *_FEATS; docs/ELEVATION.md).
 *            SALTWIND, PORT BRINE and GULL ISLE have one
 *            (docs/handoff/towns_west.md).
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
    "PPPP.....PPP.P..........PPPPP.......PPPPPPPPPPPP", /*  2 */
    "pppp.........p..........ppppp.......pppppppppppp", /*  3 */
    "P.P.....ry=y..y...........P...........P...P.PP.P", /*  4 */
    "p.p.....y.=.r.............p..r........p...p.pp.p", /*  5 */
    "P.......r.=.y.#........###.........yy......P..PP", /*  6 */
    "p.........=..#############......=..........p..pp", /*  7 */
    "P....=======###############=======.......P..P..P", /*  8 */
    "p....=.......#############.=....==r==y===p..p..p", /*  9 */
    "P.ry.=.......###.....=....................P...PP", /* 10 */
    "p....=.......###.....=......r.............p...pp", /* 11 */
    "~P...=.......###.....=..................=...P..P", /* 12 */
    "~p..==y..ssss........=.~~~qqy...........=...p..p", /* 13 */
    "~.P.=....ssss........=.~~~qq............=..P.P.P", /* 14 */
    "~.p.=....ssssry......=.~~~qq............=..p.p.p", /* 15 */
    "~s..=..P.ssss...=======~~~qq......=======r.....P", /* 16 */
    "~s..=..p.....==========~~~qq=============......p", /* 17 */
    "~s.P=....yr...ry...=...~~~qq=======....==.......", /* 18 */
    "~~.p=.......y...r..=...~~~qq..=....yr..=========", /* 19 */
    "~P..==.r...............~~~qq..=..ry....=========", /* 20 */
    "~p...=...qqqqqqqqqqqqqq~~~qq..=.....y.....ry...P", /* 21 */
    "~.P..====qqqqqqqqqqqqqq~~~qq..=................p", /* 22 */
    "~.p..=...qqqqqqqqqqqqqq~~~qqqqqqqq..............", /* 23 */
    "~..r.=...qqqqqqqqqqqqqq~~~qqqqqqqqqqqqqqqkkkkk~~", /* 24 */
    "~~...=...qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqkkkkk~~", /* 25 */
    "~~...=...qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqkkokkk~", /* 26 */
    "~~...=..~ssss~~~~~~~~~~~~~~~~~~~~~~~qq~~~kokkkk~", /* 27 */
    "~~......~ssss~~~~~~~~~~~~~~~~~~~~~~~qq~~~kkkkkk~", /* 28 */
    "~~....y.~s~~~~~~~~~~~~~~~~~~~~~~~~~~qq~~~~~kkok~", /* 29 */
    "~~r.....~~~~~~~~~~~~~~~~~~~~~~~~~~~~qq~~~~kkkkk~", /* 30 */
    "~~......~~~~~~~~~~~~~~~~~~~~~~~~~~~~qq~~~~~~kk~~", /* 31 */
    "~~......~~~~~~~~~~~~~~~~~~~~~~~~~~~~qq~~~~~~~~~~", /* 32 */
    "~~......~~~~~~~~~~~~~~~~~~~~~~qqqqqqqq~~~~~~~~~~", /* 33 */
    "~~......~~~~~~~~~~~~~~~~~~~~~~qqqqqqqq~~~~~~~~~~", /* 34 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 35 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 36 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 37 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 38 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 39 */
};

/* heights (docs/ELEVATION.md): the upper town, LAMP HEAD and the east bluff 3, the
 * terraces 1, the quays, the Gut and the Smugglers' Hollow 0 */
static const char *const PORT_BRINE_ELEV[] = {
    "333333333333333333333333333333333333333333333333", /*  0 */
    "333333333333333333333333333333333333333333333333", /*  1 */
    "333333333333333333333333333333333333333333333333", /*  2 */
    "333333332222233333333333333333333333333333333333", /*  3 */
    "333333332222233333333333333333333333333333333333", /*  4 */
    "333333332222233333333333333333333333333333333333", /*  5 */
    "333333332222233333333333333333333333333333333333", /*  6 */
    "3333333333v3333333333333333333333333333333333333", /*  7 */
    "333333333333333333333333333333333333333333333333", /*  8 */
    "333333333333333333333333333333333333333333333333", /*  9 */
    "333333333000033311111^10000^333333311111^3333333", /* 10 */
    "333333333000033311111^10000^111111111111^3333333", /* 11 */
    "033333333000033311111110000^11111111111113333333", /* 12 */
    "033333333000011111111110000011111111111113333333", /* 13 */
    "033333333000011111111110000011111111111111133333", /* 14 */
    "033333333000011111111110000011111111111111133333", /* 15 */
    "003333333000011111111110000011111111111111133333", /* 16 */
    "003333333101111111111110000011111111111111111111", /* 17 */
    "003333333101111111111110000011111111111111111111", /* 18 */
    "003333333101111111111110000011111111111111111111", /* 19 */
    "0333333330000000000^0__0000011111111111111111111", /* 20 */
    "033333333000000000000000000011111111111111111111", /* 21 */
    "033333<<<000000000000000000000^00011111111111111", /* 22 */
    "03333333300000000000000000000000000000000000___0", /* 23 */
    "033333333000000000000000000000000000000000000000", /* 24 */
    "003333330000000000000000000000000000000000000000", /* 25 */
    "003333330000000000000000000000000000000000000000", /* 26 */
    "003333330000000000000000000000000000000000000000", /* 27 */
    "003333330000000000000000000000000000000000000000", /* 28 */
    "003333330000000000000000000000000000000000000000", /* 29 */
    "003333330000000000000000000000000000000000000000", /* 30 */
    "003333330000000000000000000000000000000000000000", /* 31 */
    "000000000000000000000000000000000000000000000000", /* 32 */
    "000000000000000000000000000000000000000000000000", /* 33 */
    "000000000000000000000000000000000000000000000000", /* 34 */
    "000000000000000000000000000000000000000000000000", /* 35 */
    "000000000000000000000000000000000000000000000000", /* 36 */
    "000000000000000000000000000000000000000000000000", /* 37 */
    "000000000000000000000000000000000000000000000000", /* 38 */
    "000000000000000000000000000000000000000000000000", /* 39 */
};

static const ElevFeat PORT_BRINE_FEATS[] = {
    EF(BRIDGE_H, 23, 16, 5, 2),  /* ROPE WALK over the Gut: the road over, the lane (and the tide) under */
    EF(TUNNEL, 10, 17, 1, 3),    /* the smugglers' run under the west terrace ... */
    EF(HIDDEN, 10, 20, 1, 1),    /* ... behind a crack in the quay wall */
};
static const Stamp PORT_BRINE_STAMPS[] = {
    STAMP(CO, HALL, 16, 2), STAMP(CO, HOUSE_BLUE, 30, 3), STAMP(CO, HEAL, 16, 12), STAMP(CO, SHOP, 29, 13), STAMP(CO, INN, 35, 12), STAMP(CO, HARBOR, 12, 21),
};
static const DecorPlace PORT_BRINE_DECOR[] = {
    DP(LIGHTHOUSE, 3, 26), DP(FERRY_BOAT, 27, 33), DP(FISH_STALL, 17, 22), DP(SIGNPOST, 23, 7),
    DP(SIGNPOST, 45, 21), DP(SIGNPOST, 18, 25), DP(SIGNPOST, 15, 16), DP(SIGNPOST, 9, 4),
    DP(SHELL_LAMP, 13, 10), DP(SHELL_LAMP, 26, 6), DP(SHELL_LAMP, 22, 14), DP(SHELL_LAMP, 28, 15),
    DP(SHELL_LAMP, 38, 17), DP(SHELL_LAMP, 34, 22), DP(SHELL_LAMP, 11, 23), DP(SHELL_LAMP, 4, 12),
    DP(BOLLARD, 13, 26), DP(BOLLARD, 17, 26), DP(BOLLARD, 24, 26), DP(BOLLARD, 29, 26),
    DP(BOLLARD, 34, 26), DP(BOLLARD, 36, 34), DP(BOLLARD, 32, 34), DP(BARREL, 21, 23),
    DP(BARREL, 29, 23), DP(LOBSTER_POTS, 22, 23), DP(LOBSTER_POTS, 39, 24), DP(BARREL, 37, 28),
    DP(PIER_POST, 19, 30), DP(PIER_POST, 22, 34), DP(BARREL, 12, 13), DP(LOBSTER_POTS, 9, 16),
    DP(BARREL, 12, 16), DP(BELL_BUOY, 14, 34), DP(BELL_BUOY, 42, 36), DP(SEA_ROCK, 9, 31),
    DP(SEA_ROCK, 44, 33), DP(SEA_ROCK, 3, 37), DP(SEA_ROCK, 26, 38), DP(SEA_ROCK, 39, 30),
    DP(SEA_ROCK, 0, 22), DP(BRIDGE_V, 20, 27), DP(BRIDGE_V, 21, 27), DP(BRIDGE_V, 20, 28),
    DP(BRIDGE_V, 21, 28), DP(BRIDGE_V, 20, 29), DP(BRIDGE_V, 21, 29), DP(BRIDGE_V, 20, 30),
    DP(BRIDGE_V, 21, 30), DP(BRIDGE_V, 20, 31), DP(BRIDGE_V, 21, 31), DP(BRIDGE_V, 20, 32),
    DP(BRIDGE_V, 21, 32), DP(BRIDGE_V, 20, 33), DP(BRIDGE_V, 21, 33), DP(BRIDGE_V, 20, 34),
    DP(BRIDGE_V, 21, 34), DP(BRIDGE_V, 20, 35), DP(BRIDGE_V, 21, 35), DP(BRIDGE_V, 20, 36),
    DP(BRIDGE_V, 21, 36), DP(BRIDGE_V, 20, 37), DP(BRIDGE_V, 21, 37), DP(BRIDGE_V, 20, 38),
    DP(BRIDGE_V, 21, 38), DP(BRIDGE_V, 20, 39), DP(BRIDGE_V, 21, 39),
};
static const MapObj PORT_BRINE_OBJS[] = {
    OBJ(FERRY, 29, 34, MAP_GULL_ISLE),
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
    "~~~~~~~~~~~~~~~~sssssssss~~~~~~~~~~~~~~~", /* 45 */
    "~~~~~~~~~~~~~~~~~~ssssss~~~~~~~~~~~~~~~~", /* 46 */
    "~~~~~~~~~~~~~~~~~~~~ss~~~~~~~~~~~~~~~~~~", /* 47 */
};
static const DecorPlace SEA_ROUTE_DECOR[] = {
    DP(BRIDGE_V, 20, 0), DP(BRIDGE_V, 21, 0), DP(BRIDGE_V, 20, 1), DP(BRIDGE_V, 21, 1),
    DP(BRIDGE_V, 20, 2), DP(BRIDGE_V, 21, 2), DP(BRIDGE_V, 20, 3), DP(BRIDGE_V, 21, 3),
    DP(SIGNPOST, 17, 4), DP(PIER_POST, 16, 5), DP(PIER_POST, 25, 5), DP(BELL_BUOY, 14, 7),
    DP(BELL_BUOY, 27, 30), DP(BELL_BUOY, 4, 42), DP(SEA_ROCK, 3, 4), DPF(SEA_ROCK, 36, 9),
    DP(SEA_ROCK, 20, 20), DP(SEA_ROCK, 37, 30), DPF(SEA_ROCK, 16, 39), DP(SEA_ROCK, 26, 43),
    DP(DRIFTWOOD, 6, 14), DP(DRIFTWOOD, 27, 24), DP(STARFISH, 13, 34), DP(SHELLS, 7, 10),
    DP(GULL_POST, 13, 13), DP(GULL_POST, 32, 34), DP(SEAWEED, 22, 45),
};
static const MapObj SEA_ROUTE_OBJS[] = {
    OBJ(BERRY, 14, 29, 12),
};

static const char *const GULL_ISLE_ROWS[] = {
    "~~~~~~~~~~~~~~~~~~~~ss~~~~~~~~~~~~~~~~~~", /*  0 */
    "~~~~~~~~~~~~~~~~~~~ssss~~~~~~~~~~~~~~~~~", /*  1 */
    "~~~~~~~~~~~~~~~~~~ssssss~~~~~~~~~~~~~~~~", /*  2 */
    "~~~~~~~~~~~~~~~~ssssssssss~~~~~~~~~~~~~~", /*  3 */
    "~~~~~~AAsssssssssssssssssssssss~~~~~~~~~", /*  4 */
    "~~~sssaasA;;;;ssssssssssssssssssss~~~~~~", /*  5 */
    "~~ssssAAsa;;;;ssssssssAssssAsssssss~~~~~", /*  6 */
    "~~ssssaasssssss=ssssssassssassssssss~~~~", /*  7 */
    "~~~~~~AAss.....=....sssssssss.....sss~~~", /*  8 */
    "~~~~~~aa.....ry=......ssssss.......ss~~~", /*  9 */
    "~~~~sAs........=..y....ssss.........s~~~", /* 10 */
    "~~~~sa.........=.....r..sss....y....s~~~", /* 11 */
    "~~~~ss.y...=====........sss.........s~~~", /* 12 */
    "~~~~~~.........========.sss===...r..s~~~", /* 13 */
    "~~~~~s......=..=========sss====.....s~~~", /* 14 */
    "~~~~ss.,,,,.=.......=...sss...=.....s~~~", /* 15 */
    "~~~~ss.,,,,.=...,,,,=...sss...=.....s~~~", /* 16 */
    "~~~~As.,,,,.=.y.,,,,=...sss.,,===,,.s~~~", /* 17 */
    "~~~~ass,,,,.=...,,,,=...sss.,A,,,,,.~~~~", /* 18 */
    "~~~~ssss....=...,,,,=...ssss,a,,,,A.~~~~", /* 19 */
    "~~~~sssss...=.......=..sssss,,,,,,as~~~~", /* 20 */
    "~~~~sssssss.s....ss.ssssssss,,,,,,,ss~~~", /* 21 */
    "~~~~~ssssssssssssssssssssssss......ss~~~", /* 22 */
    "~~~~ss%s%s%ss;;;;;;sssssss;;ssss..sss~~~", /* 23 */
    "~~~~sssssssss;;;;;;sssssss;;sssssssss~~~", /* 24 */
    "~~~~ss%s%s%ss;;;;;;ssssssssssssssAss~~~~", /* 25 */
    "~~~~~ssssssss;;;;;;sssssssssss;;;as~~~~~", /* 26 */
    "~~~~~~~ssssssAssssssssAsssssss;;;s~~~~~~", /* 27 */
    "~~~~~~~~~ssssassssssssasssssssss~~~~~~~~", /* 28 */
    "~~~~~~~~~~~~sssssssssssssssss~~~~~~~~~~~", /* 29 */
    "~~~~~~~~~~~~~~~ssssssssss~~~~~~~~~~~~~~~", /* 30 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 31 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 32 */
    "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~", /* 33 */
};

/* heights (docs/ELEVATION.md): beaches 0, the Green and the stack 1, Gull Crag 2 */
static const char *const GULL_ISLE_ELEV[] = {
    "0000000000000000000000000000000000000000", /*  0 */
    "0000000000000000000000000000000000000000", /*  1 */
    "0000000000000000000000000000000000000000", /*  2 */
    "0000000000000000000000000000000000000000", /*  3 */
    "0000000000000000000000000000000000000000", /*  4 */
    "0000000000000000000000000000000000000000", /*  5 */
    "0000000000000000000000000000000000000000", /*  6 */
    "0000000000000000000000000000000000000000", /*  7 */
    "000000000011111v111100000000011111000000", /*  8 */
    "0000000011111111111111000000111111100000", /*  9 */
    "0000000111111111111111100001112222110000", /* 10 */
    "0000001111111111111111110001112222210000", /* 11 */
    "0000001111111111111111110001111222210000", /* 12 */
    "0000000111111111111111110001111222210000", /* 13 */
    "0000001111111111111111110001111122200000", /* 14 */
    "0000001111111111111111100001111122110000", /* 15 */
    "00000011111111111111111100011111^1110000", /* 16 */
    "0000000111111111111111110001111111110000", /* 17 */
    "0000000011111111111111110000111111110000", /* 18 */
    "0000000001111111111111100000111111100000", /* 19 */
    "0000000000011111111110000000111111100000", /* 20 */
    "000000000000^0000__0^0000000011111100000", /* 21 */
    "0000000000000000000000000000011011000000", /* 22 */
    "00000000000000000000000000000__000000000", /* 23 */
    "0000000000000000000000000000000000000000", /* 24 */
    "0000000000000000000000000000000000000000", /* 25 */
    "0000000000000000000000000000000000000000", /* 26 */
    "0000000000000000000000000000000000000000", /* 27 */
    "0000000000000000000000000000000000000000", /* 28 */
    "0000000000000000000000000000000000000000", /* 29 */
    "0000000000000000000000000000000000000000", /* 30 */
    "0000000000000000000000000000000000000000", /* 31 */
    "0000000000000000000000000000000000000000", /* 32 */
    "0000000000000000000000000000000000000000", /* 33 */
};

static const ElevFeat GULL_ISLE_FEATS[] = {
    EF(BRIDGE_H, 24, 13, 3, 2),  /* the rope bridge: the Green to the stack over the gully, the gully path under */
    EF(TUNNEL, 31, 22, 1, 1),    /* the sea cave's throat: its mouth (31,23) is the DROWNED BELL door */
    EF(HIDDEN, 6, 7, 2, 1),      /* through the palm grove to the secret cove */
};
static const Stamp GULL_ISLE_STAMPS[] = {
    STAMP(CO, HUT, 10, 9), STAMP(CO, CAVE, 31, 23),
};
static const DecorPlace GULL_ISLE_DECOR[] = {
    DP(WHALE_ARCH, 14, 27), DP(FERRY_BOAT, 36, 6), DP(PIER_POST, 37, 4), DP(SIGNPOST, 18, 3),
    DP(SIGNPOST, 28, 25), DP(SALT_HEAP, 12, 24), DP(SALT_HEAP, 5, 24), DP(NETS, 11, 13),
    DP(LOBSTER_POTS, 7, 10), DP(CAMPFIRE, 17, 11), DP(DRIFTWOOD, 22, 29), DP(SHELLS, 3, 7),
    DP(STARFISH, 21, 28), DP(CRAB_SHELL, 8, 27), DP(SHELLS, 35, 22), DP(SEA_ROCK, 1, 20),
    DP(SEA_ROCK, 38, 24), DP(SEA_ROCK, 1, 9), DP(SEA_ROCK, 4, 3), DP(SEA_ROCK, 30, 31),
    DP(GULL_POST, 23, 3), DP(GULL_POST, 31, 10), DP(GULL_POST, 33, 13), DP(BRIDGE_H, 31, 5),
    DP(BRIDGE_H, 32, 5), DP(BRIDGE_H, 33, 5), DP(BRIDGE_H, 34, 5), DP(BRIDGE_H, 35, 5),
    DP(BRIDGE_H, 36, 5),
};
static const MapObj GULL_ISLE_OBJS[] = {
    OBJ(FERRY, 36, 6, MAP_PORT_BRINE), OBJ(BERRY, 28, 11, 13),
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
