/*
 * Shared helpers for the host test programs (tools/test_*.c and
 * tools/tests/test_*.c): include the whole game, drive frames and keys,
 * flood-fill walkable cells. Every test file defines its own main().
 */
#ifndef TEST_HARNESS_H
#define TEST_HARNESS_H
#define main gba_main
#include "../../src/main.c"
#undef main

#include <stdio.h>
#include <string.h>

static int failures = 0;

#define CHECK(cond, msg)                                                    \
    do {                                                                    \
        if (cond) {                                                         \
            printf("ok: %s\n", (msg));                                      \
        } else {                                                            \
            printf("FAIL: %s\n", (msg));                                    \
            failures++;                                                     \
        }                                                                   \
    } while (0)

static void step(u16 keys)
{
    keys_prev = keys_now;
    keys_now = keys;
    game_frame();
}

static void tap(u16 keys)
{
    if (keys_now) step(0); /* a press only counts after a release */
    step(keys);
    step(0);
}

static void hold(u16 keys, int frames)
{
    while (frames--) step(keys);
    step(0);
}

static void settle(void)
{
    for (int f = 0; f < 60 && (player.moving || warp.active); f++) step(0);
}

static void run_dialog(int limit)
{
    for (int f = 0; f < limit && (dialog_active() || game_mode == MODE_SHOP); f++)
        step((f & 3) == 0 ? KEY_A : 0);
}

static void fresh_game(void)
{
    new_game();
    dialog_clear();
    canvas_clear();
    game_mode = MODE_FIELD;
    opt.follower = 1;
}

static void give_starter(void)
{
    Monster m = monster_make(SP_FLARIX, 8);
    give_monster(&m);
    flag_set(FLAG_STARTER);
    follower_reset();
}

/* ---------------- maps ---------------- */

static u8 seen_cells[MAP_MAX_W * MAP_MAX_H];

/* Flood modes (OR them):
 *   FLOOD_SOLVED  every puzzle solved: gates and barriers open, boulders
 *                 pushed aside, teleport pads followed to their partner.
 *                 An optimistic shortcut for quick local checks only: it
 *                 proves nothing about whether a puzzle can be solved.
 *                 tools/tests/test_puzzles.c searches the real game state
 *                 (pushes, slides, switches, pads) for that.
 *   FLOOD_SURF    surfable water (A_WATER without A_DEEP) is open */
enum { FLOOD_WALK = 0, FLOOD_SOLVED = 1, FLOOD_SURF = 2 };

static int flood_open(int x, int y, int mode)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h) return 0;
    if (npc_at(x, y) >= 0 || npc_kin_at(x, y) >= 0 || item_ball_at(x, y) >= 0) return 0;
    int raw = cell_attr_raw(x, y);
    int a = (mode & FLOOD_SOLVED) ? travel_attr_solved(x, y, raw) : travel_attr(x, y, raw);
    if ((mode & FLOOD_SURF) && (a & A_WATER) && !(a & A_DEEP) && !travel_attr_solved(x, y, 0)) return 1;
    return !(a & (A_SOLID | A_LEDGE));
}

/* Flood fill over walkable cells (people and satchels count as walls). */
static void flood_ex(int sx, int sy, int mode)
{
    static int qx[MAP_MAX_W * MAP_MAX_H], qy[MAP_MAX_W * MAP_MAX_H];
    memset(seen_cells, 0, sizeof(seen_cells));
    if (!flood_open(sx, sy, mode) && !(cell_attr(sx, sy) & A_EXIT)) return;
    int head = 0, tail = 0;
    qx[tail] = sx;
    qy[tail++] = sy;
    seen_cells[sy * map_w + sx] = 1;
    while (head < tail) {
        int x = qx[head], y = qy[head++];
        int px, py;
        if ((mode & FLOOD_SOLVED) && travel_pad_partner(x, y, &px, &py) && !seen_cells[py * map_w + px]) {
            seen_cells[py * map_w + px] = 1;
            qx[tail] = px;
            qy[tail++] = py;
        }
        for (int d = 0; d < 4; d++) {
            int nx = x + DIR_DX[d], ny = y + DIR_DY[d];
            /* ledges: one-way hop south */
            if (d == DIR_DOWN && nx >= 0 && ny >= 0 && nx < map_w && ny < map_h &&
                (cell_attr(nx, ny) & A_LEDGE) && flood_open(nx, ny + 1, mode))
                ny++;
            if (nx < 0 || ny < 0 || nx >= map_w || ny >= map_h) continue;
            if (seen_cells[ny * map_w + nx] || !flood_open(nx, ny, mode)) continue;
            seen_cells[ny * map_w + nx] = 1;
            qx[tail] = nx;
            qy[tail++] = ny;
        }
    }
}

/* Walk-only flood, as the map is right now. */
static void flood(int sx, int sy)
{
    flood_ex(sx, sy, FLOOD_WALK);
}

static int reached(int x, int y)
{
    return x >= 0 && y >= 0 && x < map_w && y < map_h && seen_cells[y * map_w + x];
}

static int reached_beside(int x, int y)
{
    for (int d = 0; d < 4; d++)
        if (reached(x + DIR_DX[d], y + DIR_DY[d])) return 1;
    return 0;
}

#endif
