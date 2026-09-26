/*
 * Overworld engine: maps, the streaming metatile renderer, decor, grid
 * movement, people, wardens' sight lines, kin that follow you, visible wild
 * kin, ledges, map links and weather.
 *
 * Maps (maps.h) are ASCII grids of 16x16 metatiles plus building stamps
 * and decor placements. Three hardware layers show a map:
 *   BG0 (prio 3)  ground: terrain and stamps (opaque)
 *   BG2 (prio 2)  decor: transparent objects over any ground
 *   BG3 (prio 1)  top: tall-grass blades and decor cells drawn over people
 * Each uses a 32x32-tile screenblock as a 16x16 metatile ring buffer, so a
 * map can be any size: cells entering the view are written as the camera
 * moves. Paths and ponds are autotiled per 8x8 quadrant. Decor tiles are
 * copied into VRAM after the tileset when a map loads, one block per kind
 * the map uses.
 */

enum { DIR_DOWN, DIR_UP, DIR_LEFT, DIR_RIGHT };
static const s8 DIR_DX[4] = { 0, 0, -1, 1 };
static const s8 DIR_DY[4] = { 1, -1, 0, 0 };
static const u8 DIR_BACK[4] = { DIR_UP, DIR_DOWN, DIR_RIGHT, DIR_LEFT };

/* ---------------- map data types ---------------- */

/* Special cell values beyond metatile ids. */
#define CELL_PATH  0x100
#define CELL_WATER 0x101

enum {
    A_SOLID = 1, A_GRASS = 2, A_DOOR = 4, A_WATER = 8, A_COUNTER = 16,
    A_EXIT = 32, A_SIGN = 64, A_LEDGE = 128,
};

typedef struct { u16 base; u8 w, h, x, y; } Stamp;
#define STAMP(TS, NAME, X, Y) { MT_##TS##_##NAME, MT_##TS##_##NAME##_W, MT_##TS##_##NAME##_H, X, Y }

typedef struct { u8 kind, x, y, flags; } DecorPlace;
enum { DF_HFLIP = 1 };

enum { LINK_N, LINK_S, LINK_W, LINK_E };
#define MAP_NONE 0xFF
#define ZONE_NONE 0xFF

enum { MF_OUTDOOR = 1, MF_HEAL = 2 };

typedef struct {
    u8 w, h, tileset, scene;       /* scene: battle backdrop (BSCENE_*) */
    const char *const *rows;
    const Stamp *stamps;
    u8 stamp_count;
    const DecorPlace *decor;
    u8 decor_count;
    const char *name;
    u8 zone;                       /* WILD_ZONES index or ZONE_NONE */
    u8 flags;                      /* MF_* */
    u8 link[4];                    /* neighbour map per edge (LINK_*), MAP_NONE */
    s8 link_off[4];                /* coordinate shift into the neighbour */
} MapDef;

typedef struct { u8 map, x, y, dest, dx, dy; } Warp;

enum { BEH_STILL, BEH_LOOK, BEH_WANDER, BEH_PACE_H, BEH_PACE_V };
#define NO_TRAINER 0xFF
#define NO_KIN 0xFF
#define NO_LORE 0xFF

typedef struct {
    u8 map, x, y, chr, facing, behavior;
    u8 script;          /* SCR_* */
    u8 lore;            /* LSRC_* the person reveals, or NO_LORE */
    u8 trainer;         /* TRAINERS index or NO_TRAINER */
    u8 sight;           /* cells a warden can see */
    u8 kin;             /* species walking beside them, or NO_KIN */
    const char *name;
    const char *text;   /* what they say (after the bout, for wardens) */
} NpcDef;

typedef struct {
    const char *name;   /* "WARDEN ROSA" */
    u8 count;
    u8 species[3], level[3];
    u16 prize;
    const char *intro;  /* said when they spot you */
    const char *lose;   /* said when you beat them */
} TrainerDef;

typedef struct { u8 map, x, y; const char *text; } Sign;
typedef struct { u8 map, x, y, item, qty; } ItemBall;

typedef struct { u8 species, weight, min_level, max_level; } WildSlot;
typedef struct { const WildSlot *slots; u8 count, max_active; const char *name; } WildZone;

#define NSTAMP(a) ((u8)(sizeof(a) / sizeof(a[0])))
#define NROWS(a) ((u8)(sizeof(a) / sizeof(a[0])))

#include "maps.h"

#define WARP_COUNT ((int)(sizeof(WARPS) / sizeof(WARPS[0])))
#define NPC_COUNT ((int)(sizeof(NPCS) / sizeof(NPCS[0])))
#define SIGN_COUNT ((int)(sizeof(SIGNS) / sizeof(SIGNS[0])))
#define ITEM_BALL_COUNT ((int)(sizeof(ITEM_BALLS) / sizeof(ITEM_BALLS[0])))
#define TRAINER_COUNT ((int)(sizeof(TRAINERS) / sizeof(TRAINERS[0])))
#define WILD_ZONE_COUNT ((int)(sizeof(WILD_ZONES) / sizeof(WILD_ZONES[0])))

/* ---------------- actors & world state ---------------- */

typedef struct {
    s16 x, y;       /* metatile */
    s8 ox, oy;      /* pixel offset while walking */
    u8 facing, moving, anim, hop;
    u16 timer;
} Actor;

typedef struct { Actor a; u8 species, lustrous, shown; } KinActor;

static Actor npc_state[NPC_COUNT];
static KinActor npc_kin[NPC_COUNT];
static KinActor follower;

#define WILD_MAX 5
static struct {
    KinActor k;
    Monster mon;
    u8 active, brimming, noticed;
    u16 life, think;
} wild[WILD_MAX] EWRAM_BSS;
static int wild_spawn_timer;
static int wild_battle_slot = -1;

static int cur_map;
static Actor player;
static u32 story_flags;      /* FLAG_* bits */
static u32 item_flags[2];    /* picked-up satchels */
static u32 trainer_flags;    /* beaten wardens */

enum {
    FLAG_STARTER = 1u << 0,
    FLAG_LEAF_STONE = 1u << 1,     /* the gardener's BLOOM SHARD */
    FLAG_BAKER_GIFT = 1u << 2,
    FLAG_KID_GIFT = 1u << 3,
    FLAG_INTRO = 1u << 4,          /* storybook seen */
    FLAG_NOTE = 1u << 5,           /* read Gran's note */
    FLAG_SASH = 1u << 6,           /* beat Warden Marlo */
    FLAG_STORM_TOLD = 1u << 7,     /* the Keeper sent you to the Stormstone */
    FLAG_STORM_CALMED = 1u << 8,
    FLAG_DRAKORA_JOINED = 1u << 9,
    FLAG_TWIN_CRYSTAL = 1u << 10,
    FLAG_GRAN_GIFT = 1u << 11,
    FLAG_PIP_GIFT = 1u << 12,
    FLAG_VASS_GIFT = 1u << 13,
    FLAG_HERMIT_GIFT = 1u << 14,
    FLAG_WOODWARD_GIFT = 1u << 15,
    FLAG_RING_WON_ONCE = 1u << 16,
};

static int item_taken(int i) { return (item_flags[i >> 5] >> (i & 31)) & 1; }
static void item_take(int i) { item_flags[i >> 5] |= 1u << (i & 31); }
static int trainer_beaten(int t) { return (trainer_flags >> t) & 1; }

#define MAP_MAX_W 48
#define MAP_MAX_H 48
EWRAM_BSS static u16 map_cells[MAP_MAX_W * MAP_MAX_H];
EWRAM_BSS static u8 map_decor[MAP_MAX_W * MAP_MAX_H];  /* decor instance + 1, 0 = none */
static u8 map_w, map_h, map_tileset;
static u16 decor_base[DK_COUNT];                        /* VRAM tile of each loaded kind */
static int decor_tiles_used;                            /* first free scene tile */

/* ---------------- map decoding ---------------- */

static unsigned cell_hash(int x, int y)
{
    unsigned h = (unsigned)x * 73856093u ^ (unsigned)y * 19349663u;
    h ^= h >> 13;
    h *= 0x5bd1e995u;
    h ^= h >> 15;
    return h;
}

static u16 grass_variant(int x, int y, u16 g1, u16 g2, u16 g3)
{
    unsigned h = cell_hash(x, y) % 16u;
    return h == 0 ? g3 : h < 5 ? g2 : g1;
}

static u16 decode_town_char(char c, int x, int y)
{
    switch (c) {
    case '.': return grass_variant(x, y, MT_T_GRASS, MT_T_GRASS2, MT_T_GRASS3);
    case ',': return MT_T_TALLGRASS;
    case 'r': return MT_T_FLOWER_RED;
    case 'y': return MT_T_FLOWER_YELLOW;
    case '=': return CELL_PATH;
    case '~': return CELL_WATER;
    case '#': return MT_T_STONE;
    case 'T': return MT_T_TREE_TOP;
    case 't': return MT_T_TREE_BOTTOM;
    case 'c': return MT_T_COURT;
    case 'h': return MT_T_COURT_LINE_H;
    case 'v': return MT_T_COURT_LINE_V;
    default: return MT_T_GRASS;
    }
}

static u16 decode_wild_char(char c, int x, int y)
{
    switch (c) {
    case '.': return grass_variant(x, y, MT_W_GRASS, MT_W_GRASS2, MT_W_GRASS3);
    case ',': return MT_W_TALLGRASS;
    case 'r': return MT_W_FLOWER_RED;
    case 'y': return MT_W_FLOWER_YELLOW;
    case '=': return CELL_PATH;
    case '~': return CELL_WATER;
    case '#': return MT_W_STONE;
    case 'T': return MT_W_TREE_TOP;
    case 't': return MT_W_TREE_BOTTOM;
    case 'P': return MT_W_PINE_TOP;
    case 'p': return MT_W_PINE_BOTTOM;
    case 'L': return MT_W_LEDGE;
    case '[': return MT_W_LEDGE_L;
    case ']': return MT_W_LEDGE_R;
    case 'C': return MT_W_CLIFF;
    case 'c': return MT_W_CLIFF_FACE;
    case 'd': return MT_W_DIRT;
    case 'm': return MT_W_MEADOW;
    case 's': return (cell_hash(x, y) % 8u) ? MT_W_SAND : MT_W_SAND2;
    case 'f': return (cell_hash(x, y) & 3) ? MT_W_FOREST : MT_W_FOREST2;
    case 'R': return MT_W_REEDS;
    default: return MT_W_GRASS;
    }
}

static u16 decode_interior_char(char c)
{
    switch (c) {
    case 'W': return MT_I_WALL_TOP;
    case 'w': return MT_I_WALL;
    case 'n': return MT_I_WINDOW;
    case 'k': return MT_I_WALL_CLOCK;
    case 'p': return MT_I_PAINTING;
    case '.': return MT_I_FLOOR;
    case ':': return MT_I_FLOOR2;
    case 'D': return MT_I_DOORMAT;
    case '<': return MT_I_COUNTER_L;
    case '=': return MT_I_COUNTER;
    case '>': return MT_I_COUNTER_R;
    default: return MT_I_VOID;
    }
}

static void map_decode(int id)
{
    const MapDef *m = &MAPS[id];
    for (int y = 0; y < m->h; y++)
        for (int x = 0; x < m->w; x++) {
            char c = m->rows[y][x];
            u16 v = m->tileset == TS_TOWN ? decode_town_char(c, x, y)
                  : m->tileset == TS_WILD ? decode_wild_char(c, x, y)
                  : decode_interior_char(c);
            map_cells[y * m->w + x] = v;
            map_decor[y * m->w + x] = 0;
        }
    for (int i = 0; i < m->stamp_count; i++) {
        const Stamp *s = &m->stamps[i];
        for (int dy = 0; dy < s->h; dy++)
            for (int dx = 0; dx < s->w; dx++)
                map_cells[(s->y + dy) * m->w + s->x + dx] = (u16)(s->base + dy * s->w + dx);
    }
    for (int i = 0; i < m->decor_count; i++) {
        const DecorPlace *p = &m->decor[i];
        const DecorDef *d = &DECOR_DEFS[m->tileset][p->kind];
        for (int dy = 0; dy < d->h; dy++)
            for (int dx = 0; dx < d->w; dx++) {
                int x = p->x + dx, y = p->y + dy;
                if (x < m->w && y < m->h) map_decor[y * m->w + x] = (u8)(i + 1);
            }
    }
}

static u16 map_cell(int x, int y)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h)
        return map_tileset == TS_TOWN ? MT_T_TREE_TOP : map_tileset == TS_WILD ? MT_W_TREE_TOP : MT_I_VOID;
    return map_cells[y * map_w + x];
}

/* Decor instance covering a cell (or 0), its sub-cell index in the kind's
 * own row-major layout (hflip resolved) and the kind's definition. */
static const DecorPlace *decor_at(int x, int y, int *sub, const DecorDef **def)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h) return 0;
    int i = map_decor[y * map_w + x];
    if (!i) return 0;
    const DecorPlace *p = &MAPS[cur_map].decor[i - 1];
    const DecorDef *d = &DECOR_DEFS[map_tileset][p->kind];
    int dx = x - p->x, dy = y - p->y;
    if (p->flags & DF_HFLIP) dx = d->w - 1 - dx;
    if (sub) *sub = dy * d->w + dx;
    if (def) *def = d;
    return p;
}

static int town_door_cell(int v)
{
    return v == MT_T_HOUSE_RED + 17 || v == MT_T_HOUSE_BLUE + 17 ||
           v == MT_T_SHOP + 17 || v == MT_T_HEAL + 17 || v == MT_T_LAB + 31;
}

static int wild_door_cell(int v)
{
    return v == MT_W_CABIN + 17 || v == MT_W_STATION + 17;
}

static int is_door_cell(int v)
{
    return map_tileset == TS_TOWN ? town_door_cell(v) : map_tileset == TS_WILD && wild_door_cell(v);
}

static int terrain_attr(int tileset, int v)
{
    if (tileset == TS_TOWN) {
        if (v == CELL_PATH) return 0;
        if (v == CELL_WATER) return A_SOLID | A_WATER;
        if (town_door_cell(v)) return A_SOLID | A_DOOR;
        if (v >= MT_T_HOUSE_RED && v < MT_T_COURT_CIRCLE) return A_SOLID;
        switch (v) {
        case MT_T_TALLGRASS: return A_GRASS;
        case MT_T_TREE_TOP: case MT_T_TREE_BOTTOM: return A_SOLID;
        default: return 0;
        }
    }
    if (tileset == TS_WILD) {
        if (v == CELL_PATH) return 0;
        if (v == CELL_WATER) return A_SOLID | A_WATER;
        if (wild_door_cell(v)) return A_SOLID | A_DOOR;
        if (v >= MT_W_CABIN && v < MT_WILD_COUNT) return A_SOLID;
        switch (v) {
        case MT_W_TALLGRASS: case MT_W_REEDS: return A_GRASS;
        case MT_W_TREE_TOP: case MT_W_TREE_BOTTOM: case MT_W_PINE_TOP: case MT_W_PINE_BOTTOM:
        case MT_W_CLIFF: case MT_W_CLIFF_FACE:
            return A_SOLID;
        case MT_W_LEDGE: case MT_W_LEDGE_L: case MT_W_LEDGE_R: return A_LEDGE;
        default: return 0;
        }
    }
    switch (v) {
    case MT_I_FLOOR: case MT_I_FLOOR2: return 0;
    case MT_I_DOORMAT: return A_EXIT;
    case MT_I_COUNTER: case MT_I_COUNTER_L: case MT_I_COUNTER_R: return A_SOLID | A_COUNTER;
    default:
        if (v >= MT_I_RUG && v < MT_I_RUG + MT_I_RUG_W * MT_I_RUG_H) return 0;
        return A_SOLID;
    }
}

static int cell_attr(int x, int y)
{
    int a = terrain_attr(map_tileset, map_cell(x, y));
    int sub;
    const DecorDef *d;
    if (decor_at(x, y, &sub, &d)) {
        if (d->floor & (1u << sub)) a &= ~(A_SOLID | A_WATER | A_LEDGE);
        if (d->solid & (1u << sub)) a |= A_SOLID;
    }
    return a;
}

/* ---------------- rendering ---------------- */

static s16 ring_x[16][16], ring_y[16][16]; /* map cell cached in each ring slot */
static int cam_x, cam_y;
static int field_anim_frame;

static void ring_invalidate(void)
{
    for (int y = 0; y < 16; y++)
        for (int x = 0; x < 16; x++)
            ring_x[y][x] = ring_y[y][x] = -32768;
}

static int same_kind(int v, int x, int y)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h) return 1;
    int n = map_cells[y * map_w + x];
    /* paths run right up to doorsteps */
    return n == v || (v == CELL_PATH && is_door_cell(n));
}

/* 8x8 autotile quadrants for a path/water cell. */
static void autotile_quads(int v, int x, int y, u16 out[4])
{
    const u16 (*q)[5];
    if (map_tileset == TS_WILD) q = v == CELL_PATH ? wild_path_quads : wild_water_quads;
    else q = v == CELL_PATH ? town_path_quads : town_water_quads;
    static const s8 qdx[4] = { -1, 1, -1, 1 }, qdy[4] = { -1, -1, 1, 1 };
    for (int c = 0; c < 4; c++) {
        int vs = same_kind(v, x, y + qdy[c]);
        int hs = same_kind(v, x + qdx[c], y);
        int ds = same_kind(v, x + qdx[c], y + qdy[c]);
        int variant = vs && hs ? (ds ? 0 : 1) : (vs ? 2 : (hs ? 3 : 4));
        out[c] = q[c][variant];
    }
}

static const u16 (*meta_bottom(void))[4]
{
    return map_tileset == TS_TOWN ? town_meta_bottom : map_tileset == TS_WILD ? wild_meta_bottom
                                                                              : interior_meta_bottom;
}

static const u16 (*meta_top(void))[4]
{
    return map_tileset == TS_TOWN ? town_meta_top : map_tileset == TS_WILD ? wild_meta_top
                                                                           : interior_meta_top;
}

/* Resolve a decor entry (local tile + 1) against the kind's VRAM block. */
static u16 decor_entry(u16 e, int kind)
{
    if (!e) return 0;
    return (u16)((e & 0xFC00) | (decor_base[kind] + (e & 1023) - 1));
}

static void render_cell(int mx, int my)
{
    int rx = mx & 15, ry = my & 15;
    if (ring_x[ry][rx] == mx && ring_y[ry][rx] == my) return;
    ring_x[ry][rx] = (s16)mx;
    ring_y[ry][rx] = (s16)my;
    u16 bottom[4], top[4], mid[4] = { 0, 0, 0, 0 };
    int v = map_cell(mx, my);
    if (map_tileset != TS_INTERIOR && (v == CELL_PATH || v == CELL_WATER)) {
        autotile_quads(v, mx, my, bottom);
        for (int i = 0; i < 4; i++) top[i] = 0;
    } else {
        for (int i = 0; i < 4; i++) {
            bottom[i] = meta_bottom()[v][i];
            top[i] = meta_top()[v][i];
        }
    }
    int sub;
    const DecorDef *d;
    const DecorPlace *p = decor_at(mx, my, &sub, &d);
    if (p) {
        const u16 *e = decor_meta[d->meta_first + sub];
        u16 q[4];
        if (p->flags & DF_HFLIP) {
            static const u8 SWAP[4] = { 1, 0, 3, 2 };
            for (int i = 0; i < 4; i++) {
                u16 x = decor_entry(e[SWAP[i]], p->kind);
                q[i] = x ? (u16)(x ^ 0x0400) : 0;
            }
        } else {
            for (int i = 0; i < 4; i++) q[i] = decor_entry(e[i], p->kind);
        }
        u16 *dst = (d->top & (1u << sub)) ? top : mid;
        for (int i = 0; i < 4; i++) dst[i] = q[i];
    }
    u16 *b = VRAM_MAP(SB_FIELD_BOTTOM), *t = VRAM_MAP(SB_FIELD_TOP), *m = VRAM_MAP(SB_PANEL);
    int idx = ry * 2 * 32 + rx * 2;
    static const u8 OFF[4] = { 0, 1, 32, 33 };
    for (int i = 0; i < 4; i++) {
        b[idx + OFF[i]] = bottom[i];
        m[idx + OFF[i]] = mid[i];
        t[idx + OFF[i]] = top[i];
    }
}

static int floor_div16(int v)
{
    return v >= 0 ? v >> 4 : -((15 - v) >> 4);
}

/* Write any newly visible cells; called in vblank. */
static void field_render_view(void)
{
    int x0 = floor_div16(cam_x), y0 = floor_div16(cam_y);
    for (int my = y0; my <= y0 + 10; my++)
        for (int mx = x0; mx <= x0 + 15; mx++)
            render_cell(mx, my);
    REG_BG0HOFS = (u16)cam_x;
    REG_BG0VOFS = (u16)cam_y;
    REG_BG3HOFS = (u16)cam_x;
    REG_BG3VOFS = (u16)cam_y;
    REG_BG2HOFS = (u16)cam_x;
    REG_BG2VOFS = (u16)cam_y;
}

/* ---------------- tileset, decor & weather palettes ---------------- */

static int storm_active(void)
{
    return !(story_flags & FLAG_STORM_CALMED) && (story_flags & FLAG_STARTER) &&
           (MAPS[cur_map].flags & MF_OUTDOOR);
}

/* Storm light: the palette mixed toward a cold grey-blue. */
static u16 storm_tint(u16 c)
{
    int r = c & 31, g = (c >> 5) & 31, b = (c >> 10) & 31;
    r = r * 72 / 100 + 3;
    g = g * 76 / 100 + 3;
    b = b * 80 / 100 + 5;
    return RGB15(clampi(r, 0, 31), clampi(g, 0, 31), clampi(b, 0, 31));
}

static void field_load_palettes(void)
{
    const u16 (*pal)[16] = map_tileset == TS_TOWN ? town_palettes
                         : map_tileset == TS_WILD ? wild_palettes : interior_palettes;
    int storm = storm_active();
    for (int b = 0; b < 8; b++)
        for (int i = 0; i < 16; i++)
            bg_palette[b * 16 + i] = storm ? storm_tint(pal[b][i]) : pal[b][i];
    bg_palette[0] = map_tileset == TS_INTERIOR ? RGB15(0, 0, 0) : bg_palette[1];
}

static void field_load_tileset(void)
{
    if (map_tileset == TS_TOWN) {
        copy32(VRAM_SCENE_TILES, town_tiles, TOWN_TILE_COUNT * 8);
        decor_tiles_used = TOWN_TILE_COUNT;
    } else if (map_tileset == TS_WILD) {
        copy32(VRAM_SCENE_TILES, wild_tiles, WILD_TILE_COUNT * 8);
        decor_tiles_used = WILD_TILE_COUNT;
    } else {
        copy32(VRAM_SCENE_TILES, interior_tiles, INTERIOR_TILE_COUNT * 8);
        decor_tiles_used = INTERIOR_TILE_COUNT;
    }
    /* one block per decor kind this map uses (first animation frame) */
    for (int k = 0; k < DK_COUNT; k++) decor_base[k] = 0;
    const MapDef *m = &MAPS[cur_map];
    for (int i = 0; i < m->decor_count; i++) {
        int k = m->decor[i].kind;
        if (decor_base[k]) continue;
        const DecorDef *d = &DECOR_DEFS[map_tileset][k];
        if (decor_tiles_used + d->tile_count > 512) continue; /* the map tests catch this */
        decor_base[k] = (u16)decor_tiles_used;
        copy32(VRAM_SCENE_TILES + decor_tiles_used * 8, decor_tiles + d->tile_first * 8,
               (unsigned)d->tile_count * 8);
        decor_tiles_used += d->tile_count;
    }
    field_load_palettes();
    ring_invalidate();
}

/* Tile-data swaps for rippling water, swaying flowers and animated decor. */
static void field_animate_tiles(void)
{
    field_anim_frame++;
    if (map_tileset != TS_INTERIOR) {
        int wild_ts = map_tileset == TS_WILD;
        if (field_anim_frame % 20 == 0) {
            int f = field_anim_frame / 20 % 3;
            if (wild_ts)
                copy32(VRAM_SCENE_TILES + WILD_WATER_ANIM_TILE * 8, wild_water_anim[f], WILD_WATER_ANIM_COUNT * 8);
            else
                copy32(VRAM_SCENE_TILES + TOWN_WATER_ANIM_TILE * 8, town_water_anim[f], TOWN_WATER_ANIM_COUNT * 8);
        }
        if (field_anim_frame % 32 == 0) {
            int f = field_anim_frame / 32 % 2;
            if (wild_ts)
                copy32(VRAM_SCENE_TILES + WILD_FLOWER_ANIM_TILE * 8, wild_flower_anim[f], WILD_FLOWER_ANIM_COUNT * 8);
            else
                copy32(VRAM_SCENE_TILES + TOWN_FLOWER_ANIM_TILE * 8, town_flower_anim[f], TOWN_FLOWER_ANIM_COUNT * 8);
        }
    }
    for (int k = 0; k < DK_COUNT; k++) {
        const DecorDef *d = &DECOR_DEFS[map_tileset][k];
        if (!decor_base[k] || d->frames < 2 || !d->period) continue;
        if (field_anim_frame % d->period) continue;
        int f = field_anim_frame / d->period % d->frames;
        copy32(VRAM_SCENE_TILES + decor_base[k] * 8, decor_tiles + (d->tile_first + f * d->tile_count) * 8,
               (unsigned)d->tile_count * 8);
    }
}

static void field_setup_bg(void)
{
    REG_BG0CNT = BGCNT_CHARBLOCK(0) | BGCNT_SCREENBLOCK(SB_FIELD_BOTTOM) | BGCNT_PRIO(3);
    REG_BG3CNT = BGCNT_CHARBLOCK(0) | BGCNT_SCREENBLOCK(SB_FIELD_TOP) | BGCNT_PRIO(1);
    /* BG2 = decor layer (below people) while in the field */
    REG_BG2CNT = BGCNT_CHARBLOCK(0) | BGCNT_SCREENBLOCK(SB_PANEL) | BGCNT_PRIO(2);
    REG_DISPCNT = DCNT_MODE0 | DCNT_BG0 | DCNT_BG1 | DCNT_BG2 | DCNT_BG3 | DCNT_OBJ | DCNT_OBJ_1D;
    ring_invalidate();
}

/* ---------------- map loading & queries ---------------- */

static void kin_place(KinActor *k, int species, int lustrous, int x, int y, int facing)
{
    k->a.x = (s16)x;
    k->a.y = (s16)y;
    k->a.ox = k->a.oy = 0;
    k->a.facing = (u8)facing;
    k->a.moving = 0;
    k->a.anim = 0;
    k->a.hop = 0;
    k->species = (u8)species;
    k->lustrous = (u8)lustrous;
    k->shown = 1;
}

static void npcs_reset(void)
{
    for (int i = 0; i < NPC_COUNT; i++) {
        Actor *a = &npc_state[i];
        a->x = NPCS[i].x;
        a->y = NPCS[i].y;
        a->ox = a->oy = 0;
        a->facing = NPCS[i].facing;
        a->moving = 0;
        a->anim = 0;
        a->hop = 0;
        a->timer = (u16)(60 + rng_range(90));
        npc_kin[i].shown = 0;
        if (NPCS[i].kin != NO_KIN && NPCS[i].map == cur_map) {
            int bx = a->x + DIR_DX[DIR_BACK[a->facing]], by = a->y + DIR_DY[DIR_BACK[a->facing]];
            if (NPCS[i].facing == DIR_DOWN || NPCS[i].facing == DIR_UP) {
                bx = a->x + 1;
                by = a->y;
            }
            kin_place(&npc_kin[i], NPCS[i].kin, 0, bx, by, a->facing);
        }
    }
}

static void wild_clear(void)
{
    for (int i = 0; i < WILD_MAX; i++) wild[i].active = 0;
    wild_spawn_timer = 30;
}

static void map_load(int id)
{
    cur_map = id;
    map_w = MAPS[id].w;
    map_h = MAPS[id].h;
    map_tileset = MAPS[id].tileset;
    map_decode(id);
    npcs_reset();
    wild_clear();
}

static int npc_at(int x, int y)
{
    for (int i = 0; i < NPC_COUNT; i++) {
        if (NPCS[i].map != cur_map) continue;
        const Actor *a = &npc_state[i];
        if (a->x == x && a->y == y) return i;
        /* a walking NPC also occupies the cell it is leaving */
        if (a->moving && a->x - DIR_DX[a->facing] == x && a->y - DIR_DY[a->facing] == y)
            return i;
    }
    return -1;
}

static int npc_kin_at(int x, int y)
{
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].map == cur_map && npc_kin[i].shown && npc_kin[i].a.x == x && npc_kin[i].a.y == y)
            return i;
    return -1;
}

static int wild_at(int x, int y)
{
    for (int i = 0; i < WILD_MAX; i++)
        if (wild[i].active && wild[i].k.a.x == x && wild[i].k.a.y == y) return i;
    return -1;
}

static int item_ball_at(int x, int y)
{
    for (int i = 0; i < ITEM_BALL_COUNT; i++)
        if (ITEM_BALLS[i].map == cur_map && ITEM_BALLS[i].x == x &&
            ITEM_BALLS[i].y == y && !item_taken(i))
            return i;
    return -1;
}

static int sign_at(int x, int y)
{
    for (int i = 0; i < SIGN_COUNT; i++)
        if (SIGNS[i].map == cur_map && SIGNS[i].x == x && SIGNS[i].y == y) return i;
    return -1;
}

static int warp_at(int map, int x, int y)
{
    for (int i = 0; i < WARP_COUNT; i++)
        if (WARPS[i].map == map && WARPS[i].x == x && WARPS[i].y == y) return i;
    return -1;
}

static int follower_active(void);

/* Walkable for people: no walls, people, their kin, wild kin or satchels. */
static int cell_walkable(int x, int y)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h) return 0;
    if (cell_attr(x, y) & (A_SOLID | A_LEDGE)) return 0;
    if (npc_at(x, y) >= 0) return 0;
    if (npc_kin_at(x, y) >= 0) return 0;
    if (wild_at(x, y) >= 0) return 0;
    if (item_ball_at(x, y) >= 0) return 0;
    return 1;
}

/* ---------------- camera ---------------- */

static void field_update_camera(void)
{
    int px = player.x * 16 + player.ox, py = player.y * 16 + player.oy;
    int mw = map_w * 16, mh = map_h * 16;
    cam_x = mw <= SCREEN_WIDTH ? (mw - SCREEN_WIDTH) / 2
                               : clampi(px + 8 - SCREEN_WIDTH / 2, 0, mw - SCREEN_WIDTH);
    cam_y = mh <= SCREEN_HEIGHT ? (mh - SCREEN_HEIGHT) / 2
                                : clampi(py + 8 - SCREEN_HEIGHT / 2, 0, mh - SCREEN_HEIGHT);
}

/* ---------------- sprites ---------------- */

/* Walk cycle: stand, step A, stand, step B. */
static int actor_frame(const Actor *a)
{
    static const u8 base[4] = { 0, 3, 6, 6 };
    int f = 0;
    if (a->moving) {
        int phase = (a->anim >> 3) & 3;
        f = phase == 1 ? 1 : phase == 3 ? 2 : 0;
    }
    return base[a->facing] + f;
}

/* Hop arc (ledges): pixels above the ground. */
static int actor_lift(const Actor *a)
{
    if (!a->hop) return 0;
    int t = a->hop; /* 16 .. 1 */
    return (t * (16 - t)) / 8;
}

#define OT_EMOTE 64                     /* EMOTE_COUNT x 4 tiles (NPC slots 7+ unused) */
#define OT_OWKIN(i) (768 + (i) * 16)    /* 16 overworld kin slots */
#define OBANK_EMOTE 15
#define KIN_BANK_FIRST 9
#define KIN_BANK_COUNT 6

static const u32 *kin_frame_gfx(int species, int frame)
{
#ifdef MON_OW_FRAMES
    return mon_ow_gfx[species][frame];
#else
    (void)frame;
    return mon_icon_gfx[species];
#endif
}

/* Frame of a kin: down 0/1, up 2/3, side 4/5 (right = flipped left). */
static int kin_frame(const KinActor *k)
{
    int step = k->a.moving ? (k->a.anim >> 3) & 1 : (field_anim_frame >> 5) & 1;
    switch (k->a.facing) {
    case DIR_UP: return 2 + step;
    case DIR_LEFT: case DIR_RIGHT: return 4 + step;
    default: return step;
    }
}

typedef struct { int y, x, kind, a, b, flip; } FieldSprite; /* kind: 0 person, 1 kin, 2 satchel */

static struct { int npc, kind, timer; } emote = { -1, 0, 0 };
static int starter_preview = -1; /* script.c: species shown while choosing a starter */

static void field_emote(int npc, int kind, int frames)
{
    emote.npc = npc;
    emote.kind = kind;
    emote.timer = frames;
}

/* Rain streaks while the storm brims (outdoors). */
static void draw_weather(void)
{
    if (!storm_active()) return;
    for (int i = 0; i < 10; i++) {
        int speed = 5 + (i % 3);
        int x = (int)((cell_hash(i, 7) % 272u) + field_anim_frame * 2 - cam_x / 2) % 272 - 16;
        int y = (int)((cell_hash(i, 3) % 192u) + field_anim_frame * speed) % 192 - 16;
        spr_push(x, y, OT_EMOTE + EMOTE_RAIN * 4, SQ16, OBANK_EMOTE, 1, 0);
    }
}

static void field_draw_sprites(void)
{
    FieldSprite list[48];
    int n = 0;
    int lift = actor_lift(&player);
    copy32(VRAM_OBJ_TILES + OT_PLAYER * 8, char_gfx[CHR_PLAYER][actor_frame(&player)], 64);
    list[n++] = (FieldSprite){ player.y * 16 + player.oy, player.x * 16 + player.ox, 0,
                               OT_PLAYER | (lift << 16), OBANK_PLAYER, player.facing == DIR_RIGHT };
    int slot = 0;
    for (int i = 0; i < NPC_COUNT && n < 40; i++) {
        if (NPCS[i].map != cur_map) continue;
        const Actor *a = &npc_state[i];
        int wx = a->x * 16 + a->ox, wy = a->y * 16 + a->oy;
        if (wx - cam_x >= -16 && wx - cam_x <= SCREEN_WIDTH && wy - cam_y >= -16 &&
            wy - cam_y <= SCREEN_HEIGHT + 16 && slot < 7) {
            copy32(VRAM_OBJ_TILES + OT_NPC(slot) * 8, char_gfx[NPCS[i].chr][actor_frame(a)], 64);
            load_pal(obj_palette + (OBANK_NPC + slot) * 16, char_palettes[NPCS[i].chr]);
            list[n++] = (FieldSprite){ wy, wx, 0, OT_NPC(slot), OBANK_NPC + slot, a->facing == DIR_RIGHT };
            if (emote.npc == i && emote.timer > 0)
                list[n++] = (FieldSprite){ wy + 1, wx, 3, emote.kind, 0, 0 };
            slot++;
        }
    }
    /* kin: follower, people's companions, wild kin */
    const KinActor *kins[1 + NPC_COUNT + WILD_MAX];
    int nk = 0;
    if (follower_active() && starter_preview < 0) kins[nk++] = &follower;
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].map == cur_map && npc_kin[i].shown) kins[nk++] = &npc_kin[i];
    for (int i = 0; i < WILD_MAX; i++)
        if (wild[i].active) kins[nk++] = &wild[i].k;
    u16 bank_key[KIN_BANK_COUNT];
    int banks = 0, kslot = 0;
    for (int i = 0; i < nk && kslot < 16 && n < 44; i++) {
        const KinActor *k = kins[i];
        int wx = k->a.x * 16 + k->a.ox, wy = k->a.y * 16 + k->a.oy;
        if (wx - cam_x < -24 || wx - cam_x > SCREEN_WIDTH + 8 || wy - cam_y < -8 ||
            wy - cam_y > SCREEN_HEIGHT + 24)
            continue;
        u16 key = (u16)(k->species | (k->lustrous << 8));
        int bank = -1;
        for (int b = 0; b < banks; b++)
            if (bank_key[b] == key) bank = b;
        if (bank < 0) {
            if (banks >= KIN_BANK_COUNT) continue;
            bank = banks;
            bank_key[banks++] = key;
            load_mon_pal(KIN_BANK_FIRST + bank, k->species, k->lustrous);
        }
        copy32(VRAM_OBJ_TILES + OT_OWKIN(kslot) * 8, kin_frame_gfx(k->species, kin_frame(k)), 16 * 8);
        list[n++] = (FieldSprite){ wy, wx, 1, OT_OWKIN(kslot) | (actor_lift(&k->a) << 16),
                                   KIN_BANK_FIRST + bank, k->a.facing == DIR_RIGHT };
        if (emote.timer > 0 && emote.npc <= -2 && k == &wild[-2 - emote.npc].k)
            list[n++] = (FieldSprite){ wy + 1, wx, 3, emote.kind, 0, 0 };
        kslot++;
    }
    for (int i = 0; i < ITEM_BALL_COUNT && n < 46; i++) {
        if (ITEM_BALLS[i].map != cur_map || item_taken(i)) continue;
        list[n++] = (FieldSprite){ ITEM_BALLS[i].y * 16 - 1, ITEM_BALLS[i].x * 16, 2, 0, 0, 0 };
    }
    /* Sort front-to-back: larger y is closer to the camera. */
    for (int i = 1; i < n; i++)
        for (int j = i; j > 0 && list[j].y > list[j - 1].y; j--) {
            FieldSprite t = list[j];
            list[j] = list[j - 1];
            list[j - 1] = t;
        }
    for (int i = 0; i < n; i++) {
        const FieldSprite *s = &list[i];
        int sx = s->x - cam_x, sy = s->y - cam_y;
        switch (s->kind) {
        case 0:
            spr_push(sx, sy - 16 - (s->a >> 16), s->a & 0xFFFF, TALL16x32, s->b, 2,
                     s->flip ? ATTR1_HFLIP : 0);
            break;
        case 1:
            spr_push(sx - 8, sy - 16 - (s->a >> 16), s->a & 0xFFFF, SQ32, s->b, 2,
                     s->flip ? ATTR1_HFLIP : 0);
            break;
        case 2:
            spr_push(sx, sy + 1, OT_ITEM_BALL, SQ16, OBANK_ITEM_BALL, 2, 0);
            break;
        case 3:
            spr_push(sx, sy - 34, OT_EMOTE + s->a * 4, SQ16, OBANK_EMOTE, 1, 0);
            break;
        }
    }
    if (emote.timer > 0 && emote.npc == -1)
        spr_push(player.x * 16 + player.ox - cam_x, player.y * 16 + player.oy - cam_y - 34,
                 OT_EMOTE + emote.kind * 4, SQ16, OBANK_EMOTE, 1, 0);
    draw_weather();
}

static void field_load_objects(void)
{
    copy32(VRAM_OBJ_TILES + OT_ITEM_BALL * 8, item_ball_gfx, 4 * 8);
    load_pal(obj_palette + OBANK_ITEM_BALL * 16, item_ball_palette);
    load_pal(obj_palette + OBANK_PLAYER * 16, char_palettes[CHR_PLAYER]);
    copy32(VRAM_OBJ_TILES + OT_EMOTE * 8, emote_gfx, EMOTE_COUNT * 4 * 8);
    load_pal(obj_palette + OBANK_EMOTE * 16, emote_palette);
}

/* ---------------- movement ---------------- */

static int player_turn_timer;
static int steps_since_battle;
static void on_player_step(void);
static int field_try_interact(void);

/* Advance an actor's walk; returns 1 on the frame it reaches its cell. */
static int actor_step(Actor *a, int speed)
{
    if (!a->moving) return 0;
    a->anim++;
    if (a->hop) a->hop--;
    int dx = DIR_DX[a->facing], dy = DIR_DY[a->facing];
    /* offsets count from -16 (just left the previous cell) up to 0 */
    a->ox = (s8)(a->ox + dx * speed);
    a->oy = (s8)(a->oy + dy * speed);
    if ((dx && a->ox * dx >= 0) || (dy && a->oy * dy >= 0)) {
        a->ox = a->oy = 0;
        a->moving = 0;
        a->hop = 0;
        return 1;
    }
    return 0;
}

static void actor_start_move(Actor *a, int dir)
{
    a->facing = (u8)dir;
    a->x = (s16)(a->x + DIR_DX[dir]);
    a->y = (s16)(a->y + DIR_DY[dir]);
    a->ox = (s8)(-DIR_DX[dir] * 16);
    a->oy = (s8)(-DIR_DY[dir] * 16);
    a->moving = 1;
}

/* Two cells at once (ledge hop). */
static void actor_start_hop(Actor *a, int dir)
{
    a->facing = (u8)dir;
    a->x = (s16)(a->x + DIR_DX[dir] * 2);
    a->y = (s16)(a->y + DIR_DY[dir] * 2);
    a->ox = (s8)(-DIR_DX[dir] * 32);
    a->oy = (s8)(-DIR_DY[dir] * 32);
    a->moving = 1;
    a->hop = 16;
}

/* Direction from one cell to an adjacent one (or -1). */
static int dir_to(int x0, int y0, int x1, int y1)
{
    for (int d = 0; d < 4; d++)
        if (x0 + DIR_DX[d] == x1 && y0 + DIR_DY[d] == y1) return d;
    return -1;
}

/* A kin that walks to where its person just was. */
static void kin_follow(KinActor *k, int tx, int ty, int hop)
{
    if (!k->shown) return;
    if (hop) {
        int d = dir_to(k->a.x, k->a.y, tx, ty);
        if (d >= 0) {
            actor_start_move(&k->a, d);
            k->a.hop = 16;
            return;
        }
    }
    if (k->a.x == tx && k->a.y == ty) return;
    int d = dir_to(k->a.x, k->a.y, tx, ty);
    if (d < 0) {
        /* two cells straight ahead: its person hopped a ledge, so hop too */
        for (int dd = 0; dd < 4; dd++)
            if (k->a.x + DIR_DX[dd] * 2 == tx && k->a.y + DIR_DY[dd] * 2 == ty) {
                actor_start_hop(&k->a, dd);
                return;
            }
    }
    if (d < 0) { /* too far behind (after a warp): pop into place */
        k->a.x = (s16)tx;
        k->a.y = (s16)ty;
        k->a.ox = k->a.oy = 0;
        k->a.moving = 0;
        return;
    }
    actor_start_move(&k->a, d);
}

static int follower_active(void)
{
    return opt.follower && follower.shown && party_count > 0;
}

/* The lead kin (first one still awake) walks behind the player. */
static void follower_sync(void)
{
    int lead = party_first_healthy();
    if (lead < 0 || !party_count) {
        follower.shown = 0;
        return;
    }
    follower.species = party[lead].species;
    follower.lustrous = (party[lead].flags & MF_LUSTROUS) != 0;
    follower.shown = 1;
}

/* Put the follower behind the player (after warps). */
static void follower_reset(void)
{
    follower_sync();
    int bx = player.x + DIR_DX[DIR_BACK[player.facing]], by = player.y + DIR_DY[DIR_BACK[player.facing]];
    if (bx < 0 || by < 0 || bx >= map_w || by >= map_h || (cell_attr(bx, by) & A_SOLID)) {
        bx = player.x;
        by = player.y;
    }
    kin_place(&follower, follower.species, follower.lustrous, bx, by, player.facing);
    follower_sync();
}

static void npcs_update(void)
{
    for (int i = 0; i < NPC_COUNT; i++) {
        if (NPCS[i].map != cur_map) continue;
        Actor *a = &npc_state[i];
        KinActor *k = &npc_kin[i];
        if (k->shown && k->a.moving) actor_step(&k->a, 1);
        if (a->moving) {
            actor_step(a, 1);
            continue;
        }
        if (NPCS[i].behavior == BEH_STILL || a->timer-- > 0) continue;
        a->timer = (u16)(70 + rng_range(120));
        int dir = (int)rng_range(4);
        if (NPCS[i].behavior == BEH_LOOK) {
            a->facing = (u8)dir;
            continue;
        }
        if (NPCS[i].behavior == BEH_PACE_H) dir = (a->x <= NPCS[i].x - 2) ? DIR_RIGHT : (a->x >= NPCS[i].x + 2) ? DIR_LEFT : (rng_range(2) ? DIR_LEFT : DIR_RIGHT);
        if (NPCS[i].behavior == BEH_PACE_V) dir = (a->y <= NPCS[i].y - 2) ? DIR_DOWN : (a->y >= NPCS[i].y + 2) ? DIR_UP : (rng_range(2) ? DIR_UP : DIR_DOWN);
        int nx = a->x + DIR_DX[dir], ny = a->y + DIR_DY[dir];
        a->facing = (u8)dir;
        if (absi(nx - NPCS[i].x) > 2 || absi(ny - NPCS[i].y) > 2) continue;
        if (nx == player.x && ny == player.y) continue;
        if (follower_active() && nx == follower.a.x && ny == follower.a.y) continue;
        if (k->shown && nx == k->a.x && ny == k->a.y) {
            /* swap places with their own kin */
            int ox = a->x, oy = a->y;
            actor_start_move(a, dir);
            kin_follow(k, ox, oy, 0);
            continue;
        }
        if (!cell_walkable(nx, ny)) continue;
        if (cell_attr(nx, ny) & (A_GRASS | A_EXIT)) continue;
        int ox = a->x, oy = a->y;
        actor_start_move(a, dir);
        if (k->shown) kin_follow(k, ox, oy, 0);
    }
}

static int held_dir(void)
{
    if (key_down(KEY_UP)) return DIR_UP;
    if (key_down(KEY_DOWN)) return DIR_DOWN;
    if (key_down(KEY_LEFT)) return DIR_LEFT;
    if (key_down(KEY_RIGHT)) return DIR_RIGHT;
    return -1;
}

static void field_begin_warp(int dest, int x, int y, int facing);
static void wild_touch(int slot);
static void edge_blocked(void);

/* Walking off the edge of a map into a linked neighbour. */
static int try_edge_link(int dir, int nx, int ny)
{
    static const u8 LINK_FOR_DIR[4] = { LINK_S, LINK_N, LINK_W, LINK_E };
    const MapDef *m = &MAPS[cur_map];
    int l = LINK_FOR_DIR[dir];
    if (m->link[l] == MAP_NONE) return 0;
    if (!(story_flags & FLAG_STARTER)) {
        edge_blocked();
        return 1;
    }
    const MapDef *d = &MAPS[m->link[l]];
    int x = nx, y = ny;
    switch (l) {
    case LINK_N: y = d->h - 1; x = nx + m->link_off[l]; break;
    case LINK_S: y = 0; x = nx + m->link_off[l]; break;
    case LINK_W: x = d->w - 1; y = ny + m->link_off[l]; break;
    default: x = 0; y = ny + m->link_off[l]; break;
    }
    field_begin_warp(m->link[l], clampi(x, 0, d->w - 1), clampi(y, 0, d->h - 1), dir);
    return 1;
}

/* Returns 1 when the player started a step or triggered something. */
static int player_try_move(int dir)
{
    int nx = player.x + DIR_DX[dir], ny = player.y + DIR_DY[dir];
    player.facing = (u8)dir;
    if (map_tileset != TS_INTERIOR && dir == DIR_UP && (cell_attr(nx, ny) & A_DOOR)) {
        int w = warp_at(cur_map, nx, ny);
        if (w >= 0) {
            sfx_play(SFX_DOOR);
            field_begin_warp(WARPS[w].dest, WARPS[w].dx, WARPS[w].dy, DIR_UP);
            return 1;
        }
    }
    if (map_tileset == TS_INTERIOR && dir == DIR_DOWN &&
        (cell_attr(player.x, player.y) & A_EXIT)) {
        for (int i = 0; i < WARP_COUNT; i++)
            if (WARPS[i].dest == cur_map) {
                sfx_play(SFX_DOOR);
                field_begin_warp(WARPS[i].map, WARPS[i].x, WARPS[i].y + 1, DIR_DOWN);
                return 1;
            }
    }
    if ((nx < 0 || ny < 0 || nx >= map_w || ny >= map_h) && try_edge_link(dir, nx, ny)) return 1;
    int w = wild_at(nx, ny);
    if (w >= 0) {
        wild_touch(w);
        return 1;
    }
    /* ledges: hop down over them */
    if (dir == DIR_DOWN && nx >= 0 && ny >= 0 && nx < map_w && ny < map_h &&
        (cell_attr(nx, ny) & A_LEDGE) && cell_walkable(nx, ny + 1)) {
        int ox = player.x, oy = player.y;
        actor_start_hop(&player, dir);
        sfx_play(SFX_LEDGE);
        if (follower_active()) kin_follow(&follower, ox, oy, 0);
        actor_step(&player, 2);
        return 1;
    }
    int swap = follower_active() && follower.a.x == nx && follower.a.y == ny && !follower.a.moving &&
               !(cell_attr(nx, ny) & (A_SOLID | A_LEDGE));
    if (!swap && !cell_walkable(nx, ny)) {
        if (!player.anim) sfx_play(SFX_BUMP);
        player.anim++; /* walk in place against obstacles */
        return 0;
    }
    int ox = player.x, oy = player.y;
    actor_start_move(&player, dir);
    if (follower_active()) kin_follow(&follower, ox, oy, 0);
    /* advance on the same frame so consecutive steps flow without a stall */
    int speed = key_down(KEY_B) ? 2 : 1;
    actor_step(&player, speed);
    if (follower_active()) actor_step(&follower.a, speed);
    return 1;
}

/* One frame of overworld control. */
static int field_player_update(void)
{
    if (player.moving) {
        int speed = player.hop ? 2 : key_down(KEY_B) ? 2 : 1;
        if (follower_active() && follower.a.moving) actor_step(&follower.a, speed);
        if (actor_step(&player, speed)) {
            on_player_step();
            return 1;
        }
        return 0;
    }
    if (follower_active() && follower.a.moving) actor_step(&follower.a, 2);
    if (key_hit(KEY_A) && field_try_interact()) return 1;
    int dir = held_dir();
    if (dir < 0) {
        player_turn_timer = 0;
        player.anim = 0;
        return 0;
    }
    if (dir != player.facing && player_turn_timer == 0 && !key_down(KEY_B)) {
        /* a tap turns in place; holding the direction starts walking */
        player.facing = (u8)dir;
        player_turn_timer = 6;
        return 0;
    }
    if (player_turn_timer > 1) {
        player_turn_timer--;
        return 0;
    }
    return player_try_move(dir);
}

/* ---------------- wild kin ---------------- */

/* Level-grow a species as far as the level allows (wild/warden teams). */
static int species_for_level(int sp, int level)
{
    for (int guard = 0; guard < 3; guard++) {
        const Species *s = &SPECIES[sp];
        if (s->evo_kind != EVO_LEVEL || level < s->evo_param + 3) break;
        sp = s->evo_into;
    }
    return sp;
}

static int party_max_level(void);

static Monster roll_wild(int zone)
{
    const WildZone *z = &WILD_ZONES[zone];
    int total = 0;
    for (int i = 0; i < z->count; i++) total += z->slots[i].weight;
    int r = (int)rng_range((unsigned)total);
    const WildSlot *s = &z->slots[0];
    for (int i = 0; i < z->count; i++) {
        if (r < z->slots[i].weight) {
            s = &z->slots[i];
            break;
        }
        r -= z->slots[i].weight;
    }
    int level = s->min_level + (int)rng_range((unsigned)(s->max_level - s->min_level + 1));
    /* kin keep up a little with strong teams, so routes stay worth a bout */
    int over = party_max_level() - (s->max_level + 6);
    if (over > 0) level += over / 2;
    level = clampi(level, 2, 70);
    Monster m = monster_make(species_for_level(s->species, level), level);
    m.met_map = (u8)cur_map;
    return m;
}

static int wild_cell_ok(int x, int y)
{
    return x >= 0 && y >= 0 && x < map_w && y < map_h && (cell_attr(x, y) & A_GRASS) &&
           cell_walkable(x, y) && !(x == player.x && y == player.y) &&
           !(follower_active() && x == follower.a.x && y == follower.a.y);
}

static void wild_spawn(void)
{
    const MapDef *m = &MAPS[cur_map];
    if (m->zone == ZONE_NONE || !(story_flags & FLAG_STARTER)) return;
    const WildZone *z = &WILD_ZONES[m->zone];
    int active = 0, slot = -1;
    for (int i = 0; i < WILD_MAX; i++) {
        if (wild[i].active) active++;
        else if (slot < 0) slot = i;
    }
    if (active >= z->max_active || slot < 0) return;
    for (int tries = 0; tries < 12; tries++) {
        int x = player.x - 9 + (int)rng_range(19), y = player.y - 7 + (int)rng_range(15);
        if (absi(x - player.x) + absi(y - player.y) < 4) continue;
        if (!wild_cell_ok(x, y)) continue;
        wild[slot].mon = roll_wild(m->zone);
        wild[slot].active = 1;
        wild[slot].brimming = rng_range(100) < 45;
        wild[slot].noticed = 0;
        wild[slot].life = (u16)(1200 + rng_range(900));
        wild[slot].think = (u16)(20 + rng_range(60));
        kin_place(&wild[slot].k, wild[slot].mon.species, (wild[slot].mon.flags & MF_LUSTROUS) != 0,
                  x, y, (int)rng_range(4));
        return;
    }
}

static int field_busy(void);

static void wild_update(void)
{
    if (field_busy()) return;
    if (--wild_spawn_timer <= 0) {
        wild_spawn_timer = 45 + (int)rng_range(60);
        wild_spawn();
    }
    for (int i = 0; i < WILD_MAX; i++) {
        if (!wild[i].active) continue;
        KinActor *k = &wild[i].k;
        if (k->a.moving) {
            if (actor_step(&k->a, 1) && !player.moving &&
                absi(k->a.x - player.x) + absi(k->a.y - player.y) == 1 && wild[i].brimming &&
                !hush_steps) {
                k->a.facing = (u8)dir_to(k->a.x, k->a.y, player.x, player.y);
                wild_touch(i);
                return;
            }
            continue;
        }
        int dist = absi(k->a.x - player.x) + absi(k->a.y - player.y);
        if (wild[i].life) wild[i].life--;
        if ((!wild[i].life && dist > 6) || dist > 16) {
            wild[i].active = 0;
            continue;
        }
        if (wild[i].think) {
            wild[i].think--;
            continue;
        }
        int chase = wild[i].brimming && !hush_steps && dist <= 4;
        if (chase && !wild[i].noticed) {
            /* it spots you: a "!" and a moment's pause before it charges */
            wild[i].noticed = 1;
            field_emote(-2 - i, EMOTE_EXCLAIM, 30);
            sfx_play(SFX_RUSTLE);
            wild[i].think = 24;
            continue;
        }
        wild[i].think = (u16)(chase ? 14 : 30 + rng_range(70));
        int dir;
        if (chase) {
            int dx = player.x - k->a.x, dy = player.y - k->a.y;
            if (dist == 1) {
                k->a.facing = (u8)dir_to(k->a.x, k->a.y, player.x, player.y);
                if (!player.moving) {
                    wild_touch(i);
                    return;
                }
                continue;
            }
            dir = absi(dx) >= absi(dy) ? (dx < 0 ? DIR_LEFT : DIR_RIGHT) : (dy < 0 ? DIR_UP : DIR_DOWN);
        } else {
            dir = (int)rng_range(4);
        }
        int nx = k->a.x + DIR_DX[dir], ny = k->a.y + DIR_DY[dir];
        k->a.facing = (u8)dir;
        int ok = chase ? (cell_walkable(nx, ny) && !(nx == player.x && ny == player.y) &&
                          !(follower_active() && nx == follower.a.x && ny == follower.a.y))
                       : wild_cell_ok(nx, ny);
        if (ok) actor_start_move(&k->a, dir);
    }
}

/* ---------------- warps & transitions ---------------- */

static struct {
    int active, timer, dest, x, y, facing;
} warp;

static void field_begin_warp(int dest, int x, int y, int facing)
{
    warp.active = 1;
    warp.timer = 0;
    warp.dest = dest;
    warp.x = x;
    warp.y = y;
    warp.facing = facing;
}

static void field_on_enter(void);

static void field_enter_map(int map, int x, int y, int facing)
{
    map_load(map);
    player.x = (s16)x;
    player.y = (s16)y;
    player.ox = player.oy = 0;
    player.moving = 0;
    player.hop = 0;
    player.facing = (u8)facing;
    field_load_tileset();
    follower_reset();
    field_update_camera();
    field_on_enter();
}

/* Returns 1 while a fade is running (input is frozen). */
static int field_warp_update(void)
{
    if (!warp.active) return 0;
    warp.timer++;
    if (warp.timer <= 8) {
        set_brightness(-warp.timer * 2);
    } else if (warp.timer == 9) {
        field_enter_map(warp.dest, warp.x, warp.y, warp.facing);
    } else if (warp.timer <= 18) {
        set_brightness(-(18 - warp.timer) * 2);
    } else {
        set_brightness(0);
        warp.active = 0;
    }
    return 1;
}
