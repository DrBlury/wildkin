/*
 * Traversal: field abilities (surf, fly, teleport, light, strength), the
 * bike, boats, dark maps, puzzle tiles and map objects, seamless map edges
 * and location banners (docs/EXPANSION.md 7.5). Owner: TRAVERSAL system.
 */

typedef struct {
    u8 visited[8];      /* MF_TOWN maps you have been to (fly points), bit per map */
    u8 crests;          /* bit per Hall crest (CREST_*) */
    u8 biking, surfing;
    u8 last_hearth;     /* map of the last Hearth Hall (teleport / WAYSTONE) */
    u8 puzzle[16];      /* per-puzzle solved bits */
    u8 pad[5];
} TravelState;

enum { CREST_VOLT, CREST_TIDE, CREST_ANVIL, CREST_RIME, CREST_LANTERN, CREST_DREAM, CREST_COUNT };

static TravelState travel;

static void travel_reset(void)
{
    u8 *raw = (u8 *)&travel;
    for (unsigned i = 0; i < sizeof(travel); i++) raw[i] = 0;
}

static void travel_validate(void)
{
    if (travel.last_hearth >= MAP_COUNT) travel.last_hearth = 0;
    travel.biking &= 1;
    travel.surfing = 0;
}

/* Map objects and puzzle tiles can change how a cell looks (field.c). */
static int travel_dyn_cell(int mx, int my, u16 bottom[4], u16 mid[4], u16 top[4])
{
    (void)mx; (void)my; (void)bottom; (void)mid; (void)top;
    return 0;
}

/* Extra attributes from map objects (a boulder is solid, an open gate isn't). */
static int travel_attr(int x, int y, int a)
{
    (void)x; (void)y;
    return a;
}
