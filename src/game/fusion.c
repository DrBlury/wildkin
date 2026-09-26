/*
 * Energy and fusion at the RESONANCE WORKS (docs/EXPANSION.md 7.4). Owner:
 * FUSION system.
 *
 *   UNBIND  a kin from the team or the Shelf becomes typed energy
 *           (8 + level / 2, x1.5 rare or fusion, x4 legend, x2 lustrous;
 *           dual types split 60/40, fusion kin give back their signature
 *           50/50). Its body goes home to the wild.
 *   ENERGY  the 18 pools (u16, capped at 9999), what makes each and what
 *           it weaves.
 *   MIX     two energies become a third (MIX_RECIPES: 26 unordered pairs,
 *           every type reachable from the seven starting ones). The tuning
 *           minigame sets the yield from 60% to 120%.
 *   LOOM    pick up to 3 types and a stake (10 / 30 / 60 of each). Chance
 *           = 6 + stake bonus (0 / 6 / 14) + harmony (8 * min / max of the
 *           picked stores) + 3 per miss since the last fusion, and a sure
 *           thing after 25 misses. A hit weaves one of the candidates (the
 *           fusions whose signature types are all picked; ones you have
 *           never had weigh 3, the rest 1) at level 15 / 25 / 40. A miss
 *           gives 1 / 2 / 3 MOTE DUST and 30% of the stake back.
 *
 * The screens draw the machine scenes from gfx_fusion.h into the UI canvas
 * (BG banks 3..7; banks 0..2 hold the type-glyph palettes) and use OBJ tiles
 * 640..767 (glyphs, particles, the cursor corner) with OBJ banks 2..6.
 * field_return() reloads everything the field needs afterwards.
 *
 * APIs for other owners:
 *   fusion_open(FUSION_SCREEN_*)   the Works machines (SCR_FUSION_DESK)
 *   fusion_key_use(KEY_ENERGY_FLASK)
 *   fusion_energy(t), fusion_energy_add(t, n)   quest / craft rewards
 *   fusion_tuner_open(title, done)  the tuning minigame (yield 60..120%)
 *   fusion_examine(decor_kind)      the machines in the Works (script.c)
 */

/* ================================================================ */
/*  State (saved: docs/EXPANSION.md 10.4, at most MOD_FUSION_MAX)    */
/* ================================================================ */

#define FZ_ENERGY_MAX 9999
#define FZ_PITY_CAP 25          /* misses in a row that guarantee a fusion */

enum {
    FZF_INTRO = 1,      /* the desk clerk explained the Works and gave the ENERGY FLASK */
    FZF_UNBOUND = 2,    /* first unbinding done */
    FZF_MIXED = 4,      /* first mix done */
    FZF_WOVEN = 8,      /* first fusion woven */
    FZF_WEAVED = 16,    /* first weave tried */
};

typedef struct {
    u16 energy[TYPE_COUNT];   /* 0..9999 each */
    u16 pity;                 /* misses since the last fusion (0..25) */
    u16 weaves;               /* total weaves */
    u16 hits;                 /* fusions woven */
    u16 unbound;              /* kin unbound */
    u16 mixes;                /* mixes done */
    u8 flags;                 /* FZF_* */
    u8 pad;
} FusionState;
typedef char FusionStateIs48[sizeof(FusionState) == 48 ? 1 : -1];

static FusionState fusion;

static void fusion_reset(void)
{
    u8 *raw = (u8 *)&fusion;
    for (unsigned i = 0; i < sizeof(fusion); i++) raw[i] = 0;
}

static void fusion_validate(void)
{
    for (int t = 0; t < TYPE_COUNT; t++)
        if (fusion.energy[t] > FZ_ENERGY_MAX) fusion.energy[t] = FZ_ENERGY_MAX;
    if (fusion.pity > FZ_PITY_CAP) fusion.pity = FZ_PITY_CAP;
    if (fusion.hits > fusion.weaves) fusion.hits = fusion.weaves;
    fusion.flags &= 31;
    fusion.pad = 0;
}

MAYBE_UNUSED static int fusion_energy(int type)
{
    return type >= 0 && type < TYPE_COUNT ? fusion.energy[type] : 0;
}

/* Adds (or with n < 0 takes) energy; returns the amount actually moved. */
static int fusion_energy_add(int type, int n)
{
    if (type < 0 || type >= TYPE_COUNT) return 0;
    int before = fusion.energy[type];
    fusion.energy[type] = (u16)clampi(before + n, 0, FZ_ENERGY_MAX);
    return fusion.energy[type] - before;
}

MAYBE_UNUSED static int fusion_energy_total(void)
{
    int n = 0;
    for (int t = 0; t < TYPE_COUNT; t++) n += fusion.energy[t];
    return n;
}

/* ================================================================ */
/*  Rules                                                           */
/* ================================================================ */

/* ---------------- unbinding ---------------- */

/* The energy a kin unbinds into: fills type[] / amt[], returns 1 or 2. */
static int fusion_unbind_yield(const Monster *m, u8 *type, u16 *amt)
{
    const Species *s = &SPECIES[m->species];
    int n = 8 + m->level / 2;
    if (s->rarity == R_RARE || s->rarity == R_FUSION) n = n * 3 / 2;
    if (s->rarity == R_LEGEND) n *= 4;
    if (m->flags & MF_LUSTROUS) n *= 2;
    if (s->rarity == R_FUSION && s->fusion[0] < TYPE_COUNT && s->fusion[1] < TYPE_COUNT) {
        type[0] = s->fusion[0];
        type[1] = s->fusion[1];
        amt[0] = (u16)((n + 1) / 2);
        amt[1] = (u16)(n / 2);
        return 2;
    }
    type[0] = s->type1;
    amt[0] = (u16)n;
    if (s->type2 == TYPE_NONE || s->type2 == s->type1) return 1;
    type[1] = s->type2;
    amt[0] = (u16)((n * 6 + 5) / 10);
    amt[1] = (u16)(n - amt[0]);
    return 2;
}

/* The wild zone a kin (or the first stage of its line) lives in, or 0. */
static const char *fusion_home_wild(int sp)
{
    for (int pass = 0; pass < 4 && sp >= 0; pass++) {
        for (int z = 1; z < ZONE_COUNT; z++) {
            const WildZone *w = &WILD_ZONES[z];
            if (!w->name || !w->name[0]) continue;
            for (int i = 0; i < w->count; i++)
                if (w->slots[i].species == sp) return w->name;
        }
        sp = species_prevo(sp);
    }
    return 0;
}

/* Unbinding slot `i` of the combined list (team first, then the Shelf):
 * why it can't be done (a message), or 0 when it can. */
static const char *fusion_unbind_blocked(int i)
{
    if (i < 0 || i >= party_count + storage_count) return "There's no kin there.";
    if (i >= party_count) return 0;
    if (party_count <= 1) return "That's your only kin on the team! Keep it with you.";
    int healthy = 0;
    for (int k = 0; k < party_count; k++)
        if (k != i && party[k].hp > 0) healthy++;
    if (!healthy) return "It's the last kin on your team who's still awake!";
    return 0;
}

static Monster fusion_list_get(int i)
{
    return i < party_count ? party[i] : storage_get(i - party_count);
}

/* Unbinds a kin (team slot, or Shelf slot i - party_count): the energy is
 * added and the kin leaves. Returns the number of energy types (0 = not
 * allowed); the kin, types and amounts gained are written out. */
static int fusion_unbind(int i, Monster *out, u8 *type, u16 *amt)
{
    if (fusion_unbind_blocked(i)) return 0;
    Monster m;
    if (i < party_count) {
        m = party[i];
        for (int k = i; k < party_count - 1; k++) party[k] = party[k + 1];
        party_count--;
    } else {
        m = storage_take(i - party_count);
    }
    int n = fusion_unbind_yield(&m, type, amt);
    for (int k = 0; k < n; k++) amt[k] = (u16)fusion_energy_add(type[k], amt[k]);
    if (fusion.unbound < 0xFFFF) fusion.unbound++;
    fusion.flags |= FZF_UNBOUND;
    if (out) *out = m;
    return n;
}

/* ---------------- mixing ---------------- */

typedef struct { u8 a, b, out; const char *name; } MixRecipe;

static const MixRecipe MIX_RECIPES[] = {
    { T_BLAZE, T_TIDE, T_GALE, "STEAM" },
    { T_SPARK, T_STONE, T_METAL, "SMELTING" },
    { T_HOLLOW, T_DREAM, T_RELIC, "MEMORY" },
    { T_BLOOM, T_DUSK, T_VENOM, "ROT" },
    { T_BLOOM, T_BRAWL, T_BEAST, "GRAZING" },
    { T_VENOM, T_GALE, T_BLAZE, "MARSH GAS" },
    { T_SPARK, T_BLOOM, T_BLAZE, "WILDFIRE" },
    { T_FROST, T_BLAZE, T_TIDE, "MELT" },
    { T_TIDE, T_STONE, T_BLOOM, "SOIL" },
    { T_GALE, T_FROST, T_SPARK, "STORMCLOUD" },
    { T_DUSK, T_TIDE, T_FROST, "HOARFROST" },
    { T_STONE, T_BEAST, T_BRAWL, "HAULING" },
    { T_SWARM, T_TIDE, T_STONE, "REEF" },
    { T_METAL, T_TIDE, T_STONE, "RUST" },
    { T_HOLLOW, T_TIDE, T_STONE, "FOSSIL" },
    { T_SWARM, T_SPARK, T_DREAM, "NEURONS" },
    { T_BEAST, T_DUSK, T_DREAM, "SLUMBER" },
    { T_RELIC, T_SPARK, T_DREAM, "ECHO" },
    { T_BLOOM, T_GALE, T_SWARM, "POLLEN" },
    { T_BLAZE, T_BLOOM, T_DUSK, "CHARCOAL" },
    { T_GALE, T_TIDE, T_WYRM, "STORM" },
    { T_BEAST, T_VENOM, T_HOLLOW, "DECAY" },
    { T_WYRM, T_STONE, T_HOLLOW, "DEEP TIME" },
    { T_METAL, T_BRAWL, T_RELIC, "HANDWORK" },
    { T_ASTRAL, T_STONE, T_METAL, "METEORITE" },
    { T_SPARK, T_DUSK, T_ASTRAL, "AURORA" },
};
#define MIX_COUNT ((int)(sizeof(MIX_RECIPES) / sizeof(MIX_RECIPES[0])))
#define MIX_STEP 10             /* units per step of the amount picker */
#define TUNE_YIELD_MIN 60
#define TUNE_YIELD_MAX 120

/* The recipe for an unordered pair, or -1. */
MAYBE_UNUSED static int fusion_mix_find(int a, int b)
{
    for (int r = 0; r < MIX_COUNT; r++)
        if ((MIX_RECIPES[r].a == a && MIX_RECIPES[r].b == b) ||
            (MIX_RECIPES[r].a == b && MIX_RECIPES[r].b == a))
            return r;
    return -1;
}

/* The most of each input recipe r can take (a multiple of MIX_STEP). */
static int fusion_mix_max(int r)
{
    if (r < 0 || r >= MIX_COUNT) return 0;
    int a = fusion.energy[MIX_RECIPES[r].a], b = fusion.energy[MIX_RECIPES[r].b];
    int n = a < b ? a : b;
    return n - n % MIX_STEP;
}

/* What n of each input give at a yield (percent). */
static int fusion_mix_output(int n, int yield)
{
    return n * clampi(yield, TUNE_YIELD_MIN, TUNE_YIELD_MAX) / 100;
}

/* Mixes n of each input of recipe r at `yield` percent; returns the energy
 * made (0 = not enough energy). */
static int fusion_mix(int r, int n, int yield)
{
    if (r < 0 || r >= MIX_COUNT || n <= 0) return 0;
    const MixRecipe *m = &MIX_RECIPES[r];
    if (fusion.energy[m->a] < n || fusion.energy[m->b] < n) return 0;
    fusion.energy[m->a] = (u16)(fusion.energy[m->a] - n);
    fusion.energy[m->b] = (u16)(fusion.energy[m->b] - n);
    int made = fusion_energy_add(m->out, fusion_mix_output(n, yield));
    if (fusion.mixes < 0xFFFF) fusion.mixes++;
    fusion.flags |= FZF_MIXED;
    return made;
}

/* ---------------- the Loom ---------------- */

#define LOOM_PICK_MAX 3
#define LOOM_CAND_MAX 8
enum { STAKE_SMALL, STAKE_MEDIUM, STAKE_LARGE, STAKE_COUNT };
static const u8 STAKE_UNITS[STAKE_COUNT] = { 10, 30, 60 };
static const u8 STAKE_BONUS[STAKE_COUNT] = { 0, 6, 14 };
static const u8 STAKE_LEVEL[STAKE_COUNT] = { 15, 25, 40 };
static const u8 STAKE_DUST[STAKE_COUNT] = { 1, 2, 3 };
#define LOOM_BASE 6
#define LOOM_HARMONY 8
#define LOOM_PITY_STEP 3
#define LOOM_REFUND_PCT 30

static int loom_has(const u8 *types, int n, int t)
{
    for (int i = 0; i < n; i++)
        if (types[i] == t) return 1;
    return 0;
}

/* The fusion kin the picked types can weave (at most LOOM_CAND_MAX). */
static int fusion_loom_candidates(const u8 *types, int n, u8 *out)
{
    int c = 0;
    for (int sp = 0; sp < SP_COUNT && c < LOOM_CAND_MAX; sp++) {
        const Species *s = &SPECIES[sp];
        if (s->rarity != R_FUSION || s->fusion[0] >= TYPE_COUNT || s->fusion[1] >= TYPE_COUNT) continue;
        if (loom_has(types, n, s->fusion[0]) && loom_has(types, n, s->fusion[1])) out[c++] = (u8)sp;
    }
    return c;
}

/* Harmony bonus: 8 * the smallest picked store / the largest. */
static int fusion_loom_harmony(const u8 *types, int n)
{
    int lo = FZ_ENERGY_MAX + 1, hi = 0;
    for (int i = 0; i < n; i++) {
        int e = fusion.energy[types[i]];
        if (e < lo) lo = e;
        if (e > hi) hi = e;
    }
    return n > 0 && hi > 0 ? LOOM_HARMONY * lo / hi : 0;
}

/* The chance (percent) of a weave hitting. */
static int fusion_loom_chance(const u8 *types, int n, int stake)
{
    if (fusion.pity >= FZ_PITY_CAP) return 100;
    stake = clampi(stake, 0, STAKE_COUNT - 1);
    int c = LOOM_BASE + STAKE_BONUS[stake] + fusion_loom_harmony(types, n) + LOOM_PITY_STEP * fusion.pity;
    return clampi(c, 0, 100);
}

enum { LOOM_OK, LOOM_TOO_FEW, LOOM_NO_CANDIDATE, LOOM_LOW_ENERGY, LOOM_NO_ROOM };

static int fusion_loom_check(const u8 *types, int n, int stake)
{
    if (n < 2) return LOOM_TOO_FEW;
    u8 cand[LOOM_CAND_MAX];
    if (!fusion_loom_candidates(types, n, cand)) return LOOM_NO_CANDIDATE;
    for (int i = 0; i < n; i++)
        if (fusion.energy[types[i]] < STAKE_UNITS[clampi(stake, 0, STAKE_COUNT - 1)]) return LOOM_LOW_ENERGY;
    if (party_count >= PARTY_MAX && storage_count >= STORAGE_MAX) return LOOM_NO_ROOM;
    return LOOM_OK;
}

/* Picks a candidate: never-owned kin weigh 3, the rest 1. */
static int fusion_loom_pick(const u8 *cand, int c)
{
    int total = 0;
    for (int i = 0; i < c; i++) total += dex_caught[cand[i]] ? 1 : 3;
    if (total <= 0) return cand[0];
    int r = (int)rng_range((unsigned)total);
    for (int i = 0; i < c; i++) {
        r -= dex_caught[cand[i]] ? 1 : 3;
        if (r < 0) return cand[i];
    }
    return cand[c - 1];
}

typedef struct {
    int hit;          /* 1 = a fusion was woven */
    int species;      /* the new kin (hit) */
    int where;        /* give_monster(): 0 team, 1 Shelf */
    int dust;         /* MOTE DUST gained (miss) */
    int refund;       /* energy back per type (miss) */
    int chance;
    Monster mon;
} WeaveResult;

/* One weave on the Loom. Returns 0 (nothing spent) unless fusion_loom_check
 * passes. */
static int fusion_weave(const u8 *types, int n, int stake, WeaveResult *res)
{
    if (fusion_loom_check(types, n, stake) != LOOM_OK) return 0;
    stake = clampi(stake, 0, STAKE_COUNT - 1);
    u8 cand[LOOM_CAND_MAX];
    int c = fusion_loom_candidates(types, n, cand);
    int chance = fusion_loom_chance(types, n, stake);
    for (int i = 0; i < n; i++) fusion_energy_add(types[i], -STAKE_UNITS[stake]);
    if (fusion.weaves < 0xFFFF) fusion.weaves++;
    fusion.flags |= FZF_WEAVED;
    res->chance = chance;
    res->hit = (int)rng_range(100) < chance;
    res->dust = res->refund = 0;
    if (res->hit) {
        res->species = fusion_loom_pick(cand, c);
        res->mon = monster_make(res->species, STAKE_LEVEL[stake]);
        res->mon.met_map = (u8)cur_map;
        res->where = give_monster(&res->mon);
        fusion.pity = 0;
        if (fusion.hits < 0xFFFF) fusion.hits++;
        fusion.flags |= FZF_WOVEN;
    } else {
        res->species = -1;
        res->where = -1;
        if (fusion.pity < FZ_PITY_CAP) fusion.pity++;
        res->dust = STAKE_DUST[stake];
        bag_add(ITEM_MOTE_DUST, res->dust);
        res->refund = STAKE_UNITS[stake] * LOOM_REFUND_PCT / 100;
        for (int i = 0; i < n; i++) fusion_energy_add(types[i], res->refund);
    }
    return 1;
}

/* ================================================================ */
/*  Screens                                                         */
/* ================================================================ */

enum { FUSION_SCREEN_MENU, FUSION_SCREEN_UNBIND, FUSION_SCREEN_MIX, FUSION_SCREEN_LOOM,
       FUSION_SCREEN_ENERGY };

static void field_return(void);

/* OBJ VRAM 640..767 and OBJ banks 2..6 (docs/EXPANSION.md 10.3). */
#define OT_FZ_GLYPH(t)    (640 + (t) * 4)
#define OT_FZ_PART(set, k) (712 + (set) * 4 + (k))
#define OT_FZ_CORNER      720
#define OBANK_FZ_PART     2      /* 2, 3: two ramps each (A at 1..4, B at 5..8) */
#define OBANK_FZ_GLYPH    4      /* 4..6: fz_glyph_pal[t / 6] */
#define FZ_GOLD           TYPE_COUNT  /* particle ramp slot for gold sparks */

enum { FZS_WORKS, FZS_UNBIND, FZS_ENERGY, FZS_MIX, FZS_TUNE, FZS_LOOM };

enum { UB_PICK, UB_ANIM };
enum { MX_LIST, MX_AMOUNT };
enum { LM_PICK, LM_SPIN };

static struct {
    int screen, scene, redraw, frame;
    int via_works;          /* B goes back to the machine hall (else to the field) */
    int works_cursor;
    /* UNBIND */
    int ub_state, ub_cursor, ub_timer, ub_ntypes, ub_species, ub_lustrous;
    u8 ub_type[2];
    u16 ub_amt[2], ub_before[2];
    /* ENERGY */
    int en_cursor;
    /* MIX */
    int mx_state, mx_cursor, mx_scroll, mx_amount;
    /* TUNE */
    int tn_ft, tn_pt, tn_f, tn_p, tn_timer, tn_match, tn_locked, tn_shown_match;
    const char *tn_title;
    void (*tn_done)(int yield);
    int tn_return;          /* screen to go back to when the tuner closes */
    /* LOOM */
    int lm_state, lm_cursor, lm_stake, lm_n, lm_timer;
    u8 lm_types[LOOM_PICK_MAX];
    u8 lm_reel[2];
    WeaveResult lm_res;
} fz;

/* ---------------- particles ---------------- */

typedef struct {
    s32 x, y, vx, vy;       /* 8.8 fixed point */
    s16 life, tx, ty;       /* seek target (tx < 0: ballistic) */
    u8 kind, bank, set, grav, prio, active;
} FzPart;

#define FZ_PARTS 40
static FzPart fzp[FZ_PARTS];

static void fzp_clear(void)
{
    for (int i = 0; i < FZ_PARTS; i++) fzp[i].active = 0;
}

static FzPart *fzp_spawn(int x, int y, int vx, int vy, int life, int kind, int ramp_slot)
{
    for (int i = 0; i < FZ_PARTS; i++) {
        FzPart *p = &fzp[i];
        if (p->active) continue;
        p->x = x << 8;
        p->y = y << 8;
        p->vx = vx;
        p->vy = vy;
        p->life = (s16)life;
        p->tx = p->ty = -1;
        p->kind = (u8)kind;
        p->bank = (u8)(OBANK_FZ_PART + (ramp_slot >> 1));
        p->set = (u8)(ramp_slot & 1);
        p->grav = 0;
        p->prio = 0;
        p->active = 1;
        return p;
    }
    return 0;
}

static void fzp_update(void)
{
    for (int i = 0; i < FZ_PARTS; i++) {
        FzPart *p = &fzp[i];
        if (!p->active) continue;
        if (p->tx >= 0) {
            /* seek: steer toward the target, arrive and vanish */
            int dx = (p->tx << 8) - p->x, dy = (p->ty << 8) - p->y;
            p->vx = (p->vx * 3 + dx / 8) / 4;
            p->vy = (p->vy * 3 + dy / 8) / 4;
            if (absi(dx) < 0x600 && absi(dy) < 0x600) p->life = 0;
        }
        p->vy += p->grav;
        p->x += p->vx;
        p->y += p->vy;
        if (--p->life <= 0) p->active = 0;
    }
}

static void fzp_draw(void)
{
    for (int i = 0; i < FZ_PARTS; i++) {
        const FzPart *p = &fzp[i];
        if (!p->active) continue;
        int kind = p->kind;
        if (p->life < 8 && kind > FZP_DOT) kind--;   /* shrink as it dies */
        spr_push((p->x >> 8) - 4, (p->y >> 8) - 4, OT_FZ_PART(p->set, kind), SQ8, p->bank, p->prio, 0);
    }
}

/* Particle ramps: slot 0..3 = OBJ bank 2 (A, B) and 3 (A, B). */
static void fz_ramp_load(int slot, int type)
{
    static const u16 GOLD[4] = { 0x7FFF, 0x4B9F, 0x229B, 0x0D8F };
    const u16 *r = type >= 0 && type < TYPE_COUNT ? fz_type_ramp[type] : GOLD;
    u16 *pal = obj_palette + (OBANK_FZ_PART + (slot >> 1)) * 16 + 1 + (slot & 1) * 4;
    for (int i = 0; i < 4; i++) pal[i] = r[i];
    obj_palette[(OBANK_FZ_PART + (slot >> 1)) * 16] = 0;
}

/* ---------------- drawing helpers ---------------- */

static void fz_load_objects(void)
{
    copy32(VRAM_OBJ_TILES + OT_FZ_GLYPH(0) * 8, fz_glyph_gfx, TYPE_COUNT * 4 * 8);
    for (int s = 0; s < 2; s++)
        for (int k = 0; k < FZP_COUNT * 8; k++) VRAM_OBJ_TILES[OT_FZ_PART(s, 0) * 8 + k] = fz_particle_gfx[s][k / 8][k % 8];
    copy32(VRAM_OBJ_TILES + OT_FZ_CORNER * 8, fz_corner_gfx, 8);
    for (int b = 0; b < 3; b++) load_pal(obj_palette + (OBANK_FZ_GLYPH + b) * 16, fz_glyph_pal[b]);
    for (int b = 0; b < 3; b++) load_pal(bg_palette + b * 16, fz_glyph_pal[b]);
    fz_ramp_load(3, FZ_GOLD);
}

/* A machine scene over the whole canvas (BG banks 3..7). */
static void fz_scene_cells(int cx, int cy, int cw, int ch)
{
    const u32 *tiles = fz_scene_tiles[fz.scene];
    const u16 *map = fz_scene_map[fz.scene];
    for (int y = cy; y < cy + ch; y++)
        for (int x = cx; x < cx + cw; x++) {
            if ((unsigned)x >= CANVAS_COLS || (unsigned)y >= CANVAS_ROWS) continue;
            u16 e = map[y * CANVAS_COLS + x];
            canvas_tile(x, y, tiles + (e & 0x3FF) * 8, 0);
            canvas_set_banks(x, y, 1, 1, e >> 12);
        }
}

static void fz_scene_begin(int scene)
{
    fz.scene = scene;
    canvas_clear();
    REG_DISPCNT = DCNT_MODE0 | DCNT_BG1 | DCNT_OBJ | DCNT_OBJ_1D;
    for (int b = 0; b < 5; b++) load_pal(bg_palette + (3 + b) * 16, fz_scene_pal[scene][b]);
    fz_load_objects();
    bg_palette[0] = RGB15(3, 3, 7);   /* seen through the dome and the reel windows */
    fz_scene_cells(0, 0, CANVAS_COLS, CANVAS_ROWS);
}

/* White text with an ink shadow, straight onto scene art. */
static int fz_text_light(int x, int y, const char *s)
{
    return text_draw_col(x, y, s, 1, 2);
}

static void fz_glyph_bg(int cx, int cy, int type)
{
    canvas_image(cx, cy, 2, 2, fz_glyph_gfx[type], 1, type / 6);
}

static void fz_glyph_spr(int x, int y, int type, int prio)
{
    spr_push(x, y, OT_FZ_GLYPH(type), SQ16, OBANK_FZ_GLYPH + type / 6, prio, 0);
}

/* Cursor corners around a pixel rectangle; they breathe in and out. */
static void fz_corners(int x0, int y0, int x1, int y1)
{
    int b = (fz.frame >> 3) & 1;
    spr_push(x0 - 3 - b, y0 - 3 - b, OT_FZ_CORNER, SQ8, OBANK_FZ_GLYPH, 0, 0);
    spr_push(x1 - 5 + b, y0 - 3 - b, OT_FZ_CORNER, SQ8, OBANK_FZ_GLYPH, 0, ATTR1_HFLIP);
    spr_push(x0 - 3 - b, y1 - 5 + b, OT_FZ_CORNER, SQ8, OBANK_FZ_GLYPH, 0, ATTR1_VFLIP);
    spr_push(x1 - 5 + b, y1 - 5 + b, OT_FZ_CORNER, SQ8, OBANK_FZ_GLYPH, 0, ATTR1_HFLIP | ATTR1_VFLIP);
}

static void fz_amount_text(char *buf, int n, int type)
{
    buf[0] = 0;
    str_put(buf, "+");
    str_put_int(buf, n);
    str_put(buf, " ");
    str_put(buf, TYPE_NAMES[type]);
}

/* ---------------- screen switching ---------------- */

static void fz_update(void);
static void fz_draw(void);
static void fz_redraw(void);

static void fz_goto(int screen)
{
    fz.screen = screen;
    fz.redraw = 1;
    fzp_clear();
    set_brightness(0);
    REG_MOSAIC = 0;
}

static void fz_exit(void)
{
    fzp_clear();
    REG_MOSAIC = 0;
    dialog_clear();
    field_return();
}

/* B on a machine: back to the hall, or out. */
static void fz_back(void)
{
    sfx_play(SFX_CANCEL);
    if (fz.via_works && fz.screen != FZS_WORKS) fz_goto(FZS_WORKS);
    else fz_exit();
}

static void fz_start(int screen, int via_works)
{
    dialog_clear();
    fz.via_works = via_works;
    fz.frame = 0;
    ext_open(fz_update, fz_draw, 0);
    fz_goto(screen);
}

/* ================================================================ */
/*  WORKS: the machine hall                                         */
/* ================================================================ */

typedef struct { u8 x0, y0, x1, y1, screen; const char *name, *desc; } WorksMachine;
static const WorksMachine WORKS_MACHINES[4] = {
    { 7, 40, 54, 110, FZS_UNBIND, "EXTRACTOR", "Unbind a kin into typed energy." },
    { 65, 22, 136, 110, FZS_LOOM, "FUSION LOOM", "Weave energies into a fusion kin." },
    { 133, 22, 175, 45, FZS_MIX, "MIXER", "Mix two energies into a third one." },
    { 136, 48, 171, 110, FZS_ENERGY, "ENERGY TANKS", "Check the energy in your flask." },
};

static void works_redraw(void)
{
    fz_scene_begin(FZ_SCENE_WORKS);
    fz_ramp_load(2, T_ASTRAL);
    canvas_window(0, 14, CANVAS_COLS, 6, WIN_STD);
    const WorksMachine *m = &WORKS_MACHINES[fz.works_cursor];
    text_draw_col(16, 120, m->name, INK_BLUE, INK_BLUE_SH);
    text_draw_right(224, 120, "A: use  B: leave");
    text_draw(16, 136, m->desc);
    fz_text_light(6, 2, "RESONANCE WORKS");
}

static void works_update(void)
{
    int old = fz.works_cursor;
    if (key_rep(KEY_LEFT)) fz.works_cursor = (fz.works_cursor + 3) % 4;
    if (key_rep(KEY_RIGHT)) fz.works_cursor = (fz.works_cursor + 1) % 4;
    if (key_rep(KEY_UP) && fz.works_cursor == 3) fz.works_cursor = 2;
    if (key_rep(KEY_DOWN) && fz.works_cursor == 2) fz.works_cursor = 3;
    if (old != fz.works_cursor) {
        sfx_play(SFX_CURSOR);
        fz.redraw = 1;
    }
    if (key_hit(KEY_B)) {
        fz_back();
        return;
    }
    if (key_hit(KEY_A)) {
        sfx_play(SFX_CONFIRM);
        fz_goto(WORKS_MACHINES[fz.works_cursor].screen);
    }
}

static void works_draw(void)
{
    const WorksMachine *m = &WORKS_MACHINES[fz.works_cursor];
    fz_corners(m->x0, m->y0, m->x1, m->y1);
    /* motes drifting up from the Loom */
    if ((fz.frame & 7) == 0) {
        int t = (fz.frame >> 3) % 2;
        fzp_spawn(FZ_WORKS_LOOM_X - 10 + (int)rng_range(20), FZ_WORKS_LOOM_Y + (int)rng_range(12),
                  (int)rng_range(64) - 32, -80 - (int)rng_range(60), 50, FZP_SOFT, 2 + t);
    }
    fzp_update();
    fzp_draw();
}

/* ================================================================ */
/*  UNBIND: the extractor                                           */
/* ================================================================ */

#define UB_ANIM_LEN 120

static int fz_level_rows(int amount)
{
    return amount <= 0 ? 0 : 2 + 76 * amount / (amount + 300);
}

/* The flask with rows_a of liquid A under rows_b of B (EXTRACT bank 7). */
static void ub_flask_draw(int rows_a, int rows_b)
{
    fz_scene_cells(19, 3, 8, 11);
    rows_a = clampi(rows_a, 0, FZ_FLASK_ROWS);
    rows_b = clampi(rows_b, 0, FZ_FLASK_ROWS - rows_a);
    for (int r = 0; r < FZ_FLASK_ROWS; r++) {
        int k = FZ_FLASK_ROWS - 1 - r;   /* 0 = the bottom row */
        if (k >= rows_a + rows_b) continue;
        int base = k < rows_a ? 10 : 13;
        int x0 = fz_flask_span[r][0], x1 = fz_flask_span[r][1], y = FZ_FLASK_Y0 + r;
        int surface = k == rows_a + rows_b - 1 || k == rows_a - 1;
        canvas_fill(x0, y, x1 - x0 + 1, 1, base + 1);
        canvas_fill(x0, y, 2, 1, base);
        canvas_fill(x1 - 2, y, 3, 1, base + 2);
        if (surface) canvas_fill(x0, y, x1 - x0 + 1, 1, base);
    }
}

static void ub_liquid_colors(int ta, int tb)
{
    u16 *pal = bg_palette + 7 * 16;
    for (int i = 0; i < 3; i++) {
        pal[10 + i] = fz_type_ramp[ta][1 + i];
        pal[13 + i] = fz_type_ramp[tb < TYPE_COUNT ? tb : ta][1 + i];
    }
}

static int ub_count(void)
{
    return party_count + storage_count;
}

static void ub_load_portrait(void)
{
    if (fz.ub_state == UB_ANIM) {
        load_monster_gfx_ex(0, fz.ub_species, 0, fz.ub_lustrous);
        return;
    }
    if (!ub_count()) return;
    Monster m = fusion_list_get(fz.ub_cursor);
    load_monster_gfx_ex(0, m.species, 0, (m.flags & MF_LUSTROUS) != 0);
}

static void ub_redraw(void)
{
    char buf[64];
    fz_scene_begin(FZ_SCENE_EXTRACT);
    fz_text_light(6, 3, "EXTRACTOR");
    fz_text_light(120, 3, "</>: kin  A: unbind");
    canvas_window(0, 14, CANVAS_COLS, 6, WIN_STD);
    int n = ub_count();
    if (fz.ub_cursor >= n) fz.ub_cursor = n > 0 ? n - 1 : 0;
    if (fz.ub_state == UB_ANIM) {
        ub_liquid_colors(fz.ub_type[0], fz.ub_ntypes > 1 ? fz.ub_type[1] : fz.ub_type[0]);
        ub_flask_draw(fz_level_rows(fz.ub_before[0]), 0);
        str_copy(buf, SPECIES[fz.ub_species].name);
        str_put(buf, " is coming unbound...");
        text_draw(16, 120, buf);
        ub_load_portrait();
        return;
    }
    if (!n) {
        text_draw(16, 120, "You have no kin to unbind.");
        return;
    }
    Monster m = fusion_list_get(fz.ub_cursor);
    const Species *s = &SPECIES[m.species];
    u8 type[2];
    u16 amt[2];
    int k = fusion_unbind_yield(&m, type, amt);
    ub_liquid_colors(type[0], k > 1 ? type[1] : type[0]);
    int la = fz_level_rows(fusion.energy[type[0]]);
    int lb = k > 1 ? fz_level_rows(fusion.energy[type[0]] + fusion.energy[type[1]]) - la : 0;
    ub_flask_draw(la, lb);
    str_copy(buf, s->name);
    if (m.flags & MF_LUSTROUS) str_put(buf, "*");
    str_put(buf, "  Lv");
    str_put_int(buf, m.level);
    text_draw_col(16, 120, buf, INK_BLUE, INK_BLUE_SH);
    str_copy(buf, fz.ub_cursor < party_count ? "TEAM " : "SHELF ");
    str_put_int(buf, fz.ub_cursor + 1);
    str_put(buf, "/");
    str_put_int(buf, n);
    text_draw_right(224, 120, buf);
    buf[0] = 0;
    for (int i = 0; i < k; i++) {
        char part[24];
        fz_amount_text(part, amt[i], type[i]);
        if (i) str_put(buf, "  ");
        str_put(buf, part);
    }
    text_draw(16, 136, buf);
    if (s->rarity == R_LEGEND) text_draw_col(176, 136, "LEGEND", INK_RED, INK_RED_SH);
    else if (s->rarity == R_FUSION) text_draw_col(176, 136, "FUSION", INK_GREEN, INK_GREEN_SH);
    ub_load_portrait();
}

static void ub_begin_anim(int i)
{
    Monster m;
    u8 type[2] = { 0, 0 };
    u16 amt[2] = { 0, 0 };
    Monster before = fusion_list_get(i);
    u8 bt[2];
    u16 ba[2];
    int bn = fusion_unbind_yield(&before, bt, ba);
    fz.ub_before[0] = fusion.energy[bt[0]];
    fz.ub_before[1] = bn > 1 ? fusion.energy[bt[1]] : 0;
    int n = fusion_unbind(i, &m, type, amt);
    if (!n) return;
    fz.ub_ntypes = n;
    fz.ub_type[0] = type[0];
    fz.ub_type[1] = n > 1 ? type[1] : type[0];
    fz.ub_amt[0] = amt[0];
    fz.ub_amt[1] = n > 1 ? amt[1] : 0;
    fz.ub_species = m.species;
    fz.ub_lustrous = (m.flags & MF_LUSTROUS) != 0;
    fz.ub_state = UB_ANIM;
    fz.ub_timer = 0;
    fz_ramp_load(0, fz.ub_type[0]);
    fz_ramp_load(1, fz.ub_type[1]);
    sfx_play(SFX_DRAIN);
    fz.redraw = 1;
}

static void ub_finish(void)
{
    char msg[160];
    fz.ub_state = UB_PICK;
    REG_MOSAIC = 0;
    fzp_clear();
    str_copy(msg, SPECIES[fz.ub_species].name);
    str_put(msg, "'s kernel came unbound: ");
    for (int i = 0; i < fz.ub_ntypes; i++) {
        char part[24];
        fz_amount_text(part, fz.ub_amt[i], fz.ub_type[i]);
        if (i) str_put(msg, " and ");
        str_put(msg, part);
    }
    str_put(msg, " flowed into the flask.");
    dlg_say(msg);
    const char *home = SPECIES[fz.ub_species].rarity == R_FUSION ? 0 : fusion_home_wild(fz.ub_species);
    str_copy(msg, "Its body, free of the kernel's pull, ");
    if (SPECIES[fz.ub_species].rarity == R_FUSION) {
        str_put(msg, "scattered into bright motes. Woven kin have no wild to go home to.");
    } else if (home) {
        str_put(msg, "drifted home to the wild at ");
        str_put(msg, home);
        str_put(msg, ", where a new kernel will kindle.");
    } else {
        str_put(msg, "drifted home to the wild, where a new kernel will kindle.");
    }
    dlg_say(msg);
    lore_story(LORE_UNBINDING);
    fz.redraw = 1;
}

static void ub_confirm_final(int c)
{
    if (c != 0) return;
    ub_begin_anim(fz.ub_cursor);
}

static void ub_confirm(int c)
{
    if (c != 0) return;
    Monster m = fusion_list_get(fz.ub_cursor);
    const Species *s = &SPECIES[m.species];
    if (s->rarity == R_LEGEND || (m.flags & MF_LUSTROUS)) {
        char msg[128];
        str_copy(msg, s->name);
        str_put(msg, s->rarity == R_LEGEND ? " is a legend. There will never be another like it. Really unbind it?"
                                           : " is lustrous, a rare colour you may never see again. Really unbind it?");
        dlg_ask(msg, YES_NO, 2, ub_confirm_final);
        return;
    }
    ub_begin_anim(fz.ub_cursor);
}

static void ub_update(void)
{
    if (fz.ub_state == UB_ANIM) {
        fz.ub_timer++;
        int t = fz.ub_timer;
        /* the kernel shakes loose: mosaic grows over the portrait */
        int mos = clampi((t - 10) / 6, 0, 15);
        REG_MOSAIC = (u16)((mos << 8) | (mos << 12));
        /* motes stream from the dome up the pipe and into the flask */
        if (t >= 12 && t < UB_ANIM_LEN - 30 && (t & 1)) {
            int slot = fz.ub_ntypes > 1 && (t & 2) ? 1 : 0;
            FzPart *p = fzp_spawn(FZ_DOME_CX - 16 + (int)rng_range(32), FZ_DOME_CY - 12 + (int)rng_range(28),
                                  (int)rng_range(256) - 128, -256 - (int)rng_range(128), 90,
                                  (t & 4) ? FZP_ORB : FZP_SOFT, slot);
            if (p) {
                p->tx = FZ_FLASK_MOUTH_X;
                p->ty = FZ_FLASK_MOUTH_Y + 24;
            }
        }
        /* the flask fills */
        if ((t & 3) == 0) {
            int f = clampi((t - 20) * 256 / (UB_ANIM_LEN - 40), 0, 256);
            int a = fz.ub_before[0] + fz.ub_amt[0] * f / 256;
            int b = fz.ub_ntypes > 1 && fz.ub_type[1] != fz.ub_type[0] ? fz.ub_before[1] + fz.ub_amt[1] * f / 256 : 0;
            int la = fz_level_rows(a);
            ub_flask_draw(la, b ? fz_level_rows(a + b) - la : 0);
        }
        if (t == 40) sfx_play(SFX_SPARKLE);
        fzp_update();
        if (t >= UB_ANIM_LEN) ub_finish();
        return;
    }
    int n = ub_count();
    int old = fz.ub_cursor;
    if (n) {
        if (key_rep(KEY_LEFT)) fz.ub_cursor = (fz.ub_cursor + n - 1) % n;
        if (key_rep(KEY_RIGHT)) fz.ub_cursor = (fz.ub_cursor + 1) % n;
        if (key_rep(KEY_L)) fz.ub_cursor = clampi(fz.ub_cursor - 10, 0, n - 1);
        if (key_rep(KEY_R)) fz.ub_cursor = clampi(fz.ub_cursor + 10, 0, n - 1);
    }
    if (old != fz.ub_cursor) {
        sfx_play(SFX_CURSOR);
        fz.redraw = 1;
    }
    if (key_hit(KEY_B)) {
        fz_back();
        return;
    }
    if (key_hit(KEY_A) && n) {
        const char *why = fusion_unbind_blocked(fz.ub_cursor);
        if (why) {
            sfx_play(SFX_ERROR);
            dlg_say(why);
            return;
        }
        sfx_play(SFX_CONFIRM);
        Monster m = fusion_list_get(fz.ub_cursor);
        u8 type[2];
        u16 amt[2];
        int k = fusion_unbind_yield(&m, type, amt);
        char msg[160];
        str_copy(msg, "Unbind ");
        str_put(msg, SPECIES[m.species].name);
        str_put(msg, "? Its kernel becomes ");
        for (int i = 0; i < k; i++) {
            char part[24];
            fz_amount_text(part, amt[i], type[i]);
            if (i) str_put(msg, " and ");
            str_put(msg, part + 1);
        }
        str_put(msg, " energy, and it leaves you for good.");
        dlg_ask(msg, YES_NO, 2, ub_confirm);
    }
}

static void ub_draw(void)
{
    int show = fz.ub_state == UB_ANIM ? fz.ub_timer < UB_ANIM_LEN - 36 && (fz.ub_timer < 70 || (fz.ub_timer & 2))
                                      : ub_count() > 0;
    if (show)
        spr_push(FZ_DOME_CX - 32, FZ_DOME_CY - 32, OT_MON_A, SQ64, OBANK_MON_A, 1,
                 fz.ub_state == UB_ANIM ? SPR_MOSAIC : 0);
    fzp_draw();
}

/* ================================================================ */
/*  ENERGY: the 18 pools                                            */
/* ================================================================ */

static void en_cell(int t, int *cx, int *cy)
{
    *cx = 1 + (t % 3) * 9;
    *cy = 1 + (t / 3) * 2;
}

static void en_redraw(void)
{
    char buf[80];
    screen_begin(0);
    fz_load_objects();
    canvas_window(0, 0, CANVAS_COLS, 14, WIN_STD);
    for (int t = 0; t < TYPE_COUNT; t++) {
        int cx, cy;
        en_cell(t, &cx, &cy);
        fz_glyph_bg(cx, cy, t);
        text_draw(cx * 8 + 19, cy * 8 + 1, TYPE_NAMES[t]);
        buf[0] = 0;
        str_put_int(buf, fusion.energy[t]);
        small_text_draw(cx * 8 + 69 - small_text_width(buf), cy * 8 + 5, buf);
    }
    canvas_window(0, 14, CANVAS_COLS, 6, WIN_STD);
    int t = fz.en_cursor;
    str_copy(buf, "MADE BY: ");
    int any = 0;
    for (int r = 0; r < MIX_COUNT; r++) {
        if (MIX_RECIPES[r].out != t) continue;
        if (any++) str_put(buf, ", ");
        str_put(buf, TYPE_NAMES[MIX_RECIPES[r].a]);
        str_put(buf, "+");
        str_put(buf, TYPE_NAMES[MIX_RECIPES[r].b]);
    }
    if (!any) str_put(buf, "unbinding only");
    text_draw_fit(12, 120, buf, 216);
    str_copy(buf, "WEAVES WITH: ");
    any = 0;
    for (int sp = 0; sp < SP_COUNT; sp++) {
        const Species *s = &SPECIES[sp];
        if (s->rarity != R_FUSION || (s->fusion[0] != t && s->fusion[1] != t)) continue;
        if (str_len(buf) > 26) {
            str_put(buf, " ...");
            break;
        }
        if (any++) str_put(buf, " ");
        str_put(buf, TYPE_NAMES[s->fusion[0] == t ? s->fusion[1] : s->fusion[0]]);
    }
    if (!any) str_put(buf, "nothing");
    text_draw_fit(12, 136, buf, 216);
}

static void en_update(void)
{
    int old = fz.en_cursor;
    if (key_rep(KEY_LEFT)) fz.en_cursor = (fz.en_cursor + TYPE_COUNT - 1) % TYPE_COUNT;
    if (key_rep(KEY_RIGHT)) fz.en_cursor = (fz.en_cursor + 1) % TYPE_COUNT;
    if (key_rep(KEY_UP)) fz.en_cursor = (fz.en_cursor + TYPE_COUNT - 3) % TYPE_COUNT;
    if (key_rep(KEY_DOWN)) fz.en_cursor = (fz.en_cursor + 3) % TYPE_COUNT;
    if (old != fz.en_cursor) {
        sfx_play(SFX_CURSOR);
        fz.redraw = 1;
    }
    if (key_hit(KEY_B) || key_hit(KEY_A)) fz_back();
}

static void en_draw(void)
{
    int cx, cy;
    en_cell(fz.en_cursor, &cx, &cy);
    fz_corners(cx * 8 - 2, cy * 8 - 1, cx * 8 + 72, cy * 8 + 17);
}

/* ================================================================ */
/*  TUNE: the tuning minigame (also for crafting's STATION_TUNE)     */
/* ================================================================ */

#define TN_TIME 600              /* frames */
#define TN_FREQS 13              /* 1.00 .. 4.00 cycles across the scope */
#define TN_PHASES 32
#define TN_AMP 22

static int tn_wave_y(int x, int f, int p)
{
    int ang = x * (4 + f) * 256 / (FZ_CRT_W * 4) + p * (256 / TN_PHASES);
    return FZ_CRT_Y + FZ_CRT_H / 2 - fz_sin[ang & 255] * TN_AMP / 256;
}

/* How well your wave matches the target, 0..100. */
static int tn_match(int ft, int pt, int f, int p)
{
    int sum = 0, n = 0;
    for (int x = 0; x < FZ_CRT_W; x += 4, n++) sum += absi(tn_wave_y(x, ft, pt) - tn_wave_y(x, f, p));
    int mean100 = sum * 100 / n;   /* mean distance x100 */
    return clampi(100 - mean100 / 30, 0, 100);
}

static int tn_yield(int match)
{
    return TUNE_YIELD_MIN + clampi(match, 0, 100) * (TUNE_YIELD_MAX - TUNE_YIELD_MIN) / 100;
}

static void tn_draw_scope(void)
{
    canvas_fill(FZ_CRT_X, FZ_CRT_Y, FZ_CRT_W, FZ_CRT_H, 3);
    for (int x = 0; x < FZ_CRT_W; x += 21) canvas_fill(FZ_CRT_X + x, FZ_CRT_Y, 1, FZ_CRT_H, 4);
    for (int y = 0; y < FZ_CRT_H; y += 16) canvas_fill(FZ_CRT_X, FZ_CRT_Y + y, FZ_CRT_W, 1, 4);
    canvas_fill(FZ_CRT_X, FZ_CRT_Y + FZ_CRT_H / 2, FZ_CRT_W, 1, 5);
    for (int pass = 0; pass < 2; pass++) {
        int f = pass ? fz.tn_f : fz.tn_ft, p = pass ? fz.tn_p : fz.tn_pt;
        int core = pass ? 8 : 6, glow = pass ? 9 : 7;
        int prev = tn_wave_y(0, f, p);
        for (int x = 0; x < FZ_CRT_W; x++) {
            int y = tn_wave_y(x, f, p);
            int lo = y < prev ? y : prev, hi = y < prev ? prev : y;
            canvas_fill(FZ_CRT_X + x, lo - 1, 1, hi - lo + 3, glow);
            canvas_fill(FZ_CRT_X + x, lo, 1, hi - lo + 1, core);
            prev = y;
        }
    }
}

static void tn_draw_meter(void)
{
    int h = (FZ_METER_H - 4) * fz.tn_shown_match / 100;
    canvas_fill(FZ_METER_X + 2, FZ_METER_Y + 2, FZ_METER_W - 4, FZ_METER_H - 4, 10);
    canvas_fill(FZ_METER_X + 2, FZ_METER_Y + FZ_METER_H - 2 - h, FZ_METER_W - 4, h, 11);
    if (h > 0) canvas_fill(FZ_METER_X + 3, FZ_METER_Y + FZ_METER_H - 2 - h, 2, h, 12);
    int w = FZ_TIMER_W * (TN_TIME - fz.tn_timer) / TN_TIME;
    canvas_fill(FZ_TIMER_X, FZ_TIMER_Y, FZ_TIMER_W, FZ_TIMER_H, 10);
    canvas_fill(FZ_TIMER_X, FZ_TIMER_Y, w, FZ_TIMER_H, 11);
}

static void tn_draw_text(void)
{
    char buf[40];
    canvas_window(0, 16, CANVAS_COLS, 4, WIN_STD);
    str_copy(buf, "YIELD ");
    str_put_int(buf, tn_yield(fz.tn_match));
    str_put(buf, "%");
    text_draw_col(16, 136, buf, INK_BLUE, INK_BLUE_SH);
    text_draw_right(224, 136, "</> pitch  ^v phase  A lock");
}

static void tn_redraw(void)
{
    fz_scene_begin(FZ_SCENE_TUNER);
    fz_ramp_load(0, T_TIDE);
    fz_text_light(6, 2, fz.tn_title ? fz.tn_title : "TUNING");
    tn_draw_scope();
    tn_draw_meter();
    tn_draw_text();
}

/* Opens the tuner; done(yield) runs when it locks (A or time). */
static void fusion_tuner_open(const char *title, void (*done)(int yield))
{
    int inside = game_mode == MODE_EXT && ext.update == fz_update;
    if (!inside) fz_start(FZS_TUNE, 0);
    fz.tn_return = inside ? fz.screen : -1;
    fz.tn_title = title;
    fz.tn_done = done;
    fz.tn_ft = (int)rng_range(TN_FREQS);
    fz.tn_pt = (int)rng_range(TN_PHASES);
    do {
        fz.tn_f = (int)rng_range(TN_FREQS);
    } while (absi(fz.tn_f - fz.tn_ft) < 3);
    fz.tn_p = (fz.tn_pt + TN_PHASES / 2) % TN_PHASES;
    fz.tn_timer = 0;
    fz.tn_locked = 0;
    fz.tn_match = fz.tn_shown_match = tn_match(fz.tn_ft, fz.tn_pt, fz.tn_f, fz.tn_p);
    fz_goto(FZS_TUNE);
}

static void tn_lock(void)
{
    fz.tn_locked = 1;
    int y = tn_yield(fz.tn_match);
    sfx_play(fz.tn_match >= 90 ? SFX_PERFECT : SFX_CONFIRM);
    if (fz.tn_return < 0) fz_exit();   /* opened on its own (crafting): back to the field */
    else fz_goto(fz.tn_return);
    if (fz.tn_done) fz.tn_done(y);
}

static void tn_update(void)
{
    int old_f = fz.tn_f, old_p = fz.tn_p;
    if (key_rep(KEY_LEFT) && fz.tn_f > 0) fz.tn_f--;
    if (key_rep(KEY_RIGHT) && fz.tn_f < TN_FREQS - 1) fz.tn_f++;
    if (key_rep(KEY_UP)) fz.tn_p = (fz.tn_p + 1) % TN_PHASES;
    if (key_rep(KEY_DOWN)) fz.tn_p = (fz.tn_p + TN_PHASES - 1) % TN_PHASES;
    int changed = old_f != fz.tn_f || old_p != fz.tn_p;
    if (changed) {
        sfx_play(SFX_CURSOR);
        fz.tn_match = tn_match(fz.tn_ft, fz.tn_pt, fz.tn_f, fz.tn_p);
        tn_draw_scope();
        tn_draw_text();
    }
    /* the meter eases toward the match */
    if (fz.tn_shown_match != fz.tn_match) {
        int d = fz.tn_match - fz.tn_shown_match;
        fz.tn_shown_match += d / 4 ? d / 4 : (d > 0 ? 1 : -1);
    }
    fz.tn_timer++;
    if ((fz.tn_timer & 3) == 0 || changed) tn_draw_meter();
    if (key_hit(KEY_A) || fz.tn_timer >= TN_TIME) tn_lock();
    else if (key_hit(KEY_B) && fz.tn_timer > 30) tn_lock();
}

static void tn_draw(void)
{
    /* knob pointers */
    for (int k = 0; k < 2; k++) {
        int v = k ? fz.tn_p * 256 / TN_PHASES : 160 + fz.tn_f * 192 / TN_FREQS;
        int x = fz_knob[k][0] + fz_sin[(v + 64) & 255] * 7 / 256;
        int y = fz_knob[k][1] + fz_sin[v & 255] * 7 / 256;
        spr_push(x - 4, y - 4, OT_FZ_PART(0, FZP_ORB), SQ8, OBANK_FZ_PART, 0, 0);
    }
}

/* ================================================================ */
/*  MIX: the recipe list                                            */
/* ================================================================ */

#define MX_ROWS 6

static void mx_redraw(void)
{
    char buf[48];
    screen_begin(0);
    fz_load_objects();
    canvas_window(0, 0, CANVAS_COLS, 3, WIN_STD);
    text_draw_col(16, 8, "MIXER", INK_BLUE, INK_BLUE_SH);
    text_draw_right(224, 8, "A: mix   B: back");
    canvas_window(0, 3, CANVAS_COLS, 14, WIN_STD);
    for (int i = 0; i < MX_ROWS && fz.mx_scroll + i < MIX_COUNT; i++) {
        int r = fz.mx_scroll + i;
        const MixRecipe *m = &MIX_RECIPES[r];
        int cy = 4 + i * 2, y = cy * 8 + 1;
        fz_glyph_bg(2, cy, m->a);
        text_draw(34, y, "+");
        fz_glyph_bg(5, cy, m->b);
        text_draw(58, y, "=");
        fz_glyph_bg(8, cy, m->out);
        text_draw(88, y, m->name);
        buf[0] = 0;
        str_put_int(buf, fusion.energy[m->a]);
        str_put(buf, "/");
        str_put_int(buf, fusion.energy[m->b]);
        if (fusion_mix_max(r) >= MIX_STEP) text_draw_right(228, y, buf);
        else text_draw_col(228 - text_width(buf), y, buf, INK_RED, INK_RED_SH);
    }
    canvas_window(0, 17, CANVAS_COLS, 3, WIN_STD);
    const MixRecipe *m = &MIX_RECIPES[fz.mx_cursor];
    if (fz.mx_state == MX_AMOUNT) {
        str_copy(buf, "MIX < ");
        str_put_int(buf, fz.mx_amount);
        str_put(buf, " > OF EACH  ->  ");
        str_put_int(buf, fusion_mix_output(fz.mx_amount, 100));
        str_put(buf, " ");
        str_put(buf, TYPE_NAMES[m->out]);
        text_draw(16, 144, buf);
    } else {
        str_copy(buf, TYPE_NAMES[m->a]);
        str_put(buf, " + ");
        str_put(buf, TYPE_NAMES[m->b]);
        str_put(buf, " = ");
        str_put(buf, TYPE_NAMES[m->out]);
        str_put(buf, "  (you have ");
        str_put_int(buf, fusion.energy[m->out]);
        str_put(buf, ")");
        text_draw_fit(16, 144, buf, 208);
    }
}

static void mx_done(int yield)
{
    char msg[160];
    const MixRecipe *m = &MIX_RECIPES[fz.mx_cursor];
    int n = fz.mx_amount;
    int first = !(fusion.flags & FZF_MIXED);
    int made = fusion_mix(fz.mx_cursor, n, yield);
    str_copy(msg, "The resonance settled at ");
    str_put_int(msg, yield);
    str_put(msg, "%! ");
    str_put_int(msg, n);
    str_put(msg, " ");
    str_put(msg, TYPE_NAMES[m->a]);
    str_put(msg, " and ");
    str_put_int(msg, n);
    str_put(msg, " ");
    str_put(msg, TYPE_NAMES[m->b]);
    str_put(msg, " became ");
    str_put_int(msg, made);
    str_put(msg, " ");
    str_put(msg, TYPE_NAMES[m->out]);
    str_put(msg, " (");
    str_put(msg, m->name);
    str_put(msg, ").");
    sfx_play(SFX_SPARKLE);
    dlg_say(msg);
    if (first) lore_story(LORE_MIX_TABLE);
    fz.mx_state = MX_LIST;
}

static void mx_update(void)
{
    if (fz.mx_state == MX_AMOUNT) {
        int max = fusion_mix_max(fz.mx_cursor), old = fz.mx_amount;
        if (key_rep(KEY_LEFT)) fz.mx_amount -= MIX_STEP;
        if (key_rep(KEY_RIGHT)) fz.mx_amount += MIX_STEP;
        if (key_rep(KEY_L) || key_rep(KEY_DOWN)) fz.mx_amount -= MIX_STEP * 10;
        if (key_rep(KEY_R) || key_rep(KEY_UP)) fz.mx_amount += MIX_STEP * 10;
        fz.mx_amount = clampi(fz.mx_amount, MIX_STEP, max);
        if (old != fz.mx_amount) {
            sfx_play(SFX_CURSOR);
            fz.redraw = 1;
        }
        if (key_hit(KEY_B)) {
            sfx_play(SFX_CANCEL);
            fz.mx_state = MX_LIST;
            fz.redraw = 1;
        } else if (key_hit(KEY_A)) {
            sfx_play(SFX_CONFIRM);
            static char title[40];
            const MixRecipe *m = &MIX_RECIPES[fz.mx_cursor];
            str_copy(title, TYPE_NAMES[m->a]);
            str_put(title, " + ");
            str_put(title, TYPE_NAMES[m->b]);
            str_put(title, " = ");
            str_put(title, TYPE_NAMES[m->out]);
            fusion_tuner_open(title, mx_done);
        }
        return;
    }
    int old = fz.mx_cursor;
    if (key_rep(KEY_UP)) fz.mx_cursor = (fz.mx_cursor + MIX_COUNT - 1) % MIX_COUNT;
    if (key_rep(KEY_DOWN)) fz.mx_cursor = (fz.mx_cursor + 1) % MIX_COUNT;
    if (key_rep(KEY_L) || key_rep(KEY_LEFT)) fz.mx_cursor = clampi(fz.mx_cursor - MX_ROWS, 0, MIX_COUNT - 1);
    if (key_rep(KEY_R) || key_rep(KEY_RIGHT)) fz.mx_cursor = clampi(fz.mx_cursor + MX_ROWS, 0, MIX_COUNT - 1);
    if (fz.mx_cursor < fz.mx_scroll) fz.mx_scroll = fz.mx_cursor;
    if (fz.mx_cursor >= fz.mx_scroll + MX_ROWS) fz.mx_scroll = fz.mx_cursor - MX_ROWS + 1;
    if (old != fz.mx_cursor) {
        sfx_play(SFX_CURSOR);
        fz.redraw = 1;
    }
    if (key_hit(KEY_B)) {
        fz_back();
        return;
    }
    if (key_hit(KEY_A)) {
        const MixRecipe *m = &MIX_RECIPES[fz.mx_cursor];
        if (fusion_mix_max(fz.mx_cursor) < MIX_STEP) {
            char msg[96];
            sfx_play(SFX_ERROR);
            str_copy(msg, "You need at least 10 ");
            str_put(msg, TYPE_NAMES[m->a]);
            str_put(msg, " and 10 ");
            str_put(msg, TYPE_NAMES[m->b]);
            str_put(msg, " energy for that.");
            dlg_say(msg);
            return;
        }
        sfx_play(SFX_CONFIRM);
        fz.mx_state = MX_AMOUNT;
        fz.mx_amount = clampi(fusion_mix_max(fz.mx_cursor) / 2 / MIX_STEP * MIX_STEP, MIX_STEP, 9999);
        fz.redraw = 1;
    }
}

static void mx_draw(void)
{
    int row = fz.mx_cursor - fz.mx_scroll;
    int y = (4 + row * 2) * 8;
    fz_corners(12, y - 1, 228, y + 17);
}

/* ================================================================ */
/*  LOOM: weaving                                                   */
/* ================================================================ */

#define LM_STRIP_Y 112
#define LM_STRIP_X 12
#define LM_STRIP_N 9
#define LM_PITCH 24
#define LM_SPIN_LEN 200
#define LM_REEL1_STOP 110
#define LM_REEL2_STOP 140
#define LM_REVEAL 160

static int lm_scroll(void)
{
    return clampi(fz.lm_cursor - LM_STRIP_N / 2, 0, TYPE_COUNT - LM_STRIP_N);
}

static int lm_picked(int t)
{
    return loom_has(fz.lm_types, fz.lm_n, t);
}

static void lm_redraw(void)
{
    char buf[64];
    fz_scene_begin(FZ_SCENE_LOOM);
    for (int i = 0; i < 3; i++) fz_ramp_load(i, i < fz.lm_n ? fz.lm_types[i] : T_ASTRAL);
    fz_text_light(6, 3, "FUSION LOOM");
    str_copy(buf, "WEAVES ");
    str_put_int(buf, fusion.weaves);
    fz_text_light(174, 3, buf);
    /* candidates on the left wall */
    u8 cand[LOOM_CAND_MAX];
    int c = fusion_loom_candidates(fz.lm_types, fz.lm_n, cand);
    fz_text_light(6, 22, c ? "MAY WEAVE:" : fz.lm_n < 2 ? "PICK 2 OR 3" : "NO FUSION");
    if (!c && fz.lm_n < 2) fz_text_light(6, 36, "ENERGIES");
    for (int i = 0; i < c && i < 4; i++) {
        str_copy(buf, dex_caught[cand[i]] ? "" : "NEW ");
        str_put(buf, SPECIES[cand[i]].name);
        fz_text_light(6, 36 + i * 14, buf);
    }
    /* pity on the right wall */
    str_copy(buf, "MISSES ");
    str_put_int(buf, fusion.pity);
    str_put(buf, "/");
    str_put_int(buf, FZ_PITY_CAP);
    fz_text_light(166, 22, buf);
    canvas_window(0, 13, CANVAS_COLS, 7, WIN_STD);
    for (int i = 0; i < LM_STRIP_N; i++) {
        int t = lm_scroll() + i;
        buf[0] = 0;
        str_put_int(buf, fusion.energy[t]);
        small_text_draw(LM_STRIP_X + i * LM_PITCH + 8 - small_text_width(buf) / 2, LM_STRIP_Y + 19, buf);
    }
    int chance = fusion_loom_chance(fz.lm_types, fz.lm_n, fz.lm_stake);
    str_copy(buf, "STAKE ");
    str_put_int(buf, STAKE_UNITS[fz.lm_stake]);
    str_put(buf, " (L/R)   CHANCE ");
    str_put_int(buf, fz.lm_n >= 2 && c ? chance : 0);
    str_put(buf, "%");
    text_draw(12, 140, buf);
    text_draw_right(228, 140, "START");
    if (lm_scroll() > 0) text_draw(3, LM_STRIP_Y + 2, "<");
    if (lm_scroll() < TYPE_COUNT - LM_STRIP_N) text_draw(232, LM_STRIP_Y + 2, ">");
}

static const char *lm_block_text(int why)
{
    switch (why) {
    case LOOM_TOO_FEW: return "Pick two or three energies to weave with (A).";
    case LOOM_NO_CANDIDATE: return "No fusion kin answers to those energies. Try another pair.";
    case LOOM_LOW_ENERGY: return "You don't have enough of each energy for that stake.";
    case LOOM_NO_ROOM: return "Your team and the Shelf are full. Make room first!";
    default: return 0;
    }
}

static void lm_after(void)
{
    char msg[160];
    WeaveResult *r = &fz.lm_res;
    if (r->hit) {
        str_copy(msg, "A ");
        str_put(msg, SPECIES[r->species].name);
        str_put(msg, " was woven from the resonance!");
        dlg_say(msg);
        str_copy(msg, SPECIES[r->species].name);
        str_put(msg, r->where == 0 ? " joined your team." : " was sent to the LANTERN SHELF.");
        dlg_say(msg);
        lore_story(LORE_WOVEN_KIN);
    } else {
        str_copy(msg, "The weave came apart... The motes settled as ");
        str_put_int(msg, r->dust);
        str_put(msg, " MOTE DUST, and ");
        str_put_int(msg, r->refund);
        str_put(msg, " of each energy flowed back.");
        dlg_say(msg);
        str_copy(msg, "The Loom hums a little warmer. Next weave: ");
        str_put_int(msg, fusion_loom_chance(fz.lm_types, fz.lm_n, fz.lm_stake));
        str_put(msg, "%.");
        dlg_say(msg);
    }
    lore_story(LORE_LOOM_ODDS);
    /* drop picks you can no longer afford */
    int k = 0;
    for (int i = 0; i < fz.lm_n; i++)
        if (fusion.energy[fz.lm_types[i]] > 0) fz.lm_types[k++] = fz.lm_types[i];
    fz.lm_n = k;
    fz.lm_state = LM_PICK;
    set_brightness(0);
    fzp_clear();
    fz.redraw = 1;
}

static void lm_start_weave(void)
{
    int why = fusion_loom_check(fz.lm_types, fz.lm_n, fz.lm_stake);
    if (why != LOOM_OK) {
        sfx_play(SFX_ERROR);
        dlg_say(lm_block_text(why));
        return;
    }
    fusion_weave(fz.lm_types, fz.lm_n, fz.lm_stake, &fz.lm_res);
    for (int i = 0; i < 3; i++) fz_ramp_load(i, fz.lm_types[i < fz.lm_n ? i : 0]);
    if (fz.lm_res.hit) {
        const Species *s = &SPECIES[fz.lm_res.species];
        fz.lm_reel[0] = s->fusion[0];
        fz.lm_reel[1] = s->fusion[1];
        load_monster_gfx_ex(0, fz.lm_res.species, 0, (fz.lm_res.mon.flags & MF_LUSTROUS) != 0);
    } else {
        /* the reels land on a pair that doesn't weave */
        fz.lm_reel[0] = fz.lm_types[rng_range((unsigned)fz.lm_n)];
        for (int tries = 0; tries < 40; tries++) {
            int t = (int)rng_range(TYPE_COUNT);
            u8 pair[2] = { fz.lm_reel[0], (u8)t };
            u8 cand[LOOM_CAND_MAX];
            fz.lm_reel[1] = (u8)t;
            if (t != fz.lm_reel[0] && !fusion_loom_candidates(pair, 2, cand)) break;
        }
    }
    fz.lm_state = LM_SPIN;
    fz.lm_timer = 0;
    fzp_clear();
    sfx_play(SFX_CHARGE);
    fz.redraw = 1;
}

static void lm_update(void)
{
    if (fz.lm_state == LM_SPIN) {
        int t = ++fz.lm_timer;
        if (t == LM_REEL1_STOP || t == LM_REEL2_STOP) sfx_play(SFX_BUMP);
        if (fz.lm_res.hit) {
            if (t == LM_REEL2_STOP + 4) sfx_play(SFX_SPARKLE);
            if (t > LM_REEL2_STOP && t <= LM_REVEAL) set_brightness((t - LM_REEL2_STOP) * 16 / (LM_REVEAL - LM_REEL2_STOP));
            if (t > LM_REVEAL) set_brightness(clampi(16 - (t - LM_REVEAL), 0, 16));
            if (t == LM_REVEAL) {
                sfx_play(SFX_BEFRIEND);
                for (int i = 0; i < 24; i++) {
                    int a = (int)rng_range(256);
                    int sp = 256 + (int)rng_range(384);
                    FzPart *p = fzp_spawn(FZ_LOOM_X, FZ_LOOM_Y, fz_sin[(a + 64) & 255] * sp / 256,
                                          fz_sin[a & 255] * sp / 256 - 256, 50 + (int)rng_range(30),
                                          i & 1 ? FZP_STAR : FZP_ORB, i % 4);
                    if (p) p->grav = 12;
                }
            }
        } else if (t == LM_REEL2_STOP + 6) {
            sfx_play(SFX_MISS);
            for (int i = 0; i < 16; i++) {
                int a = (int)rng_range(256);
                FzPart *p = fzp_spawn(FZ_LOOM_X + fz_sin[(a + 64) & 255] * FZ_LOOM_RING_R / 256,
                                      FZ_LOOM_Y + fz_sin[a & 255] * FZ_LOOM_RING_R / 256,
                                      (int)rng_range(128) - 64, 0, 40 + (int)rng_range(30), FZP_SOFT, i % 3);
                if (p) p->grav = 10;
            }
        }
        fzp_update();
        if (t >= LM_SPIN_LEN) lm_after();
        return;
    }
    int old = fz.lm_cursor, old_stake = fz.lm_stake, old_n = fz.lm_n;
    if (key_rep(KEY_LEFT) && fz.lm_cursor > 0) fz.lm_cursor--;
    if (key_rep(KEY_RIGHT) && fz.lm_cursor < TYPE_COUNT - 1) fz.lm_cursor++;
    if (key_hit(KEY_L)) fz.lm_stake = (fz.lm_stake + STAKE_COUNT - 1) % STAKE_COUNT;
    if (key_hit(KEY_R)) fz.lm_stake = (fz.lm_stake + 1) % STAKE_COUNT;
    if (key_hit(KEY_A)) {
        int t = fz.lm_cursor;
        if (lm_picked(t)) {
            int k = 0;
            for (int i = 0; i < fz.lm_n; i++)
                if (fz.lm_types[i] != t) fz.lm_types[k++] = fz.lm_types[i];
            fz.lm_n = k;
            sfx_play(SFX_CANCEL);
        } else if (fz.lm_n >= LOOM_PICK_MAX) {
            sfx_play(SFX_ERROR);
        } else if (!fusion.energy[t]) {
            sfx_play(SFX_ERROR);
        } else {
            fz.lm_types[fz.lm_n++] = (u8)t;
            sfx_play(SFX_CONFIRM);
        }
    }
    if (old != fz.lm_cursor || old_stake != fz.lm_stake) sfx_play(SFX_CURSOR);
    if (old != fz.lm_cursor || old_stake != fz.lm_stake || old_n != fz.lm_n) fz.redraw = 1;
    if (key_hit(KEY_START) || key_hit(KEY_SELECT)) {
        lm_start_weave();
        return;
    }
    if (key_hit(KEY_B)) {
        if (fz.lm_n) {
            fz.lm_n--;
            sfx_play(SFX_CANCEL);
            fz.redraw = 1;
            return;
        }
        fz_back();
    }
}

static void lm_draw(void)
{
    int spin = fz.lm_state == LM_SPIN, t = fz.lm_timer;
    /* the sockets */
    for (int i = 0; i < fz.lm_n; i++) {
        int pulse = spin && ((t >> 2) & 1) && t < LM_REEL2_STOP;
        fz_glyph_spr(fz_loom_socket[i][0] - 8, fz_loom_socket[i][1] - 8 - pulse, fz.lm_types[i], 0);
    }
    if (!dialog_active()) {
        int sc = lm_scroll();
        for (int i = 0; i < LM_STRIP_N; i++) {
            int ty = sc + i;
            int x = LM_STRIP_X + i * LM_PITCH, y = LM_STRIP_Y - (lm_picked(ty) ? 3 : 0);
            fz_glyph_spr(x, y, ty, 0);
            if (lm_picked(ty)) spr_push(x + 4, LM_STRIP_Y + 13, OT_FZ_PART(1, FZP_DOT), SQ8, OBANK_FZ_PART + 1, 0, 0);
        }
        int x = LM_STRIP_X + (fz.lm_cursor - sc) * LM_PITCH;
        if (!spin) fz_corners(x - 1, LM_STRIP_Y - 4, x + 17, LM_STRIP_Y + 27);
    }
    if (!spin) {
        if (dialog_active()) return;
        /* a lazy orbit while you choose */
        for (int i = 0; i < fz.lm_n * 2; i++) {
            int a = fz.frame * 2 + i * 256 / (fz.lm_n * 2);
            int x2 = FZ_LOOM_X + fz_sin[(a + 64) & 255] * FZ_LOOM_RING_R / 256;
            int y2 = FZ_LOOM_Y + fz_sin[a & 255] * FZ_LOOM_RING_R / 256;
            int slot = i % fz.lm_n;
            spr_push(x2 - 4, y2 - 4, OT_FZ_PART(slot & 1, FZP_SOFT), SQ8, OBANK_FZ_PART + (slot >> 1), 0, 0);
        }
        return;
    }
    /* the ring spins up */
    if (t < LM_REEL2_STOP + 10) {
        int speed = clampi(t / 8, 1, 12);
        int n = 12;
        for (int i = 0; i < n; i++) {
            int a = t * speed + i * 256 / n;
            int r = FZ_LOOM_RING_R - (t > LM_REEL2_STOP ? (t - LM_REEL2_STOP) * 3 : 0);
            int x = FZ_LOOM_X + fz_sin[(a + 64) & 255] * r / 256;
            int y = FZ_LOOM_Y + fz_sin[a & 255] * r / 256;
            int slot = i % (fz.lm_n > 0 ? fz.lm_n : 1);
            spr_push(x - 4, y - 4, OT_FZ_PART(slot & 1, i & 1 ? FZP_ORB : FZP_SOFT), SQ8,
                     OBANK_FZ_PART + (slot >> 1), 0, 0);
        }
    }
    /* the reels (behind the canvas: they show through the windows) */
    for (int k = 0; k < 2; k++) {
        int stop = k ? LM_REEL2_STOP : LM_REEL1_STOP;
        int rx = fz_loom_reel[k][0] + 2, ry = fz_loom_reel[k][1] + 2;
        if (t >= stop) {
            fz_glyph_spr(rx, ry, fz.lm_reel[k], 1);
            continue;
        }
        int off = (t * (6 - k)) % 20;
        int ty = (t * (6 - k) / 20 + k * 5) % TYPE_COUNT;
        fz_glyph_spr(rx, ry - 20 + off, ty, 1);
        fz_glyph_spr(rx, ry + off, (ty + 1) % TYPE_COUNT, 1);
    }
    /* the new kin */
    if (fz.lm_res.hit && t >= LM_REVEAL) {
        int s = clampi((t - LM_REVEAL) * 24, 16, 256);
        int aff = oam_affine_scale_rot(s, s, 0);
        spr_push_affine(FZ_LOOM_X - 32, FZ_LOOM_Y - 26, OT_MON_A, SQ64, OBANK_MON_A, 0, 0, aff, 1);
    }
    fzp_draw();
}

/* ================================================================ */
/*  The ext screen                                                  */
/* ================================================================ */

static void fz_redraw(void)
{
    switch (fz.screen) {
    case FZS_WORKS: works_redraw(); break;
    case FZS_UNBIND: ub_redraw(); break;
    case FZS_ENERGY: en_redraw(); break;
    case FZS_MIX: mx_redraw(); break;
    case FZS_TUNE: tn_redraw(); break;
    case FZS_LOOM: lm_redraw(); break;
    default: break;
    }
}

static void fz_update(void)
{
    fz.frame++;
    if (dialog_active()) {
        dialog_update();
        if (game_mode != MODE_EXT || ext.update != fz_update) return;
        if (!dialog_active()) fz.redraw = 1;
        return;
    }
    if (fz.redraw) {
        fz.redraw = 0;
        fz_redraw();
    }
    switch (fz.screen) {
    case FZS_WORKS: works_update(); break;
    case FZS_UNBIND: ub_update(); break;
    case FZS_ENERGY: en_update(); break;
    case FZS_MIX: mx_update(); break;
    case FZS_TUNE: tn_update(); break;
    case FZS_LOOM: lm_update(); break;
    default: break;
    }
}

static void fz_draw(void)
{
    if (fz.redraw) return;
    switch (fz.screen) {
    case FZS_WORKS: works_draw(); break;
    case FZS_UNBIND: ub_draw(); break;
    case FZS_ENERGY: en_draw(); break;
    case FZS_MIX: mx_draw(); break;
    case FZS_TUNE: tn_draw(); break;
    case FZS_LOOM: lm_draw(); break;
    default: break;
    }
}

/* The RESONANCE WORKS machines (SCR_FUSION_DESK and the machines call this). */
static void fusion_open(int screen)
{
    static const u8 TO[] = { FZS_WORKS, FZS_UNBIND, FZS_MIX, FZS_LOOM, FZS_ENERGY };
    int s = screen >= 0 && screen < (int)sizeof(TO) ? TO[screen] : FZS_WORKS;
    fz.ub_state = UB_PICK;
    fz.mx_state = MX_LIST;
    fz.lm_state = LM_PICK;
    fz_start(s, 1);
}

/* KEY item ENERGY FLASK: the energy screen. */
static int fusion_key_use(int key)
{
    (void)key;
    fz_start(FZS_ENERGY, 0);
    return 1;
}

/* Examining the machines in the Works (script.c examine_cell). */
static int fusion_examine(int decor_kind)
{
    int screen;
    switch (decor_kind) {
    case DK_FZ_EXTRACTOR: screen = FUSION_SCREEN_UNBIND; break;
    case DK_FZ_MIXER: screen = FUSION_SCREEN_MIX; break;
    case DK_FZ_LOOM: screen = FUSION_SCREEN_LOOM; break;
    case DK_FZ_TANKS: screen = FUSION_SCREEN_ENERGY; break;
    default: return 0;
    }
    if (!(fusion.flags & FZF_INTRO)) {
        dlg_say("The machine hums, but its controls are locked. Ask at the front desk.");
        return 1;
    }
    fusion_open(screen);
    return 1;
}
