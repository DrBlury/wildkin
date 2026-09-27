/* Daily-event model checks; run by make test after E3/E10 and routes merge. */
#include "harness.h"
#include <string.h>

static void gameplay_checks(void)
{
    fresh_game();
    give_starter();
    flag_set(FLAG_RIME_CREST);
    for (int i = 0; i < REMATCH_COUNT; i++) trainer_mark_beaten(REMATCHES[i].trainer);
    gtime.day = 2;
    events_new_day_impl();
    int ready = 0, challenger = -1;
    for (int i = 0; i < REMATCH_COUNT; i++) if (events_rematch_ready(REMATCHES[i].trainer)) {
        ready++;
        challenger = REMATCHES[i].trainer;
    }
    CHECK(REMATCH_COUNT >= 35 && REMATCH_COUNT <= 64 && ready >= 3 && ready <= 5,
          "stable rematch table refreshes 3-5 beaten wardens in eight bytes");
    int first_win = trainer_beaten(challenger);
    int upgraded = events_rematch_level(challenger, 0);
    CHECK(upgraded > TRAINERS[challenger].level[0], "ready rematch gets upgraded team levels");
    CHECK(events_rematch_used(challenger) && !events_rematch_ready(challenger) &&
          !events_rematch_used(challenger) && trainer_beaten(challenger) == first_win,
          "winning consumes only readiness, not the first-win flag");
    events.rolled_day = gtime.day;
    static u8 sram[32768];
    CHECK(save_write_to(sram), "consumed rematch saved");
    new_game();
    CHECK(save_load_from(sram) == SAVE_VERSION && !events_rematch_ready(challenger) &&
          trainer_beaten(challenger), "consumed rematch remains consumed on reload");

    map_load(MAP_REST);
    scr_rematch_board(0);
    int board_opponent = rematch_challenger;
    CHECK(board_opponent != NO_TRAINER && events_rematch_ready(board_opponent),
          "rematch board offers a currently ready warden");
    dialog_clear();
    rematch_answer(0);
    CHECK(game_mode == MODE_BATTLE && battle.team[0].level ==
          events_rematch_level(board_opponent, 0),
          "board launches the upgraded team through the battle engine");
    game_mode = MODE_FIELD;
    battle_end_hook = 0;
    rematch_finished(BR_LOSE);
    CHECK(events_rematch_ready(board_opponent), "losing a board rematch preserves readiness");
    scr_rematch_board(0);
    dialog_clear();
    rematch_finished(BR_WIN);
    CHECK(!events_rematch_ready(board_opponent) && trainer_beaten(board_opponent),
          "winning a board rematch consumes only its daily readiness");
    map_load(CARAVAN_ROUTE[events.caravan_map].map);
    bag_add(ITEM_MINT_TEA, 1);
    int sale_money = money;
    caravan_answer(1);
    CHECK(money == sale_money + 1500 && bag[ITEM_MINT_TEA] == 0,
          "caravan buys one crafted HONEY DROP for a premium");
    caravan_answer(2);
    int destination = events.courier_target;
    CHECK(events.courier_pending && destination != events.caravan_map,
          "caravan offers an errand to the next reachable stop");
    gtime.day++;
    events_new_day_impl();
    map_load(CARAVAN_ROUTE[events.caravan_map].map);
    CHECK(events.caravan_map == destination && events.courier_pending,
          "courier stays pending while the caravan travels");
    int courier_money = money;
    caravan_answer(2);
    CHECK(!events.courier_pending && money == courier_money + 450,
          "delivering the parcel at the next stop pays a bounded reward");
    gtime.day = 13;
    events_new_day_impl();
    events.active[2] = EV_SURGE;
    WildSlot surge = { SP_NIBBIT, 10, 4, 8, WHEN_ANY };
    events_wild_override_impl(ZONE_MEADOW, &surge);
    CHECK(surge.min_level == 7 && surge.max_level == 11, "surge strengthens actual Meadow spawns");
    events.active[2] = EV_NONE;
    events.front_region = ER_HOME;
    events.front_kind = WX_STORM;
    map_load(MAP_MEADOW);
    WildSlot storm = { SP_ZAPPET, 10, 8, 10, WHEN_ANY };
    events_wild_override_impl(ZONE_MEADOW, &storm);
    CHECK(storm.min_level == 10 && storm.max_level == 12,
          "storm front levels up Spark or Gale encounters");
    events.active[2] = EV_METEOR;
    gtime.minute = 21 * 60;
    CHECK(events_active(EV_METEOR), "meteor event becomes visible at night");
    int meteor = 0;
    WildSlot sample = { SP_NIBBIT, 10, 9, 12, WHEN_ANY };
    for (int i = 0; i < 1000; i++) {
        sample.species = SP_NIBBIT;
        events_wild_override_impl(ZONE_RISE, &sample);
        meteor += sample.species == SP_METEORB;
    }
    CHECK(meteor > 0, "meteor night offers METEORB encounters");
    gtime.minute = 8 * 60;
    CHECK(!events_active(EV_METEOR), "meteor host vanishes after night");
    gtime.day = 14;
    events_new_day_impl();
    events.active[2] = EV_WASHOUT;
    int washout = 0;
    for (int i = 0; i < 100; i++) {
        sample.species = SP_NIBBIT;
        events_wild_override_impl(ZONE_BROOK_REEDS, &sample);
        washout += sample.species == SP_KOIRIN;
    }
    CHECK(washout > 0, "washout adds a rare water kin without closing a path");

    events.active[2] = EV_LOST_KIN;
    events.arg[3] = 0;
    gtime.day = 14;
    map_load(MAP_MEADOW);
    int keeper = -1, pet = -1;
    for (int i = 0; i < NPC_COUNT; i++) {
        if (NPCS[i].event == EV_LOST_KIN) keeper = i;
        if (NPCS[i].event == EV_LOST_KIN_PET) pet = i;
    }
    int coins = money;
    CHECK(keeper >= 0 && pet >= 0 && events_active(EV_LOST_KIN_PET),
          "Lost Kin spawns a visible route pet and keeper");
    scr_event_guest(keeper);
    CHECK(money == coins, "keeper does not pay before the pet is found");
    scr_event_guest(pet);
    CHECK(events.arg[3] == 1 && !events_active(EV_LOST_KIN_PET),
          "pet returns and disappears after contact");
    scr_event_guest(keeper);
    scr_event_guest(keeper);
    CHECK(money == coins + 250, "keeper pays only once after the reunion");

    events.active[2] = EV_TOURNEY;
    events.tourney_wins = 0;
    map_load(MAP_REST);
    int tonics = bag[ITEM_TONIC];
    tourney_answer(0);
    CHECK(game_mode == MODE_BATTLE && battle.team_count == TRAINERS[TR_LUCA].count &&
          battle.team[0].level > TRAINERS[TR_LUCA].level[0],
          "tourney starts a real upgraded trainer bout");
    game_mode = MODE_FIELD;
    battle_end_hook = 0;
    tourney_end(BR_LOSE);
    CHECK(events.tourney_wins == 0 && bag[ITEM_TONIC] == tonics,
          "losing a tourney bout gives no progress or prize");
    tourney_end(BR_WIN);
    tourney_end(BR_WIN);
    CHECK(events.tourney_wins == 2 && bag[ITEM_TONIC] == tonics,
          "tourney progress persists between the first two wins");
    CHECK(save_write_to(sram), "tourney ladder progress saves");
    new_game();
    CHECK(save_load_from(sram) == SAVE_VERSION && events.tourney_wins == 2 &&
          events.active[2] == EV_TOURNEY, "two tourney wins survive a reload");
    tourney_end(BR_WIN);
    tourney_end(BR_WIN);
    CHECK(events.tourney_wins == 3 && bag[ITEM_TONIC] == tonics + 1,
          "third tourney victory grants exactly one prize");
    gtime.day = 17;
    gtime.minute = 21 * 60;
    events_new_day_impl();
    events.active[2] = EV_NIGHT_MARKET;
    map_load(MAP_LUMEN);
    scr_event_market(0);
    CHECK(events_active(EV_NIGHT_MARKET) && game_mode == MODE_SHOP &&
          shop_stock_count == 3 && shop_stock[0] == ITEM_WAYSTONE,
          "Lumen's night-market trader opens its dedicated stock");
    game_mode = MODE_FIELD;
    gtime.minute = 8 * 60;
    CHECK(!events_active(EV_NIGHT_MARKET), "night-market stall closes by day");
    events.active[2] = EV_FISH_MARKET;
    map_load(MAP_PORT_BRINE);
    scr_event_market(0);
    CHECK(game_mode == MODE_SHOP && shop_stock_count == 3 &&
          shop_stock[0] == ITEM_SALT, "Port Brine fish market opens its stock");
    game_mode = MODE_FIELD;
    gtime.day = 1;
    events_new_day_impl();
    map_load(MAP_TOWN);
    int seeds = bag[ITEM_SUNSEED];
    scr_festival(0);
    scr_festival(0);
    CHECK(bag[ITEM_SUNSEED] == seeds + 1 && events.kindling_claimed,
          "Kindling host grants a SUNSEED once per year");
    events.courier_pending = 1;
    events.courier_target = 7;
    CHECK(save_write_to(sram), "festival and parcel state saved");
    new_game();
    CHECK(save_load_from(sram) == SAVE_VERSION && events.kindling_claimed &&
          events.courier_pending && events.courier_target == 7,
          "festival and courier state persist after reload");
    scr_festival(0);
    CHECK(bag[ITEM_SUNSEED] == seeds + 1, "festival cannot duplicate a reward after reload");
    SaveData legacy;
    memcpy(&legacy, sram, sizeof legacy);
    legacy.mod_size[6] = 0;
    legacy.checksum_v7 = save_checksum(&legacy);
    memcpy(sram, &legacy, sizeof legacy);
    memcpy(sram + SAVE_BACKUP_OFFSET, &legacy, sizeof legacy);
    new_game();
    CHECK(save_load_from(sram) == SAVE_VERSION && events.rolled_day == gtime.day &&
          events.festival == FEST_KINDLING && !events.courier_pending,
          "legacy save without event module deterministically rolls the saved day");
    CHECK(save_write_to(sram), "event module can be restored to migrated save");
    memcpy(&legacy, sram, sizeof legacy);
    legacy.mod_size[6] = 32; /* previous EventState prefix */
    legacy.checksum_v7 = save_checksum(&legacy);
    memcpy(sram, &legacy, sizeof legacy);
    memcpy(sram + SAVE_BACKUP_OFFSET, &legacy, sizeof legacy);
    new_game();
    CHECK(save_load_from(sram) == SAVE_VERSION && events.rolled_day == gtime.day &&
          events.festival == FEST_KINDLING && !events.courier_pending &&
          !events.kindling_claimed,
          "shorter event blob preserves the roll while new fields default safely");
    gtime.day = 41;
    events_new_day_impl();
    map_load(MAP_TOWN);
    int next_year_seeds = bag[ITEM_SUNSEED];
    scr_festival(0);
    scr_festival(0);
    CHECK(bag[ITEM_SUNSEED] == next_year_seeds + 1,
          "Kindling renews once in a later in-game year");
    for (int fest = FEST_MILLRACE; fest <= FEST_STARFALL; fest++) {
        static const int days[] = { 0, 1, 13, 27, 35, 10 };
        static const int maps[] = { MAP_NONE, MAP_TOWN, MAP_BROOKMILL,
                                    MAP_DUSKMERE, MAP_FROSTHOLLOW, MAP_RISE };
        static const int gifts[] = { 0, ITEM_SUNSEED, ITEM_WAYSTONE,
                                     ITEM_LANTERN, ITEM_MINT_TEA, ITEM_ASTRAL_SHARD };
        gtime.day = days[fest];
        gtime.minute = 21 * 60;
        events_new_day_impl();
        map_load(maps[fest]);
        int before_gift = bag[gifts[fest]];
        CHECK(events_active(EV_FEST_KINDLING + fest - FEST_KINDLING),
              "festival host condition matches the calendar");
        scr_festival(0);
        scr_festival(0);
        CHECK(bag[gifts[fest]] == before_gift + 1,
              "festival host rewards exactly once on the day");
    }
    gtime.day = 13;
    events_new_day_impl();
    events.active[2] = EV_LOST_KIN;
    events.arg[3] = 0;
    map_load(MAP_MEADOW);
    int coins_before = money;
    scr_event_guest(pet);
    scr_event_guest(keeper);
    map_load(MAP_BROOKMILL);
    int waystones_before = bag[ITEM_WAYSTONE];
    scr_festival(0);
    CHECK(money == coins_before + 250 && bag[ITEM_WAYSTONE] == waystones_before + 1 &&
          events.visit_claimed && events.festival_claimed,
          "festival and happening can each pay once on the same day");
    CHECK(save_write_to(sram), "overlapping event claims save");
    new_game();
    CHECK(save_load_from(sram) == SAVE_VERSION && events.visit_claimed &&
          events.festival_claimed, "overlapping event claims survive reload");
    gtime.day = 27;
    gtime.minute = 8 * 60;
    events_new_day_impl();
    CHECK(!events_active(EV_FEST_LANTERN), "Lantern host only appears at night");
    dialog_clear();
}

static void route_rematch_checks(void)
{
    fresh_game();
    give_starter();
    gtime.day = 9;
    events_new_day_impl();
    int rematch = -1, npc = -1;
    for (int r = 0; r < REMATCH_COUNT && npc < 0; r++)
        for (int i = 0; i < NPC_COUNT; i++)
            if (NPCS[i].trainer == REMATCHES[r].trainer && NPCS[i].script == SCR_WARDEN) {
                rematch = r;
                npc = i;
                break;
            }
    CHECK(npc >= 0, "a listed route rematch has a live warden NPC");
    if (npc < 0) return;
    int trainer = REMATCHES[rematch].trainer;
    trainer_mark_beaten(trainer);
    events.rematch_bits[rematch / 8] |= (u8)(1u << (rematch % 8));
    map_load(NPCS[npc].map);
    int upgraded = events_rematch_level(trainer, 0);
    script_warden(npc);
    CHECK(dialog_count >= 2 && dialog_q[(dialog_head + 1) % DIALOG_QUEUE].kind == DQ_CALL,
          "a beaten, ready route warden queues another challenge");
    dialog_clear();
    warden_battle(npc);
    CHECK(game_mode == MODE_BATTLE && battle.team[0].level == upgraded,
          "route rematch starts with the upgraded team");
    game_mode = MODE_FIELD;
    battle_end_hook = 0;
    warden_end(BR_LOSE);
    CHECK(events_rematch_ready(trainer) && trainer_beaten(trainer),
          "losing the route rematch keeps its first-win and daily-ready bits");
    warden_battle(npc);
    game_mode = MODE_FIELD;
    battle_end_hook = 0;
    warden_end(BR_WIN);
    CHECK(!events_rematch_ready(trainer) && trainer_beaten(trainer),
          "winning the route rematch consumes readiness without resetting the first win");
    dialog_clear();
}

static void budget_checks(void)
{
    int max_people = 0, event_people = 0;
    for (int map = 0; map < MAP_COUNT; map++) {
        int count = 0;
        for (int i = 0; i < NPC_COUNT; i++) if (NPCS[i].map == map) {
            count++;
            event_people += NPCS[i].event != EV_NONE;
        }
        if (count > max_people) max_people = count;
    }
    CHECK(sizeof(EventState) <= 64 && REMATCH_COUNT <= 64 && event_people <= 24,
          "event save and actor additions fit reserved capacities");
    CHECK(max_people <= 24, "every map fits 24 actor definitions at worst");
    int placed = 1;
    for (int i = 0; i < NPC_COUNT; i++) if (NPCS[i].event) {
        map_load(NPCS[i].map);
        if (NPCS[i].x >= map_w || NPCS[i].y >= map_h ||
            (cell_attr(NPCS[i].x, NPCS[i].y) & A_SOLID)) {
            printf("event actor blocked: %s on %s at %d,%d\n", NPCS[i].name,
                   MAPS[NPCS[i].map].name, NPCS[i].x, NPCS[i].y);
            placed = 0;
        }
    }
    CHECK(placed, "event actors stand on valid nonsolid cells");
    events.active[2] = EV_WASHOUT;
    const MapPatch *wash = events_washout_patch(MAP_BROOKMILL_TRAIL);
    CHECK(wash && !events_washout_patch(MAP_RISE),
          "washout patch API targets only Brookmill Trail");
    CHECK(wash[0].event == EV_WASHOUT && wash[0].x == 45 && wash[0].y == 25 &&
          wash[0].w == 1 && wash[0].h == 2 &&
          BROOK_TRAIL_ROWS[17][wash[0].x] == '=' &&
          BROOK_TRAIL_ROWS[25][wash[0].x] == 'R',
          "washout descriptor modifies only optional reeds below the route spine");
    events.rolled_day = gtime.day;
    events.active[2] = EV_NONE;
    map_load(MAP_BROOKMILL_TRAIL);
    CHECK(!(cell_attr(45, 25) & A_WATER), "optional reed crossing is dry without washout");
    events.active[2] = EV_WASHOUT;
    map_load(MAP_BROOKMILL_TRAIL);
    CHECK((cell_attr(45, 25) & A_WATER) && (cell_attr(45, 26) & A_WATER) &&
          !(cell_attr(45, 17) & (A_WATER | A_SOLID)),
          "washout floods only the side reeds and leaves the main road open");
    events.active[2] = EV_NONE;
    map_load(MAP_BROOKMILL_TRAIL);
    CHECK(!(cell_attr(45, 25) & A_WATER), "side reeds recover when the event ends");
}

int main(void)
{
    game_init();
    fresh_game();
    flag_set(FLAG_RIME_CREST); /* Exercise the full regional front rotation. */
    CHECK(sizeof(EventState) <= 64, "event save blob is at most 64 bytes");
    int different = 0, outbreaks = 0, weather = 0, caravan = 0;
    int stable = 1, gated = 1, short_lines = 1, validated = 1;
    EventState baseline;
    int happening_seen[EV_COUNT] = { 0 };
    for (int day = 1; day <= 1000; day++) {
        gtime.day = day;
        gtime.rain_days = 3;
        events.rolled_day = 0;
        events_new_day();
        baseline = events;
        if (events.active[2] < EV_COUNT) happening_seen[events.active[2]]++;
        events_new_day();
        stable &= !memcmp(&baseline, &events, sizeof events);
        gated &= events.caravan_map < CARAVAN_COUNT &&
                 CARAVAN_ROUTE[events.caravan_map].min_act <= events_act();
        if (events_active(EV_OUTBREAK)) {
            outbreaks++;
            gated &= OUTBREAKS[events_arg(EV_OUTBREAK)].min_act <= events_act();
        }
        if (events_active(EV_CARAVAN)) caravan++;
        if (events.front_kind > WX_RAIN) weather++;
        different += day > 1 && baseline.front_region != 0;
        for (int line = 0; line < 5; line++)
            short_lines &= strlen(events_gazette_line(line)) <= 30;
        events_validate();
        validated &= !memcmp(&baseline, &events, sizeof events);
    }
    int happening_coverage = 1;
    for (int kind = EV_LOST_KIN; kind <= EV_TALES; kind++)
        if (kind != EV_FESTIVAL) happening_coverage &= happening_seen[kind] > 0;
    CHECK(happening_coverage, "all rolled happenings recur within 1000 simulated days");
    CHECK(stable && validated, "same day and valid state never reroll");
    CHECK(gated, "no outbreak or caravan beyond current act");
    CHECK(short_lines, "all Gazette lines fit dialogue");
    CHECK(different > 0 && outbreaks > 0 && weather > 0 && caravan == 1000,
          "daily event kinds recur and move");
    gtime.day = 2;
    EventState before = events;
    before.rolled_day = 0;
    events = before;
    events_new_day();
    EventState first = events;
    events = before;
    events_new_day();
    CHECK(!memcmp(&first, &events, sizeof events), "same save seed and day reproduces the roll");
    CHECK(events_festival_for_day(1) == FEST_KINDLING &&
          events_festival_for_day(13) == FEST_MILLRACE &&
          events_festival_for_day(27) == FEST_LANTERN &&
          events_festival_for_day(35) == FEST_FROST &&
          events_festival_for_day(10) == FEST_STARFALL, "festival calendar");
    events.front_region = ER_COUNT;
    events_validate();
    CHECK(events.front_region < ER_COUNT && events.rolled_day == gtime.day, "corrupt state re-rolls");
    events.rolled_day = gtime.day;
    EventState saved = events;
    static u8 event_sram[32768];
    memset(event_sram, 0xFF, sizeof(event_sram));
    give_starter();
    CHECK(save_write_to(event_sram), "event state writes with the current save");
    new_game();
    CHECK(save_load_from(event_sram) == SAVE_VERSION &&
          !memcmp(&events, &saved, sizeof saved), "daily roll and caravan survive save and load");
    gameplay_checks();
    route_rematch_checks();
    budget_checks();
    if (failures) printf("%d event check(s) FAILED\n", failures);
    else printf("all event checks passed\n");
    return failures ? 1 : 0;
}
