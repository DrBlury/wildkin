/* Field OBJ ownership, screen clipping, and rain placement regressions. */
#include "harness.h"

static int visible_rain(void)
{
    int n = 0;
    for (int i = 0; i < oam_count; i++)
        if ((oam_shadow[i * 4 + 2] & 1023) == OT_EMOTE + EMOTE_RAIN * 4) {
            int x = oam_shadow[i * 4 + 1] & 511;
            int y = oam_shadow[i * 4] & 255;
            if ((x < SCREEN_WIDTH || x > 512 - 16) && (y < SCREEN_HEIGHT || y > 256 - 16)) n++;
        }
    return n;
}

int main(void)
{
    fresh_game();
    CHECK(OT_NPC(6) + 8 <= OT_EMOTE && OT_EMOTE + EMOTE_COUNT * 4 <= OT_ITEM_BALL,
          "field people and emotes own disjoint OBJ tiles");
    CHECK(OT_CARAVAN + 8 <= OT_TO(0) && OT_TO(TO_COUNT - 1) + 4 <= OT_GRIM_ASH &&
          OT_TO(TO_COUNT - 1) + 4 <= OT_TX(0),
          "farm, travel objects, ash, and effects own disjoint OBJ tiles");
    travel_load_gfx();
    u32 boulder[32];
    for (int i = 0; i < 32; i++) boulder[i] = VRAM_OBJ_TILES[OT_TO(TO_BOULDER) * 8 + i];
    copy32(VRAM_OBJ_TILES + OT_GRIM_ASH * 8, GRIM_ASH_FLAKE, 8);
    int boulder_intact = 1;
    for (int i = 0; i < 32; i++)
        if (VRAM_OBJ_TILES[OT_TO(TO_BOULDER) * 8 + i] != boulder[i]) boulder_intact = 0;
    CHECK(boulder_intact, "ash upload cannot overwrite the boulder tile");

    oam_begin();
    spr_push(-16, 0, 1, SQ16, 0, 2, 0);
    spr_push(-15, 0, 1, SQ16, 0, 2, 0);
    spr_push(0, -32, 1, TALL16x32, 0, 2, 0);
    spr_push(0, -31, 1, TALL16x32, 0, 2, 0);
    spr_push(-32, 0, 1, WIDE32x16, 0, 2, 0);
    spr_push(-31, 0, 1, WIDE32x16, 0, 2, 0);
    CHECK(oam_count == 3, "only intersecting 16x16, 16x32 and 32x16 sprites enter OAM");
    oam_begin();
    spr_push(-64, 0, 1, SQ64, 0, 2, 0);
    spr_push(-63, 0, 1, SQ64, 0, 2, 0);
    CHECK(oam_count == 1, "64-pixel sprites retain their own partial-screen margin");

    map_load(MAP_MEADOW);
    gtime.weather = WEATHER_RAIN;
    events.front_region = ER_NORTH;
    cam_x = 11000;
    cam_y = 0;
    field_anim_frame = 0;
    frame_count += 2;
    oam_begin();
    farm_draw();
    CHECK(time_raining_here() && visible_rain() >= 6,
          "rain stays on screen even when the camera phase exceeds the rain period");
    flag_set(FLAG_STARTER);
    oam_begin();
    draw_weather();
    CHECK(storm_active() && visible_rain() >= 5, "storm rain also wraps into the visible camera range");
    map_load(MAP_REST);
    int foreign_visible = 0;
    for (int i = 0; i < NPC_COUNT; i++)
        if (npc_visible[i] && NPCS[i].map != cur_map) foreign_visible++;
    CHECK(!foreign_visible, "map load does not retain a foreign-map person's visibility");
    oam_begin();
    farm_draw();
    CHECK(!visible_rain(), "rain is not emitted inside a room");
    /* Battle portraits really occupy 0..127, overlapping rain/emotes. */
    map_load(MAP_MEADOW);
    field_load_tileset();
    copy32(VRAM_OBJ_TILES + OT_PORTRAIT(SIDE_ALLY) * 8, hero_back_gfx[0], 64 * 8);
    CHECK(memcmp(VRAM_OBJ_TILES + OT_EMOTE * 8, emote_gfx, sizeof(emote_gfx)) != 0,
          "battle portrait reproduces overwritten rain and emote tiles");
    game_mode = MODE_PARTY;
    field_return();
    CHECK(memcmp(VRAM_OBJ_TILES + OT_EMOTE * 8, emote_gfx, sizeof(emote_gfx)) == 0,
          "returning to the field restores rain and emotes instead of displaying portrait fragments");
    CHECK(memcmp(obj_palette + OBANK_PLAYER * 16, char_palettes[CHR_PLAYER], 32) == 0 &&
          memcmp(obj_palette + OBANK_EMOTE * 16, travel_fx_palette, 32) == 0,
          "field return restores player colours and the compatible rain/travel palette");
    map_load(MAP_WILLOW_ACRE);
    field_load_tileset();
    CHECK(memcmp(obj_palette + FARM_OBANK * 16 + 9, FX_PAL, sizeof(FX_PAL)) == 0,
          "farm cursor and tool colours survive the shared travel palette upload");
    u32 cursor[32];
    memcpy(cursor, VRAM_OBJ_TILES + OT_FARM_CURSOR * 8, sizeof(cursor));
    memset(VRAM_OBJ_TILES + OT_FARM_CURSOR * 8, 0x55, sizeof(cursor));
    game_mode = MODE_PARTY;
    field_return();
    CHECK(memcmp(cursor, VRAM_OBJ_TILES + OT_FARM_CURSOR * 8, sizeof(cursor)) == 0 &&
          memcmp(obj_palette + FARM_OBANK * 16 + 9, FX_PAL, sizeof(FX_PAL)) == 0,
          "field return restores area-specific farm sprites and their colours");
    int berry_map = -1;
    for (int m = 0; m < MAP_COUNT && berry_map < 0; m++)
        if (m != MAP_WILLOW_ACRE)
            for (int i = 0; i < MAPS[m].obj_count; i++)
                if (MAPS[m].objs[i].kind == OBJ_BERRY) { berry_map = m; break; }
    CHECK(berry_map >= 0, "an outdoor berry fixture exists");
    if (berry_map >= 0) {
        map_load(berry_map);
        u16 berry_palette[7];
        memcpy(berry_palette, obj_palette + FARM_OBANK * 16 + 9, sizeof(berry_palette));
        field_load_tileset();
        CHECK(memcmp(berry_palette, obj_palette + FARM_OBANK * 16 + 9, sizeof(berry_palette)) == 0,
              "berry colours are restored after shared palettes instead of taking travel colours");
    }
    return failures ? 1 : 0;
}
