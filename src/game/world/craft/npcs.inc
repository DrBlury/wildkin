/* world/craft/npcs.inc -- People: PERSON(...), PERSON_KIN(...), WARDEN(...),. Owner: CRAFT system.
 *
 * The three crafting teachers. CRAFT owns these entries; the region owners
 * own the rooms. When a region redraws one of these rooms, move the x / y
 * here (keep one free cell in front of the teacher) and put the station
 * decor next to them in the region's data.h:
 *   MAP_BAKERY      (core, Maple Village)  the CHEF: STOVE / BRICK_OVEN are there already
 *   MAP_APOTHECARY  (W-GRIM, Duskmere)      the BREWER: add DP(CAULDRON, x, y)
 *   MAP_FORGE       (W-FAR, Cindermoor)     the SMITH:  add DP(ANVIL, x, y)
 * Don't add a second SCR_CHEF / SCR_BREWER / SCR_SMITH person anywhere:
 * tools/tests/test_craft.c checks there is at most one of each.
 *
 * The APOTHECARY and THE FORGE are still door-less placeholders, and the
 * map test wants every person reachable from a door, so the brewer and
 * the smith wait here commented out. W-GRIM / W-FAR (or the merger):
 * uncomment the line once the room has its door, and add the decor. */
    PERSON(MAP_BAKERY, 4, 3, VILLAGER, DOWN, LOOK, CHEF, LSRC_CHEF, "CHEF ROSA", 0),
/*  PERSON(MAP_APOTHECARY, 5, 3, HEALER, DOWN, LOOK, BREWER, LSRC_BREWER, "BREWER MOSS", 0),  */
/*  PERSON(MAP_FORGE, 5, 3, HERMIT, DOWN, LOOK, SMITH, LSRC_SMITH, "SMITH BRANN", 0),  */
