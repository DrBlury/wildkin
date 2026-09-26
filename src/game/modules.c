/*
 * Reset / validate every system module at once (new game, loading a save).
 */

static void modules_reset(void)
{
    time_reset();
    farm_reset();
    craft_reset();
    fusion_reset();
    travel_reset();
    quest_reset();
}

static void modules_validate(void)
{
    time_validate();
    farm_validate();
    craft_validate();
    fusion_validate();
    travel_validate();
    quest_validate();
}

/* KEY item params (items/key.inc) and who handles them. */
enum { KEY_BIKE, KEY_WATERING_CAN, KEY_HOE, KEY_FARM_DEED, KEY_FERRY_PASS, KEY_TOWN_MAP,
       KEY_CREST_CASE, KEY_RECIPE_BOOK, KEY_ENERGY_FLASK };

static int key_item_use(int key)
{
    switch (key) {
    case KEY_WATERING_CAN: case KEY_HOE: case KEY_FARM_DEED: return farm_key_use(key);
    case KEY_RECIPE_BOOK: return craft_key_use(key);
    case KEY_ENERGY_FLASK: return fusion_key_use(key);
    case KEY_CREST_CASE: crest_case_open(); return 1;   /* menu.c */
    default: return travel_key_use(key);
    }
}
