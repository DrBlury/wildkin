#include "harness.h"

static int callback_value;
static void walked(int arg) { callback_value = arg; }
static int active_event(int event) { return event == 3; }

int main(void)
{
    fresh_game();
    give_starter();
    int id = -1, x = -1, y = -1;
    for (int i = 0; i < NPC_COUNT && id < 0; i++) {
        if (NPCS[i].map != cur_map || !npc_visible[i]) continue;
        for (int cy = 2; cy < map_h - 2 && id < 0; cy++)
            for (int cx = 2; cx < map_w - 2 && id < 0; cx++) {
                if (!cell_walkable(cx, cy) || !cell_walkable(cx + 1, cy) ||
                    !cell_walkable(cx + 1, cy + 1) || npc_at(cx + 1, cy) >= 0 ||
                    npc_at(cx + 1, cy + 1) >= 0 ||
                    (player.x >= cx && player.x <= cx + 1 && player.y >= cy && player.y <= cy + 1)) continue;
                id = i; x = cx; y = cy;
            }
    }
    CHECK(id >= 0, "cutscene fixture has a walkable L path");
    if (id >= 0) {
        npc_state[id].x = x;
        npc_state[id].y = y;
        npc_state[id].moving = 0;
        npc_state[id].level = (u8)elev_level_at(x, y, -1, -1);
        static const u8 path[] = { DIR_RIGHT, DIR_DOWN };
        callback_value = 0;
        npc_walk(id, path, 2, walked, 19);
        for (int i = 0; i < 75 && !callback_value; i++) script_cutscene_update();
        CHECK(callback_value == 19 && npc_state[id].x == x + 1 && npc_state[id].y == y + 1 &&
              npc_state[id].facing == DIR_DOWN, "NPC L-path reaches final cell and callback");
        npc_face(id, DIR_LEFT);
        CHECK(npc_state[id].facing == DIR_LEFT, "NPC facing changes");
        npc_warp_out(id);
        CHECK(!npc_visible[id] && npc_at(x + 1, y + 1) < 0, "warped NPC no longer blocks field");
        npcs_reset();
        CHECK(npc_visible[id], "NPC warp-out resets when map reloads");
    }
    field_update_camera();
    int before_x = cam_x, before_y = cam_y;
    callback_value = 0;
    cam_pan_to(map_w - 1, map_h - 1, 8, walked, 27);
    for (int i = 0; i < 8; i++) script_cutscene_update();
    CHECK(callback_value == 27 && cam_scripted, "camera pan completes while view stays pinned");
    cam_follow_player();
    CHECK(!cam_scripted && cam_x == before_x && cam_y == before_y, "camera follows player again");

    static const char *const heights[] = { "12" };
    static const MapPatch patch = { .flag = FLAG_STARTER, .x = 1, .w = 2, .h = 1,
                                    .y = 1, .elev = heights };
    MapDef map = { .w = 8, .h = 8, .patches = &patch, .patch_count = 1 };
    CHECK(map_patch_active(&patch) && map_patch_elev(&map, 2, 1, '0') == '2' &&
          map_patch_elev(&map, 3, 1, '0') == '0', "flag patch overrides only its rectangle");
    MapPatch event_patch = { .event = 3 };
    npc_event_active = active_event;
    CHECK(map_patch_active(&event_patch), "event patches use event provider");
    npc_event_active = 0;

    NpcDef conditional = { .map = cur_map, .show_flag = FLAG_STARTER,
                           .hide_flag = FLAG_STORM_CALMED, .when = WHEN_DAY };
    gtime.minute = 12 * 60;
    CHECK(npc_condition(&conditional), "flagged daytime NPC appears with its show flag");
    gtime.minute = 23 * 60;
    CHECK(!npc_condition(&conditional), "daytime NPC disappears at night");
    gtime.minute = 12 * 60;
    flag_set(FLAG_STORM_CALMED);
    CHECK(!npc_condition(&conditional), "hide flag takes precedence over show flag");
    int valid_patches = 1;
    for (int m = 0; m < MAP_COUNT; m++)
        for (int i = 0; i < MAPS[m].patch_count; i++) {
            const MapPatch *p = &MAPS[m].patches[i];
            if (!p->w || !p->h || p->x + p->w > MAPS[m].w || p->y + p->h > MAPS[m].h)
                valid_patches = 0;
            for (int j = 0; j < p->h; j++) {
                if (p->rows && (int)strlen(p->rows[j]) != p->w) valid_patches = 0;
                if (p->elev && (int)strlen(p->elev[j]) != p->w) valid_patches = 0;
            }
        }
    CHECK(valid_patches, "all map patches fit and have exact-width rows");
    const MapDef *base = &MAPS[cur_map];
    const TilesetDef *tiles = &TILESETS[base->tileset];
    char tile_row[] = { base->rows[2][2], 0 };
    const char *const replacement[] = { tile_row };
    MapPatch cell_patch = { .flag = FLAG_STARTER, .x = 3, .y = 3,
                            .w = 1, .h = 1, .rows = replacement };
    MapDef patched = *base;
    patched.patches = &cell_patch;
    patched.patch_count = 1;
    map_load(cur_map);
    map_cells[3 * map_w + 3] = 0xFFFF;
    map_apply_patches(&patched, tiles);
    CHECK(map_cells[3 * map_w + 3] == legend_pick(legend_for(tiles, tile_row[0]), 3, 3),
          "active patch decodes legend cells in its rectangle");
    cell_patch.invert = 1;
    map_cells[3 * map_w + 3] = 0xFFFF;
    map_apply_patches(&patched, tiles);
    CHECK(map_cells[3 * map_w + 3] == 0xFFFF, "inactive patch leaves cells untouched");

    map_load(cur_map);
    if (tobj_count) {
        int old_x = tobj[0].x, old_state = tobj[0].state;
        tobj[0].x++;
        tobj[0].state = 2;
        /* A synthetic patch count is not needed: reapply exits for empty maps.
         * Verify the terrain refresh helper itself preserves live puzzle state. */
        travel_patch_elevation_refresh();
        CHECK(tobj[0].x == old_x + 1 && tobj[0].state == 2,
              "patch height refresh preserves moved objects and switch state");
        tobj[0].x = old_x;
        tobj[0].state = old_state;
    }

    int npc_budget = 1;
    for (int m = 0; m < MAP_COUNT; m++)
        for (int night = 0; night <= 1; night++) {
            int count = 0;
            for (int i = 0; i < NPC_COUNT; i++)
                if (NPCS[i].map == m && (NPCS[i].when == WHEN_ANY ||
                    (NPCS[i].when == WHEN_NIGHT) == night)) count++;
            if (count > 24) { printf("NPC budget: %s has %d in time window %d\n", MAPS[m].name, count, night); npc_budget = 0; }
        }
    CHECK(npc_budget, "24 NPCs per map per time window maximum");

    int same_edge = 0;
    static const int edge_dir[] = { DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT };
    for (int m = 0; m < MAP_COUNT && !same_edge; m++)
        for (int l = 0; l < 4 && !same_edge; l++) {
            int dest = MAPS[m].link[l];
            if (dest >= MAP_COUNT || MAPS[m].tileset != MAPS[dest].tileset) continue;
            map_load(m);
            int nx = l == LINK_W ? -1 : l == LINK_E ? map_w : 1;
            int ny = l == LINK_N ? -1 : l == LINK_S ? map_h : 1;
            if (try_edge_link(edge_dir[l], nx, ny)) {
                same_edge = warp.active && warp.duration == 6;
                warp.active = 0;
            }
        }
    CHECK(same_edge, "matching-tileset edge transition uses six-frame dip");
    quest_reset();
    quest_advance_to(1, 2);
    quest_advance_to(1, 1);
    CHECK(quest_is(1, 2) && quest_between(1, 1, 3) && sizeof(quest) <= MOD_QUEST_MAX,
          "quest advance is monotone and expanded save state fits");
    time_reset();
    gtime.day = 7;
    u32 seed = time_day_seed();
    time_roll_weather();
    int weather = gtime.weather;
    gtime.weather = WEATHER_CLEAR;
    time_roll_weather();
    CHECK(time_day_seed() == seed && weather == gtime.weather,
          "same save and day reproduce the same weather");
    CHECK(sizeof(gtime) <= MOD_TIME_MAX, "appended day seed fits time save module");
    return failures ? 1 : 0;
}
