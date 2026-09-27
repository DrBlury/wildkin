/* Saga content is compiled into script.c's unified translation unit. */
typedef struct { int quest, flag, gate, item_a, qty_a, item_b, qty_b, price; } SagaProject;
static const SagaProject saga_projects[] = {
    { QUEST_PROJECT_TRAM, FLAG_PROJECT_TRAM, FLAG_VOLT_CREST, ITEM_IRON_ORE, 5, 0, 0, 3000 },
    { QUEST_PROJECT_BRIDGE, FLAG_PROJECT_CINDER_BRIDGE, FLAG_CREST_ANVIL, ITEM_IRON_ORE, 4, ITEM_COAL, 2, 4000 },
    { QUEST_PROJECT_LIFT, FLAG_PROJECT_LIFT, FLAG_RIME_CREST, ITEM_SAGA_TIMBER, 6, 0, 0, 2500 },
    { QUEST_PROJECT_FERRY, FLAG_PROJECT_REED_FERRY, 0, ITEM_SAGA_TIMBER, 4, ITEM_SALT, 2, 2000 },
    { QUEST_PROJECT_MARKET, FLAG_PROJECT_MARKET, 0, ITEM_SAGA_FLOUR, 5, ITEM_SAGA_HONEY, 5, 6000 },
};

typedef struct { u8 map, x, y, ability; int solved_flag; const char *name; } SagaNote;
static const SagaNote saga_notes[] = {
#define SAGA_NOTE(ID, MAP, X, Y, ABILITY, SOLVED) { MAP, X, Y, SAGA_##ABILITY, SOLVED, #ID },
#include "notes.inc"
#undef SAGA_NOTE
};
typedef char SagaNotesFit[(NOTE_COUNT <= 32 && sizeof(saga_notes) / sizeof(saga_notes[0]) == NOTE_COUNT) ? 1 : -1];
static int saga_note_map(int id) { return saga_notes[id].map; }
static int saga_note_x(int id) { return saga_notes[id].x; }
static int saga_note_y(int id) { return saga_notes[id].y; }
static int saga_note_ability(int id) { return saga_notes[id].ability; }

/* QuestState.pad is save-backed: observed [0..2], solved [3..5], paid day [6..15].
 * These bytes are zero in old saves; no non-save static progression is required. */
static int saga_note_bit(int id, int offset)
{
    return id >= 0 && id < NOTE_COUNT && (quest.pad[offset + id / 8] & (1u << (id & 7)));
}
static void saga_note(int id, int solved)
{
    if (id < 0 || id >= NOTE_COUNT) return;
    quest.pad[id / 8] |= (u8)(1u << (id & 7));
    if (solved) quest.pad[3 + id / 8] |= (u8)(1u << (id & 7));
    if (!quest_get(QUEST_FIELD_NOTES)) quest_set(QUEST_FIELD_NOTES, 1);
}
static int saga_note_ready(int ability)
{
    switch (ability) {
    case SAGA_LIGHT: return flag(FLAG_VOLT_CREST);
    case SAGA_SURF: return flag(FLAG_TIDE_CREST);
    case SAGA_STRENGTH: return flag(FLAG_CREST_ANVIL);
    case SAGA_FLY: return flag(FLAG_RIME_CREST);
    case SAGA_WARD: return flag(FLAG_LANTERN_CREST);
    default: return flag(FLAG_CREST_DREAM);
    }
}
static void saga_notes_sync(void)
{
    for (int i = 0; i < NOTE_COUNT; i++)
        if (saga_notes[i].solved_flag && flag(saga_notes[i].solved_flag))
            saga_note(i, 1);
}
static void saga_notes_here(int map)
{
    /* Regional scripts can call saga_note(id, solved) on examination. Until
     * their handlers are wired, entering a mapped region records its hints. */
    for (int i = 0; i < NOTE_COUNT; i++) if (saga_notes[i].map == map)
        saga_note(i, saga_notes[i].solved_flag && flag(saga_notes[i].solved_flag));
}

static int saga_project_state(int proj)
{
    if (proj < 0 || proj >= SAGA_PROJECT_COUNT) return 0;
    if (flag(saga_projects[proj].flag)) return 3;
    return quest_get(saga_projects[proj].quest);
}
static void saga_project_new_day(void)
{
    for (int i = 0; i < SAGA_PROJECT_COUNT; i++) {
        if (quest_is(saga_projects[i].quest, 2) &&
            (u16)gtime.day != (u16)(quest.pad[6 + i * 2] | (quest.pad[7 + i * 2] << 8))) {
            flag_set(saga_projects[i].flag);
            quest_set(saga_projects[i].quest, 255);
        }
    }
}
static void saga_entered(int map)
{
    saga_project_new_day();
    saga_notes_here(map);
    saga_notes_sync();
}
static void saga_bind(void)
{
    daily_extra_hook = saga_project_new_day;
    saga_map_entered = saga_entered;
    saga_project_new_day();
    saga_notes_sync();
}
static int saga_market_unlocked(void)
{
    int total = 0;
    for (int i = 0; i < SAGA_MARKET; i++) total += saga_project_state(i) == 3;
    return total >= 3;
}
static int saga_project_unlocked(int proj)
{
    if (proj == SAGA_FERRY) return quest_get(QUEST_VALE_COURIER) >= 7;
    if (proj == SAGA_MARKET) return saga_market_unlocked();
    return flag(saga_projects[proj].gate);
}
static void saga_project_offer(int proj)
{
    saga_bind();
    if (proj < 0 || proj >= SAGA_PROJECT_COUNT || !saga_project_unlocked(proj)) return;
    if (!quest_get(saga_projects[proj].quest)) quest_set(saga_projects[proj].quest, 1);
}
static int saga_pending_project;
static void saga_project_answer(int choice)
{
    const SagaProject *p = &saga_projects[saga_pending_project];
    if (choice) { dlg_say("The guild will hold the plans for you."); return; }
    if (!quest_is(p->quest, 1)) return;
    if (money < p->price || bag[p->item_a] < p->qty_a ||
        (p->qty_b && bag[p->item_b] < p->qty_b)) {
        dlg_say("You still need materials and coins. Check the project in your quest log.");
        return;
    }
    money -= p->price;
    bag[p->item_a] -= p->qty_a;
    if (p->qty_b) bag[p->item_b] -= p->qty_b;
    quest_advance_to(p->quest, 2);
    quest.pad[6 + saga_pending_project * 2] = (u8)gtime.day;
    quest.pad[7 + saga_pending_project * 2] = (u8)(gtime.day >> 8);
    dlg_say("The guild has your supplies. The work will be finished after the next dawn.");
}
static void saga_project_talk(int proj, const char *name)
{
    saga_project_offer(proj);
    if (!saga_project_unlocked(proj)) { dlg_say("The guild needs a safer road before this work can start."); return; }
    int st = saga_project_state(proj);
    if (st == 3) { dlg_say("The work is finished. The Vale has a new shortcut!"); return; }
    if (st == 2) { dlg_say("The builders are working. Come back after dawn."); return; }
    saga_pending_project = proj;
    dlg_ask(name, YES_NO, 2, saga_project_answer);
}
static void saga_courier_step(int stage, const char *message)
{
    if (!quest_is(QUEST_VALE_COURIER, stage)) return;
    quest_advance_to(QUEST_VALE_COURIER, stage + 1);
    dlg_say(message);
}
static void scr_saga_holt(int npc) { (void)npc; saga_project_talk(SAGA_TRAM, "HOLT: Five IRON ORE and 3000c for the tram. Fund it?"); }
static void scr_saga_greta(int npc)
{
    (void)npc; saga_bind();
    if (quest_is(QUEST_VALE_COURIER, 5)) { saga_courier_step(5, "GRETA: My answer for Elspeth. Take it west, safely."); return; }
    saga_project_talk(SAGA_BRIDGE, "GRETA: Four IRON ORE, two COAL, 4000c for the bridge. Fund it?");
}
static void scr_saga_astrid(int npc)
{
    (void)npc; saga_bind();
    if (quest_is(QUEST_VALE_COURIER, 7)) { saga_courier_step(7, "ASTRID: Thank you. Bring my reply to Elspeth."); return; }
    saga_project_talk(SAGA_LIFT, "ASTRID: Six TIMBER and 2500c for the lift. Fund it?");
}
static void scr_saga_elspeth(int npc)
{
    (void)npc; saga_bind();
    int st = quest_get(QUEST_VALE_COURIER);
    if (!st) {
        if (!flag(FLAG_VOLT_CREST)) { dlg_say("ELSPETH: The Fen boardwalk is closed. Come back after Lumen's lamps are lit."); return; }
        quest_set(QUEST_VALE_COURIER, 1);
        lore_reveal(LSRC_SAGA_COURIER, 0);
        dlg_say("ELSPETH: I run Reedwick's post by hand. This parcel goes to Brookmill's miller.");
    } else if (st == 2 || st == 4 || st == 6 || st == 8) {
        quest_advance_to(QUEST_VALE_COURIER, st + 1);
        money += 300;
        if (st == 8 && !bag[ITEM_FERRY_PASS]) give_item(ITEM_FERRY_PASS, 1);
        dlg_say("ELSPETH: A reply! Here is the next letter. I put 300 coins aside for the trip.");
    } else if (st == 12) {
        quest_set(QUEST_VALE_COURIER, 255);
        flag_set(FLAG_COURIER_REUNITED);
        give_item(ITEM_COURIER_SATCHEL, 1);
        dlg_say("ELSPETH: He's alive! My brother is coming home. Keep the satchel; you earned it.");
    } else if (st == 255) dlg_say("ELSPETH: We send the post together now. Thank you.");
    else dlg_say("ELSPETH: Follow the place marked in your quest log; the reply comes back to Reedwick.");
}
static void scr_saga_miller(int npc)
{
    (void)npc; saga_bind();
    if (quest_is(QUEST_VALE_COURIER, 1)) { saga_courier_step(1, "MILLER: A parcel for me? Tell Elspeth the wheel still turns."); return; }
    if (money >= 100) { money -= 100; give_item(ITEM_SAGA_FLOUR, 1); dlg_say("MILLER: Fresh flour, one bag for 100c."); }
    else dlg_say("MILLER: Flour is 100c a bag, if you need it for Maple.");
}
static void scr_saga_telegraph(int npc)
{ (void)npc; saga_bind(); if (quest_is(QUEST_VALE_COURIER, 3)) saga_courier_step(3, "CLERK: The hamlets need wires. Take my reply to Reedwick."); else dlg_say("CLERK: Letters still travel, even with the wires down."); }
static void scr_saga_pilgrim(int npc)
{ (void)npc; saga_bind(); if (quest_is(QUEST_VALE_COURIER, 11)) saga_courier_step(11, "PILGRIM: Elspeth is my sister. Take her this letter; I'll follow you home."); else dlg_say("PILGRIM: The road through the mist leads back to family."); }
static void scr_saga_audra(int npc)
{ (void)npc; saga_bind(); if (quest_is(QUEST_VALE_COURIER, 9)) saga_courier_step(9, "AUDRA: A sealed letter for Maud. Please take it to the Waychapel."); else dlg_say("AUDRA: Keep your papers safe on the March road."); }
static void scr_saga_maud(int npc)
{ (void)npc; saga_bind(); if (quest_is(QUEST_VALE_COURIER, 10)) saga_courier_step(10, "MAUD: The pilgrim at Mistfen's rest house knows this name. Find him."); else dlg_say("MAUD: Letters reach places voices cannot."); }
/* Survey from the actual day/night wild slots on each region's maps. */
static const u8 saga_survey_maps[6][5] = {
    { MAP_BROOKMILL_TRAIL, MAP_COPPERLINE, MAP_LUMEN, MAP_COPPER_MINE, MAP_NONE },
    { MAP_HERON_FEN, MAP_SALTWIND, MAP_SEA_ROUTE, MAP_REEDWICK, MAP_NONE },
    { MAP_CINDER_CROSSING, MAP_CINDER_ROAD, MAP_EMBER_TUNNEL, MAP_RAILHEAD, MAP_NONE },
    { MAP_FOOTHILLS, MAP_FROSTPINE, MAP_GLIMMER_1, MAP_GLIMMER_2, MAP_NONE },
    { MAP_HOLLOW_DOWNS, MAP_ASHEN_FIELDS, MAP_GRAVEWOOD, MAP_DUSKMERE, MAP_NONE },
    { MAP_MISTFEN, MAP_MOONVEIL, MAP_DREAMSPIRE, MAP_DUST_LIBRARY, MAP_NONE },
};
static void saga_survey_count(int region, int *met, int *total)
{
    u8 native[SP_COUNT] = { 0 };
    *met = *total = 0;
    for (int m = 0; m < 5; m++) {
        int map = saga_survey_maps[region][m];
        if (map == MAP_NONE) continue;
        int zones[] = { MAPS[map].zone, MAPS[map].water_zone };
        for (int z = 0; z < 2; z++) {
            int zone = zones[z];
            if (zone <= ZONE_NONE || zone >= ZONE_COUNT) continue;
            for (int i = 0; i < WILD_ZONES[zone].count; i++) {
                int sp = WILD_ZONES[zone].slots[i].species;
                if (sp > 0 && sp < SP_COUNT) native[sp] = 1;
            }
        }
    }
    for (int sp = 1; sp < SP_COUNT; sp++) if (native[sp]) {
        ++*total;
        *met += !!(dex_seen[sp] || dex_caught[sp]);
    }
}
static void scr_saga_survey(int npc)
{
    (void)npc; saga_bind();
    int st = quest_get(QUEST_ALMANAC_SURVEY);
    if (!st) { quest_set(QUEST_ALMANAC_SURVEY, 1); lore_reveal(LSRC_SAGA_ALMANAC, 0);
        dlg_say("LINDEN: Meet the wild kin in each region. Day and night sightings both count."); return; }
    if (st == 255) { dlg_say("LINDEN: Every page of the Vale is in your almanac now."); return; }
    int met, total, region = st - 1;
    saga_survey_count(region, &met, &total);
    int target = total < 6 ? total : 6;
    if (target && met >= target) {
        if (region == 5) { quest_set(QUEST_ALMANAC_SURVEY, 255); give_item(ITEM_STAR_LANTERN, 5); }
        else { quest_advance_to(QUEST_ALMANAC_SURVEY, st + 1);
            give_item(region == 1 ? ITEM_TIDE_LANTERN : region == 4 ? ITEM_DUSK_LANTERN : ITEM_GLOW_LANTERN, 2); }
        dlg_say("LINDEN: The survey is complete. Here are lanterns for your next journey.");
    } else {
        char text[100] = "LINDEN: Native kin met: ";
        str_put_int(text, met); str_put(text, "/"); str_put_int(text, target);
        str_put(text, ". Return after exploring the region at different hours.");
        dlg_say(text);
    }
}
static void scr_saga_linden(int npc)
{
    (void)npc; saga_bind();
    saga_project_talk(SAGA_MARKET, "LINDEN: Five FLOUR, five HONEY, 6000c for the market. Fund it?");
}
static void scr_saga_widow(int npc)
{
    (void)npc; saga_bind(); int st = quest_get(QUEST_HERONS_RING);
    if (!st) { quest_set(QUEST_HERONS_RING, 1); dlg_say("WIDOW: The herons took my reed ring to the Fen. Could you look?"); }
    else if (st == 3) { quest_set(QUEST_HERONS_RING, 255); give_item(ITEM_RING_OF_REEDS, 1); dlg_say("WIDOW: You found it. Keep it: you carried it all this way."); }
    else dlg_say("WIDOW: Did you find the ring? Follow the quest log.");
}
static void scr_saga_ring(int npc)
{
    (void)npc; saga_bind(); int st = quest_get(QUEST_HERONS_RING);
    if (st == 1 && flag(FLAG_TIDE_CREST)) { quest_advance_to(QUEST_HERONS_RING, 2); dlg_say("An empty nest. RACCOIN tracks lead back toward Maple."); }
    else if (st == 2 && cur_map == MAP_TOWN) { quest_advance_to(QUEST_HERONS_RING, 3); flag_set(FLAG_RING_FOUND); dlg_say("RACCOIN drops the ring. Return to the widow in Reedwick."); }
    else dlg_say("The nest is just out of reach. SURF may help.");
}
static void scr_saga_mine(int npc)
{
    (void)npc; saga_bind(); int st = quest_get(QUEST_MINERS_LAMP);
    if (!st) { quest_set(QUEST_MINERS_LAMP, 1); dlg_say("MINER: My lamp is lost in the dark gallery. Bring it to the Cindermoor forge."); }
    else if (st == 1 && flag(FLAG_VOLT_CREST)) { quest_advance_to(QUEST_MINERS_LAMP, 2); flag_set(FLAG_LAMP_FOUND); dlg_say("The gallery is lit. You found the miner's lamp!"); }
    else if (st == 3) { quest_set(QUEST_MINERS_LAMP, 255); give_item(ITEM_METAL_SHARD, 1); dlg_say("MINER: The repaired lamp burns again. Take this shard."); }
    else dlg_say("MINER: LIGHT reveals the gallery; the forge in Cindermoor can repair it.");
}
static void scr_saga_forge(int npc)
{ (void)npc; saga_bind(); if (quest_is(QUEST_MINERS_LAMP, 2)) { quest_advance_to(QUEST_MINERS_LAMP, 3); dlg_say("SMITH: The lamp is repaired. Bring it back to the mine."); } else dlg_say("SMITH: Iron remembers the hands that shape it."); }
static void scr_saga_chalk(int npc)
{
    (void)npc; saga_bind(); int st = quest_get(QUEST_CHALK_HORSE);
    if (!st) { quest_set(QUEST_CHALK_HORSE, 1); dlg_say("CUTTER: BONE MEAL and SALT will restore the chalk horse."); }
    else if (st == 1 && bag[ITEM_BONE_MEAL] && bag[ITEM_SALT]) {
        bag[ITEM_BONE_MEAL]--; bag[ITEM_SALT]--; quest_advance_to(QUEST_CHALK_HORSE, 2);
        flag_set(FLAG_CHALK_DRAWN); dlg_say("CUTTER: The white horse is drawn again. Return to see it.");
    } else if (st == 2) { quest_set(QUEST_CHALK_HORSE, 255); dlg_say("CUTTER: Some say DULLAHAN follows that old outline at dusk."); }
    else dlg_say("CUTTER: The chalk needs BONE MEAL and SALT.");
}
static void scr_saga_ida(int npc)
{
    (void)npc; saga_bind(); int st = quest_get(QUEST_STARLIGHT_IDA);
    if (!st) { quest_set(QUEST_STARLIGHT_IDA, 1); dlg_say("IDA: Read the Star Cairn in the north and come back."); }
    else if (st == 1 && flag(FLAG_RIME_CREST)) { dlg_say("IDA: Find a clear northern star; bring me the reading."); }
    else if (st == 2) { quest_set(QUEST_STARLIGHT_IDA, 255); give_item(ITEM_ASTRAL_SHARD, 1); dlg_say("IDA: A new star! Keep this shard."); }
    else dlg_say("IDA: The northern stars are waiting.");
}
static void scr_saga_cairn(int npc)
{
    (void)npc; saga_bind();
    if (quest_is(QUEST_STARLIGHT_IDA, 1) && flag(FLAG_RIME_CREST)) {
        quest_advance_to(QUEST_STARLIGHT_IDA, 2); flag_set(FLAG_IDA_READING);
        dlg_say("The cairn's stars mirror Ida's chart. Tell her what you saw.");
    } else dlg_say("Stars trace an ancient path in the stone.");
}
static const int saga_legend_pages[] = {
    LORE_SYLVARCH, LORE_NOCTHALE, LORE_HOARFANG, LORE_CALDERON,
    LORE_SELENOTH, LORE_HOROLOGOS, LORE_SCRIPTORA, LORE_SKYLORN
};
static int saga_legend_count(void)
{
    int count = 0;
    for (unsigned i = 0; i < sizeof(saga_legend_pages) / sizeof(saga_legend_pages[0]); i++)
        count += lore_is_known(saga_legend_pages[i]);
    return count;
}
static void scr_saga_book(int npc)
{
    (void)npc; saga_bind(); lore_reveal(LSRC_SAGA_LEGENDS, 0);
    if (!quest_get(QUEST_LEGEND_TRAIL)) quest_set(QUEST_LEGEND_TRAIL, 1);
    int verses = saga_legend_count();
    if (flag(FLAG_OSSUREX_ANSWERED)) quest_advance_to(QUEST_LEGEND_TRAIL, 2);
    if (verses == 8 && flag(FLAG_OSSUREX_ANSWERED)) {
        quest_set(QUEST_LEGEND_TRAIL, 255);
        dlg_say("Eight legends answered. The book calls you STORMFRIEND; the Rise remembers DRAKORA.");
    } else {
        char text[100] = "The pilgrim's book holds ";
        str_put_int(text, verses); str_put(text, "/8 legend pages. Their lairs wait until the March heals.");
        dlg_say(text);
    }
}
static void scr_saga_notes(int npc)
{
    (void)npc; saga_bind();
    for (int i = 0; i < NOTE_COUNT; i++) if (saga_notes[i].map == cur_map) saga_note(i, 0);
    int found = 0, solved = 0, ready = 0;
    for (int i = 0; i < NOTE_COUNT; i++) if (saga_note_bit(i, 0)) {
        found++; solved += !!saga_note_bit(i, 3);
        ready += !saga_note_bit(i, 3) && saga_note_ready(saga_notes[i].ability);
    }
    char text[90] = "FIELD NOTES: ";
    str_put_int(text, found); str_put(text, " found, "); str_put_int(text, solved);
    str_put(text, " solved, "); str_put_int(text, ready); str_put(text, " ready to revisit.");
    dlg_say(text);
    static const char *const ability_names[] = {
        "LIGHT", "SURF", "STRENGTH", "FLY", "WARD LANTERN", "TELEPORT"
    };
    for (int ability = 0; ability <= SAGA_TELEPORT; ability++) {
        char page[250];
        str_copy(page, ability_names[ability]);
        int count = 0;
        for (int i = 0; i < NOTE_COUNT; i++) {
            const SagaNote *note = &saga_notes[i];
            if (note->ability != ability || !saga_note_bit(i, 0)) continue;
            str_put(page, "\n"); str_put(page, MAPS[note->map].name);
            str_put(page, saga_note_bit(i, 3) ? " DONE" : saga_note_ready(ability) ? " READY" : " LOCKED");
            count++;
        }
        if (count) dlg_say(page);
    }
}
static void scr_saga_ferry(int npc)
{ (void)npc; saga_project_talk(SAGA_FERRY, "ELSPETH: Four TIMBER, two SALT, 2000c for the ferry. Fund it?"); }
static void saga_punt_answer(int choice)
{
    if (choice) return;
    if (cur_map == MAP_REEDWICK) field_begin_warp(MAP_LAKE, 31, 17, DIR_RIGHT);
    else field_begin_warp(MAP_REEDWICK, 25, 20, DIR_LEFT);
}
static void scr_saga_punt(int npc)
{
    (void)npc; saga_bind();
    if (!flag(FLAG_PROJECT_REED_FERRY)) { dlg_say("The punt is not afloat yet. Ask Elspeth about the ferry."); return; }
    dlg_ask("Take the Reedwick punt to the other shore?", YES_NO, 2, saga_punt_answer);
}
static void scr_saga_sawyer(int npc)
{
    (void)npc; saga_bind();
    if (money < 100) { dlg_say("SAWYER: TIMBER is 100c a length."); return; }
    money -= 100; give_item(ITEM_SAGA_TIMBER, 1);
    dlg_say("SAWYER: One sound length of TIMBER, for 100c.");
}
static void scr_saga_honey(int npc)
{
    (void)npc; saga_bind();
    if (!bag[ITEM_GLOW_HONEY]) { dlg_say("BEEKEEPER: Bring GLOW HONEY to strain into market HONEY."); return; }
    bag[ITEM_GLOW_HONEY]--; give_item(ITEM_SAGA_HONEY, 1);
    dlg_say("BEEKEEPER: One jar of HONEY for the Maple market.");
}
static int saga_tram_from;
static const char *const saga_tram_choices[] = { "MAPLE", "BROOKMILL", "LUMEN", "CANCEL" };
static void saga_tram_answer(int choice)
{
    if (choice < 0 || choice >= 3 || choice == saga_tram_from) return;
    /* Town landings have a clear return path to their stop. */
    const int maps[] = { MAP_TOWN, MAP_BROOKMILL, MAP_LUMEN };
    const int xs[] = { 12, 31, 36 }, ys[] = { 17, 29, 20 };
    field_begin_warp(maps[choice], xs[choice], ys[choice], DIR_DOWN);
}
static void saga_tram_stop(int stop)
{
    saga_bind();
    if (!flag(FLAG_PROJECT_TRAM)) { dlg_say("The tram rails are quiet. Guildmaster Holt has the plans."); return; }
    saga_tram_from = stop;
    dlg_ask("Ride the tram to which town?", saga_tram_choices, 4, saga_tram_answer);
}
static void scr_saga_tram_maple(int npc) { (void)npc; saga_tram_stop(0); }
static void scr_saga_tram_brook(int npc) { (void)npc; saga_tram_stop(1); }
static void scr_saga_tram_lumen(int npc) { (void)npc; saga_tram_stop(2); }
static void saga_lift_answer(int choice)
{
    if (choice) return;
    if (cur_map == MAP_TIMBERLINE) field_begin_warp(MAP_FOOTHILLS, 11, 52, DIR_DOWN);
    else field_begin_warp(MAP_TIMBERLINE, 11, 30, DIR_UP);
}
static void saga_lift_stop(void)
{
    saga_bind();
    if (!flag(FLAG_PROJECT_LIFT)) { dlg_say("The lift is not built yet. Ask Astrid at Timberline."); return; }
    dlg_ask("Take the cable lift?", YES_NO, 2, saga_lift_answer);
}
static void scr_saga_lift_low(int npc) { (void)npc; saga_lift_stop(); }
static void scr_saga_lift_high(int npc) { (void)npc; saga_lift_stop(); }

/* Until the far owner attaches its dormant E5 MapPatch, this keeps the
 * SURF-first route and the paid bridge bidirectional without a trap. */
static void saga_bridge_pass_answer(int choice)
{
    if (choice) return;
    field_begin_warp(MAP_CINDER_CROSSING, player.x < 8 ? 11 : 4, 21,
                     player.x < 8 ? DIR_RIGHT : DIR_LEFT);
}
static void scr_saga_bridge_pass(int npc)
{
    (void)npc; saga_bind();
    if (!flag(FLAG_TIDE_CREST) && !flag(FLAG_PROJECT_CINDER_BRIDGE)) {
        dlg_say("The spring flood took the bridge. Return with the TIDE CREST."); return;
    }
    dlg_ask(flag(FLAG_PROJECT_CINDER_BRIDGE) ? "Cross the rebuilt Cinder bridge?"
                : "SURF across the Cinder river?", YES_NO, 2, saga_bridge_pass_answer);
}
