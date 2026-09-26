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

/* Special cell values beyond metatile ids (A_* attributes and the tileset
 * table TILESETS[] come from gfx_field.h). */
#define CELL_PATH  0xFFF0
#define CELL_WATER 0xFFF1

typedef struct { u16 base; u8 w, h, x, y; } Stamp;
#define STAMP(TS, NAME, X, Y) { MT_##TS##_##NAME, MT_##TS##_##NAME##_W, MT_##TS##_##NAME##_H, X, Y }

typedef struct { u16 kind; u8 x, y, flags; } DecorPlace;   /* kind: DK_* (more than 255) */
enum { DF_HFLIP = 1 };

enum { LINK_N, LINK_S, LINK_W, LINK_E };
#define MAP_NONE 0xFF
#define ZONE_NONE 0     /* WILD_ZONES[0] is the empty zone */

/* Map flags (docs/EXPANSION.md 10.2). */
enum {
    MF_OUTDOOR = 1, MF_HEAL = 2, MF_DARK = 4, MF_NOFLY = 8, MF_TOWN = 16, MF_ASH = 32,
    MF_SNOW = 64, MF_RAIN = 128, MF_NIGHTLESS = 256, MF_DEBUG = 512,
};

/* Elevation features over a map's height layer (elev.c, docs/ELEVATION.md). */
typedef struct { u8 kind, x, y, w, h; } ElevFeat;
enum { EF_BRIDGE_H = 1, EF_BRIDGE_V, EF_TUNNEL, EF_HIDDEN };

/* Map objects: puzzle pieces, berry patches, ferries, legends, chests...
 * Their behaviour lives in travel.c / farm.c; kind values are OBJ_*. */
typedef struct { u8 kind, x, y, arg; } MapObj;
enum {
    OBJ_NONE, OBJ_BOULDER, OBJ_PLATE, OBJ_GATE, OBJ_SWITCH, OBJ_BARRIER, OBJ_PAD,
    OBJ_BERRY, OBJ_FERRY, OBJ_LEGEND, OBJ_CHEST, OBJ_LADDER, OBJ_KIND_COUNT
};

typedef struct {
    u8 w, h, tileset, scene;       /* scene: battle backdrop (SC_*) */
    const char *const *rows;
    const Stamp *stamps;
    u8 stamp_count;
    const DecorPlace *decor;
    u8 decor_count;
    const char *name;
    u8 zone;                       /* WILD_ZONES index (ZONE_NONE = 0: no wild kin) */
    u16 flags;                     /* MF_* */
    u8 link[4];                    /* neighbour map per edge (LINK_*), MAP_NONE */
    s8 link_off[4];                /* coordinate shift into the neighbour */
    /* optional (trailing, zero by default) */
    const MapObj *objs;
    u8 obj_count;
    u8 water_zone;                 /* WILD_ZONES index for kin on water (surf), 0 = none */
    const u16 *cells, *ground;     /* pre-decoded cells (generated viewer maps) or 0 */
    u8 song;                       /* SONG_* for this map, 0 = automatic (music.c) */
    const char *const *elev;       /* height layer, one char per cell, or 0 (elev.c) */
    const ElevFeat *feats;         /* bridges, tunnels, hidden passages */
    u8 feat_count;
} MapDef;

/* Called at the end of every map load (music.c defines it; see script.c). */
static void music_map_changed(int map);

typedef struct { u8 map, x, y, dest, dx, dy; } Warp;

enum { BEH_STILL, BEH_LOOK, BEH_WANDER, BEH_PACE_H, BEH_PACE_V };
#define NO_TRAINER 0xFFFF
#define NO_KIN 0xFF
#define NO_LORE 0xFF

typedef struct {
    u8 map, x, y, chr, facing, behavior;
    u8 script;          /* SCR_* */
    u8 lore;            /* LSRC_* the person reveals, or NO_LORE */
    u16 trainer;        /* TRAINERS index or NO_TRAINER */
    u8 sight;           /* cells a warden can see */
    u8 kin;             /* species walking beside them, or NO_KIN */
    const char *name;
    const char *text;   /* what they say (after the bout, for wardens) */
} NpcDef;

#define TRAINER_TEAM_MAX 6
typedef struct {
    const char *name;   /* "WARDEN ROSA" */
    u8 count;
    u8 species[TRAINER_TEAM_MAX], level[TRAINER_TEAM_MAX];
    u16 prize;
    const char *intro;  /* said when they spot you */
    const char *lose;   /* said when you beat them */
} TrainerDef;

typedef struct { u8 map, x, y; const char *text; } Sign;
typedef struct { u8 map, x, y, item, qty; } ItemBall;

enum { WHEN_ANY, WHEN_DAY, WHEN_NIGHT };
typedef struct { u8 species, weight, min_level, max_level, when; } WildSlot;
typedef struct { const WildSlot *slots; u8 count, max_active; const char *name; } WildZone;

#define NSTAMP(a) ((u8)(sizeof(a) / sizeof(a[0])))
#define NROWS(a) ((u8)(sizeof(a) / sizeof(a[0])))

#include "world/world.h"

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
    u8 level;       /* elevation the actor stands on (elev.c) */
} Actor;

typedef struct { Actor a; u8 species, lustrous, shown; } KinActor;

static Actor npc_state[NPC_COUNT];
static KinActor npc_kin[NPC_COUNT];
static KinActor follower;

#define WILD_MAX 5
static struct {
    KinActor k;
    Monster mon;
    u8 active, brimming, noticed, water;   /* water: swims (surf zone) */
    u16 life, think;
} wild[WILD_MAX] EWRAM_BSS;
static int wild_spawn_timer;
static int wild_battle_slot = -1;

static int cur_map;
static Actor player;
/* Story flags, picked-up satchels and beaten wardens: bit arrays (the ids
 * come from each region's flag_ids.inc / satchels.inc / trainer_ids.inc). */
#define FLAG_BYTES 64
#define ITEM_FLAG_BYTES 64
#define TRAINER_FLAG_BYTES 64
static u8 story_bits[FLAG_BYTES];
static u8 item_bits[ITEM_FLAG_BYTES];
static u8 trainer_bits[TRAINER_FLAG_BYTES];
typedef char FlagsFit[FLAG_COUNT <= FLAG_BYTES * 8 ? 1 : -1];

static int bit_get(const u8 *bits, int i) { return i >= 0 && ((bits[i >> 3] >> (i & 7)) & 1); }
static void bit_set(u8 *bits, int i) { if (i >= 0) bits[i >> 3] |= (u8)(1u << (i & 7)); }
static void bit_clear(u8 *bits, int i) { if (i >= 0) bits[i >> 3] &= (u8)~(1u << (i & 7)); }

static int flag(int f) { return bit_get(story_bits, f); }
static void flag_set(int f) { bit_set(story_bits, f); }
__attribute__((unused)) static void flag_clear(int f) { bit_clear(story_bits, f); }
__attribute__((unused)) static void flags_story_clear(void)
{
    for (int i = 0; i < FLAG_BYTES; i++) story_bits[i] = 0;
}
static void flags_reset(void)
{
    for (int i = 0; i < FLAG_BYTES; i++) story_bits[i] = 0;
    for (int i = 0; i < ITEM_FLAG_BYTES; i++) item_bits[i] = 0;
    for (int i = 0; i < TRAINER_FLAG_BYTES; i++) trainer_bits[i] = 0;
}

static int item_taken(int i) { return bit_get(item_bits, i); }
static void item_take(int i) { bit_set(item_bits, i); }
static int trainer_beaten(int t) { return bit_get(trainer_bits, t); }
static void trainer_mark_beaten(int t) { bit_set(trainer_bits, t); }

#define MAP_MAX_W 64
#define MAP_MAX_H 64
EWRAM_BSS static u16 map_cells[MAP_MAX_W * MAP_MAX_H];
EWRAM_BSS static u16 map_ground[MAP_MAX_W * MAP_MAX_H];  /* ground under overlay cells (trees) */
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

static const TilesetDef *tset(void) { return &TILESETS[map_tileset]; }

static const LegendEntry *legend_for(const TilesetDef *t, char c)
{
    const LegendEntry *e = (c >= 32 && c < 127) ? &t->legend[c - 32] : 0;
    if (!e || !e->kind) e = &t->legend[t->legend_default - 32];
    return e;
}

/* Metatile for a legend entry at (x, y): variants by cell hash % 16. */
static u16 legend_pick(const LegendEntry *e, int x, int y)
{
    switch (e->kind) {
    case LG_PATH: return CELL_PATH;
    case LG_WATER: return CELL_WATER;
    case LG_VARIANT: {
        unsigned h = cell_hash(x, y) % 16u, acc = 0;
        for (int i = 0; i < e->n; i++) {
            acc += e->w[i];
            if (h < acc) return e->id[i];
        }
        return e->id[e->n - 1];
    }
    default: return e->id[0];
    }
}

static int legend_is_ground(const TilesetDef *t, const LegendEntry *e)
{
    if (e->kind != LG_SIMPLE && e->kind != LG_VARIANT) return 0;
    for (int i = 0; i < e->n; i++)
        if (!(t->mflags[e->id[i]] & MTF_GROUND)) return 0;
    return 1;
}

static int is_overlay(u16 v)
{
    return v < CELL_PATH && (tset()->mflags[v] & MTF_OVERLAY);
}

/* Ground drawn under an overlay cell (a tree): the nearest ground character
 * below, above, left or right (up to 8 cells), picked at the tree's own
 * position so textures stay aligned. tools/fieldmap.py does the same. */
#define GROUND_SEARCH 8
static u16 map_infer_ground(const MapDef *m, int x, int y)
{
    const TilesetDef *t = &TILESETS[m->tileset];
    for (int d = 1; d <= GROUND_SEARCH; d++) {
        const s8 nx[4] = { 0, 0, -1, 1 }, ny[4] = { 1, -1, 0, 0 };
        for (int k = 0; k < 4; k++) {
            int cx = x + nx[k] * d, cy = y + ny[k] * d;
            if (cx < 0 || cy < 0 || cx >= m->w || cy >= m->h) continue;
            const LegendEntry *e = legend_for(t, m->rows[cy][cx]);
            if (legend_is_ground(t, e)) return legend_pick(e, x, y);
        }
    }
    return t->ground;
}

#include "elev.c"

static void map_decode(int id)
{
    const MapDef *m = &MAPS[id];
    const TilesetDef *t = &TILESETS[m->tileset];
    for (int y = 0; y < m->h; y++)
        for (int x = 0; x < m->w; x++) {
            int i = y * m->w + x;
            u16 v = m->cells ? m->cells[i] : legend_pick(legend_for(t, m->rows[y][x]), x, y);
            map_cells[i] = v;
            map_decor[i] = 0;
            map_ground[i] = 0;
            if (v < CELL_PATH && (t->mflags[v] & MTF_OVERLAY))
                map_ground[i] = m->ground ? m->ground[i] : map_infer_ground(m, x, y);
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
    elev_decode(m);
}

static u16 map_cell(int x, int y)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h) return tset()->oob;
    return map_cells[y * map_w + x];
}

/* Ground under an overlay cell (the tileset's default outside the map). */
static u16 map_ground_at(int x, int y)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h) return tset()->ground;
    return map_ground[y * map_w + x];
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

static int terrain_attr(int tileset, int v)
{
    if (v == CELL_PATH) return 0;
    if (v == CELL_WATER) return A_SOLID | A_WATER;
    if (v >= TILESETS[tileset].meta_count) return A_SOLID;
    return TILESETS[tileset].attr[v];
}

static int is_door_cell(int v)
{
    return v < CELL_PATH && (terrain_attr(map_tileset, v) & A_DOOR);
}

static int travel_attr(int x, int y, int a);
static int farm_cell_attr(int x, int y, int a);      /* farm.c: trees, sprinklers, workers, berry bushes */

/* Terrain and decor only (no map objects). */
static int cell_attr_raw(int x, int y)
{
    int a = terrain_attr(map_tileset, map_cell(x, y));
    int sub;
    const DecorDef *d;
    if (decor_at(x, y, &sub, &d)) {
        if (d->floor & (1u << sub)) a &= ~(A_SOLID | A_WATER | A_LEDGE);
        if (d->solid & (1u << sub)) a |= A_SOLID;
    }
    return elev_attr(x, y, a);
}

static int cell_attr(int x, int y)
{
    return farm_cell_attr(x, y, travel_attr(x, y, cell_attr_raw(x, y)));
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
    const u16 (*q)[5] = v == CELL_PATH ? tset()->path_q : tset()->water_q;
    static const s8 qdx[4] = { -1, 1, -1, 1 }, qdy[4] = { -1, -1, 1, 1 };
    for (int c = 0; c < 4; c++) {
        if (!q) {
            out[c] = 0;
            continue;
        }
        int vs = same_kind(v, x, y + qdy[c]);
        int hs = same_kind(v, x + qdx[c], y);
        int ds = same_kind(v, x + qdx[c], y + qdy[c]);
        int variant = vs && hs ? (ds ? 0 : 1) : (vs ? 2 : (hs ? 3 : 4));
        out[c] = q[c][variant];
    }
}

/* Resolve a decor entry (local tile + 1) against the kind's VRAM block. */
static u16 decor_entry(u16 e, int kind)
{
    if (!e) return 0;
    return (u16)((e & 0xFC00) | (decor_base[kind] + (e & 1023) - 1));
}

/* Hook for cells whose look changes at run time (farm soil and crops,
 * berry patches, puzzle pieces drawn into the map). Return 1 after filling
 * the three layers yourself. See farm.c / travel.c. */
static int dyn_cell(int mx, int my, u16 bottom[4], u16 mid[4], u16 top[4]);

static void render_cell(int mx, int my)
{
    int rx = mx & 15, ry = my & 15;
    if (ring_x[ry][rx] == mx && ring_y[ry][rx] == my) return;
    ring_x[ry][rx] = (s16)mx;
    ring_y[ry][rx] = (s16)my;
    const TilesetDef *t = tset();
    u16 bottom[4], top[4], mid[4] = { 0, 0, 0, 0 };
    int v = map_cell(mx, my);
    if (v == CELL_PATH || v == CELL_WATER) {
        autotile_quads(v, mx, my, bottom);
        for (int i = 0; i < 4; i++) top[i] = 0;
    } else if (t->mflags[v] & MTF_OVERLAY) {
        /* a tree: ground beneath on BG0, trunk on BG2, crown on BG3 */
        int g = map_ground_at(mx, my);
        for (int i = 0; i < 4; i++) {
            bottom[i] = t->meta_bottom[g][i];
            mid[i] = t->meta_bottom[v][i];
            top[i] = t->meta_top[v][i];
        }
    } else {
        for (int i = 0; i < 4; i++) {
            bottom[i] = t->meta_bottom[v][i];
            top[i] = t->meta_top[v][i];
        }
    }
    elev_render_base(mx, my, mid);
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
    if (map_elevated) elev_render_cover(mx, my, bottom, mid, top);
    dyn_cell(mx, my, bottom, mid, top);
    u16 *b = VRAM_MAP(SB_FIELD_BOTTOM), *tp = VRAM_MAP(SB_FIELD_TOP), *m = VRAM_MAP(SB_PANEL);
    int idx = ry * 2 * 32 + rx * 2;
    static const u8 OFF[4] = { 0, 1, 32, 33 };
    for (int i = 0; i < 4; i++) {
        b[idx + OFF[i]] = bottom[i];
        m[idx + OFF[i]] = mid[i];
        tp[idx + OFF[i]] = top[i];
    }
}

/* Force a cell to be redrawn (after its look changed at run time). */
__attribute__((unused)) static void field_redraw_cell(int mx, int my)
{
    ring_x[my & 15][mx & 15] = -32768;
}

static int floor_div16(int v)
{
    return v >= 0 ? v >> 4 : -((15 - v) >> 4);
}

/* Write any newly visible cells; called in vblank. */
static void travel_dark_present(void);

static void field_render_view(void)
{
    travel_dark_present();
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
    return !(flag(FLAG_STORM_CALMED)) && (flag(FLAG_STARTER)) &&
           (MAPS[cur_map].flags & MF_OUTDOOR) && !(MAPS[cur_map].flags & MF_DEBUG);
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

/* Extra tint for the field palettes (time of day, the Ashen March...);
 * time.c owns it. Returns the colour unchanged when there is no tint. */
static u16 field_tint(u16 c);

/* The Ashen March haze and ash-fall (MF_ASH) until OSSUREX is answered:
 * world/grim/scripts.c. */
static int grim_ash_active(int map);
static u16 grim_ash_tint(u16 c);
static void grim_draw_ash(void);

static void field_load_palettes(void)
{
    const u16 (*pal)[16] = tset()->palettes;
    int storm = storm_active(), ash = grim_ash_active(cur_map);
    for (int b = 0; b < 8; b++)
        for (int i = 0; i < 16; i++) {
            u16 c = storm ? storm_tint(pal[b][i]) : pal[b][i];
            if (ash) c = grim_ash_tint(c);
            bg_palette[b * 16 + i] = field_tint(c);
        }
    u16 bd = tset()->backdrop;
    if (ash) bd = grim_ash_tint(bd);
    bg_palette[0] = field_tint(storm ? storm_tint(bd) : bd);
}

static void travel_load_gfx(void);

static void field_load_tileset(void)
{
    copy32(VRAM_SCENE_TILES, tset()->tiles, (unsigned)tset()->tile_count * 8);
    decor_tiles_used = tset()->tile_count;
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
    travel_load_gfx();
}

/* Tile-data swaps for rippling water, swaying flowers and animated decor. */
static void field_animate_tiles(void)
{
    field_anim_frame++;
    const TilesetDef *t = tset();
    for (int i = 0; i < t->anim_count; i++) {
        const TileAnim *a = &t->anims[i];
        if (!a->period || field_anim_frame % a->period) continue;
        int f = field_anim_frame / a->period % a->frames;
        copy32(VRAM_SCENE_TILES + a->tile * 8, a->data + (unsigned)f * a->count * 8, (unsigned)a->count * 8);
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

static void travel_dark_off(void);

static void field_setup_bg(void)
{
    travel_dark_off();
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
        a->level = NPCS[i].map == cur_map ? (u8)elev_level_at(a->x, a->y, -1, a->facing) : 0;
        npc_kin[i].shown = 0;
        if (NPCS[i].kin != NO_KIN && NPCS[i].map == cur_map) {
            int bx = a->x + DIR_DX[DIR_BACK[a->facing]], by = a->y + DIR_DY[DIR_BACK[a->facing]];
            if (NPCS[i].facing == DIR_DOWN || NPCS[i].facing == DIR_UP) {
                bx = a->x + 1;
                by = a->y;
            }
            kin_place(&npc_kin[i], NPCS[i].kin, 0, bx, by, a->facing);
            npc_kin[i].a.level = (u8)elev_level_at(bx, by, a->level, a->facing);
        }
    }
}

static void wild_clear(void)
{
    for (int i = 0; i < WILD_MAX; i++) wild[i].active = wild[i].water = 0;
    wild_spawn_timer = 30;
}

static void travel_map_loaded(int map);
static void farm_map_loaded(void);

static void map_load(int id)
{
    cur_map = id;
    map_w = MAPS[id].w;
    map_h = MAPS[id].h;
    map_tileset = MAPS[id].tileset;
    map_decode(id);
    npcs_reset();
    wild_clear();
    travel_map_loaded(id);
    farm_map_loaded();
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

/* The same, for an actor on `level` stepping onto the ground (top = 0) or
 * onto a deck / tunnel top (top = 1, the terrain below does not matter).
 * Only people and kin on the same level are in the way. */
static int npc_at_lv(int x, int y, int level)
{
    for (int i = 0; i < NPC_COUNT; i++) {
        if (NPCS[i].map != cur_map) continue;
        const Actor *a = &npc_state[i];
        if (a->level != level) continue;
        if (a->x == x && a->y == y) return i;
        if (a->moving && a->x - DIR_DX[a->facing] == x && a->y - DIR_DY[a->facing] == y) return i;
    }
    return -1;
}

static int wild_at_lv(int x, int y, int level)
{
    int w = wild_at(x, y);
    return w >= 0 && wild[w].k.a.level == level ? w : -1;
}

static int cell_walkable_lv(int x, int y, int level, int top)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h) return 0;
    if (!top && (cell_attr(x, y) & (A_SOLID | A_LEDGE))) return 0;
    if (npc_at_lv(x, y, level) >= 0) return 0;
    int k = npc_kin_at(x, y);
    if (k >= 0 && npc_kin[k].a.level == level) return 0;
    if (wild_at_lv(x, y, level) >= 0) return 0;
    if (!top && item_ball_at(x, y) >= 0) return 0;
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

/* kind: 0 person, 1 kin, 2 satchel, 3 emote, 4 map object (tile a, bank b,
 * drawn `dy` below the sort line y, shape `shape`) */
typedef struct { int y, x, kind, a, b, flip, dy, shape, prio; } FieldSprite;   /* prio 0 = 2 */

/* traversal (travel.c) */
static int travel_player_entry(FieldSprite *e, int lift);
static int travel_player_lift(void);
static int travel_kin_actors(const KinActor **out, int max);
static int travel_push_sprites(FieldSprite *list, int n, int max);
static void travel_draw_floor(void);
static int farm_field_kin(const KinActor **out);  /* farm.c: workers on WILLOW ACRE (at most 4) */

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
    grim_draw_ash();
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
    FieldSprite list[80];
    int n = 0;
    int lift = actor_lift(&player) + travel_player_lift();
    if (travel_player_entry(&list[n], lift)) {
        list[n++].prio = elev_obj_prio(&player);
    } else {
        copy32(VRAM_OBJ_TILES + OT_PLAYER * 8, char_gfx[CHR_PLAYER][actor_frame(&player)], 64);
        list[n++] = (FieldSprite){ player.y * 16 + player.oy, player.x * 16 + player.ox, 0,
                                   OT_PLAYER | (lift << 16), OBANK_PLAYER, player.facing == DIR_RIGHT,
                                   0, 0, elev_obj_prio(&player) };
    }
    int slot = 0;
    for (int i = 0; i < NPC_COUNT && n < 40; i++) {
        if (NPCS[i].map != cur_map) continue;
        const Actor *a = &npc_state[i];
        int wx = a->x * 16 + a->ox, wy = a->y * 16 + a->oy;
        if (wx - cam_x >= -16 && wx - cam_x <= SCREEN_WIDTH && wy - cam_y >= -16 &&
            wy - cam_y <= SCREEN_HEIGHT + 16 && slot < 7) {
            copy32(VRAM_OBJ_TILES + OT_NPC(slot) * 8, char_gfx[NPCS[i].chr][actor_frame(a)], 64);
            load_pal(obj_palette + (OBANK_NPC + slot) * 16, char_palettes[NPCS[i].chr]);
            list[n++] = (FieldSprite){ wy, wx, 0, OT_NPC(slot), OBANK_NPC + slot, a->facing == DIR_RIGHT,
                                       0, 0, elev_obj_prio(a) };
            if (emote.npc == i && emote.timer > 0)
                list[n++] = (FieldSprite){ wy + 1, wx, 3, emote.kind, 0, 0 };
            slot++;
        }
    }
    /* kin: follower, people's companions, wild kin, farm workers */
    const KinActor *kins[1 + NPC_COUNT + WILD_MAX + 8 + 4];
    int nk = 0;
    if (follower_active() && starter_preview < 0) kins[nk++] = &follower;
    nk += travel_kin_actors(kins + nk, 8);
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].map == cur_map && npc_kin[i].shown) kins[nk++] = &npc_kin[i];
    for (int i = 0; i < WILD_MAX; i++)
        if (wild[i].active) kins[nk++] = &wild[i].k;
    nk += farm_field_kin(kins + nk);
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
                                   KIN_BANK_FIRST + bank, k->a.facing == DIR_RIGHT, 0, 0,
                                   elev_obj_prio(&k->a) };
        if (emote.timer > 0 && emote.npc <= -2 && k == &wild[-2 - emote.npc].k)
            list[n++] = (FieldSprite){ wy + 1, wx, 3, emote.kind, 0, 0 };
        kslot++;
    }
    for (int i = 0; i < ITEM_BALL_COUNT && n < 46; i++) {
        if (ITEM_BALLS[i].map != cur_map || item_taken(i)) continue;
        list[n++] = (FieldSprite){ ITEM_BALLS[i].y * 16 - 1, ITEM_BALLS[i].x * 16, 2, 0, 0, 0 };
    }
    n = travel_push_sprites(list, n, 78);
    /* Sort front-to-back: larger y is closer to the camera. */
    for (int i = 1; i < n; i++)
        for (int j = i; j > 0 && list[j].y > list[j - 1].y; j--) {
            FieldSprite t = list[j];
            list[j] = list[j - 1];
            list[j - 1] = t;
        }
    for (int i = 0; i < n; i++) {
        const FieldSprite *s = &list[i];
        int sx = s->x - cam_x, sy = s->y - cam_y, pr = s->prio ? s->prio : 2;
        switch (s->kind) {
        case 0:
            spr_push(sx, sy - 16 - (s->a >> 16), s->a & 0xFFFF, TALL16x32, s->b, pr,
                     s->flip ? ATTR1_HFLIP : 0);
            break;
        case 1:
            spr_push(sx - 8, sy - 16 - (s->a >> 16), s->a & 0xFFFF, SQ32, s->b, pr,
                     s->flip ? ATTR1_HFLIP : 0);
            break;
        case 2:
            spr_push(sx, sy + 1, OT_ITEM_BALL, SQ16, OBANK_ITEM_BALL, 2, 0);
            break;
        case 3:
            spr_push(sx, sy - 34, OT_EMOTE + s->a * 4, SQ16, OBANK_EMOTE, 1, 0);
            break;
        case 4:
            spr_push(sx, sy + s->dy, s->a, s->shape, s->b, 2, s->flip ? ATTR1_HFLIP : 0);
            break;
        }
    }
    if (emote.timer > 0 && emote.npc == -1)
        spr_push(player.x * 16 + player.ox - cam_x, player.y * 16 + player.oy - cam_y - 34,
                 OT_EMOTE + emote.kind * 4, SQ16, OBANK_EMOTE, 1, 0);
    travel_draw_floor();
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
static void kin_follow_move(KinActor *k, int tx, int ty, int hop);

static void kin_follow(KinActor *k, int tx, int ty, int hop)
{
    if (!k->shown) return;
    kin_follow_move(k, tx, ty, hop);
    if (map_elevated) k->a.level = (u8)elev_level_at(k->a.x, k->a.y, k->a.level, k->a.facing);
}

static void kin_follow_move(KinActor *k, int tx, int ty, int hop)
{
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

static int travel_hides_follower(void);

static int follower_active(void)
{
    return opt.follower && follower.shown && party_count > 0 && !travel_hides_follower();
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
    follower.a.level = (u8)elev_level_at(bx, by, player.level, player.facing);
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
        int nl, ek = elev_enter(a->x, a->y, a->level, dir, &nl);
        if (ek == ELEV_BLOCK || !cell_walkable_lv(nx, ny, nl, ek == ELEV_TOP)) continue;
        if (cell_attr(nx, ny) & (A_GRASS | A_EXIT)) continue;
        if (elev_hidden(nx, ny)) continue;
        int ox = a->x, oy = a->y;
        actor_start_move(a, dir);
        a->level = (u8)nl;
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
    if (!(flag(FLAG_STARTER))) {
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

static int travel_player_move(int dir, int nx, int ny);
static int travel_player_arrived(void);
static int travel_speed(int base);
static int travel_update(void);

/* Returns 1 when the player started a step or triggered something. */
static int player_try_move(int dir)
{
    int nx = player.x + DIR_DX[dir], ny = player.y + DIR_DY[dir];
    player.facing = (u8)dir;
    /* doors, cave mouths, ladders: a warp on the cell you step into */
    if (nx >= 0 && ny >= 0 && nx < map_w && ny < map_h && (cell_attr(nx, ny) & A_DOOR)) {
        int w = warp_at(cur_map, nx, ny);
        if (w >= 0) {
            sfx_play(SFX_DOOR);
            field_begin_warp(WARPS[w].dest, WARPS[w].dx, WARPS[w].dy, dir);
            return 1;
        }
    }
    /* exit mats: back out of the door that leads to this mat */
    if (dir == DIR_DOWN && (cell_attr(player.x, player.y) & A_EXIT)) {
        int best = -1, best_d = 1 << 30;
        for (int i = 0; i < WARP_COUNT; i++)
            if (WARPS[i].dest == cur_map) {
                int d = absi(WARPS[i].dx - player.x) + absi(WARPS[i].dy - player.y);
                if (d < best_d) {
                    best_d = d;
                    best = i;
                }
            }
        if (best >= 0) {
            sfx_play(SFX_DOOR);
            field_begin_warp(WARPS[best].map, WARPS[best].x, WARPS[best].y + 1, DIR_DOWN);
            return 1;
        }
    }
    if ((nx < 0 || ny < 0 || nx >= map_w || ny >= map_h) && try_edge_link(dir, nx, ny)) return 1;
    /* elevation: cliffs, stairs, decks (elev.c); nl = the level stepped onto */
    int nl, ek = elev_enter(player.x, player.y, player.level, dir, &nl);
    int w = ek != ELEV_BLOCK ? wild_at_lv(nx, ny, nl) : -1;
    if (w >= 0) {
        wild_touch(w);
        return 1;
    }
    /* surfing, boulders (travel.c) */
    if (ek == ELEV_FLOOR) {
        int t = travel_player_move(dir, nx, ny);
        if (t > 0) player.level = (u8)nl;
        if (t >= 0) return t;
    }
    /* ledges: hop down over them (off a rise onto the ground below) */
    if (dir == DIR_DOWN && nx >= 0 && ny >= 0 && nx < map_w && ny < map_h &&
        (cell_attr(nx, ny) & A_LEDGE) && cell_walkable(nx, ny + 1) &&
        (!map_elevated || player.level > elev_floor(nx, ny))) {
        int ox = player.x, oy = player.y, ol = player.level;
        actor_start_hop(&player, dir);
        player.level = (u8)elev_level_at(player.x, player.y, -1, dir);
        sfx_play(SFX_LEDGE);
        if (follower_active()) {
            kin_follow(&follower, ox, oy, 0);
            follower.a.level = (u8)ol;
        }
        actor_step(&player, 2);
        return 1;
    }
    int swap = follower_active() && follower.a.x == nx && follower.a.y == ny && !follower.a.moving &&
               follower.a.level == nl && ek != ELEV_BLOCK &&
               (ek == ELEV_TOP || !(cell_attr(nx, ny) & (A_SOLID | A_LEDGE)));
    if (!swap && (ek == ELEV_BLOCK || !cell_walkable_lv(nx, ny, nl, ek == ELEV_TOP))) {
        if (!player.anim) sfx_play(SFX_BUMP);
        player.anim++; /* walk in place against obstacles */
        return 0;
    }
    int ox = player.x, oy = player.y, ol = player.level;
    actor_start_move(&player, dir);
    player.level = (u8)nl;
    if (follower_active()) {
        kin_follow(&follower, ox, oy, 0);
        if (follower.a.x == ox && follower.a.y == oy) follower.a.level = (u8)ol;
    }
    /* advance on the same frame so consecutive steps flow without a stall */
    int speed = travel_speed(key_down(KEY_B) ? 2 : 1);
    actor_step(&player, speed);
    if (follower_active()) actor_step(&follower.a, speed);
    return 1;
}

/* The player walked into a hidden passage for the first time: a rustle
 * and a "!" (the passage stays found while you are on the map). */
static void elev_player_arrived(void)
{
    if (!map_elevated) return;
    if (player.level != elev_level_at(player.x, player.y, player.level, player.facing))
        player.level = (u8)elev_level_at(player.x, player.y, -1, player.facing);
    u16 *e = &map_elev[player.y * map_w + player.x];
    if (EV_COVER(*e) != EC_HIDDEN || (*e & EV_FOUND)) return;
    *e |= EV_FOUND;
    sfx_play(SFX_RUSTLE);
    field_emote(-1, EMOTE_EXCLAIM, 30);
}

/* One frame of overworld control. */
static int field_player_update(void)
{
    if (travel_update()) return 0;
    if (player.moving) {
        int speed = travel_speed(player.hop ? 2 : key_down(KEY_B) ? 2 : 1);
        if (follower_active() && follower.a.moving) actor_step(&follower.a, speed);
        if (actor_step(&player, speed)) {
            elev_player_arrived();
            travel_player_arrived();
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
static int time_is_night(void);

/* A wild slot can show up now (WildSlot.when: day-only / night-only). */
static int wild_slot_now(const WildSlot *s)
{
    return s->when == WHEN_ANY || (s->when == WHEN_NIGHT) == time_is_night();
}

static int travel_lure_active(void);
static int travel_surfing(void);
static int travel_surf_cell(int x, int y);

static int wild_weight(const WildSlot *s, int lure)
{
    return lure && s->weight <= 5 ? s->weight * 3 : s->weight;
}

static Monster roll_wild(int zone)
{
    const WildZone *z = &WILD_ZONES[zone];
    if (zone <= ZONE_NONE || zone >= ZONE_COUNT || !z->count) return monster_make(SP_NIBBIT, 3);
    /* LURE INCENSE (travel.c): the rarer slots come three times as often;
     * day-only / night-only slots (time.c) count only at their time */
    int lure = travel_lure_active();
    int total = 0, timed = 0;
    for (int i = 0; i < z->count; i++) timed += wild_slot_now(&z->slots[i]) ? z->slots[i].weight : 0;
    for (int i = 0; i < z->count; i++) total += !timed || wild_slot_now(&z->slots[i]) ? wild_weight(&z->slots[i], lure) : 0;
    int r = (int)rng_range((unsigned)total);
    const WildSlot *s = &z->slots[0];
    for (int i = 0; i < z->count; i++) {
        int w = !timed || wild_slot_now(&z->slots[i]) ? wild_weight(&z->slots[i], lure) : 0;
        if (r < w) {
            s = &z->slots[i];
            break;
        }
        r -= w;
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

/* Where a wild kin may wander: tall grass, or open water for swimmers. */
static int wild_cell_ok(int x, int y, int water)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h) return 0;
    if (x == player.x && y == player.y) return 0;
    if (follower_active() && x == follower.a.x && y == follower.a.y) return 0;
    if (water) return travel_surf_cell(x, y);
    return (cell_attr(x, y) & A_GRASS) && cell_walkable(x, y);
}

static void debug_parade_spawn(void);

static void wild_spawn(void)
{
    const MapDef *m = &MAPS[cur_map];
    if (m->flags & MF_DEBUG) {   /* asset viewer: a pen of wandering kin (debug.c) */
        debug_parade_spawn();
        return;
    }
    /* surfing: the map's water kin come out instead */
    int water = travel_surfing() && m->water_zone;
    int zone = water ? m->water_zone : m->zone;
    if (zone == ZONE_NONE || zone >= ZONE_COUNT || !(flag(FLAG_STARTER))) return;
    const WildZone *z = &WILD_ZONES[zone];
    int active = 0, slot = -1;
    for (int i = 0; i < WILD_MAX; i++) {
        if (wild[i].active) active++;
        else if (slot < 0) slot = i;
    }
    if (active >= z->max_active || slot < 0) return;
    for (int tries = 0; tries < 12; tries++) {
        int x = player.x - 9 + (int)rng_range(19), y = player.y - 7 + (int)rng_range(15);
        if (absi(x - player.x) + absi(y - player.y) < 4) continue;
        if (!wild_cell_ok(x, y, water)) continue;
        wild[slot].mon = roll_wild(zone);
        wild[slot].active = 1;
        wild[slot].water = (u8)water;
        wild[slot].brimming = rng_range(100) < 45;
        wild[slot].noticed = 0;
        wild[slot].life = (u16)(1200 + rng_range(900));
        wild[slot].think = (u16)(20 + rng_range(60));
        kin_place(&wild[slot].k, wild[slot].mon.species, (wild[slot].mon.flags & MF_LUSTROUS) != 0,
                  x, y, (int)rng_range(4));
        wild[slot].k.a.level = (u8)elev_level_at(x, y, -1, -1);
        return;
    }
}

static int field_busy(void);

/* A wild kin next to the player can reach them (not across a cliff). */
static int wild_reaches_player(const KinActor *k)
{
    int d = dir_to(k->a.x, k->a.y, player.x, player.y), nl;
    return d >= 0 && elev_enter(k->a.x, k->a.y, k->a.level, d, &nl) != ELEV_BLOCK && nl == player.level;
}

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
                !hush_steps && wild_reaches_player(k)) {
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
            if (dist == 1 && wild_reaches_player(k)) {
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
        int nl, ek = elev_enter(k->a.x, k->a.y, k->a.level, dir, &nl);
        int ok = ek == ELEV_FLOOR &&
                 (chase ? ((wild[i].water ? travel_surf_cell(nx, ny) : cell_walkable_lv(nx, ny, nl, 0)) &&
                           !(nx == player.x && ny == player.y) &&
                           !(follower_active() && nx == follower.a.x && ny == follower.a.y))
                        : wild_cell_ok(nx, ny, wild[i].water));
        if (ok) {
            actor_start_move(&k->a, dir);
            k->a.level = (u8)nl;
        }
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
static void travel_map_entered(int map);

static void field_enter_map(int map, int x, int y, int facing)
{
    map_load(map);
    player.x = (s16)x;
    player.y = (s16)y;
    player.ox = player.oy = 0;
    player.moving = 0;
    player.hop = 0;
    player.facing = (u8)facing;
    player.level = (u8)elev_level_at(x, y, -1, facing);
    travel_map_entered(map);
    field_load_tileset();
    follower_reset();
    field_update_camera();
    field_on_enter();
    music_map_changed(map);
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
