/* Focused Ember Conduits and Dusk Hollows route / puzzle checks. */
#include "harness.h"

static int door_at(const Warp *w)
{
    map_load(w->map);
    return (cell_attr(w->x, w->y) & A_DOOR) != 0 &&
           w->dx < MAPS[w->dest].w && w->dy < MAPS[w->dest].h;
}

static void test_routes(void)
{
    const int maps[] = { MAP_EMBER_SPAN, MAP_COOLING_CHAMBER,
                         MAP_ROOT_GALLERY, MAP_DUSK_VAULT };
    for (unsigned i = 0; i < sizeof(maps) / sizeof(maps[0]); i++) {
        const MapDef *m = &MAPS[maps[i]];
        CHECK(m->depth && m->surface_map < MAP_COUNT && (m->flags & MF_NOFLY),
              "underground map has a valid surface anchor and no flight");
        for (int y = 0; y < m->h; y++)
            CHECK((int)strlen(m->rows[y]) == m->w, "new cave row matches map width");
    }
    CHECK(MAPS[MAP_GRAVEWOOD].tileset == TS_DUSK &&
          (MAPS[MAP_LANTERN_CRYPT].flags & MF_NOFLY),
          "Gravewood uses Dusk art; existing crypt disallows flight");
    int new_warps = 0, paired = 1, doors = 1, gated = 1;
    for (int i = 0; i < WARP_COUNT; i++) {
        const Warp *w = &WARPS[i];
        if (w->map != MAP_EMBER_SPAN && w->map != MAP_COOLING_CHAMBER &&
            w->map != MAP_ROOT_GALLERY && w->map != MAP_DUSK_VAULT &&
            !(w->map == MAP_RAILHEAD_SHAFT && w->dest == MAP_EMBER_SPAN) &&
            !(w->map == MAP_EMBER_TUNNEL && w->dest == MAP_COOLING_CHAMBER) &&
            !(w->map == MAP_BARROW_B && w->dest == MAP_DUSK_VAULT) &&
            !(w->map == MAP_GRAVEWOOD && w->dest == MAP_ROOT_GALLERY) &&
            !(w->map == MAP_DUSKMERE &&
              (w->dest == MAP_ROOT_GALLERY || w->dest == MAP_DUSK_VAULT))) continue;
        new_warps++;
        doors &= door_at(w);
        int reverse = 0;
        for (int j = 0; j < WARP_COUNT; j++)
            if (WARPS[j].map == w->dest && WARPS[j].dest == w->map &&
                WARPS[j].required_flag == w->required_flag) reverse = 1;
        paired &= reverse;
        gated &= w->required_flag == FLAG_CREST_ANVIL ||
                 w->required_flag == FLAG_RIME_CREST ||
                 w->required_flag == FLAG_DUSK_SHORTCUT ||
                 w->required_flag == FLAG_LANTERN_CREST;
    }
    CHECK(new_warps == 18 && paired && gated, "all 18 cave portals are paired and story-gated");
    CHECK(doors, "all new portal sources are real door tiles or ladders");
    int mine = -1;
    for (int i = 0; i < WARP_COUNT; i++)
        if (WARPS[i].map == MAP_RAILHEAD_SHAFT && WARPS[i].dest == MAP_COPPER_MINE)
            mine = i;
    int mine_back = -1;
    for (int i = 0; i < WARP_COUNT; i++)
        if (WARPS[i].map == MAP_COPPER_MINE && WARPS[i].dest == MAP_RAILHEAD_SHAFT)
            mine_back = i;
    CHECK(mine >= 0 && mine_back >= 0 && WARPS[mine].x == 4 && WARPS[mine].y == 9 &&
          WARPS[mine].dx == 9 && WARPS[mine].dy == 18 &&
          WARPS[mine_back].dx == 4 && WARPS[mine_back].dy == 10 &&
          WARPS[mine].required_flag == FLAG_CREST_ANVIL &&
          WARPS[mine_back].required_flag == FLAG_CREST_ANVIL &&
          door_at(&WARPS[mine]) && door_at(&WARPS[mine_back]),
          "Copper Mine and Collapsed Shaft are reciprocal Anvil-gated doors");
    flag_clear(FLAG_CREST_ANVIL);
    flag_clear(FLAG_RIME_CREST);
    flag_clear(FLAG_DUSK_SHORTCUT);
    flag_clear(FLAG_LANTERN_CREST);
    for (int i = 0; i < WARP_COUNT; i++)
        if (WARPS[i].required_flag == FLAG_CREST_ANVIL ||
            WARPS[i].required_flag == FLAG_RIME_CREST ||
            WARPS[i].required_flag == FLAG_DUSK_SHORTCUT ||
            WARPS[i].required_flag == FLAG_LANTERN_CREST)
            CHECK(!warp_is_open(&WARPS[i]), "closed crest/shortcut gate blocks early entry");
    flag_set(FLAG_CREST_ANVIL);
    flag_set(FLAG_RIME_CREST);
    int gallery = -1, shortcut = -1;
    for (int i = 0; i < WARP_COUNT; i++) {
        if (WARPS[i].map == MAP_ROOT_GALLERY && WARPS[i].dest == MAP_DUSKMERE)
            gallery = i;
        if (WARPS[i].map == MAP_DUSK_VAULT && WARPS[i].dest == MAP_DUSKMERE)
            shortcut = i;
    }
    CHECK(gallery >= 0 && shortcut >= 0 && warp_is_open(&WARPS[gallery]) &&
          !warp_is_open(&WARPS[shortcut]),
          "Rime gallery opens without opening the unsolved vault shortcut");
    int seam = -1;
    for (int i = 0; i < WARP_COUNT; i++)
        if (WARPS[i].map == MAP_COOLING_CHAMBER && WARPS[i].dest == MAP_ROOT_GALLERY)
            seam = i;
    CHECK(seam >= 0 && !warp_is_open(&WARPS[seam]),
          "the cross-region seam stays closed before Lantern Crest");
    flag_set(FLAG_LANTERN_CREST);
    CHECK(warp_is_open(&WARPS[seam]), "Lantern Crest opens the reciprocal regional seam");
}

static void test_walked_portals(void)
{
    flag_clear(FLAG_CREST_ANVIL);
    field_enter_map(MAP_RAILHEAD_SHAFT, 11, 4, DIR_UP);
    hold(KEY_UP, 16);
    CHECK(cur_map == MAP_RAILHEAD_SHAFT, "shaft ladder blocks traversal before Anvil Crest");
    flag_set(FLAG_CREST_ANVIL);
    for (int f = 0; f < 150 && cur_map == MAP_RAILHEAD_SHAFT; f++) step(KEY_UP);
    settle();
    CHECK(cur_map == MAP_EMBER_SPAN && player.x == 11 && player.y == 15,
          "Anvil Crest enters the span at its south bank");
    field_enter_map(MAP_EMBER_SPAN, 11, 15, DIR_DOWN);
    for (int f = 0; f < 150 && cur_map == MAP_EMBER_SPAN; f++) step(KEY_DOWN);
    settle();
    CHECK(cur_map == MAP_RAILHEAD_SHAFT && player.x == 11 && player.y == 4,
          "paired shaft return lands beside its door");
    field_enter_map(MAP_RAILHEAD_SHAFT, 4, 10, DIR_UP);
    for (int f = 0; f < 150 && cur_map == MAP_RAILHEAD_SHAFT; f++) step(KEY_UP);
    settle();
    CHECK(cur_map == MAP_COPPER_MINE && player.x == 9 && player.y == 18,
          "Anvil-gated Copperline branch lands before the Ember lava span");
    flag_clear(FLAG_RIME_CREST);
    field_enter_map(MAP_BARROW_B, 8, 6, DIR_UP);
    hold(KEY_UP, 16);
    CHECK(cur_map == MAP_BARROW_B, "barrow stair blocks traversal before Rime Crest");
    flag_set(FLAG_RIME_CREST);
    for (int f = 0; f < 150 && cur_map == MAP_BARROW_B; f++) step(KEY_UP);
    settle();
    CHECK(cur_map == MAP_DUSK_VAULT && player.x == 11 && player.y == 14,
          "Rime Crest enters the vault at its south approach");
}

static void test_ember(void)
{
    map_load(MAP_EMBER_SPAN);
    flood(11, 15);
    CHECK(seen_cells[2 * map_w + 11], "the iron bridge connects both banks above impassable lava");
    CHECK(MAPS[MAP_EMBER_SPAN].feat_count == 1 &&
          MAPS[MAP_EMBER_SPAN].feats[0].kind == EF_BRIDGE_V &&
          EV_LO(elev_at(11, 8)) == 0 && EV_HI(elev_at(11, 8)) == 1 &&
          EV_LO(elev_at(11, 6)) == 1 && EV_LO(elev_at(11, 10)) == 1,
          "bridge deck is one level above lava and meets both elevated banks");
    CHECK((cell_attr_raw(8, 8) & A_SOLID) && (cell_attr_raw(11, 8) & A_SOLID),
          "lava remains physically impassable below the bridge");
    map_load(MAP_COOLING_CHAMBER);
    CHECK((cell_attr(5, 10) & A_SOLID) && (cell_attr(14, 10) & A_SOLID),
          "both valves are physical solid fixtures rather than character sprites");
    flag_clear(FLAG_EMBER_COOLED);
    flag_clear(FLAG_EMBER_PRIMED);
    map_patches_reapply();
    CHECK((cell_attr_raw(9, 7) & A_SOLID) != 0, "uncooked seam is molten and blocked");
    flood(9, 12);
    CHECK(seen_cells[11 * map_w + 5] && seen_cells[11 * map_w + 14] &&
          (cell_attr(7, 11) & A_SOLID),
          "south-bank valve approach and solid clue sign are reachable");
    CHECK(!seen_cells[2 * map_w + 9], "before cooling, the south bank cannot reach the north portal");
    flood(9, 2);
    CHECK(seen_cells[2 * map_w + 10] && !seen_cells[12 * map_w + 9],
          "unsolved north arrival can safely exit without crossing molten tiles");
    field_enter_map(MAP_COOLING_CHAMBER, 14, 11, DIR_UP);
    CHECK(field_try_interact() && !flag(FLAG_EMBER_COOLED),
          "field interaction with release first does not solve the chamber");
    dialog_clear();
    field_enter_map(MAP_COOLING_CHAMBER, 5, 11, DIR_UP);
    CHECK(field_try_interact() && flag(FLAG_EMBER_PRIMED),
          "field interaction opens the marked intake");
    dialog_clear();
    field_enter_map(MAP_COOLING_CHAMBER, 14, 11, DIR_UP);
    CHECK(field_try_interact(), "field interaction turns the marked release");
    CHECK(flag(FLAG_EMBER_COOLED) && !(cell_attr_raw(9, 7) & A_SOLID) &&
          !(cell_attr_raw(10, 7) & A_SOLID),
          "intake then release permanently patches two safe basalt cells");
    map_load(MAP_COOLING_CHAMBER);
    CHECK(!(cell_attr_raw(9, 7) & A_SOLID), "cooled crossing survives reloading the room");
    flood(9, 12);
    CHECK(seen_cells[2 * map_w + 9], "solved basalt seam connects both cooling-chamber banks");
    dialog_clear();
}

static void test_dusk(void)
{
    map_load(MAP_ROOT_GALLERY);
    flood(11, 15);
    CHECK(seen_cells[3 * map_w + 4] && seen_cells[3 * map_w + 19],
          "root gallery branches to both Gravewood and Duskmere");
    map_load(MAP_DUSK_VAULT);
    CHECK((cell_attr(6, 6) & A_SOLID) && (cell_attr(12, 8) & A_SOLID) &&
          (cell_attr(17, 6) & A_SOLID),
          "root, bell, and lantern are solid visible crypt fixtures");
    flood(11, 14);
    CHECK(seen_cells[2 * map_w + 11] && seen_cells[7 * map_w + 6] &&
          seen_cells[9 * map_w + 12] && seen_cells[7 * map_w + 17],
          "south vault entrance reaches the through path and all three controls");
    flood(11, 2);
    CHECK(seen_cells[14 * map_w + 11] && seen_cells[7 * map_w + 6] &&
          seen_cells[9 * map_w + 12] && seen_cells[7 * map_w + 17],
          "north vault entrance has a safe return and reaches every control");
    flag_clear(FLAG_DUSK_FIRST);
    flag_clear(FLAG_DUSK_SECOND);
    flag_clear(FLAG_DUSK_SHORTCUT);
    map_patches_reapply();
    CHECK(cell_attr_raw(19, 4) & A_SOLID, "vault shortcut starts blocked");
    field_enter_map(MAP_DUSK_VAULT, 12, 9, DIR_UP);
    CHECK(field_try_interact() && !flag(FLAG_DUSK_FIRST) && !flag(FLAG_DUSK_SECOND),
          "wrong opening bell harmlessly resets both sequence flags");
    dialog_clear();
    field_enter_map(MAP_DUSK_VAULT, 6, 7, DIR_UP);
    CHECK(field_try_interact() && flag(FLAG_DUSK_FIRST), "root control responds from its reachable approach");
    dialog_clear();
    field_enter_map(MAP_DUSK_VAULT, 17, 7, DIR_UP);
    CHECK(field_try_interact() && !flag(FLAG_DUSK_SHORTCUT) && !flag(FLAG_DUSK_FIRST),
          "premature lantern resets without awarding a shortcut");
    dialog_clear();
    field_enter_map(MAP_DUSK_VAULT, 6, 7, DIR_UP);
    CHECK(field_try_interact(), "root begins a fresh sequence");
    dialog_clear();
    field_enter_map(MAP_DUSK_VAULT, 12, 9, DIR_UP);
    CHECK(field_try_interact() && flag(FLAG_DUSK_SECOND), "bell continues the root sequence");
    dialog_clear();
    field_enter_map(MAP_DUSK_VAULT, 17, 7, DIR_UP);
    CHECK(field_try_interact(), "lantern completes the sequence");
    CHECK(flag(FLAG_DUSK_SHORTCUT) && !(cell_attr_raw(19, 4) & A_SOLID),
          "root-bell-lantern unlocks a lasting physical shortcut");
    map_load(MAP_DUSK_VAULT);
    CHECK(!(cell_attr_raw(19, 4) & A_SOLID) && !(cell_attr_raw(19, 5) & A_SOLID),
          "both shortcut throat cells stay open after reload");
    flood(11, 14);
    CHECK(seen_cells[4 * map_w + 19] && seen_cells[5 * map_w + 20],
          "solved shortcut joins the vault floor to the reverse arrival");
    dialog_clear();
    field_enter_map(MAP_DUSKMERE, 26, 28, DIR_UP);
    for (int f = 0; f < 150 && cur_map == MAP_DUSKMERE; f++) step(KEY_UP);
    settle();
    CHECK(cur_map == MAP_DUSK_VAULT && player.x == 20 && player.y == 5,
          "Duskmere reverse shortcut enters the vault beside its arch");
    for (int f = 0; f < 40 && player.x == 20; f++) step(KEY_LEFT);
    settle();
    CHECK(cur_map == MAP_DUSK_VAULT && player.x == 19 && player.y == 5,
          "reverse arrival can step inward instead of immediately warping out");
    for (int f = 0; f < 40 && player.x == 19; f++) step(KEY_LEFT);
    settle();
    CHECK(cur_map == MAP_DUSK_VAULT && player.x == 18 && player.y == 5,
          "reverse shortcut reaches the ordinary vault floor");
    dialog_clear();
    map_load(MAP_GRAVEWOOD);
    flood(2, 20);
    CHECK(seen_cells[20 * map_w + 41] && seen_cells[13 * map_w + 10] &&
          seen_cells[28 * map_w + 20] && seen_cells[32 * map_w + 19],
          "winding woodland preserves east-west road, sinkhole and quest cells");
}

int main(void)
{
    fresh_game();
    printf("map ids: EMBER_SPAN=%d COOLING_CHAMBER=%d ROOT_GALLERY=%d DUSK_VAULT=%d\n",
           MAP_EMBER_SPAN, MAP_COOLING_CHAMBER, MAP_ROOT_GALLERY, MAP_DUSK_VAULT);
    test_routes();
    test_walked_portals();
    test_ember();
    test_dusk();
    printf("ember-hollows: %d failure(s)\n", failures);
    return failures != 0;
}
