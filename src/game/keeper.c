/*
 * Bout portraits (gfx_keepers.h): the keeper who challenges you and the
 * player seen from behind, with the little sequence that opens a bout.
 *
 *   intro    both slide in while the lantern light opens (the player's
 *            back on the left, the keeper on the enemy pad)
 *   FLAIR    the keeper's signature pose with a hop ("... wants a bout!")
 *   THROW    the keeper raises a lantern, the send-out lantern leaves its
 *            hand and the keeper backs off to the right; the player winds
 *            up, throws and steps off to the left the same way
 *   RETURN   when the bout is decided the keeper walks back in, sheepish
 *            (LOSE) when you won, showing off (FLAIR) when you lost
 *
 * While standing, both breathe and blink now and then (the BREATH frame).
 *
 * A keeper is one of 20 archetypes (KP_*) plus a variation: vary 0 is the
 * archetype's default look, any other value picks skin, hair and outfit
 * colours from its pools. The tiles are shared; only the palette changes
 * (keeper_palette). TrainerTeam.look / .vary choose them.
 *
 * Every warden in TRAINERS has one fixed look (keeper_trainer_look): a Hall
 * Master is a Hall Master, anyone else an archetype of the scene where their
 * NPC stands, picked by name, with a variation from the name too. The same
 * look walks the overworld (keeper_ow_gfx, npc_keeper_look), so the warden
 * you see on the path is the one who steps onto the pad. Ordinary folk of
 * the same kinds (kids, farmers, fishers, grans, hermits...) are drawn from
 * the cast as well; the healer, clerk, professor and scientist keep their
 * own sprites so you can pick them out in any town.
 *
 * VRAM: the field people's OBJ tiles (0..127) and NPC banks 5 and 6 are
 * free in a bout (the field reloads them every frame).
 */

#define OT_PORTRAIT(side)    ((side) == SIDE_ENEMY ? 0 : 64)
#define OBANK_PORTRAIT(side) ((side) == SIDE_ENEMY ? 5 : 6)

#define PORTRAIT_ENTER_LEN 30
#define PORTRAIT_FLAIR_LEN 48
#define PORTRAIT_WINDUP    10   /* player: wind-up frames before the throw */
#define PORTRAIT_THROW_LEN 12   /* frames the throw pose holds before the lantern flies */
#define PORTRAIT_LEAVE_LEN 22
#define PORTRAIT_RETURN_LEN 26

typedef struct {
    u8 on;
    u8 act;
    u8 frame;       /* KF_* for the keeper, HB_* for the player */
    u8 hold;        /* the frame PA_RETURN settles in */
    u8 loaded;      /* frame in VRAM + 1, 0 = reload */
    s16 t;
    s16 x, y;       /* offset from the rest spot */
} Portrait;

static Portrait portrait[2];
static u8 keeper_kind, keeper_vary;
static u8 portrait_uploaded;   /* a frame already went to VRAM this frame */

static u32 keeper_name_hash(const char *s)
{
    u32 h = 2166136261u;
    while (s && *s) {
        h ^= (u8)*s++;
        h *= 16777619u;
    }
    return h;
}

/* The 16 colours of keeper `kind` in variation `vary` (see
 * keeper_variant() in tools/gen_keeper_gfx.py: the same hash). */
static void keeper_palette(u16 *dst, int kind, int vary)
{
    const KeeperLook *k = &KEEPER_LOOK[clampi(kind, 0, KEEPER_COUNT - 1)];
    int skin = k->skin, hair = k->hair, a = k->a, b = k->b;
    if (vary) {
        u32 h = (u32)vary * 2654435761u;
        h ^= h >> 15;
        h *= 2246822519u;
        h ^= h >> 13;
        skin = (int)(h % KP_SKIN_COUNT);
        hair = k->hair_pool[(h >> 4) % k->nhair];
        a = k->a_pool[(h >> 9) % k->na];
        int bi = (int)((h >> 14) % k->nb);
        b = k->b_pool[bi];
        if (b == a && k->nb > 1) b = k->b_pool[(bi + 1) % k->nb];
    }
    for (int i = 0; i < 4; i++) dst[i] = kp_fixed_pal[i];
    for (int i = 0; i < 3; i++) dst[4 + i] = kp_skin_ramp[skin][i];
    for (int i = 0; i < 3; i++) dst[7 + i] = kp_hair_ramp[hair][i];
    dst[10] = kp_cloth_ramp[a][0];
    dst[11] = kp_cloth_ramp[a][1];
    dst[12] = kp_cloth_ramp[b][0];
    dst[13] = kp_cloth_ramp[b][1];
    dst[14] = k->acc[0];
    dst[15] = k->acc[1];
}

/* Who a scene's wardens usually are (BSCENE_* order). */
static const u8 KEEPER_SCENE_POOL[BSCENE_COUNT][6] = {
    { KP_SPROUT, KP_BLOSSOM, KP_FARMER, KP_IDOL, KP_ELDER, KP_COOK },     /* meadow */
    { KP_RANGER, KP_SPROUT, KP_HEXLING, KP_HIKER, KP_BLOSSOM, KP_RANGER }, /* forest */
    { KP_ANGLER, KP_SWIMMER, KP_SPROUT, KP_BLOSSOM, KP_ANGLER, KP_SWIMMER }, /* lake */
    { KP_SENTINEL, KP_SMITH, KP_IDOL, KP_HIKER, KP_TINKER, KP_COOK },     /* ring */
    { KP_MYSTIC, KP_HEXLING, KP_SENTINEL, KP_RANGER, KP_MYSTIC, KP_HEXLING }, /* storm */
    { KP_TINKER, KP_SCHOLAR, KP_IDOL, KP_COOK, KP_SENTINEL, KP_TINKER },  /* city */
    { KP_SAILOR, KP_SWIMMER, KP_ANGLER, KP_COOK, KP_SAILOR, KP_SWIMMER }, /* coast */
    { KP_SAILOR, KP_SWIMMER, KP_ANGLER, KP_SAILOR, KP_SWIMMER, KP_ANGLER }, /* sea */
    { KP_SNOWBELL, KP_HIKER, KP_RANGER, KP_ELDER, KP_SNOWBELL, KP_HIKER }, /* snow */
    { KP_MINER, KP_HIKER, KP_SCHOLAR, KP_MINER, KP_HIKER, KP_MINER },     /* cave */
    { KP_HEXLING, KP_ELDER, KP_SCHOLAR, KP_MYSTIC, KP_HEXLING, KP_ELDER }, /* grim */
    { KP_HEXLING, KP_SCHOLAR, KP_SENTINEL, KP_HEXLING, KP_SCHOLAR, KP_ELDER }, /* crypt */
    { KP_SMITH, KP_MINER, KP_HIKER, KP_SMITH, KP_MINER, KP_TINKER },      /* volcano */
    { KP_MYSTIC, KP_HEXLING, KP_IDOL, KP_SCHOLAR, KP_MYSTIC, KP_BLOSSOM }, /* dream */
    { KP_FARMER, KP_BLOSSOM, KP_COOK, KP_SPROUT, KP_FARMER, KP_ELDER },   /* farm */
    { KP_MASTER, KP_SENTINEL, KP_MASTER, KP_SENTINEL, KP_MASTER, KP_SENTINEL }, /* lair */
};

/* Pick the keeper for a warden bout (after battle.scene is set). */
static void keeper_choose(const TrainerTeam *t, int master)
{
    u32 h = keeper_name_hash(t->name ? t->name : "WARDEN");
    if (t->look) keeper_kind = (u8)clampi(t->look - 1, 0, KEEPER_COUNT - 1);
    else if (master) keeper_kind = KP_MASTER;
    else keeper_kind = KEEPER_SCENE_POOL[clampi(battle.scene, 0, BSCENE_COUNT - 1)][(h >> 3) % 6];
    keeper_vary = t->vary ? t->vary : (u8)(h % 255u + 1u);
}

/* "MASTER FARA" / "HALL MASTER MORWEN" / "WARDEN MARLO" is trainer name `tr`. */
static int keeper_name_is(const char *npc, const char *tr)
{
    if (!npc || !tr) return 0;
    if (str_eq(npc, tr)) return 1;
    for (int k = 0; k < 2; k++) {
        const char *pre = k ? "HALL MASTER " : "MASTER ";
        const char *n = npc;
        while (*pre && *n == *pre) {
            pre++;
            n++;
        }
        if (!*pre && str_eq(n, tr)) return 1;
    }
    return 0;
}

static int keeper_scene_of_map(int map)
{
    return clampi(MAPS[map].scene, 0, BSCENE_COUNT - 1);
}

/* A scene's keeper for hash h (never a Hall Master: only the six are). */
static int keeper_of_scene(int scene, u32 h)
{
    int k = KEEPER_SCENE_POOL[clampi(scene, 0, BSCENE_COUNT - 1)][(h >> 3) % 6];
    return k == KP_MASTER ? KP_SENTINEL : k;
}

/* Warden `tid`'s look, on the map and in the bout. */
static void keeper_trainer_look(int tid, u8 *kind, u8 *vary)
{
    const char *name = TRAINERS[tid].name ? TRAINERS[tid].name : "WARDEN";
    u32 h = keeper_name_hash(name);
    int master = 1;              /* the Hall Masters go by one name: "FARA" */
    for (const char *c = name; *c; c++)
        if (*c == ' ') master = 0;
    if (master) {
        *kind = KP_MASTER;
    } else {
        int scene = BSCENE_MEADOW;
        for (int i = 0; i < NPC_COUNT; i++)
            if (NPCS[i].trainer == tid || keeper_name_is(NPCS[i].name, name)) {
                scene = keeper_scene_of_map(NPCS[i].map);
                break;
            }
        *kind = (u8)keeper_of_scene(scene, h);
    }
    *vary = (u8)(h % 255u + 1u);
}

/* How NPC i looks when drawn from the cast; 0 = it keeps its own sprite. */
static int npc_keeper_look_uncached(int i, u8 *kind, u8 *vary)
{
    const NpcDef *n = &NPCS[i];
    if (n->trainer != NO_TRAINER) {
        keeper_trainer_look(n->trainer, kind, vary);
        return 1;
    }
    if (n->name)
        for (int t = 0; t < TRAINER_COUNT; t++)
            if (keeper_name_is(n->name, TRAINERS[t].name)) {
                keeper_trainer_look(t, kind, vary);
                return 1;
            }
    int scene = keeper_scene_of_map(n->map);
    u32 h = keeper_name_hash(n->name) ^ ((u32)i * 2654435761u);
    h ^= h >> 11;
    int k;
    switch (n->chr) {
    case CHR_KID: k = scene == BSCENE_SNOW ? KP_SNOWBELL : KP_SPROUT; break;
    case CHR_KID_B: k = scene == BSCENE_SNOW ? KP_SNOWBELL : KP_BLOSSOM; break;
    case CHR_FISHER: k = scene == BSCENE_SEA || scene == BSCENE_COAST ? KP_SAILOR : KP_ANGLER; break;
    case CHR_GARDENER: k = KP_FARMER; break;
    case CHR_BAKER: k = KP_COOK; break;
    case CHR_GRAN:
    case CHR_ELDER: k = KP_ELDER; break;
    case CHR_HERMIT: k = KP_MYSTIC; break;
    case CHR_GUIDE: k = KP_RANGER; break;
    case CHR_VILLAGER:
    case CHR_WARDEN_A:
    case CHR_WARDEN_B: k = keeper_of_scene(scene, h); break;
    default: return 0;           /* player, professor, clerk, healer, scientist */
    }
    *kind = (u8)k;
    *vary = (u8)(h % 255u + 1u);
    return 1;
}

static s8 npc_look_kind[NPC_COUNT];   /* KP_* + 1, 0 = not worked out yet, -1 = own sprite */
static u8 npc_look_vary[NPC_COUNT];

static int npc_keeper_look(int i, u8 *kind, u8 *vary)
{
    if (!npc_look_kind[i]) {
        u8 k = 0, v = 0;
        npc_look_kind[i] = npc_keeper_look_uncached(i, &k, &v) ? (s8)(k + 1) : -1;
        npc_look_vary[i] = v;
    }
    if (npc_look_kind[i] < 0) return 0;
    *kind = (u8)(npc_look_kind[i] - 1);
    *vary = npc_look_vary[i];
    return 1;
}

static void portrait_load_palettes(void)
{
    keeper_palette(obj_palette + OBANK_PORTRAIT(SIDE_ENEMY) * 16, keeper_kind, keeper_vary);
    copy16(obj_palette + OBANK_PORTRAIT(SIDE_ALLY) * 16, hero_palette, 16);
    portrait[0].loaded = portrait[1].loaded = 0;
}

static void portrait_reset(void)
{
    for (int s = 0; s < 2; s++) {
        Portrait *p = &portrait[s];
        p->on = 0;
        p->act = PA_NONE;
        p->loaded = 0;
        p->t = 0;
        p->x = p->y = 0;
    }
}

/* the side slides in from off screen (keeper: from the right) */
static int portrait_off_x(int side)
{
    return side == SIDE_ENEMY ? 112 : -112;
}

static void portrait_act(int side, int act, int hold)
{
    Portrait *p = &portrait[side];
    p->act = (u8)act;
    p->t = 0;
    if (act == PA_ENTER || act == PA_RETURN) {
        p->on = 1;
        p->x = (s16)portrait_off_x(side);
    }
    p->hold = (u8)hold;
}

/* Keeper frames and player-back frames line up: 0 idle, 1 breath. */
static void portrait_update_one(int side)
{
    Portrait *p = &portrait[side];
    if (!p->on) return;
    int t = ++p->t;
    int off = portrait_off_x(side);
    int f = 0;
    p->y = 0;
    switch (p->act) {
    case PA_ENTER:
        p->x = (s16)(off - off * ease_out(t, PORTRAIT_ENTER_LEN) / 256);
        if (t >= PORTRAIT_ENTER_LEN) {
            p->x = 0;
            p->act = PA_IDLE;
            p->t = 0;
        }
        break;
    case PA_FLAIR:
        f = side == SIDE_ENEMY ? KF_FLAIR : HB_IDLE;
        if (t < 12) p->y = (s16)(-soft_sin(t * 128 / 12) * 6 / 64);   /* a happy hop */
        if (t >= PORTRAIT_FLAIR_LEN) {
            p->act = PA_IDLE;
            p->t = 0;
        }
        break;
    case PA_THROW:
        if (side == SIDE_ENEMY) {
            f = KF_THROW;
            if (t < 6) p->y = (s16)(-t / 2);
        } else {
            f = t <= PORTRAIT_WINDUP ? HB_WINDUP : HB_THROW;
            if (t > PORTRAIT_WINDUP && t < PORTRAIT_WINDUP + 6) p->y = -2;
        }
        if (t >= (side == SIDE_ENEMY ? PORTRAIT_THROW_LEN : PORTRAIT_WINDUP + PORTRAIT_THROW_LEN)) {
            p->act = PA_LEAVE;
            p->t = 0;
        }
        break;
    case PA_LEAVE:
        f = side == SIDE_ENEMY ? KF_THROW : HB_THROW;
        if (t > 6) f = 0;
        p->x = (s16)(off * ease_in(t, PORTRAIT_LEAVE_LEN) / 256);
        if (t >= PORTRAIT_LEAVE_LEN) {
            p->on = 0;
            p->act = PA_NONE;
        }
        break;
    case PA_RETURN:
        /* a step further back than the pad's centre: the player's HUD is up now */
        p->y = -12;
        p->x = (s16)(off - off * ease_out(t, PORTRAIT_RETURN_LEN) / 256);
        f = t < PORTRAIT_RETURN_LEN ? 0 : p->hold;
        if (t >= PORTRAIT_RETURN_LEN) p->x = 0;
        /* a sheepish bob / a proud bounce */
        if (t >= PORTRAIT_RETURN_LEN && p->hold == KF_FLAIR && ((t - PORTRAIT_RETURN_LEN) % 40) < 10)
            p->y = (s16)(p->y - soft_sin((t - PORTRAIT_RETURN_LEN) % 40 * 128 / 10) * 4 / 64);
        break;
    default: {
        /* standing: breathe in now and then, and blink */
        int period = side == SIDE_ENEMY ? 90 : 76;
        int ph = (int)((frame_count + (unsigned)side * 37) % (unsigned)period);
        if (ph < 8) f = 1;
        break;
    }
    }
    p->frame = (u8)f;
    if (p->loaded != f + 1 && !portrait_uploaded) {
        portrait_uploaded = 1;   /* one 2 KB upload a frame; the other side waits a frame */
        const u32 *src = side == SIDE_ENEMY ? keeper_gfx[keeper_kind][f] : hero_back_gfx[f];
        copy32(VRAM_OBJ_TILES + OT_PORTRAIT(side) * 8, src, 64 * 8);
        p->loaded = (u8)(f + 1);
    }
}

static void portrait_update(void)
{
    portrait_uploaded = 0;
    int first = (int)(frame_count & 1);
    portrait_update_one(first);
    portrait_update_one(first ^ 1);
}

/* the rest spots: where the kin stand */
static int portrait_rest_x(int side) { return side == SIDE_ENEMY ? ENEMY_X : ALLY_X; }
static int portrait_rest_y(int side) { return side == SIDE_ENEMY ? ENEMY_Y + 6 : ALLY_Y; }

static void portrait_draw(void)
{
    for (int side = 0; side < 2; side++) {
        const Portrait *p = &portrait[side];
        if (!p->on || !p->loaded) continue;   /* (a stale frame shows for one frame at most) */
        spr_push(portrait_rest_x(side) + p->x + shake_x, portrait_rest_y(side) + p->y + shake_y,
                 OT_PORTRAIT(side), SQ64, OBANK_PORTRAIT(side), 1, 0);
    }
}

/* Where the send-out lantern leaves from: the raised hand, or off screen. */
static int portrait_hand(int side, int *x, int *y)
{
    const Portrait *p = &portrait[side];
    if (!p->on) return 0;
    *x = portrait_rest_x(side) + p->x + 44;
    *y = portrait_rest_y(side) + p->y + 16;
    return 1;
}

/* Blocking portrait events wait for these. */
static int portrait_ready(int side, int act)
{
    const Portrait *p = &portrait[side];
    if (!p->on) return 1;
    if (act == PA_THROW) return p->act != PA_THROW;
    if (act == PA_RETURN) return p->t >= PORTRAIT_RETURN_LEN + 8;
    return 1;
}
