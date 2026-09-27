/* Event IDs are available to world NPC condition data. */
enum { EV_NONE, EV_CARAVAN, EV_OUTBREAK, EV_LOST_KIN, EV_SURGE,
       EV_METEOR, EV_NIGHT_MARKET, EV_FISH_MARKET, EV_WASHOUT,
       EV_TOURNEY, EV_TALES, EV_FESTIVAL, EV_COUNT };
enum { FEST_NONE, FEST_KINDLING, FEST_MILLRACE, FEST_LANTERN, FEST_FROST, FEST_STARFALL, FEST_COUNT };
enum { ER_HOME, ER_EAST, ER_WEST, ER_FORGE, ER_NORTH, ER_ASH, ER_DREAM, ER_COUNT };

enum { EV_CARAVAN_STOP_BASE = 32, EV_FEST_KINDLING = 44,
       EV_FEST_MILLRACE, EV_FEST_LANTERN, EV_FEST_FROST, EV_FEST_STARFALL,
       EV_LOST_KIN_PET };

/* Proposed E5 attachment for Brookmill Trail's eastern reeds. The road and
 * raised bridge are at y=17-18; this changes only two optional reed cells.
 * W-EAST must attach this descriptor in its MAP_BROOKMILL_TRAIL initializer. */
static const char *const EVENT_BROOK_WASHOUT_ROWS[] = { "~", "~" };
static const MapPatch EVENT_BROOK_WASHOUT_PATCHES[] = {
    { .x = 45, .y = 25, .w = 1, .h = 2, .rows = EVENT_BROOK_WASHOUT_ROWS,
      .event = EV_WASHOUT },
};
