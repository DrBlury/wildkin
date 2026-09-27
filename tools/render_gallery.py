#!/usr/bin/env python3
"""Render the kin gallery (every front sprite with numbers, names and
types) straight from the generated src/gfx_monsters.h, i.e. exactly the
pixels the GBA shows.

    python3 tools/render_gallery.py OUT.png [--scale 2] [--overworld OUT2.png]
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixelart import Canvas, c15_to_rgb  # noqa: E402
from gen_field_gfx import draw_label  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_u32_array(src, name):
    m = re.search(r'%s\[[^=]*=\s*\{(.*?)\n\};' % re.escape(name), src, re.S)
    return [int(x, 16) for x in re.findall(r'0x([0-9A-Fa-f]+)', m.group(1))]


def species_info():
    src = open(os.path.join(ROOT, 'src', 'species_data.h')).read()
    body = src[src.index('static const Species SPECIES'):]
    out = []
    for m in re.finditer(r'\[SP_\w+\] = \{ "(\w+)", T_(\w+), (?:T_(\w+)|TYPE_NONE)', body):
        out.append((m.group(1), m.group(2), m.group(3)))
    return out


def blit_sprite(cv, words, pal, x0, y0, tiles_w, tiles_h):
    for ty in range(tiles_h):
        for tx in range(tiles_w):
            base = (ty * tiles_w + tx) * 8
            for y in range(8):
                row = words[base + y]
                for x in range(8):
                    i = (row >> (4 * x)) & 15
                    if i:
                        cv.put(x0 + tx * 8 + x, y0 + ty * 8 + y, c15_to_rgb(pal[i]))


TYPE_RGB = {
    'BEAST': (168, 152, 104), 'BLAZE': (240, 120, 40), 'TIDE': (96, 136, 240),
    'BLOOM': (112, 200, 72), 'SPARK': (248, 200, 40), 'FROST': (136, 216, 224),
    'BRAWL': (192, 64, 40), 'VENOM': (160, 64, 160), 'STONE': (200, 160, 96),
    'GALE': (152, 160, 240), 'DREAM': (248, 96, 152), 'SWARM': (160, 184, 32),
    'DUSK': (96, 72, 136), 'WYRM': (112, 64, 240),
    'HOLLOW': (120, 112, 128), 'RELIC': (176, 136, 72), 'METAL': (136, 152, 168),
    'ASTRAL': (72, 88, 176),
}


def main(argv):
    out = argv[0] if argv else 'build/gallery.png'
    scale = int(argv[argv.index('--scale') + 1]) if '--scale' in argv else 2
    src = open(os.path.join(ROOT, 'src', 'gfx_monsters.h')).read()
    front = parse_u32_array(src, 'mon_front_gfx')
    pals = parse_u32_array(src, 'mon_palettes')
    info = species_info()
    n = len(info)
    cols, cw, ch = 12, 80, 92
    rows = (n + cols - 1) // cols
    cv = Canvas(cols * cw, rows * ch, bg=(28, 30, 44))
    for i, (name, t1, t2) in enumerate(info):
        x0, y0 = (i % cols) * cw, (i // cols) * ch
        for yy in range(y0 + 2, y0 + ch - 2):
            for xx in range(x0 + 2, x0 + cw - 2):
                cv.put(xx, yy, (40, 44, 62))
        words = front[i * 512:(i + 1) * 512]
        pal = pals[i * 16:(i + 1) * 16]
        blit_sprite(cv, words, pal, x0 + 8, y0 + 4, 8, 8)
        draw_label(cv, x0 + 5, y0 + 70, '%03d %s' % (i + 1, name))
        for k, t in enumerate([t for t in (t1, t2) if t]):
            rgb = TYPE_RGB.get(t, (200, 200, 200))
            for yy in range(y0 + 79, y0 + 86):
                for xx in range(x0 + 5 + k * 36, x0 + 38 + k * 36):
                    cv.put(xx, yy, rgb)
            draw_label(cv, x0 + 7 + k * 36, y0 + 80, t, (255, 255, 255))
    cv.save(out, scale)
    print('wrote', out)
    if '--overworld' in argv:
        out2 = argv[argv.index('--overworld') + 1]
        ow = parse_u32_array(src, 'mon_ow_gfx')
        cv2 = Canvas(cols * 40, rows * 40, bg=(104, 176, 88))
        for i in range(n):
            words = ow[i * 6 * 128:i * 6 * 128 + 128]
            pal = pals[i * 16:(i + 1) * 16]
            blit_sprite(cv2, words, pal, (i % cols) * 40 + 4, (i // cols) * 40 + 4, 4, 4)
        cv2.save(out2, scale)
        print('wrote', out2)


if __name__ == '__main__':
    main(sys.argv[1:])
