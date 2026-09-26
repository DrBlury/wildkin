/*
 * Farming: WILLOW ACRE, soil, crops, watering, fertiliser, harvest, the
 * shipping bin, processors, kin workers, the storage chest and wild berry
 * patches (docs/EXPANSION.md 7.2). Owner: FARM system.
 *
 * The plot. Every A_SOIL cell of WILLOW ACRE ('s' soil, 'o' orchard
 * mound) is a plot, numbered in row-major order from the map rows (so the
 * numbering never depends on run-time state). A plot is tilled with the
 * HOE, watered with the CAN, seeded, fertilised and harvested; farm.c
 * draws its look over the map through dyn_cell() (the MT_FA_* metatiles
 * of tools/tilesets/ts_farm.py) and makes grown trees and sprinklers
 * solid through farm_cell_attr().
 *
 * Growth. When a day starts (time.c, 06:00 or sleeping), a watered plot
 * grows GROW_PER_DAY units (+1 with FERTILIZER); a crop is ripe after
 * CropDef.days days of growth. Trees grow every day, watered or not.
 * Then the plots dry, and rain, sprinklers, GROW MULCH and WATER workers
 * wet them again for the new day. Regrowing crops and fruit trees give
 * again after CropDef.regrow days.
 *
 * On the farm, L/R turn the tool ring (HOE, CAN, seeds, fertilisers,
 * sprinkler) and A uses the tool on the plot you face; ripe crops are
 * picked with any tool. Quality (OK / GREAT / PERFECT) comes from compost,
 * fertiliser and tending, and adds to the yield.
 *
 * Hooks into the field (the only lines outside this module):
 *   field.c map_load        farm_map_loaded()
 *   field.c cell_attr       farm_cell_attr()
 *   field.c sprites         farm_field_kin() (workers walk as kin)
 *   script.c interact       farm_interact()
 *   script.c field_draw     farm_draw()
 *   time.c time_tick        farm_tick(), time_new_day -> farm_new_day()
 *
 * OBJ use (docs/EXPANSION.md 10.3): tiles 512-639; palette bank 8 entries
 * 9-15 (the satchel uses 1-8): the effect colours on the farm, the berry
 * colours on other maps.
 */

/* ================================================================ */
/*  Crops                                                           */
/* ================================================================ */

/* Order = tools/tilesets/ts_farm.py CROPS + TREES, and the IK_PLANT /
 * IK_CROP params in items/farm.inc. */
enum {
    CROP_GLOWBERRY, CROP_EMBERBERRY, CROP_TIDEBERRY, CROP_RADISH, CROP_CARROT, CROP_POTATO,
    CROP_PUMPKIN, CROP_CHILI, CROP_TOMATO, CROP_CORN, CROP_SUNFLOWER, CROP_MOTEBLOOM,
    CROP_APPLE, CROP_PEACH, CROP_COUNT
};
#define CROP_FIELD_COUNT 12
#define GROW_PER_DAY 4

typedef struct {
    u8 days;        /* days of growth to ripen (trees: to grow up) */
    u8 regrow;      /* days to give again after a harvest, 0 = one harvest */
    u8 yield;       /* picked per harvest (before quality) */
    u16 value;      /* coins each in the shipping bin */
    u16 grow_mt, ripe_mt;
} CropDef;

static const CropDef CROPS[CROP_COUNT] = {
    [CROP_GLOWBERRY]  = { 3, 2, 3, 35, MT_FA_GLOWBERRY_GROW, MT_FA_GLOWBERRY_RIPE },
    [CROP_EMBERBERRY] = { 4, 2, 3, 45, MT_FA_EMBERBERRY_GROW, MT_FA_EMBERBERRY_RIPE },
    [CROP_TIDEBERRY]  = { 4, 2, 3, 45, MT_FA_TIDEBERRY_GROW, MT_FA_TIDEBERRY_RIPE },
    [CROP_RADISH]     = { 2, 0, 1, 45, MT_FA_RADISH_GROW, MT_FA_RADISH_RIPE },
    [CROP_CARROT]     = { 3, 0, 1, 70, MT_FA_CARROT_GROW, MT_FA_CARROT_RIPE },
    [CROP_POTATO]     = { 4, 0, 2, 50, MT_FA_POTATO_GROW, MT_FA_POTATO_RIPE },
    [CROP_PUMPKIN]    = { 7, 0, 1, 340, MT_FA_PUMPKIN_GROW, MT_FA_PUMPKIN_RIPE },
    [CROP_CHILI]      = { 4, 2, 3, 30, MT_FA_CHILI_GROW, MT_FA_CHILI_RIPE },
    [CROP_TOMATO]     = { 5, 2, 2, 45, MT_FA_TOMATO_GROW, MT_FA_TOMATO_RIPE },
    [CROP_CORN]       = { 6, 3, 1, 90, MT_FA_CORN_GROW, MT_FA_CORN_RIPE },
    [CROP_SUNFLOWER]  = { 5, 0, 1, 150, MT_FA_SUNFLOWER_GROW, MT_FA_SUNFLOWER_RIPE },
    [CROP_MOTEBLOOM]  = { 8, 0, 1, 900, MT_FA_MOTEBLOOM_GROW, MT_FA_MOTEBLOOM_RIPE },
    [CROP_APPLE]      = { 12, 3, 3, 90, MT_FA_FRUIT_BOTTOM, MT_FA_APPLE_BOTTOM },
    [CROP_PEACH]      = { 12, 3, 3, 110, MT_FA_FRUIT_BOTTOM, MT_FA_PEACH_BOTTOM },
};

/* The item ids run in crop order (items/farm_ids.inc). */
typedef char FarmSeedIds[ITEM_SEED_MOTEBLOOM - ITEM_SEED_GLOWBERRY == 11 &&
                         ITEM_SAPLING_PEACH - ITEM_SEED_GLOWBERRY == 13 ? 1 : -1];
typedef char FarmCropIds[ITEM_CROP_PEACH - ITEM_CROP_GLOWBERRY == 13 ? 1 : -1];

static int crop_is_tree(int c) { return c >= CROP_APPLE; }
static int crop_item(int c) { return ITEM_CROP_GLOWBERRY + c; }
static int crop_target(int c) { return CROPS[c].days * GROW_PER_DAY; }
/* Growth at which the crop can be picked (trees: grown up plus one fruiting). */
static int crop_ripe_at(int c) { return crop_target(c) + (crop_is_tree(c) ? CROPS[c].regrow * GROW_PER_DAY : 0); }

enum { FERT_BASIC, FERT_COMPOST, FERT_MULCH };

/* ================================================================ */
/*  Processed goods                                                 */
/* ================================================================ */

enum { PROC_JAR, PROC_PRESS, PROC_DRIER, PROC_COUNT };
static const char *const PROC_NAMES[PROC_COUNT] = { "PRESERVES JAR", "FRUIT PRESS", "DRYING RACK" };

typedef struct { u8 proc, crop, in, days; u8 out; } Recipe;
static const Recipe RECIPES[] = {
    { PROC_JAR, CROP_GLOWBERRY, 2, 1, ITEM_FRUIT_JAM }, { PROC_JAR, CROP_EMBERBERRY, 2, 1, ITEM_FRUIT_JAM },
    { PROC_JAR, CROP_TIDEBERRY, 2, 1, ITEM_FRUIT_JAM }, { PROC_JAR, CROP_APPLE, 1, 1, ITEM_FRUIT_JAM },
    { PROC_JAR, CROP_PEACH, 1, 1, ITEM_FRUIT_JAM },     { PROC_JAR, CROP_TOMATO, 2, 1, ITEM_FRUIT_JAM },
    { PROC_JAR, CROP_RADISH, 2, 1, ITEM_PICKLES },      { PROC_JAR, CROP_CARROT, 2, 1, ITEM_PICKLES },
    { PROC_JAR, CROP_CHILI, 3, 1, ITEM_PICKLES },       { PROC_JAR, CROP_CORN, 2, 1, ITEM_PICKLES },
    { PROC_PRESS, CROP_GLOWBERRY, 3, 1, ITEM_BERRY_JUICE }, { PROC_PRESS, CROP_EMBERBERRY, 3, 1, ITEM_BERRY_JUICE },
    { PROC_PRESS, CROP_TIDEBERRY, 3, 1, ITEM_BERRY_JUICE }, { PROC_PRESS, CROP_APPLE, 2, 1, ITEM_APPLE_PRESS },
    { PROC_PRESS, CROP_PEACH, 2, 1, ITEM_PEACH_NECTAR },
    { PROC_DRIER, CROP_CHILI, 3, 2, ITEM_DRIED_CHILI }, { PROC_DRIER, CROP_APPLE, 2, 2, ITEM_DRIED_FRUIT },
    { PROC_DRIER, CROP_PEACH, 2, 2, ITEM_DRIED_FRUIT }, { PROC_DRIER, CROP_SUNFLOWER, 1, 2, ITEM_SUN_SEEDS },
};
#define RECIPE_COUNT ((int)(sizeof(RECIPES) / sizeof(RECIPES[0])))
#define PROC_BATCH_MAX 5

/* Coins each in the shipping bin (0 = the bin won't take it). */
static int farm_value(int item)
{
    if (item >= ITEM_CROP_GLOWBERRY && item <= ITEM_CROP_PEACH) return CROPS[item - ITEM_CROP_GLOWBERRY].value;
    switch (item) {
    case ITEM_FRUIT_JAM: return 150;
    case ITEM_PICKLES: return 130;
    case ITEM_DRIED_CHILI: return 160;
    case ITEM_DRIED_FRUIT: return 300;
    case ITEM_SUN_SEEDS: return 240;
    default: return 0;
    }
}

/* What REEVE sells once you own the farm (shop_open_stock). */
static const u8 FARM_SHOP_STOCK[] = {
    ITEM_SEED_RADISH, ITEM_SEED_CARROT, ITEM_SEED_POTATO, ITEM_SEED_GLOWBERRY, ITEM_SEED_EMBERBERRY,
    ITEM_SEED_TIDEBERRY, ITEM_SEED_CHILI, ITEM_SEED_TOMATO, ITEM_SEED_CORN, ITEM_SEED_SUNFLOWER,
    ITEM_SEED_PUMPKIN, ITEM_SEED_MOTEBLOOM, ITEM_SAPLING_APPLE, ITEM_SAPLING_PEACH,
    ITEM_FERTILIZER, ITEM_RICH_COMPOST, ITEM_GROW_MULCH, ITEM_SPRINKLER,
};
#define FARM_SHOP_STOCK_COUNT ((int)sizeof(FARM_SHOP_STOCK))

/* ================================================================ */
/*  Kin workers                                                     */
/* ================================================================ */

enum { JOB_NONE, JOB_WATER, JOB_TEND, JOB_HARVEST, JOB_GUARD, JOB_FORAGE, JOB_HONEY, JOB_COUNT };
static const char *const JOB_NAMES[JOB_COUNT] = { "---", "WATER", "TEND", "HARVEST", "GUARD", "FORAGE", "HONEY" };
static const char *const JOB_DESC[JOB_COUNT] = {
    "No job. Pick a kin from the Shelf with A.",
    "Waters dry crops every morning. TIDE kin are best at it.",
    "Tends growing crops so they grow faster and better. BLOOM kin are best.",
    "Brings ripe crops in to your bag. BEAST and BRAWL kin are best.",
    "Keeps the crows off the crops. RELIC and DUSK kin are best.",
    "Roams the Vale and brings back materials. Any kin does well.",
    "Collects GLOW HONEY from the beehives. SWARM kin are best.",
};

/* 2 = suited, 1 = can do it (half as well). */
static int job_fit(int job, int species)
{
    const Species *s = &SPECIES[species];
    int t1 = s->type1, t2 = s->type2;
#define HAS(T) (t1 == (T) || t2 == (T))
    switch (job) {
    case JOB_WATER: return HAS(T_TIDE) ? 2 : 1;
    case JOB_TEND: return HAS(T_BLOOM) ? 2 : 1;
    case JOB_HARVEST: return HAS(T_BEAST) || HAS(T_BRAWL) ? 2 : 1;
    case JOB_GUARD: return HAS(T_RELIC) || HAS(T_DUSK) ? 2 : 1;
    case JOB_FORAGE: return 2;
    case JOB_HONEY: return HAS(T_SWARM) ? 2 : 1;
    default: return 0;
    }
#undef HAS
}

/* The job a kin is best at (for a new hand). */
static int job_best(int species)
{
    static const u8 ORDER[] = { JOB_WATER, JOB_TEND, JOB_HARVEST, JOB_GUARD, JOB_HONEY };
    for (unsigned i = 0; i < sizeof(ORDER); i++)
        if (job_fit(ORDER[i], species) == 2) return ORDER[i];
    return JOB_FORAGE;
}

static const u8 FORAGE_FINDS[] = {
    ITEM_MINT_LEAF, ITEM_GLOWCAP, ITEM_SALT, ITEM_COAL, ITEM_BONE_MEAL, ITEM_HEARTGLASS_SAND,
    ITEM_SILK_THREAD, ITEM_IRON_ORE, ITEM_MINT_LEAF, ITEM_GLOWCAP,
};

/* ================================================================ */
/*  State (saved: docs/EXPANSION.md 10.4, at most MOD_FARM_MAX)      */
/* ================================================================ */

#define FARM_VERSION 1
#define FARM_PLOTS 176
#define FARM_BERRIES 64
#define FARM_WORKERS 4
#define FARM_CHEST 24
#define CAN_MAX 20
#define BERRY_RIPE 12            /* growth units; +GROW_PER_DAY a day: 3 days */
#define FARM_DEED_PRICE 15000
#define FARM_DEED_PRICE_QUEST 10000

enum {
    PF_TILLED = 1, PF_WET = 2, PF_FERT = 4, PF_COMPOST = 8, PF_MULCH = 16, PF_WET2 = 32,
    PF_SPRINKLER = 64, PF_REGROWN = 128,
};

typedef struct { u8 crop, growth, flags, care; } FarmPlot;  /* crop: CROP_* + 1, 0 = empty */
typedef struct { u8 growth, picks; } BerryPatch;
typedef struct { u8 job, species, level, days; u32 pot; } FarmWorker;  /* found on the Shelf by species + pot */
typedef struct { u8 recipe, batches; u16 ready_day; } FarmProc;        /* recipe: RECIPES index + 1 */
typedef struct { u16 code, count; } FarmChestSlot;                    /* code: item_code() */

typedef struct {
    u8 version, owned, can_water, tool;
    u8 last_crows, pad[3];
    u32 bin_value;              /* paid next morning */
    u16 bin_items, pad2;
    u32 earned;                 /* everything the bin ever paid */
    FarmPlot plots[FARM_PLOTS];
    BerryPatch berries[FARM_BERRIES];
    FarmWorker workers[FARM_WORKERS];
    FarmProc procs[PROC_COUNT];
    FarmChestSlot chest[FARM_CHEST];
    u16 great[CROP_COUNT], perfect[CROP_COUNT], harvested[CROP_COUNT];
} FarmState;

static FarmState farm;

static u16 item_code(int item);
static int item_from_code(u16 code);

static void farm_reset(void)
{
    u8 *raw = (u8 *)&farm;
    for (unsigned i = 0; i < sizeof(farm); i++) raw[i] = 0;
    farm.version = FARM_VERSION;
    farm.can_water = CAN_MAX;
    for (int i = 0; i < FARM_BERRIES; i++) farm.berries[i].growth = BERRY_RIPE;
}

static void farm_validate(void)
{
    if (farm.version != FARM_VERSION) {
        farm_reset();
        return;
    }
    farm.owned &= 1;
    if (farm.can_water > CAN_MAX) farm.can_water = CAN_MAX;
    for (int i = 0; i < FARM_PLOTS; i++) {
        FarmPlot *p = &farm.plots[i];
        if (p->crop > CROP_COUNT) p->crop = 0;
        if (p->crop && p->growth > crop_ripe_at(p->crop - 1)) p->growth = (u8)crop_ripe_at(p->crop - 1);
        if (!p->crop) p->growth = 0;
        if (p->crop && (p->flags & PF_SPRINKLER)) p->flags &= (u8)~PF_SPRINKLER;
    }
    for (int i = 0; i < FARM_BERRIES; i++)
        if (farm.berries[i].growth > BERRY_RIPE) farm.berries[i].growth = BERRY_RIPE;
    for (int i = 0; i < FARM_WORKERS; i++) {
        FarmWorker *w = &farm.workers[i];
        if (w->job >= JOB_COUNT || w->species >= SP_COUNT) w->job = 0;
        if (!w->job) w->species = 0;
    }
    for (int i = 0; i < PROC_COUNT; i++) {
        FarmProc *p = &farm.procs[i];
        if (p->recipe > RECIPE_COUNT || !p->batches || RECIPES[p->recipe - 1].proc != i) p->recipe = p->batches = 0;
        if (p->batches > PROC_BATCH_MAX) p->batches = PROC_BATCH_MAX;
    }
    for (int i = 0; i < FARM_CHEST; i++)
        if (farm.chest[i].count > 999) farm.chest[i].count = 999;
}

/* ================================================================ */
/*  WILLOW ACRE geometry                                            */
/* ================================================================ */

static u8 plot_x[FARM_PLOTS], plot_y[FARM_PLOTS], plot_orchard[FARM_PLOTS];
static int plot_count = -1;
EWRAM_BSS static u8 plot_at_cell[MAP_MAX_W * MAP_MAX_H];   /* plot + 1, 0 = none */

static void farm_geom_init(void)
{
    if (plot_count >= 0) return;
    const MapDef *m = &MAPS[MAP_WILLOW_ACRE];
    const TilesetDef *t = &TILESETS[m->tileset];
    plot_count = 0;
    for (int y = 0; y < m->h; y++)
        for (int x = 0; x < m->w; x++) {
            u16 v = legend_pick(legend_for(t, m->rows[y][x]), x, y);
            plot_at_cell[y * m->w + x] = 0;
            if (v >= CELL_PATH || !(terrain_attr(m->tileset, v) & A_SOIL) || plot_count >= FARM_PLOTS) continue;
            plot_x[plot_count] = (u8)x;
            plot_y[plot_count] = (u8)y;
            plot_orchard[plot_count] = v == MT_FA_ORCHARD;
            plot_at_cell[y * m->w + x] = (u8)(++plot_count);
        }
}

/* The plot at a WILLOW ACRE cell (whatever map is loaded), or -1. */
static int plot_at_xy(int x, int y)
{
    farm_geom_init();
    const MapDef *m = &MAPS[MAP_WILLOW_ACRE];
    if (x < 0 || y < 0 || x >= m->w || y >= m->h) return -1;
    return plot_at_cell[y * m->w + x] - 1;
}

/* The plot at a cell of the loaded map, or -1. */
static int farm_plot_at(int x, int y)
{
    return cur_map == MAP_WILLOW_ACRE ? plot_at_xy(x, y) : -1;
}

static int plot_ripe(const FarmPlot *p)
{
    return p->crop && p->growth >= crop_ripe_at(p->crop - 1);
}

/* A tree tall enough to be solid and wear a crown. */
static int plot_tree_up(const FarmPlot *p)
{
    return p->crop && crop_is_tree(p->crop - 1) && p->growth * 3 >= crop_target(p->crop - 1);
}

/* ================================================================ */
/*  Berry patches (OBJ_BERRY, arg = patch id)                       */
/* ================================================================ */

/* Patch ids by region: east 0-9, west 10-19, north 20-29, grim 30-39,
 * far 40-49, village/farm 50-63. One berry per region, so every map's
 * patches share one sprite palette. */
static int berry_crop(int patch)
{
    static const u8 KIND[7] = { CROP_EMBERBERRY, CROP_TIDEBERRY, CROP_TIDEBERRY, CROP_EMBERBERRY,
                                CROP_EMBERBERRY, CROP_GLOWBERRY, CROP_GLOWBERRY };
    return KIND[clampi(patch / 10, 0, 6)];
}

static int berry_obj_at(int x, int y)
{
    const MapDef *m = &MAPS[cur_map];
    for (int i = 0; i < m->obj_count; i++)
        if (m->objs[i].kind == OBJ_BERRY && m->objs[i].x == x && m->objs[i].y == y) return i;
    return -1;
}

static int berry_ripe(int patch)
{
    return patch >= 0 && patch < FARM_BERRIES && farm.berries[patch].growth >= BERRY_RIPE;
}

/* ================================================================ */
/*  Workers in the field                                            */
/* ================================================================ */

static KinActor farm_kin[FARM_WORKERS];
static u16 farm_kin_timer[FARM_WORKERS];

/* The fenced field (workers stay inside it): world/farm/data.h. */
#define FIELD_X0 4
#define FIELD_Y0 13
#define FIELD_X1 35
#define FIELD_Y1 32

static int worker_at(int x, int y)
{
    if (cur_map != MAP_WILLOW_ACRE) return -1;
    for (int i = 0; i < FARM_WORKERS; i++) {
        const KinActor *k = &farm_kin[i];
        if (!k->shown) continue;
        if (k->a.x == x && k->a.y == y) return i;
        if (k->a.moving && k->a.x - DIR_DX[k->a.facing] == x && k->a.y - DIR_DY[k->a.facing] == y) return i;
    }
    return -1;
}

/* The Shelf slot of a worker (slots shift, so it is found by species and
 * potential), or -1 when it is no longer on the Shelf. */
static int worker_slot(const FarmWorker *w)
{
    if (!w->job) return -1;
    for (int i = 0; i < storage_count; i++)
        if (storage[i].species == w->species && storage[i].pot == w->pot) return i;
    return -1;
}

/* ================================================================ */
/*  Cells: look and solidity                                        */
/* ================================================================ */

static void meta_over(u16 mt, u16 mid[4], u16 top[4])
{
    const TilesetDef *t = tset();
    for (int i = 0; i < 4; i++) {
        if (t->meta_bottom[mt][i]) mid[i] = t->meta_bottom[mt][i];
        if (t->meta_top[mt][i]) top[i] = t->meta_top[mt][i];
    }
}

/* The overlay on a plot (0 = none) and, for trees, the crown drawn on the
 * cell above (*crown). */
static u16 plot_overlay(const FarmPlot *p, u16 *crown)
{
    *crown = 0;
    if (p->flags & PF_SPRINKLER) return MT_FA_SPRINKLER;
    if (!p->crop) return 0;
    int c = p->crop - 1, g = p->growth, target = crop_target(c);
    if (crop_is_tree(c)) {
        if (g * 3 < target) return MT_FA_SAPLING;
        if (g < target) {
            *crown = MT_FA_YOUNG_TOP;
            return MT_FA_YOUNG_BOTTOM;
        }
        if (g < crop_ripe_at(c)) {
            *crown = MT_FA_FRUIT_TOP;
            return MT_FA_FRUIT_BOTTOM;
        }
        *crown = c == CROP_APPLE ? MT_FA_APPLE_TOP : MT_FA_PEACH_TOP;
        return CROPS[c].ripe_mt;
    }
    if (g >= target) return CROPS[c].ripe_mt;
    if (p->flags & PF_REGROWN) return CROPS[c].grow_mt;
    int f = g * 8 / target;
    return f < 2 ? MT_FA_SEEDED : f < 4 ? MT_FA_SPROUT : CROPS[c].grow_mt;
}

static int farm_dyn_cell(int mx, int my, u16 bottom[4], u16 mid[4], u16 top[4])
{
    if (cur_map != MAP_WILLOW_ACRE) return 0;
    const TilesetDef *t = tset();
    int done = 0;
    int pi = farm_plot_at(mx, my);
    if (pi >= 0) {
        const FarmPlot *p = &farm.plots[pi];
        if (!plot_orchard[pi] && (p->flags & PF_TILLED)) {
            int wet = (p->flags & PF_WET) != 0, fert = (p->flags & (PF_FERT | PF_COMPOST | PF_MULCH)) != 0;
            u16 mt = wet ? (fert ? MT_FA_TILLED_WET_FERT : MT_FA_TILLED_WET) : (fert ? MT_FA_TILLED_FERT : MT_FA_TILLED);
            for (int i = 0; i < 4; i++) bottom[i] = t->meta_bottom[mt][i];
        }
        u16 crown, ov = plot_overlay(p, &crown);
        if (ov) meta_over(ov, mid, top);
        done = 1;
    }
    int below = farm_plot_at(mx, my + 1);
    if (below >= 0) {
        u16 crown;
        plot_overlay(&farm.plots[below], &crown);
        if (crown) {
            for (int i = 0; i < 4; i++)
                if (t->meta_top[crown][i]) top[i] = t->meta_top[crown][i];
            done = 1;
        }
    }
    int b = berry_obj_at(mx, my);
    if (b >= 0) {
        int patch = MAPS[cur_map].objs[b].arg;
        int c = berry_crop(patch);
        meta_over(berry_ripe(patch) ? CROPS[c].ripe_mt : CROPS[c].grow_mt, mid, top);
        done = 1;
    }
    return done;
}

/* The field's hook for cells that change at run time (field.c). */
static int dyn_cell(int mx, int my, u16 bottom[4], u16 mid[4], u16 top[4])
{
    return farm_dyn_cell(mx, my, bottom, mid, top) || travel_dyn_cell(mx, my, bottom, mid, top);
}

/* Extra attributes (field.c cell_attr): grown trees, sprinklers, workers
 * and berry bushes are solid. */
static int farm_cell_attr(int x, int y, int a)
{
    if (cur_map == MAP_WILLOW_ACRE) {
        int pi = farm_plot_at(x, y);
        if (pi >= 0 && ((farm.plots[pi].flags & PF_SPRINKLER) || plot_tree_up(&farm.plots[pi]))) a |= A_SOLID;
        if (worker_at(x, y) >= 0) a |= A_SOLID;
    }
    if (MAPS[cur_map].obj_count && berry_obj_at(x, y) >= 0) a |= A_SOLID;
    return a;
}

static void plot_redraw(int pi)
{
    field_redraw_cell(plot_x[pi], plot_y[pi]);
    field_redraw_cell(plot_x[pi], plot_y[pi] - 1);
}

/* ================================================================ */
/*  Field effects: particles, the plot cursor, toasts               */
/* ================================================================ */

#define OT_FARM 512
#define OT_FARM_BERRY OT_FARM            /* 2 frames x 4 tiles (off the farm) */
#define OT_FARM_FX (OT_FARM + 8)         /* FXT_COUNT tiles */
#define OT_FARM_CURSOR (OT_FARM + 16)    /* 4 tiles */
#define FARM_OBANK OBANK_ITEM_BALL       /* colours 9-15 */

enum { FXT_CLOD, FXT_DROP, FXT_SPARK, FXT_LEAF, FXT_SEED, FXT_COUNT };

/* 8x8 effect art: '.' clear, a-g = colours 9-15 (FX_PAL). */
static const char *const FX_ART[FXT_COUNT][8] = {
    { "........", "..aab...", ".aaaab..", ".aaabb..", "..abbb..", "...bb...", "........", "........" },
    { "...c....", "...c....", "..ccd...", "..cddd..", ".ccdddd.", ".cfddd..", "..ddd...", "........" },
    { "...e....", "...e....", "..efe...", "eeefeee.", "..efe...", "...e....", "...e....", "........" },
    { "........", ".....gg.", "...gggg.", "..ggggg.", ".gggg...", ".gg.....", "g.......", "........" },
    { "........", "...a....", "..aab...", "..abb...", "...b....", "........", "........", "........" },
};
static const u16 FX_PAL[7] = {
    RGB15(26, 19, 12), RGB15(15, 9, 5), RGB15(20, 26, 31), RGB15(8, 16, 30),
    RGB15(31, 27, 8), RGB15(31, 31, 31), RGB15(9, 22, 7),
};

typedef struct { s16 x, y; s8 vx, vy; u8 life, tile; } FarmParticle;   /* x, y: world pixels x4 */
#define PARTICLE_MAX 10
static FarmParticle particles[PARTICLE_MAX];
static int fx_freeze;               /* frames the player stands still while a tool works */

static void fx_load_farm(void)
{
    for (int t = 0; t < FXT_COUNT; t++) {
        u32 rows[8];
        for (int y = 0; y < 8; y++) {
            u32 r = 0;
            for (int x = 0; x < 8; x++) {
                char ch = FX_ART[t][y][x];
                if (ch >= 'a' && ch <= 'g') r |= (u32)(9 + ch - 'a') << (x * 4);
            }
            rows[y] = r;
        }
        copy32(VRAM_OBJ_TILES + (OT_FARM_FX + t) * 8, rows, 8);
    }
    /* the plot cursor: four white corner brackets with a dark edge */
    for (int q = 0; q < 4; q++) {
        u32 rows[8];
        for (int y = 0; y < 8; y++) {
            u32 r = 0;
            for (int x = 0; x < 8; x++) {
                int gx = (q & 1) ? 15 - (8 + x) : x, gy = (q & 2) ? 15 - (8 + y) : y;
                int v = 0;
                if ((gx < 5 && gy < 2) || (gy < 5 && gx < 2)) v = 14;
                else if ((gx < 6 && gy == 2 && gx >= 2) || (gy < 6 && gx == 2 && gy >= 2)) v = 10;
                r |= (u32)v << (x * 4);
            }
            rows[y] = r;
        }
        copy32(VRAM_OBJ_TILES + (OT_FARM_CURSOR + q) * 8, rows, 8);
    }
    for (int i = 0; i < 7; i++) obj_palette[FARM_OBANK * 16 + 9 + i] = FX_PAL[i];
}

static void fx_burst(int tile, int cx, int cy, int n)
{
    for (int k = 0; k < n; k++) {
        int slot = -1;
        for (int i = 0; i < PARTICLE_MAX; i++)
            if (!particles[i].life) {
                slot = i;
                break;
            }
        if (slot < 0) return;
        FarmParticle *p = &particles[slot];
        p->x = (s16)((cx * 16 + 4 + (int)rng_range(9) - 4) * 4);
        p->y = (s16)((cy * 16 + 4 + (int)rng_range(5) - 2) * 4);
        p->vx = (s8)((int)rng_range(9) - 4);
        p->vy = (s8)(tile == FXT_DROP ? 3 + (int)rng_range(3) : -6 - (int)rng_range(5));
        if (tile == FXT_DROP) p->y = (s16)(p->y - 40);
        p->life = (u8)(18 + rng_range(8));
        p->tile = (u8)tile;
    }
}

static void fx_update(void)
{
    for (int i = 0; i < PARTICLE_MAX; i++) {
        FarmParticle *p = &particles[i];
        if (!p->life) continue;
        p->life--;
        p->x = (s16)(p->x + p->vx);
        p->y = (s16)(p->y + p->vy);
        if (p->tile != FXT_DROP && p->tile != FXT_SPARK && (p->life & 1)) p->vy++;
    }
}

/* ---- toasts: one short line near the top of the screen ---- */

static struct { char text[40]; int timer, drawn; } toast;

static void farm_toast(const char *text)
{
    str_copy(toast.text, text);
    toast.timer = 100;
    toast.drawn = 0;
}

/* ================================================================ */
/*  Giving and taking                                               */
/* ================================================================ */

static void farm_give(int item, int qty)
{
    char msg[64];
    bag_add(item, qty);
    sfx_play(SFX_ITEM);
    str_copy(msg, "You received ");
    if (qty > 1) {
        str_put_int(msg, qty);
        str_put(msg, " ");
    }
    str_put(msg, ITEMS[item].name);
    str_put(msg, "!");
    dlg_say(msg);
}

/* ================================================================ */
/*  The day                                                         */
/* ================================================================ */

static char day_report[MSG_TEXT_MAX];

static void report_add(const char *s)
{
    if (str_len(day_report) + str_len(s) + 2 >= sizeof(day_report)) return;
    if (day_report[0]) str_put(day_report, " ");
    str_put(day_report, s);
}

static void plot_water(FarmPlot *p)
{
    if (!(p->flags & PF_TILLED) && !(p->crop && crop_is_tree(p->crop - 1))) return;
    p->flags |= PF_WET;
    if (p->flags & PF_MULCH) p->flags |= PF_WET2;
}

static int plot_harvest_roll(const FarmPlot *p)
{
    int care = p->care > 6 ? 6 : p->care, compost = (p->flags & PF_COMPOST) != 0;
    int perfect = 2 + compost * 8 + care * 2;
    int great = 12 + compost * 12 + ((p->flags & PF_FERT) ? 4 : 0) + care * 3;
    int r = (int)rng_range(100);
    return r < perfect ? 2 : r < perfect + great ? 1 : 0;
}

/* Pick a ripe plot: returns the number picked (quality in *q). */
static int plot_harvest(int pi, int *q)
{
    FarmPlot *p = &farm.plots[pi];
    int c = p->crop - 1;
    int quality = plot_harvest_roll(p);
    int n = CROPS[c].yield + quality;
    if (q) *q = quality;
    bag_add(crop_item(c), n);
    if (farm.harvested[c] < 65535) farm.harvested[c]++;
    if (quality == 1 && farm.great[c] < 65535) farm.great[c]++;
    if (quality == 2 && farm.perfect[c] < 65535) farm.perfect[c]++;
    if (CROPS[c].regrow) {
        p->growth = (u8)(crop_ripe_at(c) - CROPS[c].regrow * GROW_PER_DAY);
        p->flags |= PF_REGROWN;
    } else {
        p->crop = 0;
        p->growth = 0;
        p->care = 0;
        p->flags &= (u8)~(PF_FERT | PF_COMPOST | PF_MULCH | PF_WET2 | PF_REGROWN);
    }
    return n;
}

/* The workers' morning. Returns a sentence for the report (or ""). */
static void workers_work(int *guarded)
{
    int watered = 0, tended = 0, picked = 0, honey = 0, found = 0, left = 0;
    for (int wi = 0; wi < FARM_WORKERS; wi++) {
        FarmWorker *w = &farm.workers[wi];
        if (!w->job) continue;
        int slot = worker_slot(w);
        if (slot < 0) {   /* it left the Shelf (withdrawn or released) */
            w->job = 0;
            left++;
            continue;
        }
        BoxMon *b = &storage[slot];
        int fit = job_fit(w->job, b->species);
        int power = (fit == 2 ? 2 : 1) * (3 + b->level / 8);
        switch (w->job) {
        case JOB_WATER:
            for (int i = 0; i < FARM_PLOTS && power > 0; i++) {
                FarmPlot *p = &farm.plots[i];
                if (p->crop && !(p->flags & PF_WET) && (p->flags & PF_TILLED)) {
                    plot_water(p);
                    watered++;
                    power--;
                }
            }
            break;
        case JOB_TEND:
            for (int i = 0; i < FARM_PLOTS && power > 0; i++) {
                FarmPlot *p = &farm.plots[i];
                if (p->crop && !plot_ripe(p) && (i + gtime.day) % 3 != 0) {
                    p->growth++;
                    if (p->care < 15) p->care++;
                    tended++;
                    power--;
                }
            }
            break;
        case JOB_HARVEST:
            for (int i = 0; i < FARM_PLOTS && power > 0; i++)
                if (plot_ripe(&farm.plots[i])) {
                    picked += plot_harvest(i, 0);
                    power--;
                }
            break;
        case JOB_GUARD: *guarded += fit; break;
        case JOB_FORAGE: {
            int n = 1 + (fit == 2 && rng_range(2));
            for (int k = 0; k < n; k++) bag_add(FORAGE_FINDS[rng_range(sizeof(FORAGE_FINDS))], 1);
            found += n;
            break;
        }
        case JOB_HONEY: {
            int n = fit == 2 ? 1 + (int)rng_range(2) : (rng_range(10) < 4);
            bag_add(ITEM_GLOW_HONEY, n);
            honey += n;
            break;
        }
        }
        /* work builds bond and a little experience */
        if (b->bond < 254) b->bond = (u8)(b->bond + 2);
        b->xp += (u32)(6 + b->level * 2);
        while (b->level < MAX_LEVEL && b->xp >= xp_for_level(b->level + 1)) b->level++;
        w->level = b->level;
        if (w->days < 255) w->days++;
    }
    char s[96];
    if (watered || tended) {
        str_copy(s, "Your kin ");
        if (watered) {
            str_put(s, "watered ");
            str_put_int(s, watered);
            str_put(s, tended ? " plots and " : " plots.");
        }
        if (tended) {
            str_put(s, "tended ");
            str_put_int(s, tended);
            str_put(s, " crops.");
        }
        report_add(s);
    }
    if (picked) {
        str_copy(s, "They brought in ");
        str_put_int(s, picked);
        str_put(s, " crops.");
        report_add(s);
    }
    if (found) {
        str_copy(s, "A forager found ");
        str_put_int(s, found);
        str_put(s, found > 1 ? " materials." : " material.");
        report_add(s);
    }
    if (honey) report_add("The hives gave GLOW HONEY.");
    if (left) report_add("A farmhand left the Shelf, so its job is open.");
}

/* A new day began (time.c): growth, weather, workers, the bin. */
static void farm_new_day(void)
{
    day_report[0] = 0;
    char s[64];
    if (farm.bin_value) {
        money = clampi(money + (int)farm.bin_value, 0, 9999999);
        farm.earned += farm.bin_value;
        str_copy(s, "The bin paid ");
        str_put_int(s, (int)farm.bin_value);
        str_put(s, "c.");
        report_add(s);
        farm.bin_value = 0;
        farm.bin_items = 0;
    }
    /* growth: watered crops grow, trees always do; then the soil dries */
    for (int i = 0; i < FARM_PLOTS; i++) {
        FarmPlot *p = &farm.plots[i];
        if (p->crop) {
            int c = p->crop - 1;
            int wet = (p->flags & PF_WET) != 0;
            if (wet || crop_is_tree(c)) {
                int g = p->growth + GROW_PER_DAY + ((p->flags & PF_FERT) ? 1 : 0);
                p->growth = (u8)clampi(g, 0, crop_ripe_at(c));
            }
        }
        if (p->flags & PF_WET2) p->flags &= (u8)~PF_WET2;   /* mulch kept it damp one more day */
        else p->flags &= (u8)~PF_WET;
    }
    /* berry patches regrow */
    for (int i = 0; i < FARM_BERRIES; i++) {
        BerryPatch *b = &farm.berries[i];
        b->growth = (u8)clampi(b->growth + GROW_PER_DAY, 0, BERRY_RIPE);
    }
    if (!farm.owned) return;
    /* rain and sprinklers water the new day */
    if (gtime.weather == WEATHER_RAIN) {
        for (int i = 0; i < FARM_PLOTS; i++) plot_water(&farm.plots[i]);
        report_add("It's raining, so the crops are watered.");
    }
    farm_geom_init();
    for (int i = 0; i < plot_count; i++) {
        if (!(farm.plots[i].flags & PF_SPRINKLER)) continue;
        for (int dy = -1; dy <= 1; dy++)
            for (int dx = -1; dx <= 1; dx++) {
                int n = plot_at_xy(plot_x[i] + dx, plot_y[i] + dy);
                if (n >= 0 && n != i) plot_water(&farm.plots[n]);
            }
    }
    int guarded = 0;
    workers_work(&guarded);
    /* crows, when nobody keeps them off */
    int growing = 0;
    for (int i = 0; i < FARM_PLOTS; i++)
        if (farm.plots[i].crop && !crop_is_tree(farm.plots[i].crop - 1)) growing++;
    int crow_odds = guarded >= 2 ? 0 : guarded == 1 ? 12 : 25;
    farm.last_crows = 0;
    if (growing >= 6 && (int)rng_range(100) < crow_odds) {
        int hit = 0;
        for (int k = 0; k < 3; k++) {
            int i = (int)rng_range(FARM_PLOTS);
            FarmPlot *p = &farm.plots[i];
            if (!p->crop || crop_is_tree(p->crop - 1) || p->growth < GROW_PER_DAY) continue;
            p->growth = (u8)(p->growth - GROW_PER_DAY);
            p->flags &= (u8)~PF_REGROWN;
            hit++;
        }
        if (hit) {
            farm.last_crows = (u8)hit;
            report_add("Crows pecked at the crops! A GUARD kin would keep them off.");
        }
    }
    /* processors finish */
    for (int i = 0; i < PROC_COUNT; i++)
        if (farm.procs[i].recipe && farm.procs[i].ready_day == gtime.day) {
            str_copy(s, "The ");
            str_put(s, PROC_NAMES[i]);
            str_put(s, " is done.");
            report_add(s);
        }
    if (farm.can_water < CAN_MAX && gtime.weather == WEATHER_RAIN) farm.can_water = CAN_MAX;
    if (cur_map == MAP_WILLOW_ACRE) ring_invalidate();
    if (day_report[0]) {
        char msg[MSG_TEXT_MAX];
        str_copy(msg, "WILLOW ACRE, DAY ");
        str_put_int(msg, gtime.day);
        str_put(msg, ": ");
        if (str_len(msg) + str_len(day_report) < sizeof(msg)) str_put(msg, day_report);
        dlg_say(msg);
    }
}

/* ================================================================ */
/*  The tool ring                                                   */
/* ================================================================ */

#define TOOL_HOE (-1)
#define TOOL_CAN (-2)
static const s16 FARM_TOOLS[] = {
    TOOL_HOE, TOOL_CAN,
    ITEM_SEED_RADISH, ITEM_SEED_CARROT, ITEM_SEED_POTATO, ITEM_SEED_GLOWBERRY, ITEM_SEED_EMBERBERRY,
    ITEM_SEED_TIDEBERRY, ITEM_SEED_CHILI, ITEM_SEED_TOMATO, ITEM_SEED_CORN, ITEM_SEED_SUNFLOWER,
    ITEM_SEED_PUMPKIN, ITEM_SEED_MOTEBLOOM, ITEM_SAPLING_APPLE, ITEM_SAPLING_PEACH,
    ITEM_FERTILIZER, ITEM_RICH_COMPOST, ITEM_GROW_MULCH, ITEM_SPRINKLER,
};
#define FARM_TOOL_COUNT ((int)(sizeof(FARM_TOOLS) / sizeof(FARM_TOOLS[0])))

static int tool_have(int t)
{
    int v = FARM_TOOLS[t];
    if (v == TOOL_HOE) return bag[ITEM_HOE] > 0;
    if (v == TOOL_CAN) return bag[ITEM_WATERING_CAN] > 0;
    return bag[v] > 0;
}

/* The selected tool (a FARM_TOOLS index that you still have), or -1. */
static int tool_current(void)
{
    int t = farm.tool < FARM_TOOL_COUNT ? farm.tool : 0;
    if (tool_have(t)) return t;
    for (int k = 1; k < FARM_TOOL_COUNT; k++) {
        int n = (t + k) % FARM_TOOL_COUNT;
        if (tool_have(n)) {
            farm.tool = (u8)n;
            return n;
        }
    }
    return -1;
}

static void tool_label(int t, char *buf)
{
    buf[0] = 0;
    if (t < 0) return;
    int v = FARM_TOOLS[t];
    if (v == TOOL_HOE) {
        str_copy(buf, "HOE");
    } else if (v == TOOL_CAN) {
        str_copy(buf, "CAN ");
        str_put_int(buf, farm.can_water);
        str_put(buf, "/");
        str_put_int(buf, CAN_MAX);
    } else {
        str_copy(buf, ITEMS[v].name);
        str_put(buf, " x");
        str_put_int(buf, bag[v]);
    }
}

static void tool_cycle(int dir)
{
    int t = tool_current();
    if (t < 0) return;
    for (int k = 1; k < FARM_TOOL_COUNT; k++) {
        int n = (t + dir * k + FARM_TOOL_COUNT * 2) % FARM_TOOL_COUNT;
        if (tool_have(n)) {
            farm.tool = (u8)n;
            break;
        }
    }
    sfx_play(SFX_CURSOR);
}

/* Select an item (or the HOE / CAN) as the tool, if it is in the ring. */
static int tool_select_item(int item)
{
    for (int t = 0; t < FARM_TOOL_COUNT; t++) {
        int v = FARM_TOOLS[t];
        int match = v == item || (v == TOOL_HOE && item == ITEM_HOE) || (v == TOOL_CAN && item == ITEM_WATERING_CAN);
        if (match) {
            farm.tool = (u8)t;
            return 1;
        }
    }
    return 0;
}

static int farm_here(void)
{
    return cur_map == MAP_WILLOW_ACRE && farm.owned;
}

/* ================================================================ */
/*  Working a plot                                                  */
/* ================================================================ */

static void tool_done(int fx_tile, int x, int y, int sfx, const char *msg)
{
    fx_burst(fx_tile, x, y, fx_tile == FXT_DROP ? 5 : 4);
    sfx_play(sfx);
    fx_freeze = 12;
    if (msg) farm_toast(msg);
}

static void tool_fail(const char *msg)
{
    sfx_play(SFX_ERROR);
    farm_toast(msg);
}

static void sprinkler_answer(int c)
{
    int pi = farm_plot_at(player.x + DIR_DX[player.facing], player.y + DIR_DY[player.facing]);
    if (c != 0 || pi < 0 || !(farm.plots[pi].flags & PF_SPRINKLER)) return;
    farm.plots[pi].flags &= (u8)~PF_SPRINKLER;
    bag_add(ITEM_SPRINKLER, 1);
    sfx_play(SFX_ITEM);
    plot_redraw(pi);
}

/* A on a plot. Returns 1 (a plot always answers). */
static int farm_use_on_plot(int pi)
{
    FarmPlot *p = &farm.plots[pi];
    int x = plot_x[pi], y = plot_y[pi];
    char msg[40];
    if (plot_ripe(p)) {
        int c = p->crop - 1, q;
        int n = plot_harvest(pi, &q);
        str_copy(msg, "+");
        str_put_int(msg, n);
        str_put(msg, " ");
        str_put(msg, ITEMS[crop_item(c)].name);
        if (q) str_put(msg, q == 2 ? "  PERFECT!" : "  GREAT!");
        tool_done(q ? FXT_SPARK : FXT_LEAF, x, y, q == 2 ? SFX_SPARKLE : SFX_ITEM, msg);
        plot_redraw(pi);
        return 1;
    }
    if (p->flags & PF_SPRINKLER) {
        dlg_ask("A SPRINKLER. Pick it up?", YES_NO, 2, sprinkler_answer);
        return 1;
    }
    int t = tool_current();
    if (t < 0) {
        tool_fail("You have no farm tools.");
        return 1;
    }
    int v = FARM_TOOLS[t];
    if (v == TOOL_HOE) {
        if (plot_orchard[pi]) tool_fail("Plant saplings right in the mound.");
        else if (p->crop) tool_fail("Something is growing here.");
        else if (p->flags & PF_TILLED) tool_fail("It's already tilled.");
        else {
            p->flags |= PF_TILLED;
            tool_done(FXT_CLOD, x, y, SFX_ROCK, 0);
        }
    } else if (v == TOOL_CAN) {
        if (!farm.can_water) tool_fail("The can is empty. Fill it at the pond.");
        else if (!(p->flags & PF_TILLED) && !p->crop) tool_fail("Till the soil first.");
        else if (p->flags & PF_WET) tool_fail("It's already watered.");
        else {
            plot_water(p);
            farm.can_water--;
            tool_done(FXT_DROP, x, y, SFX_SPLASH, 0);
        }
    } else if (ITEMS[v].kind == IK_PLANT) {
        int c = ITEMS[v].param;
        if (p->crop) tool_fail("Something is growing here.");
        else if (crop_is_tree(c) && !plot_orchard[pi]) tool_fail("Saplings go in the orchard mounds.");
        else if (!crop_is_tree(c) && plot_orchard[pi]) tool_fail("The mounds are for fruit trees.");
        else if (!crop_is_tree(c) && !(p->flags & PF_TILLED)) tool_fail("Till the soil with the HOE first.");
        else {
            p->crop = (u8)(c + 1);
            p->growth = 0;
            p->care = 0;
            p->flags &= (u8)~PF_REGROWN;
            if (crop_is_tree(c)) p->flags |= PF_TILLED;
            bag[v]--;
            tool_done(FXT_SEED, x, y, SFX_LEAF, 0);
        }
    } else if (ITEMS[v].kind == IK_FERTILIZER) {
        static const u8 FLAG[3] = { PF_FERT, PF_COMPOST, PF_MULCH };
        int f = FLAG[clampi(ITEMS[v].param, 0, 2)];
        if (!(p->flags & PF_TILLED)) tool_fail("Till the soil first.");
        else if (p->flags & f) tool_fail("That's already been spread here.");
        else {
            p->flags |= (u8)f;
            if (f == PF_MULCH && (p->flags & PF_WET)) p->flags |= PF_WET2;
            bag[v]--;
            tool_done(FXT_SPARK, x, y, SFX_GROW, 0);
        }
    } else if (v == ITEM_SPRINKLER) {
        if (p->crop || plot_orchard[pi]) tool_fail("Put it on bare soil.");
        else {
            p->flags |= PF_SPRINKLER;
            bag[v]--;
            tool_done(FXT_DROP, x, y, SFX_CONFIRM, "It waters the 8 plots around it.");
        }
    }
    plot_redraw(pi);
    return 1;
}

/* ================================================================ */
/*  Shipping bin, processors, chest                                 */
/* ================================================================ */

static int shippable(int item)
{
    return ITEMS[item].kind == IK_CROP && farm_value(item) > 0;
}

static const char *const BIN_MENU[3] = { "SHIP ALL", "KEEP ONE EACH", "CANCEL" };

static void bin_answer(int c)
{
    if (c < 0 || c > 1) return;
    int items = 0, value = 0;
    for (int i = 0; i < ITEM_COUNT; i++) {
        if (!shippable(i) || bag[i] <= 0) continue;
        int n = c == 1 ? bag[i] - 1 : bag[i];
        if (n <= 0) continue;
        bag[i] -= n;
        items += n;
        value += n * farm_value(i);
    }
    if (!items) {
        dlg_say("You have nothing to ship.");
        return;
    }
    farm.bin_value += (u32)value;
    farm.bin_items = (u16)clampi(farm.bin_items + items, 0, 65535);
    sfx_play(SFX_BUY);
    char msg[120];
    str_copy(msg, "You put ");
    str_put_int(msg, items);
    str_put(msg, items > 1 ? " items" : " item");
    str_put(msg, " in the bin, worth ");
    str_put_int(msg, value);
    str_put(msg, "c. You'll be paid tomorrow morning.");
    dlg_say(msg);
}

static void farm_ship_open(void)
{
    int any = 0;
    for (int i = 0; i < ITEM_COUNT; i++)
        if (shippable(i) && bag[i] > 0) any = 1;
    char msg[120];
    if (farm.bin_value) {
        str_copy(msg, "The bin holds ");
        str_put_int(msg, (int)farm.bin_value);
        str_put(msg, "c of goods for tomorrow.");
    } else {
        str_copy(msg, "The SHIPPING BIN. Produce put in is paid for next morning.");
    }
    if (!any) {
        str_put(msg, " You have no produce to ship.");
        dlg_say(msg);
        return;
    }
    dlg_ask(msg, BIN_MENU, 3, bin_answer);
}

/* ---- processors ---- */

static int proc_open_kind;
static u8 proc_choice_recipe[8];
static const char *proc_choice_names[8];

static void proc_answer(int c)
{
    if (c < 0 || c >= 8 || !proc_choice_names[c] || proc_choice_recipe[c] == 0xFF) return;
    int r = proc_choice_recipe[c];
    const Recipe *rc = &RECIPES[r];
    int item = crop_item(rc->crop);
    int batches = bag[item] / rc->in;
    if (batches > PROC_BATCH_MAX) batches = PROC_BATCH_MAX;
    if (batches <= 0) return;
    bag[item] -= batches * rc->in;
    FarmProc *p = &farm.procs[rc->proc];
    p->recipe = (u8)(r + 1);
    p->batches = (u8)batches;
    p->ready_day = (u16)(gtime.day + rc->days);
    sfx_play(SFX_CONFIRM);
    char msg[120];
    str_copy(msg, "You put in ");
    str_put_int(msg, batches * rc->in);
    str_put(msg, " ");
    str_put(msg, ITEMS[item].name);
    str_put(msg, rc->days > 1 ? ". Come back in two mornings." : ". Come back tomorrow morning.");
    dlg_say(msg);
}

static void farm_proc_open(int kind)
{
    FarmProc *p = &farm.procs[kind];
    char msg[120];
    if (p->recipe) {
        const Recipe *rc = &RECIPES[p->recipe - 1];
        if (gtime.day >= p->ready_day) {
            int n = p->batches;
            p->recipe = p->batches = 0;
            farm_give(rc->out, n);
            return;
        }
        str_copy(msg, "The ");
        str_put(msg, ITEMS[rc->out].name);
        str_put(msg, p->ready_day - gtime.day > 1 ? " needs two more mornings." : " will be ready tomorrow morning.");
        dlg_say(msg);
        return;
    }
    proc_open_kind = kind;
    int n = 0;
    for (int r = 0; r < RECIPE_COUNT && n < 7; r++) {
        if (RECIPES[r].proc != kind || bag[crop_item(RECIPES[r].crop)] < RECIPES[r].in) continue;
        proc_choice_recipe[n] = (u8)r;
        proc_choice_names[n++] = ITEMS[crop_item(RECIPES[r].crop)].name;
    }
    str_copy(msg, "The ");
    str_put(msg, PROC_NAMES[kind]);
    if (!n) {
        str_put(msg, kind == PROC_JAR ? ". Berries and fruit become jam, vegetables pickles."
                     : kind == PROC_PRESS ? ". It presses berries, apples and peaches into drinks."
                                          : ". It dries chilies, fruit and sunflower heads.");
        str_put(msg, " You have nothing it takes.");
        dlg_say(msg);
        return;
    }
    proc_choice_recipe[n] = 0xFF;
    proc_choice_names[n++] = "CANCEL";
    str_put(msg, ". What goes in?");
    dlg_ask(msg, proc_choice_names, n, proc_answer);
}

/* ---- the storage chest ---- */

static const char *const CHEST_MENU[3] = { "STORE PRODUCE", "TAKE ALL", "CANCEL" };

static int chest_total(void)
{
    int n = 0;
    for (int i = 0; i < FARM_CHEST; i++) n += farm.chest[i].count;
    return n;
}

static void chest_answer(int c)
{
    char msg[80];
    int moved = 0;
    if (c == 0) {
        for (int it = 0; it < ITEM_COUNT; it++) {
            if (ITEMS[it].pocket != POCKET_FARM || ITEMS[it].kind != IK_CROP || bag[it] <= 0) continue;
            u16 code = item_code(it);
            int slot = -1;
            for (int s = 0; s < FARM_CHEST && slot < 0; s++)
                if (farm.chest[s].count && farm.chest[s].code == code) slot = s;
            for (int s = 0; s < FARM_CHEST && slot < 0; s++)
                if (!farm.chest[s].count) slot = s;
            if (slot < 0) break;
            int n = bag[it];
            if (farm.chest[slot].count + n > 999) n = 999 - farm.chest[slot].count;
            farm.chest[slot].code = code;
            farm.chest[slot].count = (u16)(farm.chest[slot].count + n);
            bag[it] -= n;
            moved += n;
        }
        str_copy(msg, moved ? "You stored " : "You have no produce to store.");
    } else if (c == 1) {
        for (int s = 0; s < FARM_CHEST; s++) {
            if (!farm.chest[s].count) continue;
            int it = item_from_code(farm.chest[s].code);
            if (it < 0) continue;
            int n = farm.chest[s].count;
            if (bag[it] + n > 999) n = 999 - bag[it];
            bag_add(it, n);
            farm.chest[s].count = (u16)(farm.chest[s].count - n);
            moved += n;
        }
        str_copy(msg, moved ? "You took out " : "The chest is empty.");
    } else {
        return;
    }
    if (moved) {
        str_put_int(msg, moved);
        str_put(msg, moved > 1 ? " things." : " thing.");
        sfx_play(SFX_ITEM);
    }
    dlg_say(msg);
}

static void farm_chest_open(void)
{
    char msg[80];
    str_copy(msg, "The storage chest holds ");
    str_put_int(msg, chest_total());
    str_put(msg, " things.");
    dlg_ask(msg, CHEST_MENU, 3, chest_answer);
}

/* ================================================================ */
/*  The WORK BOARD screen                                           */
/* ================================================================ */

static struct {
    int state;          /* 0 slots, 1 choosing a kin */
    int cursor;         /* slot 0..3 */
    int lcursor, lscroll;
} wb;
#define WB_ROWS 7

static int worker_of_slot(int shelf_slot)
{
    for (int i = 0; i < FARM_WORKERS; i++)
        if (farm.workers[i].job && worker_slot(&farm.workers[i]) == shelf_slot) return i;
    return -1;
}

static void wb_redraw(void)
{
    char buf[48];
    screen_begin(0);
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    text_draw(12, 8, "WORK BOARD");
    text_draw_right(228, 8, wb.state ? "PICK A KIN" : "FARM JOBS");
    if (wb.state == 0) {
        canvas_window(0, 3, CANVAS_COLS, 11, WIN_STD);
        for (int i = 0; i < FARM_WORKERS; i++) {
            const FarmWorker *w = &farm.workers[i];
            int y = 32 + i * LINE_H * 2 - 4;
            if (i == wb.cursor) text_draw(10, y, "{");
            buf[0] = 0;
            str_put_int(buf, i + 1);
            text_draw(20, y, buf);
            text_draw_col(36, y, JOB_NAMES[w->job], INK_BLUE, INK_BLUE_SH);
            if (w->job) {
                str_copy(buf, SPECIES[w->species].name);
                str_put(buf, " Lv");
                str_put_int(buf, w->level);
                text_draw(100, y, buf);
                int fit = job_fit(w->job, w->species);
                text_draw_col(196, y, fit == 2 ? "GOOD" : "OK", fit == 2 ? INK_GREEN : INK_DARK,
                              fit == 2 ? INK_GREEN_SH : INK_SHADOW);
            } else {
                text_draw(100, y, "(free)");
            }
        }
        text_draw_col(16, 94, "^/}: slot  </>: job  A: kin  B: done", INK_BLUE, INK_BLUE_SH);
        canvas_window(0, 14, CANVAS_COLS, 6, WIN_STD);
        char wrapped[160];
        text_wrap(wrapped, JOB_DESC[farm.workers[wb.cursor].job], 216);
        text_draw(12, 120, wrapped);
        return;
    }
    /* the Shelf list: (NOBODY) first */
    canvas_window(0, 3, CANVAS_COLS, 17, WIN_STD);
    int job = farm.workers[wb.cursor].job;
    for (int r = 0; r < WB_ROWS; r++) {
        int idx = wb.lscroll + r;
        if (idx > storage_count) break;
        int y = 32 + r * LINE_H;
        if (idx == wb.lcursor) text_draw(10, y, "{");
        if (idx == 0) {
            text_draw(20, y, "(NOBODY)");
            continue;
        }
        const BoxMon *b = &storage[idx - 1];
        str_copy(buf, SPECIES[b->species].name);
        text_draw(20, y, buf);
        buf[0] = 0;
        str_put(buf, "Lv");
        str_put_int(buf, b->level);
        text_draw(104, y, buf);
        int other = worker_of_slot(idx - 1);
        if (other >= 0 && other != wb.cursor) text_draw_col(140, y, "BUSY", INK_RED, INK_RED_SH);
        int fit = job ? job_fit(job, b->species) : 0;
        int best = job_best(b->species);
        str_copy(buf, fit == 2 ? "GOOD" : JOB_NAMES[best]);
        text_draw_col(184, y, buf, fit == 2 ? INK_GREEN : INK_BLUE, fit == 2 ? INK_GREEN_SH : INK_BLUE_SH);
    }
    if (!storage_count) text_draw(20, 32 + LINE_H, "Your Shelf is empty.");
    text_draw_col(16, 146, "Kin on the Shelf can work here.", INK_BLUE, INK_BLUE_SH);
}

static void wb_close(void)
{
    canvas_clear();
    field_setup_bg();
    field_load_tileset();
    game_mode = MODE_FIELD;
}

static void wb_update(void)
{
    if (wb.state == 0) {
        int old = wb.cursor;
        if (key_rep(KEY_UP)) wb.cursor = (wb.cursor + FARM_WORKERS - 1) % FARM_WORKERS;
        if (key_rep(KEY_DOWN)) wb.cursor = (wb.cursor + 1) % FARM_WORKERS;
        FarmWorker *w = &farm.workers[wb.cursor];
        if ((key_rep(KEY_LEFT) || key_rep(KEY_RIGHT)) && w->job) {
            int d = key_rep(KEY_LEFT) ? JOB_COUNT - 2 : 1;
            w->job = (u8)(1 + (w->job - 1 + d) % (JOB_COUNT - 1));
            sfx_play(SFX_CURSOR);
            wb_redraw();
        }
        if (old != wb.cursor) {
            sfx_play(SFX_CURSOR);
            wb_redraw();
        }
        if (key_hit(KEY_A)) {
            sfx_play(SFX_CONFIRM);
            wb.state = 1;
            wb.lcursor = wb.lscroll = 0;
            int cur = worker_slot(w);
            if (cur >= 0) {
                wb.lcursor = cur + 1;
                wb.lscroll = clampi(wb.lcursor - WB_ROWS / 2, 0, storage_count + 1 > WB_ROWS ? storage_count + 1 - WB_ROWS : 0);
            }
            wb_redraw();
        } else if (key_hit(KEY_B)) {
            sfx_play(SFX_CANCEL);
            wb_close();
        }
        return;
    }
    int old = wb.lcursor, n = storage_count + 1;
    if (key_rep(KEY_UP)) wb.lcursor = (wb.lcursor + n - 1) % n;
    if (key_rep(KEY_DOWN)) wb.lcursor = (wb.lcursor + 1) % n;
    if (key_rep(KEY_LEFT)) wb.lcursor = clampi(wb.lcursor - WB_ROWS, 0, n - 1);
    if (key_rep(KEY_RIGHT)) wb.lcursor = clampi(wb.lcursor + WB_ROWS, 0, n - 1);
    if (wb.lcursor < wb.lscroll) wb.lscroll = wb.lcursor;
    if (wb.lcursor >= wb.lscroll + WB_ROWS) wb.lscroll = wb.lcursor - WB_ROWS + 1;
    if (old != wb.lcursor) {
        sfx_play(SFX_CURSOR);
        wb_redraw();
    }
    if (key_hit(KEY_B)) {
        sfx_play(SFX_CANCEL);
        wb.state = 0;
        wb_redraw();
    } else if (key_hit(KEY_A)) {
        FarmWorker *w = &farm.workers[wb.cursor];
        if (wb.lcursor == 0) {
            w->job = 0;
            w->species = 0;
        } else {
            int s = wb.lcursor - 1, other = worker_of_slot(s);
            if (other >= 0 && other != wb.cursor) {
                sfx_play(SFX_ERROR);
                return;
            }
            const BoxMon *b = &storage[s];
            if (!w->job) w->job = (u8)job_best(b->species);
            w->species = b->species;
            w->pot = b->pot;
            w->level = b->level;
            w->days = 0;
        }
        sfx_play(SFX_CONFIRM);
        wb.state = 0;
        wb_redraw();
    }
}

static void farm_workboard_open(void)
{
    wb.state = 0;
    wb.cursor = 0;
    ext_open(wb_update, 0, 0);
    wb_redraw();
}

/* ================================================================ */
/*  Berry patches                                                   */
/* ================================================================ */

/* A wild berry patch (OBJ_BERRY, arg = patch id 0..63) was examined. */
static int farm_berry_interact(int patch)
{
    if (patch < 0 || patch >= FARM_BERRIES) return 0;
    BerryPatch *b = &farm.berries[patch];
    int c = berry_crop(patch);
    if (b->growth < BERRY_RIPE) {
        dlg_say(b->growth ? "Little green berries are forming. They'll be ripe in a day or two."
                          : "The bush has been picked clean. Berries grow back in a few days.");
        return 1;
    }
    int n = 2 + (int)rng_range(2);
    b->growth = 0;
    if (b->picks < 255) b->picks++;
    char msg[64];
    str_copy(msg, "You picked ");
    str_put_int(msg, n);
    str_put(msg, " ");
    str_put(msg, ITEMS[crop_item(c)].name);
    str_put(msg, "!");
    bag_add(crop_item(c), n);
    sfx_play(SFX_ITEM);
    dlg_say(msg);
    return 1;
}

/* Berry sprites off the farm: the crop art of ts_farm.py, squeezed into
 * colours 9-15 of the satchel palette (other tilesets' BG palettes are not
 * ours). */
static void berry_sprite_load(int crop)
{
    const TilesetDef *t = &TILESETS[TS_FARM];
    u16 mts[2] = { CROPS[crop].grow_mt, CROPS[crop].ripe_mt };
    static u8 pix[2][4][64];
    u16 col[32], freq[32];
    u8 grp[32];
    int nc = 0;
    for (int f = 0; f < 2; f++)
        for (int q = 0; q < 4; q++) {
            u16 e = t->meta_bottom[mts[f]][q];
            const u32 *src = t->tiles + (e & 1023) * 8;
            for (int y = 0; y < 8; y++)
                for (int x = 0; x < 8; x++) {
                    int sx = (e & 0x400) ? 7 - x : x, sy = (e & 0x800) ? 7 - y : y;
                    int v = e ? (int)((src[sy] >> (sx * 4)) & 15) : 0;
                    u8 slot = 0xFF;
                    if (v) {
                        u16 c = t->palettes[e >> 12][v];
                        for (int k = 0; k < nc; k++)
                            if (col[k] == c) slot = (u8)k;
                        if (slot == 0xFF && nc < 32) {
                            col[nc] = c;
                            freq[nc] = 0;
                            slot = (u8)nc++;
                        }
                        if (slot != 0xFF) freq[slot]++;
                    }
                    pix[f][q][y * 8 + x] = slot;
                }
        }
    /* merge the closest colours until 7 are left */
    u8 alive[32];
    for (int i = 0; i < nc; i++) {
        grp[i] = (u8)i;
        alive[i] = 1;
    }
    int left = nc;
    while (left > 7) {
        int ba = -1, bb = -1, bd = 1 << 30;
        for (int a = 0; a < nc; a++) {
            if (!alive[a]) continue;
            for (int b = a + 1; b < nc; b++) {
                if (!alive[b]) continue;
                int dr = (col[a] & 31) - (col[b] & 31), dg = ((col[a] >> 5) & 31) - ((col[b] >> 5) & 31);
                int db = ((col[a] >> 10) & 31) - ((col[b] >> 10) & 31);
                int d = dr * dr * 3 + dg * dg * 4 + db * db * 2;
                if (d < bd) {
                    bd = d;
                    ba = a;
                    bb = b;
                }
            }
        }
        if (freq[bb] > freq[ba]) col[ba] = col[bb];
        freq[ba] = (u16)(freq[ba] + freq[bb]);
        alive[bb] = 0;
        for (int i = 0; i < nc; i++)
            if (grp[i] == bb) grp[i] = (u8)ba;
        left--;
    }
    u8 out_index[32];
    int k = 0;
    for (int i = 0; i < nc; i++)
        if (alive[i]) {
            out_index[i] = (u8)(9 + k);
            obj_palette[FARM_OBANK * 16 + 9 + k] = col[i];
            k++;
        }
    for (int f = 0; f < 2; f++)
        for (int q = 0; q < 4; q++) {
            u32 rows[8];
            for (int y = 0; y < 8; y++) {
                u32 r = 0;
                for (int x = 0; x < 8; x++) {
                    u8 s = pix[f][q][y * 8 + x];
                    if (s != 0xFF) r |= (u32)out_index[grp[s]] << (x * 4);
                }
                rows[y] = r;
            }
            copy32(VRAM_OBJ_TILES + (OT_FARM_BERRY + f * 4 + q) * 8, rows, 8);
        }
}

/* ================================================================ */
/*  Workers walking on the farm                                     */
/* ================================================================ */

static void workers_place(void)
{
    for (int i = 0; i < FARM_WORKERS; i++) {
        farm_kin[i].shown = 0;
        const FarmWorker *w = &farm.workers[i];
        if (!w->job || cur_map != MAP_WILLOW_ACRE || worker_slot(w) < 0) continue;
        for (int tries = 0; tries < 40; tries++) {
            int x = FIELD_X0 + (int)rng_range(FIELD_X1 - FIELD_X0 + 1);
            int y = FIELD_Y0 + (int)rng_range(FIELD_Y1 - FIELD_Y0 + 1);
            if (!cell_walkable(x, y) || (x == player.x && y == player.y)) continue;
            int lustrous = (storage[worker_slot(w)].flags & MF_LUSTROUS) != 0;
            kin_place(&farm_kin[i], w->species, lustrous, x, y, (int)rng_range(4));
            farm_kin_timer[i] = (u16)(30 + rng_range(90));
            break;
        }
    }
}

static void workers_update(void)
{
    for (int i = 0; i < FARM_WORKERS; i++) {
        KinActor *k = &farm_kin[i];
        if (!k->shown) continue;
        if (k->a.moving) {
            actor_step(&k->a, 1);
            continue;
        }
        if (farm_kin_timer[i]) {
            farm_kin_timer[i]--;
            continue;
        }
        farm_kin_timer[i] = (u16)(40 + rng_range(100));
        int dir = (int)rng_range(4);
        int nx = k->a.x + DIR_DX[dir], ny = k->a.y + DIR_DY[dir];
        k->a.facing = (u8)dir;
        if (nx < FIELD_X0 || ny < FIELD_Y0 || nx > FIELD_X1 || ny > FIELD_Y1) continue;
        if ((nx == player.x && ny == player.y) || (follower_active() && nx == follower.a.x && ny == follower.a.y))
            continue;
        k->shown = 0;           /* don't block itself */
        int ok = cell_walkable(nx, ny) && worker_at(nx, ny) < 0;
        k->shown = 1;
        if (ok) actor_start_move(&k->a, dir);
    }
}

/* Kin sprites the field draws with its own (field.c field_draw_sprites). */
static int farm_field_kin(const KinActor **out)
{
    int n = 0;
    if (cur_map != MAP_WILLOW_ACRE) return 0;
    for (int i = 0; i < FARM_WORKERS; i++)
        if (farm_kin[i].shown) out[n++] = &farm_kin[i];
    return n;
}

/* ================================================================ */
/*  Map load, per-frame work, drawing                               */
/* ================================================================ */

/* Clear a decor instance's cells (the gate and sign once you own the farm). */
static void decor_remove_kind(int kind)
{
    const MapDef *m = &MAPS[cur_map];
    for (int i = 0; i < m->decor_count; i++) {
        if (m->decor[i].kind != kind) continue;
        const DecorDef *d = &DECOR_DEFS[m->tileset][kind];
        for (int dy = 0; dy < d->h; dy++)
            for (int dx = 0; dx < d->w; dx++) {
                int x = m->decor[i].x + dx, y = m->decor[i].y + dy;
                if (x < map_w && y < map_h) {
                    map_decor[y * map_w + x] = 0;
                    field_redraw_cell(x, y);
                }
            }
    }
}

/* Called at the end of every map load (field.c map_load). */
static void farm_map_loaded(void)
{
    farm_geom_init();
    for (int i = 0; i < PARTICLE_MAX; i++) particles[i].life = 0;
    for (int i = 0; i < FARM_WORKERS; i++) farm_kin[i].shown = 0;
    fx_freeze = 0;
    if (cur_map == MAP_WILLOW_ACRE) {
        fx_load_farm();
        if (farm.owned) {
            decor_remove_kind(DK_FARM_GATE);
            decor_remove_kind(DK_FOR_SALE);
            workers_place();
        }
        return;
    }
    const MapDef *m = &MAPS[cur_map];
    for (int i = 0; i < m->obj_count; i++)
        if (m->objs[i].kind == OBJ_BERRY) {
            berry_sprite_load(berry_crop(m->objs[i].arg));
            break;
        }
}

/* Per field frame (time.c time_tick): the tool ring, effects, workers. */
static void farm_tick(void)
{
    if (fx_freeze > 0) {
        fx_freeze--;
        keys_now = 0;           /* the player stands still while the tool works */
    }
    fx_update();
    if (cur_map != MAP_WILLOW_ACRE) return;
    workers_update();
    if (farm.owned && !player.moving) {
        if (key_hit(KEY_L)) tool_cycle(-1);
        if (key_hit(KEY_R)) tool_cycle(1);
    }
}

/* ---- canvas labels in the field: clock, tool, toast ---- */

static int tool_shown = -2;
static char tool_shown_text[32];

static void farm_canvas_draw(void)
{
    static unsigned last_frame;
    static int clock_shown = -1;
    int fresh = (unsigned)frame_count != last_frame + 1 || game_mode != MODE_FIELD;
    last_frame = (unsigned)frame_count;
    if (fresh) {
        clock_shown = -1;
        tool_shown = -2;
        toast.drawn = 0;
    }
    if (game_mode != MODE_FIELD || warp.active) return;
    /* the HUD clock (option) */
    int want_clock = opt.hud_clock && !(MAPS[cur_map].flags & MF_DEBUG);
    int ck = want_clock ? gtime.minute + (gtime.day << 11) : -2;
    if (ck != clock_shown) {
        canvas_clear_cells(0, 0, 10, 2);
        if (want_clock) {
            char buf[20];
            time_text(buf);
            canvas_fill(0, 0, 76, 15, 1);
            text_draw(4, 1, buf);
        }
        clock_shown = ck;
    }
    /* the farm tool */
    char label[32] = "";
    if (farm_here()) tool_label(tool_current(), label);
    if (tool_shown == -2 || !str_eq(label, tool_shown_text)) {
        canvas_clear_cells(16, 0, 14, 2);
        if (label[0]) {
            int w = text_width(label) + 16;
            canvas_fill(240 - w, 0, w, 15, 1);
            text_draw(240 - w + 4, 1, "<");
            text_draw(240 - w + 11, 1, label);
        }
        str_copy(tool_shown_text, label);
        tool_shown = 0;
    }
    /* toast */
    if (toast.timer > 0) {
        if (!toast.drawn) {
            canvas_clear_cells(0, 2, CANVAS_COLS, 2);
            int w = text_width(toast.text) + 12;
            canvas_fill(120 - w / 2, 17, w, 15, 1);
            text_draw(120 - w / 2 + 6, 18, toast.text);
            toast.drawn = 1;
        }
        if (--toast.timer == 0) canvas_clear_cells(0, 2, CANVAS_COLS, 2);
    }
}

/* Sprites and labels over the field (script.c field_draw, after the
 * field's own sprites). */
static void farm_draw(void)
{
    farm_canvas_draw();
    /* particles */
    for (int i = 0; i < PARTICLE_MAX; i++) {
        const FarmParticle *p = &particles[i];
        if (!p->life || cur_map != MAP_WILLOW_ACRE) continue;
        spr_push(p->x / 4 - cam_x, p->y / 4 - cam_y, OT_FARM_FX + p->tile, SQ8, FARM_OBANK, 1, 0);
    }
    /* the plot you face */
    if (farm_here() && !player.moving && game_mode == MODE_FIELD && !dialog_active()) {
        int fx = player.x + DIR_DX[player.facing], fy = player.y + DIR_DY[player.facing];
        if (farm_plot_at(fx, fy) >= 0)
            spr_push(fx * 16 - cam_x, fy * 16 - cam_y, OT_FARM_CURSOR, SQ16, FARM_OBANK, 2, 0);
    }
    /* berry bushes off the farm */
    const MapDef *m = &MAPS[cur_map];
    if (cur_map != MAP_WILLOW_ACRE)
        for (int i = 0; i < m->obj_count; i++) {
            if (m->objs[i].kind != OBJ_BERRY) continue;
            int sx = m->objs[i].x * 16 - cam_x, sy = m->objs[i].y * 16 - cam_y;
            if (sx < -16 || sy < -16 || sx > SCREEN_WIDTH || sy > SCREEN_HEIGHT) continue;
            spr_push(sx, sy, OT_FARM_BERRY + (berry_ripe(m->objs[i].arg) ? 4 : 0), SQ16, FARM_OBANK, 2, 0);
        }
    /* rain (the storm draws its own) */
    if (time_raining_here() && !storm_active()) {
        for (int i = 0; i < 12; i++) {
            int speed = 5 + (i % 3);
            int x = (int)((cell_hash(i, 11) % 272u) + field_anim_frame * 2 - cam_x / 2) % 272 - 16;
            int y = (int)((cell_hash(i, 5) % 192u) + field_anim_frame * speed) % 192 - 16;
            spr_push(x, y, OT_EMOTE + EMOTE_RAIN * 4, SQ16, OBANK_EMOTE, 1, 0);
        }
    }
}

/* ================================================================ */
/*  Interacting                                                     */
/* ================================================================ */

static void farm_bed_answer(int c)
{
    if (c != 0) return;
    party_heal_all();
    sfx_play(SFX_HEAL);
    time_sleep();
    dlg_say("You slept soundly in your own bed. Your kin curled up beside you and woke up full of vigor!");
}

static int farm_worker_talk(int i)
{
    const FarmWorker *w = &farm.workers[i];
    char msg[120];
    str_copy(msg, SPECIES[w->species].name);
    switch (w->job) {
    case JOB_WATER: str_put(msg, " splashes water over the rows. It looks very pleased with itself."); break;
    case JOB_TEND: str_put(msg, " pats the soil around a sprout, very gently."); break;
    case JOB_HARVEST: str_put(msg, " sniffs each crop to see if it's ripe."); break;
    case JOB_GUARD: str_put(msg, " keeps a sharp eye on the sky. No crow gets past."); break;
    case JOB_FORAGE: str_put(msg, " has burrs in its fur from roaming. It found something today!"); break;
    default: str_put(msg, " hums near the beehives. The bees don't seem to mind."); break;
    }
    field_emote(-1, EMOTE_HAPPY, 40);
    dlg_say(msg);
    return 1;
}

/*
 * A pressed while facing (fx, fy), after people, signs and satchels
 * (script.c field_try_interact). Handles plots, water for the CAN, the
 * farm decor, the farmhouse and wild berry patches. Returns 1 if handled.
 */
static int farm_interact(int fx, int fy)
{
    int b = berry_obj_at(fx, fy);
    if (b >= 0) return farm_berry_interact(MAPS[cur_map].objs[b].arg);
    if (cur_map == MAP_WILLOW_ACRE) {
        int w = worker_at(fx, fy);
        if (w >= 0) return farm_worker_talk(w);
        int pi = farm_plot_at(fx, fy);
        if (pi >= 0 && farm.owned) return farm_use_on_plot(pi);
    }
    /* fill the can at any water */
    if (bag[ITEM_WATERING_CAN] && farm.can_water < CAN_MAX && fx >= 0 && fy >= 0 && fx < map_w && fy < map_h &&
        (terrain_attr(map_tileset, map_cell(fx, fy)) & A_WATER)) {
        farm.can_water = CAN_MAX;
        fx_burst(FXT_DROP, fx, fy, 3);
        sfx_play(SFX_SPLASH);
        farm_toast("You filled the WATERING CAN.");
        return 1;
    }
    const DecorPlace *p = decor_at(fx, fy, 0, 0);
    if (!p) return 0;
    if (cur_map == MAP_WILLOW_ACRE) {
        switch (p->kind) {
        case DK_SHIPPING_BIN: farm_ship_open(); return 1;
        case DK_PRESERVES_JAR: farm_proc_open(PROC_JAR); return 1;
        case DK_PRESS: farm_proc_open(PROC_PRESS); return 1;
        case DK_DRIER: farm_proc_open(PROC_DRIER); return 1;
        default: return 0;
        }
    }
    if (cur_map == MAP_FARMHOUSE) {
        switch (p->kind) {
        case DK_BED:
            if (!farm.owned) dlg_say("A neat, empty bed. This isn't your house... yet.");
            else dlg_ask("Your own bed. Sleep until morning?", YES_NO, 2, farm_bed_answer);
            return 1;
        case DK_FARM_CHEST:
            if (!farm.owned) dlg_say("A big storage chest. It's locked.");
            else farm_chest_open();
            return 1;
        case DK_WORK_BOARD:
            if (!farm.owned) dlg_say("A cork board with nothing pinned to it.");
            else if (!storage_count) dlg_say("The WORK BOARD. Kin resting on your Shelf can work the farm. Your Shelf is empty.");
            else farm_workboard_open();
            return 1;
        case DK_BOOKSHELF_SMALL:
            lore_reveal(LSRC_FARM_NOTES, "An old farmer's almanac, full of notes in the margins.");
            return 1;
        default: return 0;
        }
    }
    return 0;
}

/* ================================================================ */
/*  REEVE and the deed (world/farm/scripts.c)                       */
/* ================================================================ */

static int farm_deed_price(void)
{
    return quest_done(QUEST_REEVE_BERRIES) ? FARM_DEED_PRICE_QUEST : FARM_DEED_PRICE;
}

/* The deed changes hands: the farm, the farmhouse, tools and seeds. */
static void farm_grant_deed(void)
{
    farm.owned = 1;
    farm.can_water = CAN_MAX;
    farm.tool = 0;
    bag_add(ITEM_FARM_DEED, 1);
    bag_add(ITEM_HOE, 1);
    bag_add(ITEM_WATERING_CAN, 1);
    bag_add(ITEM_SEED_RADISH, 5);
    bag_add(ITEM_SEED_CARROT, 3);
    sfx_play(SFX_LEVEL_UP);
    if (cur_map == MAP_WILLOW_ACRE) {
        decor_remove_kind(DK_FARM_GATE);
        decor_remove_kind(DK_FOR_SALE);
    }
}

/* ================================================================ */
/*  Items from the bag                                              */
/* ================================================================ */

/* Seeds, fertiliser, the sprinkler and produce used from the bag. */
static int farm_use_item(int item)
{
    const Item *it = &ITEMS[item];
    if (it->kind == IK_CROP) {
        dlg_say(farm_value(item) ? "Ship it in the SHIPPING BIN at WILLOW ACRE, or cook something with it."
                                 : "Save it for a meal.");
        return 0;
    }
    if (farm_here() && tool_select_item(item)) {
        char msg[80];
        str_copy(msg, it->name);
        str_put(msg, " is in your hands. Press A on a plot. (L/R: tools)");
        dlg_say(msg);
        return 0;
    }
    dlg_say("That's for the farm. Use it on the soil at WILLOW ACRE.");
    return 0;
}

/* KEY items owned by the farm: WATERING CAN, HOE, FARM DEED. */
static int farm_key_use(int key)
{
    char msg[160];
    if (key == ITEMS[ITEM_FARM_DEED].param) {
        int planted = 0;
        for (int i = 0; i < FARM_PLOTS; i++) planted += farm.plots[i].crop != 0;
        str_copy(msg, "FARM DEED: WILLOW ACRE. ");
        str_put_int(msg, planted);
        str_put(msg, planted == 1 ? " plot planted. " : " plots planted. ");
        str_put(msg, "The bin has paid ");
        str_put_int(msg, (int)farm.earned);
        str_put(msg, "c so far.");
        dlg_say(msg);
        return 0;
    }
    if (farm_here()) {
        tool_select_item(key == ITEMS[ITEM_HOE].param ? ITEM_HOE : ITEM_WATERING_CAN);
        dlg_say(key == ITEMS[ITEM_HOE].param ? "The HOE is in your hands. Till the soil with A." :
                                 "The WATERING CAN is in your hands. Water tilled soil with A.");
        return 0;
    }
    if (key == ITEMS[ITEM_WATERING_CAN].param) {
        str_copy(msg, "The WATERING CAN holds ");
        str_put_int(msg, farm.can_water);
        str_put(msg, " of 20 uses. Fill it at any water.");
        dlg_say(msg);
        return 0;
    }
    dlg_say("You'll need to be on your farm to use that.");
    return 0;
}
