/*
 * Tall grass: the front blades over people and kin, the rustle when
 * someone steps in, and the little leaves (snow, ash, sparks...) it throws.
 *
 * Tall grass cells are plain BG0 metatiles whose four tiles are a tile
 * animation (wind: each variety sways at its own pace, each of its three
 * variants at its own phase) -- see tools/grass.py. Nothing of the grass
 * is on the BG3 top layer: instead, every grass cell someone overlaps gets
 * a 16x16 sprite of the cell's *front* blades, sorted with the people just
 * in front of whoever stands in that cell. So only the lower part of an
 * actor hides behind ragged blade tips, whatever their size (people 16x32,
 * kin 32x32, the bike) and mid-step, and the cell above never cuts
 * through a head.
 *
 * Stepping into grass starts a rustle: for a few frames the whole cell is
 * repainted by a sprite (blades parting and springing back, drawn behind
 * the actors) with the matching front blades over them, and two particles
 * fly off.
 *
 * Everyone standing on open ground (not in grass or water) also gets a
 * small ordered-dither shadow (the people palettes' outline colour; two
 * checker phases, picked by world position so it does not shimmer as they
 * walk). Hopping actors keep theirs on the ground.
 *
 * VRAM: object tiles OT_GRASS.. (the party-icon area, unused in the field)
 * hold every variant's front blades at the current wind frame, the rustle
 * slots' frames, the particles and the shadows; they are refreshed in vblank from
 * field_animate_tiles. Palettes: the grass sprites use copies of the BG
 * banks the grass is drawn with (already tinted for time of day / storm),
 * in object banks 7 (and 6), so on maps with tall grass there are 6 (5)
 * palette slots for people instead of 7.
 */

#define OT_GRASS          132
#define GRASS_DEF_MAX     4                         /* varieties per tileset */
#define OT_GRASS_IDLE(k)  (OT_GRASS + (k) * 4)      /* k = def * 3 + variant: 48 tiles */
#define GRASS_RUSTLE_MAX  5
#define OT_GRASS_RUSTLE(s) (OT_GRASS + 48 + (s) * 8) /* back 4 + front 4: 40 tiles */
#define OT_GRASS_PART(d)  (OT_GRASS + 88 + (d) * 2)  /* 8 tiles */
#define OT_SHADOW(p)      (OT_GRASS + 96 + (p) * 4)  /* person 16x16, 2 phases: 8 tiles */
#define OT_SHADOW_KIN(p)  (OT_GRASS + 104 + (p) * 8) /* kin 32x16, 2 phases: 16 tiles */
#define GRASS_RUSTLE_STEP 5                         /* frames per rustle frame */
#define GRASS_RUSTLE_TIME (GRASS_RUSTLE * GRASS_RUSTLE_STEP)
#define GRASS_OVER_MAX    16                        /* overlay sprites per frame */

static unsigned frame_count;                        /* battle_ui.c: frames since boot */

typedef char GrassTilesFit[OT_GRASS + 120 <= 256 && OT_GRASS_PART(GRASS_DEF_MAX) <= OT_SHADOW(0) ? 1 : -1];

static struct {
    int tileset;                   /* tileset the tables below are for (-1: none) */
    const GrassSet *set;
    u8 obank[8];                   /* BG bank -> object bank (0 = not grass) */
    u8 banks;                      /* object banks in use (0..2) */
    u8 wind[GRASS_DEF_MAX];        /* wind frame shown per variety */
    unsigned last_frame;           /* frame_count of the last vblank upload */
    u8 dirty;
} grass = { -1, 0, { 0 }, 0, { 0 }, 0, 1 };

static struct {
    s16 x, y;                      /* cell */
    u8 t, kind, shown, active;     /* t: frames since it started; kind: def*3+variant */
} rustle[GRASS_RUSTLE_MAX];

/* Grass variety * 3 + variant of a metatile, or -1. */
static int grass_kind_of(u16 v)
{
    const GrassSet *s = grass.set;
    if (!s || v >= CELL_PATH) return -1;
    for (int d = 0; d < s->count; d++)
        for (int k = 0; k < GRASS_VARIANTS; k++)
            if (s->defs[d].meta[k] == v) return d * GRASS_VARIANTS + k;
    return -1;
}

static int grass_cell_kind(int x, int y)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h) return -1;
    if (!(cell_attr(x, y) & A_GRASS)) return -1;
    return grass_kind_of(map_cells[y * map_w + x]);
}

static const GrassDef *grass_def(int kind) { return &grass.set->defs[kind / GRASS_VARIANTS]; }

/* People palette slots left on this map (field_draw_sprites). */
static int grass_npc_slots(void)
{
    return 7 - grass.banks;
}

/* A new tileset is in VRAM (field_load_tileset). */
static void grass_tileset_loaded(void)
{
    grass.tileset = map_tileset;
    grass.set = &GRASS_SETS[map_tileset];
    if (!grass.set->count) grass.set = 0;
    for (int b = 0; b < 8; b++) grass.obank[b] = 0;
    grass.banks = 0;
    if (grass.set)
        for (int d = 0; d < grass.set->count && d < GRASS_DEF_MAX; d++) {
            int b = grass.set->defs[d].bank;
            if (!grass.obank[b] && grass.banks < 2) grass.obank[b] = (u8)(7 - grass.banks++);
        }
    for (int d = 0; d < GRASS_DEF_MAX; d++) grass.wind[d] = 0;   /* the tileset copy is frame 0 */
    for (int i = 0; i < GRASS_RUSTLE_MAX; i++) rustle[i].active = 0;
    grass.dirty = 1;
}

/* An actor starts walking into (x, y) (field.c actor_start_move / hop). */
static void grass_step_into(int x, int y)
{
    if (!grass.set) return;
    int kind = grass_cell_kind(x, y);
    if (kind < 0) return;
    /* only near the screen */
    if (x * 16 < cam_x - 32 || x * 16 > cam_x + SCREEN_WIDTH + 16 || y * 16 < cam_y - 32 ||
        y * 16 > cam_y + SCREEN_HEIGHT + 16)
        return;
    int slot = -1, oldest = 0;
    for (int i = 0; i < GRASS_RUSTLE_MAX; i++) {
        if (rustle[i].active && rustle[i].x == x && rustle[i].y == y) {
            slot = i;
            break;
        }
        if (!rustle[i].active && slot < 0) slot = i;
        if (rustle[i].t > rustle[oldest].t) oldest = i;
    }
    if (slot < 0) slot = oldest;
    rustle[slot].x = (s16)x;
    rustle[slot].y = (s16)y;
    rustle[slot].t = 0;
    rustle[slot].kind = (u8)kind;
    rustle[slot].shown = 0xFF;
    rustle[slot].active = 1;
}

static int grass_rustle_at(int x, int y)
{
    for (int i = 0; i < GRASS_RUSTLE_MAX; i++)
        if (rustle[i].active && rustle[i].x == x && rustle[i].y == y) return i;
    return -1;
}

/* Wind frame of a variety at the current animation frame (same timing as
 * the tileset's tile animation in field_animate_tiles). */
static int grass_wind_frame(const GrassDef *d)
{
    return field_anim_frame / d->period % GRASS_WIND;
}

/* Shadow tiles: a w x 16 sprite (w 16 or 32) with a dithered ellipse
 * (colour 1) around (w / 2, 14.5); phase flips the checker. */
static void shadow_build(u32 *dst, int w, int rx4, int phase)
{
    static const u8 BAYER[4][4] = { { 0, 8, 2, 10 }, { 12, 4, 14, 6 }, { 3, 11, 1, 9 }, { 15, 7, 13, 5 } };
    int tw = w / 8;
    for (int t = 0; t < tw * 2; t++)
        for (int y = 0; y < 8; y++) {
            u32 row = 0;
            for (int x = 0; x < 8; x++) {
                int px = (t % tw) * 8 + x, py = (t / tw) * 8 + y;
                /* in quarter pixels: ((dx / rx)^2 + (dy / 2.25)^2) scaled by 256 */
                int dx = (px * 4 + 2) - w * 2, dy = (py * 4 + 2) - 58;
                int r = dx * dx * 256 / (rx4 * rx4) + dy * dy * 256 / (9 * 9);
                if (r > 256) continue;
                int thr = r < 110 ? 12 : 7;   /* denser in the middle */
                if (BAYER[py & 3][(px + phase) & 3] < thr) row |= 1u << (x * 4);
            }
            dst[t * 8 + y] = row;
        }
}

/* Vblank: sprite tiles for the wind frame, the rustles, the shadows and
 * the palettes. */
static void grass_present(void)
{
    /* a menu may have used the object tiles / palettes in between */
    if (frame_count != grass.last_frame + 1) grass.dirty = 1;
    grass.last_frame = frame_count;
    if (grass.dirty)
        for (int p = 0; p < 2; p++) {
            shadow_build(VRAM_OBJ_TILES + OT_SHADOW(p) * 8, 16, 22, p);
            shadow_build(VRAM_OBJ_TILES + OT_SHADOW_KIN(p) * 8, 32, 38, p);
        }
    if (!grass.set) {
        grass.dirty = 0;
        return;
    }
    for (int b = 0; b < 8; b++)
        if (grass.obank[b]) {
            u16 *dst = obj_palette + grass.obank[b] * 16;
            for (int i = 1; i < 16; i++) dst[i] = bg_palette[b * 16 + i];
        }
    const GrassSet *s = grass.set;
    for (int d = 0; d < s->count && d < GRASS_DEF_MAX; d++) {
        const GrassDef *g = &s->defs[d];
        if (field_anim_frame % g->period == 0) grass.wind[d] = (u8)grass_wind_frame(g);
        static u8 up[GRASS_DEF_MAX];
        if (!grass.dirty && up[d] == grass.wind[d] + 1) continue;
        up[d] = (u8)(grass.wind[d] + 1);
        for (int v = 0; v < GRASS_VARIANTS; v++)
            copy32(VRAM_OBJ_TILES + OT_GRASS_IDLE(d * GRASS_VARIANTS + v) * 8,
                   g->front + (v * GRASS_WIND + grass.wind[d]) * 4 * 8, 4 * 8);
        if (grass.dirty) copy32(VRAM_OBJ_TILES + OT_GRASS_PART(d) * 8, g->part, 2 * 8);
    }
    for (int i = 0; i < GRASS_RUSTLE_MAX; i++) {
        if (!rustle[i].active) continue;
        int f = rustle[i].t / GRASS_RUSTLE_STEP;
        if (f >= GRASS_RUSTLE) continue;
        if (!grass.dirty && rustle[i].shown == f) continue;
        rustle[i].shown = (u8)f;
        const GrassDef *g = grass_def(rustle[i].kind);
        int v = rustle[i].kind % GRASS_VARIANTS;
        copy32(VRAM_OBJ_TILES + OT_GRASS_RUSTLE(i) * 8, g->rback + (v * GRASS_RUSTLE + f) * 4 * 8, 4 * 8);
        copy32(VRAM_OBJ_TILES + (OT_GRASS_RUSTLE(i) + 4) * 8, g->rfront + (v * GRASS_RUSTLE + f) * 4 * 8,
               4 * 8);
    }
    grass.dirty = 0;
}

/* Field sprites: the front blades of every grass cell an actor overlaps,
 * the rustles (their repainted cell behind, their particles in front).
 * Called by field_draw_sprites before sorting; returns the new count. */
static int grass_push_sprites(FieldSprite *list, int n, int max)
{
    /* shadows under everyone on open ground */
    for (int i = 0, actors = n; i < actors && n < max; i++) {
        const FieldSprite *s = &list[i];
        if (s->kind != 0 && s->kind != 1) continue;
        int fx = floor_div16(s->x + 8), fy = floor_div16(s->y + 12);
        if (fx < 0 || fy < 0 || fx >= map_w || fy >= map_h) continue;
        /* on a bridge deck (elev.c) the shadow falls on the deck, above its layer */
        int deck = s->prio == 1 && ec_walkable(EV_COVER(elev_at(fx, fy)));
        if (!deck && ((cell_attr(fx, fy) & A_WATER) || grass_cell_kind(fx, fy) >= 0)) continue;
        int ph = (s->x + s->y) & 1;
        if (s->kind == 0)
            list[n++] = (FieldSprite){ s->y - 1, s->x, 4, OT_SHADOW(ph), OBANK_PLAYER, 0, 1, SQ16, s->prio };
        else
            list[n++] = (FieldSprite){ s->y - 1, s->x - 8, 4, OT_SHADOW_KIN(ph), OBANK_PLAYER, 0, 1, WIDE32x16,
                                       s->prio };
    }
    if (!grass.set) return n;
    for (int i = 0; i < GRASS_RUSTLE_MAX; i++)
        if (rustle[i].active && ++rustle[i].t >= GRASS_RUSTLE_TIME) rustle[i].active = 0;
    s16 cx[GRASS_OVER_MAX], cy[GRASS_OVER_MAX];
    u8 cp[GRASS_OVER_MAX];
    int nc = 0;
    for (int i = 0; i < n; i++) {
        const FieldSprite *s = &list[i];
        if (s->kind != 0 && s->kind != 1) continue;
        if (s->a >> 16) continue;   /* hopping, surfing: above the grass */
        /* the part of the sprite that stands in cells: people 16 wide, kin 32 */
        int x0 = s->kind == 1 ? s->x - 8 : s->x, x1 = s->kind == 1 ? s->x + 23 : s->x + 15;
        int ytop = floor_div16(s->y), ybot = floor_div16(s->y + 15);
        for (int y = ytop; y <= ybot; y++)
            for (int x = floor_div16(x0); x <= floor_div16(x1); x++) {
                if (grass_cell_kind(x, y) < 0) continue;
                /* up on a deck over the grass (elev.c): no blades over them */
                if (s->prio == 1 && ec_walkable(EV_COVER(elev_at(x, y)))) continue;
                int dup = -1;
                for (int k = 0; k < nc; k++)
                    if (cx[k] == x && cy[k] == y) dup = k;
                if (dup >= 0) {
                    if (s->prio == 1) cp[dup] = 1;
                } else if (nc < GRASS_OVER_MAX) {
                    cx[nc] = (s16)x;
                    cy[nc] = (s16)y;
                    cp[nc] = s->prio == 1;
                    nc++;
                }
            }
    }
    for (int k = 0; k < nc && n < max; k++) {
        int kind = grass_cell_kind(cx[k], cy[k]);
        int r = grass_rustle_at(cx[k], cy[k]);
        int tile = r >= 0 ? OT_GRASS_RUSTLE(r) + 4 : OT_GRASS_IDLE(kind);
        int bank = grass.obank[grass_def(kind)->bank];
        if (!bank) continue;
        /* sorted just in front of anyone standing in the cell */
        list[n++] = (FieldSprite){ cy[k] * 16 + 1, cx[k] * 16, 4, tile, bank, 0, -1, SQ16, cp[k] ? 1 : 0 };
    }
    for (int i = 0; i < GRASS_RUSTLE_MAX && n + 3 <= max; i++) {
        if (!rustle[i].active) continue;
        const GrassDef *g = grass_def(rustle[i].kind);
        int bank = grass.obank[g->bank];
        if (!bank) continue;
        int x = rustle[i].x * 16, y = rustle[i].y * 16, t = rustle[i].t;
        /* the repainted cell, behind everyone who overlaps it */
        list[n++] = (FieldSprite){ y - 16, x, 4, OT_GRASS_RUSTLE(i), bank, 0, 16, SQ16 };
        /* two particles thrown up and out, falling back */
        int d = rustle[i].kind / GRASS_VARIANTS;
        int rise = t * 3 / 2 - t * t / 16;
        int pf = OT_GRASS_PART(d) + ((t >> 2) & 1);
        list[n++] = (FieldSprite){ y + 15, x + 2 - t / 3, 4, pf, bank, 0, 4 - rise - 15, SQ8 };
        list[n++] = (FieldSprite){ y + 15, x + 6 + t / 3, 4, pf, bank, 1, 1 - rise * 4 / 5 - 15, SQ8 };
    }
    return n;
}
