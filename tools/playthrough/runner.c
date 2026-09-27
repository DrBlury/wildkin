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
static unsigned phase_addr, battle_addr, party_addr, moves_addr, warp_addr;
static int wild_wins, wild_runs, wardens, dialogs, wild_limit = 6;
/* Filled only after run.py verifies unique ELF structures and all members. */
static struct {
    unsigned kind, team, team2, team_idx, ally, pair, no_run;
    unsigned state, cursor, move_cursor, result, timer;
    unsigned monster_size, moves, pp, hp;
    unsigned move_size, cat, power, acc, effect;
} layout;
enum { KEY_A = 1u, KEY_RIGHT = 1u << 4,
       KEY_LEFT = 1u << 5, KEY_UP = 1u << 6, KEY_DOWN = 1u << 7 };
static int rd8(unsigned a) { return core->busRead8(core, a); }
static unsigned long frames;
static int title_from_mode = -1, title_from_map = -1, title_from_x = -1, title_from_y = -1;
static int saw_battle, last_battle_state = -1, last_battle_result = -1, last_battle_pair = -1;
#define FRAMES_PER_MINUTE (59.7275 * 60.0)
static void quiet(struct mLogger *l, int c, enum mLogLevel level, const char *fmt, va_list v)
{ (void)l; (void)c; (void)level; (void)fmt; (void)v; }
static struct mLogger logger = { quiet, NULL };
static int rd16(unsigned a) { return core->busRead16(core, a); }
static int rd32(unsigned a) { return (int)core->busRead32(core, a); }
static int battle_state(void) { return rd32(battle_addr + layout.state); }
static int battle_kind(void) { return rd32(battle_addr + layout.kind); }
static int map(void) { return rd32(map_addr); }
static int x(void) { return (short)rd16(player_addr); }
static int y(void) { return (short)rd16(player_addr + 2); }
static int mode(void) { return rd32(mode_addr); }
static void frame(unsigned keys, int timed) {
    int before = timed ? mode() : -1;
    int before_map = timed ? map() : -1, before_x = timed ? x() : -1, before_y = timed ? y() : -1;
    if (timed && before == 8) {
        saw_battle = 1;
        last_battle_state = battle_state();
        last_battle_result = rd32(battle_addr + layout.result);
        last_battle_pair = rd32(battle_addr + layout.pair);
    }
    core->setKeys(core, keys); core->runFrame(core);
    if (timed) {
        frames++;
        int after = mode();
        if (after == 8) {
            saw_battle = 1;
            last_battle_state = battle_state();
            last_battle_result = rd32(battle_addr + layout.result);
            last_battle_pair = rd32(battle_addr + layout.pair);
        }
        if (before != 10 && after == 10 && title_from_mode < 0) {
            title_from_mode = before;
            title_from_map = before_map;
            title_from_x = before_x;
            title_from_y = before_y;
        }
    }
}
static void press(unsigned keys) {
    frame(keys, 1);
    frame(0, 1);
}
static void tap(unsigned keys) {
    frame(keys, 0); frame(keys, 0);
    for (int i = 0; i < 8; i++) frame(0, 0);
}
static void fail(int line, const char *message) {
    fprintf(stderr, "BLOCKED line=%d reason=%s map=%d x=%d y=%d mode=%d dialog=%d phase=%d battle_state=%d wild_wins=%d wild_runs=%d wardens=%d dialogs=%d frames=%lu minutes=%.3f title_from_mode=%d title_from_map=%d title_from_x=%d title_from_y=%d saw_battle=%d last_battle_state=%d last_battle_result=%d last_battle_pair=%d\n",
            line, message, map(), x(), y(), mode(), rd32(dialog_addr), rd32(phase_addr), mode() == 8 ? battle_state() : -1,
            wild_wins, wild_runs, wardens, dialogs, frames, frames / FRAMES_PER_MINUTE,
            title_from_mode, title_from_map, title_from_x, title_from_y, saw_battle,
            last_battle_state, last_battle_result, last_battle_pair);
    core->deinit(core); exit(2);
}
/* The ROM move table is read-only. Rank usable attacking moves by expected raw
 * power; type effectiveness/status utility cannot be inferred from raw strength. */
static int best_move(void) {
    int ally = rd32(battle_addr + layout.ally);
    if (ally < 0 || ally >= 6) return -1;
    unsigned mon = party_addr + (unsigned)ally * layout.monster_size;
    int best = -1, score = -1;
    for (int i = 0; i < 4; i++) {
        int id = rd8(mon + layout.moves + i), pp = rd8(mon + layout.pp + i);
        if (id <= 0 || id >= 130 || !pp) continue;
        unsigned move = moves_addr + (unsigned)id * layout.move_size;
        if (rd8(move + layout.cat) >= 2) continue; /* CAT_STATUS */
        int power = rd8(move + layout.power), accuracy = rd8(move + layout.acc);
        int value = power * (accuracy ? accuracy : 100);
        if (value > score) { score = value; best = i; }
    }
    return best;
}
static void drive_battle(int line, int *last_kind) {
    int kind = battle_kind(), state = battle_state();
    if (kind != 0 && kind != 1) fail(line, "unknown battle kind");
    if (rd32(battle_addr + layout.pair)) fail(line, "paired bout needs explicit actor/target policy");
    if (*last_kind < 0) {
        *last_kind = kind;
        printf("BOUT kind=%s map=%d x=%d y=%d wild_wins=%d\n",
               kind ? "warden" : "wild", map(), x(), y(), wild_wins);
    }
    static int intro_timer = -1, intro_still = 0;
    if (state == 0) {
        int timer = rd32(battle_addr + layout.timer);
        if (timer == intro_timer) intro_still++;
        else intro_still = 0;
        intro_timer = timer;
        if (intro_still > 300) fail(line, "battle intro stalled; ROM timer unchanged");
    } else {
        intro_timer = -1;
        intro_still = 0;
    }
    if (state == 2) { /* action */
        int flee = !kind && wild_wins >= wild_limit;
        if (flee && rd8(battle_addr + layout.no_run)) fail(line, "wild bout forbids fleeing");
        int cursor = rd32(battle_addr + layout.cursor), target = flee ? 3 : 0;
        if (cursor < 0 || cursor > 3) fail(line, "invalid battle action cursor");
        if (cursor != target) press(KEY_DOWN);
        else press(KEY_A);
    } else if (state == 3) { /* move grid */
        int target = best_move(), cursor = rd32(battle_addr + layout.move_cursor);
        if (target < 0) fail(line, "no usable attacking move; recovery needed");
        if (cursor < 0 || cursor > 3) fail(line, "invalid battle move cursor");
        if (cursor == target) press(KEY_A);
        else if ((cursor & 2) != (target & 2)) press((target & 2) ? KEY_DOWN : KEY_UP);
        else press((target & 1) ? KEY_RIGHT : KEY_LEFT);
    } else if (state == 0 || state == 1 || state == 7) {
        /* Intro, animation/text event, outro: pulse A only for text pages. */
        press(KEY_A);
    } else fail(line, "battle needs manual party/item/learn choice");
}
static void drive_dialog(int line) {
    if (rd32(phase_addr) == 2) fail(line, "dialog choice needs explicit route policy");
    press(KEY_A);
    dialogs++;
}
static void step(int line, unsigned direction, int *last_kind) {
    int previous_mode = mode();
    if (previous_mode == 10) fail(line, "returned to title during timed route; possible ROM reset");
    if (previous_mode == 8) drive_battle(line, last_kind);
    else if (previous_mode == 0 && rd32(dialog_addr)) drive_dialog(line);
    else if (previous_mode == 0) frame(direction, 1);
    else fail(line, "unhandled mode; manual recovery/healing required");
    if (mode() == 10) fail(line, "returned to title during timed route; possible ROM reset");
    if (previous_mode == 8 && mode() != 8) {
        int result = rd32(battle_addr + layout.result);
        if (result == 2) fail(line, "party lost; no unmeasured recovery");
        if (*last_kind == 1) {
            if (result != 1) fail(line, "warden did not end in victory");
            wardens++;
        } else if (result == 1) wild_wins++;
        else if (result == 3) wild_runs++;
        else fail(line, "wild bout ended without victory or flight");
        printf("BOUT_END kind=%s result=%d wild_wins=%d wild_runs=%d wardens=%d frames=%lu\n",
               *last_kind ? "warden" : "wild", result, wild_wins, wild_runs, wardens, frames);
        *last_kind = -1;
    }
}
int main(int argc, char **argv) {
    if (argc != 36) { fprintf(stderr, "usage: runner rom route 10 addresses 23 ELF layout values\n"); return 1; }
    map_addr = strtoul(argv[3], 0, 16); player_addr = strtoul(argv[4], 0, 16);
    mode_addr = strtoul(argv[5], 0, 16); flags_addr = strtoul(argv[6], 0, 16); dialog_addr = strtoul(argv[7], 0, 16);
    phase_addr = strtoul(argv[8], 0, 16); battle_addr = strtoul(argv[9], 0, 16);
    party_addr = strtoul(argv[10], 0, 16); moves_addr = strtoul(argv[11], 0, 16); warp_addr = strtoul(argv[12], 0, 16);
    /* Layout argument order is LAYOUT_FIELDS in run.py: size then members. */
    unsigned offsets[23];
    for (int i = 0; i < 23; i++) {
        char *end;
        unsigned long value = strtoul(argv[13 + i], &end, 10);
        if (!argv[13 + i][0] || *end || value > 0xfffffffful) {
            fprintf(stderr, "invalid ELF layout argument %d\n", i); return 1;
        }
        offsets[i] = (unsigned)value;
    }
    layout.kind = offsets[1]; layout.team = offsets[2]; layout.team2 = offsets[3];
    layout.team_idx = offsets[4]; layout.ally = offsets[5]; layout.pair = offsets[6];
    layout.no_run = offsets[7]; layout.state = offsets[8]; layout.cursor = offsets[9];
    layout.move_cursor = offsets[10]; layout.result = offsets[11]; layout.timer = offsets[12];
    layout.monster_size = offsets[13]; layout.moves = offsets[14];
    layout.pp = offsets[15]; layout.hp = offsets[16];
    layout.move_size = offsets[18]; layout.cat = offsets[19];
    layout.power = offsets[20]; layout.acc = offsets[21]; layout.effect = offsets[22];
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
    char buf[256], op[32]; int a, b, c, line_direction, dest, line = 0, started = 0;
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
            int still = 0, no_progress = 0, last_kind = -1;
            for (int i = 0; i < 30000 &&
                 (map() != a || x() != b || y() != c || mode() != 0 ||
                  rd32(dialog_addr) || rd32(warp_addr)); i++) {
                if (map() != a && mode() == 0) fail(line, "unexpected map; use explicit edge/door checkpoint");
                unsigned key = 0;
                if (x() < b) key = 1u << 4;
                else if (x() > b) key = 1u << 5;
                else if (y() < c) key = 1u << 7;
                else if (y() > c) key = 1u << 6;
                int old_map = map(), old_x = x(), old_y = y();
                step(line, key, &last_kind);
                if (old_map == map() && old_x == x() && old_y == y()) no_progress++;
                else no_progress = 0;
                if (mode() == 0 && !rd32(dialog_addr) && !rd32(warp_addr) &&
                    old_map == map() && old_x == x() && old_y == y()) still++;
                else still = 0;
                if (still > 600) fail(line, "field collision; checkpoint not navigable");
                if (no_progress > 12000) fail(line, "interaction/battle frame budget exceeded");
            }
            if (map() != a || x() != b || y() != c || mode() != 0 || rd32(dialog_addr) || rd32(warp_addr))
                fail(line, "waypoint frame budget exceeded");
            printf("WAY line=%d map=%d x=%d y=%d frames=%lu minutes=%.3f\n", line, map(), x(), y(), frames, frames / FRAMES_PER_MINUTE);
        } else if (!strcmp(op, "wild_limit") && sscanf(buf, "%*s %d", &a) == 1 && started && (a == 3 || a == 6)) {
            wild_limit = a;
            printf("WILD_LIMIT per_map=%d\n", a);
        } else if (!strcmp(op, "warden") && sscanf(buf, "%*s %d %d %d %d", &a, &b, &c, &line_direction) == 4 && started) {
            if (map() != a || x() != b || y() != c || mode() != 0)
                fail(line, "warden interaction starting checkpoint mismatch");
            int before = wardens, last_kind = -1;
            press(1u << line_direction); /* face NPC without crossing its tile */
            if (map() != a || x() != b || y() != c) fail(line, "warden not adjacent; facing step moved player");
            press(KEY_A);
            for (int i = 0; i < 12000 && wardens == before; i++)
                step(line, 0, &last_kind);
            if (wardens != before + 1 || map() != a)
                fail(line, "warden interaction did not yield a victory");
            printf("WARDEN line=%d map=%d x=%d y=%d frames=%lu\n", line, map(), x(), y(), frames);
        } else if (!strcmp(op, "door") && sscanf(buf, "%*s %d %d %d %d %d", &a, &b, &c, &line_direction, &dest) == 5 && started) {
            if (map() != a || x() != b || y() != c || mode() != 0 || rd32(dialog_addr) || rd32(warp_addr))
                fail(line, "door starting checkpoint mismatch");
            int last_kind = -1;
            for (int i = 0; i < 300 && map() == a; i++) step(line, 1u << line_direction, &last_kind);
            if (map() != dest) fail(line, "door did not reach expected map");
            for (int i = 0; i < 300 && (mode() != 0 || rd32(warp_addr)) && map() == dest; i++) step(line, 0, &last_kind);
            if (map() != dest || mode() != 0 || rd32(warp_addr)) fail(line, "door transition did not settle");
            wild_wins = wild_runs = 0;
            printf("DOOR line=%d map=%d x=%d y=%d frames=%lu\n", line, map(), x(), y(), frames);
        } else if (!strcmp(op, "edge") && sscanf(buf, "%*s %d %d %d", &a, &b, &c) == 3 && started) {
            if (map() != a) fail(line, "edge source map mismatch");
            int last_kind = -1;
            for (int i = 0; i < 3000 && map() == a; i++) step(line, 1u << b, &last_kind);
            if (map() != c) fail(line, "edge did not reach expected map");
            for (int i = 0; i < 300 && (mode() != 0 || rd32(warp_addr)) && map() == c; i++) step(line, 0, &last_kind);
            if (map() != c || mode() != 0 || rd32(warp_addr)) fail(line, "edge transition did not settle in expected map");
            wild_wins = wild_runs = 0;
            printf("EDGE line=%d map=%d x=%d y=%d frames=%lu\n", line, map(), x(), y(), frames);
        } else fail(line, "invalid command or order");
    }
    if (!started) fail(line, "missing start");
    if (mode() != 0 || rd32(dialog_addr) || rd32(warp_addr)) fail(line, "last checkpoint is not settled");
    printf("CHECKPOINTS_COMPLETE frames=%lu minutes=%.3f wardens=%d wild_wins=%d wild_runs=%d dialogs=%d (not an act total)\n", frames, frames / FRAMES_PER_MINUTE, wardens, wild_wins, wild_runs, dialogs);
    fclose(file); core->deinit(core); return 0;
}
