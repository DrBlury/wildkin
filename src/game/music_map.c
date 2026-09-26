/*
 * Which song plays where: the field song for each map, the bout themes and
 * the title screen. The engine is music.c; this file only picks songs.
 *
 * A map plays MapDef.song when it sets one; otherwise its song follows from
 * the map itself:
 *   HEARTH HALL (MF_HEAL)                          SONG_HEARTH
 *   indoors in a cave or crypt tileset, dark
 *   (MF_DARK) or a legend's lair (SC_LAIR)         SONG_CAVE
 *   outdoors in a town (MF_TOWN)                   SONG_VILLAGE
 *   other outdoor maps (routes, woods, coast)      SONG_ROUTE
 *   houses, shops and every other interior         SONG_VILLAGE
 *
 * Bouts (battle.c's battle_music_hook): wild and warden bouts play
 * SONG_BATTLE, Hall Masters and legends SONG_MASTER; a win or a catch plays
 * SONG_VICTORY (a Hall Master's PSG fanfare ducks it at first), a loss or an
 * escape fades out, and when the bout closes the field song comes back.
 */

static u8 mus_field_song = SONG_NONE;  /* the song of the map the player is on */

static int music_song_for_map(int map)
{
    if (map < 0 || map >= MAP_COUNT) return SONG_VILLAGE;
    const MapDef *m = &MAPS[map];
    if (m->song > SONG_NONE && m->song < SONG_COUNT) return m->song;
    if (m->flags & MF_HEAL) return SONG_HEARTH;
    if (!(m->flags & MF_OUTDOOR)) {
        if ((m->flags & MF_DARK) || m->scene == SC_LAIR || m->scene == SC_CAVE || m->scene == SC_CRYPT ||
            m->tileset == TS_CAVE || m->tileset == TS_CRYPT)
            return SONG_CAVE;
        return SONG_VILLAGE;
    }
    if (m->flags & MF_TOWN) return SONG_VILLAGE;
    return SONG_ROUTE;
}

/* field.c: the end of every map load. */
static void music_map_changed(int map)
{
    mus_field_song = (u8)music_song_for_map(map);
    music_play(mus_field_song);
}

/* battle.c: bout cues (BCUE_*). */
static void music_battle_cue(int cue)
{
    switch (cue) {
    case BCUE_START_WILD:
    case BCUE_START_WARDEN: music_play_now(SONG_BATTLE); break;
    case BCUE_START_MASTER:
    case BCUE_START_LEGEND: music_play_now(SONG_MASTER); break;
    case BCUE_WIN:
    case BCUE_MASTER_WIN:
    case BCUE_CAUGHT: music_play_now(SONG_VICTORY); break;
    case BCUE_LOSE:
    case BCUE_RUN: music_stop(); break;
    case BCUE_END: music_play(mus_field_song != SONG_NONE ? mus_field_song : SONG_VILLAGE); break;
    default: break;
    }
}

/* Once at boot, after music_init(). */
static void music_map_init(void)
{
    battle_music_hook = music_battle_cue;
}
