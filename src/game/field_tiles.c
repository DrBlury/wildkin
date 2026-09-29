/*
 * Area-local scene residency. ROM tileset IDs are not VRAM addresses:
 * only terrain actually drawn and this area's declared decor are loaded.
 * Terrain entries keep their ROM IDs through composition (including dynamic
 * farm tiles), while decor carries a private tag. Both resolve once at the
 * screen-map boundary. Compatible seam previews share this cache; an ordinary area change resets it completely.
 */
#define FIELD_TILE_IDS 1024
#define FIELD_TILE_MISSING 0xFFFF
/* Field palettes occupy banks 0..7; bit 15 is free until map upload. */
#define FIELD_DECOR_ENTRY 0x8000

EWRAM_BSS static u16 field_tile_slot[FIELD_TILE_IDS];
static int field_decor_tiles;
static int field_tiles_failed;

static void field_tiles_reset(void)
{
    for (int i = 0; i < FIELD_TILE_IDS; i++) field_tile_slot[i] = FIELD_TILE_MISSING;
    for (int k = 0; k < DK_COUNT; k++) decor_base[k] = 0;
    field_decor_tiles = 0;
    field_tiles_failed = tset()->tile_count > FIELD_TILE_IDS;
    decor_tiles_used = decor_tiles_wanted = 1;
    /* Tile zero is always transparent, including after menus and battles. */
    field_tile_slot[0] = 0;
    fill32(VRAM_SCENE_TILES, 0, SCENE_TILE_MAX * 8);
    fill32(VRAM_MAP(SB_FIELD_BOTTOM), 0, 512);
    fill32(VRAM_MAP(SB_PANEL), 0, 512);
    fill32(VRAM_MAP(SB_FIELD_TOP), 0, 512);
}

static int field_tiles_load_decor(int kind)
{
    if (decor_base[kind]) return 1;
    const DecorDef *d = &DECOR_DEFS[map_tileset][kind];
    decor_tiles_wanted += d->tile_count;
    if (!d->w || !d->tile_count ||
        decor_tiles_used + d->tile_count > SCENE_TILE_MAX) {
        field_tiles_failed = 1;
        return 0;
    }
    decor_base[kind] = (u16)decor_tiles_used;
    int frame = d->frames > 1 && d->period ? field_anim_frame / d->period % d->frames : 0;
    copy32(VRAM_SCENE_TILES + decor_tiles_used * 8,
           decor_tiles + (d->tile_first + frame * d->tile_count) * 8, (unsigned)d->tile_count * 8);
    field_decor_tiles += d->tile_count;
    decor_tiles_used += d->tile_count;
    return 1;
}

/* Called only as cells are uploaded or a bounded seam preview is built. */
static u16 field_tile_entry(u16 entry)
{
    if (entry & FIELD_DECOR_ENTRY) return entry & ~FIELD_DECOR_ENTRY;
    int id = entry & 1023;
    int slot = field_tile_slot[id];
    if (slot == FIELD_TILE_MISSING) {
        decor_tiles_wanted++;
        if (id >= tset()->tile_count || decor_tiles_used >= SCENE_TILE_MAX) {
            field_tiles_failed = 1;
            return 0; /* Never turn a bad reference into UI or stale scene graphics. */
        }
        slot = decor_tiles_used++;
        field_tile_slot[id] = (u16)slot;
        const u32 *src = tset()->tiles + id * 8;
        /* First use may be halfway through water/grass animation. */
        for (int i = 0; i < tset()->anim_count; i++) {
            const TileAnim *a = &tset()->anims[i];
            if (id >= a->tile && id < a->tile + a->count && a->period && a->frames) {
                int f = field_anim_frame / a->period % a->frames;
                src = a->data + (f * a->count + id - a->tile) * 8;
                break;
            }
        }
        copy32(VRAM_SCENE_TILES + slot * 8, src, 8);
    }
    return (u16)((entry & 0xFC00) | slot);
}

static void field_tiles_animate(const TileAnim *a, int frame)
{
    for (int i = 0; i < a->count; i++) {
        int id = a->tile + i;
        if (id >= FIELD_TILE_IDS) { field_tiles_failed = 1; return; }
        int slot = field_tile_slot[id];
        if (slot != FIELD_TILE_MISSING)
            copy32(VRAM_SCENE_TILES + slot * 8, a->data + (frame * a->count + i) * 8, 8);
    }
}
