/* Daily Vale events. E10 calls the hooks below; save integration is described
 * in docs/handoff/events_routes.md. No event changes the traversable spine. */
typedef struct {
    u16 rolled_day;
    u8 active[8], arg[8];
    u8 caravan_map, rematch_bits[8];
    u8 festival, front_region, front_kind, front_days;
    u16 kindling_year;
    u8 kindling_claimed, visit_claimed;
    u8 courier_target, courier_pending;
    u8 festival_claimed, tourney_wins;
} EventState;
static EventState events;

typedef struct { u8 map, min_act; const char *name; } CaravanStop;
static const CaravanStop CARAVAN_ROUTE[] = {
    { MAP_BROOKMILL_TRAIL, 2, "BROOKMILL TRAIL" }, { MAP_COPPERLINE, 2, "COPPERLINE" },
    { MAP_LUMEN, 2, "LUMEN" }, { MAP_CINDER_CROSSING, 4, "CINDER CROSSING" },
    { MAP_RAILHEAD, 4, "RAILHEAD" }, { MAP_LUMEN, 2, "LUMEN" },
    { MAP_BROOKMILL, 2, "BROOKMILL" }, { MAP_TOWN, 1, "MAPLE" },
    { MAP_HERON_FEN, 3, "HERON FEN" }, { MAP_REEDWICK, 3, "REEDWICK" },
    { MAP_SALTWIND, 3, "SALTWIND" }, { MAP_PORT_BRINE, 3, "PORT BRINE" },
};
#define CARAVAN_COUNT ((int)(sizeof(CARAVAN_ROUTE) / sizeof(CARAVAN_ROUTE[0])))

typedef struct { u8 zone, species, min_act; const char *name, *place; } Outbreak;
static const Outbreak OUTBREAKS[] = {
    { ZONE_MEADOW, SP_HUMBEE, 1, "HUMBEE", "MEADOW" },
    { ZONE_BROOK_TRAIL, SP_BLINKET, 2, "BLINKET", "BROOKMILL TRAIL" },
    { ZONE_FEN_REEDS, SP_PEBBOTTER, 3, "PEBBOTTER", "HERON FEN" },
    { ZONE_CINDER_ROAD, SP_KETTLEKIN, 4, "KETTLEKIN", "CINDER ROAD" },
    { ZONE_FROSTPINE, SP_FROSTOAT, 5, "FROSTOAT", "FROSTPINE" },
    { ZONE_ASHEN, SP_PUMPKLING, 6, "PUMPKLING", "ASHEN FIELDS" },
    { ZONE_MOONVEIL, SP_MOONHARE, 7, "MOONHARE", "MOONVEIL" },
};
#define OUTBREAK_COUNT ((int)(sizeof(OUTBREAKS) / sizeof(OUTBREAKS[0])))

typedef struct { u8 trainer, map, min_act; const char *name; } Rematch;
static const Rematch REMATCHES[] = {
    { TR_LUCA, MAP_MEADOW, 1, "LUCA" }, { TR_MAE, MAP_MEADOW, 1, "MAE" },
    { TR_IDA, MAP_RISE, 1, "IDA" }, { TR_FERN, MAP_WOOD, 1, "FERN" },
    { TR_KAI, MAP_WOOD, 1, "KAI" }, { TR_ORLA, MAP_WOOD, 1, "ORLA" },
    { TR_DUNN, MAP_COPPERLINE, 2, "DUNN" }, { TR_PIA, MAP_COPPERLINE, 2, "PIA" },
    { TR_ROSS, MAP_COPPERLINE, 2, "ROSS" }, { TR_JUNO, MAP_COPPERLINE, 2, "JUNO" },
    { TR_BRIN, MAP_LAKE, 1, "BRIN" }, { TR_SELA, MAP_LAKE, 1, "SELA" },
    { TR_TOMAS, MAP_LAKE, 1, "TOMAS" },
    { TR_ARLO, MAP_NONE, 2, "ARLO" }, { TR_IONE, MAP_NONE, 2, "IONE" },
    { TR_CORRIN, MAP_NONE, 2, "CORRIN" }, { TR_LUX, MAP_NONE, 2, "LUX" },
    { TR_BRISK, MAP_NONE, 2, "BRISK" },
    { TR_FEN_TEASER, MAP_HERON_FEN, 3, "FEN TEASER" },
    { TR_FEN_BIRDER, MAP_HERON_FEN, 3, "FEN BIRDER" },
    { TR_FEN_REED_A, MAP_HERON_FEN, 3, "FEN REEDS" },
    { TR_FEN_REED_B, MAP_HERON_FEN, 3, "FEN REEDS" },
    { TR_WEST_NILS, MAP_SALTWIND, 3, "NILS" },
    { TR_WEST_PERLA, MAP_SALTWIND, 3, "PERLA" },
    { TR_CC_SURVEYOR, MAP_CINDER_CROSSING, 4, "SURVEYOR" },
    { TR_CC_RAIL, MAP_CINDER_CROSSING, 4, "RAIL" },
    { TR_RH_HOB, MAP_RAILHEAD, 4, "HOB" },
    { TR_RH_TESS, MAP_RAILHEAD, 4, "TESS" },
    { TR_N_BRYN, MAP_FROSTPINE, 5, "BRYN" },
    { TR_N_ODA, MAP_FROSTPINE, 5, "ODA" },
    { TR_N_TOVE, MAP_FROSTPINE, 5, "TOVE" },
    { TR_ROOK, MAP_ASHEN_FIELDS, 6, "ROOK" },
    { TR_PENN, MAP_ASHEN_FIELDS, 6, "PENN" },
    { TR_IVO, MAP_ASHEN_FIELDS, 6, "IVO" },
    { TR_MV_LUNA, MAP_MOONVEIL, 7, "LUNA" },
    { TR_MV_ORIN, MAP_MOONVEIL, 7, "ORIN" },
    { TR_MV_SELA, MAP_MOONVEIL, 7, "SELA" },
};
#define REMATCH_COUNT ((int)(sizeof(REMATCHES) / sizeof(REMATCHES[0])))

static u32 events_mix(u32 n)
{
    n ^= n >> 16; n *= 0x7feb352dU;
    n ^= n >> 15; n *= 0x846ca68bU;
    return n ^ (n >> 16);
}
static u32 events_random(u32 *seed) { *seed = events_mix(*seed + 0x9e3779b9U); return *seed; }
static int events_act(void)
{
    if (flag(FLAG_CREST_DREAM)) return 8;
    if (flag(FLAG_LANTERN_CREST)) return 7;
    if (flag(FLAG_RIME_CREST)) return 6;
    if (flag(FLAG_CREST_ANVIL)) return 5;
    if (flag(FLAG_TIDE_CREST)) return 4;
    if (flag(FLAG_VOLT_CREST)) return 3;
    if (flag(FLAG_STORM_CALMED)) return 2;
    return 1;
}
static int events_region(int map)
{
    switch (map) {
    case MAP_MEADOW: case MAP_WOOD: case MAP_LAKE: case MAP_RISE: return ER_HOME;
    case MAP_BROOKMILL_TRAIL: case MAP_BROOKMILL: case MAP_COPPERLINE: case MAP_LUMEN: return ER_EAST;
    case MAP_HERON_FEN: case MAP_REEDWICK: case MAP_SALTWIND: case MAP_PORT_BRINE: return ER_WEST;
    case MAP_CINDER_CROSSING: case MAP_RAILHEAD: case MAP_CINDER_ROAD: return ER_FORGE;
    case MAP_FOOTHILLS: case MAP_TIMBERLINE: case MAP_FROSTPINE: return ER_NORTH;
    case MAP_HOLLOW_DOWNS: case MAP_ASHEN_FIELDS: return ER_ASH;
    case MAP_MISTFEN: case MAP_MOONVEIL: return ER_DREAM;
    default: return ER_COUNT;
    }
}
static int events_festival_for_day(int day)
{
    int season = day_season(day), ordinal = (day - 1) % SEASON_DAYS + 1;
    if (ordinal == 10) return FEST_STARFALL;
    if (season == SEASON_SPRING && ordinal == 1) return FEST_KINDLING;
    if (season == SEASON_SUMMER && ordinal == 3) return FEST_MILLRACE;
    if (season == SEASON_AUTUMN && ordinal == 7) return FEST_LANTERN;
    if (season == SEASON_WINTER && ordinal == 5) return FEST_FROST;
    return FEST_NONE;
}
static void events_new_day_impl(void)
{
    if (events.rolled_day == gtime.day) return;
    u32 seed = time_day_seed();
    int act = events_act();
    int previous = events.caravan_map, previous_day = events.rolled_day;
    for (int i = 0; i < 8; i++) events.active[i] = events.arg[i] = events.rematch_bits[i] = 0;
    events.rolled_day = gtime.day;
    events.visit_claimed = 0;
    events.festival_claimed = events.tourney_wins = 0;
    events.festival = events_festival_for_day(gtime.day);
    int allowed = 0;
    for (int i = 0; i < OUTBREAK_COUNT; i++) if (OUTBREAKS[i].min_act <= act) allowed++;
    if (allowed && events_random(&seed) % 4 != 0) {
        events.active[0] = EV_OUTBREAK;
        events.arg[0] = (u8)(events_random(&seed) % allowed);
    }
    if (previous_day && gtime.day == previous_day + 1) {
        for (int i = 1; i <= CARAVAN_COUNT; i++) {
            int next = (previous + i) % CARAVAN_COUNT;
            if (CARAVAN_ROUTE[next].min_act <= act) { events.caravan_map = (u8)next; break; }
        }
    } else {
        events.caravan_map = 0;
        if (act < 2) events.caravan_map = 7; /* Maple remains reachable in Act I */
    }
    events.active[1] = EV_CARAVAN;
    events.arg[1] = events.caravan_map;
    if (events.front_days && previous_day + 1 == gtime.day && events.front_region < ER_COUNT &&
        events.front_kind > WX_RAIN && events.front_kind < WX_COUNT) events.front_days--;
    else {
        events.front_region = (u8)(events_random(&seed) % (act < 2 ? 1 : act < 3 ? 2 : act < 5 ? 4 : act < 7 ? 6 : 7));
        static const u8 fronts[] = { WX_STORM, WX_STORM, WX_FOG, WX_HEAT, WX_SNOW, WX_ASH, WX_FOG };
        events.front_kind = fronts[events.front_region];
        if (events.front_region == ER_NORTH && events_random(&seed) % 4 == 0)
            events.front_kind = WX_AURORA;
        events.front_days = (u8)(events_random(&seed) % 2);
    }
    static const u8 happenings[] = { EV_LOST_KIN, EV_SURGE, EV_METEOR, EV_TOURNEY, EV_TALES };
    int choice = (int)(events_random(&seed) % 8);
    if (choice < 5 && (choice != 1 || act >= 2)) events.active[2] = happenings[choice];
    if (act >= 2 && gtime.day % 7 == 3) events.active[2] = EV_NIGHT_MARKET;
    if (act >= 3 && gtime.day % 7 == 5) events.active[2] = EV_FISH_MARKET;
    if (act >= 2 && gtime.rain_days >= 3 && events_random(&seed) % 4 == 0) events.active[2] = EV_WASHOUT;
    int pool[REMATCH_COUNT], count = 0;
    for (int i = 0; i < REMATCH_COUNT; i++)
        if (REMATCHES[i].min_act <= act && trainer_beaten(REMATCHES[i].trainer)) pool[count++] = i;
    int target = 3 + (int)(events_random(&seed) % 3);
    while (count && target--) {
        int pick = (int)(events_random(&seed) % count);
        int index = pool[pick];
        events.rematch_bits[index / 8] |= (u8)(1 << (index % 8));
        pool[pick] = pool[--count];
    }
}
static void events_validate(void)
{
    if (events.rolled_day != gtime.day || events.caravan_map >= CARAVAN_COUNT ||
        events.front_region >= ER_COUNT || events.front_kind >= WX_COUNT || events.front_days > 1 ||
        events.festival >= FEST_COUNT || CARAVAN_ROUTE[events.caravan_map].min_act > events_act() ||
        events.arg[0] >= OUTBREAK_COUNT || events.active[0] >= EV_COUNT || events.active[2] >= EV_COUNT ||
        events.active[1] != EV_CARAVAN || events.arg[1] != events.caravan_map ||
        events.festival != events_festival_for_day(gtime.day) ||
        (events.courier_pending && events.courier_target >= CARAVAN_COUNT)) {
        events.rolled_day = 0;
        events.front_days = 0;
        events_new_day_impl();
    }
}
static int events_active(int ev)
{
    if (events.rolled_day != gtime.day) events_new_day_impl();
    if (ev >= EV_CARAVAN_STOP_BASE && ev < EV_CARAVAN_STOP_BASE + CARAVAN_COUNT)
        return events.active[1] == EV_CARAVAN &&
               (events.caravan_map == ev - EV_CARAVAN_STOP_BASE ||
                (ev == EV_CARAVAN_STOP_BASE + 2 && events.caravan_map == 5));
    if (ev >= EV_FEST_KINDLING && ev <= EV_FEST_STARFALL) {
        int festival = ev - EV_FEST_KINDLING + FEST_KINDLING;
        return events.festival == festival &&
               ((festival != FEST_LANTERN && festival != FEST_STARFALL) || time_is_night());
    }
    if (ev == EV_NIGHT_MARKET && !time_is_night()) return 0;
    if (ev == EV_METEOR && !time_is_night()) return 0;
    if (ev == EV_LOST_KIN_PET) return events.active[2] == EV_LOST_KIN && !events.arg[3];
    if (ev == EV_FESTIVAL) return events.festival != FEST_NONE &&
        ((events.festival != FEST_LANTERN && events.festival != FEST_STARFALL) || time_is_night());
    for (int i = 0; i < 8; i++) if (events.active[i] == ev && ev != EV_NONE) return 1;
    return 0;
}
/* Map owner can attach EVENT_BROOK_WASHOUT_PATCHES to Brookmill Trail.
 * The E5 map decoder evaluates its event predicate on map load/refresh. */
MAYBE_UNUSED static const MapPatch *events_washout_patch(int map)
{
    return map == MAP_BROOKMILL_TRAIL && events_active(EV_WASHOUT) ?
           EVENT_BROOK_WASHOUT_PATCHES : 0;
}
static int events_arg(int ev)
{
    if (!events_active(ev)) return -1;
    if (ev >= EV_CARAVAN_STOP_BASE && ev < EV_CARAVAN_STOP_BASE + CARAVAN_COUNT)
        return events.caravan_map;
    if ((ev >= EV_FEST_KINDLING && ev <= EV_FEST_STARFALL) || ev == EV_FESTIVAL) return events.festival;
    for (int i = 0; i < 8; i++) if (events.active[i] == ev) return events.arg[i];
    return -1;
}
static int events_caravan_here(int map) { return events_active(EV_CARAVAN) && CARAVAN_ROUTE[events.caravan_map].map == map; }
/* Visuals share the calendar and night gate with festival hosts; no saved state. */
static int events_visual_festival(int map)
{
    if (events.rolled_day != gtime.day) events_new_day_impl();
    switch (events.festival) {
    case FEST_KINDLING: return map == MAP_TOWN ? FEST_KINDLING : FEST_NONE;
    case FEST_MILLRACE: return map == MAP_BROOKMILL ? FEST_MILLRACE : FEST_NONE;
    case FEST_LANTERN: return map == MAP_DUSKMERE && time_is_night() ? FEST_LANTERN : FEST_NONE;
    case FEST_FROST: return map == MAP_FROSTHOLLOW ? FEST_FROST : FEST_NONE;
    case FEST_STARFALL: return map == MAP_RISE && time_is_night() ? FEST_STARFALL : FEST_NONE;
    default: return FEST_NONE;
    }
}
static int events_weather_here_impl(int map)
{
    if (map < 0 || map >= MAP_COUNT || !(MAPS[map].flags & MF_OUTDOOR)) return WX_CLEAR;
    if (events.rolled_day != gtime.day) events_new_day_impl();
    if (events_region(map) == events.front_region &&
        (events.front_kind != WX_AURORA || time_is_night())) return events.front_kind;
    if (MAPS[map].flags & MF_SNOW) return WX_SNOW;
    if (MAPS[map].flags & MF_ASH) return WX_ASH;
    return gtime.weather == WEATHER_RAIN ? WX_RAIN : WX_CLEAR;
}
static void events_wild_override_impl(int zone, WildSlot *slot)
{
    if (!slot) return;
    if (events_active(EV_OUTBREAK) && OUTBREAKS[events.arg[0]].zone == zone) {
        /* The caller's ordinary roll remains 5/6 of spawns. */
        if (rng_range(6) == 0) {
            slot->species = OUTBREAKS[events.arg[0]].species;
            return;
        }
    }
    if ((events_active(EV_METEOR) || events.festival == FEST_STARFALL) &&
        zone == ZONE_RISE && time_is_night() && rng_range(10) == 0) {
        slot->species = SP_METEORB;
        slot->when = WHEN_NIGHT;
    }
    if (events_active(EV_WASHOUT) && zone == ZONE_BROOK_REEDS && rng_range(6) == 0)
        slot->species = SP_KOIRIN;
    if (day_season(gtime.day) == SEASON_SPRING && events_act() >= 3 &&
        zone == ZONE_FEN_REEDS && rng_range(6) == 0) slot->species = SP_KOIRIN;
    if (day_season(gtime.day) == SEASON_SUMMER && zone == ZONE_MEADOW && rng_range(6) == 0)
        slot->species = SP_HUMBEE;
    if (events_weather_here_impl(cur_map) == WX_STORM &&
        (species_has_type(slot->species, T_SPARK) || species_has_type(slot->species, T_GALE))) {
        slot->min_level = (u8)clampi(slot->min_level + 2, 1, 70);
        slot->max_level = (u8)clampi(slot->max_level + 2, slot->min_level, 70);
    }
    if (events_active(EV_SURGE) && zone == ZONE_MEADOW) {
        slot->min_level = slot->min_level + 3 > 70 ? 70 : slot->min_level + 3;
        slot->max_level = slot->max_level + 3 > 70 ? 70 : slot->max_level + 3;
    }
}
static int events_rematch_ready(int trainer)
{
    if (events.rolled_day != gtime.day) events_new_day_impl();
    for (int i = 0; i < REMATCH_COUNT; i++)
        if (REMATCHES[i].trainer == trainer && trainer_beaten(trainer) &&
            (events.rematch_bits[i / 8] & (1 << (i % 8)))) return 1;
    return 0;
}
/* Winning consumes readiness but never clears first-time trainer rewards. */
static int events_rematch_used(int trainer)
{
    if (!events_rematch_ready(trainer)) return 0;
    for (int i = 0; i < REMATCH_COUNT; i++) if (REMATCHES[i].trainer == trainer) {
        events.rematch_bits[i / 8] &= (u8)~(1u << (i % 8));
        return 1;
    }
    return 0;
}
static int events_rematch_level(int trainer, int slot)
{
    if (!events_rematch_ready(trainer) || trainer < 0 || trainer >= TRAINER_COUNT ||
        slot < 0 || slot >= TRAINERS[trainer].count) return 0;
    int floor = events_act() >= 7 ? 48 : events_act() >= 5 ? 35 : events_act() >= 3 ? 23 : 16;
    return clampi(TRAINERS[trainer].level[slot] + 6, floor, 60);
}
static int events_claim(int kind, int map)
{
    if (!events_active(kind) || events.visit_claimed || cur_map != map) return 0;
    events.visit_claimed = 1;
    return 1;
}
static void events_map_entered_impl(int map)
{
    if (events.rolled_day != gtime.day) events_new_day_impl();
    (void)map; /* E10 refreshes NPC conditions and weather on entry. */
}
static const char *events_gazette_line(int i)
{
    static char line[40];
    if (events.rolled_day != gtime.day) events_new_day_impl();
    switch (i) {
    case 0:
        if (events.front_kind == WX_AURORA) str_copy(line, "AURORA OVER ");
        else if (events.front_kind == WX_FOG) str_copy(line, "FOG OVER ");
        else if (events.front_kind == WX_SNOW) str_copy(line, "SNOW OVER ");
        else if (events.front_kind == WX_HEAT) str_copy(line, "HEAT OVER ");
        else if (events.front_kind == WX_ASH) str_copy(line, "ASH OVER ");
        else str_copy(line, "STORM OVER ");
        static const char *const regions[] = { "MAPLE", "LUMEN", "HERON FEN", "RAILHEAD", "FROSTPINE", "ASHEN", "MISTFEN" };
        str_put(line, regions[events.front_region]); break;
    case 1:
        if (events_active(EV_OUTBREAK)) {
            str_copy(line, OUTBREAKS[events.arg[0]].name);
            str_put(line, " AT "); str_put(line, OUTBREAKS[events.arg[0]].place);
        } else str_copy(line, "NO OUTBREAK TODAY");
        break;
    case 2: str_copy(line, "CARAVAN: "); str_put(line, CARAVAN_ROUTE[events.caravan_map].name); break;
    case 3:
        switch (events.active[2]) {
        case EV_LOST_KIN: str_copy(line, "LOST KIN ON A ROUTE"); break;
        case EV_SURGE: str_copy(line, "BRIMMING SURGE TODAY"); break;
        case EV_METEOR: str_copy(line, "METEOR AT THE RISE"); break;
        case EV_NIGHT_MARKET: str_copy(line, "LUMEN NIGHT MARKET"); break;
        case EV_FISH_MARKET: str_copy(line, "PORT BRINE FISH MARKET"); break;
        case EV_WASHOUT: str_copy(line, "SIDE TRAIL WASHOUT"); break;
        case EV_TOURNEY: str_copy(line, "HEARTH WARDEN TOURNEY"); break;
        case EV_TALES: str_copy(line, "HEARTH TALES TODAY"); break;
        default: str_copy(line, "QUIET ROADS TODAY"); break;
        } break;
    case 4: {
        int upcoming = 0;
        for (int d = 0; d <= 2; d++) if (events_festival_for_day(gtime.day + d)) {
            upcoming = events_festival_for_day(gtime.day + d);
            break;
        }
        if (upcoming) {
            static const char *const festival_names[] = { "", "KINDLING DAY", "MILLRACE",
                "LANTERN NIGHT", "FROST FAIR", "STARFALL" };
            str_copy(line, "SOON: "); str_put(line, festival_names[upcoming]);
            break;
        }
        int count = 0;
        for (int j = 0; j < REMATCH_COUNT; j++) count += !!(events.rematch_bits[j / 8] & (1 << (j % 8)));
        str_copy(line, "WARDENS READY: "); str_put_int(line, count); break;
    }
    default: return 0;
    }
    return line;
}
