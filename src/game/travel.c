/*
 * Traversal: field abilities (surf, fly, teleport, light, strength), the
 * bike, boats, dark maps, puzzle tiles and map objects, location banners,
 * the town map and the crest case (docs/EXPANSION.md 7.5). Owner:
 * TRAVERSAL system.
 *
 * Map objects (MapDef.objs) become run-time objects when a map loads
 * (map_load -> travel_map_loaded). An EWRAM cell grid makes travel_attr()
 * O(1); boulders and switch/barrier state reset whenever a map loads, which
 * is also the soft-lock guard. Solved gates, opened chests and answered
 * legends persist as bits in travel.puzzle.
 *
 * Object arguments:
 *   OBJ_BOULDER  0 = needs STRENGTH, 1 = "pumice" (pushable without it)
 *   OBJ_PLATE    group; OBJ_GATE group: a gate opens (for good) once every
 *                plate of its group has a boulder on it
 *   OBJ_SWITCH   group (0..15): stepping on it toggles every OBJ_BARRIER of
 *                that group; barrier arg bit 7 = starts lowered
 *   OBJ_PAD      pads with the same arg on a map are partners
 *   OBJ_FERRY    destination map (you land next to the ferry there whose
 *                arg is the map you came from)
 *   OBJ_LEGEND   species (a static encounter; gone once answered)
 *   OBJ_CHEST    item id; 255 = TRINKIT mimic, 254 = HOARDMAW mimic
 *   OBJ_LADDER   none: a door (A_DOOR) that uses the WARPS entry on it
 *   OBJ_BERRY    patch id for farm_berry_interact()
 *
 * Field OBJ VRAM while traversal runs (docs/EXPANSION.md 10.3):
 *   256-335 16x32 objects   336-367 banner (voyage: the boat)
 *   384-399 the bike        640-691 16x16 objects   692-751 16x16 effects
 *   752-765 8x8 particles   400-491 the RUNESTONE spell (while it plays)
 */

typedef struct {
    u8 visited[16];     /* maps you have been to (fly points), bit per map */
    u8 crests;          /* bit per Hall crest (CREST_*) */
    u8 biking, surfing;
    u8 last_hearth;     /* Hearth Hall the party last rested in (respawn / teleport / WAYSTONE) */
    u8 puzzle[16];      /* solved gates, opened chests, answered legends */
    u8 lure_lo, lure_hi;/* LURE INCENSE steps left */
    u8 mount;           /* species that carries you while surfing */
    u8 pad[2];
} TravelState;

enum { CREST_VOLT, CREST_TIDE, CREST_ANVIL, CREST_RIME, CREST_LANTERN, CREST_DREAM, CREST_COUNT };
static const char *const CREST_NAMES[CREST_COUNT] = { "VOLT", "TIDE", "ANVIL", "RIME", "LANTERN", "DREAM" };

/* Field abilities: the crest that allows each, the species flag and the
 * lowest level of the kin that lends it. (Species carry no size yet, so
 * the "size AVERAGE or bigger" rule is not checked.) */
enum { AB_LIGHT, AB_SURF, AB_STRENGTH, AB_FLY, AB_TELEPORT, AB_COUNT };
static const u8 AB_CREST[AB_COUNT] = { CREST_VOLT, CREST_TIDE, CREST_ANVIL, CREST_RIME, CREST_DREAM };
static const u8 AB_FLAG[AB_COUNT] = { FA_LIGHT, FA_SURF, FA_STRENGTH, FA_FLY, FA_TELEPORT };
static const u8 AB_LEVEL[AB_COUNT] = { 0, 20, 20, 30, 0 };
static const char *const AB_NAMES[AB_COUNT] = { "LIGHT", "SURF", "STRENGTH", "FLY", "TELEPORT" };

static TravelState travel;

#define OT_TT(i)    (256 + (i) * 8)     /* 16x32 objects (TT_*) */
#define OT_BANNER   336
#define OT_BOAT     336
#define OT_BIKE     384
#define OT_TO(i)    (640 + (i) * 4)     /* 16x16 objects (TO_*) */
#define OT_TX(i)    (692 + (i) * 4)     /* 16x16 effects (TX_*) */
#define OT_TF(i)    (752 + (i))         /* 8x8 particles (TF_*) */
#define OBANK_TRAVEL 8                  /* travel_misc_palette */
#define OBANK_TFX    15                 /* travel_fx_palette */
#define OBANK_CREST  10                 /* crest case (menus only) */

/* screens and glue defined later in the unity build */
static void ext_open(void (*update)(void), void (*draw)(void), void (*present)(void));
static void screen_begin(int pattern);
static void field_return(void);
static void travel_legend_go(int obj);    /* world/travel/scripts.c */
static void travel_chest_go(int obj);     /* world/travel/scripts.c */
static int farm_berry_interact(int patch);
static void worldmap_open(int fly);
static void travel_dark_off(void);

static void travel_reset(void)
{
    u8 *raw = (u8 *)&travel;
    for (unsigned i = 0; i < sizeof(travel); i++) raw[i] = 0;
    travel.last_hearth = MAP_REST;
}

static void travel_validate(void)
{
    if (travel.last_hearth >= MAP_COUNT || !(MAPS[travel.last_hearth].flags & MF_HEAL))
        travel.last_hearth = MAP_REST;
    travel.biking &= 1;
    travel.surfing &= 1;   /* re-derived from the player's cell every frame */
    if (travel.mount >= SP_COUNT) travel.mount = 0;
    travel.crests &= (1u << CREST_COUNT) - 1;
    if (bag[ITEM_RUNESTONE] <= 0) bag[ITEM_RUNESTONE] = 1;   /* saves from before the RUNESTONE get one */
}

/* ---- entry points other modules call ---- */

static int travel_has_crest(int c) { return c >= 0 && c < CREST_COUNT && ((travel.crests >> c) & 1); }

/* A Hall Master hands over a crest. */
MAYBE_UNUSED static void travel_award_crest(int c)
{
    if (c >= 0 && c < CREST_COUNT) travel.crests |= (u8)(1u << c);
}

MAYBE_UNUSED static int travel_crest_count(void)
{
    int n = 0;
    for (int c = 0; c < CREST_COUNT; c++) n += travel_has_crest(c);
    return n;
}

/* The party slot of a kin that can lend ability `ab` (crest held, species
 * flag, level), or -1. */
static int travel_ability_kin(int ab)
{
    if (ab < 0 || ab >= AB_COUNT || !travel_has_crest(AB_CREST[ab])) return -1;
    for (int i = 0; i < party_count; i++) {
        const Monster *m = &party[i];
        if ((SPECIES[m->species].field & AB_FLAG[ab]) && m->level >= AB_LEVEL[ab]) return i;
    }
    return -1;
}

static int travel_surfing(void) { return travel.surfing; }
static int travel_hides_follower(void) { return travel.surfing; }

/* ================================================================ */
/*  Map objects                                                     */
/* ================================================================ */

#define TOBJ_MAX 48
typedef struct {
    u8 kind, x, y, arg;
    u8 state;           /* GATE 0 shut / 1 sinking / 2 open; BARRIER 1 up; PLATE 1 pressed;
                           CHEST 1 open; LEGEND 1 answered */
    u8 anim;
    s8 ox, oy;          /* boulder slide offset (pixels) */
    u8 bit;             /* persistent bit (travel.puzzle) or 0xFF */
} TObj;

static TObj tobj[TOBJ_MAX];
static int tobj_count;
EWRAM_BSS static u8 obj_grid[MAP_MAX_W * MAP_MAX_H];   /* top object index + 1 */
static u8 sw_on[16];                                   /* switch groups toggled */

static struct {
    u8 strength_on, light_on;
    u8 slide, hop1, push_t, busy;
    u8 flash_t, flash_x, flash_y, flash_x2, flash_y2;
    u8 splash_t, splash_x, splash_y;
    u8 pending, pending_arg;
    u8 banner_t;
    int banner_map;
    int ask_obj;
} tv = { .banner_map = -1, .ask_obj = -1 };

enum { PEND_NONE, PEND_TELEPORT, PEND_FLY, PEND_MAP, PEND_HOME };

#define LEGEND_MAX 4
static KinActor legend_kin[LEGEND_MAX];
static u8 legend_obj[LEGEND_MAX];
static int legend_count;
static KinActor mount_kin;

static int obj_persists(int kind) { return kind == OBJ_GATE || kind == OBJ_CHEST || kind == OBJ_LEGEND; }

/* The first persistent bit of `map`: persistent objects are numbered in
 * map order, then object order. */
static int pbit_base(int map)
{
    int n = 0;
    for (int m = 0; m < map && m < MAP_COUNT; m++)
        for (int i = 0; i < MAPS[m].obj_count; i++) n += obj_persists(MAPS[m].objs[i].kind);
    return n;
}

/* Every persistent object in the world (must stay <= 128: tested). */
MAYBE_UNUSED static int travel_pbit_total(void) { return pbit_base(MAP_COUNT); }

static int pbit_get(int b) { return b < 128 && bit_get(travel.puzzle, b); }
static void pbit_set(int b) { if (b < 128) bit_set(travel.puzzle, b); }

static int obj_in_map(int x, int y) { return x >= 0 && y >= 0 && x < map_w && y < map_h; }

static int obj_index_at(int x, int y)
{
    return obj_in_map(x, y) ? (int)obj_grid[y * map_w + x] - 1 : -1;
}

/* Recompute which object a cell shows (a boulder sits on top of a plate). */
static void grid_cell(int x, int y)
{
    if (!obj_in_map(x, y)) return;
    int best = -1;
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].x == x && tobj[i].y == y && (best < 0 || tobj[i].kind == OBJ_BOULDER)) best = i;
    obj_grid[y * map_w + x] = (u8)(best + 1);
}

static int boulder_at(int x, int y)
{
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].kind == OBJ_BOULDER && tobj[i].x == x && tobj[i].y == y) return i;
    return -1;
}

static int barrier_up(const TObj *o) { return !(sw_on[o->arg & 15] ^ ((o->arg >> 7) & 1)); }

/* Plates follow the boulders; a gate opens for good once every plate of its
 * group is covered. */
static void plates_update(int animate)
{
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].kind == OBJ_PLATE) {
            int down = boulder_at(tobj[i].x, tobj[i].y) >= 0;
            if (animate && down && !tobj[i].state) sfx_play(SFX_CONFIRM);
            tobj[i].state = (u8)down;
        }
    for (int i = 0; i < tobj_count; i++) {
        TObj *g = &tobj[i];
        if (g->kind != OBJ_GATE || g->state) continue;
        int plates = 0, covered = 0;
        for (int k = 0; k < tobj_count; k++)
            if (tobj[k].kind == OBJ_PLATE && tobj[k].arg == g->arg) {
                plates++;
                covered += tobj[k].state;
            }
        if (!plates || covered < plates) continue;
        g->state = (u8)(animate ? 1 : 2);
        g->anim = 0;
        pbit_set(g->bit);
        if (animate) sfx_play(SFX_STAT_UP);
    }
}

/* Open every gate of a group from a script (a lever, a Hall Master...). */
MAYBE_UNUSED static void travel_gate_open(int group)
{
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].kind == OBJ_GATE && tobj[i].arg == group && !tobj[i].state) {
            tobj[i].state = 1;
            tobj[i].anim = 0;
            pbit_set(tobj[i].bit);
        }
}

/* A legend answered / a chest emptied (called by the bout glue). */
static void travel_obj_done(int i)
{
    if (i < 0 || i >= tobj_count) return;
    tobj[i].state = 1;
    pbit_set(tobj[i].bit);
}

static void legends_build(void)
{
    legend_count = 0;
    for (int i = 0; i < tobj_count && legend_count < LEGEND_MAX; i++) {
        const TObj *o = &tobj[i];
        if (o->kind != OBJ_LEGEND || o->arg >= SP_COUNT) continue;
        kin_place(&legend_kin[legend_count], o->arg, 0, o->x, o->y, DIR_DOWN);
        legend_obj[legend_count++] = (u8)i;
    }
}

/* map_load() calls this: build the run-time objects of the new map. */
static void travel_map_loaded(int map)
{
    const MapDef *m = &MAPS[map];
    for (int i = 0; i < map_w * map_h; i++) obj_grid[i] = 0;
    for (int g = 0; g < 16; g++) sw_on[g] = 0;
    tobj_count = 0;
    tv.strength_on = tv.light_on = 0;
    tv.slide = tv.hop1 = tv.push_t = tv.busy = 0;
    tv.flash_t = tv.splash_t = 0;
    int bit = pbit_base(map);
    for (int i = 0; i < m->obj_count && tobj_count < TOBJ_MAX; i++) {
        const MapObj *s = &m->objs[i];
        TObj *o = &tobj[tobj_count++];
        o->kind = s->kind;
        o->x = s->x;
        o->y = s->y;
        o->arg = s->arg;
        o->state = 0;
        o->anim = 0;
        o->ox = o->oy = 0;
        o->bit = 0xFF;
        if (obj_persists(s->kind)) {
            o->bit = (u8)(bit < 128 ? bit : 0xFF);
            bit++;
        }
        switch (o->kind) {
        case OBJ_GATE: o->state = pbit_get(o->bit) ? 2 : 0; break;
        case OBJ_BARRIER: o->state = (u8)barrier_up(o); break;
        case OBJ_CHEST: case OBJ_LEGEND: o->state = (u8)pbit_get(o->bit); break;
        default: break;
        }
    }
    for (int i = 0; i < tobj_count; i++) grid_cell(tobj[i].x, tobj[i].y);
    plates_update(0);
    legends_build();
}

static int obj_attr(const TObj *o)
{
    switch (o->kind) {
    case OBJ_BOULDER: return A_SOLID;
    case OBJ_GATE: return o->state == 2 ? 0 : A_SOLID;
    case OBJ_BARRIER: return o->state ? A_SOLID : 0;
    case OBJ_PAD: return A_PAD;
    case OBJ_SWITCH: return A_SWITCH;
    case OBJ_PLATE: return 0;
    case OBJ_LADDER: return A_DOOR | A_SOLID;
    case OBJ_LEGEND: return o->state ? 0 : A_SOLID;
    default: return A_SOLID;   /* chest, ferry post, berry patch */
    }
}

/* Extra attributes from map objects (a boulder is solid, an open gate isn't). */
static int travel_attr(int x, int y, int a)
{
    if (!obj_in_map(x, y)) return a;
    int i = obj_grid[y * map_w + x];
    return i ? a | obj_attr(&tobj[i - 1]) : a;
}

/* The same, with every puzzle solved: gates and barriers open, boulders
 * pushed out of the way (the reachability tests use this). */
MAYBE_UNUSED static int travel_attr_solved(int x, int y, int a)
{
    if (!obj_in_map(x, y)) return a;
    int i = obj_grid[y * map_w + x];
    if (!i) return a;
    const TObj *o = &tobj[i - 1];
    if (o->kind == OBJ_BOULDER || o->kind == OBJ_GATE || o->kind == OBJ_BARRIER) {
        for (int k = 0; k < tobj_count; k++)   /* what lies under a boulder */
            if (k != i - 1 && tobj[k].x == x && tobj[k].y == y && tobj[k].kind != OBJ_BOULDER &&
                tobj[k].kind != OBJ_GATE && tobj[k].kind != OBJ_BARRIER)
                return a | obj_attr(&tobj[k]);
        return a;
    }
    return a | obj_attr(o);
}

/* The pad a pad at (x, y) sends you to: (px, py), or 0 when none. */
static int travel_pad_partner(int x, int y, int *px, int *py)
{
    int i = obj_index_at(x, y);
    if (i < 0 || tobj[i].kind != OBJ_PAD) {
        for (i = 0; i < tobj_count; i++)
            if (tobj[i].kind == OBJ_PAD && tobj[i].x == x && tobj[i].y == y) break;
        if (i >= tobj_count) return 0;
    }
    for (int k = 0; k < tobj_count; k++)
        if (k != i && tobj[k].kind == OBJ_PAD && tobj[k].arg == tobj[i].arg) {
            *px = tobj[k].x;
            *py = tobj[k].y;
            return 1;
        }
    return 0;
}

/* Map objects and puzzle tiles can change how a cell looks (field.c). The
 * objects are sprites, so nothing is drawn into the map. */
static int travel_dyn_cell(int mx, int my, u16 bottom[4], u16 mid[4], u16 top[4])
{
    (void)mx; (void)my; (void)bottom; (void)mid; (void)top;
    return 0;
}

/* ================================================================ */
/*  Moving around                                                   */
/* ================================================================ */

/* Water you can surf on: no rock, person, object or satchel in the way. */
static int travel_surf_cell(int x, int y)
{
    if (!obj_in_map(x, y)) return 0;
    int a = cell_attr(x, y);
    if (!(a & A_WATER) || (a & A_DEEP) || obj_grid[y * map_w + x]) return 0;
    int sub;
    const DecorDef *d;
    if (decor_at(x, y, &sub, &d) && (d->solid & (1u << sub))) return 0;
    if (npc_at(x, y) >= 0 || npc_kin_at(x, y) >= 0 || wild_at(x, y) >= 0 || item_ball_at(x, y) >= 0) return 0;
    return 1;
}

static int player_can_enter(int x, int y)
{
    return travel.surfing ? travel_surf_cell(x, y) : cell_walkable(x, y);
}

static void travel_bump(void)
{
    if (!player.anim) sfx_play(SFX_BUMP);
    player.anim++;
}

static int travel_speed(int base)
{
    if (tv.hop1 || tv.push_t) return 1;
    if (tv.slide) return 2;
    if (travel.biking && !travel.surfing) return 4;
    return base;
}

static void pick_mount(void)
{
    int k = travel_ability_kin(AB_SURF);
    if (k < 0) k = party_first_healthy();
    if (k < 0) k = 0;
    travel.mount = party_count ? party[k].species : SP_AXOLURK;
}

static void set_splash(int x, int y)
{
    tv.splash_t = 16;
    tv.splash_x = (u8)x;
    tv.splash_y = (u8)y;
}

static int can_push(const TObj *o) { return o->arg == 1 || tv.strength_on; }

static int boulder_push(int i, int dir)
{
    TObj *o = &tobj[i];
    if (!can_push(o) || o->ox || o->oy) return 0;
    int bx = o->x + DIR_DX[dir], by = o->y + DIR_DY[dir];
    if (!obj_in_map(bx, by)) return 0;
    if (cell_attr(bx, by) & (A_SOLID | A_LEDGE | A_WATER | A_DOOR | A_EXIT)) return 0;   /* never onto an exit mat */
    int j = obj_index_at(bx, by);
    if (j >= 0 && tobj[j].kind != OBJ_PLATE && !(tobj[j].kind == OBJ_GATE && tobj[j].state == 2)) return 0;
    if (npc_at(bx, by) >= 0 || npc_kin_at(bx, by) >= 0 || wild_at(bx, by) >= 0 || item_ball_at(bx, by) >= 0)
        return 0;
    if (follower_active() && follower.a.x == bx && follower.a.y == by) return 0;
    int ox = o->x, oy = o->y;
    o->x = (u8)bx;
    o->y = (u8)by;
    o->ox = (s8)(-DIR_DX[dir] * 16);
    o->oy = (s8)(-DIR_DY[dir] * 16);
    grid_cell(ox, oy);
    grid_cell(bx, by);
    sfx_play(SFX_ROCK);
    tv.push_t = 16;
    plates_update(1);
    return 1;
}

/* player_try_move() asks first: -1 = not ours, 0 = blocked, 1 = moving. */
static int travel_player_move(int dir, int nx, int ny)
{
    if (!obj_in_map(nx, ny)) return -1;
    if (travel.surfing) {
        int ox = player.x, oy = player.y;
        if (travel_surf_cell(nx, ny)) {
            actor_start_move(&player, dir);
            actor_step(&player, travel_speed(key_down(KEY_B) ? 2 : 1));
            return 1;
        }
        if (cell_walkable(nx, ny) && !(cell_attr(nx, ny) & A_WATER)) {
            /* back onto land: the kin that carried you climbs out too */
            travel.surfing = 0;
            actor_start_move(&player, dir);
            player.hop = 16;
            tv.hop1 = 1;
            sfx_play(SFX_SPLASH);
            set_splash(ox, oy);
            follower_sync();
            if (follower.shown) kin_place(&follower, follower.species, follower.lustrous, ox, oy, dir);
            return 1;
        }
        travel_bump();
        return 0;
    }
    int i = obj_index_at(nx, ny);
    if (i >= 0 && tobj[i].kind == OBJ_BOULDER) {
        if (!boulder_push(i, dir)) {
            travel_bump();
            return 0;
        }
        int ox = player.x, oy = player.y;
        actor_start_move(&player, dir);
        if (follower_active()) kin_follow(&follower, ox, oy, 0);
        return 1;
    }
    return -1;
}

static void forced_move(int d)
{
    int ox = player.x, oy = player.y;
    actor_start_move(&player, d);
    if (follower_active()) kin_follow(&follower, ox, oy, 0);
    tv.slide = 1;
    player.anim = 0;
    actor_step(&player, 2);
    if (follower_active() && follower.a.moving) actor_step(&follower.a, 2);
}

static void switch_press(const TObj *s)
{
    int g = s->arg & 15;
    sw_on[g] ^= 1;
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].kind == OBJ_BARRIER && (tobj[i].arg & 15) == g) tobj[i].state = (u8)barrier_up(&tobj[i]);
    sfx_play(SFX_ZAP);
}

static int pad_teleport(int x, int y)
{
    int px, py;
    if (!travel_pad_partner(x, y, &px, &py)) return 0;
    tv.flash_t = 20;
    tv.flash_x = (u8)x;
    tv.flash_y = (u8)y;
    tv.flash_x2 = (u8)px;
    tv.flash_y2 = (u8)py;
    player.x = (s16)px;
    player.y = (s16)py;
    player.ox = player.oy = 0;
    follower_reset();
    sfx_play(SFX_DREAM);
    tv.busy = 14;
    return 1;
}

static void lure_tick(void)
{
    int steps = travel.lure_lo | (travel.lure_hi << 8);
    if (!steps) return;
    steps--;
    travel.lure_lo = (u8)(steps & 255);
    travel.lure_hi = (u8)(steps >> 8);
    if (!steps) dlg_say("The LURE INCENSE has burned out.");
}

MAYBE_UNUSED static int travel_lure_active(void) { return travel.lure_lo || travel.lure_hi; }

/* The player reached a cell: switches, pads, ice and currents. Returns 1
 * when a new (forced) move started or the player was teleported. */
static int travel_player_arrived(void)
{
    tv.hop1 = 0;
    lure_tick();
    int x = player.x, y = player.y;
    int i = obj_index_at(x, y);
    if (i >= 0 && tobj[i].kind == OBJ_SWITCH) switch_press(&tobj[i]);
    if (i >= 0 && tobj[i].kind == OBJ_PAD && pad_teleport(x, y)) {
        tv.slide = 0;
        return 1;
    }
    int a = cell_attr(x, y), d = -1;
    if (a & A_CURRENT) d = ((a & A_DIR_HI) ? 2 : 0) | ((a & A_DIR_LO) ? 1 : 0);
    else if ((a & A_ICE) && !travel.surfing) d = player.facing;
    if (d >= 0 && player_can_enter(x + DIR_DX[d], y + DIR_DY[d])) {
        forced_move(d);
        return 1;
    }
    tv.slide = 0;
    return 0;
}

/* ================================================================ */
/*  Abilities                                                       */
/* ================================================================ */

static int map_has(int kind)
{
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].kind == kind) return 1;
    return 0;
}

static int map_outdoor(void) { return (MAPS[cur_map].flags & MF_OUTDOOR) != 0; }

static int bike_toggle(int quiet)
{
    if (bag[ITEM_BIKE] <= 0) return 0;
    if (travel.biking) {
        travel.biking = 0;
        sfx_play(SFX_CANCEL);
        if (!quiet) dlg_say("You got off the BIKE.");
        return 1;
    }
    if (travel.surfing) {
        dlg_say("You can't ride a BIKE on the water!");
        return 0;
    }
    if (!map_outdoor()) {
        dlg_say("There's no room to ride a BIKE in here.");
        return 0;
    }
    travel.biking = 1;
    sfx_play(SFX_CONFIRM);
    if (!quiet) dlg_say("You got on the BIKE.");
    return 1;
}

static void surf_begin(void)
{
    pick_mount();
    travel.surfing = 1;
    travel.biking = 0;
    int dir = player.facing;
    actor_start_move(&player, dir);
    player.hop = 16;
    tv.hop1 = 1;
    sfx_play(SFX_SPLASH);
    set_splash(player.x, player.y);
}

static void surf_answer(int c)
{
    if (c == 0) surf_begin();
}

static void surf_ask(void)
{
    static char msg[MSG_TEXT_MAX];
    int k = travel_ability_kin(AB_SURF);
    str_copy(msg, "The water is calm and deep blue. SURF on ");
    str_put(msg, kin_name(&party[k]));
    str_put(msg, "?");
    dlg_ask(msg, YES_NO, 2, surf_answer);
}

static void strength_use(void)
{
    char msg[MSG_TEXT_MAX];
    int k = travel_ability_kin(AB_STRENGTH);
    tv.strength_on = 1;
    str_copy(msg, kin_name(&party[k]));
    str_put(msg, " used STRENGTH! It can push heavy boulders now.");
    sfx_play(SFX_ROCK);
    dlg_say(msg);
}

static void strength_answer(int c)
{
    if (c == 0) strength_use();
}

static void light_use(void)
{
    char msg[MSG_TEXT_MAX];
    int k = travel_ability_kin(AB_LIGHT);
    tv.light_on = 1;
    str_copy(msg, kin_name(&party[k]));
    str_put(msg, " used LIGHT! Its glow pushes the dark back.");
    sfx_play(SFX_SPARKLE);
    dlg_say(msg);
}

/* Where TELEPORT and the WAYSTONE land: the door mat of the last Hearth Hall. */
static int hearth_spot(int *x, int *y)
{
    for (int i = 0; i < WARP_COUNT; i++)
        if (WARPS[i].dest == travel.last_hearth) {
            *x = WARPS[i].dx;
            *y = WARPS[i].dy;
            return 1;
        }
    return 0;
}

static void teleport_go(void)
{
    int x, y;
    if (!hearth_spot(&x, &y)) return;
    travel.surfing = 0;
    travel.biking = 0;
    sfx_play(SFX_DREAM);
    field_begin_warp(travel.last_hearth, x, y, DIR_UP);
}

/* Arrive somewhere after a full-screen scene (town map, voyage): the new
 * map fades in. */
static void travel_arrive(int map, int x, int y, int facing)
{
    field_return();
    field_enter_map(map, x, y, facing);
    warp.active = 1;
    warp.timer = 9;
    set_brightness(-16);
}

/* ================================================================ */
/*  The RUNESTONE: spun home in a ring of runes                     */
/* ================================================================ */

/*
 * Using the RUNESTONE (a KEY item, unlimited) sets PEND_HOME; once the
 * player stands still the spell plays and the field is frozen:
 *
 *   charge (RUNE_CHARGE frames)  a magic circle opens under the feet
 *       (an affine sprite turned in its plane, then squashed flat), eight
 *       runes appear one by one and orbit on an ellipse (bright in front
 *       of the player, dim behind), the ring shrinks, rises and speeds up
 *       while the player spins on the spot and floats, sparkles rise; at
 *       the end a column of light engulfs the player and the screen burns
 *       white.
 *   arrive (RUNE_ARRIVE frames)  at home (MAP_HOME 9,3 facing down) the
 *       screen fades back from white while the circle and the runes burst
 *       outward and the player settles.
 *
 * OBJ tiles RUNE_OT.. (400-491, unused in the field) hold the art; OBJ
 * bank 15 (the fx bank) shows travel_rune_palette while the spell plays (it
 * keeps the emote colours) and gets travel_fx_palette back afterwards.
 */

#define RUNE_OT       400
#define RUNE_CHARGE   104
#define RUNE_ARRIVE   44
#define RUNE_SPARKS   20
#define HOME_X        9
#define HOME_Y        3

typedef struct { s16 x, y, vx, vy; u8 life, max; } RuneSpark;   /* 1/16 px */

static struct {
    u8 active;          /* 0 idle, 1 charging, 2 arriving */
    u8 t;
    u32 seed;
    RuneSpark spark[RUNE_SPARKS];
} rune;

MAYBE_UNUSED static int travel_rune_active(void) { return rune.active != 0; }

static int rune_sin(int a) { return travel_sin[a & 255]; }
static int rune_cos(int a) { return travel_sin[(a + 64) & 255]; }

/* A private generator, so the spell never shifts the game's RNG. */
static int rune_rand(int n)
{
    rune.seed = rune.seed * 1103515245u + 12345u;
    return (int)((rune.seed >> 16) % (u32)n);
}

static void rune_load_gfx(void)
{
    copy32(VRAM_OBJ_TILES + RUNE_OT * 8, travel_rune_gfx, TR_TILE_COUNT * 8);
    load_pal(obj_palette + OBANK_TFX * 16, travel_rune_palette);
}

/* Why the RUNESTONE will not work here, or 0 when it will. */
static const char *runestone_refusal(void)
{
    if (MAPS[cur_map].flags & MF_DEBUG) return "The RUNESTONE stays silent here.";
    if (cur_map == MAP_HOME) return "You're already home. The RUNESTONE hums softly.";
    return 0;
}

static int runestone_use(void)
{
    const char *no = runestone_refusal();
    if (no) {
        dlg_say(no);
        return 0;
    }
    if (rune.active || tv.pending) return 0;
    tv.pending = PEND_HOME;
    return 1;
}

static void rune_spark_add(int x, int y, int vx, int vy, int life)
{
    for (int i = 0; i < RUNE_SPARKS; i++) {
        RuneSpark *s = &rune.spark[i];
        if (s->life) continue;
        *s = (RuneSpark){ (s16)x, (s16)y, (s16)vx, (s16)vy, (u8)life, (u8)life };
        return;
    }
}

static void rune_start(void)
{
    rune.active = 1;
    rune.t = 0;
    rune.seed = 0x52554E45u ^ (u32)(player.x * 977 + player.y * 131 + cur_map);
    for (int i = 0; i < RUNE_SPARKS; i++) rune.spark[i].life = 0;
    rune_load_gfx();
    sfx_play(SFX_CHARGE);
}

/* The player's feet in world pixels (x centred). */
static int rune_feet_x(void) { return player.x * 16 + player.ox + 8; }
static int rune_feet_y(void) { return player.y * 16 + player.oy + 14; }

static void rune_arrive(void)
{
    travel.surfing = 0;
    travel.biking = 0;
    field_enter_map(MAP_HOME, HOME_X, HOME_Y, DIR_DOWN);
    rune_load_gfx();
    set_brightness(16);
    sfx_play(SFX_DREAM);
    rune.active = 2;
    rune.t = 0;
    for (int i = 0; i < RUNE_SPARKS; i++) rune.spark[i].life = 0;
    int fx = rune_feet_x() * 16, fy = (rune_feet_y() - 10) * 16;
    for (int k = 0; k < 16; k++) {
        int a = k * 16 + rune_rand(8), sp = 24 + rune_rand(16);
        rune_spark_add(fx, fy, rune_cos(a) * sp / 256, rune_sin(a) * sp / 512 - 6, 22 + rune_rand(12));
    }
}

static void rune_end(void)
{
    rune.active = 0;
    set_brightness(0);
    load_pal(obj_palette + OBANK_TFX * 16, travel_fx_palette);
    player.facing = DIR_DOWN;
}

/* Brighten toward white; with `obj` 0 the sprites stay out of it, so the
 * runes and the light keep burning while the world fades. */
static void rune_glow(int level, int obj)
{
    if (level <= 0) {
        set_brightness(0);
        return;
    }
    REG_BLDCNT = (u16)((obj ? 0x3F : 0x2F) | 0x80);
    REG_BLDY = (u16)clampi(level, 0, 16);
}

/* The ring's turn (256 = one turn): it keeps accelerating. */
static int rune_angle(int t) { return 2 * t + t * t * t / 2400; }

/* Once per field frame before anything else (script.c field_update).
 * Returns 1 while the spell plays: input and the world are frozen. */
static int travel_rune_update(void)
{
    static const u8 SPIN[4] = { DIR_RIGHT, DIR_DOWN, DIR_LEFT, DIR_UP };
    if (!rune.active) return 0;
    int t = ++rune.t;
    for (int i = 0; i < RUNE_SPARKS; i++) {
        RuneSpark *s = &rune.spark[i];
        if (!s->life) continue;
        s->life--;
        s->x = (s16)(s->x + s->vx);
        s->y = (s16)(s->y + s->vy);
        if (rune.active == 2) s->vx = (s16)(s->vx * 15 / 16);
    }
    if (rune.active == 1) {
        /* the player turns on the spot, faster and faster */
        int period = t < 28 ? 12 : t < 52 ? 7 : t < 74 ? 4 : 2;
        if (t % period == 0) {
            int k = 0;
            while (k < 4 && SPIN[k] != player.facing) k++;
            player.facing = SPIN[(k + 1) & 3];
        }
        /* sparkles rise from the ring at the feet */
        if (t % (t < 50 ? 4 : 2) == 0 && t < RUNE_CHARGE - 6) {
            int a = rune_rand(256), rx = 18 + rune_rand(10);
            int x = rune_feet_x() * 16 + rune_cos(a) * rx / 16;
            int y = (rune_feet_y() - 2) * 16 + rune_sin(a) * rx * 3 / 128;
            rune_spark_add(x, y, -rune_cos(a) / 64, -(10 + rune_rand(14)), 24 + rune_rand(14));
        }
        if (t == 36) sfx_play(SFX_SPARKLE);
        if (t == 72) sfx_play(SFX_ASTRAL);
        if (t >= RUNE_CHARGE - 26) rune_glow((t - (RUNE_CHARGE - 26)) * 16 / 22, t >= RUNE_CHARGE - 5);
        if (t >= RUNE_CHARGE) rune_arrive();
        return 1;
    }
    set_brightness(t < 26 ? 16 - t * 16 / 26 : 0);
    if (t == 4) sfx_play(SFX_SPARKLE);
    if (t >= RUNE_ARRIVE) rune_end();
    return 1;
}

/* How high the player floats during the spell. */
static int rune_lift(void)
{
    if (rune.active == 1) return rune.t < 40 ? 0 : clampi((rune.t - 40) / 6, 0, 7) + ((rune.t >> 3) & 1);
    if (rune.active == 2) return rune.t < 14 ? 7 - rune.t / 2 : 0;
    return 0;
}

/* A matrix that turns a flat image by `ang` in its own plane, then
 * squashes it (sx, sy in 8.8): the ground circle seen at an angle. */
static int rune_affine_flat(int sx, int sy, int ang)
{
    if (sx < 8) sx = 8;
    if (sy < 8) sy = 8;
    int s = rune_sin(ang), c = rune_cos(ang);
    return oam_affine(c * 256 / sx, s * 256 / sy, -s * 256 / sx, c * 256 / sy);
}

static void rune_draw_ring(int cx, int cy, int rx, int ry, int base, int count, int glyph_shift)
{
    for (int i = 0; i < count; i++) {
        int a = base + i * (256 / TR_RUNES);
        int sn = rune_sin(a);
        int x = cx + rune_cos(a) * rx / 256 - 8;
        int y = cy + sn * ry / 256 - 8 + rune_sin(a * 3 + i * 40) * 2 / 256;
        int g = (i + glyph_shift) % TR_RUNES;
        if (sn >= 0)
            spr_push(x, y, RUNE_OT + TR_FRONT + g * 4, SQ16, OBANK_TFX, 1, 0);
        else
            spr_push(x, y, RUNE_OT + TR_BACK + g * 4, SQ16, OBANK_TFX, 2, 0);
    }
}

/* From travel_draw_floor, after the actors: prio-2 sprites pushed here sit
 * behind the player, prio-1 ones in front. */
static void rune_draw(void)
{
    if (!rune.active) return;
    load_pal(obj_palette + OBANK_TFX * 16, travel_rune_palette);
    int t = rune.t;
    int cx = rune_feet_x() - cam_x, fy = rune_feet_y() - cam_y;
    for (int i = 0; i < RUNE_SPARKS; i++) {
        const RuneSpark *s = &rune.spark[i];
        if (!s->life) continue;
        int f = 3 - s->life * 4 / (s->max + 1);
        spr_push(s->x / 16 - cam_x - 4, s->y / 16 - cam_y - 4, RUNE_OT + TR_SPARK + clampi(f, 0, 3), SQ8,
                 OBANK_TFX, 1, 0);
    }
    if (rune.active == 1) {
        int p = t * 256 / RUNE_CHARGE;                        /* 0..256 */
        /* the column of light at the climax */
        if (t >= RUNE_CHARGE - 34) {
            int bw = clampi((t - (RUNE_CHARGE - 34)) * 256 / 16, 16, 256) + rune_sin(t * 16) * 24 / 256;
            int aff = oam_affine(256 * 256 / bw, 0, 0, 256);
            int prio = t >= RUNE_CHARGE - 10 ? 1 : 2;           /* behind the player, then over */
            for (int y = fy - 30; y > -40; y -= 32)
                spr_push_affine(cx - 8, y, RUNE_OT + TR_BEAM, TALL16x32, OBANK_TFX, prio, 0, aff, 1);
        }
        int count = clampi(t / 3 + 1, 0, TR_RUNES);
        int rx = 34 - 22 * p * p / 65536, ry = rx * 3 / 8 + 2;
        int cy = fy - 6 - 14 * p / 256;
        if (t < RUNE_CHARGE - 10 || (t & 1)) rune_draw_ring(cx, cy, rx, ry, rune_angle(t), count, 0);
        /* the circle on the ground: opens, breathes, spins up */
        int grow = t < 18 ? t * 256 / 18 : 256;
        int sc = grow * 400 / 256 + rune_sin(t * 6) * 18 / 256;
        int aff = rune_affine_flat(sc, sc * 7 / 16, t * 2 + t * t / 90);
        spr_push_affine(cx - 16, fy - 16, RUNE_OT + TR_CIRCLE, SQ32, OBANK_TFX, 2, 0, aff, 1);
        return;
    }
    /* arriving: the runes and the circle burst outward and fade */
    if (t < 22 && (t < 14 || (t & 1))) {
        int rx = 10 + t * 4, ry = rx * 3 / 8 + 2;
        rune_draw_ring(cx, fy - 20 + t / 2, rx, ry, rune_angle(RUNE_CHARGE) + t * 6, TR_RUNES, 3);
    }
    if (t < 30 && (t < 20 || (t & 1))) {
        int sc = 256 + t * 256 / 30;
        int aff = rune_affine_flat(sc, sc * 7 / 16, t * 5);
        spr_push_affine(cx - 16, fy - 16, RUNE_OT + TR_CIRCLE, SQ32, OBANK_TFX, 2, 0, aff, 1);
    }
}

/* ================================================================ */
/*  Location banners                                                */
/* ================================================================ */

#define LBANNER_TIME 150
EWRAM_BSS static u32 lbanner_px[16 * 2 * 8];

static void lbanner_render(const char *name)
{
    for (int i = 0; i < 16 * 2 * 8; i++) lbanner_px[i] = 0;
    target_set(lbanner_px, 16, 2);
    canvas_fill(1, 0, 126, 16, TPAL_EDGE);
    canvas_fill(0, 1, 128, 14, TPAL_EDGE);
    canvas_fill(1, 1, 126, 14, TPAL_PAPER);
    canvas_fill(2, 13, 124, 1, TPAL_GOLD);
    int w = text_width(name);
    text_draw_col(64 - w / 2, 0, name, TPAL_INK, TPAL_SHADE);
    target_canvas();
    /* 16x2 tiles -> four 32x16 sprites (4x2 tiles each, row-major) */
    u32 *dst = VRAM_OBJ_TILES + OT_BANNER * 8;
    for (int s = 0; s < 4; s++)
        for (int r = 0; r < 2; r++)
            copy32(dst + (s * 8 + r * 4) * 8, lbanner_px + (r * 16 + s * 4) * 8, 4 * 8);
}

static int lbanner_wanted(int map)
{
    const MapDef *m = &MAPS[map];
    if (m->flags & MF_DEBUG) return 0;
    return (m->flags & (MF_OUTDOOR | MF_DARK | MF_TOWN)) != 0;
}

static void lbanner_start(int map)
{
    int same = tv.banner_map >= 0 && tv.banner_map < MAP_COUNT && MAPS[tv.banner_map].name &&
               MAPS[map].name && str_eq(MAPS[tv.banner_map].name, MAPS[map].name);
    tv.banner_map = map;
    if (same || !lbanner_wanted(map) || !MAPS[map].name) return;
    tv.banner_t = LBANNER_TIME;
}

static void lbanner_draw(void)
{
    if (!tv.banner_t) return;
    if (tv.banner_t == LBANNER_TIME) lbanner_render(MAPS[tv.banner_map].name);
    int t = LBANNER_TIME - tv.banner_t, y = 4;
    if (t < 12) y = -16 + t * 20 / 12;
    else if (tv.banner_t < 12) y = -16 + tv.banner_t * 20 / 12;
    for (int s = 0; s < 4; s++) spr_push(56 + s * 32, y, OT_BANNER + s * 8, WIDE32x16, OBANK_TRAVEL, 0, 0);
    tv.banner_t--;
}

/* ================================================================ */
/*  Dark maps                                                       */
/* ================================================================ */

#define DARK_BLDY 10
static u16 dark_lines[2][OAM_LINES];
static u8 dark_buf, dark_want, dark_applied;

static int isqrt_i(int v)
{
    int r = 0;
    while ((r + 1) * (r + 1) <= v) r++;
    return r;
}

static int travel_light_radius(void)
{
    return tv.light_on ? 78 : 34;
}

/* Called from field_draw every frame: the light circle around the player
 * (WIN0 per scanline) on MF_DARK maps. `active` is 0 in menus and fades. */
static void travel_dark_frame(int active)
{
    dark_want = 0;
    if (!active || !(MAPS[cur_map].flags & MF_DARK)) {
        if (dark_applied) oam_line_win0h = 0;
        return;
    }
    int r = travel_light_radius();
    int cx = player.x * 16 + player.ox - cam_x + 8, cy = player.y * 16 + player.oy - cam_y + 2;
    u16 *wl = dark_lines[dark_buf ^= 1];
    for (int y = 0; y < SCREEN_HEIGHT; y++) {
        int d = y - cy, h2 = r * r - d * d;
        if (h2 <= 0) {
            wl[y] = 0;
            continue;
        }
        int h = isqrt_i(h2);
        int l = clampi(cx - h, 0, 240), rr = clampi(cx + h, 0, 240);
        wl[y] = (u16)((l << 8) | rr);
    }
    for (int k = 1; k < LINE_COPIES; k++)
        for (int y = 0; y < SCREEN_HEIGHT; y++) wl[k * SCREEN_HEIGHT + y] = wl[y];
    wl[OAM_LINES - 1] = wl[0];
    oam_line_win0h = wl;
    dark_want = 1;
}

/* In vblank (field_render_view): apply or drop the darkness. */
static void travel_dark_present(void)
{
    if (dark_want) {
        REG_WIN0V = SCREEN_HEIGHT;
        REG_WININ = 0x001F;     /* inside the light: everything, no darkening */
        REG_WINOUT = 0x003F;    /* outside: everything, darkened */
        REG_BLDCNT = 0x00FD;    /* darken BG0/BG2/BG3/OBJ/backdrop, never the UI (BG1) */
        REG_BLDY = DARK_BLDY;
        REG_DISPCNT = (u16)(REG_DISPCNT | DCNT_WIN0);
        dark_applied = 1;
    } else if (dark_applied) {
        travel_dark_off();
    }
}

/* field_setup_bg() calls this (menus, bouts and screens start clean). */
static void travel_dark_off(void)
{
    dark_want = 0;
    if (oam_line_win0h == dark_lines[0] || oam_line_win0h == dark_lines[1]) oam_line_win0h = 0;
    if (!dark_applied) return;
    dark_applied = 0;
    REG_DISPCNT = (u16)(REG_DISPCNT & ~DCNT_WIN0);
    REG_BLDCNT = 0;
    REG_BLDY = 0;
}

/* ================================================================ */
/*  Field hooks                                                     */
/* ================================================================ */

/* field_enter_map(): the player is on the new map. */
static void travel_map_entered(int map)
{
    bit_set(travel.visited, map);
    travel.surfing = (cell_attr(player.x, player.y) & A_WATER) != 0;
    if (travel.surfing) {
        travel.biking = 0;
        if (!travel.mount) pick_mount();
    }
    if (!map_outdoor()) travel.biking = 0;
    else if (opt.bike_auto && bag[ITEM_BIKE] > 0 && !travel.surfing) travel.biking = 1;
    lbanner_start(map);
}

/* Once per field frame before the player moves (not during dialog, warps
 * or menus). Returns 1 while input is frozen. */
static int travel_update(void)
{
    for (int i = 0; i < tobj_count; i++) {
        TObj *o = &tobj[i];
        if (o->ox) o->ox = (s8)(o->ox + (o->ox < 0 ? 1 : -1));
        if (o->oy) o->oy = (s8)(o->oy + (o->oy < 0 ? 1 : -1));
        if (o->kind == OBJ_GATE && o->state == 1 && ++o->anim >= 24) o->state = 2;
    }
    if (tv.push_t) tv.push_t--;
    if (tv.flash_t) tv.flash_t--;
    if (tv.splash_t) tv.splash_t--;
    if (!player.moving) {
        int w = (cell_attr(player.x, player.y) & A_WATER) != 0;
        if (w != travel.surfing) {
            travel.surfing = (u8)w;
            if (w) {
                travel.biking = 0;
                pick_mount();
            } else {
                follower_reset();
            }
        }
    }
    if (tv.slide) player.anim = 0;
    if (tv.busy) {
        tv.busy--;
        return 1;
    }
    if (tv.pending && !player.moving) {
        int p = tv.pending;
        tv.pending = 0;
        if (p == PEND_TELEPORT) teleport_go();
        if (p == PEND_FLY) worldmap_open(1);
        if (p == PEND_MAP) worldmap_open(0);
        if (p == PEND_HOME) rune_start();
        return 1;
    }
    if (key_hit(KEY_R) && !player.moving && !(MAPS[cur_map].flags & MF_DEBUG)) {
        bike_toggle(1);
        return 1;
    }
    return 0;
}

/* The player's sprite on the bike (a 32x32 in the player palette). */
static int travel_player_entry(FieldSprite *e, int lift)
{
    if (!travel.biking || travel.surfing) return 0;
    int f = player.facing == DIR_UP ? 2 : (player.facing == DIR_LEFT || player.facing == DIR_RIGHT) ? 4 : 0;
    if (player.moving) f += (player.anim >> 2) & 1;
    copy32(VRAM_OBJ_TILES + OT_BIKE * 8, travel_bike_gfx[f], 16 * 8);
    *e = (FieldSprite){ player.y * 16 + player.oy, player.x * 16 + player.ox, 1, OT_BIKE | (lift << 16),
                        OBANK_PLAYER, player.facing == DIR_RIGHT };
    return 1;
}

/* Surfing: the player rides a little higher, bobbing on the kin's back. */
static int travel_player_lift(void)
{
    if (rune.active) return rune_lift();
    if (!travel.surfing) return 0;
    return 5 + ((field_anim_frame >> 4) & 1);
}

/* Kin drawn like overworld kin: the surf mount and the legends. */
static int travel_kin_actors(const KinActor **out, int max)
{
    int n = 0;
    if (travel.surfing && n < max) {
        mount_kin.a = player;
        mount_kin.a.hop = player.hop;
        mount_kin.species = travel.mount < SP_COUNT ? travel.mount : 0;
        mount_kin.lustrous = 0;
        mount_kin.shown = 1;
        out[n++] = &mount_kin;
    }
    for (int i = 0; i < legend_count && n < max; i++)
        if (!tobj[legend_obj[i]].state) out[n++] = &legend_kin[i];
    return n;
}

static int obj_on_screen(int wx, int wy)
{
    return wx - cam_x >= -16 && wx - cam_x <= SCREEN_WIDTH && wy - cam_y >= -32 && wy - cam_y <= SCREEN_HEIGHT + 16;
}

/* Standing objects join the field's depth-sorted sprite list. */
static int travel_push_sprites(FieldSprite *list, int n, int max)
{
    for (int i = 0; i < tobj_count && n < max; i++) {
        const TObj *o = &tobj[i];
        int wx = o->x * 16 + o->ox, wy = o->y * 16 + o->oy;
        if (!obj_on_screen(wx, wy)) continue;
        int tile = -1, shape = SQ16, top = wy;
        switch (o->kind) {
        case OBJ_BOULDER: tile = OT_TO(TO_BOULDER); break;
        case OBJ_CHEST: tile = OT_TO(o->state ? TO_CHEST_OPEN : TO_CHEST); break;
        case OBJ_LADDER: tile = OT_TO(TO_LADDER); break;
        case OBJ_GATE:
            if (o->state == 2) break;
            tile = OT_TT(o->state ? TT_GATE_1 + clampi(o->anim / 8, 0, 2) : TT_GATE);
            shape = TALL16x32;
            top = wy - 16;
            break;
        case OBJ_BARRIER:
            tile = OT_TT(o->state ? TT_BARRIER0 + (field_anim_frame / 6) % 4 : TT_BARRIER_OFF);
            shape = TALL16x32;
            top = wy - 16;
            break;
        case OBJ_FERRY:
            tile = OT_TT(TT_FERRY);
            shape = TALL16x32;
            top = wy - 16;
            break;
        default: break;
        }
        if (tile < 0) continue;
        int sort = o->y * 16 - 1;
        list[n++] = (FieldSprite){ sort, wx, 4, tile, OBANK_TRAVEL, 0, top - sort, shape };
    }
    return n;
}

/* Floor objects and effects: drawn after (under) everything else. */
static void travel_draw_floor(void)
{
    rune_draw();
    for (int i = 0; i < tobj_count; i++) {
        const TObj *o = &tobj[i];
        int wx = o->x * 16, wy = o->y * 16, tile = -1;
        if (!obj_on_screen(wx, wy)) continue;
        switch (o->kind) {
        case OBJ_PLATE: tile = OT_TO(o->state ? TO_PLATE_DOWN : TO_PLATE); break;
        case OBJ_SWITCH: tile = OT_TO(sw_on[o->arg & 15] ? TO_SWITCH_ON : TO_SWITCH); break;
        case OBJ_PAD: tile = OT_TO(TO_PAD0 + (field_anim_frame / 8) % 4); break;
        case OBJ_GATE: if (o->state == 2) tile = OT_TO(TO_GATE_SLOT); break;
        default: break;
        }
        if (tile >= 0) spr_push(wx - cam_x, wy - cam_y, tile, SQ16, OBANK_TRAVEL, 3, 0);
    }
    if (tv.flash_t) {
        int f = tv.flash_t & 2 ? 0 : 1;
        if (!f) {
            spr_push(tv.flash_x * 16 - cam_x, tv.flash_y * 16 - cam_y - 8, OT_TX(TX_FLASH), SQ16, OBANK_TFX, 1, 0);
            spr_push(tv.flash_x2 * 16 - cam_x, tv.flash_y2 * 16 - cam_y - 8, OT_TX(TX_FLASH), SQ16, OBANK_TFX, 1, 0);
        }
    }
    if (tv.splash_t)
        spr_push(tv.splash_x * 16 - cam_x, tv.splash_y * 16 - cam_y - 2,
                 OT_TX(tv.splash_t > 8 ? TX_SPLASH0 : TX_SPLASH1), SQ16, OBANK_TFX, 2, 0);
    if (travel.surfing) {
        int wx = player.x * 16 + player.ox, wy = player.y * 16 + player.oy;
        int tile = player.moving ? OT_TX(TX_WAKE0 + ((field_anim_frame >> 3) & 1)) : OT_TX(TX_RIPPLE);
        int flip = player.facing == DIR_LEFT ? ATTR1_HFLIP : 0;
        spr_push(wx - cam_x, wy - cam_y + 4, tile, SQ16, OBANK_TFX, 3, flip);
    }
    lbanner_draw();
}

/* The object and effect sheets (field_load_tileset: after every map
 * load, menu, bout and screen). */
static void travel_load_gfx(void)
{
    copy32(VRAM_OBJ_TILES + OT_TT(0) * 8, travel_obj32, TT_COUNT * 64);
    copy32(VRAM_OBJ_TILES + OT_TO(0) * 8, travel_obj16, TO_COUNT * 32);
    copy32(VRAM_OBJ_TILES + OT_TX(0) * 8, travel_fx16, TX_COUNT * 32);
    copy32(VRAM_OBJ_TILES + OT_TF(0) * 8, travel_fx8, TF_COUNT * 8);
    load_pal(obj_palette + OBANK_TRAVEL * 16, travel_misc_palette);
    load_pal(obj_palette + OBANK_TFX * 16, travel_fx_palette);
    if (tv.banner_t && tv.banner_t < LBANNER_TIME && tv.banner_map >= 0) lbanner_render(MAPS[tv.banner_map].name);
}

/* ================================================================ */
/*  Examining things (A)                                            */
/* ================================================================ */

static void legend_answer(int c)
{
    if (c == 0 && tv.ask_obj >= 0) travel_legend_go(tv.ask_obj);
}

static void boat_ride(int map, int x, int y);

static void ferry_answer(int c)
{
    if (c != 0 || tv.ask_obj < 0) return;
    const TObj *o = &tobj[tv.ask_obj];
    if (bag[ITEM_FERRY_PASS] <= 0) {
        if (money < 500) {
            dlg_say("You don't have enough coins for the fare.");
            return;
        }
        money -= 500;
        sfx_play(SFX_BUY);
    }
    boat_ride(o->arg, 255, 255);
}

/* Something the player faces that is a map object or water. Returns 1 when
 * handled. */
static int obj_interact(int x, int y)
{
    char msg[MSG_TEXT_MAX];
    int i = obj_index_at(x, y);
    if (i < 0) {
        if (travel.surfing || !travel_surf_cell(x, y)) return 0;
        if (travel_ability_kin(AB_SURF) >= 0) surf_ask();
        else dlg_say("The water is deep blue. A kin that can SURF could carry you across (TIDE CREST, level 20).");
        return 1;
    }
    TObj *o = &tobj[i];
    tv.ask_obj = i;
    switch (o->kind) {
    case OBJ_BOULDER:
        if (o->arg == 1) dlg_say("A pumice boulder, full of air bubbles. It looks light enough to push.");
        else if (tv.strength_on) dlg_say("Your kin is ready to push boulders. Walk into it!");
        else if (travel_ability_kin(AB_STRENGTH) >= 0)
            dlg_ask("A huge boulder. Your kin could shift it. Use STRENGTH?", YES_NO, 2, strength_answer);
        else dlg_say("A huge boulder. A kin with STRENGTH could push it (ANVIL CREST, level 20).");
        return 1;
    case OBJ_GATE:
        if (o->state == 2) return 0;
        dlg_say("A heavy iron gate. Somewhere, a pressure plate must work it.");
        return 1;
    case OBJ_BARRIER:
        if (!o->state) return 0;
        dlg_say("A crackling barrier of static. A floor switch must control it.");
        return 1;
    case OBJ_SWITCH: dlg_say("A floor switch. Step on it to throw it."); return 1;
    case OBJ_PAD: dlg_say("A teleport pad. It hums softly. Step on it!"); return 1;
    case OBJ_PLATE: dlg_say("A pressure plate. It is too stiff to press by standing on it."); return 1;
    case OBJ_BERRY:
        if (!farm_berry_interact(o->arg)) dlg_say("A wild berry patch. Nothing is ripe yet.");
        return 1;
    case OBJ_CHEST:
        if (o->state) {
            dlg_say("The chest is empty.");
            return 1;
        }
        travel_chest_go(i);
        return 1;
    case OBJ_LEGEND:
        if (o->state || o->arg >= SP_COUNT) return 0;
        str_copy(msg, "A great presence fills the air. ");
        str_put(msg, SPECIES[o->arg].name);
        str_put(msg, " is watching you, brimming. Answer it?");
        dlg_ask(msg, YES_NO, 2, legend_answer);
        return 1;
    case OBJ_FERRY:
        if (o->arg >= MAP_COUNT) {
            dlg_say("The ferry isn't running today.");
            return 1;
        }
        str_copy(msg, "The ferry to ");
        str_put(msg, MAPS[o->arg].name);
        str_put(msg, bag[ITEM_FERRY_PASS] > 0 ? ". Your FERRY PASS is welcome! Sail?" : ". The fare is 500c. Sail?");
        dlg_ask(msg, YES_NO, 2, ferry_answer);
        return 1;
    default: return 0;
    }
}

/* ================================================================ */
/*  The voyage (boat cutscene)                                      */
/* ================================================================ */

#define VOY_END 200
static struct { int t, map, x, y, from; } voy;

static void voyage_land(void)
{
    int map = voy.map, x = voy.x, y = voy.y;
    if (x == 255) {
        /* next to the ferry on the far side that sails back here */
        x = MAPS[map].w / 2;
        y = MAPS[map].h / 2;
        for (int i = 0; i < MAPS[map].obj_count; i++) {
            const MapObj *o = &MAPS[map].objs[i];
            if (o->kind == OBJ_FERRY && o->arg == voy.from) {
                x = o->x;
                y = o->y + 1;
                break;
            }
        }
    }
    travel.surfing = 0;
    travel.biking = 0;
    travel_arrive(map, x, y, DIR_DOWN);
    /* the landing cell may be taken: the nearest walkable cell instead */
    if (!cell_walkable(player.x, player.y)) {
        int best = 1 << 30, bx = player.x, by = player.y;
        for (int yy = 0; yy < map_h; yy++)
            for (int xx = 0; xx < map_w; xx++)
                if (cell_walkable(xx, yy) && !(cell_attr(xx, yy) & A_WATER)) {
                    int d = absi(xx - player.x) + absi(yy - player.y);
                    if (d < best) {
                        best = d;
                        bx = xx;
                        by = yy;
                    }
                }
        player.x = (s16)bx;
        player.y = (s16)by;
        follower_reset();
        field_update_camera();
    }
}

static void voyage_update(void)
{
    if (voy.t == 0) {
        /* drawn here: a dialog callback that started the trip clears the
         * message rows when it returns */
        char msg[64];
        canvas_window(0, 17, CANVAS_COLS, 3, WIN_STD);
        str_copy(msg, "Sailing to ");
        str_put(msg, MAPS[voy.map].name);
        str_put(msg, "...");
        text_draw_center(120, 140, msg);
    }
    voy.t++;
    if (voy.t > 24 && voy.t < VOY_END - 16 && (key_hit(KEY_A) || key_hit(KEY_B))) voy.t = VOY_END - 16;
    if (voy.t < 16) set_brightness(-(16 - voy.t));
    else if (voy.t >= VOY_END - 16) set_brightness(-clampi(voy.t - (VOY_END - 16), 0, 16));
    else set_brightness(0);
    if (voy.t == 40) sfx_play(SFX_WIND);
    if (voy.t >= VOY_END) voyage_land();
}

static void voyage_draw(void)
{
    int bob = (voy.t >> 4) & 1;
    int aff = oam_affine_scale_rot(512, 512, 0);
    spr_push_affine(96, 84 + bob, OT_BOAT + bob * 16, SQ32, OBANK_TRAVEL, 1, 0, aff, 1);
    spr_push(62 - (voy.t & 15) / 4, 118 + bob, OT_TX(TX_WAKE0 + ((voy.t >> 3) & 1)), SQ16, OBANK_TFX, 1, 0);
    for (int g = 0; g < 2; g++) {
        int gx = 260 - ((voy.t * (2 + g) + g * 97) % 300), gy = 24 + g * 14 + ((voy.t >> 3) & 1);
        spr_push(gx, gy, OT_TX(((voy.t >> 3) + g) & 1 ? TX_GULL1 : TX_GULL0), SQ16, OBANK_TFX, 1, 0);
    }
}

static void voyage_present(void)
{
    REG_BG0HOFS = (u16)(voy.t / 2);
    REG_BG0VOFS = 0;
}

/* A boat trip to (map, x, y): a sailing cutscene, then you arrive. x = 255
 * lands next to the ferry there that sails back to the map you left. */
static void boat_ride(int map, int x, int y)
{
    if (map < 0 || map >= MAP_COUNT) return;
    voy.t = 0;
    voy.map = map;
    voy.x = x;
    voy.y = y;
    voy.from = cur_map;
    dialog_clear();
    canvas_clear();
    travel_dark_off();
    copy32(VRAM_SCENE_TILES, travel_sea_tiles, TRAVEL_SEA_TILE_COUNT * 8);
    u16 *sb = VRAM_MAP(SB_FIELD_BOTTOM);
    for (int yy = 0; yy < 32; yy++)
        for (int xx = 0; xx < 32; xx++) sb[yy * 32 + xx] = yy < 20 ? travel_sea_screen[yy * 32 + xx] : 0;
    load_pal(bg_palette, travel_sea_palette);
    copy32(VRAM_OBJ_TILES + OT_BOAT * 8, travel_boat_gfx, 2 * 16 * 8);
    REG_BG0CNT = BGCNT_CHARBLOCK(0) | BGCNT_SCREENBLOCK(SB_FIELD_BOTTOM) | BGCNT_PRIO(3);
    REG_BG0HOFS = REG_BG0VOFS = 0;
    REG_DISPCNT = DCNT_MODE0 | DCNT_BG0 | DCNT_BG1 | DCNT_OBJ | DCNT_OBJ_1D;
    set_brightness(-16);
    ext_open(voyage_update, voyage_draw, voyage_present);
}

MAYBE_UNUSED static void travel_boat_to(int map, int x, int y)
{
    boat_ride(map, x, y);
}

/* ================================================================ */
/*  The town map (and FLY)                                          */
/* ================================================================ */

/* Town-map spot of a map (interiors: the map whose door leads in). */
static int map_spot(int m)
{
    for (int guard = 0; guard < 5 && m >= 0 && m < MAP_COUNT; guard++) {
        switch (m) {
        case MAP_TOWN: return WM_MAPLE;
        case MAP_MEADOW: return WM_MEADOW;
        case MAP_RISE: return WM_RISE;
        case MAP_WOOD: return WM_WOOD;
        case MAP_LAKE: return WM_LAKE;
        case MAP_WILLOW_ACRE: return WM_WILLOW;
        case MAP_SALTWIND: return WM_SALTWIND;
        case MAP_PORT_BRINE: return WM_PORT_BRINE;
        case MAP_SEA_ROUTE: return WM_SEA_ROUTE;
        case MAP_GULL_ISLE: return WM_GULL_ISLE;
        case MAP_DROWNED_BELL: return WM_DROWNED_BELL;
        case MAP_FROSTPINE: return WM_FROSTPINE;
        case MAP_FROSTHOLLOW: return WM_FROSTHOLLOW;
        case MAP_WHITECROWN: return WM_WHITECROWN;
        case MAP_SKY_ISLE: return WM_SKY_ISLE;
        case MAP_GLIMMER_1: case MAP_GLIMMER_2: return WM_GLIMMER;
        case MAP_STARFALL: return WM_STARFALL;
        case MAP_COPPERLINE: return WM_COPPERLINE;
        case MAP_LUMEN: return WM_LUMEN;
        case MAP_ELDERWOOD: return WM_ELDERWOOD;
        case MAP_MOONVEIL: return WM_MOONVEIL;
        case MAP_DREAMSPIRE: return WM_DREAMSPIRE;
        case MAP_DUST_LIBRARY: return WM_DUST_LIBRARY;
        case MAP_CINDER_ROAD: return WM_CINDER_ROAD;
        case MAP_CINDERMOOR: return WM_CINDERMOOR;
        case MAP_EMBER_TUNNEL: return WM_EMBER_TUNNEL;
        case MAP_CALDERA: return WM_CALDERA;
        case MAP_CLOCKWORK_SPIRE: return WM_CLOCKWORK;
        case MAP_ASHEN_FIELDS: return WM_ASHEN;
        case MAP_GRAVEWOOD: return WM_GRAVEWOOD;
        case MAP_DUSKMERE: return WM_DUSKMERE;
        case MAP_OSSUARY_1: case MAP_OSSUARY_2: return WM_OSSUARY;
        case MAP_BONE_THRONE: return WM_BONE_THRONE;
        default: break;
        }
        int parent = -1;
        for (int i = 0; i < WARP_COUNT && parent < 0; i++)
            if (WARPS[i].dest == m && WARPS[i].map != m) parent = WARPS[i].map;
        m = parent;
    }
    return -1;
}

/* A fly point you may fly to: visited (the Sky Isle only needs the wings). */
static int fly_point_open(int i)
{
    int m = FLY_POINTS[i].map;
    return bit_get(travel.visited, m) || m == MAP_SKY_ISLE;
}

#define WM_PTS 32
static struct { u8 fly, cur, n, pt[WM_PTS]; int here, t; } wm;

static void wm_caption(void)
{
    char buf[64];
    canvas_window(0, 17, CANVAS_COLS, 3, WIN_STD);
    if (wm.n) {
        const FlyPoint *f = &FLY_POINTS[wm.pt[wm.cur]];
        str_copy(buf, wm.fly ? "FLY to " : "");
        str_put(buf, f->name);
        text_draw(12, 140, buf);
    } else {
        text_draw(12, 140, MAPS[cur_map].name);
    }
    text_draw_right(228, 140, wm.fly ? "A:FLY  B:BACK" : "B:BACK");
}

static void wm_update(void)
{
    wm.t++;
    if (key_hit(KEY_B) || key_hit(KEY_START) || (!wm.fly && key_hit(KEY_A))) {
        sfx_play(SFX_CANCEL);
        field_return();
        return;
    }
    if (wm.fly && wm.n && key_hit(KEY_A)) {
        const FlyPoint *f = &FLY_POINTS[wm.pt[wm.cur]];
        sfx_play(SFX_WIND);
        travel.biking = 0;
        travel_arrive(f->map, f->x, f->y, DIR_DOWN);
        return;
    }
    int dx = key_hit(KEY_RIGHT) - key_hit(KEY_LEFT), dy = key_hit(KEY_DOWN) - key_hit(KEY_UP);
    if ((!dx && !dy) || wm.n < 2) return;
    const FlyPoint *c = &FLY_POINTS[wm.pt[wm.cur]];
    int best = -1, best_d = 1 << 30;
    for (int k = 0; k < wm.n; k++) {
        if (k == wm.cur) continue;
        const FlyPoint *f = &FLY_POINTS[wm.pt[k]];
        int vx = f->map_x - c->map_x, vy = f->map_y - c->map_y;
        int along = vx * dx + vy * dy, across = absi(vx * dy - vy * dx);
        if (along <= 0) continue;
        int d = along + across * 2;
        if (d < best_d) {
            best_d = d;
            best = k;
        }
    }
    if (best >= 0) {
        wm.cur = (u8)best;
        sfx_play(SFX_CURSOR);
        wm_caption();
    }
}

static void wm_draw(void)
{
    static u8 seen[WM_COUNT];
    for (int s = 0; s < WM_COUNT; s++) seen[s] = 0;
    for (int m = 0; m < MAP_COUNT; m++)
        if (bit_get(travel.visited, m)) {
            int s = map_spot(m);
            if (s >= 0) seen[s] = 1;
        }
    if (wm.here >= 0 && ((wm.t >> 4) & 1))
        spr_push(WM_SPOTS[wm.here][0] - 8, WM_SPOTS[wm.here][1] - 16, OT_TX(TX_PIN), SQ16, OBANK_TFX, 0, 0);
    if (wm.n) {
        const FlyPoint *f = &FLY_POINTS[wm.pt[wm.cur]];
        spr_push(f->map_x - 8, f->map_y - 8, OT_TX(TX_CURSOR0 + ((wm.t >> 4) & 1)), SQ16, OBANK_TFX, 0, 0);
    }
    for (int s = 0; s < WM_COUNT; s++) {
        int kind = WM_SPOTS[s][2], tile;
        if (kind == 3) tile = TF_MARK_SKY;
        else if (seen[s] && kind == 0) tile = TF_MARK_TOWN;
        else if (seen[s] || kind == 0) tile = TF_MARK_DIM;
        else continue;
        spr_push(WM_SPOTS[s][0] - 4, WM_SPOTS[s][1] - 4, OT_TF(tile), SQ8, OBANK_TFX, 1, 0);
    }
}

/* The town map (fly = 1: pick a destination). */
static void worldmap_open(int fly)
{
    dialog_clear();
    canvas_clear();
    travel_dark_off();
    set_brightness(0);
    copy32(VRAM_SCENE_TILES, travel_map_tiles, TRAVEL_MAP_TILE_COUNT * 8);
    u16 *sb = VRAM_MAP(SB_FIELD_BOTTOM);
    for (int y = 0; y < 32; y++)
        for (int x = 0; x < 32; x++) sb[y * 32 + x] = (y < 20 && x < 30) ? travel_map_screen[y * 30 + x] : 0;
    load_pal(bg_palette, travel_map_palette);
    REG_BG0CNT = BGCNT_CHARBLOCK(0) | BGCNT_SCREENBLOCK(SB_FIELD_BOTTOM) | BGCNT_PRIO(3);
    REG_BG0HOFS = REG_BG0VOFS = 0;
    REG_DISPCNT = DCNT_MODE0 | DCNT_BG0 | DCNT_BG1 | DCNT_OBJ | DCNT_OBJ_1D;
    wm.fly = (u8)(fly != 0);
    wm.here = map_spot(cur_map);
    wm.n = 0;
    wm.cur = 0;
    wm.t = 0;
    int best = 1 << 30;
    for (int i = 0; i < FLY_POINT_COUNT && wm.n < WM_PTS; i++) {
        if (!fly_point_open(i)) continue;
        if (wm.here >= 0) {
            int d = absi(FLY_POINTS[i].map_x - WM_SPOTS[wm.here][0]) + absi(FLY_POINTS[i].map_y - WM_SPOTS[wm.here][1]);
            if (d < best) {
                best = d;
                wm.cur = wm.n;
            }
        }
        wm.pt[wm.n++] = (u8)i;
    }
    wm_caption();
    ext_open(wm_update, wm_draw, 0);
}

/* ================================================================ */
/*  The ALMANAC's AREA map: where a kin lives                       */
/* ================================================================ */

/*
 * SELECT on an ALMANAC page shows the town map with every place the kin
 * lives in ringed (wild grass, water while surfing, a legend's lair), once
 * you have met it. A kin that only grows out of another shows where that
 * one lives. LEFT/RIGHT (or UP/DOWN) step through the places; the caption
 * gives the levels, how common it is and when it comes out.
 */

typedef struct {
    u8 spot, map, lo, hi, share, when, water, legend;
} KinPlace;

static struct {
    int sp, via, met, t;       /* via: the kin whose places are shown (sp or an earlier form) */
    int n, cur;
    KinPlace pl[WM_PTS];
    void (*back)(void);
} wa;

/* Adds what a wild zone says about sp to *k; returns 1 if sp lives there. */
static int zone_kin_info(int zone, int sp, KinPlace *k, int water)
{
    if (zone <= ZONE_NONE || zone >= ZONE_COUNT) return 0;
    const WildZone *z = &WILD_ZONES[zone];
    int total = 0, w = 0;
    for (int i = 0; i < z->count; i++) {
        total += z->slots[i].weight;
        if (z->slots[i].species != sp) continue;
        w += z->slots[i].weight;
        if (!k->lo || z->slots[i].min_level < k->lo) k->lo = z->slots[i].min_level;
        if (z->slots[i].max_level > k->hi) k->hi = z->slots[i].max_level;
        k->when |= (u8)(1 << z->slots[i].when);
    }
    if (!w) return 0;
    int share = total ? w * 100 / total : 0;
    if (share > k->share) k->share = (u8)share;
    if (water) k->water = 1;
    return 1;
}

/* Every town-map place where sp can be met (one entry per spot). */
static int kin_places(int sp, KinPlace *out)
{
    int n = 0;
    for (int m = 0; m < MAP_COUNT; m++) {
        if (MAPS[m].flags & MF_DEBUG) continue;
        KinPlace k = { 0 };
        int found = zone_kin_info(MAPS[m].zone, sp, &k, 0);
        found |= zone_kin_info(MAPS[m].water_zone, sp, &k, 1);
        for (int i = 0; i < MAPS[m].obj_count; i++)
            if (MAPS[m].objs[i].kind == OBJ_LEGEND && MAPS[m].objs[i].arg == sp) k.legend = found = 1;
        if (!found) continue;
        int s = map_spot(m);
        if (s < 0) continue;
        int j = 0;
        while (j < n && out[j].spot != s) j++;
        if (j == n) {
            if (n >= WM_PTS) break;
            k.spot = (u8)s;
            k.map = (u8)m;
            out[n++] = k;
            continue;
        }
        KinPlace *o = &out[j];   /* another map on the same spot (a cave's second floor) */
        if (k.lo && (!o->lo || k.lo < o->lo)) o->lo = k.lo;
        if (k.hi > o->hi) o->hi = k.hi;
        if (k.share > o->share) o->share = k.share;
        o->when |= k.when;
        o->water |= k.water;
        o->legend |= k.legend;
    }
    return n;
}

/* The caption box sits at the bottom, or at the top while the place
 * picked is down there. */
static int wa_caption_row(void)
{
    return wa.n && WM_SPOTS[wa.pl[wa.cur].spot][1] > 112 ? 0 : 16;
}

static void wa_caption(void)
{
    char buf[64];
    canvas_clear();
    int row = wa_caption_row(), y1 = row * 8 + 6, y2 = y1 + 13;
    canvas_window(0, row, CANVAS_COLS, 4, WIN_STD);
    const Species *s = &SPECIES[wa.sp];
    if (!wa.met || !wa.n) {
        text_draw(12, y1, s->name);
        const char *why = !wa.met ? "Meet it first to learn where it lives."
                        : s->rarity == R_FUSION ? "Only made at the FUSION LOOM."
                        : "It isn't found in the wild.";
        for (int i = 0; i < 3; i++)
            if (STARTER_SPECIES[i] == wa.sp) why = "It comes in a Kindling kit.";
        if (wa.sp == SP_DRAKORA) why = "It soars above STORMSTONE RISE.";
        text_draw_col(12, y2, why, INK_BLUE, INK_BLUE_SH);
        text_draw_right(228, y1, "B:BACK");
        return;
    }
    const KinPlace *k = &wa.pl[wa.cur];
    str_copy(buf, s->name);
    str_put(buf, ": ");
    str_put(buf, MAPS[k->map].name);
    text_draw_fit(12, y1, buf, 180);
    buf[0] = 0;
    str_put_int(buf, wa.cur + 1);
    str_put(buf, "/");
    str_put_int(buf, wa.n);
    text_draw_right(228, y1, buf);
    buf[0] = 0;
    if (wa.via != wa.sp) {
        str_put(buf, "grows from ");
        str_put(buf, SPECIES[wa.via].name);
    } else if (k->hi) {
        str_put(buf, k->share >= 15 ? "common" : k->share >= 8 ? "uncommon" : "rare");
        int w = k->when;
        if (!(w & (1 << WHEN_ANY)) && w == (1 << WHEN_DAY)) str_put(buf, ", day");
        if (!(w & (1 << WHEN_ANY)) && w == (1 << WHEN_NIGHT)) str_put(buf, ", night");
        if (k->water) str_put(buf, ", surf");
        if (k->legend) str_put(buf, ", lair");
    } else {
        str_put(buf, "a legend's lair");
    }
    text_draw_col(12, y2, buf, INK_BLUE, INK_BLUE_SH);
    if (k->hi) {
        str_copy(buf, "Lv");
        str_put_int(buf, k->lo);
        if (k->hi != k->lo) {
            str_put(buf, "-");
            str_put_int(buf, k->hi);
        }
        text_draw_col(228 - text_width(buf), y2, buf, INK_BLUE, INK_BLUE_SH);
    }
}

static void wa_update(void)
{
    wa.t++;
    if (key_hit(KEY_B) || key_hit(KEY_A) || key_hit(KEY_START) || key_hit(KEY_SELECT)) {
        sfx_play(SFX_CANCEL);
        canvas_clear();
        wa.back();
        return;
    }
    int d = (key_rep(KEY_RIGHT) || key_rep(KEY_DOWN)) - (key_rep(KEY_LEFT) || key_rep(KEY_UP));
    if (d && wa.n > 1) {
        wa.cur = (wa.cur + d + wa.n) % wa.n;
        sfx_play(SFX_CURSOR);
        wa_caption();
    }
}

static void wa_draw(void)
{
    if (wa.n) {
        const KinPlace *k = &wa.pl[wa.cur];
        int bob = (wa.t >> 3) & 1;
        spr_push(WM_SPOTS[k->spot][0] - 8, WM_SPOTS[k->spot][1] - 18 - bob, OT_TX(TX_PIN), SQ16, OBANK_TFX, 1, 0);
    }
    for (int i = 0; i < wa.n; i++) {
        const KinPlace *k = &wa.pl[i];
        int blink = ((wa.t >> 4) + i) & 1;
        spr_push(WM_SPOTS[k->spot][0] - 8, WM_SPOTS[k->spot][1] - 8, OT_TX(TX_CURSOR0 + blink), SQ16, OBANK_TFX, 1, 0);
    }
    for (int s = 0; s < WM_COUNT; s++) {
        int kind = WM_SPOTS[s][2];
        spr_push(WM_SPOTS[s][0] - 4, WM_SPOTS[s][1] - 4, OT_TF(kind == 3 ? TF_MARK_SKY : TF_MARK_DIM), SQ8, OBANK_TFX, 1, 0);
    }
}

/* The AREA map for a kin; back() is called when it closes (it must set up
 * its own screen again: this one borrows the field's BG0 tiles). */
static void kin_area_open(int sp, void (*back)(void))
{
    wa.sp = wa.via = sp;
    wa.back = back;
    wa.met = dex_seen[sp] || dex_caught[sp];
    wa.n = wa.cur = wa.t = 0;
    if (wa.met) {
        wa.n = kin_places(sp, wa.pl);
        for (int guard = 0; !wa.n && guard < 4; guard++) {   /* grown kin: where the earlier form lives */
            int p = species_prevo(wa.via);
            if (p < 0) break;
            wa.via = p;
            wa.n = kin_places(p, wa.pl);
        }
        if (!wa.n) wa.via = sp;
    }
    dialog_clear();
    canvas_clear();
    travel_dark_off();
    set_brightness(0);
    travel_load_gfx();
    copy32(VRAM_SCENE_TILES, travel_map_tiles, TRAVEL_MAP_TILE_COUNT * 8);
    u16 *sb = VRAM_MAP(SB_FIELD_BOTTOM);
    for (int y = 0; y < 32; y++)
        for (int x = 0; x < 32; x++) sb[y * 32 + x] = (y < 20 && x < 30) ? travel_map_screen[y * 30 + x] : 0;
    load_pal(bg_palette, travel_map_palette);
    REG_BG0CNT = BGCNT_CHARBLOCK(0) | BGCNT_SCREENBLOCK(SB_FIELD_BOTTOM) | BGCNT_PRIO(3);
    REG_BG0HOFS = REG_BG0VOFS = 0;
    REG_DISPCNT = DCNT_MODE0 | DCNT_BG0 | DCNT_BG1 | DCNT_OBJ | DCNT_OBJ_1D;
    wa_caption();
    ext_open(wa_update, wa_draw, 0);
}

/* ================================================================ */
/*  The crest case                                                  */
/* ================================================================ */

/* The CREST CASE screen lives in menu.c (UI). */
static void crest_case_open(void);

/* ================================================================ */
/*  The FIELD menu (START -> FIELD)                                 */
/* ================================================================ */

enum { FM_BIKE, FM_SURF, FM_STRENGTH, FM_LIGHT, FM_FLY, FM_TELEPORT, FM_CANCEL };
static const char *fm_names[8];
static u8 fm_ids[8];
static int fm_n;

static void fm_add(int id, const char *name)
{
    if (fm_n >= 8) return;
    fm_ids[fm_n] = (u8)id;
    fm_names[fm_n++] = name;
}

static void fm_pick(int c)
{
    if (c < 0 || c >= fm_n) return;
    switch (fm_ids[c]) {
    case FM_BIKE: bike_toggle(0); break;
    case FM_SURF: surf_begin(); break;
    case FM_STRENGTH: strength_use(); break;
    case FM_LIGHT: light_use(); break;
    case FM_FLY: tv.pending = PEND_FLY; break;
    case FM_TELEPORT:
        dlg_say("Your kin closes its eyes... The world folds like a page.");
        tv.pending = PEND_TELEPORT;
        break;
    default: break;
    }
}

/* What the FIELD menu would offer right now (tests use this too). */
static int field_menu_build(void)
{
    const MapDef *m = &MAPS[cur_map];
    int fx = player.x + DIR_DX[player.facing], fy = player.y + DIR_DY[player.facing];
    int x, y;
    fm_n = 0;
    if (bag[ITEM_BIKE] > 0 && map_outdoor() && !travel.surfing) fm_add(FM_BIKE, travel.biking ? "WALK" : "BIKE");
    int nl;   /* not down a cliff or off a bridge (elev.c) */
    if (!travel.surfing && travel_surf_cell(fx, fy) && travel_ability_kin(AB_SURF) >= 0 &&
        elev_enter(player.x, player.y, player.level, player.facing, &nl) == ELEV_FLOOR)
        fm_add(FM_SURF, "SURF");
    if (!tv.strength_on && map_has(OBJ_BOULDER) && travel_ability_kin(AB_STRENGTH) >= 0) fm_add(FM_STRENGTH, "STRENGTH");
    if (!tv.light_on && (m->flags & MF_DARK) && travel_ability_kin(AB_LIGHT) >= 0) fm_add(FM_LIGHT, "LIGHT");
    if (map_outdoor() && !(m->flags & (MF_NOFLY | MF_DEBUG)) && travel_ability_kin(AB_FLY) >= 0) fm_add(FM_FLY, "FLY");
    if (!(m->flags & MF_DEBUG) && travel_ability_kin(AB_TELEPORT) >= 0 && hearth_spot(&x, &y))
        fm_add(FM_TELEPORT, "TELEPORT");
    return fm_n;
}

/* The FIELD menu on START: surf, fly, teleport, light, strength, bike. */
static void travel_field_menu_open(void)
{
    if (!field_menu_build()) {
        dlg_say(travel_crest_count()
                    ? "There's nothing your kin can do here right now."
                    : "Hall crests let your kin help out in the field. You don't have any yet.");
        return;
    }
    fm_add(FM_CANCEL, "CANCEL");
    dlg_ask("Which field ability?", fm_names, fm_n, fm_pick);
}

/* ================================================================ */
/*  Items                                                           */
/* ================================================================ */

/* LURE INCENSE and WAYSTONE. */
static int travel_use_item(int item)
{
    const Item *it = &ITEMS[item];
    if (bag[item] <= 0) return 0;
    if (it->kind == IK_LURE) {
        int steps = (it->param ? it->param : 20) * 10;
        travel.lure_lo = (u8)(steps & 255);
        travel.lure_hi = (u8)(steps >> 8);
        bag[item]--;
        sfx_play(SFX_SPARKLE);
        dlg_say("You lit the LURE INCENSE. A sweet smoke drifts out: rare kin will come looking.");
        return 1;
    }
    if (it->kind == IK_WAYSTONE) {
        int x, y;
        if ((MAPS[cur_map].flags & MF_DEBUG) || !hearth_spot(&x, &y)) {
            dlg_say("The WAYSTONE stays cold here.");
            return 0;
        }
        bag[item]--;
        dlg_say("The WAYSTONE glows warm in your hand...");
        tv.pending = PEND_TELEPORT;
        return 1;
    }
    dlg_say("Nothing happens.");
    return 0;
}

/* KEY items owned by traversal: BIKE, FERRY PASS, TOWN MAP, CREST CASE, RUNESTONE. */
static int travel_key_use(int key)
{
    if (key == ITEMS[ITEM_BIKE].param) return bike_toggle(0);
    if (key == ITEMS[ITEM_TOWN_MAP].param) {
        worldmap_open(0);
        return 1;
    }
    if (key == ITEMS[ITEM_CREST_CASE].param) {
        crest_case_open();
        return 1;
    }
    if (key == ITEMS[ITEM_RUNESTONE].param) return runestone_use();
    if (key == ITEMS[ITEM_FERRY_PASS].param) {
        dlg_say("Show it at any ferry post to sail for free.");
        return 0;
    }
    dlg_say("Not now.");
    return 0;
}
