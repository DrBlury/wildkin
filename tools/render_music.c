/*
 * Render songs with the game's own music engine (src/game/music.c) on the
 * host: one WAV per song plus level statistics, so the mix can be checked
 * without an emulator.
 *
 *   make songs                        (all songs -> build/music/*.wav)
 *   build/render_music [-s SECONDS] [-o DIR] [SONG...]
 *
 * SONG is a name like VILLAGE (see src/music_data.h). By default a song
 * plays its intro, the loop twice and a short tail. Stats per song: peak,
 * RMS (dBFS), share of clipped samples and the busiest channel count.
 */
#include "../src/game/gba.h"

/* the options the audio code reads (the real ones live in options.h) */
static struct {
    u8 text_speed, battle_anims, sound, follower, autosave, music, music_vol, pad;
} opt = { 1, 1, 1, 1, 1, 1, 0, 0 };

#include "../src/game/sfx.c"
#include "../src/game/music.c"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void put16(FILE *f, unsigned v)
{
    fputc((int)(v & 0xFF), f);
    fputc((int)((v >> 8) & 0xFF), f);
}

static void put32(FILE *f, unsigned v)
{
    put16(f, v & 0xFFFF);
    put16(f, v >> 16);
}

static int render(int song, double seconds, const char *dir)
{
    int frames = seconds > 0 ? (int)(seconds * 60.0) : MUS_FRAMES[song] * 2 + 90;
    if (MUS_SONGS[song].loop[0] == 0xFFFF && seconds <= 0) frames = MUS_FRAMES[song] + 60;
    char path[512];
    snprintf(path, sizeof(path), "%s/%s.wav", dir, MUS_TITLES[song]);
    for (char *p = path + strlen(dir) + 1; *p; p++)
        if (*p == ' ' || *p == '\'' || *p == '/') *p = '_';
    FILE *f = fopen(path, "wb");
    if (!f) {
        perror(path);
        return 1;
    }
    unsigned n = (unsigned)frames * MUS_MIX_LEN;
    unsigned rate = (unsigned)(16777216.0 / MUS_RATE_CYCLES + 0.5);
    fwrite("RIFF", 1, 4, f);
    put32(f, 36 + n * 2);
    fwrite("WAVEfmt ", 1, 8, f);
    put32(f, 16);
    put16(f, 1);
    put16(f, 1);
    put32(f, rate);
    put32(f, rate * 2);
    put16(f, 2);
    put16(f, 16);
    fwrite("data", 1, 4, f);
    put32(f, n * 2);

    music_play_now(song);
    double sum = 0;
    int peak = 0;
    unsigned clipped = 0;
    int busiest = 0;
    for (int fr = 0; fr < frames; fr++) {
        const s8 *buf = music_host_frame();
        int busy = 0;
        for (int c = 0; c < MUS_CHANNELS; c++)
            if (mus_voice[c].count && mus_voice[c].vol) busy++;
        if (busy > busiest) busiest = busy;
        for (int i = 0; i < MUS_MIX_LEN; i++) {
            int s = buf[i];
            put16(f, (unsigned)(s * 256) & 0xFFFF);
            sum += (double)s * s;
            if (abs(s) > peak) peak = abs(s);
            if (s >= 127 || s <= -128) clipped++;
        }
    }
    fclose(f);
    double rms = sqrt(sum / n);
    printf("%-24s %6.1f s  peak %3d  rms %5.1f dBFS  clipped %5.2f%%  voices %d\n", MUS_TITLES[song],
           frames / 60.0, peak, rms > 0 ? 20 * log10(rms / 128.0) : -99.0, 100.0 * clipped / n, busiest);
    return 0;
}

int main(int argc, char **argv)
{
    double seconds = 0;
    const char *dir = "build/music";
    int first = 1;
    while (first < argc && argv[first][0] == '-') {
        if (!strcmp(argv[first], "-s") && first + 1 < argc) {
            seconds = atof(argv[first + 1]);
            first += 2;
        } else if (!strcmp(argv[first], "-o") && first + 1 < argc) {
            dir = argv[first + 1];
            first += 2;
        } else {
            fprintf(stderr, "usage: %s [-s SECONDS] [-o DIR] [SONG...]\n", argv[0]);
            return 1;
        }
    }
    music_init();
    int fails = 0;
    if (first >= argc) {
        for (int s = 1; s < SONG_COUNT; s++) fails += render(s, seconds, dir);
        return fails != 0;
    }
    for (int a = first; a < argc; a++) {
        int found = -1;
        for (int s = 1; s < SONG_COUNT; s++) {
            char want[64];
            snprintf(want, sizeof(want), "%s", MUS_TITLES[s]);
            if (!strcmp(argv[a], want) || !strcmp(argv[a], MUS_IDENTS[s])) found = s;
        }
        if (found < 0) {
            fprintf(stderr, "unknown song %s\n", argv[a]);
            fails++;
            continue;
        }
        fails += render(found, seconds, dir);
    }
    return fails != 0;
}
