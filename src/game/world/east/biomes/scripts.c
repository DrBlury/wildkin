/* Village repairs commit resources only after explicit consent and stock checks. */
static void mistbell_repair_answer(int choice)
{
    if (choice != 0 || flag(FLAG_MISTBELL_BELL)) return;
    if (bag[ITEM_IRON_ORE] < 2) {
        dlg_say("BELLKEEPER: We still need two IRON ORE. Nothing was taken.");
        return;
    }
    if (bag[ITEM_BIG_TONIC] > 997) {
        dlg_say("BELLKEEPER: Make room for two BIG TONICS first. Keep your ore until then.");
        return;
    }
    bag_add(ITEM_IRON_ORE, -2);
    flag_set(FLAG_MISTBELL_BELL);
    quest_set(QUEST_MISTBELL_BELL, 255);
    give_item(ITEM_BIG_TONIC, 2);
    dlg_say("BELLKEEPER: The signal rings again! The shelter path is open.");
}

static void scr_mistbell_bell(int npc)
{
    (void)npc;
    if (flag(FLAG_MISTBELL_BELL)) {
        dlg_say("BELLKEEPER: Listen. The signal carries right across the falls.");
        return;
    }
    if (!quest_get(QUEST_MISTBELL_BELL)) quest_set(QUEST_MISTBELL_BELL, 1);
    dlg_ask("BELLKEEPER: The signal bell needs two IRON ORE. Repair it?",
            YES_NO, 2, mistbell_repair_answer);
}

static void canopy_restore_answer(int choice)
{
    if (choice != 0 || flag(FLAG_CANOPY_MARKER)) return;
    if (bag[ITEM_GLOWCAP] < 3) {
        dlg_say("WEAVER: Three GLOWCAP will light the marker. Keep your supplies.");
        return;
    }
    if (bag[ITEM_REVIVAL_BREW] >= 999) {
        dlg_say("WEAVER: Make room for a REVIVAL BREW first. Your glowcaps can wait.");
        return;
    }
    bag_add(ITEM_GLOWCAP, -3);
    flag_set(FLAG_CANOPY_MARKER);
    quest_set(QUEST_CANOPY_MARKER, 255);
    give_item(ITEM_REVIVAL_BREW, 1);
    dlg_say("WEAVER: The waymarker glows! The lower root path is safe now.");
}

static void scr_canopy_marker(int npc)
{
    (void)npc;
    if (flag(FLAG_CANOPY_MARKER)) {
        dlg_say("WEAVER: The old marker still guides travelers home.");
        return;
    }
    if (!quest_get(QUEST_CANOPY_MARKER)) quest_set(QUEST_CANOPY_MARKER, 1);
    dlg_ask("WEAVER: Could you spare three GLOWCAP to restore the waymarker?",
            YES_NO, 2, canopy_restore_answer);
}

static const u8 CANOPY_STOCK[] = {
    ITEM_TONIC, ITEM_BIG_TONIC, ITEM_HONEY_BUN, ITEM_LANTERN,
};
static void scr_canopy_keeper(int npc)
{
    (void)npc;
    shop_open_stock(CANOPY_STOCK, (int)sizeof(CANOPY_STOCK));
}

static void scr_mistbell_keeper(int npc)
{
    (void)npc;
    dlg_say("TENDER: The bellhouse is a safe place to rest before the crossing.");
}
