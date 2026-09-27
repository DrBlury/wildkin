/*
 * Elevation (docs/ELEVATION.md): heights, cliffs, stairs, ledges, bridges
 * you walk over one way and under the other, tunnels and hidden passages.
 * Included by field.c after the map decoding helpers.
 *
 * A map may give an elevation layer (MapDef.elev): one character per cell,
 *   '0'..'3'          the height of the ground there
 *   '^' 'v' '<' '>'   stairs climbing north / south / west / east: they join
 *                     the cell on their low side (its height) to the cell on
 *                     their high side (one higher); stairs may be chained
 *   '_'               a ledge: a cliff face you may hop down (south) but not
 *                     climb; its height is the one of the cell below it
 * and features over it (MapDef.feats, rectangles):
 *   EF_BRIDGE_H / EF_BRIDGE_V  a deck one level above the ground below,
 *                     walked east-west / north-south on top, and freely
 *                     underneath at the ground's height
 *   EF_TUNNEL         the cells are covered by a plateau one level up (its
 *                     top is walkable, drawn over anyone below); the cliff
 *                     face just south of the tunnel becomes its mouth
 *   EF_HIDDEN         a secret passage: whatever the cells show (trees, a
 *                     cliff), they are walkable and drawn over the walker;
 *                     once the player has walked in, it is "found" for good
 *                     (a bit in the save, travel.secrets) and shows it: a
 *                     worn gap at the foot of the trees, an open cave mouth
 *                     in a cliff
 *
 * Cliff faces are derived: a cell lower than the top surface right above it
 * is a face (solid), one row per level of drop, so authors only paint
 * heights. Faces, plateau rims, cast shadows, stairs, decks and mouths are
 * autotiled here from the tileset's ElevArt (tools/elevation.py).
 *
 * Actors (player, people, their kin, the follower, wild kin) carry a level.
 * Steps keep the level (or change it on stairs, ledges and deck ends);
 * elev_enter() says whether a step is allowed and onto what, and
 * elev_obj_prio() lifts a sprite over the top layer when it stands on a
 * deck (or in front of one) and keeps it under when it walks beneath.
 */

/* per-cell decoded info (u16) */
enum { EK_GROUND, EK_FACE, EK_LEDGE, EK_STAIRS };   /* EK_STAIRS + DIR_* (climbing direction) */
enum { EC_NONE, EC_BRIDGE_H, EC_BRIDGE_V, EC_TUNNEL, EC_MOUTH, EC_HIDDEN };
#define EV_LO(e)     ((e) & 3)           /* ground height */
#define EV_HI(e)     (((e) >> 2) & 3)    /* deck / tunnel-top height */
#define EV_VIS(e)    (((e) >> 4) & 3)    /* height of the surface drawn there */
#define EV_KIND(e)   (((e) >> 6) & 7)    /* EK_* */
#define EV_COVER(e)  (((e) >> 9) & 7)    /* EC_* */
#define EV_FOUND     0x1000              /* a hidden cell the player walked through */
#define EV_MAKE(lo, hi, vis, kind, cov) \
    ((u16)((lo) | ((hi) << 2) | ((vis) << 4) | ((kind) << 6) | ((cov) << 9)))
#define EK_IS_STAIRS(k) ((k) >= EK_STAIRS)
#define EK_UP(k)        ((k) - EK_STAIRS)   /* DIR_* the stairs climb toward */

/* elev_enter() results */
enum { ELEV_BLOCK, ELEV_FLOOR, ELEV_TOP };

EWRAM_BSS static u16 map_elev[MAP_MAX_W * MAP_MAX_H];
static u8 map_elevated;   /* the current map has an elevation layer */

static int cell_attr_raw(int x, int y);
static int travel_secret_get(int b);    /* travel.c: found hidden passages (saved) */
static void travel_secret_set(int b);
#define SECRET_MAX 64                   /* bits in TravelState.secrets */

static u16 elev_at(int x, int y)
{
    if (!map_elevated || x < 0 || y < 0 || x >= map_w || y >= map_h) return 0;
    return map_elev[y * map_w + x];
}

/* A cover you can stand on (deck, tunnel top). */
static int ec_walkable(int c) { return c == EC_BRIDGE_H || c == EC_BRIDGE_V || c == EC_TUNNEL; }
/* Anything drawn over a walker below. */
static int ec_covers(int c) { return c != EC_NONE; }

/* ---------------- decoding ---------------- */

static char elev_char(const MapDef *m, int x, int y)
{
    if (x < 0 || y < 0 || x >= m->w || y >= m->h) return '0';
    char c = map_patch_elev(m, x, y, m->elev[y][x]);
    return c ? c : '0';
}

static int elev_stairs_dir(char c)
{
    switch (c) {
    case '^': return DIR_UP;
    case 'v': return DIR_DOWN;
    case '<': return DIR_LEFT;
    case '>': return DIR_RIGHT;
    default: return -1;
    }
}

/* Ground height of an elevation character (stairs / ledges look at their
 * low-side neighbour; chains of the same stairs add one per step). */
static int elev_floor_of(const MapDef *m, int x, int y, int depth)
{
    char c = elev_char(m, x, y);
    if (c >= '0' && c <= '3') return c - '0';
    if (depth > 8) return 0;
    if (c == '_') return elev_floor_of(m, x, y + 1, depth + 1);
    int d = elev_stairs_dir(c);
    if (d < 0) return 0;
    int lx = x - DIR_DX[d], ly = y - DIR_DY[d];   /* the low side */
    if (elev_char(m, lx, ly) == c) return elev_floor_of(m, lx, ly, depth + 1) + 1;
    return elev_floor_of(m, lx, ly, depth + 1);
}

/* Hidden passages are numbered across the world (map order, then feature
 * order): the bit of a map's first one. */
static int elev_secret_base(int map)
{
    int n = 0;
    for (int i = 0; i < map && i < MAP_COUNT; i++)
        for (int k = 0; k < MAPS[i].feat_count; k++) n += MAPS[i].feats[k].kind == EF_HIDDEN;
    return n;
}

/* Every hidden passage in the world (must stay <= SECRET_MAX: tested). */
MAYBE_UNUSED static int elev_secret_total(void) { return elev_secret_base(MAP_COUNT); }

/* Mark a hidden feature's cells found (or not). */
static void elev_mark_found(const ElevFeat *f, int found)
{
    for (int y = f->y; y < f->y + f->h && y < map_h; y++)
        for (int x = f->x; x < f->x + f->w && x < map_w; x++) {
            u16 *e = &map_elev[y * map_w + x];
            *e = (u16)(found ? *e | EV_FOUND : *e & ~EV_FOUND);
        }
}

static void elev_decode(const MapDef *m)
{
    map_elevated = m->elev != 0 && TILESETS[m->tileset].elev != 0;
    if (!map_elevated) return;
    for (int y = 0; y < m->h; y++)
        for (int x = 0; x < m->w; x++) {
            char c = elev_char(m, x, y);
            int lo = elev_floor_of(m, x, y, 0) & 3, kind = EK_GROUND;
            int d = elev_stairs_dir(c);
            if (d >= 0) kind = EK_STAIRS + d;
            if (c == '_') kind = EK_LEDGE;
            map_elev[y * m->w + x] = EV_MAKE(lo, lo, lo, kind, EC_NONE);
        }
    for (int i = 0; i < m->feat_count; i++) {
        const ElevFeat *f = &m->feats[i];
        static const u8 COVER[] = { EC_NONE, EC_BRIDGE_H, EC_BRIDGE_V, EC_TUNNEL, EC_HIDDEN };
        int cov = f->kind < sizeof(COVER) ? COVER[f->kind] : EC_NONE;
        for (int y = f->y; y < f->y + f->h && y < m->h; y++)
            for (int x = f->x; x < f->x + f->w && x < m->w; x++) {
                u16 *e = &map_elev[y * m->w + x];
                int lo = EV_LO(*e), hi = cov == EC_HIDDEN ? lo : (lo < 3 ? lo + 1 : 3);
                *e = EV_MAKE(lo, hi, lo, EV_KIND(*e), cov);
            }
    }
    /* faces: a cell lower than the surface drawn just above it; tunnel
     * mouths: a face right under a tunnel */
    for (int x = 0; x < m->w; x++) {
        int above = -1, above_cov = EC_NONE, above_hi = 0;
        for (int y = 0; y < m->h; y++) {
            u16 *e = &map_elev[y * m->w + x];
            int lo = EV_LO(*e), hi = EV_HI(*e), kind = EV_KIND(*e), cov = EV_COVER(*e);
            int eff = cov == EC_TUNNEL ? hi : lo, vis;
            if (EK_IS_STAIRS(kind)) {
                vis = above - 1 > lo ? above - 1 : lo;
            } else if (above > eff) {
                if (kind != EK_LEDGE) kind = EK_FACE;
                vis = above - 1;
                if (cov == EC_NONE && above_cov == EC_TUNNEL) {
                    cov = EC_MOUTH;
                    hi = above_hi;
                }
            } else {
                if (kind == EK_LEDGE) kind = EK_GROUND;   /* not a drop after all */
                vis = eff;
            }
            *e = EV_MAKE(lo, hi, vis & 3, kind, cov);
            above = vis;
            above_cov = cov;
            above_hi = hi;
        }
    }
    /* hidden passages found on an earlier visit (the save remembers them) */
    int b = elev_secret_base((int)(m - MAPS));
    for (int i = 0; i < m->feat_count; i++)
        if (m->feats[i].kind == EF_HIDDEN) elev_mark_found(&m->feats[i], travel_secret_get(b++));
}

/* The player walked into hidden cell (x, y): the passage it belongs to is
 * found for good. Returns its feature (to redraw), or 0 when it already
 * was found or there is none. */
static const ElevFeat *elev_secret_find(int x, int y)
{
    if (!map_elevated) return 0;
    u16 e = elev_at(x, y);
    if (EV_COVER(e) != EC_HIDDEN || (e & EV_FOUND)) return 0;
    const MapDef *m = &MAPS[cur_map];
    int b = elev_secret_base(cur_map);
    for (int i = 0; i < m->feat_count; i++) {
        const ElevFeat *f = &m->feats[i];
        if (f->kind != EF_HIDDEN) continue;
        if (x >= f->x && y >= f->y && x < f->x + f->w && y < f->y + f->h) {
            travel_secret_set(b);
            elev_mark_found(f, 1);
            return f;
        }
        b++;
    }
    return 0;
}

/* A found hidden cell. */
static int elev_found(int x, int y)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h) return 0;
    u16 e = elev_at(x, y);
    return EV_COVER(e) == EC_HIDDEN && (e & EV_FOUND);
}

/* ---------------- rules ---------------- */

/* Terrain attributes adjusted for elevation: faces are walls, ledges hop,
 * stairs, mouths and hidden passages are open. */
static int elev_attr(int x, int y, int a)
{
    u16 e = elev_at(x, y);
    if (!e) return a;
    int kind = EV_KIND(e), cov = EV_COVER(e);
    if (kind == EK_FACE) a |= A_SOLID;
    if (kind == EK_LEDGE) a = (a & ~A_SOLID) | A_LEDGE;
    if (EK_IS_STAIRS(kind)) a &= ~A_SOLID;
    if (cov == EC_MOUTH || cov == EC_HIDDEN) a &= ~A_SOLID;
    return a;
}

static int elev_floor(int x, int y) { return EV_LO(elev_at(x, y)); }
static int elev_hidden(int x, int y) { return EV_COVER(elev_at(x, y)) == EC_HIDDEN; }

/* Can an actor at (x0, y0) on `level` step in `dir`? ELEV_FLOOR: onto the
 * ground (terrain rules apply), ELEV_TOP: onto a deck / tunnel top (the
 * terrain below does not matter), ELEV_BLOCK. *level_out gets the level. */
static int elev_enter(int x0, int y0, int level, int dir, int *level_out)
{
    *level_out = level;
    if (!map_elevated) return ELEV_FLOOR;
    u16 e0 = elev_at(x0, y0);
    int k0 = EV_KIND(e0), c0 = EV_COVER(e0), lv = level;
    if (ec_walkable(c0) && level == EV_HI(e0) && level != EV_LO(e0)) {
        /* on a deck: only along it */
        if (c0 == EC_BRIDGE_H && DIR_DY[dir]) return ELEV_BLOCK;
        if (c0 == EC_BRIDGE_V && DIR_DX[dir]) return ELEV_BLOCK;
    } else if (EK_IS_STAIRS(k0)) {
        int up = EK_UP(k0);
        if (dir == up) lv = EV_LO(e0) + 1;
        else if (dir == DIR_BACK[up]) lv = EV_LO(e0);
        else return ELEV_BLOCK;
    }
    int nx = x0 + DIR_DX[dir], ny = y0 + DIR_DY[dir];
    *level_out = lv;
    if (nx < 0 || ny < 0 || nx >= map_w || ny >= map_h) return ELEV_FLOOR;
    u16 e1 = elev_at(nx, ny);
    int k1 = EV_KIND(e1), c1 = EV_COVER(e1), lo1 = EV_LO(e1);
    if (ec_walkable(c1) && EV_HI(e1) == lv && lv != lo1) {
        int side = (c1 == EC_BRIDGE_H && DIR_DY[dir]) || (c1 == EC_BRIDGE_V && DIR_DX[dir]);
        if (!side) {
            *level_out = lv;
            return ELEV_TOP;
        }
    }
    if (EK_IS_STAIRS(k1)) {
        int up = EK_UP(k1);
        if (dir == up && lv == lo1) return ELEV_FLOOR;
        if (dir == DIR_BACK[up] && lv == lo1 + 1) return ELEV_FLOOR;
        return ELEV_BLOCK;
    }
    if (k1 == EK_LEDGE) return ELEV_BLOCK;   /* hopped over (field.c) */
    if (k1 == EK_FACE && c1 != EC_MOUTH && c1 != EC_HIDDEN) return ELEV_BLOCK;
    if (lo1 != lv) return ELEV_BLOCK;
    return ELEV_FLOOR;
}

/* The level to stand on at (x, y): `hint` when it is one of the cell's
 * levels, else the ground when it is walkable, else the deck; facing along
 * a bridge prefers its deck when there is no hint (arrivals). */
static int elev_level_at(int x, int y, int hint, int facing)
{
    u16 e = elev_at(x, y);
    if (!e) return 0;
    int lo = EV_LO(e), kind = EV_KIND(e), cov = EV_COVER(e);
    int hi = ec_walkable(cov) ? EV_HI(e) : EK_IS_STAIRS(kind) ? lo + 1 : lo;
    if (hint == lo || hint == hi) return hint;
    if (hint < 0 && facing >= 0 && hi != lo &&
        ((cov == EC_BRIDGE_H && DIR_DX[facing]) || (cov == EC_BRIDGE_V && DIR_DY[facing])))
        return hi;
    if (hi != lo && (cell_attr_raw(x, y) & A_SOLID)) return hi;
    return lo;
}

/* OBJ priority for an actor: 1 (over the top layer) on a deck or tunnel
 * top, in front of (just south of) one and beside one on its level; 2
 * (under it: the top layer clips it) otherwise.
 *
 * Decided from the cells the actor's 16x16 ground square stands on (one
 * cell at rest; mid-step the cell it left and the one it is entering) and
 * its level, never from the sprite's centre: an actor stepping between the
 * cell in front of a deck and the cell under it stays at 2 for the whole
 * step, so the deck's edge clips it smoothly as it walks in or out. (It
 * used to be lifted over the deck up to the half-way pixel and then vanish
 * at once, the follower doing the same one step behind.) `wide`: a 32-wide
 * sprite centred on the cell (kin, the bike); people are 16 wide. Both are
 * 32 tall, the head one cell up. */
static int elev_obj_prio_w(const Actor *a, int wide)
{
    if (!map_elevated) return 2;
    wide = wide != 0;
    int px = a->x * 16 + a->ox, py = a->y * 16 + a->oy;
    int gx0 = px >> 4, gx1 = (px + 15) >> 4, gy0 = py >> 4, gy1 = (py + 15) >> 4;
    /* under something: a deck or tunnel top above the actor's level, a
     * tunnel mouth or a hidden passage (drawn over whoever is in it) */
    for (int y = gy0; y <= gy1; y++)
        for (int x = gx0; x <= gx1; x++) {
            u16 e = elev_at(x, y);
            int cov = EV_COVER(e);
            if (ec_covers(cov) && (!ec_walkable(cov) || a->level < EV_HI(e))) return 2;
        }
    /* the sprite's cells (whole cells: a 32-wide sprite reaches half a cell
     * past its ground square on both sides, the head a cell up; taken at
     * the cells stood on, so nothing changes mid-step) overlap a cover it
     * is not under: in front of it (the row above, where the cover ends
     * there), or on it / beside it at its level */
    for (int y = gy0 - 1; y <= gy1; y++)
        for (int x = gx0 - wide; x <= gx1 + wide; x++) {
            u16 e = elev_at(x, y);
            int cov = EV_COVER(e);
            if (!ec_covers(cov)) continue;
            if (y < gy0) {
                if (!ec_covers(EV_COVER(elev_at(x, gy0)))) return 1;
            } else if (ec_walkable(cov) && a->level >= EV_HI(e) && a->level != EV_LO(e)) {
                return 1;
            }
        }
    return 2;
}

static int elev_obj_prio(const Actor *a) { return elev_obj_prio_w(a, 0); }

/* ---------------- drawing ---------------- */

static int elev_facey(int x, int y)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h) return 1;
    int k = EV_KIND(elev_at(x, y));
    return k == EK_FACE || k == EK_LEDGE || EK_IS_STAIRS(k);
}

/* Is the neighbour lower than a top surface at height v (a rim there)? */
static int elev_lower(int x, int y, int v)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h) return 0;
    u16 e = elev_at(x, y);
    if (EK_IS_STAIRS(EV_KIND(e))) return 0;
    if (ec_walkable(EV_COVER(e)) && EV_HI(e) >= v) return 0;
    return EV_VIS(e) < v;
}

static int elev_is_bridge(int x, int y, int cov)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h) return 0;
    return EV_COVER(elev_at(x, y)) == cov;
}

/* Cliffs, rims, shadows and stairs (BG2), before decor. */
static void elev_render_base(int mx, int my, u16 mid[4])
{
    if (!map_elevated || mx < 0 || my < 0 || mx >= map_w || my >= map_h) return;
    u16 e = elev_at(mx, my);
    const ElevArt *ea = tset()->elev;
    int kind = EV_KIND(e), cov = EV_COVER(e);
    if (EK_IS_STAIRS(kind)) {
        for (int c = 0; c < 4; c++) mid[c] = ea->stairs[EK_UP(kind)][c];
        return;
    }
    if (kind == EK_FACE || kind == EK_LEDGE) {
        if (cov == EC_MOUTH) {
            for (int c = 0; c < 4; c++) mid[c] = ea->mouth[c];
            return;
        }
        for (int c = 0; c < 4; c++) {
            int sx = (c & 1) ? 1 : -1, sy = (c >> 1) ? 1 : -1;
            if (kind == EK_LEDGE) {
                mid[c] = ea->ledge[c][elev_facey(mx + sx, my)];
                continue;
            }
            int v = (elev_facey(mx, my + sy) ? 1 : 0) | (elev_facey(mx + sx, my) ? 2 : 0);
            mid[c] = ea->face[c][v];
        }
        return;
    }
    int vis = EV_VIS(e);
    for (int c = 0; c < 4; c++) {
        if (mid[c]) continue;   /* trees and the like keep their own look */
        int sx = (c & 1) ? 1 : -1, sy = (c >> 1) ? 1 : -1;
        int vs = !elev_lower(mx, my + sy, vis), hs = !elev_lower(mx + sx, my, vis);
        int ds = !elev_lower(mx + sx, my + sy, vis);
        int v = vs && hs ? (ds ? 0 : 1) : vs ? 2 : hs ? 3 : 4;
        mid[c] = ea->rim[c][v];
        if (!mid[c] && !(c & 1) && mx > 0) {
            /* a rise just west casts a shadow over this low ground */
            u16 w = elev_at(mx - 1, my);
            if (EV_VIS(w) > vis && !EK_IS_STAIRS(EV_KIND(w))) mid[c] = ea->shadow[c];
        }
    }
}

/* Path-like for a found passage's worn gap: a path or another found cell. */
static int elev_pathy(int x, int y)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h) return 0;
    return map_cells[y * map_w + x] == CELL_PATH || elev_found(x, y);
}

/* Decks, tunnel tops and hidden passages (BG3), after decor. */
static void elev_render_cover(int mx, int my, u16 bottom[4], u16 mid[4], u16 top[4])
{
    u16 e = elev_at(mx, my);
    int cov = EV_COVER(e);
    if (!cov) return;
    const TilesetDef *t = tset();
    const ElevArt *ea = t->elev;
    if (cov == EC_BRIDGE_H || cov == EC_BRIDGE_V) {
        int h = cov == EC_BRIDGE_H;
        for (int c = 0; c < 4; c++) {
            int sx = (c & 1) ? 1 : -1, sy = (c >> 1) ? 1 : -1;
            int rail = h ? !elev_is_bridge(mx, my + sy, cov) : !elev_is_bridge(mx + sx, my, cov);
            int end = h ? !elev_is_bridge(mx + sx, my, cov) : !elev_is_bridge(mx, my + sy, cov);
            top[c] = (h ? ea->deck_h : ea->deck_v)[c][rail | (end << 1)];
        }
    } else if (cov == EC_TUNNEL) {
        u16 g = legend_pick(legend_for(t, t->legend_default), mx, my);
        if (g >= CELL_PATH || (t->mflags[g] & MTF_OVERLAY)) g = t->ground;
        for (int c = 0; c < 4; c++) top[c] = t->meta_bottom[g][c];
    } else if (cov == EC_HIDDEN) {
        int found = (e & EV_FOUND) != 0;
        if (found && EV_KIND(e) == EK_FACE) {
            /* a crack in a cliff, found: an open cave mouth now */
            for (int c = 0; c < 4; c++) {
                mid[c] = ea->mouth[c];
                top[c] = 0;
            }
            return;
        }
        int has_top = top[0] | top[1] | top[2] | top[3];
        int has_mid = mid[0] | mid[1] | mid[2] | mid[3];
        for (int c = 0; c < 4; c++) {
            if (has_mid) {
                if (!top[c]) top[c] = mid[c];
                mid[c] = 0;
            } else if (!has_top) {
                top[c] = bottom[c];
            }
        }
        if (found) {
            /* found: a worn gap at the foot of the trees (or rocks), a
             * trodden path joining any path beside it; a passage running
             * north-south opens all the way down */
            int open_up = elev_found(mx, my - 1);
            for (int c = 0; c < 4; c++) {
                if (c < 2 && !open_up) continue;
                int sx = (c & 1) ? 1 : -1, sy = (c >> 1) ? 1 : -1;
                int vs = elev_pathy(mx, my + sy), hs = elev_pathy(mx + sx, my);
                int v = vs && hs ? (elev_pathy(mx + sx, my + sy) ? 0 : 1) : vs ? 2 : hs ? 3 : 4;
                if (t->path_q) bottom[c] = t->path_q[c][v];
                mid[c] = top[c] = 0;
            }
        }
    }
}
