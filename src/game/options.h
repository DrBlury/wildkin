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
    u8 pad[3];
} opt = { TEXT_MID, 1, 1, 1, 1, { 0, 0, 0 } };

static void options_reset(void)
{
    opt.text_speed = TEXT_MID;
    opt.battle_anims = 1;
    opt.sound = 1;
    opt.follower = 1;
    opt.autosave = 1;
}
