/*
 * world/east/scripts.c -- NPC scripts for REGION EAST (owner: W-EAST).
 * Registered in script_ids.inc and script_table.inc. Uses the stub APIs of
 * the other systems: travel_award_crest (travel.c), quest_set (quest.c),
 * shop_open_stock (menu.c), battle_start_master (battle_ui.c).
 */

/* ---------------- Copperline Road ---------------- */

static void scr_miner(int npc)
{
    (void)npc;
    if (lore_reveal(LSRC_MINER, 0)) return;
    if (!flag(FLAG_MINER_GIFT)) {
        flag_set(FLAG_MINER_GIFT);
        dlg_say("HESK: You listened to an old man ramble. Here, a bit of the old seam for your trouble.");
        give_item(ITEM_IRON_ORE, 3);
        return;
    }
    dlg_say("HESK: Copper for the wires, iron for the pylons. Lumen was built out of this hill.");
}

/* ---------------- Lumen City ---------------- */

static const u8 LUMEN_STOCK[] = {
    ITEM_LANTERN, ITEM_GLOW_LANTERN, ITEM_STAR_LANTERN, ITEM_TONIC, ITEM_BIG_TONIC,
    ITEM_GRAND_TONIC, ITEM_SOOTHE_BALM, ITEM_WAKE_BELL, ITEM_MINT_TEA, ITEM_HUSH_BELL,
    ITEM_SWIFT_COIL, ITEM_FOCUS_COIL, ITEM_WILL_COIL, ITEM_LURE_INCENSE, ITEM_WAYSTONE,
    ITEM_SPARK_SHARD, ITEM_METAL_SHARD,
};

static void lumen_shop_answer(int c)
{
    if (c == 0) shop_open_stock(LUMEN_STOCK, (int)sizeof(LUMEN_STOCK));
    else if (c == 1) dlg_say("A COIL gives one kin a boost for a bout. They're wound right here in Lumen.");
    else dlg_say("Come again! Mind the tram rails. We don't have trams. Mind them anyway.");
}

static void scr_lumen_shop(int npc)
{
    (void)npc;
    dlg_ask("Welcome to the LUMEN MARKET! Coils, lanterns, shards. What can I do for you?", SHOP_MENU, 3,
            lumen_shop_answer);
}

/* The BIKE errand: OTTO (stage 1) -> VEX (stage 2) -> OTTO gives the BIKE. */
static void scr_bike_otto(int npc)
{
    (void)npc;
    int st = quest_get(QUEST_BIKE_ERRAND);
    if (quest_done(QUEST_BIKE_ERRAND)) {
        dlg_say("OTTO: How's the BIKE riding? Press R to hop on outdoors. Not in my shop!");
    } else if (st == 0) {
        quest_set(QUEST_BIKE_ERRAND, 1);
        dlg_say("OTTO: Bikes, bikes, bikes! I'd sell you one, but my courier's off sick.\f"
                "Take this bag of spokes to TINKER VEX in the east canal house? Do that and we'll talk.");
    } else if (st == 1) {
        dlg_say("OTTO: The spokes go to TINKER VEX. East canal house, south of the boulevard.");
    } else {
        quest_set(QUEST_BIKE_ERRAND, 255);
        dlg_say("OTTO: Vex has them? Brilliant! A deal's a deal. This one's yours.");
        give_item(ITEM_BIKE, 1);
    }
}

static void scr_tinker(int npc)
{
    (void)npc;
    if (quest_get(QUEST_BIKE_ERRAND) == 1) {
        quest_set(QUEST_BIKE_ERRAND, 2);
        dlg_say("VEX: Spokes from OTTO! Finally. Tell him the dynamo hubs are ready. He'll know.");
        return;
    }
    if (flag(FLAG_VOLT_CREST) && !flag(FLAG_FEN_RIVETS) && !flag(FLAG_RIVET_BUNDLE)) {
        flag_set(FLAG_RIVET_BUNDLE);
        dlg_say("VEX: Volt rivets for Brookmill! Take this bundle to GUILDMASTER HOLT.");
        return;
    }
    if (lore_reveal(LSRC_TINKER, 0)) return;
    if (!flag(FLAG_TINKER_GIFT)) {
        flag_set(FLAG_TINKER_GIFT);
        dlg_say("VEX: You actually listened! Nobody listens. Take this. I wound it myself.");
        give_item(ITEM_WILL_COIL, 1);
        return;
    }
    dlg_say("VEX: Spin a magnet in a coil of wire and you get current. Everything else is details.");
}

static void inn_answer(int c)
{
    if (c != 0) {
        dlg_say("The kettle's always on. Come back any time.");
        return;
    }
    if (money < 50) {
        dlg_say("Fifty coins a night, I'm afraid. The kettle's free, though.");
        return;
    }
    money -= 50;
    hearth_rest();
    dlg_say("You slept in a soft bed above the canal. Your kin are full of vigor!");
}

static void scr_innkeeper(int npc)
{
    (void)npc;
    dlg_ask("Welcome to the COPPER KETTLE! A room for the night is 50 coins. Stay?", YES_NO, 2, inn_answer);
}

/* ---------------- the Volt Hall ---------------- */

static void scr_volt_guide(int npc)
{
    (void)npc;
    if (quest_get(QUEST_VOLT_HALL) == 0) quest_set(QUEST_VOLT_HALL, 1);
    if (flag(FLAG_VOLT_CREST)) {
        dlg_say("GUIDE: The VOLT CREST! Your SPARK kin can light up any dark place for you now.");
        return;
    }
    if (lore_reveal(LSRC_VOLT_GUIDE, 0)) return;
    dlg_say("GUIDE: A tip. Each floor switch flips every barrier of its colour, up or down.\f"
            "Start with the switch nearest the door. And one switch undoes another's work. Watch for it!");
}

static void fara_end(int result)
{
    if (result != BR_WIN) return;
    trainer_mark_beaten(TR_FARA);
    if (flag(FLAG_VOLT_CREST)) return;
    flag_set(FLAG_VOLT_CREST);
    travel_award_crest(CREST_VOLT);
    quest_set(QUEST_VOLT_HALL, 255);
    sfx_play(SFX_ITEM);
    dlg_say("You received the VOLT CREST! A copper bolt in a ring of glass.");
    lore_story(LORE_VOLT_CREST);
    dlg_say("FARA: With it, your SPARK kin will share their LIGHT in the dark. And take these. I wind them myself.");
    give_item(ITEM_SWIFT_COIL, 2);
}

static void fara_answer(int c)
{
    if (c != 0) {
        dlg_say("FARA: The current will wait. It always does.");
        return;
    }
    static TrainerTeam t;
    t = team_from(&TRAINERS[TR_FARA], BSCENE_CITY);
    battle_end_hook = fara_end;
    battle_start_master(&t);
}

static void scr_fara(int npc)
{
    (void)npc;
    if (flag(FLAG_VOLT_CREST)) {
        dlg_say("FARA: Lightning never strikes twice, they say. They've never met my kin. Come back for a rematch sometime.");
        return;
    }
    if (party_first_healthy() < 0) {
        dlg_say("FARA: Your kin are spent. Rest them at the hearth, then come find me.");
        return;
    }
    dlg_ask("FARA: You threaded my barriers. Most wardens just walk into them.\f"
            "I am FARA, Master of the VOLT HALL. Six kin, one crest. Ready?", YES_NO, 2, fara_answer);
}

/* ---------------- Elderwood Heart ---------------- */

static void scr_grove(int npc)
{
    (void)npc;
    if (lore_reveal(LSRC_GROVE, 0)) return;
    if (!flag(FLAG_GROVE_GIFT)) {
        flag_set(FLAG_GROVE_GIFT);
        dlg_say("KEEPER: You've heard the Elder's story. Take these caps. They glow when a friend is near.");
        give_item(ITEM_GLOWCAP, 3);
        return;
    }
    dlg_say("KEEPER: SYLVARCH walks the glade at the Elder's feet. Be gentle. It is older than the village.");
}

/* ---------------- the Clockwork Spire ---------------- */

static void scr_clockmaker(int npc)
{
    (void)npc;
    if (lore_reveal(LSRC_CLOCKMAKER, 0)) return;
    dlg_say("HORA: The stair to the Crown is sealed by that stone. It would take real STRENGTH to shift it.");
}

/* ---------------- Brookmill and the mine ---------------- */
static void scr_holt(int npc)
{
    (void)npc;
    if (flag(FLAG_FEN_RIVETS)) {
        dlg_say("HOLT: Our carpenters have the rivets. The Heron Fen boardwalk can be mended.");
        return;
    }
    if (!flag(FLAG_VOLT_CREST)) {
        dlg_say("HOLT: We need Lumen rivets for the Heron Fen boardwalk. FARA's Volt crest will get them.");
        return;
    }
    /* One script owns this gate flag. Vex's bundle is optional once the crest is held. */
    flag_set(FLAG_FEN_RIVETS);
    dlg_say(flag(FLAG_RIVET_BUNDLE) ?
        "HOLT: Those are our rivets! The Fen carpenters can finish the boardwalk." :
        "HOLT: You already hold the Volt crest. I'll order the rivets direct. The boardwalk is ours!");
}

static void scr_miller(int npc)
{
    (void)npc;
    if (quest_done(QUEST_GRIST_WHEEL)) {
        dlg_say("ADA: The wheel hums like a happy TIDE kin again.");
        return;
    }
    if (lore_reveal(LSRC_MILLER, 0)) return;
    if (bag[ITEM_CROP_CORN] >= 3 || bag[ITEM_IRON_ORE] >= 3) {
        int item = bag[ITEM_CROP_CORN] >= 3 ? ITEM_CROP_CORN : ITEM_IRON_ORE;
        bag_add(item, -3);
        quest_set(QUEST_GRIST_WHEEL, 255);
        give_item(ITEM_HONEY_BUN, 2);
        dlg_say("ADA: Three bags for a new cog! Take these honey buns for the road.");
        return;
    }
    quest_set(QUEST_GRIST_WHEEL, 1);
    dlg_say("ADA: Bring me three CORN or three IRON ORE and I'll mend the wheel's cog.");
}

static void scr_koirin_kid(int npc)
{
    (void)npc;
    if (quest_done(QUEST_KOIRIN_SONG)) { dlg_say("KID: KOIRIN really can climb waterfalls!"); return; }
    for (int i = 0; i < party_count; i++)
        if (party[i].species == SP_KOIRIN) {
            quest_set(QUEST_KOIRIN_SONG, 255);
            give_item(ITEM_LURE_INCENSE, 1);
            dlg_say("KID: A KOIRIN! You found it! Here's my lucky lure.");
            return;
        }
    quest_set(QUEST_KOIRIN_SONG, 1);
    dlg_say("KID: They say KOIRIN climb the mill waterfall. Show me one someday!");
}

static const u8 BROOK_STOCK[] = {
    ITEM_LANTERN, ITEM_TONIC, ITEM_BIG_TONIC, ITEM_HONEY_BUN, ITEM_LURE_INCENSE,
};
static void scr_brook_shop(int npc)
{
    (void)npc;
    shop_open_stock(BROOK_STOCK, (int)sizeof(BROOK_STOCK));
}

static void scr_brook_secret(int npc)
{
    (void)npc;
    if (travel_ability_kin(AB_LIGHT) < 0) {
        dlg_say("Under the toll bridge is a hollow too dark to search. A kin's LIGHT could help.");
        return;
    }
    if (!flag(FLAG_BROOK_LIGHT_CACHE)) {
        flag_set(FLAG_BROOK_LIGHT_CACHE);
        give_item(ITEM_GLOW_LANTERN, 3);
        dlg_say("The hollow holds three glow lanterns and the toll keeper's notes.");
        lore_story(LORE_BROOK_TOLL);
        return;
    }
    dlg_say("Only heron feathers remain in the hollow.");
}

static void scr_mine_gallery(int npc)
{
    (void)npc;
    if (travel_ability_kin(AB_LIGHT) < 0) {
        dlg_say("FOREMAN: The mine is passable in the dark, but that gallery needs a kin's LIGHT.");
        return;
    }
    if (!flag(FLAG_MINE_LIGHT_CACHE)) {
        flag_set(FLAG_MINE_LIGHT_CACHE);
        lore_story(LORE_COPPER_RUSH);
        dlg_say("FOREMAN: The tablet marks a shard inside the newly opened gallery.");
        return;
    }
    dlg_say("FOREMAN: The side gallery's survey marks are legible again.");
}
