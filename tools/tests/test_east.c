/*
 * REGION EAST tests (owner: W-EAST): Copperline Road, Lumen City and its
 * interiors, the Volt Hall, the Clockwork Spire, Elderwood Heart and the
 * Land Office. Edge contracts, every door both ways, region reachability
 * (with the Bramblewood boulders pushed), the Volt Hall puzzle (solvable,
 * gated, no soft-lock), people limits, wardens, the BIKE errand, the Hall
 * Master and the crest, and the Lumen market.
 */
#include "harness.h"

static const int EAST_MAPS[] = {
    MAP_COPPERLINE, MAP_LUMEN, MAP_ELDERWOOD, MAP_LAND_OFFICE, MAP_LUMEN_HEARTH, MAP_LUMEN_MARKET,
    MAP_VOLT_HALL, MAP_RESONANCE_WORKS, MAP_BIKE_SHOP, MAP_LUMEN_HOUSE, MAP_CLOCKWORK_SPIRE,
    MAP_LUMEN_INN, MAP_LUMEN_HOUSE_B,
};
#define EAST_COUNT ((int)(sizeof(EAST_MAPS) / sizeof(EAST_MAPS[0])))

static int npc_named(const char *name)
{
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].name && !strcmp(NPCS[i].name, name)) return i;
    return -1;
}

static int walk_ok(int x, int y) { return !(cell_attr(x, y) & (A_SOLID | A_WATER | A_LEDGE)); }

/* ---------------- edges ---------------- */

static int edge_open(int map, int side, int a, int b)
{
    map_load(map);
    for (int k = a; k <= b; k++) {
        int x = side == LINK_W ? 0 : side == LINK_E ? map_w - 1 : k;
        int y = side == LINK_N ? 0 : side == LINK_S ? map_h - 1 : k;
        if (!walk_ok(x, y)) return 0;
    }
    return 1;
}

static void test_edges(void)
{
    CHECK(edge_open(MAP_COPPERLINE, LINK_W, 17, 18) && edge_open(MAP_WOOD, LINK_E, 17, 18) &&
          MAPS[MAP_COPPERLINE].link[LINK_W] == MAP_WOOD && MAPS[MAP_WOOD].link[LINK_E] == MAP_COPPERLINE,
          "Copperline <-> Bramblewood at y 17-18");
    CHECK(edge_open(MAP_COPPERLINE, LINK_S, 20, 21) && MAPS[MAP_COPPERLINE].link[LINK_S] == MAP_ASHEN_FIELDS,
          "Copperline -> Ashen Fields at x 20-21");
    CHECK(edge_open(MAP_COPPERLINE, LINK_E, 20, 21) && edge_open(MAP_LUMEN, LINK_W, 20, 21),
          "Copperline <-> Lumen at y 20-21");
    CHECK(edge_open(MAP_LUMEN, LINK_N, 24, 25) && MAPS[MAP_LUMEN].link[LINK_N] == MAP_MOONVEIL,
          "Lumen -> Moonveil Path at x 24-25");
    CHECK(edge_open(MAP_LUMEN, LINK_E, 20, 21) && MAPS[MAP_LUMEN].link[LINK_E] == MAP_CINDER_ROAD,
          "Lumen -> Cinder Road at y 20-21");
    CHECK(edge_open(MAP_ELDERWOOD, LINK_N, 30, 31) && edge_open(MAP_WOOD, LINK_S, 30, 31),
          "Elderwood <-> Bramblewood at x 30-31");
    /* only the contracted cells are open on the region's outer edges */
    int tight = 1;
    map_load(MAP_LUMEN);
    for (int y = 0; y < map_h; y++)
        if ((y < 20 || y > 21) && (walk_ok(0, y) || walk_ok(map_w - 1, y))) tight = 0;
    for (int x = 0; x < map_w; x++)
        if ((x < 24 || x > 25) && walk_ok(x, 0)) tight = 0;
    map_load(MAP_COPPERLINE);
    for (int x = 0; x < map_w; x++)
        if ((x < 20 || x > 21) && walk_ok(x, map_h - 1)) tight = 0;
    CHECK(tight, "no stray openings on the contracted edges");
    const MapDef *w = &MAPS[MAP_WOOD];
    int boulders = 0;
    for (int i = 0; i < w->obj_count; i++)
        if (w->objs[i].kind == OBJ_BOULDER && w->objs[i].y == 33 && (w->objs[i].x == 30 || w->objs[i].x == 31))
            boulders++;
    CHECK(boulders == 2, "two STRENGTH boulders block Bramblewood's way south");
}

/* ---------------- doors ---------------- */

static void test_doors(void)
{
    int ok = 1, count = 0;
    for (int i = 0; i < WARP_COUNT; i++) {
        int dest = WARPS[i].dest, is_east = 0;
        for (int k = 0; k < EAST_COUNT; k++) is_east |= dest == EAST_MAPS[k] || WARPS[i].map == EAST_MAPS[k];
        if (!is_east) continue;
        count++;
        map_load(WARPS[i].map);
        if (!(cell_attr(WARPS[i].x, WARPS[i].y) & A_DOOR) || !walk_ok(WARPS[i].x, WARPS[i].y + 1)) ok = 0;
        map_load(dest);
        if (!(cell_attr(WARPS[i].dx, WARPS[i].dy) & A_EXIT)) {
            ok = 0;
            printf("  warp %d lands off the exit mat of %s\n", i, MAPS[dest].name);
        }
        /* the mat leads back out of this very door */
        int best = -1, bd = 1 << 30;
        for (int j = 0; j < WARP_COUNT; j++)
            if (WARPS[j].dest == dest) {
                int d = absi(WARPS[j].dx - WARPS[i].dx) + absi(WARPS[j].dy - WARPS[i].dy);
                if (d < bd) { bd = d; best = j; }
            }
        if (best != i) ok = 0;
    }
    CHECK(ok && count == 10, "every east door lands on its exit mat and the mat leads back out");

    /* walk in and back out of the Volt Hall for real */
    fresh_game();
    give_starter();
    field_enter_map(MAP_LUMEN, 7, 9, DIR_UP);
    hold(KEY_UP, 4);
    for (int f = 0; f < 30; f++) step(0);
    int in = cur_map == MAP_VOLT_HALL && player.x == 7 && player.y == 16;
    hold(KEY_DOWN, 12);
    for (int f = 0; f < 30; f++) step(0);
    CHECK(in && cur_map == MAP_LUMEN && player.x == 7 && player.y == 9, "you can walk into the Volt Hall and out again");
}

/* ---------------- region reachability ---------------- */

static void test_reach(void)
{
    /* map-level search: from Bramblewood's east edge, through reachable
     * edge cells and doors (boulders count as pushed: travel_attr is the
     * traversal owner's). */
    u8 seen[MAP_COUNT];
    int queue[MAP_COUNT], qx[MAP_COUNT], qy[MAP_COUNT], head = 0, tail = 0;
    memset(seen, 0, sizeof(seen));
    seen[MAP_COPPERLINE] = 1;
    queue[tail] = MAP_COPPERLINE; qx[tail] = 0; qy[tail++] = 17;
    seen[MAP_ELDERWOOD] = 1;
    queue[tail] = MAP_ELDERWOOD; qx[tail] = 30; qy[tail++] = 0;
    seen[MAP_LAND_OFFICE] = 1;
    queue[tail] = MAP_LAND_OFFICE; qx[tail] = 5; qy[tail++] = 8;
    int all_ok = 1;
    while (head < tail) {
        int m = queue[head], sx = qx[head], sy = qy[head];
        head++;
        map_load(m);
        flood_ex(sx, sy, FLOOD_SOLVED);   /* puzzles solved (traversal makes objects solid) */
        /* everything on the map is reachable from where you come in */
        for (int i = 0; i < NPC_COUNT; i++)
            if (NPCS[i].map == m) {
                int ok = reached_beside(NPCS[i].x, NPCS[i].y);
                for (int d = 0; d < 4 && !ok; d++) {
                    int cx = NPCS[i].x + DIR_DX[d], cy = NPCS[i].y + DIR_DY[d];
                    if ((cell_attr(cx, cy) & A_COUNTER) && reached(cx + DIR_DX[d], cy + DIR_DY[d])) ok = 1;
                }
                if (!ok) { all_ok = 0; printf("  %s: %s unreachable\n", MAPS[m].name, NPCS[i].name); }
            }
        for (int i = 0; i < MAPS[m].obj_count; i++) {
            const MapObj *o = &MAPS[m].objs[i];
            if (!reached(o->x, o->y) && !reached_beside(o->x, o->y)) {
                all_ok = 0;
                printf("  %s: object %d at %d,%d unreachable\n", MAPS[m].name, o->kind, o->x, o->y);
            }
        }
        for (int i = 0; i < WARP_COUNT; i++)
            if (WARPS[i].map == m && reached(WARPS[i].x, WARPS[i].y + 1) && !seen[WARPS[i].dest]) {
                int d = WARPS[i].dest;
                seen[d] = 1;
                queue[tail] = d; qx[tail] = WARPS[i].dx; qy[tail++] = WARPS[i].dy;
            }
        for (int l = 0; l < 4; l++) {
            int to = MAPS[m].link[l];
            if (to == MAP_NONE || seen[to]) continue;
            int is_east = 0;
            for (int k = 0; k < EAST_COUNT; k++) is_east |= to == EAST_MAPS[k];
            if (!is_east) continue;
            for (int k = 0; k < (l < 2 ? map_w : map_h); k++) {
                int x = l < 2 ? k : (l == LINK_W ? 0 : map_w - 1);
                int y = l < 2 ? (l == LINK_N ? 0 : map_h - 1) : k;
                if (!reached(x, y)) continue;
                seen[to] = 1;
                queue[tail] = to;
                qx[tail] = l < 2 ? x : (l == LINK_W ? MAPS[to].w - 1 : 0);
                qy[tail++] = l < 2 ? (l == LINK_N ? MAPS[to].h - 1 : 0) : y;
                break;
            }
        }
    }
    int every = 1;
    for (int k = 0; k < EAST_COUNT; k++)
        if (!seen[EAST_MAPS[k]]) { every = 0; printf("  %s never reached\n", MAPS[EAST_MAPS[k]].name); }
    CHECK(every, "every east map is reachable by walking and doors");
    CHECK(all_ok, "every person and map object in the east is reachable");

    /* the Spire's Crown is only reachable through the boulder's cell */
    map_load(MAP_CLOCKWORK_SPIRE);
    flood_ex(6, 18, FLOOD_SOLVED);
    int crown = reached(6, 4);
    CHECK(crown && (cell_attr(5, 7) & A_SOLID) && (cell_attr(7, 7) & A_SOLID) &&
          MAPS[MAP_CLOCKWORK_SPIRE].objs[0].kind == OBJ_BOULDER && MAPS[MAP_CLOCKWORK_SPIRE].objs[0].x == 6 &&
          MAPS[MAP_CLOCKWORK_SPIRE].objs[0].y == 9 && (cell_attr(5, 9) & A_SOLID) == 0 &&
          (cell_attr(7, 9) & A_SOLID) == 0,
          "the Spire's stair runs past one boulder that can be pushed aside");
}

/* ---------------- the Volt Hall puzzle ---------------- */

#define HW 15
#define HH 17
static u8 hall_seen[8][HH][HW];

static int barrier_at(int x, int y)
{
    const MapDef *m = &MAPS[MAP_VOLT_HALL];
    for (int i = 0; i < m->obj_count; i++)
        if (m->objs[i].kind == OBJ_BARRIER && m->objs[i].x == x && m->objs[i].y == y) return m->objs[i].arg;
    return -1;
}

static int switch_at(int x, int y)
{
    const MapDef *m = &MAPS[MAP_VOLT_HALL];
    for (int i = 0; i < m->obj_count; i++)
        if (m->objs[i].kind == OBJ_SWITCH && m->objs[i].x == x && m->objs[i].y == y) return m->objs[i].arg;
    return -1;
}

/* bits: a set bit = that group's barriers are LOWERED. */
static int hall_free(int x, int y, int bits)
{
    if (x < 0 || y < 0 || x >= HW || y >= HH) return 0;
    /* this solver models the barriers itself: read the map without traversal's objects */
    if (cell_attr_raw(x, y) & (A_SOLID | A_LEDGE)) return 0;
    if (npc_at(x, y) >= 0 || npc_kin_at(x, y) >= 0 || item_ball_at(x, y) >= 0) return 0;
    int b = barrier_at(x, y);
    return b < 0 || ((bits >> b) & 1);
}

static int hall_bfs(int sx, int sy, int bits0, int allow_switches)
{
    static int qx[8 * HH * HW], qy[8 * HH * HW], qb[8 * HH * HW];
    memset(hall_seen, 0, sizeof(hall_seen));
    int head = 0, tail = 0;
    hall_seen[bits0][sy][sx] = 1;
    qx[tail] = sx; qy[tail] = sy; qb[tail++] = bits0;
    while (head < tail) {
        int x = qx[head], y = qy[head], b = qb[head];
        head++;
        for (int d = 0; d < 4; d++) {
            int nx = x + DIR_DX[d], ny = y + DIR_DY[d];
            if (!hall_free(nx, ny, b)) continue;
            int nb = b, s = switch_at(nx, ny);
            if (s >= 0 && allow_switches) nb ^= 1 << s;
            if (hall_seen[nb][ny][nx]) continue;
            hall_seen[nb][ny][nx] = 1;
            qx[tail] = nx; qy[tail] = ny; qb[tail++] = nb;
        }
    }
    return tail;
}

static int hall_master_reached(void)
{
    for (int b = 0; b < 8; b++)
        for (int d = 0; d < 4; d++) {
            int x = VOLT_MASTER_X + DIR_DX[d], y = VOLT_MASTER_Y + DIR_DY[d];
            if (x >= 0 && y >= 0 && x < HW && y < HH && hall_seen[b][y][x]) return 1;
        }
    return 0;
}

static void test_volt_hall(void)
{
    map_load(MAP_VOLT_HALL);
    CHECK(map_w == HW && map_h == HH && (cell_attr(7, 16) & A_EXIT), "the Volt Hall is 15x17 with its mat at 7,16");
    int wall = 1;
    for (int x = 0; x < HW; x++)
        if (x != 7 && !(cell_attr(x, 4) & A_SOLID)) wall = 0;
    CHECK(wall, "pylons wall the maze (only the barrier gaps are open)");
    hall_bfs(7, 16, 0, 0);
    CHECK(!hall_master_reached(), "the Master can't be reached without using the switches");
    int states = hall_bfs(7, 16, 0, 1);
    CHECK(hall_master_reached(), "the Volt Hall is solvable");
    /* no soft-lock: from every reachable state you can still reach the Master */
    static u8 snap[8][HH][HW];
    memcpy(snap, hall_seen, sizeof(snap));
    int stuck = 0;
    for (int b = 0; b < 8; b++)
        for (int y = 0; y < HH; y++)
            for (int x = 0; x < HW; x++)
                if (snap[b][y][x]) {
                    hall_bfs(x, y, b, 1);
                    if (!hall_master_reached()) stuck++;
                }
    printf("  (%d reachable states)\n", states);
    CHECK(stuck == 0, "no reachable state of the Volt Hall is a soft-lock");
    /* the intended order works step by step: a, b, c */
    int ok = 1, bits = 0;
    static const u8 SEQ[3][2] = { { 4, 13 }, { 3, 9 }, { 11, 9 } };
    int sx = 7, sy = 16;
    for (int k = 0; k < 3; k++) {
        hall_bfs(sx, sy, bits, 0);
        if (!hall_seen[bits][SEQ[k][1]][SEQ[k][0]]) ok = 0;
        sx = SEQ[k][0]; sy = SEQ[k][1];
        bits ^= 1 << switch_at(sx, sy);
    }
    hall_bfs(sx, sy, bits, 0);
    CHECK(ok && hall_master_reached(), "pressing a, then b, then c opens the way to the Master");
}

/* ---------------- people, wardens, scripts ---------------- */

static void test_people(void)
{
    int limits = 1;
    for (int k = 0; k < EAST_COUNT; k++) {
        int m = EAST_MAPS[k], n = 0, chars = 0;
        u8 used[32];
        memset(used, 0, sizeof(used));
        for (int i = 0; i < NPC_COUNT; i++)
            if (NPCS[i].map == m) {
                n++;
                if (!used[NPCS[i].chr]) { used[NPCS[i].chr] = 1; chars++; }
            }
        if (n > 24 || chars > 7) { limits = 0; printf("  %s: %d people, %d characters\n", MAPS[m].name, n, chars); }
    }
    CHECK(limits, "at most 24 people and 7 characters per east map");

    int teams = 1;
    for (int t = TR_DUNN; t <= TR_COGSWORTH; t++) {
        const TrainerDef *d = &TRAINERS[t];
        if (d->count < 1 || d->count > 6) teams = 0;
        for (int i = 0; i < d->count; i++)
            if (d->species[i] >= SP_COUNT || d->level[i] < 10 || d->level[i] > 45) teams = 0;
    }
    CHECK(teams, "east warden teams have 1-6 kin at sane levels");
    CHECK(TRAINERS[TR_FARA].count == 6, "MASTER FARA fields six kin");
    int spark = 1;
    for (int i = 0; i < TRAINERS[TR_FARA].count; i++) {
        const Species *s = &SPECIES[TRAINERS[TR_FARA].species[i]];
        if (s->type1 != T_SPARK && s->type2 != T_SPARK) spark = 0;
    }
    CHECK(spark, "every kin on FARA's team is SPARK");
    int volt_lv = 0;
    for (int t = TR_IONE; t <= TR_BRISK; t++)
        for (int i = 0; i < TRAINERS[t].count; i++)
            if (TRAINERS[t].level[i] > volt_lv) volt_lv = TRAINERS[t].level[i];
    int fara_lo = 99;
    for (int i = 0; i < 6; i++)
        if (TRAINERS[TR_FARA].level[i] < fara_lo) fara_lo = TRAINERS[TR_FARA].level[i];
    CHECK(fara_lo >= 20 && volt_lv <= TRAINERS[TR_FARA].level[5], "the Hall's wardens lead up to the Master");

    /* lore sources all have entries */
    static const int SRC[] = { LSRC_MINER, LSRC_LUMEN_GUIDE, LSRC_LAMPLIGHTER, LSRC_TINKER, LSRC_VOLT_GUIDE,
                               LSRC_GROVE, LSRC_CLOCKMAKER };
    int lore_ok = 1;
    for (unsigned k = 0; k < sizeof(SRC) / sizeof(SRC[0]); k++) {
        int n = 0;
        for (int i = 0; i < LORE_COUNT; i++) n += LORE[i].source == SRC[k];
        if (!n) lore_ok = 0;
    }
    CHECK(lore_ok, "every east lore source has a Lorebook entry");
}

static void talk(int npc)
{
    map_load(NPCS[npc].map);
    script_run(npc);
    run_dialog(4000);
}

static void test_scripts(void)
{
    fresh_game();
    give_starter();
    money = 5000;
    int otto = npc_named("OTTO"), vex = npc_named("TINKER VEX");
    CHECK(otto >= 0 && vex >= 0, "OTTO and TINKER VEX are in Lumen");
    talk(otto);
    CHECK(quest_get(QUEST_BIKE_ERRAND) == 1 && !bag[ITEM_BIKE], "OTTO sends you to VEX with the spokes");
    talk(otto);
    CHECK(quest_get(QUEST_BIKE_ERRAND) == 1 && !bag[ITEM_BIKE], "and reminds you where VEX lives");
    talk(vex);
    CHECK(quest_get(QUEST_BIKE_ERRAND) == 2, "VEX takes the spokes");
    talk(otto);
    CHECK(quest_done(QUEST_BIKE_ERRAND) && bag[ITEM_BIKE] == 1, "OTTO hands over the BIKE");

    int miner = npc_named("OLD MINER HESK");
    int known = lore_known_count();
    talk(miner);
    CHECK(lore_known_count() == known + 1, "the old miner tells you about the Copperline");
    talk(miner);
    talk(miner);
    CHECK(flag(FLAG_MINER_GIFT) && bag[ITEM_IRON_ORE] >= 3, "and gives you ore once he's done talking");

    int clerk = -1;
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].map == MAP_LUMEN_MARKET && NPCS[i].script == SCR_LUMEN_SHOP) clerk = i;
    map_load(MAP_LUMEN_MARKET);
    script_run(clerk);
    for (int f = 0; f < 400 && game_mode != MODE_SHOP; f++) step((f & 3) == 0 ? KEY_A : 0);
    CHECK(game_mode == MODE_SHOP && shop_stock == LUMEN_STOCK && shop_stock_count == (int)sizeof(LUMEN_STOCK),
          "the Lumen market opens with its own stock");
    tap(KEY_B);
    run_dialog(400);
    game_mode = MODE_FIELD;

    int inn = npc_named("INNKEEPER");
    party[0].hp = 1;
    int m0 = money;
    talk(inn);
    CHECK(party[0].hp == party[0].max_hp && money == m0 - 50, "the inn lets you rest for 50 coins");

    /* the Hall Master */
    int fara = npc_named("MASTER FARA");
    map_load(MAP_VOLT_HALL);
    script_run(fara);
    for (int f = 0; f < 4000 && game_mode != MODE_BATTLE; f++) step((f & 3) == 0 ? KEY_A : 0);
    CHECK(game_mode == MODE_BATTLE && battle.kind == BK_TRAINER && battle.master && battle.team_count == 6,
          "FARA starts a Hall Master bout with six kin");
    CHECK(battle.scene == BSCENE_CITY, "on the city backdrop");
    battle_end_hook = 0;
    game_mode = MODE_FIELD;
    dialog_clear();
    fara_end(BR_WIN);
    run_dialog(4000);
    CHECK(flag(FLAG_VOLT_CREST) && travel_has_crest(CREST_VOLT) && trainer_beaten(TR_FARA) &&
          quest_done(QUEST_VOLT_HALL) && lore_is_known(LORE_VOLT_CREST),
          "beating FARA awards the VOLT CREST");
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    test_edges();
    test_doors();
    test_reach();
    test_volt_hall();
    test_people();
    test_scripts();
    if (failures == 0) {
        printf("all east checks passed\n");
        return 0;
    }
    printf("%d east check(s) FAILED\n", failures);
    return 1;
}
