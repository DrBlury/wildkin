/*
 * world/farm/scripts.c -- NPC scripts: static void scr_x(int npc) { ... }
 * (register each in script_ids.inc and script_table.inc). Owner: FARM system.
 */

/* REEVE at the LAND OFFICE: sells the FARM DEED (docs/EXPANSION.md 7.2) (placeholder) */
static void scr_reeve(int npc)
{
    (void)npc;
    dlg_say("WILLOW ACRE, south of the village, is for sale. Come back when the paperwork is ready!");
}
