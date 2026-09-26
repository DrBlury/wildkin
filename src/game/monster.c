/*
 * Creature rules: stats, experience, learnsets, evolution, damage and
 * catching. Pure functions over Monster structs; the battle engine and
 * the host tests share them.
 */

#define MAX_MOVES 4
#define MAX_LEVEL 100
#define KIN_NAME_LEN 10   /* nickname length (uppercase, digits, a few symbols) */

typedef struct {
    u8 species, level, status, sleep_turns;
    u8 moves[MAX_MOVES];
    u8 pp[MAX_MOVES];   /* remaining uses */
    u16 hp, max_hp;
    u16 stat[5];        /* ATK DEF FOCUS WILL SPE */
    u32 xp;             /* total experience points */
    u8 pot[6];          /* potential 0..31: HP ATK DEF FOCUS WILL SPE */
    u8 temper, trait;   /* TEMPERAMENTS index, TR_* */
    u8 size;            /* 0..255, 128 = average */
    u8 flags;           /* MF_* */
    u8 bond;            /* 0..255 */
    u8 met_map, met_level;
    char name[KIN_NAME_LEN + 1];   /* nickname, 0-terminated; "" = the species name */
} Monster;

enum { MF_LUSTROUS = 1 };
#define MET_NOWHERE 0xFF
#define POT_MAX 31
#define BOND_START 70
#define LUSTROUS_ODDS 128

/* What the player calls this kin: its nickname, or else its species name
 * (so a kin without a nickname shows its new name after evolving). */
static const char *kin_name(const Monster *m)
{
    return m->name[0] ? m->name : SPECIES[m->species].name;
}

/* Characters a nickname may hold. */
static int kin_name_char_ok(char c)
{
    return (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == ' ' || c == '-' || c == '.' ||
           c == '\'' || c == '!' || c == '?' || c == '&' || c == '+' || c == '/';
}

/* Set a nickname (clipped to KIN_NAME_LEN; bad characters dropped, the
 * spaces around it trimmed). A name equal to the species name, or an empty
 * one, clears the nickname. */
static void kin_set_name(Monster *m, const char *src)
{
    int n = 0;
    for (int i = 0; src && src[i] && n < KIN_NAME_LEN; i++)
        if (kin_name_char_ok(src[i]) && !(n == 0 && src[i] == ' ')) m->name[n++] = src[i];
    while (n > 0 && m->name[n - 1] == ' ') n--;
    for (int i = n; i <= KIN_NAME_LEN; i++) m->name[i] = 0;
    if (str_eq(m->name, SPECIES[m->species].name)) m->name[0] = 0;
}

static int calc_hp_stat(int base, int pot, int level)
{
    return (2 * base + pot) * level / 100 + level + 10;
}

static int calc_other_stat(int base, int pot, int level, int temper, int stat)
{
    int v = (2 * base + pot) * level / 100 + 5;
    const Temperament *t = &TEMPERAMENTS[temper % TEMPERAMENT_COUNT];
    if (t->up == stat) v = v * 110 / 100;
    else if (t->down == stat) v = v * 90 / 100;
    return v;
}

/* Potential grade shown in the summary. */
static const char *potential_grade(int pot)
{
    if (pot >= 31) return "PERFECT";
    if (pot >= 28) return "STELLAR";
    if (pot >= 20) return "GREAT";
    if (pot >= 10) return "DECENT";
    return "DUD";
}

static const char *size_name(int size)
{
    if (size < 24) return "TINY";
    if (size < 88) return "SMALL";
    if (size < 168) return "AVERAGE";
    if (size < 232) return "LARGE";
    return "HUGE";
}

/* Height/weight scaled by size: 0 -> 70%, 128 -> 100%, 255 -> 130%. */
static int size_scale(int value, int size)
{
    return value * (700 + size * 600 / 255) / 1000;
}

/* Total experience needed to reach `level` ("fast" growth curve). */
static u32 xp_for_level(int level)
{
    if (level <= 1) return 0;
    u32 l = (u32)level;
    return l * l * l * 4 / 5;
}

static void monster_recalc(Monster *m)
{
    const Species *s = &SPECIES[m->species];
    int old_max = m->max_hp;
    m->max_hp = (u16)calc_hp_stat(s->base[BS_HP], m->pot[0], m->level);
    for (int i = 0; i < 5; i++)
        m->stat[i] = (u16)calc_other_stat(s->base[BS_ATK + i], m->pot[1 + i], m->level,
                                          m->temper, i);
    /* Missing HP stays the same when max HP grows (fainted stays fainted). */
    if (m->hp > 0 || old_max == 0) {
        int hp = m->hp + (m->max_hp - old_max);
        m->hp = (u16)clampi(hp, 1, m->max_hp);
    }
}

static int monster_move_count(const Monster *m)
{
    int n = 0;
    for (int i = 0; i < MAX_MOVES; i++)
        if (m->moves[i] != MOVE_NONE) n++;
    return n;
}

static int monster_knows(const Monster *m, int move)
{
    for (int i = 0; i < MAX_MOVES; i++)
        if (m->moves[i] == move) return 1;
    return 0;
}

/* Put a move into the first free slot; returns 0 when all four are taken. */
static int monster_add_move(Monster *m, int move)
{
    if (monster_knows(m, move)) return 1;
    for (int i = 0; i < MAX_MOVES; i++)
        if (m->moves[i] == MOVE_NONE) {
            m->moves[i] = (u8)move;
            m->pp[i] = MOVES[move].pp;
            return 1;
        }
    return 0;
}

static void monster_replace_move(Monster *m, int slot, int move)
{
    m->moves[slot] = (u8)move;
    m->pp[slot] = MOVES[move].pp;
}

static Monster monster_make(int species, int level)
{
    Monster m;
    for (unsigned i = 0; i < sizeof(m); i++) ((u8 *)&m)[i] = 0;
    m.species = (u8)species;
    m.level = (u8)clampi(level, 1, MAX_LEVEL);
    for (int i = 0; i < MAX_MOVES; i++) m.moves[i] = MOVE_NONE;
    /* Wild creatures know the four most recent moves for their level. */
    const LearnEntry *ls = SPECIES[species].learnset;
    int count = 0;
    while (ls[count].level) count++;
    int known[MAX_MOVES], n = 0;
    for (int i = count - 1; i >= 0 && n < MAX_MOVES; i--) {
        if (ls[i].level > m.level) continue;
        int dup = 0;
        for (int j = 0; j < n; j++)
            if (known[j] == ls[i].move) dup = 1;
        if (!dup) known[n++] = ls[i].move;
    }
    for (int i = n - 1; i >= 0; i--) monster_add_move(&m, known[i]);
    m.xp = xp_for_level(m.level);
    /* individuality: potential, temperament, trait, size, lustre */
    for (int i = 0; i < 6; i++) m.pot[i] = (u8)rng_range(POT_MAX + 1);
    m.temper = (u8)rng_range(TEMPERAMENT_COUNT);
    m.trait = SPECIES[species].traits[rng_range(2)];
    m.size = (u8)((rng_range(128) + rng_range(129)));
    m.flags = rng_range(LUSTROUS_ODDS) == 0 ? MF_LUSTROUS : 0;
    m.bond = BOND_START;
    m.met_map = MET_NOWHERE;
    m.met_level = m.level;
    m.hp = 0;
    m.max_hp = 0;
    monster_recalc(&m);
    m.hp = m.max_hp;
    return m;
}

static void monster_heal_full(Monster *m)
{
    m->hp = m->max_hp;
    m->status = STATUS_NONE;
    m->sleep_turns = 0;
    for (int i = 0; i < MAX_MOVES; i++)
        if (m->moves[i] != MOVE_NONE) m->pp[i] = MOVES[m->moves[i]].pp;
}

/* Moves a species learns at exactly `level` (up to 4), returns the count. */
static int learnset_at(int species, int level, u8 *out)
{
    int n = 0;
    for (const LearnEntry *e = SPECIES[species].learnset; e->level && n < 4; e++)
        if (e->level == level && level > 1) out[n++] = e->move;
    return n;
}

/* Raise the level by one; returns 1 if the level actually changed. */
static int monster_level_up(Monster *m)
{
    if (m->level >= MAX_LEVEL) return 0;
    m->level++;
    if (m->xp < xp_for_level(m->level)) m->xp = xp_for_level(m->level);
    monster_recalc(m);
    return 1;
}

/* Target species if this creature should evolve now by level, else -1. */
static int monster_level_evolution(const Monster *m)
{
    const Species *s = &SPECIES[m->species];
    if (s->evo_kind == EVO_LEVEL && m->level >= s->evo_param && m->hp > 0)
        return s->evo_into;
    return -1;
}

static int monster_item_evolution(const Monster *m, int item)
{
    const Species *s = &SPECIES[m->species];
    if (s->evo_kind == EVO_ITEM && s->evo_param == item)
        return s->evo_into;
    return -1;
}

static void monster_evolve(Monster *m, int into)
{
    m->species = (u8)into;
    monster_recalc(m);
}

static int monster_xp_yield(const Monster *foe, int trainer)
{
    int xp = SPECIES[foe->species].xp_yield * foe->level / 5;
    if (trainer) xp = xp * 3 / 2;
    return xp < 1 ? 1 : xp;
}

/* ---------------- battle math ---------------- */

static int type_effectiveness(int move_type, int species)
{
    const Species *s = &SPECIES[species];
    return type_mult(move_type, s->type1) * type_mult(move_type, s->type2) / 100;
}

static int species_has_type(int species, int type)
{
    return SPECIES[species].type1 == type || SPECIES[species].type2 == type;
}

/* Stat stage multiplier applied to `v`: +1 = x1.5, -1 = x0.67, ... */
static int apply_stage(int v, int stage)
{
    if (stage >= 0) return v * (2 + stage) / 2;
    return v * 2 / (2 - stage);
}

static int apply_acc_stage(int acc, int stage)
{
    if (stage >= 0) return acc * (3 + stage) / 3;
    return acc * 3 / (3 - stage);
}

/* Effective battle stat: stages and status penalties included. */
static int battle_stat(const Monster *m, const s8 *stages, int stat)
{
    int v = apply_stage(m->stat[stat], stages ? stages[stat] : 0);
    if (stat == STAT_SPE && m->status == STATUS_NUMB) v /= 4;
    return v < 1 ? 1 : v;
}

/* A move's power in this matchup (some effects scale it). */
static int move_power(int move, const Monster *att, const Monster *def)
{
    const Move *mv = &MOVES[move];
    int p = mv->power;
    switch (mv->effect) {
    case EF_PUNISH:
        if (def && def->status != STATUS_NONE) p *= 2;
        break;
    case EF_DESPERATE:
        if (att->max_hp) p += p * 3 * (att->max_hp - att->hp) / att->max_hp;
        break;
    case EF_BRIM:
        if (att->max_hp) p = p * att->hp / att->max_hp;
        if (p < 10) p = 10;
        break;
    }
    return p;
}

/*
 * Effectiveness of `move` used by `att` on `def` in percent, traits
 * included: a DRIFTER floats clear of STONE moves.
 */
static int move_effectiveness(int move, const Monster *att, const Monster *def)
{
    (void)att;
    if (move == M_LAST_GASP) return 100;
    if (def->trait == TR_DRIFTER && MOVES[move].type == T_STONE) return 0;
    return type_effectiveness(MOVES[move].type, def->species);
}

/* SURGE: moves of its own type hit harder at 1/3 HP or less. */
static int trait_surging(const Monster *att, int move)
{
    return att->trait == TR_SURGE && att->hp * 3 <= att->max_hp && move != M_LAST_GASP &&
           species_has_type(att->species, MOVES[move].type);
}

typedef struct {
    int damage;
    int effectiveness; /* percent: 0, 25, 50, 100, 200, 400 */
    int crit;
    int att_trait;     /* the attacker's trait strengthened this hit */
    int def_trait;     /* the defender's trait softened it */
} DamageResult;

/*
 * Gen-3 style damage: physical/special by category, STAB x1.5, type chart,
 * critical hits x2 (ignoring the attacker's negative and the defender's
 * positive stages), random 85..100%, burn halves physical damage.
 * Traits: BRUISER / FOCUSED x1.2, SURGE x1.5, THICK FUR halves BLAZE and
 * FROST, BEDROCK takes x0.75 from weak-spot hits, DRIFTER ignores STONE.
 */
static DamageResult calc_damage(const Monster *att, const s8 *att_st,
                                const Monster *def, const s8 *def_st,
                                int move, int crit, int rand_pct)
{
    DamageResult r = { 0, 100, crit, 0, 0 };
    const Move *mv = &MOVES[move];
    int phys = mv->cat == CAT_PHYS;
    int as = phys ? STAT_ATK : STAT_SPA;
    int ds = phys ? STAT_DEF : STAT_SPD;
    s8 a_stage = att_st ? att_st[as] : 0;
    s8 d_stage = def_st ? def_st[ds] : 0;
    if (crit) {
        if (a_stage < 0) a_stage = 0;
        if (d_stage > 0) d_stage = 0;
    }
    int a = apply_stage(att->stat[as], a_stage);
    int d = apply_stage(def->stat[ds], d_stage);
    if (d < 1) d = 1;
    int dmg = (2 * att->level / 5 + 2) * move_power(move, att, def) * a / d / 50;
    if (phys && att->status == STATUS_BRN) dmg /= 2;
    dmg += 2;
    if (crit) dmg *= 2;
    if (move != M_LAST_GASP && species_has_type(att->species, mv->type))
        dmg = dmg * 3 / 2;
    r.effectiveness = move_effectiveness(move, att, def);
    dmg = dmg * r.effectiveness / 100;
    if ((att->trait == TR_BRUISER && phys) || (att->trait == TR_FOCUSED && !phys))
        dmg = dmg * 6 / 5;
    if (trait_surging(att, move)) {
        dmg = dmg * 3 / 2;
        r.att_trait = 1;
    }
    if (def->trait == TR_THICK_FUR && (mv->type == T_BLAZE || mv->type == T_FROST)) {
        dmg /= 2;
        r.def_trait = 1;
    }
    if (def->trait == TR_BEDROCK && r.effectiveness > 100) {
        dmg = dmg * 3 / 4;
        r.def_trait = 1;
    }
    dmg = dmg * rand_pct / 100;
    if (r.effectiveness > 0 && dmg < 1) dmg = 1;
    r.damage = dmg;
    return r;
}

/* Gen-3 catch formula; returns the number of shakes (4 = caught). */
static int catch_shakes(const Monster *m, int capsule_x10)
{
    u32 max = m->max_hp, hp = m->hp;
    u32 a = (3 * max - 2 * hp) * SPECIES[m->species].catch_rate * (u32)capsule_x10 /
            (3 * max) / 10;
    if (m->status == STATUS_SLP || m->status == STATUS_FRZ) a = a * 2;
    else if (m->status != STATUS_NONE) a = a * 3 / 2;
    if (a < 1) a = 1;
    if (a >= 255) return 4;
    /* b = 1048560 / sqrt(sqrt(16711680 / a)), in 12-bit fixed point */
    unsigned long long x = (unsigned long long)(16711680u / a) << 16;
    unsigned long long root2 = isqrt64(x);            /* sqrt(v) * 256 */
    unsigned long long root4 = isqrt64(root2 << 16);  /* v^(1/4) * 4096 */
    u32 b = (u32)(1048560ull * 4096ull / (root4 ? root4 : 1));
    int shakes = 0;
    while (shakes < 4 && (rng_next() & 0xFFFF) < b) shakes++;
    return shakes;
}
