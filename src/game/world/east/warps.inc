/* world/east/warps.inc -- Doors / cave mouths: { MAP_FROM, x, y, MAP_TO, dx, dy },. Owner: W-EAST. */
    { MAP_TOWN, 26, 25, MAP_LAND_OFFICE, 5, 8 },       /* Maple Village: the LAND OFFICE */
    { MAP_LUMEN, 10, 6, MAP_VOLT_HALL, 7, 16 },
    { MAP_LUMEN, 9, 17, MAP_LUMEN_HEARTH, 5, 8 },
    { MAP_LUMEN, 7, 26, MAP_BIKE_SHOP, 5, 8 },
    { MAP_LUMEN, 35, 16, MAP_LUMEN_INN, 5, 8 },
    { MAP_LUMEN, 47, 16, MAP_RESONANCE_WORKS, 6, 9 },
    { MAP_LUMEN, 49, 26, MAP_LUMEN_MARKET, 5, 8 },
    { MAP_LUMEN, 5, 32, MAP_LUMEN_HOUSE, 5, 8 },
    { MAP_LUMEN, 48, 7, MAP_CLOCKWORK_SPIRE, 6, 18 },
    { MAP_LUMEN, 40, 5, MAP_LUMEN_HOUSE_B, 5, 8 },
    { MAP_BROOKMILL, 5, 13, MAP_BROOKMILL_REST, 5, 8 },
    { MAP_BROOKMILL, 31, 13, MAP_BROOKMILL_MILL, 6, 9 },
    { MAP_BROOKMILL, 6, 26, MAP_BROOKMILL_HOUSE, 5, 8 },
    { MAP_COPPERLINE, 25, 7, MAP_COPPER_MINE, 15, 2 },
    { MAP_COPPERLINE, 20, 34, MAP_ACCORD_GATE, 6, 8 }, /* G5 / plan 07 */
    { MAP_ROOTWOOD_PATH, 2, 7, MAP_WOOD, 17, 6, .required_flag = FLAG_VOLT_CREST },
    { MAP_ROOTWOOD_PATH, 17, 3, MAP_ROOTWAYS, 3, 8, .required_flag = FLAG_VOLT_CREST },
    { MAP_ROOTWAYS, 2, 8, MAP_ROOTWOOD_PATH, 16, 3, .required_flag = FLAG_VOLT_CREST },
    { MAP_ROOTWAYS, 21, 3, MAP_MILL_CELLAR, 6, 3, .required_flag = FLAG_VOLT_CREST },
    { MAP_MILL_CELLAR, 6, 2, MAP_ROOTWAYS, 20, 3, .required_flag = FLAG_VOLT_CREST },
    { MAP_MILL_CELLAR, 6, 7, MAP_BROOKMILL_MILL, 6, 5, .required_flag = FLAG_VOLT_CREST },
    { MAP_BROOKMILL_MILL, 6, 6, MAP_MILL_CELLAR, 6, 6, .required_flag = FLAG_VOLT_CREST },
    { MAP_ROOTWAYS, 21, 14, MAP_COPPER_MINE, 4, 18, .required_flag = FLAG_VOLT_CREST },
    { MAP_COPPER_MINE, 3, 18, MAP_ROOTWAYS, 20, 14, .required_flag = FLAG_VOLT_CREST },
    { MAP_COPPER_MINE, 8, 18, MAP_RAILHEAD_SHAFT, 4, 10, .required_flag = FLAG_CREST_ANVIL },
    { MAP_ROOTWAYS, 19, 11, MAP_TIDAL_UNDERFLOW, 11, 3, .required_flag = FLAG_TIDE_CREST },

#include "biomes/warps.inc"
