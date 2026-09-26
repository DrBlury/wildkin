/*
 * Farming: WILLOW ACRE, soil, crops, watering, fertiliser, harvest, the
 * shipping bin, kin workers, processors and wild berry patches
 * (docs/EXPANSION.md 7.2). Owner: FARM system.
 */

typedef struct {
    u8 owned;           /* 1 once the FARM DEED is bought */
    u8 can_water;       /* uses left in the WATERING CAN */
    u8 pad[2];
    u8 cells[1024];     /* the FARM owner lays out soil/crop state here */
} FarmState;

static FarmState farm;

static void farm_reset(void)
{
    u8 *raw = (u8 *)&farm;
    for (unsigned i = 0; i < sizeof(farm); i++) raw[i] = 0;
}

static void farm_validate(void)
{
    farm.owned &= 1;
}

/* A new day began (time.c): crops grow, workers work, the bin pays out. */
static void farm_new_day(void)
{
}

static int farm_dyn_cell(int mx, int my, u16 bottom[4], u16 mid[4], u16 top[4])
{
    (void)mx; (void)my; (void)bottom; (void)mid; (void)top;
    return 0;
}

/* The farmhouse WORK BOARD (kin workers) and the SHIPPING BIN. */
MAYBE_UNUSED static void farm_workboard_open(void) { dlg_say("The work board is empty."); }
MAYBE_UNUSED static void farm_ship_open(void) { dlg_say("The shipping bin is empty."); }

/* The field's hook for cells that change at run time (field.c). */
static int dyn_cell(int mx, int my, u16 bottom[4], u16 mid[4], u16 top[4])
{
    return farm_dyn_cell(mx, my, bottom, mid, top) || travel_dyn_cell(mx, my, bottom, mid, top);
}
