/* Whole-expansion acceptance; renamed to test_biome_integration.c at integration. */
#include "harness.h"

static const struct { const char *name; int route; } BIOME_EXPECTED[] = {
    { "MISTFALL GORGE", 1 }, { "MISTBELL", 0 }, { "MISTBELL BELLHOUSE", 0 },
    { "SAFFRON DUNES", 1 }, { "SUNWELL", 0 }, { "SUNWELL CISTERN", 0 },
    { "ROOTCOIL JUNGLE", 1 }, { "CANOPY HEARTH", 0 }, { "CANOPY LODGE", 0 },
    { "CORALHOOK REEF", 1 }, { "RIMEWIND TUNDRA", 1 }, { "SPORELIGHT HOLLOW", 1 }
};

static int biome_named_map(const char *name)
{
    for (int map = 0; map < MAP_COUNT; map++)
        if (MAPS[map].name && !strcmp(MAPS[map].name, name)) return map;
    return -1;
}

static void biome_battles(int map)
{
    int entered = 0;
    for (int n = 0; n < NPC_COUNT; n++) {
        if (NPCS[n].map != map || NPCS[n].trainer == NO_TRAINER) continue;
        fresh_game();
        give_starter();
        hush_steps = 2000;
        opt.text_speed = TEXT_FAST;
        int x = NPCS[n].x + DIR_DX[NPCS[n].facing];
        int y = NPCS[n].y + DIR_DY[NPCS[n].facing];
        field_enter_map(map, x, y, DIR_UP);
        int valid = x >= 0 && y >= 0 && x < map_w && y < map_h &&
                    !(cell_attr(x, y) & (A_SOLID | A_WATER)) && warden_sees(n);
        printf("warden: %s\n", TRAINERS[NPCS[n].trainer].name);
        CHECK(valid, "authored warden faces a real traversable approach");
        if (!valid || entered) continue;
        check_spotting();
        CHECK(spot.active && spot.npc == n, "route encounter spots the player on its authored approach");
        for (int f = 0; f < 400 && game_mode != MODE_BATTLE; f++)
            step((f & 7) == 0 ? KEY_A : 0);
        CHECK(game_mode == MODE_BATTLE && battle.kind == BK_TRAINER,
              "biome warden enters the real trainer battle flow");
        if (game_mode == MODE_BATTLE) {
            battle.result = BR_WIN;
            battle.state = BST_END;
            battle.timer = 16;
            for (int f = 0; f < 8 && game_mode == MODE_BATTLE; f++) step(0);
            CHECK(trainer_beaten(NPCS[n].trainer), "route victory records the authored trainer ID");
            run_dialog(200);
            CHECK(game_mode == MODE_FIELD && cur_map == map,
                  "battle completion restores the same biome field");
        }
        entered = 1;
    }
    CHECK(entered, "each biome route has a working battle encounter");
}

int main(void)
{
    fresh_game();
    give_starter();
    CHECK(MAP_COUNT < MAP_NONE && SCR_COUNT <= 256 && FLAG_COUNT <= FLAG_BYTES * 8 &&
          TRAINER_COUNT <= TRAINER_FLAG_BYTES * 8 && ITEM_BALL_COUNT <= ITEM_FLAG_BYTES * 8,
          "expanded world fits saved map, script, flag, trainer and satchel IDs");
    for (unsigned i = 0; i < sizeof(BIOME_EXPECTED) / sizeof(BIOME_EXPECTED[0]); i++) {
        int id = biome_named_map(BIOME_EXPECTED[i].name);
        printf("biome: %s\n", BIOME_EXPECTED[i].name);
        CHECK(id >= 0, "approved biome map is registered in the playable world");
        if (id < 0) continue;
        const MapDef *m = &MAPS[id];
        CHECK(!(m->flags & MF_DEBUG) && m->rows && m->w <= MAP_MAX_W && m->h <= MAP_MAX_H,
              "biome map is playable and within runtime dimensions");
        int inbound = 0, outbound = 0;
        for (int w = 0; w < WARP_COUNT; w++) {
            inbound += WARPS[w].dest == id;
            outbound += WARPS[w].map == id;
        }
        for (int side = 0; side < 4; side++) outbound += m->link[side] < MAP_COUNT;
        int exit_mat = 0;
        if (!outbound && inbound) {
            map_load(id);
            for (int y = 0; y < map_h; y++) for (int x = 0; x < map_w; x++)
                exit_mat |= (cell_attr(x, y) & A_EXIT) != 0;
        }
        CHECK(inbound > 0 && (outbound > 0 || exit_mat),
              "new destination has an authored entrance and a reciprocal portal or interior exit mat");
        if (BIOME_EXPECTED[i].route) {
            int trainers = 0;
            for (int n = 0; n < NPC_COUNT; n++)
                trainers += NPCS[n].map == id && NPCS[n].trainer != NO_TRAINER;
            CHECK((m->zone > ZONE_NONE || m->water_zone > ZONE_NONE) && trainers > 0,
                  "each biome route supports wild encounters and authored trainer fights");
            biome_battles(id);
        }
    }
    return failures ? 1 : 0;
}
