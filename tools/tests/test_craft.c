/*
 * Crafting tests (craft.c, world/craft): recipes, ratings, yields, meal
 * buffs, food and books, lessons, the stations and the crafting screen,
 * each minigame driven with keys, and the save round trip.
 */
#include "harness.h"

static void clear_bag(void)
{
    for (int i = 0; i < ITEM_COUNT; i++) bag[i] = 0;
}

static void stock(int r, int batches)
{
    for (int k = 0; k < 3; k++)
        if (RECIPES[r].in[k].qty) bag[RECIPES[r].in[k].item] = RECIPES[r].in[k].qty * batches;
}

static void test_data(void)
{
    int ok = 1, counts[CRAFT_STATIONS] = { 0 };
    for (int r = 0; r < RC_COUNT; r++) {
        const Recipe *rc = &RECIPES[r];
        if (rc->station >= CRAFT_STATIONS || !rc->yield || rc->result >= ITEM_COUNT || !rc->in[0].qty) ok = 0;
        for (int k = 0; k < 3; k++)
            if (rc->in[k].qty && (rc->in[k].item >= ITEM_COUNT || rc->in[k].item == rc->result)) ok = 0;
        counts[rc->station]++;
    }
    CHECK(ok, "every recipe has a station, a result and real ingredients");
    CHECK(RC_COUNT == 32 && counts[0] == 13 && counts[1] == 8 && counts[2] == 11, "32 recipes: 13 dishes, 8 brews, 11 forgings");
    int res_ok = 1;
    for (int a = 0; a < RC_COUNT; a++)
        for (int b = a + 1; b < RC_COUNT; b++)
            if (RECIPES[a].result == RECIPES[b].result) res_ok = 0;
    CHECK(res_ok, "no two recipes make the same thing");
    /* every recipe is learnable: start, a lesson or a book */
    int learn_ok = 1;
    for (int r = 0; r < RC_COUNT; r++) {
        int found = RECIPES[r].source == SRC_START;
        for (int s = 0; s < CRAFT_STATIONS; s++)
            for (int i = 0; i < LESSONS[s].count; i++)
                if (LESSONS[s].recipes[i] == r) found += RECIPES[r].source == SRC_LESSON && RECIPES[r].station == s;
        const u8 *bk[3] = { BOOK_COOK_RC, BOOK_BREW_RC, BOOK_FORGE_RC };
        int bn[3] = { (int)sizeof(BOOK_COOK_RC), (int)sizeof(BOOK_BREW_RC), (int)sizeof(BOOK_FORGE_RC) };
        for (int b = 0; b < 3; b++)
            for (int i = 0; i < bn[b]; i++)
                if (bk[b][i] == r) found += RECIPES[r].source == SRC_BOOK;
        if (found != 1) {
            learn_ok = 0;
            printf("  recipe %s is learnable %d ways\n", ITEMS[RECIPES[r].result].name, found);
        }
    }
    CHECK(learn_ok, "every recipe is learned exactly one way");
    int meals_ok = 1;
    for (int m = 0; m < MEAL_COUNT; m++)
        if (meal_item(m) < 0) meals_ok = 0;
    CHECK(meals_ok && meal_of(ITEM_COOKBOOK) < 0 && meal_of(ITEM_TONIC) < 0, "every MEAL has its food item");
    CHECK(sizeof(CraftState) <= MOD_CRAFT_MAX, "CraftState fits its save blob");
    int sold = (ITEMS[ITEM_COOKBOOK].price > 0) + (ITEMS[ITEM_BREW_NOTES].price > 0) + (ITEMS[ITEM_FORGE_MANUAL].price > 0) == 3;
    CHECK(sold, "the three books are sold");
    int teachers[3] = { 0 };
    for (int i = 0; i < NPC_COUNT; i++) {
        teachers[0] += NPCS[i].script == SCR_CHEF;
        teachers[1] += NPCS[i].script == SCR_BREWER;
        teachers[2] += NPCS[i].script == SCR_SMITH;
    }
    CHECK(teachers[0] == 1 && teachers[1] <= 1 && teachers[2] <= 1, "the chef is placed; at most one brewer and one smith");
}

static void test_rules(void)
{
    fresh_game();
    CHECK(recipe_known(RC_BERRY_TART) && recipe_known(RC_GLOW_TONIC) && recipe_known(RC_LANTERN) &&
          !recipe_known(RC_HONEY_BUN), "a new game knows the four starter recipes");
    CHECK(rating_of(95) == RATE_PERFECT && rating_of(90) == RATE_PERFECT && rating_of(60) == RATE_GREAT &&
          rating_of(25) == RATE_OK && rating_of(24) == RATE_FAIL, "score thresholds: 90 / 60 / 25");
    clear_bag();
    stock(RC_LANTERN, 3);
    CHECK(recipe_batches(RC_LANTERN) == 3, "batches follow the bag");
    int n = craft_apply(RC_LANTERN, 2, RATE_PERFECT);
    CHECK(n == 3 * 2 + 2 && bag[ITEM_LANTERN] == 8 && recipe_batches(RC_LANTERN) == 1, "PERFECT forging: a whole extra batch");
    n = craft_apply(RC_LANTERN, 1, RATE_FAIL);
    CHECK(n == 0 && recipe_batches(RC_LANTERN) == 0, "a fail costs one batch and makes nothing");
    clear_bag();
    stock(RC_GLOW_TONIC, 3);
    n = craft_apply(RC_GLOW_TONIC, 3, RATE_GREAT);
    CHECK(n == 2 * 3 + 2 && bag[ITEM_TONIC] == 8, "GREAT brewing: half a batch more");
    CHECK(craft.made[STATION_BREW] == 3 && craft.made[STATION_FORGE] == 2, "successful batches count per station");

    /* food keeps its quality */
    clear_bag();
    stock(RC_BERRY_TART, 4);
    craft_apply(RC_BERRY_TART, 2, RATE_PERFECT);
    craft_apply(RC_BERRY_TART, 1, RATE_GREAT);
    craft_apply(RC_BERRY_TART, 1, RATE_OK);
    CHECK(bag[ITEM_BERRY_TART] == 4 && craft.fine[MEAL_TART] == 3 && craft.perfect[MEAL_TART] == 2,
          "dishes remember GREAT and PERFECT copies");
    bag[ITEM_BERRY_TART] = 1;
    craft_sync_quality();
    CHECK(craft.fine[MEAL_TART] == 1 && craft.perfect[MEAL_TART] == 1, "quality counts clamp to the bag");
}

static void test_meals(void)
{
    fresh_game();
    give_starter();
    clear_bag();
    CHECK(meal_xp_percent() == 100 && meal_catch_bonus() == 0 && meal_stat_stage(STAT_ATK) == 0,
          "no meal, no bonus");
    bag[ITEM_BERRY_TART] = 2;
    craft.fine[MEAL_TART] = 1;
    craft.perfect[MEAL_TART] = 1;
    CHECK(craft_use_food(ITEM_BERRY_TART, 0) && craft.meal == MEAL_TART + 1 && craft.meal_tier == RATE_PERFECT &&
          craft.meal_bouts == 10 && meal_xp_percent() == 150, "a PERFECT tart: +50% XP for 10 bouts");
    dialog_clear();
    CHECK(craft_use_food(ITEM_BERRY_TART, 0) && craft.meal_tier == RATE_OK && craft.meal_bouts == 5 &&
          meal_xp_percent() == 125 && bag[ITEM_BERRY_TART] == 0, "an ordinary tart: +25% for 5");
    dialog_clear();
    bag[ITEM_CHILI_POT] = 1;
    craft_use_food(ITEM_CHILI_POT, 0);
    dialog_clear();
    CHECK(craft.meal == MEAL_CHILI + 1 && meal_xp_percent() == 100 && meal_stat_stage(STAT_ATK) == 1 &&
          meal_stat_stage(STAT_SPA) == 1 && meal_stat_stage(STAT_DEF) == 0, "one buff at a time: CHILI replaces the tart");
    for (int i = 0; i < 3; i++) meal_bout_finished();
    CHECK(craft.meal == 0 && meal_stat_stage(STAT_ATK) == 0, "the buff wears off after its bouts");
    bag[ITEM_PUMPKIN_PIE] = 1;
    craft.fine[MEAL_PIE] = 1;
    craft_use_food(ITEM_PUMPKIN_PIE, 0);
    dialog_clear();
    CHECK(meal_catch_bonus() == 4 && meal_lure_active() == 0, "a GREAT pie adds to lantern finesse");
    bag[ITEM_MOONCAKE] = 1;
    craft_use_food(ITEM_MOONCAKE, 0);
    dialog_clear();
    CHECK(meal_lure_active() == 1 && meal_catch_bonus() == 0, "MOONCAKE lures rare kin");
    bag[ITEM_HONEY_BUN] = 1;
    craft_use_food(ITEM_HONEY_BUN, 0);
    dialog_clear();
    party[0].hp = 1;
    meal_bout_finished();
    CHECK(party[0].hp > 1, "HONEY BUN heals a little after each bout");

    /* drinks, salad, candy */
    party[0].hp = 1;
    bag[ITEM_BERRY_JUICE] = 1;
    CHECK(craft_use_food(ITEM_BERRY_JUICE, 0) && party[0].hp == clampi(41, 0, party[0].max_hp) &&
          bag[ITEM_BERRY_JUICE] == 0, "BERRY JUICE restores 40 HP");
    dialog_clear();
    bag[ITEM_APPLE_PRESS] = 1;
    party[0].hp = party[0].max_hp;
    CHECK(!craft_use_food(ITEM_APPLE_PRESS, 0) && bag[ITEM_APPLE_PRESS] == 1, "a drink on a healthy kin isn't used up");
    dialog_clear();
    party[0].hp = 1;
    party[0].pp[0] = 0;
    bag[ITEM_PEACH_NECTAR] = 1;
    CHECK(craft_use_food(ITEM_PEACH_NECTAR, 0) && party[0].hp == party[0].max_hp && party[0].pp[0] > 0,
          "PEACH NECTAR restores everything");
    dialog_clear();
    party[0].hp = 1;
    bag[ITEM_SUN_SALAD] = 1;
    CHECK(craft_use_food(ITEM_SUN_SALAD, 0) && party[0].hp > party[0].max_hp / 2, "SUN SALAD heals the team by half");
    dialog_clear();
    int lv = party[0].level;
    bag[ITEM_KERNEL_CANDY] = 1;
    CHECK(craft_use_food(ITEM_KERNEL_CANDY, 0) && party[0].level == lv + 1, "KERNEL CANDY grows a level");
    dialog_clear();
    evo_count = 0;

    /* books */
    bag[ITEM_COOKBOOK] = 1;
    CHECK(!recipe_known(RC_PUMPKIN_PIE) && craft_use_food(ITEM_COOKBOOK, 0) && recipe_known(RC_PUMPKIN_PIE) &&
          recipe_known(RC_PEACH_NECTAR) && recipe_known(RC_TRUFFLE_RICE) && bag[ITEM_COOKBOOK] == 0,
          "the COOKBOOK teaches its three dishes and is used up");
    dialog_clear();
    bag[ITEM_COOKBOOK] = 1;
    CHECK(!craft_use_food(ITEM_COOKBOOK, 0) && bag[ITEM_COOKBOOK] == 1, "a book you know is kept");
    dialog_clear();
}

static void test_lessons(void)
{
    fresh_game();
    int gate = -1;
    CHECK(lesson_next(STATION_COOK, &gate) == RC_HONEY_BUN && gate == 0, "the chef's first lesson is free");
    craft_lesson(STATION_COOK);
    dialog_clear();
    CHECK(recipe_known(RC_HONEY_BUN) && lesson_next(STATION_COOK, &gate) == RC_VEGGIE_STEW && gate == 1,
          "lessons come in order");
    craft_lesson(STATION_COOK);
    dialog_clear();
    CHECK(!recipe_known(RC_VEGGIE_STEW), "the next lesson waits until you've cooked");
    craft.made[STATION_COOK] = 99;
    for (int i = 0; i < 10; i++) {
        craft_lesson(STATION_COOK);
        dialog_clear();
    }
    int all = 1;
    for (int i = 0; i < LESSONS[STATION_COOK].count; i++) all &= recipe_known(LESSONS[STATION_COOK].recipes[i]);
    CHECK(all && lesson_next(STATION_COOK, 0) < 0 && !recipe_known(RC_PUMPKIN_PIE), "the chef teaches all 8, not the book's");
}

/* Put the player in the bakery facing the stove, with a kin. */
static void at_stove(void)
{
    fresh_game();
    give_starter();
    field_enter_map(MAP_BAKERY, 2, 3, DIR_UP);
    settle();
    player.x = 2;
    player.y = 3;
    player.facing = DIR_UP;
}

static void test_screens(void)
{
    at_stove();
    CHECK(station_faced() == STATION_COOK, "the bakery stove is a kitchen");
    CHECK(station_of_decor(DK_CAULDRON) == STATION_BREW && station_of_decor(DK_ANVIL) == STATION_FORGE &&
          station_of_decor(DK_COOKTOP) == STATION_COOK && station_of_decor(DK_BED) < 0, "decor kinds map to stations");
    tap(KEY_A);
    CHECK(dialog_active(), "A on the stove asks to cook");
    run_dialog(200);
    CHECK(game_mode == MODE_EXT && ext.update == craft_update && cg.state == CS_LIST && cg.station == STATION_COOK,
          "YES opens the kitchen screen");
    /* not enough ingredients */
    clear_bag();
    tap(KEY_A);
    CHECK(cg.state == CS_LIST && cg.note, "no ingredients: stays on the list with a note");
    /* a potion recipe is not cooked here */
    tap(KEY_B);
    CHECK(game_mode == MODE_FIELD, "B leaves the screen");
    bag[ITEM_RECIPE_BOOK] = 1;
    item_use_field(ITEM_RECIPE_BOOK, 0);
    CHECK(game_mode == MODE_EXT && cg.station == STATION_COOK, "the RECIPE BOOK opens the station you face");
    tap(KEY_B);
    player.facing = DIR_DOWN;
    item_use_field(ITEM_RECIPE_BOOK, 0);
    CHECK(game_mode == MODE_EXT && cg.station < 0, "elsewhere it opens as a book with tabs");
    tap(KEY_RIGHT);
    CHECK(cg.tab == STATION_BREW, "RIGHT turns to the next station");
    cg.cursor = 0;
    stock(RC_GLOW_TONIC, 2);
    tap(KEY_A);
    CHECK(cg.state == CS_LIST && cg.note, "the book alone can't brew");
    tap(KEY_B);
    CHECK(game_mode == MODE_FIELD, "and closes back to the field");
}

/* Opens the kitchen on `r` with `batches` of stock, through the intro. */
static void start_game(int station, int r, int batches)
{
    at_stove();
    clear_bag();
    stock(r, batches);
    craft_open(station);
    for (int i = 0; i < cg.count; i++)
        if (cg.list[i] == r) cg.cursor = i;
    recipe_learn(r);
    tap(KEY_A);          /* choose */
    tap(KEY_A);          /* one batch */
    step(0);
}

static void test_minigames(void)
{
    /* B in the intro costs nothing */
    start_game(STATION_COOK, RC_BERRY_TART, 1);
    CHECK(cg.state == CS_INTRO, "choosing a recipe and a batch shows the how-to");
    tap(KEY_B);
    CHECK(cg.state == CS_LIST && recipe_batches(RC_BERRY_TART) == 1, "B in the intro keeps the ingredients");

    /* the kitchen, played perfectly by watching the needle */
    tap(KEY_A);
    tap(KEY_A);
    tap(KEY_A);
    CHECK(cg.state == CS_PLAY && cg.phase == 0, "A starts the kitchen");
    for (int toss = 0; toss < 3; toss++) {
        for (int f = 0; f < 400 && absi(cg.needle / 16 - cg.zone) > 1; f++) step(0);
        step(KEY_A);
        step(0);
        for (int f = 0; f < 40 && cg.flip_t; f++) step(0);
    }
    CHECK(cg.phase == 1 && cg.score == 75, "three perfect tosses score 75");
    static const u16 RING[8] = { KEY_UP, KEY_UP | KEY_RIGHT, KEY_RIGHT, KEY_DOWN | KEY_RIGHT,
                                 KEY_DOWN, KEY_DOWN | KEY_LEFT, KEY_LEFT, KEY_UP | KEY_LEFT };
    for (int f = 0; f < 200 && cg.state == CS_PLAY; f++) step(RING[(f / 3) % 8]);
    CHECK(cg.state == CS_RESULT && cg.rating == RATE_PERFECT && bag[ITEM_BERRY_TART] == 1 &&
          craft.perfect[MEAL_TART] == 1, "stirring in circles finishes a PERFECT tart");
    tap(KEY_A);
    for (int i = 0; i < 30; i++) step(0);
    tap(KEY_A);
    CHECK(cg.state == CS_LIST, "A goes back to the list");

    /* the kitchen, ignored: it burns and costs one batch */
    start_game(STATION_COOK, RC_BERRY_JUICE, 2);
    tap(KEY_A);
    for (int f = 0; f < 2000 && cg.state == CS_PLAY; f++) step(0);
    CHECK(cg.state == CS_RESULT && cg.rating == RATE_FAIL && recipe_batches(RC_BERRY_JUICE) == 1 &&
          bag[ITEM_BERRY_JUICE] == 0, "an idle kitchen burns one batch");

    /* the cauldron: follow the band, bottle at the peak */
    start_game(STATION_BREW, RC_GLOW_TONIC, 1);
    tap(KEY_A);
    for (int f = 0; f < 400 && cg.state == CS_PLAY && cg.phase == 0; f++)
        step((cg.heat + cg.vel * 12) / 256 < brew_band_center(cg.t + 1) ? KEY_A : 0);
    CHECK(cg.phase == 1 && cg.heat_pts >= 60, "holding A into the band scores the heat");
    step(0);
    for (int f = 0; f < 200 && cg.bub_t != BREW_PEAK; f++) step(0);
    step(KEY_A);
    for (int f = 0; f < 100 && cg.state == CS_PLAY; f++) step(0);
    CHECK(cg.state == CS_RESULT && cg.rating >= RATE_GREAT && bag[ITEM_TONIC] >= 3, "bottled at the peak: a good brew");

    /* the forge: strike every mark on the beat */
    start_game(STATION_FORGE, RC_LANTERN, 1);
    tap(KEY_A);
    CHECK(cg.state == CS_PLAY && cg.marks == 4, "the LANTERN is four marks");
    for (int i = 0; i < cg.marks; i++) {
        while (cg.t + 1 < forge_mark_time(i)) step(0);
        step(KEY_A);
    }
    for (int f = 0; f < 200 && cg.state == CS_PLAY; f++) step(0);
    CHECK(cg.state == CS_RESULT && cg.rating == RATE_PERFECT && bag[ITEM_LANTERN] == 4,
          "four strikes on the beat: PERFECT, 3 + 1 LANTERNS");
    tap(KEY_A);
    for (int i = 0; i < 30; i++) step(0);
    tap(KEY_A);
    tap(KEY_B);
    tap(KEY_B);
    for (int i = 0; i < 5; i++) step(0);
    CHECK(game_mode == MODE_FIELD, "and back to the field");
}

static void test_teacher(void)
{
    fresh_game();
    give_starter();
    int chef = -1;
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].script == SCR_CHEF) chef = i;
    field_enter_map(MAP_BAKERY, NPCS[chef].x, NPCS[chef].y + 1, DIR_UP);
    settle();
    script_run(chef);
    run_dialog(2000);
    CHECK(bag[ITEM_RECIPE_BOOK] == 1 && bag[ITEM_CROP_GLOWBERRY] == 6 && craft_met(STATION_COOK),
          "the chef hands over the RECIPE BOOK and berries");
    script_run(chef);
    for (int f = 0; f < 200 && !choice.active; f++) step(0);
    CHECK(choice.active && choice.count == 5, "then offers LESSON / COOK / BUY / CHAT / BYE");
    step(KEY_A);
    run_dialog(1000);
    CHECK(recipe_known(RC_HONEY_BUN), "LESSON teaches HONEY BUN");
    int before = lore_known_count();
    script_run(chef);
    for (int f = 0; f < 200 && !choice.active; f++) step(0);
    tap(KEY_DOWN);
    tap(KEY_DOWN);
    tap(KEY_DOWN);
    tap(KEY_A);
    run_dialog(1000);
    CHECK(lore_known_count() == before + 1 && lore_is_known(LORE_CRAFT_MAILLARD), "CHAT reveals crafting lore");
    script_run(chef);
    for (int f = 0; f < 200 && !choice.active; f++) step(0);
    tap(KEY_DOWN);
    tap(KEY_DOWN);
    tap(KEY_A);
    for (int f = 0; f < 30 && game_mode != MODE_SHOP; f++) step(0);
    CHECK(game_mode == MODE_SHOP && shop_stock == CHEF_STOCK, "BUY opens the chef's stock");
}

static void test_save(void)
{
    fresh_game();
    give_starter();
    recipe_learn(RC_STAR_LANTERN);
    craft.meal = MEAL_STEW + 1;
    craft.meal_bouts = 4;
    craft.meal_tier = RATE_GREAT;
    craft.made[STATION_FORGE] = 7;
    bag[ITEM_VEGGIE_STEW] = 3;
    craft.fine[MEAL_STEW] = 2;
    craft.perfect[MEAL_STEW] = 1;
    CraftState before = craft;
    CHECK(save_write(), "save written");
    craft_reset();
    CHECK(save_load(), "save loaded");
    CHECK(memcmp(&before, &craft, sizeof(craft)) == 0, "crafting state round-trips");
    /* junk gets clamped */
    memset(&craft, 0xFF, sizeof(craft));
    craft_validate();
    CHECK(craft.meal == 0 && craft.batch == 10 && craft.fine[MEAL_STEW] <= bag[ITEM_VEGGIE_STEW] &&
          craft.perfect[0] <= craft.fine[0] && recipe_known(RC_LANTERN) &&
          !((craft.recipes[RC_COUNT >> 3] >> (RC_COUNT & 7)) & 1), "craft_validate clamps junk");
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    rng_seed(99);
    test_data();
    test_rules();
    test_meals();
    test_lessons();
    test_screens();
    test_minigames();
    test_teacher();
    test_save();
    if (failures) {
        printf("%d craft check(s) FAILED\n", failures);
        return 1;
    }
    printf("all craft checks passed\n");
    return 0;
}
