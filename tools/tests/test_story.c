/* Story runtime checks on the E1/E2 base. E3/E6 NPC visibility and graph
 * checks are integration tests, not emulated by this harness. */
#include "harness.h"

/* Compile the E3-facing authored placements as metadata on the E1/E2 base;
 * runtime visibility and physical gating require E3 and E6 integration. */
typedef struct { int map, x, y, show, hide; } StoryPlacement;
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

int main(void)
{
    test_g1_metadata();
    test_wires();
    test_sorrel();
    test_teams_and_pacing();
    printf("story: %d failure(s)\n", failures);
    return failures ? 1 : 0;
}
