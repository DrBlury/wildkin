/*
 * Farming and time (docs/EXPANSION.md 7.1, 7.2): the clock and tint,
 * sleeping, the plot rules (till, water, plant, grow, harvest, regrow,
 * trees, fertiliser, sprinklers), the deed from REEVE, the gate, the
 * shipping bin, processors, workers, berry patches, the tool ring, the
 * work board screen and the save round trip.
 */
#include "harness.h"

static void to_farm(int x, int y, int facing)
{
    field_enter_map(MAP_WILLOW_ACRE, x, y, facing);
    dialog_clear();
    game_mode = MODE_FIELD;
}

static int find_plot(int orchard)
{
    for (int i = 0; i < plot_count; i++)
        if (plot_orchard[i] == orchard && !farm.plots[i].crop && !(farm.plots[i].flags & PF_SPRINKLER)) return i;
    return -1;
}

/* Stand south of a plot, facing it, with a tool in hand, and press A. */
static void use_on(int pi, int tool_item)
{
    to_farm(plot_x[pi], plot_y[pi] + 1, DIR_UP);
    tool_select_item(tool_item);
    fx_freeze = 0;
    field_try_interact();
    dialog_clear();
}

static void new_day(void)
{
    gtime.weather = WEATHER_CLEAR;
    time_new_day();
    gtime.weather = WEATHER_CLEAR;
    dialog_clear();
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    fresh_game();
    give_starter();
    flag_set(FLAG_STORM_CALMED);   /* no storm tint in the way */

    /* ---- geometry and state ---- */
    farm_geom_init();
    CHECK(plot_count == 152, "WILLOW ACRE has 144 field plots and 8 orchard mounds");
    CHECK(sizeof(FarmState) <= MOD_FARM_MAX && sizeof(TimeState) <= MOD_TIME_MAX, "farm and time state fit their save blobs");
    int berries_ok = 1;
    for (int i = 0; i < FARM_BERRIES; i++) berries_ok &= berry_ripe(i);
    CHECK(berries_ok && !farm.owned && farm.can_water == CAN_MAX, "a new game: every berry patch ripe, farm not owned, can full");

    /* ---- time ---- */
    char buf[24];
    gtime.day = 3;
    gtime.minute = 14 * 60 + 5;
    time_text(buf);
    CHECK(str_eq(buf, "DAY 3  14:05"), "time_text reads DAY 3  14:05");
    to_farm(19, 5, DIR_DOWN);
    u16 day_col = TILESETS[TS_FARM].palettes[0][3];
    gtime.minute = 12 * 60;
    field_load_palettes();
    CHECK(bg_palette[3] == day_col, "noon outdoors: the palette is untinted");
    gtime.minute = 23 * 60;
    field_load_palettes();
    int night_blue = (bg_palette[3] & 31) < (day_col & 31);
    CHECK(night_blue && time_is_night(), "at 23:00 outdoor palettes darken");
    field_enter_map(MAP_FARMHOUSE, 5, 7, DIR_UP);
    CHECK(field_tint(day_col) == day_col, "indoors (MF_NIGHTLESS) there is no tint");
    int d0 = gtime.day;
    time_sleep();
    CHECK(gtime.day == d0 + 1 && gtime.minute == 6 * 60, "sleeping skips to 06:00 the next day");
    for (int f = 0; f < 40; f++) step(0);
    gtime.minute = 5 * 60 + 59;
    gtime.frames = 59;
    d0 = gtime.day;
    game_mode = MODE_FIELD;
    dialog_clear();
    time_tick();
    CHECK(gtime.day == d0 + 1, "the day rolls over by itself at 06:00");

    /* ---- the deed ---- */
    to_farm(19, 11, DIR_DOWN);
    CHECK(cell_attr(19, 12) & A_SOLID, "the farm gate is shut before you own the farm");
    money = 20000;
    int reeve = -1;
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].script == SCR_REEVE) reeve = i;
    CHECK(reeve >= 0 && NPCS[reeve].map == MAP_WILLOW_ACRE, "REEVE stands at WILLOW ACRE");
    /* the berry quest: ask, pick, deliver */
    reeve_discount();
    dialog_clear();
    CHECK(quest_get(QUEST_REEVE_BERRIES) == 1, "REEVE asks for 3 GLOWBERRY");
    int picked = farm_berry_interact(50) && bag[ITEM_CROP_GLOWBERRY] >= 2;
    dialog_clear();
    farm_berry_interact(51);
    dialog_clear();
    CHECK(picked && bag[ITEM_CROP_GLOWBERRY] >= 4 && !berry_ripe(50), "wild glowberry bushes can be picked");
    farm_berry_interact(50);
    dialog_clear();
    scr_reeve(reeve);
    CHECK(quest_done(QUEST_REEVE_BERRIES) && farm_deed_price() == FARM_DEED_PRICE_QUEST,
          "delivering the berries brings the deed down to 10,000c");
    dialog_clear();
    reeve_buy();
    dialog_clear();
    CHECK(farm.owned && money == 10000 && bag[ITEM_HOE] && bag[ITEM_WATERING_CAN] && bag[ITEM_FARM_DEED] &&
          bag[ITEM_SEED_RADISH] == 5, "buying the deed gives the farm, HOE, CAN, deed and seeds");
    CHECK(!(cell_attr(19, 12) & A_SOLID), "the gate opens once you own the farm");
    new_day();
    new_day();
    new_day();
    CHECK(berry_ripe(50), "berry bushes are ripe again after 3 days");

    /* ---- plots ---- */
    int pi = find_plot(0);
    use_on(pi, ITEM_SEED_RADISH);
    CHECK(!farm.plots[pi].crop, "seeds need tilled soil");
    use_on(pi, ITEM_HOE);
    CHECK(farm.plots[pi].flags & PF_TILLED, "the HOE tills soil");
    use_on(pi, ITEM_SEED_RADISH);
    CHECK(farm.plots[pi].crop == CROP_RADISH + 1 && bag[ITEM_SEED_RADISH] == 4, "a seed plants a crop");
    new_day();
    CHECK(farm.plots[pi].growth == 0, "a dry crop does not grow");
    use_on(pi, ITEM_WATERING_CAN);
    CHECK((farm.plots[pi].flags & PF_WET) && farm.can_water == CAN_MAX - 1, "the CAN waters a plot and uses one fill");
    new_day();
    CHECK(farm.plots[pi].growth == GROW_PER_DAY && !(farm.plots[pi].flags & PF_WET), "a watered crop grows and the soil dries");
    use_on(pi, ITEM_WATERING_CAN);
    new_day();
    CHECK(plot_ripe(&farm.plots[pi]), "radishes are ripe after 2 watered days");
    int had = bag[ITEM_CROP_RADISH];
    use_on(pi, ITEM_HOE);
    CHECK(bag[ITEM_CROP_RADISH] > had && !farm.plots[pi].crop && (farm.plots[pi].flags & PF_TILLED),
          "A picks a ripe crop; one-harvest crops leave tilled soil");

    /* regrowing crop + fertiliser */
    bag[ITEM_SEED_GLOWBERRY] = 1;
    bag[ITEM_FERTILIZER] = 1;
    use_on(pi, ITEM_SEED_GLOWBERRY);
    use_on(pi, ITEM_FERTILIZER);
    CHECK(farm.plots[pi].flags & PF_FERT, "fertiliser goes on tilled soil");
    for (int d = 0; d < 3; d++) {
        plot_water(&farm.plots[pi]);
        new_day();
    }
    CHECK(plot_ripe(&farm.plots[pi]), "fertilised glowberries ripen in 3 days");
    use_on(pi, ITEM_HOE);
    CHECK(farm.plots[pi].crop == CROP_GLOWBERRY + 1 && !plot_ripe(&farm.plots[pi]), "glowberries regrow after a harvest");

    /* fruit trees grow without water and become solid */
    int oi = find_plot(1);
    bag[ITEM_SAPLING_APPLE] = 1;
    use_on(oi, ITEM_SAPLING_APPLE);
    CHECK(farm.plots[oi].crop == CROP_APPLE + 1, "saplings go straight into orchard mounds");
    for (int d = 0; d < 15; d++) new_day();
    to_farm(plot_x[oi], plot_y[oi] + 1, DIR_UP);
    CHECK(plot_ripe(&farm.plots[oi]) && (cell_attr(plot_x[oi], plot_y[oi]) & A_SOLID), "an apple tree grows up, fruits and is solid");
    had = bag[ITEM_CROP_APPLE];
    use_on(oi, ITEM_HOE);
    CHECK(bag[ITEM_CROP_APPLE] > had && farm.plots[oi].crop, "apples are picked and the tree stays");

    /* sprinkler */
    int si = plot_at_xy(10, 15), ni = plot_at_xy(11, 15);
    bag[ITEM_SPRINKLER] = 1;
    use_on(ni, ITEM_HOE);
    use_on(si, ITEM_SPRINKLER);
    new_day();
    CHECK((farm.plots[si].flags & PF_SPRINKLER) && (farm.plots[ni].flags & PF_WET), "a sprinkler waters its neighbours each morning");

    /* ---- tool ring ---- */
    to_farm(19, 18, DIR_DOWN);
    farm.tool = 0;
    tool_cycle(1);
    CHECK(FARM_TOOLS[tool_current()] == TOOL_CAN, "R moves the ring from the HOE to the CAN");
    tool_cycle(-1);
    CHECK(FARM_TOOLS[tool_current()] == TOOL_HOE, "L moves it back");

    /* ---- shipping bin ---- */
    bag[ITEM_CROP_PUMPKIN] = 2;
    int before = money;
    bin_answer(0);
    dialog_clear();
    CHECK(!bag[ITEM_CROP_PUMPKIN] && farm.bin_value >= 2u * CROPS[CROP_PUMPKIN].value && money == before,
          "the bin takes produce and pays nothing yet");
    u32 due = farm.bin_value;
    new_day();
    CHECK(money == before + (int)due && !farm.bin_value, "the bin pays out next morning");
    bag[ITEM_CROP_CARROT] = 3;
    bin_answer(1);
    dialog_clear();
    CHECK(bag[ITEM_CROP_CARROT] == 1, "KEEP ONE EACH keeps one of each");

    /* ---- processors ---- */
    bag[ITEM_CROP_TIDEBERRY] = 5;
    farm_proc_open(PROC_JAR);
    dialog_clear();
    proc_answer(0);
    dialog_clear();
    CHECK(farm.procs[PROC_JAR].recipe && bag[ITEM_CROP_TIDEBERRY] == 1, "the jar takes berries in pairs");
    new_day();
    had = bag[ITEM_FRUIT_JAM];
    farm_proc_open(PROC_JAR);
    dialog_clear();
    CHECK(bag[ITEM_FRUIT_JAM] == had + 2 && !farm.procs[PROC_JAR].recipe, "next morning the jam is ready");

    /* ---- chest ---- */
    bag[ITEM_CROP_CORN] = 7;
    chest_answer(0);
    dialog_clear();
    CHECK(!bag[ITEM_CROP_CORN] && chest_total() >= 7, "the chest stores produce");
    chest_answer(1);
    dialog_clear();
    CHECK(bag[ITEM_CROP_CORN] == 7 && !chest_total(), "and gives it back");

    /* ---- workers ---- */
    Monster tide = monster_make(SP_AQUAPO, 10);
    storage_add(&tide);
    farm.workers[0].job = JOB_WATER;
    farm.workers[0].species = storage[0].species;
    farm.workers[0].pot = storage[0].pot;
    int wp = find_plot(0);
    farm.plots[wp].flags = PF_TILLED;
    farm.plots[wp].crop = CROP_CARROT + 1;
    new_day();
    int bond0 = storage[0].bond;
    CHECK(farm.plots[wp].flags & PF_WET, "a WATER worker waters dry crops each morning");
    new_day();
    CHECK(storage[0].bond > bond0 && farm.workers[0].days >= 2, "workers gain bond as they work");
    CHECK(job_fit(JOB_WATER, SP_AQUAPO) == 2 && job_best(SP_AQUAPO) == JOB_WATER, "TIDE kin suit the WATER job");
    to_farm(19, 18, DIR_DOWN);
    CHECK(farm_kin[0].shown, "the worker walks on the farm");
    storage_take(0);
    new_day();
    CHECK(!farm.workers[0].job, "a worker that left the Shelf gives up its job");

    /* ---- the work board screen ---- */
    storage_add(&tide);
    field_enter_map(MAP_FARMHOUSE, 3, 2, DIR_UP);
    dialog_clear();
    game_mode = MODE_FIELD;
    field_try_interact();
    CHECK(game_mode == MODE_EXT, "the WORK BOARD opens its screen");
    tap(KEY_A);
    tap(KEY_DOWN);
    tap(KEY_A);
    CHECK(farm.workers[0].job == JOB_WATER && farm.workers[0].species == SP_AQUAPO, "picking a Shelf kin gives it its best job");
    tap(KEY_RIGHT);
    CHECK(farm.workers[0].job == JOB_TEND, "left/right change the job");
    tap(KEY_B);
    CHECK(game_mode == MODE_FIELD, "B closes the board");

    /* ---- save round trip ---- */
    farm.plots[5].crop = CROP_CORN + 1;
    farm.plots[5].growth = 7;
    farm.bin_value = 123;
    gtime.day = 42;
    static u8 sram[32768];
    memset(sram, 0xFF, sizeof(sram));
    int wrote = save_write_to(sram);
    FarmState keep = farm;
    farm_reset();
    time_reset();
    int loaded = save_load_from(sram);
    CHECK(wrote && loaded && !memcmp(&keep, &farm, sizeof(farm)) && gtime.day == 42, "farm and time survive a save");
    farm.version = 99;
    farm_validate();
    CHECK(!farm.owned && farm.version == FARM_VERSION, "a farm blob of another version is reset");

    if (failures) {
        printf("%d farm check(s) FAILED\n", failures);
        return 1;
    }
    printf("all farm checks passed\n");
    return 0;
}
