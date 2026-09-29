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
/* Elevation (docs/ELEVATION.md): features over the height layer, and the
 * designated initializers that give a map its layer:
 *   [MAP_X] = { ..., { links }, { offsets }, ELEV(X_ELEV, X_FEATS) }, */
#define EF(K, X, Y, W, H) { EF_##K, X, Y, W, H }
#define NFEAT(a) ((u8)(sizeof(a) / sizeof(a[0])))
#define ELEV(ROWS, FEATS) .elev = ROWS, .feats = FEATS, .feat_count = NFEAT(FEATS)
#define ELEV_ONLY(ROWS) .elev = ROWS

#define PERSON(map, x, y, chr, face, beh, scr, lore, name, text) \
    { map, x, y, CHR_##chr, DIR_##face, BEH_##beh, SCR_##scr, lore, NO_TRAINER, 0, NO_KIN, name, text }
#define FIXTURE(MAP, X, Y, SCRIPT, NAME) \
    { .map = MAP, .x = X, .y = Y, .chr = CHR_SCIENTIST, .facing = DIR_DOWN, \
      .behavior = BEH_STILL, .script = SCR_##SCRIPT, .lore = NO_LORE, \
      .trainer = NO_TRAINER, .kin = NO_KIN, .name = NAME, .fixture = 1 }
#define PERSON_KIN(map, x, y, chr, face, beh, scr, lore, kin, name, text) \
    { map, x, y, CHR_##chr, DIR_##face, BEH_##beh, SCR_##scr, lore, NO_TRAINER, 0, kin, name, text }
#define WARDEN(map, x, y, chr, face, sight, tr, kin, text) \
    { map, x, y, CHR_##chr, DIR_##face, BEH_LOOK, SCR_WARDEN, NO_LORE, tr, sight, kin, 0, text }

#define MAP_PATCHES(P) .patches = P, .patch_count = NDEC(P)
#define SIGN_ROUTE(map, x, y, title, directions) { map, x, y, title "\n" directions }
#define PERSON_EVENT(map, x, y, chr, face, beh, scr, lore, name, text, event_id) \
    { map, x, y, CHR_##chr, DIR_##face, BEH_##beh, SCR_##scr, lore, NO_TRAINER, 0, NO_KIN, name, text, 0, 0, WHEN_ANY, event_id }

/* Conditional people keep the original macros unchanged for existing regions. */
#define PERSON_IF(map, x, y, chr, face, beh, scr, lore, name, text, show, hide) \
    { map, x, y, CHR_##chr, DIR_##face, BEH_##beh, SCR_##scr, lore, NO_TRAINER, 0, NO_KIN, name, text, show, hide, WHEN_ANY, 0 }
#define PERSON_WHEN(map, x, y, chr, face, beh, scr, lore, name, text, time) \
    { map, x, y, CHR_##chr, DIR_##face, BEH_##beh, SCR_##scr, lore, NO_TRAINER, 0, NO_KIN, name, text, 0, 0, WHEN_##time, 0 }
#define PERSON_KIN_IF(map, x, y, chr, face, beh, scr, lore, kin, name, text, show, hide) \
    { map, x, y, CHR_##chr, DIR_##face, BEH_##beh, SCR_##scr, lore, NO_TRAINER, 0, kin, name, text, show, hide, WHEN_ANY, 0 }
#define WARDEN_IF(map, x, y, chr, face, sight, tr, kin, text, show, hide) \
    { map, x, y, CHR_##chr, DIR_##face, BEH_LOOK, SCR_WARDEN, NO_LORE, tr, sight, kin, 0, text, show, hide, WHEN_ANY, 0 }

/* Route aliases are declared before the region map initializers. */
#define SONG_ROUTE_EAST SONG_ROUTE
#define SONG_ROUTE_WEST SONG_ROUTE
#define SONG_ROUTE_NORTH SONG_ROUTE
#define SONG_ROUTE_FAR SONG_ROUTE
#define SONG_ROUTE_GRIM SONG_ROUTE

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
enum { QUEST_SIDE, QUEST_MAIN, QUEST_PROJECT, QUEST_EVENT, QUEST_CATEGORY_COUNT };
typedef struct {
    const char *name, *goal;
    const char *const *stage_goals;
    u8 n_stages, category;
    const u8 *stage_maps; /* MAP_NONE means no marker; index is current stage */
} QuestDef;
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
