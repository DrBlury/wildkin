#include "harness.h"

static void unlock_world(void)
{
    fresh_game();
    give_starter();
    memset(story_bits, 255, sizeof story_bits);
    travel.crests = 63;
    opt.follower = 0;
}

static int portal_approach(const Warp *w)
{
    for (int d = 0; d < 4; d++) {
        int x = w->x - DIR_DX[d], y = w->y - DIR_DY[d];
        if (!cell_walkable(x, y) || (cell_attr(x, y) & (A_DOOR | A_EXIT | A_ICE | A_CURRENT))) continue;
        player.x = (s16)x;
        player.y = (s16)y;
        player.level = (u8)elev_level_at(x, y, -1, d);
        int nl;
        if (elev_enter(x, y, player.level, d, &nl) == ELEV_BLOCK) continue;
        player.facing = (u8)d;
        return d;
    }
    return -1;
}

static void test_portal_contract(void)
{
    unlock_world();
    Warp invalid = { .required_flag = FLAG_COUNT };
    CHECK(!warp_is_open(&invalid), "invalid portal flags fail closed without reading past flag storage");
    invalid.required_flag = 0;
    CHECK(warp_is_open(&invalid), "legacy zero-initialized portal flags remain open");
    int tested = 0, all_safe = 1;
    for (int i = 0; i < WARP_COUNT; i++) {
        const Warp *w = &WARPS[i];
        if (!w->required_flag) continue;
        unlock_world();
        field_enter_map(w->map, 0, 0, DIR_DOWN);
        int d = portal_approach(w);
        if (d < 0 || !(cell_attr(w->x, w->y) & A_DOOR)) {
            printf("portal lacks reachable door approach: %s (%d,%d)\n", MAPS[w->map].name, w->x, w->y);
            all_safe = 0;
            continue;
        }
        int x = player.x, y = player.y;
        bit_clear(story_bits, w->required_flag);
        warp.active = 0;
        player_try_move(d);
        if (warp.active || player.x != x || player.y != y) all_safe = 0;
        if (!field_try_interact() || !dialog_active()) all_safe = 0;
        dialog_clear();
        bit_set(story_bits, w->required_flag);
        player_try_move(d);
        if (!warp.active || warp.dest != w->dest || warp.x != w->dx || warp.y != w->dy) all_safe = 0;
        warp.active = 0;
        tested++;
    }
    printf("%d guarded portals exercised through real movement\n", tested);
    CHECK(tested > 0 && all_safe, "all guarded doors reject missing flags, explain locks, and warp only when open");
}

static void test_atlas(void)
{
    unlock_world();
    int cave = -1, cave_count = 0, metadata_ok = 1;
    for (int m = 0; m < MAP_COUNT; m++) {
        if (!MAPS[m].depth) continue;
        cave = m;
        cave_count++;
        if (MAPS[m].surface_map >= MAP_COUNT || MAPS[MAPS[m].surface_map].depth ||
            !(MAPS[m].flags & MF_NOFLY) || map_spot(m) < 0) {
            printf("invalid cave metadata: %s anchor=%d flags=%u spot=%d\n", MAPS[m].name,
                   MAPS[m].surface_map, MAPS[m].flags, map_spot(m));
            metadata_ok = 0;
        }
    }
    CHECK(cave_count >= 5 && metadata_ok, "underground maps have explicit surface anchors, atlas positions and no flight");
    field_enter_map(MAP_TOWN, 23, 17, DIR_DOWN);
    memset(travel.visited, 0, sizeof travel.visited);
    memset(travel.visited_hi, 0, sizeof travel.visited_hi);
    worldmap_open(0);
    tap(KEY_L);
    CHECK(wm.underground && uw.count == 0, "unexplored caves stay hidden and the atlas has an empty state");
    tap(KEY_B);
    if (cave < 0) return;
    int spawn = -1;
    for (int i = 0; i < WARP_COUNT; i++) if (WARPS[i].dest == cave) { spawn = i; break; }
    CHECK(spawn >= 0, "the sampled cave has an authored entrance");
    if (spawn < 0) return;
    field_enter_map(cave, WARPS[spawn].dx, WARPS[spawn].dy, DIR_DOWN);
    Actor before = player;
    u16 cells[MAP_MAX_W * MAP_MAX_H];
    memcpy(cells, map_cells, sizeof cells);
    worldmap_open(0);
    CHECK(wm.underground && uw.count == 1 && uw.maps[uw.current] == cave,
          "entering a cave charts it and opens the atlas at the current depth");
    CHECK(uw.exit_count > 0 && !memcmp(cells, map_cells, sizeof cells) &&
          cur_map == cave && !memcmp(&before, &player, sizeof before),
          "drawing cave connections does not load a map or move the player");
    tap(KEY_R);
    CHECK(!wm.underground && wm.here == map_spot(MAPS[cave].surface_map),
          "surface toggle pins the cave to its authored region");
    tap(KEY_L);
    CHECK(wm.underground, "layer toggle returns to the underground diagram");
    tap(KEY_B);
    CHECK(game_mode == MODE_FIELD && cur_map == cave && !field_tiles_failed,
          "closing the atlas restores the cave field graphics");
    worldmap_open(1);
    tap(KEY_L);
    CHECK(!wm.underground && wm.fly, "FLY never offers an underground layer or destination");
    tap(KEY_B);
}

int main(void)
{
    test_portal_contract();
    test_atlas();
    return failures ? 1 : 0;
}
