/*
 * Traversal checks (src/game/travel.c) on the TEST maps in
 * src/game/world/travel/: map objects and their attributes, pumice and
 * STRENGTH boulders, plates and gates, switches and barriers, teleport
 * pads, currents, ice, surfing and water kin, the bike, ferries and the
 * voyage, the town map and FLY, the crest case, the FIELD menu, chests,
 * legends, dark maps, the reachability flood modes and the save.
 */
#include "harness.h"

static const u16 DIR_KEY[4] = { KEY_DOWN, KEY_UP, KEY_LEFT, KEY_RIGHT };

static void wait_still(void)
{
    for (int f = 0; f < 400 && (player.moving || warp.active || tv.busy); f++) step(0);
}

/* One step (or push, or slide) in `dir`, then wait until everything stops. */
static void go(int dir)
{
    player.facing = (u8)dir;
    player_turn_timer = 0;
    for (int f = 0; f < 4 && !player.moving; f++) step(DIR_KEY[dir]);
    wait_still();
}

static void enter(int map, int x, int y, int dir)
{
    game_mode = MODE_FIELD;
    dialog_clear();
    field_enter_map(map, x, y, dir);
    warp.active = 0;
    set_brightness(0);
    step(0);
}

static int obj_kind_at(int x, int y)
{
    int i = obj_index_at(x, y);
    return i >= 0 ? tobj[i].kind : -1;
}

static int find_obj(int kind, int x, int y)
{
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].kind == kind && tobj[i].x == x && tobj[i].y == y) return i;
    return -1;
}

static void give(int sp, int level)
{
    Monster m = monster_make(sp, level);
    give_monster(&m);
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    fresh_game();
    give_starter();
    opt.follower = 1;

    /* ---- world data sanity ---- */
    int objs_ok = 1, pads_ok = 1, ferry_ok = 1;
    for (int m = 0; m < MAP_COUNT; m++) {
        const MapDef *d = &MAPS[m];
        for (int i = 0; i < d->obj_count; i++) {
            const MapObj *o = &d->objs[i];
            if (o->kind == OBJ_NONE || o->kind >= OBJ_KIND_COUNT || o->x >= d->w || o->y >= d->h) {
                objs_ok = 0;
                printf("  %s: object %d is broken\n", d->name, i);
            }
            if (o->kind == OBJ_PAD) {
                int partners = 0;
                for (int k = 0; k < d->obj_count; k++)
                    if (k != i && d->objs[k].kind == OBJ_PAD && d->objs[k].arg == o->arg) partners++;
                if (partners != 1) {
                    pads_ok = 0;
                    printf("  %s: pad at %d,%d has %d partners\n", d->name, o->x, o->y, partners);
                }
            }
            if (o->kind == OBJ_FERRY) {
                int back = 0;
                if (o->arg < MAP_COUNT)
                    for (int k = 0; k < MAPS[o->arg].obj_count; k++)
                        if (MAPS[o->arg].objs[k].kind == OBJ_FERRY && MAPS[o->arg].objs[k].arg == m) back = 1;
                if (!back) {
                    ferry_ok = 0;
                    printf("  %s: ferry at %d,%d has no ferry back\n", d->name, o->x, o->y);
                }
            }
            if (o->kind == OBJ_LADDER && warp_at(m, o->x, o->y) < 0) {
                objs_ok = 0;
                printf("  %s: ladder at %d,%d has no warp\n", d->name, o->x, o->y);
            }
            if (o->kind == OBJ_LEGEND && o->arg >= SP_COUNT) objs_ok = 0;
        }
    }
    CHECK(objs_ok, "every map object is a known kind, inside its map (ladders have warps)");
    CHECK(pads_ok, "every teleport pad has exactly one partner");
    CHECK(ferry_ok, "every ferry has a ferry back on its destination map");
    CHECK(travel_pbit_total() <= 128, "gates, chests and legends fit the 128 puzzle bits");
    CHECK(sizeof(TravelState) == 41, "the travel save blob keeps its size");

    /* ---- attributes ---- */
    enter(MAP_TT_HALL, 9, 14, DIR_UP);
    CHECK((cell_attr(3, 9) & A_SOLID) && (cell_attr(4, 6) & A_SOLID) && (cell_attr(14, 6) & A_SOLID),
          "boulders, shut gates and raised barriers are solid");
    CHECK(!(cell_attr(6, 11) & A_SOLID) && (cell_attr(16, 9) & A_SWITCH) && (cell_attr(17, 12) & A_PAD),
          "plates, switches and pads are floor");
    CHECK((cell_attr(2, 3) & A_SOLID), "chests are solid");
    {
        flood_ex(9, 14, FLOOD_WALK);
        int walk_a = reached(2, 4), walk_b = reached(18, 3);
        flood_ex(9, 14, FLOOD_SOLVED);
        CHECK(!walk_a && !walk_b && reached(2, 4) && reached(18, 3),
              "the flood reaches the rooms behind the gate and the barrier only with puzzles solved");
    }

    /* ---- pumice boulder onto the plate opens the gate ---- */
    enter(MAP_TT_HALL, 6, 8, DIR_DOWN);
    go(DIR_DOWN);
    CHECK(obj_kind_at(6, 10) == OBJ_BOULDER && player.y == 9, "a pumice boulder is pushed without STRENGTH");
    go(DIR_DOWN);
    for (int f = 0; f < 40; f++) step(0);
    int gate = find_obj(OBJ_GATE, 4, 6);
    CHECK(obj_kind_at(6, 11) == OBJ_BOULDER && tobj[find_obj(OBJ_PLATE, 6, 11)].state == 1 && tobj[gate].state == 2 &&
              !(cell_attr(4, 6) & A_SOLID),
          "a boulder on the plate opens the gate");
    enter(MAP_TT_HALL, 9, 14, DIR_UP);
    CHECK(obj_kind_at(6, 9) == OBJ_BOULDER && !(cell_attr(4, 6) & A_SOLID),
          "boulders reset when the map reloads, the solved gate stays open");

    /* ---- a normal boulder needs STRENGTH ---- */
    enter(MAP_TT_HALL, 3, 8, DIR_DOWN);
    go(DIR_DOWN);
    CHECK(obj_kind_at(3, 9) == OBJ_BOULDER && player.y == 8, "a heavy boulder won't move without STRENGTH");
    travel_award_crest(CREST_ANVIL);
    give(SP_BOULDRON, 25);
    CHECK(travel_ability_kin(AB_STRENGTH) >= 0, "the ANVIL crest and a STRENGTH kin allow STRENGTH");
    CHECK(obj_interact(3, 9) && dialog_active(), "examining the boulder offers STRENGTH");
    run_dialog(400);
    CHECK(tv.strength_on, "STRENGTH is on after saying yes");
    go(DIR_DOWN);
    CHECK(obj_kind_at(3, 10) == OBJ_BOULDER && player.y == 9, "then the boulder moves");
    go(DIR_DOWN);
    go(DIR_DOWN);
    CHECK(obj_kind_at(3, 12) == OBJ_BOULDER, "and keeps moving");

    /* ---- switch and barrier ---- */
    enter(MAP_TT_HALL, 16, 8, DIR_DOWN);
    go(DIR_DOWN);
    CHECK(sw_on[1] && !(cell_attr(14, 6) & A_SOLID), "stepping on a switch drops its barrier");
    go(DIR_UP);
    go(DIR_DOWN);
    CHECK(!sw_on[1] && (cell_attr(14, 6) & A_SOLID), "stepping on it again raises the barrier");

    /* ---- teleport pads ---- */
    enter(MAP_TT_HALL, 17, 11, DIR_DOWN);
    go(DIR_DOWN);
    CHECK(player.x == 17 && player.y == 3, "a teleport pad sends you to its partner");
    go(DIR_DOWN);
    go(DIR_UP);
    CHECK(player.x == 17 && player.y == 12, "and back again");

    /* ---- currents ---- */
    enter(MAP_TT_HALL, 3, 13, DIR_RIGHT);
    go(DIR_RIGHT);
    CHECK(player.x == 8 && player.y == 13, "a current carries you to its end");

    /* ---- chests ---- */
    enter(MAP_TT_HALL, 2, 4, DIR_UP);
    int tonics = bag[ITEM_BIG_TONIC];
    tap(KEY_A);
    run_dialog(600);
    CHECK(bag[ITEM_BIG_TONIC] == tonics + 1 && tobj[find_obj(OBJ_CHEST, 2, 3)].state, "a chest gives its item once");
    enter(MAP_TT_HALL, 9, 14, DIR_UP);
    CHECK(tobj[find_obj(OBJ_CHEST, 2, 3)].state, "an opened chest stays open");
    enter(MAP_TT_HALL, 10, 4, DIR_UP);
    tap(KEY_A);
    run_dialog(600);
    CHECK(game_mode == MODE_BATTLE, "a mimic chest starts a bout");
    game_mode = MODE_FIELD;
    battle_end_hook = 0;

    /* ---- ice ---- */
    enter(MAP_TT_ICE, 1, 3, DIR_RIGHT);
    go(DIR_RIGHT);
    CHECK(player.x == 7 && player.y == 3, "you slide over ice until a frozen rock stops you");
    enter(MAP_TT_ICE, 1, 4, DIR_RIGHT);
    go(DIR_RIGHT);
    CHECK(player.x == 12 && player.y == 4, "and off the far side of the pond");

    /* ---- the ladder is a door ---- */
    CHECK((cell_attr(4, 12) & A_DOOR) && warp_at(MAP_TT_ICE, 4, 12) >= 0, "a ladder is a door with a warp");
    enter(MAP_TT_ICE, 4, 13, DIR_UP);
    go(DIR_UP);
    wait_still();
    CHECK(cur_map == MAP_TT_HALL, "climbing the ladder leads to the hall");

    /* ---- legends ---- */
    enter(MAP_TT_ICE, 15, 13, DIR_UP);
    CHECK((cell_attr(15, 12) & A_SOLID) && legend_count == 1, "a legend stands on its cell");
    int li = find_obj(OBJ_LEGEND, 15, 12);
    tap(KEY_A);
    run_dialog(600);
    CHECK(game_mode == MODE_BATTLE && battle.no_run, "answering a legend starts a bout you can't run from");
    travel_bout_end(BR_CAUGHT);
    game_mode = MODE_FIELD;
    CHECK(tobj[li].state && !(cell_attr(15, 12) & A_SOLID), "once answered, the legend is gone");
    enter(MAP_TT_ICE, 15, 13, DIR_UP);
    CHECK(!(cell_attr(15, 12) & A_SOLID), "and stays gone");

    /* ---- surfing ---- */
    enter(MAP_TT_SHORE, 3, 3, DIR_DOWN);
    CHECK(!obj_interact(3, 5) || !travel.surfing, "no SURF without the crest");
    run_dialog(400);
    travel_award_crest(CREST_TIDE);
    give(SP_AXOLURK, 25);
    enter(MAP_TT_SHORE, 3, 3, DIR_DOWN);
    int has_surf = 0;
    for (int i = 0; i < field_menu_build(); i++) has_surf |= fm_ids[i] == FM_SURF;
    CHECK(has_surf, "facing water, the FIELD menu offers SURF");
    tap(KEY_A);
    run_dialog(400);
    wait_still();
    CHECK(travel.surfing && player.y == 4 && !follower_active(), "you ride your kin onto the water");
    go(DIR_DOWN);
    go(DIR_RIGHT);
    go(DIR_RIGHT);
    go(DIR_RIGHT);
    CHECK(travel.surfing && player.x == 6 && player.y == 5, "surfing moves over water");
    enter(MAP_TT_SHORE, 6, 6, DIR_RIGHT);
    CHECK(travel.surfing, "surf state comes from the cell you stand on");
    go(DIR_RIGHT);
    CHECK(!travel.surfing && player.x == 7, "stepping onto land gets off the water");
    for (int f = 0; f < 4; f++) step(0);
    CHECK(follower_active(), "and your kin walks with you again");
    {
        map_load(MAP_TT_SHORE);
        flood_ex(3, 3, FLOOD_SOLVED);
        int walk = reached_beside(8, 7);
        flood_ex(3, 3, FLOOD_SOLVED | FLOOD_SURF);
        CHECK(!walk && reached_beside(8, 7), "the island satchel is reachable only by surfing");
    }
    /* water kin */
    enter(MAP_TT_SHORE, 10, 9, DIR_DOWN);
    int swam = 0;
    for (int t = 0; t < 40 && !swam; t++) {
        wild_spawn_timer = 1;
        step(0);
        for (int i = 0; i < WILD_MAX; i++)
            if (wild[i].active && wild[i].water && (cell_attr(wild[i].k.a.x, wild[i].k.a.y) & A_WATER)) swam = 1;
    }
    CHECK(swam, "while surfing, water kin appear on the water");
    wild_clear();

    /* ---- the bike ---- */
    bag[ITEM_BIKE] = 1;
    enter(MAP_TT_SHORE, 3, 12, DIR_RIGHT);
    CHECK(travel_key_use(ITEMS[ITEM_BIKE].param) && travel.biking, "the BIKE key item gets you on the bike");
    run_dialog(200);
    CHECK(travel_speed(1) == 4, "the bike is fast");
    int t0 = frame_count;
    go(DIR_RIGHT);
    CHECK(player.x == 4 && frame_count - t0 <= 8, "a bike step takes a quarter of the time");
    tap(KEY_R);
    CHECK(!travel.biking, "R gets off the bike");
    tap(KEY_R);
    CHECK(travel.biking, "and on again");
    enter(MAP_TT_HALL, 9, 14, DIR_UP);
    CHECK(!travel.biking, "no biking indoors");
    tap(KEY_R);
    run_dialog(200);
    CHECK(!travel.biking, "not even with R");

    /* ---- ferry and voyage ---- */
    enter(MAP_TT_SHORE, 16, 13, DIR_UP);
    money = 1000;
    tap(KEY_A);
    run_dialog(400);
    CHECK(game_mode == MODE_EXT && ext.update == voyage_update && money == 500, "the ferry costs 500c and sets sail");
    for (int f = 0; f < VOY_END + 40 && game_mode == MODE_EXT; f++) step(0);
    wait_still();
    CHECK(game_mode == MODE_FIELD && cur_map == MAP_TT_ICE && player.x == 16 && player.y == 2,
          "the voyage lands next to the ferry back");
    bag[ITEM_FERRY_PASS] = 1;
    enter(MAP_TT_ICE, 16, 2, DIR_UP);
    tap(KEY_A);
    run_dialog(400);
    CHECK(game_mode == MODE_EXT && money == 500, "a FERRY PASS rides for free");
    for (int f = 0; f < 30; f++) step(0);
    tap(KEY_A); /* skip */
    for (int f = 0; f < 60 && game_mode == MODE_EXT; f++) step(0);
    CHECK(game_mode == MODE_FIELD && cur_map == MAP_TT_SHORE && player.x == 16 && player.y == 13,
          "A skips the voyage");

    /* ---- town map and FLY ---- */
    enter(MAP_TOWN, 7, 26, DIR_DOWN);
    enter(MAP_TT_SHORE, 3, 12, DIR_DOWN);
    worldmap_open(0);
    CHECK(game_mode == MODE_EXT && ext.update == wm_update && wm.n >= 1, "the town map opens and lists visited towns");
    for (int f = 0; f < 20; f++) step(0);
    tap(KEY_B);
    CHECK(game_mode == MODE_FIELD && cur_map == MAP_TT_SHORE, "B closes it");
    give(SP_ZEPHRAM, 32);
    int has_fly = 0;
    for (int i = 0; i < field_menu_build(); i++) has_fly |= fm_ids[i] == FM_FLY;
    CHECK(!has_fly, "no FLY without the RIME crest");
    travel_award_crest(CREST_RIME);
    for (int i = 0; i < field_menu_build(); i++) has_fly |= fm_ids[i] == FM_FLY;
    CHECK(has_fly, "with it, the FIELD menu offers FLY");
    travel_field_menu_open();
    for (int f = 0; f < 200 && dialog_active(); f++) {
        if (choice.active) choice.cursor = 0;
        for (int i = 0; i < fm_n; i++)
            if (choice.active && fm_ids[i] == FM_FLY) choice.cursor = i;
        step(choice.active && (f & 3) == 0 ? KEY_A : (f & 3) == 0 && !choice.active ? KEY_A : 0);
    }
    for (int f = 0; f < 10 && game_mode == MODE_FIELD; f++) step(0);
    CHECK(game_mode == MODE_EXT && wm.fly, "FLY opens the town map to pick a place");
    tap(KEY_A);
    wait_still();
    CHECK(game_mode == MODE_FIELD && cur_map == FLY_POINTS[0].map && player.x == FLY_POINTS[0].x,
          "flying lands on the fly point");
    CHECK(map_spot(MAP_TOWN) == WM_MAPLE && map_spot(MAP_REST) == WM_MAPLE, "interiors sit on their town's spot");

    /* ---- TELEPORT and WAYSTONE ---- */
    enter(MAP_REST, 5, 8, DIR_UP);
    CHECK(travel.last_hearth == MAP_REST, "a Hearth Hall becomes the teleport target");
    enter(MAP_TT_SHORE, 3, 12, DIR_DOWN);
    bag[ITEM_WAYSTONE] = 1;
    CHECK(travel_use_item(ITEM_WAYSTONE) && bag[ITEM_WAYSTONE] == 0, "a WAYSTONE is used up");
    run_dialog(200);
    for (int f = 0; f < 40; f++) step(0);
    wait_still();
    CHECK(cur_map == MAP_REST, "and takes you to the last Hearth Hall");
    bag[ITEM_LURE_INCENSE] = 1;
    travel_use_item(ITEM_LURE_INCENSE);
    run_dialog(200);
    CHECK(travel_lure_active() && bag[ITEM_LURE_INCENSE] == 0, "LURE INCENSE burns for a while");

    /* ---- crest case ---- */
    crest_case_open();
    CHECK(game_mode == MODE_EXT && ext.update == cc_update, "the crest case opens");
    step(0);
    tap(KEY_B);
    CHECK(game_mode == MODE_FIELD, "and closes");

    /* ---- dark maps ---- */
    enter(MAP_TT_DARK, 5, 6, DIR_DOWN);
    step(0);
    CHECK(dark_want && oam_line_win0h != 0, "a dark map shows a light circle");
    int r0 = travel_light_radius();
    travel_award_crest(CREST_VOLT);
    int has_light = 0;
    for (int i = 0; i < field_menu_build(); i++) has_light |= fm_ids[i] == FM_LIGHT;
    CHECK(has_light, "the VOLT crest and a LIGHT kin offer LIGHT");
    light_use();
    run_dialog(200);
    CHECK(travel_light_radius() > r0, "LIGHT widens the circle");
    start_menu_open();
    CHECK(!dark_applied && oam_line_win0h == 0, "menus switch the darkness off");
    tap(KEY_B);

    /* ---- START menu entries ---- */
    bag[ITEM_TOWN_MAP] = 1;
    start_menu_build();
    int has_map = 0, has_field = 0;
    for (int i = 0; i < start_count; i++) {
        has_map |= start_items[i] == SM_MAP;
        has_field |= start_items[i] == SM_FIELD;
    }
    CHECK(has_map && has_field && start_count <= 10, "START shows MAP and FIELD and still fits");

    /* ---- save round trip ---- */
    enter(MAP_TT_HALL, 9, 14, DIR_UP);
    TravelState keep = travel;
    static u8 sram[32768];
    memset(sram, 0xFF, sizeof(sram));
    CHECK(save_write_to(sram), "the game saves");
    travel_reset();
    CHECK(save_load_from(sram) == 4 && !memcmp(&keep, &travel, sizeof(travel)), "crests, visits and puzzles come back");
    CHECK(!(cell_attr(4, 6) & A_SOLID), "the solved gate is still open after loading");
    enter(MAP_TT_SHORE, 6, 6, DIR_RIGHT);
    save_write_to(sram);
    save_load_from(sram);
    step(0);
    CHECK(travel.surfing, "a save made on the water loads surfing");

    if (failures == 0) {
        printf("all travel checks passed\n");
        return 0;
    }
    printf("%d check(s) FAILED\n", failures);
    return 1;
}
