/*
 * world/elev/data.h -- the elevation TEST map. Owner: ELEVATION system
 * (docs/ELEVATION.md; src/game/elev.c; tools/tests/test_elevation.c).
 *
 * TEST HEIGHTS (debug WARP menu only) shows every elevation feature:
 *   - two plateaus (height 1) with irregular edges either side of a gorge
 *     (a path beside a stream, height 0) and a mesa (height 2) on the east
 *     plateau
 *   - a bridge (rows 9-10) walked east-west on top, and north-south
 *     underneath along the gorge
 *   - stairs up (6,14) (19,14) and to the mesa (23,9), side stairs from the
 *     gorge up the west plateau (12,6), stairs down the north side (18,4)
 *   - ledges to hop off the east plateau (24-26,14)
 *   - a tunnel under the west plateau (column 4, mouth at (4,14))
 *   - a hidden passage through the trees (24-25,19) to a satchel
 */

static const char *const EV_TEST_ROWS[] = {
    "TTTTTTTTTTTT==~~TTTTTTTTTTTTTT", /*  0 */
    "tttttttttttt==~~tttttttttttttt", /*  1 */
    "TT..........==~~............TT", /*  2 */
    "tt..=.......==~~..=.........tt", /*  3 */
    "TT..=.......==~~..=.........TT", /*  4 */
    "tt..=.......==~~....yy..yy..tt", /*  5 */
    "TT..=...r...==~~....r....r..TT", /*  6 */
    "tt..=.......==~~............tt", /*  7 */
    "TT..=.......==~~.......=....TT", /*  8 */
    "tt..=.========~~====...=....tt", /*  9 */
    "TT..=.========~~====........TT", /* 10 */
    "tt..=.=.....==~~...=........tt", /* 11 */
    "TT..=.=.....==~~...=........TT", /* 12 */
    "tt..=.=.....==~~...=........tt", /* 13 */
    "TT..=.=.....==~~...=........TT", /* 14 */
    "tt..=.=.....==~~...=........tt", /* 15 */
    "TT..==========~~....=...TTTTTT", /* 16 */
    "tt..........==~~....=...tttttt", /* 17 */
    "TT..,,,,....==~~,,,,=...TT..TT", /* 18 */
    "tt..,,,,....==~~,,,,====tt..tt", /* 19 */
    "TT..........==~~,,,,....TT..TT", /* 20 */
    "tt..........==~~........tt..tt", /* 21 */
    "TTTTTTTTTTTT==~~TTTTTTTTTTTTTT", /* 22 */
    "tttttttttttt==~~tttttttttttttt", /* 23 */
};

/* heights ('0'..'3'), stairs ('^' 'v' '<' '>') and ledges ('_') */
static const char *const EV_TEST_ELEV[] = {
    "000000000000000000000000000000", /*  0 */
    "000000000000000000000000000000", /*  1 */
    "000000000000000000000000000000", /*  2 */
    "000000000000000000000000000000", /*  3 */
    "000000000000000000v00000000000", /*  4 */
    "001101111111000011112222221100", /*  5 */
    "001101111111<00011112222221100", /*  6 */
    "001101111111000011112222221100", /*  7 */
    "001101111111000011112222221100", /*  8 */
    "00110111111100001111111^111100", /*  9 */
    "001101111111000011111111111100", /* 10 */
    "001101111111000011111111111100", /* 11 */
    "000101111111000011111111111100", /* 12 */
    "000001111111000011111111111000", /* 13 */
    "000000^000000000000^0000___000", /* 14 */
    "000000000000000000000000000000", /* 15 */
    "000000000000000000000000000000", /* 16 */
    "000000000000000000000000000000", /* 17 */
    "000000000000000000000000000000", /* 18 */
    "000000000000000000000000000000", /* 19 */
    "000000000000000000000000000000", /* 20 */
    "000000000000000000000000000000", /* 21 */
    "000000000000000000000000000000", /* 22 */
    "000000000000000000000000000000", /* 23 */
};

static const ElevFeat EV_TEST_FEATS[] = {
    EF(BRIDGE_H, 12, 9, 4, 2),   /* over the gorge: E-W on top, N-S below */
    EF(TUNNEL, 4, 5, 1, 9),      /* under the west plateau; mouth at (4,14) */
    EF(HIDDEN, 24, 19, 2, 1),    /* through the trees to the nook */
};

static const DecorPlace EV_TEST_DECOR[] = {
    DP(SIGNPOST, 8, 15), DP(SIGNPOST, 10, 6), DP(BUSH, 2, 2), DP(BUSH, 26, 2),
    DP(ROCK, 9, 19), DP(FLOWER_POT, 17, 6), DP(LAMP, 16, 11),
};
