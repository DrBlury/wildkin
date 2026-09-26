/*
 * Music checks: every song compiles to streams the sequencer can play for
 * two full passes, the title, field and bout themes start where they
 * should (and are audible), bouts hand the field song back, and the
 * MUSIC option silences the mix. The host runs the same sequencer and
 * mixer as the cartridge (game_frame -> music_host_frame).
 */
#include "harness.h"

/* square root without libm (the test build does not link it) */
static double root(double x)
{
    if (x <= 0) return 0;
    double r = x > 1 ? x : 1;
    for (int i = 0; i < 60; i++) r = 0.5 * (r + x / r);
    return r;
}

/* RMS of the next `frames` frames of mixed output (int8 units). */
static double music_rms(int frames)
{
    double sum = 0;
    for (int f = 0; f < frames; f++) {
        step(0);
        const s8 *out = mus_buf + mus.play_buf * MUS_MIX_LEN;
        for (int i = 0; i < MUS_MIX_LEN; i++) sum += (double)out[i] * out[i];
    }
    return root(sum / ((double)frames * MUS_MIX_LEN));
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();

    /* the title screen plays the main theme */
    double rms = music_rms(90);
    CHECK(game_mode == MODE_TITLE && mus.song == SONG_TITLE, "the title screen plays SONG_TITLE");
    CHECK(rms > 4.0, "the title theme is audible");
    printf("  title rms %.1f\n", rms);

    /* every song keeps playing through two passes (loops) or ends (jingles) */
    int songs_ok = 1;
    for (int s = SONG_NONE + 1; s < SONG_COUNT; s++) {
        music_play_now(s);
        int frames = MUS_FRAMES[s] * 2 + 30;
        double sum = 0;
        for (int f = 0; f < frames; f++) {
            const s8 *out = music_host_frame();
            for (int i = 0; i < MUS_MIX_LEN; i++) sum += (double)out[i] * out[i];
        }
        int alive = 0;
        for (int c = 0; c < MUS_SONGS[s].count; c++)
            if (mus_ch[c].pc) alive++;
        double r = root(sum / ((double)frames * MUS_MIX_LEN));
        if (mus.song != s || alive != MUS_SONGS[s].count || r < 4.0) {
            songs_ok = 0;
            printf("  %s: song %d, %d of %d channels alive, rms %.1f\n", MUS_IDENTS[s], mus.song, alive,
                   MUS_SONGS[s].count, r);
        }
    }
    CHECK(songs_ok, "every song loops through two passes with all channels alive and audible");

    /* the song for each kind of map */
    CHECK(music_song_for_map(MAP_TOWN) == SONG_VILLAGE, "Maple Village plays the village theme");
    CHECK(music_song_for_map(MAP_HOME) == SONG_VILLAGE, "houses play the village theme");
    CHECK(music_song_for_map(MAP_MEADOW) == SONG_ROUTE, "Whisper Meadow plays the route theme");
    CHECK(music_song_for_map(MAP_REST) == SONG_HEARTH, "the Hearth Hall plays its own theme");
    CHECK(music_song_for_map(MAP_LUMEN_HEARTH) == SONG_HEARTH, "every Hearth Hall plays the hearth theme");
    CHECK(music_song_for_map(MAP_GLIMMER_1) == SONG_CAVE, "caves play the cave theme");
    CHECK(music_song_for_map(MAP_LANTERN_CRYPT) == SONG_CAVE, "crypts play the cave theme");
    int all_ok = 1;
    for (int m = 0; m < MAP_COUNT; m++) {
        int s = music_song_for_map(m);
        if (s <= SONG_NONE || s >= SONG_COUNT) all_ok = 0;
    }
    CHECK(all_ok, "every map has a song");

    /* walking into the meadow starts the route theme */
    fresh_game();
    give_starter();
    field_enter_map(MAP_MEADOW, 10, 10, DIR_DOWN);
    rms = music_rms(60);
    CHECK(mus.song == SONG_ROUTE, "entering the meadow fades into the route theme");
    CHECK(rms > 4.0, "the route theme is audible");
    printf("  route rms %.1f\n", rms);

    /* a wild bout: battle theme, victory, then the route theme again */
    battle_start_wild(monster_make(SP_DANDELAMB, 3));
    rms = music_rms(30);
    CHECK(mus.song == SONG_BATTLE, "a wild bout cuts to the battle theme");
    CHECK(rms > 4.0, "the battle theme is audible");
    printf("  battle rms %.1f\n", rms);
    music_battle_cue(BCUE_WIN);
    step(0);
    CHECK(mus.song == SONG_VICTORY, "winning plays the victory theme");
    music_battle_cue(BCUE_END);
    music_rms(40);
    CHECK(mus.song == SONG_ROUTE, "closing the bout brings the route theme back");

    music_battle_cue(BCUE_START_MASTER);
    step(0);
    CHECK(mus.song == SONG_MASTER, "a Hall Master bout plays the master theme");
    music_battle_cue(BCUE_RUN);
    music_rms(40);
    CHECK(mus.song == SONG_NONE, "running away fades the music out");
    music_battle_cue(BCUE_END);
    music_rms(4);
    CHECK(mus.song == SONG_ROUTE, "and the field song comes back after the bout");

    /* the MUSIC option */
    opt.music = 0;
    rms = music_rms(10);
    CHECK(rms == 0.0, "MUSIC OFF silences the mix");
    opt.music = 1;
    opt.music_vol = 1;
    double low = music_rms(60);
    opt.music_vol = 0;
    double high = music_rms(60);
    CHECK(low > 0.0 && low < high, "MUSIC VOLUME LOW is quieter than HIGH");

    if (failures) {
        printf("%d music checks FAILED\n", failures);
        return 1;
    }
    printf("all music checks passed\n");
    return 0;
}
