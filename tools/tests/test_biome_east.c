/* East biome integration: run once all east/biomes snippets are registered. */
#include "harness.h"

static const Warp *portal(int from, int x, int y, int to)
{
    for (int i = 0; i < WARP_COUNT; ++i)
        if (WARPS[i].map == from && WARPS[i].x == x && WARPS[i].y == y && WARPS[i].dest == to)
            return &WARPS[i];
    return 0;
}

static void route(int from, int x, int y, int to, int back_x, int back_y, int gate)
{
    const Warp *out = portal(from, x, y, to);
    const Warp *back = portal(to, back_x, back_y, from);
    CHECK(out != 0, "biome portal has an authored entrance");
    if (!out) return;
    if (!back && (MAPS[to].flags & MF_HEAL)) {
        map_load(to);
        CHECK((cell_attr(back_x, back_y) & A_EXIT) && out->required_flag == gate,
              "single-room village interior returns through its gated entrance using an exit mat");
        return;
    }
    CHECK(back != 0, "outdoor biome portal has reciprocal endpoint");
    if (!back) return;
    CHECK(out->required_flag == gate && back->required_flag == gate, "portal gates agree");
    map_load(to);
    CHECK(!(cell_attr(out->dx, out->dy) & (A_SOLID | A_WATER | A_DOOR)), "outbound landing is safe");
    map_load(from);
    CHECK(!(cell_attr(back->dx, back->dy) & (A_SOLID | A_WATER | A_DOOR)), "return landing is safe");
}

static void dimensions(int map)
{
    const MapDef *def = &MAPS[map];
    CHECK(def->w <= 64 && def->h <= 64 && def->obj_count <= 48 && def->decor_count < 128,
          "biome map respects dimensions and placement caps");
    for (int y = 0; y < def->h; ++y)
        CHECK((int)strlen(def->rows[y]) == def->w, "biome terrain row has declared width");
}

static void hidden_waterfall_shelf(void)
{
    fresh_game();
    give_starter();
    hush_steps = 2000;
    field_enter_map(MAP_MISTFALL_GORGE, 16, 8, DIR_UP);
    CHECK(player.level == 1 && !elev_found(16, 7), "spray shelf begins concealed above the overlook");
    for (int i = 0; i < 3; i++) {
        player_try_move(DIR_UP);
        settle();
    }
    CHECK(player.x == 16 && player.y == 5 && elev_found(16, 7),
          "real movement discovers the rock gap behind the waterfall");
    for (int i = 0; i < 3; i++) {
        player_try_move(DIR_RIGHT);
        settle();
    }
    int before = bag[ITEM_GLOW_LANTERN];
    tap(KEY_A);
    run_dialog(150);
    CHECK(player.x == 19 && player.y == 5 && bag[ITEM_GLOW_LANTERN] == before + 1,
          "the concealed waterfall passage leads to its collectible reward");
    static SaveData saved;
    save_capture(&saved);
    fresh_game();
    save_apply(&saved);
    CHECK(elev_found(16, 7) && elev_found(18, 5) && bag[ITEM_GLOW_LANTERN] == before + 1,
          "waterfall discovery and collected reward survive save restoration");
}

static void quest_full_bag(int jungle)
{
    fresh_game();
    int item = jungle ? ITEM_GLOWCAP : ITEM_IRON_ORE;
    int cost = jungle ? 3 : 2;
    int reward = jungle ? ITEM_REVIVAL_BREW : ITEM_BIG_TONIC;
    int flag_id = jungle ? FLAG_CANOPY_MARKER : FLAG_MISTBELL_BELL;
    bag[item] = cost;
    bag[reward] = 999;
    if (jungle) canopy_restore_answer(0); else mistbell_repair_answer(0);
    CHECK(!flag(flag_id) && bag[item] == cost && bag[reward] == 999,
          "full reward stack preserves repair supplies and unfinished quest");
    dialog_clear();
}

static void quest_lifecycle(int jungle)
{
    fresh_game();
    int item = jungle ? ITEM_GLOWCAP : ITEM_IRON_ORE;
    int cost = jungle ? 3 : 2;
    int reward = jungle ? ITEM_REVIVAL_BREW : ITEM_BIG_TONIC;
    int amount = jungle ? 1 : 2;
    int quest_id = jungle ? QUEST_CANOPY_MARKER : QUEST_MISTBELL_BELL;
    int flag_id = jungle ? FLAG_CANOPY_MARKER : FLAG_MISTBELL_BELL;
    int start = bag[item], bonus = bag[reward];
    if (jungle) scr_canopy_marker(0); else scr_mistbell_bell(0);
    CHECK(quest_get(quest_id) == 1 && !flag(flag_id), "repair quest starts without unlocking shortcut");
    if (jungle) canopy_restore_answer(1); else mistbell_repair_answer(1);
    CHECK(bag[item] == start && bag[reward] == bonus && !flag(flag_id),
          "cancel keeps materials, reward and gate unchanged");
    dialog_clear();
    if (jungle) canopy_restore_answer(0); else mistbell_repair_answer(0);
    CHECK(bag[item] == start && !flag(flag_id), "missing resources do not unlock or charge");
    dialog_clear();
    bag_add(item, cost);
    if (jungle) canopy_restore_answer(0); else mistbell_repair_answer(0);
    CHECK(bag[item] == start && bag[reward] == bonus + amount && flag(flag_id) &&
          quest_done(quest_id), "confirmed repair charges once, rewards once, opens path");
    dialog_clear();
    if (jungle) canopy_restore_answer(0); else mistbell_repair_answer(0);
    CHECK(bag[item] == start && bag[reward] == bonus + amount,
          "repeat callback cannot duplicate reward or consume resources");
    static u8 sram[32768];
    memset(sram, 0xFF, sizeof(sram));
    dialog_clear();
    CHECK(save_write_to(sram), "completed repair save writes");
    new_game();
    CHECK(save_load_from(sram) == SAVE_VERSION && flag(flag_id) && quest_done(quest_id) &&
          bag[reward] == bonus + amount, "repair gate, quest and reward survive reload");
    if (jungle) canopy_restore_answer(0); else mistbell_repair_answer(0);
    CHECK(bag[reward] == bonus + amount, "reloaded quest remains one-time");
    dialog_clear();
}

static void enter_portal(int from, int x, int y, int facing, int to, int dx, int dy)
{
    game_mode = MODE_FIELD;
    dialog_clear();
    field_enter_map(from, x, y, facing);
    warp.active = 0;
    set_brightness(0);
    step(0);
    int triggered = player_try_move(facing);
    for (int i = 0; i < 50 && warp.active; ++i) step(0);
    CHECK(triggered && !warp.active && cur_map == to && player.x == dx && player.y == dy,
          "walking into a biome portal reaches its destination");
    dialog_clear();
}

static void leave_interior(int interior, int village)
{
    game_mode = MODE_FIELD;
    dialog_clear();
    field_enter_map(interior, 5, 7, DIR_DOWN);
    warp.active = 0;
    set_brightness(0);
    step(0);
    int stepped = player_try_move(DIR_DOWN);
    for (int i = 0; i < 30 && player.moving; ++i) step(0);
    CHECK(stepped && player.x == 5 && player.y == 8 && (cell_attr(5, 8) & A_EXIT),
          "interior exit mat is reachable from its arrival");
    int triggered = player_try_move(DIR_DOWN);
    for (int i = 0; i < 50 && warp.active; ++i) step(0);
    CHECK(triggered && !warp.active && cur_map == village && player.x == 16 && player.y == 6,
          "walking south from exit mat returns to the village");
    dialog_clear();
}

static void shortcut_movement(int village, int route_map, int gate)
{
    fresh_game();
    field_enter_map(village, 22, 18, DIR_RIGHT);
    warp.active = 0;
    dialog_clear();
    CHECK(!player_try_move(DIR_RIGHT) && !warp.active && cur_map == village,
          "unrepaired shortcut refuses movement");
    flag_set(gate);
    enter_portal(village, 22, 18, DIR_RIGHT, route_map, 28, 24);
    enter_portal(route_map, 28, 24, DIR_LEFT, village, 24, 18);
}

int main(void)
{
    fresh_game();
    const int biome_maps[] = { MAP_MISTFALL_GORGE, MAP_MISTBELL, MAP_MISTBELL_BELLHOUSE,
        MAP_ROOTCOIL_JUNGLE, MAP_CANOPY_HEARTH, MAP_CANOPY_LODGE };
    for (unsigned i = 0; i < sizeof(biome_maps) / sizeof(biome_maps[0]); ++i)
        dimensions(biome_maps[i]);
    route(MAP_BROOKMILL, 12, 30, MAP_MISTFALL_GORGE, 2, 14, 0);
    route(MAP_MISTFALL_GORGE, 32, 14, MAP_MISTBELL, 2, 13, 0);
    route(MAP_MISTBELL, 16, 5, MAP_MISTBELL_BELLHOUSE, 5, 8, 0);
    route(MAP_ELDERWOOD, 20, 20, MAP_ROOTCOIL_JUNGLE, 2, 14, 0);
    route(MAP_ROOTCOIL_JUNGLE, 32, 14, MAP_CANOPY_HEARTH, 2, 13, 0);
    route(MAP_CANOPY_HEARTH, 16, 5, MAP_CANOPY_LODGE, 5, 8, 0);
    route(MAP_MISTBELL, 23, 18, MAP_MISTFALL_GORGE, 27, 24, FLAG_MISTBELL_BELL);
    route(MAP_CANOPY_HEARTH, 23, 18, MAP_ROOTCOIL_JUNGLE, 27, 24, FLAG_CANOPY_MARKER);
    map_load(MAP_MISTFALL_GORGE);
    flood_ex(3, 14, FLOOD_SOLVED);
    CHECK(reached_beside(32, 14) && reached_beside(2, 14), "gorge traverses to village and returns");
    CHECK(MAPS[MAP_MISTFALL_GORGE].feat_count &&
          MAPS[MAP_MISTFALL_GORGE].feats[0].kind == EF_BRIDGE_H &&
          MAPS[MAP_MISTFALL_GORGE].rows[14][18] == '~',
          "gorge bridge is a raised deck over actual waterfall water");
    map_load(MAP_ROOTCOIL_JUNGLE);
    flood_ex(3, 14, FLOOD_SOLVED);
    CHECK(reached_beside(32, 14) && reached_beside(2, 14), "jungle traverses to village and returns");
    CHECK(MAPS[MAP_ROOTCOIL_JUNGLE].feat_count &&
          MAPS[MAP_ROOTCOIL_JUNGLE].feats[0].kind == EF_BRIDGE_H &&
          MAPS[MAP_ROOTCOIL_JUNGLE].rows[14][18] == '~',
          "canopy bridge crosses river water");
    enter_portal(MAP_MISTFALL_GORGE, 31, 14, DIR_RIGHT, MAP_MISTBELL, 3, 13);
    enter_portal(MAP_MISTBELL, 3, 13, DIR_LEFT, MAP_MISTFALL_GORGE, 31, 14);
    enter_portal(MAP_MISTBELL, 16, 6, DIR_UP, MAP_MISTBELL_BELLHOUSE, 5, 7);
    leave_interior(MAP_MISTBELL_BELLHOUSE, MAP_MISTBELL);
    enter_portal(MAP_ROOTCOIL_JUNGLE, 31, 14, DIR_RIGHT, MAP_CANOPY_HEARTH, 3, 13);
    enter_portal(MAP_CANOPY_HEARTH, 3, 13, DIR_LEFT, MAP_ROOTCOIL_JUNGLE, 31, 14);
    enter_portal(MAP_CANOPY_HEARTH, 16, 6, DIR_UP, MAP_CANOPY_LODGE, 5, 7);
    leave_interior(MAP_CANOPY_LODGE, MAP_CANOPY_HEARTH);
    shortcut_movement(MAP_MISTBELL, MAP_MISTFALL_GORGE, FLAG_MISTBELL_BELL);
    shortcut_movement(MAP_CANOPY_HEARTH, MAP_ROOTCOIL_JUNGLE, FLAG_CANOPY_MARKER);
    fresh_game();
    CHECK(!flag(FLAG_MISTBELL_BELL) && !flag(FLAG_CANOPY_MARKER), "shortcuts start closed");
    hidden_waterfall_shelf();
    quest_full_bag(0);
    quest_full_bag(1);
    quest_lifecycle(0);
    quest_lifecycle(1);
    flag_set(FLAG_MISTBELL_BELL);
    flag_set(FLAG_CANOPY_MARKER);
    CHECK(warp_is_open(portal(MAP_MISTBELL, 23, 18, MAP_MISTFALL_GORGE)) &&
          warp_is_open(portal(MAP_CANOPY_HEARTH, 23, 18, MAP_ROOTCOIL_JUNGLE)),
          "both persistent shortcut flags open their warps");
    printf("east biomes: %d failure(s)\n", failures);
    return failures ? 1 : 0;
}
