#!/usr/bin/env python3
"""Regenerate the README screenshots and animations in docs/images/.

Needs a built ROM (make), the screenshot harness (make shot) and a host C
compiler. Every clip is a scripted mGBA run on a demo save, so the media
always shows the current game:

    python3 tools/make_media.py            # everything
    python3 tools/make_media.py routes     # labeled route renders (needs Pillow)
    python3 tools/make_media.py world      # stitched outdoor layout (needs Pillow)
    python3 tools/make_media.py mill-wheel cinder-bridge heron-fog mistfen-fog caravan-arriving

Weather and caravan clips require visible ROM frame differences.
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

# Resolve IDs from the same compiled MAPS table used by the save writer.
# Explicit aliases are only for historical media names that differ from the map title.
MAP_TITLES = {
    'TOWN': 'MAPLE VILLAGE', 'HOME': 'YOUR HOUSE', 'LAB': 'ALMANAC HOUSE',
    'REST': 'HEARTH HALL', 'MEADOW': 'WHISPER MEADOW', 'RISE': 'STORMSTONE RISE',
    'WOOD': 'BRAMBLEWOOD', 'LAKE': 'MIRROR LAKE', 'LUMEN': 'LUMEN CITY',
    'WORKS': 'RESONANCE WORKS', 'GULL_ISLE': 'GULL ISLE',
    'CRYPT': 'LANTERN CRYPT', 'LIBRARY': 'DUST LIBRARY',
    'STARFALL': 'STARFALL GROTTO', 'CALDERA': 'CALDERA HEART',
}
_map_ids = None


def save_executable():
    exe = os.path.join(ROOT, 'build', 'make_demo_save')
    os.makedirs(WORK, exist_ok=True)
    subprocess.check_call(['cc', '-std=c11', '-Wno-unused-function', '-o', exe,
                           os.path.join(ROOT, 'tools', 'make_demo_save.c')])
    return exe


def map_ids(exe):
    global _map_ids
    if _map_ids is None:
        entries = subprocess.check_output([exe, '--list-maps'], text=True)
        ids = {}
        for line in entries.splitlines():
            number, title = line.split('\t', 1)
            if title in ids:
                raise ValueError('ambiguous compiled map title: ' + title)
            ids[title] = int(number)
        if 'BROOKMILL' not in ids or 'PORT BRINE' not in ids or ids['BROOKMILL'] == ids['PORT BRINE']:
            raise ValueError('incomplete or colliding compiled map listing')
        _map_ids = ids
    return _map_ids


def saved_map_id(name, exe):
    title = MAP_TITLES.get(name, name.replace('_', ' '))
    try:
        return map_ids(exe)[title]
    except KeyError as exc:
        raise ValueError('map %s (%s) not present in compiled ROM source' % (name, title)) from exc


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


def demo_save(name, map_name, x, y, calm=False, low=False, extra=()):
    exe = save_executable() if _map_ids is None else os.path.join(ROOT, 'build', 'make_demo_save')
    path = os.path.join(WORK, name + '.sav')
    args = [exe, path, str(saved_map_id(map_name, exe)), str(x), str(y)] + (['calm'] if calm else []) + (['low'] if low else []) + list(extra)
    subprocess.check_call(args, stdout=subprocess.DEVNULL)
    return path


def run(script, save=None):
    path = os.path.join(WORK, 'script.txt')
    open(path, 'w').write('\n'.join(script.lines) + '\n')
    args = [SHOT, ROM, 'script.txt'] + ([save] if save else [])
    subprocess.check_call(args, cwd=WORK, stdout=subprocess.DEVNULL)


def gif(prefix, out, delay=5, scale=2):
    """prefix: one recording, or a list of them played one after another."""
    frames = []
    for p in ([prefix] if isinstance(prefix, str) else prefix):
        frames += sorted(glob.glob(os.path.join(WORK, p + '_[0-9][0-9][0-9][0-9].png')))
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


def render_world():
    """Read the game's renderer output and its canonical edge/hint positions."""
    exe = os.path.join(ROOT, 'build', 'render_world')
    subprocess.check_call(['cc', '-std=c11', '-O2', '-Wno-unused-function', '-o', exe,
                           os.path.join(ROOT, 'tools', 'render_world.c')])
    out = os.path.join(WORK, 'world')
    os.makedirs(out, exist_ok=True)
    subprocess.check_call([exe, out])
    maps = {}
    with open(os.path.join(out, 'maps.txt')) as listing:
        for line in listing:
            mid, rest = line.rstrip('\n').split(' ', 1)
            name, w, h, outdoor, links, offs = rest.split('|')
            maps[int(mid)] = (name, int(w), int(h), outdoor == '1',
                              os.path.join(out, mid + '.rgb'))
    positions = {}
    with open(os.path.join(out, 'positions.txt')) as placed:
        for line in placed:
            mid, x, y = map(int, line.split())
            if mid not in maps or not maps[mid][3] or mid in positions:
                raise ValueError('invalid or duplicate outdoor position: %d' % mid)
            positions[mid] = (x, y)
    return maps, positions


ROUTE_STILLS = (
    ('brookmill-trail', 'BROOKMILL TRAIL'), ('brookmill', 'BROOKMILL'),
    ('heron-fen', 'HERON FEN'), ('reedwick', 'REEDWICK'),
    ('stormstep-foothills', 'STORMSTEP FOOTHILLS'), ('timberline', 'TIMBERLINE'),
    ('hollow-downs', 'HOLLOW DOWNS'), ('waychapel', 'WAYCHAPEL'),
    ('cinder-crossing', 'CINDER CROSSING'), ('railhead', 'RAILHEAD'),
    ('mistfen', 'MISTFEN'),
)


def route_image(maps, mid):
    """Actual renderer pixels at noon/clear, not a simulated gameplay frame."""
    from PIL import Image
    _, w, h, _, path = maps[mid]
    with open(path, 'rb') as rendered:
        rgb = rendered.read()
    if len(rgb) != w * h * 16 * 16 * 3:
        raise ValueError('incomplete rendered map %d' % mid)
    return Image.frombytes('RGB', (w * 16, h * 16), rgb)


def label_map(image, name, x, y):
    from PIL import ImageDraw
    from gen_field_gfx import draw_label
    glyph = Canvas1(len(name) * 4, 5)
    draw_label(glyph, 0, 0, name)
    scale = 2
    width = (glyph.w + 4) * scale
    x = max(0, min(x, image.width - width))
    y = max(0, min(y, image.height - 9 * scale))
    pen = ImageDraw.Draw(image)
    pen.rectangle((x, y, x + width - 1, y + 9 * scale - 1), fill=(20, 24, 40))
    for gy, row in enumerate(glyph.rows):
        for gx, pixel in enumerate(row):
            if pixel:
                px, py = x + (gx + 2) * scale, y + (gy + 2) * scale
                pen.rectangle((px, py, px + scale - 1, py + scale - 1), fill=(250, 236, 180))


def clip_routes():
    """Labeled full-map renders, including the indoor Waychapel rest stop."""
    maps, _ = render_world()
    destination = os.path.join(OUT, 'routes')
    os.makedirs(destination, exist_ok=True)
    exe = save_executable()
    for slug, title in ROUTE_STILLS:
        mid = map_ids(exe)[title]
        image = route_image(maps, mid)
        label_map(image, maps[mid][0], 8, 8)
        path = os.path.join(destination, slug + '.png')
        image.save(path)
        print('wrote', path)


def clip_world():
    """Stitch edge-linked and warp-only outdoor maps using WORLD_POS hints."""
    from PIL import Image
    maps, pos = render_world()
    x0 = min(x for x, _ in pos.values())
    y0 = min(y for _, y in pos.values())
    w = max(x + maps[m][1] for m, (x, _) in pos.items()) - x0
    h = max(y + maps[m][2] for m, (_, y) in pos.items()) - y0
    image = Image.new('RGB', (w * 8, h * 8), (22, 26, 38))
    for m, (x, y) in pos.items():
        source = route_image(maps, m)
        image.paste(source.resize((source.width // 2, source.height // 2),
                                  Image.Resampling.NEAREST), ((x - x0) * 8, (y - y0) * 8))
    for m, (x, y) in pos.items():
        label_map(image, maps[m][0], (x - x0) * 8 + 4, (y - y0) * 8 + 4)
    destination = os.path.join(OUT, 'routes')
    os.makedirs(destination, exist_ok=True)
    image.save(os.path.join(destination, 'world.png'))
    print('wrote routes/world.png (%dx%d, %d outdoor maps)' % (w * 8, h * 8, len(pos)))



def clip_mill_wheel():
    """Record the animated WATERWHEEL decor at Brookmill from the ROM."""
    save = demo_save('mill_wheel', 'BROOKMILL', 19, 15, calm=True, extra=['beaten'])
    run(Script().boot().wait(30).rec('mill_wheel', 3).wait(100).stop(), save)
    gif('mill_wheel', 'routes/mill-wheel.gif', delay=5)


def record_route(name, map_name, x, y, extra=(), travel=None):
    """Capture consecutive, unaltered ROM frames on a deterministic demo save."""
    save = demo_save(name, map_name, x, y, calm=True, extra=('beaten',) + extra)
    for stale in route_frames(name):
        os.remove(stale)
    script = Script().boot().wait(32).rec(name, 4).wait(18)
    if travel:
        script.tap(travel).hold(travel, 80).wait(22)
    else:
        script.wait(72)
    run(script.stop(), save)
    return name


def route_frames(prefix):
    return sorted(glob.glob(os.path.join(WORK, prefix + '_[0-9][0-9][0-9][0-9].png')))


def assert_route_change(first, second, min_pixels=500):
    """A state transition must alter the game image, not just repeat a still."""
    from PIL import Image, ImageChops
    a, b = route_frames(first), route_frames(second)
    if len(a) < 5 or len(b) < 5:
        raise RuntimeError('insufficient game frames for route clip')
    # Identical camera/player coordinates before movement; skip the title/boot.
    before, after = Image.open(a[1]).convert('RGB'), Image.open(b[1]).convert('RGB')
    changed = sum(1 for p in ImageChops.difference(before, after).getdata() if p != (0, 0, 0))
    if changed < min_pixels:
        raise RuntimeError('route states do not differ visibly (%d pixels)' % changed)
    frames = b[1:]
    unique = len({Image.open(f).convert('RGB').tobytes() for f in frames})
    if unique < 4:
        raise RuntimeError('route recording is effectively static (%d unique frames)' % unique)
    print('verified %s -> %s: %d state pixels, %d unique motion frames' %
          (first, second, changed, unique))


def clip_cinder_bridge():
    """Actual Cinder Crossing broken span, then the repaired walkable deck."""
    before = record_route('cinder_before', 'CINDER_CROSSING', 5, 20, travel='RIGHT')
    after = record_route('cinder_after', 'CINDER_CROSSING', 5, 20,
                         extra=('bridge-built',), travel='RIGHT')
    assert_route_change(before, after)
    gif([before, after], 'routes/cinder-bridge.gif', delay=6)


def require_fog_visuals():
    with open(os.path.join(ROOT, 'src', 'game', 'farm.c')) as field:
        if 'case WX_FOG:' not in field.read():
            raise RuntimeError('WX_FOG has no field renderer yet; defer fog GIF until weather visuals merge')


def clip_heron_fog():
    # When the weather branch draws WX_FOG, compare this against the clear save.
    record_route('heron_clear', 'HERON_FEN', 22, 19, extra=('front-clear',))
    record_route('heron_fog', 'HERON_FEN', 22, 19, extra=('front-west',))
    require_fog_visuals()
    assert_route_change('heron_clear', 'heron_fog', min_pixels=4000)
    gif(['heron_clear', 'heron_fog'], 'routes/heron-fog.gif')


def clip_mistfen_fog():
    # The lantern crest opens a path; fog lifting also requires field visuals.
    record_route('mist_fog', 'MISTFEN', 23, 52, extra=('front-dream',), travel='RIGHT')
    record_route('mist_clear', 'MISTFEN', 23, 52, extra=('front-clear', 'mist-lifted'), travel='RIGHT')
    require_fog_visuals()
    assert_route_change('mist_fog', 'mist_clear', min_pixels=4000)
    gif(['mist_fog', 'mist_clear'], 'routes/mistfen-fog.gif')


def clip_caravan_arriving():
    """Record the actual day rollover: caravan stop 5 -> Brookmill stop 6."""
    save = demo_save('caravan_eve', 'BROOKMILL', 11, 13, calm=True,
                     extra=('beaten', 'caravan-eve'))
    for stale in route_frames('caravan_arrive'):
        os.remove(stale)
    run(Script().boot().rec('caravan_arrive', 3).wait(125).stop(), save)
    frames = route_frames('caravan_arrive')
    if len(frames) < 35:
        raise RuntimeError('not enough frames to show the daily caravan arrival')
    from PIL import Image
    # The covered wagon's cyan roof is in the existing farm OBJ palette. Track
    # its screen-space position, not just whole-frame differences at daybreak.
    roof_positions = []
    for path in frames:
        image = Image.open(path).convert('RGB')
        roof = [x for y in range(45, 68) for x in range(20, 150)
                if image.getpixel((x, y)) == (165, 214, 255)]
        if len(roof) >= 60:
            roof_positions.append(min(roof))
    if len(set(roof_positions)) < 4 or max(roof_positions, default=0) - min(roof_positions, default=0) < 24:
        raise RuntimeError('caravan wagon did not move visibly across multiple ROM frames')
    print('verified caravan wagon movement: %d pixels' %
          (max(roof_positions) - min(roof_positions)))
    gif('caravan_arrive', 'routes/caravan-arriving.gif', delay=6)


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
    s = Script().boot().wait(20).walk('UP', 1).wait(20).shot('elevation_front')
    s.walk('UP', 2).wait(20).shot('elevation_under')
    run(s, save)
    save = demo_save('elev_over', 'TOWN', 15, 17, calm=True)
    run(Script().boot().wait(20).tap('RIGHT').walk('RIGHT', 5).wait(20).shot('elevation_over'), save)
    for n in ('elevation_front', 'elevation_under', 'elevation_over'):
        still(n, n + '.png')


CROP_SEASONS = {  # farm.c CROPS[].seasons
    'GLOWBERRY': 'SPRING WINTER', 'EMBERBERRY': 'SUMMER AUTUMN', 'TIDEBERRY': 'SPRING SUMMER',
    'RADISH': 'SPRING AUTUMN WINTER', 'CARROT': 'SPRING AUTUMN', 'POTATO': 'SPRING AUTUMN',
    'PUMPKIN': 'AUTUMN', 'CHILI': 'SUMMER', 'TOMATO': 'SUMMER', 'CORN': 'SUMMER AUTUMN',
    'SUNFLOWER': 'SUMMER AUTUMN', 'MOTEBLOOM': 'WINTER', 'STRAWBERRY': 'SPRING', 'MELON': 'SUMMER',
    'EGGPLANT': 'AUTUMN', 'SNOWPEA': 'WINTER',
}


def clip_crops():
    """Every field crop through its five stages (seeded, sprout, young,
    growing, ripe) on watered soil, drawn from the farm tileset's own art;
    tall crops reach into the cell above as they do in the game."""
    import gen_field_gfx as gf
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'tilesets'))
    import ts_farm
    from pixelart import write_png
    gf.register_colors(ts_farm.FARM_COLORS)
    imgs, over = ts_farm.terrain_images(gf)
    soil, grass = imgs['TILLED_WET'], imgs['GRASS']
    S, cols = 3, 2
    crops = ts_farm.CROPS
    per_col = (len(crops) + cols - 1) // cols
    cell_w, row_h = 16 * 5 + 64, 32 + 10
    gap = 40
    W, H = cols * cell_w * S + (cols - 1) * gap + 16, per_col * row_h * S + 8
    bg = (34, 40, 56)
    rows = [[bg] * W for _ in range(H)]

    def col_of(k):
        return gf.C[k]

    def blit(img, x0, y0, under=None):
        for y in range(16):
            for x in range(16):
                k = img.p[y][x]
                if k is None:
                    if under is None:
                        continue
                    k = under.p[y][x]
                c = col_of(k)
                for yy in range(S):
                    r = rows[y0 + y * S + yy]
                    for xx in range(S):
                        r[x0 + x * S + xx] = c

    def label(text, x0, y0, rgb, px=2):
        glyph = Canvas1(len(text) * 4, 5)
        gf.draw_label(glyph, 0, 0, text)
        for gy in range(5):
            for gx in range(len(text) * 4):
                if glyph.rows[gy][gx]:
                    for yy in range(px):
                        for xx in range(px):
                            rows[y0 + gy * px + yy][x0 + gx * px + xx] = rgb
    for i, crop in enumerate(crops):
        cx = 8 + (i // per_col) * (cell_w * S + gap)
        cy = 8 + (i % per_col) * row_h * S
        label(crop, cx, cy + 10 * S, (250, 236, 180), 3)
        label(CROP_SEASONS[crop], cx, cy + 22 * S, (150, 200, 240), 2)
        stages = [('SEEDED', None), ('SPROUT', None), (crop + '_YOUNG', crop + '_YOUNG_TOP'),
                  (crop + '_GROW', crop + '_GROW_TOP'), (crop + '_RIPE', crop + '_RIPE_TOP')]
        for k, (low, top) in enumerate(stages):
            x0 = cx + 64 * S + k * 16 * S
            blit(grass, x0, cy)
            if top:
                blit(over[top], x0, cy)
            blit(over[low], x0, cy + 16 * S, under=soil)
    write_png(os.path.join(OUT, 'farm_crops.png'), W, H, rows)
    print('wrote farm_crops.png (%dx%d)' % (W, H))


def clip_farm():
    """WILLOW ACRE at work: till, water and plant a plot, then pick a ripe
    row; and a still of the built farm."""
    save = demo_save('farm', 'WILLOW_ACRE', 23, 18, calm=True, extra=['farm'])
    s = Script().boot().wait(40).rec('farm_work', 4).wait(20)
    s.tap('A').wait(28)                       # HOE: till
    s.tap('R').wait(16).tap('A').wait(30)     # CAN: water
    s.tap('R').wait(16).tap('A').wait(34)     # CORN SEED: plant
    s.walk('RIGHT', 4).tap('UP').wait(10)
    for k in range(4):                        # pick the ripe row
        s.tap('A').wait(40)
        s.walk('RIGHT', 1).tap('UP').wait(10)
    s.wait(20).stop()
    run(s, save)
    gif('farm_work', 'farm_work.gif', delay=5)
    save = demo_save('farm_view', 'WILLOW_ACRE', 29, 20, calm=True, extra=['farm'])
    run(Script().boot().wait(90).shot('farm_built'), save)
    still('farm_built', 'farm_built.png')


def clip_bridge():
    """The Maple Run bridge: walking north under it along the creek, then
    crossing over it on the road (docs/ELEVATION.md)."""
    save = demo_save('bridge_under', 'TOWN', 20, 25, calm=True)
    run(Script().boot().wait(20).rec('bridge_a', 3).walk('UP', 7).wait(20).stop(), save)
    save = demo_save('bridge_over', 'TOWN', 15, 17, calm=True)
    run(Script().boot().wait(20).rec('bridge_b', 3).tap('RIGHT').walk('RIGHT', 8).wait(20).stop().shot('bridge_end'), save)
    gif(['bridge_a', 'bridge_b'], 'bridge.gif')


SHOWCASE_MOVES = ['MUON_RAIN', 'KENAZ_FLARE', 'UNDERTOW', 'SOWILO_BEAM', 'ISA_SEAL', 'MOONBEAM',
                  'PRISM_RAY', 'ARC_FLASH']


def clip_moves():
    """A few of the biggest move animations, one bout each (the lead kin
    gets the move in its first slot; all of these always hit)."""
    parts = []
    for k, mv in enumerate(SHOWCASE_MOVES):
        save = demo_save('move%d' % k, 'MEADOW', 21, 38, low=True, extra=['move=' + mv])
        s = Script().boot().walk('UP', 3).wait(120).tap('A', 3, 40).wait(150)
        s.tap('A').wait(16).rec('move%d' % k, 4).tap('A').wait(130).stop()
        run(s, save)
        parts.append('move%d' % k)
    gif(parts, 'moves.gif', delay=5)


def field_ability(n, rec):
    """START -> FIELD (the demo 'travel' save has a TOWN MAP) -> entry n,
    recording from the ability list on."""
    s = Script().tap('START').wait(16).tap('DOWN', 6, 4).wait(8).tap('A').wait(24).rec(rec, 3).wait(10)
    return s.tap('DOWN', n, 10).wait(8).tap('A')


def clip_travel():
    """Getting around: the BIKE, SURF, the ferry, FLY and TELEPORT."""
    save = demo_save('bike', 'MEADOW', 21, 38, calm=True, extra=['travel', 'beaten'])
    s = Script().boot().wait(20).tap('R').wait(20).rec('bike', 3)
    s.hold('UP', 34).hold('LEFT', 20).hold('UP', 30).hold('RIGHT', 26).hold('UP', 20).wait(16)
    run(s.stop(), save)
    gif('bike', 'bike.gif')
    save = demo_save('surf', 'LAKE', 21, 27, calm=True, extra=['travel'])
    s = Script().boot().wait(20).rec('surf', 3).tap('A').wait(40).tap('A').wait(40)
    run(s.walk('UP', 6).walk('LEFT', 6).wait(20).stop(), save)
    gif('surf', 'surf.gif')
    save = demo_save('ferry', 'PORT_BRINE', 30, 34, calm=True, extra=['travel'])
    s = Script().boot().wait(20).rec('ferry', 4).tap('A').wait(50).tap('A').wait(40).tap('A')
    run(s.wait(330).stop(), save)
    gif('ferry', 'ferry.gif')
    save = demo_save('fly', 'MEADOW', 21, 38, calm=True, extra=['travel'])
    s = Script().boot().wait(20)
    s.lines += field_ability(1, 'fly').lines
    s.wait(10).tap('B').wait(50).tap('RIGHT').wait(40).tap('A').wait(110).stop()
    run(s, save)
    gif('fly', 'fly.gif')
    save = demo_save('teleport', 'MEADOW', 21, 38, calm=True, extra=['travel'])
    s = Script().boot().wait(20)
    s.lines += field_ability(2, 'teleport').lines
    s.wait(60).tap('A').wait(10).tap('B').wait(130).stop()
    run(s, save)
    gif('teleport', 'teleport.gif')


def clip_runestone():
    """The RUNESTONE (registered to SELECT) takes you home from anywhere."""
    save = demo_save('rune', 'LUMEN', 9, 18, calm=True, extra=['runestone'])
    run(Script().boot().wait(20).rec('rune', 3).tap('SELECT').wait(240).stop(), save)
    gif('rune', 'runestone.gif')


def clip_fusion():
    """The Fusion Loom: BLAZE + TIDE energy, the biggest stake, weave."""
    save = demo_save('fusion', 'WORKS', 10, 7, calm=True, extra=['fusion'])
    s = Script().boot().wait(20).rec('fusion', 3).tap('A').wait(40)
    s.tap('RIGHT').wait(10).tap('A').wait(16).tap('RIGHT').wait(10).tap('A').wait(16)
    s.tap('R').wait(12).tap('R').wait(24).tap('START').wait(200).tap('A').wait(40).tap('A').wait(30).stop()
    run(s, save)
    gif('fusion', 'fusion.gif')


def clip_evolve():
    """A THORNIP touches a BLOOM SHARD and grows into BRAMBLOR."""
    save = demo_save('evolve', 'MEADOW', 21, 38, calm=True, extra=['evolve'])
    s = Script().boot().wait(20).tap('START').wait(16).tap('DOWN', 3, 4).tap('A').wait(30)
    s.rec('evolve', 3).tap('RIGHT', 2, 10).wait(10).tap('A').wait(12).tap('A').wait(30).tap('A').wait(40)
    s.tap('A').wait(260).tap('A').wait(60).tap('A').wait(40).stop()
    run(s, save)
    gif('evolve', 'evolve.gif')


def clip_area():
    """The Almanac's area map: where a kin you have met lives."""
    save = demo_save('area', 'MEADOW', 21, 38, calm=True)
    s = Script().boot().wait(20).tap('START').wait(16).tap('A').wait(30).tap('RIGHT', 6, 6).wait(10)
    s.tap('A').wait(40).shot('almanac_page').tap('SELECT').wait(40).shot('almanac_area')
    run(s, save)
    still('almanac_area', 'almanac_area.png')


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
    'lorebook': clip_lorebook, 'menus': clip_menus, 'places': clip_places, 'world': clip_world, 'routes': clip_routes, 'mill-wheel': clip_mill_wheel, 'cinder-bridge': clip_cinder_bridge,
    'heron-fog': clip_heron_fog, 'mistfen-fog': clip_mistfen_fog, 'caravan-arriving': clip_caravan_arriving,
    'regions': clip_regions, 'elevation': clip_elevation, 'crops': clip_crops, 'farm': clip_farm, 'bridge': clip_bridge, 'moves': clip_moves, 'travel': clip_travel,
    'runestone': clip_runestone, 'fusion': clip_fusion, 'evolve': clip_evolve, 'area': clip_area,
}


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    for name in (argv or CLIPS):
        print('--', name)
        CLIPS[name]()
    if not argv:
        subprocess.check_call([sys.executable, os.path.join(ROOT, 'tools', 'render_gallery.py'),
                               os.path.join(OUT, 'kin.png'), '--scale', '1'])


if __name__ == '__main__':
    main(sys.argv[1:])
