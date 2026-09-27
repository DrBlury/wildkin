/* Saga content and save-backed progression checks. Host build: cc -std=c11
 * -O0 -o /tmp/test_saga tools/tests/test_saga.c (after base art/regions build). */
#include "harness.h"

static void test_quests(void)
{
    CHECK(QUEST_COUNT <= QUEST_MAX, "saga quest ids fit the save");
    for (int q = QUEST_PROJECT_TRAM; q <= QUEST_FIELD_NOTES; q++) {
        const QuestDef *def = &QUESTS[q];
        CHECK(def->name && def->goal && def->n_stages > 1, "saga quest has goals");
        for (int stage = 1; stage < def->n_stages; stage++) {
            if (!def->stage_goals[stage] || !def->stage_goals[stage][0] ||
                def->stage_maps[stage] >= MAP_COUNT) {
                printf("  quest %s stage %d has no goal/real map\n", def->name, stage);
                failures++;
            }
        }
    }
    for (int i = 0; i < SAGA_PROJECT_COUNT; i++)
        CHECK(QUESTS[saga_projects[i].quest].category == QUEST_PROJECT &&
              saga_projects[i].price > 0 && saga_projects[i].flag < FLAG_COUNT,
              "project has a valid category, cost and done flag");
}

static void test_notes(void)
{
    fresh_game();
    CHECK(NOTE_COUNT <= 32, "note ids fit two save-backed bitsets");
    for (int i = 0; i < NOTE_COUNT; i++) {
        const SagaNote *n = &saga_notes[i];
        if (n->map == MAP_NONE || n->map >= MAP_COUNT || n->x >= MAPS[n->map].w ||
            n->y >= MAPS[n->map].h || n->ability > SAGA_TELEPORT) {
            printf("  invalid note %s\n", n->name); failures++;
        }
    }
    for (int i = 0; i < NOTE_COUNT; i++) {
        const SagaNote *n = &saga_notes[i];
        map_load(n->map);
        int near = 0;
        for (int d = 0; d < 4; d++) {
            int x = n->x + DIR_DX[d], y = n->y + DIR_DY[d];
            if (x >= 0 && x < map_w && y >= 0 && y < map_h &&
                !(cell_attr(x, y) & (A_SOLID | A_LEDGE)) &&
                (!(cell_attr(x, y) & A_WATER) || n->ability == SAGA_SURF)) near++;
        }
        if (!near) { printf("  note %s has no walkable approach\n", n->name); failures++; }
    }
    CHECK(!saga_note_bit(NOTE_WOOD_LOG, 0) && !saga_note_bit(NOTE_LAKE_ISLET, 0),
          "unvisited note locations stay hidden");
    saga_entered(MAP_WOOD);
    CHECK(saga_note_bit(NOTE_WOOD_LOG, 0) && saga_note_bit(NOTE_WOOD_FOG, 0),
          "entering an old map records its ability-secret hints");
    saga_note(NOTE_WOOD_LOG, 0);
    CHECK(saga_note_bit(NOTE_WOOD_LOG, 0) && !saga_note_bit(NOTE_WOOD_LOG, 3), "examining a spot records it unsolved");
    saga_note(NOTE_WOOD_LOG, 1);
    CHECK(saga_note_bit(NOTE_WOOD_LOG, 3), "solving a secret updates its note");
    QuestState persisted = quest;
    quest_reset();
    CHECK(!saga_note_bit(NOTE_WOOD_LOG, 0), "legacy zero-initialized notes are empty");
    quest = persisted;
    CHECK(saga_note_bit(NOTE_WOOD_LOG, 0) && saga_note_bit(NOTE_WOOD_LOG, 3), "note bits survive save state copy");
    CHECK(!saga_note_bit(NOTE_LAKE_ISLET, 0), "other regions remain hidden after discovery");
    give_starter();
    CHECK(save_write(), "save stores saga notes in quest module");
    new_game();
    CHECK(save_load() == SAVE_VERSION && saga_note_bit(NOTE_WOOD_LOG, 3),
          "saved saga notes load with current layout");
}

static void test_notes_ui(void)
{
    fresh_game();
    quest_log_open();
    CHECK(game_mode == MODE_EXT && qlog.state == 0 && qlog.count == 0,
          "empty quest log opens without auto-starting notes");
    tap(KEY_SELECT);
    CHECK(qlog.state == 2 && qlog.note_ability == SAGA_LIGHT &&
          qlog_note_count(SAGA_LIGHT) == 0, "SELECT opens an empty FIELD NOTES page");
    tap(KEY_RIGHT);
    CHECK(qlog.note_ability == SAGA_SURF, "right moves to the SURF group");
    tap(KEY_LEFT);
    CHECK(qlog.note_ability == SAGA_LIGHT, "left returns to the LIGHT group");
    tap(KEY_B);
    CHECK(qlog.state == 0, "B returns from notes to the quest list");
    tap(KEY_B);
    CHECK(game_mode == MODE_FIELD, "B closes the quest log as before");

    saga_entered(MAP_COPPER_MINE);
    CHECK(qlog_note_count(SAGA_LIGHT) == 1 &&
          !strcmp(qlog_note_status(NOTE_MINE_LIGHT), "LOCKED"),
          "visited mine note is visible but locked without the crest");
    int spot = map_spot(MAP_COPPER_MINE);
    CHECK(spot >= 0 && !wm_note_marker(spot), "locked note has no town-map marker");
    flag_set(FLAG_VOLT_CREST);
    CHECK(!strcmp(qlog_note_status(NOTE_MINE_LIGHT), "READY") && wm_note_marker(spot),
          "crest makes a recorded unfinished note READY with a map marker");
    CHECK(!saga_note_bit(NOTE_LAKE_ISLET, 0) &&
          !wm_note_marker(map_spot(MAP_LAKE)), "hidden notes have no marker");
    quest_log_open();
    CHECK(qlog.count && qlog.ids[qlog.cursor] == QUEST_FIELD_NOTES,
          "discovery registers FIELD NOTES in ordinary quest state");
    tap(KEY_A);
    CHECK(qlog.state == 2 && qlog_note_count(SAGA_LIGHT) == 1,
          "A on FIELD NOTES opens its grouped page");
    flag_set(FLAG_MINE_LIGHT_CACHE);
    saga_notes_sync();
    CHECK(!strcmp(qlog_note_status(NOTE_MINE_LIGHT), "DONE") && !wm_note_marker(spot),
          "existing regional solved flag completes the note and clears its marker");
    give_starter();
    CHECK(save_write(), "completed field note saves");
    new_game();
    CHECK(save_load() == SAVE_VERSION && saga_note_bit(NOTE_MINE_LIGHT, 3) &&
          !strcmp(qlog_note_status(NOTE_MINE_LIGHT), "DONE"),
          "FIELD NOTES completion reloads from the save");
}

static void test_projects(void)
{
    fresh_game();
    flag_set(FLAG_VOLT_CREST);
    saga_project_offer(SAGA_TRAM);
    CHECK(saga_project_state(SAGA_TRAM) == 1 && saga_project_state(SAGA_BRIDGE) == 0,
          "tram offered after Volt, bridge unavailable before Anvil");
    money = 2999; bag[ITEM_IRON_ORE] = 5; saga_pending_project = SAGA_TRAM;
    saga_project_answer(0);
    CHECK(saga_project_state(SAGA_TRAM) == 1 && bag[ITEM_IRON_ORE] == 5,
          "insufficient funds never consume ore");
    money = 3000; saga_project_answer(0);
    CHECK(saga_project_state(SAGA_TRAM) == 2 && bag[ITEM_IRON_ORE] == 0 && money == 0,
          "paid tram consumes exact resources once");
    saga_project_new_day();
    CHECK(saga_project_state(SAGA_TRAM) == 2, "paid project does not finish on the same day");
    give_starter();
    CHECK(save_write(), "paid project saves before dawn");
    new_game();
    CHECK(save_load() == SAVE_VERSION && saga_project_state(SAGA_TRAM) == 2,
          "paid project loads without completing prematurely");
    saga_project_answer(0);
    CHECK(money == 0 && bag[ITEM_IRON_ORE] == 0, "project cannot be paid twice");
    QuestState persisted = quest;
    quest_reset(); quest = persisted;
    ++gtime.day;
    saga_project_new_day();
    CHECK(saga_project_state(SAGA_TRAM) == 3 && flag(FLAG_PROJECT_TRAM) &&
          quest_done(QUEST_PROJECT_TRAM), "next dawn completes project even after a save round-trip");
    saga_project_new_day();
    CHECK(saga_project_state(SAGA_TRAM) == 3, "completed project remains complete");
    flag_set(FLAG_CREST_ANVIL);
    saga_project_offer(SAGA_BRIDGE);
    bag[ITEM_IRON_ORE] = 4; bag[ITEM_COAL] = 2; money = 4000;
    saga_pending_project = SAGA_BRIDGE; saga_project_answer(0);
    ++gtime.day; saga_project_new_day();
    CHECK(flag(FLAG_PROJECT_CINDER_BRIDGE), "bridge flag opens the existing Cinder map patch");
}

static void test_courier(void)
{
    fresh_game();
    scr_saga_elspeth(0);
    CHECK(!quest_get(QUEST_VALE_COURIER), "courier cannot start before the Volt boardwalk");
    flag_set(FLAG_VOLT_CREST);
    scr_saga_elspeth(0);
    CHECK(quest_is(QUEST_VALE_COURIER, 1), "Elspeth starts the Brookmill delivery");
    scr_saga_miller(0);
    CHECK(quest_is(QUEST_VALE_COURIER, 2), "miller's reply returns to Reedwick");
    scr_saga_elspeth(0);
    scr_saga_telegraph(0);
    CHECK(quest_is(QUEST_VALE_COURIER, 4), "Lumen clerk accepts mail without mandatory tram");
    quest_set(QUEST_VALE_COURIER, 12);
    scr_saga_elspeth(0);
    CHECK(quest_done(QUEST_VALE_COURIER) && flag(FLAG_COURIER_REUNITED) &&
          bag[ITEM_COURIER_SATCHEL] == 1, "courier reunion and satchel reward happen once");
    scr_saga_elspeth(0);
    CHECK(bag[ITEM_COURIER_SATCHEL] == 1, "courier reward cannot be duplicated");
}

static void test_survey_and_legends(void)
{
    fresh_game();
    for (int region = 0; region < 6; region++) {
        int met, total;
        saga_survey_count(region, &met, &total);
        if (total < 6 || met != 0) { printf("  survey region %d has %d native kin, %d met\n", region, total, met); failures++; }
        int species = WILD_ZONES[MAPS[saga_survey_maps[region][0]].zone].slots[0].species;
        dex_seen[species] = 1;
        saga_survey_count(region, &met, &total);
        CHECK(met >= 1, "wild sighting counts toward the appropriate region");
        dex_seen[species] = 0;
    }
    CHECK(saga_legend_count() < 8, "legend trail cannot complete before reading the lore");
    for (int i = 0; i < 8; i++) lore_learn(saga_legend_pages[i]);
    CHECK(saga_legend_count() == 8, "book recognizes all eight legend lore entries");
}

static void test_shortcuts(void)
{
    const struct { int map, x, y; } landings[] = {
        { MAP_TOWN, 12, 17 }, { MAP_BROOKMILL, 31, 29 }, { MAP_LUMEN, 36, 20 },
        { MAP_LAKE, 31, 17 }, { MAP_REEDWICK, 25, 20 },
        { MAP_FOOTHILLS, 11, 52 }, { MAP_TIMBERLINE, 11, 30 }
    };
    fresh_game();
    for (unsigned i = 0; i < sizeof(landings) / sizeof(landings[0]); i++) {
        map_load(landings[i].map);
        if ((cell_attr(landings[i].x, landings[i].y) & (A_SOLID | A_WATER | A_LEDGE)) ||
            npc_at(landings[i].x, landings[i].y) >= 0) {
            printf("  shortcut landing blocked on map %d at %d,%d\n",
                   landings[i].map, landings[i].x, landings[i].y); failures++;
        }
    }
    int bridge_guides = 0;
    for (int i = 0; i < NPC_COUNT; i++)
        bridge_guides += NPCS[i].map == MAP_CINDER_CROSSING && NPCS[i].script == SCR_SAGA_BRIDGE_PASS;
    CHECK(bridge_guides == 2, "Cinder bridge has reversible fallback guides while its map patch is pending");
    map_load(MAP_CINDER_CROSSING);
    CHECK(!(cell_attr(4, 21) & (A_SOLID | A_WATER | A_LEDGE)) &&
          !(cell_attr(11, 21) & (A_SOLID | A_WATER | A_LEDGE)),
          "Cinder crossing fallback lands on both safe banks");
}

static void test_people(void)
{
    fresh_game();
    for (int i = 0; i < NPC_COUNT; i++) {
        if (NPCS[i].script < SCR_SAGA_HOLT || NPCS[i].script > SCR_SAGA_BRIDGE_PASS) continue;
        const NpcDef *n = &NPCS[i];
        map_load(n->map);
        int valid = n->x < map_w && n->y < map_h &&
            !(cell_attr(n->x, n->y) & (A_SOLID | A_WATER | A_LEDGE));
        int neighbour = 0, overlap = 0;
        for (int d = 0; d < 4; d++) {
            int x = n->x + DIR_DX[d], y = n->y + DIR_DY[d];
            if (x >= 0 && x < map_w && y >= 0 && y < map_h &&
                !(cell_attr(x, y) & (A_SOLID | A_WATER | A_LEDGE))) neighbour++;
        }
        for (int j = 0; j < NPC_COUNT; j++)
            if (j != i && NPCS[j].map == n->map && NPCS[j].x == n->x && NPCS[j].y == n->y &&
                (n->show_flag == NPCS[j].show_flag && n->hide_flag == NPCS[j].hide_flag)) overlap++;
        if (!valid || !neighbour || overlap) {
            printf("  saga actor %s map %d at %d,%d: cell %d neighbors %d overlap %d\n",
                   n->name, n->map, n->x, n->y, valid, neighbour, overlap);
            failures++;
        }
    }
    CHECK(1, "saga people placement inspected on loaded maps");
}

int main(void)
{
    test_quests(); test_notes(); test_notes_ui(); test_projects(); test_courier(); test_survey_and_legends(); test_shortcuts(); test_people();
    printf("saga: %d failure(s)\n", failures);
    return failures ? 1 : 0;
}
