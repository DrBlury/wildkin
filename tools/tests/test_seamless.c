/* Edge-transition safety baseline. The one-map renderer cannot display both
 * sides of an edge yet, so these assertions protect the short-fade fallback. */
#include "harness.h"

static int edge_dir(int side)
{
    static const int dirs[] = { DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT };
    return dirs[side];
}

static int opposite(int side)
{
    static const int sides[] = { LINK_S, LINK_N, LINK_E, LINK_W };
    return sides[side];
}

static void edge_entry(int map, int side, int *x, int *y)
{
    const MapDef *m = &MAPS[map];
    *x = side == LINK_W ? 0 : side == LINK_E ? m->w - 1 : m->w / 2;
    *y = side == LINK_N ? 0 : side == LINK_S ? m->h - 1 : m->h / 2;
    /* Seek an actual opening, not merely a matching link in the graph. */
    map_load(map);
    int len = side < LINK_W ? m->w : m->h;
    for (int i = 0; i < len; i++) {
        int cx = side < LINK_W ? i : *x;
        int cy = side < LINK_W ? *y : i;
        if (cell_walkable(cx, cy)) { *x = cx; *y = cy; return; }
    }
    *x = -1;
}

static void finish_fade(void)
{
    for (int frame = 0; frame < 20 && warp.active; frame++) field_warp_update();
}

int main(void)
{
    fresh_game();
    give_starter();
    opt.autosave = 0;
    int source = -1, dest = -1, side = -1, x = -1, y = -1;
    for (int m = 0; m < MAP_COUNT && source < 0; m++)
        for (int s = 0; s < 4 && source < 0; s++) {
            int d = MAPS[m].link[s];
            if (d >= MAP_COUNT || MAPS[d].link[opposite(s)] != m ||
                !edge_palette_compatible(m, d) || MAPS[m].link_off[s] ||
                MAPS[d].link_off[opposite(s)]) continue;
            edge_entry(m, s, &x, &y);
            if (x < 0) continue;
            int dx = s < LINK_W ? x : (opposite(s) == LINK_W ? 0 : MAPS[d].w - 1);
            int dy = s < LINK_W ? (opposite(s) == LINK_N ? 0 : MAPS[d].h - 1) : y;
            map_load(d);
            if (!cell_walkable(dx, dy)) continue;
            source = m; dest = d; side = s;
        }
    CHECK(source >= 0, "a reciprocal palette-compatible edge has walkable landings");
    if (source < 0) return failures ? 1 : 0;

    map_load(source);
    int nx = x + DIR_DX[edge_dir(side)], ny = y + DIR_DY[edge_dir(side)];
    player.x = x; player.y = y;
    warp.active = 0;
    CHECK(try_edge_link(edge_dir(side), nx, ny) && warp.active &&
          warp.duration == 6 && cur_map == source,
          "compatible edge retains the six-frame fade until the midpoint");
    finish_fade();
    int landing_x = player.x, landing_y = player.y;
    CHECK(cur_map == dest && !warp.active && player.facing == edge_dir(side) &&
          landing_x >= 0 && landing_x < map_w && landing_y >= 0 && landing_y < map_h &&
          wild_spawn_timer == 30,
          "arrival loads the neighbour and resets its wild spawn timer");
    int npcs_loaded = 1;
    for (int i = 0; i < NPC_COUNT; i++)
        if (!!npc_visible[i] != (NPCS[i].map == dest && npc_condition(&NPCS[i])))
            npcs_loaded = 0;
    CHECK(npcs_loaded, "arrival refreshes only the destination's eligible NPCs");

    int back = opposite(side);
    nx = landing_x + DIR_DX[edge_dir(back)];
    ny = landing_y + DIR_DY[edge_dir(back)];
    warp.active = 0;
    CHECK(try_edge_link(edge_dir(back), nx, ny) && warp.active &&
          warp.duration == 6, "return edge retains the short fade");
    finish_fade();
    CHECK(cur_map == source && player.x == x && player.y == y && !warp.active,
          "two-way crossing returns to the exact departure cell");

    int mismatched = 0;
    for (int m = 0; m < MAP_COUNT && !mismatched; m++)
        for (int s = 0; s < 4 && !mismatched; s++) {
            int d = MAPS[m].link[s];
            if (d >= MAP_COUNT || edge_palette_compatible(m, d)) continue;
            map_load(m);
            int ex = s == LINK_W ? -1 : s == LINK_E ? map_w : 1;
            int ey = s == LINK_N ? -1 : s == LINK_S ? map_h : 1;
            warp.active = 0;
            if (try_edge_link(edge_dir(s), ex, ey))
                mismatched = warp.active && warp.duration == 9;
        }
    CHECK(mismatched, "incompatible edge preserves the full fade");
    return failures ? 1 : 0;
}
