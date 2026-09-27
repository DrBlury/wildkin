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

int main(int argc, char **argv)
{
    if (argc < 2) {
        fprintf(stderr, "usage: %s OUT.sav [MAP X Y [calm] [low] [beaten] [night] [rain]]\n", argv[0]);
        return 1;
    }
    game_init();
    rng_seed(20260926u);
    new_game();
    int calm = 0, low = 0, beaten = 0, night = 0, rain = 0;
    for (int i = 5; i < argc; i++) {
        if (!strcmp(argv[i], "calm")) calm = 1;
        if (!strcmp(argv[i], "low")) low = 1;
        if (!strcmp(argv[i], "beaten")) beaten = 1;
        if (!strcmp(argv[i], "night")) night = 1;
        if (!strcmp(argv[i], "rain")) rain = 1;
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
