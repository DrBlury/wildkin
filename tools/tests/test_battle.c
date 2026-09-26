/*
 * Bout checks for the expansion: the new moves match docs/EXPANSION.md 5
 * and resolve with the right effects, the 18x18 type chart equals the doc,
 * every animation kind finishes and draws, every battle scene loads, and
 * opt.battle_speed plays bouts faster without skipping a beat.
 */
#include "harness.h"

#include <stdlib.h>

/* ---------------- helpers ---------------- */

static int find_move(const char *name)
{
    for (int m = 0; m < MOVE_COUNT; m++)
        if (strcmp(MOVES[m].name, name) == 0) return m;
    return -1;
}

static int find_type(const char *name)
{
    for (int t = 0; t < TYPE_COUNT; t++)
        if (strcmp(TYPE_NAMES[t], name) == 0) return t;
    return -1;
}

static char *read_file(const char *path)
{
    FILE *f = fopen(path, "rb");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    char *buf = malloc((size_t)n + 1);
    if (fread(buf, 1, (size_t)n, f) != (size_t)n) n = 0;
    buf[n] = 0;
    fclose(f);
    return buf;
}

/* Trim spaces in place. */
static char *trim(char *s)
{
    while (*s == ' ') s++;
    char *e = s + strlen(s);
    while (e > s && (e[-1] == ' ' || e[-1] == '\r')) *--e = 0;
    return s;
}

/* A fresh bout: ally (Lv la) against a wild foe (Lv lb), no intro, both
 * with a trait that never changes a bout (QUICK STUDY). */
static void bout(int a, int la, int b, int lb)
{
    new_game();
    dialog_clear();
    game_mode = MODE_FIELD;
    Monster m = monster_make(a, la);
    give_monster(&m);
    battle_start_wild(monster_make(b, lb));
    battle.state = BST_ACTION;
    battle.turn = 0;
    party[0].trait = TR_QUICK_STUDY;
    battle.team[0].trait = TR_QUICK_STUDY;
}

/* Reset both kin for another use of a move. */
static void rearm(void)
{
    Monster *a = &party[battle.ally], *d = &battle.team[battle.team_idx];
    a->hp = a->max_hp;
    d->hp = d->max_hp;
    a->status = d->status = STATUS_NONE;
    for (int s = 0; s < 2; s++) {
        battle.flinch[s] = 0;
        for (int i = 0; i < STAT_COUNT; i++) battle.stages[s][i] = 0;
    }
    battle.ev_count = 0;
}

/* Use `move` from the ally `n` times; count how often `pred` held after. */
typedef int (*Pred)(void);
static int trials(int move, int n, Pred pred)
{
    int hits = 0;
    for (int i = 0; i < n; i++) {
        rearm();
        use_move(SIDE_ALLY, move);
        hits += pred();
    }
    return hits;
}

static int p_foe_spe_down(void) { return battle.stages[SIDE_ENEMY][STAT_SPE] < 0; }
static int p_foe_def_down(void) { return battle.stages[SIDE_ENEMY][STAT_DEF] < 0; }
static int p_foe_spd_down(void) { return battle.stages[SIDE_ENEMY][STAT_SPD] < 0; }
static int p_foe_acc_down(void) { return battle.stages[SIDE_ENEMY][STAT_ACC] < 0; }
static int p_foe_asleep(void) { return battle.team[battle.team_idx].status == STATUS_SLP; }
static int p_foe_burned(void) { return battle.team[battle.team_idx].status == STATUS_BRN; }
static int p_foe_numb(void) { return battle.team[battle.team_idx].status == STATUS_NUMB; }
static int p_foe_flinch(void) { return battle.flinch[SIDE_ENEMY]; }

static int in_pct(int hits, int n, int lo, int hi)
{
    int pct = hits * 100 / n;
    return pct >= lo && pct <= hi;
}

/* ---------------- the move table against the doc ---------------- */

static void test_move_table(void)
{
    char *doc = read_file("docs/EXPANSION.md");
    CHECK(doc != NULL, "docs/EXPANSION.md can be read");
    if (!doc) return;
    char *sec = strstr(doc, "## 5. Moves");
    char *end = sec ? strstr(sec, "## 6.") : NULL;
    int rows = 0, ok = 1;
    for (char *line = sec; line && line < end; ) {
        char *nl = strchr(line, '\n');
        if (!nl) break;
        *nl = 0;
        if (line[0] == '|' && strncmp(line, "| move", 6) != 0 && strncmp(line, "| ---", 5) != 0) {
            char *col[8];
            int nc = 0;
            for (char *p = line + 1; nc < 8 && *p; ) {
                char *bar = strchr(p, '|');
                if (!bar) break;
                *bar = 0;
                col[nc++] = trim(p);
                p = bar + 1;
            }
            if (nc >= 7) {
                rows++;
                int m = find_move(col[0]);
                int type = find_type(col[1]);
                int cat = strcmp(col[2], "phys") == 0 ? CAT_PHYS : strcmp(col[2], "spec") == 0 ? CAT_SPEC : CAT_STATUS;
                int pow = col[3][0] == '-' ? 0 : atoi(col[3]);
                int acc = col[4][0] == '-' ? 0 : atoi(col[4]);
                int uses = atoi(col[5]);
                if (m < 0) {
                    ok = 0;
                    printf("     %s is not in the move table\n", col[0]);
                } else if (MOVES[m].type != type || MOVES[m].cat != cat || MOVES[m].power != pow ||
                           MOVES[m].acc != acc || MOVES[m].pp != uses || m < M_BONE_RATTLE) {
                    ok = 0;
                    printf("     %s differs from the doc\n", col[0]);
                }
            }
        }
        line = nl + 1;
    }
    CHECK(rows == MOVE_COUNT - M_BONE_RATTLE, "the doc lists exactly the new moves");
    CHECK(ok, "every new move's type, class, power, accuracy and uses match the doc");

    /* the 18x18 chart equals the doc's block */
    char *chart = strstr(doc, "          Be Bl Ti");
    int chart_ok = chart != NULL;
    if (chart) {
        char *line = strchr(chart, '\n') + 1;
        for (int atk = 0; atk < TYPE_COUNT && chart_ok; atk++) {
            char name[16];
            int k = 0;
            while (line[k] != ' ' && k < 15) name[k] = line[k], k++;
            name[k] = 0;
            if (find_type(name) != atk) {
                chart_ok = 0;
                printf("     chart row %d is %s\n", atk, name);
                break;
            }
            for (int def = 0; def < TYPE_COUNT; def++) {
                char c = line[10 + def * 3];
                char want = TYPE_CHART[atk][def];
                if (c != want) {
                    chart_ok = 0;
                    printf("     %s vs %s: doc '%c', game '%c'\n", TYPE_NAMES[atk], TYPE_NAMES[def], c, want);
                }
            }
            line = strchr(line, '\n') + 1;
        }
    }
    CHECK(chart_ok, "the 18x18 type chart equals the block in docs/EXPANSION.md");

    /* every new move has its own look: kind + particles unique among them */
    int unique = 1;
    for (int a = M_BONE_RATTLE; a < MOVE_COUNT; a++)
        for (int b = a + 1; b < MOVE_COUNT; b++)
            if (MOVES[a].anim == MOVES[b].anim && MOVES[a].fx == MOVES[b].fx && MOVES[a].fx2 == MOVES[b].fx2) {
                unique = 0;
                printf("     %s and %s look the same\n", MOVES[a].name, MOVES[b].name);
            }
    CHECK(unique, "every new move has its own animation recipe");
    free(doc);
}

/* ---------------- effects ---------------- */

static void test_effects(void)
{
    /* a sturdy neutral foe (BEAST takes every new type normally) */
    bout(SP_FLARIX, 40, SP_PRICKLET, 70);
    rng_seed(4242);

    rearm();
    use_move(SIDE_ALLY, M_SHROUD);
    CHECK(battle.stages[SIDE_ALLY][STAT_DEF] == 1 && battle.stages[SIDE_ALLY][STAT_SPD] == 1,
          "SHROUD raises DEFENSE and WILL");
    rearm();
    use_move(SIDE_ALLY, M_STEEL_SHELL);
    CHECK(battle.stages[SIDE_ALLY][STAT_DEF] == 2, "STEEL SHELL sharply raises DEFENSE");
    rearm();
    use_move(SIDE_ALLY, M_NEBULA_VEIL);
    CHECK(battle.stages[SIDE_ALLY][STAT_SPA] == 1 && battle.stages[SIDE_ALLY][STAT_SPD] == 1,
          "NEBULA VEIL raises FOCUS and WILL");
    rearm();
    use_move(SIDE_ALLY, M_WYRM_DANCE);
    CHECK(battle.stages[SIDE_ALLY][STAT_ATK] == 1 && battle.stages[SIDE_ALLY][STAT_SPE] == 1,
          "WYRM DANCE raises ATTACK and SPEED");
    rearm();
    use_move(SIDE_ALLY, M_THORN_WALL);
    CHECK(battle.stages[SIDE_ALLY][STAT_DEF] == 1 && battle.stages[SIDE_ALLY][STAT_SPD] == 1,
          "THORN WALL raises DEFENSE and WILL");

    /* foe stat moves (retry past a rare miss) */
    int ok = 0;
    for (int i = 0; i < 10 && !ok; i++) {
        rearm();
        use_move(SIDE_ALLY, M_MAGNET_PULL);
        ok = battle.stages[SIDE_ENEMY][STAT_SPE] == -2;
    }
    CHECK(ok, "MAGNET PULL sharply lowers the foe's SPEED");
    ok = 0;
    for (int i = 0; i < 10 && !ok; i++) {
        rearm();
        use_move(SIDE_ALLY, M_SNOWDRIFT);
        ok = battle.stages[SIDE_ENEMY][STAT_SPE] == -1 && battle.stages[SIDE_ENEMY][STAT_ACC] == -1;
    }
    CHECK(ok, "SNOWDRIFT lowers the foe's SPEED and ACCURACY");
    ok = 0;
    for (int i = 0; i < 10 && !ok; i++) {
        rearm();
        use_move(SIDE_ALLY, M_TARNISH);
        ok = battle.stages[SIDE_ENEMY][STAT_ATK] == -1;
    }
    CHECK(ok, "TARNISH lowers the foe's ATTACK");
    ok = 0;
    for (int i = 0; i < 10 && !ok; i++) {
        rearm();
        use_move(SIDE_ALLY, M_STARDUST);
        ok = battle.stages[SIDE_ENEMY][STAT_ACC] == -1;
    }
    CHECK(ok, "STARDUST lowers the foe's ACCURACY");
    ok = 0;
    for (int i = 0; i < 20 && !ok; i++) {
        rearm();
        use_move(SIDE_ALLY, M_LULLABY);
        ok = p_foe_asleep();
    }
    CHECK(ok, "LULLABY puts the foe to sleep");
    ok = 0;
    for (int i = 0; i < 10 && !ok; i++) {
        rearm();
        use_move(SIDE_ALLY, M_SNARL);
        ok = battle.stages[SIDE_ENEMY][STAT_SPA] == -1;
    }
    CHECK(ok, "SNARL lowers the foe's FOCUS");

    /* self drops after the hit */
    rearm();
    use_move(SIDE_ALLY, M_HEIRLOOM);
    CHECK(battle.stages[SIDE_ALLY][STAT_DEF] == -1 && battle.stages[SIDE_ALLY][STAT_SPD] == -1,
          "HEIRLOOM lowers the user's DEFENSE and WILL");
    ok = 0;
    for (int i = 0; i < 10 && !ok; i++) {
        rearm();
        use_move(SIDE_ALLY, M_SUPERNOVA);
        ok = battle.stages[SIDE_ALLY][STAT_SPA] == -2;
    }
    CHECK(ok, "SUPERNOVA harshly lowers the user's FOCUS");

    /* healing, draining, recoil */
    rearm();
    party[0].hp = party[0].max_hp / 4;
    int before = party[0].hp;
    use_move(SIDE_ALLY, M_LAST_RITES);
    CHECK(party[0].hp == before + party[0].max_hp / 2, "LAST RITES restores half the user's HP");
    int drained = 1;
    for (int k = 0; k < 2; k++) {
        int mv = k ? M_MOONBEAM : M_MARROW_SIP;
        rearm();
        party[0].hp = party[0].max_hp / 4;
        before = party[0].hp;
        use_move(SIDE_ALLY, mv);
        int dealt = battle.team[0].max_hp - battle.team[0].hp;
        if (dealt > 0 && party[0].hp != before + (dealt / 2 > 0 ? dealt / 2 : 1)) drained = 0;
    }
    CHECK(drained, "MARROW SIP and MOONBEAM heal by half the damage dealt");
    rearm();
    use_move(SIDE_ALLY, M_COMET_DASH);
    int dealt = battle.team[0].max_hp - battle.team[0].hp;
    CHECK(dealt > 0 && party[0].max_hp - party[0].hp == (dealt / 3 > 0 ? dealt / 3 : 1),
          "COMET DASH hurts the user by a third of the damage");

    /* multi-hit */
    int lo = 9, hi = 0;
    for (int k = 0; k < 2; k++)
        for (int i = 0; i < 40; i++) {
            rearm();
            use_move(SIDE_ALLY, k ? M_RIVET_SHOT : M_TRINKET_TOSS);
            int n = 0;
            for (int e = 0; e < battle.ev_count; e++)
                if (battle.ev[e].type == EV_HIT && battle.ev[e].side == SIDE_ENEMY) n++;
            if (n == 0) continue;   /* missed */
            if (n < lo) lo = n;
            if (n > hi) hi = n;
        }
    CHECK(lo == 2 && hi >= 4 && hi <= 5, "TRINKET TOSS and RIVET SHOT hit 2 to 5 times");

    /* CURSED CURIO doubles on a troubled foe */
    Monster *d = &battle.team[0];
    d->status = STATUS_NONE;
    int plain = calc_damage(&party[0], battle.stages[0], d, battle.stages[1], M_CURSED_CURIO, 0, 100).damage;
    d->status = STATUS_BRN;
    int punished = calc_damage(&party[0], battle.stages[0], d, battle.stages[1], M_CURSED_CURIO, 0, 100).damage;
    d->status = STATUS_NONE;
    CHECK(punished >= plain * 2 - 2 && punished <= plain * 2 + 2, "CURSED CURIO is twice as strong on a troubled foe");

    /* perfect-strike moves are marked */
    CHECK(MOVES[M_GILDED_GLEAM].effect == EF_HIGHCRIT && MOVES[M_GEAR_GRIND].effect == EF_HIGHCRIT &&
          MOVES[M_CROSSWIND].effect == EF_HIGHCRIT && MOVES[M_SHADE_CUT].effect == EF_HIGHCRIT,
          "GILDED GLEAM, GEAR GRIND, CROSSWIND and SHADE CUT often strike perfectly");

    /* chance effects land about as often as the doc says */
    int n = 400;
    CHECK(in_pct(trials(M_GRAVE_CHILL, n, p_foe_spe_down), n, 12, 30), "GRAVE CHILL lowers SPEED about 20% of the time");
    CHECK(in_pct(trials(M_OSSIFY, n, p_foe_def_down), n, 20, 40), "OSSIFY lowers DEFENSE about 30% of the time");
    CHECK(in_pct(trials(M_DEATH_KNELL, n, p_foe_asleep), n, 10, 28), "DEATH KNELL puts the foe to sleep about 20% of the time");
    CHECK(in_pct(trials(M_BONE_RATTLE, n, p_foe_flinch), n, 4, 17), "BONE RATTLE makes the foe flinch about 10% of the time");
    CHECK(in_pct(trials(M_CHEST_CHOMP, n, p_foe_flinch), n, 11, 28), "CHEST CHOMP makes the foe flinch about 20% of the time");
    CHECK(in_pct(trials(M_METEOR_FALL, n, p_foe_flinch), n, 10, 28), "METEOR FALL makes the foe flinch about 20% of the time");
    CHECK(in_pct(trials(M_POLTERGUST, n, p_foe_numb), n, 4, 17), "POLTERGUST numbs about 10% of the time");
    CHECK(in_pct(trials(M_ARC_FLASH, n, p_foe_numb), n, 12, 30), "ARC FLASH numbs about 20% of the time");
    CHECK(in_pct(trials(M_FORGE_FLASH, n, p_foe_burned), n, 4, 17), "FORGE FLASH burns about 10% of the time");
    CHECK(in_pct(trials(M_EMBER_STORM, n, p_foe_burned), n, 11, 30), "EMBER STORM burns about 20% of the time");
    CHECK(in_pct(trials(M_LODE_BEAM, n, p_foe_spd_down), n, 4, 17), "LODE BEAM lowers WILL about 10% of the time");
    CHECK(in_pct(trials(M_ACID_SPIT, n, p_foe_spd_down), n, 20, 40), "ACID SPIT lowers WILL about 30% of the time");
    CHECK(in_pct(trials(M_MUON_RAIN, n, p_foe_def_down), n, 4, 17), "MUON RAIN lowers DEFENSE about 10% of the time");
    CHECK(in_pct(trials(M_SANDBLAST, n, p_foe_acc_down), n, 11, 30), "SANDBLAST lowers ACCURACY about 20% of the time");

    /* priority: IRON TAP and COUNTERJAB go before a faster foe */
    int first = 1;
    for (int k = 0; k < 2; k++) {
        bout(SP_GOLEMIT, 30, SP_PUFFOWL, 30);
        party[0].moves[0] = k ? M_COUNTERJAB : M_IRON_TAP;
        party[0].pp[0] = 10;
        battle.ev_count = 0;
        battle_player_move(0);
        int ally = -1, foe = -1;
        for (int e = 0; e < battle.ev_count; e++) {
            if (battle.ev[e].type != EV_ANIM) continue;
            if (battle.ev[e].side == SIDE_ALLY && ally < 0) ally = e;
            if (battle.ev[e].side == SIDE_ENEMY && foe < 0) foe = e;
        }
        if (ally < 0 || (foe >= 0 && foe < ally)) first = 0;
    }
    CHECK(first, "IRON TAP and COUNTERJAB strike first");

    /* poison can't touch the dead or iron */
    int immune = 1;
    for (int s = 0; s < SP_COUNT; s++) {
        if (!species_has_type(s, T_HOLLOW) && !species_has_type(s, T_METAL)) continue;
        Monster m = monster_make(s, 10);
        if (!status_immune(&m, STATUS_PSN)) immune = 0;
    }
    CHECK(immune, "HOLLOW and METAL kin can't be poisoned");
    battle.ev_count = 0;
}

/* ---------------- animations ---------------- */

static int run_anim(int max, int *sprites)
{
    int f = 0;
    *sprites = 0;
    while (anim_busy() && f < max) {
        oam_begin();
        anim_update();
        *sprites += oam_count;
        oam_end();
        f++;
    }
    return f;
}

static void test_animations(void)
{
    bout(SP_FLARIX, 30, SP_GOLEMIT, 30);
    opt.battle_anims = 1;
    /* every kind: finishes, draws something and lands its impact */
    int finish = 1, draws = 1, lands = 1, covered = 1;
    for (int kind = AK_RATTLE; kind < AK_COUNT; kind++) {
        int mv = -1;
        for (int m = 0; m < MOVE_COUNT && mv < 0; m++)
            if (MOVES[m].anim == kind) mv = m;
        if (mv < 0) {
            covered = 0;
            printf("     kind %d has no move\n", kind);
            continue;
        }
        for (int m = 0; m < MOVE_COUNT; m++) {
            if (MOVES[m].anim != kind) continue;
            for (int side = 0; side < 2; side++) {
                anim_clear();
                battle.impacted = 0;
                anim_start(m, side, HITF_LAST);
                int spr, f = run_anim(400, &spr);
                if (f >= 400 || f < 20) {
                    finish = 0;
                    printf("     %s: %d frames\n", MOVES[m].name, f);
                }
                if (spr < f) {
                    draws = 0;
                    printf("     %s draws only %d sprites in %d frames\n", MOVES[m].name, spr, f);
                }
                if (MOVES[m].cat != CAT_STATUS && !battle.impacted) {
                    lands = 0;
                    printf("     %s never lands its blow\n", MOVES[m].name);
                }
            }
        }
    }
    CHECK(covered, "every new animation kind is used by a move");
    CHECK(finish, "every new animation kind finishes");
    CHECK(draws, "every new animation kind draws its particles");
    CHECK(lands, "every new attack animation lands an impact");

    /* the legend's arrival finishes */
    anim_clear();
    anim_start_legend(SIDE_ENEMY);
    int spr, f = run_anim(400, &spr);
    CHECK(f < 400 && spr > 0, "the legend intro animation finishes");

    /* a step that is not shown pushes no sprites but still advances */
    anim_clear();
    anim_start(M_SHROUD, SIDE_ALLY, HITF_NODMG | HITF_LAST);
    for (int i = 0; i < 20; i++) {
        oam_begin();
        anim_update();
        oam_end();
    }
    int t0 = anim.t;
    oam_begin();
    anim_nodraw = 1;
    anim_update();
    anim_nodraw = 0;
    int hidden = oam_count;
    oam_end();
    CHECK(hidden == 0 && anim.t == t0 + 1, "a hidden animation step draws nothing and advances one frame");
    anim_clear();
}

/* ---------------- scenes ---------------- */

static void test_scenes(void)
{
    CHECK(BBG_SCENE_COUNT == BSCENE_COUNT, "every BSCENE_* has a painted background");
    int ok = 1;
    for (int sc = 0; sc < BSCENE_COUNT; sc++) {
        battle.scene = sc;
        memset((void *)VRAM_SCENE_TILES, 0, 32 * 16);
        battle_load_scene();
        const BattleSceneArt *a = &bbg_scenes[sc < BBG_SCENE_COUNT ? sc : BBG_SCENE_COUNT - 1];
        int tiles_ok = a->tile_count > 1 && a->tile_count <= 500;
        int colours = 0;
        for (int b = 0; b < 4; b++)
            for (int i = 1; i < 16; i++) colours += scene_pal[b][i] != 0;
        u32 sum = 0;
        for (int i = 0; i < 8 * 16; i++) sum |= VRAM_SCENE_TILES[8 + i];
        if (!tiles_ok || colours < 6 || !sum) {
            ok = 0;
            printf("     scene %d: %d tiles, %d colours\n", sc, a->tile_count, colours);
        }
    }
    CHECK(ok, "every battle scene loads its tiles, map and colours");
}

/* ---------------- speed ---------------- */

/* Frames from choosing the first move until the menu comes back. */
static int timed_turn(int speed)
{
    rng_seed(99);
    bout(SP_FLARIX, 30, SP_GOLEMIT, 30);
    opt.battle_speed = (u8)speed;
    for (int side = 0; side < 2; side++) {
        disp_sync(side);
        battle.disp[side].visible = 1;
    }
    battle.ev_count = 0;
    battle.state = BST_ACTION;
    battle_player_move(0);
    battle_play();
    int f = 0;
    while (f < 4000 && game_mode == MODE_BATTLE && battle.state != BST_ACTION && battle.state != BST_MOVES) {
        step((f & 7) == 0 ? KEY_A : 0);
        f++;
    }
    return f;
}

/* Frames of a wild bout's intro, from the wipe to the menu. */
static int timed_intro(int speed)
{
    new_game();
    dialog_clear();
    game_mode = MODE_FIELD;
    Monster m = monster_make(SP_FLARIX, 20);
    give_monster(&m);
    opt.battle_speed = (u8)speed;
    rng_seed(77);
    battle_start_wild(monster_make(SP_GOLEMIT, 12));
    int f = 0;
    while (f < 4000 && game_mode == MODE_BATTLE && battle.state != BST_ACTION) {
        step((f & 7) == 0 ? KEY_A : 0);
        f++;
    }
    return f;
}

static void test_speed(void)
{
    int slow = timed_turn(0), fast = timed_turn(1);
    printf("     one turn: %d frames normal, %d fast\n", slow, fast);
    CHECK(slow < 4000 && fast < 4000, "a turn plays through at both speeds");
    CHECK(fast * 100 < slow * 75, "battle speed plays a turn in well under 3/4 of the frames");
    int is = timed_intro(0), ifast = timed_intro(1);
    printf("     intro: %d frames normal, %d fast\n", is, ifast);
    CHECK(ifast < is, "battle speed shortens the intro");

    /* the fast mode lands every impact of a multi-hit animation */
    opt.battle_speed = 1;
    bout(SP_FLARIX, 30, SP_GOLEMIT, 30);
    anim_clear();
    anim_start(M_DEATH_KNELL, SIDE_ALLY, HITF_LAST);
    int impacts = 0, f = 0;
    while (anim_busy() && f < 400) {
        oam_begin();
        int before = anim.last_impact;
        anim_nodraw = 1;
        anim_update();
        anim_nodraw = 0;
        if (anim.last_impact != before) impacts++;
        before = anim.last_impact;
        anim_update();
        if (anim.last_impact != before) impacts++;
        oam_end();
        f++;
    }
    CHECK(impacts == MOVES[M_DEATH_KNELL].count, "fast mode still fires every toll of DEATH KNELL");
    opt.battle_speed = 0;
    anim_clear();
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    opt.sound = 0;
    test_move_table();
    test_effects();
    test_animations();
    test_scenes();
    test_speed();
    if (failures == 0) {
        printf("all battle checks passed\n");
        return 0;
    }
    printf("%d battle check(s) FAILED\n", failures);
    return 1;
}
