/* Contract 01 section 5: wild encounter ranges, with a tolerance of one. */
typedef struct { int zone, low, high; } ProgressionLevel;
static const ProgressionLevel progression_levels[] = {
    { ZONE_MEADOW, 2, 9 }, { ZONE_WOOD, 4, 11 },
    { ZONE_LAKE, 5, 11 }, { ZONE_RISE, 9, 15 },
    { ZONE_BROOK_TRAIL, 10, 15 }, { ZONE_COPPERLINE, 14, 19 },
    { ZONE_LUMEN, 16, 22 }, { ZONE_FEN_REEDS, 17, 21 },
    { ZONE_SALTWIND, 19, 23 }, { ZONE_CROSSING, 24, 28 },
    { ZONE_CROSSING_WATER, 25, 29 }, { ZONE_CINDER_ROAD, 26, 30 },
    { ZONE_EMBER_TUNNEL, 27, 32 }, { ZONE_FOOTHILLS_LOW, 28, 32 },
    { ZONE_FROSTPINE, 30, 34 }, { ZONE_GLIMMER, 30, 34 },
    { ZONE_GLIMMER_DEEP, 32, 36 }, { ZONE_DOWNS, 33, 37 },
    { ZONE_ASHEN, 34, 38 }, { ZONE_GRAVEWOOD, 35, 39 },
    { ZONE_MIRE, 36, 40 }, { ZONE_MISTFEN, 37, 41 },
    { ZONE_MOONVEIL, 38, 42 }, { ZONE_DREAMSPIRE, 39, 43 },
    { ZONE_DUST_LIBRARY, 39, 43 }, { ZONE_OSSUARY, 44, 48 },
    { ZONE_OSSUARY_DEEP, 46, 50 }
};
