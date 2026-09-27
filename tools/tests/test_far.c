/*
 * FAR region checks (Cinder Road, Cindermoor, the Anvil Hall, Ember Tunnel,
 * Caldera Heart, Moonveil Path, Dreamspire, the Mirror Hall, the Dust
 * Library): edge contracts, the Anvil Hall's pumice puzzle solved by
 * search, the Mirror Hall's pads, the legends' lairs, both Hall Masters and
 * their crests, the two quests, shops, hearths, lore and wild kin.
 */
#include "harness.h"

/* ---------------- helpers ---------------- */

static int edge_open(int map, int side, int k)
{
    map_load(map);
    int x = side < 2 ? k : (side == LINK_W ? 0 : map_w - 1);
    int y = side < 2 ? (side == LINK_N ? 0 : map_h - 1) : k;
    return !(cell_attr(x, y) & (A_SOLID | A_WATER | A_LEDGE));
}

/* the walkable cells of an edge are exactly [a, b] */
static int edge_exactly(int map, int side, int a, int b)
{
    map_load(map);
    int len = side < 2 ? map_w : map_h;
    for (int k = 0; k < len; k++)
        if (edge_open(map, side, k) != (k >= a && k <= b)) return 0;
    return 1;
}

static int npc_index(int map, int script)
{
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].map == map && NPCS[i].script == script) return i;
    return -1;
}

/* Stand south of NPC i (or north if that is blocked) and talk. */
static void talk_to(int i)
{
    const NpcDef *n = &NPCS[i];
    map_load(n->map);
    int dy = cell_walkable(n->x, n->y + 1) || (cell_attr(n->x, n->y + 1) & A_COUNTER) ? 1 : -1;
    int y = n->y + dy;
    if (cell_attr(n->x, y) & A_COUNTER) y += dy;
    field_enter_map(n->map, n->x, y, dy > 0 ? DIR_UP : DIR_DOWN);
    for (int f = 0; f < 200 && dialog_active(); f++) step((f & 3) == 0 ? KEY_A : 0);
    tap(KEY_A);
    for (int f = 0; f < 3000 && dialog_active() && game_mode == MODE_FIELD; f++) step((f & 3) == 0 ? KEY_A : 0);
}

static void win_bout(void)
{
    battle.result = BR_WIN;
    battle.state = BST_END;
    battle.timer = 16;
    for (int f = 0; f < 3000 && game_mode == MODE_BATTLE; f++) step((f & 7) == 0 ? KEY_A : 0);
    run_dialog(3000);
}

/* ---------------- the Anvil Hall puzzle, solved by search ---------------- */

#define AH_MAXB 4
typedef struct { u8 px, py, bx[AH_MAXB], by[AH_MAXB]; } AhState;

static const MapObj *ah_obj;
static int ah_nobj, ah_nb;
static u8 ah_wall[64 * 64], ah_gate[64 * 64];   /* gate: its group + 1 */

static int ah_boulder_at(const AhState *s, int x, int y)
{
    for (int i = 0; i < ah_nb; i++)
        if (s->bx[i] == x && s->by[i] == y) return i;
    return -1;
}

static int ah_gate_open(const AhState *s, int group)
{
    for (int i = 0; i < ah_nobj; i++)
        if (ah_obj[i].kind == OBJ_PLATE && ah_obj[i].arg == group && ah_boulder_at(s, ah_obj[i].x, ah_obj[i].y) < 0)
            return 0;
    return 1;
}

static int ah_blocked(const AhState *s, int x, int y)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h || ah_wall[y * map_w + x]) return 1;
    int g = ah_gate[y * map_w + x];
    return g && !ah_gate_open(s, g - 1);
}

static u32 ah_hash(const AhState *s)
{
    u32 h = 2166136261u;
    const u8 *p = (const u8 *)s;
    for (unsigned i = 0; i < sizeof(*s); i++) h = (h ^ p[i]) * 16777619u;
    return h;
}

#define AH_QMAX 1500000
#define AH_HMAX (1 << 22)
static AhState ah_q[AH_QMAX];
static u32 ah_seen[AH_HMAX];   /* hash | 1, open addressing */
static u32 ah_reach[64 * 64], ah_gen;

static int ah_visit(const AhState *s)
{
    u32 h = ah_hash(s) | 1u;
    for (u32 k = h & (AH_HMAX - 1);; k = (k + 1) & (AH_HMAX - 1)) {
        if (ah_seen[k] == h) return 0;
        if (!ah_seen[k] || k == ((h - 1) & (AH_HMAX - 1))) {   /* never loop forever */
            ah_seen[k] = h;
            return 1;
        }
    }
}

static int ah_on_plate(const AhState *s, int b)
{
    for (int i = 0; i < ah_nobj; i++)
        if (ah_obj[i].kind == OBJ_PLATE && ah_obj[i].x == s->bx[b] && ah_obj[i].y == s->by[b]) return 1;
    return 0;
}

/* A boulder off a plate, in a corner of walls, can never move again. */
static int ah_dead(const AhState *s, int b)
{
    int x = s->bx[b], y = s->by[b];
    for (int i = 0; i < ah_nobj; i++)
        if (ah_obj[i].kind == OBJ_PLATE && ah_obj[i].x == x && ah_obj[i].y == y) return 0;
    int n = ah_blocked(s, x, y - 1), so = ah_blocked(s, x, y + 1);
    int w = ah_blocked(s, x - 1, y), e = ah_blocked(s, x + 1, y);
    return (n || so) && (w || e);
}

/* Flood the player's walkable region (no pushing) into ah_reach and move
 * the player to its first cell, so states differ only by boulders + region. */
static void ah_region(AhState *s)
{
    static int qx[64 * 64], qy[64 * 64];
    ah_gen++;
    int h = 0, t = 0, best = s->py * map_w + s->px;
    qx[t] = s->px;
    qy[t++] = s->py;
    ah_reach[best] = ah_gen;
    while (h < t) {
        int x = qx[h], y = qy[h++];
        if (y * map_w + x < best) best = y * map_w + x;
        for (int d = 0; d < 4; d++) {
            int nx = x + DIR_DX[d], ny = y + DIR_DY[d];
            if (ah_blocked(s, nx, ny) || ah_boulder_at(s, nx, ny) >= 0 || ah_reach[ny * map_w + nx] == ah_gen) continue;
            ah_reach[ny * map_w + nx] = ah_gen;
            qx[t] = nx;
            qy[t++] = ny;
        }
    }
    s->px = (u8)(best % map_w);
    s->py = (u8)(best / map_w);
}

/* Can the player reach a cell beside (tx, ty) from the entrance, pushing
 * pumice boulders (people and walls block; gates open while their plates
 * are covered)? Sokoban search over boulder positions. */
static int anvil_hall_solvable(int tx, int ty)
{
    map_load(MAP_ANVIL_HALL);
    const MapDef *d = &MAPS[MAP_ANVIL_HALL];
    ah_obj = d->objs;
    ah_nobj = d->obj_count;
    AhState s0;
    memset(&s0, 0, sizeof(s0));
    ah_nb = 0;
    for (int i = 0; i < ah_nobj; i++)
        if (ah_obj[i].kind == OBJ_BOULDER && ah_nb < AH_MAXB) {
            s0.bx[ah_nb] = ah_obj[i].x;
            s0.by[ah_nb++] = ah_obj[i].y;
        }
    for (int y = 0; y < map_h; y++)
        for (int x = 0; x < map_w; x++)
            /* the solver models boulders and gates itself: raw cells, not traversal's */
            ah_wall[y * map_w + x] = (cell_attr_raw(x, y) & A_SOLID) || npc_at(x, y) >= 0 || item_ball_at(x, y) >= 0;
    memset(ah_gate, 0, sizeof(ah_gate));
    for (int i = 0; i < ah_nobj; i++)
        if (ah_obj[i].kind == OBJ_GATE) ah_gate[ah_obj[i].y * map_w + ah_obj[i].x] = (u8)(ah_obj[i].arg + 1);
    for (int i = 0; i < WARP_COUNT; i++)
        if (WARPS[i].dest == MAP_ANVIL_HALL) {
            s0.px = WARPS[i].dx;
            s0.py = WARPS[i].dy;
        }
    memset(ah_seen, 0, sizeof(ah_seen));
    ah_region(&s0);
    int head = 0, tail = 0;
    ah_q[tail++] = s0;
    ah_visit(&s0);
    while (head < tail) {
        AhState s = ah_q[head++];
        ah_region(&s);
        for (int d2 = 0; d2 < 4; d2++) {
            int ax = tx + DIR_DX[d2], ay = ty + DIR_DY[d2];
            if (ax >= 0 && ay >= 0 && ax < map_w && ay < map_h && ah_reach[ay * map_w + ax] == ah_gen) return 1;
        }
        static u8 reach[64 * 64];
        for (int k = 0; k < map_w * map_h; k++) reach[k] = ah_reach[k] == ah_gen;
        for (int b = 0; b < ah_nb; b++)
            for (int d2 = 0; d2 < 4 && !ah_on_plate(&s, b); d2++) {   /* placed boulders stay */
                int px = s.bx[b] - DIR_DX[d2], py = s.by[b] - DIR_DY[d2];
                int bx = s.bx[b] + DIR_DX[d2], by = s.by[b] + DIR_DY[d2];
                if (px < 0 || py < 0 || px >= map_w || py >= map_h || !reach[py * map_w + px]) continue;
                if (ah_blocked(&s, bx, by) || ah_boulder_at(&s, bx, by) >= 0) continue;
                AhState n = s;
                n.bx[b] = (u8)bx;
                n.by[b] = (u8)by;
                n.px = s.bx[b];
                n.py = s.by[b];
                if (ah_dead(&n, b)) continue;
                ah_region(&n);
                if (ah_visit(&n) && tail < AH_QMAX) ah_q[tail++] = n;
            }
    }
    return 0;
}

/* ---------------- main ---------------- */

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    fresh_game();
    give_starter();

    /* edge contracts (docs/EXPANSION.md 9) */
    CHECK(edge_exactly(MAP_CINDER_ROAD, LINK_W, 20, 21) && edge_exactly(MAP_CINDER_ROAD, LINK_E, 20, 21) &&
              edge_exactly(MAP_CINDERMOOR, LINK_W, 20, 21),
          "CINDER ROAD and CINDERMOOR keep the y20-21 road opening");
    CHECK(edge_exactly(MAP_MOONVEIL, LINK_S, 24, 25) && edge_exactly(MAP_MOONVEIL, LINK_N, 24, 25) &&
              edge_exactly(MAP_DREAMSPIRE, LINK_S, 24, 25),
          "MOONVEIL PATH and DREAMSPIRE keep the x24-25 opening");
    CHECK(MAPS[MAP_CINDER_ROAD].link[LINK_W] == MAP_RAILHEAD && MAPS[MAP_MOONVEIL].link[LINK_S] == MAP_MISTFEN &&
              MAPS[MAP_CINDER_CROSSING].link[LINK_W] == MAP_LUMEN && MAPS[MAP_MISTFEN].link[LINK_S] == MAP_LUMEN,
          "new Far route segments attach to Lumen on the Far side only");

    /* towns, fly points, hearths */
    int fly_c = 0, fly_d = 0;
    for (int i = 0; i < FLY_POINT_COUNT; i++) {
        fly_c |= FLY_POINTS[i].map == MAP_CINDERMOOR;
        fly_d |= FLY_POINTS[i].map == MAP_DREAMSPIRE;
    }
    CHECK(fly_c && fly_d && (MAPS[MAP_CINDERMOOR].flags & MF_TOWN) && (MAPS[MAP_DREAMSPIRE].flags & MF_TOWN),
          "CINDERMOOR and DREAMSPIRE are fly points");
    CHECK((MAPS[MAP_CINDER_HEARTH].flags & MF_HEAL) && (MAPS[MAP_DREAM_HEARTH].flags & MF_HEAL),
          "both towns have a Hearth Hall");

    /* the Anvil Hall: pumice boulders, plates and gates */
    const MapDef *ah = &MAPS[MAP_ANVIL_HALL];
    int pumice = 1, plates = 0, gates = 0;
    for (int i = 0; i < ah->obj_count; i++) {
        if (ah->objs[i].kind == OBJ_BOULDER && ah->objs[i].arg != 1) pumice = 0;
        plates += ah->objs[i].kind == OBJ_PLATE;
        gates += ah->objs[i].kind == OBJ_GATE;
    }
    CHECK(pumice && plates == 4 && gates == 2, "the ANVIL HALL has pumice boulders (arg 1), 4 plates and 2 gates");
    int m_bron = npc_index(MAP_ANVIL_HALL, SCR_ANVIL_MASTER);
    CHECK(m_bron >= 0 && anvil_hall_solvable(NPCS[m_bron].x, NPCS[m_bron].y),
          "the ANVIL HALL can be solved: pushing pumice onto the plates opens a way to BRONWEN");
    {
        /* and not without pushing: with every gate shut the Master is out of reach */
        map_load(MAP_ANVIL_HALL);
        int ex = 8, ey = 21;
        flood(ex, ey);
        int gy = 0;
        for (int i = 0; i < ah->obj_count; i++)
            if (ah->objs[i].kind == OBJ_GATE && ah->objs[i].arg == 1) gy = ah->objs[i].y;
        int walled = 1;
        for (int x = 0; x < map_w; x++)
            if (x != 8 && !(cell_attr(x, gy) & A_SOLID)) walled = 0;
        CHECK(walled, "the gates are the only ways between the ANVIL HALL's chambers");
    }

    /* the Mirror Hall: its rooms are joined by pads only */
    map_load(MAP_MIRROR_HALL);
    CHECK(cell_attr(2, 21) & A_EXIT, "the MIRROR HALL door lands on its hall mat (2,21)");
    flood_ex(2, 21, FLOOD_SOLVED);   /* pads followed */
    int m_ves = npc_index(MAP_MIRROR_HALL, SCR_DREAM_MASTER);
    CHECK(m_ves >= 0 && reached_beside(NPCS[m_ves].x, NPCS[m_ves].y), "the MIRROR HALL's pads lead to VESPER");
    {
        /* without the pads the Master's room is cut off */
        memset(seen_cells, 0, sizeof(seen_cells));
        static int qx[64 * 64], qy[64 * 64];
        int h = 0, t = 0;
        qx[t] = 2;
        qy[t++] = 21;
        seen_cells[21 * map_w + 2] = 1;
        while (h < t) {
            int x = qx[h], y = qy[h++];
            for (int d = 0; d < 4; d++) {
                int nx = x + DIR_DX[d], ny = y + DIR_DY[d];
                if (nx < 0 || ny < 0 || nx >= map_w || ny >= map_h || seen_cells[ny * map_w + nx] ||
                    !cell_walkable(nx, ny))
                    continue;
                seen_cells[ny * map_w + nx] = 1;
                qx[t] = nx;
                qy[t++] = ny;
            }
        }
        CHECK(!reached_beside(NPCS[m_ves].x, NPCS[m_ves].y), "on foot alone, VESPER's room is out of reach");
    }
    int pads_paired = 1;
    for (int i = 0; i < MAPS[MAP_MIRROR_HALL].obj_count; i++) {
        const MapObj *o = &MAPS[MAP_MIRROR_HALL].objs[i];
        int twins = 0;
        for (int j = 0; j < MAPS[MAP_MIRROR_HALL].obj_count; j++)
            twins += MAPS[MAP_MIRROR_HALL].objs[j].kind == OBJ_PAD && MAPS[MAP_MIRROR_HALL].objs[j].arg == o->arg;
        if (o->kind == OBJ_PAD && twins != 2) pads_paired = 0;
    }
    CHECK(pads_paired, "every Mirror Hall pad has exactly one twin");
    {
        /* the mirror: each west room's doorway barrier has an east twin of the
         * same group that starts the other way (one switch opens one, shuts the other) */
        int mirrored = 0, doorways = 0;
        for (int i = 0; i < MAPS[MAP_MIRROR_HALL].obj_count; i++) {
            const MapObj *o = &MAPS[MAP_MIRROR_HALL].objs[i];
            if (o->kind != OBJ_BARRIER || o->x >= 10) continue;
            doorways++;
            for (int j = 0; j < MAPS[MAP_MIRROR_HALL].obj_count; j++) {
                const MapObj *t = &MAPS[MAP_MIRROR_HALL].objs[j];
                if (t->kind == OBJ_BARRIER && t->y == o->y && t->x == o->x + 10 && (t->arg & 15) == (o->arg & 15) &&
                    (t->arg & 0x80) != (o->arg & 0x80))
                    mirrored++;
            }
        }
        CHECK(doorways == 3 && mirrored == 3, "the MIRROR HALL's three doorway pairs are mirrored barriers");
    }

    /* legends in their lairs */
    int lairs = 0;
    for (int m = 0; m < 2; m++) {
        int map = m ? MAP_DUST_LIBRARY : MAP_CALDERA, sp = m ? SP_SCRIPTORA : SP_CALDERON;
        const MapDef *d = &MAPS[map];
        map_load(map);
        int ex = 0, ey = 0;
        for (int i = 0; i < WARP_COUNT; i++)
            if (WARPS[i].dest == map) {
                ex = WARPS[i].dx;
                ey = WARPS[i].dy;
            }
        flood(ex, ey);
        for (int i = 0; i < d->obj_count; i++)
            if (d->objs[i].kind == OBJ_LEGEND && d->objs[i].arg == sp && reached_beside(d->objs[i].x, d->objs[i].y))
                lairs++;
    }
    CHECK(lairs == 2, "CALDERON waits in the CALDERA HEART and SCRIPTORA in the DUST LIBRARY, both reachable");
    const MapDef *et = &MAPS[MAP_EMBER_TUNNEL];
    int strength = 0;
    for (int i = 0; i < et->obj_count; i++) strength += et->objs[i].kind == OBJ_BOULDER && et->objs[i].arg == 0;
    CHECK(strength >= 1, "STRENGTH boulders guard the way through the EMBER TUNNEL");

    /* wardens: at most 6 kin, masters exactly 6 */
    int teams_ok = 1;
    for (int t = TR_CR_OSKAR; t <= TR_DL_QUILL; t++)
        if (TRAINERS[t].count < 1 || TRAINERS[t].count > 6) teams_ok = 0;
    CHECK(teams_ok && TRAINERS[TR_MASTER_BRONWEN].count == 6 && TRAINERS[TR_MASTER_VESPER].count == 6,
          "far wardens have 1-6 kin and both Hall Masters bring 6");

    /* Hall Master BRONWEN: a Master bout, then the ANVIL CREST */
    party_heal_all();
    talk_to(m_bron);
    CHECK(game_mode == MODE_BATTLE && battle.master && battle.team_count == 6 &&
              battle.team[5].species == SP_FOUNDRAKE,
          "MASTER BRONWEN starts a 6-kin Hall Master bout");
    win_bout();
    CHECK(flag(FLAG_CREST_ANVIL) && travel_has_crest(CREST_ANVIL) && trainer_beaten(TR_MASTER_BRONWEN) &&
              bag[ITEM_HEAVY_LANTERN] >= 3,
          "beating BRONWEN awards the ANVIL CREST");
    talk_to(m_bron);
    CHECK(game_mode == MODE_FIELD, "BRONWEN doesn't ask for a rematch");

    /* Hall Master VESPER */
    party_heal_all();
    talk_to(m_ves);
    CHECK(game_mode == MODE_BATTLE && battle.master && battle.team[5].species == SP_SLUMBAKU,
          "MASTER VESPER starts a 6-kin Hall Master bout");
    win_bout();
    CHECK(flag(FLAG_CREST_DREAM) && travel_has_crest(CREST_DREAM), "beating VESPER awards the DREAM CREST");

    /* IRON FOR THE BELL */
    int founder = npc_index(MAP_CINDERMOOR, SCR_FOUNDER);
    talk_to(founder);
    CHECK(quest_get(QUEST_IRON_BELL) == 1, "FOUNDER HALVARD asks for iron");
    bag[ITEM_IRON_ORE] = 2;
    talk_to(founder);
    CHECK(quest_get(QUEST_IRON_BELL) == 1 && bag[ITEM_IRON_ORE] == 2, "two ore is not enough");
    int ore_satchels = 0;
    for (int i = 0; i < ITEM_BALL_COUNT; i++)
        if (ITEM_BALLS[i].item == ITEM_IRON_ORE &&
            (ITEM_BALLS[i].map == MAP_CINDER_ROAD || ITEM_BALLS[i].map == MAP_EMBER_TUNNEL))
            ore_satchels += ITEM_BALLS[i].qty;
    CHECK(ore_satchels >= 3, "at least 3 IRON ORE lie in satchels on the road and in the tunnel");
    bag[ITEM_IRON_ORE] = 3;
    int coins = money;
    talk_to(founder);
    CHECK(quest_done(QUEST_IRON_BELL) && bag[ITEM_IRON_ORE] == 0 && bag[ITEM_METAL_SHARD] >= 1 && money == coins + 1500,
          "three IRON ORE recast the bell: a METAL SHARD and 1500 coins");

    /* THE DRIFTING VERSES */
    int poet = npc_index(MAP_DREAMSPIRE, SCR_POET);
    int sleepers[3], ns = 0;
    for (int i = 0; i < NPC_COUNT && ns < 3; i++)
        if (NPCS[i].script == SCR_SLEEPER) sleepers[ns++] = i;
    CHECK(ns == 3 && NPCS[sleepers[0]].map != NPCS[sleepers[1]].map && NPCS[sleepers[1]].map != NPCS[sleepers[2]].map,
          "three sleepers on three maps");
    talk_to(sleepers[0]);
    CHECK(!flag(FLAG_VERSE_1) && !flag(FLAG_VERSE_2) && !flag(FLAG_VERSE_3), "sleepers only mumble before the quest");
    talk_to(poet);
    CHECK(quest_get(QUEST_DRIFTING_VERSES) == 1, "POET ISOLDE asks for her verses");
    for (int k = 0; k < 3; k++) talk_to(sleepers[k]);
    CHECK(flag(FLAG_VERSE_1) && flag(FLAG_VERSE_2) && flag(FLAG_VERSE_3) && quest_get(QUEST_DRIFTING_VERSES) == 4,
          "each sleeper gives one verse");
    talk_to(poet);
    CHECK(quest_done(QUEST_DRIFTING_VERSES) && bag[ITEM_MOONCAKE] >= 3, "the whole poem earns MOONCAKES");

    /* shops and hearths */
    int stock_ok = 0;
    for (int k = 0; k < 2; k++) {
        talk_to(npc_index(k ? MAP_DREAM_SHOP : MAP_CINDER_SHOP, k ? SCR_DREAM_CLERK : SCR_CINDER_CLERK));
        stock_ok += game_mode == MODE_SHOP && shop_stock == (k ? DREAM_STOCK : CINDER_STOCK);
        for (int f = 0; f < 60 && game_mode == MODE_SHOP; f++) step((f & 3) == 0 ? KEY_B : 0);
        run_dialog(400);
    }
    CHECK(stock_ok == 2 && game_mode == MODE_FIELD, "both town shops open with their own stock");
    int all_priced = 1;
    for (unsigned i = 0; i < sizeof(CINDER_STOCK); i++) all_priced &= ITEMS[CINDER_STOCK[i]].price > 0;
    for (unsigned i = 0; i < sizeof(DREAM_STOCK); i++) all_priced &= ITEMS[DREAM_STOCK[i]].price > 0;
    CHECK(all_priced, "everything the far shops sell has a price");
    party[0].hp = 1;
    talk_to(npc_index(MAP_CINDER_HEARTH, SCR_CINDER_TENDER));
    CHECK(party[0].hp == party[0].max_hp, "the CINDER HEARTH HALL restores the team");
    party[0].hp = 1;
    talk_to(npc_index(MAP_DREAM_HEARTH, SCR_DREAM_TENDER));
    CHECK(party[0].hp == party[0].max_hp, "the SPIRE HEARTH HALL restores the team");

    /* lore: every far source has entries, and someone tells them */
    int lore_ok = 1;
    for (int src = LSRC_CINDER_ELDER; src <= LSRC_LIBRARIAN; src++) {
        int entries = 0, teller = 0;
        for (int i = 0; i < LORE_COUNT; i++) entries += LORE[i].source == src;
        for (int i = 0; i < NPC_COUNT; i++) teller |= NPCS[i].lore == src;
        if (!entries || !teller) {
            lore_ok = 0;
            printf("  lore source %d: %d entries, teller %d\n", src, entries, teller);
        }
    }
    CHECK(lore_ok, "every far lore source has pages and a person who tells them");
    int before = lore_known_count();
    talk_to(npc_index(MAP_DUST_LIBRARY, SCR_TALK) >= 0 ? npc_index(MAP_DUST_LIBRARY, SCR_TALK) : 0);
    CHECK(lore_known_count() == before + 1, "the LIBRARIAN adds a Lorebook page");

    /* wild kin */
    int night_baku = 0, levels_ok = 1;
    const WildZone *z = &WILD_ZONES[ZONE_DREAMSPIRE];
    for (int i = 0; i < z->count; i++) night_baku |= z->slots[i].species == SP_SLUMBAKU && z->slots[i].when == WHEN_NIGHT;
    for (int zi = ZONE_CINDER_ROAD; zi <= ZONE_DUST_LIBRARY; zi++)
        for (int i = 0; i < WILD_ZONES[zi].count; i++) {
            const WildSlot *s = &WILD_ZONES[zi].slots[i];
            if (s->min_level < 26 || s->max_level > (zi < ZONE_MOONVEIL ? 32 : 43) || s->min_level > s->max_level ||
                SPECIES[s->species].rarity == R_LEGEND || SPECIES[s->species].rarity == R_FUSION)
                levels_ok = 0;
        }
    CHECK(night_baku, "SLUMBAKU roams DREAMSPIRE at night");
    CHECK(levels_ok, "re-levelled far wild kin stay within Act IV/VII bands and exclude legends");

    /* Region-local G3 contract; repair branch needs E5 map patches + saga flag. */
    CHECK(edge_exactly(MAP_CINDER_CROSSING, LINK_W, 20, 21) &&
          edge_exactly(MAP_CINDER_CROSSING, LINK_E, 20, 21) &&
          edge_exactly(MAP_RAILHEAD, LINK_W, 20, 21) &&
          edge_exactly(MAP_RAILHEAD, LINK_E, 20, 21),
          "Crossing and Railhead retain both y20-21 edge openings");
    map_load(MAP_CINDER_CROSSING);
    int river = 1;
    for (int y = 2; y < 34; y++)
        for (int x = 6; x <= 9; x++) river &= !!(cell_attr(x, y) & A_WATER);
    CHECK(river, "G3 is a continuous four-cell-wide surfable river");
    flood_ex(2, 20, FLOOD_WALK);
    CHECK(!seen_cells[20 * map_w + 58], "G3 cannot be crossed on foot before bridge repair");
    flood_ex(2, 20, FLOOD_SURF);
    CHECK(!!seen_cells[20 * map_w + 58], "SURF crosses G3 to Railhead");
    CHECK(edge_exactly(MAP_MISTFEN, LINK_S, 24, 25) &&
          edge_exactly(MAP_MISTFEN, LINK_N, 24, 25),
          "Mistfen preserves Lumen and Moonveil x24-25 openings");
    map_load(MAP_MISTFEN);
    flood(24, 58);
    CHECK(!seen_cells[1 * map_w + 24], "G6 fog wall blocks the northern road until E5 patching");
    CHECK(WILD_ZONES[ZONE_MISTFEN].slots[0].min_level == 37 &&
          WILD_ZONES[ZONE_CROSSING].slots[0].min_level == 24 &&
          WILD_ZONES[ZONE_CROSSING_WATER].slots[0].min_level == 25,
          "new routes use Act IV and Act VII level bands");
    CHECK((MAPS[MAP_PILGRIM_REST].flags & MF_HEAL) &&
          (MAPS[MAP_RAILHEAD_BUNK].flags & MF_HEAL),
          "both new mid-route stops heal the party");

    if (failures == 0) {
        printf("all far checks passed\n");
        return 0;
    }
    printf("%d check(s) FAILED\n", failures);
    return 1;
}
