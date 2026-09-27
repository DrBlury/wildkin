/*
 * world/travel/scripts.c -- NPC scripts: static void scr_x(int npc) { ... }
 * (register each in script_ids.inc and script_table.inc). Owner: TRAVERSAL system.
 *
 * Also the traversal glue that needs the bout engine and give_item (both
 * are compiled after travel.c): static legends and chests (OBJ_LEGEND,
 * OBJ_CHEST; travel.c obj_interact calls these).
 */

static int travel_bout_obj = -1;

static void travel_bout_end(int result)
{
    if ((result == BR_WIN || result == BR_CAUGHT) && travel_bout_obj >= 0) travel_obj_done(travel_bout_obj);
    travel_bout_obj = -1;
}

static void travel_bout_start(int obj, int species, int level, int no_run)
{
    if (party_first_healthy() < 0) {
        dlg_say("Your kin are all dozing. Rest them first!");
        return;
    }
    Monster m = monster_make(species, level);
    m.met_map = (u8)cur_map;
    set_battle_scene(SC_LAIR);
    travel_bout_obj = obj;
    battle_end_hook = travel_bout_end;
    battle_start_wild(m);
    if (no_run) battle.no_run = 1;
}

/* A static legend (OBJ_LEGEND, arg = species): once answered (won or
 * befriended) it is gone for good. */
static void travel_legend_go(int obj)
{
    if (obj < 0 || obj >= tobj_count) return;
    travel_bout_start(obj, tobj[obj].arg, clampi(party_max_level() + 4, 30, 60), 1);
}

static void travel_mimic_go(int obj)
{
    int sp = tobj[obj].arg == 254 ? SP_HOARDMAW : SP_TRINKIT;
    travel_bout_start(obj, sp, clampi(party_max_level(), 12, 50), 0);
}

/* A chest (OBJ_CHEST, arg = item; 255 / 254 = a TRINKIT / HOARDMAW mimic). */
static void travel_chest_go(int obj)
{
    if (obj < 0 || obj >= tobj_count) return;
    int arg = tobj[obj].arg;
    if (arg == 255 || arg == 254) {
        dlg_say("You lift the lid... The chest has teeth!");
        dlg_call(travel_mimic_go, obj);
        return;
    }
    if (arg >= ITEM_COUNT) {
        dlg_say("The chest is empty.");
        travel_obj_done(obj);
        return;
    }
    travel_obj_done(obj);
    dlg_say("You open the chest...");
    give_item(arg, 1);
}
