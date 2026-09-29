/* Rename to test_biome_redesign.c only after the coordinator applies the
 * guarded regional spans. This file is intentionally not Makefile-collected. */
#include "harness.h"

typedef struct { int map, x, y; char tile; } Beat;
static const Beat beats[] = {
    { MAP_BROOKMILL_TRAIL, 30, 9, '.' }, { MAP_BROOKMILL, 15, 20, '=' },
    { MAP_HERON_FEN, 35, 8, '=' }, { MAP_REEDWICK, 23, 8, '=' },
    { MAP_SALTWIND, 25, 5, '.' }, { MAP_PORT_BRINE, 20, 24, 's' },
    { MAP_GULL_ISLE, 16, 15, '=' }, { MAP_FROSTPINE, 29, 32, '=' },
    { MAP_TIMBERLINE, 24, 14, '=' }, { MAP_FROSTHOLLOW, 26, 30, '=' },
    { MAP_EMBER_TUNNEL, 9, 9, '_' }, { MAP_CALDERA, 4, 3, 'y' },
    { MAP_CINDERMOOR, 31, 12, '=' }, { MAP_RAILHEAD, 13, 22, '=' },
    { MAP_MOONVEIL, 16, 20, 'f' }, { MAP_DREAMSPIRE, 25, 24, 'f' },
    { MAP_HOLLOW_DOWNS, 44, 9, 'd' }, { MAP_GRAVEWOOD, 5, 5, 'g' },
    { MAP_DUSKMERE, 18, 28, 'd' },
};

static int flavor(int map, const char *needle)
{
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].map == map && NPCS[i].text && strstr(NPCS[i].text, needle))
            return 1;
    return 0;
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    fresh_game();
    give_starter();
    for (unsigned i = 0; i < sizeof beats / sizeof beats[0]; i++) {
        const Beat *b = &beats[i];
        CHECK(MAPS[b->map].w <= 64 && MAPS[b->map].h <= 64 &&
              MAPS[b->map].rows[b->y][b->x] == b->tile,
              "authored location survives map decoding");
        map_load(b->map);
        printf("map %d (%d,%d): ", b->map, b->x, b->y);
        CHECK(flood_open(b->x, b->y, FLOOD_WALK),
              "authored 3-wide route beat is actually walkable");
    }
    /* A straight-line crossing is impossible at each new terrain pinch;
     * both sides remain connected by the ordinary walking graph. */
    static const struct { int map, sx, sy, wallx, wally, tx, ty, bendx, bendy; } bends[] = {
        { MAP_BROOKMILL_TRAIL, 14, 17, 21, 17, 26, 17, 21, 19 },
        { MAP_SALTWIND, 4, 19, 11, 19, 19, 19, 11, 21 },
        { MAP_FROSTPINE, 19, 26, 19, 27, 19, 29, 21, 28 },
        { MAP_MOONVEIL, 24, 19, 24, 20, 24, 24, 23, 21 },
    };
    for (unsigned i = 0; i < sizeof bends / sizeof bends[0]; i++) {
        const int map = bends[i].map;
        map_load(map);
        CHECK(!flood_open(bends[i].wallx, bends[i].wally, FLOOD_WALK),
              "old straight route gains a solid landscape obstacle");
        CHECK(flood_open(bends[i].bendx, bends[i].bendy, FLOOD_WALK),
              "winding route has a walkable bend");
        flood(bends[i].sx, bends[i].sy);
        CHECK(reached(bends[i].tx, bends[i].ty) &&
              reached(bends[i].bendx, bends[i].bendy),
              "detour and destination reachable from original lane");
    }
    CHECK(flavor(MAP_BROOKMILL, "mill wheel"), "Brookmill night fiddler custom");
    CHECK(flavor(MAP_REEDWICK, "weave the walk boards"), "Reedwick reed-craft custom");
    CHECK(flavor(MAP_PORT_BRINE, "nets dry"), "Port Brine net-yard custom");
    CHECK(flavor(MAP_GULL_ISLE, "shell grit"), "Gull Isle salvage garden custom");
    CHECK(flavor(MAP_TIMBERLINE, "sawmill flume"), "Timberline sawmill custom");
    CHECK(flavor(MAP_FROSTHOLLOW, "steam from the spring"), "Frosthollow geothermal custom");
    CHECK(flavor(MAP_CINDERMOOR, "cooled Caldera stone"), "Cindermoor forge custom");
    CHECK(flavor(MAP_RAILHEAD, "lantern repairs"), "Railhead night-shift custom");
    CHECK(flavor(MAP_DREAMSPIRE, "paper lanterns"), "Dreamspire night garden custom");
    CHECK(flavor(MAP_DUSKMERE, "memorial lanterns"), "Duskmere lantern custom");
    /* Existing portals and shape-changing stories must remain where they are. */
    CHECK(MAPS[MAP_HERON_FEN].rows[19][28] == '=' &&
          MAPS[MAP_EMBER_TUNNEL].rows[6][15] == '_' &&
          MAPS[MAP_DUSKMERE].rows[20][28] == 'm',
          "fen project bridge, guarded Caldera passage and Duskmere underpass unchanged");
    return failures ? 1 : 0;
}
