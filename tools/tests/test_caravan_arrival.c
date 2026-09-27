/* Visual-only caravan lifecycle and OAM checks; no sprite slots are added. */
#include "harness.h"

static int wagon_oam_x(void)
{
    oam_begin();
    farm_draw();
    for (int i = 0; i < oam_count; i++)
        if ((oam_shadow[i * 4 + 2] & 1023) == OT_CARAVAN)
            return ((oam_shadow[i * 4 + 1] & 511) + 256) % 512 - 256;
    return -1;
}

int main(int argc, char **argv)
{
    fresh_game();
    give_starter();
    npc_event_active = events_active;
    gtime.day = 1;
    events_new_day_impl();
    CHECK(sizeof(EventState) <= 64, "arrival does not expand serialized event state");
    CHECK(events.caravan_map == 7, "Act I caravan stops at Maple");
    map_load(MAP_TOWN);
    player.x = 8; player.y = 8;
    field_update_camera();
    events_map_entered_impl(MAP_TOWN);
    field_events_refresh();
    int npc = -1;
    for (int i = 0; i < NPC_COUNT; i++) if (events_caravan_person(i)) { npc = i; break; }
    CHECK(npc >= 0 && caravan_arrival.active, "arrival starts at matching stop");
    if (npc < 0) return 1;
    farm_tick();
    CHECK(!npc_visible[npc] && !npc_kin[npc].shown, "merchant and kin stay hidden during arrival");
    for (int f = 0; f < 16; f++) farm_tick();
    int first = wagon_oam_x();
    for (int f = 0; f < 20; f++) farm_tick();
    int middle = wagon_oam_x();
    CHECK(first > -32 && middle > first, "actual wagon sprite moves across screen");
    CHECK(first != middle && VRAM_OBJ_TILES[OT_CARAVAN * 8 + 10] != 0,
          "wagon art occupies the dedicated eight OBJ tiles");
    for (int f = 37; f < CARAVAN_ARRIVAL_FRAMES; f++) farm_tick();
    CHECK(!caravan_arrival.active && npc_visible[npc] &&
          events_caravan_wagon_x() == NPCS[npc].x * 16 - 32,
          "merchant reappears beside parked wagon at end");
    events_map_entered_impl(MAP_TOWN);
    CHECK(!caravan_arrival.active, "same-day reentry does not replay arrival");
    map_load(MAP_MEADOW);
    CHECK(events_caravan_wagon_x() < 0, "wagon is absent on other maps");
    map_load(MAP_TOWN);
    events_map_entered_impl(MAP_TOWN);
    CHECK(!caravan_arrival.active, "returning on the same day stays parked");

    events_caravan_reset();
    events_map_entered_impl(MAP_TOWN);
    CHECK(caravan_arrival.active, "new entry can start a pending arrival");
    map_load(MAP_MEADOW);
    farm_tick();
    CHECK(!caravan_arrival.active && events_caravan_wagon_x() < 0,
          "mid-arrival map exit cancels tween");
    gtime.day++;
    events_new_day_impl();
    CHECK(!caravan_arrival.active, "new day invalidates previous tween");
    gtime.day = 1;
    events.rolled_day = 0;
    events_new_day_impl();
    events_caravan_reset();
    map_load(MAP_TOWN);
    player.x = 8; player.y = 8;
    events_map_entered_impl(MAP_TOWN);
    farm_tick();
    CHECK(caravan_arrival.active, "fresh state can start arrival again");
    static u8 sram[32768];
    CHECK(save_write_to(sram), "in-flight stop saves normally");
    if (argc > 1) {
        FILE *out = fopen(argv[1], "wb");
        CHECK(out && fwrite(sram, 1, sizeof(sram), out) == sizeof(sram),
              "capture save written for real ROM playback");
        if (out) fclose(out);
    }
    new_game();
    CHECK(!caravan_arrival.active && !caravan_arrival.seen, "new game clears ephemeral tween");
    CHECK(save_load_from(sram) == SAVE_VERSION, "in-flight save loads with unchanged format");
    CHECK(!caravan_arrival.active && !caravan_arrival.seen && events_caravan_wagon_x() < 0,
          "reload discards stale tween without a parked first-frame pop");
    farm_tick();
    CHECK(caravan_arrival.active && events_caravan_wagon_x() != NPCS[npc].x * 16 - 32,
          "loaded stop gets a fresh independent arrival");
    if (failures) return 1;
    puts("caravan arrival checks passed");
    return 0;
}
