#!/usr/bin/env python3
"""Capture the compiled underworld in libmGBA, using disposable checked saves.

Run `make && make shot && python3 tools/capture_underworld.py`.
Outputs only build/world-expansion/rom; never reads or writes a player's save.
"""
from pathlib import Path
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/world-expansion/rom'
FIXTURE = r'''
#include "harness.h"
#include <stddef.h>
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    const struct { const char *name; int map,x,y,hour,solved; } scenes[] = {
        {"rootwood", MAP_ROOTWOOD_PATH, 5,7,12,0},
        {"rootways", MAP_ROOTWAYS, 5,8,12,0},
        {"underflow", MAP_TIDAL_UNDERFLOW, 8,13,12,0},
        {"karst", MAP_KARST_FROST, 11,11,12,0},
        {"ember-span", MAP_EMBER_SPAN, 11,11,12,0},
        {"cooling-before", MAP_COOLING_CHAMBER, 9,11,12,0},
        {"cooling-after", MAP_COOLING_CHAMBER, 9,11,12,1},
        {"dusk-vault", MAP_DUSK_VAULT, 11,8,12,0},
        {"gravewood-day", MAP_GRAVEWOOD, 10,13,12,0},
        {"gravewood-night", MAP_GRAVEWOOD, 10,13,22,0},
        {"sea", MAP_SEA_ROUTE, 20,4,12,0}
    };
    for (unsigned i=0; i<sizeof scenes/sizeof scenes[0]; i++) {
        fresh_game();
        party_count=3;
        party[0]=monster_make(SP_FLARIX,30);
        party[1]=monster_make(SP_AXOLURK,30);
        party[2]=monster_make(SP_GOLEMIT,30);
        int flags[]={FLAG_STARTER,FLAG_INTRO,FLAG_TWIN_CRYSTAL,FLAG_SASH,FLAG_STORM_TOLD,
                     FLAG_STORM_CALMED,FLAG_VOLT_CREST,FLAG_TIDE_CREST,FLAG_CREST_ANVIL,
                     FLAG_RIME_CREST,FLAG_LANTERN_CREST,FLAG_CREST_DREAM};
        for(unsigned j=0;j<sizeof flags/sizeof flags[0];j++) flag_set(flags[j]);
        travel.crests=63;
        travel.mount=SP_AXOLURK;
        opt.follower=opt.bike_auto=opt.autosave=opt.hud_clock=0;
        opt.text_speed=TEXT_FAST;
        bag[ITEM_TOWN_MAP]=1;
        opt.registered=ITEM_TOWN_MAP+1;
        gtime.minute=scenes[i].hour*60;
        gtime.weather=WEATHER_CLEAR;
        events.front_region=ER_HOME;
        events.front_kind=WX_CLEAR;
        events.front_days=1;
        for(int m=0;m<MAP_COUNT;m++)
            if(MAPS[m].depth || (MAPS[m].flags & MF_TOWN)) travel_visited_set(m);
        for(int t=0;t<TRAINER_COUNT;t++) trainer_mark_beaten(t);
        if(scenes[i].solved) flag_set(FLAG_EMBER_COOLED);
        field_enter_map(scenes[i].map,scenes[i].x,scenes[i].y,DIR_UP);
        travel.surfing=(cell_attr(player.x,player.y)&A_WATER) && player.level==elev_floor(player.x,player.y);
        if(!save_position_safe(player.x,player.y,player.level)) {
            fprintf(stderr,"unsafe capture spawn: %s\n",scenes[i].name); return 1;
        }
        static u8 sram[32768];
        memset(sram,255,sizeof sram);
        if(!save_write_to(sram)) return 1;
        char path[1024];
        snprintf(path,sizeof path,"%s/%s.sav",argv[1],scenes[i].name);
        FILE *f=fopen(path,"wb"); if(!f) {perror(path); return 1;}
        int ok=fwrite(sram,1,sizeof sram,f)==sizeof sram;
        if(fclose(f) || !ok) return 1;
        printf("SCENE %s %d %d %d\n",scenes[i].name,scenes[i].map,scenes[i].x,scenes[i].y);
    }
    printf("LAYOUT %zu %zu\n",offsetof(Actor,level),offsetof(TravelState,puzzle));
    printf("ROOTBIT %d\n",pbit_base(MAP_ROOTWAYS));
    return 0;
}
'''


def run(*args):
    return subprocess.run(args, cwd=ROOT, check=True, text=True, capture_output=True).stdout


def read_bytes(log, address, length):
    matches = re.findall(rf'^{address:08x}:((?: [0-9a-f]{{2}}){{{length}}})$', log, re.M)
    if not matches:
        raise RuntimeError(f'missing ROM observation at {address:08x}')
    return bytes.fromhex(matches[-1])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = OUT / 'fixtures.c'
    source.write_text(FIXTURE)
    exe = OUT / 'fixtures'
    run(os.environ.get('HOSTCC', 'cc'), '-std=c11', '-w', '-I', str(ROOT / 'tools/tests'),
        str(source), '-o', str(exe))
    fixtures = run(str(exe), str(OUT))
    symbols = {}
    for line in run('arm-none-eabi-nm', '-a', 'game.elf').splitlines():
        match = re.fullmatch(r'([0-9a-fA-F]+)\s+\w\s+(\S+)', line)
        if match:
            symbols[match[2]] = int(match[1], 16)
    map_addr, player_addr = symbols['cur_map'], symbols['player']
    level_offset, puzzle_offset = map(int, re.search(r'LAYOUT (\d+) (\d+)', fixtures).groups())
    root_bit = int(re.search(r'ROOTBIT (\d+)', fixtures)[1])
    bootstrap = 'wait 90\ntap START\nwait 20\ntap A\nwait 140\n'
    results = []
    for name, map_id, x, y in re.findall(r'SCENE (\S+) (\d+) (\d+) (\d+)', fixtures):
        script = bootstrap
        script += f'peek {map_addr:x} 4\npeek {player_addr:x} 4\nshot {OUT / (name + ".png")}\n'
        if name == 'rootways':
            script += 'tap SELECT\nwait 30\n'
            script += f'shot {OUT / "atlas-underground.png"}\ntap R\nwait 20\nshot {OUT / "atlas-surface.png"}\n'
            script += 'tap B\nwait 30\nhold RIGHT 40\nwait 24\n'
            script += f'peek {symbols["travel"] + puzzle_offset + root_bit // 8:x} 1\nshot {OUT / "rootways-solved.png"}\n'
        if name == 'ember-span':
            script += 'hold UP 54\nwait 20\n'
            script += f'peek {player_addr + level_offset:x} 1\nshot {OUT / "ember-on-bridge.png"}\n'
        commands = OUT / (name + '.txt')
        commands.write_text(script)
        log = run(str(ROOT / 'build/shot'), str(ROOT / 'game.gba'), str(commands), str(OUT / (name + '.sav')))
        (OUT / (name + '.log')).write_text(log)
        if int.from_bytes(read_bytes(log, map_addr, 4), 'little') != int(map_id):
            raise RuntimeError(f'{name}: ROM did not load the requested map')
        position = read_bytes(log, player_addr, 4)
        if (int.from_bytes(position[:2], 'little'), int.from_bytes(position[2:], 'little')) != (int(x), int(y)):
            raise RuntimeError(f'{name}: ROM did not preserve the fixture position')
        if name == 'rootways' and not read_bytes(log, symbols['travel'] + puzzle_offset + root_bit // 8, 1)[0] & (1 << (root_bit % 8)):
            raise RuntimeError('ROM counterweight did not permanently open the gate')
        if name == 'ember-span' and read_bytes(log, player_addr + level_offset, 1)[0] != 1:
            raise RuntimeError('ROM player did not reach the bridge deck')
        results.append(f'{name}: verified ROM map and position; capture saved')
    results += ['rootways: counterweight gate opened through gameplay', 'ember-span: walked onto level-1 lava bridge']
    (OUT / 'validation.txt').write_text('\n'.join(results) + '\n')
    print('\n'.join(results))


if __name__ == '__main__':
    main()
