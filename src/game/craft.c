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
