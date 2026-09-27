#!/usr/bin/env python3
"""Regenerate the README screenshots and animations in docs/images/.

Needs a built ROM (make), the screenshot harness (make shot) and a host C
compiler. Every clip is a scripted mGBA run on a demo save, so the media
always shows the current game:

    python3 tools/make_media.py            # everything
    python3 tools/make_media.py bout       # just one clip (see CLIPS below)
"""

import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'images')
WORK = os.path.join(ROOT, 'build', 'media')
SHOT = os.path.join(ROOT, 'build', 'shot')
ROM = os.path.join(ROOT, 'game.gba')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import make_gif  # noqa: E402

MAP_IDS = {'TOWN': 0, 'HOME': 1, 'LAB': 3, 'REST': 5, 'MEADOW': 7, 'RISE': 8, 'WOOD': 9, 'LAKE': 10,
           'LUMEN': 14, 'VOLT_HALL': 19, 'WORKS': 20, 'PORT_BRINE': 27, 'GULL_ISLE': 29, 'CURRENT_HALL': 32,
           'DROWNED_BELL': 36, 'FROSTHOLLOW': 39, 'SKY_ISLE': 41, 'RIME_HALL': 44, 'STARFALL': 48,
           'DUSKMERE': 53, 'CRYPT': 57, 'BONE_THRONE': 60, 'CINDERMOOR': 63, 'DREAMSPIRE': 65,
           'ANVIL_HALL': 69, 'CALDERA': 71, 'MIRROR_HALL': 74, 'LIBRARY': 75, 'WILLOW_ACRE': 76}


class Script:
    def __init__(self):
        self.lines = []

    def wait(self, n):
        self.lines.append('wait %d' % n)
        return self

    def tap(self, keys, n=1, gap=12):
        for _ in range(n):
            self.lines.append('tap ' + keys)
            self.wait(gap)
        return self

    def hold(self, keys, frames):
        self.lines.append('hold %s %d' % (keys, frames))
        return self

    def walk(self, keys, cells):
        return self.hold(keys, cells * 16 + 4).wait(4)

    def shot(self, name):
        self.lines.append('shot %s.png' % name)
        return self

    def rec(self, name, step=3):
        self.lines.append('rec %s %d' % (name, step))
        return self

    def stop(self):
        self.lines.append('stop')
        return self

    def boot(self):
        """Title -> CONTINUE (from the save)."""
        return self.wait(60).tap('START').wait(10).tap('A').wait(40)


def demo_save(name, map_name, x, y, calm=False, low=False):
    exe = os.path.join(ROOT, 'build', 'make_demo_save')
    if True:  # always rebuild: it includes the whole game
        subprocess.check_call(['cc', '-std=c11', '-Wno-unused-function', '-o', exe,
                               os.path.join(ROOT, 'tools', 'make_demo_save.c')])
    path = os.path.join(WORK, name + '.sav')
    args = [exe, path, str(MAP_IDS[map_name]), str(x), str(y)] + (['calm'] if calm else []) + (['low'] if low else [])
    subprocess.check_call(args, stdout=subprocess.DEVNULL)
    return path


def run(script, save=None):
    path = os.path.join(WORK, 'script.txt')
    open(path, 'w').write('\n'.join(script.lines) + '\n')
    args = [SHOT, ROM, 'script.txt'] + ([save] if save else [])
    subprocess.check_call(args, cwd=WORK, stdout=subprocess.DEVNULL)


def gif(prefix, out, delay=5, scale=2):
    frames = sorted(glob.glob(os.path.join(WORK, prefix + '_[0-9][0-9][0-9][0-9].png')))
    make_gif.main([os.path.join(OUT, out)] + frames + ['--delay', str(delay), '--scale', str(scale),
                                                       '--skip-same'])
    if os.environ.get('MEDIA_SHEET'):
        contact_sheet(frames, os.path.join(WORK, out.replace('.gif', '_sheet.png')))
    for f in frames:
        os.remove(f)


def contact_sheet(frames, path, cols=6, count=36):
    """Every n-th frame of a clip on one page, for checking a clip's timing."""
    from pixelart import write_png
    pick = frames[::max(1, len(frames) // count)][:count]
    imgs = [make_gif.read_png(f) for f in pick]
    w, h = imgs[0][0], imgs[0][1]
    rows_n = (len(imgs) + cols - 1) // cols
    rows = [[(0, 0, 0)] * (cols * (w + 2)) for _ in range(rows_n * (h + 2))]
    for i, (_, _, src) in enumerate(imgs):
        x0, y0 = (i % cols) * (w + 2), (i // cols) * (h + 2)
        for y in range(h):
            rows[y0 + y][x0:x0 + w] = src[y]
    write_png(path, cols * (w + 2), rows_n * (h + 2), rows)


def still(name, out):
    shutil.copy(os.path.join(WORK, name + '.png'), os.path.join(OUT, out))


# ---------------------------------------------------------------- clips

def clip_title():
    s = Script().wait(20).rec('title', 3).wait(150).tap('START').wait(10).tap('A').wait(50)
    s.tap('A', 6, 40).stop()
    run(s)
    gif('title', 'title.gif', delay=6)


def clip_village():
    # over the Maple Run bridge on the road, back along its lower row
    save = demo_save('village', 'TOWN', 14, 17, calm=True)
    s = Script().boot().rec('village', 3).tap('RIGHT')
    s.walk('RIGHT', 9).wait(20).walk('DOWN', 1).wait(10).walk('LEFT', 9).wait(20).stop()
    s.shot('village')
    run(s, save)
    gif('village', 'village.gif')
    still('village', 'village.png')


def clip_warden():
    save = demo_save('warden', 'MEADOW', 21, 38)
    s = Script().boot().rec('warden', 3).walk('UP', 3).wait(120).tap('A', 3, 40).wait(150).stop()
    run(s, save)
    gif('warden', 'warden.gif')


def clip_bout():
    save = demo_save('bout', 'MEADOW', 21, 38, low=True)
    s = Script().boot().walk('UP', 3).wait(120).tap('A', 3, 40).wait(150)
    # A on "X awaits your call." opens MOVES, A again uses the remembered move
    s.rec('bout', 4).tap('A').wait(16).tap('DOWN').wait(16).shot('bout_moves').tap('A', 15, 40).stop()
    run(s, save)
    gif('bout', 'bout.gif', delay=5)
    still('bout_moves', 'bout_moves.png')


def clip_lorebook():
    save = demo_save('lore', 'TOWN', 16, 19)
    s = Script().boot().rec('lore', 3).tap('SELECT').wait(20).tap('DOWN', 2, 16).tap('A').wait(20)
    s.tap('A').wait(30).hold('DOWN', 150).wait(20).tap('RIGHT').wait(30).hold('DOWN', 60).wait(20).stop()
    s.shot('lore_page')
    run(s, save)
    gif('lore', 'lorebook.gif', delay=5)
    still('lore_page', 'lorebook.png')


def clip_menus():
    save = demo_save('menus', 'TOWN', 16, 19)
    s = Script().boot().tap('START').wait(10).shot('start_menu')
    s.tap('DOWN', 2).tap('A').wait(10).tap('A').tap('A').wait(10).shot('summary_info')
    s.tap('RIGHT').wait(10).shot('summary_traits').tap('RIGHT').wait(10).shot('summary_stats')
    s.tap('B').tap('B').wait(10).tap('UP', 2).tap('A').wait(20).tap('DOWN', 6).tap('A').wait(30)
    s.shot('almanac')
    run(s, save)
    for n in ('start_menu', 'summary_traits', 'summary_stats', 'almanac'):
        still(n, n + '.png')


def clip_places():
    shots = [('lake', 'LAKE', 24, 14, True), ('wood', 'WOOD', 20, 8, True), ('rise', 'RISE', 12, 13, False),
             ('home', 'HOME', 6, 6, True), ('town_clear', 'TOWN', 12, 18, True)]
    for (name, mp, x, y, calm) in shots:
        save = demo_save(name, mp, x, y, calm)
        s = Script().boot().wait(30).shot(name)
        run(s, save)
        still(name, 'place_%s.png' % name)


def clip_world():
    """All outdoor maps stitched the way their edges connect, with names."""
    from gen_field_gfx import draw_label
    from pixelart import write_png
    mapdir = os.path.join(WORK, 'maps')
    subprocess.check_call([sys.executable, os.path.join(ROOT, 'tools', 'render_maps.py'), mapdir],
                          stdout=subprocess.DEVNULL)
    # cell origins: links in maps.h have no offsets, so neighbours share x or y
    rise_h, meadow_h = 20, 44
    layout = [('rise', 40, 0, 'STORMSTONE RISE'), ('meadow', 40, rise_h, 'WHISPER MEADOW'),
              ('town', 40, rise_h + meadow_h, 'MAPLE VILLAGE'), ('lake', 0, rise_h + meadow_h, 'MIRROR LAKE'),
              ('wood', 80, rise_h + meadow_h, 'BRAMBLEWOOD')]
    files = {'rise': '08_stormstone_rise', 'meadow': '07_whisper_meadow', 'town': '00_maple_village',
             'lake': '10_mirror_lake', 'wood': '09_bramblewood'}  # render_maps.py names
    imgs = {name: make_gif.read_png(os.path.join(mapdir, files[name] + '.png')) for (name, _, _, _) in layout}
    W = max(x * 16 + imgs[n][0] for (n, x, _, _) in layout)
    H = max(y * 16 + imgs[n][1] for (n, _, y, _) in layout)
    bg = (22, 26, 38)
    rows = [[bg] * W for _ in range(H)]
    for (name, cx, cy, _) in layout:
        w, h, src = imgs[name]
        for y in range(h):
            rows[cy * 16 + y][cx * 16:cx * 16 + w] = src[y]
    S = 5  # label pixel size
    for (name, cx, cy, label) in layout:
        w = imgs[name][0]
        tw, th = len(label) * 4 * S + 4 * S, 9 * S
        x0, y0 = cx * 16 + (w - tw) // 2, cy * 16 + 24
        glyph = Canvas1(len(label) * 4, 5)
        draw_label(glyph, 0, 0, label)
        for y in range(th):
            for x in range(tw):
                rows[y0 + y][x0 + x] = (20, 24, 40)
        for gy in range(5):
            for gx in range(len(label) * 4):
                if glyph.rows[gy][gx]:
                    for y in range(S):
                        for x in range(S):
                            rows[y0 + 2 * S + gy * S + y][x0 + 2 * S + gx * S + x] = (250, 236, 180)
    write_png(os.path.join(OUT, 'world.png'), W, H, rows)
    print('wrote world.png (%dx%d)' % (W, H))


def clip_regions():
    """One still per expansion town, Hall and lair (the player on its fly
    point or just inside its door)."""
    shots = [('lumen', 'LUMEN', 9, 18), ('brine', 'PORT_BRINE', 21, 17), ('gull', 'GULL_ISLE', 22, 14),
             ('frosthollow', 'FROSTHOLLOW', 6, 14), ('skyisle', 'SKY_ISLE', 17, 21),
             ('duskmere', 'DUSKMERE', 12, 13), ('cindermoor', 'CINDERMOOR', 19, 19),
             ('dreamspire', 'DREAMSPIRE', 24, 29), ('willow', 'WILLOW_ACRE', 19, 3),
             ('volt', 'VOLT_HALL', 7, 15), ('works', 'WORKS', 6, 8), ('current', 'CURRENT_HALL', 8, 20),
             ('rime', 'RIME_HALL', 9, 25), ('crypt', 'CRYPT', 11, 21), ('anvil', 'ANVIL_HALL', 8, 20),
             ('mirror', 'MIRROR_HALL', 2, 20), ('bell', 'DROWNED_BELL', 9, 16), ('starfall', 'STARFALL', 11, 18),
             ('throne', 'BONE_THRONE', 8, 12), ('caldera', 'CALDERA', 9, 15), ('library', 'LIBRARY', 11, 18)]
    for (name, mp, x, y) in shots:
        save = demo_save(name, mp, x, y, calm=True)
        run(Script().boot().wait(30).shot(name), save)
        still(name, 'region_%s.png' % name)
    save = demo_save('ui', 'LUMEN', 9, 18, calm=True)
    s = Script().boot().wait(30).tap('START').wait(10).shot('clock_menu')
    s.tap('DOWN', 3).tap('A').wait(30).shot('bag_pockets')
    run(s, save)
    still('clock_menu', 'ui_start_clock.png')
    still('bag_pockets', 'ui_bag.png')


def clip_elevation():
    """The Maple Run bridge (docs/ELEVATION.md): in front of it, under it
    walking north along the lane, and over it on the road."""
    save = demo_save('elev_under', 'TOWN', 20, 22, calm=True)
    s = Script().boot().wait(20).walk('UP', 3).wait(20).shot('elevation_front')
    s.walk('UP', 2).wait(20).shot('elevation_under')
    run(s, save)
    save = demo_save('elev_over', 'TOWN', 15, 17, calm=True)
    run(Script().boot().wait(20).tap('RIGHT').walk('RIGHT', 5).wait(20).shot('elevation_over'), save)
    for n in ('elevation_front', 'elevation_under', 'elevation_over'):
        still(n, n + '.png')


class Canvas1:
    """Just enough of pixelart.Canvas for draw_label: 1 bit per pixel."""
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.rows = [[0] * w for _ in range(h)]

    def put(self, x, y, rgb):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.rows[y][x] = 1


CLIPS = {
    'title': clip_title, 'village': clip_village, 'warden': clip_warden, 'bout': clip_bout,
    'lorebook': clip_lorebook, 'menus': clip_menus, 'places': clip_places, 'world': clip_world,
    'regions': clip_regions, 'elevation': clip_elevation,
}


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    for name in (argv or list(CLIPS)):
        print('--', name)
        CLIPS[name]()
    subprocess.check_call([sys.executable, os.path.join(ROOT, 'tools', 'render_gallery.py'),
                           os.path.join(OUT, 'kin.png'), '--scale', '1'])


if __name__ == '__main__':
    main(sys.argv[1:])
