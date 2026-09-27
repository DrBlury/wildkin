/*
 * Puzzle solver: proves that every map can actually be played through.
 *
 * For every map (debug viewer maps excepted) this searches the true game
 * state: the player's cell, every boulder, the switch groups, the opened
 * gates and the answered legends. Every move that could change something
 * (a boulder push, a ledge hop, an ice slide, a current, a teleport pad, a
 * switch, surfing, a door, an exit mat, a map edge) is played by the REAL
 * game code: the state is written into travel.c's objects and the player,
 * then player_try_move() / surf_begin() run and the frames are stepped
 * with travel_update() / actor_step() / travel_player_arrived() exactly as
 * field_player_update() does, and the resulting state is read back.
 *
 * Only plain steps between two plain cells (walkable, nothing special on
 * arrival, no door, mat, ledge, edge, water or object) take a fast path;
 * validate_fast_path() replays every such step on every map through the
 * real code and fails on any disagreement, so the solver cannot drift from
 * the game.
 *
 * Plain steps that work both ways join cells into a component; a search
 * node is (objects state, component). The search is a 0-1 BFS where an
 * "event" (a push, a switch press, a legend answered, leaving and coming
 * back) costs 1 and everything else 0, so the depth of a node is the fewest
 * events needed to reach it.
 *
 * It then checks, per map:
 *   - every target is reachable from the entrances: every person (standing
 *     beside them, or across a counter), every satchel, chest, legend and
 *     ferry, every door / ladder out, every linked edge and the exit mat;
 *   - no soft-lock: from every reachable state some exit can still be
 *     reached (a map reload, which resets boulders and switches, is only
 *     possible through an exit). Leaving through an exit and coming back in
 *     through any entrance keeps the persistent state (opened gates,
 *     answered legends), as travel.c does.
 *
 * Abilities: Halls must be solvable with no SURF or STRENGTH (they are
 * self-contained); every other map is searched with SURF + STRENGTH (+ FLY
 * landings). Soft-locks are checked under both ability sets.
 */
#include "harness.h"
#include <stdint.h>
#include <stdlib.h>
typedef uint64_t u64;

#define CELLS (MAP_MAX_W * MAP_MAX_H)
#define LEVELS 4                    /* elevation levels (elev.c: 2 bits) */
#define POSMAX (CELLS * LEVELS)     /* a position: level * NC + cell */
#define KEY_MAX 40
#define NIL 0xFFFFFFFFu

enum { ABL_SURF = 1, ABL_STRENGTH = 2, ABL_FLY = 4, ABL_ALL = 7 };
enum { SA_MOVE, SA_SURF, SA_LEGEND, SA_REENTER, SA_PLAIN, SA_START };
enum { R_BLOCK, R_MOVE, R_EXIT, R_LOOP };
enum { FM_SIM = -2, FM_BLOCK = -1 };

/* ---------------- the map being solved ---------------- */

static int W, H, NC, abil;
static int elevated;            /* the map has a height layer: every step goes through the game */
static u16 sattr[CELLS];        /* cell_attr with the movable objects taken out */
static u8 swalk[CELLS];         /* cell_walkable, same */
static u8 ssurf[CELLS];         /* travel_surf_cell, same */
static u8 special[CELLS];       /* arriving here does something */
static u8 dyn[CELLS];           /* loaded state: 1 boulder, 2 other solid object */
static s16 exit_cache[POSMAX * 4];  /* -1 unknown, 0 bump, 1+LINK edge, 5 mat, 16+warp */

static int nb, np, keylen;
static int nsat;                /* satchels on the map: one more state bit, "all taken" */
static u16 sat_idx[64], sat_cell[64];
#define SAT_BIT (np)                /* its index among the lasting bits */
static u8 bobj[TOBJ_MAX], pobj[TOBJ_MAX];
static u8 key_init[KEY_MAX];

static int is_dynamic(int kind)
{
    return kind == OBJ_BOULDER || kind == OBJ_GATE || kind == OBJ_BARRIER || kind == OBJ_LEGEND;
}

/* ---------------- state <-> game ---------------- */

static void grid_rebuild(void)
{
    memset(obj_grid, 0, (size_t)(W * H));
    for (int i = 0; i < tobj_count; i++) grid_cell(tobj[i].x, tobj[i].y);
}

static void capture(u8 *k)
{
    memset(k, 0, KEY_MAX);
    for (int s = 0; s < nb;) {
        int e = s;
        while (e < nb && tobj[bobj[e]].arg == tobj[bobj[s]].arg) e++;
        int pos[TOBJ_MAX], n = 0;
        for (int i = s; i < e; i++) pos[n++] = tobj[bobj[i]].y * W + tobj[bobj[i]].x;
        for (int i = 1; i < n; i++)
            for (int j = i; j > 0 && pos[j - 1] > pos[j]; j--) {
                int t = pos[j];
                pos[j] = pos[j - 1];
                pos[j - 1] = t;
            }
        for (int i = 0; i < n; i++) {
            k[2 * (s + i)] = (u8)(pos[i] % W);
            k[2 * (s + i) + 1] = (u8)(pos[i] / W);
        }
        s = e;
    }
    int sw = 0;
    for (int g = 0; g < 16; g++) sw |= (sw_on[g] & 1) << g;
    k[2 * nb] = (u8)(sw & 255);
    k[2 * nb + 1] = (u8)(sw >> 8);
    for (int j = 0; j < np; j++)
        if (tobj[pobj[j]].state) k[2 * nb + 2 + j / 8] |= (u8)(1u << (j & 7));
    if (nsat && item_taken(sat_idx[0])) k[2 * nb + 2 + SAT_BIT / 8] |= (u8)(1u << (SAT_BIT & 7));
}

static void restore(const u8 *k)
{
    for (int i = 0; i < nb; i++) {
        TObj *o = &tobj[bobj[i]];
        o->x = k[2 * i];
        o->y = k[2 * i + 1];
        o->ox = o->oy = 0;
    }
    int sw = k[2 * nb] | (k[2 * nb + 1] << 8);
    for (int g = 0; g < 16; g++) sw_on[g] = (u8)((sw >> g) & 1);
    for (int j = 0; j < np; j++) {
        TObj *o = &tobj[pobj[j]];
        int bit = (k[2 * nb + 2 + j / 8] >> (j & 7)) & 1;
        o->state = (u8)(o->kind == OBJ_GATE ? (bit ? 2 : 0) : bit);
        o->anim = 0;
    }
    if (nsat) {
        int taken = (k[2 * nb + 2 + SAT_BIT / 8] >> (SAT_BIT & 7)) & 1;
        for (int i = 0; i < nsat; i++) {
            if (taken) item_take(sat_idx[i]);
            else bit_clear(item_bits, sat_idx[i]);
        }
    }
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].kind == OBJ_BARRIER) tobj[i].state = (u8)barrier_up(&tobj[i]);
    grid_rebuild();
    plates_update(0);
}

static void place_player(int c)
{
    player.level = (u8)(c / NC);
    c %= NC;
    player.x = (s16)(c % W);
    player.y = (s16)(c / W);
    player.ox = player.oy = 0;
    player.moving = 0;
    player.hop = 0;
    player.anim = 0;
    player.facing = DIR_DOWN;
    travel.surfing = (cell_attr(player.x, player.y) & A_WATER) != 0;
    travel.biking = 0;
    tv.slide = tv.hop1 = tv.push_t = tv.busy = 0;
    tv.flash_t = tv.splash_t = 0;
    tv.pending = 0;
    tv.strength_on = (abil & ABL_STRENGTH) != 0;
    warp.active = 0;
    keys_now = keys_prev = 0;
}

/* ---------------- tables ---------------- */

typedef struct {
    u32 macro;
    u16 canon, cell;    /* the cell the node was first entered at */
    u32 depth;
    u32 entry;          /* the entry that created it */
    u8 exit;
} Node;

typedef struct {
    u32 macro;
    u16 cell, src;      /* where the player ends up; where the move started */
    u32 parent;         /* node, or NIL for a start */
    u32 node;           /* resolved when processed */
    u32 depth;
    u8 act, dir;
} Entry;

static u8 *mkeys;
static u32 mcount, mcap, *mhash, mhcap;
static Node *nodes;
static u32 ncount, ncap;
static u64 *nhash_k;
static u32 *nhash_v, nhcap;
static Entry *entries;
static u32 ecount, ecap;
static u32 *layer[2];
static u32 lcount[2], lcap[2];
static int cur_l;               /* the list of the depth being searched */

static u32 ENTRY_CAP = 12000000u;

static u32 hash_bytes(const u8 *k, int n)
{
    u32 h = 2166136261u;
    for (int i = 0; i < n; i++) h = (h ^ k[i]) * 16777619u;
    return h;
}

static void *grow(void *p, u32 *cap, u32 need, size_t sz)
{
    if (need <= *cap) return p;
    u32 c = *cap ? *cap : 1024;
    while (c < need) c *= 2;
    p = realloc(p, (size_t)c * sz);
    if (!p) {
        printf("FAIL: out of memory\n");
        exit(1);
    }
    *cap = c;
    return p;
}

static u32 macro_intern(const u8 *k)
{
    if (mcount * 2 + 2 > mhcap) {
        u32 nc = mhcap ? mhcap * 2 : 4096;
        free(mhash);
        mhash = malloc((size_t)nc * sizeof(u32));
        memset(mhash, 0xFF, (size_t)nc * sizeof(u32));
        mhcap = nc;
        for (u32 i = 0; i < mcount; i++) {
            u32 h = hash_bytes(mkeys + (size_t)i * keylen, keylen) & (mhcap - 1);
            while (mhash[h] != NIL) h = (h + 1) & (mhcap - 1);
            mhash[h] = i;
        }
    }
    u32 h = hash_bytes(k, keylen) & (mhcap - 1);
    while (mhash[h] != NIL) {
        if (!memcmp(mkeys + (size_t)mhash[h] * keylen, k, (size_t)keylen)) return mhash[h];
        h = (h + 1) & (mhcap - 1);
    }
    mkeys = grow(mkeys, &mcap, mcount + 1, (size_t)keylen);
    memcpy(mkeys + (size_t)mcount * keylen, k, (size_t)keylen);
    mhash[h] = mcount;
    return mcount++;
}

static const u8 *macro_key(u32 m) { return mkeys + (size_t)m * keylen; }

static u64 nkey(u32 macro, int canon) { return ((u64)macro << 16) | (u64)canon; }

static u32 node_find(u64 k)
{
    if (!nhcap) return NIL;
    u32 h = (u32)((k * 0x9E3779B97F4A7C15ull) >> 32) & (nhcap - 1);
    while (nhash_v[h] != NIL) {
        if (nhash_k[h] == k) return nhash_v[h];
        h = (h + 1) & (nhcap - 1);
    }
    return NIL;
}

static void node_put(u64 k, u32 v)
{
    if (ncount * 2 + 2 > nhcap) {
        u32 nc = nhcap ? nhcap * 2 : 4096;
        u64 *ok = nhash_k;
        u32 *ov = nhash_v, oc = nhcap;
        nhash_k = malloc((size_t)nc * sizeof(u64));
        nhash_v = malloc((size_t)nc * sizeof(u32));
        memset(nhash_v, 0xFF, (size_t)nc * sizeof(u32));
        nhcap = nc;
        for (u32 i = 0; i < oc; i++)
            if (ov[i] != NIL) {
                u32 h = (u32)((ok[i] * 0x9E3779B97F4A7C15ull) >> 32) & (nhcap - 1);
                while (nhash_v[h] != NIL) h = (h + 1) & (nhcap - 1);
                nhash_k[h] = ok[i];
                nhash_v[h] = ov[i];
            }
        free(ok);
        free(ov);
    }
    u32 h = (u32)((k * 0x9E3779B97F4A7C15ull) >> 32) & (nhcap - 1);
    while (nhash_v[h] != NIL) h = (h + 1) & (nhcap - 1);
    nhash_k[h] = k;
    nhash_v[h] = v;
}

static void tables_reset(void)
{
    mcount = ncount = ecount = 0;
    free(mkeys);   /* the key length changes from map to map */
    mkeys = NULL;
    mcap = 0;
    if (mhash) memset(mhash, 0xFF, (size_t)mhcap * sizeof(u32));
    if (nhash_v) memset(nhash_v, 0xFF, (size_t)nhcap * sizeof(u32));
    lcount[0] = lcount[1] = 0;
}

static int overflow;

static void add_entry(u32 macro, int cell, u32 parent, int src, int act, int dir, u32 depth, int cost)
{
    if (ecount >= ENTRY_CAP) {
        overflow = 1;
        return;
    }
    entries = grow(entries, &ecap, ecount + 1, sizeof(Entry));
    Entry *e = &entries[ecount];
    e->macro = macro;
    e->cell = (u16)cell;
    e->src = (u16)src;
    e->parent = parent;
    e->node = NIL;
    e->depth = depth + (u32)cost;
    e->act = (u8)act;
    e->dir = (u8)dir;
    int l = cost ? cur_l ^ 1 : cur_l;
    layer[l] = grow(layer[l], &lcap[l], lcount[l] + 1, sizeof(u32));
    layer[l][lcount[l]++] = ecount++;
}

/* ---------------- the loaded state ---------------- */


/* ---------------- the loaded state ---------------- */

static u32 loaded = NIL;        /* the state travel.c's run-time objects hold */
static u32 dyn_m = NIL;         /* the state dyn[] describes */
static u16 dyn_cells[TOBJ_MAX + 64];
static int dyn_n;

static void real_load(u32 m)
{
    if (loaded == m) return;
    restore(macro_key(m));
    loaded = m;
}

static void dyn_set(u32 m)
{
    if (dyn_m == m) return;
    for (int i = 0; i < dyn_n; i++) dyn[dyn_cells[i]] = 0;
    dyn_n = 0;
    real_load(m);
    for (int i = 0; i < tobj_count; i++)
        if (is_dynamic(tobj[i].kind)) dyn_cells[dyn_n++] = (u16)(tobj[i].y * W + tobj[i].x);
    for (int i = 0; i < tobj_count; i++) {
        const TObj *o = &tobj[i];
        if (!is_dynamic(o->kind)) continue;
        int c = o->y * W + o->x;
        if (o->kind == OBJ_BOULDER) dyn[c] = 1;
        else if (!dyn[c] && (obj_attr(o) & A_SOLID)) dyn[c] = 2;
    }
    if (nsat && !((macro_key(m)[2 * nb + 2 + SAT_BIT / 8] >> (SAT_BIT & 7)) & 1))
        for (int i = 0; i < nsat; i++) {
            dyn_cells[dyn_n++] = sat_cell[i];
            if (!dyn[sat_cell[i]]) dyn[sat_cell[i]] = 2;
        }
    dyn_m = m;
}

/* The fast path for a step from c: the cell it lands on (a plain step),
 * FM_BLOCK (a certain bump) or FM_SIM (let the game play it). */
static int fast_move(int c, int d)
{
    if (elevated) return FM_SIM;
    int x = c % W, y = c / W, nx = x + DIR_DX[d], ny = y + DIR_DY[d];
    if (nx < 0 || ny < 0 || nx >= W || ny >= H) return FM_SIM;
    int a = sattr[c];
    int n = ny * W + nx, b = sattr[n];
    if (a & A_WATER) {   /* surfing */
        if (b & A_DOOR) return FM_SIM;
        if (dyn[n]) return dyn[n] == 1 ? FM_SIM : FM_BLOCK;
        if (ssurf[n]) return (b & A_CURRENT) ? FM_SIM : n;
        if (swalk[n] && !(b & A_WATER)) return special[n] ? FM_SIM : n;   /* back onto land */
        return FM_BLOCK;
    }
    if (d == DIR_DOWN && (a & A_EXIT)) return FM_SIM;
    if (b & A_DOOR) return FM_SIM;
    if (dyn[n] == 1) return FM_SIM;
    if (dyn[n] == 2) return FM_BLOCK;
    if (d == DIR_DOWN && (b & A_LEDGE)) return FM_SIM;
    if (!swalk[n]) return FM_BLOCK;
    if (special[n]) return FM_SIM;
    return n;
}

/* ---------------- one move, played by the real game ---------------- */

static int sim(u32 m, int c, int d, int act, u32 *om, int *oc, int *exit_code)
{
    restore(macro_key(m));
    loaded = NIL;
    place_player(c);
    int cl = c % NC, x = cl % W, y = cl / W, nx = x + DIR_DX[d], ny = y + DIR_DY[d];
    int r;
    if (act == SA_SURF) {
        player.facing = (u8)d;
        int nl;
        if (elev_enter(player.x, player.y, player.level, d, &nl) == ELEV_BLOCK) return R_BLOCK;
        if (travel.surfing || obj_index_at(nx, ny) >= 0 || !travel_surf_cell(nx, ny)) return R_BLOCK;
        surf_begin();
        r = 1;
    } else {
        r = player_try_move(d);
    }
    if (warp.active) {
        static const u8 LINK_FOR_DIR[4] = { LINK_S, LINK_N, LINK_W, LINK_E };
        warp.active = 0;
        int out = nx < 0 || ny < 0 || nx >= W || ny >= H;
        if (d == DIR_DOWN && (cell_attr(x, y) & A_EXIT) && (out || !(cell_attr(nx, ny) & A_DOOR))) *exit_code = 5;
        else if (out) *exit_code = 1 + LINK_FOR_DIR[d];
        else *exit_code = 16 + warp_at(cur_map, nx, ny);
        return R_EXIT;
    }
    if (!r) return R_BLOCK;
    int f;
    for (f = 0; f < 6000; f++) {
        if (travel_update()) continue;
        if (player.moving) {
            if (actor_step(&player, travel_speed(player.hop ? 2 : 1))) {
                elev_player_arrived();
                travel_player_arrived();
            }
            continue;
        }
        int busy = 0;
        for (int i = 0; i < tobj_count; i++)
            if (tobj[i].ox || tobj[i].oy || (tobj[i].kind == OBJ_GATE && tobj[i].state == 1)) busy = 1;
        if (!busy) break;
    }
    if (f >= 6000) return R_LOOP;
    u8 k[KEY_MAX];
    capture(k);
    *om = macro_intern(k);
    *oc = player.level * NC + player.y * W + player.x;
    if (*om == m && *oc == c) return R_BLOCK;
    return R_MOVE;
}

/* ---------------- targets ---------------- */

enum { T_NPC, T_SATCHEL, T_CHEST, T_LEGEND, T_FERRY, T_WARP, T_EDGE, T_MAT };
static const char *const T_KIND[] = { "person", "satchel", "chest", "legend", "ferry", "door", "edge", "exit mat" };
static const char *const EDGE_NAME[4] = { "north", "south", "west", "east" };

typedef struct {
    int kind, idx, x, y;
    const char *name;
    u32 node, depth;
    int from;           /* the cell it was reached from */
} Target;

#define TGT_MAX 160
static Target tgt[TGT_MAX];
static int ntgt;
static s16 tgt_at[CELLS];
static int tgt_edge[4], tgt_mat;
static s16 tgt_warp[256];
static u8 legend_at[CELLS];     /* persist index + 1 of a legend */
static u8 ferry_at[CELLS];
static u8 sat_at[CELLS];        /* a satchel lies here */

static int tgt_add(int kind, int idx, int x, int y, const char *name)
{
    if (ntgt >= TGT_MAX) return -1;
    Target *t = &tgt[ntgt];
    t->kind = kind;
    t->idx = idx;
    t->x = x;
    t->y = y;
    t->name = name;
    t->node = NIL;
    t->depth = NIL;
    t->from = -1;
    if (kind <= T_FERRY) tgt_at[y * W + x] = (s16)ntgt;
    return ntgt++;
}

static void tgt_hit(int t, u32 node, int from)
{
    if (t < 0) return;
    if (tgt[t].node == NIL || nodes[node].depth < tgt[t].depth) {
        tgt[t].node = node;
        tgt[t].depth = nodes[node].depth;
        tgt[t].from = from;
    }
}

static void tgt_hit_exit(int code, u32 node, int from)
{
    if (code >= 1 && code <= 4) tgt_hit(tgt_edge[code - 1], node, from);
    else if (code == 5) tgt_hit(tgt_mat, node, from);
    else if (code >= 16 && code - 16 < 256) tgt_hit(tgt_warp[code - 16], node, from);
}

/* ---------------- the search ---------------- */

static u32 cmark[POSMAX], cgen;
static u16 comp[POSMAX];
static int ncomp;

/* The component of `s` (plain steps both ways) in the state dyn[] holds;
 * returns its smallest cell. */
static int flood_comp(int s)
{
    cgen++;
    ncomp = 0;
    comp[ncomp++] = (u16)s;
    cmark[s] = cgen;
    int canon = s;
    for (int h = 0; h < ncomp; h++) {
        int c = comp[h];
        if (c < canon) canon = c;
        for (int d = 0; d < 4; d++) {
            int n = fast_move(c, d);
            if (n < 0 || cmark[n] == cgen || fast_move(n, DIR_BACK[d]) != c) continue;
            cmark[n] = cgen;
            comp[ncomp++] = (u16)n;
        }
    }
    return canon;
}

/* Distance between two cells of one component (plain steps). */
static int comp_dist(u32 m, int a, int b)
{
    static s16 dist[POSMAX];
    static u16 q[POSMAX];
    dyn_set(m);
    for (int i = 0; i < NC * LEVELS; i++) dist[i] = -1;
    int head = 0, tail = 0;
    q[tail++] = (u16)a;
    dist[a] = 0;
    while (head < tail) {
        int c = q[head++];
        if (c == b) return dist[c];
        for (int d = 0; d < 4; d++) {
            int n = fast_move(c, d);
            if (n < 0 || dist[n] >= 0 || fast_move(n, DIR_BACK[d]) != c) continue;
            dist[n] = (s16)(dist[c] + 1);
            q[tail++] = (u16)n;
        }
    }
    return 0;
}

static u16 entr[512];             /* positions */
static int nentr;
static u64 reentered[256];
static int nreentered, loops_found, cache_odd;

static u64 persist_bits(const u8 *k)
{
    u64 p = 0;
    for (int j = 0; j < np + (nsat ? 1 : 0) && j < 64; j++)
        if ((k[2 * nb + 2 + j / 8] >> (j & 7)) & 1) p |= 1ull << j;
    return p;
}

/* Leave through an exit and come back through any entrance: boulders and
 * switches reset, opened gates and answered legends stay. */
static void reenter(u32 from, int src, u32 depth)
{
    u8 k[KEY_MAX];
    memcpy(k, macro_key(nodes[from].macro), KEY_MAX > keylen ? (size_t)keylen : KEY_MAX);
    u64 p = persist_bits(k);
    for (int i = 0; i < nreentered; i++)
        if (reentered[i] == p) return;
    if (nreentered < 256) reentered[nreentered++] = p;
    u8 nk[KEY_MAX];
    memcpy(nk, key_init, KEY_MAX);
    memcpy(nk + 2 * nb + 2, k + 2 * nb + 2, (size_t)(keylen - 2 * nb - 2));
    restore(nk);
    loaded = NIL;
    capture(nk);
    u32 m = macro_intern(nk);
    for (int i = 0; i < nentr; i++) add_entry(m, entr[i], from, src, SA_REENTER, 0, depth, 1);
}

static void mark_exit(u32 id, int c)
{
    if (nodes[id].exit) return;
    nodes[id].exit = 1;
    reenter(id, c, nodes[id].depth);
}

/* Same-state targets found from one node: skip a cell whose component
 * already got an entry. */
static u32 tmark[POSMAX], tgen;

static int same_seen(int t)
{
    static u16 q[POSMAX];
    if (tmark[t] == tgen) return 1;
    int n = 0;
    q[n++] = (u16)t;
    tmark[t] = tgen;
    for (int h = 0; h < n; h++) {
        int c = q[h];
        for (int d = 0; d < 4; d++) {
            int k = fast_move(c, d);
            if (k < 0 || tmark[k] == tgen || fast_move(k, DIR_BACK[d]) != c) continue;
            tmark[k] = tgen;
            q[n++] = (u16)k;
        }
    }
    return 0;
}

static void process_node(u32 id)
{
    tgen++;
    u32 m = nodes[id].macro, depth = nodes[id].depth;
    static u16 cells[POSMAX];
    int n = ncomp;
    memcpy(cells, comp, (size_t)n * sizeof(u16));
    u32 gen = cgen;
    u8 key[KEY_MAX];
    memset(key, 0, sizeof(key));
    memcpy(key, macro_key(m), (size_t)keylen);
    for (int i = 0; i < n; i++) {
        int c = cells[i], cl = c % NC, lvl = c / NC, x = cl % W, y = cl / W;
        for (int d = 0; d < 4; d++) {
            int nx = x + DIR_DX[d], ny = y + DIR_DY[d];
            int inside = nx >= 0 && ny >= 0 && nx < W && ny < H;
            if (inside) {
                int nc = ny * W + nx;
                int t = tgt_at[nc];
                /* people and satchels across a cliff or under a deck are out of reach
                 * (field_try_interact); objects can still be used */
                int nl, reach = elev_enter(x, y, lvl, d, &nl) != ELEV_BLOCK;
                if (t >= 0 && !reach && (tgt[t].kind == T_NPC || tgt[t].kind == T_SATCHEL)) t = -1;
                int sat_taken = nsat && ((key[2 * nb + 2 + SAT_BIT / 8] >> (SAT_BIT & 7)) & 1);
                if (t >= 0 && !(tgt[t].kind == T_SATCHEL && sat_taken)) tgt_hit(t, id, c);
                if (sat_at[nc] && reach && !sat_taken) {   /* pick it up: the way is clear from now on */
                    u8 k[KEY_MAX];
                    memcpy(k, key, KEY_MAX);
                    k[2 * nb + 2 + SAT_BIT / 8] |= (u8)(1u << (SAT_BIT & 7));
                    add_entry(macro_intern(k), c, id, c, SA_LEGEND, d, depth, 1);
                }
                if (t < 0 && reach && (sattr[nc] & A_COUNTER)) {
                    int fx = nx + DIR_DX[d], fy = ny + DIR_DY[d];
                    if (fx >= 0 && fy >= 0 && fx < W && fy < H && tgt_at[fy * W + fx] >= 0 &&
                        tgt[tgt_at[fy * W + fx]].kind == T_NPC)
                        tgt_hit(tgt_at[fy * W + fx], id, c);
                }
                if (ferry_at[nc]) mark_exit(id, c);
                /* answer a legend: it is gone for good */
                int j = legend_at[nc] - 1;
                if (j >= 0 && !((key[2 * nb + 2 + j / 8] >> (j & 7)) & 1)) {
                    u8 k[KEY_MAX];
                    memcpy(k, key, KEY_MAX);
                    k[2 * nb + 2 + j / 8] |= (u8)(1u << (j & 7));
                    add_entry(macro_intern(k), c, id, c, SA_LEGEND, d, depth, 1);
                }
            }
            int r = fast_move(c, d);
            if (r >= 0) {
                if (cmark[r] != gen && !same_seen(r)) add_entry(m, r, id, c, SA_PLAIN, d, depth, 0);
                continue;
            }
            if (r == FM_BLOCK) continue;
            int cacheable = !inside || (sattr[ny * W + nx] & A_DOOR) || (d == DIR_DOWN && (sattr[cl] & A_EXIT));
            int code = 0, oc = 0;
            u32 om = NIL;
            if (cacheable && exit_cache[c * 4 + d] >= 0) {
                code = exit_cache[c * 4 + d];
                if (code) {
                    tgt_hit_exit(code, id, c);
                    mark_exit(id, c);
                }
                continue;
            }
            int res = sim(m, c, d, SA_MOVE, &om, &oc, &code);
            if (cacheable) {
                if (res == R_EXIT) exit_cache[c * 4 + d] = (s16)code;
                else if (res == R_BLOCK) exit_cache[c * 4 + d] = 0;
                else cache_odd++;
            }
            if (res == R_EXIT) {
                tgt_hit_exit(code, id, c);
                mark_exit(id, c);
            } else if (res == R_LOOP) {
                if (loops_found++ < 5)
                    printf("  %s: endless forced move from %d,%d dir %d\n", MAPS[cur_map].name, x, y, d);
            } else if (res == R_MOVE) {
                if (om != m || (cmark[oc] != gen && !same_seen(oc))) add_entry(om, oc, id, c, SA_MOVE, d, depth, om != m);
            }
        }
        /* SURF from the shore */
        if ((abil & ABL_SURF) && !(sattr[cl] & A_WATER))
            for (int d = 0; d < 4; d++) {
                int nx = x + DIR_DX[d], ny = y + DIR_DY[d];
                if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
                int b = sattr[ny * W + nx];
                if (!(b & A_WATER) || (b & A_DEEP)) continue;
                int nc = ny * W + nx;
                if (dyn[nc] || !ssurf[nc]) continue;
                if (!(b & A_CURRENT) && !elevated) {   /* the fast path: one hop onto the water */
                    if (!same_seen(nc)) add_entry(m, nc, id, c, SA_SURF, d, depth, 0);
                    continue;
                }
                int oc, code;
                u32 om;
                if (sim(m, c, d, SA_SURF, &om, &oc, &code) == R_MOVE)
                    add_entry(om, oc, id, c, SA_SURF, d, depth, om != m);
            }
    }
}

static void search(void)
{
    while (!overflow) {
        if (!lcount[cur_l]) {
            if (!lcount[cur_l ^ 1]) break;
            cur_l ^= 1;   /* the next depth */
            continue;
        }
        u32 ei = layer[cur_l][--lcount[cur_l]];
        Entry e = entries[ei];
        dyn_set(e.macro);
        int canon = flood_comp(e.cell);
        u64 k = nkey(e.macro, canon);
        u32 id = node_find(k);
        if (id != NIL) {
            entries[ei].node = id;
            continue;
        }
        nodes = grow(nodes, &ncap, ncount + 1, sizeof(Node));
        id = ncount++;
        if ((id & 0x3FFFF) == 0 && id && getenv("PZ_TRACE"))
            fprintf(stderr, "  ... %u nodes %u states %u entries depth %u\n", id, mcount, ecount, e.depth);
        node_put(k, id);
        Node *nd = &nodes[id];
        nd->macro = e.macro;
        nd->canon = (u16)canon;
        nd->cell = e.cell;
        nd->depth = e.depth;
        nd->entry = ei;
        nd->exit = 0;
        entries[ei].node = id;
        process_node(id);
    }
}

/* ---------------- per map ---------------- */

static int is_hall(int m)
{
    return m == MAP_VOLT_HALL || m == MAP_CURRENT_HALL || m == MAP_ANVIL_HALL || m == MAP_RIME_HALL ||
           m == MAP_LANTERN_CRYPT || m == MAP_MIRROR_HALL;
}

/* Maps worth a line in the summary: puzzle objects or puzzle tiles. */
static int interesting;

/* An entrance, on the level you arrive on facing `facing` (field_enter_map). */
static void entr_add(int x, int y, int facing)
{
    if (x < 0 || y < 0 || x >= W || y >= H || nentr >= 512) return;
    int c = elev_level_at(x, y, -1, facing) * NC + y * W + x;
    for (int i = 0; i < nentr; i++)
        if (entr[i] == c) return;
    entr[nentr++] = (u16)c;
}

static void setup_map(int m, int ability)
{
    memset(travel.puzzle, 0, sizeof(travel.puzzle));
    abil = ability;
    map_load(m);
#ifdef PZ_PATCH
    PZ_PATCH(m);
#endif
    W = map_w;
    H = map_h;
    NC = W * H;
    elevated = map_elevated;
    nb = np = 0;
    for (int a = 0; a < 256; a++)
        for (int i = 0; i < tobj_count; i++)
            if (tobj[i].kind == OBJ_BOULDER && tobj[i].arg == a) bobj[nb++] = (u8)i;
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].kind == OBJ_GATE || tobj[i].kind == OBJ_LEGEND) pobj[np++] = (u8)i;
    nsat = 0;
    for (int i = 0; i < ITEM_BALL_COUNT && nsat < 64; i++)
        if (ITEM_BALLS[i].map == m) {
            sat_idx[nsat] = (u16)i;
            sat_cell[nsat++] = (u16)(ITEM_BALLS[i].y * W + ITEM_BALLS[i].x);
        }
    for (int i = 0; i < nsat; i++) bit_clear(item_bits, sat_idx[i]);
    keylen = 2 * nb + 2 + (np + (nsat ? 1 : 0) + 7) / 8;
    if (keylen > KEY_MAX) {
        printf("FAIL: %s has too many objects for the solver\n", MAPS[m].name);
        exit(1);
    }
    /* the static picture: movable objects and satchels taken out */
    for (int i = 0; i < nsat; i++) item_take(sat_idx[i]);
    memset(dyn, 0, sizeof(dyn));
    dyn_n = 0;
    for (int i = 0; i < tobj_count; i++)
        if (is_dynamic(tobj[i].kind)) obj_grid[tobj[i].y * W + tobj[i].x] = 0;
    interesting = is_hall(m);
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].kind != OBJ_BERRY && tobj[i].kind != OBJ_FERRY) interesting = 1;
    for (int c = 0; c < NC; c++) {
        int x = c % W, y = c / W;
        sattr[c] = (u16)cell_attr(x, y);
        swalk[c] = (u8)cell_walkable(x, y);
        ssurf[c] = (u8)travel_surf_cell(x, y);
        special[c] = (sattr[c] & (A_ICE | A_CURRENT | A_WATER | A_PAD | A_SWITCH)) != 0;
        if (sattr[c] & (A_ICE | A_CURRENT | A_PAD | A_SWITCH | A_LEDGE)) interesting = 1;
        tgt_at[c] = -1;
        legend_at[c] = 0;
        ferry_at[c] = 0;
        sat_at[c] = 0;
    }
    for (int i = 0; i < nsat; i++) {
        bit_clear(item_bits, sat_idx[i]);
        sat_at[sat_cell[i]] = 1;
    }
    grid_rebuild();
    for (int i = 0; i < NC * LEVELS * 4; i++) exit_cache[i] = -1;
    for (int j = 0; j < np; j++)
        if (tobj[pobj[j]].kind == OBJ_LEGEND) legend_at[tobj[pobj[j]].y * W + tobj[pobj[j]].x] = (u8)(j + 1);
    capture(key_init);
    tables_reset();
    loaded = dyn_m = NIL;
    cur_l = 0;
    overflow = 0;
    nreentered = 0;

    /* targets */
    ntgt = 0;
    for (int i = 0; i < 4; i++) tgt_edge[i] = -1;
    for (int i = 0; i < 256; i++) tgt_warp[i] = -1;
    tgt_mat = -1;
    for (int i = 0; i < NPC_COUNT; i++)
        if (NPCS[i].map == m) tgt_add(T_NPC, i, NPCS[i].x, NPCS[i].y, NPCS[i].name ? NPCS[i].name : "warden");
    for (int i = 0; i < ITEM_BALL_COUNT; i++)
        if (ITEM_BALLS[i].map == m) tgt_add(T_SATCHEL, i, ITEM_BALLS[i].x, ITEM_BALLS[i].y, "satchel");
    for (int i = 0; i < tobj_count; i++) {
        if (tobj[i].kind == OBJ_CHEST) tgt_add(T_CHEST, i, tobj[i].x, tobj[i].y, "chest");
        if (tobj[i].kind == OBJ_LEGEND) tgt_add(T_LEGEND, i, tobj[i].x, tobj[i].y, SPECIES[tobj[i].arg].name);
        if (tobj[i].kind == OBJ_FERRY) {
            tgt_add(T_FERRY, i, tobj[i].x, tobj[i].y, "ferry");
            ferry_at[tobj[i].y * W + tobj[i].x] = 1;
        }
    }
    for (int i = 0; i < WARP_COUNT && i < 256; i++)
        if (WARPS[i].map == m) tgt_warp[i] = (s16)tgt_add(T_WARP, i, -1, -1, MAPS[WARPS[i].dest].name);
    for (int l = 0; l < 4; l++)
        if (MAPS[m].link[l] != MAP_NONE) tgt_edge[l] = tgt_add(T_EDGE, l, -1, -1, MAPS[MAPS[m].link[l]].name);
    int into = 0;
    for (int i = 0; i < WARP_COUNT; i++) into |= WARPS[i].dest == m;
    int mat = 0;
    for (int c = 0; c < NC; c++) mat |= (sattr[c] & A_EXIT) != 0;
    if (into && mat) tgt_mat = tgt_add(T_MAT, 0, -1, -1, "outside");

    /* entrances */
    nentr = 0;
    for (int i = 0; i < WARP_COUNT; i++)
        if (WARPS[i].dest == m) entr_add(WARPS[i].dx, WARPS[i].dy, -1);
    for (int l = 0; l < 4; l++) {
        if (MAPS[m].link[l] == MAP_NONE) continue;
        for (int k = 0; k < (l < 2 ? W : H); k++) {
            int x = l < 2 ? k : (l == LINK_W ? 0 : W - 1);
            int y = l < 2 ? (l == LINK_N ? 0 : H - 1) : k;
            int a = sattr[y * W + x];
            static const s8 INWARD[4] = { DIR_DOWN, DIR_UP, DIR_RIGHT, DIR_LEFT };
            if (!(a & (A_SOLID | A_WATER | A_LEDGE)) && swalk[y * W + x]) entr_add(x, y, INWARD[l]);
            else if ((abil & ABL_SURF) && (a & A_WATER) && !(a & A_DEEP) && travel_surf_cell(x, y))
                entr_add(x, y, INWARD[l]);
        }
    }
    for (int i = 0; i < tobj_count; i++)
        if (tobj[i].kind == OBJ_FERRY) entr_add(tobj[i].x, tobj[i].y + 1, DIR_DOWN);
    if (abil & ABL_FLY)
        for (int i = 0; i < FLY_POINT_COUNT; i++)
            if (FLY_POINTS[i].map == m) entr_add(FLY_POINTS[i].x, FLY_POINTS[i].y, DIR_DOWN);
}

/* Replay every fast-path step of the starting state through the game. */
static int validate_fast_path(void)
{
    u32 m0 = macro_intern(key_init);
    int bad = 0;
    dyn_set(m0);
    for (int c = 0; c < NC; c++) {
        if (dyn[c] || (!swalk[c] && !ssurf[c])) continue;
        for (int d = 0; d < 4; d++) {
            int r = fast_move(c, d);
            if (r == FM_SIM) continue;
            u32 om = NIL;
            int oc = -1, code = 0;
            int res = sim(m0, c, d, SA_MOVE, &om, &oc, &code);
            int ok = r == FM_BLOCK ? res == R_BLOCK : (res == R_MOVE && om == m0 && oc == r);
            if (!ok && bad++ < 4)
                printf("  %s: fast path says %d for %d,%d dir %d, the game says %d (%d,%d)\n", MAPS[cur_map].name, r,
                       c % W, c / W, d, res, oc % W, oc / W);
            int nx = c % W + DIR_DX[d], ny = c / W + DIR_DY[d], nc = ny * W + nx;
            if ((abil & ABL_SURF) && !(sattr[c] & A_WATER) && nx >= 0 && ny >= 0 && nx < W && ny < H && ssurf[nc] &&
                !dyn[nc] && !(sattr[nc] & A_CURRENT)) {
                res = sim(m0, c, d, SA_SURF, &om, &oc, &code);
                if (!(res == R_MOVE && om == m0 && oc == nc) && bad++ < 4)
                    printf("  %s: SURF fast path from %d,%d dir %d disagrees with the game\n", MAPS[cur_map].name, c % W, c / W, d);
            }
        }
    }
    return bad;
}

static void describe_state(u32 m, int c)
{
    const u8 *k = macro_key(m);
    printf("player %d,%d", c % NC % W, c % NC / W);
    if (elevated) printf(" level %d", c / NC);
    for (int i = 0; i < nb; i++) printf(" boulder %d,%d", k[2 * i], k[2 * i + 1]);
    int sw = k[2 * nb] | (k[2 * nb + 1] << 8);
    if (sw) printf(" switches %04x", sw);
    for (int j = 0; j < np; j++)
        if ((k[2 * nb + 2 + j / 8] >> (j & 7)) & 1)
            printf(" %s@%d,%d done", tobj[pobj[j]].kind == OBJ_GATE ? "gate" : "legend", tobj[pobj[j]].x,
                   tobj[pobj[j]].y);
    if (nsat && ((k[2 * nb + 2 + SAT_BIT / 8] >> (SAT_BIT & 7)) & 1)) printf(" satchels taken");
}

static void print_path(u32 id)
{
    static u32 chain[4096];
    int n = 0;
    for (u32 v = id; v != NIL && n < 4096; v = entries[nodes[v].entry].parent) chain[n++] = v;
    static const char *const ACT[] = { "move", "surf", "answer/take", "re-enter", "step", "start" };
    static const char *const DN[] = { "down", "up", "left", "right" };
    for (int i = n - 1; i >= 0; i--) {
        const Entry *e = &entries[nodes[chain[i]].entry];
        if (e->parent == NIL) printf("      start ");
        else printf("      from %d,%d %s %s -> ", e->src % NC % W, e->src % NC / W, ACT[e->act], DN[e->dir]);
        describe_state(e->macro, e->cell);
        printf("\n");
    }
}

/* Events (pushes etc.), pushes and moves along the solution found. */
static void solution_len(int t, int *events, int *pushes, int *moves)
{
    u32 v = tgt[t].node;
    *events = (int)tgt[t].depth;
    *pushes = 0;
    *moves = comp_dist(nodes[v].macro, nodes[v].cell, tgt[t].from);
    for (;;) {
        const Entry *e = &entries[nodes[v].entry];
        if (e->parent == NIL) break;
        u32 p = e->parent;
        *moves += 1 + comp_dist(nodes[p].macro, nodes[p].cell, e->src);
        if (memcmp(macro_key(nodes[p].macro), macro_key(e->macro), (size_t)(2 * nb))) ++*pushes;
        v = p;
    }
}

typedef struct { int maps, unreachable, softlocks, drift, loops, overflow; } Tally;
static u32 last_bad;
static int last_missing;

static void solve(int m, int ability, int need_targets, Tally *tal, int report)
{
    if (getenv("PZ_TRACE")) fprintf(stderr, "solve %d %s abil %d\n", m, MAPS[m].name, ability);
    setup_map(m, ability);
    if (report) tal->drift += validate_fast_path();
    if (!nentr) return;   /* no way in with these abilities */
    loops_found = 0;
    u32 m0 = macro_intern(key_init);
    for (int i = 0; i < nentr; i++) add_entry(m0, entr[i], NIL, entr[i], SA_START, 0, 0, 0);
    if (nsat) {   /* coming back after the satchels were picked up */
        u8 k[KEY_MAX];
        memcpy(k, key_init, KEY_MAX);
        k[2 * nb + 2 + SAT_BIT / 8] |= (u8)(1u << (SAT_BIT & 7));
        u32 m1 = macro_intern(k);
        for (int i = 0; i < nentr; i++) add_entry(m1, entr[i], NIL, entr[i], SA_START, 0, 0, 0);
    }
    search();
    tal->maps++;
    if (getenv("PZ_DEBUG"))
        for (u32 i = 0; i < ncount; i++) {
            int c = nodes[i].canon % NC;
            if (c / W == atoi(getenv("PZ_DEBUG"))) printf("  node %u: %d,%d level %d\n", i, c % W, c / W, nodes[i].canon / NC);
        }
    tal->loops += loops_found;
    if (overflow) {
        tal->overflow++;
        printf("  %s: more than %u search entries, gave up\n", MAPS[m].name, ENTRY_CAP);
        return;
    }
    /* targets */
    int missing = 0;
    if (need_targets)
        for (int t = 0; t < ntgt; t++)
            if (tgt[t].node == NIL) {
                missing++;
                if (tgt[t].x >= 0)
                    printf("  %s: %s %s at %d,%d cannot be reached\n", MAPS[m].name, T_KIND[tgt[t].kind], tgt[t].name,
                           tgt[t].x, tgt[t].y);
                else
                    printf("  %s: %s to %s (%s) cannot be reached\n", MAPS[m].name, T_KIND[tgt[t].kind], tgt[t].name,
                           tgt[t].kind == T_EDGE ? EDGE_NAME[tgt[t].idx] : "-");
            }
    tal->unreachable += missing;
    /* soft-locks: reachable states from which no exit can be reached */
    int exits = 0;
    for (int t = 0; t < ntgt; t++) exits += tgt[t].kind >= T_FERRY && tgt[t].node != NIL;
    u32 bad = 0, worst = NIL;
    if (exits) {
        u32 *cnt = calloc((size_t)ncount + 1, sizeof(u32)), *par = malloc((size_t)ecount * sizeof(u32) + 4);
        u32 *fill = malloc((size_t)ncount * sizeof(u32) + 4), *q = malloc((size_t)ncount * sizeof(u32) + 4);
        u8 *good = calloc((size_t)ncount + 1, 1);
        for (u32 i = 0; i < ecount; i++)
            if (entries[i].parent != NIL && entries[i].node != NIL) cnt[entries[i].node + 1]++;
        for (u32 i = 0; i < ncount; i++) cnt[i + 1] += cnt[i];
        for (u32 i = 0; i < ncount; i++) fill[i] = cnt[i];
        for (u32 i = 0; i < ecount; i++)
            if (entries[i].parent != NIL && entries[i].node != NIL) par[fill[entries[i].node]++] = entries[i].parent;
        u32 qh = 0, qt = 0;
        for (u32 i = 0; i < ncount; i++)
            if (nodes[i].exit) {
                good[i] = 1;
                q[qt++] = i;
            }
        while (qh < qt) {
            u32 v = q[qh++];
            for (u32 k = cnt[v]; k < cnt[v + 1]; k++)
                if (!good[par[k]]) {
                    good[par[k]] = 1;
                    q[qt++] = par[k];
                }
        }
        for (u32 i = 0; i < ncount; i++)
            if (!good[i]) {
                bad++;
                if (worst == NIL || nodes[i].depth < nodes[worst].depth) worst = i;
            }
        free(cnt);
        free(par);
        free(fill);
        free(q);
        free(good);
    }
    tal->softlocks += bad ? 1 : 0;
    last_bad = bad;
    last_missing = missing;
    if (bad) {
        printf("  %s (%s): %u soft-locked states, e.g. ", MAPS[m].name, ability ? "all abilities" : "no abilities", bad);
        describe_state(nodes[worst].macro, nodes[worst].cell);
        printf(", reached by:\n");
        print_path(worst);
    }
    if (!report || !interesting) return;
    /* the summary line: the hardest target */
    int best = -1, be = 0, bp = 0, bm = 0;
    for (int t = 0; t < ntgt; t++) {
        if (tgt[t].node == NIL) continue;
        int e, p, mv;
        solution_len(t, &e, &p, &mv);
        if (best < 0 || e > be || (e == be && mv > bm)) {
            best = t;
            be = e;
            bp = p;
            bm = mv;
        }
    }
    int reached = 0;
    for (int t = 0; t < ntgt; t++) reached += tgt[t].node != NIL;
    printf("  %-18s %-4s %7u nodes %7u states  targets %3d/%-3d", MAPS[m].name, ability == ABL_ALL ? "all" : "none",
           ncount, mcount, reached, ntgt);
    if (best >= 0)
        printf("  hardest: %s %s: %d events, %d pushes, %d moves", T_KIND[tgt[best].kind], tgt[best].name, be, bp, bm);
    for (int t = 0; t < ntgt; t++)   /* a Hall Master: the one the designer cares about */
        if (tgt[t].kind == T_NPC && tgt[t].node != NIL && !strncmp(tgt[t].name, "MASTER", 6) && t != best) {
            int e, p, mv;
            solution_len(t, &e, &p, &mv);
            printf("\n  %-18s      %s: %d events, %d pushes, %d moves", "", tgt[t].name, e, p, mv);
        }
    if (getenv("PZ_PATH"))   /* the event path to the Master (or the hardest target) */
        for (int t = 0; t < ntgt; t++)
            if (t == best || (tgt[t].kind == T_NPC && tgt[t].node != NIL && !strncmp(tgt[t].name, "MASTER", 6))) {
                printf("\n    path to %s:\n", tgt[t].name);
                print_path(tgt[t].node);
            }
    printf("%s\n", bad ? "  SOFT-LOCK" : "");
}

/* Does SURF, STRENGTH or FLY change anything on this map? */
static int abilities_matter(int m)
{
    for (int i = 0; i < MAPS[m].obj_count; i++)
        if (MAPS[m].objs[i].kind == OBJ_BOULDER && MAPS[m].objs[i].arg == 0) return 1;
    for (int i = 0; i < FLY_POINT_COUNT; i++)
        if (FLY_POINTS[i].map == m) return 1;
    map_load(m);
    for (int y = 0; y < map_h; y++)
        for (int x = 0; x < map_w; x++)
            if ((cell_attr(x, y) & A_WATER) && !(cell_attr(x, y) & A_DEEP)) return 1;
    return 0;
}

#ifndef PZ_NO_MAIN
int main(void)
{
    setvbuf(stdout, NULL, _IOLBF, 0);
    if (getenv("PZ_CAP")) ENTRY_CAP = (u32)atol(getenv("PZ_CAP"));
    fresh_game();
    opt.follower = 0;
    follower.shown = 0;
    flag_set(FLAG_STARTER);
    Tally tal = { 0 };
    printf("puzzle solver (Halls without SURF/STRENGTH, other maps with SURF+STRENGTH+FLY):\n");
    for (int m = 0; m < MAP_COUNT; m++) {
        if (MAPS[m].flags & MF_DEBUG) continue;
        if (!strncmp(MAPS[m].name, "TEST ", 5)) continue;   /* traversal fixtures (test_travel.c), not the game */
        const char *only = getenv("PZ_MAP");   /* a map id or name */
        if (only && (only[0] >= '0' && only[0] <= '9' ? atoi(only) != m : strcmp(only, MAPS[m].name) != 0)) continue;
        int designed = is_hall(m) ? 0 : ABL_ALL;
        solve(m, designed, 1, &tal, 1);
        /* soft-locks with the other ability set too */
        if (abilities_matter(m)) solve(m, designed ? 0 : ABL_ALL, 0, &tal, 0);
    }
    printf("searched %d map/ability combinations\n", tal.maps);
    CHECK(!tal.drift, "the solver's fast path agrees with the game on every plain step");
    CHECK(!tal.overflow, "every map's state space was searched completely");
    CHECK(!tal.loops, "no endless forced moves (ice / current loops)");
    CHECK(!tal.unreachable, "every person, satchel, chest, legend, door, edge and exit mat is reachable");
    CHECK(!tal.softlocks, "no soft-locks: from every reachable state an exit stays reachable");
    if (failures) {
        printf("%d puzzle check(s) FAILED\n", failures);
        return 1;
    }
    printf("puzzle checks passed\n");
    return 0;
}
#endif
