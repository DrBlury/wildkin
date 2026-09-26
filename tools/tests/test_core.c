/*
 * Core checks for the expansion foundations: every tileset has asset viewer
 * pages covering all of its decor, trees always stand on real ground, the
 * registries (items, quests, fly points) are sane and the save fits.
 */
#include "harness.h"

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    game_init();

    /* asset viewer: every tileset has pages, every decor kind is on one */
    int pages_ok = 1, decor_ok = 1;
    for (int ts = 0; ts < TS_COUNT; ts++) {
        int pages = 0;
        static u8 shown[DK_COUNT];
        memset(shown, 0, sizeof(shown));
        for (int m = 0; m < MAP_COUNT; m++) {
            if (!(MAPS[m].flags & MF_DEBUG) || MAPS[m].tileset != ts) continue;
            pages++;
            for (int i = 0; i < MAPS[m].decor_count; i++) shown[MAPS[m].decor[i].kind] = 1;
        }
        if (!pages) {
            pages_ok = 0;
            printf("  tileset %s has no viewer page\n", TILESETS[ts].name);
        }
        for (int k = 0; k < DK_COUNT; k++)
            if (DECOR_DEFS[ts][k].w && !shown[k]) {
                decor_ok = 0;
                printf("  %s: decor %s is on no viewer page\n", TILESETS[ts].name, DECOR_NAMES[k]);
            }
    }
    CHECK(pages_ok, "every tileset has asset viewer pages");
    CHECK(decor_ok, "every decor kind of every tileset appears in the asset viewer");

    /* trees (overlay cells) always get real ground drawn underneath */
    int ground_ok = 1;
    for (int m = 0; m < MAP_COUNT; m++) {
        map_load(m);
        const TilesetDef *t = &TILESETS[map_tileset];
        for (int y = 0; y < map_h; y++)
            for (int x = 0; x < map_w; x++) {
                u16 v = map_cells[y * map_w + x];
                if (v >= CELL_PATH || !(t->mflags[v] & MTF_OVERLAY)) continue;
                u16 g = map_ground[y * map_w + x];
                if (g >= t->meta_count || !(t->mflags[g] & MTF_GROUND)) {
                    ground_ok = 0;
                    printf("  %s: tree at %d,%d stands on no ground\n", MAPS[m].name, x, y);
                }
            }
    }
    CHECK(ground_ok, "every tree on every map stands on a real ground tile");

    /* registries */
    int items_ok = 1;
    for (int i = 0; i < ITEM_COUNT; i++)
        if (!ITEMS[i].name || !ITEMS[i].desc || ITEMS[i].pocket >= POCKET_COUNT || ITEMS[i].icon >= ICON_COUNT)
            items_ok = 0;
    CHECK(items_ok, "every item has a name, text, pocket and icon");
    int fly_ok = 1;
    for (int i = 0; i < FLY_POINT_COUNT; i++) {
        const FlyPoint *f = &FLY_POINTS[i];
        if (f->map >= MAP_COUNT || f->x >= MAPS[f->map].w || f->y >= MAPS[f->map].h || f->map_x >= 240 ||
            f->map_y >= 160 || !f->name)
            fly_ok = 0;
        else {
            map_load(f->map);
            if (cell_attr(f->x, f->y) & (A_SOLID | A_WATER)) fly_ok = 0;
        }
    }
    CHECK(fly_ok, "fly points land on walkable cells and sit on the town map");
    int quests_ok = 1;
    for (int q = 1; q < QUEST_COUNT; q++)
        if (!QUESTS[q].name || !QUESTS[q].goal || text_width(QUESTS[q].name) > 200) quests_ok = 0;
    CHECK(quests_ok, "quests have names and goals");
    CHECK(sizeof(SaveData) <= SAVE_SLOT_SIZE, "the save fits its 16 KB slot");

    /* a full Shelf round-trips through the save */
    new_game();
    for (int i = 0; i < STORAGE_MAX; i++) {
        Monster m = monster_make(i % SP_COUNT, 5 + i % 40);
        storage_add(&m);
    }
    Monster keep = storage_get(STORAGE_MAX - 1);
    static u8 sram[32768];
    memset(sram, 0xFF, sizeof(sram));
    CHECK(storage_count == STORAGE_MAX && save_write_to(sram), "a full LANTERN SHELF saves");
    new_game();
    Monster back;
    CHECK(save_load_from(sram) == SAVE_VERSION && storage_count == STORAGE_MAX &&
              (back = storage_get(STORAGE_MAX - 1), back.species == keep.species && back.level == keep.level &&
               back.xp == keep.xp && back.pot[5] == keep.pot[5] && back.hp == back.max_hp),
          "all 240 stored kin come back exactly (and rested)");

    if (failures == 0) {
        printf("all core checks passed\n");
        return 0;
    }
    printf("%d check(s) FAILED\n", failures);
    return 1;
}
