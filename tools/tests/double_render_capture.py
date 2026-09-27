#!/usr/bin/env python3
"""Build a disposable GBA ROM that opens an interactive four-kin pair bout.

Run after the normal ROM build: python3 tools/tests/double_render_capture.py
The generated translation unit and ROM stay in build/; src/main.c is untouched.
"""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[2]
build = root / "build"
build.mkdir(exist_ok=True)
main = (root / "src/main.c").read_text()
needle = "    rng_seed(REG_VCOUNT * 33u + 7u + frame_count);"
assert main.count(needle) == 1
fixture = '''    Monster first_ally = monster_make(SP_FLARIX, 15);
    Monster second_ally = monster_make(SP_PUFFLEECE, 14);
    give_monster(&first_ally);
    give_monster(&second_ally);
    static const TrainerTeam foe_a = { .name = "OAK", .count = 1,
        .species = { SP_PYREFOX }, .level = { 12 }, .scene = BSCENE_RING, .prize = 70 };
    static const TrainerTeam foe_b = { .name = "ASH", .count = 1,
        .species = { SP_AXOLURK }, .level = { 12 }, .scene = BSCENE_RING, .prize = 70 };
    battle_start_trainer_pair(&foe_a, &foe_b);
    battle_load_scene();
    canvas_clear();
    for (int actor = 0; actor < BATTLE_ACTORS; actor++) {
        battle_load_mon_gfx(actor);
        disp_sync(actor);
        battle.disp[actor].visible = 1;
    }
    battle.state = BST_ACTION;
    battle.hud_dirty = 15;
    battle.ui_dirty = 1;
'''
(build / "double_capture_main.c").write_text(main.replace(needle, fixture + needle))
subprocess.run([
    "make", "SOURCES=build/double_capture_main.c src/mem.c", "TARGET=double_capture",
    "CFLAGS=-g -O2 -Wall -Wextra -Wno-missing-field-initializers -mcpu=arm7tdmi -mthumb -mthumb-interwork -fomit-frame-pointer -ffreestanding -DGBA -Isrc",
    "double_capture.gba", "shot"
], cwd=root, check=True)
script = build / "double_capture.script"
script.write_text("wait 120\nshot build/double_capture.png\ntap A\nshot build/double_moves.png\ntap A\nshot build/double_target.png\ntap RIGHT\nshot build/double_target_second.png\ntap A\nshot build/double_second_action.png\ntap A\ntap A\nshot build/double_second_target.png\n")
subprocess.run([str(build / "shot"), "double_capture.gba", str(script)], cwd=root, check=True)
print("Captured pair action, move and both target selections in build/double_*.png")
