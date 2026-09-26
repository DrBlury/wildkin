/*
 * Energy and fusion (src/game/fusion.c, docs/EXPANSION.md 7.4): unbinding
 * yields and rules, the mixing table, the Loom's odds and outcomes, the
 * screens (open, drive, close), the Works desk, decor and the save.
 */
#include "harness.h"

static Monster mk(int sp, int lv, int lustrous)
{
    Monster m = monster_make(sp, lv);
    m.flags = lustrous ? MF_LUSTROUS : 0;
    return m;
}

static int first_of_rarity(int r)
{
    for (int sp = 0; sp < SP_COUNT; sp++)
        if (SPECIES[sp].rarity == r) return sp;
    return -1;
}

static int single_type_common(void)
{
    for (int sp = 0; sp < SP_COUNT; sp++)
        if (SPECIES[sp].rarity == R_COMMON && SPECIES[sp].type2 == TYPE_NONE) return sp;
    return -1;
}

static int dual_type_common(void)
{
    for (int sp = 0; sp < SP_COUNT; sp++)
        if (SPECIES[sp].rarity == R_COMMON && SPECIES[sp].type2 != TYPE_NONE &&
            SPECIES[sp].type2 != SPECIES[sp].type1)
            return sp;
    return -1;
}

static void run_frames(int n)
{
    for (int i = 0; i < n; i++) step(0);
}

static void test_unbind_rules(void)
{
    u8 ty[2];
    u16 am[2];
    int sp = single_type_common();
    Monster m = mk(sp, 20, 0);
    int n = fusion_unbind_yield(&m, ty, am);
    CHECK(n == 1 && ty[0] == SPECIES[sp].type1 && am[0] == 18, "a single-type kin gives 8 + level/2 of its type");
    m = mk(sp, 20, 1);
    fusion_unbind_yield(&m, ty, am);
    CHECK(am[0] == 36, "lustrous kin give twice as much");
    int dsp = dual_type_common();
    m = mk(dsp, 20, 0);
    n = fusion_unbind_yield(&m, ty, am);
    CHECK(n == 2 && ty[0] == SPECIES[dsp].type1 && ty[1] == SPECIES[dsp].type2 && am[0] == 11 && am[1] == 7,
          "dual types split 60/40");
    int rsp = first_of_rarity(R_RARE);
    if (rsp >= 0) {
        m = mk(rsp, 20, 0);
        fusion_unbind_yield(&m, ty, am);
        CHECK(am[0] + (SPECIES[rsp].type2 != TYPE_NONE ? am[1] : 0) == 27, "rare kin give x1.5");
    }
    int lsp = first_of_rarity(R_LEGEND);
    m = mk(lsp, 20, 0);
    n = fusion_unbind_yield(&m, ty, am);
    CHECK(am[0] + (n > 1 ? am[1] : 0) == 72, "legends give x4");
    m = mk(SP_STEAMOTH, 20, 0);
    n = fusion_unbind_yield(&m, ty, am);
    CHECK(n == 2 && ty[0] == T_BLAZE && ty[1] == T_TIDE && am[0] == 14 && am[1] == 13,
          "fusion kin give back their signature energies 50/50 (x1.5)");

    /* the home wild */
    int homed = 0, any = 0;
    for (int s = 0; s < SP_COUNT; s++) {
        if (SPECIES[s].rarity != R_COMMON) continue;
        any++;
        homed += fusion_home_wild(s) != 0;
    }
    CHECK(any > 0 && homed > 0, "common kin have a home wild to go back to");

    /* who may be unbound */
    fresh_game();
    Monster a = mk(sp, 10, 0);
    give_monster(&a);
    CHECK(fusion_unbind_blocked(0) != 0, "your only kin can't be unbound");
    Monster b = mk(dsp, 10, 0);
    give_monster(&b);
    party[1].hp = 0;
    CHECK(fusion_unbind_blocked(0) != 0, "nor the last one still awake");
    CHECK(fusion_unbind_blocked(1) == 0, "a dozing kin can be unbound if another is awake");
    party[1].hp = party[1].max_hp;
    Monster c = mk(SP_GOLEMIT, 12, 0);
    storage_add(&c);
    int before_stone = fusion.energy[T_STONE];
    Monster out;
    n = fusion_unbind(2, &out, ty, am);
    CHECK(n > 0 && out.species == SP_GOLEMIT && storage_count == 0 && fusion.energy[T_STONE] > before_stone,
          "unbinding a Shelf kin removes it and fills the flask");
    n = fusion_unbind(0, &out, ty, am);
    CHECK(n > 0 && party_count == 1 && party[0].species == dsp && fusion.unbound == 2 && (fusion.flags & FZF_UNBOUND),
          "unbinding a team kin closes the gap in the team");
    fusion.energy[T_BEAST] = 9990;
    CHECK(fusion_energy_add(T_BEAST, 50) == 9 && fusion.energy[T_BEAST] == FZ_ENERGY_MAX, "pools cap at 9999");
}

static void test_mixing(void)
{
    CHECK(MIX_COUNT == 26, "26 mixing recipes");
    int pairs_ok = 1, made[TYPE_COUNT] = { 0 };
    for (int r = 0; r < MIX_COUNT; r++) {
        const MixRecipe *m = &MIX_RECIPES[r];
        if (m->a == m->b || fusion_mix_find(m->a, m->b) != r || fusion_mix_find(m->b, m->a) != r) pairs_ok = 0;
        made[m->out] = 1;
    }
    CHECK(pairs_ok, "recipes are distinct unordered pairs");
    int all = 1;
    for (int t = 0; t < TYPE_COUNT; t++) all &= made[t];
    CHECK(all, "every type is the output of some recipe");
    /* closure from the seven starting types */
    u8 have[TYPE_COUNT] = { 0 };
    have[T_BEAST] = have[T_BLAZE] = have[T_TIDE] = have[T_BLOOM] = have[T_SPARK] = have[T_GALE] = have[T_STONE] = 1;
    for (int grew = 1; grew;) {
        grew = 0;
        for (int r = 0; r < MIX_COUNT; r++)
            if (have[MIX_RECIPES[r].a] && have[MIX_RECIPES[r].b] && !have[MIX_RECIPES[r].out]) {
                have[MIX_RECIPES[r].out] = 1;
                grew = 1;
            }
    }
    int reach = 1;
    for (int t = 0; t < TYPE_COUNT; t++) reach &= have[t];
    CHECK(reach, "mixing reaches all 18 types from the seven starting ones");

    fusion_reset();
    int steam = fusion_mix_find(T_BLAZE, T_TIDE);
    CHECK(MIX_RECIPES[steam].out == T_GALE, "BLAZE + TIDE make GALE (steam)");
    CHECK(fusion_mix(steam, 10, 100) == 0, "no mixing without the energy");
    fusion.energy[T_BLAZE] = 100;
    fusion.energy[T_TIDE] = 57;
    CHECK(fusion_mix_max(steam) == 50, "the most you can mix is a multiple of 10 of the smaller store");
    CHECK(fusion_mix(steam, 50, 120) == 60 && fusion.energy[T_BLAZE] == 50 && fusion.energy[T_TIDE] == 7 &&
          fusion.energy[T_GALE] == 60, "a perfect tune yields 120%");
    CHECK(fusion_mix(steam, 50, 10) == 0 && fusion_mix(steam, 5, 10) == 3, "yield never drops below 60%");
    CHECK(fusion.mixes == 1 + 1 && (fusion.flags & FZF_MIXED), "mixes are counted");

    /* the tuner's scoring */
    CHECK(tn_match(4, 7, 4, 7) == 100, "a matched wave scores 100");
    CHECK(tn_match(4, 0, 4, TN_PHASES / 2) < 20, "an inverted wave scores badly");
    CHECK(tn_yield(100) == 120 && tn_yield(0) == 60, "the tuner yield runs 60..120%");
}

static void test_loom(void)
{
    fresh_game();
    give_starter();
    /* signatures: unique pairs, both types valid */
    int sig_ok = 1, fusions = 0;
    for (int a = 0; a < SP_COUNT; a++) {
        const Species *s = &SPECIES[a];
        if (s->rarity != R_FUSION) continue;
        fusions++;
        if (s->fusion[0] >= TYPE_COUNT || s->fusion[1] >= TYPE_COUNT || s->fusion[0] == s->fusion[1]) sig_ok = 0;
        for (int b = a + 1; b < SP_COUNT; b++) {
            const Species *t = &SPECIES[b];
            if (t->rarity == R_FUSION &&
                ((t->fusion[0] == s->fusion[0] && t->fusion[1] == s->fusion[1]) ||
                 (t->fusion[0] == s->fusion[1] && t->fusion[1] == s->fusion[0])))
                sig_ok = 0;
        }
    }
    CHECK(fusions == 44 && sig_ok, "44 fusion kin, each with its own signature pair");

    u8 pick[3] = { T_BLAZE, T_TIDE, T_FROST };
    u8 cand[LOOM_CAND_MAX];
    int c = fusion_loom_candidates(pick, 3, cand);
    int has_steam = 0, has_ember = 0;
    for (int i = 0; i < c; i++) {
        has_steam |= cand[i] == SP_STEAMOTH;
        has_ember |= cand[i] == SP_EMBERIME;
    }
    CHECK(has_steam && has_ember, "three types list every fusion whose signature they cover");
    CHECK(fusion_loom_candidates(pick, 1, cand) == 0, "one type weaves nothing");

    fusion.energy[T_BLAZE] = 100;
    fusion.energy[T_TIDE] = 50;
    fusion.pity = 0;
    CHECK(fusion_loom_chance(pick, 2, STAKE_SMALL) == 6 + 4, "chance = 6 + harmony (8 * min / max)");
    CHECK(fusion_loom_chance(pick, 2, STAKE_LARGE) == 6 + 14 + 4, "a stake of 60 adds 14%");
    fusion.pity = 3;
    CHECK(fusion_loom_chance(pick, 2, STAKE_MEDIUM) == 6 + 6 + 4 + 9, "each miss adds 3%");
    fusion.pity = FZ_PITY_CAP;
    CHECK(fusion_loom_chance(pick, 2, STAKE_SMALL) == 100, "25 misses make the next weave certain");

    CHECK(fusion_loom_check(pick, 1, 0) == LOOM_TOO_FEW, "the Loom needs two types");
    u8 nothing[2] = { T_BEAST, T_BLAZE };
    fusion.energy[T_BEAST] = 100;
    int nc = fusion_loom_candidates(nothing, 2, cand);
    if (!nc) CHECK(fusion_loom_check(nothing, 2, 0) == LOOM_NO_CANDIDATE, "a pair without a fusion is refused");
    fusion.energy[T_TIDE] = 5;
    CHECK(fusion_loom_check(pick, 2, STAKE_SMALL) == LOOM_LOW_ENERGY, "the stake must be covered");

    /* a sure hit */
    fusion.energy[T_TIDE] = 100;
    fusion.pity = FZ_PITY_CAP;
    int team = party_count;
    WeaveResult r;
    CHECK(fusion_weave(pick, 2, STAKE_MEDIUM, &r) && r.hit && r.species == SP_STEAMOTH, "a certain weave weaves");
    CHECK(party_count == team + 1 && party[team].species == SP_STEAMOTH && party[team].level == 25 &&
          dex_caught[SP_STEAMOTH], "the woven kin joins the team at the stake's level");
    CHECK(fusion.pity == 0 && fusion.hits == 1 && fusion.weaves == 1 && fusion.energy[T_BLAZE] == 70 &&
          fusion.energy[T_TIDE] == 70, "a hit resets the misses and spends the stake");

    /* a miss: find a seed that misses at the base chance */
    fusion.energy[T_BLAZE] = fusion.energy[T_TIDE] = 100;
    int missed = 0;
    for (u32 seed = 1; seed < 200 && !missed; seed++) {
        FusionState keep = fusion;
        int dust = bag[ITEM_MOTE_DUST];
        rng_seed(seed);
        fusion_weave(pick, 2, STAKE_LARGE, &r);
        if (r.hit) {
            fusion = keep;
            continue;
        }
        missed = 1;
        CHECK(r.dust == 3 && bag[ITEM_MOTE_DUST] == dust + 3, "a miss leaves MOTE DUST (3 at stake 60)");
        CHECK(r.refund == 18 && fusion.energy[T_BLAZE] == 100 - 60 + 18, "and gives 30% of the stake back");
        CHECK(fusion.pity == 1, "and counts toward the pity");
    }
    CHECK(missed, "weaves can miss");

    /* the candidate pick leans toward kin you never had */
    int news = 0;
    u8 two[2] = { SP_STEAMOTH, SP_EMBERIME };   /* STEAMOTH owned now */
    rng_seed(99);
    for (int i = 0; i < 400; i++) news += fusion_loom_pick(two, 2) == SP_EMBERIME;
    CHECK(news > 240 && news < 360, "a never-owned candidate is three times as likely");
}

static void test_screens(void)
{
    fresh_game();
    give_starter();
    Monster b = mk(SP_GOLEMIT, 14, 0);
    give_monster(&b);
    Monster s = mk(SP_NIBBIT, 9, 0);
    storage_add(&s);
    fusion.energy[T_BLAZE] = 200;
    fusion.energy[T_TIDE] = 200;
    fusion.flags |= FZF_INTRO;

    fusion_open(FUSION_SCREEN_MENU);
    run_frames(3);
    CHECK(game_mode == MODE_EXT && fz.screen == FZS_WORKS, "the Works menu opens");
    tap(KEY_RIGHT);
    tap(KEY_A);
    run_frames(3);
    CHECK(fz.screen == FZS_LOOM, "the Loom opens from the hall");
    tap(KEY_RIGHT);
    tap(KEY_A);                       /* BLAZE */
    tap(KEY_RIGHT);
    tap(KEY_A);                       /* TIDE */
    CHECK(fz.lm_n == 2, "types are picked on the strip");
    fusion.pity = FZ_PITY_CAP;
    tap(KEY_START);
    CHECK(fz.lm_state == LM_SPIN, "START weaves");
    run_frames(LM_SPIN_LEN + 5);
    run_dialog(600);
    run_frames(3);
    CHECK(fz.lm_state == LM_PICK && fusion.hits == 1 && lore_is_known(LORE_WOVEN_KIN) &&
          lore_is_known(LORE_LOOM_ODDS), "the weave plays out and tells the story");
    tap(KEY_B);
    tap(KEY_B);
    tap(KEY_B);
    run_frames(3);
    CHECK(fz.screen == FZS_WORKS, "B steps back to the hall");

    /* unbind the Shelf kin */
    fz.works_cursor = 0;
    tap(KEY_A);
    run_frames(3);
    CHECK(fz.screen == FZS_UNBIND, "the extractor opens");
    int n = party_count + storage_count;
    for (int i = 0; i < n - 1; i++) tap(KEY_RIGHT);
    tap(KEY_A);
    run_frames(60);
    tap(KEY_A);                        /* past the question, YES */
    for (int f = 0; f < 200 && fz.ub_state != UB_ANIM; f++) step((f & 7) == 0 ? KEY_A : 0);
    CHECK(fz.ub_state == UB_ANIM, "confirming starts the unbinding");
    run_frames(UB_ANIM_LEN + 2);
    run_dialog(600);
    CHECK(storage_count == 0 && fusion.unbound == 1 && lore_is_known(LORE_UNBINDING), "the Shelf kin was unbound");
    tap(KEY_B);
    run_frames(3);

    /* mix with the tuner */
    fz.works_cursor = 2;
    tap(KEY_A);
    run_frames(3);
    CHECK(fz.screen == FZS_MIX, "the mixer opens");
    fz.mx_cursor = fusion_mix_find(T_BLAZE, T_TIDE);
    tap(KEY_A);
    run_frames(2);
    CHECK(fz.mx_state == MX_AMOUNT, "A picks an amount");
    tap(KEY_A);
    run_frames(2);
    CHECK(fz.screen == FZS_TUNE, "then tunes");
    int gale = fusion.energy[T_GALE];
    run_frames(TN_TIME + 5);
    run_dialog(600);
    run_frames(3);
    CHECK(fz.screen == FZS_MIX && fusion.energy[T_GALE] > gale && lore_is_known(LORE_MIX_TABLE),
          "time runs out, the mix is made");
    tap(KEY_B);
    run_frames(3);
    fz.works_cursor = 3;
    tap(KEY_A);
    run_frames(3);
    CHECK(fz.screen == FZS_ENERGY, "the energy tanks open");
    tap(KEY_B);
    run_frames(3);
    tap(KEY_B);
    run_frames(3);
    CHECK(game_mode == MODE_FIELD, "B leaves the Works");

    /* the flask key item */
    fusion_key_use(KEY_ENERGY_FLASK);
    run_frames(3);
    CHECK(game_mode == MODE_EXT && fz.screen == FZS_ENERGY, "the ENERGY FLASK shows the energy");
    tap(KEY_B);
    run_frames(3);
    CHECK(game_mode == MODE_FIELD, "and closes back to the field");

    /* the standalone tuner (crafting) */
    fusion_tuner_open("TEST", 0);
    run_frames(3);
    tap(KEY_A);
    run_frames(3);
    CHECK(game_mode == MODE_FIELD, "the tuner on its own returns to the field");
}

static void test_desk_and_map(void)
{
    fresh_game();
    give_starter();
    int nell = -1;
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].script == SCR_FUSION_DESK) nell = i;
    CHECK(nell >= 0 && NPCS[nell].map == MAP_RESONANCE_WORKS, "ENGINEER NELL stands in the RESONANCE WORKS");
    scr_fusion_desk(nell);
    for (int f = 0; f < 900 && dialog_active(); f++) {
        if (choice.active) {
            tap(KEY_B);   /* BYE */
            continue;
        }
        step((f & 3) == 0 ? KEY_A : 0);
    }
    CHECK(bag[ITEM_ENERGY_FLASK] == 1 && (fusion.flags & FZF_INTRO), "the desk explains once and gives the ENERGY FLASK");
    int machines = 0;
    const MapDef *m = &MAPS[MAP_RESONANCE_WORKS];
    for (int i = 0; i < m->decor_count; i++) {
        int k = m->decor[i].kind;
        machines += k == DK_FZ_EXTRACTOR || k == DK_FZ_MIXER || k == DK_FZ_LOOM || k == DK_FZ_TANKS;
    }
    CHECK(machines == 4, "the four machines stand in the Works");
    CHECK(fusion_examine(DK_FZ_LOOM) && game_mode == MODE_EXT && fz.screen == FZS_LOOM, "examining the Loom opens it");
    fz_exit();
    CHECK(!fusion_examine(DK_PLANT), "other decor is left alone");

    /* lore talk fits the message box rules */
    int lore_ok = 1;
    for (int i = LORE_RESONANCE_WORKS; i <= LORE_WOVEN_KIN; i++) {
        if (LORE[i].chapter != LCH_ENERGY && LORE[i].chapter != LCH_PLACES) lore_ok = 0;
        if (str_len(LORE[i].title) > 18) lore_ok = 0;
        if (LORE[i].talk && str_len(LORE[i].talk) >= 400) lore_ok = 0;
    }
    CHECK(lore_ok, "fusion lore entries are well formed");
}

static void test_save(void)
{
    fresh_game();
    give_starter();
    fusion.energy[T_ASTRAL] = 1234;
    fusion.pity = 7;
    fusion.weaves = 9;
    fusion.hits = 2;
    fusion.flags = FZF_INTRO | FZF_WOVEN;
    static u8 sram[32768];
    memset(sram, 0xFF, sizeof(sram));
    CHECK(save_write_to(sram), "the save writes");
    fusion_reset();
    CHECK(save_load_from(sram) && fusion.energy[T_ASTRAL] == 1234 && fusion.pity == 7 && fusion.weaves == 9 &&
          fusion.hits == 2 && fusion.flags == (FZF_INTRO | FZF_WOVEN), "fusion state round-trips through the save");
    fusion.energy[0] = 60000;
    fusion.pity = 99;
    fusion.hits = 50;
    fusion_validate();
    CHECK(fusion.energy[0] == FZ_ENERGY_MAX && fusion.pity == FZ_PITY_CAP && fusion.hits <= fusion.weaves,
          "validate clamps bad data");
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    rng_seed(12345);
    test_unbind_rules();
    test_mixing();
    test_loom();
    test_screens();
    test_desk_and_map();
    test_save();
    if (failures) printf("%d check(s) FAILED\n", failures);
    return failures ? 1 : 0;
}
