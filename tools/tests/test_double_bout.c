/* Synthetic four-active battle-core checks. Route initiation and battle
 * presentation are tested separately when they are wired to this API. */
#include "harness.h"

static void test_order(void)
{
    BattleTurnChoice choices[4] = {
        { 0, 0, 70, 0 }, { 1, 1, 10, 0 },
        { 2, 0, 100, 0 }, { 3, 0, 70, 1 },
    };
    battle_order_choices(choices, 4);
    CHECK(choices[0].actor == 1 && choices[1].actor == 2 &&
          choices[2].actor == 3 && choices[3].actor == 0,
          "four distinct actors resolve by priority, speed and tie key");

    BattleTurnChoice even[4] = {
        { 0, 0, 50, 0 }, { 1, 0, 50, 0 },
        { 2, 0, 50, 0 }, { 3, 0, 50, 0 },
    };
    battle_order_choices(even, 4);
    CHECK(even[0].actor == 0 && even[1].actor == 1 &&
          even[2].actor == 2 && even[3].actor == 3,
          "exact ties retain deterministic input order");

    BattleTurnChoice singles[2] = { { 0, 0, 60, -1 }, { 1, 0, 60, 0 } };
    battle_order_choices(singles, 2);
    CHECK(singles[0].actor == 1, "single-bout losing tie acts second");
    singles[0] = (BattleTurnChoice){ 0, 0, 60, 1 };
    singles[1] = (BattleTurnChoice){ 1, 0, 60, 0 };
    battle_order_choices(singles, 2);
    CHECK(singles[0].actor == 0, "single-bout winning tie acts first");
}

static void test_targets(void)
{
    CHECK(battle_live_target(0, 3, 0xF) == 3 &&
          battle_live_target(2, 1, 0xF) == 1 &&
          battle_live_target(1, 2, 0xF) == 2 &&
          battle_live_target(3, 0, 0xF) == 0,
          "each actor can select either live opposing position");
    CHECK(battle_live_target(0, 1, 0xD) == 3 &&
          battle_live_target(1, 0, 0xE) == 2,
          "fainted chosen target redirects to the other opposing position");
    CHECK(battle_live_target(2, 0, 0x5) == -1 &&
          battle_live_target(3, 1, 0xA) == -1,
          "no living opponents skips safely rather than hitting an ally");
    CHECK(battle_live_target(4, 1, 0xF) == -1 &&
          battle_live_target(0, 2, 0xF) == 1,
          "invalid actor and teammate target cannot become hit targets");
}

static void pair_fixture(void)
{
    new_game();
    dialog_clear();
    game_mode = MODE_FIELD;
    for (int i = 0; i < 3; i++) {
        Monster m = monster_make(i == 0 ? SP_FLARIX : i == 1 ? SP_BUBBLIN : SP_THORNIP, 18);
        give_monster(&m);
    }
    battle_reset(BK_TRAINER);
    static const TrainerTeam first = { .name = "OAK", .count = 2,
        .species = { SP_GOLEMIT, SP_PUFFOWL }, .level = { 14, 14 }, .prize = 90 };
    static const TrainerTeam second = { .name = "ASH", .count = 2,
        .species = { SP_ZAPPET, SP_NIBBIT }, .level = { 14, 14 }, .prize = 110 };
    CHECK(battle_pair_setup(&first, &second), "two healthy allies allow independent paired teams");
    battle.state = BST_ACTION;
    battle.ev_count = 0;
}

static void test_pair_core(void)
{
    pair_fixture();
    CHECK(side_mon(0) == &party[0] && side_mon(2) == &party[1] &&
          side_mon(1) == &battle.team[0] && side_mon(3) == &battle.team2[0],
          "all four positions map to distinct active kin");
    int pp0 = side_mon(0)->pp[0], pp2 = side_mon(2)->pp[0];
    BattlePairAction invalid[2] = { { ACT_MOVE, 0, 1 }, { ACT_MOVE, MAX_MOVES, 3 } };
    CHECK(!battle_take_double_turn(invalid) && side_mon(0)->pp[0] == pp0 && battle.turn == 0,
          "invalid second choice does not consume first actor's turn or PP");
    BattlePairAction actions[2] = { { ACT_MOVE, 0, 3 }, { ACT_MOVE, 0, 1 } };
    CHECK(battle_take_double_turn(actions) && battle.turn == 1 &&
          side_mon(0)->pp[0] == pp0 - 1 && side_mon(2)->pp[0] == pp2 - 1,
          "both player kin consume their own PP on one shared turn");
    int actors = 0, valid = 1;
    for (int e = 0; e < battle.ev_count; e++) {
        BEvent *ev = &battle.ev[e];
        if (ev->type != EV_ANIM) continue;
        actors |= 1 << ev->side;
        if ((ev->side & 1) == (ev->target & 1) || ev->target > SIDE_ENEMY_2) valid = 0;
    }
    CHECK(actors == 15 && valid, "four actors each animate toward an opposing target");

    /* Drain the two independent opposing teams without playing the queued UI.
     * Both payouts are queued once only after the last kin on both teams. */
    battle.ev_count = 0;
    battle.team[0].hp = battle.team2[0].hp = 0;
    battle_pair_finish_turn();
    CHECK(battle.result == BR_NONE && battle.team_idx == 1 && battle.team_idx2 == 1,
          "both trainers independently replenish their fainted positions");
    battle.ev_count = 0;
    battle.team[1].hp = battle.team2[1].hp = 0;
    battle_pair_finish_turn();
    int prize_count = 0, amount = 0, xp_count = 0;
    for (int e = 0; e < battle.ev_count; e++) {
        if (battle.ev[e].type == EV_MONEY) { prize_count++; amount += battle.ev[e].a; }
        if (battle.ev[e].type == EV_XP) xp_count++;
    }
    CHECK(battle.result == BR_WIN && prize_count == 2 && amount == 200 && xp_count > 0,
          "winning both teams awards both prizes and kin XP in one bout");
    int event_count = battle.ev_count;
    battle_pair_finish_turn();
    CHECK(battle.result == BR_WIN && battle.ev_count == event_count,
          "completed bout does not repeat its result or rewards");
}

static void test_switch_status_and_loss(void)
{
    pair_fixture();
    battle.team[0].status = STATUS_SLP;
    battle.team[0].sleep_turns = 3;
    int sleeping_pp = side_mon(1)->pp[0];
    int other_pp = 0;
    for (int i = 0; i < MAX_MOVES; i++) other_pp += side_mon(3)->pp[i];
    BattlePairAction actions[2] = { { ACT_MOVE, 0, 1 }, { ACT_SWITCH, 2, 1 } };
    int accepted = battle_take_double_turn(actions);
    int remaining_pp = 0;
    for (int i = 0; i < MAX_MOVES; i++) remaining_pp += side_mon(3)->pp[i];
    CHECK(accepted && battle.ally2 == 2 &&
          side_mon(1)->pp[0] == sleeping_pp && remaining_pp == other_pp - 1,
          "switch spends one ally action; sleeping foe skips only its own action");
    int switched = 0, sent = 0;
    for (int e = 0; e < battle.ev_count; e++) {
        if (battle.ev[e].type == EV_WITHDRAW && battle.ev[e].side == SIDE_ALLY_2) switched++;
        if (battle.ev[e].type == EV_SEND_OUT && battle.ev[e].side == SIDE_ALLY_2 &&
            battle.ev[e].a == 2) sent++;
    }
    CHECK(switched == 1 && sent == 1, "secondary ally withdrawal and replacement retain actor identity");

    pair_fixture();
    for (int i = 0; i < party_count; i++) party[i].hp = 0;
    battle_pair_finish_turn();
    int prizes = 0;
    for (int e = 0; e < battle.ev_count; e++)
        if (battle.ev[e].type == EV_MONEY) prizes++;
    CHECK(battle.result == BR_LOSE && prizes == 0,
          "both allies dozing without reserves loses with neither warden prize");
}

static void test_live_retarget_and_replacement(void)
{
    pair_fixture();
    battle.team[0].hp = 0;
    BattlePairAction actions[2] = { { ACT_MOVE, 0, SIDE_ENEMY },
                                    { ACT_MOVE, 0, SIDE_ENEMY } };
    CHECK(battle_take_double_turn(actions), "one live opposing slot permits a shared four-position turn");
    int redirects = 0, reserved = 0;
    for (int e = 0; e < battle.ev_count; e++) {
        BEvent *ev = &battle.ev[e];
        if (ev->type == EV_ANIM && !(ev->side & 1) && ev->target == SIDE_ENEMY_2) redirects++;
        if (ev->type == EV_SEND_OUT && ev->side == SIDE_ENEMY && ev->a == 1) reserved++;
    }
    CHECK(redirects >= 2, "both ally moves retarget away from a dozing foe");
    CHECK(reserved == 1, "a fainted primary foe receives only its own replacement event");
}

static void test_auto_substitution(void)
{
    pair_fixture();
    party[1].hp = 0;
    battle_pair_finish_turn();
    int sent = 0;
    for (int e = 0; e < battle.ev_count; e++)
        if (battle.ev[e].type == EV_SEND_OUT && battle.ev[e].side == SIDE_ALLY_2 &&
            battle.ev[e].a == 2) sent++;
    CHECK(battle.ally2 == 2 && sent == 1 && battle.result == BR_NONE,
          "fainted second ally automatically draws an unoccupied reserve before next turn");
    pair_fixture();
    party[1].hp = party[2].hp = 0;
    battle_pair_finish_turn();
    CHECK(battle.result == BR_NONE && party[0].hp && !party[battle.ally2].hp,
          "without a reserve the first ally continues a two-versus-one bout");
}

static void test_item_actions(void)
{
    pair_fixture();
    party[0].hp = party[0].max_hp / 2;
    party[1].hp = party[1].max_hp / 2;
    bag[ITEM_TONIC] = 1;
    BattlePairAction actions[2] = {
        { ACT_ITEM, ITEM_TONIC, 1, 0 }, { ACT_ITEM, ITEM_TONIC, 3, 1 }
    };
    int hp0 = party[0].hp, hp1 = party[1].hp;
    CHECK(!battle_take_double_turn(actions) && battle.turn == 0 && bag[ITEM_TONIC] == 1 &&
          party[0].hp == hp0 && party[1].hp == hp1,
          "two ally items reject one shared bag charge atomically");
    bag[ITEM_TONIC] = 2;
    CHECK(battle_take_double_turn(actions) && bag[ITEM_TONIC] == 0,
          "both ally item charges resolve once on independent targets");
    int hp_events = 0, healed0 = 0, healed2 = 0;
    for (int e = 0; e < battle.ev_count; e++)
        if (battle.ev[e].type == EV_HP) {
            if (battle.ev[e].side == SIDE_ALLY) {
                hp_events++;
                if (battle.ev[e].a > hp0) healed0 = 1;
            }
            if (battle.ev[e].side == SIDE_ALLY_2) {
                hp_events++;
                if (battle.ev[e].a > hp1) healed2 = 1;
            }
        }
    CHECK(hp_events >= 2 && healed0 && healed2,
          "both ally item HP updates precede later enemy damage on correct actors");
}

static void test_pair_requirements(void)
{
    pair_fixture();
    battle.pair = 0;
    party[1].hp = party[2].hp = 0;
    static const TrainerTeam solo = { .name = "OAK", .count = 1,
        .species = { SP_GOLEMIT }, .level = { 14 } };
    CHECK(!battle_pair_setup(&solo, &solo) && !battle.pair,
          "one healthy ally refuses the pair instead of disguising a 1v2 bout");
}

int main(void)
{
    test_order();
    test_targets();
    test_pair_core();
    test_switch_status_and_loss();
    test_item_actions();
    test_auto_substitution();
    test_live_retarget_and_replacement();
    test_pair_requirements();
    printf("%d failures\n", failures);
    return failures ? 1 : 0;
}
