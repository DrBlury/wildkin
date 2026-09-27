/* Story runtime checks on the E1/E2 base. E3/E6 NPC visibility and graph
 * checks are integration tests, not emulated by this harness. */
#include "harness.h"

/* Compile the E3-facing authored placements as metadata on the E1/E2 base;
 * runtime visibility and physical gating require E3 and E6 integration. */
typedef struct { int map, x, y, show, hide; } StoryPlacement;
#undef PERSON_IF
#undef PERSON
#define PERSON(map, x, y, chr, face, beh, scr, lore, name, text) \
    { map, x, y, 0, 0 }
#define PERSON_IF(map, x, y, chr, face, beh, scr, lore, name, text, show, hide) \
    { map, x, y, show, hide }
static const StoryPlacement STORY_PLACEMENTS[] = {
#include "../../src/game/world/story/npcs.inc"
};
#undef PERSON_IF
#undef PERSON

static void test_g1_metadata(void)
{
    int wood = 0, lake = 0, rival = 0, ok = 1;
    for (unsigned i = 0; i < sizeof(STORY_PLACEMENTS) / sizeof(STORY_PLACEMENTS[0]); i++) {
        const StoryPlacement *p = &STORY_PLACEMENTS[i];
        if (p->hide == FLAG_STORM_CALMED && !p->show) {
            if (p->map == MAP_WOOD && p->x == MAPS[MAP_WOOD].w - 1 &&
                (p->y == 17 || p->y == 18)) wood++;
            if (p->map == MAP_LAKE && p->x == 0 && (p->y == 31 || p->y == 32)) lake++;
        }
        if (p->show == FLAG_STARTER && p->hide == FLAG_SORREL_MAPLE) rival++;
        if (p->map >= MAP_COUNT || p->x < 0 || p->y < 0 ||
            p->x >= MAPS[p->map].w || p->y >= MAPS[p->map].h) ok = 0;
    }
    CHECK(wood == 2 && lake == 2, "both cells at each G1 road exit have a storm blocker");
    CHECK(rival == 1, "Sorrel appears in Maple only after Kindling and before their first win");
    CHECK(ok, "authored Act I NPC coordinates are within existing maps");
}

static void test_wires(void)
{
    fresh_game();
    CHECK(story_act() == 1, "Kindling begins in Act I");
    CHECK(!story_hearth_talk(), "no wire before the storm calms");
    flag_set(FLAG_STORM_CALMED);
    CHECK(story_act() == 2, "storm calm starts Act II");
    CHECK(story_hearth_talk() && flag(FLAG_STORY_WIRE_HOME), "Linden's east wire arrives once");
    CHECK(!story_hearth_talk(), "the east wire is not repeated");
    flag_set(FLAG_VOLT_CREST);
    CHECK(story_hearth_talk() && flag(FLAG_STORY_WIRE_VOLT), "Volt crest sends player home west");
    CHECK(!story_hearth_talk(), "Volt wire is not repeated");
    dialog_clear();

    fresh_game();
    flag_set(FLAG_STORM_CALMED);
    flag_set(FLAG_VOLT_CREST);
    flag_set(FLAG_TIDE_CREST);
    CHECK(story_hearth_talk() && flag(FLAG_STORY_WIRE_TIDE), "latest unread wire takes priority");
    CHECK(flag(FLAG_STORY_WIRE_HOME) && flag(FLAG_STORY_WIRE_VOLT), "obsolete wires are caught up silently");
    CHECK(!story_hearth_talk(), "older wires do not send player backward");
    dialog_clear();
}

static void test_sorrel(void)
{
    for (int i = 0; i < 3; i++) {
        fresh_game();
        Monster starter = monster_make(STARTER_SPECIES[i], 5);
        starter.met_map = MAP_LAB;
        give_monster(&starter);
        CHECK(story_rival_starter() == STARTER_SPECIES[(i + 1) % 3],
              "Sorrel picks the next starter in the strength triangle");
        party[0] = monster_make(SP_NIBBIT, 5);
        CHECK(story_rival_starter() == STARTER_SPECIES[(i + 1) % 3],
              "Sorrel remembers the chosen starter after the party changes");
    }
    fresh_game();
    flag_set(FLAG_STARTER);
    story_bout_flag = FLAG_SORREL_MAPLE;
    story_bout_end(BR_LOSE);
    CHECK(!flag(FLAG_SORREL_MAPLE), "losing does not remove Sorrel");
    story_bout_flag = FLAG_SORREL_MAPLE;
    story_bout_end(BR_WIN);
    CHECK(flag(FLAG_SORREL_MAPLE), "winning records Sorrel without opening a gate");
    CHECK(!flag(FLAG_STORM_CALMED), "Sorrel never opens G1");
}

static void test_teams_and_pacing(void)
{
    const int rivals[] = { TR_SORREL_MAPLE, TR_SORREL_MEADOW, TR_SORREL_BROOKMILL,
                            TR_SORREL_HARBOUR, TR_SORREL_FINALE };
    const int leads[] = { 5, 11, 15, 24, 46 };
    const int counts[] = { 1, 2, 3, 4, 6 };
    int ok = 1;
    for (int i = 0; i < 5; i++)
        if (TRAINERS[rivals[i]].level[0] != leads[i] || TRAINERS[rivals[i]].count != counts[i]) ok = 0;
    CHECK(ok, "Sorrel's roster grows at contract levels");
    CHECK(TRAINERS[TR_STILL_LUMEN].level[0] >= 18 &&
          TRAINERS[TR_STILL_LUMEN].level[1] <= 22 &&
          TRAINERS[TR_STILL_EMBER].level[0] >= 27 &&
          TRAINERS[TR_STILL_EMBER].level[2] <= 33,
          "early Husher and lieutenant teams fit route level bands");
    int max = 0;
    for (unsigned i = 0; i < NSLOT(WILD_RISE); i++)
        if (WILD_RISE[i].max_level > max) max = WILD_RISE[i].max_level;
    CHECK(max == 15, "Rise wild levels end at 15 in Act I");
}

static void test_encounters(void)
{
    static const struct { int map, trigger, win, trainer, script; } encounters[] = {
        { MAP_TOWN, FLAG_STARTER, FLAG_SORREL_MAPLE, TR_SORREL_MAPLE, SCR_STORY_SORREL },
        { MAP_MEADOW, FLAG_SASH, FLAG_SORREL_MEADOW, TR_SORREL_MEADOW, SCR_STORY_SORREL },
        { MAP_BROOKMILL_TRAIL, FLAG_STORM_CALMED, FLAG_SORREL_BROOKMILL, TR_SORREL_BROOKMILL, SCR_STORY_SORREL },
        { MAP_LUMEN, FLAG_STORM_CALMED, FLAG_STILL_LUMEN, TR_STILL_LUMEN, SCR_STORY_STILL },
        { MAP_SALTWIND, FLAG_VOLT_CREST, FLAG_STILL_SALTWIND, TR_STILL_SALTWIND, SCR_STORY_STILL },
        { MAP_PORT_BRINE, FLAG_VOLT_CREST, FLAG_SORREL_HARBOUR, TR_SORREL_HARBOUR, SCR_STORY_SORREL },
        { MAP_EMBER_TUNNEL, FLAG_TIDE_CREST, FLAG_STILL_EMBER, TR_STILL_EMBER, SCR_STORY_STILL },
        { MAP_GLIMMER_1, FLAG_CREST_ANVIL, FLAG_STILL_GLIMMER, TR_STILL_GLIMMER, SCR_STORY_STILL },
        { MAP_BARROW_A, FLAG_RIME_CREST, FLAG_STILL_BARROW, TR_STILL_VESTA, SCR_STORY_VESTA },
        { MAP_OSSUARY_1, FLAG_CREST_DREAM, FLAG_SORREL_FINALE, TR_SORREL_FINALE, SCR_STORY_SORREL },
    };
    fresh_game();
    for (unsigned k = 0; k < sizeof(encounters) / sizeof(encounters[0]); k++) {
        const int map = encounters[k].map;
        int found = 0, placement = -1, trainer = encounters[k].trainer;
        for (int n = 0; n < NPC_COUNT; n++) {
            const NpcDef *p = &NPCS[n];
            if (p->map != map || p->script != encounters[k].script ||
                p->show_flag != encounters[k].trigger || p->hide_flag != encounters[k].win) continue;
            found++;
            placement = n;
        }
        CHECK(found == 1, "encounter has one registered conditional NPC and win flag");
        CHECK(SCRIPT_FNS[encounters[k].script] != 0, "encounter script is dispatched");
        CHECK((encounters[k].script == SCR_STORY_SORREL ? story_rival_trainer_for(map) : story_still_trainer_for(map)) == trainer,
              "encounter dispatches its authored battle team");
        if (placement < 0) continue;
        const NpcDef *p = &NPCS[placement];
        map_load(map);
        CHECK(p->x >= 0 && p->y >= 0 && p->x < map_w && p->y < map_h &&
              !(cell_attr(p->x, p->y) & (A_SOLID | A_WATER | A_LEDGE)) &&
              item_ball_at(p->x, p->y) < 0, "encounter stands on passable, unoccupied ground");
        int clashes = 0;
        for (int n = 0; n < NPC_COUNT; n++)
            if (n != placement && NPCS[n].map == map && NPCS[n].x == p->x && NPCS[n].y == p->y) clashes++;
        CHECK(!clashes, "encounter does not overlap another NPC");
        int nearby = 0;
        flag_set(encounters[k].trigger);
        for (int n = 0; n < NPC_COUNT; n++)
            if (NPCS[n].map == map && npc_condition(&NPCS[n]) &&
                absi((int)NPCS[n].x - p->x) <= 8 &&
                absi((int)NPCS[n].y - p->y) <= 6) nearby++;
        CHECK(nearby <= 7, "encounter viewport keeps within seven NPC sprites");
        flag_set(encounters[k].trigger);
        CHECK(npc_condition(p), "encounter appears after the preceding story flag");
        flag_set(encounters[k].win);
        CHECK(!npc_condition(p), "encounter disappears after its own win");
        flag_clear(encounters[k].trigger);
        flag_clear(encounters[k].win);
        if (encounters[k].trigger)
            CHECK(!npc_condition(p), "encounter is absent before its preceding story flag");
        story_bout_flag = encounters[k].win;
        story_bout_end(BR_LOSE);
        CHECK(!flag(encounters[k].win), "a lost encounter is retryable");
        story_bout_flag = encounters[k].win;
        story_bout_end(BR_WIN);
        CHECK(flag(encounters[k].win), "a won encounter saves its stable completion flag");
        CHECK(!flag(FLAG_STORM_CALMED) && !flag(FLAG_VOLT_CREST) &&
              !flag(FLAG_TIDE_CREST) && !flag(FLAG_CREST_ANVIL) &&
              !flag(FLAG_RIME_CREST) && !flag(FLAG_LANTERN_CREST) &&
              !flag(FLAG_CREST_DREAM), "encounter wins cannot open a route gate");
        flag_clear(encounters[k].trigger);
        flag_clear(encounters[k].win);
    }
    int dream = 0;
    for (int n = 0; n < NPC_COUNT; n++)
        if (NPCS[n].map == MAP_DREAMSPIRE && NPCS[n].script == SCR_STORY_VESTA &&
            NPCS[n].show_flag == FLAG_LANTERN_CREST && NPCS[n].hide_flag == FLAG_CREST_DREAM) dream++;
    CHECK(dream == 1, "Vesta's reconciliation appears only during the Dream crest window");
    static const struct { int trainer, low, high; } bands[] = {
        { TR_STILL_LUMEN, 18, 22 }, { TR_STILL_SALTWIND, 19, 23 },
        { TR_STILL_EMBER, 27, 33 }, { TR_STILL_GLIMMER, 30, 37 },
        { TR_STILL_VESTA, 35, 40 },
    };
    for (unsigned k = 0; k < sizeof(bands) / sizeof(bands[0]); k++) {
        int in_band = 1;
        const TrainerDef *team = &TRAINERS[bands[k].trainer];
        for (int slot = 0; slot < team->count; slot++)
            if (team->level[slot] < bands[k].low || team->level[slot] > bands[k].high)
                in_band = 0;
        CHECK(in_band, "Stillwarden team stays within its act's level band");
    }
}

static void test_story_budgets(void)
{
    int locations = 1, collisions = 0, budget = 1;
    for (int map = 0; map < MAP_COUNT; map++) {
        int count = 0;
        for (int n = 0; n < NPC_COUNT; n++) {
            const NpcDef *p = &NPCS[n];
            if (p->map != map) continue;
            count++;
            if (p->x < 0 || p->y < 0 || p->x >= MAPS[map].w || p->y >= MAPS[map].h)
                locations = 0;
            for (int o = n + 1; o < NPC_COUNT; o++)
                if (NPCS[o].map == map && NPCS[o].x == p->x && NPCS[o].y == p->y &&
                    !((p->show_flag && NPCS[o].hide_flag == p->show_flag) ||
                      (NPCS[o].show_flag && p->hide_flag == NPCS[o].show_flag))) collisions++;
        }
        if (count > 24) budget = 0;
    }
    CHECK(locations, "all registered NPCs are in bounds");
    CHECK(!collisions, "NPC placements do not share live cells");
    CHECK(budget, "each map fits the 24-person definition budget");
}

int main(void)
{
    test_g1_metadata();
    test_wires();
    test_sorrel();
    test_teams_and_pacing();
    test_encounters();
    test_story_budgets();
    printf("story: %d failure(s)\n", failures);
    return failures ? 1 : 0;
}
