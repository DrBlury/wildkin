#!/usr/bin/env python3
"""Reproduce Oak/Ash through the production ROM's field dialogue.

Run after `make all shot`: python3 tools/tests/real_rom_battle_entry.py
All saves, scripts and captures are disposable build/qa files.
"""
from pathlib import Path
import re
import subprocess

root = Path(__file__).resolve().parents[2]
qa = root / "build/qa"
qa.mkdir(parents=True, exist_ok=True)
rom = root / "game.gba"
elf = root / "game.elf"
shot = root / "build/shot"
assert rom.is_file() and elf.is_file() and shot.is_file(), "run make all shot first"

def run(*args):
    return subprocess.run(args, cwd=root, check=True, text=True, capture_output=True).stdout

symbols = dict((name, int(address, 16)) for address, _, name in
               (line.split() for line in run("arm-none-eabi-nm", "-n", str(elf)).splitlines()
                if len(line.split()) == 3))
frame = symbols["frame_count"]
mode = symbols["game_mode"]
compiler = root / "build/make_demo_save"
run("cc", "-std=c11", "-O2", "-o", str(compiler), "tools/make_demo_save.c")
save = qa / "oak-entry.sav"
run(str(compiler), str(save), "26", "25", "16", "calm")
script = qa / "oak-entry.script"
script.write_text(f"""wait 60
tap START
wait 10
tap A
wait 90
peek {frame:08x} 4
tap A
wait 124
peek {frame:08x} 4
peek {mode:08x} 4
""" + "tap A\nwait 65\ntap A\nwait 65\ntap A\nwait 65\n" +
                  "".join("tap A\nwait 60\n" for _ in range(6)) +
                  "shot build/qa/oak-four-actors.png\n" +
                  f"peek {frame:08x} 4\npeek {mode:08x} 4\n")
output = run(str(shot), str(rom), str(script), str(save))

def reads(address):
    return [int.from_bytes(bytes.fromhex(match), "little") for match in
            re.findall(rf"^{address:08x}: ((?:[0-9a-f]{{2}} ){{3}}[0-9a-f]{{2}})$",
                       output, re.MULTILINE)]

frames = reads(frame)
modes = reads(mode)
assert len(frames) == 3 and len(modes) == 2, output
assert frames[0] == 0x80 and frames[1] > frames[0] and frames[2] > frames[1], output
assert modes == [8, 8], output
assert (qa / "oak-four-actors.png").is_file(), "missing ROM capture"
print(f"production ROM Oak/Ash: frames {[hex(n) for n in frames]}, modes {modes}; "
      "capture build/qa/oak-four-actors.png")
