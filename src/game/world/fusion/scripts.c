/*
 * world/fusion/scripts.c -- NPC scripts: static void scr_x(int npc) { ... }
 * (register each in script_ids.inc and script_table.inc). Owner: FUSION system.
 */

/* the RESONANCE WORKS front desk: opens the machines (placeholder) */
static void scr_fusion_desk(int npc)
{
    (void)npc;
    dlg_say("The Resonance Works is still calibrating. Come back soon!");
}
