/* Exact A-button FIELD NOTES discovery, ability markers and save persistence. */
#include "harness.h"

static void face_note(int id, int px, int py, int dir)
{
    const SagaNote *note = &saga_notes[id];
    game_mode = MODE_FIELD;
    dialog_clear();
    field_enter_map(note->map, px, py, dir);
    warp.active = 0;
    player.facing = (u8)dir;
    step(0);
    dialog_clear();
}

static void test_examination(void)
{
    fresh_game();
    give_starter();
    face_note(NOTE_WOOD_LOG, 34, 25, DIR_LEFT);
    saga_bind();
    CHECK(!saga_note_bit(NOTE_WOOD_LOG, 0), "walking into Brookmill Trail never discovers the cache");
    scr_saga_notes(0);
    CHECK(!saga_note_bit(NOTE_WOOD_LOG, 0), "reading the FIELD NOTES NPC never discovers a tile");
    dialog_clear();
    quest_log_open();
    tap(KEY_SELECT);
    CHECK(qlog_note_count(SAGA_LIGHT) == 0, "opening FIELD NOTES does not discover a tile");
    tap(KEY_B); tap(KEY_B);
    CHECK(!saga_note_bit(NOTE_WOOD_LOG, 0), "returning to the field leaves the note hidden");
    player.facing = DIR_LEFT;
    tap(KEY_A);
    CHECK(saga_note_bit(NOTE_WOOD_LOG, 0) && !saga_note_bit(NOTE_WOOD_LOG, 3),
          "A on the rookery hollow records the stable LIGHT note unsolved");
    CHECK(!strcmp(qlog_note_status(NOTE_WOOD_LOG), "LOCKED"), "unowned LIGHT note is LOCKED");
    QuestState once = quest;
    dialog_clear(); tap(KEY_A);
    CHECK(!memcmp(&once, &quest, sizeof(quest)), "examining a note again records no extra state");
    flag_set(FLAG_VOLT_CREST);
    CHECK(!strcmp(qlog_note_status(NOTE_WOOD_LOG), "READY"), "owned LIGHT changes the note to READY");
    flag_set(FLAG_BROOK_LIGHT_CACHE);
    saga_notes_sync();
    CHECK(saga_note_bit(NOTE_WOOD_LOG, 3) && !strcmp(qlog_note_status(NOTE_WOOD_LOG), "DONE"),
          "actual cache completion flag marks the same note DONE");
    CHECK(save_write(), "examined and solved note saves");
    new_game();
    CHECK(save_load() == SAVE_VERSION && saga_note_bit(NOTE_WOOD_LOG, 3),
          "observed and solved bits survive reload");
}

static void test_normal_interactions(void)
{
    fresh_game(); give_starter();
    face_note(NOTE_LAKE_ISLET, 2, 14, DIR_RIGHT);
    CHECK(!saga_note_bit(NOTE_LAKE_ISLET, 0), "approaching water does not discover a SURF note");
    tap(KEY_A);
    CHECK(saga_note_bit(NOTE_LAKE_ISLET, 0) && dialog_active(),
          "A on deep water records SURF note and retains ordinary water dialog");
    CHECK(!strcmp(qlog_note_status(NOTE_LAKE_ISLET), "LOCKED"), "SURF still requires TIDE");
    flag_set(FLAG_TIDE_CREST);
    CHECK(!strcmp(qlog_note_status(NOTE_LAKE_ISLET), "READY"), "TIDE makes the SURF note READY");
    CHECK(!saga_note_bit(NOTE_WOOD_FOG, 0), "another map's WARD note stays hidden");

    fresh_game(); give_starter();
    face_note(NOTE_RAIL_SHAFT, 32, 10, DIR_UP);
    tap(KEY_A);
    CHECK(saga_note_bit(NOTE_RAIL_SHAFT, 0) && dialog_active() &&
          !strcmp(qlog_note_status(NOTE_RAIL_SHAFT), "LOCKED"),
          "A on the shaft boulder keeps its ordinary STRENGTH interaction");

    fresh_game(); give_starter();
    face_note(NOTE_WILLOW_CREEK, 10, 11, DIR_DOWN);
    tap(KEY_A);
    CHECK(saga_note_bit(NOTE_WILLOW_CREEK, 0) && dialog_active(),
          "A on a solid authored sign records its note and keeps sign dialog");
    CHECK(!saga_note_bit(NOTE_WOOD_LOG, 0), "examining a creek sign does not record another note");
}

static void test_note_data(void)
{
    for (int id = 0; id < NOTE_COUNT; id++) {
        const SagaNote *n = &saga_notes[id];
        map_load(n->map);
        int approaches = 0;
        for (int d = 0; d < 4; d++) {
            int x = n->x + DIR_DX[d], y = n->y + DIR_DY[d];
            if (x < 0 || y < 0 || x >= map_w || y >= map_h) continue;
            if (!(cell_attr(x, y) & (A_SOLID | A_LEDGE | A_WATER))) approaches++;
        }
        if (!approaches) { printf("  unreachable note anchor: %s\n", n->name); failures++; }
        if (approaches) {
            fresh_game();
            map_load(n->map);
            for (int d = 0; d < 4; d++) {
                int x = n->x + DIR_DX[d], y = n->y + DIR_DY[d];
                if (x < 0 || y < 0 || x >= map_w || y >= map_h ||
                    (cell_attr(x, y) & (A_SOLID | A_LEDGE | A_WATER))) continue;
                face_note(id, x, y, d ^ 1);
                break;
            }
            if (saga_note_bit(id, 0)) { printf("  auto-discovered note: %s\n", n->name); failures++; }
            tap(KEY_A);
            if (!saga_note_bit(id, 0)) { printf("  A examination missed note: %s\n", n->name); failures++; }
        }
        if (n->ability != SAGA_SURF && (cell_attr(n->x, n->y) & A_WATER)) {
            printf("  note uses SURF water but requires another ability: %s\n", n->name); failures++;
        }
    }
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    test_note_data();
    test_examination();
    test_normal_interactions();
    printf("field notes: %d failure(s)\n", failures);
    return failures != 0;
}
