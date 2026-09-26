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
