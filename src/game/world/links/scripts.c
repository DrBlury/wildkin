/* Scripted cave crossings cannot be used before the shortcut's story crest. */
static int links_scorch_ready(void) { return flag(FLAG_LANTERN_CREST); }
static int links_aurora_ready(void) { return flag(FLAG_LANTERN_CREST) && flag(FLAG_CREST_DREAM); }
static int links_fjord_ready(void) { return flag(FLAG_CREST_ANVIL); }

static void links_cross_scorch(int unused)
{
    (void)unused;
    field_begin_warp(MAP_DUSKMERE, 38, 34, DIR_LEFT);
}

static void scr_links_scorch_cave(int npc)
{
    (void)npc;
    if (!links_scorch_ready()) {
        dlg_say("The ashfall hides the March. Return with MORWEN's lantern crest.");
        return;
    }
    dlg_say("The rockfall has settled. The passage leads to DUSKMERE.");
    dlg_call(links_cross_scorch, 0);
}

static void links_cross_aurora(int unused)
{
    (void)unused;
    field_begin_warp(MAP_DREAMSPIRE, 4, 29, DIR_RIGHT);
}

static void scr_links_aurora_cave(int npc)
{
    (void)npc;
    if (!links_aurora_ready()) {
        dlg_say("The frozen fall bars the cave. The Lantern and Dream crests must both answer it.");
        return;
    }
    dlg_say("The frozen fall opens onto DREAMSPIRE.");
    dlg_call(links_cross_aurora, 0);
}

static void links_cross_fjord(int unused)
{
    (void)unused;
    field_begin_warp(MAP_FROSTPINE, 3, 29, DIR_RIGHT);
}

static void scr_links_fjord_cave(int npc)
{
    (void)npc;
    if (!links_fjord_ready()) {
        dlg_say("A rockfall seals the sea cave. Only STRENGTH can clear it.");
        return;
    }
    dlg_say("The sea cave climbs toward FROSTPINE PASS.");
    dlg_call(links_cross_fjord, 0);
}
