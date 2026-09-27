/* Event interaction scripts; the underlying day is rolled by E10. */
static void scr_gazette(int npc)
{
    (void)npc;
    for (int i = 0; i < 5; i++) dlg_say(events_gazette_line(i));
}
static void caravan_answer(int choice)
{
    if (!events_caravan_here(cur_map)) return;
    if (choice == 0) {
        static const u8 pool[] = { ITEM_TONIC, ITEM_LURE_INCENSE, ITEM_WAYSTONE,
            ITEM_SEED_MOTEBLOOM, ITEM_SEED_SNOWPEA, ITEM_MINT_TEA, ITEM_METAL_SHARD };
        static u8 stock[5];
        for (int i = 0; i < 4; i++) stock[i] = pool[(gtime.day + i + events.caravan_map) % NDEC(pool)];
        stock[4] = ITEM_ASTRAL_SHARD;
        shop_open_stock(stock, NDEC(stock));
    } else if (choice == 1) {
        if (bag[ITEM_MINT_TEA] == 0) { dlg_say("Bring a crafted HONEY DROP."); return; }
        bag_add(ITEM_MINT_TEA, -1);
        money = clampi(money + 1500, 0, 9999999);
        dlg_say("HONEY DROP bought for 1500!");
    } else if (choice == 2) {
        if (events.courier_pending) {
            if (events.caravan_map != events.courier_target) {
                dlg_say("Meet me at the next stop!"); return;
            }
            events.courier_pending = 0;
            money = clampi(money + 450, 0, 9999999);
            dlg_say("Parcel delivered! 450 coins.");
        } else {
            int next = (events.caravan_map + 1) % CARAVAN_COUNT;
            while (CARAVAN_ROUTE[next].min_act > events_act()) next = (next + 1) % CARAVAN_COUNT;
            if (next == events.caravan_map) {
                dlg_say("More stops open after the storm."); return;
            }
            events.courier_target = (u8)next;
            events.courier_pending = 1;
            dlg_say("Carry this parcel to my next stop!");
        }
    }
}
static void scr_caravan(int npc)
{
    (void)npc;
    if (!events_caravan_here(cur_map)) {
        dlg_say("The caravan moved. Check the Gazette."); return;
    }
    static const char *const choices[] = { "SHOP", "SELL HONEY DROP", "PARCEL", "LEAVE" };
    dlg_ask("MERRIWEATHER: Need anything?", choices, NDEC(choices), caravan_answer);
}
static int rematch_challenger = NO_TRAINER;
static void rematch_finished(int result)
{
    if (result == BR_WIN && rematch_challenger != NO_TRAINER)
        events_rematch_used(rematch_challenger);
    rematch_challenger = NO_TRAINER;
}
static void rematch_answer(int choice)
{
    if (choice || rematch_challenger == NO_TRAINER ||
        !events_rematch_ready(rematch_challenger)) return;
    if (party_first_healthy() < 0) { dlg_say("Heal your kin first!"); return; }
    static TrainerTeam team;
    team = team_from(&TRAINERS[rematch_challenger], BSCENE_AREA);
    for (int i = 0; i < team.count; i++)
        team.level[i] = (u8)events_rematch_level(rematch_challenger, i);
    set_battle_scene(MAPS[cur_map].scene);
    battle_end_hook = rematch_finished;
    battle_start_trainer_team(&team);
}
static void scr_rematch_board(int npc)
{
    (void)npc;
    dlg_say(events_gazette_line(4));
    rematch_challenger = NO_TRAINER;
    for (int i = 0; i < REMATCH_COUNT; i++) if (events_rematch_ready(REMATCHES[i].trainer)) {
        char line[40];
        str_copy(line, REMATCHES[i].name);
        str_put(line, " @ ");
        int map = REMATCHES[i].map;
        if (map == MAP_NONE)
            for (int j = 0; j < NPC_COUNT; j++)
                if (NPCS[j].trainer == REMATCHES[i].trainer) { map = NPCS[j].map; break; }
        if (map != MAP_NONE) {
            const char *place = MAPS[map].name;
            int length = str_len(line);
            while (*place && length < 30) line[length++] = *place++;
            line[length] = 0;
        } else str_put(line, "VALE");
        dlg_say(line);
        if (rematch_challenger == NO_TRAINER) rematch_challenger = REMATCHES[i].trainer;
    }
    if (rematch_challenger != NO_TRAINER) {
        static const char *const choices[] = { "CHALLENGE", "LATER" };
        dlg_ask("Challenge the first ready warden?", choices, NDEC(choices), rematch_answer);
    }
}
static void scr_festival(int npc)
{
    (void)npc;
    if (!events_active(EV_FESTIVAL)) return;
    static const char *const lines[] = {
        "", "KINDLING DAY: A new year!", "MILLRACE: Cheer the runners!",
        "LANTERN NIGHT: Follow lights.", "FROST FAIR: Welcome!", "STARFALL: Watch the sky!"
    };
    dlg_say(lines[events_arg(EV_FESTIVAL)]);
    if (events.festival != FEST_KINDLING && !events.festival_claimed) {
        static const u8 gifts[] = { 0, 0, ITEM_WAYSTONE, ITEM_LANTERN,
                                    ITEM_MINT_TEA, ITEM_ASTRAL_SHARD };
        static const u8 maps[] = { MAP_NONE, MAP_TOWN, MAP_BROOKMILL, MAP_DUSKMERE,
                                   MAP_FROSTHOLLOW, MAP_RISE };
        int gift = gifts[events.festival];
        if (cur_map == maps[events.festival] && bag[gift] < 999) {
            events.festival_claimed = 1;
            bag_add(gift, 1);
            dlg_say("A festival keepsake for you!");
        }
    }
    if (events.festival == FEST_KINDLING && cur_map == MAP_TOWN) {
        u16 year = (u16)((gtime.day - 1) / (SEASON_DAYS * SEASON_COUNT));
        if (events.kindling_year != year) events.kindling_claimed = 0;
        if (!events.kindling_claimed && bag[ITEM_SUNSEED] < 999) {
            events.kindling_year = year;
            events.kindling_claimed = 1;
            bag_add(ITEM_SUNSEED, 1);
            dlg_say("A free SUNSEED for the year!");
        }
    }
}
static void tourney_end(int result)
{
    if (result != BR_WIN || !events_active(EV_TOURNEY)) return;
    if (events.tourney_wins >= 3) return;
    events.tourney_wins++;
    if (events.tourney_wins == 3 && bag[ITEM_TONIC] < 999) {
        bag_add(ITEM_TONIC, 1);
        dlg_say("Three wins! Ring prize: TONIC!");
    }
}
static void tourney_answer(int choice)
{
    if (choice || !events_active(EV_TOURNEY) || events.tourney_wins >= 3) return;
    if (party_first_healthy() < 0) { dlg_say("Heal your kin first!"); return; }
    static const int challengers[] = { TR_LUCA, TR_MAE, TR_IDA };
    static TrainerTeam team;
    team = team_from(&TRAINERS[challengers[events.tourney_wins]], BSCENE_RING);
    for (int i = 0; i < team.count; i++)
        team.level[i] = (u8)clampi(team.level[i] + 5, 12 + events_act() * 3, 60);
    battle_end_hook = tourney_end;
    battle_start_trainer_team(&team);
}
static void scr_event_guest(int npc)
{
    if (NPCS[npc].event == EV_LOST_KIN_PET && events_active(EV_LOST_KIN_PET)) {
        events.arg[3] = 1;
        field_events_refresh();
        dlg_say("NIBBIT hurries back to its keeper!");
    } else if (events_active(EV_LOST_KIN) && cur_map == MAP_MEADOW) {
        if (!events.arg[3]) { dlg_say("Find my NIBBIT in the Meadow!"); return; }
        if (events_claim(EV_LOST_KIN, MAP_MEADOW)) {
            money = clampi(money + 250, 0, 9999999);
            dlg_say("My lost kin came home! 250 coins!");
        } else dlg_say("My kin is safe now. Thank you!");
    } else if (events_active(EV_TOURNEY) && cur_map == MAP_REST) {
        if (events.tourney_wins >= 3) dlg_say("The ring is quiet now.");
        else {
            static const char *const choices[] = { "BOUT", "LATER" };
            dlg_ask("Three ring bouts for a prize?", choices, NDEC(choices), tourney_answer);
        }
    } else if (events_active(EV_TALES) && cur_map == MAP_REST) {
        if (events_claim(EV_TALES, MAP_REST)) {
            lore_story(LORE_BOUT_RING);
            dlg_say("A tale of the old bout ring.");
        } else dlg_say("Tomorrow brings a new tale.");
    } else if (events_active(EV_METEOR) && cur_map == MAP_RISE) {
        if (events_claim(EV_METEOR, MAP_RISE)) {
            bag_add(ITEM_ASTRAL_SHARD, 1);
            dlg_say("A fallen ASTRAL SHARD!");
        } else dlg_say("The stars have gone quiet.");
    }
}
static void scr_event_market(int npc)
{
    (void)npc;
    static const u8 night_stock[] = { ITEM_WAYSTONE, ITEM_MINT_TEA, ITEM_LURE_INCENSE };
    static const u8 fish_stock[] = { ITEM_SALT, ITEM_TONIC, ITEM_WAYSTONE };
    if (cur_map == MAP_LUMEN && events_active(EV_NIGHT_MARKET))
        shop_open_stock(night_stock, NDEC(night_stock));
    else if (cur_map == MAP_PORT_BRINE && events_active(EV_FISH_MARKET))
        shop_open_stock(fish_stock, NDEC(fish_stock));
}
