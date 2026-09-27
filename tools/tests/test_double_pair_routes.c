/* Named route-warden encounter and persistent outcome checks. */
#include "harness.h"

typedef struct { int first, second; } RoutePair;
static const RoutePair route_pairs[] = {
    { TR_OAK, TR_ASH }, { TR_FEN_REED_A, TR_FEN_REED_B },
    { TR_CC_SPA_A, TR_CC_SPA_B }, { TR_MF_TWIN_A, TR_MF_TWIN_B },
    { TR_N_CLIMBER_1, TR_N_CLIMBER_2 }, { TR_PILGRIM_A, TR_PILGRIM_B },
};

static int route_npc(int trainer)
{
    for (int i = 0; i < NPC_COUNT; i++) if (NPCS[i].trainer == trainer) return i;
    return -1;
}

static void route_setup(int trainer, int allies)
{
    new_game();
    dialog_clear();
    game_mode = MODE_FIELD;
    for (int i = 0; i < allies; i++) {
        Monster m = monster_make(i ? SP_BUBBLIN : SP_FLARIX, 22);
        give_monster(&m);
    }
    int npc = route_npc(trainer);
    map_load(NPCS[npc].map);
    player.level = npc_state[npc].level;
}

static void test_named_pairs(void)
{
    for (unsigned p = 0; p < sizeof(route_pairs) / sizeof(route_pairs[0]); p++) {
        int a = route_npc(route_pairs[p].first), b = route_npc(route_pairs[p].second);
        CHECK(a >= 0 && b >= 0 && NPCS[a].map == NPCS[b].map,
              "named wardens share one map and retain distinct trainer IDs");
        for (int side = 0; side < 2; side++) {
            int npc = side ? b : a, other = side ? a : b;
            route_setup(NPCS[npc].trainer, 2);
            CHECK(warden_pair_partner(npc) == other, "either named warden finds its visible partner");
            script_warden(npc);
            CHECK(dialog_count == 2 && dialog_q[(dialog_head + 1) % DIALOG_QUEUE].kind == DQ_CALL,
                  "talk queues exactly one challenge");
            dialog_clear();
            warden_battle(npc);
            CHECK(game_mode == MODE_BATTLE && battle.pair &&
                  battle.team[0].species == TRAINERS[NPCS[npc].trainer].species[0] &&
                  battle.team2[0].species == TRAINERS[NPCS[other].trainer].species[0] &&
                  battle.prize == TRAINERS[NPCS[npc].trainer].prize &&
                  battle.prize2 == TRAINERS[NPCS[other].trainer].prize,
                  "both named teams and prizes enter one four-active bout");
            CHECK(battle.ally != battle.ally2 && side_mon(SIDE_ALLY_2) != side_mon(SIDE_ALLY),
                  "the shared bout has two independent healthy allies");
            warden_end(BR_LOSE);
            CHECK(!trainer_beaten(NPCS[npc].trainer) && !trainer_beaten(NPCS[other].trainer),
                  "loss leaves both trainer bits clear");
            battle_end_hook = 0;
        }
    }
}

static void test_sight_and_outcome(void)
{
    int a = route_npc(TR_PILGRIM_A), b = route_npc(TR_PILGRIM_B);
    route_setup(TR_PILGRIM_A, 2);
    player.x = npc_state[a].x - 1;
    player.y = npc_state[a].y;
    npc_state[a].facing = DIR_LEFT;
    check_spotting();
    CHECK(spot.active && spot.npc == a, "sight reserves one initiating warden");
    spot.active = 0;
    warden_battle(a);
    CHECK(battle.pair && warden_partner_battling == TR_PILGRIM_B,
          "sight encounter enters one shared bout, not sequential fights");
    warden_end(BR_LOSE);
    static u8 sram[32768];
    CHECK(save_write_to(sram), "paired loss writes save");
    new_game();
    CHECK(save_load_from(sram) == SAVE_VERSION &&
          !trainer_beaten(TR_PILGRIM_A) && !trainer_beaten(TR_PILGRIM_B),
          "both bits remain clear across reload after a loss");
    map_load(NPCS[b].map);
    player.level = npc_state[b].level;
    player.x = npc_state[b].x + 1;
    player.y = npc_state[b].y;
    npc_state[b].facing = DIR_RIGHT;
    check_spotting();
    CHECK(spot.active && spot.npc == b, "either partner can initiate by sight");
    spot.active = 0;
    warden_battle(b);
    CHECK(battle.pair && warden_partner_battling == TR_PILGRIM_A,
          "second warden's sight initiates the same shared bout");
    warden_end(BR_WIN);
    CHECK(trainer_beaten(TR_PILGRIM_A) && trainer_beaten(TR_PILGRIM_B) &&
          warden_battling == -1 && warden_partner_battling == -1,
          "one win marks both saved bits and clears pending pair state");
    CHECK(save_write_to(sram), "paired victory writes save");
    new_game();
    CHECK(save_load_from(sram) == SAVE_VERSION &&
          trainer_beaten(TR_PILGRIM_A) && trainer_beaten(TR_PILGRIM_B),
          "paired victory bits survive reload");
    map_load(NPCS[a].map);
    dialog_clear();
    script_warden(a);
    CHECK(dialog_count == 1 && dialog_q[dialog_head].kind != DQ_CALL,
          "won pair speaks completed dialogue without another challenge");
    dialog_clear();
    script_warden(b);
    CHECK(dialog_count == 1 && dialog_q[dialog_head].kind != DQ_CALL,
          "both partners speak completed dialogue");
    battle_end_hook = 0;
}

static void test_fallbacks(void)
{
    int a = route_npc(TR_OAK), b = route_npc(TR_ASH);
    route_setup(TR_OAK, 1);
    CHECK(warden_pair_partner(a) == -1, "one healthy ally rejects shared bout");
    warden_battle(a);
    CHECK(!battle.pair && warden_partner_battling == -1, "one ally starts solo bout");
    warden_end(BR_LOSE);
    route_setup(TR_OAK, 2);
    trainer_mark_beaten(TR_ASH);
    CHECK(warden_pair_partner(a) == -1, "previously defeated partner cannot join");
    warden_battle(a);
    CHECK(!battle.pair, "partially completed pair starts solo bout");
    warden_end(BR_WIN);
    CHECK(trainer_beaten(TR_OAK) && trainer_beaten(TR_ASH), "solo result does not reset partner bit");
    route_setup(TR_OAK, 2);
    npc_visible[b] = 0;
    CHECK(warden_pair_partner(a) == -1, "hidden partner cannot join");
    npc_visible[b] = 1;
    npc_state[b].level = player.level + 1;
    CHECK(warden_pair_partner(a) == -1, "partner on another elevation cannot join");
    battle_end_hook = 0;
}

int main(void)
{
    test_named_pairs();
    test_sight_and_outcome();
    test_fallbacks();
    printf("%d route pair failures\n", failures);
    return failures ? 1 : 0;
}
