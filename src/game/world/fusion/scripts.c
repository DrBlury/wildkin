/*
 * world/fusion/scripts.c -- NPC scripts: static void scr_x(int npc) { ... }
 * (register each in script_ids.inc and script_table.inc). Owner: FUSION system.
 */

/* ---------------- the RESONANCE WORKS front desk ---------------- */

static const char *const WORKS_DESK_MENU[3] = { "MACHINES", "CHAT", "BYE" };

static void works_desk_answer(int c)
{
    if (c == 0) {
        fusion_open(FUSION_SCREEN_MENU);
    } else if (c == 1) {
        lore_reveal(LSRC_WORKS, fusion.hits ? "A woven kin! I never get tired of seeing one. Take good care of it."
                                            : "The Loom remembers every miss, you know. It gets kinder the more you try.");
    } else {
        dlg_say("Mind the copper pipes on your way out. They hum when they're full!");
    }
}

static void works_desk_menu(int unused)
{
    (void)unused;
    dlg_ask("What can the Works do for you?", WORKS_DESK_MENU, 3, works_desk_answer);
}

static void works_desk_gift(int unused)
{
    (void)unused;
    bag_add(ITEM_ENERGY_FLASK, 1);
    sfx_play(SFX_ITEM);
    dlg_say("You received the ENERGY FLASK!");
    dlg_say("It shows every drop of typed energy you own. Use it from your bag, or register it to SELECT.");
}

/* the RESONANCE WORKS front desk: explains once, gives the ENERGY FLASK,
 * then opens the machines */
static void scr_fusion_desk(int npc)
{
    (void)npc;
    if (!(fusion.flags & FZF_INTRO)) {
        fusion.flags |= FZF_INTRO;
        dlg_say("Welcome to the RESONANCE WORKS! I'm NELL. We work with the energy inside kin kernels.");
        dlg_say("The EXTRACTOR unbinds a kin into typed energy. Its body goes home to the wild, safe and sound.");
        dlg_say("The MIXER turns two energies into a third. And the LOOM can weave energies into a brand new kin!");
        dlg_call(works_desk_gift, 0);
    } else {
        dlg_say("Welcome back to the Works!");
    }
    dlg_call(works_desk_menu, 0);
}
