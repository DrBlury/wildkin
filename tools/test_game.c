/*
 * Host-side unit tests for the game rules in src/main.c: data tables
 * (types, 60 moves, 32 species, learnsets, evolutions, items), stats and
 * damage, catching, the battle event timeline (damage must only appear
 * after the attack animation), XP/level-ups/move learning, evolution,
 * saving and a tiered round-robin balance simulation.
 *
 * The whole game compiles for the host with plain memory standing in for
 * the GBA hardware, so screens and battles can be driven frame by frame.
 * Run with `make test`.
 */
#define main gba_main
#include "../src/main.c"
#undef main

#include <stdio.h>
#include <string.h>

static int failures = 0;

#define CHECK(cond, msg)                                                   \
    do {                                                                   \
        if (cond) {                                                        \
            printf("ok: %s\n", (msg));                                     \
        } else {                                                           \
            printf("FAIL: %s\n", (msg));                                   \
            failures++;                                                    \
        }                                                                  \
    } while (0)

static void step(u16 keys)
{
    keys_prev = keys_now;
    keys_now = keys;
    game_frame();
}

static void tap(u16 keys)
{
    if (keys_now) step(0); /* a press only counts after a release */
    step(keys);
    step(0);
}

static int renderable(const char *s)
{
    for (; *s; s++)
        if ((unsigned char)*s < FONT_FIRST || (unsigned char)*s >= FONT_FIRST + FONT_COUNT)
            if (*s != '\n' && *s != '\f') return 0;
    return 1;
}

/* Play queued battle events until the menu comes back (pressing A for
 * messages that wait). Returns frames used. */
static int battle_settle(int limit)
{
    int f = 0;
    while (f < limit && game_mode == MODE_BATTLE && battle.state != BST_ACTION &&
           battle.state != BST_MOVES) {
        step((f & 7) == 0 ? KEY_A : 0);
        f++;
    }
    return f;
}

static void fresh_game(void)
{
    new_game();
    dialog_clear();
    game_mode = MODE_FIELD;
}

/* ---------------- data ---------------- */

static void test_data(void)
{
    CHECK(MOVE_COUNT == 130, "there are exactly 130 learnable moves (docs/EXPANSION.md 5)");
    CHECK(SP_COUNT == 174, "there are 174 species (docs/EXPANSION.md 4)");
    CHECK(ITEM_COUNT >= 100, "there are at least 100 different items");
    CHECK(TYPE_COUNT == 18, "there are 18 types");

    int moves_ok = 1, names_ok = 1, anim_ok = 1;
    for (int i = 0; i < MOVE_TABLE_SIZE; i++) {
        const Move *m = &MOVES[i];
        if (m->type >= TYPE_COUNT || m->cat > CAT_STATUS || m->pp < 1 || m->pp > 40 ||
            m->acc > 100 || (m->cat == CAT_STATUS) != (m->power == 0) || !m->desc)
            moves_ok = 0;
        if (str_len(m->name) > 12 || text_width(m->name) > 82 || !renderable(m->name) ||
            !renderable(m->desc)) {
            names_ok = 0;
            printf("  move name/desc does not fit: %s (%d px)\n", m->name, text_width(m->name));
        }
        if (m->anim >= AK_COUNT || m->fx >= FX_COUNT || m->fx2 >= FX_COUNT || m->count < 1)
            anim_ok = 0;
    }
    CHECK(moves_ok, "every move has a sane type, category, power, accuracy and PP");
    CHECK(names_ok, "move names and descriptions fit the UI and the font");
    CHECK(anim_ok, "every move has a valid animation, particles and count");

    /* distinct animation recipes: no two moves look exactly alike */
    int distinct = 1;
    for (int a = 0; a < MOVE_COUNT; a++)
        for (int b = a + 1; b < MOVE_COUNT; b++)
            if (MOVES[a].anim == MOVES[b].anim && MOVES[a].fx == MOVES[b].fx &&
                MOVES[a].col1 == MOVES[b].col1 && MOVES[a].count == MOVES[b].count) {
                distinct = 0;
                printf("     %s and %s look alike\n", MOVES[a].name, MOVES[b].name);
            }
    CHECK(distinct, "every move has its own animation recipe");

    int learned[MOVE_COUNT] = { 0 };
    int ls_ok = 1, stab_ok = 1, species_ok = 1, text_ok = 1;
    for (int s = 0; s < SP_COUNT; s++) {
        const Species *sp = &SPECIES[s];
        int prev = 1, has_stab = 0, n = 0;
        if (str_len(sp->name) > 10 || !renderable(sp->name) || !renderable(sp->desc) ||
            !renderable(sp->category) || text_width(sp->category) > 72)
            text_ok = 0;
        if (sp->type1 >= TYPE_COUNT || (sp->type2 != TYPE_NONE && sp->type2 >= TYPE_COUNT) ||
            sp->type1 == sp->type2 || sp->catch_rate < 3 || !sp->xp_yield) {
            species_ok = 0;
            printf("     %s: bad types / catch / xp\n", sp->name);
        }
        for (int b = 0; b < BS_COUNT; b++)
            if (sp->base[b] < 20 || sp->base[b] > (sp->rarity == R_LEGEND ? 160 : 150)) {
                species_ok = 0;
                printf("     %s: base stat %d out of range\n", sp->name, sp->base[b]);
            }
        if (sp->learnset[0].level != 1) ls_ok = 0;
        for (const LearnEntry *e = sp->learnset; e->level; e++, n++) {
            if (e->level < prev || e->move >= MOVE_COUNT) ls_ok = 0;
            prev = e->level;
            learned[e->move] = 1;
            if (MOVES[e->move].power && species_has_type(s, MOVES[e->move].type) && e->level <= 20)
                has_stab = 1;
        }
        if (n < 6) {
            ls_ok = 0;
            printf("     %s: only %d moves\n", sp->name, n);
        }
        if (!has_stab) {
            stab_ok = 0;
            printf("     %s: no same-type attack by Lv20\n", sp->name);
        }
    }
    CHECK(species_ok, "species types, base stats and catch rates are sane");
    CHECK(text_ok, "species names, categories and catalogue text fit the UI");
    CHECK(ls_ok, "learnsets start at Lv1, are ordered, valid and at least six moves long");
    CHECK(stab_ok, "every species learns a same-type attack by Lv20");
    int all_learned = 1;
    for (int m = 0; m < MOVE_COUNT; m++)
        if (!learned[m]) {
            all_learned = 0;
            printf("     move %s is never learned\n", MOVES[m].name);
        }
    CHECK(all_learned, "every move can be learned by some species");

    int evo_ok = 1, evo_count = 0, stone_evos = 0;
    for (int s = 0; s < SP_COUNT; s++) {
        const Species *sp = &SPECIES[s];
        if (sp->evo_kind == EVO_NONE) continue;
        evo_count++;
        int into = sp->evo_into;
        if (into >= SP_COUNT || into == s || species_base_stat_total(into) <= species_base_stat_total(s))
            evo_ok = 0;
        if (sp->evo_kind == EVO_LEVEL && (sp->evo_param < 10 || sp->evo_param > 50)) evo_ok = 0;
        if (sp->evo_kind == EVO_ITEM) {
            stone_evos++;
            if (ITEMS[sp->evo_param].kind != IK_SHARD) evo_ok = 0;
        }
        if (species_prevo(into) != s) evo_ok = 0;
    }
    CHECK(evo_ok, "evolutions point forward, raise base stats and use stones correctly");
    CHECK(evo_count >= 50 && stone_evos >= 8, "there are level and shard growths");

    int items_ok = 1;
    for (int i = 0; i < ITEM_COUNT; i++)
        if (!renderable(ITEMS[i].name) || text_width(ITEMS[i].name) > 88 || !renderable(ITEMS[i].desc) ||
            ITEMS[i].pocket >= POCKET_COUNT || ITEMS[i].icon >= ICON_COUNT) {
            items_ok = 0;
            printf("     item %s does not fit (%d px)\n", ITEMS[i].name, text_width(ITEMS[i].name));
        }
    CHECK(items_ok, "items have renderable names, descriptions and a pocket");

    /* type chart */
    int chart_ok = 1;
    for (int a = 0; a < TYPE_COUNT; a++) {
        int bites = 0;
        for (int d = 0; d < TYPE_COUNT; d++) {
            int m = type_mult(a, d);
            if (m != 0 && m != 50 && m != 100 && m != 200) chart_ok = 0;
            if (m == 200) bites = 1;
        }
        if (a != T_BEAST && !bites) chart_ok = 0;
    }
    CHECK(chart_ok, "the 14-type chart is valid and every type (but NORMAL) hits something hard");
    CHECK(type_effectiveness(T_SPARK, SP_TERRASHELL) == 0 &&
          type_effectiveness(T_FROST, SP_ZEPHRAM) == 400 &&
          type_effectiveness(T_BLAZE, SP_ZEPHRAM) == 200 &&
          type_effectiveness(T_BEAST, SP_WISPIRE) == 0,
          "dual types multiply (immunities, x4 weaknesses)");
}

/* ---------------- monster rules ---------------- */

static void test_monsters(void)
{
    Monster a = monster_make(SP_FLARIX, 5), b = monster_make(SP_FLARIX, 40);
    CHECK(b.max_hp > a.max_hp && b.stat[STAT_ATK] > a.stat[STAT_ATK], "stats grow with level");
    int curve = 1;
    for (int l = 1; l < 100; l++)
        if (xp_for_level(l + 1) <= xp_for_level(l)) curve = 0;
    CHECK(curve, "the experience curve rises every level");

    Monster w = monster_make(SP_PYREFOX, 30);
    int ember = 0, pp = 1, count = 0;
    for (int i = 0; i < MAX_MOVES; i++) {
        if (w.moves[i] == MOVE_NONE) continue;
        count++;
        if (w.pp[i] != MOVES[w.moves[i]].pp) pp = 0;
        if (w.moves[i] == M_KILN_BREATH) ember = 1;
    }
    CHECK(count == 4 && ember && pp, "wild creatures know their four latest moves with full PP");

    Monster l7 = monster_make(SP_FLARIX, 6);
    u8 got[4];
    CHECK(learnset_at(SP_FLARIX, 7, got) == 1 && got[0] == M_CINDER_FLICK, "FLARIX learns EMBER at Lv7");
    l7.xp = xp_for_level(7);
    monster_level_up(&l7);
    CHECK(l7.level == 7 && monster_add_move(&l7, M_CINDER_FLICK) && monster_knows(&l7, M_CINDER_FLICK),
          "leveling up and learning into a free slot works");
    Monster full = monster_make(SP_FLARIX, 30);
    CHECK(monster_move_count(&full) == 4 && !monster_add_move(&full, M_SUNFLARE),
          "a creature with four moves must forget one to learn another");

    Monster evo = monster_make(SP_FLARIX, 16);
    CHECK(monster_level_evolution(&evo) == SP_PYREFOX, "FLARIX evolves at Lv16");
    evo.hp = 5;
    int missing = evo.max_hp - evo.hp;
    monster_evolve(&evo, SP_PYREFOX);
    CHECK(evo.species == SP_PYREFOX && evo.max_hp - evo.hp == missing,
          "evolving recalculates stats and keeps missing HP");
    Monster thornip = monster_make(SP_THORNIP, 10);
    CHECK(monster_item_evolution(&thornip, ITEM_BLOOM_SHARD) == SP_BRAMBLOR &&
          monster_item_evolution(&thornip, ITEM_FROST_SHARD) < 0 && monster_level_evolution(&thornip) < 0,
          "stone evolutions need the right stone");

    /* damage math */
    Monster att = monster_make(SP_FLARIX, 30);
    Monster grass = monster_make(SP_DANDELAMB, 30), water = monster_make(SP_AQUAPO, 30);
    DamageResult se = calc_damage(&att, 0, &grass, 0, M_CINDER_FLICK, 0, 100);
    DamageResult nv = calc_damage(&att, 0, &water, 0, M_CINDER_FLICK, 0, 100);
    DamageResult crit = calc_damage(&att, 0, &grass, 0, M_CINDER_FLICK, 1, 100);
    CHECK(se.effectiveness == 200 && nv.effectiveness == 50 && se.damage > nv.damage * 3,
          "super-effective hits far harder than resisted ones");
    CHECK(crit.damage >= se.damage * 2 - 2, "critical hits double the damage");
    Monster earth = monster_make(SP_GOLEMIT, 30), zap = monster_make(SP_ZAPPET, 30);
    CHECK(calc_damage(&zap, 0, &earth, 0, M_STATIC_POP, 0, 100).damage == 0,
          "EARTH types are immune to ELECTRIC moves");
    s8 up[STAT_COUNT] = { 2, 0, 0, 0, 0, 0 };
    CHECK(calc_damage(&att, up, &water, 0, M_SWIPE, 0, 100).damage >
          calc_damage(&att, 0, &water, 0, M_SWIPE, 0, 100).damage,
          "stat stages change damage");
    int healthy = calc_damage(&att, 0, &water, 0, M_SWIPE, 0, 100).damage;
    att.status = STATUS_BRN;
    int burned = calc_damage(&att, 0, &water, 0, M_SWIPE, 0, 100).damage;
    att.status = STATUS_NONE;
    CHECK(burned < healthy, "burns weaken physical attacks");

    /* catching */
    rng_seed(3);
    Monster wild = monster_make(SP_NIBBIT, 10);
    int full_caught = 0, low_caught = 0, ultra = 0;
    for (int i = 0; i < 400; i++) {
        wild.hp = wild.max_hp;
        full_caught += catch_shakes(&wild, 10) >= 4;
        wild.hp = 1;
        low_caught += catch_shakes(&wild, 10) >= 4;
    }
    Monster drake = monster_make(SP_DRAKORA, 30);
    drake.hp = 1;
    int drake_normal = 0;
    for (int i = 0; i < 400; i++) {
        drake_normal += catch_shakes(&drake, 10) >= 4;
        ultra += catch_shakes(&drake, 20) >= 4;
    }
    CHECK(low_caught > full_caught, "weakened creatures are easier to catch");
    CHECK(ultra > drake_normal && drake_normal < 200, "better capsules catch more; legends resist");
}

/* ---------------- battle timeline (the reported bug) ---------------- */

static int first_event_index(int type, int side)
{
    for (int i = 0; i < battle.ev_count; i++)
        if (battle.ev[i].type == type && battle.ev[i].side == side) return i;
    return -1;
}

static void test_battle_timing(void)
{
    fresh_game();
    Monster me = monster_make(SP_FLARIX, 20);
    give_monster(&me);
    rng_seed(11);
    battle_start_wild(monster_make(SP_GOLEMIT, 12)); /* slow foe: we move first */
    int f = battle_settle(2000);
    CHECK(battle.state == BST_ACTION && f < 2000, "the battle intro plays and reaches the menu");
    CHECK(battle.disp[SIDE_ENEMY].visible && battle.disp[SIDE_ALLY].visible,
          "both creatures are sent out");

    int shown = battle.disp[SIDE_ENEMY].hp;
    battle.state = BST_MOVES;
    battle.move_cursor = 0;
    tap(KEY_A);
    CHECK(battle.team[0].hp < shown, "choosing a move resolves the damage in the rules...");
    CHECK(battle.disp[SIDE_ENEMY].hp == shown, "...but the foe's HP bar does not move yet");
    int anim_i = first_event_index(EV_ANIM, SIDE_ALLY);
    int hp_i = first_event_index(EV_HP, SIDE_ENEMY);
    CHECK(anim_i >= 0 && hp_i > anim_i, "the attack animation is queued before the HP drain");

    int bar_moved_early = 0, saw_anim = 0, frames = 0;
    while (battle.ev_count && frames < 600) {
        int type = battle.ev[0].type;
        if (type == EV_ANIM) saw_anim = 1;
        if ((type == EV_TEXT || type == EV_ANIM || type == EV_HIT) &&
            first_event_index(EV_HP, SIDE_ENEMY) >= 0 && battle.disp[SIDE_ENEMY].hp != shown)
            bar_moved_early = 1;
        step(0);
        frames++;
        if (type == EV_HP && battle.ev_count && battle.ev[0].type != EV_HP) break;
    }
    CHECK(saw_anim && !bar_moved_early, "the HP bar stays full while the move animates");
    battle_settle(2000);
    CHECK(battle.disp[SIDE_ENEMY].hp == battle.team[0].hp,
          "after the hit lands the bar drains to the real HP");

    /* priority: QUICK STRIKE beats a faster foe */
    fresh_game();
    Monster slow = monster_make(SP_GOLEMIT, 20);
    monster_replace_move(&slow, 0, M_DART);
    give_monster(&slow);
    battle_start_wild(monster_make(SP_PUFFOWL, 20)); /* faster, but no priority moves */
    battle_settle(2000);
    for (int i = 0; i < MAX_MOVES; i++)
        if (party[0].moves[i] == M_DART) battle.move_cursor = i;
    battle.ev_count = 0;
    battle_player_move(battle.move_cursor);
    int ally_anim = first_event_index(EV_ANIM, SIDE_ALLY);
    int foe_anim = first_event_index(EV_ANIM, SIDE_ENEMY);
    CHECK(party[0].moves[battle.move_cursor] == M_DART &&
          (foe_anim < 0 || ally_anim < foe_anim), "priority moves strike first");
}

/* ---------------- battle outcomes ---------------- */

static void test_battle_flow(void)
{
    /* knock out a wild creature: XP, level up and a learned move */
    fresh_game();
    Monster me = monster_make(SP_FLARIX, 6);
    me.xp = xp_for_level(7) - 1;
    give_monster(&me);
    rng_seed(21);
    Monster foe = monster_make(SP_NIBBIT, 5);
    foe.hp = 1;
    battle_start_wild(foe);
    battle_settle(2000);
    battle.state = BST_MOVES;
    battle.move_cursor = 0;
    tap(KEY_A);
    int levels_before = party[0].level;
    for (int f = 0; f < 3000 && game_mode == MODE_BATTLE; f++) step((f & 7) == 0 ? KEY_A : 0);
    CHECK(game_mode != MODE_BATTLE && party[0].level > levels_before,
          "defeating a wild creature grants XP and levels up");
    CHECK(monster_knows(&party[0], M_CINDER_FLICK), "reaching Lv7 teaches EMBER");

    /* catching fills the catalogue and the team */
    fresh_game();
    Monster c = monster_make(SP_FLARIX, 30);
    give_monster(&c);
    bag[ITEM_STAR_LANTERN] = 20;
    rng_seed(5);
    Monster target = monster_make(SP_PUFFOWL, 3);
    target.hp = 1;
    target.status = STATUS_SLP;
    battle_start_wild(target);
    battle_settle(2000);
    int thrown = 0;
    while (game_mode == MODE_BATTLE && thrown < 10) {
        battle_item_result(ITEM_STAR_LANTERN, 0);
        thrown++;
        for (int f = 0; f < 800 && game_mode == MODE_BATTLE && battle.state != BST_ACTION; f++)
            step((f & 7) == 0 ? KEY_A : 0);
    }
    CHECK(party_count == 2 && party[1].species == SP_PUFFOWL && dex_caught[SP_PUFFOWL],
          "a caught creature joins the team and is marked in the catalogue");

    /* capsules are refused in trainer battles */
    fresh_game();
    give_monster(&c);
    bag[ITEM_LANTERN] = 3;
    battle_start_trainer();
    battle_settle(3000);
    CHECK(battle.team_count >= 2, "the arena guide fields a team");
    battle_item_result(ITEM_LANTERN, 0);
    battle_settle(2000);
    CHECK(bag[ITEM_LANTERN] == 3 && battle.result == BR_NONE, "no catching in trainer battles");

    /* winning a trainer battle pays prize money */
    int money_before = money;
    for (int round = 0; round < 60 && game_mode == MODE_BATTLE; round++) {
        party[0].max_hp = party[0].hp = 999; /* this check is about the prize, not survival */
        battle.team[battle.team_idx].hp = 1;
        battle.state = BST_MOVES;
        battle.move_cursor = 0;
        tap(KEY_A);
        for (int f = 0; f < 1500 && game_mode == MODE_BATTLE && battle.state != BST_ACTION; f++)
            step((f & 7) == 0 ? KEY_A : 0);
    }
    CHECK(game_mode != MODE_BATTLE && money > money_before, "beating the guide pays prize money");

    /* status effects */
    fresh_game();
    give_monster(&c);
    battle_start_wild(monster_make(SP_NIBBIT, 30));
    battle_settle(2000);
    battle.ev_count = 0;
    Monster *foe_m = side_mon(SIDE_ENEMY);
    foe_m->status = STATUS_BRN;
    int hp0 = foe_m->hp;
    end_of_turn();
    CHECK(foe_m->hp == hp0 - foe_m->max_hp / 8, "burns cost an eighth of max HP each turn");
    foe_m->status = STATUS_NUMB;
    CHECK(battle_stat(foe_m, battle.stages[SIDE_ENEMY], STAT_SPE) == foe_m->stat[STAT_SPE] / 4,
          "paralysis cuts speed");
    CHECK(status_immune(&party[0], STATUS_BRN), "FIRE types cannot be burned");
}

/* ---------------- learning & evolution through the UI flow ---------------- */

static void run_dialog(int choice_first, int limit)
{
    for (int f = 0; f < limit && dialog_active(); f++) {
        if (choice.active && choice_first >= 0) {
            choice.cursor = choice_first;
            choice_first = -1;
        }
        step((f & 3) == 0 ? KEY_A : 0);
    }
}

static void test_learning_and_evolution(void)
{
    fresh_game();
    Monster m = monster_make(SP_FLARIX, 30);
    give_monster(&m);
    int old = party[0].moves[2];
    learn_begin(0, M_SUNFLARE);
    CHECK(dialog_active(), "a full move set asks before learning");
    /* YES, then forget slot 2 */
    for (int f = 0; f < 600 && dialog_active(); f++) {
        if (choice.active) {
            choice.cursor = choice.count == 2 ? 0 : 2;
        }
        step((f & 3) == 0 ? KEY_A : 0);
    }
    CHECK(party[0].moves[2] == M_SUNFLARE && old != M_SUNFLARE,
          "choosing a move to forget replaces it with the new one");
    CHECK(party[0].pp[2] == MOVES[M_SUNFLARE].pp, "the new move starts with full PP");

    /* rare candy at the evolution level queues an evolution scene */
    fresh_game();
    Monster f15 = monster_make(SP_FLARIX, 15);
    give_monster(&f15);
    bag[ITEM_SUNSEED] = 1;
    CHECK(item_use_field(ITEM_SUNSEED, 0) && party[0].level == 16 && evo_count == 1,
          "a RARE CANDY levels up and requests the evolution");
    run_dialog(-1, 400);
    evolve_start_next();
    CHECK(game_mode == MODE_EVOLVE, "the evolution scene starts");
    for (int f = 0; f < 1500 && game_mode == MODE_EVOLVE; f++) step((f & 7) == 0 ? KEY_A : 0);
    CHECK(party[0].species == SP_PYREFOX && dex_caught[SP_PYREFOX],
          "FLARIX evolves into PYREFOX and the catalogue records it");

    /* B cancels an evolution */
    fresh_game();
    give_monster(&f15);
    party[0].level = 16;
    evo_request(0, SP_PYREFOX);
    evolve_start_next();
    for (int f = 0; f < 60 && evo.state == EVS_INTRO; f++) step((f & 7) == 0 ? KEY_A : 0);
    step(0);
    step(KEY_B);
    for (int f = 0; f < 600 && game_mode == MODE_EVOLVE; f++) step((f & 7) == 0 ? KEY_A : 0);
    CHECK(party[0].species == SP_FLARIX, "pressing B stops an evolution");

    /* stones */
    fresh_game();
    Monster v = monster_make(SP_VOLTUX, 20);
    give_monster(&v);
    bag[ITEM_SPARK_SHARD] = 1;
    CHECK(!item_use_field(ITEM_BLOOM_SHARD, 0), "the wrong stone does nothing");
    CHECK(item_use_field(ITEM_SPARK_SHARD, 0) && evo_count == 1 && evo_queue[0].into == SP_VOLTLOPE &&
          bag[ITEM_SPARK_SHARD] == 0, "a THUNDERSTONE evolves VOLTUX and is used up");

    /* healing items */
    fresh_game();
    give_monster(&v);
    bag[ITEM_TONIC] = 2;
    party[0].hp = 5;
    CHECK(item_use_field(ITEM_TONIC, 0) && party[0].hp == 25 && bag[ITEM_TONIC] == 1,
          "a POTION restores 20 HP");
    party[0].hp = party[0].max_hp;
    CHECK(!item_use_field(ITEM_TONIC, 0) && bag[ITEM_TONIC] == 1,
          "a POTION is not wasted at full HP");
    party[0].hp = 0;
    bag[ITEM_WAKE_BELL] = 1;
    CHECK(item_use_field(ITEM_WAKE_BELL, 0) && party[0].hp == party[0].max_hp / 2, "REVIVE restores half HP");
    dialog_clear();
}

/* ---------------- saving ---------------- */

static void test_save(void)
{
    fresh_game();
    Monster a = monster_make(SP_AQUAPO, 12), b = monster_make(SP_ZAPPET, 9);
    give_monster(&a);
    give_monster(&b);
    for (int i = 0; i < 8; i++) {
        Monster s = monster_make(i, 5);
        give_monster(&s);
    }
    bag[ITEM_GLOW_LANTERN] = 7;
    money = 4321;
    flags_story_clear(); flag_set(FLAG_STARTER); flag_set(FLAG_LEAF_STONE);
    item_take(0);
    item_take(2);
    field_enter_map(MAP_SHOP, 3, 5, DIR_LEFT);

    static u8 sram[32768];
    memset(sram, 0xFF, sizeof(sram));
    CHECK(!save_load_from(sram), "blank SRAM loads nothing");
    CHECK(save_write_to(sram), "saving writes and verifies both slots");
    fresh_game();
    CHECK(save_load_from(sram) == SAVE_VERSION && party_count == 6 && storage_count == 4 &&
          bag[ITEM_GLOW_LANTERN] == 7 && money == 4321 && cur_map == MAP_SHOP &&
          player.x == 3 && player.y == 5 && player.facing == DIR_LEFT &&
          flag(FLAG_LEAF_STONE) && item_taken(0) && !item_taken(1) && item_taken(2) && party[0].species == SP_AQUAPO,
          "loading restores team, PC storage, bag, money, flags and position");
    sram[20] ^= 0x55;
    fresh_game();
    CHECK(save_load_from(sram) == SAVE_VERSION && party_count == 6, "a damaged primary slot falls back to the backup");
    sram[SAVE_BACKUP_OFFSET + 20] ^= 0x55;
    fresh_game();
    CHECK(!save_load_from(sram), "two damaged slots are rejected");

    /* version-1 saves from the previous release migrate */
    SaveDataV1 old;
    memset(&old, 0, sizeof(old));
    old.magic = SAVE_MAGIC;
    old.version = 1;
    old.party_count = 2;
    old.party[0].species = 0;  /* FLARIX */
    old.party[0].level = 12;
    old.party[0].cur_hp = 10;
    old.party[0].max_hp = 20;
    old.party[1].species = 8;  /* GOLEMIT */
    old.party[1].level = 9;
    old.party[1].cur_hp = 30;
    old.party[1].max_hp = 30;
    old.bag[0] = 4;
    old.bag[2] = 6;
    old.caught[8] = 1;
    old.starter_given = 1;
    old.checksum = fnv_bytes(&old, sizeof(old) - sizeof(old.checksum));
    memset(sram, 0xFF, sizeof(sram));
    memcpy(sram, &old, sizeof(old));
    fresh_game();
    CHECK(save_load_from(sram) == 1 && party_count == 2 && party[0].species == SP_FLARIX &&
          party[0].level == 12 && party[1].species == SP_GOLEMIT && bag[ITEM_TONIC] == 4 &&
          bag[ITEM_LANTERN] == 6 && dex_caught[SP_GOLEMIT] && (flag(FLAG_STARTER)) &&
          party[0].hp == party[0].max_hp / 2,
          "old saves migrate: team, HP ratio, bag and catalogue carry over");
}

/* ---------------- traits, effects, bond, XP, wardens, story bouts ---------------- */

/* A bout with no intro: ally `a` against wild `b`, both at full health. */
static void duel(int a, int la, int b, int lb)
{
    fresh_game();
    Monster m = monster_make(a, la);
    give_monster(&m);
    battle_start_wild(monster_make(b, lb));
    battle.state = BST_ACTION;
    battle.ev_count = 0;
    battle.turn = 0;
}

static int count_text(const char *needle)
{
    int n = 0;
    for (int i = 0; i < battle.ev_count; i++) {
        const char *t = battle.ev[i].text;
        if (battle.ev[i].type != EV_TEXT) continue;
        for (const char *p = t; *p; p++) {
            const char *a = p, *b = needle;
            while (*a && *b && *a == *b) a++, b++;
            if (!*b) { n++; break; }
        }
    }
    return n;
}

static int count_events(int type, int side)
{
    int n = 0;
    for (int i = 0; i < battle.ev_count; i++)
        if (battle.ev[i].type == type && (side < 0 || battle.ev[i].side == side)) n++;
    return n;
}

static void test_vocabulary(void)
{
    duel(SP_FLARIX, 10, SP_NIBBIT, 5);
    battle_queue_intro();
    CHECK(count_text("A brimming NIBBIT wants a bout!") == 1 && count_text("Out you come, FLARIX!") == 1,
          "wild bouts open with 'A brimming X wants a bout!' and a lantern-release line");
    int old_words = count_text("fainted") + count_text("capsule") + count_text("CAPSULE") +
                    count_text("PP") + count_text("super effective") + count_text("paralyz");
    battle.ev_count = 0;
    Monster *foe = side_mon(SIDE_ENEMY);
    foe->hp = 1;
    use_move(SIDE_ALLY, M_CINDER_FLICK);
    CHECK(count_text("dozed off!") == 1, "a kin at 0 HP 'dozed off'");
    battle.ev_count = 0;
    foe->hp = foe->max_hp;
    foe->status = STATUS_NONE;
    inflict_status(SIDE_ENEMY, STATUS_NUMB);
    CHECK(count_text("is numb!") == 1 && old_words == 0, "NUMB replaces paralysis; no old vocabulary");
    duel(SP_FLARIX, 30, SP_DANDELAMB, 30);
    side_mon(SIDE_ENEMY)->trait = TR_SURGE;
    use_move(SIDE_ALLY, M_CINDER_FLICK);
    CHECK(count_text("It struck a weak spot!") == 1, "super-effective hits 'strike a weak spot'");
    duel(SP_FLARIX, 30, SP_AQUAPO, 30);
    side_mon(SIDE_ENEMY)->trait = TR_SURGE;
    use_move(SIDE_ALLY, M_CINDER_FLICK);
    CHECK(count_text("It was shrugged off...") == 1, "resisted hits are 'shrugged off'");
}

static void test_traits(void)
{
    Monster att = monster_make(SP_FLARIX, 30), def = monster_make(SP_GOLEMIT, 30);
    att.trait = TR_EMBERSKIN;
    def.trait = TR_STUBBORN;
    int base = calc_damage(&att, 0, &def, 0, M_CINDER_FLICK, 0, 100).damage;
    def.trait = TR_THICK_FUR;
    DamageResult fur = calc_damage(&att, 0, &def, 0, M_CINDER_FLICK, 0, 100);
    CHECK(fur.damage <= base / 2 + 1 && fur.def_trait, "THICK FUR halves BLAZE damage");
    Monster grass = monster_make(SP_DANDELAMB, 30);
    grass.trait = TR_SURGE;
    int se = calc_damage(&att, 0, &grass, 0, M_CINDER_FLICK, 0, 100).damage;
    grass.trait = TR_BEDROCK;
    int se_bed = calc_damage(&att, 0, &grass, 0, M_CINDER_FLICK, 0, 100).damage;
    CHECK(se_bed < se && se_bed >= se * 3 / 4 - 2, "BEDROCK softens weak-spot hits to x0.75");
    Monster bear = monster_make(SP_MAGMAUL, 50), rat = monster_make(SP_NIBBIT, 50);
    bear.trait = TR_THICK_FUR;
    rat.trait = TR_HOARDER;
    int phys = calc_damage(&bear, 0, &rat, 0, M_BONK, 0, 100).damage;
    int spec = calc_damage(&bear, 0, &rat, 0, M_KILN_BREATH, 0, 100).damage;
    bear.trait = TR_BRUISER;
    CHECK(calc_damage(&bear, 0, &rat, 0, M_BONK, 0, 100).damage > phys &&
          calc_damage(&bear, 0, &rat, 0, M_KILN_BREATH, 0, 100).damage == spec,
          "BRUISER hits harder with physical moves only");
    att.trait = TR_SURGE;
    int full = calc_damage(&att, 0, &grass, 0, M_CINDER_FLICK, 0, 100).damage;
    att.hp = att.max_hp / 4;
    CHECK(calc_damage(&att, 0, &grass, 0, M_CINDER_FLICK, 0, 100).damage > full, "SURGE powers up at low HP");
    att.hp = att.max_hp;
    Monster zeph = monster_make(SP_ZEPHRAM, 30);
    zeph.trait = TR_DRIFTER;
    CHECK(move_effectiveness(M_ROCKFALL, &att, &zeph) == 0 && calc_damage(&att, 0, &zeph, 0, M_ROCKFALL, 0, 100).damage == 0,
          "DRIFTER floats clear of STONE moves");
    Monster owl = monster_make(SP_PUFFOWL, 10);
    owl.trait = TR_WAKEFUL;
    CHECK(status_immune(&owl, STATUS_SLP), "WAKEFUL kin can't fall asleep");

    /* SOAKER drinks TIDE moves */
    duel(SP_AQUAPO, 30, SP_BUBBLIN, 30);
    Monster *foe = side_mon(SIDE_ENEMY);
    foe->trait = TR_SOAKER;
    foe->hp = foe->max_hp / 2;
    int hp0 = foe->hp;
    use_move(SIDE_ALLY, M_SWELL);
    CHECK(foe->hp == hp0 + foe->max_hp / 4 && count_text("SOAKER") == 1, "SOAKER heals from TIDE moves and says so");
    /* CONDUCTOR drinks SPARK moves */
    duel(SP_ZAPPET, 30, SP_ZAPPET, 30);
    foe = side_mon(SIDE_ENEMY);
    foe->trait = TR_CONDUCTOR;
    foe->hp = foe->max_hp / 2;
    hp0 = foe->hp;
    use_move(SIDE_ALLY, M_STATIC_POP);
    CHECK(foe->hp > hp0, "CONDUCTOR heals from SPARK moves");

    /* STUBBORN: survives a knockout blow from full HP */
    duel(SP_MAGMAUL, 60, SP_GOLEMIT, 5);
    foe = side_mon(SIDE_ENEMY);
    foe->trait = TR_STUBBORN;
    use_move(SIDE_ALLY, M_BONK);
    CHECK(foe->hp == 1 && count_text("STUBBORN") == 1, "STUBBORN holds on with 1 HP from full");
    battle.ev_count = 0;
    use_move(SIDE_ALLY, M_BONK);
    CHECK(foe->hp == 0, "...but not twice");

    /* contact traits */
    int caught = 0;
    for (int i = 0; i < 60; i++) {
        duel(SP_NIBBIT, 30, SP_ZAPPET, 30);
        side_mon(SIDE_ENEMY)->trait = TR_STATIC_FUR;
        side_mon(SIDE_ENEMY)->max_hp = side_mon(SIDE_ENEMY)->hp = 999;
        use_move(SIDE_ALLY, M_BONK);
        if (party[0].status == STATUS_NUMB) caught++;
    }
    CHECK(caught > 6 && caught < 35, "STATIC FUR numbs physical attackers about 30% of the time");
    caught = 0;
    for (int i = 0; i < 60; i++) {
        duel(SP_NIBBIT, 30, SP_FLARIX, 30);
        side_mon(SIDE_ENEMY)->trait = TR_EMBERSKIN;
        side_mon(SIDE_ENEMY)->max_hp = side_mon(SIDE_ENEMY)->hp = 999;
        use_move(SIDE_ALLY, M_CINDER_FLICK);   /* special: never touches */
        if (party[0].status == STATUS_BRN) caught++;
    }
    CHECK(caught == 0, "contact traits only answer physical moves");

    /* GLOWER on entry */
    duel(SP_FLARIX, 20, SP_GNAWLORD, 20);
    side_mon(SIDE_ENEMY)->trait = TR_GLOWER;
    party[0].trait = TR_SURGE;
    entry_traits(SIDE_ENEMY);
    entry_traits(SIDE_ALLY);
    CHECK(battle.stages[SIDE_ALLY][STAT_ATK] == -1 && battle.stages[SIDE_ENEMY][STAT_ATK] == 0 &&
          count_text("GLOWER") == 1, "GLOWER lowers the foe's ATTACK when it enters");

    /* BASKER, SELFMEND, MOMENTUM at the end of turns */
    duel(SP_DANDELAMB, 20, SP_VOLTUX, 20);
    party[0].trait = TR_BASKER;
    party[0].hp = party[0].max_hp / 2;
    hp0 = party[0].hp;
    side_mon(SIDE_ENEMY)->trait = TR_MOMENTUM;
    end_of_turn();
    CHECK(party[0].hp == hp0 + (party[0].max_hp / 16 > 0 ? party[0].max_hp / 16 : 1), "BASKER recovers 1/16 each turn");
    CHECK(battle.stages[SIDE_ENEMY][STAT_SPE] == 0, "MOMENTUM waits a turn...");
    end_of_turn();
    CHECK(battle.stages[SIDE_ENEMY][STAT_SPE] == 1, "...then SPEED rises every other turn");
    int cured = 0;
    rng_seed(77);
    for (int i = 0; i < 90; i++) {
        duel(SP_AQUAPO, 20, SP_NIBBIT, 20);
        party[0].trait = TR_SELFMEND;
        party[0].bond = 70;
        party[0].status = STATUS_PSN;
        party[0].max_hp = party[0].hp = 999;
        end_of_turn();
        if (party[0].status == STATUS_NONE) cured++;
    }
    CHECK(cured > 15 && cured < 50, "SELFMEND shakes off a status problem about 1 turn in 3");

    /* SLIPPERY always escapes wild bouts */
    int escaped = 0;
    for (int i = 0; i < 20; i++) {
        duel(SP_GOLEMIT, 5, SP_VOLTUX, 40);
        party[0].trait = TR_SLIPPERY;
        battle_try_run();
        if (battle.result == BR_RUN) escaped++;
    }
    CHECK(escaped == 20, "SLIPPERY always escapes from wild bouts");

    /* no fleeing a bout with another keeper, not even when SLIPPERY */
    duel(SP_GOLEMIT, 5, SP_VOLTUX, 40);
    battle.kind = BK_TRAINER;
    party[0].trait = TR_SLIPPERY;
    battle_try_run();
    CHECK(battle.result == BR_NONE && battle_run_chance() == 0, "keeper bouts can't be fled");

    /* lantern odds: better lanterns and a weaker foe both raise them */
    duel(SP_FLARIX, 20, SP_NIBBIT, 5);
    foe = side_mon(SIDE_ENEMY);
    int plain = lantern_catch_pct(ITEM_LANTERN), star = lantern_catch_pct(ITEM_STAR_LANTERN);
    foe->hp = 1;
    int tired = lantern_catch_pct(ITEM_LANTERN);
    CHECK(plain >= 0 && plain <= star && plain <= tired && tired <= 100, "lantern odds rise with finesse and fatigue");
    int got = 0;
    rng_seed(77);
    for (int i = 0; i < 400; i++) got += catch_shakes(foe, lantern_finesse(ITEM_LANTERN)) == 4;
    CHECK(got / 4 >= tired - 8 && got / 4 <= tired + 8, "the shown odds match the real catch rate");
    battle.kind = BK_TRAINER;
    CHECK(lantern_catch_pct(ITEM_LANTERN) < 0, "no odds are shown in keeper bouts");

    /* blacking out wakes you in the Hearth Hall you last rested in */
    duel(SP_FLARIX, 20, SP_NIBBIT, 5);
    field_enter_map(MAP_LUMEN_HEARTH, 5, 5, DIR_UP);
    hearth_rest();
    field_enter_map(MAP_TOWN, 6, 8, DIR_DOWN);
    party[0].hp = 1;
    battle.result = BR_LOSE;
    battle_exit();
    CHECK(cur_map == MAP_LUMEN_HEARTH && party[0].hp == party[0].max_hp, "a blackout returns you to the last Hearth Hall, healed");
    dialog_clear();
    game_mode = MODE_FIELD;

    /* KEEN EYE: perfect strikes about twice as often */
    int crit_plain = 0, crit_keen = 0;
    rng_seed(9);
    for (int i = 0; i < 400; i++) {
        duel(SP_THORNIP, 30, SP_BOULDRON, 60);
        rng_seed(9000 + i); /* independent of how much the world data drew from the rng */
        party[0].trait = i & 1 ? TR_KEEN_EYE : TR_SPORESKIN;
        side_mon(SIDE_ENEMY)->trait = TR_BRUISER;
        use_move(SIDE_ALLY, M_SWIPE);
        if (count_text("A perfect strike!")) {
            if (i & 1) crit_keen++;
            else crit_plain++;
        }
    }
    CHECK(crit_keen > crit_plain * 3 / 2 && crit_plain > 3, "KEEN EYE doubles the perfect-strike rate");

    /* QUICK STUDY and HOARDER */
    duel(SP_HOOTLORD, 20, SP_NIBBIT, 20);
    party[0].trait = TR_QUICK_STUDY;
    int qs = xp_share(0, 100);
    party[0].trait = TR_WAKEFUL;
    CHECK(qs == 120 && xp_share(0, 100) == 100, "QUICK STUDY earns 20% more XP");
    int finds = 0;
    rng_seed(123);
    for (int i = 0; i < 300; i++) {
        duel(SP_NIBBIT, 20, SP_ZAPPET, 5);
        party[0].trait = TR_HOARDER;
        int before = 0;
        for (int k = 0; k < ITEM_COUNT; k++) before += bag[k];
        battle_finish(BR_WIN);
        int after = 0;
        for (int k = 0; k < ITEM_COUNT; k++) after += bag[k];
        if (after > before) finds++;
    }
    CHECK(finds > 12 && finds < 60, "HOARDER finds an item after about 1 win in 10");
}

static void test_effects_and_bond(void)
{
    /* move effects */
    Monster a = monster_make(SP_GNAWLORD, 40), d = monster_make(SP_PUFFOWL, 40);
    int punish = move_power(M_HAUNT, &a, &d);
    d.status = STATUS_PSN;
    CHECK(move_power(M_HAUNT, &a, &d) == punish * 2, "PUNISH doubles against a statused foe");
    int desp_full = move_power(M_LAST_EMBER, &a, &d);
    a.hp = a.max_hp / 4;
    CHECK(move_power(M_LAST_EMBER, &a, &d) > desp_full * 2, "DESPERATE burns hotter at low HP");
    CHECK(move_power(M_BRIM_BURST, &a, &d) < MOVES[M_BRIM_BURST].power / 2, "BRIM weakens as HP drops");
    int hits_ok = 1;
    rng_seed(4);
    for (int i = 0; i < 30; i++) {
        duel(SP_VOLTLOPE, 40, SP_BOULDRON, 60);
        side_mon(SIDE_ENEMY)->trait = TR_BRUISER;
        use_move(SIDE_ALLY, M_PUMMEL);
        int n = count_events(EV_ANIM, SIDE_ALLY);
        if (n < 2 || n > 5) hits_ok = 0;
    }
    CHECK(hits_ok, "MULTI moves land 2 to 5 times, one animation each");
    duel(SP_DRAKORA, 50, SP_BOULDRON, 50);
    side_mon(SIDE_ENEMY)->trait = TR_BRUISER;
    party[0].moves[0] = M_STARFALL;
    for (int i = 0; i < 20 && battle.stages[SIDE_ALLY][STAT_SPA] == 0; i++) {
        side_mon(SIDE_ENEMY)->hp = side_mon(SIDE_ENEMY)->max_hp;
        battle.ev_count = 0;
        use_move(SIDE_ALLY, M_STARFALL);
    }
    CHECK(battle.stages[SIDE_ALLY][STAT_SPA] == -2, "SELF_DOWN harshly lowers the user's FOCUS");
    duel(SP_DANDELAMB, 30, SP_NIBBIT, 30);
    party[0].hp = 1;
    use_move(SIDE_ALLY, M_BASK);
    CHECK(party[0].hp == 1 + party[0].max_hp / 2, "HEAL restores half the user's HP");

    /* bond */
    duel(SP_FLARIX, 20, SP_NIBBIT, 5);
    party[0].bond = 100;
    battle_finish(BR_WIN);
    CHECK(party[0].bond == 102, "bond grows by 2 for every bout a kin takes part in");
    duel(SP_FLARIX, 20, SP_NIBBIT, 5);
    party[0].bond = 100;
    party[0].hp = 0;
    check_faint(SIDE_ALLY);
    CHECK(party[0].bond == 97, "bond falls by 3 when a kin dozes off");
    party[0].bond = 254;
    battle_finish(BR_LOSE);
    CHECK(party[0].bond == 255, "bond caps at 255");
    int held = 0;
    rng_seed(31);
    for (int i = 0; i < 200; i++) {
        duel(SP_NIBBIT, 5, SP_MAGMAUL, 60);
        party[0].bond = 220;
        party[0].trait = TR_HOARDER;
        party[0].hp = party[0].max_hp - 1;
        use_move(SIDE_ENEMY, M_BONK);
        if (party[0].hp == 1) held++;
    }
    CHECK(held > 6 && held < 45, "high bond sometimes holds on at 1 HP for you");
    duel(SP_FLARIX, 20, SP_NIBBIT, 5);
    party[0].bond = 220;
    party[0].trait = TR_SURGE;
    CHECK(xp_share(0, 100) == 110, "high bond earns 10% more XP");

    /* XP for the whole team: fighters full, bench half, dozing none */
    fresh_game();
    Monster m1 = monster_make(SP_FLARIX, 20), m2 = monster_make(SP_AQUAPO, 20), m3 = monster_make(SP_ZAPPET, 20);
    m1.trait = m2.trait = m3.trait = TR_SURGE;
    m1.bond = m2.bond = m3.bond = 70;
    give_monster(&m1);
    give_monster(&m2);
    give_monster(&m3);
    party[2].hp = 0;
    battle_start_wild(monster_make(SP_NIBBIT, 10));
    battle.ev_count = 0;
    int base = monster_xp_yield(side_mon(SIDE_ENEMY), 0);
    award_xp(side_mon(SIDE_ENEMY));
    int got[3] = { -1, -1, -1 };
    for (int i = 0; i < battle.ev_count; i++)
        if (battle.ev[i].type == EV_XP) got[battle.ev[i].a] = battle.ev[i].b;
    CHECK(got[0] == base && got[1] == base / 2 && got[2] == -1,
          "XP: the fighter gets it all, the bench half, dozing kin none");

    /* befriending gives XP and records where and when */
    fresh_game();
    Monster c = monster_make(SP_FLARIX, 30);
    give_monster(&c);
    u32 xp0 = party[0].xp;
    bag[ITEM_STAR_LANTERN] = 20;
    Monster target = monster_make(SP_PUFFOWL, 7);
    target.hp = 1;
    target.status = STATUS_SLP;
    target.flags = MF_LUSTROUS;
    battle_start_wild(target);
    battle_settle(3000);
    for (int k = 0; k < 10 && game_mode == MODE_BATTLE; k++) {
        battle_item_result(ITEM_STAR_LANTERN, 0);
        for (int f = 0; f < 900 && game_mode == MODE_BATTLE && battle.state != BST_ACTION; f++)
            step((f & 7) == 0 ? KEY_A : 0);
    }
    CHECK(party_count == 2 && party[0].xp > xp0, "befriending a kin gives XP");
    CHECK(party[1].met_map == (u8)cur_map && party[1].met_level == 7 && (party[1].flags & MF_LUSTROUS),
          "a befriended kin remembers where and at what level it was met, and stays lustrous");
}

static int hook_calls, hook_result;
static void test_hook(int result)
{
    hook_calls++;
    hook_result = result;
}

static void test_wardens_and_story(void)
{
    static const TrainerTeam birch = { "BIRCH", 2, { SP_THORNIP, SP_PUFFOWL, 0 }, { 6, 7, 0 }, 321,
                                       BSCENE_FOREST, "BIRCH: The woods chose you, it seems." };
    fresh_game();
    Monster m = monster_make(SP_MAGMAUL, 50);
    monster_replace_move(&m, 0, M_KILN_BREATH);
    give_monster(&m);
    battle_start_trainer_team(&birch);
    CHECK(battle.kind == BK_TRAINER && battle.team_count == 2 && battle.team[0].species == SP_THORNIP &&
          battle.team[1].level == 7 && battle.scene == BSCENE_FOREST && str_eq(battle.foe_title, "WARDEN BIRCH"),
          "battle_start_trainer_team sets up a warden's team, title and scene");
    battle_settle(3000);
    CHECK(battle.state == BST_ACTION, "a warden bout reaches the menu");
    int money0 = money;
    hook_calls = 0;
    battle_end_hook = test_hook;
    int saw_lose_line = 0, saw_intro = 0;
    for (int round = 0; round < 20 && game_mode == MODE_BATTLE; round++) {
        party[0].max_hp = party[0].hp = 999;
        battle.team[battle.team_idx].hp = 1;
        battle.state = BST_MOVES;
        battle.move_cursor = 0;
        tap(KEY_A);
        for (int f = 0; f < 1500 && game_mode == MODE_BATTLE && battle.state != BST_ACTION; f++) {
            if (battle.ev_count && battle.ev[0].type == EV_TEXT) {
                if (str_eq(battle.ev[0].text, birch.lose_line)) saw_lose_line = 1;
            }
            step((f & 7) == 0 ? KEY_A : 0);
        }
    }
    (void)saw_intro;
    CHECK(game_mode != MODE_BATTLE && money == money0 + 321 && saw_lose_line,
          "beating a warden pays the prize and they say their line");
    CHECK(hook_calls == 1 && hook_result == BR_WIN && battle_end_hook == 0,
          "the end hook runs once with the result, then clears");

    /* Marlo keeps working through the same code */
    fresh_game();
    give_monster(&m);
    battle_next_scene = BSCENE_LAKE;
    battle_start_trainer();
    CHECK(str_eq(battle.foe_title, "WARDEN MARLO") && battle.scene == BSCENE_RING && battle.team_count >= 2,
          "WARDEN MARLO fields a random team in the Bout Ring");
    battle_next_scene = BSCENE_MEADOW;

    /* wild bouts take their scene from the area */
    fresh_game();
    give_monster(&m);
    battle_next_scene = BSCENE_STORM;
    battle_start_wild(monster_make(SP_PYREFOX, 40));   /* not a legend: legends refuse with their own line */
    CHECK(battle.scene == BSCENE_STORM, "battle_next_scene picks the background");
    battle_next_scene = BSCENE_MEADOW;

    /* legends: their own intro, no running */
    fresh_game();
    give_monster(&m);
    battle_start_legend(monster_make(SP_DRAKORA, 40), BSCENE_LAIR);
    CHECK(battle.legend && battle.no_run && battle.scene == BSCENE_LAIR, "a legend bout sets legend, no_run and its lair");
    battle_queue_intro();
    CHECK(count_text("The legendary DRAKORA rises before you!") == 1 && battle.ev[1].type == EV_LEGEND,
          "a legend rears up and rises before you");
    battle.ev_count = 0;
    battle.no_run = 0;

    /* Hall Masters: title and banner */
    {
        static TrainerTeam hm;
        hm.name = "ODESSA";
        hm.count = 2;
        hm.species[0] = SP_PYREFOX; hm.level[0] = 20;
        hm.species[1] = SP_AXOLURK; hm.level[1] = 20;
        hm.prize = 1000;
        hm.scene = BSCENE_RING;
        hm.lose_line = "ODESSA: Well fought.";
        fresh_game();
        give_monster(&m);
        battle_start_master(&hm);
        CHECK(battle.master && str_eq(battle.foe_title, "HALL MASTER ODESSA"), "a Hall Master is titled HALL MASTER");
        battle_queue_intro();
        CHECK(battle.ev[0].type == EV_BANNER && str_eq(battle.ev[0].text, "HALL MASTER ODESSA") &&
              count_text("HALL MASTER ODESSA wants a bout!") == 1, "a Hall Master opens with the banner");
        battle.ev_count = 0;
        battle_settle(3000);
        CHECK(battle.state == BST_ACTION || battle.state == BST_MOVES, "a Hall Master bout reaches the menu");
    }
    fresh_game();
    give_monster(&m);
    battle_start_wild(monster_make(SP_PYREFOX, 40));

    /* story bouts: no running */
    battle.no_run = 1;
    hook_calls = 0;
    battle_end_hook = test_hook;
    battle_settle(3000);
    battle_try_run();
    CHECK(battle.result == BR_NONE && count_text("There's no running from this one!") == 1,
          "no_run refuses to let you run");
    battle_settle(2000);
    battle.result = BR_WIN;
    battle.state = BST_END;
    battle.timer = 16;
    step(0);
    CHECK(game_mode != MODE_BATTLE && hook_calls == 1 && battle.no_run == 0,
          "leaving a story bout calls the hook and clears no_run");

    /* L throws the best lantern in wild bouts */
    fresh_game();
    give_monster(&m);
    bag[ITEM_LANTERN] = 2;
    bag[ITEM_GLOW_LANTERN] = 1;
    battle_start_wild(monster_make(SP_NIBBIT, 5));
    battle_settle(3000);
    tap(KEY_L);
    CHECK(bag[ITEM_GLOW_LANTERN] == 0 && bag[ITEM_LANTERN] == 2, "L throws your best lantern");

    /* the move menu knows weak spots and resisted moves */
    duel(SP_FLARIX, 30, SP_DANDELAMB, 30);
    CHECK(move_tab(M_CINDER_FLICK) == BL_WEAK && move_tab(M_SWIPE) < 0, "move menu marks weak spots");
    duel(SP_FLARIX, 30, SP_AQUAPO, 30);
    CHECK(move_tab(M_CINDER_FLICK) == BL_RESIST, "move menu marks resisted moves");
    duel(SP_ZAPPET, 30, SP_GOLEMIT, 30);
    CHECK(move_tab(M_STATIC_POP) == BL_NONE && move_tab(M_TINGLE) == BL_NONE, "move menu marks moves with no effect");

    /* the move cursor is remembered per kin */
    fresh_game();
    Monster f = monster_make(SP_FLARIX, 30);
    give_monster(&f);
    battle_start_wild(monster_make(SP_NIBBIT, 30));
    battle_settle(3000);
    battle.move_cursor_of[0] = 2;
    battle.cursor = 0;
    tap(KEY_A);
    CHECK(battle.state == BST_MOVES && battle.move_cursor == 2, "FIGHT opens on the last move you chose");
}

static void test_animations_and_sound(void)
{
    duel(SP_FLARIX, 30, SP_GOLEMIT, 30);
    int ok = 1, ok_short = 0;
    for (int anims = 1; anims >= 0; anims--) {
        opt.battle_anims = (u8)anims;
        int all = 1;
        for (int mv = 0; mv <= M_LAST_GASP; mv++) {
            for (int side = 0; side < 2; side++) {
                anim_start(mv, side, HITF_LAST);
                int f = 0;
                while (anim_busy() && f < 400) {
                    oam_begin();
                    anim_update();
                    oam_end();
                    f++;
                }
                if (f >= 400 || (anims == 0 && f > 40)) {
                    all = 0;
                    printf("     animation of %s does not finish (%d frames)\n", MOVES[mv].name, f);
                }
            }
        }
        if (anims) ok = all;
        else ok_short = all;
    }
    opt.battle_anims = 1;
    CHECK(ok, "every move's animation finishes");
    CHECK(ok_short, "with animations off every move plays a short version");
    anim_clear();

    /* a hit shows its feedback: flash, squash and hit-stop */
    anim_start(M_HAYMAKER, SIDE_ALLY, HITF_LAST | HITF_CRIT);
    int flashed = 0, squashed = 0, stopped = 0;
    for (int f = 0; f < 200 && anim_busy(); f++) {
        oam_begin();
        anim_update();
        oam_end();
        if (feel.flash[SIDE_ENEMY]) flashed = 1;
        if (feel.sx[SIDE_ENEMY] != 256) squashed = 1;
        if (feel.hitstop) stopped = 1;
    }
    CHECK(flashed && squashed && stopped, "impacts flash, squash and freeze the target");

    /* sound */
    opt.sound = 1;
    sfx_stop_all();
    sfx_play(SFX_LEVEL_UP);
    int frames = 0;
    while (sfx_busy() && frames < 600) {
        sfx_update();
        frames++;
    }
    CHECK(frames > 10 && frames < 600 && (REG16(0x084) & 0x80), "sound effects play and finish");
    sfx_play(SFX_ITEM);
    sfx_play(SFX_TEXT);
    CHECK(sfx_ch[1].prio == 5, "a text blip never cuts a jingle short");
    opt.sound = 0;
    sfx_update();
    sfx_play(SFX_CONFIRM);
    CHECK(!sfx_busy() && !(REG16(0x080) & 0xFF00), "sound off silences every effect (music is separate)");
    opt.sound = 1;
    int all_end = 1;
    for (int id = 1; id < SFX_COUNT; id++) {
        sfx_stop_all();
        sfx_play(id);
        int n = 0;
        while (sfx_busy() && n < 600) {
            sfx_update();
            n++;
        }
        if (n >= 600) all_end = 0;
    }
    CHECK(all_end, "every sound effect ends");
    sfx_stop_all();
}

/* ---------------- balance ---------------- */

/* Headless battle with the game's own turn rules and AI. */
static int sim_battle(int a, int b, int level)
{
    party[0] = monster_make(a, level);
    party_count = 1;
    battle.team[0] = monster_make(b, level);
    battle.team_count = 1;
    battle.team_idx = 0;
    battle.ally = 0;
    battle.kind = BK_TRAINER;
    battle.result = BR_NONE;
    battle.turn = 0;
    battle.ally = 0;
    for (int s = 0; s < 2; s++) {
        battle.flinch[s] = 0;
        for (int i = 0; i < STAT_COUNT; i++) battle.stages[s][i] = 0;
    }
    battle.ev_count = 0;
    entry_traits(SIDE_ENEMY);
    entry_traits(SIDE_ALLY);
    for (int turn = 0; turn < 100; turn++) {
        battle.ev_count = 0;
        battle_take_turn(ai_choose_move(SIDE_ALLY));
        if (party[0].hp == 0 || battle.team[0].hp == 0) return party[0].hp > 0;
    }
    return party[0].hp * battle.team[0].max_hp >= battle.team[0].hp * party[0].max_hp;
}

static void tier_balance(const char *name, const int *tier, int n, int level, int lo, int hi)
{
    int ok = 1;
    rng_seed(20260926u);
    printf("     %s tier at Lv%d:\n", name, level);
    for (int i = 0; i < n; i++) {
        int wins = 0, games = 0;
        for (int j = 0; j < n; j++) {
            if (i == j) continue;
            for (int g = 0; g < 12; g++) {
                wins += sim_battle(tier[i], tier[j], level);
                wins += !sim_battle(tier[j], tier[i], level);
                games += 2;
            }
        }
        int pct = wins * 100 / games;
        printf("       %-10s %3d%%\n", SPECIES[tier[i]].name, pct);
        if (pct < lo || pct > hi) ok = 0;
    }
    char msg[96];
    snprintf(msg, sizeof(msg), "%s forms stay within a %d%%..%d%% overall win rate", name, lo, hi);
    CHECK(ok, msg);
}

/* ---- the whole roster, tiered by stage and rarity (docs/EXPANSION.md 3-4) ---- */

static int evolves_from_something(int sp)
{
    for (int s = 0; s < SP_COUNT; s++)
        if (SPECIES[s].evo_kind != EVO_NONE && SPECIES[s].evo_into == sp) return 1;
    return 0;
}

/* Round robin: every kin meets up to `opp` evenly spaced tier-mates,
 * `games` times from each side. Prints the kin outside [lo, hi]. */
static int sampled_tier(const char *name, const int *tier, int n, int level, int lo, int hi, int opp, int games)
{
    int ok = 1, worst_lo = 100, worst_hi = 0;
    rng_seed(0xBA1A2CEu);
    for (int i = 0; i < n; i++) {
        int wins = 0, played = 0;
        int k = opp < n - 1 ? opp : n - 1;
        for (int j = 1; j <= k; j++) {
            int o = tier[(i + j * (n - 1) / k) % n];
            if (o == tier[i]) continue;
            for (int g = 0; g < games; g++) {
                wins += sim_battle(tier[i], o, level);
                wins += !sim_battle(o, tier[i], level);
                played += 2;
            }
        }
        int pct = played ? wins * 100 / played : 50;
        if (pct < worst_lo) worst_lo = pct;
        if (pct > worst_hi) worst_hi = pct;
        if (pct < lo || pct > hi) {
            ok = 0;
            printf("       %-12s %3d%%  (%s tier, Lv%d)\n", SPECIES[tier[i]].name, pct, name, level);
        }
    }
    printf("     %s tier: %d kin at Lv%d, win rates %d%%..%d%%\n", name, n, level, worst_lo, worst_hi);
    return ok;
}

static void roster_balance(void)
{
    static int basic[SP_COUNT], final_[SP_COUNT], rare[SP_COUNT], fusion[SP_COUNT], legend[SP_COUNT];
    int nb = 0, nf = 0, nr = 0, nu = 0, nl = 0;
    for (int s = 0; s < SP_COUNT; s++) {
        const Species *sp = &SPECIES[s];
        int from = evolves_from_something(s), into = sp->evo_kind != EVO_NONE;
        switch (sp->rarity) {
        case R_LEGEND: legend[nl++] = s; break;
        case R_FUSION: fusion[nu++] = s; break;
        case R_RARE: if (!into) rare[nr++] = s; break;
        default:
            if (!from && into) basic[nb++] = s;
            if (!into) final_[nf++] = s;
            break;
        }
    }
    int ok = 1;
    ok &= sampled_tier("basic", basic, nb, 15, 20, 85, 64, 2);
    ok &= sampled_tier("final", final_, nf, 50, 20, 85, 64, 2);
    if (nr > 1) ok &= sampled_tier("rare", rare, nr, 50, 20, 85, 64, 2);
    if (nu > 1) ok &= sampled_tier("fusion", fusion, nu, 50, 20, 85, 64, 2);
    CHECK(ok, "the whole roster stays within a 20%..85% win rate in its tier");
    /* legends beat the regular finals most of the time */
    int weak = 0;
    rng_seed(0x1E6E2Du);
    for (int i = 0; i < nl; i++) {
        int wins = 0, played = 0;
        for (int j = 0; j < 8 && nf; j++) {
            int o = final_[(i * 7 + j * nf / 8) % nf];
            wins += sim_battle(legend[i], o, 50);
            wins += !sim_battle(o, legend[i], 50);
            played += 2;
        }
        if (played && wins * 100 / played < 55) {
            weak++;
            printf("       legend %-12s wins only %d%% against final forms\n", SPECIES[legend[i]].name,
                   wins * 100 / played);
        }
    }
    CHECK(nl > 0 && weak == 0, "every legend beats regular final forms most of the time");
}

static void test_balance(void)
{
    fresh_game();
    static const int BASIC[] = {
        SP_FLARIX, SP_AQUAPO, SP_DANDELAMB, SP_CINDERUB, SP_BUBBLIN, SP_THORNIP,
        SP_MOSSHELL, SP_ZAPPET, SP_VOLTUX, SP_GOLEMIT, SP_PUFFOWL, SP_SKYWISP, SP_NIBBIT,
    };
    static const int FINAL[] = {
        SP_INFERNOX, SP_TIDALOTL, SP_ZEPHRAM, SP_MAGMAUL, SP_GLACIBLOB, SP_BRAMBLOR,
        SP_TERRASHELL, SP_STORMHAWK, SP_VOLTLOPE, SP_BOULDRON, SP_HOOTLORD, SP_LUMOTH,
        SP_GNAWLORD, SP_WISPIRE,
    };
    tier_balance("basic", BASIC, (int)(sizeof(BASIC) / sizeof(BASIC[0])), 15, 30, 75);
    tier_balance("final", FINAL, (int)(sizeof(FINAL) / sizeof(FINAL[0])), 50, 30, 75);
    int legend = 0;
    for (int i = 0; i < 20; i++) legend += sim_battle(SP_DRAKORA, SP_GNAWLORD, 50);
    CHECK(legend >= 12, "the legendary DRAKORA beats a regular final form most of the time");
    roster_balance();
    party_count = 0;
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    test_data();
    test_monsters();
    test_battle_timing();
    test_battle_flow();
    test_learning_and_evolution();
    test_save();
    test_vocabulary();
    test_traits();
    test_effects_and_bond();
    test_wardens_and_story();
    test_animations_and_sound();
    test_balance();
    if (failures == 0) {
        printf("all game checks passed\n");
        return 0;
    }
    printf("%d check(s) FAILED\n", failures);
    return 1;
}
