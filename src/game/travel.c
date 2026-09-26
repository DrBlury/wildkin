/*
 * Traversal: field abilities (surf, fly, teleport, light, strength), the
 * bike, boats, dark maps, puzzle tiles and map objects, seamless map edges
 * and location banners (docs/EXPANSION.md 7.5). Owner: TRAVERSAL system.
 */

typedef struct {
    u8 visited[16];     /* maps you have been to (fly points), bit per map */
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

/* ---- entry points other modules call (TRAVERSAL owner implements) ---- */

MAYBE_UNUSED static int travel_has_crest(int c) { return (travel.crests >> c) & 1; }

/* A Hall Master hands over a crest. */
MAYBE_UNUSED static void travel_award_crest(int c)
{
    if (c >= 0 && c < CREST_COUNT) travel.crests |= (u8)(1u << c);
}

/* A boat trip to (map, x, y): a sailing cutscene, then you arrive. */
MAYBE_UNUSED static void travel_boat_to(int map, int x, int y)
{
    field_begin_warp(map, x, y, DIR_DOWN);
}

/* The FIELD menu on START: surf, fly, teleport, light, strength, bike. */
MAYBE_UNUSED static void travel_field_menu_open(void)
{
    dlg_say("No field abilities yet.");
}

/* The town map (fly = 1: pick a destination). */
MAYBE_UNUSED static void worldmap_open(int fly)
{
    (void)fly;
    dlg_say("A map of the Vale.");
}

/* LURE INCENSE and WAYSTONE. */
static int travel_use_item(int item)
{
    (void)item;
    dlg_say("Nothing happens.");
    return 0;
}

/* KEY items owned by traversal: BIKE, FERRY PASS, TOWN MAP, CREST CASE. */
static int travel_key_use(int key)
{
    (void)key;
    dlg_say("Not now.");
    return 0;
}

/* Something the player faces that is a map object (boulder, chest, legend,
 * ferry, berry patch...). Return 1 when handled. */
static int obj_interact(int x, int y)
{
    (void)x; (void)y;
    return 0;
}
