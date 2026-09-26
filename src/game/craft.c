/*
 * Crafting (docs/EXPANSION.md 7.3). Owner: CRAFT system.
 *
 *   recipes      32 recipes at three stations (kitchen, cauldron, forge).
 *                Four are known from the start; the chef, the brewer and
 *                the smith teach the rest as LESSONs (gated by how many
 *                things you have made at their station), and three books
 *                (COOKBOOK, BREW NOTES, FORGE MANUAL) teach the last ones.
 *   stations     decor you face and press A on (station_examine): STOVE,
 *                BRICK OVEN, CAMPFIRE, COOKTOP -> kitchen; CAULDRON ->
 *                cauldron; ANVIL -> forge. The three teachers also lend
 *                their station from their menu (craft_open).
 *   the screen   craft_open(station) / the RECIPE BOOK: a recipe list per
 *                station with have/need counts, a batch picker (1-10), then
 *                the station's minigame and a rating: PERFECT (>= 90),
 *                GREAT (>= 60), OK (>= 25) or a fail (BURNT / FIZZLED /
 *                CRACKED). A fail costs one batch of ingredients; B during
 *                the intro costs nothing.
 *   minigames    KITCHEN: three pan tosses on a heat gauge, then stir by
 *                rolling the D-pad. CAULDRON: hold A to heat, keep the
 *                needle in a drifting band, then A at the big bubble's
 *                peak. FORGE: A on the beat as marks reach the anvil, then
 *                the quench.
 *   rewards      lanterns and potions: GREAT adds half a batch, PERFECT a
 *                whole batch more. Food keeps its quality (fine / perfect
 *                counts per dish); eating a dish gives a meal buff (one at
 *                a time) for a few bouts, scaled by that quality.
 *   meal buffs   read by the bout rules in battle.c: meal_stat_stage,
 *                meal_xp_percent, meal_catch_bonus, meal_bout_finished;
 *                meal_lure_active for traversal (rare kin).
 *
 * VRAM while a minigame runs: backdrop on BG0 (charblock 0, SB 24, BG banks
 * 0-5), text windows on BG1, sprites in OBJ tiles 768-1023 and OBJ banks
 * 9-14 only. Leaving always goes through field_load_tileset() (via
 * field_return or before reopening the bag).
 */

/* ---------------- ids ---------------- */

enum { STATION_COOK, STATION_BREW, STATION_FORGE, STATION_TUNE, STATION_COUNT };
#define CRAFT_STATIONS 3      /* the three owned here; TUNE is the fusion owner's */

/* IK_FOOD params (items/craft.inc): dishes and drinks 0-12, books 20-22. */
enum { MEAL_TART, MEAL_BUN, MEAL_STEW, MEAL_CHILI, MEAL_PIE, MEAL_MOONCAKE, MEAL_TRUFFLE,
       MEAL_SKEWER, MEAL_SALAD, MEAL_CANDY, MEAL_JUICE, MEAL_APPLE, MEAL_NECTAR, MEAL_COUNT };
enum { FOOD_BOOK_COOK = 20, FOOD_BOOK_BREW, FOOD_BOOK_FORGE };

enum { RATE_FAIL = -1, RATE_OK, RATE_GREAT, RATE_PERFECT };

enum {
    /* kitchen */
    RC_BERRY_TART, RC_BERRY_JUICE, RC_HONEY_BUN, RC_VEGGIE_STEW, RC_CAMP_SKEWER, RC_CHILI_POT,
    RC_SUN_SALAD, RC_APPLE_PRESS, RC_MOONCAKE, RC_KERNEL_CANDY, RC_PUMPKIN_PIE, RC_PEACH_NECTAR,
    RC_TRUFFLE_RICE,
    /* cauldron */
    RC_GLOW_TONIC, RC_HONEY_DROP, RC_VIGOR_DRAUGHT, RC_BRIGHT_TONIC, RC_CLARITY_BREW,
    RC_RADIANT_TONIC, RC_REVIVAL_BREW, RC_LURE_INCENSE,
    /* forge */
    RC_LANTERN, RC_PRISM_LANTERN, RC_DUSK_LANTERN, RC_TIDE_LANTERN, RC_BONE_LANTERN,
    RC_HEAVY_LANTERN, RC_SPRINKLER, RC_STAR_LANTERN, RC_QUICK_LANTERN, RC_TUNING_FORK,
    RC_HUSH_BELL,
    RC_COUNT
};

/* where a recipe comes from */
enum { SRC_START, SRC_LESSON, SRC_BOOK };

typedef struct { u8 item, qty; } Ingredient;
typedef struct {
    u8 station, result, yield, source;
    u8 marks;                 /* forge: hammer marks (4-6); kitchen: food colour */
    Ingredient in[3];         /* qty 0 = unused */
} Recipe;

#define ING(i, n) { ITEM_##i, n }
#define NO_ING { 0, 0 }

static const Recipe RECIPES[RC_COUNT] = {
    /* ---- kitchen ---- */
    [RC_BERRY_TART]    = { STATION_COOK, ITEM_BERRY_TART, 1, SRC_START, 0, { ING(CROP_GLOWBERRY, 2), ING(GLOW_HONEY, 1), NO_ING } },
    [RC_BERRY_JUICE]   = { STATION_COOK, ITEM_BERRY_JUICE, 2, SRC_START, 1, { ING(CROP_GLOWBERRY, 2), NO_ING, NO_ING } },
    [RC_HONEY_BUN]     = { STATION_COOK, ITEM_HONEY_BUN, 2, SRC_LESSON, 2, { ING(GLOW_HONEY, 2), ING(SALT, 1), NO_ING } },
    [RC_VEGGIE_STEW]   = { STATION_COOK, ITEM_VEGGIE_STEW, 1, SRC_LESSON, 3, { ING(CROP_POTATO, 1), ING(CROP_CARROT, 1), ING(SALT, 1) } },
    [RC_CAMP_SKEWER]   = { STATION_COOK, ITEM_CAMP_SKEWER, 1, SRC_LESSON, 3, { ING(CROP_CORN, 1), ING(CROP_TOMATO, 1), ING(SALT, 1) } },
    [RC_CHILI_POT]     = { STATION_COOK, ITEM_CHILI_POT, 1, SRC_LESSON, 4, { ING(CROP_CHILI, 2), ING(CROP_TOMATO, 1), NO_ING } },
    [RC_SUN_SALAD]     = { STATION_COOK, ITEM_SUN_SALAD, 1, SRC_LESSON, 5, { ING(CROP_SUNFLOWER, 1), ING(CROP_RADISH, 1), ING(MINT_LEAF, 1) } },
    [RC_APPLE_PRESS]   = { STATION_COOK, ITEM_APPLE_PRESS, 2, SRC_LESSON, 6, { ING(CROP_APPLE, 2), NO_ING, NO_ING } },
    [RC_MOONCAKE]      = { STATION_COOK, ITEM_MOONCAKE, 1, SRC_LESSON, 2, { ING(CROP_MOTEBLOOM, 1), ING(GLOW_HONEY, 1), NO_ING } },
    [RC_KERNEL_CANDY]  = { STATION_COOK, ITEM_KERNEL_CANDY, 1, SRC_LESSON, 7, { ING(GLOW_HONEY, 2), ING(MOTE_DUST, 2), NO_ING } },
    [RC_PUMPKIN_PIE]   = { STATION_COOK, ITEM_PUMPKIN_PIE, 1, SRC_BOOK, 6, { ING(CROP_PUMPKIN, 1), ING(GLOW_HONEY, 1), NO_ING } },
    [RC_PEACH_NECTAR]  = { STATION_COOK, ITEM_PEACH_NECTAR, 1, SRC_BOOK, 7, { ING(CROP_PEACH, 2), ING(GLOW_HONEY, 1), NO_ING } },
    [RC_TRUFFLE_RICE]  = { STATION_COOK, ITEM_TRUFFLE_RICE, 1, SRC_BOOK, 3, { ING(GLOWCAP, 2), ING(CROP_CORN, 1), ING(SALT, 1) } },
    /* ---- cauldron ---- */
    [RC_GLOW_TONIC]    = { STATION_BREW, ITEM_TONIC, 2, SRC_START, 0, { ING(MINT_LEAF, 1), ING(GLOW_HONEY, 1), NO_ING } },
    [RC_HONEY_DROP]    = { STATION_BREW, ITEM_MINT_TEA, 2, SRC_LESSON, 0, { ING(GLOW_HONEY, 2), NO_ING, NO_ING } },
    [RC_VIGOR_DRAUGHT] = { STATION_BREW, ITEM_VIGOR_DRAUGHT, 1, SRC_LESSON, 0, { ING(GLOWCAP, 1), ING(MINT_LEAF, 2), NO_ING } },
    [RC_BRIGHT_TONIC]  = { STATION_BREW, ITEM_BIG_TONIC, 2, SRC_LESSON, 0, { ING(GLOWCAP, 1), ING(GLOW_HONEY, 1), NO_ING } },
    [RC_CLARITY_BREW]  = { STATION_BREW, ITEM_CLARITY_BREW, 1, SRC_LESSON, 0, { ING(MINT_LEAF, 2), ING(SALT, 1), ING(GLOW_HONEY, 1) } },
    [RC_RADIANT_TONIC] = { STATION_BREW, ITEM_GRAND_TONIC, 1, SRC_LESSON, 0, { ING(GLOWCAP, 2), ING(GLOW_HONEY, 1), ING(MOTE_DUST, 1) } },
    [RC_REVIVAL_BREW]  = { STATION_BREW, ITEM_REVIVAL_BREW, 1, SRC_BOOK, 0, { ING(GLOWCAP, 2), ING(BONE_MEAL, 1), ING(STARDUST_CHIP, 1) } },
    [RC_LURE_INCENSE]  = { STATION_BREW, ITEM_LURE_INCENSE, 1, SRC_BOOK, 0, { ING(MOTE_DUST, 2), ING(MINT_LEAF, 1), NO_ING } },
    /* ---- forge ---- */
    [RC_LANTERN]       = { STATION_FORGE, ITEM_LANTERN, 3, SRC_START, 4, { ING(HEARTGLASS_SAND, 1), ING(IRON_ORE, 1), NO_ING } },
    [RC_PRISM_LANTERN] = { STATION_FORGE, ITEM_GLOW_LANTERN, 2, SRC_LESSON, 4, { ING(HEARTGLASS_SAND, 2), ING(IRON_ORE, 1), NO_ING } },
    [RC_DUSK_LANTERN]  = { STATION_FORGE, ITEM_DUSK_LANTERN, 1, SRC_LESSON, 5, { ING(HEARTGLASS_SAND, 1), ING(IRON_ORE, 1), ING(COAL, 2) } },
    [RC_TIDE_LANTERN]  = { STATION_FORGE, ITEM_TIDE_LANTERN, 1, SRC_LESSON, 5, { ING(HEARTGLASS_SAND, 1), ING(IRON_ORE, 1), ING(SALT, 2) } },
    [RC_BONE_LANTERN]  = { STATION_FORGE, ITEM_BONE_LANTERN, 1, SRC_LESSON, 5, { ING(HEARTGLASS_SAND, 1), ING(IRON_ORE, 1), ING(BONE_MEAL, 2) } },
    [RC_HEAVY_LANTERN] = { STATION_FORGE, ITEM_HEAVY_LANTERN, 1, SRC_LESSON, 6, { ING(HEARTGLASS_SAND, 1), ING(IRON_ORE, 3), ING(COAL, 1) } },
    [RC_SPRINKLER]     = { STATION_FORGE, ITEM_SPRINKLER, 1, SRC_LESSON, 5, { ING(IRON_ORE, 2), ING(COAL, 1), NO_ING } },
    [RC_STAR_LANTERN]  = { STATION_FORGE, ITEM_STAR_LANTERN, 1, SRC_LESSON, 6, { ING(HEARTGLASS_SAND, 2), ING(STARDUST_CHIP, 1), ING(IRON_ORE, 1) } },
    [RC_QUICK_LANTERN] = { STATION_FORGE, ITEM_QUICK_LANTERN, 1, SRC_BOOK, 5, { ING(HEARTGLASS_SAND, 1), ING(IRON_ORE, 1), ING(SILK_THREAD, 1) } },
    [RC_TUNING_FORK]   = { STATION_FORGE, ITEM_SOOTHE_BALM, 2, SRC_BOOK, 4, { ING(IRON_ORE, 1), ING(COAL, 1), NO_ING } },
    [RC_HUSH_BELL]     = { STATION_FORGE, ITEM_HUSH_BELL, 1, SRC_BOOK, 6, { ING(IRON_ORE, 2), ING(SILK_THREAD, 1), NO_ING } },
};

/* The teachers' lessons, in order, and how many things you must have made
 * at their station before each one. */
static const u8 LESSONS_COOK[] = { RC_HONEY_BUN, RC_VEGGIE_STEW, RC_CAMP_SKEWER, RC_CHILI_POT,
                                   RC_SUN_SALAD, RC_APPLE_PRESS, RC_MOONCAKE, RC_KERNEL_CANDY };
static const u8 GATES_COOK[] = { 0, 1, 2, 4, 6, 8, 11, 15 };
static const u8 LESSONS_BREW[] = { RC_HONEY_DROP, RC_VIGOR_DRAUGHT, RC_BRIGHT_TONIC, RC_CLARITY_BREW,
                                   RC_RADIANT_TONIC };
static const u8 GATES_BREW[] = { 0, 1, 3, 5, 8 };
static const u8 LESSONS_FORGE[] = { RC_PRISM_LANTERN, RC_DUSK_LANTERN, RC_TIDE_LANTERN, RC_BONE_LANTERN,
                                    RC_HEAVY_LANTERN, RC_SPRINKLER, RC_STAR_LANTERN };
static const u8 GATES_FORGE[] = { 0, 1, 2, 4, 6, 8, 11 };

typedef struct { const u8 *recipes, *gates; u8 count; } LessonPlan;
static const LessonPlan LESSONS[CRAFT_STATIONS] = {
    { LESSONS_COOK, GATES_COOK, (u8)sizeof(LESSONS_COOK) },
    { LESSONS_BREW, GATES_BREW, (u8)sizeof(LESSONS_BREW) },
    { LESSONS_FORGE, GATES_FORGE, (u8)sizeof(LESSONS_FORGE) },
};

/* What each book teaches. */
static const u8 BOOK_COOK_RC[] = { RC_PUMPKIN_PIE, RC_PEACH_NECTAR, RC_TRUFFLE_RICE };
static const u8 BOOK_BREW_RC[] = { RC_REVIVAL_BREW, RC_LURE_INCENSE };
static const u8 BOOK_FORGE_RC[] = { RC_QUICK_LANTERN, RC_TUNING_FORK, RC_HUSH_BELL };

static const char *const STATION_NAMES[CRAFT_STATIONS] = { "KITCHEN", "CAULDRON", "FORGE" };
static const char *const STATION_VERB[CRAFT_STATIONS] = { "COOK", "BREW", "FORGE" };
static const char *const RATE_NAMES[4] = { "FAIL", "OK", "GREAT", "PERFECT" };

/* Meal buffs: bouts they last at OK / GREAT / PERFECT (0 = eaten at once). */
static const u8 MEAL_BOUTS[MEAL_COUNT][3] = {
    [MEAL_TART] = { 5, 7, 10 }, [MEAL_BUN] = { 5, 7, 10 }, [MEAL_STEW] = { 3, 5, 7 },
    [MEAL_CHILI] = { 3, 5, 7 }, [MEAL_PIE] = { 5, 7, 10 }, [MEAL_MOONCAKE] = { 5, 7, 10 },
    [MEAL_TRUFFLE] = { 3, 5, 7 }, [MEAL_SKEWER] = { 3, 5, 7 },
};

/* ---------------- state (saved) ---------------- */

enum { CF_MET_CHEF = 1, CF_MET_BREWER = 2, CF_MET_SMITH = 4 };

typedef struct {
    u8 recipes[16];     /* bit per known recipe (RC_*) */
    u8 meal;            /* active buff: MEAL_* + 1, 0 = none */
    u8 meal_bouts;      /* bouts left */
    u8 meal_tier;       /* RATE_OK / GREAT / PERFECT of the dish eaten */
    u8 flags;           /* CF_* */
    u16 made[4];        /* successful crafts per station (lesson gates) */
    u8 fine[16];        /* GREAT-or-better dishes in the bag, per MEAL_* */
    u8 perfect[16];     /* PERFECT dishes in the bag (<= fine) */
    u8 cursor[4];       /* recipe list cursor per station */
    u8 batch;           /* last batch size */
    u8 pad[7];
} CraftState;

static CraftState craft;

static int recipe_known(int r) { return r >= 0 && r < RC_COUNT && ((craft.recipes[r >> 3] >> (r & 7)) & 1); }
static void recipe_learn(int r) { if (r >= 0 && r < RC_COUNT) craft.recipes[r >> 3] |= (u8)(1u << (r & 7)); }

static void craft_reset(void)
{
    u8 *raw = (u8 *)&craft;
    for (unsigned i = 0; i < sizeof(craft); i++) raw[i] = 0;
    for (int r = 0; r < RC_COUNT; r++)
        if (RECIPES[r].source == SRC_START) recipe_learn(r);
    craft.batch = 1;
}

/* The MEAL_* id of a food item, or -1. */
static int meal_of(int item)
{
    if (item < 0 || item >= ITEM_COUNT || ITEMS[item].kind != IK_FOOD) return -1;
    return ITEMS[item].param < MEAL_COUNT ? ITEMS[item].param : -1;
}

/* The food item for a MEAL_* id, or -1. */
static int meal_item(int meal)
{
    for (int i = 0; i < ITEM_COUNT; i++)
        if (meal_of(i) == meal) return i;
    return -1;
}

/* Keep the quality counts within what the bag really holds. */
static void craft_sync_quality(void)
{
    for (int m = 0; m < 16; m++) {
        int it = m < MEAL_COUNT ? meal_item(m) : -1;
        int have = it >= 0 ? bag[it] : 0;
        if (craft.fine[m] > have) craft.fine[m] = (u8)clampi(have, 0, 255);
        if (craft.perfect[m] > craft.fine[m]) craft.perfect[m] = craft.fine[m];
    }
}

static void craft_validate(void)
{
    for (int r = RC_COUNT; r < 128; r++) craft.recipes[r >> 3] &= (u8)~(1u << (r & 7));
    for (int r = 0; r < RC_COUNT; r++)
        if (RECIPES[r].source == SRC_START) recipe_learn(r);
    if (craft.meal > MEAL_COUNT || craft.meal_tier > RATE_PERFECT) craft.meal = 0;
    if (craft.meal && !MEAL_BOUTS[craft.meal - 1][0]) craft.meal = 0;
    if (craft.meal_bouts > 10) craft.meal_bouts = 10;
    if (!craft.meal || !craft.meal_bouts) {
        craft.meal = 0;
        craft.meal_bouts = 0;
        craft.meal_tier = 0;
    }
    craft.flags &= CF_MET_CHEF | CF_MET_BREWER | CF_MET_SMITH;
    for (int s = 0; s < 4; s++) {
        if (craft.made[s] > 9999) craft.made[s] = 9999;
        if (craft.cursor[s] >= RC_COUNT) craft.cursor[s] = 0;
    }
    craft.batch = (u8)clampi(craft.batch, 1, 10);
    for (int i = 0; i < 7; i++) craft.pad[i] = 0;
    craft_sync_quality();
}

/* ---------------- recipe rules ---------------- */

/* How many batches the bag can pay for (0..10). */
static int recipe_batches(int r)
{
    int n = 10;
    for (int k = 0; k < 3; k++) {
        const Ingredient *g = &RECIPES[r].in[k];
        if (!g->qty) continue;
        int can = bag[g->item] / g->qty;
        if (can < n) n = can;
    }
    return n;
}

static int rating_of(int score)
{
    if (score >= 90) return RATE_PERFECT;
    if (score >= 60) return RATE_GREAT;
    if (score >= 25) return RATE_OK;
    return RATE_FAIL;
}

/* Items you get for `batch` batches at `rating` (0 on a fail). */
static int craft_yield(int r, int batch, int rating)
{
    if (rating == RATE_FAIL) return 0;
    int n = RECIPES[r].yield * batch;
    if (meal_of(RECIPES[r].result) >= 0) return n;       /* food keeps its quality instead */
    if (rating == RATE_GREAT) n += (batch + 1) / 2;
    if (rating == RATE_PERFECT) n += batch;
    return n;
}

/* Pays the ingredients and hands out the result. Returns the item count. */
static int craft_apply(int r, int batch, int rating)
{
    const Recipe *rc = &RECIPES[r];
    int pay = rating == RATE_FAIL ? 1 : batch;         /* a fail costs one batch */
    for (int k = 0; k < 3; k++)
        if (rc->in[k].qty) bag_add(rc->in[k].item, -rc->in[k].qty * pay);
    int n = craft_yield(r, batch, rating);
    if (!n) return 0;
    bag_add(rc->result, n);
    int m = meal_of(rc->result);
    if (m >= 0 && rating >= RATE_GREAT) {
        craft.fine[m] = (u8)clampi(craft.fine[m] + n, 0, 255);
        if (rating == RATE_PERFECT) craft.perfect[m] = (u8)clampi(craft.perfect[m] + n, 0, 255);
    }
    craft.made[rc->station] = (u16)clampi(craft.made[rc->station] + batch, 0, 9999);
    craft_sync_quality();
    return n;
}

/* The next lesson a teacher has for you (RC_*), -1 when none are left.
 * *gate = how many things you must have made first. */
static int lesson_next(int station, int *gate)
{
    const LessonPlan *p = &LESSONS[station];
    for (int i = 0; i < p->count; i++)
        if (!recipe_known(p->recipes[i])) {
            if (gate) *gate = p->gates[i];
            return p->recipes[i];
        }
    return -1;
}

/* ---------------- meal buffs (battle.c reads these) ---------------- */

static int meal_active(void) { return craft.meal && craft.meal_bouts ? craft.meal - 1 : -1; }

/* Extra starting stages for every kin you send out (STAT_*). */
static int meal_stat_stage(int stat)
{
    int m = meal_active(), up = craft.meal_tier == RATE_PERFECT ? 2 : 1;
    switch (m) {
    case MEAL_STEW: return stat == STAT_DEF || stat == STAT_SPD ? up : 0;
    case MEAL_CHILI: return stat == STAT_ATK || stat == STAT_SPA ? up : 0;
    case MEAL_SKEWER: return stat == STAT_SPE ? up : 0;
    default: return 0;
    }
}

/* XP multiplier in percent (100 = no bonus). */
static int meal_xp_percent(void)
{
    static const u8 TART[3] = { 125, 135, 150 }, TRUFFLE[3] = { 150, 175, 200 };
    int m = meal_active(), t = clampi(craft.meal_tier, 0, 2);
    if (m == MEAL_TART) return TART[t];
    if (m == MEAL_TRUFFLE) return TRUFFLE[t];
    return 100;
}

/* Added to a lantern's finesse (x10 units: 3 = +0.3). */
static int meal_catch_bonus(void)
{
    static const u8 PIE[3] = { 3, 4, 6 };
    return meal_active() == MEAL_PIE ? PIE[clampi(craft.meal_tier, 0, 2)] : 0;
}

/* Rare kin are more likely while a MOONCAKE lasts: 0 or strength 1-3. */
MAYBE_UNUSED static int meal_lure_active(void)
{
    return meal_active() == MEAL_MOONCAKE ? clampi(craft.meal_tier, 0, 2) + 1 : 0;
}

/* Once per finished bout: the HONEY BUN heals, and the buff counts down. */
static void meal_bout_finished(void)
{
    int m = meal_active();
    if (m < 0) return;
    if (m == MEAL_BUN) {
        static const u8 PCT[3] = { 10, 15, 20 };
        int pct = PCT[clampi(craft.meal_tier, 0, 2)];
        for (int i = 0; i < party_count; i++) {
            Monster *k = &party[i];
            if (!k->hp || k->hp >= k->max_hp) continue;
            int add = k->max_hp * pct / 100;
            k->hp = (u16)clampi(k->hp + (add > 0 ? add : 1), 0, k->max_hp);
        }
    }
    if (--craft.meal_bouts == 0) {
        craft.meal = 0;
        craft.meal_tier = 0;
    }
}

/* "CHILI POT (GREAT), 4 bouts left" or "no meal buff" */
static void meal_status_text(char *buf)
{
    int m = meal_active();
    if (m < 0) {
        str_copy(buf, "No meal buff. Eat a dish before a bout!");
        return;
    }
    str_copy(buf, "MEAL: ");
    str_put(buf, ITEMS[meal_item(m)].name);
    str_put(buf, " (");
    str_put(buf, RATE_NAMES[clampi(craft.meal_tier, 0, 2) + 1]);
    str_put(buf, "), ");
    str_put_int(buf, craft.meal_bouts);
    str_put(buf, craft.meal_bouts == 1 ? " bout left" : " bouts left");
}

/* ---------------- eating and reading (from the bag) ---------------- */

/* Quality of the next dish taken from the bag, and take it. */
static int food_take(int item)
{
    int m = meal_of(item), tier = RATE_OK;
    craft_sync_quality();
    if (m >= 0) {
        if (craft.perfect[m]) {
            tier = RATE_PERFECT;
            craft.perfect[m]--;
            craft.fine[m]--;
        } else if (craft.fine[m]) {
            tier = RATE_GREAT;
            craft.fine[m]--;
        }
    }
    bag[item]--;
    return tier;
}

/* A dish's quality if it were eaten now (without taking it). */
static int food_peek_tier(int item)
{
    int m = meal_of(item);
    craft_sync_quality();
    if (m < 0) return RATE_OK;
    return craft.perfect[m] ? RATE_PERFECT : craft.fine[m] ? RATE_GREAT : RATE_OK;
}

static void put_tier(char *msg, int tier)
{
    if (tier == RATE_OK) return;
    str_put(msg, tier == RATE_PERFECT ? " It was perfect!" : " It was great!");
}

static int craft_read_book(int item, int book)
{
    const u8 *list = book == FOOD_BOOK_COOK ? BOOK_COOK_RC : book == FOOD_BOOK_BREW ? BOOK_BREW_RC : BOOK_FORGE_RC;
    int n = book == FOOD_BOOK_COOK ? (int)sizeof(BOOK_COOK_RC)
          : book == FOOD_BOOK_BREW ? (int)sizeof(BOOK_BREW_RC) : (int)sizeof(BOOK_FORGE_RC);
    char msg[MSG_TEXT_MAX];
    int learned = 0;
    str_copy(msg, "You read the ");
    str_put(msg, ITEMS[item].name);
    str_put(msg, " from cover to cover.");
    for (int i = 0; i < n; i++) {
        if (recipe_known(list[i])) continue;
        recipe_learn(list[i]);
        str_put(msg, learned ? ", " : "\fYou learned: ");
        str_put(msg, ITEMS[RECIPES[list[i]].result].name);
        learned++;
    }
    if (!learned) {
        dlg_say("You already know everything in this book.");
        return 0;
    }
    str_put(msg, "!");
    bag[item]--;
    sfx_play(SFX_LORE);
    dlg_say(msg);
    return 1;
}

/* Heal one kin by `amount` (0 = fully, moves too). */
static int food_heal_one(Monster *k, int amount, char *msg)
{
    const char *name = SPECIES[k->species].name;
    if (!k->hp) return 0;
    if (amount) {
        if (k->hp >= k->max_hp) return 0;
        int before = k->hp;
        k->hp = (u16)clampi(k->hp + amount, 0, k->max_hp);
        str_copy(msg, name);
        str_put(msg, "'s HP was restored by ");
        str_put_int(msg, k->hp - before);
        str_put(msg, " points.");
        return 1;
    }
    int any = k->hp < k->max_hp || k->status != STATUS_NONE;
    for (int i = 0; i < MAX_MOVES; i++)
        if (k->moves[i] != MOVE_NONE && k->moves[i] < MOVE_COUNT && k->pp[i] < MOVES[k->moves[i]].pp) any = 1;
    if (!any) return 0;
    k->hp = k->max_hp;
    k->status = STATUS_NONE;
    k->sleep_turns = 0;
    for (int i = 0; i < MAX_MOVES; i++)
        if (k->moves[i] != MOVE_NONE && k->moves[i] < MOVE_COUNT) k->pp[i] = MOVES[k->moves[i]].pp;
    str_copy(msg, name);
    str_put(msg, " is fully refreshed, moves and all!");
    return 1;
}

/* Eating a meal or drink from the bag (slot = the kin it was used on). */
static int craft_use_food(int item, int slot)
{
    char msg[MSG_TEXT_MAX];
    if (item < 0 || item >= ITEM_COUNT || bag[item] <= 0) return 0;
    int p = ITEMS[item].param;
    if (p >= FOOD_BOOK_COOK && p <= FOOD_BOOK_FORGE) return craft_read_book(item, p);
    int m = meal_of(item);
    if (m < 0) return 0;
    int tier = food_peek_tier(item);
    Monster *k = slot >= 0 && slot < party_count ? &party[slot] : 0;
    switch (m) {
    case MEAL_SALAD: {
        static const u8 PCT[3] = { 50, 65, 80 };
        int any = 0;
        for (int i = 0; i < party_count; i++) {
            Monster *t = &party[i];
            if (!t->hp || t->hp >= t->max_hp) continue;
            t->hp = (u16)clampi(t->hp + t->max_hp * PCT[tier] / 100 + 1, 0, t->max_hp);
            any = 1;
        }
        if (!any) return 0;
        food_take(item);
        str_copy(msg, "Your team shared the SUN SALAD. Everyone feels much better!");
        put_tier(msg, tier);
        sfx_play(SFX_HEAL);
        dlg_say(msg);
        return 1;
    }
    case MEAL_JUICE: case MEAL_APPLE: case MEAL_NECTAR: {
        static const u8 HP[3][3] = { { 40, 50, 60 }, { 80, 100, 120 }, { 0, 0, 0 } };
        if (!k || !food_heal_one(k, HP[m - MEAL_JUICE][tier], msg)) return 0;
        food_take(item);
        put_tier(msg, tier);
        sfx_play(SFX_HEAL);
        dlg_say(msg);
        return 1;
    }
    case MEAL_CANDY: {
        static const u8 BOND[3] = { 5, 10, 20 };
        if (!k || k->level >= MAX_LEVEL) return 0;
        food_take(item);
        monster_level_up(k);
        if (k->hp == 0) k->hp = 1;
        k->bond = (u8)clampi(k->bond + BOND[tier], 0, 255);
        str_copy(msg, SPECIES[k->species].name);
        str_put(msg, " crunched the KERNEL CANDY and grew to Lv. ");
        str_put_int(msg, k->level);
        str_put(msg, "!");
        put_tier(msg, tier);
        sfx_play(SFX_LEVEL_UP);
        dlg_say(msg);
        u8 moves[4];
        int n = learnset_at(k->species, k->level, moves);
        for (int i = 0; i < n; i++) learn_begin(slot, moves[i]);
        int into = monster_level_evolution(k);
        if (into >= 0) evo_request(slot, into);
        return 1;
    }
    default:
        break;
    }
    /* a buff meal: the whole team eats; it replaces the one before */
    int old = meal_active();
    food_take(item);
    craft.meal = (u8)(m + 1);
    craft.meal_tier = (u8)tier;
    craft.meal_bouts = MEAL_BOUTS[m][tier];
    str_copy(msg, "Your team ate the ");
    str_put(msg, ITEMS[item].name);
    str_put(msg, ".");
    put_tier(msg, tier);
    if (old >= 0 && old != m) {
        str_put(msg, "\fIt replaces the ");
        str_put(msg, ITEMS[meal_item(old)].name);
        str_put(msg, " from before.");
    }
    str_put(msg, "\fThe meal lasts ");
    str_put_int(msg, craft.meal_bouts);
    str_put(msg, " bouts.");
    sfx_play(SFX_HEAL);
    dlg_say(msg);
    return 1;
}

/* ================================================================ */
/*  The crafting screen: recipe list, batch, minigame, result        */
/* ================================================================ */

enum { CS_LIST, CS_BATCH, CS_INTRO, CS_PLAY, CS_RESULT };
enum { FROM_FIELD, FROM_BAG };

#define CG_OT      768          /* first OBJ tile we may use */
#define CG_OT_END  1024
#define CB_METAL   9            /* OBJ banks 9-14 */
#define CB_FOOD    10
#define CB_LABEL   11
#define CB_SPARK   12
#define CB_BAD     13
#define CB_BUBBLE  14
#define CG_ROWS    6
#define GAUGE_X    68           /* the gauge in the top window */
#define GAUGE_W    152
#define GAUGE_Y    18
#define FORGE_HIT_X 88          /* where the marks meet the anvil */
#define FORGE_LEAD 60
#define CG_PARTS   10

typedef struct { s16 x, y, vx, vy; u8 life, frame; } CraftPart;

static struct {
    int state, station, tab, from, redraw;
    int list[RC_COUNT], count, cursor, scroll;
    int batch, recipe;
    const char *note;
    int t, phase, score, rating, made;
    /* labels and particles */
    int lbl, lbl_t, lbl_bank;
    CraftPart part[CG_PARTS];
    /* kitchen */
    int toss, needle, ndir, zone, zone_w, flip_t, stir_acc, stir_oct, stir_pts;
    /* cauldron */
    int heat, vel, band, inband, bub_t, bub_cycles, heat_pts, bub_pts;
    /* forge */
    int marks, beat, mark_state[6], hammer_t, quench_t;
    u16 tile[CSP_COUNT];
} cg;

static void field_return(void);

/* ---------------- sprites ---------------- */

static void cg_upload(const u8 *ids, int n)
{
    int t = CG_OT;
    for (int i = 0; i < n; i++) {
        const CraftSprite *s = &craft_sprites[ids[i]];
        int count = s->tiles * s->frames;
        if (t + count > CG_OT_END) break;
        cg.tile[ids[i]] = (u16)t;
        copy32(VRAM_OBJ_TILES + t * 8, craft_sprite_gfx + s->first * 8, (unsigned)count * 8);
        t += count;
    }
}

/* One craft sprite (64-wide images are two 32-wide halves). prio 0 draws
 * over the text windows (gauge needles), 1 under them (the scene). */
static void cg_spr_p(int id, int frame, int x, int y, int bank, int flags, int prio)
{
    const CraftSprite *s = &craft_sprites[id];
    int tile = cg.tile[id] + frame * s->tiles;
    int shape = s->w == 8 ? SQ8 : s->w == 16 ? (s->h == 32 ? TALL16x32 : SQ16)
              : s->h == 32 ? SQ32 : WIDE32x16;
    if (s->w == 64) {
        int half = s->tiles / 2, flip = flags & ATTR1_HFLIP;
        spr_push(x, y, tile + (flip ? half : 0), shape, bank, prio, flags);
        spr_push(x + 32, y, tile + (flip ? 0 : half), shape, bank, prio, flags);
        return;
    }
    spr_push(x, y, tile, shape, bank, prio, flags);
}

static void cg_spr(int id, int frame, int x, int y, int bank, int flags)
{
    cg_spr_p(id, frame, x, y, bank, flags, 1);
}

static void cg_label(int csp, int bank)
{
    cg.lbl = csp;
    cg.lbl_t = 36;
    cg.lbl_bank = bank;
}

static void cg_burst(int x, int y, int n, int frame)
{
    for (int i = 0, k = 0; i < CG_PARTS && k < n; i++) {
        if (cg.part[i].life) continue;
        CraftPart *p = &cg.part[i];
        p->x = (s16)(x * 16);
        p->y = (s16)(y * 16);
        p->vx = (s16)((int)rng_range(64) - 32);
        p->vy = (s16)(-24 - (int)rng_range(32));
        p->life = (u8)(16 + rng_range(10));
        p->frame = (u8)frame;
        k++;
    }
}

static void cg_parts_update(void)
{
    for (int i = 0; i < CG_PARTS; i++) {
        CraftPart *p = &cg.part[i];
        if (!p->life) continue;
        p->life--;
        p->x = (s16)(p->x + p->vx);
        p->y = (s16)(p->y + p->vy);
        p->vy = (s16)(p->vy + 4);
    }
    if (cg.lbl_t > 0) cg.lbl_t--;
}

static void cg_parts_draw(void)
{
    for (int i = 0; i < CG_PARTS; i++)
        if (cg.part[i].life)
            cg_spr(CSP_CHUNK, cg.part[i].frame, cg.part[i].x / 16, cg.part[i].y / 16, CB_SPARK, 0);
    if (cg.lbl_t <= 0) return;
    const CraftSprite *s = &craft_sprites[cg.lbl];
    if (cg.state == CS_RESULT) {
        /* the final rating: twice the size, popping in */
        int k = clampi(cg.t * 32, 128, 512), aff = oam_affine_scale_rot(k, k, 0);
        int halves = s->w / 32, tile = cg.tile[cg.lbl];
        for (int h = 0; h < halves; h++) {
            int cx = 120 + (h * 2 - (halves - 1)) * 16 * k / 256;
            spr_push_affine(cx - 16, 52, tile + h * 8, WIDE32x16, cg.lbl_bank, 0, 0, aff, 1);
        }
        return;
    }
    int rise = cg.lbl_t < 36 ? (36 - cg.lbl_t) / 4 : 0;
    cg_spr_p(cg.lbl, 0, 120 - s->w / 2, 40 - rise, cg.lbl_bank, 0, 0);
}

/* ---------------- canvas helpers ---------------- */

/* A bag icon by item (its ICON_* image). */
static void craft_draw_icon(int cx, int cy, int item)
{
    int icon = ITEMS[item].icon < ICON_COUNT ? ITEMS[item].icon : 0;
    for (int i = 0; i < 16; i++) bg_palette[BANK_ITEM_ICON * 16 + i] = item_icon_pal[icon][i];
    canvas_image(cx, cy, 3, 3, item_icon_gfx[icon], 1, BANK_ITEM_ICON);
}

/* A text window along the bottom, as tall as the text needs. */
static void cg_bottom(const char *text)
{
    char wrapped[200];
    text_wrap(wrapped, text, 220);
    int lines = 1;
    for (const char *c = wrapped; *c; c++) lines += *c == '\n';
    int rows = lines * 2 + 2;
    canvas_window(0, CANVAS_ROWS - rows, CANVAS_COLS, rows, WIN_STD);
    text_draw(12, (CANVAS_ROWS - rows) * 8 + 8, wrapped);
}

/* ---------------- the recipe list ---------------- */

static void cg_build_list(void)
{
    cg.count = 0;
    for (int r = 0; r < RC_COUNT; r++)
        if (RECIPES[r].station == cg.tab) cg.list[cg.count++] = r;
    cg.cursor = clampi(craft.cursor[cg.tab], 0, cg.count - 1);
    if (cg.scroll > cg.cursor) cg.scroll = cg.cursor;
    if (cg.cursor >= cg.scroll + CG_ROWS) cg.scroll = cg.cursor - CG_ROWS + 1;
}

static const char *const SOURCE_HINT[CRAFT_STATIONS][3] = {
    { "", "The chef teaches this one.", "It's in the COOKBOOK." },
    { "", "The brewer teaches this one.", "It's in the BREW NOTES." },
    { "", "The smith teaches this one.", "It's in the FORGE MANUAL." },
};

static void cg_list_redraw(void)
{
    char buf[48];
    screen_begin(1);
    /* tabs */
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    if (cg.station >= 0) {
        str_copy(buf, STATION_NAMES[cg.station]);
        str_put(buf, ": what will you ");
        str_put(buf, STATION_VERB[cg.station]);
        str_put(buf, "?");
        text_draw_col(12, 8, buf, INK_BLUE, INK_BLUE_SH);
    } else {
        text_draw(8, 8, "<");
        for (int s = 0; s < CRAFT_STATIONS; s++) {
            if (s == cg.tab) text_draw_col(22 + s * 72, 8, STATION_NAMES[s], INK_BLUE, INK_BLUE_SH);
            else text_draw(22 + s * 72, 8, STATION_NAMES[s]);
        }
        text_draw(224, 8, ">");
    }
    /* the list */
    canvas_window(0, 3, 15, 12, WIN_STD);
    for (int i = 0; i < CG_ROWS && cg.scroll + i < cg.count; i++) {
        int idx = cg.scroll + i, r = cg.list[idx], y = 32 + i * 14;
        if (idx == cg.cursor) text_draw(8, y, "{");
        if (!recipe_known(r)) text_draw_col(18, y, "?????", INK_SHADOW, 0);
        else if (recipe_batches(r) > 0) text_draw_col(18, y, ITEMS[RECIPES[r].result].name, INK_GREEN, INK_GREEN_SH);
        else text_draw(18, y, ITEMS[RECIPES[r].result].name);
    }
    if (cg.scroll > 0) text_draw_col(104, 22, "^", INK_BLUE, INK_BLUE_SH);
    if (cg.scroll + CG_ROWS < cg.count) text_draw_col(104, 104, "}", INK_BLUE, INK_BLUE_SH);
    /* the recipe */
    canvas_window(15, 3, 15, 12, WIN_STD);
    int r = cg.list[cg.cursor];
    const Recipe *rc = &RECIPES[r];
    if (recipe_known(r)) {
        craft_draw_icon(16, 4, rc->result);
        text_draw_fit(156, 30, ITEMS[rc->result].name, 72);
        str_copy(buf, "makes ");
        str_put_int(buf, rc->yield);
        text_draw_col(156, 44, buf, INK_BLUE, INK_BLUE_SH);
        for (int k = 0; k < 3; k++) {
            const Ingredient *g = &rc->in[k];
            if (!g->qty) continue;
            int y = 64 + k * 14;
            text_draw_fit(130, y, ITEMS[g->item].name, 72);
            buf[0] = 0;
            str_put_int(buf, bag[g->item]);
            str_put(buf, "/");
            str_put_int(buf, g->qty);
            if (bag[g->item] < g->qty) text_draw_col(228 - text_width(buf), y, buf, INK_RED, INK_RED_SH);
            else text_draw_right(228, y, buf);
        }
    } else {
        char wrapped[96];
        text_draw_col(130, 30, "NOT LEARNED", INK_SHADOW, 0);
        text_wrap(wrapped, SOURCE_HINT[rc->station][rc->source], 96);
        text_draw(130, 50, wrapped);
    }
    /* the bottom line */
    if (cg.note) {
        cg_bottom(cg.note);
    } else {
        char meal[64];
        meal_status_text(meal);
        canvas_window(0, 15, CANVAS_COLS, 5, WIN_STD);
        text_draw(12, 126, meal);
        text_draw_col(12, 142, cg.station >= 0 ? "A: choose   B: leave" : "A: choose   LEFT/RIGHT: station   B: close",
                      INK_BLUE, INK_BLUE_SH);
    }
    if (cg.state == CS_BATCH) {
        canvas_window(16, 7, 14, 7, WIN_STD);
        str_copy(buf, "BATCHES  x");
        str_put_int(buf, cg.batch);
        text_draw(136, 64, buf);
        str_copy(buf, "you get ");
        str_put_int(buf, rc->yield * cg.batch);
        text_draw(136, 78, buf);
        text_draw_col(136, 92, "</> amount", INK_BLUE, INK_BLUE_SH);
    }
}

/* ---------------- opening and closing ---------------- */

static void craft_update(void);
static void craft_draw(void);

static void cg_open(int station, int from)
{
    dialog_clear();
    cg.station = station;
    cg.tab = station >= 0 ? station : 0;
    cg.from = from;
    cg.state = CS_LIST;
    cg.note = 0;
    cg.scroll = 0;
    cg.lbl_t = 0;
    for (int i = 0; i < CG_PARTS; i++) cg.part[i].life = 0;
    cg_build_list();
    ext_open(craft_update, craft_draw, 0);
    cg_list_redraw();
    cg.redraw = 1;     /* again next frame: a closing dialog clears its box after us */
}

/* Open a crafting station's screen (lent by a teacher or from its decor). */
static void craft_open(int station)
{
    if (station < 0 || station >= CRAFT_STATIONS) {
        dlg_say("The mixer hums. (Energy tuning lives at the RESONANCE WORKS.)");
        return;
    }
    cg_open(station, FROM_FIELD);
}

static void cg_close(void)
{
    canvas_clear();
    if (cg.from == FROM_BAG) {
        field_load_tileset();
        bag_screen_open(BAGCTX_FIELD);
    } else {
        field_return();
    }
}

/* ---------------- minigame: setup ---------------- */

static const u8 CG_SPR_COOK[] = { CSP_PAN, CSP_FOOD, CSP_CHUNK, CSP_SPOON, CSP_POINTER, CSP_LBL_PERFECT,
                                  CSP_LBL_GREAT, CSP_LBL_GOOD, CSP_LBL_OK, CSP_LBL_MISS, CSP_LBL_BURNT };
static const u8 CG_SPR_BREW[] = { CSP_LIQUID, CSP_BUBBLE, CSP_POINTER, CSP_CHUNK, CSP_LBL_PERFECT,
                                  CSP_LBL_GREAT, CSP_LBL_GOOD, CSP_LBL_OK, CSP_LBL_MISS, CSP_LBL_FIZZLED };
static const u8 CG_SPR_FORGE[] = { CSP_HAMMER, CSP_INGOT, CSP_MARK, CSP_CHUNK, CSP_BUBBLE, CSP_LBL_PERFECT,
                                   CSP_LBL_GREAT, CSP_LBL_GOOD, CSP_LBL_OK, CSP_LBL_MISS, CSP_LBL_CRACKED };

/* food tints for the pan, by Recipe.marks on kitchen recipes */
static const u16 FOOD_COL[8][2] = {
    { RGB15(26, 8, 14), RGB15(31, 26, 12) },  /* berry red */
    { RGB15(20, 8, 26), RGB15(28, 20, 31) },  /* juice purple */
    { RGB15(30, 22, 8), RGB15(31, 30, 20) },  /* golden bun */
    { RGB15(24, 14, 6), RGB15(16, 24, 8) },   /* stew brown */
    { RGB15(30, 8, 4), RGB15(31, 24, 4) },    /* chili red */
    { RGB15(16, 26, 8), RGB15(31, 29, 8) },   /* greens */
    { RGB15(31, 18, 6), RGB15(31, 28, 16) },  /* orange */
    { RGB15(28, 24, 14), RGB15(31, 31, 24) }, /* cream */
};

static void cg_backdrop(int cbg)
{
    const CraftBackdrop *b = &craft_backdrops[cbg];
    copy32(VRAM_SCENE_TILES, b->tiles, (unsigned)b->tile_count * 8);
    u16 *dst = VRAM_MAP(SB_FIELD_BOTTOM);
    for (int i = 0; i < 20 * 32; i++) dst[i] = b->map[i];
    for (int i = 20 * 32; i < 32 * 32; i++) dst[i] = b->map[19 * 32];
    for (int k = 0; k < 6; k++) copy16(bg_palette + k * 16, b->pal[k], 16);
    REG_BG0HOFS = 0;
    REG_BG0VOFS = 0;
    REG_BG0CNT = BGCNT_CHARBLOCK(0) | BGCNT_SCREENBLOCK(SB_FIELD_BOTTOM) | BGCNT_PRIO(3);
    REG_DISPCNT = DCNT_MODE0 | DCNT_BG0 | DCNT_BG1 | DCNT_OBJ | DCNT_OBJ_1D;
}

static const char *const CG_HOWTO[CRAFT_STATIONS] = {
    "Toss the pan: press A when the needle is in the green zone, three times. Then stir by rolling the D-pad in circles!",
    "Hold A to heat, let go to cool. Keep the needle in the green band. Then press A when the big bubble is fullest!",
    "Press A as each mark reaches the anvil line. Keep the beat, then let the iron quench!",
};

static void cg_gauge_window(void)
{
    canvas_window(1, 0, 28, 4, WIN_STD);
}

static void cg_intro(void)
{
    cg.state = CS_INTRO;
    int st = RECIPES[cg.recipe].station;
    canvas_clear();
    dialog_clear();
    cg_backdrop(st == STATION_COOK ? CBG_KITCHEN : st == STATION_BREW ? CBG_APOTHECARY : CBG_FORGE);
    if (st == STATION_COOK) cg_upload(CG_SPR_COOK, (int)sizeof(CG_SPR_COOK));
    else if (st == STATION_BREW) cg_upload(CG_SPR_BREW, (int)sizeof(CG_SPR_BREW));
    else cg_upload(CG_SPR_FORGE, (int)sizeof(CG_SPR_FORGE));
    load_pal(obj_palette + CB_METAL * 16, cpal_metal);
    build_fx_palette(CB_LABEL, RGB15(30, 22, 4), RGB15(31, 30, 18));
    build_fx_palette(CB_BAD, RGB15(20, 8, 8), RGB15(28, 20, 18));
    build_fx_palette(CB_SPARK, RGB15(31, 20, 4), RGB15(31, 31, 20));
    build_fx_palette(CB_BUBBLE, RGB15(8, 22, 20), RGB15(24, 31, 30));
    if (st == STATION_COOK) {
        const u16 *c = FOOD_COL[RECIPES[cg.recipe].marks & 7];
        build_fx_palette(CB_FOOD, c[0], c[1]);
    } else if (st == STATION_BREW) {
        build_fx_palette(CB_FOOD, RGB15(6, 14, 28), RGB15(20, 28, 31));
    } else {
        build_fx_palette(CB_FOOD, RGB15(31, 14, 2), RGB15(31, 30, 12));
    }
    char buf[64];
    cg_gauge_window();
    str_copy(buf, ITEMS[RECIPES[cg.recipe].result].name);
    str_put(buf, "  x");
    str_put_int(buf, cg.batch);
    text_draw(14, 11, buf);
    text_draw_col(226 - text_width("A: start  B: back"), 11, "A: start  B: back", INK_BLUE, INK_BLUE_SH);
    cg_bottom(CG_HOWTO[st]);
    cg.t = 0;
    cg.phase = 0;
    cg.score = 0;
    cg.lbl_t = 0;
}

/* ---------------- minigame: kitchen ---------------- */

static void cook_new_toss(void)
{
    static const u8 ZONE_W[3] = { 28, 22, 16 };
    cg.zone_w = ZONE_W[clampi(cg.toss, 0, 2)];
    int lo = cg.zone_w / 2 + 4, hi = GAUGE_W - cg.zone_w / 2 - 4;
    cg.zone = lo + (int)rng_range((unsigned)(hi - lo));
    cg.needle = 0;
    cg.ndir = 1;
    cg.t = 0;
}

static void cook_gauge_draw(void)
{
    cg_gauge_window();
    canvas_fill(GAUGE_X - 1, GAUGE_Y - 1, GAUGE_W + 2, 8, INK_DARK);
    canvas_fill(GAUGE_X, GAUGE_Y, GAUGE_W, 6, INK_SHADOW);
    if (cg.phase == 0) {
        canvas_fill(GAUGE_X + cg.zone - cg.zone_w / 2, GAUGE_Y, cg.zone_w, 6, 13);
        canvas_fill(GAUGE_X + cg.zone - 3, GAUGE_Y, 7, 6, 12);
        char buf[24];
        str_copy(buf, "TOSS ");
        str_put_int(buf, cg.toss + 1);
        str_put(buf, "/3");
        text_draw(12, 11, buf);
    } else {
        int px = clampi(absi(cg.stir_acc) * GAUGE_W / 48, 0, GAUGE_W);
        if (px) canvas_fill(GAUGE_X, GAUGE_Y, px, 6, 12);
        text_draw(12, 11, "STIR!");
    }
}

/* Points for one toss: needle vs zone centre. */
static int cook_toss_points(int needle, int zone, int zone_w)
{
    int d = absi(needle - zone);
    if (d <= 3) return 25;
    if (d <= zone_w / 2) return 17;
    return 0;
}

/* D-pad octant 0..7 clockwise from UP, or -1. */
static int dpad_octant(void)
{
    int u = (keys_now & KEY_UP) != 0, d = (keys_now & KEY_DOWN) != 0;
    int l = (keys_now & KEY_LEFT) != 0, r = (keys_now & KEY_RIGHT) != 0;
    if (u && r) return 1;
    if (d && r) return 3;
    if (d && l) return 5;
    if (u && l) return 7;
    if (u) return 0;
    if (r) return 2;
    if (d) return 4;
    if (l) return 6;
    return -1;
}

/* Stirring: the signed octant steps become the score (6 turns = 25). */
static int cook_stir_points(int acc)
{
    return clampi(absi(acc) * 25 / 48, 0, 25);
}

static void cook_update(void)
{
    cg.t++;
    if (cg.phase == 0) {                       /* the tosses */
        static const u8 SPEED[3] = { 32, 40, 48 };
        if (cg.flip_t > 0) {
            if (--cg.flip_t == 0) {
                if (++cg.toss >= 3) {
                    cg.phase = 1;
                    cg.t = 0;
                    cg.stir_acc = 0;
                    cg.stir_oct = -1;
                } else {
                    cook_new_toss();
                }
                cook_gauge_draw();
            }
            return;
        }
        cg.needle += cg.ndir * SPEED[cg.toss];
        if (cg.needle >= (GAUGE_W - 1) * 16) { cg.needle = (GAUGE_W - 1) * 16; cg.ndir = -1; }
        if (cg.needle <= 0) { cg.needle = 0; cg.ndir = 1; }
        if (key_hit(KEY_A) || cg.t > 300) {
            int pts = cg.t > 300 ? 0 : cook_toss_points(cg.needle / 16, cg.zone, cg.zone_w);
            cg.score += pts;
            cg_label(pts == 25 ? CSP_LBL_PERFECT : pts ? CSP_LBL_GOOD : CSP_LBL_MISS, pts ? CB_LABEL : CB_BAD);
            sfx_play(pts == 25 ? SFX_PERFECT : pts ? SFX_SWING : SFX_MISS);
            if (pts) cg_burst(116, 100, 4, (int)rng_range(4));
            cg.flip_t = 32;
        }
        return;
    }
    /* stirring */
    int o = dpad_octant();
    if (o >= 0) {
        if (cg.stir_oct >= 0 && o != cg.stir_oct) {
            int d = (o - cg.stir_oct + 8) % 8;
            if (d <= 2) cg.stir_acc += d;
            else if (d >= 6) cg.stir_acc -= 8 - d;
            if ((absi(cg.stir_acc) & 7) == 0) sfx_play(SFX_RUSTLE);
            cook_gauge_draw();
        }
        cg.stir_oct = o;
    }
    if (cg.t >= 180) {
        cg.stir_pts = cook_stir_points(cg.stir_acc);
        cg.score += cg.stir_pts;
        cg.phase = 2;
    }
}

static void cook_draw(void)
{
    int px = 88, py = 96;
    if (cg.state == CS_PLAY && cg.phase == 0) {
        cg_spr_p(CSP_POINTER, 0, GAUGE_X + cg.needle / 16 - 8, 5, CB_METAL, 0, 0);
    }
    /* the food: flies up while a toss is in the air */
    int fy = py + 4, flip = 0;
    if (cg.flip_t > 0) {
        int k = 32 - cg.flip_t;                   /* 0..31 */
        fy -= (k * (32 - k)) / 6;
        flip = k > 8 && k < 24;
    }
    int jump = cg.flip_t > 26 ? -4 : 0;
    if (cg.state == CS_PLAY && cg.phase == 1) {
        /* the spoon circles the pan with the D-pad */
        int a = (cg.stir_oct < 0 ? 0 : cg.stir_oct) * 32;
        int sx = px + 20 + soft_sin(a) / 5, sy = py - 22 - soft_sin(a + 64) / 10;
        cg_spr(CSP_FOOD, (cg.t >> 3) & 1, px + 8 + soft_sin(a + 128) / 32, fy, CB_FOOD, 0);
        cg_spr(CSP_SPOON, 0, sx, sy, CB_METAL, 0);
    } else {
        cg_spr(CSP_FOOD, flip, px + 8, fy, CB_FOOD, 0);
    }
    cg_spr(CSP_PAN, 0, px, py + jump, CB_METAL, 0);
}

/* ---------------- minigame: cauldron ---------------- */

#define BREW_FRAMES 300
#define BREW_CYCLE  64
#define BREW_PEAK   40

static int brew_band_center(int t)
{
    return 50 + soft_sin(t * 256 / 200) * 22 / 64 + soft_sin(t * 256 / 77) * 6 / 64;
}

/* 85% of the frames in the band is worth the full 70. */
static int brew_heat_points(int inband, int total)
{
    return total > 0 ? clampi(inband * 70 * 100 / (total * 85), 0, 70) : 0;
}

static int brew_bubble_points(int t_in_cycle)
{
    int d = absi(t_in_cycle - BREW_PEAK);
    if (d <= 3) return 30;
    if (d <= 8) return 18;
    return 0;
}

static void brew_gauge_draw(void)
{
    cg_gauge_window();
    canvas_fill(GAUGE_X - 1, GAUGE_Y - 1, GAUGE_W + 2, 8, INK_DARK);
    canvas_fill(GAUGE_X, GAUGE_Y, GAUGE_W, 6, INK_SHADOW);
    if (cg.phase == 0) {
        int c = cg.band * GAUGE_W / 100, hw = 10 * GAUGE_W / 100;
        canvas_fill(GAUGE_X + c - hw, GAUGE_Y, hw * 2, 6, 13);
        canvas_fill(GAUGE_X + c - 1, GAUGE_Y, 2, 6, 12);
        text_draw(12, 11, "HEAT");
        int px = clampi(cg.t * GAUGE_W / BREW_FRAMES, 0, GAUGE_W);
        canvas_fill(GAUGE_X, GAUGE_Y + 6, px, 1, INK_BLUE);
    } else {
        text_draw(12, 11, "BOTTLE!");
    }
}

static void brew_liquid_colour(void)
{
    int h = cg.heat / 256, d = h - cg.band;
    u16 main;
    if (d < -10) main = RGB15(6, 12, 28);            /* too cool: dull blue */
    else if (d > 10) main = RGB15(30, 10, 4);        /* too hot: scorching */
    else main = RGB15(6, 26, 16);                    /* just right: bright green */
    if (cg.phase) main = RGB15(8, 28, 20);
    build_fx_palette(CB_FOOD, main, RGB15(24, 31, 28));
}

static void brew_update(void)
{
    cg.t++;
    if (cg.phase == 0) {
        cg.vel += (keys_now & KEY_A) ? 10 : -8;
        cg.vel = clampi(cg.vel, -180, 180);
        cg.heat += cg.vel;
        if (cg.heat < 0) { cg.heat = 0; cg.vel = 0; }
        if (cg.heat > 100 * 256) { cg.heat = 100 * 256; cg.vel = 0; }
        cg.band = brew_band_center(cg.t);
        if (absi(cg.heat / 256 - cg.band) <= 10) cg.inband++;
        brew_gauge_draw();
        brew_liquid_colour();
        if (cg.heat > 60 * 256 && !(cg.t & 7)) cg_burst(96 + (int)rng_range(40), 92, 1, 0);
        if (cg.t >= BREW_FRAMES) {
            cg.heat_pts = brew_heat_points(cg.inband, BREW_FRAMES);
            cg.score += cg.heat_pts;
            cg_label(cg.heat_pts >= 60 ? CSP_LBL_GREAT : cg.heat_pts >= 30 ? CSP_LBL_OK : CSP_LBL_MISS,
                     cg.heat_pts >= 30 ? CB_LABEL : CB_BAD);
            cg.phase = 1;
            cg.bub_t = 0;
            cg.bub_cycles = 0;
            cg.t = 0;
            brew_gauge_draw();
            brew_liquid_colour();
        }
        return;
    }
    if (cg.phase == 1) {                            /* the big bubble */
        if (++cg.bub_t >= BREW_CYCLE) {
            cg.bub_t = 0;
            if (++cg.bub_cycles >= 3) {
                cg.bub_pts = 0;
                cg.phase = 2;
                cg.t = 0;
                cg_label(CSP_LBL_MISS, CB_BAD);
                sfx_play(SFX_MISS);
            }
        }
        if (cg.bub_t == BREW_PEAK + 1) sfx_play(SFX_SPLASH);
        if (key_hit(KEY_A)) {
            cg.bub_pts = brew_bubble_points(cg.bub_t);
            cg.score += cg.bub_pts;
            cg_label(cg.bub_pts == 30 ? CSP_LBL_PERFECT : cg.bub_pts ? CSP_LBL_GOOD : CSP_LBL_MISS,
                     cg.bub_pts ? CB_LABEL : CB_BAD);
            sfx_play(cg.bub_pts == 30 ? SFX_PERFECT : cg.bub_pts ? SFX_CONFIRM : SFX_MISS);
            cg_burst(108, 70, 5, 0);
            cg.phase = 2;
            cg.t = 0;
        }
        return;
    }
    if (cg.t >= 40) cg.phase = 3;                   /* let the label show */
}

static void brew_draw(void)
{
    int lx = 76, ly = 82;
    int bob = soft_sin(cg.t * 6) / 32;
    if (cg.state == CS_PLAY && cg.phase == 0)
        cg_spr_p(CSP_POINTER, 0, GAUGE_X + clampi(cg.heat / 256, 0, 100) * GAUGE_W / 100 - 8, 5, CB_METAL, 0, 0);
    if (cg.state == CS_PLAY && cg.phase == 1) {
        /* the big bubble swells to its peak, then pops */
        if (cg.bub_t <= BREW_PEAK) {
            int s = 64 + cg.bub_t * 192 / BREW_PEAK;        /* 25% .. 100% */
            int aff = oam_affine_scale_rot(s, s, 0);
            spr_push_affine(lx + 16, ly - 18 - cg.bub_t / 4, cg.tile[CSP_BUBBLE], SQ32, CB_BUBBLE, 1, 0, aff, 1);
        } else if (cg.bub_t < BREW_PEAK + 8) {
            cg_spr(CSP_BUBBLE, 1, lx + 16, ly - 28, CB_BUBBLE, 0);
        }
    }
    cg_spr(CSP_LIQUID, 0, lx, ly + bob, CB_FOOD, 0);
}

/* ---------------- minigame: forge ---------------- */

enum { MK_WAIT, MK_HIT, MK_MISS };

static int forge_mark_time(int i) { return FORGE_LEAD + i * cg.beat; }

/* Points for one strike, dt frames off the beat (N marks share 100). */
static int forge_strike_points(int dt, int marks)
{
    dt = absi(dt);
    if (dt <= 3) return 100 / marks;
    if (dt <= 8) return 60 / marks;
    return 0;
}

static void forge_gauge_draw(void)
{
    cg_gauge_window();
    canvas_fill(GAUGE_X - 1, GAUGE_Y - 1, GAUGE_W + 2, 8, INK_DARK);
    canvas_fill(GAUGE_X, GAUGE_Y, GAUGE_W, 6, INK_SHADOW);
    canvas_fill(FORGE_HIT_X - 1, GAUGE_Y - 3, 3, 12, INK_RED);
    text_draw(12, 11, cg.phase ? "QUENCH" : "BEAT");
}

static void forge_update(void)
{
    cg.t++;
    if (cg.hammer_t > 0) cg.hammer_t--;
    if (cg.phase == 0) {
        if (key_hit(KEY_A)) {
            int best = -1, bd = 99;
            for (int i = 0; i < cg.marks; i++) {
                if (cg.mark_state[i] != MK_WAIT) continue;
                int d = absi(cg.t - forge_mark_time(i));
                if (d < bd) { bd = d; best = i; }
            }
            cg.hammer_t = 10;
            if (best >= 0 && bd <= 12) {
                int pts = forge_strike_points(bd, cg.marks);
                cg.mark_state[best] = pts ? MK_HIT : MK_MISS;
                cg.score += pts;
                cg_label(bd <= 3 ? CSP_LBL_PERFECT : pts ? CSP_LBL_GOOD : CSP_LBL_MISS, pts ? CB_LABEL : CB_BAD);
                sfx_play(bd <= 3 ? SFX_METAL : pts ? SFX_HIT : SFX_HIT_LIGHT);
                if (pts) cg_burst(112, 92, bd <= 3 ? 8 : 4, 0);
            } else {
                cg.score -= 5;                      /* a stray swing */
                cg_label(CSP_LBL_MISS, CB_BAD);
                sfx_play(SFX_HIT_LIGHT);
            }
        }
        int open = 0;
        for (int i = 0; i < cg.marks; i++) {
            if (cg.mark_state[i] == MK_WAIT && cg.t > forge_mark_time(i) + 12) {
                cg.mark_state[i] = MK_MISS;
                cg_label(CSP_LBL_MISS, CB_BAD);
            }
            open += cg.mark_state[i] == MK_WAIT;
        }
        if (!open && cg.t > forge_mark_time(cg.marks - 1) + 20) {
            cg.phase = 1;
            cg.quench_t = 0;
            forge_gauge_draw();
            sfx_play(SFX_SPLASH);
        }
        return;
    }
    if (cg.phase == 1) {                            /* the quench: glowing iron cools to steel */
        cg.quench_t++;
        int k = clampi(cg.quench_t * 31 / 60, 0, 31);
        u16 hot = RGB15(31 - k * 20 / 31, 14 - k * 2 / 31, 2 + k * 14 / 31);
        build_fx_palette(CB_FOOD, hot, RGB15(31 - k / 3, 30 - k / 4, 12 + k / 3));
        if (!(cg.quench_t & 3)) cg_burst(104 + (int)rng_range(24), 84, 1, 1);
        if (cg.quench_t >= 60) cg.phase = 2;
    }
}

static void forge_draw(void)
{
    if (cg.state == CS_PLAY && cg.phase == 0) {
        for (int i = 0; i < cg.marks; i++) {
            if (cg.mark_state[i] != MK_WAIT) continue;
            int x = FORGE_HIT_X + (forge_mark_time(i) - cg.t) * 2;
            if (x < FORGE_HIT_X - 12 || x > 216) continue;
            cg_spr_p(CSP_MARK, 0, x - 8, GAUGE_Y - 5, CB_SPARK, 0, 0);
        }
    }
    /* the hammer: raised, mid, strike */
    int f = cg.hammer_t > 7 ? 1 : cg.hammer_t > 3 ? 2 : 0;
    cg_spr(CSP_HAMMER, f, 104, 68, CB_METAL, 0);
    int shape = RECIPES[cg.recipe].result == ITEM_SPRINKLER || RECIPES[cg.recipe].result == ITEM_HUSH_BELL ? 2 :
                cg.phase ? 1 : 0;
    cg_spr(CSP_INGOT, shape, 94, 90, CB_FOOD, 0);
    if (cg.phase == 1 && (cg.quench_t & 8))
        cg_spr(CSP_BUBBLE, 1, 196, 88 - cg.quench_t / 4, CB_BUBBLE, 0);
}

/* ---------------- minigame: start, finish, result ---------------- */

static void cg_play(void)
{
    int st = RECIPES[cg.recipe].station;
    cg.state = CS_PLAY;
    cg.t = 0;
    cg.phase = 0;
    cg.score = 0;
    cg.flip_t = 0;
    cg.toss = 0;
    cg.heat = 20 * 256;
    cg.vel = 0;
    cg.inband = 0;
    cg.band = 50;
    cg.hammer_t = 0;
    canvas_clear();
    cg_bottom(st == STATION_COOK ? "A: toss   D-pad circles: stir" : st == STATION_BREW ? "Hold A: heat   A: bottle"
                                                                         : "A: strike on the beat");
    if (st == STATION_COOK) {
        cook_new_toss();
        cook_gauge_draw();
    } else if (st == STATION_BREW) {
        brew_gauge_draw();
    } else {
        static const u8 BEAT[3] = { 44, 38, 32 };
        cg.beat = BEAT[RECIPES[cg.recipe].source];
        cg.marks = clampi(RECIPES[cg.recipe].marks, 4, 6);
        for (int i = 0; i < 6; i++) cg.mark_state[i] = MK_WAIT;
        build_fx_palette(CB_FOOD, RGB15(31, 14, 2), RGB15(31, 30, 12));
        forge_gauge_draw();
    }
    sfx_play(SFX_CONFIRM);
}

static void cg_finish(void)
{
    static const u8 FAIL_LBL[CRAFT_STATIONS] = { CSP_LBL_BURNT, CSP_LBL_FIZZLED, CSP_LBL_CRACKED };
    static const u8 RATE_LBL[3] = { CSP_LBL_OK, CSP_LBL_GREAT, CSP_LBL_PERFECT };
    const Recipe *rc = &RECIPES[cg.recipe];
    char msg[160];
    cg.score = clampi(cg.score, 0, 100);
    cg.rating = rating_of(cg.score);
    cg.made = craft_apply(cg.recipe, cg.batch, cg.rating);
    cg.state = CS_RESULT;
    cg.t = 0;
    if (cg.rating == RATE_FAIL) {
        cg_label(FAIL_LBL[rc->station], CB_BAD);
        sfx_play(SFX_ERROR);
        str_copy(msg, rc->station == STATION_COOK ? "Oh no, it burnt!" : rc->station == STATION_BREW
                      ? "The brew fizzled out." : "The metal cracked.");
        str_put(msg, " You lost one batch of ingredients. (score ");
        str_put_int(msg, cg.score);
        str_put(msg, ")");
    } else {
        cg_label(RATE_LBL[cg.rating], CB_LABEL);
        sfx_play(cg.rating == RATE_PERFECT ? SFX_LEVEL_UP : SFX_ITEM);
        str_copy(msg, RATE_NAMES[cg.rating + 1]);
        str_put(msg, "! (score ");
        str_put_int(msg, cg.score);
        str_put(msg, ") You made ");
        str_put_int(msg, cg.made);
        str_put(msg, " ");
        str_put(msg, ITEMS[rc->result].name);
        str_put(msg, ".");
        if (meal_of(rc->result) >= 0 && cg.rating >= RATE_GREAT)
            str_put(msg, cg.rating == RATE_PERFECT ? " Perfect dishes give the strongest buffs!"
                                                   : " Great dishes give stronger buffs.");
    }
    canvas_clear();
    cg_gauge_window();
    text_draw_center(120, 10, ITEMS[rc->result].name);
    cg_bottom(msg);
    cg.lbl_t = 0x7FFF;                      /* the rating stays up */
}

/* ---------------- the screen: update and draw ---------------- */

static void cg_list_input(void)
{
    int old = cg.cursor, old_tab = cg.tab;
    if (key_rep(KEY_UP) && cg.cursor > 0) cg.cursor--;
    if (key_rep(KEY_DOWN) && cg.cursor < cg.count - 1) cg.cursor++;
    if (cg.station < 0) {
        if (key_hit(KEY_LEFT) || key_hit(KEY_L)) cg.tab = (cg.tab + CRAFT_STATIONS - 1) % CRAFT_STATIONS;
        if (key_hit(KEY_RIGHT) || key_hit(KEY_R)) cg.tab = (cg.tab + 1) % CRAFT_STATIONS;
    }
    if (old_tab != cg.tab) {
        craft.cursor[old_tab] = (u8)old;
        cg.scroll = 0;
        cg_build_list();
    } else {
        craft.cursor[cg.tab] = (u8)cg.cursor;
    }
    if (cg.cursor < cg.scroll) cg.scroll = cg.cursor;
    if (cg.cursor >= cg.scroll + CG_ROWS) cg.scroll = cg.cursor - CG_ROWS + 1;
    if (old != cg.cursor || old_tab != cg.tab) {
        sfx_play(SFX_CURSOR);
        cg.note = 0;
        cg_list_redraw();
    }
    if (key_hit(KEY_B)) {
        sfx_play(SFX_CANCEL);
        cg_close();
        return;
    }
    if (!key_hit(KEY_A)) return;
    int r = cg.list[cg.cursor];
    if (!recipe_known(r)) {
        cg.note = "You haven't learned this recipe yet.";
    } else if (cg.station != RECIPES[r].station) {
        static const char *const WHERE[CRAFT_STATIONS] = {
            "Cook this at a kitchen: a stove, an oven or a campfire.",
            "Brew this at a cauldron, like the one in DUSKMERE's apothecary.",
            "Forge this at an anvil, like the one at the CINDERMOOR forge.",
        };
        cg.note = WHERE[RECIPES[r].station];
    } else if (recipe_batches(r) <= 0) {
        cg.note = "You don't have enough ingredients. The missing ones are in red.";
    } else {
        cg.recipe = r;
        cg.batch = clampi(craft.batch, 1, recipe_batches(r));
        cg.state = CS_BATCH;
        cg.note = 0;
        sfx_play(SFX_CONFIRM);
        cg_list_redraw();
        return;
    }
    sfx_play(SFX_ERROR);
    cg_list_redraw();
}

static void cg_batch_input(void)
{
    int max = recipe_batches(cg.recipe), old = cg.batch;
    if (key_rep(KEY_RIGHT) || key_rep(KEY_UP)) cg.batch = cg.batch >= max ? 1 : cg.batch + 1;
    if (key_rep(KEY_LEFT) || key_rep(KEY_DOWN)) cg.batch = cg.batch <= 1 ? max : cg.batch - 1;
    if (old != cg.batch) {
        sfx_play(SFX_CURSOR);
        cg_list_redraw();
    }
    if (key_hit(KEY_B)) {
        cg.state = CS_LIST;
        sfx_play(SFX_CANCEL);
        cg_list_redraw();
    } else if (key_hit(KEY_A)) {
        craft.batch = (u8)cg.batch;
        sfx_play(SFX_CONFIRM);
        cg_intro();
    }
}

static void craft_update(void)
{
    cg_parts_update();
    if (cg.redraw) {
        cg.redraw = 0;
        if (cg.state == CS_LIST) cg_list_redraw();
    }
    switch (cg.state) {
    case CS_LIST: cg_list_input(); break;
    case CS_BATCH: cg_batch_input(); break;
    case CS_INTRO:
        cg.t++;
        if (key_hit(KEY_A)) {
            cg_play();
        } else if (key_hit(KEY_B)) {           /* nothing is used up */
            sfx_play(SFX_CANCEL);
            cg.state = CS_LIST;
            cg_list_redraw();
        }
        break;
    case CS_PLAY: {
        int st = RECIPES[cg.recipe].station;
        if (st == STATION_COOK) {
            cook_update();
            if (cg.phase == 2) cg_finish();
        } else if (st == STATION_BREW) {
            brew_update();
            if (cg.phase == 3) cg_finish();
        } else {
            forge_update();
            if (cg.phase == 2) cg_finish();
        }
        break;
    }
    case CS_RESULT:
        cg.t++;
        if (cg.t > 20 && (key_hit(KEY_A) || key_hit(KEY_B))) {
            sfx_play(SFX_CONFIRM);
            cg.state = CS_LIST;
            cg.lbl_t = 0;
            cg_list_redraw();
        }
        break;
    }
}

static void craft_draw(void)
{
    if (cg.state != CS_INTRO && cg.state != CS_PLAY && cg.state != CS_RESULT) return;
    cg_parts_draw();
    switch (RECIPES[cg.recipe].station) {
    case STATION_COOK: cook_draw(); break;
    case STATION_BREW: brew_draw(); break;
    default: forge_draw(); break;
    }
}

/* ================================================================ */
/*  Stations in the field, the RECIPE BOOK and the teachers          */
/* ================================================================ */

/* The station a decor kind is, or -1. */
static int station_of_decor(int kind)
{
    switch (kind) {
    case DK_STOVE: case DK_BRICK_OVEN: case DK_CAMPFIRE: case DK_COOKTOP: return STATION_COOK;
    case DK_CAULDRON: return STATION_BREW;
    case DK_ANVIL: return STATION_FORGE;
    default: return -1;
    }
}

/* The station the player faces, or -1. */
static int station_faced(void)
{
    int fx = player.x + DIR_DX[player.facing], fy = player.y + DIR_DY[player.facing];
    const DecorPlace *p = decor_at(fx, fy, 0, 0);
    return p ? station_of_decor(p->kind) : -1;
}

static int station_pending;

static void station_answer(int c)
{
    if (c == 0) craft_open(station_pending);
}

static const char *const STATION_ASK[CRAFT_STATIONS] = {
    "A good hot stove. Cook something?",
    "A bubbling cauldron. Brew something?",
    "An anvil, still warm from the forge. Forge something?",
};

/* Examining decor: is it a crafting station? (called before the decor's
 * examine text; return 1 when handled) */
static int station_examine(int decor_kind)
{
    int st = station_of_decor(decor_kind);
    if (st < 0) return 0;
    station_pending = st;
    if (MAPS[cur_map].flags & MF_DEBUG) {
        /* asset viewer: every recipe and a stock of ingredients to try them */
        for (int r = 0; r < RC_COUNT; r++) {
            recipe_learn(r);
            for (int k = 0; k < 3; k++)
                if (RECIPES[r].station == st && RECIPES[r].in[k].qty && bag[RECIPES[r].in[k].item] < 20)
                    bag[RECIPES[r].in[k].item] = 20;
        }
        dlg_say("(DEBUG: every recipe known, ingredients stocked.)");
    }
    dlg_ask(STATION_ASK[st], YES_NO, 2, station_answer);
    return 1;
}

/* KEY item RECIPE BOOK: opens at the station you face, else as a book. */
static int craft_key_use(int key)
{
    (void)key;
    int from = game_mode == MODE_FIELD ? FROM_FIELD : FROM_BAG;
    cg_open(station_faced(), from);
    return 1;
}

/* ---------------- teachers (world/craft/scripts.c) ---------------- */

/* Teach the next lesson at a station; queues what the teacher says. */
static void craft_lesson(int station)
{
    static const char *const DONE[CRAFT_STATIONS] = {
        "I've taught you every dish I know. The COOKBOOK has a few more, if you can find a copy.",
        "That's all my recipes. The rest are in the BREW NOTES.",
        "You know all I can teach. The FORGE MANUAL covers the fiddly ones.",
    };
    static const char *const VERB[CRAFT_STATIONS] = { "dishes", "brews", "pieces" };
    char msg[MSG_TEXT_MAX];
    int gate = 0, r = lesson_next(station, &gate);
    if (r < 0) {
        dlg_say(DONE[station]);
        return;
    }
    if (craft.made[station] < gate) {
        str_copy(msg, "Not yet! Make ");
        str_put_int(msg, gate - craft.made[station]);
        str_put(msg, " more ");
        str_put(msg, VERB[station]);
        str_put(msg, " first, then come back for your next lesson.");
        dlg_say(msg);
        return;
    }
    recipe_learn(r);
    sfx_play(SFX_LORE);
    str_copy(msg, "Watch closely... Here's how it's done.\fYou learned to make ");
    str_put(msg, ITEMS[RECIPES[r].result].name);
    str_put(msg, "! It's in your RECIPE BOOK.");
    dlg_say(msg);
}

/* First meeting: the RECIPE BOOK and a few ingredients to start with. */
static void craft_welcome(int station)
{
    static const u8 FLAG[CRAFT_STATIONS] = { CF_MET_CHEF, CF_MET_BREWER, CF_MET_SMITH };
    static const u8 GIFT[CRAFT_STATIONS][2][2] = {
        { { ITEM_CROP_GLOWBERRY, 6 }, { ITEM_GLOW_HONEY, 3 } },
        { { ITEM_MINT_LEAF, 3 }, { ITEM_GLOW_HONEY, 3 } },
        { { ITEM_HEARTGLASS_SAND, 3 }, { ITEM_IRON_ORE, 3 } },
    };
    char msg[64];
    craft.flags |= FLAG[station];
    if (bag[ITEM_RECIPE_BOOK] <= 0) {
        bag_add(ITEM_RECIPE_BOOK, 1);
        dlg_say("Every crafter needs one of these. Keep your recipes in it!");
        sfx_play(SFX_ITEM);
        dlg_say("You received the RECIPE BOOK!");
    }
    for (int i = 0; i < 2; i++) {
        bag_add(GIFT[station][i][0], GIFT[station][i][1]);
        str_copy(msg, "You received ");
        str_put_int(msg, GIFT[station][i][1]);
        str_put(msg, " ");
        str_put(msg, ITEMS[GIFT[station][i][0]].name);
        str_put(msg, "!");
        dlg_say(msg);
    }
}

static int craft_met(int station)
{
    static const u8 FLAG[CRAFT_STATIONS] = { CF_MET_CHEF, CF_MET_BREWER, CF_MET_SMITH };
    return (craft.flags & FLAG[station]) != 0;
}
