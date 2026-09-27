/* Per-recipient XP scaling and parity between real bouts and the route model. */
#include "harness.h"
#include "../playthrough/act_balance.h"

static void test_scale(void)
{
    CHECK(monster_scaled_xp(120, 20, 15) == 120 &&
          monster_scaled_xp(120, 20, 20) == 120,
          "lower-level recipients receive no bonus; equal levels keep full XP");
    CHECK(monster_scaled_xp(120, 20, 21) == 90 &&
          monster_scaled_xp(120, 20, 23) == 60 &&
          monster_scaled_xp(120, 20, 29) == 30,
          "XP falls monotonically as the recipient outlevels the foe");
    CHECK(monster_scaled_xp(1, 1, MAX_LEVEL) == 1 &&
          monster_scaled_xp(120, 20, MAX_LEVEL) >= 1,
          "lower-level opponents still give at least one XP");
}

static void test_award_and_sim(void)
{
    fresh_game();
    Monster active = monster_make(SP_FLARIX, 20);
    Monster bench = monster_make(SP_AQUAPO, 15);
    Monster asleep = monster_make(SP_ZAPPET, 20);
    active.trait = bench.trait = asleep.trait = TR_SURGE;
    active.bond = bench.bond = asleep.bond = 0;
    give_monster(&active);
    give_monster(&bench);
    give_monster(&asleep);
    party[2].hp = 0;
    battle_start_wild(monster_make(SP_NIBBIT, 15));
    battle.ev_count = 0;
    int base = monster_xp_yield(side_mon(SIDE_ENEMY), 0);
    award_xp(side_mon(SIDE_ENEMY));
    int actual[3] = {-1, -1, -1};
    for (int i = 0; i < battle.ev_count; i++)
        if (battle.ev[i].type == EV_XP) actual[battle.ev[i].a] = battle.ev[i].b;
    CHECK(actual[0] == monster_scaled_xp(base, 15, 20) &&
          actual[1] == base / 2 && actual[2] == -1,
          "active and bench scale independently; a dozing kin gets no XP");

    fresh_game();
    active = monster_make(SP_FLARIX, 20);
    bench = monster_make(SP_AQUAPO, 15);
    active.trait = bench.trait = TR_SURGE;
    active.bond = bench.bond = 0;
    give_monster(&active);
    give_monster(&bench);
    qa_lead_slot = 0;
    u32 before_active = party[0].xp, before_bench = party[1].xp;
    qa_gain(SP_NIBBIT, 15, 0);
    CHECK(party[0].xp - before_active == (u32)actual[0] &&
          party[1].xp - before_bench == (u32)actual[1],
          "act simulator uses the same per-recipient XP as a real battle");

    /* Scaling follows the existing active/bench, trait, bond and meal share. */
    party[0].trait = TR_QUICK_STUDY;
    party[0].bond = 220;
    battle.participants = 1;
    CHECK(xp_share(0, 100) == 132 &&
          monster_scaled_xp(xp_share(0, 100), 15, 20) == 49,
          "QUICK STUDY and bond apply before opponent-level scaling");
}

int main(void)
{
    test_scale();
    test_award_and_sim();
    printf("%d check(s) FAILED\n", failures);
    return failures ? 1 : 0;
}
