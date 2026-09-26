/*
 * Moves: effects, animation recipes and the move table.
 *
 * Slots 0..59 keep the numbering of the original move list so older saves
 * still load (each slot now holds a new move); 60.. are later additions.
 * See docs/WORLD.md section 7 for the concepts behind each move.
 */

enum {
    EF_NONE,
    EF_STATUS,    /* param: status, chance% */
    EF_FLINCH,    /* chance% */
    EF_FOE_STAT,  /* param: stat, stages (negative) */
    EF_SELF_STAT, /* param: stat mask, stages */
    EF_DRAIN,     /* heals half the damage dealt */
    EF_RECOIL,    /* user takes a third of the damage dealt */
    EF_HIGHCRIT,
    EF_TWICE,     /* hits two times */
    EF_HEAL,      /* status move: user recovers half its max HP */
    EF_PUNISH,    /* double power if the foe has a status problem */
    EF_DESPERATE, /* power grows as the user's HP falls (up to x4) */
    EF_BRIM,      /* power scales with the user's HP (full HP = listed power) */
    EF_MULTI,     /* hits 2-5 times */
    EF_SELF_DOWN, /* after hitting: param stat mask, stages (negative) on the user */
};

/* Battle animation kinds (see anim.c). */
enum {
    AK_CONTACT, AK_SLASH, AK_PROJECTILE, AK_STREAM, AK_BEAM, AK_RAIN,
    AK_BOLT, AK_BURST, AK_ORBIT, AK_WAVE, AK_QUAKE, AK_BUFF, AK_DEBUFF,
    AK_FANGS, AK_DRAIN, AK_DASH, AK_SLAM, AK_WHIP, AK_PSYCHIC,
    AK_POWDER, AK_STRIKE,
    AK_ROAR,      /* rears up; shockwave rings; heavy shake */
    AK_GEYSER,    /* rumble, then a column bursts up under the foe */
    AK_SUNSHAFT,  /* a shaft of light falls from the sky */
    AK_FAULT,     /* the ground cracks in a jagged line, debris heaves */
    AK_WOBBLE,    /* the world wobbles (scanline warp + mosaic) */
    AK_HEAL,      /* sunlight / a curled-up nap on the user, sparkles */
    AK_CHARGE,    /* charge-up (motes rush in), then release */
    AK_LURE,      /* a bobbing wisp drifts over, circles, flares */
    AK_STOOP,     /* rises out of sight and dives on the foe */
    AK_HAYMAKER,  /* long trembling wind-up, then a huge swing */
    AK_SPIRAL,    /* a corkscrew of particles */
    AK_RIPPLE,    /* calm rings spread around the user */
    AK_WRAP,      /* threads shoot over and wind round the foe */
    AK_GUARD,     /* plants its feet (squash), hardens, a glint */
    AK_RUSH,      /* wind-up, speed lines, a crushing charge, bounced back */
    AK_COUNT
};

enum {
    /* BEAST */
    M_BONK, M_SWIPE, M_DART, M_POUT, M_BRACE, M_BELLY_FLOP,
    M_RECKLESS_RUSH, M_GLINT, M_PRIMAL_ROAR,
    /* BLAZE */
    M_CINDER_FLICK, M_SEAR_BITE, M_KILN_BREATH, M_SUNFLARE, M_LANTERN_LURE,
    /* TIDE */
    M_FIZZ, M_SLIPSTREAM, M_SWELL, M_GEYSER,
    /* BLOOM */
    M_BRAMBLE_LASH, M_SAP_SIP, M_LEAF_FLURRY, M_DROWSY_POLLEN, M_REED_BLADE,
    M_SUNSHAFT,
    /* SPARK */
    M_STATIC_POP, M_LIVE_WIRE, M_FORKED_BOLT, M_TINGLE,
    /* FROST */
    M_FLURRY, M_RIME_SHOT, M_WINTER_RAY,
    /* BRAWL */
    M_HAMMER_FIST, M_ONE_TWO, M_HAYMAKER,
    /* VENOM */
    M_BARB, M_SPORE_CLOUD, M_BOG_BOMB,
    /* STONE */
    M_GRIT_KICK, M_PEBBLE_PELT, M_MUD_PIE, M_ROCKFALL, M_FAULTLINE,
    /* GALE */
    M_DRAFT, M_BEAK_JAB, M_FEATHER_CUT, M_STOOP,
    /* DREAM */
    M_DAYDREAM, M_PRISM_RAY, M_DREAMQUAKE, M_STILL_POND,
    /* SWARM */
    M_SILK_SNARE, M_PINCER, M_WINGDUST,
    /* DUSK */
    M_SNAP, M_STARE_DOWN, M_GLOOM_ORB, M_GNASH,
    /* WYRM */
    M_WYRMBREATH, M_SCALE_REND, M_STARFALL,
    /* later additions */
    M_BASK, M_CATNAP, M_FESTER, M_HAUNT, M_LAST_EMBER, M_BRIM_BURST,
    M_PUMMEL, M_HAILSTONES, M_BURR_VOLLEY, M_OVERCHARGE, M_UPDRAFT,
    M_STONESKIN, M_WAR_CRY, M_UNDERTOW,
    MOVE_COUNT,
    M_LAST_GASP = MOVE_COUNT, /* not learnable: used when every move is out of uses */
    MOVE_TABLE_SIZE
};
#define MOVE_NONE 0xFF

typedef struct {
    const char *name;
    u8 type, cat, power, acc, pp; /* acc 0 = never misses; pp = uses */
    s8 priority;
    u8 effect, chance, param;
    s8 stages;
    u8 anim, fx, fx2, count;      /* animation kind, particles, repeat count */
    u16 col1, col2;               /* particle main / secondary colors */
    const char *desc;
} Move;

/* Effect particle ids are defined by gfx_battle.h (FX_*). */
#define MV(n, t, c, p, a, pp, pr, ef, ch, pa, st, an, fx, fx2, cnt, c1, c2, d) \
    { n, t, c, p, a, pp, pr, ef, ch, pa, st, an, fx, fx2, cnt, c1, c2, d }

static const Move MOVES[MOVE_TABLE_SIZE] = {
    /* ---------------- BEAST ---------------- */
    [M_BONK] = MV("BONK", T_BEAST, CAT_PHYS, 40, 100, 35, 0, EF_NONE, 0, 0, 0,
        AK_CONTACT, FX_IMPACT, FX_STAR, 1, RGB15(31, 31, 28), RGB15(31, 27, 10),
        "A clumsy headbutt. Simple, honest, effective."),
    [M_SWIPE] = MV("SWIPE", T_BEAST, CAT_PHYS, 40, 100, 35, 0, EF_NONE, 0, 0, 0,
        AK_SLASH, FX_CLAW, FX_IMPACT_SMALL, 1, RGB15(31, 31, 31), RGB15(26, 26, 31),
        "A quick swipe of the paw."),
    [M_DART] = MV("DART", T_BEAST, CAT_PHYS, 40, 100, 30, 1, EF_NONE, 0, 0, 0,
        AK_DASH, FX_IMPACT_SMALL, FX_SPEEDLINE, 1, RGB15(31, 31, 31), RGB15(20, 26, 31),
        "Darts in before the foe can blink. Always first."),
    [M_POUT] = MV("POUT", T_BEAST, CAT_STATUS, 0, 100, 40, 0, EF_FOE_STAT, 100, STAT_ATK, -1,
        AK_DEBUFF, FX_HEART, FX_TEAR, 3, RGB15(31, 14, 20), RGB15(16, 24, 31),
        "Pouts so pitifully the foe's ATTACK drops."),
    [M_BRACE] = MV("BRACE", T_BEAST, CAT_STATUS, 0, 0, 30, 0, EF_SELF_STAT, 100, SM(STAT_DEF), 1,
        AK_GUARD, FX_SPARKLE, FX_SPARKLE, 1, RGB15(26, 26, 30), RGB15(31, 31, 31),
        "Plants its feet and braces. Raises DEFENSE."),
    [M_BELLY_FLOP] = MV("BELLY FLOP", T_BEAST, CAT_PHYS, 85, 100, 15, 0, EF_STATUS, 30, STATUS_NUMB, 0,
        AK_SLAM, FX_IMPACT, FX_DUST, 1, RGB15(31, 28, 20), RGB15(31, 31, 31),
        "Flops onto the foe with its full weight. May numb."),
    [M_RECKLESS_RUSH] = MV("BULLRUSH", T_BEAST, CAT_PHYS, 110, 100, 15, 0, EF_RECOIL, 100, 0, 0,
        AK_RUSH, FX_IMPACT, FX_SPEEDLINE, 1, RGB15(31, 31, 31), RGB15(31, 24, 8),
        "A headlong charge that also jolts the user."),
    [M_GLINT] = MV("GLINT", T_BEAST, CAT_SPEC, 60, 0, 20, 0, EF_NONE, 0, 0, 0,
        AK_PROJECTILE, FX_SPARKLE, FX_STAR, 1, RGB15(31, 30, 18), RGB15(31, 31, 28),
        "A glint of light that always finds its mark."),
    [M_PRIMAL_ROAR] = MV("PRIMAL ROAR", T_BEAST, CAT_SPEC, 130, 90, 5, 0, EF_NONE, 0, 0, 0,
        AK_ROAR, FX_RING, FX_RING, 3, RGB15(31, 24, 10), RGB15(31, 31, 24),
        "A roar from the dawn of the world. Hits like a wall."),

    /* ---------------- BLAZE ---------------- */
    [M_CINDER_FLICK] = MV("CINDER FLICK", T_BLAZE, CAT_SPEC, 40, 100, 25, 0, EF_STATUS, 10, STATUS_BRN, 0,
        AK_PROJECTILE, FX_FIREBALL, FX_FLAME_A, 1, RGB15(31, 10, 2), RGB15(31, 27, 6),
        "Flicks a hot cinder at the foe. May burn."),
    [M_SEAR_BITE] = MV("SEAR BITE", T_BLAZE, CAT_PHYS, 65, 95, 15, 0, EF_STATUS, 10, STATUS_BRN, 0,
        AK_FANGS, FX_FANG_TOP, FX_FLAME_A, 1, RGB15(31, 31, 31), RGB15(31, 13, 2),
        "Bites with fangs glowing like coals. May burn."),
    [M_KILN_BREATH] = MV("KILN BREATH", T_BLAZE, CAT_SPEC, 90, 100, 15, 0, EF_STATUS, 10, STATUS_BRN, 0,
        AK_STREAM, FX_FLAME_A, FX_FLAME_B, 12, RGB15(31, 12, 2), RGB15(31, 28, 8),
        "A steady stream of kiln-hot breath. May burn."),
    [M_SUNFLARE] = MV("SUNFLARE", T_BLAZE, CAT_SPEC, 110, 85, 5, 0, EF_STATUS, 30, STATUS_BRN, 0,
        AK_CHARGE, FX_BURST, FX_FLAME_B, 8, RGB15(31, 8, 2), RGB15(31, 28, 6),
        "Releases a stored summer day at once. May burn."),
    [M_LANTERN_LURE] = MV("LANTERN LURE", T_BLAZE, CAT_STATUS, 0, 85, 15, 0, EF_STATUS, 100, STATUS_BRN, 0,
        AK_LURE, FX_WISP, FX_SPARKLE, 1, RGB15(31, 22, 8), RGB15(31, 30, 20),
        "A friendly bobbing flame that burns its followers."),

    /* ---------------- TIDE ---------------- */
    [M_FIZZ] = MV("FIZZ", T_TIDE, CAT_SPEC, 40, 100, 30, 0, EF_FOE_STAT, 10, STAT_SPE, -1,
        AK_PROJECTILE, FX_BUBBLE, FX_DROP, 4, RGB15(12, 22, 31), RGB15(28, 31, 31),
        "Fizzy bubbles pop on the foe. May lower SPEED."),
    [M_SLIPSTREAM] = MV("SLIPSTREAM", T_TIDE, CAT_PHYS, 40, 100, 20, 1, EF_NONE, 0, 0, 0,
        AK_DASH, FX_IMPACT_SMALL, FX_DROP, 1, RGB15(8, 18, 31), RGB15(20, 28, 31),
        "Rides a slick of water to strike first."),
    [M_SWELL] = MV("SWELL", T_TIDE, CAT_SPEC, 90, 100, 15, 0, EF_NONE, 0, 0, 0,
        AK_WAVE, FX_WAVE, FX_DROP, 6, RGB15(6, 16, 31), RGB15(26, 30, 31),
        "A rolling swell crashes over the foe."),
    [M_GEYSER] = MV("GEYSER", T_TIDE, CAT_SPEC, 110, 80, 5, 0, EF_NONE, 0, 0, 0,
        AK_GEYSER, FX_DROP, FX_STEAM, 1, RGB15(4, 12, 30), RGB15(18, 28, 31),
        "The ground under the foe bursts in a hot column."),

    /* ---------------- BLOOM ---------------- */
    [M_BRAMBLE_LASH] = MV("BRAMBLE LASH", T_BLOOM, CAT_PHYS, 45, 100, 25, 0, EF_NONE, 0, 0, 0,
        AK_WHIP, FX_VINE, FX_LEAF_A, 2, RGB15(6, 22, 6), RGB15(20, 30, 10),
        "Lashes the foe with a thorny bramble."),
    [M_SAP_SIP] = MV("SAP SIP", T_BLOOM, CAT_SPEC, 50, 100, 15, 0, EF_DRAIN, 100, 0, 0,
        AK_DRAIN, FX_ORB, FX_SPARKLE, 5, RGB15(10, 28, 8), RGB15(26, 31, 16),
        "Sips vigor like sap. Heals half the damage dealt."),
    [M_LEAF_FLURRY] = MV("LEAF FLURRY", T_BLOOM, CAT_PHYS, 55, 95, 25, 0, EF_HIGHCRIT, 100, 0, 0,
        AK_SPIRAL, FX_LEAF_A, FX_LEAF_B, 8, RGB15(8, 24, 6), RGB15(22, 30, 8),
        "A spiral of razor leaves. Often a perfect strike."),
    [M_DROWSY_POLLEN] = MV("DOZE POLLEN", T_BLOOM, CAT_STATUS, 0, 75, 15, 0, EF_STATUS, 100, STATUS_SLP, 0,
        AK_POWDER, FX_POWDER, FX_ZZZ, 8, RGB15(30, 28, 12), RGB15(31, 31, 26),
        "A puff of golden pollen that makes the foe sleep."),
    [M_REED_BLADE] = MV("REED BLADE", T_BLOOM, CAT_PHYS, 90, 100, 15, 0, EF_HIGHCRIT, 100, 0, 0,
        AK_SLASH, FX_SLASH, FX_LEAF_A, 2, RGB15(8, 26, 8), RGB15(24, 31, 14),
        "A long reed swung like a blade. Often perfect."),
    [M_SUNSHAFT] = MV("SUNSHAFT", T_BLOOM, CAT_SPEC, 120, 100, 10, 0, EF_NONE, 0, 0, 0,
        AK_SUNSHAFT, FX_SUNRAY, FX_SPARKLE, 1, RGB15(24, 31, 8), RGB15(31, 31, 20),
        "Calls down a shaft of stored sunlight."),

    /* ---------------- SPARK ---------------- */
    [M_STATIC_POP] = MV("STATIC POP", T_SPARK, CAT_SPEC, 40, 100, 30, 0, EF_STATUS, 10, STATUS_NUMB, 0,
        AK_BURST, FX_SPARK_A, FX_SPARK_B, 4, RGB15(31, 28, 4), RGB15(31, 31, 24),
        "Static pops all around the foe. May numb it."),
    [M_LIVE_WIRE] = MV("LIVE WIRE", T_SPARK, CAT_PHYS, 65, 100, 20, 0, EF_STATUS, 30, STATUS_NUMB, 0,
        AK_CONTACT, FX_SPARK_A, FX_SPARK_B, 1, RGB15(31, 26, 2), RGB15(31, 31, 20),
        "Charges in crackling with static. May numb."),
    [M_FORKED_BOLT] = MV("FORKED BOLT", T_SPARK, CAT_SPEC, 90, 100, 15, 0, EF_STATUS, 10, STATUS_NUMB, 0,
        AK_BOLT, FX_BOLT, FX_SPARK_A, 2, RGB15(31, 29, 6), RGB15(31, 31, 26),
        "A forked bolt from a clear sky. May numb."),
    [M_TINGLE] = MV("TINGLE", T_SPARK, CAT_STATUS, 0, 90, 20, 0, EF_STATUS, 100, STATUS_NUMB, 0,
        AK_ORBIT, FX_SPARK_B, FX_SPARK_A, 4, RGB15(31, 30, 10), RGB15(28, 31, 31),
        "A field of pins and needles that numbs the foe."),

    /* ---------------- FROST ---------------- */
    [M_FLURRY] = MV("FLURRY", T_FROST, CAT_SPEC, 40, 100, 25, 0, EF_STATUS, 10, STATUS_FRZ, 0,
        AK_RAIN, FX_SNOWFLAKE, FX_SPARKLE, 6, RGB15(24, 30, 31), RGB15(31, 31, 31),
        "A swirl of snow. May freeze the foe."),
    [M_RIME_SHOT] = MV("RIME SHOT", T_FROST, CAT_PHYS, 40, 100, 30, 1, EF_NONE, 0, 0, 0,
        AK_PROJECTILE, FX_SHARD, FX_SPARKLE, 2, RGB15(16, 28, 31), RGB15(28, 31, 31),
        "A dart of rime ice. Always strikes first."),
    [M_WINTER_RAY] = MV("WINTER RAY", T_FROST, CAT_SPEC, 90, 100, 10, 0, EF_STATUS, 10, STATUS_FRZ, 0,
        AK_BEAM, FX_BEAM, FX_SNOWFLAKE, 1, RGB15(14, 28, 31), RGB15(28, 31, 31),
        "A ray that frosts all it touches. May freeze."),

    /* ---------------- BRAWL ---------------- */
    [M_HAMMER_FIST] = MV("HAMMER FIST", T_BRAWL, CAT_PHYS, 50, 100, 25, 0, EF_HIGHCRIT, 100, 0, 0,
        AK_STRIKE, FX_FIST, FX_IMPACT, 1, RGB15(30, 22, 14), RGB15(31, 31, 28),
        "An overhead fist. Often a perfect strike."),
    [M_ONE_TWO] = MV("ONE-TWO", T_BRAWL, CAT_PHYS, 30, 100, 30, 0, EF_TWICE, 100, 0, 0,
        AK_STRIKE, FX_FIST, FX_IMPACT, 2, RGB15(28, 18, 10), RGB15(31, 31, 28),
        "A jab and a cross. Hits twice."),
    [M_HAYMAKER] = MV("HAYMAKER", T_BRAWL, CAT_PHYS, 100, 80, 5, 0, EF_HIGHCRIT, 100, 0, 0,
        AK_HAYMAKER, FX_FIST, FX_IMPACT, 1, RGB15(30, 14, 6), RGB15(31, 30, 20),
        "A huge wind-up swing. Often a perfect strike."),

    /* ---------------- VENOM ---------------- */
    [M_BARB] = MV("BARB", T_VENOM, CAT_PHYS, 35, 100, 35, 0, EF_STATUS, 30, STATUS_PSN, 0,
        AK_PROJECTILE, FX_NEEDLE, FX_TEAR, 1, RGB15(24, 10, 28), RGB15(31, 28, 31),
        "A dripping barb. May poison the foe."),
    [M_SPORE_CLOUD] = MV("SPORE CLOUD", T_VENOM, CAT_STATUS, 0, 75, 35, 0, EF_STATUS, 100, STATUS_PSN, 0,
        AK_POWDER, FX_POWDER, FX_STEAM, 8, RGB15(22, 8, 26), RGB15(30, 20, 31),
        "A cloud of purple spores that poisons the foe."),
    [M_BOG_BOMB] = MV("BOG BOMB", T_VENOM, CAT_SPEC, 90, 100, 10, 0, EF_STATUS, 30, STATUS_PSN, 0,
        AK_PROJECTILE, FX_GLOB, FX_SPLAT, 1, RGB15(20, 6, 24), RGB15(28, 16, 30),
        "Lobs a ball of bog muck. May poison."),

    /* ---------------- STONE ---------------- */
    [M_GRIT_KICK] = MV("GRIT KICK", T_STONE, CAT_STATUS, 0, 100, 15, 0, EF_FOE_STAT, 100, STAT_ACC, -1,
        AK_DEBUFF, FX_DUST, FX_PEBBLE, 4, RGB15(28, 24, 14), RGB15(31, 30, 22),
        "Kicks grit into the foe's eyes. Lowers ACCURACY."),
    [M_PEBBLE_PELT] = MV("PEBBLE PELT", T_STONE, CAT_PHYS, 50, 90, 15, 0, EF_NONE, 0, 0, 0,
        AK_PROJECTILE, FX_PEBBLE, FX_IMPACT_SMALL, 5, RGB15(20, 16, 10), RGB15(28, 26, 20),
        "Pelts the foe with a handful of pebbles."),
    [M_MUD_PIE] = MV("MUD PIE", T_STONE, CAT_SPEC, 55, 95, 15, 0, EF_FOE_STAT, 100, STAT_SPE, -1,
        AK_PROJECTILE, FX_GLOB, FX_SPLAT, 1, RGB15(18, 12, 6), RGB15(26, 20, 12),
        "Splats the foe with a mud pie. Lowers SPEED."),
    [M_ROCKFALL] = MV("ROCKFALL", T_STONE, CAT_PHYS, 75, 90, 10, 0, EF_FLINCH, 30, 0, 0,
        AK_RAIN, FX_ROCK, FX_PEBBLE, 5, RGB15(18, 16, 14), RGB15(26, 24, 20),
        "Boulders tumble down. May make the foe flinch."),
    [M_FAULTLINE] = MV("FAULTLINE", T_STONE, CAT_PHYS, 100, 100, 10, 0, EF_NONE, 0, 0, 0,
        AK_FAULT, FX_CRACK, FX_ROCK, 1, RGB15(22, 16, 8), RGB15(30, 26, 16),
        "The ground splits open under the foe."),

    /* ---------------- GALE ---------------- */
    [M_DRAFT] = MV("DRAFT", T_GALE, CAT_SPEC, 40, 100, 35, 0, EF_NONE, 0, 0, 0,
        AK_PROJECTILE, FX_WIND, FX_WIND, 2, RGB15(26, 30, 31), RGB15(31, 31, 31),
        "A sudden cold draft buffets the foe."),
    [M_BEAK_JAB] = MV("BEAK JAB", T_GALE, CAT_PHYS, 35, 100, 35, 0, EF_NONE, 0, 0, 0,
        AK_CONTACT, FX_IMPACT_SMALL, FX_IMPACT_SMALL, 3, RGB15(31, 31, 26), RGB15(31, 26, 10),
        "Rapid jabs with a sharp beak."),
    [M_FEATHER_CUT] = MV("FEATHER CUT", T_GALE, CAT_PHYS, 60, 100, 35, 0, EF_NONE, 0, 0, 0,
        AK_SLASH, FX_SLASH, FX_FEATHER, 2, RGB15(22, 26, 31), RGB15(31, 31, 31),
        "Wing edges slice past; feathers scatter."),
    [M_STOOP] = MV("STOOP", T_GALE, CAT_PHYS, 120, 100, 15, 0, EF_RECOIL, 100, 0, 0,
        AK_STOOP, FX_IMPACT, FX_FEATHER, 1, RGB15(14, 20, 31), RGB15(31, 31, 31),
        "Drops on the foe like a falcon. Jolts the user."),

    /* ---------------- DREAM ---------------- */
    [M_DAYDREAM] = MV("DAYDREAM", T_DREAM, CAT_SPEC, 50, 100, 25, 0, EF_NONE, 0, 0, 0,
        AK_PSYCHIC, FX_RING, FX_SPARKLE, 1, RGB15(31, 14, 24), RGB15(31, 26, 31),
        "Traps the foe in a dizzy daydream."),
    [M_PRISM_RAY] = MV("PRISM RAY", T_DREAM, CAT_SPEC, 65, 100, 20, 0, EF_NONE, 0, 0, 0,
        AK_BEAM, FX_BEAM, FX_SPARKLE, 1, RGB15(30, 12, 28), RGB15(24, 20, 31),
        "A ray split into every colour at once."),
    [M_DREAMQUAKE] = MV("DREAMQUAKE", T_DREAM, CAT_SPEC, 90, 100, 10, 0, EF_FOE_STAT, 10, STAT_SPD, -1,
        AK_WOBBLE, FX_RING, FX_RING, 3, RGB15(31, 10, 22), RGB15(31, 24, 31),
        "The world wobbles like a dream. May lower WILL."),
    [M_STILL_POND] = MV("STILL POND", T_DREAM, CAT_STATUS, 0, 0, 20, 0, EF_SELF_STAT, 100,
        SM(STAT_SPA) | SM(STAT_SPD), 1,
        AK_RIPPLE, FX_RING, FX_DROP, 3, RGB15(20, 24, 31), RGB15(28, 26, 31),
        "Calms its mind like a still pond: FOCUS, WILL up."),

    /* ---------------- SWARM ---------------- */
    [M_SILK_SNARE] = MV("SILK SNARE", T_SWARM, CAT_STATUS, 0, 95, 40, 0, EF_FOE_STAT, 100, STAT_SPE, -2,
        AK_WRAP, FX_THREAD, FX_THREAD, 3, RGB15(29, 29, 31), RGB15(24, 24, 28),
        "Wraps the foe in silk. Sharply lowers SPEED."),
    [M_PINCER] = MV("PINCER", T_SWARM, CAT_PHYS, 60, 100, 20, 0, EF_NONE, 0, 0, 0,
        AK_FANGS, FX_FANG_TOP, FX_IMPACT_SMALL, 1, RGB15(22, 28, 6), RGB15(30, 31, 16),
        "Snaps shut with sharp mandibles."),
    [M_WINGDUST] = MV("WINGDUST", T_SWARM, CAT_SPEC, 60, 100, 5, 0, EF_SELF_STAT, 10, SM_ALL5, 1,
        AK_WAVE, FX_POWDER, FX_SPARKLE, 8, RGB15(26, 26, 30), RGB15(31, 31, 31),
        "Shimmering wing dust. May raise all stats."),

    /* ---------------- DUSK ---------------- */
    [M_SNAP] = MV("SNAP", T_DUSK, CAT_PHYS, 60, 100, 25, 0, EF_FLINCH, 30, 0, 0,
        AK_FANGS, FX_FANG_TOP, FX_IMPACT_SMALL, 1, RGB15(30, 30, 30), RGB15(28, 8, 8),
        "A sudden snap from the shadows. May flinch."),
    [M_STARE_DOWN] = MV("STARE DOWN", T_DUSK, CAT_STATUS, 0, 90, 10, 0, EF_FOE_STAT, 100, STAT_SPE, -2,
        AK_DEBUFF, FX_EYES, FX_EYES, 1, RGB15(26, 24, 4), RGB15(20, 8, 24),
        "Unblinking glowing eyes. Sharply lowers SPEED."),
    [M_GLOOM_ORB] = MV("GLOOM ORB", T_DUSK, CAT_SPEC, 80, 100, 15, 0, EF_FOE_STAT, 20, STAT_SPD, -1,
        AK_PROJECTILE, FX_ORB, FX_WISP, 1, RGB15(14, 6, 20), RGB15(24, 16, 30),
        "An orb of pooled night. May lower WILL."),
    [M_GNASH] = MV("GNASH", T_DUSK, CAT_PHYS, 80, 100, 15, 0, EF_FOE_STAT, 20, STAT_DEF, -1,
        AK_FANGS, FX_FANG_TOP, FX_IMPACT, 2, RGB15(26, 26, 30), RGB15(16, 6, 22),
        "Grinding teeth. May lower the foe's DEFENSE."),

    /* ---------------- WYRM ---------------- */
    [M_WYRMBREATH] = MV("WYRMBREATH", T_WYRM, CAT_SPEC, 60, 100, 20, 0, EF_STATUS, 30, STATUS_NUMB, 0,
        AK_STREAM, FX_FLAME_B, FX_FLAME_A, 12, RGB15(12, 10, 30), RGB15(20, 26, 31),
        "Ancient breath that leaves the foe numb."),
    [M_SCALE_REND] = MV("SCALE REND", T_WYRM, CAT_PHYS, 80, 100, 15, 0, EF_NONE, 0, 0, 0,
        AK_SLASH, FX_CLAW, FX_IMPACT, 2, RGB15(10, 12, 28), RGB15(12, 28, 26),
        "Rends the foe with scaled claws."),
    [M_STARFALL] = MV("STARFALL", T_WYRM, CAT_SPEC, 130, 90, 5, 0, EF_SELF_DOWN, 100, SM(STAT_SPA), -2,
        AK_RAIN, FX_METEOR, FX_IMPACT, 5, RGB15(31, 14, 6), RGB15(22, 10, 30),
        "Calls down fallen stars. Harshly lowers FOCUS."),

    /* ---------------- later additions ---------------- */
    [M_BASK] = MV("BASK", T_BLOOM, CAT_STATUS, 0, 0, 10, 0, EF_HEAL, 100, 0, 0,
        AK_HEAL, FX_SUNRAY, FX_SPARKLE, 5, RGB15(30, 30, 10), RGB15(16, 30, 10),
        "Basks in remembered sunlight. Heals half its HP."),
    [M_CATNAP] = MV("CATNAP", T_BEAST, CAT_STATUS, 0, 0, 10, 0, EF_HEAL, 100, 0, 0,
        AK_HEAL, FX_ZZZ, FX_SPARKLE, 3, RGB15(24, 24, 31), RGB15(31, 31, 31),
        "Curls up for a quick nap. Heals half its HP."),
    [M_FESTER] = MV("FESTER", T_VENOM, CAT_SPEC, 65, 100, 10, 0, EF_PUNISH, 100, 0, 0,
        AK_BURST, FX_GLOB, FX_BUBBLE, 6, RGB15(22, 8, 28), RGB15(16, 28, 10),
        "Twice as strong if the foe has a status problem."),
    [M_HAUNT] = MV("HAUNT", T_DUSK, CAT_SPEC, 70, 100, 10, 0, EF_PUNISH, 100, 0, 0,
        AK_ORBIT, FX_WISP, FX_EYES, 3, RGB15(16, 10, 28), RGB15(28, 24, 31),
        "Twice as strong if the foe has a status problem."),
    [M_LAST_EMBER] = MV("LAST EMBER", T_BLAZE, CAT_PHYS, 40, 100, 10, 0, EF_DESPERATE, 100, 0, 0,
        AK_CONTACT, FX_FLAME_A, FX_FLAME_B, 1, RGB15(31, 14, 2), RGB15(31, 28, 10),
        "The lower its HP, the hotter this ember burns."),
    [M_BRIM_BURST] = MV("BRIM BURST", T_BEAST, CAT_SPEC, 150, 100, 5, 0, EF_BRIM, 100, 0, 0,
        AK_CHARGE, FX_STAR, FX_SPARKLE, 10, RGB15(31, 26, 12), RGB15(31, 31, 28),
        "Spills all its element at once. Weaker when tired."),
    [M_PUMMEL] = MV("PUMMEL", T_BRAWL, CAT_PHYS, 20, 100, 20, 0, EF_MULTI, 100, 0, 0,
        AK_STRIKE, FX_FIST, FX_IMPACT_SMALL, 1, RGB15(30, 20, 12), RGB15(31, 31, 26),
        "A flurry of fists that lands 2 to 5 times."),
    [M_HAILSTONES] = MV("HAILSTONES", T_FROST, CAT_PHYS, 25, 100, 20, 0, EF_MULTI, 100, 0, 0,
        AK_RAIN, FX_SHARD, FX_SNOWFLAKE, 3, RGB15(20, 28, 31), RGB15(30, 31, 31),
        "Hail rattles down 2 to 5 times."),
    [M_BURR_VOLLEY] = MV("BURR VOLLEY", T_BLOOM, CAT_PHYS, 25, 100, 20, 0, EF_MULTI, 100, 0, 0,
        AK_PROJECTILE, FX_BURR, FX_LEAF_B, 2, RGB15(16, 22, 6), RGB15(26, 30, 12),
        "Sticky burrs fly 2 to 5 times."),
    [M_OVERCHARGE] = MV("OVERCHARGE", T_SPARK, CAT_SPEC, 120, 90, 5, 0, EF_SELF_DOWN, 100, SM(STAT_SPA), -2,
        AK_CHARGE, FX_BOLT, FX_SPARK_B, 1, RGB15(31, 31, 8), RGB15(24, 28, 31),
        "Dumps every spark at once. Harshly lowers FOCUS."),
    [M_UPDRAFT] = MV("UPDRAFT", T_GALE, CAT_STATUS, 0, 0, 15, 0, EF_SELF_STAT, 100, SM(STAT_SPE), 2,
        AK_BUFF, FX_WIND, FX_FEATHER, 4, RGB15(24, 30, 31), RGB15(31, 31, 31),
        "Rides a rising wind. Sharply raises SPEED."),
    [M_STONESKIN] = MV("STONESKIN", T_STONE, CAT_STATUS, 0, 0, 15, 0, EF_SELF_STAT, 100, SM(STAT_DEF), 2,
        AK_GUARD, FX_PEBBLE, FX_SPARKLE, 4, RGB15(22, 20, 16), RGB15(30, 28, 22),
        "Its hide hardens to granite. Sharply ups DEFENSE."),
    [M_WAR_CRY] = MV("WAR CRY", T_BRAWL, CAT_STATUS, 0, 0, 15, 0, EF_SELF_STAT, 100, SM(STAT_ATK), 2,
        AK_ROAR, FX_RING, FX_NOTE, 2, RGB15(31, 16, 8), RGB15(31, 28, 16),
        "A bellow that fires it up. Sharply ups ATTACK."),
    [M_UNDERTOW] = MV("UNDERTOW", T_TIDE, CAT_PHYS, 65, 100, 15, 0, EF_FOE_STAT, 100, STAT_SPE, -1,
        AK_WAVE, FX_WAVE, FX_BUBBLE, 4, RGB15(4, 14, 28), RGB15(20, 28, 31),
        "A sudden current drags the foe. Lowers SPEED."),

    [M_LAST_GASP] = MV("LAST GASP", T_BEAST, CAT_PHYS, 50, 0, 1, 0, EF_RECOIL, 100, 0, 0,
        AK_CONTACT, FX_IMPACT, FX_IMPACT_SMALL, 1, RGB15(31, 31, 31), RGB15(31, 20, 20),
        "Used only when out of uses. Hurts the user."),
};
