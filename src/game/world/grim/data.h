/*
 * world/grim/data.h -- the Ashen March (W-GRIM): ASHEN FIELDS, GRAVEWOOD,
 * DUSKMERE and its interiors, the LANTERN CRYPT (the LANTERN Hall), THE
 * OSSUARY (two floors) and the BONE THRONE.
 *
 * Edges (docs/EXPANSION.md 9): ASHEN FIELDS north opens at x 20-21 into
 * COPPERLINE ROAD; ASHEN FIELDS east <-> GRAVEWOOD west and GRAVEWOOD
 * east <-> DUSKMERE west open at y 20-21. The OSSUARY has no door: the gate
 * warden in DUSKMERE lets crest-holders in (scripts.c).
 *
 * 'grim' legend (tools/tilesets/ts_grim.py):
 *   . ash   , dead grass (wild)   : scorch   e embers   # cobbles   = ash road
 *   ~ black water   g grave soil   b dead bracken (wild)   m peat mud
 *   M moss   r reeds (wild)   d boardwalk   T/t dead oak   P/p charred pine
 *   Y/y swamp cypress   L [ ] ash ledges   C/c crag
 * 'crypt' legend (tools/tilesets/ts_crypt.py):
 *   (space) void   W wall top   w wall   n niche   o bone wall   v wisp crack
 *   . flagstones   : dusty flags   , bone dust (wild)   # maze block
 *   % FAKE block (walkable)   _ GHOST floor (solid)   D exit mat   | carpet
 *   U stairs up   S stairs down   A archway (doors)   I/i pillar
 */

static const char *const ASHEN_FIELDS_ROWS[] = {
    "PPTPPPPTPPPPTPPPPTPP==TPPPPTPPPPTPPPPTPPPPPP",
    "pptpppptpppptpppptpp==tpppptpppptpppptpppppp",
    "PP..................==....................PP",
    "pp...,,,,,,.........==.......CCCCCCCCCCC..pp",
    "PP....,,,,,,,,......==.......ccccccccccc..PP",
    "pp.,,,,,,,,,,,,..T..==..T....ccccccccccc..pp",
    "PP.,,,,,,,,,,,,..t..==..t.................PP",
    "pp.,,,,,,,,,,,,,....==.............,,.,...pp",
    "PP..,,,,,,,,,,,.....==...........,,,,,,,..PP",
    "pp.,,,,,,,,,,,,,....==..........,,,,,,T,..pp",
    "PP.,,,,,,,,,,,,.....==...........,,,,,t,..PP",
    "pp....,,,,,,,,,.....=========...,,,,,,,,,.pp",
    "PP..................=========...,,,,,,,,,.PP",
    "ppLLLLLLLLLLLLLLL].........==...,,,,,,,,,.pp",
    "PP.......................P.==....,,,,,,,,.PP",
    "pp.....######............p.==...,,,,,,,,..pp",
    "PP.....######..........T...==....,,,,,,...PP",
    "pp..::::::::::::.......t...==.....,,,,,...pp",
    "PP.::::::::::::.:..........==....T........PP",
    "pp.:::ee:::::::::..........==....t........pp",
    "PP.::::::::::::::..........=================",
    "pp..::::::::::::..P........=================",
    "PP.:::::::::ee::..p....,.,,,,,,,,,........PP",
    "pp.T.::::::::::.......,,,,,,,,,,,,,,.,....pp",
    "PP.t....:.::::.......,,,,,,,,,,,,,,,,.....PP",
    "pp....,.,,,,,,.......,,,,,,,,,,,,,,,,,....pp",
    "PP...,,,,,,,,,,T,......,,,,,,,,,,,,,,.,...PP",
    "pp..,,,,,,,,,,,t.........,,,,,,,,.,,,,,,,.pp",
    "PP..,,,,,,,,,,,,,........::::::::,,,,,,,P.PP",
    "pp..,,,,,,,,,,,,,,.......:::ee:::,,,,,,,p,pp",
    "PP.,,,,,,,,,,,,,,,.T......::ee:::,,,,,,,,,PP",
    "pp.,,,,,,,,,,,,,,,.t......:::::::,,,,,,,,,pp",
    "PP..,,,,,,,,,,,,,..........::::..,,,,,,,,.PP",
    "pp..,,,,,,,,,,,,,,................,,,,,,,,pp",
    "PP...,,,,,,,,,,.,,......T.........,,,,,,,.PP",
    "pp...,,,,,,,,,,.........t..........,,,,,..pp",
    "PP.......,,,T........................P....PP",
    "pp..........t........................p....pp",
    "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP",
    "pppppppppppppppppppppppppppppppppppppppppppp",
};

static const char *const GRAVEWOOD_ROWS[] = {
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
    "tttttttttttttttttttttttttttttttttttttttttttt",
    "TTgggggggggggggggggggbbbbbgggggggggmgmmgggTT",
    "ttgggggbbbbgTbggggggbbbbbbbbgggggggmmmmmmgtt",
    "TTgggbbbbbbbtbbggggbbbbbTbbbbggggggmrrrrmmTT",
    "ttgggbbbbbbbbbbgggbbbbbbtbbbbbggggmmrrrrrrtt",
    "TTgbbbTbbbbbbbbbbggbbbbbbbbbbggggmrr~~~~~~TT",
    "ttgbbbtbbbbbbbbbbgbbbbbbbbbbbbgggmmr~~~~~~tt",
    "TTgbbbbbbbbbbbbbbggbbbbbbbbbgggggmrr~~~~~~TT",
    "ttgbbbbbbbbbbbbTbggggggbbbgggggggmrr~~~~~~tt",
    "TTgbbbbbbbbbbbbtbgggggTggggggggggmrr~~~~~~TT",
    "ttggbbbbbbbbbbbbggggggtggTgggggggmrr~~~~~~tt",
    "TTggggbbbbbbbbgggggggggggtggggggggmrrrrrrrTT",
    "ttgggggbbbbbbgggggggggggggggggggggMrrrrrrrtt",
    "TTggggggggggggggggggggggbbbbbgggMMMMrrrrmmTT",
    "ttgggggg========================MMMMMmmmmmtt",
    "TTggTggg========================MMMMMmmmggTT",
    "ttggtggg==ggggggggg==gbbbbbbbb==gMMMMgggggtt",
    "TTgggggg==ggggggggg==gbbbbbbbb==ggMMggYgggTT",
    "ttgggggg==ggggTgggg==gggbbbbgg==ggggggygggtt",
    "==========ggggtgggg==ggggggggg==============",
    "==========ggggggggg==ggggggggg==============",
    "TTgTggggggggggggTgg==ggggggTggggggggggggggTT",
    "ttgtggggggggggggtgg==ggggggtgggggYggggggggtt",
    "TTggggggggggggggggg==ggggggggggggyggggggggTT",
    "ttggggbgbgggggggggggggggggggggggggggmmgmmYtt",
    "TTgggbbbbbgggggggggggggggggggggggggmmmmmmyTT",
    "ttgggbbbbbbbgggggggggggggggggTgggmmmmmmmmmtt",
    "TTggbbbbbbbbgggggggggggggggggtgggmmmmmmmmmTT",
    "ttgbbTbbbbbbggggggggggggggggggggmmmmm~~~mmtt",
    "TTgbbtbbbbbbggggggggggggggggggggmmmm~~~~~mTT",
    "ttgbbbbbbbbbggggggggggggggggggggmmm~~~~~~mtt",
    "TTgbbbbbbbbbggggggggggggggggggggmmm~~~~~~mTT",
    "ttgbbbbbbbTbggggggggggggggggggggmmm~~~~~~mtt",
    "TTgbbbbbbbtbggggggggggggggggggTggmmm~~~mmmTT",
    "ttgggbbbbbggggggggggggggggggggtggmmmmmmmmmtt",
    "TTgggbbbbggggggggggggggggggggggggmYmmmmmmmTT",
    "ttgggggggggggggggggggggggggggggggmymmmmmmgtt",
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
    "tttttttttttttttttttttttttttttttttttttttttttt",
};

static const char *const DUSKMERE_ROWS[] = {
    "YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY",
    "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",
    "YYmrrrrrrmmmmmmmmmm~~~~mmmmmmmmmmmmmmmmmmmYY",
    "yyrrrrrrrmmmmmmYmmm~~~~mmYmmmmmmmmmmmmmYmmyy",
    "YYmrrrrrrrmmmmmymmm~~~~mmymmmmmmmmmmmmmymmYY",
    "yyrrrrrrrrmmmmmmmmm~~~~mmmmmmmmmmmmmmmmmmmyy",
    "YYrrrrrrrrmmmmmmmmm~~~~mmmmmmmmmmmmmmmmmmmYY",
    "yymmrrrmmmmmmmmmmmm~~~~mmmmmYmmmmmmmmmmmmmyy",
    "YYmmmmmmmmmmmmmmmmm~~~~mmmmmymmmmmmmmmmmmmYY",
    "yymmmmmmmmmmmmmmmmm~~~~mmmmmmmmmmmmmmmmmmYyy",
    "YYmmmYmmmmmmmmmmmmm~~~~ddddddddddddmmmmmmyYY",
    "yymmmymmmmmmmmmmmmm~~~~ddddddddddddmmmmmmmyy",
    "YYmmmmmmmm==mmmmmmm~~~~mmm==mmmmm==mmmmmmmYY",
    "yymmmmmmmm==mmmmmmm~~~~mmm==rrrmm==m~~~mmmyy",
    "YYmmmmmmmm==MMMMmmmmddmmrr==rrrrm==~~~~~~mYY",
    "yymmmmmmmm==MMMMmmmmddmmrr==rrrrr==~~~~~~myy",
    "YYmYmmmmmm==MMMMMmmmddmmmr==rrrrm==~~~~~~~YY",
    "yymymmmmmm==MMMMMmmmddmmmr==rrrrm==~~~~~~~yy",
    "YYmmmmmmmm==MMMMmmmmddmmmm==mmmmm==~~~~~~~YY",
    "yymmmmmmm##########dddd########mmm~~~~~~~myy",
    "=========##########dddd########===========YY",
    "=========##########dddd########===========yy",
    "YYmmmmmmm##########dddd########mmmmmmmrrrrYY",
    "yymmmYmmm##########dddd######Y#mmmmmmmmmrryy",
    "YYmmmymmmmmmmm==mmmmddmmmmMMMymm==mmmmmmrrYY",
    "yymmmmmmmmmmmm==mmmmddmmmmmMMMMm==mmmmmmrryy",
    "YYmmmmmmmmmmmm==mYmmddmmmmmMMMMm==mmmmmmrmYY",
    "yymmmmmmmmmmmm==mymmddmmmmmMMMmm=======mmmyy",
    "YYmmmmmmmmmmmm==mmmmddmmmmmmmmmm=======mmmYY",
    "yymmmmmmmmmmYm==mmmmddmmmmmmmrrrrrrrrrmmmmyy",
    "YYmmmmmrrrrryr==mmm~~~~mmmmmrrrrrrrrrrrmmmYY",
    "yymrrrrrrrrrrrrrrmm~~~~mmmmrrrrrrrrrrrrmmmyy",
    "YYmrrrrrrrrrrrrrrmm~~~~mmmmmrr~r~~~r~rmmmmYY",
    "yymmm~~~~~~~~~mmmmm~~~~mmmm~~~~~~~~~~~~~~myy",
    "YYm~~~~~~~~~~~~~~mm~~~~mmm~~~~~~~~~~~~~~~mYY",
    "yy~~~~~~~~~~~~~~~mm~~~~mmm~~~~~~~~~~~~~~~myy",
    "YY~~~~~~~~~~~~~~~mm~~~~mmmm~~~~~~~~~~~~~~~YY",
    "yymm~~~~~~~~~~~~~mm~~~~mmmmm~~~~~~~~~~~~~myy",
    "YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY",
    "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",
};

static const char *const LANTERN_CRYPT_ROWS[] = {
    "WWWWWWWWWWWWWWWWWWWWWWW",
    "wwnwwvwwnwwwwwnwwvwwnww",
    "#.....................#",
    "#...I......|......I...#",
    "#...i......|......i...#",
    "#..........|..........#",
    "#..........|..........#",
    "###%#######_###########",
    "#...#.....#...#.......#",
    "#.#.#.###.#.#.#.#####.#",
    "#.#...#...#.#...#...#.#",
    "#.####..###.####..#.#.#",
    "#.....#...%.....#.#...#",
    "#####.###.#####.#.###.#",
    "#...#...#.....#.#...#.#",
    "#.#.###..####.#.###.#.#",
    "#.#.....#.....#.....#.#",
    "#.#######.#_##.######.#",
    "#.........#...........#",
    "###########.###########",
    "###########D###########",
};

static const char *const OSSUARY_1_ROWS[] = {
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "ooooUoooooovooooooooovooooSooo",
    "W...........,,,,,,...........W",
    "W..........,,,,,,,,,,........W",
    "W..I.....I.,,,,I,,,,,I.....I.W",
    "W..i.....i.,,,,i,,,,,i.....i.W",
    "W..........,,,,,,,...........W",
    "WWWWWWWW.WWWWWWWWWWWWW.WWWWWWW",
    "Woooooo.oooooooooooooo.ooooooW",
    "W............................W",
    "W....,.,,...........,,,,,,...W",
    "W...,,,,,,,.......,,,,,,,,,..W",
    "W..,,,,,,,,,.I..I,,,,,,,,,,,.W",
    "W.,,,,,,,,,,,i..i,,,,,,,,,,,,W",
    "W.,,,,,,,,,,,.....,,,,,,,,,,,W",
    "W..,,,,,,,,,......,,,,,,,,,,,W",
    "W.,,,,,,,,,,.I..I.,,,,,,,,,,,W",
    "W..,,,,,,,,,.i..i.,,,,,,,,.,.W",
    "W....,,.,.,........,,,,,.,...W",
    "W............................W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
};

static const char *const OSSUARY_2_ROWS[] = {
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "ovooooooooooooAoooooooooooUooW",
    "W.............|...,,,,,,.....W",
    "W.............|...,,,,,,,....W",
    "W..I..........|..,,,,,,,,I...W",
    "W..i..........|...,,,,,,,i...W",
    "W.............|..,,,,,,,.....W",
    "W.............|...,,,,,......W",
    "W.......WWWWW.|.WWWW.........W",
    "W.......oooon.|.noooo........W",
    "W.............|.....,.,,,....W",
    "W....,,,,.........,.,,,,,,,..W",
    "W...,,,,,,,......,,,,,,,,,,,.W",
    "W.,,,,,,,,,......,,,,,,,,,,,,W",
    "W.,,,,,,,,,,.....,,,,,,,,,,,.W",
    "W..,,,,,,,,,.....,,,,,,,,,,,.W",
    "W.,,,,,,,,,,......,,,,,,,,,,,W",
    "W..,,,,,,,,,......,,,,,,,,,,,W",
    "W..,,,,,,,,........,,,,,,,,..W",
    "W...,.,,.,..........,.,,,....W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
};

static const char *const BONE_THRONE_ROWS[] = {
    "WWWWWWWWWWWWWWWWW",
    "oooovooooooovoooo",
    "W...............W",
    "W...............W",
    "W...............W",
    "W.......|.......W",
    "W..I....|....I..W",
    "W..i....|....i..W",
    "W.......|.......W",
    "W.......|.......W",
    "W..I....|....I..W",
    "W..i....|....i..W",
    "W.......|.......W",
    "WWWWWWWWDWWWWWWWW",
};

static const char *const DUSK_HEARTH_ROWS[] = {
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

static const char *const DUSK_SHOP_ROWS[] = {
    "WWnWWpWWnWW",
    "wwwwwwwwwww",
    ":::::::::::",
    "<==>:::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::::::::",
    ":::::D:::::",
};

static const char *const APOTHECARY_ROWS[] = {
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

static const char *const DUSK_HOUSE_ROWS[] = {
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

/* ---------------- ASHEN FIELDS ---------------- */

static const DecorPlace ASHEN_FIELDS_DECOR[] = {
    DP(GR_SIGN, 19, 3), DP(GR_SIGN, 40, 18), DP(GR_MEMORIAL, 22, 8),
    /* the burnt farmstead */
    DP(GR_CART, 9, 17), DP(GR_STUMP, 5, 16), DP(GR_STUMP, 14, 15), DP(GR_BONES, 12, 20),
    DP(GR_BONES, 30, 8), DP(GR_BONES, 8, 33), DP(GR_BONES, 38, 24),
    DP(GR_SHRUB, 16, 9), DP(GR_SHRUB, 26, 7), DP(GR_SHRUB, 5, 21), DP(GR_SHRUB, 31, 34),
    DP(GR_SHRUB, 18, 27),
    /* the ash farmer's pumpkin patch */
    DP(GR_PUMPKIN, 26, 34), DP(GR_PUMPKIN, 27, 34), DP(GR_PUMPKIN, 28, 34),
    DP(GR_PUMPKIN, 26, 36), DP(GR_PUMPKIN, 28, 36),
    DP(GR_WISP, 10, 30), DP(GR_WISP, 36, 12),
};
static const MapObj ASHEN_FIELDS_OBJS[] = { OBJ(BERRY, 16, 20, 30), OBJ(BERRY, 31, 14, 31) };

static const WildSlot WILD_ASHEN[] = {
    { SP_DREGCROW, 20, 24, 28, WHEN_ANY }, { SP_CALCIPUP, 18, 24, 28, WHEN_ANY },
    { SP_PUMPKLING, 16, 24, 27, WHEN_ANY }, { SP_SCYTHLING, 14, 25, 28, WHEN_DAY },
    { SP_DIGGET, 12, 24, 27, WHEN_ANY }, { SP_STRAWSPECT, 8, 25, 29, WHEN_DAY },
    { SP_JACKOGRIM, 6, 27, 30, WHEN_NIGHT }, { SP_REAPMANTIS, 4, 28, 31, WHEN_ANY },
    { SP_CAWDAVER, 2, 29, 31, WHEN_NIGHT },
};

/* ---------------- GRAVEWOOD ---------------- */

static const DecorPlace GRAVEWOOD_DECOR[] = {
    DP(GR_SIGN, 3, 19), DP(GR_SIGN, 41, 18),
    /* the cemetery railing, with its gate at x 19-20 */
    DP(GR_FENCE, 13, 25), DP(GR_FENCE, 14, 25), DP(GR_FENCE, 15, 25), DP(GR_FENCE, 16, 25),
    DP(GR_FENCE, 17, 25), DP(GR_FENCE, 18, 25), DP(GR_FENCE, 21, 25), DP(GR_FENCE, 22, 25),
    DP(GR_FENCE, 23, 25), DP(GR_FENCE, 24, 25), DP(GR_FENCE, 25, 25), DP(GR_FENCE, 26, 25),
    DP(GR_FENCE, 27, 25),
    DP(GR_GRAVE, 14, 27), DP(GR_CROSS, 16, 27), DP(GR_GRAVE, 18, 27),
    DP(GR_CROSS, 22, 27), DP(GR_GRAVE, 24, 27), DP(GR_GRAVE, 26, 27),
    DP(GR_CROSS, 14, 29), DP(GR_GRAVE, 16, 29), DP(GR_GRAVE, 18, 29),
    DP(GR_GRAVE, 22, 29), DP(GR_CROSS, 24, 29), DP(GR_GRAVE, 26, 29),
    DP(GR_GRAVE, 14, 31), DP(GR_GRAVE, 16, 31), DP(GR_CROSS, 18, 31),
    DP(GR_GRAVE, 22, 31), DP(GR_GRAVE, 24, 31), DP(GR_CROSS, 26, 31),
    DP(GR_CROSS, 14, 33), DP(GR_GRAVE, 16, 33), DP(GR_GRAVE, 18, 33),
    DP(GR_CROSS, 22, 33), DP(GR_GRAVE, 24, 33), DP(GR_GRAVE, 26, 33),
    DP(GR_SHRUB, 12, 30), DP(GR_SHRUB, 28, 31), DP(GR_SHRUB, 12, 34),
    DP(GR_BONES, 33, 4), DP(GR_STUMP, 17, 5), DP(GR_STUMP, 28, 12),
    DP(GR_WISP, 24, 30), DP(GR_WISP, 15, 12), DP(GR_WISP, 37, 15),
};
static const MapObj GRAVEWOOD_OBJS[] = { OBJ(BERRY, 5, 23, 32), OBJ(BERRY, 28, 8, 33) };

static const WildSlot WILD_GRAVEWOOD[] = {
    { SP_SHROOMLET, 18, 27, 31, WHEN_ANY }, { SP_WEBBIT, 16, 27, 31, WHEN_ANY },
    { SP_OSSIHOUND, 10, 29, 32, WHEN_ANY }, { SP_SEXTONE, 10, 29, 32, WHEN_ANY },
    { SP_REAPMANTIS, 8, 29, 32, WHEN_ANY }, { SP_MYCOLOSSUS, 6, 30, 33, WHEN_DAY },
    { SP_CAWDAVER, 8, 29, 32, WHEN_ANY }, { SP_LACEWIDOW, 8, 30, 33, WHEN_NIGHT },
    { SP_NOCTAVE, 6, 30, 33, WHEN_NIGHT }, { SP_HOPSHI, 2, 32, 34, WHEN_NIGHT },
};

/* ---------------- DUSKMERE ---------------- */

static const Stamp DUSKMERE_STAMPS[] = {
    STAMP(GR, HEARTH, 8, 7), STAMP(GR, SHOP, 14, 8), STAMP(GR, APOTHECARY, 7, 25),
    STAMP(GR, HOUSE, 23, 25), STAMP(GR, CRYPT_HALL, 32, 5), STAMP(GR, BONE_GATE, 35, 23),
};
static const DecorPlace DUSKMERE_DECOR[] = {
    DP(GR_SIGN, 4, 19), DP(GR_SIGN, 31, 8),
    DP(GR_BELL, 26, 19),
    DP(GR_LANTERN, 9, 22), DP(GR_LANTERN, 30, 22), DP(GR_LANTERN, 12, 11), DP(GR_LANTERN, 31, 9),
    DP(GR_LANTERN, 34, 26),
    DP(GR_PUMPKIN, 13, 12), DP(GR_PUMPKIN, 7, 11), DP(GR_PUMPKIN, 25, 29), DP(GR_PUMPKIN, 6, 29),
    DP(GR_MOORING, 18, 13), DP(GR_MOORING, 22, 16),
    DP(GR_WISP, 36, 16), DP(GR_WISP, 8, 35), DP(GR_WISP, 30, 35),
};

static const WildSlot WILD_MIRE[] = {
    { SP_MUDDLE, 20, 28, 32, WHEN_ANY }, { SP_NOXKIT, 18, 28, 31, WHEN_ANY },
    { SP_CRANICRAB, 16, 28, 31, WHEN_ANY }, { SP_BOGSHAMBLE, 10, 30, 33, WHEN_ANY },
    { SP_SHROOMLET, 10, 28, 31, WHEN_DAY }, { SP_UMBRAKAT, 8, 30, 33, WHEN_NIGHT },
    { SP_WICKLET, 3, 31, 33, WHEN_NIGHT },
};

static const DecorPlace DUSK_HEARTH_DECOR[] = {
    DP(PLANT, 0, 1), DP(LANTERN_RACK, 3, 1), DP(HEAL_MACHINE, 7, 1), DP(FLOOR_LAMP, 9, 1), DP(PC, 10, 1),
    DP(PENNANT, 1, 0), DP(CALENDAR, 9, 0),
    DP(TABLE_ROUND, 1, 5), DP(CHAIR, 1, 4), DP(CHAIR, 2, 4), DP(TEA_SET, 0, 6),
    DP(KIN_BASKET, 8, 6), DP(KIN_BASKET, 10, 6), DP(SMALL_PLANT, 10, 7),
};
static const Stamp DUSK_HEARTH_STAMPS[] = { STAMP(I, RUG, 4, 6) };
static const DecorPlace DUSK_SHOP_DECOR[] = {
    DP(BARREL_IN, 0, 2), DP(SACKS_IN, 3, 2), DP(PENNANT, 1, 0),
    DP(SHOP_SHELF, 5, 1), DP(SHOP_SHELF, 7, 1), DP(LANTERN_RACK, 9, 1),
    DP(DISPLAY_CASE, 6, 5), DP(BARREL_IN, 9, 5), DP(SMALL_PLANT, 0, 7), DP(SMALL_RUG, 5, 7),
};
static const DecorPlace APOTHECARY_DECOR[] = {
    DP(SPECIMEN_SHELF, 0, 1), DP(BOOKSHELF_SMALL, 2, 1), DP(SPECIMEN_SHELF, 8, 1),
    DP(FIREPLACE, 4, 1), DP(SACKS_IN, 10, 2), DP(PLANT, 0, 6), DP(SMALL_PLANT, 10, 7),
    DP(TABLE, 7, 5), DP(CHAIR, 7, 4),
};
static const DecorPlace DUSK_HOUSE_DECOR[] = {
    DP(BOOKSHELF, 0, 1), DP(FIREPLACE, 3, 1), DP(BED, 9, 2), DP(MAP_POSTER, 6, 0),
    DP(TABLE, 5, 4), DP(CHAIR, 5, 3), DP(CHAIR, 6, 3), DP(KIN_BASKET, 1, 6), DP(COAT_RACK, 10, 6),
};

/* ---------------- LANTERN CRYPT (the LANTERN Hall, MF_DARK) ---------------- */

static const DecorPlace LANTERN_CRYPT_DECOR[] = {
    DP(CR_PEDESTAL, 11, 2), DP(CR_BRAZIER, 8, 2), DP(CR_BRAZIER, 14, 2),
    DP(CR_STATUE, 2, 2), DP(CR_STATUE, 20, 2), DP(CR_BANNER, 6, 0), DP(CR_BANNER, 16, 0),
    DP(CR_CANDLES, 1, 6), DP(CR_CANDLES, 21, 6),
    DP(CR_PLAQUE, 10, 18), DP(CR_SKULLS, 21, 2), DP(CR_SKULLS, 1, 2),
};

/* ---------------- THE OSSUARY ---------------- */

static const DecorPlace OSSUARY_1_DECOR[] = {
    DP(CR_BRAZIER, 7, 2), DP(CR_BRAZIER, 24, 2),
    DP(CR_SARCOPHAGUS, 12, 9), DP(CR_SARCOPHAGUS, 17, 9), DP(CR_COFFIN, 5, 17), DP(CR_COFFIN, 24, 17),
    DP(CR_SKULLS, 1, 9), DP(CR_SKULLS, 28, 9), DP(CR_SKULLS, 14, 19), DP(CR_URN, 15, 19),
    DP(CR_CANDLES, 1, 2), DP(CR_CANDLES, 28, 2), DP(CR_CHAINS, 11, 1), DP(CR_CHAINS, 21, 1),
};
static const MapObj OSSUARY_1_OBJS[] = { OBJ(CHEST, 28, 4, 255) };
static const DecorPlace OSSUARY_2_DECOR[] = {
    DP(CR_BRAZIER, 12, 2), DP(CR_BRAZIER, 16, 2), DP(CR_STATUE, 9, 2), DP(CR_STATUE, 19, 2),
    DP(CR_SARCOPHAGUS, 22, 9), DP(CR_SARCOPHAGUS, 25, 9), DP(CR_COFFIN, 4, 8),
    DP(CR_SKULLS, 1, 19), DP(CR_SKULLS, 28, 19), DP(CR_URN, 13, 19), DP(CR_URN, 16, 19),
    DP(CR_CANDLES, 1, 2), DP(CR_CANDLES, 28, 2), DP(CR_BANNER, 11, 0), DP(CR_BANNER, 17, 0),
};

static const WildSlot WILD_OSSUARY[] = {
    { SP_CRYPTCLAW, 18, 40, 44, WHEN_ANY }, { SP_OSSIHOUND, 16, 40, 44, WHEN_ANY },
    { SP_SEXTONE, 14, 40, 43, WHEN_ANY }, { SP_SQUEAKLE, 12, 39, 42, WHEN_ANY },
    { SP_NOCTAVE, 12, 41, 44, WHEN_ANY }, { SP_CAWDAVER, 10, 41, 44, WHEN_ANY },
    { SP_RATTLEBONE, 4, 40, 43, WHEN_ANY }, { SP_TRINKIT, 3, 40, 43, WHEN_ANY },
};
static const WildSlot WILD_OSSUARY_DEEP[] = {
    { SP_CRYPTCLAW, 16, 43, 47, WHEN_ANY }, { SP_OSSIHOUND, 14, 43, 47, WHEN_ANY },
    { SP_NOCTAVE, 14, 43, 47, WHEN_ANY }, { SP_BOGSHAMBLE, 12, 43, 47, WHEN_ANY },
    { SP_REAPMANTIS, 12, 44, 47, WHEN_ANY }, { SP_CAWDAVER, 12, 44, 47, WHEN_ANY },
    { SP_RATTLEBONE, 5, 43, 46, WHEN_ANY }, { SP_HOPSHI, 4, 45, 48, WHEN_ANY },
    { SP_TRINKIT, 3, 43, 46, WHEN_ANY },
};

/* ---------------- BONE THRONE ---------------- */

#define BONE_THRONE_X 7   /* the 3x3 throne decor; OSSUREX waits on its middle */
#define BONE_THRONE_Y 2
static const DecorPlace BONE_THRONE_DECOR[] = {
    DP(CR_THRONE, BONE_THRONE_X, BONE_THRONE_Y), DP(CR_BRAZIER, 5, 3), DP(CR_BRAZIER, 11, 3),
    DP(CR_STATUE, 2, 2), DP(CR_STATUE, 14, 2), DP(CR_SKULLS, 1, 12), DP(CR_SKULLS, 15, 12),
    DP(CR_CANDLES, 4, 8), DP(CR_CANDLES, 12, 8), DP(CR_BANNER, 4, 0), DP(CR_BANNER, 12, 0),
};
static const MapObj BONE_THRONE_OBJS[] = { OBJ(LEGEND, 8, 3, SP_OSSUREX) };
