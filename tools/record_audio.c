/*
 * Headless audio capture harness built on libmgba.
 *
 *   cc -O2 -I/opt/homebrew/include -o build/record_audio tools/record_audio.c \
 *      -L/opt/homebrew/lib -lmgba -lz
 *   build/record_audio game.gba script.txt [save.sav]
 *
 * The script is a list of whitespace-separated commands, one per line:
 *   wait N            run N frames with no keys held
 *   hold KEYS N       hold KEYS (e.g. A, RIGHT, A+B) for N frames
 *   tap KEYS          hold KEYS for 2 frames, then release for 6
 *   peek ADDR LEN     print LEN bytes of bus memory at hex ADDR
 *   wav FILE.wav      start writing the audio output (16-bit stereo, 32768 Hz)
 *   wavstop           finish the file and print its levels
 *   # comment
 * An optional save file is loaded read-only into cartridge SRAM. A file
 * still open when the script ends is finished the same way as wavstop.
 *
 * The stats line gives the duration, then peak and RMS per channel in dBFS
 * (0 dBFS = int16 full scale), each peak also as a percentage of the GBA's
 * DAC ceiling, the fraction of samples beyond that ceiling and the fraction
 * at the int16 rails.
 *
 * Levels (mGBA 0.10, measured): the 10-bit DAC swings +-512 units and mGBA
 * writes 48 per unit, so the ceiling is +-24576 (-2.5 dBFS). One PSG channel
 * at envelope 15 (SNDCNT_L 0x77, PSG 100%) is about +-120 units; Direct
 * Sound at 100% is 4 units per int8 step, at 50% 2 units. The DAC clamps a
 * sum that leaves the range before int16 ever clips, and the resampler adds
 * a little ringing, so a square at exactly full scale reads about 103%.
 */
#include <mgba/core/blip_buf.h>
#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <mgba-util/vfs.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SAMPLE_RATE 32768
#define AUDIO_BUFFER 4096
#define DAC_CEILING 24576

static color_t frame[256 * 256];

static void log_quiet(struct mLogger *logger, int category, enum mLogLevel level,
                      const char *format, va_list args)
{
    (void)logger; (void)category; (void)level; (void)format; (void)args;
}
static struct mLogger quiet_logger = { log_quiet, NULL };

static struct {
    FILE *f;
    char path[512];
    unsigned long frames;          /* stereo sample pairs written */
    unsigned long clipped;         /* individual samples at an int16 rail */
    unsigned long over_dac;        /* individual samples beyond the DAC ceiling */
    double sum_sq[2];
    int peak[2];
} wav;

static void put_le(unsigned char *p, unsigned v, int bytes)
{
    for (int i = 0; i < bytes; i++) p[i] = (unsigned char)(v >> (8 * i));
}

static void wav_header(FILE *f, unsigned long frames)
{
    unsigned data = (unsigned)(frames * 4);
    unsigned char h[44];
    memcpy(h, "RIFF", 4);
    put_le(h + 4, 36 + data, 4);
    memcpy(h + 8, "WAVEfmt ", 8);
    put_le(h + 16, 16, 4);              /* fmt chunk size */
    put_le(h + 20, 1, 2);               /* PCM */
    put_le(h + 22, 2, 2);               /* channels */
    put_le(h + 24, SAMPLE_RATE, 4);
    put_le(h + 28, SAMPLE_RATE * 4, 4); /* byte rate */
    put_le(h + 32, 4, 2);               /* block align */
    put_le(h + 34, 16, 2);              /* bits per sample */
    memcpy(h + 36, "data", 4);
    put_le(h + 40, data, 4);
    fseek(f, 0, SEEK_SET);
    fwrite(h, 1, sizeof(h), f);
}

static void wav_start(const char *path)
{
    if (wav.f) {
        fprintf(stderr, "wav: %s is still open (wavstop first)\n", wav.path);
        exit(1);
    }
    memset(&wav, 0, sizeof(wav));
    snprintf(wav.path, sizeof(wav.path), "%s", path);
    wav.f = fopen(path, "wb");
    if (!wav.f) {
        perror(path);
        exit(1);
    }
    wav_header(wav.f, 0);
}

static double dbfs(double v)
{
    return v > 0 ? 20.0 * log10(v / 32768.0) : -INFINITY;
}

static void wav_stop(void)
{
    if (!wav.f) {
        fprintf(stderr, "wavstop: no wav file is open\n");
        exit(1);
    }
    wav_header(wav.f, wav.frames);
    fclose(wav.f);
    wav.f = NULL;
    double n = wav.frames ? (double)wav.frames : 1.0;
    double rms_l = sqrt(wav.sum_sq[0] / n), rms_r = sqrt(wav.sum_sq[1] / n);
    printf("wav %s: %.2f s @ %d Hz stereo"
           " | L peak %.1f dBFS (%d, %.0f%% DAC) rms %.1f dBFS"
           " | R peak %.1f dBFS (%d, %.0f%% DAC) rms %.1f dBFS"
           " | over DAC %.4f%% | clipped %.4f%%\n",
           wav.path, wav.frames / (double)SAMPLE_RATE, SAMPLE_RATE,
           dbfs(wav.peak[0]), wav.peak[0], 100.0 * wav.peak[0] / DAC_CEILING, dbfs(rms_l),
           dbfs(wav.peak[1]), wav.peak[1], 100.0 * wav.peak[1] / DAC_CEILING, dbfs(rms_r),
           100.0 * wav.over_dac / (2.0 * n), 100.0 * wav.clipped / (2.0 * n));
}

/* Take every sample the core produced this frame; keep them while a file
 * is open. Draining every frame keeps the core from dropping samples. */
static void drain_audio(struct mCore *core)
{
    static short buf[AUDIO_BUFFER * 2];
    struct blip_t *left = core->getAudioChannel(core, 0);
    struct blip_t *right = core->getAudioChannel(core, 1);
    int avail;
    while ((avail = blip_samples_avail(left)) > 0) {
        if (avail > AUDIO_BUFFER) avail = AUDIO_BUFFER;
        int got = blip_read_samples(left, buf, avail, 1);
        blip_read_samples(right, buf + 1, got, 1);
        if (!wav.f) continue;
        for (int i = 0; i < got * 2; i++) {
            int s = buf[i], a = s < 0 ? -s : s;
            if (a > wav.peak[i & 1]) wav.peak[i & 1] = a;
            wav.sum_sq[i & 1] += (double)s * s;
            if (a > DAC_CEILING) wav.over_dac++;
            if (s >= 32767 || s <= -32768) wav.clipped++;
            unsigned char le[2];
            put_le(le, (unsigned)(unsigned short)s, 2);
            fwrite(le, 1, 2, wav.f);
        }
        wav.frames += (unsigned long)got;
    }
}

static void run_frame(struct mCore *core)
{
    core->runFrame(core);
    drain_audio(core);
}

static unsigned parse_keys(const char *s)
{
    static const char *names[] = { "A", "B", "SELECT", "START", "RIGHT",
                                   "LEFT", "UP", "DOWN", "R", "L" };
    unsigned keys = 0;
    char buf[64];
    snprintf(buf, sizeof(buf), "%s", s);
    for (char *tok = strtok(buf, "+"); tok; tok = strtok(NULL, "+")) {
        int found = 0;
        for (unsigned i = 0; i < sizeof(names) / sizeof(names[0]); i++)
            if (!strcmp(tok, names[i])) {
                keys |= 1u << i;
                found = 1;
            }
        if (!found && strcmp(tok, "NONE")) {
            fprintf(stderr, "unknown key %s\n", tok);
            exit(1);
        }
    }
    return keys;
}

int main(int argc, char **argv)
{
    if (argc < 3) {
        fprintf(stderr, "usage: %s rom.gba script.txt [save.sav]\n", argv[0]);
        return 1;
    }
    mLogSetDefaultLogger(&quiet_logger);
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) {
        fprintf(stderr, "cannot create core\n");
        return 1;
    }
    mCoreInitConfig(core, NULL);
    core->setVideoBuffer(core, frame, 256);
    if (!mCoreLoadFile(core, argv[1])) {
        fprintf(stderr, "cannot load %s\n", argv[1]);
        return 1;
    }
    static unsigned char sram[65536];
    size_t sram_len = 32768;
    memset(sram, 0xFF, sizeof(sram));
    if (argc > 3) {
        FILE *sf = fopen(argv[3], "rb");
        if (sf) {
            sram_len = fread(sram, 1, sizeof(sram), sf);
            fclose(sf);
        }
    }
    core->loadSave(core, VFileMemChunk(sram, sram_len));
    core->reset(core);
    core->setAudioBufferSize(core, AUDIO_BUFFER);
    blip_set_rates(core->getAudioChannel(core, 0), core->frequency(core), SAMPLE_RATE);
    blip_set_rates(core->getAudioChannel(core, 1), core->frequency(core), SAMPLE_RATE);

    FILE *script = fopen(argv[2], "r");
    if (!script) {
        perror(argv[2]);
        return 1;
    }
    char line[1024];
    while (fgets(line, sizeof(line), script)) {
        char cmd[32] = { 0 }, a1[512] = { 0 }, a2[32] = { 0 };
        int n = sscanf(line, "%31s %511s %31s", cmd, a1, a2);
        if (n <= 0 || cmd[0] == '#')
            continue;
        if (!strcmp(cmd, "wait")) {
            core->setKeys(core, 0);
            for (int i = atoi(a1); i > 0; i--) run_frame(core);
        } else if (!strcmp(cmd, "hold")) {
            core->setKeys(core, parse_keys(a1));
            for (int i = atoi(a2); i > 0; i--) run_frame(core);
            core->setKeys(core, 0);
        } else if (!strcmp(cmd, "tap")) {
            core->setKeys(core, parse_keys(a1));
            run_frame(core);
            run_frame(core);
            core->setKeys(core, 0);
            for (int i = 0; i < 6; i++) run_frame(core);
        } else if (!strcmp(cmd, "peek")) {
            unsigned addr = (unsigned)strtoul(a1, NULL, 16), len = (unsigned)atoi(a2);
            printf("%08x:", addr);
            for (unsigned i = 0; i < len; i++) printf(" %02x", core->busRead8(core, addr + i));
            printf("\n");
        } else if (!strcmp(cmd, "wav")) {
            wav_start(a1);
        } else if (!strcmp(cmd, "wavstop")) {
            wav_stop();
        } else {
            fprintf(stderr, "unknown command %s\n", cmd);
            return 1;
        }
    }
    fclose(script);
    if (wav.f) wav_stop();
    core->deinit(core);
    return 0;
}
