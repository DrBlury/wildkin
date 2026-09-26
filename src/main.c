/*
 * WILDKIN -- The Brimming Storm: a creature-collecting adventure for the GBA.
 *
 * Unity build: this file includes every module so the whole game is one
 * translation unit (the host unit tests include it the same way).
 *
 *   game/gba.h        hardware registers, host shims, input, RNG, strings
 *   gfx_*.h           generated art (tools/gen_*.py): UI, monsters,
 *                     overworld tilesets/characters, battle effects
 *   game/data.h       types, 60 moves, 32 species, learnsets, items
 *   game/monster.c    stats, XP, learning, evolution, damage, catching
 *   game/gfx.c        UI canvas, variable-width text, windows, sprites
 *   game/msg.c        typewriter message box, choices, dialog queue
 *   game/party.c      team, PC storage, bag, money, catalogue flags
 *   game/field.c      metatile maps, streaming renderer, movement, NPCs
 *   game/battle.c     turn rules that queue presentation events
 *   game/anim.c       move animations
 *   game/battle_ui.c  event playback, HUD, battle menus, transitions
 *   game/menu.c       START menu, team, summary, bag, shop, PC
 *   game/dex.c        monster catalogue with scrolling detail pages
 *   game/evolve.c     evolution scene
 *   game/script.c     people, signs, items and field glue
 *   save_game.h       checked SRAM save slots (+ v1 migration)
 *
 * Build with `make`, run with `make run`, test with `make test`.
 */

#include "game/gba.h"
#include "game/options.h"
#include "game/sfx.c"
#include "gfx_ui.h"
#include "gfx_monsters.h"
#include "gfx_field.h"
#include "gfx_battle.h"
#include "game/data.h"
#include "game/lore.h"
#include "game/monster.c"
#include "game/gfx.c"
#include "game/msg.c"
#include "game/party.c"
#include "game/field.c"
#include "game/battle.c"
#include "game/anim.c"
#include "game/battle_ui.c"
#include "game/menu.c"
#include "game/dex.c"
#include "game/lorebook.c"
#include "game/evolve.c"
#include "game/script.c"
#include "game/title.c"
#include "save_game.h"

/* VRAM uploads prepared during the previous frame; runs in vblank. */
static void present(void)
{
    canvas_present();
    oam_commit();
    if (game_mode == MODE_FIELD || game_mode == MODE_START_MENU) {
        field_render_view();
        field_animate_tiles();
    }
    if ((game_mode == MODE_DEX && dex.state == 1) || (game_mode == MODE_LORE && lb.state == 2))
        panel_present();
}

static void game_update(void)
{
    switch (game_mode) {
    case MODE_FIELD: field_update(); break;
    case MODE_START_MENU: start_menu_update(); break;
    case MODE_PARTY: party_screen_update(); break;
    case MODE_SUMMARY: summary_update(); break;
    case MODE_BAG: bag_screen_update(); break;
    case MODE_DEX: dex_update(); break;
    case MODE_SHOP: shop_update(); break;
    case MODE_PC: pc_update(); break;
    case MODE_BATTLE: battle_update(); break;
    case MODE_EVOLVE: evolve_update(); break;
    case MODE_TITLE: title_update(); break;
    case MODE_LORE: lorebook_update(); break;
    case MODE_OPTIONS: options_update(); break;
    }
}

static void game_draw(void)
{
    switch (game_mode) {
    case MODE_FIELD:
    case MODE_START_MENU: field_draw(); break;
    case MODE_PARTY: party_screen_draw(); break;
    case MODE_SUMMARY: summary_draw(); break;
    case MODE_DEX: dex_draw(); break;
    case MODE_PC: pc_draw(); break;
    case MODE_BATTLE: battle_draw(); break;
    case MODE_EVOLVE: evolve_draw(); break;
    case MODE_TITLE: title_draw_sprites(); break;
    default: break;
    }
}

static void game_init(void)
{
    gfx_init_tables();
    load_ui_palettes();
    copy32(VRAM_OBJ_TILES + OT_FX * 8, fx_gfx, FX_COUNT * 4 * 8);
    copy32(VRAM_OBJ_TILES + OT_CAPSULE * 8, capsule_gfx, 4 * 4 * 8);
    field_load_objects();
    canvas_clear();
    for (int i = 0; i < 128; i++) oam_shadow[i * 4] = ATTR0_HIDE;
    REG_BG1CNT = BGCNT_CHARBLOCK(1) | BGCNT_SCREENBLOCK(SB_UI) | BGCNT_PRIO(0);
    int has_save = save_load() != 0;
    if (!has_save) {
        options_reset();
        new_game();
    }
    title_open(has_save);
}

static void read_keys(void)
{
    keys_prev = keys_now;
    keys_now = (u16)(~REG_KEYINPUT & 0x03FF);
}

/* One frame of game logic and drawing (the host tests drive this too). */
static void game_frame(void)
{
    frame_count++;
    if ((keys_now & (KEY_UP | KEY_DOWN | KEY_LEFT | KEY_RIGHT | KEY_L | KEY_R)) && keys_now == keys_prev)
        key_repeat_timer++;
    else
        key_repeat_timer = 0;
    oam_begin();
    game_update();
    game_draw();
    oam_end();
    sfx_update();
}

int main(void)
{
    REG_DISPCNT = DCNT_BLANK;
    REG_WAITCNT = 0x4317; /* faster ROM access with prefetch */
    rng_seed(0x1234567u);
    game_init();
    rng_seed(REG_VCOUNT * 33u + 7u + frame_count);
    while (1) {
        vsync();
        present();
        read_keys();
        game_frame();
    }
}
