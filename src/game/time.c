/*
 * Game time: the clock, day counter, weather and day/night tint
 * (docs/EXPANSION.md 7.1). Owner: FARM system.
 *
 * One game minute per real second while the field runs (menus pause it);
 * a day is 24 minutes of play. The day counter turns over at 06:00, by
 * itself or when you sleep in any bed (time_sleep). Night is 20:00-05:59:
 * outdoor maps (MF_OUTDOOR, not MF_NIGHTLESS) tint warm at dusk and dawn
 * and blue at night, and grey under rain. Each new day rolls the weather;
 * rain waters the farm (farm_new_day()).
 *
 * The field calls time_tick() once per frame (script.c field_update); it
 * also drives the farm's per-frame work (farm_tick()).
 */

typedef struct {
    u16 day;            /* 1.. */
    u16 minute;         /* 0..1439 since midnight */
    u8 frames;          /* 0..59 frames into the current minute */
    u8 weather;         /* WEATHER_* for today */
    u8 rain_days;       /* days of rain so far (a dry spell makes rain likelier) */
    u8 pad;
} TimeState;

enum { WEATHER_CLEAR, WEATHER_RAIN, WEATHER_COUNT };

#define MINUTES_PER_DAY (24 * 60)
#define DAWN_MINUTE (6 * 60)        /* the day counter turns over here */
#define NIGHT_START (20 * 60)

static TimeState gtime;
static int tint_applied = -1;       /* last tint key loaded into the palettes */

static void farm_new_day(void);
static void farm_tick(void);

static void time_reset(void)
{
    gtime.day = 1;
    gtime.minute = 8 * 60;
    gtime.frames = 0;
    gtime.weather = WEATHER_CLEAR;
    gtime.rain_days = 0;
    gtime.pad = 0;
    tint_applied = -1;
}

static void time_validate(void)
{
    if (!gtime.day) gtime.day = 1;
    if (gtime.day > 9999) gtime.day = 9999;
    if (gtime.minute >= MINUTES_PER_DAY) gtime.minute = 8 * 60;
    if (gtime.frames >= 60) gtime.frames = 0;
    if (gtime.weather >= WEATHER_COUNT) gtime.weather = WEATHER_CLEAR;
    tint_applied = -1;
}

static int time_hour(void) { return gtime.minute / 60; }
static int time_is_night(void) { return gtime.minute >= NIGHT_START || gtime.minute < DAWN_MINUTE; }

/* "DAY 3  14:05" (buf: at least 16 chars). The START menu and HUD show it. */
static void time_text(char *buf)
{
    str_copy(buf, "DAY ");
    str_put_int(buf, gtime.day);
    str_put(buf, "  ");
    int h = time_hour(), m = gtime.minute % 60;
    char t[6] = { (char)('0' + h / 10), (char)('0' + h % 10), ':', (char)('0' + m / 10),
                  (char)('0' + m % 10), 0 };
    str_put(buf, t);
}

/* ---------------- weather ---------------- */

static int time_raining_here(void)
{
    const MapDef *m = &MAPS[cur_map];
    if (!(m->flags & MF_OUTDOOR) || (m->flags & (MF_NIGHTLESS | MF_DEBUG))) return 0;
    return gtime.weather == WEATHER_RAIN || (m->flags & MF_RAIN);
}

/* Today's weather: dry spells make rain likelier (about 1 day in 4). */
static void time_roll_weather(void)
{
    if (gtime.day <= 2) {   /* the first days are always clear */
        gtime.weather = WEATHER_CLEAR;
        return;
    }
    int odds = gtime.weather == WEATHER_RAIN ? 20 : 26;
    gtime.weather = (int)rng_range(100) < odds ? WEATHER_RAIN : WEATHER_CLEAR;
    if (gtime.weather == WEATHER_RAIN && gtime.rain_days < 255) gtime.rain_days++;
}

/* ---------------- tint ---------------- */

/* How dark it is outside, 0 (day) .. 16 (night), in 10-minute steps:
 * dusk 18:00 -> 20:40, dawn 04:00 -> 06:40. */
static int time_night_level(void)
{
    int m = gtime.minute;
    if (m >= 18 * 60 && m < NIGHT_START + 40) return (m - 18 * 60) / 10;
    if (m >= NIGHT_START + 40 || m < 4 * 60) return 16;
    if (m < DAWN_MINUTE + 40) return 16 - (m - 4 * 60) / 10;
    return 0;
}

static int time_tint_applies(void)
{
    const MapDef *m = &MAPS[cur_map];
    return (m->flags & MF_OUTDOOR) && !(m->flags & (MF_NIGHTLESS | MF_DEBUG));
}

/* One number for the current tint (0 = none), so the field re-tints only
 * when it changes. */
static int time_tint_key(void)
{
    if (!time_tint_applies()) return 0;
    return time_night_level() * 2 + time_raining_here() + 1;
}

/* Field palettes pass through here (field.c field_load_palettes). */
static u16 field_tint(u16 c)
{
    if (!time_tint_applies()) return c;
    int n = time_night_level(), rain = time_raining_here();
    if (!n && !rain) return c;
    int r = c & 31, g = (c >> 5) & 31, b = (c >> 10) & 31;
    if (rain) {  /* overcast: toward grey, a little darker */
        int l = (r * 5 + g * 8 + b * 3) >> 4;
        r = (r * 5 + l * 3) * 7 >> 6;
        g = (g * 5 + l * 3) * 7 >> 6;
        b = ((b * 5 + l * 3) * 7 >> 6) + 1;
    }
    if (n) {
        int warm = n < 8 ? n : 16 - n;   /* orange light mid-dusk and mid-dawn */
        if (n == 16) warm = 0;
        r = (r * (256 - n * 9) >> 8) + warm / 2;
        g = (g * (256 - n * 8) >> 8) + warm / 5;
        b = (b * (256 - n * 3) >> 8) + n / 4;
    }
    return RGB15(clampi(r, 0, 31), clampi(g, 0, 31), clampi(b, 0, 31));
}

/* Re-tint the field palettes when the tint band changed. */
static void time_update_tint(void)
{
    int key = time_tint_key();
    if (key == tint_applied) return;
    tint_applied = key;
    field_load_palettes();
}

/* ---------------- the day ---------------- */

/* Start a new day: weather, then the farm (growth, workers, the bin). */
static void time_new_day(void)
{
    if (gtime.day < 9999) gtime.day++;
    time_roll_weather();
    farm_new_day();
}

/* Called once per field frame (script.c field_update). */
static void time_tick(void)
{
    farm_tick();
    if (++gtime.frames >= 60) {
        gtime.frames = 0;
        if (++gtime.minute >= MINUTES_PER_DAY) gtime.minute = 0;
        if (gtime.minute == DAWN_MINUTE) time_new_day();
    }
    time_update_tint();
}

/* Sleep in a bed: skip to 06:00 of the next day (the screen fades). Called
 * from script.c bed_answer and the farmhouse bed. */
static void time_sleep(void)
{
    gtime.minute = DAWN_MINUTE;
    gtime.frames = 0;
    time_new_day();
    tint_applied = -1;
    if (!warp.active)
        field_begin_warp(cur_map, player.x, player.y, player.facing);  /* fade out and in */
}
