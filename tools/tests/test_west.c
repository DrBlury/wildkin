/*
 * W-WEST checks: the coast tileset budget, the region's edge contracts,
 * the CURRENT HALL solved with the A_CURRENT rule, map objects (ferries,
 * berry patches, NOCTHALE), people limits, and the scripts: the shop, the
 * ferry, HARBOR POST (-> FERRY PASS), SALT FOR THE ISLE and the Hall Master
 * bout (TT_MASTER, six kin, TIDE CREST).
 */
#include "harness.h"

static const u8 WEST_MAPS[] = {
    MAP_SALTWIND, MAP_PORT_BRINE, MAP_SEA_ROUTE, MAP_GULL_ISLE, MAP_BRINE_HEARTH, MAP_BRINE_SHOP,
    MAP_CURRENT_HALL, MAP_HARBOR_OFFICE, MAP_BRINE_INN, MAP_GULL_HOUSE, MAP_DROWNED_BELL, MAP_BRINE_HOUSE,
};
#define WEST_N ((int)sizeof(WEST_MAPS))

static int open_cell(int x, int y)
{
    return x >= 0 && y >= 0 && x < map_w && y < map_h && !(cell_attr(x, y) & (A_SOLID | A_WATER | A_LEDGE));
}

/* ---- the current rule (docs in world/west/data.h) ---- */

static int cur_dir(int x, int y)
{
    int a = cell_attr(x, y);
    if (!(a & A_CURRENT)) return -1;
    return ((a & A_DIR_HI) ? 2 : 0) | ((a & A_DIR_LO) ? 1 : 0);
}

static int hall_free(int x, int y)
{
    return x >= 0 && y >= 0 && x < map_w && y < map_h && !(cell_attr(x, y) & (A_SOLID | A_LEDGE)) &&
           npc_at(x, y) < 0 && item_ball_at(x, y) < 0;
}

/* Step from (x, y) in direction d; returns 0 if blocked, else the resting cell. */
static int hall_step(int x, int y, int d, int *ox, int *oy)
{
    int nx = x + DIR_DX[d], ny = y + DIR_DY[d];
    if (!hall_free(nx, ny)) return 0;
    for (int guard = 0; guard < 200; guard++) {
        int cd = cur_dir(nx, ny);
        if (cd < 0) break;
        int tx = nx + DIR_DX[cd], ty = ny + DIR_DY[cd];
        if (!hall_free(tx, ty)) break;
        nx = tx;
        ny = ty;
    }
    *ox = nx;
    *oy = ny;
    return 1;
}

static u8 hall_seen[MAP_MAX_W * MAP_MAX_H];

static void hall_flood(int sx, int sy)
{
    static int qx[MAP_MAX_W * MAP_MAX_H], qy[MAP_MAX_W * MAP_MAX_H];
    memset(hall_seen, 0, sizeof(hall_seen));
    int head = 0, tail = 0;
    qx[tail] = sx;
    qy[tail++] = sy;
    hall_seen[sy * map_w + sx] = 1;
    while (head < tail) {
        int x = qx[head], y = qy[head++];
        for (int d = 0; d < 4; d++) {
            int nx, ny;
            if (!hall_step(x, y, d, &nx, &ny) || hall_seen[ny * map_w + nx]) continue;
            hall_seen[ny * map_w + nx] = 1;
            qx[tail] = nx;
            qy[tail++] = ny;
        }
    }
}

static int npc_by_script(int map, int scr)
{
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].map == map && NPCS[i].script == scr) return i;
    return -1;
}

static void talk(int map, int scr)
{
    int i = npc_by_script(map, scr);
    if (i < 0) return;
    if (cur_map != map) map_load(map);
    game_mode = MODE_FIELD;
    script_run(i);
}

static void finish(void)
{
    for (int f = 0; f < 1500 && (dialog_active() || warp.active || game_mode == MODE_SHOP || game_mode == MODE_EXT); f++) {
        if (game_mode == MODE_SHOP) {
            tap(KEY_B);
            continue;
        }
        step((f & 3) == 0 ? KEY_A : 0);
    }
    settle();
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();

    /* ~380 + the animated tall grass (tools/grass.py: 3 variants x 2 varieties) */
    CHECK(TILESETS[TS_COAST].tile_count <= 410, "the coast tileset stays under ~410 tiles");

    /* budget, people and characters on every west map */
    int budget_ok = 1, people_ok = 1;
    for (int k = 0; k < WEST_N; k++) {
        int m = WEST_MAPS[k];
        map_load(m);
        field_load_tileset();
        if (decor_tiles_used > 512) budget_ok = 0;
        int n = 0, chars = 0;
        u8 seen[64] = { 0 };
        for (int i = 0; i < NPC_COUNT; i++) {
            if (NPCS[i].map != m) continue;
            n++;
            if (!seen[NPCS[i].chr]) chars++;
            seen[NPCS[i].chr] = 1;
        }
        if (n > 24 || chars > 7) {
            people_ok = 0;
            printf("  %s: %d people, %d characters\n", MAPS[m].name, n, chars);
        }
    }
    CHECK(budget_ok, "every west map fits its tiles and decor in 512 scene tiles");
    CHECK(people_ok, "at most 24 people and 7 characters on every west map");

    /* edge contracts (docs/EXPANSION.md 9) */
    map_load(MAP_SALTWIND);
    int e1 = open_cell(49, 31) && open_cell(49, 32) && open_cell(0, 19) && open_cell(0, 20);
    map_load(MAP_LAKE);
    e1 = e1 && open_cell(0, 31) && open_cell(0, 32);
    map_load(MAP_PORT_BRINE);
    e1 = e1 && open_cell(47, 19) && open_cell(47, 20) && open_cell(20, 43) && open_cell(21, 43);
    map_load(MAP_SEA_ROUTE);
    e1 = e1 && open_cell(20, 0) && open_cell(21, 0) && open_cell(20, 47) && open_cell(21, 47);
    map_load(MAP_GULL_ISLE);
    e1 = e1 && open_cell(20, 0) && open_cell(21, 0);
    CHECK(e1, "the edge openings match: Lake y31-32, Brine y19-20, Sea Route x20-21 (both ends)");
    CHECK(MAPS[MAP_SALTWIND].link[LINK_E] == MAP_LAKE && MAPS[MAP_PORT_BRINE].link[LINK_S] == MAP_SEA_ROUTE &&
              MAPS[MAP_SEA_ROUTE].link[LINK_S] == MAP_GULL_ISLE,
          "the region's links follow the world graph");

    /* the Sea Route needs SURF: without it the south shore can't be reached */
    map_load(MAP_SEA_ROUTE);
    hall_flood(20, 0);   /* no currents here: a plain walking flood */
    int walk_only = hall_seen[47 * map_w + 20];
    flood_ex(20, 0, FLOOD_SURF);   /* as if with SURF */
    CHECK(!walk_only && reached(20, 47), "the SEA ROUTE is crossed by SURF, not on foot");
    int kelp = 0;
    for (int i = 0; i < WILD_ZONES[ZONE_SEA].count; i++)
        if (WILD_ZONES[ZONE_SEA].slots[i].species == SP_KELPYRE &&
            WILD_ZONES[ZONE_SEA].slots[i].when == WHEN_NIGHT && WILD_ZONES[ZONE_SEA].slots[i].weight <= 3)
            kelp = 1;
    CHECK(kelp && MAPS[MAP_PORT_BRINE].water_zone == ZONE_SEA && MAPS[MAP_GULL_ISLE].water_zone == ZONE_SEA,
          "the coast has a water zone, with KELPYRE rare at night");

    /* the CURRENT HALL */
    map_load(MAP_CURRENT_HALL);
    int cur = 0;
    for (int y = 0; y < map_h; y++)
        for (int x = 0; x < map_w; x++)
            if (cur_dir(x, y) >= 0) cur++;
    CHECK(cur >= 20, "the Hall has a current network");
    int master = npc_by_script(MAP_CURRENT_HALL, SCR_MAREN);
    hall_flood(7, 17);
    int solved = 0;
    for (int d = 0; d < 4; d++) {
        int x = NPCS[master].x + DIR_DX[d], y = NPCS[master].y + DIR_DY[d];
        if (x >= 0 && y >= 0 && hall_seen[y * map_w + x]) solved = 1;
    }
    CHECK(solved, "riding the currents from the door reaches MASTER MAREN");
    int nx, ny;
    CHECK(hall_step(7, 14, DIR_UP, &nx, &ny) && nx == 9 && ny == 15, "the middle channel loops back to the start");
    int dais_direct = 0, way_back = 0;
    for (int x = 3; x <= 11; x++) {
        if (!(cell_attr(x, 4) & A_SOLID) && cur_dir(x, 4) != DIR_UP && cur_dir(x, 4) != DIR_DOWN) dais_direct = 1;
        if (cur_dir(x, 4) == DIR_DOWN) way_back = 1;
    }
    CHECK(!dais_direct, "the dais is only reached by the up-current");
    CHECK(way_back, "a down-current carries you off the dais again (no soft-lock, test_puzzles)");

    /* objects */
    map_load(MAP_DROWNED_BELL);
    int legend = 0;
    flood(9, 17);
    for (int i = 0; i < MAPS[MAP_DROWNED_BELL].obj_count; i++) {
        const MapObj *o = &MAPS[MAP_DROWNED_BELL].objs[i];
        if (o->kind == OBJ_LEGEND && o->arg == SP_NOCTHALE && reached_beside(o->x, o->y)) legend = 1;
    }
    CHECK(legend, "NOCTHALE waits in the Drowned Bell and can be faced");
    int ferries = 0, berries_ok = 1;
    for (int k = 0; k < WEST_N; k++) {
        int m = WEST_MAPS[k];
        map_load(m);
        for (int i = 0; i < MAPS[m].obj_count; i++) {
            const MapObj *o = &MAPS[m].objs[i];
            if (o->kind == OBJ_FERRY && o->arg < MAP_COUNT) {
                int w = 0;
                for (int d = 0; d < 4; d++) w |= open_cell(o->x + DIR_DX[d], o->y + DIR_DY[d]);
                ferries += w;
            }
            if (o->kind == OBJ_BERRY && (o->arg < 10 || o->arg > 19)) berries_ok = 0;
        }
    }
    CHECK(ferries == 2, "Port Brine and Gull Isle each have a ferry you can walk up to");
    CHECK(berries_ok, "west berry patches use ids 10-19");

    /* ---- scripts ---- */
    fresh_game();
    give_starter();

    talk(MAP_BRINE_SHOP, SCR_BRINE_SHOP);
    for (int f = 0; f < 60 && game_mode != MODE_SHOP; f++) step((f & 3) == 0 ? KEY_A : 0);
    CHECK(game_mode == MODE_SHOP && shop_stock == BRINE_STOCK, "the BRINE SHOP opens its own stock");
    finish();

    money = 1000;
    talk(MAP_PORT_BRINE, SCR_FERRY);
    finish();
    CHECK(cur_map == MAP_GULL_ISLE && money == 500 && cell_walkable(player.x, player.y),
          "the ferry takes you to GULL ISLE for 500c");
    talk(MAP_GULL_ISLE, SCR_FERRY);
    finish();
    CHECK(cur_map == MAP_PORT_BRINE && money == 500, "and back for free");

    talk(MAP_HARBOR_OFFICE, SCR_HARBORMASTER);
    finish();
    CHECK(quest_get(QUEST_HARBOR_POST) == 1, "the harbor master hands out HARBOR POST");
    talk(MAP_BRINE_INN, SCR_BRINE_INNKEEPER);
    finish();
    talk(MAP_BRINE_HOUSE, SCR_SKIPPER);
    finish();
    talk(MAP_CURRENT_HALL, SCR_HALL_GUIDE);
    finish();
    CHECK(flag(FLAG_POST_INN) && flag(FLAG_POST_SKIPPER) && flag(FLAG_POST_HALL), "all three letters delivered");
    talk(MAP_HARBOR_OFFICE, SCR_HARBORMASTER);
    finish();
    CHECK(quest_done(QUEST_HARBOR_POST) && bag[ITEM_FERRY_PASS] == 1, "HARBOR POST ends with the FERRY PASS");
    money = 0;
    talk(MAP_PORT_BRINE, SCR_FERRY);
    finish();
    CHECK(cur_map == MAP_GULL_ISLE, "the FERRY PASS sails for free");

    talk(MAP_GULL_ISLE, SCR_ODA);
    finish();
    CHECK(quest_get(QUEST_ISLE_SALT) == 1, "Oda asks for SALT");
    talk(MAP_SALTWIND, SCR_SALT_RAKER);
    finish();
    CHECK(bag[ITEM_SALT] >= 3, "the salt raker gives SALT");
    int lore0 = lore_known_count();
    talk(MAP_GULL_ISLE, SCR_ODA);
    finish();
    CHECK(quest_done(QUEST_ISLE_SALT) && lore_known_count() > lore0, "3 SALT finish Oda's quest, with a story");

    /* the Hall Master */
    talk(MAP_CURRENT_HALL, SCR_MAREN);
    for (int f = 0; f < 200 && game_mode != MODE_BATTLE; f++) step((f & 3) == 0 ? KEY_A : 0);
    CHECK(game_mode == MODE_BATTLE && battle.master && battle.team_count == 6 && battle_end_hook == maren_end,
          "MAREN fights a six-kin Hall Master bout");
    battle_end_hook = 0;
    dialog_clear();
    game_mode = MODE_FIELD;
    map_load(MAP_CURRENT_HALL);
    maren_end(BR_WIN);
    finish();
    CHECK(flag(FLAG_TIDE_CREST) && travel_has_crest(CREST_TIDE) && trainer_beaten(TR_MAREN) &&
              lore_is_known(LORE_TIDE_CREST) && bag[ITEM_TIDE_LANTERN] >= 3,
          "beating MAREN gives the TIDE CREST, TIDE LANTERNS and the crest's lore");

    if (failures == 0) {
        printf("all west checks passed\n");
        return 0;
    }
    printf("%d check(s) FAILED\n", failures);
    return 1;
}
