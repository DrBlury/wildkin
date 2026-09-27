/*
 * Story and overworld glue: people and what they say (and the lore they
 * reveal), wardens who spot you, bouts with wild kin, signs, satchels,
 * decor you can examine, the Kindling, the Bout Ring, the Stormstone and
 * DRAKORA, and the per-frame field update/draw.
 */

static int save_write(void);
static void start_menu_open(void);

static const char *const STARTER_NAMES[3] = { "FLARIX", "AQUAPO", "DANDELAMB" };
static int starter_pick;
static int kid_tip;
static u16 step_counter;
static int storm_flash;

static void npc_face_player(int i)
{
    npc_state[i].facing = DIR_BACK[player.facing];
    npc_state[i].timer = 120;
}

static void give_item(int item, int qty)
{
    char msg[64];
    bag_add(item, qty);
    sfx_play(SFX_ITEM);
    str_copy(msg, "You received ");
    if (qty > 1) {
        str_put_int(msg, qty);
        str_put(msg, " ");
    }
    str_put(msg, ITEMS[item].name);
    str_put(msg, qty > 1 && ITEMS[item].name[str_len(ITEMS[item].name) - 1] != 'S' ? "S!" : "!");
    dlg_say(msg);
}

/* Battle backdrop for the current area. */
static void set_battle_scene(int sc)
{
    /* SC_* and BSCENE_* share their order (MEADOW..LAIR) */
    battle_next_scene = sc >= 0 && sc < BSCENE_COUNT ? sc : BSCENE_MEADOW;
}

/* One cutscene walk and camera pan at a time; the path must outlive the callback. */
static struct {
    const u8 *path;
    int npc, count, step, blocked, active, map;
    void (*done)(int);
    int arg;
} cut_walk;
static struct {
    int active, frames, elapsed, start_x, start_y, end_x, end_y;
    void (*done)(int);
    int arg;
} cut_pan;

static int script_walking_npc(void) { return cut_walk.active ? cut_walk.npc : -2; }

MAYBE_UNUSED static void npc_face(int npc, int dir)
{
    if (npc >= 0 && npc < NPC_COUNT && npc_visible[npc] && dir >= 0 && dir < 4)
        npc_state[npc].facing = (u8)dir;
}

MAYBE_UNUSED static void npc_warp_out(int npc)
{
    if (npc < 0 || npc >= NPC_COUNT || !npc_visible[npc]) return;
    npc_warped[npc] = 1;
    npcs_refresh();
}

static void script_walk_start(int npc, const u8 *path, int n, void (*done)(int), int arg)
{
    if (cut_walk.active || cut_pan.active || !path || n <= 0 ||
        (npc >= 0 && (npc >= NPC_COUNT || !npc_visible[npc]))) {
        if (done) done(arg);
        return;
    }
    cut_walk.path = path;
    cut_walk.npc = npc;
    cut_walk.count = n;
    cut_walk.step = cut_walk.blocked = 0;
    cut_walk.active = 1;
    cut_walk.map = cur_map;
    cut_walk.done = done;
    cut_walk.arg = arg;
}

MAYBE_UNUSED static void npc_walk(int npc, const u8 *path, int n, void (*done)(int), int arg)
{
    script_walk_start(npc, path, n, done, arg);
}

MAYBE_UNUSED static void player_walk(const u8 *path, int n, void (*done)(int), int arg)
{
    script_walk_start(-1, path, n, done, arg);
}

MAYBE_UNUSED static void cam_pan_to(int x, int y, int frames, void (*done)(int), int arg)
{
    if (cut_walk.active || cut_pan.active || frames <= 0) {
        if (done) done(arg);
        return;
    }
    cut_pan.active = cam_scripted = 1;
    cut_pan.frames = frames;
    cut_pan.elapsed = 0;
    cut_pan.start_x = cam_x;
    cut_pan.start_y = cam_y;
    cut_pan.end_x = clampi(x * 16 + 8 - SCREEN_WIDTH / 2, 0, map_w * 16 > SCREEN_WIDTH ? map_w * 16 - SCREEN_WIDTH : 0);
    cut_pan.end_y = clampi(y * 16 + 8 - SCREEN_HEIGHT / 2, 0, map_h * 16 > SCREEN_HEIGHT ? map_h * 16 - SCREEN_HEIGHT : 0);
    cut_pan.done = done;
    cut_pan.arg = arg;
}

MAYBE_UNUSED static void cam_follow_player(void)
{
    cut_pan.active = cam_scripted = 0;
    field_update_camera();
}

static int script_cutscene_update(void)
{
    if (cut_pan.active) {
        int f = ++cut_pan.elapsed;
        cam_x = cut_pan.start_x + (cut_pan.end_x - cut_pan.start_x) * f / cut_pan.frames;
        cam_y = cut_pan.start_y + (cut_pan.end_y - cut_pan.start_y) * f / cut_pan.frames;
        if (f >= cut_pan.frames) {
            cut_pan.active = 0;
            void (*done)(int) = cut_pan.done;
            if (done) done(cut_pan.arg);
        }
        return 1;
    }
    if (!cut_walk.active) return 0;
    if (cut_walk.map != cur_map) { cut_walk.active = 0; return 1; }
    Actor *a = cut_walk.npc < 0 ? &player : &npc_state[cut_walk.npc];
    if (a->moving) {
        actor_step(a, 1);
        return 1;
    }
    if (cut_walk.step >= cut_walk.count) {
        cut_walk.active = 0;
        void (*done)(int) = cut_walk.done;
        if (done) done(cut_walk.arg);
        return 1;
    }
    int dir = cut_walk.path[cut_walk.step];
    if (dir >= 0 && dir < 4) {
        int nx = a->x + DIR_DX[dir], ny = a->y + DIR_DY[dir], nl;
        a->facing = (u8)dir;
        int ek = elev_enter(a->x, a->y, a->level, dir, &nl);
        if (ek != ELEV_BLOCK && cell_walkable_lv(nx, ny, nl, ek == ELEV_TOP) &&
            (cut_walk.npc < 0 || (nx != player.x || ny != player.y)) &&
            (cut_walk.npc >= 0 || npc_at(nx, ny) < 0)) {
            actor_start_move(a, dir);
            a->level = (u8)nl;
            cut_walk.step++;
            cut_walk.blocked = 0;
            return 1;
        }
    }
    if (++cut_walk.blocked >= 6) { cut_walk.blocked = 0; cut_walk.step++; }
    return 1;
}

/* ---------------- the Kindling (Keeper Linden) ---------------- */

static void keeper_confirm(int c);

static void keeper_preview_on(int unused)
{
    (void)unused;
    starter_preview = 0;
    canvas_window(9, 1, 12, 11, WIN_STD);
    load_monster_gfx(0, STARTER_SPECIES[0], 0);
}

static void keeper_preview_off(void)
{
    starter_preview = -1;
    canvas_clear_cells(9, 1, 12, 11);
}

static void keeper_pick(int c)
{
    char msg[120];
    starter_pick = c;
    str_copy(msg, STARTER_NAMES[c]);
    str_put(msg, ", the ");
    str_put(msg, TYPE_NAMES[SPECIES[STARTER_SPECIES[c]].type1]);
    str_put(msg, " kin? Once the lantern closes, it's your partner for life. Sure?");
    dlg_ask(msg, YES_NO, 2, keeper_confirm);
}

static void keeper_ask(int unused)
{
    (void)unused;
    dlg_ask("Which one will you choose as your partner?", STARTER_NAMES, 3, keeper_pick);
}

static void keeper_confirm(int c)
{
    if (c != 0) {
        keeper_ask(0);
        return;
    }
    keeper_preview_off();
    int sp = STARTER_SPECIES[starter_pick];
    Monster m = monster_make(sp, 5);
    m.met_map = MAP_LAB;
    m.bond = 120;
    give_monster(&m);
    dex_seen[sp] = 1;
    flag_set(FLAG_STARTER);
    follower_reset();
    char msg[96];
    str_copy(msg, SPECIES[sp].name);
    str_put(msg, " stepped out of the lantern and nuzzled your hand!");
    sfx_play(SFX_ITEM);
    dlg_say(msg);
    lore_story(LORE_KINDLING);
    dlg_say("Then it's done: you're a warden now. Here, every warden starts with these.");
    give_item(ITEM_LANTERN, 5);
    give_item(ITEM_TONIC, 3);
    dlg_say("Every bout you fight out there spills a little of that storm into the soil. Go on, answer the brimming kin in the meadows!");
    dlg_say("And talk to people. Everything they teach you goes in your LOREBOOK. Pip has something for you too.");
}

static void relearn_pick_kin(int c);
static int grim_keeper_talk(void);          /* world/grim/scripts.c: the Hollowing */
static int grim_interact(int x, int y);     /* world/grim/scripts.c: the Bone Throne */
static void grim_on_enter(void);
static void (*events_map_entered)(int map);
static void (*story_map_entered)(int map);
static void (*saga_map_entered)(int map);

static void keeper_after(void)
{
    char msg[120];
    if (!(flag(FLAG_SASH))) {
        if (!lore_reveal(LSRC_KEEPER, 0))
            dlg_say("WARDEN MARLO runs the BOUT RING in the plaza. Earn the RING SASH, then come and see me.");
        return;
    }
    if (!(flag(FLAG_STORM_TOLD))) {
        flag_set(FLAG_STORM_TOLD);
        dlg_say("The RING SASH! Then I can ask you. Listen closely.");
        dlg_say("The sky has grumbled for weeks. The Almanac page from a hundred years ago says the same: DRAKORA is brimming.");
        dlg_say("Go up WHISPER MEADOW to STORMSTONE RISE and lay your hand on the Stormstone. DRAKORA will come to answer a warden. Give it the bout it needs.");
        return;
    }
    if (!(flag(FLAG_STORM_CALMED))) {
        dlg_say("The Stormstone waits at the top of STORMSTONE RISE, north of WHISPER MEADOW. Rest your kin first!");
        return;
    }
    if (grim_keeper_talk()) return;
    if (lore_reveal(LSRC_KEEPER, 0)) return;
    str_copy(msg, "Your ALMANAC: ");
    str_put_int(msg, dex_caught_count());
    str_put(msg, " of ");
    str_put_int(msg, SP_COUNT);
    str_put(msg, " kin befriended. Clear skies suit you, warden!");
    dlg_say(msg);
    static const char *const OFFER[2] = { "REMEMBER", "NO THANKS" };
    dlg_ask("I can also help a kin REMEMBER a move it has forgotten. Would you like that?", OFFER, 2,
            relearn_pick_kin);
}

static void script_keeper(void)
{
    if (!(flag(FLAG_STARTER))) {
        dlg_say("There you are! Happy Kindling day. I'm KEEPER LINDEN; I keep the ALMANAC.");
        dlg_say("Three kits were born by the Almanac hearth this spring. Each is ready to choose a warden. Come, meet them.");
        dlg_call(keeper_preview_on, 0);
        keeper_ask(0);
        return;
    }
    if (bag_total(POCKET_LANTERNS) < 3) {
        dlg_say("Short on lanterns? Take these; the Almanac grows heartglass for new wardens.");
        give_item(ITEM_LANTERN, 5);
        return;
    }
    keeper_after();
}

/* ---- move re-teacher ---- */

static const char *relearn_names[7];
static u8 relearn_moves[6];
static int relearn_slot;

static void relearn_pick_move(int c)
{
    if (c < 0 || relearn_names[c] == 0 || c >= 6 || relearn_moves[c] == 0xFF) return;
    learn_begin(relearn_slot, relearn_moves[c]);
}

static void relearn_list(int slot);

/* "REMEMBER" was picked: choose the kin. */
static void relearn_pick_kin(int c)
{
    static char names[PARTY_MAX][12];
    static const char *kin[PARTY_MAX + 1];
    if (c != 0) return;
    int n = 0;
    for (int i = 0; i < party_count; i++) {
        str_copy(names[i], kin_name(&party[i]));
        kin[n++] = names[i];
    }
    kin[n++] = "CANCEL";
    dlg_ask("Which kin should remember?", kin, n, relearn_list);
}

/* Called from the kin choice (party slot) of relearn_pick_kin. */
static void relearn_list(int slot)
{
    if (slot < 0 || slot >= party_count) return;
    Monster *m = &party[slot];
    int n = 0;
    for (const LearnEntry *e = SPECIES[m->species].learnset; e->level && n < 5; e++) {
        if (e->level > m->level || monster_knows(m, e->move)) continue;
        int dup = 0;
        for (int k = 0; k < n; k++)
            if (relearn_moves[k] == e->move) dup = 1;
        if (dup) continue;
        relearn_moves[n] = e->move;
        relearn_names[n++] = MOVES[e->move].name;
    }
    if (!n) {
        dlg_say("It remembers everything it has ever learned. Impressive!");
        return;
    }
    relearn_slot = slot;
    relearn_moves[n] = 0xFF;
    relearn_names[n++] = "CANCEL";
    dlg_ask("Which move should it remember?", relearn_names, n, relearn_pick_move);
}

/* ---------------- people with gifts ---------------- */

static void script_aide(void)
{
    if ((flag(FLAG_STARTER)) && !(flag(FLAG_PIP_GIFT))) {
        flag_set(FLAG_PIP_GIFT); flag_set(FLAG_TWIN_CRYSTAL);
        dlg_say("A new warden! I'm PIP, the Keeper's aide. This is for you: a TWIN CRYSTAL.");
        sfx_play(SFX_ITEM);
        dlg_say("You received the TWIN CRYSTAL! Open the LANTERN SHELF anywhere from your START menu.");
        dlg_say("Its twin sits in the Hearth Hall rack. Kin you send go across the wire. Clever, right? Oh, and take a HUSH BELL.");
        give_item(ITEM_HUSH_BELL, 1);
        return;
    }
    lore_reveal(LSRC_AIDE, "Heartglass grows by about a hair's width a year. Every lantern is older than you are!");
}

static void script_gran(void)
{
    if (!(flag(FLAG_STARTER))) {
        dlg_say("Morning, sleepyhead! Today's your Kindling! KEEPER LINDEN is waiting at the ALMANAC HOUSE, up north-east.");
        dlg_say("Your parents would be so proud. They sent a telegram from the far side of the Vale. Now go on!");
        return;
    }
    if (!(flag(FLAG_GRAN_GIFT))) {
        flag_set(FLAG_GRAN_GIFT);
        dlg_say("Oh, look at you two! Here, for the road. And remember, your bed is always here for a nap.");
        give_item(ITEM_TONIC, 3);
        return;
    }
    lore_reveal(LSRC_GRAN, "Mind the weather out there. And come home for supper!");
}

static void script_baker(void)
{
    if ((flag(FLAG_STARTER)) && !(flag(FLAG_BAKER_GIFT))) {
        flag_set(FLAG_BAKER_GIFT);
        dlg_say("A brand-new warden! Take these for the road, dear. Kin love a glowing tonic.");
        give_item(ITEM_TONIC, 3);
        give_item(ITEM_BIG_TONIC, 1);
        return;
    }
    lore_reveal(LSRC_BAKER, "My CINDERUB keeps the oven warm. The NIBBIT keeps the crumbs... gone.");
}

static void script_gardener(void)
{
    if (!(flag(FLAG_LEAF_STONE))) {
        flag_set(FLAG_LEAF_STONE);
        dlg_say("I dug this up in my flower bed. It hums in spring. Maybe you can use it.");
        give_item(ITEM_BLOOM_SHARD, 1);
        dlg_say("A shard makes certain kin grow at once. THORNIP just adores springtime...");
        return;
    }
    lore_reveal(LSRC_GARDENER, "The DUSK SHARD is supposed to be hidden deep in BRAMBLEWOOD. The SHOP sells the others.");
}

static void script_woodward(void)
{
    if (!(flag(FLAG_WOODWARD_GIFT))) {
        flag_set(FLAG_WOODWARD_GIFT);
        dlg_say("Mind your step, warden. My MOSSHELL naps on the path. Here, these help when the spores get you.");
        give_item(ITEM_SOOTHE_BALM, 2);
        return;
    }
    lore_reveal(LSRC_WOODWARD, "Thirty years I've watched this wood. It's never been this restless.");
}

static void bed_answer(int c);

static void script_hermit(void)
{
    if (!(flag(FLAG_HERMIT_GIFT))) {
        flag_set(FLAG_HERMIT_GIFT);
        dlg_say("...You knocked twice. Good manners. Hardly anyone knocks twice.");
        dlg_say("Take this seed. It held a summer once. And use the cot if your kin are tired.");
        give_item(ITEM_SUNSEED, 1);
        return;
    }
    lore_reveal(LSRC_HERMIT, "The wood dreams. So do you. Sleep on it.");
}

static void script_vass(void)
{
    if (!(flag(FLAG_VASS_GIFT))) {
        flag_set(FLAG_VASS_GIFT);
        dlg_say("Oh! A visitor! Are you here about the polaritons? Nobody is ever here about the polaritons.");
        dlg_say("Take these prism lanterns. Higher finesse mirrors! Please report back on your data.");
        give_item(ITEM_GLOW_LANTERN, 3);
        return;
    }
    lore_reveal(LSRC_RESEARCHER, "The lake is a perfect mirror today. A cavity the size of a valley... imagine the Q-factor!");
}

/* ---------------- Bout Ring (Warden Marlo) ---------------- */

static void marlo_end(int result)
{
    if (result != BR_WIN) return;
    flag_set(FLAG_RING_WON_ONCE);
    if (!(flag(FLAG_SASH))) {
        flag_set(FLAG_SASH);
        trainer_mark_beaten(TR_MARLO);
        sfx_play(SFX_ITEM);
        dlg_say("You received the RING SASH! Two linked rings: one for people, one for kin.");
        lore_story(LORE_RING_SASH);
        dlg_say("MARLO: The Keeper asked me to send the first warden who beat me straight to the ALMANAC HOUSE. Go!");
    }
}

static TrainerTeam team_from(const TrainerDef *t, int scene)
{
    TrainerTeam tt;
    tt.name = t->name;
    tt.count = t->count;
    for (int i = 0; i < TRAINER_TEAM_MAX; i++) {
        tt.species[i] = t->species[i];
        tt.level[i] = t->level[i];
    }
    tt.flags = 0;
    tt.prize = t->prize;
    tt.scene = (u8)scene;
    tt.lose_line = t->lose;
    keeper_trainer_look((int)(t - TRAINERS), &tt.look, &tt.vary);   /* as they look on the map */
    tt.look++;
    return tt;
}

static void marlo_answer(int c)
{
    if (c != 0) {
        dlg_say("Come back when your kin are itching for it!");
        return;
    }
    battle_end_hook = marlo_end;
    if (!(flag(FLAG_SASH))) {
        static TrainerTeam t;
        t = team_from(&TRAINERS[TR_MARLO], BSCENE_RING);
        battle_start_trainer_team(&t);
    } else {
        battle_next_scene = BSCENE_RING;
        battle_start_trainer();
    }
}

static void script_marlo(void)
{
    if (!party_count) {
        dlg_say("No kin, no bout! Get yourself Kindled at the ALMANAC HOUSE first, kid.");
        return;
    }
    lore_story(LORE_BOUT_RING);
    if (party_first_healthy() < 0) {
        dlg_say("Your kin are all dozing! Take them to the HEARTH HALL first.");
        return;
    }
    lore_reveal(LSRC_MARLO, 0);
    if (!(flag(FLAG_SASH)))
        dlg_ask("Want the RING SASH? Beat my team of three and it's yours! Ready?", YES_NO, 2, marlo_answer);
    else
        dlg_ask("Back for more? My team changes every time. Winner takes the coins!", YES_NO, 2, marlo_answer);
}

/* ---------------- shop & hearth ---------------- */

static const char *const SHOP_MENU[3] = { "BUY", "CHAT", "QUIT" };

static void shop_answer(int c)
{
    if (c == 0) shop_open();
    else if (c == 1) lore_reveal(LSRC_CLERK, "Tonics are brewed in the village. The lanterns come all the way from the glassworks.");
    else dlg_say("Please come again!");
}

static const char *const HEARTH_MENU[3] = { "REST", "CHAT", "NO THANKS" };

/* Resting in a Hearth Hall also makes it the respawn point. */
static void hearth_rest(void)
{
    if (MAPS[cur_map].flags & MF_HEAL) travel.last_hearth = (u8)cur_map;
    party_heal_all();
    sfx_play(SFX_HEAL);
    follower_reset();
}

static void heal_answer(int c)
{
    if (c == 1) {
        lore_reveal(LSRC_TENDER, "The hearth has not gone out in three hundred years. I just add the wood.");
        return;
    }
    if (c != 0) {
        dlg_say("The hearth is always lit. Come back any time.");
        return;
    }
    hearth_rest();
    dlg_say("Your kin curled up by the hearth and soaked up its warmth. They're full of vigor again!");
    if (opt.autosave && save_write()) dlg_say("(Your progress was saved.)");
}

/* ---------------- wardens ---------------- */

static struct { int active, npc, phase, timer; } spot;

static void warden_end(int result);
static int warden_battling = -1;

static void warden_battle(int npc)
{
    int t = NPCS[npc].trainer;
    static TrainerTeam team;
    team = team_from(&TRAINERS[t], BSCENE_AREA);
    if (trainer_beaten(t) && events_rematch_ready(t))
        for (int i = 0; i < team.count; i++)
            team.level[i] = (u8)events_rematch_level(t, i);
    set_battle_scene(MAPS[cur_map].scene);
    warden_battling = t;
    battle_end_hook = warden_end;
    battle_start_trainer_team(&team);
}

static void warden_battle_call(int npc)
{
    warden_battle(npc);
}

static void warden_end(int result)
{
    if (result == BR_WIN && warden_battling >= 0) {
        if (trainer_beaten(warden_battling)) events_rematch_used(warden_battling);
        else trainer_mark_beaten(warden_battling);
    }
    warden_battling = -1;
}

static void script_warden(int npc)
{
    int t = NPCS[npc].trainer;
    if (trainer_beaten(t) && !events_rematch_ready(t)) {
        dlg_say(NPCS[npc].text ? NPCS[npc].text : "Good bout, warden.");
        return;
    }
    if (party_first_healthy() < 0) {
        dlg_say("Your kin are dozing. Come back after the HEARTH HALL!");
        return;
    }
    dlg_say(TRAINERS[t].intro);
    dlg_call(warden_battle_call, npc);
}

/* Can warden `i` see the player (straight line, nothing in the way)? */
static int warden_sees(int i)
{
    const Actor *a = &npc_state[i];
    int x = a->x, y = a->y, level = a->level;
    for (int k = 1; k <= NPCS[i].sight; k++) {
        /* the walk up to you must be a real one: no cliffs, same level (elev.c) */
        int nl, ek = elev_enter(x, y, level, a->facing, &nl);
        if (ek == ELEV_BLOCK) return 0;
        x += DIR_DX[a->facing];
        y += DIR_DY[a->facing];
        level = nl;
        if (x == player.x && y == player.y) return level == player.level;
        if (ek != ELEV_TOP && (cell_attr(x, y) & A_SOLID)) return 0;
        if (npc_at(x, y) >= 0 || npc_kin_at(x, y) >= 0) return 0;
    }
    return 0;
}

static void check_spotting(void)
{
    if (!party_count || party_first_healthy() < 0) return;
    for (int i = 0; i < NPC_COUNT; i++) {
        if (!npc_visible[i] || NPCS[i].trainer == NO_TRAINER) continue;
        if ((trainer_beaten(NPCS[i].trainer) && !events_rematch_ready(NPCS[i].trainer)) ||
            npc_state[i].moving) continue;
        if (!warden_sees(i)) continue;
        spot.active = 1;
        spot.npc = i;
        spot.phase = 0;
        spot.timer = 0;
        sfx_play(SFX_EXCLAIM);
        field_emote(i, EMOTE_EXCLAIM, 40);
        return;
    }
}

/* The "!" moment: the warden walks up and challenges you. */
static int spot_update(void)
{
    if (!spot.active) return 0;
    Actor *a = &npc_state[spot.npc];
    spot.timer++;
    if (spot.phase == 0) {
        if (spot.timer >= 40) spot.phase = 1;
        return 1;
    }
    if (spot.phase == 1) {
        if (a->moving) {
            actor_step(a, 2);
            KinActor *k = &npc_kin[spot.npc];
            if (k->shown && k->a.moving) actor_step(&k->a, 2);
            return 1;
        }
        int dist = absi(a->x - player.x) + absi(a->y - player.y);
        if (dist > 1) {
            int ox = a->x, oy = a->y, nl;
            elev_enter(a->x, a->y, a->level, a->facing, &nl);
            actor_start_move(a, a->facing);
            a->level = (u8)nl;
            if (npc_kin[spot.npc].shown) kin_follow(&npc_kin[spot.npc], ox, oy, 0);
            return 1;
        }
        player.facing = DIR_BACK[a->facing];
        spot.active = 0;
        script_warden(spot.npc);
        return 1;
    }
    return 1;
}

/* ---------------- wild kin ---------------- */

static void wild_end(int result)
{
    (void)result;
    if (wild_battle_slot >= 0) wild[wild_battle_slot].active = 0;
    wild_battle_slot = -1;
}

static void debug_parade_touch(int slot);
static void debug_parade_shift(int by);
static void debug_open(void);

static void wild_touch(int slot)
{
    if (MAPS[cur_map].flags & MF_DEBUG) {
        debug_parade_touch(slot);
        return;
    }
    if (!party_count || party_first_healthy() < 0) {
        dlg_say("The wild kin looks ready for a bout, but your kin are all dozing...");
        wild[slot].active = 0;
        return;
    }
    wild_battle_slot = slot;
    set_battle_scene(travel.surfing || wild[slot].water ? SC_SEA : MAPS[cur_map].scene);
    battle_end_hook = wild_end;
    battle_start_wild(wild[slot].mon);
    steps_since_battle = 0;
}

/* ---------------- the Stormstone & DRAKORA ---------------- */

static void drakora_end(int result)
{
    if (result == BR_WIN || result == BR_CAUGHT) {
        flag_set(FLAG_STORM_CALMED);
        if (result == BR_CAUGHT) flag_set(FLAG_DRAKORA_JOINED);
        dlg_say("The clouds over the Rise tear open. Warm rain falls, then sunlight. The storm spilled into the Vale, gently.");
        if (result == BR_WIN) dlg_say("DRAKORA circles once, its kernel calm at last, and rises into a clear sky.");
        lore_story(LORE_CLEAR_SKIES);
        dlg_say("Everyone in MAPLE VILLAGE will want to hear about this. Keeper Linden most of all!");
    } else {
        dlg_say("DRAKORA is still brimming. Rest your kin and try again.");
    }
}

static void drakora_begin(int unused)
{
    (void)unused;
    int level = clampi(party_max_level() + 2, 16, 45);
    Monster d = monster_make(SP_DRAKORA, level);
    d.met_map = MAP_RISE;
    battle_next_scene = BSCENE_STORM;
    battle_end_hook = drakora_end;
    battle_start_wild(d);
    battle.no_run = 1;
}

static void script_stormstone(void)
{
    if (flag(FLAG_STORM_CALMED)) {
        lore_reveal(LSRC_STORMSTONE, "The Stormstone is quiet now. Warm to the touch, like a sleeping kin.");
        return;
    }
    if (!(flag(FLAG_STORM_TOLD))) {
        lore_reveal(LSRC_STORMSTONE, "The standing stone hums under your hand. The air tastes like rain. (Maybe the Keeper knows more.)");
        return;
    }
    if (party_first_healthy() < 0) {
        dlg_say("The stone hums... but your kin are dozing. Rest them first.");
        return;
    }
    dlg_say("You lay your hand on the Stormstone. It thrums like a plucked string...");
    dlg_say("Thunder rolls across the Rise. A shape unfolds from the clouds: DRAKORA, the Stormwyrm!");
    dlg_call(drakora_begin, 0);
}

/* ---------------- dispatch ---------------- */

static void script_kid(void)
{
    static const char *const TIPS[] = {
        "Hold B to run! Everybody knows that.",
        "Wild kin wander in the tall grass. The brimming ones come right at you!",
        "Press START to open your LOREBOOK. It remembers everything people tell you!",
        "Wardens challenge you the moment they see you. Walk behind them if you're not ready!",
        "Your lead kin walks with you. Talk to it! It tells you how it's feeling.",
    };
    if (lore_reveal(LSRC_KID, 0)) return;
    dlg_say(TIPS[kid_tip++ % 5]);
}

/* ---------------- NPC script dispatch ---------------- */

typedef void (*ScriptFn)(int npc);

/* The default: say NpcDef.text, revealing lore when the person has some. */
static void scr_talk(int npc)
{
    const NpcDef *n = &NPCS[npc];
    /* after the storm, the villagers of the first area all talk about it */
    if (flag(FLAG_STORM_CALMED) && n->lore == NO_LORE && n->map <= MAP_STATION)
        dlg_say("Did you see? The sky over the Rise cleared! Someone must have answered DRAKORA!");
    else
        lore_reveal(n->lore, n->text ? n->text : "...");
}

#include "world/all_scripts.c"

static const ScriptFn SCRIPT_FNS[SCR_COUNT] = {
    [SCR_TALK] = scr_talk,
    [SCR_WARDEN] = script_warden,
#include "world/all_script_table.inc"
};

static void script_run(int npc)
{
    npc_face_player(npc);
    ScriptFn f = NPCS[npc].script < SCR_COUNT ? SCRIPT_FNS[NPCS[npc].script] : 0;
    (f ? f : scr_talk)(npc);
}

/* Talking to your own follower: its mood, from its bond. */
static void follower_talk(void)
{
    int lead = party_first_healthy();
    if (lead < 0) return;
    const Monster *m = &party[lead];
    char msg[96];
    str_copy(msg, kin_name(m));
    if (m->bond >= 220) {
        str_put(msg, " leans against you and glows warmly. It trusts you completely.");
        field_emote(-1, EMOTE_HAPPY, 50);
    } else if (m->bond >= 150) {
        str_put(msg, " hums happily. It likes walking with you.");
        field_emote(-1, EMOTE_NOTE, 50);
    } else if (m->hp * 3 < m->max_hp) {
        str_put(msg, " looks tired. A rest by a hearth would do it good.");
        field_emote(-1, EMOTE_DOTS, 50);
    } else {
        str_put(msg, " sniffs the air curiously, keeping close to you.");
        field_emote(-1, EMOTE_NOTE, 50);
    }
    dlg_say(msg);
}

static void pc_answer(int c)
{
    if (c == 0) pc_open(0);
}

static void bed_answer(int c)
{
    if (c == 0) {
        hearth_rest();
        time_sleep();
        dlg_say("You slept until morning. Your kin curled up beside you and woke up full of vigor!");
    }
}

static int book_source(void)
{
    switch (cur_map) {
    case MAP_HOME: return LSRC_BOOK_HOME;
    case MAP_LAB: return LSRC_BOOK_ALMANAC;
    case MAP_STATION: return LSRC_BOOK_STATION;
    case MAP_CABIN: return LSRC_BOOK_CABIN;
    default: return NO_LORE;
    }
}

static int debug_examine(int x, int y);

/* Decor and places that can be examined. */
static int examine_cell(int x, int y)
{
    const DecorPlace *p = decor_at(x, y, 0, 0);
    if (!p) return 0;
    if (station_examine(p->kind)) return 1;
    if (fusion_examine(p->kind)) return 1;   /* the Resonance Works machines */
    switch (p->kind) {
    case DK_STORMSTONE:
        script_stormstone();
        return 1;
    case DK_OLD_HEARTH:
        lore_reveal(NO_LORE, "The Old Hearth. Its flames have burned since the first Kinship. Your hands feel warm, and so does your kin.");
        return 1;
    case DK_WELL:
        dlg_say("A deep, cool well. A TIDE kin's ripple glints far below.");
        return 1;
    case DK_BED:
        if (cur_map == MAP_HOME || cur_map == MAP_CABIN || cur_map == MAP_STATION) {
            dlg_ask("A cozy bed. Take a rest?", YES_NO, 2, bed_answer);
            return 1;
        }
        return 0;
    case DK_PC:
        dlg_ask("A LANTERN SHELF terminal. Its twin crystal glows softly. Open the Shelf?", YES_NO, 2, pc_answer);
        return 1;
    case DK_BOOKSHELF:
        lore_reveal(book_source(), "It's packed with books about kin, weather and the old Kinship.");
        return 1;
    case DK_TV:
        dlg_say(flag(FLAG_STORM_CALMED)
                ? "The news: \"Clear skies over the whole Vale! A young warden from MAPLE VILLAGE answered DRAKORA!\""
                : "A show about DRAKORA. The presenter says it's only a legend. The picture flickers with static.");
        return 1;
    case DK_STOVE: dlg_say("Something smells wonderful in the oven. Honey buns?"); return 1;
    case DK_LAB_MACHINE: dlg_say("A resonance scope. Its needles twitch every time a kin walks past."); return 1;
    case DK_HEAL_MACHINE: dlg_say("The hearth resonator. Warm light pulses slowly through its heartglass."); return 1;
    case DK_SHOP_SHELF: dlg_say("Shelves of lanterns, glowing tonics and tuning forks."); return 1;
    case DK_BOOKSHELF_SMALL:
        lore_reveal(book_source(), "Well-thumbed field guides and a book of old warden songs.");
        return 1;
    case DK_FIREPLACE:
        dlg_say("A crackling fire. A hearth pumps every kernel near it, so kin love to nap in front of one.");
        return 1;
    case DK_BRICK_OVEN: dlg_say("The brick oven roars. Loaves need steady heat, and a sleepy BLAZE kin is very steady."); return 1;
    case DK_LANTERN_RACK:
        dlg_say("Rows of resting lanterns. Each heartglass cavity holds a kin's kernel, glowing softly while it sleeps.");
        return 1;
    case DK_PIANO: dlg_say("You press a key. Somewhere nearby, a kin hums the same note, perfectly in tune."); return 1;
    case DK_BREAD_DISPLAY: dlg_say("Honey buns, sunseed loaves and glow-bee tarts. The whole room smells golden."); return 1;
    case DK_TELESCOPE:
    case DK_TELESCOPE_IN:
        dlg_say(flag(FLAG_STORM_CALMED)
                ? "Through the lens: clear blue sky, and a tiny speck circling high above STORMSTONE RISE."
                : "Through the lens: black clouds turning slowly above STORMSTONE RISE, lit from inside.");
        return 1;
    case DK_SPECIMEN_SHELF:
        dlg_say("Jars of shed kin mist, each one labelled with a date. The mist inside still glitters.");
        return 1;
    case DK_MICROSCOPE: dlg_say("Under the lens: a sliver of kernel crystal. Its layers look like tree rings."); return 1;
    case DK_DISPLAY_CASE:
        dlg_say("Four shards behind glass: BLOOM, SPARK, DUSK and FROST. Each is a seed crystal of one symmetry.");
        return 1;
    case DK_AQUARIUM: dlg_say("Little fish dart between the weeds. A bubble rises and pops with a tiny rainbow."); return 1;
    case DK_TELEGRAPH:
        dlg_say("A telegraph key. Twin crystals can't send a kin any faster than this wire can send the message.");
        return 1;
    case DK_CHALKBOARD:
        dlg_say("Two mirrors, a wave bouncing between them and a kernel in the middle. Underneath: \"Q = one billion!!\"");
        return 1;
    case DK_MAP_POSTER:
        dlg_say("A map of the Vale. MAPLE VILLAGE sits at the south end. STORMSTONE RISE is circled in red.");
        return 1;
    case DK_CALENDAR:
        dlg_say(cur_map == MAP_HOME ? "Today is circled three times: \"KINDLING DAY!\""
                                    : "A calendar. Market day, bout night, market day, rest day...");
        return 1;
    case DK_GRANDFATHER_CLOCK: dlg_say("Tick... tock... The pendulum swings as steadily as a kin's heartbeat."); return 1;
    case DK_KIN_PLUSH: dlg_say("A plush FLARIX. Its ember tail is stitched from orange felt."); return 1;
    case DK_GLOBE: dlg_say("A globe of the world. The Vale is a tiny green smudge near the middle."); return 1;
    case DK_MIRROR: dlg_say("You look ready for anything. Your kin would agree."); return 1;
    case DK_ICEBOX: dlg_say("The icebox. A FROST kin's shed rime keeps it cold for a whole week."); return 1;
    case DK_SINK_COUNTER: dlg_say("The dishes are done. Mostly."); return 1;
    case DK_TOY_BOX: dlg_say("Old toys: a wooden DRAKORA, a spinning top and a kite with no string."); return 1;
    case DK_WARDROBE: dlg_say("Clothes for every season. A raincoat hangs right at the front, just in case."); return 1;
    case DK_KIN_BASKET: dlg_say("A cozy wicker basket. Kin love to curl up in it after a long day of bouts."); return 1;
    case DK_DESK: dlg_say("A writing desk covered in notes: sightings, weather, and a sketch of a kin's tail."); return 1;
    case DK_TEA_SET: dlg_say("A pot of honey tea, still warm."); return 1;
    case DK_NOTICE_BOARD:
        dlg_say(flag(FLAG_STORM_CALMED)
                ? "NOTICE: Clear skies! Harvest festival at the Old Hearth. Bring your kin and a dish to share."
                : "NOTICE: Brimming kin seen on every route. Wardens, please answer them kindly!");
        return 1;
    case DK_SHRINE: dlg_say("A tiny shrine to the first wardens. Someone left a honey drop as an offering."); return 1;
    case DK_KIN_STATUE: dlg_say("A statue of the first warden's kin. Its stone eyes seem to follow you."); return 1;
    case DK_BEEHIVE: dlg_say("Glow-bees buzz in and out. Their honey glows faintly in the dark."); return 1;
    case DK_RAIN_GAUGE:
        dlg_say(flag(FLAG_STORM_CALMED) ? "The rain gauge holds a gentle inch of water."
                                                : "The rain gauge is overflowing. Again.");
        return 1;
    case DK_WEATHER_VANE:
        dlg_say(flag(FLAG_STORM_CALMED) ? "The weather vane creaks lazily in a warm breeze."
                                                : "The weather vane spins wildly, then points at STORMSTONE RISE.");
        return 1;
    case DK_SCARECROW: dlg_say("The scarecrow wears an old warden's sash. The birds don't seem impressed."); return 1;
    case DK_STANDING_STONE:
        dlg_say("An old standing stone. It hums faintly, and the side facing the Rise is warm.");
        return 1;
    case DK_CRYSTAL_CLUSTER: dlg_say("Raw crystal, pulsing with trapped light. It's far too big to carry."); return 1;
    case DK_BERRY_BUSH: dlg_say("Ripe berries! You eat a few. Your kin eats the rest."); return 1;
    case DK_CAMPFIRE: dlg_say("The campfire crackles. Somebody's kettle is just starting to whistle."); return 1;
    case DK_ROWBOAT: dlg_say("A little rowboat, tied to the dock. The oars are missing."); return 1;
    case DK_MARKET_STALL: dlg_say("Fresh sunseed, honey drops and crates of crisp red apples."); return 1;
    case DK_LANTERN_POST:
        dlg_say("A heartglass street lantern. It brightens a little whenever a kin walks past.");
        return 1;
    case DK_BIG_TREE: dlg_say("An enormous old tree. Its roots are older than the village."); return 1;
    case DK_TENT: dlg_say("A warden's tent. Snoring comes from inside."); return 1;
    case DK_MAILBOX:
        dlg_say(cur_map == MAP_TOWN
                ? "A telegram from your parents: \"Happy Kindling! Answer the brimming ones. Love, Mum and Dad.\""
                : "The mailbox is empty.");
        return 1;
    default:
        if (DECOR_EXAMINE[p->kind]) {
            dlg_say(DECOR_EXAMINE[p->kind]);
            return 1;
        }
        return 0;
    }
}

static int field_try_interact(void)
{
    int fx = player.x + DIR_DX[player.facing], fy = player.y + DIR_DY[player.facing];
    /* elevation (elev.c): people, kin and satchels across a cliff or below
     * a deck are out of reach; signs and objects can still be read */
    int nl, reach = elev_enter(player.x, player.y, player.level, player.facing, &nl) != ELEV_BLOCK;
    if (!reach) {
        int s = sign_at(fx, fy);
        if (s >= 0) {
            dlg_say(SIGNS[s].text);
            return 1;
        }
        return examine_cell(fx, fy);
    }
    int n = map_elevated ? npc_at_lv(fx, fy, nl) : npc_at(fx, fy);
    if (n < 0 && (cell_attr(fx, fy) & A_COUNTER))
        n = npc_at(fx + DIR_DX[player.facing], fy + DIR_DY[player.facing]);
    if (n >= 0) {
        script_run(n);
        return 1;
    }
    int k = npc_kin_at(fx, fy);
    if (k >= 0) {
        char msg[96];
        str_copy(msg, NPCS[k].name ? NPCS[k].name : "The warden");
        str_put(msg, "'s ");
        str_put(msg, SPECIES[NPCS[k].kin].name);
        str_put(msg, " looks at you curiously.");
        dex_seen[NPCS[k].kin] = 1;
        dlg_say(msg);
        return 1;
    }
    if (follower_active() && fx == follower.a.x && fy == follower.a.y) {
        follower_talk();
        return 1;
    }
    int ib = item_ball_at(fx, fy);
    if (ib >= 0) {
        item_take(ib);
        char msg[64];
        str_copy(msg, "You opened a satchel... ");
        dlg_say(msg);
        give_item(ITEM_BALLS[ib].item, ITEM_BALLS[ib].qty);
        return 1;
    }
    int s = sign_at(fx, fy);
    if (s >= 0) {
        dlg_say(SIGNS[s].text);
        return 1;
    }
    if (debug_examine(fx, fy)) return 1;
    if (farm_interact(fx, fy)) return 1;
    if (grim_interact(fx, fy)) return 1;
    if (obj_interact(fx, fy)) return 1;
    return examine_cell(fx, fy);
}

/* ---------------- stepping ---------------- */

static void on_player_step(void)
{
    steps_since_battle++;
    step_counter++;
    if (hush_steps) {
        hush_steps--;
        if (!hush_steps) dlg_say("The HUSH BELL's hum has faded. Wild kin can sense your team again.");
    }
    /* walking together builds bond */
    if ((step_counter & 127) == 0) {
        int lead = party_first_healthy();
        if (lead >= 0 && party[lead].bond < 255) party[lead].bond++;
    }
    if (!player.moving) check_spotting();
}

/* The village keeps new villagers home until they have a kin. */
static void edge_blocked(void)
{
    dlg_say("GRAN's voice echoes in your head: \"Never leave the village without a kin partner!\"");
    player.facing = DIR_BACK[player.facing];
}

static void field_on_enter(void)
{
    if (cur_map == MAP_RISE) lore_story(LORE_STORMSTONE_RISE);
    if (cur_map == travel.last_hearth && opt.autosave && party_count) save_write();
    grim_on_enter();
    if (events_map_entered) events_map_entered(cur_map);
    if (story_map_entered) story_map_entered(cur_map);
    if (saga_map_entered) saga_map_entered(cur_map);
    field_events_refresh();
}

static int field_busy(void)
{
    return dialog_active() || warp.active || spot.active || game_mode != MODE_FIELD;
}

/* ---------------- save prompt ---------------- */

static void save_answer(int c)
{
    if (c != 0) return;
    int ok = save_write();
    sfx_play(ok ? SFX_SAVE : SFX_ERROR);
    dlg_say(ok ? "Your progress was saved to the cartridge." : "The save failed!");
}

static void save_prompt(void)
{
    dlg_ask("Would you like to save your progress?", YES_NO, 2, save_answer);
}

/* ---------------- field mode ---------------- */

/* Back to the overworld from menus, bouts or the growth scene. */
static void field_return(void)
{
    int from_battle = game_mode == MODE_BATTLE;
    game_mode = MODE_FIELD;
    canvas_clear();
    set_brightness(0);
    field_setup_bg();
    field_load_tileset();
    follower_sync();
    field_update_camera();
    if (from_battle && battle.result == BR_LOSE)
        dlg_say("Your kin all dozed off... You carried them back to the HEARTH HALL, where they soon woke up.");
    if (evo_count) evolve_start_next();
}

static void storm_update(void)
{
    if (!storm_active()) {
        storm_flash = 0;
        return;
    }
    if (storm_flash > 0) {
        storm_flash--;
        if (!warp.active) set_brightness(storm_flash > 6 ? 6 : storm_flash > 3 ? 2 : 0);
        return;
    }
    if (rng_range(600) == 0) storm_flash = 10;
}

static void field_update(void)
{
    if (emote.timer > 0) emote.timer--;
    if (travel_rune_update()) return;   /* the RUNESTONE's spell freezes the field */
    if (dialog_active()) {
        dialog_update();
        return;
    }
    if (field_warp_update()) return;
    if (spot_update()) return;
    time_tick();
    storm_update();
    if (script_cutscene_update()) return;
    if (key_hit(KEY_START) && !player.moving) {
        sfx_play(SFX_CONFIRM);
        start_menu_open();
        return;
    }
    if ((MAPS[cur_map].flags & MF_DEBUG) && !player.moving && !dialog_active()) {
        if (key_hit(KEY_SELECT)) {
            debug_open();
            return;
        }
        if (key_hit(KEY_L)) debug_parade_shift(-WILD_MAX);
        if (key_hit(KEY_R)) debug_parade_shift(WILD_MAX);
    }
    if (key_hit(KEY_SELECT) && !player.moving && registered_item_use()) return; /* the key item registered in the bag */
    if (key_hit(KEY_SELECT) && !player.moving) { /* shortcut: straight to the LOREBOOK */
        sfx_play(SFX_CONFIRM);
        field_setup_bg();
        lorebook_open();
        return;
    }
    field_player_update();
    npcs_update();
    wild_update();
    if (!player.moving && !dialog_active() && !warp.active) check_spotting();
}

static void field_draw(void)
{
    field_update_camera();
    farm_draw_fx();
    field_draw_sprites();
    farm_draw();
    travel_dark_frame(game_mode == MODE_FIELD && !warp.active);
    if (starter_preview >= 0) {
        /* follow the cursor of the three-way choice; keep showing the pick
         * while the Keeper asks you to confirm it */
        if (choice.active && choice.count == 3 && choice.cursor != starter_preview) {
            starter_preview = choice.cursor;
            load_monster_gfx(0, STARTER_SPECIES[starter_preview], 0);
        }
        spr_push(88, 16, OT_MON_A, SQ64, OBANK_MON_A, 0, 0);
    }
}

static void new_game(void)
{
    party_count = storage_count = 0;
    for (int i = 0; i < ITEM_COUNT; i++) bag[i] = 0;
    for (int i = 0; i < SP_COUNT; i++) dex_seen[i] = dex_caught[i] = 0;
    money = 3000;
    flags_reset();
    cut_walk.active = cut_pan.active = cam_scripted = 0;
    modules_reset();
    hush_steps = 0;
    step_counter = 0;
    evo_count = 0;
    lore_reset();
    bag[ITEM_RUNESTONE] = 1;   /* always takes you home (travel.c) */
    follower.shown = 0;
    field_enter_map(MAP_HOME, 9, 3, DIR_DOWN);
}

#ifndef HAVE_MUSIC
/* No music module in this build: map changes are silent. */
static void music_map_changed(int map) { (void)map; }
#endif
