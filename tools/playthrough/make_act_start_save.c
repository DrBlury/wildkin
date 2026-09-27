/* Disposable Act II entry fixture, serialized by the game's checked save writer. */
#define main gba_main
#include "../../src/main.c"
#undef main
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
    if (argc != 2) { fprintf(stderr, "usage: make_act_start_save output.sav\n"); return 1; }
    static u8 sram[32768];
    memset(sram, 0xff, sizeof(sram));
    new_game();
    rng_seed(0xAC7202u);
    const int species[] = { SP_FLARIX, SP_AQUAPO, SP_THORNIP, SP_GOLEMIT };
    const int levels[] = { 20, 19, 19, 20 };
    for (int i = 0; i < 4; i++) {
        Monster m = monster_make(species[i], levels[i]);
        if (give_monster(&m) != 0) { fprintf(stderr, "party insertion failed at %d\n", i); return 1; }
        printf("KIN index=%d species=%d level=%d hp=%u/%u pp=%u,%u,%u,%u\n",
               i, m.species, m.level, m.hp, m.max_hp, m.pp[0], m.pp[1], m.pp[2], m.pp[3]);
    }
    flag_set(FLAG_STARTER);
    flag_set(FLAG_STORM_CALMED);
    cur_map = MAP_BROOKMILL_TRAIL;
    player.x = 34; player.y = 18; player.facing = DIR_DOWN; player.level = 0;
    if (!save_write_to(sram)) { fprintf(stderr, "game save writer rejected fixture\n"); return 1; }
    FILE *out = fopen(argv[1], "wb");
    if (!out) { perror(argv[1]); return 1; }
    int ok = fwrite(sram, 1, sizeof(sram), out) == sizeof(sram);
    if (fclose(out) != 0) ok = 0;
    if (!ok) { fprintf(stderr, "fixture write failed\n"); return 1; }
    printf("SAVE version=%u party=%d map=%d x=%d y=%d flags=STARTER,STORM_CALMED bytes=%zu\n",
           SAVE_VERSION, party_count, cur_map, player.x, player.y, sizeof(sram));
    return 0;
}
