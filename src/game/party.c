/*
 * Player-owned state: team, LANTERN SHELF storage, bag, money, Almanac
 * flags and the HUSH BELL,
 * plus flows shared by several screens: learning moves (with the "forget
 * a move?" prompt), using items outside battle and queuing evolutions.
 */

#define PARTY_MAX 6
#define BOX_SIZE 30
#define BOX_COUNT 8
#define STORAGE_MAX (BOX_SIZE * BOX_COUNT)   /* the LANTERN SHELF: 8 boxes of 30 */

/* A kin resting on the Shelf, packed to 24 bytes. Stats, HP and uses are
 * rebuilt when it comes back (resting on the Shelf heals it fully). */
typedef struct {
    u8 species, level, flags, bond;
    u8 moves[MAX_MOVES];
    u32 xp;
    u32 pot;                 /* six 5-bit potentials: HP ATK DEF FOCUS WILL SPE */
    u8 temper, trait, size, met_map;
    u8 met_level, pad[3];
} BoxMon;
typedef char BoxMonIs24[sizeof(BoxMon) == 24 ? 1 : -1];

static Monster party[PARTY_MAX];
static int party_count;
EWRAM_BSS static BoxMon storage[STORAGE_MAX];
static int storage_count;
static int bag[ITEM_COUNT];
static int money;
static u8 dex_seen[SP_COUNT];
static u8 dex_caught[SP_COUNT];
static u16 hush_steps;      /* HUSH BELL: steps left before wild kin notice you again */

static BoxMon box_pack(const Monster *m)
{
    BoxMon b;
    u8 *raw = (u8 *)&b;
    for (unsigned i = 0; i < sizeof(b); i++) raw[i] = 0;
    b.species = m->species;
    b.level = m->level;
    b.flags = m->flags;
    b.bond = m->bond;
    for (int i = 0; i < MAX_MOVES; i++) b.moves[i] = m->moves[i];
    b.xp = m->xp;
    for (int i = 0; i < 6; i++) b.pot |= (u32)(m->pot[i] & 31) << (i * 5);
    b.temper = m->temper;
    b.trait = m->trait;
    b.size = m->size;
    b.met_map = m->met_map;
    b.met_level = m->met_level;
    return b;
}

static Monster box_unpack(const BoxMon *b)
{
    Monster m;
    u8 *raw = (u8 *)&m;
    for (unsigned i = 0; i < sizeof(m); i++) raw[i] = 0;
    m.species = b->species;
    m.level = b->level;
    m.flags = b->flags;
    m.bond = b->bond;
    for (int i = 0; i < MAX_MOVES; i++) {
        m.moves[i] = b->moves[i];
        m.pp[i] = b->moves[i] < MOVE_COUNT ? MOVES[b->moves[i]].pp : 0;
    }
    m.xp = b->xp;
    for (int i = 0; i < 6; i++) m.pot[i] = (u8)((b->pot >> (i * 5)) & 31);
    m.temper = b->temper;
    m.trait = b->trait;
    m.size = b->size;
    m.met_map = b->met_map;
    m.met_level = b->met_level;
    monster_recalc(&m);
    monster_heal_full(&m);
    return m;
}

/* The kin in Shelf slot i, rebuilt (read-only view). */
static Monster storage_get(int i)
{
    return box_unpack(&storage[i]);
}

/* Puts a kin on the Shelf: 1 = stored, 0 = the Shelf is full. */
static int storage_add(const Monster *m)
{
    if (storage_count >= STORAGE_MAX) return 0;
    storage[storage_count++] = box_pack(m);
    return 1;
}

/* Takes a kin off the Shelf (the rest move up). */
static Monster storage_take(int i)
{
    Monster m = box_unpack(&storage[i]);
    for (int k = i; k < storage_count - 1; k++) storage[k] = storage[k + 1];
    storage_count--;
    return m;
}

static int party_first_healthy(void)
{
    for (int i = 0; i < party_count; i++)
        if (party[i].hp > 0) return i;
    return -1;
}

static int party_max_level(void)
{
    int best = 1;
    for (int i = 0; i < party_count; i++)
        if (party[i].level > best) best = party[i].level;
    return best;
}

static void party_heal_all(void)
{
    for (int i = 0; i < party_count; i++) monster_heal_full(&party[i]);
}

static int dex_caught_count(void)
{
    int n = 0;
    for (int i = 0; i < SP_COUNT; i++) n += dex_caught[i] != 0;
    return n;
}

static int dex_seen_count(void)
{
    int n = 0;
    for (int i = 0; i < SP_COUNT; i++) n += dex_seen[i] != 0;
    return n;
}

enum { OWN_NONE, OWN_CAUGHT_BEFORE, OWN_IN_PC, OWN_IN_TEAM };

static int species_ownership(int sp)
{
    for (int i = 0; i < party_count; i++)
        if (party[i].species == sp) return OWN_IN_TEAM;
    for (int i = 0; i < storage_count; i++)
        if (storage[i].species == sp) return OWN_IN_PC;
    return dex_caught[sp] ? OWN_CAUGHT_BEFORE : OWN_NONE;
}

/* Adds a caught creature: 0 = joined the team, 1 = sent to the PC, -1 = no room. */
static int give_monster(const Monster *m)
{
    dex_seen[m->species] = 1;
    dex_caught[m->species] = 1;
    if (party_count < PARTY_MAX) {
        party[party_count++] = *m;
        return 0;
    }
    if (storage_add(m)) return 1;
    return -1;
}

static int bag_total(int pocket)
{
    int n = 0;
    for (int i = 0; i < ITEM_COUNT; i++)
        if (ITEMS[i].pocket == pocket) n += bag[i];
    return n;
}

static void bag_add(int item, int qty)
{
    bag[item] = clampi(bag[item] + qty, 0, 999);
}

/* ---------------- learning moves ---------------- */

static struct {
    int slot, move;
    char choice_text[MAX_MOVES + 1][16];
    const char *choices[MAX_MOVES + 1];
} learn;

static void learn_forget_pick(int c)
{
    char msg[MSG_TEXT_MAX];
    Monster *m = &party[learn.slot];
    const char *name = SPECIES[m->species].name;
    if (c < 0 || c >= MAX_MOVES) {
        str_copy(msg, name);
        str_put(msg, " did not learn ");
        str_put(msg, MOVES[learn.move].name);
        str_put(msg, ".");
        dlg_say(msg);
        return;
    }
    str_copy(msg, "1, 2 and... Poof! ");
    str_put(msg, name);
    str_put(msg, " forgot ");
    str_put(msg, MOVES[m->moves[c]].name);
    str_put(msg, ".\fAnd... ");
    str_put(msg, name);
    str_put(msg, " learned ");
    str_put(msg, MOVES[learn.move].name);
    str_put(msg, "!");
    monster_replace_move(m, c, learn.move);
    dlg_say(msg);
}

static void learn_answer(int c)
{
    if (c != 0) {
        learn_forget_pick(-1);
        return;
    }
    Monster *m = &party[learn.slot];
    for (int i = 0; i < MAX_MOVES; i++) {
        str_copy(learn.choice_text[i], MOVES[m->moves[i]].name);
        learn.choices[i] = learn.choice_text[i];
    }
    str_copy(learn.choice_text[MAX_MOVES], "CANCEL");
    learn.choices[MAX_MOVES] = learn.choice_text[MAX_MOVES];
    dlg_ask("Which move should be forgotten?", learn.choices, MAX_MOVES + 1, learn_forget_pick);
}

/* Queue the dialog for learning `move`; learns silently-free if a slot is open. */
static void learn_begin(int slot, int move)
{
    char msg[MSG_TEXT_MAX];
    Monster *m = &party[slot];
    const char *name = SPECIES[m->species].name;
    if (monster_knows(m, move)) return;
    if (monster_add_move(m, move)) {
        str_copy(msg, name);
        str_put(msg, " learned ");
        str_put(msg, MOVES[move].name);
        str_put(msg, "!");
        dlg_say(msg);
        return;
    }
    learn.slot = slot;
    learn.move = move;
    str_copy(msg, name);
    str_put(msg, " wants to learn ");
    str_put(msg, MOVES[move].name);
    str_put(msg, ".\fBut ");
    str_put(msg, name);
    str_put(msg, " can't learn more than four moves. Forget an older move?");
    dlg_ask(msg, YES_NO, 2, learn_answer);
}

/* ---------------- evolution queue ---------------- */

typedef struct { u8 slot, into; } EvoRequest;
static EvoRequest evo_queue[PARTY_MAX];
static int evo_count;

static void evo_request(int slot, int into)
{
    for (int i = 0; i < evo_count; i++)
        if (evo_queue[i].slot == slot) return;
    if (evo_count < PARTY_MAX) {
        evo_queue[evo_count].slot = (u8)slot;
        evo_queue[evo_count].into = (u8)into;
        evo_count++;
    }
}

/* ---------------- items outside battle ---------------- */

/* Returns 1 if the item did something (and was consumed). Messages are
 * queued on the dialog system. */
/* Items whose use belongs to a system module (defined later). */
static int farm_use_item(int item);                /* seeds, fertiliser, sprinkler, crops */
static int craft_use_food(int item, int slot);     /* meals and drinks */
static int travel_use_item(int item);              /* LURE INCENSE, WAYSTONE */
static int key_item_use(int key);                  /* KEY_* (modules.c dispatches) */

static int item_use_field(int item, int slot)
{
    const Item *it = &ITEMS[item];
    if (bag[item] <= 0) return 0;
    switch (it->kind) {
    case IK_PLANT: case IK_FERTILIZER: case IK_PLACE: case IK_CROP: return farm_use_item(item);
    case IK_LURE: case IK_WAYSTONE: return travel_use_item(item);
    case IK_KEY: return key_item_use(it->param);
    case IK_FOOD: return craft_use_food(item, slot);
    case IK_MATERIAL: return 0;
    default: break;
    }
    Monster *m = &party[slot];
    const char *name = SPECIES[m->species].name;
    char msg[MSG_TEXT_MAX];
    if (it->kind == IK_HUSH) {
        if (bag[item] <= 0) return 0;
        hush_steps = it->param;
        bag[item]--;
        dlg_say("The HUSH BELL rings out a soft anti-phase hum. Wild kin won't notice your team for a while.");
        return 1;
    }
    if (bag[item] <= 0 || slot < 0 || slot >= party_count) return 0;
    switch (it->kind) {
    case IK_HEAL:
        if (m->hp == 0 || m->hp >= m->max_hp) return 0;
        {
            int before = m->hp;
            m->hp = (u16)clampi(m->hp + it->param, 0, m->max_hp);
            str_copy(msg, name);
            str_put(msg, "'s HP was restored by ");
            str_put_int(msg, m->hp - before);
            str_put(msg, " points.");
        }
        break;
    case IK_FULL_HEAL:
        if (m->hp == 0 || m->status == STATUS_NONE) return 0;
        m->status = STATUS_NONE;
        m->sleep_turns = 0;
        str_copy(msg, name);
        str_put(msg, " was cured of its status problem.");
        break;
    case IK_WAKE:
        if (m->hp > 0) return 0;
        m->hp = (u16)(m->max_hp / 2 > 0 ? m->max_hp / 2 : 1);
        str_copy(msg, name);
        str_put(msg, " woke up with a start, ready to go!");
        break;
    case IK_TEA: {
        int ok = 0;
        for (int i = 0; i < MAX_MOVES; i++)
            if (m->moves[i] != MOVE_NONE && m->pp[i] < MOVES[m->moves[i]].pp) {
                m->pp[i] = (u8)clampi(m->pp[i] + it->param, 0, MOVES[m->moves[i]].pp);
                ok = 1;
            }
        if (!ok) return 0;
        str_copy(msg, name);
        str_put(msg, "'s moves got their uses back.");
        break;
    }
    case IK_SEED: {
        if (m->level >= MAX_LEVEL) return 0;
        monster_level_up(m);
        if (m->hp == 0) m->hp = 1;
        str_copy(msg, name);
        str_put(msg, " grew to Lv. ");
        str_put_int(msg, m->level);
        str_put(msg, "!");
        bag[item]--;
        dlg_say(msg);
        u8 moves[4];
        int n = learnset_at(m->species, m->level, moves);
        for (int i = 0; i < n; i++) learn_begin(slot, moves[i]);
        int into = monster_level_evolution(m);
        if (into >= 0) evo_request(slot, into);
        return 1;
    }
    case IK_SHARD: {
        int into = monster_item_evolution(m, item);
        if (into < 0) return 0;
        bag[item]--;
        evo_request(slot, into);
        return 1;
    }
    default:
        return 0;
    }
    bag[item]--;
    dlg_say(msg);
    return 1;
}
