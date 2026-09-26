/*
 * Host-side unit tests for the overworld and the UI in src/main.c: every
 * map's layout, links, doors and reachability, the decor VRAM budget,
 * grid movement, ledges, the follower, visible wild kin, wardens' sight
 * lines, people and the lore they reveal, the Lorebook, the options, the
 * text/canvas renderer, every menu screen and the save format.
 *
 * Run with `make test`.
 */
#include "tests/harness.h"

/* A walkable cell of `map` to start flood fills from. */
static void map_entry(int map, int *ex, int *ey)
{
    for (int i = 0; i < WARP_COUNT; i++)
        if (WARPS[i].dest == map) {
            *ex = WARPS[i].dx;
            *ey = WARPS[i].dy;
            return;
        }
    const MapDef *m = &MAPS[map];
    /* the cell just inside the first linked edge */
    for (int l = 0; l < 4; l++) {
        if (m->link[l] == MAP_NONE) continue;
        for (int k = 0; k < (l < 2 ? m->w : m->h); k++) {
            int x = l < 2 ? k : (l == LINK_W ? 0 : m->w - 1);
            int y = l < 2 ? (l == LINK_N ? 0 : m->h - 1) : k;
            if (cell_walkable(x, y)) {
                *ex = x;
                *ey = y;
                return;
            }
        }
    }
    /* no door or edge leads in: a ferry landing, a fly point, else the
     * walkable cell nearest the middle (maps reached by boat or FLY) */
    for (int i = 0; i < m->obj_count; i++)
        if (m->objs[i].kind == OBJ_FERRY) {
            *ex = m->objs[i].x;
            *ey = m->objs[i].y + 1;
            return;
        }
    for (int i = 0; i < FLY_POINT_COUNT; i++)
        if (FLY_POINTS[i].map == map) {
            *ex = FLY_POINTS[i].x;
            *ey = FLY_POINTS[i].y;
            return;
        }
    int best = 1 << 30;
    *ex = *ey = 0;
    for (int y = 0; y < m->h; y++)
        for (int x = 0; x < m->w; x++)
            if (cell_walkable(x, y) && absi(x - m->w / 2) + absi(y - m->h / 2) < best) {
                best = absi(x - m->w / 2) + absi(y - m->h / 2);
                *ex = x;
                *ey = y;
            }
}

static void test_maps(void)
{
    int rows_ok = 1, stamps_ok = 1, decor_ok = 1, budget_ok = 1;
    for (int m = 0; m < MAP_COUNT; m++) {
        const MapDef *d = &MAPS[m];
        if (d->w > MAP_MAX_W || d->h > MAP_MAX_H) rows_ok = 0;
        for (int y = 0; d->rows && y < d->h; y++)   /* generated viewer maps have no rows */
            if ((int)strlen(d->rows[y]) != d->w) {
                rows_ok = 0;
                printf("  %s row %d is %d wide\n", d->name, y, (int)strlen(d->rows[y]));
            }
        for (int i = 0; i < d->stamp_count; i++)
            if (d->stamps[i].x + d->stamps[i].w > d->w || d->stamps[i].y + d->stamps[i].h > d->h) stamps_ok = 0;
        for (int i = 0; i < d->decor_count; i++) {
            const DecorPlace *p = &d->decor[i];
            const DecorDef *dd = &DECOR_DEFS[d->tileset][p->kind];
            if (!dd->w || p->x + dd->w > d->w || p->y + dd->h > d->h) {
                decor_ok = 0;
                printf("  %s: decor %s at %d,%d does not fit\n", d->name, DECOR_NAMES[p->kind], p->x, p->y);
            }
        }
        map_load(m);
        field_load_tileset();
        if (decor_tiles_used > 512) {
            budget_ok = 0;
            printf("  %s needs %d scene tiles\n", d->name, decor_tiles_used);
        }
    }
    CHECK(rows_ok, "every map row has the declared width and fits the buffers");
    CHECK(stamps_ok && decor_ok, "stamps and decor fit their maps (and exist in the map's tileset)");
    CHECK(budget_ok, "each map's tileset plus its decor fits the 512-tile scene charblock");

    /* links are two-way and land on walkable cells */
    int links_ok = 1;
    static const u8 BACK[4] = { LINK_S, LINK_N, LINK_E, LINK_W };
    for (int m = 0; m < MAP_COUNT; m++)
        for (int l = 0; l < 4; l++) {
            int to = MAPS[m].link[l];
            if (to == MAP_NONE) continue;
            if (MAPS[to].link[BACK[l]] != m) links_ok = 0;
        }
    CHECK(links_ok, "map links are two-way");

    /* every walkable edge cell lands on a walkable cell of the neighbour
     * (the edge contracts in docs/EXPANSION.md 9) */
    int land_ok = 1;
    for (int m = 0; m < MAP_COUNT; m++)
        for (int l = 0; l < 4; l++) {
            int to = MAPS[m].link[l];
            if (to == MAP_NONE) continue;
            static u8 xs[MAP_MAX_W + MAP_MAX_H];
            int n = 0;
            map_load(m);
            int len = l < 2 ? map_w : map_h;
            for (int k = 0; k < len; k++) {
                int x = l < 2 ? k : (l == LINK_W ? 0 : map_w - 1);
                int y = l < 2 ? (l == LINK_N ? 0 : map_h - 1) : k;
                if (!(cell_attr(x, y) & (A_SOLID | A_WATER | A_LEDGE))) xs[n++] = (u8)k;
            }
            int off = MAPS[m].link_off[l];
            map_load(to);
            for (int i = 0; i < n; i++) {
                int x, y;
                switch (l) {
                case LINK_N: x = xs[i] + off; y = map_h - 1; break;
                case LINK_S: x = xs[i] + off; y = 0; break;
                case LINK_W: x = map_w - 1; y = xs[i] + off; break;
                default: x = 0; y = xs[i] + off; break;
                }
                if (x < 0 || y < 0 || x >= map_w || y >= map_h || (cell_attr(x, y) & (A_SOLID | A_WATER))) {
                    land_ok = 0;
                    printf("  %s -> %s: walking off at %d lands on a wall (%d,%d)\n", MAPS[m].name,
                           MAPS[to].name, xs[i], x, y);
                }
            }
        }
    CHECK(land_ok, "walking off any edge lands on a walkable cell of the next map");

    int doors_ok = 1;
    for (int i = 0; i < WARP_COUNT; i++) {
        map_load(WARPS[i].map);
        if (!(cell_attr(WARPS[i].x, WARPS[i].y) & A_DOOR)) doors_ok = 0;
    }
    CHECK(doors_ok, "every door warp sits on a building's door cell");

    /* reachability of everything on every map */
    int reach_ok = 1;
    for (int m = 0; m < MAP_COUNT; m++) {
        map_load(m);
        int ex, ey;
        map_entry(m, &ex, &ey);
        /* puzzles solved (Halls behind gates, barriers and pads); water is
         * open on maps with water kin (surf routes) */
        flood_ex(ex, ey, FLOOD_SOLVED | (MAPS[m].water_zone ? FLOOD_SURF : 0));
        for (int i = 0; i < NPC_COUNT; i++) {
            if (NPCS[i].map != m) continue;
            int ok = reached_beside(NPCS[i].x, NPCS[i].y);
            for (int d = 0; d < 4 && !ok; d++) {
                int cx = NPCS[i].x + DIR_DX[d], cy = NPCS[i].y + DIR_DY[d];
                if ((cell_attr(cx, cy) & A_COUNTER) && reached(cx + DIR_DX[d], cy + DIR_DY[d])) ok = 1;
            }
            if (!ok) {
                reach_ok = 0;
                printf("  %s: %s at %d,%d unreachable\n", MAPS[m].name, NPCS[i].name ? NPCS[i].name : "warden",
                       NPCS[i].x, NPCS[i].y);
            }
        }
        for (int i = 0; i < ITEM_BALL_COUNT; i++)
            if (ITEM_BALLS[i].map == m && !reached_beside(ITEM_BALLS[i].x, ITEM_BALLS[i].y)) {
                reach_ok = 0;
                printf("  %s: satchel %d at %d,%d unreachable\n", MAPS[m].name, i, ITEM_BALLS[i].x, ITEM_BALLS[i].y);
            }
        for (int i = 0; i < SIGN_COUNT; i++)
            if (SIGNS[i].map == m &&
                (!(cell_attr(SIGNS[i].x, SIGNS[i].y) & A_SOLID) || !reached_beside(SIGNS[i].x, SIGNS[i].y))) {
                reach_ok = 0;
                printf("  %s: sign at %d,%d not solid/reachable\n", MAPS[m].name, SIGNS[i].x, SIGNS[i].y);
            }
        for (int i = 0; i < WARP_COUNT; i++)
            if (WARPS[i].map == m && !reached(WARPS[i].x, WARPS[i].y + 1)) {
                reach_ok = 0;
                printf("  %s: door at %d,%d unreachable\n", MAPS[m].name, WARPS[i].x, WARPS[i].y);
            }
        for (int l = 0; l < 4; l++) {
            if (MAPS[m].link[l] == MAP_NONE) continue;
            int found = 0;
            for (int k = 0; k < (l < 2 ? map_w : map_h); k++) {
                int x = l < 2 ? k : (l == LINK_W ? 0 : map_w - 1);
                int y = l < 2 ? (l == LINK_N ? 0 : map_h - 1) : k;
                if (reached(x, y)) found = 1;
            }
            if (!found) {
                reach_ok = 0;
                printf("  %s: exit %d unreachable\n", MAPS[m].name, l);
            }
        }
        if (MAPS[m].zone != ZONE_NONE) {
            int grass = 0;
            for (int y = 0; y < map_h; y++)
                for (int x = 0; x < map_w; x++)
                    if ((cell_attr(x, y) & A_GRASS) && reached(x, y)) grass++;
            if (grass < 20) {
                reach_ok = 0;
                printf("  %s: only %d reachable grass cells\n", MAPS[m].name, grass);
            }
        }
    }
    CHECK(reach_ok, "people, satchels, signs, doors, exits and grass are reachable on every map");

    map_load(MAP_RISE);
    flood(11, 17);
    CHECK(reached_beside(STORMSTONE_X, STORMSTONE_Y) && (cell_attr(STORMSTONE_X, STORMSTONE_Y) & A_SOLID),
          "the Stormstone stands on the Rise and can be reached");

    int wardens_ok = 1;
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].trainer != NO_TRAINER &&
            (NPCS[i].trainer >= TRAINER_COUNT || !NPCS[i].sight || TRAINERS[NPCS[i].trainer].count < 1))
            wardens_ok = 0;
    CHECK(wardens_ok, "every route warden has a team and a line of sight");

    /* generated tilesets reference valid tiles and banks */
    int tiles_ok = 1;
    for (int m = 0; m < MT_TOWN_COUNT; m++)
        for (int q = 0; q < 4; q++)
            if ((town_meta_bottom[m][q] & 0x3FF) >= TOWN_TILE_COUNT) tiles_ok = 0;
    for (int m = 0; m < MT_WILD_COUNT; m++)
        for (int q = 0; q < 4; q++)
            if ((wild_meta_bottom[m][q] & 0x3FF) >= WILD_TILE_COUNT) tiles_ok = 0;
    for (int m = 0; m < MT_INTERIOR_COUNT; m++)
        for (int q = 0; q < 4; q++)
            if ((interior_meta_bottom[m][q] & 0x3FF) >= INTERIOR_TILE_COUNT) tiles_ok = 0;
    CHECK(tiles_ok, "terrain metatiles point at real tiles");
    CHECK(town_meta_top[MT_T_TALLGRASS][2] != 0 && wild_meta_top[MT_W_REEDS][2] != 0,
          "tall grass and reeds have a front layer drawn over legs");
}

/* ---------------- movement ---------------- */

static void test_movement(void)
{
    fresh_game();
    CHECK(cur_map == MAP_HOME, "a new game starts at home");
    field_enter_map(MAP_TOWN, 6, 9, DIR_DOWN);
    tap(KEY_RIGHT);
    CHECK(player.x == 6 && player.facing == DIR_RIGHT, "tapping a new direction only turns the player");
    hold(KEY_RIGHT, 40);
    settle();
    CHECK(player.x >= 8 && player.y == 9 && player.ox == 0, "holding a direction walks cell by cell");
    int x0 = player.x;
    hold(KEY_B | KEY_RIGHT, 16);
    settle();
    CHECK(player.x - x0 == 2, "holding B runs twice as fast");

    field_enter_map(MAP_TOWN, 6, 7, DIR_UP);
    hold(KEY_UP, 4);
    for (int f = 0; f < 30; f++) step(0);
    CHECK(cur_map == MAP_HOME && player.x == 5 && player.y == 8, "walking into a door enters the house");
    hold(KEY_DOWN, 12);
    for (int f = 0; f < 30; f++) step(0);
    CHECK(cur_map == MAP_TOWN && player.x == 6 && player.y == 7, "stepping off the mat leaves the house");

    /* the village won't let you out without a kin */
    field_enter_map(MAP_TOWN, 19, 2, DIR_UP);
    hold(KEY_UP, 40);
    run_dialog(300);
    settle();
    CHECK(cur_map == MAP_TOWN, "you can't leave the village before your Kindling");
    give_starter();
    field_enter_map(MAP_TOWN, 19, 1, DIR_UP);
    hold(KEY_UP, 20);
    for (int f = 0; f < 40; f++) step(0);
    CHECK(cur_map == MAP_MEADOW && player.y == MAPS[MAP_MEADOW].h - 1 && player.x == 19,
          "walking off the north edge leads into WHISPER MEADOW");
    CHECK(follower_active() && absi(follower.a.x - player.x) + absi(follower.a.y - player.y) <= 1,
          "your lead kin arrives behind you");
    hold(KEY_UP, 50);
    settle();
    CHECK(absi(follower.a.x - player.x) + absi(follower.a.y - player.y) == 1,
          "the follower stays one step behind while walking");

    /* ledge hop */
    field_enter_map(MAP_MEADOW, 18, 23, DIR_DOWN);
    hold(KEY_DOWN, 4);
    settle();
    CHECK(player.y == 25, "walking down onto a ledge hops over it");
    hold(KEY_UP, 30);
    settle();
    CHECK(player.y == 25, "ledges can't be climbed back up");
}

/* ---------------- wild kin & wardens ---------------- */

static void test_encounters(void)
{
    fresh_game();
    give_starter();
    field_enter_map(MAP_MEADOW, 8, 30, DIR_DOWN);
    rng_seed(3);
    int spawned = 0;
    for (int f = 0; f < 900 && !spawned; f++) {
        step(0);
        for (int i = 0; i < WILD_MAX; i++) spawned |= wild[i].active;
    }
    CHECK(spawned, "wild kin appear in the tall grass");
    int in_grass = 1;
    for (int i = 0; i < WILD_MAX; i++)
        if (wild[i].active && !(cell_attr(wild[i].k.a.x, wild[i].k.a.y) & A_GRASS)) in_grass = 0;
    CHECK(in_grass, "they spawn in grass");
    int lv_lo = 99, lv_hi = 0;
    for (int n = 0; n < 60; n++) {
        Monster m = roll_wild(ZONE_MEADOW);
        if (m.level < lv_lo) lv_lo = m.level;
        if (m.level > lv_hi) lv_hi = m.level;
    }
    CHECK(lv_hi - lv_lo >= 3, "wild kin come at a spread of levels");

    /* walking into one starts a bout, and it's gone afterwards */
    int s = -1;
    for (int i = 0; i < WILD_MAX; i++)
        if (wild[i].active) s = i;
    wild_touch(s);
    for (int f = 0; f < 80 && game_mode == MODE_FIELD; f++) step(0);
    CHECK(game_mode == MODE_BATTLE, "touching a wild kin starts a bout");
    battle.state = BST_END;
    battle.result = BR_RUN;
    battle.timer = 16;
    for (int f = 0; f < 4 && game_mode == MODE_BATTLE; f++) step(0);
    CHECK(game_mode == MODE_FIELD && !wild[s].active, "after the bout that kin is gone");

    /* hush bell */
    bag[ITEM_HUSH_BELL] = 1;
    CHECK(item_use_field(ITEM_HUSH_BELL, 0) && hush_steps == ITEMS[ITEM_HUSH_BELL].param,
          "the HUSH BELL quiets wild kin for a while");
    hush_steps = 0;

    /* a warden spots you */
    fresh_game();
    give_starter();
    int w = -1;
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].map == MAP_MEADOW && NPCS[i].trainer == TR_LUCA) w = i;
    field_enter_map(MAP_MEADOW, 20, 38, DIR_UP);
    for (int f = 0; f < 60 && !spot.active; f++) step(f < 40 ? KEY_UP : 0);
    CHECK(spot.active && spot.npc == w, "walking into a warden's line of sight gets you spotted");
    for (int f = 0; f < 400 && game_mode != MODE_BATTLE; f++) step((f & 7) == 0 ? KEY_A : 0);
    CHECK(game_mode == MODE_BATTLE && battle.kind == BK_TRAINER, "the warden walks over and starts a bout");
    battle.result = BR_WIN;
    battle.state = BST_END;
    battle.timer = 16;
    for (int f = 0; f < 4 && game_mode == MODE_BATTLE; f++) step(0);
    CHECK(trainer_beaten(TR_LUCA), "a beaten warden is remembered");
    run_dialog(200);
    int again = 0;
    for (int f = 0; f < 120; f++) {
        step(0);
        again |= spot.active;
    }
    CHECK(!again, "a beaten warden won't challenge you again");
}

/* ---------------- people, lore & story ---------------- */

static void test_people(void)
{
    fresh_game();
    field_enter_map(MAP_LAB, 6, 5, DIR_UP);
    tap(KEY_A);
    CHECK(dialog_active(), "Keeper Linden talks when you face them and press A");
    int f = 0;
    while (dialog_active() && !choice.active && f < 1200) step((f++ & 3) == 0 ? KEY_A : 0);
    CHECK(choice.active && choice.count == 3 && starter_preview >= 0,
          "the Kindling offers three kits and shows the highlighted one");
    step(KEY_DOWN);
    step(0);
    CHECK(starter_preview == 1, "the preview follows the cursor");
    for (f = 0; f < 1500 && dialog_active(); f++) step((f & 3) == 0 ? KEY_A : 0);
    CHECK(party_count == 1 && party[0].species == SP_AQUAPO && (flag(FLAG_STARTER)) &&
          bag[ITEM_LANTERN] == 5 && dex_caught[SP_AQUAPO] && lore_is_known(LORE_KINDLING),
          "choosing gives the kit, lanterns, an Almanac entry and a Lorebook page");

    /* Pip: twin crystal */
    field_enter_map(MAP_LAB, 3, 6, DIR_UP);
    tap(KEY_A);
    run_dialog(1200);
    CHECK((flag(FLAG_TWIN_CRYSTAL)) && bag[ITEM_HUSH_BELL] == 1, "Pip hands over the TWIN CRYSTAL");

    /* lore from people */
    int before = lore_known_count();
    field_enter_map(MAP_TOWN, 16, 15, DIR_UP);
    tap(KEY_A);
    run_dialog(1200);
    CHECK(lore_known_count() == before + 1 && lore_is_known(lore_next_from(LSRC_ELDER) < 0 ? LORE_KINSHIP : LORE_KINSHIP),
          "talking to Elder Bram adds a Lorebook page");
    int told = 0;
    for (int n = 0; n < 12; n++) {
        tap(KEY_A);
        run_dialog(1200);
    }
    for (int i = 0; i < LORE_COUNT; i++)
        if (LORE[i].source == LSRC_ELDER) told += lore_is_known(i);
    int total = 0;
    for (int i = 0; i < LORE_COUNT; i++) total += LORE[i].source == LSRC_ELDER;
    CHECK(told == total, "people keep telling new lore until they run out");

    /* satchels are picked up once */
    field_enter_map(MAP_TOWN, 36, 3, DIR_RIGHT);
    int t = bag[ITEM_TONIC];
    tap(KEY_A);
    run_dialog(400);
    CHECK(bag[ITEM_TONIC] == t + 2 && item_taken(0), "a satchel gives its item");
    CHECK(cell_walkable(37, 3), "an opened satchel no longer blocks the way");

    /* the tender across the counter */
    party[0].hp = 1;
    field_enter_map(MAP_REST, 5, 4, DIR_UP);
    tap(KEY_A);
    for (f = 0; f < 800 && dialog_active(); f++) step((f & 3) == 0 ? KEY_A : 0);
    CHECK(party[0].hp == party[0].max_hp, "the Tender's hearth restores the team");

    /* shop: buy two lanterns */
    money = 1000;
    field_enter_map(MAP_SHOP, 1, 4, DIR_UP);
    tap(KEY_A);
    for (f = 0; f < 300 && game_mode != MODE_SHOP; f++) step((f & 3) == 0 ? KEY_A : 0);
    CHECK(game_mode == MODE_SHOP, "the clerk opens the shop");
    int caps = bag[ITEM_LANTERN];
    tap(KEY_A);
    tap(KEY_UP);
    tap(KEY_A);
    for (f = 0; f < 200 && shop.state == 2; f++) step((f & 3) == 0 ? KEY_A : 0);
    CHECK(bag[ITEM_LANTERN] == caps + 2 && money == 1000 - 2 * ITEMS[ITEM_LANTERN].price,
          "buying two lanterns costs the right number of coins");
    tap(KEY_B);
    run_dialog(200);
    CHECK(game_mode == MODE_FIELD, "leaving the shop returns to the field");

    /* gardener's shard, once */
    field_enter_map(MAP_GARDEN, 7, 5, DIR_UP);
    tap(KEY_A);
    run_dialog(800);
    tap(KEY_A);
    run_dialog(800);
    CHECK(bag[ITEM_BLOOM_SHARD] == 1, "the gardener gives exactly one BLOOM SHARD");

    /* the story: sash -> keeper -> stormstone -> DRAKORA */
    flag_set(FLAG_SASH);
    field_enter_map(MAP_LAB, 6, 5, DIR_UP);
    for (int n = 0; n < 8 && !(flag(FLAG_STORM_TOLD)); n++) {
        tap(KEY_A);
        run_dialog(1500);
    }
    CHECK(flag(FLAG_STORM_TOLD), "with the RING SASH the Keeper sends you to the Stormstone");
    party_heal_all();
    field_enter_map(MAP_RISE, STORMSTONE_X, STORMSTONE_Y + 1, DIR_UP);
    run_dialog(400);
    tap(KEY_A);
    for (f = 0; f < 1200 && game_mode != MODE_BATTLE; f++) step((f & 3) == 0 ? KEY_A : 0);
    CHECK(game_mode == MODE_BATTLE && battle.team[0].species == SP_DRAKORA && battle.no_run,
          "the Stormstone calls DRAKORA to a bout you can't run from");
    battle.result = BR_WIN;
    battle.state = BST_END;
    battle.timer = 16;
    for (f = 0; f < 4 && game_mode == MODE_BATTLE; f++) step(0);
    run_dialog(2000);
    CHECK((flag(FLAG_STORM_CALMED)) && lore_is_known(LORE_CLEAR_SKIES), "winning calms the storm");
    CHECK(!storm_active(), "and the sky clears");
}

/* ---------------- text & canvas ---------------- */

static void test_text(void)
{
    char out[400];
    text_wrap(out, "It walks the edge of the night, cloaked in smoke. Its tail burns with light it drank from a hundred sunsets.", 120);
    int ok = 1;
    for (char *line = out; *line;) {
        char *nl = strchr(line, '\n');
        char buf[128];
        int n = nl ? (int)(nl - line) : (int)strlen(line);
        memcpy(buf, line, (size_t)n);
        buf[n] = 0;
        if (text_width(buf) > 120) ok = 0;
        line += n + (nl ? 1 : 0);
    }
    int lines = 1;
    for (char *p = out; *p; p++) lines += *p == '\n';
    CHECK(ok && lines >= 3, "word wrap keeps every line within the width");
    text_wrap(out, "AAAAAAAAAA\fBBB BBB BBB BBB", 120);
    CHECK(strchr(out, '\n') == 0, "a page break resets the line width");

    canvas_clear();
    canvas_window(0, 14, 30, 6, WIN_STD);
    int paper = (canvas[(15 * 30 + 5) * 8 + 3] & 15) == 1;
    text_draw(16, 120, "HELLO");
    int inked = 0;
    for (int r = 0; r < 8; r++) inked |= canvas[(15 * 30 + 2) * 8 + r] != 0x11111111u;
    CHECK(paper && inked, "windows fill with paper and text draws ink into the canvas");
    CHECK(text_width("ABC") > text_width("iii"), "the font is variable width");
}

/* ---------------- menus ---------------- */

static int start_index(int item)
{
    start_menu_build();
    for (int i = 0; i < start_count; i++)
        if (start_items[i] == item) return i;
    return -1;
}

static void test_menus(void)
{
    fresh_game();
    Monster team[3] = { monster_make(SP_FLARIX, 20), monster_make(SP_AQUAPO, 18), monster_make(SP_GOLEMIT, 15) };
    for (int i = 0; i < 3; i++) give_monster(&team[i]);
    flag_set(FLAG_STARTER); flag_set(FLAG_TWIN_CRYSTAL);
    bag[ITEM_TONIC] = 3;
    bag[ITEM_FROST_SHARD] = 1;
    field_enter_map(MAP_TOWN, 20, 16, DIR_DOWN);

    tap(KEY_START);
    CHECK(game_mode == MODE_START_MENU && start_index(SM_SHELF) >= 0, "START opens the menu (with the SHELF)");
    start_cursor = start_index(SM_ALMANAC);
    tap(KEY_A);
    CHECK(game_mode == MODE_DEX && dex.state == 0, "ALMANAC opens the kin list");
    for (int i = 0; i < 60; i++) step(KEY_DOWN);
    step(0);
    CHECK(dex.cursor > DEX_ROWS && dex.scroll > 0, "the list scrolls through all species");
    tap(KEY_A);
    CHECK(dex.state == 1, "A opens a species' page");
    int long_enough = 1, narrow = 1;
    for (int s = 0; s < SP_COUNT; s++) {
        dex_build_content(s);
        if (dex.content_lines * LINE_H <= PANEL_H || dex.content_lines >= PANEL_MAX_LINES) long_enough = 0;
        for (int k = 0; k < dex.content_lines; k++) {
            const PanelLine *l = &dex.lines[k];
            int w = text_width(l->text) + (l->kind == PL_MOVE ? 32 : 0);
            if (l->kind != PL_STAT && w > panel_cols * 8 - 8) {
                narrow = 0;
                printf("  %s: \"%s\" is too wide\n", SPECIES[s].name, l->text);
            }
        }
    }
    CHECK(long_enough, "every species has a page longer than the panel (scrollable)");
    CHECK(narrow, "every Almanac line fits the panel");
    dex_detail_redraw();
    for (int i = 0; i < 90; i++) step(KEY_DOWN);
    step(0);
    CHECK(dex.scroll_px > 0 && dex.scroll_px <= panel_max_scroll(), "UP/DOWN scroll the page");
    {
        int before = dex.cursor;
        tap(KEY_RIGHT);
        CHECK(dex.cursor != before && dex.scroll_px == 0 && (REG_DISPCNT & DCNT_BG2) && (REG_DISPCNT & DCNT_WIN0),
              "RIGHT turns to the next species with the page panel still shown");
    }
    tap(KEY_B);
    tap(KEY_B);
    CHECK(game_mode == MODE_START_MENU, "B leaves the Almanac");

    /* lorebook */
    lore_learn(LORE_KERNEL);
    start_cursor = start_index(SM_LORE);
    tap(KEY_A);
    CHECK(game_mode == MODE_LORE && lb.state == 0, "LOREBOOK opens the chapter list");
    int fits = 1;
    for (int i = 0; i < LORE_COUNT; i++) {
        panel_wide(1);
        lb_build_page(i);
        if (dex.content_lines >= PANEL_MAX_LINES) {
            fits = 0;
            printf("  %s is too long for the reader\n", LORE[i].title);
        }
        for (int k = 0; k < dex.content_lines; k++)
            if (text_width(dex.lines[k].text) > panel_cols * 8 - 8) {
                fits = 0;
                printf("  %s: a line is too wide\n", LORE[i].title);
                break;
            }
    }
    panel_wide(0);
    CHECK(fits, "every Lorebook page fits the reader");
    lb.chapter = LCH_BIOLOGY;
    tap(KEY_A);
    CHECK(lb.state == 1 && lb.count > 0, "A opens a chapter");
    while (lb.ids[lb.cursor] != LORE_KERNEL) tap(KEY_DOWN);
    tap(KEY_A);
    CHECK(lb.state == 2 && !lore_is_unread(LORE_KERNEL), "A opens a page and marks it read");
    for (int i = 0; i < 90; i++) step(KEY_DOWN);
    step(0);
    CHECK(dex.scroll_px > 0, "the page scrolls");
    CHECK((REG_DISPCNT & DCNT_BG2) && (REG_DISPCNT & DCNT_WIN0), "the reader shows the page panel");
    lore_learn(LORE_KERNEL + 1);
    {
        int before = lb.entry;
        for (int i = 0; i < 4 && lb.entry == before; i++) tap(KEY_RIGHT);
        CHECK(lb.entry != before && lb.state == 2 && (REG_DISPCNT & DCNT_BG2) && (REG_DISPCNT & DCNT_WIN0),
              "LEFT/RIGHT turn the page with the panel still shown");
    }
    tap(KEY_B);
    tap(KEY_B);
    tap(KEY_B);
    CHECK(game_mode == MODE_START_MENU, "B backs out of the Lorebook");

    /* options */
    start_cursor = start_index(SM_OPTIONS);
    tap(KEY_A);
    CHECK(game_mode == MODE_OPTIONS, "OPTIONS opens");
    int speed = opt.text_speed;
    tap(KEY_RIGHT);
    CHECK(opt.text_speed == (speed + 1) % TEXT_SPEED_COUNT, "LEFT/RIGHT change an option");
    tap(KEY_DOWN);
    tap(KEY_DOWN);
    int snd = opt.sound;
    tap(KEY_A);
    CHECK(opt.sound == !snd, "A toggles an option");
    opt.sound = 1;
    opt.text_speed = TEXT_MID;
    tap(KEY_B);
    CHECK(game_mode == MODE_START_MENU, "B leaves the options");

    /* team & summary */
    start_cursor = start_index(SM_KIN);
    tap(KEY_A);
    CHECK(game_mode == MODE_PARTY, "KIN opens the team screen");
    tap(KEY_DOWN);
    tap(KEY_A);
    CHECK(pscr.state == PS_SUBMENU, "A on a kin opens its options");
    tap(KEY_A);
    CHECK(game_mode == MODE_SUMMARY && sum.slot == 1, "SUMMARY shows that kin");
    tap(KEY_RIGHT);
    CHECK(sum.page == SUM_TRAITS, "the next page shows temperament, trait and potential");
    tap(KEY_RIGHT);
    tap(KEY_RIGHT);
    CHECK(sum.page == SUM_MOVES, "LEFT/RIGHT flip through the summary pages");
    tap(KEY_B);
    CHECK(game_mode == MODE_PARTY, "B returns to the team");
    pscr.cursor = 0;
    tap(KEY_A);
    choice.cursor = 1; /* SWITCH */
    tap(KEY_A);
    tap(KEY_DOWN);
    tap(KEY_DOWN);
    tap(KEY_A);
    CHECK(party[0].species == SP_GOLEMIT && party[2].species == SP_FLARIX, "SWITCH reorders the team");
    tap(KEY_B);
    CHECK(game_mode == MODE_START_MENU, "B leaves the team screen");

    /* bag */
    start_cursor = start_index(SM_BAG);
    tap(KEY_A);
    CHECK(game_mode == MODE_BAG && bscr.pocket == POCKET_SUPPLIES, "BAG opens on SUPPLIES");
    tap(KEY_RIGHT);
    tap(KEY_RIGHT);
    CHECK(bscr.pocket == POCKET_SHARDS && bscr.list[0] == ITEM_FROST_SHARD, "LEFT/RIGHT switch pockets");
    tap(KEY_LEFT);
    tap(KEY_LEFT);
    party[1].hp = 3;
    tap(KEY_A);
    tap(KEY_A);
    CHECK(game_mode == MODE_PARTY && pscr.ctx == PCTX_ITEM_FIELD, "USE asks which kin");
    tap(KEY_DOWN);
    tap(KEY_A);
    for (int f = 0; f < 300 && game_mode == MODE_PARTY; f++) step((f & 3) == 0 ? KEY_A : 0);
    CHECK(party[1].hp == 23 && bag[ITEM_TONIC] == 2, "the tonic heals the chosen kin");
    tap(KEY_B);
    tap(KEY_B);
    CHECK(game_mode == MODE_FIELD, "B twice closes everything");

    /* lantern shelf from the menu */
    storage_count = 0;
    tap(KEY_START);
    start_cursor = start_index(SM_SHELF);
    tap(KEY_A);
    CHECK(game_mode == MODE_PC, "SHELF opens the Lantern Shelf anywhere");
    tap(KEY_SELECT);
    CHECK(pc.deposit, "SELECT swaps between withdraw and deposit");
    tap(KEY_A);
    for (int f = 0; f < 200 && pc.state == 2; f++) step((f & 3) == 0 ? KEY_A : 0);
    CHECK(party_count == 2 && storage_count == 1, "a kin goes to the shelf");
    tap(KEY_SELECT);
    tap(KEY_A);
    for (int f = 0; f < 200 && pc.state == 2; f++) step((f & 3) == 0 ? KEY_A : 0);
    CHECK(party_count == 3 && storage_count == 0, "and comes back");
    tap(KEY_B);
    CHECK(game_mode == MODE_START_MENU, "B returns to the START menu");
}

/* ---------------- saves ---------------- */

static void test_saves(void)
{
    fresh_game();
    give_starter();
    party[0].temper = 3;
    party[0].trait = party[0].trait;
    lore_learn(LORE_POLARITONS);
    trainer_mark_beaten(0);
    trainer_mark_beaten(2);
    opt.text_speed = TEXT_FAST;
    field_enter_map(MAP_LAKE, 30, 17, DIR_LEFT);
    CHECK(save_write(), "saving works");
    Monster before = party[0];
    new_game();
    opt.text_speed = TEXT_MID;
    CHECK(save_load() == 4, "a version 4 save loads back");
    CHECK(cur_map == MAP_LAKE && player.x == 30 && party_count == 1 &&
          memcmp(&party[0], &before, sizeof(Monster)) == 0 && lore_is_known(LORE_POLARITONS) &&
          trainer_beaten(0) && !trainer_beaten(1) && trainer_beaten(2) && opt.text_speed == TEXT_FAST,
          "position, kin individuality, lore, wardens and options are restored");
    opt.text_speed = TEXT_MID;

    /* an old version 2 save migrates */
    static SaveDataV2 old;
    memset(&old, 0, sizeof(old));
    old.magic = SAVE_MAGIC;
    old.version = 2;
    old.party_count = 1;
    old.party[0].species = SP_PYREFOX;
    old.party[0].level = 20;
    old.party[0].moves[0] = M_SEAR_BITE;
    old.party[0].moves[1] = 0xFF;
    old.party[0].moves[2] = 0xFF;
    old.party[0].moves[3] = 0xFF;
    old.party[0].pp[0] = 10;
    old.party[0].hp = 30;
    old.party[0].max_hp = 60;
    old.bag[ITEM_LANTERN] = 7;
    old.money = 1234;
    old.caught[SP_PYREFOX] = 1;
    old.story_flags = 1u << FLAG_STARTER;
    old.checksum = fnv_bytes(&old, sizeof(old) - sizeof(old.checksum));
    memset(host_sram, 0xFF, sizeof(host_sram));
    sram_write(&old, (volatile u8 *)MEM_SRAM, sizeof(old));
    sram_write(&old, (volatile u8 *)MEM_SRAM + SAVE_V3_BACKUP_OFFSET, sizeof(old));
    CHECK(save_load() == 2, "a version 2 save is recognised");
    CHECK(party_count == 1 && party[0].species == SP_PYREFOX && party[0].level == 20 &&
          party[0].moves[0] == M_SEAR_BITE && bag[ITEM_LANTERN] == 7 && money == 1234 &&
          monster_valid(&party[0]) && cur_map == MAP_HOME,
          "its team, bag, coins and Almanac carry over");

    /* a version 3 save (the release before the expansion) migrates in full */
    static SaveDataV3 v3;
    memset(&v3, 0, sizeof(v3));
    v3.magic = SAVE_MAGIC;
    v3.version = 3;
    v3.party_count = 1;
    v3.party[0] = monster_make(SP_AXOLURK, 22);
    v3.storage_count = 2;
    v3.storage[0] = monster_make(SP_GOLEMIT, 9);
    v3.storage[1] = monster_make(SP_ZAPPET, 11);
    v3.storage[1].flags |= MF_LUSTROUS;
    v3.bag[ITEM_HUSH_BELL] = 2;
    v3.money = 4321;
    v3.caught[SP_ZAPPET] = v3.seen[SP_ZAPPET] = 1;
    v3.story_flags = (1u << FLAG_STARTER) | (1u << FLAG_SASH);
    v3.item_flags[1] = 1u << 3;          /* satchel 35 */
    v3.trainer_flags = 1u << 4;
    v3.lore_known[0] = 0x81;
    v3.options[0] = TEXT_FAST;
    v3.map = MAP_WOOD;
    v3.player_x = 20;
    v3.player_y = 8;
    v3.facing = DIR_UP;
    v3.checksum = fnv_bytes(&v3, sizeof(v3) - sizeof(v3.checksum));
    memset(host_sram, 0xFF, sizeof(host_sram));
    sram_write(&v3, (volatile u8 *)MEM_SRAM + SAVE_V3_BACKUP_OFFSET, sizeof(v3));
    CHECK(save_load() == 3, "a version 3 save is recognised (even from its backup slot)");
    CHECK(party_count == 1 && party[0].species == SP_AXOLURK && storage_count == 2 &&
          storage[1].species == SP_ZAPPET && (storage[1].flags & MF_LUSTROUS) &&
          bag[ITEM_HUSH_BELL] == 2 && money == 4321 && dex_caught[SP_ZAPPET] &&
          flag(FLAG_SASH) && item_taken(35) && !item_taken(34) && trainer_beaten(4) &&
          lore_known[0] == 0x81 && opt.text_speed == TEXT_FAST && cur_map == MAP_WOOD &&
          player.x == 20 && player.y == 8,
          "the whole version 3 game carries over");
    CHECK(save_write() && save_load() == 4, "and it saves back as version 4");
    opt.text_speed = TEXT_MID;
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    test_maps();
    test_movement();
    test_encounters();
    test_people();
    test_text();
    test_menus();
    test_saves();
    if (failures == 0) {
        printf("all field checks passed\n");
        return 0;
    }
    printf("%d check(s) FAILED\n", failures);
    return 1;
}
