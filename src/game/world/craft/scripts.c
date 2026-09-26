/*
 * world/craft/scripts.c -- NPC scripts: static void scr_x(int npc) { ... }
 * (register each in script_ids.inc and script_table.inc). Owner: CRAFT system.
 *
 * The three crafting teachers (craft.c has the rules). Each one:
 *   first talk  hands over the RECIPE BOOK (once) and a few ingredients
 *   LESSON      teaches their next recipe once you've made enough things
 *               at their station (craft_lesson)
 *   COOK / BREW / FORGE  lends their station: opens the crafting screen
 *   BUY         their ingredients and their book
 *   CHAT        crafting lore (LSRC_CHEF / BREWER / SMITH)
 */

static const u8 CHEF_STOCK[] = { ITEM_GLOW_HONEY, ITEM_SALT, ITEM_MINT_LEAF, ITEM_GLOWCAP, ITEM_COOKBOOK };
static const u8 BREWER_STOCK[] = { ITEM_MINT_LEAF, ITEM_GLOW_HONEY, ITEM_GLOWCAP, ITEM_BONE_MEAL, ITEM_SALT,
                                   ITEM_BREW_NOTES };
static const u8 SMITH_STOCK[] = { ITEM_HEARTGLASS_SAND, ITEM_IRON_ORE, ITEM_COAL, ITEM_SILK_THREAD,
                                  ITEM_STARDUST_CHIP, ITEM_FORGE_MANUAL };

static const char *const CHEF_MENU[5] = { "LESSON", "COOK", "BUY", "CHAT", "BYE" };
static const char *const BREWER_MENU[5] = { "LESSON", "BREW", "BUY", "CHAT", "BYE" };
static const char *const SMITH_MENU[5] = { "LESSON", "FORGE", "BUY", "CHAT", "BYE" };

static void teacher_answer(int station, int c)
{
    static const char *const IDLE[3] = {
        "Salt makes everything taste more like itself. Remember that.",
        "Mint for clarity, glowcap for strength, honey to make it all go down.",
        "Coal, ore, sand. And a steady arm. That's all a forge needs.",
    };
    static const char *const BYE[3] = {
        "Come back hungry!",
        "Mind the fumes on your way out.",
        "Keep your lanterns ringing.",
    };
    switch (c) {
    case 0: craft_lesson(station); break;
    case 1: craft_open(station); break;
    case 2:
        if (station == STATION_COOK) shop_open_stock(CHEF_STOCK, (int)sizeof(CHEF_STOCK));
        else if (station == STATION_BREW) shop_open_stock(BREWER_STOCK, (int)sizeof(BREWER_STOCK));
        else shop_open_stock(SMITH_STOCK, (int)sizeof(SMITH_STOCK));
        break;
    case 3:
        lore_reveal(station == STATION_COOK ? LSRC_CHEF : station == STATION_BREW ? LSRC_BREWER : LSRC_SMITH,
                    IDLE[station]);
        break;
    default: dlg_say(BYE[station]); break;
    }
}

static void chef_answer(int c) { teacher_answer(STATION_COOK, c); }
static void brewer_answer(int c) { teacher_answer(STATION_BREW, c); }
static void smith_answer(int c) { teacher_answer(STATION_FORGE, c); }

/* a cook who teaches recipes and lends the kitchen */
static void scr_chef(int npc)
{
    (void)npc;
    if (!craft_met(STATION_COOK)) {
        dlg_say("Oh, a warden! I'm ROSA. I cook for half the village, and for their kin.\f"
                "A good meal makes a good bout, you know. Let me get you started.");
        craft_welcome(STATION_COOK);
        dlg_say("Try a BERRY TART on the stove. Toss the pan, then stir! Talk to me for lessons.");
        return;
    }
    dlg_ask("What'll it be, dear?", CHEF_MENU, 5, chef_answer);
}

/* the apothecary brewer: cauldron and potion recipes */
static void scr_brewer(int npc)
{
    (void)npc;
    if (!craft_met(STATION_BREW)) {
        dlg_say("Mm? A visitor. I'm MOSS. Every tonic sold in the Vale was once brewed in a pot like "
                "this one.\fYou want to learn? Then take these, and mind the heat.");
        craft_welcome(STATION_BREW);
        dlg_say("A GLOW TONIC is the first brew. Hold the heat in the band, then bottle at the bubble's peak.");
        return;
    }
    dlg_ask("The cauldron's warm. What do you need?", BREWER_MENU, 5, brewer_answer);
}

/* the forge smith: lanterns and tools */
static void scr_smith(int npc)
{
    (void)npc;
    if (!craft_met(STATION_FORGE)) {
        dlg_say("Name's BRANN. I make the frames every lantern in the Vale sits in.\f"
                "You've got the look of someone who breaks things. Good. Learn to make them too.");
        craft_welcome(STATION_FORGE);
        dlg_say("Start with a plain LANTERN. Strike on the beat, then quench it.");
        return;
    }
    dlg_ask("Forge is hot. What'll it be?", SMITH_MENU, 5, smith_answer);
}
