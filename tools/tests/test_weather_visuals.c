/* Field visual states: forced regional fronts and calendar-gated festivals. */
#include "harness.h"

static int tile_count(int tile)
{
    int n = 0;
    for (int i = 0; i < oam_count; i++)
        if ((oam_shadow[i * 4 + 2] & 1023) == tile) n++;
    return n;
}

static int weather_tiles(void)
{
    int n = 0;
    for (int i = 0; i < oam_count; i++) {
        int tile = oam_shadow[i * 4 + 2] & 1023;
        if (tile >= OT_WEATHER && tile < OT_WEATHER + WFX_COUNT) n++;
    }
    return n;
}

static void force_front(int map, int wx)
{
    map_load(map);
    events.rolled_day = gtime.day;
    events.front_region = events_region(map);
    events.front_kind = wx;
    cam_x = cam_y = 0;
    field_anim_frame = 64;
    oam_count = 0;
    weather_draw_particles();
}

int main(void)
{
    fresh_game();
    events_weather_here = events_weather_here_impl;
    gtime.day = 12;
    gtime.minute = 12 * 60;
    gtime.weather = WEATHER_CLEAR;
    force_front(MAP_HERON_FEN, WX_FOG);
    CHECK(tile_count(OT_WEATHER + WFX_FOG) > 0 && field_tint(RGB15(8, 8, 8)) != RGB15(8, 8, 8),
          "forced fog draws wisps and lightens field palette");
    int palette_shared = 1;
    for (int i = 1; i <= 6; i++)
        if (travel_fx_palette[i] != emote_palette[i] || travel_rune_palette[i] != emote_palette[i])
            palette_shared = 0;
    CHECK(palette_shared && VRAM_OBJ_TILES[(OT_WEATHER + WFX_FOG) * 8 + 2] != 0,
          "procedural tile pixels survive map load and reuse stable shared palette entries");
    CHECK(weather_tiles() <= 16 && OT_WEATHER + WFX_COUNT <= 640,
          "regional effects stay in bounded OAM and farm OBJ range");
    u32 fog_pixel = VRAM_OBJ_TILES[(OT_WEATHER + WFX_FOG) * 8 + 2];
    VRAM_OBJ_TILES[(OT_WEATHER + WFX_FOG) * 8 + 2] = 0; /* battle FX clobber */
    frame_count += 2;
    oam_count = 0;
    farm_draw();
    CHECK(VRAM_OBJ_TILES[(OT_WEATHER + WFX_FOG) * 8 + 2] == fog_pixel,
          "weather art reloads after a battle or menu overwrites field OBJ tiles");
    force_front(MAP_FROSTPINE, WX_SNOW);
    int blizzard = tile_count(OT_WEATHER + WFX_SNOW);
    CHECK(blizzard >= 8, "snow front thickens north snowfall");
    events.front_region = ER_HOME;
    oam_count = 0;
    weather_draw_particles();
    CHECK(time_weather_here(MAP_FROSTPINE) == WX_SNOW && tile_count(OT_WEATHER + WFX_SNOW) < blizzard &&
          tile_count(OT_WEATHER + WFX_SNOW) >= 6,
          "MF_SNOW falls without a regional front");
    force_front(MAP_RAILHEAD, WX_HEAT);
    int heat_key = time_tint_key();
    field_anim_frame += 10;
    CHECK(tile_count(OT_WEATHER + WFX_HEAT) > 0 && heat_key != time_tint_key(),
          "heat has moving distortion marks and animated warm palette");
    force_front(MAP_ASHEN_FIELDS, WX_ASH);
    CHECK(tile_count(OT_WEATHER + WFX_ASH) > 0, "ash front adds flakes to the existing haze");
    gtime.minute = 22 * 60;
    force_front(MAP_FROSTPINE, WX_AURORA);
    int aurora_key = time_tint_key();
    field_anim_frame += 12;
    CHECK(tile_count(OT_WEATHER + WFX_STREAM) > 0 && aurora_key != time_tint_key(),
          "night aurora draws streamers and cycles field colours");
    gtime.minute = 12 * 60;
    oam_count = 0;
    weather_draw_particles();
    CHECK(time_weather_here(MAP_FROSTPINE) == WX_SNOW && !tile_count(OT_WEATHER + WFX_STREAM),
          "aurora yields to snow during daylight");
    map_load(MAP_REST);
    oam_count = 0;
    weather_draw_particles();
    CHECK(!weather_tiles(), "interiors do not draw outdoor particles");

    const int days[] = { 1, 13, 27, 35, 10 };
    const int maps[] = { MAP_TOWN, MAP_BROOKMILL, MAP_DUSKMERE, MAP_FROSTHOLLOW, MAP_RISE };
    const int tiles[] = { WFX_GLOW, WFX_STREAM, WFX_GLOW, WFX_SNOW, WFX_STAR };
    for (int i = 0; i < 5; i++) {
        gtime.day = days[i];
        gtime.minute = (i == 2 || i == 4) ? 22 * 60 : 12 * 60;
        events.rolled_day = gtime.day;
        events.festival = events_festival_for_day(gtime.day);
        map_load(maps[i]);
        cam_x = (i == 2 ? 29 : i == 0 ? 13 : i == 1 ? 14 : i == 3 ? 12 : 9) * 16 - 120;
        cam_y = (i == 0 ? 10 : i == 1 || i == 4 ? 12 : 14) * 16 - 80;
        oam_count = 0;
        festival_draw_particles();
        CHECK(tile_count(OT_WEATHER + tiles[i]) > 0, "scheduled festival renders visible effect on its host map");
        if (i == 2 || i == 4) {
            gtime.minute = 12 * 60;
            oam_count = 0;
            festival_draw_particles();
            CHECK(!weather_tiles(), "night festival effect is absent by day");
        }
    }
    gtime.day = 2;
    events.rolled_day = 2;
    events.festival = FEST_NONE;
    map_load(MAP_TOWN);
    oam_count = 0;
    festival_draw_particles();
    CHECK(!weather_tiles(), "festival effect disappears after its date");
    CHECK(gtime.weather == WEATHER_CLEAR, "visuals do not change global farm rainfall");
    gtime.weather = WEATHER_RAIN;
    events.front_region = ER_NORTH;
    map_load(MAP_MEADOW);
    CHECK(time_raining_here() && gtime.weather == WEATHER_RAIN,
          "global rain still reaches ordinary outdoor maps independently of regional fronts");
    return failures ? 1 : 0;
}
