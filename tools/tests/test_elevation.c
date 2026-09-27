/*
 * Elevation checks (src/game/elev.c, docs/ELEVATION.md) on the TEST HEIGHTS
 * map (src/game/world/elev/) and every map with a height layer: decoding
 * (faces, stairs, ledges, mouths, hidden passages), the step rules, stairs
 * up and down (north, south and side stairs), ledges, the bridge walked over
 * east-west and under north-south, the tunnel, the hidden passage, the OBJ
 * priority of everyone above / under / in front of the deck, the follower,
 * people and wild kin keeping to their level, the save, the level-aware
 * reachability flood and the elevation art of the tilesets.
 */
#include "harness.h"

static const u16 DIR_KEY[4] = { KEY_DOWN, KEY_UP, KEY_LEFT, KEY_RIGHT };

static void wait_still(void)
{
    for (int f = 0; f < 400 && (player.moving || warp.active || tv.busy); f++) step(0);
}

static void go(int dir)
{
    player.facing = (u8)dir;
    player_turn_timer = 0;
    for (int f = 0; f < 4 && !player.moving; f++) step(DIR_KEY[dir]);
    wait_still();
    dialog_clear();
}

static void walk(int dir, int n)
{
    while (n--) go(dir);
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

static int at(int x, int y, int level)
{
    return player.x == x && player.y == y && player.level == level;
}

/* OBJ priority the field gave the player's sprite this frame. */
static int player_obj_prio(void)
{
    oam_count = 0;
    field_draw_sprites();
    for (int i = 0; i < oam_count; i++) {
        u16 a2 = oam_shadow[i * 4 + 2];
        if ((a2 & 1023) == OT_PLAYER) return (a2 >> 10) & 3;
    }
    return -1;
}

static int npc_named(const char *name)
{
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].map == MAP_EV_TEST && NPCS[i].name && !strcmp(NPCS[i].name, name)) return i;
    return -1;
}

/* Every map with a height layer: its stairs, bridges and tunnels join
 * levels that exist, and its tileset has elevation art. */
static void lint_maps(void)
{
    int ok = 1, art = 1, maps = 0;
    for (int m = 0; m < MAP_COUNT; m++) {
        const MapDef *d = &MAPS[m];
        if (!d->elev) continue;
        maps++;
        if (!TILESETS[d->tileset].elev) {
            art = 0;
            printf("  %s: tileset %s has no elevation art\n", d->name, TILESETS[d->tileset].name);
            continue;
        }
        for (int y = 0; y < d->h; y++)
            if ((int)strlen(d->elev[y]) != d->w) {
                ok = 0;
                printf("  %s: elevation row %d is %d wide\n", d->name, y, (int)strlen(d->elev[y]));
            }
        map_load(m);
        for (int y = 0; y < map_h; y++)
            for (int x = 0; x < map_w; x++) {
                char c = d->elev[y][x];
                if (!((c >= '0' && c <= '3') || c == '^' || c == 'v' || c == '<' || c == '>' || c == '_')) {
                    ok = 0;
                    printf("  %s: bad elevation character '%c' at %d,%d\n", d->name, c, x, y);
                }
                u16 e = elev_at(x, y);
                int k = EV_KIND(e);
                if (EK_IS_STAIRS(k)) {
                    int up = EK_UP(k);
                    int hx = x + DIR_DX[up], hy = y + DIR_DY[up], lx = x - DIR_DX[up], ly = y - DIR_DY[up];
                    u16 h = elev_at(hx, hy), l = elev_at(lx, ly);
                    int hlo = EK_IS_STAIRS(EV_KIND(h)) ? EV_LO(h) : EV_LO(h);
                    int llo = EK_IS_STAIRS(EV_KIND(l)) ? EV_LO(l) + 1 : EV_LO(l);
                    if (hlo != EV_LO(e) + 1 || llo != EV_LO(e)) {
                        ok = 0;
                        printf("  %s: stairs at %d,%d do not join %d and %d\n", d->name, x, y, EV_LO(e),
                               EV_LO(e) + 1);
                    }
                }
                if (c == '_' && k != EK_LEDGE) {
                    ok = 0;
                    printf("  %s: ledge at %d,%d has no rise above it\n", d->name, x, y);
                }
            }
        for (int i = 0; i < d->feat_count; i++) {
            const ElevFeat *f = &d->feats[i];
            if (f->kind < EF_BRIDGE_H || f->kind > EF_HIDDEN || f->x + f->w > d->w || f->y + f->h > d->h) {
                ok = 0;
                printf("  %s: feature %d does not fit\n", d->name, i);
                continue;
            }
            if (f->kind == EF_BRIDGE_H || f->kind == EF_BRIDGE_V) {
                /* both ends of the deck meet ground at the deck's height */
                int hz = f->kind == EF_BRIDGE_H, deck = EV_HI(elev_at(f->x, f->y));
                for (int k = 0; k < (hz ? f->h : f->w); k++) {
                    int ax = hz ? f->x - 1 : f->x + k, ay = hz ? f->y + k : f->y - 1;
                    int bx = hz ? f->x + f->w : f->x + k, by = hz ? f->y + k : f->y + f->h;
                    if (EV_VIS(elev_at(ax, ay)) != deck || EV_VIS(elev_at(bx, by)) != deck) {
                        ok = 0;
                        printf("  %s: bridge %d does not meet height %d at both ends\n", d->name, i, deck);
                        break;
                    }
                }
            }
        }
    }
    CHECK(ok, "every height layer is well formed: stairs join their levels, bridges meet ground at deck height");
    CHECK(art, "every map with a height layer uses a tileset with elevation art");
    CHECK(maps >= 2, "the test map and Maple Village have height layers");
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    fresh_game();
    give_starter();
    flag_set(FLAG_STORM_CALMED);

    /* ---------------- decoding ---------------- */
    map_load(MAP_EV_TEST);
    CHECK(map_elevated && TILESETS[MAPS[MAP_EV_TEST].tileset].elev, "TEST HEIGHTS has a height layer and art");
    CHECK(EV_KIND(elev_at(8, 14)) == EK_FACE && (cell_attr(8, 14) & A_SOLID),
          "the row under a plateau is a cliff face, and solid");
    CHECK(EV_KIND(elev_at(7, 20)) == EK_GROUND && EV_LO(elev_at(7, 8)) == 1 && EV_LO(elev_at(22, 6)) == 2,
          "heights decode: ground 0, plateau 1, mesa 2");
    CHECK(EV_KIND(elev_at(22, 9)) == EK_FACE && EV_VIS(elev_at(22, 9)) == 1,
          "the mesa's face stands on the plateau (drawn at height 1)");
    CHECK(EV_KIND(elev_at(6, 14)) == EK_STAIRS + DIR_UP && !(cell_attr(6, 14) & A_SOLID) &&
              EV_LO(elev_at(6, 14)) == 0,
          "stairs in a face are open and start at the ground below");
    CHECK(EV_KIND(elev_at(23, 9)) == EK_STAIRS + DIR_UP && EV_LO(elev_at(23, 9)) == 1,
          "the mesa stairs climb from 1 to 2");
    CHECK(EV_KIND(elev_at(12, 6)) == EK_STAIRS + DIR_LEFT && EV_KIND(elev_at(18, 4)) == EK_STAIRS + DIR_DOWN,
          "side stairs and stairs down the north side decode");
    CHECK(EV_KIND(elev_at(26, 14)) == EK_LEDGE && (cell_attr(26, 14) & A_LEDGE) && !(cell_attr(26, 14) & A_SOLID),
          "a '_' under a rise is a ledge");
    CHECK(EV_COVER(elev_at(4, 14)) == EC_MOUTH && !(cell_attr(4, 14) & A_SOLID),
          "the face under a tunnel is its open mouth");
    CHECK(EV_COVER(elev_at(4, 8)) == EC_TUNNEL && EV_LO(elev_at(4, 8)) == 0 && EV_HI(elev_at(4, 8)) == 1,
          "tunnel cells: ground 0, walkable top 1");
    CHECK(EV_COVER(elev_at(13, 9)) == EC_BRIDGE_H && EV_HI(elev_at(13, 9)) == 1 && EV_LO(elev_at(13, 9)) == 0,
          "bridge cells: ground 0 below a deck at 1");
    CHECK(EV_COVER(elev_at(24, 19)) == EC_HIDDEN && !(cell_attr(24, 19) & A_SOLID) && (cell_attr(24, 18) & A_SOLID),
          "the hidden passage is open; the trees around it are not");

    /* ---------------- step rules ---------------- */
    int nl;
    CHECK(elev_enter(11, 7, 1, DIR_RIGHT, &nl) == ELEV_BLOCK, "no stepping off a plateau's side");
    CHECK(elev_enter(13, 7, 0, DIR_LEFT, &nl) == ELEV_FLOOR && nl == 0 &&
              elev_enter(12, 7, 0, DIR_LEFT, &nl) == ELEV_BLOCK,
          "no climbing a plateau's side from below");
    CHECK(elev_enter(11, 9, 1, DIR_RIGHT, &nl) == ELEV_TOP && nl == 1, "the bridge deck is entered from its end");
    CHECK(elev_enter(13, 8, 0, DIR_DOWN, &nl) == ELEV_FLOOR && nl == 0, "and walked under from the gorge");
    CHECK(elev_enter(13, 9, 1, DIR_DOWN, &nl) == ELEV_BLOCK && elev_enter(13, 9, 1, DIR_UP, &nl) == ELEV_BLOCK,
          "the deck's railings stop you walking off its sides");
    CHECK(elev_enter(6, 15, 0, DIR_LEFT, &nl) == ELEV_FLOOR && elev_enter(5, 15, 0, DIR_RIGHT, &nl) == ELEV_FLOOR &&
              elev_enter(5, 14, 0, DIR_RIGHT, &nl) == ELEV_BLOCK && elev_enter(7, 13, 1, DIR_LEFT, &nl) == ELEV_FLOOR,
          "stairs are entered only from their ends");
    CHECK(elev_enter(26, 15, 0, DIR_UP, &nl) == ELEV_BLOCK, "a ledge can't be climbed");

    /* ---------------- stairs, walking ---------------- */
    opt.follower = 1;
    enter(MAP_EV_TEST, 6, 16, DIR_UP);
    CHECK(at(6, 16, 0), "enter below the west plateau on the ground");
    go(DIR_UP);
    CHECK(at(6, 15, 0), "walk to the stairs");
    go(DIR_UP);
    CHECK(at(6, 14, 0), "onto the stairs from their low end");
    go(DIR_UP);
    CHECK(at(6, 13, 1), "up the stairs onto the plateau (level 1)");
    go(DIR_LEFT);
    CHECK(at(5, 13, 1), "walk on the plateau");
    go(DIR_DOWN);
    CHECK(at(5, 13, 1), "the cliff edge stops you");
    go(DIR_RIGHT);
    go(DIR_DOWN);
    go(DIR_DOWN);
    CHECK(at(6, 15, 0), "and back down the stairs to the ground");
    go(DIR_UP);
    go(DIR_UP);
    walk(DIR_UP, 3);
    CHECK(at(6, 10, 1), "up to the bridge path");
    CHECK(follower.a.level == 1, "the follower climbed too");

    /* ---------------- the bridge, on top ---------------- */
    walk(DIR_RIGHT, 5);
    CHECK(at(11, 10, 1), "to the bridge's west end");
    go(DIR_RIGHT);
    CHECK(at(12, 10, 1), "onto the deck, still level 1");
    CHECK(player_obj_prio() == 1, "on the deck the player draws over it (OBJ priority 1)");
    go(DIR_DOWN);
    CHECK(at(12, 10, 1), "the railing stops a step off the deck's side");
    walk(DIR_RIGHT, 2);
    CHECK(at(14, 10, 1), "cross the deck over the stream");
    CHECK(follower.a.level == 1 && follower.a.x == 13 && player_obj_prio() == 1,
          "the follower crosses on top as well");
    walk(DIR_RIGHT, 2);
    CHECK(at(16, 10, 1), "off the deck onto the east plateau");

    /* ---------------- the bridge, underneath ---------------- */
    enter(MAP_EV_TEST, 13, 16, DIR_UP);
    CHECK(at(13, 16, 0), "enter the gorge path below");
    walk(DIR_UP, 3);
    CHECK(at(13, 13, 0), "walk north along the gorge");
    walk(DIR_UP, 1);
    CHECK(at(13, 12, 0), "past the surveyor");
    go(DIR_UP);
    CHECK(at(13, 11, 0) && player_obj_prio() == 1, "just south of the bridge the player is in front of it");
    go(DIR_UP);
    CHECK(at(13, 10, 0), "under the bridge: level 0");
    CHECK(player_obj_prio() == 2, "under the deck the player is drawn under it (OBJ priority 2)");
    go(DIR_UP);
    CHECK(at(13, 9, 0) && player_obj_prio() == 2, "still under");
    CHECK(follower.a.x == 13 && follower.a.y == 10 && follower.a.level == 0 && elev_obj_prio(&follower.a) == 2,
          "the follower passes under too");
    go(DIR_UP);
    CHECK(at(13, 8, 0) && player_obj_prio() == 2, "out from under the bridge on the far side");
    go(DIR_RIGHT);
    CHECK(at(13, 8, 0), "the stream stops you (no surfing)");

    /* ---------------- side stairs and north stairs ---------------- */
    walk(DIR_UP, 2);
    CHECK(at(13, 6, 0), "up the gorge to the side stairs");
    go(DIR_LEFT);
    CHECK(at(12, 6, 0), "onto the side stairs from their low (east) end");
    go(DIR_UP);
    CHECK(at(12, 6, 0), "side stairs can't be left sideways");
    go(DIR_LEFT);
    CHECK(at(11, 6, 1), "up the side stairs onto the west plateau");
    enter(MAP_EV_TEST, 18, 2, DIR_DOWN);
    walk(DIR_DOWN, 3);
    CHECK(at(18, 5, 1), "down-facing stairs lead from the north up onto the east plateau");

    /* ---------------- mesa ---------------- */
    enter(MAP_EV_TEST, 23, 11, DIR_UP);
    CHECK(player.level == 1, "on the east plateau");
    walk(DIR_UP, 3);
    CHECK(at(23, 8, 2), "up the mesa stairs to level 2");
    int kid = npc_named("KID"), hiker = npc_named("HIKER"), surveyor = npc_named("SURVEYOR");
    CHECK(kid >= 0 && npc_state[kid].level == 2 && npc_state[hiker].level == 1 && npc_state[surveyor].level == 0,
          "people stand on the level of their cell");
    for (int f = 0; f < 3000; f++) npcs_update();
    CHECK(EV_LO(elev_at(npc_state[kid].x, npc_state[kid].y)) == 2 && npc_state[kid].level == 2,
          "a wandering kid stays up on the mesa");

    /* ---------------- ledges ---------------- */
    enter(MAP_EV_TEST, 26, 12, DIR_DOWN);
    CHECK(player.level == 1, "near the ledges on the plateau");
    go(DIR_DOWN);
    go(DIR_DOWN);
    CHECK(at(26, 15, 0), "hop off the ledge down to the ground (level 0)");
    go(DIR_UP);
    CHECK(at(26, 15, 0), "and the ledge can't be climbed");

    /* ---------------- tunnel ---------------- */
    enter(MAP_EV_TEST, 4, 16, DIR_UP);
    go(DIR_UP);
    go(DIR_UP);
    CHECK(at(4, 14, 0), "into the tunnel mouth");
    go(DIR_UP);
    CHECK(at(4, 13, 0) && player_obj_prio() == 2, "inside the tunnel, under the plateau (drawn under it)");
    go(DIR_LEFT);
    CHECK(at(4, 13, 0), "the tunnel walls hold");
    walk(DIR_UP, 9);
    CHECK(at(4, 4, 0), "out of the tunnel's north end");
    enter(MAP_EV_TEST, 3, 8, DIR_RIGHT);
    CHECK(player.level == 1, "on the plateau west of the tunnel");
    walk(DIR_RIGHT, 2);
    CHECK(at(5, 8, 1), "walk over the tunnel on top");

    /* ---------------- hidden passage ---------------- */
    enter(MAP_EV_TEST, 22, 19, DIR_RIGHT);
    go(DIR_RIGHT);
    CHECK(at(23, 19, 0), "to the tree wall");
    go(DIR_RIGHT);
    CHECK(at(24, 19, 0), "into the trees: a hidden passage");
    CHECK((elev_at(24, 19) & EV_FOUND) && emote.npc == -1 && emote.timer > 0, "finding it rustles and shows a '!'");
    CHECK(player_obj_prio() == 2, "the trees are drawn over the player in the passage");
    walk(DIR_RIGHT, 2);
    CHECK(at(26, 19, 0), "through to the nook");
    go(DIR_DOWN);
    go(DIR_RIGHT);
    tap(KEY_A);
    run_dialog(400);
    int satchel = -1;
    for (int i = 0; i < ITEM_BALL_COUNT; i++)
        if (ITEM_BALLS[i].map == MAP_EV_TEST && ITEM_BALLS[i].x == 27 && ITEM_BALLS[i].y == 20) satchel = i;
    CHECK(satchel >= 0 && item_taken(satchel), "the satchel behind the passage can be taken");

    /* ---------------- interaction and wild kin across levels ---------------- */
    enter(MAP_EV_TEST, 11, 12, DIR_RIGHT);
    CHECK(player.level == 1 && npc_at(12, 13) >= 0, "above the surveyor, across the cliff");
    KinActor k = { 0 };
    k.a.x = 12;
    k.a.y = 12;
    k.a.level = 0;
    CHECK(!wild_reaches_player(&k), "a wild kin below the cliff can't reach the player above");
    k.a.x = 10;
    k.a.level = 1;
    CHECK(wild_reaches_player(&k), "one beside the player on the plateau can");

    int mesa = -1;
    for (int i = 0; i < ITEM_BALL_COUNT; i++)
        if (ITEM_BALLS[i].map == MAP_EV_TEST && ITEM_BALLS[i].x == 21 && ITEM_BALLS[i].y == 5) mesa = i;
    enter(MAP_EV_TEST, 21, 4, DIR_DOWN);
    tap(KEY_A);
    run_dialog(400);
    CHECK(mesa >= 0 && player.level == 0 && !item_taken(mesa), "a satchel up on the mesa can't be taken from below");
    enter(MAP_EV_TEST, 21, 6, DIR_UP);
    tap(KEY_A);
    run_dialog(400);
    CHECK(player.level == 2 && item_taken(mesa), "but can from beside it on the mesa");

    /* ---------------- render ---------------- */
    enter(MAP_EV_TEST, 13, 16, DIR_UP);
    field_redraw_cell(13, 9);
    render_cell(13, 9);
    u16 *top = VRAM_MAP(SB_FIELD_TOP), *mid = VRAM_MAP(SB_PANEL);
    int idx = (9 & 15) * 64 + (13 & 15) * 2;
    CHECK(top[idx] && top[idx + 1] && top[idx + 32] && top[idx + 33], "the deck is drawn on the top layer (BG3)");
    field_redraw_cell(8, 14);
    render_cell(8, 14);
    idx = (14 & 15) * 64 + (8 & 15) * 2;
    CHECK(mid[idx] && mid[idx + 32], "cliff faces are drawn on the decor layer (BG2)");
    field_redraw_cell(25, 19);
    render_cell(25, 19);
    idx = (19 & 15) * 64 + (25 & 15) * 2;
    CHECK((top[idx] || top[idx + 32]) && !mid[idx + 32], "a hidden cell's trunk moves to the top layer");

    /* ---------------- save / load ---------------- */
    enter(MAP_EV_TEST, 11, 9, DIR_RIGHT);
    go(DIR_RIGHT);
    go(DIR_RIGHT);
    CHECK(at(13, 9, 1), "stand on the deck");
    static u8 sram[32768];
    memset(sram, 0xFF, sizeof(sram));
    CHECK(save_write_to(sram), "save on the deck");
    player.level = 0;
    CHECK(save_load_from(sram) == SAVE_VERSION && at(13, 9, 1), "loading puts you back on the deck (level 1)");
    enter(MAP_EV_TEST, 13, 8, DIR_DOWN);
    go(DIR_DOWN);
    CHECK(at(13, 9, 0), "stand under the deck");
    save_write_to(sram);
    player.level = 1;
    CHECK(save_load_from(sram) == SAVE_VERSION && at(13, 9, 0), "loading puts you back under it (level 0)");
    static SaveData old;
    save_capture(&old);
    old.level = 0;               /* a save from before elevation */
    old.player_x = 13;
    old.player_y = 9;
    old.facing = DIR_LEFT;
    old.checksum_v6 = save_checksum(&old);
    save_apply(&old);
    CHECK(at(13, 9, 1), "an old save on a bridge cell derives the level from the facing (along the deck: on top)");
    old.facing = DIR_UP;
    old.checksum_v6 = save_checksum(&old);
    save_apply(&old);
    CHECK(at(13, 9, 0), "(across it: underneath)");
    old.player_x = 7;
    old.player_y = 8;
    old.checksum_v6 = save_checksum(&old);
    save_apply(&old);
    CHECK(at(7, 8, 1), "and from the cell elsewhere");

    /* ---------------- reachability ---------------- */
    map_load(MAP_EV_TEST);
    flood_ex_lv(13, 16, 0, FLOOD_WALK);
    CHECK(reached_lv(13, 9, 0) && reached_lv(13, 9, 1), "the flood reaches the bridge cells both under and on top");
    CHECK(reached_lv(4, 8, 0) && reached_lv(4, 8, 1), "and the tunnel both inside and over it");
    CHECK(reached_lv(22, 5, 2) && !reached_lv(22, 5, 0) && !reached_lv(22, 5, 1), "the mesa only at its height");
    CHECK(reached_lv(26, 19, 0), "the nook through the hidden passage");
    CHECK(!reached(8, 14) && !reached(26, 14), "never onto a face or a ledge");
    flood_ex_lv(22, 16, 0, FLOOD_WALK);
    CHECK(reached_lv(26, 12, 1), "up from the ledges' foot by the stairs");

    lint_maps();

    /* ---------------- art ---------------- */
    int art_ok = 1;
    for (int t = 0; t < TS_COUNT; t++) {
        const ElevArt *ea = TILESETS[t].elev;
        if (!ea) continue;
        for (int c = 0; c < 4; c++) {
            for (int v = 0; v < 4; v++)
                if (!ea->face[c][v] || !ea->deck_h[c][v] || !ea->deck_v[c][v] || !ea->stairs[v][c]) art_ok = 0;
            for (int v = 1; v < 5; v++)
                if (!ea->rim[c][v] && !(c >= 2 && v == 3)) art_ok = 0;
            if (!ea->mouth[c] || (ea->face[c][0] & 1023) >= TILESETS[t].tile_count) art_ok = 0;
        }
    }
    CHECK(art_ok && TILESETS[TS_TOWN].elev && TILESETS[TS_WILD].elev,
          "the town and wild tilesets carry complete elevation art");

    if (failures) {
        printf("%d elevation check(s) failed\n", failures);
        return 1;
    }
    printf("all elevation checks passed\n");
    return 0;
}
