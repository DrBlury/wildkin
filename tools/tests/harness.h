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

/* Cells reached, one bit per elevation level (elev.c); reached() is any. */
static u8 seen_cells[MAP_MAX_W * MAP_MAX_H];

/* Flood modes (OR them):
 *   FLOOD_SOLVED  every puzzle solved: gates and barriers open, boulders
 *                 pushed aside, teleport pads followed to their partner
 *   FLOOD_SURF    surfable water (A_WATER without A_DEEP) is open */
enum { FLOOD_WALK = 0, FLOOD_SOLVED = 1, FLOOD_SURF = 2 };

static int flood_open_lv(int x, int y, int mode, int level, int top)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h) return 0;
    if (npc_at_lv(x, y, level) >= 0) return 0;
    int k = npc_kin_at(x, y);
    if (k >= 0 && npc_kin[k].a.level == level) return 0;
    if (top) return 1;   /* a deck or tunnel top: the terrain below does not matter */
    if (item_ball_at(x, y) >= 0) return 0;
    int raw = cell_attr_raw(x, y);
    int a = (mode & FLOOD_SOLVED) ? travel_attr_solved(x, y, raw) : travel_attr(x, y, raw);
    if ((mode & FLOOD_SURF) && (a & A_WATER) && !(a & A_DEEP) && !travel_attr_solved(x, y, 0)) return 1;
    return !(a & (A_SOLID | A_LEDGE));
}

static int flood_open(int x, int y, int mode)
{
    return flood_open_lv(x, y, mode, elev_level_at(x, y, -1, -1), 0);
}

/* Flood fill over walkable cells (people and satchels count as walls).
 * The state is (x, y, level): cliffs, stairs, ledges and decks follow the
 * game's own rules (elev_enter). */
static void flood_ex_lv(int sx, int sy, int slevel, int mode)
{
    static int qx[MAP_MAX_W * MAP_MAX_H * 4], qy[MAP_MAX_W * MAP_MAX_H * 4];
    static u8 ql[MAP_MAX_W * MAP_MAX_H * 4];
    memset(seen_cells, 0, sizeof(seen_cells));
    if (!flood_open_lv(sx, sy, mode, slevel, slevel != elev_floor(sx, sy)) && !(cell_attr(sx, sy) & A_EXIT))
        return;
    int head = 0, tail = 0;
    qx[tail] = sx;
    qy[tail] = sy;
    ql[tail++] = (u8)slevel;
    seen_cells[sy * map_w + sx] = (u8)(1 << slevel);
    while (head < tail) {
        int x = qx[head], y = qy[head], l = ql[head++];
        int px, py;
        if ((mode & FLOOD_SOLVED) && travel_pad_partner(x, y, &px, &py) && !seen_cells[py * map_w + px]) {
            int pl = elev_level_at(px, py, l, -1);
            seen_cells[py * map_w + px] = (u8)(1 << pl);
            qx[tail] = px;
            qy[tail] = py;
            ql[tail++] = (u8)pl;
        }
        for (int d = 0; d < 4; d++) {
            int nx = x + DIR_DX[d], ny = y + DIR_DY[d], nl;
            int ek = elev_enter(x, y, l, d, &nl), top = ek == ELEV_TOP;
            /* ledges: one-way hop south (off a rise onto the ground below) */
            if (d == DIR_DOWN && nx >= 0 && ny >= 0 && nx < map_w && ny < map_h &&
                (cell_attr(nx, ny) & A_LEDGE) && (!map_elevated || l > elev_floor(nx, ny)) &&
                flood_open_lv(nx, ny + 1, mode, elev_floor(nx, ny + 1), 0)) {
                ny++;
                nl = elev_level_at(nx, ny, -1, d);
                ek = ELEV_FLOOR;
                top = 0;
            }
            if (ek == ELEV_BLOCK) continue;
            if (nx < 0 || ny < 0 || nx >= map_w || ny >= map_h) continue;
            if ((seen_cells[ny * map_w + nx] >> nl) & 1) continue;
            if (!flood_open_lv(nx, ny, mode, nl, top)) continue;
            seen_cells[ny * map_w + nx] |= (u8)(1 << nl);
            qx[tail] = nx;
            qy[tail] = ny;
            ql[tail++] = (u8)nl;
        }
    }
}

static void flood_ex(int sx, int sy, int mode)
{
    flood_ex_lv(sx, sy, elev_level_at(sx, sy, -1, -1), mode);
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

/* Reached on a given level (elevation). */
static int reached_lv(int x, int y, int level)
{
    return reached(x, y) && ((seen_cells[y * map_w + x] >> level) & 1);
}

static int reached_beside(int x, int y)
{
    for (int d = 0; d < 4; d++)
        if (reached(x + DIR_DX[d], y + DIR_DY[d])) return 1;
    return 0;
}

#endif
