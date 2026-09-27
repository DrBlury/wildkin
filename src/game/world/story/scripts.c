/* Story dialogue and local callbacks. Region NPC placement is deferred until E3. */
__attribute__((unused)) static int story_act(void)
{
    if (flag(FLAG_OSSUREX_ANSWERED)) return 9;
    if (flag(FLAG_CREST_DREAM)) return 8;
    if (flag(FLAG_LANTERN_CREST)) return 7;
    if (flag(FLAG_RIME_CREST)) return 6;
    if (flag(FLAG_CREST_ANVIL)) return 5;
    if (flag(FLAG_TIDE_CREST)) return 4;
    if (flag(FLAG_VOLT_CREST)) return 3;
    if (flag(FLAG_STORM_CALMED)) return 2;
    return 1;
}

/* Ordered from newest to oldest: an older unread wire cannot suppress a
 * newer direction. Each wire is marked read before its message is queued. */
static int story_hearth_talk(void)
{
    static const struct { int trigger, read; const char *message; } wires[] = {
        { FLAG_CREST_DREAM, FLAG_STORY_WIRE_DREAM,
          "Linden's wire: Six crests. I'll meet you at the DUSKMERE gate. Let us answer OSSUREX together." },
        { FLAG_LANTERN_CREST, FLAG_STORY_WIRE_LANTERN,
          "Linden's wire: Your WARD LANTERN can part Moonveil's mist. Follow it north of LUMEN." },
        { FLAG_RIME_CREST, FLAG_STORY_WIRE_RIME,
          "Linden's wire: The Accord will open the March. Captain Audra waits south of COPPERLINE." },
        { FLAG_CREST_ANVIL, FLAG_STORY_WIRE_ANVIL,
          "Linden's wire: STRENGTH can clear the Rise rockslide. Come home through MAPLE and climb north." },
        { FLAG_TIDE_CREST, FLAG_STORY_WIRE_TIDE,
          "Linden's wire: The Cinder bridge is out, but a surfer can cross east of LUMEN." },
        { FLAG_VOLT_CREST, FLAG_STORY_WIRE_VOLT,
          "Linden's wire: PORT BRINE's lighthouse is dark. Brookmill has fixed the fen boardwalk; come home west." },
        { FLAG_STORM_CALMED, FLAG_STORY_WIRE_HOME,
          "Linden's wire: Old kernels are stirring. The Accord needs wardens. Go east to LUMEN; Fara holds the first crest." },
    };
    for (unsigned i = 0; i < sizeof(wires) / sizeof(wires[0]); i++) {
        if (flag(wires[i].trigger) && !flag(wires[i].read)) {
            /* Catch up silently on any earlier wire superseded by this act. */
            for (unsigned older = i + 1; older < sizeof(wires) / sizeof(wires[0]); older++)
                if (flag(wires[older].trigger)) flag_set(wires[older].read);
            flag_set(wires[i].read);
            dlg_say(wires[i].message);
            return 1;
        }
    }
    return 0;
}

static void scr_story_road(int npc)
{
    (void)npc;
    dlg_say("Nobody leaves the valley while the sky grumbles. Keeper's orders. Answer DRAKORA at the Rise first.");
}

static void scr_story_farewell(int npc)
{
    (void)npc;
    dlg_say("The sky is clear. The road is yours, warden. Rest your kin along the way.");
}

static void scr_story_ridge(int npc)
{
    (void)npc;
    dlg_say("The storm's last thunderclap brought the ridge down. Those boulders need STRENGTH, not a shove.");
}

static int story_rival_starter(void)
{
    const int choices[3] = { FLAG_SORREL_STARTER_FIRE, FLAG_SORREL_STARTER_WATER,
                             FLAG_SORREL_STARTER_LEAF };
    for (int i = 0; i < 3; i++)
        if (flag(choices[i])) return STARTER_SPECIES[(i + 1) % 3];
    for (int member = 0; member < party_count; member++) {
        int sp = party[member].species;
        /* The Kindling partner may have grown or moved to another party slot. */
        while (species_prevo(sp) >= 0) sp = species_prevo(sp);
        if (party[member].met_map != MAP_LAB) continue;
        for (int i = 0; i < 3; i++) {
            if (sp != STARTER_SPECIES[i]) continue;
            flag_set(choices[i]);
            return STARTER_SPECIES[(i + 1) % 3];
        }
    }
    /* A traded-away starter needs the Kindling hook to preserve its choice. */
    return STARTER_SPECIES[1];
}

static int story_rival_flag_for(int map)
{
    if (map == MAP_TOWN) return FLAG_SORREL_MAPLE;
    if (map == MAP_MEADOW) return FLAG_SORREL_MEADOW;
    return 0;
}

static int story_rival_trainer_for(int map)
{
    if (map == MAP_TOWN) return TR_SORREL_MAPLE;
    if (map == MAP_MEADOW) return TR_SORREL_MEADOW;
    return NO_TRAINER;
}

static int story_bout_flag;
static void story_bout_end(int result)
{
    if (result == BR_WIN && story_bout_flag) flag_set(story_bout_flag);
    story_bout_flag = 0;
}

static void story_start_bout(int trainer, int beaten_flag)
{
    static TrainerTeam team;
    team = team_from(&TRAINERS[trainer], BSCENE_AREA);
    set_battle_scene(MAPS[cur_map].scene);
    if (trainer >= TR_SORREL_MAPLE && trainer <= TR_SORREL_FINALE)
        team.species[0] = story_rival_starter();
    story_bout_flag = beaten_flag;
    battle_end_hook = story_bout_end;
    battle_start_trainer_team(&team);
}

static void story_rival_bout(int npc)
{
    (void)npc;
    story_start_bout(story_rival_trainer_for(cur_map), story_rival_flag_for(cur_map));
}

static void scr_story_sorrel(int npc)
{
    int trainer = story_rival_trainer_for(cur_map);
    if (trainer == NO_TRAINER) return;
    if (party_first_healthy() < 0) {
        dlg_say("SORREL: Your kin are dozing. Rest first; I can wait.");
        return;
    }
    dlg_say(TRAINERS[trainer].intro);
    dlg_call(story_rival_bout, npc);
}

static void scr_story_still(int npc)
{
    (void)npc;
    dlg_say("We rang the bell so no kin would need a bout. But the brimming has nowhere to go.");
}

static void scr_story_vesta(int npc)
{
    (void)npc;
    dlg_say("VESTA: I wanted a gentler Vale. The hush only made the hollow kernels stir. Help me put it right.");
}
