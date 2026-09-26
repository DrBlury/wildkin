/*
 * Game data: types, moves (moves.h), traits, temperaments, species,
 * learnsets, growth and items.
 *
 * Everything here is plain constant tables so balance and consistency can
 * be checked by the host unit tests (tools/test_game.c). The concepts
 * behind the names are in docs/WORLD.md.
 */

/* ================================================================ */
/*  Types                                                           */
/* ================================================================ */

enum {
    T_BEAST, T_BLAZE, T_TIDE, T_BLOOM, T_SPARK, T_FROST, T_BRAWL,
    T_VENOM, T_STONE, T_GALE, T_DREAM, T_SWARM, T_DUSK, T_WYRM,
    TYPE_COUNT
};
#define TYPE_NONE 0xFF

static const char *const TYPE_NAMES[TYPE_COUNT] = {
    "BEAST", "BLAZE", "TIDE", "BLOOM", "SPARK", "FROST", "BRAWL",
    "VENOM", "STONE", "GALE", "DREAM", "SWARM", "DUSK", "WYRM",
};

/*
 * Attacker rows, defender columns in enum order:
 *   Be Bl Ti Bo Sp Fr Br Ve St Ga Dr Sw Du Wy
 * '+' strikes a weak spot (x2), '-' shrugged off (x0.5), '0' no effect.
 * Physics first: water quenches heat, charge races through water, stone
 * grounds charge, heat melts frost. Light and dark (BLAZE, DUSK) eat each
 * other, and VENOM fouls water.
 */
static const char TYPE_CHART[TYPE_COUNT][TYPE_COUNT + 1] = {
    /* BEAST */ "........-...0.",
    /* BLAZE */ ".--+.+..-..++-",
    /* TIDE  */ ".+--....+....-",
    /* BLOOM */ ".-+-...-+-.-.-",
    /* SPARK */ "..+--...0+...-",
    /* FROST */ ".--+.-..++...+",
    /* BRAWL */ "+....+.-+---+.",
    /* VENOM */ "..++...--...-.",
    /* STONE */ ".+.-++.+...-..",
    /* GALE  */ "...+-.+.-..+..",
    /* DREAM */ "......++..-.-.",
    /* SWARM */ ".-.+..--.-+.+.",
    /* DUSK  */ "0+....-...+.+.",
    /* WYRM  */ ".............+",
};

/* Percent multiplier of one attacking type against one defending type. */
static int type_mult(int atk, int def)
{
    if (def == TYPE_NONE) return 100;
    switch (TYPE_CHART[atk][def]) {
    case '+': return 200;
    case '-': return 50;
    case '0': return 0;
    default: return 100;
    }
}

/* ================================================================ */
/*  Categories, status problems, stats                              */
/* ================================================================ */

enum { CAT_PHYS, CAT_SPEC, CAT_STATUS };

enum { STATUS_NONE, STATUS_BRN, STATUS_PSN, STATUS_NUMB, STATUS_SLP, STATUS_FRZ, STATUS_COUNT };
static const char *const STATUS_NAMES[STATUS_COUNT] = { "", "BRN", "PSN", "NMB", "SLP", "FRZ" };

/* STAT_SPA / STAT_SPD are shown to the player as FOCUS / WILL. */
enum { STAT_ATK, STAT_DEF, STAT_SPA, STAT_SPD, STAT_SPE, STAT_ACC, STAT_COUNT };
static const char *const STAT_NAMES[STAT_COUNT] = {
    "ATTACK", "DEFENSE", "FOCUS", "WILL", "SPEED", "ACCURACY",
};
#define SM(s) (1u << (s))
#define SM_ALL5 (SM(STAT_ATK) | SM(STAT_DEF) | SM(STAT_SPA) | SM(STAT_SPD) | SM(STAT_SPE))

/* ================================================================ */
/*  Moves                                                           */
/* ================================================================ */

#include "moves.h"

/* ================================================================ */
/*  Traits (one per kin, rolled from its species' two options)       */
/* ================================================================ */

enum {
    TR_SURGE, TR_BRUISER, TR_FOCUSED, TR_KEEN_EYE, TR_THICK_FUR, TR_BEDROCK,
    TR_DRIFTER, TR_SOAKER, TR_CONDUCTOR, TR_STATIC_FUR, TR_EMBERSKIN,
    TR_SPORESKIN, TR_WAKEFUL, TR_SELFMEND, TR_BASKER, TR_GLOWER,
    TR_STUBBORN, TR_MOMENTUM, TR_HOARDER, TR_QUICK_STUDY, TR_SLIPPERY,
    TRAIT_COUNT
};

typedef struct { const char *name, *desc; } Trait;

static const Trait TRAITS[TRAIT_COUNT] = {
    [TR_SURGE]       = { "SURGE", "Moves of its own type hit 1.5x harder when its HP is low." },
    [TR_BRUISER]     = { "BRUISER", "Its physical moves hit 1.2x harder." },
    [TR_FOCUSED]     = { "FOCUSED", "Its special moves hit 1.2x harder." },
    [TR_KEEN_EYE]    = { "KEEN EYE", "Lands perfect strikes twice as often." },
    [TR_THICK_FUR]   = { "THICK FUR", "Takes half damage from BLAZE and FROST moves." },
    [TR_BEDROCK]     = { "BEDROCK", "Takes less damage when struck on a weak spot." },
    [TR_DRIFTER]     = { "DRIFTER", "It floats, so STONE moves can't touch it." },
    [TR_SOAKER]      = { "SOAKER", "TIDE moves heal it instead of hurting it." },
    [TR_CONDUCTOR]   = { "CONDUCTOR", "SPARK moves heal it instead of hurting it." },
    [TR_STATIC_FUR]  = { "STATIC FUR", "Foes that touch it may be left numb." },
    [TR_EMBERSKIN]   = { "EMBERSKIN", "Foes that touch it may be burned." },
    [TR_SPORESKIN]   = { "SPORESKIN", "Foes that touch it may be poisoned." },
    [TR_WAKEFUL]     = { "WAKEFUL", "It never falls asleep." },
    [TR_SELFMEND]    = { "SELFMEND", "May shake off a status problem each turn." },
    [TR_BASKER]      = { "BASKER", "Recovers a little HP at the end of every turn." },
    [TR_GLOWER]      = { "GLOWER", "Its glare lowers the foe's ATTACK when it enters." },
    [TR_STUBBORN]    = { "STUBBORN", "Holds on with 1 HP after a hit taken at full HP." },
    [TR_MOMENTUM]    = { "MOMENTUM", "Its SPEED rises every other turn." },
    [TR_HOARDER]     = { "HOARDER", "Sometimes finds an item after a bout." },
    [TR_QUICK_STUDY] = { "QUICK STUDY", "Earns 20% more XP." },
    [TR_SLIPPERY]    = { "SLIPPERY", "Always gets away from wild bouts." },
};

/* ================================================================ */
/*  Temperaments: +10% to one stat, -10% to another                 */
/* ================================================================ */

typedef struct { const char *name; s8 up, down; } Temperament; /* stat[] index or -1 */

#define TEMPERAMENT_COUNT 16
static const Temperament TEMPERAMENTS[TEMPERAMENT_COUNT] = {
    { "FIERY", STAT_ATK, STAT_SPD },   { "STEADY", STAT_DEF, STAT_SPE },
    { "CURIOUS", STAT_SPA, STAT_ATK }, { "DREAMY", STAT_SPD, STAT_SPE },
    { "NIMBLE", STAT_SPE, STAT_DEF },  { "SCRAPPY", STAT_ATK, STAT_SPA },
    { "STUBBORN", STAT_DEF, STAT_SPA },{ "CLEVER", STAT_SPA, STAT_DEF },
    { "SUNNY", STAT_SPE, STAT_SPD },   { "GRUMPY", STAT_ATK, STAT_SPE },
    { "PATIENT", STAT_SPD, STAT_ATK }, { "RESTLESS", STAT_SPE, STAT_ATK },
    { "PROUD", STAT_SPA, STAT_SPD },   { "SHY", STAT_SPD, STAT_SPA },
    { "SLEEPY", STAT_DEF, STAT_ATK },  { "EVEN", -1, -1 },
};

/* ================================================================ */
/*  Species                                                         */
/* ================================================================ */

enum {
    SP_FLARIX, SP_PYREFOX, SP_INFERNOX, SP_AQUAPO, SP_AXOLURK, SP_TIDALOTL,
    SP_DANDELAMB, SP_PUFFLEECE, SP_ZEPHRAM, SP_CINDERUB, SP_MAGMAUL,
    SP_BUBBLIN, SP_GLACIBLOB, SP_THORNIP, SP_BRAMBLOR, SP_MOSSHELL,
    SP_TERRASHELL, SP_ZAPPET, SP_STORMHAWK, SP_VOLTUX, SP_VOLTLOPE,
    SP_GOLEMIT, SP_BOULDRON, SP_PUFFOWL, SP_HOOTLORD, SP_SKYWISP,
    SP_LUMOTH, SP_NIBBIT, SP_GNAWLORD, SP_FROSTOAT, SP_WISPIRE, SP_DRAKORA,
    SP_COUNT
};

enum { EVO_NONE, EVO_LEVEL, EVO_ITEM };

enum { BS_HP, BS_ATK, BS_DEF, BS_SPA, BS_SPD, BS_SPE, BS_COUNT };
static const char *const BASE_STAT_NAMES[BS_COUNT] = {
    "HP", "ATTACK", "DEFENSE", "FOCUS", "WILL", "SPEED",
};

typedef struct { u8 level, move; } LearnEntry;

typedef struct {
    const char *name;
    u8 type1, type2;
    u8 base[BS_COUNT];
    u8 catch_rate;         /* 3..255, higher = easier */
    u8 xp_yield;
    u8 evo_kind, evo_param, evo_into;
    const char *category;
    u16 height_dm, weight_hg;
    const LearnEntry *learnset;
    const char *desc;
    u8 traits[2];
} Species;

/* Learnsets: level-ordered, level-1 moves first, terminated by {0, 0}. */
static const LearnEntry LS_FLARIX[] = {
    {1, M_SWIPE}, {1, M_POUT}, {7, M_CINDER_FLICK}, {11, M_DART},
    {15, M_SEAR_BITE}, {19, M_LANTERN_LURE}, {23, M_LAST_EMBER},
    {27, M_KILN_BREATH}, {33, M_GLINT}, {39, M_SUNFLARE}, {0, 0} };
static const LearnEntry LS_PYREFOX[] = {
    {1, M_SWIPE}, {1, M_POUT}, {1, M_CINDER_FLICK}, {11, M_DART},
    {15, M_SEAR_BITE}, {16, M_SNAP}, {21, M_LANTERN_LURE}, {25, M_LAST_EMBER},
    {29, M_KILN_BREATH}, {35, M_GLINT}, {42, M_SUNFLARE}, {0, 0} };
static const LearnEntry LS_INFERNOX[] = {
    {1, M_SWIPE}, {1, M_CINDER_FLICK}, {1, M_DART}, {1, M_SNAP},
    {15, M_SEAR_BITE}, {21, M_LANTERN_LURE}, {27, M_KILN_BREATH},
    {34, M_HAUNT}, {38, M_GLOOM_ORB}, {44, M_SUNFLARE}, {50, M_BRIM_BURST},
    {0, 0} };
static const LearnEntry LS_AQUAPO[] = {
    {1, M_BONK}, {1, M_POUT}, {6, M_FIZZ}, {10, M_SLIPSTREAM},
    {14, M_MUD_PIE}, {19, M_SNAP}, {23, M_UNDERTOW}, {28, M_SWELL},
    {34, M_BELLY_FLOP}, {40, M_GEYSER}, {0, 0} };
static const LearnEntry LS_AXOLURK[] = {
    {1, M_BONK}, {1, M_POUT}, {1, M_FIZZ}, {10, M_SLIPSTREAM},
    {14, M_MUD_PIE}, {20, M_SNAP}, {24, M_UNDERTOW}, {29, M_SWELL},
    {35, M_BELLY_FLOP}, {42, M_GEYSER}, {0, 0} };
static const LearnEntry LS_TIDALOTL[] = {
    {1, M_BONK}, {1, M_FIZZ}, {1, M_SLIPSTREAM}, {1, M_MUD_PIE},
    {20, M_SNAP}, {24, M_UNDERTOW}, {29, M_SWELL}, {34, M_WYRMBREATH},
    {38, M_SCALE_REND}, {45, M_GEYSER}, {52, M_STARFALL}, {0, 0} };
static const LearnEntry LS_DANDELAMB[] = {
    {1, M_BONK}, {1, M_POUT}, {7, M_BRAMBLE_LASH}, {11, M_DROWSY_POLLEN},
    {15, M_SAP_SIP}, {19, M_LEAF_FLURRY}, {23, M_BASK}, {27, M_BURR_VOLLEY},
    {33, M_BELLY_FLOP}, {39, M_SUNSHAFT}, {0, 0} };
static const LearnEntry LS_PUFFLEECE[] = {
    {1, M_BONK}, {1, M_POUT}, {1, M_BRAMBLE_LASH}, {11, M_DROWSY_POLLEN},
    {15, M_SAP_SIP}, {16, M_DRAFT}, {20, M_LEAF_FLURRY}, {25, M_BASK},
    {29, M_BURR_VOLLEY}, {35, M_BELLY_FLOP}, {42, M_SUNSHAFT}, {0, 0} };
static const LearnEntry LS_ZEPHRAM[] = {
    {1, M_BONK}, {1, M_BRAMBLE_LASH}, {1, M_DRAFT}, {1, M_DROWSY_POLLEN},
    {15, M_SAP_SIP}, {20, M_LEAF_FLURRY}, {25, M_BASK}, {30, M_FEATHER_CUT},
    {34, M_REED_BLADE}, {40, M_UPDRAFT}, {46, M_SUNSHAFT}, {52, M_STOOP},
    {0, 0} };
static const LearnEntry LS_CINDERUB[] = {
    {1, M_SWIPE}, {1, M_POUT}, {6, M_CINDER_FLICK}, {10, M_SNAP},
    {15, M_SEAR_BITE}, {20, M_BRACE}, {26, M_BELLY_FLOP},
    {32, M_KILN_BREATH}, {0, 0} };
static const LearnEntry LS_MAGMAUL[] = {
    {1, M_SWIPE}, {1, M_CINDER_FLICK}, {1, M_SNAP}, {1, M_SEAR_BITE},
    {20, M_BRACE}, {24, M_ROCKFALL}, {30, M_BELLY_FLOP}, {34, M_STONESKIN},
    {38, M_KILN_BREATH}, {44, M_FAULTLINE}, {50, M_SUNFLARE}, {0, 0} };
static const LearnEntry LS_BUBBLIN[] = {
    {1, M_BONK}, {1, M_FIZZ}, {8, M_POUT}, {12, M_SLIPSTREAM},
    {16, M_FLURRY}, {20, M_CATNAP}, {24, M_BELLY_FLOP}, {30, M_SWELL},
    {36, M_GEYSER}, {0, 0} };
static const LearnEntry LS_GLACIBLOB[] = {
    {1, M_FIZZ}, {1, M_FLURRY}, {1, M_RIME_SHOT}, {1, M_SWELL},
    {30, M_WINTER_RAY}, {36, M_HAILSTONES}, {42, M_GEYSER}, {0, 0} };
static const LearnEntry LS_THORNIP[] = {
    {1, M_SWIPE}, {1, M_GRIT_KICK}, {5, M_BRAMBLE_LASH},
    {9, M_BARB}, {13, M_SNAP}, {18, M_LEAF_FLURRY},
    {24, M_STARE_DOWN}, {30, M_REED_BLADE}, {0, 0} };
static const LearnEntry LS_BRAMBLOR[] = {
    {1, M_BRAMBLE_LASH}, {1, M_BARB}, {1, M_STARE_DOWN}, {1, M_LEAF_FLURRY},
    {25, M_SPORE_CLOUD}, {30, M_FESTER}, {34, M_REED_BLADE}, {40, M_BOG_BOMB},
    {46, M_BURR_VOLLEY}, {0, 0} };
static const LearnEntry LS_MOSSHELL[] = {
    {1, M_BONK}, {1, M_BRACE}, {6, M_BRAMBLE_LASH}, {10, M_SNAP},
    {14, M_SAP_SIP}, {19, M_PEBBLE_PELT}, {24, M_LEAF_FLURRY},
    {30, M_BASK}, {0, 0} };
static const LearnEntry LS_TERRASHELL[] = {
    {1, M_BONK}, {1, M_BRACE}, {1, M_BRAMBLE_LASH}, {1, M_SNAP},
    {14, M_SAP_SIP}, {19, M_PEBBLE_PELT}, {26, M_MUD_PIE}, {30, M_STONESKIN},
    {34, M_BELLY_FLOP}, {38, M_REED_BLADE}, {44, M_FAULTLINE}, {0, 0} };
static const LearnEntry LS_ZAPPET[] = {
    {1, M_BEAK_JAB}, {1, M_POUT}, {5, M_STATIC_POP}, {9, M_DART},
    {13, M_TINGLE}, {17, M_FEATHER_CUT}, {22, M_LIVE_WIRE},
    {28, M_FORKED_BOLT}, {0, 0} };
static const LearnEntry LS_STORMHAWK[] = {
    {1, M_BEAK_JAB}, {1, M_STATIC_POP}, {1, M_DART},
    {1, M_TINGLE}, {17, M_FEATHER_CUT}, {22, M_LIVE_WIRE},
    {28, M_UPDRAFT}, {32, M_FORKED_BOLT}, {38, M_STOOP}, {45, M_OVERCHARGE},
    {0, 0} };
static const LearnEntry LS_VOLTUX[] = {
    {1, M_BONK}, {1, M_POUT}, {6, M_STATIC_POP}, {10, M_DART},
    {14, M_SNAP}, {18, M_TINGLE}, {23, M_LIVE_WIRE}, {29, M_GLINT},
    {35, M_FORKED_BOLT}, {0, 0} };
static const LearnEntry LS_VOLTLOPE[] = {
    {1, M_DART}, {1, M_LIVE_WIRE}, {1, M_TINGLE}, {1, M_ONE_TWO},
    {30, M_PUMMEL}, {35, M_WAR_CRY}, {40, M_HAYMAKER}, {46, M_OVERCHARGE},
    {50, M_RECKLESS_RUSH}, {0, 0} };
static const LearnEntry LS_GOLEMIT[] = {
    {1, M_BONK}, {1, M_BRACE}, {6, M_PEBBLE_PELT}, {10, M_GRIT_KICK},
    {15, M_MUD_PIE}, {20, M_HAMMER_FIST}, {26, M_ROCKFALL},
    {31, M_BELLY_FLOP}, {37, M_FAULTLINE}, {0, 0} };
static const LearnEntry LS_BOULDRON[] = {
    {1, M_BONK}, {1, M_BRACE}, {1, M_PEBBLE_PELT}, {1, M_GRIT_KICK},
    {15, M_MUD_PIE}, {20, M_HAMMER_FIST}, {25, M_ROCKFALL}, {29, M_STONESKIN},
    {33, M_PUMMEL}, {38, M_FAULTLINE}, {44, M_HAYMAKER}, {50, M_RECKLESS_RUSH},
    {0, 0} };
static const LearnEntry LS_PUFFOWL[] = {
    {1, M_BONK}, {1, M_POUT}, {5, M_BEAK_JAB}, {9, M_DRAFT},
    {13, M_DAYDREAM}, {17, M_FEATHER_CUT}, {22, M_CATNAP}, {25, M_GLINT},
    {29, M_PRISM_RAY}, {0, 0} };
static const LearnEntry LS_HOOTLORD[] = {
    {1, M_BONK}, {1, M_POUT}, {1, M_BEAK_JAB}, {1, M_DRAFT},
    {13, M_DAYDREAM}, {17, M_FEATHER_CUT}, {20, M_PRISM_RAY},
    {24, M_CATNAP}, {28, M_GLINT}, {32, M_DREAMQUAKE}, {36, M_STILL_POND},
    {42, M_STOOP}, {48, M_PRIMAL_ROAR}, {0, 0} };
static const LearnEntry LS_SKYWISP[] = {
    {1, M_BONK}, {1, M_SILK_SNARE}, {6, M_DRAFT}, {10, M_SPORE_CLOUD},
    {14, M_DROWSY_POLLEN}, {18, M_PINCER}, {23, M_DAYDREAM},
    {28, M_WINGDUST}, {0, 0} };
static const LearnEntry LS_LUMOTH[] = {
    {1, M_DRAFT}, {1, M_DAYDREAM}, {1, M_WINGDUST}, {1, M_DROWSY_POLLEN},
    {30, M_PRISM_RAY}, {36, M_STILL_POND}, {42, M_DREAMQUAKE}, {0, 0} };
static const LearnEntry LS_NIBBIT[] = {
    {1, M_BONK}, {1, M_POUT}, {4, M_DART}, {8, M_SNAP},
    {12, M_GRIT_KICK}, {16, M_ONE_TWO}, {20, M_STARE_DOWN},
    {26, M_GNASH}, {32, M_RECKLESS_RUSH}, {0, 0} };
static const LearnEntry LS_GNAWLORD[] = {
    {1, M_BONK}, {1, M_DART}, {1, M_SNAP}, {1, M_GRIT_KICK},
    {16, M_ONE_TWO}, {18, M_STARE_DOWN}, {24, M_GNASH}, {28, M_CATNAP},
    {32, M_HAUNT}, {38, M_RECKLESS_RUSH}, {44, M_BRIM_BURST}, {0, 0} };
static const LearnEntry LS_FROSTOAT[] = {
    {1, M_SWIPE}, {1, M_POUT}, {5, M_FLURRY}, {9, M_DART},
    {13, M_RIME_SHOT}, {18, M_SNAP}, {22, M_HAILSTONES}, {26, M_GLINT},
    {30, M_WINTER_RAY}, {36, M_STILL_POND}, {0, 0} };
static const LearnEntry LS_WISPIRE[] = {
    {1, M_STARE_DOWN}, {1, M_DAYDREAM}, {8, M_LANTERN_LURE},
    {14, M_HAUNT}, {20, M_GLOOM_ORB}, {26, M_PRISM_RAY}, {30, M_STILL_POND},
    {36, M_DREAMQUAKE}, {42, M_KILN_BREATH}, {0, 0} };
static const LearnEntry LS_DRAKORA[] = {
    {1, M_WYRMBREATH}, {1, M_DRAFT}, {1, M_STARE_DOWN}, {1, M_FEATHER_CUT},
    {30, M_SCALE_REND}, {36, M_UPDRAFT}, {40, M_STOOP}, {46, M_FAULTLINE},
    {52, M_STARFALL}, {0, 0} };

#define SPC(n, t1, t2, hp, at, df, sa, sd, sp, cr, xp, ek, ep, ei, cat, h, w, ls, tr1, tr2, d) \
    { n, t1, t2, { hp, at, df, sa, sd, sp }, cr, xp, ek, ep, ei, cat, h, w, ls, d, { tr1, tr2 } }

/* Item ids (growth shards are referenced by the species table). */
enum {
    ITEM_TONIC, ITEM_BIG_TONIC, ITEM_GRAND_TONIC, ITEM_SOOTHE_BALM,
    ITEM_WAKE_BELL, ITEM_MINT_TEA, ITEM_SUNSEED, ITEM_LANTERN,
    ITEM_GLOW_LANTERN, ITEM_STAR_LANTERN, ITEM_BLOOM_SHARD,
    ITEM_SPARK_SHARD, ITEM_DUSK_SHARD, ITEM_FROST_SHARD, ITEM_BRAVE_CHILI,
    ITEM_IRONBARK, ITEM_HUSH_BELL, ITEM_COUNT
};

static const Species SPECIES[SP_COUNT] = {
    [SP_FLARIX] = SPC("FLARIX", T_BLAZE, TYPE_NONE, 41, 55, 42, 58, 47, 66, 45, 62,
        EVO_LEVEL, 16, SP_PYREFOX, "LANTERN KIT", 5, 85, LS_FLARIX, TR_SURGE, TR_EMBERSKIN,
        "The ember in its tail cage never goes out. Travelers who follow its "
        "glow always find their way to a warm hearth."),
    [SP_PYREFOX] = SPC("PYREFOX", T_BLAZE, TYPE_NONE, 58, 68, 55, 78, 62, 83, 45, 142,
        EVO_LEVEL, 34, SP_INFERNOX, "TWIN FLAME", 10, 210, LS_PYREFOX, TR_SURGE, TR_EMBERSKIN,
        "It swishes its two lantern tails to signal its pack. The steadier "
        "the glow, the calmer it feels."),
    [SP_INFERNOX] = SPC("INFERNOX", T_BLAZE, T_DUSK, 76, 98, 70, 108, 75, 103, 45, 239,
        EVO_NONE, 0, 0, "LANTERN FOX", 18, 620, LS_INFERNOX, TR_SURGE, TR_GLOWER,
        "It walks the edge of the night, cloaked in smoke. Its tail burns with "
        "light it drank from a hundred sunsets."),
    [SP_AQUAPO] = SPC("AQUAPO", T_TIDE, TYPE_NONE, 52, 58, 50, 50, 52, 44, 45, 62,
        EVO_LEVEL, 16, SP_AXOLURK, "AXOLOTL", 4, 52, LS_AQUAPO, TR_SURGE, TR_SELFMEND,
        "It keeps smiling even mid-bout. Its frilly gills taste the water for "
        "the tiny ripples other kin make."),
    [SP_AXOLURK] = SPC("AXOLURK", T_TIDE, TYPE_NONE, 72, 78, 66, 62, 62, 66, 45, 142,
        EVO_LEVEL, 34, SP_TIDALOTL, "AXOLOTL", 10, 245, LS_AXOLURK, TR_SURGE, TR_SELFMEND,
        "It waits under lily pads until the water ripples just right, then "
        "lunges out on a jet of current."),
    [SP_TIDALOTL] = SPC("TIDALOTL", T_TIDE, T_WYRM, 94, 100, 84, 96, 88, 70, 45, 239,
        EVO_NONE, 0, 0, "RIVER DRAKE", 30, 1050, LS_TIDALOTL, TR_SURGE, TR_SELFMEND,
        "Its gill crown pulls charge from the current. River towns once sang "
        "to it each spring so the floods would pass gently."),
    [SP_DANDELAMB] = SPC("DANDELAMB", T_BLOOM, TYPE_NONE, 48, 46, 50, 62, 64, 48, 45, 62,
        EVO_LEVEL, 16, SP_PUFFLEECE, "PUFF LAMB", 5, 64, LS_DANDELAMB, TR_SURGE, TR_BASKER,
        "Its wool is one big dandelion puff. When it sneezes, seeds scatter, "
        "and a meadow grows wherever it naps."),
    [SP_PUFFLEECE] = SPC("PUFFLEECE", T_BLOOM, TYPE_NONE, 62, 58, 64, 80, 82, 62, 45, 142,
        EVO_LEVEL, 34, SP_ZEPHRAM, "SEED SHEEP", 10, 200, LS_PUFFLEECE, TR_SURGE, TR_BASKER,
        "Blossoms open in its fleece on sunny days. Fields a flock has grazed "
        "grow back twice as thick."),
    [SP_ZEPHRAM] = SPC("ZEPHRAM", T_BLOOM, T_GALE, 84, 80, 78, 104, 96, 92, 45, 236,
        EVO_NONE, 0, 0, "WIND RAM", 19, 600, LS_ZEPHRAM, TR_SURGE, TR_DRIFTER,
        "Its fleece holds so much warm air that it floats on a breeze. It "
        "leads flocks over the mountains on rising winds."),
    [SP_CINDERUB] = SPC("CINDERUB", T_BLAZE, TYPE_NONE, 60, 68, 54, 44, 48, 40, 120, 64,
        EVO_LEVEL, 24, SP_MAGMAUL, "EMBER CUB", 6, 120, LS_CINDERUB, TR_THICK_FUR, TR_BRUISER,
        "The ember on its brow glows brighter when it is hungry. It loves to "
        "doze in warm ashes after a bout."),
    [SP_MAGMAUL] = SPC("MAGMAUL", T_BLAZE, T_STONE, 98, 112, 92, 66, 72, 48, 60, 172,
        EVO_NONE, 0, 0, "MAGMA BEAR", 19, 1400, LS_MAGMAUL, TR_THICK_FUR, TR_BRUISER,
        "Molten rock creeps through the cracks of its stony shoulders. One "
        "swipe splits a boulder like firewood."),
    [SP_BUBBLIN] = SPC("BUBBLIN", T_TIDE, TYPE_NONE, 72, 38, 52, 56, 54, 40, 190, 58,
        EVO_ITEM, ITEM_FROST_SHARD, SP_GLACIBLOB, "DROPLET", 3, 30, LS_BUBBLIN, TR_SOAKER, TR_SELFMEND,
        "Clean spring water wrapped around a tiny kernel. Startle it and it "
        "splits into droplets, then flows back together."),
    [SP_GLACIBLOB] = SPC("GLACIBLOB", T_TIDE, T_FROST, 112, 58, 82, 96, 88, 54, 75, 170,
        EVO_NONE, 0, 0, "GLACIER", 12, 880, LS_GLACIBLOB, TR_SOAKER, TR_BEDROCK,
        "A FROST SHARD froze it solid from the kernel out. The spikes on its "
        "crown never melt, even in summer."),
    [SP_THORNIP] = SPC("THORNIP", T_BLOOM, TYPE_NONE, 46, 62, 44, 54, 46, 60, 190, 58,
        EVO_ITEM, ITEM_BLOOM_SHARD, SP_BRAMBLOR, "RADISH", 4, 40, LS_THORNIP, TR_SPORESKIN, TR_KEEN_EYE,
        "It buries itself up to its leaves, pops out to startle passersby, "
        "then giggles and runs."),
    [SP_BRAMBLOR] = SPC("BRAMBLOR", T_BLOOM, T_VENOM, 78, 104, 76, 82, 72, 84, 75, 168,
        EVO_NONE, 0, 0, "BRAMBLE", 16, 450, LS_BRAMBLOR, TR_SPORESKIN, TR_KEEN_EYE,
        "A tangle of briars around a bitter kernel. Its purple berries are "
        "safe to touch, but never to eat."),
    [SP_MOSSHELL] = SPC("MOSSHELL", T_BLOOM, TYPE_NONE, 58, 56, 74, 42, 56, 28, 150, 60,
        EVO_LEVEL, 26, SP_TERRASHELL, "MOSS SNAIL", 5, 160, LS_MOSSHELL, TR_BASKER, TR_STUBBORN,
        "Moss grows thicker on its shell every year. It naps in sunbeams so "
        "the moss can pump its kernel for it."),
    [SP_TERRASHELL] = SPC("TERRASHELL", T_BLOOM, T_STONE, 98, 92, 114, 54, 82, 42, 60, 172,
        EVO_NONE, 0, 0, "CAIRN SNAIL", 18, 2800, LS_TERRASHELL, TR_BASKER, TR_BEDROCK,
        "It has stacked stones on its shell for a thousand years. Ferns, "
        "beetles and small kin live in the cairn it carries."),
    [SP_ZAPPET] = SPC("ZAPPET", T_SPARK, T_GALE, 42, 44, 40, 66, 46, 76, 190, 58,
        EVO_LEVEL, 22, SP_STORMHAWK, "SPARK CHICK", 3, 18, LS_ZAPPET, TR_STATIC_FUR, TR_CONDUCTOR,
        "Static builds in its fluffy down until it crackles. It flings tiny "
        "sparks at anything that surprises it."),
    [SP_STORMHAWK] = SPC("STORMHAWK", T_SPARK, T_GALE, 72, 78, 66, 102, 70, 104, 60, 172,
        EVO_NONE, 0, 0, "STORM", 15, 320, LS_STORMHAWK, TR_STATIC_FUR, TR_KEEN_EYE,
        "It rides the edges of thunderheads and dives faster than sound. Its "
        "crest glows white before lightning strikes."),
    [SP_VOLTUX] = SPC("VOLTUX", T_SPARK, TYPE_NONE, 46, 54, 40, 58, 44, 82, 170, 60,
        EVO_ITEM, ITEM_SPARK_SHARD, SP_VOLTLOPE, "SPARK HARE", 6, 75, LS_VOLTUX, TR_STATIC_FUR, TR_MOMENTUM,
        "It rubs its zigzag ears on dry grass to charge up. On dark nights its "
        "tail puff pops with little blue sparks."),
    [SP_VOLTLOPE] = SPC("VOLTLOPE", T_SPARK, T_BRAWL, 72, 104, 64, 78, 72, 108, 60, 175,
        EVO_NONE, 0, 0, "JACKALOPE", 14, 420, LS_VOLTLOPE, TR_MOMENTUM, TR_BRUISER,
        "Its antlers are frozen lightning. One thump of its hind legs sends a "
        "crackle through the ground for a mile."),
    [SP_GOLEMIT] = SPC("GOLEMIT", T_STONE, TYPE_NONE, 56, 76, 86, 30, 42, 24, 150, 60,
        EVO_LEVEL, 25, SP_BOULDRON, "PEBBLE", 6, 400, LS_GOLEMIT, TR_STUBBORN, TR_BEDROCK,
        "A living lump of rock. Moss grows in its cracks, and it nibbles the "
        "moss when it gets hungry."),
    [SP_BOULDRON] = SPC("BOULDRON", T_STONE, T_BRAWL, 92, 124, 128, 44, 66, 40, 60, 172,
        EVO_NONE, 0, 0, "BOULDER", 21, 5200, LS_BOULDRON, TR_STUBBORN, TR_BRUISER,
        "It sleeps for months and is often mistaken for a hill. Its crystals "
        "hum when anyone nearby is brimming."),
    [SP_PUFFOWL] = SPC("PUFFOWL", T_GALE, TYPE_NONE, 62, 40, 42, 44, 54, 56, 255, 52,
        EVO_LEVEL, 20, SP_HOOTLORD, "OWLET", 4, 60, LS_PUFFOWL, TR_WAKEFUL, TR_KEEN_EYE,
        "It puffs up to twice its size when surprised. Its huge eyes can read "
        "by starlight alone."),
    [SP_HOOTLORD] = SPC("HOOTLORD", T_GALE, T_DREAM, 98, 62, 66, 94, 96, 80, 90, 158,
        EVO_NONE, 0, 0, "GREAT OWL", 15, 380, LS_HOOTLORD, TR_WAKEFUL, TR_QUICK_STUDY,
        "It perches over old libraries and seems to read over people's "
        "shoulders. Its wings are speckled like the night sky."),
    [SP_SKYWISP] = SPC("SKYWISP", T_SWARM, T_GALE, 46, 34, 42, 62, 54, 70, 190, 56,
        EVO_ITEM, ITEM_DUSK_SHARD, SP_LUMOTH, "CLOUD MOTH", 4, 20, LS_SKYWISP, TR_DRIFTER, TR_SPORESKIN,
        "It drifts on warm breezes like a scrap of cloud. The dust on its "
        "wings flashes in time with every SKYWISP nearby."),
    [SP_LUMOTH] = SPC("LUMOTH", T_SWARM, T_DREAM, 72, 48, 64, 112, 90, 98, 75, 170,
        EVO_NONE, 0, 0, "MOON MOTH", 13, 125, LS_LUMOTH, TR_DRIFTER, TR_FOCUSED,
        "The patterns on its wings glow in the dark. Anyone who stares at "
        "them long enough starts to daydream."),
    [SP_NIBBIT] = SPC("NIBBIT", T_BEAST, TYPE_NONE, 44, 64, 40, 30, 42, 72, 255, 50,
        EVO_LEVEL, 18, SP_GNAWLORD, "PACK RAT", 3, 35, LS_NIBBIT, TR_HOARDER, TR_SLIPPERY,
        "It collects buttons, bottle caps and lost keys. If something shiny "
        "goes missing, check the nearest NIBBIT's bundle."),
    [SP_GNAWLORD] = SPC("GNAWLORD", T_BEAST, T_DUSK, 76, 102, 64, 44, 66, 104, 127, 140,
        EVO_NONE, 0, 0, "RAT KING", 9, 220, LS_GNAWLORD, TR_HOARDER, TR_GLOWER,
        "It wears the finest bottle cap in its hoard as a crown. Packs of "
        "NIBBIT bring it treasures every dusk."),
    [SP_FROSTOAT] = SPC("FROSTOAT", T_FROST, TYPE_NONE, 56, 64, 50, 78, 64, 92, 75, 150,
        EVO_NONE, 0, 0, "ERMINE", 5, 70, LS_FROSTOAT, TR_THICK_FUR, TR_SLIPPERY,
        "It pumps its kernel by shedding heat, so the ground frosts over "
        "wherever it curls up to sleep."),
    [SP_WISPIRE] = SPC("WISPIRE", T_DUSK, TYPE_NONE, 64, 54, 66, 112, 94, 96, 60, 160,
        EVO_NONE, 0, 0, "MARSH LIGHT", 10, 5, LS_WISPIRE, TR_DRIFTER, TR_FOCUSED,
        "A flickering light over the marshes. Some say it guides travelers "
        "home; others say it leads them in circles for fun."),
    [SP_DRAKORA] = SPC("DRAKORA", T_WYRM, T_GALE, 96, 114, 90, 114, 92, 96, 15, 250,
        EVO_NONE, 0, 0, "STORMWYRM", 45, 2100, LS_DRAKORA, TR_GLOWER, TR_MOMENTUM,
        "Its kernel is so old and vast that it feels the whole sky. When "
        "DRAKORA brims, the heavens brim with it."),
};

static const int STARTER_SPECIES[3] = { SP_FLARIX, SP_AQUAPO, SP_DANDELAMB };

/* The species a kin grows from, or -1 for a first stage. */
static int species_prevo(int sp)
{
    for (int i = 0; i < SP_COUNT; i++)
        if (SPECIES[i].evo_kind != EVO_NONE && SPECIES[i].evo_into == sp)
            return i;
    return -1;
}

static int species_base_stat_total(int sp)
{
    int t = 0;
    for (int i = 0; i < BS_COUNT; i++) t += SPECIES[sp].base[i];
    return t;
}

/* ================================================================ */
/*  Items                                                           */
/* ================================================================ */

enum { POCKET_SUPPLIES, POCKET_LANTERNS, POCKET_SHARDS, POCKET_COUNT };
static const char *const POCKET_NAMES[POCKET_COUNT] = { "SUPPLIES", "LANTERNS", "SHARDS" };

enum { IK_HEAL, IK_FULL_HEAL, IK_WAKE, IK_TEA, IK_SEED, IK_LANTERN, IK_SHARD, IK_XSTAT, IK_HUSH };

typedef struct {
    const char *name;
    u8 pocket, kind, param;
    u16 price; /* 0 = not sold */
    const char *desc;
} Item;

static const Item ITEMS[ITEM_COUNT] = {
    [ITEM_TONIC]         = { "GLOW TONIC", POCKET_SUPPLIES, IK_HEAL, 20, 200,
                             "A luciferin drink whose cold light pumps a kernel. Restores 20 HP." },
    [ITEM_BIG_TONIC]     = { "BRIGHT TONIC", POCKET_SUPPLIES, IK_HEAL, 60, 700,
                             "A stronger brew of glowing tonic. Restores 60 HP." },
    [ITEM_GRAND_TONIC]   = { "RADIANT TONIC", POCKET_SUPPLIES, IK_HEAL, 120, 1500,
                             "Tonic bright enough to read by. Restores 120 HP." },
    [ITEM_SOOTHE_BALM]   = { "TUNING FORK", POCKET_SUPPLIES, IK_FULL_HEAL, 0, 600,
                             "Its pure tone re-phases a kin's field, curing any status problem." },
    [ITEM_WAKE_BELL]     = { "IGNITER", POCKET_SUPPLIES, IK_WAKE, 0, 1500,
                             "A piezo flash that re-seeds a collapsed field. Wakes a dozing kin with half HP." },
    [ITEM_MINT_TEA]      = { "HONEY DROP", POCKET_SUPPLIES, IK_TEA, 10, 1200,
                             "Glow-bee honey that refuels tired modes. Restores 10 uses to every move." },
    [ITEM_SUNSEED]       = { "SUNSEED", POCKET_SUPPLIES, IK_SEED, 0, 0,
                             "A seed that stored a whole summer. Its kernel absorbs it and grows one level." },
    [ITEM_LANTERN]       = { "LANTERN", POCKET_LANTERNS, IK_LANTERN, 10, 200,
                             "A heartglass cavity. A calm, tired wild kin may choose to rest inside." },
    [ITEM_GLOW_LANTERN]  = { "PRISM LANTERN", POCKET_LANTERNS, IK_LANTERN, 15, 600,
                             "Finer mirrors hold livelier kin. Better than a plain LANTERN." },
    [ITEM_STAR_LANTERN]  = { "STAR LANTERN", POCKET_LANTERNS, IK_LANTERN, 20, 1200,
                             "Star-polished heartglass of the highest finesse. The best lantern made." },
    [ITEM_BLOOM_SHARD]   = { "BLOOM SHARD", POCKET_SHARDS, IK_SHARD, 0, 2100,
                             "A seed crystal of springtime. It makes THORNIP grow at once." },
    [ITEM_SPARK_SHARD]   = { "SPARK SHARD", POCKET_SHARDS, IK_SHARD, 0, 2100,
                             "A seed crystal that crackles. It makes VOLTUX grow at once." },
    [ITEM_DUSK_SHARD]    = { "DUSK SHARD", POCKET_SHARDS, IK_SHARD, 0, 0,
                             "A seed crystal that drinks light. It makes SKYWISP grow at once." },
    [ITEM_FROST_SHARD]   = { "FROST SHARD", POCKET_SHARDS, IK_SHARD, 0, 2100,
                             "A seed crystal that never warms. It makes BUBBLIN grow at once." },
    [ITEM_BRAVE_CHILI]   = { "AMP COIL", POCKET_SUPPLIES, IK_XSTAT, STAT_ATK, 500,
                             "Clips on to boost a kin's pump. Sharply raises ATTACK for the bout." },
    [ITEM_IRONBARK]      = { "GUARD COIL", POCKET_SUPPLIES, IK_XSTAT, STAT_DEF, 550,
                             "Stiffens a kin's outer field. Sharply raises DEFENSE for the bout." },
    [ITEM_HUSH_BELL]     = { "HUSH BELL", POCKET_SUPPLIES, IK_HUSH, 150, 700,
                             "Its anti-phase hum hides your team's field. Wild kin ignore you for 150 steps." },
};
