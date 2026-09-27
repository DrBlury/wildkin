/*
 * world/travel/data.h -- map rows, stamps, decor, objects and wild slots.
 * Owner: TRAVERSAL system.
 *
 * Four TEST maps for the traversal systems (reached only through the debug
 * WARP menu; tools/tests/test_travel.c drives them):
 *   TEST SHORE  sand around a lake with an island (SURF, water kin, a
 *               satchel only a surfer reaches), a ferry to TEST ICE and a
 *               ladder down to it
 *   TEST ICE    an ice pond with frozen rocks (sliding), a STRENGTH boulder
 *               in a gap, a static legend, a ferry back and a ladder to
 *               TEST HALL
 *   TEST HALL   a pumice boulder onto a plate opens a gate (room A), a
 *               floor switch drops a barrier (room B), teleport pads,
 *               a chest, a mimic chest and a run of currents
 *   TEST DARK   an MF_DARK grotto (the light circle, LIGHT)
 */

static const char *const TT_SHORE_ROWS[] = {
    "oooooooooooooooooooo",
    "osssssssssssssssssso",
    "osssssssssssssssssso",
    "osssssssssssssssssso",
    "oss~~~~~~~~~~~~~~sso",
    "oss~~~~~~~~~~~~~~sso",
    "oss~~~~ssss~~~~~~sso",
    "oss~~~~ssss~~~~~~sso",
    "oss~~~~ssss~~~~~~sso",
    "oss~~~~~~~~~~~~~~sso",
    "oss~~~~~~~~~~~~~~sso",
    "osssssssssssssssssso",
    "osssssssssssssssssso",
    "osssssssssssssssssso",
    "osssssssssssssssssso",
    "oooooooooooooooooooo",
};

static const char *const TT_ICE_ROWS[] = {
    "RRRRRRRRRRRRRRRRRRRR",
    "R..................R",
    "R.7888888889.......R",
    "R.4iiiiioii6.......R",
    "R.4iiiiiiii6.......R",
    "R.4oiiiiiii6.......R",
    "R.4iiiiiiio6.......R",
    "R.1222222223.......R",
    "R..................R",
    "RRRRRRRR.RRRRRRRRRRR",
    "R..................R",
    "R..................R",
    "R..................R",
    "R..................R",
    "R..................R",
    "RRRRRRRRRRRRRRRRRRRR",
};

static const char *const TT_HALL_ROWS[] = {
    "HHHHHHHHHHHHHHHHHHHH",
    "hhhhhhhhhhhhhhhhhhhh",
    "H_______H__________H",
    "H_______H__________H",
    "H_______H__________H",
    "H_______H__________H",
    "HHHH_HHHHHHHHH_HHHHH",
    "H__________________H",
    "H_H_HH_H___________H",   /* the boulders sit in dead-end slots (x 3, x 6): */
    "H_H_HH_H___________H",   /* they can only be pushed down, deeper in, so   */
    "H_H_HH_H___________H",   /* they never jam the gate corridor or the mat   */
    "H_H_HH_H___________H",
    "H_H_HHHH___________H",
    "H__H_>>>>__________H",
    "H__________________H",
    "HHHHHHHHHMHHHHHHHHHH",
};

static const char *const TT_DARK_ROWS[] = {
    "GGGGGGGGGGGG",
    "gggggggggggg",
    "G::::::::::G",
    "G::::::::::G",
    "G::::G:::::G",
    "G::::G:::::G",
    "G::::::::::G",
    "G::::::::::G",
    "G::::::::::G",
    "GGGGGGGGGGGG",
};

static const MapObj TT_SHORE_OBJS[] = {
    OBJ(FERRY, 16, 12, MAP_TT_ICE),
    OBJ(LADDER, 2, 2, 0),
};

static const MapObj TT_ICE_OBJS[] = {
    OBJ(BOULDER, 8, 9, 0),
    OBJ(LEGEND, 15, 12, SP_HOARFANG),
    OBJ(FERRY, 16, 1, MAP_TT_SHORE),
    OBJ(LADDER, 4, 12, 0),
};

static const MapObj TT_HALL_OBJS[] = {
    OBJ(BOULDER, 3, 9, 0),
    OBJ(BOULDER, 6, 9, 1),
    OBJ(PLATE, 6, 11, 0),
    OBJ(GATE, 4, 6, 0),
    OBJ(CHEST, 2, 3, ITEM_BIG_TONIC),
    OBJ(SWITCH, 16, 9, 1),
    OBJ(BARRIER, 14, 6, 1),
    OBJ(PAD, 17, 12, 2),
    OBJ(PAD, 17, 3, 2),
    OBJ(CHEST, 10, 3, 255),
};

static const WildSlot WILD_TT_SEA[] = {
    { SP_BUBBLIN, 10, 12, 16, WHEN_ANY },
    { SP_AQUAPO, 6, 12, 16, WHEN_ANY },
    { SP_AXOLURK, 2, 16, 18, WHEN_ANY },
};
