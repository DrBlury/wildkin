/*
 * Ground transitions: blended grounds fade into the ground around them per
 * 8x8 quadrant (field.c blend_quads), tilled and watered soil join up with
 * their neighbours (farm.c soil_quads), tall crops grow into the cell
 * above instead of being cut off, and every map fits the scene tiles.
 */
#include "harness.h"

static int same4(const u16 a[4], const u16 b[4])
{
    return a[0] == b[0] && a[1] == b[1] && a[2] == b[2] && a[3] == b[3];
}

/* The bottom layer field.c would draw at (x, y) (before farm.c's hook). */
static void bottom_of(int x, int y, u16 q[4])
{
    const TilesetDef *t = tset();
    int v = map_cells[y * map_w + x];
    for (int i = 0; i < 4; i++) q[i] = t->meta_bottom[v][i];
    blend_quads(v, x, y, q);
}

static void setp(int x, int y, int flags)
{
    int pi = plot_at_xy(x, y);
    farm.plots[pi].crop = 0;
    farm.plots[pi].growth = 0;
    farm.plots[pi].flags = (u8)flags;
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();
    fresh_game();
    give_starter();
    flag_set(FLAG_STORM_CALMED);

    /* ---- blends on a real map ---- */
    int found_edge = 0, found_inside = 0, water_edge = 0, checked = 0;
    for (int m = 0; m < MAP_COUNT && checked < 40; m++) {
        if (MAPS[m].flags & MF_DEBUG || !TILESETS[MAPS[m].tileset].blend_of) continue;
        map_load(m);
        checked++;
        const TilesetDef *t = tset();
        for (int y = 1; y < map_h - 1; y++)
            for (int x = 1; x < map_w - 1; x++) {
                int v = map_cells[y * map_w + x];
                if (v >= CELL_PATH || !t->blend_of[v]) continue;
                u16 q[4];
                bottom_of(x, y, q);
                int outer = 0, water = 0;
                static const s8 dx[4] = { 0, 0, -1, 1 }, dy[4] = { -1, 1, 0, 0 };
                for (int k = 0; k < 4; k++) {
                    outer |= blend_outer_at(t->blend_of[v] - 1, x + dx[k], y + dy[k]);
                    water |= map_cells[(y + dy[k]) * map_w + x + dx[k]] == CELL_WATER;
                }
                if (outer && !same4(q, t->meta_bottom[v])) found_edge = 1;
                if (!outer && same4(q, t->meta_bottom[v])) found_inside = 1;
                /* against water alone a blended ground keeps its own edge */
                if (water && !outer && !same4(q, t->meta_bottom[v])) {
                    int diag = 0;
                    for (int ex = -1; ex <= 1; ex += 2)
                        for (int ey = -1; ey <= 1; ey += 2)
                            diag |= blend_outer_at(t->blend_of[v] - 1, x + ex, y + ey);
                    if (!diag) water_edge = 1;
                }
            }
    }
    CHECK(checked > 0, "some tilesets have ground blends");
    CHECK(found_edge, "a blended ground next to its surrounding ground fades into it");
    CHECK(found_inside, "inside a blended area the cell keeps its own tiles");
    CHECK(!water_edge, "no blend edge is drawn against water");

    /* ---- farm soil ---- */
    farm.owned = 1;
    field_enter_map(MAP_WILLOW_ACRE, 21, 15, DIR_RIGHT);
    dialog_clear();
    game_mode = MODE_FIELD;
    for (int i = 0; i < FARM_PLOTS; i++) farm.plots[i].flags = farm.plots[i].crop = 0;
    u16 b[4], m[4], tp[4];
    /* one tilled plot alone: every quadrant is an edge */
    setp(25, 15, PF_TILLED);
    farm_dyn_cell(25, 15, b, m, tp);
    int all_edges = 1;
    for (int c = 0; c < 4; c++) all_edges &= b[c] == farm_soil_q[c][farm_soil_combo[4][FARM_SOIL_DRY]];
    CHECK(all_edges, "a lone tilled plot fades into the soil on every side");
    /* a 3x3 bed: the middle plot is tilled right through */
    for (int y = 14; y <= 16; y++)
        for (int x = 24; x <= 26; x++) setp(x, y, PF_TILLED);
    farm_dyn_cell(25, 15, b, m, tp);
    int inside = 1;
    for (int c = 0; c < 4; c++) inside &= b[c] == farm_soil_q[c][farm_soil_combo[0][FARM_SOIL_DRY]];
    CHECK(inside, "inside a tilled bed there are no edges");
    /* water the middle and its right neighbour: wet joins wet, fades into dry */
    setp(25, 15, PF_TILLED | PF_WET);
    setp(26, 15, PF_TILLED | PF_WET);
    farm_dyn_cell(25, 15, b, m, tp);
    int right_joined = b[1] == farm_soil_q[1][farm_soil_combo[0][3]] && b[3] == farm_soil_q[3][farm_soil_combo[0][3]];
    int left_edge = b[0] == farm_soil_q[0][farm_soil_combo[0][4]] && b[2] == farm_soil_q[2][farm_soil_combo[0][4]];
    CHECK(right_joined, "a wet plot runs on into the wet plot beside it");
    CHECK(left_edge, "and fades out towards the dry plots");
    setp(24, 15, PF_TILLED | PF_WET);
    farm_dyn_cell(25, 15, b, m, tp);
    CHECK(b[0] == farm_soil_q[0][farm_soil_combo[0][3]], "with wet on both sides only the dry rows above and below show an edge");
    /* fertiliser shows inside a bed */
    setp(25, 15, PF_TILLED | PF_FERT);
    farm_dyn_cell(25, 15, b, m, tp);
    CHECK(b[0] == farm_soil_fert_q[0][0], "fertilised soil shows its specks");

    /* ---- tall crops ---- */
    int pi = plot_at_xy(25, 15);
    farm.plots[pi].crop = CROP_CORN + 1;
    farm.plots[pi].growth = (u8)crop_target(CROP_CORN);
    u16 crown;
    plot_overlay(&farm.plots[pi], &crown);
    int crown_drawn = 0;
    for (int i = 0; i < 4; i++) crown_drawn |= TILESETS[TS_FARM].meta_top[crown][i] != 0;
    CHECK(crown && crown_drawn, "ripe corn grows into the cell above");
    for (int i = 0; i < 4; i++) tp[i] = 0;
    farm_dyn_cell(25, 14, b, m, tp);
    CHECK(tp[0] | tp[1] | tp[2] | tp[3], "and is drawn there on the top layer");
    farm.plots[pi].crop = CROP_RADISH + 1;
    farm.plots[pi].growth = (u8)crop_target(CROP_RADISH);
    plot_overlay(&farm.plots[pi], &crown);
    int radish_top = 0;
    for (int i = 0; i < 4; i++) radish_top |= TILESETS[TS_FARM].meta_top[crown][i] != 0;
    CHECK(!radish_top, "a low crop stays in its own cell");

    /* ---- scene budget ---- */
    int budget_ok = 1;
    for (int mm = 0; mm < MAP_COUNT; mm++) {
        map_load(mm);
        field_load_tileset();
        if (decor_tiles_wanted > SCENE_TILE_MAX) {
            budget_ok = 0;
            printf("  %s needs %d scene tiles\n", MAPS[mm].name, decor_tiles_wanted);
        }
    }
    CHECK(budget_ok, "every map's tiles and decor fit the scene tiles, none dropped");

    if (failures) {
        printf("%d ground check(s) FAILED\n", failures);
        return 1;
    }
    printf("all ground checks passed\n");
    return 0;
}
