/*
 * world/farm/scripts.c -- NPC scripts: static void scr_x(int npc) { ... }
 * (register each in script_ids.inc and script_table.inc). Owner: FARM system.
 */

/* REEVE: sells the FARM DEED for 15,000c (10,000c once you bring her 3
 * GLOWBERRY: QUEST_REEVE_BERRIES), then sells seeds and farm supplies. */
static const char *const REEVE_SALE_MENU[3] = { "BUY THE DEED", "A DISCOUNT?", "NOT NOW" };
static const char *const REEVE_MENU[3] = { "SEEDS", "CHAT", "BYE" };

static void reeve_buy(void)
{
    int price = farm_deed_price();
    char msg[120];
    if (money < price) {
        str_copy(msg, "The deed is ");
        str_put_int(msg, price);
        str_put(msg, "c, and you're ");
        str_put_int(msg, price - money);
        str_put(msg, "c short. The farm will wait for you.");
        dlg_say(msg);
        return;
    }
    money -= price;
    farm_grant_deed();
    dlg_say("Signed and sealed! WILLOW ACRE is yours. Here's the FARM DEED, a HOE, a WATERING CAN and some seeds to start you off.");
    dlg_say("Press L or R on the farm to switch between your tools and seeds, and A to use one. I've opened the gate for you.");
    dlg_say("Put your harvest in the SHIPPING BIN and you'll be paid each morning. Come back to me for more seeds!");
}

static void reeve_discount(void)
{
    int stage = quest_get(QUEST_REEVE_BERRIES);
    if (stage == 255) {
        dlg_say("A deal's a deal: 10,000c, and the berries were lovely.");
    } else if (stage == 0) {
        quest_set(QUEST_REEVE_BERRIES, 1);
        dlg_say("A discount? Hmm... I do love GLOWBERRY tart. The wild bushes up by the yard are ripe right now.");
        dlg_say("Bring me 3 GLOWBERRY and I'll take 5,000c off the deed.");
    } else {
        dlg_say("Three GLOWBERRY, from the wild bushes north of the fence. Then 10,000c and the farm is yours.");
    }
}

static void reeve_sale_answer(int c)
{
    if (c == 0) reeve_buy();
    else if (c == 1) reeve_discount();
    else dlg_say("Take your time. Good land doesn't spoil.");
}

static void reeve_answer(int c)
{
    if (c == 0) farm_shop_open();
    else if (c == 1) lore_reveal(LSRC_REEVE, "Rainy days are a farmer's holiday: the sky does your watering.");
    else dlg_say("Happy farming!");
}

static void scr_reeve(int npc)
{
    (void)npc;
    if (farm.owned) {
        dlg_ask("How's the farm? Need seeds?", REEVE_MENU, 3, reeve_answer);
        return;
    }
    if (quest_get(QUEST_REEVE_BERRIES) == 1 && bag[ITEM_CROP_GLOWBERRY] >= 3) {
        bag[ITEM_CROP_GLOWBERRY] -= 3;
        quest_set(QUEST_REEVE_BERRIES, 255);
        sfx_play(SFX_ITEM);
        dlg_say("GLOWBERRY! Three of them, and so bright. Thank you! As promised: the deed is yours for 10,000c.");
    }
    char msg[160];
    str_copy(msg, "I'm REEVE of the LAND OFFICE. WILLOW ACRE is for sale: fields, orchard, pond and farmhouse, for ");
    str_put_int(msg, farm_deed_price());
    str_put(msg, "c.");
    dlg_ask(msg, REEVE_SALE_MENU, 3, reeve_sale_answer);
}
