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

/* Flood fill over walkable cells (people and satchels count as walls). */
static void flood(int sx, int sy)
{
    static int qx[MAP_MAX_W * MAP_MAX_H], qy[MAP_MAX_W * MAP_MAX_H];
    memset(seen_cells, 0, sizeof(seen_cells));
    if (!cell_walkable(sx, sy) && !(cell_attr(sx, sy) & A_EXIT)) return;
    int head = 0, tail = 0;
    qx[tail] = sx;
    qy[tail++] = sy;
    seen_cells[sy * map_w + sx] = 1;
    while (head < tail) {
        int x = qx[head], y = qy[head++];
        for (int d = 0; d < 4; d++) {
            int nx = x + DIR_DX[d], ny = y + DIR_DY[d];
            /* ledges: one-way hop south */
            if (d == DIR_DOWN && nx >= 0 && ny >= 0 && nx < map_w && ny < map_h &&
                (cell_attr(nx, ny) & A_LEDGE) && cell_walkable(nx, ny + 1))
                ny++;
            if (nx < 0 || ny < 0 || nx >= map_w || ny >= map_h) continue;
            if (seen_cells[ny * map_w + nx] || !cell_walkable(nx, ny)) continue;
            seen_cells[ny * map_w + nx] = 1;
            qx[tail] = nx;
            qy[tail++] = ny;
        }
    }
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
