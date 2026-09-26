/*
 * Two checked SRAM slots (primary at 0, backup at 4096), each verified by
 * reading it back. Version 3 stores the full game (kin individuality,
 * lore, wardens, options). Older saves are migrated: version 2 keeps the
 * team, the shelf, the bag and the Almanac (each kin gets rolled
 * individuality and wakes up at home); version 1 keeps team, bag, Almanac.
 */
#define SAVE_VERSION 3u
#define SAVE_MAGIC 0x4D515354u
#define SAVE_BACKUP_OFFSET 4096u
__attribute__((used)) static const char gba_save_type[] = "SRAM_V113";

typedef struct {
    u32 magic, version;
    int party_count, storage_count;
    Monster party[PARTY_MAX];
    Monster storage[STORAGE_MAX];
    u16 bag[ITEM_COUNT];
    int money;
    u8 seen[SP_COUNT], caught[SP_COUNT];
    u32 story_flags, item_flags[2], trainer_flags;
    u8 lore_known[LORE_BYTES], lore_unread[LORE_BYTES];
    u16 hush_steps, step_counter;
    u8 options[8];
    int map, player_x, player_y, facing;
    u32 checksum;
} SaveData;

/* ---- version 2 layout (read-only, for migration) ---- */
typedef struct {
    u8 species, level, status, sleep_turns;
    u8 moves[MAX_MOVES];
    u8 pp[MAX_MOVES];
    u16 hp, max_hp;
    u16 stat[5];
    u32 xp;
} MonsterV2;

typedef struct {
    u32 magic, version;
    int party_count, storage_count;
    MonsterV2 party[PARTY_MAX];
    MonsterV2 storage[STORAGE_MAX];
    u16 bag[16];
    int money;
    u8 seen[SP_COUNT], caught[SP_COUNT];
    u32 story_flags, item_flags;
    int map, player_x, player_y, facing;
    u32 checksum;
} SaveDataV2;

typedef char SaveSlotsFitSram[(sizeof(SaveData) <= SAVE_BACKUP_OFFSET &&
    SAVE_BACKUP_OFFSET + sizeof(SaveData) <= 32768u) ? 1 : -1];

/* ---- version 1 layout (read-only, for migration) ---- */
typedef struct {
    u8 species, level, moves[3], last_learned;
    s16 cur_hp, max_hp, atk, def, spd;
    u16 xp;
} MonsterV1;

typedef struct {
    u32 magic, version;
    MonsterV1 party[6];
    int party_count;
    int bag[3];
    u8 seen[12], caught[12];
    int starter_given, player_x, player_y, inside_house;
    u32 checksum;
} SaveDataV1;

/* Old species order -> new catalogue numbers. */
static const u8 V1_SPECIES[12] = {
    SP_FLARIX, SP_CINDERUB, SP_AQUAPO, SP_BUBBLIN, SP_DANDELAMB, SP_THORNIP,
    SP_ZAPPET, SP_VOLTUX, SP_GOLEMIT, SP_PUFFOWL, SP_MOSSHELL, SP_SKYWISP,
};

static u32 fnv_bytes(const void *p, unsigned n)
{
    const u8 *bytes = p;
    u32 hash = 2166136261u;
    for (unsigned i = 0; i < n; i++) hash = (hash ^ bytes[i]) * 16777619u;
    return hash;
}

static u32 save_checksum(const SaveData *data)
{
    return fnv_bytes(data, sizeof(*data) - sizeof(data->checksum));
}

static int monster_valid(const Monster *m)
{
    if (m->species >= SP_COUNT || m->level < 1 || m->level > MAX_LEVEL ||
        m->max_hp < 1 || m->hp > m->max_hp || m->status >= STATUS_COUNT ||
        m->temper >= TEMPERAMENT_COUNT || m->trait >= TRAIT_COUNT)
        return 0;
    for (int i = 0; i < 6; i++)
        if (m->pot[i] > POT_MAX) return 0;
    int known = 0;
    for (int j = 0; j < MAX_MOVES; j++) {
        if (m->moves[j] == MOVE_NONE) continue;
        if (m->moves[j] >= MOVE_COUNT || m->pp[j] > MOVES[m->moves[j]].pp) return 0;
        known++;
    }
    return known > 0;
}

static void save_capture(SaveData *data)
{
    u8 *raw = (u8 *)data;
    for (unsigned i = 0; i < sizeof(*data); i++) raw[i] = 0;
    data->magic = SAVE_MAGIC;
    data->version = SAVE_VERSION;
    data->party_count = party_count;
    data->storage_count = storage_count;
    for (int i = 0; i < PARTY_MAX; i++) data->party[i] = party[i];
    for (int i = 0; i < STORAGE_MAX; i++) data->storage[i] = storage[i];
    for (int i = 0; i < ITEM_COUNT; i++) data->bag[i] = (u16)bag[i];
    data->money = money;
    for (int i = 0; i < SP_COUNT; i++) {
        data->seen[i] = dex_seen[i];
        data->caught[i] = dex_caught[i];
    }
    data->story_flags = story_flags;
    data->item_flags[0] = item_flags[0];
    data->item_flags[1] = item_flags[1];
    data->trainer_flags = trainer_flags;
    for (int i = 0; i < LORE_BYTES; i++) {
        data->lore_known[i] = lore_known[i];
        data->lore_unread[i] = lore_unread[i];
    }
    data->hush_steps = hush_steps;
    data->step_counter = step_counter;
    data->options[0] = opt.text_speed;
    data->options[1] = opt.battle_anims;
    data->options[2] = opt.sound;
    data->options[3] = opt.follower;
    data->options[4] = opt.autosave;
    data->map = cur_map;
    data->player_x = player.x;
    data->player_y = player.y;
    data->facing = player.facing;
    data->checksum = save_checksum(data);
}

static int save_valid(const SaveData *data)
{
    if (data->magic != SAVE_MAGIC || data->version != SAVE_VERSION ||
        data->checksum != save_checksum(data) ||
        data->party_count < 0 || data->party_count > PARTY_MAX ||
        data->storage_count < 0 || data->storage_count > STORAGE_MAX ||
        data->money < 0 || data->money > 999999 ||
        data->map < 0 || data->map >= MAP_COUNT || data->facing < 0 || data->facing > 3 ||
        data->player_x < 0 || data->player_y < 0 ||
        data->player_x >= MAPS[data->map].w || data->player_y >= MAPS[data->map].h ||
        ((data->story_flags & FLAG_STARTER) && !data->party_count))
        return 0;
    for (int i = 0; i < ITEM_COUNT; i++)
        if (data->bag[i] > 999) return 0;
    for (int i = 0; i < data->party_count; i++)
        if (!monster_valid(&data->party[i])) return 0;
    for (int i = 0; i < data->storage_count; i++)
        if (!monster_valid(&data->storage[i])) return 0;
    return 1;
}

static void save_apply(const SaveData *data)
{
    party_count = data->party_count;
    storage_count = data->storage_count;
    for (int i = 0; i < PARTY_MAX; i++) party[i] = data->party[i];
    for (int i = 0; i < STORAGE_MAX; i++) storage[i] = data->storage[i];
    for (int i = 0; i < ITEM_COUNT; i++) bag[i] = data->bag[i];
    money = data->money;
    for (int i = 0; i < SP_COUNT; i++) {
        dex_seen[i] = data->seen[i];
        dex_caught[i] = data->caught[i];
    }
    story_flags = data->story_flags;
    item_flags[0] = data->item_flags[0];
    item_flags[1] = data->item_flags[1];
    trainer_flags = data->trainer_flags;
    for (int i = 0; i < LORE_BYTES; i++) {
        lore_known[i] = data->lore_known[i];
        lore_unread[i] = data->lore_unread[i];
    }
    hush_steps = data->hush_steps;
    step_counter = data->step_counter;
    opt.text_speed = (u8)(data->options[0] % TEXT_SPEED_COUNT);
    opt.battle_anims = data->options[1] & 1;
    opt.sound = data->options[2] & 1;
    opt.follower = data->options[3] & 1;
    opt.autosave = data->options[4] & 1;
    map_load(data->map);
    player.x = (s16)data->player_x;
    player.y = (s16)data->player_y;
    player.facing = (u8)data->facing;
    player.ox = player.oy = 0;
    player.moving = 0;
}

/* ---- v2 migration ---- */

static int save_v2_valid(const SaveDataV2 *d)
{
    if (d->magic != SAVE_MAGIC || d->version != 2u ||
        d->checksum != fnv_bytes(d, sizeof(*d) - sizeof(d->checksum)) ||
        d->party_count < 0 || d->party_count > PARTY_MAX ||
        d->storage_count < 0 || d->storage_count > STORAGE_MAX)
        return 0;
    for (int i = 0; i < d->party_count + d->storage_count; i++) {
        const MonsterV2 *m = i < d->party_count ? &d->party[i] : &d->storage[i - d->party_count];
        if (m->species >= SP_COUNT || m->level < 1 || m->level > MAX_LEVEL) return 0;
    }
    return 1;
}

/* An old kin keeps species, level, XP, moves and health; the rest is rolled. */
static Monster migrate_v2_monster(const MonsterV2 *o)
{
    Monster m = monster_make(o->species, o->level);
    int known = 0;
    for (int i = 0; i < MAX_MOVES; i++) {
        int mv = o->moves[i];
        if (mv < MOVE_COUNT) {
            m.moves[known] = (u8)mv;
            m.pp[known] = (u8)clampi(o->pp[i], 0, MOVES[mv].pp);
            known++;
        }
    }
    if (known)
        for (int i = known; i < MAX_MOVES; i++) m.moves[i] = MOVE_NONE;
    m.xp = o->xp < xp_for_level(m.level) ? xp_for_level(m.level) : o->xp;
    m.status = o->status < STATUS_COUNT ? o->status : STATUS_NONE;
    m.sleep_turns = o->sleep_turns;
    m.met_map = MET_NOWHERE;
    m.bond = 140;
    if (o->max_hp) m.hp = (u16)clampi(m.max_hp * o->hp / o->max_hp, o->hp ? 1 : 0, m.max_hp);
    return m;
}

static void save_apply_v2(const SaveDataV2 *d)
{
    new_game();
    party_count = d->party_count;
    storage_count = d->storage_count;
    for (int i = 0; i < party_count; i++) party[i] = migrate_v2_monster(&d->party[i]);
    for (int i = 0; i < storage_count; i++) storage[i] = migrate_v2_monster(&d->storage[i]);
    for (int i = 0; i < 16 && i < ITEM_COUNT; i++) bag[i] = clampi(d->bag[i], 0, 999);
    money = clampi(d->money, 0, 999999);
    for (int i = 0; i < SP_COUNT; i++) {
        dex_seen[i] = d->seen[i] ? 1 : 0;
        dex_caught[i] = d->caught[i] ? 1 : 0;
    }
    story_flags = (d->story_flags & 0xFu) | FLAG_INTRO;
    if (party_count) story_flags |= FLAG_STARTER | FLAG_TWIN_CRYSTAL | FLAG_PIP_GIFT;
    map_load(MAP_HOME);
    player.x = 9;
    player.y = 3;
    player.facing = DIR_DOWN;
}

/* ---- v1 migration ---- */

static int save_v1_valid(const SaveDataV1 *d)
{
    if (d->magic != SAVE_MAGIC || d->version != 1u ||
        d->checksum != fnv_bytes(d, sizeof(*d) - sizeof(d->checksum)) ||
        d->party_count < 0 || d->party_count > 6)
        return 0;
    for (int i = 0; i < d->party_count; i++)
        if (d->party[i].species >= 12 || d->party[i].level < 1 || d->party[i].level > 100)
            return 0;
    return 1;
}

static void save_apply_v1(const SaveDataV1 *d)
{
    new_game();
    party_count = 0;
    for (int i = 0; i < d->party_count; i++) {
        const MonsterV1 *o = &d->party[i];
        Monster m = monster_make(V1_SPECIES[o->species], o->level);
        if (o->max_hp > 0) m.hp = (u16)(m.max_hp * (o->cur_hp > 0 ? o->cur_hp : 0) / o->max_hp);
        party[party_count++] = m;
    }
    bag[ITEM_TONIC] = clampi(d->bag[0], 0, 999);
    bag[ITEM_BIG_TONIC] = clampi(d->bag[1], 0, 999);
    bag[ITEM_LANTERN] = clampi(d->bag[2], 0, 999);
    for (int i = 0; i < 12; i++) {
        dex_seen[V1_SPECIES[i]] = d->seen[i] ? 1 : 0;
        dex_caught[V1_SPECIES[i]] = d->caught[i] ? 1 : 0;
    }
    if (d->starter_given && party_count) story_flags |= FLAG_STARTER;
}

/* ---- SRAM access ---- */

static void sram_read(void *dst, volatile u8 *sram, unsigned n)
{
    u8 *bytes = dst;
    for (unsigned i = 0; i < n; i++) bytes[i] = sram[i];
}

static void sram_write(const void *src, volatile u8 *sram, unsigned n)
{
    const u8 *bytes = src;
    for (unsigned i = 0; i < n; i++) sram[i] = bytes[i];
}

static int save_write_slot(const SaveData *data, volatile u8 *slot)
{
    EWRAM_BSS static SaveData check;
    sram_write(data, slot, sizeof(*data));
    sram_read(&check, slot, sizeof(check));
    const u8 *a = (const u8 *)data, *b = (const u8 *)&check;
    for (unsigned i = 0; i < sizeof(*data); i++)
        if (a[i] != b[i]) return 0;
    return save_valid(&check);
}

static int save_write_to(volatile u8 *sram)
{
    EWRAM_BSS static SaveData data;
    save_capture(&data);
    if (!save_valid(&data)) return 0;
    if (!save_write_slot(&data, sram + SAVE_BACKUP_OFFSET)) return 0;
    return save_write_slot(&data, sram);
}

/* 3 = loaded, 2 = migrated v2, 1 = migrated v1, 0 = nothing usable. */
static int save_load_from(volatile u8 *sram)
{
    EWRAM_BSS static SaveData data;
    EWRAM_BSS static SaveDataV2 v2;
    EWRAM_BSS static SaveDataV1 old;
    for (int slot = 0; slot < 2; slot++) {
        volatile u8 *base = sram + (slot ? SAVE_BACKUP_OFFSET : 0);
        sram_read(&data, base, sizeof(data));
        if (save_valid(&data)) {
            save_apply(&data);
            return 3;
        }
    }
    for (int slot = 0; slot < 2; slot++) {
        volatile u8 *base = sram + (slot ? SAVE_BACKUP_OFFSET : 0);
        sram_read(&v2, base, sizeof(v2));
        if (save_v2_valid(&v2)) {
            save_apply_v2(&v2);
            return 2;
        }
    }
    for (int slot = 0; slot < 2; slot++) {
        volatile u8 *base = sram + (slot ? SAVE_BACKUP_OFFSET : 0);
        sram_read(&old, base, sizeof(old));
        if (save_v1_valid(&old)) {
            save_apply_v1(&old);
            return 1;
        }
    }
    return 0;
}

static int save_write(void)
{
    return save_write_to((volatile u8 *)MEM_SRAM);
}

static int save_load(void)
{
    return save_load_from((volatile u8 *)MEM_SRAM);
}
