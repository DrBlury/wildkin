/*
 * Battle engine (bouts).
 *
 * A turn is resolved immediately (damage, status, dozing are decided by
 * the rules in monster.c and the traits below) but everything the player
 * SEES is queued as events: messages, the move animation, the target's
 * hit reaction, the HP bar draining, dozing off, XP filling. The HUD draws
 * "display" values that only change when those events play, so damage
 * appears exactly when the attack lands instead of the moment a move is
 * chosen.
 *
 * Public hooks for the field and story scripts:
 *   battle_start_wild(Monster)              a brimming wild kin. A legend
 *                                           (R_LEGEND) gets the legend intro
 *                                           (shake, roar) and no_run by itself
 *   battle_start_legend(Monster, scene)     the same, with its lair's scene
 *                                           (BSCENE_LAIR, or BSCENE_AREA)
 *   battle_start_trainer_team(&TrainerTeam) a warden with a fixed team (1..6
 *                                           kin); flags TT_MASTER makes it a
 *                                           Hall Master bout (banner, finale)
 *   battle_start_master(&TrainerTeam)       the same with TT_MASTER set
 *   battle_start_trainer()                  WARDEN MARLO's random team
 *   battle_next_scene = BSCENE_*            background for the next bout
 *   battle.no_run = 1                       story bout: running is refused
 *   battle.on_water = 1                     the bout is on water (surfing):
 *                                           TIDE LANTERN bonus
 *   battle_end_hook = fn                    called once when the bout ends
 *   battle_music_hook = fn                  music cues (BCUE_*), see below
 * (no_run, on_water and the end hook may be set before or after
 * battle_start_*; they are cleared when the bout ends.)
 *
 * Meal buffs (craft.c) are read here: extra starting stages for every kin
 * sent out, XP and lantern bonuses, and meal_bout_finished() once a bout
 * ends. opt.battle_speed plays the event queue and the animations at double
 * speed (battle_ui.c / anim.c).
 */

enum { SIDE_ALLY, SIDE_ENEMY };
enum { BK_WILD, BK_TRAINER };
enum { BR_NONE, BR_WIN, BR_LOSE, BR_RUN, BR_CAUGHT };

enum {
    BST_INTRO, BST_EVENTS, BST_ACTION, BST_MOVES, BST_BAG, BST_PARTY,
    BST_FORCED, BST_END
};

/* Battle backgrounds (gfx_battle.h: bbg_scenes, same order). The field
 * sets battle_next_scene for its area (script.c set_battle_scene). */
enum {
    BSCENE_MEADOW, BSCENE_FOREST, BSCENE_LAKE, BSCENE_RING, BSCENE_STORM,
    BSCENE_CITY, BSCENE_COAST, BSCENE_SEA, BSCENE_SNOW, BSCENE_CAVE, BSCENE_GRIM,
    BSCENE_CRYPT, BSCENE_VOLCANO, BSCENE_DREAM, BSCENE_FARM, BSCENE_LAIR,
    BSCENE_COUNT
};
#define BSCENE_AREA 0xFF        /* TrainerTeam.scene: use battle_next_scene */
/* every BSCENE_* has a painted background (tools/bout_scenes.py) */
typedef char BattleScenesPainted[BSCENE_COUNT == BBG_SCENE_COUNT ? 1 : -1];
static int battle_next_scene = BSCENE_MEADOW;

/* Called once from battle_exit (result = BR_*) before returning to the
 * field, then cleared. */
static void (*battle_end_hook)(int result);

/*
 * Music cues for the music module (it sets the pointer; bouts work without
 * it). START_* when a bout begins, WIN / MASTER_WIN / CAUGHT / LOSE / RUN
 * when it is decided, END when the bout closes. A Hall Master win also
 * plays the PSG fanfare SFX_VICTORY, which ducks the music by itself.
 */
enum {
    BCUE_START_WILD, BCUE_START_WARDEN, BCUE_START_MASTER, BCUE_START_LEGEND,
    BCUE_WIN, BCUE_MASTER_WIN, BCUE_CAUGHT, BCUE_LOSE, BCUE_RUN, BCUE_END,
};
static void (*battle_music_hook)(int cue);

static void battle_cue(int cue)
{
    if (battle_music_hook) battle_music_hook(cue);
}

/* Meal buffs (craft.c, later in the unity build). */
static int meal_stat_stage(int stat);
static int meal_xp_percent(void);
static int meal_catch_bonus(void);
static void meal_bout_finished(void);

#define TEAM_MAX 6
typedef char TeamMaxMatchesField[TEAM_MAX == TRAINER_TEAM_MAX ? 1 : -1];

enum { TT_MASTER = 1 };   /* TrainerTeam.flags */

/* A warden's team (1..6 kin). `name` is shown as "WARDEN <name>" (or "HALL
 * MASTER <name>" with TT_MASTER) unless it already contains a space
 * ("KEEPER LINDEN"); lose_line is said when you win. */
typedef struct {
    const char *name;
    u8 count;
    u8 species[TEAM_MAX];
    u8 level[TEAM_MAX];
    u16 prize;
    u8 scene;
    const char *lose_line;
    u8 flags;             /* TT_* */
    u8 look;              /* bout portrait: 1 + KP_* (0: by the scene) */
    u8 vary;              /* its colour variation (0: by the name) */
} TrainerTeam;

/* Bout-portrait actions (keeper.c), EV_PORTRAIT a. */
enum { PA_NONE, PA_ENTER, PA_IDLE, PA_FLAIR, PA_THROW, PA_LEAVE, PA_RETURN };

enum {
    EV_TEXT,      /* a: MSGM_* mode */
    EV_ANIM,      /* a: move id, b: hit index | HITF_* */
    EV_HIT,       /* side reacts to a hit (skipped if the animation landed it) */
    EV_HP,        /* side's bar drains/fills to a */
    EV_FAINT,     /* side dozes off */
    EV_STAT,      /* a: +1 up / -1 down */
    EV_STATUS,    /* a: status (sync badge + small effect) */
    EV_SEND_OUT,  /* ally: a = party slot; enemy: a = team index */
    EV_WITHDRAW,
    EV_LANTERN,   /* a: shakes (4 = befriended), b: lantern kind */
    EV_XP,        /* a: party slot, b: amount */
    EV_LEARN,     /* a: party slot, b: move */
    EV_SYNC,      /* refresh display of side from the real kin */
    EV_MONEY,     /* a: amount */
    EV_END,       /* a: result */
    EV_TRAIT,     /* side's trait kicked in: glow + chime */
    EV_FLEE,      /* the ally scampers off */
    EV_SFX,       /* a: SFX_* */
    EV_BANNER,    /* a Hall Master's banner slides across (text = the title) */
    EV_LEGEND,    /* a legend rears up: roar, shockwaves, heavy shake */
    EV_CUE,       /* a: BCUE_* for the music module */
    EV_NAME,      /* a befriended kin may get a name: a = 0 team / 1 Shelf, b = its slot */
    EV_PORTRAIT,  /* side's portrait: a = PA_*, b = the frame PA_RETURN settles in */
};

/* EV_ANIM b flags (low byte = hit index). */
#define HITF_CRIT   0x0100
#define HITF_WEAK   0x0200
#define HITF_RESIST 0x0400
#define HITF_KO     0x0800
#define HITF_MISS   0x1000
#define HITF_LAST   0x2000
#define HITF_NODMG  0x4000

#define BEV_MAX 96
#define BEV_TEXT 96

typedef struct {
    u8 type, side;
    s16 a, b;
    char text[BEV_TEXT];
} BEvent;

static struct {
    int kind;
    Monster team[TEAM_MAX];
    int team_count, team_idx;
    int ally;                 /* party slot in battle */
    s8 stages[2][STAT_COUNT];
    u8 flinch[2];
    u8 participants;          /* party slots that fought the current foe */
    u8 fought;                /* party slots that took part in this bout */
    u8 no_run;                /* story bouts: running is refused */
    u8 on_water;              /* the bout is on water (TIDE LANTERN) */
    u8 master;                /* a Hall Master bout */
    u8 legend;                /* a legendary encounter */
    u8 foe_entered;           /* turn the current foe came out (AI switching) */
    u8 foe_switches;          /* times the warden switched this bout */
    u8 move_cursor_of[6];     /* last move chosen by each party slot */
    int turn;
    int scene;                /* BSCENE_* */
    char foe_title[24];       /* "WARDEN MARLO" */
    const char *lose_line;
    int state, return_state;
    int cursor, move_cursor, bag_cursor, bag_scroll;
    int escape_tries;
    int result;
    int prize;
    int timer;

    BEvent ev[BEV_MAX];
    int ev_count;
    int ev_started;
    int ev_timer;

    /* what the screen shows */
    struct {
        int species, level, hp, max_hp, status, lustrous;
        char name[KIN_NAME_LEN + 1]; /* what the HUD calls it */
        int visible, slide, drop, blink;
        int hp_from, hp_t, hp_dur;   /* eased HP drain */
        int trail, trail_hold;       /* the lighter "lost HP" chunk */
        int jolt;                    /* HUD jolt frames */
        int pop;                     /* pop-in timer after a lantern opens (0 = done) */
        int shrink;                  /* 0..256 shrinking into a lantern */
        int inlantern;               /* not out of its lantern yet */
        int fade;                    /* dozing: 0..16 */
        int caught;                  /* wild foe's species is befriended */
        u16 pal[16];                 /* sprite palette (lustre applied) */
    } disp[2];
    u32 disp_xp;
    int hud_dirty;
    int ui_dirty;
    int lantern_kind;
    int lantern_frame, lantern_x, lantern_y, lantern_visible, lantern_glow;
    int impacted;             /* side + 1 the last animation already hit, 0 none */
} battle EWRAM_BSS;

static Monster *side_mon(int side)
{
    return side == SIDE_ALLY ? &party[battle.ally] : &battle.team[battle.team_idx];
}

/* ---------------- event queue ---------------- */

static BEvent *bev_push(int type, int side, int a, int b)
{
    if (battle.ev_count >= BEV_MAX) return &battle.ev[BEV_MAX - 1];
    BEvent *e = &battle.ev[battle.ev_count++];
    e->type = (u8)type;
    e->side = (u8)side;
    e->a = (s16)a;
    e->b = (s16)b;
    e->text[0] = 0;
    return e;
}

/* Insert right after the event that is currently playing. */
static BEvent *bev_insert_next(int type, int side, int a, int b, int offset)
{
    if (battle.ev_count >= BEV_MAX) return &battle.ev[BEV_MAX - 1];
    int at = 1 + offset;
    if (at > battle.ev_count) at = battle.ev_count;
    for (int i = battle.ev_count; i > at; i--) battle.ev[i] = battle.ev[i - 1];
    battle.ev_count++;
    BEvent *e = &battle.ev[at];
    e->type = (u8)type;
    e->side = (u8)side;
    e->a = (s16)a;
    e->b = (s16)b;
    e->text[0] = 0;
    return e;
}

static void bev_text(const char *s, int mode)
{
    BEvent *e = bev_push(EV_TEXT, 0, mode, 0);
    str_copy(e->text, s);
}

static void bsay(const char *s)
{
    bev_text(s, MSGM_AUTO);
}

static void bsay_wait(const char *s)
{
    bev_text(s, MSGM_WAIT);
}

/* "Wild FLARIX" / "Foe FLARIX" / "FLARIX" */
static void side_name(char *dst, int side)
{
    dst[0] = 0;
    if (side == SIDE_ENEMY) str_copy(dst, battle.kind == BK_WILD ? "Wild " : "Foe ");
    str_put(dst, kin_name(side_mon(side)));
}

/* "<name><rest>" in one message. */
static void bsay_side(int side, const char *rest)
{
    char msg[BEV_TEXT];
    side_name(msg, side);
    str_put(msg, rest);
    bsay(msg);
}

/* "<name>'s <TRAIT> <rest>" with the trait glow. */
static void trait_say(int side, const char *rest)
{
    char msg[BEV_TEXT];
    bev_push(EV_TRAIT, side, 0, 0);
    side_name(msg, side);
    str_put(msg, "'s ");
    str_put(msg, TRAITS[side_mon(side)->trait].name);
    str_put(msg, " ");
    str_put(msg, rest);
    bsay(msg);
}

static int has_trait(int side, int trait)
{
    return side_mon(side)->trait == trait;
}

/* ---------------- rules ---------------- */

static int status_immune(const Monster *m, int status)
{
    if (status == STATUS_BRN) return species_has_type(m->species, T_BLAZE);
    /* poison can't touch the dead or iron (docs/EXPANSION.md 2) */
    if (status == STATUS_PSN)
        return species_has_type(m->species, T_VENOM) || species_has_type(m->species, T_HOLLOW) ||
               species_has_type(m->species, T_METAL);
    if (status == STATUS_FRZ) return species_has_type(m->species, T_FROST);
    if (status == STATUS_NUMB) return species_has_type(m->species, T_SPARK);
    if (status == STATUS_SLP) return m->trait == TR_WAKEFUL;
    return 0;
}

static const char *const STATUS_INFLICT[STATUS_COUNT] = {
    "", " was burned!", " was poisoned!", " is numb! It may not be able to move!",
    " fell asleep!", " was frozen solid!",
};

static const char *const STATUS_WORD[STATUS_COUNT] = {
    "", "burn", "poison", "numbness", "sleepiness", "frost",
};

static void inflict_status(int side, int status)
{
    Monster *m = side_mon(side);
    m->status = (u8)status;
    if (status == STATUS_SLP) m->sleep_turns = (u8)(1 + rng_range(3));
    bev_push(EV_STATUS, side, status, 0);
    bsay_side(side, STATUS_INFLICT[status]);
}

static void cure_status(int side)
{
    side_mon(side)->status = STATUS_NONE;
    bev_push(EV_STATUS, side, STATUS_NONE, 0);
}

/* Change a stat stage; `quiet` skips the standard message. Returns 1 if
 * the stage moved. */
static int change_stat_ex(int side, int stat, int stages, int quiet)
{
    char msg[BEV_TEXT];
    s8 *st = &battle.stages[side][stat];
    side_name(msg, side);
    str_put(msg, "'s ");
    str_put(msg, STAT_NAMES[stat]);
    if ((stages > 0 && *st >= 6) || (stages < 0 && *st <= -6)) {
        if (!quiet) {
            str_put(msg, stages > 0 ? " won't go higher!" : " won't go lower!");
            bsay(msg);
        }
        return 0;
    }
    *st = (s8)clampi(*st + stages, -6, 6);
    bev_push(EV_STAT, side, stages > 0 ? 1 : -1, 0);
    if (!quiet) {
        str_put(msg, stages >= 2 ? " sharply rose!" : stages > 0 ? " rose!" :
                     stages <= -2 ? " harshly fell!" : " fell!");
        bsay(msg);
    }
    return 1;
}

static void change_stat(int side, int stat, int stages)
{
    change_stat_ex(side, stat, stages, 0);
}

static void damage_side(int side, int amount)
{
    Monster *m = side_mon(side);
    int hp = m->hp - amount;
    m->hp = (u16)(hp < 0 ? 0 : hp);
    bev_push(EV_HP, side, m->hp, 0);
}

static void heal_side(int side, int amount)
{
    Monster *m = side_mon(side);
    int hp = m->hp + amount;
    m->hp = (u16)(hp > m->max_hp ? m->max_hp : hp);
    bev_push(EV_HP, side, m->hp, 0);
}

static void bond_add(Monster *m, int d)
{
    m->bond = (u8)clampi(m->bond + d, 0, 255);
}

static int bond_high(int side)
{
    return side == SIDE_ALLY && side_mon(side)->bond >= 200;
}

static void check_faint(int side)
{
    Monster *m = side_mon(side);
    if (m->hp > 0) return;
    bev_push(EV_FAINT, side, 0, 0);
    char msg[BEV_TEXT];
    side_name(msg, side);
    str_put(msg, " dozed off!");
    bsay_wait(msg);
    if (side == SIDE_ALLY) bond_add(m, -3);
}

/* Can the battler act this turn? Queues the reason if not. */
static int can_act(int side)
{
    Monster *m = side_mon(side);
    if (m->status == STATUS_SLP) {
        if (m->sleep_turns > 0) m->sleep_turns--;
        if (m->sleep_turns > 0) {
            bev_push(EV_STATUS, side, STATUS_SLP, 1);
            bsay_side(side, " is fast asleep.");
            return 0;
        }
        cure_status(side);
        bsay_side(side, " woke up!");
    } else if (m->status == STATUS_FRZ) {
        if (rng_range(5) == 0) {
            cure_status(side);
            bsay_side(side, " thawed out!");
        } else {
            bev_push(EV_STATUS, side, STATUS_FRZ, 1);
            bsay_side(side, " is frozen solid!");
            return 0;
        }
    } else if (m->status == STATUS_NUMB && rng_range(4) == 0) {
        bev_push(EV_STATUS, side, STATUS_NUMB, 1);
        bsay_side(side, " is numb! It can't move!");
        return 0;
    }
    if (battle.flinch[side]) {
        bsay_side(side, " flinched!");
        return 0;
    }
    return 1;
}

static void apply_secondary(int side, const Move *mv)
{
    int foe = !side;
    Monster *def = side_mon(foe);
    if (mv->effect == EF_NONE || mv->effect == EF_HIGHCRIT || mv->effect == EF_TWICE ||
        mv->effect == EF_DRAIN || mv->effect == EF_RECOIL || mv->effect == EF_PUNISH ||
        mv->effect == EF_DESPERATE || mv->effect == EF_BRIM || mv->effect == EF_MULTI ||
        mv->effect == EF_HEAL)
        return;
    if ((int)rng_range(100) >= mv->chance) return;
    switch (mv->effect) {
    case EF_STATUS:
        if (def->hp > 0 && def->status == STATUS_NONE && !status_immune(def, mv->param))
            inflict_status(foe, mv->param);
        break;
    case EF_FLINCH:
        if (def->hp > 0) battle.flinch[foe] = 1;
        break;
    case EF_FOE_STAT:
        if (def->hp > 0) change_stat(foe, mv->param, mv->stages);
        break;
    case EF_FOE_STATS:
        if (def->hp == 0) break;
        for (int s = 0; s < STAT_COUNT; s++)
            if (mv->param & SM(s)) change_stat(foe, s, mv->stages);
        break;
    case EF_SELF_STAT:
    case EF_SELF_DOWN:
        if (side_mon(side)->hp == 0) break;
        for (int s = 0; s < STAT_COUNT; s++)
            if (mv->param & SM(s)) change_stat(side, s, mv->stages);
        break;
    }
}

/* 2-5 hits: 2 and 3 are common, 4 and 5 rarer. */
static int multi_hit_count(void)
{
    int r = (int)rng_range(20);
    return r < 7 ? 2 : r < 14 ? 3 : r < 17 ? 4 : 5;
}

static int move_hits(int side, const Move *mv)
{
    if (mv->acc == 0) return 1;
    int acc = apply_acc_stage(mv->acc, battle.stages[side][STAT_ACC]);
    return (int)rng_range(100) < acc;
}

/* SOAKER / CONDUCTOR: moves of that type restore 1/4 HP instead. */
static int trait_absorbs(const Monster *def, int move)
{
    int t = MOVES[move].type;
    return (def->trait == TR_SOAKER && t == T_TIDE) || (def->trait == TR_CONDUCTOR && t == T_SPARK);
}

/* Does this move land on the foe at all (status moves included)? */
static int move_targets_foe(const Move *mv)
{
    return mv->cat != CAT_STATUS || mv->effect == EF_STATUS || mv->effect == EF_FOE_STAT ||
           mv->effect == EF_FOE_STATS;
}

/* Handles absorbing and floating traits; returns 1 if the move was stopped. */
static int trait_blocks_move(int side, int move)
{
    int foe = !side;
    Monster *def = side_mon(foe);
    if (move == M_LAST_GASP) return 0;
    if (trait_absorbs(def, move)) {
        bev_push(EV_ANIM, side, move, HITF_NODMG | HITF_LAST);
        if (def->hp < def->max_hp) {
            heal_side(foe, def->max_hp / 4 > 0 ? def->max_hp / 4 : 1);
            trait_say(foe, "drank in the blow and recovered!");
        } else {
            trait_say(foe, "drank in the blow harmlessly!");
        }
        return 1;
    }
    if (def->trait == TR_DRIFTER && MOVES[move].type == T_STONE) {
        trait_say(foe, "kept it floating clear!");
        return 1;
    }
    return 0;
}

/* STATIC FUR / EMBERSKIN / SPORESKIN: physical attackers may catch it. */
static void contact_traits(int side, const Move *mv)
{
    int foe = !side;
    Monster *att = side_mon(side), *def = side_mon(foe);
    if (mv->cat != CAT_PHYS || att->hp == 0 || att->status != STATUS_NONE) return;
    int st = def->trait == TR_STATIC_FUR ? STATUS_NUMB : def->trait == TR_EMBERSKIN ? STATUS_BRN :
             def->trait == TR_SPORESKIN ? STATUS_PSN : STATUS_NONE;
    if (st == STATUS_NONE || status_immune(att, st) || rng_range(10) >= 3) return;
    trait_say(foe, st == STATUS_NUMB ? "crackled!" : st == STATUS_BRN ? "flared!" : "puffed spores!");
    inflict_status(side, st);
}

static void use_status_move(int side, int move)
{
    int foe = !side;
    Monster *att = side_mon(side), *def = side_mon(foe);
    const Move *mv = &MOVES[move];
    if (move_targets_foe(mv) && trait_blocks_move(side, move)) return;
    if (mv->effect == EF_STATUS) {
        if (def->status == STATUS_NONE && mv->param == STATUS_SLP && def->trait == TR_WAKEFUL) {
            trait_say(foe, "kept it wide awake!");
            return;
        }
        if (def->status != STATUS_NONE || status_immune(def, mv->param) ||
            type_effectiveness(mv->type, def->species) == 0) {
            bsay("But it failed!");
            return;
        }
        bev_push(EV_ANIM, side, move, HITF_NODMG | HITF_LAST);
        inflict_status(foe, mv->param);
    } else if (mv->effect == EF_FOE_STAT) {
        bev_push(EV_ANIM, side, move, HITF_NODMG | HITF_LAST);
        change_stat(foe, mv->param, mv->stages);
    } else if (mv->effect == EF_FOE_STATS) {
        bev_push(EV_ANIM, side, move, HITF_NODMG | HITF_LAST);
        for (int s = 0; s < STAT_COUNT; s++)
            if (mv->param & SM(s)) change_stat(foe, s, mv->stages);
    } else if (mv->effect == EF_SELF_STAT) {
        bev_push(EV_ANIM, side, move, HITF_NODMG | HITF_LAST);
        for (int s = 0; s < STAT_COUNT; s++)
            if (mv->param & SM(s)) change_stat(side, s, mv->stages);
    } else if (mv->effect == EF_HEAL) {
        if (att->hp >= att->max_hp) {
            bsay("But its HP is already full!");
            return;
        }
        bev_push(EV_ANIM, side, move, HITF_NODMG | HITF_LAST);
        heal_side(side, att->max_hp / 2 > 0 ? att->max_hp / 2 : 1);
        bsay_side(side, " recovered its vigor!");
    }
}

static void use_move(int side, int move)
{
    int foe = !side;
    Monster *att = side_mon(side), *def = side_mon(foe);
    const Move *mv = &MOVES[move];
    char msg[BEV_TEXT], name[32];

    side_name(msg, side);
    str_put(msg, " used ");
    str_put(msg, mv->name);
    str_put(msg, "!");
    bsay(msg);

    if (!move_hits(side, mv)) {
        bev_push(EV_ANIM, side, move, HITF_MISS | HITF_LAST);
        bsay_side(side, "'s attack missed!");
        return;
    }
    if (mv->cat == CAT_STATUS) {
        use_status_move(side, move);
        return;
    }
    if (trait_blocks_move(side, move)) return;

    int eff = move_effectiveness(move, att, def);
    if (eff == 0) {
        side_name(name, foe);
        str_copy(msg, "It had no effect on ");
        str_put(msg, name);
        str_put(msg, "...");
        bsay(msg);
        return;
    }

    int hits = mv->effect == EF_TWICE ? 2 : mv->effect == EF_MULTI ? multi_hit_count() : 1;
    int landed = 0, total = 0, said_att = 0, said_def = 0;
    for (int h = 0; h < hits && def->hp > 0 && att->hp > 0; h++) {
        int crit_chance = mv->effect == EF_HIGHCRIT ? 8 : 16;
        if (att->trait == TR_KEEN_EYE) crit_chance /= 2;
        int crit = rng_range((unsigned)crit_chance) == 0;
        int roll = 85 + (int)rng_range(16);
        DamageResult dr = calc_damage(att, battle.stages[side], def, battle.stages[foe],
                                      move, crit, roll);
        int dmg = dr.damage > def->hp ? def->hp : dr.damage;
        int held = 0;
        if (dmg >= def->hp && def->hp > 1) {
            if (def->trait == TR_STUBBORN && def->hp == def->max_hp) held = 1;
            else if (bond_high(foe) && rng_range(10) == 0) held = 2;
            if (held) dmg = def->hp - 1;
        }
        int flags = h;
        if (crit) flags |= HITF_CRIT;
        if (eff > 100) flags |= HITF_WEAK;
        if (eff < 100) flags |= HITF_RESIST;
        if (dmg >= def->hp) flags |= HITF_KO;
        if (h == hits - 1 || dmg >= def->hp) flags |= HITF_LAST;
        bev_push(EV_ANIM, side, move, flags);
        bev_push(EV_HIT, foe, flags, 0);
        damage_side(foe, dmg);
        total += dmg;
        landed++;
        if (crit) bsay("A perfect strike!");
        if (dr.att_trait && !said_att) {
            said_att = 1;
            trait_say(side, "surged with power!");
        }
        if (dr.def_trait && !said_def) {
            said_def = 1;
            trait_say(foe, eff > 100 ? "braced against the weak spot!" : "softened the blow!");
        }
        if (held == 1) trait_say(foe, "kept it standing!");
        if (held == 2) bsay_side(foe, " held on for you!");
        if (dmg > 0) contact_traits(side, mv);
    }
    if (eff > 100) bsay("It struck a weak spot!");
    else if (eff < 100) bsay("It was shrugged off...");
    if (hits > 1) {
        str_copy(msg, "It struck ");
        str_put_int(msg, landed);
        str_put(msg, landed == 1 ? " time!" : " times!");
        bsay(msg);
    }
    if (mv->effect == EF_DRAIN && total > 0 && att->hp > 0 && att->hp < att->max_hp) {
        heal_side(side, total / 2 > 0 ? total / 2 : 1);
        side_name(name, foe);
        str_copy(msg, name);
        str_put(msg, " had its vigor sipped away!");
        bsay(msg);
    }
    if (mv->effect == EF_RECOIL && total > 0 && att->hp > 0) {
        int recoil = move == M_LAST_GASP ? att->max_hp / 4 : total / 3;
        bev_push(EV_HIT, side, 0, 0);
        damage_side(side, recoil > 0 ? recoil : 1);
        bsay_side(side, " was jolted by the recoil!");
    }
    apply_secondary(side, mv);
    check_faint(foe);
    check_faint(side);
}

/* ---------------- AI ---------------- */

/*
 * How good `move` is for `self` against `foe` right now (stages st_self /
 * st_foe, 0 = none). Status moves score by what they would still change;
 * attacks by power x effectiveness x same-type x accuracy x the stat ratio,
 * and a hit that would knock the foe out scores double.
 */
static int ai_score(const Monster *self, const s8 *st_self, const Monster *foe, const s8 *st_foe, int move)
{
    const Move *mv = &MOVES[move];
    static const s8 NO_STAGES[STAT_COUNT];
    if (!st_self) st_self = NO_STAGES;
    if (!st_foe) st_foe = NO_STAGES;
    if (move_targets_foe(mv) && trait_absorbs(foe, move)) return 1;
    if (mv->cat == CAT_STATUS) {
        if (mv->effect == EF_HEAL)
            return self->hp * 2 < self->max_hp ? 70 : self->hp * 4 < self->max_hp * 3 ? 20 : 1;
        if (move_targets_foe(mv) && move_effectiveness(move, self, foe) == 0) return 0;
        if (mv->effect == EF_STATUS)
            return (foe->status || status_immune(foe, mv->param) ||
                    type_effectiveness(mv->type, foe->species) == 0) ? 0 : 55;
        if (mv->effect == EF_FOE_STAT)
            return st_foe[mv->param] <= -2 ? 5 : 35;
        if (mv->effect == EF_FOE_STATS) {
            for (int s = 0; s < STAT_COUNT; s++)
                if ((mv->param & SM(s)) && st_foe[s] > -2) return 40;
            return 5;
        }
        /* self boosts: worth it while one of its stats is still low */
        for (int s = 0; s < STAT_COUNT; s++)
            if ((mv->param & SM(s)) && st_self[s] < 2) return 35;
        return 5;
    }
    int eff = move_effectiveness(move, self, foe);
    int stab = species_has_type(self->species, mv->type) ? 3 : 2;
    int acc = mv->acc ? mv->acc : 100;
    int phys = mv->cat == CAT_PHYS;
    int as = phys ? STAT_ATK : STAT_SPA, ds = phys ? STAT_DEF : STAT_SPD;
    int ratio = apply_stage(self->stat[as], st_self[as]) * 10 / (apply_stage(foe->stat[ds], st_foe[ds]) + 1);
    int hits = mv->effect == EF_TWICE ? 2 : mv->effect == EF_MULTI ? 3 : 1;
    int trait = 10;   /* tenths */
    if ((self->trait == TR_BRUISER && phys) || (self->trait == TR_FOCUSED && !phys)) trait = 12;
    if (trait_surging(self, move)) trait = trait * 3 / 2;
    if (foe->trait == TR_THICK_FUR && (mv->type == T_BLAZE || mv->type == T_FROST)) trait /= 2;
    if (foe->trait == TR_BEDROCK && eff > 100) trait = trait * 3 / 4;
    int score = move_power(move, self, foe) * hits * eff / 100 * stab / 2 * acc / 100 * ratio / 10 *
                trait / 10 + 1;
    /* a sure knockout (lowest damage roll) is worth twice as much */
    if (eff > 0 && foe->hp > 0) {
        int low = calc_damage(self, st_self, foe, st_foe, move, 0, 85).damage * (hits > 1 ? 2 : 1);
        if (low >= foe->hp) score *= 2;
    }
    return score;
}

static int ai_move_score(int side, int move)
{
    return ai_score(side_mon(side), battle.stages[side], side_mon(!side), battle.stages[!side], move);
}

/* The best attack score `a` has against `d` (fresh stages). */
static int ai_best_attack(const Monster *a, const Monster *d)
{
    int best = 0;
    for (int i = 0; i < MAX_MOVES; i++) {
        int mv = a->moves[i];
        if (mv == MOVE_NONE || MOVES[mv].cat == CAT_STATUS) continue;
        int s = ai_score(a, 0, d, 0, mv);
        if (s > best) best = s;
    }
    return best;
}

/* How well warden kin `idx` would fare against your kin: its best attack
 * against yours over yours against it (x100). */
static int ai_matchup(int idx)
{
    const Monster *me = &battle.team[idx], *you = side_mon(SIDE_ALLY);
    int hp_part = me->max_hp ? 50 + 50 * me->hp / me->max_hp : 100;
    return ai_best_attack(me, you) * hp_part / (ai_best_attack(you, me) + 8);
}

/* A healthy warden kin other than the one out, best matchup first; -1 none. */
static int ai_best_reserve(void)
{
    int best = -1, best_m = -1;
    for (int i = 0; i < battle.team_count; i++) {
        if (i == battle.team_idx || battle.team[i].hp == 0) continue;
        int m = ai_matchup(i);
        if (m > best_m) {
            best_m = m;
            best = i;
        }
    }
    return best;
}

/* Wardens pull a kin that is badly outmatched when a clearly better one is
 * waiting (not the turn it came out; masters a little more often). */
static int ai_want_switch(void)
{
    if (battle.kind != BK_TRAINER || side_mon(SIDE_ALLY)->hp == 0) return -1;
    if (battle.turn - battle.foe_entered < 1 || battle.foe_switches >= (battle.master ? 3 : 2)) return -1;
    Monster *cur = side_mon(SIDE_ENEMY);
    if (cur->hp * 4 < cur->max_hp) return -1;      /* too hurt to bother: fight on */
    int now = ai_matchup(battle.team_idx);
    if (now >= 60) return -1;
    int alt = ai_best_reserve();
    if (alt < 0 || ai_matchup(alt) < now * 2 + 20) return -1;
    if ((int)rng_range(100) >= (battle.master ? 90 : 65)) return -1;
    return alt;
}

static int ai_choose_move(int side)
{
    Monster *m = side_mon(side);
    int scores[MAX_MOVES], best = -1, best_score = 0, total = 0;
    for (int i = 0; i < MAX_MOVES; i++) {
        scores[i] = 0;
        if (m->moves[i] == MOVE_NONE || m->pp[i] == 0) continue;
        scores[i] = ai_move_score(side, m->moves[i]);
        total += scores[i];
        if (scores[i] > best_score) {
            best_score = scores[i];
            best = i;
        }
    }
    if (best < 0) return -1; /* LAST GASP */
    int smart = battle.kind != BK_TRAINER ? (battle.legend ? 60 : 45) : battle.master ? 88 : 70;
    if ((int)rng_range(100) < smart) return best;
    int r = (int)rng_range((unsigned)total);
    for (int i = 0; i < MAX_MOVES; i++) {
        if (r < scores[i]) return i;
        r -= scores[i];
    }
    return best;
}

/* ---------------- turn resolution ---------------- */

enum { ACT_MOVE, ACT_ITEM, ACT_SWITCH, ACT_RUN };

static void resolve_move_slot(int side, int slot)
{
    Monster *m = side_mon(side);
    if (slot < 0) {
        bsay_side(side, " has no uses left!");
        use_move(side, M_LAST_GASP);
        return;
    }
    if (m->pp[slot] > 0) m->pp[slot]--;
    use_move(side, m->moves[slot]);
}

/* GLOWER: when a kin enters, its glare lowers the foe's ATTACK. */
static void entry_traits(int side)
{
    if (!has_trait(side, TR_GLOWER) || side_mon(side)->hp == 0 || side_mon(!side)->hp == 0) return;
    trait_say(side, "glared at its foe!");
    change_stat(!side, STAT_ATK, -1);
}

/* A meal buff (craft.c) gives every kin you send out extra starting stages. */
static void apply_meal_stages(void)
{
    int any = 0;
    for (int s = 0; s < STAT_COUNT; s++) {
        int v = clampi(meal_stat_stage(s), -6, 6);
        if (!v) continue;
        battle.stages[SIDE_ALLY][s] = (s8)clampi(battle.stages[SIDE_ALLY][s] + v, -6, 6);
        any = 1;
    }
    if (any && side_mon(SIDE_ALLY)->hp > 0) {
        bev_push(EV_STAT, SIDE_ALLY, 1, 0);
        bsay_side(SIDE_ALLY, " is fired up by your cooking!");
    }
}

/* The warden's next kin comes out of its lantern. */
static void enemy_send_out(int idx)
{
    char msg[BEV_TEXT];
    battle.team_idx = idx;
    for (int s = 0; s < STAT_COUNT; s++) battle.stages[SIDE_ENEMY][s] = 0;
    battle.flinch[SIDE_ENEMY] = 0;
    battle.participants = (u8)(1u << battle.ally);
    battle.foe_entered = (u8)battle.turn;
    str_copy(msg, battle.foe_title);
    str_put(msg, " sent out ");
    str_put(msg, SPECIES[battle.team[idx].species].name);
    str_put(msg, "!");
    bsay(msg);
    bev_push(EV_SEND_OUT, SIDE_ENEMY, idx, 0);
    entry_traits(SIDE_ENEMY);
}

/* A warden recalls an outmatched kin and sends out another (its action). */
static void enemy_switch_to(int idx)
{
    char msg[BEV_TEXT];
    str_copy(msg, battle.foe_title);
    str_put(msg, " called back ");
    str_put(msg, SPECIES[side_mon(SIDE_ENEMY)->species].name);
    str_put(msg, "!");
    bsay(msg);
    bev_push(EV_WITHDRAW, SIDE_ENEMY, 0, 0);
    battle.foe_switches++;
    enemy_send_out(idx);
}

static void end_of_turn(void)
{
    battle.turn++;
    for (int side = 0; side < 2; side++) {
        Monster *m = side_mon(side);
        battle.flinch[side] = 0;
        if (m->hp == 0) continue;
        if (m->status == STATUS_BRN || m->status == STATUS_PSN) {
            int dmg = m->max_hp / 8 > 0 ? m->max_hp / 8 : 1;
            bev_push(EV_HIT, side, 0, 0);
            damage_side(side, dmg);
            bsay_side(side, m->status == STATUS_BRN ? " is hurt by its burn!" : " is hurt by poison!");
            check_faint(side);
            if (m->hp == 0) continue;
        }
        if (m->trait == TR_BASKER && m->hp < m->max_hp) {
            heal_side(side, m->max_hp / 16 > 0 ? m->max_hp / 16 : 1);
            trait_say(side, "soaked up a little vigor!");
        }
        if (m->status != STATUS_NONE) {
            int st = m->status;
            char msg[BEV_TEXT];
            if (m->trait == TR_SELFMEND && rng_range(3) == 0) {
                cure_status(side);
                side_name(msg, side);
                str_put(msg, "'s SELFMEND cured its ");
                str_put(msg, STATUS_WORD[st]);
                str_put(msg, "!");
                bev_push(EV_TRAIT, side, 0, 0);
                bsay(msg);
            } else if (bond_high(side) && rng_range(10) == 0) {
                cure_status(side);
                side_name(msg, side);
                str_put(msg, " shook off its ");
                str_put(msg, STATUS_WORD[st]);
                str_put(msg, " for you!");
                bsay(msg);
            }
        }
        if (m->trait == TR_MOMENTUM && (battle.turn & 1) == 0 && battle.stages[side][STAT_SPE] < 6) {
            bev_push(EV_TRAIT, side, 0, 0);
            change_stat_ex(side, STAT_SPE, 1, 1);
            char msg[BEV_TEXT];
            side_name(msg, side);
            str_put(msg, "'s MOMENTUM raised its SPEED!");
            bsay(msg);
        }
    }
}

static void queue_enemy_fainted(void);
static void queue_ally_fainted(void);

/* After all actions: route to victory, next foe, forced switch or menu. */
static void finish_turn(void)
{
    Monster *foe = side_mon(SIDE_ENEMY), *me = side_mon(SIDE_ALLY);
    if (battle.result != BR_NONE) return;
    if (foe->hp == 0) {
        queue_enemy_fainted();
        /* both dozed off at once (recoil): your next kin, too */
        if (battle.result == BR_NONE && side_mon(SIDE_ALLY)->hp == 0) queue_ally_fainted();
        return;
    }
    if (me->hp == 0) {
        queue_ally_fainted();
        return;
    }
}

static int move_priority(int side, int slot)
{
    if (slot < 0) return 0;
    return MOVES[side_mon(side)->moves[slot]].priority;
}

static int ally_goes_first(int ally_slot, int enemy_slot)
{
    int pa = move_priority(SIDE_ALLY, ally_slot), pe = move_priority(SIDE_ENEMY, enemy_slot);
    if (pa != pe) return pa > pe;
    int sa = battle_stat(side_mon(SIDE_ALLY), battle.stages[SIDE_ALLY], STAT_SPE);
    int se = battle_stat(side_mon(SIDE_ENEMY), battle.stages[SIDE_ENEMY], STAT_SPE);
    if (sa != se) return sa > se;
    return (int)rng_range(2);
}

/* The foe acts after the player used an item, switched or failed to run. */
static void enemy_only_turn(void)
{
    if (side_mon(SIDE_ENEMY)->hp > 0 && side_mon(SIDE_ALLY)->hp > 0 && can_act(SIDE_ENEMY))
        resolve_move_slot(SIDE_ENEMY, ai_choose_move(SIDE_ENEMY));
    end_of_turn();
    finish_turn();
}

static void battle_play(void);

static void battle_take_turn(int ally_slot)
{
    int sw = ai_want_switch();
    if (sw >= 0) {                       /* switching comes before any move */
        enemy_switch_to(sw);
        if (side_mon(SIDE_ALLY)->hp > 0 && can_act(SIDE_ALLY)) resolve_move_slot(SIDE_ALLY, ally_slot);
        end_of_turn();
        finish_turn();
        battle_play();
        return;
    }
    int enemy_slot = ai_choose_move(SIDE_ENEMY);
    int first = ally_goes_first(ally_slot, enemy_slot) ? SIDE_ALLY : SIDE_ENEMY;
    for (int k = 0; k < 2; k++) {
        int side = k == 0 ? first : !first;
        if (side_mon(side)->hp == 0 || side_mon(!side)->hp == 0) break;
        if (!can_act(side)) continue;
        resolve_move_slot(side, side == SIDE_ALLY ? ally_slot : enemy_slot);
    }
    end_of_turn();
    finish_turn();
    battle_play();
}

/* ---------------- XP, prizes, the end of a bout ---------------- */

/*
 * XP for every kin that is still awake: those that fought this foe get the
 * full amount, the rest of the team half. QUICK STUDY +20%, bond 200+ +10%.
 */
static int xp_share(int slot, int base)
{
    const Monster *m = &party[slot];
    int xp = (battle.participants & (1u << slot)) ? base : base / 2;
    if (m->trait == TR_QUICK_STUDY) xp = xp * 6 / 5;
    if (m->bond >= 200) xp = xp * 11 / 10;
    int meal = meal_xp_percent();                 /* a meal buff (craft.c): 100 = none */
    if (meal > 0 && meal != 100) xp = xp * clampi(meal, 0, 400) / 100;
    if (xp < 1) xp = 1;
    return xp > 32000 ? 32000 : xp;
}

static void award_xp(const Monster *foe)
{
    int base = monster_xp_yield(foe, battle.kind == BK_TRAINER);
    char msg[BEV_TEXT];
    int others = 0;
    Monster *me = &party[battle.ally];
    if (me->hp > 0 && me->level < MAX_LEVEL) {
        int xp = monster_scaled_xp(xp_share(battle.ally, base), foe->level, me->level);
        str_copy(msg, kin_name(me));
        str_put(msg, " gained ");
        str_put_int(msg, xp);
        str_put(msg, " XP!");
        bsay(msg);
        bev_push(EV_XP, SIDE_ALLY, battle.ally, xp);
    }
    for (int i = 0; i < party_count; i++)
        if (i != battle.ally && party[i].hp > 0 && party[i].level < MAX_LEVEL) others++;
    if (!others) return;
    bsay(others == 1 ? "Your other kin gained XP too!" : "The rest of your team gained XP too!");
    for (int i = 0; i < party_count; i++)
        if (i != battle.ally && party[i].hp > 0 && party[i].level < MAX_LEVEL)
            bev_push(EV_XP, SIDE_ALLY, i,
                     monster_scaled_xp(xp_share(i, base), foe->level, party[i].level));
}

/* HOARDER: 10% per hoarding kin to bring back something after a win. */
static void hoarder_finds(void)
{
    static const u8 FINDS[16] = {
        ITEM_TONIC, ITEM_TONIC, ITEM_TONIC, ITEM_TONIC, ITEM_TONIC, ITEM_BIG_TONIC,
        ITEM_BIG_TONIC, ITEM_LANTERN, ITEM_LANTERN, ITEM_LANTERN, ITEM_GLOW_LANTERN,
        ITEM_MINT_TEA, ITEM_MINT_TEA, ITEM_SOOTHE_BALM, ITEM_GRAND_TONIC, ITEM_SUNSEED,
    };
    for (int i = 0; i < party_count; i++) {
        if (party[i].hp == 0 || party[i].trait != TR_HOARDER || rng_range(10) != 0) continue;
        int item = FINDS[rng_range(16)];
        bag_add(item, 1);
        char msg[BEV_TEXT];
        str_copy(msg, kin_name(&party[i]));
        str_put(msg, " found a");
        str_put(msg, ITEMS[item].name[0] == 'I' ? "n " : " ");
        str_put(msg, ITEMS[item].name);
        str_put(msg, " and brought it to you!");
        bev_push(EV_SFX, 0, SFX_ITEM, 0);
        bsay_wait(msg);
    }
}

/* Decide the bout: bond for everyone who took part, then the end event. */
static void battle_finish(int result)
{
    static const u8 CUE[] = { BCUE_END, BCUE_WIN, BCUE_LOSE, BCUE_RUN, BCUE_CAUGHT };
    if (result == BR_WIN) hoarder_finds();
    for (int i = 0; i < party_count; i++)
        if (battle.fought & (1u << i)) bond_add(&party[i], 2);
    battle.result = result;
    /* (wins and catches cued their music when they happened, under the XP,
     * prize and lantern lines: queue_enemy_fainted, battle_use_lantern) */
    if (result == BR_LOSE || result == BR_RUN)
        bev_push(EV_CUE, 0, CUE[result], 0);
    bev_push(EV_END, 0, result, 0);
}

static void queue_enemy_fainted(void)
{
    int last = 1;              /* the foe has no one left: the win music starts now */
    if (battle.kind == BK_TRAINER)
        for (int i = 0; i < battle.team_count; i++)
            if (i != battle.team_idx && battle.team[i].hp) last = 0;
    if (last && !battle.master) bev_push(EV_CUE, 0, BCUE_WIN, 0);
    award_xp(side_mon(SIDE_ENEMY));
    int next = battle.kind == BK_TRAINER ? ai_best_reserve() : -1;
    if (next >= 0) {
        enemy_send_out(next);
        return;
    }
    if (battle.kind == BK_TRAINER) {
        char msg[BEV_TEXT];
        bev_push(EV_PORTRAIT, SIDE_ENEMY, PA_RETURN, KF_LOSE);   /* the keeper walks back in, sheepish */
        if (battle.master) {                 /* the Hall Master's finale */
            bev_push(EV_SFX, 0, SFX_VICTORY, 0);
            bev_push(EV_CUE, 0, BCUE_MASTER_WIN, 0);
        }
        str_copy(msg, "You won the bout against ");
        str_put(msg, battle.foe_title);
        str_put(msg, "!");
        bsay_wait(msg);
        if (battle.lose_line && battle.lose_line[0]) bsay_wait(battle.lose_line);
        str_copy(msg, "You got ");
        str_put_int(msg, battle.prize);
        str_put(msg, "c for winning!");
        bev_push(EV_MONEY, 0, battle.prize, 0);
        bsay_wait(msg);
    }
    battle_finish(BR_WIN);
}

static void queue_ally_fainted(void)
{
    if (party_first_healthy() < 0) {
        if (battle.kind == BK_TRAINER) bev_push(EV_PORTRAIT, SIDE_ENEMY, PA_RETURN, KF_FLAIR);
        bsay_wait("You have no more kin that can go on!");
        bsay_wait("You hurried back to the HEARTH HALL...");
        battle_finish(BR_LOSE);
        return;
    }
    battle.return_state = BST_FORCED;
}

/* ---------------- player actions ---------------- */

static int battle_player_move(int slot)
{
    Monster *m = side_mon(SIDE_ALLY);
    int any_pp = 0;
    for (int i = 0; i < MAX_MOVES; i++)
        if (m->moves[i] != MOVE_NONE && m->pp[i] > 0) any_pp = 1;
    if (!any_pp) {
        battle_take_turn(-1);
        return 1;
    }
    if (m->moves[slot] == MOVE_NONE) return 0;
    if (m->pp[slot] == 0) {
        bsay("That move has no uses left!");
        battle.return_state = BST_MOVES;
        battle_play();
        return 1;
    }
    if (battle.ally < 6) battle.move_cursor_of[battle.ally] = (u8)slot;
    battle_take_turn(slot);
    return 1;
}

/* Escape odds (percent) of the next RUN (0 in keeper bouts: no fleeing). The odds grow with
 * every failed try and a faster (or SLIPPERY) kin always gets away. */
static int battle_run_chance(void)
{
    if (battle.no_run || battle.kind == BK_TRAINER) return 0;
    if (has_trait(SIDE_ALLY, TR_SLIPPERY)) return 100;
    int a = battle_stat(side_mon(SIDE_ALLY), 0, STAT_SPE);
    int b = battle_stat(side_mon(SIDE_ENEMY), 0, STAT_SPE);
    if (a >= b) return 100;
    int odds = a * 128 / (b ? b : 1) + 30 * (battle.escape_tries + 1);
    return odds >= 256 ? 100 : odds * 100 / 256;
}

static void battle_try_run(void)
{
    if (battle.no_run) {
        bsay_wait(battle.legend ? "The legend's presence holds you fast. There's no running!"
                                : "There's no running from this one!");
        battle.return_state = BST_ACTION;
        battle_play();
        return;
    }
    if (battle.kind == BK_TRAINER) {
        /* a bout with another keeper is a promise: see it through */
        bsay_wait("You gave your word to this bout. There's no walking away!");
        battle.return_state = BST_ACTION;
        battle_play();
        return;
    }
    battle.escape_tries++;
    if (has_trait(SIDE_ALLY, TR_SLIPPERY)) {
        trait_say(SIDE_ALLY, "found a way out!");
        bev_push(EV_FLEE, SIDE_ALLY, 0, 0);
        bsay_wait("Got away safely!");
        battle_finish(BR_RUN);
        battle_play();
        return;
    }
    int a = battle_stat(side_mon(SIDE_ALLY), 0, STAT_SPE);
    int b = battle_stat(side_mon(SIDE_ENEMY), 0, STAT_SPE);
    int odds = a * 128 / (b ? b : 1) + 30 * battle.escape_tries;
    if (a >= b || odds >= 256 || (int)rng_range(256) < odds) {
        bev_push(EV_FLEE, SIDE_ALLY, 0, 0);
        bsay_wait("Got away safely!");
        battle_finish(BR_RUN);
    } else {
        bsay("Can't escape!");
        enemy_only_turn();
    }
    battle_play();
}

static void battle_switch_to(int slot, int forced)
{
    char msg[BEV_TEXT];
    if (!forced) {
        str_copy(msg, kin_name(&party[battle.ally]));
        str_put(msg, ", back to your lantern!");
        bsay(msg);
        bev_push(EV_WITHDRAW, SIDE_ALLY, 0, 0);
    }
    for (int s = 0; s < STAT_COUNT; s++) battle.stages[SIDE_ALLY][s] = 0;
    battle.ally = slot;
    battle.participants |= (u8)(1u << slot);
    battle.fought |= (u8)(1u << slot);
    battle.move_cursor = battle.move_cursor_of[slot];
    str_copy(msg, forced ? "Out you come, " : "Your turn, ");
    str_put(msg, kin_name(&party[slot]));
    str_put(msg, "!");
    bsay(msg);
    bev_push(EV_SEND_OUT, SIDE_ALLY, slot, 0);
    apply_meal_stages();
    entry_traits(SIDE_ALLY);
    if (!forced) enemy_only_turn();
    battle_play();
}

/* Thrown-lantern looks (gfx_battle.h capsule_pal order). */
enum { LK_PLAIN, LK_PRISM, LK_STAR, LK_DUSK, LK_TIDE, LK_HEAVY, LK_QUICK, LK_BONE, LK_COUNT };
typedef char LanternLooksMatchArt[LK_COUNT == CAPSULE_PAL_COUNT ? 1 : -1];

static int battle_lantern_kind(int item)
{
    switch (item) {
    case ITEM_GLOW_LANTERN: return LK_PRISM;
    case ITEM_STAR_LANTERN: return LK_STAR;
    case ITEM_DUSK_LANTERN: return LK_DUSK;
    case ITEM_TIDE_LANTERN: return LK_TIDE;
    case ITEM_HEAVY_LANTERN: return LK_HEAVY;
    case ITEM_QUICK_LANTERN: return LK_QUICK;
    case ITEM_BONE_LANTERN: return LK_BONE;
    default: return LK_PLAIN;
    }
}

/* Is it night or dark here (DUSK LANTERN)? */
static int battle_is_dark(void)
{
    return time_is_night() || (MAPS[cur_map].flags & MF_DARK) || battle.scene == BSCENE_CAVE ||
           battle.scene == BSCENE_CRYPT;
}

/* Is the bout on water (TIDE LANTERN)? */
static int battle_is_on_water(void)
{
    return battle.on_water || travel.surfing || battle.scene == BSCENE_SEA;
}

/*
 * A lantern's finesse (x10 multiplier for catch_shakes) against the wild
 * kin out now. The crafted lanterns (param 16) double in their own
 * situation, the QUICK LANTERN 2.5x on the first turn; a HEAVY LANTERN
 * scales with the kin's weight (1000 hg and up). A meal can add to it.
 */
static int lantern_finesse(int item)
{
    const Monster *w = side_mon(SIDE_ENEMY);
    const Species *s = &SPECIES[w->species];
    int f = ITEMS[item].param, on = 0;
    switch (item) {
    case ITEM_DUSK_LANTERN: on = battle_is_dark(); break;
    case ITEM_TIDE_LANTERN: on = species_has_type(w->species, T_TIDE) || battle_is_on_water(); break;
    case ITEM_BONE_LANTERN: on = species_has_type(w->species, T_HOLLOW); break;
    case ITEM_QUICK_LANTERN:
        if (battle.turn == 0) f = f * 5 / 2;
        break;
    case ITEM_HEAVY_LANTERN: {
        int kg10 = size_scale(s->weight_hg, w->size);    /* hectograms */
        if (kg10 >= 2000) f = f * 5 / 2;
        else if (kg10 >= 1000) on = 1;
        break;
    }
    default: break;
    }
    if (on) f *= 2;
    return clampi(f + meal_catch_bonus(), 1, 255);
}

/* The chance (percent) that this lantern befriends the wild foe right now,
 * or -1 where lanterns do nothing (keeper bouts, fused kin). */
static int lantern_catch_pct(int item)
{
    if (battle.kind != BK_WILD || ITEMS[item].kind != IK_LANTERN) return -1;
    const Monster *w = side_mon(SIDE_ENEMY);
    if (SPECIES[w->species].rarity == R_FUSION) return -1;
    return catch_chance_pct(w, lantern_finesse(item));
}

/* The lantern that suits this wild kin best (L quick-throw), or -1. */
static int battle_best_lantern(void)
{
    int best = -1, best_f = 0;
    for (int i = 0; i < ITEM_COUNT; i++) {
        if (ITEMS[i].kind != IK_LANTERN || bag[i] <= 0) continue;
        int f = battle.kind == BK_WILD ? lantern_finesse(i) : ITEMS[i].param;
        if (best < 0 || f > best_f) {
            best = i;
            best_f = f;
        }
    }
    return best;
}

static void battle_throw_lantern(int item)
{
    const Item *it = &ITEMS[item];
    char msg[BEV_TEXT];
    if (battle.kind == BK_TRAINER) {
        str_copy(msg, SPECIES[side_mon(SIDE_ENEMY)->species].name);
        str_put(msg, " is bonded to ");
        str_put(msg, battle.foe_title);
        str_put(msg, ". It can't be befriended!");
        bsay_wait(msg);
        battle.return_state = BST_ACTION;
        battle_play();
        return;
    }
    Monster *wild = side_mon(SIDE_ENEMY);
    if (SPECIES[wild->species].rarity == R_FUSION) {   /* woven kin only come from the Loom */
        str_copy(msg, SPECIES[wild->species].name);
        str_put(msg, "'s woven kernel won't settle in a lantern!");
        bsay_wait(msg);
        battle.return_state = BST_ACTION;
        battle_play();
        return;
    }
    bag[item]--;
    str_copy(msg, "You threw a");
    str_put(msg, it->name[0] == 'A' || it->name[0] == 'E' || it->name[0] == 'I' || it->name[0] == 'O' ||
                  it->name[0] == 'U' ? "n " : " ");
    str_put(msg, it->name);
    str_put(msg, "!");
    bsay(msg);
    int shakes = catch_shakes(wild, lantern_finesse(item));
    bev_push(EV_LANTERN, SIDE_ENEMY, shakes, battle_lantern_kind(item));
    if (shakes >= 4) {
        const char *name = SPECIES[wild->species].name;
        bev_push(EV_CUE, 0, BCUE_CAUGHT, 0);
        str_copy(msg, "Yes! ");
        str_put(msg, name);
        str_put(msg, " settled into the lantern!");
        bsay_wait(msg);
        str_copy(msg, "You befriended ");
        str_put(msg, name);
        str_put(msg, "!");
        bsay_wait(msg);
        Monster m = *wild;
        m.met_map = (u8)cur_map;
        m.met_level = m.level;
        award_xp(wild);
        int where = give_monster(&m);
        if (where >= 0) {   /* "Give it a name?" (then where it went) */
            bev_push(EV_NAME, 0, where, where ? storage_newest() : party_count - 1);
        } else {
            str_copy(msg, name);
            str_put(msg, " went home: the LANTERN SHELF is full!");
            bsay_wait(msg);
        }
        battle_finish(BR_CAUGHT);
    } else {
        static const char *const BREAK[4] = {
            "Oh no! It broke free!", "Aww! It seemed to settle, then tuned out!",
            "Aargh! Almost had it!", "So close! It slipped out at the last moment!",
        };
        bsay(BREAK[shakes]);
        enemy_only_turn();
    }
    battle_play();
}

/* Item kinds that work in a bout (the bag's BOUT pocket view can ask). */
MAYBE_UNUSED static int battle_item_kind_usable(int kind)
{
    return kind == IK_HEAL || kind == IK_FULL_HEAL || kind == IK_WAKE || kind == IK_TEA ||
           kind == IK_XSTAT || kind == IK_LANTERN || kind == IK_HEAL_CURE || kind == IK_TEA_ALL ||
           kind == IK_REVIVE;
}

/* Use a bag item in battle on party slot `target`. Returns 0 if refused. */
static int battle_use_item(int item, int target)
{
    if (item < 0 || item >= ITEM_COUNT || bag[item] <= 0) return 0;
    const Item *it = &ITEMS[item];
    char msg[BEV_TEXT];
    if (it->kind == IK_LANTERN) {
        battle_throw_lantern(item);
        return 1;
    }
    if (target < 0 || target >= party_count) return 0;
    Monster *m = &party[target];
    if (it->kind == IK_XSTAT) {
        if (it->param >= STAT_COUNT || battle.stages[SIDE_ALLY][it->param] >= 6) return 0;
        bag[item]--;
        str_copy(msg, "You used ");
        str_put(msg, it->name);
        str_put(msg, "!");
        bsay(msg);
        change_stat(SIDE_ALLY, it->param, 2);
        enemy_only_turn();
        battle_play();
        return 1;
    }
    int ok = 0;
    if (it->kind == IK_HEAL) ok = m->hp > 0 && m->hp < m->max_hp;
    else if (it->kind == IK_FULL_HEAL) ok = m->hp > 0 && m->status != STATUS_NONE;
    else if (it->kind == IK_HEAL_CURE) ok = m->hp > 0 && (m->hp < m->max_hp || m->status != STATUS_NONE);
    else if (it->kind == IK_WAKE || it->kind == IK_REVIVE) ok = m->hp == 0;
    else if (it->kind == IK_TEA || it->kind == IK_TEA_ALL) {
        for (int i = 0; i < MAX_MOVES; i++)
            if (m->moves[i] != MOVE_NONE && m->pp[i] < MOVES[m->moves[i]].pp) ok = 1;
    }
    if (!ok) return 0;
    bag[item]--;
    str_copy(msg, "You used ");
    str_put(msg, it->name);
    str_put(msg, "!");
    bsay(msg);
    if (it->kind == IK_HEAL || it->kind == IK_WAKE || it->kind == IK_REVIVE || it->kind == IK_HEAL_CURE) {
        int amount = it->kind == IK_WAKE ? m->max_hp / 2 : it->kind == IK_REVIVE ? m->max_hp : it->param;
        int hp = m->hp + (amount > 0 ? amount : 1);
        int cured = it->kind == IK_HEAL_CURE && m->status != STATUS_NONE;
        m->hp = (u16)(hp > m->max_hp ? m->max_hp : hp);
        if (it->kind != IK_HEAL) {
            m->status = STATUS_NONE;
            m->sleep_turns = 0;
        }
        if (target == battle.ally) {
            bev_push(EV_HP, SIDE_ALLY, m->hp, 0);
            if (cured) bev_push(EV_STATUS, SIDE_ALLY, STATUS_NONE, 0);
        } else {
            bev_push(EV_SFX, 0, SFX_SPARKLE, 0);
        }
        str_copy(msg, kin_name(m));
        str_put(msg, it->kind == IK_WAKE ? " woke up, bright and ready!" :
                     it->kind == IK_REVIVE ? " woke up at full strength!" :
                     cured ? "'s HP was restored and it was cured!" : "'s HP was restored.");
        bsay(msg);
    } else if (it->kind == IK_FULL_HEAL) {
        m->status = STATUS_NONE;
        if (target == battle.ally) bev_push(EV_STATUS, SIDE_ALLY, STATUS_NONE, 0);
        bev_push(EV_SFX, 0, SFX_SPARKLE, 0);
        str_copy(msg, kin_name(m));
        str_put(msg, "'s field rang true again. It was cured!");
        bsay(msg);
    } else {
        for (int i = 0; i < MAX_MOVES; i++)
            if (m->moves[i] != MOVE_NONE)
                m->pp[i] = (u8)(it->kind == IK_TEA_ALL ? MOVES[m->moves[i]].pp :
                                clampi(m->pp[i] + it->param, 0, MOVES[m->moves[i]].pp));
        bev_push(EV_SFX, 0, SFX_SPARKLE, 0);
        str_copy(msg, kin_name(m));
        str_put(msg, "'s moves got their uses back.");
        bsay(msg);
    }
    enemy_only_turn();
    battle_play();
    return 1;
}
