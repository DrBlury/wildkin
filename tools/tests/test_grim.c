/*
 * W-GRIM checks: the Ashen March maps and their edge contracts, the Lantern
 * Crypt's dark maze (fake walls and ghost floors), HALL MASTER MORWEN and
 * the LANTERN crest, the Ossuary gate, OSSUREX on the Bone Throne, the
 * Hollowing story beats, the side quests and the MF_ASH haze that lifts
 * once OSSUREX is answered (grim_healed).
 */
#include "harness.h"

static int find_npc(int map, const char *name)
{
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].map == map && NPCS[i].name && strcmp(NPCS[i].name, name) == 0) return i;
    return -1;
}

/* Stand below (or beside) person `n`, face them and talk until the dialog ends. */
static void talk_to(int n)
{
    int x = NPCS[n].x, y = NPCS[n].y;
    static const s8 DX[4] = { 0, 0, -1, 1 }, DY[4] = { 1, -1, 0, 0 };
    field_enter_map(NPCS[n].map, x, y + 1, DIR_UP);
    for (int d = 0; d < 4; d++) {
        int px = x + DX[d], py = y + DY[d];
        if (cell_walkable(px, py)) {
            field_enter_map(NPCS[n].map, px, py, DIR_BACK[d]);
            break;
        }
    }
    npc_state[n].x = (s16)x;
    npc_state[n].y = (s16)y;
    dialog_clear();
    tap(KEY_A);
}

static void finish_battle(int result)
{
    battle.result = (u8)result;
    battle.state = BST_END;
    battle.timer = 16;
    for (int f = 0; f < 4 && game_mode == MODE_BATTLE; f++) step(0);
    run_dialog(3000);
}

static void run_until_battle(int limit)
{
    for (int f = 0; f < limit && game_mode != MODE_BATTLE; f++) step((f & 3) == 0 ? KEY_A : 0);
}

static int walkable_only(int map, int edge, int a, int b)
{
    map_load(map);
    int len = edge < 2 ? map_w : map_h;
    for (int k = 0; k < len; k++) {
        int x = edge < 2 ? k : (edge == LINK_W ? 0 : map_w - 1);
        int y = edge < 2 ? (edge == LINK_N ? 0 : map_h - 1) : k;
        int open = !(cell_attr(x, y) & (A_SOLID | A_WATER | A_LEDGE));
        if (open != (k >= a && k <= b)) return 0;
    }
    return 1;
}

static void test_maps(void)
{
    CHECK(walkable_only(MAP_ASHEN_FIELDS, LINK_N, 20, 21) && MAPS[MAP_ASHEN_FIELDS].link[LINK_N] == MAP_COPPERLINE,
          "ASHEN FIELDS opens north only at x 20-21, into COPPERLINE ROAD");
    CHECK(walkable_only(MAP_ASHEN_FIELDS, LINK_E, 20, 21) && walkable_only(MAP_GRAVEWOOD, LINK_W, 20, 21) &&
              walkable_only(MAP_GRAVEWOOD, LINK_E, 20, 21) && walkable_only(MAP_DUSKMERE, LINK_W, 20, 21),
          "the March's east-west edges open at y 20-21 on both sides");
    CHECK((MAPS[MAP_ASHEN_FIELDS].flags & MF_ASH) && (MAPS[MAP_GRAVEWOOD].flags & MF_ASH) &&
              (MAPS[MAP_DUSKMERE].flags & (MF_ASH | MF_TOWN)) == (MF_ASH | MF_TOWN),
          "the outdoor March maps carry MF_ASH; DUSKMERE is a town");
    CHECK((MAPS[MAP_LANTERN_CRYPT].flags & MF_DARK) && MAPS[MAP_LANTERN_CRYPT].tileset == TS_CRYPT &&
              MAPS[MAP_BONE_THRONE].tileset == TS_CRYPT,
          "the LANTERN CRYPT is dark, and the crypts use the crypt tileset");
    int fly = 0;
    for (int i = 0; i < FLY_POINT_COUNT; i++)
        if (FLY_POINTS[i].map == MAP_DUSKMERE) fly = 1;
    CHECK(fly, "DUSKMERE is a fly point");

    /* HOLLOW kin roam the March; levels rise from the fields to the deeps */
    int hollow = 0, rising = 1, prev = 0;
    static const u8 ZONES[] = { ZONE_ASHEN, ZONE_GRAVEWOOD, ZONE_OSSUARY, ZONE_OSSUARY_DEEP };
    for (unsigned z = 0; z < sizeof(ZONES); z++) {
        const WildZone *w = &WILD_ZONES[ZONES[z]];
        int lo = 255;
        for (int i = 0; i < w->count; i++) {
            const Species *s = &SPECIES[w->slots[i].species];
            if (s->type1 == T_HOLLOW || s->type2 == T_HOLLOW) hollow++;
            if (w->slots[i].min_level < lo) lo = w->slots[i].min_level;
            if (s->rarity == R_LEGEND || s->rarity == R_FUSION) rising = 0;
        }
        if (lo < prev) rising = 0;
        prev = lo;
    }
    CHECK(hollow >= 12 && rising, "HOLLOW kin fill the wild slots, levels rise toward the Ossuary, no legends or fusions");

    int teams = 1;
    for (int t = TR_ROOK; t <= TR_HESTER; t++)
        if (TRAINERS[t].count < 1 || TRAINERS[t].count > 6) teams = 0;
    CHECK(teams && TRAINERS[TR_MORWEN].count == 6, "grim wardens field 1-6 kin; MORWEN a full six");
}

static void test_crypt(void)
{
    /* the fake block is walkable, the ghost floor is solid, and they look alike */
    const TilesetDef *t = &TILESETS[TS_CRYPT];
    int same_look = 1;
    for (int q = 0; q < 4; q++) {
        if (t->meta_bottom[MT_CR_FAKE_BLOCK][q] != t->meta_bottom[MT_CR_BLOCK][q]) same_look = 0;
        if (t->meta_bottom[MT_CR_GHOST_FLOOR][q] != t->meta_bottom[MT_CR_FLOOR][q]) same_look = 0;
    }
    CHECK(same_look && !(t->attr[MT_CR_FAKE_BLOCK] & A_SOLID) && (t->attr[MT_CR_GHOST_FLOOR] & A_SOLID),
          "fake blocks look solid but aren't; ghost floors look open but aren't");

    int m = find_npc(MAP_LANTERN_CRYPT, "HALL MASTER MORWEN");
    map_load(MAP_LANTERN_CRYPT);
    CHECK(cell_attr(11, 22) & A_EXIT, "the LANTERN CRYPT door lands on its exit mat (11,22)");
    flood(11, 22);
    CHECK(m >= 0 && !reached_beside(NPCS[m].x, NPCS[m].y), "MORWEN's gates are shut until their switches are found");
    flood_ex(11, 22, FLOOD_SOLVED);   /* gates open, pads followed (test_puzzles plays the real thing) */
    CHECK(m >= 0 && reached_beside(NPCS[m].x, NPCS[m].y), "MORWEN can be reached through the maze");

    /* without walking through a false wall, the sanctum stays out of reach */
    static u8 saved[MAP_MAX_W * MAP_MAX_H];
    memcpy(saved, seen_cells, sizeof(saved));
    for (int i = 0; i < map_w * map_h; i++)
        if (map_cells[i] == MT_CR_FAKE_BLOCK) map_cells[i] = MT_CR_BLOCK;
    flood_ex(11, 22, FLOOD_SOLVED);
    CHECK(!reached_beside(NPCS[m].x, NPCS[m].y), "only a false wall leads to the sanctum");
}

static void test_story(void)
{
    fresh_game();
    give_starter();
    party[0].level = 45;
    party_heal_all();
    flag_set(FLAG_SASH);
    flag_set(FLAG_STORM_TOLD);
    flag_set(FLAG_STORM_CALMED);

    /* Keeper Linden sends you east after DRAKORA */
    int keeper = find_npc(MAP_LAB, "KEEPER LINDEN");
    for (int n = 0; n < 6 && !flag(FLAG_ASH_TOLD); n++) {
        talk_to(keeper);
        run_dialog(3000);
    }
    CHECK(flag(FLAG_ASH_TOLD) && quest_get(QUEST_HOLLOWING) >= 1 && lore_is_known(LORE_HOLLOWING),
          "after DRAKORA the Keeper tells you about the Hollowing");

    /* the haze: MF_ASH tints the palette until OSSUREX is answered */
    field_enter_map(MAP_DUSKMERE, 12, 13, DIR_DOWN);
    CHECK(quest_get(QUEST_HOLLOWING) >= 2, "reaching DUSKMERE moves the Hollowing on");
    u16 raw = TILESETS[TS_GRIM].palettes[0][3];
    CHECK(grim_ash_active(MAP_DUSKMERE) && bg_palette[3] == field_tint(grim_ash_tint(raw)) &&
              bg_palette[3] != raw,
          "the March is hazed with ash before OSSUREX is answered");
    field_enter_map(MAP_TOWN, 20, 20, DIR_DOWN);
    CHECK(!grim_ash_active(MAP_TOWN), "no ash outside the March");

    /* the gate stays shut without six crests */
    int gate = find_npc(MAP_DUSKMERE, "GATE WARDEN OSRIC");
    talk_to(gate);
    for (int f = 0; f < 3000 && (dialog_active() || warp.active); f++) step((f & 3) == 0 ? KEY_A : 0);
    CHECK(cur_map == MAP_DUSKMERE && !flag(FLAG_OSSUARY_OPEN), "the Ossuary gate stays shut without the crests");

    /* HALL MASTER MORWEN: a TT_MASTER bout for the LANTERN crest */
    int morwen = find_npc(MAP_LANTERN_CRYPT, "HALL MASTER MORWEN");
    talk_to(morwen);
    run_until_battle(2000);
    CHECK(game_mode == MODE_BATTLE && battle.kind == BK_TRAINER && battle.master &&
              battle.team_count == 6,
          "MORWEN fights a six-kin Hall Master bout");
    finish_battle(BR_WIN);
    CHECK(travel_has_crest(CREST_LANTERN) && flag(FLAG_LANTERN_CREST) && trainer_beaten(TR_MORWEN) &&
              lore_is_known(LORE_LANTERN_CRYPT),
          "beating MORWEN awards the LANTERN crest");

    /* with all six crests the gate warden opens the Ossuary */
    for (int c = 0; c < CREST_COUNT; c++) travel_award_crest(c);
    talk_to(gate);
    for (int f = 0; f < 3000 && cur_map != MAP_OSSUARY_1; f++) step((f & 3) == 0 ? KEY_A : 0);
    settle();
    CHECK(cur_map == MAP_OSSUARY_1 && flag(FLAG_OSSUARY_OPEN) && quest_get(QUEST_HOLLOWING) >= 4,
          "six crests open the Ossuary gate");

    /* OSSUREX on the Bone Throne */
    party_heal_all();
    field_enter_map(MAP_BONE_THRONE, BONE_THRONE_X + 1, BONE_THRONE_Y + 3, DIR_UP);
    dialog_clear();
    tap(KEY_A);
    run_until_battle(2000);
    CHECK(game_mode == MODE_BATTLE && battle.team[0].species == SP_OSSUREX && battle.no_run &&
              battle.team[0].level >= 50,
          "the Bone Throne wakes OSSUREX for a bout you can't run from");
    finish_battle(BR_LOSE);
    CHECK(!grim_healed(), "losing leaves OSSUREX brimming");
    party_heal_all();
    field_enter_map(MAP_BONE_THRONE, BONE_THRONE_X + 1, BONE_THRONE_Y + 3, DIR_UP);
    dialog_clear();
    tap(KEY_A);
    run_until_battle(2000);
    finish_battle(BR_WIN);
    CHECK(grim_healed() && quest_done(QUEST_HOLLOWING) && lore_is_known(LORE_ASH_GREEN) &&
              grim_legend_hidden(SP_OSSUREX),
          "answering OSSUREX heals the Ashen March");
    field_enter_map(MAP_ASHEN_FIELDS, 20, 2, DIR_DOWN);
    CHECK(!grim_ash_active(MAP_ASHEN_FIELDS) && bg_palette[3] == field_tint(TILESETS[TS_GRIM].palettes[0][3]),
          "the ash haze lifts once the March is healed");
    int surveyor = find_npc(MAP_ASHEN_FIELDS, "SURVEYOR ASH");
    CHECK(surveyor >= 0, "the surveyor waits at the edge of the ash");
}

static void test_quests(void)
{
    fresh_game();
    give_starter();

    /* the mourner's letter */
    int mourner = find_npc(MAP_GRAVEWOOD, "MOURNER");
    for (int n = 0; n < 6 && !flag(FLAG_LETTER_TAKEN); n++) {
        talk_to(mourner);
        run_dialog(3000);
    }
    CHECK(flag(FLAG_LETTER_TAKEN) && quest_get(QUEST_MIRE_LETTER) == 1, "the mourner hands you a letter");
    int brew = bag[ITEM_REVIVAL_BREW];
    talk_to(find_npc(MAP_DUSK_HOUSE, "WIDOW MAREN"));
    run_dialog(3000);
    CHECK(quest_done(QUEST_MIRE_LETTER) && bag[ITEM_REVIVAL_BREW] == brew + 2, "her sister thanks you for it");

    /* a BONE LANTERN for the ash farmer */
    int farmer = find_npc(MAP_ASHEN_FIELDS, "ASH FARMER");
    for (int n = 0; n < 6 && !quest_get(QUEST_ASH_LANTERN); n++) {
        talk_to(farmer);
        run_dialog(3000);
    }
    CHECK(quest_get(QUEST_ASH_LANTERN) == 1, "the ash farmer asks for a BONE LANTERN");
    bag_add(ITEM_BONE_LANTERN, 1);
    talk_to(farmer);
    run_dialog(3000);
    CHECK(quest_done(QUEST_ASH_LANTERN) && bag[ITEM_BONE_LANTERN] == 0 && bag[ITEM_SEED_PUMPKIN] >= 5,
          "and trades pumpkin seeds for it");

    /* the Dusk shop and the hearth */
    talk_to(find_npc(MAP_DUSK_SHOP, "CLERK"));
    for (int f = 0; f < 200 && game_mode != MODE_SHOP; f++) step((f & 7) == 0 ? KEY_A : 0);
    CHECK(game_mode == MODE_SHOP, "the DUSK SHOP opens its stock");
    for (int f = 0; f < 200 && game_mode == MODE_SHOP; f++) step((f & 7) == 0 ? KEY_B : 0);
    party[0].hp = 1;
    talk_to(find_npc(MAP_DUSK_HEARTH, "TENDER WREN"));
    run_dialog(3000);
    CHECK(party[0].hp == party[0].max_hp && (MAPS[MAP_DUSK_HEARTH].flags & MF_HEAL), "the Dusk Hearth rests your kin");

    /* ash falls outdoors in the March (one OBJ per flake) */
    field_enter_map(MAP_GRAVEWOOD, 5, 20, DIR_DOWN);
    CHECK(grim_ash_active(MAP_GRAVEWOOD), "ash falls in GRAVEWOOD");
}

/* Duskmere on its levels (docs/handoff/towns_north_grim.md) */
static void test_duskmere(void)
{
    map_load(MAP_DUSKMERE);
    field_load_tileset();
    int decor_ok = 1;
    for (int i = 0; i < MAPS[MAP_DUSKMERE].decor_count; i++)
        if (!decor_base[MAPS[MAP_DUSKMERE].decor[i].kind]) decor_ok = 0;
    CHECK(decor_ok, "DUSKMERE: every decor kind (lanterns, bell, graves...) fits the scene tiles");
    flood(0, 20);
    CHECK(reached_lv(33, 21, 1) && reached_lv(33, 21, 0),
          "DUSKMERE: the Long Walk crosses the gate yard on top; the lane runs under it");
    int gate = find_npc(MAP_DUSKMERE, "GATE WARDEN OSRIC");
    int gx = NPCS[gate].x, gy = NPCS[gate].y;
    CHECK(elev_floor(gx, gy) == 0 && reached_lv(gx + 1, gy, 0) && elev_floor(gx, gy - 7) == 2,
          "DUSKMERE: the Ossuary gate waits in the sunken yard under Lantern Hill");
    int chapel = -1;
    for (int i = 0; i < ITEM_BALL_COUNT; i++)
        if (ITEM_BALLS[i].map == MAP_DUSKMERE && ITEM_BALLS[i].item == ITEM_REVIVAL_BREW) chapel = i;
    CHECK(chapel >= 0 && reached_beside(ITEM_BALLS[chapel].x, ITEM_BALLS[chapel].y) && elev_hidden(36, 33),
          "DUSKMERE: the drowned chapel lies behind a hidden gap in the cypress");
    int back = -1;
    for (int i = 0; i < WARP_COUNT; i++)
        if (WARPS[i].map == MAP_OSSUARY_1 && WARPS[i].dest == MAP_DUSKMERE) back = i;
    CHECK(back >= 0 && cell_walkable(WARPS[back].dx, WARPS[back].dy) && elev_floor(WARPS[back].dx, WARPS[back].dy) == 0 &&
              absi(WARPS[back].dx - gx) + absi(WARPS[back].dy - gy) == 1,
          "DUSKMERE: climbing out of the Ossuary lands beside the gate warden");
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    test_maps();
    test_duskmere();
    test_crypt();
    test_story();
    test_quests();
    if (failures) {
        printf("%d grim check(s) FAILED\n", failures);
        return 1;
    }
    printf("all grim checks passed\n");
    return 0;
}
