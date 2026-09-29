/* world/west/warps.inc -- Doors / cave mouths: { MAP_FROM, x, y, MAP_TO, dx, dy },. Owner: W-WEST. */
    { MAP_PORT_BRINE, 19, 6, MAP_CURRENT_HALL, 8, 21 },    /* upper town (level 3) */
    { MAP_PORT_BRINE, 18, 15, MAP_BRINE_HEARTH, 5, 8 },    /* west terrace (1) */
    { MAP_PORT_BRINE, 31, 16, MAP_BRINE_SHOP, 5, 8 },      /* east terrace (1) */
    { MAP_PORT_BRINE, 37, 15, MAP_BRINE_INN, 6, 8 },       /* east terrace (1) */
    { MAP_PORT_BRINE, 32, 6, MAP_BRINE_HOUSE, 5, 8 },      /* upper town (3) */
    { MAP_PORT_BRINE, 14, 24, MAP_HARBOR_OFFICE, 6, 8 },   /* west quay (0) */
    { MAP_GULL_ISLE, 11, 11, MAP_GULL_HOUSE, 5, 8 },     /* the Green (level 1) */
    { MAP_GULL_ISLE, 31, 23, MAP_DROWNED_BELL, 9, 17 },  /* the sea cave: a tunnel mouth in the stack (0) */
    { MAP_REEDWICK, 9, 10, MAP_REED_HEARTH, 5, 8 },
    { MAP_REEDWICK, 15, 10, MAP_REED_SHOP, 5, 8 },
    { MAP_HERON_FEN, 12, 8, MAP_REED_TUNNEL, 3, 10 },
    { MAP_HERON_FEN, 41, 33, MAP_FEN_HERMIT, 5, 8 }, /* SURF-only island */
    { MAP_REED_TUNNEL, 2, 10, MAP_HERON_FEN, 12, 10 },
    { MAP_REED_TUNNEL, 17, 3, MAP_TIDAL_UNDERFLOW, 4, 10, FLAG_TIDE_CREST },
    { MAP_TIDAL_UNDERFLOW, 3, 10, MAP_REED_TUNNEL, 16, 3, FLAG_TIDE_CREST },
    { MAP_REEDWICK, 23, 23, MAP_TIDAL_UNDERFLOW, 26, 5, FLAG_TIDE_CREST },
    { MAP_TIDAL_UNDERFLOW, 27, 5, MAP_REEDWICK, 22, 23, FLAG_TIDE_CREST },
    { MAP_PORT_BRINE, 35, 33, MAP_TIDAL_UNDERFLOW, 26, 14, FLAG_TIDE_CREST },
    { MAP_TIDAL_UNDERFLOW, 27, 14, MAP_PORT_BRINE, 35, 34, FLAG_TIDE_CREST },
    { MAP_TIDAL_UNDERFLOW, 10, 3, MAP_ROOTWAYS, 20, 11, FLAG_TIDE_CREST },

#include "biomes/warps.inc"
