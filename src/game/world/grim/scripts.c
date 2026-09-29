/*
 * world/grim/scripts.c -- the Ashen March and the Hollowing (W-GRIM).
 *
 * Story: after DRAKORA is answered, Keeper Linden sends you east to the
 * Ashen March (grim_keeper_talk, called from script.c keeper_after). The
 * LANTERN Hall is the dark LANTERN CRYPT in DUSKMERE (HALL MASTER MORWEN,
 * battle_start_master -> CREST_LANTERN). With all six crests the gate warden
 * opens THE OSSUARY; on the BONE THRONE you answer OSSUREX (grim_interact,
 * called from script.c field_try_interact). Answering it heals the March:
 * grim_healed() turns the MF_ASH haze and ash-fall off (field.c asks
 * grim_ash_active / grim_ash_tint / grim_draw_ash).
 *
 * Other owners may call:
 *   grim_healed()              OSSUREX answered (the March is healing)
 *   grim_ash_active(map)       MF_ASH effects should show on `map`
 *   grim_legend_hidden(sp)     1 once OSSUREX is answered (hide its OBJ_LEGEND)
 */

/* ---------------- the Ashen March heals ---------------- */

static int grim_healed(void) { return flag(FLAG_OSSUREX_ANSWERED); }

static int grim_ash_active(int map)
{
    return map >= 0 && map < MAP_COUNT && (MAPS[map].flags & MF_ASH) && !grim_healed() &&
           !(MAPS[map].flags & MF_DEBUG);
}

MAYBE_UNUSED static int grim_legend_hidden(int species)
{
    return species == SP_OSSUREX && grim_healed();
}

/* Ash haze: colours drift toward a dim violet grey. */
static u16 grim_ash_tint(u16 c)
{
    int r = c & 31, g = (c >> 5) & 31, b = (c >> 10) & 31;
    int lum = (r * 3 + g * 5 + b * 2) / 10;
    r = (r * 55 + lum * 45) / 100 * 86 / 100 + 2;
    g = (g * 55 + lum * 45) / 100 * 82 / 100 + 2;
    b = (b * 55 + lum * 45) / 100 * 88 / 100 + 4;
    return RGB15(clampi(r, 0, 31), clampi(g, 0, 31), clampi(b, 0, 31));
}

/* One ash flake (8x8, emote palette: 2 white, 6 pale blue-grey). */
#define OT_GRIM_ASH 640
static const u32 GRIM_ASH_FLAKE[8] = {
    0x00000000, 0x00000000, 0x00060000, 0x00262000, 0x00060600, 0x00000000, 0x00000000, 0x00000000,
};

/* Ash falling over the March until OSSUREX is answered (outdoors). */
static void grim_draw_ash(void)
{
    if (!grim_ash_active(cur_map)) return;
    copy32(VRAM_OBJ_TILES + OT_GRIM_ASH * 8, GRIM_ASH_FLAKE, 8);
    for (int i = 0; i < 12; i++) {
        int t = field_anim_frame + (int)(cell_hash(i, 11) % 997u);
        int sway = ((t >> 4) & 15) < 8 ? (t >> 1) & 7 : 7 - ((t >> 1) & 7);
        int x = (int)((cell_hash(i, 5) % 256u) + (unsigned)(t / 3) + 512u - (unsigned)(cam_x & 255)) % 256 - 8 + sway;
        int y = (int)((cell_hash(i, 9) % 176u) + (unsigned)(t / 2) + 704u - (unsigned)(cam_y % 176)) % 176 - 8;
        spr_push(x, y, OT_GRIM_ASH, SQ8, OBANK_EMOTE, 1, 0);
    }
}

/* ---------------- helpers ---------------- */


static int grim_crest_count(void)
{
    int n = 0;
    for (int c = 0; c < CREST_COUNT; c++) n += travel_has_crest(c);
    return n;
}

static void grim_quest_at_least(int q, int stage)
{
    if (!quest_done(q) && quest_get(q) < stage) quest_set(q, stage);
}

/* Called from field_on_enter (script.c) on every map load. */
static void grim_on_enter(void)
{
    if (cur_map == MAP_ASHEN_FIELDS) grim_quest_at_least(QUEST_HOLLOWING, 1);
    else if (cur_map == MAP_DUSKMERE) grim_quest_at_least(QUEST_HOLLOWING, 2);
    else if (cur_map == MAP_OSSUARY_1) grim_quest_at_least(QUEST_HOLLOWING, 4);
}

/* ---------------- Keeper Linden, after the storm ---------------- */

/* keeper_after (script.c) asks this once DRAKORA is answered; 1 = handled. */
static int grim_keeper_talk(void)
{
    if (!flag(FLAG_ASH_TOLD)) {
        flag_set(FLAG_ASH_TOLD);
        grim_quest_at_least(QUEST_HOLLOWING, 1);
        dlg_say("Clear skies! And yet... look at this Almanac page. East of COPPERLINE ROAD lies the Ashen March.");
        dlg_say("A century ago OSSUREX, the bone dragon, brimmed there and nobody answered it. The March burned for a summer.");
        dlg_say("Now the old kernels in the ash are waking and building bodies from bone. The Hollowing. It's OSSUREX's surplus, leaking.");
        dlg_say("Only a warden with all six Hall crests may pass the Ossuary gate in DUSKMERE. Earn them, and answer it. Please.");
        lore_story(LORE_HOLLOWING);
        return 1;
    }
    if (grim_healed() && !flag(FLAG_ASH_HEALED_TOLD)) {
        flag_set(FLAG_ASH_HEALED_TOLD);
        dlg_say("A letter from DUSKMERE: rain over the Ashen March, the first in a hundred years. You answered OSSUREX!");
        dlg_say("Two legends in one Almanac, by one warden. I'll need a bigger book.");
        return 1;
    }
    return 0;
}

/* ---------------- ASHEN FIELDS ---------------- */

static void scr_surveyor(int npc)
{
    (void)npc;
    grim_quest_at_least(QUEST_HOLLOWING, 1);
    if (!flag(FLAG_SURVEYOR_GIFT)) {
        flag_set(FLAG_SURVEYOR_GIFT);
        dlg_say("A warden! Out here! The Almanac sent me to measure the ash. Take these; HOLLOW kin rest easy in them.");
        give_item(ITEM_DUSK_LANTERN, 3);
        return;
    }
    if (lore_reveal(LSRC_SURVEYOR, 0)) return;
    dlg_say(grim_healed() ? "The ash is drinking the rain. My measurements are all wrong now, and I've never been happier."
                          : "GRAVEWOOD's east, then DUSKMERE on the mire. The Ossuary is under DUSKMERE. Mind the crows.");
}

static void scr_ashfarmer(int npc)
{
    (void)npc;
    if (flag(FLAG_ASHFARMER_DONE)) {
        dlg_say(grim_healed() ? "Rain on the pumpkins! They'll be as big as carts by autumn."
                              : "The BONE LANTERN glows all night. Not a single HOLLOW kin has wandered off since.");
        return;
    }
    if (quest_get(QUEST_ASH_LANTERN) && bag[ITEM_BONE_LANTERN] > 0) {
        bag_add(ITEM_BONE_LANTERN, -1);
        flag_set(FLAG_ASHFARMER_DONE);
        quest_set(QUEST_ASH_LANTERN, 255);
        dlg_say("A BONE LANTERN! You hand it over and the farmer hangs it on the scarecrow pole.");
        dlg_say("There. Now the lost ones can find the patch. Here, seeds from my best pumpkins, and something for your kin.");
        give_item(ITEM_SEED_PUMPKIN, 5);
        give_item(ITEM_BIG_TONIC, 2);
        return;
    }
    if (!quest_get(QUEST_ASH_LANTERN)) {
        if (lore_reveal(LSRC_ASHFARMER, 0)) return;
        quest_set(QUEST_ASH_LANTERN, 1);
        dlg_say("If you ever find a BONE LANTERN, bring it here. A light on the pole would guide the lost ones in.");
        dlg_say("Folk say they turn up in GRAVEWOOD, among the graves.");
        return;
    }
    dlg_say("A BONE LANTERN, warden. Just the one. GRAVEWOOD is east.");
}

/* People of the March: lore first, then (once healed) talk about the rain. */
static void scr_grim_talk(int npc)
{
    static const char *const HEALED[] = {
        "Rain! Real rain! I stood in it until my boots filled up.",
        "The haze is gone. I can see all the way to COPPERLINE ROAD from here.",
        "Green shoots in the ash, warden. Green!",
        "The hollow kin are so calm now. One of them followed me home.",
    };
    const NpcDef *n = &NPCS[npc];
    if (n->lore != NO_LORE && lore_reveal(n->lore, 0)) return;
    if (grim_healed()) dlg_say(HEALED[npc % 4]);
    else dlg_say(n->text ? n->text : "...");
}

/* ---------------- GRAVEWOOD ---------------- */

static void scr_sexton(int npc)
{
    (void)npc;
    if (!flag(FLAG_SEXTON_GIFT)) {
        flag_set(FLAG_SEXTON_GIFT);
        dlg_say("You walked in through the gate, not over the railing. Good manners. Take this; SEXTONE digs up plenty.");
        give_item(ITEM_BONE_MEAL, 5);
        return;
    }
    lore_reveal(LSRC_SEXTON, grim_healed() ? "The ground's warm and wet now. Best digging weather in a century."
                                           : "The graves are quiet. The ones under the ash aren't.");
}

static void scr_mourner(int npc)
{
    (void)npc;
    if (flag(FLAG_LETTER_GIVEN)) {
        dlg_say("Maren wrote back! She's coming out to the wood on Sunday. Thank you, warden.");
        return;
    }
    if (flag(FLAG_LETTER_TAKEN)) {
        dlg_say("Maren lives in the MIRE HOUSE in DUSKMERE, by the square. Please, give her my letter.");
        return;
    }
    if (lore_reveal(LSRC_MOURNER, 0)) return;
    flag_set(FLAG_LETTER_TAKEN);
    quest_set(QUEST_MIRE_LETTER, 1);
    dlg_say("Would you carry a letter for me? My sister Maren lives in DUSKMERE. We haven't spoken since the funeral.");
    sfx_play(SFX_ITEM);
    dlg_say("You took the MOURNER'S LETTER.");
}

/* ---------------- DUSKMERE ---------------- */

static void grim_enter_ossuary(int unused)
{
    (void)unused;
    flag_set(FLAG_OSSUARY_OPEN);
    grim_quest_at_least(QUEST_HOLLOWING, 4);
    sfx_play(SFX_DOOR);
    field_begin_warp(MAP_OSSUARY_1, 4, 2, DIR_DOWN);
}

static void gate_answer(int c)
{
    if (c != 0) {
        dlg_say("The gate will wait. It has had practice.");
        return;
    }
    dlg_say("OSRIC turns an iron key the size of your arm. Bone grinds on bone, and the Ossuary gate swings open.");
    dlg_call(grim_enter_ossuary, 0);
}

static void scr_gatekeeper(int npc)
{
    (void)npc;
    if (flag(FLAG_OSSUARY_OPEN) || grim_crest_count() == CREST_COUNT) {
        if (!flag(FLAG_OSSUARY_OPEN))
            dlg_say("Six crests. Six! My family has waited a hundred years to see that. By the Accord, the gate is yours.");
        if (grim_healed()) {
            dlg_say("OSSUREX sleeps easy now. The gate stays open for you, warden.");
        }
        dlg_ask("Go down into the Ossuary?", YES_NO, 2, gate_answer);
        return;
    }
    if (lore_reveal(LSRC_GATEKEEPER, 0)) return;
    char msg[160];
    str_copy(msg, "The Accord asks for six crests. You still need:");
    int first = 1;
    for (int c = 0; c < CREST_COUNT; c++) {
        if (travel_has_crest(c)) continue;
        str_put(msg, first ? " " : ", ");
        str_put(msg, CREST_NAMES[c]);
        first = 0;
    }
    str_put(msg, ".");
    dlg_say(msg);
    if (!travel_has_crest(CREST_LANTERN))
        dlg_say("The LANTERN crest is close: MORWEN keeps it in the crypt across the boardwalk.");
}

static void scr_bellkeeper(int npc)
{
    (void)npc;
    if (!flag(FLAG_BELL_GIFT)) {
        flag_set(FLAG_BELL_GIFT);
        dlg_say("Welcome to DUSKMERE, the town that kept its lanterns lit. Here: every visitor gets a bell of their own.");
        give_item(ITEM_HUSH_BELL, 1);
        return;
    }
    if (lore_reveal(LSRC_BELLKEEPER, 0)) return;
    dlg_say(grim_healed() ? "I rang the mire bell yesterday. Just once. It's the first time it has ever rung for good news."
                          : "The bell has been silent a hundred years. May it stay that way, unless it's for good news.");
}

static void scr_dusk_tender(int npc)
{
    (void)npc;
    dlg_ask("Welcome to the DUSK HEARTH HALL. The fire's peat, but it's warm. Rest your kin?", HEARTH_MENU, 3,
            heal_answer);
}

static const u8 DUSK_STOCK[] = {
    ITEM_LANTERN, ITEM_GLOW_LANTERN, ITEM_STAR_LANTERN, ITEM_TONIC, ITEM_BIG_TONIC, ITEM_GRAND_TONIC,
    ITEM_SOOTHE_BALM, ITEM_WAKE_BELL, ITEM_HUSH_BELL, ITEM_HOLLOW_SHARD,
};

static void dusk_shop_answer(int c)
{
    if (c == 0) shop_open_stock(DUSK_STOCK, (int)sizeof(DUSK_STOCK));
    else if (c == 1) dlg_say("HOLLOW SHARDS come up out of the peat. DIGGET touch one and grow into SEXTONE, just like that.");
    else dlg_say("Keep your lantern lit.");
}

static void scr_dusk_shop(int npc)
{
    (void)npc;
    dlg_ask("DUSK SHOP. Lanterns, tonics, shards. What'll it be?", SHOP_MENU, 3, dusk_shop_answer);
}

static void scr_sister(int npc)
{
    (void)npc;
    if (flag(FLAG_LETTER_TAKEN) && !flag(FLAG_LETTER_GIVEN)) {
        flag_set(FLAG_LETTER_GIVEN);
        quest_set(QUEST_MIRE_LETTER, 255);
        dlg_say("A letter? From Ada? ...She wants to see me. After all this time.");
        dlg_say("Thank you, warden. Take these; my husband brewed them, and he'd want them used.");
        give_item(ITEM_REVIVAL_BREW, 2);
        return;
    }
    dlg_say(flag(FLAG_LETTER_GIVEN) ? "Sunday I'm walking out to GRAVEWOOD to see my sister. I've baked for her."
                                    : "Mind the boardwalk, dear. The planks by the channel are loose.");
}

/* ---------------- the LANTERN CRYPT: HALL MASTER MORWEN ---------------- */

static void morwen_end(int result)
{
    if (result != BR_WIN) return;
    trainer_mark_beaten(TR_MORWEN);
    if (flag(FLAG_LANTERN_CREST)) return;
    flag_set(FLAG_LANTERN_CREST);
    travel_award_crest(CREST_LANTERN);
    grim_quest_at_least(QUEST_HOLLOWING, 3);
    sfx_play(SFX_ITEM);
    dlg_say("MORWEN lights the last lamp of the crypt and presses something warm into your hand.");
    dlg_say("You received the LANTERN CREST! Five of the six crests the Accord asks for at the Ossuary gate.");
    lore_story(LORE_LANTERN_CRYPT);
    dlg_say("MORWEN: And these, for the dark places. A light you carry is worth ten on the wall.");
    give_item(ITEM_BONE_LANTERN, 3);
}

static void morwen_answer(int c)
{
    if (c != 0) {
        dlg_say("The dark will keep. So will I.");
        return;
    }
    static TrainerTeam t;
    t = team_from(&TRAINERS[TR_MORWEN], BSCENE_CRYPT);
    battle_end_hook = morwen_end;
    battle_start_master(&t);
}

static void scr_morwen(int npc)
{
    (void)npc;
    if (flag(FLAG_LANTERN_CREST)) {
        dlg_say(grim_healed() ? "You answered OSSUREX. I can feel it in the stone: the crypt is cooler. Rest well, warden."
                              : "Five crests... six, soon. When the gate opens, go softly. OSSUREX has never had a friend.");
        return;
    }
    if (party_first_healthy() < 0) {
        dlg_say("Your kin are dozing. Carry them back to the HEARTH HALL, then find me again. In the dark.");
        return;
    }
    dlg_say("You found me. Most wardens are still walking into the wall that isn't there.");
    dlg_ask("I am MORWEN, Master of the LANTERN Hall. Six HOLLOW kin, one crest. Shall we?", YES_NO, 2,
            morwen_answer);
}

/* ---------------- the BONE THRONE: OSSUREX ---------------- */

static void ossurex_end(int result)
{
    if (result == BR_WIN || result == BR_CAUGHT) {
        flag_set(FLAG_OSSUREX_ANSWERED);
        if (result == BR_CAUGHT) flag_set(FLAG_OSSUREX_JOINED);
        quest_set(QUEST_HOLLOWING, 255);
        dlg_say("A hundred years of heat pours out of OSSUREX at once, and the Bone Throne rings like the mire bell.");
        dlg_say(result == BR_CAUGHT ? "The bone dragon settles into your lantern, its kernel calm and cool at last."
                                    : "OSSUREX lowers its great skull onto the throne and sleeps: truly sleeps, for the first time.");
        dlg_say("Far above, over the Ashen March, the haze thins and the first rain in a century begins to fall.");
        lore_story(LORE_ASH_GREEN);
    } else {
        dlg_say("OSSUREX is still brimming. Rest your kin and come back; it isn't going anywhere.");
    }
}

static void ossurex_begin(int unused)
{
    (void)unused;
    int level = clampi(party_max_level() + 3, 50, 70);
    Monster o = monster_make(SP_OSSUREX, level);
    o.met_map = MAP_BONE_THRONE;
    battle_next_scene = BSCENE_LAIR;
    battle_end_hook = ossurex_end;
    battle_start_wild(o);
    battle.no_run = 1;
}

static int on_throne(int x, int y)
{
    return cur_map == MAP_BONE_THRONE && x >= BONE_THRONE_X && x < BONE_THRONE_X + 3 && y >= BONE_THRONE_Y &&
           y < BONE_THRONE_Y + 3;
}

/* Facing (x, y): the BONE THRONE. Called from field_try_interact before
 * obj_interact, so the OBJ_LEGEND on the throne plays this story. */
static int grim_interact(int x, int y)
{
    int candle = cur_map == MAP_BARROW_A && x == 4 && y == 3 ? FLAG_CANDLE_A :
                 cur_map == MAP_BARROW_B && x == 4 && y == 3 ? FLAG_CANDLE_B :
                 cur_map == MAP_HOLLOW_DOWNS && x == 12 && y == 29 ? FLAG_CANDLE_CAIRN : 0;
    if (candle) {
        if (!flag(candle)) { flag_set(candle); dlg_say("You light a candle for the buried kin."); }
        else dlg_say("The candle is still burning.");
        return 1;
    }
    if (!on_throne(x, y)) return 0;
    if (grim_healed()) {
        dlg_say(flag(FLAG_OSSUREX_JOINED) ? "The Bone Throne is empty. Its bones are cool to the touch."
                                          : "OSSUREX sleeps on the throne, breathing slow and even. It's only sleeping now.");
        return 1;
    }
    if (party_first_healthy() < 0) {
        dlg_say("The throne radiates heat like an oven door... but your kin are dozing. Rest them first.");
        return 1;
    }
    if (!flag(FLAG_OSSUREX_MET)) {
        flag_set(FLAG_OSSUREX_MET);
        dlg_say("The bones on the throne are warm. Warmer. They shift, and rise, and keep rising.");
        dlg_say("A skull the size of a cart turns toward your lantern. Green fire kindles in its eyes: OSSUREX, the bone dragon!");
        lore_story(LORE_OSSUREX);
    } else {
        dlg_say("OSSUREX uncoils from the throne once more, heat shimmering off its stone-hard bones.");
    }
    dlg_call(ossurex_begin, 0);
    return 1;
}

static void scr_vigil(int npc)
{
    (void)npc;
    if (grim_healed()) {
        dlg_say("It's over. Forty years of vigil, and it's over. I'm going home to DUSKMERE to sleep in a real bed.");
        return;
    }
    if (lore_reveal(LSRC_VIGIL, 0)) return;
    if (!flag(FLAG_VIGIL_GIFT)) {
        flag_set(FLAG_VIGIL_GIFT);
        dlg_say("Take these. I kept them for the warden who would come. Your kin will need them.");
        give_item(ITEM_REVIVAL_BREW, 2);
        give_item(ITEM_GRAND_TONIC, 2);
        return;
    }
    dlg_say("Face the throne and lay your hand on the bones. It will wake for you. Go softly.");
}

/* Until E3 visibility is merged the captain physically occupies the only lane.
 * Talk lets a qualified warden through without letting an early player walk by. */
static void grim_across_accord(int ignored)
{
    (void)ignored;
    field_begin_warp(MAP_HOLLOW_DOWNS, 20, 2, DIR_DOWN);
}

static void grim_back_to_copperline(int ignored)
{
    (void)ignored;
    field_begin_warp(MAP_COPPERLINE, 20, 34, DIR_UP);
}

static void scr_audra(int npc)
{
    (void)npc;
    if (player.y < 6) {
        dlg_say("ACCORD PASS checked. Follow me back to COPPERLINE.");
        dlg_call(grim_back_to_copperline, 0);
        return;
    }
    if (!flag(FLAG_RIME_CREST)) {
        char msg[120];
        str_copy(msg, "Only wardens with four crests may enter the March. You have ");
        str_put_int(msg, grim_crest_count());
        str_put(msg, ".");
        dlg_say(msg);
        return;
    }
    dlg_say("Four crests. The quarantine opens to you. HOLLOW kin borrow bone and ash to build a body; keep your lantern lit.");
    lore_reveal(LSRC_AUDRA, "HOLLOW kin bind their kernels to borrowed remains. Steady light calms the bind.");
    dlg_call(grim_across_accord, 0);
}

static const u8 ACCORD_STOCK[] = { ITEM_BIG_TONIC, ITEM_HUSH_BELL, ITEM_BONE_LANTERN };
static void accord_shop_answer(int choice)
{
    if (choice == 0) shop_open_stock(ACCORD_STOCK, (int)sizeof(ACCORD_STOCK));
}
static void scr_accord_shop(int npc)
{
    (void)npc;
    dlg_ask("Accord supplies. Tonics, hush bells and bone lanterns?", SHOP_MENU, 3, accord_shop_answer);
}

static void scr_maud(int npc)
{
    (void)npc;
    if (!quest_get(QUEST_BARROW_CANDLES)) {
        quest_set(QUEST_BARROW_CANDLES, 1);
        dlg_say("The Kinship vows ask us to remember the lost. Light both barrow candles and the cairn on the downs.");
    } else if (!flag(FLAG_CANDLES_REWARD) && flag(FLAG_CANDLE_A) &&
               flag(FLAG_CANDLE_B) && flag(FLAG_CANDLE_CAIRN)) {
        flag_set(FLAG_CANDLES_REWARD);
        quest_set(QUEST_BARROW_CANDLES, 255);
        dlg_say("Three flames. The old vows hold. Take these bells for the way ahead.");
        give_item(ITEM_HUSH_BELL, 3);
    } else {
        dlg_say(flag(FLAG_CANDLES_REWARD) ? "A flame for every traveller. Rest now."
                                         : "Two candles in the barrows, one at the cairn. None need an item to light.");
    }
    lore_reveal(LSRC_MAUD, "The Kinship vow: care for every kernel, including the ones left behind.");
    dlg_ask("Rest your kin at the WAYCHAPEL?", HEARTH_MENU, 3, heal_answer);
}

/* Wrong symbols extinguish only the current sequence; the gallery route
 * stays open, and a solved shortcut is never reset. */
static void dusk_sequence_reset(void)
{
    flag_clear(FLAG_DUSK_FIRST);
    flag_clear(FLAG_DUSK_SECOND);
    dlg_say("The sigils fade harmlessly. Roots, bell, lantern; try again.");
}

static void scr_dusk_root(int npc)
{
    (void)npc;
    if (flag(FLAG_DUSK_SHORTCUT)) { dlg_say("The roots still glow beside the opened shortcut."); return; }
    flag_set(FLAG_DUSK_FIRST);
    flag_clear(FLAG_DUSK_SECOND);
    dlg_say("The root sigil wakes. A distant bell answers.");
}

static void scr_dusk_bell(int npc)
{
    (void)npc;
    if (flag(FLAG_DUSK_SHORTCUT)) { dlg_say("The bell's low note still rings."); return; }
    if (!flag(FLAG_DUSK_FIRST) || flag(FLAG_DUSK_SECOND)) { dusk_sequence_reset(); return; }
    flag_set(FLAG_DUSK_SECOND);
    dlg_say("The bell rings once. The lantern sigil waits.");
}

static void scr_dusk_lantern(int npc)
{
    (void)npc;
    if (flag(FLAG_DUSK_SHORTCUT)) { dlg_say("The lantern lights the opened shortcut."); return; }
    if (!flag(FLAG_DUSK_SECOND)) { dusk_sequence_reset(); return; }
    flag_set(FLAG_DUSK_SHORTCUT);
    map_patches_reapply();
    dlg_say("Roots, bell, lantern. A stone gives way: a lasting path to the Duskmere well!");
}
