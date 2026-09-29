#include "harness.h"

static SaveLayout old_layout, expanded;
static SaveData sample;
static u8 sram[32768];

static void checked_load_at(int x, int y, int level, int expected_map, const char *message)
{
    fresh_game();
    give_starter();
    flag_set(FLAG_LEAF_STONE);
    field_enter_map(MAP_LAKE, 30, 17, DIR_LEFT);
    save_capture(&sample);
    if (x == 0 && y == 0)
        CHECK(cell_attr(x, y) & A_SOLID, "blocked-save fixture is actually a wall");
    sample.player_x = (u8)x;
    sample.player_y = (u8)y;
    sample.level = (u8)level;
    sample.checksum_v7 = save_checksum(&sample);
    memset(sram, 0xFF, sizeof(sram));
    memcpy(sram, &sample, sizeof(sample));
    fresh_game();
    int loaded = save_load_from(sram);
    CHECK(loaded == SAVE_VERSION && cur_map == expected_map &&
          player.x >= 0 && player.y >= 0 && player.x < map_w && player.y < map_h &&
          !(cell_attr(player.x, player.y) & (A_SOLID | A_LEDGE | A_WATER)) &&
          flag(FLAG_LEAF_STONE) && party_count == 1, message);
}

static void test_position_recovery(void)
{
    checked_load_at(0, 0, 0, MAP_REST, "authenticated position inside a wall recovers at last Hearth without losing progress");
    checked_load_at(255, 255, 0, MAP_REST, "authenticated old out-of-bounds coordinate recovers at Hearth");
    /* Exercise application independently of a concurrently regenerated ID manifest. */
    save_apply(&sample);
    CHECK(cur_map == MAP_REST && save_position_safe(player.x, player.y, player.level) &&
          flag(FLAG_LEAF_STONE), "post-load safety also handles old bounds directly");
    sample.checksum_v7 ^= 1;
    memcpy(sram, &sample, sizeof(sample));
    fresh_game();
    CHECK(save_load_from(sram) == 0, "tampered coordinate checksum remains rejected");
}

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

static void test_unique_entrance_recovery(void)
{
    fresh_game();
    give_starter();
    field_enter_map(MAP_HOME, 5, 8, DIR_UP);
    save_capture(&sample);
    sample.player_x = sample.player_y = 0;
    sample.checksum_v7 = save_checksum(&sample);
    memset(sram, 0xFF, sizeof(sram));
    memcpy(sram, &sample, sizeof(sample));
    fresh_game();
    CHECK(save_load_from(sram) == SAVE_VERSION && cur_map == MAP_HOME &&
          save_position_safe(player.x, player.y, player.level) && party_count == 1,
          "unique safe authored entrance recovers in the same map");
}

static void test_valid_terrain_positions(void)
{
    fresh_game();
    give_starter();
    field_enter_map(MAP_EV_TEST, 13, 9, DIR_RIGHT);
    player.level = 1;
    save_capture(&sample);
    save_apply(&sample);
    CHECK(cur_map == MAP_EV_TEST && player.x == 13 && player.y == 9 && player.level == 1,
          "valid bridge deck survives post-load safety");
    fresh_game();
    give_starter();
    field_enter_map(MAP_LAKE, 30, 17, DIR_LEFT);
    int found = 0;
    for (int y = 0; y < map_h && !found; y++) for (int x = 0; x < map_w && !found; x++)
        if ((cell_attr(x, y) & A_WATER) && !(cell_attr(x, y) & A_DEEP) && travel_surf_cell(x, y)) {
            player.x = x; player.y = y;
            player.level = elev_level_at(x, y, -1, -1);
            travel.surfing = 1;
            found = 1;
        }
    CHECK(found, "surf fixture exists on the Lake");
    if (found) {
        int x = player.x, y = player.y;
        save_capture(&sample);
        save_apply(&sample);
        CHECK(cur_map == MAP_LAKE && player.x == x && player.y == y && travel.surfing,
              "valid surfing position survives post-load safety");
    }
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
    test_position_recovery();
    test_unique_entrance_recovery();
    test_valid_terrain_positions();
    test_visits();
    return failures ? 1 : 0;
}
