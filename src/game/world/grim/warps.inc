/* world/grim/warps.inc -- Doors / stairs: { MAP_FROM, x, y, MAP_TO, dx, dy },. Owner: W-GRIM.
 * There is no door into THE OSSUARY: the gate warden in DUSKMERE opens it (scripts.c). */
    { MAP_DUSKMERE, 12, 12, MAP_DUSK_HEARTH, 5, 8 },
    { MAP_DUSKMERE, 17, 12, MAP_DUSK_SHOP, 5, 8 },
    { MAP_DUSKMERE, 6, 34, MAP_APOTHECARY, 5, 8 },
    { MAP_DUSKMERE, 40, 26, MAP_DUSK_HOUSE, 5, 8 },
    { MAP_DUSKMERE, 34, 7, MAP_LANTERN_CRYPT, 11, 22 },
    /* the Ossuary stairs (doors cut into the walls) */
    { MAP_OSSUARY_1, 4, 1, MAP_DUSKMERE, 35, 19 },
    { MAP_OSSUARY_1, 26, 1, MAP_OSSUARY_2, 26, 2 },
    { MAP_OSSUARY_2, 26, 1, MAP_OSSUARY_1, 26, 2 },
    { MAP_OSSUARY_2, 14, 1, MAP_BONE_THRONE, 8, 13 },
    { MAP_ACCORD_GATE, 6, 1, MAP_HOLLOW_DOWNS, 20, 2 },
    { MAP_ACCORD_GATE, 6, 8, MAP_COPPERLINE, 20, 34 },
    { MAP_HOLLOW_DOWNS, 20, 1, MAP_ACCORD_GATE, 6, 2 },
    { MAP_HOLLOW_DOWNS, 30, 8, MAP_WAYCHAPEL, 6, 8 },
    { MAP_HOLLOW_DOWNS, 11, 13, MAP_BARROW_A, 6, 6 },
    { MAP_HOLLOW_DOWNS, 29, 10, MAP_BARROW_B, 6, 6 },
