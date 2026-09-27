/* Host-only diagnostic against live world tables and the shipped XP curve.
 * Treat all mapped wardens and satchels as accessible: this is an upper
 * bound on encounters and sellable loot until the critical path is gated. */
typedef struct { const char *name; int master; int maps[10]; } QaAct;
static const QaAct QA_ACTS[] = {
    {"I Home", TR_MARLO, {MAP_MEADOW, MAP_WOOD, MAP_LAKE, MAP_RISE, MAP_NONE}},
    {"II East", TR_FARA, {MAP_BROOKMILL_TRAIL, MAP_BROOKMILL, MAP_COPPERLINE, MAP_LUMEN, MAP_VOLT_HALL, MAP_NONE}},
    {"III West", TR_MAREN, {MAP_HERON_FEN, MAP_REEDWICK, MAP_SALTWIND, MAP_PORT_BRINE, MAP_CURRENT_HALL, MAP_NONE}},
    {"IV Forge", TR_MASTER_BRONWEN, {MAP_CINDER_CROSSING, MAP_RAILHEAD, MAP_CINDER_ROAD, MAP_CINDERMOOR, MAP_EMBER_TUNNEL, MAP_ANVIL_HALL, MAP_NONE}},
    {"V North", TR_N_SIGRUN, {MAP_FOOTHILLS, MAP_TIMBERLINE, MAP_FROSTPINE, MAP_FROSTHOLLOW, MAP_GLIMMER_1, MAP_GLIMMER_2, MAP_RIME_HALL, MAP_NONE}},
    {"VI Ash", TR_MORWEN, {MAP_HOLLOW_DOWNS, MAP_ASHEN_FIELDS, MAP_GRAVEWOOD, MAP_DUSKMERE, MAP_LANTERN_CRYPT, MAP_NONE}},
    {"VII Dream", TR_MASTER_VESPER, {MAP_MISTFEN, MAP_MOONVEIL, MAP_DREAMSPIRE, MAP_DUST_LIBRARY, MAP_MIRROR_HALL, MAP_NONE}},
    {"VIII Finale", -1, {MAP_OSSUARY_1, MAP_OSSUARY_2, MAP_BONE_THRONE, MAP_NONE}}
};
#define QA_ACT_COUNT ((int)(sizeof(QA_ACTS) / sizeof(QA_ACTS[0])))

static int qa_lead_slot;

static void qa_gain(int species, int level, int trainer)
{
    Monster foe = monster_make(species, level);
    int xp = monster_xp_yield(&foe, trainer);
    int lead = qa_lead_slot++ % party_count;
    for (int p = 0; p < party_count; p++) {
        Monster *m = &party[p];
        m->xp += p == lead ? xp : xp / 2; /* round-robin lead, half XP for each bench kin */
        while (m->level < MAX_LEVEL && m->xp >= xp_for_level(m->level + 1)) m->level++;
    }
}

static int qa_zone_bouts(int map)
{
    int zone = MAPS[map].zone;
    if (zone <= ZONE_EMPTY || zone >= ZONE_COUNT || !WILD_ZONES[zone].count) return 0;
    if (map == MAP_BROOKMILL || map == MAP_REEDWICK || map == MAP_RAILHEAD || map == MAP_TIMBERLINE) return 3;
    return 6;
}

static void qa_wild(int map, int bouts)
{
    const WildZone *z = &WILD_ZONES[MAPS[map].zone];
    int weight = 0;
    for (int i = 0; i < z->count; i++) weight += z->slots[i].weight;
    if (!weight) return;
    /* Fixed weighted quantiles across slots, including day/night variants. */
    for (int b = 0; b < bouts; b++) {
        int pick = (2 * b + 1) * weight / (2 * bouts);
        int i = 0;
        while (i + 1 < z->count && pick >= z->slots[i].weight) pick -= z->slots[i++].weight;
        const WildSlot *slot = &z->slots[i];
        qa_gain(slot->species, (slot->min_level + slot->max_level) / 2, 0);
    }
}

static void qa_team_join(int map)
{
    if (party_count >= 4 || !qa_zone_bouts(map)) return;
    const WildSlot *slot = &WILD_ZONES[MAPS[map].zone].slots[0];
    Monster m = monster_make(slot->species, (slot->min_level + slot->max_level) / 2);
    m.trait = TR_SURGE; m.bond = 0; /* neutral XP traits and bond */
    give_monster(&m);
}

static void qa_act_pass(int include_wild)
{
    fresh_game();
    Monster starter = monster_make(SP_FLARIX, 5);
    starter.trait = TR_SURGE; starter.bond = 0;
    give_monster(&starter);
    qa_lead_slot = 0;
    int coins = money, seen[TRAINER_ID_COUNT] = {0};
    for (int a = 0; a < QA_ACT_COUNT; a++) {
        const QaAct *act = &QA_ACTS[a];
        int wardens = 0, wilds = 0, satchels = 0;
        for (int j = 0; j < 10 && act->maps[j] != MAP_NONE; j++) {
            int map = act->maps[j], bouts = qa_zone_bouts(map);
            qa_team_join(map);
            if (include_wild && bouts) { qa_wild(map, bouts); wilds += bouts; }
            for (int n = 0; n < NPC_COUNT; n++) {
                const NpcDef *npc = &NPCS[n];
                int t = npc->trainer;
                if (npc->map != map || npc->script != SCR_WARDEN || t >= TRAINER_ID_COUNT ||
                    t == act->master || seen[t]) continue;
                seen[t] = 1;
                const TrainerDef *tr = &TRAINERS[t];
                for (int k = 0; k < tr->count; k++) qa_gain(tr->species[k], tr->level[k], 1);
                coins += tr->prize; wardens++;
            }
            for (int n = 0; n < ITEM_BALL_COUNT; n++)
                if (ITEM_BALLS[n].map == map)
                    satchels += ITEM_BALLS[n].qty * item_sell_price(ITEM_BALLS[n].item);
        }
        /* One mature Glowberry plot sold per act, when in season; no seed costs. */
        int harvest = CROPS[CROP_GLOWBERRY].yield * CROPS[CROP_GLOWBERRY].value;
        coins += satchels + harvest;
        int lowest = 0;
        if (act->master >= 0) {
            const TrainerDef *tr = &TRAINERS[act->master];
            lowest = 100;
            for (int k = 0; k < tr->count; k++) if (tr->level[k] < lowest) lowest = tr->level[k];
        }
        int levels = 0;
        for (int p = 0; p < party_count; p++) levels += party[p].level;
        int mean = levels / party_count;
        printf("QA %s: team-mean %d levels %d/%d/%d/%d master-min %d delta %+d wardens %d wild %d coins %d (satchels %d harvest %d)\n",
               act->name, mean, party[0].level, party_count > 1 ? party[1].level : 0,
               party_count > 2 ? party[2].level : 0, party_count > 3 ? party[3].level : 0,
               lowest, lowest ? mean - lowest : 0, wardens, wilds, coins, satchels, harvest);
        if (include_wild && lowest) {
            char label[120];
            snprintf(label, sizeof(label), "%s arrival team mean within 2 levels of lowest Master kin", act->name);
            CHECK(mean >= lowest - 2 && mean <= lowest + 2, label);
            snprintf(label, sizeof(label), "%s team needs no grinding (at least Master minus 4)", act->name);
            CHECK(mean >= lowest - 4, label);
        }
        if (include_wild) {
            static const char *projects[] = {"tram", "bridge", "lift", "Reedwick ferry", "market"};
            static const int costs[] = {3000, 4000, 2500, 2000, 6000};
            static const int deadlines[] = {2, 4, 5, 4, 6};
            if (a == 2) CHECK(coins >= 500, "Act III ferry costs at most earned coins (before spending)");
            for (int p = 0; p < 5; p++) if (deadlines[p] == a) {
                char label[120];
                snprintf(label, sizeof(label), "%s %dc affordable by following act (before spending/materials)",
                         projects[p], costs[p]);
                CHECK(coins >= costs[p], label);
            }
        }
        if (act->master >= 0) {
            const TrainerDef *tr = &TRAINERS[act->master];
            for (int k = 0; k < tr->count; k++) qa_gain(tr->species[k], tr->level[k], 1);
            coins += tr->prize;
        }
    }
}

static void test_act_balance(void)
{
    CHECK(QA_ACT_COUNT == 8 && TRAINERS[TR_FARA].count > 0 && qa_zone_bouts(MAP_BROOKMILL_TRAIL) == 6,
          "act diagnostic reads shipped Master and route zone tables");
    puts("QA diagnostic: all mapped wardens including optional; weighted wild quantiles; no survival, purchase, catch or quest simulation");
    qa_act_pass(1);
    puts("QA zero-wild stress diagnostic (stricter than no extra grinding):");
    qa_act_pass(0);
    party_count = 0;
}
