/*
 * Two checked SRAM slots of up to 16 KB (primary at 0, backup at 16384),
 * each verified by reading it back. Version 4 stores the whole expanded
 * game (docs/EXPANSION.md 10.4):
 *
 *   - the team as full Monsters, the 240-slot LANTERN SHELF packed (BoxMon)
 *   - the bag as (item-name hash, count) pairs, so item ids can move
 *   - bit arrays for the Almanac, story flags, satchels, wardens and lore
 *   - one blob per system module (time, farm, craft, fusion, travel,
 *     quest), each with its recorded size: a blob whose size no longer
 *     matches its struct is reset instead of failing the whole load, and
 *     every module clamps what it loads (X_validate)
 *
 * Older saves are migrated: version 3 keeps everything it had; version 2
 * keeps the team, the shelf, the bag and the Almanac (each kin gets rolled
 * individuality and wakes up at home); version 1 keeps team, bag, Almanac.
 */
#define SAVE_VERSION 4u
#define SAVE_MAGIC 0x4D515354u
#define SAVE_SLOT_SIZE 16384u
#define SAVE_BACKUP_OFFSET SAVE_SLOT_SIZE
#define SAVE_V3_BACKUP_OFFSET 4096u
__attribute__((used)) static const char gba_save_type[] = "SRAM_V113";

#define BAG_SAVE_MAX 200
typedef struct { u16 code, count; } BagEntry;

#define MOD_TIME_MAX 32
#define MOD_FARM_MAX 3072
#define MOD_CRAFT_MAX 256
#define MOD_FUSION_MAX 256
#define MOD_TRAVEL_MAX 256
#define MOD_QUEST_MAX 128

typedef struct {
    u32 magic, version;
    u32 size;                        /* sizeof(SaveData) when written */
    u8 party_count, map, player_x, player_y;
    u16 storage_count, bag_count;
    u8 facing, pad0[3];
    Monster party[PARTY_MAX];
    BoxMon storage[STORAGE_MAX];
    BagEntry bag[BAG_SAVE_MAX];
    u32 money;
    u8 seen[32], caught[32];         /* bit per species (up to 256) */
    u8 flags[FLAG_BYTES], satchels[ITEM_FLAG_BYTES], wardens[TRAINER_FLAG_BYTES];
    u8 lore_known[32], lore_unread[32];
    u16 hush_steps, step_counter;
    u8 options[16];
    u16 mod_size[8];                 /* time farm craft fusion travel quest */
    u8 time[MOD_TIME_MAX];
    u8 farm[MOD_FARM_MAX];
    u8 craft[MOD_CRAFT_MAX];
    u8 fusion[MOD_FUSION_MAX];
    u8 travel[MOD_TRAVEL_MAX];
    u8 quest[MOD_QUEST_MAX];
    u32 checksum;
} SaveData;

typedef char SaveFitsSlot[sizeof(SaveData) <= SAVE_SLOT_SIZE ? 1 : -1];
typedef char LoreFits[LORE_BYTES <= 32 ? 1 : -1];
typedef char DexFits[SP_COUNT <= 256 ? 1 : -1];
typedef char ModTimeFits[sizeof(TimeState) <= MOD_TIME_MAX ? 1 : -1];
typedef char ModFarmFits[sizeof(FarmState) <= MOD_FARM_MAX ? 1 : -1];
typedef char ModCraftFits[sizeof(CraftState) <= MOD_CRAFT_MAX ? 1 : -1];
typedef char ModFusionFits[sizeof(FusionState) <= MOD_FUSION_MAX ? 1 : -1];
typedef char ModTravelFits[sizeof(TravelState) <= MOD_TRAVEL_MAX ? 1 : -1];
typedef char ModQuestFits[sizeof(QuestState) <= MOD_QUEST_MAX ? 1 : -1];

/* ---- version 3 layout (read-only, for migration) ---- */
typedef struct {
    u32 magic, version;
    int party_count, storage_count;
    Monster party[6];
    Monster storage[30];
    u16 bag[17];
    int money;
    u8 seen[32], caught[32];
    u32 story_flags, item_flags[2], trainer_flags;
    u8 lore_known[10], lore_unread[10];
    u16 hush_steps, step_counter;
    u8 options[8];
    int map, player_x, player_y, facing;
    u32 checksum;
} SaveDataV3;

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
    MonsterV2 party[6];
    MonsterV2 storage[30];
    u16 bag[16];
    int money;
    u8 seen[32], caught[32];
    u32 story_flags, item_flags;
    int map, player_x, player_y, facing;
    u32 checksum;
} SaveDataV2;


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

/* Stable code for an item: a hash of its name (ids may move between builds). */
static u16 item_code(int item)
{
    u32 h = fnv_bytes(ITEMS[item].name, str_len(ITEMS[item].name));
    return (u16)((h ^ (h >> 16)) | 1);
}

static int item_from_code(u16 code)
{
    for (int i = 0; i < ITEM_COUNT; i++)
        if (item_code(i) == code) return i;
    return -1;
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

static int boxmon_valid(const BoxMon *b)
{
    if (b->species >= SP_COUNT || b->level < 1 || b->level > MAX_LEVEL ||
        b->temper >= TEMPERAMENT_COUNT || b->trait >= TRAIT_COUNT)
        return 0;
    int known = 0;
    for (int j = 0; j < MAX_MOVES; j++) {
        if (b->moves[j] == MOVE_NONE) continue;
        if (b->moves[j] >= MOVE_COUNT) return 0;
        known++;
    }
    return known > 0;
}

static void mod_store(u8 *dst, u16 *size, const void *src, unsigned n)
{
    const u8 *p = src;
    for (unsigned i = 0; i < n; i++) dst[i] = p[i];
    *size = (u16)n;
}

/* 1 = copied; 0 = the stored blob has another size (reset the module). */
static int mod_load(void *dst, const u8 *src, u16 size, unsigned n)
{
    if (size != n) return 0;
    u8 *p = dst;
    for (unsigned i = 0; i < n; i++) p[i] = src[i];
    return 1;
}

static void save_capture(SaveData *data)
{
    u8 *raw = (u8 *)data;
    for (unsigned i = 0; i < sizeof(*data); i++) raw[i] = 0;
    data->magic = SAVE_MAGIC;
    data->version = SAVE_VERSION;
    data->size = sizeof(*data);
    data->party_count = (u8)party_count;
    data->storage_count = (u16)storage_count;
    for (int i = 0; i < PARTY_MAX; i++) data->party[i] = party[i];
    for (int i = 0; i < STORAGE_MAX; i++) data->storage[i] = storage[i];
    int n = 0;
    for (int i = 0; i < ITEM_COUNT && n < BAG_SAVE_MAX; i++)
        if (bag[i] > 0) {
            data->bag[n].code = item_code(i);
            data->bag[n].count = (u16)bag[i];
            n++;
        }
    data->bag_count = (u16)n;
    data->money = (u32)money;
    for (int i = 0; i < SP_COUNT; i++) {
        if (dex_seen[i]) data->seen[i >> 3] |= (u8)(1u << (i & 7));
        if (dex_caught[i]) data->caught[i >> 3] |= (u8)(1u << (i & 7));
    }
    for (int i = 0; i < FLAG_BYTES; i++) data->flags[i] = story_bits[i];
    for (int i = 0; i < ITEM_FLAG_BYTES; i++) data->satchels[i] = item_bits[i];
    for (int i = 0; i < TRAINER_FLAG_BYTES; i++) data->wardens[i] = trainer_bits[i];
    for (int i = 0; i < LORE_BYTES; i++) {
        data->lore_known[i] = lore_known[i];
        data->lore_unread[i] = lore_unread[i];
    }
    data->hush_steps = hush_steps;
    data->step_counter = step_counter;
    const u8 *o = (const u8 *)&opt;
    for (int i = 0; i < 16; i++) data->options[i] = o[i];
    data->map = (u8)cur_map;
    data->player_x = (u8)player.x;
    data->player_y = (u8)player.y;
    data->facing = player.facing;
    mod_store(data->time, &data->mod_size[0], &gtime, sizeof(gtime));
    mod_store(data->farm, &data->mod_size[1], &farm, sizeof(farm));
    mod_store(data->craft, &data->mod_size[2], &craft, sizeof(craft));
    mod_store(data->fusion, &data->mod_size[3], &fusion, sizeof(fusion));
    mod_store(data->travel, &data->mod_size[4], &travel, sizeof(travel));
    mod_store(data->quest, &data->mod_size[5], &quest, sizeof(quest));
    data->checksum = save_checksum(data);
}

static int save_valid(const SaveData *data)
{
    if (data->magic != SAVE_MAGIC || data->version != SAVE_VERSION || data->size != sizeof(*data) ||
        data->checksum != save_checksum(data) ||
        data->party_count > PARTY_MAX || data->storage_count > STORAGE_MAX ||
        data->bag_count > BAG_SAVE_MAX || data->money > 9999999u ||
        data->map >= MAP_COUNT || data->facing > 3 ||
        data->player_x >= MAPS[data->map].w || data->player_y >= MAPS[data->map].h ||
        ((data->flags[FLAG_STARTER >> 3] >> (FLAG_STARTER & 7) & 1) && !data->party_count))
        return 0;
    for (int i = 0; i < data->bag_count; i++)
        if (data->bag[i].count > 999) return 0;
    for (int i = 0; i < data->party_count; i++)
        if (!monster_valid(&data->party[i])) return 0;
    for (int i = 0; i < data->storage_count; i++)
        if (!boxmon_valid(&data->storage[i])) return 0;
    return 1;
}

static void save_apply(const SaveData *data)
{
    party_count = data->party_count;
    storage_count = data->storage_count;
    for (int i = 0; i < PARTY_MAX; i++) party[i] = data->party[i];
    for (int i = 0; i < STORAGE_MAX; i++) storage[i] = data->storage[i];
    for (int i = 0; i < ITEM_COUNT; i++) bag[i] = 0;
    for (int i = 0; i < data->bag_count; i++) {
        int it = item_from_code(data->bag[i].code);
        if (it >= 0) bag[it] = data->bag[i].count;
    }
    money = (int)data->money;
    for (int i = 0; i < SP_COUNT; i++) {
        dex_seen[i] = (data->seen[i >> 3] >> (i & 7)) & 1;
        dex_caught[i] = (data->caught[i >> 3] >> (i & 7)) & 1;
    }
    for (int i = 0; i < FLAG_BYTES; i++) story_bits[i] = data->flags[i];
    for (int i = 0; i < ITEM_FLAG_BYTES; i++) item_bits[i] = data->satchels[i];
    for (int i = 0; i < TRAINER_FLAG_BYTES; i++) trainer_bits[i] = data->wardens[i];
    for (int i = 0; i < LORE_BYTES; i++) {
        lore_known[i] = data->lore_known[i];
        lore_unread[i] = data->lore_unread[i];
    }
    hush_steps = data->hush_steps;
    step_counter = data->step_counter;
    u8 *o = (u8 *)&opt;
    for (int i = 0; i < 16; i++) o[i] = data->options[i];
    opt.text_speed = (u8)(opt.text_speed % TEXT_SPEED_COUNT);
    opt.battle_anims &= 1;
    opt.sound &= 1;
    opt.follower &= 1;
    opt.autosave &= 1;
    opt.music &= 1;
    opt.music_vol = (u8)(opt.music_vol % 3);
    opt.hud_clock &= 1;
    opt.battle_speed &= 1;
    opt.bike_auto &= 1;
    modules_reset();
    mod_load(&gtime, data->time, data->mod_size[0], sizeof(gtime));
    mod_load(&farm, data->farm, data->mod_size[1], sizeof(farm));
    mod_load(&craft, data->craft, data->mod_size[2], sizeof(craft));
    mod_load(&fusion, data->fusion, data->mod_size[3], sizeof(fusion));
    mod_load(&travel, data->travel, data->mod_size[4], sizeof(travel));
    mod_load(&quest, data->quest, data->mod_size[5], sizeof(quest));
    modules_validate();
    map_load(data->map);
    player.x = (s16)data->player_x;
    player.y = (s16)data->player_y;
    player.facing = data->facing;
    player.ox = player.oy = 0;
    player.moving = 0;
}

/* ---- v3 migration ---- */

static int save_v3_valid(const SaveDataV3 *d)
{
    if (d->magic != SAVE_MAGIC || d->version != 3u ||
        d->checksum != fnv_bytes(d, sizeof(*d) - sizeof(d->checksum)) ||
        d->party_count < 0 || d->party_count > 6 || d->storage_count < 0 || d->storage_count > 30 ||
        d->money < 0 || d->map < 0 || d->map > MAP_STATION)
        return 0;
    for (int i = 0; i < d->party_count; i++)
        if (!monster_valid(&d->party[i])) return 0;
    for (int i = 0; i < d->storage_count; i++)
        if (!monster_valid(&d->storage[i])) return 0;
    return 1;
}

static void save_apply_v3(const SaveDataV3 *d)
{
    new_game();
    party_count = d->party_count;
    for (int i = 0; i < party_count; i++) party[i] = d->party[i];
    storage_count = 0;
    for (int i = 0; i < d->storage_count; i++) storage_add(&d->storage[i]);
    for (int i = 0; i < 17; i++) bag[i] = clampi(d->bag[i], 0, 999);
    money = clampi(d->money, 0, 9999999);
    for (int i = 0; i < 32; i++) {
        dex_seen[i] = d->seen[i] ? 1 : 0;
        dex_caught[i] = d->caught[i] ? 1 : 0;
    }
    for (int f = 0; f < 32; f++)
        if (d->story_flags >> f & 1) flag_set(f);
    for (int i = 0; i < 64; i++)
        if (d->item_flags[i >> 5] >> (i & 31) & 1) item_take(i);
    for (int t = 0; t < 32; t++)
        if (d->trainer_flags >> t & 1) trainer_mark_beaten(t);
    for (int i = 0; i < 10; i++) {
        lore_known[i] = d->lore_known[i];
        lore_unread[i] = d->lore_unread[i];
    }
    hush_steps = d->hush_steps;
    step_counter = d->step_counter;
    opt.text_speed = (u8)(d->options[0] % TEXT_SPEED_COUNT);
    opt.battle_anims = d->options[1] & 1;
    opt.sound = d->options[2] & 1;
    opt.follower = d->options[3] & 1;
    opt.autosave = d->options[4] & 1;
    map_load(d->map);
    player.x = (s16)clampi(d->player_x, 0, MAPS[d->map].w - 1);
    player.y = (s16)clampi(d->player_y, 0, MAPS[d->map].h - 1);
    player.facing = (u8)(d->facing & 3);
    player.ox = player.oy = 0;
    player.moving = 0;
}

/* ---- v2 migration ---- */

static int save_v2_valid(const SaveDataV2 *d)
{
    if (d->magic != SAVE_MAGIC || d->version != 2u ||
        d->checksum != fnv_bytes(d, sizeof(*d) - sizeof(d->checksum)) ||
        d->party_count < 0 || d->party_count > PARTY_MAX ||
        d->storage_count < 0 || d->storage_count > 30)
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
    for (int i = 0; i < party_count; i++) party[i] = migrate_v2_monster(&d->party[i]);
    storage_count = 0;
    for (int i = 0; i < d->storage_count; i++) {
        Monster m = migrate_v2_monster(&d->storage[i]);
        storage_add(&m);
    }
    for (int i = 0; i < 16 && i < ITEM_COUNT; i++) bag[i] = clampi(d->bag[i], 0, 999);
    money = clampi(d->money, 0, 999999);
    for (int i = 0; i < 32; i++) {
        dex_seen[i] = d->seen[i] ? 1 : 0;
        dex_caught[i] = d->caught[i] ? 1 : 0;
    }
    for (int f = 0; f < 4; f++)
        if (d->story_flags >> f & 1) flag_set(f);
    flag_set(FLAG_INTRO);
    if (party_count) {
        flag_set(FLAG_STARTER);
        flag_set(FLAG_TWIN_CRYSTAL);
        flag_set(FLAG_PIP_GIFT);
    }
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
    if (d->starter_given && party_count) flag_set(FLAG_STARTER);
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

/* 4 = loaded, 3/2/1 = migrated from that version, 0 = nothing usable. */
static int save_load_from(volatile u8 *sram)
{
    EWRAM_BSS static SaveData data;
    EWRAM_BSS static SaveDataV3 v3;
    EWRAM_BSS static SaveDataV2 v2;
    EWRAM_BSS static SaveDataV1 old;
    for (int slot = 0; slot < 2; slot++) {
        volatile u8 *base = sram + (slot ? SAVE_BACKUP_OFFSET : 0);
        sram_read(&data, base, sizeof(data));
        if (save_valid(&data)) {
            save_apply(&data);
            return 4;
        }
    }
    /* older versions used 4 KB slots at 0 and 4096 */
    for (int slot = 0; slot < 2; slot++) {
        volatile u8 *base = sram + (slot ? SAVE_V3_BACKUP_OFFSET : 0);
        sram_read(&v3, base, sizeof(v3));
        if (save_v3_valid(&v3)) {
            save_apply_v3(&v3);
            return 3;
        }
    }
    for (int slot = 0; slot < 2; slot++) {
        volatile u8 *base = sram + (slot ? SAVE_V3_BACKUP_OFFSET : 0);
        sram_read(&v2, base, sizeof(v2));
        if (save_v2_valid(&v2)) {
            save_apply_v2(&v2);
            return 2;
        }
    }
    for (int slot = 0; slot < 2; slot++) {
        volatile u8 *base = sram + (slot ? SAVE_V3_BACKUP_OFFSET : 0);
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
