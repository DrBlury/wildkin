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
static u8 valid_seed[MAX_SEEDS];
static u8 act_maps[8][MAP_COUNT];
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

static void solve_from(int map, int x, int y)
{
    memset(visited, 0, sizeof visited);
    memset(reached_maps, 0, sizeof reached_maps);
    memset(valid_seed, 0, sizeof valid_seed);
    for (int i = 0; i < MAP_COUNT; i++) first_seed[i] = -1;
    nseeds = 0;
    enqueue(map, x, y, -1);
    for (int head = 0; head < nseeds; head++) {
        Seed s = seeds[head];
        if (visited[s.map][s.y * MAPS[s.map].w + s.x]) continue;
        map_load(s.map); /* decode active patches and refresh visible blockers */
        /* Strength-enabled obstacle paths are optimistic here; each Hall
         * Master is separately proven by the real-move puzzle search. */
        int mode = (flag(FLAG_TIDE_CREST) ? FLOOD_SURF : 0) |
                   (flag(FLAG_CREST_ANVIL) ? FLOOD_SOLVED : 0);
        flood_ex(s.x, s.y, mode);
        if (!at(s.x, s.y)) continue;
        valid_seed[head] = 1;
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
            if (w->dest == s.map && at(w->dx, w->dy)) {
                /* Interior exit mats can sit beside the spawn (Reed Tunnel's
                 * mat is diagonally one cell away), not necessarily on it. */
                for (int oy = -1; oy <= 1; oy++) for (int ox = -1; ox <= 1; ox++) {
                    int ex = w->dx + ox, ey = w->dy + oy;
                    if (at(ex, ey) && (cell_attr(ex, ey) & A_EXIT))
                        enqueue(w->map, w->x, w->y + 1, head);
                }
            }
        }
        /* OSRIC's yes/no script warps to the Ossuary; no MapDef link or
         * entrance warp exists. Merely entering Duskmere cannot grant it. */
        if (s.map == MAP_DUSKMERE && beside(34, 19) &&
            flag(FLAG_VOLT_CREST) && flag(FLAG_TIDE_CREST) &&
            flag(FLAG_CREST_ANVIL) && flag(FLAG_RIME_CREST) &&
            flag(FLAG_LANTERN_CREST) && flag(FLAG_CREST_DREAM))
            enqueue(MAP_OSSUARY_1, 4, 2, head);
        /* Aurora's cave guides use scripted warps, not automatic Warp rows. */
        if (flag(FLAG_LANTERN_CREST) && flag(FLAG_CREST_DREAM)) {
            if (s.map == MAP_DREAMSPIRE && beside(3, 18))
                enqueue(MAP_AURORA_RIDGE_2, 49, 19, head);
            if (s.map == MAP_AURORA_RIDGE_2 && beside(50, 18))
                enqueue(MAP_DREAMSPIRE, 4, 29, head);
        }
        /* Only offer destinations permitted by the actual FLY-point rules. */
        if (flag(FLAG_RIME_CREST) && (MAPS[s.map].flags & MF_OUTDOOR) &&
            !(MAPS[s.map].flags & MF_NOFLY)) {
            for (int i = 0; i < FLY_POINT_COUNT; i++)
                if (FLY_POINTS[i].map == MAP_SKY_ISLE && fly_point_open(i))
                    enqueue(MAP_SKY_ISLE, FLY_POINTS[i].x, FLY_POINTS[i].y, head);
            enqueue(MAP_TOWN, 23, 17, head); /* visited Maple fly point */
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

static void solve(void) { solve_from(MAP_TOWN, 23, 17); }

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
    CHECK(!flood_open(0, 31, FLOOD_WALK) && !flood_open(0, 32, FLOOD_WALK),
          "G2 fen wardens keep the western road sealed after G1");
    flag_set(FLAG_VOLT_CREST);
    map_load(MAP_LAKE);
    CHECK(flood_open(0, 31, FLOOD_WALK) && flood_open(0, 32, FLOOD_WALK),
          "G2 releases the Lake border after VOLT");
    flag_clear(FLAG_VOLT_CREST);
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

    map_load(MAP_RISE);
    CHECK(!flood_open(11, 0, FLOOD_WALK) && !flood_open(12, 0, FLOOD_WALK),
          "G4 also seals the Rise border before Anvil");
    flag_set(FLAG_CREST_ANVIL);
    map_load(MAP_RISE);
    CHECK(flood_open(11, 0, FLOOD_WALK) && flood_open(12, 0, FLOOD_WALK),
          "G4 Rise border reopens after Anvil");
    flag_clear(FLAG_CREST_ANVIL);

    map_load(MAP_COPPERLINE);
    CHECK(!(cell_attr(20, 34) & A_DOOR), "G5 seals the Copperline checkpoint door");
    flag_set(FLAG_RIME_CREST);
    map_load(MAP_COPPERLINE);
    CHECK(cell_attr(20, 34) & A_DOOR, "G5 reopens the door after Rime");
    flag_clear(FLAG_RIME_CREST);

    map_load(MAP_LUMEN);
    CHECK(!flood_open(55, 20, FLOOD_WALK) && !flood_open(24, 0, FLOOD_WALK),
          "G3 and G6 seal their Lumen departures");
    flag_set(FLAG_TIDE_CREST);
    flag_set(FLAG_LANTERN_CREST);
    map_load(MAP_LUMEN);
    CHECK(flood_open(55, 20, FLOOD_WALK) && flood_open(24, 0, FLOOD_WALK),
          "G3 and G6 reopen their Lumen departures after their crests");
    flag_clear(FLAG_TIDE_CREST);
    flag_clear(FLAG_LANTERN_CREST);

    map_load(MAP_FOOTHILLS);
    int east_rock = -1, guide = -1;
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].kind == OBJ_BOULDER && tobj[i].x == 12 && tobj[i].y == 56) east_rock = i;
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].map == MAP_FOOTHILLS && NPCS[i].script == SCR_ROCKFALL_RETURN &&
            NPCS[i].x == 15 && NPCS[i].y == 52) guide = i;
    CHECK(east_rock >= 0 && guide >= 0, "G4 has a north-side one-way return guide");
    if (east_rock >= 0 && guide >= 0) {
        tobj[east_rock].y = 59; /* adverse south push blocks the narrow return lane */
        grid_cell(12, 56);
        grid_cell(12, 59);
        flood_ex(14, 53, FLOOD_WALK);
        CHECK(at(15, 53), "G4 return guide remains reachable behind a south-pushed rock");
        rockfall_return_answer(0);
        CHECK(warp.active && warp.dest == MAP_RISE && warp.x == 11 && warp.y == 2,
              "G4 one-way ridge chute returns directly to the Rise");
        warp.active = 0;
        flag_set(FLAG_CREST_ANVIL);
        map_load(MAP_RISE);
        flood_ex(11, 2, FLOOD_WALK);
        CHECK(at(11, 19) || at(12, 19), "G4 ridge chute landing can walk home through the Rise");
        flag_clear(FLAG_CREST_ANVIL);
    }
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

/* Compose with the real-move exhaustive puzzle search, not the optimistic
 * FLOOD_SOLVED shortcut. A Hall crest is earned only when its actual Master
 * NPC target has a complete, non-soft-locked solution from the Hall entrance. */
#define PZ_NO_MAIN
#define solve puzzle_solve
#include "test_puzzles.c"
#undef solve

static int hall_master_proved(const Milestone *m)
{
    Tally proof = { 0 };
    ENTRY_CAP = m->map == MAP_ANVIL_HALL ? 12000000u : 500000u;
    puzzle_solve(m->map, 0, 1, &proof, 0);
    int master = 0;
    for (int i = 0; i < ntgt; i++)
        if (tgt[i].kind == T_NPC && tgt[i].x == m->x && tgt[i].y == m->y &&
            tgt[i].node != NIL) master = 1;
    if (!master || proof.overflow || proof.unreachable || proof.softlocks ||
        proof.loops || proof.maps != 1) {
        printf("  %s puzzle proof: master=%d maps=%d overflow=%d missing=%d softlocks=%d loops=%d\n",
               MAPS[m->map].name, master, proof.maps, proof.overflow,
               proof.unreachable, proof.softlocks, proof.loops);
        return 0;
    }
    return 1;
}

static void check_returns(int act)
{
    Seed roots[MAX_SEEDS];
    int count = 0;
    for (int i = 0; i < nseeds; i++)
        if (valid_seed[i]) roots[count++] = seeds[i];
    int stranded = 0;
    for (int i = 0; i < count; i++) {
        Seed r = roots[i];
        solve_from(r.map, r.x, r.y);
        int hearth = 0;
        for (int map = 0; map < MAP_COUNT; map++)
            if (reached_maps[map] && (MAPS[map].flags & MF_HEAL)) hearth = 1;
        if (!hearth) {
            printf("  act %d: %s entry (%d,%d) cannot return to a Hearth\n",
                   act, MAPS[r.map].name, r.x, r.y);
            stranded++;
        }
    }
    CHECK(!stranded, "each reached entry component can return to a Hearth");
    solve(); /* restore forward reachable cells for the next milestone */
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
        check_returns(act);
        memcpy(act_maps[act], reached_maps, sizeof reached_maps);
        if (act >= 5 && !flag(FLAG_OSSUREX_ANSWERED))
            CHECK(!reached_maps[MAP_SKY_ISLE],
                  "postgame Sky Isle remains gated until Ossurex is answered");
        const Milestone *m = &milestones[act - 1];
        int interactable = reached_maps[m->map] && (act == 1 ? milestone_reached(m) : hall_master_proved(m));
        if (!flag(m->requires) || !interactable) {
            printf("FAIL: act %d milestone %s at (%d,%d) not interactable\n",
                   act, MAPS[m->map].name, m->x, m->y);
            failures++;
        }
        if (flag(m->requires) && interactable) {
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
    flag_set(FLAG_MINE_LIGHT_CACHE);
    flag_set(FLAG_PROJECT_CINDER_BRIDGE);
    solve();
    int missing = 0;
    for (int map = 0; map < MAP_COUNT; map++)
        if (!(MAPS[map].flags & MF_DEBUG) && strncmp(MAPS[map].name, "TEST ", 5) && !reached_maps[map]) {
            printf("  completeness: %s unreachable after all milestones\n", MAPS[map].name);
            missing++;
        }
    CHECK(!missing, "every non-debug map is reachable after all milestones");
    check_levels();
    if (failures)
        for (int act = 1; act <= 7; act++) {
            printf("  act %d reachable:", act);
            for (int map = 0; map < MAP_COUNT; map++)
                if (act_maps[act][map]) printf(" %s;", MAPS[map].name);
            putchar('\n');
        }
    return failures ? 1 : 0;
}
