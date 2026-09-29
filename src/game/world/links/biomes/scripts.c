static const u8 SUNWELL_STOCK[] = {
    ITEM_TONIC, ITEM_BIG_TONIC, ITEM_MINT_TEA, ITEM_WAYSTONE,
};

static void sunwell_repair_answer(int answer)
{
    if (answer != 0) {
        dlg_say("KEEPER: The old valve can wait. Nothing has been taken.");
        return;
    }
    if (quest_done(QUEST_SUNWELL_IRRIGATION) || flag(FLAG_SUNWELL_IRRIGATED)) {
        dlg_say("KEEPER: The gardens are green again. Thank you.");
        return;
    }
    if (bag[ITEM_IRON_ORE] < 2 || bag[ITEM_METAL_SHARD] < 1) {
        dlg_say("KEEPER: We still need two IRON ORE and one METAL SHARD.");
        return;
    }
    if (bag[ITEM_GRAND_TONIC] > 997) {
        dlg_say("KEEPER: Your bag is full. Make room for two GRAND TONICS first.");
        return;
    }
    bag_add(ITEM_IRON_ORE, -2);
    bag_add(ITEM_METAL_SHARD, -1);
    flag_set(FLAG_SUNWELL_IRRIGATED);
    quest_set(QUEST_SUNWELL_IRRIGATION, 255);
    give_item(ITEM_GRAND_TONIC, 2);
    dlg_say("KEEPER: Water flows through the beds again! Take two GRAND TONICS.");
}

static void scr_sunwell_repair(int npc)
{
    (void)npc;
    if (quest_done(QUEST_SUNWELL_IRRIGATION) || flag(FLAG_SUNWELL_IRRIGATED)) {
        dlg_say("KEEPER: The cistern is holding. Sunwell's gardens can grow again.");
        return;
    }
    if (quest_get(QUEST_SUNWELL_IRRIGATION) == 0)
        quest_set(QUEST_SUNWELL_IRRIGATION, 1);
    dlg_ask("KEEPER: Repair the irrigation valve with two IRON ORE and one METAL SHARD?",
            YES_NO, 2, sunwell_repair_answer);
}

static void scr_sunwell_heal(int npc)
{
    (void)npc;
    hearth_rest();
    dlg_say("Your kin rested in the cool cistern shade.");
}

static void scr_sunwell_shop(int npc)
{
    (void)npc;
    shop_open_stock(SUNWELL_STOCK, (int)sizeof(SUNWELL_STOCK));
}

static void scr_sunwell_jars(int npc)
{
    (void)npc;
    dlg_say(flag(FLAG_SUNWELL_IRRIGATED) ?
            "The water jars are full. New shoots line the irrigation channel." :
            "The jars are almost dry. The cistern keeper knows where the water went.");
}
