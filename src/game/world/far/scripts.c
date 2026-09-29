/*
 * world/far/scripts.c -- NPC scripts of the FAR region (owner: W-FAR):
 * the hearths and shops of Cindermoor and Dreamspire, the two Hall Masters
 * (BRONWEN, ANVIL CREST; VESPER, DREAM CREST), IRON FOR THE BELL, THE
 * DRIFTING VERSES, and a few gifts.
 */

/* ---------------- hearths and shops ---------------- */

static void far_heal_answer(int c)
{
    if (c == 1) {
        dlg_say(cur_map == MAP_CINDER_HEARTH
                ? "Our hearth burns volcano coal. It never goes out, and neither does the smell."
                : "Our hearth is lit with moonstone glow. Kin sleep here like they've come home.");
        return;
    }
    if (c != 0) {
        dlg_say("The hearth is always lit. Come back any time.");
        return;
    }
    hearth_rest();
    dlg_say("Your kin curled up by the hearth and soaked up its warmth. They're full of vigor again!");
    if (opt.autosave && save_write()) dlg_say("(Your progress was saved.)");
}

static void scr_far_tender(int npc)
{
    (void)npc;
    dlg_ask(cur_map == MAP_CINDER_HEARTH
            ? "Welcome to the CINDER HEARTH HALL. Would your kin like to rest by the hearth?"
            : "Welcome to the SPIRE HEARTH HALL. Would your kin like to rest by the hearth?",
            HEARTH_MENU, 3, far_heal_answer);
}

static const u8 CINDER_STOCK[] = {
    ITEM_LANTERN, ITEM_GLOW_LANTERN, ITEM_STAR_LANTERN, ITEM_BIG_TONIC, ITEM_GRAND_TONIC,
    ITEM_SOOTHE_BALM, ITEM_WAKE_BELL, ITEM_BRAVE_CHILI, ITEM_IRONBARK, ITEM_WAYSTONE, ITEM_COAL,
};

static const u8 DREAM_STOCK[] = {
    ITEM_LANTERN, ITEM_GLOW_LANTERN, ITEM_STAR_LANTERN, ITEM_GRAND_TONIC, ITEM_MINT_TEA,
    ITEM_SWIFT_COIL, ITEM_FOCUS_COIL, ITEM_WILL_COIL, ITEM_HUSH_BELL, ITEM_LURE_INCENSE,
    ITEM_WAYSTONE, ITEM_MINT_LEAF, ITEM_STARDUST_CHIP,
};

static void cinder_shop_answer(int c)
{
    if (c == 0) shop_open_stock(CINDER_STOCK, (int)sizeof(CINDER_STOCK));
    else if (c == 1) dlg_say("Everything's forged or brewed right here. The lanterns come from the FORGE, still warm.");
    else dlg_say("Mind the heat on your way out!");
}

static void dream_shop_answer(int c)
{
    if (c == 0) shop_open_stock(DREAM_STOCK, (int)sizeof(DREAM_STOCK));
    else if (c == 1) dlg_say("LURE INCENSE smells of moonpetals. Rare kin can't resist a good dream.");
    else dlg_say("Sweet dreams!");
}

static void scr_cinder_clerk(int npc)
{
    (void)npc;
    dlg_ask("Welcome to the CINDER SHOP! What can I do for you?", SHOP_MENU, 3, cinder_shop_answer);
}

static void scr_dream_clerk(int npc)
{
    (void)npc;
    dlg_ask("Welcome to the SPIRE SHOP. Browse as slowly as you like.", SHOP_MENU, 3, dream_shop_answer);
}

/* ---------------- Hall Masters ---------------- */

static int far_master_tr = -1;

static void far_master_end(int result)
{
    int tr = far_master_tr;
    far_master_tr = -1;
    if (result != BR_WIN || tr < 0) return;
    trainer_mark_beaten(tr);
    sfx_play(SFX_ITEM);
    if (tr == TR_MASTER_BRONWEN) {
        flag_set(FLAG_CREST_ANVIL);
        travel_award_crest(CREST_ANVIL);
        dlg_say("You received the ANVIL CREST!");
        dlg_say("BRONWEN: With that crest, a strong kin in your team can push real boulders. Try the EMBER TUNNEL.");
        give_item(ITEM_HEAVY_LANTERN, 3);
    } else {
        flag_set(FLAG_CREST_DREAM);
        travel_award_crest(CREST_DREAM);
        dlg_say("You received the DREAM CREST!");
        dlg_say("VESPER: A TELEPORT kin will carry you back to the last Hearth Hall you rested at. Dream of home.");
        give_item(ITEM_QUICK_LANTERN, 3);
    }
}

static void far_master_begin(int tr)
{
    static TrainerTeam team;
    team = team_from(&TRAINERS[tr], tr == TR_MASTER_BRONWEN ? BSCENE_VOLCANO : BSCENE_DREAM);
    far_master_tr = tr;
    battle_end_hook = far_master_end;
    battle_start_master(&team);
}

static void far_master_talk(int tr, int crest_flag, const char *after)
{
    if (flag(crest_flag)) {
        dlg_say(after);
        return;
    }
    if (party_first_healthy() < 0) {
        dlg_say("Your kin are dozing. Rest them at the HEARTH HALL, then come back.");
        return;
    }
    dlg_say(TRAINERS[tr].intro);
    dlg_call(far_master_begin, tr);
}

static void scr_anvil_master(int npc)
{
    (void)npc;
    if (!flag(FLAG_CREST_ANVIL))
        dlg_say("BRONWEN: You pushed your way up here. Good. Now let's see if your kin are as stubborn as you.");
    far_master_talk(TR_MASTER_BRONWEN, FLAG_CREST_ANVIL,
                    "BRONWEN: Wear that crest with pride. And come by the FORGE; DAGNY owes me a favour.");
}

static void scr_dream_master(int npc)
{
    (void)npc;
    if (!flag(FLAG_CREST_DREAM))
        dlg_say("VESPER: I dreamed you would come by the long way round. The mirrors agreed.");
    far_master_talk(TR_MASTER_VESPER, FLAG_CREST_DREAM,
                    "VESPER: Sleep well, warden. I'll be watching your bouts in the mirrors.");
}

/* ---------------- IRON FOR THE BELL ---------------- */

static void scr_founder(int npc)
{
    (void)npc;
    int stage = quest_get(QUEST_IRON_BELL);
    if (stage == 255) {
        dlg_say("HALVARD: Hear that? Neither do I. That's the sound of a bell that isn't cracked. Thank you!");
        return;
    }
    if (stage == 0) {
        quest_set(QUEST_IRON_BELL, 1);
        dlg_say("HALVARD: See that crack? The bell rings flat, and a flat bell won't carry to the tunnel.");
        dlg_say("I can recast it, but the forge is out of good iron. Bring me 3 IRON ORE. The EMBER TUNNEL has plenty.");
        return;
    }
    if (bag[ITEM_IRON_ORE] < 3) {
        char msg[96];
        str_copy(msg, "HALVARD: 3 IRON ORE, that's all I need. You've got ");
        str_put_int(msg, bag[ITEM_IRON_ORE]);
        str_put(msg, " so far.");
        dlg_say(msg);
        return;
    }
    bag_add(ITEM_IRON_ORE, -3);
    quest_set(QUEST_IRON_BELL, 255);
    dlg_say("HALVARD: Good heavy ore! Into the furnace with it. By tomorrow the bell will sing true.");
    dlg_say("Here, for your trouble. A seed crystal of iron: METAL kin love them.");
    give_item(ITEM_METAL_SHARD, 1);
    money += 1500;
    dlg_say("HALVARD also paid you 1500 coins.");
}

/* ---------------- gifts ---------------- */

static void scr_tunnel_miner(int npc)
{
    (void)npc;
    if (!flag(FLAG_FAR_MINER_GIFT)) {
        flag_set(FLAG_FAR_MINER_GIFT);
        dlg_say("OLD MINER: Heading deeper? Take these. Heavy kin are easier to befriend with a heavy lantern.");
        give_item(ITEM_HEAVY_LANTERN, 2);
        return;
    }
    lore_reveal(LSRC_FAR_MINER, "OLD MINER: The boulders past the lava chamber? Only a strong kin with the ANVIL CREST shifts those.");
}

static void scr_far_stargazer(int npc)
{
    (void)npc;
    if (lore_reveal(LSRC_FAR_STARGAZER, 0)) return;
    if (!flag(FLAG_STARGAZER_GIFT)) {
        flag_set(FLAG_STARGAZER_GIFT);
        dlg_say("STARGAZER: I found these in the grass after a meteor shower. Starlight you can hold!");
        give_item(ITEM_STARDUST_CHIP, 2);
        return;
    }
    dlg_say("STARGAZER: Come back on a clear night. The QILUMEN only crosses when the sky is perfect.");
}

/* ---------------- THE DRIFTING VERSES ---------------- */

static int far_verses(void)
{
    return (flag(FLAG_VERSE_1) ? 1 : 0) + (flag(FLAG_VERSE_2) ? 1 : 0) + (flag(FLAG_VERSE_3) ? 1 : 0);
}

static const char *const FAR_VERSES[3] = {
    "\"The moon is a lantern the whole sky keeps,\"",
    "\"and every kin dreams while the warden sleeps;\"",
    "\"so rest, little light, till the morning comes round.\"",
};

static void scr_sleeper(int npc)
{
    (void)npc;
    int i = cur_map == MAP_MOONVEIL ? 0 : cur_map == MAP_DREAMSPIRE ? 1 : 2;
    int f = FLAG_VERSE_1 + i;
    int stage = quest_get(QUEST_DRIFTING_VERSES);
    if (stage == 0) {
        dlg_say("Zzz... the moon... a lantern... zzz... (They're fast asleep and mumbling.)");
        return;
    }
    if (stage == 255) {
        dlg_say("Zzz... (They smile in their sleep.)");
        return;
    }
    dlg_say("The dreamer mumbles in their sleep:");
    dlg_say(FAR_VERSES[i]);
    if (flag(f)) return;
    flag_set(f);
    sfx_play(SFX_ITEM);
    quest_set(QUEST_DRIFTING_VERSES, 1 + far_verses());
    if (far_verses() == 3) {
        dlg_say("That's the whole poem! Take it back to POET ISOLDE in DREAMSPIRE.");
    } else {
        char msg[64];
        str_copy(msg, "(A verse of ISOLDE's poem! ");
        str_put_int(msg, far_verses());
        str_put(msg, " of 3.)");
        dlg_say(msg);
    }
}

static void scr_poet(int npc)
{
    (void)npc;
    int stage = quest_get(QUEST_DRIFTING_VERSES);
    if (stage == 255) {
        dlg_say("ISOLDE: I read the poem to the SLUMBAKU statue every night now. It seems to like it.");
        return;
    }
    if (stage == 0) {
        quest_set(QUEST_DRIFTING_VERSES, 1);
        dlg_say("ISOLDE: I wrote my best poem in a dream, and woke up with nothing but the title.");
        dlg_say("But dreams drift here. Three sleepers have been mumbling my verses: one on MOONVEIL PATH, one in town, one in the DUST LIBRARY.");
        dlg_say("Listen to them for me? Sleepers only talk to the patient.");
        return;
    }
    if (far_verses() < 3) {
        dlg_say("ISOLDE: Any verses? The sleepers are on MOONVEIL PATH, here in DREAMSPIRE and in the DUST LIBRARY.");
        return;
    }
    quest_set(QUEST_DRIFTING_VERSES, 255);
    dlg_say("You recite the three verses. ISOLDE closes her eyes and mouths every word.");
    for (int i = 0; i < 3; i++) dlg_say(FAR_VERSES[i]);
    dlg_say("ISOLDE: That's it. That's exactly it. Oh, thank you. Take these, and sweet dreams.");
    give_item(ITEM_MOONCAKE, 3);
    give_item(ITEM_LURE_INCENSE, 2);
}


/* Railhead and Pilgrim Rest are safe mid-route stops, including the return trip. */
static void scr_route_heal(int npc)
{
    (void)npc;
    hearth_rest();
    dlg_say("The hearth warms your kin. They're ready for the road again.");
}
static void scr_rail_tender(int npc) { scr_route_heal(npc); }
static void scr_pilgrim_tender(int npc) { scr_route_heal(npc); }
static void scr_rail_cook(int npc)
{
    (void)npc;
    dlg_say("RAIL COOK: CHILI POT takes BRAVE CHILI and a pinch of the crossing's hot salt.");
    shop_open_stock(CINDER_STOCK, (int)sizeof(CINDER_STOCK));
}
static void scr_far_greta(int npc)
{
    (void)npc;
    if (!flag(FLAG_CREST_ANVIL)) {
        dlg_say("GRETA: The spring flood took the Cinder bridge. SURF will get you here; rebuilding takes an Anvil warden.");
        return;
    }
    /* The project state and offer function belong to plan 10. Until it lands,
     * Greta gives the player the actionable location without pretending the
     * bridge has already been rebuilt. */
    dlg_say("GRETA: You have the ANVIL CREST! Bring ore to our town project board when the bridge works begin.");
}

/* Both marked controls are reachable from the south bank. The solved basalt
 * patch is permanent, so returning from the north can never strand a warden. */
static void scr_ember_intake(int npc)
{
    (void)npc;
    if (flag(FLAG_EMBER_COOLED)) {
        dlg_say("INTAKE VALVE: The basalt seam has set. The crossing is safe.");
        return;
    }
    flag_set(FLAG_EMBER_PRIMED);
    dlg_say("You open the intake. Cool air roars beneath the lava. Now release the sluice.");
}

static void scr_ember_release(int npc)
{
    (void)npc;
    if (flag(FLAG_EMBER_COOLED)) {
        dlg_say("RELEASE VALVE: The cooled basalt will hold.");
        return;
    }
    if (!flag(FLAG_EMBER_PRIMED)) {
        dlg_say("The release wheel will not turn. The intake must open first.");
        return;
    }
    flag_set(FLAG_EMBER_COOLED);
    map_patches_reapply();
    dlg_say("The sluice hisses. A pair of basalt stones sets across the molten seam!");
}
