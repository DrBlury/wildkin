/*
 * world/craft/scripts.c -- NPC scripts: static void scr_x(int npc) { ... }
 * (register each in script_ids.inc and script_table.inc). Owner: CRAFT system.
 */

/* a cook who teaches recipes and lends the kitchen (placeholder) */
static void scr_chef(int npc)
{
    (void)npc;
    dlg_say("A good meal makes a good bout. Come back and I'll teach you a recipe.");
}

/* the apothecary brewer: cauldron and potion recipes (placeholder) */
static void scr_brewer(int npc)
{
    (void)npc;
    dlg_say("The cauldron needs a steady hand. Come back later.");
}

/* the forge smith: lanterns and tools (placeholder) */
static void scr_smith(int npc)
{
    (void)npc;
    dlg_say("The forge isn't hot yet.");
}
