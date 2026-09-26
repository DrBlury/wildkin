/*
 * world/village/scripts.c -- NPC scripts: static void scr_x(int npc) { ... }
 * (register each in script_ids.inc and script_table.inc). Owner: core (the original Maple Village area).
 */

static void scr_keeper(int npc) { (void)npc; script_keeper(); }
static void scr_aide(int npc) { (void)npc; script_aide(); }
static void scr_gran(int npc) { (void)npc; script_gran(); }
static void scr_baker(int npc) { (void)npc; script_baker(); }
static void scr_gardener(int npc) { (void)npc; script_gardener(); }
static void scr_marlo(int npc) { (void)npc; script_marlo(); }
static void scr_hermit(int npc) { (void)npc; script_hermit(); }
static void scr_vass(int npc) { (void)npc; script_vass(); }
static void scr_woodward(int npc) { (void)npc; script_woodward(); }
static void scr_kid(int npc) { (void)npc; script_kid(); }

static void scr_shop(int npc)
{
    (void)npc;
    dlg_ask("Welcome to MAPLE SHOP! What can I do for you?", SHOP_MENU, 3, shop_answer);
}

static void scr_tender(int npc)
{
    (void)npc;
    dlg_ask("Welcome to the HEARTH HALL. Would your kin like to rest by the hearth?", HEARTH_MENU, 3,
            heal_answer);
}
