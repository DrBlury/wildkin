/*
 * Game time: the clock, day counter and day/night tint (docs/EXPANSION.md
 * 7.1). Owner: FARM system.
 *
 * One game minute per real second while the field runs (menus pause it);
 * a day is 24 minutes of play. Sleeping skips to 06:00 the next day; the
 * day also rolls over by itself. Night is 20:00-05:59. Crops grow and
 * farm workers act when a new day starts (farm_new_day()).
 */

typedef struct {
    u16 day;            /* 1.. */
    u16 minute;         /* 0..1439 since midnight */
    u8 frames;          /* 0..59 frames into the current minute */
    u8 weather;         /* 0 clear, 1 rain (waters crops) */
    u8 pad[2];
} TimeState;

static TimeState gtime;

static void farm_new_day(void);

static void time_reset(void)
{
    gtime.day = 1;
    gtime.minute = 8 * 60;
    gtime.frames = 0;
    gtime.weather = 0;
}

static void time_validate(void)
{
    if (!gtime.day) gtime.day = 1;
    if (gtime.minute >= 24 * 60) gtime.minute = 8 * 60;
    if (gtime.frames >= 60) gtime.frames = 0;
    if (gtime.weather > 1) gtime.weather = 0;
}

__attribute__((unused)) static int time_hour(void) { return gtime.minute / 60; }
__attribute__((unused)) static int time_is_night(void) { return gtime.minute >= 20 * 60 || gtime.minute < 6 * 60; }

/* Field palettes pass through here (field.c): day/night tint. */
static u16 field_tint(u16 c)
{
    return c;   /* the FARM owner adds dusk / night / dawn tints */
}

/* Called once per field frame. */
static void time_tick(void)
{
    if (++gtime.frames < 60) return;
    gtime.frames = 0;
    if (++gtime.minute >= 24 * 60)
        gtime.minute = 0;
    if (gtime.minute == 6 * 60) {   /* a new day starts at dawn */
        gtime.day++;
        farm_new_day();
    }
}
