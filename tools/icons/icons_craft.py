"""Bag icons owned by 'craft' (see tools/icons/__init__.py).

The five crafted lanterns (gen_battle_gfx.lantern_icon role palettes), the
13 dishes and drinks, the 11 crafting materials and the three recipe books
(docs/EXPANSION.md 6). 24x24, top-left light, index 1 pure white, drawn
with the same helpers as the core icons.
"""

import math


def _sphere(g, cv, mask, cx, cy, rx, ry, cols, th=(-0.1, 0.42, 0.82)):
    for (x, y) in mask:
        nx = (x + 0.5 - cx) / (rx + 0.5)
        ny = (y + 0.5 - cy) / (ry + 0.5)
        lv = g.quant(g.sphere_b(max(-0.99, min(0.99, nx)), max(-0.99, min(0.99, ny))), th)
        cv.set(x, y, cols[min(lv, len(cols) - 1)])


def _blob(g, cv, cx, cy, rx, ry, cols):
    _sphere(g, cv, g.ellipse_mask(cx, cy, rx, ry), cx, cy, rx, ry, cols)


def _plate(g, cv, y=18, x0=2, x1=21):
    """A white plate seen from the front, under a dish."""
    rim = g.ramp((120, 128, 152), (200, 208, 224), (240, 244, 252))
    for (x, yy) in g.ellipse_mask((x0 + x1 + 1) / 2, y, (x1 - x0 + 1) / 2, 2.6):
        cv.set(x, yy, rim[0] if yy > y + 0.5 else rim[1] if yy > y - 1 else rim[2])


def _bowl(g, cv, cols, y0=12, fill=None):
    """A bowl from the side; fill = ramp for the food heaped in it."""
    if fill:
        _blob(g, cv, 11.5, y0 + 0.5, 8.5, 4.0, fill)
    body = set()
    for (x, y) in g.ellipse_mask(11.5, y0, 9.5, 9.0):
        if y >= y0:
            body.add((x, y))
    g.paint_levels(cv, g.lathe_levels(body), cols)
    for x in range(3, 21):
        cv.set(x, y0, cols[-1])


def _bottle(g, glass, liquid, outc, cork=None, round_=True):
    cv = g.Canvas(24, 24)
    body = g.ellipse_mask(11.5, 15.0, 7.0, 7.0) if round_ else g.rect_mask(6, 8, 17, 21, r=2)
    for (x, y) in body:
        cv.set(x, y, glass[1])
    for (x, y) in body:
        if y >= 12:
            cv.set(x, y, liquid[0] if x > 13 else liquid[1] if x > 8 else liquid[2])
    for y in range(3, 9):
        for x in range(10, 14):
            cv.set(x, y, glass[1] if x < 13 else glass[0])
    cork = cork or g.ramp((120, 72, 32), (176, 120, 64))
    for y in range(1, 4):
        for x in range(10, 14):
            cv.set(x, y, cork[1] if x < 12 else cork[0])
    g.outline(cv, outc)
    for (x, y) in [(8, 12), (8, 13), (9, 11), (11, 5)]:
        cv.set(x, y, g.WHITE)
    return cv


def _book(g, cover, band, emblem_fn):
    C = g.C
    cv = g.Canvas(24, 24)
    pages = g.ramp((200, 188, 160), (240, 232, 208))
    for y in range(3, 22):
        for x in range(4, 20):
            cv.set(x, y, cover[1] if x > 5 else cover[2])
    for y in range(4, 21):
        cv.set(19, y, pages[1])
        cv.set(20, y, pages[0])
    for x in range(5, 21):
        cv.set(x, 21, pages[0])
    for x in range(4, 20):
        cv.set(x, 6, band)
        cv.set(x, 18, band)
    emblem_fn(cv)
    g.outline(cv, C(40, 24, 24))
    cv.set(7, 4, g.WHITE)
    cv.set(7, 5, g.WHITE)
    return cv


def icons(g):
    C, W = g.C, g.WHITE
    out = []
    for v in ('DUSK LANTERN', 'TIDE LANTERN', 'HEAVY LANTERN', 'QUICK LANTERN', 'BONE LANTERN'):
        out.append((v.replace(' ', '_'), g.lantern_icon(v)))

    crust = g.ramp((152, 88, 32), (208, 136, 64), (240, 184, 104), (255, 224, 160))
    berry = g.ramp((96, 16, 56), (176, 40, 88), (232, 96, 136))

    # BERRY TART: a crust ring full of berries
    cv = g.Canvas(24, 24)
    _plate(g, cv)
    _blob(g, cv, 11.5, 14.0, 9.0, 4.5, crust)
    for (x, y) in g.ellipse_mask(11.5, 13.0, 7.0, 2.6):
        cv.set(x, y, berry[1])
    for (bx, by) in [(8, 12), (11, 12), (14, 12), (9, 14), (13, 14), (16, 13)]:
        _blob(g, cv, bx + 0.5, by + 0.5, 1.4, 1.4, berry)
    g.outline(cv, C(80, 32, 24))
    cv.set(9, 11, W)
    out.append(('BERRY_TART', cv))

    # HONEY BUN: a glossy round bun with a honey drizzle
    cv = g.Canvas(24, 24)
    _plate(g, cv)
    _blob(g, cv, 11.5, 12.5, 8.5, 6.5, crust)
    honey = C(255, 200, 48)
    for x in range(5, 19):
        cv.set(x, 9 + (x % 3 == 0), honey)
    g.outline(cv, C(96, 48, 16))
    cv.set(8, 8, W)
    out.append(('HONEY_BUN', cv))

    wood = g.ramp((104, 56, 24), (160, 96, 48), (208, 144, 88))
    # VEGGIE STEW: a wooden bowl with carrots and greens
    cv = g.Canvas(24, 24)
    _bowl(g, cv, wood, fill=g.ramp((136, 72, 24), (184, 112, 48), (224, 160, 88)))
    for (x, y, c) in [(7, 10, C(248, 136, 40)), (12, 9, C(96, 176, 64)), (15, 10, C(248, 136, 40)),
                      (10, 11, C(232, 208, 120))]:
        cv.set(x, y, c)
        cv.set(x + 1, y, c)
    g.outline(cv, C(56, 32, 16))
    for (x, y) in [(9, 4), (10, 3), (14, 5), (14, 4)]:
        cv.set(x, y, C(224, 224, 232))
    out.append(('VEGGIE_STEW', cv))

    # CHILI POT: a black pot of red chili, a pepper on top
    cv = g.Canvas(24, 24)
    iron = g.ramp((32, 32, 40), (64, 64, 80), (104, 104, 120))
    _bowl(g, cv, iron, fill=g.ramp((136, 16, 16), (200, 48, 32), (240, 96, 64)))
    for (x, y) in [(13, 8), (14, 8), (15, 9), (16, 9), (12, 9)]:
        cv.set(x, y, C(232, 32, 32))
    cv.set(11, 8, C(64, 160, 48))
    cv.set(2, 13, iron[1])
    cv.set(21, 13, iron[1])
    g.outline(cv, C(24, 16, 16))
    out.append(('CHILI_POT', cv))

    # PUMPKIN PIE: a wedge with an orange filling
    cv = g.Canvas(24, 24)
    _plate(g, cv, y=19)
    wedge = g.poly_mask([(3, 17), (20, 17), (20, 9), (5, 13)], 24, 24)
    fill = g.ramp((200, 88, 16), (240, 136, 40), (255, 184, 88))
    for (x, y) in wedge:
        cv.set(x, y, fill[2] if y < 12 else fill[1] if y < 15 else crust[1])
    for y in range(9, 18):
        cv.set(20, y, crust[2])
        cv.set(21, y, crust[1])
    for (x, y) in [(15, 9), (16, 8), (17, 8), (16, 9)]:
        cv.set(x, y, C(255, 248, 232))
    g.outline(cv, C(96, 40, 8))
    out.append(('PUMPKIN_PIE', cv))

    # MOONCAKE: a round pressed cake with a crescent stamp
    cv = g.Canvas(24, 24)
    _blob(g, cv, 11.5, 12.5, 8.5, 8.5, g.ramp((136, 72, 24), (192, 120, 48), (232, 168, 88), (248, 208, 144)))
    for (x, y) in g.ellipse_mask(11.5, 12.5, 4.5, 4.5):
        if (x + 0.5 - 13.0) ** 2 + (y + 0.5 - 11.5) ** 2 > 12:
            cv.set(x, y, C(255, 232, 160))
    g.outline(cv, C(80, 40, 16))
    cv.set(7, 7, W)
    out.append(('MOONCAKE', cv))

    # TRUFFLE RICE: a bowl of rice with dark truffle shavings
    cv = g.Canvas(24, 24)
    _bowl(g, cv, g.ramp((56, 88, 136), (88, 128, 184), (152, 184, 224)),
          fill=g.ramp((200, 192, 176), (232, 228, 216), (252, 252, 244)))
    for (x, y) in [(8, 10), (12, 9), (15, 11), (10, 12)]:
        cv.set(x, y, C(72, 48, 32))
    g.outline(cv, C(32, 40, 64))
    out.append(('TRUFFLE_RICE', cv))

    # CAMP SKEWER: a stick with corn, tomato and a pepper
    cv = g.Canvas(24, 24)
    for (x, y) in g.line_pts(2, 21, 21, 2):
        cv.set(x, y, C(176, 128, 72))
    for (cx, cy, cols) in [(7, 16, g.ramp((176, 24, 24), (232, 56, 48), (255, 128, 104))),
                           (12, 11, g.ramp((200, 152, 16), (248, 208, 48), (255, 240, 136))),
                           (17, 6, g.ramp((40, 120, 40), (80, 176, 64), (152, 224, 112)))]:
        _blob(g, cv, cx, cy, 3.2, 3.2, cols)
    g.outline(cv, C(56, 32, 16))
    out.append(('CAMP_SKEWER', cv))

    # SUN SALAD: greens with a sunflower on top
    cv = g.Canvas(24, 24)
    _bowl(g, cv, g.ramp((200, 200, 208), (232, 232, 240), (252, 252, 255)),
          fill=g.ramp((32, 120, 40), (72, 168, 64), (136, 216, 96)))
    for (x, y) in g.ellipse_mask(12, 8, 3.2, 3.2):
        cv.set(x, y, C(255, 208, 32))
    for (x, y) in g.ellipse_mask(12, 8, 1.4, 1.4):
        cv.set(x, y, C(120, 72, 24))
    cv.set(6, 10, C(232, 64, 48))
    cv.set(17, 11, C(232, 64, 48))
    g.outline(cv, C(40, 56, 40))
    out.append(('SUN_SALAD', cv))

    # KERNEL CANDY: a faceted amber candy with a glowing mote inside
    cv = g.Canvas(24, 24)
    gem = g.poly_mask([(12, 3), (20, 9), (18, 19), (6, 19), (4, 9)], 24, 24)
    amber = g.ramp((176, 96, 8), (232, 160, 32), (255, 216, 96), (255, 244, 200))
    for (x, y) in gem:
        u = (x - 4) / 16.0 + (y - 3) / 32.0
        cv.set(x, y, amber[3] if u < 0.25 else amber[2] if u < 0.55 else amber[1] if u < 0.85 else amber[0])
    for (x, y) in g.ellipse_mask(12, 12, 2.2, 2.2):
        cv.set(x, y, C(200, 255, 232))
    g.outline(cv, C(96, 48, 0))
    cv.set(9, 6, W)
    cv.set(12, 12, W)
    out.append(('KERNEL_CANDY', cv))

    # drinks
    glass = g.ramp((152, 184, 200), (216, 236, 244))
    out.append(('BERRY_JUICE', _bottle(g, glass, g.ramp((96, 16, 72), (168, 40, 120), (216, 96, 168)),
                                      C(48, 24, 48))))
    out.append(('APPLE_PRESS', _bottle(g, glass, g.ramp((176, 120, 16), (224, 176, 48), (248, 216, 112)),
                                      C(72, 56, 16), round_=False)))
    out.append(('PEACH_NECTAR', _bottle(g, glass, g.ramp((224, 104, 64), (248, 152, 104), (255, 200, 160)),
                                       C(96, 40, 24))))

    # materials
    cv = g.Canvas(24, 24)                                   # GLOW HONEY: a honey jar
    jar = g.rect_mask(5, 7, 18, 21, r=3)
    hon = g.ramp((200, 112, 8), (248, 176, 32), (255, 224, 104))
    g.paint_levels(cv, g.lathe_levels(jar), hon)
    for y in range(4, 7):
        for x in range(6, 18):
            cv.set(x, y, C(232, 232, 216) if y > 4 else C(200, 64, 48))
    for x in range(6, 18):
        cv.set(x, 12, C(255, 248, 200) if x % 2 else hon[2])
    g.outline(cv, C(96, 48, 0))
    cv.set(7, 9, W)
    out.append(('GLOW_HONEY', cv))

    cv = g.Canvas(24, 24)                                   # HEART SAND: a pile of pink crystal sand
    pile = set((x, y) for (x, y) in g.ellipse_mask(11.5, 20, 10, 10) if y >= 11 and y <= 20)
    sand = g.ramp((200, 96, 136), (240, 152, 184), (255, 208, 224))
    _sphere(g, cv, pile, 11.5, 20, 10, 10, sand)
    for (x, y) in [(8, 14), (14, 13), (11, 17), (16, 17)]:
        cv.set(x, y, W)
    g.outline(cv, C(96, 32, 64))
    out.append(('HEART_SAND', cv))

    def rock(cols, outc, pts, specks, speck_col):
        cv = g.Canvas(24, 24)
        m = g.poly_mask(pts, 24, 24)
        _sphere(g, cv, m, 11.5, 12.5, 9, 8, cols)
        for (x, y) in specks:
            if (x, y) in m:
                cv.set(x, y, speck_col)
        g.outline(cv, outc)
        return cv
    rock_pts = [(4, 12), (8, 5), (16, 4), (21, 10), (19, 19), (10, 20), (3, 17)]
    out.append(('IRON_ORE', rock(g.ramp((72, 48, 40), (128, 80, 64), (176, 120, 96), (208, 160, 136)),
                                  C(40, 24, 24), rock_pts, [(8, 9), (14, 8), (12, 14), (17, 13), (7, 15)],
                                  C(200, 88, 48))))
    out.append(('COAL', rock(g.ramp((16, 16, 24), (40, 40, 48), (72, 72, 88), (112, 112, 128)),
                              C(8, 8, 8), rock_pts, [(9, 8), (15, 11)], W)))

    cv = g.Canvas(24, 24)                                   # BONE MEAL: a sack of white powder
    sack = g.ellipse_mask(11.5, 14.5, 8, 7.5)
    _sphere(g, cv, sack, 11.5, 14.5, 8, 7.5, g.ramp((168, 144, 104), (208, 184, 136), (232, 216, 176)))
    for y in range(3, 8):
        for x in range(9, 15):
            cv.set(x, y, C(176, 152, 112))
    for x in range(8, 16):
        cv.set(x, 7, C(120, 88, 56))
    for (x, y) in g.ellipse_mask(11.5, 4, 3.5, 1.5):
        cv.set(x, y, C(248, 244, 232))
    g.outline(cv, C(72, 56, 40))
    out.append(('BONE_MEAL', cv))

    cv = g.Canvas(24, 24)                                   # SILK THREAD: a spool
    for y in range(6, 18):
        for x in range(6, 18):
            cv.set(x, y, C(232, 232, 248) if (y + x // 3) % 3 else C(184, 184, 216))
    for x in range(4, 20):
        for y in (4, 5, 18, 19):
            cv.set(x, y, C(176, 120, 64) if x < 16 else C(128, 80, 40))
    for (x, y) in g.line_pts(17, 12, 22, 21):
        cv.set(x, y, C(232, 232, 248))
    g.outline(cv, C(64, 48, 64))
    out.append(('SILK_THREAD', cv))

    cv = g.Canvas(24, 24)                                   # SALT: a little salt cellar
    body = g.rect_mask(7, 8, 16, 21, r=2)
    g.paint_levels(cv, g.lathe_levels(body), g.ramp((152, 168, 192), (200, 216, 232), (240, 248, 255)))
    for (x, y) in g.ellipse_mask(11.5, 6.5, 5, 3):
        cv.set(x, y, C(168, 176, 192))
    for (x, y) in [(10, 5), (12, 5), (11, 7), (13, 7)]:
        cv.set(x, y, C(64, 72, 88))
    g.outline(cv, C(56, 64, 88))
    cv.set(9, 11, W)
    out.append(('SALT', cv))

    def leaf(cols, outc, vein):
        cv = g.Canvas(24, 24)
        m = set()
        for (x, y) in g.ellipse_mask(12, 12, 5.5, 9.5):
            m.add((x, y))
        _sphere(g, cv, m, 12, 12, 5.5, 9.5, cols)
        for (x, y) in g.line_pts(12, 4, 12, 22):
            cv.set(x, y, vein)
        for k in range(3):
            cv.set(11 - k, 9 + k * 4, vein)
            cv.set(13 + k, 9 + k * 4, vein)
        g.outline(cv, outc)
        return cv
    out.append(('MINT_LEAF', leaf(g.ramp((24, 112, 72), (56, 168, 104), (128, 224, 160)), C(16, 56, 40),
                                  C(176, 240, 200))))

    cv = g.Canvas(24, 24)                                   # GLOWCAP: a glowing mushroom
    cap = set((x, y) for (x, y) in g.ellipse_mask(11.5, 11.5, 9, 7.5) if y <= 11)
    _sphere(g, cv, cap, 11.5, 11.5, 9, 7.5, g.ramp((32, 136, 136), (64, 200, 176), (152, 248, 216)))
    for y in range(12, 21):
        for x in range(9, 15):
            cv.set(x, y, C(232, 224, 200) if x < 13 else C(184, 176, 152))
    for (x, y) in [(7, 7), (12, 5), (16, 8)]:
        cv.set(x, y, C(224, 255, 240))
    g.outline(cv, C(16, 64, 72))
    out.append(('GLOWCAP', cv))

    cv = g.Canvas(24, 24)                                   # STARDUST CHIP: a glittering shard
    shard = g.poly_mask([(12, 2), (19, 10), (14, 21), (5, 13)], 24, 24)
    star = g.ramp((40, 40, 112), (88, 80, 176), (160, 152, 232), (224, 224, 255))
    for (x, y) in shard:
        u = (x - 5) / 14.0 - (y - 2) / 40.0
        cv.set(x, y, star[3] if u < 0.2 else star[2] if u < 0.5 else star[1] if u < 0.8 else star[0])
    for (x, y) in [(10, 8), (14, 13), (9, 14)]:
        cv.set(x, y, W)
    g.outline(cv, C(16, 16, 56))
    out.append(('STARDUST_CHIP', cv))

    cv = g.Canvas(24, 24)                                   # OLD COIN: a worn gold coin
    _blob(g, cv, 11.5, 11.5, 9, 9, g.ramp((136, 88, 16), (192, 136, 32), (232, 184, 64), (255, 224, 136)))
    for (x, y) in g.ellipse_mask(11.5, 11.5, 6, 6):
        if abs(math.hypot(x + 0.5 - 11.5, y + 0.5 - 11.5) - 5.5) < 0.6:
            cv.set(x, y, C(152, 104, 24))
    for (x, y) in g.line_pts(9, 9, 14, 14):
        cv.set(x, y, C(152, 104, 24))
    g.outline(cv, C(80, 48, 8))
    cv.set(7, 6, W)
    out.append(('OLD_COIN', cv))

    # books
    def emblem_pan(cv):
        for (x, y) in g.ellipse_mask(11, 12, 3.5, 2.5):
            cv.set(x, y, C(248, 232, 200))
        for x in range(14, 18):
            cv.set(x, 12, C(248, 232, 200))

    def emblem_flask(cv):
        for (x, y) in g.ellipse_mask(11.5, 13.5, 3.2, 3.2):
            cv.set(x, y, C(160, 248, 200))
        for y in range(8, 11):
            cv.set(11, y, C(160, 248, 200))

    def emblem_anvil(cv):
        for x in range(8, 17):
            cv.set(x, 11, C(224, 224, 232))
        for x in range(10, 15):
            cv.set(x, 12, C(224, 224, 232))
            cv.set(x, 14, C(224, 224, 232))
        cv.set(12, 13, C(224, 224, 232))
    out.append(('COOKBOOK', _book(g, g.ramp((136, 24, 24), (192, 48, 40), (224, 96, 80)), C(248, 200, 64),
                                  emblem_pan)))
    out.append(('BREW_NOTES', _book(g, g.ramp((32, 80, 64), (48, 120, 96), (96, 168, 136)), C(200, 176, 96),
                                    emblem_flask)))
    out.append(('FORGE_MANUAL', _book(g, g.ramp((56, 56, 72), (88, 88, 112), (136, 136, 160)), C(232, 120, 40),
                                      emblem_anvil)))
    return out
