/*
 * world/west/scripts.c -- NPC scripts of W-WEST: Saltwind Trail, Port Brine
 * (shop, harbor office, inn, the Current Hall and its Master), Gull Isle.
 * Registered in script_ids.inc and script_table.inc. Owner: W-WEST.
 *
 * Quests: HARBOR POST (three letters in Port Brine -> the FERRY PASS) and
 * SALT FOR THE ISLE (3 SALT for Oda). The Hall Master bout goes through
 * battle_start_master (TT_MASTER) and hands over the TIDE CREST with
 * travel_award_crest. Crossings use travel_boat_to.
 */

#define WEST_FARE 500
/* where the ferry lands (a pier cell next to the other side's ferry) */
#define WEST_ISLE_PIER_X 33
#define WEST_ISLE_PIER_Y 5
#define WEST_BRINE_PIER_X 31
#define WEST_BRINE_PIER_Y 34

/* ---------------- Saltwind ---------------- */

static void scr_salt_raker(int npc)
{
    (void)npc;
    if (!flag(FLAG_SALT_GIFT)) {
        flag_set(FLAG_SALT_GIFT);
        dlg_say("A traveler! Here, a pinch for the road. Well, a sack. Salt keeps; so do friends.");
        give_item(ITEM_SALT, 3);
        return;
    }
    lore_reveal(LSRC_SALT_RAKER, "The best salt comes on the windy days. Today is a good day.");
}

/* ---------------- ferries ---------------- */

static void ferry_sail(int to_isle)
{
    if (to_isle) travel_boat_to(MAP_GULL_ISLE, WEST_ISLE_PIER_X, WEST_ISLE_PIER_Y);
    else travel_boat_to(MAP_PORT_BRINE, WEST_BRINE_PIER_X, WEST_BRINE_PIER_Y);
}

static void brine_ferry_answer(int c)
{
    int to_isle = cur_map != MAP_GULL_ISLE;
    if (c != 0) {
        dlg_say("The tide will wait. I won't, mind!");
        return;
    }
    if (to_isle && !bag[ITEM_FERRY_PASS]) {
        if (money < WEST_FARE) {
            dlg_say("That's 500c for the crossing, and your purse is a little light.");
            return;
        }
        money -= WEST_FARE;
        sfx_play(SFX_ITEM);
        dlg_say("500c, thank you kindly. All aboard!");
    } else {
        dlg_say(to_isle ? "A FERRY PASS! Hop on, the gulls are waiting." : "Back to Brine it is. Hold on to your hat!");
    }
    dlg_call(ferry_sail, to_isle);
}

static void scr_ferry(int npc)
{
    (void)npc;
    if (cur_map == MAP_GULL_ISLE)
        dlg_ask("Sailing back to PORT BRINE? The return is paid for.", YES_NO, 2, brine_ferry_answer);
    else if (bag[ITEM_FERRY_PASS])
        dlg_ask("GULL ISLE with your FERRY PASS? Free as the wind.", YES_NO, 2, brine_ferry_answer);
    else
        dlg_ask("The ferry to GULL ISLE: 500c a crossing, the way back included. Sail?", YES_NO, 2,
                brine_ferry_answer);
}

/* ---------------- Port Brine ---------------- */

static void scr_lightkeeper(int npc)
{
    (void)npc;
    if (!flag(FLAG_WEST_ROCKPOOL)) {
        flag_set(FLAG_WEST_ROCKPOOL);
        lore_reveal(LSRC_LIGHTKEEPER, 0);
        give_item(ITEM_TIDE_LANTERN, 2);
        return;
    }
    lore_reveal(LSRC_LIGHTKEEPER, "Fog tonight, I'd wager. The light will be busy.");
}

static const u8 BRINE_STOCK[] = {
    ITEM_LANTERN, ITEM_GLOW_LANTERN, ITEM_TIDE_LANTERN, ITEM_TONIC, ITEM_BIG_TONIC,
    ITEM_SOOTHE_BALM, ITEM_WAKE_BELL, ITEM_MINT_TEA, ITEM_HUSH_BELL, ITEM_SALT, ITEM_FROST_SHARD,
};

static const char *const BRINE_SHOP_MENU[3] = { "BUY", "CHAT", "QUIT" };

static void brine_shop_answer(int c)
{
    if (c == 0) shop_open_stock(BRINE_STOCK, (int)sizeof(BRINE_STOCK));
    else if (c == 1) dlg_say("TIDE LANTERNS are woven with sea glass. They hold water kin best, and anything you meet while surfing.");
    else dlg_say("Fair winds!");
}

static void scr_brine_shop(int npc)
{
    (void)npc;
    dlg_ask("Welcome to the BRINE SHOP! Lanterns, tonics, and salt by the scoop.", BRINE_SHOP_MENU, 3,
            brine_shop_answer);
}

static int west_post_count(void)
{
    return flag(FLAG_POST_INN) + flag(FLAG_POST_SKIPPER) + flag(FLAG_POST_HALL);
}

/* A person on the HARBOR POST round: takes their letter once. */
static int west_post_deliver(int f, const char *thanks)
{
    if (quest_get(QUEST_HARBOR_POST) != 1 || flag(f)) return 0;
    flag_set(f);
    sfx_play(SFX_ITEM);
    dlg_say("You handed over a letter from the HARBOR OFFICE.");
    dlg_say(thanks);
    if (west_post_count() == 3) dlg_say("That was the last letter. Time to report to the HARBOR MASTER!");
    return 1;
}

static void harbor_crossing(int unused)
{
    (void)unused;
    scr_ferry(0);
}

static void scr_harbormaster(int npc)
{
    (void)npc;
    int st = quest_get(QUEST_HARBOR_POST);
    if (st == 0) {
        quest_set(QUEST_HARBOR_POST, 1);
        dlg_say("A warden with free hands! My runner's down with a cold. Three letters, all in town:");
        dlg_say("the GULL INN keeper, the old skipper up the hill, and the guide in the CURRENT HALL. "
                "Do that and I'll see you right.");
        dlg_say("(HARBOR POST was added to your QUEST LOG.)");
        return;
    }
    if (st == 1) {
        if (west_post_count() < 3) {
            dlg_say("Still letters in your bag? The inn, the skipper and the Hall guide. Off you go!");
            dlg_call(harbor_crossing, 0);
            return;
        }
        quest_set(QUEST_HARBOR_POST, 255);
        dlg_say("All three delivered, and not one soggy. You're hired. Well, thanked.");
        give_item(ITEM_FERRY_PASS, 1);
        dlg_say("Show the FERRY PASS at the pier and the ferry takes you to GULL ISLE for free.");
        return;
    }
    if (lore_reveal(LSRC_HARBORMASTER, 0)) return;
    dlg_call(harbor_crossing, 0);
}

static const char *const INN_MENU[3] = { "REST 100c", "CHAT", "NO THANKS" };

static void brine_inn_answer(int c)
{
    if (c == 1) {
        dlg_say("Fish pie tonight. Fish pie every night, truth be told. Ask the cook for the recipe!");
        return;
    }
    if (c != 0) {
        dlg_say("Door's always open. Mind the step.");
        return;
    }
    if (money < 100) {
        dlg_say("100c for a bed, love. Come back when the purse is heavier.");
        return;
    }
    money -= 100;
    hearth_rest();
    dlg_say("You slept to the sound of the harbor. Your kin woke up full of vigor!");
}

static void scr_brine_innkeeper(int npc)
{
    (void)npc;
    if (west_post_deliver(FLAG_POST_INN, "A letter from the harbor? My brother on GULL ISLE! Thank you, dear.")) return;
    dlg_ask("Welcome to the GULL INN. A bed for your team is 100c.", INN_MENU, 3, brine_inn_answer);
}

static void scr_skipper(int npc)
{
    (void)npc;
    if (west_post_deliver(FLAG_POST_SKIPPER, "Post, for me? My old crew. Still alive, the lot of them. Ha!")) return;
    lore_reveal(LSRC_SKIPPER, "Watch the Moon, warden. The sea always does.");
}

static void scr_hall_guide(int npc)
{
    (void)npc;
    if (west_post_deliver(FLAG_POST_HALL, "A letter? Oh, it's the harbor's water bill. Lovely. Thanks, I think.")) return;
    if (lore_reveal(LSRC_HALL_GUIDE, 0)) return;
    dlg_say(flag(FLAG_TIDE_CREST) ? "The TIDE CREST suits you! With a big TIDE kin you can SURF now."
                                  : "Up is MAREN. Down is me. Look where a channel ends before you ride it!");
}

/* ---------------- HALL MASTER MAREN ---------------- */

static void maren_end(int result)
{
    if (result != BR_WIN) {
        dlg_say("MAREN: The current's not going anywhere. Neither am I. Come back when you're rested.");
        return;
    }
    trainer_mark_beaten(TR_MAREN);
    if (flag(FLAG_TIDE_CREST)) return;
    flag_set(FLAG_TIDE_CREST);
    travel_award_crest(CREST_TIDE);
    sfx_play(SFX_ITEM);
    dlg_say("You received the TIDE CREST! A wave of blue glass set in a silver ring.");
    lore_story(LORE_TIDE_CREST);
    dlg_say("MAREN: With that, a TIDE kin of level 20 or more can carry you over open water. Take these too.");
    give_item(ITEM_TIDE_LANTERN, 3);
}

static void maren_begin(int c)
{
    if (c != 0) {
        dlg_say("MAREN: Take your time. Water always does.");
        return;
    }
    static TrainerTeam t;
    t = team_from(&TRAINERS[TR_MAREN], BSCENE_SEA);
    battle_end_hook = maren_end;
    battle_start_master(&t);
}

static void scr_maren(int npc)
{
    (void)npc;
    if (!party_count || party_first_healthy() < 0) {
        dlg_say("MAREN: Your kin are worn out. The BRINE HEARTH HALL is just down the hill.");
        return;
    }
    if (flag(FLAG_TIDE_CREST)) {
        dlg_ask("MAREN: Back for the channels? A rematch, for the joy of it?", YES_NO, 2, maren_begin);
        return;
    }
    dlg_say("MAREN: You found the right currents and set the tides. Most people ride the chute back to the door three times first.");
    dlg_say("I'm MAREN, Master of the CURRENT HALL. Six TIDE kin, and every one of them knows how to wait.");
    dlg_ask("Shall we see which way the tide turns?", YES_NO, 2, maren_begin);
}

/* ---------------- Gull Isle ---------------- */

static void scr_oda(int npc)
{
    (void)npc;
    int st = quest_get(QUEST_ISLE_SALT);
    if (st == 0) {
        quest_set(QUEST_ISLE_SALT, 1);
        dlg_say("Oh, a warden! Our salt boat is late again, and the catch won't cure itself.");
        dlg_say("Could you bring me 3 SALT? The pans on SALTWIND TRAIL are full of it.");
        dlg_say("(SALT FOR THE ISLE was added to your QUEST LOG.)");
        return;
    }
    if (st == 1) {
        if (bag[ITEM_SALT] < 3) {
            dlg_say("3 SALT, dear, for the fish. The rakers on SALTWIND TRAIL will help you.");
            return;
        }
        bag_add(ITEM_SALT, -3);
        quest_set(QUEST_ISLE_SALT, 255);
        dlg_say("You handed over 3 SALT. The fish thank you. So do I!");
        give_item(ITEM_GRAND_TONIC, 2);
        dlg_say("And a story, since you've been kind. Sit, sit.");
        lore_reveal(LSRC_ODA, 0);
        return;
    }
    lore_reveal(LSRC_ODA, "The bell rang again last night. Somebody down there is waiting for an answer.");
}

/* Brookmill's Lumen rivets arrive once VOLT is earned. E5 refreshes the gap
 * when flag_set runs, and E3 swaps the two builders for their thank-you. */
static void scr_fen_carpenter(int npc)
{
    (void)npc;
    if (flag(FLAG_FEN_RIVETS)) {
        dlg_say("The boardwalk holds now. Mind the reeds under your feet!");
    } else if (flag(FLAG_VOLT_CREST)) {
        flag_set(FLAG_FEN_RIVETS);
        dlg_say("Lumen's rivets came through Brookmill! We've finished the span. Head west to REEDWICK.");
    } else {
        dlg_say("Lumen's lamps went out west. No rivets till a Volt warden helps them. "
                "Mind the missing planks; the eastern bank is safe to explore.");
    }
}

/* Quest stage 2..254 records the season ordinal modulo 253.
 * Save state stays in the quest slot; no new global season counter. */
static int reed_roof_season(void)
{
    return ((gtime.day - 1) / SEASON_DAYS) % 253 + 2;
}

static void scr_reed_nell(int npc)
{
    (void)npc;
    if (cur_map == MAP_REED_SHOP) {
        static const u8 stock[] = { ITEM_BERRY_JUICE, ITEM_TONIC, ITEM_SALT };
        shop_open_stock(stock, (int)sizeof(stock));
        return;
    }
    int stage = quest_get(QUEST_REED_ROOF);
    if (!stage) {
        quest_set(QUEST_REED_ROOF, 1);
        lore_reveal(LSRC_REEDWICK, "Five TIDEBERRIES for the smokehouse roof, please.");
        return;
    }
    if (stage == reed_roof_season()) {
        dlg_say("The new roof is holding. Come back when the season turns!");
        return;
    }
    if (bag[ITEM_CROP_TIDEBERRY] < 5) {
        dlg_say("Five TIDEBERRIES from the fen berry bushes. They grow back after a few days.");
        return;
    }
    bag_add(ITEM_CROP_TIDEBERRY, -5);
    money += 300;
    quest_set(QUEST_REED_ROOF, reed_roof_season());
    sfx_play(SFX_ITEM);
    dlg_say("NELL: Five bundles for the roof! Here's 300c. Come again next season.");
}

static void fen_tutor_answer(int choice)
{
    if (choice != 0) return;
    int slot = party_first_healthy();
    if (slot < 0 || bag[ITEM_SALT] < 2) {
        dlg_say("Bring a healthy kin and two SALT for the lesson.");
        return;
    }
    Monster *m = &party[slot];
    for (int i = 0; i < MAX_MOVES; i++) {
        if (m->moves[i] == M_SLIPSTREAM) {
            dlg_say("Your kin already knows SLIPSTREAM.");
            return;
        }
    }
    int empty = -1;
    for (int i = 0; i < MAX_MOVES; i++)
        if (m->moves[i] == MOVE_NONE) { empty = i; break; }
    if (empty < 0) {
        dlg_say("Your first healthy kin knows four moves already. Make room before returning.");
        return;
    }
    bag_add(ITEM_SALT, -2);
    monster_replace_move(m, empty, M_SLIPSTREAM);
    dlg_say("The hermit taught your kin SLIPSTREAM! The tide remembers the lesson.");
}

static void scr_fen_hermit(int npc)
{
    (void)npc;
    dlg_ask("I'll teach your first healthy kin SLIPSTREAM for two SALT. Learn?",
            YES_NO, 2, fen_tutor_answer);
}

#include "biomes/scripts.c"
