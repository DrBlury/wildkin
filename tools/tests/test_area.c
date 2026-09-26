/*
 * The ALMANAC's AREA map (travel.c kin_area_open): where a kin lives,
 * shown only once you have met it, grown kin falling back to where their
 * earlier form lives, and SELECT / B moving between the page and the map.
 */
#include "harness.h"

static int back_called;
static void back_stub(void) { back_called++; }

/* A kin that lives in the wild but grows out of nothing wild itself. */
static int wild_kin(void)
{
    static KinPlace pl[WM_PTS];
    for (int sp = 0; sp < SP_COUNT; sp++)
        if (kin_places(sp, pl) >= 2) return sp;
    return -1;
}

/* A grown kin that lives nowhere itself but whose earlier form does. */
static int grown_kin(void)
{
    static KinPlace pl[WM_PTS];
    for (int sp = 0; sp < SP_COUNT; sp++) {
        int p = species_prevo(sp);
        if (p >= 0 && !kin_places(sp, pl) && kin_places(p, pl)) return sp;
    }
    return -1;
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    fresh_game();
    give_starter();
    flag_set(FLAG_STORM_CALMED);

    /* ---- places ---- */
    int sp = wild_kin();
    CHECK(sp >= 0, "some kin lives in two places or more");
    static KinPlace pl[WM_PTS];
    int n = kin_places(sp, pl);
    int spots_ok = 1, dupes = 0;
    for (int i = 0; i < n; i++) {
        spots_ok &= pl[i].spot < WM_COUNT && pl[i].hi >= pl[i].lo && pl[i].lo > 0;
        spots_ok &= !(MAPS[pl[i].map].flags & MF_DEBUG) && map_spot(pl[i].map) == pl[i].spot;
        for (int j = 0; j < i; j++) dupes += pl[i].spot == pl[j].spot;
    }
    CHECK(spots_ok && !dupes, "each place is one town-map spot, with its levels");
    int every_zone = 1;
    for (int m = 0; m < MAP_COUNT; m++) {
        if (MAPS[m].flags & MF_DEBUG || map_spot(m) < 0) continue;
        KinPlace k = { 0 };
        if (!zone_kin_info(MAPS[m].zone, sp, &k, 0) && !zone_kin_info(MAPS[m].water_zone, sp, &k, 1)) continue;
        int found = 0;
        for (int i = 0; i < n; i++) found |= pl[i].spot == map_spot(m);
        every_zone &= found;
    }
    CHECK(every_zone, "every map it lives on shows up");

    /* ---- only once met ---- */
    dex_seen[sp] = dex_caught[sp] = 0;
    back_called = 0;
    kin_area_open(sp, back_stub);
    CHECK(game_mode == MODE_EXT && !wa.met && !wa.n, "an unmet kin's map shows no places");
    tap(KEY_B);
    CHECK(back_called == 1, "B closes the map");
    dex_seen[sp] = 1;
    kin_area_open(sp, back_stub);
    CHECK(wa.met && wa.n == n && wa.via == sp, "once met, its places are ringed");
    int first = wa.cur;
    tap(KEY_RIGHT);
    CHECK(wa.cur == (first + 1) % wa.n, "RIGHT steps to the next place");
    tap(KEY_LEFT);
    CHECK(wa.cur == first, "LEFT steps back");
    tap(KEY_B);

    /* ---- grown kin ---- */
    int g = grown_kin();
    if (g >= 0) {
        dex_seen[g] = 1;
        kin_area_open(g, back_stub);
        CHECK(wa.n > 0 && wa.via != g && wa.via >= 0, "a grown kin shows where its earlier form lives");
        tap(KEY_B);
    }

    /* ---- from the ALMANAC ---- */
    field_enter_map(MAP_TOWN, 10, 10, DIR_DOWN);
    dialog_clear();
    game_mode = MODE_FIELD;
    dex_open();
    dex_goto(sp);
    tap(KEY_A);
    CHECK(game_mode == MODE_DEX && dex.state == 1 && dex.cursor == sp, "A opens the kin's page");
    tap(KEY_SELECT);
    CHECK(game_mode == MODE_EXT && wa.sp == sp, "SELECT on the page opens its AREA map");
    tap(KEY_B);
    CHECK(game_mode == MODE_DEX && dex.state == 1 && dex.cursor == sp, "B goes back to the same page");
    tap(KEY_B);
    tap(KEY_B);
    CHECK(REG_BG0CNT == (BGCNT_CHARBLOCK(0) | BGCNT_SCREENBLOCK(SB_FIELD_BOTTOM) | BGCNT_PRIO(3)),
          "the field's layers are set up again afterwards");

    if (failures) {
        printf("%d area check(s) FAILED\n", failures);
        return 1;
    }
    printf("all area checks passed\n");
    return 0;
}
