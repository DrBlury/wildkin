#include "harness.h"

static SaveLayout old_layout, expanded;
static SaveData sample;
static u8 sram[32768];

static void test_layout_growth(void)
{
    save_layout_current(&old_layout);
    expanded = old_layout;
    /* Insert a flag, satchel and warden in east, then one map in west. */
    expanded.region[2].count[SAVE_FLAG]++;
    expanded.region[2].count[SAVE_SATCHEL]++;
    expanded.region[2].count[SAVE_WARDEN]++;
    expanded.region[3].count[SAVE_MAP]++;
    for (int k = 0; k < SAVE_KINDS; k++) {
        u16 base = 0;
        for (int r = 0; r < expanded.regions; r++) {
            expanded.region[r].base[k] = base;
            base += expanded.region[r].count[k];
        }
    }
    int west = old_layout.region[3].base[SAVE_MAP];
    int inserted = old_layout.region[3].base[SAVE_MAP] + old_layout.region[3].count[SAVE_MAP];
    for (int m = old_layout.maps; m > inserted; m--) {
        expanded.map_bits[m][0] = old_layout.map_bits[m - 1][0];
        expanded.map_bits[m][1] = old_layout.map_bits[m - 1][1];
    }
    expanded.map_bits[inserted][0] = expanded.map_bits[inserted][1] = 0;
    expanded.maps++;
    CHECK(save_layout_valid(&expanded), "synthetic expanded manifest is valid");
    for (int k = SAVE_FLAG; k <= SAVE_WARDEN; k++) {
        int old_id = old_layout.region[4].base[k] + 1;
        int new_id = expanded.region[4].base[k] + 1;
        CHECK(save_id_map(&old_layout, &expanded, k, old_id) == new_id,
              "later region ID survives earlier region growth");
    }
    int north_map = old_layout.region[4].base[SAVE_MAP];
    CHECK(save_id_map(&old_layout, &expanded, SAVE_MAP, north_map) == north_map + 1 &&
          save_id_map(&old_layout, &expanded, SAVE_MAP, west) == west,
          "west map insertion remaps north but preserves west prefix");
    u8 saved[64] = { 0 }, restored[64] = { 0 };
    int old_flag = old_layout.region[4].base[SAVE_FLAG] + 1;
    bit_set(saved, old_flag);
    save_bits_map(restored, 64, saved, 64, &old_layout, &expanded, SAVE_FLAG);
    CHECK(bit_get(restored, old_flag + 1) && !bit_get(restored, old_flag),
          "set flag bits migrate to the later region's new offset");
}

static void test_v5_load(void)
{
    fresh_game();
    give_starter();
    flag_set(FLAG_LEAF_STONE);
    field_enter_map(MAP_LAKE, 30, 17, DIR_LEFT);
    save_capture(&sample);
    sample.version = 5;
    sample.size = SAVE_V5_SIZE;
    sample.checksum = fnv_bytes(&sample, SAVE_V5_SIZE - sizeof(sample.checksum));
    memset(sram, 0xFF, sizeof(sram));
    memcpy(sram, &sample, SAVE_V5_SIZE);
    fresh_game();
    CHECK(save_load_from(sram) == 5 && cur_map == MAP_LAKE && player.x == 30 &&
          flag(FLAG_LEAF_STONE) && party_count == 1,
          "checksum-verified v5 prefix loads and migrates into v7");
}

static void test_v6_load(void)
{
    fresh_game();
    give_starter();
    flag_set(FLAG_LEAF_STONE);
    field_enter_map(MAP_LAKE, 30, 17, DIR_LEFT);
    save_capture(&sample);
    sample.version = 6;
    sample.size = (u8 *)&sample.events - (u8 *)&sample;
    sample.mod_size[6] = 0;
    sample.checksum_v6 = fnv_bytes(&sample, (u8 *)&sample.checksum_v6 - (u8 *)&sample);
    memset(sram, 0xFF, sizeof(sram));
    memcpy(sram, &sample, sample.size);
    fresh_game();
    CHECK(save_load_from(sram) == 6 && cur_map == MAP_LAKE && player.x == 30 &&
          flag(FLAG_LEAF_STONE) && party_count == 1 && events.rolled_day == gtime.day,
          "authenticated v6 save migrates while initializing today's events");
}

static void test_visits(void)
{
    fresh_game();
    travel_visited_set(127);
    travel_visited_set(128);
    travel_visited_set(MAP_COUNT - 1);
    CHECK(travel_visited_get(127) && travel_visited_get(128) &&
          travel_visited_get(MAP_COUNT - 1), "both halves of visited retain map IDs");
    CHECK(!travel_visited_get(-1) && !travel_visited_get(MAP_COUNT) &&
          !travel_visited_get(256), "out-of-range map reads are rejected");
    TravelState before = travel;
    travel_visited_set(-1);
    travel_visited_set(MAP_COUNT);
    travel_visited_set(256);
    CHECK(memcmp(&before, &travel, sizeof(travel)) == 0, "out-of-range map writes are ignored");
}

int main(void)
{
    test_layout_growth();
    test_v5_load();
    test_v6_load();
    test_visits();
    return failures ? 1 : 0;
}
