/*
 * Headless screenshot harness built on libmgba.
 *
 *   make shot  (builds build/shot)
 *   build/shot game.gba script.txt [save.sav]
 *
 * The script is a list of whitespace-separated commands, one per line:
 *   wait N            run N frames with no keys held
 *   hold KEYS N       hold KEYS (e.g. A, RIGHT, A+B) for N frames
 *   tap KEYS          hold KEYS for 2 frames, then release for 6
 *   shot FILE.png     write the current frame as a PNG (2x)
 *   rec PREFIX STEP   start recording: every STEP frames write PREFIX_0000.png
 *                     (1x) while the following commands run
 *   stop              stop recording
 *   save FILE.sav     write the cartridge SRAM to a file
 *   peek ADDR LEN     print LEN bytes of bus memory at hex ADDR
 *   # comment
 * An optional save file is loaded read-only into cartridge SRAM.
 */
#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <mgba-util/vfs.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <zlib.h>

static color_t frame[256 * 256];

static void log_quiet(struct mLogger *logger, int category, enum mLogLevel level,
                      const char *format, va_list args)
{
    (void)logger; (void)category; (void)level; (void)format; (void)args;
}
static struct mLogger quiet_logger = { log_quiet, NULL };

static void put32(unsigned char *p, unsigned v)
{
    p[0] = (unsigned char)(v >> 24);
    p[1] = (unsigned char)(v >> 16);
    p[2] = (unsigned char)(v >> 8);
    p[3] = (unsigned char)v;
}

static void write_chunk(FILE *f, const char *type, const unsigned char *data, unsigned len)
{
    unsigned char hdr[8];
    put32(hdr, len);
    memcpy(hdr + 4, type, 4);
    fwrite(hdr, 1, 8, f);
    if (len) fwrite(data, 1, len, f);
    unsigned crc = (unsigned)crc32(0, (const unsigned char *)type, 4);
    if (len) crc = (unsigned)crc32(crc, data, len);
    unsigned char c[4];
    put32(c, crc);
    fwrite(c, 1, 4, f);
}

/* Screenshots are scaled 2x so small pixel details are easy to inspect;
 * recorded animation frames stay at 1x. */
static void write_png(struct mCore *core, const char *path, unsigned w, unsigned h, unsigned scale)
{
    const void *pixels;
    size_t stride;
    core->getPixels(core, &pixels, &stride);
    const color_t *src = pixels;
    unsigned ow = w * scale, oh = h * scale;
    size_t raw_len = (size_t)(ow * 3 + 1) * oh;
    unsigned char *raw = malloc(raw_len);
    for (unsigned y = 0; y < oh; y++) {
        unsigned char *row = raw + (size_t)y * (ow * 3 + 1);
        row[0] = 0;
        for (unsigned x = 0; x < ow; x++) {
            color_t c = src[(y / scale) * stride + x / scale];
            row[1 + x * 3 + 0] = (unsigned char)(c & 0xFF);
            row[1 + x * 3 + 1] = (unsigned char)((c >> 8) & 0xFF);
            row[1 + x * 3 + 2] = (unsigned char)((c >> 16) & 0xFF);
        }
    }
    uLongf zlen = compressBound(raw_len);
    unsigned char *z = malloc(zlen);
    compress2(z, &zlen, raw, raw_len, 6);
    FILE *f = fopen(path, "wb");
    if (!f) {
        perror(path);
        exit(1);
    }
    static const unsigned char sig[8] = { 137, 'P', 'N', 'G', 13, 10, 26, 10 };
    fwrite(sig, 1, 8, f);
    unsigned char ihdr[13];
    put32(ihdr, ow);
    put32(ihdr + 4, oh);
    ihdr[8] = 8;  /* bit depth */
    ihdr[9] = 2;  /* truecolor */
    ihdr[10] = ihdr[11] = ihdr[12] = 0;
    write_chunk(f, "IHDR", ihdr, 13);
    write_chunk(f, "IDAT", z, (unsigned)zlen);
    write_chunk(f, "IEND", NULL, 0);
    fclose(f);
    free(raw);
    free(z);
}

static struct {
    char prefix[160];
    int step, active, frame, count;
    unsigned w, h;
} rec;

/* Advance one frame, writing a recorded frame when due. */
static void run_frame(struct mCore *core)
{
    core->runFrame(core);
    if (!rec.active) return;
    if (rec.frame++ % rec.step) return;
    char path[200];
    snprintf(path, sizeof(path), "%s_%04d.png", rec.prefix, rec.count++);
    write_png(core, path, rec.w, rec.h, 1);
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
    unsigned w, h;
    core->desiredVideoDimensions(core, &w, &h);
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

    FILE *script = fopen(argv[2], "r");
    if (!script) {
        perror(argv[2]);
        return 1;
    }
    char line[256];
    while (fgets(line, sizeof(line), script)) {
        char cmd[32] = { 0 }, a1[128] = { 0 }, a2[32] = { 0 };
        int n = sscanf(line, "%31s %127s %31s", cmd, a1, a2);
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
        } else if (!strcmp(cmd, "shot")) {
            write_png(core, a1, w, h, 2);
            printf("wrote %s\n", a1);
        } else if (!strcmp(cmd, "rec")) {
            snprintf(rec.prefix, sizeof(rec.prefix), "%s", a1);
            rec.step = atoi(a2) > 0 ? atoi(a2) : 2;
            rec.active = 1;
            rec.frame = rec.count = 0;
            rec.w = w;
            rec.h = h;
        } else if (!strcmp(cmd, "stop")) {
            rec.active = 0;
            printf("recorded %d frames to %s_*\n", rec.count, rec.prefix);
        } else if (!strcmp(cmd, "save")) {
            FILE *sf = fopen(a1, "wb");
            if (sf) {
                for (unsigned i = 0; i < 32768; i++) fputc(core->busRead8(core, 0x0E000000u + i), sf);
                fclose(sf);
                printf("wrote %s\n", a1);
            }
        } else {
            fprintf(stderr, "unknown command %s\n", cmd);
            return 1;
        }
    }
    fclose(script);
    core->deinit(core);
    return 0;
}
