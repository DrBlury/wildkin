/*
 * Player options (stored in the save file as 16 raw bytes, changed in
 * START > OPTIONS). Kept in their own header so every module can read them.
 * The last bytes also keep two small UI preferences that travel with the
 * save: the key item registered to SELECT and the Shelf box last used,
 * and the ADMIN MODE switch (admin.c). Saves written before a byte was
 * used carry 0 there, so old saves load with everything new switched off.
 */

enum { TEXT_SLOW, TEXT_MID, TEXT_FAST, TEXT_INSTANT, TEXT_SPEED_COUNT };

static struct {
    u8 text_speed;    /* TEXT_* */
    u8 battle_anims;  /* 1 = play move animations */
    u8 sound;         /* 1 = sound effects on */
    u8 follower;      /* 1 = the lead kin walks behind the player */
    u8 autosave;      /* 1 = save when entering a HEARTH HALL */
    u8 music;         /* 1 = background music on (music.c) */
    u8 music_vol;     /* 0 = full, 1 = low, 2 = mid volume (music.c) */
    u8 hud_clock;     /* 1 = show the clock in the field */
    u8 battle_speed;  /* 0 = normal, 1 = fast animations */
    u8 bike_auto;     /* 1 = hold R not needed: the bike stays on outdoors */
    u8 registered;    /* bag item registered to SELECT, as item id + 1 (0 = none) */
    u8 shelf_box;     /* LANTERN SHELF box last viewed (new kin go there first) */
    u8 admin;         /* 1 = the ADMIN entry shows in the START menu (debug.c toggles it) */
    u8 pad[3];
} opt = { TEXT_MID, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, { 0 } };
typedef char OptionsFit16[sizeof(opt) == 16 ? 1 : -1];

static void options_reset(void)
{
    opt.text_speed = TEXT_MID;
    opt.battle_anims = 1;
    opt.sound = 1;
    opt.follower = 1;
    opt.autosave = 1;
    opt.music = 1;
    opt.music_vol = 0;
    opt.hud_clock = 0;
    opt.battle_speed = 0;
    opt.bike_auto = 0;
    opt.registered = 0;
    opt.shelf_box = 0;
    opt.admin = 0;
}
