/*
 * Sound effects on the four DMG-style PSG channels.
 *
 *   ch1  square with hardware sweep   ch2  square
 *   ch3  4-bit wave (soft pads)       ch4  noise
 *
 * Every effect is one to three short tracks, each a list of notes on one
 * channel. sfx_update() (called once per frame) steps the notes: it
 * starts each note (restart bit) and slides its pitch. An effect only
 * takes a channel that is idle or playing something of equal or lower
 * priority, so a text blip never cuts a level-up jingle short.
 * The effects are silent while opt.sound is 0. Music plays on Direct Sound
 * (music.c) and ducks while a fanfare (priority 5) is sounding here.
 *
 * Host builds map the I/O registers to plain memory, so the tests run the
 * sequencer too.
 */

/* ---------------- registers ---------------- */

#define SREG_SND1_SWEEP  REG16(0x060)
#define SREG_SND1_ENV    REG16(0x062)
#define SREG_SND1_FREQ   REG16(0x064)
#define SREG_SND2_ENV    REG16(0x068)
#define SREG_SND2_FREQ   REG16(0x06C)
#define SREG_SND3_SEL    REG16(0x070)
#define SREG_SND3_VOL    REG16(0x072)
#define SREG_SND3_FREQ   REG16(0x074)
#define SREG_SND4_ENV    REG16(0x078)
#define SREG_SND4_FREQ   REG16(0x07C)
#define SREG_SNDCNT_L    REG16(0x080)
#define SREG_SNDCNT_H    REG16(0x082)
#define SREG_SNDCNT_X    REG16(0x084)
#define SREG_WAVE(i)     REG32(0x090 + (i) * 4)

/* ---------------- ids ---------------- */

enum {
    SFX_NONE,
    /* menus and field */
    SFX_CURSOR, SFX_CONFIRM, SFX_CANCEL, SFX_ERROR, SFX_BUMP, SFX_DOOR, SFX_TEXT,
    SFX_SAVE, SFX_ITEM, SFX_HEAL, SFX_LEVEL_UP, SFX_EXCLAIM, SFX_LEDGE, SFX_GROW,
    SFX_LORE, SFX_BUY, SFX_RUSTLE,
    /* battle: hits */
    SFX_HIT_LIGHT, SFX_HIT, SFX_HIT_STRONG, SFX_WEAK_SPOT, SFX_PERFECT, SFX_SHRUGGED,
    SFX_MISS,
    /* battle: move flavour by type */
    SFX_SWING, SFX_FIRE, SFX_SPLASH, SFX_LEAF, SFX_ZAP, SFX_ICE, SFX_ROCK, SFX_WIND,
    SFX_DREAM, SFX_BUZZ, SFX_DUSK, SFX_VENOM, SFX_WYRM,
    /* battle: other */
    SFX_CHARGE, SFX_THUNDER, SFX_ROAR, SFX_DRAIN, SFX_SPARKLE, SFX_STAT_UP,
    SFX_STAT_DOWN, SFX_STATUS, SFX_DOZE, SFX_THROW, SFX_WOBBLE, SFX_BEFRIEND,
    SFX_RUN, SFX_SEND_OUT, SFX_TRAIT, SFX_WIPE, SFX_BREAK_FREE,
    /* battle: the four newer types, halls and legends */
    SFX_HOLLOW, SFX_RELIC, SFX_METAL, SFX_ASTRAL, SFX_KNELL, SFX_BANNER, SFX_VICTORY,
    SFX_COUNT
};

/* ---------------- note data ---------------- */

enum {
    SN_C2 = 36, SN_D2 = 38, SN_E2 = 40, SN_F2 = 41, SN_G2 = 43, SN_A2 = 45, SN_B2 = 47,
    SN_C3 = 48, SN_D3 = 50, SN_E3 = 52, SN_F3 = 53, SN_G3 = 55, SN_A3 = 57, SN_B3 = 59,
    SN_C4 = 60, SN_D4 = 62, SN_E4 = 64, SN_F4 = 65, SN_G4 = 67, SN_A4 = 69, SN_B4 = 71,
    SN_C5 = 72, SN_D5 = 74, SN_E5 = 76, SN_F5 = 77, SN_G5 = 79, SN_A5 = 81, SN_B5 = 83,
    SN_C6 = 84, SN_D6 = 86, SN_E6 = 88, SN_F6 = 89, SN_G6 = 91, SN_A6 = 93, SN_B6 = 95,
    SN_C7 = 96, SN_D7 = 98, SN_E7 = 100, SN_F7 = 101, SN_G7 = 103, SN_A7 = 105, SN_B7 = 107,
};

/* 11-bit square frequency for MIDI notes 36..107 (131072 / (2048 - n) Hz). */
static const u16 SFX_NOTE_FREQ[72] = {
    44, 157, 263, 363, 457, 547, 631, 711, 786, 856, 923, 986, 1046, 1102, 1155, 1205,
    1253, 1297, 1339, 1379, 1417, 1452, 1486, 1517, 1547, 1575, 1602, 1627, 1650, 1673,
    1694, 1714, 1732, 1750, 1767, 1783, 1798, 1812, 1825, 1837, 1849, 1860, 1871, 1881,
    1890, 1899, 1907, 1915, 1923, 1930, 1936, 1943, 1949, 1954, 1959, 1964, 1969, 1974,
    1978, 1982, 1985, 1989, 1992, 1995, 1998, 2001, 2004, 2006, 2009, 2011, 2013, 2015,
};

/*
 * One note. Squares: note = MIDI number (0 = rest), env = NRx2 (volume << 4
 * | increase << 3 | step), arg = duty 0..3, slide = frequency units per
 * frame, sweep = NR10 (ch1 only). Wave: env = volume code (1 full, 2 half,
 * 3 quarter), arg = waveform. Noise: note = NR43 (clock shift << 4 |
 * 7-bit << 3 | ratio), env = NR42. len 0 ends the track.
 */
typedef struct { u8 len, note, env, arg; s8 slide; u8 sweep; } SfxNote;

#define SQ(l, n, e, d)          { l, n, e, d, 0, 0 }
#define SQS(l, n, e, d, s)      { l, n, e, d, s, 0 }
#define SW(l, n, e, d, sw)      { l, n, e, d, 0, sw }
#define NZ(l, n, e)             { l, n, e, 0, 0, 0 }
#define WV(l, n, v, w, s)       { l, n, v, w, s, 0 }
#define REST(l)                 { l, 0, 0, 0, 0, 0 }
#define SEND                    { 0, 0, 0, 0, 0, 0 }

enum { SWAVE_SINE, SWAVE_TRI, SWAVE_COUNT };

typedef struct { u8 ch, prio; const SfxNote *notes; } SfxTrack;
typedef struct { SfxTrack t[3]; } SfxDef;

/* ---- menus / field ---- */
static const SfxNote sfxn_cursor[] = { SQ(3, SN_E6, 0x71, 2), SEND };
static const SfxNote sfxn_confirm[] = { SQ(3, SN_C6, 0xA1, 2), SQ(7, SN_G6, 0xA2, 2), SEND };
static const SfxNote sfxn_cancel[] = { SQ(3, SN_G5, 0x91, 2), SQ(7, SN_C5, 0x92, 2), SEND };
static const SfxNote sfxn_error[] = { SQ(5, SN_A3, 0xC1, 3), REST(2), SQ(9, SN_A3, 0xC2, 3), SEND };
static const SfxNote sfxn_bump_n[] = { NZ(6, 0x74, 0xB1), SEND };
static const SfxNote sfxn_bump_s[] = { SW(6, SN_A3, 0x91, 2, 0x1B), SEND };
static const SfxNote sfxn_door_n[] = { NZ(3, 0x61, 0x60), NZ(3, 0x51, 0x70), NZ(3, 0x41, 0x80), NZ(9, 0x31, 0x93), SEND };
static const SfxNote sfxn_door_s[] = { SQ(4, SN_E4, 0x62, 1), SQ(9, SN_B4, 0x63, 1), SEND };
static const SfxNote sfxn_text[] = { SQ(2, SN_D6, 0x31, 2), SEND };
static const SfxNote sfxn_save_a[] = {
    SQ(4, SN_C5, 0xB1, 2), SQ(4, SN_E5, 0xB1, 2), SQ(4, SN_G5, 0xB1, 2), SQ(14, SN_C6, 0xB3, 2), SEND };
static const SfxNote sfxn_save_b[] = {
    REST(2), SQ(4, SN_C5, 0x51, 2), SQ(4, SN_E5, 0x51, 2), SQ(4, SN_G5, 0x51, 2), SQ(12, SN_C6, 0x53, 2), SEND };
static const SfxNote sfxn_item_a[] = {
    SQ(5, SN_G5, 0xB2, 2), SQ(5, SN_C6, 0xB2, 2), SQ(5, SN_E6, 0xB2, 2), SQ(5, SN_G6, 0xB2, 2),
    REST(2), SQ(4, SN_E6, 0xA1, 2), SQ(20, SN_G6, 0xB4, 2), SEND };
static const SfxNote sfxn_item_b[] = {
    SQ(5, SN_E5, 0x82, 1), SQ(5, SN_G5, 0x82, 1), SQ(5, SN_C6, 0x82, 1), SQ(5, SN_E6, 0x82, 1),
    REST(2), SQ(4, SN_C6, 0x71, 1), SQ(20, SN_E6, 0x84, 1), SEND };
static const SfxNote sfxn_heal_a[] = {
    SQ(6, SN_C5, 0xA2, 1), SQ(6, SN_E5, 0xA2, 1), SQ(6, SN_G5, 0xA2, 1), SQ(6, SN_C6, 0xA2, 1),
    SQ(6, SN_E5, 0xA2, 1), SQ(6, SN_G5, 0xA2, 1), SQ(6, SN_C6, 0xA2, 1), SQ(24, SN_E6, 0xA5, 1), SEND };
static const SfxNote sfxn_heal_w[] = {
    WV(24, SN_C4, 2, SWAVE_SINE, 0), WV(24, SN_G3, 2, SWAVE_SINE, 0), WV(24, SN_C4, 3, SWAVE_SINE, 0), SEND };
static const SfxNote sfxn_lvl_a[] = {
    SQ(4, SN_C5, 0xC1, 2), SQ(4, SN_E5, 0xC1, 2), SQ(4, SN_G5, 0xC1, 2), SQ(4, SN_C6, 0xC1, 2),
    REST(2), SQ(4, SN_G5, 0xB1, 2), SQ(18, SN_C6, 0xB4, 2), SEND };
static const SfxNote sfxn_lvl_b[] = {
    SQ(4, SN_E4, 0x81, 1), SQ(4, SN_G4, 0x81, 1), SQ(4, SN_C5, 0x81, 1), SQ(4, SN_E5, 0x81, 1),
    REST(2), SQ(4, SN_E5, 0x71, 1), SQ(18, SN_G5, 0x74, 1), SEND };
static const SfxNote sfxn_excl_a[] = { SQ(4, SN_B5, 0xD1, 2), SQ(12, SN_E6, 0xD2, 2), SEND };
static const SfxNote sfxn_excl_b[] = { SQ(4, SN_B6, 0x71, 1), SQ(12, SN_E7, 0x72, 1), SEND };
static const SfxNote sfxn_ledge_s[] = { SW(10, SN_G4, 0xB2, 2, 0x14), SEND };
static const SfxNote sfxn_ledge_n[] = { REST(12), NZ(5, 0x64, 0x81), SEND };
static const SfxNote sfxn_grow_a[] = {
    SQ(3, SN_E6, 0xA1, 1), SQ(3, SN_G6, 0xA1, 1), SQ(3, SN_B6, 0xA1, 1), SQ(3, SN_E7, 0xA1, 1),
    SQ(3, SN_G7, 0x91, 1), SQ(10, SN_B7, 0x83, 1), SEND };
static const SfxNote sfxn_grow_b[] = {
    REST(2), SQ(3, SN_B5, 0x61, 2), SQ(3, SN_E6, 0x61, 2), SQ(3, SN_G6, 0x61, 2), SQ(3, SN_B6, 0x61, 2),
    SQ(12, SN_E7, 0x53, 2), SEND };
static const SfxNote sfxn_lore_a[] = { SQ(6, SN_E6, 0xA3, 2), SQ(28, SN_B6, 0xA6, 2), SEND };
static const SfxNote sfxn_lore_b[] = { REST(4), SQ(6, SN_B5, 0x63, 2), SQ(26, SN_E6, 0x66, 2), SEND };
static const SfxNote sfxn_buy[] = { SQ(3, SN_B5, 0xB1, 2), SQ(14, SN_E6, 0xB3, 2), SEND };
static const SfxNote sfxn_rustle[] = { NZ(3, 0x23, 0x51), NZ(3, 0x33, 0x41), NZ(4, 0x23, 0x31), SEND };

/* ---- battle: hits ---- */
static const SfxNote sfxn_hitl_n[] = { NZ(2, 0x22, 0xA1), NZ(6, 0x44, 0x91), SEND };
static const SfxNote sfxn_hitl_s[] = { SW(5, SN_E4, 0x81, 2, 0x1A), SEND };
static const SfxNote sfxn_hit_n[] = { NZ(2, 0x12, 0xE1), NZ(9, 0x44, 0xC1), SEND };
static const SfxNote sfxn_hit_s[] = { SW(7, SN_C4, 0xC1, 2, 0x19), SEND };
static const SfxNote sfxn_hits_n[] = { NZ(3, 0x02, 0xF1), NZ(16, 0x55, 0xF2), SEND };
static const SfxNote sfxn_hits_s[] = { SW(12, SN_G3, 0xF2, 2, 0x29), SEND };
static const SfxNote sfxn_weak_p[] = { SQ(3, SN_C7, 0xC1, 2), SQ(10, SN_G6, 0xA2, 2), SEND };
static const SfxNote sfxn_perf_n[] = { NZ(2, 0x00, 0xF1), NZ(4, 0x21, 0xE1), NZ(14, 0x52, 0xC2), SEND };
static const SfxNote sfxn_perf_p[] = { SQ(2, SN_E7, 0xF1, 3), SQ(4, SN_B6, 0xD1, 2), SQ(12, SN_E7, 0xA3, 2), SEND };
static const SfxNote sfxn_shrug_n[] = { NZ(7, 0x66, 0x91), SEND };
static const SfxNote sfxn_shrug_s[] = { SQS(8, SN_E3, 0x81, 1, -6), SEND };
static const SfxNote sfxn_miss[] = { NZ(3, 0x53, 0x40), NZ(3, 0x43, 0x60), NZ(3, 0x33, 0x70), NZ(7, 0x23, 0x72), SEND };

/* ---- battle: move flavour ---- */
static const SfxNote sfxn_swing[] = { NZ(3, 0x42, 0x60), NZ(5, 0x32, 0x82), SEND };
static const SfxNote sfxn_fire_n[] = { NZ(8, 0x51, 0x5D), NZ(22, 0x41, 0xC3), SEND };
static const SfxNote sfxn_fire_s[] = { SQS(14, SN_C3, 0x62, 3, 4), SEND };
static const SfxNote sfxn_splash_n[] = { NZ(3, 0x21, 0xC1), NZ(14, 0x33, 0xA2), SEND };
static const SfxNote sfxn_splash_s[] = {
    SQS(4, SN_C5, 0x71, 2, 20), SQS(4, SN_E5, 0x61, 2, 20), SQS(5, SN_D5, 0x51, 2, 20), SEND };
static const SfxNote sfxn_leaf_n[] = { NZ(3, 0x31, 0x50), NZ(8, 0x21, 0x72), SEND };
static const SfxNote sfxn_leaf_s[] = { SQ(3, SN_E6, 0x41, 1), SQ(7, SN_A6, 0x42, 1), SEND };
static const SfxNote sfxn_zap_s[] = {
    SQ(2, SN_C6, 0xD1, 0), SQ(2, SN_C7, 0xD1, 0), SQ(2, SN_G5, 0xD1, 0), SQ(2, SN_G6, 0xD1, 0),
    SQ(2, SN_D6, 0xC1, 0), SQ(7, SN_D7, 0xB2, 0), SEND };
static const SfxNote sfxn_zap_n[] = { NZ(14, 0x08, 0xA2), SEND };
static const SfxNote sfxn_ice_s[] = {
    SQ(3, SN_E7, 0x91, 1), SQ(3, SN_C7, 0x81, 1), SQ(3, SN_G7, 0x71, 1), SQ(9, SN_D7, 0x62, 1), SEND };
static const SfxNote sfxn_ice_n[] = { NZ(9, 0x10, 0x52), SEND };
static const SfxNote sfxn_rock_n[] = { NZ(22, 0x77, 0xC3), SEND };
static const SfxNote sfxn_rock_s[] = { SQS(14, SN_E2, 0x92, 3, -1), SEND };
static const SfxNote sfxn_wind[] = { NZ(8, 0x33, 0x2D), NZ(18, 0x33, 0xA3), SEND };
static const SfxNote sfxn_dream[] = {
    WV(6, SN_E5, 1, SWAVE_SINE, 6), WV(6, SN_G5, 1, SWAVE_SINE, -6), WV(6, SN_E5, 1, SWAVE_SINE, 6),
    WV(12, SN_B5, 2, SWAVE_SINE, -4), SEND };
static const SfxNote sfxn_buzz[] = {
    SQ(2, SN_A4, 0x92, 0), SQ(2, SN_B4, 0x92, 0), SQ(2, SN_A4, 0x92, 0), SQ(2, SN_B4, 0x92, 0),
    SQ(2, SN_A4, 0x82, 0), SQ(2, SN_B4, 0x82, 0), SQ(2, SN_A4, 0x72, 0), SQ(4, SN_B4, 0x72, 0), SEND };
static const SfxNote sfxn_dusk_s[] = { SQS(22, SN_G3, 0xA3, 1, -3), SEND };
static const SfxNote sfxn_dusk_n[] = { NZ(18, 0x74, 0x63), SEND };
static const SfxNote sfxn_venom[] = {
    SQS(3, SN_C4, 0x81, 1, 30), SQS(3, SN_E4, 0x71, 1, 30), SQS(3, SN_B3, 0x81, 1, 30),
    SQS(5, SN_D4, 0x61, 1, 30), SEND };
static const SfxNote sfxn_wyrm_n[] = { NZ(26, 0x75, 0xF3), SEND };
static const SfxNote sfxn_wyrm_s[] = { SQS(26, SN_G2, 0xD3, 3, -1), SEND };

/* ---- battle: other ---- */
static const SfxNote sfxn_charge[] = { SQS(30, SN_C4, 0x4B, 2, 8), SQ(4, SN_C6, 0x91, 2), SEND };
static const SfxNote sfxn_thunder_n[] = { NZ(3, 0x01, 0xF1), NZ(32, 0x65, 0xF4), SEND };
static const SfxNote sfxn_thunder_s[] = { SQ(3, SN_C7, 0xF1, 0), SQS(10, SN_C5, 0xB2, 0, -20), SEND };
static const SfxNote sfxn_roar_n[] = { NZ(32, 0x86, 0xF4), SEND };
static const SfxNote sfxn_roar_a[] = { SQS(30, SN_E2, 0xF4, 3, -1), SEND };
static const SfxNote sfxn_roar_b[] = { SQS(30, SN_B2, 0xC4, 2, -1), SEND };
static const SfxNote sfxn_drain[] = { SQS(18, SN_C6, 0x93, 1, -8), SEND };
static const SfxNote sfxn_sparkle_a[] = {
    SQ(4, SN_G6, 0x81, 1), SQ(4, SN_C7, 0x81, 1), SQ(4, SN_E7, 0x71, 1), SQ(4, SN_G6, 0x71, 1),
    SQ(4, SN_C7, 0x61, 1), SQ(10, SN_E7, 0x53, 1), SEND };
static const SfxNote sfxn_sparkle_w[] = { WV(40, SN_C5, 3, SWAVE_SINE, 0), SEND };
static const SfxNote sfxn_statup[] = {
    SQ(3, SN_C5, 0xA1, 2), SQ(3, SN_E5, 0xA1, 2), SQ(3, SN_G5, 0xA1, 2), SQ(3, SN_C6, 0xA1, 2),
    SQ(9, SN_E6, 0xA2, 2), SEND };
static const SfxNote sfxn_statdown[] = {
    SQ(3, SN_C6, 0xA1, 2), SQ(3, SN_G5, 0xA1, 2), SQ(3, SN_E5, 0xA1, 2), SQ(3, SN_C5, 0xA1, 2),
    SQ(9, SN_G4, 0xA2, 2), SEND };
static const SfxNote sfxn_status[] = {
    SQ(4, SN_E5, 0xA1, 1), SQ(4, SN_G5, 0xA1, 1), SQ(4, SN_E5, 0x91, 1), SQ(4, SN_G5, 0x91, 1),
    SQ(4, SN_E5, 0x81, 1), SQ(8, SN_G5, 0x72, 1), SEND };
static const SfxNote sfxn_doze_s[] = { SQS(34, SN_C5, 0xC4, 2, -6), SEND };
static const SfxNote sfxn_doze_n[] = { REST(6), NZ(22, 0x76, 0x83), SEND };
static const SfxNote sfxn_throw_n[] = { NZ(3, 0x63, 0x60), NZ(3, 0x53, 0x70), NZ(3, 0x43, 0x80), NZ(7, 0x33, 0x72), SEND };
static const SfxNote sfxn_throw_s[] = { SQS(14, SN_G4, 0x62, 1, 10), SEND };
static const SfxNote sfxn_wobble_n[] = { NZ(3, 0x12, 0x91), SEND };
static const SfxNote sfxn_wobble_s[] = { SQ(3, SN_G5, 0x71, 1), SQ(3, SN_D5, 0x51, 1), SEND };
static const SfxNote sfxn_befr_a[] = {
    SQ(6, SN_C5, 0xB1, 2), SQ(6, SN_E5, 0xB1, 2), SQ(6, SN_G5, 0xB1, 2), SQ(10, SN_C6, 0xB2, 2),
    REST(2), SQ(6, SN_G5, 0xA1, 2), SQ(6, SN_A5, 0xA1, 2), SQ(6, SN_B5, 0xA1, 2), SQ(28, SN_C6, 0xB5, 2), SEND };
static const SfxNote sfxn_befr_b[] = {
    SQ(6, SN_E4, 0x81, 1), SQ(6, SN_G4, 0x81, 1), SQ(6, SN_C5, 0x81, 1), SQ(10, SN_E5, 0x82, 1),
    REST(2), SQ(6, SN_E5, 0x71, 1), SQ(6, SN_F5, 0x71, 1), SQ(6, SN_G5, 0x71, 1), SQ(28, SN_E5, 0x85, 1), SEND };
static const SfxNote sfxn_befr_w[] = {
    WV(28, SN_C3, 1, SWAVE_TRI, 0), REST(2), WV(18, SN_G3, 1, SWAVE_TRI, 0), WV(28, SN_C3, 2, SWAVE_TRI, 0), SEND };
static const SfxNote sfxn_run[] = {
    NZ(2, 0x33, 0x81), REST(3), NZ(2, 0x33, 0x71), REST(3), NZ(2, 0x33, 0x61), REST(3), NZ(2, 0x33, 0x51), SEND };
static const SfxNote sfxn_sendout_n[] = { NZ(2, 0x11, 0xB1), NZ(7, 0x31, 0x92), SEND };
static const SfxNote sfxn_sendout_s[] = {
    SQ(3, SN_C6, 0x91, 2), SQ(3, SN_E6, 0x91, 2), SQ(3, SN_G6, 0x91, 2), SQ(9, SN_C7, 0x82, 2), SEND };
static const SfxNote sfxn_trait[] = { SQ(3, SN_G6, 0x91, 2), SQ(3, SN_D6, 0x81, 2), SQ(9, SN_G6, 0x83, 2), SEND };
static const SfxNote sfxn_wipe_w[] = { WV(34, SN_C4, 2, SWAVE_SINE, 3), SEND };
static const SfxNote sfxn_wipe_s[] = {
    REST(6), SQ(4, SN_G5, 0x51, 1), SQ(4, SN_C6, 0x61, 1), SQ(4, SN_E6, 0x71, 1), SQ(4, SN_G6, 0x81, 1),
    SQ(12, SN_C7, 0x83, 1), SEND };
static const SfxNote sfxn_break_n[] = { NZ(2, 0x10, 0xC1), NZ(10, 0x42, 0xA2), SEND };
static const SfxNote sfxn_break_s[] = { SQS(10, SN_G5, 0xA2, 2, -24), SEND };

static const SfxNote sfxn_hollow_w[] = { WV(10, SN_E4, 2, SWAVE_SINE, -4), WV(16, SN_B3, 1, SWAVE_SINE, -3), SEND };
static const SfxNote sfxn_hollow_n[] = { REST(4), NZ(18, 0x76, 0x52), SEND };
static const SfxNote sfxn_relic_s[] = { SQ(3, SN_A5, 0x91, 2), SQ(3, SN_E5, 0x81, 2), SQ(12, SN_A4, 0x83, 2), SEND };
static const SfxNote sfxn_relic_n[] = { NZ(10, 0x55, 0x62), SEND };
static const SfxNote sfxn_metal_s[] = { SQ(2, SN_E7, 0xE1, 0), SQ(16, SN_B6, 0xB4, 0), SEND };
static const SfxNote sfxn_metal_n[] = { NZ(2, 0x01, 0xD1), NZ(8, 0x22, 0x82), SEND };
static const SfxNote sfxn_astral[] = {
    SQ(3, SN_E6, 0x91, 2), SQ(3, SN_B6, 0x91, 2), SQ(3, SN_G6, 0x81, 2), SQ(3, SN_D7, 0x81, 2),
    SQ(12, SN_B6, 0x73, 2), SEND };
static const SfxNote sfxn_knell_w[] = { WV(40, SN_C3, 1, SWAVE_TRI, 0), SEND };
static const SfxNote sfxn_knell_s[] = { SQ(3, SN_C5, 0xB1, 2), SQ(34, SN_G4, 0x96, 2), SEND };
static const SfxNote sfxn_banner_a[] = {
    SQ(4, SN_G4, 0xC1, 2), SQ(4, SN_C5, 0xC1, 2), SQ(20, SN_G5, 0xC4, 2), SEND };
static const SfxNote sfxn_banner_n[] = { NZ(2, 0x01, 0xF1), NZ(12, 0x33, 0xB2), SEND };
static const SfxNote sfxn_vict_a[] = {
    SQ(6, SN_G5, 0xC1, 2), SQ(6, SN_G5, 0xC1, 2), SQ(6, SN_G5, 0xC1, 2), SQ(14, SN_E5, 0xC2, 2),
    SQ(6, SN_F5, 0xC1, 2), SQ(6, SN_A5, 0xC1, 2), SQ(32, SN_C6, 0xC6, 2), SEND };
static const SfxNote sfxn_vict_b[] = {
    SQ(6, SN_E5, 0x81, 1), SQ(6, SN_E5, 0x81, 1), SQ(6, SN_E5, 0x81, 1), SQ(14, SN_C5, 0x82, 1),
    SQ(6, SN_D5, 0x81, 1), SQ(6, SN_F5, 0x81, 1), SQ(32, SN_G5, 0x86, 1), SEND };
static const SfxNote sfxn_vict_w[] = {
    WV(18, SN_C3, 1, SWAVE_TRI, 0), WV(14, SN_C3, 1, SWAVE_TRI, 0), WV(12, SN_F3, 1, SWAVE_TRI, 0),
    WV(32, SN_C3, 2, SWAVE_TRI, 0), SEND };

#define T1(c, p, n)                { { { c, p, n }, { 0, 0, 0 }, { 0, 0, 0 } } }
#define T2(c1, p1, n1, c2, p2, n2) { { { c1, p1, n1 }, { c2, p2, n2 }, { 0, 0, 0 } } }
#define T3(c1, p1, n1, c2, p2, n2, c3, p3, n3) { { { c1, p1, n1 }, { c2, p2, n2 }, { c3, p3, n3 } } }

/* Channels are 1..4; priorities 0 (text) .. 5 (fanfares). */
static const SfxDef SFX_DEFS[SFX_COUNT] = {
    [SFX_NONE]       = T1(0, 0, 0),
    [SFX_CURSOR]     = T1(2, 1, sfxn_cursor),
    [SFX_CONFIRM]    = T1(2, 2, sfxn_confirm),
    [SFX_CANCEL]     = T1(2, 2, sfxn_cancel),
    [SFX_ERROR]      = T1(1, 2, sfxn_error),
    [SFX_BUMP]       = T2(4, 1, sfxn_bump_n, 1, 1, sfxn_bump_s),
    [SFX_DOOR]       = T2(4, 2, sfxn_door_n, 2, 2, sfxn_door_s),
    [SFX_TEXT]       = T1(2, 0, sfxn_text),
    [SFX_SAVE]       = T2(1, 4, sfxn_save_a, 2, 4, sfxn_save_b),
    [SFX_ITEM]       = T2(1, 5, sfxn_item_a, 2, 5, sfxn_item_b),
    [SFX_HEAL]       = T2(1, 5, sfxn_heal_a, 3, 5, sfxn_heal_w),
    [SFX_LEVEL_UP]   = T2(1, 5, sfxn_lvl_a, 2, 5, sfxn_lvl_b),
    [SFX_EXCLAIM]    = T2(1, 4, sfxn_excl_a, 2, 4, sfxn_excl_b),
    [SFX_LEDGE]      = T2(1, 2, sfxn_ledge_s, 4, 2, sfxn_ledge_n),
    [SFX_GROW]       = T2(1, 4, sfxn_grow_a, 2, 4, sfxn_grow_b),
    [SFX_LORE]       = T2(1, 4, sfxn_lore_a, 2, 4, sfxn_lore_b),
    [SFX_BUY]        = T1(2, 3, sfxn_buy),
    [SFX_RUSTLE]     = T1(4, 1, sfxn_rustle),
    [SFX_HIT_LIGHT]  = T2(4, 3, sfxn_hitl_n, 1, 3, sfxn_hitl_s),
    [SFX_HIT]        = T2(4, 3, sfxn_hit_n, 1, 3, sfxn_hit_s),
    [SFX_HIT_STRONG] = T2(4, 3, sfxn_hits_n, 1, 3, sfxn_hits_s),
    [SFX_WEAK_SPOT]  = T3(4, 3, sfxn_hits_n, 1, 3, sfxn_hits_s, 2, 3, sfxn_weak_p),
    [SFX_PERFECT]    = T3(4, 3, sfxn_perf_n, 1, 3, sfxn_hits_s, 2, 3, sfxn_perf_p),
    [SFX_SHRUGGED]   = T2(4, 3, sfxn_shrug_n, 1, 3, sfxn_shrug_s),
    [SFX_MISS]       = T1(4, 3, sfxn_miss),
    [SFX_SWING]      = T1(4, 2, sfxn_swing),
    [SFX_FIRE]       = T2(4, 2, sfxn_fire_n, 1, 2, sfxn_fire_s),
    [SFX_SPLASH]     = T2(4, 2, sfxn_splash_n, 2, 2, sfxn_splash_s),
    [SFX_LEAF]       = T2(4, 2, sfxn_leaf_n, 2, 2, sfxn_leaf_s),
    [SFX_ZAP]        = T2(1, 2, sfxn_zap_s, 4, 2, sfxn_zap_n),
    [SFX_ICE]        = T2(2, 2, sfxn_ice_s, 4, 2, sfxn_ice_n),
    [SFX_ROCK]       = T2(4, 2, sfxn_rock_n, 1, 2, sfxn_rock_s),
    [SFX_WIND]       = T1(4, 2, sfxn_wind),
    [SFX_DREAM]      = T1(3, 2, sfxn_dream),
    [SFX_BUZZ]       = T1(2, 2, sfxn_buzz),
    [SFX_DUSK]       = T2(1, 2, sfxn_dusk_s, 4, 2, sfxn_dusk_n),
    [SFX_VENOM]      = T1(2, 2, sfxn_venom),
    [SFX_WYRM]       = T2(4, 2, sfxn_wyrm_n, 1, 2, sfxn_wyrm_s),
    [SFX_CHARGE]     = T1(2, 2, sfxn_charge),
    [SFX_THUNDER]    = T2(4, 3, sfxn_thunder_n, 1, 3, sfxn_thunder_s),
    [SFX_ROAR]       = T3(4, 3, sfxn_roar_n, 1, 3, sfxn_roar_a, 2, 3, sfxn_roar_b),
    [SFX_DRAIN]      = T1(2, 2, sfxn_drain),
    [SFX_SPARKLE]    = T2(2, 2, sfxn_sparkle_a, 3, 2, sfxn_sparkle_w),
    [SFX_STAT_UP]    = T1(2, 2, sfxn_statup),
    [SFX_STAT_DOWN]  = T1(2, 2, sfxn_statdown),
    [SFX_STATUS]     = T1(2, 2, sfxn_status),
    [SFX_DOZE]       = T2(1, 3, sfxn_doze_s, 4, 3, sfxn_doze_n),
    [SFX_THROW]      = T2(4, 2, sfxn_throw_n, 2, 2, sfxn_throw_s),
    [SFX_WOBBLE]     = T2(4, 2, sfxn_wobble_n, 2, 2, sfxn_wobble_s),
    [SFX_BEFRIEND]   = T3(1, 5, sfxn_befr_a, 2, 5, sfxn_befr_b, 3, 5, sfxn_befr_w),
    [SFX_HOLLOW]     = T2(3, 2, sfxn_hollow_w, 4, 2, sfxn_hollow_n),
    [SFX_RELIC]      = T2(1, 2, sfxn_relic_s, 4, 2, sfxn_relic_n),
    [SFX_METAL]      = T2(1, 2, sfxn_metal_s, 4, 2, sfxn_metal_n),
    [SFX_ASTRAL]     = T1(2, 2, sfxn_astral),
    [SFX_KNELL]      = T2(3, 3, sfxn_knell_w, 1, 3, sfxn_knell_s),
    [SFX_BANNER]     = T2(1, 4, sfxn_banner_a, 4, 4, sfxn_banner_n),
    [SFX_VICTORY]    = T3(1, 5, sfxn_vict_a, 2, 5, sfxn_vict_b, 3, 5, sfxn_vict_w),
    [SFX_RUN]        = T1(4, 2, sfxn_run),
    [SFX_SEND_OUT]   = T2(4, 2, sfxn_sendout_n, 2, 2, sfxn_sendout_s),
    [SFX_TRAIT]      = T1(2, 3, sfxn_trait),
    [SFX_WIPE]       = T2(3, 3, sfxn_wipe_w, 2, 3, sfxn_wipe_s),
    [SFX_BREAK_FREE] = T2(4, 3, sfxn_break_n, 1, 3, sfxn_break_s),
};

#undef SQ
#undef SQS
#undef SW
#undef NZ
#undef WV
#undef REST
#undef SEND
#undef T1
#undef T2
#undef T3

/* ---------------- sequencer ---------------- */

static struct {
    const SfxNote *n;  /* current note, 0 = idle */
    u8 left;           /* frames left of this note */
    u8 prio;
    s16 freq;          /* current frequency register value (slides) */
} sfx_ch[4];

static u8 snd_on;      /* master enable and mixer routing written */
static u8 sfx_on;      /* PSG channels routed to the speakers */
static s8 sfx_wave_loaded = -1;
static volatile u8 sfx_fanfare;   /* a priority-5 jingle is playing (music ducks) */

/* PSG at 100%, Direct Sound A (music) at 50% on both sides, timer 0: a
 * full-scale music mix fills half the DAC and leaves the rest to the PSG. */
#define SNDCNT_H_MIX 0x0302

static void snd_power_on(void)
{
    if (snd_on) return;
    SREG_SNDCNT_X = 0x0080;      /* master enable (other registers need it first) */
    SREG_SNDCNT_L = 0x0077;      /* PSG volume 7 both sides; channels off until needed */
    SREG_SNDCNT_H = SNDCNT_H_MIX;
    snd_on = 1;
}

static void sfx_load_wave(int w)
{
    static const u8 SHAPES[SWAVE_COUNT][32] = {
        { 8, 9, 10, 12, 13, 14, 14, 15, 15, 15, 14, 14, 13, 12, 10, 9,
          8, 6, 5, 3, 2, 1, 1, 0, 0, 0, 1, 1, 2, 3, 5, 6 },
        { 0, 1, 2, 3, 4, 5, 6, 7, 8, 8, 9, 10, 11, 12, 13, 14,
          15, 14, 13, 12, 11, 10, 9, 8, 8, 7, 6, 5, 4, 3, 2, 1 },
    };
    if (sfx_wave_loaded == w) return;
    SREG_SND3_SEL = 0;                   /* stop; CPU writes the other bank */
    for (int i = 0; i < 4; i++) {
        u32 word = 0;
        for (int b = 0; b < 4; b++) {
            int k = (i * 4 + b) * 2;
            u32 byte = (u32)((SHAPES[w][k] << 4) | SHAPES[w][k + 1]);
            word |= byte << (b * 8);
        }
        SREG_WAVE(i) = word;
    }
    sfx_wave_loaded = (s8)w;
}

static int sfx_note_freq(int ch, int note)
{
    int i = clampi(note, 36, 107) - 36;
    int f = SFX_NOTE_FREQ[i];
    if (ch == 2) f = 2048 - (2048 - f) / 2;   /* 32-sample wave: one octave lower */
    return f;
}

static void sfx_silence(int ch)
{
    switch (ch) {
    case 0: SREG_SND1_ENV = 0; SREG_SND1_SWEEP = 0x08; SREG_SND1_FREQ = 0x8000; break;
    case 1: SREG_SND2_ENV = 0; SREG_SND2_FREQ = 0x8000; break;
    case 2: SREG_SND3_SEL = 0; break;
    case 3: SREG_SND4_ENV = 0; SREG_SND4_FREQ = 0x8000; break;
    }
}

static void sfx_start_note(int c)
{
    const SfxNote *n = sfx_ch[c].n;
    sfx_ch[c].left = n->len;
    if (!n->note) {
        sfx_silence(c);
        return;
    }
    switch (c) {
    case 0:
        sfx_ch[c].freq = (s16)sfx_note_freq(0, n->note);
        SREG_SND1_SWEEP = (u16)(n->sweep ? n->sweep : 0x08);
        SREG_SND1_ENV = (u16)((n->arg & 3) << 6 | n->env << 8);
        SREG_SND1_FREQ = (u16)(sfx_ch[c].freq | 0x8000);
        break;
    case 1:
        sfx_ch[c].freq = (s16)sfx_note_freq(1, n->note);
        SREG_SND2_ENV = (u16)((n->arg & 3) << 6 | n->env << 8);
        SREG_SND2_FREQ = (u16)(sfx_ch[c].freq | 0x8000);
        break;
    case 2:
        sfx_load_wave(n->arg % SWAVE_COUNT);
        sfx_ch[c].freq = (s16)sfx_note_freq(2, n->note);
        SREG_SND3_SEL = 0x0040 | 0x0080;     /* play the bank just written */
        SREG_SND3_VOL = (u16)((n->env & 3) << 13);
        SREG_SND3_FREQ = (u16)(sfx_ch[c].freq | 0x8000);
        break;
    case 3:
        SREG_SND4_ENV = (u16)(n->env << 8);
        SREG_SND4_FREQ = (u16)(n->note | 0x8000);
        break;
    }
}

static void sfx_slide(int c)
{
    const SfxNote *n = sfx_ch[c].n;
    if (!n->slide || !n->note || c == 3) return;
    int f = clampi(sfx_ch[c].freq + n->slide, 0, 2040);
    sfx_ch[c].freq = (s16)f;
    if (c == 0) SREG_SND1_FREQ = (u16)f;
    else if (c == 1) SREG_SND2_FREQ = (u16)f;
    else SREG_SND3_FREQ = (u16)f;
}

/* Silence every effect and take the PSG off the speakers (music keeps playing). */
static void sfx_stop_all(void)
{
    for (int c = 0; c < 4; c++) {
        sfx_ch[c].n = 0;
        sfx_ch[c].prio = 0;
        if (snd_on) sfx_silence(c);
    }
    if (snd_on) SREG_SNDCNT_L = 0x0077;
    sfx_on = 0;
    sfx_fanfare = 0;
    sfx_wave_loaded = -1;
}

static void sfx_power_on(void)
{
    if (sfx_on) return;
    snd_power_on();
    SREG_SNDCNT_L = 0xFF77;      /* all PSG channels, full volume, both sides */
    sfx_on = 1;
    sfx_wave_loaded = -1;
    for (int c = 0; c < 4; c++) sfx_silence(c);
}

/* Start an effect (SFX_*). Ignored while sound is off. */
static void sfx_play(int id)
{
    if (!opt.sound || id <= SFX_NONE || id >= SFX_COUNT) return;
    sfx_power_on();
    const SfxDef *d = &SFX_DEFS[id];
    for (int k = 0; k < 3; k++) {
        const SfxTrack *t = &d->t[k];
        if (!t->ch || !t->notes) continue;
        int c = t->ch - 1;
        if (sfx_ch[c].n && sfx_ch[c].prio > t->prio) continue;
        sfx_ch[c].n = t->notes;
        sfx_ch[c].prio = t->prio;
        sfx_start_note(c);
    }
}

/* Is anything still sounding? (tests and fades) */
static int sfx_busy(void) __attribute__((unused));
static int sfx_busy(void)
{
    for (int c = 0; c < 4; c++)
        if (sfx_ch[c].n) return 1;
    return 0;
}

/* Once per frame. */
static void sfx_update(void)
{
    if (!opt.sound) {
        if (sfx_on) sfx_stop_all();
        return;
    }
    int fanfare = 0;
    for (int c = 0; c < 4; c++)
        if (sfx_ch[c].n && sfx_ch[c].prio >= 5) fanfare = 1;
    sfx_fanfare = (u8)fanfare;
    for (int c = 0; c < 4; c++) {
        if (!sfx_ch[c].n) continue;
        if (sfx_ch[c].left > 1) {
            sfx_ch[c].left--;
            sfx_slide(c);
            continue;
        }
        sfx_ch[c].n++;
        if (!sfx_ch[c].n->len) {
            sfx_ch[c].n = 0;
            sfx_ch[c].prio = 0;
            sfx_silence(c);
            continue;
        }
        sfx_start_note(c);
    }
}
