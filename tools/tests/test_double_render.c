/* Four independent OBJ banks, HUDs, target selection, and actor reactions. */
#include "harness.h"

static const TrainerTeam first = {
    .name = "OAK", .count = 1, .species = { SP_PYREFOX }, .level = { 12 },
    .prize = 70, .scene = BSCENE_RING,
};
static const TrainerTeam second = {
    .name = "ASH", .count = 1, .species = { SP_AXOLURK }, .level = { 12 },
    .prize = 70, .scene = BSCENE_RING,
};

static int has_tile(int tile, int bank)
{
    for (int i = 0; i < oam_count; i++)
        if ((oam_shadow[i * 4 + 2] & 1023) == tile &&
            ((oam_shadow[i * 4 + 2] >> 12) & 15) == bank) return 1;
    return 0;
}

int main(void)
{
    fresh_game();
    Monster a = monster_make(SP_FLARIX, 15);
    Monster b = monster_make(SP_PUFFLEECE, 14);
    give_monster(&a);
    give_monster(&b);
    oam_shadow[0] = 32;
    oam_shadow[4] = 48;
    oam_shadow[8] = ATTR0_HIDE;
    battle_start_trainer_pair(&first, &second);
    CHECK(intro_field_oam_count == 2, "battle snapshots the two completed field sprites");
    oam_begin();
    battle_update();
    battle_draw();
    CHECK(battle.timer == 1 && oam_count == 2 && oam_shadow[0] == 32 &&
          oam_shadow[4] == 48, "first intro frame reuses field OAM without redrawing field sprites");
    oam_end();
    oam_begin();
    battle_update();
    battle_draw();
    CHECK(battle.timer == 2 && oam_count == 2,
          "dark wipe retains the field sprites on later frames");
    CHECK(battle.pair && battle.ally != battle.ally2, "pair has independent healthy ally slots");
    battle_queue_intro();
    int sent[4], sent_count = 0;
    for (int i = 0; i < battle.ev_count; i++)
        if (battle.ev[i].type == EV_SEND_OUT && sent_count < 4) sent[sent_count++] = battle.ev[i].side;
    CHECK(sent_count == 4 && sent[0] == SIDE_ENEMY && sent[1] == SIDE_ENEMY_2 &&
          sent[2] == SIDE_ALLY && sent[3] == SIDE_ALLY_2,
          "pair intro independently sends both foes and both allies");
    battle.ev_count = 0;
    battle_load_scene();
    for (int actor = 0; actor < BATTLE_ACTORS; actor++) {
        battle_load_mon_gfx(actor);
        disp_sync(actor);
        battle.disp[actor].visible = 1;
    }
    CHECK(memcmp(VRAM_OBJ_TILES + OT_MON_A * 8, mon_front_gfx[SP_PYREFOX], 64 * 32) == 0,
          "first foe has its own front tiles");
    CHECK(memcmp(VRAM_OBJ_TILES + OT_PAIR_FOE * 8, mon_front_gfx[SP_AXOLURK], 64 * 32) == 0,
          "second foe has its own front tiles");
    CHECK(memcmp(VRAM_OBJ_TILES + OT_MON_B * 8, mon_back_gfx[SP_FLARIX], 64 * 32) == 0,
          "first ally has its own back tiles");
    CHECK(memcmp(VRAM_OBJ_TILES + OT_PAIR_ALLY * 8, mon_back_gfx[SP_PUFFLEECE], 64 * 32) == 0,
          "second ally has its own back tiles");
    battle.state = BST_ACTION;
    battle.ui_dirty = battle.hud_dirty = 15;
    oam_begin();
    battle_draw();
    CHECK(has_tile(OT_MON_A, OBANK_MON_A) && has_tile(OT_MON_B, OBANK_MON_B) &&
          has_tile(OT_PAIR_FOE, OBANK_PAIR_FOE) && has_tile(OT_PAIR_ALLY, OBANK_PAIR_ALLY),
          "four different sprites occupy OAM simultaneously");
    for (int actor = 0; actor < BATTLE_ACTORS; actor++) {
        CHECK(battle.disp[actor].hp == side_mon(actor)->hp && battle.disp[actor].max_hp > 0,
              "actor HUD tracks its own kin HP");
    }
    u32 lower_hud_tile[8];
    memcpy(lower_hud_tile, &canvas[(13 * CANVAS_COLS + 26) * 8], sizeof(lower_hud_tile));
    battle.state = BST_MOVES;
    draw_move_box();
    battle.state = BST_TARGET;
    battle_redraw_ui();
    CHECK(memcmp(lower_hud_tile, &canvas[(13 * CANVAS_COLS + 26) * 8], sizeof(lower_hud_tile)) == 0,
          "switching menus preserves the second ally's HP plaque");
    pair_target = SIDE_ENEMY_2;
    pair_choice = 0;
    battle.state = BST_TARGET;
    keys_prev = keys_now = 0;
    keys_now = KEY_A;
    battle_update();
    CHECK(pair_choices[0].target == SIDE_ENEMY_2 && pair_choice == 1,
          "first ally can explicitly select the second foe");
    anim_start_target(M_BONK, SIDE_ENEMY_2, SIDE_ALLY_2, 0);
    CHECK(anim.side == SIDE_ENEMY_2 && anim.target == SIDE_ALLY_2,
          "animation carries source and target actor IDs");
    anim_impact_at(SIDE_ALLY_2, 0, side_cx(SIDE_ALLY_2), side_cy(SIDE_ALLY_2));
    CHECK(feel.flash[SIDE_ALLY_2] && !feel.flash[SIDE_ALLY] &&
          !feel.flash[SIDE_ENEMY] && !feel.flash[SIDE_ENEMY_2],
          "hit reaction flashes only the targeted secondary ally");
    anim_clear();
    bag[ITEM_TONIC] = 2;
    party[battle.ally2].hp -= 8;
    battle_item_result(ITEM_TONIC, battle.ally2);
    CHECK(pair_choices[1].kind == ACT_ITEM && pair_choices[1].item_target == battle.ally2,
          "second ally can queue an item for its own party slot");
    CHECK(bag[ITEM_TONIC] == 1 && party[battle.ally2].hp > battle.disp[SIDE_ALLY_2].hp - 8,
          "queued pair item resolves without spending the other ally's item");

    fresh_game();
    give_monster(&a);
    oam_shadow[0] = 72;
    oam_shadow[4] = ATTR0_HIDE;
    battle_start_trainer_team(&first);
    oam_begin();
    battle_update();
    battle_draw();
    CHECK(!battle.pair && battle.timer == 1 && oam_count == 1 && oam_shadow[0] == 72,
          "solo warden also enters via the stack-safe dark wipe");
    return failures ? 1 : 0;
}
