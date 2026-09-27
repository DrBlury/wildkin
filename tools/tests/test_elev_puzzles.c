/*
 * Puzzles and farms on heights (src/game/elev.c + travel.c + farm.c,
 * docs/ELEVATION.md 7): boulders keep their level (no stairs, no pushing
 * off a cliff edge, a drop off a ledge, over and under a bridge by the
 * pusher's level, over a tunnel), plates and switches answer only on their
 * own level, ice slides and currents stop at a height change, teleport pads
 * put you on the partner's level, farm plots, workers and sprinklers keep
 * to their terrace; the TEST HEIGHTS terrace puzzle played through; hidden
 * passages found for good (the save, older saves, their changed look); a
 * lint of every map object and farm plot on a height layer.
 */
#include "harness.h"

static const u16 DIR_KEY[4] = { KEY_DOWN, KEY_UP, KEY_LEFT, KEY_RIGHT };

static int objs_busy(void)
{
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].ox || tobj[i].oy || (tobj[i].kind == OBJ_GATE && tobj[i].state == 1)) return 1;
    return 0;
}

static void wait_still(void)
{
    for (int f = 0; f < 400 && (player.moving || warp.active || tv.busy || objs_busy()); f++) step(0);
}

/* Stand somewhere else on the loaded map (objects keep their places). */
static void moveto(int x, int y, int level, int dir)
{
    player.x = (s16)x;
    player.y = (s16)y;
    player.ox = player.oy = 0;
    player.moving = player.hop = 0;
    player.facing = (u8)dir;
    player.level = (u8)level;
    field_update_camera();
    step(0);
}

static void go(int dir)
{
    player.facing = (u8)dir;
    player_turn_timer = 0;
    for (int f = 0; f < 4 && !player.moving; f++) step(DIR_KEY[dir]);
    wait_still();
    dialog_clear();
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

/* One step played by the game's rules without drawing (for maps whose
 * tileset has no elevation art but get a height layer poked in below):
 * the same loop as field_player_update(). */
static void play(int dir)
{
    player.facing = (u8)dir;
    if (!player_try_move(dir)) return;
    for (int f = 0; f < 2000; f++) {
        if (travel_update()) continue;
        if (player.moving) {
            if (actor_step(&player, travel_speed(player.hop ? 2 : 1))) {
                elev_player_arrived();
                travel_player_arrived();
            }
            continue;
        }
        int busy = 0;
        for (int i = 0; i < tobj_count; i++)
            if (tobj[i].ox || tobj[i].oy || (tobj[i].kind == OBJ_GATE && tobj[i].state == 1)) busy = 1;
        if (!busy) break;
    }
}

static void place(int map, int x, int y, int level, int dir)
{
    map_load(map);
    player.x = (s16)x;
    player.y = (s16)y;
    player.ox = player.oy = 0;
    player.moving = player.hop = 0;
    player.facing = (u8)dir;
    player.level = (u8)level;
    travel.surfing = 0;
    tv.busy = tv.slide = 0;
    warp.active = 0;
}

static int at(int x, int y, int level)
{
    return player.x == x && player.y == y && player.level == level;
}

static int find_obj(int kind, int x, int y)
{
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].kind == kind && tobj[i].x == x && tobj[i].y == y) return i;
    return -1;
}

/* Move object i (a boulder) to (x, y) on `level`, as if pushed there. */
static void put(int i, int x, int y, int level)
{
    int ox = tobj[i].x, oy = tobj[i].y;
    tobj[i].x = (u8)x;
    tobj[i].y = (u8)y;
    tobj[i].level = (u8)level;
    tobj[i].ox = tobj[i].oy = 0;
    grid_cell(ox, oy);
    grid_cell(x, y);
    plates_update(0);
}

/* A run-time object added to the loaded map (tests only). */
static int add_obj(int kind, int x, int y, int arg, int level)
{
    TObj *o = &tobj[tobj_count];
    memset(o, 0, sizeof(*o));
    o->kind = (u8)kind;
    o->x = (u8)x;
    o->y = (u8)y;
    o->arg = (u8)arg;
    o->level = (u8)level;
    o->bit = 0xFF;
    if (kind == OBJ_BARRIER) o->state = (u8)barrier_up(o);
    tobj_count++;
    grid_cell(x, y);
    return tobj_count - 1;
}

/* OBJ priority travel.c gives object i's sprite. */
static int obj_prio(int i)
{
    FieldSprite list[80];
    int n = travel_push_sprites(list, 0, 80);
    int k = 0;
    for (int j = 0; j < tobj_count; j++) {
        const TObj *o = &tobj[j];
        int wx = o->x * 16 + o->ox, wy = o->y * 16 + o->oy;
        if (!obj_on_screen(wx, wy)) continue;
        int drawn = o->kind == OBJ_BOULDER || o->kind == OBJ_CHEST || o->kind == OBJ_LADDER || o->kind == OBJ_FERRY ||
                    o->kind == OBJ_BARRIER || (o->kind == OBJ_GATE && o->state != 2);
        if (!drawn) continue;
        if (j == i) return k < n ? list[k].prio : -1;
        k++;
    }
    return -1;
}

/* A made-up height layer on the loaded map (for maps without one): every
 * cell plain ground at height 0. */
static void flat_layer(void)
{
    map_elevated = 1;
    for (int i = 0; i < map_w * map_h; i++) map_elev[i] = EV_MAKE(0, 0, 0, EK_GROUND, EC_NONE);
}

static void set_cell(int x, int y, u16 e) { map_elev[y * map_w + x] = e; }

/* ---------------- boulders ---------------- */

static void test_boulders(void)
{
    enter(MAP_EV_TEST, 10, 9, DIR_RIGHT);
    int b = find_obj(OBJ_BOULDER, 24, 12);
    CHECK(b >= 0 && tobj[b].level == 1 && obj_index_at(24, 12) == b,
          "TEST HEIGHTS: the pumice boulder stands on the east plateau (level 1)");

    /* cliff edge */
    enter(MAP_EV_TEST, 10, 7, DIR_RIGHT);
    put(b, 11, 7, 1);
    go(DIR_RIGHT);
    CHECK(tobj[b].x == 11 && tobj[b].level == 1 && at(10, 7, 1), "a boulder can't be pushed off a cliff edge");

    /* stairs, from above and from below */
    enter(MAP_EV_TEST, 6, 12, DIR_DOWN);
    put(b, 6, 13, 1);
    go(DIR_DOWN);
    CHECK(tobj[b].x == 6 && tobj[b].y == 13 && at(6, 12, 1), "nor down stairs");
    enter(MAP_EV_TEST, 6, 16, DIR_UP);
    put(b, 6, 15, 0);
    go(DIR_UP);
    CHECK(tobj[b].y == 15 && at(6, 16, 0), "nor up them");

    /* over a bridge: a plate under the deck, the boulder pushed along the top */
    enter(MAP_EV_TEST, 10, 9, DIR_RIGHT);
    int plate = add_obj(OBJ_PLATE, 12, 9, 5, 0);
    put(b, 11, 9, 1);
    go(DIR_RIGHT);
    CHECK(tobj[b].x == 12 && tobj[b].y == 9 && tobj[b].level == 1 && at(11, 9, 1),
          "a boulder is pushed from the road onto the bridge deck (level 1)");
    CHECK(!tobj[plate].state, "rolling over the deck, it doesn't press the plate on the ground below");
    CHECK(obj_index_at(12, 9) == plate && !(cell_attr(12, 9) & A_SOLID) && travel_top_solid(12, 9, 1),
          "it blocks the deck, not the lane under it");
    CHECK(obj_prio(b) == 1, "a boulder on the deck is drawn over it (OBJ priority 1)");
    go(DIR_RIGHT);
    CHECK(tobj[b].x == 13 && tobj[b].level == 1 && at(12, 9, 1), "and along the deck by a pusher on the deck");

    /* walking under the deck boulder */
    moveto(13, 7, 0, DIR_DOWN);
    go(DIR_DOWN);
    go(DIR_DOWN);
    CHECK(at(13, 9, 0) && tobj[b].x == 13 && tobj[b].y == 9 && tobj[b].level == 1,
          "a pusher under the bridge walks beneath the deck boulder without moving it");
    go(DIR_DOWN);
    CHECK(at(13, 10, 0), "and out the other side");

    /* a boulder on the ground under the deck */
    moveto(12, 7, 0, DIR_DOWN);
    int g = add_obj(OBJ_BOULDER, 12, 8, 1, 0);
    go(DIR_DOWN);
    CHECK(tobj[g].x == 12 && tobj[g].y == 9 && tobj[g].level == 0 && tobj[plate].state,
          "a boulder pushed along the lane under the bridge presses the plate there");
    CHECK(obj_prio(g) == 2 && obj_prio(b) == 1, "under the deck it is drawn under it; the one on top over it");
    moveto(11, 9, 1, DIR_RIGHT);
    go(DIR_RIGHT);
    CHECK(at(12, 9, 1) && tobj[g].y == 9, "a walker on the deck passes over the ground boulder");
    go(DIR_RIGHT);
    CHECK(at(13, 9, 1) && tobj[b].x == 14 && tobj[b].level == 1, "and pushes the deck boulder ahead of them");
    CHECK(obj_interact(14, 9) == 1, "facing along the deck, the deck boulder can be examined");
    dialog_clear();

    /* over a tunnel */
    enter(MAP_EV_TEST, 6, 8, DIR_LEFT);
    put(b, 5, 8, 1);
    go(DIR_LEFT);
    CHECK(tobj[b].x == 4 && tobj[b].y == 8 && tobj[b].level == 1 && at(5, 8, 1),
          "a boulder is pushed over the tunnel's top (level 1)");
    moveto(4, 10, 0, DIR_UP);
    go(DIR_UP);
    go(DIR_UP);
    CHECK(at(4, 8, 0), "and someone in the tunnel below walks under it");
    map_load(MAP_EV_TEST);   /* drop the added plate and boulder */
}

/* ---------------- the TEST HEIGHTS terrace puzzle ---------------- */

static void test_terrace_puzzle(void)
{
    enter(MAP_EV_TEST, 24, 10, DIR_DOWN);
    int b = find_obj(OBJ_BOULDER, 24, 12), plate = find_obj(OBJ_PLATE, 22, 15), gate = find_obj(OBJ_GATE, 27, 13);
    int chest = find_obj(OBJ_CHEST, 27, 10);
    CHECK(b >= 0 && plate >= 0 && gate >= 0 && chest >= 0 && tobj[plate].level == 0 && tobj[gate].level == 1 &&
              tobj[chest].level == 2,
          "the terrace puzzle: boulder on the plateau, plate below, gate before the knoll, chest on top");
    CHECK(cell_attr(27, 13) & A_SOLID, "the gate is shut");
    go(DIR_DOWN);
    go(DIR_DOWN);
    CHECK(at(24, 12, 1) && tobj[b].y == 13, "push the boulder down the chute");
    go(DIR_DOWN);
    CHECK(tobj[b].x == 24 && tobj[b].y == 15 && tobj[b].level == 0 && at(24, 13, 1),
          "pushed off the ledge it drops to the ground below (level 0), past the ledge");
    go(DIR_DOWN);
    CHECK(at(24, 13, 1), "the player can't hop down onto it");
    go(DIR_UP);
    go(DIR_UP);
    go(DIR_UP);
    CHECK(at(24, 10, 1), "back out of the chute");
    moveto(26, 12, 1, DIR_DOWN);
    go(DIR_DOWN);
    go(DIR_DOWN);
    CHECK(at(26, 15, 0), "hop down the other ledge");
    go(DIR_LEFT);
    go(DIR_LEFT);
    CHECK(tobj[b].x == 23 && at(24, 15, 0), "push the boulder west along the ground");
    CHECK(!tobj[plate].state && tobj[gate].state == 0, "not on the plate yet");
    go(DIR_LEFT);
    CHECK(tobj[b].x == 22 && tobj[plate].state && tobj[gate].state == 2 && !(cell_attr(27, 13) & A_SOLID),
          "onto the plate: the gate before the knoll sinks");
    moveto(26, 13, 1, DIR_RIGHT);
    go(DIR_RIGHT);
    go(DIR_UP);
    go(DIR_UP);
    CHECK(at(27, 11, 2), "through the gate and up the stairs onto the knoll (level 2)");
    int tonics = bag[ITEM_TONIC];
    tap(KEY_A);
    run_dialog(600);
    CHECK(bag[ITEM_TONIC] == tonics + 1 && tobj[chest].state, "the chest on the knoll opens");
    enter(MAP_EV_TEST, 24, 10, DIR_DOWN);
    CHECK(tobj[b].x == 24 && tobj[b].y == 12 && tobj[b].level == 1 && tobj[gate].state == 2,
          "coming back: the boulder is back on the plateau, the gate stays open");
    /* the chest from below the knoll is out of reach */
    enter(MAP_EV_TEST, 26, 10, DIR_RIGHT);
    CHECK(player.level == 1, "beside the knoll on the plateau");
    tobj[chest].state = 0;
    tonics = bag[ITEM_TONIC];
    tap(KEY_A);
    run_dialog(600);
    CHECK(bag[ITEM_TONIC] == tonics && !tobj[chest].state, "a chest up on the knoll can't be opened from below it");
    tobj[chest].state = 1;
}

/* ---------------- plates, switches, pads, ice and currents ---------------- */

static void test_tiles(void)
{
    /* ice: TEST ICE with a terrace poked in east of x 8 */
    enter(MAP_TT_ICE, 1, 4, DIR_RIGHT);
    flat_layer();
    for (int y = 0; y < map_h; y++)
        for (int x = 8; x < map_w; x++) set_cell(x, y, EV_MAKE(1, 1, 1, EK_GROUND, EC_NONE));
    player.level = 0;
    ring_invalidate();
    go(DIR_RIGHT);
    CHECK(at(7, 4, 0), "an ice slide stops where the ground rises");
    enter(MAP_TT_ICE, 1, 4, DIR_RIGHT);
    flat_layer();
    for (int y = 0; y < map_h; y++)
        for (int x = 0; x < 8; x++) set_cell(x, y, EV_MAKE(1, 1, 1, EK_GROUND, EC_NONE));
    player.level = 1;
    ring_invalidate();
    go(DIR_RIGHT);
    CHECK(at(7, 4, 1), "and where it falls away (no sliding off a terrace)");
    enter(MAP_TT_ICE, 8, 4, DIR_RIGHT);
    flat_layer();
    for (int y = 0; y < map_h; y++)
        for (int x = 8; x < map_w; x++) set_cell(x, y, EV_MAKE(1, 1, 1, EK_GROUND, EC_NONE));
    player.level = 1;
    ring_invalidate();
    go(DIR_RIGHT);
    CHECK(at(12, 4, 1), "ice up on a terrace slides as on flat ground");

    /* currents: TEST HALL (no elevation art: played without drawing) */
    place(MAP_TT_HALL, 4, 13, 0, DIR_RIGHT);
    play(DIR_RIGHT);
    CHECK(at(9, 13, 0), "flat: the current carries you to its end");
    place(MAP_TT_HALL, 4, 13, 0, DIR_RIGHT);
    flat_layer();
    for (int x = 7; x < map_w; x++) set_cell(x, 13, EV_MAKE(1, 1, 1, EK_GROUND, EC_NONE));
    play(DIR_RIGHT);
    CHECK(at(6, 13, 0), "a current stops at a height change and keeps your level");

    /* pads: the partner pad up on a terrace */
    place(MAP_TT_HALL, 17, 11, 0, DIR_DOWN);
    flat_layer();
    for (int y = 0; y <= 5; y++)
        for (int x = 0; x < map_w; x++) set_cell(x, y, EV_MAKE(1, 1, 1, EK_GROUND, EC_NONE));
    tobj[find_obj(OBJ_PAD, 17, 3)].level = 1;
    play(DIR_DOWN);
    CHECK(at(17, 3, 1), "a teleport pad puts you on its partner's level");
    play(DIR_DOWN);
    play(DIR_UP);
    CHECK(at(17, 12, 0), "and back down on the ground");

    /* a switch under a deck: only someone on its level presses it */
    place(MAP_TT_HALL, 14, 9, 1, DIR_RIGHT);
    flat_layer();
    set_cell(14, 9, EV_MAKE(1, 1, 1, EK_GROUND, EC_NONE));
    set_cell(18, 9, EV_MAKE(1, 1, 1, EK_GROUND, EC_NONE));
    for (int x = 15; x <= 17; x++) set_cell(x, 9, EV_MAKE(0, 1, 0, EK_GROUND, EC_BRIDGE_H));
    int sw = find_obj(OBJ_SWITCH, 16, 9);
    CHECK(sw >= 0 && tobj[sw].level == 0, "the TEST HALL switch lies on the ground");
    play(DIR_RIGHT);
    play(DIR_RIGHT);
    CHECK(at(16, 9, 1) && !sw_on[1], "walking over it on a deck above doesn't press the switch");
    play(DIR_RIGHT);
    CHECK(at(17, 9, 1) && !sw_on[1], "still not");
    place(MAP_TT_HALL, 16, 8, 0, DIR_DOWN);
    flat_layer();
    for (int x = 15; x <= 17; x++) set_cell(x, 9, EV_MAKE(0, 1, 0, EK_GROUND, EC_BRIDGE_H));
    play(DIR_DOWN);
    CHECK(at(16, 9, 0) && sw_on[1], "walking onto it under the deck does");

    /* plates: a boulder on a deck over a plate doesn't press it (see above);
     * a pumice boulder on the plate's own level does */
    place(MAP_TT_HALL, 6, 8, 0, DIR_DOWN);
    flat_layer();
    play(DIR_DOWN);
    play(DIR_DOWN);
    int p = find_obj(OBJ_PLATE, 6, 11);
    CHECK(tobj[p].state && tobj[p].level == 0, "on a height layer a boulder on the plate's level presses it");
    tobj[find_obj(OBJ_BOULDER, 6, 11)].level = 1;   /* the same boulder, as if on a deck above */
    plates_update(0);
    CHECK(!tobj[p].state, "one level above it doesn't");
    map_load(MAP_TT_HALL);
    memset(travel.puzzle, 0, sizeof(travel.puzzle));
}

/* ---------------- farm plots on terraces ---------------- */

static void test_farm(void)
{
    farm_geom_init();
    farm.owned = 1;
    bag[ITEM_HOE] = 1;
    /* WILLOW ACRE with a terrace poked in: x <= 10 is one level up */
    int si = plot_at_xy(10, 15), low = plot_at_xy(11, 15), same = plot_at_xy(10, 16);
    if (same < 0) same = plot_at_xy(10, 14);
    CHECK(si >= 0 && low >= 0 && same >= 0, "WILLOW ACRE plots for the terrace checks");
    u8 saved_lv[FARM_PLOTS];
    memcpy(saved_lv, plot_lv, sizeof(saved_lv));
    for (int i = 0; i < plot_count; i++) plot_lv[i] = plot_x[i] <= 10 ? 1 : 0;
    FarmPlot keep[3] = { farm.plots[si], farm.plots[low], farm.plots[same] };
    farm.plots[si].flags = PF_TILLED | PF_SPRINKLER;
    farm.plots[low].flags = PF_TILLED;
    farm.plots[same].flags = PF_TILLED;
    gtime.weather = WEATHER_CLEAR;
    time_weather_fixed = 1;
    time_new_day();
    time_weather_fixed = 0;
    dialog_clear();
    CHECK((farm.plots[same].flags & PF_WET) && !(farm.plots[low].flags & PF_WET),
          "a sprinkler waters the plots of its own terrace only");
    farm.plots[si] = keep[0];
    farm.plots[low] = keep[1];
    farm.plots[same] = keep[2];

    /* tools: a plot below the terrace edge is out of reach, one beside you isn't */
    field_enter_map(MAP_WILLOW_ACRE, 10, 20, DIR_RIGHT);
    dialog_clear();
    game_mode = MODE_FIELD;
    flat_layer();
    for (int y = 0; y < map_h; y++)
        for (int x = 0; x <= 10; x++) set_cell(x, y, EV_MAKE(1, 1, 1, EK_GROUND, EC_NONE));
    player.level = 1;
    int right = plot_at_xy(11, 20), left = plot_at_xy(9, 20);
    CHECK(right >= 0 && left >= 0 && !(farm.plots[right].flags & PF_TILLED) && !(farm.plots[left].flags & PF_TILLED),
          "two untilled plots either side of the terrace edge");
    tool_select_item(ITEM_HOE);
    fx_freeze = 0;
    field_try_interact();
    dialog_clear();
    CHECK(!(farm.plots[right].flags & PF_TILLED), "the HOE can't reach a plot below the terrace edge");
    player.facing = DIR_LEFT;
    fx_freeze = 0;
    field_try_interact();
    dialog_clear();
    CHECK(farm.plots[left].flags & PF_TILLED, "it tills one on your own terrace");
    farm.plots[left].flags = 0;

    /* a worker keeps to its terrace */
    farm_kin[0].shown = 1;
    farm_kin[0].species = SP_FLARIX;
    farm_kin[0].a.x = 10;
    farm_kin[0].a.y = 22;
    farm_kin[0].a.level = 1;
    farm_kin[0].a.moving = 0;
    int stayed = 1, moved = 0;
    for (int f = 0; f < 20000; f++) {
        workers_update();
        if (!farm_kin[0].a.moving && elev_floor(farm_kin[0].a.x, farm_kin[0].a.y) != 1) stayed = 0;
        if (farm_kin[0].a.x != 10 || farm_kin[0].a.y != 22) moved = 1;
    }
    CHECK(moved && stayed, "a farm worker wanders its own terrace, never off the edge");
    farm_kin[0].shown = 0;
    memcpy(plot_lv, saved_lv, sizeof(saved_lv));
    farm.owned = 0;
}

/* ---------------- hidden passages ---------------- */

static void test_secrets(void)
{
    CHECK(elev_secret_total() > 0 && elev_secret_total() <= SECRET_MAX, "every hidden passage has a save bit");
    int b = elev_secret_base(MAP_EV_TEST);
    memset(travel.secrets, 0, sizeof(travel.secrets));
    enter(MAP_EV_TEST, 22, 19, DIR_RIGHT);
    CHECK(!(elev_at(24, 19) & EV_FOUND) && !travel_secret_get(b), "a new game: the passage isn't found");
    u16 *top = VRAM_MAP(SB_FIELD_TOP), *bottom = VRAM_MAP(SB_FIELD_BOTTOM);
    int idx = (19 & 15) * 64 + (24 & 15) * 2;
    field_redraw_cell(24, 19);
    render_cell(24, 19);
    u16 hidden_bl = bottom[idx + 32], hidden_tl = top[idx + 32];
    go(DIR_RIGHT);
    go(DIR_RIGHT);
    CHECK((elev_at(24, 19) & EV_FOUND) && (elev_at(25, 19) & EV_FOUND) && travel_secret_get(b) && emote.timer > 0,
          "stepping in finds the whole passage (both cells), with a rustle and a '!'");
    field_redraw_cell(24, 19);
    render_cell(24, 19);
    CHECK(top[idx] && !top[idx + 32] && bottom[idx + 32] != hidden_bl && hidden_tl,
          "found, it shows a worn gap at the foot of the trees (the crowns still hang over it)");
    CHECK(bottom[idx + 32] == TILESETS[TS_TOWN].path_q[2][3] || bottom[idx + 32] == TILESETS[TS_TOWN].path_q[2][4] ||
              bottom[idx + 32] == TILESETS[TS_TOWN].path_q[2][0] || bottom[idx + 32] == TILESETS[TS_TOWN].path_q[2][1] ||
              bottom[idx + 32] == TILESETS[TS_TOWN].path_q[2][2],
          "the gap is drawn with the tileset's path");
    emote.timer = 0;
    enter(MAP_EV_TEST, 22, 19, DIR_RIGHT);
    CHECK((elev_at(24, 19) & EV_FOUND) && (elev_at(25, 19) & EV_FOUND), "leaving and coming back: still found");
    go(DIR_RIGHT);
    go(DIR_RIGHT);
    CHECK(at(24, 19, 0) && emote.timer == 0, "no second '!'");

    /* the save */
    static u8 sram[32768];
    memset(sram, 0xFF, sizeof(sram));
    CHECK(save_write_to(sram), "save with the passage found");
    memset(travel.secrets, 0, sizeof(travel.secrets));
    map_load(MAP_EV_TEST);
    CHECK(!(elev_at(24, 19) & EV_FOUND), "(forgotten)");
    CHECK(save_load_from(sram) == SAVE_VERSION && travel_secret_get(b) && (elev_at(24, 19) & EV_FOUND),
          "loading the save: the passage is found again");

    /* an older save: its travel blob is 41 bytes (no secrets) */
    static SaveData old;
    travel.crests = 5;
    save_capture(&old);
    CHECK(old.mod_size[4] == sizeof(TravelState) && sizeof(TravelState) == 41 + 8 + 16, "the travel blob grew for secrets and high map visits");
    old.mod_size[4] = 41;
    for (int i = 41; i < MOD_TRAVEL_MAX; i++) old.travel[i] = 0;
    old.checksum_v7 = save_checksum(&old);
    travel.crests = 0;
    CHECK(save_valid(&old), "a save from before the secrets is valid");
    save_apply(&old);
    CHECK(travel.crests == 5 && !travel_secret_get(b) && !(elev_at(24, 19) & EV_FOUND),
          "it loads with its travel state and no passages found");
    old.map = MAP_EV_TEST;
    old.player_x = 22;
    old.player_y = 19;
    old.checksum_v7 = save_checksum(&old);
    save_apply(&old);
    go(DIR_RIGHT);
    go(DIR_RIGHT);
    CHECK(travel_secret_get(b) && (elev_at(24, 19) & EV_FOUND), "and finds them as it plays on");

    /* a secret cave in a cliff face opens once found */
    int fm = -1, fx = 0, fy = 0;
    for (int m = 0; m < MAP_COUNT && fm < 0; m++)
        for (int k = 0; k < MAPS[m].feat_count && fm < 0; k++) {
            const ElevFeat *f = &MAPS[m].feats[k];
            if (f->kind != EF_HIDDEN || !MAPS[m].elev || !TILESETS[MAPS[m].tileset].elev) continue;
            map_load(m);
            if (EV_KIND(elev_at(f->x, f->y)) == EK_FACE) {
                fm = m;
                fx = f->x;
                fy = f->y;
            }
        }
    CHECK(fm >= 0, "some map hides a passage in a cliff face");
    if (fm >= 0) {
        memset(travel.secrets, 0, sizeof(travel.secrets));
        enter(fm, fx, fy + 1, DIR_UP);
        u16 *mid = VRAM_MAP(SB_PANEL);
        int ci = (fy & 15) * 64 + (fx & 15) * 2;
        field_redraw_cell(fx, fy);
        render_cell(fx, fy);
        int was_mouth = mid[ci] == TILESETS[MAPS[fm].tileset].elev->mouth[0];
        elev_secret_find(fx, fy);
        field_redraw_cell(fx, fy);
        render_cell(fx, fy);
        CHECK(!was_mouth && mid[ci] == TILESETS[MAPS[fm].tileset].elev->mouth[0] && !top[ci],
              "a crack in a cliff, once found, is drawn as an open cave mouth");
        memset(travel.secrets, 0, sizeof(travel.secrets));
    }
}

/* ---------------- lint ---------------- */

static void lint(void)
{
    int ok = 1;
    for (int m = 0; m < MAP_COUNT; m++) {
        if (!MAPS[m].elev || !MAPS[m].obj_count) continue;
        map_load(m);
        for (int i = 0; i < tobj_count; i++) {
            const TObj *o = &tobj[i];
            u16 e = elev_at(o->x, o->y);
            int bad = EV_KIND(e) != EK_GROUND || EV_COVER(e) == EC_HIDDEN;
            if (o->kind != OBJ_BOULDER && o->level != EV_LO(e)) bad = 1;   /* only boulders go up on decks */
            if (bad) {
                ok = 0;
                printf("  %s: object %d at %d,%d is on a face, stairs, a ledge, a secret or a deck\n", MAPS[m].name, i,
                       o->x, o->y);
            }
        }
    }
    CHECK(ok, "map objects on height layers stand on plain ground (boulders may start on a deck)");
    int farm_ok = 1;
    const MapDef *fm = &MAPS[MAP_WILLOW_ACRE];
    if (fm->elev) {
        map_load(MAP_WILLOW_ACRE);
        for (int i = 0; i < plot_count; i++) {
            u16 e = elev_at(plot_x[i], plot_y[i]);
            if (EV_KIND(e) != EK_GROUND || EV_COVER(e) != EC_NONE || EV_LO(e) != plot_lv[i]) farm_ok = 0;
        }
    }
    CHECK(farm_ok, "farm plots lie on plain ground of their terrace");
    /* Later loop routes may add persistent objects; their bit ranges remain disjoint. */
    int bit_order = 1;
    for (int m = MAP_EV_TEST + 1; m < MAP_COUNT; m++)
        bit_order &= pbit_base(m + 1) >= pbit_base(m);
    CHECK(bit_order, "later route puzzle bits follow TEST HEIGHTS without overlap");
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    fresh_game();
    give_starter();
    flag_set(FLAG_STORM_CALMED);
    opt.follower = 0;
    follower.shown = 0;

    test_boulders();
    test_terrace_puzzle();
    test_tiles();
    test_farm();
    test_secrets();
    lint();

    if (failures) {
        printf("%d elevation puzzle check(s) failed\n", failures);
        return 1;
    }
    printf("all elevation puzzle checks passed\n");
    return 0;
}
