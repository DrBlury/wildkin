/* world/north/warps.inc -- Doors / cave mouths: { MAP_FROM, x, y, MAP_TO, dx, dy },. Owner: W-NORTH.
 * Exit mats lead back out of the nearest door that leads to their map. */
    /* Frosthollow */
    { MAP_FROSTHOLLOW, 6, 13, MAP_FROST_HEARTH, 5, 8 },
    { MAP_FROSTHOLLOW, 12, 13, MAP_FROST_SHOP, 5, 8 },
    { MAP_FROSTHOLLOW, 28, 6, MAP_RIME_HALL, 7, 19 },
    { MAP_FROSTHOLLOW, 10, 31, MAP_FROST_HOUSE, 5, 8 },
    { MAP_FROSTHOLLOW, 39, 35, MAP_STARGAZER, 5, 8 },
    { MAP_FROSTHOLLOW, 38, 27, MAP_HOT_SPRING, 6, 9 },
    { MAP_FROSTHOLLOW, 36, 16, MAP_GLIMMER_1, 19, 29 },
    /* Glimmer Caverns: the stairs between the floors, the crack to the grotto */
    { MAP_GLIMMER_1, 9, 4, MAP_GLIMMER_2, 7, 3 },
    { MAP_GLIMMER_2, 7, 2, MAP_GLIMMER_1, 9, 5 },
    { MAP_GLIMMER_2, 30, 3, MAP_STARFALL, 11, 19 },
