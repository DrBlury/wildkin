/*
 * Player options (stored in the save file, changed in START > OPTIONS).
 * Kept in their own header so every module can read them.
 */

enum { TEXT_SLOW, TEXT_MID, TEXT_FAST, TEXT_INSTANT, TEXT_SPEED_COUNT };

static struct {
    u8 text_speed;    /* TEXT_* */
    u8 battle_anims;  /* 1 = play move animations */
    u8 sound;         /* 1 = sound effects on */
    u8 follower;      /* 1 = the lead kin walks behind the player */
    u8 autosave;      /* 1 = save when entering a HEARTH HALL */
    u8 music;         /* 1 = background music on (music.c) */
    u8 music_vol;     /* 0 = default volume (music.c) */
    u8 hud_clock;     /* 1 = show the clock in the field */
    u8 battle_speed;  /* 0 = normal, 1 = fast animations */
    u8 bike_auto;     /* 1 = hold R not needed: the bike stays on outdoors */
    u8 pad[6];
} opt = { TEXT_MID, 1, 1, 1, 1, 1, 0, 0, 0, 0, { 0 } };
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
}
