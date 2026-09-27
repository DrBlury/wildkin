/*
 * Sprites under and over bridges, frame by frame (docs/ELEVATION.md 4,
 * docs/handoff/elevation.md "Flicker under the bridge").
 *
 * For every bridge and tunnel of every map with a height layer:
 *   - the player walks under it and back with the follower (and again on
 *     the bike), in the storm's rain;
 *   - the player walks over it (deck ends included) and back;
 *   - with the player standing on the deck, a person, a person's kin and a
 *     wild kin walk under it, a mostly transparent priority-1 sprite (a rain
 *     streak) laid over each of them every frame.
 * After every frame the test composes what the GBA shows from OAM, the OBJ
 * tiles, the BG3 map and its scroll, with the OBJ line buffer rules of the
 * hardware (as mGBA does them: a later sprite of a higher priority lowers
 * the priority of the pixels already in the buffer, even through its
 * transparent pixels), and checks:
 *   - no pixel of an actor (or its shadow) that is under a deck, a tunnel
 *     top or in a hidden passage shows over the top layer on a covered cell;
 *   - an actor up on a deck has OBJ priority 1 and no pixel of it is hidden
 *     by the top layer;
 *   - no priority-2 sprite pixel ever shows through an opaque BG3 pixel
 *     (the transparent-pixel priority quirk);
 *   - an actor's priority never changes in the middle of a step.
 */
#include "harness.h"
#include <stdlib.h>

static const u16 DIR_KEY[4] = { KEY_DOWN, KEY_UP, KEY_LEFT, KEY_RIGHT };

/* ---------------- the screen as the GBA composes it ---------------- */

static s16 owner[160][240];   /* OAM index whose colour the OBJ layer shows, -1: none */
static u8 oprio[160][240];    /* the OBJ layer's priority there (after the quirk) */
static u8 top[160][240];      /* BG3 opaque */
static u8 opaque_of[128][64 * 64 / 8];   /* per entry: its own opaque pixels (bit per pixel of its box) */

static const u8 OBJ_W[3][4] = { { 8, 16, 32, 64 }, { 16, 32, 32, 64 }, { 8, 8, 16, 32 } };
static const u8 OBJ_H[3][4] = { { 8, 16, 32, 64 }, { 8, 8, 16, 32 }, { 16, 32, 32, 64 } };

static int obj_pixel(int tile, int w, int x, int y)
{
    int t = tile + (y >> 3) * (w >> 3) + (x >> 3);
    const u8 *d = (const u8 *)VRAM_OBJ_TILES + (t & 1023) * 32 + (y & 7) * 4 + ((x & 7) >> 1);
    return (x & 1) ? *d >> 4 : *d & 15;
}

static int entry_box(int i, int *x, int *y, int *w, int *h)
{
    const u16 *o = &oam_shadow[i * 4];
    if ((o[0] & 0x0300) == 0x0200) return 0;        /* hidden */
    if (o[0] & 0x0100) return 0;                    /* affine: none in these scenes */
    if (((o[0] >> 10) & 3) == 2) return 0;          /* OBJ window */
    int shape = o[0] >> 14, size = o[1] >> 14;
    if (shape > 2) return 0;
    *w = OBJ_W[shape][size];
    *h = OBJ_H[shape][size];
    *y = o[0] & 255;
    if (*y >= 160) *y -= 256;
    *x = o[1] & 511;
    if (*x >= 240) *x -= 512;
    return 1;
}

static void compose(void)
{
    memset(owner, 0xFF, sizeof(owner));
    memset(oprio, 4, sizeof(oprio));
    memset(opaque_of, 0, sizeof(opaque_of));
    for (int i = 0; i < 128; i++) {
        int x0, y0, w, h;
        if (!entry_box(i, &x0, &y0, &w, &h)) continue;
        const u16 *o = &oam_shadow[i * 4];
        int prio = (o[2] >> 10) & 3, tile = o[2] & 1023, hf = (o[1] >> 12) & 1, vf = (o[1] >> 13) & 1;
        for (int y = 0; y < h; y++) {
            int sy = y0 + y;
            if (sy < 0 || sy >= 160) continue;
            for (int x = 0; x < w; x++) {
                int sx = x0 + x;
                if (sx < 0 || sx >= 240) continue;
                int c = obj_pixel(tile, w, hf ? w - 1 - x : x, vf ? h - 1 - y : y);
                if (c) opaque_of[i][(y * w + x) >> 3] |= (u8)(1 << ((y * w + x) & 7));
                if (owner[sy][sx] >= 0 && oprio[sy][sx] <= prio) continue;
                if (c) {
                    owner[sy][sx] = (s16)i;
                    oprio[sy][sx] = (u8)prio;
                } else if (owner[sy][sx] >= 0) {
                    oprio[sy][sx] = (u8)prio;   /* the quirk: a transparent pixel lifts what is there */
                }
            }
        }
    }
    const u16 *map = VRAM_MAP(SB_FIELD_TOP);
    int hofs = REG_BG3HOFS, vofs = REG_BG3VOFS;
    for (int sy = 0; sy < 160; sy++)
        for (int sx = 0; sx < 240; sx++) {
            int bx = (sx + hofs) & 255, by = (sy + vofs) & 255;
            u16 e = map[(by >> 3) * 32 + (bx >> 3)];
            int px = bx & 7, py = by & 7;
            if (e & 0x400) px = 7 - px;
            if (e & 0x800) py = 7 - py;
            const u8 *d = (const u8 *)MEM_VRAM + (e & 1023) * 32 + py * 4 + (px >> 1);
            top[sy][sx] = ((px & 1) ? *d >> 4 : *d & 15) != 0;
        }
}

static int shown(int sx, int sy) { return owner[sy][sx] >= 0 && (!top[sy][sx] || oprio[sy][sx] <= 1); }

/* The world cell under screen pixel (sx, sy) is covered (deck, tunnel top,
 * mouth, hidden passage). */
static int covered_px(int sx, int sy)
{
    return EV_COVER(elev_at((sx + cam_x) >> 4, (sy + cam_y) >> 4)) != EC_NONE;
}

/* ---------------- actors ---------------- */

typedef struct {
    const Actor *a;
    int wide, tile;        /* tile: OT_PLAYER / OT_BIKE / OT_OWKIN(0) or -1 (match by place) */
    const char *name;
    int last_prio, last_x, last_y, last_moving;
} Track;

static int under(const Actor *a)
{
    int px = a->x * 16 + a->ox, py = a->y * 16 + a->oy;
    for (int y = py >> 4; y <= (py + 15) >> 4; y++)
        for (int x = px >> 4; x <= (px + 15) >> 4; x++) {
            u16 e = elev_at(x, y);
            int c = EV_COVER(e);
            if (c == EC_HIDDEN || c == EC_MOUTH) return 1;
            if ((c == EC_BRIDGE_H || c == EC_BRIDGE_V || c == EC_TUNNEL) && a->level < EV_HI(e)) return 1;
        }
    return 0;
}

static int on_deck(const Actor *a)
{
    int px = a->x * 16 + a->ox, py = a->y * 16 + a->oy;
    u16 e = elev_at((px + 8) >> 4, (py + 8) >> 4);
    int c = EV_COVER(e);
    return (c == EC_BRIDGE_H || c == EC_BRIDGE_V || c == EC_TUNNEL) && a->level == EV_HI(e) &&
           a->level != EV_LO(e);
}

/* The actor's OAM entries: its sprite (first) and its shadow; 0 when its
 * sprite is not in OAM. */
static int entries_of(const Track *t, int *out)
{
    int wx = t->a->x * 16 + t->a->ox, wy = t->a->y * 16 + t->a->oy, lift = actor_lift(t->a);
    int ex = (wx - (t->wide ? 8 : 0) - cam_x) & 511;
    int by = (wy - cam_y - 16 - lift) & 255, sy = (wy - cam_y) & 255;
    out[0] = out[1] = -1;
    for (int i = 0; i < 128; i++) {
        int x, y, w, h;
        if (!entry_box(i, &x, &y, &w, &h)) continue;
        const u16 *o = &oam_shadow[i * 4];
        int tile = o[2] & 1023, oy = o[0] & 255;
        if ((o[1] & 511) != ex) continue;
        if (out[0] < 0 && oy == by && (t->wide ? w == 32 && h == 32 : w == 16 && h == 32) &&
            (t->tile < 0 || tile == t->tile))
            out[0] = i;
        else if (out[1] < 0 && oy == sy &&
                 (t->wide ? w == 32 && h == 16 && (tile == OT_SHADOW_KIN(0) || tile == OT_SHADOW_KIN(1))
                          : w == 16 && h == 16 && (tile == OT_SHADOW(0) || tile == OT_SHADOW(1))))
            out[1] = i;
    }
    if (out[0] < 0) return 0;
    return out[1] >= 0 ? 2 : 1;
}

static int frame_fail, frames_checked, quirk_px, under_px, deck_hidden, toggles;
static char first_fail[160];

static void fail_once(const char *what, const Track *t)
{
    frame_fail = 1;
    if (!first_fail[0])
        snprintf(first_fail, sizeof(first_fail), "%s: %s at %d,%d%+d%+d level %d (map %s)", what, t->name,
                 t->a->x, t->a->y, t->a->ox, t->a->oy, t->a->level, MAPS[cur_map].name);
}

/* Draw the field's sprites as game_frame does (plus a rain streak pushed
 * last over the head of each `rain` actor), present the view and compose
 * the screen. */
static void draw_compose(Actor *const *rain, int nr)
{
    oam_begin();
    field_draw_sprites();
    for (int k = 0; k < nr; k++)
        spr_push(rain[k]->x * 16 + rain[k]->ox - cam_x, rain[k]->y * 16 + rain[k]->oy - cam_y - 14,
                 OT_EMOTE + EMOTE_RAIN * 4, SQ16, OBANK_EMOTE, 1, 0);
    oam_end();
    field_render_view();
    compose();
    frames_checked++;
}

static void check_tracks(Track *tr, int nt)
{
    /* the quirk: a priority-2 pixel through the top layer */
    for (int sy = 0; sy < 160; sy++)
        for (int sx = 0; sx < 240; sx++) {
            int i = owner[sy][sx];
            if (i >= 0 && top[sy][sx] && oprio[sy][sx] <= 1 && ((oam_shadow[i * 4 + 2] >> 10) & 3) >= 2) {
                quirk_px++;
                frame_fail = 1;
                if (!first_fail[0])
                    snprintf(first_fail, sizeof(first_fail), "a priority-2 pixel through the top layer at %d,%d",
                             sx, sy);
            }
        }
    for (int k = 0; k < nt; k++) {
        Track *t = &tr[k];
        int e[2], ne = entries_of(t, e);
        int wx = t->a->x * 16 + t->a->ox - cam_x, wy = t->a->y * 16 + t->a->oy - cam_y;
        if (!ne) {
            if (wx > -8 && wx < 232 && wy > 0 && wy < 150) fail_once("sprite not found", t);
            continue;
        }
        int prio = (oam_shadow[e[0] * 4 + 2] >> 10) & 3;
        int is_under = under(t->a), is_on = on_deck(t->a);
        for (int j = 0; j < ne; j++) {
            int x0, y0, w, h;
            entry_box(e[j], &x0, &y0, &w, &h);
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++) {
                    int sx = x0 + x, sy = y0 + y;
                    if (sx < 0 || sy < 0 || sx >= 240 || sy >= 160) continue;
                    if (!(opaque_of[e[j]][(y * w + x) >> 3] & (1 << ((y * w + x) & 7)))) continue;
                    if (!top[sy][sx] || !covered_px(sx, sy)) continue;
                    if (is_under && owner[sy][sx] == e[j] && shown(sx, sy)) {
                        under_px++;
                        fail_once("under a cover but drawn over it", t);
                    }
                    if (is_on && !shown(sx, sy)) {
                        deck_hidden++;
                        fail_once("on a deck but hidden by it", t);
                    }
                }
        }
        if (is_on && prio != 1) fail_once("on a deck without priority 1", t);
        /* no change of priority in the middle of a step */
        if (t->last_prio && prio != t->last_prio && t->a->moving && t->last_moving && t->a->x == t->last_x &&
            t->a->y == t->last_y) {
            toggles++;
            fail_once("priority changed mid-step", t);
        }
        t->last_prio = prio;
        t->last_x = t->a->x;
        t->last_y = t->a->y;
        t->last_moving = t->a->moving;
    }
}

static void check_frame(Track *tr, int nt)
{
    draw_compose(0, 0);
    check_tracks(tr, nt);
}

/* ---------------- scenes ---------------- */

static void enter(int map, int x, int y, int dir)
{
    game_mode = MODE_FIELD;
    dialog_clear();
    field_enter_map(map, x, y, dir);
    warp.active = 0;
    set_brightness(0);
    for (int i = 0; i < WILD_MAX; i++) wild[i].active = 0;
    step(0);
    step(0);
}

/* Is (x, y) plain walkable ground at `level` (not a face, stairs, ledge,
 * deck top; no person or wall)? */
static int ground(int x, int y, int level)
{
    if (x < 0 || y < 0 || x >= map_w || y >= map_h) return 0;
    u16 e = elev_at(x, y);
    if (EV_KIND(e) != EK_GROUND || EV_LO(e) != level) return 0;
    if (cell_attr(x, y) & (A_SOLID | A_WATER | A_LEDGE)) return 0;
    return npc_at_lv(x, y, level) < 0;
}

/* A straight line of `n` steps from (x, y) in `dir` on `level` that the
 * elevation rules allow. */
static int line_ok(int x, int y, int level, int dir, int n)
{
    for (int i = 0; i < n; i++) {
        int nl, k = elev_enter(x, y, level, dir, &nl);
        if (k == ELEV_BLOCK || nl != level) return 0;
        x += DIR_DX[dir];
        y += DIR_DY[dir];
        if (k == ELEV_FLOOR && !ground(x, y, level)) return 0;
        if (npc_at_lv(x, y, level) >= 0) return 0;
    }
    return 1;
}

static Track tracks[4];

/* Walk the player (and the follower behind) `n` cells in `dir` with the
 * key held, checking every frame; returns the cells actually walked. */
static int walk_checked(int dir, int n, int nt)
{
    int sx = player.x, sy = player.y, stuck = 0;
    int tx = sx + DIR_DX[dir] * n, ty = sy + DIR_DY[dir] * n;
    for (int f = 0; f < 60 * 20 && stuck < 40; f++) {
        int arrived = player.x == tx && player.y == ty;
        step(arrived ? 0 : DIR_KEY[dir]);
        check_frame(tracks, nt);
        if (arrived && !player.moving && !follower.a.moving) break;
        stuck = player.moving ? 0 : stuck + 1;
    }
    for (int f = 0; f < 20; f++) {   /* standing: the follower catches up */
        step(0);
        check_frame(tracks, nt);
    }
    return abs(player.x - sx) + abs(player.y - sy);
}

static void track_player(int nt_extra)
{
    (void)nt_extra;
    memset(tracks, 0, sizeof(tracks));
    tracks[0] = (Track){ &player, travel.biking, travel.biking ? OT_BIKE : OT_PLAYER, "the player", 0, 0, 0, 0 };
    tracks[1] = (Track){ &follower.a, 1, OT_OWKIN(0), "the follower", 0, 0, 0, 0 };
}

typedef struct { int x, y, dir, n, level; } Line;

/* The line walked under a feature (and n steps), -1 when there is none. */
static int under_line(const ElevFeat *f, Line *l)
{
    int lo = EV_LO(elev_at(f->x, f->y));
    if (f->kind == EF_BRIDGE_V) {   /* under it: east-west */
        for (int y = f->y; y < f->y + f->h; y++)
            for (int back = 2; back >= 1; back--) {
                int x0 = f->x - back, n = f->w + back + 1;
                if (ground(x0, y, lo) && line_ok(x0, y, lo, DIR_RIGHT, n)) {
                    *l = (Line){ x0, y, DIR_RIGHT, n, lo };
                    return 1;
                }
            }
        return 0;
    }
    /* BRIDGE_H and TUNNEL: north-south, from two (or one) cells south of
     * the cell in front of it (a tunnel's front is its mouth) */
    for (int x = f->x; x < f->x + f->w; x++)
        for (int back = 3; back >= 2; back--) {
            int y0 = f->y + f->h + back - 1 + (f->kind == EF_TUNNEL), n = y0 - (f->y - 1);
            if (ground(x, y0, lo) && line_ok(x, y0, lo, DIR_UP, n)) {
                *l = (Line){ x, y0, DIR_UP, n, lo };
                return 1;
            }
        }
    return 0;
}

/* The line walked over a feature: along a bridge, across a tunnel top. */
static int over_line(const ElevFeat *f, Line *l)
{
    int hi = EV_HI(elev_at(f->x, f->y));
    if (f->kind == EF_BRIDGE_V) {
        for (int x = f->x; x < f->x + f->w; x++)
            for (int back = 2; back >= 1; back--) {
                int y0 = f->y - back, n = f->h + 2 * back;
                if (ground(x, y0, hi) && line_ok(x, y0, hi, DIR_DOWN, n)) {
                    *l = (Line){ x, y0, DIR_DOWN, n, hi };
                    return 1;
                }
            }
        return 0;
    }
    for (int y = f->y; y < f->y + f->h; y++)
        for (int back = 2; back >= 1; back--) {
            int x0 = f->x - back, n = f->w + 2 * back;
            if (ground(x0, y, hi) && line_ok(x0, y, hi, DIR_RIGHT, n)) {
                *l = (Line){ x0, y, DIR_RIGHT, n, hi };
                return 1;
            }
        }
    return 0;
}

static int scenes, crossings;

/* The player (with the follower, on foot or on the bike) walks the line
 * and back. */
static void cross(int map, const Line *l, int bike, const char *what)
{
    enter(map, l->x, l->y, l->dir);
    player.level = (u8)l->level;
    follower_reset();
    travel.biking = (u8)bike;
    track_player(0);
    frame_fail = 0;
    first_fail[0] = 0;
    int a = walk_checked(l->dir, l->n, 2);
    int b = walk_checked(DIR_BACK[l->dir], l->n, 2);
    travel.biking = 0;
    char msg[256];
    static const char *const DIR_NAME[4] = { "south", "north", "west", "east" };
    snprintf(msg, sizeof(msg), "%s: %s %s, from %d,%d %s (%d + %d cells)%s%s", MAPS[map].name, what,
             bike ? "on the bike" : "with the follower", l->x, l->y, DIR_NAME[l->dir], a, b,
             first_fail[0] ? " -- " : "", first_fail);
    CHECK(!frame_fail && a == l->n && b == l->n, msg);
    crossings++;
}

/* The player stands on the deck (or tunnel top); a person, a person's kin
 * and a wild kin walk the line under it, a rain streak over each. */
static void parade(int map, const ElevFeat *f, const Line *l)
{
    Line ov;
    if (!over_line(f, &ov)) return;
    /* the player up on the deck in the middle of the over line, off the
     * walkers' own line (sprites are told apart by where they are), alone */
    int hx = ov.x + DIR_DX[ov.dir] * (ov.n / 2), hy = ov.y + DIR_DY[ov.dir] * (ov.n / 2);
    int vertical = DIR_DY[l->dir] != 0;
    if (vertical ? hx == l->x : hy == l->y) {
        hx += vertical ? 1 : 0;
        hy += vertical ? 0 : 1;
        if (vertical ? !(hx < f->x + f->w) : !(hy < f->y + f->h)) {
            hx -= vertical ? 2 : 0;
            hy -= vertical ? 0 : 2;
        }
    }
    opt.follower = 0;
    enter(map, hx, hy, ov.dir);
    player.level = (u8)elev_level_at(hx, hy, ov.level, ov.dir);
    int npc = -1;
    for (int i = 0; i < NPC_COUNT && npc < 0; i++)
        if (NPCS[i].map == map) npc = i;
    if (npc < 0) return;
    Actor keep = npc_state[npc];
    KinActor keep_kin = npc_kin[npc];
    Actor *walker[3] = { &npc_state[npc], &npc_kin[npc].a, &wild[0].k.a };
    npc_kin[npc].species = SP_PYREFOX;
    npc_kin[npc].shown = 1;
    wild[0].active = 1;
    wild[0].k.species = SP_GOLEMIT;
    wild[0].k.shown = 1;
    for (int k = 0; k < 3; k++) {
        Actor *a = walker[k];
        memset(a, 0, sizeof(*a));
        a->x = (s16)(l->x - DIR_DX[l->dir] * k * 2);
        a->y = (s16)(l->y - DIR_DY[l->dir] * k * 2);
        a->facing = (u8)l->dir;
        a->level = (u8)l->level;
    }
    memset(tracks, 0, sizeof(tracks));
    tracks[0] = (Track){ &player, 0, OT_PLAYER, "the player on top", 0, 0, 0, 0 };
    tracks[1] = (Track){ walker[0], 0, -1, "a person", 0, 0, 0, 0 };
    tracks[2] = (Track){ walker[1], 1, -1, "a person's kin", 0, 0, 0, 0 };
    tracks[3] = (Track){ walker[2], 1, -1, "a wild kin", 0, 0, 0, 0 };
    frame_fail = 0;
    first_fail[0] = 0;
    int steps[3] = { 0, 0, 0 }, total = l->n + 4;
    for (int f = 0; f < 16 * (total + 6) + 40; f++) {
        for (int k = 0; k < 3; k++) {
            Actor *a = walker[k];
            if (!a->moving && steps[k] < total) {
                actor_start_move(a, steps[k] < total / 2 + 2 ? l->dir : DIR_BACK[l->dir]);
                steps[k]++;
            }
            actor_step(a, 1);
        }
        field_anim_frame++;
        draw_compose(walker, 3);
        check_tracks(tracks, 4);
    }
    npc_state[npc] = keep;
    npc_kin[npc] = keep_kin;
    wild[0].active = 0;
    opt.follower = 1;
    char msg[256];
    snprintf(msg, sizeof(msg), "%s: a person, a kin and a wild kin pass under, the player on top%s%s",
             MAPS[map].name, first_fail[0] ? " -- " : "", first_fail);
    CHECK(!frame_fail, msg);
}

/* ---------------- the priority rule, cell by cell ---------------- */

static void rule_checks(void)
{
    /* Maple Village: the Maple Run bridge (19-22, 17-18) over the lane
     * (x 19-20) */
    map_load(MAP_TOWN);
    Actor a = { 0 };
    a.x = 19;
    a.y = 19;
    a.level = 0;
    CHECK(elev_obj_prio(&a) == 1, "rule: standing just south of the deck, in front of it (1)");
    a.y = 18;
    a.oy = 15;
    a.moving = 1;
    a.facing = DIR_UP;
    CHECK(elev_obj_prio(&a) == 2 && elev_obj_prio_w(&a, 1) == 2,
          "rule: the first pixel of a step under the deck: already under it (2)");
    a.oy = 1;
    CHECK(elev_obj_prio(&a) == 2, "rule: the last pixel of that step: under it (2)");
    a.y = 19;
    a.oy = -15;
    a.facing = DIR_DOWN;
    CHECK(elev_obj_prio(&a) == 2, "rule: stepping out from under it southward stays under until the step ends");
    a.oy = -1;
    CHECK(elev_obj_prio(&a) == 2, "rule: ... to its last pixel");
    a.oy = 0;
    a.moving = 0;
    CHECK(elev_obj_prio(&a) == 1, "rule: then in front of it (1)");
    a.x = 22;
    a.y = 17;
    a.level = 1;
    CHECK(elev_obj_prio(&a) == 1, "rule: on the deck (1)");
    a.x = 23;
    CHECK(elev_obj_prio(&a) == 2 && elev_obj_prio_w(&a, 1) == 1,
          "rule: off its east end a person is clear of it (2), a 32-wide kin still overlaps it (1)");
    a.x = 20;
    a.y = 16;
    a.level = 0;
    CHECK(elev_obj_prio(&a) == 2, "rule: north of the deck on the ground: behind it (2)");
}

/* ---------------- OAM order ---------------- */

static void oam_checks(void)
{
    oam_begin();
    spr_push(10, 10, 5, SQ16, 0, 2, 0);
    spr_push(20, 10, 6, SQ16, 0, 1, 0);
    spr_push(30, 10, 7, SQ16, 0, 3, 0);
    spr_push(40, 10, 8, SQ16, 0, 1, 0);
    spr_push(50, 10, 9, SQ16, 0, 0, 0);
    oam_end();
    int order[5];
    for (int i = 0; i < 5; i++) order[i] = oam_shadow[i * 4 + 2] & 1023;
    CHECK(order[0] == 9 && order[1] == 6 && order[2] == 8 && order[3] == 5 && order[4] == 7 && oam_count == 5 &&
              (oam_shadow[5 * 4] & 0x0300) == 0x0200,
          "OAM: sprites ordered by priority, pushed order kept within one");
    oam_begin();
    int m = oam_affine(256, 0, 0, 256);
    spr_push_affine(10, 10, 5, SQ16, 0, 2, 0, m, 0);
    spr_push(20, 10, 6, SQ16, 0, 1, 0);
    oam_end();
    CHECK((oam_shadow[0 * 4 + 2] & 1023) == 6 && (oam_shadow[1 * 4 + 2] & 1023) == 5 &&
              (oam_shadow[1 * 4] & 0x0100) && oam_shadow[3] == 256,
          "OAM: affine sprites move with their attributes, the matrices stay");
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    fresh_game();
    give_starter();
    flag_set(FLAG_INTRO);
    opt.follower = 1;
    bag[ITEM_BIKE] = 1;

    oam_checks();
    rule_checks();

    /* every bridge and tunnel, in the rain (the storm is not calmed) */
    for (int m = 0; m < MAP_COUNT; m++) {
        const MapDef *d = &MAPS[m];
        if (!d->elev || !d->feat_count) continue;
        map_load(m);
        if (!map_elevated) continue;
        for (int i = 0; i < d->feat_count; i++) {
            const ElevFeat *f = &d->feats[i];
            if (f->kind == EF_HIDDEN) continue;
            Line l;
            map_load(m);
            scenes++;
            if (under_line(f, &l)) {
                cross(m, &l, 0, f->kind == EF_TUNNEL ? "through the tunnel" : "under the bridge");
                cross(m, &l, 1, f->kind == EF_TUNNEL ? "through the tunnel" : "under the bridge");
                map_load(m);
                parade(m, f, &l);
            }
            map_load(m);
            if (over_line(f, &l)) cross(m, &l, 0, f->kind == EF_TUNNEL ? "over the tunnel" : "over the bridge");
        }
    }
    printf("%d features, %d crossings, %d frames composed\n", scenes, crossings, frames_checked);
    CHECK(crossings >= 20, "every town's bridges are crossed over and under");
    CHECK(quirk_px == 0, "no priority-2 pixel ever shows through the top layer");
    CHECK(under_px == 0 && toggles == 0 && deck_hidden == 0,
          "nobody under a deck is drawn over it, nobody on one is hidden, no priority flips mid-step");

    if (failures) {
        printf("%d elevation sprite check(s) FAILED\n", failures);
        return 1;
    }
    printf("all elevation sprite checks passed\n");
    return 0;
}
