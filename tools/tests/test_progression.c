/* Contract 01, sections 3-5: discover transitions from actual walkable cells,
 * not merely MapDef.link. This intentionally fails on an unenforced gate. */
#include "harness.h"
#include "progression_levels.h"

#define CELLS (MAP_MAX_W * MAP_MAX_H)
#define MAX_SEEDS (MAP_COUNT * 64)
typedef struct { u8 map, x, y; int from; } Seed;
static Seed seeds[MAX_SEEDS];
static u8 visited[MAP_COUNT][CELLS];
static u8 reached_maps[MAP_COUNT];
static int first_seed[MAP_COUNT];
static int nseeds;

static void enqueue(int map, int x, int y, int from)
{
    if (map < 0 || map >= MAP_COUNT || x < 0 || y < 0 || x >= MAPS[map].w || y >= MAPS[map].h) return;
    if (visited[map][y * MAPS[map].w + x]) return;
    for (int i = 0; i < nseeds; i++)
        if (seeds[i].map == map && seeds[i].x == x && seeds[i].y == y) return;
    if (nseeds >= MAX_SEEDS) {
        fprintf(stderr, "progression seed capacity exceeded\n");
        failures++;
        return;
    }
    seeds[nseeds++] = (Seed){ map, x, y, from };
}

static int at(int x, int y)
{
    return x >= 0 && y >= 0 && x < map_w && y < map_h && seen_cells[y * map_w + x];
}

static int beside(int x, int y)
{
    for (int d = 0; d < 4; d++)
        if (at(x + DIR_DX[d], y + DIR_DY[d])) return 1;
    return 0;
}

static void path_to(int index)
{
    if (index < 0) return;
    path_to(seeds[index].from);
    printf(" -> %s(%d,%d)", MAPS[seeds[index].map].name, seeds[index].x, seeds[index].y);
}

static void solve(void)
{
    memset(visited, 0, sizeof visited);
    memset(reached_maps, 0, sizeof reached_maps);
    for (int i = 0; i < MAP_COUNT; i++) first_seed[i] = -1;
    nseeds = 0;
    enqueue(MAP_TOWN, 23, 17, -1);
    for (int head = 0; head < nseeds; head++) {
        Seed s = seeds[head];
        if (visited[s.map][s.y * MAPS[s.map].w + s.x]) continue;
        map_load(s.map); /* decode active patches and refresh visible blockers */
        flood_ex(s.x, s.y, flag(FLAG_TIDE_CREST) ? FLOOD_SURF : FLOOD_WALK);
        if (!at(s.x, s.y)) continue;
        reached_maps[s.map] = 1;
        if (first_seed[s.map] < 0) first_seed[s.map] = head;
        for (int y = 0; y < map_h; y++) for (int x = 0; x < map_w; x++) {
            if (!at(x, y)) continue;
            visited[s.map][y * map_w + x] = seen_cells[y * map_w + x];
            for (int d = 0; d < 4; d++) {
                int nx = x + DIR_DX[d], ny = y + DIR_DY[d];
                if (nx >= 0 && ny >= 0 && nx < map_w && ny < map_h) continue;
                int link = (int[]){ LINK_S, LINK_N, LINK_W, LINK_E }[d];
                int dest = MAPS[s.map].link[link];
                if (dest >= MAP_COUNT) continue;
                int dx = nx, dy = ny;
                if (link == LINK_N) { dx += MAPS[s.map].link_off[link]; dy = MAPS[dest].h - 1; }
                if (link == LINK_S) { dx += MAPS[s.map].link_off[link]; dy = 0; }
                if (link == LINK_W) { dx = MAPS[dest].w - 1; dy += MAPS[s.map].link_off[link]; }
                if (link == LINK_E) { dx = 0; dy += MAPS[s.map].link_off[link]; }
                enqueue(dest, clampi(dx, 0, MAPS[dest].w - 1),
                        clampi(dy, 0, MAPS[dest].h - 1), head);
            }
        }
        for (int i = 0; i < WARP_COUNT; i++) {
            const Warp *w = &WARPS[i];
            if (w->map == s.map && beside(w->x, w->y) && (cell_attr(w->x, w->y) & A_DOOR))
                enqueue(w->dest, w->dx, w->dy, head);
            if (w->dest == s.map && at(w->dx, w->dy) && (cell_attr(w->dx, w->dy) & A_EXIT))
                enqueue(w->map, w->x, w->y + 1, head);
        }
        for (int i = 0; i < MAPS[s.map].obj_count; i++) {
            const MapObj *o = &MAPS[s.map].objs[i];
            if (o->kind != OBJ_FERRY || o->arg >= MAP_COUNT || !beside(o->x, o->y)) continue;
            const MapDef *dest = &MAPS[o->arg];
            for (int j = 0; j < dest->obj_count; j++) {
                const MapObj *back = &dest->objs[j];
                if (back->kind == OBJ_FERRY && back->arg == s.map)
                    enqueue(o->arg, back->x, back->y + 1, head);
            }
        }
    }
}

/* Milestones are interactions: a Master occupies the target cell, so the
 * player must reach an adjacent cell; simply reaching the map is insufficient. */
typedef struct { int map, x, y, sets, requires, level; } Milestone;
static const Milestone milestones[] = {
    { MAP_RISE, 12, 8, FLAG_STORM_CALMED, FLAG_STORM_TOLD, 14 },
    { MAP_VOLT_HALL, VOLT_MASTER_X, VOLT_MASTER_Y, FLAG_VOLT_CREST, FLAG_STORM_CALMED, 22 },
    { MAP_CURRENT_HALL, 8, 2, FLAG_TIDE_CREST, FLAG_VOLT_CREST, 26 },
    { MAP_ANVIL_HALL, 8, 3, FLAG_CREST_ANVIL, FLAG_TIDE_CREST, 32 },
    { MAP_RIME_HALL, 9, 2, FLAG_RIME_CREST, FLAG_CREST_ANVIL, 35 },
    { MAP_LANTERN_CRYPT, 11, 3, FLAG_LANTERN_CREST, FLAG_RIME_CREST, 39 },
    { MAP_MIRROR_HALL, 18, 2, FLAG_CREST_DREAM, FLAG_LANTERN_CREST, 43 }
};

static int milestone_reached(const Milestone *m)
{
    for (int d = 0; d < 4; d++) {
        int x = m->x + DIR_DX[d], y = m->y + DIR_DY[d];
        if (x >= 0 && y >= 0 && x < MAPS[m->map].w && y < MAPS[m->map].h &&
            visited[m->map][y * MAPS[m->map].w + x]) return 1;
    }
    return 0;
}

/* Every critical-path map (including interiors) has an explicit act. Zero
 * means a side area rather than a critical-path act; completeness still tests it. */
static const u8 map_act[MAP_COUNT] = {
    [MAP_TOWN]=1, [MAP_MEADOW]=1, [MAP_WOOD]=1, [MAP_LAKE]=1, [MAP_RISE]=1,
    [MAP_HOME]=1, [MAP_REST]=1, [MAP_BAKERY]=1, [MAP_LAB]=1, [MAP_SHOP]=1,
    [MAP_GARDEN]=1, [MAP_CABIN]=1, [MAP_STATION]=1,
    [MAP_BROOKMILL_TRAIL]=2, [MAP_BROOKMILL]=2, [MAP_COPPERLINE]=2,
    [MAP_LUMEN]=2, [MAP_VOLT_HALL]=2, [MAP_LUMEN_HEARTH]=2,
    [MAP_BROOKMILL_MILL]=2, [MAP_BROOKMILL_HOUSE]=2, [MAP_BROOKMILL_REST]=2,
    [MAP_HERON_FEN]=3, [MAP_REEDWICK]=3, [MAP_SALTWIND]=3,
    [MAP_PORT_BRINE]=3, [MAP_CURRENT_HALL]=3, [MAP_BRINE_HEARTH]=3,
    [MAP_REED_HEARTH]=3, [MAP_REED_SHOP]=3,
    [MAP_CINDER_CROSSING]=4, [MAP_RAILHEAD]=4, [MAP_CINDER_ROAD]=4,
    [MAP_CINDERMOOR]=4, [MAP_EMBER_TUNNEL]=4, [MAP_ANVIL_HALL]=4,
    [MAP_CINDER_HEARTH]=4, [MAP_RAILHEAD_BUNK]=4, [MAP_RAILHEAD_OFFICE]=4,
    [MAP_FOOTHILLS]=5, [MAP_TIMBERLINE]=5, [MAP_FROSTPINE]=5,
    [MAP_FROSTHOLLOW]=5, [MAP_GLIMMER_1]=5, [MAP_GLIMMER_2]=5,
    [MAP_RIME_HALL]=5, [MAP_FROST_HEARTH]=5,
    [MAP_ACCORD_GATE]=6, [MAP_HOLLOW_DOWNS]=6, [MAP_ASHEN_FIELDS]=6,
    [MAP_GRAVEWOOD]=6, [MAP_DUSKMERE]=6, [MAP_LANTERN_CRYPT]=6,
    [MAP_DUSK_HEARTH]=6, [MAP_WAYCHAPEL]=6,
    [MAP_MISTFEN]=7, [MAP_MOONVEIL]=7, [MAP_DREAMSPIRE]=7,
    [MAP_DUST_LIBRARY]=7, [MAP_MIRROR_HALL]=7, [MAP_DREAM_HEARTH]=7,
    [MAP_PILGRIM_REST]=7,
    [MAP_OSSUARY_1]=8, [MAP_OSSUARY_2]=8, [MAP_BONE_THRONE]=8
};

static void check_order(int act)
{
    int leaks = 0;
    for (int map = 0; map < MAP_COUNT; map++) {
        if (map_act[map] <= act || !reached_maps[map]) continue;
        printf("  gate G%d leak: %s reachable in act %d before %s; path:", act,
               MAPS[map].name, act, MAPS[milestones[act - 1].map].name);
        path_to(first_seed[map]);
        putchar('\n');
        leaks++;
    }
    if (leaks) failures++;
    else printf("ok: act %d excludes all later critical-path maps\n", act);
}

/* These local checks complement the world-order flood: they require actual
 * collision changes at each gate rather than an inferred story prerequisite. */
static void check_gate_cells(void)
{
    map_load(MAP_WOOD);
    CHECK(!flood_open(43, 17, FLOOD_WALK) && !flood_open(43, 18, FLOOD_WALK),
          "G1 road wardens close both Bramblewood exits before the calm");
    map_load(MAP_LAKE);
    CHECK(!flood_open(0, 31, FLOOD_WALK) && !flood_open(0, 32, FLOOD_WALK),
          "G1 road wardens close both Lake exits before the calm");
    flag_set(FLAG_STORM_CALMED);
    map_load(MAP_WOOD);
    CHECK(flood_open(43, 17, FLOOD_WALK) && flood_open(43, 18, FLOOD_WALK),
          "G1 releases the east road after the calm");
    map_load(MAP_LAKE);
    CHECK(flood_open(0, 31, FLOOD_WALK) && flood_open(0, 32, FLOOD_WALK),
          "G1 releases the west road after the calm");
    flag_clear(FLAG_STORM_CALMED);

    map_load(MAP_HERON_FEN);
    CHECK((cell_attr(29, 19) & (A_WATER | A_DEEP)) == (A_WATER | A_DEEP),
          "G2 missing planks are deep water before rivets");
    flag_set(FLAG_FEN_RIVETS);
    map_load(MAP_HERON_FEN);
    CHECK(flood_open(29, 19, FLOOD_WALK), "G2 boardwalk opens with rivets");
    flag_clear(FLAG_FEN_RIVETS);

    map_load(MAP_CINDER_CROSSING);
    CHECK((cell_attr(7, 20) & A_WATER) && !flood_open(7, 20, FLOOD_WALK),
          "G3 washed-out bridge needs SURF before repair");
    flag_set(FLAG_PROJECT_CINDER_BRIDGE);
    map_load(MAP_CINDER_CROSSING);
    CHECK(flood_open(7, 20, FLOOD_WALK), "G3 rebuilt bridge is walkable without SURF");
    flag_clear(FLAG_PROJECT_CINDER_BRIDGE);

    map_load(MAP_FOOTHILLS);
    CHECK(!flood_open(11, 56, FLOOD_WALK) && !flood_open(12, 56, FLOOD_WALK),
          "G4 Strength rocks seal both foothill entrance cells");
    map_load(MAP_ACCORD_GATE);
    CHECK(!flood_open(6, 6, FLOOD_WALK), "G5 Audra blocks the checkpoint without Rime");
    flag_set(FLAG_RIME_CREST);
    map_load(MAP_ACCORD_GATE);
    CHECK(flood_open(6, 6, FLOOD_WALK), "G5 checkpoint opens and leaves the return lane clear");
    flag_clear(FLAG_RIME_CREST);

    map_load(MAP_MISTFEN);
    CHECK(!flood_open(24, 52, FLOOD_WALK), "G6 fog seals the north road without Lantern");
    flag_set(FLAG_LANTERN_CREST);
    map_load(MAP_MISTFEN);
    CHECK(flood_open(24, 52, FLOOD_WALK), "G6 Ward Lantern parts the fog");
    flag_clear(FLAG_LANTERN_CREST);
}

static void check_levels(void)
{
    int bad = 0;
    for (int i = 0; i < (int)NDEC(progression_levels); i++) {
        const ProgressionLevel *p = &progression_levels[i];
        const WildZone *z = &WILD_ZONES[p->zone];
        int lo = 999, hi = 0;
        for (int j = 0; j < z->count; j++) {
            if (z->slots[j].min_level < lo) lo = z->slots[j].min_level;
            if (z->slots[j].max_level > hi) hi = z->slots[j].max_level;
        }
        if (!z->count || absi(lo - p->low) > 1 || absi(hi - p->high) > 1) {
            printf("  level: %s actual %d-%d, contract %d-%d\n", z->name, lo, hi, p->low, p->high);
            bad++;
        }
    }
    CHECK(!bad, "contract wild-zone levels are within one level");
}

int main(void)
{
    fresh_game();
    flag_set(FLAG_STARTER);
    flag_set(FLAG_STORM_TOLD); /* story introduction is prerequisite to answering DRAKORA */
    check_gate_cells();
    int party_level = 8;
    for (int act = 1; act <= 7; act++) {
        solve();
        check_order(act);
        int heal = 0;
        for (int map = 0; map < MAP_COUNT; map++)
            if (reached_maps[map] && (MAPS[map].flags & MF_HEAL)) heal = 1;
        CHECK(heal, "a Hearth is reachable from the starting cell");
        const Milestone *m = &milestones[act - 1];
        if (!flag(m->requires) || !milestone_reached(m)) {
            printf("FAIL: act %d milestone %s at (%d,%d) not interactable\n",
                   act, MAPS[m->map].name, m->x, m->y);
            failures++;
        }
        if (milestone_reached(m)) {
            if (party_level > m->level + 2) {
                printf("FAIL: act %d party estimate %d exceeds master %d by over two\n",
                       act, party_level, m->level);
                failures++;
            }
            party_level = m->level;
            flag_set(m->sets);
        }
        if (act == 2 && reached_maps[MAP_BROOKMILL]) {
            /* The carpenter, not the crest itself, repairs G2. */
            const Milestone rivets = { MAP_BROOKMILL, 26, 20, FLAG_FEN_RIVETS, FLAG_VOLT_CREST, 24 };
            if (flag(rivets.requires) && milestone_reached(&rivets)) flag_set(rivets.sets);
            else { puts("FAIL: G2 carpenter milestone prerequisite or interaction unavailable"); failures++; }
        }
    }
    /* Independently inspect the fully unlocked world even if a milestone was
     * inaccessible; preceding checks already record that progression failure. */
    for (int i = 0; i < (int)NDEC(milestones); i++) flag_set(milestones[i].sets);
    flag_set(FLAG_FEN_RIVETS);
    flag_set(FLAG_OSSUREX_ANSWERED);
    solve();
    int missing = 0;
    for (int map = 0; map < MAP_COUNT; map++)
        if (!(MAPS[map].flags & MF_DEBUG) && strncmp(MAPS[map].name, "TEST ", 5) && !reached_maps[map]) {
            printf("  completeness: %s unreachable after all milestones\n", MAPS[map].name);
            missing++;
        }
    CHECK(!missing, "every non-debug map is reachable after all milestones");
    check_levels();
    return failures ? 1 : 0;
}
