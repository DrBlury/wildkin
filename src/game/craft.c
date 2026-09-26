/*
 * Crafting: cooking, brewing, forging and energy tuning minigames, recipes
 * and meal buffs (docs/EXPANSION.md 7.3). Owner: CRAFT system.
 */

typedef struct {
    u8 recipes[16];     /* bit per known recipe */
    u8 meal;            /* active MEAL_* buff, 0 = none */
    u8 meal_bouts;      /* bouts left */
    u8 pad[14];
} CraftState;

static CraftState craft;

static void craft_reset(void)
{
    u8 *raw = (u8 *)&craft;
    for (unsigned i = 0; i < sizeof(craft); i++) raw[i] = 0;
}

static void craft_validate(void)
{
}

enum { STATION_COOK, STATION_BREW, STATION_FORGE, STATION_TUNE, STATION_COUNT };

/* Open a crafting station's minigame screen. */
MAYBE_UNUSED static void craft_open(int station)
{
    (void)station;
    dlg_say("You can't craft anything here yet.");
}

/* Examining decor: is it a crafting station? (called before the decor's
 * examine text; return 1 when handled) */
static int station_examine(int decor_kind)
{
    (void)decor_kind;
    return 0;
}

/* ---- meal buffs, read by the bout rules (battle.c) ---- */
MAYBE_UNUSED static int meal_stat_stage(int stat) { (void)stat; return 0; }   /* extra starting stages */
MAYBE_UNUSED static int meal_xp_percent(void) { return 100; }
MAYBE_UNUSED static int meal_catch_bonus(void) { return 0; }                  /* added to the lantern roll, x10 */
MAYBE_UNUSED static void meal_bout_finished(void) {}
