/*
 * The world: every region's maps, doors, people, wardens, signs, satchels,
 * wild zones and story flags, gathered from src/game/world/<region>/.
 * Each region is owned by one contributor (docs/EXPANSION.md, section 9);
 * add things to your own region's files, never here.
 *
 * Map rows are ASCII grids of 16x16 metatiles decoded through the map's
 * tileset legend (tools/tilesets/, gfx_field.h: TILESETS[ts].legend), plus
 * building stamps, decor placements and objects.
 */

/* ---------------- ids ---------------- */

enum {
#include "all_ids.inc"
    MAP_COUNT
};
typedef char MapIdsFitU8[MAP_COUNT < MAP_NONE ? 1 : -1];

/* Battle backdrops for a map (set_battle_scene maps these onto the bout
 * engine's scenes). */
enum {
    SC_MEADOW, SC_FOREST, SC_LAKE, SC_RING, SC_STORM, SC_CITY, SC_COAST, SC_SEA, SC_SNOW,
    SC_CAVE, SC_GRIM, SC_CRYPT, SC_VOLCANO, SC_DREAM, SC_FARM, SC_LAIR, SC_COUNT
};

enum {
    ZONE_EMPTY = ZONE_NONE,
#include "all_zone_ids.inc"
    ZONE_COUNT
};

enum {
#include "all_trainer_ids.inc"
    TRAINER_ID_COUNT
};

enum {
    SCR_TALK,      /* says NpcDef.text; reveals lore if it has a source */
    SCR_WARDEN,    /* a warden: bout (or after-bout text) */
#include "all_script_ids.inc"
    SCR_COUNT
};

enum {
#include "all_flag_ids.inc"
    FLAG_COUNT
};

enum {
    QUEST_NONE_ID,
#include "all_quest_ids.inc"
    QUEST_COUNT
};

/* ---------------- helpers for region data ---------------- */

#define DP(K, X, Y) { DK_##K, X, Y, 0 }
#define DPF(K, X, Y) { DK_##K, X, Y, DF_HFLIP }
#define OBJ(K, X, Y, ARG) { OBJ_##K, X, Y, ARG }
#define NDEC(a) ((u8)(sizeof(a) / sizeof(a[0])))
#define NOBJ(a) ((u8)(sizeof(a) / sizeof(a[0])))
#define NSLOT(a) ((u8)(sizeof(a) / sizeof(a[0])))
#define NO_LINKS { MAP_NONE, MAP_NONE, MAP_NONE, MAP_NONE }, { 0, 0, 0, 0 }

#define PERSON(map, x, y, chr, face, beh, scr, lore, name, text) \
    { map, x, y, CHR_##chr, DIR_##face, BEH_##beh, SCR_##scr, lore, NO_TRAINER, 0, NO_KIN, name, text }
#define PERSON_KIN(map, x, y, chr, face, beh, scr, lore, kin, name, text) \
    { map, x, y, CHR_##chr, DIR_##face, BEH_##beh, SCR_##scr, lore, NO_TRAINER, 0, kin, name, text }
#define WARDEN(map, x, y, chr, face, sight, tr, kin, text) \
    { map, x, y, CHR_##chr, DIR_##face, BEH_LOOK, SCR_WARDEN, NO_LORE, tr, sight, kin, 0, text }

/* ---------------- data ---------------- */

#include "all_data.h"

static const MapDef MAPS[MAP_COUNT] = {
#include "all_maps.inc"
};

/* Doors, cave mouths and ladders: stepping into (map, x, y) takes you to
 * (dest, dx, dy). Exit mats inside lead back out of the nearest door. */
static const Warp WARPS[] = {
#include "all_warps.inc"
};

static const TrainerDef TRAINERS[TRAINER_ID_COUNT] = {
#include "all_trainers.inc"
};

static const NpcDef NPCS[] = {
#include "all_npcs.inc"
};

static const Sign SIGNS[] = {
#include "all_signs.inc"
};

static const ItemBall ITEM_BALLS[] = {
#include "all_satchels.inc"
};

static const WildZone WILD_ZONES[ZONE_COUNT] = {
    [ZONE_EMPTY] = { 0, 0, 0, "" },
#include "all_zones.inc"
};

/* Quests shown in the quest log (quest.c keeps their stages). */
typedef struct { const char *name, *goal; } QuestDef;
static const QuestDef QUESTS[QUEST_COUNT] = {
    [QUEST_NONE_ID] = { "", "" },
#include "all_quests.inc"
};

/* Places you can fly to (once visited) and where they sit on the town map. */
typedef struct { u8 map, x, y, map_x, map_y; const char *name; } FlyPoint;
static const FlyPoint FLY_POINTS[] = {
#include "all_flypoints.inc"
};
#define FLY_POINT_COUNT ((int)(sizeof(FLY_POINTS) / sizeof(FLY_POINTS[0])))
