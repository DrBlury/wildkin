/*
 * Writes a mid-game save file for screenshots and playtesting:
 *
 *   cc -std=c11 -o build/make_demo_save tools/make_demo_save.c
 *   build/make_demo_save OUT.sav [MAP X Y [calm] [low]]
 *
 * The save has a team of five, a stocked bag, a good part of the Lorebook,
 * the TWIN CRYSTAL and the RING SASH, and puts the player at MAP (index
 * into maps.h, default Whisper Meadow) X, Y. With "calm" the storm is
 * already over (clear skies, DRAKORA answered); with "low" the team is
 * around level 6, for even early bouts; with "beaten" every warden on MAP
 * is already beaten (to replay a Hall's puzzle without bouts); "night"
 * sets the clock to 22:00, "rain" makes today rainy.
 */
#define main gba_main
#include "../src/main.c"
#undef main

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* "farm": WILLOW ACRE owned in early summer, a built field (every stage,
 * watered and dry soil, tall corn and sunflowers, ripe rows to pick), two
 * kin at work, the tools and a few seed packets. The row the farm clip
 * works on (y 17, x 23-26) is left untouched. */
static void demo_plot(int x, int y, int crop, int growth, int flags)
{
    int pi = plot_at_xy(x, y);
    if (pi < 0) return;
    farm.plots[pi].crop = (u8)crop;
    farm.plots[pi].growth = (u8)growth;
    farm.plots[pi].flags = (u8)flags;
}

static void demo_farm(void)
{
    farm.owned = 1;
    farm.can_water = CAN_MAX;
    gtime.day = 12;            /* SUMMER 2 */
    gtime.minute = 9 * 60;
    bag[ITEM_FARM_DEED] = bag[ITEM_HOE] = bag[ITEM_WATERING_CAN] = 1;
    bag[ITEM_SEED_MELON] = 6;
    bag[ITEM_SEED_CORN] = 4;
    static const u8 RIPE[] = { CROP_TOMATO, CROP_CORN, CROP_SUNFLOWER, CROP_MELON, CROP_CHILI,
                               CROP_TIDEBERRY, CROP_EMBERBERRY, CROP_CORN };
    for (int x = 27; x <= 34; x++) {
        int c = RIPE[x - 27];
        demo_plot(x, 17, c + 1, crop_target(c), PF_TILLED);
    }
    for (int y = 14; y <= 16; y++)
        for (int x = 23; x <= 34; x++) {
            int c = (x < 27) ? CROP_MELON : (x < 31) ? CROP_CORN : CROP_SUNFLOWER;
            int stage = (x + y) % 5;       /* seeded .. ripe across the bed */
            int wet = x < 29 ? PF_WET : 0;
            demo_plot(x, y, c + 1, crop_target(c) * stage / 4, PF_TILLED | wet);
        }
    for (int y = 20; y <= 23; y++)
        for (int x = 5; x <= 16; x++) {
            int c = (y < 22) ? CROP_TOMATO : CROP_PUMPKIN;
            demo_plot(x, y, (x % 4 == 0) ? 0 : c + 1, crop_target(c) * ((x + y) % 5) / 4,
                         PF_TILLED | ((x + y) % 3 ? PF_WET : 0));
        }
    Monster a = monster_make(SP_AQUAPO, 14), b = monster_make(SP_DANDELAMB, 12);
    storage_add(&a);
    storage_add(&b);
    for (int k = 0; k < 2; k++) {
        farm.workers[k].job = k ? JOB_TEND : JOB_WATER;
        farm.workers[k].species = storage[k].species;
        farm.workers[k].pot = storage[k].pot;
        farm.workers[k].level = storage[k].level;
    }
}

/* "travel": the RIME, DREAM and TIDE crests, a HOOTLORD that can FLY and
 * TELEPORT, an AXOLURK big enough to SURF, the BIKE, the TOWN MAP and every
 * town visited (so every fly point is open). */
static void demo_travel(void)
{
    travel.crests |= (1 << CREST_RIME) | (1 << CREST_DREAM) | (1 << CREST_TIDE);
    party[2] = monster_make(SP_HOOTLORD, 32);   /* the lead that follows you stays small */
    party[1] = monster_make(SP_AXOLURK, 24);
    for (int k = 1; k < 3; k++) {
        party[k].met_map = MAP_MEADOW;
        dex_seen[party[k].species] = dex_caught[party[k].species] = 1;
    }
    bag[ITEM_BIKE] = bag[ITEM_TOWN_MAP] = bag[ITEM_FERRY_PASS] = 1;
    for (int m = 0; m < MAP_COUNT; m++)
        if (!(MAPS[m].flags & MF_DEBUG)) bit_set(travel.visited, m);
}

/* "move=NAME": the lead kin's first move (NAME as in the game, _ for a space). */
static int demo_move(const char *name)
{
    char want[32];
    int n = 0;
    for (; name[n] && n < 31; n++) want[n] = name[n] == '_' ? ' ' : name[n];
    want[n] = 0;
    for (int mv = 0; mv < MOVE_TABLE_SIZE; mv++)
        if (MOVES[mv].name && !strcmp(MOVES[mv].name, want)) {
            party[0].moves[0] = (u8)mv;
            party[0].pp[0] = MOVES[mv].pp;
            return 1;
        }
    return 0;
}

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: %s OUT.sav [MAP X Y [calm] [low] [beaten] [night] [rain] [farm] [travel] [fusion] [evolve] [runestone] [move=NAME]]\n", argv[0]);
        return 1;
    }
    game_init();
    rng_seed(20260926u);
    new_game();
    int calm = 0, low = 0, beaten = 0, night = 0, rain = 0, farm_on = 0;
    int travel_on = 0, fusion_on = 0, evolve_on = 0, rune_on = 0;
    const char *move_name = 0;
    for (int i = 5; i < argc; i++) {
        if (!strcmp(argv[i], "calm")) calm = 1;
        if (!strcmp(argv[i], "low")) low = 1;
        if (!strcmp(argv[i], "beaten")) beaten = 1;
        if (!strcmp(argv[i], "night")) night = 1;
        if (!strcmp(argv[i], "rain")) rain = 1;
        if (!strcmp(argv[i], "farm")) farm_on = 1;
        if (!strcmp(argv[i], "travel")) travel_on = 1;
        if (!strcmp(argv[i], "fusion")) fusion_on = 1;
        if (!strcmp(argv[i], "evolve")) evolve_on = 1;
        if (!strcmp(argv[i], "runestone")) rune_on = 1;
        if (!strncmp(argv[i], "move=", 5)) move_name = argv[i] + 5;
    }
    static const u8 TEAM[5] = { SP_PYREFOX, SP_AXOLURK, SP_ZAPPET, SP_DANDELAMB, SP_GOLEMIT };
    static const u8 LV[5] = { 17, 15, 14, 13, 13 };
    static const u8 TEAM_LOW[5] = { SP_FLARIX, SP_AQUAPO, SP_ZAPPET, SP_DANDELAMB, SP_GOLEMIT };
    static const u8 LV_LOW[5] = { 8, 6, 5, 5, 5 };
    for (int i = 0; i < 5; i++) {
        Monster m = monster_make(low ? TEAM_LOW[i] : TEAM[i], low ? LV_LOW[i] : LV[i]);
        m.met_map = i ? MAP_MEADOW : MAP_LAB;
        m.bond = (u8)(120 + i * 20);
        give_monster(&m);
        dex_seen[low ? TEAM_LOW[i] : TEAM[i]] = 1;
    }
    Monster lus = monster_make(SP_NIBBIT, 9);
    lus.flags |= MF_LUSTROUS;
    lus.met_map = MAP_MEADOW;
    give_monster(&lus);
    for (int s = 0; s < SP_COUNT; s += 2) dex_seen[s] = 1;
    bag[ITEM_TONIC] = 6;
    bag[ITEM_BIG_TONIC] = 2;
    bag[ITEM_SOOTHE_BALM] = 2;
    bag[ITEM_LANTERN] = 9;
    bag[ITEM_GLOW_LANTERN] = 3;
    bag[ITEM_HUSH_BELL] = 1;
    bag[ITEM_BLOOM_SHARD] = 1;
    money = 4820;
    opt.text_speed = TEXT_FAST;  /* snappier clips */
    flags_story_clear(); flag_set(FLAG_STARTER); flag_set(FLAG_INTRO); flag_set(FLAG_TWIN_CRYSTAL); flag_set(FLAG_PIP_GIFT); flag_set(FLAG_GRAN_GIFT); flag_set(FLAG_BAKER_GIFT); flag_set(FLAG_LEAF_STONE); flag_set(FLAG_SASH); flag_set(FLAG_STORM_TOLD);
    trainer_mark_beaten(TR_MARLO);
    if (calm) flag_set(FLAG_STORM_CALMED);
    for (int i = 0; i < LORE_COUNT; i += 2) lore_learn(i);
    lore_learn(LORE_KINDLING);
    lore_learn(LORE_RING_SASH);
    int map = argc > 2 ? atoi(argv[2]) : MAP_MEADOW;
    int x = argc > 3 ? atoi(argv[3]) : 19, y = argc > 4 ? atoi(argv[4]) : 40;
    for (int i = 0; beaten && i < NPC_COUNT; i++)
        if (NPCS[i].map == map && NPCS[i].trainer != NO_TRAINER) trainer_mark_beaten(NPCS[i].trainer);
    if (night) gtime.minute = 22 * 60;
    if (rain) gtime.weather = WEATHER_RAIN;
    if (farm_on) demo_farm();
    if (travel_on) demo_travel();
    if (fusion_on) {                       /* the Works explained, energy in the tanks, a sure weave */
        fusion.flags |= FZF_INTRO;
        fusion.energy[T_BLAZE] = fusion.energy[T_TIDE] = 240;
        fusion.pity = 25;
    }
    if (evolve_on) {                       /* a THORNIP in the lead, ready for the BLOOM SHARD */
        Monster t = monster_make(SP_THORNIP, 12);
        t.met_map = MAP_MEADOW;
        party[0] = t;
        dex_seen[SP_THORNIP] = 1;
        bag[ITEM_BLOOM_SHARD] = 1;
    }
    if (rune_on) opt.registered = (u8)(ITEM_RUNESTONE + 1);
    if (move_name && !demo_move(move_name)) {
        fprintf(stderr, "no move %s\n", move_name);
        return 1;
    }
    field_enter_map(map, x, y, DIR_UP);
    static u8 sram[32768];
    for (unsigned i = 0; i < sizeof(sram); i++) sram[i] = 0xFF;
    if (!save_write_to(sram)) {
        fprintf(stderr, "could not build the save\n");
        return 1;
    }
    FILE *f = fopen(argv[1], "wb");
    if (!f) {
        perror(argv[1]);
        return 1;
    }
    fwrite(sram, 1, sizeof(sram), f);
    fclose(f);
    printf("wrote %s (map %d at %d,%d)\n", argv[1], map, x, y);
    return 0;
}
