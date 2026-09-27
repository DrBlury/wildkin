/* Event interaction scripts; the underlying day is rolled by E10. */
static void scr_gazette(int npc)
{
    (void)npc;
    for (int i = 0; i < 5; i++) dlg_say(events_gazette_line(i));
}
static void scr_caravan(int npc)
{
    (void)npc;
    if (!events_caravan_here(cur_map)) {
        dlg_say("The caravan has moved on. See the Gazette for today's stop.");
        return;
    }
    static const u8 pool[] = { ITEM_TONIC, ITEM_LURE_INCENSE, ITEM_WAYSTONE,
        ITEM_SEED_MOTEBLOOM, ITEM_SEED_SNOWPEA, ITEM_MINT_TEA, ITEM_METAL_SHARD };
    static u8 stock[5];
    for (int i = 0; i < 4; i++) stock[i] = pool[(gtime.day + i + events.caravan_map) % (int)sizeof(pool)];
    stock[4] = ITEM_ASTRAL_SHARD;
    shop_open_stock(stock, (int)sizeof(stock));
}
static void scr_rematch_board(int npc)
{
    (void)npc;
    dlg_say(events_gazette_line(4));
    for (int i = 0; i < REMATCH_COUNT; i++) if (events_rematch_ready(REMATCHES[i].trainer)) {
        char line[40];
        str_copy(line, REMATCHES[i].name);
        str_put(line, " WANTS A REMATCH");
        dlg_say(line);
    }
}
static void scr_festival(int npc)
{
    (void)npc;
    if (!events_active(EV_FESTIVAL)) return;
    static const char *const lines[] = {
        "", "KINDLING DAY: A new year!", "MILLRACE: Cheer the runners!",
        "LANTERN NIGHT: Follow the lights.", "FROST FAIR: Welcome!", "STARFALL: Watch the sky!"
    };
    dlg_say(lines[events_arg(EV_FESTIVAL)]);
}
