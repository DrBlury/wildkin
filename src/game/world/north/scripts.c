/*
 * world/north/scripts.c -- NPC scripts of the NORTH region (owner: W-NORTH):
 * the Frost Hearth tender, the Frost Shop, the Rime Hall guide and HALL
 * MASTER SIGRUN (RIME CREST), the ice carver's and the stargazer's quests,
 * the Starfall scholar, the hot-spring keeper and Granny Alder.
 * (Registered in script_ids.inc and script_table.inc.)
 */

/* ---------------- the Frost Hearth Hall ---------------- */

static void frost_heal_answer(int c)
{
    if (c == 1) {
        lore_reveal(LSRC_FROST_TENDER, "Snow outside, fire inside. That's the whole secret of Frosthollow.");
        return;
    }
    if (c != 0) {
        dlg_say("The hearth stays lit all winter. Come back any time.");
        return;
    }
    hearth_rest();
    travel.last_hearth = (u8)cur_map;
    dlg_say("Your kin curled up by the hearth and thawed out. They're full of vigor again!");
    if (opt.autosave && save_write()) dlg_say("(Your progress was saved.)");
}

static void scr_frost_tender(int npc)
{
    (void)npc;
    dlg_ask("Welcome to the FROST HEARTH HALL. Shall your kin rest by the fire?", HEARTH_MENU, 3,
            frost_heal_answer);
}

/* ---------------- the Frost Shop ---------------- */

static const u8 FROST_STOCK[] = {
    ITEM_LANTERN, ITEM_GLOW_LANTERN, ITEM_STAR_LANTERN, ITEM_BIG_TONIC, ITEM_GRAND_TONIC,
    ITEM_SOOTHE_BALM, ITEM_WAKE_BELL, ITEM_MINT_TEA, ITEM_WAYSTONE, ITEM_LURE_INCENSE,
    ITEM_SWIFT_COIL, ITEM_FROST_SHARD, ITEM_ASTRAL_SHARD,
};

static void frost_shop_answer(int c)
{
    if (c == 0) shop_open_stock(FROST_STOCK, (int)sizeof(FROST_STOCK));
    else if (c == 1) lore_reveal(LSRC_FROST_CLERK, "Everything here came up the pass on a yak. Everything.");
    else dlg_say("Stay warm out there!");
}

static void scr_frost_shop(int npc)
{
    (void)npc;
    dlg_ask("Welcome to the FROST SHOP! Mountain goods, fair prices.", SHOP_MENU, 3, frost_shop_answer);
}

/* ---------------- the Rime Hall ---------------- */

static void scr_rime_guide(int npc)
{
    (void)npc;
    if (flag(FLAG_RIME_CREST)) {
        dlg_say("The RIME CREST! With a strong flying kin you can FLY now, even to the SKY ISLE above the peak.");
        return;
    }
    if (lore_reveal(LSRC_RIME_GUIDE, 0)) return;
    dlg_say("Inside, the ice decides where you stop. Look for the rock that will stop you where you want to be. No rock? Push the pumice there.");
}

static void rime_master_end(int result)
{
    if (result != BR_WIN) {
        dlg_say("SIGRUN: The ice is patient. So am I. Come back when you are ready.");
        return;
    }
    trainer_mark_beaten(TR_N_SIGRUN);
    if (flag(FLAG_RIME_CREST)) return;
    flag_set(FLAG_RIME_CREST);
    travel_award_crest(CREST_RIME);
    sfx_play(SFX_ITEM);
    dlg_say("You received the RIME CREST! Clear ice-blue glass that never fogs.");
    lore_story(LORE_RIME_CREST);
    dlg_say("SIGRUN: With this crest, a strong kin that flies will carry you to any town you know.");
    dlg_say("And higher. Above the clouds over Whitecrown floats the SKY ISLE. Go and see who lives there.");
}

static void rime_master_answer(int c)
{
    if (c != 0) {
        dlg_say("SIGRUN: Then rest. The ice will still be here.");
        return;
    }
    static TrainerTeam t;
    t = team_from(&TRAINERS[TR_N_SIGRUN], BSCENE_SNOW);
    battle_end_hook = rime_master_end;
    battle_start_master(&t);
}

static void scr_rime_master(int npc)
{
    (void)npc;
    if (party_first_healthy() < 0) {
        dlg_say("SIGRUN: Your kin are dozing. The Hearth Hall is across the lane.");
        return;
    }
    if (!flag(FLAG_RIME_CREST)) {
        dlg_say("I am SIGRUN, Master of the Rime Hall. You crossed my ice. Few do it on the first day.");
        dlg_ask("Now cross me. Six kin, no mercy, no slipping. Ready?", YES_NO, 2, rime_master_answer);
    } else {
        dlg_ask("SIGRUN: Back for another bout? The ice never tires, and neither do I.", YES_NO, 2,
                rime_master_answer);
    }
}

/* ---------------- the ice carver: LAMPS FOR THE LONG NIGHT ---------------- */

static void scr_ice_carver(int npc)
{
    (void)npc;
    int q = quest_get(QUEST_GLOWCAPS);
    if (q == 0) {
        dlg_say("These statues glow at night with a GLOWCAP inside. The long night is coming, and I'm out of them.");
        dlg_say("GLOWCAPS grow in the GLIMMER CAVERNS, east of the plaza. Bring me three and I'll make it worth it.");
        quest_set(QUEST_GLOWCAPS, 1);
        return;
    }
    if (q == 1) {
        if (bag[ITEM_GLOWCAP] >= 3) {
            bag_add(ITEM_GLOWCAP, -3);
            quest_set(QUEST_GLOWCAPS, 255);
            dlg_say("Three GLOWCAPS! Look how they shine. The statues will glow all winter.");
            dlg_say("Here. The hall stocks these for wardens who chase fast kin.");
            give_item(ITEM_STAR_LANTERN, 3);
            give_item(ITEM_FROST_SHARD, 1);
            return;
        }
        dlg_say("Three GLOWCAPS, from the GLIMMER CAVERNS. They glow a little, so they're easy to spot in the dark.");
        return;
    }
    lore_reveal(LSRC_ICE_CARVER, "Every statue starts as a block of lake ice and a lot of patience.");
}

/* ---------------- the stargazer and the scholar: THE STAR CHART ---------------- */

static void scr_stargazer(int npc)
{
    (void)npc;
    int q = quest_get(QUEST_STAR_CHART);
    if (q == 0) {
        dlg_say("A visitor! I'm IDA. I map the stars, and the thing that crosses them at night.");
        dlg_say("My colleague DR. MAREN camps in the STARFALL GROTTO, under the GLIMMER CAVERNS. Would you take her my star chart?");
        dlg_say("You received IDA'S STAR CHART. (It's rolled up very tight.)");
        quest_set(QUEST_STAR_CHART, 1);
        return;
    }
    if (q == 1) {
        dlg_say("The grotto is below the caverns: take the stairs down, then follow the violet light.");
        return;
    }
    if (q == 2) {
        quest_set(QUEST_STAR_CHART, 255);
        dlg_say("A chip of real stardust from Maren! She says the moth is resting? Wonderful.");
        dlg_say("Keep the chip. And take this; I've no use for it up here with my telescope.");
        give_item(ITEM_ASTRAL_SHARD, 1);
        return;
    }
    lore_reveal(LSRC_STARGAZER, "Clear skies tonight. I'll be at the lens until dawn.");
}

static void scr_grotto_scholar(int npc)
{
    (void)npc;
    if (quest_get(QUEST_STAR_CHART) == 1) {
        quest_set(QUEST_STAR_CHART, 2);
        dlg_say("Ida's chart! She drew the moon's path over the roof hole to the hour. Brilliant.");
        dlg_say("Take her this in thanks. It fell through that hole a thousand years ago.");
        give_item(ITEM_STARDUST_CHIP, 1);
        return;
    }
    if (lore_reveal(LSRC_GROTTO_SCHOLAR, 0)) return;
    dlg_say("The moth rests on the moonstone dais. Walk softly. It's older than the Kinship.");
}

/* ---------------- the hot spring and the Alder house ---------------- */

static void spring_answer(int c)
{
    if (c != 0) {
        dlg_say("Suit yourself. The water will still be warm tomorrow.");
        return;
    }
    hearth_rest();
    dlg_say("You and your kin soak in the steaming water. Every ache melts away. Your kin are full of vigor!");
}

static void scr_spring_keeper(int npc)
{
    (void)npc;
    dlg_ask("The spring is warm today. Would you and your kin like a soak?", YES_NO, 2, spring_answer);
}

static void scr_alder_gran(int npc)
{
    (void)npc;
    if (!flag(FLAG_ALDER_GIFT)) {
        flag_set(FLAG_ALDER_GIFT);
        dlg_say("Come in, come in, you're letting the cold in! Here, something hot for your kin.");
        give_item(ITEM_MINT_TEA, 2);
        return;
    }
    dlg_say("On the longest night, HOARFANG howls on the Crown, and the snow listens. So my granny said.");
}
