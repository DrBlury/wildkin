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
    MAP_HERON_FEN, MAP_REEDWICK, MAP_REED_HEARTH, MAP_REED_SHOP, MAP_REED_TUNNEL, MAP_FEN_HERMIT,
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

    /* the outdoor art + tall grass + the elevation art; the Current Hall and the
     * Drowned Bell are the 'tide' tileset, so the towns keep ~100 tiles for props */
    CHECK(TILESETS[TS_COAST].tile_count <= 420, "the coast tileset stays under ~420 tiles");

    /* budget, people and characters on every west map */
    int budget_ok = 1, people_ok = 1;
    for (int k = 0; k < WEST_N; k++) {
        int m = WEST_MAPS[k];
        map_load(m);
        field_load_tileset();
        if (decor_tiles_wanted > SCENE_TILE_MAX) budget_ok = 0;
        /* field_load_tileset skips a kind that doesn't fit: it would draw garbage */
        for (int i = 0; i < MAPS[m].decor_count; i++)
            if (!decor_base[MAPS[m].decor[i].kind]) {
                if (budget_ok) printf("  %s: decor kind %d doesn't fit the 768 scene tiles\n", MAPS[m].name,
                                      MAPS[m].decor[i].kind);
                budget_ok = 0;
            }
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
    CHECK(budget_ok, "every west map fits its tileset and every decor kind in 768 scene tiles");
    CHECK(people_ok, "at most 24 people and 7 characters on every west map");

    /* Worst-case NPC configuration also includes mutually exclusive carpenter variants. */
    int conditional_npcs = 0, night_wardens = 0;
    for (int i = 0; i < NPC_COUNT; i++) {
        if (NPCS[i].map == MAP_HERON_FEN && NPCS[i].script == SCR_FEN_CARPENTER) conditional_npcs++;
        if (NPCS[i].map == MAP_HERON_FEN && NPCS[i].trainer == TR_FEN_WISP &&
            NPCS[i].when == WHEN_NIGHT) night_wardens++;
    }
    CHECK(conditional_npcs == 3 && night_wardens == 1,
          "two conditional carpenters, a replacement, and a night-only warden exist");

    /* Route edge contracts, including the two distinct fen entrances. */
    map_load(MAP_SALTWIND);
    int e1 = open_cell(49, 31) && open_cell(49, 32) && open_cell(0, 19) && open_cell(0, 20);
    map_load(MAP_REEDWICK);
    e1 = e1 && open_cell(0, 31) && open_cell(0, 32) && open_cell(39, 19) && open_cell(39, 20);
    map_load(MAP_HERON_FEN);
    e1 = e1 && open_cell(0, 19) && open_cell(0, 20) && open_cell(63, 31) && open_cell(63, 32);
    map_load(MAP_LAKE);
    e1 = e1 && open_cell(0, 31) && open_cell(0, 32);
    map_load(MAP_PORT_BRINE);
    e1 = e1 && open_cell(47, 19) && open_cell(47, 20) &&
         open_cell(20, map_h - 1) && open_cell(21, map_h - 1);
    map_load(MAP_SEA_ROUTE);
    e1 = e1 && open_cell(20, 0) && open_cell(21, 0) && open_cell(20, 47) && open_cell(21, 47);
    map_load(MAP_GULL_ISLE);
    e1 = e1 && open_cell(20, 0) && open_cell(21, 0);
    CHECK(e1, "all West edges match, including Heron Fen east y31-32 and Reedwick west y31-32");
    CHECK(MAPS[MAP_LAKE].link[LINK_W] == MAP_HERON_FEN &&
              MAPS[MAP_HERON_FEN].link[LINK_W] == MAP_REEDWICK &&
              MAPS[MAP_REEDWICK].link[LINK_W] == MAP_SALTWIND &&
              MAPS[MAP_SALTWIND].link[LINK_E] == MAP_REEDWICK &&
              MAPS[MAP_PORT_BRINE].link[LINK_S] == MAP_SEA_ROUTE &&
              MAPS[MAP_SEA_ROUTE].link[LINK_S] == MAP_GULL_ISLE,
          "the West route is linked in both directions");

    /* The E5 patch closes the only foot span, never the east bank or home.
     * E3 carpenters stand on the lake side until the rivets arrive. */
    fresh_game();
    map_load(MAP_HERON_FEN);
    flood(63, 31);
    CHECK(reached(56, 19) && !reached(0, 19), "G2 closes the west shore while the teaser stays open");
    CHECK((cell_attr(29, 19) & (A_WATER | A_DEEP)) == (A_WATER | A_DEEP) &&
              MAPS[MAP_HERON_FEN].patch_count == 1,
          "G2 is impassable deep water while FEN_RIVETS is clear");
    int before_crew = 0;
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].map == MAP_HERON_FEN && NPCS[i].script == SCR_FEN_CARPENTER &&
            NPCS[i].hide_flag == FLAG_FEN_RIVETS) before_crew++;
    CHECK(before_crew == 2, "the work crew is hidden once G2 opens");
    flag_set(FLAG_VOLT_CREST);
    talk(MAP_HERON_FEN, SCR_FEN_CARPENTER);
    finish();
    map_load(MAP_HERON_FEN);
    flood(63, 31);
    field_load_tileset();
    CHECK(decor_tiles_wanted <= SCENE_TILE_MAX, "the repaired Fen stays within the tile budget");
    CHECK(flag(FLAG_FEN_RIVETS) && reached(0, 19) && !(cell_attr(29, 19) & A_WATER),
          "Volt rivets close G2 and connect Lake to Reedwick and Port Brine on foot");
    CHECK(MAPS[MAP_REED_TUNNEL].flags & MF_DARK, "the LIGHT reed tunnel stays dark");
    CHECK((MAPS[MAP_REED_HEARTH].flags & MF_HEAL) != 0,
          "Reedwick has a separate Hearth interior");
    map_load(MAP_PORT_BRINE);
    CHECK(MAPS[MAP_PORT_BRINE].link[LINK_N] == MAP_NONE &&
              (cell_attr(20, 0) & A_WATER) && (cell_attr(21, 0) & A_WATER) &&
              !open_cell(20, 0) && !open_cell(21, 0),
          "Greywater Fjord mouth remains closed until the Links wave");
    flood_ex(1, 12, FLOOD_SURF);
    CHECK(reached(20, 0) && reached(21, 0), "SURF can reach both fjord edge water cells");

    CHECK(MAPS[MAP_SALTWIND].objs[2].kind == OBJ_BOULDER &&
              MAPS[MAP_SALTWIND].objs[2].arg == 0,
          "Saltwind cache requires STRENGTH rather than a pushable pumice stone");

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
    int w = -1;
    for (int i = 0; i < WARP_COUNT; i++)
        if (WARPS[i].dest == MAP_CURRENT_HALL) w = i;
    CHECK(w >= 0 && (cell_attr(WARPS[w].dx, WARPS[w].dy) & A_EXIT), "the Port Brine door lands on the Hall's mat");
    int dx = w >= 0 ? WARPS[w].dx : 8, dy = w >= 0 ? WARPS[w].dy : 21;
    hall_flood(dx, dy);
    int solved = 0;
    for (int d = 0; d < 4; d++) {
        int x = NPCS[master].x + DIR_DX[d], y = NPCS[master].y + DIR_DY[d];
        if (x >= 0 && y >= 0 && hall_seen[y * map_w + x]) solved = 1;
    }
    CHECK(!solved, "with every sluice as it starts, no current reaches MASTER MAREN");
    /* the tides the solver's answer ends with (test_puzzles): A back down, B and C raised */
    sw_on[0] = 0;
    sw_on[1] = sw_on[2] = 1;
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].kind == OBJ_BARRIER) tobj[i].state = (u8)barrier_up(&tobj[i]);
    hall_flood(dx, dy);
    for (int d = 0; d < 4; d++) {
        int x = NPCS[master].x + DIR_DX[d], y = NPCS[master].y + DIR_DY[d];
        if (x >= 0 && y >= 0 && hall_seen[y * map_w + x]) solved = 1;
    }
    CHECK(solved, "with tide A down and tides B and C up, the currents carry you to MASTER MAREN");
    map_load(MAP_CURRENT_HALL);
    int bell = 0;
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].kind == OBJ_SWITCH && cur_dir(tobj[i].x, tobj[i].y) >= 0) bell++;
    CHECK(bell == 1, "one switch (the tide bell) sits in a current: every ride over it rings it");
    int dais_direct = 0, way_back = 0;
    for (int x = 0; x < map_w; x++) {
        if (!(cell_attr(x, 4) & A_SOLID) && cur_dir(x, 4) != DIR_UP && cur_dir(x, 4) != DIR_DOWN) dais_direct = 1;
        if (cur_dir(x, 4) == DIR_DOWN) way_back = 1;
    }
    CHECK(!dais_direct, "the dais is only reached by the up-current");
    CHECK(way_back, "a down-current carries you off the dais again (no soft-lock, test_puzzles)");

    /* objects */
    map_load(MAP_DROWNED_BELL);
    int legend = 0;
    flood(9, 17);
    CHECK(!reached_beside(11, 8), "the Drowned Bell remains sealed before OSSUREX is answered");
    flag_set(FLAG_OSSUREX_ANSWERED);
    map_load(MAP_DROWNED_BELL);
    flood(9, 17);
    for (int i = 0; i < MAPS[MAP_DROWNED_BELL].obj_count; i++) {
        const MapObj *o = &MAPS[MAP_DROWNED_BELL].objs[i];
        if (o->kind == OBJ_LEGEND && o->arg == SP_NOCTHALE && reached_beside(o->x, o->y)) legend = 1;
    }
    CHECK(legend, "NOCTHALE can be faced after the March is quiet");
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

    /* Seasonal roof materials use West berry ids and pay only once per season. */
    talk(MAP_REEDWICK, SCR_REED_NELL);
    finish();
    CHECK(quest_get(QUEST_REED_ROOF) == 1, "Nell starts REEDS FOR THE ROOF");
    bag_add(ITEM_CROP_TIDEBERRY, 5);
    int roof_money = money;
    talk(MAP_REEDWICK, SCR_REED_NELL);
    finish();
    CHECK(money == roof_money + 300 && quest_get(QUEST_REED_ROOF) == reed_roof_season(),
          "five TIDEBERRIES pay 300c and record the season");
    talk(MAP_REEDWICK, SCR_REED_NELL);
    finish();
    CHECK(money == roof_money + 300, "the roof quest cannot be paid twice in the same season");

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
