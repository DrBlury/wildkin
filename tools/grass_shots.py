#!/usr/bin/env python3
"""Screenshots of people and kin in tall grass across the regions, for
checking the grass overlay, rustle and wind animations:

    make && make shot && python3 tools/grass_shots.py [OUTDIR]
    python3 tools/grass_shots.py --compare BEFORE_DIR AFTER_DIR OUT_PREFIX

Each spot boots a demo save standing in tall grass, waits for wild kin to
appear, then walks through the grass (a still mid-step and one after the
step lands, while the rustle plays). Writes OUTDIR/<name>_<n>.png (1x)
OUTDIR/sheet.png (all stills, 1x) and OUTDIR/zoom_<n>.png (3x close-ups).
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import make_media  # noqa: E402
import make_gif  # noqa: E402

# name, map id, x, y, walk direction
SPOTS = [
    ('meadow', 7, 8, 7, 'UP'),
    ('wood', 9, 26, 13, 'UP'),
    ('lake', 10, 28, 13, 'LEFT'),
    ('copper', 13, 8, 12, 'UP'),
    ('coast', 26, 8, 8, 'UP'),
    ('snow', 38, 8, 7, 'UP'),
    ('cave', 46, 8, 18, 'UP'),
    ('ashen', 51, 8, 7, 'UP'),
    ('grave', 52, 8, 7, 'UP'),
    ('cinder', 62, 13, 24, 'UP'),
    ('moon', 64, 15, 22, 'UP'),
    ('city', 14, 31, 37, 'UP'),
]


def shoot(outdir):
    make_media.WORK = outdir
    os.makedirs(outdir, exist_ok=True)
    names = []
    for (name, mp, x, y, d) in SPOTS:
        path = os.path.join(outdir, name + '.sav')
        exe = os.path.join(ROOT, 'build', 'make_demo_save')
        if not os.path.exists(exe) or os.path.getmtime(exe) < os.path.getmtime(os.path.join(ROOT, 'game.gba')):
            subprocess.check_call(['cc', '-std=c11', '-Wno-unused-function', '-o', exe,
                                   os.path.join(ROOT, 'tools', 'make_demo_save.c')])
        subprocess.check_call([exe, path, str(mp), str(x), str(y), 'calm'], stdout=subprocess.DEVNULL)
        s = make_media.Script().boot().wait(240).shot(name + '_0')
        if name == 'meadow':  # the rustle, frame by frame
            s.rec(os.path.join(outdir, 'rec'), 2).hold('LEFT', 34).wait(24).stop()
        s.hold(d, 7).shot(name + '_1').hold(d, 9).wait(3).shot(name + '_2')
        s.wait(40).shot(name + '_3')
        make_media.run(s, path)
        names += [name + '_%d' % i for i in range(4)]
    return names


def sheet(outdir, names, path, scale=1, cols=4, crop=None, half=True):
    """Stills side by side; crop=(x, y, w, h) in 1x screen pixels."""
    from pixelart import write_png
    imgs = [make_gif.read_png(os.path.join(outdir, n + '.png')) for n in names]
    # shots are written at 2x by the harness (recorded frames at 1x)
    f = 2 if half else 1
    cx, cy, w, h = crop or (0, 0, imgs[0][0] // f, imgs[0][1] // f)
    W, H = w * scale, h * scale
    rows_n = (len(imgs) + cols - 1) // cols
    out = [[(0, 0, 0)] * (cols * (W + 2)) for _ in range(rows_n * (H + 2))]
    for i, (_, _, src) in enumerate(imgs):
        x0, y0 = (i % cols) * (W + 2), (i // cols) * (H + 2)
        for y in range(H):
            sy = (cy + y // scale) * f
            row = out[y0 + y]
            for x in range(W):
                row[x0 + x] = src[sy][(cx + x // scale) * f]
    write_png(path, cols * (W + 2), rows_n * (H + 2), out)


def compare(before, after, out):
    """Before/after contact sheets of two shot directories (same SPOTS):
    out_zoom.png -- per spot, 3x close-ups: before / after standing, before /
    after mid-step; out_full.png -- 1x screens, before | after, two spots a row."""
    tmp = os.path.dirname(os.path.abspath(out))
    pairs = []
    for (name, _, _, _, _) in SPOTS:
        for i in (0, 1):
            pairs += [os.path.join(before, '%s_%d' % (name, i)), os.path.join(after, '%s_%d' % (name, i))]
    sheet(tmp, [os.path.relpath(p, tmp) for p in pairs], out + '_zoom.png', 3, cols=4, crop=(64, 40, 112, 80))
    full = []
    for (name, _, _, _, _) in SPOTS:
        full += [os.path.join(before, name + '_0'), os.path.join(after, name + '_0')]
    sheet(tmp, [os.path.relpath(p, tmp) for p in full], out + '_full.png', 1, cols=4)


def main(argv):
    if argv and argv[0] == '--compare':
        compare(os.path.abspath(argv[1]), os.path.abspath(argv[2]), os.path.abspath(argv[3]))
        return
    outdir = os.path.abspath(argv[0] if argv else os.path.join(ROOT, 'build', 'grass'))
    names = shoot(outdir)
    sheet(outdir, names, os.path.join(outdir, 'sheet.png'))
    import glob
    rec = sorted(glob.glob(os.path.join(outdir, 'rec_*.png')))
    if rec:
        sheet(outdir, [os.path.basename(r)[:-4] for r in rec], os.path.join(outdir, 'rustle.png'), 4,
              cols=9, crop=(96, 48, 48, 64), half=False)
    # 3x close-ups around the player, three spots per page
    for k in range(0, len(names), 12):
        sheet(outdir, names[k:k + 12], os.path.join(outdir, 'zoom_%d.png' % (k // 12)), 3,
              crop=(64, 40, 112, 80))
    print('wrote', outdir)


if __name__ == '__main__':
    main(sys.argv[1:])
