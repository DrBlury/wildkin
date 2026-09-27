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
    T_HOLLOW, T_RELIC, T_METAL, T_ASTRAL,
    TYPE_COUNT
};
#define TYPE_NONE 0xFF

static const char *const TYPE_NAMES[TYPE_COUNT] = {
    "BEAST", "BLAZE", "TIDE", "BLOOM", "SPARK", "FROST", "BRAWL",
    "VENOM", "STONE", "GALE", "DREAM", "SWARM", "DUSK", "WYRM",
    "HOLLOW", "RELIC", "METAL", "ASTRAL",
};

/*
 * Attacker rows, defender columns in enum order:
 *   Be Bl Ti Bo Sp Fr Br Ve St Ga Dr Sw Du Wy Ho Re Me As
 * '+' strikes a weak spot (x2), '-' shrugged off (x0.5), '0' no effect.
 * Physics first: water quenches heat, charge races through water, stone
 * grounds charge, heat melts frost. Light and dark (BLAZE, DUSK) eat each
 * other, and VENOM fouls water. The expansion types (docs/EXPANSION.md 2):
 * heat cremates HOLLOW, burns RELIC and forges METAL; water rusts METAL;
 * carrion beetles and woodworm (SWARM) beat HOLLOW and RELIC; talismans
 * (RELIC) ward off HOLLOW; starlight (ASTRAL) scours HOLLOW, DUSK and WYRM;
 * magnetism (METAL) bends ASTRAL; poison can't touch the dead or iron.
 */
static const char TYPE_CHART[TYPE_COUNT][TYPE_COUNT + 1] = {
    /* BEAST  */ "........-...0.-.-.",
    /* BLAZE  */ ".--+.+..-..++-+++-",
    /* TIDE   */ ".+--....+....-..+.",
    /* BLOOM  */ ".-+-...-+-.-.--.-.",
    /* SPARK  */ "..+--...0+...-....",
    /* FROST  */ ".--+.-..++...+..-.",
    /* BRAWL  */ "+....+.-+---+.-++-",
    /* VENOM  */ "..++...--...-.0-0.",
    /* STONE  */ ".+.-++.+...-....-.",
    /* GALE   */ "...+-.+.-..+....--",
    /* DREAM  */ "......++..-.-.---.",
    /* SWARM  */ ".-.+..--.-+.+.++-.",
    /* DUSK   */ "0+....-...+.+....+",
    /* WYRM   */ ".............+..-.",
    /* HOLLOW */ ".-.+......+.-..---",
    /* RELIC  */ ".-......-.+...+.-.",
    /* METAL  */ ".--.-+..+.......-+",
    /* ASTRAL */ ".-..........+++.--",
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
/*  Species (the tables are generated from tools/kin/ into            */
/*  src/species_data.h: SP_* ids, learnsets and SPECIES[])            */
/* ================================================================ */

enum { EVO_NONE, EVO_LEVEL, EVO_ITEM, EVO_BOND };   /* EVO_BOND: bond >= 220 on a level-up */
#define EVO_BOND_MIN 220

enum { R_COMMON, R_UNCOMMON, R_RARE, R_LEGEND, R_FUSION, RARITY_COUNT };
static const char *const RARITY_NAMES[RARITY_COUNT] = { "COMMON", "UNCOMMON", "RARE", "LEGEND", "FUSION" };

/* Field abilities a species can lend (docs/EXPANSION.md 7.5). */
enum { FA_SURF = 1, FA_FLY = 2, FA_TELEPORT = 4, FA_LIGHT = 8, FA_STRENGTH = 16 };

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
    u8 rarity;             /* R_* */
    u8 field;              /* FA_* */
    u8 fusion[2];          /* signature energy types of a fusion kin, else TYPE_NONE */
} Species;

/* ================================================================ */
/*  Item ids (growth shards are referenced by the species table).    */
/*  Items 0-16 keep their ids; every owner appends in its own        */
/*  src/game/items/<owner>_ids.inc and <owner>.inc (see EXPANSION.md) */
/* ================================================================ */

enum {
    ITEM_TONIC, ITEM_BIG_TONIC, ITEM_GRAND_TONIC, ITEM_SOOTHE_BALM,
    ITEM_WAKE_BELL, ITEM_MINT_TEA, ITEM_SUNSEED, ITEM_LANTERN,
    ITEM_GLOW_LANTERN, ITEM_STAR_LANTERN, ITEM_BLOOM_SHARD,
    ITEM_SPARK_SHARD, ITEM_DUSK_SHARD, ITEM_FROST_SHARD, ITEM_BRAVE_CHILI,
    ITEM_IRONBARK, ITEM_HUSH_BELL,
#include "items/all_ids.inc"
    ITEM_COUNT
};
typedef char ItemIdsFitU8[ITEM_COUNT <= 255 ? 1 : -1];

#include "../species_data.h"

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

enum { POCKET_SUPPLIES, POCKET_LANTERNS, POCKET_SHARDS, POCKET_FOOD, POCKET_FARM, POCKET_MATERIALS,
       POCKET_KEY, POCKET_COUNT };
static const char *const POCKET_NAMES[POCKET_COUNT] = {
    "SUPPLIES", "LANTERNS", "SHARDS", "FOOD", "FARM", "MATERIALS", "KEY ITEMS",
};

/* What using an item does (party.c / battle.c / farm.c / craft.c). */
enum {
    IK_HEAL, IK_FULL_HEAL, IK_WAKE, IK_TEA, IK_SEED, IK_LANTERN, IK_SHARD, IK_XSTAT, IK_HUSH,
    IK_HEAL_CURE,     /* heal param HP and cure status */
    IK_TEA_ALL,       /* restore every move's uses fully */
    IK_REVIVE,        /* wake a dozing kin with full HP */
    IK_LURE,          /* rare kin more likely for param*10 steps */
    IK_WAYSTONE,      /* back to the last Hearth Hall */
    IK_FOOD,          /* a meal: param = MEAL_* buff (craft.c) */
    IK_MATERIAL,      /* crafting ingredient, not used directly */
    IK_PLANT,         /* seed or sapling: param = CROP_* (farm.c) */
    IK_FERTILIZER,    /* param = FERT_* (farm.c) */
    IK_CROP,          /* produce: sell it or cook with it */
    IK_PLACE,         /* placed on the farm (sprinkler) */
    IK_KEY,           /* key item: param = KEY_* */
};

typedef struct {
    const char *name;
    u8 pocket, kind, param;
    u16 price; /* 0 = not sold */
    const char *desc;
    u8 icon;   /* ICON_* (gfx_battle.h) */
} Item;

#define ITEM_DEF(id, name, pocket, kind, param, price, icon, desc) \
    [id] = { name, pocket, kind, param, price, desc, icon },

static const Item ITEMS[ITEM_COUNT] = {
    [ITEM_TONIC]         = { "GLOW TONIC", POCKET_SUPPLIES, IK_HEAL, 20, 200,
                             "A luciferin drink whose cold light pumps a kernel. Restores 20 HP.", ICON_GLOW_TONIC },
    [ITEM_BIG_TONIC]     = { "BRIGHT TONIC", POCKET_SUPPLIES, IK_HEAL, 60, 700,
                             "A stronger brew of glowing tonic. Restores 60 HP.", ICON_BRIGHT_TONIC },
    [ITEM_GRAND_TONIC]   = { "RADIANT TONIC", POCKET_SUPPLIES, IK_HEAL, 120, 1500,
                             "Tonic bright enough to read by. Restores 120 HP.", ICON_RADIANT_TONIC },
    [ITEM_SOOTHE_BALM]   = { "TUNING FORK", POCKET_SUPPLIES, IK_FULL_HEAL, 0, 600,
                             "Its pure tone re-phases a kin's field, curing any status problem.", ICON_TUNING_FORK },
    [ITEM_WAKE_BELL]     = { "IGNITER", POCKET_SUPPLIES, IK_WAKE, 0, 1500,
                             "A piezo flash that re-seeds a collapsed field. Wakes a dozing kin with half HP.", ICON_IGNITER },
    [ITEM_MINT_TEA]      = { "HONEY DROP", POCKET_SUPPLIES, IK_TEA, 10, 1200,
                             "Glow-bee honey that refuels tired modes. Restores 10 uses to every move.", ICON_HONEY_DROP },
    [ITEM_SUNSEED]       = { "SUNSEED", POCKET_SUPPLIES, IK_SEED, 0, 0,
                             "A seed that stored a whole summer. Its kernel absorbs it and grows one level.", ICON_SUNSEED },
    [ITEM_LANTERN]       = { "LANTERN", POCKET_LANTERNS, IK_LANTERN, 10, 200,
                             "A heartglass cavity. A calm, tired wild kin may choose to rest inside.", ICON_LANTERN },
    [ITEM_GLOW_LANTERN]  = { "PRISM LANTERN", POCKET_LANTERNS, IK_LANTERN, 15, 600,
                             "Finer mirrors hold livelier kin. Better than a plain LANTERN.", ICON_PRISM_LANTERN },
    [ITEM_STAR_LANTERN]  = { "STAR LANTERN", POCKET_LANTERNS, IK_LANTERN, 20, 1200,
                             "Star-polished heartglass of the highest finesse. The best lantern made.", ICON_STAR_LANTERN },
    [ITEM_BLOOM_SHARD]   = { "BLOOM SHARD", POCKET_SHARDS, IK_SHARD, 0, 2100,
                             "A seed crystal of springtime. It makes THORNIP grow at once.", ICON_BLOOM_SHARD },
    [ITEM_SPARK_SHARD]   = { "SPARK SHARD", POCKET_SHARDS, IK_SHARD, 0, 2100,
                             "A seed crystal that crackles. It makes VOLTUX grow at once.", ICON_SPARK_SHARD },
    [ITEM_DUSK_SHARD]    = { "DUSK SHARD", POCKET_SHARDS, IK_SHARD, 0, 0,
                             "A seed crystal that drinks light. It makes SKYWISP grow at once.", ICON_DUSK_SHARD },
    [ITEM_FROST_SHARD]   = { "FROST SHARD", POCKET_SHARDS, IK_SHARD, 0, 2100,
                             "A seed crystal that never warms. It makes BUBBLIN grow at once.", ICON_FROST_SHARD },
    [ITEM_BRAVE_CHILI]   = { "AMP COIL", POCKET_SUPPLIES, IK_XSTAT, STAT_ATK, 500,
                             "Clips on to boost a kin's pump. Sharply raises ATTACK for the bout.", ICON_AMP_COIL },
    [ITEM_IRONBARK]      = { "GUARD COIL", POCKET_SUPPLIES, IK_XSTAT, STAT_DEF, 550,
                             "Stiffens a kin's outer field. Sharply raises DEFENSE for the bout.", ICON_GUARD_COIL },
    [ITEM_HUSH_BELL]     = { "HUSH BELL", POCKET_SUPPLIES, IK_HUSH, 150, 700,
                             "Its anti-phase hum hides your team's field. Wild kin ignore you for 150 steps.", ICON_HUSH_BELL },
#include "items/all_items.inc"
};

