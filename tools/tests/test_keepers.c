/*
 * Bout portraits (src/game/keeper.c): a warden's look is stable and follows
 * the scene, variations stay inside the archetype's pools, and a warden bout
 * plays the whole sequence (enter, flair, throw from the hand, walk back in
 * sheepish) while a wild bout only brings the player in. On the overworld
 * every warden wears the look they have in the bout.
 */
#include "harness.h"

static int in_pool(const u8 *pool, int n, int v)
{
    for (int i = 0; i < n; i++)
        if (pool[i] == v) return 1;
    return 0;
}

static int pal_ramp_index(const u16 (*ramp)[3], int count, u16 first)
{
    for (int i = 0; i < count; i++)
        if (ramp[i][0] == first) return i;
    return -1;
}

static int cloth_index(u16 c)
{
    for (int i = 0; i < KP_CLOTH_COUNT; i++)
        if (kp_cloth_ramp[i][0] == c) return i;
    return -1;
}

static void test_variations(void)
{
    u16 pal[16];
    int ok_default = 1, ok_pools = 1, distinct = 0;
    for (int k = 0; k < KEEPER_COUNT; k++) {
        const KeeperLook *l = &KEEPER_LOOK[k];
        keeper_palette(pal, k, 0);
        if (pal[4] != kp_skin_ramp[l->skin][0] || pal[7] != kp_hair_ramp[l->hair][0] ||
            pal[10] != kp_cloth_ramp[l->a][0] || pal[12] != kp_cloth_ramp[l->b][0])
            ok_default = 0;
        u16 first[16];
        keeper_palette(first, k, 1);
        for (int v = 1; v < 256; v++) {
            keeper_palette(pal, k, v);
            int hair = pal_ramp_index(kp_hair_ramp, KP_HAIR_COUNT, pal[7]);
            if (pal_ramp_index(kp_skin_ramp, KP_SKIN_COUNT, pal[4]) < 0 ||
                !in_pool(l->hair_pool, l->nhair, hair) ||
                !in_pool(l->a_pool, l->na, cloth_index(pal[10])) ||
                !in_pool(l->b_pool, l->nb, cloth_index(pal[12])))
                ok_pools = 0;
            if (pal[4] != first[4] || pal[7] != first[7] || pal[10] != first[10]) distinct = 1;
        }
    }
    CHECK(ok_default, "look 0 is every keeper's default look");
    CHECK(ok_pools, "every variation takes skin, hair and cloth from the keeper's pools");
    CHECK(distinct, "variations actually change the colours");
}

static void test_choice(void)
{
    TrainerTeam t = { "WARDEN LUCA", 1, { SP_NIBBIT }, { 4 }, 100, BSCENE_MEADOW, 0, 0 };
    battle.scene = BSCENE_MEADOW;
    keeper_choose(&t, 0);
    int k1 = keeper_kind, v1 = keeper_vary;
    keeper_choose(&t, 0);
    CHECK(keeper_kind == k1 && keeper_vary == v1 && v1 != 0, "a warden looks the same every time (varied by name)");
    int fits = 0;
    for (int i = 0; i < 6; i++) fits |= KEEPER_SCENE_POOL[BSCENE_MEADOW][i] == k1;
    CHECK(fits, "a meadow warden is one of the meadow's keepers");
    battle.scene = BSCENE_CAVE;
    keeper_choose(&t, 1);
    CHECK(keeper_kind == KP_MASTER, "a Hall Master bout brings a Hall Master");
    t.look = 1 + KP_SMITH;
    t.vary = 7;
    keeper_choose(&t, 1);
    CHECK(keeper_kind == KP_SMITH && keeper_vary == 7, "TrainerTeam.look / .vary pick the portrait by hand");
}

static void run_bout_frames(int n, int *saw_enemy, int *saw_ally, int *saw_flair, int *saw_throw)
{
    for (int f = 0; f < n && game_mode == MODE_BATTLE; f++) {
        step((f % 8) == 0 ? KEY_A : 0);
        if (portrait[SIDE_ENEMY].on) *saw_enemy = 1;
        if (portrait[SIDE_ALLY].on) *saw_ally = 1;
        if (portrait[SIDE_ENEMY].on && portrait[SIDE_ENEMY].frame == KF_FLAIR) *saw_flair = 1;
        if (portrait[SIDE_ALLY].on && portrait[SIDE_ALLY].frame == HB_THROW) *saw_throw = 1;
        if (battle.state == BST_ACTION) break;
    }
}

static void test_bouts(void)
{
    fresh_game();
    Monster m = monster_make(SP_PYREFOX, 40);
    give_monster(&m);
    flag_set(FLAG_STARTER);
    field_enter_map(MAP_MEADOW, 21, 38, DIR_UP);
    static TrainerTeam t = { "WARDEN PIP", 1, { SP_NIBBIT }, { 3 }, 100, BSCENE_MEADOW, "PIP: aw!", 0 };
    battle_start_trainer_team(&t);
    int se = 0, sa = 0, sf = 0, st = 0;
    run_bout_frames(1200, &se, &sa, &sf, &st);
    CHECK(se && sa, "a warden bout brings in the keeper and the player");
    CHECK(sf, "the keeper strikes its signature pose");
    CHECK(st, "the player throws the lantern");
    CHECK(battle.state == BST_ACTION && !portrait[SIDE_ENEMY].on && !portrait[SIDE_ALLY].on,
          "both step aside once the kin are out");
    /* win: the keeper walks back in, sheepish (the foe is left on 1 HP so
     * the first move wins, whatever move the A presses pick) */
    side_mon(SIDE_ENEMY)->hp = 1;
    int back = 0, lose = 0;
    for (int f = 0; f < 3000 && game_mode == MODE_BATTLE; f++) {
        step((f % 6) == 0 ? KEY_A : 0);
        if (portrait[SIDE_ENEMY].on) back = 1;
        if (portrait[SIDE_ENEMY].on && portrait[SIDE_ENEMY].frame == KF_LOSE) lose = 1;
    }
    CHECK(back && lose, "after the win the keeper walks back in, sheepish");
    CHECK(game_mode != MODE_BATTLE, "the bout ends");

    Monster w = monster_make(SP_NIBBIT, 3);
    battle_start_wild(w);
    se = sa = sf = st = 0;
    run_bout_frames(1200, &se, &sa, &sf, &st);
    CHECK(!se && sa && st, "a wild bout brings only the player, who throws the lantern");
}

static void test_overworld(void)
{
    int wardens = 0, match = 1, masters = 0, masters_ok = 1, services_ok = 1, cast = 0;
    for (int i = 0; i < NPC_COUNT; i++) {
        u8 k, v;
        int drawn = npc_keeper_look(i, &k, &v);
        cast += drawn;
        if (NPCS[i].trainer != NO_TRAINER) {
            wardens++;
            TrainerTeam t = team_from(&TRAINERS[NPCS[i].trainer], BSCENE_AREA);
            if (!drawn || t.look != k + 1 || t.vary != v) match = 0;
        }
        const char *n = NPCS[i].name;
        if (n && (keeper_name_is(n, "FARA") || keeper_name_is(n, "SIGRUN") || keeper_name_is(n, "MORWEN") ||
                  keeper_name_is(n, "MAREN") || keeper_name_is(n, "VESPER") || keeper_name_is(n, "BRONWEN"))) {
            masters++;
            if (!drawn || k != KP_MASTER) masters_ok = 0;
        }
        if ((NPCS[i].chr == CHR_HEALER || NPCS[i].chr == CHR_SHOPKEEPER) && drawn && NPCS[i].trainer == NO_TRAINER)
            services_ok = 0;
    }
    CHECK(wardens > 50 && match, "every warden walks the map in the look they have in the bout");
    CHECK(masters == 6 && masters_ok, "the six Hall Masters look like Hall Masters on the map");
    CHECK(services_ok, "tenders and clerks keep their own sprites");
    CHECK(cast > wardens, "ordinary folk are drawn from the cast too");
    u8 k, v;
    int tender = -1;
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].name && str_eq(NPCS[i].name, "TENDER MAREN")) tender = i;
    CHECK(tender >= 0 && !npc_keeper_look(tender, &k, &v), "TENDER MAREN is not mistaken for MASTER MAREN");

    /* a warden on the map: its frame and palette come from the cast */
    fresh_game();
    give_starter();
    int w = -1;
    for (int i = 0; i < NPC_COUNT && w < 0; i++)
        if (NPCS[i].trainer == TR_LUCA) w = i;
    field_enter_map(NPCS[w].map, NPCS[w].x, NPCS[w].y + 2, DIR_UP);
    settle();
    step(0);
    npc_keeper_look(w, &k, &v);
    u16 pal[16];
    keeper_palette(pal, k, v);
    int found = 0;
    for (int s = 0; s < 7; s++) {
        int same = 1;
        for (int c = 1; c < 16; c++) same &= obj_palette[(OBANK_NPC + s) * 16 + c] == pal[c];
        found |= same;
    }
    CHECK(found, "the field loads a warden's keeper palette");
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    test_variations();
    test_choice();
    test_bouts();
    test_overworld();
    if (failures == 0) {
        printf("all keeper checks passed\n");
        return 0;
    }
    printf("%d keeper check(s) FAILED\n", failures);
    return 1;
}
