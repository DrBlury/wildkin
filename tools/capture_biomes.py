#!/usr/bin/env python3
"""Capture all twelve biome maps from the ROM using disposable verified saves.

Run make, make shot, then python3 tools/capture_biomes.py. Outputs are confined
 to build/biome-validation/rom; no player save is opened or overwritten.
"""
from pathlib import Path
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/biome-validation/rom'
FIXTURE = r'''
#include "harness.h"
#include <stddef.h>
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    const struct { const char *name; int map, x, y, restored; } scenes[] = {
        {"mistfall", MAP_MISTFALL_GORGE, 15,9,0},
        {"mistbell", MAP_MISTBELL, 11,7,0},
        {"bellhouse", MAP_MISTBELL_BELLHOUSE, 5,6,0},
        {"rootcoil", MAP_ROOTCOIL_JUNGLE, 24,13,0},
        {"canopy", MAP_CANOPY_HEARTH, 12,7,0},
        {"lodge", MAP_CANOPY_LODGE, 5,6,0},
        {"saffron", MAP_SAFFRON_DUNES, 18,17,0},
        {"sunwell", MAP_SUNWELL, 9,12,0},
        {"cistern", MAP_SUNWELL_CISTERN, 6,7,0},
        {"coralhook", MAP_CORALHOOK_REEF, 16,12,0},
        {"rimewind", MAP_RIMEWIND_TUNDRA, 24,7,0},
        {"sporelight", MAP_SPORELIGHT_HOLLOW, 19,7,0},
        {"sunwell-restored", MAP_SUNWELL, 12,18,1},
        {"mistfall-bridge", MAP_MISTFALL_GORGE, 14,14,0}
    };
    for (unsigned i=0; i<sizeof scenes/sizeof scenes[0]; i++) {
        fresh_game();
        party_count=3;
        party[0]=monster_make(SP_FLARIX,30);
        party[1]=monster_make(SP_AXOLURK,30);
        party[2]=monster_make(SP_GOLEMIT,30);
        const int flags[]={FLAG_STARTER,FLAG_INTRO,FLAG_STORM_CALMED,FLAG_STORM_TOLD,
            FLAG_VOLT_CREST,FLAG_TIDE_CREST,FLAG_CREST_ANVIL,FLAG_RIME_CREST,
            FLAG_LANTERN_CREST,FLAG_CREST_DREAM};
        for (unsigned j=0;j<sizeof flags/sizeof flags[0];j++) flag_set(flags[j]);
        travel.crests=63;
        opt.follower=opt.bike_auto=opt.autosave=opt.hud_clock=0;
        opt.text_speed=TEXT_FAST;
        hush_steps=2000;
        gtime.minute=12*60;
        gtime.weather=WEATHER_CLEAR;
        events.front_region=ER_HOME;
        events.front_kind=WX_CLEAR;
        events.front_days=1;
        for (int t=0;t<TRAINER_COUNT;t++) trainer_mark_beaten(t);
        if (scenes[i].restored) { flag_set(FLAG_SUNWELL_IRRIGATED); quest_set(QUEST_SUNWELL_IRRIGATION,255); }
        field_enter_map(scenes[i].map,scenes[i].x,scenes[i].y,DIR_RIGHT);
        if (!save_position_safe(player.x,player.y,player.level) || npc_at(player.x,player.y)>=0) {
            fprintf(stderr,"unsafe biome capture spawn: %s (%d,%d)\n",scenes[i].name,player.x,player.y); return 1;
        }
        static u8 sram[32768];
        memset(sram,255,sizeof sram);
        if (!save_write_to(sram)) return 1;
        char path[1024];
        snprintf(path,sizeof path,"%s/%s.sav",argv[1],scenes[i].name);
        FILE *f=fopen(path,"wb"); if (!f) { perror(path); return 1; }
        int ok=fwrite(sram,1,sizeof sram,f)==sizeof sram;
        if (fclose(f) || !ok) return 1;
        printf("SCENE %s %d %d %d %d\n",scenes[i].name,scenes[i].map,player.x,player.y,player.level);
    }
    printf("FIELD %d LEVEL %zu\n",MODE_FIELD,offsetof(Actor,level));
    return 0;
}
'''


def run(*args):
    result = subprocess.run(args, cwd=ROOT, check=True, text=True, capture_output=True)
    return result.stdout


def memory(log, address, length):
    match = re.findall(rf'^{address:08x}:((?: [0-9a-f]{{2}}){{{length}}})$', log, re.M)
    if not match:
        raise RuntimeError(f'missing ROM observation at {address:08x}')
    return bytes.fromhex(match[-1])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source, exe = OUT / 'fixtures.c', OUT / 'fixtures'
    source.write_text(FIXTURE)
    run(os.environ.get('HOSTCC', 'cc'), '-std=c11', '-w', '-I', str(ROOT / 'tools/tests'),
        str(source), '-o', str(exe))
    fixtures = run(str(exe), str(OUT))
    symbols = {}
    for line in run('arm-none-eabi-nm', '-a', 'game.elf').splitlines():
        match = re.fullmatch(r'([0-9a-fA-F]+)\s+\w\s+(\S+)', line)
        if match:
            symbols[match[2]] = int(match[1], 16)
    field, level_offset = map(int, re.search(r'FIELD (\d+) LEVEL (\d+)', fixtures).groups())
    map_addr, actor_addr, mode_addr = (symbols[key] for key in ('cur_map', 'player', 'game_mode'))
    bootstrap = 'wait 90\ntap START\nwait 20\ntap A\nwait 100\n'
    evidence = []
    for name, map_id, x, y, level in re.findall(r'SCENE (\S+) (\d+) (\d+) (\d+) (\d+)', fixtures):
        movement = 'hold RIGHT 48\nwait 12\n' if name == 'mistfall-bridge' else ''
        script = bootstrap + movement
        script += (f'peek {map_addr:x} 4\npeek {actor_addr:x} 4\n'
                   f'peek {actor_addr+level_offset:x} 1\npeek {mode_addr:x} 4\n'
                   f'shot {OUT / (name + ".png")}\n')
        path = OUT / (name + '.txt')
        path.write_text(script)
        log = run(str(ROOT / 'build/shot'), str(ROOT / 'game.gba'), str(path), str(OUT / (name + '.sav')))
        (OUT / (name + '.log')).write_text(log)
        actual_map = int.from_bytes(memory(log, map_addr, 4), 'little')
        xy = memory(log, actor_addr, 4)
        actual_xy = (int.from_bytes(xy[:2], 'little'), int.from_bytes(xy[2:], 'little'))
        actual_level = memory(log, actor_addr+level_offset, 1)[0]
        actual_mode = int.from_bytes(memory(log, mode_addr, 4), 'little')
        if actual_map != int(map_id) or actual_mode != field:
            raise RuntimeError(f'{name}: ROM did not reach the requested field scene')
        if movement:
            if actual_level != 1 or not (17 <= actual_xy[0] <= 20 and actual_xy[1] == 14):
                raise RuntimeError(f'{name}: ROM did not walk onto the authored level-1 bridge deck')
        elif actual_xy != (int(x), int(y)) or actual_level != int(level):
            raise RuntimeError(f'{name}: save was relocated rather than showing the authored spawn')
        evidence.append(f'{name}: map={actual_map} position={actual_xy} level={actual_level}, FIELD verified')
    (OUT / 'verified.txt').write_text('\n'.join(evidence) + '\n')
    print('\n'.join(evidence))


if __name__ == '__main__':
    main()
