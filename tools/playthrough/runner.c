/* ROM-backed, fail-closed waypoint timer. Build via run.py, not the game's Makefile. */
#include <mgba/core/core.h>
#include <mgba/core/log.h>
#include <mgba-util/vfs.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static color_t pixels[256 * 256];
static struct mCore *core;
static unsigned map_addr, player_addr, mode_addr, flags_addr, dialog_addr;
static unsigned long frames;
#define FRAMES_PER_MINUTE (59.7275 * 60.0)
static void quiet(struct mLogger *l, int c, enum mLogLevel level, const char *fmt, va_list v)
{ (void)l; (void)c; (void)level; (void)fmt; (void)v; }
static struct mLogger logger = { quiet, NULL };
static int rd16(unsigned a) { return core->busRead16(core, a); }
static int rd32(unsigned a) { return (int)core->busRead32(core, a); }
static int map(void) { return rd32(map_addr); }
static int x(void) { return (short)rd16(player_addr); }
static int y(void) { return (short)rd16(player_addr + 2); }
static int mode(void) { return rd32(mode_addr); }
static void frame(unsigned keys, int timed) {
    core->setKeys(core, keys); core->runFrame(core); if (timed) frames++;
}
static void tap(unsigned keys) {
    frame(keys, 0); frame(keys, 0);
    for (int i = 0; i < 8; i++) frame(0, 0);
}
static void fail(int line, const char *message) {
    fprintf(stderr, "BLOCKED line=%d reason=%s map=%d x=%d y=%d mode=%d dialog=%d frames=%lu minutes=%.3f\n",
            line, message, map(), x(), y(), mode(), rd32(dialog_addr), frames, frames / FRAMES_PER_MINUTE);
    core->deinit(core); exit(2);
}
int main(int argc, char **argv) {
    if (argc != 8) { fprintf(stderr, "usage: runner rom route mapAddr playerAddr modeAddr flagsAddr dialogAddr\n"); return 1; }
    map_addr = strtoul(argv[3], 0, 16); player_addr = strtoul(argv[4], 0, 16);
    mode_addr = strtoul(argv[5], 0, 16); flags_addr = strtoul(argv[6], 0, 16); dialog_addr = strtoul(argv[7], 0, 16);
    mLogSetDefaultLogger(&logger);
    core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) { fprintf(stderr, "libmgba core initialization failed\n"); return 1; }
    mCoreInitConfig(core, NULL);
    core->setVideoBuffer(core, pixels, 256);
    if (!mCoreLoadFile(core, argv[1])) { fprintf(stderr, "ROM load failed: %s\n", argv[1]); return 1; }
    /* Deliberately start with blank ephemeral SRAM; never read or write a user save. */
    static unsigned char sram[32768]; memset(sram, 0xff, sizeof(sram));
    core->loadSave(core, VFileMemChunk(sram, sizeof(sram))); core->reset(core);
    for (int i = 0; i < 180; i++) frame(0, 0);
    FILE *file = fopen(argv[2], "r");
    if (!file) { perror(argv[2]); return 1; }
    char buf[256], op[32]; int a, b, c, line = 0, started = 0;
    while (fgets(buf, sizeof(buf), file)) {
        line++;
        if (sscanf(buf, "%31s", op) != 1 || op[0] == '#') continue;
        if (!strcmp(op, "start") && sscanf(buf, "%*s %d", &a) == 1 && !started) {
            tap((1u << 2) | (1u << 3)); /* SELECT + START: title debug menu */
            for (int i = 0; i < 3; i++) tap(1u << 7); /* WARP TO MAP */
            tap(1u); /* open warp list */
            for (int i = 0; i < a / 8; i++) tap(1u << 8); /* R: 8 entries */
            for (int i = 0; i < a % 8; i++) tap(1u << 7);
            tap(1u);
            for (int i = 0; i < 300 && mode() != 0; i++) frame(0, 0);
            for (int i = 0; i < 30; i++) frame(0, 0);
            if (map() != a || mode() != 0) fail(line, "debug warp did not enter requested map");
            started = 1;
            printf("START map=%d x=%d y=%d\n", map(), x(), y());
        } else if (!strcmp(op, "flag") && sscanf(buf, "%*s %d", &a) == 1 && a >= 0 && a < 512) {
            unsigned addr = flags_addr + (unsigned)a / 8;
            core->busWrite8(core, addr, core->busRead8(core, addr) | (1u << (a % 8)));
            if (!(core->busRead8(core, addr) & (1u << (a % 8)))) fail(line, "flag write did not persist");
            printf("FLAG id=%d set=1\n", a);
        } else if (!strcmp(op, "way") && sscanf(buf, "%*s %d %d %d", &a, &b, &c) == 3 && started) {
            int still = 0;
            for (int i = 0; i < 30000 && (map() != a || x() != b || y() != c); i++) {
                if (map() != a) fail(line, "unexpected map; cross-map traversal not implemented");
                unsigned key = 0;
                if (x() < b) key = 1u << 4;
                else if (x() > b) key = 1u << 5;
                else if (y() < c) key = 1u << 7;
                else if (y() > c) key = 1u << 6;
                int old_map = map(), old_x = x(), old_y = y();
                frame(key, 1);
                if (old_map == map() && old_x == x() && old_y == y()) still++;
                else still = 0;
                if (still > 240) fail(line, mode() == 8 ? "bout needs policy-aware auto-resolution" : rd32(dialog_addr) ? "dialog stalled; no dialog policy" : "field collision or warden stalled; no auto-resolution policy");
            }
            if (map() != a || x() != b || y() != c) fail(line, "waypoint frame budget exceeded");
            printf("WAY line=%d map=%d x=%d y=%d frames=%lu minutes=%.3f\n", line, map(), x(), y(), frames, frames / FRAMES_PER_MINUTE);
        } else fail(line, "invalid command or order");
    }
    if (!started) fail(line, "missing start");
    printf("SEGMENT_COMPLETE frames=%lu minutes=%.3f heuristic_2.5x_minutes=%.3f\n", frames, frames / FRAMES_PER_MINUTE, frames * 2.5 / FRAMES_PER_MINUTE);
    fclose(file); core->deinit(core); return 0;
}
