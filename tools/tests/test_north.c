/*
 * Tests for the NORTH region (owner: W-NORTH): the edge contracts, the Rime
 * Hall ice puzzle (a slide solver), floor-to-floor reachability through the
 * Glimmer Caverns to the Starfall Grotto, the STRENGTH boulder on Whitecrown
 * Peak, the legends' lairs, warden teams, lore sources, the quests and the
 * Hall Master's RIME CREST.
 */
#include "harness.h"

/* ---------------- helpers ---------------- */

static const MapObj *find_obj(int map, int kind)
{
    const MapDef *m = &MAPS[map];
    for (int i = 0; i < m->obj_count; i++)
        if (m->objs[i].kind == kind) return &m->objs[i];
    return 0;
}

/* A cell the player can stand on, with a set of extra blocked cells. */
static int open_cell(int x, int y, int bx, int by)
{
    if (x == bx && y == by) return 0;
    return cell_walkable(x, y);
}

/* Ice sliding (docs/EXPANSION.md 7.5): stepping onto A_ICE you keep going
 * until the next cell is blocked, or you reach a cell without ice. */
static u8 slide_seen[MAP_MAX_W * MAP_MAX_H];

static void slide_flood(int sx, int sy)
{
    static int qx[MAP_MAX_W * MAP_MAX_H], qy[MAP_MAX_W * MAP_MAX_H];
    memset(slide_seen, 0, sizeof(slide_seen));
    int head = 0, tail = 0;
    qx[tail] = sx;
    qy[tail++] = sy;
    slide_seen[sy * map_w + sx] = 1;
    while (head < tail) {
        int x0 = qx[head], y0 = qy[head++];
        for (int d = 0; d < 4; d++) {
            int x = x0 + DIR_DX[d], y = y0 + DIR_DY[d];
            if (!cell_walkable(x, y)) continue;
            while ((cell_attr(x, y) & A_ICE) && cell_walkable(x + DIR_DX[d], y + DIR_DY[d])) {
                x += DIR_DX[d];
                y += DIR_DY[d];
            }
            if (slide_seen[y * map_w + x]) continue;
            slide_seen[y * map_w + x] = 1;
            qx[tail] = x;
            qy[tail++] = y;
        }
    }
}

static int slide_beside(int x, int y)
{
    for (int d = 0; d < 4; d++) {
        int nx = x + DIR_DX[d], ny = y + DIR_DY[d];
        if (nx >= 0 && ny >= 0 && nx < map_w && ny < map_h && slide_seen[ny * map_w + nx]) return 1;
    }
    return 0;
}

/* Walkable flood that treats one cell (a boulder) as a wall. */
static u8 bseen[MAP_MAX_W * MAP_MAX_H];

static void flood_block(int sx, int sy, int bx, int by)
{
    static int qx[MAP_MAX_W * MAP_MAX_H], qy[MAP_MAX_W * MAP_MAX_H];
    memset(bseen, 0, sizeof(bseen));
    int head = 0, tail = 0;
    qx[tail] = sx;
    qy[tail++] = sy;
    bseen[sy * map_w + sx] = 1;
    while (head < tail) {
        int x = qx[head], y = qy[head++];
        for (int d = 0; d < 4; d++) {
            int nx = x + DIR_DX[d], ny = y + DIR_DY[d];
            if (!open_cell(nx, ny, bx, by) || bseen[ny * map_w + nx]) continue;
            bseen[ny * map_w + nx] = 1;
            qx[tail] = nx;
            qy[tail++] = ny;
        }
    }
}

static int bseen_beside(int x, int y)
{
    for (int d = 0; d < 4; d++) {
        int nx = x + DIR_DX[d], ny = y + DIR_DY[d];
        if (nx >= 0 && ny >= 0 && nx < map_w && ny < map_h && bseen[ny * map_w + nx]) return 1;
    }
    return 0;
}

static int npc_on(int map, int script)
{
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].map == map && NPCS[i].script == script) return i;
    return -1;
}

static int warp_from(int map, int dest)
{
    for (int i = 0; i < WARP_COUNT; i++)
        if (WARPS[i].map == map && WARPS[i].dest == dest) return i;
    return -1;
}

static int is_north(int map) { return map >= MAP_FROSTPINE && map <= MAP_STARGAZER; }

/* ---------------- maps ---------------- */

static void test_edges(void)
{
    map_load(MAP_FROSTPINE);
    int ok = 1;
    for (int x = 0; x < map_w; x++) {
        int open = !(cell_attr(x, map_h - 1) & A_SOLID);
        if (open != (x == 11 || x == 12)) ok = 0;
    }
    CHECK(ok && MAPS[MAP_FROSTPINE].link[LINK_S] == MAP_RISE,
          "Frostpine Pass opens south onto Stormstone Rise at exactly x 11-12");
    map_load(MAP_WHITECROWN);
    ok = !(cell_attr(19, map_h - 1) & A_SOLID) && !(cell_attr(20, map_h - 1) & A_SOLID);
    map_load(MAP_FROSTHOLLOW);
    ok = ok && !(cell_attr(19, 0) & A_SOLID) && !(cell_attr(20, 0) & A_SOLID);
    CHECK(ok, "Frosthollow and Whitecrown Peak meet at x 19-20");
    CHECK(MAPS[MAP_SKY_ISLE].link[0] == MAP_NONE && MAPS[MAP_SKY_ISLE].link[1] == MAP_NONE &&
          MAPS[MAP_SKY_ISLE].link[2] == MAP_NONE && MAPS[MAP_SKY_ISLE].link[3] == MAP_NONE &&
          warp_from(MAP_FROSTHOLLOW, MAP_SKY_ISLE) < 0,
          "the SKY ISLE has no path in: FLY only");
    int fly = 0;
    for (int i = 0; i < FLY_POINT_COUNT; i++)
        fly += FLY_POINTS[i].map == MAP_FROSTHOLLOW || FLY_POINTS[i].map == MAP_SKY_ISLE;
    CHECK(fly == 2, "Frosthollow and the Sky Isle are fly points");
    CHECK((MAPS[MAP_GLIMMER_1].flags & MF_DARK) && (MAPS[MAP_GLIMMER_2].flags & MF_DARK) &&
          (MAPS[MAP_FROST_HEARTH].flags & MF_HEAL) && (MAPS[MAP_FROSTHOLLOW].flags & MF_TOWN),
          "the caverns are dark, the hearth heals, Frosthollow is a town");
}

static void test_rime_hall(void)
{
    map_load(MAP_RIME_HALL);
    int w = warp_from(MAP_FROSTHOLLOW, MAP_RIME_HALL);
    CHECK(w >= 0 && (cell_attr(WARPS[w].dx, WARPS[w].dy) & A_EXIT), "the Rime Hall door lands on its exit mat");
    int ice = 0;
    for (int y = 0; y < map_h; y++)
        for (int x = 0; x < map_w; x++) ice += (cell_attr(x, y) & A_ICE) != 0;
    CHECK(ice > 100, "the Rime Hall floor is a sheet of ice");
    int master = npc_on(MAP_RIME_HALL, SCR_RIME_MASTER);
    int pumice = -1, rocks = 0;
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].kind == OBJ_BOULDER) {
            pumice = i;
            rocks++;
        }
    CHECK(rocks == 1 && tobj[pumice].arg == 1, "the Rime Hall has one pumice boulder (no STRENGTH in a Hall)");
    slide_flood(WARPS[w].dx, WARPS[w].dy);
    CHECK(master >= 0 && !slide_beside(NPCS[master].x, NPCS[master].y),
          "with the pumice where it starts, MASTER SIGRUN can't be reached");
    /* the solver's answer (test_puzzles): push the pumice to 10,5, then slide
     * east along row 5 from the west wall and stop under the dais gap */
    int bx = tobj[pumice].x, by = tobj[pumice].y;
    tobj[pumice].x = 10;
    tobj[pumice].y = 5;
    grid_cell(bx, by);
    grid_cell(10, 5);
    slide_flood(WARPS[w].dx, WARPS[w].dy);
    CHECK(master >= 0 && slide_beside(NPCS[master].x, NPCS[master].y),
          "with the pumice pushed to 10,5, sliding by the rules reaches the Master");
    int wardens = 0, all = 1;
    for (int i = 0; i < NPC_COUNT; i++) {
        if (NPCS[i].map != MAP_RIME_HALL || NPCS[i].trainer == NO_TRAINER) continue;
        wardens++;
        if (!slide_beside(NPCS[i].x, NPCS[i].y)) all = 0;
    }
    CHECK(wardens >= 3 && wardens <= 5 && all, "the Hall's 3-5 wardens can all be reached on the ice");
    map_load(MAP_RIME_HALL);
    /* no straight shot: from any floor below the dais, one slide north never reaches it */
    int straight = 0;
    for (int y0 = 5; y0 < map_h; y0++)
        for (int x = 0; x < map_w; x++) {
            if ((cell_attr(x, y0) & A_ICE) || !cell_walkable(x, y0) || !cell_walkable(x, y0 - 1)) continue;
            int y = y0 - 1;
            while ((cell_attr(x, y) & A_ICE) && cell_walkable(x, y - 1)) y--;
            if ((cell_attr(x, y0 - 1) & A_ICE) && y <= 4) straight = 1;
        }
    CHECK(!straight, "the ice can't be crossed to the dais in one slide");
}

static void test_caves(void)
{
    int in = warp_from(MAP_FROSTHOLLOW, MAP_GLIMMER_1);
    int down = warp_from(MAP_GLIMMER_1, MAP_GLIMMER_2);
    int up = warp_from(MAP_GLIMMER_2, MAP_GLIMMER_1);
    int crack = warp_from(MAP_GLIMMER_2, MAP_STARFALL);
    CHECK(in >= 0 && down >= 0 && up >= 0 && crack >= 0, "cave mouth, stairs both ways and the crack exist");
    map_load(MAP_GLIMMER_1);
    flood(WARPS[in].dx, WARPS[in].dy);
    CHECK(reached(WARPS[down].x, WARPS[down].y + 1), "floor 1: from the mouth to the stairs down");
    flood(WARPS[up].dx, WARPS[up].dy);
    CHECK(reached(WARPS[in].dx, WARPS[in].dy), "floor 1: from the stairs back out to the mouth");
    map_load(MAP_GLIMMER_2);
    flood(WARPS[down].dx, WARPS[down].dy);
    CHECK(reached(WARPS[crack].x, WARPS[crack].y + 1) && reached(WARPS[up].x, WARPS[up].y + 1),
          "floor 2: from the stairs to the crack and back");
    map_load(MAP_STARFALL);
    flood(WARPS[crack].dx, WARPS[crack].dy);
    const MapObj *o = find_obj(MAP_STARFALL, OBJ_LEGEND);
    CHECK(o && o->arg == SP_SELENOTH && reached_beside(o->x, o->y) && (cell_attr(WARPS[crack].dx, WARPS[crack].dy) & A_EXIT),
          "the grotto: SELENOTH's lair is reachable and the mat leads back");
    CHECK(MAPS[MAP_GLIMMER_1].water_zone != ZONE_NONE, "the underground lake has water kin");
}

static void test_whitecrown(void)
{
    const MapObj *b = find_obj(MAP_WHITECROWN, OBJ_BOULDER);
    const MapObj *l = find_obj(MAP_WHITECROWN, OBJ_LEGEND);
    CHECK(b && l && l->arg == SP_HOARFANG, "Whitecrown has HOARFANG's lair and the STRENGTH boulder");
    if (!b || !l) return;
    map_load(MAP_WHITECROWN);
    int sx = 19, sy = map_h - 1;
    flood_block(sx, sy, b->x, b->y);
    CHECK(!bseen_beside(l->x, l->y), "the boulder seals the summit");
    /* push it: stand east of the boulder and push west until the way north opens */
    int bx = b->x, by = b->y, pushes = 0, open = 0;
    while (pushes < 40 && !open) {
        int px = bx + 1;
        flood_block(sx, sy, bx, by);
        if (!bseen[by * map_w + px]) break;            /* can't get behind it */
        if (!cell_walkable(bx - 1, by)) break;         /* stuck */
        int bi = boulder_at(bx, by);                   /* move traversal's boulder too */
        if (bi >= 0) {
            tobj[bi].x = (u8)(bx - 1);
            grid_cell(bx, by);
            grid_cell(bx - 1, by);
        }
        bx--;
        pushes++;
        flood_block(sx, sy, bx, by);
        open = bseen_beside(l->x, l->y);
    }
    CHECK(open, "pushing the boulder west into its pocket opens the way to the summit");
}

static void test_people(void)
{
    int ok = 1;
    for (int i = 0; i < NPC_COUNT; i++) {
        if (!is_north(NPCS[i].map) || NPCS[i].trainer == NO_TRAINER) continue;
        const TrainerDef *t = &TRAINERS[NPCS[i].trainer];
        if (t->count < 1 || t->count > TRAINER_TEAM_MAX) ok = 0;
        for (int k = 0; k < t->count; k++)
            if (t->species[k] >= SP_COUNT || SPECIES[t->species[k]].rarity == R_LEGEND ||
                SPECIES[t->species[k]].rarity == R_FUSION || t->level[k] < 18 || t->level[k] > 40)
                ok = 0;
    }
    const TrainerDef *m = &TRAINERS[TR_N_SIGRUN];
    CHECK(ok && m->count == 6, "north wardens field 1-6 non-legend kin at levels 18-40; Sigrun has six");
    int frost = 0;
    for (int k = 0; k < m->count; k++)
        frost += SPECIES[m->species[k]].type1 == T_FROST || SPECIES[m->species[k]].type2 == T_FROST;
    CHECK(frost == m->count, "every kin of the Rime Master is FROST");
    int src_ok = 1;
    for (int s = LSRC_YAK_HERDER; s <= LSRC_FROST_CLERK; s++) {
        int n = 0, lore = 0;
        for (int i = 0; i < NPC_COUNT; i++) n += NPCS[i].lore == s;
        for (int i = 0; i < LORE_COUNT; i++) lore += LORE[i].source == s;
        if (!n || !lore) {
            src_ok = 0;
            printf("  lore source %d: %d people, %d entries\n", s, n, lore);
        }
    }
    CHECK(src_ok, "every north lore source has a person and at least one entry");
    int wild = 1;
    for (int z = ZONE_FROSTPINE; z <= ZONE_GLIMMER_LAKE; z++)
        for (int i = 0; i < WILD_ZONES[z].count; i++)
            if (SPECIES[WILD_ZONES[z].slots[i].species].rarity >= R_LEGEND) wild = 0;
    CHECK(wild, "no legend or fusion kin roams the north wild");
}

static void talk_at(int map, int x, int y, int dir)
{
    field_enter_map(map, x, y, dir);
    settle();
    dialog_clear();
    tap(KEY_A);
    run_dialog(3000);
}

static void test_scripts(void)
{
    fresh_game();
    give_starter();
    /* the tender */
    party[0].hp = 1;
    talk_at(MAP_FROST_HEARTH, 5, 4, DIR_UP);
    CHECK(party[0].hp == party[0].max_hp, "the Frost Hearth tender rests the team");
    /* the shop opens its own stock */
    field_enter_map(MAP_FROST_SHOP, 1, 4, DIR_UP);
    dialog_clear();
    tap(KEY_A);
    for (int f = 0; f < 300 && game_mode != MODE_SHOP; f++) step((f & 3) == 0 ? KEY_A : 0);
    CHECK(game_mode == MODE_SHOP && shop_stock_count > 0 && shop_stock[shop_stock_count - 1] == ITEM_ASTRAL_SHARD,
          "the Frost Shop sells mountain goods");
    tap(KEY_B);
    run_dialog(400);
    game_mode = MODE_FIELD;
    /* quest 1: glowcaps */
    talk_at(MAP_FROSTHOLLOW, 24, 16, DIR_UP);
    CHECK(quest_get(QUEST_GLOWCAPS) == 1, "the ice carver asks for GLOWCAPS");
    bag_add(ITEM_GLOWCAP, 3);
    int stars = bag[ITEM_STAR_LANTERN];
    talk_at(MAP_FROSTHOLLOW, 24, 16, DIR_UP);
    CHECK(quest_done(QUEST_GLOWCAPS) && bag[ITEM_GLOWCAP] == 0 && bag[ITEM_STAR_LANTERN] == stars + 3,
          "three GLOWCAPS finish LAMPS FOR THE LONG NIGHT");
    int glow = 0;
    for (int i = 0; i < ITEM_BALL_COUNT; i++)
        glow += (ITEM_BALLS[i].map == MAP_GLIMMER_1 || ITEM_BALLS[i].map == MAP_GLIMMER_2) &&
                ITEM_BALLS[i].item == ITEM_GLOWCAP;
    CHECK(glow >= 3, "the caverns hold at least three GLOWCAPS");
    /* quest 2: the star chart */
    talk_at(MAP_STARGAZER, 7, 5, DIR_UP);
    CHECK(quest_get(QUEST_STAR_CHART) == 1, "the stargazer hands over her chart");
    talk_at(MAP_STARFALL, 18, 16, DIR_LEFT);
    CHECK(quest_get(QUEST_STAR_CHART) == 2 && bag[ITEM_STARDUST_CHIP] >= 1, "Dr. Maren takes the chart");
    int astral = bag[ITEM_ASTRAL_SHARD];
    talk_at(MAP_STARGAZER, 7, 5, DIR_UP);
    CHECK(quest_done(QUEST_STAR_CHART) && bag[ITEM_ASTRAL_SHARD] == astral + 1, "THE STAR CHART pays an ASTRAL SHARD");
    /* the Hall Master */
    party_heal_all();
    field_enter_map(MAP_RIME_HALL, 9, 3, DIR_UP);
    settle();
    dialog_clear();
    tap(KEY_A);
    for (int f = 0; f < 2000 && game_mode != MODE_BATTLE; f++) step((f & 3) == 0 ? KEY_A : 0);
    CHECK(game_mode == MODE_BATTLE && battle.master && battle.team_count == 6 &&
          battle.team[5].species == SP_WENDIGAUNT, "Master Sigrun fights a six-kin Hall Master bout");
    battle.result = BR_WIN;
    battle.state = BST_END;
    battle.timer = 16;
    for (int f = 0; f < 4 && game_mode == MODE_BATTLE; f++) step(0);
    run_dialog(3000);
    CHECK(flag(FLAG_RIME_CREST) && travel_has_crest(CREST_RIME) && lore_is_known(LORE_RIME_CREST) &&
          trainer_beaten(TR_N_SIGRUN), "winning awards the RIME CREST and its Lorebook page");
}

/* Frosthollow on its levels (docs/handoff/towns_north_grim.md) */
static void test_frosthollow(void)
{
    map_load(MAP_FROSTHOLLOW);
    field_load_tileset();
    int decor_ok = 1;
    for (int i = 0; i < MAPS[MAP_FROSTHOLLOW].decor_count; i++)
        if (!decor_base[MAPS[MAP_FROSTHOLLOW].decor[i].kind]) decor_ok = 0;
    CHECK(decor_ok, "Frosthollow: every decor kind fits the scene tiles (none silently dropped)");
    flood(19, map_h - 1);
    CHECK(reached_lv(19, 0, 3) && reached_lv(19, 24, 1) && reached_lv(19, 24, 0),
          "Frosthollow: the road climbs to Crownside over the Hollow Bridge; the Hollow lane runs under it");
    int w = warp_from(MAP_FROSTHOLLOW, MAP_HOT_SPRING);
    CHECK(w >= 0 && reached_lv(WARPS[w].x, WARPS[w].y + 1, 0) && elev_floor(WARPS[w].x, WARPS[w].y + 1) == 0,
          "Frosthollow: the bathhouse stands down in the Steam Hollow");
    int store = -1, watch = -1;
    for (int i = 0; i < ITEM_BALL_COUNT; i++) {
        if (ITEM_BALLS[i].map != MAP_FROSTHOLLOW) continue;
        if (ITEM_BALLS[i].item == ITEM_STAR_LANTERN) store = i;
        if (ITEM_BALLS[i].item == ITEM_WAYSTONE) watch = i;
    }
    CHECK(store >= 0 && watch >= 0 && reached_beside(ITEM_BALLS[store].x, ITEM_BALLS[store].y) &&
              reached_beside(ITEM_BALLS[watch].x, ITEM_BALLS[watch].y) && elev_hidden(11, 23) && elev_hidden(8, 5),
          "Frosthollow: the sunken store and the Watch are reached through hidden passages");
    CHECK(elev_floor(ITEM_BALLS[store].x, ITEM_BALLS[store].y) == 0 &&
              elev_floor(ITEM_BALLS[store].x + 2, ITEM_BALLS[store].y) == 1,
          "Frosthollow: the sunken store is a pit in the market terrace");
}

int main(void)
{
    test_edges();
    test_frosthollow();
    test_rime_hall();
    test_caves();
    test_whitecrown();
    test_people();
    test_scripts();
    if (failures) {
        printf("%d north check(s) FAILED\n", failures);
        return 1;
    }
    printf("all north checks passed\n");
    return 0;
}
