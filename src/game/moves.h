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
    EF_FOE_STATS, /* param: stat mask, stages (negative) on the foe (several stats) */
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
    /* expansion kinds */
    AK_RATTLE,    /* a cloud of bones jitters round the foe, then clatters in */
    AK_MIST,      /* a cold fog bank rolls along the ground and rises */
    AK_SHROUD,    /* grave mist spirals up and wraps the user */
    AK_TOLL,      /* a bell swings over the foe; every toll sends a ripple */
    AK_CHOIR,     /* spirits rise from the ground, sway and sing, then converge */
    AK_CHOMP,     /* a mimic's jaws open wide around the foe and snap shut */
    AK_WHIRL,     /* things whirl round the foe in a rising tornado, then close in */
    AK_MAGNET,    /* a horseshoe magnet hauls the foe; iron flakes fly to it */
    AK_GEARS,     /* two big gears close in from both sides and grind */
    AK_ANVIL,     /* a shadow grows, then an anvil drops: squash, dust, stars */
    AK_MOONLIT,   /* night falls, the moon rises, a pale shaft falls on the foe */
    AK_MUON,      /* thin streaks of light rain straight through everything */
    AK_METEOR,    /* one huge meteor streaks in: flash, crater, debris */
    AK_NOVA,      /* gathers starlight, the world goes dark, a blinding burst */
    AK_ARC,       /* a jagged arc jumps from the user to the foe */
    AK_DANCE,     /* the user sways and turns; scales spiral up around it */
    /* the RUNE set (anim_rune.c): rotation and pseudo-3D */
    AK_RUNE_BOLT,    /* a spinning rune flies at the foe in perspective and bursts */
    AK_SIGIL_SNARE,  /* a seal opens under the foe; runes rise, circle and clamp down */
    AK_ALGIZ_WARD,   /* two tilted rings of runes spin round the user like a gyroscope */
    AK_KENAZ_FLARE,  /* a fire rune turns, flies over the foe and ignites a pillar */
    AK_RUNE_ORBIT,   /* eight runes orbit the foe on a precessing ring and collapse */
    AK_THURS_SPIKE,  /* runes race along the ground; crystal thorns erupt round the foe */
    AK_RAIDO_RUSH,   /* a rune gate stands up; the user dashes through it */
    AK_ISA_SEAL,     /* an ice seal spins like a coin, slams on and crystals burst */
    AK_SOWILO_BEAM,  /* a sun circle turns to face the foe and fires a beam */
    AK_RUNE_SIPHON,  /* motes and runes spiral out of the foe into the user */
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

    /* ---------------- expansion (docs/EXPANSION.md 5) ---------------- */
    M_BONE_RATTLE, M_GRAVE_CHILL, M_MARROW_SIP, M_SHROUD,
    M_OSSIFY, M_DEATH_KNELL, M_REQUIEM, M_LAST_RITES,
    M_CLATTER, M_TRINKET_TOSS, M_TARNISH, M_GILDED_GLEAM,
    M_CHEST_CHOMP, M_POLTERGUST, M_CURSED_CURIO, M_HEIRLOOM,
    M_IRON_TAP, M_MAGNET_PULL, M_RIVET_SHOT, M_STEEL_SHELL,
    M_GEAR_GRIND, M_LODE_BEAM, M_ANVIL_DROP, M_FORGE_FLASH,
    M_TWINKLE, M_STARDUST, M_MOONBEAM, M_COMET_DASH,
    M_NEBULA_VEIL, M_MUON_RAIN, M_METEOR_FALL, M_SUPERNOVA,
    M_SNARL, M_EMBER_STORM, M_RIPTIDE, M_THORN_WALL,
    M_ARC_FLASH, M_SNOWDRIFT, M_COUNTERJAB, M_ACID_SPIT,
    M_SANDBLAST, M_CROSSWIND, M_LULLABY, M_SWARM_RUSH,
    M_SHADE_CUT, M_WYRM_DANCE,
    /* the RUNE set (docs/EXPANSION.md 5) */
    M_RUNE_BOLT, M_SIGIL_SNARE, M_ALGIZ_WARD, M_KENAZ_FLARE, M_RUNE_ORBIT,
    M_THURS_SPIKE, M_RAIDO_RUSH, M_ISA_SEAL, M_SOWILO_BEAM, M_RUNE_SIPHON,
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

    /* ---------------- expansion ---------------- */
    /* HOLLOW: bone, grave mist and old bells (ivory, ash green, dusk violet) */
    [M_BONE_RATTLE] = MV("BONE RATTLE", T_HOLLOW, CAT_PHYS, 40, 100, 30, 0, EF_FLINCH, 10, 0, 0,
        AK_RATTLE, FX_BONE, FX_IMPACT_SMALL, 5, RGB15(30, 29, 24), RGB15(20, 18, 16),
        "A clattering jab of bone. May make the foe flinch."),
    [M_GRAVE_CHILL] = MV("GRAVE CHILL", T_HOLLOW, CAT_SPEC, 55, 100, 25, 0, EF_FOE_STAT, 20, STAT_SPE, -1,
        AK_MIST, FX_STEAM, FX_SNOWFLAKE, 6, RGB15(18, 22, 26), RGB15(26, 30, 31),
        "A cold draft from under the ground. May lower SPEED."),
    [M_MARROW_SIP] = MV("MARROW SIP", T_HOLLOW, CAT_SPEC, 60, 100, 15, 0, EF_DRAIN, 100, 0, 0,
        AK_DRAIN, FX_WISP, FX_SKULL, 5, RGB15(22, 28, 18), RGB15(30, 29, 24),
        "Draws warmth from the foe and keeps half of it."),
    [M_SHROUD] = MV("SHROUD", T_HOLLOW, CAT_STATUS, 0, 0, 20, 0, EF_SELF_STAT, 100, SM(STAT_DEF) | SM(STAT_SPD), 1,
        AK_SHROUD, FX_WISP, FX_STEAM, 6, RGB15(16, 14, 22), RGB15(26, 24, 28),
        "Wraps itself in grave mist. Raises DEFENSE and WILL."),
    [M_OSSIFY] = MV("OSSIFY", T_HOLLOW, CAT_PHYS, 80, 100, 15, 0, EF_FOE_STAT, 30, STAT_DEF, -1,
        AK_SLAM, FX_BONE, FX_CRACK, 1, RGB15(30, 29, 24), RGB15(22, 20, 16),
        "A blow that stiffens like old bone. May lower DEFENSE."),
    [M_DEATH_KNELL] = MV("DEATH KNELL", T_HOLLOW, CAT_SPEC, 90, 90, 10, 0, EF_STATUS, 20, STATUS_SLP, 0,
        AK_TOLL, FX_BELL, FX_RING, 3, RGB15(22, 18, 10), RGB15(24, 22, 31),
        "A slow bell toll. May put the foe to sleep."),
    [M_REQUIEM] = MV("REQUIEM", T_HOLLOW, CAT_SPEC, 110, 85, 5, 0, EF_NONE, 0, 0, 0,
        AK_CHOIR, FX_SKULL, FX_NOTE, 6, RGB15(26, 26, 22), RGB15(22, 18, 30),
        "A dirge for every kernel that ever went out."),
    [M_LAST_RITES] = MV("LAST RITES", T_HOLLOW, CAT_STATUS, 0, 0, 10, 0, EF_HEAL, 100, 0, 0,
        AK_HEAL, FX_CANDLE, FX_SPARKLE, 5, RGB15(30, 28, 22), RGB15(31, 22, 8),
        "Settles its bones by candlelight. Restores half its HP."),
    /* RELIC: crockery, trinkets and gilt (brass, gold, old lacquer) */
    [M_CLATTER] = MV("CLATTER", T_RELIC, CAT_PHYS, 40, 100, 35, 0, EF_NONE, 0, 0, 0,
        AK_CONTACT, FX_CUP, FX_IMPACT_SMALL, 2, RGB15(30, 28, 24), RGB15(10, 16, 28),
        "Bangs its lid, handle or hinge into the foe."),
    [M_TRINKET_TOSS] = MV("TRINKET TOSS", T_RELIC, CAT_PHYS, 18, 95, 20, 0, EF_MULTI, 100, 0, 0,
        AK_PROJECTILE, FX_TRINKET, FX_COIN, 1, RGB15(28, 22, 8), RGB15(20, 30, 26),
        "Flings odds and ends 2 to 5 times."),
    [M_TARNISH] = MV("TARNISH", T_RELIC, CAT_STATUS, 0, 100, 30, 0, EF_FOE_STAT, 100, STAT_ATK, -1,
        AK_DEBUFF, FX_FLAKE, FX_DUST, 4, RGB15(18, 16, 10), RGB15(12, 20, 14),
        "Dulls the foe with old grime. Lowers ATTACK."),
    [M_GILDED_GLEAM] = MV("GILDED GLEAM", T_RELIC, CAT_SPEC, 70, 100, 15, 0, EF_HIGHCRIT, 100, 0, 0,
        AK_BEAM, FX_BEAM, FX_COIN, 1, RGB15(31, 27, 8), RGB15(31, 22, 4),
        "A flash off polished gold. Often a perfect strike."),
    [M_CHEST_CHOMP] = MV("CHEST CHOMP", T_RELIC, CAT_PHYS, 80, 95, 15, 0, EF_FLINCH, 20, 0, 0,
        AK_CHOMP, FX_COIN, FX_IMPACT, 2, RGB15(24, 16, 8), RGB15(31, 26, 8),
        "Snaps shut like a lid. May make the foe flinch."),
    [M_POLTERGUST] = MV("POLTERGUST", T_RELIC, CAT_SPEC, 65, 100, 20, 0, EF_STATUS, 10, STATUS_NUMB, 0,
        AK_WHIRL, FX_CUP, FX_TRINKET, 6, RGB15(28, 28, 31), RGB15(18, 14, 28),
        "A whirl of flying crockery. May numb the foe."),
    [M_CURSED_CURIO] = MV("CURSED CURIO", T_RELIC, CAT_SPEC, 95, 90, 10, 0, EF_PUNISH, 100, 0, 0,
        AK_LURE, FX_TRINKET, FX_EYES, 2, RGB15(20, 12, 24), RGB15(30, 20, 31),
        "An unlucky trinket. Twice as strong on a troubled foe."),
    [M_HEIRLOOM] = MV("HEIRLOOM", T_RELIC, CAT_PHYS, 120, 100, 5, 0, EF_SELF_DOWN, 100, SM(STAT_DEF) | SM(STAT_SPD), -1,
        AK_HAYMAKER, FX_TRINKET, FX_STAR, 1, RGB15(31, 24, 8), RGB15(31, 31, 24),
        "Swings a century of weight. Lowers its DEF and WILL."),
    /* METAL: iron, rivets, gears and magnets (steel blue, forge orange) */
    [M_IRON_TAP] = MV("IRON TAP", T_METAL, CAT_PHYS, 40, 100, 30, 1, EF_NONE, 0, 0, 0,
        AK_DASH, FX_IMPACT_SMALL, FX_FLAKE, 1, RGB15(24, 26, 28), RGB15(28, 20, 12),
        "A quick rap of iron. Always first."),
    [M_MAGNET_PULL] = MV("MAGNET PULL", T_METAL, CAT_STATUS, 0, 100, 20, 0, EF_FOE_STAT, 100, STAT_SPE, -2,
        AK_MAGNET, FX_MAGNET, FX_FLAKE, 3, RGB15(28, 6, 8), RGB15(26, 28, 31),
        "A magnetic grip slows the foe. Sharply lowers SPEED."),
    [M_RIVET_SHOT] = MV("RIVET SHOT", T_METAL, CAT_PHYS, 20, 95, 20, 0, EF_MULTI, 100, 0, 0,
        AK_PROJECTILE, FX_RIVET, FX_SPARK_B, 1, RGB15(22, 24, 26), RGB15(31, 18, 4),
        "Fires hot rivets 2 to 5 times."),
    [M_STEEL_SHELL] = MV("STEEL SHELL", T_METAL, CAT_STATUS, 0, 0, 15, 0, EF_SELF_STAT, 100, SM(STAT_DEF), 2,
        AK_GUARD, FX_FLAKE, FX_SPARKLE, 6, RGB15(20, 22, 26), RGB15(31, 31, 31),
        "Plates itself in iron. Sharply raises DEFENSE."),
    [M_GEAR_GRIND] = MV("GEAR GRIND", T_METAL, CAT_PHYS, 80, 95, 15, 0, EF_HIGHCRIT, 100, 0, 0,
        AK_GEARS, FX_GEAR, FX_SPARK_A, 2, RGB15(26, 22, 12), RGB15(31, 28, 16),
        "Grinds the foe between gears. Often a perfect strike."),
    [M_LODE_BEAM] = MV("LODE BEAM", T_METAL, CAT_SPEC, 90, 100, 10, 0, EF_FOE_STAT, 10, STAT_SPD, -1,
        AK_BEAM, FX_BEAM, FX_MAGNET, 1, RGB15(12, 14, 31), RGB15(31, 8, 10),
        "A beam of pure magnetism. May lower WILL."),
    [M_ANVIL_DROP] = MV("ANVIL DROP", T_METAL, CAT_PHYS, 110, 85, 5, 0, EF_NONE, 0, 0, 0,
        AK_ANVIL, FX_DUST, FX_STAR, 1, RGB15(16, 17, 20), RGB15(31, 30, 20),
        "Drops something heavy and iron on the foe."),
    [M_FORGE_FLASH] = MV("FORGE FLASH", T_METAL, CAT_SPEC, 60, 100, 20, 0, EF_STATUS, 10, STATUS_BRN, 0,
        AK_BURST, FX_SPARK_A, FX_RIVET, 3, RGB15(31, 20, 6), RGB15(31, 31, 20),
        "A spray of forge sparks. May burn the foe."),
    /* ASTRAL: starlight, moons and falling stars (indigo, silver, gold) */
    [M_TWINKLE] = MV("TWINKLE", T_ASTRAL, CAT_SPEC, 40, 100, 30, 0, EF_NONE, 0, 0, 0,
        AK_PROJECTILE, FX_MOTE, FX_SPARKLE, 3, RGB15(28, 28, 31), RGB15(31, 31, 18),
        "A tiny star darts at the foe."),
    [M_STARDUST] = MV("STARDUST", T_ASTRAL, CAT_STATUS, 0, 90, 20, 0, EF_FOE_STAT, 100, STAT_ACC, -1,
        AK_POWDER, FX_MOTE, FX_SPARKLE, 10, RGB15(28, 26, 31), RGB15(31, 31, 24),
        "Glittering dust in the eyes. Lowers ACCURACY."),
    [M_MOONBEAM] = MV("MOONBEAM", T_ASTRAL, CAT_SPEC, 65, 100, 15, 0, EF_DRAIN, 100, 0, 0,
        AK_MOONLIT, FX_MOON, FX_SUNRAY, 5, RGB15(28, 30, 31), RGB15(22, 24, 31),
        "Pale moonlight that heals the user by half the damage."),
    [M_COMET_DASH] = MV("COMET DASH", T_ASTRAL, CAT_PHYS, 80, 100, 15, 0, EF_RECOIL, 100, 0, 0,
        AK_RUSH, FX_METEOR, FX_MOTE, 1, RGB15(31, 24, 12), RGB15(28, 28, 31),
        "Streaks in like a comet. The user is hurt too."),
    [M_NEBULA_VEIL] = MV("NEBULA VEIL", T_ASTRAL, CAT_STATUS, 0, 0, 15, 0, EF_SELF_STAT, 100, SM(STAT_SPA) | SM(STAT_SPD), 1,
        AK_BUFF, FX_MOTE, FX_ORB, 6, RGB15(20, 14, 28), RGB15(30, 18, 26),
        "Wraps itself in star haze. Raises FOCUS and WILL."),
    [M_MUON_RAIN] = MV("MUON RAIN", T_ASTRAL, CAT_SPEC, 90, 100, 10, 0, EF_FOE_STAT, 10, STAT_DEF, -1,
        AK_MUON, FX_STREAK, FX_SPARKLE, 12, RGB15(24, 28, 31), RGB15(26, 20, 31),
        "Particles from the sky pass through all. May lower DEF."),
    [M_METEOR_FALL] = MV("METEOR FALL", T_ASTRAL, CAT_PHYS, 100, 90, 10, 0, EF_FLINCH, 20, 0, 0,
        AK_METEOR, FX_METEOR, FX_ROCK, 1, RGB15(31, 20, 8), RGB15(22, 18, 14),
        "Calls down a falling star. May make the foe flinch."),
    [M_SUPERNOVA] = MV("SUPERNOVA", T_ASTRAL, CAT_SPEC, 130, 90, 5, 0, EF_SELF_DOWN, 100, SM(STAT_SPA), -2,
        AK_NOVA, FX_STAR, FX_MOTE, 8, RGB15(31, 31, 24), RGB15(31, 24, 12),
        "Bursts like a dying star. Harshly lowers FOCUS."),
    /* new moves of the old types */
    [M_SNARL] = MV("SNARL", T_BEAST, CAT_SPEC, 55, 95, 15, 0, EF_FOE_STAT, 100, STAT_SPA, -1,
        AK_ROAR, FX_RING, FX_EYES, 2, RGB15(30, 26, 18), RGB15(31, 8, 8),
        "A rough growl. Lowers the foe's FOCUS."),
    [M_EMBER_STORM] = MV("EMBER STORM", T_BLAZE, CAT_SPEC, 75, 95, 15, 0, EF_STATUS, 20, STATUS_BRN, 0,
        AK_WHIRL, FX_FLAME_A, FX_FLAME_B, 8, RGB15(31, 14, 2), RGB15(31, 28, 10),
        "A whirl of embers. May burn the foe."),
    [M_RIPTIDE] = MV("RIPTIDE", T_TIDE, CAT_PHYS, 75, 100, 15, 0, EF_NONE, 0, 0, 0,
        AK_RUSH, FX_WAVE, FX_DROP, 1, RGB15(4, 14, 28), RGB15(20, 28, 31),
        "Rides a hard current into the foe."),
    [M_THORN_WALL] = MV("THORN WALL", T_BLOOM, CAT_STATUS, 0, 0, 15, 0, EF_SELF_STAT, 100, SM(STAT_DEF) | SM(STAT_SPD), 1,
        AK_GUARD, FX_VINE, FX_LEAF_A, 5, RGB15(10, 22, 6), RGB15(20, 30, 12),
        "Grows a hedge of thorns. Raises DEFENSE and WILL."),
    [M_ARC_FLASH] = MV("ARC FLASH", T_SPARK, CAT_SPEC, 70, 100, 15, 0, EF_STATUS, 20, STATUS_NUMB, 0,
        AK_ARC, FX_BOLT, FX_SPARK_B, 2, RGB15(26, 28, 31), RGB15(31, 31, 8),
        "A blinding arc. May numb the foe."),
    [M_SNOWDRIFT] = MV("SNOWDRIFT", T_FROST, CAT_STATUS, 0, 90, 20, 0, EF_FOE_STATS, 100, SM(STAT_SPE) | SM(STAT_ACC), -1,
        AK_POWDER, FX_SNOWFLAKE, FX_DUST, 8, RGB15(26, 30, 31), RGB15(31, 31, 31),
        "Buries the foe in snow. Lowers SPEED and ACCURACY."),
    [M_COUNTERJAB] = MV("COUNTERJAB", T_BRAWL, CAT_PHYS, 60, 100, 20, 1, EF_NONE, 0, 0, 0,
        AK_DASH, FX_FIST, FX_SPEEDLINE, 1, RGB15(31, 24, 16), RGB15(31, 31, 26),
        "A snap jab thrown before the foe moves."),
    [M_ACID_SPIT] = MV("ACID SPIT", T_VENOM, CAT_SPEC, 60, 100, 20, 0, EF_FOE_STAT, 30, STAT_SPD, -1,
        AK_PROJECTILE, FX_DROP, FX_STEAM, 3, RGB15(18, 26, 4), RGB15(28, 30, 14),
        "Sour spit that sizzles. May lower the foe's WILL."),
    [M_SANDBLAST] = MV("SANDBLAST", T_STONE, CAT_SPEC, 70, 95, 15, 0, EF_FOE_STAT, 20, STAT_ACC, -1,
        AK_STREAM, FX_DUST, FX_PEBBLE, 4, RGB15(28, 24, 14), RGB15(31, 28, 20),
        "A blast of grit. May lower ACCURACY."),
    [M_CROSSWIND] = MV("CROSSWIND", T_GALE, CAT_SPEC, 75, 100, 15, 0, EF_HIGHCRIT, 100, 0, 0,
        AK_SLASH, FX_WIND, FX_FEATHER, 2, RGB15(24, 30, 31), RGB15(31, 31, 31),
        "Two gusts cross at the foe. Often a perfect strike."),
    [M_LULLABY] = MV("LULLABY", T_DREAM, CAT_STATUS, 0, 60, 15, 0, EF_STATUS, 100, STATUS_SLP, 0,
        AK_ORBIT, FX_NOTE, FX_ZZZ, 4, RGB15(30, 20, 28), RGB15(28, 28, 31),
        "A soft song that puts the foe to sleep."),
    [M_SWARM_RUSH] = MV("SWARM RUSH", T_SWARM, CAT_PHYS, 75, 100, 15, 0, EF_NONE, 0, 0, 0,
        AK_RUSH, FX_BUG, FX_IMPACT_SMALL, 5, RGB15(20, 24, 6), RGB15(28, 30, 14),
        "A buzzing rush of wings and legs."),
    [M_SHADE_CUT] = MV("SHADE CUT", T_DUSK, CAT_PHYS, 70, 100, 15, 0, EF_HIGHCRIT, 100, 0, 0,
        AK_SLASH, FX_SLASH, FX_WISP, 1, RGB15(14, 8, 20), RGB15(26, 20, 31),
        "A cut from the dark. Often a perfect strike."),
    [M_WYRM_DANCE] = MV("WYRM DANCE", T_WYRM, CAT_STATUS, 0, 0, 15, 0, EF_SELF_STAT, 100, SM(STAT_ATK) | SM(STAT_SPE), 1,
        AK_DANCE, FX_SCALE, FX_SPARKLE, 6, RGB15(16, 10, 30), RGB15(12, 28, 26),
        "An ancient coiling dance. Raises ATTACK and SPEED."),

    /* the RUNE set: runes of the elder row, circles and seals (anim_rune.c) */
    [M_RUNE_BOLT] = MV("RUNE BOLT", T_ASTRAL, CAT_SPEC, 50, 100, 25, 0, EF_NONE, 0, 0, 0,
        AK_RUNE_BOLT, FX_STAR, FX_SPARKLE, 1, RGB15(18, 11, 29), RGB15(11, 26, 31),
        "A spinning rune flung like a spear of light."),
    [M_SIGIL_SNARE] = MV("SIGIL SNARE", T_RELIC, CAT_STATUS, 0, 95, 20, 0, EF_FOE_STAT, 100, STAT_SPE, -2,
        AK_SIGIL_SNARE, FX_RING, FX_SPARKLE, 1, RGB15(24, 9, 25), RGB15(31, 15, 29),
        "A seal opens under the foe. Sharply lowers SPEED."),
    [M_ALGIZ_WARD] = MV("ALGIZ WARD", T_RELIC, CAT_STATUS, 0, 0, 15, 0, EF_SELF_STAT, 100, SM(STAT_DEF) | SM(STAT_SPD), 1,
        AK_ALGIZ_WARD, FX_SPARKLE, FX_RING, 1, RGB15(6, 21, 20), RGB15(31, 26, 12),
        "Rings of warding runes. Raises DEFENSE and WILL."),
    [M_KENAZ_FLARE] = MV("KENAZ FLARE", T_BLAZE, CAT_SPEC, 80, 100, 15, 0, EF_STATUS, 10, STATUS_BRN, 0,
        AK_KENAZ_FLARE, FX_FLAME_A, FX_FLAME_B, 1, RGB15(28, 10, 2), RGB15(31, 21, 5),
        "The torch rune kindles under the foe. May burn."),
    [M_RUNE_ORBIT] = MV("RUNE ORBIT", T_ASTRAL, CAT_SPEC, 110, 85, 5, 0, EF_NONE, 0, 0, 0,
        AK_RUNE_ORBIT, FX_STAR, FX_RING, 8, RGB15(18, 11, 29), RGB15(24, 31, 31),
        "Eight runes circle the foe, faster, then collapse."),
    [M_THURS_SPIKE] = MV("THURS SPIKE", T_STONE, CAT_PHYS, 85, 95, 10, 0, EF_HIGHCRIT, 100, 0, 0,
        AK_THURS_SPIKE, FX_ROCK, FX_CRACK, 5, RGB15(21, 13, 7), RGB15(29, 12, 9),
        "Thorn runes burst up as crystal. Often perfect."),
    [M_RAIDO_RUSH] = MV("RAIDO RUSH", T_RELIC, CAT_PHYS, 70, 100, 15, 0, EF_SELF_STAT, 100, SM(STAT_SPE), 1,
        AK_RAIDO_RUSH, FX_IMPACT, FX_SPEEDLINE, 1, RGB15(7, 20, 27), RGB15(27, 31, 31),
        "Dashes through a rune gate. Raises the user's SPEED."),
    [M_ISA_SEAL] = MV("ISA SEAL", T_FROST, CAT_SPEC, 70, 100, 15, 0, EF_STATUS, 10, STATUS_FRZ, 0,
        AK_ISA_SEAL, FX_SHARD, FX_SNOWFLAKE, 1, RGB15(11, 18, 27), RGB15(27, 31, 31),
        "The ice rune seals the foe in frost. May freeze."),
    [M_SOWILO_BEAM] = MV("SOWILO BEAM", T_RELIC, CAT_SPEC, 90, 100, 10, 0, EF_STATUS, 10, STATUS_BRN, 0,
        AK_SOWILO_BEAM, FX_BEAM, FX_SUNRAY, 1, RGB15(29, 20, 4), RGB15(31, 30, 22),
        "The sun rune opens and fires a beam. May burn."),
    [M_RUNE_SIPHON] = MV("RUNE SIPHON", T_ASTRAL, CAT_SPEC, 75, 100, 10, 0, EF_DRAIN, 100, 0, 0,
        AK_RUNE_SIPHON, FX_MOTE, FX_SPARKLE, 1, RGB15(10, 23, 15), RGB15(22, 16, 31),
        "Draws the foe's glow out rune by rune. Heals half."),

    [M_LAST_GASP] = MV("LAST GASP", T_BEAST, CAT_PHYS, 50, 0, 1, 0, EF_RECOIL, 100, 0, 0,
        AK_CONTACT, FX_IMPACT, FX_IMPACT_SMALL, 1, RGB15(31, 31, 31), RGB15(31, 20, 20),
        "Used only when out of uses. Hurts the user."),
};
