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
    MAP_LUMEN_INN, MAP_LUMEN_HOUSE_B, MAP_BROOKMILL_TRAIL, MAP_BROOKMILL,
    MAP_BROOKMILL_MILL, MAP_BROOKMILL_HOUSE, MAP_BROOKMILL_REST, MAP_COPPER_MINE,
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

/* Lumen City's heights (docs/ELEVATION.md): the Boulevard over the Cut, the
 * towpath under it, the conduit under the Crown walk to the Well garden. */
static void test_lumen_heights(void)
{
    /* every decor kind of an east map is really loaded (the loader skips a
     * kind that no longer fits after the tileset and its elevation art) */
    int decor_ok = 1;
    for (int k = 0; k < EAST_COUNT; k++) {
        map_load(EAST_MAPS[k]);
        field_load_tileset();
        const MapDef *m = &MAPS[EAST_MAPS[k]];
        for (int i = 0; i < m->decor_count; i++)
            if (!decor_base[m->decor[i].kind]) {
                decor_ok = 0;
                printf("  %s: decor kind %d does not fit\n", m->name, m->decor[i].kind);
                break;
            }
    }
    CHECK(decor_ok, "every decor kind on the east maps fits in VRAM next to the tileset");

    flag_set(FLAG_LANTERN_CREST);
    map_load(MAP_LUMEN);
    flood_ex(24, 0, FLOOD_SOLVED);
    CHECK(reached_lv(41, 20, 1) && reached_lv(42, 20, 0) && reached_lv(42, 20, 1) && reached_lv(44, 20, 1),
          "Lumen: the Boulevard crosses the Cut on the bridge, the towpath runs under it");
    CHECK(reached_lv(47, 17, 0) && reached_lv(30, 9, 2) && reached_lv(30, 9, 3) && reached_lv(32, 6, 2),
          "Lumen: the Works yard lies down in the Cut; the conduit runs under the Crown walk to the Well garden");
    CHECK(elev_level_at(24, 11, -1, -1) == 2 && elev_level_at(24, 5, -1, -1) == 3 &&
              elev_level_at(24, 30, -1, -1) == 0 && elev_level_at(9, 18, -1, -1) == 1,
          "Lumen: canal quarter 0, west terrace 1, Beacon terrace 2, the Crown 3");
    flag_clear(FLAG_LANTERN_CREST);
}

static int accord_warp_registered(void)
{
    for (int i = 0; i < WARP_COUNT; i++)
        if (WARPS[i].map == MAP_COPPERLINE && WARPS[i].x == 20 && WARPS[i].y == 34 &&
            WARPS[i].dest == MAP_ACCORD_GATE && WARPS[i].dx == 6 && WARPS[i].dy == 8)
            return 1;
    return 0;
}

static void test_edges(void)
{
    CHECK(edge_open(MAP_COPPERLINE, LINK_W, 17, 18) && edge_open(MAP_WOOD, LINK_E, 17, 18) &&
          edge_open(MAP_BROOKMILL_TRAIL, LINK_W, 17, 18) &&
          edge_open(MAP_BROOKMILL_TRAIL, LINK_E, 17, 18) &&
          edge_open(MAP_BROOKMILL, LINK_W, 17, 18) && edge_open(MAP_BROOKMILL, LINK_E, 17, 18) &&
          MAPS[MAP_BROOKMILL_TRAIL].link[LINK_E] == MAP_BROOKMILL &&
          MAPS[MAP_BROOKMILL].link[LINK_E] == MAP_COPPERLINE &&
          MAPS[MAP_COPPERLINE].link[LINK_W] == MAP_BROOKMILL &&
          MAPS[MAP_WOOD].link[LINK_E] == MAP_BROOKMILL_TRAIL,
          "Bramblewood -> Brookmill Trail -> Brookmill -> Copperline at y 17-18");
    CHECK(MAPS[MAP_COPPERLINE].link[LINK_S] == MAP_NONE &&
          accord_warp_registered(),
          "Copperline G5 uses an enterable door at (20,34), not a south edge");
    CHECK(edge_open(MAP_COPPERLINE, LINK_E, 20, 21) && edge_open(MAP_LUMEN, LINK_W, 20, 21),
          "Copperline <-> Lumen at y 20-21");
    CHECK(!edge_open(MAP_LUMEN, LINK_N, 24, 25) && MAPS[MAP_LUMEN].link[LINK_N] == MAP_MISTFEN,
          "G6 closes the Lumen -> Mistfen edge before Lantern");
    CHECK(!edge_open(MAP_LUMEN, LINK_E, 20, 21) && MAPS[MAP_LUMEN].link[LINK_E] == MAP_CINDER_CROSSING,
          "G3 closes the Lumen -> Cinder Crossing edge before Tide");
    CHECK(edge_open(MAP_ELDERWOOD, LINK_N, 30, 31) && edge_open(MAP_WOOD, LINK_S, 30, 31),
          "Elderwood and Bramblewood retain their edge geometry; the interior thorns and boulder gate passage");
    map_load(MAP_WOOD);
    CHECK(!flood_open(43, 17, FLOOD_WALK) && !flood_open(43, 18, FLOOD_WALK),
          "G1 seals both Bramblewood departures before the calm");
    map_load(MAP_ELDERWOOD);
    CHECK(!flood_open(30, 2, FLOOD_WALK) && !flood_open(31, 2, FLOOD_WALK),
          "postgame thorns seal the interior Elderwood route before Ossurex");
    flag_set(FLAG_STORM_CALMED);
    map_load(MAP_WOOD);
    CHECK(flood_open(43, 17, FLOOD_WALK) && flood_open(43, 18, FLOOD_WALK),
          "G1 opens both Bramblewood exits after the calm");
    flag_set(FLAG_TIDE_CREST);
    CHECK(edge_open(MAP_LUMEN, LINK_E, 20, 21), "G3 opens the Cinder edge after Tide");
    flag_set(FLAG_LANTERN_CREST);
    CHECK(edge_open(MAP_LUMEN, LINK_N, 24, 25), "G6 opens the Mistfen edge after Lantern");
    flag_set(FLAG_CREST_ANVIL);
    flag_set(FLAG_OSSUREX_ANSWERED);
    map_load(MAP_ELDERWOOD);
    CHECK(flood_open(30, 2, FLOOD_WALK) && flood_open(31, 2, FLOOD_WALK),
          "postgame Elderwood interior opens after Ossurex");
    flag_clear(FLAG_STORM_CALMED); flag_clear(FLAG_TIDE_CREST);
    flag_clear(FLAG_LANTERN_CREST); flag_clear(FLAG_CREST_ANVIL);
    flag_clear(FLAG_OSSUREX_ANSWERED);
    /* only the contracted cells are open on the region's outer edges */
    int tight = 1;
    map_load(MAP_LUMEN);
    for (int y = 0; y < map_h; y++)
        if ((y < 20 || y > 21) && (walk_ok(0, y) || walk_ok(map_w - 1, y))) tight = 0;
    for (int x = 0; x < map_w; x++)
        if ((x < 24 || x > 25) && walk_ok(x, 0)) tight = 0;
    map_load(MAP_COPPERLINE);
    for (int x = 0; x < map_w; x++)
        if ((x < 17 || x > 21) && walk_ok(x, map_h - 1)) tight = 0;
    CHECK(tight, "no stray openings on the contracted edges");
    const MapDef *w = &MAPS[MAP_WOOD];
    int boulders = 0;
    for (int i = 0; i < w->obj_count; i++)
        if (w->objs[i].kind == OBJ_BOULDER && w->objs[i].y == 33 && (w->objs[i].x == 30 || w->objs[i].x == 31))
            boulders++;
    CHECK(boulders == 1, "a STRENGTH boulder blocks Bramblewood's way south (test_puzzles proves the push)");
}

/* ---------------- doors ---------------- */

static void test_doors(void)
{
    map_load(MAP_COPPERLINE);
    CHECK(!(cell_attr(20, 34) & A_DOOR), "G5 checkpoint door is sealed before Rime");
    flag_set(FLAG_RIME_CREST);
    map_load(MAP_COPPERLINE);
    CHECK(cell_attr(20, 34) & A_DOOR, "G5 checkpoint door opens after Rime");
    int ok = 1, count = 0;
    for (int i = 0; i < WARP_COUNT; i++) {
        int dest = WARPS[i].dest, is_east = 0;
        for (int k = 0; k < EAST_COUNT; k++) is_east |= dest == EAST_MAPS[k] || WARPS[i].map == EAST_MAPS[k];
        if (!is_east) continue;
        count++;
        map_load(WARPS[i].map);
        if (!(cell_attr(WARPS[i].x, WARPS[i].y) & A_DOOR) ||
            !((walk_ok(WARPS[i].x, WARPS[i].y + 1)) ||
              (WARPS[i].y > 0 && walk_ok(WARPS[i].x, WARPS[i].y - 1)))) ok = 0;
        map_load(dest);
        if (!(cell_attr(WARPS[i].dx, WARPS[i].dy) & (A_EXIT | A_DOOR)) &&
            !(MAPS[dest].flags & MF_OUTDOOR && walk_ok(WARPS[i].dx, WARPS[i].dy))) {
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
    CHECK(ok && count >= 15, "every east door lands on its exit mat and the mat leads back out");
    flag_clear(FLAG_RIME_CREST);

    /* walk in and back out of the Volt Hall for real */
    fresh_game();
    give_starter();
    field_enter_map(MAP_LUMEN, 10, 7, DIR_UP);
    hold(KEY_UP, 4);
    for (int f = 0; f < 30; f++) step(0);
    int in = cur_map == MAP_VOLT_HALL && player.x == 7 && player.y == 16;
    hold(KEY_DOWN, 12);
    for (int f = 0; f < 30; f++) step(0);
    CHECK(in && cur_map == MAP_LUMEN && player.x == 10 && player.y == 7, "you can walk into the Volt Hall and out again");
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
    seen[MAP_BROOKMILL_TRAIL] = 1;
    queue[tail] = MAP_BROOKMILL_TRAIL; qx[tail] = 0; qy[tail++] = 17;
    seen[MAP_ELDERWOOD] = 1;
    queue[tail] = MAP_ELDERWOOD; qx[tail] = 30; qy[tail++] = 0;
    seen[MAP_LAND_OFFICE] = 1;
    queue[tail] = MAP_LAND_OFFICE; qx[tail] = 5; qy[tail++] = 8;
    flag_set(FLAG_OSSUREX_ANSWERED);
    flag_set(FLAG_MINE_LIGHT_CACHE);
    flag_set(FLAG_STORM_CALMED);
    flag_set(FLAG_TIDE_CREST);
    flag_set(FLAG_CREST_ANVIL);
    flag_set(FLAG_RIME_CREST);
    flag_set(FLAG_LANTERN_CREST);
    int all_ok = 1;
    while (head < tail) {
        int m = queue[head], sx = qx[head], sy = qy[head];
        head++;
        map_load(m);
        flood_ex(sx, sy, FLOOD_SOLVED);   /* puzzles solved (traversal makes objects solid) */
        /* everything on the map is reachable from where you come in */
        for (int i = 0; i < NPC_COUNT; i++)
            if (NPCS[i].map == m && m != MAP_ACCORD_GATE) {
                int ok = reached_beside(NPCS[i].x, NPCS[i].y);
                for (int d = 0; d < 4 && !ok; d++) {
                    int cx = NPCS[i].x + DIR_DX[d], cy = NPCS[i].y + DIR_DY[d];
                    if ((cell_attr(cx, cy) & A_COUNTER) && reached(cx + DIR_DX[d], cy + DIR_DY[d])) ok = 1;
                }
                if (!ok) { all_ok = 0; printf("  %s: %s unreachable\n", MAPS[m].name, NPCS[i].name); }
            }
        for (int i = 0; i < MAPS[m].obj_count; i++) {
            const MapObj *o = &MAPS[m].objs[i];
            if (m == MAP_ACCORD_GATE) continue; /* Captain Audra scripts the locked exit. */
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
    for (int t = TR_DUNN; t <= TR_MINE_BOSS; t++) {
        const TrainerDef *d = &TRAINERS[t];
        if (d->count < 1 || d->count > 6) teams = 0;
        for (int i = 0; i < d->count; i++)
            if (d->species[i] >= SP_COUNT || d->level[i] < 10 || d->level[i] > 55) teams = 0;
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
                               LSRC_GROVE, LSRC_CLOCKMAKER, LSRC_TOLL, LSRC_HERON, LSRC_MILLER,
                               LSRC_FIDDLER, LSRC_COPPER_RUSH };
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
    CHECK(!flag(FLAG_FEN_RIVETS), "FARA awards only the crest, not the boardwalk flag");
    talk(vex);
    CHECK(flag(FLAG_RIVET_BUNDLE) && !flag(FLAG_FEN_RIVETS),
          "VEX grants the virtual rivet bundle, but not the boardwalk flag");
    int holt = npc_named("GUILDMASTER HOLT");
    talk(holt);
    CHECK(flag(FLAG_FEN_RIVETS), "HOLT sets the boardwalk flag after VOLT");
    fresh_game(); give_starter();
    talk(holt);
    CHECK(!flag(FLAG_FEN_RIVETS), "HOLT cannot open the Fen before VOLT");
    flag_set(FLAG_VOLT_CREST);
    talk(holt);
    CHECK(flag(FLAG_FEN_RIVETS), "HOLT handles a pre-held crest without requiring VEX");
    fresh_game(); give_starter();
    int ada = npc_named("MILLER ADA");
    talk(ada); talk(ada);
    bag_add(ITEM_IRON_ORE, 3);
    talk(ada);
    CHECK(quest_done(QUEST_GRIST_WHEEL) && !bag[ITEM_IRON_ORE] && bag[ITEM_HONEY_BUN] == 2,
          "MILLER ADA accepts three ore and gives the quest reward once");

}

static void test_routes(void)
{
    CHECK(MAPS[MAP_BROOKMILL_TRAIL].w == 64 && MAPS[MAP_BROOKMILL].w == 40 &&
          MAPS[MAP_COPPER_MINE].w == 36 && (MAPS[MAP_COPPER_MINE].flags & MF_DARK),
          "route widths, hamlet and optional dark mine match the contract");
    CHECK(MAPS[MAP_BROOKMILL_REST].flags & MF_HEAL, "Brookmill has a Hearth");
    CHECK(MAPS[MAP_BROOKMILL_TRAIL].feats[0].kind == EF_BRIDGE_H &&
          MAPS[MAP_BROOKMILL_TRAIL].zone == ZONE_BROOK_TRAIL &&
          WILD_ZONES[ZONE_BROOK_REEDS].count >= 5,
          "the bridge, grass and uncommon reed encounters are defined");
    CHECK(MAPS[MAP_COPPER_MINE].patch_count == 1 &&
          MAPS[MAP_COPPER_MINE].patches[0].flag == FLAG_MINE_LIGHT_CACHE &&
          MAPS[MAP_COPPER_MINE].patches[0].invert == 1,
          "the optional mine gallery is shut before LIGHT");
    CHECK(MAPS[MAP_ELDERWOOD].patches[0].flag == FLAG_OSSUREX_ANSWERED &&
          MAPS[MAP_CLOCKWORK_SPIRE].patches[0].flag == FLAG_OSSUREX_ANSWERED,
          "legend entrances need the post-game flag as well as STRENGTH");
    int visible = 0, millpond = 0;
    for (int i = 0; i < (int)(sizeof(ITEM_BALLS) / sizeof(ITEM_BALLS[0])); i++) {
        visible += ITEM_BALLS[i].map == MAP_BROOKMILL_TRAIL;
        millpond += ITEM_BALLS[i].map == MAP_BROOKMILL && ITEM_BALLS[i].item == ITEM_TIDE_LANTERN;
    }
    CHECK(visible >= 4 && millpond == 1, "trail rewards and SURF return reward are placed");
    int timed = 0;
    for (int i = 0; i < NPC_COUNT; i++) timed += NPCS[i].map == MAP_BROOKMILL && NPCS[i].when == WHEN_NIGHT;
    CHECK(timed == 1, "the millpond fiddler comes out at night");
}

static void test_project_visuals(void)
{
    fresh_game();
    map_load(MAP_BROOKMILL);
    u16 bare_depot = map_cells[29 * map_w + 33];
    CHECK(MAPS[MAP_BROOKMILL].patch_count == 1 &&
          MAPS[MAP_BROOKMILL].patches[0].flag == FLAG_PROJECT_TRAM &&
          cell_walkable(31, 29), "Brookmill depot is absent before construction; tram arrival stays walkable");
    flag_set(FLAG_PROJECT_TRAM);
    map_load(MAP_BROOKMILL);
    CHECK(map_cells[29 * map_w + 33] != bare_depot && cell_walkable(31, 29),
          "Brookmill depot apron appears after tram project without blocking its arrival");
    flood(31, 29);
    CHECK(reached(0, 17) && reached(39, 17) && reached(5, 14),
          "tram arrival can return west/east or reach the Brookmill Hearth approach");
    field_load_tileset();
    CHECK(decor_tiles_wanted <= SCENE_TILE_MAX, "completed Brookmill depot fits the scene budget");
    map_load(MAP_LUMEN);
    CHECK(MAPS[MAP_LUMEN].patch_count == 3 && cell_walkable(36, 20) &&
          !walk_ok(55, 20) && !walk_ok(24, 0),
          "Lumen tram does not bypass the Tide or Lantern gates");
    field_load_tileset();
    CHECK(decor_tiles_wanted <= SCENE_TILE_MAX, "completed Lumen stop fits the scene budget");
    flag_clear(FLAG_PROJECT_TRAM);
    map_load(MAP_LUMEN);
    u16 bare_stop = map_cells[22 * map_w + 33];
    flag_set(FLAG_PROJECT_TRAM);
    map_load(MAP_LUMEN);
    CHECK(map_cells[22 * map_w + 33] != bare_stop && cell_walkable(36, 20),
          "Lumen buffer stop appears only after tram completion; return landing stays open");
    flag_clear(FLAG_PROJECT_TRAM);
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    test_routes();
    test_project_visuals();
    test_lumen_heights();
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
