/*
 * world/far/data.h -- map rows, stamps, decor, objects and wild slots of
 * the FAR region (owner: W-FAR): CINDER ROAD, CINDERMOOR (+ hearth, shop,
 * forge, ANVIL HALL), EMBER TUNNEL, CALDERA HEART, MOONVEIL PATH,
 * DREAMSPIRE (+ hearth, shop, MIRROR HALL) and the DUST LIBRARY.
 *
 * Exits (docs/EXPANSION.md 9):
 *   CINDER ROAD west  y 20-21 <-> LUMEN CITY east
 *   CINDER ROAD east  y 20-21 <-> CINDERMOOR west
 *   MOONVEIL PATH south x 24-25 <-> LUMEN CITY north
 *   MOONVEIL PATH north x 24-25 <-> DREAMSPIRE south
 *   Cindermoor's cave mouth (37,4) -> EMBER TUNNEL; its arch (21,3) -> CALDERA HEART
 *   Dreamspire's library door (39,18) -> the DUST LIBRARY
 *
 * Legend, volcanic (tools/tilesets/ts_volcanic.py):
 *   . ash   , ember brush (wild kin)   : basalt   # setts   y sulfur
 *   = cinder path   ~ hot spring   C cliff   c cliff face   L [ ] ledge
 *   T/t crag spire (top/bottom)   D/d charred tree   r j rails
 *   _ cave floor   ; ember moss (wild kin)   M cave rock   m cave face
 *   x cave exit   + iron deck   v vent   H/h hall wall   X hall mat
 *   lava as a numpad: 7 8 9 / 4 5 6 / 1 2 3, q p b n inner corners,
 *   - | one-cell streams, o a single pool
 * Legend, dream (tools/tilesets/ts_dream.py):
 *   . moon grass   , moonpetals (wild kin)   f moonflowers   # moonstone
 *   = moonstone path   ~ moon pond   C c cliff   L [ ] ledge
 *   T/t blossom tree   + mirror floor   * star inlay (pads)
 *   M/m mirror wall   X hall mat   _ plum boards   ; paper dust (wild kin)
 *   B/b bookshelves   x library mat
 */

/* ================================================================ */
/*  CINDER ROAD                                                     */
/* ================================================================ */

static const char *const CINDER_ROAD_ROWS[] = {
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT", /*  0 */
    "tttttttttttttttttttttttttttttttttttttttttttt", /*  1 */
    "TT.........D...D......TT..D...............TT", /*  2 */
    "tt.,,,,....d...d......tt..d..D.....,,,,,,.tt", /*  3 */
    "TT.,,,,......................d.....,,,,,,.TT", /*  4 */
    "tt.,,,,............................,,,,,,.tt", /*  5 */
    "TT.,,,,.==========================.,,,,,,.TT", /*  6 */
    "tt.,,,,.==========================.,,,,,,.tt", /*  7 */
    "TT.,,,,.==......................==.,,,,,,.TT", /*  8 */
    "tt.,,,,.==.yy::::::::::::::::::.==.,,,,,,.tt", /*  9 */
    "TT.,,,,.==.::::788888888889::::.==.,,,,,,.TT", /* 10 */
    "tt.,,,,.==.::78q5555555555p9:::.==........tt", /* 11 */
    "TT......==.::455555555555556:::.==[LLLLLL]TT", /* 12 */
    "tt......==.::455555555555556:::.==........tt", /* 13 */
    "TT..D...==.::1b5555555555n23:::.==....D...TT", /* 14 */
    "tt..d...==.:::122222222223:::::.==....d...tt", /* 15 */
    "TT......==.:::::::78889:::::yyy.==........TT", /* 16 */
    "tt......==.yyy::::12223:::::yyy.==.....TT.tt", /* 17 */
    "TT......==.yyy::::::::::::::yyy.==.....tt.TT", /* 18 */
    "tt......==......T...............==........tt", /* 19 */
    "==========......t...............============", /* 20 */
    "==========..,,,,,,,,,,..........============", /* 21 */
    "TT...D..==..,,,,,,,,,,..,,,,,............DTT", /* 22 */
    "tt...d..==..,,,,,,,,,,..,,,,,............dtt", /* 23 */
    "TT......==..,,,,,,,,,,..,,,,,.D....,,,,,,.TT", /* 24 */
    "tt......==..,,,,,,,,,,..,,,,,.d....,,,,,,.tt", /* 25 */
    "TT.~~~~.==.........................,,,,,,.TT", /* 26 */
    "tt.~~~~.===============............,,,,,,.tt", /* 27 */
    "TT.~~~~.===============rrrrrrrrrrrr,,,,,,.TT", /* 28 */
    "tt.~~~~............................,,,,,,.tt", /* 29 */
    "TT.~~~~....:::D:::::::::::TT:::::T.,,,,,,.TT", /* 30 */
    "tt.~~~.....:::d:::::D:::::tt:::::t.,,,,,,.tt", /* 31 */
    "TT..................d.....................TT", /* 32 */
    "tt........................................tt", /* 33 */
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT", /* 34 */
    "tttttttttttttttttttttttttttttttttttttttttttt", /* 35 */
};
static const DecorPlace CINDER_ROAD_DECOR[] = {
    DP(SIGNPOST, 3, 18), DP(SIGNPOST, 40, 18),
    DP(STEAM_VENT, 11, 8), DP(STEAM_VENT, 29, 15), DP(STEAM_VENT, 12, 16),
    DP(OBSIDIAN, 17, 9), DP(OBSIDIAN, 24, 17), DP(EMBER_ROCK, 29, 11), DP(EMBER_ROCK, 11, 12),
    DP(STEAM_VENT, 7, 25), DP(LAVA_ORE_CART, 30, 28), DP(COAL_PILE, 34, 27), DP(CAMPFIRE, 14, 33),
    DP(WOODPILE, 16, 33), DP(OBSIDIAN, 36, 13), DP(EMBER_ROCK, 23, 31),
};

/* ================================================================ */
/*  CINDERMOOR                                                    */
/* ================================================================ */

/*
 * CINDERMOOR climbs the flank of the volcano in three steps, split by the
 * rail cut and hemmed in by the lava river:
 *   - the LOWER WARD (height 0): the west gate (edge y 20-21), the Hearth,
 *     the public hot springs spilling off the west edge;
 *   - the WEST TERRACE (1): the Bell Plaza and the shop, reached by the
 *     road's side stairs (12,20-21); the OLD QUARTER bluff (2) above it
 *     (side stairs 12,7; a 2-high face with stairs 9,12-13 down to the ward);
 *   - the RAIL CUT (0): the mine rails run from the EMBER TUNNEL mouth
 *     (23,4) south to the slag yard, UNDER the Iron Bridge (22-25,17-18)
 *     that carries the plaza road OVER the cut to the forge ward;
 *   - the FORGE WARD (1) east of the cut and the ANVIL CRAG (2) above it
 *     (stairs 38,11) with the ANVIL HALL; ledges drop from both terraces
 *     into the SLAG YARD (0), where the rails tip ore into the lava pool.
 * A hidden gap in the crags above the Old Quarter (8,3-4, hint: the path
 * stub) leads to the smiths' secret soak (satchel + an old smith).
 */
static const char *const CINDERMOOR_ROWS[] = {
    "TTTTTttttttTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.456TTT", /*  0 */
    "ttttt....~~tttttttttttttttttttttttttttttt.456ttt", /*  1 */
    "TTTTT....~~T..........CCCC:TTTT::::::::TT.456TTT", /*  2 */
    "tttttTTTTTTt.......TTTcccc:tttt::::::::tt.456ttt", /*  3 */
    "TT...tttttt........tttcccc:::::::::::::::.456TTT", /*  4 */
    "tt......=:::........TT:j==:::::::::::::::.456ttt", /*  5 */
    "T.......=:::=.......tt:j==:::::::::::::::.456TTT", /*  6 */
    "t:..........=======...:j==:::::::::::::::.456ttt", /*  7 */
    "T:..........=.....=...:j==:::::#######:::7q56TTT", /*  8 */
    "t:................=...:j==:::::####======4556ttt", /*  9 */
    "T..=======........=...:j==...............4556TTT", /* 10 */
    "t........=........=...:j==...............4556ttt", /* 11 */
    "..................=...:j==............=..4556TTT", /* 12 */
    "..............########:j==............=D.1b56ttt", /* 13 */
    "TT.......=....########:j==............=d..45p9TT", /* 14 */
    "tt.......=...D########:j==............=...4556tt", /* 15 */
    "TT.......=...d########:j==............=...4556TT", /* 16 */
    "tt.......=....########:j==###############.4556tt", /* 17 */
    "T........=....########:j==###############.4556TT", /* 18 */
    "t....=...=....########:j==....=.....=.....4556tt", /* 19 */
    "============.#########:j==.D..=..::.=yyyy.4556TT", /* 20 */
    "============.#########:j==.d.....::.=yyyy.45n3tt", /* 21 */
    "T..D.....=......=.....:j==.......::.=....7q56TTT", /* 22 */
    "t..d.....=......=..D..:j==.......::.=...D4556ttt", /* 23 */
    "~~~......=......=yyd..:j==.......::.=...d4556TTT", /* 24 */
    "~~~~~....==.....=yy...:j==..........=....4556ttt", /* 25 */
    "~~~~~~~...=.....=yy...:j==.......D.===...4556TTT", /* 26 */
    "~~~~~~~...=.....=.....:j==.......d......7q556ttt", /* 27 */
    "~~~~~.....=...........:j==..............4555p9TT", /* 28 */
    "~~......D.==..........:j==.............7q5555p9t", /* 29 */
    "TT......d..=....yyyyyy:j==::::::......7q555555p8", /* 30 */
    "tt.........=D...yyyyyy:j==::::::....78q555555555", /* 31 */
    "TT.........=d.........:j==::::::..78q55555555555", /* 32 */
    "tt.........=..........:jrrrrrrrrr7q5555555555555", /* 33 */
    "TTT..=================....::::::.455555555555555", /* 34 */
    "ttt.........,,,,,,,,,,..........-q55555555555555", /* 35 */
    "TTTT.....TTT,,,,,,,,,,.....TTTT..1b5555555555555", /* 36 */
    "tttt.....ttt,,,,,,,,,,.....tttt...1b555555555555", /* 37 */
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.1b55555555555", /* 38 */
    "tttttttttttttttttttttttttttttttttt..455555555555", /* 39 */
};

/* heights (0-3), stairs (^ v < >) and ledges (_): docs/ELEVATION.md */
static const char *const CINDERMOOR_ELEV[] = {
    "222222222222222222222200003333333333333333000000", /*  0 */
    "222222222222222222222200003333333333333333000000", /*  1 */
    "222222222222111111111100003333333333333333000000", /*  2 */
    "222222222222111111111100003333333333333333000000", /*  3 */
    "222222222222111111111100003333333333333333000000", /*  4 */
    "222222222222111111111100003333333333333333000000", /*  5 */
    "222222222222111111111100003333333333333333000000", /*  6 */
    "222222222222<11111111100003333333333333333000000", /*  7 */
    "222222222222111111111100003333333333333330000000", /*  8 */
    "222222222222111111111100003333333333333330000000", /*  9 */
    "22222222222211111111110000111111111111^110000000", /* 10 */
    "22222222220011111111110000111111111111^110000000", /* 11 */
    "000000000^00111111111100001111111111111110000000", /* 12 */
    "000000000^00111111111100001111111111111110000000", /* 13 */
    "000000000000111111111100001111111111111111000000", /* 14 */
    "000000000000111111111100001111111111111111000000", /* 15 */
    "000000000000111111111100001111111111111111000000", /* 16 */
    "000000000000111111111100001111111111111111000000", /* 17 */
    "000000000000111111111100001111111111111111000000", /* 18 */
    "000000000000111111111100001111111111111111000000", /* 19 */
    "000000000000>11111111100001111111111111111000000", /* 20 */
    "000000000000>11111111100001111111111111111000000", /* 21 */
    "000000000000001111111100001111111111111110000000", /* 22 */
    "000000000000001111111100001111111111111110000000", /* 23 */
    "000000000000001111111100001111111111111110000000", /* 24 */
    "000000000000000011111100001111111111111110000000", /* 25 */
    "000000000000000011111100001111111110^00000000000", /* 26 */
    "000000000000000011100000001111111110000000000000", /* 27 */
    "0000000000000000^__00000001111111100000000000000", /* 28 */
    "0000000000000000000000000000___00000000000000000", /* 29 */
    "000000000000000000000000000000000000000000000000", /* 30 */
    "000000000000000000000000000000000000000000000000", /* 31 */
    "000000000000000000000000000000000000000000000000", /* 32 */
    "000000000000000000000000000000000000000000000000", /* 33 */
    "000000000000000000000000000000000000000000000000", /* 34 */
    "000000000000000000000000000000000000000000000000", /* 35 */
    "000000000000000000000000000000000000000000000000", /* 36 */
    "000000000000000000000000000000000000000000000000", /* 37 */
    "000000000000000000000000000000000000000000000000", /* 38 */
    "000000000000000000000000000000000000000000000000", /* 39 */
};

static const ElevFeat CINDERMOOR_FEATS[] = {
    EF(BRIDGE_H, 22, 17, 4, 2),  /* the Iron Bridge: the plaza road over, the rails under */
    EF(HIDDEN, 8, 3, 1, 2),      /* through the crags to the smiths' soak */
};
static const Stamp CINDERMOOR_STAMPS[] = {
    STAMP(VO, HEARTH, 3, 15),       /* CINDER HEARTH HALL, door 5,18 */
    STAMP(VO, SHOP, 13, 9),         /* CINDER SHOP, door 15,12 */
    STAMP(VO, FORGE, 27, 13),       /* THE FORGE, door 29,16 */
    STAMP(VO, HOUSE, 33, 13),
    STAMP(VO, ANVIL_HALL, 31, 3),   /* ANVIL HALL, door 34,7 */
    STAMP(VO, HOUSE_RUST, 2, 6),
    STAMP(VO, HOUSE_RUST, 28, 21),
    STAMP(VO, HOUSE, 3, 30),
    STAMP(VO, CAVE_MOUTH, 22, 3),   /* the EMBER TUNNEL, door 23,4 */
};
static const DecorPlace CINDERMOOR_DECOR[] = {
    DP(BIG_BELL, 16, 16), DP(SIGNPOST, 2, 19), DP(SIGNPOST, 30, 8), DP(SIGNPOST, 25, 6),
    DP(LANTERN_POST, 14, 13), DP(LANTERN_POST, 20, 13), DP(LANTERN_POST, 14, 18), DP(LANTERN_POST, 20, 21),
    DP(BRAZIER, 33, 8), DP(BRAZIER, 35, 8), DP(BRAZIER, 21, 16), DP(BRAZIER, 21, 19), DP(BRAZIER, 26, 16),
    DP(BRAZIER, 26, 19), DP(BRAZIER, 8, 11),
    DP(SMOKE, 28, 12), DP(SMOKE, 30, 12), DP(SMOKE, 36, 12), DP(SMOKE, 30, 20), DP(SMOKE, 4, 5), DP(SMOKE, 6, 29),
    DP(BARREL, 32, 14), DP(CRATE, 32, 15), DP(COAL_PILE, 26, 14), DP(LAVA_ORE_CART, 30, 32), DP(COAL_PILE, 29, 31),
    DP(BENCH, 18, 20), DP(WATER_TROUGH, 9, 17), DP(SACKS, 19, 11), DP(WOODPILE, 10, 15),
    DP(STEAM_VENT, 7, 24), DP(STEAM_VENT, 26, 30), DP(SALAMANDER_STATUE, 15, 15),
    DP(EMBER_ROCK, 13, 31), DP(OBSIDIAN, 19, 33), DP(OBSIDIAN, 9, 7), DP(EMBER_ROCK, 39, 21),
};

/* ================================================================ */
/*  THE FORGE                                                       */
/* ================================================================ */

static const char *const FORGE_ROWS[] = {
    "HHHHHHHHHHHHHHH", /*  0 */
    "HhhhhhhhhhhhhhH", /*  1 */
    "H+++++++++++++H", /*  2 */
    "H+++++++++++++H", /*  3 */
    "H+++++++++++++H", /*  4 */
    "H+++++++++++++H", /*  5 */
    "H++++++v++++++H", /*  6 */
    "H+++++++++++++H", /*  7 */
    "H+++++++++++++H", /*  8 */
    "H++++++X++++++H", /*  9 */
};
static const DecorPlace FORGE_DECOR[] = {
    DP(FURNACE, 2, 1), DP(TOOL_RACK, 5, 1), DP(FORGE_ANVIL, 5, 4), DP(COAL_PILE, 1, 4),
    DP(LAVA_ORE_CART, 12, 2), DP(COAL_PILE, 13, 3), DP(TOOL_RACK, 9, 1), DP(BARREL, 13, 7),
    DP(CRATE, 1, 8), DP(BRAZIER, 11, 1),
};

/* ================================================================ */
/*  ANVIL HALL                                                      */
/* ================================================================ */

static const char *const ANVIL_HALL_ROWS[] = {
    "HHHHHHHHHHHHHHHHH", /*  0 */
    "HhhhhhhhhhhhhhhhH", /*  1 */
    "H+++++++++++++++H", /*  2 */
    "H++v+++++++++v++H", /*  3 */
    "H+++++++++++++++H", /*  4 */
    "H+++++++++++++++H", /*  5 */
    "HHHHHHHH+HHHHHHHH", /*  6 */
    "Hhhhhhhh+hhhhhhhH", /*  7 */
    "HH++++H+++H++++HH", /*  8 */
    "HH+++++++++++++HH", /*  9 */
    "HH++++H+v+H++++HH", /* 10 */
    "HH++++H+++H++++HH", /* 11 */
    "HHHHHHH+++HHHHHHH", /* 12 */
    "HHHHHHHH+HHHHHHHH", /* 13 */
    "Hhhhhhhh+hhhhhhhH", /* 14 */
    "HHHHHHH+++HHHHHHH", /* 15 */
    "HH++++H+++H++++HH", /* 16 */
    "HH++++H+++H++++HH", /* 17 */
    "HH+++++++++++++HH", /* 18 */
    "HH++++H+v+H++++HH", /* 19 */
    "HHHHHHH+++HHHHHHH", /* 20 */
    "H+++++++X+++++++H", /* 21 */
};
static const DecorPlace ANVIL_HALL_DECOR[] = {
    DP(HALL_BANNER, 4, 0), DP(HALL_BANNER, 12, 0), DP(BRAZIER, 1, 2), DP(BRAZIER, 15, 2),
    DP(FORGE_ANVIL, 8, 9), DP(COAL_PILE, 15, 21), DP(BRAZIER, 1, 21),
    /* a brazier in each pen, two cells in from its door: a boulder can never
     * be pushed out through the door (you would have to stand in the fire) */
    DP(BRAZIER, 4, 9), DP(BRAZIER, 12, 9), DP(BRAZIER, 4, 18), DP(BRAZIER, 12, 18),
};
/* Pumice boulders (arg 1: light enough to push before you hold the ANVIL
 * CREST) onto plates; a gate opens once every plate of its group is
 * covered. Each chamber has two walled pens, one boulder and one plate
 * each, off a central aisle (x 7-9) that boulders can never reach, so a
 * jammed boulder only ever costs a trip outside (which resets them), never
 * a way out (tools/tests/test_puzzles.c proves it).
 * Chamber 1: plates 4,16 / 12,16, boulders 3,18 / 13,18 (up twice, then in).
 * Chamber 2: plates 2,8 / 14,8, boulders 3,10 / 13,10 (up twice, then out). */
static const MapObj ANVIL_HALL_OBJS[] = {
    OBJ(BOULDER, 3, 18, 1), OBJ(BOULDER, 13, 18, 1), OBJ(PLATE, 4, 16, 1), OBJ(PLATE, 12, 16, 1),
    OBJ(GATE, 8, 14, 1),
    OBJ(BOULDER, 3, 10, 1), OBJ(BOULDER, 13, 10, 1), OBJ(PLATE, 2, 8, 2), OBJ(PLATE, 14, 8, 2),
    OBJ(GATE, 8, 7, 2),
};

/* ================================================================ */
/*  EMBER TUNNEL                                                    */
/* ================================================================ */

static const char *const EMBER_TUNNEL_ROWS[] = {
    "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMM", /*  0 */
    "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMM", /*  1 */
    "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMM", /*  2 */
    "MMMMMMMMMMMMMMMMMmmmmmmmmmmMMM", /*  3 */
    "MMMMmmmmmmmmmmmMM__________MMM", /*  4 */
    "MMMM_____;;;;;_mm__________MMM", /*  5 */
    "MMMM_____;;;;;_____________MMM", /*  6 */
    "MMMM___________MM__________MMM", /*  7 */
    "MMMM___________MMMMMMmmmmmMMMM", /*  8 */
    "MMMM__j__mmmmmmmmmmmm_____MMMM", /*  9 */
    "MMMM__j___________________MMMM", /* 10 */
    "MMMM__j__M__7888889_______MMMM", /* 11 */
    "MMMM__j__M__1222223__M;;;;MMMM", /* 12 */
    "MMMM__j__M___________M;;;;MMMM", /* 13 */
    "MMMM__j__mmmmmmmmmmmmm;;;;MMMM", /* 14 */
    "MMMM______________________MMMM", /* 15 */
    "MMMM_;;;;;_________;;;;;;_MMMM", /* 16 */
    "MMMM_;;;;;_________;;;;;;_MMMM", /* 17 */
    "MMMM_;;;;;_________;;;;;;_MMMM", /* 18 */
    "MMMMrrrrrrrrrrrrrrrrrrrrrrMMMM", /* 19 */
    "MMMMMMMMMMMMM___MMMMMMMMMMMMMM", /* 20 */
    "MMMMMMMMMMMMM___MMMMMMMMMMMMMM", /* 21 */
    "MMMMMMMMMMMMM___MMMMMMMMMMMMMM", /* 22 */
    "MMMMMMMMMMMMM___MMMMMMMMMMMMMM", /* 23 */
    "MMMMMMMMMMMMM_x_MMMMMMMMMMMMMM", /* 24 */
    "MMMMMMMMMMMMMMMMMMMMMMMMMMMMMM", /* 25 */
};
static const Stamp EMBER_TUNNEL_STAMPS[] = {
    STAMP(VO, TUNNEL_ARCH, 20, 2),  /* to CALDERA HEART, door 21,3 */
};
static const DecorPlace EMBER_TUNNEL_DECOR[] = {
    DP(LAVA_ORE_CART, 7, 19), DP(EMBER_ROCK, 20, 10), DP(STEAM_VENT, 25, 8), DP(OBSIDIAN, 4, 8),
    DP(COAL_PILE, 25, 17), DP(BRAZIER, 12, 19), DP(BRAZIER, 16, 19), DP(OBSIDIAN, 26, 5),
    DP(EMBER_ROCK, 17, 7),
};
/* STRENGTH boulders (arg 0): the one in the gap guards the Caldera arch */
static const MapObj EMBER_TUNNEL_OBJS[] = {
    OBJ(BOULDER, 15, 6, 0), OBJ(BOULDER, 24, 10, 0),
};

/* ================================================================ */
/*  CALDERA HEART                                                   */
/* ================================================================ */

static const char *const CALDERA_ROWS[] = {
    "MMMMMMMMMMMMMMMMMMMM", /*  0 */
    "MMMMMMMMMMMMMMMMMMMM", /*  1 */
    "MMmmmmmmmmmmmmmmmmMM", /*  2 */
    "MMyy::::::::::::::MM", /*  3 */
    "MMyy788888888889::MM", /*  4 */
    "MM::455555555556::MM", /*  5 */
    "MM::455n2222b556::MM", /*  6 */
    "MM::4556____4556::MM", /*  7 */
    "MM::4556____4556::MM", /*  8 */
    "MM::4556____4556::MM", /*  9 */
    "MM::455p9::7q556::MM", /* 10 */
    "MM::45556::45556yyMM", /* 11 */
    "MM::12223::12223yyMM", /* 12 */
    "MM:::::::__:::::yyMM", /* 13 */
    "MMMMMMMMM__MMMMMMMMM", /* 14 */
    "MMMMMMMMM__MMMMMMMMM", /* 15 */
    "MMMMMMMMMxMMMMMMMMMM", /* 16 */
};
static const DecorPlace CALDERA_DECOR[] = {
    DP(SALAMANDER_STATUE, 6, 12), DP(SALAMANDER_STATUE, 13, 12), DP(STEAM_VENT, 2, 5),
    DP(STEAM_VENT, 17, 4), DP(EMBER_ROCK, 3, 11), DP(OBSIDIAN, 16, 8), DP(OBSIDIAN, 2, 8),
};
static const MapObj CALDERA_OBJS[] = {
    OBJ(LEGEND, 9, 7, SP_CALDERON),
};

/* ================================================================ */
/*  MOONVEIL PATH                                                   */
/* ================================================================ */

static const char *const MOONVEIL_ROWS[] = {
    "TTTTTTTTTTTTTTTTTTTTTTTT==TTTTTTTTTTTTTTTTTTTTTT", /*  0 */
    "tttttttttttttttttttttttt==tttttttttttttttttttttt", /*  1 */
    "TT......................==....................TT", /*  2 */
    "tt.,,,,,,...T......T....==....T..........T....tt", /*  3 */
    "TT.,,,,,,...t......t....==....t..........t....TT", /*  4 */
    "tt.,,,,,,...............==============........tt", /*  5 */
    "TT.,,,,,,...............==============........TT", /*  6 */
    "tt.,,,,,,....~~~~~~~~...............==........tt", /*  7 */
    "TT.,,,,,,....~~~~~~~~...............==..,,,,,,TT", /*  8 */
    "tt.,,,,,,....~~~~~~~~......fffffff..==..,,,,,,tt", /*  9 */
    "TT.,,,,,,....~~~~~~~~......fffffff..==..,,,,,,TT", /* 10 */
    "tt...........~~~~~~~~......fffffff..==..,,,,,,tt", /* 11 */
    "TT............~~~~~~..T....fffffff..==..,,,,,,TT", /* 12 */
    "tt.fffff..............t.............==..,,,,,,tt", /* 13 */
    "TT.fffff............................==..,,,,,,TT", /* 14 */
    "tt.fffff..============================........tt", /* 15 */
    "TT.fffff..============================........TT", /* 16 */
    "tt.fffff..==..................................tt", /* 17 */
    "TT........==..........................CCCCCCCCTT", /* 18 */
    "tt........==..,,,,,,,,................cccccccctt", /* 19 */
    "TT........==..,,,,,,,,......,,,,,,,,..........TT", /* 20 */
    "tt........==..,,,,,,,,......,,,,,,,,..........tt", /* 21 */
    "TT.T......==..,,,,,,,,......,,,,,,,,........T.TT", /* 22 */
    "tt.t......==..,,,,,,,,......,,,,,,,,........t.tt", /* 23 */
    "TT........==..,,,,,,,,......,,,,,,,,....T.....TT", /* 24 */
    "tt.....T..==..,,,,,,,,......,,,,,,,,....t.....tt", /* 25 */
    "TT.....t..==..........T.....,,,,,,,,..........TT", /* 26 */
    "tt........==..........t.......................tt", /* 27 */
    "TT........==..................................TT", /* 28 */
    "tt........================.T..........fffffff.tt", /* 29 */
    "TT........================.t..........fffffff.TT", /* 30 */
    "tt.,,,,,,...............==............fffffff.tt", /* 31 */
    "TT.,,,,,,.....fffffff...==............fffffff.TT", /* 32 */
    "tt.,,,,,,.....fffffff...==..[LLLLLLL].fffffff.tt", /* 33 */
    "TT.,,,,,,.....fffffff...==............fffffff.TT", /* 34 */
    "tt.,,,,,,.....fffffff...==....................tt", /* 35 */
    "TT.,,,,,,....T..........==.......T....T.....T.TT", /* 36 */
    "tt...........t..........==.......t....t.....t.tt", /* 37 */
    "TTTTTTTTTTTTTTTTTTTTTTTT==TTTTTTTTTTTTTTTTTTTTTT", /* 38 */
    "tttttttttttttttttttttttt==tttttttttttttttttttttt", /* 39 */
};
static const DecorPlace MOONVEIL_DECOR[] = {
    DP(SIGNPOST, 22, 36), DP(SIGNPOST, 22, 3), DP(DREAM_STATUE, 16, 13), DP(MOONSTONE, 21, 9),
    DP(MOON_LANTERN, 23, 28), DP(MOON_LANTERN, 12, 17), DP(MOON_LANTERN, 35, 13), DP(MOON_LANTERN, 26, 3),
    DP(PETALS, 19, 5), DP(PETALS, 41, 26), DP(PETALS, 7, 27), DP(MOONSTONE, 45, 20),
    DP(BENCH, 27, 17), DP(MOONSTONE, 3, 28), DP(PETALS, 34, 37),
};

/* ================================================================ */
/*  DREAMSPIRE                                                    */
/* ================================================================ */

/*
 * DREAMSPIRE rises in rings toward the MIRROR HALL on the Crown:
 *   - the GARDENS (height 0): the south gate (edge x 24-25), the moon pond
 *     spilling off the south-east edges, the moonpetal meadow (wild kin);
 *   - the GRAND STAIR (24-25,25-26) climbs the 2-high wall from the plaza
 *     straight onto the LANTERN TERRACE (2): the SLUMBAKU statue, benches;
 *   - the lower RINGS (1): Hearth and shop west, houses and a tower east;
 *     between the terrace and the north blocks runs the SLEEPERS' LANE (1),
 *     walked east-west UNDER the Dream Bridge (23-24,13-16) that carries
 *     the Grand Stair north OVER it; a TUNNEL (16,17-24, mouth 16,25)
 *     runs under the terrace from the lantern walk up to the lane;
 *   - the NORTH BLOCKS (2): towers west, the DUST LIBRARY east, and the
 *     CROWN (3) with the MIRROR HALL (stairs 23-24,10).
 * Ledges drop off the rings into the gardens. A hidden gap in the trees
 * (45,10-11, hint: the path stub) opens the secret moon garden (satchel +
 * the night gardener).
 */
static const char *const DREAMSPIRE_ROWS[] = {
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT", /*  0 */
    "tttttttttttttttttttttttttttttttttttttttttttttttt", /*  1 */
    "TT,,,...........TTT..#######..TTT,,,.......TfffT", /*  2 */
    "tt,,,.........ffttt###########ttt,,,.......tffft", /*  3 */
    "TT,,,.........ff.T#############T.,,,.......Tf=fT", /*  4 */
    "tt,,,.........ff.t#############t.,,,.......tf=ft", /*  5 */
    "T.,,,.........ff..#############..,,,.......Tf=fT", /*  6 */
    "t.,,,.........ff..#############..,,,.......tf=ft", /*  7 */
    "TTT.........=.ff..#############..,,,.......Tf=fT", /*  8 */
    "ttt...===...=.....#############........=...tf=ft", /*  9 */
    "TTT.....=...=..........................=...TTTTT", /* 10 */
    "ttt.....================================...ttttt", /* 11 */
    "TT......=..............==.............=......=.T", /* 12 */
    "................................................", /* 13 */
    "TTT....................##.....................TT", /* 14 */
    "ttt====================##=====================tt", /* 15 */
    "TTT.........=..........##..........,,,,,......TT", /* 16 */
    "ttt.........=..........##..........,,,,,......tt", /* 17 */
    "T...........=....##########........,,,,,.....TTT", /* 18 */
    "t...........=....##########........,,,,,.....ttt", /* 19 */
    "T...........=.#############..................TTT", /* 20 */
    "t...........=....##########...............=..ttt", /* 21 */
    "TT...=......=....##########..=====........=..TTT", /* 22 */
    "tt...========....##########........==========ttt", /* 23 */
    "TT.....................##................=....TT", /* 24 */
    "tt.......................................=....tt", /* 25 */
    "T.ffff..........=.............ffff...=...=.....T", /* 26 */
    "t.ffff..........=...##########ffff...=...=......", /* 27 */
    "T.ffff...=......=...##########ffff.......=....TT", /* 28 */
    ".......=======..=...##########...........=....tt", /* 29 */
    "T...................##########................TT", /* 30 */
    "t......=................==...............=..~~~~", /* 31 */
    "TTTT...=................==..............~~~~~~~~", /* 32 */
    "tttt...=................==............~~~~~~~~~~", /* 33 */
    "T......===================================~~~~~~", /* 34 */
    "t.,,,,,,,,,,,,,.........==.......~~~~~~~~~~~~~~~", /* 35 */
    "TTTT,,,,,,,,,,,ffffff...==......~~~~~~~~~~~~~~~~", /* 36 */
    "tttt,,,,,,,,,,,ffffff...==......~~~~~~~~~~~~~~~~", /* 37 */
    "TTTT,,,,,,,,,,,ffffff...==.......~~~~~~~~~~~~~~~", /* 38 */
    "tttt,,,,,,,,,,,ffffff...==........~~~~~~~~~~~~~~", /* 39 */
    "T.TTTTTT,,,TTT,..TT.TT..==..TTTTT..~~~~~~~~~~~~~", /* 40 */
    "t.tttttt,,,ttt,..tt.tt..==..ttttt...~~~~~~~~~~~~", /* 41 */
    "TTTTTTTTTTTTTTTTTTTTTTTT==TTTTTTTTTTT~~~~~~~~~~~", /* 42 */
    "tttttttttttttttttttttttt==ttttttttttt~~~~~~~~~~~", /* 43 */
};

/* heights (0-3), stairs (^ v < >) and ledges (_): docs/ELEVATION.md */
static const char *const DREAMSPIRE_ELEV[] = {
    "222222222222222223333333333333332222222222222222", /*  0 */
    "222222222222222223333333333333332222222222222222", /*  1 */
    "222222222222222223333333333333332222222222222222", /*  2 */
    "222222222222222223333333333333332222222222222222", /*  3 */
    "222222222222222223333333333333332222222222222222", /*  4 */
    "222222222222222223333333333333332222222222222222", /*  5 */
    "222222222222222223333333333333332222222222222222", /*  6 */
    "222222222222222223333333333333332222222222222222", /*  7 */
    "222222222222222223333333333333332222222222222222", /*  8 */
    "222222222222222223333333333333332222222222222222", /*  9 */
    "22222222222222222222222^^22222222222222222222222", /* 10 */
    "222222222222222222222222222222222222222222222222", /* 11 */
    "222222222222222222222222222222222222222222222222", /* 12 */
    "11111111^11111111111111111111111111111^111111111", /* 13 */
    "111111111111111111111111111111111111111111111111", /* 14 */
    "111111111111111111111111111111111111111111111111", /* 15 */
    "111111111111111111111111111111111111111111111111", /* 16 */
    "111111111111112212222222222222222211111111111111", /* 17 */
    "111111111111112212222222222222222211111111111111", /* 18 */
    "111111111111112212222222222222222211111111111111", /* 19 */
    "1111111111111>2212222222222222222211111111111111", /* 20 */
    "1111111111111122122222222222222222<1111111111111", /* 21 */
    "111111111111112212222222222222222211111111111111", /* 22 */
    "111111111111112212222222222222222211111111111111", /* 23 */
    "111111111111112212222222222222222211111111111111", /* 24 */
    "111111111111111111110000^^0000111111111111111111", /* 25 */
    "111111111111111111110000^^0000111111111111111111", /* 26 */
    "111111111111111111110000000000111111111111110000", /* 27 */
    "111111111111111111110000000000111111111111110000", /* 28 */
    "00001111111111111111000000000000000__0000^000000", /* 29 */
    "000011111111111111110000000000000000000000000000", /* 30 */
    "0000000^000000000___0000000000000000000000000000", /* 31 */
    "000000000000000000000000000000000000000000000000", /* 32 */
    "000000000000000000000000000000000000000000000000", /* 33 */
    "000000000000000000000000000000000000000000000000", /* 34 */
    "000000000000000000000000000000000000000000000000", /* 35 */
    "000000000000000000000000000000000000000000000000", /* 36 */
    "000000000000000000000000000000000000000000000000", /* 37 */
    "000000000000000000000000000000000000000000000000", /* 38 */
    "000000000000000000000000000000000000000000000000", /* 39 */
    "000000000000000000000000000000000000000000000000", /* 40 */
    "000000000000000000000000000000000000000000000000", /* 41 */
    "000000000000000000000000000000000000000000000000", /* 42 */
    "000000000000000000000000000000000000000000000000", /* 43 */
};

static const ElevFeat DREAMSPIRE_FEATS[] = {
    EF(BRIDGE_V, 23, 13, 2, 4),  /* the Dream Bridge: the Grand Stair over, the lane under */
    EF(TUNNEL, 16, 17, 1, 8),    /* under the Lantern Terrace: lantern walk -> lane */
    EF(HIDDEN, 45, 10, 1, 2),    /* through the trees to the secret moon garden */
};
static const Stamp DREAMSPIRE_STAMPS[] = {
    STAMP(DR, MIRROR_HALL, 21, 3),  /* MIRROR HALL, door 24,7 */
    STAMP(DR, HEARTH, 3, 18),       /* SPIRE HEARTH HALL, door 5,21 */
    STAMP(DR, SHOP, 7, 24),         /* SPIRE SHOP, door 9,27 */
    STAMP(DR, LIBRARY, 36, 4),      /* the DUST LIBRARY, door 39,8 */
    STAMP(DR, TOWER, 5, 4),
    STAMP(DR, TOWER_ROSE, 11, 3),
    STAMP(DR, TOWER, 41, 16),
    STAMP(DR, HOUSE_ROSE, 28, 18),
    STAMP(DR, HOUSE, 35, 22),
};
static const DecorPlace DREAMSPIRE_DECOR[] = {
    DP(DREAM_STATUE, 20, 19), DP(SIGNPOST, 22, 39), DP(SIGNPOST, 35, 9), DP(SIGNPOST, 20, 8),
    DP(MOON_LANTERN, 22, 8), DP(MOON_LANTERN, 26, 8), DP(MOON_LANTERN, 22, 11), DP(MOON_LANTERN, 25, 11),
    DP(MOON_LANTERN, 22, 17), DP(MOON_LANTERN, 25, 17), DP(MOON_LANTERN, 18, 23), DP(MOON_LANTERN, 26, 23),
    DP(MOON_LANTERN, 23, 29), DP(MOON_LANTERN, 26, 29), DP(MOON_LANTERN, 12, 14), DP(MOON_LANTERN, 34, 14),
    DP(MOON_LANTERN, 40, 22), DP(MOON_LANTERN, 6, 22),
    DP(BENCH, 18, 20), DP(BENCH, 25, 21), DP(BENCH, 21, 28), DP(MOONSTONE, 44, 8),
    DP(PETALS, 11, 2), DP(PETALS, 30, 4), DP(PETALS, 30, 38), DP(PETALS, 9, 19), DP(PETALS, 18, 37),
    DP(PETALS, 45, 5), DP(MOONSTONE, 33, 30), DP(MOONSTONE, 46, 4), DP(MOONSTONE, 15, 33),
    DP(FLOAT_PAGES, 38, 3), DP(STANDING_MIRROR, 19, 5),
};

/* ================================================================ */
/*  MIRROR HALL                                                     */
/* ================================================================ */

static const char *const MIRROR_HALL_ROWS[] = {
    "MMMMMMMMMMMMMMMMMMMMM", /*  0 */
    "MmmmmmmmmmMmmmmmmmmmM", /*  1 */
    "M+++++++*+M+++++++++M", /*  2 */
    "M+*+++++++M+++++++++M", /*  3 */
    "M+++++++++M+++++++++M", /*  4 */
    "M+++++++++M+++++++++M", /*  5 */
    "M+++++++*+M+*+++++*+M", /*  6 */
    "MMMMMMMMMMMMMMMMMMMMM", /*  7 */
    "MmmmmmmmmmMmmmmmmmmmM", /*  8 */
    "M+++++++++M+++++++++M", /*  9 */
    "M+*+++++*+M+++++++*+M", /* 10 */
    "M+++++++++M+++++++++M", /* 11 */
    "M+++++++++M+++++++++M", /* 12 */
    "M+++++++++M+++++++++M", /* 13 */
    "M+*+++++++M+*+++++++M", /* 14 */
    "M++++X++++M+++++++++M", /* 15 */
};
static const DecorPlace MIRROR_HALL_DECOR[] = {
    DP(STANDING_MIRROR, 3, 0), DP(STANDING_MIRROR, 7, 0), DP(STANDING_MIRROR, 13, 0),
    DP(STANDING_MIRROR, 17, 0), DP(STANDING_MIRROR, 4, 7), DP(STANDING_MIRROR, 16, 7),
    DP(MOONSTONE, 1, 9), DP(MOONSTONE, 19, 15), DP(MOONSTONE, 1, 2), DP(MOONSTONE, 19, 2),
    DP(MOON_LANTERN, 10, 7), DP(PETALS, 15, 4),
};
/* Teleport pads pair by arg: A (bottom-left, the door) -1-> B -2-> C -4->
 * D (the Master). C's pad 3 drops you back in A; D's pad 5 is the way home. */
static const MapObj MIRROR_HALL_OBJS[] = {
    OBJ(PAD, 8, 10, 1), OBJ(PAD, 12, 14, 1), OBJ(PAD, 18, 10, 2), OBJ(PAD, 2, 3, 2),
    OBJ(PAD, 8, 6, 3), OBJ(PAD, 2, 14, 3), OBJ(PAD, 8, 2, 4), OBJ(PAD, 12, 6, 4),
    OBJ(PAD, 18, 6, 5), OBJ(PAD, 2, 10, 5),
};

/* ================================================================ */
/*  DUST LIBRARY                                                    */
/* ================================================================ */

static const char *const DUST_LIBRARY_ROWS[] = {
    "BBBBBBBBBBBBBBBBBBBBBBBB", /*  0 */
    "BbbbbbbbbbbbbbbbbbbbbbbB", /*  1 */
    "B______________________B", /*  2 */
    "B______________________B", /*  3 */
    "B______________________B", /*  4 */
    "B__BBBBBB______BBBBBB__B", /*  5 */
    "B__bbbbbb______bbbbbb__B", /*  6 */
    "B;;;;;;;;_;;;;_______;;B", /*  7 */
    "B;;;;;;;;_;;;;_______;;B", /*  8 */
    "B;;BBBBBB______BBBBBB;;B", /*  9 */
    "B;;bbbbbb______bbbbbb;;B", /* 10 */
    "B;;____________;;;;;;;;B", /* 11 */
    "B;;____________;;;;;;;;B", /* 12 */
    "B;;BBBBBB______BBBBBB;;B", /* 13 */
    "B;;bbbbbb______bbbbbb;;B", /* 14 */
    "B;;__________________;;B", /* 15 */
    "B;;__________________;;B", /* 16 */
    "B;;__________________;;B", /* 17 */
    "B______________________B", /* 18 */
    "B__________x___________B", /* 19 */
};
static const DecorPlace DUST_LIBRARY_DECOR[] = {
    DP(SCRIPT_PEDESTAL, 9, 2), DP(SCRIPT_PEDESTAL, 14, 2), DP(FLOAT_PAGES, 11, 5), DP(FLOAT_PAGES, 5, 11),
    DP(FLOAT_PAGES, 18, 15), DP(FLOAT_PAGES, 2, 4), DP(READING_DESK, 16, 17), DP(BOOK_PILE, 1, 18),
    DP(BOOK_PILE, 22, 2), DP(MOON_LANTERN, 9, 15), DP(MOON_LANTERN, 14, 15), DP(BOOKCASE, 1, 2),
    DP(BOOKCASE, 21, 4), DP(BOOK_PILE, 20, 8),
};
static const MapObj DUST_LIBRARY_OBJS[] = {
    OBJ(LEGEND, 11, 2, SP_SCRIPTORA),
};


/* ================================================================ */
/*  Hearth halls and shops (interior tileset)                       */
/* ================================================================ */

static const char *const CINDER_HEARTH_ROWS[] = {
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
static const Stamp CINDER_HEARTH_STAMPS[] = { STAMP(I, RUG, 4, 6) };
static const DecorPlace CINDER_HEARTH_DECOR[] = {
    DP(PLANT, 0, 1), DP(LANTERN_RACK, 3, 1), DP(HEAL_MACHINE, 7, 1), DP(FIREPLACE, 9, 1), DP(PC, 1, 4),
    DP(PENNANT, 1, 0), DP(CALENDAR, 9, 0),
    DP(TABLE_ROUND, 8, 5), DP(CHAIR, 8, 4), DP(CHAIR, 9, 4), DP(TEA_SET, 10, 6),
    DP(KIN_BASKET, 0, 7), DP(SMALL_PLANT, 10, 7),
};

static const char *const CINDER_SHOP_ROWS[] = {
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
static const DecorPlace CINDER_SHOP_DECOR[] = {
    DP(BARREL_IN, 0, 2), DP(SACKS_IN, 3, 2), DP(PENNANT, 1, 0),
    DP(SHOP_SHELF, 5, 1), DP(SHOP_SHELF, 7, 1), DP(LANTERN_RACK, 9, 1),
    DP(DISPLAY_CASE, 6, 5), DP(BARREL_IN, 9, 5), DP(SACKS_IN, 10, 5),
    DP(SMALL_PLANT, 0, 7), DP(SMALL_RUG, 5, 7),
};

static const char *const DREAM_HEARTH_ROWS[] = {
    "WWnWWpWWnWW",
    "wwwwwwwwwww",
    ":::::::::::",
    ":::<===>:::",
    ":::::::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::D:::::",
};
static const Stamp DREAM_HEARTH_STAMPS[] = { STAMP(I, RUG, 4, 6) };
static const DecorPlace DREAM_HEARTH_DECOR[] = {
    DP(FLOWER_VASE, 0, 2), DP(LANTERN_RACK, 3, 1), DP(HEAL_MACHINE, 7, 1), DP(FLOOR_LAMP, 9, 1), DP(PC, 10, 1),
    DP(CALENDAR, 9, 0),
    DP(CUSHION, 1, 5), DP(CUSHION, 2, 6), DP(AQUARIUM, 9, 4), DP(KIN_BASKET, 8, 6), DP(KIN_BASKET, 10, 6),
    DP(PLANT, 0, 7),
};

static const char *const DREAM_SHOP_ROWS[] = {
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
static const DecorPlace DREAM_SHOP_DECOR[] = {
    DP(BOOKSHELF_SMALL, 0, 1), DP(FLOWER_VASE, 3, 2), DP(PENNANT, 1, 0),
    DP(SHOP_SHELF, 5, 1), DP(SHOP_SHELF, 7, 1), DP(LANTERN_RACK, 9, 1),
    DP(DISPLAY_CASE, 6, 5), DP(GLOBE, 9, 5), DP(PLANT, 10, 6),
    DP(SMALL_PLANT, 0, 7), DP(SMALL_RUG, 5, 7),
};


/* ================================================================ */
/*  Wild kin                                                        */
/* ================================================================ */

static const WildSlot WILD_CINDER_ROAD[] = {
    { SP_SALAMBER, 20, 24, 28 }, { SP_STINGLET, 18, 24, 27 }, { SP_MAGNITICK, 16, 24, 28 },
    { SP_RIVETILLO, 14, 25, 29 }, { SP_CINDERUB, 10, 24, 27 }, { SP_FULGECKO, 10, 26, 29 },
    { SP_SCORCHION, 6, 28, 30, WHEN_NIGHT }, { SP_LODEHORN, 4, 28, 30 }, { SP_FOUNDRAKE, 2, 29, 31 },
};
static const WildSlot WILD_EMBER_TUNNEL[] = {
    { SP_SALAMBER, 18, 27, 31 }, { SP_RIVETILLO, 16, 27, 31 }, { SP_GOLEMIT, 14, 27, 30 },
    { SP_SQUEAKLE, 12, 27, 30 }, { SP_DIGGET, 12, 27, 30 }, { SP_LODEHORN, 8, 29, 32 },
    { SP_FORTADILLO, 6, 30, 33 }, { SP_MAGMAUL, 4, 30, 33 }, { SP_FOUNDRAKE, 4, 30, 33 },
};
static const WildSlot WILD_MOONVEIL[] = {
    { SP_DOZLOTH, 20, 30, 33 }, { SP_PUFFOWL, 14, 30, 32 }, { SP_MANDRAGOR, 12, 31, 34 },
    { SP_RADISHOO, 10, 30, 32, WHEN_DAY }, { SP_LUMOTH, 10, 31, 34, WHEN_NIGHT },
    { SP_SKYWISP, 8, 30, 33, WHEN_NIGHT }, { SP_TANUKETTLE, 6, 32, 34 },
    { SP_SOMNISLOTH, 4, 33, 35 }, { SP_QILUMEN, 1, 34, 36, WHEN_NIGHT },
};
static const WildSlot WILD_DREAMSPIRE[] = {
    { SP_DOZLOTH, 20, 31, 34, WHEN_DAY }, { SP_MANDRAGOR, 14, 32, 34 }, { SP_TANUKETTLE, 10, 32, 35 },
    { SP_LUMOTH, 16, 32, 35, WHEN_NIGHT }, { SP_SOMNISLOTH, 6, 33, 36 },
    { SP_HOOTLORD, 4, 34, 36, WHEN_NIGHT }, { SP_SLUMBAKU, 3, 33, 36, WHEN_NIGHT },
    { SP_QILUMEN, 1, 35, 36, WHEN_NIGHT },
};
static const WildSlot WILD_DUST_LIBRARY[] = {
    { SP_KETTLEKIN, 18, 32, 35 }, { SP_PARASOLE, 16, 32, 35 }, { SP_LUMOTH, 14, 32, 35 },
    { SP_WEBBIT, 12, 32, 34 }, { SP_SQUEAKLE, 10, 32, 34 }, { SP_WICKLET, 4, 33, 36 },
    { SP_LAMPJINN, 3, 34, 36 },
};
